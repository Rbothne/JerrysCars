"""What a car like this one usually asks, worked out from the other cars in the catalogue.

Two estimates, and the lower one is kept, so a car is only called cheap when both agree:

1. A price model over every car: year, mileage, make, model, trim words, body, drive, fuel, engine and weight
   class, and whether a private seller is asking (a ridge regression on the log of the price). Each car is
   priced by a model fitted without it.
2. The car's own neighbours: the same model within two years and 30,000 miles, each one's asking price moved
   to this car's year, mileage and kind of seller, and the median taken.

Every figure says what it stands on, because they are not equally good (research/11-valuing-old-cars.md):

- "close": three or more neighbours within two years and 30,000 miles.
- "wide": none that close, but three within 3 years and 45,000 miles, or 4 and 60,000, or 6 and 90,000.
- "rough": no neighbours at all, so the model's figure alone. Worth showing, never worth a mark.

`low` and `high` are where six in ten asking prices fell around such a figure when this was measured.

Three things here exist for private sellers' cars, which are older and cheaper than what the lots hold:

- A private seller asks less than a dealer, and the gap widens with the car's age (6% at two years old, 31% at
  eleven, half at twenty-one), except on pickups. Two terms say so. Without them the model learned it by
  accident: a private car has no decoded VIN, so its engine fields were blank, and "blank" came to mean cheap.
- So a car that lacks its engine size, cylinders, weight class, drive or body takes the commonest value among
  cars of its own make and model before anything is fitted.
- Age and mileage are capped where the curve is made (30 years, 300,000 miles), so one odometer typed as
  1,824,979 cannot bend it for everyone.

A car marked `apart` (a rebuilt, salvage or lien title) is priced against the others but teaches the model
nothing and is nobody's neighbour: its figure says what a clean one asks.

How well this does on the Memphis catalogue is in research/09-value.md and research/11-valuing-old-cars.md. It
is a guide to where to look, not an appraisal: no listing states condition, and condition decides the price
of a cheap car."""

import math
import re
import statistics
import zlib

MIN_MARKET = 200          # fewer cars than this and the model would be describing noise
MIN_SIMILAR = 3
FOLDS = 5
LADDER = ((2, 30000), (3, 45000), (4, 60000), (6, 90000))     # (years, miles) either side; the first is "close"
MAX_AGE, MAX_MILES = 30, 300000
RIDGE = 0.5
FILL = ("cylinders", "litres", "weight_class", "drive", "body")
PICKUPS = ("pickup", "truck")
_FREE = {"one", "age", "age2", "m", "m2", "agem", "lm", "m>6", "m>10", "m>14", "age>5", "age>9",
         "private_age", "private_pickup"}                     # not shrunk
# Where six in ten asking prices fell, as a share of the figure, by who is selling and what the figure stands on.
# Measured on the catalogue of 2026-11-21; the private rows rest on 29, 50 and 93 cars.
RANGES = {("dealer", "close"): (0.96, 1.13), ("dealer", "wide"): (0.94, 1.19), ("dealer", "rough"): (0.85, 1.19),
          ("private", "close"): (0.90, 1.25), ("private", "wide"): (0.84, 1.47), ("private", "rough"): (0.64, 1.63)}


def _words(trim):
    return {word for word in re.findall(r"[a-z0-9]+", (trim or "").lower()) if len(word) > 1}


def _counts(cars):
    """How often each model, trim word, model-and-trim-word and model-and-series occurs: rare ones get no term."""
    counts = {}
    for car in cars:
        model = (car["make"], car["model"])
        keys = [model] + [("word", word) for word in _words(car.get("trim"))]
        keys += [(model, word) for word in _words(car.get("trim"))]
        if car.get("series"):
            keys.append((model, "series", car["series"]))
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    return counts


def _filled(cars, known_from):
    """`cars` with each missing FILL field taken from the commonest value among the cars of `known_from` of
    the same make and model that state it (at a tie, the smaller as text). Nothing known: left empty."""
    known = {}
    for car in known_from:
        for field in FILL:
            if car.get(field) not in (None, ""):
                tally = known.setdefault((car["make"], car["model"], field), {})
                tally[car[field]] = tally.get(car[field], 0) + 1
    filled = []
    for car in cars:
        car = dict(car)
        for field in FILL:
            tally = known.get((car["make"], car["model"], field))
            if car.get(field) in (None, "") and tally:
                car[field] = min(tally, key=lambda value: (-tally[value], str(value)))
        filled.append(car)
    return filled


def _features(car, this_year, counts):
    age, miles = min(max(this_year + 1 - car["year"], 0), MAX_AGE), min(car["miles"], MAX_MILES)
    m = miles / 10000
    model, name = (car["make"], car["model"]), f"{car['make']}|{car['model']}"
    found = {"one": 1.0, "age": age, "age2": age * age / 10, "m": m, "m2": m * m / 10, "agem": age * m / 10,
             "lm": math.log1p(miles / 1000), "m>6": max(m - 6, 0), "m>10": max(m - 10, 0),
             "m>14": max(m - 14, 0), "age>5": max(age - 5, 0), "age>9": max(age - 9, 0),
             f"make:{car['make']}": 1.0, f"body:{car.get('body')}": 1.0, f"drive:{car.get('drive')}": 1.0,
             f"fuel:{car.get('fuel')}": 1.0}
    if car.get("seller") == "private":
        found["private_age"] = age / 10              # the older the car, the further under a dealer a private seller asks
        if car.get("body") in PICKUPS:
            found["private_pickup"] = 1.0             # but not on a pickup
    if counts.get(model, 0) >= 4:
        found[f"model:{name}"] = 1.0
    if counts.get(model, 0) >= 15:
        found[f"ages:{name}"] = age / 5              # how fast this model loses value, beside the average
    for word in _words(car.get("trim")):
        if counts.get(("word", word), 0) >= 20:
            found[f"word:{word}"] = 1.0
        if counts.get((model, word), 0) >= 6:
            found[f"trim:{name}|{word}"] = 1.0
    if car.get("series") and counts.get((model, "series", car["series"]), 0) >= 6:
        found[f"series:{name}|{car['series']}"] = 1.0
    if car.get("cylinders"):
        found["cylinders"] = car["cylinders"] / 4
    if car.get("litres"):
        found["litres"] = car["litres"] / 2
    if car.get("weight_class"):
        found[f"weight:{car['weight_class']}"] = 1.0
    return found


def _fit(rows):
    """Ridge regression of log price on `rows` ([(features, price)]). Returns {feature name: weight}."""
    index = {}
    for features, _ in rows:
        for name in features:
            index.setdefault(name, len(index))
    size = len(index)
    left, right = [[0.0] * size for _ in range(size)], [0.0] * size
    for features, price in rows:
        target, terms = math.log(price), [(index[name], value) for name, value in features.items()]
        for i, a in terms:
            right[i] += a * target
            row = left[i]
            for j, b in terms:
                row[j] += a * b
    for name, i in index.items():
        left[i][i] += 1e-6 if name in _FREE else RIDGE
    for i in range(size):                             # elimination; the ridge keeps every pivot positive
        pivot, top = left[i][i], left[i]
        for j in range(i + 1, size):
            if left[j][i]:
                factor, row = left[j][i] / pivot, left[j]
                for k in range(i, size):
                    row[k] -= factor * top[k]
                right[j] -= factor * right[i]
    weights = [0.0] * size
    for i in range(size - 1, -1, -1):
        weights[i] = (right[i] - sum(left[i][k] * weights[k] for k in range(i + 1, size))) / left[i][i]
    return {name: weights[i] for name, i in index.items()}


def _priced(weights, features):
    return math.exp(sum(weights.get(name, 0.0) * value for name, value in features.items()))


def _hundreds(dollars):
    return int(round(dollars / 100)) * 100


def judge(cars, this_year):
    """{car id: {"typical", "similar", "basis", "window", "low", "high"}} for every car that can be priced.
    `cars` are dicts with id, price, year, miles, make and model, and whatever is known of seller ("private"
    or not), trim, body, drive, fuel, series, cylinders, litres and weight_class. Each should be one vehicle,
    listed once. `basis` is "close", "wide" or "rough"; `window` the (years, miles) the neighbours were found
    within, None when rough; `similar` how many neighbours, 0 when rough. A car with `apart` set is priced
    like the rest but is left out of everything the others are priced from."""
    usable = sorted((car for car in cars if car.get("price") and car.get("year") and car.get("miles") is not None
                     and car.get("make") and car.get("model")), key=lambda car: car["id"])
    learnt = [car for car in usable if not car.get("apart")]
    if len(learnt) < MIN_MARKET:
        return {}
    usable = _filled(usable, learnt)
    learnt = [car for car in usable if not car.get("apart")]
    counts = _counts(learnt)
    fold = {car["id"]: zlib.crc32(car["id"].encode()) % FOLDS for car in usable}
    fitted = [_fit([(_features(car, this_year, counts), car["price"]) for car in learnt if fold[car["id"]] != held])
              for held in range(FOLDS)]
    features = {car["id"]: _features(car, this_year, counts) for car in usable}
    by_model = {}
    for car in learnt:
        by_model.setdefault((car["make"], car["model"]), []).append(car)

    judged = {}
    for car in usable:
        weights = fitted[fold[car["id"]]]             # the model that never saw this car
        modelled = _priced(weights, features[car["id"]])
        others = [other for other in by_model.get((car["make"], car["model"]), ()) if other["id"] != car["id"]]
        near, window = [], None
        for years, miles in LADDER:
            near = [other for other in others
                    if abs(other["year"] - car["year"]) <= years and abs(other["miles"] - car["miles"]) <= miles]
            if len(near) >= MIN_SIMILAR:
                window = (years, miles)
                break
        if window:
            # What each neighbour would ask at this car's year and mileage, from this car's kind of seller. Only
            # the model's slopes are used: the neighbour's trim, engine and the rest stay its own and cancel
            # out, so a trim word the model misreads cannot mislead both estimates at once.
            moved = [other["price"] * _priced(weights, _features(
                {**other, "year": car["year"], "miles": car["miles"], "seller": car.get("seller")}, this_year, counts))
                / _priced(weights, features[other["id"]]) for other in near]
            typical, basis = min(modelled, statistics.median(moved)), "close" if window == LADDER[0] else "wide"
        else:
            typical, basis, near = modelled, "rough", []
        low, high = RANGES[("private" if car.get("seller") == "private" else "dealer", basis)]
        typical = _hundreds(typical)
        judged[car["id"]] = {"typical": typical, "similar": len(near), "basis": basis, "window": window,
                             "low": _hundreds(typical * low), "high": _hundreds(typical * high)}
    return judged
