"""DealerFire (DealerSocket): the used search page is server-rendered and carries one JSON object per car.

`/inventory?isNew=0&limit=100&offset=N` is the platform's own address for the used search (the page then
names its local alias, e.g. /used-vehicles-memphis-tn). Each car is pushed to the page's data layer as
`VehicleObject_{id}` with VIN, stock, identity, mileage, price figures, `dateInStock` and the main photo, and
the listing element states the total in `data-total-items`. Plain requests, no cookies needed. robots.txt asks
for a 10 second crawl delay. Seen working on jr-autosales.com, 2026-11-21, 26 of 26 cars in one request."""

import json
import re

from . import NotRead, dealer_listing, drive, history, site

PAGE = 100                 # asked for; the next page starts after however many came back
MAX_PAGES = 20
PRICES = ("finalPrice", "internetPrice", "sellingPrice", "originalPrice", "MSRP", "NADARetailPrice", "blueBook")
_OBJECT = re.compile(r"pushData\('VehicleObject_\d+', (\{.*?\})\); \}\);</script>")


def _photo(url):
    return "https:" + url if url and url.startswith("//") else url


def _listing(dealer, base, car, seen):
    photo = _photo(car.get("mainImageUrl"))
    stock_art = photo if photo and "/chrome/" in photo else None   # Chrome Data's maker picture, not this car
    stocked = re.match(r"\d{4}-\d{2}-\d{2}", (car.get("dateInStock") or {}).get("date") or "")
    named = [car.get("year"), car.get("make"), car.get("model"), car.get("trim")]
    url = car.get("vdp") or (f"{base}/{car['seoUrl']}" if car.get("seoUrl") else None)
    extra = {"stock": car.get("stockNumber"), "prices": {name: car.get(name) for name in PRICES if car.get(name)},
             "days_in_stock": car.get("daysInStock")}
    if stock_art:
        extra["stock_art"] = stock_art
    report = car.get("carfaxReport") or {}
    extra.update(history(" ".join(str(part) for part in report.values())))
    if isinstance(report.get("isOneOwner"), bool):
        extra["one_owner"] = report["isOneOwner"]
    return dealer_listing(
        dealer, car.get("vuid"), seen,
        url=url, title=" ".join(str(part) for part in named if part),
        price=car.get("finalPrice") or car.get("internetPrice") or car.get("sellingPrice"),
        posted=stocked.group() + "T00:00" if stocked else None,
        vin=car.get("vin"), year=car.get("year"), make=car.get("make"), model=car.get("model"), trim=car.get("trim"),
        body=car.get("bodyStyle") or car.get("body"), drive=drive(car.get("drivetrain")),
        engine=car.get("engineDescription"), fuel=car.get("fuelType"), transmission=car.get("transmission"),
        miles=car.get("mileage"), color=car.get("exteriorColor") or None,
        photos=[photo] if photo and not stock_art else [],
        photo_count=0 if stock_art or not photo else car.get("photoCount") or 1,
        extra=extra)


def read(dealer, get, seen):
    base = site(dealer)
    found, seen_ids, total, offset = [], set(), None, 0
    for _ in range(MAX_PAGES):
        page = get(f"{base}/inventory?isNew=0&limit={PAGE}&offset={offset}").decode("utf-8", "replace")
        if total is None:
            counted = re.search(r'data-total-items="(\d+)"', page) or re.search(r"'FilteredVehiclesCount', (\d+)", page)
            total = int(counted.group(1)) if counted else None
        cars = []
        for blob in _OBJECT.findall(page):
            try:
                cars.append(json.loads(blob))
            except ValueError:
                continue
        fresh = [car for car in cars if car.get("vuid") not in seen_ids]
        for car in fresh:
            seen_ids.add(car.get("vuid"))
            if car.get("isNew"):
                continue
            listing = _listing(dealer, base, car, seen)
            if listing:
                found.append(listing)
        offset += len(cars)                 # by what came back, in case the site serves fewer than asked
        if not fresh or total is None or len(seen_ids) >= total:
            break
    if not found:
        raise NotRead(f"{dealer['host']}: no vehicle objects on the used search page")
    return found, total is not None and len(found) >= total
