"""Team Velocity (Apollo sites): the site's own used-inventory JSON feed, then one search page for the photos.

`/inventory-used.json` is the feed the site's llms.txt names: 50 cars a page, `totalVehicles`, `nextPage`,
and per car the VIN, stock number, identity, miles, `dateInStock`, `sellingPrice` and the group store that
holds it. The feed has no photos (`imageUrls` is null), so `/inventory/used?limit=N` is asked once for the
whole search page, whose schema.org Vehicle blocks carry each car's picture.

The sites sit behind Fastly, which answers 406 with an empty body to a user agent without "Mozilla/5.0"
whenever its cache misses, so every request here sends `UA`. Seen working on gossettmotorcars.net,
gossettmotors.com and infinitiofmemphis.com, 2026-11-21 (research/08-routing-teamvelocity-dealerfire.md)."""

import json
import re

from . import NotRead, dealer_listing, drive, site

UA = "Mozilla/5.0 (compatible; cartrack/0.1)"
MAX_PAGES = 40
_LD = re.compile(r'<script type="application/ld(?:&#x2B;|\+)json">\s*(.*?)\s*</script>', re.S)


def _page_cars(page):
    """{VIN: schema.org Vehicle block} from a search page."""
    cars = {}
    for block in _LD.findall(page):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "Vehicle" and data.get("vehicleIdentificationNumber"):
            cars[data["vehicleIdentificationNumber"].upper()] = data
    return cars


def _number(value):
    try:
        return float(value) or None
    except (TypeError, ValueError):
        return None


def _listing(dealer, car, shown, seen):
    offer = (shown or {}).get("offers") or {}
    page_price = _number(offer.get("price"))
    photo = ((shown or {}).get("image") or {}).get("contentUrl")
    store = car.get("dealerName")
    seller = {**dealer, "name": store or dealer.get("name"), "zip": car.get("dealerZip") or dealer.get("zip"),
              "city": car.get("dealerCity") or dealer.get("city"), "state": car.get("dealerState") or dealer.get("state")}
    if store and store != dealer.get("name"):
        seller.update(lat=None, lon=None)          # the dealer row's point is its own store, not this one
    stocked = re.match(r"\d{4}-\d{2}-\d{2}", car.get("dateInStock") or "")
    named = [car.get("year"), car.get("make"), car.get("model"), car.get("trim")]
    return dealer_listing(
        seller, car.get("vin") or car.get("stockNumber"), seen,
        url=car.get("vdpUrl") or (shown or {}).get("url"),
        title=" ".join(str(part) for part in named if part),
        price=_number(car.get("sellingPrice")) or page_price,
        posted=stocked.group() + "T00:00" if stocked else None,
        vin=car.get("vin"), year=car.get("year"), make=car.get("make"), model=car.get("model"), trim=car.get("trim"),
        body=car.get("bodyStyle"), drive=drive(car.get("driveTrain")), engine=car.get("engine"),
        fuel=car.get("fuelType"), transmission=car.get("transmission"), miles=car.get("miles"),
        color=car.get("exteriorColor"), photos=[photo] if photo else [],
        extra={"stock": car.get("stockNumber"), "store": store, "msrp": _number(car.get("msrp")),
               "page_price": page_price, "certified": bool(car.get("certified")), "in_transit": bool(car.get("inTransit"))})


def read(dealer, get, seen):
    base = site(dealer)
    headers = {"User-Agent": UA, "Accept": "application/json"}
    cars, number, total, pages = [], 1, 0, 1
    while True:
        address = f"{base}/inventory-used.json" + (f"?page={number}" if number > 1 else "")
        try:
            answer = json.loads(get(address, headers=headers))
        except ValueError:
            raise NotRead(f"{dealer['host']}: /inventory-used.json is not JSON") from None
        if number == 1:
            total, pages = answer.get("totalVehicles") or 0, answer.get("totalPages") or 0
        cars += answer.get("vehicles") or []
        if not answer.get("nextPage") or number >= pages or number >= MAX_PAGES:
            break
        number += 1
    if not cars:
        raise NotRead(f"{dealer['host']}: the used-inventory feed lists no cars")

    try:                                              # photos only: the cars stand without them
        shown = _page_cars(get(f"{base}/inventory/used?limit={max(total, len(cars))}",
                               headers={"User-Agent": UA}).decode("utf-8", "replace"))
    except Exception:
        shown = {}

    found, vins = [], set()
    for car in cars:
        vin = (car.get("vin") or "").upper()
        if vin in vins:
            continue
        vins.add(vin)
        listing = _listing(dealer, car, shown.get(vin), seen)
        if listing:
            found.append(listing)
    return found, len(found) >= total
