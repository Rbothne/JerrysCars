"""Dealer eProcess: the used search page itself, 48 cars a page, read from the server-rendered HTML.

`/search/used/?ct=48&p={n}&tp=used`, pages 1 to the pager's `page_count`. Each card carries schema.org Vehicle
JSON-LD (VIN, mileage, stock number, address, photo) and a price stack (`<dt>` label, `<dd>` figure); the page
also holds `filter_vehicle_data`, the same cars with date in stock, body, drivetrain and rooftop. The results
count (`data-vehicle_count`) says what a whole read is.

Every Dealer eProcess site sits behind Cloudflare's managed challenge, so a plain `get` is refused (403,
"Just a moment..."). The caller's `get` must carry a `cf_clearance` cookie and the exact user agent of the
browser that earned it, from the same address: research/08-routing-dealereprocess.md. Seen working on
landersused.com, pohanka.com and jacksaysyes.com, 2026-11-21."""

import json
import pathlib
import re
import urllib.parse

from . import NotRead, dealer_listing, drive, site, text

PAGE = 48                   # the largest page size the site's own menu offers short of "All"
MAX_PAGES = 80
CALL_FOR_PRICE = 100_000_000   # the figure the site prints under "Call for Price"
PLACEHOLDERS = ("defaultmake_asset", "stockphoto_asset", "/svp/")   # make logos and makers' renders, not the car

_CARD = re.compile(r'<div\s+class="vehicle_item[^"]*"\s+data-vehicle_id="(\d+)"')
_ROW = re.compile(r'<(dt|dd)\s+class="([^"]*)"[^>]*>(.*?)</\1>', re.S)


def load_clearances(folder):
    """{host: saved clearance} from the .json files a browser run saved in `folder` ({"host", "cookie",
    "user_agent", ...} each). A missing folder is no clearances."""
    found = {}
    for path in sorted(pathlib.Path(folder).glob("*.json")) if pathlib.Path(folder).is_dir() else []:
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if isinstance(saved, dict) and saved.get("host") and saved.get("cookie") and saved.get("user_agent"):
            found[saved["host"]] = saved
    return found


def with_clearance(get, clearances):
    """A `get` that sends a host's saved Cloudflare clearance: its cookie and the user agent that earned it.
    Hosts without one are asked exactly as before."""
    def cleared_get(url, **options):
        saved = clearances.get(urllib.parse.urlparse(url).netloc)
        if saved:
            options["headers"] = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9",
                                  **(options.get("headers") or {}),
                                  "User-Agent": saved["user_agent"], "Cookie": saved["cookie"]}
        return get(url, **options)
    return cleared_get


def _filter_data(page):
    """The page's `filter_vehicle_data`: {vehicle id: facts}."""
    key = '"filter_vehicle_data":'
    at = page.find(key)
    if at < 0:
        return {}
    try:
        return json.JSONDecoder().raw_decode(page, at + len(key))[0] or {}
    except ValueError:
        return {}


def _locations(page):
    """{location id: name} from the search page's location filter menu. Group sites list several stores, and
    `filter_vehicle_data` names only some of them."""
    return dict(re.findall(r'data-filter-field="location_id"\s+data-filter-value="(\d+)".*?data-filter-label="([^"]*)"',
                           page, re.S))


def _vehicle_ld(card):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', card, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Vehicle":
            return data
    return {}


def _amount(fragment):
    words = (text(fragment) or "").replace(" ", "")
    match = re.search(r"\d[\d,]*(?:\.\d+)?", words)
    return float(match.group().replace(",", "")) if match else None


def _stack(card):
    """The card's price rows in order: (label, amount, kind, last). Labels lose their tooltip text."""
    pricing = (re.search(r'data-tab_content="pricing"(.*?)</dl>', card, re.S)          # tabbed cards (Landers)
               or re.search(r"<dl>((?:(?!</dl>).)*?price_item_label_class.*?)</dl>", card, re.S))   # plain cards
    rows, label = [], None
    for tag, classes, inner in _ROW.findall(pricing.group(1) if pricing else ""):
        if tag == "dt":
            label = (text(inner.split("<span", 1)[0]), classes)
            continue
        if not label:
            continue
        name, label_classes = label
        label = None
        amount = _amount(inner)
        if amount is None or not name:
            continue
        if "discount" in label_classes or "price_subtract" in inner:
            amount, kind = -amount, "discount"
        elif "fee_label_class" in label_classes or "fee" in name.lower():
            kind = "fee"
        else:
            kind = "price"
        rows.append((name, amount, kind, "last_price_item_label_class" in label_classes))
    return rows


def _whole(number):
    return int(number) if number is not None and float(number).is_integer() else number


def _prices(card):
    """(asking price, extra fields). The asking price is the final figure less the fees the stack adds."""
    rows = _stack(card)
    extra = {}
    if not rows:
        return None, extra
    final = next((row for row in rows if row[3]), rows[-1])
    if final[1] >= CALL_FOR_PRICE or "call" in final[0].lower():
        extra["price_note"] = final[0]
        return None, extra
    fees = sum(amount for _, amount, kind, _ in rows if kind == "fee")
    extra["prices"] = {name: _whole(amount) for name, amount, _, _ in rows}
    extra["price_all_in"] = _whole(final[1])
    extra["fees"] = _whole(fees)
    return final[1] - fees, extra


def _listing(dealer, base, vehicle_id, card, facts, locations, seen):
    ld = _vehicle_ld(card)
    brand = ld.get("brand") if isinstance(ld.get("brand"), dict) else {}
    year = facts.get("year") or ld.get("vehicleModelDate")
    make = facts.get("make") or brand.get("name")
    model = facts.get("model") or ld.get("model")
    trim = facts.get("trim") or ld.get("vehicleConfiguration")
    vin = facts.get("vin") or ld.get("vehicleIdentificationNumber")
    path = ld.get("url")
    photo = ld.get("image") if isinstance(ld.get("image"), str) else None
    photos = [photo] if photo and not any(mark in photo for mark in PLACEHOLDERS) else []
    total = re.search(r'loopslider_controls_count__total">\s*(\d+)\s*<', card)
    stocked = re.fullmatch(r"\d{4}-\d{2}-\d{2}", facts.get("date_instock") or "")
    miles = (ld.get("mileageFromOdometer") or {}).get("value") if isinstance(ld.get("mileageFromOdometer"), dict) else None
    price, extra = _prices(card)
    extra.update(stock=facts.get("stock") or ld.get("sku"), vehicle_id=vehicle_id,
                 location=facts.get("location_name") or locations.get(facts.get("location_id")) or None,
                 location_id=facts.get("location_id"), certified=facts.get("flag_certified") == "1")
    return dealer_listing(
        dealer, vin or vehicle_id, seen,
        url=base + path if path and path.startswith("/") else path,
        title=" ".join(str(part) for part in (year, make, model, trim) if part),
        price=price,
        posted=stocked.group() + "T00:00" if stocked else None,
        vin=vin, year=year, make=make, model=model, trim=trim, body=facts.get("body"),
        drive=drive(facts.get("drivetrain")), engine=facts.get("engine"), fuel=facts.get("fuel_type"),
        transmission=facts.get("transmission"), miles=miles,
        color=facts.get("exterior_color") or ld.get("color"),
        photos=photos, photo_count=int(total.group(1)) if photos and total else len(photos),
        extra=extra)


def _cards(page):
    starts = [(match.start(), match.group(1)) for match in _CARD.finditer(page)]
    for number, (start, vehicle_id) in enumerate(starts):
        end = starts[number + 1][0] if number + 1 < len(starts) else len(page)
        yield vehicle_id, page[start:end]


def read(dealer, get, seen):
    base = site(dealer)
    found, ids, total, number, pages, locations = [], set(), None, 1, 1, {}
    while True:
        page = get(f"{base}/search/used/?ct={PAGE}&p={number}&tp=used").decode("utf-8", "replace")
        cards = list(_cards(page))
        if number == 1:
            if not cards and "vehicle_search_no_results" in page:
                return [], True
            counted = re.search(r'data-vehicle_count="(\d+)"', page) or re.search(r'"vehicle_count":(\d+)', page)
            if not (cards and counted):
                raise NotRead(f"{base}: no cars and no results count on the used search page")
            total = int(counted.group(1))
            pager = re.search(r"var page_count = (\d+);", page)
            pages = int(pager.group(1)) if pager else 1
        facts = _filter_data(page)
        locations = {**_locations(page), **locations}
        for vehicle_id, card in cards:
            if vehicle_id in ids:
                continue
            listing = _listing(dealer, base, vehicle_id, card, facts.get(vehicle_id) or {}, locations, seen)
            if listing:
                ids.add(vehicle_id)
                found.append(listing)
        if number >= pages or number >= MAX_PAGES or not cards:
            break
        number += 1
    return found, len(found) >= total
