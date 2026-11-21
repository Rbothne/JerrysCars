"""What a car like this one usually asks, worked out from the other cars in the catalogue.

Two estimates, and the lower one is kept, so a car is only called cheap when both agree:

1. A price model over every car: year, mileage, make, model, trim words, body, drive, fuel, engine and weight
   class (a ridge regression on the log of the price). Each car is priced by a model fitted without it.
2. The car's own neighbours: the same model within two years and 30,000 miles, each one's asking price moved
   to this car's year and mileage, and the median taken. A car with fewer than three such neighbours gets no
   judgement at all.

How well this does on the Memphis catalogue is in research/09-value.md. It is a guide to where to look, not
an appraisal: no listing states condition, and condition decides the price of a cheap car."""

import math
import re
import statistics
import zlib

MIN_MARKET = 200          # fewer cars than this and the model would be describing noise
MIN_SIMILAR = 3
FOLDS = 5
NEAR_YEARS, NEAR_MILES = 2, 30000
RIDGE = 0.5
_FREE = {"one", "age", "age2", "m", "m2", "agem", "lm", "m>6", "m>10", "m>14", "age>5", "age>9"}   # not shrunk


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


def _features(car, this_year, counts):
    age, m = max(this_year + 1 - car["year"], 0), car["miles"] / 10000
    model, name = (car["make"], car["model"]), f"{car['make']}|{car['model']}"
    found = {"one": 1.0, "age": age, "age2": age * age / 10, "m": m, "m2": m * m / 10, "agem": age * m / 10,
             "lm": math.log1p(car["miles"] / 1000), "m>6": max(m - 6, 0), "m>10": max(m - 10, 0),
             "m>14": max(m - 14, 0), "age>5": max(age - 5, 0), "age>9": max(age - 9, 0),
             f"make:{car['make']}": 1.0, f"body:{car.get('body')}": 1.0, f"drive:{car.get('drive')}": 1.0,
             f"fuel:{car.get('fuel')}": 1.0}
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


def judge(cars, this_year):
    """{car id: {"typical": dollars, "similar": how many neighbours}} for every car that has neighbours enough.
    `cars` are dicts with id, price, year, miles, make and model, and whatever is known of trim, body, drive,
    fuel, series, cylinders, litres and weight_class. Each car should be one vehicle, listed once."""
    usable = sorted((car for car in cars if car.get("price") and car.get("year") and car.get("miles") is not None
                     and car.get("make") and car.get("model")), key=lambda car: car["id"])
    if len(usable) < MIN_MARKET:
        return {}
    counts = _counts(usable)
    rows = [(_features(car, this_year, counts), car["price"]) for car in usable]
    fold = [zlib.crc32(car["id"].encode()) % FOLDS for car in usable]

    fitted = [_fit([row for row, at in zip(rows, fold) if at != held]) for held in range(FOLDS)]
    features = {car["id"]: row[0] for car, row in zip(usable, rows)}
    by_model = {}
    for car in usable:
        by_model.setdefault((car["make"], car["model"]), []).append(car)

    judged = {}
    for car, at in zip(usable, fold):
        near = [other for other in by_model[(car["make"], car["model"])]
                if other["id"] != car["id"] and abs(other["year"] - car["year"]) <= NEAR_YEARS
                and abs(other["miles"] - car["miles"]) <= NEAR_MILES]
        if len(near) < MIN_SIMILAR:
            continue
        weights = fitted[at]                          # the model that never saw this car
        modelled = _priced(weights, features[car["id"]])
        # What each neighbour would ask at this car's year and mileage. Only the model's slopes for age and
        # miles are used: the neighbour's trim, engine and the rest stay its own and cancel out, so a trim
        # word the model misreads cannot mislead both estimates at once.
        moved = [other["price"] * _priced(weights, _features({**other, "year": car["year"], "miles": car["miles"]},
                                                             this_year, counts))
                 / _priced(weights, features[other["id"]]) for other in near]
        typical = min(modelled, statistics.median(moved))
        judged[car["id"]] = {"typical": int(round(typical / 100)) * 100, "similar": len(near)}
    return judged
