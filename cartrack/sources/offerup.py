"""OfferUp: cars and trucks for sale around one city.

`https://offerup.com/c/cars-and-trucks/in/{city}` (and `?page=2`...) holds its results in the page, in
`script#__NEXT_DATA__` under `props.pageProps.searchFeedResponse.looseTiles`: 50 a page, newest first, within
OfferUp's 30 miles of the city whatever address the request comes from. Memphis held about 1,000 on
2026-11-21, about 21 pages; a page past the end is empty. robots.txt allows these pages and disallows search
words, sorting and filters, so none is used. **OfferUp's terms forbid collecting its listings by program** (its
terms of 21 July 2026); this reader is here because the owner chose to read it anyway, and it asks for one city's
pages once a run, three seconds apart (research/11-routing-more-marketplaces.md).

A card gives a title, a price, a town, often the mileage, and one photo. It does not say who is selling, when it
was posted, the VIN, or anything about the car's condition, and its own page (not read) sits behind a challenge.
So the seller is guessed, and `extra.seller_guessed` says so:

- a paid seller tile (`AD_1P`), or a price in whole dollars that is not a round fifty (`20591`): a dealer's
  stock fed in by a program. 73 of 200 cards on 2026-11-21, median $25,141;
- a price that is a round fifty (`3500`): a private seller, mostly. 87 of 200, median $4,000;
- a price with cents (`2499.00`): either, so it is left unsaid, unless it ends in 95 or 99, a lot's price.

The title is free text ("2012 Toyota Camry", "Chevy Caprice"): the year at its front is taken, and the rest
goes to `extra.makemodel` for cartrack/identify.py to name. Tiles that are not listings (display adverts) are
left out. A card has no map point, so a car is placed at the middle of the city searched (`lat` and `lon` on the
place's row), which OfferUp's 30 miles reach beyond: its distance is rough."""

import json
import re

from ..listings import make_listing, num
from ..readers import NotRead

MAX_PAGES = 50         # the site's own limit on how far its pages go
_DATA = re.compile(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', re.S)
_YEAR = re.compile(r"^\s*((?:19|20)\d\d)\b\s*(.*)$")


def _tiles(page, address):
    found = _DATA.search(page)
    if not found:
        raise NotRead(f"{address}: no page data")
    try:
        props = json.loads(found.group(1))["props"]["pageProps"]
        return props["searchFeedResponse"]["looseTiles"] or []
    except (ValueError, KeyError, TypeError) as error:
        raise NotRead(f"{address}: the page data holds no results ({error!r})") from error


def _seller(tile, price):
    """(seller type or None, as guessed from the tile and how its price is written)."""
    if tile.get("tileType") == "AD_1P":
        return "dealer"
    written = str(price or "")
    if "." in written:
        whole = written.split(".")[0]
        return "dealer" if whole[-2:] in ("95", "99") else None
    dollars = num(written)
    if dollars is None:
        return None
    return "private" if dollars % 50 == 0 else "dealer"


def _listing(place, tile, seen):
    car = tile.get("listing") or {}
    title = " ".join((car.get("title") or "").split())
    year = _YEAR.match(title)
    where = [part.strip() for part in (car.get("locationName") or "").split(",")]
    image = car.get("image")
    photo = image.get("url") if isinstance(image, dict) else image
    point = car.get("approximateLocation") or {}
    extra = {"makemodel": year.group(2) if year else title, "seller_guessed": True, "tile": tile.get("tileType")}
    return make_listing(
        place["key"], car.get("listingId"), seen=seen, channel="marketplace",
        url=f"https://offerup.com/item/detail/{car.get('listingId')}", title=title, price=car.get("price"),
        seller_type=_seller(tile, car.get("price")), year=year.group(1) if year else None, miles=car.get("vehicleMiles"),
        city=where[0] if where and where[0] else None, state=where[1] if len(where) > 1 else None,
        lat=point.get("latitude") if isinstance(point, dict) and point.get("latitude") is not None else place.get("lat"),
        lon=point.get("longitude") if isinstance(point, dict) and point.get("longitude") is not None else place.get("lon"),
        geo_how="city",                               # the card's own point when it has one, else the city searched
        photos=[photo] if photo else [], extra=extra)


def read(place, get, seen, known=()):
    base = f"https://offerup.com/c/cars-and-trucks/in/{place['site']}"
    found, ids, complete = [], set(), False
    for number in range(1, MAX_PAGES + 1):
        address = base + (f"?page={number}" if number > 1 else "")
        page = get(address).decode("utf-8", "replace")
        tiles = [tile for tile in _tiles(page, address) if isinstance(tile, dict) and tile.get("listing")]
        fresh = [car for car in (_listing(place, tile, seen) for tile in tiles) if car and car["id"] not in ids]
        ids.update(car["id"] for car in fresh)
        found += fresh
        if not tiles or 'rel="next"' not in page:
            complete = True                           # the last page: everything the city holds has been seen
            break
        if not fresh:
            break                                     # a full page of nothing new: the site is repeating itself
    if not found:
        raise NotRead(f"{base}: no listings")
    return found, complete
