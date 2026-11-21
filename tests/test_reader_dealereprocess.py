import pathlib
import unittest

from cartrack import readers
from cartrack.readers import dealereprocess

FIXTURES = pathlib.Path(__file__).parent / "fixtures"   # cut from real Dealer eProcess search pages, 2026-11-21
SEEN = "2026-11-21T06:00"


def pages(table):
    """A `get` that answers from `table` ({address: fixture file name or bytes}) and remembers what was asked."""
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table[url]
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


def page(name, page_count=None, count=None, old_pages=None, old_count=None):
    """A fixture with its pager's page count and its results count changed."""
    body = (FIXTURES / name).read_text(encoding="utf-8")
    if page_count is not None:
        body = body.replace(f"var page_count = {old_pages};", f"var page_count = {page_count};")
    if count is not None:
        body = body.replace(f'data-vehicle_count="{old_count}"', f'data-vehicle_count="{count}"')
    return body.encode()


class Landers(unittest.TestCase):
    DEALER = {"host": "landersused.com", "website": "https://www.landersused.com/", "name": "Landers Used",
              "city": "Southaven", "state": "MS", "zip": None, "lat": None, "lon": None}
    SEARCH = "https://www.landersused.com/search/used/?ct=48&p={}&tp=used"
    FIXTURE = "dealereprocess_landers_srp.html"

    def one_page(self, count=3):
        return page(self.FIXTURE, page_count=1, count=count, old_pages=16, old_count=764)

    def read(self, table=None):
        self.get = pages(table or {self.SEARCH.format(1): self.one_page()})
        found, complete = dealereprocess.read(self.DEALER, self.get, SEEN)
        self.cars = {car["vin"]: car for car in found}
        return found, complete

    def test_asks_the_used_search_48_cars_a_page(self):
        self.read()
        self.assertEqual(self.get.asked, [self.SEARCH.format(1)])

    def test_reads_the_real_malibu(self):
        found, complete = self.read()
        malibu = self.cars["1G1ZH57B394261898"]
        self.assertEqual(malibu["id"], "landersused.com:1G1ZH57B394261898")
        self.assertEqual((malibu["year"], malibu["make"], malibu["model"], malibu["trim"]),
                         (2009, "chevrolet", "Malibu", "LT w/1LT"))
        self.assertEqual((malibu["miles"], malibu["body"], malibu["drive"], malibu["color"]),
                         (222383, "4dr car", "fwd", "Dark Gray Metallic"))
        self.assertEqual((malibu["engine"], malibu["transmission"], malibu["fuel"]),
                         ("gas 4-cyl 2.4l/146.5", "6-speed automatic w/od", "gasoline"))
        self.assertEqual(malibu["url"], "https://www.landersused.com/auto/used-2009-chevrolet-malibu-lt-w1lt/127078461/")
        self.assertEqual(malibu["title"], "2009 Chevrolet Malibu LT w/1LT")
        self.assertEqual(malibu["posted"], "2026-10-22T00:00")
        self.assertEqual(malibu["extra"]["stock"], "A05151A")
        self.assertEqual(malibu["extra"]["vehicle_id"], "127078461")
        self.assertEqual(malibu["extra"]["location"], "Landers Auto Sales Mississippi")
        self.assertTrue(complete)

    def test_the_price_is_before_the_processing_fee_and_the_stack_is_kept(self):
        self.read()
        malibu = self.cars["1G1ZH57B394261898"]
        self.assertEqual(malibu["price"], 4988)
        self.assertEqual(malibu["extra"]["prices"], {"Internet Price": 4988, "Processing Fee": 425, "Landers Price": 5413})
        self.assertEqual((malibu["extra"]["price_all_in"], malibu["extra"]["fees"]), (5413, 425))

    def test_call_for_price_is_no_price_not_the_fee(self):
        # The page's JSON-LD offer says "425" for these cars: that is the processing fee alone.
        self.read()
        sierra = self.cars["1GTPHDED1TZ226011"]
        self.assertIsNone(sierra["price"])
        self.assertEqual(sierra["extra"]["price_note"], "Call for Price")
        self.assertNotIn("price_all_in", sierra["extra"])

    def test_the_photo_is_the_cars_own_and_placeholders_are_not_photos(self):
        self.read()
        silverado = self.cars["3GCUKSEC3EG510727"]
        self.assertEqual(silverado["photos"], [
            "https://cloudflareimages.dealereprocess.com/resrc/images/c_limit,fl_lossy,w_auto/v1/dvp/1645/56891807772/"
            "Used-2014-Chevrolet-Silverado1500-LTZ-ID56891807772-aHR0cDovL2ltYWdlcy51bml0c2ludmVudG9yeS5jb20vdXBsb2Fkcy9w"
            "aG90b3MvMC8yMDI2LTEwLTA1LzEtMjE3OTkwNzAtNmFjM2M1MDFiYzgwNS5qcGc="])
        self.assertEqual(silverado["photo_count"], 2)
        self.assertEqual(self.cars["1G1ZH57B394261898"]["photos"], [])      # a make logo in place of a photo
        self.assertEqual(self.cars["1GTPHDED1TZ226011"]["photos"], [])      # a maker's stock render
        self.assertEqual(self.cars["1GTPHDED1TZ226011"]["photo_count"], 0)

    def test_a_car_at_another_rooftop_is_named_from_the_location_menu(self):
        # landersused.com lists ten Landers stores; the car data names only one, the menu names them all.
        body = page("dealereprocess_landers_p5.html", page_count=1, count=1, old_pages=16, old_count=764)
        self.read({self.SEARCH.format(1): body})
        taurus = self.cars["1FAHP2FW9BG115931"]
        self.assertEqual((taurus["extra"]["location"], taurus["extra"]["location_id"]), ("ELanders Buick GMC", "4877"))
        self.assertEqual(taurus["price"], 4855)

    def test_the_dealer_is_the_seller_and_the_place(self):
        self.read()
        malibu = self.cars["1G1ZH57B394261898"]
        self.assertEqual((malibu["channel"], malibu["seller_type"], malibu["seller_name"], malibu["seller_id"]),
                         ("dealer_site", "dealer", "Landers Used", "landersused.com"))
        self.assertEqual((malibu["city"], malibu["state"]), ("Southaven", "MS"))

    def test_every_page_the_pager_counts_is_read_and_a_car_seen_twice_counts_once(self):
        body = page(self.FIXTURE, page_count=3, count=3, old_pages=16, old_count=764)
        found, complete = self.read({self.SEARCH.format(n): body for n in (1, 2, 3)})
        self.assertEqual(self.get.asked, [self.SEARCH.format(n) for n in (1, 2, 3)])
        self.assertEqual(len(found), 3)
        self.assertTrue(complete)

    def test_fewer_cars_than_the_site_counted_is_not_a_whole_read(self):
        found, complete = self.read({self.SEARCH.format(1): self.one_page(count=764)})
        self.assertEqual(len(found), 3)
        self.assertFalse(complete)

    def test_paging_stops_at_the_limit(self):
        body = page(self.FIXTURE, page_count=500, count=764, old_pages=16, old_count=764)
        table = {self.SEARCH.format(n): body for n in range(1, dealereprocess.MAX_PAGES + 1)}
        found, complete = self.read(table)
        self.assertEqual(len(self.get.asked), dealereprocess.MAX_PAGES)
        self.assertFalse(complete)

    def test_the_cloudflare_challenge_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.SEARCH.format(1): b"<!DOCTYPE html><html><head><title>Just a moment...</title></head></html>"})

    def test_a_dealer_without_a_website_is_asked_at_www(self):
        dealer = {**self.DEALER, "website": None}
        get = pages({self.SEARCH.format(1): self.one_page()})
        dealereprocess.read(dealer, get, SEEN)
        self.assertEqual(get.asked, [self.SEARCH.format(1)])


class Clearance(unittest.TestCase):
    """The site answers a plain request only with the browser's cf_clearance cookie and its exact user agent."""
    SAVED = {"host": "www.landersused.com", "minted": "2026-11-21T06:16:42Z", "cookie": "cf_clearance=abc",
             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/157.0.0.0"}

    def setUp(self):
        self.calls = []
        self.get = dealereprocess.with_clearance(lambda url, **options: self.calls.append((url, options)) or b"",
                                                 {"www.landersused.com": self.SAVED})

    def test_a_cleared_host_gets_the_cookie_and_the_browsers_user_agent(self):
        self.get("https://www.landersused.com/search/used/?ct=48&p=1&tp=used")
        headers = self.calls[0][1]["headers"]
        self.assertEqual((headers["Cookie"], headers["User-Agent"]), ("cf_clearance=abc", self.SAVED["user_agent"]))
        self.assertTrue(headers["Accept"].startswith("text/html"))

    def test_other_hosts_are_asked_as_before(self):
        self.get("https://www.jimkerasnissan.com/searchused.aspx", headers={"Accept": "application/json"})
        self.assertEqual(self.calls[0], ("https://www.jimkerasnissan.com/searchused.aspx", {"headers": {"Accept": "application/json"}}))

    def test_saved_clearances_are_read_from_a_folder_by_host(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            (pathlib.Path(folder) / "landersused.json").write_text(json.dumps(self.SAVED), encoding="utf-8")
            (pathlib.Path(folder) / "notes.txt").write_text("not a clearance", encoding="utf-8")
            self.assertEqual(dealereprocess.load_clearances(folder), {"www.landersused.com": self.SAVED})
        self.assertEqual(dealereprocess.load_clearances(pathlib.Path(folder) / "missing"), {})


class OtherSites(unittest.TestCase):
    """The same reader on Dealer eProcess sites elsewhere: Pohanka (Virginia), Antwerpen's Jack Says Yes
    (Maryland) and Radley (Virginia, no used cars listed)."""

    def read(self, host, fixture, pages_were, count_was, count):
        dealer = {"host": host, "website": f"https://www.{host}/", "name": host, "city": None, "state": None}
        body = page(fixture, page_count=1, count=count, old_pages=pages_were, old_count=count_was)
        get = pages({f"https://www.{host}/search/used/?ct=48&p=1&tp=used": body})
        found, complete = dealereprocess.read(dealer, get, SEEN)
        return {car["vin"]: car for car in found}, complete

    def test_pohanka_price_is_after_the_discount_and_before_the_fee(self):
        cars, complete = self.read("pohanka.com", "dealereprocess_pohanka_srp.html", 46, 2161, 2)
        lexus = cars["JTHAP1D24R5006805"]
        self.assertEqual(lexus["price"], 73900)
        self.assertEqual(lexus["extra"]["prices"],
                         {"Retail Price": 76900, "Savings": -3000, "Processing Fee": 989, "Price": 74889})
        self.assertEqual((lexus["extra"]["price_all_in"], lexus["extra"]["fees"]), (74889, 989))
        self.assertEqual((lexus["year"], lexus["make"], lexus["model"], lexus["trim"]),
                         (2024, "lexus", "IS 500", "F SPORT Performance Premium"))
        self.assertEqual((lexus["miles"], lexus["drive"], lexus["posted"]), (13506, "rwd", "2026-05-13T00:00"))
        self.assertTrue(lexus["extra"]["certified"])
        self.assertEqual(lexus["extra"]["location"], "Pohanka Lexus")
        self.assertEqual(cars["W1N4M4HB7SW407115"]["price"], 36233)
        self.assertTrue(complete)

    def test_jack_says_yes_cards_and_documentation_fee(self):
        cars, complete = self.read("jacksaysyes.com", "dealereprocess_jacksaysyes_srp.html", 11, 527, 2)
        altima = cars["1N4BL4DV8RN324459"]
        self.assertEqual(altima["price"], 16980)
        self.assertEqual(altima["extra"]["prices"],
                         {"Retail Price": 19527, "Dealer Discount": -2547, "Documentation Fee": 799,
                          "Jack Says Yes Price": 17779})
        self.assertEqual(altima["url"], "https://www.jacksaysyes.com/auto/used-2024-nissan-altima-25-sv/122616485/")
        self.assertEqual(altima["miles"], 57849)
        self.assertEqual(len(altima["photos"]), 1)
        self.assertEqual(altima["photo_count"], 27)
        self.assertIsNone(cars["JM3KFBCM1L0784718"]["fuel"])
        self.assertTrue(complete)

    def test_a_site_that_says_no_vehicles_found_is_an_empty_whole_read(self):
        dealer = {"host": "radleyauto.com", "website": "https://www.radleyauto.com/", "name": "Radley"}
        get = pages({"https://www.radleyauto.com/search/used/?ct=48&p=1&tp=used": "dealereprocess_radley_none.html"})
        self.assertEqual(dealereprocess.read(dealer, get, SEEN), ([], True))


if __name__ == "__main__":
    unittest.main()
