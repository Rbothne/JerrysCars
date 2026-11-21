# 09. Which cars are good value, and how far to trust the answer

Measured on the catalogue of 2026-11-21: 3,605 cars for sale on the page, 1,899 of them Carvana's.
The code is `cartrack/value.py`; the experiments are in `research/_scratch/scoring/`.

## What the data can support

Every car has year, make, model, mileage and VIN; 99% have trim and body, 91% the driven wheels. No listing
states condition, accident history or title status, and none of the 19 dealers publishes them.

| Field | Filled | Used for |
|---|---|---|
| Year, make, model, mileage, price, VIN | 100% | filters, value |
| Trim, body | 99% | filters (body), value |
| Drive | 91% | filter, value |
| Fuel (listing), hybrid or electric (VIN decode) | 99.8% | filter, value |
| Cylinders, litres, weight class (VIN decode) | most | value |
| Dealer's distance from home | 59% | shown; not a filter, because the hand-kept dealers have no map position |
| Transmission | 77% | not used: 53 manuals in 3,605 cars |
| Title status, condition | 0% | nothing |

398 models are on the page; 173 of them have five or more cars, and those hold 3,204 of the 3,605.

## The judgement

`typical` is the lower of two estimates, so a car is called cheap only when both agree:

1. A ridge regression of log price on age, mileage, make, model, trim words, body, drive, fuel, engine size
   and weight class, each car priced by a fit that left it out (five folds).
2. The median asking price of the same model within two years and 30,000 miles, each neighbour moved to the
   car's own year and mileage by the regression's age and mileage slopes only.

A car with fewer than three such neighbours is not judged. The page marks a car when it asks a tenth or more
under `typical`.

## How good it is

| Measure | Result |
|---|---|
| Cars judged (three or more neighbours) | 2,470 of 3,605 |
| Typical against the asking price, median car | 6.2% apart |
| The same, 80th centile | 13.7% apart |
| Regression alone, cross-validated, every car | 7.1% median |
| Regression alone, cars priced under $10,000 | 23% median, and 21% too high |
| Cars marked a tenth or more under | 141 (100 on local lots, 22 under $10,000) |

Carvana publishes a KBB figure for each of its own cars, which gives an outside check on 1,372 judged cars:
53% of them ask less than KBB; of the 41 the judgement marks, 61% do. The mark carries some signal and not
much. It is a reason to look at a car.

Things seen while checking the top of the list:

- The first version took its second estimate from the regression too. A 2026 Tacoma SR at $36,590 was called
  typical at $54,600, though no similar Tacoma asked over $43,000, because "SR" is a dear trim on Nissans.
  Taking the second estimate from the neighbours' own prices removed it (257 marks became 141).
- Cheap cars at the top are often sold as-is. The Jim Keras stores photograph some with "Wholesale to the
  public. Sold AS IS. No warranty, no financing available", which no data field carries.
- Independent lots sit about 10% under the regression as a group (Victory Auto 14%, Street Cars 11%, Peck
  Daniel 10%), which may be price or may be condition.

## Not done

- Nothing for the 1,135 cars without three neighbours.
- No net figure after tax, title and repairs, and nothing about how fast a model sells: both need sold
  prices or the catalogue's own gone-dates, which take weeks to build up.
- No distance filter until the hand-kept dealers have map positions.
