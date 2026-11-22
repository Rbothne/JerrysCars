import json
import pathlib
import unittest

from cartrack import fetch
from cartrack.readers import NotRead
from cartrack.sources import auctioneersoftware

FIXTURES = pathlib.Path(__file__).parent / "fixtures"     # cut from www.venture-auctions.com as saved 2026-11-21:
SEEN = "2026-11-21T23:00"                                 # the lists and lot pages cut short, their totals edited to fit
PLACE = {"key": "venture-auctions.com", "kind": "auctioneersoftware", "site": "https://www.venture-auctions.com",
         "name": "City of Memphis impound auction", "city": "Memphis", "state": "TN", "zip": "38127",
         "lat": 35.20956, "lon": -90.04762}
BASE = "https://www.venture-auctions.com"
AUCTIONS, PAST, PAST_2 = BASE + "/auctions", BASE + "/past-auctions", BASE + "/past-auctions?page=2"
OPEN = BASE + "/auctions/5362-memphis-impound-public-webcast-auction-11-25-2026"
MARK = "window.__APOLLO_STATE__ = "


def sale_address(auction_id):
    state = json.loads((FIXTURES / "venture_past.html").read_text(encoding="utf-8").split(MARK)[1].split(";\n</script>")[0])
    older = json.loads((FIXTURES / "venture_past_p2.html").read_text(encoding="utf-8").split(MARK)[1].split(";\n</script>")[0])
    return {**state, **older}[f"Auction.{auction_id}"]["public_url"]


def sale_pages(auction_id):
    """The 18 November sale's two fixture pages, renumbered as sale `auction_id`."""
    address = sale_address(auction_id)
    first, second = ((FIXTURES / name).read_text(encoding="utf-8").replace("5361", auction_id)
                     for name in ("venture_sale.html", "venture_sale_p2.html"))
    return {address: first.encode(), address + "?page=2": second.encode()}


def edited(name, change):
    """A fixture page with its data changed by `change(state)`."""
    head, rest = (FIXTURES / name).read_text(encoding="utf-8").split(MARK)
    body, tail = rest.split(";\n</script>")
    state = json.loads(body)
    change(state)
    return (head + MARK + json.dumps(state) + ";\n</script>" + tail).encode()


PAGES = {AUCTIONS: "venture_auctions.html", OPEN: "venture_open.html", PAST: "venture_past.html",
         PAST_2: "venture_past_p2.html", **sale_pages("5361"), **sale_pages("5360"), **sale_pages("5359"),
         **sale_pages("5324")}
SALE = sale_address("5361")


def answers(table=None):
    table = {**PAGES, **(table or {})}
    asked = []

    def get(url, **options):
        asked.append(url)
        answer = table[url]
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, bytes) else (FIXTURES / answer).read_bytes()
    get.asked = asked
    return get


class Venture(unittest.TestCase):
    def read(self, table=None, **options):
        self.get = answers(table)
        found, complete = auctioneersoftware.read(PLACE, self.get, SEEN, **options)
        self.lots = {lot["source_id"]: lot for lot in found}
        return found, complete

    def test_asks_for_the_coming_sales_then_the_finished_ones_not_read_before(self):
        found, complete = self.read(limit=1)
        self.assertEqual(self.get.asked, [AUCTIONS, OPEN, PAST, SALE, SALE + "?page=2"])
        self.assertEqual(sorted(self.lots), ["5361-3608", "5361-3609", "5361-3611", "5361-3672", "5361-3673"])
        self.assertTrue(complete)

    def test_reads_the_real_scion_as_sold(self):
        self.read(limit=1)
        scion = self.lots["5361-3611"]
        self.assertEqual(scion["id"], "venture-auctions.com:5361-3611")
        self.assertEqual(scion["title"], "2009 SCION TC COUPE 2-DR 2.4L L4")
        self.assertEqual(scion["url"], BASE + "/auctions/5361/lot/3611-2009-scion-tc-coupe-2-dr-24l-l4")
        self.assertEqual((scion["channel"], scion["price"], scion["price_kind"], scion["ends"]),
                         ("auction", 900, "sold", "2026-11-18T15:47"))
        self.assertEqual((scion["vin"], scion["vin_ok"], scion["year"], scion["make"], scion["model"]),
                         ("JTKDE167090282241", True, 2009, "scion", "TC COUPE 2-DR 2.4L L4"))
        self.assertEqual((scion["miles"], scion["title_status"], scion["seller_type"]), (None, None, None))
        self.assertEqual((scion["seller_name"], scion["city"], scion["state"], scion["zip"], scion["geo_how"]),
                         ("City of Memphis impound auction", "Memphis", "TN", "38127", "street"))
        self.assertEqual(scion["photo_count"], 8)
        self.assertTrue(scion["photos"][0].startswith("https://auctioneersoftware.s3.us-east-1.amazonaws.com/vent/2026/11/large/"))
        self.assertEqual(scion["extra"], {"auction": "Memphis Impound Public Webcast Auction 11/18/2026", "auction_id": "5361",
                                          "lot": "1", "ticket": "6510381", "bids": 3, "watchers": 16})

    def test_a_lot_the_auctioneer_marked_no_sale_keeps_its_last_bid_and_is_not_called_sold(self):
        self.read(limit=1)
        camaro = self.lots["5361-3672"]
        self.assertEqual((camaro["price"], camaro["price_kind"], camaro["extra"]["no_sale"]), (500, "reserve_not_met", True))

    def test_a_sale_with_a_lot_already_recorded_as_over_is_not_read_again(self):
        self.read(known={"5361-3611"}, limit=1)
        self.assertEqual(self.get.asked, [AUCTIONS, OPEN, PAST, sale_address("5360"), sale_address("5360") + "?page=2"])
        self.assertEqual(len(self.lots), 5)

    def test_only_so_many_finished_sales_are_read_in_one_run_newest_first(self):
        self.read(limit=2)
        self.assertEqual({key.split("-")[0] for key in self.lots}, {"5361", "5360"})
        self.assertNotIn(PAST_2, self.get.asked)

    def test_the_list_of_finished_sales_is_followed_to_its_next_page_while_there_is_room_for_more(self):
        self.read(known={"5361-3611", "5360-3611"})
        self.assertEqual(self.get.asked[:4], [AUCTIONS, OPEN, PAST, PAST_2])
        self.assertEqual({key.split("-")[0] for key in self.lots}, {"5359", "5324"})

    def test_once_every_finished_sale_is_recorded_an_ordinary_run_is_three_requests(self):
        found, complete = self.read(known={"5361-3611", "5360-3611", "5359-3611", "5324-3611"})
        self.assertEqual(self.get.asked, [AUCTIONS, OPEN, PAST])
        self.assertEqual((found, complete), ([], True))

    def open_sale(self, change=lambda state: None):
        """The coming sale given the 18 November lots, as a sale not yet held (an edit: none was seen with lots up)."""
        def reopen(state):
            for key, record in state.items():
                if key.startswith("Auction."):
                    record.update(auction_status=200, start_time="2026-11-25T15:30:00.000Z")
                if key.startswith("AuctionLot."):
                    record.update(end_time=None, is_no_sale=False)
            if "AuctionLot.3609" in state:            # `change` is about the first page's lots
                change(state)
        return {OPEN: edited("venture_sale.html", reopen).replace(b"5361", b"5362"),
                OPEN + "?page=2": edited("venture_sale_p2.html", reopen).replace(b"5361", b"5362")}

    def test_a_lot_in_a_sale_not_yet_held_carries_the_bid_so_far_and_when_the_sale_starts(self):
        def no_bids_yet(state):
            state["AuctionLot.3608"].update(bid_count=0, winning_bid_amount=None)
        found, complete = self.read(self.open_sale(no_bids_yet), limit=0)
        self.assertEqual(self.get.asked, [AUCTIONS, OPEN, OPEN + "?page=2", PAST])
        scion, malibu = self.lots["5362-3611"], self.lots["5362-3608"]
        self.assertEqual((scion["price"], scion["price_kind"], scion["ends"]), (900, "bid", "2026-11-25T15:30"))
        self.assertEqual((malibu["price"], malibu["price_kind"], malibu["extra"]["bids"]), (10, "starting", 0))
        self.assertEqual((len(found), complete), (5, True))

    def test_a_lot_that_is_not_a_vehicle_is_left_out(self):
        def a_mower(state):
            state["AuctionLot.3609"].update(title="JOHN DEERE Z930M MOWER", description="<strong>CITY ID#</strong> 44817")
            state["AuctionLot.3609"]["category"]["name"] = "EQUIPMENT - CITY"
        self.read(self.open_sale(a_mower), limit=0)
        self.assertEqual(sorted(self.lots), ["5362-3608", "5362-3611", "5362-3672", "5362-3673"])

    def test_a_lot_sold_for_parts_only_says_so(self):
        def for_parts(state):
            state["AuctionLot.3609"]["title"] = "*FOR PARTS ONLY* 2001  CHEVROLET  MALIBU SEDAN 4-DR 3.1L V6"
        self.read(self.open_sale(for_parts), limit=0)
        self.assertEqual(self.lots["5362-3609"]["title_status"], "parts_only")

    def test_a_finished_sale_whose_page_fails_is_left_out_whole_and_the_next_is_still_read(self):
        found, complete = self.read({SALE + "?page=2": OSError("timed out")}, limit=2)
        self.assertEqual({key.split("-")[0] for key in self.lots}, {"5360"})
        self.assertFalse(complete)

    def test_a_coming_sale_whose_page_fails_makes_the_read_partial(self):
        found, complete = self.read({OPEN: OSError("timed out")}, limit=1)
        self.assertEqual(len(found), 5)
        self.assertFalse(complete)

    def test_told_to_slow_down_it_stops_asking_for_finished_sales(self):
        found, complete = self.read({SALE: fetch.RateLimited(SALE)}, limit=3)
        self.assertEqual(self.get.asked, [AUCTIONS, OPEN, PAST, SALE])
        self.assertEqual((found, complete), ([], False))

    def test_a_page_without_its_data_is_not_read(self):
        with self.assertRaises(NotRead):
            self.read({AUCTIONS: b"<html><body>Down for maintenance</body></html>"})

    def test_only_the_addresses_the_pages_themselves_give_are_asked_for(self):
        self.read()
        for address in self.get.asked:
            self.assertRegex(address, r"^https://www\.venture-auctions\.com/(auctions|past-auctions)(\?page=\d+)?$"
                                      r"|^https://www\.venture-auctions\.com/auctions/\d+-[a-z0-9-]+(\?page=\d+)?$")


if __name__ == "__main__":
    unittest.main()
