"""The catalogue: one SQLite file holding every listing seen, its price history, and the dealers found.

History follows the wishlist site's history.py: a price point is added only when something changed, a
listing keeps the first and last time it was seen, and "gone" is only decided by a whole read of its source."""

import datetime
import json
import sqlite3

from . import listings
from . import vin as vins

# One entry per version, never edited once released (ticketdesk's way). PRAGMA user_version says how far a file is.
MIGRATIONS = ["""
CREATE TABLE listing (
    id              TEXT PRIMARY KEY,                 -- "<source>:<source_id>"
    source          TEXT NOT NULL,
    source_id       TEXT NOT NULL,
    url             TEXT NOT NULL,
    posted          TEXT,
    updated         TEXT,
    ends            TEXT,
    title           TEXT NOT NULL,
    price           INTEGER CHECK (price IS NULL OR price > 0),      -- latest; the series is in price_point
    price_kind      TEXT NOT NULL CHECK (price_kind IN ('ask','bid','sold','reserve_not_met','starting')),
    currency        TEXT NOT NULL DEFAULT 'USD',
    seller_type     TEXT CHECK (seller_type IN ('private','dealer')),
    channel         TEXT NOT NULL CHECK (channel IN ('classified','marketplace','dealer_site','aggregator','auction')),
    seller_id       TEXT,
    seller_name     TEXT,
    vin             TEXT CHECK (vin IS NULL OR length(vin) = 17),
    vin_ok          INTEGER,                          -- 1, 0, NULL
    year            INTEGER CHECK (year IS NULL OR year BETWEEN 1900 AND 2100),
    make            TEXT,
    model           TEXT,
    trim            TEXT,
    body            TEXT,
    drive           TEXT CHECK (drive IS NULL OR drive IN ('fwd','rwd','awd','4wd','2wd')),
    engine          TEXT,
    fuel            TEXT,
    transmission    TEXT,
    identity_how    TEXT CHECK (identity_how IS NULL OR identity_how IN ('vin','source','title','manual')),
    vehicle_key     TEXT,
    miles           INTEGER CHECK (miles IS NULL OR miles >= 0),
    title_status    TEXT CHECK (title_status IS NULL OR title_status IN
                        ('clean','rebuilt','salvage','lien','missing','parts_only','lemon')),
    condition       TEXT,
    color           TEXT,
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    lat             REAL,
    lon             REAL,
    geo_how         TEXT CHECK (geo_how IS NULL OR geo_how IN ('pin','street','zip','city')),
    photos          TEXT,                             -- JSON list
    photo_count     INTEGER NOT NULL DEFAULT 0,
    photo_ids       TEXT,                             -- JSON list
    extra           TEXT,                             -- JSON object
    first_seen      TEXT NOT NULL,
    last_seen       TEXT NOT NULL,
    gone            TEXT,
    gone_how        TEXT CHECK (gone_how IS NULL OR gone_how IN ('sold','removed','expired','unseen','ended_unsold')),
    vehicle_id      TEXT NOT NULL,                    -- "vin:<VIN>", or "v:<listing id>" until something links it
    UNIQUE (source, source_id)
);
CREATE INDEX listing_vin ON listing(vin);
CREATE INDEX listing_vehicle ON listing(vehicle_id);
CREATE INDEX listing_source_live ON listing(source, gone);

CREATE TABLE price_point (                            -- added only when the price or the odometer changed
    listing_id      TEXT NOT NULL REFERENCES listing(id),
    observed        TEXT NOT NULL,
    price           INTEGER,                          -- NULL: the price was withdrawn
    miles           INTEGER,
    PRIMARY KEY (listing_id, observed)
);

CREATE TABLE seen_span (                              -- one row per unbroken stretch of reads that found the listing
    listing_id      TEXT NOT NULL REFERENCES listing(id),
    start           TEXT NOT NULL,
    stop            TEXT NOT NULL,
    PRIMARY KEY (listing_id, start)
);

CREATE TABLE vin_decode (                             -- every VIN decoded once, kept for good
    vin             TEXT PRIMARY KEY,
    decoded         TEXT NOT NULL,
    error_code      TEXT,
    row_json        TEXT NOT NULL
);

CREATE TABLE dealer (
    key             TEXT PRIMARY KEY,                 -- the website host, or where it was found when it has none
    name            TEXT,
    host            TEXT,
    website         TEXT,
    platform        TEXT,
    reads           TEXT,                             -- 'plain', 'browser', NULL = not known yet
    resolves        INTEGER,
    lat             REAL,
    lon             REAL,
    miles           REAL,
    street          TEXT,
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    phone           TEXT,
    brand           TEXT,
    used_only       INTEGER,
    osm             TEXT,
    found_by        TEXT NOT NULL,                    -- JSON list
    first_found     TEXT NOT NULL,
    last_found      TEXT NOT NULL
);

CREATE VIEW vehicle AS                                -- one physical car, however many times and places it is listed
SELECT l.vehicle_id,
       max(l.vin) AS vin,
       max(l.vehicle_key) AS vehicle_key,
       min(l.first_seen) AS first_seen,
       max(l.last_seen) AS last_seen,
       count(*) AS listings,
       (SELECT min(p.price) FROM price_point p JOIN listing m ON m.id = p.listing_id
         WHERE m.vehicle_id = l.vehicle_id) AS low_price
  FROM listing l
 GROUP BY l.vehicle_id;
"""]

_JSON_FIELDS = ("photos", "photo_ids", "extra")
_FIELDS = (
    "source", "source_id", "url", "posted", "updated", "ends", "title", "price_kind", "currency", "seller_type",
    "channel", "seller_id", "seller_name", "vin", "vin_ok", "year", "make", "model", "trim", "body", "drive",
    "engine", "fuel", "transmission", "identity_how", "vehicle_key", "miles", "title_status", "condition",
    "color", "city", "state", "zip", "lat", "lon", "geo_how", "photos", "photo_count", "photo_ids", "extra",
)
_DEALER_FIELDS = (
    "name", "host", "website", "platform", "reads", "resolves", "lat", "lon", "miles", "street", "city", "state",
    "zip", "phone", "brand", "used_only", "osm",
)
_IDENTITY = ("year", "make", "model", "trim", "body", "drive", "engine", "fuel", "transmission")

FLOOR = 0.8            # a read that found fewer than this share of a source's live listings is taken as broken
UNSEEN_DAYS = 3        # a listing no read has found for this long is gone, whatever the reads called themselves


class Shrunk(Exception):
    """A read found so few of a source's live listings that it is more likely broken than true."""


def open_catalogue(path):
    """Open the catalogue at `path` (":memory:" for a throwaway one), creating or upgrading its tables."""
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    version = db.execute("PRAGMA user_version").fetchone()[0]
    for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
        db.executescript(script)
        db.execute(f"PRAGMA user_version = {number}")
    db.commit()
    return db


def _stored(name, value):
    if name in _JSON_FIELDS:
        return json.dumps(value) if value else None
    return int(value) if isinstance(value, bool) else value


def _vehicle_id(listing_id, vin):
    return f"vin:{vin}" if vin else f"v:{listing_id}"


def record(db, listing):
    """Store one read of one listing. Returns "new", "back" (it had gone and has returned), "changed" (its
    price or odometer moved) or "same". A field this read does not give keeps the value an earlier read gave;
    the price is the exception, since a price taken down is itself news. Identity that came from a decoded
    VIN stays as the VIN gave it."""
    seen, key = listing["seen"], listing["id"]
    values = {name: _stored(name, listing.get(name)) for name in _FIELDS}
    old = db.execute("SELECT price, miles, gone, vin, identity_how FROM listing WHERE id = ?", (key,)).fetchone()
    if old is not None and old["identity_how"] == "vin":
        for name in (*_IDENTITY, "identity_how", "vehicle_key"):
            values[name] = None                       # the VIN has spoken: a reader's wording does not replace it
    with db:
        if old is None:
            names = ("id", *_FIELDS, "price", "first_seen", "last_seen", "vehicle_id")
            db.execute(
                f"INSERT INTO listing ({', '.join(names)}) VALUES ({', '.join('?' * len(names))})",
                (key, *values.values(), listing["price"], seen, seen, _vehicle_id(key, listing["vin"])))
            db.execute("INSERT INTO price_point VALUES (?, ?, ?, ?)", (key, seen, listing["price"], listing["miles"]))
            db.execute("INSERT INTO seen_span VALUES (?, ?, ?)", (key, seen, seen))
            return "new"

        miles = listing["miles"] if listing["miles"] is not None else old["miles"]
        changed = (listing["price"], miles) != (old["price"], old["miles"])
        db.execute(
            f"UPDATE listing SET {', '.join(f'{name} = coalesce(?, {name})' for name in _FIELDS)}, "
            "price = ?, last_seen = max(last_seen, ?), gone = NULL, gone_how = NULL, vehicle_id = ? WHERE id = ?",
            (*values.values(), listing["price"], seen, _vehicle_id(key, listing["vin"] or old["vin"]), key))
        if changed:
            db.execute("INSERT OR REPLACE INTO price_point VALUES (?, ?, ?, ?)", (key, seen, listing["price"], miles))
        if old["gone"] is not None:
            db.execute("INSERT OR IGNORE INTO seen_span VALUES (?, ?, ?)", (key, seen, seen))
            return "back"
        db.execute(
            "UPDATE seen_span SET stop = max(stop, ?) WHERE listing_id = ? AND start = "
            "(SELECT max(start) FROM seen_span WHERE listing_id = ?)", (seen, key, key))
        return "changed" if changed else "same"


def close_out(db, source, seen_ids, when, floor=FLOOR):
    """After a whole read of `source`, mark its live listings that were not among `seen_ids` as gone at `when`.
    Returns how many. Raises Shrunk, marking nothing, when the read found under `floor` of the live listings.
    Never call this after a partial read: gone is not decided from part of a source."""
    seen_ids = set(seen_ids)
    live = [row["id"] for row in db.execute("SELECT id FROM listing WHERE source = ? AND gone IS NULL", (source,))]
    missing = [key for key in live if key not in seen_ids]
    if live and len(live) - len(missing) < floor * len(live):
        raise Shrunk(f"{source}: found {len(live) - len(missing)} of {len(live)} live listings")
    with db:
        db.executemany("UPDATE listing SET gone = ?, gone_how = 'unseen' WHERE id = ?", [(when, key) for key in missing])
    return len(missing)


def end(db, listing_id, when, how):
    """Mark one listing over at `when` because its source says so outright: "sold", or "ended_unsold" for an
    auction lot that drew bids and was not sold. Unlike close_out and age_out, nothing is inferred."""
    with db:
        db.execute("UPDATE listing SET gone = ?, gone_how = ? WHERE id = ?", (when, how, listing_id))


def age_out(db, source, when, days=UNSEEN_DAYS):
    """Mark `source`'s live listings gone when no read has found them for `days`, though reads since have found
    others. Returns how many. close_out decides "gone" only from a whole read that did not shrink, and some
    reads are never quite whole (a count that moves while the pages are fetched, a second page never asked
    for) or shrink for good (a lot that sold half its cars); this is what lets those listings go. A source
    not read at all in that time keeps everything: its silence says nothing about its cars.
    Do not call it for a source whose list is cut short by design, where an old listing drops off the end
    while still for sale."""
    cutoff = (datetime.datetime.fromisoformat(when) - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M")
    with db:
        return db.execute(
            "UPDATE listing SET gone = ?, gone_how = 'unseen' WHERE source = ? AND gone IS NULL AND last_seen <= ? "
            "AND EXISTS (SELECT 1 FROM listing fresh WHERE fresh.source = ? AND fresh.last_seen > ?)",
            (when, source, cutoff, source, cutoff)).rowcount


def undecoded(db):
    """Every VIN in the catalogue that vPIC has not been asked about yet."""
    return [row["vin"] for row in db.execute(
        "SELECT DISTINCT vin FROM listing WHERE vin IS NOT NULL AND vin NOT IN (SELECT vin FROM vin_decode) ORDER BY vin")]


def save_decodes(db, rows, when):
    """Keep vPIC's rows ({vin: row}, from vin.decode) and give their listings the identity the VIN states.
    The VIN's answer wins over what the listing said, wherever vPIC gave one."""
    with db:
        for vin, row in rows.items():
            db.execute("INSERT OR REPLACE INTO vin_decode VALUES (?, ?, ?, ?)",
                       (vin, when, row.get("ErrorCode"), json.dumps(row, sort_keys=True)))
            known = {name: value for name, value in vins.identity(row).items() if value is not None}
            if not {"year", "make", "model"} <= set(known):
                continue
            for listing in db.execute(f"SELECT id, {', '.join(_IDENTITY)} FROM listing WHERE vin = ?", (vin,)).fetchall():
                merged = {name: known.get(name, listing[name]) for name in _IDENTITY}
                db.execute(
                    f"UPDATE listing SET {', '.join(f'{name} = ?' for name in _IDENTITY)}, identity_how = 'vin', "
                    "vehicle_key = ? WHERE id = ?",
                    (*merged.values(), listings.vehicle_key(*(merged[name] for name in
                                                              ("year", "make", "model", "trim", "body", "drive", "engine"))),
                     listing["id"]))


def save_dealers(db, dealers, when):
    """Keep the dealers discovery found, one row per key. A dealer found before keeps the date it was first found."""
    with db:
        for dealer in dealers:
            values = [_stored(name, dealer.get(name)) for name in _DEALER_FIELDS]
            db.execute(
                f"INSERT INTO dealer (key, {', '.join(_DEALER_FIELDS)}, found_by, first_found, last_found) "
                f"VALUES ({', '.join('?' * (len(_DEALER_FIELDS) + 4))}) "
                f"ON CONFLICT(key) DO UPDATE SET {', '.join(f'{name} = excluded.{name}' for name in _DEALER_FIELDS)}, "
                "found_by = excluded.found_by, last_found = excluded.last_found",
                (dealer["key"], *values, json.dumps(dealer.get("found_by") or []), when, when))
