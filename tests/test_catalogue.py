import unittest

from cartrack import catalogue
from cartrack.listings import make_listing


def camry(source_id="1", seen="2026-11-21T03:03", **fields):
    return make_listing("craigslist", source_id, **{
        "url": f"https://memphis.craigslist.org/cto/d/x/{source_id}.html",
        "title": "2012 Toyota Camry LE",
        "seen": seen,
        "channel": "classified",
        "price": 6500,
        "miles": 134200,
        **fields,
    })


def rows(db, sql, *args):
    return [tuple(row) for row in db.execute(sql, args)]


class Record(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def test_a_new_listing_gets_a_first_price_point_and_a_seen_span(self):
        self.assertEqual(catalogue.record(self.db, camry()), "new")
        self.assertEqual(rows(self.db, "SELECT id, price, first_seen, last_seen, gone FROM listing"),
                         [("craigslist:1", 6500, "2026-11-21T03:03", "2026-11-21T03:03", None)])
        self.assertEqual(rows(self.db, "SELECT observed, price, miles FROM price_point"),
                         [("2026-11-21T03:03", 6500, 134200)])
        self.assertEqual(rows(self.db, "SELECT start, stop FROM seen_span"),
                         [("2026-11-21T03:03", "2026-11-21T03:03")])

    def test_seeing_it_again_unchanged_adds_no_point_and_stretches_the_span(self):
        catalogue.record(self.db, camry())
        self.assertEqual(catalogue.record(self.db, camry(seen="2026-11-21T09:00")), "same")
        self.assertEqual(rows(self.db, "SELECT count(*) FROM price_point"), [(1,)])
        self.assertEqual(rows(self.db, "SELECT start, stop FROM seen_span"),
                         [("2026-11-21T03:03", "2026-11-21T09:00")])
        self.assertEqual(rows(self.db, "SELECT first_seen, last_seen FROM listing"),
                         [("2026-11-21T03:03", "2026-11-21T09:00")])

    def test_a_price_cut_adds_a_point_and_updates_the_listing(self):
        catalogue.record(self.db, camry())
        self.assertEqual(catalogue.record(self.db, camry(seen="2026-11-22T03:00", price=5900)), "changed")
        self.assertEqual(rows(self.db, "SELECT observed, price FROM price_point ORDER BY observed"),
                         [("2026-11-21T03:03", 6500), ("2026-11-22T03:00", 5900)])
        self.assertEqual(rows(self.db, "SELECT price FROM listing"), [(5900,)])

    def test_a_changed_odometer_adds_a_point(self):
        catalogue.record(self.db, camry())
        catalogue.record(self.db, camry(seen="2026-11-22T03:00", miles=135000))
        self.assertEqual(rows(self.db, "SELECT count(*) FROM price_point"), [(2,)])

    def test_a_later_read_that_lacks_a_field_does_not_erase_it(self):
        catalogue.record(self.db, camry(vin="1HGCM82633A004352"))
        catalogue.record(self.db, camry(seen="2026-11-22T03:00"))
        self.assertEqual(rows(self.db, "SELECT vin FROM listing"), [("1HGCM82633A004352",)])

    def test_lists_and_extra_are_stored_as_json(self):
        catalogue.record(self.db, camry(photos=["https://images.example/a.jpg"], extra={"where": "Midtown"}))
        self.assertEqual(rows(self.db, "SELECT photos, extra FROM listing"),
                         [('["https://images.example/a.jpg"]', '{"where": "Midtown"}')])


class CloseOut(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)
        for n in range(1, 11):
            catalogue.record(self.db, camry(str(n)))

    def test_listings_a_whole_read_did_not_find_are_marked_gone(self):
        seen = [f"craigslist:{n}" for n in range(1, 10)]
        self.assertEqual(catalogue.close_out(self.db, "craigslist", seen, "2026-11-22T03:00"), 1)
        self.assertEqual(rows(self.db, "SELECT id, gone, gone_how FROM listing WHERE gone IS NOT NULL"),
                         [("craigslist:10", "2026-11-22T03:00", "unseen")])

    def test_a_read_that_found_under_80_percent_marks_nothing(self):
        seen = [f"craigslist:{n}" for n in range(1, 8)]
        with self.assertRaises(catalogue.Shrunk):
            catalogue.close_out(self.db, "craigslist", seen, "2026-11-22T03:00")
        self.assertEqual(rows(self.db, "SELECT count(*) FROM listing WHERE gone IS NOT NULL"), [(0,)])

    def test_other_sources_are_left_alone(self):
        catalogue.record(self.db, make_listing("ebay", "77", url="https://www.ebay.com/itm/77", title="2015 Ford F-150",
                                               seen="2026-11-21T03:03", channel="marketplace"))
        catalogue.close_out(self.db, "craigslist", [f"craigslist:{n}" for n in range(1, 11)], "2026-11-22T03:00")
        self.assertEqual(rows(self.db, "SELECT count(*) FROM listing WHERE gone IS NOT NULL"), [(0,)])

    def test_a_listing_that_comes_back_is_live_again_with_a_new_span(self):
        catalogue.close_out(self.db, "craigslist", [f"craigslist:{n}" for n in range(1, 10)], "2026-11-22T03:00")
        self.assertEqual(catalogue.record(self.db, camry("10", seen="2026-11-25T03:00")), "back")
        self.assertEqual(rows(self.db, "SELECT gone, gone_how FROM listing WHERE id = 'craigslist:10'"), [(None, None)])
        self.assertEqual(rows(self.db, "SELECT start, stop FROM seen_span WHERE listing_id = 'craigslist:10' ORDER BY start"),
                         [("2026-11-21T03:03", "2026-11-21T03:03"), ("2026-11-25T03:00", "2026-11-25T03:00")])


class AgeOut(unittest.TestCase):
    """A read that is never quite whole (Carvana's count moved under it on 2026-11-21) marks nothing gone, and a
    read that shrank too far marks nothing gone, so without this a sold car could stay on the page for good."""

    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)

    def live(self):
        return [row[0] for row in rows(self.db, "SELECT source_id FROM listing WHERE gone IS NULL ORDER BY source_id")]

    def test_a_listing_no_read_has_found_for_three_days_is_gone(self):
        catalogue.record(self.db, camry("old", "2026-11-21T03:00"))
        for day in ("21", "22", "23", "24"):
            catalogue.record(self.db, camry("kept", f"2026-11-{day}T03:00"))
        self.assertEqual(catalogue.age_out(self.db, "craigslist", "2026-11-23T15:00"), 0)      # two and a half days
        self.assertEqual(catalogue.age_out(self.db, "craigslist", "2026-11-24T03:00"), 1)
        self.assertEqual(self.live(), ["kept"])
        self.assertEqual(rows(self.db, "SELECT gone, gone_how FROM listing WHERE source_id = 'old'"),
                         [("2026-11-24T03:00", "unseen")])

    def test_nothing_ages_out_of_a_source_that_has_not_been_read_since(self):
        catalogue.record(self.db, camry("a", "2026-11-21T03:00"))
        catalogue.record(self.db, camry("b", "2026-11-21T03:00"))
        self.assertEqual(catalogue.age_out(self.db, "craigslist", "2026-11-30T03:00"), 0)      # the source was down
        self.assertEqual(self.live(), ["a", "b"])

    def test_other_sources_are_left_alone(self):
        catalogue.record(self.db, camry("old", "2026-11-21T03:00"))
        catalogue.record(self.db, make_listing("elsewhere", "1", url="https://e/1", title="a car", seen="2026-11-21T03:00",
                                               channel="dealer_site", price=5000))
        catalogue.record(self.db, camry("kept", "2026-11-25T03:00"))
        catalogue.age_out(self.db, "craigslist", "2026-11-25T03:00")
        self.assertEqual(rows(self.db, "SELECT source, source_id FROM listing WHERE gone IS NULL ORDER BY source"),
                         [("craigslist", "kept"), ("elsewhere", "1")])

    def test_a_source_stuck_on_a_read_that_shrank_comes_unstuck(self):
        for name in "abcdefghij":
            catalogue.record(self.db, camry(name, "2026-11-21T03:00"))
        for day in ("22", "23", "24"):
            for name in "abcdef":
                catalogue.record(self.db, camry(name, f"2026-11-{day}T03:00"))
            with self.assertRaises(catalogue.Shrunk):
                catalogue.close_out(self.db, "craigslist", [f"craigslist:{name}" for name in "abcdef"], f"2026-11-{day}T03:00")
        self.assertEqual(catalogue.age_out(self.db, "craigslist", "2026-11-24T03:00"), 4)
        self.assertEqual(catalogue.close_out(self.db, "craigslist", [f"craigslist:{name}" for name in "abcdef"],
                                             "2026-11-24T15:00"), 0)


class Vins(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)
        catalogue.record(self.db, camry("1", vin="1HGCM82633A004352", title="Clean title, runs great"))
        catalogue.record(self.db, camry("2"))

    def test_undecoded_lists_each_vin_not_yet_decoded(self):
        self.assertEqual(catalogue.undecoded(self.db), ["1HGCM82633A004352"])

    def test_a_saved_decode_fills_identity_and_is_not_asked_for_again(self):
        row = {"VIN": "1HGCM82633A004352", "ModelYear": "2003", "Make": "HONDA", "Model": "Accord",
               "Trim": "EX-V6", "BodyClass": "Coupe", "ErrorCode": "0"}
        catalogue.save_decodes(self.db, {"1HGCM82633A004352": row}, "2026-11-21T04:00")
        self.assertEqual(catalogue.undecoded(self.db), [])
        self.assertEqual(
            rows(self.db, "SELECT year, make, model, body, identity_how, vehicle_key FROM listing WHERE id = 'craigslist:1'"),
            [(2003, "honda", "Accord", "coupe", "vin", "2003|honda|accord|ex-v6|coupe||")])

    def test_a_later_read_does_not_put_the_sources_identity_back_over_the_vins(self):
        row = {"VIN": "1HGCM82633A004352", "ModelYear": "2003", "Make": "HONDA", "Model": "Accord", "ErrorCode": "0"}
        catalogue.save_decodes(self.db, {"1HGCM82633A004352": row}, "2026-11-21T04:00")
        catalogue.record(self.db, camry("1", seen="2026-11-22T03:00", vin="1HGCM82633A004352",
                                        year=2004, make="Hondaa", model="Acord"))
        self.assertEqual(
            rows(self.db, "SELECT year, make, model, identity_how, vehicle_key FROM listing WHERE id = 'craigslist:1'"),
            [(2003, "honda", "Accord", "vin", "2003|honda|accord||||")])

    def test_two_listings_with_one_vin_are_one_vehicle(self):
        catalogue.record(self.db, make_listing("ebay", "77", url="https://www.ebay.com/itm/77", title="2003 Honda Accord",
                                               seen="2026-11-23T03:00", channel="marketplace", price=5200,
                                               vin="1HGCM82633A004352"))
        self.assertEqual(
            rows(self.db, "SELECT vehicle_id, listings, low_price, first_seen, last_seen FROM vehicle WHERE listings > 1"),
            [("vin:1HGCM82633A004352", 2, 5200, "2026-11-21T03:03", "2026-11-23T03:00")])

    def test_a_listing_without_a_vin_is_its_own_vehicle(self):
        self.assertEqual(rows(self.db, "SELECT vehicle_id FROM listing WHERE id = 'craigslist:2'"), [("v:craigslist:2",)])


class Dealers(unittest.TestCase):
    def setUp(self):
        self.db = catalogue.open_catalogue(":memory:")
        self.addCleanup(self.db.close)
        self.dealer = {"key": "subarumemphis.com", "name": "Jim Keras Subaru", "host": "subarumemphis.com",
                       "website": "https://www.subarumemphis.com/", "platform": "dealer.com", "reads": "browser",
                       "lat": 35.18172, "lon": -89.89487, "miles": 9.0, "city": "Memphis", "state": "TN",
                       "zip": "38128", "found_by": ["osm"]}

    def test_dealers_are_saved_once_by_key(self):
        catalogue.save_dealers(self.db, [self.dealer], "2026-11-21T03:00")
        catalogue.save_dealers(self.db, [{**self.dealer, "platform": "dealeron", "reads": "plain"}], "2026-11-28T03:00")
        self.assertEqual(rows(self.db, "SELECT key, platform, reads, first_found, last_found, found_by FROM dealer"),
                         [("subarumemphis.com", "dealeron", "plain", "2026-11-21T03:00", "2026-11-28T03:00", '["osm"]')])


class Open(unittest.TestCase):
    def test_opening_an_existing_catalogue_keeps_what_is_in_it(self):
        import os
        import tempfile
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "catalogue.db")
        db = catalogue.open_catalogue(path)
        catalogue.record(db, camry())
        db.close()
        db = catalogue.open_catalogue(path)
        self.addCleanup(lambda: (db.close(), os.remove(path), os.rmdir(folder)))
        self.assertEqual(rows(db, "SELECT count(*) FROM listing"), [(1,)])


if __name__ == "__main__":
    unittest.main()
