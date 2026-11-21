"""VINs: the check digit, and what NHTSA's free vPIC service says a VIN is."""

import json
import urllib.parse

from . import fetch

BATCH_URL = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVINValuesBatch/"
BATCH = 50                                    # vPIC's own limit per request

# 49 CFR 565: each character's value, and the weight of each of the 17 positions. I, O and Q are never used.
_VALUES = {
    **{str(digit): digit for digit in range(10)},
    **dict(zip("ABCDEFGH", range(1, 9))),
    **dict(zip("JKLMN", range(1, 6))),
    "P": 7, "R": 9,
    **dict(zip("STUVWXYZ", range(2, 10))),
}
_WEIGHTS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)

_BODIES = (                                   # first match wins, so "minivan" is asked before "van"
    ("minivan", "minivan"), ("pickup", "pickup"), ("sport utility", "suv"), ("crossover", "suv"),
    ("sedan", "sedan"), ("coupe", "coupe"), ("convertible", "convertible"), ("hatchback", "hatchback"),
    ("wagon", "wagon"), ("van", "van"),
)
_DRIVES = (("4x4", "4wd"), ("4wd", "4wd"), ("awd", "awd"), ("fwd", "fwd"), ("rwd", "rwd"), ("4x2", "2wd"), ("2wd", "2wd"))
_LAYOUTS = {"v-shaped": "v", "in-line": "i", "horizontally opposed": "h", "w-shaped": "w"}


def valid(vin):
    """True when `vin` is 17 allowed characters and its ninth one is the right check digit."""
    if len(vin) != 17 or any(character not in _VALUES for character in vin):
        return False
    remainder = sum(_VALUES[character] * weight for character, weight in zip(vin, _WEIGHTS)) % 11
    return vin[8] == ("X" if remainder == 10 else str(remainder))


def _post(url, body, headers=None):
    return fetch.get(url, data=body, headers=headers, timeout=60)


def decode(vins, post=_post):
    """Ask vPIC about `vins`, 50 at a time. Returns {vin: row}, each row holding only the fields vPIC filled in.
    A VIN with a wrong check digit still comes back, decoded from its pattern, with ErrorCode "1"."""
    vins = list(dict.fromkeys(vins))
    rows = {}
    for start in range(0, len(vins), BATCH):
        body = urllib.parse.urlencode({"DATA": ";".join(vins[start:start + BATCH]), "format": "json"}).encode()
        answer = json.loads(post(BATCH_URL, body, {"Content-Type": "application/x-www-form-urlencoded"}))
        for row in answer.get("Results") or []:
            if row.get("VIN"):
                rows[row["VIN"].upper()] = {name: value for name, value in row.items() if value not in ("", None)}
    return rows


def _first(text, table):
    text = (text or "").lower()
    return next((word for needle, word in table if needle in text), None)


def _engine(row):
    try:
        litres = f"{float(row.get('DisplacementL')):.1f}l"
    except (TypeError, ValueError):
        return None
    cylinders = row.get("EngineCylinders")
    if not cylinders:
        return litres
    layout = _LAYOUTS.get((row.get("EngineConfiguration") or "").lower())
    return f"{litres} {layout}{cylinders}" if layout else f"{litres} {cylinders}cyl"


def identity(row):
    """A vPIC row as the catalogue's identity fields. Anything vPIC left blank is None."""
    year = row.get("ModelYear")
    return {
        "year": int(year) if year and str(year).isdigit() else None,
        "make": (row.get("Make") or "").strip().lower() or None,
        "model": (row.get("Model") or "").strip() or None,
        "trim": (row.get("Trim") or "").strip() or None,
        "body": _first(row.get("BodyClass"), _BODIES),
        "drive": _first(row.get("DriveType"), _DRIVES),
        "engine": _engine(row),
        "fuel": (row.get("FuelTypePrimary") or "").strip().lower() or None,
        "transmission": (row.get("TransmissionStyle") or "").strip().lower() or None,
    }
