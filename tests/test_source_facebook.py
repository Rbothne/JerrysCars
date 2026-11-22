import json
import os
import unittest
from unittest import mock

from cartrack import fetch
from cartrack.readers import NotRead
from cartrack.sources import facebook

SEEN = "2026-11-22T05:00"
PLACE = {"key": "facebook.com", "kind": "facebook", "name": "Facebook Marketplace", "repo": "owner/captures", "unseen_days": 14}
FOLDER = "https://api.github.com/repos/owner/captures/contents/captures"
RAW = "https://raw.githubusercontent.com/owner/captures/main/captures/"
# Made-up captures in the form the extension writes (research/11-facebook-capture.md, section 6).
OPENED = {"id": "1234567890123456", "first_seen": "2026-11-19T14:02", "seen": "2026-11-21T22:58",
          "detail_seen": "2026-11-20T01:15", "status": "pending", "status_seen": "2026-11-21T22:58",
          "title": "2012 Honda Civic LX Sedan 4D", "price": 4500, "currency": "USD", "was": 5200, "miles": 142350,
          "miles_how": "detail", "posted": "2026-11-18T09:31", "seller_type": "private", "year": 2012, "make": "Honda",
          "model": "Civic", "vin": None, "title_status": "clean", "transmission": "AUTOMATIC", "fuel": "GASOLINE",
          "color": "Silver", "condition": "USED_GOOD", "city": "Memphis", "state": "TN", "zip": "38111", "lat": 35.11,
          "lon": -89.94, "photo": "https://scontent.example/civic.jpg"}
CARD = {"id": "222", "first_seen": "2026-11-21T20:00", "seen": "2026-11-21T20:00", "detail_seen": None, "status": "live",
        "status_seen": "2026-11-21T20:00", "title": "2009 Toyota Camry", "price": 3800, "currency": "USD", "was": None,
        "miles": 188000, "miles_how": "card", "posted": None, "seller_type": None, "year": 2009, "make": None, "model": None,
        "vin": None, "title_status": None, "transmission": None, "fuel": None, "color": None, "condition": None,
        "city": "Southaven", "state": "MS", "zip": None, "lat": None, "lon": None, "photo": None}


def captured(*rows, form=1):
    return json.dumps({"format": form, "written": "2026-11-21T23:05", "extension": "0.1.0", "horizon_days": 21,
                       "listings": list(rows)}).encode()


def folder(*names):
    return json.dumps([{"name": name, "path": f"captures/{name}", "type": "file", "download_url": RAW + name} for name in names]
                      + [{"name": "notes", "path": "captures/notes", "type": "dir", "download_url": None}]).encode()


class Facebook(unittest.TestCase):
    def read(self, files):
        """`files` is {name: body}; a body that is an exception is raised instead."""
        self.asked = []

        def get(url, headers=None, **options):
            self.asked.append((url, (headers or {}).get("Authorization")))
            answer = folder(*files) if url == FOLDER else files[url[len(RAW):]]
            if isinstance(answer, Exception):
                raise answer
            return answer
        found, complete = facebook.read(PLACE, get, SEEN)
        self.cars = {car["source_id"]: car for car in found}
        return found, complete

    def test_every_file_in_the_folder_is_read_and_it_is_never_a_whole_read(self):
        found, complete = self.read({"anna-1a2b3c4d.json": captured(OPENED), "ben-9f8e7d6c.json": captured(CARD)})
        self.assertEqual([url for url, _ in self.asked], [FOLDER, RAW + "anna-1a2b3c4d.json", RAW + "ben-9f8e7d6c.json"])
        self.assertEqual((sorted(self.cars), complete), (["1234567890123456", "222"], False))

    def test_an_opened_listing_carries_what_its_own_page_gave(self):
        self.read({"a.json": captured(OPENED)})
        civic = self.cars["1234567890123456"]
        self.assertEqual((civic["url"], civic["channel"], civic["seen"]),
                         ("https://www.facebook.com/marketplace/item/1234567890123456/", "marketplace", "2026-11-21T22:58"))
        self.assertEqual((civic["price"], civic["price_kind"], civic["miles"], civic["posted"], civic["seller_type"]),
                         (4500, "ask", 142350, "2026-11-18T09:31", "private"))
        self.assertEqual((civic["make"], civic["model"], civic["title_status"], civic["condition"], civic["zip"]),
                         ("honda", "Civic", "clean", "used good", "38111"))
        self.assertEqual(civic["extra"], {"was": 5200, "miles_how": "detail", "pending": True, "last_seen": "2026-11-21T22:58",
                                          "opened": True})

    def test_a_car_two_people_saw_is_one_car_as_last_seen_with_what_the_opener_added(self):
        later_card = {**CARD, "id": OPENED["id"], "title": OPENED["title"], "seen": "2026-11-22T01:00", "price": 4200,
                      "miles": 142000, "miles_how": "card", "status": "live"}
        self.read({"a.json": captured(OPENED), "b.json": captured(later_card)})
        civic = self.cars["1234567890123456"]
        self.assertEqual((civic["seen"], civic["price"], civic["miles"], civic["extra"]["miles_how"]),
                         ("2026-11-22T01:00", 4200, 142350, "detail"))
        self.assertEqual((civic["make"], civic["posted"], civic["city"], civic["extra"]["opened"]), ("honda", "2026-11-18T09:31", "Southaven", True))

    def test_a_card_only_listing_is_named_from_its_title_later(self):
        self.read({"a.json": captured(CARD)})
        camry = self.cars["222"]
        self.assertEqual((camry["make"], camry["extra"]["makemodel"], camry["extra"]["opened"]), (None, "Toyota Camry", False))

    def test_a_car_seen_marked_sold_says_when(self):
        self.read({"a.json": captured({**CARD, "status": "sold", "status_seen": "2026-11-21T21:00"})})
        self.assertEqual((self.cars["222"]["over"], self.cars["222"]["price_kind"]), ({"when": "2026-11-21T21:00", "how": "sold"}, "ask"))

    def test_a_row_not_seen_for_longer_than_the_place_allows_is_left_out(self):
        self.read({"a.json": captured(OPENED, {**CARD, "seen": "2026-11-01T20:00"})})
        self.assertEqual(list(self.cars), ["1234567890123456"])

    def test_no_folder_yet_is_no_listings(self):
        def get(url, **options):
            raise fetch.Gone(url)
        self.assertEqual(facebook.read(PLACE, get, SEEN), ([], False))

    def test_a_file_it_does_not_understand_is_refused(self):
        for body in (b"<html>not json</html>", captured(OPENED, form=2), json.dumps({"format": 1}).encode(),
                     captured({"id": "1"}, {"id": "2"}, OPENED)):
            with self.assertRaises(NotRead):
                self.read({"a.json": body})

    def test_a_private_repository_is_read_with_the_token_in_the_environment_and_a_public_one_without(self):
        self.read({"a.json": captured(CARD)})
        self.assertEqual({token for _, token in self.asked}, {None})
        with mock.patch.dict(os.environ, {"CAPTURES_TOKEN": "t0ken"}):
            self.read({"a.json": captured(CARD)})
        self.assertEqual({token for _, token in self.asked}, {"Bearer t0ken"})


if __name__ == "__main__":
    unittest.main()
