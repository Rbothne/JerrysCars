# 08: Inventory routes for Team Velocity and DealerFire

Tested 2026-11-21 from a home connection, with plain HTTP from Python's standard library. No browser was needed for either platform. Requests were paced per host: 4 s on the Team Velocity sites, and 10-11 s on jr-autosales.com, whose robots.txt asks for `Crawl-delay: 10`.

Readers: `cartrack/readers/teamvelocity.py`, `cartrack/readers/dealerfire.py`. Tests: `tests/test_reader_teamvelocity.py` and `tests/test_reader_dealerfire.py` (23 tests), with fixtures `tests/fixtures/teamvelocity_feed.json`, `teamvelocity_srp.html` and `dealerfire_used.html`, cut from real responses by `research/_scratch/routing/teamvelocity/cut_fixtures.py`. Captures and scripts are in `research/_scratch/routing/{teamvelocity,dealerfire}/`.

## Results

| Dealer | Cars read | Site's own total | Requests | Time (paced) | Complete |
|---|---|---|---|---|---|
| gossettmotorcars.net (Gossett CDJR FIAT, account 25456) | 370 | 370 (`totalVehicles`, ItemList `numberOfItems`) | 9 | 34 s | yes |
| infinitiofmemphis.com (account 53818) | 370 | 370 | 9 | 34 s | yes |
| gossettmotors.com (group site, account 75829) | 334 | 334 ("Results: 334 Vehicles") | 8 | 29 s | yes |
| jr-autosales.com | 26 | 26 (`data-total-items`, "26 Vehicles found") | 1 | 2 s | yes |

These figures come from `research/_scratch/routing/teamvelocity/live_check.py`, which ran the readers through `cartrack.fetch.paced` against the live sites. It writes nothing to the catalogue.

## Team Velocity: the site's own JSON feed, plus one search page for photos

### Route

1. `GET {site}/inventory-used.json` returns JSON (about 45 KB a page): `totalVehicles`, `totalPages`, `pageSize` 50, `nextPage` (`/inventory-used.json?page=2`, ...), and `vehicles[]`. Each vehicle carries `vin, stockNumber, year, make, model, trim, bodyStyle, engine, transmission, driveTrain, fuelType, miles, dateInStock, msrp, sellingPrice, dealerDiscount, cashRebates, certified, inTransit, vdpUrl, exteriorColor, interiorColor`, and the store that holds the car: `dealerName, dealerCity, dealerState, dealerZip`. `imageUrls` is null on every car on all three sites.
2. Page with `?page=N` until `nextPage` is null. A page past the end answers `totalVehicles: 0`, so the reader takes the total from page 1 only. `pageSize=500` and `pagesize=500` are ignored (still 50).
3. Photos: `GET {site}/inventory/used?limit={totalVehicles}` returns the whole search page in one response (gmc 22 MB, inf 19.6 MB, gm 10.3 MB, about 2 s each). It holds one schema.org `Vehicle` JSON-LD block per car with `image.contentUrl` (content.homenetiol.com), and every car had one (370/370, 370/370, 334/334). Without `limit` the page holds 32 cars, and `pagesize=400` is ignored. The reader joins the two sources by VIN. If this request fails, the cars are still returned, without photos.

The feed is advertised in each site's `/llms.txt` ("Used Inventory JSON"). robots.txt allows `/inventory*` except addresses with commas. The same file names `/llm/inventory?condition=used` as an HTML inventory for AI agents, but that page answered 204 with an empty body to a browser user agent and 406 to ours.

### Headers and the bot defence

- The sites are on Fastly (151.101.x / 146.75.x, `via: 1.1 varnish`, `x-served-by: cache-iad-…`), with a Google load balancer in front of the origin (`via: 1.1 google`).
- The edge filters on user agent. On a cache miss, any user agent without `Mozilla/5.0` gets **406 with an empty body**. The 406 response carries no `1.1 google` hop, so it never reached the origin. Tested on the uncached `gossettmotorcars.net/inventory-used.json?page=9`:
  - `curl/8.9.1` and `cartrack/0.1 (python-urllib)` got 406.
  - `Mozilla/5.0` and `Mozilla/5.0 (compatible; cartrack/0.1)` got 200.
- A cache hit is served to any user agent. That is why the bare `/inventory-used.json` once answered 200 to `cartrack/0.1`.
- No cookie, token, header order or HTTP version was needed. The sites set `TID`, `.AspNetCore.Session` and antiforgery cookies, and the reader sends none of them back.
- The reader sends `User-Agent: Mozilla/5.0 (compatible; cartrack/0.1)` on every request. This UA still names the tracker. Nothing was spoofed.

### The three sites share one pool

All three sites serve the same group inventory, and each car is labelled with its real store:

| Store (feed `dealerName`) | Cars |
|---|---|
| INFINITI of Memphis | 114 |
| Gossett Chrysler Dodge Jeep RAM FIAT | 58 |
| Audi Memphis | 55 |
| Gossett Mitsubishi | 46 |
| Gossett Volkswagen | 38 |
| Kia of Covington Pike | 32 |
| Gossett Volkswagen of Germantown | 23 |
| Hyundai of South Memphis | 4 |

- gossettmotorcars.net and infinitiofmemphis.com list the same 370 VINs.
- gossettmotors.com lists 334 of them: everything except the Kia of Covington Pike and Hyundai of South Memphis cars.
- Overlap: 334 VINs appear on all three sites, and the union is 370.
- The feeds agree on price and store for every shared car (0 differences).
- Only `vdpUrl` changes from site to site (each site links to its own copy).

The reader sets each listing's `seller_name`, city, state and zip from the feed's store, and keeps the store in `extra.store`. `seller_id` and `source` stay the site's host. When the store is not the dealer row's own name, `lat/lon` is cleared.

Reading all three sites puts each car in the catalogue up to three times (`host:VIN`), at the same price. Reading gossettmotorcars.net alone, or infinitiofmemphis.com alone, covers all 370 cars in 9 requests (about 22 MB).

### Price labels

- **Asking price = feed `sellingPrice`.** On used cars `msrp` equals `sellingPrice` on all but 2. `dealerDiscount` and `cashRebates` were 0 throughout.
- The search page's own figure (JSON-LD `offers.price`, kept as `extra.page_price`) matched the feed on 276 of 334 cars on gm and on 312 of 370 on inf. The differences:
  - **+$899 on gossettmotorcars.net only**, for its 36 Kia of Covington Pike and Hyundai of South Memphis cars. The card reads "Your Price $5,894 … Doc Fee +$899" over an "MSRP $4,995". That figure includes the fee, so it is not taken as the asking price. On infinitiofmemphis.com the same cars show the feed price.
  - −$8 on one car (2016 Acura MDX: "Internet Price $14,880", "MSRP $14,888", "Dealer Discount"), and +$100 and +$1,400 on one car each. The feed figure is kept.
- 55 cars have `sellingPrice` 0. The page shows a price for 9 of them (for example a 2018 Buick Encore, "Internet Price $13,991"), and the reader takes that figure. The other 46 show "Call For Price" and have no price.
- Card labels differ by site template. infinitiofmemphis.com uses "Selling Price" and "MSRP". gossettmotorcars.net uses "Your Price", "Internet Price", "MSRP" and "Doc Fee". The group site's template has no `clean-design-srp-card` markup at all, so the reader does not parse card text.
- Stock date: `dateInStock` is present on 334/334 cars on gm and 353/370 on gmc and inf. The inf search page also has `ga4ASCDataLayerVehicle` with `item_inventory_date`; it is empty on gm and gmc, and the reader does not need it.

### Routes found and not used

- `/inventory/used?...&page=N`: server-rendered HTML, 32 cars a page, about 2 MB a page. JSON-LD gives VIN, identity, stock, color and photo; card text gives mileage. It needs a Mozilla user agent. It works, but it is 12 requests and has no stock date on gm or gmc.
- `/inventoryvdpsitemap.xml`: 419 VDP URLs on inf, with no images and no prices.
- The site's own JS API (`{site}/api/Inventory/vehicle?vin=…`, `getVdpPriceStackV2`) is per VIN. It was found in `prod.cdn.secureoffersites.com/dist/p1314/vue3/js/inventory.js` and not needed.

## DealerFire: one server-rendered page

### Route

- `GET {site}/inventory?isNew=0&limit=100&offset=0` returns 200, about 1.2 MB of HTML. The page's `PageObject` maps it to the dealer's alias `/used-vehicles-memphis-tn?limit=100&offset=0`, and the alias returns the identical page. The platform address is used so the reader needs no per-dealer slug.
- Each car is in `Moff.modules.get('DataLayer').pushData('VehicleObject_{vuid}', {...})`. The fields are `vuid, vin, stockNumber, year, make, model, trim, bodyStyle, drivetrain, engineDescription, transmission, fuelType, exteriorColor, mileage, finalPrice, sellingPrice, internetPrice, originalPrice, MSRP, invoiceAmount, dateInStock.date, daysInStock, mainImageUrl, photoCount, vdp, isNew, status`.
- Total: `data-total-items="26"` and `pushData('FilteredVehiclesCount', 26)`.
- Paging: the default page is 20 cars (`?limit=20&offset=20` is the site's own next link), and `limit=100` returned all 26. The reader asks for 100 at a time and starts the next page after however many cars came back. It stops when it reaches the count or when a page brings no new cars. Never needed here: one request.
- Headers: none special. The default `cartrack/0.1 (python-urllib)` user agent got 200 on every request. The server is nginx and sets PHPSESSID and `df_session_id` cookies; none are needed. No CDN or bot-defence vendor showed in the headers. Address 136.179.129.162.

### Evidence and checks

- 26 of 26 cars, 26 distinct VINs.
- `/sitemap.xml` leads to `/sitemap-vehicle.xml.gz` (a gzip file served with gzip transfer encoding, so it is compressed twice). It lists 27 VDPs, lastmod 2026-11-19. The extra one, a 2010 Kia Soul (id 65043036), answers 200 with a filtered search showing 0 matches, so it has been sold and the sitemap is stale. The search page is the truth.
- `/cars-for-sale-memphis-tn?limit=100` (all inventory) also counts 26. The dealer sells only used cars.

### Price labels and photos

- `finalPrice = sellingPrice = internetPrice = originalPrice` on all 26 cars, and `MSRP` is 0. The asking price is `finalPrice`. The other figures are kept in `extra.prices`.
- `vehicleDealerDiscount_{id}` equals minus the price on every car, so it means nothing.
- One car is a placeholder: a 2011 GMC Terrain with price $0 and 1 mile. It gets no price. The mileage of 1 is passed through as given.
- `daysInStock` disagrees with `dateInStock` (1 day for a car stocked 2026-11-10). `dateInStock` is used, and `daysInStock` is kept in `extra` only.
- Photos:
  - 7 cars have the dealer's own photo (`cdn-ds.com/stock/...`).
  - 11 cars have only `cdn-ds.com/chrome/.../cc_*.jpg`: Chrome Data's colourised maker picture. The car is tagged "Images Coming Soon". It is kept in `extra.stock_art` and not given as a photo of the car (`photo_count` 0).
  - 8 cars have no image.

## Avenues 2 and 3 (other routes, browser) were not used

Both platforms gave the complete used inventory over plain HTTP and matched each site's own count. The manufacturer search, listing sites and a headless browser were therefore not tried.

## Will it work from GitHub Actions?

This was not tested from a datacenter address. The reasoning:

- **Team Velocity:** The block seen here keys on the user agent, not on the address. Earlier research (02, section 1.4) found the Fastly-hosted Team Velocity sites answered plain requests and the Akamai-hosted ones (`wildcard.teamvelocity.com.edgesuite.net`) returned 403. These three are on Fastly. The likely risk is rate limiting of large responses, not a challenge page.
- **DealerFire:** plain nginx with no WAF headers. It is likely to work.
- `build.py` reports a refusal per dealer in its run log either way.

## What the integrator must add

`cartrack/readers/__init__.py`:

```python
from . import autorevo, dealercarsearch, dealerfire, dealeron, teamvelocity  # noqa: E402  (they use the helpers above)

READERS = {
    "dealeron": dealeron.read,
    "autorevo": autorevo.read,
    "dealercarsearch": dealercarsearch.read,
    "teamvelocity": teamvelocity.read,
    "dealerfire": dealerfire.read,
}
```

`tests/test_readers.py`, line 33:

```python
        self.assertEqual(set(readers.READERS), {"dealeron", "autorevo", "dealercarsearch", "teamvelocity", "dealerfire"})
```

`cartrack/dealers.py`: `READS` already says `"teamvelocity": "plain"` and `"dealerfire": "plain"`. That is right, and no change is needed.

`dealers.json` / `dealers-seed.json`: nothing is required. Optional: to avoid storing the Gossett pool three times, read only one of gossettmotorcars.net and infinitiofmemphis.com. Either holds all 370 cars, and gossettmotors.com is a strict subset. There is no switch for this today; it would mean dropping the other two seeds or adding a skip flag the build honours.

`build.py`: none. `fetch.paced()` defaults to 3 s. That is fine for Team Velocity, where 9 requests to a host is under 40 s. DealerFire is one request per dealer, so its 10 s crawl delay is not reached. If a DealerFire dealer ever needs more than one page, give that host a 10 s delay.

README "What the readers were seen to do" rows, if wanted:

| Team Velocity | Gossett CDJR, INFINITI of Memphis, Gossett group site | 1 per 50 cars (feed) + 1 search page for photos | Yes, against the feed's `totalVehicles`; the three sites share one 370-car pool |
| DealerFire | JR's Auto Sales | 1 per 100 cars | Yes, against the page's `data-total-items` |
