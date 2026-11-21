import json
import pathlib
import unittest

from cartrack.readers import NotRead
from cartrack.readers import carvana

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from apik.carvana.io answers for ZIP 38103, 2026-11-21
SEEN = "2026-11-21T05:00"
DEALER = {"host": "carvana.com", "website": "https://carvana.com", "name": "Carvana", "city": "Memphis",
          "state": "TN", "zip": "38133", "lat": 35.1819, "lon": -89.82339}
SEARCH = "https://apik.carvana.io/merch/search/api/v2/search"
DISTANCE = "https://apik.carvana.io/merch/carvanamerchcontextapi/api/v3/distance?zip5=38103"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class Site:
    """A `get` that answers the distance service from the fixture and each search page from `pages`
    ({page number: payload}), and remembers every request."""

    def __init__(self, pages=None):
        self.pages = pages or {1: fixture("carvana_search.json")}
        self.asked = []

    def __call__(self, url, **options):
        body = json.loads(options["data"]) if options.get("data") is not None else None
        self.asked.append((url, body, options.get("headers") or {}))
        if url == DISTANCE:
            return (FIXTURES / "carvana_distance.json").read_bytes()
        if url == SEARCH:
            return json.dumps(self.pages[body["pagination"]["page"]]).encode()
        raise AssertionError(f"unexpected request {url}")


def paged(total, sizes):
    """Real cars from the fixture, repeated under new ids, as search pages of the given sizes."""
    car = fixture("carvana_search.json")["inventory"]["vehicles"][0]
    pages, number = {}, 0
    for page, size in enumerate(sizes, 1):
        cars = []
        for _ in range(size):
            number += 1
            cars.append({**car, "vehicleId": 5000000 + number, "vin": None})
        pages[page] = {"inventory": {"pagination": {"currentPage": page, "pageSize": 100, "totalMatchedInventory": total,
                                                    "totalMatchedPages": -(-total // 100)}, "vehicles": cars}}
    return pages


class Carvana(unittest.TestCase):
    def read(self, pages=None):
        self.get = Site(pages)
        return carvana.read(DEALER, self.get, SEEN)

    def test_asks_the_distance_service_then_posts_the_free_delivery_search_for_memphis(self):
        self.read()
        (first, _, _), (second, body, headers) = self.get.asked
        self.assertEqual(first, DISTANCE)
        self.assertEqual(second, SEARCH)
        self.assertEqual(body["zip5"], "38103")
        self.assertEqual(body["filters"], {"isFreeDelivery": True})
        self.assertEqual(body["pagination"], {"page": 1, "pageSize": 100})
        self.assertEqual(headers["Content-Type"], "application/json")

    def test_reads_the_real_mustang(self):
        mustang = self.read()[0][0]
        self.assertEqual(mustang["id"], "carvana.com:4895072")
        self.assertEqual((mustang["year"], mustang["make"], mustang["model"], mustang["trim"]), (2010, "ford", "Mustang", "base"))
        self.assertEqual((mustang["vin"], mustang["miles"], mustang["body"], mustang["color"], mustang["fuel"]),
                         ("1ZVBP8AN9A5146816", 87061, "coupe", "Blue", "gas"))
        self.assertEqual(mustang["url"], "https://www.carvana.com/vehicle/4895072")
        self.assertEqual(mustang["title"], "2010 Ford Mustang base")

    def test_the_asking_price_is_the_total_and_shipping_is_kept_apart(self):
        mustang = self.read()[0][0]
        self.assertEqual(mustang["price"], 13990)
        self.assertEqual(mustang["extra"]["shipping"], 0)
        self.assertEqual((mustang["extra"]["kbb"], mustang["extra"]["msrp"]), (9985, 22840))
        self.assertEqual(mustang["extra"]["stock"], 3006972015)

    def test_the_photo_is_the_tiles_own_on_carvanas_image_host(self):
        self.assertEqual(self.read()[0][0]["photos"],
                         ["https://cdnblob.fastly.carvana.io/3006972015/post-large/normalized/zoomcrop/"
                          "3006972015-edc-02.jpg?v=2026.11.21_6.16.2"])

    def test_carvana_is_the_seller_and_the_car_is_where_carvana_keeps_it(self):
        mustang = self.read()[0][0]
        self.assertEqual((mustang["channel"], mustang["seller_type"], mustang["seller_id"], mustang["seller_name"]),
                         ("dealer_site", "dealer", "carvana.com", "Carvana"))
        self.assertEqual((mustang["city"], mustang["state"], mustang["zip"]), ("West Memphis", "AR", "72301"))
        self.assertEqual((mustang["extra"]["location_id"], mustang["extra"]["location_miles"]), (131, 9))

    def test_a_car_shipped_free_from_nashville_says_so(self):
        gladiator = self.read()[0][1]
        self.assertEqual(gladiator["vin"], "1C6PJTAGXSL506209")
        self.assertEqual((gladiator["city"], gladiator["state"]), ("Old Hickory", "TN"))
        self.assertEqual((gladiator["extra"]["location_id"], gladiator["extra"]["location_miles"]), (294, 205))

    def test_a_car_kept_at_a_place_not_yet_named_has_its_distance_but_no_town(self):
        payload = fixture("carvana_search.json")
        payload["inventory"]["vehicles"][0]["locationId"] = 328
        car = self.read({1: payload})[0][0]
        self.assertIsNone(car["city"])
        self.assertEqual(car["extra"]["location_miles"], 118)

    def test_a_car_still_being_readied_is_marked_reservable(self):
        found = self.read()[0]
        self.assertEqual([car["extra"]["reservable"] for car in found], [False, False, True])

    def test_as_many_cars_as_the_service_counted_is_a_whole_read(self):
        found, complete = self.read()
        self.assertEqual(len(found), 3)
        self.assertTrue(complete)

    def test_every_page_the_service_says_exists_is_read(self):
        found, complete = self.read(paged(250, [100, 100, 50]))
        self.assertEqual([body["pagination"]["page"] for url, body, _ in self.get.asked if url == SEARCH], [1, 2, 3])
        self.assertEqual(len(found), 250)
        self.assertTrue(complete)

    def test_a_short_page_before_the_last_is_not_a_whole_read(self):
        # Asked for more than it serves, the service sends 24 cars and still counts pages at the size asked.
        found, complete = self.read(paged(250, [100, 24, 50]))
        self.assertFalse(complete)

    def test_fewer_cars_than_the_service_counted_is_not_a_whole_read(self):
        payload = fixture("carvana_search.json")
        payload["inventory"]["pagination"]["totalMatchedInventory"] = 9
        self.assertFalse(self.read({1: payload})[1])

    def test_an_answer_without_an_inventory_is_an_error(self):
        with self.assertRaises(NotRead):
            self.read({1: {"error": {"code": "UnsupportedApiVersion"}}})

class Warranty(unittest.TestCase):
    def test_keeps_what_is_left_of_the_makers_warranty(self):
        found, _ = carvana.read(DEALER, Site(None), SEEN)
        left = [car["extra"].get("warranty") for car in found]
        self.assertIn({"basic": [15, 24500], "drivetrain": [39, 48500]}, left)
        self.assertIsNone(left[0])                       # the 2010 car has none left


if __name__ == "__main__":
    unittest.main()
