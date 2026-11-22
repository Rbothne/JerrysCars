import pathlib
import unittest

from cartrack.readers import NotRead
from cartrack.sources import offerup

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from offerup.com's Memphis pages, 2026-11-21
SEEN = "2026-11-22T05:00"
PLACE = {"key": "offerup.com/memphis-tn", "kind": "offerup", "site": "memphis-tn", "name": "OfferUp: Memphis"}
BASE = "https://offerup.com/c/cars-and-trucks/in/memphis-tn"
PAGES = {BASE: "offerup_memphis_p1.html", BASE + "?page=2": "offerup_memphis_p2.html", BASE + "?page=3": "offerup_memphis_p3.html"}


def answers(table=None):
    table = {**PAGES, **(table or {})}
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table[url]
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


class OfferUp(unittest.TestCase):
    def read(self, table=None):
        self.get = answers(table)
        found, complete = offerup.read(PLACE, self.get, SEEN)
        self.cars = {car["title"]: car for car in found}
        return found, complete

    def test_reads_page_after_page_until_one_comes_back_empty(self):
        found, complete = self.read()
        self.assertEqual(self.get.asked, [BASE, BASE + "?page=2", BASE + "?page=3"])
        self.assertEqual(sorted(self.cars), ["2007 BMW X5", "2011 Hyundai Sonata", "2012 Toyota Camry",
                                             "2015 Infiniti Q70l", "2021 Ford Bronco", "2024 Ford Escape"])
        self.assertEqual((len(found), complete), (6, True))     # the BMW was on both pages; the advert is no car

    def test_reads_the_real_bmw(self):
        self.read()
        bmw = self.cars["2007 BMW X5"]
        self.assertEqual(bmw["id"], "offerup.com/memphis-tn:fd765a56-2237-3251-aa78-6827b289542e")
        self.assertEqual(bmw["url"], "https://offerup.com/item/detail/fd765a56-2237-3251-aa78-6827b289542e")
        self.assertEqual((bmw["channel"], bmw["price"], bmw["price_kind"]), ("marketplace", 5000, "ask"))
        self.assertEqual((bmw["year"], bmw["make"], bmw["miles"], bmw["city"], bmw["state"]), (2007, None, 141912, "Memphis", "TN"))
        self.assertEqual(bmw["extra"], {"makemodel": "BMW X5", "seller_guessed": True, "tile": "LISTING"})
        self.assertTrue(bmw["photos"][0].startswith("https://images.offerup.com/"))

    def test_the_seller_is_guessed_from_the_tile_and_how_the_price_is_written(self):
        self.read()
        self.assertEqual({title: car["seller_type"] for title, car in self.cars.items()},
                         {"2021 Ford Bronco": "dealer",          # $36,740: whole dollars, not a round fifty
                          "2024 Ford Escape": "dealer",          # a paid seller tile
                          "2012 Toyota Camry": "dealer",         # $10,995.00: a lot's price
                          "2007 BMW X5": "private", "2015 Infiniti Q70l": "private", "2011 Hyundai Sonata": "private"})

    def test_a_price_with_cents_that_is_round_says_nothing_of_the_seller(self):
        round_cents = (FIXTURES / "offerup_memphis_p1.html").read_bytes().replace(b'"10995.00"', b'"3000.00"')
        self.read({BASE: round_cents})
        self.assertIsNone(self.cars["2012 Toyota Camry"]["seller_type"])

    def test_a_card_with_no_mileage_has_none(self):
        self.read()
        self.assertIsNone(self.cars["2011 Hyundai Sonata"]["miles"])

    def test_a_page_that_repeats_the_last_brings_the_read_to_an_end_and_it_is_not_whole(self):
        found, complete = self.read({BASE + "?page=2": "offerup_memphis_p1.html", BASE + "?page=3": "offerup_memphis_p1.html"})
        self.assertEqual(self.get.asked, [BASE, BASE + "?page=2"])
        self.assertFalse(complete)

    def test_a_page_without_its_data_is_not_read(self):
        with self.assertRaises(NotRead):
            self.read({BASE: b"<html><body>Just a moment...</body></html>"})


if __name__ == "__main__":
    unittest.main()
