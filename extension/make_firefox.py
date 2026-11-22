"""Write the Firefox copy of the Marketplace capture: extension/facebook-firefox/, from extension/facebook/.

    py extension/make_firefox.py

The scripts are the same files (they take `browser` in Firefox and `chrome` in Chrome). Only the manifest differs:
Firefox runs the background as an event page listing its scripts, not a service worker; it needs an add-on id of
its own to keep its storage and to be signed; Mozilla asks a new add-on to say what data it sends away; and the
page-world script needs Firefox 128 or later. tests/test_firefox_extension.py fails when the copy is out of date,
so after changing anything in extension/facebook/, run this again."""

import json
import pathlib
import shutil

HERE = pathlib.Path(__file__).parent
SOURCE, TARGET = HERE / "facebook", HERE / "facebook-firefox"
FILES = ("capture.js", "page.js", "relay.js", "background.js", "popup.html", "popup.js")
ID = "car-capture@jerryscars"


def manifest():
    made = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    made.pop("minimum_chrome_version", None)
    made["background"] = {"scripts": ["capture.js", "background.js"]}
    made["browser_specific_settings"] = {"gecko": {
        "id": ID, "strict_min_version": "128.0",
        "data_collection_permissions": {"required": ["websiteContent"]}}}   # listings read off the page go to GitHub
    return json.dumps(made, indent=2) + "\n"


def readme():
    return """# Car capture for Firefox

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
"""


def main():
    TARGET.mkdir(exist_ok=True)
    for name in FILES:
        shutil.copyfile(SOURCE / name, TARGET / name)
    (TARGET / "manifest.json").write_text(manifest(), encoding="utf-8", newline="\n")
    (TARGET / "README.md").write_text(readme(), encoding="utf-8", newline="\n")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
