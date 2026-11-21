"""Dealer Car Search: independent lots. `/inventory?pagesize=100` is one HTML page of up to 100 vehicle cards.

The platform has numbered page templates whose class names differ (i08r_, i10r_, i17r_ seen so far), so this
matches what they share: the card wrapper, the link's label, the option lines and the price. Only the box
labelled "Retail Price" is taken as the asking price; one template shows a bare figure that turned out to be
a down payment, and that is kept in `extra` instead. Seen working on
901scm.com, importsofmemphis.com and victoryauto.org, 2026-11-20. A lot with exactly 100 cards on the page may
have more behind it; reading a second page has not been tried, so that read is reported as partial."""

import html
import re

from . import NotRead, dealer_listing, drive, site, text
from ..listings import num

PAGE = 100
_CARD = r'(?=<div class="[^"]*infinite-scroll-current-page)'
_PHOTO = r"""(?:data-src|src)=['"](https://imagescdn\.dealercarsearch\.com/Media/[^'"]+)"""


def _listing(dealer, base, card, seen):
    link = re.search(r'href="(/vdp/(\d+)/[^"]*)"', card)
    label = re.search(r'<a aria-label="([^"]*)" href="/vdp/', card)
    if not (link and label):
        return None
    title = " ".join(html.unescape(label.group(1)).split())
    trim = text("".join(re.findall(r'<span class="vehicleTrim">(.*?)</span>', card, re.S)[:1]))
    named = (title[:-len(trim)] if trim and title.endswith(trim) else title).split()
    year = named[0] if named and named[0].isdigit() else None
    rest = named[1:] if year else named
    facts = {}
    for name, value in re.findall(r'class="i\d+r_opt(\w+)">(.*?)</p>', card, re.S):
        value = text(re.sub(r"<label.*?</label>", "", value, flags=re.S))
        if value and name.lower() not in facts:       # a template may print a line twice, once empty
            facts[name.lower()] = value
    price = re.search(r"""class=['"]price-2['"]>([^<]*)""", card)          # the box labelled "Retail Price"
    bare = re.search(r'class="lblPrice[^"]*">([^<]*)', card)                # a figure with no label at all
    photo = re.search(_PHOTO, card)
    extra = {"stock": facts.get("stock")}
    if bare and not price and num(bare.group(1)) is not None:
        extra["unlabelled_price"] = int(num(bare.group(1)))    # seen to be a down payment, so not the asking price
    return dealer_listing(
        dealer, link.group(2), seen,
        url=base + link.group(1),
        title=title,
        price=price.group(1) if price else None,
        vin=facts.get("vin"), year=year, make=rest[0] if rest else None, model=" ".join(rest[1:]) or None, trim=trim,
        drive=drive(facts.get("drive")), engine=facts.get("engine"), transmission=facts.get("trans"),
        fuel=facts.get("fuel"), miles=facts.get("mileage"), color=facts.get("color"),
        photos=[photo.group(1)] if photo else [],
        extra=extra)


def read(dealer, get, seen):
    base = site(dealer)
    cards = re.split(_CARD, get(f"{base}/inventory?pagesize={PAGE}").decode("utf-8", "replace"))[1:]
    found = [listing for listing in (_listing(dealer, base, card, seen) for card in cards) if listing]
    if not found:
        raise NotRead(f"{dealer['host']}: no vehicle cards on /inventory")
    return found, len(cards) < PAGE
