"""Read every dealer and every other source that has a reader, update the catalogue, and write the page's data.

    py build.py

Reads dealers.json (from discover.py) and sources.json (hand-kept: the places that are not a dealer's own
website). Updates data/catalogue.db and writes site/data/cars.json. A dealer or source whose read fails keeps
what the catalogue already knew about it; the others carry on."""

import concurrent.futures
import datetime
import functools
import json
import pathlib
import re
import statistics
import sys

from cartrack import catalogue, cost, fetch, identify, value, vin
from cartrack.dealers import miles_between
from cartrack.listings import num
from cartrack.readers import READERS
from cartrack.sources import SOURCES

ROOT = pathlib.Path(__file__).parent
ONLINE = {"carvana"}                              # platforms that deliver a car instead of keeping a lot to visit
OWN_IDS = 0.8          # a read where fewer than this share of the listings have an id of their own was read wrongly
WORKERS = 32           # sources read at the same time; each site still gets one request at a time (fetch.paced)
ONE_COMPANY = ("craigslist.org",)                 # every host under these is paced as a single site
BRANDED = ("rebuilt", "salvage", "lien")          # titles that are priced against clean cars and never the other way
OVER = {"sold": "sold", "reserve_not_met": "ended_unsold"}     # a price that is a sale's result -> how the listing ended
NEAR_YEARS = 3         # model years either side that count as the same car when auction lots are set beside others
# What a private seller's own title says about why the car is cheap. Only the title is read: the description
# is not kept. "needs nothing" is not a warning, and "rebuilt" alone usually means an engine, so only a title is.
CAUTIONS = (
    ("mechanic special", r"mechanic'?s?\s+special"),
    ("as-is", r"\bas[\s-]+is\b"),
    ("needs work", r"\bneeds?\b(?!\s+nothing)"),
    ("not running", r"\bnot\s+running\b|\b(?:won'?t|wont|doesn'?t|does\s+not|will\s+not)\s+(?:start|run)\b|\bnon[\s-]?running\b|\bno\s+start\b"),
    ("for parts", r"\bfor\s+parts\b|\bparts\s+(?:only|car)\b"),
    ("blown", r"\bblown\b"),
    ("project", r"\bproject\b"),
    ("no title", r"\bno\s+title\b|\bbill\s+of\s+sale\b"),
    ("salvage", r"\bsalvage\b"),
    ("rebuilt title", r"\brebuilt\s+title\b"),
)


def _keep(db, key, platform, source, read, now, say, floor=catalogue.FLOOR):
    """Run one read and record what it found under `source`. Returns the report line for it.

    Two things a read can get wrong without failing are caught here. A reader that takes the wrong thing for
    a listing's id gives many listings the same one, and they would overwrite each other down to a handful:
    such a read is refused. And a read that is never quite whole, or that shrank for good, marks nothing
    gone: so a listing no read has found for three days is let go whatever the reads called themselves."""
    line = {"dealer": key, "platform": platform, "ok": False, "read": 0, "new": 0, "gone": 0, "complete": None,
            "error": None}
    try:
        found, complete = read()
        listed = {listing["id"]: listing for listing in found}
        if len(listed) < OWN_IDS * len(found):
            raise ValueError(f"{len(found)} listings share {len(listed)} ids")
        outcomes = [catalogue.record(db, listing) for listing in listed.values()]
        for listing in listed.values():               # an auction's result: the lot is over, and says how
            if listing["price_kind"] in OVER:
                catalogue.end(db, listing["id"], listing["ends"] or now, OVER[listing["price_kind"]])
        line.update(read=len(listed), new=outcomes.count("new"), complete=complete)
        line["gone"] = catalogue.age_out(db, source, now)
        if complete:
            line["gone"] += catalogue.close_out(db, source, list(listed), now, floor)
        line["ok"] = True
    except Exception as error:                    # one source's trouble is reported, never the run's
        line["error"] = f"{type(error).__name__}: {error}"
    say(f"{key:<34} {platform:<16} "
        + (f"{line['read']:4d} read {line['new']:4d} new {line['gone']:3d} gone"
           + ("" if line["complete"] else "  (partial)") if line["ok"] else f"FAILED {line['error']}"))
    return line


def dealer_jobs(dealers, readers, get, now):
    """One read to run for each dealer whose platform has a reader."""
    return [{"key": dealer["key"], "platform": dealer["platform"], "source": dealer["host"], "floor": catalogue.FLOOR,
             "read": functools.partial(readers[dealer["platform"]], dealer, get, now)}
            for dealer in dealers if dealer.get("platform") in readers and dealer.get("host")]


def source_jobs(db, places, readers, get, now):
    """One read to run for each place in sources.json whose kind has a reader. The reader is told which of the
    place's listings the catalogue already holds in full: the ones with a posted time, which only a listing's
    own page gives, and the auction lots recorded as over. So it asks for each listing's page, and each
    finished sale, once. A place may set its own `floor`: classifieds turn over faster than a dealer's lot,
    and every lot of an auction goes at once."""
    jobs = []
    for place in places:
        read = readers.get(place.get("kind"))
        if not read:
            continue
        known = {row[0] for row in db.execute(
            "SELECT source_id FROM listing WHERE source = ? AND (posted IS NOT NULL OR gone_how IN ('sold', 'ended_unsold'))",
            (place["key"],))}
        jobs.append({"key": place["key"], "platform": place["kind"], "source": place["key"],
                     "floor": place.get("floor", catalogue.FLOOR),
                     "read": functools.partial(read, place, get, now, known=known)})
    return jobs


def run(db, jobs, now, say=print, workers=1):
    """Run the reads and record what each found. Returns one report line a job, in the order given.

    With `workers` above one, the reads are all started together, a thread each, and this waits for them in
    order. Only the asking is done side by side; the catalogue is written here, one source at a time. So a
    run takes as long as its slowest site, not as long as all of them added up, and no site is asked any
    faster for it: the `get` the readers share (fetch.paced) still gives each site one request at a time."""
    def keep(job, read):
        return _keep(db, job["key"], job["platform"], job["source"], read, now, say, job["floor"])
    if workers <= 1 or len(jobs) <= 1:
        return [keep(job, job["read"]) for job in jobs]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, len(jobs))) as pool:
        waiting = [pool.submit(job["read"]) for job in jobs]
        return [keep(job, wait.result) for job, wait in zip(jobs, waiting)]


def read_dealers(db, dealers, readers, get, now, say=print, workers=1):
    """Read each dealer whose platform has a reader and record what it lists. Returns one report line a dealer.
    Cars missing from a read are marked gone only when the reader saw the dealer's whole inventory."""
    return run(db, dealer_jobs(dealers, readers, get, now), now, say, workers)


def read_sources(db, places, readers, get, now, say=print, workers=1):
    """Read each place in sources.json whose kind has a reader, and report it the way a dealer is reported."""
    return run(db, source_jobs(db, places, readers, get, now), now, say, workers)


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


def cautions(title):
    """The warnings in a private seller's title, in CAUTIONS' own order: ["mechanic special", "as-is"]."""
    return [name for name, pattern in CAUTIONS if re.search(pattern, title or "", re.I)]


def _away(row, dealer, area):
    """Miles from the home point: the dealer's lot, else the listing's own map pin, else unknown."""
    if dealer.get("miles") is not None:
        return dealer["miles"]
    if area and row["lat"] is not None and row["lon"] is not None:
        return round(miles_between(area["home"], (row["lat"], row["lon"])), 1)
    return None


def page_data(db, dealers, now, report=None, judge=value.judge, places=(), area=None):
    """What the page shows: every live car with a price, how long it has been for sale, and what its price
    has done. `price` includes the dealer's stated fees. `was` and `drop` compare today's price with the first
    one the tracker saw. A car listed in
    several places is shown once, at its lowest price, with `places` saying how many. `typical` is what cars
    like it ask and `similar` how many that rests on (cartrack/value.py); both are None for a car not judged.
    `total` adds the dealer's stated fees and Tennessee sales tax; `per_year` is miles for each year on the road.

    `places` are the rows of sources.json and `area` the home point. A car from a place carries `seller`
    ("private"), `where` (the seller's word for the neighbourhood, else the city) and, as `dealer_miles`, its
    distance from its own map pin. No car is left off for being far: the page filters by distance. A listing
    without a VIN that two places both show (one address) is one car. `title_status` is what the seller says
    of the title, and `cautions` what the seller's own title warns of ("mechanic special", "as-is").
    `basis`, `window`, `low` and `high` say what a car's `typical` stands on (cartrack/value.py). A car with a
    rebuilt, salvage or lien title is priced against clean cars and is never one of the cars others are
    priced from; one for parts, with no title, or with a caution gets no figure at all. A private car posted again by its seller (the same year, mileage, price and map pin, and no VIN
    to tell by) is one car, shown once."""
    by_key = {dealer["key"]: dealer for dealer in (*dealers, *places)}
    decodes = {vin: json.loads(row) for vin, row in db.execute("SELECT vin, row_json FROM vin_decode")}
    vehicles = {}                                 # one physical car -> the listings of it; a group lists a car on each of its sites
    addresses = {}                                # a listing's address -> the car it was first taken for
    for row in db.execute("SELECT * FROM listing WHERE gone IS NULL AND price IS NOT NULL AND price_kind = 'ask' "
                          "ORDER BY id").fetchall():   # an auction lot's bid is not an asking price: auction_data shows those
        points = [point[0] for point in db.execute(
            "SELECT price FROM price_point WHERE listing_id = ? AND price IS NOT NULL ORDER BY observed", (row["id"],))]
        first = points[0] if points else row["price"]
        drop = max(first - row["price"], 0)
        dealer = by_key.get(row["source"], {})
        away = _away(row, dealer, area)
        on_lot = row["channel"] == "dealer_site"
        vehicle = row["vehicle_id"] if row["vin"] else addresses.setdefault(row["url"], row["vehicle_id"])
        if not row["vin"] and not on_lot and None not in (row["year"], row["miles"], row["lat"], row["lon"]):
            again = ("posted again", row["year"], row["miles"], row["price"], row["lat"], row["lon"])
            vehicle = addresses.setdefault(again, vehicle)
        photos = json.loads(row["photos"] or "[]")
        extra = json.loads(row["extra"] or "{}")
        years = max(int(now[:4]) - row["year"] + 1, 1) if row["year"] else None
        money = _money(row, extra)
        vehicles.setdefault(vehicle, []).append({
            "id": row["id"], "title": row["title"], "url": row["url"],
            "also": [],
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
            "cautions": [] if on_lot else cautions(row["title"]),
            "where": None if on_lot else extra.get("where") or row["city"],
            "dealer": row["seller_name"] if not dealer else dealer.get("name"), "dealer_key": row["source"],
            "dealer_miles": away, "city": row["city"], "state": row["state"],
            "photo": photos[0] if photos else None,
        })
    cars = []
    for listed in vehicles.values():                  # shown once, where it costs least, and counted for every seller of it
        best = min(listed, key=lambda car: car["price"])
        others = sorted({car["dealer_key"] for car in listed} - {best["dealer_key"]})
        cars.append({**best, "places": len(listed), "also": others})
    cars.sort(key=lambda car: car["id"])
    by_dealer = {}
    for car in cars:
        by_dealer.setdefault(car["dealer_key"], []).append(car)
    for lot in by_dealer.values():                # a dealer that calls every car certified is saying nothing
        if len(lot) > 1 and all(car["certified"] is True for car in lot):
            for car in lot:
                car["certified"] = None
    sound = {car["id"] for car in cars if car["title_status"] in (None, "clean") and not car["cautions"]}
    apart = {car["id"] for car in cars if car["title_status"] in BRANDED and not car["cautions"]}
    judged = judge([{**car, **_engine(decodes.get(car["vin"], {})), "apart": car["id"] in apart} for car in cars
                    if car["id"] in sound or car["id"] in apart], int(now[:4]))
    for car in cars:
        fair = judged.get(car["id"], {}) if car["id"] in sound or car["id"] in apart else {}
        for name in ("typical", "similar", "basis", "window", "low", "high"):
            car[name] = fair.get(name)
    counts = {}
    for car in cars:
        for seller in (car["dealer_key"], *car["also"]):
            counts[seller] = counts.get(seller, 0) + 1
    return {
        "built": now,
        "cars": cars,
        "dealers": [{"key": line["dealer"], "name": by_key.get(line["dealer"], {}).get("name"),
                     "cars": counts.get(line["dealer"], 0), "ok": line["ok"]} for line in report or []],
    }


def _middle(prices):
    """{"count", "median", "low", "high"} of some prices, or None when there are none."""
    if not prices:
        return None
    return {"count": len(prices), "median": int(statistics.median(prices)), "low": min(prices), "high": max(prices)}


def auction_data(db, places, now):
    """What the auction page shows. `lots` are the lots of sales not yet held; `results` every lot of the sales
    that are over, newest first. A lot states no mileage and no condition, so it is not judged the way a car
    for sale is. Beside each coming lot go the facts that can be had: `before`, what the same make and model
    within three model years fetched at these sales; `asks`, what such cars are asking around here today;
    and `back`, when this very car (by VIN) was in an earlier sale and how that ended. `places` carries each
    auction's own charges, so the page can say what a bid costs."""
    rows = db.execute("SELECT * FROM listing WHERE channel = 'auction' AND price_kind != 'ask' ORDER BY id").fetchall()
    coming = [row for row in rows if row["gone"] is None]
    over = [row for row in rows if row["gone_how"] in ("sold", "ended_unsold")]
    fetched, asked, earlier = {}, {}, {}
    for row in over:
        if row["gone_how"] == "sold" and row["price"] and row["year"] and row["make"] and row["model"]:
            fetched.setdefault((row["make"], row["model"]), []).append((row["year"], row["price"]))
        if row["vin"]:
            earlier.setdefault(row["vin"], []).append(row)
    for year, make, model, price in db.execute(
            "SELECT year, make, model, price FROM listing WHERE gone IS NULL AND price_kind = 'ask' AND price IS NOT NULL "
            "AND year IS NOT NULL AND make IS NOT NULL AND model IS NOT NULL"):
        asked.setdefault((make, model), []).append((year, price))

    def near(table, row):
        return [price for year, price in table.get((row["make"], row["model"]), ())
                if row["year"] and abs(year - row["year"]) <= NEAR_YEARS]

    def lot(row):
        extra, photos = json.loads(row["extra"] or "{}"), json.loads(row["photos"] or "[]")
        return {"id": row["id"], "title": row["title"], "url": row["url"], "photo": photos[0] if photos else None,
                "year": row["year"], "make": row["make"], "model": row["model"], "vin": row["vin"],
                "price": row["price"], "kind": row["price_kind"], "bids": extra.get("bids"), "ends": row["ends"],
                "auction": extra.get("auction"), "lot": extra.get("lot"), "place": row["source"],
                "parts_only": row["title_status"] == "parts_only"}

    lots = []
    for row in coming:
        last = max(earlier.get(row["vin"], ()), key=lambda one: one["gone"], default=None)
        lots.append({**lot(row), "before": _middle(near(fetched, row)), "asks": _middle(near(asked, row)),
                     "back": {"when": last["gone"][:10], "price": last["price"], "sold": last["gone_how"] == "sold"}
                             if last else None})
    results = sorted(({**lot(row), "sold": row["gone_how"] == "sold"} for row in over),
                     key=lambda one: (one["ends"] or "", one["id"]), reverse=True)
    return {"built": now, "lots": lots, "results": results,
            "places": [{"key": place["key"], "name": place.get("name"), "premium": place.get("premium"),
                        "fee": place.get("fee"), "card": place.get("card")}
                       for place in places if place.get("kind") in ("auctioneersoftware",)]}


def funnel(db, data, auctions=None):
    """For each source with live listings: how many it has, how many of those carry a usable price, and how
    many cars on the page are its own or shared with it (for an auction, how many lots its page shows). A
    source that reads well and shows nothing looks, on the page, exactly like a source with no cars; this is
    where the difference can be seen."""
    shown = {}
    for car in data["cars"]:
        for seller in (car["dealer_key"], *car["also"]):
            shown[seller] = shown.get(seller, 0) + 1
    for lot in (auctions or {}).get("lots", ()):
        shown[lot["place"]] = shown.get(lot["place"], 0) + 1
    return [{"source": source, "live": live, "priced": priced, "shown": shown.get(source, 0)}
            for source, live, priced in db.execute(
                "SELECT source, count(*), count(price) FROM listing WHERE gone IS NULL GROUP BY source ORDER BY source")]


def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")
    found = json.loads((ROOT / "dealers.json").read_text(encoding="utf-8"))
    places = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    (ROOT / "data").mkdir(exist_ok=True)
    db = catalogue.open_catalogue(ROOT / "data" / "catalogue.db")

    get = fetch.paced(shared=ONE_COMPANY)
    jobs = source_jobs(db, places, SOURCES, get, now) + dealer_jobs(found["dealers"], READERS, get, now)
    report = run(db, jobs, now, workers=WORKERS)
    try:
        print(f"{decode_vins(db, vin.decode, now)} VINs decoded")
    except Exception as error:                    # vPIC being down must not cost the run its listings
        print(f"VIN decoding skipped: {type(error).__name__}: {error}")
    print(f"{identify.fill(db)} listings named from their sellers' words")

    data = page_data(db, found["dealers"], now, report, places=places, area=found["area"])
    data["area"] = found["area"]
    auctions = auction_data(db, places, now)
    print(f"{len(auctions['lots'])} auction lots coming up, {len(auctions['results'])} results on record")
    print(f"{'source':<34} {'live':>5} {'priced':>6} {'on page':>7}")
    for line in funnel(db, data, auctions):
        print(f"{line['source']:<34} {line['live']:5d} {line['priced']:6d} {line['shown']:7d}"
              + ("   <- none of its cars reach the page" if line["live"] and not line["shown"] else ""))
    db.close()
    (ROOT / "site" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "site" / "data" / "cars.json").write_text(json.dumps(data, separators=(",", ":")) + "\n", encoding="utf-8")
    (ROOT / "site" / "data" / "auctions.json").write_text(json.dumps(auctions, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(data['cars'])} cars on the page from {sum(1 for line in report if line['ok'])} of {len(report)} sources")
    if report and not any(line["ok"] for line in report):
        sys.exit("every source failed")


if __name__ == "__main__":
    main()
