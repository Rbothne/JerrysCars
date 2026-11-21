"""One reader per dealer website platform, so one reader covers every dealer on it (after aptrack/readers).

Each reader is `read(dealer, get, seen)` and gives back `(listings, complete)`. `dealer` is a row of
dealers.json, `get(url, **options)` fetches bytes, `seen` is this read's time. `complete` is False when the
reader could not see the dealer's whole inventory; only a complete read may mark cars as gone. A reader
that gets nothing usable raises NotRead."""

import html
import re
import urllib.parse

from ..listings import make_listing

_DRIVES = (("4x4", "4wd"), ("4wd", "4wd"), ("awd", "awd"), ("all wheel", "awd"), ("fwd", "fwd"), ("front", "fwd"),
           ("rwd", "rwd"), ("rear", "rwd"), ("4x2", "2wd"), ("2wd", "2wd"))


class NotRead(Exception):
    """The dealer's site answered, but not with an inventory this reader understands."""


def site(dealer):
    """The dealer's own address, scheme and host only. Without a full website address, "www." is assumed."""
    parts = urllib.parse.urlparse(dealer.get("website") or "")
    if parts.scheme and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return f"https://www.{dealer['host']}"


def text(fragment):
    """The words in a piece of HTML: tags out, entities read, spaces collapsed. None when nothing is left."""
    words = html.unescape(re.sub(r"<[^>]+>", " ", fragment or "")).replace("\xa0", " ")
    return " ".join(words.split()) or None


def drive(value):
    """A dealer's word for the driven wheels ("Fwd", "4x4", "All Wheel Drive") as the catalogue's."""
    value = (value or "").lower()
    return next((word for needle, word in _DRIVES if needle in value), None)


_REPORT = re.compile(r"""https:(?:\\?/){2}www\.carfax\.com\\?/(?:vehiclehistory|cfm)\\?/[^"'\s<>]+""")
_BADGE = re.compile(r"valuebadge\\?/([a-z0-9_]+)\.svg")


def history(fragment):
    """What a card says of the car's past: the address of the free Carfax report the dealer links, and what
    Carfax's own badge beside it claims ("1own": one owner; "great", "good", "fair": its view of the price).
    The plain "show me" badge claims nothing. Only what is there is given back."""
    found = {}
    report = _REPORT.search(fragment or "")
    if report:
        found["history_url"] = html.unescape(report.group().replace("\\/", "/"))
    badge = _BADGE.search(fragment or "")
    if badge:
        if badge.group(1).startswith("1own"):
            found["one_owner"] = True
        worth = next((word for word in ("great", "good", "fair") if badge.group(1).endswith(word)), None)
        if worth:
            found["carfax_value"] = worth
    return found


def dealer_listing(dealer, source_id, seen, **fields):
    """make_listing for a car on a dealer's own site: the dealer is the source, the seller and the place."""
    return make_listing(
        dealer["host"], source_id, seen=seen, channel="dealer_site", seller_type="dealer",
        seller_id=dealer["host"], seller_name=dealer.get("name"), city=dealer.get("city"), state=dealer.get("state"),
        zip=dealer.get("zip"), lat=dealer.get("lat"), lon=dealer.get("lon"),
        geo_how="street" if dealer.get("lat") is not None else None, **fields)


from . import (autorevo, carsforsale, carvana, dealeralchemist, dealercarsearch, dealercenter,  # noqa: E402  (they use the helpers above)
               dealerfire, dealeron, teamvelocity)

READERS = {
    "carvana": carvana.read,
    "dealeralchemist": dealeralchemist.read,
    "dealercenter": dealercenter.read,
    "carsforsale": carsforsale.read,
    "dealeron": dealeron.read,
    "autorevo": autorevo.read,
    "dealercarsearch": dealercarsearch.read,
    "teamvelocity": teamvelocity.read,
    "dealerfire": dealerfire.read,
}
