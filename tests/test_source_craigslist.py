import pathlib
import unittest

from cartrack import fetch
from cartrack.readers import NotRead
from cartrack.sources import craigslist

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from memphis.craigslist.org, 2026-11-21: four of 120
SEEN = "2026-11-21T21:00"                                 # results, and three listings without the sellers' words
PLACE = {"key": "memphis.craigslist.org", "kind": "craigslist", "site": "memphis", "name": "Craigslist, by owner"}
SEARCH = "https://memphis.craigslist.org/search/cto"
VIEW = "https://www.craigslist.org/view/d/"
EXPEDITION = VIEW + "memphis-2011-ford-expedition-xl/xz6FPUVRjeUCWxy7xGL77Q"
DISCOVERY = VIEW + "cordova-2017-land-rover-discovery-sport/gBzhCkQLqke86wy25xZCeW"
ACADIA = VIEW + "greenwood-2013-gmc-acadia-slt/3MNmKx9nMZJ6m82LbgMUdR"
SIERRA = VIEW + "memphis-2017-gmc-sierra-3500hd-denali/qKwY5Qp8mXrFkopbKgyAf8"
PAGES = {SEARCH: "craigslist_search.html", EXPEDITION: "craigslist_expedition.html",
         DISCOVERY: "craigslist_discovery.html", ACADIA: fetch.Gone(ACADIA), SIERRA: "craigslist_sierra.html"}


def answers(table=None):
    table = {**PAGES, **(table or {})}
    asked = []

    def get(url, headers=None, **options):
        asked.append(url)
        answer = table[url]
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


def page(name, old=None, new=None):
    text = (FIXTURES / name).read_text(encoding="utf-8")
    if old is not None:
        assert old in text, old
        text = text.replace(old, new)
    return text.encode("utf-8")


class Craigslist(unittest.TestCase):
    def read(self, table=None, known=()):
        self.get = answers(table)
        found, complete = craigslist.read(PLACE, self.get, SEEN, known=known)
        self.cars = {car["source_id"]: car for car in found}
        return found, complete

    def test_one_search_page_then_one_page_for_each_listing_not_read_before(self):
        self.read()
        self.assertEqual(self.get.asked, [SEARCH, EXPEDITION, DISCOVERY, ACADIA, SIERRA])

    def test_a_listing_taken_down_between_the_two_requests_is_left_out(self):
        found, complete = self.read()
        self.assertEqual([car["source_id"] for car in found],
                         ["xz6FPUVRjeUCWxy7xGL77Q", "gBzhCkQLqke86wy25xZCeW", "qKwY5Qp8mXrFkopbKgyAf8"])
        self.assertTrue(complete)

    def test_reads_the_real_expedition(self):
        self.read()
        suv = self.cars["xz6FPUVRjeUCWxy7xGL77Q"]
        self.assertEqual(suv["id"], "memphis.craigslist.org:xz6FPUVRjeUCWxy7xGL77Q")
        self.assertEqual((suv["title"], suv["url"], suv["price"]), ("2011 FORD EXPEDITION XL", EXPEDITION, 4000))
        self.assertEqual((suv["channel"], suv["seller_type"], suv["price_kind"]), ("classified", "private", "ask"))
        self.assertEqual((suv["year"], suv["miles"], suv["title_status"]), (2011, 180000, "clean"))
        self.assertEqual((suv["fuel"], suv["transmission"], suv["body"]), ("gas", "automatic", "suv"))
        self.assertEqual((suv["city"], suv["state"], suv["zip"]), ("Memphis", "TN", "38125"))
        self.assertEqual((suv["lat"], suv["lon"], suv["geo_how"]), (35.0312, -89.8124, "pin"))
        self.assertEqual(suv["posted"], "2026-11-21T17:10")                  # 11:10 Central, kept as UTC like `seen`
        self.assertIsNone(suv["updated"])
        self.assertEqual(len(suv["photos"]), 8)
        self.assertEqual(suv["photos"][0], "https://images.craigslist.org/00K0K_34mMtDiAmy4_0x20oM_600x450.jpg")
        self.assertEqual(suv["extra"], {"post_id": "8004309228", "makemodel": "ford expedition xl", "where": "EAST MEMPHIS"})

    def test_the_sellers_make_and_model_are_kept_as_typed_for_the_catalogue_to_name(self):
        self.read()
        suv = self.cars["xz6FPUVRjeUCWxy7xGL77Q"]
        self.assertEqual((suv["make"], suv["model"]), (None, None))
        self.assertEqual(suv["extra"]["makemodel"], "ford expedition xl")

    def test_reads_drive_colour_condition_cylinders_and_the_updated_time_where_given(self):
        self.read()
        rover, truck = self.cars["gBzhCkQLqke86wy25xZCeW"], self.cars["qKwY5Qp8mXrFkopbKgyAf8"]
        self.assertEqual((rover["drive"], rover["color"], rover["condition"]), ("fwd", "grey", "like new"))
        self.assertEqual((rover["posted"], rover["updated"]), ("2026-11-21T01:10", "2026-11-21T01:10"))
        self.assertEqual(rover["extra"]["cylinders"], 4)
        self.assertEqual((truck["drive"], truck["fuel"], truck["miles"]), ("4wd", "diesel", 74300))
        self.assertEqual(truck["extra"]["cylinders"], 8)
        self.assertNotIn("where", truck["extra"])                            # this seller named no neighbourhood

    def test_a_vin_is_read_when_the_seller_gives_one(self):
        with_vin = page("craigslist_expedition.html", '<div class="attr auto_fuel_type">',
                        '<div class="attr auto_vin">\n<span class="labl">VIN:</span>\n'
                        '<span class="valu">1FMJU1F58BEF12345</span>\n</div>\n<div class="attr auto_fuel_type">')
        self.read({EXPEDITION: with_vin})
        self.assertEqual(self.cars["xz6FPUVRjeUCWxy7xGL77Q"]["vin"], "1FMJU1F58BEF12345")

    def test_an_odometer_typed_in_thousands_on_an_old_car_is_read_as_thousands(self):
        short = page("craigslist_expedition.html", '<span class="valu">180,000</span>', '<span class="valu">180</span>')
        self.read({EXPEDITION: short})
        suv = self.cars["xz6FPUVRjeUCWxy7xGL77Q"]
        self.assertEqual((suv["miles"], suv["extra"]["odometer"]), (180000, "180"))

    def test_an_odometer_that_cannot_be_believed_either_way_is_left_blank(self):
        silly = page("craigslist_expedition.html", '<span class="valu">180,000</span>', '<span class="valu">1</span>')
        self.read({EXPEDITION: silly})
        suv = self.cars["xz6FPUVRjeUCWxy7xGL77Q"]
        self.assertEqual((suv["miles"], suv["extra"]["odometer"]), (None, "1"))

    def test_a_low_odometer_on_a_new_car_is_believed(self):
        fresh = page("craigslist_expedition.html", '<span class="valu">180,000</span>', '<span class="valu">180</span>')
        fresh = fresh.replace(b'<span class="valu year">2011</span>', b'<span class="valu year">2026</span>')
        self.read({EXPEDITION: fresh})
        self.assertEqual(self.cars["xz6FPUVRjeUCWxy7xGL77Q"]["miles"], 180)

    def test_titles_that_are_not_clean_are_named_in_the_catalogues_words(self):
        for typed, kept in (("salvage", "salvage"), ("rebuilt", "rebuilt"), ("parts only", "parts_only"),
                            ("lien", "lien"), ("missing", "missing")):
            branded = page("craigslist_expedition.html", "auto_title_status=1&amp;cat=cta\">clean<",
                           f"auto_title_status=2&amp;cat=cta\">{typed}<")
            self.read({EXPEDITION: branded})
            self.assertEqual(self.cars["xz6FPUVRjeUCWxy7xGL77Q"]["title_status"], kept)

    def test_a_listing_read_before_is_not_asked_for_again_and_gives_only_what_the_search_page_says(self):
        found, complete = self.read(known={"xz6FPUVRjeUCWxy7xGL77Q", "qKwY5Qp8mXrFkopbKgyAf8"})
        self.assertEqual(self.get.asked, [SEARCH, DISCOVERY, ACADIA])
        suv = self.cars["xz6FPUVRjeUCWxy7xGL77Q"]
        self.assertEqual((suv["title"], suv["price"], suv["url"]), ("2011 FORD EXPEDITION XL", 4000, EXPEDITION))
        self.assertEqual((suv["year"], suv["miles"], suv["posted"], suv["photos"], suv["extra"]), (None, None, None, [], {}))
        self.assertEqual(len(found), 3)                                      # the Acadia is still gone
        self.assertTrue(complete)

    def test_a_listing_page_that_fails_leaves_the_listing_in_with_what_the_search_page_says(self):
        found, complete = self.read({DISCOVERY: OSError("timed out")})
        rover = self.cars["gBzhCkQLqke86wy25xZCeW"]
        self.assertEqual((rover["title"], rover["price"], rover["posted"]), ("2017 Land Rover Discovery Sport Luxury", 9000, None))
        self.assertEqual(self.cars["qKwY5Qp8mXrFkopbKgyAf8"]["year"], 2017)   # the next one is still read

    def test_told_to_slow_down_it_asks_for_no_more_listing_pages_this_run(self):
        found, complete = self.read({DISCOVERY: fetch.RateLimited(DISCOVERY)})
        self.assertEqual(self.get.asked, [SEARCH, EXPEDITION, DISCOVERY])
        self.assertEqual(len(found), 4)                                      # all four results, three of them bare
        self.assertIsNone(self.cars["3MNmKx9nMZJ6m82LbgMUdR"]["posted"])

    def test_no_more_listing_pages_in_one_run_than_the_cap(self):
        get = answers()
        craigslist.read(PLACE, get, SEEN, limit=2)
        self.assertEqual(get.asked, [SEARCH, EXPEDITION, DISCOVERY])

    def test_a_page_as_long_as_the_search_shows_at_most_is_not_a_whole_read(self):
        found, complete = craigslist.read(PLACE, answers(), SEEN, full_page=4)
        self.assertFalse(complete)

    def test_a_search_page_with_no_results_is_not_read(self):
        with self.assertRaises(NotRead):
            self.read({SEARCH: b"<html><body><ol class=\"cl-static-search-results\"></ol></body></html>"})

    def test_sends_the_trackers_own_name(self):
        seen = []

        def get(url, headers=None, **options):
            seen.append((headers or {}).get("User-Agent"))
            return (FIXTURES / "craigslist_search.html").read_bytes() if url == SEARCH else page("craigslist_expedition.html")
        craigslist.read(PLACE, get, SEEN, limit=1)
        self.assertEqual(seen, [None, None])                                 # fetch.get's default: "cartrack/0.1"


if __name__ == "__main__":
    unittest.main()
