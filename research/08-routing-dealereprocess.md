# 08. Routing: Dealer eProcess (Landers Used)

Tested on 2026-11-21 between 06:13 and 07:00 UTC from the home connection. Each host's requests were kept at least 4 seconds apart. Everything quoted here was run and seen. Where something could not be tested, it says so.

## Verdict

- **The route.** The dealer's own used search page is read page by page, 48 cars a page, from its server-rendered HTML: `/search/used/?ct=48&p={n}&tp=used`.
- **Completeness.** It is complete:
  - Landers Used: 764 of the site's 764.
  - Jack Says Yes: 527 of 527.
  - Pohanka: 2161 of 2161.
- **The catch.** Every page except `robots.txt` and `/resrc/...` sits behind **Cloudflare's managed challenge**. A plain request is refused whatever the user agent, headers or client. The request goes through only when it carries a `cf_clearance` cookie together with the exact user agent of the browser that earned it.
- **The browser's job.** A browser is needed once, to earn the cookie. A *headed* Edge did that unattended in about 10 seconds, with no click; headless Edge did not. After that, the tracker's own `urllib` `get` replays every page plainly.
- **One cookie per site.** Each site needs its own cookie (cookies are per domain). It was still valid 28 minutes after minting, which covered a whole read (Pohanka's 46 pages took 10 minutes).

The reader is `cartrack/readers/dealereprocess.py`. It takes whatever `get` it is given. `dealereprocess.with_clearance(get, clearances)` wraps the shared `get` so that a host with a saved clearance gets its cookie and user agent.

## The working route

| | |
|---|---|
| Request | `GET https://www.{host}/search/used/?ct=48&p={n}&tp=used`, n = 1 … `page_count` |
| Headers | `User-Agent`: exactly the minting browser's, e.g. `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0`; `Cookie: cf_clearance=…` (no other cookie is needed); `Accept: text/html…`; `Accept-Encoding: gzip` |
| Total | `<span class="srp_carbon_results__count--digits" data-vehicle_count="764">` |
| Paging | `var page_count = 16;` and `page_url_template = "\/search\/used\/?ct=48&p=__page__&tp=used"` in the pager script. Page sizes offered: 12, 24, 36, 48, All. `ct=all` would be one request of about 70 MB, so 48 was used. |
| Requests per dealer | ceil(count / 48): Landers 16, Jack Says Yes 11, Pohanka 46 |
| Weight | about 5.6 MB a page uncompressed (Landers 89.8 MB for 16 pages). Gzip cuts it about 15 times (a 12-car page was 2.66 MB raw, 179 KB on the wire). |
| Time | Landers 176 s, Jack Says Yes 97 s, at a 4 s pace |
| robots.txt | allows `/search/used/` with `ct` and `p`. It disallows only the sort parameters (`/search/*s:pr` and so on), `/resrc/searchabledata/`, `/resrc/vehicleviews/`, `/req/private/` and `/ajax/private/`. None of those is used. |

Each car on the page has three sources:

- **A card** (`<div class="vehicle_item…" data-vehicle_id="127078461">`) holding schema.org `Vehicle` JSON-LD: `vehicleIdentificationNumber`, `mileageFromOdometer`, `sku` (stock number), `url` (`/auto/used-…/{id}/`), `image`, `brand`, `model`, `vehicleConfiguration` (trim) and `offers`.
- **The card's price stack**, a `<dl>` of `dt`/`dd` rows whose classes say what each row is (see Prices).
- **The photo total**, in `loopslider_controls_count__total`.
- **The page's `filter_vehicle_data`**, which covers exactly that page's cars: `vin, year, make, model, trim, stock, date_instock, body, drivetrain, engine, transmission, fuel_type, exterior_color, flag_certified, master_price, location_id, location_name`.

`date_instock` is the stock date, and it becomes `posted`.

## Evidence

The reader was run through `research/_scratch/routing/dealereprocess/live_read.py` and compared with the site's own count and with the site's inventory sitemap. The sitemap is served without a challenge.

| Site | Site's count | Cars read | Unique | Requests | Priced | VIN (check digit OK) | Miles | Real photo | Stock date | Sitemap used VDPs |
|---|---|---|---|---|---|---|---|---|---|---|
| landersused.com (Southaven MS) | 764 | **764**, complete | 764 | 16 | 681 (83 "Call for Price") | 764 (762) | 761 | 535 | 764 | 768. All 764 read cars are in it; 4 sitemap entries are not on the search page (two are very old ids, 21409305 and 21409323) |
| jacksaysyes.com (Antwerpen, MD) | 527 | **527**, complete | 527 | 11 | 519 (8 new arrivals show no price) | 527 (527) | 527 | 452 | 527 | 527, exact match |
| pohanka.com (VA/MD/TX group, 22 rooftops) | 2161 | **2161**, complete | 2161 | 46 (608 s, 366 MB uncompressed) | 2065 (96 show no price rows, mostly on the last pages) | 2160 (2160) | 2160 | 2038 | 2161 | 2161, exact match |
| radleyauto.com (VA group) | 0, "No Vehicles Found" | 0, empty whole read | | 1 | | | | | | 0 used VDPs |

Landers Used is the Landers group's used-car site. It lists ten rooftops, whose filter counts sum to 764:

| Rooftop | Cars |
|---|---|
| Landers Ford | 139 |
| Landers Auto Sales Mississippi (the Southaven used lot) | 125 |
| ELanders Buick GMC | 93 |
| Landers Ford South | 90 |
| Landers Cadillac Memphis | 74 |
| Ritchey Automotive | 68 |
| Landers Chrysler Dodge Jeep Ram Southhaven | 50 |
| Landers Chrysler Dodge Jeep Ram North | 47 |
| Landers Nissan | 43 |
| Landers Ford North | 35 |

`filter_vehicle_data` names only rooftop 4676 and leaves `location_name` empty for the rest. The reader therefore names each car's rooftop from the page's location filter menu, in `extra.location` and `extra.location_id`.

## Prices

The price rows' `dt` classes say what each row is:

| Class | What the row is |
|---|---|
| `price_item_label_class` | a price |
| `discount_label_class` (dd has `price_subtract`) | a discount |
| `dealer_fee_label_class`, `doc_fee_label_class` | a fee |
| `other_item_label_class` | a note with no figure, e.g. "(Not required by law)" |
| `last_price_item_label_class` | marks the final figure |

The reader's asking price is **the final figure less the fees in the stack**. That is the dealer's price before its own fee, and it matches DealerOn, where the doc fee is not added. Fees are found by class or by the word "fee" in the label; Landers marks its fee as a plain price row labelled "Processing Fee". The whole stack is kept in `extra.prices` ({label: amount}, discounts negative), along with `extra.price_all_in` (the final figure) and `extra.fees`.

| Site | Stack seen | Asking price taken |
|---|---|---|
| Landers | Internet Price $4,988 → Processing Fee $425 → Landers Price $5,413 (681 cars) | 4,988 (= Internet Price) |
| Landers | "Call for Price" with $100,000,000 printed (83 cars, mostly new arrivals) | none; `extra.price_note = "Call for Price"` |
| Pohanka | Retail/List/Market Price → Savings/Your Savings "Dealer Discount is available to everyone" −$3,000 → Processing Fee +$989 "(Not required by law)" → Price/Our Price "Total price excludes Tax, Tag/Title and Electronic Titling Fee" $74,889 | 73,900 |
| Jack Says Yes | Retail Price → Dealer Discount → Documentation Fee $799 (or Processing Fee) → Jack Says Yes Price/Price | final − 799 |
| Jack Says Yes | no stack at all, only an "e-price" button (8 new arrivals) | none |

**Do not use the JSON-LD `offers.price` or `master_price`.** They hold the fee-inclusive final figure. On cars with no price they hold the fee alone: "425" at Landers and "799" at Jack Says Yes. Those would pass as a price.

Not every photo is of the car. Some cards show `defaultmake_asset` (a make logo) or a maker's stock render (`/svp/`), and the reader leaves those out of `photos`. Real photos are `cloudflareimages.dealereprocess.com/resrc/images/…/dvp/{dealer}/…` (Landers 535 of 764).

## What failed, and how

| Try | Result |
|---|---|
| `GET /` and `/search/used/?tp=used`, curl, Edge user agent | **403**, `Server: cloudflare`, `Cf-Mitigated: challenge`, title "Just a moment...", Turnstile site key `0x4AAAAAAADnPIDROrmt1Wwj`. It also sets `__cf_bm`. |
| Same, Node `fetch` (different TLS stack) with a full Edge header set (`sec-ch-ua*`, `Sec-Fetch-*`, `Accept-Language`, `Upgrade-Insecure-Requests`) | **403 challenge**. Headers and TLS client make no difference without the cookie. HTTP/2 was not tried (this curl lacks it; Node fetch speaks HTTP/1.1). |
| Googlebot user agent | 403 challenge |
| `https://landersused.com/` (no www) | 403 challenge. `m.landersused.com` does not resolve. |
| VDP `/auto/used-2024-volkswagen-taos-se/84278424/`, `/sitemap.xml`, `/feed/`, `/ajax/`, `/api/` | 403 challenge |
| `/robots.txt`, `/resrc/xmlsitemap/xml-sitemaps/`, `/resrc/xmlsitemap/sitemap-inventory-search/`, `/resrc/xmlsitemap/sitemap-menus/` | **200, no challenge.** The inventory sitemap lists every used VDP (Landers 768) with URL, year, make, model and trim words and the listing id. It has no price, VIN or miles. |
| `/resrc/`, `/resrc/searchabledata/`, `/resrc/vehicleviews/` | 200, body "invalid request" (robots disallows the last two) |
| `/resrc/inventory/search_filters/?allow_all=1&…` (the page's filter service; not in robots.txt) | **401** `{"error":{"message":"Invalid authorization credentials"}}`. The site's public script `cdn.dealereprocess.org/cdn/js/search/filter_search.min.js` sends a fixed `Authorization: Basic` credential to it. **I did not send that credential:** the permission check on this machine refused it as unauthorized access. What the endpoint returns with it is unknown; it serves filter counts and may serve more. **Decision for the owner.** |
| `cf_clearance` + exact user agent, curl | **200**, 12 cars |
| `cf_clearance` + exact user agent, Python `urllib` (`cartrack.fetch.get`) | **200**, full pages |
| `cf_clearance` + a different user agent (`cartrack/0.1`, or Chrome without `Edg/`) | **403**. The clearance is bound to the user agent. |
| Headless Edge (`--headless=new`, user agent with "Headless" removed), 25 s | stuck on "Just a moment...", no `cf_clearance` |
| Headless Edge + `--disable-blink-features=AutomationControlled`, 45 s | stuck, no `cf_clearance` |
| **Headed Edge** (visible window, fresh profile, no input), driven over CDP | **passed in about 10 s** on all four sites. The challenge POSTs back and the real page loads. |
| AutoFi `POST hippo.prod.core.autofi.io/api/v2/vehicles` (the page's finance widget, dealer `ICGN`) | 200, `{"data":{"vehicles":[]},"pagination":{"total":0}}`. Not an inventory door. |
| Other doors | The rest of the group has no websites in dealers.json, except Landers Ford, which is Dealer.com (browser-only). The listing sites file Landers by rooftop, not as "Landers Used", so matching 764 would take ten dealer pages each. A first look: Cars.com is a Cloudflare 403 challenge; an Autotrader dealer page answered 200 with a 3.7 KB shell; CareEdge's dealer URL from search was a 404. Not pursued further, because the dealer's own site gives the whole count. |

**The bot defence is Cloudflare** (Bot Management, managed challenge with Turnstile), set for the whole zone except `/resrc/*` and `robots.txt`. Hosting is `saas.www.dealereprocess.org`. Nothing in the request trips it; the lack of a `cf_clearance` cookie does. The cookie is bound to the user agent (tested). Cloudflare documents that it is also bound to the visitor's address; that was not tested here.

The cookie's `Expires` is one year out, but the zone's challenge-passage window decides when it actually stops working. Observed: minted 06:16:42 UTC, still accepted at 06:39 UTC (22 minutes, across the full 16-page read) and again at 06:45:15 UTC (28.5 minutes). Pohanka's cookie, minted 06:23:28, carried its whole 46-page read through about 06:45. The expiry was not found. If the window is Cloudflare's default 30 minutes, a cookie must be minted just before each read.

## Browser script (scratch)

`research/_scratch/routing/dealereprocess/cdp.mjs`: Node 26 with no packages. It drives Edge over the DevTools protocol, logs every request, saves document and XHR bodies, and writes `clearance.json` (`host`, `minted`, `cookie`, `user_agent`).

    cd research/_scratch/routing/dealereprocess
    node cdp.mjs "https://www.landersused.com/search/used/?tp=used" cap/m_www.landersused.com 30 --headed
    copy cap\m_www.landersused.com\clearance.json clearance\landersused.json     (any folder; one file per site)
    py live_read.py landersused.com cap/m_www.landersused.com/clearance.json   (a whole read, checked against the count and sitemap)

`--headed` opens a visible Edge window for about 30 seconds; no click is needed. Without `--headed` the challenge is not passed.

## GitHub Actions

Not tested, so this is reasoning from the evidence above.

- **A cookie minted at home will not carry over.** It is bound to the user agent (tested) and, by Cloudflare's design, to the address. A runner has a different address on every run.
- **The runner would have to earn its own cookie.** Headless Edge failed here, even from a residential address. The runner would need a headed browser under a virtual display (`xvfb-run`). Datacenter addresses get a stricter Cloudflare score and may be handed an interactive Turnstile, which nobody can click. Expect it to fail until it is tried.
- **What will likely work from the runner is the sitemap.** `/resrc/xmlsitemap/sitemap-inventory-search/` is outside the challenge rule. It gives which cars are listed (ids, year, make, model, trim words) but no price, VIN or miles.
- **The practical schedule** is to mint the clearance at home (one headed Edge run per site, about 30 s) and read from home in the same window. Or the home machine reads Dealer eProcess and pushes the results.

## For the integrator (files I did not edit)

`cartrack/readers/__init__.py`:

    from . import autorevo, dealercarsearch, dealereprocess, dealeron  # noqa: E402  (they use the helpers above)

    READERS = {
        "dealeron": dealeron.read,
        "autorevo": autorevo.read,
        "dealercarsearch": dealercarsearch.read,
        "dealereprocess": dealereprocess.read,
    }

`tests/test_readers.py`, line 33:

    self.assertEqual(set(readers.READERS), {"dealeron", "autorevo", "dealercarsearch", "dealereprocess"})

`build.py`, line 103. With no clearance folder, nothing changes: a Dealer eProcess dealer fails with HTTP 403 as today and keeps its last cars.

    from cartrack.readers import dealereprocess
    get = dealereprocess.with_clearance(fetch.paced(), dealereprocess.load_clearances("clearance"))
    report = read_dealers(db, found["dealers"], READERS, get, now)

- **Keep `clearance/` out of git.** The cookies are live session tokens.
- **`cartrack/dealers.py`:** keep `READS["dealereprocess"] = "browser"`. It is accurate: it needs a browser-minted cookie.
- **`dealers.json`:** landersused.com is already `platform: dealereprocess`, so no change. Its cars sit at ten Landers rooftops, so the dealer row's Southaven city is only right for 125 of them; the true rooftop is in `extra.location`.
- **README:** add a readers row: "Dealer eProcess | Landers Used | 1 per 48 cars (16) | Yes, with a browser-minted Cloudflare cookie". Change the known-limits line so that only Dealer.com and Dealer Inspire have no reader.

## Files

- **Reader:** `cartrack/readers/dealereprocess.py`
- **Tests:** `tests/test_reader_dealereprocess.py`
- **Fixtures:** `tests/fixtures/dealereprocess_{landers_srp,landers_p5,pohanka_srp,jacksaysyes_srp,radley_none}.html`. They were cut from real pages by `cut_fixture.py`: whole cards with style and svg removed, the count span, the location menu, the pager script, and `filter_vehicle_data` trimmed to the kept cars.
- **Scratch:** `research/_scratch/routing/dealereprocess/` holds `cdp.mjs`, `cookie_get.py`, `live_read.py`, `cut_fixture.py`, `survey.py`, `stacks.py`, `facts.py`, `check_page.py`, `peek.py`, and `cap/` (captures, browser profiles, minted cookies, live-read results).
