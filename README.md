# CraigsCars

A catalogue of used cars for sale around Memphis, Tennessee, with their price history, and a page that shows them.
It reads dealers' own websites and Craigslist's for-sale-by-owner listings. The dealers are the yardstick; the
cars worth finding are the ones priced well under them.

Python standard library only. Tested with Python 3.14 and Node 26.

## What is here

| Piece | File | What it does |
|---|---|---|
| Dealer discovery | `discover.py`, `cartrack/dealers.py` | Dealers within the radius of the home point, and the website platform each runs on. Writes `dealers.json`. |
| Readers | `cartrack/readers/` | One per dealer platform: DealerOn, AutoRevo, Dealer Car Search, Team Velocity, DealerFire, Dealer Alchemist, DealerCenter, Carsforsale.com, Carvana. Each gives back listings and whether it saw the whole inventory. |
| Other sources | `cartrack/sources/` | Readers for places that are not one dealer's website, listed by hand in `sources.json`. Craigslist by owner is the first: one search page a run, and each listing's own page once. |
| Naming | `cartrack/identify.py` | Make and model for a listing that gives them only in the seller's words ("chevy silverado lt"), matched against the models the catalogue knows from decoded VINs. |
| Listing record | `cartrack/listings.py` | `make_listing()`: the one record every reader hands back. `None` means the source does not say. |
| Catalogue | `cartrack/catalogue.py` | One SQLite file, `data/catalogue.db`: listings, price points added only on change, seen-spans, gone and back, VIN decodes, dealers. |
| VINs | `cartrack/vin.py` | Check digit, and identity from NHTSA's free vPIC service, 50 VINs a request. A decoded VIN's identity wins over the dealer's wording. |
| Value | `cartrack/value.py` | What cars like each one usually ask, from the other cars in the catalogue: the lower of a price model and the car's nearest neighbours. How far to trust it is in `research/09-value.md`. |
| Cost | `cartrack/cost.py` | Tennessee sales tax on a vehicle, for the total shown under each price (price, the dealer's stated fee, tax). Title and registration are not in it. |
| Build | `build.py` | Reads every source and every dealer that has a reader, updates the catalogue, decodes new VINs, names the listings that have only a seller's words, judges value, writes `site/data/cars.json`. |
| Page | `site/` | Plain HTML and JavaScript, no build step. `logic.js` holds the search, filtering and ordering. Search reads title, make and model, ignores punctuation ("crv", "f150", "f 150"), knows a few nicknames ("chevy", "vw") and, for a word that matches no car, falls back to names one slip away ("camery"). Filters: sold by (private sellers or dealers), make, model, price, year, mileage, body, drive, fuel, source, local lots only, price cuts only, below typical price only, no branded titles. Sorts by one field (value, price, price cut, year, mileage, miles a year, days listed), ascending or descending, and opens with the cars furthest under similar ones first. |
| Schedule | `.github/workflows/update.yml` | Twice a day on GitHub Actions: build, keep the catalogue on the `data` branch, publish `site/` to GitHub Pages. |
| Fetching | `cartrack/fetch.py` | Plain HTTP with retries and a per-site delay. Sends the tracker's own name. |

## Run

    py discover.py                              # rewrites dealers.json and the catalogue's dealer table
    py build.py                                 # reads the sources and dealers, updates data/catalogue.db and site/data/cars.json
    py -m http.server 8000 --directory site     # then open http://localhost:8000
    py -m unittest discover -s tests -t .       # 297 Python tests
    node --test tests/js/logic.test.mjs         # 48 page-logic tests

## Publishing the page

Published at https://rbothne.github.io/jerryscars/ from https://github.com/Rbothne/jerryscars. The page's address
follows the repository's name letter for letter, capitals included: when the repository was renamed from
JerrysCars to jerryscars on 2026-11-21, the old page address began answering 404. The "Track cars"
workflow runs twice a day, on a push to `main`, and by hand from the Actions tab. GitHub Pages is on with
"GitHub Actions" as its source; a workflow cannot turn that on itself, so a new repository needs it set once
in Settings, under Pages.

From GitHub's servers on 2026-11-21 the build read 19 of 19 dealers. A dealer that refuses is reported in the
run log and keeps its last known cars.

## Configuration

- `area.json`: home point and radius. Memphis, 60 miles.
- `dealers-seed.json`: hand-kept dealers that OpenStreetMap lacks. Add a line to add a dealer, then run `py discover.py`.
- `dealers.json`: written by discovery and read by the build. Committed, so the scheduled build does not rediscover.
- `sources.json`: hand-kept places that are not a dealer's website. `kind` names the reader, `site` the Craigslist city, and `floor` how far the place's listings may thin out between two reads before the read is taken as broken (0.5 for Craigslist, where listings come and go faster than on a lot; 0.8 otherwise).

## Craigslist (seen 2026-11-21, from a home connection)

- `https://memphis.craigslist.org/search/cto` answered the tracker's own name with 120 by-owner results in the page. Each result's address ends in a key that did not change between two reads minutes apart; that key is the listing's id here. Whether it lasts the life of a listing has not been watched yet: if it does not, every listing will look new each day.
- Each listing's page was read once (120 requests, three seconds apart) and gave a year and a posting time for all 120, and a VIN for 8. Later runs ask only for listings they have not read, so a normal run is one request plus a few.
- That first build put 101 of the 120 on the page (the rest had no usable price or were pinned outside the radius): 84 with a clean title, 12 rebuilt, 2 with a lien, 2 with no title, 1 for parts. 78 were named to a model the catalogue knows. Only 7 had the three similar cars a judgement needs, because private sellers' cars are older and higher-mileage than what the lots hold; 3 of those sat a tenth or more under.
- It has not been read from GitHub's servers yet. A refusal there is reported in the run log and costs nothing else.
- Craigslist's robots.txt allows these pages; its terms of use forbid collecting listings by program without a licence.
- Make and model are whatever the seller typed, matched to models the catalogue already knows; a make it has never seen, or a model it has never seen, stays unnamed and is not judged. An odometer of 10 to 400 on a car over three years old is read as thousands.
- Private cars are judged against a catalogue that is almost all dealers, who ask more, so most show as under similar cars. A car pinned more than the radius from the home point is kept in the catalogue and left off the page. A car whose seller says the title is not clean is shown without a judgement.
- The seller's description and phone number are not kept.

## How discovery places a dealer

1. OpenStreetMap (`shop=car`) gives the dealers in the box around the home point. Seeds are merged in by website host.
2. DNS for the dealer's host names the platform for the big ones, with no request to the dealer's site.
3. Only when DNS says nothing, the dealer's front page is fetched once and matched against `PAGE_MARKS`.
4. `READS` says whether that platform's inventory answers a plain request (`plain`), needs a real browser (`browser`), or has not been classified (absent).

## What the readers were seen to do (2026-11-21, from a home connection)

A live build read 19 of 19 dealers and put 3,605 cars on the page, 1,706 of them from dealers other than Carvana.

| Platform | Dealers read | Requests per dealer | Whole inventory? |
|---|---|---|---|
| DealerOn | Jim Keras Nissan, Subaru and Buick GMC, Jimmy Gray Chevrolet | 1 page, then 1 per 96 cars | Yes |
| AutoRevo | Peck Daniel, Memphis Car Smart, Stanley's, Tim Pomp | 2 | Yes when the sitemap lists no more cars than the page; robots.txt forbids its further pages |
| Dealer Car Search | Street Cars of Memphis, Victory Auto, Imports of Memphis | 1 | Yes under 100 cars; a second page has not been tried |
| Team Velocity | Gossett Motor Cars (two sites), INFINITI of Memphis | 1 per 50 cars, then 1 for photos | Yes. The three sites share one pool of 370 cars |
| DealerFire | JR's Auto Sales | 1 per 100 cars | Yes |
| Dealer Alchemist | City Auto | 1 page, then 1 per 250 cars | Yes. Only the lots in the dealer's own city are kept (451 of the group's 844) |
| DealerCenter | Collierville Auto Center | 1, then 1 per 30 cars | Yes. Its pages sit behind a Cloudflare challenge; the reader asks the site's own admin-ajax service, which does not |
| Carsforsale.com | E Z Auto | 1 per 24 cars | Yes |
| Carvana | Carvana | 1, then 1 per 100 cars | Yes: the 1,899 cars with free delivery to ZIP 38103. 1,392 are kept within 60 miles, `extra.location_miles` says how far each is |

Each platform's route, and what was tried and failed, is in `research/08-routing-*.md`.

Known limits:

- Imports of Memphis shows one unlabelled figure per car that is a down payment, so its cars have no asking price and stay off the page. The figure is kept in `extra.unlabelled_price`.
- The catalogue keeps the asking price before the dealer's fees, and the fees beside it in `extra.fees`. The page shows the two added together, because dealers differ: Jim Keras advertises the price with its $899 fee in it, Jimmy Gray shows its $425 fee apart. A dealer that states no fee is shown at its asking price, marked "dealer fee not stated".
- Dealer.com (six sites) and Dealer Inspire (two) refuse plain requests and have no reader.
- Landers Used (Dealer eProcess) and Supercars Autosales (Dealer Car Search) are behind a Cloudflare challenge on every page. A route through a visible browser was found for both and is not part of the build: `research/08-routing-dealereprocess.md`, `research/08-routing-unknowns.md`. `cartrack/readers/dealereprocess.py` is written and tested but not registered.
- The Jim Keras sites, and the Gossett sites, list many of the same cars. The page shows each car once, by VIN, at its lowest price.
- Some sites turn away particular user agents: Carsforsale.com answers "python-urllib" with a false 500, and the Team Velocity sites answer 406 without "Mozilla/5.0". The readers say which name they send.
- Car Choice's website is gone, and King Cotton Ford is now Landers Ford North, on Dealer.com.

## What a card shows beyond the car

Seen on the build of 2026-11-21 (3,602 cars):

| Shown | From | Cars |
|---|---|---|
| Total with fee and tax | the dealer's stated fee (`extra.fees`) and `cartrack/cost.py` | tax on all; a fee on 977 |
| Miles a year | mileage and model year | all |
| Carfax report link | the link on the dealer's own listing (`readers.history`) | 681 |
| One owner, Carfax's value badge | the Carfax badge on the listing | 27 and 50 |
| Certified | the dealer's feed, unless it marks every car | 72 |
| Warranty left, not ready yet | Carvana's feed | 854 and 500 |
| Fuel economy | City Auto's feed | 328 |
| Recall check link | NHTSA's lookup by VIN | all |

## Not built yet

- Readers for the city impound auction, government surplus and lenders' repossessions, and the Facebook extension.
- Craigslist sites beyond Memphis, its by-dealer listings, and reposts of one car under a new listing.
- Linking the same car across listings by photo or phone. Today only a shared VIN links two listings.
- A net figure after tax, title and repairs, and how fast each model sells. Price-cut ordering needs a few days of history to mean anything.

Research behind these choices is in `research/`, numbered 01 to 09.
