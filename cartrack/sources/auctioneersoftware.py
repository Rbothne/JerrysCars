"""Auction houses whose bidding site runs on Auctioneer Software: first, the City of Memphis impound auction.

Venture Auctions sells the city's impounded vehicles every Wednesday, about 60 a week, and since May 2026 does
it on its own site, www.venture-auctions.com. Every page answers a plain request with its data in the page,
as `window.__APOLLO_STATE__`: `Auction.<id>` and `AuctionLot.<id>` records.

- `/auctions` lists the sales that are open or coming, `/past-auctions` (and `?page=2`...) the finished ones,
  twenty a page, newest first, with the total.
- A sale's own address (its `public_url`, and `?page=2`...) gives its lots, 25 a page, with the total.

A lot states its year, make and model, its full VIN and the city's ticket number, a photo, the bids so far and,
once the sale is over, what it sold for. It never states mileage, keys, whether it runs, or the title: nobody
has looked. So a lot has no asking price and cannot be set beside cars for sale. Before the sale its price is
the bid so far ("bid") or the opening figure ("starting"), and `ends` is when the sale starts: lots have no
closing time of their own, they are called one a minute. Afterwards the price is the hammer price ("sold"),
or the last bid on a lot the auctioneer marked no-sale ("reserve_not_met"), and `ends` is when it was called.

A finished sale never changes, so each is read once: `known` holds the lots already recorded as over, and a
sale with any lot among them is skipped. The first runs work back through the earlier sales a few at a time.
Lots that are not vehicles (the quarterly surplus sale also sells equipment) are left out.

robots.txt disallows /api/, /asset/ and any ?search, ?filter, ?sort or ?pageSize; none is used. The site
answers a request that follows a redirect at once with 429, so only the addresses the pages themselves give
are asked for. What an open lot shows once prebidding starts was not seen when this was written (the next
sale's lots were not up): it is read as the sister site showed it, the bid so far in `winning_bid_amount`.
Seen 2026-11-21: the 18 November sale, 78 lots in four pages, 76 sold, median $575."""

import datetime
import json
import re

from .. import fetch
from ..listings import make_listing
from ..readers import NotRead, text

PAST_PER_RUN = 10      # finished sales read in one run; the rest wait for the next
MAX_PAGES = 12         # of one sale's lots, or of the list of finished sales
OVER = (300, 400)      # auction_status of a sale that has finished
_MARK = "window.__APOLLO_STATE__ = "
_FAILED = (OSError, ValueError, NotRead)


def _state(page, where):
    at = page.find(_MARK)
    if at < 0:
        raise NotRead(f"{where}: no page data")
    try:
        return json.JSONDecoder().raw_decode(page, at + len(_MARK))[0]
    except ValueError as error:
        raise NotRead(f"{where}: the page data is not JSON") from error


def _one(record, start):
    """The value of the one key of `record` that starts with `start` (Apollo keys carry their arguments)."""
    return next((value for key, value in record.items() if key.startswith(start)), None)


def _sales(get, address):
    """(the sales listed at `address`, how many the site says there are in all)."""
    state = _state(get(address).decode("utf-8", "replace"), address)
    found = _one(state.get("ROOT_QUERY") or {}, "auctions(")
    if found is None:
        raise NotRead(f"{address}: no list of sales")
    return [state[entry["__ref"]] for entry in found.get("auctions") or []], found.get("total") or 0


def _lots(get, sale):
    """Every lot of one sale, each with the sale's own record beside it."""
    lots, ids = [], set()
    for number in range(1, MAX_PAGES + 1):
        address = sale["public_url"] + (f"?page={number}" if number > 1 else "")
        state = _state(get(address).decode("utf-8", "replace"), address)
        record = _one(state.get("ROOT_QUERY") or {}, "auction(")
        found = _one(state[record["__ref"]], "lots(") if record else None
        if found is None:
            raise NotRead(f"{address}: no list of lots")
        fresh = [state[entry["__ref"]] for entry in found.get("lots") or []]
        fresh = [lot for lot in fresh if lot["auction_lot_id"] not in ids]
        ids.update(lot["auction_lot_id"] for lot in fresh)
        lots += fresh
        if not fresh or len(lots) >= (found.get("total") or 0):
            break
    return lots


def _utc(stamp):
    """The site's time ("2026-11-18T15:47:56.108Z") as the catalogue keeps times: UTC, to the minute."""
    if not stamp:
        return None
    return datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")


def _listing(place, sale, lot, seen):
    said = text(lot.get("description")) or ""
    vin = re.search(r"VIN#\s*([A-Za-z0-9]{17})\b", said)
    kind = ((lot.get("category") or {}).get("name") or "").upper()
    if not (vin or kind.startswith("VEHICLE")):
        return None                                   # a mower, a pallet of radios
    facts = {field.get("label"): (field.get("data") or {}).get("value") for field in lot.get("dynamic_fields") or []}
    ticket = re.search(r"(?:VMS|CITY) ID#\s*(\S+)", said)
    over, bids = sale.get("auction_status") in OVER, lot.get("bid_count") or 0
    if over:
        price, price_kind = lot.get("winning_bid_amount"), "reserve_not_met" if lot.get("is_no_sale") else "sold"
    else:
        price, price_kind = (lot.get("winning_bid_amount"), "bid") if bids else (lot.get("starting_bid"), "starting")
    image = lot.get("primary_image") or {}
    photo = image.get("large") or image.get("url")
    extra = {"auction": sale.get("title"), "auction_id": sale.get("auction_id"), "lot": lot.get("lot_number"),
             "ticket": ticket.group(1) if ticket else None, "bids": bids, "watchers": lot.get("watch_count"),
             "no_sale": True if over and lot.get("is_no_sale") else None}
    return make_listing(
        place["key"], f"{sale['auction_id']}-{lot['auction_lot_id']}", seen=seen, channel="auction",
        url=lot.get("public_url"), title=" ".join((lot.get("title") or "").split()),
        price=price, price_kind=price_kind, ends=_utc(lot.get("end_time") if over else sale.get("start_time")),
        vin=vin.group(1) if vin else None, year=facts.get("YEAR"), make=facts.get("MAKE"), model=facts.get("MODEL"),
        title_status="parts_only" if "PARTS ONLY" in (lot.get("title") or "").upper() else None,
        seller_name=place.get("name"), city=place.get("city"), state=place.get("state"), zip=place.get("zip"),
        lat=place.get("lat"), lon=place.get("lon"), geo_how="street" if place.get("lat") is not None else None,
        photos=[photo] if photo else [], photo_count=lot.get("image_count"),
        extra={name: value for name, value in extra.items() if value is not None})


def read(place, get, seen, known=(), limit=PAST_PER_RUN):
    base = place["site"].rstrip("/")
    recorded = {key.split("-")[0] for key in known}
    found, complete = [], True

    coming, _ = _sales(get, f"{base}/auctions")       # a failure here is the whole read's: nothing can be said
    for sale in coming:
        try:
            lots = _lots(get, sale)
        except (fetch.RateLimited, *_FAILED):
            complete = False                          # part of what is for sale was not seen: mark nothing gone
            continue
        found += [made for made in (_listing(place, sale, lot, seen) for lot in lots) if made]

    todo, listed = [], 0
    try:
        for number in range(1, MAX_PAGES + 1):
            sales, total = _sales(get, f"{base}/past-auctions" + (f"?page={number}" if number > 1 else ""))
            listed += len(sales)
            todo += [sale for sale in sales if sale["auction_id"] not in recorded]
            if not sales or listed >= total or len(todo) >= limit or len(recorded) >= total:
                break
        for sale in todo[:limit]:
            try:
                lots = _lots(get, sale)
            except _FAILED:
                complete = False                      # this sale is left out whole, and read on a later run
                continue
            found += [made for made in (_listing(place, sale, lot, seen) for lot in lots) if made]
    except (fetch.RateLimited, *_FAILED):
        complete = False                              # asked to slow down, or the list would not load: enough for this run
    return found, complete
