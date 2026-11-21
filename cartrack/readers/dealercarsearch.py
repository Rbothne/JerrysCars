"""Dealer Car Search: independent lots. `/inventory?pagesize=100` is an HTML page of up to 100 vehicle cards,
and `&page=2` the next hundred.

The platform has numbered page templates whose class names differ (i08r_, i10r_, i17r_ seen so far), so this
matches what they share: the card wrapper, the link's label, the option lines and the price. Only the box
labelled "Retail Price" is taken as the asking price; one template shows a bare figure that turned out to be
a down payment, and that is kept in `extra` instead. Seen working on
901scm.com, importsofmemphis.com and victoryauto.org, 2026-11-20. No lot here has over 100 cars, so paging was
checked small: on victoryauto.org, 2026-11-21, `pagesize=25` gave 25 cards and `&page=2` gave 25 others. Pages
are read until one comes back short. A full page that brings nothing new means the site ignored the page
number, and that read is reported as partial."""

import html
import re

from . import NotRead, dealer_listing, drive, every, history, site, text
from ..listings import num

PAGE = 100
MAX_PAGES = 20
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
    extra = {"stock": facts.get("stock"), **history(card)}
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
    found, ids, complete = [], set(), False
    for number in range(1, MAX_PAGES + 1):
        address = f"{base}/inventory?pagesize={PAGE}" + (f"&page={number}" if number > 1 else "")
        cards = re.split(_CARD, get(address).decode("utf-8", "replace"))[1:]
        fresh = [car for car in every((_listing(dealer, base, card, seen) for card in cards), dealer["host"])
                 if car["id"] not in ids]
        ids.update(car["id"] for car in fresh)
        found += fresh
        if len(cards) < PAGE:
            complete = True                           # a short page is the last one
        if len(cards) < PAGE or not fresh:
            break
    if not found:
        raise NotRead(f"{dealer['host']}: no vehicle cards on /inventory")
    return found, complete
