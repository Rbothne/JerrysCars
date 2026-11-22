# 11. Listing quality: telling a sound cheap car from a problem on Craigslist

Worked 2026-11-21 on the catalogue as it stood at 22:02 UTC (293 Craigslist by-owner listings in seven sites; it
held 291 when the question was set) and on **90 listing pages** read that evening: plain GET, `cartrack/0.1`, one
at a time, 3.5 s apart, each page once. All 90 answered 200; nothing was refused or slowed. 90 was the limit, so
no further page can be read under this brief. Nothing else was asked of Craigslist: its help pages are quoted
second-hand for that reason.
Scripts, the request ledger and the saved pages are in `research/_scratch/listing-quality/` (gitignored). Sellers'
descriptions were read there and nowhere else; this note quotes short phrases only.
Labels: TESTED = measured here, DOCUMENTED = read in the source's own text, REPORTED = second-hand.

**How to read the counts.** 76 of the 90 pages are a spread sample: one page per car (cars posted twice counted
once), taken evenly across each site's price order (Memphis 23, Little Rock 18, North Mississippi 11, Jackson 8,
Southeast Missouri 6, Jonesboro 5, Muscle Shoals 5; one seller with 34 listings held to 3). Ten more were chosen
on purpose (both ends of same-site reposts, a cross-posted twin) and four to test a seller rule. Shares of the
catalogue are estimated from the 76 and given with a range; counts marked "exact" were run on all 293.
The flag patterns below were written after reading these same pages, so "0 false alarms" is a fit, not a
forecast. Two outside checks follow the flags.

## Recommendation

### What to change, and how many of the 293 listings each change touches

| # | Change | Listings touched | Basis |
|---|---|---|---|
| 1 | Set flags from the description when a listing page is read; keep the flag names, never the text | kept out of the ranking: 22 of 76 pages; 11 of those are not already out by title or condition box, so **about 40 more of 293** (24 to 71). Shown with a note only: 9 of 76, **about 35** (19 to 62) | estimate |
| 2 | Treat the condition box "fair" or "salvage" as a caution | **27** (18 of them with a clean title) | exact |
| 3 | One car, however often posted: match on shared photo ids, not on year + miles + price + pin | **45 listings are 22 cars**; 23 rows fold away. The present rule folds 20; photo ids fold 3 more | exact |
| 4 | Keep `repost_of` from the page: the listing is a re-post of an older one | 22 of 76 pages, **about 85 of 293** (58 to 117); for 21 of the 30 found, the older post is more than 30 days older | estimate |
| 5 | Keep `data-accuracy`; say on the page when a distance is to a ZIP's centre | **198** ZIP centre, 62 placed by the seller, 33 street-level | exact |
| 6 | Group listings by seller; mark a group with three or more different cars a trader | **60 listings (42 cars) in 5 groups**; 41 of the 60 already have a title that is not clean | exact |
| 7 | Keep matching listings on the address key, and hold `post_id` as a second key | all 293; nothing visible changes | - |

Today 73 of 293 are shown but not judged (69 by the title box, 4 more by the six title cautions). With changes
1 and 2 that becomes roughly 125 to 130. Of the 76 spread pages, 46 would still be judged; 11 of those 46 are a
trader's by my reading, and 32 of the 76 are judged, carry no flag of any kind and are not a trader's.

One practical point: the reader asks for each listing page once and never again, so flags, `repost_of` and
`data-accuracy` reach only listings read after the change. Listings live 30 days at most, so the catalogue renews
itself in a month; reading the known ones again would be about 290 requests, 15 minutes at the present pace.

### 1. The flags

Text is the title, then " . ", then the description, with curly apostrophes made straight and runs of white
space made one space; matching ignores case. A hit is **dropped** when a denial stands just before it:

```python
NEG = r"(?:\bno|\bnot|\bnever|\bzero|\bwithout|\bw/o|n't|\bnon|\bany)[\s-]+(?:\w+[\s-]+){0,2}$|\bno$|\bno\b[^.!?]{0,40}\b(?:or|nor)\s+$"
# looked for in the 30 characters before the hit: "No Leaks", "Zero check engine lights", "no clutch slippage",
# "no mechanical issues or check engine light"
PART = r"(?:motor|engine|trans(?:mission)?|tranny|head ?gaskets?|clutch|rear ?end|differentials?|transfer case|turbo|oil cooler|timing (?:chain|belt))"
```

Counts are pages hit / truly so / false alarm / missed, on the 90 pages; "spread" is the share of the 76.

**`not_running`** - out of the ranking. 5 / 5 / 0 / 0; spread 5 of 76; 3 of the 5 have a clean title box.

```python
r"won'?t (?:start|crank|run|move|shift|go into|stay running)"
r"(?:does|did)(?:n'?t| not) (?:run|start|crank|move|drive)|\bnot (?:running|driv(?:e)?able)|\bnon[- ]?runn(?:ing|er)"
r"\blast r[au]n\b|ran when parked|only short distances"
r"\bblown (?:\w+ )?" + PART + r"|" + PART + r" (?:is |was |has )?(?:blown|locked|seized|shot|gone)\b|locked[- ]up|\bseized\b|rod knock|spun (?:a )?bearing|threw (?:a )?rod"
r"\bparts? (?:car|truck|vehicle|only|out)\b|\bfor parts\b|parting (?:it )?out"
r"\btow (?:it|truck|away)\b|must (?:be )?tow|needs? (?:to be )?(?:towed|trailered)|(?:bring|come with) (?:a |your )?trailer"
r"mechanic'?s? special|handy ?man special"
```

Exceptions, by construction: "tow package", "tow hitch", "towing" (6 of the 7 pages with "tow" are these);
"extra parts", "spare parts", "new parts" (3 of the 10 pages with "parts"); "won't answer a call", "won't reply".

**`mechanical_fault`** - out of the ranking. 9 / 9 / 0 / 1 (the one missed says "blown motor" and is caught by
`not_running`); spread 9 of 76, all 9 with a clean title box.

```python
r"\bneeds? (?:\w+ ){0,3}" + PART + r"\b"
PART + r"(?: \w+){0,4} (?:needs?\b|is bad|are bad|went out|going out|getting old|mess(?:ed|ing)? up|trouble|problems?|slip)"
r"mis-?fir\w*"
r"\bslip(?:s|ping)\b"
r"(?:check|service) engine(?: soon)?(?: light)?\b|\bengine light\b|\bcel\b"
r"over-?heat\w*|\bruns? hot\b|\bknock(?:s|ing)\b|\bsmok(?:es|ing)\b"
r"\bleak(?:s|ing)?\b"
```

Exceptions: the denial guard ("No Leaks", "Zero check engine lights", "no clutch slippage", one page each);
"transmission replaced in 2024", "newly rebuilt transmission", "new Jasper engine" do not match because no
fault word follows the part.

**`needs_work`** - out of the ranking (the price already answers for the need, and the reader cannot cost it);
if the owner wants a "cheap, needs work" list, the 8 pages with this flag and neither flag above are that list.
13 / 13 / 0 / 0; spread 13 of 76, 12 with a clean title box.

```python
r"\bneeds\b|\b(?:will|does|would|may|might|gonna) need\b|\bneed(?:s|ed)? to be (?:replac|fix|repair)\w*"
r"(?:does|do)(?:n'?t| not) work\b|\bnot (?:working|functioning)|(?:isn'?t|is not|ain'?t) (?:working|warm|cold|blowing)|\binop\w*|(?:stopped|quit) working"
r"\bknown issues?\b(?! or)"
r"project (?:car|truck|vehicle)|needs (?:to be )?restor|fixer[- ]upper|needs tlc"
# not a hit when followed by:  \s+(?:nothing|no\b|absolutely nothing|to go\b|to be gone|to sell\b|gone\b|a (?:new|good) home)
```

Exceptions: "needs nothing mechanically" (1 page); and every "need" whose subject is the seller, which the
pattern never matches because it wants "needs" or "will/does need": "I need a smaller truck", "need to sell",
"no longer need", "if you don't need the tires", "if I need to" (5 pages). "needs to go" is excepted by name.

**`damage`** - shown only. 9 / 9 / 0 / 0; spread 7 of 76. Four of the nine are repaired or cosmetic on a car
that otherwise reads sound, which is why it should not remove a car.

```python
r"\b(?:was|been|got) (?:hit|wrecked|totaled|totalled|rear[- ]ended)|\bwreck(?:ed)?\b|deer hit|hit (?:a|by a) deer|side ?swipe"
r"\b(?:deer|hail|flood|fire|water|frame|body|front|rear|side|cosmetic|minor|some|bit of|amount of|had) damage\b|\bdamage (?:to|on|from)\b|\bcosmetic (?:left|right|front|rear)\b"
r"air ?bags? (?:deployed|light)|total(?:ed|led)\b"
```

Exceptions: the bare word "accident" is not used at all: all 5 pages with it are denials ("no accidents",
"accident free", "never been in any accidents", and once run together as one word, which no guard catches).
"no dents or damage" falls to the guard. "airbags", "collision warning", "sub frame" as equipment do not match.

**`title_lien`**, **`title_none`**, **`title_brand`** - the text against the title box. When the box says clean
and the text does not, believe the text: `title_none` and `title_brand` then act as the box would (out);
`title_lien` is shown only. 3 / 3 / 0, 1 / 1 / 0 and 3 / 3 / 0. Only the lien pages (one truck on three sites,
"bank has clean title") contradict a clean box; the other four repeat what the box already says.
**No page of the 90 says salvage or rebuilt in the text while the box says clean.**

```python
# title_lien; not a hit when followed by "free"; denial guard on ("no lien")
r"\blien\b|\bbank (?:still )?(?:has|holds)\b|\bpay ?off\b|\bstill owe\b|\bowe (?:on|\$)|take over payments"
# title_none; no denial guard; not a hit when followed by "issues", "problems" or "worries"
r"\bno title\b|bill of sale|lost (?:the )?title|title (?:is )?(?:lost|missing)|missing title|bonded title|applied for (?:a )?title|title (?:is )?in transit|open title|title (?:is )?not in my name"
# title_brand; denial guard on
r"\bsalvaged?\b|rebuil[dt],? ?title|title,? (?:is )?rebuil[dt]|rebuilt salvage|reconstructed|branded title|\br[- ]title\b|buy ?back|lemon law|flood (?:car|damage|title|vehicle)"
```

Exception that matters: the bare word "rebuilt" is on 5 pages, and 2 of them are a rebuilt transmission. The
pattern wants "title" beside it.

**`trade_seller`** - shown only, as "looks like a trader", and joined to the seller group of change 6.
6 / 6 / 0 / 0; spread 6 of 76. It finds 6 of the 21 pages I take for a trader's: traders posing as owners
mostly leave these words out, which is the point of posing.

```python
r"(?:https?://|www\.)\S+|(?<![@\w.])(?!(?:carfax|kbb|autocheck|youtube|youtu|craigslist|gmail|yahoo|hotmail|icloud|aol|outlook)\.)[a-z0-9-]{3,}\.(?:com|net|org|biz)\b"
r"trade[- ]?in'?s? (?:are )?welcome|we (?:take|accept) trades"
r"\bwe (?:have|got) (?:\d+|two|three|several|more|other)\b|(?:more|other) (?:cars|trucks|vehicles) (?:available|for sale|in stock)|\bour (?:inventory|lot|dealership|website)\b"
r"ran through (?:the |our )?shop"
r"\bwe finance|financing (?:is )?available|buy here|pay here|in[- ]house financ|down payment|\$ ?\d[\d,]* down\b|no credit check|bad credit"
r"\bstock ?(?:#|no\.?|number)|\bstk ?#|doc(?:ument)? fee|dealer fee|plus (?:tax|ttl|t\.t\.l)"
```

Exceptions: "no financing" (4 pages, 2 cars, all the finance words there are) falls to the guard; a family's
"we" ("we have owned it four years", "we are selling") does not match because a number or "more/other" must
follow; "serviced by a dealer" does not match.

**Outside checks (TESTED).** (a) The same patterns on the 293 titles alone hit 9 listings, 5 of them pages I had
not read; all 9 are right ("won't start", "mechanic special / as-is", "excellent car for parts", "needs major
repairs"). (b) On 80 Washington-area postings saved on 20 November (title plus the first 300 characters only;
40 from the owner category, 40 from the dealer category): in the 40 owner postings the first version of the
patterns hit 5 and 3 were wrong ("needs to go ASAP", "no mechanical issues or check engine light", a link to an
article about the car's history). The first two are now excepted; the link still hits. In the 40 dealer postings
`trade_seller` hit 22 on 300 characters, 16 by a web address, 7 by "we have many other", 5 by "we finance".
So expect roughly one wrong hit in ten on text it has not seen, and review the hits now and then.

**Against the present rule.** `build.py`, as it stood in the working tree that evening, reads ten cautions from
the title only. On the 293 titles they touch 6
listings. Run unchanged over the 90 descriptions they would hit 22 pages, 17 rightly and 5 wrongly (all five
from the bare "needs" and "project"), and would miss four stated faults: a misfire, a slipping transmission, a
service-engine light, an oil and coolant leak. The lists above are those ten, tightened and extended.

### 2. The condition box

Already kept, and the seller's own word. On the 90 pages, 8 of the 9 that say "fair" or "salvage" state a fault
in the text; none of the 33 that say "excellent", "like new" or "new" do; "good" does in 7 of 31, blank in 4 of
17 (TESTED). Treat fair and salvage as a caution: 27 listings, 18 with a clean title, median price $2,000
against $6,898 for the rest (exact). This needs no new read.

### 3. The repost rule

**Two listings are one car when they share a photo id.** The id is the middle part of a photo's address:
`images.craigslist.org/00K0K_34mMtDiAmy4_0x20oM_600x450.jpg` is photo `34mMtDiAmy4`. The reader already keeps
the first 12 addresses; put the ids in `photo_ids` (the field exists and is empty for Craigslist), all of them,
since 25 of 90 pages have more than 12 photos.

- In the catalogue this joins **45 listings into 22 cars** (TESTED, exact). 17 pairs are one seller putting each
  car on Memphis and North Mississippi minutes apart; one truck is on three sites; four cars were posted twice on
  one site, 2 to 17 days apart.
- No two different cars share a photo: in all 22 groups the odometer is identical (TESTED).
- The present rule (year, miles, price, pin) finds 19 of the 22 groups. It misses a car whose price went from
  $4,850 to $5,800 on the second posting, one whose year was retyped 1998 to 1997, and one whose pin moved.
- Title alone finds 17 groups; title + price + odometer 16.
- 9 listings have no photos. For those keep the present rule.

**Second key, from the page: `repost_of`.** A page made with Craigslist's repost button carries
`'repost_of': <post id>` in a script; other pages do not carry the key at all (TESTED: 30 of 90 pages have it).
Read it with `'repost_of':\s*(\d+)`.

- Where both ends were in view it named the same car's earlier post: three cars of three (TESTED).
- It does not link copies on different sites: the two-site and three-site cars each name different older posts,
  or none (TESTED).
- It is not always the same car. One seller's two listings point at posts about five years old by their
  numbers, which reads as an old advert reused for the next car. So: same `repost_of` (or `repost_of` equal to
  the other's post id) **and** the same odometer is the same car; `repost_of` alone is the same seller.
- It misses a seller who simply writes a second advert (one pair of the four same-site pairs). Photo ids catch
  that pair.
- Its better use is the age of the advert. Post ids rise steadily: 0.548 million a day over the last 30 days,
  with `posted` never out of order across 293 listings and a straight line through them never off by more than
  half a day (TESTED). So `posted - (post_id - repost_of) / 548,000 days` dates the first posting. For 21 of the
  30 pages that is more than 30 days before `posted`, for 11 more than 90 days: the car, or at least the advert,
  has been for sale through more than one 30-day listing. "Days for sale" on the page understates these.

### 4. Map pins

`data-accuracy` on `div#map` says what the pin is. On the 90 pages (TESTED):

| `data-accuracy` | Pages | What the pin is | Coordinates |
|---|---|---|---|
| 22 | 61 | the centre point of a ZIP code: all 61 match a point in GeoNames' public postal table to four decimals | 4 decimals |
| 99 | 22 | a spot the seller chose, coarse; never a ZIP point; several different ones in one town | 3 or 4 decimals |
| 5 or 7 | 7 | street level; 5 of the 7 show a street beside the map | 6 decimals |

The coordinates alone tell the three apart: five or more decimals, else on a postal point, else neither. That
rule agrees with `data-accuracy` on 90 of 90 pages, so the whole catalogue can be sorted without a new read
(exact): **198 of 293 pins (68%) are a ZIP's centre, 62 (21%) a seller's own spot, 33 (11%) street level.** Of the
112 listings within 60 miles of home, 75 sit on a ZIP centre.

- A ZIP-centre pin puts the car somewhere in that ZIP. The ZIPs behind these 198 pins have a median radius of
  5.1 miles, a ninth-decile radius of 7.9 and a largest of 10.7 (land area from the Census gazetteer, as a
  circle). Show "about N miles (ZIP area)" for these, and treat a distance filter as soft by that much.
- **The ZIP in the schema.org block is worse, not better.** For 81 of the 198 ZIP-centre pins it names a
  different ZIP from the one the pin is the centre of, and 92 of all 293 page ZIPs are not delivery areas at all
  (post-office-box ZIPs with no Census area). The page ZIP looks like a lookup from the pin against another
  table: it is one of the three nearest postal points to the pin for 268 of 284. Example: 33 listings whose pin
  is the centre of ZIP 38930 carry 38935, a box-only ZIP. Do not use it for distance. If a ZIP is wanted, take
  the one whose point the pin sits on.
- 6 of the 61 ZIP-centre pages show a street the seller typed while the pin stayed at the ZIP centre, so a
  street on the page does not mean a street-level pin.
- This also explains the shared pins. Of the 126 listings sharing a pin with two or more others, 106 sit on a
  ZIP centre, where sharing means only "same ZIP". The other 20 are three sellers (9, 7 and 4 cars).

### 5. Traders posing as owners

What marked them on the pages read (TESTED; 21 of the 90 pages are a trader's by my reading, 18 of the 76 spread
pages; nine sellers):

| Mark | Seen | How reliable |
|---|---|---|
| Several different cars on one pin that is **not** a ZIP centre | 3 sellers, 20 listings (9, 7 and 4 cars in 30 days) | strong: every page read in these groups was the same seller's |
| Different cars at one pin posted within 15 minutes | 19 listings at 5 pins; 3 of the 5 are sellers with 3 or more cars | strong for "same seller"; two cars is not yet a trade |
| Five or more different cars on one ZIP-centre pin with the same typed place name | 2 sellers: 17 cars (34 listings, each car on two sites) and 5 cars | held on these two; with three or four cars it was right once and wrong once (four unrelated owners in one town) |
| Business words in the text (`trade_seller`) | 6 pages: a dealer's web address (2), "we have 2", "trade-ins welcome", "ran through the shop" (2) | right 6 of 6 here; finds a third of the traders |
| One wording used for different cars | 6 of the 9 sellers | real, but needs the text: see "not settled" |
| Rebuilt titles in bulk | 41 of the catalogue's 69 not-clean titles are two sellers' | strong, and already handled by the title box |
| Stock numbers, "we finance", down payments | 0 of 90 pages | absent here; 22 of 40 postings in Washington's dealer category carry one of the `trade_seller` marks |
| Posting to a second site | 18 cars | not a mark: one of the two sellers doing it is a private owner with one truck |
| Phone digits spelled as words | 10 pages, 7 sellers | not a mark: 6 of the 7 are not traders by my reading |
| Street-level pin | 7 pages | not a mark here: 3 are one trader's, 4 private (29 of 40 in the Washington dealer category) |
| A VIN given | 11 of 90 pages; 2 of the 21 trader pages | not a mark |

**Rule.** Join listings into a seller group when they (a) share a pin that is not a ZIP centre, or (b) share any
pin and were posted within 15 minutes of each other, or (c) share a photo id, or (d) share a ZIP-centre pin and
the same typed place name and that pair has five or more different cars. A group with **three or more different
cars** (different year or odometer) is a trader: show its cars marked so, with the group's size, and do not
count them as private sales. On the catalogue: 5 groups, 60 listings, 42 cars (exact). On the pages read, this
rule plus `trade_seller` marks 18 of the 21 trader pages and no page I took for a private owner's. The three it
misses are a seller of three cars whose shared wording is the only link, and the second car of a two-car seller.
Tennessee lets a private person sell up to five vehicles titled in their own name in twelve months (REPORTED:
Tenn. Comp. R. & Regs. 0960-01-.20, via law.cornell.edu's copy, not read in full), so 7, 9 and 17 cars in thirty
days are trade by the state's own measure.

### 6. Listing ids

Keep the last part of the address as the id, and keep `post_id` beside it as a second key, so that if a key is
ever new while its post id is known the listing is recognised.

- TESTED: all 90 pages, read 39 to 48 minutes after the catalogue's last read, still answer at the same address;
  `link rel="canonical"` ends in the same key and the post id is unchanged on all 90.
- TESTED, one case: a listing posted 20 November had no `updated` time when the catalogue read it at 22:02 UTC
  and shows `updated` 22:39 UTC now. Same key, same post id, same `posted`. An edit keeps all three.
- TESTED: 49 of the 90 pages carry `updated`; 24 of those are more than a day after `posted`, and `posted` is
  still in step with the post id on every one, so an edit does not mint a new post or move `posted`. 13 are
  within a minute of `posted`, which is the posting form's own save, not a later edit.
- TESTED: a repost is a new post id, a new key and a new `posted` (four cars, eight listings).
- REPORTED (Craigslist's help pages, seen only as search summaries): a paid post lives 30 days, cannot be
  renewed to the top, and "repost" makes a new paid copy in the same area
  (craigslist.org/about/help/faqs/lifespan, /about/help/posting/modify/repost). Cars by owner are paid posts
  (REPORTED, from memory, not checked). The catalogue agrees: no listing is older than 30.4 days (TESTED).

## Evidence

### Warning words, as plain words (TESTED, 90 pages)

"With a fault" means the page does state something wrong with the car, whatever the word was doing there.

| Word or phrase | Pages | With a stated fault | Without | Note |
|---|---|---|---|---|
| need, needs, needed, needing | 21 | 14 | 7 | the seven: "I need", "need to sell", "no longer need", "needs nothing" |
| issue, problem, trouble | 20 | 4 | 16 | 14 are plain denials: "no issues", "no mechanical issues", "no problems at all" |
| runs and drives | 18 | 2 | 16 | says nothing either way |
| clean title, title in hand | 20 | 2 | 18 | on 5 pages the box says rebuilt or the bank holds the title |
| parts | 10 | 7 | 3 | "for parts", "parts truck", "part out": 3 pages, all true |
| tow | 7 | 1 | 6 | six are tow packages and hitches |
| damage | 6 | 2 | 4 | "cosmetic damage" twice, "no dents or damage" once |
| accident | 5 | 1 | 4 | every use is a denial |
| rebuilt | 5 | 0 | 5 | 3 rebuilt titles (box agrees), 2 rebuilt transmissions |
| rust | 4 | 3 | 1 | "no rust" twice |
| sitting, sat, when parked | 4 | 2 | 2 | true each time, but two of the four run and drive |
| finance, credit, payment, down | 4 | 0 | 4 | all four are "no financing" |
| as-is | 2 | 2 | 0 | both cars are caught by other words; boilerplate elsewhere (1 sound car of 1 in the Washington set) |
| project | 2 | 1 | 1 | "other projects", "bus conversion project" |
| leak | 2 | 1 | 1 | "No Leaks" |
| won't start, last ran, not running | 2 | 2 | 0 | plus one title in the catalogue |
| blown | 1 | 1 | 0 | |
| no title, bill of sale | 1 | 1 | 0 | a parts truck; the box already says parts only |
| lien, bank has | 3 | 0 | 3 | one truck on three sites, box says clean |
| salvage | 0 | - | - | not once in 90 texts |
| mechanic special | 0 | - | - | once in the 293 titles |
| we finance, down payment, stock number, doc fee | 0 | - | - | |
| cash only / scam / OBO / trade | 4 / 5 / 10 / 6 | | | no use: spread evenly over sound and faulty, private and trader |

Where the faults are (TESTED, 76 spread pages): under $3,000, 10 of 11 pages carry a fault or damage flag; from
$3,000 to $5,999, 6 of 20; from $6,000 to $9,999, 4 of 20; at $10,000 and over, 3 of 25. The median price of
pages kept out by `not_running` or `mechanical_fault` is $4,200, against $9,000 for pages with no flag. The
cheapest listings are the ones the ranking would put first, and nearly all of them say why they are cheap.

### Photos, reposts and ids (TESTED)

- The first photo id on the page equals the first one the catalogue kept on 89 of 89 pages with photos.
- Photo-id groups: 22 groups, 45 listings; matching on the first photo alone finds 21. Shared ids within a
  group: 8 to 12 of the first 12.
- `repost_of`: 30 of 90 pages; 22 of the 76 spread pages. Estimated age of the named post: 2 to 169 days for
  27 of them, and about 800 and 1,970 days for three (the day rate is measured over one month only, so the long
  ones are rough).
- Post ids are all multiples of 3 and strictly ordered with `posted` across the 293.

### Pins (TESTED)

- GeoNames `US.zip` (41,488 postal codes, coordinates to four decimals; licence CC BY 4.0, REPORTED) was the
  table. 117 catalogue pins equal the point of the page's own ZIP, 81 equal another ZIP's point, 95 neither.
- The Washington pages saved on 20 November show the same values: owners 29 at 22, 8 at 99, 3 at 5; dealers 14
  at 5, 13 at 7, 2 at 15, 10 at 22, 1 at 99.
- The map pin and the schema.org `geo` are the same numbers on 89 of 90 pages.

### Sellers (TESTED)

- The five groups: 17 cars in 34 listings, all but one rebuilt, each on two sites; 9 cars, all rebuilt, seven
  of them posted inside ten minutes; 7 cars over thirty days from one seller-placed pin, each ad signed the
  same way; 5 cars in 6 listings under one place name typed in capitals; 4 vehicles at one street address
  posted over two days.
- A 16-number min-hash of the description's three-word runs (letters only, so no prices, miles or phone
  numbers; no text kept) joined 14 of the 20 same-seller pairs it could score (two very short adverts get no sketch) with no wrong
  join among 3,808 other pairs, at three or more matching numbers. Most of the 14 are the same car posted twice, which photo ids
  already find. It missed sellers who write each advert afresh.

## Not settled

- **What `data-accuracy` 99 is.** It behaves like a pin the seller dragged, rounded to three or four decimals;
  one seller's two adverts for one car had two different such pins. Whether it is the seller's street or a
  spot nearby cannot be told from the page. Craigslist's map script would say; it was not read.
- **Whether `repost_of` names the first post of a line or the one before.** The one case that could tell (two
  reposts naming one older post) fits either.
- **Whether the address key survives a repost button used across sites, or anything other than an edit.** Only
  edits were seen. Nothing here contradicts the key being fixed for the life of a post.
- **The false-alarm rate on new text.** The patterns were fitted to these pages. The outside checks suggest
  about one wrong hit in ten; a count after a month of real reads would settle it. Keeping, beside each flag,
  the name of the pattern that fired (not the text) would make that review possible without storing anything
  a seller wrote.
- **Sellers linked only by their wording.** Three of the 21 trader pages are joined to their seller by nothing else. The
  min-hash above would link some; a hash of the phone number would link more but is a phone number in all but
  name (ten digits can be tried exhaustively), so it is not recommended.
- **The ZIP-centre place-name rule (d)** rests on two sellers. With fewer than five cars it wrongly joined four
  owners in one town; five was chosen to clear that one case.
- **Spanish-language adverts** (1 of 90) and photo-only adverts get no flags from English patterns.
- **Faults nobody states.** 33 of the 76 spread pages are clean on every test here. That is "nothing said", not
  "nothing wrong": the checks in `06-common-practice.md` A2 still apply at the car.
- **Things that are not cars.** 11 of the 90 pages are buses, box and dump trucks, a road tractor, a motorcycle
  and a pair of ATVs. Not asked here; they will not find "similar cars" and may deserve their own filter.

## Files

`research/_scratch/listing-quality/`: `pick.py` (the sample), `grab.py` and `ledger.tsv` (the 90 requests),
`parse.py` (a page taken apart), `final.py` (the flags and the hand labels), `existing.py` (the present rules
measured), `facts.py`, `ids.py`, `dups.py` (accuracy, ids, reposts), `gn.py`, `gn2.py`, `zips.py` (pins against
postal tables), `groups.py`, `sellers.py`, `sellers2.py` (seller groups), `sketch.py` (the min-hash), `dc.py`
(the Washington check), `pages/` (the saved pages: these hold descriptions and phone numbers and must stay out
of git).
