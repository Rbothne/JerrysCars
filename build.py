"""Read every dealer and every other source that has a reader, update the catalogue, and write the page's data.

    py build.py

Reads dealers.json (from discover.py) and sources.json (hand-kept: the places that are not a dealer's own
website). Updates data/catalogue.db and writes site/data/cars.json. A dealer or source whose read fails keeps
what the catalogue already knew about it; the others carry on."""

import datetime
import json
import pathlib
import re
import sys

from cartrack import catalogue, cost, fetch, identify, value, vin
from cartrack.dealers import miles_between
from cartrack.listings import num
from cartrack.readers import READERS
from cartrack.sources import SOURCES

ROOT = pathlib.Path(__file__).parent
ONLINE = {"carvana"}                              # platforms that deliver a car instead of keeping a lot to visit


def _keep(db, key, platform, source, read, now, say, floor=catalogue.FLOOR):
    """Run one read and record what it found under `source`. Returns the report line for it."""
    line = {"dealer": key, "platform": platform, "ok": False, "read": 0, "new": 0, "gone": 0, "complete": None,
            "error": None}
    try:
        found, complete = read()
        outcomes = [catalogue.record(db, listing) for listing in found]
        line.update(read=len(found), new=outcomes.count("new"), complete=complete)
        if complete:
            line["gone"] = catalogue.close_out(db, source, [listing["id"] for listing in found], now, floor)
        line["ok"] = True
    except Exception as error:                    # one source's trouble is reported, never the run's
        line["error"] = f"{type(error).__name__}: {error}"
    say(f"{key:<34} {platform:<16} "
        + (f"{line['read']:4d} read {line['new']:4d} new {line['gone']:3d} gone"
           + ("" if line["complete"] else "  (partial)") if line["ok"] else f"FAILED {line['error']}"))
    return line


def read_dealers(db, dealers, readers, get, now, say=print):
    """Read each dealer whose platform has a reader and record what it lists. Returns one report line a dealer.
    Cars missing from a read are marked gone only when the reader saw the dealer's whole inventory."""
    return [_keep(db, dealer["key"], dealer["platform"], dealer["host"],
                  lambda: readers[dealer["platform"]](dealer, get, now), now, say)
            for dealer in dealers if dealer.get("platform") in readers and dealer.get("host")]


def read_sources(db, places, readers, get, now, say=print):
    """Read each place in sources.json whose kind has a reader, and report it the way a dealer is reported.
    The reader is told which of the place's listings the catalogue already holds in full (the ones with a
    posted time, which only a listing's own page gives), so it asks for each listing's page once. A place
    may set its own `floor`: classifieds turn over faster than a dealer's lot."""
    report = []
    for place in places:
        read = readers.get(place.get("kind"))
        if not read:
            continue
        known = {row[0] for row in db.execute(
            "SELECT source_id FROM listing WHERE source = ? AND posted IS NOT NULL", (place["key"],))}
        report.append(_keep(db, place["key"], place["kind"], place["key"],
                            lambda: read(place, get, now, known=known), now, say,
                            place.get("floor", catalogue.FLOOR)))
    return report


def decode_vins(db, decode, now):
    """Ask vPIC about every VIN it has not been asked about, and keep the answers. Returns how many came back."""
    todo = catalogue.undecoded(db)
    if not todo:
        return 0
    rows = decode(todo)
    catalogue.save_decodes(db, rows, now)
    return len(rows)


def _days(since, now):
    return (datetime.date.fromisoformat(now[:10]) - datetime.date.fromisoformat(since[:10])).days


def _fuel(listed, decoded):
    """What the car runs on, in the page's four words. The listing says petrol for a hybrid; the VIN knows better."""
    level = decoded.get("ElectrificationLevel") or ""
    listed = (listed or "").lower()
    if "BEV" in level or "electric" in listed:
        return "electric"
    if "HEV" in level:
        return "hybrid"
    if "diesel" in listed:
        return "diesel"
    return "gas" if "gas" in listed or "flex" in listed else None


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _money(row, extra):
    """What the car costs. `price` is the asking price with the dealer's stated fees in it, because that is what
    the buyer pays before tax and what some dealers advertise (Jim Keras does; Jimmy Gray shows the fee
    apart). `base` is the price without them, `fees` their sum (None when the dealer states none), `tax`
    Tennessee sales tax on `price`, and `total` the two together. Title and registration are not in it."""
    stated = [num(amount) for amount in (extra.get("fees") or {}).values()]
    fees = int(sum(amount for amount in stated if amount)) or None
    price = int(row["price"]) + (fees or 0)
    tax = round(cost.tennessee_tax(price))
    return {"price": price, "base": int(row["price"]), "fees": fees, "tax": tax, "total": price + tax}


def _past(extra):
    """What the listing says beyond the car itself: the free history report, Carfax's badge, certification,
    fuel economy, warranty left, and whether the seller says the car is not ready yet."""
    report = extra.get("history_url") or ""
    return {"history": report if report.startswith("https://www.carfax.com/") else None,
            "one_owner": extra.get("one_owner"), "carfax_value": extra.get("carfax_value"),
            "certified": extra.get("certified"), "mpg": extra.get("mpg"), "warranty": extra.get("warranty"),
            "waiting": bool(extra.get("reservable") or extra.get("in_transit"))}


def _engine(decoded):
    """What the VIN adds for the value judgement: series, engine size and weight class."""
    weight = re.search(r"Class (\d)", decoded.get("GVWR") or "")
    return {"series": decoded.get("Series"), "cylinders": _number(decoded.get("EngineCylinders")),
            "litres": _number(decoded.get("DisplacementL")), "weight_class": weight.group(1) if weight else None}


def _away(row, dealer, area):
    """(miles from the home point, whether that came from the listing's own pin and not a dealer's lot)."""
    if dealer.get("miles") is not None:
        return dealer["miles"], False
    if area and row["lat"] is not None and row["lon"] is not None:
        return round(miles_between(area["home"], (row["lat"], row["lon"])), 1), True
    return None, False


def page_data(db, dealers, now, report=None, judge=value.judge, places=(), area=None):
    """What the page shows: every live car with a price, how long it has been for sale, and what its price
    has done. `price` includes the dealer's stated fees. `was` and `drop` compare today's price with the first
    one the tracker saw. A car listed in
    several places is shown once, at its lowest price, with `places` saying how many. `typical` is what cars
    like it ask and `similar` how many that rests on (cartrack/value.py); both are None for a car not judged.
    `total` adds the dealer's stated fees and Tennessee sales tax; `per_year` is miles for each year on the road.

    `places` are the rows of sources.json and `area` the home point and radius. A car from a place carries
    `seller` ("private"), `where` (the seller's word for the neighbourhood, else the city) and its distance
    from its own map pin; one pinned outside the radius is left off. `title_status` is what the seller says
    of the title. A car whose title is not clean is shown but not judged, and is not used to judge others."""
    by_key = {dealer["key"]: dealer for dealer in (*dealers, *places)}
    decodes = {vin: json.loads(row) for vin, row in db.execute("SELECT vin, row_json FROM vin_decode")}
    vehicles = {}                                 # one physical car -> the listings of it; a group lists a car on each of its sites
    for row in db.execute("SELECT * FROM listing WHERE gone IS NULL AND price IS NOT NULL ORDER BY id").fetchall():
        points = [point[0] for point in db.execute(
            "SELECT price FROM price_point WHERE listing_id = ? AND price IS NOT NULL ORDER BY observed", (row["id"],))]
        first = points[0] if points else row["price"]
        drop = max(first - row["price"], 0)
        dealer = by_key.get(row["source"], {})
        away, pinned = _away(row, dealer, area)
        if pinned and away > area["radius_miles"]:
            continue
        on_lot = row["channel"] == "dealer_site"
        photos = json.loads(row["photos"] or "[]")
        extra = json.loads(row["extra"] or "{}")
        years = max(int(now[:4]) - row["year"] + 1, 1) if row["year"] else None
        money = _money(row, extra)
        vehicles.setdefault(row["vehicle_id"], []).append({
            "id": row["id"], "title": row["title"], "url": row["url"],
            "was": first + (money["fees"] or 0) if drop else None, "drop": drop,
            "cuts": sum(1 for before, after in zip(points, points[1:]) if after < before),
            "days": _days(min(row["first_seen"], row["posted"] or row["first_seen"]), now),
            "first_seen": row["first_seen"],
            "year": row["year"], "make": row["make"], "model": row["model"], "trim": row["trim"],
            "body": row["body"], "drive": row["drive"], "miles": row["miles"], "color": row["color"], "vin": row["vin"],
            "per_year": row["miles"] // years if years and row["miles"] is not None else None,
            **money, **_past(extra),
            "fuel": _fuel(row["fuel"], decodes.get(row["vin"], {})),
            "kind": "online" if dealer.get("platform") in ONLINE else "private" if row["seller_type"] == "private" else "lot",
            "seller": row["seller_type"] or ("dealer" if on_lot else None),
            "title_status": row["title_status"],
            "where": None if on_lot else extra.get("where") or row["city"],
            "dealer": row["seller_name"] if not dealer else dealer.get("name"), "dealer_key": row["source"],
            "dealer_miles": away, "city": row["city"], "state": row["state"],
            "photo": photos[0] if photos else None,
        })
    cars = sorted(({**min(listed, key=lambda car: car["price"]), "places": len(listed)} for listed in vehicles.values()),
                  key=lambda car: car["id"])
    by_dealer = {}
    for car in cars:
        by_dealer.setdefault(car["dealer_key"], []).append(car)
    for lot in by_dealer.values():                # a dealer that calls every car certified is saying nothing
        if len(lot) > 1 and all(car["certified"] is True for car in lot):
            for car in lot:
                car["certified"] = None
    sound = {car["id"] for car in cars if car["title_status"] in (None, "clean")}
    judged = judge([{**car, **_engine(decodes.get(car["vin"], {}))} for car in cars if car["id"] in sound], int(now[:4]))
    for car in cars:
        fair = judged.get(car["id"], {}) if car["id"] in sound else {}
        car["typical"], car["similar"] = (fair.get(name) for name in ("typical", "similar"))
    counts = {}
    for car in cars:
        counts[car["dealer_key"]] = counts.get(car["dealer_key"], 0) + 1
    return {
        "built": now,
        "cars": cars,
        "dealers": [{"key": line["dealer"], "name": by_key.get(line["dealer"], {}).get("name"),
                     "cars": counts.get(line["dealer"], 0), "ok": line["ok"]} for line in report or []],
    }


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
    found = json.loads((ROOT / "dealers.json").read_text(encoding="utf-8"))
    places = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    (ROOT / "data").mkdir(exist_ok=True)
    db = catalogue.open_catalogue(ROOT / "data" / "catalogue.db")

    get = fetch.paced()
    report = read_sources(db, places, SOURCES, get, now) + read_dealers(db, found["dealers"], READERS, get, now)
    try:
        print(f"{decode_vins(db, vin.decode, now)} VINs decoded")
    except Exception as error:                    # vPIC being down must not cost the run its listings
        print(f"VIN decoding skipped: {type(error).__name__}: {error}")
    print(f"{identify.fill(db)} listings named from their sellers' words")

    data = page_data(db, found["dealers"], now, report, places=places, area=found["area"])
    data["area"] = found["area"]
    db.close()
    (ROOT / "site" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "site" / "data" / "cars.json").write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(data['cars'])} cars on the page from {sum(1 for line in report if line['ok'])} of {len(report)} sources")
    if report and not any(line["ok"] for line in report):
        sys.exit("every source failed")


if __name__ == "__main__":
    main()
