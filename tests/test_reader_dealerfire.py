import pathlib
import re
import unittest

from cartrack import readers
from cartrack.readers import dealerfire

FIXTURES = pathlib.Path(__file__).parent / "fixtures"      # cut from jr-autosales.com, 2026-11-21
SEEN = "2026-11-21T07:00"


def pages(table):
    """A `get` that answers from `table` ({address: fixture file name or bytes}) and remembers what was asked."""
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table[url]
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


class DealerFire(unittest.TestCase):
    DEALER = {"host": "jr-autosales.com", "website": "https://www.jr-autosales.com/", "name": "JR's Auto Sales",
              "city": "Memphis", "state": "TN", "zip": None, "lat": None, "lon": None}
    FIRST = "https://www.jr-autosales.com/inventory?isNew=0&limit=100&offset=0"

    def read(self, table=None):
        self.get = pages(table or {self.FIRST: "dealerfire_used.html"})
        return dealerfire.read(self.DEALER, self.get, SEEN)

    def by_id(self, found):
        return {listing["source_id"]: listing for listing in found}

    def test_asks_the_platforms_own_used_inventory_address_once(self):
        self.read()
        self.assertEqual(self.get.asked, [self.FIRST])

    def test_reads_the_real_rogue(self):
        found, complete = self.read()
        rogue = self.by_id(found)["66672578"]
        self.assertEqual(rogue["id"], "jr-autosales.com:66672578")
        self.assertEqual((rogue["year"], rogue["make"], rogue["model"], rogue["trim"]), (2019, "nissan", "Rogue", "SV"))
        self.assertEqual((rogue["vin"], rogue["miles"], rogue["price"], rogue["drive"]), ("KNMAT2MT2KP525342", 175572, 13995, "fwd"))
        self.assertEqual(rogue["url"], "https://www.jr-autosales.com/vehicle-details/used-2019-nissan-rogue-sv-memphis-tn-id-66672578")
        self.assertEqual(rogue["title"], "2019 Nissan Rogue SV")
        self.assertEqual(rogue["posted"], "2026-11-10T00:00")
        self.assertEqual(rogue["extra"]["stock"], "7961J")
        self.assertEqual((rogue["body"], rogue["color"]), ("sport utility", "GRAY"))
        self.assertEqual(rogue["photo_count"], 7)
        self.assertTrue(rogue["photos"][0].startswith("https://cdn-ds.com/stock/2019-Nissan-Rogue-SV-Memphis-TN/"))
        self.assertTrue(complete)

    def test_the_price_figures_are_kept(self):
        rogue = self.by_id(self.read()[0])["66672578"]
        self.assertEqual(rogue["extra"]["prices"]["finalPrice"], 13995)
        self.assertEqual(rogue["extra"]["prices"]["originalPrice"], 13995)

    def test_maker_stock_art_is_not_taken_as_a_photo_of_the_car(self):
        # cdn-ds.com/chrome/... is Chrome Data's colourised stock picture; the dealer flags the car "Images Coming Soon".
        elantra = self.by_id(self.read()[0])["66672576"]
        self.assertEqual(elantra["photos"], [])
        self.assertEqual(elantra["photo_count"], 0)
        self.assertTrue(elantra["extra"]["stock_art"].startswith("https://cdn-ds.com/chrome/"))

    def test_a_zero_price_is_no_price(self):
        terrain = self.by_id(self.read()[0])["63908348"]
        self.assertIsNone(terrain["price"])
        self.assertEqual(terrain["photos"], [])

    def test_the_dealer_is_the_seller_and_the_place(self):
        rogue = self.by_id(self.read()[0])["66672578"]
        self.assertEqual((rogue["channel"], rogue["seller_type"], rogue["seller_name"], rogue["seller_id"]),
                         ("dealer_site", "dealer", "JR's Auto Sales", "jr-autosales.com"))

    def test_as_many_cars_as_the_page_counted_is_a_whole_read(self):
        found, complete = self.read()
        self.assertEqual(len(found), 3)
        self.assertTrue(complete)

    def test_later_pages_start_after_the_cars_already_given_until_the_count_is_reached(self):
        page = (FIXTURES / "dealerfire_used.html").read_text(encoding="utf-8")
        first = page.replace('data-total-items="3"', 'data-total-items="6"')
        second = re.sub(r"VehicleObject_(\d+)', \{\"vuid\":(\d+)", lambda m: f"VehicleObject_9{m[1]}', {{\"vuid\":9{m[2]}", first)
        later = "https://www.jr-autosales.com/inventory?isNew=0&limit=100&offset=3"
        found, complete = self.read({self.FIRST: first.encode(), later: second.encode()})
        self.assertEqual(self.get.asked, [self.FIRST, later])
        self.assertEqual(len(found), 6)
        self.assertTrue(complete)

    def test_a_page_that_brings_no_new_cars_ends_the_read_short_of_the_count(self):
        page = (FIXTURES / "dealerfire_used.html").read_text(encoding="utf-8")
        first = page.replace('data-total-items="3"', 'data-total-items="103"')
        later = "https://www.jr-autosales.com/inventory?isNew=0&limit=100&offset=3"
        found, complete = self.read({self.FIRST: first.encode(), later: first.encode()})   # offset ignored: page 1 again
        self.assertEqual(self.get.asked, [self.FIRST, later])
        self.assertEqual(len(found), 3)
        self.assertFalse(complete)

    def test_a_page_with_no_cars_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.FIRST: b"<html>maintenance</html>"})

class Past(unittest.TestCase):
    def test_keeps_the_history_report_and_whether_carfax_counts_one_owner(self):
        found, _ = dealerfire.read(DealerFire.DEALER, pages({DealerFire.FIRST: "dealerfire_used.html"}), SEEN)
        reports = [car["extra"] for car in found if car["extra"].get("history_url")]
        self.assertTrue(reports)
        self.assertTrue(all(extra["history_url"].startswith("https://www.carfax.com/vehiclehistory/") for extra in reports))
        self.assertIn(False, [extra.get("one_owner") for extra in reports])


if __name__ == "__main__":
    unittest.main()
