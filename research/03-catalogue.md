# 03 — How listings are catalogued

Research date 2026-11-20/21 (UTC). Region tested: Washington DC metro (the region aptHJunt already covers).
Evidence marks: **TESTED** (run here, output under `research/_scratch/catalogue/samples/`), **DOCUMENTED**
(read in a primary source, URL given), **REPORTED** (second-hand), **ESTIMATE** (my arithmetic on stated assumptions).

---

## Summary: the recommended design (one page)

**One record, made by one function.** Every reader emits a plain dict from `make_listing(source, source_id, ...)`,
the way every aptrack reader emits `make_unit(...)`. `None` for anything the source does not say, never `""` or `0`.
Whole US dollars, statute miles, UTC times to the minute (`"2026-11-21T03:03"`, history.py's form). The id is
`"<source>:<source_id>"`. Typed definition: `catalogue_schema.Listing` (section 1); the same fields as SQL:
`catalogue.sql`. The schema runs in both SQLite and DuckDB (TESTED).

**Vehicle identity in this order: VIN, then the source's own fields, then the title.** A VIN goes to NHTSA vPIC
`DecodeVINValuesBatch` (50 a request, free, no key) and is decoded once and cached for good. Without a VIN, a
standard-library title parser matches the title against vPIC's own make and model lists, plus a hand-kept
`aliases.toml` in govcon-compass's style: exact keys only, every entry taken from a real title. On 695 real
Craigslist titles it found make 96% and model 93% of the time, and agreed with the seller's own menu choice on 75 of
79 models (TESTED, though tuned on the same sample). How often a VIN is given depends on the seller: Craigslist
private sellers 28%, Craigslist dealers 92%, Bring a Trailer 93% for 1981 and later (TESTED, n = 40/40/15). eBay
requires one for 1981 and later (DOCUMENTED).

**One car, many listings.** Every listing joins a `vehicle` cluster. Links are made in this order: (1) the same VIN;
(2) the same source image id (a same-day Craigslist cross-post reuses them; TESTED); (3) a perceptual photo hash
match, meaning at least 2 photos within Hamming distance 6, with no conflicting VIN; (4) the same phone key plus the
same year, make and model plus miles within 2%; (5) a fuzzy match on fields, which is only ever a *candidate* for a
person to approve, as in govcon's exceptions file. A key of title plus price plus mileage plus place both failed to
link a real relist and falsely linked two different cars (TESTED, section 3).

**History is his history.py, with four changes.** Points are added only on change: `"h": [[time, price, miles]]`,
plus `"f"` first seen and `"x"` gone. New: `"l"` last seen, `"s"` seen-spans (run-length sightings), `"why"` (how
the listing ended) and `"v"`/`"r"` (its vehicle and the listing it relists). Gone is never inferred from one partial
read. Nothing is forgotten after 90 days: gone listings move to monthly archives, because comparables need a year of
data.

**Storage: JSON Lines files on the data branch, read with DuckDB in notebooks.** `data/state/<source>.jsonl` holds
one live listing per line. `data/archive/<yyyy-mm>.jsonl.gz` holds gone listings by month. Writes need only the
standard library and fit GitHub's 100 MiB file limit indefinitely. A single SQLite file would pass that limit in
roughly 8 months at the base volume. An analyst loads everything with one `read_json` view (TESTED, section 5). Base
volume for one metro is about 900 new listings a day, ~22,000 live at once, ~7 MB of gzip a month (ESTIMATE).

**Comparisons within make|model|generation|body.** Generation ranges come from a hand-kept `generations.toml`,
falling back to a 4-model-year window. Within a segment, price is fitted against age and miles. Mileage is not a
bucket. Radius widens 75 → 150 → 300 miles → national until there are 20 comparables. Below 8, nothing is flagged.
One day of Craigslist alone has only 11 make|model|4-year buckets with 5 or more listings (TESTED), so pooling
across sources over 90 days is required, not optional.

**Geography.** The source's own map pin first (Craigslist gave one on 80 of 80 postings; TESTED). Then
`aptrack.geo.place_addresses` for dealer street addresses that have a house number. Then Census ZCTA centroids for
ZIP-only sources, a median 0.6 miles from the pin (TESTED). County comes from `aptrack.geo.locate`. `from_home` is
a straight-line distance computed at build time, so the home point can move.

**Other goods.** The record, history, de-duplication by photo and phone, relist chains and storage carry over
unchanged to motorcycles, boats, trailers, tools, electronics and furniture. Identity and segments do not: VIN/vPIC,
odometer, title status and generations are vehicle-only, and one-off items (antiques, art) have no comparables
(section 8).

---

## 1. The common listing record

### 1.1 Definition

A full working version is in `_scratch/catalogue/catalogue_schema.py`: the `Listing` TypedDict and `make_listing()`.
It reuses `aptrack.units.num` unchanged. The fields:

| field | type | req. | unit / values | notes |
|---|---|---|---|---|
| `id` | str | yes | `"<source>:<source_id>"` | the same shape as units.py's `"<building>:<unit>"` |
| `source` | str | yes | key in `sources.json`: `craigslist`, `facebook`, `ebay`, `bringatrailer.com`, a dealer host | wishlist keys stores by host; this does too, for dealers |
| `source_id` | str | yes | Craigslist post id, eBay item id, BaT slug or id, FB item id, dealer stock no. or VIN | |
| `url` | str | yes | | |
| `seen` | str | yes | UTC `YYYY-MM-DDTHH:MM` | this read; becomes `f`/`l` in history |
| `posted`, `updated`, `ends` | str\|None | | UTC to the minute | the source's own dates. `ends` is for auctions |
| `title` | str | yes | | a listing with no title is dropped (returns None, as `make_unit` does for no rent) |
| `price` | int\|None | | whole USD | None for "call", and for asks under $500. Real dealer posts ask "$0 – we finance everyone" (TESTED, 2 seen) |
| `price_kind` | enum | yes | `ask` `bid` `sold` `reserve_not_met` `starting` | an auction's current bid is not an ask; they are compared separately |
| `currency` | str | yes | ISO 4217 | `USD` everywhere planned |
| `seller_type` | enum\|None | | `private` `dealer` | Craigslist says so by section (cto/ctd). For FB and BaT, None unless marked |
| `channel` | enum | yes | `classified` `marketplace` `dealer_site` `aggregator` `auction` | The brief's "private, dealer, auction" splits into two fields: *who* sells and *how*. A BaT car can be a private party's or a dealer's |
| `seller_id` | str\|None | | the source's handle | eBay user, FB profile id, BaT user, dealer host. Craigslist owners have none |
| `seller_name` | str\|None | | | dealers only. Kept null for private sellers |
| `phone_key` | str\|None | | `sha256(salt + 10 digits)[:16]` | a matching key, never the number. The salt lives in a repository secret |
| `vin` | str\|None | | 17 chars, upper case, as given | non-17-character chassis numbers (pre-1981, imports) go in `extra.chassis` |
| `vin_ok` | bool\|None | | check digit per 49 CFR 565 | a False VIN still decodes in vPIC (TESTED, ErrorCode 1) |
| `year` `make` `model` `trim` `body` `drive` `engine` `fuel` `transmission` | int/str\|None | | make lower case vPIC name; model vPIC name; `drive` ∈ fwd rwd awd 4wd 2wd; `body` ∈ sedan coupe convertible wagon hatchback suv pickup minivan van | section 2 |
| `identity_how` | enum\|None | | `vin` `source` `title` `manual` | precedence, like JobScope's `extraction_method` |
| `vehicle_key` | str\|None | | `year\|make\|model\|trim\|body\|drive\|engine` | section 2.4 |
| `segment` | str\|None | | `make\|model\|gen\|body` | section 6 |
| `miles` | int\|None | | odometer, statute miles | `miles_how` ∈ `field` `title` `text` |
| `title_status` | enum\|None | | `clean` `rebuilt` `salvage` `lien` `missing` `parts_only` `lemon` | Craigslist's own list plus `lemon` |
| `condition`, `color` | str\|None | | the source's own word | |
| `city` `state` `zip` | str\|None | | state 2 letters, zip 5 digits | a ZIP that is not 5 digits becomes None |
| `lat` `lon` | float\|None | | WGS84, 5 decimals | |
| `geo_how` | enum\|None | | `pin` `street` `zip` `city` | section 7 |
| `county` | str\|None | | 5-digit FIPS | `aptrack.geo.locate` |
| `from_home` | float\|None | | miles, straight line | filled at build time, not by the reader |
| `photos` | list[str] | yes (may be `[]`) | first 12 addresses | |
| `photo_count` | int | yes | | the source's total |
| `photo_ids` | list[str] | yes | the source's own image ids | Craigslist: `00505_kUkcSj4gJ5r_0dm0t2` |
| `photo_hash` | list[str] | yes | 16-hex 64-bit dHash of up to 6 photos | `[]` when not hashed |
| `extra` | dict | no | | anything source-specific: stock no., `where` text, BaT reserve, bid count |

**Missing values.** `None`, which is JSON `null`, means "the source does not say". A list is `[]`. Booleans are
three-valued (`True`/`False`/`None`), as `restricted` is in units.py. Zero is only ever a real zero.

**Raw pages.** These are not kept in the record. Following JobScope's `raw_posting`, a reader may write the
source's own JSON (Craigslist's `ld_posting_data`, BaT's item) to `data/raw/<source>/<yyyy-mm-dd>.jsonl.gz`, so a
fixed parser can be re-run. At ~1–2 KB a description, keep 30 days.

### 1.2 What each source gives

TESTED unless marked.

| field | Craigslist (no-JS search page + posting page) | Bring a Trailer (auctions page JSON + listing page) | eBay Motors | Facebook Marketplace | dealer sites |
|---|---|---|---|---|---|
| id | `post id` (e.g. 8004100263) | numeric `id` + slug | item id (DOCUMENTED, Browse API) | item id (REPORTED) | stock no. / VIN |
| price | `offers.price` in LD JSON | `current_bid`; `sold_text` at the end | ask or bid | ask | ask |
| seller type | by section: cto owner / ctd dealer | not in the list data (it is in the page text; my regex missed it) | seller account type (REPORTED) | profile vs. dealer page (REPORTED) | dealer |
| VIN | `VIN:` attribute, 28% owners / 92% dealers | `Chassis:`, 93% for 1981+ | required for 1981+ (DOCUMENTED) | optional, rarely shown (REPORTED) | usually (REPORTED) |
| odometer | attribute, 80/80 | in the title ("35k-Mile 2017 …") or the essentials text | item specific | field (REPORTED) | yes |
| title status | attribute, 80/80 (78 clean, 2 rebuilt) | essentials text | item specific | field (REPORTED) | rarely |
| location | lat/lon pin 80/80; postal code 73/80; street 28/80 (mostly dealers) | `lat`,`lon`, country on every item | ZIP/city | city, approximate (REPORTED) | the lot address |
| photos | 12 median for owners, 24 for dealers | thumbnail + gallery | yes | yes | yes |

Craigslist cars posts also carry `condition`, `cylinders`, `drive`, `fuel`, `transmission`, `type` and a
year + make/model chosen from Craigslist's own menu (`samples/cl_postings_*.json`).

---

## 2. Vehicle identity

### 2.1 From a VIN: NHTSA vPIC

**TESTED.** `GET https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/1HGCM82633A004352?format=json` returned
in 0.26 s:

```
ModelYear 2003  Make HONDA  Model Accord  Trim EX-V6  BodyClass Coupe  Doors 2
DisplacementL 2.998832712  EngineCylinders 6  EngineConfiguration V-Shaped  EngineModel J30A4  EngineHP 240
TransmissionStyle Automatic  TransmissionSpeeds 5  FuelTypePrimary Gasoline  PlantCity MARYSVILLE
ErrorCode 0  "0 - VIN decoded clean. Check Digit (9th position) is correct"
```

**Batch decode, TESTED.** `POST .../DecodeVINValuesBatch/` with form fields `DATA=vin;vin;vin,year` and
`format=json`. All 46 real VINs from the Craigslist sample decoded with ErrorCode 0. The decoded year, make and
model agreed with the seller's Craigslist fields on 46 of 46 (`samples/vin_check_report.txt`). That near-perfect
agreement suggests Craigslist fills its make/model menu from the VIN; I infer this and have not checked it.
- The limit is 50 VINs per batch, and traffic is "controlled by an automated traffic rate control mechanism" with
  no number given. A standalone vPIC database can be downloaded (DOCUMENTED, https://vpic.nhtsa.dot.gov/api/).
- **Wrong check digit:** VINs with a deliberately wrong 9th character still decode from their pattern (ErrorCode 1,
  TESTED). So keep `vin_ok` as a flag, do not reject on it. A typo elsewhere in a VIN gives a wrong vehicle, and a
  VIN whose decoded year, make or model contradicts the listing is the signal for that.
- **Trim is messy:** vPIC often returns a set or a fleet label rather than one trim:
  `EXL/EXL-NAVI/EXL-RES`, `SEL / Value Edition / Limited`, `Sport ES/SE (ASX ES in Puerto Rico)`, `Others`,
  `LEV 1 - All Models`, `Police` (TESTED). Trim was given for 32 of 46 VINs and DriveType for 31 of 46; the 2008
  Audi S8 came back with no drive at all. Rule: vPIC's trim is a *candidate set*. Where the listing names one trim
  inside that set, take it; otherwise keep the set.
- vPIC's model names are the vocabulary for everything else. `GetModelsForMakeYear/make/<m>/vehicletype/<t>` for
  50 makes gave the model lists in `samples/vpic_models.json` (TESTED). Scion returns nothing under a vehicle type,
  so it is seeded by hand.

**Decode once.** `data/vin_cache.json` maps a VIN to the kept vPIC fields plus the decode date (the `vin_decode`
table in SQL). A daily run sends only VINs it has never seen, 50 at a time.

### 2.2 From a free-text title

Prototype: `_scratch/catalogue/identity.py` (standard library: `re`, `difflib`). It works in this order:

1. **Clean.** Upper case; `/ | , ( ) ! * + ~` become spaces; `&` becomes `AND` (vPIC spells "Town and Country");
   `2019-Lexus` becomes `2019 Lexus`.
2. **Year.** The first `19[4-9]x|20[0-3]x`; or `'05`; or a bare two-digit first token (`04 Ford F250`).
3. **Make**, within 4 tokens of the year. Checked in turn: a two-word make (`LAND ROVER`, `ALFA ROMEO`, `RANGE ROVER`
   → land rover); an exact vPIC make; a hand alias (`CHEVY`, `VW`, `MERCEDES`, `BENZ`, `INFINITY`, `HUNDAI`, …);
   fuzzy (`difflib`, cutoff 0.85, only for words of 5 letters or more).
4. **No make?** A model name that belongs to exactly one make implies the make (`2012 Camry` → toyota; 23 titles).
5. **Model.** The longest vPIC model of that make spelled by the 1–3 tokens after the make, ignoring hyphens and
   spaces (`F150` = `F 150` = `F-150`). Then one fuzzy slip in a long word. Then the same exact match anywhere in
   the first tokens (`2014 Outlander Mitsubishi Sport`). Mercedes class rule: `SL500`, `GLK 350`, `C300` →
   `SL-Class`, `GLK-Class`, `C-Class`, which is how vPIC names them.
6. **The rest.** Drive tokens (`4X4 AWD XDRIVE 4MATIC QUATTRO …`), body (`CREW CAB` → pickup), engine (`5.3L`,
   `V8`, `HEMI`, `ECOBOOST`, `DIESEL`), miles in the title (`134K MILES`), and one trim word (`SPORT`, `EX-L`).

**Results, TESTED on real titles** (`samples/identity_eval.txt`):
- On all 695 titles from one Craigslist DC search, owner + dealer: year found 93%, make 96%, model 93%. How each
  matched: exact/exact 547, model-implies-make 23, alias 17, fuzzy model 15, Mercedes class rule 20.
- Against the seller's own Craigslist year and make/model on 80 sampled postings: year 76/80, make 79/80, model
  75/79 (95%, 95% CI 88–98%). **Caveat:** the rules were tuned on this sample, so held-out accuracy will be lower.
  The first version, before tuning, scored 73/79 on model (`identity_v1.py`).
- What still fails, and what to do about it:
  - Titles with no vehicle in them ("Clean title", "Reliable low miles", "FOR SALE"). Fall back to the source's own
    fields or the VIN.
  - Not a car listing at all ("European Classic Cars Wanted", "Rear Trunk & Bumper for 2013-2019 Ford Escape",
    "$500 Down & $100 Weekly – Lease-to-Own"). A `not_a_vehicle` rule list is needed.
  - BMW numeric models (`BMW 328`, `BMW325xi`; vPIC says `328i`). Add a BMW series rule like the Mercedes one.
  - Misspellings like `Rap4` and `Verona` (Verano), commercial makes vPIC does not list under passenger types
    (International, Workhorse, Freightliner), and model-variant names (`NV1500` vs `NV`). These are what the alias
    file is for.

**Alias file, govcon-compass style.** `aliases.toml` with sections `[make]`, `[model."<make>"]`,
`[not_a_vehicle]` and `[twins]` (badge-engineered pairs, section 6). Exact keys only; every entry added because a real
title needed it. Each build writes `review.csv` listing the unparsed titles of the week, to promote by hand. Never
promote automatically.

**Where the identity comes from, in order:** a decoded VIN, then the source's own fields (Craigslist's menu, eBay
item specifics, FB vehicle fields), then the title. `identity_how` records which one won. If the title contradicts
the VIN (a different make, or a year off by more than 1), keep the VIN's answer and flag the listing. That
contradiction is either a typo in the VIN or a bait listing.

### 2.3 How often a VIN is present, by source

| source | VIN present | n | evidence |
|---|---|---|---|
| Craigslist DC, owner (cto) | 11/40 = **28%** (95% CI 16–43%); none only in the text | 40 random postings, 2026-11-20 | TESTED |
| Craigslist DC, dealer (ctd) | 35 in the field + 2 only in the text = **92%** (80–97%) | 40 | TESTED |
| Bring a Trailer, live auctions | chassis shown 25/25; 17-char VIN **14/15** for model year 1981+ (70–99%), 14/25 overall | 25 of 1,226 live | TESTED |
| eBay Motors US, Cars & Trucks | **required** for model year 1981+ (`Item.VIN`) | — | DOCUMENTED: https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/ebay-motors-vin.html |
| Facebook Marketplace | optional field, usually blank for private sellers | — | REPORTED (carwhere.com, keysavvy.com guides) |
| Dealer sites, aggregators | not measured. cars.com answered with a Cloudflare challenge (HTTP 403) | — | Dealers on Craigslist give one 92% of the time, so dealer feeds very likely do (inference) |

Practical meaning: dealer and auction listings get identity from the VIN. Private-party listings (Craigslist owners,
FB), which are where underpriced cars are likeliest, mostly do not. The title parser and photo matching carry that
part.

### 2.4 The canonical key

`vehicle_key = year|make|model|trim|body|drive|engine`, lower case, empty where unknown, for example
`2013|ford|expedition|limited|suv|4wd|5.4l v8`. Only the first three parts are used to *match* two listings. The
rest are tie-breakers and segment inputs, because sources disagree on trim and drive far more than on year, make
and model.

---

## 3. Listing identity and de-duplication

### 3.1 What actually happens (TESTED on the 695-row DC sample, `samples/dupes_phash_report.txt`)

| case | what was seen | VIN | image ids | dHash (nearest of 6 photos) | title + price + miles + place |
|---|---|---|---|---|---|
| **Cross-post, same day**: 2014 Accord, owner, posted under "Va,md,dc" and "district of columbia" | same price, same 185,000 mi, pins 9 miles apart | none | **8 of 8 identical** | 0,0,0,0,0,0 | matches on title+price+miles; place differs |
| **Relist at a new price**: 2007 Trailblazer, owner, $2,200 then $1,950 | odometer 200,000 then 208,000; pins 18 miles apart | none | 0 shared (photos re-uploaded) | 4,5,6,7,10 | **misses**: price, miles and place all differ |
| **Two cars, one title**: "Clean title", Sterling dealer lot | $10,400 vs $10,200 | different | 0 | 22+ | **false match** risk on title + place |
| **Fleet sale**: 2016 Ford Explorer Police Interceptor ×2, same lot | $8,470 vs $5,950 | different | 0 | **10,10,12** | same title and place |
| **Dealer double post**: 2019 Rogue, "$0 – we finance everyone" | | different | — | — | the same bait title on two cars |

I looked at the Trailblazer photos side by side (`samples/trailblazer_pair.jpg`): it is the same truck, with the
same rear shot in the same parking lot. A dHash of a Craigslist 300×300 thumbnail against its 600×450 full image
differed by 0–1 bits (TESTED).

### 3.2 The order of precedence

The cluster is a union-find over listings. Rules run from the strongest down, and **a VIN conflict vetoes every
weaker rule**.

| # | key | links when | known errors | handling |
|---|---|---|---|---|
| 0 | `(source, source_id)` | always | Craigslist *renew* keeps the post id; a *repost* gets a new one | a returning id clears `x` and opens a new seen-span |
| 1 | **VIN** | same 17 characters | placeholder VINs (17 zeros, `12345678901234567`), and a dealer pasting one VIN into two ads | a `vin_blocklist` in `aliases.toml`. A VIN on 2+ *simultaneously live* listings from *different* sellers goes to review, not merged |
| 2 | **source image id** | the same Craigslist image id in two listings | dealer banner or logo images appear in every ad | ignore any image id seen in more than 2 listings |
| 3 | **photo dHash** | ≥2 of the first 6 photos within Hamming distance **≤6**, and year/make/model agree, and no VIN conflict | same-lot fleet cars measured at 10–12; manufacturer stock photos on new cars; watermarks | the threshold sits between 7 (same car, worst seen) and 10 (different cars, best seen). This is from **one** sample; widen the test before trusting it |
| 4 | **phone key** + year/make/model | same phone hash and identity, miles within 2% or 2,000 | a dealer has one phone for every car; fleets | for `seller_type = dealer`, also require a photo or miles match |
| 5 | **fields** (title-independent): same year/make/model, miles within 3%, distance ≤30 mi, price within 20%, first seen ≤60 days apart | — | common cars (Camry, F-150) collide often; fleet units | **candidate only**: written to `review.csv` with a score, merged when promoted to `merges.toml` by hand (govcon's exceptions → alias_map rule) |
| — | title + price + mileage + location | **not used as a key** | missed the real relist above, and falsely matched two cars | used only to *rank* rule 5 candidates |

Rules 0–2 need only the standard library. Rule 3 needs JPEG decoding: either a `pip install pillow` step in the
workflow (the way wishlist's `algolia-keys.yml` installs a browser only when needed), or hashing in the browser
extension with a canvas, which suits Facebook, where the extension is the reader anyway. This is the owner's
choice (section 10).

**Vehicle id.** `vin:<VIN>` when any listing in the cluster has a VIN; otherwise `v:<id of its first listing>`.
When a VIN turns up later, the cluster is renamed and the old id is kept as an alias.

**Relist chain.** The listings of one vehicle ordered by `first_seen`. A listing whose `first_seen` comes after
the previous one's `gone` is a **relist** (`r` = the previous listing's id). One that overlaps a live listing is a
**cross-post**. What the analysis wants from a chain: the number of relists, days on market across the chain, and
price from first ask to last ask. "Listed 3 times, down 25% in 6 weeks" is a motivated seller.

---

## 4. History

### 4.1 What a listing line holds

Per listing, in `data/state/<source>.jsonl`, the record from section 1 is followed by these short keys:

```
"f": "2026-11-12T14:05"                  first seen                          history.py "f"
"l": "2026-11-21T03:40"                  last seen                           NEW
"x": "2026-11-21T09:00" | absent         noticed gone                        history.py "x"
"why": "sold"|"removed"|"expired"|"unseen"|"ended_unsold"                    NEW
"h": [["2026-11-12T14:05", 2200, 200000], ["2026-11-19T10:31", 1950, 208000]]
                                         a point only on change: [time, price, miles]    history.py "h", fields changed
"s": [["2026-11-12T14:05","2026-11-16T08:00"], ["2026-11-18T20:00","2026-11-21T03:40"]]
                                         seen-spans: sightings, run-length   NEW (JobScope's sighting table, folded)
"v": "v:craigslist:8002538988"           vehicle cluster                     NEW
"r": "craigslist:8002538988" | absent    relist of                           NEW
```

Points are added with aptrack's `history.put()`, unchanged: it appends `[time, values…]` only if the values
differed, and replaces a second point from the same day. A seen-span is extended while reads keep finding the
listing. A new span starts when it reappears after a gap longer than twice the source's read interval.

### 4.2 Mapping onto his history.py, and what must change

| history.py (wishlist) | carry over? | change for CraigsCars |
|---|---|---|
| `data/state/<store>.json` = `{head…, "products": {id: {...}}}`, one product per line | **change** | DuckDB reads that shape as a single struct with one column per product id (TESTED on a copy of `state/www.yoox.com.json`), which is useless for analysis. Make it pure JSON Lines (`<source>.jsonl`, one listing per line) plus `<source>.meta.json` for the head (`since`, `fetched`, `reads`, `fails`, `error`, `log`) |
| `record()`: a point on a price move ≥ `NOISE` 3%, discount ±3, stock flip | **change** | there is no exchange-rate drift, so every price change counts. Use aptrack `put()`. The point is `[t, price, miles]`: miles matter because relists change them; stock and percent-off do not exist |
| `track()` marks `x` for every product missing from a *clean, whole* read | **change** | marketplace reads are never whole. A Craigslist search page shows ~350 results; FB shows what was scrolled. Mark gone only on (a) the posting page answering deleted or expired (untested here), (b) the source's own end (BaT `sold_text` / `timestamp_end`, present in the item JSON; TESTED), (c) the source's life limit passing (Craigslist paid car posts run 30 days, DOCUMENTED: https://www.craigslist.org/about/help/faqs/lifespan), or (d) `unseen`: absent from K reads of a search that should have contained it (its posted time is newer than the oldest result returned) |
| `KEEP_DAYS` 90, `KEEP_POINTS` 30 | **change** | never forget. 30 days after `x`, a listing moves to `data/archive/<yyyy-mm of x>.jsonl.gz`, which is immutable once its month closes. Comparables and relists span months |
| `"b"` brand, `"k"` kind, `"p"` published | replaced | by the full record (`make`, `segment`, `posted`) |
| `"z"` sizes in stock | dropped | |
| `log` (a line a day per store), `events` | keep | per source: `[day, live, new, gone, median ask]` |
| `survival(spans)` Kaplan–Meier | **reuse unchanged** | days on market per segment. Spans are `(days from f to x or now, ended?)`. Live listings count for as long as they have been watched, as for wishlist deals |
| `storewide()` repricing detection | adapt | a dealer site cutting every price by the same % on the same day is a repricing, not a deal. The index of "percent off" goes; the rest stands |
| `deals()`, `was_check()`, sale events | not used | cars have no "was" price; the deal signal is the segment comparison (section 6) |
| aptrack `record()` moving a returning unit's old life into `"past"` | **reuse the idea** | a returning *source_id* opens a new span. A *new* source_id for a known vehicle is a new listing with `r`, so the chain is explicit, not buried in `past` |
| aptrack `safe_to_save()` (80% floor) | keep | per source: refuse to save if live listings fell under 80% of the previous run, unless that source's read failed |

**Sold versus removed.** This is only known when the source says it: BaT `sold_text`, eBay ended with a sale, FB's
"Sold" label (REPORTED). Everything else is `removed` or `expired`. "Probably sold" is a *derived* column in
analysis, not stored truth: removed before its life limit, at or near its last ask, and not relisted within 30
days. As in JobScope, keep the guess apart from the fact.

---

## 5. Storage

### 5.1 Expected volume: one metro (DC), all planned sources

| source | new listings a day | basis | mark |
|---|---|---|---|
| Craigslist cars + trucks | **104** (29 owner, 75 dealer) | `?postedToday=1` counts, Friday 2026-11-20, one day only | TESTED |
| Facebook Marketplace | 150–400 *captured* | bounded by what the extension sees while browsing | ESTIMATE |
| eBay Motors, ≤100 mi | 20–60 | assumption | ESTIMATE |
| dealer sites, 50–100 lots tracked | 150–400 | ~100 units a lot, ~45-day turn ≈ 2.2 new a lot a day | ESTIMATE |
| auctions, national (BaT, Cars & Bids) | 150–250 | BaT had 1,226 live; at 7-day auctions that is ≈175 new a day | count TESTED, turn REPORTED |
| **total** | **base ≈ 900, high ≈ 2,000** | | ESTIMATE |

**Record size, measured on the three real worked examples:** 943–1,351 bytes compact JSON with up to 6 photo
hashes and 1–2 photo URLs (`samples/examples_report.txt`). With 12 photo URLs, add ~700 bytes. With history,
allow about **1.5 KB per listing** as JSON. A price point adds ~30 bytes, a seen-span ~40.

**Working:**
- New per month (base): 900 × 30 = 27,000 listings × 1.5 KB = **~40 MB raw JSON**. Gzipped, the benchmark ratio is
  6.3 : 1, so **~7 MB/month**. As Parquet, ~200 B per listing gives ~5 MB/month.
- Live at once: 900/day × ~25 days average life ≈ **22,000 listings**, about 33 MB raw across the state files.
  High case: 60,000 listings, ~90 MB, split by source and by dealer host, so no single file nears 50 MiB.
- Per year (base): ~330,000 listings; ~500 MB raw JSON, **~80 MB as gzip archives**, ~65 MB as Parquet.
- Per-read sightings stored one row each (JobScope's `sighting`) would cost 22,000 rows × 4 reads × 30 days =
  2.6 M rows a month. Seen-spans make it ~1.2 rows per listing.

### 5.2 The three layouts compared

**TESTED** with `storage_bench.py`: a synthetic year of 511,000 listings and 1,174,844 price points, built with the
real field set. Random hashes stand in for VINs, URLs and photo hashes, so compression here is *worse* than on real
text.

| | flat JSON Lines (per source, history inline) | SQLite (stdlib) | Parquet (zstd) + DuckDB |
|---|---|---|---|
| size, one year | 369 MB raw / **58 MB gzipped** | **242 MB**, one file | **46 MB** in 61 files (source × month) |
| bytes per listing | 721 raw / 114 gz | 473 | 90 |
| write path | stdlib; his existing pattern | stdlib; his ticketdesk pattern (migrations, WAL) | needs `duckdb` or `pyarrow` in the workflow |
| analyst query (segment medians), cold | DuckDB `read_json`: **0.30 s** | sqlite3 + Python median: 0.50 s | DuckDB: **0.11 s** |
| GitHub data branch | many files, each well under 100 MiB; reads as text | one binary file passes the **100 MiB hard block** (DOCUMENTED: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) in ~8 months at base volume | small files, but binary, and not writable with the stdlib |
| static site | per-segment JSON slices are a direct export | needs an export step | needs an export step; browsers can't read it without a WASM engine |
| joins for de-dup (VIN, photo, phone) | load the live set into dicts: 22k listings is trivial | indexes | SQL |

DuckDB reading gzipped JSON Lines directly: 255,500 rows in 0.68 s (TESTED). DuckDB's `sqlite` extension also
installed and loaded the SQLite file. The query then needed typed columns (my benchmark table was untyped), so
"DuckDB can read the SQLite file" is TESTED and "the query ran" is not.

### 5.3 Recommendation

**JSON Lines as the record, DuckDB as the analyst's engine, Parquet only as a local cache.**

```
data/                                  (data branch, one commit replaced each run, as in wishlist)
  state/<source>.jsonl                 live + gone < 30 days, one listing per line, sorted by id
  state/<source>.meta.json             since, fetched, reads, fails, error, log
  archive/<yyyy-mm>.jsonl.gz           listings gone that month; immutable once the month ends
  vehicles.jsonl                       vehicle clusters
  merges.toml / review.csv             hand-approved merges / candidates (in main, not the data branch)
  vin_cache.json, geo_cache.json       decode once, place once
site/data/                             what the page loads (section 5.4)
aliases.toml, generations.toml, sources.json   hand-kept, in main
```

Why: it is his house style (stdlib, JSON, no server, Actions), it is diffable, and every file stays far below
GitHub's limits for years. It loses only query speed (0.30 s versus 0.11 s on a year), and a notebook can buy that
back by exporting Parquet locally. If the runner moves to a home machine and the data leaves git, SQLite (with
ticketdesk's `MIGRATIONS` list and `catalogue.sql` as v1) becomes the better record. `catalogue.sql` already runs
in both engines.

**What an analyst runs** (TESTED by `loader_test.py` against the layout above):

```python
import duckdb                                   # pip install duckdb   (2.0.1 tested)
con = duckdb.connect()
con.sql("""CREATE VIEW listings AS SELECT * FROM read_json(
             ['data/state/*.jsonl', 'data/archive/*.jsonl.gz'],
             format='newline_delimited', union_by_name=true, filename=true)""")
con.sql("""CREATE VIEW points AS SELECT id, p[1]::VARCHAR AS at, p[2]::INTEGER AS price, p[3]::INTEGER AS miles
           FROM (SELECT id, unnest(h) AS p FROM listings)""")
con.sql("SELECT segment, count(*), median(price) FROM listings WHERE x IS NULL GROUP BY 1 ORDER BY 2 DESC").show()
# optional local cache:  con.sql("COPY listings TO 'cache/listings.parquet' (FORMAT parquet)")
```

Pin column types with `columns={...}` generated from `catalogue.sql`: a field that is null in every row otherwise
comes back typed `"NULL"` (seen in the test with `updated`). `.df()` for pandas needs pandas installed (not tested).

### 5.4 Publishing the static site

This follows his two precedents: aptHJunt's `units-<county>.json` per county and wishlist's `docs/brands/<n>.json`
per brand bucket.
- `site/data/index.json`: the segments with counts, medians and fit parameters; the sources with read status.
- `site/data/seg/<n>.json`: the live listings of a group of segments, with each listing's points, so the page can
  draw a price line and place it against its comparables. `n` comes from wishlist's `brand_file()` hash over the
  segment key; 256 files is plenty.
- `site/data/deals.json`: only the flagged listings, which keeps the first page load small.
- For a public repository: round private sellers' `lat`/`lon` to 2 decimals (~1 km) and leave out `seller_name` and
  `phone_key` in `site/data`. The state files keep the precise values.

---

## 6. Segments for comparison

**Key:** `segment = make|model|generation|body`, for example `ford|f-150|2015-2020|pickup` or
`honda|accord|2013-2017|sedan`.

- **Generation.** `generations.toml`: `[ford."f-150"] = [[2004,2008],[2009,2014],[2015,2020],[2021,2026]]`,
  hand-kept for the models that actually show up (the top ~150 cover most listings). A model with no entry gets
  fixed 4-model-year windows (`(year // 4) * 4`). Generations matter because a refresh moves price more than a
  model year does.
- **Body (and cab, for pickups).** Pickups split by cab (regular / extended / crew) and by `drive`, because 4wd vs
  2wd is a large price step in pickups and SUVs. Cars split by body only.
- **Twins.** `[twins]` in `aliases.toml` pools badge-engineered pairs when one side is sparse: Silverado/Sierra,
  86/BRZ/FR-S, Sienna/none, Tahoe/Yukon. They are pooled for the fit, never relabelled.
- **Mileage is a covariate, not a bucket.** Within a segment, fit `log(price) ~ age + miles (+ trim class, +
  title_status ≠ clean)` over the comparison window. A listing's **deal score** is its residual as a percentile
  among its comparables. This mirrors JobScope's decision (docs/decisions.md, 2026-08-09) to drop cell baselines for
  a pooled fit, because the cells the user cares about are the sparsest. The fit can be done with the standard
  library (`statistics.linear_regression` on log price, or a median-of-slopes fit for robustness). For display only,
  bands are <60k, 60–120k, 120–180k and 180k+.
- **Window and price kind.** Use 90 days of asks, live and gone. Compare asks with asks. Auction bids and sold
  prices form their own series: a BaT result is a transaction, a Craigslist ask is not. A gone listing's *last* ask
  is the closest thing to a transaction price the classifieds offer, so weight it above a fresh ask.
- **Region: a radius ladder.** 75 mi from home, then 150, then 300, then national, stopping at the first that gives
  **n ≥ 20**. Auctions are national by nature.
- **Sparse segments: a fall-back ladder.** Same as JobScope's low-n path:
  1. n ≥ 20: the fitted residual, as above.
  2. 8 ≤ n < 20: show the comparables table and the median. Give a flag only when the price is below every
     comparable *and* ≥15% below the median.
  3. Borrow: pool an adjacent generation or a twin, adding a year term.
  4. n < 8: no flag; "not enough comparables". Shrink percentiles toward 50% when n is small, as wishlist does with
     `SHRINK`.
- **Why pooling is required, TESTED.** One day of Craigslist DC (643 parsed listings) has 243 distinct make|models.
  Only 11 have ≥10 listings, and only 11 make|model|4-year buckets have ≥5 (`samples/segment_sparsity.txt`). The
  top models were F-150 24, Accord 23, Odyssey 16, Explorer 16, Camry/Prius/Highlander 13. At the base estimate, 90
  days of all sources is ~80,000 listings, about 120× this sample. The top ~150 models then clear n = 20 per
  generation inside 150 miles (ESTIMATE, scaling the sample's distribution).
- **Title status** goes into the fit as a term, not into the segment. Rebuilt and salvage cars are few (2 of 80 in
  the sample) and sell for less; a segment of their own would always be sparse.

---

## 7. Geography

**TESTED** with `geo_test.py`, which imports his `aptrack/geo.py` from its own folder, unchanged, with `-B` so no
bytecode is written there.

1. **The source's pin (`geo_how = "pin"`).** Craigslist gave `data-latitude/longitude` on 80 of 80 postings.
   Accuracy codes seen: owners mostly `22`, dealers `5`/`7`. Lower looks more exact, but Craigslist does not
   document this, so the reading is my inference. BaT gives `lat`/`lon` on every item. Where a Census match existed
   it agreed with the pin within 0.05 mi in 5 of 6 cases (one at 1.7 mi).
2. **A street address with a house number (`street`):** `geo.place_addresses(rows, post)`. Only 6 of 28 matched
   (0 exact). The addresses are seller-typed: "Mountain rd", "main street", and a Chantilly lot filed as
   "Washington DC 20041". So use it only when the pin is missing or coarse. Two things in `place_addresses` are
   specific to aptHJunt's region: it **blanks every ZIP not starting with 2** (line 62), and `geo.batch()` assumes
   one city. For listings from farther away (auctions, eBay), CraigsCars needs its own copy without the ZIP filter.
   Copy it; do not edit aptHJunt's.
3. **ZIP only (`zip`):** Census ZCTA gazetteer centroids (`2024_Gaz_zcta_national.zip`, 1 MB, 33,791 ZCTAs;
   TESTED). Median 0.6 mi from the Craigslist pin, 90th percentile 1.6 mi, worst 4.1 mi. **16 of the ZIPs sellers
   typed are not ZCTAs** (PO-box and business ZIPs such as 20041, 20177 and 22195); those fall back to the city.
4. **City only (`city`):** the Census Places gazetteer centroid (not tested here).
5. **County:** `geo.locate(get, lat=, lon=)` returned 5-digit FIPS (`24009`, `24031`) at ~1.3 s a call (TESTED).
   Cache it by rounded pin.
6. **Distance:** haversine, straight line, from a home point in `sources.json` settings, computed at build so the
   home can change. In the sample, median 23 mi; 54 of 80 within 25 mi; one dealer post 903 mi away. Straight line
   is enough for the radius ladder; driving time is not needed.

---

## 8. Other resellable goods

| part of the design | holds for other goods? |
|---|---|
| the record (source, ids, price, price_kind, seller type, channel, location, photos, extra) | **yes**, unchanged except the vehicle fields |
| history: change-only points, f/l/x, seen-spans, why, relist chains | **yes** |
| de-dup by source id, image id, photo hash, phone | **yes**. Photo hashing matters *more* where there is no serial number |
| storage, site slices, geography | **yes** |
| VIN / vPIC identity, odometer, title status | **no**. Motorcycles, RVs and trailers have VINs (eBay lists them as VIN categories, DOCUMENTED) and vPIC decodes motorcycles; boats have 12-character HINs with no free decoder that I know of; tools and electronics have model numbers in the title, which suit the alias-map parser |
| segments by make/model/generation + a fit on age and miles | **partly**. Goods with a catalogue identity (a DeWalt DCD791, an iPhone 13 128 GB) segment by model and condition. One-off goods (antiques, art, custom furniture) have **no comparables**, so the deal score cannot work there |

---

## 9. Worked examples

These were built by `catalogue_schema.py` from the real sampled listings, with VINs decoded live by vPIC
(`samples/examples.json`). They are shortened here: the photo lists are cut. The history keys (`f`, `l`, `h`, `s`,
`v`) are as `loader_test.py` writes them. The `segment` values are illustrative: they are filled at build time from
`generations.toml`, which does not exist yet.

**A. Craigslist, private seller, no VIN, a cross-post** (identity from Craigslist's own fields)

```json
{"id":"craigslist:8003893269","source":"craigslist","source_id":"8003893269",
 "url":"https://www.craigslist.org/view/d/washington-2014-honda-accord-sport-35/kXeaTkJ7csDxsCN7UGFDV9",
 "seen":"2026-11-21T03:40","posted":null,"updated":null,"ends":null,
 "title":"2014 Honda Accord Sport 35 mpg,Loaded, Clean Title 4cyl,4 door Sedan",
 "price":6500,"price_kind":"ask","currency":"USD","seller_type":"private","channel":"classified",
 "seller_id":null,"seller_name":null,"phone_key":null,"vin":null,"vin_ok":null,
 "year":2014,"make":"honda","model":"Accord","trim":"SPORT","body":"sedan","drive":null,"engine":null,
 "fuel":null,"transmission":null,"identity_how":"source","vehicle_key":"2014|honda|accord|sport|sedan||",
 "segment":"honda|accord|2013-2017|sedan","miles":185000,"miles_how":"field","title_status":"clean",
 "condition":null,"color":null,"city":null,"state":null,"zip":null,"lat":38.9277,"lon":-76.9762,
 "geo_how":"pin","county":null,"from_home":null,
 "photos":["https://images.craigslist.org/00505_kUkcSj4gJ5r_0dm0t2_600x450.jpg","…"],"photo_count":8,
 "photo_ids":["00505_kUkcSj4gJ5r_0dm0t2","00E0E_ariEEyifYdj_0x20oM"],
 "photo_hash":["079981135a6632c3","3777434fe7376ce9","515306b3a0cda375","00228b0b3b784600","025e00cc3e02a6d2","9203b52927532b2e"],
 "extra":{"where":"Va,md,dc","cross_post_of":"craigslist:8002926669"},
 "f":"2026-11-21T03:40","l":"2026-11-21T03:40","h":[["2026-11-21T03:40",6500,185000]],
 "s":[["2026-11-21T03:40","2026-11-21T03:40"]],"v":"v:craigslist:8002926669"}
```
It is linked to `craigslist:8002926669` by rule 2 (8 of 8 image ids identical), and by rule 3 as well. `segment`,
`county` and `from_home` are filled at build time.

**B. Craigslist, dealer, with a VIN** (identity from vPIC)

```json
{"id":"craigslist:8004100263","source":"craigslist","source_id":"8004100263",
 "title":"2013 FORD EXPEDITION (LTD) NAV/CAM/SUNROOF/1-OWNER/HEATED-COOLED SEATS",
 "posted":"2026-11-21T03:03","price":8999,"price_kind":"ask","seller_type":"dealer","channel":"classified",
 "vin":"1FMJU2A56DEF14910","vin_ok":true,"year":2013,"make":"ford","model":"Expedition","trim":"Limited",
 "body":"suv","drive":"4wd","engine":"5.4L V8","fuel":"gasoline","identity_how":"vin",
 "vehicle_key":"2013|ford|expedition|limited|suv|4wd|5.4l v8","segment":"ford|expedition|2007-2017|suv",
 "miles":134815,"miles_how":"field","title_status":"clean","condition":"excellent",
 "city":"Leesburg","state":"VA","zip":"20177","lat":39.10412,"lon":-77.57094,"geo_how":"pin",
 "photo_count":24,"photo_ids":["00T0T_2yt0I3sVc0h_0kE0fu"],"photo_hash":[],
 "extra":{"stock":"LMC1914"},"f":"2026-11-21T03:40","l":"2026-11-21T03:40",
 "h":[["2026-11-21T03:40",8999,134815]],"v":"vin:1FMJU2A56DEF14910"}
```
ZIP 20177 is not a ZCTA (it is a PO-box ZIP), which is one reason the pin comes first.

**C. Bring a Trailer, a live auction** (a bid, not an ask; national)

```json
{"id":"bringatrailer.com:2008-audi-s8-22","source":"bringatrailer.com","source_id":"2008-audi-s8-22",
 "url":"https://bringatrailer.com/listing/2008-audi-s8-22/","title":"2008 Audi S8",
 "price":27000,"price_kind":"bid","channel":"auction","seller_type":null,
 "vin":"WAUPN94E08N005821","vin_ok":true,"year":2008,"make":"audi","model":"S8","trim":null,
 "body":"sedan","drive":null,"engine":"5.2L 10cyl","identity_how":"vin",
 "vehicle_key":"2008|audi|s8||sedan||5.2l 10cyl","segment":"audi|s8|2006-2009|sedan",
 "f":"2026-11-21T03:40","l":"2026-11-21T03:40","h":[["2026-11-21T03:40",27000,null]],
 "v":"vin:WAUPN94E08N005821"}
```
vPIC gave no drive type for this VIN; an `aliases.toml` rule (`audi s8` → awd) or the listing text has to fill
it. For BaT, `ends` and the final `why` (`sold` / `ended_unsold`) come from the item's `timestamp_end` and
`sold_text`.

---

## 10. Open choices for the owner

1. **Photo hashing:** a Pillow step in the workflow (breaks stdlib-only for that one step), hashing in the browser
   extension (natural for FB), or neither for now (rules 0–2 and 4 still work; the Trailblazer-type relist is then
   missed).
2. **Data branch or a home runner.** On the data branch, JSON Lines as recommended. If the data leaves git, SQLite
   with `catalogue.sql` as migration v1 becomes the better record.
3. **Public or private repository.** This decides how much location and seller detail `site/data` may carry
   (section 5.4).
4. **Home point and radius ladder** (75/150/300 mi), and the flag rule (residual percentile; n ≥ 20 / ≥ 8).
5. **How much hand-kept data he wants to keep:** `generations.toml` for the top ~150 models, and the
   `aliases.toml` review cadence.
6. **Which dealer lots and auction sites to read**, which drives volume from ~900 to ~2,000 new listings a day.

## Evidence index

| claim | mark | where |
|---|---|---|
| vPIC single + batch decode, field values, ErrorCode behaviour | TESTED | `samples/vpic_single_*.json`, `samples/vpic_batch.json`, `samples/cl_vin_decodes.json` |
| vPIC 50 a batch, rate control, standalone database | DOCUMENTED | https://vpic.nhtsa.dot.gov/api/ |
| Craigslist VIN/odometer/title/pin rates (n = 40 + 40) | TESTED | `cl_sample.py`, `samples/cl_report.txt`, `samples/cl_postings_*.json` |
| Craigslist daily counts 29 / 75 | TESTED (one day) | `samples/cl_today_*.html` |
| BaT chassis/VIN rates, 1,226 live | TESTED | `bat_sample.py`, `samples/bat_report.txt` |
| eBay VIN required for 1981+ | DOCUMENTED | developer.ebay.com link above |
| eBay search refused (HTTP 403; robots.txt disallows `/sch/`); Browse API needs a developer key, not tried | TESTED / limit | `samples/ebay_search.html` |
| cars.com Cloudflare challenge (HTTP 403) | TESTED | `samples/carscom_search.html` |
| FB VIN optional | REPORTED | carwhere.com, keysavvy.com |
| title parser rates | TESTED (tuned on the same sample) | `identity.py`, `samples/identity_eval.txt` |
| duplicate cases, image-id reuse, dHash distances | TESTED | `dupes_phash.py`, `samples/dupes_phash_report.txt`, `samples/trailblazer_pair.jpg` |
| storage sizes and timings | TESTED (synthetic data) | `storage_bench.py`, `samples/storage_bench_report.txt` |
| DuckDB over the proposed layout; DDL runs in SQLite + DuckDB | TESTED | `loader_test.py`, `catalogue.sql`, `samples/loader_test_report.txt` |
| DuckDB cannot use the history.py state shape directly | TESTED | the run against a copy of `state/www.yoox.com.json` (copy deleted afterwards) |
| GitHub 100 MiB block / 50 MiB warning | DOCUMENTED | docs.github.com link above |
| Craigslist paid posts last 30 days | DOCUMENTED (FAQ page) / REPORTED for renewal rules | https://www.craigslist.org/about/help/faqs/lifespan |
| geo.py reuse, ZCTA centroids | TESTED | `geo_test.py`, `samples/geo_test_report.txt`, `samples/gazetteer/zcta.zip` |
| volume per source other than Craigslist and BaT | ESTIMATE | section 5.1 |

Scratch scripts are run from `_scratch/catalogue/`. `_pylib/` (63 MB) holds duckdb 2.0.1 and Pillow 13.0.0,
installed with `pip --target` for the tests only. `PYTHONPATH=_pylib py <script>` uses them. Delete the folder when
it is no longer needed.
