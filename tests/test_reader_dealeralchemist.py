import json
import pathlib
import unittest

from cartrack import readers
from cartrack.readers import dealeralchemist

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from cityauto.com and its search service, 2026-11-21
SEEN = "2026-11-21T06:00"
PAGE = "https://www.cityauto.com/used-vehicles/"
SEARCH = ("https://hjnrb3s21408ezpfp.a1.typesense.net/multi_search"
          "?x-typesense-api-key=eQUa8iq30l8Tu908Drz9WKqar6tCJGd4")


def answers(search=None):
    asked = []

    def get(url, data=None, headers=None, **options):
        asked.append((url, json.loads(data) if data else None, headers or {}))
        if url == PAGE:
            return (FIXTURES / "dealeralchemist_used.html").read_bytes()
        if url == SEARCH:
            body = search(json.loads(data)) if search else None
            return body or (FIXTURES / "dealeralchemist_search.json").read_bytes()
        raise AssertionError(f"unexpected address {url}")
    get.asked = asked
    return get


class DealerAlchemist(unittest.TestCase):
    DEALER = {"host": "cityauto.com", "website": "https://www.cityauto.com/", "name": "City Auto",
              "city": "Memphis", "state": "TN", "zip": None, "lat": None, "lon": None}

    def read(self, get=None, dealer=None):
        self.get = get or answers()
        return dealeralchemist.read(dealer or self.DEALER, self.get, SEEN)

    def test_learns_the_search_service_from_the_used_page_then_asks_it_for_used_cars(self):
        self.read()
        self.assertEqual([url for url, _, _ in self.get.asked], [PAGE, SEARCH])
        search = self.get.asked[1][1]["searches"][0]
        self.assertEqual((search["collection"], search["q"], search["filter_by"], search["per_page"], search["page"]),
                         ("vehicles-GRP00028", "*", "condition:Used", 250, 1))

    def test_reads_the_real_x1(self):
        x1 = self.read()[0][0]
        self.assertEqual(x1["id"], "cityauto.com:WBX73EF02P5X53474")
        self.assertEqual((x1["year"], x1["make"], x1["model"], x1["trim"]), (2023, "bmw", "X1", "xDrive28i"))
        self.assertEqual((x1["vin"], x1["miles"], x1["drive"]), ("WBX73EF02P5X53474", 31102, "awd"))
        self.assertEqual(x1["url"], "https://www.cityauto.com/vehicle/Used/2023/BMW/X1/WBX73EF02P5X53474/")
        self.assertEqual(x1["title"], "2023 BMW X1 xDrive28i")
        self.assertEqual(x1["extra"]["stock"], "520797")
        self.assertTrue(x1["photos"][0].startswith("https://dealerslink.s3.amazonaws.com/vehicles/5832/520797-"))

    def test_the_asking_price_is_the_internet_price_without_the_processing_fee(self):
        x1 = self.read()[0][0]
        self.assertEqual(x1["price"], 29717)
        self.assertEqual(x1["extra"]["shown_price"], 30712)
        self.assertEqual(x1["extra"]["fees"], {"Processing Fee": 995})

    def test_days_on_the_lot_give_the_stock_date(self):
        self.assertEqual(self.read()[0][0]["posted"], "2026-11-17T00:00")    # age 4 on 2026-11-21

    def test_a_car_with_no_price_has_none(self):
        ram = self.read()[0][1]
        self.assertEqual(ram["vin"], "1C6RRFFG7KN862360")
        self.assertIsNone(ram["price"])

    def test_only_the_lots_in_the_dealers_own_city_are_kept(self):
        found, complete = self.read()
        self.assertEqual([car["vin"] for car in found], ["WBX73EF02P5X53474", "1C6RRFFG7KN862360"])
        self.assertTrue(complete)
        self.assertEqual(found[0]["extra"]["lot"], "City Auto Memphis")

    def test_a_dealer_with_no_city_keeps_every_lot(self):
        self.assertEqual(len(self.read(dealer={**self.DEALER, "city": None})[0]), 3)

    def test_a_city_with_none_of_the_groups_lots_is_an_error_not_an_empty_lot(self):
        with self.assertRaises(readers.NotRead):
            self.read(dealer={**self.DEALER, "city": "Nashville"})

    def test_every_page_the_service_counts_is_read(self):
        real = json.loads((FIXTURES / "dealeralchemist_search.json").read_text(encoding="utf-8"))

        def search(asked):
            answer = json.loads(json.dumps(real))
            answer["results"][0]["found"] = 251 + 2      # one full page, then the rest
            answer["results"][0]["page"] = asked["searches"][0]["page"]
            return json.dumps(answer).encode()
        found, complete = self.read(answers(search))
        self.assertEqual([body["searches"][0]["page"] for _, body, _ in self.get.asked[1:]], [1, 2])
        self.assertFalse(complete)                         # 6 cars read where 253 were counted

    def test_a_page_without_the_search_settings_is_an_error(self):
        get = answers()
        with self.assertRaises(readers.NotRead):
            dealeralchemist.read(self.DEALER, lambda url, **o: b"<html>maintenance</html>" if url == PAGE else get(url, **o), SEEN)


if __name__ == "__main__":
    unittest.main()
