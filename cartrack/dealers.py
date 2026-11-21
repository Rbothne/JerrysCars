"""Dealer discovery: which car dealers are near the home point, and which website platform each one runs on.

The platform matters because one reader covers every dealer on it (aptrack's "one reader per listing system").
The list comes from OpenStreetMap plus a hand-kept seed file. The platform comes from DNS first, which asks
nothing of the dealer's own site, and from the dealer's front page only when DNS says nothing."""

import json
import math
import socket
import urllib.parse

from . import fetch

OVERPASS = "https://overpass-api.de/api/interpreter"       # refuses browser user-agents, accepts a tool's own name

# Sites many businesses have a page on. An address there is not a dealer's own website.
SHARED = ("facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com", "tiktok.com", "yelp.com",
          "google.com", "goo.gl", "linktr.ee", "tesla.com")

# A name seen in a dealer's DNS answer -> the platform. Each entry was seen on a real dealer site
# (research/02-endpoints-dealers-reference.md, section 1.0).
DNS_NAMES = (
    ("secure.dealer.com", "dealer.com"),
    ("dealeronsite.com", "dealeron"),
    ("dealerinspire.com", "dealerinspire"),
    ("teamvelocity", "teamvelocity"),
    ("tvmoffset", "teamvelocity"),
    ("dealereprocess", "dealereprocess"),
    ("dealerfire.com", "dealerfire"),
    ("foxdealer.com", "foxdealer"),
    ("dealercenterwebsite.net", "dealercenter"),           # research/08-routing-unknowns.md
)

# Something a platform's pages load -> the platform. Asked only when DNS says nothing.
PAGE_MARKS = (
    ("static.overfuel.com", "overfuel"),
    ('content="overfuel"', "overfuel"),
    ("cdn.dlron.us", "dealeron"),
    ("dealerinspire.com", "dealerinspire"),
    ("secureoffersites.com", "teamvelocity"),
    ("cdn.dealereprocess.org", "dealereprocess"),
    ("cdn-ds.com", "dealerfire"),
    ("foxdealer", "foxdealer"),
    ("static.dealer.com", "dealer.com"),
    ("pictures.dealer.com", "dealer.com"),
    ("autorevo-powersites.com", "autorevo"),               # seen on Memphis independent lots, 2026-11-20
    ("dealercarsearch.com", "dealercarsearch"),
    ("bucket.dealeralchemist.com", "dealeralchemist"),     # seen on the lots discovery could not place, 2026-11-21
    ("cdn05.carsforsale.com", "carsforsale"),
    ("dealercenterwsstatic.net", "dealercenter"),
    ("assets.fastly.carvana.io", "carvana"),
)

# Whether a platform's inventory answers a plain request or needs a real browser (same research file).
# A platform not listed here has not been tested.
READS = {
    "dealeron": "plain",
    "teamvelocity": "plain",
    "dealerfire": "plain",
    "foxdealer": "plain",
    "overfuel": "plain",
    "dealeralchemist": "plain",
    "dealercenter": "plain",
    "carsforsale": "plain",
    "carvana": "plain",
    "dealer.com": "browser",
    "dealerinspire": "browser",
    "dealereprocess": "browser",
}

_EARTH_MILES = 3958.8
_NO_PAGE = (OSError, ValueError, fetch.Gone, fetch.RateLimited)    # a front page that could not be had: platform stays unknown


def host_of(website):
    """The dealer's own host from a website address, lower case and without "www.". None when there is no
    address, or it is a page on a shared site."""
    website = (website or "").strip()
    if not website:
        return None
    if "//" not in website:
        website = "//" + website
    host = (urllib.parse.urlparse(website).hostname or "").lower()
    host = host[4:] if host.startswith("www.") else host
    if "." not in host or any(host == shared or host.endswith("." + shared) for shared in SHARED):
        return None
    return host


def miles_between(a, b):
    """Straight-line miles between two (lat, lon) points."""
    lat_a, lon_a, lat_b, lon_b = map(math.radians, (*a, *b))
    half = math.sin((lat_b - lat_a) / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin((lon_b - lon_a) / 2) ** 2
    return 2 * _EARTH_MILES * math.asin(math.sqrt(half))


def box(home, miles):
    """(south, west, north, east) of the square that holds every point within `miles` of `home`."""
    lat, lon = home
    up = math.degrees(miles / _EARTH_MILES)
    across = math.degrees(2 * math.asin(math.sin(miles / (2 * _EARTH_MILES)) / math.cos(math.radians(lat))))
    return (round(lat - up, 4), round(lon - across, 4), round(lat + up, 4), round(lon + across, 4))


def overpass_query(bounds):
    """The OpenStreetMap question: every car dealer (shop=car) in the box, with its tags and one point each."""
    return f'[out:json][timeout:120];(nwr["shop"="car"]({",".join(str(edge) for edge in bounds)}););out center tags;'


def from_osm(payload):
    """Dealers from an Overpass answer. A shop with neither a name nor a website of its own is dropped."""
    found = []
    for element in payload.get("elements") or []:
        tags = element.get("tags") or {}
        website = tags.get("website") or tags.get("contact:website")
        host = host_of(website)
        point = element.get("center") or element
        if not (tags.get("name") or host) or point.get("lat") is None:
            continue
        street = " ".join(part for part in (tags.get("addr:housenumber"), tags.get("addr:street")) if part)
        found.append({
            "name": tags.get("name"),
            "host": host,
            "website": website,
            "lat": round(point["lat"], 5),
            "lon": round(point["lon"], 5),
            "street": street or None,
            "city": tags.get("addr:city"),
            "state": tags.get("addr:state"),
            "zip": tags.get("addr:postcode"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "brand": tags.get("brand"),
            "used_only": True if tags.get("second_hand") == "only" else None,
            "osm": f"{element['type']}/{element['id']}",
            "found_by": ["osm"],
        })
    return found


def _first(text, table):
    text = text.lower()
    return next((platform for needle, platform in table if needle in text), None)


def platform_of(names):
    """The platform named by any of the DNS `names` a dealer's host answered with, or None."""
    return next((platform for platform in (_first(name, DNS_NAMES) for name in names) if platform), None)


def page_platform(page):
    """The platform a dealer's front page gives away by what it loads, or None."""
    return _first(page, PAGE_MARKS)


def _resolved(host, resolve):
    for name in ("www." + host, host):
        try:
            canonical, aliases, _ = resolve(name)
        except (OSError, UnicodeError):
            continue
        return name, list(dict.fromkeys(answer.lower() for answer in (canonical, *aliases)))
    return None, None


def lookup(host, resolve=socket.gethostbyname_ex):
    """Every name DNS gives for the dealer's host ("www." first, then bare), or None when neither resolves."""
    return _resolved(host, resolve)[1]


def _seeded(seed, home):
    host = host_of(seed.get("website"))
    if not host:
        return None
    placed = seed.get("lat") is not None and seed.get("lon") is not None
    return {
        "name": seed.get("name"), "host": host, "website": seed.get("website"),
        "lat": seed.get("lat") if placed else None, "lon": seed.get("lon") if placed else None,
        "miles": round(miles_between(home, (seed["lat"], seed["lon"])), 1) if placed else None,
        "street": seed.get("street"), "city": seed.get("city"), "state": seed.get("state"), "zip": seed.get("zip"),
        "phone": seed.get("phone"), "brand": seed.get("brand"), "used_only": seed.get("used_only"),
        "osm": None, "found_by": ["seed"],
    }


def discover(area, seeds=(), fetch=fetch.get, resolve=socket.gethostbyname_ex):
    """Every dealer within the area's radius of its home point, nearest first, each with its platform and
    whether that platform's inventory answers a plain request. `seeds` are hand-kept dealers
    ({"name", "website", ...}) that OpenStreetMap lacks; one already found merges into what was found."""
    home, radius = tuple(area["home"]), area["radius_miles"]
    question = urllib.parse.urlencode({"data": overpass_query(box(home, radius))}).encode()
    payload = json.loads(fetch(OVERPASS, data=question, timeout=180))

    found = {}
    for dealer in from_osm(payload):
        dealer["miles"] = round(miles_between(home, (dealer["lat"], dealer["lon"])), 1)
        key = dealer["host"] or "osm:" + dealer["osm"]
        if dealer["miles"] <= radius and (key not in found or dealer["miles"] < found[key]["miles"]):
            found[key] = dealer                       # a group's one website has several lots: keep the nearest

    for seed in seeds:
        dealer = _seeded(seed, home)
        if dealer is None:
            continue
        known = found.get(dealer["host"])
        if known is None:
            found[dealer["host"]] = dealer
            continue
        known["found_by"] = [*known["found_by"], "seed"]
        for name, value in dealer.items():
            if known.get(name) is None and value is not None:
                known[name] = value

    for key, dealer in found.items():
        dealer["key"] = key
        dealer["resolves"] = dealer["platform"] = dealer["reads"] = None
        if not dealer["host"]:
            continue
        name, names = _resolved(dealer["host"], resolve)
        dealer["resolves"] = name is not None
        if name is None:
            continue
        dealer["platform"] = platform_of(names)
        if dealer["platform"] is None:
            try:
                dealer["platform"] = page_platform(fetch(f"https://{name}/", timeout=20, tries=1).decode("utf-8", "replace"))
            except _NO_PAGE:
                pass
        dealer["reads"] = READS.get(dealer["platform"])

    return sorted(found.values(), key=lambda dealer: (dealer["miles"] is None, dealer["miles"] or 0, dealer["name"] or ""))
