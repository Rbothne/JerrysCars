# 04 — Identifying a real discount

Research date 2026-11-20. Evidence labels: **TESTED** (ran it here, files under `_scratch/discounts/`), **DOCUMENTED** (read in a primary source), **REPORTED** (second-hand). Numeric thresholds with no data behind them are marked **UNTESTED GUESS**, following the owner's convention.

---

## The recommended scoring method (page one)

**Do not rank by "percent below expected price".** Rank by the expected *net profit after every cost*, using a deliberately low resale estimate and discounted by how likely the listing is genuine:

```
expected_ask   = hedonic model of log(asking price) for this car where it would be resold          (section 1)
resale_low     = expected_ask * (1 - g_segment) * (1 - drift * months_held) * (1 - h)              (sections 2, 4)
                 g_segment  ask-to-sale gap for the segment, shrunk toward 8 %
                 h          haircut standing in for a lower-quantile model, start 7 % (UNTESTED GUESS)
cash           = ask * (1 - b) * (1 + sales_tax) + title_reg + inspection + history_report
                 + transport(miles) + recon(age, class) * 1.25                                    (section 4)
net_low        = resale_low - cash - holding(cash, H_segment) - listing_fees
SCORE          = P_genuine * net_low                                                              (section 5)
z              = log(ask / expected_ask) / sigma_segment      (how unusual the price is for this segment's model error)
SHOW only if   net_low >= $1,000  AND  net_low / cash >= 15 %  AND  z <= -2      (all three UNTESTED GUESS)
               AND no hard false-positive rule fires                                              (section 5)
```

- **Expected price, first method: a pooled hedonic regression on log asking price**, the same design as his JobScope `docs/07-scoring.md` (one ridge/OLS fit over everything, main effects plus make-model x year, make-model x trim, a per-model mileage slope, region, title status), scored out-of-fold, printed beside an aptrack-style table of the 5-10 nearest comparables so every number explains itself. On 826,484 Cars.com used listings it had a median absolute error of **5.3 %** against 4.4 % for LightGBM, 6.3 % for the shrunk segment median and 7.9 % for a plain segment median (TESTED).
- **Upgrade path:** (1) LightGBM, fit as a *quantile* model (q50 to price the buy, q20 to price the resale, after Dress, Lessmann and von Mettenheim's asymmetric-cost result); (2) per-segment ask-to-sale gap learned from price-cut-then-vanish listings and auction results; (3) the paper-trade loop retunes `g`, recon, hold time and the gates the same way `ticketdesk/learning.py` does.
- **Why not his percentile-with-shrinkage as the price model:** it works for "is this markdown unusual for this store", but on car *price levels* the shrinkage pulls a thin cell toward a parent that ignores mileage. In cells with fewer than 5 comparables it was the worst method tested (27.9 % median error, TESTED). Keep SHRINK for what it does well: shrinking per-segment *parameters* (the ask-to-sale gap, the residual spread `sigma_segment`, days to sell) toward their parents.

**What the hands-on pass changed:**

1. A flat "20 % below expected" rule is mostly a model-error detector. With the simple model it flags **7.6 %** of listings; only **31 %** of those are still flagged by the best model. Flags concentrate in thin cells (49 % against 6 % of the rest), high mileage (31 % at 150k+ miles against 2 %) and old cars, which is exactly the cheap end this project targets (TESTED).
2. The deepest consensus flags (residual -80 % or lower) were not deals: they were down-payment or placeholder prices ($2,204 or $2,999 on a 2022 QX60, 2017 Escalade, 2019 XC60 from the same few dealers), a "Demo Account" seller and an odometer of 12,345 (TESTED, `sample_flagged_consensus_deepest.csv`).
3. Below $10,000 the cost stack eats a 20 % discount. On a car expected to sell for $10,000 with $1,000 of reconditioning, break-even needs the asking price **24 %** below expected and a $1,000 net needs **34 %**. At $5,000 with $1,000 of reconditioning those figures are 38 % and 58 % (TESTED arithmetic on cited and UNTESTED GUESS inputs, `04_breakeven_grid.json`).
4. In the only public "delisted" set found (EU, 3-week crawl), cheap listings did **not** vanish sooner (median 1.0 days for 30 %+ under, 0.5 days at fair price). Treat "disappeared" as a sale only when it was polled often and checked for relists (TESTED, with the caveats in section 6).
5. Volume cap: many states treat someone who sells more than about 3-6 cars in 12 months without a dealer licence as an unlicensed dealer (Arizona 6, Washington 5, NADA "three to five in most states", DOCUMENTED/REPORTED, section 4). The tracker should rank the year's few best flips, not a stream of small ones, and the plan should price a dealer licence if more volume is wanted.

---

## 1. Expected price: the options compared

### What was run (TESTED)

Data: `KTHESAT/usa-used-car-market-cars-com` on Hugging Face, 1,614,161 Cars.com listings scraped on 2026-10-17, CC-BY-4.0, no account needed. Cleaned to 826,484 used cars: unique VIN, price $2k-$250k (drops 9,014 "$0 / call for price" rows), 100-400k miles, model years 1995-2026. All are **dealer asking prices**; there is no title status, no description text, no history. Every estimate is out-of-fold (5-fold) so no listing prices itself. Script: `_scratch/discounts/scripts/02_expected_price.py`; numbers: `02_results.json`.

| Method | Median abs. error | Mean abs. error | Within 10 % | Within 20 % | Error, cell < 5 comps | Error, cell 100+ | Error, 13+ yr old | Dealer hold-out |
|---|---|---|---|---|---|---|---|---|
| M1 segment median (make/model/year/20k-mile band, fall back when n<3) | 7.9 % | 13.0 % | 59.0 % | 83.5 % | 22.8 % | 7.0 % | 18.7 % | — |
| M2 shrunk median, K=10 (his SHRINK on price levels) | 6.3 % | 12.5 % | 67.0 % | 86.3 % | 27.9 % | 4.7 % | 23.2 % | 6.5 % |
| M3 depreciation curve per make-model (log p ~ age + age² + miles) | 8.6 % | 12.2 % | 56.2 % | 83.7 % | 13.4 % | 7.9 % | 15.7 % | — |
| M4 hedonic ridge (sparse one-hot, per-model mileage slope, zip3) | 5.3 % | 8.1 % | 75.1 % | 92.7 % | 11.0 % | 4.4 % | 13.4 % | 5.6 % |
| M5 LightGBM (same raw fields) | **4.4 %** | **7.3 %** | **79.2 %** | **93.3 %** | 10.8 % | 3.3 % | 12.3 % | 5.0 % |

Cell sizes: 63,466 listings had fewer than 5 comparables in their make/model/year/20k-mile cell, 130,086 had 5-19, 253,483 had 20-99 and 379,449 had 100 or more. Error on cars at or under $15k: M1 13.7 %, M2 15.2 %, M4 10.2 %, M5 9.4 %; over $15k: 7.2 / 5.5 / 4.8 / 3.8 %. "Dealer hold-out" scores a fifth of the dealers with none of their own stock in training (GroupKFold by seller).

![error by cell size](_scratch/discounts/charts/error_by_cell_size.png)

### The options side by side

| Option | Data needed | Thin data | Interpretability | Published or practitioner accuracy |
|---|---|---|---|---|
| **Median of comparables in a segment** (aptrack `deals.py` style) | make, model, year, mileage band; more fields shrink cells | Breaks: falls back to coarse segments that ignore mileage (22.8 % error under 5 comps, TESTED) | Best: "these 7 cars" | Same logic as CarGurus IMV, which prices "comparable current and previous car listings in a given market" plus dealer reputation (DOCUMENTED, [CarGurus help](https://cargurus.helpscoutdocs.com/article/10-what-is-imv)) |
| **Percentile with shrinkage** (wishlist `standing()`, SHRINK=10) | the same segments, plus a parent per level | Good at *not* calling 3 items an outlier; bad for price *levels* when the parent ignores mileage (27.9 % under 5 comps, TESTED) | Good | No used-car accuracy figures found |
| **Hedonic regression** on log price (year, mileage, trim, title, region...) | 10-20 structured fields; title status must be a feature | Pools strength: a rare trim borrows the mileage slope of its model (11.0 % under 5 comps, TESTED) | Good: coefficients read as "salvage -x %", "per 10k miles -y %" | Standard tool in the economics literature on car prices; Lacetera, Pope and Sydnor use 22M wholesale sales (DOCUMENTED, [NBER w17030](https://www.nber.org/papers/w17030)) |
| **Gradient boosting / random forest** | the same fields; more rows help | Close to hedonic in thin cells (10.8 %), clearly better in thick ones (3.3 %) | Medium: needs SHAP or comparables beside it | Lessmann and Voß compared 19 methods on leasing resale data and found random forest "particularly effective" (DOCUMENTED abstract, [IJF 2017](https://ideas.repec.org/a/eee/intfor/v33y2017i4p864-877.html)); Dress et al. (150,000 resold lease cars) found linear regression had the highest error of the methods tried, and quantile methods won when over-estimating resale costs more than under-estimating it (DOCUMENTED, [arXiv 1707.02736](https://arxiv.org/pdf/1707.02736), Table 4). Hobby papers on Kaggle data report "83.6 % test accuracy" without defining it (REPORTED, [arXiv 1711.06970](https://arxiv.org/pdf/1711.06970)), which is not comparable |
| **Depreciation curves** per model | age, mileage, model | Robust (one curve per model), but cannot see trim or region | Best for explaining "this model loses x % a year" | Worst point accuracy here (8.6 %) but the best of the simple methods for 13+ year cars (15.7 % against 18.7-23.2 %) (TESTED) |

### Recommendation

1. **Start with M4, the hedonic ridge.** It gets most of the gain (5.3 % against 4.4 % for LightGBM), is linear and cheap to refit on every run, and its terms can be reported the way JobScope's `premium` command reports coefficients. Add the fields this dataset lacks: **title status** (Craigslist publishes it; it must be both a feature and a hard filter), **seller type**, **condition words** from the text, and **days listed** (so stale asks don't set the baseline). Use JobScope's fit guards unchanged: `n_obs >= max(150, 15k)`, at least 10 rows per level or collapse to `other`, prediction interval printed beside every number.
2. **Express every residual as `z = log(ask/expected) / sigma_segment`**, where `sigma_segment` is that segment's out-of-fold residual spread, shrunk toward its parent with his SHRINK=10. Errors run 3.3 % for thick late-model cells and 12-23 % for 13-year-old cars, so a flat -20 % means "3 sigma" for one and "1 sigma" for the other.
3. **Show comparables beside the model** using JobScope's low-n rules: n≥20 percentiles, 5-19 a raw comparables table, <5 the model with its interval only.
4. **Upgrade to LightGBM quantile models** once the tracker has its own multi-source history. Use q50 for "what should I pay" and q20 for "what can I count on reselling for".

**Other resellable goods:** the hedonic plus comparables approach carries over to anything with structured attributes and many listings (motorcycles, trailers, boats, tools, camera bodies, GPUs). Depreciation curves suit items that age on a schedule (electronics by release date). Title status and the 10,000-mile threshold effects below are car-specific.

---

## 2. Asking price versus sale price

The model above predicts **asking** prices. Profit depends on the **sale** price, so the gap `g` has to be estimated. Sources, best first:

| Source | What it gives | Status |
|---|---|---|
| Auctions with published results (Bring a Trailer, Cars & Bids; Copart/IAA for damaged cars) | true hammer prices, plus the buyer fee (BaT 5 %, min $250, cap $7,500; Cars & Bids reported raised to match) | DOCUMENTED/REPORTED, [Autopian](https://theautopian.com/cars-bids-raises-its-buyer-fees-post-layoffs-to-match-bring-a-trailer), [Cars & Bids](https://carsandbids.com/what-is/). Auction buyers skew enthusiast, so this calibrates the enthusiast segment, not commuter cars |
| Listings that cut price, then vanish | the last asking price is an **upper bound** on the sale price; the cut sizes trace the seller's reservation path | the tracker's own data; the history code from wishlist `history.py` (`deals()`, `last_move()`) and aptrack `drop()` already captures it |
| VIN that reappears at a dealer within ~90 days | a dealer bought it: the earlier private ask minus the later dealer ask brackets the wholesale-to-retail spread | the tracker's own data (VIN in the listing or decoded from photos) |
| Consumer Reports haggling survey | median $900 or **8 % off asking** across franchise, independent and private sellers; 7 in 10 haggled, 83 % of those got a better deal | REPORTED (search summary of [CR](https://www.consumerreports.org/used-car-buying/why-haggling-for-your-next-car-really-pays); page returned 403 to direct fetch) |
| eBay Best Offer (Backus, Blake, Larsen, Tadelis, QJE 2020) | items $0.99-$1,000, 88.4M listings: sale price averages **83 %** of list, **73 %** when bargaining happened; first buyer offer 61 %; listings with a reference price sold at 91 % (81 % bargained) | DOCUMENTED, [NBER w24306](https://www.nber.org/papers/w24306.pdf) Table 1 and Appendix B. Not cars; a bound for the "other goods" lens |
| CarGurus UK "hagglers saved about 11 %"; CarSwitch (Dubai dealer) typical 8 %, top quarter 13 % | single-firm figures | REPORTED |
| CraigslistBargains (Stanford) | role-played negotiations with targets set at 0.5x, 0.7x and 0.9x of list | DOCUMENTED design ([arXiv 1808.09637](https://arxiv.org/pdf/1808.09637.pdf)); unusable as market evidence because the targets were assigned |

No published figure splits the gap between private-party and dealer sales. **Method:** start every segment at g = 8 % (CR median). Each observed bound (cut-then-vanish, VIN reappearance, auction result) updates the segment's estimate with `ticketdesk/learning.py`'s blend `base + n/(n+prior) * (estimate - base)` and a per-update step cap, so a few events move it a little. Store `g` per (seller type, price band, age band).

---

## 3. Signals beyond price level

| Signal | How to compute | Evidence and status |
|---|---|---|
| **Price cut and pace** | aptrack `drop()`: current price at least 2 % below the highest in 30 days and the latest move down; use wishlist's 3 % NOISE floor for scraped prices. Pace = cuts per week and total cut since first seen | CarGurus (2011, 2M listings): cars listed 30+ days averaged 1.5 drops and 53 % had at least one; at 45+ days 60 % had one (REPORTED via search; the post now redirects). iSeeCars: one to six cuts per listing (REPORTED) |
| **Days on market against the segment's survival curve** | wishlist `survival()` Kaplan-Meier on (days observed, ended?) per segment; signal = the listing's percentile of time-alive. Old and cut = motivated seller; new and very cheap = check for a false positive | Cox Automotive, Oct 2026: market days' supply 49.2; **under $15k only 34 days** (DOCUMENTED, [Cox](https://www.coxautoinc.com/insights/used-vehicle-inventory-october-2026/)). iSeeCars Feb 2026: 1-5-year-old cars averaged 53 days to sell (REPORTED) |
| **Relists** | same VIN, phone, or perceptual hash of the first photo under a new listing ID: carry the old first-seen date and price history forward (aptrack keeps `past` for exactly this) | without it, days-on-market resets and a stale car looks fresh |
| **Motivated-seller wording** | lexicon: "must sell", "moving", "OBO", "divorce", "estate", "need gone", "make offer", "priced to sell", "cash only today" | none quantified for cars; start as a +0.1 tie-breaker, learn the weight from paper results (UNTESTED GUESS) |
| **Low-visibility listings** | misspelled make or model (fuzzy match against NHTSA vPIC make/model names), missing year or mileage, fewer than 5 photos, wrong category (car under "auto parts", truck under "farm+garden"), all-caps or no description | eBay misspelling studies are anecdotal (a misspelled PlayStation 3 sold for $159 against $290; REPORTED). On Cars.com dealer data, flagged listings had **fewer** missing photos (3.4 % had under 5 photos, against 10.0 % of the rest), so listing quality did not mark dealer flags (TESTED). This signal belongs to Craigslist and Marketplace private ads, where it still has to be tested |
| **Mileage and year just over a threshold** | flag cars at 100,0xx-104,999 miles, or registered in January | wholesale prices drop **$150-200** at each 10,000-mile mark (DOCUMENTED, [NBER digest](https://www.nber.org/digest/sep11/limited-attention-car-market)); retail prices drop too ([NBER w18820](https://www.nber.org/papers/w18820)); mobile.de cars registered in January sell well below otherwise identical December cars (DOCUMENTED, [Englmaier et al., Management Science 2018](https://econpapers.repec.org/RePEc:inm:ormnsc:v:64:y:2018:i:6:p:2754-2766)). A buy at 101k miles is discounted on entry and the discount is *not* recoverable on exit, so it is neutral for flipping unless the seller over-discounts |
| **Seller type** | private / small independent / franchise / buy-here-pay-here / auction. Separate `g`, separate sigma, separate false-positive priors | CarGurus rates deals using dealer reputation as well as price (DOCUMENTED) |

All of these are generic marketplace signals and apply to other resellable goods unchanged. Only the odometer and registration thresholds are car-specific.

---

## 4. From discount to profit

### Cost stack (per flip)

| Item | Figure used | Source / status |
|---|---|---|
| Purchase haggle won (b) | 5 % off ask | CR median 8 % (REPORTED); 5 % to stay conservative (UNTESTED GUESS) |
| Sales tax on purchase | state rate on price; TX 6.25 %; private sales exempt from state sales tax in AK, AZ, DE, MT, NH, OR (DE charges a 4.25 % document fee, AZ a $20 transfer fee) | DOCUMENTED [Texas Comptroller](https://comptroller.texas.gov/taxes/motor-vehicle/sales-use.php); REPORTED [BillOfSaleNow 2026 survey](https://billofsalenow.com/reports/2026-state-survey). Without a dealer licence and resale certificate the flipper pays it, and the next buyer pays it again |
| Title, transfer, temporary tags | $150 | TX title application $28-33 plus $2.50 transfer (REPORTED); total is an UNTESTED GUESS |
| Pre-purchase inspection | $175 | $100-250 typical (REPORTED, vendor guides) |
| Title / brand history (NMVTIS) | $10 | approved providers listed by DOJ (DOCUMENTED, [vehiclehistory.bja.ojp.gov](https://vehiclehistory.bja.ojp.gov/nmvtis_vehiclehistory)); $1-$45 seen (REPORTED) |
| Transport | $1.50/mile short haul | open carrier ~$1.02/mile at 1,000 mi (KBB survey), $1.50-2.05/mile short haul (REPORTED, [KBB](https://www.kbb.com/car-advice/costs-shipping-vehicle)); driving it home costs a day and a return trip |
| Reconditioning by age | 0-5 yr $600, 6-10 yr $1,000, 11+ yr $1,500, plus 25 % contingency | UNTESTED GUESS anchored on dealer figures: $629 domestic / $736 import per retail unit (undated trade table), Cox/vAuto "$600-800 baseline" (2016), vAuto default estimate $1,500, Byrider top-quartile median $2,134 (REPORTED). No public breakdown by age or class was found; this is the largest uncertain input |
| Listing fees | $10 | Craigslist $5 per 30 days by-owner (DOCUMENTED, [craigslist](https://www.craigslist.org/about/Help/posting_fees)); Facebook local $0 (REPORTED); eBay Motors $79 package for vehicles over $15,000, no final value fee (DOCUMENTED, [eBay help](https://www.ebay.com/help/selling/fees-credits-invoices/fees-selling-vehicles-ebay-motors?id=4127)) |
| Holding | cash x 7 %/yr x days + $60/month insurance + 1 %/month market drift | all UNTESTED GUESS; days = the segment's survival-curve median |
| Resale haggle conceded (g) | 8 % | CR median (REPORTED) |
| Auction buyer fees (if buying there) | BaT/C&B 5 % (cap $7,500); Copart public-buyer fees conflict across sources (~9-15 % plus gate ~$79) | DOCUMENTED / REPORTED; check the live fee page |

### Worked examples (TESTED arithmetic, `04_cost_stack.py`)

| Listing | Ask vs expected | Cash in | Expected net | Conservative net | ROI on cash | Break-even discount |
|---|---|---|---|---|---|---|
| 2012 Civic 140k, private, local, $5,500 vs $8,000 | -31 % | $7,762 | -$535 | -$1,047 | -13.5 % | -44 % |
| 2018 RAV4 70k, small dealer, 40 mi, $17,500 vs $21,000 | -17 % | $19,309 | -$360 | -$1,699 | -8.8 % | -25 % |
| 2009 F-150 160k, private, 300 mi, $6,000 vs $9,000 | -33 % | $8,716 | -$669 | -$1,242 | -14.3 % | -47 % |
| 2021 Altima 45k, local, $14,400 vs $18,000 | -20 % | $15,620 | +$617 | -$530 | -3.4 % | -23 % |

Headline discount needed (expected net, local, 30-day hold):

| Expected ask | Recon $300 | Recon $1,000 | Recon $2,000 |
|---|---|---|---|
| $5,000: break-even / $1,000 net | -24 % / -44 % | -38 % / -58 % | -58 % / -78 % |
| $10,000 | -17 % / -27 % | -24 % / -34 % | -34 % / -44 % |
| $20,000 | -14 % / -19 % | -17 % / -22 % | -22 % / -27 % |
| $35,000 | -12 % / -15 % | -14 % / -17 % | -17 % / -20 % |

Most of the cost is the two haggles (5 % in, 8 % out), sales tax and reconditioning. That is why the score must be net dollars, not a percentage. The numbers also show where to look: cars needing **little reconditioning** (which a pre-purchase inspection confirms), in **states without private-sale tax**, at **$10k-$25k**, where fixed costs are a small share of the price.

### The score

`SCORE = P_genuine * net_low` (definition on page one). Report beside it: `net_expected`, `ROI = net_low / cash`, `annualised = ROI * 365 / H_segment`, `z`, `n` comparables and the prediction interval. The score decomposes term by term, as JobScope requires ("a ranking that can't explain itself is a bug"). `P_genuine` starts as 1.0 minus soft penalties (section 5, each UNTESTED GUESS) and is then calibrated by the paper-trade results.

**Volume constraint:** an unlicensed seller doing more than about 3-6 sales in 12 months is treated as a dealer in many states: Arizona 6 in 12 months (A.R.S. 28-4301), Washington "five or more" (RCW 46.70), Maryland "3 or more may be considered", NADA "three to five in most states" (DOCUMENTED/REPORTED, [WA RCW](https://lawfilesext.leg.wa.gov/law/RCWPDF/RCW%20%2046%20%20TITLE/RCW%20%2046%20.%2070%20%20CHAPTER/RCW%20%2046%20.%2070%20.115.pdf), [NADA](https://nada.org/nada/press-releases/nada-supports-efforts-protect-car-buyers-stopping-curbstoning), [MD MVA](https://stg-mva.maryland.gov/vehicles/Pages/registration/curbstoner.aspx)). With a handful of flips a year, the tracker's job is to find the best few, so precision matters far more than recall.

---

## 5. False positives: what looks cheap but is not

Hard rules remove a listing. Soft rules lower `P_genuine`; their weights are UNTESTED GUESS until paper results calibrate them.

| Cause | Detection rule | Type |
|---|---|---|
| Salvage / rebuilt / flood / lemon / "branded" title | the title field where the source has one (Craigslist does); regex on text `salvage|rebuilt|reconstructed|flood|branded|lemon|buyback|R title`; NMVTIS check before any contact; title status as a model feature, so a salvage car is compared with salvage cars | hard filter, or a separate segment |
| Undisclosed damage / mechanical | text: `needs (engine|transmission|work)|mechanic special|as is|won't start|no reverse|check engine|blown|knock|overheat|project|parts car|TMU`; photos without one of front, rear or both sides; under 5 photos on an ad under $10k | soft: -0.3 each (UNTESTED GUESS) |
| High mileage hidden in text | parse mileage from title and description (`\d{2,3}[kK]`, "miles"); if the structured field is missing, 0 or a placeholder (1234, 12345, 99999, exact multiples of 10,000) take the text value; if none, impute the segment's 80th percentile mileage before pricing | repair the field, then reprice |
| Deposit / phantom vehicle | seller won't meet or show the car, "deployed", "moving overseas", shipping only, payment by gift card, wire or "eBay escrow", price far under market; same photos found under another city or listing (perceptual hash), new account. These are the FBI/IC3 markers (DOCUMENTED, [IC3 PSA 2018](https://www.ic3.gov/PSA/2018/PSA180117), [MN AG](https://ag.state.mn.us/Consumer/Publications/OnlineCarSalesScams.asp)) | hard filter on two or more markers |
| Too cheap to be true | `z` below -4 or residual under -60 % → "check the price", aptrack's `SUSPECT_OWN/SUSPECT_LOCAL` logic; CarGurus also keeps a separate OUTLIER class (1.0 % of its 15.2M records; DOCUMENTED in the dataset card) | hard: route to a "check" tab, never rank |
| Dealer prices that exclude fees / down-payment prices | text `plus (tax|title|fees)|doc fee|reconditioning fee|down|w.a.c.|with approved credit|cash price requires`; the same seller listing at least 5 cars of at least 3 models at one identical price; buy-here-pay-here seller names | hard when the repeated-price rule fires; otherwise add the state's typical doc fee before pricing |
| Out-of-area reposts | listing location against the seller's phone area code or the photos' licence-plate state; the same photos in several metros; a dealer whose address is more than N miles from the listing city | soft -0.3; hard if the photos are reused elsewhere |
| Stale, already sold | last polled more than 48 h ago; "SOLD" or "pending" in text or image; KM time-alive above the segment's 90th percentile with no cut (a frozen ad); on Craigslist, the "posted" vs "updated" dates | soft: rank lower and re-poll before alerting |
| Model error (thin cell, odd trim, classic) | prediction interval wider than the claimed discount; `n` under 5; flagged by one model but not by a second, different model | require agreement between two different models (hedonic and boosted) before alerting |

**Measured on the Cars.com flags (TESTED, `05_results.json`).** Only the rules that need no text or history could be run on this data:

| Rule | M2 flags (62,415) | M5 flags (23,815) | Consensus flags (15,816) | Non-flagged listings (base rate) |
|---|---|---|---|---|
| R1: same seller, one price on ≥5 cars of ≥3 models | 25.0 % | 27.9 % | 31.8 % | 8.8-9.6 % |
| R2: residual ≤ -60 % against M5 | 0.7 % | 1.7 % | 2.6 % | 0 % |
| R3: placeholder odometer (12345, round 10k...) | 0.8 % | 1.2 % | 1.3 % | 0.1 % |
| R4: blank or demo/test seller name | 4.8 % | 7.3 % | 8.0 % | 0.7-0.8 % |
| any rule | 26.2 % | 30.2 % | 34.7 % | — |
| left after rules, share of all listings | 5.57 % | 2.01 % | **1.25 %** | — |

R2-R4 are specific: they fire about ten times as often on flags as on other listings. R1 is too broad as written, because it fires on about 9 % of ordinary listings, where big lots use the same "$X,998" price on many cars. It needs tightening to "one price on cars whose *expected* prices differ by more than 2x" before it becomes a hard rule. Of the starting 7.6 % flagged by the simple model, the two-model agreement rule plus R1-R4 leaves 1.25 % of listings. Those still need the text, title and inspection checks this data cannot run.

---

## 6. Validation before any money is spent

### Adapting his paper-trade loop

`ticketdesk/paper.py` opens one paper position per recommendation, replays it against later prices and judges it once the outcome is known, keeping the lower of an optimistic and a conservative result. For cars:

1. **Open** a paper position for every listing that passes the gates, the first time it does, storing the full score breakdown, model version and parameter version (as `param_version` in ticketdesk).
2. **Controls:** for each one, also log 3 matched listings that were **not** flagged (same segment, age band, price band, seller type, first-seen week). A flag is only worth something if flagged listings behave differently from comparable unflagged ones.
3. **Poll** both sets at least daily, with relist detection (VIN, phone, photo hash).
4. **Judge** at `H_segment` (the KM median days for the segment) plus 14 days.

### What counts as a correct call when all we see is a disappearance

Define outcomes per listing; only the first is a hit:

| Outcome | Rule | Reading |
|---|---|---|
| **HIT** | vanished within half the segment's KM median, no price cut, not relisted within 14 days, not marked "sold" from a placeholder or recycled ad | someone bought at about the ask |
| **SOLD-AFTER-CUT** | vanished after cuts | sale ≤ last price; feeds the ask-to-sale gap `g`. A hit only if the last price still clears the net gate |
| **RELIST** | same car back under a new ID | not sold: a miss, and a false-positive signal |
| **STALE** | still listed at the judgement date | a miss: the market did not see a deal |
| **REVEALED** | VIN reappears at a dealer or at auction with a price | the best outcome data: realised spread for whoever bought it |
| **INSUFFICIENT** | polls missed more than 2 days in the window | not judged (ticketdesk `insufficient_data`) |

Metrics: precision = HIT / judged flags; **lift** = the flagged hazard of vanishing in the first half-median against the matched controls' hazard (KM curves for both, log-rank test); calibration = realised net (from REVEALED and SOLD-AFTER-CUT bounds) against `net_low`.

**Evidence that this matters (TESTED, `03_disappearance_and_ratings.py`):** in the EU set (`KTHESAT/european-used-cars-sold-days-on-market`, 618,623 usable rows, AutoScout24 mostly, all "delisted" during 2026-09-20 to 2026-10-12), the shrunk-median residual has a 9.7 % median error and lines up with the site's own price labels: code 0 is -16 %, 1 is -7 %, 2 is -3 %, 3 is +2 %, 4 is +9 %, 5 is +18 % and 6 is +29 %; "Sehr guter Preis" is -15 % and "Erhöhter Preis" +11 %. That is a useful sanity check on the method. But time-to-vanish did **not** fall with cheapness: median 1.0 days for 30 %+ under, 0.9 for 20-30 % under, 0.5 at fair price, 0.8 for 20 %+ over. Restricted to listings seen for over an hour, the curve is flat: 2.9 to 3.1 days in every bucket. 44 % of rows vanished the same day they were first seen and `price_drop_eur` is 0 on every row. So that "sold" label is mostly crawl churn. The tracker's own polling and relist detection have to produce the outcome; a third-party "sold" flag cannot be trusted.

![EU vanish speed](_scratch/discounts/charts/eu_vanish_speed_by_residual.png)

### Readiness gate (from `readiness.py`)

Go live only when all of these pass over the last 90 days: at least 30 judged paper flags (UNTESTED GUESS); HIT precision at least 50 % and lift at least 1.5x over controls (UNTESTED GUESS); conservative realised-to-expected net at least 70 % on REVEALED/SOLD-AFTER-CUT cases (UNTESTED GUESS); no more than 20 % INSUFFICIENT. Then one real purchase, recorded in a positions ledger like `positions.py`, with every cost line actually paid. That real cost stack replaces the guesses in section 4.

### Self-tuning (from `learning.py`)

Weekly: refit `g` per segment from cut-then-vanish bounds and auction results, recon per age class from real purchases, `H_segment` from KM, and raise the net gate if paper results realise under 70 % of expected. Use the same safeguards: a minimum sample, the blend toward the base value with weight n/(n+prior), a step cap, judging only results since the last change, and a numbered parameter version on every flag.

---

## 7. Hands-on evidence

### Public datasets found

| Dataset | Account? | What it has | Used for |
|---|---|---|---|
| [`KTHESAT/usa-used-car-market-cars-com`](https://huggingface.co/datasets/KTHESAT/usa-used-car-market-cars-com) (also mirrored as `jrbaldwin/...`), 1.61M Cars.com listings, 2026-10-17, CC-BY-4.0, 139 MB parquet | **no** | VIN, make/model/trim/year, price, mileage, body, drivetrain, fuel, CPO, dealer, zip, photo count. One day only; no title status, no text | expected-price models, the -20 % rule, the false-positive rules |
| [`KTHESAT/european-used-cars-sold-days-on-market`](https://huggingface.co/datasets/KTHESAT/european-used-cars-sold-days-on-market), 679k "sold/delisted", CC-BY-NC-SA | **no** | price, previous price (always equal), mileage, registration year, days on market (max 19.5), site price label | vanish speed vs residual; checking label meaning |
| [`rebrowser/carguruscom-dataset`](https://huggingface.co/datasets/rebrowser/carguruscom-dataset), 30 daily files of 1,000 rows (2026-10-08 to 11-06), CC-BY-NC | **no** | deal rating, `priceDifferential`, days on market, history counts; **price, expectedPrice and dealScore are redacted** ("[PREMIUM]") | deal-rating dollar bands only |
| Craigslist vehicles (Austin Reese, ~426k rows, includes title status and description) / US Used Cars 3M (Ananay Mital, CarGurus 2020, includes salvage/frame-damage flags) | Kaggle **account** | the best public sets with title status and text | not downloaded; next step if text and title rules need testing |
| eBay Best Offer research data (Backus et al.) | NBER release | 88M listings ≤ $1,000 with full bargaining threads | asking-to-sale gap for "other goods" |

Facts found in the CarGurus sample (TESTED): the dataset card says positive `priceDifferential` means overpriced, but the data shows the reverse. GREAT_PRICE has a median of **+$2,306** (95th percentile $5,747), GOOD_PRICE +$886, FAIR_PRICE -$417, POOR_PRICE -$1,635 and OVERPRICED -$2,938, so the field is expected price minus asking price. OUTLIER listings sit on both sides with extreme values (median -$5,521, minimum -$1.52M).

### First pass: the simplest expected-price model and the -20 % rule (TESTED)

Residual = asking / expected - 1, out-of-fold:

| Quantile | 1 % | 5 % | 10 % | 25 % | 50 % | 75 % | 90 % | 95 % | 99 % |
|---|---|---|---|---|---|---|---|---|---|
| M2 shrunk median | -53 % | -26 % | -16 % | -7 % | 0 % | +6 % | +14 % | +22 % | +50 % |
| M5 LightGBM | -30 % | -15 % | -10 % | -4 % | 0 % | +5 % | +11 % | +17 % | +40 % |

![residuals](_scratch/discounts/charts/residual_distribution.png)

Share flagged at ≤ -20 %: M1 7.0 %, **M2 7.6 %**, M3 6.8 %, M4 3.0 %, M5 2.9 %. Only 31 % of M2's flags and 30 % of M1's are confirmed by M5; M4 and M5 agree on 70 %. Flagged by M2, M4 and M5 together: 1.9 %.

How M2's flags (62,415) differ from the rest (764,069), as medians or shares:

| Field | Flagged | Rest |
|---|---|---|
| asking price | $9,480 | $29,795 |
| mileage | 122,379 | 34,938 |
| age (years) | 10 | 3 |
| 150k+ miles | 31.2 % | 2.1 % |
| thin cell (< 5 comps) | 49.1 % | 5.6 % |
| CPO | 3.5 % | 26.1 % |
| CarMax | 0.5 % | 5.7 % |
| price ending 95/98/99 | 30.4 % | 21.9 % |
| under 5 photos | 3.4 % | 10.0 % |
| dealer with < 20 listings | 8.6 % | 6.9 % |
| body: sedan / SUV | 25.6 % / 41.4 % | 17.1 % / 57.9 % |

For the consensus set (15,816): median ask $6,995, 111,300 miles, 10 years old, 35 % thin cells, 0 % CarMax. A random sample of consensus flags (`sample_flagged_consensus_random.csv`) looks like plausible cheap independent-lot stock (2021 Forester Limited at -31 %, 2017 Rogue S 109k at -37 %, 2020 CX-5 at -29 %) that needs the text, title and inspection checks this data cannot provide. The deepest flags (`sample_flagged_consensus_deepest.csv`) are almost all placeholder or down-payment prices.

---

## Files

`C:\Users\Aeske\Documents\active_projects\CraigsCars\research\_scratch\discounts\`
- `scripts/00_inspect.py`, `01_profile.py` (schemas, value counts; output `01_profile_output.txt`)
- `scripts/02_expected_price.py` (M1-M5, out-of-fold, -20 % rule, charts; `02_results.json`, `02_output.txt`, `flagged_vs_rest_*.csv`, `sample_flagged_*.csv`, `residuals_sample_20k.csv`, `residuals_all.parquet`)
- `scripts/03_disappearance_and_ratings.py` (EU vanish speed, site label codes, CarGurus rating bands; `03_results.json`, `eu_*.csv`, `cargurus_pricediff_by_rating.csv`)
- `scripts/04_cost_stack.py` (cost stack, score, break-even grid; `04_cost_stack_examples.json`, `04_breakeven_grid.json`)
- `scripts/05_false_positive_rules.py` (rule hit rates on the flags; `05_results.json`)
- `charts/residual_distribution.png`, `charts/error_by_cell_size.png`, `charts/eu_vanish_speed_by_residual.png`
- `data/` (downloaded parquet files; run scripts with `python -I <script> <data dir> <out dir>`; dependencies: pandas, pyarrow, numpy, scikit-learn, scipy, lightgbm, matplotlib)

## Sources

Primary or documented: [NBER w24306 Backus et al.](https://www.nber.org/papers/w24306.pdf) · [Dress, Lessmann, von Mettenheim arXiv 1707.02736](https://arxiv.org/pdf/1707.02736) · [Lessmann & Voß IJF 2017](https://ideas.repec.org/a/eee/intfor/v33y2017i4p864-877.html) · [Lacetera, Pope, Sydnor NBER w17030](https://www.nber.org/papers/w17030) and [digest](https://www.nber.org/digest/sep11/limited-attention-car-market) · [Busse et al. NBER w18820](https://www.nber.org/papers/w18820) · [Englmaier et al. Management Science 2018](https://econpapers.repec.org/RePEc:inm:ormnsc:v:64:y:2018:i:6:p:2754-2766) · [Cox Automotive used inventory Oct 2026](https://www.coxautoinc.com/insights/used-vehicle-inventory-october-2026/) · [CarGurus IMV help](https://cargurus.helpscoutdocs.com/article/10-what-is-imv) · [eBay Motors fees](https://www.ebay.com/help/selling/fees-credits-invoices/fees-selling-vehicles-ebay-motors?id=4127) · [Craigslist posting fees](https://www.craigslist.org/about/Help/posting_fees) · [NMVTIS providers](https://vehiclehistory.bja.ojp.gov/nmvtis_vehiclehistory) · [IC3 PSA 2018](https://www.ic3.gov/PSA/2018/PSA180117) · [MN AG online car scams](https://ag.state.mn.us/Consumer/Publications/OnlineCarSalesScams.asp) · [WA RCW 46.70.115](https://lawfilesext.leg.wa.gov/law/RCWPDF/RCW%20%2046%20%20TITLE/RCW%20%2046%20.%2070%20%20CHAPTER/RCW%20%2046%20.%2070%20.115.pdf) · [Texas Comptroller motor vehicle tax](https://comptroller.texas.gov/taxes/motor-vehicle/sales-use.php) · [CraigslistBargains arXiv 1808.09637](https://arxiv.org/pdf/1808.09637.pdf) · dataset cards linked in section 7.

Reported (second-hand, check before relying on them): Consumer Reports haggling survey (via search summary) · [KBB shipping costs](https://www.kbb.com/car-advice/costs-shipping-vehicle) · reconditioning figures ([Auto Dealer Today](https://www.autodealertodaymagazine.com/articles/pushing-your-used-vehicle-department), [vAuto](https://www.vauto.com/resources/a-miss-that-matters-with-customer-vehicle-acquisitions/), [Byrider FDD](https://www.fdd.ninja/brands/byrider/2025/median_reconditioning_expense_stores_first_quartile_2)) · [Bring a Trailer / Cars & Bids fees](https://theautopian.com/cars-bids-raises-its-buyer-fees-post-layoffs-to-match-bring-a-trailer) · Copart fee calculators · [NADA curbstoning](https://nada.org/nada/press-releases/nada-supports-efforts-protect-car-buyers-stopping-curbstoning) · CarGurus 2011 price-drop study and iSeeCars days-to-sell (search summaries) · [eBay misspelling anecdotes](https://www.nbcdfw.com/news/tech/looking-for-an-ebay-deal-trying-misspelling-it/2116164/?amp=1) · [BillOfSaleNow private-sale tax survey](https://billofsalenow.com/reports/2026-state-survey) · [pre-purchase inspection costs](https://www.cars.com/articles/what-is-a-pre-purchase-car-inspection-425469).
