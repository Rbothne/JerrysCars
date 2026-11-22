"""Tow-lot and garage lien sales, from the public notices The Daily News prints.

A garage or tow lot that is owed money on a car must advertise before selling it. In Memphis those notices run
in The Daily News, whose site lists each day's at `/notices/{YYYY}/{Mon}/{D}/`, one request a day (robots.txt
allows /notices/). Under `<a id="misc">` each notice is a table row: an ad number, then lines of text. The cars
are sold in person at the lot, a week or two after the notice, and the notice gives no price.

**A notice also prints the owner's name beside each car, and often the lienholder's.** Nothing is done to
recognise names. Only what matches a pattern is kept, and a name matches none of them:

- each 17-character VIN, and never the text that follows it on its line;
- the "year and words" beside it ("2018 Kia Optima"), tried on the VIN's own line, at the end of the sentence
  before it, on the line before and on the line after, and accepted only when the year agrees with the VIN's
  own model-year character. That agreement is what tells a car's line from a stray one;
- the sale's date, hour and address, by pattern, from the notice's heading or from the car's own line;
- the seller, only where the notice says "sold at auction by ..." and the name has a business word in it: three
  of eleven such sellers were a person.

Every other line is discarded unread. Seen on six days' pages in November 2026: 47 notices, 265 cars, words
found for 97% of them (research/11-routing-more-marketplaces.md).

A listing is one car in one notice. It has no price ("starting" with none), `ends` is the day of the sale, and
`extra` holds the printed hour and the address. Year, make and model come from decoding the VIN; the printed
words are only the title. A read is never whole: a notice is printed once or twice and the sale comes later,
so these listings are not aged out when the paper stops printing them; they expire the day after the sale.
The first read looks back two weeks, later ones three days."""

import datetime
import html
import re

from .. import fetch
from ..listings import make_listing
from ..readers import NotRead

FIRST_DAYS, DAYS = 14, 3
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_VIN = re.compile(r"(?<![A-Z0-9])[A-HJ-NPR-Z0-9]{17}(?![A-Z0-9])")
_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"         # the VIN's tenth character: 1980 on, repeating every 30 years
_WORDS = re.compile(r"^(?:(19[5-9]\d|20[0-3]\d)|(\d\d))\s+([A-Za-z][\w&./-]*(?:\s+[\w&./()-]+){0,5})\s*$")
_TAIL = re.compile(r"(?:^|[,.;:]\s*|\s)((?:19[5-9]\d|20[0-3]\d)\s+[A-Za-z][\w&/-]*(?:\s+[\w&/()-]+){0,4})$")
_DATE = re.compile(r"(?<!\d)(\d{1,2})\s*[/\\-]\s*(\d{1,2})\s*[/\\-]\s*(\d{4}|\d{2})(?!\d)")
_DATE_WORDS = re.compile(r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})")
_HOUR = re.compile(r"(?i)(?:@|\bat\b|\s)\s*(\d{1,2})(?::(\d\d))?\s*([ap])\.?\s?m\b\.?|\b(12\s+noon|noon)\b")
_ADDRESS = re.compile(r"(?i)(\d{2,5}\s+(?:(?!\bat\b|@)[A-Za-z0-9 .#&-]){3,45}?)[.,]?\s+([A-Za-z ]{3,20}),\s*(TN|MS|AR)\.?,?\s+(\d{5})")
#                              the street may not run across an "at" or "@": "12/05/2026 at 10 am located at 3301 Winbrook Drive"
_BUSINESS = re.compile(r"(?i)\b(llc|inc|towing|tow|wrecker|recovery|auto|automotive|motors?|imports|sales|service"
                       r"|garage|repair|center|collision|storage|transport|truck)\b")
_CITIES = ("West Memphis", "Olive Branch", "Horn Lake", "Memphis", "Southaven", "Millington", "Bartlett", "Germantown",
           "Collierville", "Cordova", "Arlington", "Lakeland", "Piperton", "Jackson", "Marion", "Hernando")
_FOOT = re.compile(r"^[A-Z][a-z]{2}\.? \d{1,2}, \d{4}\W{0,3}[A-Za-z]{2}\d+$")     # "Nov. 20, 2026 Md117766": the printing


def _years(vin):
    """The model years the VIN's tenth character can stand for, up to next year's."""
    if vin[9] not in _YEAR_CODES:
        return []
    first = 1980 + _YEAR_CODES.index(vin[9])
    return [year for year in (first, first + 30, first + 60) if year <= datetime.date.today().year + 1]


def _words(lines, at, vin):
    """(year, the words printed for the car) from beside the VIN on lines[at], or None when nothing agrees."""
    line = lines[at]
    before = re.sub(r"(?i)[\s,:;–—-]*(vin)?\s*(no\.?|number)?\s*[#:.]?\s*$", "", line[:line.find(vin)]).strip(" -–—,:;")
    tail = _TAIL.search(before)
    tries = [before] + ([tail.group(1)] if tail else []) + ([lines[at - 1]] if at else []) + lines[at + 1:at + 2]
    years = _years(vin)
    for said in tries:                                # never the text after the VIN: that is where names are
        found = _WORDS.match(said.strip())
        if not found:
            continue
        year = int(found.group(1)) if found.group(1) else next((year for year in years if year % 100 == int(found.group(2))), None)
        if year in years:
            return year, found.group(3)
    return None


def _date(said):
    found = _DATE.search(said)
    if found:
        month, day, year = (int(part) for part in found.groups())
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"{year + (2000 if year < 100 else 0):04d}-{month:02d}-{day:02d}"
    found = _DATE_WORDS.search(said)
    return f"{int(found.group(3)):04d}-{_MONTHS.index(found.group(1).title()) + 1:02d}-{int(found.group(2)):02d}" if found else None


def _hour(said):
    found = _HOUR.search(said)
    if not found:
        return None
    if found.group(4):
        return "12:00"
    return f"{int(found.group(1)) % 12 + (12 if found.group(3).lower() == 'p' else 0):02d}:{found.group(2) or '00'}"


def _place(found):
    """(street, city, state, zip) from an address match. A notice often runs the street into the city with no
    comma ("3501 KNIGHT ARNOLD MEMPHIS, TN. 38118"): a known city's name at the end is taken for the city."""
    street, city, state, zip5 = (part.strip() for part in found.groups())
    known = next((name for name in _CITIES if city.lower().endswith(name.lower())), None)
    if known and len(city) > len(known):
        street, city = f"{street} {city[:-len(known)].strip()}", known
    return street, known or city.title(), state.upper(), zip5


def _notices(page):
    """Each notice under the page's miscellaneous heading that sells a vehicle: (ad number, its lines)."""
    at = page.find('<a id="misc">')
    if at < 0:
        raise NotRead("the notices page has no miscellaneous section")
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page[at:], re.S):
        ad = re.search(r"OpenChildFT2\('([^']+)'", row)
        lines = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", part)).split()) for part in re.split(r"</p>|<br\s*/?>", row)]
        lines = [line for line in lines if line and line != "View" and not _FOOT.match(line) and "... more" not in line]
        said = " ".join(lines)
        if ad and _VIN.search(said) and re.search(r"(?i)sold|auction|sale", said):
            yield ad.group(1), lines


def _cars(place, ad, lines, printed, address_of_page, seen):
    """A listing for each car of one notice."""
    heading = " ".join(line for line in lines if not _VIN.search(line))
    hour, address = _hour(heading), _ADDRESS.search(heading)
    named = re.search(r"(?i)sold at auction by (.+?) on ", heading)
    seller = named.group(1).strip() if named and _BUSINESS.search(named.group(1)) else None
    date = None
    for at, line in enumerate(lines):
        vins = [vin for vin in _VIN.findall(line) if re.search(r"\d", vin) and re.search(r"[A-Z]", vin)]
        if not vins:
            date = _date(line) or date                # the latest date line above a car is that car's sale day
            continue
        here = _ADDRESS.search(line[:line.find(vins[0])]) or address
        day = _date(line[:line.find(vins[0])]) or date
        for vin in vins:
            found = _words(lines, at, vin)
            where = _place(here) if here else None
            yield make_listing(
                place["key"], f"{ad}-{vin}", seen=seen, channel="auction", price_kind="starting", url=address_of_page,
                title=f"{found[0]} {found[1]}" if found else f"Vehicle {vin}", vin=vin, year=found[0] if found else None,
                posted=f"{printed}T00:00", ends=f"{day}T00:00" if day and day >= printed else None, seller_name=seller,
                city=where[1] if where else None, state=where[2] if where else None, zip=where[3] if where else None,
                extra={name: value for name, value in (
                    ("ad", ad), ("hour", hour), ("address", f"{where[0]}, {where[1]}, {where[2]} {where[3]}" if where else None))
                    if value})


def read(place, get, seen, known=(), days=None):
    base = place["site"].rstrip("/")
    today = datetime.date.fromisoformat(seen[:10])
    found, read_any = {}, False
    for back in range(days or (DAYS if known else FIRST_DAYS)):
        day = today - datetime.timedelta(days=back)
        address = f"{base}/notices/{day.year}/{_MONTHS[day.month - 1]}/{day.day}/"
        try:
            page = get(address).decode("utf-8", "replace")
        except fetch.RateLimited:
            break                                     # asked to slow down: the other days wait for the next run
        except (OSError, ValueError):
            continue                                  # that day is asked for again on the next run
        try:
            notices = list(_notices(page))
        except NotRead:
            continue                                  # a day with no miscellaneous notices at all
        read_any = True
        for ad, lines in notices:
            for car in _cars(place, ad, lines, day.isoformat(), address, seen):
                if car:
                    found.setdefault(car["id"], car)  # a notice printed twice: the later printing is read first
    if not read_any:
        raise NotRead(f"{base}: no day's notices could be read")
    return list(found.values()), False
