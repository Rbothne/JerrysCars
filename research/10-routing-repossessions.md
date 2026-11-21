# 10. Repossessed cars around Memphis: who sells them to the public, and what a program can read

Worked 2026-11-21 (a Saturday) from a home connection. Plain urllib only, no account, no browser, no cookies kept.
A Chrome user-agent string for the survey; every route marked "works" below was then repeated with the tool's own
`cartrack/0.1` and answered the same, except the state portal (see its section). Roughly 400 requests to 87 hosts
(counted from the captures, not logged one by one): about 60 to repofinder.com, no more than about 10 to any other.
Pace 2.5 s per host.
Scripts, captures and trimmed samples are in `research/_scratch/routing/repos/` (`probe.py`, `batch.py`, `hunt.py`,
`go.py`, `rf_pull.py`, `dailynews_count.py`, `cap/`, and the small `*_sample.json` / `*_block.html` files).
Labels: TESTED = fetched and seen here, DOCUMENTED = read in the source's own text, REPORTED = second-hand.

**The main finding: almost no repossessed car near Memphis is offered to the public on a page.** 19 credit unions
and 17 banks were read on their own sites (6 more banks did not answer). Five credit unions have a vehicle-sale page
that reaches the area, and those pages show **one car between them today, 76 miles out**. The lenders' cars go to
three dealer-only auctions in Shelby County, whose run lists sit behind robots.txt rules or a login. What the public can actually buy, and a program can read, is the
tow-lot and garage **lien sale**: 147 vehicles with VINs in one week of Memphis public notices. Those are not
repossessions in the strict sense, but they are the forced sales that exist here, and title lenders show up in them
as lienholders.

Two other notes written the same day cover the neighbours: `10-routing-impound-auctions.md` (the city impound sale,
HiBid, the Daily Memphian feed) and `10-routing-government-sales.md`. This note does not repeat them.

## Verdict

| Outlet | Address | Vehicles today | Price type | Plain request works? | Worth a reader? |
|---|---|---|---|---|---|
| **Leaders Credit Union** (branches in Bartlett and Arlington; cars kept in Jackson TN) | `www.leaderscu.com/auto-loans/pre-owned-vehicles` | **1** (2023 Mazda CX-5, $20,900) | fixed ask | yes, HubSpot HTML | small one, yes: the only lender near Memphis that posts priced repos steadily (23 since August, 40 this year, by RepoFinder's copies). Lot is about 76 miles out; buyer must be a member |
| Southeast Financial Credit Union (Franklin TN) | `www.southeastfinancial.org/for-sale` | 2 | fixed ask, with NADA value beside it | yes, Squarespace HTML | no for this area: no location per car, head office 187 miles out. Same parser shape as Leaders if wanted |
| Memphis City Employees Credit Union | `www.memphiscu.org/loans/services-offered/auction` | **0** ("no scheduled auctions"), and 0 in three archive copies from 2026 | sealed bids, then an auction | yes, plain HTML | a watcher, not a reader: tell the owner when the sentence changes |
| Success Credit Union (Blytheville AR, about 54 miles) | `www.successcreditunion.com/repossessions` | 0 ("do not have any repossessions available") | sealed bids on a bid form, with an expiry date per vehicle | yes | watcher |
| UPS Employees Credit Union (Memphis) | `www.upscu.org/for-sale/` | 0 ("nothing at this time") | not stated | yes (robots asks 10 s) | watcher |
| Memphis Municipal Employees FCU | `www.mmefcu.org/automobiles-for-sale.html` | none shown; the page says to stop by the branch | - | yes | no |
| Orion, First South, Southern Security, FedEx Employees Credit Association, Hope, UT Federal, Ascend, Navy Federal, Methodist Healthcare FCU, Kimberly Clark CU, LG&W FCU, SecurCommunity (ex Shelby County FCU) | own sites | **no repo page found** | - | - | no |
| Regions, First Horizon, Trustmark, BankPlus, Renasant, Centennial and 11 more banks | own sites | **no vehicle page; real estate only** where anything | - | - | no |
| **RepoFinder** | `www.repofinder.com/wp-json/wp/v2/repo?state=126` | 560 posts for Tennessee, but it is an **archive back to 2019**, not stock. 11 posted this November; every one that names a place near here is a Leaders car in Jackson | free text, mixed | yes, WordPress JSON, robots allow | not as a listing source. Useful once a quarter as a **directory of lenders with repo pages** |
| ADESA Memphis, Dealers Auto Auction of Memphis (Eads), United Auto Exchange (ex Memphis Auto Auction) | see section 3 | not readable | wholesale bids | run lists: robots.txt disallows, or login | no. **Dealer licence needed at all three** |
| IAA Memphis (Millington) | `www.iaai.com/US/Locations/738` | not read | bids | branch page yes; `/Search` is disallowed by robots.txt | no (see note on report 01 below) |
| **The Daily News, public notices** (tow and garage lien sales, Shelby County and some DeSoto) | `www.memphisdailynews.com/notices/2026/Nov/20/` | **102 VINs in 11 notices on 20 Nov; 147 distinct VINs in the week 16-20 Nov** | public auction at the lot, no figure | **yes**, one request per day, full text | **yes.** The best yield here by far. No price, no miles, in-person sales |
| **Tennessee Abandoned Vehicle Portal** (state; tow firms must post there from 25 Jan 2027) | `abandonedvehicles.revenue.tn.gov/api/v1/search?q=` | 7 for the one query sent ("1HG"), 2 of them in Memphis | none | yes with a browser user agent; **403 to `cartrack/0.1`**. Full list needs an API key | **ask the state for a key now**; do not build on the public search |
| Peak Auto Auctions (tow-lot lien sales, online, public) | `peakautoauctionstn.com`, `...ms.com`, `...ar.com` | TN 1 sale (Newport, far east), MS 0, AR 1 sale: **7 cars in Jonesboro**, about 60 miles | online bids from a $400 start | yes, JSON in the page | not yet: nothing in the 60 miles today. Cheap to add if a Memphis tow firm joins |
| Self-storage auction sites | StorageTreasures, Lockerfox | not read | - | StorageTreasures is a script shell; Lockerfox robots disallow `/auctions/` | no |
| Proxibid, Copart | - | - | - | **no: Incapsula** ("Request unsuccessful. Incapsula incident ID ...") | no |

## 1. Lenders, one by one

How "no repo page" was checked (TESTED, `hunt.py`): robots.txt, the home page, and the addresses in the sitemap files
robots names (or `/sitemap.xml`; at most six files a site, passing over blog, news and branch sitemaps), searched for
*repo, repossess, for sale, auction, pre-owned, sealed, bid, vehicles for, liquidat, foreclos, bank-owned,
properties*. A page left out of the sitemap, reachable only through the site's own search box, or a PDF linked from a
deeper page, would be missed.

| Lender | Searched | Result |
|---|---|---|
| Orion FCU (`orionfcu.com`) | 90 home links, 125 sitemap addresses | none. Vehicle pages are loans only |
| First South Financial (`firstsouth.com`) | 206 links, 239 addresses | none |
| Southern Security FCU (`southernsecurity.org`) | 191 links, 129 addresses | none |
| FedEx Employees Credit Association (`fecca.com`) | 373 links, 145 addresses | none |
| Hope CU (`hopecu.org`) | 381 links, 283 addresses | none |
| UT FCU (`utfcu.org`) | 181 links, 169 addresses | none |
| Ascend FCU (`ascend.org`) | 120 links, 137 addresses | only `/foreclosure-notices` (real estate) |
| Navy Federal (`navyfederal.org`) | 231 links, 1,579 addresses (first sitemap file) | none. ADESA Memphis names Navy Federal among its sellers (section 3), so at least some of its cars here go to the dealer sale |
| Methodist Healthcare FCU, Kimberly Clark CU | the pages RepoFinder links | loan pages only, no cars |
| LG&W FCU | RepoFinder's link answers 404; 183 home links, no sitemap | none |
| iTrust FCU | `itrustfcu.com` does not resolve | - |
| SecurCommunity FCU (ex Shelby County FCU) | 111 home links | none |
| Regions | 6,715 sitemap addresses; home page answered "Pardon Our Interruption" | `/real-estate-properties` only |
| First Horizon | 1,212 addresses | `/personal/foreclosures` only |
| Trustmark | 961 addresses | links out to `trustmarkforeclosedproperties.com` (real estate) |
| BankPlus | 368 addresses | `/personal/resources/properties` (real estate) |
| Renasant | 657 addresses | a PDF, `rnst-ore-for-sale-list.pdf` (real estate) |
| Centennial (`my100bank.com`) | 136 links | "Bank Owned Real Estate" |
| Bank of Bartlett, Paragon, Guaranty (`gbtonline.com`), First Security (Batesville), BankFirst (where `sycamorebank.com` now lands), Uplift Bank (where `banksouthern.com` now lands), First National Bank of Eastern Arkansas, Independent Bank, BankTennessee, INSOUTH, Park National (where `firstcnb.com` now lands) | home and sitemaps | none |
| Cadence | 403 "Access Denied" (Akamai) on every address | not read |
| Financial Federal, Evolve, Triumph, Patriot, Fidelity National (West Memphis) | timed out, empty answer, no DNS, or a parked domain at the host I tried | not settled |

RepoFinder's own state lists agree: it marks Regions, First Horizon, Renasant, Trustmark, BankPlus and Cadence
"(Real Estate)".

### Leaders Credit Union (TESTED: plain, one car)

- `GET https://www.leaderscu.com/auto-loans/pre-owned-vehicles` gives 200, 175 KB, HubSpot. robots.txt disallows only
  HubSpot preview addresses.
- Each car is one block, `div.paragraph-gallery` > `div.content-paragraph` (sample `leaders_listing_block.html`):

      <div class="h2">2023 Mazda CX-5 Utility 4D S Premium Plus AWD 2.5L I4</div>
      <div class="h5">$20,900.00</div>
      <ul><li>Vin # JM3KFBEM4P0116527</li><li>131,751 miles</li><li>No Money Down</li>
          <li>$1,551 sales tax</li><li>Location: 138 North Star Dr., Jackson, TN</li>...

  Photos are `https://www.leaderscu.com/hs-fs/hubfs/<name>.jpg?width=...` in the same block.
- Written by hand, so expect drift: one past car (seen through RepoFinder's copy) had a stray character after the VIN,
  another wrote "Miles" with a capital.
- The page's own words: Leaders "resells repossessed vehicles", each is "inspected and reconditioned by an independent
  third party", and "membership is a requirement" to buy ($25 once).
- Volume (TESTED through RepoFinder's copies, 51 posts since January 2024 that all read "Location: 138 North Star
  Dr., Jackson, TN"): 40 posted in 2026, 23 of them from August to 13 November, $6,900 to $55,900. Today the page
  itself shows one. So cars sell or come down within weeks. RepoFinder may not copy every car.
- Its sitemap has branch pages `/locations/bartlett-memphis` and `/locations/arlington` (addresses seen, pages not
  read). The cars sit in Jackson, about 76 miles from the home point by rough coordinates.

| Listing field | From |
|---|---|
| `source`, `source_id` | `leaderscu.com`, the VIN (the page has no id of its own) |
| `url` | the page address (there is no page per car) |
| `title`, `year`, `make`, `model`, `trim` | `div.h2`, split after the year and the make |
| `price`, `price_kind` | `div.h5`, `ask` |
| `vin`, `miles` | the "Vin #" and "miles" list items |
| `city`, `state`, `geo_how` | the "Location:" item; `street` |
| `seller_name`, `seller_id` | "Leaders Credit Union", `leaderscu.com` |
| `photos` | the block's `hs-fs/hubfs` images |
| `extra` | `{"repo": true, "members_only": true, "sales_tax_quoted": 1551}` |

`complete` can be True: the whole stock is on the one page.

### Southeast Financial Credit Union (TESTED: plain, two cars, no location)

- `GET https://www.southeastfinancial.org/for-sale`, 200, Squarespace. robots.txt disallows `/config`, `/search`,
  `/account`, `/api/`, `/static/`; this page is allowed.
- Each car is an `h3` with year, make, model, then `p` lines (sample `sefcu_listing_blocks.html`):
  "Crew Cab RST 4WD 5.3L v8 / Miles: 17,650 / Color: Blue / VIN: 1GCUKEED3SZ248956", "Title Status: Clean",
  "$53,975 NADA Value | Listing Price $52,000 / Reduced Price: $43,180". The second car: 2022 Nissan Altima,
  112,736 miles, $13,450 NADA, listing price $11,433.
- Price rule: take "Reduced Price" when present, else "Listing Price". Keep the NADA figure and the first listing
  price in `extra`; the lender is stating its own discount (20% under NADA on the truck).
- No town is given for either car. Head office is Franklin, 187 miles out. Its blog has a post
  "cordova-branch-closing" (address seen in the sitemap, not read). Out of area unless the owner calls and asks.

### Memphis City Employees Credit Union (TESTED: plain, empty)

- `GET https://www.memphiscu.org/loans/services-offered/auction`, 200. robots.txt has no rules.
- "Notice of Public/Private Sale. There are currently no scheduled auctions at this time." Then the standing rules:
  sealed bids accepted, a member's bid amount is put on hold, a non-member sends a cashier's check with the bid, cash
  or cashier's check only, the credit union may bid and may reject all bids, $200 fee for backing out, questions to
  Debt Solutions 901-321-1250. Office 2608 Avery Ave, Memphis 38112.
- Wayback has three different copies from 2026 (14 Jan, 16 Apr, 11 Jun); all three say no auctions are scheduled, in
  slightly different words. So I never saw what a posted car looks like here, and the "no auctions" sentence is edited
  by hand. A watcher should compare the text of the block under the heading, not look for one exact sentence.

### Success Credit Union, UPS Employees Credit Union, Memphis Municipal Employees FCU (TESTED: plain, empty)

- Success CU: "We currently do not have any repossessions available." Bids go on a "Repossession Bid Form", in person
  at 211 N. Broadway, Blytheville AR, by mail or by fax, "before bid expiration dates shown for each vehicle".
- UPS Employees CU (1814 E. Brooks Rd, Memphis): "Well we have nothing at this time, but you can always check with
  Groove Car". robots.txt asks a 10 s crawl delay.
- MMEFCU (577 Dr. Martin Luther King Ave, Memphis): "Automobiles are available for purchase at our Credit Union ...
  Stop by the credit union often to see our great deals!" Nothing is listed on the page. A phone call, not a reader.

## 2. Aggregators and shared platforms

No platform is shared by the lenders here. Each page above is hand-made on a different site builder (HubSpot,
Squarespace, WordPress, Weebly). No embedded widget and no PDF list was found on any of them.

### RepoFinder (TESTED: plain JSON, but an archive)

- robots.txt: disallows `/wp-admin/` (allows `admin-ajax.php`), `/wp-content/upgrade/`, `/tag/`. Nothing about
  `/wp-json/` or `/repo/`. Its `/legal/` page is a disclaimer about sellers and accuracy; I searched it for *scrap,
  robot, automat, spider, crawl, harvest* and found none. Hosted on WP Engine behind Cloudflare; no challenge met.
- Every listing page links its own JSON, and the WordPress route answers with no key:

      GET https://www.repofinder.com/wp-json/wp/v2/repo?state=126&per_page=100&page=N
          &_fields=id,date,modified,link,title,content,vehicle_type,featured_media

  Headers `X-WP-Total: 560`, `X-WP-TotalPages: 6`. State ids from `/wp-json/wp/v2/state?per_page=100`:
  Tennessee 126 (560 posts), Mississippi 122 (143), Arkansas 94 (219). Vehicle types from `/wp-json/wp/v2/vehicle_type`
  (car 104, suv 105, truck 110, ...). There is no radius or town filter; state is the finest cut.
- Fields: `id`, `date`, `modified`, `link`, `title.rendered`, `content.rendered` (the lender's own words pasted in),
  `vehicle_type`, `featured_media`. A 17-character VIN appears in 377 of 560 Tennessee posts, 27 of 143 Mississippi,
  9 of 219 Arkansas; a dollar figure in 312, 91 and 162. Sample `repofinder_posts_sample.json`.
- **It does not remove sold cars.** Tennessee posts by year: 38 from 2019, 82 from 2020, ... 88 from 2026. The listing
  page says so itself: "Some listings are still available and others may already be sold, but this page remains part of
  our historical repo archive". The state counts sum to 38,512 posts nationwide.
- **It does not name the seller.** The public page shows "Price: Taking Bids", "Location: Alabama, Tennessee" and a
  button "Join Repo Finder to Bid Now" (the paid RepoFinder Pro). Its JSON-LD gives `price: "0"` and the seller as
  RepoFinder.com. The town is known only when the lender's pasted text happens to carry it.
- For this area: of the Tennessee posts, 51 name a town I searched for, and all 51 are Leaders cars in Jackson. No
  Mississippi or Arkansas post names a town within 60 miles. Posted this November: Tennessee 11, Mississippi 3,
  Arkansas 15.
- The useful part is the directory. `GET /state/tennessee/` (also `/mississippi/`, `/arkansas/`) lists lenders as
  `/go/<slug>/` links; each `/go/` page is an interstitial whose `<meta http-equiv="refresh">` holds the lender's own
  address. That is how the MCECU, MMEFCU, UPS, Leaders and Success pages above were found. Some targets are stale
  (LG&W 404, iTrust gone, Southeast Financial points back at RepoFinder).

### Peak Auto Auctions (TESTED: plain, complete, nothing in range today)

Not lender repos: tow firms' unclaimed cars, sold online to anyone. Included because RepoFinder lists it under every
state and it reads cleanly.

- One site per state: `peakautoauctionstn.com`, `peakautoauctionsms.com`, `peakautoauctionsar.com`. robots.txt on
  each: `User-agent: *` / `Disallow:` (nothing barred). The terms text carried in the page (14 KB) has none of
  *scrap, robot, automat, crawl, spider, harvest*. Main site FAQ: "Do I need a special license ...? No, Peak is open
  to the public."
- The pages are a Laravel app that ships its data in `<script data-page="app" type="application/json">`:
  1. `GET https://peakautoauctionsar.com/` gives `props.auctions[]`: `id`, `name`, `starts_at`, `ends_at`,
     `counts.lots`, `links.index`.
  2. `GET <links.index>` gives `props.lotIds` (and `props.auction.location` with street, city, state, zip).
  3. `GET https://peakautoauctionsar.com/auction/3782/lots?ids=57637,57638,...` gives `{"lots":[...]}`. The same
     address with no `ids` gives `{"lots":[]}`; with `ids[]=` it gives 500.
- Lot fields (sample `peak_lot_sample.json`): `name`, `starting_bid`, `current_bid`, `minimum_bid`, `ends_at`,
  `status`, `counts.bids`, and `item`: **`vin` (full)**, `year`, `make`, `model`, `mileage`, `color`, `key`, `runs`,
  `drives`, `title_status`, `catalytic_converter`, `airbag_status`, photos in `assets`.
- Today: Tennessee one sale (Wilton Springs Towing, Newport, the far east of the state). Mississippi none. Arkansas
  one: Neat's Towing, 5400 Stadium Blvd, Jonesboro, 7 cars from a $400 start, closing 30 Nov, 13.5% buyer's premium
  and a $50 deposit. A 2016 Jeep Compass with 65,008 miles and a 2023 Outlander Sport with 54,039 are in it.
  Jonesboro is 58 to 61 miles by rough coordinates, on the edge of the circle.

### Others

- **U.S. Bank "auto sales"** (`auto-sales.usbank.com`, where RepoFinder's "US BANK REPOS" link goes): a marketplace of
  participating dealers' stock, not repos. robots.txt is `Disallow: /`. Off limits and off topic.
- **Proxibid**: 403 with an Incapsula page on robots.txt and on the vehicles page. Stopped.
- **HiBid**: searches for "repo", "repossessed" and "bank owned" within 60 miles of 38103 each returned
  `totalCount: 0`. The impound note found that HiBid's terms forbid automated access; I had not read them, made six
  requests there, and stopped.
- **Capital Auto Auction "Memphis"**: a marketing page for an online sale held elsewhere (it says its stock includes
  "repossessions"). No Memphis yard.
- Older credit-union repo marketplaces named in the trade press (TitleAuctions, SmartCarAuctions, LiveRepos) are
  2003-2010 stories (REPORTED). None of the lenders here links to one.

## 3. Where the rest go: the wholesale auctions

| Sale | Where, when | Who may buy | Repo sellers named | Run list |
|---|---|---|---|---|
| **ADESA Memphis** | 5400 Getwell Rd, Memphis. Every Tuesday: in-op and specialty 8:30, fleet/lease and dealer consignment 9:00 CT (TESTED, its page) | Dealers. "Most ADESA auctions are for licensed, registered car and specialty dealers only"; its public-auction list names only Cincinnati/Dayton and Cleveland (DOCUMENTED, `adesa.com/public-auctions/`) | Ally, American Credit Acceptance, Bridgecrest, Navy Federal Credit Union, PAR North America, PRA Receivables, Primeritus Remarketing, Remarketing Solutions, U.S. Bank, World Omni, and rental fleets (TESTED, "featured consignors" on its page) | behind login (`buy.adesa.com`). Not tried |
| **Dealers Auto Auction of Memphis** | 11713 US-64, Eads (about 23 miles). Thursdays, in-ops 8:30, lanes from 9:00 (TESTED, EDGE Pipeline page). Thanksgiving week: Tuesday 24 Nov | Dealers. "all other consignment privileges are exclusively available to licensed, registered dealers"; GSA and TVA fleet sales are public "at some locations", Memphis not named (DOCUMENTED, `dealersauto.com/memphis/`) | Credit Acceptance, UACC, "national and regional financial institutions" (same page) | on `edgepipeline.com`; its robots.txt disallows `/components/report`, `/components/event`, `/components/vehicle`. Not read |
| **United Auto Exchange Memphis** (`memphisautoauction.com` now redirects to `uaxmemphis.com`) | 3710 Prescott Rd, Memphis. Wednesdays, in-op 8:00, drive-through 9:15 (TESTED) | Dealers: registration asks for "your dealer license number" and AuctionACCESS (DOCUMENTED, `/dealers`) | not listed; the site says Bridgecrest named it auction of the year 2025 | `tools.uaxmemphis.com/components/report/presale/...`, same EDGE software, same robots.txt disallow. Not read |
| IAA Memphis | 3033 Fite Rd, Millington (about 15 miles). Tuesdays 9:30 CT | "Auction: Open to public buyers" (DOCUMENTED, branch page) | insurance cars mainly; no repo seller named | `/Search` is disallowed by IAA's robots.txt |
| America's Auto Auction | - | dealers | - | its site lists no Memphis or Tennessee sale (TESTED: neither word is on the page its `/locations/` address lands on, which lists its sales) |
| Manheim | no Memphis sale found | dealers (DOCUMENTED in report 06) | - | its locations page carries no list in the HTML; not settled which Manheim sale is nearest |
| Copart Memphis | - | - | has a "repossessions" quick-pick page (REPORTED via search) | Incapsula block on that page. Stopped |

- **No public auto auction selling lender repos was found** in Memphis, Southaven, Olive Branch, Horn Lake, West
  Memphis or Jackson TN (four web searches; REPORTED absence, not proof). Tennessee does have a licence class for one
  (DOCUMENTED, tn.gov "Public Automobile Auction": a used-car dealer with a $50,000 bond, a designated public
  automobile auctioneer). The state's roster of who holds it was not searched; that would settle this.
- "Dealers Auto Auction Jackson" is Pearl, Mississippi, not Jackson, Tennessee.
- **Buy-here-pay-here lots with a "repo" inventory: none found.** No title, seller name or `extra` among the
  catalogue's 4,823 listings contains "repo" or "repossess", no dealer in `dealers.json` is named that way, and a
  search turned up none. These lots resell their own repossessions as ordinary stock without saying so.
- For a buyer without a licence the dealer sales are closed. Report 06 already notes that unlicensed buyers use brokers
  for Copart and IAA; nothing equivalent was found for ADESA, DAA or UAX.

## 4. Lien sales: tow lots, garages, title lenders, storage

Why lenders' repos are not in the paper: a secured lender must tell the borrower before selling, but nothing found
requires a public advertisement (REPORTED, search summaries of T.C.A. 47-9-611 and of the title pledge act,
45-15-114, which asks for a commercially reasonable sale and the surplus back to the borrower; the statutes were not
read here). A tow firm or garage selling for unpaid charges must advertise (REPORTED; Peak's Tennessee sale cites
T.C.A. 66-19-103 for its paperwork). So the newspaper holds the lien sales and not the bank repos.

### The Daily News, Memphis (TESTED: plain, a whole day in one request)

- robots.txt: `User-agent: *` / `Allow: /notices/` ... `Disallow: /`. The notices path is the one it opens.
- `GET https://www.memphisdailynews.com/notices/2026/Nov/20/` gives 200, 150 KB, every notice printed that day with its
  full text. `/Nov/3/` and `/Nov/03/` both work. Sections: foreclosure, court, bid, miscellaneous; the cars are under
  `<a id="misc">`. Each notice is a table row:

      <td><a href="javascript:OpenChildFT2('MD117766','11%2f20%2f2026')">View</a></td>
      <td style="width:400px;"><p>NOTICE OF PUBLIC SALE</p><p>The following vehicle(s) will be sold at auction by
      TurboKnights, LLC on 12/05/2026 at 10 am located at 3301 Winbrook Drive, Memphis, TN 38116</p>...
      <p>YEAR MAKE MODEL VIN# </p><p>2018 Kia Optima KNAGT4L30J5232389</p>...

  The id (`MD117766`) is the same ad number the Daily Memphian shows, so the two sites carry the same notices. The
  impound note reads them through the Daily Memphian's feed and one request per notice; this page does a day at once.
- Counts (`dailynews_count.py`): 16 Nov, no notices of any kind. 17 Nov, 10 vehicle notices, 33 VINs. 18 Nov, 3 and 12.
  19 Nov, none of any kind. 20 Nov, 11 and 102. **24 notices and 147 distinct VINs in the week; 145 of 147 VIN
  occurrences pass the check digit** in `cartrack/vin.py`. 3 Nov: 5 vehicle notices.
- Sellers on 20 Nov: towing firms (901 Express Towing with 24 cars, Adre's Wrecker Service, a lot at 3501 Knight Arnold
  with 35), garages and small dealers (Wilson Imports, Immaculate Auto Sales, Lamar Auto Center), one sale in Southaven
  MS (1376 Brookhaven Dr, 14 Dec). Sale dates run 2 to 4 weeks after the notice.
- Wording varies by advertiser: "YEAR MAKE MODEL VIN#" tables, "2011 BMW 335i - VIN# ...", "22 Toyota 4T1G11AK8NU618521"
  under a lot name, dates as `12/05/2026`, `12-05-2026`, `12\03\2026`, `12/14/26`. A reader should anchor on the VIN and
  take the words before it, and take the sale date and address by pattern, leaving them empty when unsure.
- **Some notices print the owner's name and the lienholder beside each car.** On 20 Nov three tow notices did, and
  the parties named included TMX Finance (TitleMax), Neighborhood Title Loans, a used-car lot and an insurer. So
  title-loan cars do reach these sales, by way of the tow lot. The owner names are personal data: read past them, never
  store them. The lienholder is worth keeping as a flag.
- How far back: 3 Nov answers in full; 20 Aug 2026 and 20 Nov 2025 answer with zero notices. Somewhere between 18 days
  and 3 months is kept. Read daily and keep your own copy.
- Not there: price, mileage, photos, condition, whether it runs. The sale is in person at the lot.

| Listing field | From |
|---|---|
| `source`, `source_id` | `memphisdailynews.com`, ad number + VIN (`MD117766:KNAGT4L30J5232389`) |
| `url` | the day page |
| `title`, `year`, `make`, `model` | the words before the VIN |
| `vin` | the 17 characters; `vin_ok` comes from `make_listing` |
| `price`, `price_kind` | none; `starting` fits best of the five kinds, with no figure |
| `channel`, `ends` | `auction`, the sale date and hour |
| `seller_name` | the firm in the notice |
| `city`, `state`, `zip`, `geo_how` | the sale address; `street` if geocoded, else `zip` |
| `posted` | the day of the page |
| `extra` | `{"lien_sale": true, "in_person": true, "sale_address": ..., "lienholder": ..., "notice": "MD117766"}` |

`complete` should be False: a notice is an announcement, and the car may be reclaimed before the sale.

### Tennessee Abandoned Vehicle Portal (TESTED: live, public search works, list needs a key)

- DOCUMENTED (tn.gov, Department of Revenue): the portal "became operational October 27, 2026". Towing firms,
  garagekeepers and police "are not required to utilize the portal until January 25, 2027"; from then they must enter
  every abandoned or immobile vehicle and "advertise the public sale" there. REPORTED (search summary of the same
  pages): newspaper advertising ends 90 days after the portal opened. If so, the Daily News route above dries up at
  the end of January 2027 and this becomes the only source.
- The portal is `https://abandonedvehicles.revenue.tn.gov/`, "Powered by Autura". `/robots.txt` answers 404. It
  publishes `/api-docs` (DOCUMENTED there):
  - `GET /api/v1/search?q=<3 or more characters of a VIN or plate>`: "No authentication required", the same search as
    the public page. Rate limit 2,000 requests per 5 minutes per address.
  - `GET /api/v1/notices?limit=100&offset=N&status=active|sold|closed` and `GET /api/v1/notices/{id}`: need an
    `X-API-Key`, "issued to approved integration partners". The detail adds `storage_address`, `storage_zip`,
    **`sale_date`, `sale_time`**, `payment_methods_accepted`, `image_urls`. Owner and lienholder names are never
    returned at these tiers.
- TESTED: `GET /api/v1/health` gives `{"status":"ok",...}`. `GET /api/v1/search?q=1HG` gives 7 notices, two stored in
  Memphis, with `id`, `status`, `vin`, `plate_number`, `plate_state`, `vehicle_year`, `vehicle_make`, `vehicle_model`,
  `vehicle_color`, `storage_city`, `storage_state`, `storage_daily_rate`, `publisher_name`, `created_at`. No sale date
  at this tier. Sample `tn_portal_search_sample.json` (plates removed).
- **User-agent rule:** `cartrack/0.1`, `Mozilla/5.0 (compatible; cartrack/0.1)` and `curl/8.0` each get **403** from
  the load balancer (`Server: awselb/2.0`). A Chrome user-agent string gets 200. The documentation does not mention
  this.
- A notice here is a towed car its owner may still collect. Only one with a sale date is for sale, and the sale date
  is behind the key. Walking the public search by VIN prefix to rebuild the list would work against the way the state
  split the tiers, and it returns plates. I sent one search and stopped.

### Other notice sites

- `tnpublicnotice.com` (Tennessee Press Association; lists The Commercial Appeal, The Daily News, the Collierville
  Herald-Independent and others), `mspublicnotices.org`, `arkansaspublicnotices.com`: one platform, ASP.NET forms with
  the session in the address. robots.txt allows `/`. No captcha on the search form. One hand-built search post for
  Shelby County answered **500** (the form depends on fields its script fills). Not pursued. **Not settled: whether The
  Commercial Appeal carries vehicle notices that The Daily News does not**, and the same question for DeSoto and
  Crittenden county papers.
- Self-storage: one U-STOR auction notice appeared in the Daily Memphian list in October and one PODS notice on 20 Nov;
  neither lists vehicles. StorageTreasures' Memphis page is a script shell with no auctions in the HTML. Lockerfox
  robots.txt disallows `/auctions/` and `/public-notices/`. Storage units are sold as contents; a car in one would be
  named in the paper notice, which the Daily News route already reads.
- Title lenders: no page of their own was found for repossessed cars in Shelby County. Seen only as lienholders in tow
  notices (above). Where TitleMax and the rest sell what they repossess themselves is **not settled**.

## Mistakes in my own probing, for the record

- Crawl delays read late: `southernsecurity.org` and `gbtonline.com` ask 10 s and got about six and eight requests at
  2.5 s; `upscu.org`, `kimberlyclarkcu.org`, `memphistn.gov` and `adesa.com` got two each at 2.5 s. The scripts now take
  the delay from robots.txt before the next request.
- `auto-sales.usbank.com`: robots.txt is `Disallow: /`; the batch script had already asked for the home page. One page,
  nothing further.
- `www.tn.gov/robots.txt` reset the connection for the Chrome user agent and answered `Allow: /` for `cartrack/0.1`,
  the reverse of what the impound note saw. Three tn.gov pages were read before that was known.
- Captured notice pages in `cap/` contain owners' names as printed by the paper. The trimmed samples leave those
  notices out, and plates are removed from the portal capture.

## For the integrator

1. **Build the Daily News reader first.** `GET https://www.memphisdailynews.com/notices/{YYYY}/{Mon}/{D}/` once a day,
   rows under `a#misc` that hold a 17-character VIN and "sold" or "auction". It is not a dealer reader: no `dealer`
   row, `channel="auction"`, no price, `complete=False`. Drop owner names at parse time. Its value is the VIN list and
   the sale date; `value.py` has to price each car from the VIN decode alone.
2. **Write to the Department of Revenue for a portal API key now** (the docs name "approved integration partners").
   From 25 January 2027 the portal is where lien sales must be advertised, and `/api/v1/notices?status=active` with
   `sale_date` is exactly the feed wanted. Until there is a key, leave the portal alone. If a key comes, the tool's
   user agent still gets 403; that needs raising with them too.
3. **Leaders is a 40-line reader**, shaped like the dealer readers (`read(dealer, get, seen)`, one request, complete).
   It needs a seller row with the Jackson lot's coordinates, and it is outside the 60-mile circle, so the owner must
   decide whether a lender's lot at 76 miles counts. Southeast Financial is the same shape and further out.
4. **Watch three pages instead of reading them**: MCECU, Success CU, UPS Employees CU. One GET a day each (UPS asks
   10 s between requests), compare the text under the heading with yesterday's, raise an alert on change. The sales are
   sealed bids, so there will never be a price to catalogue; the alert is the product.
5. **The record has no place for these sellers.** `SELLER_TYPES` is private or dealer; a credit union and a tow lot
   are neither. `CHANNELS` has no "lender site" or "notice". Either add values or leave `seller_type` empty and carry
   `extra.repo` / `extra.lien_sale`, so the page can filter on them. The owner asked for repos by name, so a filter
   he can see matters more than the label.
6. **RepoFinder: do not catalogue it.** It never marks a car gone, hides the seller, and has no place finer than the
   state. Use `/state/<name>/` and the `/go/` links two or four times a year to find lender pages that have appeared.
7. **Peak**: nothing to read in range today. The three state home pages cost three requests; a weekly check of
   `props.auctions[]` for a location within 60 miles is enough to know when to build it. Jonesboro (7 cars, closing
   30 Nov) is at the edge.
8. **Dealer auctions are closed twice over**: licence to buy, robots.txt or login to read. Do not build. If the owner
   takes the dealer licence in report 05, ADESA, DAA and UAX become his main supply, and their run lists come with the
   account.
9. **Report 01 needs a correction**: it calls IAAI "plain stdlib works" through `/Search`. IAA's robots.txt disallows
   `/Search` and `/Marketing/Search`.

## Not settled

- Whether any Tennessee-licensed public automobile auction operates within 60 miles (the state roster was not searched).
- Where the title lenders sell their own repossessions.
- What the MCECU and Success pages look like with a car on them (never seen; no archive copy has one).
- Whether The Commercial Appeal, the DeSoto Times-Tribune or the West Memphis paper carry vehicle notices the Daily
  News lacks.
- How many days of notices the Daily News keeps (more than 18, fewer than about 93).
- Whether the portal's 403 for non-browser user agents is deliberate.
- Lenders not reached: Cadence (403), Financial Federal, Evolve, Triumph, Patriot (no answer or wrong host). Lenders
  never tried: the smaller DeSoto and Crittenden county banks beyond those named.
- Manheim's nearest sale, and whether any Manheim, ADESA or DAA sale near here ever opens a lane to the public.
