"""Facebook Marketplace, as the owner's own browser saw it.

Nothing here asks Facebook for anything. The extension in `extension/facebook/` keeps the vehicle listings the
owner looks at while he browses Marketplace, without the sellers, and writes them as one JSON file to a GitHub
repository of their own: `captures/<who>.json`, one file for each person running it. This lists that folder and
reads every file in it, one request each, and joins them: a car two people saw is one car, as the one who saw it
last saw it, with what the other's opening of it added. When the repository is private, the build reads it with
the token in the CAPTURES_TOKEN environment variable (an Actions secret). The file's form is in
research/11-facebook-capture.md, section 6. **Meta's terms forbid collecting its data by automated means**; the
owner chose to run the extension knowing that, and the account it runs in is his.

What follows from reading only what one person saw:

- A read is never whole: he never sees all of Marketplace. Nothing is marked gone for being missing from the file.
- Each listing is recorded at the time he last saw it, not at the time of the build, so that a car he saw once
  ages out (`unseen_days` on the place's row) instead of looking fresh at every build.
- A car he saw marked sold is over from that moment. Its price stays what it was: an asking price. Facebook
  never shows what a car fetched.
- A listing opened on its own page carries a posting time, the exact odometer and the vehicle's fields; one seen
  only in search results carries a title, a price, a rounded mileage and a town.

A missing file (404) means no capture yet and reads as no listings. A file this reader does not understand, or
whose rows mostly lack an id or a title, is refused."""

import datetime
import json
import os

from .. import fetch
from ..listings import make_listing
from ..readers import NotRead

FORMATS = (1,)
UNSEEN_DAYS = 14
_TITLES = {"clean": "clean", "rebuilt": "rebuilt", "salvage": "salvage", "lien": "lien"}


def _year_free(title):
    """The title without the year sellers put first, for cartrack/identify.py to name."""
    words = (title or "").split()
    return " ".join(words[1:]) if words and words[0].isdigit() and len(words[0]) == 4 else title


def _rows(body, where):
    """The usable rows of one capture file. Raises NotRead for a file this reader does not understand."""
    try:
        captured = json.loads(body.decode("utf-8"))
        rows = captured["listings"]
    except (ValueError, KeyError, TypeError) as error:
        raise NotRead(f"{where}: not a capture file ({error!r})") from error
    if captured.get("format") not in FORMATS:
        raise NotRead(f"{where}: capture format {captured.get('format')!r} is not one this reader knows")
    usable = [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("title")]
    if rows and len(usable) < 0.8 * len(rows):
        raise NotRead(f"{where}: only {len(usable)} of {len(rows)} rows have an id and a title")
    return usable


def _joined(old, new):
    """One car two people saw: the later sighting, with the fields only the other's carries."""
    later, earlier = (new, old) if (new.get("seen") or "") >= (old.get("seen") or "") else (old, new)
    joined = {**earlier, **{name: value for name, value in later.items() if value is not None}}
    if earlier.get("miles_how") == "detail" and later.get("miles_how") != "detail":
        joined["miles"], joined["miles_how"] = earlier["miles"], "detail"     # an odometer beats a card's rounding
    return joined


def _captures(place, get):
    """Every row of every file in the place's captures folder, joined by listing id."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get(place.get("token_env", "CAPTURES_TOKEN"))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    folder = f"https://api.github.com/repos/{place['repo']}/contents/{place.get('folder', 'captures')}"
    try:
        listed = json.loads(get(folder, headers=headers).decode("utf-8"))
    except fetch.Gone:
        return {}                                     # nothing uploaded yet
    except ValueError as error:
        raise NotRead(f"{folder}: the folder listing is not JSON") from error
    files = [entry for entry in listed if isinstance(entry, dict) and entry.get("type") == "file"
             and entry.get("name", "").endswith(".json")]
    joined = {}
    for entry in files:
        where = f"{place['repo']}/{entry.get('path')}"
        for row in _rows(get(entry["download_url"], headers=headers), where):
            key = str(row["id"])
            joined[key] = _joined(joined[key], row) if key in joined else row
    return joined


def read(place, get, seen, known=()):
    usable = list(_captures(place, get).values())
    cutoff = (datetime.datetime.fromisoformat(seen) - datetime.timedelta(days=place.get("unseen_days", UNSEEN_DAYS))
              ).strftime("%Y-%m-%dT%H:%M")
    found = []
    for row in usable:
        if (row.get("seen") or "") < cutoff:
            continue                                  # a stale file must not hold a car open
        extra = {"was": row.get("was"), "miles_how": row.get("miles_how"), "pending": True if row.get("status") == "pending" else None,
                 "last_seen": row.get("seen"), "opened": bool(row.get("detail_seen"))}
        if not (row.get("make") and row.get("model")):
            extra["makemodel"] = _year_free(row["title"])
        listing = make_listing(
            place["key"], str(row["id"]), seen=row["seen"], channel="marketplace",
            url=f"https://www.facebook.com/marketplace/item/{row['id']}/", title=row["title"],
            price=row.get("price"), currency=row.get("currency") or "USD", posted=row.get("posted"),
            seller_type=row.get("seller_type"), year=row.get("year"), make=row.get("make"), model=row.get("model"),
            vin=row.get("vin"), title_status=_TITLES.get((row.get("title_status") or "").lower()),
            transmission=row.get("transmission"), fuel=row.get("fuel"), color=row.get("color"),
            condition=(row.get("condition") or "").replace("_", " ").lower() or None,
            miles=row.get("miles"), city=row.get("city"), state=row.get("state"), zip=row.get("zip"),
            lat=row.get("lat"), lon=row.get("lon"), geo_how="city" if row.get("lat") is not None else None,
            photos=[row["photo"]] if row.get("photo") else [],
            extra={name: value for name, value in extra.items() if value is not None})
        if listing and row.get("status") == "sold":
            listing["over"] = {"when": row.get("status_seen") or row["seen"], "how": "sold"}
        if listing:
            found.append(listing)
    return found, False
