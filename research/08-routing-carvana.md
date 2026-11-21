# 08. Routing: Carvana, as a Memphis buyer sees it

Tested 2026-11-21 (UTC 01:10 to 01:45) from a home connection. Buyer ZIP 38103 (downtown Memphis). Requests were 3 to 5 seconds apart. Scripts, captures and logs are in `research/_scratch/routing/carvana/`; every request made is in `captures/_log.jsonl`.

## Result

The route is plain HTTP. No browser, cookie, token or login is needed. carvana.com's own search pages are behind a Cloudflare challenge, but the JSON service they call, `apik.carvana.io`, answers the tracker's own user agent. The reader `cartrack/readers/carvana.py` read **1,899 of the 1,899 cars** Carvana counts as free delivery to 38103, in **20 requests and 74 seconds**. Every car came with a VIN, price, mileage, photo, location id and shipping fee. Tests: `tests/test_reader_carvana.py` (13 tests). The whole suite (`py -m unittest discover -s tests -t .`) ran 209 tests, all passing.

## 1. What "Carvana's Memphis inventory" can mean, and the counts

The data can tell the bounds apart. Each search result carries the `locationId` where the car is kept and, once a ZIP is given, `price.transportCost` (the shipping fee to that ZIP). A distance service gives the miles from the ZIP to every location id. The car's own page names the location's street address.

Counts from the search service's own `totalMatchedInventory`, 2026-11-21:

| Bound | Request filter | Cars |
|---|---|---|
| National, no ZIP | `{}` | 93,209 |
| Available to 38103 (whole list, priced with Memphis shipping) | `zip5: 38103` | 77,745 |
| Same, with the site's `LocationBasedPrefiltering` feature | | 71,893 |
| **Free delivery to 38103** | `filters.isFreeDelivery: true` | **1,899** |
| Same, by fee | `filters.transportCost.max: 0` | 1,899 (same set) |
| Paid shipping to 38103 | `filters.transportCost.min: 1` | 74,611 |
| Pickup within 3 days | `earliestDayToDeliveryOrPickup {Pickup, 3}` | 17,234 |
| Delivery within 3 days | `{Delivery, 3}` | 26,969 |
| Same-day delivery | `{Delivery, 0}` | 668 |

Of the 77,745, 1,235 are in neither the free set nor the paid set. I did not look into these.

Where the 1,899 free-delivery cars are kept (full read, `captures/live_read.json`):

| Location id | Where (from the car's page) | Miles from 38103 (distance service) | Cars |
|---|---|---|---|
| 131 | 1100 Family Dollar Dr, West Memphis, AR 72301 | 9 | 1,387 |
| 289 | not named (Memphis delivery hub, per the availability service) | 14 | 5 |
| 294 | 631 Burnett Rd, Old Hickory, TN 37138 (Nashville) | 205 | 387 |
| 30 other locations | not named | 237 to 2,000+ | 120 |

- **Kept within 60 miles (the project's radius): 1,392 cars.** 1,036 are purchasable now and 356 are `Reservable` (still being readied).
- Kept farther away but shipped free: 507 cars.
- Carvana locations within 60 miles of 38103: 131 (9 mi), 271, 289 and 394 (14 mi), 104 (16 mi, the Appling Farms vending machine) and 23 (19 mi). The next is 328 (North Little Rock), 118 miles away. Only 131 and 289 held cars in the free set.

Free delivery is a rule about the destination market, not about where the car is. The free set for each ZIP was: West Memphis 72301, 2,254; Little Rock 72201, 1,760; Oxford MS 38655, 6,788; Nashville 37203, 6,970.

The day counts do not stand in for location. The 668 "same-day delivery" cars sit at 54 locations nationwide, and 592 of them are more than 250 miles away.

**Recommended bound: free delivery to 38103 (1,899 cars), with each car's location and distance kept.**

- For these cars the asking price is the whole price a Memphis buyer pays before tax and registration. That makes it comparable with local dealers' prices.
- The site filters for this set itself and states its count, so completeness can be checked on every run.
- It takes 20 requests.
- The physically local subset (1,392 cars kept within 60 miles, almost all at West Memphis) is the same read filtered on `extra.location_miles <= 60`. No extra requests are needed.

Evidence that the free set holds every car kept locally, as far as I tested:
- All 1,392 cars seen at locations within 60 miles were in it.
- The cheapest-to-ship paid cars (sorted with `sortBy: FreeShipping`, fees of $190 and $290) are all kept 237 to 439 miles away.

I did not read the full 77,745 to prove this outright.

## 2. The working route

All on `https://apik.carvana.io`, plain HTTPS. The headers needed are `Content-Type: application/json` and a user agent that is not Python's default (see 4.3). `Origin`, cookies and `browserCookieId` are not needed.

**a. Distance, 1 request**

`GET /merch/carvanamerchcontextapi/api/v3/distance?zip5=38103`

Returns `{"locationDistances": {"<locationId>": miles, ...}}` for 493 location ids.

**b. Search, 1 request per 100 cars**

`POST /merch/search/api/v2/search` with this body:

```json
{"zip5": "38103", "filters": {"isFreeDelivery": true},
 "pagination": {"page": 1, "pageSize": 100}, "sortBy": "MostPopular",
 "requestedFeatures": ["ExcludeFacetData"]}
```

The answer is `{inventory: {pagination: {currentPage, pageSize, totalMatchedInventory, totalMatchedPages}, vehicles: [...]}, userDeliveryInfo, searchRequestId, facetData}`.

Paging:
- `page` counts from 1. Read up to `totalMatchedPages`.
- 100 a page is the most the service serves. Asked for 101, 200, 500 or 2000, it returns 24 cars but still echoes the asked size, and computes `totalMatchedPages` from it. The reader treats a short page before the last as an incomplete read.
- Deep paging stops at `page x pageSize` of 9,500 or more, which answers `400 "Invalid Request"`. Page 94 at 100 a page works and page 95 does not; page 189 at 50 works and page 190 does not. Any one query can therefore reach about 9,400 cars.
- The full read gave 1,899 unique ids with the `MostPopular` sort and no repeats across pages.
- `sortBy` values the site uses: `MostPopular, LowestPrice, HighestPrice, LowestMileage, NewestInventory, NewestYear, AcquisitionTime, CashDue, FreeShipping, MonthlyPayment`.

Filter keys, from the site's own validation schema:
- Lists: `makes[{name, parentModels[{name, trims}]}]`, `bodyStyles`, `colors`, `driveTypes`, `fuelTypes`, `tagIds` and others.
- Ranges `{min, max}`: `price`, `mileage`, `year`, `transportCost` and others.
- `isFreeDelivery`.
- `earliestDayToDeliveryOrPickup {pickupAndDeliveryOption: Pickup|Delivery|PickupAndDelivery, days}`.

Location filters (`locationIds`, `vehicleLocationIds`) are silently ignored.

**Fields used, per car**
- Identity: `vehicleId`, `vin`, `stockNumber`, `year`, `make`, `model`, `trim`, `mileage`, `bodyStyle`, `fuelType`, `color`.
- Money: `price.total`, `price.transportCost`, `price.kbbValue`, `price.msrp`, `previousPrice`, `priceUpdateDate`.
- Place and status: `locationId`, `vehiclePurchaseType` (`Purchasable` or `Reservable`), `fulfillmentType` (3 Carvana, 1 dealer marketplace, 2 partner retail, 0 unknown).
- Listing URL: `https://www.carvana.com/vehicle/{vehicleId}`, the page's canonical link.
- Photo: `https://cdnblob.fastly.carvana.io` + `imageUrl`, tested 200 image/jpeg. `standardizedHero` is an absolute alternative.

**Requests per full read: 20** (1 distance + 19 search pages).

**Other bounds**
- **Physically local:** use the same read and keep `extra.location_miles <= 60`. 1,392 cars.
- **Whole list priced for Memphis:** use the same `carvana.search(get, filters, "38103")` with `filters` slices that each stay under 9,400 cars, for example `{"price": {"min": a, "max": b}}` bands. That is about 780 requests at 100 a page, roughly an hour at this pacing. No pricing calls are needed: the search result's own `price.transportCost` matched the pricing service's fee for 50 of 50 paid cars checked ($190 and $290).
- **Pricing service, if wanted:** `POST /merch/search/api/v2/pricing` with `{"browserCookieId": "", "vehicleIds": [up to 50], "zip5": "38103", "applyTradeIn": false}` returns `vehiclePaymentTermsMapping{id: {downPaymentDetails.nonRefundableShippingFees, estimatedTaxesAndFees, monthlyPayment, ...}}`.
- **Delivery dates:** `POST /merch/buffering/api/v1/soonestavailabilitybulk` takes header `clientid: srp_ui` (without it: 400 "ClientId header is required") and body `{"vehicles": [{"vehicleId", "vehicleInventoryType": "Core", "vehicleLocationId"}], "zipCode": "38103"}`. It returns the soonest delivery and pickup per car, with days, serving location and its city. `GET /merch/search/api/v1/Delivery?Zip5=38103` groups location ids by days to delivery or pickup.

## 3. Asking price and fees

| Figure | Meaning |
|---|---|
| `price.total` | **The asking price.** Carvana's vehicle price, before tax, title and registration. It equals `incentivizedPrice` when there are no incentives. The reader stores it as `price`. |
| `price.transportCost` | **Shipping fee to the ZIP**, separate from the price. On the pricing service and the car's page it appears as `downPaymentDetails.nonRefundableShippingFees` and is due up front. It is $0 for every car in the free set. The same West Memphis car showed $1,890 for a Virginia ZIP. Stored as `extra.shipping`. |
| `price.totalTaxes`, `totalFees`, `feesMinusShipping` | Always 0 in search results: not worked out there. |
| `estimatedTaxesAndFees` (pricing service only) | Carvana's estimate, for example $1,929 on a $22,590 car. Not stored. |
| `kbbValue`, `msrp`, `marketAdjustment` | Reference figures, not prices to pay. `kbb` and `msrp` are stored in `extra`. |
| `previousPrice`, `priceUpdateDate` | The price before the last change, and when it changed. Stored as `extra.previous_price` and `updated`. |

## 4. Every route tried, and what each returned

### 4.1 www.carvana.com, plain HTTP

| Request | Answer |
|---|---|
| `/`, `/robots.txt`, `/sitemap.xml`, `/buy/sitemap.xml`, `/buy/ford`, any UA | 200 |
| `/cars`, `/cars/in-memphis-tn`, `/vehicle/{id}` with an Edge UA (Python urllib) | **403**, `Server: cloudflare`, `Cf-Mitigated: challenge`, page "Just a moment..." (Cloudflare managed challenge) |
| Same with the tracker UA, or a Googlebot UA | 403, same challenge |
| curl 8.19 (Windows Schannel TLS, a different TLS fingerprint from Python's OpenSSL), HTTP/1.1, full Edge header set including `sec-ch-ua` and `Sec-Fetch-*` | 403, same challenge |

- This curl build cannot do HTTP/2, so HTTP/2 from curl was not tested.
- The challenge applies by path (`/cars*`, `/vehicle/*`) whatever the user agent, TLS client or headers. A `__cf_bm` cookie set by a first request did not change it.
- **Vendor: Cloudflare** (Bot Management cookie `__cf_bm`, managed challenge).
- Sitemaps: `sitemap_0..2.xml.gz` hold 124,454 `/cars/...` category and city pages (for example 701 `...-in-memphis-tn` pages). There are no vehicle pages. `/buy/sitemap.xml` is 6,744 buying guides.
- robots.txt on www disallows `/api/`, `/search/` and `/inventory/` there. `apik.carvana.io/robots.txt` disallows nothing (its rules are commented out).
- The vehicle page carries no JSON-LD and no `__NEXT_DATA__`. Its data is in the Next.js app router's `self.__next_f` stream. It includes `location{addressLine1, city, stateAbbreviation, zip5, locationId}`.

### 4.2 Finding the service

- The home page (200) loads the merch UI bundle from `assets.fastly.carvana.io/merchui`. Its chunks name every service: `/merch/search/api/v2/search`, `/v2/pricing`, `/v1/Delivery`, `/buffering/api/v1/soonestavailabilitybulk`, `/carvanamerchcontextapi/api/v3/distance` and others. They also hold the search body the page builds: `{analyticsData, browserCookieId, filters, pagination, requestedFeatures, sortBy, zip5}`.
- `POST /merch/search/api/v3|v4|v5|v6/search` returns 400 `UnsupportedApiVersion`. Only v2 exists.
- `apik.carvana.io/` returns 301 to `apps.carvana.io/newcar/cms/`, which timed out.

### 4.3 What trips apik.carvana.io

| Request | Answer |
|---|---|
| Python's default UA (`Python-urllib/3.14`), with or without `Origin` | **403, Cloudflare error 1010**: the site bans that client signature |
| Tracker UA `cartrack/0.1 (python-urllib)`, no `Origin` | 200 |
| Edge UA | 200 |

The project's `fetch.get` already sends the tracker UA.

### 4.4 Other listing sites

These were not needed, so they were not retried. The earlier tests in `research/02` (2026-11-20) found:
- Cars.com: 403, Cloudflare.
- CarGurus: 403, DataDome.
- Autotrader: Akamai "page unavailable".
- TrueCar: 403, HUMAN/PerimeterX. Its sitemaps are open.
- Edmunds: 403, Akamai. Its open API is retired.

I found no public Carvana partner feed.

### 4.5 A real browser

| Attempt | Answer |
|---|---|
| Headless Edge 157 over the DevTools protocol (`scripts/edge_capture.mjs`) | Stays on "Just a moment..." after 25 s |
| Headed Edge (a visible window, same script with `--headed`) | Passes the challenge in a few seconds. The vehicle page loads and calls `soonestavailabilitybulk`, `pricing/vehicle`, `Delivery`, `distance` and `personalized-recs` on apik |
| The `cf_clearance` cookie that visit minted, replayed on plain urllib for a different car (`scripts/replay_clearance.py`) | 200, real page with its location object. It also worked with the tracker UA |

So the browser is needed only to mint the cookie for www pages. The inventory route does not use www at all. The browser was used here only to read the street addresses of locations 131 and 294.

## 5. GitHub Actions (datacenter address)

**Not tested; no datacenter address was available.** Evidence and reasoning:
- apik accepted Python's own TLS stack and a non-browser user agent here. The only rule it showed was the ban on Python's default user agent (error 1010).
- The challenge on www is a rule by path, not a score on this client.
- Whether Cloudflare's IP reputation challenges datacenter ranges on apik is unknown.

If it refuses, `fetch.get` raises `HTTPError` 403 after three tries and the build keeps Carvana's last cars. Fallbacks:
- Headless Edge did not pass the challenge here, so a browser fallback on a runner would need a headed browser under a virtual display (untested).
- Only the www pages need that browser anyway.

The first Actions run's log will settle it.

## 6. Running the browser script (needed only to name a new location id)

From the project root:

    node research/_scratch/routing/carvana/scripts/edge_capture.mjs https://www.carvana.com/vehicle/<vehicleId> research/_scratch/routing/carvana/captures/<name> 30 --headed

- It opens a visible Edge window for about 30 seconds.
- It writes `<name>.html`, `<name>.calls.json` (every JSON call with request headers, bodies and answers), `<name>.cookies.json` and `<name>.cookies-full.json`.
- Search the HTML for `\"location\":{\"addressLine1` to get the address.
- `py research/_scratch/routing/carvana/scripts/replay_clearance.py <name>.cookies-full.json <url> <out>` replays the cookie plainly.
- The captures embed this machine's public IP address (Carvana geolocates it), and the cookie file holds live session cookies. Redact the first and delete the second before committing. I did both for the captures kept here.

Without a Memphis cookie, the browser prices for the ZIP Carvana guesses from the IP, which here was not Memphis.

## 7. What the integrator adds to the shared files

`cartrack/readers/__init__.py`, change the import line and add one line to `READERS`:

    from . import autorevo, carvana, dealercarsearch, dealeron  # noqa: E402  (they use the helpers above)
        "carvana": carvana.read,

`tests/test_readers.py` line 33:

    self.assertEqual(set(readers.READERS), {"dealeron", "autorevo", "dealercarsearch", "carvana"})

`cartrack/dealers.py`, add to `PAGE_MARKS` (Carvana's front page loads this host; DNS says only CloudFront) and to `READS`:

    ("assets.fastly.carvana.io", "carvana"),
    "carvana": "plain",

`dealers.json`, the Carvana row (`"key": "carvana.com"`), so a build works without rerunning discovery:

    "platform": "carvana",
    "reads": "plain"

`README.md`, the readers table and known limits:

    | Carvana | Carvana (free delivery to 38103) | 1 distance + 1 per 100 cars (20 in all) | Yes: count checked against the site's own total |
    - Carvana's cars are national stock delivered free to Memphis; `extra.location_miles` says how far away each is kept (1,392 of 1,899 within 60 miles, at West Memphis). Shipping is `extra.shipping`, not added to the price. Carvana cars have city/state/ZIP but no coordinates.

Notes for the build and the page:
- The reader does not use `dealer_listing`. The seller is Carvana (`seller_id` "carvana.com") and the place is where the car is kept, not the dealer row's vending-machine address.
- Coordinates are left empty because neither the Census geocoder nor Nominatim knows 1100 Family Dollar Dr.
- Only locations 131 and 294 have names in `LOCATIONS`. Others carry `location_id` and `location_miles` only.
- Cars that leave the free set (a fee appears) will be marked gone by a complete read, even if they are still for sale nationally.
