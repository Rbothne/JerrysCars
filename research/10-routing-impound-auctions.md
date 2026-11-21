# 10. Impound and auction sales around Memphis: what the public can read

Worked 2026-11-21 (a Saturday) from a home connection. Plain GETs only, user agent `cartrack/0.1`, no account, no
internal API, no browser. Pace: 15 s on venture-auctions.com after one 429, 10.5 s on memphistn.gov (its robots.txt
asks for 10), 5 s on hibid.com, 2.5 s elsewhere. 74 requests in all, 27 of them to venture-auctions.com.
Scripts and every capture are in `research/_scratch/routing/impound/` (`g.py` fetch and log, `va.py` and `lots.py`
for the auctioneer's pages, `pdfrows.py` for the city PDF, `auctions.py` and `state.py` for HiBid, `cap/`, request
log `cap/_log.tsv`). Labels: TESTED = fetched and seen here, DOCUMENTED = read in the source's own text,
REPORTED = second-hand (search results, other sites).

**The main finding: the city's auctioneer left HiBid in May 2026.** Venture Auctions now runs the weekly impound
sale on its own site, `www.venture-auctions.com`. That site answers a plain request with the whole catalogue in the
page, and it keeps every finished sale with the hammer price of each car. The city page still points at two dead
addresses.

## Summary

| Source | Public page | Plain request? | Whole catalogue? | Sold prices? | Vehicles seen today |
|---|---|---|---|---|---|
| **Venture Auctions, own site** (City of Memphis impound, weekly) | `www.venture-auctions.com/auctions`, `/past-auctions`, `/auctions/{id}-{slug}?page=N` | **yes**, server-rendered JSON in the page | **yes**: 78 of 78 lots of the 11/18 sale in 4 pages | **yes**, per lot, for all 31 sales since 2026-05-06 | next sale 11/25: 0 lots posted yet. Last sale 11/18: 78 lots, 76 sold, median $575 |
| **City of Memphis PDF list** | linked from `memphistn.gov/city-auto-auctions` | yes | yes when it is text (5 of 6 lists); 1 of 6 is a scan | no | no current list today. Newest (11-09): 108 vehicles |
| City surplus sale (quarterly) | same Venture site | yes | first page read (25 of 93) | yes | none scheduled ("TBD") |
| Venture Auctions on HiBid | `venture-auctions.hibid.com` | shell only | **nothing there**: a placeholder "WE'VE MOVED", 0 lots | no | 0 |
| HiBid search, 60 miles of 38103 | `hibid.com/auctions?zip=38103&miles=60` | yes, but **HiBid's terms forbid automated access** | 9 auctions listed | field exists (`priceRealized`), not explored | **0 vehicles** (25 "Cars & Vehicles" lots, all accessories) |
| Walker Auctions, Memphis (estate, consignment) | `bids.walkerauctions.com/auctions/{id}-{slug}` | yes, same platform as Venture | first 50 of 95 lots read | current bids yes; results not read | 4 vehicles in one estate sale closing 12/1 |
| Daily Memphian public notices (tow and garage lien sales) | RSS `dailymemphian.com/feed/section/public-noticesmiscellaneous-notices`, then `/article/{id}` | yes | newest 20 notices per feed read | no | 1 notice read: 2 cars. 3 vehicle-sale notices on page 1 |
| IAA Memphis (branch 738, Millington) | `www.iaai.com/US/Locations/738` | branch page yes; **sale list blocked** (Incapsula); `/Search` is disallowed by robots.txt | no | no | not readable |
| Copart Memphis | `www.copart.com/locations` | **no**: 212-byte Incapsula script page | no | no | not readable |
| Tennessee Abandoned Vehicle Portal | tn.gov | **no**: 403 on robots.txt itself | - | - | not read |

## 1. City of Memphis impound auction: Venture Auctions' own site (plain, complete, with sold prices)

### How the move was found (TESTED)

- The city page says the sale is "online via https://www.venture-auctions.com/UpcomingAuctions.html" and "register
  online https://venture-auctions.hibid.com/". The first address answers **404**. The second is HiBid's
  client-rendered shell (15 KB, no data).
- `GET https://hibid.com/auctions?zip=38103&miles=60` is server-rendered (`script#hibid-state`). In it, auctioneer
  64305 "Venture Auctions" has one auction, id 739346: `eventName` "WE'VE MOVED...click the VA logo at the top of
  page!", `lotCount` 0, `bidType` NO_INTERNET_BIDDING, `altBiddingUrl` `https://www.venture-auctions.com/`,
  description "ALL users must create NEW accounts on the NEW platform! ... DO NOT REGISTER ON THIS PAGE!!!",
  open from 2026-05-04.
- `www.venture-auctions.com` is "powered by auctioneersoftware.com" (Auctioneer Software; the menu's Home link goes
  to `ventureauctions.auctioneersoftware.com`). The responses carry no `Server` header and no challenge was met.

### robots.txt and terms (TESTED)

- `https://www.venture-auctions.com/robots.txt`: for `*`, disallows `/admin/`, `/api/`, `/asset/`, and any address
  with `?search`, `?filter`, `?sort`, `?pageSize` or `*_page_size` (also with `&`). Everything used below is allowed.
  It names two sitemaps: `/sitemap.xml` (5 pages) and `/sitemap/past-auctions` (one sitemap per finished auction).
- `/terms` holds only the terms of sale. `/privacy` is an empty page with a heading. **Neither says anything about
  automated access.**
- Each page carries `window.__APP_TOKEN__` (a JWT) for the site's own `/api/`. Not used: `/api/` is disallowed and
  it is an internal API. The document links in the auction record (`/asset/document/...?token=`) are also off limits
  for the same reason (`/asset/`).
- **Rate limit.** Every response has `RateLimit-Limit: 1`, `RateLimit-Remaining: 0` and a `RateLimit-Reset` about a
  second ahead. A request that follows a redirect at once gets **429 "Too Many Requests"** (17 bytes). Seen twice:
  `/auctions/5361/lot/3611` redirects to `/auctions/5361/lot/3611-2009-scion-tc-coupe-2-dr-24l-l4`, and on the sister
  site a slug with a trailing dash redirects to the one without. Those two were the only 429s: the first 12
  requests passed at 2.5-3 s spacing, and the next 14 at 15 s. The shortest safe gap was not measured.

### The pages (all TESTED, 200, tool UA)

| Page | What it gives |
|---|---|
| `GET /auctions` | open and coming auctions. Today one: `Auction.5362`, "Memphis Impound Public Webcast Auction 11/25/2026", `auction_status` 100, 0 lots |
| `GET /past-auctions` and `/past-auctions?page=2` | finished auctions, 20 a page, `total` 31. 29 weekly impound sales from 05/06/2026 to 11/18/2026 and 2 surplus sales (05/08, 06/26) |
| `GET /auctions/{id}-{slug}` and `?page=2..N` | the auction record (times, terms, removal rules, location) and **25 lots a page**, with `total` in the lot query and `front_visible_lot_count` on the auction |
| `GET /auctions/{id}/lot/{lot_id}-{slug}` | one lot: adds all photos (8 on the one read), plain description, bid increments, neighbours. No extra vehicle facts |
| `GET /sitemap/auction/{id}` | every lot address of one auction (9 KB). The cheapest way to count a sale |

The data is in `window.__APOLLO_STATE__ = {...}` in the HTML: keys `Auction.{id}` and `AuctionLot.{lot_id}`.
`va.load(path)` in the scratch folder reads it with `json.JSONDecoder().raw_decode`.

### What a lot states (TESTED on 128 lots of three sales)

    title               "2009  SCION  TC COUPE 2-DR 2.4L L4"          (double spaces as given)
    description         "Year: 2009  Make: SCION  VMS ID# 6510381  Model: TC COUPE 2-DR 2.4L L4  VIN# JTKDE167090282241"
    dynamic_fields      YEAR, MAKE, MODEL as separate values
    lot_number          "1"                    auction_lot_id "3611"       auction_id "5361"
    category.name       "VEHICLE - PUBLIC"     (surplus sale: "VEHICLE - CITY")
    starting_bid        10                     bid_increment_amount 50     required_bid 950
    winning_bid_amount  900                    bid_count 3                 watch_count 16
    is_no_sale          false                  no_sale_status ""           winning_bidder "e****m"
    start_time          2026-11-18T15:30:00Z   end_time 2026-11-18T15:47:56Z (when that lot was hammered)
    primary_image       large/medium/small/thumb on auctioneersoftware.s3.us-east-1.amazonaws.com
    image_count         8                      public_url (the canonical lot address)
    front_lot_location  Memphis, TN            (lot page: "Memphis Impoundment Lot 465 Klinke Ave", 38127)

- **VIN: yes, full, on every lot.** 78 of 78 lots of the 11/18 sale have a 17-character VIN and all 78 pass the
  check digit (`cartrack.vin.valid`).
- **Not stated anywhere: mileage, keys, runs or not, title type, damage.** The terms say why: "No effort has been
  made ... to inspect or verify the condition ... Some vehicles will have keys provided to the purchaser; most
  vehicles will not" and "No effort has been made to research or verify the existing title status".
  The only title mark seen is a title prefix `*FOR PARTS ONLY*` (one lot in the 05/06 sale).
- **Photos:** one on the list page, about 8 on the lot page (64 of 78 lots have 8).
- **Close time:** it is a live webcast, not a timed sale. Prebidding opens Monday 6:00 pm Central
  (`prebid_start_time`), the live sale starts Wednesday 9:30 am Central (`start_time`), and lots sell about one a
  minute (median gap 62 s; the 78 lots took 9:47 to 11:32). A lot's `end_time` is only known after it sells.
- **Fees** are in the auction record, not the lot: 10% buyer's premium, $10 technology fee per item, 4% more on card
  payments. A $575 hammer price is $642.50 in cash.

### Sold prices (TESTED)

- Finished auctions keep `winning_bid_amount` on every lot, and the page shows it ("Completed, Winning Bidder :
  e****m, $900.00, Bids: 3"). `hide_winning_info` is false.
- **How far back: to the first sale on this platform, 2026-05-06** (`/auctions/5324-...`: 114 lots, the 25 on page 1
  all with a price). Sales before May 2026 were on HiBid and are not on this site. HiBid's past pages were not read.
- 11/18/2026 sale, all four pages: **78 lots, 76 sold, 2 marked `is_no_sale` ("no-sale")**. Hammer prices: lowest
  $300, median $575, mean $1,062, highest $6,900 (a 2010 Corvette Grand Sport and a 2021 Kia Soul). 16 sold at
  $1,000 or more, 8 at $2,000 or more. Median model year about 2008, range 1989-2024. Median 10 bids a lot.
- 11/11/2026 sale, page 1 only: 24 sold, median $537.50, range $400-$1,250.
- Cars that fail to sell or are not paid for come back: 5 of the 78 lots on 11/18 were on the city list of 11-09.
  The VIN is the same and the lot id is new.
- Surplus sale 05/08/2026 (`/auctions/5318-...`): 93 lots, description gives `VIN#` and `CITY ID#`. Page 1 is
  retired police cars: Dodge Chargers 2018-2022 at $275-$1,150, a 2019 Durango at $500.

### Weekly volume (TESTED: lot counts from auction pages, auction sitemaps and city PDFs)

| Sale | 05/06 | 05/20 | 06/24 | 07/29 | 09/02 | 10/07 | 10/14 | 10/21 | 10/28 | 11/04 | 11/11 | 11/18 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vehicles | 114 | 58 | 63 | 46 | 49 | 64 | 66 | 53 | 62 | 66 | 108 | 78 |

About 45 to 115 a week, usually around 60 (the 12 sales counted average 69). The past-auction list has an impound
sale for every one of the 29 weeks from 05/06 to 11/18; one was held on a Thursday (09/10). The other sales' lot
counts were not fetched.

### Mapped to the listing record

| Record field | From |
|---|---|
| `source`, `source_id` | a new source name; `auction_lot_id` (new each week, so a re-offered car is tied by VIN) |
| `url` | `public_url` |
| `title` | `title`, spaces collapsed |
| `channel` | `"auction"` |
| `price`, `price_kind` | `winning_bid_amount`. `"sold"` when the auction's `auction_status` is 300 and `is_no_sale` is false. Before the sale: `"starting"` with `starting_bid` (10) when `bid_count` is 0, else `"bid"`. A no-sale lot has a figure but no sale: keep it out of `"sold"` and put `no_sale` in `extra` |
| `ends` | before the sale, the auction `start_time` (lots have no close time of their own); after it, the lot `end_time` |
| `posted` | not given. The lot sitemap's `lastmod` is the Monday morning the catalogue went up |
| `vin` | `VIN#` in `description` |
| `year`, `make` | `dynamic_fields` YEAR, MAKE |
| `model`, `trim`, `body`, `engine` | MODEL is one string, "TC COUPE 2-DR 2.4L L4" or "F-150 4WD STYLESIDE PICKUP 5.4L V8". Older sales give the model alone ("TAHOE"). Decoding the VIN is safer than splitting it |
| `miles`, `condition`, `title_status` | none. `"parts_only"` when the title starts `*FOR PARTS ONLY*` |
| `seller_name`, `seller_type` | "City of Memphis impound (Venture Auctions)"; neither private nor dealer |
| `city`, `state`, `zip`, `geo_how` | Memphis, TN, 38127, `"street"` (465 Klinke Ave; coordinates not looked up) |
| `photos`, `photo_count` | `primary_image.large`; `image_count` |
| `extra` | `lot_number`, `vms_id` (the city's ticket number), `bid_count`, `watch_count`, `auction_id`, fees |

### What was not settled

- **What a lot shows between Monday evening and the sale.** The 11/25 catalogue is not posted yet. On the sister
  site (section 3) an open lot carries the current high bid in `winning_bid_amount`, with `bid_count`. Whether
  Venture's prebids show the same way needs one read on Monday evening or Tuesday.
- The shortest request gap the rate limit allows.
- Whether a datacenter address (GitHub Actions) gets the same answers. Untested.

## 2. The city's own PDF list

- **Where** (TESTED): `https://memphistn.gov/city-auto-auctions` (`https://memphistn.gov/?p=2041` redirects to it).
  WordPress behind Cloudflare, 200 to the tool UA. robots.txt: `Crawl-delay: 10`, nothing disallowed.
  The current list sits in `section.caa-current-card` under "Current Impounded Vehicle Auction List"; today that box
  reads "No upcoming auction lists are available yet." Past lists are `a.caa-archive-link` under "Previous Impounded
  Vehicle Auction Lists": six, from 10-05 to 11-09.
- **No list was posted for the 11/18 sale**, which ran with 78 lots. The page is not a complete record.
- **Address pattern** (TESTED, six links): `https://memphistn.gov/wp-content/uploads/{YYYY}/{MM}/` then either
  `Impound-Sales-List-{MM}-{DD}-{YYYY}.pdf` (10-05, 10-26, 11-02, 11-09) or `{MM}-{DD}-{YYYY}-Sales-List.pdf`
  (10-12, 10-19). The date is the Monday before the sale. The name is not safe to guess: read the link from the page.
  Link labels use the Wednesday in October and the Monday in November.
- **When**: `Last-Modified` is Monday between 9 am and 2 pm Central on five files, and the Friday before on one (10-26).
- **Text or scan** (TESTED): five are Crystal Reports text PDFs (64-75 KB, 5-9 pages, 12 vehicles a page).
  **One (10-05) is a scan** from a Canon copier (439 KB, images only, no text).
- **Columns**: Tag #, Group, Ticket #, Invoice #, Year, Make, Tow Chrg, VIN, Date on Lot, Bidder Name, Bid Amount.
  Group is always "S"; Invoice, Bidder Name and Bid Amount are blank. **VIN: yes. Model: no. Price: no.**
- **Reading it with the standard library** (TESTED, `pdfrows.py`): inflate each page stream, map bytes through each
  font's ToUnicode table (the fonts are subset TrueType with their own byte codes, so the raw strings are gibberish
  without it), and group text by baseline. The report cuts cells at kerning pairs and moves on with the same `Td`
  operator it uses between cells, so a VIN arrives as "1" + "FA6P0H78E5393298". Joining a row with no separator and
  matching its shape works: 66, 53, 62, 65 and 108 rows read from the five text lists, every VIN passing the check
  digit. The one row missed is a 1979 Chevrolet with a 13-character serial. `pdftotext` (Git for Windows) gives the
  same counts.
- **Against the auction site** (TESTED): the 11-09 list has 108 rows and the 11/11 auction has 108 lots. On the 25
  lots compared, VIN, ticket number (= "VMS ID#") and tag number (= lot number) all match.
- **What the PDF adds**: tow charge ($125-$375) and the date the car reached the lot. On the 11-09 list, 71 of 108
  arrived in September-October 2026 and 37 between 2017 and 2021. One date is impossible (a 2016 Dodge "on lot"
  3/9/06), so the column has typing errors.
- **Verdict**: the auction site is the better source in every way but those two columns. The PDF is worth reading
  only as a second look at the VINs or if the auction site ever closes.

## 3. Other sellers within about 60 miles

### HiBid (TESTED; terms forbid it)

- `hibid.com` robots.txt disallows `*/livecatalog/`, `*/webcast/`, `/auctioneer/`, `*/account/`, `*/catalog/print/`,
  `/auctions/past/*?q=*` and a few more. Sitemaps at `cdn.hibid.com/cdn/sitemaps/` hold category pages by state
  (`/tennessee/auctions/700006/cars-and-vehicles`), not auctioneers or catalogues.
- Pages on `hibid.com` are server-rendered with `script#hibid-state`. `GET /auctions?zip=38103&miles=60` lists 9 open
  auctions: Venture's placeholder; ATX Auctions Olive Branch (3 sales, 144-613 lots); PrimeBidz, Hernando MS (4 sales,
  819-1,005 lots); Morris Realty & Auction, Holly Springs MS (1 house). All general merchandise or real estate.
- `GET /lots/700006/cars-and-vehicles?zip=38103&miles=60`: 25 lots, **none a vehicle** (tonneau covers, tire shine,
  tires, a scooter). Lot records carry `lotState.highBid`, `timeLeft`, `priceRealized`.
- **Wall, by terms**: HiBid's Terms of Use (`/home/termsofuse`, last updated 22 November 2022) say users must not
  "conduct any web scraping, web harvesting, web data extraction, or any other data scraping of Auction Information"
  nor "use any robot, spider, scraper, data mining tool ... or any other automated means to access our Sites".
  I read the terms last and stopped there, 13 requests to HiBid hosts in all (robots, sitemaps, six pages, the
  terms). For the owner to decide. Nothing is lost today: there are no
  vehicles on HiBid near Memphis and the city sale is no longer there.

### Walker Auctions, Memphis (TESTED)

- 2749 Park Ave, Memphis 38114. Estate and consignment sales, online only, a vehicle sale now and then.
  `www.walkerauctions.com` (server-rendered; robots disallows `/ajax` and `*/document/`) lists its own sales and
  those of partner firms (Taylor Auction & Realty in Grenada MS, others far away).
- Bidding is on `bids.walkerauctions.com`, **the same Auctioneer Software platform as Venture**: the same robots.txt,
  the same `RateLimit-Limit: 1` header, the same `__APOLLO_STATE__` with `Auction.{id}` and `AuctionLot.{id}`.
  One reader would cover both. This site is behind Cloudflare and answered the tool UA (one 429 after a redirect,
  then 200).
- Today: "Private Estate Auction: Vehicles, Tools, Honda Shadow, and more!" (auction 49244, with Roebuck Auctions),
  95 lots, closing 12/1 from 8:00 pm Central, each lot with its own end time 18 s after the last. First 50 lots
  read (this site serves 50 a page); 4 are vehicles:
  a 2006 Honda Shadow trike (current bid $650, 14 bids), a 1980 Mercedes 280 SL ($850), a 1986 Mercedes 300 SDL
  ($1,050, VIN and mileage in the description), a GMC bus conversion ($100). An open lot shows the current bid in
  `winning_bid_amount`, plus `bid_count` and its own `end_time`. Buyer's premium 15%.
- "Auction Results" page exists (`/search/auctions/all-sales/recently-completed/...`). Prices on it not checked.

### Daily Memphian public notices: tow-lot and garage lien sales (TESTED)

- Tennessee makes a towing firm or garage advertise a lien sale. In Memphis these run in the Daily Memphian.
  robots.txt disallows only `/feed/tag/` and `/start`. No terms-of-use link was found on the pages read.
- `GET https://dailymemphian.com/feed/section/public-noticesmiscellaneous-notices` is RSS with the newest 20 notices
  (title is an ad number such as "MD117766", link `https://dailymemphian.com/article/{id}`). The feed and the list
  page (`/section/public-notices`, 190 pages) cut each notice short. The parent feed `/feed/section/public-notices`
  is empty.
- `GET /article/68753` shows the whole notice without logging in: "The following vehicle(s) will be sold at auction
  by TurboKnights, LLC on 12/05/2026 at 10 am located at 3301 Winbrook Drive, Memphis, TN 38116", then a table
  **YEAR MAKE MODEL VIN#** with two cars. Seller, date, hour, street address, year, make, model, VIN. No price, no
  photos, no mileage.
- Page 1 of the list today has three such notices (TurboKnights, Wilson Imports, Adre's) and one from Choice Towing.
  These are sales of one to a few cars at the seller's own lot, in person.
- REPORTED and not checked: from October 2026 the state is to run an Abandoned Vehicle Portal where towing firms
  and police must post these sales instead of newspapers, searchable by VIN and plate (Department of Revenue pages,
  via search results). `www.tn.gov` answered **403** to robots.txt and to the page, so I stopped. If the portal is
  live, it replaces the newspaper as the source.

### Looked for and not found

- **Shelby County government and Sheriff**: no current public page for surplus or seized vehicles. REPORTED: the
  county bid in 2022 went to Morris Auction Group; an undated Memphis Flyer piece has Roebuck Auctions selling county
  and drug-task-force vehicles. `bids.shelbycountytn.gov` did not resolve from here.
- **City of Memphis other surplus**: on GovDeals (DOCUMENTED, city PDF "Bid on Surplus Items"). GovDeals is an app
  shell with an internal API (note 01).
- **DeSoto County, Southaven, Olive Branch, Horn Lake, West Memphis, Crittenden County**: searches found no auction
  page for any of them, only the state rules (sale by public auction after newspaper notice).
- **Capital Auto Auction "Memphis"** (`capitalautoauction.com/locations/tennessee/memphis`): a marketing page with no
  Memphis address or stock. Not a local sale.
- **Purple Wave "near Memphis"**: the page reads but holds no items in its HTML.
- **Dealer-only** (REPORTED, not public): ADESA Memphis, Dealers Auto Auction of Memphis (Eads), Memphis Auto Auction
  (3719 Old Getwell Rd). MLGW sells surplus through JJ Kane on Proxibid (REPORTED).

## 4. IAA and Copart, Memphis yards

- **IAA Memphis, branch 738** (TESTED, `GET https://www.iaai.com/US/Locations/738`, 200): 3033 Fite Rd, Millington
  TN 38053. "Auction: Open to public buyers." Every Tuesday 9:30 am Central; next sales 11/24, 12/01, 12/08. Preview
  10 am-2 pm the day before. Pay within 2 days; remove within 5 business days; storage $50 a day after that.
  Nearest other branches are over 110 miles away (Grenada, Little Rock, Paducah).
- **Which lots a member of the public may bid on**: IAA's how-to-register page is reported to say that individual
  buyers may bid at auctions open to the public, which varies by state, and only on vehicles that can be sold to
  the public (REPORTED, via search; not fetched). So the limit is per vehicle, and that flag was not read.
- **Walls at IAA**: robots.txt disallows `/Search` and `/Marketing/Search`. **Note 01 section 5 used `/Search`; that
  route is off limits.** The sale list `GET /SalesList/738~US/11242026` (allowed by robots) came back as an Incapsula
  block page ("Request unsuccessful. Incapsula incident ID ..."), the third request to the host, 16 s after the
  second. Stopped. Vehicle count not read.
- **Copart Memphis** (REPORTED, search index of Copart's own pages): one yard, 5545 Swinnea Road, Memphis.
  Copart's Tennessee licensing page is reported to say that private individuals must go through a broker for all
  clean-titled and salvage items, and may buy only boats, jet skis and snowmobiles directly. Copart's general
  "No License Required" page reads the other way, so this is not settled; on the Tennessee page's wording a member
  of the public cannot bid on cars at Copart Memphis without a broker.
- **Wall at Copart** (TESTED): `GET https://www.copart.com/locations` answers 200 with 212 bytes, an
  `/_Incapsula_Resource` script and nothing else. robots.txt disallows `/public/data/` (the lot-detail route in
  note 01) and `/lotSearchResults/`. Stopped. Vehicle count not read.

## 5. What a public buyer faces at the city sale

From the auction's own terms ("EFFECTIVE 07-01-2026", in the 11/25 auction record) and the city page. All DOCUMENTED.

- **Who**: dealers and the general public. A person without a dealer licence may buy **6 vehicles a calendar year**
  (city ordinance). A first-time buyer may win **one** vehicle in their first sale unless approved in person at the
  preview.
- **Registration**: an account on venture-auctions.com (HiBid accounts do not carry over), legal name and address as
  on a government ID, one account each. Register for **each** auction **before 9:00 am Central on Wednesday**.
  Government ID shown in person before any purchase is completed. No deposit is mentioned
  (`payment_authorization_amount` is 0 in the record).
- **Bidding**: online only. Prebids from Monday 6 pm; live webcast Wednesday 9:30 am Central.
- **Preview**: Tuesday 12-2 pm at the Memphis Police Impound Lot, 465 Klinke Ave, Memphis 38127 (run by Vehicle
  Management Solutions). No bags.
- **Fees**: 10% buyer's premium, $10 technology fee per item, 4% more if paid by card.
- **Payment**: in full **by 2 pm Central on sale day**. Cash, card (in person or entered by the buyer online), or
  certified funds payable to Venture Auctions, at the Venture trailer on the lot. Unpaid at 2 pm is a "no sale" and
  a permanent ban.
- **Paperwork**: a paid invoice from Venture and a **bill of sale with odometer statement from the City**. No
  title. The terms call these "wholly sufficient for titling purposes in Shelby County" and leave buyers elsewhere
  to find out for themselves. No warranty against salvage, flood or any title brand. "FOR PARTS ONLY" lots get an
  invoice only and cannot be registered or resold. Odometer statements are collected at City Hall, 125 N. Main,
  Room 546, Monday-Wednesday 9 am-1 pm, or mailed after two weeks.
- **Removal**: by 11:59 pm Friday. Storage fees after that. Anything left at midnight going into Monday is
  re-impounded and sold again with no refund. No repairs on the lot; a car that will not drive must leave on an
  approved tow truck. The buyer carries all risk once the lot is awarded.
- **Condition**: as is. "Many vehicles could potentially run and drive; some vehicles will not." Most have no keys.
- Sales tax is not mentioned in the terms.
- **Surplus sales** differ: city fleet vehicles come with "a clean negotiable title directly from the City of
  Memphis, when applicable" and do not count toward the 6-car limit (site `/terms`, dated 03-01-2026); preview at
  3720 Knight Arnold Rd.

## For the integrator (nothing here was added to the product)

1. **One reader for the Auctioneer Software platform**, taking a base address, serves both
   `https://www.venture-auctions.com` and `https://bids.walkerauctions.com`. Per read: `GET /auctions`, then for each
   auction `GET {public_url}?page=N` until 25 x N reaches the lot `total`. Five or six requests a week for Venture.
   Data: `window.__APOLLO_STATE__`, keys `Auction.*` and `AuctionLot.*`.
2. **Do not follow redirects straight away and do not shorten addresses.** Use `public_url` from the record or the
   address from `/sitemap/auction/{id}` as given. Leave several seconds between requests (15 s was clean; 2.5 s
   passed once). Treat 429 as "come back later" (`fetch.RateLimited` already does).
3. **Do not ask for a bigger page** (`?pageSize=` is disallowed in robots.txt) and do not touch `/api/` or `/asset/`.
   Photo addresses on `auctioneersoftware.s3.us-east-1.amazonaws.com` are the ones to store, not the
   `/asset/image/...` ones.
4. **Weekly rhythm** (Central time): catalogue goes up Monday (sitemap `lastmod` 9:32 am on 11/16; prebids from
   6 pm); sale Wednesday 9:30 am to about 11:30 am. Read Monday evening for the list, Tuesday evening for prebids,
   Wednesday afternoon for results (`"sold"`). The auction moves from `/auctions` to `/past-auctions` once finished.
5. **Sold prices are a local comparable set**: 31 finished sales since May 2026, each lot with a VIN and a hammer
   price. By the average of the 12 sales counted that is about 2,000 prices (an estimate, not a count). Reading
   them all is about 31 x 3 pages. These are impound cars with no keys, no title and unknown
   mileage, so the prices sit far below retail (median $575).
6. **All-in price** for the cost model: `bid x 1.10 + 10`, times 1.04 by card. Add a tow for most cars.
7. **Skip the lot page** unless more photos are wanted: it adds nothing else.
8. **City PDF**: optional. If used, take the link from `section.caa-current-card` on the city page, keep 10 s
   between requests, and expect a scan now and then (no text streams: report "not read", do not guess). The reading
   method is in `pdfrows.py`.
9. **Lien-sale notices**: RSS `dailymemphian.com/feed/section/public-noticesmiscellaneous-notices`, keep items whose
   article text has "will be sold at auction", read `/article/{id}` once each. They have no price, so `price` is
   empty; `ends` is the sale date in the text.
10. **Leave out**: HiBid (terms), IAA `/Search` (robots), Copart and tn.gov (blocked). These need the owner's
    decision, not code.
11. **Correction to earlier notes**: 07-tennessee.md says the sale is "online through Venture Auctions on HiBid";
    it is on venture-auctions.com since May 2026. 01-endpoints-marketplaces.md lists IAA `/Search` as a working
    route; robots.txt disallows it.

## Files

- `research/_scratch/routing/impound/cap/_log.tsv`: every request, time, status, size.
- `cap/sample_venture_lot_3611.json` (one sold lot and its auction, 7 KB), `cap/sample_walker_open_lot_12.json`
  (one open lot with a current bid, 12 KB).
- `cap/va_a5361_lots.tsv`: the 78 lots of the 11/18 sale with VIN and hammer price. `cap/va_lots_sample.tsv`,
  `cap/va_a5360_p1_lots.tsv`: partial tables of two sales.
- `cap/list_2026-*.pdf` and `.txt`: the six city lists. `cap/list_2026-11-09.rows.tsv`: 108 rows read by `pdfrows.py`.
- `cap/va_auction_5362_terms.txt`: the terms of sale as plain text. `cap/hibid_termsofuse.txt`: HiBid's terms.
- `cap/iaai_saleslist_738_1124.html`: the Incapsula block page (client address removed).
  `cap/copart_locations.html`: the 212-byte script page.
