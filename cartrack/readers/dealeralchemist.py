"""Dealer Alchemist (formerly DealerVenom; WordPress theme "dv-framework"): the used-vehicles page names a
Typesense Cloud search service, its search-only key and the dealer group's collection; one POST then lists 250
cars with everything on them.

The key is the one the page itself sends from every visitor's browser. The service needs no cookie, origin or
browser user agent. A group site lists all its lots; only the lots in the dealer's own city are kept, so a
group with stores in other states is not counted as a Memphis dealer. `internetPrice` is the asking price;
`finalPrice` adds the dealer's processing fee and is kept in `extra`. `age` is days on the lot. Seen working on
cityauto.com, 2026-11-21: 844 used cars counted and read in 4 requests, 451 of them at the Memphis lot."""

import datetime
import json
import re

from . import NotRead, dealer_listing, drive, site
from ..listings import num

PAGE = 250                 # the most Typesense gives in one page
MAX_PAGES = 20


def _settings(page):
    host = re.search(r'__tsHost\s*=\s*"([^"]+)"', page) or re.search(r"host:\s*'([a-z0-9.-]+\.typesense\.net)'", page)
    key = re.search(r'__tsApiKey\s*=\s*"([^"]+)"', page) or re.search(r'apiKey:\s*"([^"]+)"', page)
    index = re.search(r'var indexName\s*=\s*"([^"]+)"', page)
    if not (host and key and index):
        return None
    return host.group(1), key.group(1), index.group(1).split("/")[0]


def _stocked(seen, age):
    try:
        day = datetime.date.fromisoformat(seen[:10]) - datetime.timedelta(days=int(age))
    except (TypeError, ValueError):
        return None
    return day.isoformat() + "T00:00"


def _listing(dealer, base, car, seen):
    price = num(car.get("internetPrice"))
    shown = num(car.get("finalPriceInt") or car.get("finalPrice"))
    fees = {fee.get("name"): fee.get("amount") for fee in car.get("dealerFees") or [] if not fee.get("isDiscount")}
    lot = car.get("dealer") or {}
    return dealer_listing(
        dealer, car.get("vin") or car.get("stockNumber"), seen,
        url=base + car["vdpUrl"] if (car.get("vdpUrl") or "").startswith("/") else car.get("vdpUrl"),
        title=car.get("vehicleTitle"),
        price=price or None,
        posted=_stocked(seen, car.get("age")),
        vin=car.get("vin"), year=car.get("yr") or car.get("year"), make=car.get("make"), model=car.get("model"),
        trim=car.get("trim"), body=car.get("body"), drive=drive(car.get("drivetrain")), engine=car.get("engine"),
        fuel=car.get("fuel"), transmission=car.get("transmission"), miles=car.get("mileage"),
        color=car.get("exteriorColor"), photos=car.get("imageUrls") or [], photo_count=len(car.get("imageUrls") or []),
        extra={"stock": car.get("stockNumber"), "shown_price": int(shown) if shown else None, "fees": fees,
               "lot": lot.get("name") or car.get("dealerName"), "certified": car.get("certified")})


def read(dealer, get, seen):
    base = site(dealer)
    settings = _settings(get(f"{base}/used-vehicles/").decode("utf-8", "replace"))
    if not settings:
        raise NotRead(f"{dealer['host']}: no search service named on /used-vehicles/")
    host, key, index = settings
    service = f"https://{host}/multi_search?x-typesense-api-key={key}"
    city = (dealer.get("city") or "").strip().lower()

    found, read_count, total = [], 0, None
    for number in range(1, MAX_PAGES + 1):
        question = {"searches": [{"collection": index, "q": "*", "filter_by": "condition:Used",
                                  "per_page": PAGE, "page": number}]}
        answer = json.loads(get(service, data=json.dumps(question).encode(), headers={"Content-Type": "text/plain"}))
        result = (answer.get("results") or [{}])[0]
        if "error" in result or "found" not in result:
            raise NotRead(f"{dealer['host']}: the search service said {result.get('error') or 'nothing'}")
        total, hits = result["found"], result.get("hits") or []
        read_count += len(hits)
        for hit in hits:
            car = hit.get("document") or {}
            if city and ((car.get("dealer") or {}).get("city") or "").strip().lower() != city:
                continue                                 # another lot of the same group
            listing = _listing(dealer, base, car, seen)
            if listing:
                found.append(listing)
        if not hits or number * PAGE >= total:
            break
    if not found:                  # nothing at all, or no lot in the dealer's city: never an empty "whole" lot
        raise NotRead(f"{dealer['host']}: no used cars at a lot in {dealer.get('city') or 'any city'}")
    return found, total is not None and read_count >= total
