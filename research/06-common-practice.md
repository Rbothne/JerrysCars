# 06 - Common practice: the trade and the engineering

Research date: 20 November 2026. Region examples: DC / Maryland / Virginia.
Evidence tags: **TESTED** = I ran or inspected it myself (code read, PDF extracted, API queried). **DOCUMENTED** = primary source read, URL given. **REPORTED** = second-hand: forum, vendor marketing, press, or general practitioner consensus I could not tie to one primary source.

One limit applies to the whole document: live requests to the listing sites themselves (Craigslist, Facebook Marketplace) were not permitted from this session. Every statement below about whether an access route "still works" therefore comes from repository code, commit history and issue history, not from my own requests. Reddit's JSON endpoints also returned 403, so forum practice comes from search extracts and vendor pages, not from reading threads.

Saved material: `research/_scratch/common-practice/` (`pdf/` state statutes and fee sheets with extracted text, `gh/` GitHub API search and issue dumps, `repos/` shallow clones of the eight tracker repositories read).

---

## ONE-PAGE SUMMARY

### The trade

- **Sourcing is a speed game on Facebook Marketplace first.** Private-party cars at cheap price points are mostly on FB Marketplace now. Craigslist and OfferUp come second, then impound and public auctions, then dealer-only auctions once a flipper is licensed. Meta stopped dealer catalog feeds to Marketplace (Sept 2021) and dealer Business-page posting (Jan 2023), so FB vehicle listings are mostly private-party (REPORTED, AutoSweet, CBT News). The paid alert tools charge for speed: Swoopa's tiers are literally named by alert speed, at $47, $144 and $352 a month (DOCUMENTED). Under-$15k used cars had only a 34-day supply nationally in October 2026, against 49 days overall (DOCUMENTED, Cox). Cheap cars sell fastest.
- **Evaluation is a fixed routine.** Pull the VIN, then a history report (Carfax about $44.99 for one; AutoCheck $29.99 for one or 25 for $49.99, which is the volume buyer's choice), plus NMVTIS and recalls. Then an OBD scan that checks the readiness monitors, since several "not ready" means codes were recently cleared. Then a paint-meter or panel-gap walk-round, a cold start and a test drive (REPORTED). For max buy price the common rules are: expected resale − all-in costs − target profit; a "70% of resale minus repairs" rule; and dealers' 85–90% cost-to-market at auction (REPORTED).
- **Operations: cheap reconditioning, fast turn, records per car.** Detailing, photos, small fixes and fresh fluids pay. Big mechanical work usually does not. Relisting goes back onto FB Marketplace, Craigslist and OfferUp. Target hold time is under about 30 days (REPORTED).
- **Volume runs into hard legal ceilings fast.** **Maryland:** a person who offers **3 or more** vehicles in any 12 months is *presumed* a dealer (Transp. §15-101(c)(2)(ii), TESTED from the statute PDF). The MVA cites a penalty of up to $5,000 / 1 year. **Virginia:** **5 or more** in any 12 consecutive months is a rebuttable dealer presumption (§46.2-1500, DOCUMENTED). **DC:** I found no count presumption, but selling **5+ vehicles a year** triggers buyer/VIN record-keeping (DC Code §50-1501.31, DOCUMENTED). On top of that, every unlicensed flip is titled and taxed: 6.5% in MD since 1 July 2025, and 4.15% (minimum $75) in VA.
- **That is why serious flippers get licensed.** **MD:** used-dealer licence $300, wholesale $350, $15,000 bond for 1–250 cars a year, dealer plate $50, orientation and site inspection. **VA:** $270 certificate, $350 a year to the Recovery Fund for 3 years, a $50,000 bond, a 250 sq ft non-residential office with space to display 10 cars, open 20 h/week, and a dealer-operator test. **DC:** $99 per 2 years from DLCP, a $25,000 bond, a certificate of occupancy, and separate DC DMV dealer registration. A licence unlocks AuctionACCESS, which leads to Manheim, ADESA/OPENLANE and ACV, plus dealer plates, MMR wholesale values and no titling tax per flip.

### The engineering

- **There is no dominant open-source car tracker.** The most used maintained tool is **BoPeng/ai-marketplace-monitor** (425★, AGPL, commits to Nov 2026). It drives a *headed* Playwright Chromium logged into the user's own FB account, saves `storage_state` to skip re-login and CAPTCHAs, and polls on a jittered interval (`every(n).to(1.5n)`; 30 min in the README example). It caches each listing by URL and re-reads it only when price or title changes, then pushes alerts to ntfy, Pushover, Telegram or email (TESTED, code read).
- **Facebook access splits three ways, and all three break every few weeks.** (1) A logged-in browser (AIMM, hyacinth). (2) Cookies lifted from the user's own Chrome plus FB's internal GraphQL with `fb_dtsg`/`lsd` and `doc_id`s, rate-limited to 3 requests a minute (jdcodes1/facebook-marketplace-mcp). Two "silent empty results / refresh doc_id" fixes landed there in Aug–Sep 2026. (3) Logged-out GraphQL with a fallback to the logged-out HTML search page, plus an optional residential proxy (jlsookiki/secondhand-mcp). That tool's search was broken for everyone from 1 to 7 Sep 2026 (TESTED, issues and commits).
- **Other sources are calmer.** eBay offers only the official Browse API now (Finding and Shopping were decommissioned 5 Feb 2025), at 5,000 calls/day by default (DOCUMENTED). OfferUp answers anonymous GraphQL, tested by the AIMM maintainer on 16 Oct 2026 (REPORTED in issue #467). The Python wrappers for Craigslist HTML are stale; the maintained Craigslist monitor (hyacinth) uses Playwright and polls every 600 s (TESTED).
- **Commercial car data comes from dealer feeds, not scraping.** CarGurus says its inventory comes from dealers' inventory and website-host feeds. Small operators can still buy aggregated dealer inventory cheaply: MarketCheck has a free tier of 500 calls a month and charges $0.002 per inventory search; auto.dev's free tier gives 1,000 calls a month (DOCUMENTED). Raw syndication feeds are dealer-controlled and closed.
- **Bot-defence practice and its costs:** residential proxies at $1–8/GB, Apify's FB Marketplace actor at $2.60–6.20 per 1,000 listings (3.9★), headed browsers with saved sessions, or **capture through an extension in the user's own session**. A Canadian Tundra tracker does exactly that: a Chrome extension posts to a local Python app, which de-duplicates at 95% year/price/mileage similarity and estimates fair market value by regression. That is the same shape as the house extension skeleton.
- **What the house style misses:** GitHub Actions cron is at best every 5 minutes, "may be delayed" and can drop jobs, runs from datacenter IPs, and pauses after 60 idle days in public repos (DOCUMENTED). A static Pages site cannot push alerts. Also missing are VIN and title checks, sold/removed status tracking and seller-type (curbstoner) detection. **What common practice misses:** price history, cross-site de-duplication and transparent scoring. Almost no tool keeps history, and that is where his design is ahead.

---

## A. THE TRADE

### A1. Sourcing

| Channel | Why flippers use it | Evidence |
|---|---|---|
| Facebook Marketplace (vehicles) | The largest pool of private-party cheap cars, with messaging built in. Since dealers lost catalog feeds and Business-page posting, it is mostly private sellers, plus dealers posting as individuals (a curbstoning signal worth detecting). | REPORTED: AutoSweet (feed distribution ended 13 Sep 2021), https://www.autosweet.com/facebook-marketplace-questions-answered/ ; CBT News (Business-page posting ended Jan 2023), https://www.cbtnews.com/how-car-dealers-can-leverage-facebooks-new-marketplace-tools-bob-lanham-head-of-automotive-retail/ |
| Craigslist (cars+trucks by owner, `cto`) | Older sellers, less competition, and an easy owner-only filter. | REPORTED (forum consensus) |
| OfferUp, Nextdoor | Secondary private-party pools that every paid alert tool covers. | DOCUMENTED that tools cover them: https://getswoopa.com/pricing |
| Impound / unclaimed-vehicle and public auctions | Sellers need the lot space cleared, so prices start below retail. Title paperwork (lien-sale packets) is the catch. | REPORTED: Autura, Mar 2026, https://www.autura.com/insights/how-to-flip-or-resell-vehicles-for-profit-part-1 |
| Copart / IAA (salvage) | Rebuild-and-resell, via brokers if unlicensed. | REPORTED |
| Manheim, ADESA/OPENLANE, ACV (dealer-only) | Volume and arbitration, for licensed dealers only (see A4). | DOCUMENTED: https://site.manheim.com/tutorials/new-dealer-registration-faqs |
| Dealer wholesale and trade-in buys, "we buy cars" ads | Repeatable supply at volume. | REPORTED |

**How fast good listings go.** No neutral study measures time-to-sale for FB listings. The market signals are indirect:
- Swoopa prices its tiers by alert speed ("Basic", "Fast", "Instant"). BigFlippa advertises about 5-minute latency; CarFlipperAI advertises "as fast as 2 minutes" (DOCUMENTED vendor pages: https://getswoopa.com/pricing , https://bigflippa.com/best/car-flipping-apps/ , https://www.carflipper.ai/en).
- Cox Automotive, October 2026: under-$15k used vehicles had a 34-day supply, against a 49.2-day industry average (DOCUMENTED, https://www.coxautoinc.com/insights/used-vehicle-inventory-october-2026/). Retail stock that is cheap turns fastest, and private-party bargains go faster still.
- Practitioners commonly say an underpriced, clean commuter car on FB gets dozens of messages and is "pending" within hours (REPORTED, forum consensus; not quantified).

**Alerts and saved searches flippers set (REPORTED, with the tool features DOCUMENTED).**
- They use FB's own saved-search notifications and Craigslist saved-search email alerts, which are free and slow.
- Paid tools add: one search per model/price band, a price ceiling, a radius, a minimum year and maximum miles, a price-drop alert (Swoopa's top tier only), scam filtering, and a profit estimate per alert (BigFlippa).
- Common search patterns: specific reliable models under a price cap, "needs work" / "mechanic special" / "moving" / "must sell" keywords, and very-new listings sorted by date.

**First contact (REPORTED, practitioner consensus).**
- Message within minutes.
- Do not send the default "Is this still available?" Ask a specific question and propose a viewing time ("Can I see it today at 5? I have cash").
- Ask for a phone number and call.
- Ask for the VIN before driving out.
- Arrive with cash, a scan tool and a title checklist.

The tools now automate parts of this: Swoopa lists an "AI negotiator" and an "AI offer pipeline" (DOCUMENTED marketing claims).

### A2. Evaluation

**Before driving out (REPORTED routine; costs DOCUMENTED where cited):**
1. **VIN.** Decode it (NHTSA vPIC, free) and check open recalls (NHTSA, free).
2. **Title-brand check.** Use NMVTIS (an approved-provider report costs a few dollars). Autura lists NMVTIS plus the NHTSA recall lookup as standard (REPORTED).
3. **History report.** Carfax is about $44.99 for one, $64.99 for three and $99.99 for six (checkout prices as of 30 Sep 2026, REPORTED via CarWhere, https://www.carwhere.com/guides/carfax-report-cost ; Edmunds lists $44.99 for one, https://www.edmunds.com/car-buying/which-vehicle-history-report-is-right-for-you.html). AutoCheck is $29.99 for one or **25 for $49.99 within 21 days**, so volume buyers use AutoCheck and pull Carfax only for the finalists (REPORTED, https://www.carwhere.com/guides/carfax-vs-autocheck).
4. **Value check.** KBB or Edmunds private-party value, local comps, and auction results for anyone with MMR access.

**At the car (REPORTED):**
- **OBD-II scan.** Read stored, pending and *permanent* codes, and the readiness monitors. Several monitors "not ready" on a car that has been driven means codes were recently cleared or the battery was disconnected. Guides treat three or more as a strong warning (https://mythinkcar.com/blogs/news/used-car-obd2-scan-checklist-what-to-read-before-you-buy - a scan-tool vendor). A full-system scan covering ABS and SRS modules catches more than an engine-only scan. Common tools are a $20–40 Bluetooth ELM327 dongle with an app, or BlueDriver / OBDLink-class tools around $100–150.
- **Paint thickness gauge** (roughly $30–150 consumer units). Look for readings well above factory, around 4–7 mils, on one panel against its neighbours, which means refinishing or filler. Add panel gaps, overspray on rubber, and non-matching glass or date codes.
- **Mechanical.** Cold start (ask the seller not to pre-warm the car), leaks, fluid condition, transmission behaviour (especially CVTs), and suspension noises.
- **Frame and rust.** Check rockers, subframes and brake lines, plus flood signs (silt, corrosion under the seats, musty smell).
- **Title in hand.** The seller's name must match the ID, with no lien, or a lien release present. Avoid "open titles" and title-jumping. In MD, VA and DC the buyer must title the car in their own name; skipping that is the classic curbstoner offence.
- **Professional inspection** (around $100–250) for higher-value buys. Flippers often skip it on sub-$5k cars and rely on their own scan and walk-round.

**Max-buy rules of thumb (REPORTED):**
- `max bid = expected resale − all-in costs − target profit`. All-in costs are the purchase price, fees, transport, repairs, title, tax, registration and reconditioning (Autura, Mar 2026).
- The "70% rule": no more than 70% of expected resale minus repairs. Example: $10k resale with $1k repairs gives a $6k maximum (blog sources via search, https://biggerpockets.com/member-blogs/14535/96933-how-to-calculate-flip-maximum-purchase-price).
- Dealers buying at auction target an all-in **85–90% cost-to-market** (DigitalDealer, https://digitaldealer.com/news/three-pointers-maximize-purchased-unit-profitability/91523/).
- Margin targets quoted by small flippers: about $750–1,500 per car on sub-$10k cars. Autura says first-timers do best under $7,500.
- Discipline: overpaying once and then sitting 90 days is the commonly told cautionary tale.

**Makes and conditions sought or avoided (REPORTED, practitioner consensus):**
- *Sought:* Toyota and Honda commuter cars (Corolla, Camry, Civic, Accord), Lexus, small trucks and body-on-frame SUVs (Tacoma, 4Runner, F-150, Silverado), and Mazda. Also clean titles, one or two owners, service records, and cosmetic-only faults (dents, dirty interior, dead battery, bad tyres).
- *Avoided:* salvage or rebuilt titles (unless that is the niche), out-of-state or lien complications, high-mile German luxury cars, CVT-era Nissans and other models with known transmission failures, and flood or frame damage. Also anything with an airbag light or emissions tampering, and cars that cannot pass the local inspection (Maryland requires a safety inspection to title a used car; VA requires an annual safety inspection; emissions testing applies in the DC-area counties).

### A3. Operations

- **Reconditioning that pays (REPORTED):**
  - A full detail and paint correction are the largest return per dollar.
  - Headlight restoration; replacing bulbs, wiper blades and floor mats; and an oil service with records.
  - Replacing a battery, fixing cheap sensor codes (O2, EVAP purge valve) and clearing them *after* the fix, so the readiness monitors set before listing.
  - Matching tyres when needed.
  - Paying dent-repair (PDR) work on prominent dings.
  - Generally avoided: paintwork, transmission jobs and anything over about 10–15% of the expected resale price.
- **Relisting (REPORTED):**
  - Listed back onto FB Marketplace (biggest audience), Craigslist and OfferUp. Higher-value cars sometimes also go on Autotrader or Cars.com private listings or eBay Motors.
  - About 20–40 daylight photos, a cold-start video, the VIN in the ad, and a maintenance list.
  - Unlicensed flippers in MD and VA must sell titled in their own name, under the count limits in A4.
- **Pricing and negotiation (REPORTED):**
  - Price at or slightly below the local comp median so the ad sits on the first screen of price-sorted searches, plus a cushion of about $300–500 for haggling.
  - Drop the price on a schedule (often weekly) if leads stall. Drops resurface the listing on FB, which is also why price-drop alerts matter on the buying side.
  - When buying: offer cash, point to the defects found (codes, tyres, paint), and pay a round number.
- **Hold time.** The target is about 30 days or less; Autura frames the choice as a "30-day turn vs showroom restore" (REPORTED). For context, the national retail days' supply was 49 in October 2026 (DOCUMENTED, Cox).
- **Record keeping (REPORTED; the DC rule DOCUMENTED):**
  - One spreadsheet row per car: VIN, source, date bought, purchase price, every receipt, tax and title cost, list date and price changes, sale date and price, buyer, days held, and net profit.
  - Bills of sale both ways, and title copies.
  - Profits are taxable as ordinary or self-employment income.
  - DC requires anyone who sells 5+ vehicles a year to record the buyer's name, address and licence number, the VIN and the original owner within 24 hours (DC Code §50-1501.31, https://code.dccouncil.gov/us/dc/council/code/sections/50-1501.31).

### A4. Scale and structure

#### Private-sale ceilings

| Jurisdiction | Rule | Source |
|---|---|---|
| **Maryland** | "Dealer" includes anyone who during any 12-month period offers to sell **three or more** vehicles acquired for resale. A person offering 3+ is **presumed** to have acquired them for resale; the owner must rebut that by a preponderance of the evidence. People selling vehicles "acquired and used for personal or business use" are excluded. | TESTED: extracted from Transp. §15-101 (2026 statute PDF), https://mgaleg.maryland.gov/2026RS/Statute_Web/gtr/15-101.pdf , saved at `_scratch/common-practice/pdf/md-gtr-15-101.txt` |
| Maryland penalty | MVA: "Unlicensed dealers may face up to a $5,000 fine or up to 1 year in jail." | DOCUMENTED: https://stg-mva.maryland.gov/vehicles/Pages/registration/curbstoner.aspx (I did not cross-check this against the penalty section of the statute.) |
| **Virginia** | A person who offers to sell, sells, displays or permits the display of **five or more** motor vehicles within **any 12 consecutive months** is presumed a motor vehicle dealer, rebuttable by a preponderance of the evidence. People disposing of vehicles acquired and actually used for their own use, in good faith, are excluded. | DOCUMENTED: Va. Code §46.2-1500, https://law.lis.virginia.gov/vacode/title46.2/chapter15/section46.2-1500/ |
| **DC** | No sales-count presumption found. "Dealer" is defined by being "engaged in the business" (§50-1501.01). Selling **5+ vehicles in one year** triggers record-keeping (§50-1501.31). | DOCUMENTED: https://code.dccouncil.gov/us/dc/council/code/sections/50-1501.31 . DC municipal regulations (16 DCMR ch. 3, 18 DCMR ch. 5) could not be retrieved, because the mirrors returned 410/503. |

**Titling tax on every unlicensed flip** (because the flipper must title in their own name):
- MD excise is **6.5%** of the purchase price from 1 July 2025 (DOCUMENTED, MVA bulletin via https://mva.maryland.gov/title-registration/fees-payment-options/excise-tax).
- VA sales and use tax is **4.15%**, minimum $75 (DOCUMENTED, https://www.dmv.virginia.gov/vehicles/taxes-fees/sut).
- On a $6,000 car that is about $390 in MD, which comes straight off a $1,000 margin. Dealers buying inventory for resale avoid this; that is a core economic reason to license (REPORTED as the general practice; I did not read the exemption statutes).

#### Licence requirements and costs

**Maryland (MVA Business Licensing & Compliance)**
- Used Car dealer licence **$300**; Wholesale licence **$350**; New Car licence $300. MVA's note: "All fees listed are annual fees - renewed bi-annually." Dealer plate (Class 1A) **$50** (TESTED: scraped from https://mva.maryland.gov/title-registration/fees-payment-options).
- Surety bond by the prior year's used sales, from Transp. §15-308 (TESTED from the statute PDF, https://mgaleg.maryland.gov/2026RS/Statute_Web/gtr/15-308.pdf):

  | Used vehicles sold (incl. wholesalers) | Bond |
  |---|---|
  | 1–250 | **$15,000** |
  | 251–500 | $25,000 |
  | 501–1,000 | $35,000 |
  | 1,001–2,500 | $50,000 |
  | over 2,500 | $150,000 |

  A new applicant's bond is based on estimated first-year volume, with a minimum of $15,000 for used and $50,000 for new. Bond premiums for applicants with good credit are commonly 1–3% of the bond per year (REPORTED, surety vendors).
- Other requirements: a monthly online business-licensing orientation (form CS-303 with the application), a site inspection of the place of business ("a lot, an office, or another approved business location"), and one free salesperson licence per dealer licence (DOCUMENTED: https://mva.maryland.gov/your-mva-guide/businesses/vehicle-dealers-title-services/business-licenses-vehicle-dealers/vehicle-dealer).
- Maryland's **wholesale licence** (sell only to dealers) is the low-overhead route flippers mention for buying at dealer auctions and wholesaling out. Retailing to the public needs the retail used licence (REPORTED).

**Virginia (Motor Vehicle Dealer Board)** (DOCUMENTED: https://mvdb.virginia.gov/how-to-be-a-dealer/ ; 2019 fee sheet saved at `pdf/va-mvdb-fees-2019.txt`)
- Fees: dealer certificate **$270** (it was $225 on the 2019 sheet), and the Motor Vehicle Transaction Recovery Fund at **$350 a year for the first 3 years**, then $100 a year (Va. Code §46.2-1527.1).
- Bond: **$50,000** for the first three years.
- Plates: first two dealer plates **$60**, each additional **$26**. Salesperson licence $50 each.
- Requirements:
  - A qualified **dealer-operator**, certified by test via form MVDB-57.
  - Zoning certification (MVDB-19).
  - An **established place of business** that cannot be a residence: room to display **10 vehicles**, a ≥**250 sq ft** enclosed office used only by the dealership, a permanent sign with ≥6-inch letters, a phone, internet and email.
  - Open **≥20 h/week**, with 10 of those hours between 9:00 and 17:00 on weekdays.
  - An approved buyer's order template.
- The fixed-location rule is the main barrier for a one-person operation in VA. In practice, small VA flippers rent space in a shared "dealer office suite" or on a used-car lot (REPORTED).

**District of Columbia** (DOCUMENTED)
- DLCP Motor Vehicle Dealer business licence: **$99 per 2 years or $198 per 4 years**, a **$25,000 motor vehicle dealer bond**, a certificate of occupancy, a sample car order and bill of sale, a police criminal-history report, and a Clean Hands certificate (https://dlcp.dc.gov/node/1618866). DLCP's "Used Car Seller" licence has the same fees (https://dlcp.dc.gov/node/1806406).
- Then a separate **DC DMV dealer registration**: original Clean Hands certificate, original business licence, certificate of occupancy, federal tax ID, salesperson licences, and insurance showing the number of dealer tags (https://dmv.dc.gov/service/how-become-dc-dmv-registered-dealer). The DMV page lists no fees.
- A certificate of occupancy means commercial premises, so DC is impractical from a home.

#### What a licence unlocks
- **Dealer-only auctions.** Register with **AuctionACCESS** (dealer licence, driver's licence, W-9), then with each auction. Manheim and AuctionACCESS registration are "two separate processes" (DOCUMENTED, https://site.manheim.com/tutorials/new-dealer-registration-faqs). ADESA/OPENLANE authorise online buying in about 5 business days (REPORTED via search extract of adesa.com). ACV uses AuctionACCESS for credential checks (https://www.acvauctions.com/blog/auctionaccess-for-acv). US buy fees are per site and per price band, and are shown only to logged-in dealers. I found no public 2026 US schedule. Manheim's commercial terms add a 2% internet purchase fee for that segment (DOCUMENTED), and a common rule of thumb is about $400 all-in fees per auction car (REPORTED).
- **Dealer plates.** Move and test-drive inventory without registering each car.
- **Wholesale data.** **Manheim Market Report (MMR)**, Manheim's actual auction sale prices by VIN, mileage and condition, comes with a Manheim account. Paid add-ons are vAuto, Black Book and J.D. Power for dealers (REPORTED). For context, the Manheim index was 207.4 in mid-October 2026, 2.2% above a year earlier (REPORTED via press, https://www.autobodynews.com/news/manheim-index-rises-0-7-in-early-october-as-wholesale-supply-tightens).
- **No per-flip titling tax** on resale inventory, and no count ceiling.

### A5. Tools flippers already pay for

| Tool | Price (as published) | Sources covered | Notable features | Complaints / weaknesses |
|---|---|---|---|---|
| **Swoopa** | Go $47/mo ($28 committed for 12 months), Turbo $144/mo ($99 for 6 months), Nitro $352/mo ($199 for 6 months); 7-day trial | Go: FB only. Higher tiers: FB, OfferUp, Craigslist, eBay, Nextdoor, Gumtree, Kijiji | Alert speed by tier (Basic, Fast, Instant). Price-drop alerts on Nitro only. 7/16/22 searches. AI scam filter, evaluator, "negotiator", VIN and title detection (Nitro) | App Store 4.4★ from 560 ratings. Visible complaints: "constantly misses cars", "doesn't update consistently", "Definitely Not Worth $352 a Month!" (DOCUMENTED, https://apps.apple.com/us/app/swoopa/id6475300269). DOCUMENTED pricing: https://getswoopa.com/pricing |
| **BigFlippa** | From $10/mo; Pro and Max tiers get 7 and 20 "radars" | FB, Craigslist | About 5 min latency claimed, a profit estimate on each alert, plain-English criteria, an MCP server | Self-declared: no VIN decode or title history (DOCUMENTED vendor page, https://bigflippa.com/best/car-flipping-apps/) |
| **CarAlert** | Starter $19/mo (Craigslist + Autotrader), Pro $39/mo adds FB | Craigslist, Autotrader, FB | Undervalued-car alerts | REPORTED via search extract; the site did not resolve when fetched |
| **CarFlipperAI** | Free bot (1 search), Premium and Pro tiers, prices not shown | FB, Craigslist, OfferUp | "As fast as 2 minutes" on Premium, deal score, Telegram bot, fleet and cost tracking | The method is opaque (DOCUMENTED vendor page, https://www.carflipper.ai/en) |
| **Flipify** | Subscription (Play Store page did not render) | FB, Craigslist | General-goods flipping alerts | — |
| **Apify FB Marketplace Scraper** (do-it-yourself) | $2.60–6.20 per 1,000 listings | FB | 12.7k users, 3.91★ | (DOCUMENTED, https://apify.com/apify/facebook-marketplace-scraper) |
| Free baseline | $0 | FB saved searches, Craigslist alerts, AutoTempest / CarGurus / Cars.com saved searches | Slow, single-source, no comps | REPORTED |

The pattern: the paid tools sell **speed + coverage + a profit or deal estimate**. Users complain about **missed listings, inconsistent refresh and price**. None of the tools reviewed advertises long-run price history or cross-site de-duplication.

---

## B. THE ENGINEERING

### B1. Open-source trackers: what they do and whether they still work

All TESTED (shallow clones read, plus GitHub API repo, issue and commit metadata pulled on 20 Nov 2026; dumps in `_scratch/common-practice/gh/`).

| Repo | ★ / last push | Sources | Access route | Sessions | Pacing | Blocks and breakage | Works now? |
|---|---|---|---|---|---|---|---|
| **BoPeng/ai-marketplace-monitor** (AGPL-3.0) | 425 / 2026-11-16, last commit 2026-10-18 | FB Marketplace. OfferUp (anonymous GraphQL) and eBay (Browse API) designed in issues #467 and #483, Oct 2026 | Playwright Chromium, **headed** (`headless=False`; Docker image with noVNC for servers). DOM parsing via aria-labels. FB location lookup through logged-out GraphQL (`doc_id`s hard-coded) | Types the username and password, waits for the user to clear a CAPTCHA or 2FA, and saves `storage_state` to a file readable only by the user. Checks the `c_user` cookie and `/checkpoint` paths. README advice: turn on 2FA, because approving the login on the phone "ends the repeated CAPTCHAs" | `schedule.every(search_interval).to(max_search_interval)` with max defaulting to 1.5× (jitter); README example `search_interval = "30m"`. Listing-detail cache keyed by URL, skipping a re-read unless price or title changed | Optional proxy support (a `swap_proxy` hook). Issues are mostly dependency bumps; the only FB breakage issues are old (#171 cookie pop-up, May 2025). The open issue on 3 Nov 2026 is a pickle-cache CVE | **Yes.** Actively maintained, the most mature |
| **stephanlensky/hyacinth** | 76 / 2026-11-20 (bots) | Craigslist, FB Marketplace | Playwright for both, with BeautifulSoup on the rendered HTML. The Craigslist URL is `.../search/{cat}#search=1~gallery~{page}~0` (client-rendered search) | Browser context | `craigslist_poll_interval_seconds = 600`, `marketplace_poll_interval_seconds = 600` | Issue #102 "Updates needed" (Nov 2025) still open; recent activity is only Renovate PRs | **Doubtful.** Maintenance has stopped |
| **jdcodes1/facebook-marketplace-mcp** | 501 / 2026-10-20 | FB | **Cookies from the user's own Chrome** (copies the Cookies SQLite file and decrypts with the macOS Keychain key) → fetch a page for the `fb_dtsg`, `lsd`, `jazoest` tokens → POST `/api/graphql/` with `doc_id`s. Ships a `capture-queries.ts` script to re-harvest `doc_id`s | The user's live browser session; no login automation | `RateLimiter(maxRequestsPerMinute ?? 3)` | PR #3 (28 Aug 2026) "Fix silent empty results: refresh doc_ids"; PR #7 (21 Sep 2026) "refresh search doc_id". Open PRs for a Windows/Edge/Brave cookie reader | **Yes, with roughly monthly doc_id churn.** macOS only on main |
| **jlsookiki/secondhand-mcp** | 106 / 2026-10-05 | FB, eBay, Depop, Poshmark, others | FB: logged-out GraphQL (after kyleronayne/marketplace-api). When FB returns a "gated" answer to non-browser clients, it **falls back to the logged-out HTML search page**, which still carries a full first page of results. Browser-shaped `sec-fetch-*` headers. eBay: official Browse API. Depop: headless browser through a residential proxy with IP rotation | None for FB | 3 attempts, 8 s per attempt, 15 s total budget; retries on 408/429/5xx; optional `SMARTPROXY_URL` residential proxy "avoids datacenter IP rate limits" | Issue #36 (1 Sep 2026): every FB query returned "No listings found". Fixed by #37 (7 Sep) with the page fallback | **Yes**, logged-out first page only |
| bhowiebkr/toyota_tundra_tracker | 3 / 2025-12-09 | FB, AutoTrader.ca, CarGurus.ca, Kijiji | **Chrome extension** that scrapes pages as the user browses (search, detail, and batch mode opening tabs) and POSTs to a local Python Qt app | The user's own session | Human-paced | — | Small, but the closest design to this project |
| irahorecka/pycraigslist, juliomalegria/python-craigslist | 58, 393 / code from 2021–22 | Craigslist | requests + HTML parsing of `/search/` | — | — | pycraigslist #10 "No results from query" (2022) and #11 still open, consistent with Craigslist moving search rendering to the client side. Recent pushes are only Dependabot | **No**, by the look of the issues |
| passivebot/facebook-marketplace-scraper | 408 / archived 2024 | FB | Playwright + BeautifulSoup | Login | — | Archived | No |
| linenoise/craigslist_monitor | 14 / 2013 code | Craigslist | RSS feeds | — | clockwork | Craigslist RSS is long gone | No |

Takeaways:
- (a) Facebook is the only hard source, and every route has broken within the last three months.
- (b) Maintained tools keep `doc_id`s and selectors in one file, plus a script that re-captures them.
- (c) The more robust FB tools use a **real logged-in browser or the user's own cookies** and accept slow pacing of minutes. Logged-out routes get the first page only.
- (d) No open-source tool found keeps long-run price history or scores cars against comps, apart from the tiny Tundra tracker.

### B2. How commercial car-data companies get their data

- **Dealer inventory syndication is the backbone.** Dealers keep inventory in an inventory or merchandising system (vAuto, HomeNet, Dealer Specialties) or in their website platform (Dealer.com, DealerOn, Dealer Inspire). That system pushes feeds, typically scheduled CSV/XML exports, to Autotrader, Cars.com, CarGurus, OEM sites and Meta automotive ads (REPORTED, industry-standard practice).
- **CarGurus** states that inventory "comes from feeds that dealers send us through the dealers' inventory partners or web site host partners" and that it does not scrape. Dealers are often unaware a provider is sending a feed (DOCUMENTED via search extract of https://dealerproducts.cargurus.ca/?p=170 ; DealerRefresh forum threads say the same, REPORTED). In 2015 it reported feeds from more than 100 sources, and Ford syndicated new inventory (REPORTED, https://www.autodealertodaymagazine.com/news/ford-syndicating-dealer-inventory-to-carguruscom).
- **Meta:** catalog feeds now feed paid Automotive Inventory Ads only, not organic Marketplace (REPORTED, AutoSweet).
- **Crawlers and aggregators:** MarketCheck and auto.dev resell coverage of "every dealership in the US and Canada" through APIs. Their collection method is not stated on the pricing pages; crawling of dealer sites is widely assumed (REPORTED).
- **Wholesale:** auction results (MMR) are proprietary to Cox and open only to logged-in dealers.

**Open to a small operator?**
- *Raw syndication feeds: no.* They are dealer-controlled B2B contracts.
- *Resold aggregates: yes, cheaply:*
  - **MarketCheck US**: Free $0 for 500 calls a month (no card), Basic $299 a month + data fees for 5,000 calls, Standard $749 a month. Per call: Inventory Search $0.002, MarketCheck Price $0.07, History by VIN $0.006 (DOCUMENTED, https://www.marketcheck.com/pricing.md).
  - **auto.dev**: Free 1,000 calls a month across VIN decode, listings and photos at 5 req/s; Growth $299 a month at $0.0015 per listings call; Scale $599 a month (DOCUMENTED, https://www.auto.dev/pricing).
  - **NHTSA vPIC** VIN decode and recalls: free (DOCUMENTED, standard public API).
  - **eBay Browse API**: free with app keys, **5,000 calls/day** default, more via the free Application Growth Check (DOCUMENTED, https://developer.ebay.com/develop/api/buy/api_call_limits). Finding and Shopping APIs decommissioned 5 Feb 2025 (REPORTED in AIMM issue #483; the eBay deprecation page returned 403).

  Together these cover the dealer half of the market legitimately, leaving scraping for the private-party sources.

### B3. Common architecture

- **Polling cadence (TESTED from code, plus vendor claims):**
  - FB: every 10 min (hyacinth), a 30 min example with 1.5× jitter (AIMM), at most 3 GraphQL requests a minute (jdcodes1). Paid services sell 2–5 min.
  - Craigslist: 10 min (hyacinth).
  - eBay: whatever 5,000 calls a day allows, so 5 min is easily affordable for a dozen searches.
  - Dealer and aggregator sources: hourly to daily is normal, because dealer inventory changes slowly.
  - Common practice is to **sort by newest and read page 1 only** on each poll, with a deeper crawl at a slow cadence.
- **Change detection.** Key on `(source, listing_id)`. Store a hash of price + title, and fetch details only when the hash changes (AIMM). Re-check status (available, pending, sold, removed) on a slower loop (AIMM's `check_status` with a delay). "Disappeared" means probably sold, which is the only free sold-price proxy.
- **Cross-site de-duplication.** Use the VIN when present: dealers almost always show it; private sellers sometimes put it in the text or photos. Otherwise use fuzzy matching on year, make, model, mileage, price and location. The Tundra tracker groups at a 95% similarity threshold on year, price and mileage. Perceptual image hashes (pHash) on the first photo are the common next step for cross-posted private listings (REPORTED). Phone numbers or seller names repeated across many listings flag dealers and curbstoners.
- **Alert delivery.** Push beats email. AIMM ships ntfy, Pushover, Pushbullet, Telegram and email. hyacinth uses Discord. Paid tools use mobile push or Telegram. Alerts are rate-limited or digested so they do not spam (AIMM `digest.py`; hyacinth `notification_frequency_seconds = 60`).
- **Browser-extension capture from the user's own session.** The common shapes are:
  - (1) A content script that reads the DOM or embedded JSON as the user browses, then POSTs to a local or remote backend (Tundra tracker).
  - (2) An extension that opens result and detail tabs in sequence as a "batch scrape" (Tundra tracker).
  - (3) Outside an extension, reading the browser's cookie store to replay the session from a script (jdcodes1).

  Shape (1) is the most robust against blocks: it is a real browser, a real account and human pace. Its weakness is coverage, since it only sees what the user loads, unless it drives tabs itself.

### B4. Sites with bot defences: what trackers actually do

| Approach | Who does it | Cost | Reliability (recent reports) |
|---|---|---|---|
| Logged-out plain HTTP against internal GraphQL | secondhand-mcp, AIMM location lookup, OfferUp (AIMM #467) | $0 | FB: works for page 1, but gated answers come back to non-browser clients and `doc_id`s change. There was a week-long total outage in Sep 2026. OfferUp: anonymous answers as of 16 Oct 2026 |
| Same, through **residential proxies** | secondhand-mcp (optional), Depop route | $1–8/GB. Budget pay-as-you-go about $1–4/GB (DataImpulse, Decodo about $3.50–3.75/GB); Oxylabs about $8/GB at 10 GB (REPORTED, https://aimultiple.com/proxy-pricing) | Reduces datacenter-IP rate limiting; does not fix the gating |
| **Headed browser with a real account and a saved session** | AIMM, hyacinth | $0 plus a machine that stays on | Most reliable for FB scale. The cost is CAPTCHA and 2FA babysitting, and some risk to the account |
| **User's own cookies replayed** | jdcodes1 | $0 | Works; breaks whenever doc_ids change (twice in Aug–Sep 2026) |
| **Extension capture in the user's session** | Tundra tracker, several FB Chrome extensions | $0 | Most robust per request; coverage is limited to pages actually loaded |
| **Paid data services** | Apify actor; Swoopa and peers | Apify $2.60–6.20 per 1k listings; alert apps $10–352/mo | Apify 3.9★. Swoopa users report missed listings |
| Official APIs or aggregators instead of scraping | eBay Browse, MarketCheck, auto.dev | Free tiers up to about $300/mo | Stable and contractual |

### B5. House style against common practice

**What the house style is missing:**
1. **Latency.** GitHub Actions `schedule` is "once every 5 minutes" at best, "can be delayed during periods of high loads", and "some queued jobs may be dropped". In a public repo, scheduled workflows are disabled after 60 days without repository activity (DOCUMENTED, https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows). The trade's edge is minutes on FB and Craigslist. Common practice runs the fast sources from an always-on box (home PC, NAS, Raspberry Pi, small VPS) or from an extension, and keeps cron for the slow sources (dealers, aggregators, history, site build).
2. **IP reputation.** Actions runners are datacenter IPs. Trackers that hit FB from servers add residential proxies or run from home.
3. **Push alerts.** A static Pages site is pull-only. Common practice sends ntfy, Pushover, Telegram or Discord. ntfy and Telegram are plain-HTTP POSTs from standard-library Python, so this fits the house style.
4. **Privacy.** Pages on a public repo publish the whole deal list and the strategy. Practitioners keep this private.
5. **Trade-specific enrichment** that flippers pay for:
   - VIN extraction and decoding (NHTSA vPIC).
   - Title-brand keywords (salvage, rebuilt, "lost title", "bill of sale only").
   - Seller-type and curbstoner detection (the same phone number or photos across listings, "dealer posing as private").
   - Sold/removed status tracking for days-on-market.
   - Price-drop alerts, which Swoopa reserves for its $352 tier.
6. **Selector and `doc_id` maintenance.** Maintained tools isolate the volatile identifiers, ship a re-capture script, and alert on "zero results" as a breakage signal rather than treating it as "no deals".
7. **Legal ceiling awareness.** In MD, 3 offers in 12 months creates the dealer presumption. A tracker for a buy-to-resell user should count his own purchases and sales per rolling 12 months.

**What common practice is missing that the house style has:**
1. **Price history and comps over time.** None of the open-source tools or the paid apps reviewed stores long-run history. History is what makes "priced well below comparable" defensible, gives a sold-price proxy from disappearance, and shows seasonality.
2. **Cross-source catalogue and de-duplication.** Only the tiny Tundra tracker does it.
3. **Transparent scoring.** Paid tools show opaque "AI" scores, while a deliberate comp model can be audited.
4. **Cost.** Standard library plus Actions plus Pages is $0 a month, against $144–352 a month for multi-source speed.
5. **Account safety.** Extension capture in his own session avoids login automation, CAPTCHA loops and credential storage, all pain points in AIMM's README.
6. **Legitimate dealer-side data.** Pairing scraped private-party listings with dealer comps from free MarketCheck or auto.dev tiers plus eBay Browse is rarer in the hobby tools than it should be.

**Net practice-led shape:**
- Cron (Actions) for dealer, aggregator and eBay pulls, history, scoring and the Pages build.
- An always-on home runner *or* the extension for FB, Craigslist and OfferUp at 5–15 minute pace.
- Push alerts via ntfy or Telegram.
- VIN and status tracking in SQLite.
- A per-12-month buy/sell counter against the state ceilings.
