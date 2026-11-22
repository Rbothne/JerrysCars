# 11 - Alerts and cadence: hearing about a bargain within minutes

Research date: 21 November 2026. Nothing was built, run, sent or signed up for. No workflow was triggered and no service's API was called.

Evidence tags, on every claim that matters:

- **DOCUMENTED**: the service's own page, address given, read today. The pages were read through a tool that summarises them, so every number should be looked at once more on the page itself before code depends on it.
- **REPORTED**: second-hand (forum, blog, vendor, issue thread).
- **MEASURED**: counted today in the local `data/catalogue.db`, opened read-only.
- **My estimate**: my own reasoning or recollection, not checked against a source.

---

## 1. Recommendation

### The design in one paragraph

Keep the full build twice a day exactly as it is. Add one small workflow, `watch.yml`, that reads only Craigslist's seven search pages every 15 minutes by day and hourly overnight, reads the listing page of each car it has not handled before, judges it against a rule kept on GitHub's side, and sends the ones that pass to the owner's phone through **ntfy.sh** with a plain HTTP POST from the standard library. What it has handled is one small JSON file on a branch of its own (`watch`). The catalogue and the page are not touched by it.

### What runs, how often, and what it reads

| Piece | Recommendation |
|---|---|
| Full build (`update.yml`) | Unchanged: 11:20 and 23:20 UTC, every dealer and source, catalogue to `data`, page to Pages. |
| Watcher (`watch.yml`, new) | A chain of runs like the shop tracker's "each run starts the next". Each run lasts just under an hour, does a check every 15 minutes (four checks), then starts the next run. From 11 pm to 6 am Central it checks once an hour. |
| Way back in | One timer, `37 * * * *`. A timer that fires while a run is going waits behind it (same `concurrency` group) and becomes the next run, exactly as in the shop tracker. If the chain breaks, the next timer that GitHub does deliver restarts it. |
| One check reads | 7 search pages (`/search/cto`, one per city), then one listing page for each key it has not handled. Same `fetch.paced`, same three seconds between requests to any `*.craigslist.org`, same `cartrack/0.1` name. |
| One check decides | Record the new listings into a throwaway copy of the catalogue (fetched once per run from the `data` branch, never saved back), run `identify.fill` and `value.judge` as the build does, apply the alert rule, send, mark handled, save the state file if it changed. |
| Permissions | `contents: write` (the `watch` branch), `actions: write` (to start the next run). No Pages, no `pull_request` trigger. |

### The request budget

| | Checks a day | Search pages | Listing pages | Craigslist pages a day | Busiest hour |
|---|---|---|---|---|---|
| Today (two builds) | 2 | 14 | about 20 | about 35 | - |
| **Recommended**: 15 min for 17 hours, hourly for 7, seven cities | 75 | 525 | about 20, plus about 20 the builds read again | **about 580** | **about 30** (28 search + 2 or so listings) |
| 15 min round the clock | 96 | 672 | same | about 725 | about 30 |
| 10 min round the clock | 144 | 1,008 | same | about 1,065 | about 44 |
| 10 min by day, 30 min by night, four nearest cities only | 116 | 464 | about 15 | about 515 | about 26 |

- New listings a day: 14, 14, 12, 10, 10, 16 posted on each of the last six days and still live, across all seven cities; 17 in the last 24 hours (MEASURED). Some cars come and go between two builds, so the true figure is higher: 20 to 30 (my estimate).
- Only 8 of 291 postings were made between 05:00 and 11:00 UTC, which is 11 pm to 5 am Central (MEASURED). That is why the night can be hourly.
- **Craigslist's own terms draw a line at 1,000 pages in 24 hours**: liquidated damages item (L), "requesting, viewing, or accessing more than 1,000 pages of CL in any 24-hour period", $0.25 a page beyond the first 1,000 (DOCUMENTED, https://www.craigslist.org/about/terms.of.use, "last updated August 16, 2019"). A ten-minute check of seven cities round the clock crosses that line on search pages alone. The recommended plan stays at about 58% of it.
- The first run must start from the keys the catalogue already holds. Without that it would read about 293 listing pages and send as many alerts.

### The channel

**ntfy.sh**, one topic with a long random name, sent with `urllib` (no new dependency). Loud alerts at priority 4 or 5 with the listing's address as the tap action; anything looser at priority 2, which arrives silently. If the owner's phone is an iPhone, or ntfy starts answering 429, the named second choice is a **Telegram bot** (also one HTTPS request, also free). Write the sender as one small function so the swap is a secret and five lines.

Also do this today, whatever is built: turn on **Craigslist's own saved-search email alerts** for each city (by owner, price ceiling, clean title). They cost no requests and break no terms, and they give a baseline to compare the watcher's speed against. Details in section 3.

### What the owner sets up once

1. Install the ntfy app, subscribe to a topic named with 30 or more random characters, allow notifications, and let high priority through Do Not Disturb.
2. In the repository: Settings, Secrets and variables, Actions. Add the secret `NTFY_TOPIC`. Optionally make a free ntfy account and add `NTFY_TOKEN`, so the limits are counted against the account, not the runner's shared address.
3. Add the alert rule: the committed `alerts.json` for the shape and harmless defaults, and the Actions **variable** `ALERT_RULES` for the real numbers if he would rather not publish his budget (section 5).
4. Press "Run workflow" on `watch.yml` once. The chain carries on from there.

### What is stored where

| What | Where | Public? |
|---|---|---|
| Listings, prices, `first_seen` | `data` branch, `catalogue.db`, written only by the full build | Yes, as now |
| Which listing keys the watcher has handled, when it first saw each, the last price it saw, the time of the last good check | `watch` branch, one small JSON file, one commit replaced each time, written only by the watcher | Yes. It says nothing about which cars were alerted. |
| The alert rule | `alerts.json` in the repository, overridden by the Actions variable `ALERT_RULES` | File: yes. Variable: only to people with access to the repository's settings (my estimate; the page read today does not say who can see variables). |
| The channel's address | Actions secret `NTFY_TOPIC` (and `NTFY_TOKEN`) | No |
| The alerts themselves | Nowhere on GitHub. ntfy keeps a message 12 hours. | No |

### How fast this is (my estimate)

A car appears on the search page, waits up to 15 minutes for the next check, costs about 25 seconds for the seven search pages and 3 seconds for its own page, and reaches the phone seconds later. Typical: 8 minutes after it shows on the search page. Worst by day: about 16 minutes. Overnight: up to an hour. How long Craigslist takes to put a new post on the search page is not known; the watcher should log `posted` against the moment it first saw each car, and a week of that settles whether 10 minutes would buy anything over 15.

---

## 2. Cadence: what GitHub Actions allows and delivers

### The rules

| Question | Answer | Tag |
|---|---|---|
| Shortest schedule | "The shortest interval you can run scheduled workflows is once every 5 minutes." | DOCUMENTED, https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows |
| Lateness | "The `schedule` event can be delayed during periods of high loads of GitHub Actions workflow runs." "If the load is sufficiently high enough, some queued jobs may be dropped." | DOCUMENTED, same page |
| Going quiet | "In a public repository, scheduled workflows are automatically disabled when no repository activity has occurred in 60 days." The page does not say whether a bot's push to the `data` branch counts as activity. | DOCUMENTED; the second sentence is unsettled |
| Lateness in practice | The owner's shop tracker: "GitHub's own timers start runs late or not at all (most hourly ones never ran)". | Owner's own record, `wishlist-site/README.md` and its `update.yml` |
| Lateness in practice, others | One small test: best run 17 minutes late, median about 26, one over ten hours. A vendor's figures for a top-of-hour job: most within 90 seconds, 1 in 10 over 5 minutes, 1 in 50 over 15. A daily job reported 8 to 14 hours late. No sound measurement of a `*/5` or `*/15` timer was found. | REPORTED, https://github.com/orgs/community/discussions/27130 , https://dev.to/smplkit/which-job-schedulers-fire-on-time-we-tested-ten-e42 , https://lowlysre.substack.com/p/predicting-github-cron-delays |
| A run starting the next | "events triggered by the `GITHUB_TOKEN` will not create a new workflow run", except that "`workflow_dispatch` and `repository_dispatch` events always create workflow runs." So `gh workflow run` with the run's own token works, as the shop tracker does. | DOCUMENTED, https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow |
| Longest job | "Each job in a workflow can run for up to 6 hours of execution time." | DOCUMENTED, https://docs.github.com/en/actions/reference/limits |
| Jobs at once, Free plan | 20, of which 5 macOS. The watcher holds one. | DOCUMENTED, same page |
| The run's own token | 1,000 API requests an hour per repository. | DOCUMENTED, same page |
| One at a time | A `concurrency` group has at most one running and, by default, one waiting; a newer waiting run cancels the older waiting one. `queue: max` allows up to 100 waiting. | DOCUMENTED, https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency |
| Cost | "The use of standard GitHub-hosted runners is free" in public repositories. A private repository on the Free plan draws on $12 of included compute a month. | DOCUMENTED, https://docs.github.com/en/billing/concepts/product-billing/github-actions |
| Terms | Actions may not be used for "any activity that places a burden on our servers, where that burden is disproportionate to the benefits provided to users", with the example "don't use Actions as a content delivery network or as part of a serverless application", nor for "any other activity unrelated to the production, testing, deployment, or publication of the software project" of the repository. GitHub may end jobs or suspend the account for misuse. | DOCUMENTED, https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features (Version Effective Date: August 27, 2026) |
| Pages | 1 GB site, 100 GB a month soft, deployments time out at 10 minutes. The 10-builds-an-hour soft limit "does not apply if you build and publish your site with a custom GitHub Actions workflow." | DOCUMENTED, https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits |

### Four ways to get a check every 15 minutes

| Way | Timing | Runner time a day | Needs | Weak point |
|---|---|---|---|---|
| A. Timer only, `*/15 * * * *` | Late by minutes to hours, sometimes dropped | about 75 short runs, about 1 minute each | Nothing | The owner's own record says the timers cannot be trusted. Lateness only delays alerts (section 6), but a dropped afternoon is the failure that matters. |
| B. One check a run, each run sleeps and starts the next (the shop tracker's chain) | Exact | A runner held all day, about 100 runs | `actions: write` | Holds a machine that mostly sleeps. |
| **C. Four checks a run, then start the next (recommended)** | Exact | A runner held all day, about 25 runs | `actions: write` | Same as B, with a quarter of the runs, one catalogue fetch an hour instead of four, and the keys already read kept in memory between checks. |
| D. An outside timer calls `workflow_dispatch` (cron-job.org is free, runs a job up to once a minute, sends custom headers and a body, mails on failure: DOCUMENTED, https://cron-job.org/en/faq/) | Exact to the minute | about 75 runs of under a minute | An account there, and a GitHub token limited to this repository's Actions, kept by that outside service | A secret held by a third party, and a token that expires. |

Why C: it is the pattern this owner already runs and trusts, it needs no outside party and no extra secret, and its timing is exact. Its cost is that it keeps one of GitHub's machines occupied around the clock, about 1,320 runner-minutes a day, free only while the repository is public. That sits uneasily beside the terms' "serverless application" and "disproportionate burden" wording. D is the answer if GitHub ever objects or the owner would rather not hold a runner; the watcher's code is the same either way, since it only needs to be started.

A cheap way to learn whether A would do: have every timer-started run print its scheduled minute beside its real start. After two weeks the log says how late this repository's timers are.

The watcher and the full build do not share a file: the build writes `data`, the watcher writes `watch` and only reads `data`. They do not need a common `concurrency` group. Twice a day both may ask Craigslist during the same minute, each at its own three-second pace; the watcher can skip a check while "Track cars" is running if that matters.

### Would Craigslist notice?

- robots.txt has no `Crawl-delay`, and neither `/search` nor `/view` is among its seven disallowed paths (DOCUMENTED, https://www.craigslist.org/robots.txt).
- The terms forbid the whole activity at any pace: one agrees "not to copy/collect CL content via robots, spiders, scripts, scrapers, crawlers", and item (K) sets $3,000 for each day of "aggregating, copying" content without written consent (DOCUMENTED, terms of use as above). The README already says so. Checking more often does not change which clause applies. It does raise the page count seventeen-fold, from about 35 to about 580 a day, and the terms count pages (item L).
- By volume, 30 requests an hour spread over seven hosts is less than one person leaving a search open (my estimate). By shape it is easy to pick out: the name `cartrack/0.1`, a datacenter address, seven hosts in 25 seconds, every 15 minutes on the dot. A site that turns away datacenter addresses or unknown names does it by class, not by counting.
- What is at stake is the twice-daily read as well: a refusal aimed at the tracker's name would cost the page its private cars. So on any 403 or 429 the watcher should leave that city alone for an hour, then two, then four, and say so in the daily summary.
- This is not legal advice, and whether Craigslist would act cannot be settled by reading.

---

## 3. Telling the owner: the channels compared

| Channel | One-time setup | Secret, and where it lives | Cost and limits | How fast | What can go wrong |
|---|---|---|---|---|---|
| **ntfy.sh** (recommended) | Install the app, subscribe to a random topic. No account needed. | The topic name, as Actions secret `NTFY_TOPIC`. "The topic is essentially a password." Optional account token as `NTFY_TOKEN`. | Free. 250 messages a day, 4,096 bytes a message, 60 requests at once then one every 5 seconds, per visitor; a visitor is an IP address. Paid from $5 a month (2,500 a day, 3 reserved topics). DOCUMENTED, https://docs.ntfy.sh/publish/ , https://docs.ntfy.sh/config/ , https://ntfy.sh/ | Seconds on Android. The Play build uses Google's Firebase for ntfy.sh, which the docs call "pretty bad at delivering messages in time"; "instant delivery" holds a connection open instead. iPhone goes through Firebase to Apple, and the FAQ calls the iOS app "very bare bones and quite frankly a little buggy". DOCUMENTED, https://docs.ntfy.sh/subscribe/phone/ , https://docs.ntfy.sh/faq/ | GitHub's runners share addresses with other people's jobs, so the per-address quota may already be spent: 429 (my estimate; an issue thread shows anonymous limits counted by IP and the server advising an access token, REPORTED, https://github.com/binwiederhier/ntfy/issues/1265). Anyone who learns the topic can read the alerts and send fake ones. "Best effort", no promise of uptime; the FAQ describes a single server. Messages pass through ntfy, Google and Apple unencrypted to them (DOCUMENTED, https://docs.ntfy.sh/privacy/ , last updated June 15, 2026). |
| **Telegram bot** (second choice) | Telegram account and app. Make a bot with BotFather (`/newbot`), press Start in its chat, read the chat's id once. | Bot token and chat id, two Actions secrets. "Keep your token secure... it can be used by anyone to control your bot." | Free: "bots are able to message their users at no cost". One message a second in a chat, 20 a minute in a group. DOCUMENTED, https://core.telegram.org/bots/faq , https://core.telegram.org/bots/features , https://core.telegram.org/bots/api (Bot API 10.4, November 9, 2026) | Seconds, on both phone systems (my estimate) | Limits are counted by bot, not by address, so shared runners do not matter (my estimate). A bot cannot write first: forgetting to press Start means silence (my recollection of the docs; not on the pages read today). A leaked token lets a stranger message him as the bot. |
| Pushover | Account, app, register an "application". | App token and user key, two Actions secrets. | 10,000 messages a month free per account; the app is a small one-time purchase after a trial (price not on the page read; about $5, my recollection). 1,024 characters. Emergency priority is "repeated until the notification is acknowledged". DOCUMENTED, https://pushover.net/api | Seconds (my estimate) | Costs a few dollars. The only one here that keeps ringing until answered, which suits a car that is gone in hours. |
| Discord webhook | Discord account, a server of his own, a channel, a webhook; set the channel to notify on every message. | The webhook address, an Actions secret. Webhooks "do not require a bot user or authentication to use". | Free. 2,000 characters, 10 embeds. Limits are dynamic; "If no authorization header is provided, then the limit is applied to the IP address." DOCUMENTED, https://docs.discord.com/developers/resources/webhook , https://docs.discord.com/developers/topics/rate-limits | Seconds (my estimate) | A webhook call carries no authorization header, so shared runner addresses can be limited for what others sent (my reading of the rule above; widely REPORTED for CI). More setup than it is worth for one reader. |
| Slack webhook | A workspace, a Slack app, incoming webhooks turned on, a channel chosen. | The webhook address, an Actions secret. "Slack actively searches out and revokes leaked secrets." | Free plan. The page gives no rate limit. DOCUMENTED, https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks | Seconds (my estimate) | The heaviest setup of all for one person. |
| Email from the workflow | A mail account that allows SMTP with an app password; `smtplib` is in the standard library. | SMTP user, app password and recipient, three Actions secrets. | Free. Gmail's sending limit is about 500 a day (my recollection; Google's page could not be read today). | Seconds to a minute to the inbox; the phone's buzz depends on the mail app | The app password opens the whole mailbox, a far bigger secret than a topic name. An alert drowns among other mail. Email-to-text is closed or closing: AT&T's ended 17 June 2025, T-Mobile's stopped in late 2024, Verizon has announced its shutdown (REPORTED, https://www.verizon.com/support/vtext-vzwpix-shutdown/ , https://www.androidauthority.com/atnt-email-to-text-feature-shutdown-3539223/). |
| GitHub's own notifications | GitHub Mobile with push on. The workflow comments on an issue and mentions him. | None: the run's own token with `issues: write`. | Free. 500 content-making requests an hour. DOCUMENTED, https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | Push arrives only for "Direct mentions", assignments, review requests and deployment approvals, so the comment must mention him; a release does not push. DOCUMENTED, https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications | An issue in a public repository is public: it would be a live list of the bargains and of what he is hunting. Private only by using a second, private repository and a personal token kept as a secret. |
| Feed file (Atom) and a reader app | Subscribe in a reader. | None, and that is the trouble: the feed is public. | Free. Each change is a Pages deployment. | Slow. Inoreader promises paying users an update "at least once every hour", faster refresh and push are paid features; Feedly is said to send no notifications at all (REPORTED, https://inoreader.com/pricing , https://feeder.co/knowledge-base/rss-basics/feedly-vs-inoreader/). An app that polls from the phone runs when the phone allows. Add Pages' own cache of about ten minutes (my recollection). Half an hour to hours. | Fails without a sound. Hands every reader the same bargains at the same moment. Good as a record, poor as an alarm. |
| The browser's notifications from the page | Open the page, allow notifications. On iPhone the page must first be added to the Home Screen (iOS 16.4 on: DOCUMENTED, https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/ , Feb 16, 2023). | For real push: the browser's subscription address, which "needs to be kept secret" (DOCUMENTED, https://developer.mozilla.org/en-US/docs/Web/API/Push_API), copied by hand into an Actions secret, plus a signing key pair. | Free | Without a sender, only while the page is open and awake. With the workflow as sender, seconds. | Sending needs elliptic-curve encryption and signing that the standard library does not have. Subscriptions lapse silently. Checking in the background on a timer is Chrome-only, for an installed app, when the browser chooses (DOCUMENTED, https://developer.mozilla.org/en-US/docs/Web/API/Web_Periodic_Background_Synchronization_API). The most work for the least dependable result. |
| Craigslist's own saved-search alerts | A Craigslist account; save a search per city; tick its alert box. | None in this project. | Free, no requests from the tracker, within the terms. "Search alerts send an automated email when new postings match one of your saved searches." DOCUMENTED, https://www.craigslist.org/about/help/account/features/searches | Not published. "At least 5-10 minutes after something is posted" in one user's experience (REPORTED, https://www.howtogeek.com/363109/how-to-set-up-craigslist-alerts-for-email-or-sms/). | Email only. No distance from his own home point, no comparison with similar cars, no other sources. Seven cities are seven searches. |

Why ntfy first: no account, one POST, a tap opens the listing, priorities separate "look when you can" from "look now", and nothing new to install in the workflow. Why Telegram second: its limits do not depend on the runner's address, and its apps are solid on both systems. Which phone the owner carries decides between them and was not known when this was written.

Whatever the channel, send one quiet message each morning: checks made, new cars seen, alerts sent, cities refused. A day without it means the watcher is dead. Failure mail from GitHub cannot be relied on for that: notifications go to whoever triggered a run, and a run started by the previous run was triggered by no person (my estimate; https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs says only "workflow runs that you've triggered").

---

## 4. What counts as worth an alert

### The rule, in the project's own fields

A listing is alerted when it is **new to the watcher** and passes every line of one of two clauses.

| Line | Field in `page_data` | Starting value (to be changed by the owner) |
|---|---|---|
| Sold by | `seller` is `private` (auction lots are handled apart, below) | private |
| Title | `title_status` is `clean` | clean only. 224 of 293 live private listings say clean (MEASURED). |
| Distance | `dealer_miles`, from the listing's own map pin | 75 miles |
| Fresh | `posted` no more than so many hours before now | 12 hours. Older ones are counted in the morning summary, not alerted. |
| A real price | at or above `MIN_ASK` ($500), which `make_listing` already enforces | - |
| **Clause 1, cheap**: price | `price` at or under the ceiling | $5,000. 100 of 293 live private listings are at or under it (MEASURED). |
| **Clause 2, under similar cars**: judged | `typical` is set, `similar` is 3 or more, and `price` is at least so far under `typical` | 25% under, with a higher ceiling of its own, say $12,000 |

Notes on the second clause:

- Only 29 of 291 private cars had the three similar cars a judgement needs (README). So "under similar cars" cannot be a condition every alert must meet; it would silence nine cars in ten. It is a second way in, and a line in the message ("$3,900, similar cars ask about $5,600, 4 of them" or "not judged").
- For cars under $10,000 the price model alone is 23% off at the median and reads 21% too high, and private cars are judged against dealers, who ask more (`research/09-value.md`, README). A tenth under, the page's mark, is inside that noise. Hence 25%, and no evidence yet that 25 is right.

With clean title, $5,000 and 75 miles, expect one to three loud alerts a day from about 15 to 25 new listings (my estimate from the counts above).

Two kinds of message keep the phone useful: **loud** (priority 4 or 5) for a car that passes the rule, and optionally **quiet** (priority 2, no sound) for a looser rule, such as any new private car under $8,000 within 150 miles. A third kind costs no extra request: a car already handled whose price on the search page has fallen under the ceiling since the watcher last saw it.

**Auction lots need a different rule, and no fast check.** The impound auction reader being added to the working tree today (`cartrack/sources/auctioneersoftware.py`, not committed when this was written) describes a weekly sale whose lots state year, make, model and VIN but "never" mileage or title, and have a bid, not an asking price. So the title, price-ceiling and under-similar lines cannot apply to a lot. What is worth sending is one message when a coming sale's lots first appear, listing the lots that match a wish list of makes, models and years. The sale is weekly, so the twice-daily build finding them is soon enough: the build can call the same sender after it saves, and the 15-minute watcher has no reason to ask that site at all (its reader notes the site answers 429 readily).

Guards against a flood: at most five loud alerts in one check, the rest folded into one message with a count; and a check in which more than a third of a city's search page is new is treated as a broken read and alerts nothing. The second guard matters because the README records that it is not yet known whether a listing's key lasts the listing's life. If keys change, every car would look new.

### Where the numbers live

The page is static and its filters live in the browser's form (the page does not even store them today: there is no `localStorage` in `site/`). Nothing in a browser can be read by a workflow. So yes: **a settings file on GitHub's side is the honest answer**, and the only one.

| Place | For | Against |
|---|---|---|
| `alerts.json` in the repository | Versioned, testable, editable from a phone in GitHub's web editor, and a push to `main` takes effect at the next check. | Public: it publishes his budget and what he is hunting. |
| Actions variable `ALERT_RULES` holding the same JSON | Off the page and out of the repository; editable in Settings. | Not masked in logs, so the watcher must never print it. Not versioned. |
| Actions secret | Hidden. | Cannot be read back, so every change means retyping the whole rule. GitHub warns that "structured data can cause secret redaction within logs to fail". |

Recommended: the file holds the shape and defaults he does not mind showing; the variable, if set, overrides them. The page can help without storing anything: a "copy as alert rule" button that turns the current filter form into the JSON to paste.

---

## 5. Not alerting twice, and not losing an alert

**The principle: "new" means "not in the handled set", never "posted in the last 15 minutes".** A check that runs late, fails, or is skipped then only delays an alert. The car is still on the search page at the next good check and is still not handled.

What has to be remembered, in `watch.json` on the `watch` branch:

| Kept | Why |
|---|---|
| `handled`: listing id, when the watcher first saw it, the price it last saw | The set that defines "new". The price lets a later cut be noticed. |
| `checked`: time of the last good check, per city | The morning summary, and the page can show "last looked for new cars 6 minutes ago". |
| Refusals and the back-off per city | So a restart does not hammer a city that said no. |

Rules that make it hold:

1. **A listing becomes handled only after its fate is settled**: judged not worth an alert, or the channel accepted the alert (HTTP 200). If the send fails, it stays unhandled and the next check tries again, at the cost of one more request for its page. No separate list of unsent alerts is needed, and nothing about which cars matched is ever written to the public branch.
2. **Order in a check**: read, judge, send, mark, save. The one gap is a crash after sending and before saving: the next run alerts that car again. ntfy can replace a message that carries the same sequence id instead of adding one (DOCUMENTED in passing on https://docs.ntfy.sh/publish/ ; check the header's exact name when building), so the listing's key as that id turns a duplicate into a refresh.
3. **The catalogue seeds the set once and never again.** The first run takes every Craigslist id in `catalogue.db` as handled. After that the watcher's set is its own. If it kept folding the catalogue in, a car the full build happened to record first would be marked handled without ever being judged for an alert.
4. **A stale alert is not sent.** After an outage, a car posted more than 12 hours ago goes into the summary.
5. **Forget old keys**: an id no search page has shown for 30 days is dropped. The file stays at a few hundred entries.
6. **`first_seen` in the catalogue stays the build's.** It will be up to 12 hours later than the watcher's. The build could later take the earlier time from `watch.json`; that is an improvement, not a need.

A repost of the same car under a new key is alerted again. The README lists reposts as not yet linked; for alerts that is the safer side to err on.

---

## 6. Privacy

The repository, both data branches, the page and the Actions logs are public.

**Must not appear in any of them:**

- The channel's address: topic, token, chat id or webhook.
- Which cars were alerted. A public list of them is a bargain feed for every other buyer, minutes after the owner gets it, and shows his rule by example. This rules out a public feed file, a public issue, and log lines such as "alerted: 2006 Camry $2,900". Logs carry counts only.
- The rule's numbers, if he wants his budget private (use the variable).
- The owner's phone number, email or anything narrower than the home point already in `area.json` (a city-centre point).
- Sellers' phone numbers, names and descriptions. The reader already drops them; an alert should carry title, price, year, miles, title status, distance, the comparison and the listing's address, nothing typed by the seller beyond the title.

**Can a private channel be used from a public repository's workflow? Yes, with these conditions:**

| Risk | Answer | Tag |
|---|---|---|
| Forks | "secrets are not passed to the runner when a workflow is triggered from a forked repository", the run's own token aside. A fork does not get the repository's secrets. | DOCUMENTED, https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets |
| Outsiders' code running with the secret | Give `watch.yml` only `schedule` and `workflow_dispatch`. Never `pull_request_target`: "These workflows are privileged". | DOCUMENTED, https://docs.github.com/en/actions/reference/security/secure-use |
| Logs | GitHub "automatically redacts" secrets, but "this redaction is not guaranteed", and it misses transformed values. So: pass the secret through `env:`, never on a command line; never print the request address, the service's reply (ntfy's reply repeats the topic) or an exception that holds the address; no `set -x`. If one leaks, "delete the log and rotate the secret". | DOCUMENTED, same page and https://docs.github.com/en/actions/concepts/security/secrets |
| Other people with write access | "Any user with write access to your repository has read access to all secrets". Keep the repository his alone. | DOCUMENTED, secure-use page |
| Third-party actions | None needed: the send is `urllib`. Nothing but GitHub's own checkout action ever runs beside the secret. | My estimate |
| The topic is a password, not a login | Anyone holding it can read the alerts and send a fake one with any link. Alerts should only ever link to `craigslist.org`; changing the topic is changing one secret and resubscribing. A reserved topic with a login costs $5 a month. | DOCUMENTED, ntfy pages above |
| Who else sees a message | ntfy's server for 12 hours, Google's Firebase, and Apple on an iPhone. The content is a public listing and the fact that it matched. | DOCUMENTED, https://docs.ntfy.sh/privacy/ |

---

## 7. Risks, and what could not be settled

1. **Craigslist's terms.** Collecting by program is forbidden at any pace; this plan multiplies the pages asked for by about seventeen. The 1,000-pages-a-day line is respected with room, but the exposure is real and could cost the twice-daily read too. Craigslist's own email alerts are the route with none of this.
2. **Holding a runner all day** leans on "free for public repositories" against terms that warn off "serverless application" use. GitHub may never mind; if it does, way D (an outside timer) is ready. The repository must stay public for either to be free.
3. **How late this repository's timers are** was not measured. The shop tracker's record is the only local evidence. The way-back-in timer can log it.
4. **How soon a new post reaches the search page**, and whether that page is cached on Craigslist's side, is unknown. The watcher's own log of posted-to-seen will say.
5. **Whether a listing's key lasts its life** is still unwatched (README). The flood guard covers the bad case; a week of `watch.json` answers it.
6. **ntfy from shared runner addresses**: the 429 risk is reasoned, not observed. An account token should remove it; Telegram does not have it. ntfy's FAQ describes a best-effort, single-server service.
7. **iPhone or Android** was not known, and it decides ntfy against Telegram or Pushover.
8. **Does a bot's push count as "repository activity"** for the 60-day rule? Not documented. The chain does not depend on timers, but the way back in does.
9. **Who can see an Actions variable** in a public repository was not stated on the page read. Treat the rule as private-ish, not secret.
10. **Numbers not confirmed on a primary page today**: Gmail's daily sending limit, Pushover's app price, Pages' cache time, Telegram's "a bot cannot write first". Each is marked above.
11. **The value judgement is weak exactly where the bargains are**: cars under $10,000, private sellers. Clause 2's 25% is a starting guess.
12. **Facebook Marketplace**, where `research/06` says most cheap private cars are, is outside this plan. The handled-set, the rule and the channel are source-blind, so the planned extension can feed the same alert path.
