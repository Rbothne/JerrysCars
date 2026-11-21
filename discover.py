"""Find the car dealers around the home point and which website platform each one runs on.

    py discover.py

Reads area.json (home point and radius) and dealers-seed.json (hand-kept dealers OpenStreetMap lacks).
Writes dealers.json and the dealer table of data/catalogue.db. Asks OpenStreetMap once, DNS once per dealer
host, and a dealer's own front page once only when DNS does not say which platform it runs on."""

import collections
import datetime
import json
import pathlib

from cartrack import catalogue, dealers

ROOT = pathlib.Path(__file__).parent


def main():
    area = json.loads((ROOT / "area.json").read_text(encoding="utf-8"))
    seeds = json.loads((ROOT / "dealers-seed.json").read_text(encoding="utf-8"))
    when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M")

    found = dealers.discover(area, seeds)

    (ROOT / "dealers.json").write_text(
        json.dumps({"area": area, "found": when, "dealers": found}, indent=1) + "\n", encoding="utf-8")
    (ROOT / "data").mkdir(exist_ok=True)
    db = catalogue.open_catalogue(ROOT / "data" / "catalogue.db")
    catalogue.save_dealers(db, found, when)
    db.close()

    with_site = [dealer for dealer in found if dealer["host"]]
    print(f"{area['name']}, {area['radius_miles']} miles: {len(found)} dealers, {len(with_site)} with a website of their own")
    platforms = collections.Counter((dealer["platform"] or "unknown", dealer["reads"] or "untested") for dealer in with_site)
    for (platform, reads), count in platforms.most_common():
        print(f"  {count:3d}  {platform:<16} {reads}")
    dead = [dealer["host"] for dealer in with_site if not dealer["resolves"]]
    if dead:
        print("  hosts that do not resolve:", ", ".join(dead))


if __name__ == "__main__":
    main()
