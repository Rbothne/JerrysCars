# CraigsCars

A catalogue of used cars for sale around Memphis, Tennessee, with their price history, and a page that shows them.
It reads dealers' own websites, Craigslist's for-sale-by-owner listings in seven cities, and the City of Memphis impound auction. The dealers are the yardstick; the
cars worth finding are the ones priced well under them.

Python standard library only. Tested with Python 3.14 and Node 26.

## What is here

| Piece | File | What it does |
|---|---|---|
| Dealer discovery | `discover.py`, `cartrack/dealers.py` | Dealers within the radius of the home point, and the website platform each runs on. Writes `dealers.json`. |
| Readers | `cartrack/readers/` | One per dealer platform: DealerOn, AutoRevo, Dealer Car Search, Team Velocity, DealerFire, Dealer Alchemist, DealerCenter, Carsforsale.com, Carvana. Each gives back listings and whether it saw the whole inventory. |
| Other sources | `cartrack/sources/` | Readers for places that are not one dealer's website, listed by hand in `sources.json`. Craigslist by owner: one search page a city a run, and each listing's own page once. The City of Memphis impound auction: the coming sale's lots every run, and each finished sale once, for what its lots sold for. |
| Naming | `cartrack/identify.py` | Make and model for a listing that gives them only in the seller's words ("chevy silverado lt"), matched against the models the catalogue knows from decoded VINs. |
| Listing record | `cartrack/listings.py` | `make_listing()`: the one record every reader hands back. `None` means the source does not say. |
| Catalogue | `cartrack/catalogue.py` | One SQLite file, `data/catalogue.db`: listings, price points added only on change, seen-spans, gone and back, VIN decodes, dealers. |
| VINs | `cartrack/vin.py` | Check digit, and identity from NHTSA's free vPIC service, 50 VINs a request. A decoded VIN's identity wins over the dealer's wording. |
| Value | `cartrack/value.py` | What cars like each one usually ask, from the other cars in the catalogue: the lower of a price model and the car's nearest neighbours. How far to trust it is in `research/09-value.md`. |
| Cost | `cartrack/cost.py` | Tennessee sales tax on a vehicle, for the total shown under each price (price, the dealer's stated fee, tax). Title and registration are not in it. |
| Build | `build.py` | Reads every source and every dealer that has a reader, updates the catalogue, decodes new VINs, names the listings that have only a seller's words, judges value, writes `site/data/cars.json`. |
| Page | `site/` | Plain HTML and JavaScript, no build step. `logic.js` holds the search, filtering and ordering. Search reads title, make and model, ignores punctuation ("crv", "f150", "f 150"), knows a few nicknames ("chevy", "vw") and, for a word that matches no car, falls back to names one slip away ("camery"). Filters: within so many miles, sold by (private sellers or dealers), make, model, price, year, mileage, body, drive, fuel, source, local lots only, price cuts only, below typical price only, no branded titles. Sorts by one field (value, price, price cut, year, mileage, miles a year, days listed, distance), ascending or descending, and opens with the cars furthest under similar ones first. |
| Auction page | `site/auctions.html`, `site/auctions.js` | The impound auction's coming lots and every past result, from `site/data/auctions.json`. Beside a coming lot: what such cars sold for there before, what they ask around Memphis, and whether this car has been through a sale already. Styles are shared with the cars page in `site/style.css`. |
| Schedule | `.github/workflows/update.yml` | Twice a day on GitHub Actions: build, keep the catalogue on the `data` branch, publish `site/` to GitHub Pages. |
| Fetching | `cartrack/fetch.py` | Plain HTTP with retries and a per-site delay. Sends the tracker's own name. Every source is read at the same time, each site at its own pace (below). |

## Run

    py discover.py                              # rewrites dealers.json and the catalogue's dealer table
    py build.py                                 # reads the sources and dealers, updates data/catalogue.db and site/data/cars.json
    py -m http.server 8000 --directory site     # then open http://localhost:8000
    py -m unittest discover -s tests -t .       # 349 Python tests
    node --test tests/js/logic.test.mjs         # 56 page-logic tests

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

- `area.json`: home point and radius. Memphis, 60 miles. The radius bounds dealer discovery only; distances on the page are measured from the home point, and the page's "Within (miles)" box does the limiting.
- `dealers-seed.json`: hand-kept dealers that OpenStreetMap lacks. Add a line to add a dealer, then run `py discover.py`.
- `dealers.json`: written by discovery and read by the build. Committed, so the scheduled build does not rediscover.
- `sources.json`: hand-kept places that are not a dealer's website. One row per Craigslist city: `kind` names the reader, `site` the city's Craigslist name, and `floor` how far the place's listings may thin out between two reads before the read is taken as broken (0.5 for Craigslist, where listings come and go faster than on a lot; 0.8 otherwise).

## The city impound auction (seen 2026-11-21, from a home connection)

- Venture Auctions sells the city's impounded vehicles most Wednesdays, about 60 a week, on www.venture-auctions.com. The route, the fields and the buyer's rules are in `research/10-routing-impound-auctions.md`.
- A live read took 12 requests, three seconds apart, with no refusal: the list of coming sales, the 25 November sale (no lots posted yet: they go up the Monday evening before), the list of finished sales, and the sales of 18 and 11 November in four and five pages. 186 lots, every one with a VIN that vPIC decoded; 180 sold, 6 marked no-sale; the middle sale price was $575.
- Earlier sales, back to 6 May 2026, are read ten a run until all 31 are on record. After that an ordinary run is three requests plus the coming sale's pages.
- A lot states no mileage, keys, running condition or title, so it has no asking price and is never ranked with the cars for sale. It lives on its own page. A lot with a result is closed the moment it is recorded: "sold", or "ended_unsold" for one the auctioneer marked no-sale.
- `sources.json` carries the auction's own charges (`premium` 0.1, `fee` 10, `card` 0.04), which the page uses to say what a bid costs before tax.
- Not seen yet: what an open lot shows once prebidding starts (read as the bid so far, as the auctioneer's sister site showed it), and whether the site answers GitHub's servers.

## Craigslist (seen 2026-11-21, from a home connection)

- `https://memphis.craigslist.org/search/cto` answered the tracker's own name with 120 by-owner results in the page. Each result's address ends in a key that did not change between two reads minutes apart; that key is the listing's id here. Whether it lasts the life of a listing has not been watched yet: if it does not, every listing will look new each day.
- Each listing's page was read once (120 requests, three seconds apart) and gave a year and a posting time for all 120, and a VIN for 8. Later runs ask only for listings they have not read, so a normal run is one request plus a few.
- That first build put 101 of the 120 on the page (the other 19 were pinned outside the radius): 84 with a clean title, 12 rebuilt, 2 with a lien, 2 with no title, 1 for parts. 78 were named to a model the catalogue knows, and 82 once the title was tried where the typed make and model failed. Only 7 had the three similar cars a judgement needs, because private sellers' cars are older and higher-mileage than what the lots hold; 3 of those sat a tenth or more under.
- From GitHub's servers the same day it read the same way: the run of 21:39 UTC put the same 101 cars on the published page, in twelve minutes for the whole build. A refusal there would be reported in the run log and cost nothing else.
- Craigslist's robots.txt allows these pages; its terms of use forbid collecting listings by program without a licence.
- Make and model are whatever the seller typed, matched to models the catalogue already knows; a make it has never seen, or a model it has never seen, stays unnamed and is not judged. An odometer of 10 to 400 on a car over three years old is read as thousands.
- Private cars are judged against a catalogue that is almost all dealers, who ask more, so most show as under similar cars. A car whose seller says the title is not clean is shown without a judgement.
- Six more cities were added the same day, the nearest by Craigslist's own list of areas: Jonesboro (60 miles), North Mississippi (62), Jackson, TN (77), Southeast Missouri (122), Little Rock (130) and Muscle Shoals (136). Read in full from a home connection that evening, they gave 11, 40, 20, 13, 82 and 7 listings, none shared with another city: 291 private cars on the page with Memphis's 120, of which 112 are within 60 miles, 143 between 60 and 150, and 36 beyond. 235 were named to a known model and 29 had enough similar cars to be judged; 8 of those sat a tenth or more under. Since then no car is left off for being far: each carries its distance from its own map pin, and the page filters and sorts by it. A listing two cities both show is one car.
- A search page stops at about 360 results. None of these cities is near that, but a page of 300 or more is asked again in five price bands, which the page honours (`min_price=5000&max_price=10000` gave 55 results, all from $5,000 to $10,000).
- The seller's description and phone number are not kept. The title is, and a title that says why the car is cheap ("mechanic special", "as-is", "needs", "won't start", "for parts", "no title": `CAUTIONS` in `build.py`) puts that on the card and keeps the car out of the comparison. On 2026-11-21 the car at the very top of the page was a "Mechanic Special / As-Is" minivan marked $6,200 under; 6 of 271 private cars carry such a warning.
- A private car posted again (the same year, mileage, price and map pin, and no VIN) is shown once. That folded 20 listings away on 2026-11-21, 11 of them one Greenwood, Mississippi seller posting each of his cars in two cities.

## Reading every site at once

The build starts every source's read together, a thread each, and writes the catalogue itself, one source at a
time, in the order the sources are listed. Each site is still asked one request at a time, three seconds
after its last one ended; only different sites overlap. So a run takes as long as its slowest site, not as
long as all of them added up. Six small dealers read this way on 2026-11-21 took 4.3 seconds for 10 requests,
with no site asked twice inside three seconds.

Hosts that belong to one company share one clock (`ONE_COMPANY` in `build.py`): every `*.craigslist.org`,
so seven cities and their listings' pages together ask Craigslist one request every three seconds, exactly
as one city did. That makes Craigslist the slowest lane whenever many listings are new, about 15 minutes for
the 300 of a first read, and a few seconds on an ordinary run, when only new listings are asked for.

## When a source has cars and the page shows none

Looked for on 2026-11-21, after the storefront tracker's trouble with stores that read as empty. What was found
here, and what now stands against it:

| What went wrong | Seen | Now |
|---|---|---|
| A car listed by several dealers was credited only to the one whose name sorts first | INFINITI of Memphis and Gossett Motor Cars (used) showed 0 of 321 and 282 priced cars; Jim Keras Subaru 24 of 248 | Each car carries `also`, the other dealers listing it. Counts and the Source filter use it. |
| A read that is never quite whole marks nothing gone | Carvana's count moved while its pages were fetched: 1,901 read, "partial", and 48 cars not seen since the morning stayed on the page | `catalogue.age_out`: a listing no read has found for three days is gone, whatever the reads called themselves. |
| A read that shrank under 80% is refused on every later run too | Not seen yet; a lot that really sold a fifth of its cars would be reported failed for good | The same three days: the missing cars age out, and the next read passes. |
| A reader that takes the wrong thing for the id gives many listings one id, and they overwrite each other | Not seen here; the storefront tracker's commonest quiet failure | A read where under 80% of the listings have an id of their own is refused and reported. |
| The seller's make-and-model box is filled wrongly | "GMC" beside "2004 GMC Sierra 1500"; "2009" beside "2009 Chevy Impala LT"; "Ford Firsta" beside "2019 Ford Fiesta" | The title is tried when those words name no model. |
| A source reads well and shows nothing, which looks like a source with no cars | Imports of Memphis: 29 read, no asking prices | The build prints, for every source, live listings, how many are priced and how many reach the page, and marks the ones where none do. |

Three gaps found in the same review were closed the same day. Dealer Car Search read only its first 100 cars:
it now follows `&page=2` and on until a page comes back short (checked on victoryauto.org with a page size of
25). A Craigslist page cut short at about 360 results is asked again in price bands. And AutoRevo, Dealer Car
Search and Craigslist refuse a page where fewer than 80% of the cards or results give a listing, so a renamed
link cannot pass for a nearly empty lot even on a first read.

Still open: the readers that take a JSON feed drop a car they cannot make a listing of without saying so. They
compare what they read with the feed's own count, so such a read is reported as partial, not refused.

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
- The Jim Keras sites, and the Gossett sites, list many of the same cars. The page shows each car once, by VIN, at its lowest price, and counts it for every dealer that lists it: choosing any of them under Source finds it.
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

- Readers for government surplus, tow-lot lien sales and lenders' repossessions, and the Facebook extension.
- Craigslist's by-dealer listings, and reposts of one car under a new listing.
- Linking the same car across listings by photo or phone. Today only a shared VIN links two listings.
- A net figure after tax, title and repairs, and how fast each model sells. Price-cut ordering needs a few days of history to mean anything.

Research behind these choices is in `research/`, numbered 01 to 10. The three numbered 10 are where impounded, government and repossessed cars around Memphis are sold and which of those places can be read: the city's weekly impound auction is the one that matters, with every lot's VIN and hammer price on plain pages.
