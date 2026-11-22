import unittest

from cartrack import flags


class Found(unittest.TestCase):
    """Phrases of the kinds read on Craigslist on 2026-11-21 (research/11-listing-quality.md), shortened."""

    def test_a_car_that_does_not_run(self):
        for said in ("Wont crank, won't start", "It doesn't run", "non running", "ran when parked", "blown head gasket",
                     "engine is locked up", "Parts car only", "selling for parts", "bring a trailer", "must be towed",
                     "2020 Chrysler Pacifica – Mechanic Special / As-Is", "motor has a rod knock"):
            self.assertIn("not_running", flags.found(said), said)

    def test_tow_packages_and_spare_parts_are_not_a_car_that_does_not_run(self):
        for said in ("Has tow package and hitch", "extra parts included", "new parts all around", "runs and drives great"):
            self.assertNotIn("not_running", flags.found(said), said)

    def test_a_named_fault(self):
        for said in ("needs transmission", "needs a new head gasket", "transmission is slipping", "Drives but has a misfire",
                     "check engine light is on", "service engine soon", "it overheats", "small oil leak", "engine knocks"):
            self.assertIn("mechanical_fault", flags.found(said), said)

    def test_a_denied_fault_is_not_a_fault(self):
        for said in ("No leaks", "Zero check engine lights", "no clutch slippage", "never overheats",
                     "rebuilt transmission", "new engine installed", "no leaks or noises"):
            self.assertEqual(flags.found(said), [], said)

    def test_needing_work(self):
        for said in ("needs brakes and tires", "will need a battery", "AC does not work", "radio stopped working",
                     "great project car", "needs tlc", "back window is not working"):
            self.assertIn("needs_work", flags.found(said), said)

    def test_a_seller_who_needs_to_sell_is_not_a_car_that_needs_work(self):
        for said in ("need to sell", "I need the room", "no longer need it", "needs nothing", "needs nothing mechanically",
                     "needs to go", "needs a good home", "everything works"):
            self.assertNotIn("needs_work", flags.found(said), said)

    def test_what_the_text_says_of_the_title(self):
        self.assertEqual(flags.found("No title, bill of sale only"), ["title_none"])
        self.assertEqual(flags.found("lost the title"), ["title_none"])
        self.assertEqual(flags.found("no title issues"), [])
        self.assertEqual(flags.found("has a rebuilt title"), ["title_brand"])
        self.assertEqual(flags.found("salvage"), ["title_brand"])
        self.assertEqual(flags.found("rebuilt engine at 120k"), [])
        self.assertEqual(flags.found("bank has clean title, still owe on it"), ["title_lien"])
        self.assertEqual(flags.found("lien free title in hand"), [])

    def test_damage_is_named_but_a_denied_accident_is_not(self):
        self.assertEqual(flags.found("was hit in the rear"), ["damage"])
        self.assertEqual(flags.found("minor hail damage"), ["damage"])
        self.assertEqual(flags.found("never been in an accident"), [])
        self.assertEqual(flags.found("no accidents, no damage"), [])

    def test_a_dealers_turns_of_phrase(self):
        for said in ("we finance everyone", "$500 down", "visit www.bestcarsmemphis.com", "more cars available",
                     "stock # 4471", "trade-ins welcome", "plus tax and doc fee"):
            self.assertEqual(flags.found(said), ["trade_seller"], said)
        for said in ("no financing", "clean carfax.com report", "cash only, no trades", "email me at someone@gmail.com"):
            self.assertEqual(flags.found(said), [], said)

    def test_title_and_description_are_read_together_and_curly_apostrophes_count(self):
        self.assertEqual(flags.found("2009 Chevy Impala LT", "Runs fine but it won’t shift into reverse. Needs trans."),
                         ["not_running", "mechanical_fault", "needs_work"])
        self.assertEqual(flags.found(None, None), [])

    def test_the_plain_words_for_a_card(self):
        names = ["not_running", "needs_work", "damage", "trade_seller"]
        self.assertEqual(flags.say(names, flags.OUT), ["not running", "needs work"])
        self.assertEqual(flags.say(names, flags.SHOWN), ["damage mentioned", "reads like a trader's advert"])


if __name__ == "__main__":
    unittest.main()
