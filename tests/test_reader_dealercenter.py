import json
import pathlib
import unittest
import urllib.parse

from cartrack import readers
from cartrack.readers import dealercenter

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from real DealerCenter answers, 2026-11-21
SEEN = "2026-11-21T06:00"
AJAX = "https://www.colliervilleautocenter.com/wp-admin/admin-ajax.php"


def answers(count="dealercenter_count.json", pages=("dealercenter_page1.html", "dealercenter_page2.html")):
    """A `get` for the site's admin-ajax: the vehicle count, then numbered pages of cards, then an empty page."""
    asked = []

    def get(url, data=None, headers=None, **options):
        form = dict(urllib.parse.parse_qsl((data or b"").decode()))
        asked.append((url, form, headers or {}))
        if url != AJAX:
            raise AssertionError(f"unexpected address {url}")
        if form.get("action") == "dws_inventory_search_service":
            return count if isinstance(count, bytes) else (FIXTURES / count).read_bytes()
        number = int(form["page_no"])
        name = pages[number - 1] if number <= len(pages) else "dealercenter_empty.html"
        return (FIXTURES / name).read_bytes()
    get.asked = asked
    return get


def counted(total):
    return json.dumps([{"OptionType": 1, "Count": total, "Value": "JEEP", "Value2": None, "OptionChild": None}]).encode()


class DealerCenter(unittest.TestCase):
    DEALER = {"host": "colliervilleautocenter.com", "website": "https://www.colliervilleautocenter.com/",
              "name": "Collierville Auto Center", "city": "Collierville", "state": "TN", "zip": None,
              "lat": None, "lon": None}

    def read(self, get=None):
        self.get = get or answers()
        return dealercenter.read(self.DEALER, self.get, SEEN)

    def test_asks_the_count_then_each_page_by_post_until_a_page_is_empty(self):
        self.read(answers(count=counted(3)))
        forms = [form for _, form, _ in self.get.asked]
        self.assertEqual(forms[0], {"action": "dws_inventory_search_service", "requestType": "get_vehicle_count"})
        self.assertEqual([form.get("page_no") for form in forms[1:]], ["1", "2"])
        self.assertTrue(all(form["action"] == "dws_inventory_vehicles" for form in forms[1:]))
        self.assertEqual(self.get.asked[1][2]["Content-Type"], "application/x-www-form-urlencoded")

    def test_reads_the_real_wrangler(self):
        jeep = self.read()[0][0]
        self.assertEqual(jeep["id"], "colliervilleautocenter.com:1C4JJXSJ1PW511496")
        self.assertEqual((jeep["year"], jeep["make"], jeep["model"], jeep["trim"]),
                         (2023, "jeep", "WRANGLER UNLIMITED", "RUBICON 392 SPORT UTILITY 4D"))
        self.assertEqual((jeep["vin"], jeep["miles"], jeep["drive"]), ("1C4JJXSJ1PW511496", 20503, "4wd"))
        self.assertEqual(jeep["url"], "https://www.colliervilleautocenter.com/inventory/jeep/wrangler-unlimited/p6842/")
        self.assertEqual(jeep["title"], "2023 JEEP WRANGLER UNLIMITED")
        self.assertEqual(jeep["extra"]["stock"], "P6842")
        self.assertEqual(jeep["photos"], ["https://imagescf.dealercenter.net/640/480/202607-5071c4aab3f5466ead15f93e034ca504/"
                                          "202609-ccf1b4f61d9c425783af87d721ad2e24.jpg"])

    def test_the_asking_price_is_before_the_dealer_fee_and_the_shown_total_is_kept(self):
        # The card shows $70,098 "*Includes Dealer Fees": $69,100 plus a $998 doc fee.
        jeep = self.read()[0][0]
        self.assertEqual(jeep["price"], 69100)
        self.assertEqual(jeep["extra"]["shown_price"], 70098)
        self.assertEqual(jeep["extra"]["fees"], {"Doc Fee": 998})

    def test_a_make_or_model_of_several_words_follows_the_address(self):
        found = self.read()[0]
        bmw = found[1]
        self.assertEqual((bmw["make"], bmw["model"]), ("bmw", "7 SERIES"))
        self.assertEqual((found[2]["make"], found[2]["model"]), ("jeep", "GRAND CHEROKEE L"))

    def test_every_page_is_read_and_as_many_cars_as_counted_is_a_whole_read(self):
        found, complete = self.read(answers(count=counted(3)))
        self.assertEqual([car["vin"] for car in found], ["1C4JJXSJ1PW511496", "WBA33EJ05PCL55879", "1C4RJJDG4M8160360"])
        self.assertTrue(complete)

    def test_fewer_cars_than_the_site_counted_is_not_a_whole_read(self):
        found, complete = self.read()          # the real count says 78
        self.assertEqual(len(found), 3)
        self.assertFalse(complete)

    def test_a_count_that_cannot_be_had_is_not_a_whole_read(self):
        found, complete = self.read(answers(count=b"<html>Just a moment...</html>"))
        self.assertEqual(len(found), 3)
        self.assertFalse(complete)

    def test_reads_the_other_card_layout_with_vin_and_mileage_lines(self):
        dealer = {**self.DEALER, "host": "carchoiceonline.com", "website": "https://www.carchoiceonline.com/"}
        get = answers(count=counted(1), pages=("dealercenter_layout_details.html",))
        ilx = dealercenter.read(dealer, lambda url, **o: get(AJAX, **o), SEEN)[0][0]
        self.assertEqual((ilx["year"], ilx["make"], ilx["model"], ilx["trim"]), (2017, "acura", "ILX", "SEDAN 4D"))
        self.assertEqual((ilx["vin"], ilx["miles"], ilx["price"]), ("19UDE2F36HA011883", 105035, 13700))
        self.assertEqual((ilx["engine"], ilx["transmission"], ilx["color"]), ("4-cyl, i-vtec, 2.4 liter", "automatic", "BLUE"))
        self.assertEqual(ilx["extra"]["stock"], "14612")

    def test_no_cards_at_all_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read(answers(pages=()))

class Past(unittest.TestCase):
    def test_keeps_the_history_report_and_carfaxs_badge(self):
        found, _ = dealercenter.read(DealerCenter.DEALER, answers(), SEEN)
        extras = [car["extra"] for car in found]
        self.assertIn("https://www.carfax.com/vehiclehistory/ar20/GsjUE-wRppZNNe2cJJ9dj0FhQJAgUwztAL8KEkOfErfhibX449dcb5hPnDQyxiVs2"
                      "CvIKiqXki3tqWfnaZqFrFJTZCR9yjSOyPc", [extra.get("history_url") for extra in extras])
        self.assertIn((True, "good"), [(extra.get("one_owner"), extra.get("carfax_value")) for extra in extras])


if __name__ == "__main__":
    unittest.main()
