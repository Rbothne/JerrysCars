import json
import pathlib
import unittest

from cartrack import readers
from cartrack.readers import teamvelocity

FIXTURES = pathlib.Path(__file__).parent / "fixtures"      # cut from gossettmotorcars.net, 2026-11-21
SEEN = "2026-11-21T07:00"


def pages(table):
    """A `get` that answers from `table` ({address: fixture name, bytes or an exception}) and remembers
    each address and the headers it was asked with."""
    asked, headers = [], []

    def get(url, **options):
        asked.append(url)
        headers.append(options.get("headers") or {})
        answer = table[url]
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked, get.headers = asked, headers
    return get


def feed(**changes):
    payload = json.loads((FIXTURES / "teamvelocity_feed.json").read_text(encoding="utf-8"))
    payload.update(changes)
    return payload


class TeamVelocity(unittest.TestCase):
    DEALER = {"host": "gossettmotorcars.net", "website": "https://gossettmotorcars.net/",
              "name": "Gossett Motor Cars (used)", "city": "Memphis", "state": "TN", "zip": None, "lat": None, "lon": None}
    FEED = "https://gossettmotorcars.net/inventory-used.json"
    SRP = "https://gossettmotorcars.net/inventory/used?limit=3"

    def read(self, table=None):
        self.get = pages(table or {self.FEED: "teamvelocity_feed.json", self.SRP: "teamvelocity_srp.html"})
        return teamvelocity.read(self.DEALER, self.get, SEEN)

    def by_vin(self, found):
        return {listing["vin"]: listing for listing in found}

    def test_reads_the_feed_then_one_search_page_holding_every_car_for_the_photos(self):
        self.read()
        self.assertEqual(self.get.asked, [self.FEED, self.SRP])

    def test_every_request_names_the_tracker_in_a_user_agent_the_edge_accepts(self):
        # The Fastly edge answers 406 to a user agent without "Mozilla/5.0" whenever its cache misses.
        self.read()
        for headers in self.get.headers:
            self.assertTrue(headers["User-Agent"].startswith("Mozilla/5.0 (compatible; cartrack/"))

    def test_reads_the_real_terrain(self):
        found, complete = self.read()
        terrain = self.by_vin(found)["2GKALREK9E6296696"]
        self.assertEqual(terrain["id"], "gossettmotorcars.net:2GKALREK9E6296696")
        self.assertEqual((terrain["year"], terrain["make"], terrain["model"], terrain["trim"]), (2014, "gmc", "Terrain", "SLE"))
        self.assertEqual((terrain["miles"], terrain["drive"], terrain["color"], terrain["body"]),
                         (149000, "fwd", "Ashen Gray Metallic", "sport utility"))
        self.assertEqual(terrain["title"], "2014 GMC Terrain SLE")
        self.assertEqual(terrain["url"], "https://gossettmotorcars.net/viewdetails/used/2gkalrek9e6296696/2014-gmc-terrain-sport-utility")
        self.assertEqual(terrain["extra"]["stock"], "E6296696A")
        self.assertTrue(complete)

    def test_the_asking_price_is_the_feeds_selling_price_and_the_pages_fee_inclusive_figure_is_kept_aside(self):
        # The CDJR site shows this Kia-store car as "Your Price $5,894" = $4,995 plus a $899 doc fee.
        terrain = self.by_vin(self.read()[0])["2GKALREK9E6296696"]
        self.assertEqual(terrain["price"], 4995)
        self.assertEqual(terrain["extra"]["page_price"], 5894)

    def test_a_car_the_feed_leaves_unpriced_takes_the_price_its_page_shows(self):
        encore = self.by_vin(self.read()[0])["KL4CJCSB0JB523965"]
        self.assertEqual(encore["price"], 13991)
        self.assertEqual(encore["extra"]["page_price"], 13991)

    def test_the_stock_date_is_the_feeds_date_in_stock(self):
        cars = self.by_vin(self.read()[0])
        self.assertEqual(cars["KL4CJCSB0JB523965"]["posted"], "2026-11-14T00:00")
        self.assertIsNone(cars["2GKALREK9E6296696"]["posted"])

    def test_the_photo_is_the_search_pages_picture_of_that_car(self):
        mdx = self.by_vin(self.read()[0])["5FRYD3H4XGB014773"]
        self.assertEqual(len(mdx["photos"]), 1)
        self.assertTrue(mdx["photos"][0].startswith("https://content.homenetiol.com/"))

    def test_each_car_is_sold_by_the_group_store_the_feed_names(self):
        cars = self.by_vin(self.read()[0])
        self.assertEqual(cars["2GKALREK9E6296696"]["seller_name"], "Kia of Covington Pike")
        self.assertEqual(cars["5FRYD3H4XGB014773"]["seller_name"], "INFINITI of Memphis")
        self.assertEqual(cars["5FRYD3H4XGB014773"]["zip"], "38133")
        self.assertEqual(cars["5FRYD3H4XGB014773"]["seller_id"], "gossettmotorcars.net")
        self.assertEqual(cars["5FRYD3H4XGB014773"]["extra"]["store"], "INFINITI of Memphis")

    def test_every_page_the_feed_says_exists_is_read(self):
        first = feed(totalVehicles=6, totalPages=2, nextPage="/inventory-used.json?page=2")
        second = feed(page=2, totalVehicles=6, totalPages=2, nextPage=None)
        for car in second["vehicles"]:
            car["vin"] = car["vin"][:-1] + "X"
        srp = "https://gossettmotorcars.net/inventory/used?limit=6"
        found, complete = self.read({self.FEED: json.dumps(first).encode(), self.FEED + "?page=2": json.dumps(second).encode(),
                                     srp: "teamvelocity_srp.html"})
        self.assertEqual(self.get.asked, [self.FEED, self.FEED + "?page=2", srp])
        self.assertEqual(len(found), 6)
        self.assertTrue(complete)

    def test_fewer_cars_than_the_feed_counted_is_not_a_whole_read(self):
        srp = "https://gossettmotorcars.net/inventory/used?limit=9"
        found, complete = self.read({self.FEED: json.dumps(feed(totalVehicles=9)).encode(), srp: "teamvelocity_srp.html"})
        self.assertEqual(len(found), 3)
        self.assertFalse(complete)

    def test_without_the_search_page_the_cars_are_still_read_without_photos(self):
        found, complete = self.read({self.FEED: "teamvelocity_feed.json", self.SRP: OSError("timed out")})
        self.assertEqual(len(found), 3)
        self.assertTrue(all(listing["photos"] == [] for listing in found))
        self.assertTrue(complete)

    def test_a_feed_with_no_cars_is_an_error(self):
        empty = feed(totalVehicles=0, totalPages=0, vehicles=[])
        with self.assertRaises(readers.NotRead):
            self.read({self.FEED: json.dumps(empty).encode()})

    def test_an_answer_that_is_not_the_feed_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.FEED: b"<html>Not Acceptable</html>"})


if __name__ == "__main__":
    unittest.main()
