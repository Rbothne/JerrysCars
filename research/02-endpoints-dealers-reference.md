# 02 - Endpoints: dealer platforms, aggregators, reference and valuation data

Researched 2026-11-20 from one residential Windows machine using Python 3.14 stdlib `urllib` with a Chrome User-Agent (the same headers as `wishlist-site/build.py`). I kept it to 1-4 requests per host, 3-4 s apart. Scripts and trimmed real responses are in `research/_scratch/endpoints-dealers/` (`scripts/`, `samples/<source>/`). The `SAMPLE_*` files are trimmed extracts of real responses. Other files there are raw captures, such as block pages and robots files.

Evidence labels: **TESTED** means I ran it here. **DOCUMENTED** means I read it in a primary source (URL given). **REPORTED** means second-hand. **UNVERIFIED** means it comes from my prior knowledge with no source checked in this session, and it should be confirmed before anyone builds on it.

## Summary table

| Source | Access route | Auth / cost | Key fields | Plain stdlib request works? | Evidence |
|---|---|---|---|---|---|
| **DealerOn** dealer sites (~23% of franchise sites; 26% with Sincro) | `GET /api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{dealerId}/{pageId}?host=&pn=&pt=` JSON | none | VIN, year/make/model/trim, mileage, stock #, inventory date, MSRP, internet/selling price, fee breakdown, colors, engine, body, dealer city/state | **Yes** (4 of 4 DMV sites) | TESTED |
| **Dealer.com** (Cox; ~33%) | site HTML + `window.DDC` integration API; host on `*.secure.dealer.com.edgekey.net` | none | documented vehicle fields: vin, odometer, trim, finalPrice, startingPrice, msrp, stockNumber, chromeId... | **No**: Akamai 403 on every path, robots.txt included (7 DMV hosts) | TESTED (block), DOCUMENTED (fields) |
| **Dealer Inspire** (Cars Commerce; ~21%) | `/used-vehicles/` SRP; search index reportedly Algolia | none | n/a here | **No**: JS challenge "Dealer Website" 403 (3 DMV hosts) | TESTED (block) |
| **Team Velocity** (~7%) | `/inventory/used?page=N` HTML: 30 schema.org `Vehicle` JSON-LD + `ga4ASCDataLayerVehicle` JS array + card text | none | VIN, price ("All In" in JSON-LD, "Market" in data layer), inventory date, mileage (card text), trim, stock, colors | **Yes** on Fastly-hosted sites (3 DMV); **No** on Akamai-hosted (Milton Martin) | TESTED |
| **Dealer eProcess** (~4%) | `/resrc/xmlsitemap/sitemap-inventory-search/` lists every VDP; SRP/VDP behind Cloudflare | none | from sitemap: VDP URL = condition, year, make, model, trim, listing id; no price | Sitemap **yes**; SRP and VDP **no** (Cloudflare challenge, 3 DMV hosts) | TESTED |
| **DealerSocket / DealerFire** | SRP HTML: `VehicleObject_{id}` JS objects + schema.org `Offer/Product` | none | VIN, **daysInStock, dateInStock**, MSRP, originalPrice, sellingPrice, finalPrice, mileage, trim, styleId, colors | **Yes** (Sheehy, 497 used) | TESTED |
| **Fox Dealer** | `/inventory/?type=used` HTML: schema.org `ItemList` of 100 `Car` | none | VIN, price, mileageFromOdometer, trim (vehicleConfiguration), drivetrain, colors, sku | **Yes** (Wise Auto Group) | TESTED |
| **Overfuel** (small share) | `/inventory` Next.js `__NEXT_DATA__` (25/page); backing API `https://api.overfuel.com/api/1.0/` | none | VIN, **inventorydate, originalprice, price**, msrp, mileage, trim, series, certified, mpg, total count | **Yes** (Fishers Imports, IN; no DMV customer found) | TESTED |
| **Sincro (CDK digital)** / **fusionZONE** | now owned by DealerOn (Sep 2024 / Nov 2023) | n/a | expect DealerOn route after migration | not tested | DOCUMENTED (ownership) |
| **Carsforsale.com** | marketplace search | none | n/a | **No**: Cloudflare "Check the box" 403 | TESTED (block) |
| **TrueCar** | `sitemaps/used/sitemap-listings_{1..21}.xml.gz`; `sitemaps/dealership/...` | none | VIN + year/make/model/trim slug for ~735k used listings, updated daily; ~7,448 dealer pages | Sitemaps **yes**; pages **no** (HUMAN/PerimeterX block) | TESTED |
| **Cars.com** | SRP / VDP | none | n/a | **No**: Cloudflare 403, robots.txt included | TESTED (block) |
| **Autotrader** | SRP | none | n/a | **No**: Akamai "page unavailable" | TESTED (block) |
| **CarGurus** | SRP; robots disallows `/Cars/detailListingJson.action` | none | deal rating, IMV ("expectedPrice"), daysOnMarket, price history (on site) | **No**: DataDome 403; sitemaps are research pages only | TESTED (block), DOCUMENTED (IMV) |
| **Edmunds** | site; developer API retired | partners only | n/a | **No**: Akamai 403, robots.txt included | TESTED (block), DOCUMENTED (API retired) |
| **AutoTempest** | page 200; results via `GET /queue-results?...&token=` (token = hash of params + client secret in JS) | none | meta-search of other sites | page **yes**; results endpoint not called | TESTED (page), DOCUMENTED (from its JS) |
| **iSeeCars** | site blocked; **VIN Insights API** (market value, depreciation, lifespan) | key on request, pricing on request | market value, 3/5-yr depreciation | site **No** (JS challenge) | TESTED (block), DOCUMENTED (API) |
| **Carfax used listings** | site | none | n/a | **No** ("enable JS") | TESTED (block) |
| **Carvana** | site; sitemap is category pages only | none | n/a | **No**: Cloudflare 403 | TESTED |
| **CarMax** | site | none | n/a | **No**: Akamai 403, robots.txt included | TESTED (block) |
| **NHTSA vPIC** | `/api/vehicles/DecodeVinValues/{vin}?format=json`, batch POST (50 VINs), makes/models; monthly standalone DB | free | 154 decoded fields | **Yes** | TESTED |
| **NHTSA recalls / complaints / ratings** | `api.nhtsa.gov/recalls/recallsByVehicle`, `/complaints/complaintsByVehicle`, `/SafetyRatings/...` | free | campaign #, component, summary, remedy; complaints with partial VIN, mileage, dates | **Yes** | TESTED |
| **EPA fueleconomy.gov** | `/ws/rest/vehicle/menu/options`, `/ws/rest/vehicle/{id}` | free | MPG city/hwy/comb, engine, drive, fuel cost | **Yes** (JSON or XML by Accept) | TESTED |
| **NICB VINCheck** | web form with reCAPTCHA | free, **5 searches / 24 h / IP** | theft-unrecovered, salvage/flood (insurer-reported) | **No** API | TESTED (page), DOCUMENTED |
| **MarketCheck** | REST API | Free 500 calls/mo; Basic $299/mo; Standard $749/mo; plus per-call fees | listings, **History by VIN** ($0.006), **MarketCheck Price** ($0.07), dealers, days supply | key required | DOCUMENTED |
| **auto.dev** | REST API | Free 1,000 calls/mo; Growth $299/mo; Scale $599/mo; plus per-call fees | listings, VIN decode, photos (free); specs, recalls, payments, TCO (paid) | key required | DOCUMENTED |
| **CarAPI** | REST API | $199-$299/yr, 1,500-6,000 calls/day | YMM, trims, specs, VIN decode; **no values or listings** | key required | DOCUMENTED |
| **Vehicle Databases** | REST API (`api.vehicledatabases.com/auction/{vin}`, market value, sales history, title...) | subscription; 100 free credits; prices only in an image PDF | trade-in / private / retail x 4 conditions; auction sale price, damage, odometer, photos | key required | DOCUMENTED (prices not extracted) |
| **VinAudit** | Data API: history (NMVTIS), market values, market listings, VIN decode | Trial 100 queries; Self-Service $100/mo + $0.10/query; Enterprise custom | value, listings, NMVTIS title/brand records | key required | DOCUMENTED |
| **KBB** | InfoDriver Web Service (Cox) | license contract, no self-serve | values, specs | no | DOCUMENTED |
| **Black Book** (J.D. Power-owned) | Used Car Web API (GraphQL), developer portal for customers | call for pricing | wholesale, trade-in, retail, private party, residual | no | DOCUMENTED (Canadian Black Book), REPORTED (US) |
| **J.D. Power** (NADA) | Web Services API (VIN Precision+) | call for pricing; reseller pass-through $0.24/valuation + $60.50/mo | used values | no | DOCUMENTED / REPORTED |
| **Manheim UVVI** | monthly + mid-month Cox Automotive release | free | index 206.8 (mid-Nov 2026), segment and EV indices | page yes; data only as a PNG | DOCUMENTED |
| **Manheim MMR** | Valuations API (`developer.manheim.com`), Mashery key | access request; Auction Access dealer credentials for Manheim | VIN-level wholesale value | no | DOCUMENTED |
| **Kaggle Craigslist "Used Cars Dataset"** | Kaggle API, redirects to a signed GCS URL; Range requests work | free, CC0 | 41 columns incl. VIN, price, odometer, seller_type, lat/long, posting_date | **Yes**, even without a Kaggle login | TESTED |
| **Kaggle "US Used cars dataset"** (CarGurus, Sept 2020) | Kaggle | free, research only | 3M rows, 66 cols, 9.98 GB | metadata yes | TESTED (metadata) |
| **Rebrowser CarGurus sample** (Hugging Face) | Parquet daily files | CC-BY-NC sample; full set $2 / 1,000 rows | dealRating, expectedPrice, daysOnMarket, daysAtDealer (VIN/price masked in sample) | free sample | DOCUMENTED |
| **OpenStreetMap Overpass** (dealer discovery) | POST `overpass-api.de/api/interpreter` | free | 355 `shop=car` in DC metro bbox, 106 with website | **Yes** (needs a non-browser tool UA; ~55 s) | TESTED |

Shares come from Provena/Digital Dealer's 16 Nov 2026 classification of 16,948 live US franchise dealer sites, by DNS host: Dealer.com 33%, DealerOn 23%, Dealer Inspire 21%, Team Velocity 7%, Dealer eProcess 4%, long tail 12%. Sincro is counted inside DealerOn (26% by owner). The top three owners hold 80%. https://digitaldealer.com/?p=173681 (DOCUMENTED). The study also reports that about 40% of sites blocked its automated Chrome browser.

## What should change the plan

1. **"One reader per platform" works today for DealerOn, Team Velocity (Fastly-hosted), DealerFire, Fox Dealer and Overfuel with plain stdlib requests.** That is roughly a third of franchise sites. DealerOn alone is about a quarter of franchise sites and has the richest open JSON. Dealer.com (33%) and Dealer Inspire (21%) block plain requests outright, so the other half needs the Playwright harvester or a paid feed. The block is not polite throttling: Dealer.com returns 403 even for `robots.txt`.
2. **Several platforms hand over "days in stock" and an earlier price for free.** DealerFire has `daysInStock`, `dateInStock` and `originalPrice`. Overfuel has `inventorydate` and `originalprice`. DealerOn has `VehicleTaggingInventoryDate` and an MSRP/selling split. Team Velocity has `item_inventory_date`. Our own price history then only has to cover changes after the first sighting.
3. **The TrueCar listing sitemaps are a free national VIN census.** There are 21 files of 35,000 used-listing URLs, each URL carrying VIN, year, make, model and trim, with `lastmod` set to today. A daily diff gives appearance and disappearance dates (a days-on-market proxy) for about 735k VINs without touching a blocked page. There is no price in them.
4. **Dealer discovery needs no requests to dealer sites.** Use OpenStreetMap, OEM locators, state dealer lists or TrueCar's dealer sitemap for the list, then a **DNS CNAME lookup** to identify the platform (table below). DNS classified 50+ DMV domains here at zero load on dealer servers.
5. **The Kaggle Craigslist dataset is current, not 2021.** `vehicles.csv` was re-uploaded 2026-11-05 (1.16 GB, CC0) with postings dated 30 Sep to 2 Nov 2026 and 41 columns. It can be pulled with stdlib HTTP and no Kaggle account, so EDA can start now.
6. **Market value via API is affordable.** VinAudit self-service is $100/mo + $0.10/query. MarketCheck Price is $0.07/call, and its History by VIN (cross-site listing and price history) is $0.006/call. KBB, Black Book, J.D. Power and MMR are contract or dealer-gated.

---

## 1. Dealer website platforms

### 1.0 Fingerprinting (TESTED)

The most reliable signal is the **DNS CNAME of `www.<dealer>`**. It needs no request to the dealer and survives bot blocks. Results are in `samples/discovery/dns_fingerprint_batch.txt`. Page markers in `samples/discovery/homepage_fingerprints.txt` confirm them.

| Platform | CNAME target seen | Page markers |
|---|---|---|
| Dealer.com | `secure.dealer.com.edgekey.net`, `le0NNN.secure.dealer.com.edgekey.net` (Akamai) | 403 "Access Denied" from AkamaiGHost; `/used-inventory/index.htm` URLs (DOCUMENTED in DDC docs) |
| DealerOn | `www.dealeronsite.com` (Fastly IPs 140.248.x, 146.75.x) | `cdn.dlron.us`, `prsnbaa.dealeron.com`, `/searchused.aspx`, `DlronGlobal_DealerId` |
| Dealer Inspire | `podNN.dealerinspire.com`, `ford-sites.dealerinspire.com` (74.119.99.3) | 403 with `<title>Dealer Website</title>` challenge; `/used-vehicles/` |
| Team Velocity | `teamvelocitymarketing.map.fastly.net`, `tvmoffset.map.fastly.net`, `wildcard.teamvelocity.com.edgesuite.net` (Akamai variant, blocked) | `secureoffersites.com` assets, `/inventory/used`, `/viewdetails/used/{vin}/` |
| Dealer eProcess | `saas.www.dealereprocess.org` (Cloudflare) | `cdn.dealereprocess.org`, `/search/used/?tp=used`, `/auto/used-.../{id}/` |
| DealerSocket / DealerFire | `e6lb.dealerfire.com` | `cdn-ds.com` images, `Moff.modules`, `/vehicle-details/used-...-id-{n}` |
| Fox Dealer | `platform.foxdealer.com`, `sites.foxdealer.com.cdn.cloudflare.net` | WordPress `/wp-json/`, `/inventory/?type=used` |
| Overfuel | apex A-records only (AWS Global Accelerator) | `<meta name="generator" content="Overfuel">`, `static.overfuel.com`, `__NEXT_DATA__` |
| Sincro (legacy CDK/Cobalt) | not seen | `/VehicleSearchResults?search=preowned` (UNVERIFIED) |

In the DMV sample, DNS classified: Dealer.com: Ourisman group, Rosenthal, MileOne, BMW of Silver Spring, Hagerstown Honda, Koons Ford, Hertrich's, Hertrich Toyota, Springfield Ford, Radley Chevrolet, Hagerstown Ford. DealerOn: Darcars, Passport, Criswell (all stores), Jerry's Leesburg, Fitzgerald, Alexandria Toyota, Priority, BMW of Sterling, Dulles Kia, Fairfax Honda, Waldorf Honda/Ford/Toyota. Dealer Inspire: Bob Bell (group, Ford, Chevrolet), Tischer, Eastern Shore Toyota, BMW of Annapolis. Team Velocity: Lindsay, Jim Coleman, Ourisman Honda, Jeffrey, Milton Martin (Akamai). Dealer eProcess: Pohanka, Radley, Antwerpen/Jack Says Yes, Sheehy Honda, Honda of Chantilly, Karen Radley VW, Alexandria Hyundai. DealerFire: Sheehy group. Fox Dealer: Wise Auto Group. Koons' group site is custom (Sanity CMS on Cloudflare).

### 1.1 DealerOn (TESTED: Alexandria Toyota, Darcars, Passport, Criswell)

- **Step 1:** `GET https://{host}/searchused.aspx` (HTML, 375-625 KB). Read `"DealerId":"23798"` and `"PageId":2245410` from inline JSON. The page also carries a schema.org `ItemList` with 12 `ListItem`s (url, name, `identifier` = VIN, image) but **no price**.
- **Step 2:** `GET https://{host}/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/{DealerId}/{PageId}?host={host}&pn={pageSize}&pt={pageNumber}`
  - Method GET, no auth, no cookies, `application/json`. I derived the parameter names from `searchResultsPageWasabiBundle.min.js`, where `PageSize="pn"` and `PageNumber="pt"`, and the JS appends `host` itself.
  - Paging: `Paging.PaginationDataModel{PageNumber, PageSize, TotalPages, TotalCount}`. The UI offers pn = 12/24/48/96. I tested 12 and 24.
  - Items: `DisplayCards[].VehicleCard` (skip `IsAdCard`). Fields: `VehicleVin, VehicleYear, VehicleMake, VehicleModel, VehicleTrim, VehicleMileage, VehicleStockNumber, VehicleModelCode, VehicleBodyType, VehicleEngine, VehicleDriveTrain, Exterior/InteriorColorLabel, VehicleInStock, VehicleTaggingInventoryDate` (e.g. `2026/10/25`), `TaggingPrice, VehicleMsrp, VehicleInternetPrice`, `DealerName, DealerLocatedAtCity/State, VehicleComments`, a Carfax link, `ShowDaysOnLot/DaysOnLotLabel` (null here), and `ShouldDisplayPriceDropIcon`.
  - **`VehiclePriceLibrary` is base64 of the full price stack**, e.g. `MSRP:45380.0;Internet Price:40700.0;Selling Price:40700.0;reff_Flat High Price:45380.0;...;calc_Dealer Doc Fee:995.0;calc_INTERNET PRICE:...`. Use `Selling Price` as the asking price. `TaggingPrice` does not always match it.
  - Size: about 50 KB per card (24 cards = 1.3 MB), so use pn=96 and few pages. Group sites return the whole group: darcars.com gave 2,015 used, criswellauto.com 408, passportauto.com 784, alexandriatoyota.com 111.
  - robots.txt: `Crawl-delay: 3`. It disallows `/rss-usedinventory.aspx` and `/vehicle-ajax.aspx` but not `/api/`. The owner's `robots_rules` handles this.
  - Sample: `samples/dealeron/SAMPLE_dealeron_cosmos_srp_vehicles.json`. Reader test: `scripts/dealeron_test.py`.
- Two GETs per dealer per run. No browser needed.

### 1.2 Dealer.com (Cox Automotive), largest share

- **TESTED block:** 7 DMV Dealer.com hosts answered `403 Access Denied` (AkamaiGHost, `errors.edgesuite.net` reference) to stdlib urllib and to curl.exe, on `/` and on `/robots.txt`. Nothing loads without a browser-grade client, so the platform needs the Playwright path (`tools/harvest.py`). I did not try further header or TLS impersonation.
- **DOCUMENTED data model:** the Dealer.com Website Integration API (https://dealerdotcom.github.io/web-integration-api-docs/) exposes `window.DDC.API` in the page. Calls include `API.subscribe('vehicle-shown-v1' | 'vehicle-data-updated-v1' | 'page-load-v1')`, `API.utils.getVehicleData()` and `getAttributeForVehicles(attr)`. Vehicle fields: `vin, year, make, model, trim, odometer, stockNumber, startingPrice, finalPrice, msrp, internetPrice, salePrice, retailValue, askingPrice, certified, bodyStyle, driveLine, engine, exteriorColor, chromeId, inventoryType, status, link, images, accountId, uuid`. SRP URLs: `/{new|used}-inventory/index.htm`. In a Playwright harvest, reading `DDC.API.utils.getVehicleData()` after load is the cleanest extraction.
- **UNVERIFIED (prior knowledge):** the SRP fetches JSON from `/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_{NEW|USED}:inventory-data-bus1/getInventory?start=N`. I found no public source for it this session, and it sits behind the same Akamai block.
- Days in stock and price history are not in the documented fields.

### 1.3 Dealer Inspire (Cars Commerce)

- **TESTED block:** `/used-vehicles/` on bmwofannapolis.com and easternshoretoyota.com, and bobbell.com's homepage, return 403 with a JS challenge page (`<title>Dealer Website</title>`, about 236 KB) behind Cloudflare.
- **UNVERIFIED:** the DI SRP runs on an Algolia index, with the app id and search-only key embedded in the page and one index per dealer. If confirmed in a browser, the harvester would only need the key once per dealer. The owner's `read_algolia` reader in `listings.py` would then query `*.algolia.net` directly, which is not behind the dealer's Cloudflare.

### 1.4 Team Velocity (TESTED: lindsaycars.com, ourismanhonda.com; Jim Coleman fingerprinted)

- `GET https://{host}/inventory/used?paymenttype=cash&instock=true&intransit=true&inproduction=true&page={n}` returns server-rendered HTML of 1.3-2.2 MB with 30 vehicles per page. `CollectionPage/ItemList numberOfItems` gives the total (Lindsay 753, Ourisman Honda 83). I tested page 2: different VINs.
- Data comes from three places in the HTML:
  - schema.org `Vehicle` JSON-LD per car: `vehicleIdentificationNumber, vehicleModelDate, brand, model, vehicleConfiguration` (trim), `sku` (stock), colors, transmission, and `offers.price` (the **"All In"** price including processing fee).
  - `var ga4ASCDataLayerVehicle = '[...]'`: `item_id` (VIN), `item_inventory_date` (**days-in-stock source**), `item_price` (**"Market Price"** before fees), `item_make/model/variant/year`, `item_condition`, `item_fuel_type`.
  - Card text: `Mileage: 47,475 Miles`, drivetrain, location (store).
- Lindsay's group site carries several stores, with a `locations=` filter.
- Akamai-hosted Team Velocity sites (`wildcard.teamvelocity.com.edgesuite.net`, e.g. Milton Martin Honda) return 403. Fastly-hosted ones work.
- Sample: `samples/teamvelocity/SAMPLE_teamvelocity_srp_extract.txt`.

### 1.5 Dealer eProcess (TESTED: Pohanka, Radley, Jack Says Yes)

- The homepage loads, but `/search/used/?tp=used` and VDPs `/auto/used-{year}-{make}-{model}-{trim}/{id}/` return the **Cloudflare managed challenge** ("Just a moment...", 403) on all three.
- **The open route is the sitemap:** `GET /resrc/xmlsitemap/xml-sitemaps/` (index) leads to `/resrc/xmlsitemap/sitemap-inventory-search/` (1.8 MB, 8,115 `<loc>`, 2,178 used VDPs for Pohanka). VIN, price and mileage are not in the sitemap. The URL gives year/make/model/trim and a stable listing id, so it is good for counting inventory and tracking appearance and disappearance per dealer. Prices need the browser.
- robots.txt disallows `/resrc/searchabledata/` and `/resrc/vehicleviews/` (likely the inventory JSON; not probed).
- Sample: `samples/dealereprocess/SAMPLE_dep_sitemap_inventory_search_head.txt`.

### 1.6 DealerSocket / DealerFire (TESTED: sheehy.com)

- `GET https://www.sheehy.com/used-cars-virginia-maryland-and-washington-dc-` returned 200, 2.2 MB HTML, 20 vehicles of "497 Results".
- `Moff.modules.get('DataLayer').pushData('VehicleObject_{vuid}', {...})` carries: `vin, stockNumber, year, make, model, trim, styleId, isNew, mileage, MSRP, originalPrice, sellingPrice, internetPrice, finalPrice, NADARetailPrice, blueBook` (0 here), `daysInStock, dateInStock.date`, colors, engine, transmission, fuelType, description.
- schema.org `Offer`/`Product`/`AggregateOffer` repeats VIN (as `mpn`), price and the selling dealer address. This is a group site with many rooftops.
- Pagination: `?page=2` returned page 1 again. The correct parameter is unconfirmed, so it needs one browser session to read the pager.
- Sample: `samples/dealerfire/SAMPLE_dealerfire_vehicleobject.json`.

### 1.7 Fox Dealer (TESTED: wiseautogroup.com)

- `GET /inventory/?type=used` returned 200, 2.1 MB, behind Cloudflare but no challenge. It contains a schema.org `ItemList` with **100 `Car` items**: `vehicleIdentificationNumber, sku, brand, model, vehicleConfiguration, mileageFromOdometer{value, unitCode SMI}, offers.price, bodyType, driveWheelConfiguration, color`. The URL slug carries the trim. The owner's `from_ld` JSON-LD extractor fits it as is.
- Sample: `samples/foxdealer/SAMPLE_foxdealer_itemlist.json`.

### 1.8 Overfuel (TESTED: fishersimports.com, Indiana; no DMV customer found)

- `GET /inventory` (`?page=N`) returns Next.js HTML. `<script id="__NEXT_DATA__">` holds `props.pageProps.inventory.meta{total, limit 25, offset}` and `results[]`: `vin, stocknumber, inventorydate, originalprice, price, specialprice, msrp, year, make, model, trim, series, body, condition, certified, mileage`, colors, `mpgcity/mpghwy`, `url`, `photocount`. It also lists `apiUrl: https://api.overfuel.com/api/1.0/` (not called).
- **Privacy note for the collector:** `pageProps.clientIp` echoes the caller's IP into the page. I redacted it from saved samples.
- Sample: `samples/overfuel/SAMPLE_overfuel_nextdata_inventory.json`.

### 1.9 Sincro, fusionZONE, Carsforsale.com, others

- **Sincro** (ex-CDK Global Digital Marketing / Cobalt) was acquired by DealerOn from Ansira on 26 Sep 2024, per https://www.ansira.com/press/dealeron-acquires-sincro-from-ansira/ (DOCUMENTED via search summary). **fusionZONE** was acquired by DealerOn on 9 Nov 2023, per https://dealeron.com/?p=14735 (DOCUMENTED). Expect both to converge on the DealerOn route. I found no live DMV example of either.
- **Carsforsale.com** (independent-dealer sites and marketplace): the marketplace search returns a Cloudflare "Check The Box To Continue Shopping" 403 (TESTED). I did not identify a DMV dealer site built on it.
- **Independents** in the OSM sample run on DealersGPT, DealersCloud and other small platforms. For example, maximumautooutlet.com (IIS; images from `cdnimages.dealersgpt.com`) served 200 to a plain request. The long tail will need the generic JSON-LD and tile extractors.

### 1.10 Discovering the dealers in a metro

| Method | Status | Notes |
|---|---|---|
| OpenStreetMap Overpass `nwr["shop"="car"](bbox)` | TESTED | DC metro bbox 38.60,-77.60,39.20,-76.80: 355 features, 106 with `website`, 77 tagged `second_hand`. Overpass returned 406 to a browser UA and accepted a plain tool UA; about 55 s per query. Sample: `samples/discovery/osm_overpass_dmv_shopcar.json` |
| DNS CNAME classification | TESTED | `Resolve-DnsName` / `socket` lookup of `www.` host; see 1.0 |
| TrueCar dealership sitemap | TESTED | `https://www.truecar.com/sitemaps/dealership/sitemap-dealership_1.xml.gz`: 7,448 `/dealership/{slug}-{id}/listings/` URLs, national, slug only (no state) |
| OEM dealer locators | DOCUMENTED as the method Provena used for its 16,948-site census | per-brand JSON locators; not probed here |
| Virginia MVDB active-dealer search | DOCUMENTED | https://mvdb.virginia.gov/search-active-dealers/ (search UI, no bulk download found) |
| Maryland MVA "dealer book" | DOCUMENTED | written request to Business Licensing and Compliance Division, https://mva.maryland.gov/your-mva-guide/businesses/vehicle-dealers-title-services/dealership-resources |
| Group sites | TESTED | DealerOn and Team Velocity group domains (darcars.com, lindsaycars.com) return all rooftops in one feed and list sibling store domains in their footers |

---

## 2. Aggregators

All TESTED with a single plain GET of a DMV search page (zip 22301) on 2026-11-20, plus robots.txt.

| Site | Plain request result | Internal route / notes | Price history / market value |
|---|---|---|---|
| Cars.com | 403 Cloudflare (robots.txt too) | none reachable | site shows price drops and "deal" badges; no open route |
| Autotrader | 200 but "page unavailable" body (AkamaiNetStorage, incident number) | none reachable | KBB price advisor on site |
| CarGurus | 403 `Server: DataDome` | robots disallows `/Cars/detailListingJson.action` (the VDP JSON). `sitemap_index.xml` (S3) has 18+ files of research and compare pages, no listings | **Deal rating vs IMV** (DOCUMENTED: IMV = estimated fair retail price from comparable current and previous listings, updated daily, https://cargurus.helpscoutdocs.com/article/10-what-is-imv); price history and days on market shown on site. The Rebrowser dataset exposes `expectedPrice, priceDifferential, dealScore, dealRatingKey, daysOnMarket, daysAtDealer` |
| TrueCar | 403 "Access to this page has been denied" (HUMAN/PerimeterX) | **Sitemaps open (TESTED):** `sitemaps/used/used-sitemap-index.xml` lists `sitemap-listings_1..21.xml.gz`, each 35,000 `used-cars-for-sale/listing/{VIN}/{year}-{make}-{model}/` URLs, lastmod 2026-11-20. robots disallows `/api/` | TrueCar shows market price bands on VDPs (not reachable) |
| Edmunds | 403 Akamai (robots.txt too) | developer API retired: "no longer able to offer our Developer Open API" (https://help.edmunds.com/hc/en-us/articles/4414038118679-Edmunds-Developer-API); dealers can request partner access via their account executive | TMV on site; not reachable |
| AutoTempest | **200** (Cloudflare, no challenge) | From `results.*.js`: results come from `GET {SITE_ROOT}queue-results?{params}&token=...`, where token is a hash of the decoded query string plus a constant in the bundle; `/api/results/duplicateListings`. It meta-searches other sites (each `sites=` code is a source). Not called | none of its own |
| iSeeCars | 403 JS challenge | **VIN Insights API** (DOCUMENTED, https://www.iseecars.com/vin-insights-api): market value, 3/5-year depreciation, remaining lifespan; 1-50 vehicles per request; key and pricing on request | market value via API |
| Carfax used listings | 403 "Please enable JS" (CloudFront) | robots disallows `/api/`, `/consumer-api-gateway/`, `/vrs` | history-based value on site |
| Carvana | 403 Cloudflare | robots disallows `/api/` and `/`; `sitemap_0.xml.gz` holds 50,000 category URLs (`/cars/{year}`...), no VDPs | n/a |
| CarMax | 403 Akamai (robots.txt too) | UNVERIFIED prior knowledge: SRP JSON at `/cars/api/search/run` | n/a |

For aggregators the plain collector gets only sitemaps (TrueCar is the useful one). Everything else needs a browser, a paid feed (MarketCheck indexes these sites), or a licensed dataset.

---

## 3. Free reference data (all TESTED, plain stdlib)

### NHTSA vPIC: https://vpic.nhtsa.dot.gov/api/
- `GET /api/vehicles/DecodeVinValues/{VIN}?format=json[&modelyear=YYYY]` returns `{Count, Message, SearchCriteria, Results:[{154 flat fields}]}`. Fields include `Make, Model, ModelYear, Trim, Series, BodyClass, Doors, DisplacementL, EngineCylinders, FuelTypePrimary, DriveType, TransmissionStyle, GVWR, PlantCountry, VehicleType, ErrorCode`. 0.3 s. Sample `samples/reference/vpic_decodevinvalues.json`.
- `POST /api/vehicles/DecodeVINValuesBatch/` with form `format=json&data=VIN1;VIN2;...` (optionally `VIN,year`) decodes **up to 50 VINs per call**. TESTED with 3 in 0.34 s. A GET returns 405. Sample `vpic_batch_post.json`.
- `GET /api/vehicles/GetModelsForMakeYear/make/{make}/modelyear/{yyyy}?format=json`, plus GetAllMakes, GetMakesForVehicleType and others. Sample `vpic_models_toyota_2017.json`.
- Limits: "automated traffic rate control mechanism", no number published. "There are quotas and rate limits ... you can avoid reaching the limits by using the standalone databases."
- **Standalone DB, monthly (TESTED page):** `https://vpic.nhtsa.dot.gov/downloads/vPICList_lite_2026_11.bak.zip` (MS SQL, 180 MB, updated 11/14/2026), plus `.custom.zip` and `.plain.zip` PostgreSQL 17 dumps (about 67 MB; schema `vpic`). VIN decoding only. This is the right choice for bulk decoding in the tracker.

### NHTSA recalls, complaints, ratings: https://api.nhtsa.gov
- `GET /recalls/recallsByVehicle?make=&model=&modelYear=` returns `{Count, results:[{NHTSACampaignNumber, Manufacturer, Component, Summary, Consequence, Remedy, ReportReceivedDate (dd/mm/yyyy), parkIt, parkOutSide, overTheAirUpdate, ...}]}` (2012 Elantra: 4).
- `GET /complaints/complaintsByVehicle?make=&model=&modelYear=` returns `{count, results:[{odiNumber, crash, fire, numberOfInjuries, numberOfDeaths, dateOfIncident, dateComplaintFiled, vin (11 chars), components, summary, products[]}]}` (2012 Elantra: 676 complaints, 650 KB, 3.1 s).
- `GET /SafetyRatings/modelyear/{y}/make/{m}/model/{md}` returns VehicleIds, then `/SafetyRatings/VehicleId/{id}` gives star ratings.
- No VIN-level open-recall API was found. NHTSA's VIN lookup is a web form.

### EPA fueleconomy.gov: https://www.fueleconomy.gov/ws/rest/
- `GET /vehicle/menu/options?year=&make=&model=` returns `{menuItem:[{text:"Auto 6-spd, 4 cyl, 1.8 L", value:"31216"}]}`, then `GET /vehicle/{id}` returns about 80 fields (`city08, highway08, comb08, displ, cylinders, drive, fuelType, trany, co2TailpipeGpm, fuelCost08, youSaveSpend`...). It returns JSON when `Accept: application/json`, XML otherwise. Bulk download: `https://www.fueleconomy.gov/feg/epadata/vehicles.csv.zip` (DOCUMENTED on fueleconomy.gov; not fetched).

### NICB VINCheck: https://www.nicb.org/vincheck
- Free web form with reCAPTCHA and terms checkbox; no API. It reports "stolen but not recovered or reported as a salvage or flood-damaged vehicle by participating NICB member insurance companies", and the page states "a maximum of five searches within a 24-hour period per IP address". Use it by hand on shortlisted cars only. For automated title/brand checks use an NMVTIS provider (VinAudit, below).

---

## 4. Valuation and listing-data products (DOCUMENTED unless noted; prices as published 2026-11-20)

| Product | Developer API today? | Returns | Published pricing | Source |
|---|---|---|---|---|
| **Kelley Blue Book** | InfoDriver Web Service (IDWS), licensed by Cox Automotive; no self-serve keys | trade-in, private party, retail values; specs; 5-yr cost to own | none published; contract per use case (consumer site, industry app, internal use) | https://www.coxautoinc.com/terms/usa/ (InfoDriver Additional Terms PDFs) |
| **Edmunds** | **No** (open API retired; partners and dealers via account executive only) | n/a | n/a | https://help.edmunds.com/hc/en-us/articles/4414038118679-Edmunds-Developer-API |
| **Black Book** (J.D. Power) | Yes for customers: Used Car Web API (REST and GraphQL), developer portal with test harness | wholesale, trade-in, retail, private party, residual; VIN decode | "call for pricing" | https://www.canadianblackbook.com/api/ , https://developer.canadianblackbook.com/ (Canadian arm; US REPORTED) |
| **J.D. Power Valuation Services** (ex-NADA) | Yes, Web Services API (REST, VIN Precision+) | used car / LDT / commercial truck values | "contact us"; REPORTED reseller pass-through (CU*Answers, Oct 2024): $60.50/mo + $0.24/valuation | https://www.jdpower.com/business/web-services-api/ |
| **MarketCheck** | Yes, self-serve | inventory search (active and recent, all major sites), **History by VIN** (listing/price history), **MarketCheck Price** (predicted price), dealers, market days supply | Free: 500 calls/mo, 5 req/s, 100-mile radius; Basic $299/mo + data fees (5,000 calls); Standard $749/mo + data fees (unlimited); per-call: search $0.002, History by VIN $0.006, Price $0.07, dealer $0.0025 | https://www.marketcheck.com/apis/pricing (a search snippet showed Basic at $749; the page I fetched shows $299) |
| **auto.dev** | Yes, self-serve | listings, VIN decode, photos (free tier); specs, OEM build, payments, recalls, TCO (Growth); plate-to-VIN, open recalls (Scale). No valuation listed | Free 1,000 calls/mo (no card); Growth $299/mo ($249 annual) + per-call; Scale $599/mo ($499 annual) + per-call | https://www.auto.dev/pricing |
| **CarAPI** | Yes | YMM, trims, specs, VIN decode, OBD codes. **No values or listings** | $199 / $249 / $299 per year for 1,500 / 3,000 / 6,000 calls/day; overage $0.001/call opt-in | https://carapi.app/pricing |
| **Vehicle Databases** | Yes | Market Value (trade-in, private party, dealer retail x Outstanding/Clean/Average/Rough), Auction History `GET https://api.vehicledatabases.com/auction/{vin}` (sale price, date, location, damage, title type, odometer, photos), Sales History, Title Check, VIN decode, recalls, warranty, window sticker | subscription; "100 Free Credits"; the price sheet is only an image PDF (`/pricing` redirects to `/pricing.pdf`, 7 MB, no extractable text) | https://vehicledatabases.com/api/vehicle-market-value , /api/auction-history |
| **VinAudit** | Yes | Vehicle History (NMVTIS), Market Values, Market Listings, VIN decode, ownership cost | Trial: 100 queries; Self-Service $100/mo + $0.10/query (qualifying developers and startups); Enterprise custom | https://data.vinaudit.com/pricing |
| **iSeeCars VIN Insights** | Yes, on request | market value, 3/5-yr depreciation, remaining lifespan | on request | https://www.iseecars.com/vin-insights-api |
| **Carfax** | No open API; enterprise agreements (dealers, lenders, insurers) | history reports, service records | none published | REPORTED (https://apis.io/providers/carfax/) |
| **AutoCheck** (Experian) | No open API found | history score | none found | not found |
| **Manheim MMR** | Valuations API at developer.manheim.com; needs a Mashery package key via access request or DataSyndication@coxautoinc.com; Manheim marketplace access needs Auction Access dealer credentials (dealer license, W-9) | VIN-level wholesale value adjusted for mileage, region, condition | none published | https://developer.manheim.com/apis/marketplace/valuations.html , https://site.manheim.com/tutorials/new-dealer-registration-faqs |

**Public wholesale indicators**
- **Manheim Used Vehicle Value Index** (Cox Automotive; free; monthly at month start plus a mid-month update). Mid-November 2026 (published 18 Nov): **206.8**, unchanged vs October, +0.7% YoY; non-adjusted -0.7% MoM, -0.1% YoY. EV index +3.4% YoY. Compact, EV and midsize segments were up YoY; luxury, SUV/CUV and pickups were down. "Download the Data" is a **PNG table**, so plan on transcribing it monthly. https://www.coxautoinc.com/insights/manheim-used-vehicle-value-index-mid-november-2026-trends/
- Restricted to licensed dealers or contracts: MMR VIN values, Manheim/ACV/ADESA auction results, Black Book and J.D. Power wholesale guides, vAuto/Stockwave. The closest legal stand-ins for a non-dealer are MarketCheck Price, VinAudit Market Values, Vehicle Databases Market Value, and its Auction History for salvage and insurance auctions.

---

## 5. Public datasets for EDA now

| Dataset | Size | Dates | Fields | Download | Evidence |
|---|---|---|---|---|---|
| **Kaggle "Used Cars Dataset" (Craigslist), austinreese/craigslist-carstrucks-data** | `vehicles.csv` 1,163,344,787 bytes (260 MB compressed per listing); CC0; 124k downloads | **re-uploaded 2026-11-05; postings 2026-09-30 to 2026-11-02** (head and tail checked) | 41 cols: id, url, region, price, year, manufacturer, model, condition, cylinders, fuel, odometer, title_status, transmission, VIN, drive, size, type, paint_color, description, state, lat, long, posting_date, **seller_type**, title, updated_date, address_*, image_count, image_urls, delivery_available, odometer_broken, odometer_rolled_over, monthly_payment, other_attributes | `GET https://www.kaggle.com/api/v1/datasets/download/austinreese/craigslist-carstrucks-data/vehicles.csv` returns a 302 to a signed `storage.googleapis.com` URL, raw CSV; **no Kaggle login needed and HTTP Range works** (TESTED). Older snapshots are in the Kaggle version history; source scraper https://github.com/AustinReese/UsedVehicleSearch | TESTED |
| Zenodo copy of the same (DOI 10.5281/zenodo.10457828) | 275 MB zip | v1 published 2024-01-04 | same family | https://zenodo.org/records/10457828 | DOCUMENTED |
| **Kaggle "US Used cars dataset"** (ananaymital/us-used-cars-dataset) | 9.98 GB, 3M rows, 66 cols | CarGurus crawl, Sept 2020 | includes dealer, days on market, price, mileage, VIN, options | Kaggle (login for CLI) | TESTED (metadata) |
| **Rebrowser CarGurus listings** (Hugging Face `rebrowser/carguruscom-dataset`) | full 15,169,651 records; free sample ≤1,000 rows/day, last 30 days | 2025-12-07 to 2026-11-15, daily | `dealRatingKey, expectedPrice, priceDifferential, dealScore, daysOnMarket, daysAtDealer, _firstSeenAt, _lastSeenAt`, mileage, YMMT, seller city/state/zip; VIN, price and seller name masked in the sample | Parquet via HF; full set $2 per 1,000 rows; CC-BY-NC sample | DOCUMENTED |
| TrueCar listing sitemaps (self-built) | ~735k VINs/day | live | VIN, YMM(T) | 21 gz files, plain GET | TESTED |
| NHTSA vPIC standalone DB | 67-180 MB | monthly | VIN decoding tables | see section 3 | TESTED |
| NHTSA complaints / recalls flat files | | | | https://www.nhtsa.gov/nhtsa-datasets-and-apis (DOCUMENTED by reference; not fetched) | |
| EPA `vehicles.csv.zip` | | 1984-present | ~80 cols MPG/specs | fueleconomy.gov/feg/epadata | not fetched |

---

## Limits observed (exact)

- Akamai `403 Access Denied` for every path, robots.txt included: Dealer.com hosts, CarMax, Edmunds, Akamai-hosted Team Velocity. Autotrader serves a 200 "page unavailable" body instead.
- Cloudflare managed challenge (403 "Just a moment..."): Dealer eProcess search and VDP pages, Cars.com (robots.txt too), Carvana. Cloudflare "check the box": Carsforsale.com.
- Dealer Inspire JS challenge 403 (`<title>Dealer Website</title>`).
- DataDome 403: CarGurus. HUMAN/PerimeterX "Access to this page has been denied": TrueCar pages (sitemaps open). JS challenge: iSeeCars, Carfax.
- Overpass: 406 for a browser User-Agent, 200 for a plain tool UA; 50-57 s per metro query.
- No 429 was seen anywhere. DealerOn asks `Crawl-delay: 3`.

## Files

- Scripts: `research/_scratch/endpoints-dealers/scripts/`: `probe.py` (polite fetcher and fingerprint), `fingerprint.py`, `dealeron_test.py` (DealerOn reader proof), `jkeys.py` (JSON field lister), `osm_dealers.py` (Overpass discovery), `fox_sample.py`, `pdftext.py`, `trim_samples.py`.
- Samples: `research/_scratch/endpoints-dealers/samples/{dealeron,teamvelocity,dealerfire,foxdealer,overfuel,dealereprocess,dealerinspire,dealercom,carsforsale,aggregators,reference,datasets,discovery}/`.
