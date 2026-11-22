# Car capture (Facebook Marketplace)

For Firefox, use `extension/facebook-firefox/` (same scripts; its README says how to load it).

A Chrome extension that keeps the vehicle listings you see while you browse Facebook Marketplace, and every half
hour writes them as one file to a GitHub repository, where the car tracker's build reads them.

It only looks. It reads copies of what Facebook sends the page you are on, and makes no request to Facebook of its
own: what it keeps is what you scrolled past or opened. It copies out the car's own fields (title, price, an
earlier price, mileage, town, sold or pending, the first photo, and, once you open a listing, the odometer, the
listing time and the vehicle's details) and drops the rest before anything is stored: the seller's name and
profile, the description, phone numbers, other photos, and anything about your own account. The design and its
reasons are in `research/11-facebook-capture.md`.

**Meta's terms forbid collecting its data "using automated means", logged in or not, and say an account can be
suspended or disabled for it.** No report was found of an account closed for a tool that only watches, but nothing
in the terms excepts one. It runs in your account, and the file it writes is public.

## Set up once

1. On GitHub, make a new **public** repository for the captures alone, for example `jerryscars-captures`, with a
   README so it has a `main` branch. Keep it separate from the tracker: the token below can then touch nothing else.
2. Make a fine-grained personal access token (Settings, Developer settings, Personal access tokens, Fine-grained):
   only that repository, permission **Contents: read and write**, nothing more. Pick an expiry and note it.
3. In Chrome (or Edge), open `chrome://extensions`, turn on **Developer mode**, choose **Load unpacked** and pick
   this folder. Leave Developer mode on: turning it off disables the extension without a word.
4. Open the extension's popup, type the repository (`owner/name`) and paste the token, and press Save.
5. If the repository is not `Rbothne/jerryscars-captures`, change the `url` of the `facebook.com` row in the
   tracker's `sources.json` to `https://raw.githubusercontent.com/<owner>/<name>/main/facebook.json`.

Then browse Marketplace as usual. Opening a listing gives the tracker far more than seeing its card.

## Handing it to someone else

Put `{"repo": "owner/name", "token": "..."}` in `extension/facebook/config.local.json` and run
`py extension/pack.py`. It writes `extension/dist/car-capture-chrome.zip` and `car-capture-firefox.zip` with the
config inside, so the person who gets one only unzips it and loads it. Each install writes its own file,
`captures/<name>.json` (a random name unless one is typed into the popup), and the build reads them all, so two
people never write over each other. Git ignores the config and the zips. **Anyone with a zip can read the token
out of it**: hand it only to people you would trust with write access to the captures repository, and give the
token no more than that. When it expires, every copy stops uploading until it is replaced and repacked.

## Every so often

- The popup says how many vehicles are kept, how many you opened, and when the last upload was. "Refused (401)"
  means the token has expired: make a new one and paste it in.
- A red line saying nothing was recognised on Marketplace means Facebook has changed what it sends. The field map
  is in one place, `row()` in `capture.js`, and its tests are in `tests/js/capture.test.mjs`.
- "Vehicle field names seen" lists the names Facebook used for vehicle details, without their values: the place to
  look when a new field appears or the VIN's name needs settling.
- Pause stops it keeping anything new. Removing the extension removes everything it kept.

The tracker reads the file at each of its twice-daily builds, so a car you saw reaches the page within twelve hours.
A car you have not seen for 14 days goes off the page; one you saw marked sold goes at once.
