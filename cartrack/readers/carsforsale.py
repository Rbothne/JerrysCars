"""Carsforsale.com dealer websites ("Powered by Carsforsale.com", photos on cdn05.carsforsale.com).

`/cars-for-sale` is server-rendered with one schema.org Car block per vehicle (VIN, price, miles, photos,
detail address), 24 a page; `?Paging.Page=N` gives the next ones, and the page's description states the total
("Find 27 vehicles ..."). The platform answers a user agent containing "python-urllib" with a false
"500 Internal Server Error", so this reader sends the tracker's name without it. The Car block's offer price
is the figure the card labels "Price". No stock number or stock date is published. Seen working on
ezautomemphis.net, 2026-11-21: 27 stated, 27 read in 2 requests."""

import json
import re

from . import NotRead, dealer_listing, drive, site

PER_PAGE = 24
MAX_PAGES = 40
HEADERS = {"User-Agent": "cartrack/0.1"}      # "python-urllib" in the user agent gets a 500 from this platform


def _cars(page):
    cars = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Car":
            cars.append(data)
    return cars


def _drive(value):
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", (value or "").rsplit("/", 1)[-1])     # RearWheelDrive... -> Rear Wheel
    return "4wd" if "four wheel" in words.lower() else drive(words)


def _listing(dealer, car, seen):
    offer = car.get("offers") or {}
    url = offer.get("url") or car.get("url")
    ident = (url or "").rstrip("/").rsplit("/", 1)[-1] or car.get("vehicleIdentificationNumber")
    images = car.get("image") or []                # one address on the Car block; the gallery is a separate block
    images = images if isinstance(images, list) else [images]
    photos = [image.get("url") if isinstance(image, dict) else image for image in images]
    named = [car.get("name"), car.get("vehicleConfiguration")]
    return dealer_listing(
        dealer, ident, seen,
        url=url,
        title=" ".join(part for part in named if part),
        price=offer.get("price"),
        vin=car.get("vehicleIdentificationNumber"), year=car.get("modelDate"),
        make=(car.get("brand") or {}).get("name"), model=car.get("model"), trim=car.get("vehicleConfiguration"),
        body=car.get("bodyType"), drive=_drive(car.get("driveWheelConfiguration")), fuel=car.get("fuelType"),
        transmission=car.get("vehicleTransmission"), miles=(car.get("mileageFromOdometer") or {}).get("value"),
        color=car.get("color"), photos=photos, photo_count=len(photos))


def read(dealer, get, seen):
    first = f"{site(dealer)}/cars-for-sale"
    found, ids, stated = [], set(), None
    for number in range(1, MAX_PAGES + 1):
        page = get(first if number == 1 else f"{first}?Paging.Page={number}", headers=HEADERS).decode("utf-8", "replace")
        if stated is None:
            count = re.search(r"Find (\d+) vehicles", page)
            stated = int(count.group(1)) if count else None
        fresh = [car for car in (_listing(dealer, car, seen) for car in _cars(page)) if car and car["id"] not in ids]
        ids.update(car["id"] for car in fresh)
        found += fresh
        if not fresh or (stated is not None and len(found) >= stated):
            break
    if not found:
        raise NotRead(f"{dealer['host']}: no vehicles on /cars-for-sale")
    return found, stated is not None and len(found) >= stated
