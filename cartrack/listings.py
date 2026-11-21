"""The one record every source reader hands back, however the source describes a car.

After aptrack/units.py: one function makes the record, None means the source does not say, and a record
that cannot be used at all comes back as None."""

import re

from . import vin as vins

CHANNELS = ("classified", "marketplace", "dealer_site", "aggregator", "auction")
PRICE_KINDS = ("ask", "bid", "sold", "reserve_not_met", "starting")
SELLER_TYPES = ("private", "dealer")
TITLE_STATUSES = ("clean", "rebuilt", "salvage", "lien", "missing", "parts_only", "lemon")
DRIVES = ("fwd", "rwd", "awd", "4wd", "2wd")
GEO_HOWS = ("pin", "street", "zip", "city")
IDENTITY_HOWS = ("vin", "source", "title", "manual")

MIN_ASK = 500          # an asking price under this is bait ("$0 - we finance everyone") or a down payment
MAX_PHOTOS = 12


def num(value):
    """The first number in `value` ("$12,500" gives 12500), or None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    match = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(value))
    return float(match.group().replace(",", "")) if match else None


def _whole(value, low=0, high=None):
    number = num(value)
    if number is None:
        return None
    number = int(round(number))
    return number if number >= low and (high is None or number <= high) else None


def _text(value):
    value = str(value).strip() if value is not None else ""
    return value or None


def _one_of(value, allowed):
    value = (_text(value) or "").lower()
    return value if value in allowed else None


def vehicle_key(year, make, model, trim=None, body=None, drive=None, engine=None):
    """year|make|model|trim|body|drive|engine in lower case, blank where unknown. None without the first three.
    Only the first three parts match two listings; the rest break ties."""
    if not (year and make and model):
        return None
    return "|".join(str(part).strip().lower() if part else "" for part in (year, make, model, trim, body, drive, engine))


def make_listing(source, source_id, *, url, title, seen, channel, price=None, price_kind="ask", currency="USD",
                 posted=None, updated=None, ends=None, seller_type=None, seller_id=None, seller_name=None,
                 vin=None, year=None, make=None, model=None, trim=None, body=None, drive=None, engine=None,
                 fuel=None, transmission=None, identity_how=None, miles=None, title_status=None, condition=None,
                 color=None, city=None, state=None, zip=None, lat=None, lon=None, geo_how=None,
                 photos=None, photo_count=None, photo_ids=None, extra=None):
    """One listing as the catalogue stores it. `seen` is this read, UTC "YYYY-MM-DDTHH:MM".
    Returns None for a listing with no title or no id of its own."""
    title, source_id = _text(title), _text(source_id)
    if not (title and source_id):
        return None
    if channel not in CHANNELS:
        raise ValueError(f"unknown channel {channel!r}")
    if price_kind not in PRICE_KINDS:
        raise ValueError(f"unknown price_kind {price_kind!r}")
    extra = dict(extra or {})

    given_vin = (_text(vin) or "").upper()
    if len(given_vin) == 17:
        vin, vin_ok = given_vin, vins.valid(given_vin)
    else:
        vin, vin_ok = None, None
        if given_vin:
            extra["chassis"] = given_vin          # pre-1981 cars and imports have shorter chassis numbers

    year = _whole(year, 1900, 2100)
    make = (_text(make) or "").lower() or None
    model, trim = _text(model), _text(trim)
    body, engine = (_text(body) or "").lower() or None, (_text(engine) or "").lower() or None
    drive = _one_of(drive, DRIVES)
    if identity_how not in IDENTITY_HOWS:
        identity_how = "source" if (year or make or model) else None

    state = _text(state)
    state = state.upper() if state and re.fullmatch(r"[A-Za-z]{2}", state) else None
    zip_match = re.match(r"\d{5}", _text(zip) or "")
    lat, lon = num(lat), num(lon)
    lat, lon = (round(lat, 5), round(lon, 5)) if lat is not None and lon is not None else (None, None)

    photos = [photo for photo in (photos or []) if photo]
    return {
        "id": f"{source}:{source_id}",
        "source": source,
        "source_id": source_id,
        "url": url,
        "seen": seen,
        "posted": posted,
        "updated": updated,
        "ends": ends,
        "title": title,
        "price": _whole(price, MIN_ASK if price_kind == "ask" else 1),
        "price_kind": price_kind,
        "currency": currency,
        "seller_type": _one_of(seller_type, SELLER_TYPES),
        "channel": channel,
        "seller_id": _text(seller_id),
        "seller_name": _text(seller_name),
        "vin": vin,
        "vin_ok": vin_ok,
        "year": year,
        "make": make,
        "model": model,
        "trim": trim,
        "body": body,
        "drive": drive,
        "engine": engine,
        "fuel": (_text(fuel) or "").lower() or None,
        "transmission": (_text(transmission) or "").lower() or None,
        "identity_how": identity_how,
        "vehicle_key": vehicle_key(year, make, model, trim, body, drive, engine),
        "miles": _whole(miles),
        "title_status": _one_of(title_status, TITLE_STATUSES),
        "condition": _text(condition),
        "color": _text(color),
        "city": _text(city),
        "state": state,
        "zip": zip_match.group() if zip_match else None,
        "lat": lat,
        "lon": lon,
        "geo_how": _one_of(geo_how, GEO_HOWS),
        "photos": photos[:MAX_PHOTOS],
        "photo_count": _whole(photo_count) if photo_count is not None else len(photos),
        "photo_ids": list(photo_ids or []),
        "extra": extra,
    }
