# Tennessee re-grounding

Written 2026-11-20. Reports 01 to 06 used DC/Maryland/Virginia as the working region. The locality is Tennessee. This note records what changes. City or home point within Tennessee: not yet given.

Labels: TESTED (run this session), DOCUMENTED (state source read via search), REPORTED (second-hand).

## What changes

| Topic | DC/MD/VA assumption in reports 01 to 06 | Tennessee | Label |
|---|---|---|---|
| Sales without a dealer licence | MD: 3 or more offered in 12 months presumes dealer. VA: 5 or more | Up to 5 used vehicles in 12 months, each registered and titled in his own name. More than 5 requires a licence | DOCUMENTED (Tenn. Comp. R. & Regs. 0960-01-.20; Motor Vehicle Commission dealer page) |
| Tax on each purchase | MD 6.5%, VA 4.15% titling tax | 7% state on the full price, plus local rate (1.5% to 2.75% by locality) on the first $1,600, plus 2.75% state single-article tax on $1,600 to $3,200. Paid at the county clerk when titling | DOCUMENTED (TN Department of Revenue) |
| Dealer licence | MD/VA/DC figures in reports 05 and 06 | Surety bond of at least $50,000 covering the two-year term. Permanent established place of business; private residences not allowed. Application fee quoted as $400 and as $600 on different state pages | DOCUMENTED, fee unreconciled |
| Craigslist sites | washingtondc | nashville, memphis, knoxville, chattanooga tested. Other Tennessee sites (tricities, clarksville, cookeville, jackson) not tested | TESTED for four |
| Auction priority | GovDeals raised because DC impounds sell there | Not established for Tennessee. Needs checking | open |

## Purchase tax, worked

Because the exemption only covers vehicles titled in his own name, every unlicensed flip is titled and taxed.

| Purchase price | State 7% | Local on first $1,600 (at 2.75% maximum) | Single-article 2.75% on $1,600 to $3,200 | Total | Share of price |
|---|---|---|---|---|---|
| $3,000 | $210 | $44 | $38.50 | $292.50 | 9.8% |
| $6,000 | $420 | $44 | $44 | $508 | 8.5% |
| $10,000 | $700 | $44 | $44 | $788 | 7.9% |

Title and registration fees are extra and not included. The break-even discounts in report 04 were computed before the locality was known and need rerunning with these rates.

## Craigslist volume snapshot (TESTED, 2026-11-20)

One plain request per search page, results counted in the static HTML. The page shows at most about 360, so 362 means "at least".

| City | By owner (cto) | By dealer (ctd) |
|---|---|---|
| Nashville | 261 | 362 (at cap) |
| Memphis | 121 | 109 |
| Knoxville | 167 | 302 |
| Chattanooga | 74 | 93 |

All eight requests returned 200. Counts may include nearby-area results; treat them as a rough size indicator.

## Implications

- Private-seller volume on Craigslist is thin: about 620 by-owner listings visible across the four largest cities. Facebook Marketplace carries more weight here than in the DC plan.
- Thin local comparables. Fit the expected-price model on national data (the current Kaggle Craigslist set) and use Tennessee listings for the local adjustment.
- Five flips a year is the working ceiling without a licence. A licence needs a commercial location, which is the main cost.
- The dealer-platform readers in report 02 carry over unchanged. Dealer discovery (OpenStreetMap plus DNS lookup) needs rerunning for Tennessee.

## Memphis

Home area confirmed as Memphis or surrounding area. The metro spans three states: Tennessee, Mississippi (DeSoto County: Southaven, Olive Branch) and Arkansas (West Memphis). A car bought in any of them is still titled and taxed in Tennessee.

### Craigslist around Memphis (TESTED, 2026-11-20)

| Site | By owner (cto) | By dealer (ctd) |
|---|---|---|
| memphis | 121 | 109 |
| northmiss | 43 | 16 |
| jacksontn | 22 | 17 |
| jonesboro | 13 | 15 |
| littlerock (about two hours away) | 85 | 241 |

About 200 by-owner listings within the Memphis area proper. All requests returned 200. Craigslist is a minor source here, cheap to collect but not the backbone.

### City of Memphis auctions (DOCUMENTED, memphistn.gov; not probed)

- Weekly impounded-vehicle auction, open to the public as well as dealers. Typically Wednesdays, online through Venture Auctions on HiBid. Registration closes 9:00 AM, webcast starts 9:30 AM Central.
- Auction list posted Monday evening, vehicle preview Tuesday.
- Quarterly surplus vehicle and equipment auction, also through Venture Auctions.
- The city page says "Updated: January 2026" and its newest list was for 4 November 2026. Confirm the schedule on the live page.
- Whether HiBid exposes the catalogue and prices realised to a plain request has not been tested. If it does, this is both a weekly sourcing channel and a local sold-price source.
- Shelby County government surplus: nothing found yet.

### Memphis tax and fees

- Memphis local sales tax rate is 2.75% (TN Department of Revenue notice, effective 1 January 2020), so the worked table above applies as written: $44 local on the first $1,600.
- Shelby County wheel tax quoted as $75 for automobiles in 2026 (REPORTED via CTAS; not confirmed).

### What Memphis changes in the plan

- Sources in priority order: Facebook Marketplace (extension in his session), the weekly city impound auction, dealer sites, then Craigslist.
- With so few local private listings, the price model must be fitted nationally and adjusted locally.
- Next probes: HiBid / Venture Auctions catalogue and results; dealer discovery for the Memphis metro across the three states; Copart and IAAI Memphis yards.

## Still to check for Tennessee

- Search radius around Memphis.
- Whether the rule text (Justia copy current to April 2024) has changed.
- Current dealer application fee ($400 or $600).
- County local tax rate for his county.
- Where Tennessee state, county and city surplus and impound vehicles are sold.
- Mortgage licensing in Tennessee, if the contract mortgage work in report 05 is pursued.

## Sources

- https://www.law.cornell.edu/regulations/tennessee/Tenn-Comp-R-Regs-0960-01-.20
- https://www.tn.gov/commerce/regboards/mvc/license/get/dealer.html
- https://tn.gov/content/dam/tn/revenue/documents/countyclerks/SalesUseTaxMotorVehicles.pdf
- https://tn.gov/revenue/taxes/sales-and-use-tax/single-article-special-tax-rates.html
- https://www.tn.gov/content/dam/tn/commerce/documents/regboards/mvc/forms/Minimum-Dealer-Requirements.pdf
- https://codes.findlaw.com/tn/title-55-motor-and-other-vehicles/tn-code-sect-55-17-111/
