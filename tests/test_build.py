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

    def test_a_car_no_read_has_found_for_three_days_is_gone_though_no_read_was_whole(self):
        # Carvana, 2026-11-21: 1,901 read against a count that moved, so "partial", and 48 sold cars stayed up
        self.run_build([PECK], {"autorevo": reader("1", "2", complete=False)})
        for day in ("22", "23"):
            report = self.run_build([PECK], {"autorevo": reader("1", complete=False)}, now=f"2026-11-{day}T05:00")
            self.assertEqual((len(self.live()), report[0]["gone"]), (2, 0))
        report = self.run_build([PECK], {"autorevo": reader("1", complete=False)}, now="2026-11-24T05:00")
        self.assertEqual((self.live(), report[0]["gone"]), (["peckdaniel.com:1"], 1))

    def test_a_dealer_whose_lot_really_shrank_is_believed_after_three_days(self):
        self.run_build([PECK], {"autorevo": reader(*"123456789")})
        for day in ("22", "23"):
            report = self.run_build([PECK], {"autorevo": reader("1")}, now=f"2026-11-{day}T05:00")
            self.assertEqual((report[0]["ok"], len(self.live())), (False, 9))
        report = self.run_build([PECK], {"autorevo": reader("1")}, now="2026-11-24T05:00")
        self.assertEqual((report[0]["ok"], report[0]["gone"], self.live()), (True, 8, ["peckdaniel.com:1"]))

    def test_a_read_whose_listings_mostly_share_an_id_is_refused(self):
        # the storefront tracker's lesson: a grid read with the wrong id gives every tile the same one
        self.run_build([PECK], {"autorevo": reader("1", "2", "3")})
        report = self.run_build([PECK], {"autorevo": reader("7", "7", "7", "7", "7", "8")}, now="2026-11-22T05:00")
        self.assertEqual(report[0]["ok"], False)
        self.assertIn("6 listings share 2 ids", report[0]["error"])
        self.assertEqual(self.live(), ["peckdaniel.com:1", "peckdaniel.com:2", "peckdaniel.com:3"])

    def test_a_stray_repeat_among_many_listings_is_let_through(self):
        report = self.run_build([PECK], {"autorevo": reader("1", "2", "3", "4", "5", "6", "7", "8", "9", "9")})
        self.assertEqual((report[0]["ok"], report[0]["read"], len(self.live())), (True, 9, 9))


CRAIGSLIST = {"key": "memphis.craigslist.org", "kind": "craigslist", "site": "memphis", "name": "Craigslist, by owner"}
AREA = {"name": "Memphis, TN", "home": [35.1495, -90.0490], "radius_miles": 60}


def private(source_id, seen=NOW, **fields):
    return make_listing("memphis.craigslist.org", source_id, **{
        "url": f"https://www.craigslist.org/view/d/a-car/{source_id}", "title": "2012 toyota camry le", "seen": seen,
        "channel": "classified", "seller_type": "private", "price": 5200, **fields})


def detailed(source_id, seen=NOW, **fields):
    return private(source_id, seen, **{"posted": "2026-11-20T15:00", "year": 2012, "miles": 140000,
                                       "title_status": "clean", "extra": {"makemodel": "toyota camry le"}, **fields})


class ReadSources(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)
        self.known = []

    def source(self, *listings, complete=True):
        def read(place, get, seen, known=()):
            self.known.append(set(known))
            return [dict(listing, seen=seen) for listing in listings], complete
        return {"craigslist": read}

    def run_build(self, readers, now=NOW, places=(CRAIGSLIST,)):
        return build.read_sources(self.db, places, readers, get=None, now=now, say=lambda line: None)

    def live(self):
        return [row[0] for row in self.db.execute("SELECT id FROM listing WHERE gone IS NULL ORDER BY id")]

    def test_each_place_is_read_by_its_kinds_reader_and_reported_like_a_dealer(self):
        report = self.run_build(self.source(detailed("a"), detailed("b")))
        self.assertEqual(self.live(), ["memphis.craigslist.org:a", "memphis.craigslist.org:b"])
        self.assertEqual({name: report[0][name] for name in ("dealer", "platform", "ok", "read", "new", "gone", "complete")},
                         {"dealer": "memphis.craigslist.org", "platform": "craigslist", "ok": True, "read": 2, "new": 2,
                          "gone": 0, "complete": True})

    def test_the_reader_is_told_which_listings_the_catalogue_already_has_in_full(self):
        self.run_build(self.source(detailed("a"), private("b")))            # b's own page could not be had
        self.run_build(self.source(private("a"), private("b")), now="2026-11-22T05:00")
        self.assertEqual(self.known, [set(), {"a"}])

    def test_a_later_read_of_the_list_alone_keeps_what_the_listings_page_gave(self):
        self.run_build(self.source(detailed("a")))
        self.run_build(self.source(private("a", price=4800)), now="2026-11-22T05:00")
        row = self.db.execute("SELECT price, year, miles, posted, title_status FROM listing").fetchone()
        self.assertEqual(row[:], (4800, 2012, 140000, "2026-11-20T15:00", "clean"))

    def test_a_listing_missing_from_a_whole_read_is_gone_and_from_a_partial_one_is_not(self):
        five = [detailed(name) for name in "abcde"]
        self.run_build(self.source(*five))
        self.run_build(self.source(*five[:4], complete=False), now="2026-11-22T05:00")
        self.assertEqual(len(self.live()), 5)
        report = self.run_build(self.source(*five[:4]), now="2026-11-23T05:00")
        self.assertEqual((len(self.live()), report[0]["gone"]), (4, 1))

    def test_a_place_whose_read_fails_is_reported_and_keeps_its_listings(self):
        self.run_build(self.source(detailed("a")))

        def broken(place, get, seen, known=()):
            raise readers.NotRead("no results")
        report = self.run_build({"craigslist": broken}, now="2026-11-22T05:00")
        self.assertEqual(self.live(), ["memphis.craigslist.org:a"])
        self.assertEqual((report[0]["ok"], report[0]["error"]), (False, "NotRead: no results"))

    def test_a_place_may_say_how_far_its_listings_can_thin_out_between_reads(self):
        ten = [detailed(name) for name in "abcdefghij"]
        self.run_build(self.source(*ten))
        report = self.run_build(self.source(*ten[:6]), now="2026-11-22T05:00")      # 60% left: under the usual 80%
        self.assertEqual((report[0]["ok"], len(self.live())), (False, 10))
        quick = {**CRAIGSLIST, "floor": 0.5}
        report = self.run_build(self.source(*ten[:6]), now="2026-11-23T05:00", places=(quick,))
        self.assertEqual((report[0]["ok"], report[0]["gone"], len(self.live())), (True, 4, 6))

    def test_a_place_of_a_kind_with_no_reader_is_left_alone(self):
        self.assertEqual(self.run_build({}), [])


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

    def test_a_car_says_what_it_runs_on(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", fuel="Gasoline"))
        catalogue.record(self.db, car("peckdaniel.com", "2", fuel="Diesel"))
        catalogue.record(self.db, car("peckdaniel.com", "3", fuel="Electric"))
        catalogue.record(self.db, car("peckdaniel.com", "4", fuel="Flexible Fuel Vehicle (FFV)"))
        catalogue.record(self.db, car("peckdaniel.com", "5"))
        self.assertEqual([one["fuel"] for one in self.cars()], ["gas", "diesel", "electric", "gas", None])

    def test_the_vin_says_when_a_petrol_car_is_a_hybrid(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", vin="1HGCM82633A004352", fuel="Gasoline"))
        catalogue.save_decodes(self.db, {"1HGCM82633A004352": {
            "ErrorCode": "0", "ModelYear": "2012", "Make": "TOYOTA", "Model": "Camry",
            "ElectrificationLevel": "Strong HEV (Hybrid Electric Vehicle)"}}, NOW)
        self.assertEqual(self.cars()[0]["fuel"], "hybrid")

    def test_a_car_sold_online_is_told_from_one_on_a_lot(self):
        online = {"key": "carvana.com", "host": "carvana.com", "name": "Carvana", "platform": "carvana"}
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        catalogue.record(self.db, car("carvana.com", "2"))
        shown = build.page_data(self.db, [PECK, online], NOW)["cars"]
        self.assertEqual([(one["id"], one["kind"]) for one in shown], [("carvana.com:2", "online"), ("peckdaniel.com:1", "lot")])

    def test_a_car_carries_the_typical_price_it_was_judged_against(self):
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        catalogue.record(self.db, car("peckdaniel.com", "2"))
        shown = build.page_data(self.db, [PECK], NOW, judge=lambda cars, year: {
            "peckdaniel.com:1": {"typical": 8000, "similar": 5}})["cars"]
        self.assertEqual([(one["typical"], one["similar"]) for one in shown], [(8000, 5), (None, None)])

    def test_the_judge_is_given_each_vehicle_once_with_what_its_vin_says(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", vin="1HGCM82633A004352", price=6500, fuel="Gasoline"))
        catalogue.record(self.db, car("jimkerasnissan.com", "9", vin="1HGCM82633A004352", price=6200))
        catalogue.save_decodes(self.db, {"1HGCM82633A004352": {
            "ErrorCode": "0", "ModelYear": "2012", "Make": "TOYOTA", "Model": "Camry", "Series": "LE",
            "EngineCylinders": "4", "DisplacementL": "2.5", "GVWR": "Class 1C: 4,001 - 5,000 lb (1,814 - 2,268 kg)"}}, NOW)
        given = []

        def judge(cars, year):
            given.extend(cars)
            given.append(year)
            return {}
        build.page_data(self.db, [PECK, KERAS], "2026-11-25T05:00", judge=judge)
        self.assertEqual(len(given), 2)
        self.assertEqual(given[1], 2026)
        self.assertEqual({name: given[0][name] for name in ("id", "price", "year", "make", "model", "miles", "series",
                                                             "cylinders", "litres", "weight_class")},
                         {"id": "jimkerasnissan.com:9", "price": 6200, "year": 2012, "make": "toyota", "model": "Camry",
                          "miles": 134200, "series": "LE", "cylinders": 4.0, "litres": 2.5, "weight_class": "1"})

    def test_miles_a_year_counts_the_model_year_as_the_first(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", year=2012, miles=134200))      # 15 years on the road in 2026
        catalogue.record(self.db, car("peckdaniel.com", "2", year=2026, miles=9000))
        catalogue.record(self.db, car("peckdaniel.com", "3", year=2027, miles=40))
        self.assertEqual([one["per_year"] for one in self.cars()], [8946, 9000, 40])

    def test_the_price_shown_includes_the_dealers_stated_fee(self):
        # Jim Keras advertises $7,252 for a car its feed prices at $6,353 plus an $899 doc fee (2026-11-21)
        catalogue.record(self.db, car("peckdaniel.com", "1", price=6353, extra={"fees": {"Dealer Doc Fee": 899}}))
        shown = self.cars()[0]
        self.assertEqual((shown["price"], shown["base"], shown["fees"]), (7252, 6353, 899))

    def test_the_total_adds_tennessee_tax_on_the_price_with_its_fee(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", price=10000, extra={"fees": {"Dealer Doc Fee": 899}}))
        shown = self.cars()[0]
        self.assertEqual((shown["price"], shown["tax"], shown["total"]), (10899, 851, 11750))

    def test_a_price_cut_is_measured_between_prices_that_both_include_the_fee(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-21T05:00", price=6500, extra={"fees": {"Doc Fee": 500}}))
        catalogue.record(self.db, car("peckdaniel.com", "1", "2026-11-23T05:00", price=5900, extra={"fees": {"Doc Fee": 500}}))
        shown = self.cars()[0]
        self.assertEqual((shown["price"], shown["was"], shown["drop"]), (6400, 7000, 600))

    def test_the_judge_weighs_the_price_with_its_fee(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", price=6353, extra={"fees": {"Dealer Doc Fee": 899}}))
        given = []
        build.page_data(self.db, [PECK], NOW, judge=lambda cars, year: given.extend(cars) or {})
        self.assertEqual(given[0]["price"], 7252)

    def test_one_car_on_two_sites_is_shown_where_it_costs_least_with_fees(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", vin="1HGCM82633A004352", price=6000, extra={"fees": {"Doc Fee": 900}}))
        catalogue.record(self.db, car("jimkerasnissan.com", "9", vin="1HGCM82633A004352", price=6500))
        shown = self.cars()
        self.assertEqual([(one["id"], one["price"]) for one in shown], [("jimkerasnissan.com:9", 6500)])

    def test_a_car_whose_dealer_states_no_fee_is_totalled_with_tax_alone(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", price=10000))
        shown = self.cars()[0]
        self.assertEqual((shown["price"], shown["base"], shown["fees"], shown["tax"], shown["total"]),
                         (10000, 10000, None, 788, 10788))

    def test_a_car_carries_what_its_listing_says_of_its_past(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", extra={
            "history_url": "https://www.carfax.com/vehiclehistory/ar20/abc", "one_owner": True, "carfax_value": "good",
            "certified": True, "mpg": [25, 34], "warranty": {"basic": [15, 24500]}, "reservable": True}))
        catalogue.record(self.db, car("peckdaniel.com", "2"))
        first, second = self.cars()
        self.assertEqual({name: first[name] for name in ("history", "one_owner", "carfax_value", "certified", "mpg", "warranty", "waiting")},
                         {"history": "https://www.carfax.com/vehiclehistory/ar20/abc", "one_owner": True, "carfax_value": "good",
                          "certified": True, "mpg": [25, 34], "warranty": {"basic": [15, 24500]}, "waiting": True})
        self.assertEqual({name: second[name] for name in ("history", "one_owner", "carfax_value", "certified", "mpg", "warranty", "waiting")},
                         {"history": None, "one_owner": None, "carfax_value": None, "certified": None, "mpg": None,
                          "warranty": None, "waiting": False})

    def test_a_dealer_that_calls_every_car_certified_is_saying_nothing(self):
        # City Auto's feed marks all 447 of its used cars certified; Gossett's marks 72 of 324
        for n in range(6):
            catalogue.record(self.db, car("peckdaniel.com", str(n), extra={"certified": True}))
            catalogue.record(self.db, car("jimkerasnissan.com", str(n), extra={"certified": n < 2}))
        shown = {one["id"]: one["certified"] for one in self.cars()}
        self.assertEqual([shown[f"peckdaniel.com:{n}"] for n in range(6)], [None] * 6)
        self.assertEqual([shown[f"jimkerasnissan.com:{n}"] for n in range(6)], [True, True, False, False, False, False])

    def test_a_history_address_that_is_not_carfaxs_is_not_passed_on(self):
        catalogue.record(self.db, car("peckdaniel.com", "1", extra={"history_url": "javascript:alert(1)"}))
        self.assertIsNone(self.cars()[0]["history"])

    def shown(self, judge=None, now=NOW):
        return build.page_data(self.db, [PECK], now, places=[CRAIGSLIST], area=AREA,
                               **({"judge": judge} if judge else {}))["cars"]

    def test_a_private_sellers_car_says_so_and_where_it_is(self):
        catalogue.record(self.db, detailed("a", make="toyota", model="Camry", lat=35.0312, lon=-89.8124, geo_how="pin",
                                           city="Memphis", state="TN", extra={"where": "EAST MEMPHIS"}))
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        mine, lot = self.shown()
        self.assertEqual((mine["seller"], mine["dealer"], mine["dealer_key"], mine["where"], mine["kind"]),
                         ("private", "Craigslist, by owner", "memphis.craigslist.org", "EAST MEMPHIS", "private"))
        self.assertEqual(mine["dealer_miles"], 15.7)                        # from the listing's own map pin
        self.assertEqual((mine["fees"], mine["price"], mine["title_status"]), (None, 5200, "clean"))
        self.assertEqual((lot["seller"], lot["where"], lot["title_status"]), ("dealer", None, None))

    def test_a_private_car_with_no_neighbourhood_is_placed_by_its_city(self):
        catalogue.record(self.db, detailed("a", city="Cordova", state="TN"))
        self.assertEqual(self.shown()[0]["where"], "Cordova")

    def test_a_private_car_far_away_is_shown_with_how_far_and_left_to_the_pages_filter(self):
        catalogue.record(self.db, detailed("near", lat=35.0312, lon=-89.8124))
        catalogue.record(self.db, detailed("far", lat=33.5162, lon=-90.1795))          # Greenwood, Mississippi
        catalogue.record(self.db, detailed("unpinned"))
        self.assertEqual([(one["id"], one["dealer_miles"]) for one in self.shown()],
                         [("memphis.craigslist.org:far", 113.1), ("memphis.craigslist.org:near", 15.7),
                          ("memphis.craigslist.org:unpinned", None)])

    def test_one_listing_that_two_craigslist_cities_both_show_is_one_car(self):
        jonesboro = {"key": "jonesboro.craigslist.org", "kind": "craigslist", "site": "jonesboro", "name": "Craigslist: Jonesboro"}
        catalogue.record(self.db, detailed("abc"))
        catalogue.record(self.db, {**detailed("abc"), "id": "jonesboro.craigslist.org:abc", "source": "jonesboro.craigslist.org"})
        catalogue.record(self.db, detailed("other"))
        shown = build.page_data(self.db, [], NOW, places=[CRAIGSLIST, jonesboro], area=AREA)["cars"]
        self.assertEqual([(one["source_id"] if "source_id" in one else one["id"], one["places"], one["also"]) for one in shown],
                         [("jonesboro.craigslist.org:abc", 2, ["memphis.craigslist.org"]), ("memphis.craigslist.org:other", 1, [])])

    def test_days_listed_counts_from_when_the_seller_posted(self):
        catalogue.record(self.db, detailed("a", "2026-11-21T05:00", posted="2026-11-18T23:30"))
        self.assertEqual(self.shown(now="2026-11-25T05:00")[0]["days"], 7)

    def test_a_car_whose_title_is_not_clean_is_shown_but_not_judged_or_used_to_judge(self):
        catalogue.record(self.db, detailed("clean"))
        catalogue.record(self.db, detailed("rebuilt", title_status="rebuilt"))
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        given = []
        shown = self.shown(judge=lambda cars, year: given.extend(car["id"] for car in cars) or {
            "memphis.craigslist.org:rebuilt": {"typical": 9000, "similar": 4}})
        self.assertEqual(given, ["memphis.craigslist.org:clean", "peckdaniel.com:1"])
        self.assertEqual([(one["id"], one["title_status"], one["typical"]) for one in shown],
                         [("memphis.craigslist.org:clean", "clean", None), ("memphis.craigslist.org:rebuilt", "rebuilt", None),
                          ("peckdaniel.com:1", None, None)])

    def test_the_page_lists_the_places_read_beside_the_dealers(self):
        catalogue.record(self.db, detailed("a"))
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        data = build.page_data(self.db, [PECK], NOW, places=[CRAIGSLIST], area=AREA, report=[
            {"dealer": "peckdaniel.com", "ok": True}, {"dealer": "memphis.craigslist.org", "ok": True}])
        self.assertEqual(data["dealers"], [
            {"key": "peckdaniel.com", "name": "Peck Daniel Auto Sales", "cars": 1, "ok": True},
            {"key": "memphis.craigslist.org", "name": "Craigslist, by owner", "cars": 1, "ok": True}])

    def test_a_car_on_two_dealers_sites_counts_for_both_and_says_where_else_it_is(self):
        # 2026-11-21: Gossett's three sites list one pool of cars, and two of the three showed no cars at all
        catalogue.record(self.db, car("peckdaniel.com", "1", vin="1HGCM82633A004352", price=6500))
        catalogue.record(self.db, car("jimkerasnissan.com", "9", vin="1HGCM82633A004352", price=6500))
        catalogue.record(self.db, car("jimkerasnissan.com", "8"))
        data = build.page_data(self.db, [PECK, KERAS], NOW, report=[
            {"dealer": "peckdaniel.com", "ok": True}, {"dealer": "jimkerasnissan.com", "ok": True}])
        self.assertEqual([(one["id"], one["places"], one["also"]) for one in data["cars"]],
                         [("jimkerasnissan.com:8", 1, []), ("jimkerasnissan.com:9", 2, ["peckdaniel.com"])])
        self.assertEqual([(dealer["key"], dealer["cars"]) for dealer in data["dealers"]],
                         [("peckdaniel.com", 1), ("jimkerasnissan.com", 2)])

    def test_the_funnel_says_how_many_of_each_sources_listings_reach_the_page(self):
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        catalogue.record(self.db, car("peckdaniel.com", "2", price=None))
        catalogue.record(self.db, car("jimkerasnissan.com", "9", price=None))      # Imports of Memphis: no asking prices
        catalogue.record(self.db, detailed("far", lat=33.5162, lon=-90.1795))        # far, and on the page all the same
        data = build.page_data(self.db, [PECK, KERAS], NOW, places=[CRAIGSLIST], area=AREA)
        self.assertEqual(build.funnel(self.db, data), [
            {"source": "jimkerasnissan.com", "live": 1, "priced": 0, "shown": 0},
            {"source": "memphis.craigslist.org", "live": 1, "priced": 1, "shown": 1},
            {"source": "peckdaniel.com", "live": 2, "priced": 1, "shown": 1}])

    def test_the_page_says_when_it_was_built_and_what_was_read(self):
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        data = build.page_data(self.db, [PECK, KERAS], NOW, report=[{"dealer": "peckdaniel.com", "ok": True, "read": 1}])
        self.assertEqual(data["built"], NOW)
        self.assertEqual(data["dealers"], [{"key": "peckdaniel.com", "name": "Peck Daniel Auto Sales", "cars": 1, "ok": True}])


if __name__ == "__main__":
    unittest.main()
