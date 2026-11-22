# 11. More places private and forced sellers list cars around Memphis

Worked 2026-11-21 (a Saturday) from a home connection. Plain urllib GETs only: no account, no browser, no cookies kept,
no internal API called, no extra browser headers. A Chrome user-agent string throughout; where a wall was met with it,
the tool's own `cartrack/0.1` was tried once (Autotrader) and met the same wall. 113 requests to 41 hosts: 10 to
offerup.com, 7 to its sitemap host, 8 that reached the Gannett classifieds host (two by redirect), 6 to
estatesales.net, 5 or fewer to every other. At least 3 s between requests to a host, 20 s on the Gannett host once
its crawl delay was read. No working route was repeated with the tool's own user agent, so "plain" below means a
plain request carrying a browser's user-agent string.
robots.txt was fetched before any page on every host and its rules for `*` were applied by the probe itself.
Scripts, the request log and trimmed samples are in `research/_scratch/routing/marketplaces/`: `probe.py` (robots
first, pacing, a cap per host), `batch.py`, `probe_log.tsv` (every request with its status), `ou.py`, `mdn_look.py`,
`mdn_parse.py`, `cap/` (raw answers), and the samples named in each section.
Labels: TESTED = fetched and seen here, DOCUMENTED = read in the source's own text, REPORTED = second-hand (a search
engine's summary of a page counts as REPORTED, even when the page is the operator's own).

**The main finding: the one new place with real private-seller volume is OfferUp, and its terms forbid reading it
with a program.** A Memphis page exists, is asked for by city name in the path, is allowed by robots.txt, answers a
plain request and holds about 1,000 cars within 30 miles. That is for the owner to decide, not for a reader to assume.
Everything else is either walled (every big car site), nearly empty (every newspaper's classifieds: 0 or 1 vehicle),
stale (Autopten, Oodle), or not a car listing at all (estate sales name a car in passing). Two things are worth
building without asking anyone: the Daily News notices, whose parsing is settled below, and a second, smaller set of
lien-sale notices in the Commercial Appeal that the Daily News does not carry.

## Verdict

| Place | Vehicles around Memphis today | Private or forced sellers? | Public page readable by a plain request? | What its terms say | Worth a reader? |
|---|---|---|---|---|---|
| **OfferUp**, `offerup.com/c/cars-and-trucks/in/memphis-tn` | **about 1,005** within 30 miles (20 full pages of 50 and 5 on page 21); of 200 sampled, about half look private by the form of the price | both, mixed; the card does not say which | **yes** (200, Cloudflare, no challenge); robots.txt allows this path and `?page=N` | **forbids it**: no "automated means ... to collect or extract data ... such as a harvesting bot, robot, spider, script, crawler, or scraper" (terms of 21 July 2026) | **owner's decision.** Technically the best new source here; by its terms, no |
| **The Daily News** lien-sale notices (found in note 10) | 265 distinct VINs in 47 notices over six days' pages | forced (tow, garage, storage liens) | yes, one request a day | no terms page is open to robots (`Disallow: /` apart from the notices and five other paths) | **yes, first.** Split settled: 97% of VINs get year and make words that agree with the VIN |
| **Commercial Appeal**, Legals > Auto Auction (Gannett classifieds) | **2 notices this week, 8 VINs, none of them in the Daily News** | forced (a dealer's lot auction, a tow lot's lien sale) | yes; robots.txt allows the category and advert pages, **crawl delay 20 s** | terms page is a script shell; not read | **yes, small**: 3 requests a day, same parser as the Daily News |
| Commercial Appeal, Automotive classifieds | **1** (a wheelchair van, posted 27 Oct) | private | yes | same | no |
| Jackson Sun classifieds (same Gannett platform) | 0 (one home-improvement ad, one public notice) | - | yes | same | no |
| **eBay Motors** (Browse API) | not testable without a key | both; the answer carries `seller.sellerAccountType` | n/a: documented API, needs the owner's key | API License Agreement; Buy APIs page says production use is "for eBay partners only" | **yes, once the owner has a key** (section 3 says how) |
| Autotrader (private-seller ads exist, $9 to $49) | not readable | private sellers yes | **no**: Akamai "page unavailable" page, for the browser string and for `cartrack/0.1` | not read (walled) | no |
| KBB (shows Autotrader's ads) | not readable | same ads as Autotrader | **no**: 403 Akamai "Access Denied" | not read | no |
| Cars.com (free private listings) | not readable | private sellers yes | **no**: Cloudflare challenge on robots.txt itself | not read | no |
| CarGurus | - | **none**: private listings ended in June 2024 | no: 403 DataDome | - | no |
| Edmunds, TrueCar, CarsDirect, Carfax listings | - | dealers only (Edmunds and CarsDirect: sources conflict) | Edmunds 403 Akamai, TrueCar 403 HUMAN, CarsDirect Cloudflare challenge; Carfax's landing page answered 200 | not read | no |
| PrivateAuto | **0** ("We didn't find any matches") | private only | yes | not read | no; a watcher at most |
| DeSoto Times-Tribune classifieds | **0** Cars & Vehicles | - | landing page yes; the vehicle page answered **429** | not read | no |
| Jonesboro Sun classifieds | **1** (2019 Ford Flex, $7,300) | private | yes | not read | no |
| Daily Journal (Tupelo) classifieds | 0 | - | yes | not read | no |
| Daily Memphian marketplace | 0 (one category, Employment, with 0 ads) | - | yes | not read | no |
| West Memphis Evening Times, Covington Leader, Oxford Eagle | not read | - | 429 on robots.txt; certificate does not match the host; `/classifieds/` is 404 (its ads live on an AdHunter site, not opened) | - | no |
| Thrifty Nickel, American Classifieds | - | - | both domains answer with a parked-domain robots.txt ending `Disallow: /`; nothing fetched | - | no |
| **Autopten** (cheap-car board) | 356 Tennessee cars on the page, but it is an archive; 103 new cars **nationwide** in six months, 8 in Tennessee, all one dealer in Bolivar | both | yes, HTML and an RSS feed, robots allow | no rule on automated reading found | no: almost nothing new, and old ads are never removed |
| Oodle | facets say 22,276 dealer and **414 private party** for the Memphis area; 13 of the 15 cars shown are over four weeks old, from AmericanListed | both | first page yes; the private-party page answered 404 twice | **forbids** "automated means, including spiders, robots, crawlers, data mining tools" | no |
| Geebo, ClassifiedAds, AmericanListed, Recycler, Claz | not established | - | my guessed addresses led nowhere (see section 4) | - | no |
| **EstateSales.net**, `/TN/Memphis` | **28 sales**; 1 of 3 sale pages opened names a car ("Dependable 2010 Toyota Prius") | forced, in a sense (estates) | yes, with schema.org `SaleEvent` blocks | **forbids** using any "engine, software, tool, agent ... (including ... spiders, robots ...) to harvest or otherwise collect information from the Service" | no reader. A car is a phrase in a description: no price, VIN or miles |
| EstateSales.org | 0 ("No estate sales currently listed near Memphis, Tennessee") | - | yes | robots.txt disallows `/terms`; not read | no |
| StorageTreasures, StorageAuctions.com, Lockerfox | not readable | forced (storage liens) | script shells; Lockerfox robots.txt disallows `/auctions/` | not read | no |
| Tennessee Abandoned Vehicle Portal, partner API | 7 for the one search note 10 sent | forced | list endpoints need a key | keys go "to approved integration partners"; **no application route is published** | ask, as note 10 said; nothing more to learn from the pages |

## 1. OfferUp (TESTED: a Memphis page by name, plain; terms forbid it)

### Pages

- robots.txt (`offerup.com/robots.txt`, 200). For `*` it **disallows `/search`** (allowing only `/search$` and
  `/search?cid=`) and any address containing `q=`, `sort=`, `radius=`, `price_min=`, `price_max=`, `condition=`,
  `veh_make=`, `veh_type=`, `veh_year_min=`, `veh_year_max=`, `veh_mile_max=`. It disallows `/api/` except
  `/api/graphql$`. It names eleven sitemaps on `c.offerup.com`. **Correction to note 01:** the address tested there,
  `/search?q=honda%20civic`, is disallowed by these rules.
- Sitemaps (TESTED): `c.offerup.com/explore-cities-sitemap-0.xml.gz` lists 776 city pages as `/in/{city}-{st}`,
  among them `memphis-tn`, `jackson-tn`, `jonesboro-ar`, `tupelo-ms`, `little-rock-ar` (no Southaven, Olive Branch
  or West Memphis). `explore-categories-sitemap-0.xml.gz` lists 1,244 categories as `/c/{slug}`, among them
  `cars-and-trucks`, `vehicles`, `motorcycles`, `trailers`, `campers-and-rvs`. `explore-regional-topics-sitemap-0`
  (49,000 addresses, the first of ten files) joins them as `/c/cars-and-trucks/{topic}/in/memphis-tn`
  (`chevy`, `chevy-suburban`, ...).
- **`GET https://offerup.com/c/cars-and-trucks/in/memphis-tn`** (TESTED, 200, 870 KB, no challenge). The category and
  the city are both in the path. `script#__NEXT_DATA__` holds `props.pageProps`:
  - `searchFeedParams`: `lat 35.1495343`, `lon -90.0489801`, `category_slug cars-and-trucks`, `limit 50`, `page 1`.
    That is the home point to four decimals. `city`: `{id: memphis, radius: 20, state: {id: tn}}`.
  - `appProps.location` still says where my connection is (`source: ip`), and it does not matter: the search is
    placed by the path. So note 01's worry about a runner's IP address does not apply to this page.
  - The distance filter reports **30 miles** selected (options 5, 25, 30, 80, 100, 200, 1500). Changing it needs
    `radius=`, which robots.txt disallows. 30 miles reaches Olive Branch, Southaven, Millington, Arlington and Munford
    in what I saw.
  - Sort is "Recent first" (`-posted`) by default. Changing it needs `sort=`, disallowed.
- **Paging:** `<link rel="next" href=".../in/memphis-tn?page=2">`; `paginatedOptions.pageNumberLimit` is 50. Pages
  2, 10 and 17 are full (50 tiles), page 21 has 5, pages 25 and 50 have none. So **about 1,005 tiles**. A daily run
  that wants only new cars reads from page 1 until it meets cars it has seen.
- Seller filter: the payload lists `SELLER_TYPE` with `All sellers`, `Verified dealer` (`DEALER`) and `Private seller`
  (`C2C`). I did not find a robots-allowed address that sets it, and did not guess one. The page's own filter goes
  through its GraphQL call, which is an internal API and was not touched.
- Item pages (`/item/detail/{uuid}`): not requested today. Note 01 found them behind a Cloudflare challenge.

### What a card gives

`looseTiles[]`, each with `tileType` (`LISTING`, or `AD_1P` for a paid seller tile that still carries a listing) and:

| Listing field | From |
|---|---|
| `source`, `source_id` | `offerup`, `listing.listingId` (a uuid) |
| `url` | `https://offerup.com/item/detail/{listingId}` (also in the page's JSON-LD `ItemList`) |
| `title`, `year`, `make`, `model` | `listing.title` ("2012 Toyota Camry"); 189 of 200 start with a year. Free text: "300c", "Chevy Caprice" and a "Cab Corner For 2007-2013 GMC" (a part) were among them |
| `price`, `price_kind` | `listing.price` (a string, "3500" or "13995.00"), `ask` |
| `miles` | `listing.vehicleMiles` (absent on 33 of the 200 sampled, 24 of them round-priced cards) |
| `city`, `state`, `geo_how` | `listing.locationName` ("Memphis, TN"), `city` |
| `photos` | `listing.image.url` (one, 333x250 or 444x250) |
| `seller_type` | **not on the card.** Only the filter knows |
| `channel` | `marketplace` |
| `posted`, `vin`, description, seller | **not on the card** |

Sample: `offerup_memphis_tiles_sample.json`.

Who is selling (TESTED counts, my reading of them): the 200 distinct listings on pages 1, 2, 10, 17 and 21 fall into
three groups by how the price is written.

| Price as written | Listings | Median | Under $5,000 | Where | Reads as |
|---|---|---|---|---|---|
| whole dollars, not a multiple of $50 (`20591`), nearly always with an exact odometer figure | 73 | $25,141 | 1 | 49 Olive Branch, 22 Memphis | dealer stock fed in by a program |
| whole dollars, a multiple of $50 (`3500`) | 87 | $4,000 | 54 | 77 Memphis, 4 Cordova | private sellers, mostly |
| with cents (`2499.00`, `3000.00`) | 40 | $3,500 | 26 | 38 Memphis | mixed: 13 are $x,999 or $x,995 lot prices, the rest round |

So roughly half of what the page holds looks private, and it is the cheap half. This is a guess from the form of
the price, not a field; only the seller filter knows. The first pages are heavy with dealer feeds; page 17 is 47 of
50 in Memphis with prices from $200 to $12,500 (and two parts at $30 and $65).

### Terms (DOCUMENTED, `offerup.com/terms`, "Last updated: July 21, 2026")

Among the things a user must not do: "Use any type of automated means to utilize the OfferUp Services or to collect or
extract data from OfferUp, such as a harvesting bot, robot, spider, script, crawler, or scraper, not provided by
OfferUp". Also no "third-party applications that interact with the OfferUp Services without OfferUp's prior written
consent". So robots.txt opens the page to crawlers and the terms close it to this tool. **A wall by terms.** I read
the terms after the pages (see "Mistakes") and stopped at ten requests.

## 2. Private sellers on the big car sites

Each site's robots.txt was read first. None of the eight gave a private-seller search to a plain request.

| Site | Private sellers today? | robots.txt | What one plain request met |
|---|---|---|---|
| Autotrader | **Yes.** Its sell page offers private ads at $9, $29 or $49, shown "on Autotrader and KBB.com" (REPORTED, search summary of `autotrader.com/sell-my-car` and `/sell-car`) | 200. For `*`: long list of internal paths, `*keyword=`, and the odd line `Disallow: *zip=[zipcode]*`, which I took to mean any `zip=` query and so used the path form | `GET /cars-for-sale/by-owner/memphis-tn`: 200, a 3.7 KB Akamai page titled "Autotrader - page unavailable" with an incident number. Same for `cartrack/0.1`. Stopped |
| KBB | Shows Autotrader's ads: "any Autotrader posting also appears here" (REPORTED, search summary of a kbb.com article) | 200; nothing bars `/cars-for-sale/` | `GET /cars-for-sale/by-owner/memphis-tn/`: **403** "Access Denied" (AkamaiGHost). Stopped |
| Cars.com | **Yes**, free: "no costs or hidden fees to selling your car yourself on Cars.com" (REPORTED, search summary of `cars.com/sell`). Whether shoppers can filter to private sellers is disputed in what I found | **403**, a Cloudflare "Just a moment..." challenge in place of robots.txt | Nothing further requested: with no robots.txt to read, I stopped |
| CarGurus | **No.** "CarGurus does not provide the option to list or sell your car privately on the site" (DOCUMENTED, its help centre, article "Listing a car privately on CarGurus", last updated 10 November 2026). Private listings stopped on 27 June 2024 (REPORTED, search summary of the same help centre) | 200 | `GET /Cars/forsale`: **403**, `Server: DataDome`, "Please enable JS and disable any ad blocker". Stopped |
| Edmunds | Dealers only by most accounts ("does not allow private-party sellers", REPORTED). A search engine's summary of its "under $2,000 in Memphis" page speaks of cars marked "For Sale By Owner" (REPORTED, and the page could not be opened to check) | 200; disallows `/api/`, `/gateway/graphql/*`, `/inventory/srp/new-used/*`, `/search/` | `GET /used-cars-memphis-tn/`: **403** "Access Denied" (Akamai). Stopped |
| TrueCar | Dealers ("Certified Dealers"); no source says otherwise (REPORTED) | 200; disallows `/*?*zipcode=`, `/api/`, and **every listing page**: `/used-cars-for-sale/listing/*` | `GET /used-cars-for-sale/listings/location-memphis-tn/`: **403**, a HUMAN (PerimeterX) captcha stub in JSON. Stopped. Note 02's sitemap of listing addresses is of no use to a reader: robots.txt bars the pages it names |
| CarsDirect | Dealer listings; one source says owners too (REPORTED, conflicting) | 200; disallows `/used_cars/vehicle-detail*` | `GET /used_cars/listings`: **403**, Cloudflare challenge (`CF-Mitigated: challenge`). Stopped |
| Carfax listings | **No**: "only ... cars sold by dealerships and not private parties" (REPORTED, a kbb.com comparison) | 200; disallows `/search`, `/vehicle/`, `/api/`, `/dealers/` | `GET /cars-for-sale`: 200, 405 KB landing page, no "private" anywhere in it. No Memphis page requested: nothing private to find, and the car pages are disallowed |

- How many private cars these sites hold around Memphis: **not established.** No count is on any page I could open.
- A search "private sellers within 100 miles of 38103" exists as a browser page on Autotrader, KBB and probably
  Cars.com. None is reachable by a plain request, and Autotrader's robots.txt line reads as barring the `zip=` form.
- **PrivateAuto** (private sellers only; found while searching): robots.txt `Allow: /`. `GET
  https://privateauto.com/buy/memphis` gives 200 and "We didn't find any matches". Zero cars today (TESTED).
- iSeeCars has a "for sale by owner" page for Memphis with about six cars (REPORTED, search index). Note 02 found
  iSeeCars behind a script challenge; not retried.

## 3. eBay Motors: what the owner must do, from eBay's documentation

developer.ebay.com answered 403 (Akamai) to three of the four documentation pages I asked for today, as it did in
note 01, and one address was a 404. What follows rests on: the OpenAPI contract and the filter and requirements pages
saved yesterday in `research/_scratch/endpoints-marketplaces/docs/` (DOCUMENTED), eBay's account-deletion page read
today (DOCUMENTED), and a search engine's summaries of other developer.ebay.com pages (REPORTED).

### Getting a key that works in production

1. **An eBay member account and an eBay Developers Program account.** Both are needed even for the sandbox
   (DOCUMENTED, Buy APIs Requirements: "An eBay member account ... An eBay Developers Program account").
2. **Create a Production keyset.** Sign in to the developer account, open Application Keys, and under Production
   choose "Create a keyset". It gives an App ID (client id) and a Cert ID (client secret) (REPORTED, summary of
   "Get started with eBay APIs" and "Getting your OAuth credentials").
3. **Answer the account-deletion requirement, or the keyset stays disabled.** New developers must comply "before they
   make their first production API call", after which "the keyset/App ID is activated" (DOCUMENTED,
   `developer.ebay.com/marketplace-account-deletion`). Two ways:
   - Opt out: "For any developer application that is not persisting any eBay data, there is an option to opt out":
     set the "Not persisting eBay data" toggle on, pick an exemption reason, submit. The page warns that "failure to
     provide correct information may result in penalties or having their account disabled". **A catalogue that keeps
     eBay listings on disk is persisting eBay data, so I do not think the opt-out is honestly open to this tool**; the
     notices are about eBay users' data, and a stored listing carries the seller's username.
   - Subscribe: give an HTTPS endpoint (not localhost, not an internal address) and a verification token of 32 to 80
     characters; eBay sends a `challengeCode`, and the endpoint must answer 200 with JSON
     `{"challengeResponse": <hash of challengeCode + verificationToken + endpoint URL, in that order>}`. Then it must
     accept the deletion notices and remove that user's data. For a tool that runs from a folder and GitHub Actions
     this means one small always-on web endpoint (a free serverless function would do). This is the real cost of the
     key.
4. **Whether Browse search needs more than that is not consistent in eBay's own pages.**
   - The Buy APIs Requirements page: "The use of eBay's Buy APIs in production is intended for eBay partners only.
     You must apply for production access through the eBay Partner Network", then a process: join the eBay Partner
     Network, send the Buy API Application with mock-ups, wait up to 10 business days, open a support ticket titled
     "Buy API Production Access (eBay user ID)", sign contracts (DOCUMENTED, saved page).
   - The Buy APIs overview marks Deal, Feed and Offer as Limited Release and does not mark Browse (REPORTED). The
     Browse contract's search method lists no restriction but the 10,000-item cap and needs only the public scope
     (DOCUMENTED). The call-limits page gives Browse a default of 5,000 calls a day (REPORTED; note 01 has the same).
   - So: do steps 1 to 3, mint a token, and make one search. If it answers 200, nothing more is needed. If it answers
     403 with an access error, the Partner Network application above is the route. **Not settled until tried.**
5. **Mint an application token** (client-credentials grant; REPORTED for the request shape, DOCUMENTED in the contract
   for the endpoint and scope):

       POST https://api.ebay.com/identity/v1/oauth2/token
       Authorization: Basic base64(<App ID>:<Cert ID>)
       Content-Type: application/x-www-form-urlencoded

       grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope

   The token lasts 7,200 seconds; the grant itself is limited to 1,000 requests a day, so one token per run.

### The search: vehicles within 100 miles of 38103

    GET https://api.ebay.com/buy/browse/v1/item_summary/search
        ?category_ids=6001
        &filter=pickupCountry:US,pickupPostalCode:38103,pickupRadius:100,pickupRadiusUnit:mi,
                deliveryOptions:{SELLER_ARRANGED_LOCAL_PICKUP}
        &fieldgroups=MATCHING_ITEMS,EXTENDED
        &sort=newlyListed&limit=200&offset=0
    Authorization: Bearer <token>
    X-EBAY-C-MARKETPLACE-ID: EBAY_MOTORS_US
    X-EBAY-C-ENDUSERCTX: contextualLocation=country%3DUS%2Czip%3D38103

- The five pickup filters must all be present together (DOCUMENTED: "The method must include all the pickup filters
  ... and the deliveryOptions filter"). With them the answer carries `distanceFromPickupLocation` per item.
  `itemLocationCountry` is ignored when they are used.
- `category_ids=6001` is Cars & Trucks. The filter page warns that `buyingOptions` "is defined at the leaf category
  level ... If this filter is used with a top-level category ID, it won't work". Motors leaves are per model, so to
  see auctions and classified ads as well as fixed-price cars, ask once with
  `buyingOptions:{FIXED_PRICE|AUCTION|BEST_OFFER|CLASSIFIED_AD}` on 6001 and check that the mix changes; if it does
  not, the default mix is what there is. Untested.
- **Private sellers cannot be asked for by filter on the US site.** `sellerAccountTypes:{INDIVIDUAL}` is "supported on
  the following sites": Austria, Belgium, Switzerland, Germany, Spain, France, Great Britain, Ireland, Italy, Poland
  (DOCUMENTED). **Correction to note 01**, which lists it as usable. The answer does carry
  `seller.sellerAccountType` (business or individual), so sort them after reading.
- Marketplace: the contract says a missing or invalid `X-EBAY-C-MARKETPLACE-ID` falls back to `EBAY_US`. Note 01's
  plan stands: try `EBAY_MOTORS_US`, compare with `EBAY_US`.
- If the pickup filters turn out to return nothing for vehicles (untested: a car is "local pickup" in practice, but
  whether sellers' listings are flagged `SELLER_ARRANGED_LOCAL_PICKUP` is not stated anywhere I read), the fallback is
  the same search without them, `sort=distance` with the `contextualLocation` header, and a distance cut on
  `itemLocation.postalCode` in the tool.
- Paging: `offset` in steps of `limit`, up to 10,000 items. Daily: add `itemStartDate:[<yesterday>T00:00:00Z]`.

| Listing field | From (DOCUMENTED field names) |
|---|---|
| `source`, `source_id` | `ebay`, `legacyItemId` |
| `url`, `title` | `itemWebUrl`, `title` |
| `price`, `price_kind` | `price.value` with `ask` for fixed price and classified ads; `currentBidPrice.value` with `bid` for auctions |
| `posted`, `ends` | `itemCreationDate`, `itemEndDate` |
| `seller_type`, `seller_id` | `seller.sellerAccountType`; `seller.username` (the contract notes some developers no longer receive US usernames since 26 Sept 2025) |
| `city`, `state`, `zip`, `geo_how` | `itemLocation.city` (EXTENDED only), `stateOrProvince`, `postalCode`; `zip` |
| `photos` | `image.imageUrl`, `additionalImages[]` |
| `vin`, `miles`, `year`, `make`, `model`, `title_status` | **not in the search answer.** `GET /item/{itemId}` returns them as `localizedAspects` name/value pairs; batches of 20 through `item/?item_ids=` |
| `channel` | `marketplace` (or `auction` when `buyingOptions` is `AUCTION` only) |

## 4. Local and regional classifieds

### Commercial Appeal and Jackson Sun (TESTED: one Gannett platform, plain)

- `classifieds.commercialappeal.com` redirects to `https://classifieds.gannettclassifieds.com/marketplace/mca`;
  `classifieds.jacksonsun.com` to `.../marketplace/jtn`. "iPublish Marketplace". robots.txt for `*`: disallows
  `/marketplace/login/`, `/registration/`, `/search/`, `/account/`, `/basket/`; **`Crawl-Delay: 20`**; a sitemap at
  `/marketplace/sitemap.xml` (not fetched).
- The front page lists every category with its count. Commercial Appeal today: Automotive > Vans (1), **Legals >
  Auto Auction (2)**, and ten other sub-categories with one ad each. Jackson Sun: Home Improvement (1), Public
  Notices (1), no vehicles.
- `GET /marketplace/mca/category/automotive`: one ad, "Handicap Van ... Chrysler Voyager ... 2022 One-owner has 4,000
  miles", post date 10/27, ref `CMCA0114216`. The search form on the page has make, model, price, year, mileage and
  ZIP fields, so the category is built for cars; people do not use it.
- **`GET /marketplace/mca/category/legals/auto-auction`** (TESTED): two notices, each a link to
  `/marketplace/mca/advert/{slug}_{id}` with the whole text on that page:
  1. `..._1524984`, posted 20 Nov: a car lot at 3271 Summer Ave, Memphis 38112, "auction held on 12-3-26 at 10:30 am",
     **seven cars, 2020 to 2025** ("2022 Hyun Elant KMHLR4AF7NU336088", "2025 Audi S5 ...", "2021 Ram 3500 ..."). All
     seven VINs pass the check digit. No owners named. Sample: `commercialappeal_auto_auction_sample.txt`.
  2. `..._1524267`, posted 17 Nov: "Notice of lien of sale" by a towing firm, one VIN, with the owner and lienholder
     wording. Not copied.
- **None of the eight VINs appears in the Daily News pages of 17, 18 or 20 November.** This settles a question note 10
  left open: the Commercial Appeal carries vehicle sale notices the Daily News does not. Small, but the first one is
  seven late-model cars at one sale.
- Fields map as for the Daily News (section 6), with `source` `commercialappeal.com`, `source_id` the ref code plus
  the VIN, `url` the advert page, `posted` the post date (printed as `11/20`, no year).
- Terms: the page links `usatodayco.com/terms-and-conditions/`, which is a script shell (816 characters of text).
  Not read.

### Other newspapers (TESTED where a page answered)

Three run the same BLOX software, whose classifieds landing page prints a count per category.

| Paper | Page | Cars & Vehicles | Note |
|---|---|---|---|
| DeSoto Times-Tribune | `desototimes.com/classifieds/` | **0** (and 1 job, 0 of everything else) | robots.txt disallows `/classifieds/*?`, so `?l=25` and the RSS form are off limits. `/classifieds/vehicle/` answered **429 "Too Many Requests"** on my third request to the host, minutes after the second. Stopped |
| Jonesboro Sun | `jonesborosun.com/classifieds/` | **1**: "2019 Ford Flex SEL 3.5 V6 engine, 152,000 miles, pearl", $7,300, with its own page under `/classifieds/vehicle/.../ad_{uuid}.html` | 58 to 61 miles out |
| Daily Journal, Tupelo | `djournal.com/classifieds/` | **0** | about 100 miles out |
| Evening Times, West Memphis | `theeveningtimes.com` | not read | **429** on robots.txt itself. Stopped |
| Covington Leader | `www.covingtonleader.com` | not read | TLS certificate is not valid for the host. Stopped |
| Oxford Eagle | `oxfordeagle.com/classifieds/` | not read | 404; the site links an AdHunter marketplace on another host, not opened |
| Arkansas Democrat-Gazette | `arkansasonline.com/classifieds/` | has an Automotive category and a sister site `autosarkansas.com` | Little Rock, 130 miles out. Not pursued |
| Daily Memphian | `marketplace.dailymemphian.com` | **0**: the only category is Employment, with 0 ads | its public notices are the same ads as the Daily News (note 10) |

### Cheap-car boards and free papers

- **Autopten** (TESTED, plain). robots.txt allows all but `/memberarea/`, `/include/`, `/searchresults`; it names
  `https://www.autopten.com/rss_latest_cars`. Terms page: no rule on automated reading found (searched for *scrap,
  robot, spider, crawl, automated, harvest*).
  - `GET /cheap-cars-for-sale-Tennessee-TN.htm`: "There are 356 used cars for sale in TN ... though some of them may
    already be sold", 24 pages, sorted by price from $600. Car ids on the first page run from 8645 to 28567 while
    today's new ids are near 36700: these are old ads kept up. Each row: year, make, model, price, colour, miles,
    photo count, "for sale by owner in {town}, TN {zip}", and the **seller's phone number in the heading**.
  - The feed: 103 items dated 15 May to 21 Nov 2026 for the whole country, so about four new cars a week nationwide.
    12 of the 103 are by owner. Tennessee: 8, all one dealer in Bolivar (65 miles), posted 19 Nov. Arkansas: 1 (near
    Little Rock). Mississippi: 0. Sample: `autopten_rss_sample.xml`.
  - Not worth a reader: nothing near Memphis is being added, and nothing is ever marked sold.
- **Oodle** (TESTED first page). `GET https://cars.oodle.com/used-cars/memphis-tn/`: 200, "1 - 15 of 24,563" for the
  "Memphis Area"; facets "Dealer (22,276)", "Private Party (414)". Of the 15 shown, 13 are "Over 4 weeks ago on
  Americanlisted": classic cars at $12,500 to $20,750 with auction-catalogue prose, which is what copied scam ads look
  like. The page's own link to the private-party list (`/used-cars/memphis-tn/seller_type_private_party/`) answered
  **404**, and so did the same path under the canonical `memphis-area` name. Outbound links go through `/r_...`,
  which robots.txt disallows. Terms forbid "automated means, including spiders, robots, crawlers, data mining tools,
  or the like to download data". Stopped at four requests.
- **Thrifty Nickel / American Classifieds**: `thriftynickel.com` and `americanclassifieds.com` both serve the same
  parked-domain robots.txt, which ends `User-agent: * / Disallow: /`. Nothing fetched. No Memphis edition found by
  search either.
- **Geebo, ClassifiedAds.com, AmericanListed, Recycler, Claz**: I guessed a Memphis vehicles address for each. Geebo
  redirected to a nationwide list; ClassifiedAds returned an unrelated page; AmericanListed timed out; Recycler 404;
  Claz 429. None established. Oodle's first page shows what AmericanListed's Memphis car ads are.
- **University and church boards**: one search found no public board for the University of Memphis, Rhodes or UTHSC.
  Not established either way.

## 5. Estate sales, storage auctions, the state portal

### EstateSales.net (TESTED: plain; terms forbid harvesting)

- robots.txt for `*`: disallows `/account`, `/homepages`, `/v2`, `/v3`, `/legacy`, `/api/user-view-details`.
- `GET https://www.estatesales.net/TN/Memphis`: 200, "Memphis Estate Sales (28 Results)", sales "currently scheduled
  for the Memphis area" out to Jackson TN, Tupelo, Bolivar and West Helena. 20 of the 28 are in the HTML as
  schema.org `SaleEvent` JSON-LD: `url` (`/TN/{city}/{zip}/{id}`), `name`, `startDate`, `endDate`, `description`
  (the kind: Estate Sale, Online Only Auction, Business Closing), `organizer` (the company; many are "Private
  Listing"), `location`, `image`. Sample: `estatesales_net_memphis_sample.json`.
- **The list never says whether a sale has a car.** That is in the free-text description on each sale's page. Of the
  three I opened: one says only "More Pics and info coming soon"; one has no vehicle; one, in East Memphis, lists
  "Dependable 2010 Toyota Prius" between a dining set and a butcher block. No price, no VIN, no mileage, and the same
  paragraph names the late owner (not copied). To know which of 28 sales has a car costs 28 requests, and the answer
  is a phrase.
- Terms (DOCUMENTED, `/terms-of-service`): users must not use "any engine, software, tool, agent, or other device or
  mechanism (including without limitation browsers, spiders, robots, avatars, or intelligent agents) to harvest or
  otherwise collect information from the Service for any use". **A wall by terms.**
- As a listing source: no. A car cannot be made into a listing record from a phrase. As a tip for the owner
  ("an estate sale this weekend mentions a car"), it would be a watcher, and the terms rule that out without the
  company's permission.

### EstateSales.org (TESTED)

`GET https://estatesales.org/estate-sales/tn/memphis`: 200. "Within 50 miles of Memphis, TN ... No estate sales
currently listed near Memphis, Tennessee", then paid national listings from Texas. robots.txt disallows `/terms` and
`/privacy`, so its terms were not read. Nothing here.

### Storage-auction sites

Note 10 opened each site's front or Memphis page; I did not repeat those. Added today:

- StorageTreasures: `sitemap.xml` lists 12,288 addresses, city pages as `/auctions/{st}/{city}` (Tennessee towns,
  `ar/west%20memphis`). robots.txt allows them. Note 10 found the Memphis page a script shell with no auctions in the
  HTML; the data behind it is an internal API. Not readable by a plain request.
- StorageAuctions.com: `sitemap.xml` lists 87 addresses, a handful of single auctions (`/auctions/{id}`) and a
  `/public-notices` page; none names Memphis or Tennessee. robots.txt disallows `/api/`. Front page is a shell.
- Lockerfox: robots.txt disallows `/auctions/` and `/public-notices/` (crawl delay 5 s). Off limits.
- Whether any of them lists a unit with a vehicle near Memphis today: **not established**, and not reachable within
  the rules. Note 10's point stands: a vehicle sold from a storage unit in Tennessee is advertised in a notice, and
  the notices are what sections 4 and 6 read.

### Tennessee Abandoned Vehicle Portal: can an individual apply for the partner API?

From the portal's own pages (`abandonedvehicles.revenue.tn.gov`, read in note 10's captures and its help page today):

- `/api-docs`: "API keys are issued to approved integration partners and carry scoped permissions." A third tier,
  for owner and lienholder data, is for "authorized state agencies and law enforcement systems" only: "Contact the
  portal administrator to initiate the authorization process." (DOCUMENTED)
- **Nowhere do the pages say who may be an integration partner, how to apply, or that an individual may or may not.**
  There is no form. The only enrolment described is for publishers: tow companies, garagekeepers, law enforcement,
  and from 25 January 2027 title service companies, each reviewed by the State (DOCUMENTED, `/contact` and the tn.gov
  user page).
- Contacts the pages give: "portal support team by email", `support@autura.com`, "Responses within one business
  day"; and the Department of Revenue, 500 Deaderick Street, Nashville, (615) 741-3101.
- The help page says public search results include "any scheduled sale or disposal date". Note 10's one search
  answer had no sale date in it. Either none of those seven cars had a date yet or the JSON omits what the web page
  shows. Not settled; I sent no further search.
- So the answer is: **not documented either way.** The owner writes to both addresses, says he wants read-only
  `status=active` notices with `sale_date` for a personal tool, and asks whether an individual can be approved.

## 6. The Daily News lien-sale notices: what a reader needs

Six days' pages: 6, 10 and 13 November fetched today (the three allowed), 17, 18 and 20 November from note 10's
captures. `mdn_parse.py` is a trial splitter, not product code; its figures:

- **49 printings of 47 distinct notices** (two repeat a week later under the same ad number), **305 VIN occurrences,
  265 distinct VINs**. 301 of 305 pass the check digit.
- Sale dates run 3 to 31 days after the printing; most are 7 to 15.

### Finding the cars

A notice is one table row under `<a id="misc">`: `OpenChildFT2('MD117766', ...)` gives the ad number, then `<p>`
lines. Keep rows that hold a 17-character VIN and one of *sold, auction, sale*. Five layouts were seen:

| Layout | Example (cars only) | VINs |
|---|---|---|
| words and VIN on one line | `2018 Kia Optima KNAGT4L30J5232389`; `2011 BMW 335i – VIN# WBADX7C53BE260568`; `17 CAMRY 4T1BF1FK1HU291095` | 115 |
| words on the line before the VIN | `2012 DODGE CHARGER` / `VIN#2C3...`, usually followed by owner and lienholder lines | 146 |
| words on the line after the VIN | VIN / `2002 GMC Savana 2500HD` | 15 |
| one sentence per car | `Vehicle Auction on December 8, 2026 at {shop}, {street}, Memphis, TN 381xx, 2016 Toyota ... VIN# {VIN}. Owner: ... Lienholder: ...` | 20 |
| a free sentence about one car | two notices, one car each | 1 split by the same tail rule, 1 not |

**The rule that makes this reliable:** for each VIN, try the text before it on its own line, then the tail of that
text after the last comma or full stop, then the line before, then the line after; accept a candidate only if it is a
year followed by at most six words **and the year agrees with the VIN's model-year character** (position 10; a
two-digit year is matched against the same decode). The agreement test is what tells a car line from a stray line.

- **296 of 305 VINs (97%)** get words this way; 258 of 265 distinct. In 291 of the 296 the first word is a make I
  listed (including the papers' own spellings: Chev, Chevy, Hyun, Volk, Crysler, Mercedez, VolksWagon, Frht, Cadi).
- The words are uneven: often make only ("Nissan"), sometimes a colour ("Honda Accord (Blue)", "Nissan Altima
  Silver"), sometimes codes ("Chevy CC1", "Ford F7P"), sometimes a trailer or a motorcycle ("Great Dane Trailers",
  "Honda CBR600"). So take **year, make, model and body from the VIN decode** (`cartrack/vin.py`, vPIC), and keep the
  printed words as the title. For the 3% with no words the decode is all there is.
- The 9 misses are 7 distinct cars. Six have a year-and-words line beside them whose **printed year disagrees with
  the VIN's** (one year apart in two of them, three to nine years apart in the other four; one of the six also
  fails the check digit). So the paper or the tow lot mistyped the year or the VIN, and the test is doing its job by
  refusing them. The seventh is a car named in the middle of a sentence. A reader could accept a one-year
  difference and take the year from the VIN; I did not, and the figure above is without that allowance.

### Sale date, hour, address

- **Date: found in all 47.** Written as `12/05/2026`, `12/1/2026`, `12/14/26`, `12-3-26`, `11-28-2026`,
  `12\03\2026`, `12/10 /2026` (a stray space), `Dec. 8, 2026`, `Nov. 24, 2026`, `December 8, 2026`,
  `December 2nd, 2026`. One pattern for digits with `/`, `\` or `-` and optional spaces, one for month names. Skip the
  footer line (`Nov. 20, 2026 Mq117766`), which is the printing date and the ad number again. In the six days no
  sale date came out earlier than its printing; keep that as a sanity test.
- **Two notices give each car its own date** (one tow lot lists nineteen cars over ten sale days, a heading line
  before each group). Carry the latest date line above a car, not the notice's first.
- **Hour: 40 of 47.** `10 am`, `10:00 a.m.`, `@ 9am`, `@ 9:00AM`, `8 AM`, `8A.M.`, `at noon`, `12 noon`, and once
  `@ 9:00` with no am or pm. Seen: 10:00 sixteen times, 9:00 fourteen, noon five, 8:00 four, 11:00 once. The seven
  without: three one-sentence notices and two lists that print a date only, one free sentence with no hour, and one
  free sentence that does print an hour on the car's own line, where my trial did not look. Leave the hour empty
  when none is found.
- **Address: 33 of 47** with street, city, state and ZIP on one line, after `located at`, `Location at`, `at` or `@`
  and ending at the ZIP (`located at 3301 Winbrook Drive, Memphis, TN 38116`; `@ 3815 Winchester Rd. Memphis, TN
  38118`; `LOCATED AT 3501 KNIGHT ARNOLD MEMPHIS, TN. 38118`; in the one-sentence layout each car has its own).
  **6 more give a street only** (`at 2217 Freemont Ave`, `at 1824 Thomas Rd.`). **8 gave my patterns nothing**: four
  print the lot's name, street and a "City, ST ZIP" line of its own above the words "Auction on the above lot"; one
  says the vehicles are "located and auctioned at the below addresses" and lists one per car; three I did not work
  out. A second pattern (a street line followed by a `City, ST 381xx` line) would catch the first four; untested.
  Sales outside Memphis were seen in Millington, Piperton, Southaven MS and Jackson TN, so check the distance.
- **Seller**: 11 notices use the sentence "will be sold at auction by {name} on ...". The rest name the firm in a
  heading line or not at all.

### Dropping owners' names

- **Do not try to recognise names. Keep an allow-list instead.** From a notice keep only: the ad number; the date,
  hour and address taken by pattern; each VIN; the year-and-words candidate that passed the agreement test; and a
  lienholder only where the line is labelled. Every other line is discarded unread. In the six days that is 531 body
  lines never kept. Under this rule a name cannot reach the catalogue, because a name is not a year that matches a
  VIN.
- Where names sit: on the lines after the VIN in the tow-lot layout (unlabelled, all capitals, owner first, then
  lienholder), and after the VIN in the one-sentence layout as `Owner: ... Lienholder: ...`. So **never keep text that
  follows a VIN on its line**, and never keep a neighbouring line that fails the year test.
- **The seller can be a person.** In 3 of the 11 "sold at auction by" notices the seller's name has no business word
  in it (a private garagekeeper or landlord, and the sale address may be a home). Keep `seller_name` only when it
  carries a business word (LLC, Inc, Towing, Wrecker, Recovery, Auto, Motors, Imports, Sales, Service, Garage, Repair,
  Center, Truck, Storage); else leave it empty and keep the address, which the notice publishes as the place of sale.
- Lienholders: 5 of the 49 printings label them. Labels seen: `OWNER:` or `Owner:` 59 times, `LIEN:` or
  `Lienholder:` 30 times, `Owner/Lienholder:` once. A labelled lien value is safe to keep when it has a finance word
  (Finance, Financial, Bank, Credit, Title, Loan, Lending, Acceptance, Capital, Services, Corp, LLC, Inc); 26 of the
  labelled values pass, among them Capital One Auto Finance, Credit Acceptance, Bridgecrest, Ally, Exeter, Westlake,
  Toyota Motor Credit, CarMax Business Services, SunTrust, Fifth Third, Republic Finance, TMX Finance / TitleMax,
  Tennessee Title Loans, Check Into Cash and Memphis City Employees Credit Union. **Never keep an `OWNER:` value**: 2
  of the 59 read as businesses, the rest are people. In the unlabelled tow-lot layout the lienholder cannot be told
  from a second owner; drop both.
- The raw pages in `cap/` hold the names as printed. The sample `dailynews_split_sample.json` holds only what the
  allow-list keeps, from notices whose seller is a business.

Field mapping: as in note 10's table, with these changes. `title` is the printed words (or "{year} {make} {model}"
from the decode when there are none). `ends` is the car's own sale date and hour, `YYYY-MM-DDTHH:MM`, or the date
alone. `seller_name` only under the business-word rule. `extra` gains `words_found` (which of the four places) and
`sale_dates_in_notice` when there is more than one.

## Walls met

| Host | What happened | Kind |
|---|---|---|
| offerup.com | pages readable; terms forbid automated collection | terms |
| www.autotrader.com | 200 with Akamai "page unavailable" body, both user agents | bot wall |
| www.kbb.com | 403 Akamai "Access Denied" | bot wall |
| www.cars.com | 403 Cloudflare challenge on robots.txt | bot wall |
| www.cargurus.com | 403 DataDome | bot wall |
| www.edmunds.com | 403 Akamai | bot wall |
| www.truecar.com | 403 HUMAN captcha stub; robots.txt also bars listing pages | bot wall and robots |
| www.carsdirect.com | 403 Cloudflare challenge | bot wall |
| developer.ebay.com | 403 Akamai on three documentation pages | bot wall (documentation only) |
| www.desototimes.com | 429 on the third request | rate limit |
| www.theeveningtimes.com | 429 on robots.txt | rate limit |
| claz.org | 429 | rate limit |
| cars.oodle.com | terms forbid automated download; private-party page 404 | terms |
| www.estatesales.net | terms forbid harvesting by any tool | terms |
| www.storagetreasures.com, www.storageauctions.com | script shells; data only through internal APIs | internal API |
| www.lockerfox.com | robots.txt disallows `/auctions/` | robots |
| thriftynickel.com, americanclassifieds.com | parked; robots.txt `Disallow: /` | robots |

## Mistakes in my own probing, for the record

- **OfferUp's terms were read last.** Nine page and sitemap-guided requests to offerup.com came before the terms page
  that forbids them. Same error as HiBid in note 10. The order should be robots.txt, terms, then pages.
- **Gannett's crawl delay of 20 s was read late.** The two newspaper hosts redirect to
  `classifieds.gannettclassifieds.com`, and three requests reached it within about ten seconds before its own
  robots.txt had been read. The later four kept 20 s.
- `offerup.com/robots.txt` was fetched twice.
- Guessed addresses on Geebo, ClassifiedAds, AmericanListed, Recycler, Claz and Oodle's filter cost eight requests and
  settled nothing. Sitemaps or the sites' own links should have come first.
- The DeSoto Times' 429 came on my third request to the host, minutes after the second. I do not know what set it
  off and did not retry to find out.
- `cap/` holds pages with personal names as the publishers print them: the Daily News pages, the Commercial Appeal
  lien notice, one estate-sale page. The trimmed samples contain none, and no phone numbers.

## For the integrator

1. **Build the Daily News reader with the section 6 rules**: anchor on the VIN, accept words only when their year
   agrees with the VIN's, allow-list what is kept, VIN decode for year, make and model. Expect words for about 97% of
   cars, a date for all, an hour for about 85%, a full address for about 70% and a street for another 13% until the
   "above lot" pattern is added.
2. **Add the Commercial Appeal's Auto Auction category as a second source for the same parser**: one request for
   `/marketplace/mca/category/legals/auto-auction`, then one per advert not seen before, **20 s apart**. The layout on
   the two notices seen is "words and VIN on one line" and a sale line `auction held on 12-3-26 at 10:30 am` with the
   address before it rather than after. The post date has no year. Dedupe against the Daily News by VIN.
3. **OfferUp is the owner's call, and the note takes no side beyond the facts**: the page is public, asked for by city
   name, allowed by robots.txt, and about 1,000 cars deep; the terms say no scripts. If he decides yes, the route is
   `/c/cars-and-trucks/in/memphis-tn?page=N`, newest first, stop at the first page of already-seen ids, never the
   `/search` or filter addresses (robots.txt), never the GraphQL call. A card has no VIN, no posting date and no seller
   type; `seller_type` must stay empty, and first-seen stands in for posted. Other city pages exist for Jackson TN,
   Jonesboro and Tupelo.
4. **eBay waits on the owner**: developer account, production keyset, and the account-deletion step, which for a tool
   that stores listings means a small HTTPS endpoint, not the opt-out. Then one test search tells whether the Partner
   Network application is needed. Do not plan on a private-seller filter; read `seller.sellerAccountType`.
5. **Do not build** for Autotrader, KBB, Cars.com, CarGurus, Edmunds, TrueCar, CarsDirect or Carfax. The only two with
   private sellers that matter (Autotrader with KBB, and Cars.com) are behind bot walls, and CarGurus has had no
   private listings since 2024.
6. **Do not build** for the newspapers' ordinary classifieds, Autopten, Oodle, PrivateAuto or the estate-sale sites.
   Between them they show two private cars near Memphis today (a van in the Commercial Appeal, a Ford Flex in
   Jonesboro). If the owner wants a tripwire, the Commercial Appeal's front page prints every category count in one
   request.
7. **Corrections to earlier notes**: 01 tests OfferUp at `/search?q=`, which robots.txt disallows, and says its
   location follows the visitor's IP, which is true of `/search` but not of the city pages; 01 lists
   `sellerAccountTypes:{INDIVIDUAL}` as usable on eBay US, and eBay's filter page limits it to ten European sites; 02
   offers TrueCar's listing sitemap as useful, and robots.txt disallows every page in it; 10 leaves open whether the
   Commercial Appeal carries other vehicle notices, and it does.
8. **The record still has no home for these sellers** (note 10, item 5): a tow lot's lien sale and a car lot's auction
   are neither `private` nor `dealer`. `extra.lien_sale` and `channel="auction"` carry it for now.

## Not settled

- How many private-seller cars Autotrader, KBB and Cars.com hold around Memphis. No page that says so could be read.
- Whether OfferUp's private-seller filter can be set by an address robots.txt allows. I did not guess parameter names.
- OfferUp's true total: about 1,005 tiles is what the pages hold at 30 miles; a 100-mile figure needs `radius=`,
  which robots.txt disallows.
- Whether an eBay production keyset alone can call Browse search, or the Partner Network application is required.
  eBay's pages say both. Whether the local-pickup filters return vehicles at all.
- Whether an individual can be approved for the state portal's API key. The pages are silent.
- Whether the portal's public search shows sale dates, as its help page says.
- Whether the Commercial Appeal's Auto Auction category is steady: two notices in one week is all I saw.
- The Commercial Appeal's and Daily News' terms on automated reading: neither could be read (a script shell; a
  robots.txt that opens only the notices).
- DeSoto Times-Tribune's vehicle page (429), the West Memphis Evening Times (429), the Covington Leader (bad
  certificate), the Oxford Eagle's AdHunter site: none read. The first showed a count of zero on its landing page.
- Whether any storage-auction site lists a unit with a vehicle near Memphis. Not reachable by a plain request.
- Whether Edmunds and CarsDirect show any private-seller cars. Sources conflict and both sites are walled.
- Public university or church boards with cars around Memphis: one search found none.
