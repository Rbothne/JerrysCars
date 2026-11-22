import threading
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
                                       "title_status": "clean", "extra": {"makemodel": "toyota camry le", "flags": []}, **fields})


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


IMPOUND = {"key": "venture-auctions.com", "kind": "auctioneersoftware", "site": "https://www.venture-auctions.com",
           "name": "City of Memphis impound auction", "floor": 0, "premium": 0.1, "fee": 10, "card": 0.04, "ready": 1500}


def lot(source_id, seen=NOW, **fields):
    return make_listing("venture-auctions.com", source_id, **{
        "url": f"https://www.venture-auctions.com/auctions/5361/lot/{source_id}", "title": "2012 TOYOTA CAMRY LE SEDAN",
        "seen": seen, "channel": "auction", "price": 900, "price_kind": "sold", "ends": "2026-11-18T15:47",
        "year": 2012, "make": "toyota", "model": "Camry", "extra": {"auction": "Impound 11/18", "lot": "1", "bids": 3},
        **fields})


class Auctions(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)
        self.known = []

    def run_build(self, *lots, now=NOW):
        def read(place, get, seen, known=()):
            self.known.append(set(known))
            return [dict(one, seen=seen) for one in lots], True
        return build.read_sources(self.db, [IMPOUND], {"auctioneersoftware": read}, None, now, say=lambda line: None)

    def ended(self):
        return [tuple(row) for row in self.db.execute("SELECT source_id, gone, gone_how FROM listing ORDER BY source_id")]

    def test_a_lot_with_a_result_is_over_from_the_moment_it_is_recorded_and_says_how(self):
        self.run_build(lot("5361-1"), lot("5361-2", price=500, price_kind="reserve_not_met", ends="2026-11-18T16:10"),
                       lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30"))
        self.assertEqual(self.ended(), [("5361-1", "2026-11-18T15:47", "sold"), ("5361-2", "2026-11-18T16:10", "ended_unsold"),
                                        ("5362-1", None, None)])

    def test_the_reader_is_told_which_lots_are_already_recorded_as_over(self):
        self.run_build(lot("5361-1"), lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30"))
        self.run_build(lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30"), now="2026-11-22T05:00")
        self.assertEqual(self.known, [set(), {"5361-1"}])

    def test_a_coming_lot_that_turns_up_sold_is_closed_and_the_sold_ones_stay_closed(self):
        self.run_build(lot("5362-1", price=450, price_kind="bid", ends="2026-11-25T15:30"))
        report = self.run_build(lot("5362-1", price=700, ends="2026-11-25T15:52"), now="2026-11-25T23:00")
        self.assertEqual(self.ended(), [("5362-1", "2026-11-25T15:52", "sold")])
        report = self.run_build(now="2026-11-26T11:00")              # nothing coming, nothing new: an ordinary week
        self.assertEqual((report[0]["ok"], self.ended()), (True, [("5362-1", "2026-11-25T15:52", "sold")]))

    def test_an_auction_lot_is_not_among_the_cars_for_sale(self):
        self.run_build(lot("5361-1"), lot("5362-1", price=450, price_kind="bid", ends="2026-11-25T15:30"))
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        shown = build.page_data(self.db, [PECK], NOW, places=[IMPOUND], area=AREA)["cars"]
        self.assertEqual([one["id"] for one in shown], ["peckdaniel.com:1"])

    def test_the_auction_page_gets_the_coming_lots_and_every_result_newest_first(self):
        self.run_build(lot("5360-9", ends="2026-11-11T15:40", price=650), lot("5361-1"),
                       lot("5361-2", price=500, price_kind="reserve_not_met", ends="2026-11-18T16:10"),
                       lot("5362-1", price=450, price_kind="bid", ends="2026-11-25T15:30", vin="1HGCM82633A004352",
                           photos=["https://images.example/a.jpg"], extra={"auction": "Impound 11/25", "lot": "7", "bids": 4}))
        data = build.auction_data(self.db, [CRAIGSLIST, IMPOUND], NOW)
        self.assertEqual(data["built"], NOW)
        self.assertEqual(data["places"], [{"key": "venture-auctions.com", "name": "City of Memphis impound auction",
                                           "premium": 0.1, "fee": 10, "card": 0.04, "ready": 1500}])
        self.assertEqual(data["assume"]["title"], 180)
        self.assertEqual([(one["id"], one["price"], one["sold"]) for one in data["results"]],
                         [("venture-auctions.com:5361-2", 500, False), ("venture-auctions.com:5361-1", 900, True),
                          ("venture-auctions.com:5360-9", 650, True)])
        coming = data["lots"][0]
        self.assertEqual({name: coming[name] for name in ("id", "title", "price", "kind", "bids", "ends", "auction", "lot",
                                                          "vin", "photo", "place", "parts_only")},
                         {"id": "venture-auctions.com:5362-1", "title": "2012 TOYOTA CAMRY LE SEDAN", "price": 450, "kind": "bid",
                          "bids": 4, "ends": "2026-11-25T15:30", "auction": "Impound 11/25", "lot": "7",
                          "vin": "1HGCM82633A004352", "photo": "https://images.example/a.jpg",
                          "place": "venture-auctions.com", "parts_only": False})

    def test_a_coming_lot_is_set_beside_what_such_cars_fetched_here_and_what_they_ask(self):
        self.run_build(lot("5360-1", price=600), lot("5360-2", price=900, year=2014), lot("5360-3", price=1500, year=2010),
                       lot("5360-4", price=4000, year=2020),                       # eight model years off: not the same car
                       lot("5360-5", price=300, price_kind="reserve_not_met"),     # no sale: not a price anyone paid
                       lot("5360-6", price=700, model="Corolla"),
                       lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30"))
        for number, asking in enumerate((6500, 7500, 8000)):
            catalogue.record(self.db, car("peckdaniel.com", str(number), price=asking))
        catalogue.record(self.db, car("peckdaniel.com", "new", price=31000, year=2024))
        coming = build.auction_data(self.db, [IMPOUND], NOW)["lots"][0]
        self.assertEqual(coming["before"], {"count": 3, "median": 900, "low": 600, "high": 1500})
        self.assertEqual(coming["asks"], {"count": 3, "median": 7500, "low": 6500, "high": 8000})
        self.assertIsNone(coming["back"])

    def test_a_lot_with_nothing_to_set_it_beside_says_nothing(self):
        self.run_build(lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30", model="Avalon"))
        coming = build.auction_data(self.db, [IMPOUND], NOW)["lots"][0]
        self.assertEqual((coming["before"], coming["asks"], coming["back"]), (None, None, None))

    def test_a_car_back_from_an_earlier_sale_says_when_and_how_that_ended(self):
        self.run_build(lot("5359-4", vin="1HGCM82633A004352", price=800, ends="2026-11-04T15:40"),
                       lot("5361-2", vin="1HGCM82633A004352", price=500, price_kind="reserve_not_met", ends="2026-11-18T16:10"),
                       lot("5362-1", vin="1HGCM82633A004352", price=10, price_kind="starting", ends="2026-11-25T15:30"))
        coming = build.auction_data(self.db, [IMPOUND], NOW)["lots"][0]
        self.assertEqual(coming["back"], {"when": "2026-11-18", "price": 500, "sold": False})

    def test_the_funnel_counts_an_auctions_coming_lots_as_shown(self):
        self.run_build(lot("5361-1"), lot("5362-1", price=10, price_kind="starting", ends="2026-11-25T15:30"))
        data = build.page_data(self.db, [], NOW, places=[IMPOUND], area=AREA)
        self.assertEqual(build.funnel(self.db, data, build.auction_data(self.db, [IMPOUND], NOW)),
                         [{"source": "venture-auctions.com", "live": 1, "priced": 1, "shown": 1}])


class SideBySide(unittest.TestCase):
    """Every source is asked at once, each at its own site's pace, so a run takes as long as its slowest site
    and not as long as all of them added up."""

    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def test_two_sources_are_being_read_at_the_same_moment(self):
        together = threading.Barrier(2, timeout=5)      # each reader waits here for the other: alone it would time out

        def dealer(dealer, get, seen):
            together.wait()
            return [car(dealer["host"], "1", seen)], True

        def place(place, get, seen, known=()):
            together.wait()
            return [detailed("a", seen)], True
        jobs = (build.source_jobs(self.db, [CRAIGSLIST], {"craigslist": place}, None, NOW)
                + build.dealer_jobs([PECK], {"autorevo": dealer}, None, NOW))
        report = build.run(self.db, jobs, NOW, say=lambda line: None, workers=8)
        self.assertEqual([(line["dealer"], line["ok"], line["read"]) for line in report],
                         [("memphis.craigslist.org", True, 1), ("peckdaniel.com", True, 1)])
        self.assertEqual(self.db.execute("SELECT count(*) FROM listing").fetchone()[0], 2)

    def test_the_report_keeps_the_order_the_sources_were_given_in_whichever_finishes_first(self):
        first_may_go = threading.Event()

        def slow(dealer, get, seen):
            first_may_go.wait(5)
            return [car(dealer["host"], "1", seen)], True

        def quick(dealer, get, seen):
            first_may_go.set()
            return [car(dealer["host"], "9", seen)], True
        report = build.read_dealers(self.db, [PECK, KERAS], {"autorevo": slow, "dealeron": quick}, None, NOW,
                                    say=lambda line: None, workers=8)
        self.assertEqual([line["dealer"] for line in report], ["peckdaniel.com", "jimkerasnissan.com"])

    def test_a_reader_that_fails_beside_others_is_reported_for_its_own_source_only(self):
        def broken(dealer, get, seen):
            raise readers.NotRead("no cars on the page")
        report = build.read_dealers(self.db, [PECK, KERAS], {"autorevo": broken, "dealeron": reader("9")}, None, NOW,
                                    say=lambda line: None, workers=8)
        self.assertEqual([(line["dealer"], line["ok"]) for line in report],
                         [("peckdaniel.com", False), ("jimkerasnissan.com", True)])
        self.assertIn("no cars on the page", report[0]["error"])


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

    def test_a_rebuilt_salvage_or_lien_title_is_priced_against_clean_cars_and_kept_apart_from_them(self):
        catalogue.record(self.db, detailed("clean"))
        catalogue.record(self.db, detailed("rebuilt", title_status="rebuilt"))
        catalogue.record(self.db, detailed("lien", title_status="lien"))
        catalogue.record(self.db, detailed("parts", title_status="parts_only"))
        catalogue.record(self.db, detailed("none", title_status="missing"))
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        given = []
        shown = self.shown(judge=lambda cars, year: given.extend((car["id"].split(":")[1], car["apart"], car["seller"])
                                                                 for car in cars) or {
            car["id"]: {"typical": 9000, "similar": 4, "basis": "wide", "window": (4, 60000), "low": 7600, "high": 13200}
            for car in cars})
        self.assertEqual(given, [("clean", False, "private"), ("lien", True, "private"), ("rebuilt", True, "private"),
                                 ("1", False, "dealer")])
        self.assertEqual({one["id"].split(":")[1]: one["typical"] for one in shown},
                         {"clean": 9000, "lien": 9000, "rebuilt": 9000, "parts": None, "none": None, "1": 9000})

    def figured(self, **found):
        """One private car asking $4,850, judged as `found` says."""
        catalogue.record(self.db, detailed("a", price=4850))
        answer = {"typical": 4600, "resale": 4624, "similar": 4, "basis": "close", "window": (2, 30000),
                  "low": 4100, "high": 5800, **found}
        return self.shown(judge=lambda cars, year: {car["id"]: answer for car in cars})[0]

    def test_a_car_judged_from_similar_cars_says_what_to_pay_to_have_a_thousand_left(self):
        # research/11-profit-estimate.md: a Terrain asked $4,850 would have to be bought at about $2,300
        shown = self.figured()
        self.assertEqual((shown["pay"], shown["pay_low"], shown["pay_high"], shown["far_under"]), (2300, 1900, 3300, False))
        self.assertEqual(build.page_data(self.db, [], NOW)["assume"]["left"], 1000)

    def test_a_rough_figure_gives_no_price_to_pay(self):
        shown = self.figured(basis="rough", window=None, similar=0)
        self.assertEqual((shown["pay"], shown["pay_low"], shown["pay_high"]), (None, None, None))

    def test_a_car_asking_far_under_the_others_is_told_apart_from_a_bargain(self):
        shown = self.figured(typical=14100, resale=14100, low=12700, high=17600)
        self.assertEqual((shown["far_under"], shown["pay"]), (True, None))

    def test_a_car_not_worth_enough_to_leave_the_sum_has_no_price_to_pay(self):
        shown = self.figured(typical=1500, resale=1500, low=1300, high=1900)
        self.assertEqual((shown["pay"], shown["far_under"]), (None, False))

    def test_a_branded_title_or_a_stated_fault_gives_no_price_to_pay(self):
        catalogue.record(self.db, detailed("b", price=4850, title_status="rebuilt"))
        catalogue.record(self.db, detailed("c", price=4850, condition="fair"))
        self.figured()
        answer = {"typical": 4600, "resale": 4624, "similar": 4, "basis": "close", "window": (2, 30000), "low": 4100, "high": 5800}
        shown = self.shown(judge=lambda cars, year: {car["id"]: answer for car in cars})
        self.assertEqual([one["pay"] for one in shown], [2300, None, None])

    def test_a_car_says_what_its_figure_stands_on(self):
        catalogue.record(self.db, car("peckdaniel.com", "1"))
        catalogue.record(self.db, car("peckdaniel.com", "2"))
        first, second = self.shown(judge=lambda cars, year: {
            "peckdaniel.com:1": {"typical": 9000, "similar": 4, "basis": "wide", "window": (4, 60000), "low": 8500, "high": 10700}})
        self.assertEqual({name: first[name] for name in ("typical", "similar", "basis", "window", "low", "high")},
                         {"typical": 9000, "similar": 4, "basis": "wide", "window": (4, 60000), "low": 8500, "high": 10700})
        self.assertEqual({name: second[name] for name in ("typical", "similar", "basis", "window", "low", "high")},
                         {"typical": None, "similar": None, "basis": None, "window": None, "low": None, "high": None})

    def test_a_private_car_whose_own_title_says_why_it_is_cheap_carries_the_warning_and_is_not_judged(self):
        # top of the page on 2026-11-21: "2020 Chrysler Pacifica - Mechanic Special / As-Is - $3,500", "$6,200 under"
        unread = {"extra": {"makemodel": "as typed"}}       # read before descriptions were: the title is all there is
        catalogue.record(self.db, detailed("a", title="2020 Chrysler Pacifica \u2013 Mechanic Special / As-Is \u2013 $3,500", **unread))
        catalogue.record(self.db, detailed("b", title="2009 Chevy Impala LT - AS IS - Needs Major Work", **unread))
        catalogue.record(self.db, detailed("c", title="2012 toyota camry le, needs nothing, new tires", **unread))
        catalogue.record(self.db, detailed("d", title="2004 Ford Ranger wont start, for parts or project, no title", **unread))
        catalogue.record(self.db, car("peckdaniel.com", "1", title="2014 Ford F-150 AS-IS Special"))      # a dealer's own wording
        given = []
        shown = self.shown(judge=lambda cars, year: given.extend(car["id"] for car in cars) or {
            car["id"]: {"typical": 9000, "similar": 4} for car in cars})
        self.assertEqual([one["cautions"] for one in shown],
                         [["not running"], ["needs work"], [], ["not running", "no title"], []])
        self.assertEqual(given, ["memphis.craigslist.org:c", "peckdaniel.com:1"])
        self.assertEqual([one["typical"] for one in shown], [None, None, 9000, None, 9000])

    def test_once_a_listings_own_page_has_been_read_for_faults_its_flags_stand_and_the_title_is_not_guessed_from(self):
        catalogue.record(self.db, detailed("a", title="Honda Accord, needs nothing", condition="good", extra={
            "makemodel": "honda accord", "flags": ["mechanical_fault", "damage", "trade_seller"], "pin": 22}))
        catalogue.record(self.db, detailed("b", title="Mechanic special", extra={"makemodel": "ford focus", "flags": []}))
        catalogue.record(self.db, detailed("c", condition="fair", extra={"makemodel": "kia rio", "flags": [], "pin": 7}))
        first, second, third = self.shown(judge=lambda cars, year: {car["id"]: {"typical": 9000, "similar": 4} for car in cars})
        self.assertEqual((first["cautions"], first["notes"], first["approx"], first["typical"]),
                         (["a mechanical fault"], ["damage mentioned", "reads like a trader's advert"], True, None))
        self.assertEqual((second["cautions"], second["notes"], second["approx"], second["typical"]), ([], [], False, 9000))
        self.assertEqual((third["cautions"], third["approx"], third["typical"]), (["condition: fair"], False, None))

    def test_two_listings_that_share_a_photo_are_one_car_whatever_else_differs(self):
        # 2026-11-21: photo ids found 22 reposted cars; year, miles, price and pin missed a price raised by $950
        catalogue.record(self.db, detailed("first", price=4850, photo_ids=["aaa", "bbb"]))
        catalogue.record(self.db, detailed("again", price=5800, year=2013, photo_ids=["bbb", "ccc"]))
        catalogue.record(self.db, detailed("third", price=5800, photo_ids=["ccc"]))
        catalogue.record(self.db, detailed("other", price=4850, photo_ids=["zzz"]))
        shown = self.shown()
        self.assertEqual([(one["id"], one["price"], one["places"]) for one in shown],
                         [("memphis.craigslist.org:first", 4850, 3), ("memphis.craigslist.org:other", 4850, 1)])

    def test_the_reader_is_asked_again_for_a_classified_whose_page_was_read_before_its_words_were(self):
        catalogue.record(self.db, detailed("old", extra={"makemodel": "toyota camry le"}))
        catalogue.record(self.db, detailed("new"))
        seen = []

        def read(place, get, when, known=()):
            seen.append(set(known))
            return [], True
        build.read_sources(self.db, [CRAIGSLIST], {"craigslist": read}, None, NOW, say=lambda line: None)
        self.assertEqual(seen, [{"new"}])

    def test_one_car_posted_twice_by_its_seller_is_shown_once_and_says_so(self):
        # 2026-11-21: "Jeep Cherokee overland 3.0 L Diesel 2014" twice, 123,340 miles and $5,000 both times, one pin
        same = {"year": 2014, "miles": 123340, "price": 5000, "lat": 37.43, "lon": -90.96}
        catalogue.record(self.db, detailed("first", title="Jeep Cherokee overland 3.0 L Diesel 2014", posted="2026-11-01T15:00", **same))
        catalogue.record(self.db, detailed("again", title="Jeep Cherokee overland 3.0L Diesel 2014", posted="2026-11-03T15:00", **same))
        catalogue.record(self.db, detailed("other", title="2014 Jeep Cherokee", **{**same, "miles": 98000}))
        catalogue.record(self.db, detailed("unpinned", **{**same, "lat": None, "lon": None}))
        shown = self.shown()
        self.assertEqual([(one["id"], one["places"], one["also"]) for one in shown],
                         [("memphis.craigslist.org:again", 2, []), ("memphis.craigslist.org:other", 1, []),
                          ("memphis.craigslist.org:unpinned", 1, [])])

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
