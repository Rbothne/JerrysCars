import json
import pathlib
import unittest

from cartrack import dealers

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "overpass_memphis.json"   # real OpenStreetMap rows, 2026-11-20
MEMPHIS = {"name": "Memphis, TN", "home": [35.1495, -90.0490], "radius_miles": 60}


def osm():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class HostOf(unittest.TestCase):
    def test_strips_scheme_www_path_and_case(self):
        self.assertEqual(dealers.host_of("https://WWW.SubaruMemphis.com/used/?a=1"), "subarumemphis.com")

    def test_reads_a_bare_host(self):
        self.assertEqual(dealers.host_of("kingcottonford.com"), "kingcottonford.com")

    def test_a_page_on_a_shared_site_is_not_a_dealer_host(self):
        for address in ("https://www.facebook.com/maxautosales", "https://www.tesla.com/findus/location/store/bartlett3020"):
            self.assertIsNone(dealers.host_of(address), address)

    def test_nothing_is_none(self):
        self.assertIsNone(dealers.host_of(None))
        self.assertIsNone(dealers.host_of("  "))


class Geometry(unittest.TestCase):
    def test_memphis_to_southaven_is_about_twelve_miles(self):
        self.assertAlmostEqual(dealers.miles_between((35.1495, -90.0490), (34.9890, -90.0126)), 11.3, delta=0.5)

    def test_the_box_reaches_the_radius_in_every_direction(self):
        south, west, north, east = dealers.box((35.1495, -90.0490), 60)
        self.assertAlmostEqual(dealers.miles_between((35.1495, -90.0490), (north, -90.0490)), 60, delta=0.5)
        self.assertAlmostEqual(dealers.miles_between((35.1495, -90.0490), (35.1495, east)), 60, delta=0.5)
        self.assertLess(south, 35.1495)
        self.assertLess(west, -90.0490)

    def test_the_query_asks_for_car_shops_in_the_box(self):
        query = dealers.overpass_query((34.28, -91.11, 36.02, -88.99))
        self.assertIn('nwr["shop"="car"](34.28,-91.11,36.02,-88.99);', query)
        self.assertIn("out center tags;", query)


class FromOsm(unittest.TestCase):
    def setUp(self):
        self.found = {dealer["name"]: dealer for dealer in dealers.from_osm(osm())}

    def test_a_node_gives_its_own_point_and_address(self):
        ford = self.found["King Cotton Ford"]
        self.assertEqual((ford["lat"], ford["lon"]), (35.58154, -89.64295))
        self.assertEqual((ford["street"], ford["city"], ford["state"], ford["zip"]),
                         ("965 Highway 51 North", "Covington", "TN", "38019"))
        self.assertEqual(ford["host"], "kingcottonford.com")
        self.assertEqual(ford["phone"], "+1-901-476-7111")

    def test_a_way_gives_its_centre(self):
        subaru = self.found["Jim Keras Subaru"]
        self.assertEqual((subaru["lat"], subaru["lon"]), (35.18172, -89.89487))

    def test_a_dealer_with_no_website_is_kept_without_a_host(self):
        self.assertIsNone(self.found["Max Auto Sales"]["host"])
        self.assertIs(self.found["Max Auto Sales"]["used_only"], True)

    def test_a_shop_with_no_name_and_no_website_is_dropped(self):
        self.assertNotIn(None, self.found)
        self.assertEqual(len(self.found), 7)

    def test_each_dealer_says_where_it_was_found(self):
        self.assertEqual(self.found["Jim Keras Subaru"]["found_by"], ["osm"])
        self.assertEqual(self.found["Jim Keras Subaru"]["osm"], "way/302750901")


class Platforms(unittest.TestCase):
    def test_names_seen_in_dns_identify_the_platform(self):
        cases = {
            "le0123.secure.dealer.com.edgekey.net": "dealer.com",
            "www.dealeronsite.com": "dealeron",
            "pod12.dealerinspire.com": "dealerinspire",
            "teamvelocitymarketing.map.fastly.net": "teamvelocity",
            "saas.www.dealereprocess.org": "dealereprocess",
            "e6lb.dealerfire.com": "dealerfire",
            "sites.foxdealer.com.cdn.cloudflare.net": "foxdealer",
        }
        for name, platform in cases.items():
            self.assertEqual(dealers.platform_of(["www.example-dealer.com", name]), platform, name)

    def test_names_that_say_nothing_give_none(self):
        self.assertIsNone(dealers.platform_of(["www.example-dealer.com", "d1234.cloudfront.net"]))

    def test_a_page_identifies_the_platform_by_what_it_loads(self):
        self.assertEqual(dealers.page_platform('<meta name="generator" content="Overfuel">'), "overfuel")
        self.assertEqual(dealers.page_platform('<script src="https://cdn.dlron.us/static/a.js">'), "dealeron")
        self.assertIsNone(dealers.page_platform("<html><body>Hello</body></html>"))

    def test_the_platforms_memphis_independent_lots_use_are_recognised(self):
        # what peckdaniel.com and 901scm.com loaded on 2026-11-20
        self.assertEqual(dealers.page_platform('<img src="https://x-assets.autorevo-powersites.com/a.png">'), "autorevo")
        self.assertEqual(dealers.page_platform('<img src="https://imagescdn.dealercarsearch.com/a.jpg">'), "dealercarsearch")

    def test_the_platforms_found_behind_the_unplaced_memphis_lots_are_recognised(self):
        # what cityauto.com, ezautomemphis.net and colliervilleautocenter.com showed on 2026-11-21
        self.assertEqual(dealers.page_platform('<script src="https://bucket.dealeralchemist.com/a.js">'), "dealeralchemist")
        self.assertEqual(dealers.page_platform('<img src="https://cdn05.carsforsale.com/a.jpg">'), "carsforsale")
        self.assertEqual(dealers.page_platform('<link href="https://x.dealercenterwsstatic.net/a.css">'), "dealercenter")
        self.assertEqual(dealers.platform_of(["www.colliervilleautocenter.com",
                                              "dealers.dealercenterwebsite.net.cdn.cloudflare.net"]), "dealercenter")
        self.assertEqual(dealers.page_platform('<img src="https://assets.fastly.carvana.io/a.svg">'), "carvana")
        for platform in ("dealeralchemist", "carsforsale", "dealercenter", "carvana"):
            self.assertEqual(dealers.READS[platform], "plain", platform)

    def test_a_platform_nobody_has_tested_has_no_reads_entry(self):
        self.assertNotIn("autorevo", dealers.READS)
        self.assertNotIn("dealercarsearch", dealers.READS)

    def test_reads_says_which_platforms_answer_a_plain_request(self):
        self.assertEqual(dealers.READS["dealeron"], "plain")
        self.assertEqual(dealers.READS["dealer.com"], "browser")


class Lookup(unittest.TestCase):
    def test_returns_every_name_dns_gave_for_the_www_host(self):
        def resolve(name):
            self.assertEqual(name, "www.subarumemphis.com")
            return ("le0123.secure.dealer.com.edgekey.net", ["www.subarumemphis.com"], ["23.1.2.3"])
        self.assertEqual(dealers.lookup("subarumemphis.com", resolve),
                         ["le0123.secure.dealer.com.edgekey.net", "www.subarumemphis.com"])

    def test_falls_back_to_the_bare_host(self):
        def resolve(name):
            if name.startswith("www."):
                raise OSError("no such host")
            return ("901scm.com", [], ["1.2.3.4"])
        self.assertEqual(dealers.lookup("901scm.com", resolve), ["901scm.com"])

    def test_a_host_that_does_not_resolve_is_none(self):
        def resolve(name):
            raise OSError("no such host")
        self.assertIsNone(dealers.lookup("gone-dealer.example", resolve))


class Discover(unittest.TestCase):
    def discover(self, seeds=(), pages=None):
        names = {
            "www.subarumemphis.com": ("le0123.secure.dealer.com.edgekey.net", ["www.subarumemphis.com"], []),
            "www.kingcottonford.com": ("www.dealeronsite.com", ["www.kingcottonford.com"], []),
            "www.carvana.com": ("d1.cloudfront.net", ["www.carvana.com"], []),
            "www.landersused.com": ("www.landersused.com", [], []),
        }

        def resolve(name):
            if name not in names:
                raise OSError("no such host")
            return names[name]

        def fetch(url, **options):
            if "overpass" in url:
                self.query = options["data"]
                return FIXTURE.read_bytes()
            self.fetched.append(url)
            if pages and url in pages:
                return pages[url].encode()
            raise OSError("refused")

        self.fetched = []
        found = dealers.discover(MEMPHIS, seeds, fetch=fetch, resolve=resolve)
        return {dealer["key"]: dealer for dealer in found}

    def test_dealers_beyond_the_radius_are_left_out(self):
        self.assertFalse([key for key in self.discover() if "car-mart" in key])

    def test_each_dealer_gets_its_platform_and_distance(self):
        found = self.discover()
        subaru = found["subarumemphis.com"]
        self.assertEqual((subaru["platform"], subaru["reads"]), ("dealer.com", "browser"))
        self.assertAlmostEqual(subaru["miles"], 9.0, delta=0.5)
        self.assertEqual((found["kingcottonford.com"]["platform"], found["kingcottonford.com"]["reads"]), ("dealeron", "plain"))

    def test_a_dealer_with_no_website_is_keyed_by_where_it_was_found(self):
        found = self.discover()
        self.assertEqual(found["osm:node/12546187295"]["name"], "Max Auto Sales")
        self.assertIsNone(found["osm:node/12546187295"]["platform"])

    def test_a_seed_adds_a_dealer_openstreetmap_does_not_have(self):
        found = self.discover([{"name": "Landers Used", "website": "https://www.landersused.com/", "city": "Southaven", "state": "MS"}])
        self.assertEqual(found["landersused.com"]["found_by"], ["seed"])
        self.assertIsNone(found["landersused.com"]["miles"])

    def test_a_seed_for_a_dealer_openstreetmap_has_merges_into_it(self):
        found = self.discover([{"name": "Jim Keras Subaru", "website": "subarumemphis.com"}])
        self.assertEqual(found["subarumemphis.com"]["found_by"], ["osm", "seed"])
        self.assertEqual(found["subarumemphis.com"]["zip"], "38128")

    def test_a_host_dns_cannot_place_is_placed_by_its_front_page(self):
        seeds = [{"name": "Landers Used", "website": "https://www.landersused.com/"}]
        pages = {"https://www.landersused.com/": '<link href="https://static.overfuel.com/a.css">'}
        found = self.discover(seeds, pages)
        self.assertEqual((found["landersused.com"]["platform"], found["landersused.com"]["reads"]), ("overfuel", "plain"))

    def test_front_pages_are_only_fetched_for_hosts_dns_could_not_place(self):
        self.discover()
        self.assertEqual(self.fetched, ["https://www.carvana.com/"])

    def test_a_seed_whose_host_does_not_resolve_is_marked(self):
        found = self.discover([{"name": "Closed Lot", "website": "closed-lot.example"}])
        self.assertIs(found["closed-lot.example"]["resolves"], False)

    def test_nearest_first_then_dealers_with_no_position(self):
        found = list(self.discover([{"name": "Landers Used", "website": "landersused.com"}]).values())
        placed = [dealer["miles"] for dealer in found if dealer["miles"] is not None]
        self.assertEqual(placed, sorted(placed))
        self.assertIsNone(found[-1]["miles"])


if __name__ == "__main__":
    unittest.main()
