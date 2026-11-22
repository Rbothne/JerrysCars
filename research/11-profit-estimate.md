# 11. What buying a car and reselling it privately would leave

Worked 2026-11-21. Research only: nothing in the product was changed. Local figures come from the page data
as built at 2026-11-21T22:02 (3,913 cars: 1,949 Carvana, 1,693 on local lots, 271 private) and from the 186
impound lots the catalogue held that evening (the sales of 11/11 and 11/18). A copy of both is in
`research/_scratch/profit/cap/`, and every script named below is in `research/_scratch/profit/`.

Labels: TESTED = computed here from the local files. DOCUMENTED = read in a primary source, with its address
and date. REPORTED = second-hand (a search extract, a news report, a trade site). "My estimate" = neither.

## Recommendation

### The short answer

1. A figure can be built, and its arithmetic is simple. Its cost side is known to within about $200. Its
   resale side is not: for a single car the resale guess is good to about a quarter either way, which is
   several times the margin anyone reports making on a cheap car ($500 to $1,500, note 05).
2. Under honest defaults the figure is **negative on almost every car in the catalogue today** (TESTED,
   `spread.py`): 0 of 2,510 judged dealer cars come out above zero, and 1 of the 19 private cars that could
   carry a figure, and that one asks 35% of what dealers ask, which is more likely a fault or a bait advert
   than a bargain. That is the true state of things: a car bought at its asking price and resold at a
   private seller's price loses the tax, the costs and the haggle. So show the figure as a range, and show
   beside it the price to pay that would leave a chosen sum. The second number is the useful one.
3. For an impound lot, show no resale figure before the sale. No lot states mileage, keys, whether it runs,
   or its title history, and the bidders who walked the lot paid a median 11% of what dealers ask for the
   same model (TESTED, 17 lots). Show what a bid costs all-in and what the car must sell for to get the
   money back.

### (a) A car from a private seller (and, unchanged, a car from a dealer)

    resale  = D x k x (1 - g)
    out     = P + tax(P) + F + W + L + H
    left    = resale - out
    range   = the same with k at 0.57 and at 1.03

| Term | What it is | Per car, or assumed | Default | Source and label |
|---|---|---|---|---|
| `P` | what is paid: the asking price (with the dealer's stated fee, as `price` already has it) | per car | the asking price, no haggle | the card. The owner may set a haggle `b`; the Consumer Reports median is 8% off (REPORTED, note 04) |
| `tax(P)` | Tennessee sales tax, `cost.tennessee_tax` | per car | 7% + 2.75% of the first $1,600 + 2.75% of the next $1,600 | DOCUMENTED, County Clerk Sales and Use Tax Manual, June 2025 |
| `D` | what dealers ask for a car like it: the median asking price of **dealer** cars of the same model within 2 years and 30,000 miles, each moved to this car's year and mileage. Needs 3 or more | per car, computed | - | TESTED method (`pairs.py`). Not the card's `typical`: see "Resale evidence" |
| `k` | a private seller's asking price as a share of `D` | assumed | **0.75**; range 0.57 to 1.03 | TESTED: median and quartiles over 52 private cars set against 183 dealer cars |
| `g` | given away between asking and selling | assumed | **0.08** | REPORTED: Consumer Reports survey median, all seller types, national |
| `F` | title and plate at the Shelby County Clerk | assumed | **$180** (title and a new plate in Memphis); $20 when a plate he already holds is moved over | part DOCUMENTED (other counties' schedules), part REPORTED; the Shelby clerk's own schedule could not be read |
| `W` | getting it ready: a check before buying, a detail, small parts | assumed | **$500**; range $150 to $1,500 | my estimate from REPORTED prices |
| `L` | advertising it | assumed | **$5** | DOCUMENTED: Craigslist, $5 a post for cars by owner; Facebook Marketplace free (REPORTED) |
| `H` | holding it: a month's insurance | assumed | **$60** | my estimate (note 04 used the same) |

Not counted, and the card must say so: repairs beyond `W`, fetching the car, his time, and income tax on a gain.

**The price to pay.** For a sum `T` he wants left (default $1,000): `pay = (resale - T - F - W - L - H - 88) / 1.07`
when that comes to more than $3,200 (the $88 is the two capped slices of tax). Up to $3,200 the tax is a flat
9.75%, so `pay = (resale - T - F - W - L - H) / 1.0975`.

### (b) An impound lot

    paid        = B x 1.10 + 10              (x 1.04 if paid by card)
    out         = paid + tax(paid) + F + W + L + H
    break-even  = out                         (asking price that gets it: out / (1 - g))
    left        = S - out                     only once he has typed in S, what he expects it to sell for

| Term | What it is | Per car, or assumed | Default | Source and label |
|---|---|---|---|---|
| `B` | the bid | per lot (current bid) or typed in | - | the lot |
| premium, fee, card | 10%, $10 an item, 4% more by card | per auction | as stated | DOCUMENTED: Venture Auctions' terms of 07-01-2026 (note 10); now in `sources.json` |
| `tax(paid)` | sales tax, paid at the clerk when the car is titled | per lot | on bid + premium + fee | the rate is DOCUMENTED; **whether the premium is in the base is not settled**. Taxing the bid alone lowers it by 9.75% of the premium: $6.58 on a $575 bid |
| `F` | title and plate | assumed | $180 | as above. No extra fee for titling on the city's bill of sale was found |
| `W` | tow off the lot, a key, a battery, tyres, a detail, and whatever is wrong | assumed | **$1,500**; range $300 to more than the car is worth | my estimate from REPORTED prices; the least certain number in this note |
| `L`, `H` | as above | assumed | $5, $60 | as above. The odometer statement can take two weeks by post, so one month is the least |
| `S` | what it will sell for | typed in by the owner after the Tuesday preview | none | see "When to show no figure" |

**The most to bid** for a sum `T` left, when the answer is under $2,900 (so that `paid` is under $3,200 and the
tax is a flat 9.75%): `B = ((S - T - F - W - L - H) / 1.0975 - 10) / 1.10`.

### What the card should say

A private or dealer car, when a figure can be shown (numbers from example 1):

> **Buy at $4,850 and resell privately: about $1,800 short** (somewhere between $2,800 short and $200 short).
> To have $1,000 left you would need to buy it for about $2,300.
>
> A rough guide, not a forecast. Nobody has seen this car. The resale price is worked from what 3 dealers ask
> for similar cars, less 25% because private sellers ask less, less 8% for haggling. Half of cars land outside
> the range. Counted: sales tax $428, title and plate $180, clean-up $500, advert $5, a month's insurance $60.
> Not counted: repairs, fetching it, your time, income tax.

Rules for the wording:

- Lead with the range's meaning in words when it crosses zero: "could go either way", never a green number.
- Round to the nearest $100. A figure given to the dollar reads as a promise.
- Say "short" and "left", not "loss" and "profit". Say how many dealer cars the resale price rests on.
- Show every assumption with its value, and let him change each one (`k`, `g`, `F`, `W`, `L`, `H`, `T`, the
  haggle). A changed assumption should show as changed.
- Put the same sentence on every card: "Nobody has seen this car."

An impound lot (numbers from example 4):

> **At a bid of $575 you pay $642.50** (10% premium and $10 fee; $668.20 by card). With sales tax ($63), title
> and plate ($180), and a guess of $1,500 for a tow, a key, a battery, tyres and a clean-up, **it has to sell for
> about $2,500 to get your money back.**
>
> No resale figure is given: the sale states no mileage, no keys, no title history, and not whether it runs.
> Dealers ask $6,900 to $17,990 for a 2016-2020 Altima (9 cars) and those run. Lots at this sale went for a
> median $575 on 11/11 and 11/18.

### When to show no figure at all

| Case | Why | How many today |
|---|---|---|
| Fewer than 3 dealer cars of the model within 2 years and 30,000 miles | no `D` | a figure would show on about 20 of the 218 clean-title private cars (TESTED) |
| Title not clean, or a caution in the seller's own title ("needs work", "as-is", "not running") | the page already withholds `typical` for these; the repair is the whole question | 53 private cars with another title status, 6 with a caution |
| Asking under 40% of `D` | below the 10th centile (0.38) of private asking prices. Say "priced far under the others: find out why first" in place of a figure, because the formula prints its largest numbers on exactly these | 1 of the 19 eligible |
| No mileage, or not an ordinary car or light truck (buses, box vans, pre-1995) | `D` means nothing | 53 private cars lack model, mileage or price |
| An impound lot before he has seen it | see (b) | all lots |

Where `D` is under $10,000 the figure may still be shown, but that is where the value judgement is weakest (the
regression is 23% out at the median there, note 09, and only 21 dealer cars under $10,000 are judged at all). The
card should say "few similar cars to go by" on those, and the break-even line matters more than the figure.

## The cost side

### Sales tax

| Question | Answer | Label and source |
|---|---|---|
| Is a private purchase taxed? | Yes. "Occasional and isolated sales of motor vehicles ... are subject to sales and use tax"; the exception is a sale between spouses, siblings and lineal relatives | DOCUMENTED: Tennessee Department of Revenue, *County Clerk Sales and Use Tax Manual for Automobiles & Boats*, June 2025, p. 4, `https://www.tn.gov/content/dam/tn/revenue/documents/tax_manuals/june-2025/County-Clerk-Tax-Manual.pdf`, read 2026-11-21 (29 pages, text extracted with `pdftotext`) |
| On what amount? | "the total amount of consideration received by the seller". Document and prep fees are in it; a title fee listed apart is not | DOCUMENTED, same manual, pp. 5-6 |
| At what rate? | 7% state on all of it; the local rate (2.75% in Memphis) on the first $1,600; 2.75% state single-article tax on the next $1,600. This is `cost.tennessee_tax`: $97.50 on $1,000, $427.50 on $4,850, $1,348 on $18,000. Up to $3,200 it is a flat 9.75% of the price | DOCUMENTED, same manual, pp. 17-20 (worked examples); TESTED against `tests/test_cost.py` |
| A car bought far under book value | Under 75% of the value in a pricing guide, seller and buyer must sign the Affidavit of Non-Dealer Transfer. Tax is then due on what was actually paid. Without the affidavit or an appraisal, "use tax is due on 100% of the vehicle's fair market value" | DOCUMENTED, same manual, p. 24. **This bites exactly on the cars the tracker marks as cheap**: get the seller's signature on the affidavit at the sale |
| Is the tax credited or due again at resale? | Neither. "Each time there is a transfer of title to a motor vehicle, the transaction is subject to sales and use tax." He pays it when he titles the car; his buyer pays it again on the resale price at the buyer's own clerk. He collects nothing and gets nothing back | DOCUMENTED, same manual, p. 4. That the buyer pays at titling is DOCUMENTED in note 07 |
| At the impound auction: on the hammer price, and on the premium? | Tax is not mentioned in the auction's terms (note 10), so it is paid at the clerk on titling like any other purchase. **Whether the 10% premium and $10 fee are in the base was not found in any Department of Revenue text.** The manual's definition (charges "necessary to complete the sale" are part of the price) points to yes. My estimate: yes; the formula takes the dearer reading | The rate DOCUMENTED; the base my estimate. The Department's Sales and Use Tax Manual (June 2025 and August 2026 editions) answered 403 to a fetch |
| Does the 75% rule apply to a city bill of sale? | Not settled. A $575 car with a book value of $8,000 is far under 75%. If a clerk taxed book value, the tax ($648) would exceed the bid. The city's bill of sale states the price and the seller is a government, so I expect the price paid to stand | my estimate. Ask the clerk before the first purchase |

### Title, plate and wheel tax (Shelby County)

The Shelby County Clerk's site answered 403 and the state's fee pages answered 403, so no Shelby schedule was
read. What follows is built from two other county clerks' published schedules and from news reports.

| Item | Figure | Label and source |
|---|---|---|
| Title and a plate moved over from a car he has sold | **$17.50 to $20.50** | DOCUMENTED for Knox County ("Transfer License Plate $17.50", `knoxcounty.org/clerk/motorvehicle/`) and Rutherford County ("transferring plate and title is $20.50", `rutherfordcountytn.gov/vehicle-titles`), both read 2026-11-21. Tennessee plates stay with the owner, not the car (REPORTED, search extract of the Department of Revenue's plate page). Shelby's own figure not confirmed |
| Title and a new standard plate, before any local tax | **$43** | DOCUMENTED for Knox County: "Private Passenger License Plate $79.00" for a new or used vehicle, and "a $36.00 wheel tax". That the $79 holds the wheel tax and the title is my reading; it fits a state plate fee of $26.50 a year (REPORTED, search extract of the state's plate page), a clerk's fee, and a title at about $14 (REPORTED: a state notice of June 2022 raised the clerk's part from $5.50 to $8.50) |
| Shelby County wheel tax | **$75 a year** | REPORTED: raised by $25 from $50 in 2023 (Daily Memphian); a Knox County Commission presentation dated 28 February 2026 lists "Shelby County $75.00". A further $5 was proposed in May 2025; outcome not found. So $75 to $80 |
| City of Memphis registration fee | **$60 a year** | The fee and who collects it are DOCUMENTED (`memphistn.gov/treasury`: Ordinance 5912, collected by the County Clerk on non-commercial vehicles since 1 February 2025). The amount, raised from $30 to $60, is REPORTED (Daily Memphian) |
| So: title and a new plate, Memphis address | **about $180** ($43 + $75 + $60) | my estimate from the rows above |
| The same outside Memphis in Shelby County | about $120 | my estimate |
| Noting a lien | $11 | DOCUMENTED (Knox). Not needed for a cash purchase |

The wheel tax and city fee are paid once a year per plate, not per car. A man who moves one plate from car to car
pays them once and about $20 for each car after the first. The default of $180 is right for a first car and too
high for the rest. Note 04's "$150 title, transfer, temporary tags" was a guess for another state; $180 or $20
replaces it.

### Titling an impound car bought on the city's bill of sale

| Step | What is known | Label and source |
|---|---|---|
| What he is given | A paid invoice from Venture and "a bill of sale with odometer statement from the City". No title. The terms call these "wholly sufficient for titling purposes in Shelby County". The odometer statement is collected at City Hall, 125 N. Main, Room 546, Monday to Wednesday 9 am to 1 pm, or posted after two weeks | DOCUMENTED: the auction's terms of 07-01-2026 (note 10, section 5) |
| The law behind it | The buyer of an abandoned vehicle at a police sale "shall take title to the motor vehicle free and clear of all liens and claims of ownership, shall receive a sales receipt from the police department", and a title is issued on presenting it (Tenn. Code Ann. 55-16-106) | REPORTED: search extract of the 2019 code text. Justia and FindLaw would not give the page (403, and an index only) |
| The form | The buyer applies at his county clerk with a completed Certification of Sales Under Special Conditions (form RV-F1312101, "Abandoned Vehicle" box) and supporting papers | REPORTED: search extract of the Department of Revenue's abandoned-vehicle page; the page itself answered 403 |
| The cost | The same title and plate fees and the same sales tax as any purchase. No surety bond: that route (and the Certification of Ownership, form RV-F1310401, for vehicles worth $3,000 or less) is for a car with no paperwork at all | my estimate from the rows above. No extra fee was found, and none was ruled out |
| What title comes out | Whatever the state's record holds. "Impound auction items are NOT warranted against salvage title, prior flood damage history, odometer discrepancy, or ANY other preexisting title brands" | DOCUMENTED: terms. Every lot shows a full VIN, so a title-history check (about $10, note 04) can be bought before bidding |
| "FOR PARTS ONLY" lots | An invoice only; cannot be registered or resold as a car | DOCUMENTED: terms |
| Time | Not settled. He cannot sign over a title he does not yet hold, so the weeks it takes to arrive are weeks of holding | my estimate: allow a month |

### Getting a cheap car ready, and advertising it

| Item | Range | Label and source |
|---|---|---|
| Emissions or safety test | **None.** Memphis closed its inspection stations on 28 June 2013 and the county never tested outside the city | REPORTED: Commercial Appeal, 28-29 June 2013; a later local TV report says inspections are "a thing of the past for Shelby County". Not confirmed on a state page (403) |
| Check before buying | $100 to $250 for a mechanic's inspection; about $10 for a title-history report | REPORTED (note 04) |
| Full detail, inside and out | $150 to $300; one 2026 guide gives a $220 average for a sedan | REPORTED: trade and consumer sites, 2026 |
| Battery, fitted | $290 to $490 at a shop | REPORTED: The General (2026), ConsumerAffairs, GOBankingRates. Fitting one himself costs less; not sourced |
| Four tyres | $400 to $1,600 | REPORTED: Chime, December 2025 |
| A key for a car with none | $90 to $400 from a locksmith or dealer; more when the car's computer must be reset because every key is lost | REPORTED: consumer sites. Most impound lots have no key (DOCUMENTED, terms) |
| A tow across Memphis, about 10 miles | $100 to $160 | REPORTED: low-quality local pages. A car that will not drive must leave the impound lot on an approved tow truck (DOCUMENTED, terms) |
| Advert | $5 for each Craigslist post ("Cars/trucks, RVs, and motorcycles by-owner in the US-$5"); Facebook Marketplace free for local sales | DOCUMENTED: `craigslist.org/about/help/posting_fees`, read 2026-11-21; REPORTED for Facebook |
| A month's insurance | $60 | my estimate |

The defaults: $500 for a private car that runs (a check $110, a detail $220, small things $170) and $1,500 for
an impound lot (tow $125, key $200, battery $300, detail $220, the rest toward tyres or a fault). Both are my
estimates. Note 04's dealer-anchored figures ($600 to $1,500 by age, plus a quarter) are no better founded. This
is the term he should overwrite first, from his own receipts.

## The resale side

### Is "what similar cars ask" the right place to start?

It is the only place the catalogue can start today, and it is wrong in three known ways.

1. **It is dealers' prices.** 3,642 of the 3,913 cars are dealers', and a private seller's median car is a 2012
   with 145,000 miles asking $6,600, where the local lots' median car is a 2022 with 69,000 miles asking $25,000
   (TESTED). Of 146 dealer cars asking under $10,000, 21 are judged.
2. **It is asking prices.** Nothing in the catalogue is a sale. Every listing was first seen today, so no private
   listing has yet disappeared.
3. **On a private seller's card, `typical` is not a dealer figure and not a private one.** It is the lower of a
   regression and a neighbours' median, both fed by dealer and private cars together, and a private listing's
   empty fields act as a hidden private-seller term. On the 21 private cars that have both, the card's `typical`
   is a median 0.67 of what dealers ask for the like, from 0.54 to 1.05 (TESTED, `pairs2.py`). The 2018 Highlander
   in example 2 has `typical` $15,800 where ten dealers' cars put it at $23,300. So the formula computes `D` from
   dealer cars alone and applies the private seller's discount in the open, as `k`.

### Private sellers' asking prices against dealers' (TESTED)

Method (`pairs.py`, `pairs2.py`): the private cars on the page with a clean title, a make, model, mileage and
price, model year 1995 or later, $1,000 or more, each listed once: 161 cars. For each, the dealer cars of the same
model within 2 years and 30,000 miles, each dealer's price moved to the private car's year and mileage by the age
and mileage slopes of a regression fitted to dealer cars only (the method of `value.py`). The ratio is the private
asking price over the median of those.

| Measure | Private cars | Dealer cars behind them | Median ratio | Quartiles |
|---|---|---|---|---|
| All with at least one dealer car | 54 | 190 | **0.74** | 0.54 to 1.03 |
| Leaving out distress wording and odd vehicles | 52 | 183 | **0.75** (10th to 90th centile 0.38 to 1.18) | 0.57 to 1.03 |
| With 3 or more dealer cars | 19 | 142 | 0.86 | 0.68 to 1.04 |
| Within 60 miles of home | 25 | 60 | 0.71 | 0.53 to 0.80 |
| No adjustment for year and mileage | 54 | 190 | 0.67 | 0.50 to 0.99 |
| Tighter match, 1 year and 15,000 miles | 31 | 73 | 0.88 | 0.67 to 1.17 |
| Wider match, 3 years and 50,000 miles | 77 | 374 | 0.71 | 0.55 to 1.02 |
| A private-seller term in one regression over everything | 142 | all | 0.68 | - |

By what dealers ask for the car:

| Dealers ask | Private cars | Median ratio | Median gap in dollars |
|---|---|---|---|
| Under $10,000 | 17 | 0.73 | $2,575 |
| $10,000 to $15,000 | 18 | 0.65 | $4,578 |
| $15,000 and over | 17 | 1.03 | none (private asks $866 more) |

What this supports, and what it does not:

- A private seller around Memphis asks **about a quarter less than a dealer** for a car of the same model, age
  and mileage: 0.74, with a bootstrap 90% interval of 0.70 to 0.81 on the median.
- The discount sits on the cheaper cars. Where dealers ask $15,000 or more, private sellers ask the same. Where
  dealers ask less, private sellers ask $2,600 to $4,600 less. Seventeen or eighteen cars a band is too few to
  set `k` by band; it is why the single 0.75 is a little generous for the cars he would buy.
- **The spread is the finding.** Half of the cars lie outside 0.57 to 1.03. That spread is condition, trim,
  honesty and luck, none of which a listing states.
- It is not a like-for-like discount. A dealer's car has been cleaned and repaired and comes with financing; a
  private car has not. Some of the quarter is the car, not the seller. The data cannot split the two.
- 54 cars, one day, asking prices only. 23 of the 147 clean private cars have even one other private car of the
  same model to compare with, so private-against-private cannot be measured yet.

### Published figures

| Gap | Figure | Label, source, date |
|---|---|---|
| Asking to selling | A median $900 or 8% off the asking price, across franchise dealers, independents and private sellers; 7 buyers in 10 haggled | REPORTED: Consumer Reports haggling survey, as carried in note 04 (the page answered 403 then and was not retried) |
| Asking to selling, dealers | "$500 to $1,000 on a standard mass-market used car" | REPORTED: a 2026 advice page (CarTipsDaily), not a study |
| Private sale against a dealer's offer for the same car | Private sales "returned an average of $2,418 more than trade-in offers", 1,200 matched transactions | REPORTED: CarCheckerVIN, 26 February 2026 |
| The same, as a share | "usually 10-20%" | REPORTED: RealCarTips, last reviewed January 2026. No data cited |
| Private-party price against dealer retail | "roughly 10 to 20 percent below dealer retail"; one appraiser's worked car puts private-party 14% under retail ($16,698 against $19,412) | REPORTED, unsourced trade pages. **No audited figure was found.** CarGurus' own article on the subject (19 March 2025) gives no number |
| A dealer's margin and preparation | $1,400 to $2,100 gross a car, $600 to $1,500 reconditioning | REPORTED (notes 04 and 05) |

The published range (10% to 20% under dealer retail) is smaller than the 25% measured here. Two reasons fit both:
the guides compare the same car in the same condition, and their gap is nearer a fixed sum of dollars ($2,000 to
$3,600 of dealer margin and preparation) than a share, which is a quarter or more of a $7,000 car and a tenth of
a $25,000 one. The local dollar gap, $2,600 to $4,600 on cars dealers price under $15,000, agrees with that.

### What the auction's own prices say (TESTED, `auction2.py`)

- 180 lots sold at the two sales the catalogue holds. Hammer price: median $575, quartiles $500 to $800, 81% under
  $1,000, highest $7,200. Median model year 2008.
- For the 17 sold lots with 3 or more dealer cars of the same model within 2 years on the page, the buyer paid
  (bid, premium and fee) a median **11%** of the dealers' median asking price; quartiles 6% to 20%; 2 of the 17
  went above 30%.
- For the 31 lots with a private seller's car of the same model within 2 years, the buyer paid a median 22% of the
  private asking price.
- 4 cars that failed to sell on 11/11 sold on 11/18, within $300 of the first bid.
- No lot's VIN is among the cars for sale on the page yet.

Bidders can walk the lot on Tuesday; the page cannot. A price a tenth of the dealers' is their judgement of what
most of these cars are. A formula that put `D x k` beside a $575 bid would print $7,000 "left" on nearly every
lot and be wrong on nearly every one.

## How wide the figure is

`left` is a small difference between two large numbers, so the error of the resale side passes straight into it.

| Source of error | Size | Label |
|---|---|---|
| The value judgement against the asking price, all judged cars | 6.5% at the median car, 15% at the 80th centile, 23% at the 90th (note 09 gave 6.2% and 13.7% on the morning's catalogue) | TESTED, `valerr.py` |
| The same where `typical` is $10,000 to $15,000 | 11% at the median, 24% at the 80th centile (139 cars) | TESTED |
| The same under $10,000 | 23% at the median for the regression, and 21% too high (note 09); only 21 dealer cars are judged there | DOCUMENTED in note 09; TESTED count |
| The private seller's discount `k` | quartiles 0.57 to 1.03 around 0.75: 24% under to 37% over | TESTED |
| Asking to selling `g` | 8% is one national median; a private seller in Memphis may give 0% or 20% | REPORTED |
| Preparation `W` | $150 to $1,500 on a running car | my estimate |

Put together for a car dealers would ask $8,000 for: resale is 8,000 x 0.75 x 0.92 = $5,520. The quartiles of `k`
alone move that from $4,200 to $7,580, a band $3,400 wide, and half of cars fall outside it. A 15% error in `D`
moves it $830 either way on its own. The margin being looked for is $500 to $1,500. **The figure can sort cars
and rule cars out. It cannot say what one car will make.** An inspection is what narrows it, and the card
should say so.

## Worked examples (TESTED arithmetic, `examples.py`)

Defaults throughout: `k` 0.75, `g` 0.08, `F` $180, `W` $500 (lot: $1,500), `L` $5, `H` $60.

| | 1. 2016 GMC Terrain SLT | 2. 2018 Toyota Highlander | 3. 2017 Jeep Grand Cherokee Limited |
|---|---|---|---|
| Listing | Craigslist Memphis, East Memphis, 176,000 miles, clean title | Craigslist Memphis, 84,000 miles, clean title | Craigslist Little Rock, Jacksonville AR (120 miles), 135,000 miles, clean title |
| Asking `P` | $4,850 | $18,000 | $5,000 |
| Dealers ask `D` | $6,165 (3 cars) | $23,302 (10 cars) | $14,142 (5 cars) |
| The card's `typical` | $6,000 | $15,800 | $13,200 |
| Resale `D x 0.75 x 0.92` | $4,254 | $16,078 | $9,758 |
| Tax | $427.50 | $1,348.00 | $438.00 |
| Title, prep, advert, holding | $745 | $745 | $745 |
| Out | $6,022.50 | $20,093.00 | $6,183.00 |
| **Left** | **-$1,769** | **-$4,015** | **+$3,575** |
| With `k` at its quartiles | -$2,790 to -$181 | -$7,874 to +$1,988 | +$1,233 to +$7,218 |
| With `D` 15% out, `k` at 0.75 | -$2,407 to -$1,131 | -$6,427 to -$1,603 | +$2,111 to +$5,039 |
| Both at once | -$3,275 to +$696 | -$9,707 to +$5,300 | +$121 to +$9,228 |
| It breaks even if it sells for | $6,022: 98% of what dealers ask | $20,093: 86% | $6,183: 44% |
| Price to pay to have $1,000 left | about $2,300 | about $13,300 | about $7,400 |
| What the card should show | the range, "short"; the price to pay | "could go either way"; the price to pay | **no figure**: it asks 35% of what dealers ask. "Priced far under the others: find out why first" |

Example 3 is the trap. It is the only car in the catalogue with a positive figure, and its listing is the least
believable one: a five-word title, a third of the going price, two hours away.

**4. Impound lot 25 of the 11/18 sale: 2018 Nissan Altima, VIN 1N4AL3AP4JC123010, hammer $575 after 13 bids.**

| Line | Amount |
|---|---|
| Bid | $575.00 |
| Premium 10% and $10 fee | $67.50, so $642.50 in cash ($668.20 by card) |
| Sales tax on $642.50 (on $575: $56.06) | $62.64 |
| Title and plate | $180.00 |
| Tow, key, battery, clean-up, faults (guess) | $1,500.00 |
| Advert and a month's insurance | $65.00 |
| **Out, and so the sale price that gets it back** | **$2,450** (asking $2,660) |
| With the prep guess at $300, and at $3,000 | $1,250, and $3,950 |
| Dealers ask for a 2016-2020 Altima | $6,900 to $17,990, median $13,993, 9 cars, their median mileage 96,000 |
| If it ran, had a clean title and that mileage | resale $9,655, left $7,205 (quartiles $4,900 to $10,800) |
| If it is scrap worth $400 | $2,050 short |

The bid was 4.6% of what dealers ask for the model. Between "$7,200 left" and "$2,050 short" the page has no
evidence at all, which is why the card should stop at the break-even line.

## What would most improve it

1. **His own ledger.** Five to ten cars bought and sold, with what was paid, each receipt, the sale price and the
   days it took, would replace `W`, `g`, `H` and in time `k` with his own numbers. Nothing else is as direct.
2. **The tracker's own record of cars that disappear.** For each private listing that goes: its last asking
   price, its cuts, and its days listed. The last price is a ceiling on the sale price, the cuts trace how far a
   seller came down (a local `g`), and the days give the holding time. It needs weeks of daily reads; it has one
   day. Note 04 section 2 sets out the method.
3. **Every finished impound sale.** The auctioneer's site keeps 31 sales since 6 May 2026, about 2,000 hammer
   prices with a VIN each (note 10); the catalogue holds two. With them the page can say what this model and age
   has gone for (a floor, and the bidders' own view of condition) and how often a car comes back unsold. The
   working tree already sets "what such cars fetched before" beside a coming lot.
4. **Lot VINs that reappear for sale.** A VIN sold at the impound sale that later shows on Craigslist or a lot is
   a real purchase price beside a real asking price: the gross spread somebody else is working to. None has
   matched yet (TESTED). Only 29 of the private listings give a VIN; every dealer listing does.
5. **More private listings.** `k` rests on 54 cars. Facebook Marketplace (note 07 puts it ahead of Craigslist
   here) would let resale be taken from private asking prices directly, with no `k` at all.
6. **A dealer-only `D` in the build**, with the count behind it, so a private card stops showing a `typical` that
   is two-thirds of the dealers' figure for reasons the card does not state.
7. **What he sees at the preview**, typed in per lot: starts or not, key or not, odometer. Three fields turn (b)
   from a break-even into an estimate.

## What could not be settled

| Question | Why not | What would settle it |
|---|---|---|
| Is the auction's premium inside the taxed price? | No Department of Revenue text read says. Its Sales and Use Tax Manual and its auctioneers' webinar page answered 403 | the clerk's receipt on the first car, or a call to the Department (the difference is under $10 on most lots) |
| Does the clerk tax an impound car on what was paid or on book value? | the 75% rule is written for sales between individuals | ask the Shelby County Clerk before bidding |
| Shelby County's own fees: title, plate, plate transfer, wheel tax ($75 or $80), the city's $60 | `shelbycountytn.gov` answered 403; `ctas.tennessee.edu` 503; `tn.gov` fee pages 403; the state's county-clerk tax guide reset the connection | one receipt, or the clerk's counter |
| How long an impound car's title takes, and what brand it carries | not in the terms; the state page answered 403 | the first purchase; a title-history report on the VIN before bidding |
| The current text of Tenn. Code Ann. 55-16-106 and whether the 2024 towing act changed it | Justia 403; FindLaw gave an index | the General Assembly's code site |
| What a private seller in Memphis sells for, as against asks | no sale prices exist in the catalogue | item 2 above |
| How much of the 25% is the seller and how much the car | no listing states condition | his own ledger |
| How long a private sale takes here | one day of history | item 2 above |
| Every preparation cost | consumer sites only | his receipts |
| That no emissions test is needed | news reports from 2013 and a later local report; no state page read | the clerk |
| Income tax on a gain | not looked into | his accountant |

Refused or failed, recorded and left: `tn.gov` (abandoned-vehicle procedure page, both Sales and Use Tax Manual
editions, `SalesUseTaxMotorVehicles.pdf`, the abandoned-vehicle procedures PDF), `revenue.support.tn.gov`,
`shelbycountytn.gov`, `ctas.tennessee.edu`, `law.justia.com`, `mtas.tennessee.edu` (404), `putnamcountytn.gov`
(404), `support.marketplace.autura.com` (TLS failure). No block was worked around.

## Files

- `research/_scratch/profit/pairs.py`, `pairs2.py`: private against dealer asking prices.
- `valerr.py`: how far `typical` sits from asking prices, by band.
- `auction2.py` (the catalogue's 186 lots) and `auction.py` (the 78 lots saved by note 10).
- `examples.py`: the four worked examples. `spread.py`: how many cars come out above zero.
- `cap/cars_snapshot.json`, `cap/lots_snapshot.tsv`: the data all of the above was run on.

## Sources

- Tennessee Department of Revenue, County Clerk Sales and Use Tax Manual for Automobiles & Boats, June 2025:
  https://www.tn.gov/content/dam/tn/revenue/documents/tax_manuals/june-2025/County-Clerk-Tax-Manual.pdf
- Knox County Clerk, motor vehicle fees: http://knoxcounty.org/clerk/motorvehicle/
- Rutherford County Clerk, vehicle titles: https://rutherfordcountytn.gov/vehicle-titles
- Knox County Commission presentation on the wheel tax, revised 28 February 2026:
  https://public.destinyhosted.com/knoxdocs/2026/AGN/20260304_5035/17592_CC-WheelTaxRepeal-CommissionPresentation-rev022826.pdf
- City of Memphis Treasury (Ordinance 5912): https://www.memphistn.gov/treasury
- Daily Memphian on the city fee and the county wheel tax: https://dailymemphian.com/article/49493 ,
  https://dailymemphian.com/section/metroshelby-county/article/51886/shelby-county-mayor-lee-harris-wants-lower-county-property-tax-rate
- Craigslist posting fees: https://www.craigslist.org/about/help/posting_fees
- CarCheckerVIN, trade-in against private sale: https://www.carcheckervin.com/blog/trade-in-vs-private-sale
- RealCarTips: https://www.realcartips.com/selling/012-pricing-guides-not-accurate.shtml
- CarGurus, why cars for sale by owner cost less: https://www.cargurus.com/Cars/articles/why-cars-for-sale-by-owner-cost-less-than-cars-from-dealerships
- Venture Auctions' terms of sale: `research/_scratch/routing/impound/cap/va_auction_5362_terms.txt` (note 10)
