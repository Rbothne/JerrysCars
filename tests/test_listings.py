import unittest

from cartrack.listings import make_listing, num

BASE = {
    "url": "https://memphis.craigslist.org/cto/d/memphis-2012-toyota-camry/8004100263.html",
    "title": "2012 Toyota Camry LE",
    "seen": "2026-11-21T03:03",
    "channel": "classified",
}


def listing(**fields):
    return make_listing("craigslist", "8004100263", **{**BASE, **fields})


class Num(unittest.TestCase):
    def test_reads_a_price_with_dollar_sign_and_commas(self):
        self.assertEqual(num("$12,500"), 12500)

    def test_text_with_no_number_is_none(self):
        self.assertIsNone(num("call for price"))

    def test_none_is_none(self):
        self.assertIsNone(num(None))


class MakeListing(unittest.TestCase):
    def test_id_joins_source_and_source_id(self):
        self.assertEqual(listing()["id"], "craigslist:8004100263")

    def test_no_title_is_no_listing(self):
        self.assertIsNone(listing(title="  "))

    def test_price_is_whole_dollars(self):
        self.assertEqual(listing(price="$6,500.00")["price"], 6500)

    def test_an_ask_under_500_is_no_price(self):
        self.assertIsNone(listing(price=0)["price"])
        self.assertIsNone(listing(price="499")["price"])

    def test_a_low_auction_bid_is_kept(self):
        made = listing(channel="auction", price_kind="bid", price=150)
        self.assertEqual(made["price"], 150)

    def test_vin_is_upper_cased_and_its_check_digit_checked(self):
        made = listing(vin=" 1hgcm82633a004352 ")
        self.assertEqual(made["vin"], "1HGCM82633A004352")
        self.assertIs(made["vin_ok"], True)

    def test_a_vin_with_a_wrong_check_digit_is_kept_and_flagged(self):
        made = listing(vin="1HGCM82613A004352")
        self.assertEqual(made["vin"], "1HGCM82613A004352")
        self.assertIs(made["vin_ok"], False)

    def test_a_chassis_number_that_is_not_17_characters_goes_to_extra(self):
        made = listing(vin="124378N400001")
        self.assertIsNone(made["vin"])
        self.assertIsNone(made["vin_ok"])
        self.assertEqual(made["extra"]["chassis"], "124378N400001")

    def test_what_the_source_does_not_say_is_none(self):
        made = listing()
        for field in ("price", "vin", "year", "make", "model", "miles", "seller_type", "lat", "lon", "zip"):
            self.assertIsNone(made[field], field)
        self.assertEqual(made["photos"], [])

    def test_make_is_lower_case_and_year_and_miles_are_whole_numbers(self):
        made = listing(year="2012", make=" Toyota ", model="Camry", miles="134,200")
        self.assertEqual((made["year"], made["make"], made["model"], made["miles"]), (2012, "toyota", "Camry", 134200))

    def test_a_year_that_cannot_be_a_model_year_is_none(self):
        self.assertIsNone(listing(year=12)["year"])

    def test_state_is_two_upper_case_letters_and_zip_five_digits(self):
        made = listing(state="tn", zip="38116-1234")
        self.assertEqual((made["state"], made["zip"]), ("TN", "38116"))
        made = listing(state="Tennessee", zip="3811")
        self.assertEqual((made["state"], made["zip"]), (None, None))

    def test_a_pin_needs_both_latitude_and_longitude(self):
        self.assertEqual(listing(lat="35.149532", lon="-90.048981")["lat"], 35.14953)
        made = listing(lat=35.1)
        self.assertEqual((made["lat"], made["lon"]), (None, None))

    def test_photos_keep_the_first_12_and_count_them_all(self):
        made = listing(photos=[f"https://images.example/{n}.jpg" for n in range(20)])
        self.assertEqual(len(made["photos"]), 12)
        self.assertEqual(made["photo_count"], 20)

    def test_a_seller_type_or_title_status_the_catalogue_does_not_know_is_none(self):
        made = listing(seller_type="broker", title_status="bonded")
        self.assertEqual((made["seller_type"], made["title_status"]), (None, None))

    def test_an_unknown_channel_is_a_mistake_in_the_reader(self):
        with self.assertRaises(ValueError):
            listing(channel="newspaper")

    def test_vehicle_key_joins_identity_in_lower_case_with_blanks_for_unknowns(self):
        made = listing(year=2013, make="Ford", model="Expedition", trim="Limited", drive="4wd")
        self.assertEqual(made["vehicle_key"], "2013|ford|expedition|limited||4wd|")

    def test_no_vehicle_key_without_year_make_and_model(self):
        self.assertIsNone(listing(year=2013, make="Ford")["vehicle_key"])


if __name__ == "__main__":
    unittest.main()
