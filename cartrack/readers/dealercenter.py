"""DealerCenter websites (WordPress, "dws" plugins): the site's own admin-ajax service lists every car, 30 a page.

The pages sit behind a Cloudflare challenge that a plain request cannot pass, but `/wp-admin/admin-ajax.php`
answers a plain POST with no cookie (robots.txt allows it, and forbids the `?page_no=` pages). Two actions:
`dws_inventory_search_service` / `get_vehicle_count` gives the cars per make, whose sum is the inventory, and
`dws_inventory_vehicles` with `page_no` gives a page of the same vehicle cards the inventory page shows; a page
past the end is empty. The card's "Price" includes the dealer's doc fee; the figure before fees is taken as the
asking price and the shown total kept in `extra`. Seen working on colliervilleautocenter.com, 2026-11-21:
78 counted, 78 read in 3 pages (research/08-routing-unknowns.md)."""

import html
import json
import re
import urllib.parse

from . import NotRead, dealer_listing, drive, history, site, text
from ..listings import num

MAX_PAGES = 40
FORM = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}
_CARD = r'(?=<div class="vehicle-container\b)'


def _slug(words):
    return re.sub(r"[^a-z0-9]+", "-", " ".join(words).lower()).strip("-")


def _take(words, slug):
    """The leading words of `words` that spell the address's `slug` ("land-rover" -> LAND ROVER), or None."""
    for size in range(1, len(words) + 1):
        if _slug(words[:size]) == slug:
            return words[:size], words[size:]
    return None, words


def _fields(card):
    """The card's labelled lines: vehicle-field-<name> blocks, and the "Mileage:" / "Vin:" lines of some layouts."""
    found = {}
    for name, body in re.findall(r'class="vehicle-info-col vehicle-field-(\w+)">(.*?)</div>', card, re.S):
        value = re.search(r'class="vehicle-info-value"[^>]*>(.*?)</span>', body, re.S)
        if value and text(value.group(1)) and name not in found:
            found[name] = text(value.group(1))
    for name, value in re.findall(r'<div class="vehicle-(mileage|vin)"><span class="label">[^<]*</span>(.*?)</div>', card, re.S):
        found.setdefault({"mileage": "odometer"}.get(name, name), text(value))
    return found


def _listing(dealer, card, seen):
    vin = re.search(r'data-vehicle-id="vehicle-id-(\w+)"', card)
    link = re.search(r'<a class="vehicle-title" href="([^"]+)"\s*>(.*?)</a>', card, re.S)
    if not (vin and link):
        return None
    url, title = link.group(1), text(link.group(2))
    path = [part for part in urllib.parse.urlparse(url).path.split("/") if part]
    words = (title or "").split()
    year = words[0] if words and words[0].isdigit() else None
    rest = words[1:] if year else words
    make, rest = _take(rest, path[-3]) if len(path) >= 3 else (None, rest)
    model, rest = _take(rest, path[-2]) if make and len(path) >= 3 else (None, rest)
    if not make:                                   # the address does not spell it out: first word is the make
        make, model, rest = rest[:1], rest[1:2], rest[2:]
    trim = re.search(r'<label>Trim: </label>\s*<span class="info-value">(.*?)</span>', card, re.S)
    trim = text(trim.group(1)) if trim else (" ".join(rest) or None)

    facts = _fields(card)
    before, fees, total = (re.search(rf'data-{name}="([^"]*)"', card) for name in ("vehicle-price", "dealer-fees", "total-price"))
    shown = re.search(r'class="vehicle-price-value[^"]*">\s*([^<]*)', card)
    stock = re.search(r'data-stock-number="([^"]+)"', card)
    extra = {"stock": facts.get("stocknumber") or (stock.group(1) if stock else None), **history(card)}
    if before and num(before.group(1)):            # "*Includes Dealer Fees": the figure before them is the ask
        price = num(before.group(1))
        extra["shown_price"] = int(num(total.group(1))) if total and num(total.group(1)) else None
        try:
            extra["fees"] = {item["Displayname"]: int(num(item["Amount"])) for item in json.loads(html.unescape(fees.group(1)))}
        except (ValueError, KeyError, TypeError, AttributeError):
            pass
    else:                                          # "*Fees Not Disclosed": the shown figure is all there is
        price = num(shown.group(1)) if shown else None
    photo = re.search(r'<img[^>]*class="vehicle-image"[^>]*srcset="([^"]+)"', card)
    photo = photo.group(1).split(",")[-1].split()[0] if photo else None
    if not photo:
        photo = (re.search(r'src="(https://imagescf\.dealercenter\.net/[^"]+)"', card) or [None, None])[1]
    return dealer_listing(
        dealer, vin.group(1), seen,
        url=url, title=title, price=price,
        vin=vin.group(1), year=year, make=" ".join(make) if make else None, model=" ".join(model) if model else None,
        trim=trim, drive=drive(facts.get("drivetrain")), engine=facts.get("engine"),
        transmission=facts.get("transmission"), miles=facts.get("odometer"), color=facts.get("exteriorcolor"),
        photos=[photo] if photo else [], extra=extra)


def read(dealer, get, seen):
    ajax = f"{site(dealer)}/wp-admin/admin-ajax.php"

    def ask(**form):
        return get(ajax, data=urllib.parse.urlencode(form).encode(), headers=FORM)

    try:
        counts = json.loads(ask(action="dws_inventory_search_service", requestType="get_vehicle_count").decode("utf-8-sig"))
        total = sum(int(entry.get("Count") or 0) for entry in counts)
    except (ValueError, TypeError, AttributeError):
        total = None                                    # no count: the read cannot be called whole

    found, ids = [], set()
    for number in range(1, MAX_PAGES + 1):
        page = ask(action="dws_inventory_vehicles", page_no=number).decode("utf-8-sig", "replace")
        fresh = [car for car in (_listing(dealer, card, seen) for card in re.split(_CARD, page)[1:])
                 if car and car["id"] not in ids]
        if not fresh:                                   # past the last page the service answers an empty body
            break
        ids.update(car["id"] for car in fresh)
        found += fresh
        if total is not None and len(found) >= total:
            break
    if not found:
        raise NotRead(f"{dealer['host']}: admin-ajax gave no vehicle cards")
    return found, total is not None and len(found) >= total
