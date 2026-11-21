import unittest

import build
from cartrack import catalogue, readers
from cartrack.listings import make_listing

NOW = "2026-11-21T05:00"
PECK = {"key": "peckdaniel.com", "host": "peckdaniel.com", "name": "Peck Daniel Auto Sales", "platform": "autorevo",
        "city": "Memphis", "state": "TN", "miles": 8.2}
KERAS = {"key": "jimkerasnissan.com", "host": "jimkerasnissan.com", "name": "Jim Keras Nissan", "platform": "dealeron",
         "city": "Memphis", "state": "TN", "miles": 9.0}
GOSSETT = {"key": "gossettmotors.com", "host": "gossettmotors.com", "name": "Gossett", "platform": "teamvelocity"}
NO_SITE = {"key": "osm:node/1", "host": None, "name": "Max Auto Sales", "platform": None}


def car(host, source_id, seen=NOW, **fields):
    return make_listing(host, source_id, **{
        "url": f"https://{host}/{source_id}", "title": "2012 Toyota Camry LE", "seen": seen, "channel": "dealer_site",
        "seller_type": "dealer", "seller_name": "A Dealer", "price": 6500, "miles": 134200,
        "year": 2012, "make": "toyota", "model": "Camry", **fields})


def reader(*source_ids, complete=True):
    def read(dealer, get, seen):
        return [car(dealer["host"], source_id, seen) for source_id in source_ids], complete
    return read


class ReadDealers(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def run_build(self, dealers, table, now=NOW):
        return build.read_dealers(self.db, dealers, table, get=None, now=now, say=lambda line: None)

    def live(self):
        return [row[0] for row in self.db.execute("SELECT id FROM listing WHERE gone IS NULL ORDER BY id")]

    def test_each_dealer_is_read_by_its_platforms_reader(self):
        self.run_build([PECK, KERAS], {"autorevo": reader("1", "2"), "dealeron": reader("9")})
        self.assertEqual(self.live(), ["jimkerasnissan.com:9", "peckdaniel.com:1", "peckdaniel.com:2"])

    def test_dealers_with_no_reader_or_no_site_are_left_alone(self):
        report = self.run_build([GOSSETT, NO_SITE, PECK], {"autorevo": reader("1")})
        self.assertEqual(self.live(), ["peckdaniel.com:1"])
        self.assertEqual([line["dealer"] for line in report], ["peckdaniel.com"])

    def test_a_car_missing_from_a_whole_read_is_gone(self):
        self.run_build([PECK], {"autorevo": reader("1", "2", "3", "4", "5")})
        self.run_build([PECK], {"autorevo": reader("1", "2", "3", "4")}, now="2026-11-22T05:00")
        self.assertEqual(self.live(), [f"peckdaniel.com:{n}" for n in range(1, 5)])

    def test_a_partial_read_marks_nothing_gone(self):
        self.run_build([PECK], {"autorevo": reader("1", "2", "3", "4", "5")})
        self.run_build([PECK], {"autorevo": reader("1", "2", "3", "4", complete=False)}, now="2026-11-22T05:00")
        self.assertEqual(len(self.live()), 5)

    def test_a_reader_that_fails_stops_only_its_own_dealer(self):
        def broken(dealer, get, seen):
            raise readers.NotRead("no cars on the page")
        report = self.run_build([PECK, KERAS], {"autorevo": broken, "dealeron": reader("9")})
        self.assertEqual(self.live(), ["jimkerasnissan.com:9"])
        self.assertEqual([(line["dealer"], line["ok"]) for line in report],
                         [("peckdaniel.com", False), ("jimkerasnissan.com", True)])
        self.assertIn("no cars on the page", report[0]["error"])

    def test_a_read_that_shrank_too_far_is_reported_and_marks_nothing(self):
        self.run_build([PECK], {"autorevo": reader(*"123456789")})
        report = self.run_build([PECK], {"autorevo": reader("1")}, now="2026-11-22T05:00")
        self.assertEqual(len(self.live()), 9)
        self.assertFalse(report[0]["ok"])

    def test_the_report_counts_what_each_dealer_gave(self):
        report = self.run_build([PECK], {"autorevo": reader("1", "2")})
        self.assertEqual({name: report[0][name] for name in ("dealer", "ok", "read", "new", "gone")},
                         {"dealer": "peckdaniel.com", "ok": True, "read": 2, "new": 2, "gone": 0})


class DecodeVins(unittest.TestCase):
    def test_only_vins_not_decoded_before_are_sent(self):
        db = catalogue.open_catalogue(":memory:")
        self.addCleanup(db.close)
        catalogue.record(db, car("peckdaniel.com", "1", vin="1HGCM82633A004352"))
        sent = []

        def decode(vins):
            sent.append(list(vins))
            return {vin: {"VIN": vin, "ModelYear": "2003", "Make": "HONDA", "Model": "Accord", "ErrorCode": "0"} for vin in vins}
        self.assertEqual(build.decode_vins(db, decode, NOW), 1)
        self.assertEqual(build.decode_vins(db, decode, NOW), 0)
        self.assertEqual(sent, [["1HGCM82633A004352"]])
        self.assertEqual(db.execute("SELECT make, identity_how FROM listing").fetchone()[:], ("honda", "vin"))


class PageData(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def cars(self, now="2026-11-25T05:00"):
        return build.page_data(self.db, [PECK, KERAS], now)["cars"]

    def test_a_live_car_carries_what_the_page_shows(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00", vin="1HGCM82633A004352",
                                      photos=["https://images.example/a.jpg", "https://images.example/b.jpg"]))
        shown = self.cars()[0]
        self.assertEqual(
            {name: shown[name] for name in ("id", "title", "price", "miles", "year", "make", "model", "dealer", "url", "vin", "photo")},
            {"id": "peckdaniel.com:1", "title": "2012 Toyota Camry LE", "price": 6500, "miles": 134200, "year": 2012,
             "make": "toyota", "model": "Camry", "dealer": "Peck Daniel Auto Sales", "url": "https://peckdaniel.com/1",
             "vin": "1HGCM82633A004352", "photo": "https://images.example/a.jpg"})
        self.assertEqual(shown["dealer_miles"], 8.2)

    def test_days_counts_from_when_the_tracker_first_saw_it(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00"))
        self.assertEqual(self.cars()[0]["days"], 4)

    def test_days_counts_from_the_dealers_own_date_when_it_gives_one(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00", posted="2026-10-24T00:00"))
        self.assertEqual(self.cars()[0]["days"], 32)

    def test_a_price_cut_shows_the_first_price_and_the_drop(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00"))
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-23T05:00", price=5900))
        shown = self.cars()[0]
        self.assertEqual((shown["price"], shown["was"], shown["drop"], shown["cuts"]), (5900, 6500, 600, 1))

    def test_a_car_never_repriced_has_no_drop(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00"))
        shown = self.cars()[0]
        self.assertEqual((shown["was"], shown["drop"], shown["cuts"]), (None, 0, 0))

    def test_one_car_on_two_dealer_sites_is_shown_once_at_its_lowest_price(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00", vin="1HGCM82633A004352", price=6500))
        catalogue.record(self.db, car("jimkerasnissan.com", "9", "2026-11-21T05:00", vin="1HGCM82633A004352", price=6200))
        catalogue.record(self.db, car("peckdaniel.com", "2", "2026-11-21T05:00"))
        shown = self.cars()
        self.assertEqual([(one["id"], one["price"], one["places"]) for one in shown],
                         [("jimkerasnissan.com:9", 6200, 2), ("peckdaniel.com:2", 6500, 1)])

    def test_gone_cars_are_not_shown(self):
        for n in range(1, 11):
            catalogue.record(self.db, car("peckdaniel.com", str(n), "2026-11-21T05:00"))
        catalogue.close_out(self.db, "peckdaniel.com", [f"peckdaniel.com:{n}" for n in range(1, 10)], "2026-11-22T05:00")
        self.assertEqual(len(self.cars()), 9)

    def test_a_car_with_no_price_is_not_shown(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", price=None))
        self.assertEqual(self.cars(), [])

    def test_the_page_says_when_it_was_built_and_what_was_read(self):
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        data = build.page_data(self.db, [PECK, KERAS], NOW, report=[{"dealer": "peckdaniel.com", "ok": True, "read": 1}])
        self.assertEqual(data["built"], NOW)
        self.assertEqual(data["dealers"], [{"key": "peckdaniel.com", "name": "Peck Daniel Auto Sales", "cars": 1, "ok": True}])


if __name__ == "__main__":
    unittest.main()
