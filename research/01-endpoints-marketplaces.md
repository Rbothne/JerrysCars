# 01 · Endpoints on consumer marketplaces and auction sites

Probed 2026-11-20 (US Eastern evening) from this machine. Every request was a Python standard-library `urllib` call with a desktop Chrome User-Agent, at most 5 per host and spaced 4 seconds or more apart. Scripts, logs and samples are in `research/_scratch/endpoints-marketplaces/`:

- `probe.py`, `probes*.json`: the probe runner and the exact requests sent. `probe_log.tsv` has every status, final URL and the relevant response headers.
- `samples_small/`: one trimmed real response per source. `make_samples.py` builds it from the raw responses in `samples/`.
- `docs/`: eBay OpenAPI contracts and doc pages, saved from developer.ebay.com.

Evidence labels: **TESTED** means I ran it here. **DOCUMENTED** means I read it in the operator's own docs or contract. **REPORTED** means it comes second-hand from open-source code, scraper vendors or forums.

One limit on testing: this session's tool policy refused a second round that sent full browser fingerprint headers (Sec-Fetch and client hints) to eBay and Facebook, and refused a JSON POST to Copart's internal search API. Those three items are therefore REPORTED or DOCUMENTED only. Everything else below was requested plainly.

## Summary

| Source | Best access route | Auth | Sold / ended data | Plain stdlib request works | Evidence |
|---|---|---|---|---|---|
| eBay (API) | Browse API `item_summary/search` + `item/{id}` | OAuth app token (client credentials) | **No.** Active listings only. Sold data needs Marketplace Insights (partner-only) | n/a (needs key) | DOCUMENTED |
| eBay (site) | `/sch/` search, `/itm/` pages | none | Site has `LH_Sold=1&LH_Complete=1`, but it is blocked | **No**: 403 Akamai on search and sold search | TESTED |
| Craigslist | `sapi.craigslist.org/web/v8/postings/search/full` JSON, plus listing page JSON-LD and attrs | none | No (expired posts disappear) | **Yes** | TESTED |
| Facebook Marketplace | Logged-in web client GraphQL `POST /api/graphql/` (doc_id), or a browser extension in his own session | FB session cookies + `fb_dtsg` | Listing `is_sold` / `is_pending` flags only, no sale price | **No**: 400 on `/marketplace/washington/vehicles` | TESTED (block), REPORTED (GraphQL) |
| OfferUp | Search page `__NEXT_DATA__` (Apollo/GraphQL result embedded) | none | No | **Search yes. Item pages no** (Cloudflare 403) | TESTED |
| Mercari | Internal GraphQL (persisted queries) | none / session | UI has a sold filter (REPORTED) | **No**: Cloudflare challenge 403 | TESTED (block) |
| Nextdoor For Sale | Logged-in app only | account | No | **No**: redirects to `/login/` | TESTED |
| Copart | `POST /public/lots/search-results` JSON (SPA backend) | none for search; member login for full VIN and final bids | Not publicly; third-party archives exist | Shell page 200, but data needs the XHR behind Imperva | TESTED (shell), REPORTED (API) |
| IAAI | Server-rendered `/Search` HTML + `/VehicleDetail/{id}~US` with embedded JSON | none (VIN masked) | No | **Yes** | TESTED |
| GovDeals | `maestro.lqdt1.com` JSON search API used by the Angular app; site search `timeType=sold` | API keys shipped in the page config | **Yes**: sold results kept about 1 year (REPORTED) | Shell yes; API not called | TESTED (shell), REPORTED (API) |
| GSA Auctions | `api.gsa.gov/assets/gsaauctions/v2/auctions` | api.data.gov key (DEMO_KEY works) | No (active lots; `highBidAmount` field) | **Yes** | TESTED |
| PublicSurplus | `/sms/browse/search` and `/sms/auction/view?auc=` HTML | none | Closed auctions viewable (REPORTED) | **Yes** | TESTED |
| Municibid | `/browse/c160883/vehicles` HTML + listing JSON-LD (`Car` with VIN and mileage) | none | Not tested | **Yes** | TESTED |
| Bring a Trailer | `wp-json/bringatrailer/1.0/data/listings-filter` JSON | none | **Yes**: sold price, date, reserve-not-met | **Yes** | TESTED |
| Cars & Bids | `/v2/autos/auctions` (signed), `/rss.xml` | API needs a session cookie and signature | Past auctions in SPA (signed API) | RSS yes; API **no** (400 "No Session token") | TESTED |
| HiBid (tow, impound, estate auctioneers) | `hibid.com/lots` SSR with `hibid-state` JSON | none | Not tested | Yes (200) | TESTED (page) |
| PropertyRoom (police property) | `/c/vehicles` HTML | none | Not tested | Yes (200, 27 vehicles) | TESTED (page) |
| Treasury seized general property | Bid-result PDFs | none | **Yes**: bid results posted about 2 weeks after each sale | Not fetched | DOCUMENTED |
| Montgomery Co. MD police impound | Monthly auction PDFs (year, make, VIN) | none | No | Not fetched | REPORTED (search index) |
| DC DPW impound | Sold on `dcgovt.govdeals.com` | none | via GovDeals | n/a | DOCUMENTED (dpw.dc.gov) |

**What this means for the plan, in short.** Price comparables for ordinary cars come from scraped asking-price history (Craigslist, OfferUp, eBay Browse, IAAI and auction current bids). Free sold prices are limited to BaT (enthusiast cars), GovDeals sold results and Treasury PDFs. eBay sold data is not available from the free API. Facebook needs the extension route.

---

## 1. eBay

### 1a. Browse API (DOCUMENTED, from the OpenAPI contract `docs/ebay_browse_oas3.json`)

Source: https://developer.ebay.com/api-docs/master/buy/browse/openapi/3/buy_browse_v1_oas3.json and the filter reference https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html

- **Search:** `GET https://api.ebay.com/buy/browse/v1/item_summary/search`
  - Auth: `Authorization: Bearer <application token>`. The token comes from the client-credentials grant at `https://api.ebay.com/identity/v1/oauth2/token` with scope `https://api.ebay.com/oauth/api_scope`.
  - Headers: `X-EBAY-C-MARKETPLACE-ID` (default `EBAY_US`). The contract's enum lists `EBAY_US` and not a separate Motors ID. eBay's Motors guide names `EBAY_MOTORS_US` (site 100) as the Motors marketplace (REPORTED). Vehicle categories sit under category 6001 either way, so the plan is `EBAY_US` + `category_ids=6001`, with `EBAY_MOTORS_US` as an A/B check once a key exists. `X-EBAY-C-ENDUSERCTX: contextualLocation=country%3DUS%2Czip%3D20001` is recommended for distance and price sorts.
  - Params:
    - `q` (100 characters max; spaces mean AND, `(a, b)` means OR)
    - `category_ids` (one ID)
    - `filter`
    - `aspect_filter=categoryId:<id>,Make:{Honda},...`. The category ID must match `category_ids`. Values are separated with `|`.
    - `fieldgroups`: `MATCHING_ITEMS`, `ASPECT_REFINEMENTS` (returns `aspectDistributions`, which shows the live aspect names for vehicles), `BUYING_OPTION_REFINEMENTS`, `CATEGORY_REFINEMENTS`, `CONDITION_REFINEMENTS`, `EXTENDED` (adds `shortDescription` and `itemLocation.city`), `FULL`.
    - `sort`: `price`, `-price`, `distance`, `newlyListed`, `endingSoonest`.
    - `limit` (1 to 200).
    - `offset` (a multiple of the limit).
    - **Hard cap of 10,000 items per result set.**
  - `compatibility_filter` is for parts fitment only (Year/Make/Model of the car a part fits), not for searching vehicles.
  - Filters relevant to cars:
    - `buyingOptions:{FIXED_PRICE|AUCTION|BEST_OFFER|CLASSIFIED_AD}`. `CLASSIFIED_AD` matters on Motors, where many local cars are classified ads. Use the filter with a leaf category.
    - `price:[500..8000],priceCurrency:USD`
    - `conditions:{USED}` or `conditionIds:{...}`
    - `itemLocationCountry:US`
    - Local area: `pickupCountry:US,pickupPostalCode:20001,pickupRadius:75,pickupRadiusUnit:mi,deliveryOptions:{SELLER_ARRANGED_LOCAL_PICKUP}`. All five are required together, and they override delivery filters.
    - `itemStartDate:[2026-11-19T00:00:00Z..]`, which picks up only new listings on incremental runs.
    - `itemEndDate:[..]`
    - `sellerAccountTypes:{INDIVIDUAL}` (private sellers) or `{BUSINESS}`
    - `excludeSellers:{...}`
    - `searchInDescription:true`
    - `bidCount:[..5]`
  - Response `SearchPagedCollection`: `total`, `limit`, `offset`, `next`, `prev`, `itemSummaries[]`, `refinement`.
  - `ItemSummary` fields:
    - IDs and links: `itemId`, `legacyItemId`, `itemWebUrl`, `itemHref`
    - Description: `title`, `shortDescription` (EXTENDED only), `condition`, `conditionId`, `categories`, `leafCategoryIds`
    - Price and bidding: `price`, `currentBidPrice`, `bidCount`, `buyingOptions`, `marketingPrice`, `priorityListing`, `watchCount`
    - Dates: `itemCreationDate`, `itemOriginDate`, `itemEndDate`
    - Location: `itemLocation{postalCode, country, city (EXTENDED)}`, `distanceFromPickupLocation`, `pickupOptions`
    - Other: `seller{username, feedbackScore, feedbackPercentage}`, `image`, `additionalImages`, `thumbnailImages`, `shippingOptions`
    - **No VIN or mileage in the summary.**
- **Item detail:** `GET /buy/browse/v1/item/{item_id}` (RESTful ID `v1|<legacy>|0`). Also `item/get_item_by_legacy_id?legacy_item_id=`, and `item/?item_ids=` for batches of up to 20.
  - Fields: `localizedAspects[{name, value}]`, `reservePriceMet`, `minimumPriceToBid`, `uniqueBidderCount`, `bidCount`, `currentBidPrice`, `itemEndDate`, `itemCreationDate`, `itemLocation{city, stateOrProvince, postalCode, county}`, `description` (HTML), `conditionDescription`, `sellerItemRevision`, `seller`, `primaryItemGroup`, `product`, `lotSize`.
  - **VIN, Mileage, Year, Make, Model, Vehicle Title and so on arrive as `localizedAspects` name/value pairs.** These are Motors item specifics. eBay requires a VIN for modern vehicles (DOCUMENTED, https://www.developer.ebay.com/api-docs/user-guides/static/trading-user-guide/ebay-motors-item-specifics.html). The exact aspect labels (for example "Vehicle Mileage" in the Insights example, or "VIN (Vehicle Identification Number)") must be read from a live response or from Taxonomy.
- **Taxonomy API (DOCUMENTED, `docs/ebay_taxonomy_oas3.json`):** base `https://api.ebay.com/commerce/taxonomy/v1`.
  - `get_default_category_tree_id?marketplace_id=EBAY_MOTORS_US`. The tree ID for Motors is reported to be `100`.
  - `category_tree/{id}/get_category_subtree?category_id=6001` returns Cars & Trucks → Make → **Model, which is the leaf** (DOCUMENTED, https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/ebay-motors-categories.html).
  - `get_item_aspects_for_category?category_id=<leaf>` **errors on non-leaf IDs**, so aspects are per model category. It returns `aspects[{localizedAspectName, aspectConstraint{aspectDataType, aspectMode, aspectRequired, ...}, aspectValues[]}]`.
  - `fetch_item_aspects` gives a bulk gzip of all leaf aspects for a tree. It is the one-call way to build the aspect map.
  - Auth: app token, scope `api_scope`.
- **Feed API (DOCUMENTED, `docs/ebay_feed_oas3.json`):** `https://api.ebay.com/buy/feed/v1` offers `/access`, `/feed_type`, `/file`, `/file/{id}/download`, which serve daily TSV_GZIP category files plus hourly snapshots. It needs scope `buy.item.feed`, and eBay states that Buy APIs in production are "Limited Release … intended for eBay partners only. You must apply for production access through the eBay Partner Network" (https://www.developer.ebay.com/api-docs/buy/buy-requirements.html). **Treat Feed as unavailable.**
- **Call limits:** 5,000 calls a day for Browse by default (established earlier this session). The call-limits page returned 403 to a plain fetch, so it was not re-read. At 200 items per call, one daily run over the region (6001 + local pickup radius) costs tens of calls. Item-detail calls for VIN and mileage are the real cost, so call `getItems` (20 per call) only for listings that pass a price screen.
- **Sold data:** none in Browse. `lastSoldDate` exists only in Marketplace Insights (partner-only).

### 1b. Public site (TESTED)

- Requests sent: `GET https://www.ebay.com/sch/6001/i.html?_nkw=honda+civic&_stpos=20001&_sadis=50&LH_PrefLoc=99` and the sold view `GET https://www.ebay.com/sch/i.html?_nkw=honda+civic&_sacat=6001&LH_Sold=1&LH_Complete=1`.
- **Both returned 403** with an "Error Page | eBay" body from `Server: AkamaiGHost` and a `bm_s` Akamai Bot Manager cookie. Samples: `samples_small/ebay_search_*.html`.
- Item pages were not tested (no known item ID, and the browser-header retry was refused).
- The sold/completed view (`LH_Sold=1&LH_Complete=1`, about 90 days of history) exists on the site (REPORTED). Reading it would need a real browser (`tools/harvest.py` Playwright) or the extension.

## 2. Craigslist (TESTED)

- **Search page:** `GET https://washingtondc.craigslist.org/search/cta?query=honda` now **redirects to `https://www.craigslist.org/search/area/washingtondc?cat=cta&query=honda`** (200).
  - The HTML carries `<ol class="cl-static-search-results">` with `li.cl-static-search-result` entries (title, price, location text, link). This query returned 160 entries. Links use the new form `https://www.craigslist.org/view/d/{slug}/{viewKey}`.
  - It also carries `script#ld_searchpage_results` JSON-LD (193 `ListItem`s, each with offer price, geo lat/lon, locality/region and 600x450 image URLs).
  - The page JS then calls sapi.
- **JSON endpoint (the one the page calls):** `GET https://sapi.craigslist.org/web/v8/postings/search/full?batch={areaId}-0-360-0-0&cc=US&lang=en&searchPath={cat}&...filters`
  - No auth. A plain request with `Referer`/`Origin` of the Craigslist site returned 200 `application/json`.
  - `data.totalResultCount`, `data.items[]` (positional arrays), `data.decode`, `data.filters`, `data.location`, `data.canonicalUrl`.
  - **Item decode, checked against a listing page:**

    | Item element | Meaning | Check |
    |---|---|---|
    | `[0]` | posting ID offset; add it to `decode.minPostingId` | 7987331382 + 16719126 = **8004050508**, the post ID on the page |
    | `[1]` | seconds offset; add it to `decode.minPostedDate` | = 19:42:17 EST, matching "posted" on the page |
    | `[2]` | category ID | **145 = cto (by owner), 146 = ctd (by dealer)** |
    | `[3]` | price in dollars | |
    | `[4]` | `"{locIdx}:{descIdx}~lat~lon"` | `locIdx` → `decode.locations` (`[10,'washingtondc','mld'/'doc'/'nva']`, the sub-area); `descIdx` → `decode.locationDescriptions` (seller's free text) |
    | `[5]` | image-set key | |
    | negative int, when present | **duplicate-cluster ID** | |
    | `[13, viewKey]` | key for the view URL | |
    | `[4, "3:{imageId}", ...]` | images | URL is `https://images.craigslist.org/{imageId}_600x450.jpg` |
    | `[6, slug]` | URL slug | |
    | `[9, odometer]` | odometer reading | |
    | `[10, "$6,500"]` | price text | |
    | last element | title | |

    `make_samples.py` implements this decode.
  - **Cap and pagination:** the full endpoint returns at most **360 items**. Unfiltered `cta` reported `totalResultCount` 2,750 but returned 360. `batch=10-360-360-0-0` returned 0 items, so the offset is not the second batch field on `/full`. Sources report a follow-up `/web/v8/postings/search/batch` call that carries the `cacheId` from the first response (REPORTED, not verified). The practical route: slice under 360 with `sort=date` and frequent runs, or with price bands, `purveyor`, sub-area, or `postal` + `search_distance`.
  - **Filters accepted (from `data.filters`, TESTED):**

    | Filter | Values |
    |---|---|
    | `query`, `srchType=T` | free text; titles only |
    | `sort` | `date`, `dateoldest`, `rel`, `priceasc`, `pricedsc`, `dist` |
    | `min_price`, `max_price` | dollars |
    | `purveyor` | `owner`, `dealer` |
    | `auto_make_model` | text |
    | `min_auto_miles`, `max_auto_miles`, `min_auto_year`, `max_auto_year` | numbers |
    | `auto_title_status` | 1 clean, 2 salvage, 3 rebuilt, 4 parts only, 5 lien, 6 missing |
    | `condition` | 10 new … 60 salvage |
    | `auto_transmission`, `auto_drivetrain`, `auto_cylinders`, `auto_fuel_type`, `auto_bodytype`, `auto_paint` | multi-select |
    | `hasPic`, `postedToday`, `bundleDuplicates` | flags |
    | `subarea` | `doc`, `nva`, `mld` |
    | `postal` + `search_distance` | **TESTED**: `postal=22030&search_distance=15` centred the search on Fairfax with radius 15 and 403 results |

  - `searchPath=cto` with `auto_title_status=1&max_price=6000` gave 371 by-owner clean-title cars under $6k across the DC area. That is the core feed.
- **Areas:** `GET https://reference.craigslist.org/Areas` (200 JSON, 707 areas) returns `AreaID`, `Hostname`, `Abbreviation`, `Description`, `Region`, `Country`, `Latitude`, `Longitude`, `Timezone`, `SubAreas[]`. washingtondc = area 10 with sub-areas doc, nva, mld. Neighbouring areas (baltimore, frederick, fredericksburg, annapolis, southern MD and so on) come from the same list.
- **Listing page:** `GET https://www.craigslist.org/view/d/{slug}/{viewKey}` (200, 28 KB).
  - `<title>` says "for sale by owner - Arlington, VA".
  - `script#ld_posting_data` (schema.org Product) carries name, price, `availableAtOrFrom` (locality, region, **postalCode**, lat/lon), the full description, and every image.
  - `div.attrgroup` holds year+make+model, condition, cylinders, drive, fuel, **odometer**, **title status**, transmission, type. VIN appears here when the seller enters it (REPORTED; absent in the sampled post).
  - `#map[data-latitude, data-longitude, data-accuracy]`.
  - `.postinginfos` gives `post id`, `posted <time datetime>` and `updated <time datetime>`.
  - The body often contains the phone number in plain text.
- **Reposts and renewals (TESTED):** in one 360-item response, 55 items carried a negative cluster ID, and pairs with identical images and price shared the same value. Examples:
  - 2014 Accord: posts 8004050508 and 8003662827 are both in cluster −6.
  - Toyota Sienna: posts 8003690058 and 8002582356, posted two days apart, are both in cluster −4.

  So **a repost is a new posting ID with a new posted time**. Group reposts by image ID or by VIN/title+price, and keep the earliest first-seen date as "days on market". `bundleDuplicates=1` collapses clusters server-side. A renewal keeps the ID and moves `updated` (REPORTED).
- **Also applies to other goods:** the same endpoint serves every for-sale category through `searchPath`, for example `sss`, `tla` (tools), `ela` (electronics) and `fua` (furniture).
- Samples: `samples_small/craigslist_sapi_search.json` (raw plus decoded) and `samples_small/craigslist_listing.json`.

## 3. Facebook Marketplace

- **Logged out (TESTED):** `GET https://www.facebook.com/marketplace/washington/vehicles` returned **400**, "Sorry, something went wrong" (sample `fb_marketplace_vehicles.html`). Vendors report that logged-out guests can get search cards only with Chrome TLS impersonation, while item pages are login-gated (REPORTED, https://apify.com/fmchisti/facebook-marketplace-vehicles-scraper and https://apify.com/crawloop/facebook-marketplace-scraper).
- **What the web client calls (REPORTED):**
  - `POST https://www.facebook.com/api/graphql/` with a form body: `doc_id`, `variables` (JSON), `fb_dtsg`, `lsd`, `fb_api_req_friendly_name`, plus session cookies `c_user` and `xs`.
  - From https://github.com/kyleronayne/marketplace-api (an older but explicit example):
    - Search `doc_id` "7111939778879383", with variables `count:24`, `query`, `filter_location_latitude`, `filter_location_longitude`, `filter_radius_km`, `filter_price_lower_bound/upper_bound`, `commerce_enable_local_pickup`, `custom_request_params{surface:"SEARCH"}`, and `cursor` for paging.
    - Location lookup `doc_id` "5585904654783609".
    - Results at `data.marketplace_search.feed_units.edges[].node.listing` with `page_info{has_next_page,end_cursor}`.
  - **doc_ids rotate with Facebook deploys.** Current projects recapture them with Playwright (https://github.com/jdcodes1/facebook-marketplace-mcp, which self-limits to 3 requests a minute) or harvest them from JS bundles.
  - Vehicle-category browsing uses the same search query with a category ID or the `/marketplace/{city}/vehicles` route, plus URL filters (`minPrice`, `maxPrice`, `maxMileage`, `minYear`, `maxYear`, `carType`, `transmissionType`, `sortBy=creation_time_descend`, `exact=false`, `radius` in km).
- **Field list for vehicle listings (REPORTED, names as returned by the GraphQL):**
  - Search card (`node.listing`), confirmed in the kyleronayne code and the raidr-api output: `id`, `marketplace_listing_title`, `listing_price{amount, formatted_amount, currency}`, `strikethrough_price` (a previous price, which is a free price-drop signal), `primary_listing_photo.image.uri`, `location.reverse_geocode{city, state, city_page.display_name}`, `is_sold`, `is_pending`, `listing_date`/`listing_date_ms`, `marketplace_listing_seller{name, __typename}`.
  - Detail (product page query), confirmed in the raidr-api output: `creation_time`, `description`, `vehicle_make_display_name`, `vehicle_model_display_name`, `vehicle_odometer_data{value, unit}`, `vehicle_condition`, `vehicle_exterior_color`, `vehicle_interior_color`, `vehicle_transmission_type`, `vehicle_fuel_type`, `location{city, state, latitude, longitude}`, seller name. VIN is reported as a detail field by the fmchisti and crawloop actors, but its raw key name was not confirmed.
  - Unconfirmed names, to check in the first captured payload: `custom_sub_titles_with_rendering_flags` (the mileage subtitle on cards), `vehicle_identification_number`, `vehicle_title_status`, `vehicle_seller_type`, `listing_photos`. Sources: https://apify.com/raidr-api/facebook-marketplace-vehicle-scraper, https://github.com/kyleronayne/marketplace-api
- **Browser-extension route (recommended):**
  - A Manifest V3 content script, plus a page-world script that wraps `window.fetch` and `XMLHttpRequest`, can read every `/api/graphql/` response the page itself receives while he scrolls.
  - The initial results are server-embedded in `<script type="application/json" data-sjs>` blobs (Relay preloads), readable from the DOM.
  - The extension then POSTs captured listing nodes to the local server (the `webtoon/extension` skeleton pattern).
  - This avoids replaying doc_ids, uses his own session at human pace, and captures `strikethrough_price` and `is_sold`/`is_pending` over time, which is the only Facebook-side "sold" signal.
  - Also applies to other goods: the same capture works for every Marketplace category.

## 4. Other consumer marketplaces

### OfferUp (TESTED)

- **Search:** `GET https://offerup.com/search?q=honda%20civic` returned 200 (Cloudflare served it, with no challenge).
  - `script#__NEXT_DATA__` (210 KB) has `props.pageProps.searchFeedResponse.looseTiles[]`, of which 50 per page are tiles and most are `tileType: LISTING`.
  - `listing{listingId (uuid), title, price, locationName, vehicleMiles, conditionText, flags[LOCAL_PICKUP...], image.url, isFirmPrice}`.
  - Also `nextPageCursor` (gzip/base64 cursor), `filters[]`, `feedOptions`, and an `initialApolloState` GraphQL cache.
  - A JSON-LD `ItemList` gives name, price, image and `https://offerup.com/item/detail/{listingId}`.
- **Filters seen in the payload:**

  | Filter | Values |
  |---|---|
  | `DISTANCE` | 5, 25, 80, 100, 200, 1500 mi |
  | `PRICE_MIN`, `PRICE_MAX` | dollars |
  | `SORT` | `-posted`, `price`, `vehicle_miles`, `-vehicle_year`, `distance` |
  | `SELLER_TYPE` | `DEALER`, `C2C` |
  | `VEH_YEAR_MIN`, `VEH_YEAR_MAX` | years |
  | `VEH_MAKE` | codes, for example `ac` Acura, `cc` Chevrolet |
  | `VEH_MILEAGE` | mileage band |
  | `VEH_STYLE` | `c`, `s`, `t`, `v` |
  | `VEH_TRANSMISSION`, `VEH_DRIVETRAIN` | options |
  | `CONDITION` | condition values |
  | category | forced `5.1` = Cars & Trucks |

- **Location:** from IP. This machine resolved to Elkton, MD (21921), with lat/lon set in `searchFeedParams`. Adding `&lat=38.9072&lon=-77.0369&radius=25` to the URL **did not move it**; the label stayed Elkton (TESTED). Vendors say the GraphQL `searchParams` lat/lon is what sets the area (REPORTED, https://apify.com/leonardparisi/offerup-scraper.md). So on a GitHub Actions runner the location will be wherever the runner's IP geolocates. Plan on a Playwright session that sets location, or on the extension.
- **Item page:** `GET /item/detail/{id}` returned **403 "Just a moment..."** (Cloudflare challenge, TESTED). VIN and description need a browser.
- Sold data: none.
- Sample: `samples_small/offerup_search_next_data.json`.

### Mercari (TESTED block)

- `GET https://www.mercari.com/search/?keyword=car%20stereo` returned **403 Cloudflare "Just a moment..."**.
- The internal API is GraphQL with persisted-query hashes (REPORTED). The site has a "sold items" filter that is useful for parts and electronics comparables (REPORTED).
- Cars are not sold on Mercari US. It is relevant for other goods only, via a browser.

### Nextdoor For Sale & Free (TESTED)

- `GET https://nextdoor.com/for_sale_and_free/` redirects to `/login/?next=/for_sale_and_free/`.
- Account-only and neighbourhood-scoped. Extension route only. Low car volume.

### Also worth including (REPORTED, not probed)

- **AutoTempest**: an aggregator that includes eBay Motors, Cars.com and Craigslist-like sources. Useful as a cross-check.
- **KSL Classifieds**: Utah only.
- **Kijiji**: Canada.
- Autotrader, Cars.com and CarGurus are dealer-heavy and belong in a separate dealer-sources note.

## 5. Auctions and surplus

### Copart (TESTED shell, REPORTED API)

- `GET https://www.copart.com/lotSearchResults?free=true&query=honda` returned 200 with a 278 KB Angular shell, **no lot data**, and the Imperva script `/_Incapsula_Resource?...` (sample `copart_shell_excerpt.txt`).
- Data comes from `POST https://www.copart.com/public/lots/search-results` with a JSON body `{query:[...], filter:{}, sort, page, size (≤100), start}`. GET returns 405. There is a 10,000-lot cap per query (REPORTED, https://scrape.do/blog/copart-scraping/). Lot detail is at `/public/data/lotdetails/solr/{lot}` (REPORTED).
- Fields (REPORTED): lot number, year/make/model, masked VIN (the full VIN needs membership), odometer and status, primary and secondary damage, title type and state, ACV/est. retail, current bid, buy-now, sale date, yard location.
- **No public sold prices.** Final bids appear on third-party archives such as bidfax, stat.vin and carsbat (REPORTED).
- The POST was not sent from this machine (refused by this session's policy, see top).

### IAAI (TESTED)

- **Search:** `GET https://www.iaai.com/Search?Keyword=honda` returned 200 (Kestrel, Imperva headers, no challenge).
  - Server-rendered result rows: `/VehicleDetail/{id}~US`, thumbnail `https://vis.iaai.com/resizer?imageKeys={id}~SID~I1&width=400&height=300`, year/make/model/trim, stock #, title status, primary and secondary damage, auction date and time, odometer, start code (Run & Drive), airbags, key, colour.
  - JSON blocks `#VehicleRefiners` and `#Facets` hold the facets.
- **Detail:** `GET https://www.iaai.com/VehicleDetail/47176988~US` returned 200.
  - `script#ProductDetailsVM` JSON plus key/value pairs: `ActualCashValue` ($5,475), `AuctionDateTime`, `Odometer` ("109,349 mi (Actual)"), `PrimaryDamage`, `SecondaryDamage`, `StartCode`, `TitleSaleDoc` ("CLEAR (New Jersey)"), `SellingBranch`, `VINMask` ("19XFB2F8XDE******"), `Engine`, `DriveLineType`, `FuelType`, `KeySlashFob`, `Lane`, `Aisle`, `Series`, `BodyStyle`, `ExteriorInterior`.
- **VIN is masked for guests. No sold prices.**
- Sample: `samples_small/iaai.json`.
- Plain stdlib works, so this is a good salvage-pricing source (ACV versus current bid).

### GovDeals (TESTED shell, REPORTED API)

- `GET https://www.govdeals.com/` returned 200 with an Angular shell.
  - `window.__APP_CONFIG__` sets `maestroUrl: https://maestro.lqdt1.com` and ships `maestroApiKey`, `authApiKey` and `ocpApimSubscriptionKey` in the page (redacted in the sample `govdeals_app_config_excerpt.txt`).
  - The app's search posts to maestro (REPORTED, for example https://apify.com/lulzasaur/govdeals-scraper.md); the API was not called here.
- **Sold results:** the site search supports `timeType=sold` with `timingWithinUnit=1-year`. Example from Liquidity Services' own case-study link: `https://www.govdeals.com/search?isAdvSearch=1&timing=bySimple&timeType=sold&timingWithinUnit=1-year&category=...`. Results are kept about one year (REPORTED).
- **DC impounded vehicles unclaimed after 28 days are sold on `dcgovt.govdeals.com`** (DOCUMENTED, https://dpw.dc.gov/service/auto-auction).
- Also applies to other goods: GovDeals sells equipment, tools and electronics.

### GSA Auctions (TESTED)

- `GET https://api.gsa.gov/assets/gsaauctions/v2/auctions?api_key=DEMO_KEY&format=JSON` returned 200. It redirects to an S3 `active-auctions.json` (2.4 MB) holding **115 active lots**.
- Fields: `saleNo`, `lotNo`, `aucStartDt`, `aucEndDt`, `itemName`, `propertyAddr1-3`, `propertyCity/State/Zip`, `auctionStatus`, `locationOrg`, `biddersCount`, `lotInfo` (HTML, often containing the VIN), `reserve`, `aucIncrement`, **`highBidAmount`**, `agencyName`, `itemDescURL` (`https://www.gsaauctions.gov/auctions/preview/{id}`), `imageURL`.
- One call returns everything. There is no paging and no filters. Limits are 5,000 calls a day and 5 per 5 seconds (DOCUMENTED, https://gsa.github.io/auctions_api/basics). A personal api.data.gov key is free.
- **No closed or sold feed.** Polling `highBidAmount` until `aucEndDt` gives a final high bid (an approximation, not a confirmed sale).
- Sample: `samples_small/gsa_auctions_api.json`.

### PublicSurplus (TESTED)

- **Search:** `GET https://www.publicsurplus.com/sms/browse/search?posting=y&keyWord=truck&page=0&sortBy=timeLeft` returned 200 HTML. Rows give state, `#auctionId - title`, price and time left. The `keyWord` param seemed ignored; mixed items came back, so the real search param name needs one more look.
- **Detail:** `GET /sms/auction/view?auc=4125950` returned 200 with title, agency, start and end times (with time zone), pick-up address, payment, high bidder, # of bids, opening price, increment and minimum bid.
- Category and state browse pages exist under `/sms/browse/...`. Closed auctions stay viewable with the final price (REPORTED).
- Sample: `samples_small/publicsurplus_auction.txt`.

### Municibid (TESTED)

- **Browse:** `GET https://municibid.com/Browse/C160883/Vehicles` redirects to `/browse/c160883/vehicles` (200).
  - JSON-LD `ItemList` has 24 items with names and `/listing/{id}/{slug}` URLs.
  - Tiles show location, agency, bid count and current bid.
  - Make pages: `/vehicles/{make}`.
- **Listing:** `GET /listing/86796670/...` returned 200.
  - JSON-LD `@type: ["Product","Car"]` with **`vehicleIdentificationNumber`** (1FTEW1E42KFA37010), **`mileageFromOdometer`** (77,745 SMI), `vehicleModelDate`, `bodyType`, `driveWheelConfiguration`, `vehicleTransmission`, `vehicleEngine`, and `offers{price: 8300, availabilityEnds, seller, availableAtOrFrom.address}`.
  - Best-structured vehicle data of any source here.
- Municibid also advertises its own ChatGPT app, Claude connector and Chrome extension (footer links `/municibid-claude-connector`, not explored).
- Sold view: not tested.
- Sample: `samples_small/municibid_listing_jsonld.json`.

### Bring a Trailer (TESTED, sold prices)

- `GET https://bringatrailer.com/wp-json/bringatrailer/1.0/data/listings-filter?page=1&per_page=24&get_items=1&get_stats=0&sort=td&base_filter[keyword_s]=porsche%20boxster` returned 200 JSON. It needs no auth or nonce for reads.
  - Paging: `items_total` 2165, `pages_total` 91, `page_current`.
  - `items[]{id, title, url, year, current_bid, sold_text ("Sold for USD $18,250 on 11/20/2026" vs "Bid to …"), sold_text_timestamp, timestamp_end, noreserve, country_code, excerpt, thumbnail_url, comments}`.
  - The endpoint URL and `restNonce` are published in `BAT_MODEL_LISTINGS_COMPLETED_TOOLBAR` on `/auctions/results/`.
- Enthusiast cars only, but these are genuine sold comparables.
- Sample: `samples_small/bat_listings_filter.json`.

### Cars & Bids (TESTED)

- `GET https://carsandbids.com/v2/autos/auctions?limit=5&status=closed&offset=0` returned **400** with `{"error_code":3,"message":"Failed to set csrf and signature secret from init cookie: No Session token found.|No Access token cookie"}`. The API needs a browser session and request signing.
- `GET https://carsandbids.com/rss.xml` returned 200 with 206 items (title, link `/auctions/{id}/{slug}`, HTML description with specs). That is live listings and has no sale price.
- `/past-auctions/` is a client-rendered SPA. Sold results need a browser.
- Samples: `carsandbids_rss.xml`, `cab_api_closed.json`.

### Tow, impound, police, bank and credit-union sales

- **HiBid** (TESTED page): `GET https://hibid.com/lots?q=impound%20vehicle&zip=20001&miles=50` returned 200. It is server-rendered with a `script#hibid-state` JSON (10 KB). Many local auctioneers, including tow-lot and estate sales, run on it; the data API is GraphQL (REPORTED).
- **PropertyRoom** (TESTED page): `GET https://www.propertyroom.com/c/vehicles` returned 200 with "1–27 of 27 Results". It is the outlet for police-seized property; Montgomery County police use it for non-vehicle property.
- **Montgomery County, MD police** (REPORTED via search index): monthly abandoned-vehicle auction PDFs at `https://www.montgomerycountymd.gov/pol/Resources/Files/AbandonedVehicleAuctions/{year}/..._POST_{year}.pdf` list case #, year, make, body and VIN. Sales are in person at 305 Metropolitan Grove Rd, Gaithersburg. Info page: https://www.montgomerycountymd.gov/pol/howdoI/vehicle-auction.html
- **DC DPW**: via GovDeals (above).
- **U.S. Treasury general property** (DOCUMENTED, https://www.treasury.gov/auctions/treasury/gp/bidresults.html): **bid-result PDFs** per sale (General Vehicle, Salvage Vehicle and others), posted about two weeks after each sale. Pattern `.../gp/bidresults/fy{YYYY}/{M.D}%20{category}.pdf`. A free sold-price source for seized vehicles.
- **Bank and credit-union repos** (REPORTED): no common platform. Credit unions post their own repo lists (for example https://sccu.com/services/repossessed-auto-listings and https://www.tinkerfcu.org/repos/), and Navy Federal sells repos to members. **RepoFinder** (https://repofinder.com) aggregates bank and credit-union repo sales. Each lender is a separate small reader, best handled with the owner's generic JSON-LD and tile extractors.

## What should change in the plan

1. **Craigslist is the backbone and works with plain stdlib.** Call sapi `search/full` per area with `searchPath=cto`, `sort=date` and price bands to stay under 360, then fetch the listing page only for candidates to get VIN, odometer, title and postal code. Keep a per-image-ID repost index for true days on market. `aptHJunt/aptrack/fetch.py` already fits this.
2. **Sold comparables are scarce.** eBay sold data is closed. Use BaT (enthusiast cars), GovDeals sold search, Treasury PDFs, and the tracker's own observed "last asking price before disappearance" as the main comparable. Treat auction current bid, IAAI ACV and Craigslist asking-price distributions as price evidence, not sale prices.
3. **eBay Browse is worth one key.** Use `category_ids=6001` with the local-pickup filters, `itemStartDate` for increments, and `getItems` only for flagged items (aspects give VIN and mileage). The public eBay site is Akamai-blocked to plain requests.
4. **Facebook and Nextdoor are extension-only,** and OfferUp detail and Mercari need a browser. The webtoon extension skeleton (fetch/XHR wrap → local server) is the route. A GitHub Actions runner's IP will also skew OfferUp's location.
5. **Copart, GovDeals and Cars & Bids data sit behind XHR APIs or bot walls.** Put them in the `tools/harvest.py` Playwright tier, run daily at most.
