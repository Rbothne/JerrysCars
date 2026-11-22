"""Make the zips to hand to someone else: extension/dist/car-capture-chrome.zip and car-capture-firefox.zip.

    py extension/pack.py

Each holds the extension and, when one is there, its config.local.json: {"repo": "owner/name", "token": "...",
"who": "anna"}. With it, the person receiving it has nothing to set up; each install still writes a file of its own,
named "who" plus a random tail. Git ignores config.local.json and extension/dist/, so the token never reaches the
public repository. Anyone who has a zip can read the token out of it: give one only to someone you would trust
with write access to the captures repository, and make that all the token can do.

Unzip it, then load the folder: Chrome's "Load unpacked", or Firefox's "Load Temporary Add-on" on manifest.json."""

import json
import pathlib
import zipfile

import make_firefox

HERE = pathlib.Path(__file__).parent
DIST = HERE / "dist"
CONFIG = "config.local.json"


def pack(folder, name, config):
    DIST.mkdir(exist_ok=True)
    target = DIST / name
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.name != CONFIG:
                archive.write(path, path.name)
        if config:
            archive.writestr(CONFIG, json.dumps(config, indent=1) + "\n")
    return target


def main():
    make_firefox.main()
    source = make_firefox.SOURCE / CONFIG
    config = json.loads(source.read_text(encoding="utf-8")) if source.exists() else None
    if config and not {"repo", "token"} <= set(config):
        raise SystemExit(f"{source} needs a repo and a token")
    for folder, name in ((make_firefox.SOURCE, "car-capture-chrome.zip"), (make_firefox.TARGET, "car-capture-firefox.zip")):
        print("wrote", pack(folder, name, config), "with a token" if config else "without a token: set it in the popup")


if __name__ == "__main__":
    main()
