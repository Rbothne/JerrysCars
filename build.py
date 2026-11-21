"""Read every dealer that has a reader, update the catalogue, and write the page's data.

    py build.py

Reads dealers.json (from discover.py). Updates data/catalogue.db and writes site/data/cars.json.
A dealer whose read fails keeps what the catalogue already knew about it; the others carry on."""

import datetime
import json
import pathlib
import re
import sys

from cartrack import catalogue, cost, fetch, value, vin
from cartrack.listings import num
from cartrack.readers import READERS

ROOT = pathlib.Path(__file__).parent
ONLINE = {"carvana"}                              # platforms that deliver a car instead of keeping a lot to visit


def read_dealers(db, dealers, readers, get, now, say=print):
    """Read each dealer whose platform has a reader and record what it lists. Returns one report line a dealer.
    Cars missing from a read are marked gone only when the reader saw the dealer's whole inventory."""
    report = []
    for dealer in dealers:
        read = readers.get(dealer.get("platform"))
        if not (read and dealer.get("host")):
            continue
        line = {"dealer": dealer["key"], "platform": dealer["platform"], "ok": False, "read": 0, "new": 0,
                "gone": 0, "complete": None, "error": None}
        report.append(line)
        try:
            found, complete = read(dealer, get, now)
            outcomes = [catalogue.record(db, listing) for listing in found]
            line.update(read=len(found), new=outcomes.count("new"), complete=complete)
            if complete:
                line["gone"] = catalogue.close_out(db, dealer["host"], [listing["id"] for listing in found], now)
            line["ok"] = True
        except Exception as error:                # one dealer's trouble is reported, never the run's
            line["error"] = f"{type(error).__name__}: {error}"
        say(f"{dealer['key']:<34} {line['platform']:<16} "
            + (f"{line['read']:4d} read {line['new']:4d} new {line['gone']:3d} gone"
               + ("" if line["complete"] else "  (partial)") if line["ok"] else f"FAILED {line['error']}"))
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
    """What the car costs to drive away: the dealer's stated fees (None when it states none), Tennessee sales
    tax on price and fees, and the total. Title and registration are not in it."""
    stated = [num(amount) for amount in (extra.get("fees") or {}).values()]
    fees = int(sum(amount for amount in stated if amount)) or None
    tax = round(cost.tennessee_tax(row["price"] + (fees or 0)))
    return {"fees": fees, "tax": tax, "total": int(row["price"]) + (fees or 0) + tax}


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


def page_data(db, dealers, now, report=None, judge=value.judge):
    """What the page shows: every live car with a price, how long it has been for sale, and what its price
    has done. `was` and `drop` compare today's price with the first one the tracker saw. A car listed in
    several places is shown once, at its lowest price, with `places` saying how many. `typical` is what cars
    like it ask and `similar` how many that rests on (cartrack/value.py); both are None for a car not judged.
    `total` adds the dealer's stated fees and Tennessee sales tax; `per_year` is miles for each year on the road."""
    by_key = {dealer["key"]: dealer for dealer in dealers}
    decodes = {vin: json.loads(row) for vin, row in db.execute("SELECT vin, row_json FROM vin_decode")}
    vehicles = {}                                 # one physical car -> the listings of it; a group lists a car on each of its sites
    for row in db.execute("SELECT * FROM listing WHERE gone IS NULL AND price IS NOT NULL ORDER BY id").fetchall():
        points = [point[0] for point in db.execute(
            "SELECT price FROM price_point WHERE listing_id = ? AND price IS NOT NULL ORDER BY observed", (row["id"],))]
        first = points[0] if points else row["price"]
        drop = max(first - row["price"], 0)
        dealer = by_key.get(row["source"], {})
        photos = json.loads(row["photos"] or "[]")
        extra = json.loads(row["extra"] or "{}")
        years = max(int(now[:4]) - row["year"] + 1, 1) if row["year"] else None
        vehicles.setdefault(row["vehicle_id"], []).append({
            "id": row["id"], "title": row["title"], "url": row["url"],
            "price": row["price"], "was": first if drop else None, "drop": drop,
            "cuts": sum(1 for before, after in zip(points, points[1:]) if after < before),
            "days": _days(min(row["first_seen"], row["posted"] or row["first_seen"]), now),
            "first_seen": row["first_seen"],
            "year": row["year"], "make": row["make"], "model": row["model"], "trim": row["trim"],
            "body": row["body"], "drive": row["drive"], "miles": row["miles"], "color": row["color"], "vin": row["vin"],
            "per_year": row["miles"] // years if years and row["miles"] is not None else None,
            **_money(row, extra), **_past(extra),
            "fuel": _fuel(row["fuel"], decodes.get(row["vin"], {})),
            "kind": "online" if dealer.get("platform") in ONLINE else "lot",
            "dealer": row["seller_name"] if not dealer else dealer.get("name"), "dealer_key": row["source"],
            "dealer_miles": dealer.get("miles"), "city": row["city"], "state": row["state"],
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
    judged = judge([{**car, **_engine(decodes.get(car["vin"], {}))} for car in cars], int(now[:4]))
    for car in cars:
        car["typical"], car["similar"] = (judged.get(car["id"], {}).get(name) for name in ("typical", "similar"))
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
    (ROOT / "data").mkdir(exist_ok=True)
    db = catalogue.open_catalogue(ROOT / "data" / "catalogue.db")

    report = read_dealers(db, found["dealers"], READERS, fetch.paced(), now)
    try:
        print(f"{decode_vins(db, vin.decode, now)} VINs decoded")
    except Exception as error:                    # vPIC being down must not cost the run its listings
        print(f"VIN decoding skipped: {type(error).__name__}: {error}")

    data = page_data(db, found["dealers"], now, report)
    data["area"] = found["area"]
    db.close()
    (ROOT / "site" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "site" / "data" / "cars.json").write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(data['cars'])} cars on the page from {sum(1 for line in report if line['ok'])} of {len(report)} dealers")
    if report and not any(line["ok"] for line in report):
        sys.exit("every dealer failed")


if __name__ == "__main__":
    main()
