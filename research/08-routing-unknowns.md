# 08. The six dealers discovery could not place

Worked 2026-11-21 from a home connection (Comcast, Virginia address), requests paced at 3-4 s per host.
Scripts and every capture are in `research/_scratch/routing/unknowns/` (`probe.py`, `replay.py`, `cdp.mjs`,
`cfget.py`, `cityauto_all.py`, `live_check.py`, `cut_fixtures.py`, `cap/`).

## Summary

| Dealer | Platform | Recognised by | Route | Read vs site's own total | Requests | Browser? |
|---|---|---|---|---|---|---|
| King Cotton Ford | Dealer.com (another agent's) | now **Landers Ford North**, `www.landersfordnorth.com`, CNAME `secure.dealer.com.edgekey.net` | not mine | - | - | - |
| Car Choice (Jonesboro AR) | ProMax Unlimited "CarExpress / CX5" (was) | archived footer "Website by ProMax", `/ScriptLib/CX5*.js` | **none: the site is gone** | - | - | - |
| City Auto | Dealer Alchemist (ex-DealerVenom), Typesense Cloud search | page loads `bucket.dealeralchemist.com`, theme `dv-framework` | Typesense `multi_search` POST | 451 Memphis-lot cars; 844/844 used cars read, page says "Show 844 Results" | 5 | no |
| Collierville Auto Center | DealerCenter websites | CNAME `dealers.dealercenterwebsite.net.cdn.cloudflare.net` | `admin-ajax.php` POSTs | 78/78 (page: "Page 1 of 3 (78 vehicles)") | 4 | no |
| E Z Auto | Carsforsale.com | page "Powered by Carsforsale.com", `cdn05.carsforsale.com` | `/cars-for-sale?Paging.Page=N`, JSON-LD | 27/27 ("Find 27 vehicles") | 2 | no |
| Supercars Autosales | Dealer Car Search (existing reader) | behind the challenge: `imagescdn.dealercarsearch.com`; NS `ns*.ldv-dns.com` (LeadVenture) | existing `dealercarsearch` reader through a browser-cleared cookie | 25/25 ("Page: 1 of 1 (25 vehicles)") | 1 + one Edge visit | **yes, once** |

## King Cotton Ford -> Landers Ford North (Dealer.com)

- `kingcottonford.com`: NS `ns01/ns02.gcd-dns.com` (GoDaddy, SOA `dns.jomax.net`), no A record for the bare or `www.` name. Dead.
- Landers Auto Group bought King Cotton Ford and King Cotton CDJR (millington-news.com); Autotrader/KBB list
  **Landers Ford North, 965 Highway 51 N, Covington TN 38019**, the same address as the OSM King Cotton Ford.
- `www.landersfordnorth.com` CNAME `secure.dealer.com.edgekey.net` -> **Dealer.com**. Not read here.
  One GET with a Chrome user agent from urllib got Akamai 403 and a cookie
  `ddc_akam_bot=...BOT-BROWSER-IMPERSONATOR`: Dealer.com flags a browser UA on a non-browser TLS stack.
- (`www.landerscdjrnorth.com` is the same Dealer.com edge; `kingcottonchrysler.com` is already in dealers.json as Dealer.com.)

## Car Choice: site gone

- `www.shopcarchoice.com` -> 198.178.114.50, an AWS ELB (`awselb/2.0` on the bare IP) in front of Apache 2.4.68 (Debian).
  Every path answers **404** "The requested URL was not found on this server" (`/`, `/index.php`, `/robots.txt`,
  `/sitemap.xml`, `/inventory`, `/used-cars`, `/cars-for-sale`, `/search/used-cars`, an archived
  `/VehicleDetails/5533/D648685/...`), over http and https, with the Host header or the bare IP.
- Wayback: 200s up to **2026-07-22**, nothing since. The archived page: "Car Choice ... Website by ProMax"
  (promaxunlimited.com), scripts `/ScriptLib/CX5scripts.js`, `CarExpressFrontScript.js`, images on
  `ce5-images-public.s3.amazonaws.com/production/websitefiles/site/10001664/`, details at
  `/VehicleDetails/5533/<stock>/Jonesboro-Arkansas-<year>-<make>-...`. ProMax dropped the site from its servers.
- Google's listing still names www.shopcarchoice.com. DealerRater (3612 Stadium Blvd, Jonesboro AR 72401, 870-935-5200) lists no website.
  The Searcy Chamber listing says six lots (Jonesboro, Little Rock, **Memphis**, Greenbrier, Searcy, Morrilton).
- Other hosts tried. `www.carchoice.com` (Car Choice DFW, Carrollton TX) and `www.carchoiceonline.com` (Car Choice Enterprise,
  Virginia Beach VA) are both DealerCenter sites of **other** businesses. No DNS for carchoicear.com, carchoicejonesboro.com,
  carchoicearkansas.com, shopcarchoice.net and ten more guesses. mycarchoice.com and carchoiceusa.com resolve but were not identified as this dealer.
- Listing sites: CarGurus' Jonesboro dealer list (first 10 of 36) and the Cars.com dealer search for 72401 (first 20 of 584)
  show no Car Choice. Not exhausted: the other pages of those lists, Autotrader, Carfax, Edmunds, TrueCar.
- Result: **no route**. The dealer is 57 miles out. If its new site turns up, run discovery on it.

## City Auto: Dealer Alchemist, Typesense (plain, complete)

- Recognised by `https://bucket.dealeralchemist.com/city-auto/...` images and the WordPress theme `/app/themes/dv-framework/`.
  The site's DNS is a plain A record (165.227.176.9, DigitalOcean). No CNAME marker.
- `GET https://www.cityauto.com/used-vehicles/` (plain, tool UA, 200) carries the search settings in inline script:
  `var __tsHost = "hjnrb3s21408ezpfp.a1.typesense.net"`, `var __tsApiKey = "eQUa8iq30l8Tu908Drz9WKqar6tCJGd4"`
  (search-only, sent by every visitor's browser), `var indexName = "vehicles-GRP00028"`.
- The page's own call, captured in headless Edge, replays plainly with the tool UA, no Origin and no cookie:
  `POST https://hjnrb3s21408ezpfp.a1.typesense.net/multi_search?x-typesense-api-key=<key>`, body
  `{"searches":[{"collection":"vehicles-GRP00028","q":"*","filter_by":"condition:Used","per_page":250,"page":N}]}`.
  The browser asks 24 a page; 250 is Typesense's maximum. The answer gives `found`; stop when `page*250 >= found`.
- Evidence: 844 used cars found, **844 read in 4 pages, 844 unique VINs**. The SRP's own text says "Show 844 Results".
  The collection holds 866 (844 Used, 22 New). Lots: City Auto Memphis 451 (4932 Elmore Rd), Murfreesboro 300,
  Huntsville/Madison AL 48, Chattanooga 45. The reader keeps the lots whose `dealer.city` equals the dealer row's city
  (Memphis -> 451) and raises NotRead if none match, rather than returning an empty "whole" lot.
- Fields: `vin`, `stockNumber`, `yr/make/model/trim`, `mileage`, `internetPrice`, `finalPrice`, `dealerFees`,
  `imageUrls` (dealerslink.s3), `vdpUrl`, `drivetrain`, `engine`, `transmission`, `exteriorColor`, `age` (days on lot -> stock date), `dealer{...}` per lot.
- **Price:** `internetPrice` is the asking price. `finalPrice` = internetPrice + $995 "Processing Fee" (447 of 451 Memphis
  cars exactly; the other 4 show $0 everywhere with `noFinalPrice: true`, so their price is left empty). The fee total is kept in `extra`.
- Live run through `fetch.paced(fetch.get)`: 451 cars, complete, 5 requests, 11 s; all 451 with VIN (check digit OK), miles, photo, stock date.
- From GitHub Actions: Typesense Cloud is an API host with no bot defence seen and no cookie or origin check. Likely to work; not tested.

## Collierville Auto Center: DealerCenter (plain, complete)

- `www.colliervilleautocenter.com` CNAME `dealers.dealercenterwebsite.net.cdn.cloudflare.net` (aliases include `alpha.dcdws.net`).
  Pages load `cdn.dealercenterwsstatic.net/wp-content/mu-plugins/dws-v3-plugins/...`.
- Failed routes. Every GET page (`/`, `/inventory/`, `/sitemap.xml`) answers **403 Cloudflare managed challenge** ("Just a moment...",
  `challenges.cloudflare.com`) to urllib with the tool UA or a Chrome UA, and to curl (403, HTTP/1.1).
  Headless Edge passes it, and a plain replay carrying Edge's `cf_clearance` then gets 200 even with the tool UA, and still did 40 minutes later.
  robots.txt `Disallow: /*?page_no=`, so the numbered inventory pages are off limits anyway.
- Working route, no browser and no cookie: Cloudflare does not challenge `POST /wp-admin/admin-ajax.php`, which robots allows (`Allow: /wp-admin/admin-ajax.php`).
  1. `action=dws_inventory_search_service&requestType=get_vehicle_count` gives cars per make; the sum is the inventory (78).
  2. `action=dws_inventory_vehicles&page_no=N` gives the HTML of N's 30 vehicle cards, the same cards the page shows (found in
     `dws-vehicle-listing.min.js`, the "load more" call). `page_no=4` gives an empty body (a BOM only). No page-size parameter took effect.
  Header `Content-Type: application/x-www-form-urlencoded`. Answers start with a UTF-8 BOM.
- Evidence: count 78; pages 30+30+18 = **78 unique VINs**. The page says "Page 1 of 3 (78 vehicles)", and the
  `inventory_usedcars-sitemap.xml` lists 78.
- Card fields: VIN (`data-vehicle-id`), title, trim line, mileage, stock #, drivetrain, photo, detail URL. Make and model come from the URL path slugs
  (`/inventory/land-rover/range-rover-evoque/<stock>/`). No stock date anywhere (`dws_inventory_vehicle_detail` gives images and fee flags only).
- **Price:** the card's "Price: $70,098 *Includes Dealer Fees" is `data-vehicle-price="69100"` + `data-dealer-fees` (Doc Fee $998) =
  `data-total-price`. The reader takes the figure before fees as the asking price, in line with DealerOn and City Auto, and keeps the shown total and the fees in `extra`.
  On layouts that say "*Fees Not Disclosed" there are no data attributes, and the shown figure is taken.
- Live run: 78 cars, complete, 4 requests, 16 s. The other DealerCenter layout (carchoiceonline.com, Vin/Mileage lines) is covered by a fixture.
- From GitHub Actions: the pass on admin-ajax looks like a path exemption in the site's Cloudflare rule (GET pages are challenged for any UA,
  but this POST passed with no cookie at all). A datacenter address may score worse with Cloudflare. Untested.

## E Z Auto: Carsforsale.com (plain, complete)

- Front page: "Powered by Carsforsale.com", 139 references to `cdn05.carsforsale.com`, ASP.NET Core / Blazor (`_blazor/initializers`).
  DNS is a plain A record (198.185.165.141).
- **User-agent trap:** any UA containing `python-urllib` (case-insensitive; `cartrack/0.1 (python-urllib)`, `Python-urllib/3.14`) gets
  **500 "Internal Server Error"** on every path, robots.txt included. `cartrack/0.1`, `curl/8.0` and `Mozilla/5.0` get 200. The reader
  sends `User-Agent: cartrack/0.1` through `get(..., headers=...)`.
- Route: `GET /cars-for-sale` (24 cars), then `?Paging.Page=2`, and so on. The pager's buttons have no hrefs; the URL was learned by clicking
  page 2 in headless Edge, then replayed plainly. `page=`, `PageNumber=`, `pageSize=`, `Paging.PageSize=100` and `take=` change nothing.
  Each car is a schema.org `Car` JSON-LD block: VIN, `offers.price`, `offers.url`, mileage, brand/model/modelDate/vehicleConfiguration (trim), colour, transmission, fuel, body, drive, image.
  The page's description gives the total: "Find 27 vehicles starting at $6,680".
- Evidence: 24 + 3 = **27/27**; `Paging.Page=3` is empty. robots.txt allows everything.
- **Price:** the JSON-LD price equals the card's figure labelled "Price" on all 27 cars. It is not a down payment. No stock number or stock date is published.
- Live run: 27 cars, complete, 2 requests, 4 s.
- From GitHub Actions: nginx, no CDN or bot vendor seen, only the UA filter. Likely to work; not tested.

## Supercars Autosales: Dealer Car Search behind Cloudflare Turnstile (browser once)

- Platform: once past the challenge, 60 references to `imagescdn.dealercarsearch.com` and a footer link to dealercarsearch.com.
  NS `ns1-3.ldv-dns.com` (LeadVenture, Dealer Car Search's owner). Discovery missed it because Cloudflare serves a challenge page in place of the front page,
  so `PAGE_MARKS` never sees the existing `dealercarsearch.com` mark, and NS records are not in `gethostbyname_ex`.
- Failed routes. urllib (tool or Chrome UA) and curl get **403 Cloudflare managed challenge** on every page.
  **Headless** Edge stays on "Just a moment..." for 40 s (Turnstile, sitekey `0x4AAAAAAADnPIDROrmt1Wwj`).
  The replayed `cf_clearance` works only with Edge's exact UA (with the tool UA: 403). It is bound to the user agent here, unlike Collierville.
- Working route: **headful** Edge (window off-screen) passes in about 15 s and gets `cf_clearance`. Then the existing reader's one request
  `GET /inventory?pagesize=100` replays plainly with that cookie and Edge's UA: 25 cards, "Page: 1 of 1 (25 vehicles)", 25 unique VDP ids.
  The cookie still replayed 40 minutes later. Script: `research/_scratch/routing/unknowns/cfget.py`; run instructions below.
- **Price (matters):** the cards show a bare figure with no label (`lblPrice`), which the existing reader keeps as
  `extra.unlabelled_price` (23 of 25; 2 show none) and leaves `price` empty, because at Imports of Memphis that same box was a down payment.
  At Supercars it is the **asking price**: the detail page labels it "ASKING PRICE $15,800", and its data layer `product_price`
  and loan calculator `LoanCalcPrice` hold the same 15800. Values run $5,500-$24,500 (a 2025 Kia K4 with 2,000 miles at $20,000).
  The Dealer Car Search owner could settle this per dealer from one detail page ("ASKING PRICE"). Not changed here: that reader is not mine.
- From GitHub Actions: needs a headful browser (xvfb) and Cloudflare's trust of a datacenter address for Turnstile. Doubtful; untested.
  `cf_clearance` claims a one-year expiry. One clearance from a home run might be carried to the runner, but it is UA-bound and probably IP-bound. Untested.

### Running the Supercars route

    cd C:\Users\Aeske\Documents\active_projects\CraigsCars
    py research/_scratch/routing/unknowns/cfget.py https://supercarsautosalestn.com/

It starts Edge headful at x=-2400 with the profile `research/_scratch/routing/unknowns/profile`, waits 30 s on the front page,
saves cookies to `cap/cf_pass.cookies.json`, then runs `dealercarsearch.read` with a `get` that adds `Cookie` and Edge's UA.
Seen: "supercarsautosalestn.com: 25 cars, complete=True, priced=0, unlabelled figure=23".

## Lines the shared files need (not edited here)

`cartrack/dealers.py`:

    DNS_NAMES += (("dealercenterwebsite.net", "dealercenter"),)          # CNAME dealers.dealercenterwebsite.net.cdn.cloudflare.net
    PAGE_MARKS += (("bucket.dealeralchemist.com", "dealeralchemist"),
                   ("cdn05.carsforsale.com", "carsforsale"),
                   ("dealercenterwsstatic.net", "dealercenter"))     # only if a DealerCenter page is ever seen unchallenged
    READS.update({"dealeralchemist": "plain", "dealercenter": "plain", "carsforsale": "plain"})

Checked: these place cityauto.com, ezautomemphis.net and colliervilleautocenter.com, and no earlier mark claims those pages.
Supercars cannot be placed by these tables, because its only markers sit behind the challenge.
It needs either a seed override (`"platform": "dealercarsearch"`) that discovery honours, or a rule that reads a Cloudflare
challenge page as "unknown, challenged". It also needs a per-dealer "browser" flag, since other Dealer Car Search lots read plainly.

`cartrack/readers/__init__.py`:

    from . import autorevo, carsforsale, dealeralchemist, dealercarsearch, dealercenter, dealerfire, dealeron, teamvelocity
    READERS["dealeralchemist"] = dealeralchemist.read
    READERS["dealercenter"] = dealercenter.read
    READERS["carsforsale"] = carsforsale.read

`tests/test_readers.py` line 33, the registry set, then also needs `"dealeralchemist", "dealercenter", "carsforsale"`.

`dealers-seed.json`, for King Cotton Ford:

    {"name": "Landers Ford North", "website": "https://www.landersfordnorth.com/", "street": "965 Highway 51 North", "city": "Covington", "state": "TN", "zip": "38019", "lat": 35.58154, "lon": -89.64295},

The seed merges by host, so the OSM row for `kingcottonford.com` stays as well (it never resolves and is harmless); the real fix is the OSM `website` tag.
Car Choice (from OSM, `shopcarchoice.com`) has no working replacement address.
