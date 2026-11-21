"""AutoRevo: independent lots. `/inventory` is one HTML page of vehicle cards, each with its VIN, price and miles.

The site's robots.txt forbids addresses with a query string, which is how its further pages are reached,
so this reads `/inventory` only and uses `/sitemap.xml` to tell whether that was every car. Seen working on
peckdaniel.com, 2026-11-20, where the page held all 25 cars the sitemap listed."""

import re

from . import NotRead, dealer_listing, drive, site, text

_CARD = '<section class="inventory_item'


def _listing(dealer, base, card, seen):
    link = re.search(r'href="([^"]+/(\d+))"', card)
    if not link:
        return None
    named = dict(re.findall(r'<span class="(year|make|model|trim)">([^<]*)</span>', card))
    facts = {name: text(value) for name, value in re.findall(r'<dd class="(\w+)_value[^"]*">(.*?)</dd>', card, re.S)}
    facts = {name: value for name, value in facts.items() if value not in (None, "-")}
    price = re.search(r'website_price">[^<]*<span>([^<]*)', card)
    photo = re.search(r'<img[^>]*\ssrc="(https?://[^"]+)"', card)
    return dealer_listing(
        dealer, link.group(2), seen,
        url=base + link.group(1),
        title=" ".join(named[part] for part in ("year", "make", "model", "trim") if named.get(part)),
        price=price.group(1) if price else None,
        vin=facts.get("vin"), year=named.get("year"), make=named.get("make"), model=named.get("model"),
        trim=named.get("trim"), drive=drive(facts.get("drivetrain")), engine=facts.get("engine"),
        transmission=facts.get("transmission"), miles=facts.get("mileage"), color=facts.get("exterior"),
        photos=[photo.group(1)] if photo else [])


def read(dealer, get, seen):
    base = site(dealer)
    cards = get(f"{base}/inventory").decode("utf-8", "replace").split(_CARD)[1:]
    found = [listing for listing in (_listing(dealer, base, card, seen) for card in cards) if listing]
    if not found:
        raise NotRead(f"{dealer['host']}: no vehicle cards on /inventory")
    try:
        sitemap = get(f"{base}/sitemap.xml").decode("utf-8", "replace")
        listed = [address for address in re.findall(r"<loc>([^<]+)</loc>", sitemap) if re.search(r"/\d{5,}$", address)]
        complete = bool(listed) and len(listed) <= len(found)
    except Exception:                             # no sitemap: cannot tell, so do not claim a whole read
        complete = False
    return found, complete
