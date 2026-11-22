# 11. Valuing old, cheap, high-mileage cars

Measured on the page of 2026-11-21T22:02, frozen as `research/_scratch/valuation/snapshot.json`: 3,933 cars, 3,642
dealer and 291 private. No auction lot is in any number here (the catalogue gained 186 while this was worked; the
snapshot was checked against the listing's channel). The page was rebuilt during the work and now shows 271
private cars; every number below is from the frozen 291. Scripts, saved outputs and the one network capture are
in `research/_scratch/valuation/`. Nothing in the product was changed.

Labels: **TESTED** = computed or fetched here. **DOCUMENTED** = read in a primary source. **REPORTED** =
second-hand. "Error" is always the figure against the car's own asking price, `|figure / ask - 1|`, with the car
held out of the fit that priced it (five folds, the same crc32 split `value.judge` uses; nothing is random except
one bootstrap, seeded).

## Recommendation

**Change the model first, then widen the window, and say on the page which of three footings a figure stands on.**
The window is not what makes private cars hard. Today's 29 judged private cars are judged badly: the figure is
29% from the ask in the median and sits 21% under it, because the model has no idea a seller is private except by
accident (below). With two added terms the same 29 cars come to 15%, and 50 more can be judged at 26%.

### What to change in `cartrack/value.py`

1. **Fill missing engine fields before anything else.** A car that lacks `cylinders`, `litres`, `weight_class`,
   `drive` or `body` takes the commonest value among the cars of its own make and model that state it (ties: the
   smaller value as text). Nothing known for the model: left empty, as now.
2. **Cap the curve's inputs.** In `_features`, use `min(age, 30)` and `min(miles, 300000)` for every term.
3. **Two new terms, not shrunk (add both to `_FREE`).** `private_age` = age / 10 when `car["seller"] == "private"`.
   `private_pickup` = 1 when the seller is private and `body` is `pickup` or `truck`. `build.py` already passes
   `seller` in each car.
4. **Neighbours on a ladder.** Same make and model, not the car itself. Take the first of these windows that
   holds three or more: 2 years / 30,000 miles, 3 / 45,000, 4 / 60,000, 6 / 90,000. Move each neighbour to the
   car's year, miles **and seller** with the held-out fit, exactly as now but with `seller` in the override:
   `other.price * priced(W, features({**other, year, miles, seller: car's})) / priced(W, features(other))`.
5. **The figure.** With three neighbours on the ladder: `typical = min(model, median of the moved neighbours)`, as
   now. Without: `typical = the model's own figure`.
6. **Say what it rests on.** Return `basis` beside `typical` and `similar`: `"close"` (the first window),
   `"wide"` (any later window; also return the window used) or `"rough"` (the model alone). Return `low` and
   `high` too: `typical` times the two factors in the table under "What the page should say".
7. **Branded titles.** Price rebuilt, salvage and lien cars against clean cars: pass them to `judge` marked so
   that they are priced but never fitted, never counted, never used to fill a field and never a neighbour.
   `parts_only` and `missing` stay unjudged (five cars, asking a quarter of the clean figure).
8. **Marks (`site/logic.js`).** Dealer `close`: 10% or more under, as now. Dealer `wide`: 15%. Private `close`
   or `wide`: 30%. `rough`: a figure and its range, never a mark. Branded: never a mark.

Three tests in `tests/test_value.py` assert the old behaviour and will need rewriting, not deleting:
`test_a_model_with_too_few_similar_cars_gets_no_judgement`, `test_cars_far_off_in_years_or_miles_are_not_similar`
(both become `basis == "rough"`), and `test_the_judgement_says_how_many_similar_cars_it_rests_on`.

### What to expect (TESTED, `10_rule.py`, `13_bands.py`)

| | Today | Proposed |
|---|---|---|
| Private cars with a figure fit to mark (`close` or `wide`) | 29 | **79** clean, plus 39 branded shown against clean |
| Their median error | 29.4% | **20.4%** (`close` 15.0%, `wide` 26.2%) |
| Off by more than 25% | 62% | 46% (`close` 34%, `wide` 52%) |
| Private cars with a rough figure only | 0 | 93 clean (median error 38.7%), plus 18 branded |
| Private cars with nothing | 262 | 62 (50 clean but unnamed, 7 branded unnamed, 5 parts-only or no title) |
| Dealer cars judged, median error | 2,510 at 6.2% | 2,510 at 6.3%, 718 `wide` at 9.9%, 414 `rough` at 13.2% |
| Marks | 134 dealer, 8 private | 143 + 61 dealer, 11 private |

So 229 of the 291 private cars get some figure, against 29 today. 118 of those stand on neighbours: 79 clean
cars that can be marked and 39 branded cars shown against clean ones. The price of the wider reach is plain in
the table: a `wide` private figure is wrong by a quarter in the median, a `rough` one by
nearly two fifths. Those errors are close to the floor the data allows (next section), so more modelling will
not buy much; more private comparables might.

The 11 private marks, read one by one (`11_checks.py`): a 2020 Pacifica "Mechanic Special / As-Is" at $3,500
against $12,400, a 2016 Maxima "Drives but has a misfire", a 2019 Rogue with 191,000 miles at $3,500, a 2013
Fusion at $1,500, a 2008 F-150 at $2,700, a 2017 Sierra 3500HD diesel at $16,250. Two are one Grand Cherokee
listed twice. They are the right cars to look at and several are cheap for a stated reason. The mark still means
"look", as note 09 said.

## Why private cars are hard (all TESTED)

**Where the cars are** (`03_support.py`; clean title, named, with mileage: 3,642 dealer, 172 private):

| Model year | Dealer | Private | | Miles | Dealer | Private |
|---|---|---|---|---|---|---|
| 2005 and earlier | 14 | 33 | | under 60,000 | 1,849 | 12 |
| 2006-2010 | 35 | 34 | | 60-120,000 | 1,548 | 42 |
| 2011-2015 | 276 | 53 | | 120-180,000 | 203 | 58 |
| 2016-2020 | 1,060 | 45 | | 180,000 and over | 42 | 60 |
| 2021 and later | 2,257 | 7 | | | | |

Before 2011 and past 180,000 miles the private cars outnumber the dealers'. There a private car's comparables are
other private cars, and there are few: 95 distinct models among 172 cars, 63 of them seen once.

**Two private sellers do not agree with each other** (`07_private_market.py`). Pairs of the same model within
two years and 30,000 miles:

| Pairs | How many | Median gap between the two asks | One ask against the middle, about |
|---|---|---|---|
| private with private | 24 | 32.6% | 22% |
| dealer with dealer, 2015 and earlier or over 120,000 miles | 203 | 20.0% | 14% |
| dealer with dealer, all | 16,335 | 11.3% | 8% |

No listing states what is wrong with a car, and at $3,000 that decides the price. About 22% is the least error any
method can show on private cars here; 24 pairs is a thin base for that number. The proposed `close` figure (15%)
and `wide` figure (26%) straddle it.

**What the misses look like** (today's model plus a plain private term, `07`): private heavy-duty and diesel
trucks ask 55% over the model (n=21), other pickups 27% over (n=29), cars and minivans 17% under (n=50). The 23
private cars asking under $3,000 are modelled at a median $4,028. The lowest dealer ask in the catalogue is
$3,495: the dealers do not sell the cars the owner is looking for, so the model has never seen their price level.

## Question 1: the model alone

Each car priced by a fit that left it out; no neighbours used (`04_ridge_alone.py`, `11_checks.py`).

| Cars | n | Today's model: median error | off >25% | bias | Proposed model: median | off >25% |
|---|---|---|---|---|---|---|
| Dealer, all | 3,642 | 7.2% | 8.0% | +0.5% | 7.3% | 7.4% |
| Dealer, 2015 and earlier | 325 | 13.6% | 26.2% | -1.8% | 13.7% | 28.3% |
| Dealer, over 120,000 miles | 245 | 13.0% | 24.5% | -1.1% | 11.4% | 24.5% |
| Dealer, under $10,000 | 146 | 19.4% | 39.0% | +15.0% | 21.6% | 45.9% |
| Private, all | 172 | 36.1% | 66.9% | -1.0% | 27.8% | 58.7% |
| Private, 2015 and earlier | 120 | 38.5% | 73.3% | +1.0% | 32.5% | 68.3% |
| Private, over 120,000 miles | 117 | 38.7% | 72.6% | +0.8% | 30.7% | 64.1% |
| Private, under $10,000 | 119 | 32.3% | 62.2% | +24.3% | 29.3% | 59.7% |
| Private, without three close neighbours | 143 | 36.6% | 67.1% | +1.4% | 29.3% | 63.6% |

("Under $10,000" picks cars by the answer, so it picks the model's overestimates: the +15% and +24% are partly
that. The rows by year and mileage do not have this fault.)

- **Usable alone for old dealer cars**: 13-14% median, about one in four off by more than 25%. Twice the error
  of a judged car today, and good enough for a labelled figure.
- **Not usable alone for private cars**: two in three are off by more than 25%. That holds for the 143 with
  fewer than three close neighbours as much as for the rest. (On this snapshot 96 of the 143 have no close
  neighbour at all, 38 have one and 9 have two.)
- **Does it extrapolate badly?** Less than feared, on the curve. A model that saw only cars from 2016 on with
  under 120,000 miles prices the 471 older or higher-mileage dealer cars at 14.8% median, against 13.1% for the
  model that saw them. The failure is the level, not the slope: a model fitted on dealers only prices private cars
  16% high in the median, 22.5% high for 2015 and earlier, and its 80th-centile miss there is 94%.
- **A hidden term.** Today's model shows no bias on private cars (-1%) only by accident. 5 of 291 private cars
  have cylinders, 7 litres and weight class (no VIN, no decode); 3,113, 3,537 and 3,612 of the 3,642 dealer cars
  have them. A missing field is a zero, so "has no engine fields" works as a private-seller term. A neighbour
  moved to the car's year and miles keeps its own engine fields, so the neighbour estimate comes out at dealer
  level and the model at private level, and `min()` takes the lower. That is why today's 29 private figures sit
  21% under the ask. An explicit private term added without filling the fields comes out at -0.16 in the log
  (five folds: -0.12 to -0.20); with the fields filled it is -0.40 (-0.38 to -0.43).
- **Leverage.** One dealer car has an odometer of 1,824,979 (a 2016 Grand Caravan at ezautomemphis.net). With it
  in the fit, the `m2` weight is 0.001; in the one fold that holds it out, 0.018. One typed number sets the
  curve for every high-mileage car. Hence the caps.

## Question 2: the cheaper alternatives, coverage against error

Private cars, clean title and named (172). "Figure" is the neighbours' median unless it says otherwise.
(`06_windows.py`, one saved output per model; `10_rule.py`.)

| Method | Private cars covered | Median error | Off >25% | Bias |
|---|---|---|---|---|
| **Today**: min(model, 2y/30k neighbours) | 29 | 29.4% | 62% | -21% |
| Today's model, neighbours only, 2y/30k | 29 | 21.3% | 41% | +8% |
| Today's model, window 4y/60k | 56 | 31.3% | 54% | +31% |
| Today's model, window 6y/90k | 79 | 31.5% | 61% | +28% |
| Today's model, widen until three (any distance) | 150 | 40.2% | 64% | +34% |
| Today's model, same make and body within 4y/60k | 78 | 28.3% | 56% | +7% |
| Today's model alone | 172 | 36.1% | 67% | -1% |
| Plain private term (fields not filled), widen until three | 150 | 30.4% | 59% | +19% |
| Private term, fields filled, widen until three | 150 | 30.1% | 60% | -4% |
| **Proposed model**, neighbours only, 2y/30k | 29 | 13.4% | 28% | -2% |
| Proposed model, window 6y/90k (ladder) | 79 | 18.8% | 34% | -1% |
| Proposed model, window 10y/150k | 120 | 24.3% | 47% | 0% |
| Proposed model, widen until three (any distance) | 150 | 28.2% | 53% | +3% |
| Proposed model, same make and body within 4y/60k | 83 | 24.0% | 47% | -2% |
| Proposed model alone | 172 | 27.8% | 59% | -2% |
| **Proposed rule**: min(model, ladder to 6y/90k) | 79 | 20.4% | 46% | -9% |
| Proposed rule, cars it adds to today's 29 | 50 | 26.2% | 52% | -13% |
| Proposed rule's `rough` cars | 93 | 38.7% | 70% | +2% |

What the table says:

- **Wider windows on today's model make things worse**, because every neighbour is a dealer car and the move
  carries it across ten years at dealer level: +28% to +34% too high.
- **The private term is what the windows needed.** Private sellers ask less than dealers by an amount that grows
  with the car's age: 6% less at two years old, 18% at six, 31% at eleven, 41% at sixteen, 50% at twenty-one
  (the five folds agree within five points at each age). A private pickup is the exception: 33% to 50% above a
  private car of its age, which leaves it near dealer level until about ten years old. Both terms keep their
  size on two other splits of the cars into folds (`11_checks.py`: age term -0.30 to -0.38, pickup +0.28 to
  +0.45), and the rule's private error on those splits is 20.4% and 20.5% against 20.4%.
- **Whether that gap is the seller or the car cannot be told from this data.** Dealers hold 49 cars from 2010 or
  earlier and private sellers 67; "private" and "old" arrive together. For comparing a private car with other
  private cars it does not matter. It would matter for saying what a dealer would ask for the same car.
- **Past 6 years / 90,000 miles the neighbours add nothing over the model** (38.4% against 38.7% on the 71 cars
  that have them), so the rule stops the ladder there.
- **Pooling by make and body** is about as good as the wide window and covers the same cars. It is not in the
  rule because it adds a second kind of neighbour to explain for no gain.
- **The donut test** (cars that have three close neighbours, priced from the ring outside them instead): for
  dealers' old cars the ring out to 6y/90k gives 14.4% against 10.9% from the close ones (n=109), and the two
  figures differ by 10% in the median. For all dealer cars 9.2% against 6.7% (n=2,321). For private cars 20.2%
  against 13.4% (n=27). A wide window costs three to seven points where it can be checked.
- **Dealer cars gain too**: 718 more judged at 9.9% median (11% off by more than 25%), and 414 with a rough
  figure at 13.2% (26% off by more than 25%).

## Question 3: more comparables, or more modelling?

**More comparables, of the private kind, and the cheapest source is the catalogue's own past.**

- Within an age band, a private car with three neighbours inside 6y/90k is judged better than one without:
  2016 and later 14.7% against 25.9% (n=41, 11); 2011-2015 27.1% against 33.4% (n=32, 21). Age costs more than
  the missing neighbours do: only 6 of the 67 private cars from 2010 or earlier have three (TESTED, `10_rule.py`).
- Of the 93 `rough` private cars, 24 lack one neighbour, 27 lack two and 42 lack all three (TESTED, `12`).
- 95 of the 172 have no private car at all among their 6y/90k neighbours; only 15 have three.
- **Keep gone listings as comparables.** `page_data` judges live cars against live cars. 85 of the 293 live
  private listings were posted in the last seven days, so at least 85 a week arrive across the seven cities
  (a floor: listings posted and already taken down are not counted) (TESTED from `posted`). Sixty days of gone
  private listings kept as neighbours would be several times today's 172. Not tested: the catalogue is one day
  old. A gone listing's last ask is the comparable; its date matters little over two months.
- **Craigslist by-dealer listings: not measured.** The one allowed request,
  `GET https://memphis.craigslist.org/search/ctd` at 2026-11-21T22:59Z with user agent `cartrack/0.1`, answered
  **301** to `https://www.craigslist.org/search/area/memphis?cat=cta&purveyor=dealer` with no body
  (`cap/memphis_ctd.headers`). The redirect is a second address and was not followed, so there is no count and no
  price range. What can be said without it: these are dealer asks. They would thicken the 2006-2015 range where
  dealers hold 311 cars, and each would still need the private-by-age move, which is the uncertain part. They
  help the shape, not the level.
- **Cars.com set of 2026-10-17** (note 04: 1.61M listings, CC-BY-4.0, no account): five weeks old, so current
  enough. Its year counts (TESTED there, `_scratch/discounts/01_profile_output.txt`) hold about 85,600 listings
  of model years 2006-2015 and about 13,000 older, against 311 and 14 here. All dealer asks, national, no title
  status, no text. It would settle each model's curve at age and mileage. It cannot give the private level.
  It is parquet: the standard library cannot read it, so it would enter as a small table made once outside the
  build. Note 04 measured the same kind of model on it at 13.4% median for cars 13 years and older.
- **Craigslist vehicles set (Kaggle, Austin Reese)**: the only public set with private sellers, title status and
  condition. Needs an account. Search results describe versions of 374,000 to 426,000 rows, a 2021 version and a
  Zenodo mirror dated January 2024 (REPORTED; the Kaggle page itself was not reached). Too old for price levels.
  Usable for ratios that move slowly: private against dealer by age, rebuilt against clean, "fair" against "good".
- **US Used Cars 3M (CarGurus, 2020)**: dealer asks from 2020. Too old for levels.
- **Impound hammer prices** (note 10): not measured here; auction lots were left out of every number. From note
  10 they carry no mileage, no keys and no title, with a median of $575. They are a different price level and
  should be compared only with each other, never with asks.

## Question 4: branded titles

62 usable branded private cars: 49 rebuilt, 5 lien, 4 parts only, 3 salvage, 1 no title (`09_branded.py`,
`11_checks.py`). Each priced by the proposed kind of model fitted on clean cars only.

| Title | n | Median year, miles, ask | Ask against clean private cars of the same year, model and miles |
|---|---|---|---|
| Rebuilt | 49 | 2014, 137,000, $5,500 | **+2.5%** (90% interval -9% to +13%, 2,000 resamples, seed 11) |
| Rebuilt, 2016 and later | 19 | | -11.6% |
| Rebuilt, 2015 and earlier | 30 | | +13.5% |
| Rebuilt, with three clean neighbours on the ladder | 33 | | ask/typical 1.17, against 1.09 for clean private cars |
| Salvage | 3 | 2014, 100,500, $5,500 | +0.7% |
| Lien | 5 | 2021, 118,000, $26,500 | -7.7% |
| Parts only | 4 | 2006, 290,000, $800 | -78% |

- **Rebuilt cars here do not ask less than clean ones.** The 90% interval puts any discount at 9% or less.
  45 of the 49 are on the Memphis and North Mississippi sites, and they vary less around their own middle (21%)
  than clean private cars do, which is how a few sellers pricing by one rule would look. That reading is a guess.
- Elsewhere rebuilt cars are said to sell for 20% to 40% less than clean ones (REPORTED: TIME citing Kelley Blue
  Book; one site that matched cars by model, year and mileage reports 17.6% on average).
- **So: yes, judge them against clean cars, and no, the data gives no discount to state.** Show "a clean-title
  car like it asks about $X" and the title word, and never mark one. A rebuilt car at the clean figure is dear,
  not fair. If the owner wants rebuilt cars marked, the rule would be "30% under the clean figure after taking a
  further 30% off it", and that second 30% is an UNTESTED GUESS taken from the reported range.
- Salvage (3) and lien (5) are too few to say anything. A lien is not damage; it is money owed on the car.

## Question 5: what the page should say

Print the footing and a range, from the measured spread of asks around the figure (`13_bands.py`):

| Seller, basis | Cars | Median error | Six in ten asks fall between | Words on the page | Mark at |
|---|---|---|---|---|---|
| Dealer, `close` | 2,510 | 6.3% | 0.96 and 1.13 of typical | "8 like it within 2 years and 30,000 miles" | 10% under |
| Dealer, `wide` | 718 | 9.9% | 0.94 and 1.19 | "4 like it, up to 6 years and 90,000 miles away" | 15% under |
| Dealer, `rough` | 414 | 13.2% | 0.85 and 1.19 | "rough: none like it for sale" | never |
| Private, `close` | 29 | 15.0% | 0.90 and 1.25 | as dealer `close`, plus "private sellers" | 30% under |
| Private, `wide` | 50 | 26.2% | 0.84 and 1.47 | as dealer `wide`, plus "private sellers" | 30% under |
| Private, `rough` | 93 | 38.7% | 0.64 and 1.63 | "rough: none like it for sale" | never |

- Show the range as dollars: "private sellers ask about $4,300 for one like it; most ask $3,600 to $6,300".
  `low` and `high` are `typical` times the two factors.
- Say the window that was used, in years and miles, with the count. A figure from "3 within 6 years" then reads
  differently from one from "8 within 2 years" without a word of explanation.
- A `rough` figure gets a range and no badge. Sorting by "most under typical" should leave `rough` cars out, or
  the top of the list will be the model's mistakes: 25% of `rough` private cars ask 30% or more under the figure.
- Mark thresholds are about one and a half times each footing's median error. At 10% a `wide` dealer figure
  would mark 13.8% of its cars against 5.7% for `close`; at 15% it marks 8.5%.
- The factors come from one evening's catalogue. They should be recomputed by `judge` on each build (the held-out
  figures are already there) once there are 30 or more cars on a footing, and fall back to these otherwise.

## Tried and rejected (all TESTED unless marked)

| Tried | Result | Why not |
|---|---|---|
| The model alone for every unjudged car | private 36.1% median, 67% off by over 25% | too wrong to mark; kept only as `rough` |
| Widen until three are found, any distance | covers 150; +34% bias on today's model | past 6y/90k no better than the model |
| Two more age hinges (over 14, over 19 years) | private 34.9% against 35.0% | no gain; weights jump between folds |
| Private term times miles | private 35.6% | no gain; sign changes between folds |
| Private term plus private-by-age, both | 27.6% against 27.8% for the one term | the pair trade off: one fold gives -0.39 and -0.06, another -0.10 and -0.29 |
| Flat private term with the pickup term, fields filled | 28.6%; bias -15.5% on 2016 and later, +27.5% on 2005 and earlier | too deep for new cars, too shallow for old |
| Own level and slopes for every pickup, dealer or private | private 34.3% | the pickup effect is a private-seller effect |
| Weight class from the seller's words ("2500", "F-350", "dually") | 39.3% against 39.7% on the 18 such trucks | 628 of 768 dealer pickups are class 2 already; the class does not separate a 1500 from a 2500 |
| The seller's stated condition as terms | "fair" is -41% to -56% across folds and variants (n=9 clean and named, 22 in all); median error unchanged at 34% | worth a caution on the page, not a model term yet; "excellent" and "good" differ by 10% |
| Naming a car by make only, as a fallback for the 42 with a make and no model | 26.0% with the model masked, against 27.8% with it | on mainstream cars the model name adds little; but the 42 are not mainstream (see below) |
| A fit on dealers only, applied to private cars | +16% bias, 80th centile 69% | this is today's model minus its accident |
| Following the Craigslist redirect | not done | outside the one request allowed |

The 56 unnamed private cars (42 with a make, 14 with none) are mostly not cars the comparison is for: 1935-1979
classics, a Freightliner, a Kenworth, a Peterbilt, a school bus, two motorcycles, a pair of ATVs. About ten are
ordinary cars the catalogue has no VIN-named model for (Mazda Tribute, Infiniti QX56 and G37x, Hyundai XG350,
Volvo C70, BMW Z4, PT Cruiser, Pontiac G6 and G8, Suburban with no make typed). A model list from vPIC by make
would name those; they would land on `rough`.

## Open questions

- **The choice of terms was made on the same 172 private cars that score it.** About a dozen variants were
  tried. Two other fold splits give the same error, which shows the fit is stable and does not show the choice
  was not lucky. The first honest test is next week's private listings, priced by tonight's fit.
- **Is the private gap the seller or the car?** Needs dealer cars from before 2011, which Craigslist's by-dealer
  listings or the Cars.com set would supply.
- **Whether a mark at 30% under finds deals or finds faults.** Of the 11 private marks, at least two state a
  fault in the title. Only gone-dates will tell: a real deal should vanish sooner than its neighbours.
- **Duplicates.** 9 private cars in 4 groups share make, model, miles and price (one Silverado three times). A
  duplicate is a neighbour that agrees exactly. Dropping neighbours with the car's own seller type, miles and price
  is recommended and was not in the measured rule.
- **Heavy-duty trucks** are still the worst-priced private cars (the 18 named by their words: 39% median). The
  fix is in naming, not valuing: "Dodge Ram" with trim "2500" should be compared with 2500s.
- **The Craigslist by-dealer count**: one followed redirect would answer it.
- **Recalibration**: the six pairs of range factors and the thresholds are from one night.

## Files

`research/_scratch/valuation/`, run from that folder with `py <script>`; each has a saved `*_out.txt`.

- `02_snapshot.py`, `02b_snapshot_condition.py`: freeze the page's cars (`snapshot.json`), auction lots excluded.
- `common.py`, `exp.py`: loading; the model with switchable terms; out-of-fold fits cached as `cache_*.pkl`.
- `01_reproduce.py`: the harness reproduces the page's `typical` and `similar` on 3,933 of 3,933 cars.
- `03_support.py` (where the cars are), `04_ridge_alone.py` (question 1), `05_residuals.py` (the worst misses).
- `06_windows.py <terms>` (question 2; outputs `06_out_*.txt`, estimates `06_est_*.json`).
- `07_private_market.py` (pairs, condition, kinds), `08_model_variants.py`, `08b_impute.py` (the variants).
- `09_branded.py` (question 4), `10_rule.py` (the proposed rule), `11_checks.py` (marks, branded tiers, other
  splits, make-only, extrapolation), `12_more_comparables.py` (question 3), `13_bands.py` (question 5).
- `cap/memphis_ctd.headers`: the 301.
- `00_profile.py` reads the live page, not the snapshot; its saved output is of the later, 271-car page.

## Sources

- REPORTED: [TIME, rebuilt against salvage titles](https://time.com/personal-finance/article/rebuilt-title-vs-salvage-title)
  (Kelley Blue Book's 20% to 40%); [forcar.org, rebuilt titles](https://forcar.org/title-check/rebuilt/) (17.6%).
- REPORTED: [Zenodo mirror of the Craigslist vehicles set](https://zenodo.org/records/10457828), January 2024.
- Notes 04, 09 and 10 in this folder for the datasets, today's method and the impound sale.
