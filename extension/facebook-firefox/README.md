# Car capture for Firefox

Written by `extension/make_firefox.py` from `extension/facebook/`: change the files there, then run that script.
What the extension does, what it keeps and drops, and the GitHub setup are in `extension/facebook/README.md`.

Firefox 128 or later. Three things differ from Chrome:

1. **Loading it.** Open `about:debugging#/runtime/this-firefox`, press **Load Temporary Add-on** and pick
   `manifest.json` in this folder. A temporary add-on is removed when Firefox closes, and what it kept goes with it.
   To keep it across restarts it must be signed by Mozilla. Signing for your own use is free and does not list it
   anywhere: make an account at addons.mozilla.org, choose "On your own" when submitting, and upload this folder
   as a zip (or run `web-ext sign --channel=unlisted` here). Install the signed `.xpi` file it gives back.
   Firefox Developer Edition or Nightly can instead run it unsigned with `xpinstall.signatures.required` set to
   false in `about:config`; release Firefox cannot.
2. **Site access.** Firefox may leave access to facebook.com and api.github.com ungranted. The popup then shows
   an **Allow** button; press it once. It can also be granted from the add-on's entry in `about:addons`,
   under Permissions.
3. **Mozilla asks what it sends away.** The manifest says it sends website content (the listings) to a server
   (GitHub). Firefox shows that when it is installed.
