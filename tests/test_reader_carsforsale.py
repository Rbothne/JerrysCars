import pathlib
import unittest

from cartrack import readers
from cartrack.readers import carsforsale

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from ezautomemphis.net, 2026-11-21 (count edited to 3)
SEEN = "2026-11-21T06:00"
BASE = "https://www.ezautomemphis.net/cars-for-sale"


def answers(table=None):
    table = table or {BASE: "carsforsale_page1.html", BASE + "?Paging.Page=2": "carsforsale_page2.html",
                      BASE + "?Paging.Page=3": "carsforsale_page3.html"}
    asked = []

    def get(url, headers=None, **options):
        asked.append((url, headers or {}))
        answer = table[url]
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


class Carsforsale(unittest.TestCase):
    DEALER = {"host": "ezautomemphis.net", "website": "https://www.ezautomemphis.net/", "name": "E Z Auto",
              "city": "Memphis", "state": "TN", "zip": None, "lat": None, "lon": None}

    def read(self, get=None):
        self.get = get or answers()
        return carsforsale.read(self.DEALER, self.get, SEEN)

    def test_reads_numbered_pages_until_the_stated_count_is_reached(self):
        found, complete = self.read()
        self.assertEqual([url for url, _ in self.get.asked], [BASE, BASE + "?Paging.Page=2"])
        self.assertEqual(len(found), 3)
        self.assertTrue(complete)

    def test_sends_a_user_agent_without_python_urllib_which_the_platform_answers_with_500(self):
        self.read()
        for _, headers in self.get.asked:
            self.assertNotIn("python-urllib", headers["User-Agent"].lower())

    def test_reads_the_real_f150(self):
        truck = self.read()[0][0]
        self.assertEqual(truck["id"], "ezautomemphis.net:a85bda32-575a-48b5-9d72-2fcbba9b2a3c")
        self.assertEqual((truck["year"], truck["make"], truck["model"], truck["trim"]), (2009, "ford", "F-150", "Lariat"))
        self.assertEqual((truck["price"], truck["miles"], truck["vin"], truck["drive"]),
                         (10990, 153922, "1FTPW12V49FA08611", "rwd"))
        self.assertEqual((truck["color"], truck["transmission"], truck["fuel"], truck["body"]),
                         ("Oxford White Clearcoat", "6-speed automatic", "flex fuel", "pickup"))
        self.assertEqual(truck["url"], "https://www.ezautomemphis.net/Inventory/Details/a85bda32-575a-48b5-9d72-2fcbba9b2a3c")
        self.assertEqual(truck["title"], "2009 Ford F-150 Lariat")
        self.assertTrue(truck["photos"][0].startswith("https://cdn05.carsforsale.com/00a1bb9b3aad98904e8da332496baa2012/"))

    def test_fewer_cars_than_the_page_states_is_not_a_whole_read(self):
        found, complete = self.read(answers({BASE: "carsforsale_page1.html", BASE + "?Paging.Page=2": "carsforsale_page3.html"}))
        self.assertEqual(len(found), 2)
        self.assertFalse(complete)

    def test_a_page_with_no_cars_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read(answers({BASE: b"<html><body>500 Internal Server Error</body></html>"}))


if __name__ == "__main__":
    unittest.main()
