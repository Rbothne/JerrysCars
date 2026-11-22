import json
import pathlib
import unittest

from cartrack import fetch
from cartrack.readers import NotRead
from cartrack.sources import liennotices

# Three notices cut from memphisdailynews.com's page of 20 November 2026. Every line that named a car's owner or
# lienholder was replaced before the file was saved; the sellers named are businesses.
FIXTURES = pathlib.Path(__file__).parent / "fixtures"
SEEN = "2026-11-20T23:00"
PLACE = {"key": "memphisdailynews.com", "kind": "liennotices", "site": "https://www.memphisdailynews.com",
         "name": "Lien sales (Daily News notices)"}
DAY = "https://www.memphisdailynews.com/notices/2026/Nov/20/"
EMPTY = b'<html><body><a id="misc"></a><table><tr><th>Notice</th></tr></table></body></html>'


def answers(table):
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table.get(url, EMPTY)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


def page(old=None, new=None):
    text = (FIXTURES / "dailynews_notices_1120.html").read_text(encoding="utf-8")
    if old is not None:
        assert old in text, old
        text = text.replace(old, new)
    return text.encode("utf-8")


class LienNotices(unittest.TestCase):
    def read(self, table=None, **options):
        self.get = answers(table or {DAY: "dailynews_notices_1120.html"})
        found, complete = liennotices.read(PLACE, self.get, SEEN, **options)
        self.cars = {car["vin"]: car for car in found}
        return found, complete

    def test_the_first_read_looks_back_two_weeks_and_later_ones_three_days(self):
        self.read()
        self.assertEqual(len(self.get.asked), 14)
        self.assertEqual(self.get.asked[:2], [DAY, "https://www.memphisdailynews.com/notices/2026/Nov/19/"])
        self.assertEqual(self.get.asked[-1], "https://www.memphisdailynews.com/notices/2026/Nov/7/")
        self.read(known={"MD117766-KNAGT4L30J5232389"})
        self.assertEqual(len(self.get.asked), 3)

    def test_reads_the_real_optima(self):
        found, complete = self.read()
        kia = self.cars["KNAGT4L30J5232389"]
        self.assertEqual(kia["id"], "memphisdailynews.com:MD117766-KNAGT4L30J5232389")
        self.assertEqual((kia["title"], kia["year"], kia["vin_ok"]), ("2018 Kia Optima", 2018, True))
        self.assertEqual((kia["channel"], kia["price"], kia["price_kind"]), ("auction", None, "starting"))
        self.assertEqual((kia["posted"], kia["ends"]), ("2026-11-20T00:00", "2026-12-05T00:00"))
        self.assertEqual((kia["seller_name"], kia["city"], kia["state"], kia["zip"]), ("TurboKnights, LLC", "Memphis", "TN", "38116"))
        self.assertEqual(kia["extra"], {"ad": "MD117766", "hour": "10:00", "address": "3301 Winbrook Drive, Memphis, TN 38116"})
        self.assertEqual(kia["url"], DAY)
        self.assertEqual((len(found), complete), (7, False))            # two, one and four cars; never a whole read

    def test_words_on_the_line_before_the_vin_are_the_cars(self):
        self.read()
        versa = self.cars["3N1CE2CP3FL431904"]
        self.assertEqual((versa["title"], versa["year"], versa["ends"]), ("2015 NISSAN VERSA", 2015, "2026-12-04T00:00"))
        self.assertEqual(versa["extra"], {"ad": "MD117697", "hour": "09:00", "address": "788 S MAIN ST, Memphis, TN 38106"})
        self.assertEqual(versa["city"], "Memphis")
        self.assertIsNone(versa["seller_name"])                         # this notice names no seller

    def test_nothing_that_is_not_matched_by_a_pattern_is_kept(self):
        # put a name where the paper prints one: after the VIN, and on a line of its own beside the car
        named = page("<p>VIN#3N1CE2CP3FL431904</p>", "<p>VIN#3N1CE2CP3FL431904 JANE Q PUBLIC</p><p>JOHN DOE</p><p>ACME TITLE LOANS</p>")
        self.read({DAY: named})
        kept = json.dumps(list(self.cars.values()))
        for word in ("JANE", "PUBLIC", "DOE", "ACME", "person was here"):
            self.assertNotIn(word, kept)
        self.assertEqual(self.cars["3N1CE2CP3FL431904"]["title"], "2015 NISSAN VERSA")

    def test_a_seller_whose_name_has_no_business_word_is_not_kept(self):
        self.read({DAY: page("sold at auction by Wilson Imports on", "sold at auction by Pat Wilson on")})
        self.assertIsNone(self.cars["SALWR2FV3HA136362"]["seller_name"])
        self.assertEqual(self.cars["SALWR2FV3HA136362"]["extra"]["address"], "6079 Resources Drive, Memphis, TN 38134")

    def test_words_whose_year_disagrees_with_the_vin_are_refused(self):
        # the Sorento's VIN says 2011: "2012 KIA SORENTO" is the paper's slip or another car's line
        self.read({DAY: page("<p>2011 KIA SORENTO</p>", "<p>2012 KIA SORENTO</p>")})
        kia = self.cars["5XYKW4A28BG131205"]
        self.assertEqual((kia["title"], kia["year"]), ("Vehicle 5XYKW4A28BG131205", None))

    def test_a_two_digit_year_is_read_against_the_vin(self):
        self.read({DAY: page("<p>2018 Kia Optima KNAGT4L30J5232389</p>", "<p>18 OPTIMA KNAGT4L30J5232389</p>")})
        self.assertEqual((self.cars["KNAGT4L30J5232389"]["title"], self.cars["KNAGT4L30J5232389"]["year"]), ("2018 OPTIMA", 2018))

    def test_a_car_with_its_sale_in_its_own_sentence_takes_that_date_and_address(self):
        # the fourth layout seen: one sentence a car, each with its own shop, day and street
        sentence = ("<p>Vehicle Auction on December 8, 2026 at Main Street Garage, 1824 Thomas Rd, Memphis, TN 38134, "
                    "2014 Chevrolet Traverse VIN# 1GNKRFKD0EJ320882. Owner: JANE Q PUBLIC. Lienholder: ACME LOANS</p>")
        self.read({DAY: page("<p>2014 CHEVROLET TRAVERSE</p><p>VIN#1GNKRFKD0EJ320882</p>", sentence)})
        chevy = self.cars["1GNKRFKD0EJ320882"]
        self.assertEqual((chevy["title"], chevy["ends"], chevy["zip"]), ("2014 Chevrolet Traverse", "2026-12-08T00:00", "38134"))
        self.assertEqual(chevy["extra"]["address"], "1824 Thomas Rd, Memphis, TN 38134")
        self.assertNotIn("PUBLIC", json.dumps(chevy))

    def test_a_street_run_into_the_city_with_no_comma_is_split_at_the_citys_name(self):
        # as printed: "LOCATED AT 3501 KNIGHT ARNOLD MEMPHIS, TN. 38118"
        self.read({DAY: page("AT 788 S MAIN ST. MEMPHIS, TN 38106", "LOCATED AT 3501 KNIGHT ARNOLD MEMPHIS, TN. 38118")})
        versa = self.cars["3N1CE2CP3FL431904"]
        self.assertEqual((versa["city"], versa["extra"]["address"]), ("Memphis", "3501 KNIGHT ARNOLD, Memphis, TN 38118"))

    def test_a_vin_in_another_part_of_the_page_is_not_a_car_for_sale(self):
        self.read()
        self.assertNotIn("1HGCM82633A004352", self.cars)                 # it stands in the foreclosure section

    def test_a_notice_printed_on_two_days_is_one_listing_per_car(self):
        found, _ = self.read({DAY: "dailynews_notices_1120.html",
                              "https://www.memphisdailynews.com/notices/2026/Nov/13/": "dailynews_notices_1120.html"})
        self.assertEqual(len(found), 7)
        self.assertEqual(self.cars["KNAGT4L30J5232389"]["posted"], "2026-11-20T00:00")

    def test_a_day_that_fails_is_passed_over_and_the_others_are_read(self):
        found, _ = self.read({DAY: OSError("timed out"),
                              "https://www.memphisdailynews.com/notices/2026/Nov/19/": "dailynews_notices_1120.html"})
        self.assertEqual(len(found), 7)

    def test_told_to_slow_down_it_asks_for_no_more_days(self):
        self.read({DAY: "dailynews_notices_1120.html",
                   "https://www.memphisdailynews.com/notices/2026/Nov/19/": fetch.RateLimited("slow down")})
        self.assertEqual(len(self.get.asked), 2)
        self.assertEqual(len(self.cars), 7)

    def test_when_no_day_can_be_read_the_read_fails(self):
        with self.assertRaises(NotRead):
            self.read({f"https://www.memphisdailynews.com/notices/2026/Nov/{day}/": OSError("down") for day in range(7, 21)})


if __name__ == "__main__":
    unittest.main()
