"""Craigslist cars and trucks for sale by owner.

`https://<site>.craigslist.org/search/cto` answers a plain request with every result in the page itself
(`li.cl-static-search-result`: title, price, the seller's word for the neighbourhood, and the listing's
address). The last part of that address names the listing and did not change between reads. Everything
else is on the listing's own page, so each listing is asked for once: year, the make and model as the seller
typed them, odometer, title status, fuel, transmission, body, and where given drive, colour, condition,
cylinders and VIN; the map pin; the posted and updated times; and a schema.org block with the photos, city,
state and ZIP. The seller's description and phone number are not kept.

Make and model stay as typed in `extra.makemodel`: sellers write "chevy silverado lt 4x4", and
cartrack/identify.py names it from the models the catalogue already knows. A VIN, when a seller gives one,
settles it instead.

Sellers type the odometer in thousands often enough to matter ("180" on a 2011). On a car more than three
years old, 10 to 400 is read as thousands and anything else under 1,000 is left blank; `extra.odometer`
keeps what was typed whenever it was not taken as it stood.

The search page stops at about 360 results. A site with that many is asked again in price bands (the page
honours `min_price` and `max_price`, both ends included: seen 2026-11-21), so every listing is still seen and
the read is whole unless one band alone is as long as the page.

robots.txt allows /search and /view. Craigslist's terms of use forbid collecting its listings by program
without a licence; this reads one search page a run and each listing once, at the build's three-second pace.
Seen working on memphis.craigslist.org, 2026-11-21: 120 results on the page, 13 listing pages read."""

import datetime
import json
import re

from .. import fetch
from ..listings import make_listing, num
from ..readers import CARDS_READ, NotRead, drive, text

MAX_DETAILS = 150      # listing pages asked for in one run; the rest wait for the next
FULL_PAGE = 300        # the search page stops somewhere past this many results, so a page this long may be cut short
OLD = 3                # years after which an odometer under 1,000 is not believed as typed
BANDS = ((None, 2999), (3000, 5999), (6000, 9999), (10000, 19999), (20000, None))     # dollars, both ends included
_TITLES = {"clean": "clean", "salvage": "salvage", "rebuilt": "rebuilt", "parts only": "parts_only",
           "lien": "lien", "missing": "missing"}
_FAILED = (OSError, ValueError)                    # a listing page that would not load, or made no sense


def _results(page, host):
    """The search page's results, in its order: key, url, title, price and the seller's word for the place.
    Raises NotRead when most results give no listing address: the page has changed, and the few that still
    match are not the site's cars."""
    rows, items = [], re.findall(r'<li class="cl-static-search-result"[^>]*>(.*?)</li>', page, re.S)
    for item in items:
        link = re.search(r'href="(https://[^"]+/view/d/[^"]*/([^/"]+))"', item)
        if not link:
            continue
        part = {name: text(match.group(1)) if match else None for name, match in (
            (name, re.search(rf'<div class="{name}">(.*?)</div>', item, re.S)) for name in ("title", "price", "location"))}
        rows.append({"key": link.group(2), "url": link.group(1), **part})
    if len(rows) < CARDS_READ * len(items):
        raise NotRead(f"{host}: only {len(rows)} of {len(items)} results name a listing")
    return rows


def _search(get, host, full_page):
    """(every result of the site's by-owner search, whether that is all of them)."""
    address = f"https://{host}/search/cto"
    rows = _results(get(address).decode("utf-8", "replace"), host)
    if len(rows) < full_page:
        return rows, True
    by_key, whole = {row["key"]: row for row in rows}, True
    for low, high in BANDS:                           # the page was cut short: ask again a price band at a time
        bounds = [f"{name}={value}" for name, value in (("min_price", low), ("max_price", high)) if value is not None]
        band = _results(get(f"{address}?{'&'.join(bounds)}").decode("utf-8", "replace"), host)
        whole = whole and len(band) < full_page
        for row in band:
            by_key.setdefault(row["key"], row)
    return list(by_key.values()), whole


def _utc(stamp):
    """A listing's own time ("2026-11-21T11:10:31-0600") as the catalogue keeps times: UTC, to the minute."""
    if not stamp:
        return None
    moment = datetime.datetime.fromisoformat(stamp)
    return moment.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M") if moment.tzinfo else None


def _odometer(typed, year, this_year):
    """(miles, what was typed when it was not taken as it stood)."""
    miles = num(typed)
    if miles is None or miles >= 1000 or not year or year > this_year - OLD:
        return miles, None
    return (miles * 1000 if 10 <= miles <= 400 else None), typed


def _details(page, this_year):
    """What a listing's own page says, as make_listing's fields."""
    attrs = {}
    for block in re.findall(r'<div class="attr [^"]*">(.*?)</div>', page, re.S):
        label = re.search(r'<span class="labl">(.*?)</span>', block, re.S)
        value = re.search(r'<span class="valu[^"]*">(.*?)</span>', block, re.S)
        if label and value:
            attrs[(text(label.group(1)) or "").rstrip(":").lower()] = text(value.group(1))
    year = num((re.search(r'<span class="valu year">\s*(\d{4})', page) or [None, None])[1])
    typed = re.search(r'<span class="valu makemodel">(.*?)</span>', page, re.S)
    miles, as_typed = _odometer(attrs.get("odometer"), year, this_year)
    when = dict(re.findall(r'<p class="postinginfo[^"]*">\s*(posted|updated):\s*<time[^>]*datetime="([^"]+)"', page))
    post = re.search(r"post id:\s*(\d+)", page)
    pin = re.search(r'id="map"[^>]*data-latitude="([-\d.]+)"[^>]*data-longitude="([-\d.]+)"', page)

    block = re.search(r'<script[^>]*id="ld_posting_data"[^>]*>(.*?)</script>', page, re.S)
    try:
        product = json.loads(block.group(1)) if block else {}
    except ValueError:
        product = {}
    place = ((product.get("offers") or {}).get("availableAtOrFrom") or {})
    address, geo = place.get("address") or {}, place.get("geo") or {}
    photos = product.get("image") or []
    lat, lon = (pin.group(1), pin.group(2)) if pin else (geo.get("latitude"), geo.get("longitude"))

    extra = {"post_id": post.group(1) if post else None, "makemodel": text(typed.group(1)) if typed else None,
             "cylinders": int(num(attrs.get("cylinders"))) if num(attrs.get("cylinders")) else None, "odometer": as_typed}
    return {
        "year": year, "miles": miles, "vin": attrs.get("vin"),
        "title_status": _TITLES.get((attrs.get("title status") or "").lower()),
        "fuel": attrs.get("fuel"), "transmission": attrs.get("transmission"), "body": attrs.get("type"),
        "drive": drive(attrs.get("drive")), "color": attrs.get("paint color"), "condition": attrs.get("condition"),
        "city": address.get("addressLocality"), "state": address.get("addressRegion"), "zip": address.get("postalCode"),
        "lat": lat, "lon": lon, "geo_how": "pin" if lat and lon else None,
        "posted": _utc(when.get("posted")), "updated": _utc(when.get("updated")),
        "photos": photos if isinstance(photos, list) else [photos],
        "extra": {name: value for name, value in extra.items() if value is not None},
    }


def read(place, get, seen, known=(), limit=MAX_DETAILS, full_page=FULL_PAGE):
    host = f"{place['site']}.craigslist.org"
    rows, whole = _search(get, host, full_page)
    if not rows:
        raise NotRead(f"{host}: no results on /search/cto")
    found, asked, slowed = [], 0, False
    for row in rows:
        facts = {}
        if row["key"] not in known and asked < limit and not slowed:
            asked += 1
            try:
                facts = _details(get(row["url"]).decode("utf-8", "replace"), int(seen[:4]))
            except fetch.Gone:
                continue                              # taken down since the search page was written
            except fetch.RateLimited:
                slowed = True                         # asked to slow down: the rest wait for the next run
            except _FAILED:
                pass                                  # this one is tried again next run; `posted` stays empty until then
        extra = facts.pop("extra", {})
        if facts and row["location"]:
            extra["where"] = row["location"]
        listing = make_listing(
            place["key"], row["key"], url=row["url"], title=row["title"], price=row["price"], seen=seen,
            channel="classified", seller_type="private", extra=extra, **facts)
        if listing:
            found.append(listing)
    return found, whole
