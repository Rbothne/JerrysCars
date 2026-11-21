import json
import unittest

from cartrack import catalogue, identify
from cartrack.listings import make_listing

SEEN = "2026-11-21T21:00"
KNOWN = {"ford": {"F-150": 40, "Expedition": 6, "Expedition MAX": 2, "Explorer": 12},
         "chevrolet": {"Silverado 1500": 30, "Silverado 2500 HD": 4, "Equinox": 20},
         "honda": {"CR-V": 15, "Civic": 22}, "mazda": {"Mazda3": 5, "CX-5": 9},
         "land rover": {"Discovery": 2, "Discovery Sport": 5, "Range Rover Sport": 3},
         "mercedes-benz": {"C-Class": 8}, "gmc": {"Sierra 3500 HD": 2, "Acadia": 7}, "bmw": {"3 Series": 9}}


class Named(unittest.TestCase):
    def named(self, typed):
        return identify.named(typed, KNOWN)

    def test_make_model_and_the_rest_as_trim(self):
        self.assertEqual(self.named("ford expedition xl"), {"make": "ford", "model": "Expedition", "trim": "xl"})

    def test_the_longest_model_that_fits_wins(self):
        self.assertEqual(self.named("ford expedition max limited")["model"], "Expedition MAX")
        self.assertEqual(self.named("land rover discovery sport hse"),
                         {"make": "land rover", "model": "Discovery Sport", "trim": "hse"})
        self.assertEqual(self.named("land rover discovery")["model"], "Discovery")

    def test_punctuation_and_spacing_inside_a_model_do_not_matter(self):
        self.assertEqual(self.named("ford f150 xlt 4x4"), {"make": "ford", "model": "F-150", "trim": "xlt 4x4"})
        self.assertEqual(self.named("ford f-150")["model"], "F-150")
        self.assertEqual(self.named("ford f 150 lariat")["model"], "F-150")
        self.assertEqual(self.named("honda crv ex")["model"], "CR-V")
        self.assertEqual(self.named("gmc sierra 3500hd denali 4x4 4dr"),
                         {"make": "gmc", "model": "Sierra 3500 HD", "trim": "denali 4x4 4dr"})

    def test_nicknames_and_two_word_makes(self):
        self.assertEqual(self.named("chevy equinox lt")["make"], "chevrolet")
        self.assertEqual(self.named("mercedes c-class")["make"], "mercedes-benz")
        self.assertEqual(self.named("Mercedes-Benz C-Class c300"), {"make": "mercedes-benz", "model": "C-Class", "trim": "c300"})

    def test_a_model_that_repeats_the_make(self):
        self.assertEqual(self.named("mazda 3 touring"), {"make": "mazda", "model": "Mazda3", "trim": "touring"})
        self.assertEqual(self.named("mazda mazda3")["model"], "Mazda3")

    def test_a_model_given_by_its_first_word_takes_the_commonest_model_that_starts_with_it(self):
        self.assertEqual(self.named("chevy silverado lt"), {"make": "chevrolet", "model": "Silverado 1500", "trim": "lt"})

    def test_a_first_word_that_is_only_a_number_is_not_enough(self):
        self.assertEqual(self.named("bmw 3"), {"make": "bmw", "model": None, "trim": None})

    def test_a_known_make_with_an_unknown_model_gives_the_make_alone(self):
        self.assertEqual(self.named("ford pinto"), {"make": "ford", "model": None, "trim": None})

    def test_an_unknown_make_gives_nothing(self):
        self.assertIsNone(self.named("freightliner cascadia"))
        self.assertIsNone(self.named(""))
        self.assertIsNone(self.named(None))


class Fill(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def add(self, source, source_id, **fields):
        catalogue.record(self.db, make_listing(source, source_id, **{
            "url": f"https://{source}/{source_id}", "title": "a car", "seen": SEEN, "channel": "dealer_site",
            "price": 9000, **fields}))

    def dealer_cars(self):
        for number in range(3):
            self.add("lot.example", f"e{number}", year=2012, make="ford", model="Expedition", identity_how="vin")
        self.add("lot.example", "x1", year=2015, make="ford", model="Explorer", identity_how="vin")
        self.add("lot.example", "typed", year=2015, make="ford", model="Exploder")       # a dealer's own wording

    def row(self, key):
        return self.db.execute("SELECT * FROM listing WHERE id = ?", (key,)).fetchone()

    def test_known_models_are_the_ones_a_vin_named(self):
        self.dealer_cars()
        self.assertEqual(identify.known_models(self.db), {"ford": {"Expedition": 3, "Explorer": 1}})

    def test_a_listing_with_only_the_sellers_words_is_named_from_them(self):
        self.dealer_cars()
        self.add("memphis.craigslist.org", "abc", channel="classified", year=2011, extra={"makemodel": "ford expedition xl"})
        self.assertEqual(identify.fill(self.db), 1)
        row = self.row("memphis.craigslist.org:abc")
        self.assertEqual((row["make"], row["model"], row["trim"], row["identity_how"]), ("ford", "Expedition", "xl", "title"))
        self.assertEqual(row["vehicle_key"], "2011|ford|expedition|xl|||")

    def test_a_listing_that_already_has_its_make_and_model_is_left_alone(self):
        self.dealer_cars()
        before = dict(self.row("lot.example:typed"))
        self.assertEqual(identify.fill(self.db), 0)
        self.assertEqual(dict(self.row("lot.example:typed")), before)

    def test_words_that_name_no_known_make_change_nothing_and_are_tried_again_later(self):
        self.add("memphis.craigslist.org", "abc", channel="classified", year=2011, extra={"makemodel": "ford expedition xl"})
        self.assertEqual(identify.fill(self.db), 0)                       # nothing is known about any Ford yet
        self.assertIsNone(self.row("memphis.craigslist.org:abc")["make"])
        self.dealer_cars()
        self.assertEqual(identify.fill(self.db), 1)

    def test_a_later_read_that_says_less_does_not_undo_the_name(self):
        self.dealer_cars()
        self.add("memphis.craigslist.org", "abc", channel="classified", year=2011, extra={"makemodel": "ford expedition xl"})
        identify.fill(self.db)
        self.add("memphis.craigslist.org", "abc", channel="classified", seen="2026-11-22T09:00")   # the search page alone
        row = self.row("memphis.craigslist.org:abc")
        self.assertEqual((row["year"], row["make"], row["model"], row["identity_how"]), (2011, "ford", "Expedition", "title"))
        self.assertEqual(json.loads(row["extra"]), {"makemodel": "ford expedition xl"})


if __name__ == "__main__":
    unittest.main()
