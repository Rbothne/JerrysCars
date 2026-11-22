"""What a private seller's own words say is wrong with the car, as a short list of flag names.

The words themselves are not kept: a description holds a phone number and whatever else the seller typed. A
reader passes the title and description through `found` once and keeps only the names that come back.

The patterns and their exceptions were worked out on 90 Craigslist listings read on 2026-11-21
(research/11-listing-quality.md). Plain words mislead: "need" stood beside no fault on 7 of 21 pages ("need
to sell"), every "accident" was a denial, six of seven "tow" were a tow package. So a hit is dropped when a
denial stands just before it ("no leaks", "zero check engine lights"), and each flag has its own exceptions.
On those pages nothing was flagged wrongly; on text they were not written from, expect about one wrong in ten.

    not_running        it does not run, or is sold for parts          \\
    mechanical_fault   a named part is failing, a warning light, a leak  > kept out of the comparison
    needs_work         it "needs" something, or something does not work /
    title_none         no title, a bill of sale only                  \\  as the title box would have said
    title_brand        salvage or rebuilt, said in the text           /
    damage             a wreck or damage is mentioned                 \\
    title_lien         money is still owed on it                       > shown, nothing more
    trade_seller       a dealer's turns of phrase                     /
"""

import re

OUT = ("not_running", "mechanical_fault", "needs_work", "title_none", "title_brand")   # no comparison for these
SHOWN = ("damage", "title_lien", "trade_seller")
WORDS = {"not_running": "not running", "mechanical_fault": "a mechanical fault", "needs_work": "needs work",
         "title_none": "no title", "title_brand": "a branded title", "damage": "damage mentioned",
         "title_lien": "money owed on it", "trade_seller": "reads like a trader's advert"}

_PART = (r"(?:motor|engine|trans(?:mission)?|tranny|head ?gaskets?|clutch|rear ?end|differentials?|transfer case|turbo"
         r"|oil cooler|timing (?:chain|belt))")
_DENIED = re.compile(r"(?:\bno|\bnot|\bnever|\bzero|\bwithout|\bw/o|n't|\bnon|\bany)[\s-]+(?:\w+[\s-]+){0,2}$|\bno$"
                     r"|\bno\b[^.!?]{0,40}\b(?:or|nor)\s+$")
_SITES = r"carfax|kbb|autocheck|youtube|youtu|craigslist|gmail|yahoo|hotmail|icloud|aol|outlook"

# name, the patterns, whether a denial just before a hit cancels it, and what may not follow a hit
_FLAGS = (
    ("not_running", (
        r"won't (?:start|crank|run|move|shift|go into|stay running)",
        r"(?:does|did)(?:n't| not) (?:run|start|crank|move|drive)|\bnot (?:running|driv(?:e)?able)|\bnon[- ]?runn(?:ing|er)",
        r"\blast r[au]n\b|ran when parked|only short distances",
        r"\bblown (?:\w+ )?" + _PART + r"|" + _PART + r" (?:is |was |has )?(?:blown|locked|seized|shot|gone)\b"
        r"|locked[- ]up|\bseized\b|rod knock|spun (?:a )?bearing|threw (?:a )?rod",
        r"\bparts? (?:car|truck|vehicle|only|out)\b|\bfor parts\b|parting (?:it )?out",
        r"\btow (?:it|truck|away)\b|must (?:be )?tow|needs? (?:to be )?(?:towed|trailered)|(?:bring|come with) (?:a |your )?trailer",
        r"mechanic'?s? special|handy ?man special"), True, None),
    ("mechanical_fault", (
        r"\bneeds? (?:\w+ ){0,3}" + _PART + r"\b",
        _PART + r"(?: \w+){0,4} (?:needs?\b|is bad|are bad|went out|going out|getting old|mess(?:ed|ing)? up|trouble|problems?|slip)",
        r"mis-?fir\w*", r"\bslip(?:s|ping)\b",
        r"(?:check|service) engine(?: soon)?(?: light)?\b|\bengine light\b|\bcel\b",
        r"over-?heat\w*|\bruns? hot\b|\bknock(?:s|ing)\b|\bsmok(?:es|ing)\b", r"\bleak(?:s|ing)?\b"), True, None),
    ("needs_work", (
        r"\bneeds\b|\b(?:will|does|would|may|might|gonna) need\b|\bneed(?:s|ed)? to be (?:replac|fix|repair)\w*",
        r"(?:does|do)(?:n't| not) work\b|\bnot (?:working|functioning)|(?:isn't|is not|ain't) (?:working|warm|cold|blowing)"
        r"|\binop\w*|(?:stopped|quit) working",
        r"\bknown issues?\b(?! or)", r"project (?:car|truck|vehicle)|needs (?:to be )?restor|fixer[- ]upper|needs tlc"),
     True, r"\s+(?:nothing|no\b|absolutely nothing|to go\b|to be gone|to sell\b|gone\b|a (?:new|good) home)"),
    ("damage", (
        r"\b(?:was|been|got) (?:hit|wrecked|totaled|totalled|rear[- ]ended)|\bwreck(?:ed)?\b|deer hit|hit (?:a|by a) deer|side ?swipe",
        r"\b(?:deer|hail|flood|fire|water|frame|body|front|rear|side|cosmetic|minor|some|bit of|amount of|had) damage\b"
        r"|\bdamage (?:to|on|from)\b|\bcosmetic (?:left|right|front|rear)\b",
        r"air ?bags? (?:deployed|light)|total(?:ed|led)\b"), True, None),
    ("title_lien", (
        r"\blien\b|\bbank (?:still )?(?:has|holds)\b|\bpay ?off\b|\bstill owe\b|\bowe (?:on|\$)|take over payments",),
     True, r"\s+free\b"),
    ("title_none", (
        r"\bno title\b|bill of sale|lost (?:the )?title|title (?:is )?(?:lost|missing)|missing title|bonded title"
        r"|applied for (?:a )?title|title (?:is )?in transit|open title|title (?:is )?not in my name",),
     False, r"\s+(?:issues?|problems?|worries)"),
    ("title_brand", (
        r"\bsalvaged?\b|rebuil[dt],? ?title|title,? (?:is )?rebuil[dt]|rebuilt salvage|reconstructed|branded title"
        r"|\br[- ]title\b|buy ?back|lemon law|flood (?:car|damage|title|vehicle)",), True, None),
    ("trade_seller", (
        r"(?:https?://|www\.)\S+|(?<![@\w.])(?!(?:" + _SITES + r")\.)[a-z0-9-]{3,}\.(?:com|net|org|biz)\b",
        r"trade[- ]?in'?s? (?:are )?welcome|we (?:take|accept) trades",
        r"\bwe (?:have|got) (?:\d+|two|three|several|more|other)\b|(?:more|other) (?:cars|trucks|vehicles) (?:available|for sale|in stock)"
        r"|\bour (?:inventory|lot|dealership|website)\b",
        r"ran through (?:the |our )?shop",
        r"\bwe finance|financing (?:is )?available|buy here|pay here|in[- ]house financ|down payment|\$ ?\d[\d,]* down\b"
        r"|no credit check|bad credit",
        r"\bstock ?(?:#|no\.?|number)|\bstk ?#|doc(?:ument)? fee|dealer fee|plus (?:tax|ttl|t\.t\.l)"), True, None),
)
_COMPILED = tuple((name, re.compile("|".join(f"(?:{pattern})" for pattern in patterns)), denied,
                   re.compile(after) if after else None) for name, patterns, denied, after in _FLAGS)


def found(*texts):
    """The flags the seller's words raise, in the order above. `texts` are the title, the description, or both."""
    words = " . ".join(text for text in texts if text).replace("’", "'").replace("‘", "'").lower()
    names = []
    for name, pattern, denied, after in _COMPILED:
        for hit in pattern.finditer(words):
            if denied and _DENIED.search(words[max(hit.start() - 30, 0):hit.start()]):
                continue
            if after and after.match(words, hit.end()):
                continue
            names.append(name)
            break
    return names


def say(names, which):
    """The plain words for those of `names` that are in `which` (OUT or SHOWN)."""
    return [WORDS[name] for name in names if name in which]
