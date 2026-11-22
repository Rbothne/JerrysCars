# 11. Facebook Marketplace: capturing what the owner himself sees

Worked 2026-11-21. A paper study. No Marketplace page and no Facebook API was requested, no account was used,
nothing was captured and no extension was built or loaded. What was read: this repository, the `webtoon`
project's extension and server, Chrome's and Mozilla's developer documentation, GitHub's REST documentation,
Meta's two terms pages and its robots.txt, Meta's own newsroom posts on scraping, and the source, READMEs and
histories of public projects on GitHub. The only addresses on facebook.com asked for were its two legal pages
and robots.txt.

Labels: **DOCUMENTED** = read in the operator's own page (address and the page's own date; all read
2026-11-21). **REPORTED** = second-hand: someone else's code, write-up or news report. **my estimate** = my
own judgement, not a source. Facts about this repository are marked "read here".

One limit to say first: nothing below about what Facebook sends has been seen by this project. Every field name
is from other people's code. The first real capture is what settles them (section 7).

## Verdict

**Workable, with one thing the owner has to accept knowingly: it is against Meta's terms as written.**

- **Technically it is ordinary.** Chrome documents everything it needs: a content script declared in the
  manifest, run in the page's own JavaScript world at `document_start`, can read the JSON the page embeds and
  the answers to the page's own requests. It needs one permission (`storage`) and no host permission for
  Facebook. A public project published in September 2026 does exactly this (section 1).
- **Chrome places no policy on it.** The Web Store's rules bind extensions submitted to the store. An unpacked
  extension is never submitted. The only condition is that Developer mode stays switched on.
- **Meta's terms forbid it in plain words** and say so "regardless of whether such automated access or
  collection is undertaken while logged-in to a Facebook account". There is no exception for personal use, for
  one user, for an extension, or for a tool that only watches. The stated consequence is suspension or
  permanent loss of the account (section 4).
- **The practical risk to the account is low but not zero, and cannot be measured from here.** No report was
  found of an account restricted for a watch-only extension. Every case found of Meta acting over an extension
  was against the maker of a published tool, not a user. What would be lost is the account he sources cars
  with.

**The one design recommended:** a three-part unpacked extension that **makes no request to Facebook of its
own, ever**; keeps vehicle listings only, with the seller left out before anything is stored; holds its own
list in the browser; and every half hour or so replaces **one JSON file in a small separate GitHub repository**
through GitHub's API, with a token that can write to that repository and nothing else. The build reads that
file as one more row of `sources.json`. This is option (c) of section 3, with the repository split off so the
token cannot touch the tracker itself.

It needs three things of the build (section 3, at its end): a listing's "seen" time must be the time he saw
it, not the time of the build; this source must age out on the calendar alone, which the build cannot do today;
and a reader needs a way to say "this one was marked sold" without calling its asking price a sale price.

---

## 1. The extension itself

### What Chrome allows on a page the user is viewing

| Point | What the documentation says | Label |
|---|---|---|
| Content scripts read the page | "Content scripts are files that run in the context of web pages. Using the standard Document Object Model (DOM), they are able to read details of the web pages the browser visits, make changes to them, and pass information to their parent extension." | DOCUMENTED, https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts (page stamp 2012-09-17, plainly not its real age) |
| Two worlds | By default a content script lives "in a private isolated execution environment that isn't accessible to the page". `"world": "MAIN"` "means the script will share the execution environment with the host page's JavaScript." | DOCUMENTED, https://developer.chrome.com/docs/extensions/reference/manifest/content-scripts (2023-08-10) |
| The warning that goes with it | "There are risks involved when using the "MAIN" world. The host page can access and interfere with the injected script." | DOCUMENTED, same page |
| When it runs | `"run_at": "document_start"`: "Scripts are injected after any files from css, but before any other DOM is constructed or any other script is run." | DOCUMENTED, content-scripts page |
| What a content script may call | `storage`, `runtime.sendMessage()`, `runtime.connect()`, `runtime.onMessage`, `runtime.getURL()`, `runtime.id`, `dom`, `i18n`. "Content scripts are unable to access other APIs directly." A main-world script has none of these. | DOCUMENTED, content-scripts page; "Scripts in this environment don't have any access to the APIs that are only available to content scripts" is Mozilla's wording for the same rule, https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/content_scripts (2026-09-22) |
| Page rules in the main world | "When a content script is injected into the main world, the CSP of the page applies." | DOCUMENTED, content-scripts page |
| Sending anything off the page | "Cross-origin requests are always treated as such in content scripts, even if the extension has host permissions." "A script executing in an extension service worker ... can talk to remote servers outside of its origin, as long as the extension requests host permissions." | DOCUMENTED, https://developer.chrome.com/docs/extensions/develop/concepts/network-requests |
| Host permission for Facebook | Not needed: "host permissions are not required" for "Allowing the injection of a content script declared in the manifest." | DOCUMENTED, https://developer.chrome.com/docs/extensions/develop/concepts/declare-permissions (2024-02-05) |
| Other ways to see response bodies | `webRequest` gives headers and the request body, not the response body. `debugger` can attach to a tab "to instrument network interaction" with the `debugger` permission; it is a debugger attached to his Facebook tab and is not suitable. | DOCUMENTED, https://developer.chrome.com/docs/extensions/reference/api/webRequest and .../api/debugger (2026-11-05) |
| The service worker sleeps | Chrome ends it "After 30 seconds of inactivity." Alarms may be set as short as 30 s. So anything not yet sent must sit in `chrome.storage`, never in a variable. | DOCUMENTED, https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle |
| `storage.local` | 10 MB, "cleared when the extension is removed", and "By default, it's exposed to content scripts, but this behavior can be changed by calling ... storage.local.setAccessLevel()". | DOCUMENTED, https://developer.chrome.com/docs/extensions/reference/api/storage (2026-10-29) |

### The conditions under which a page-world script sees the page's own responses

Chrome's pages do not describe wrapping `fetch`; they state the two facts it rests on (the main world is the
page's own JavaScript environment; `document_start` runs before any page script). Put together, with a working
public example to check against (REPORTED: https://github.com/skermiebroTech/marketplace-xray, `page.js` and
`manifest.json`, read 2026-11-21, MIT, three commits all on 2026-09-11):

1. The script is declared with `"world": "MAIN"` and `"run_at": "document_start"`, so it replaces
   `window.fetch` and `XMLHttpRequest.prototype.open/send` before Facebook's code takes its own reference to
   them. Chrome 111 or later (REPORTED, the project's README).
2. It reads a **copy** of each response (`response.clone().text()`), so the page still gets its answer.
3. It only sees what goes through those two functions. The first screen of results does not: Facebook embeds
   it in the HTML as `<script type="application/json">` blocks, which the same script reads from the DOM and
   watches for with a `MutationObserver` (REPORTED: marketplace-xray; `research/01`, section 3).
4. Facebook is one long-lived page. Clicking from the news feed to Marketplace loads no new document, so a
   script matched only on `/marketplace/*` would never be injected. The match has to be
   `https://www.facebook.com/*`, and the script must throw away everything that is not a listing, at once and
   in memory (my estimate, from how content scripts are injected; marketplace-xray matches the whole host).
5. The main-world script cannot store or send anything. It hands records to an ordinary (isolated) content
   script with `window.postMessage`; that script passes them to the service worker with
   `runtime.sendMessage()`. Only the service worker holds the list and any secret.
6. Because the page "can access and interfere with the injected script", Facebook's own code could in principle
   notice that `fetch` has been wrapped or read the messages. Whether it looks is not known (section 7).

### Permissions the recommended design asks for

```
"permissions": ["storage", "alarms"],
"host_permissions": ["https://api.github.com/*"],
"content_scripts": [
  {"matches": ["https://www.facebook.com/*"], "js": ["page.js"], "run_at": "document_start", "world": "MAIN"},
  {"matches": ["https://www.facebook.com/*"], "js": ["content.js"], "run_at": "document_start"}
]
```

No `tabs`, no `scripting`, no `webRequest`, no `cookies`, no `<all_urls>`. (The webtoon extension asks for
`<all_urls>`, `tabs` and `declarativeNetRequest` because it fetches images from any comic site; read here,
`webtoon/extension/manifest.json`. None of that carries over.)

### What Chrome's policies say for an unpacked, never-published extension

- **The Web Store's Program Policies are the store's.** "the Chrome Web Store requires all developers to comply
  with both the Developer Program Policies listed below, and the Developer Agreement. When your extension is
  reviewed by Google, these policies act as a guiding principle for those reviews." An unpacked extension is
  not submitted and not reviewed. No Chrome page was found that sets rules for what a locally loaded extension
  may do. (DOCUMENTED, https://developer.chrome.com/docs/webstore/program-policies/policies, 2025-05-22; the
  absence is my reading of it.)
- **Loading it:** `chrome://extensions`, Developer mode on, "Load unpacked". After any change to the manifest,
  the service worker or a content script, the extension must be reloaded and the Facebook tab refreshed.
  (DOCUMENTED, https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world)
- **Developer mode must stay on.** "Starting in Chrome 133, unpacked extensions loaded from the
  chrome://extensions page will only be enabled if the developer mode switch is turned on. When the switch is
  turned off, these extensions will be disabled." A later reply in the thread moved it to Chrome 134.
  (DOCUMENTED, Chrome Extensions DevRel, 2024-12-20,
  https://groups.google.com/a/chromium.org/g/chromium-extensions/c/cTdMVtxxooY)
- **There is no other off-store route on Windows.** "Windows and Mac installs must come from Chrome Web Store".
  So "never published" means unpacked with Developer mode on, for good. (DOCUMENTED,
  https://developer.chrome.com/docs/extensions/how-to/distribute/install-extensions)
- **Chrome may nag.** A "Disable developer mode extensions" prompt at start-up has been reported for years;
  whether the current version still shows it was not checked. (REPORTED,
  https://www.ghacks.net/2017/07/04/hide-chromes-disable-developer-mode-extensions-warning/)
- **If it were ever published** it would have to meet the store's user-data rules and this line: "Do not
  facilitate unauthorized access to content on websites, such as circumventing paywalls or login restrictions."
  (DOCUMENTED, same policies page.) Not a concern while it stays unpacked.
- The webtoon README has the owner loading that extension in **Opera** (read here). Opera is Chromium and loads
  unpacked extensions the same way; Opera's own behaviour with a main-world content script was not checked.

### What Firefox differs on

| Point | Firefox | Label |
|---|---|---|
| Installing for good | "Extensions and themes need to be signed by Mozilla before they can be installed in release and beta versions of Firefox." A temporary add-on "stays installed until you remove it or restart Firefox." Unsigned installs only in Developer Edition, Nightly and ESR with `xpinstall.signatures.required` turned off. Signing for one's own use ("unlisted") still goes through addons.mozilla.org and "All add-ons, including self-distributed ones, are subject to be manually reviewed at any time". | DOCUMENTED, https://extensionworkshop.com/documentation/publish/signing-and-distribution-overview/ and .../develop/temporary-installation-in-firefox/ |
| Main world | Supported in the `content_scripts` key from Firefox 128, with the same warning ("the web page can detect and interfere with the executed code"). | DOCUMENTED, MDN page above; version from Mozilla's add-ons blog of 2024-07-10, read through a search summary |
| Reading responses without touching the page | Firefox alone has `webRequest.filterResponseData()`: "The stream filter gives the web extension full control over the stream, with the ability to monitor and modify the response." Needs `webRequest`, `webRequestBlocking`, the host permission and, in Manifest V3, `webRequestFilterResponse`. Chrome has nothing like it. | DOCUMENTED, https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/filterResponseData (2025-07-17) |
| Isolation | Done by "Xray vision", not a separate world; a content script can reach page objects through `wrappedJSObject`, `cloneInto()` and `exportFunction()`. | DOCUMENTED, https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Content_scripts (2026-10-08) |
| Host access | "Registered content scripts are only executed if the extension is granted host permissions for the domain." | DOCUMENTED, same page |
| Manifest | Needs `browser_specific_settings.gecko.id`; marketplace-xray ships a second manifest for it. | REPORTED, that project |

The practical one is the first: on ordinary Firefox the extension would vanish at every restart unless Mozilla
signs it, and signing sends the code to Mozilla. **Build for Chromium only** (my estimate).

---

## 2. What would be captured

Field names are REPORTED throughout. Two independent pieces of code agree on the core ones four and a half
years apart: `kyleronayne/marketplace-api` (`MarketplaceScraper.py`, last commit 2022-04-17) and
`skermiebroTech/marketplace-xray` (`adapter-facebook.js`, 2026-09-11) both read `marketplace_listing_title`,
`listing_price`, `strikethrough_price`, `is_pending`, `primary_listing_photo`, `reverse_geocode` and
`marketplace_listing_seller` (both read 2026-11-21). The third source is `research/01`, section 3.

| What he sees | Raw field | On the search card | On the listing's own view | Keep? |
|---|---|---|---|---|
| Listing id | `id` | yes | yes | keep: it is the source id and the link |
| Title | `marketplace_listing_title` | yes | yes | keep |
| Price | `listing_price{amount, formatted_amount, currency}` | yes | yes | keep amount and currency |
| Earlier price, struck through | `strikethrough_price{amount, formatted_amount}` | yes | **no**: "The old price ("was") appears only when you reached the listing from a search page, because Facebook sends it with the search card, not with the listing page." (marketplace-xray README) | keep |
| Mileage | card: `custom_sub_titles_with_rendering_flags[].subtitle`, a short text such as "120K miles"; view: `vehicle_odometer_data{value, unit}` | rounded text only | exact | keep both, and say which (`miles_how`) |
| City and state | `location.reverse_geocode{city, state}` | yes | yes | keep |
| Postcode, map point | `location.reverse_geocode_detailed.postal_code_trimmed`, `location.latitude/longitude` ("Facebook marks the point as approximate") | not established | yes | keep the postcode; keep the point rounded to two decimals (about 0.7 mile), enough for distance |
| Sold, pending | `is_sold`, `is_pending` (also `is_live`, `is_hidden`) | yes | yes | keep as one word: live, pending, sold |
| Listing time | `creation_time` (seconds) | **not established.** `research/01` lists `listing_date` on cards from one vendor's output; marketplace-xray shows a date on cards but can fetch the listing itself to get it | yes | keep |
| Year, make, model | `vehicle_make_display_name`, `vehicle_model_display_name`; year is in the title | title only | yes | keep |
| Transmission, fuel, colours, condition | `vehicle_transmission_type`, `vehicle_fuel_type`, `vehicle_exterior_color`, `vehicle_interior_color`, `vehicle_condition` | no | yes, when the seller filled them | keep |
| Private seller or dealer | `vehicle_seller_type` (`PRIVATE_SELLER` or a dealer value) | no | yes | keep: this is a fact about the offer, not about a person |
| Title status | a `vehicle_*` key, name not confirmed | no | when filled | keep if found |
| VIN | a `vehicle_*` key, name not confirmed | no | **rarely.** Optional for the seller and "usually blank for private sellers" (`research/03`); marketplace-xray's author saw it empty on every listing in Australia | keep when present: `make_listing` checks it |
| First photo | `primary_listing_photo.image.uri` | yes | yes | keep the address only; see the note below |
| Seller name | `marketplace_listing_seller.name` | yes | yes | **drop** |
| Seller id, profile link, join date, rating, badges, other listings | `marketplace_listing_seller.id` and the seller-profile fields | id on cards | yes | **drop** |
| Seller's phone, website, dealership name | `seller_phone_number`, `vehicle_website_link`, `dealership_name` | no | when present | **drop** the phone and website; a dealership's trading name may be kept |
| Description | `redacted_description.text` | no | yes | **drop**. It is free text with phone numbers, addresses and names in it. The Craigslist reader drops it too |
| Photos beyond the first, Facebook's captions for them | `listing_photos[]` | no | yes | **drop**: driveways, number plates, people |
| His own state | whether he messaged the seller, whether he saved it, his viewer id | some | yes | **drop**. This is about the owner |

**Which need the listing opened:** exact mileage, the listing time, make and model as fields, transmission,
fuel, colour, condition, private-or-dealer, title status, VIN, postcode and map point. **The card alone gives:**
id, title, price, struck-through price, rounded mileage, city and state, sold or pending, first photo. That is
the same split as Craigslist, where the search page gives title and price and the listing's page the rest; and
"known in full" can mean the same thing (a listing with a `posted` time: read here, `build.py:source_jobs`).

**What a careful capture drops, and where.** Everything in the "drop" rows is discarded in the page-world
script, before the record is handed on, by copying named fields out and never the whole object. Also never
kept: cookies, the `fb_dtsg` and `lsd` tokens, request bodies, his search words, his own account id, and
anything from a response that is not a vehicle listing (the script sees every answer Facebook gives the page,
including the feed and message previews, because it has to look to tell). The reason is not only principle:
**this repository, its `data` branch and the page are public**, so anything kept is published. A hashed seller
id, which would let the tracker spot one person selling many cars, is still a way to single a person out and
is left out of the first version.

**The photo address will stop working.** Facebook's image addresses carry a signed expiry (`oe=`); "the image
will be invalid after a few days" (REPORTED, one Stack Overflow answer, by way of
https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/24656524/). Each time he sees the car again
the address is refreshed; a car not seen for a while will show a broken picture. Copying photos into the
repository would publish sellers' photos and is not recommended.

---

## 3. Where the captured listings go

Common to all four: the extension's own list in `chrome.storage.local` is the working copy (one record per
listing id, merged from card and view, pruned after a horizon), because the service worker is stopped after 30
seconds idle and because whatever receives the list may not be there.

### (a) The extension saves a file; the owner puts it in the repository

- **Steps for him:** click "Export" in the popup, find the file in Downloads, move it into the repository
  folder, commit, push. Each time.
- **Secret:** none new. His existing git sign-in.
- **What breaks:** he does. A capture that depends on five manual steps is done for a week. `chrome.downloads`
  can write to a fixed name under Downloads (`filename` is "A file path relative to the Downloads directory";
  `conflictAction: "overwrite"`), and a scheduled task could do the move and the push, which makes this (b)
  without the listener. It needs Python and git on the machine he browses on.
- **Honest merit:** nothing leaves his machine until he says so, and he can read the file first.

### (b) A small local program receives them and commits a file (the webtoon pattern)

How webtoon does it (read here): the content script never talks to the network; it messages the service worker,
which POSTs to `http://127.0.0.1:8765` with a header `X-WT-Client: 1`; the server refuses any request without
that header, because "A custom header forces a CORS preflight from web pages, which we never answer, so only
the extension (host permissions) and local tools can talk to us" (`server/webtoon_server/app.py`). It is
started by double-clicking `start-server.bat` and the popup shows a light when it is not running.

- **Steps for him:** once, install; then the program has to be running whenever he browses (a window left open,
  or a task at sign-in). Nothing else.
- **Secret:** none new. The program pushes with his existing git sign-in.
- **What breaks:**
  - The program is not running. With the extension's own list as a queue nothing is lost, only late.
  - Chrome's Local Network Access. From Chrome 142 a request "from the public network to a local network or
    loopback destination" needs a permission, and "Local network requests from Service Workers ... require that
    the worker's origin has previously been granted the Local Network Access permission." (DOCUMENTED,
    https://developer.chrome.com/blog/local-network-access, 2025-06-09.) Whether an extension with a host
    permission for `http://127.0.0.1/*` is exempt is said to be so by Chrome's team on its mailing list, with
    one developer in the same thread reporting it failed (REPORTED,
    https://groups.google.com/a/chromium.org/g/chromium-extensions/c/pUDh8RiTjJk). **Not settled.** The webtoon
    extension working today on his machine is the best evidence available, and it is in Opera.
  - A port on his PC that accepts listings. The header check keeps web pages out; any program on the PC can
    still write to it.
  - Python, git and a clone of the repository must be on the machine he browses on.
- **Honest merit:** no token anywhere, and it is the pattern the plan on file names. It adds a second program
  to keep alive for a job that is one HTTPS request.

### (c) The extension writes straight to GitHub with a fine-grained token (recommended, with the repository split off)

- **Steps for him:** once: make a token on GitHub and paste it into the popup. Then nothing, until the token
  expires.
- **Secret:** one fine-grained personal access token, kept in `chrome.storage.local`, used only by the service
  worker. It is typed into the popup and **never written into any file**, because the extension's folder would
  sit beside a public repository. What GitHub says of such tokens (DOCUMENTED,
  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens):
  "Each token can be further limited to only access specific repositories"; an expiry of 1 to 366 days, or
  none ("Infinite lifetimes are allowed"); "Treat your access tokens like passwords."
- **What the token must be allowed:** "Contents" repository permission, write, for `PUT
  /repos/{owner}/{repo}/contents/{path}`; the request carries the `branch` and, when replacing, the file's
  `sha` (DOCUMENTED, https://docs.github.com/en/rest/repos/contents). Changing anything under
  `.github/workflows` needs the separate "Workflows" permission, which this token would not have.
- **Why a separate repository.** The page offers no limit narrower than a repository: not a branch, not a
  path. A token with Contents-write on the tracker's own repository could rewrite `build.py`, which the
  workflow then runs with permission to replace the data branch and publish the page. Chrome's own advice is
  "If you're working with sensitive user data, instead use storage.session", which is emptied when the browser
  restarts; a token that must outlive a restart sits in `storage.local`, readable by content scripts unless
  `setAccessLevel()` is called. So: a
  second public repository holding one file (say `jerryscars-captures`, file `facebook.json`), and a token
  that can write there only. If the token leaks, the worst outcome is false listings in a file that the reader
  treats as data and checks. The simpler variant, a `captures` branch in the same repository, works the same
  and costs that protection.
- **What breaks:**
  - The token expires and the uploads fail quietly. The popup must show the last successful upload and the
    expiry date, and the build must show how old the file is.
  - Each `PUT` is a commit, so that repository's history grows by one small commit an upload (about 100 to
    200 KB of JSON before git packs it; my estimate). Uploading at most every half hour, and only when
    something changed, keeps it to a handful a day. GitHub's lower-level git endpoints can replace the branch
    with a single commit, as `data-branch.sh` does, if the growth ever matters.
  - An upload carrying an out-of-date `sha` is refused (the endpoint lists "409 Conflict"): one alarm, one
    upload at a time, and read the current `sha` first.
  - A push to another repository does not start this one's workflow. The twice-daily build picks the file up,
    so a capture can wait up to twelve hours to reach the page. That is acceptable here: he has already seen
    the car himself; the catalogue adds history and a judgement of value, not the first sight of it.
- **Honest cost:** the extension becomes a program that takes data out of a logged-in Facebook page and sends
  it to another company's server. Nothing in Chrome objects. It is the part Meta's terms are about (section 4).

### (d) The extension keeps its own list and the static page reads it in his browser

- **How:** the page cannot open an extension's storage. Either the extension declares
  `externally_connectable` with the page's address so the page may call `runtime.sendMessage()` to it ("If
  left empty or unspecified, no web pages can connect"; DOCUMENTED,
  https://developer.chrome.com/docs/extensions/reference/manifest/externally-connectable), or it runs a content
  script on `https://rbothne.github.io/jerryscars/*` that hands the list to the page.
- **Steps for him:** none.
- **Secret:** none. **Nothing captured from Facebook is published or leaves his machine.** This is the only
  option of which that is true, and the only one in which no third party could ever see what was collected.
- **What breaks, and it is most of the point of the project:**
  - The cars never enter `data/catalogue.db`. No price points, no seen-spans, no "gone", no VIN decoding, no
    naming by `identify.py`, no judgement by `value.py`: all of that runs in Python at build time (read here).
    They would appear on the page as bare, unjudged cards, or the valuation would have to be written a second
    time in JavaScript.
  - Only the one browser profile sees them; not his phone, not another PC.
  - "cleared when the extension is removed": remove the unpacked extension, or lose the profile, and the
    history is gone.
- **Honest merit:** if the owner reads section 4 and wants the lowest exposure, this is the form to build, and
  it can be built first: (c) is the same extension with an upload added.

### How the build would read the result (for a, b and c alike)

One more row in `sources.json`, one more reader in `cartrack/sources/`, registered in `SOURCES`. The reader has
the usual shape, `read(place, get, seen, known=())` giving `(listings, complete)` (read here,
`cartrack/sources/__init__.py`):

```
{"key": "facebook.com", "kind": "facebook", "name": "Facebook Marketplace",
 "url": "https://raw.githubusercontent.com/<owner>/jerryscars-captures/main/facebook.json", "unseen_days": 14}
```

- The reader asks for the file with the `get` it is given (the repository is public, so a plain request reads
  it; under (a) or (b) `url` would name a file on the `main` branch instead). One request a build. A 404 means
  no capture yet.
- It hands every row to `make_listing` with `channel="marketplace"` (already in `CHANNELS`) and returns
  `complete=False` **always**: he never sees all of Marketplace, so `close_out` must never run for this source.
- `known` is not needed for reading. It does say which captured cars still lack their own view (no `posted`
  time), which the page could one day list as "open these".

**How "gone" is decided when listings are only seen while he browses.** Three rules, in this order:

1. **He saw it marked sold.** Gone at the moment he saw that, `gone_how = 'sold'`. The catalogue's table
   allows the word (read here, `catalogue.py`); see the third point below for what sets it.
2. **He saw it marked pending.** Still live; carried as `extra.pending` for the page to show.
3. **He has not seen it for `unseen_days`.** Gone, `gone_how = 'unseen'`. Fourteen days is my estimate; the
   first month of captures will show how many cars reappear after ten or more days unseen, and the figure
   should be set from that.

A listing that comes back after being let go is "back", which `record()` already handles.

**Three things this needs of the build** (read here; this study changed none of it):

1. **The time a car was seen must be the capture's, not the build's.** Every reader passes the build's `now` as
   `seen`. If this reader did, a car he saw once would be "seen" again at every build for as long as it stayed
   in the file, and would never age out. `make_listing` takes `seen` per listing and `record()` keeps
   `max(last_seen, seen)`, so passing each row's own time works with no change to either. It is a rule for the
   reader to follow, not code to add.
2. **This source must age out on the calendar alone.** `_keep` calls `age_out` with the default three days for
   every source, and `age_out` lets nothing go unless some other listing of the source was seen inside the
   window ("A source not read at all in that time keeps everything"). Both are wrong here. Three days is too
   short for a car he may not scroll past again for a week. And if he stops browsing for a month, every
   Facebook car would stay on the page as live for that month. `age_out`'s own note warns of this kind of
   source: "Do not call it for a source whose list is cut short by design". Needed: the place's own
   `unseen_days`, and no "someone else was seen" condition for this kind.
3. **A reader's only way to say "sold" would say something untrue here.** When this study began there was no
   way at all. By its end the working tree (uncommitted, for the impound auction) had one: `catalogue.end(db,
   id, when, how)`, which `_keep` calls for any listing whose `price_kind` is `sold`, at the listing's `ends`
   time. That is the function this source needs, and it is stable under re-reading: `record()` clears `gone`
   on every call, and `end` then sets it back to the same stated time, so the date does not move. But
   `price_kind="sold"` means "this price is the sale's result", and on Facebook the price beside a sold mark is
   the last asking price; what the car fetched is never shown. Needed: a way to reach `end` that leaves the
   price an asking price (a status the reader sets, say), with `ends` carrying the time he saw it marked.

Three smaller ones:

- The struck-through price is older than anything the tracker saw, and `page_data` works out `was` only from
  its own price points, so `extra.was` would go unused until a line reads it.
- The page shows days listed but not "last seen"; for this source "last seen 6 days ago" is the honest thing
  to show.
- The working tree's `page_data` now takes two private listings with no VIN and the same year, mileage, price
  and map point for one car posted twice. Facebook's point is approximate and the capture rounds it, so two
  different cars of one year at one price and one odometer reading in the same square mile would be shown as
  one. Rare, since the exact odometer comes with the point; worth a test when the reader is written. The same
  rule will not join a Facebook car to its Craigslist twin, whose pin is exact.

These were read from the working tree on the evening of 2026-11-21, which then held other people's uncommitted
changes to `build.py`, `cartrack/catalogue.py` and `cartrack/sources/__init__.py`. Check them again before
building on this section.

---

## 4. Facebook's rules

### What the terms say

**Terms of Service**, https://www.facebook.com/legal/terms, "Effective January 1, 2025" (DOCUMENTED; read
through a fetch that returns the page's text in fragments, each quoted exactly):

- Section 3.2, among the things "You may not" do: "You may not access or collect data from our Products using
  automated means (without our prior permission) or attempt to access data you do not have permission to
  access, regardless of whether such automated access or collection is undertaken while logged-in to a Facebook
  account."
- Same section: "We can also suspend or disable your account for conduct that violates these provisions, as
  provided in Section 4.2."
- Section 4.2: "If we determine, in our discretion, that you have clearly, seriously or repeatedly breached our
  Terms or Policies, including in particular the Community Standards, we may suspend or permanently disable
  your access to Meta Company Products, and we may permanently disable or delete your account."
- The page does not contain the words "browser extension" or "scraping".

**Automated Data Collection Terms**, https://www.facebook.com/legal/automated_data_collection_terms,
"Effective October 7, 2024" (DOCUMENTED, same way):

- "You will not engage in Automated Data Collection without first obtaining Meta's express written permission
  or in any manner that is not explicitly authorized by Meta."
- The definition: Automated Data Collection "refers to the collection of data from Meta Company Products via
  the use of automated or programmatic tools capable of navigating or indexing the surface-layer of the World
  Wide Web", with the examples "web scrapers, bots, robots, spiders, crawlers, user-agents".
- Accepting these terms is not the permission; that is a separate written authorisation. With permission, the
  data may be used only for a search engine, for link previews, or as Meta approves in writing, and may not be
  sold or passed on (summarised; the fetch would not return those clauses word for word).
- They do not mention browser extensions, logged-in sessions, manual browsing or personal use.

**robots.txt**, https://www.facebook.com/robots.txt (DOCUMENTED): "Collection of data on Facebook through
automated means is prohibited unless you have express written permission from Facebook", and `Disallow: /` for
any agent not named.

**Meta's developer page** on the same subject repeats the Terms of Service sentence, including the logged-in
clause (DOCUMENTED, https://developers.facebook.com/docs/development/terms-and-policies/automated-data-collection/).

**Meta's own description of scraping:** "the automated collection of data from a website or app"; "Using
automation to get data from Facebook without our permission is a violation of our terms." (DOCUMENTED,
https://about.fb.com/news/2021/04/how-we-combat-scraping/, 2021-04-15.)

### What that means for this plan, said plainly

- **The extension is a program that collects data from Facebook while he is logged in, without Meta's
  permission. That is what the sentence in section 3.2 forbids.** The logged-in clause is aimed at exactly the
  case of a real user's own session.
- **There is one argument that it is outside the words, and it should not be leaned on.** The Automated Data
  Collection Terms define their subject as tools "capable of navigating or indexing" the web, and this
  extension navigates nothing: he does. But the Terms of Service sentence says only "automated means", Meta's
  own description is "the automated collection of data", and nothing Meta has published treats a watch-only
  tool differently. No statement from Meta either way about a passive, single-user extension was found.
- **There is no exemption** for personal use, non-commercial use, low volume, or data he is entitled to look at.
- **The public page is a second, separate exposure.** Options (a) to (c) end with Marketplace listings, their
  links and first photos on a public website and in a public repository under his name. A program nobody can
  see is one thing; a public page that visibly carries Marketplace listings is how a rights-holder finds out.
  Option (d) does not have this.
- **A court has drawn the same line.** In Meta v. Bright Data (N.D. Cal., case 3:23-cv-00077-EMC, January
  2024) Meta lost its contract claim because the scraping proved was of public pages while logged out: Bright
  Data "was not acting as a 'user' of the services at the time it was scraping, but only as a logged-out
  'visitor.'" Law-firm summaries of the ruling say Meta could have won only by proving scraping while logged
  in, and that the ruling does not speak to data behind a login (REPORTED,
  https://techcrunch.com/2024/01/24/court-rules-in-favor-of-a-web-scraper-bright-data-which-meta-had-used-and-then-sued
  and, through a search summary, https://www.jdsupra.com/legalnews/major-decision-affects-law-of-scraping-1470808/).
  This plan is the logged-in case. This note is not legal advice.

### What the practical risk to his account is reported to be

- **What Meta says it does:** "Rate limits cap the number of times anyone can interact with our products in a
  given amount of time"; data limits; looking for "patterns in activity and behavior that are typically
  associated with automated computer activity"; and, against scrapers, blocking, disabling accounts, "sending
  cease and desist letters" and "filing lawsuits against scrapers engaging in egregious behavior" (DOCUMENTED,
  the 2021 post above).
- **What the passive design gives those measures to see:** no request Facebook would not have received anyway.
  No extra page loads, no replayed queries, no timing that is not his own hand. The one thing visible from
  inside the page is that `fetch` has been wrapped (my estimate; section 7).
- **Reports of accounts restricted for a watch-only extension:** none found. Searched: the issue trackers of
  the public projects in section 5, and the web generally. That is an absence of reports, not evidence of
  safety: people who lose an account over a private tool have little reason to write it up, and vendor
  articles on the subject are selling something.
- **Who Meta has acted against over extensions, in every case found:** the makers of published tools.
  - 2021: it sued two people behind the "Oink and Stuff" extensions, which "contained hidden computer code that
    functioned like spyware", under its terms and Portuguese database law, seeking an injunction and deletion
    of the data. The users who had installed them were not defendants (DOCUMENTED,
    https://about.fb.com/news/2021/01/combating-scraping-by-malicious-browser-extensions/).
  - 2021: the author of "Unfollow Everything", an extension that acted on a user's own account, received a
    cease-and-desist letter citing the automated-means rule and wrote that Meta "permanently disabled my
    Facebook and Instagram accounts" (REPORTED,
    https://knightcolumbia.org/content/facebook-banned-me-for-life-because-i-help-people-use-it-less).
  - 2020: BrandTotal and Unimania, over extensions that read data from users' logged-in sessions (REPORTED,
    https://iapp.org/news/b/meta-settles-its-lawsuit-against-web-advertisers-for-data-scraping).
- **Tools that do far more, with real accounts, in public:** `ai-marketplace-monitor` (425 stars) drives a
  logged-in browser on a timer; its README says "Facebook's terms prohibit automated data collection without
  authorization" and "You are solely responsible", describes repeated CAPTCHAs, and says nothing either way
  about lost accounts (REPORTED, https://github.com/BoPeng/ai-marketplace-monitor). Another project sells itself on the opposite
  premise: "Your personal Facebook account at risk if you scrape it yourself" (REPORTED,
  https://github.com/diwakar57/fb-marketplace-carfinder). Neither is evidence about a passive capture.
- **My estimate:** the chance of Meta noticing a private, watch-only extension is small, and smaller than for
  anything else in `research/06`, section B4. It is not nil, it cannot be put as a number, and **the loss is
  not graded**: the account, its Marketplace standing and its message history with sellers go together, by a
  decision Meta makes "in our discretion". For a man whose buying runs through that account, that is the whole
  channel. A second account to browse with would itself break Meta's rules and is not suggested.

### What lowers the exposure, in order of effect

1. **Never make a request.** No fetching a listing he did not open, no "load more", no opening tabs, no
   refreshing on a timer. marketplace-xray fetches seller statistics and photos itself with replayed query ids;
   `majusss/fb-marketplace-filter` fetches each listing's details in the background. Both cross from watching
   into asking, and into the part that breaks (section 5). The recommended design does neither.
2. **Do not publish what was captured** (option d), or publish less (no photo, no link).
3. **Keep no seller data**, so that what is held is about cars.
4. **A pause switch** in the popup, and capture only on Marketplace addresses.

---

## 5. Effort and upkeep

### How often such tools break, by how they read Facebook

| How it reads | Project | What its history shows | Label |
|---|---|---|---|
| The rendered page (selectors, aria labels) | `BoPeng/ai-marketplace-monitor`, commits to its Facebook module, 2025-03 to 2026-10 | "Add FacebookFlexItemPage for new span/div listing layout" and "Fix Facebook login: ... broken button selector" (2026-07-17); "Skip attribute rows when reading the description of flex item pages" (2026-10-07); "Vehicle description fixes" (2026-03-21); two cookie-prompt fixes (2025-05, 2025-07); issue #29 "Handle different layouts of facebook listing items" open since 2025-02. **About three to five layout repairs a year.** | REPORTED, GitHub API, read 2026-11-21 |
| The rendered page | `bhowiebkr/toyota_tundra_tracker` (extension plus local Python program) | Its own README: "The scrapers rely on the current HTML structure of each marketplace. If they change their markup, the scrapers will break", and "unlikely to be actively maintained". No fixes after 2025-12. | REPORTED |
| The rendered page | `codensham/marketplace-declutter`, `Primitivelabai/punnet-marketplace` | Both READMEs carry the same line: "Facebook changes its pages often, which can break detection". | REPORTED |
| Replaying Facebook's queries by id | `jdcodes1/facebook-marketplace-mcp` | Two "refresh doc_id" fixes in five weeks, August to September 2026. | read here, `research/06`, B1 |
| Logged-out queries | `jlsookiki/secondhand-mcp` | A week with no results at all, September 2026. | read here, `research/06`, B1 |
| **The JSON the page already receives, by field name** | `skermiebroTech/marketplace-xray` | Three commits, all on 2026-09-11, no issues: **no track record either way.** Its README's only "when Facebook changes it" note is about a query id used for a request the extension itself makes. | REPORTED |
| Field names over time | `kyleronayne/marketplace-api` (2022-04) against marketplace-xray (2026-09) | The seven core listing fields carry the same names four and a half years apart. | REPORTED, both read 2026-11-21 |

What this adds up to (my estimate): reading the layout breaks several times a year; replaying queries breaks
monthly; reading listing objects by field name out of answers the page was getting anyway has the fewest
things that can move, and the only dated evidence on it is that the names have been stable since 2022. Expect
**one to three small repairs a year**, each a changed or added field name, and plan for the one that is not
small: Facebook changing how answers reach the page (a different transport than `fetch` and
`XMLHttpRequest`, or the embedded blocks going away), which would stop the capture entirely until the
page-world script is reworked. No public project found has a long enough history of this method to say how
often that happens.

### What keeps the repair small

1. **Depend on nothing that rotates.** No query names, no `doc_id`s, no path inside a response, no CSS class,
   no aria label, no request of its own. Find listings by shape: any object anywhere in a response that has a
   string `id` and a `marketplace_listing_title` or a `listing_price`. marketplace-xray's `walk()` does this in
   about ten lines.
2. **One field map, in one file.** Every raw name in section 2 appears once, in a table from raw name to the
   capture's name. A repair is an edit to that table.
3. **A pure function with a test.** `rows(json)` takes a parsed response and gives capture rows, touching no
   browser API, so it runs under `node --test` beside `tests/js/logic.test.mjs`, against a made-up response.
   Real responses hold other people's data and stay out of the repository.
4. **Say when it has gone blind.** The project's own rule from `research/06`: zero results is a breakage
   signal, not "no cars". In the popup: listing objects seen today, vehicles kept, and a red mark when he has
   been on Marketplace addresses for some minutes and nothing was recognised. In the build: the reader reports
   the file's age and row count, and refuses (as the other readers do with `NotRead`) a file where most rows
   lack an id or a title.
5. **Keep the names it did not understand.** For each listing object, the list of `vehicle_*` key names seen
   (names only, no values) goes into the popup's diagnostics. A new or renamed field then shows itself, and the
   VIN and title-status names get settled this way on the first day.
6. **Nothing clever on the receiving side.** The whole list is written each time, so an upload is safe to
   repeat and the reader never merges.

### Effort (my estimate)

- Extension: page-world script about 80 lines, relay 20, service worker (list, pruning, upload) 150, popup 60.
  The webtoon extension's popup and its storage and messaging habits carry over; its content script and
  background do not.
- Reader and its tests: about 60 lines of Python, shaped like `craigslist.py` without the fetching.
- The three build changes in section 3: about 20 lines, plus tests.
- Two to three working days, of which half a day is the first live capture and correcting field names. That
  step needs the owner's own browser and cannot be done by a program on a server.

---

## 6. The file a reader in `cartrack/sources/` would take

One JSON document, UTF-8, replaced whole at each upload. Times are UTC, "YYYY-MM-DDTHH:MM", as the catalogue
keeps them. A value the capture does not have is `null`. Money and miles are numbers.

```json
{
  "format": 1,
  "written": "2026-11-21T23:05",
  "extension": "0.1.0",
  "horizon_days": 21,
  "listings": [
    {
      "id": "1234567890123456",
      "first_seen": "2026-11-19T14:02",
      "seen": "2026-11-21T22:58",
      "detail_seen": "2026-11-20T01:15",
      "status": "live",
      "status_seen": "2026-11-19T14:02",
      "title": "2012 Honda Civic LX Sedan 4D",
      "price": 4500,
      "currency": "USD",
      "was": 5200,
      "miles": 142350,
      "miles_how": "detail",
      "posted": "2026-11-18T09:31",
      "seller_type": "private",
      "year": 2012,
      "make": "Honda",
      "model": "Civic",
      "vin": null,
      "title_status": null,
      "transmission": "automatic",
      "fuel": "gasoline",
      "color": "Silver",
      "condition": "good",
      "city": "Memphis",
      "state": "TN",
      "zip": "38111",
      "lat": 35.11,
      "lon": -89.94,
      "photo": "https://scontent.../first-photo.jpg"
    }
  ]
}
```

| Capture field | Meaning | `make_listing` argument |
|---|---|---|
| `id` | Facebook's listing id, a string of digits | `source_id`; `url` is `https://www.facebook.com/marketplace/item/<id>/` |
| `seen` | the last time he saw it, card or view | `seen` (**not** the build's `now`; section 3) |
| `first_seen` | the first time the extension saw it | not passed; the catalogue keeps its own, which will agree on a first read |
| `detail_seen` | the last time he opened the listing; `null` if he never has | none; tells the reader which fields to trust |
| `status`, `status_seen` | `live`, `pending` or `sold`, and when it was first seen so | `sold`: `ends=status_seen` and whatever signal reaches `catalogue.end` (section 3, third point); `pending` goes to `extra.pending` |
| `title` | as Facebook shows it | `title`; and `extra.makemodel` (the title without its leading year) when `make` or `model` is `null`, so `identify.py` names it |
| `price`, `currency` | the asking price | `price`, `currency`, `price_kind="ask"`. Under $500 becomes no price, as for every source (`MIN_ASK`) |
| `was` | the struck-through earlier price | `extra.was` |
| `miles`, `miles_how` | `detail` is the exact odometer; `card` is the rounded text ("142K miles" gives 142000) | `miles`; `extra.miles_how`. The extension never replaces a `detail` figure with a `card` one, or every scroll past would look like an odometer change and add a price point |
| `posted` | Facebook's listing time | `posted`. Present only once he has opened the listing, so "has a posted time" means "held in full", as for Craigslist |
| `seller_type` | `private`, `dealer` or `null` | `seller_type` |
| `year`, `make`, `model` | year from the title; make and model from the listing's own view | same names |
| `vin`, `title_status`, `transmission`, `fuel`, `color`, `condition` | from the listing's own view, when the seller gave them | same names; `title_status` mapped to the catalogue's words |
| `city`, `state`, `zip` | as Facebook gives them | same names |
| `lat`, `lon` | Facebook's approximate point, rounded to two decimals | `lat`, `lon`, `geo_how="city"`. Without them the car has no distance and the page's "within" filter lets it through (read here, `site/logic.js`) |
| `photo` | the first photo's address | `photos=[photo]` |

Always: `channel="marketplace"`, `source` the row's `key`. Never in the file: seller name, seller id, profile or
message links, phone, description, further photos, anything about the owner's own account.

The reader should refuse the file (`NotRead`) when `format` is not one it knows, when `listings` is missing, or
when most rows have no `id` or no `title`; and should leave out, without failing, any row whose `seen` is older
than the place's `unseen_days`, so that a stale file cannot hold a car open.

---

## 7. Risks, and what could not be settled

**Risks**

1. **Meta's terms.** The plan breaks them as written; the consequence named is the account. Section 4.
2. **Publication.** Under (a) to (c) captured listings appear on a public page and in a public repository.
   That is more visible than the capture itself. Making the tracker's repository private would end free
   GitHub Pages ("GitHub Pages is available in public repositories with GitHub Free"; DOCUMENTED,
   https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
3. **Sellers' data.** Avoided only if the drop list in section 2 is enforced where the data is first touched.
   A description or a seller name that reached the file would be public and would stay in that repository's
   history.
4. **The token** (option c). Bounded by the separate repository; still a credential in a browser profile.
5. **Coverage is his browsing.** The catalogue will hold the cars he scrolled past, not the market.
   `research/03` guessed 150 to 400. Value judgements will lean on what he tends to look at.
6. **Stale cars.** Without the calendar rule in section 3, Facebook cars would outlive their listings on the
   page.
7. **Silent failure.** A change at Facebook makes the capture see nothing, and nothing errors. Section 5,
   point 4.
8. **Developer mode.** One switch turned off in `chrome://extensions` disables the extension without a word.

**Not settled**

- **Every field name**, until one real capture. In particular: whether a search card carries the listing time;
  the raw names for VIN and title status; whether `postal_code_trimmed` is a full five-digit ZIP in the US;
  the form of the card's mileage text.
- **Whether Facebook's page code notices a wrapped `fetch`**, or does anything about it. Not knowable without
  looking at Facebook's scripts, which this study did not do.
- **Whether Facebook serves Marketplace answers only through `fetch`, `XMLHttpRequest` and embedded JSON.**
  marketplace-xray's working in September 2026 says yes at that date (REPORTED).
- **How Meta would read "automated means" for a watch-only tool.** No statement found.
- **How long a photo address lasts.** "A few days" from one old answer.
- **Local Network Access and extensions** (matters only for option b).
- **Opera.** The webtoon README shows the owner using it; main-world content scripts and the developer-mode
  rules were read for Chrome only.
- **Whether the machine he browses on is the one with Python, git and this repository.** Options (a) and (b)
  need that; (c) and (d) do not.
- **The right `unseen_days`.** Fourteen is a guess to be replaced by the first month's data.
- **The exact wording of most clauses of the Automated Data Collection Terms.** The fetch returned summaries
  for clauses 4 to 7; only the sentences quoted in section 4 were returned word for word. Meta's pages did not
  yield their text to a plain request.
