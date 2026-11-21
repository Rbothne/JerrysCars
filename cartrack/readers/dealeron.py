"""DealerOn: the used-inventory page names the dealer and page ids, and a JSON service then lists every car.

Two kinds of request, no login: `/searchused.aspx` once, then the service the page itself calls, 96 cars a
request. DealerOn sites ask for a 3 second crawl delay; the caller's `get` keeps it. Seen working on
jimkerasnissan.com, 2026-11-20 (research/02-endpoints-dealers-reference.md, section 1.1)."""

import base64
import json
import re
import urllib.parse

from . import NotRead, dealer_listing, drive, site

PAGE = 96                  # the largest page size the site's own menu offers
MAX_PAGES = 40
ASKING = ("Selling Price", "Internet Price", "calc_INTERNET PRICE")   # first one present is the asking price
FEES = {"calc_Dealer Doc Fee": "Dealer Doc Fee", "dealer_fee": "Dealer Fee"}   # price-stack lines that are added on top


def _prices(library):
    """The card's price stack, sent as base64 of "name:amount;name:amount"."""
    try:
        pairs = base64.b64decode(library or "").decode("utf-8", "replace").split(";")
    except ValueError:
        return {}
    prices = {}
    for pair in pairs:
        name, _, amount = pair.rpartition(":")
        try:
            prices[name] = float(amount)
        except ValueError:
            continue
    return prices


def _listing(dealer, base, card, seen):
    prices = _prices(card.get("VehiclePriceLibrary"))
    photo = (card.get("VehicleImageModel") or {}).get("VehiclePhotoSrc")
    photo = base + photo if photo and photo.startswith("/") else photo
    price = next((prices[name] for name in ASKING if prices.get(name)), None) or card.get("TaggingPrice")
    stocked = re.fullmatch(r"(\d{4})/(\d{2})/(\d{2})", card.get("VehicleTaggingInventoryDate") or "")
    named = [card.get("VehicleYear"), card.get("VehicleMake"), card.get("VehicleModel"), card.get("VehicleTrim")]
    return dealer_listing(
        dealer, card.get("VehicleVin") or card.get("VehicleStockNumber"), seen,
        url=card.get("VehicleDetailUrl"),
        title=" ".join(str(part) for part in named if part),
        price=price,
        posted="-".join(stocked.groups()) + "T00:00" if stocked else None,
        vin=card.get("VehicleVin"), year=card.get("VehicleYear"), make=card.get("VehicleMake"),
        model=card.get("VehicleModel"), trim=card.get("VehicleTrim"), body=card.get("VehicleBodyType"),
        drive=drive(card.get("VehicleDriveTrain")), engine=card.get("VehicleEngine"),
        fuel=card.get("VehicleFuelType"), transmission=card.get("VehicleTransmission"),
        miles=card.get("VehicleMileage"), color=card.get("ExteriorColorLabel"),
        photos=[photo] if photo else [], photo_count=card.get("VehiclePhotoCount") or 0,
        extra={"stock": card.get("VehicleStockNumber"), "prices": prices,
               "fees": {label: int(prices[name]) for name, label in FEES.items() if prices.get(name)}})


def read(dealer, get, seen):
    base = site(dealer)
    host = urllib.parse.urlparse(base).netloc
    page = get(f"{base}/searchused.aspx").decode("utf-8", "replace")
    dealer_id = re.search(r'"?DealerId"?\s*:\s*"?(\d+)', page)
    page_id = re.search(r'"?PageId"?\s*:\s*"?(\d+)', page)
    if not (dealer_id and page_id):
        raise NotRead(f"{host}: no DealerId and PageId on the used-inventory page")
    service = f"{base}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{dealer_id.group(1)}/{page_id.group(1)}"

    found, number = [], 1
    while True:
        answer = json.loads(get(f"{service}?host={host}&pn={PAGE}&pt={number}", headers={"Accept": "application/json"}))
        paging = answer["Paging"]["PaginationDataModel"]
        for card in answer.get("DisplayCards") or []:
            listing = _listing(dealer, base, card["VehicleCard"], seen) if card.get("VehicleCard") else None
            if listing:
                found.append(listing)
        if number >= paging["TotalPages"] or number >= MAX_PAGES:
            break
        number += 1
    return found, len(found) >= paging["TotalCount"]
