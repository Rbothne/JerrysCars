# 10. Government sales around Memphis: who sells where, and what a plain request can read

Worked 2026-11-21 from a home connection, plain GETs only (Python urllib and curl, a browser user agent), at least 2 s apart per host
(10 s on memphistn.gov and morrisrealtyauction.com, 5 s on govdeals.com, as their robots.txt ask). No account, no login, no internal API,
no key taken from a page, no browser. Scripts and trimmed samples are in `research/_scratch/routing/government/`
(`get.py`, `txt.py`, `pdftext2.py`, `cut_samples.py`, `samples/`, and the smaller raw captures in `cap/`).

Labels: TESTED (fetched and seen today), DOCUMENTED (read in the agency's or platform's own page), REPORTED (second-hand: a search
result, or the third-party aggregator BidProwl). "Aggregator" below always means bidprowl.com, which is not an official source.

A second note written the same day, `10-routing-impound-auctions.md`, covers the Venture Auctions site in more depth, and tow-lot and lien
sales. The two agree on Venture. Where this note leans on it, it says "the impound note".

## Summary

Almost all the volume is one outlet: the City of Memphis impound auction, every Wednesday, about 60 to 108 vehicles a week, on the
auctioneer's own site, which answers plain requests and shows the final price of every lot. Everything else is small or unreadable.

### Who sells where

| Agency | Where it sells | How often | Source |
|---|---|---|---|
| City of Memphis, impounded and abandoned vehicles (MPD lot, 465 Klinke Ave) | **Venture Auctions**, `www.venture-auctions.com`, live webcast | Weekly, Wednesday 9:30 Central. Lists of about 60 to 108 vehicles; 78 lots sold on 18 Nov | TESTED: memphistn.gov/city-auto-auctions, the lists, the auction pages |
| City of Memphis, surplus fleet (3720 Knight Arnold Rd) | Venture Auctions, same site | Quarterly. Two since May 2026; the 26 June list has 133 lots, 62 with a model year. Next: "TBD" | TESTED: same city page, its spreadsheet, auction 5339 |
| Shelby County Government fleet, and Shelby County Sheriff's Office vehicles | **Morris Realty & Auction on HiBid**. Last sale found: "Govt Surplus Vehicles", closed 8 Apr 2025, 57 lots at 6390 Haley Rd | Unknown. One sale in 2025, one in Aug 2019 found. None open today | TESTED: hibid.com/catalog/631204, morrisrealtyauction.com page. Current contract not confirmed (see "Not settled") |
| Shelby County Sheriff, seized property | GovDeals seller page `ShelbySheriffTN` exists; GovDeals' own Tennessee guide names "Shelby County Sheriff" as a seller. Court-ordered vehicles were also in the Morris sale above | Unknown | TESTED (page names in GovDeals' sitemap), DOCUMENTED (blog.govdeals.com). Listings unreadable |
| Shelby County Sheriff, civil levy ("sheriff's sales") | Public auction under each writ. No list on the sheriff's site; notices run in the Memphis Daily News and Daily Memphian | Per case | TESTED: shelby-sheriff.org/civil-levy says only "sold at public auction". Newspapers REPORTED |
| West Tennessee Violent Crime and Drug Task Force | GovDeals (`WestTennesseeDTF`, account 4384) | 2 lots today, both dirt bikes | REPORTED (aggregator); the 2 lots are in GovDeals' sitemap (TESTED) |
| Memphis Police, seized and unclaimed vehicles | The city impound auction above (its notice covers property "abandoned, stolen, or recovered ... unclaimed ... more than 30 days") | Weekly | TESTED (the list's wording). Non-vehicle property: not settled, memphispolice.org answers 403 |
| MLGW | **J.J. Kane Auctioneers**, bidding on Proxibid. Yard: 4225 Getwell Rd | Monthly, two days ("Southeast Region"). Next: 23-24 Nov, 21-22 Dec 2026 | TESTED: mlgw.com/auction, its 2026 calendar PDF, jjkane.com MLGW page |
| MATA | PublicSurplus, agency `mata,tn` | 0 auctions today | TESTED |
| Memphis-Shelby County Schools | Morris Realty & Auction, in person and/or online, Farmville warehouse | About twice a year, spring and fall. "Next Auction:" is blank | DOCUMENTED: scsk12.org/am/?PN=216. Whether buses and vehicles are included: not stated there |
| University of Memphis | GovDeals seller page `UniversityofMemphis` exists. Policy BF4027 allows public auction, sealed bid or internet auction and names no platform | Unknown | TESTED (page name), DOCUMENTED (policy) |
| State of Tennessee surplus (General Services) | GovDeals, `govdeals.com/tnsurplus` | Continuous. About 121 lots today under one account; the aggregator shows them in Nashville. No West Tennessee sale site found | DOCUMENTED: tn.gov/generalservices/vam/state-surplus/online-auction.html. Count inferred from the sitemap |
| Tennessee Department of Safety, seized vehicles | No state outlet: "Public auctions are the responsibility of the law enforcement agency that seized the property" | - | DOCUMENTED: tn.gov/safety/tnhp/forfeit.html |
| Germantown | GovDeals (`germantowntn`, account 1677) | 10 lots today, 2 of them cars (2010 Charger, 2014 Tahoe) | Page name TESTED; lots REPORTED, their ids in the sitemap TESTED |
| Collierville, Millington, Lakeland | GovDeals seller pages exist (`townofcolliervilletn`, `millingtontn`, `lakelandtn`) | No vehicle seen today (a Millington account, 26030, has 34 lots of electronics) | TESTED (page names only) |
| Bartlett | A GovDeals page `cityofbartlett` exists, but the name carries no state (there are Bartletts in Illinois and Texas) | Unknown | Not settled |
| Atoka (Tipton Co.), Somerville (Fayette Co.) | GovDeals, accounts 3116 and 1033 | 1 car and 2 cars today | REPORTED; ids in the sitemap TESTED |
| DeSoto County MS, its sheriff, Southaven, Olive Branch, Horn Lake | GovDeals seller pages `SouthavenMs` and `HornLakeMS` exist. `DeSotoCounty`, `desotocountysheriff`, `olivebranch` and `HornLakePW` exist too but carry no state (Florida has a DeSoto County) | 1 car today, in Hernando MS (account 5804, seller not named) | Page names TESTED; the car REPORTED, id in the sitemap TESTED |
| State of Mississippi surplus | Through GovDeals, for qualified public agencies only, near Jackson | Not open to the public | DOCUMENTED: dfa.ms.gov/state-surplus-and-available-property |
| West Memphis AR (city, police, utilities, schools) | GovDeals seller pages exist (`cityofwestmemphisauctions`, `WestMemphisPD`, `WestMemphisNarcotics`, `westmemphisutilities`) | Nothing seen today | TESTED (page names only) |
| Crittenden County Sheriff AR | GovDeals, account 6352 | 7 vehicles today, all in West Memphis | REPORTED (aggregator names the seller); 7 ids in the sitemap TESTED |
| State of Arkansas surplus (Marketing & Redistribution) | Vehicles on GovDeals, `arstatesurplus`; yard in Little Rock, about 130 miles | Continuous; outside the area | DOCUMENTED: sas.arkansas.gov/state-surplus/for-sale-at-state-surplus, updated 3 Nov 2026 |
| Federal surplus (GSA Auctions) | gsaauctions.gov, documented API | 740 lots nationwide today, **0 within the area** | TESTED |
| Federal fleet cars (GSA Fleet) | `marketplace.gsafleet.gov`, sold at auction houses, "30,000+ vehicles" a year nationwide | 3 cars in Memphis today | DOCUMENTED (gsa.gov); the 3 cars REPORTED |
| Treasury seized vehicles | Apple Towing Co. on HiBid, nationwide online sale | Every one to three months (2-9 Nov 2026 held; 9 Dec 2026 and 10 Mar 2027 listed). The November sale: 89 lots, **none in TN, MS or AR** | TESTED: treasury.gov general property page, hibid.com/catalog/789889 |
| US Marshals seized vehicles | Apple Auctioneering (the same firm) on HiBid | Unknown | REPORTED; usmarshals.gov answers 403 |
| USPS vehicles | GovDeals (`UnitedStatesPostalService`); a Memphis account (25803) has 20 lots, pallets seen | Unknown | REPORTED |

Other Shelby Counties (Texas, Alabama, Ohio, Indiana, Kentucky) turn up in every search and in GovDeals' seller list; none is counted here.

### Verdict per platform

| Platform | What the public gets | Plain request reads it? | Whole catalogue? | Sold prices? | Vehicles in area today | Reader? |
|---|---|---|---|---|---|---|
| Venture Auctions (AuctioneerSoftware) | Server-rendered pages | **Yes** | Yes: 25 lots a page, `?page=N`; 78 of 78 read | **Yes**: every closed auction since 6 May 2026 (31 auctions), bid and bid count per lot | 0 open (next list Monday evening); 78 sold 18 Nov | **Yes, first** |
| City of Memphis lists (PDF, xlsx) | Files on memphistn.gov | Yes | Yes | No (bid columns are blank) | 108 on the newest list (9 Nov) | Optional; the auction page has the same VINs |
| HiBid (`hibid.com`) | Server-rendered pages with a JSON block | **Yes** on `hibid.com`; **no** on `*.hibid.com` auctioneer sites (empty shell) | Yes: 100 lots a page seen (89 of 89, 57 of 57) | When the auctioneer publishes them: Apple Towing yes, Morris no (zeros) | 0 government vehicles within 50 miles | **Its terms forbid automated access. Owner's decision** |
| GSA Auctions | Documented API, one call | **Yes** | Yes, 740 lots | No | **0** | Cheap, but empty here |
| GSA Fleet marketplace | Single-page app | No (18 KB shell) | - | - | 3 (REPORTED) | Wall |
| GovDeals | Single-page app; sitemaps of bare URLs | **No**: every path returns the same 78,637-byte shell | Sitemap lists all 28,474 lot URLs, nothing else | Not readable | At least 15 (REPORTED) | **Wall. Owner's decision** |
| PublicSurplus | Server-rendered pages | Yes | Yes, by state and category | A closed auction's page shows "Final Price" if you know its number; no public list of them | **0** in TN, MS and AR | No |
| Municibid | Server-rendered pages, JSON-LD, sitemaps | Yes | Yes | State pages list "Recently sold" | **0**; no seller within 100 miles | No |
| PropertyRoom | Server-rendered pages | Yes | Yes (34 vehicle-category results nationwide) | Not tested | **0** (all in Hartford CT and Staten Island NY) | No |
| Proxibid / J.J. Kane (MLGW) | Proxibid: blocked. J.J. Kane: list drawn by the page's own search service | **No** | - | - | Unknown | Wall |

## Venture Auctions: City of Memphis impound and surplus (plain, complete, sold prices)

- The city page `https://memphistn.gov/city-auto-auctions` (TESTED) still links `venture-auctions.hibid.com` for registration. That HiBid site
  is an empty shell to a plain request, and Venture's own page says it moved to a new portal on 4 May 2026. The live site is
  `https://www.venture-auctions.com` (also `ventureauctions.auctioneersoftware.com`), "powered by auctioneersoftware.com".
- robots.txt: allows everything except `/admin/`, `/api/`, `/asset/` and any URL with `?search`, `?filter`, `?sort`, `?pageSize`
  (or `&`). `?page=` is not disallowed. Its terms page is the terms of sale only; nothing about automated reading.
- Pages, all 200 to a plain GET:
  - `/auctions`: upcoming. Today one entry, "Memphis Impound Public Webcast Auction 11/25/2026", marked "Coming Soon", no lots yet.
    The city says the list goes up by 6 pm Monday, preview Tuesday 12-2, bidding Wednesday 9:30. So lots are visible for about a day and a half.
  - `/past-auctions` and `/past-auctions?page=2`: 31 closed auctions back to 6 May 2026 (29 weekly impound sales, 2 surplus sales).
  - `/auctions/{id}-{slug}`: 25 lot cards; `?page=2`, `3`, ... until a page with no cards. Auction 5361 (18 Nov): 25+25+25+3 = **78 lots**.
    The page's own "Lots Total" reads 0 in the static HTML, so count cards.
  - `/auctions/{id}/lot/{lot_id}-{slug}`: one lot.
- A lot card gives: lot id (`data-lotid`), lot number, title ("2009 SCION TC COUPE 2-DR 2.4L L4"), one photo, state ("Completed"),
  "Winning Bidder" (masked) with the amount, "Bids", "Watching". The VIN is not in the visible card.
- The same page carries the lots as JSON, `window.__APOLLO_STATE__`, one `AuctionLot.{id}` per lot on the page (TESTED on page 4: 3 lots, 3 VINs):
  `title`, `description` (HTML with Year, Make, VMS ID#, Model, **VIN#**), `lot_number`, `start_time` and `end_time` (ISO, UTC, "2026-11-18T15:30:00.000Z"),
  `starting_bid`, `winning_bid_amount`, `bid_count`, `watch_count`, `is_no_sale`, `image_count`, `primary_image.url`, `public_url`.
  So the auction pages alone give everything; lot pages are not needed. Read the JSON, not the cards.
- A lot page adds: `Year`, `Make`, `Model`, `VMS ID#`, **`VIN#`**, "Start Time", "Starting Bid: $10.00", "Bid Increment", "Bid Count", more photos.
  A surplus lot gives `VIN#` and `CITY ID#`. **No mileage on either kind.** No title status; the terms say impound lots carry no warranty
  against salvage or flood brands, and a lot marked "FOR PARTS ONLY" cannot be registered.
- Evidence, auction 5361: 78 lots, 78 with an amount, 76 "Winning Bidder" and 2 "Current High Bidder". Low $300, median $575, high $6,900, total $81,825.
- The city's weekly list (`/wp-content/uploads/2026/11/Impound-Sales-List-11-09-2026.pdf`, Crystal Reports) gives in one request, per vehicle:
  year, make, **VIN**, date on lot, invoice number, tow charge, tag number (my rough reader found 106 rows; the impound note counts 108, equal to the auction's 108 lots). The text needs each font's ToUnicode map
  (`pdftext2.py` does it in the standard library). The file names are not regular (`Impound-Sales-List-11-09-2026.pdf`, `10-19-2026-Sales-List.pdf`),
  so read the links off the city page. memphistn.gov robots: `Crawl-delay: 10`, nothing disallowed.
- The surplus list is a spreadsheet (`Ready-For-Auction-06-26-26.xlsx`): lot, unit number, year, make, model, body, VIN, title code, keys. No mileage.
- Fields for the listing record:

  | Record field | From |
  |---|---|
  | `source`, `source_id` | `venture`, the lot id (3611); keep the auction id (5361) in `extra` |
  | `url`, `title` | lot URL; card title |
  | `channel` | `auction` |
  | `price`, `price_kind` | the amount; `sold` with "Winning Bidder", `bid` with "Current High Bidder" or while open, `starting` at $10 with no bid |
  | `ends` | `start_time` (when the live sale begins) or `end_time` (when that lot closed), both UTC. The lot page prints the same instant without a zone: "11/18/2026 3:30:00 PM" for a 9:30 am Central sale |
  | `vin`, `year`, `make`, `model` | `description` in the page JSON (or the lot page, or the city list) |
  | `miles`, `title_status` | not given; leave empty (`parts_only` if the title says FOR PARTS ONLY) |
  | `city`, `state`, `zip`, `geo_how` | Memphis, TN, 38127, `street` (465 Klinke Ave) for impound; 38118 (3720 Knight Arnold Rd) for surplus |
  | `seller_name`, `seller_type` | "City of Memphis impound" or "City of Memphis fleet"; `seller_type` has no value for a government seller, leave None |
  | `photos` | card image, more on the lot page (`auctioneersoftware.s3...amazonaws.com/vent/...`) |
  | `extra` | bids, watching, lot number, VMS ID, fees: 10% buyer's premium + $10 per lot, + 4% on cards |

- Cost: about 4 to 6 requests a week (the auction list, then one per 25 lots).
- Pace: my 14 requests, 2 s apart, all answered 200. The impound note, working the same day, got one 429, saw a `RateLimit-Limit: 1` header and settled on 15 s. Use the slower pace.
- Not tested: an open auction (none was open), so whether pre-bids show before the live sale is unknown.
- The city list's ticket number is the lot's `VMS ID#` and its tag number is the lot number (the impound note compared 25 lots; not rechecked here).
- For the owner: the terms say an unlicensed buyer may buy **6 vehicles a calendar year** at the impound, and a first-time bidder one per auction.

## HiBid: Shelby County through Morris, Treasury through Apple Towing (reads plainly; terms forbid it)

- **Terms of Use** (`https://hibid.com/home/termsofuse`, "Last Updated 22 November 2022", TESTED): users must not "conduct any web scraping, web harvesting,
  web data extraction, or any other data scraping of Auction Information or our Sites or Services", nor "use any robot, spider, scraper, data mining tool ...
  or any other automated means to access our Sites or Services". I found this page last (the impound note pointed to it; `/home/terms` is near-empty),
  after 14 requests to HiBid hosts, and stopped. What follows is what those requests showed. Whether to read HiBid at all is the owner's decision.
- robots.txt (same file on `hibid.com` and the auctioneer sites) disallows `*/livecatalog/`, `*/webcast/`, `/auctioneer/`, `*/account/`,
  `*/catalog/print/`, `/auctions/current/map/`, `/auctions/past/*?q=`.
- `https://venture-auctions.hibid.com/` and `https://morrisauctiongroup.hibid.com/auctions`: 200, 15-16 KB, no data, a Cloudflare Turnstile script. Do not use these.
- `https://hibid.com/...` pages are server-rendered with `<script id="hibid-state" type="application/json">`; read `apollo.state`:
  - `https://hibid.com/company/32146/morris-realty-and-auction`: the auctioneer's open auctions (today one, a house). Apple Towing Co is auctioneer 60432.
  - `https://hibid.com/catalog/{id}/{slug}`: the auction (`eventName`, address, `bidOpenDateTime`, `bidCloseDateTime`, `buyerPremium`, `lotCount`)
    and up to 100 `Lot:` objects.
  - `https://hibid.com/lots/700006/cars-and-vehicles?zip=38103&miles=50`: the vehicle category by distance. Today 32 lots in 7 auctions; the 25 on the
    first page are truck accessories and liquidation goods from two Mississippi resellers. No government vehicle among them; page 2 not read.
- Lot fields: `id`, `lotNumber`, `lead` (title), `description` (free text: "VIN: 1FM5K7B84HGD92748 Miles: 94924 Color: Silver ... Has Title, Has Keys"),
  `pictureCount`, `pictures[].fullSizeLocation`, `lotState{status, bidCount, highBid, minBid, priceRealized, timeLeftSeconds}`.
  Map: `price` = `highBid` (`bid`) or `priceRealized` (`sold`, when above 0); `ends` = the auction's `bidCloseDateTime`, which carries no zone and
  looks like US Eastern (the Treasury sale reads 11:00 and its text says "11 AM ET"; the Morris sale reads 13:00 and was advertised as noon Central, REPORTED);
  VIN and miles by pattern from `description`; city, state, zip from the auction for a one-site sale.
- Shelby County sale (catalogue 631204, TESTED): "Surplus vehicles from Shelby County Government and Shelby County Sheriff's Office", 57 lots,
  6390 Haley Road, bidding 27 Mar to 8 Apr 2025, 15% buyer's premium. Still public 19 months later. Every lot shows `priceRealized` 0: Morris did not publish prices.
- Treasury sale (catalogue 789889, TESTED): 89 lots (4 are notices), closed 9 Nov 2026, **`priceRealized` on each vehicle** (a 2021 Altima, 80,608 miles, $7,550).
  The title carries the state, "(CA) 2021 Nissan Altima"; the description gives the yard address, VIN, odometer. States: CA 25, TX 24, MI 8, IN 7, AZ 4 and eleven others. None near Memphis.
- Not found: a public page listing an auctioneer's past auctions (`?status=CLOSED` is ignored). A closed catalogue is reachable only if its id was noted while open.

## GSA Auctions: documented API (plain, complete, nothing here)

- `GET https://api.gsa.gov/assets/gsaauctions/v2/auctions?api_key=DEMO_KEY&format=JSON` (DOCUMENTED at gsa.github.io/auctions_api; TESTED): 200,
  redirects to a 2.4 MB file, `{"Results": [...]}` with **740** lots (590 Active, 150 Preview). Limits: 5,000 calls a day, 5 per 5 seconds.
  `DEMO_KEY` "will not work after a certain number of attempts"; a personal api.data.gov key is free. No parameters, no category field, no closed lots.
- Vehicles: there is no category, so pick them out by text. 95 lots have "VIN" and a 17-character VIN in `lotInfo`; 111 have an `itemName` starting with a
  year; 88 have both. Those 95 include trailers and boats. Standard vehicle lots carry "Make: ... Model Year: ... Estimated Mileage: 132,572 ... VIN: ..." in `lotInfo` (HTML).
- Near Memphis: `propertyCity`, `propertyState`, `propertyZip` are where the item is (`location*` is the sales office; ignore it).
  ZIP prefixes 375, 380, 381, 386 and 723 roughly cover the 60 miles (an approximation; 386 and 723 run further out). **0 lots** today.
  Whole states: TN 6 (one car, in Oneida, far east), MS 11 (trailers at Grenada, boats at Dennis), AR 4.
- Fields: `source_id` = the number in `itemDescURL` (`.../auctions/preview/383673`); `price` = `highBidAmount`, `bid`, or `starting` when null;
  `ends` = `aucEndDt` (a date, no time); `seller_name` = `agencyName`; one photo in `imageURL`; bidders in `biddersCount`.
- GSA Fleet cars are a different system, `https://marketplace.gsafleet.gov/sales/landing`: 18 KB shell, data from the app's own service. No documented API for it on open.gsa.gov.

## GovDeals: nothing in a plain page (wall)

- robots.txt: `Crawl-delay: 5`; disallows `/account/` and `/assets/`; lists six sitemaps on `files.lqdt1.com`.
- TESTED: `/en/memphistn`, `/en/ShelbyCountyTN`, `/en/asset/334/32984`, `/passenger-vehicles/tennessee` each return **the same 78,637 bytes**
  (`<title>Home</title>`, an `<app-root>`, no JSON-LD, no listing text). The listings come from the internal service; it was not called.
- `https://prod-seo.govdeals.com/passenger-vehicles/tennessee` is in search-engine results with listing text ("MEMPHIS (1)"), but answers a
  307 redirect to the shell for both a browser and a tool user agent. Not pursued.
- Sitemaps (TESTED; the assets file was rebuilt today at 05:01 GMT):
  - `Assets_Sitemap_GovDeals.xml` (20 MB): 28,474 URLs `https://www.govdeals.com/en/asset/{item}/{account}`. No title, date or place. 2,377 accounts.
  - `SellerMarketPlaces_Sitemap_GovDeals.xml`: 14,781 seller page names (the local-looking ones are in `samples/govdeals_local_seller_slugs.txt`). A name
    proves the seller has an account, not that it has anything for sale, and nothing public ties a name to an account number. Names without a state
    (`cityofbartlett`, `DeSotoCounty`, `olivebranch`, `shelbycounty911`, `shelbysheriffmagu`, `Munford`) may belong to another state.
  - `Category_Sitemap` (660 categories), `Location_Sitemap` (state pages): the shell again.
- No RSS, feed or documented API found. The terms page is inside the app and could not be read.
- What the listing shows, and the sold search (`timeType=sold`, about a year back): REPORTED in note 01, not testable here.
- Counts today come from the aggregator, checked against the sitemap: Crittenden County Sheriff 7, Germantown 2, Somerville 2, Atoka 1,
  Hernando 1, Memphis 2 (a 2013 Buick LaCrosse, a 2014 bucket truck) = **15 road vehicles**, plus a dirt bike and a trailer.
  14 of the 15 ids are in GovDeals' own sitemap; the Buick's is not. The aggregator's Memphis page showed only its first 24 of 80 listings, so 15 is a floor.
- Item numbers run in sequence per account (inferred): Crittenden Sheriff is at 101, Atoka 147, Somerville 194, Germantown 577. These are small, slow sellers.

## PublicSurplus, Municibid, PropertyRoom (plain, and empty here)

- **PublicSurplus.** robots.txt disallows only `/images/`. Agencies by state: `/sms/all,tn/browse/home` (43 agencies), `all,ms` (22), `all,ar` (38).
  Local: MATA (`mata,tn`), Memphis & Shelby County Port Commission (`portofmemphis,tn`), Town of Somerville (`somerville,tn`). None in DeSoto or Crittenden.
  Vehicles: `/sms/all,tn/browse/cataucs?catid=4` ("Motor Pool"): "No auctions found" for TN, MS and AR; the national page showed 25 rows, so the page does list them when there are any.
  `/sms/auction/view?auc=4060000` (closed 11 Aug 2026) still shows "Final Price $1,275.00", "# of Bids 6", agency, dates, address.
  `/sms/mata,tn/list/past?orgid=17553` answers **401**: an agency's past list needs a login.
- **Municibid.** robots.txt disallows `/search`. `/auctions/tn`: "0 live now", 3 agencies (Forest Hills, Knoxville, Linden). No Mississippi page.
  `/auctions/ar`: Bryant and Little Rock only. State pages list recent sales with prices. Its terms page has no clause on automated access.
- **PropertyRoom.** robots.txt disallows `?location=`, `?seller=`, `?sort=`, `/api/`. `/c/vehicles`: "1-34 of 34 Results", cars only in Hartford CT and Staten Island NY.

## Walls met

| Host | What happened | Requests |
|---|---|---|
| www.govdeals.com, prod-seo.govdeals.com | Same shell for every path; 307 to the shell | 5 + 4 |
| marketplace.gsafleet.gov | Shell only | 2 |
| www.proxibid.com | **403**, Imperva/Incapsula page, on robots.txt and on a seller page | 2 |
| www.jjkane.com (MLGW) | Page is 200, but the lot list is drawn by an Algolia search whose key sits in the page. Not used. No lot sitemap | 3 |
| www.shelbycountytn.gov | **403**, Cloudflare managed challenge, on robots.txt and a search page (both sent in one command) | 2 |
| bids.shelbycountytn.gov | Name no longer resolves (NXDOMAIN) | - |
| www.memphispolice.org | 403 (Cloudflare) | 1 |
| www.usmarshals.gov | 403 (Akamai) | 1 |
| memphistn.gov `/download/134/...` (old "bid on surplus items" PDF) | 403 | 1 |
| publicsurplus.com `/list/past` | 401 | 1 |
| hibid.com and `*.hibid.com` | Answers plainly, but the Terms of Use forbid "any robot, spider, scraper ... or any other automated means" | 14, before the terms were read |

## Not settled

- **Who sells Shelby County's fleet in 2026.** The county asked for an online auctioneer in Oct-Nov 2023 (bid SB-I000840, closed 16 Nov 2023; REPORTED),
  and Morris ran an online sale for it in April 2025. Whether Morris still holds it, and how often it sells, could not be read: the county site is behind a challenge.
- What the Shelby County Sheriff, University of Memphis, Bartlett, Collierville, Millington, Southaven, Olive Branch, Horn Lake and West Memphis have on GovDeals today.
- Whether the City of Memphis still uses its GovDeals page (`memphistn`) for anything.
- MLGW lot counts, and whether its monthly sale includes ordinary cars or mainly utility trucks.
- GSA Fleet sale dates and place in Memphis. US Marshals lots near Memphis.
- Closings per month, except Venture. The figures in "For the integrator" for the others are guesses.

## For the integrator

1. **Venture first.** One reader, `venture`: `/auctions` and `/past-auctions` for auction ids, `/auctions/{id}-{slug}?page=N` until empty, reading
   `window.__APOLLO_STATE__` on each page (VIN included), 15 s apart. Expect 250 to 450 impound vehicles a month and about 60 fleet vehicles a quarter, all with a final price.
   This is also the only local sold-price source found.
2. **HiBid is the owner's call too.** It would take a small reader: `hibid.com` only, auctioneers 32146 (Morris: Shelby County, schools) and 60432 (Apple Towing:
   Treasury, Marshals) through `/company/{id}/...`, then `/catalog/{id}/{slug}`, noting catalogue ids while they are open. But its terms forbid automated access.
   The stake is small: one 57-lot county sale found in two years, and no federal lot near Memphis. Routes that avoid HiBid: Morris announces its sales on
   `https://morrisrealtyauction.com/auctions/upcoming-auctions` (plain, `Crawl-delay: 10`; its 2019 county sale had lot, year, make, model, VIN and odometer in the page),
   and Treasury links each sale and its bid-result PDFs from `https://www.treasury.gov/auctions/treasury/gp/index.html` (plain; the PDFs are described in note 01, not reread here).
3. **GSA Auctions** costs one call a day and has nothing here today. Worth adding only if a zero-result source is acceptable; use a personal key.
4. **GovDeals is the owner's call.** It holds the suburbs, both neighbouring sheriffs and the state: at least 15 local vehicles today, perhaps 20 to 40 a month (a guess).
   Plain requests get nothing. The choices are to leave it out, to read it in a browser session, or to take it second-hand from an aggregator
   (bidprowl.com publishes an RSS feed and an OpenAPI file, neither examined here).
5. **Skip** PublicSurplus, Municibid and PropertyRoom for this area. Proxibid is blocked.
6. Record gaps: `SELLER_TYPES` has no government value; impound lots have no mileage and no title status; `ends` from Venture and HiBid is a
   date-time (Venture: UTC; HiBid: no zone, looks like US Eastern), from GSA a bare date.
7. A ZIP-to-coordinates table is not in the repo. GSA and HiBid give ZIP codes; Venture's two addresses are fixed.
