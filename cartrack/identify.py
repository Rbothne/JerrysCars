"""Make and model for a listing that gives them only in the seller's own words.

A private seller types "chevy silverado lt 4x4" or "ford f150"; a dealer's car is named by its VIN. To set
the two side by side, the seller's words are matched against the models the catalogue already knows from
decoded VINs, spelled the way vPIC spells them: the make first (two words or one, a few nicknames), then the
longest known model of that make that the next words spell, punctuation and spacing aside ("f 150", "f150"
and "F-150" are one model). A model given only by its first word ("silverado") takes the commonest known
model that starts with it. Whatever follows the model is kept as trim.

A make the catalogue has never seen names nothing, and a known make with an unknown model names only the
make: such a car has no similar cars to be judged against anyway. Both are tried again on every build, as
the catalogue learns more models."""

import json
import re

from . import listings

NICKNAMES = {"chevy": "chevrolet", "vw": "volkswagen", "mercedes": "mercedes-benz", "benz": "mercedes-benz",
             "caddy": "cadillac", "infinity": "infiniti"}
MODEL_WORDS = 4        # no known model is spelled with more words than this


def _bare(words):
    return re.sub(r"[^a-z0-9]", "", "".join(words).lower())


def named(typed, known):
    """{"make", "model", "trim"} for a seller's words, given `known` as {make: {model: how many}}.
    None when the make is not a known one; model and trim are None when only the make is."""
    words = (typed or "").lower().split()
    makes = {_bare(make): make for make in known}
    makes.update({nick: make for nick, make in NICKNAMES.items() if make in known})
    for taken in (2, 1):
        make = makes.get(_bare(words[:taken])) if len(words) >= taken else None
        if make:
            break
    else:
        return None
    rest, models = words[taken:], {_bare(model): model for model in known[make]}
    for count in range(min(MODEL_WORDS, len(rest)), 0, -1):
        spelled = _bare(rest[:count])
        model = models.get(spelled) or models.get(_bare(make) + spelled)       # "mazda 3" is the Mazda3
        if model:
            return {"make": make, "model": model, "trim": " ".join(rest[count:]) or None}
    first = _bare(rest[:1])
    if re.search(r"[a-z]", first):                                             # "3" could be a dozen models
        starting = [model for model in known[make] if _bare(model.split()[:1]) == first]
        if starting:
            model = max(starting, key=lambda name: (known[make][name], name))
            return {"make": make, "model": model, "trim": " ".join(rest[1:]) or None}
    return {"make": make, "model": None, "trim": None}


def known_models(db):
    """{make: {model: how many listings}} for every make and model a decoded VIN has named."""
    known = {}
    for make, model, count in db.execute(
            "SELECT make, model, count(*) FROM listing WHERE identity_how = 'vin' AND make IS NOT NULL "
            "AND model IS NOT NULL GROUP BY make, model"):
        known.setdefault(make, {})[model] = count
    return known


def fill(db):
    """Name every listing that has the seller's words (`extra.makemodel`) and lacks a make or a model.
    Returns how many listings it changed."""
    known = known_models(db)
    rows = db.execute("SELECT id, year, make, model, trim, body, drive, engine, extra FROM listing "
                      "WHERE (make IS NULL OR model IS NULL) AND extra LIKE '%\"makemodel\"%'").fetchall()
    changed = 0
    with db:
        for row in rows:
            found = named(json.loads(row["extra"]).get("makemodel"), known)
            if not found or (found["make"], found["model"]) == (row["make"], row["model"]):
                continue
            trim = found["trim"] or row["trim"]
            db.execute(
                "UPDATE listing SET make = ?, model = ?, trim = ?, identity_how = ?, vehicle_key = ? WHERE id = ?",
                (found["make"], found["model"], trim, "title" if found["model"] else "source",
                 listings.vehicle_key(row["year"], found["make"], found["model"], trim, row["body"], row["drive"],
                                      row["engine"]), row["id"]))
            changed += 1
    return changed
