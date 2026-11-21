"""Carvana: the search service behind carvana.com/cars, asked for the cars it delivers free to a Memphis ZIP.

Carvana's stock is national. Its own search pages (/cars, /vehicle/...) sit behind a Cloudflare challenge, but
the JSON service those pages call, apik.carvana.io, answers a plain request. Two kinds of request, no login,
no cookie: the distance service once (miles from the ZIP to every Carvana location), then the search, 100 cars
a request, filtered to free delivery to the ZIP. Every car in that set is priced with no shipping fee, so its
asking price is what a Memphis buyer pays before tax and registration. Each car says which Carvana location it
is kept at; the location's distance is kept beside it. Seen working from a home connection, 2026-11-21:
1,899 cars in 19 requests (research/08-routing-carvana.md)."""

import json
import re

from . import NotRead
from ..listings import make_listing

API = "https://apik.carvana.io"
SEARCH = f"{API}/merch/search/api/v2/search"
DISTANCE = f"{API}/merch/carvanamerchcontextapi/api/v3/distance?zip5="
PHOTOS = "https://cdnblob.fastly.carvana.io"
HOME_ZIP = "38103"                 # downtown Memphis: the buyer's ZIP every delivery figure is worked out for
FREE_DELIVERY = {"isFreeDelivery": True}
PAGE = 100                         # the most the service serves; asked for more, it sends 24 and says nothing
MAX_PAGES = 94                     # the service refuses page x size of 9,500 or more ("Invalid Request", 400)
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# Carvana location id -> (city, state, ZIP), as the car's own page names it. Only places seen are listed.
LOCATIONS = {
    131: ("West Memphis", "AR", "72301"),        # 1100 Family Dollar Dr, on /vehicle/4895072, 2026-11-21
    294: ("Old Hickory", "TN", "37138"),         # 631 Burnett Rd (Nashville), on /vehicle/4935695 and 4892269
}
INVENTORY = {0: "unknown", 1: "dealer_marketplace", 2: "partner_retail", 3: "carvana"}   # fulfillmentType


def _when(stamp):
    found = re.match(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})", stamp or "")
    return f"{found.group(1)}T{found.group(2)}" if found else None


def _whole(value):
    return int(round(value)) if isinstance(value, (int, float)) else None


def _warranty(car):
    """What is left of the maker's warranty, as [months, miles] for each part still covered. None when none is."""
    left = {name: [car.get(f"remaining{part}WarrantyMonths") or 0, car.get(f"remaining{part}WarrantyMiles") or 0]
            for name, part in (("basic", ""), ("drivetrain", "DriveTrain"))}
    return {name: pair for name, pair in left.items() if pair[0] > 0 and pair[1] > 0} or None


def _listing(dealer, car, miles, seen):
    price = car.get("price") or {}
    place = LOCATIONS.get(car.get("locationId"), (None, None, None))
    image = car.get("imageUrl") or ""
    photo = PHOTOS + image if image.startswith("/") else image or car.get("standardizedHero")
    named = [car.get("year"), car.get("make"), car.get("model"), car.get("trim")]
    return make_listing(
        dealer["host"], car.get("vehicleId"), seen=seen, channel="dealer_site", seller_type="dealer",
        seller_id=dealer["host"], seller_name=dealer.get("name"),
        url=f"https://www.carvana.com/vehicle/{car.get('vehicleId')}",
        title=" ".join(str(part) for part in named if part),
        price=price.get("total"), updated=_when(car.get("priceUpdateDate")),
        vin=car.get("vin"), year=car.get("year"), make=car.get("make"), model=car.get("model"), trim=car.get("trim"),
        body=car.get("bodyStyle"), fuel=car.get("fuelType"), miles=car.get("mileage"), color=car.get("color"),
        city=place[0], state=place[1], zip=place[2],
        photos=[photo] if photo else [],
        extra={
            "stock": car.get("stockNumber"),
            "location_id": car.get("locationId"),
            "location_miles": miles.get(str(car.get("locationId"))),
            "shipping": _whole(price.get("transportCost")),
            "kbb": _whole(price.get("kbbValue")),
            "msrp": _whole(price.get("msrp")),
            "previous_price": _whole(car.get("previousPrice")),
            "reservable": car.get("vehiclePurchaseType") == "Reservable",
            "warranty": _warranty(car),
            "inventory": INVENTORY.get(car.get("fulfillmentType")),
        })


def search(get, filters, zip5=HOME_ZIP):
    """Every car the search service lists for `filters` and `zip5`, and whether that was all it counted."""
    cars, seen_ids, number, whole = [], set(), 1, True
    while True:
        body = {"zip5": zip5, "filters": filters, "pagination": {"page": number, "pageSize": PAGE},
                "sortBy": "MostPopular", "requestedFeatures": ["ExcludeFacetData"]}
        try:
            answer = json.loads(get(SEARCH, data=json.dumps(body).encode(), headers=HEADERS))
            inventory = answer["inventory"]
            paging, vehicles = inventory["pagination"], inventory.get("vehicles") or []
        except (ValueError, KeyError, TypeError) as error:
            raise NotRead(f"carvana: the search service answered without an inventory ({error!r})") from error
        last = number >= paging["totalMatchedPages"] or number >= MAX_PAGES or not vehicles
        if len(vehicles) < PAGE and not last:
            whole = False                       # a short page in the middle: the service served less than it said
        for car in vehicles:
            if car.get("vehicleId") not in seen_ids:
                seen_ids.add(car.get("vehicleId"))
                cars.append(car)
        if last:
            break
        number += 1
    return cars, whole and len(cars) >= paging["totalMatchedInventory"]


def read(dealer, get, seen):
    miles = json.loads(get(DISTANCE + HOME_ZIP, headers={"Accept": "application/json"})).get("locationDistances") or {}
    cars, complete = search(get, FREE_DELIVERY)
    found = [listing for listing in (_listing(dealer, car, miles, seen) for car in cars) if listing]
    return found, complete and len(found) == len(cars)
