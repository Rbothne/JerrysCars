import json
import pathlib
import unittest

from cartrack import readers
from cartrack.readers import autorevo, dealercarsearch, dealeron

FIXTURES = pathlib.Path(__file__).parent / "fixtures"      # all cut from real Memphis dealer pages, 2026-11-20
SEEN = "2026-11-21T05:00"


def pages(table):
    """A `get` that answers from `table` ({address: fixture file name or bytes}) and remembers what was asked."""
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table[url]
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


class Common(unittest.TestCase):
    def test_site_is_the_dealers_own_address_without_a_path(self):
        self.assertEqual(readers.site({"host": "jimkerasnissan.com", "website": "https://www.jimkerasnissan.com/used/"}),
                         "https://www.jimkerasnissan.com")

    def test_site_without_a_website_guesses_www(self):
        self.assertEqual(readers.site({"host": "901scm.com", "website": None}), "https://www.901scm.com")

    def test_history_finds_the_free_report_and_what_carfaxs_badge_says(self):
        card = ('<a href="https://www.carfax.com/vehiclehistory/ar20/abc_DEF-1" target="_blank">'
                '<img src="https://partnerstatic.carfax.com/img/valuebadge/1own_good.svg"></a>')
        self.assertEqual(readers.history(card), {"history_url": "https://www.carfax.com/vehiclehistory/ar20/abc_DEF-1",
                                                 "one_owner": True, "carfax_value": "good"})

    def test_history_reads_a_value_badge_that_claims_no_single_owner(self):
        card = '<img src="https://partnerstatic.carfax.com/img/valuebadge/great.svg">'
        self.assertEqual(readers.history(card), {"carfax_value": "great"})

    def test_history_with_only_the_show_me_badge_gives_just_the_report(self):
        card = ('<a href="https://www.carfax.com/vehiclehistory/ar20/abc"><img src="https://partnerstatic.carfax.com'
                '/img/valuebadge/showme.svg"></a>')
        self.assertEqual(readers.history(card), {"history_url": "https://www.carfax.com/vehiclehistory/ar20/abc"})

    def test_history_reads_addresses_escaped_for_json_or_html(self):
        self.assertEqual(readers.history('"link":"https:\\/\\/www.carfax.com\\/vehiclehistory\\/ar20\\/abc"'),
                         {"history_url": "https://www.carfax.com/vehiclehistory/ar20/abc"})
        self.assertEqual(readers.history('<a href="https://www.carfax.com/cfm/check_order.cfm?partner=DCS_2&amp;vin=X1">'),
                         {"history_url": "https://www.carfax.com/cfm/check_order.cfm?partner=DCS_2&vin=X1"})

    def test_history_of_a_card_that_says_nothing_is_empty(self):
        self.assertEqual(readers.history('<img src="https://images.example/car.jpg">'), {})

    def test_every_reader_is_registered_under_its_platform(self):
        self.assertEqual(set(readers.READERS), {"dealeron", "autorevo", "dealercarsearch", "teamvelocity", "dealerfire",
                                                "dealeralchemist", "dealercenter", "carsforsale", "carvana"})


class DealerOn(unittest.TestCase):
    DEALER = {"host": "jimkerasnissan.com", "website": "https://www.jimkerasnissan.com/", "name": "Jim Keras Nissan",
              "city": "Memphis", "state": "TN", "zip": "38128", "lat": 35.18172, "lon": -89.89487}
    FIRST = "https://www.jimkerasnissan.com/searchused.aspx"
    API = ("https://www.jimkerasnissan.com/api/vhcliaa/vehicle-pages/cosmos/srp/vehicles/11814/2563574"
           "?host=www.jimkerasnissan.com&pn=96&pt=")

    def read(self, table=None):
        self.get = pages(table or {self.FIRST: "dealeron_searchused.html", self.API + "1": "dealeron_srp.json"})
        return dealeron.read(self.DEALER, self.get, SEEN)

    def test_asks_the_search_page_for_its_ids_then_the_inventory_service(self):
        self.read()
        self.assertEqual(self.get.asked, [self.FIRST, self.API + "1"])

    def test_reads_the_real_cruze(self):
        found, complete = self.read()
        cruze = found[0]
        self.assertEqual(cruze["id"], "jimkerasnissan.com:1G1PA5SHXD7214401")
        self.assertEqual((cruze["year"], cruze["make"], cruze["model"], cruze["trim"]), (2013, "chevrolet", "Cruze", "LS"))
        self.assertEqual((cruze["vin"], cruze["miles"], cruze["body"], cruze["color"]),
                         ("1G1PA5SHXD7214401", 153496, "sedan", "Atlantis Blue Metallic"))
        self.assertEqual(cruze["url"], "https://www.jimkerasnissan.com/used-Memphis-2013-Chevrolet-Cruze-LS-1G1PA5SHXD7214401")
        self.assertEqual(cruze["title"], "2013 Chevrolet Cruze LS")
        self.assertEqual(cruze["posted"], "2026-10-24T00:00")
        self.assertEqual(cruze["photo_count"], 90)
        self.assertTrue(complete)

    def test_the_price_is_the_internet_price_and_the_rest_of_the_stack_is_kept(self):
        cruze = self.read()[0][0]
        self.assertEqual(cruze["price"], 3740)
        self.assertEqual(cruze["extra"]["prices"]["MSRP"], 6999.0)
        self.assertEqual(cruze["extra"]["prices"]["calc_Dealer Doc Fee"], 899.0)
        self.assertEqual(cruze["extra"]["stock"], "S2669301A")

    def test_the_photo_is_the_cards_own_on_the_dealers_site(self):
        self.assertEqual(self.read()[0][0]["photos"],
                         ["https://www.jimkerasnissan.com/inventoryphotos/13757/1g1pa5shxd7214401/ip/thumbs/1.jpg"])

    def test_a_card_that_is_not_a_vehicle_is_skipped(self):
        self.assertEqual(len(self.read()[0]), 2)

    def test_the_dealer_is_the_seller_and_the_place(self):
        cruze = self.read()[0][0]
        self.assertEqual((cruze["channel"], cruze["seller_type"], cruze["seller_name"], cruze["seller_id"]),
                         ("dealer_site", "dealer", "Jim Keras Nissan", "jimkerasnissan.com"))
        self.assertEqual((cruze["city"], cruze["state"], cruze["zip"], cruze["lat"]), ("Memphis", "TN", "38128", 35.18172))

    def test_every_page_the_service_says_exists_is_read(self):
        payload = json.loads((FIXTURES / "dealeron_srp.json").read_text(encoding="utf-8"))
        payload["Paging"]["PaginationDataModel"].update(TotalPages=2, TotalCount=4)
        page = json.dumps(payload).encode()
        found, complete = self.read({self.FIRST: "dealeron_searchused.html", self.API + "1": page, self.API + "2": page})
        self.assertEqual(self.get.asked[1:], [self.API + "1", self.API + "2"])
        self.assertEqual(len(found), 4)
        self.assertTrue(complete)

    def test_fewer_cars_than_the_service_counted_is_not_a_whole_read(self):
        payload = json.loads((FIXTURES / "dealeron_srp.json").read_text(encoding="utf-8"))
        payload["Paging"]["PaginationDataModel"].update(TotalPages=1, TotalCount=9)
        found, complete = self.read({self.FIRST: "dealeron_searchused.html", self.API + "1": json.dumps(payload).encode()})
        self.assertFalse(complete)

    def test_a_search_page_without_ids_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.FIRST: b"<html>Access Denied</html>"})


class AutoRevo(unittest.TestCase):
    DEALER = {"host": "peckdaniel.com", "website": "https://peckdaniel.com/", "name": "Peck Daniel Auto Sales",
              "city": "Memphis", "state": "TN", "zip": None, "lat": None, "lon": None}
    INVENTORY = "https://peckdaniel.com/inventory"
    SITEMAP = "https://peckdaniel.com/sitemap.xml"

    def read(self, table=None):
        self.get = pages(table or {self.INVENTORY: "autorevo_inventory.html", self.SITEMAP: "autorevo_sitemap.xml"})
        return autorevo.read(self.DEALER, self.get, SEEN)

    def test_reads_the_real_mdx(self):
        found, complete = self.read()
        mdx = found[0]
        self.assertEqual(mdx["id"], "peckdaniel.com:7510820")
        self.assertEqual((mdx["year"], mdx["make"], mdx["model"], mdx["trim"]), (2016, "acura", "MDX", "w/Tech"))
        self.assertEqual((mdx["price"], mdx["miles"], mdx["vin"], mdx["drive"]), (10900, 160014, "5FRYD3H40GB006620", "fwd"))
        self.assertEqual(mdx["engine"], "3.5l v6 290hp 267ft. lbs.")
        self.assertEqual(mdx["title"], "2016 Acura MDX w/Tech")
        self.assertEqual(
            mdx["url"],
            "https://peckdaniel.com/2016-acura-mdx-w%2Ftech-%7C-memphis%2C-tn-%7C-peck-daniel-auto-sales-memphis-tn-38115/7510820")
        self.assertTrue(mdx["photos"][0].startswith("https://cf-img.autorevo.com/2016-acura-mdx-memphis-tn-7510820/"))

    def test_a_dash_means_the_dealer_left_it_blank(self):
        self.assertIsNone(self.read()[0][0]["color"])

    def test_as_many_cars_as_the_sitemap_lists_is_a_whole_read(self):
        found, complete = self.read()
        self.assertEqual(len(found), 2)
        self.assertTrue(complete)

    def test_a_sitemap_listing_more_cars_than_the_page_showed_is_not_a_whole_read(self):
        sitemap = (FIXTURES / "autorevo_sitemap.xml").read_text(encoding="utf-8").replace(
            "</urlset>", "<url><loc>https://peckdaniel.com/2014-ford-f-150/7517382</loc></url></urlset>")
        found, complete = self.read({self.INVENTORY: "autorevo_inventory.html", self.SITEMAP: sitemap.encode()})
        self.assertFalse(complete)

    def test_a_page_with_no_cars_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.INVENTORY: b"<html>maintenance</html>", self.SITEMAP: "autorevo_sitemap.xml"})

    def test_a_page_whose_cards_mostly_cannot_be_read_is_an_error(self):
        page = (FIXTURES / "autorevo_inventory.html").read_text(encoding="utf-8")
        empty = '<section class="inventory_item"><p>a card in some new layout</p></section>'
        with self.assertRaises(readers.NotRead) as raised:
            self.read({self.INVENTORY: page.replace("</body>", empty * 9 + "</body>").encode(),
                       self.SITEMAP: "autorevo_sitemap.xml"})
        self.assertIn("only 2 of 11 cards", str(raised.exception))


class Pasts(unittest.TestCase):
    """What the first three readers keep beyond the car itself."""

    def test_autorevo_keeps_the_history_report_and_carfaxs_view_of_the_price(self):
        get = pages({AutoRevo.INVENTORY: "autorevo_inventory.html", AutoRevo.SITEMAP: "autorevo_sitemap.xml"})
        mdx = autorevo.read(AutoRevo.DEALER, get, SEEN)[0][0]
        self.assertEqual(mdx["extra"]["history_url"], "https://www.carfax.com/vehiclehistory/ar20/46BrNKWJFo3Fg7X0DoSZAVnEx08"
                         "TzYgNK7ZVjVPr9eI_kndbScU87UmCuz_WgTWB9GDkufsUFkB9SnfRohx61rk-9PasG9yXN64")
        self.assertEqual(mdx["extra"]["carfax_value"], "good")

    def test_dealeron_names_the_document_fee_as_a_fee(self):
        get = pages({DealerOn.FIRST: "dealeron_searchused.html", DealerOn.API + "1": "dealeron_srp.json"})
        cruze = dealeron.read(DealerOn.DEALER, get, SEEN)[0][0]
        self.assertEqual(cruze["extra"]["fees"], {"Dealer Doc Fee": 899})


class DealerCarSearch(unittest.TestCase):
    DEALER = {"host": "901scm.com", "website": "https://901scm.com/", "name": "Street Cars of Memphis",
              "city": "Memphis", "state": "TN", "zip": "38108", "lat": None, "lon": None}
    INVENTORY = "https://901scm.com/inventory?pagesize=100"

    def read(self, table=None):
        self.get = pages(table or {self.INVENTORY: "dealercarsearch_inventory.html"})
        return dealercarsearch.read(self.DEALER, self.get, SEEN)

    def test_reads_the_real_express(self):
        found, complete = self.read()
        van = found[0]
        self.assertEqual(van["id"], "901scm.com:23721083")
        self.assertEqual((van["year"], van["make"], van["model"], van["trim"]), (2009, "chevrolet", "Express", "RV G3500"))
        self.assertEqual((van["price"], van["miles"], van["vin"], van["drive"]), (13499, 120225, "1GBHG396091173794", "rwd"))
        self.assertEqual((van["color"], van["engine"], van["transmission"]), ("TAN", "6.6l", "automatic"))
        self.assertEqual(van["url"], "https://901scm.com/vdp/23721083/Used-2009-Chevrolet-Express-RV-G3500-for-sale-in-Memphis-TN-38108")
        self.assertEqual(van["title"], "2009 Chevrolet Express RV G3500")
        self.assertEqual(van["extra"]["stock"], "173794")
        self.assertEqual(van["photos"], ["https://imagescdn.dealercarsearch.com/Media/23226/23721083/639104980942327575.jpg"])

    def test_keeps_the_free_history_report_from_imports_of_memphis(self):
        dealer = {**self.DEALER, "host": "importsofmemphis.com", "website": "https://importsofmemphis.com/"}
        get = pages({"https://importsofmemphis.com/inventory?pagesize=100": "dealercarsearch_i17.html"})
        found, _ = dealercarsearch.read(dealer, get, SEEN)
        self.assertIn("https://www.carfax.com/cfm/check_order.cfm?partner=DCS_2&vin=2HNYD28347H514922",
                      [car["extra"].get("history_url") for car in found])

    def test_under_a_full_page_is_a_whole_read(self):
        found, complete = self.read()
        self.assertEqual(len(found), 2)
        self.assertTrue(complete)

    def test_reads_the_template_imports_of_memphis_uses(self):
        dealer = {**self.DEALER, "host": "importsofmemphis.com", "website": "https://importsofmemphis.com/"}
        get = pages({"https://importsofmemphis.com/inventory?pagesize=100": "dealercarsearch_i17.html"})
        mdx = dealercarsearch.read(dealer, get, SEEN)[0][0]
        self.assertEqual(mdx["id"], "importsofmemphis.com:23552238")
        self.assertEqual((mdx["year"], mdx["make"], mdx["model"], mdx["trim"]), (2007, "acura", "MDX Tech Package", None))
        self.assertEqual((mdx["miles"], mdx["vin"], mdx["drive"]), (174917, "2HNYD28347H514922", "awd"))
        self.assertEqual(mdx["title"], "2007 Acura MDX Tech Package")

    def test_an_unlabelled_figure_is_kept_aside_and_not_taken_as_the_asking_price(self):
        # Imports of Memphis showed "$1,699" on a 2017 F-150 4WD: a down payment, with no label saying so.
        dealer = {**self.DEALER, "host": "importsofmemphis.com", "website": "https://importsofmemphis.com/"}
        get = pages({"https://importsofmemphis.com/inventory?pagesize=100": "dealercarsearch_i17.html"})
        mdx = dealercarsearch.read(dealer, get, SEEN)[0][0]
        self.assertIsNone(mdx["price"])
        self.assertEqual(mdx["extra"]["unlabelled_price"], 1599)
        self.assertEqual(mdx["photos"], ["https://imagescdn.dealercarsearch.com/Media/27071/23552238/639271088455497522.jpg"])

    def test_reads_the_template_victory_auto_uses_and_takes_the_retail_price_not_the_fee(self):
        dealer = {**self.DEALER, "host": "victoryauto.org", "website": "https://victoryauto.org/"}
        get = pages({"https://victoryauto.org/inventory?pagesize=100": "dealercarsearch_i08.html"})
        q7 = dealercarsearch.read(dealer, get, SEEN)[0][0]
        self.assertEqual(q7["id"], "victoryauto.org:23882817")
        self.assertEqual((q7["year"], q7["make"], q7["model"], q7["trim"]), (2008, "audi", "Q7", "quattro 4dr 3.6L Premium"))
        self.assertEqual((q7["price"], q7["miles"], q7["vin"], q7["transmission"]), (7995, 112270, "WA1BY74L68D061656", None))

    def cards(self, first, count):
        """A page of `count` cards made from the fixture's first, numbered from `first`."""
        page = (FIXTURES / "dealercarsearch_inventory.html").read_text(encoding="utf-8")
        card = '<div class="invMainCell' + page.split('<div class="invMainCell')[1]
        return ("<html><body>" + "".join(card.replace("23721083", str(first + n)) for n in range(count))
                + "</body></html>").encode()

    def test_a_full_page_of_100_is_followed_by_the_next_until_one_comes_back_short(self):
        # victoryauto.org, 2026-11-21: pagesize=25 gave 25 cards and &page=2 gave 25 others
        found, complete = self.read({self.INVENTORY: self.cards(30000000, 100),
                                     self.INVENTORY + "&page=2": self.cards(30000100, 100),
                                     self.INVENTORY + "&page=3": self.cards(30000200, 7)})
        self.assertEqual(self.get.asked, [self.INVENTORY, self.INVENTORY + "&page=2", self.INVENTORY + "&page=3"])
        self.assertEqual((len(found), len({car["id"] for car in found})), (207, 207))
        self.assertTrue(complete)

    def test_a_lot_of_exactly_100_is_whole_once_the_next_page_comes_back_empty(self):
        found, complete = self.read({self.INVENTORY: self.cards(30000000, 100),
                                     self.INVENTORY + "&page=2": b"<html><body>No vehicles</body></html>"})
        self.assertEqual((len(found), complete), (100, True))

    def test_a_site_that_ignores_the_page_number_is_not_a_whole_read(self):
        same = self.cards(30000000, 100)
        found, complete = self.read({self.INVENTORY: same, self.INVENTORY + "&page=2": same})
        self.assertEqual((len(found), complete), (100, False))

    def test_a_page_whose_cards_mostly_have_no_id_is_an_error(self):
        # the storefront tracker's lesson: a renamed link reads as a nearly empty shop, not as a failure
        page = (FIXTURES / "dealercarsearch_inventory.html").read_text(encoding="utf-8")
        card = '<div class="invMainCell' + page.split('<div class="invMainCell')[1]
        broken = card.replace('href="/vdp/', 'href="/vehicle/')
        with self.assertRaises(readers.NotRead) as raised:
            self.read({self.INVENTORY: f"<html><body>{card}{broken * 5}</body></html>".encode()})
        self.assertIn("only 1 of 6 cards", str(raised.exception))

    def test_a_page_with_no_cars_is_an_error(self):
        with self.assertRaises(readers.NotRead):
            self.read({self.INVENTORY: b"<html>maintenance</html>"})


if __name__ == "__main__":
    unittest.main()
