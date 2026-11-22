import unittest

from cartrack import value

YEAR = 2026
BASE = {"Camry": 30000, "F-150": 48000, "Rogue": 31000}
MAKE = {"Camry": "toyota", "F-150": "ford", "Rogue": "nissan"}


def fair(model, year, miles):
    """What a car of this market asks: loses 8% a year and 1.5% per 10,000 miles."""
    return BASE[model] * 0.92 ** (YEAR - year) * (1 - 0.015 * miles / 10000)


def car(n, model, year, miles, price=None, **fields):
    return {"id": f"lot:{n}", "make": MAKE.get(model, "acme"), "model": model, "year": year, "miles": miles,
            "trim": "LE", "body": "sedan", "drive": "fwd", "fuel": "gas",
            "price": round(fair(model, year, miles)) if price is None else price, **fields}


def market(each=100):
    """`each` cars of each of three models, spread over nine years and up to 149,000 miles, a few percent of noise."""
    cars = []
    for at, model in enumerate(BASE):
        for n in range(each):
            year, miles = 2016 + (n * 7 + at) % 9, 6000 + (n * 37 % 100) * 1430
            noise = 1 + ((n * 13 + at * 5) % 9 - 4) / 100          # -4% .. +4%
            cars.append(car(at * 1000 + n, model, year, miles, round(fair(model, year, miles) * noise)))
    return cars


class Judge(unittest.TestCase):
    def test_a_car_priced_like_its_peers_is_judged_near_its_price(self):
        cars = market()
        judged = value.judge(cars, YEAR)
        off = sorted(abs(judged[one["id"]]["typical"] / one["price"] - 1) for one in cars if one["id"] in judged)
        self.assertGreater(len(off), 250)                           # nearly every car has peers enough
        self.assertLess(off[len(off) // 2], 0.05)

    def test_a_car_well_under_its_peers_shows_as_under(self):
        cheap = car(9001, "Camry", 2020, 60000, price=round(fair("Camry", 2020, 60000) * 0.7))
        judged = value.judge(market() + [cheap], YEAR)["lot:9001"]
        self.assertGreater(judged["typical"], cheap["price"] * 1.25)
        self.assertLess(judged["typical"], cheap["price"] * 1.6)

    def test_a_trim_word_that_means_dear_on_other_models_does_not_make_a_plain_car_look_cheap(self):
        # "SR" is the dear trim on four other models here and the plain one on the single Camry that carries it,
        # as it was on Tacomas beside Nissan's SR trims in the 2026-11-21 catalogue: a $36,590 truck was said
        # to be typical at $54,600 when no truck like it asked over $43,000.
        others = []
        for at, model in enumerate(("Altima", "Sentra", "Kicks", "Frontier")):
            for n in range(30):
                year, miles = 2016 + n % 9, 10000 + n * 4000
                asks = (22000 + at * 3000) * 0.92 ** (YEAR - year) * (1 - 0.015 * miles / 10000)
                others.append({**car(8000 + at * 100 + n, "Camry", year, miles, price=round(asks * (1.4 if n < 5 else 1))),
                               "make": "nissan", "model": model, "trim": "SR" if n < 5 else "S"})
        plain = car(8900, "Camry", 2020, 60000, trim="SR")
        judged = value.judge(market() + others + [plain], YEAR)
        self.assertLess(judged["lot:8900"]["typical"], plain["price"] * 1.08)

    def test_the_judgement_says_how_many_similar_cars_it_rests_on_and_how_near_they_are(self):
        judged = value.judge(market(), YEAR)
        self.assertTrue(all(one["similar"] >= 3 for one in judged.values() if one["basis"] != "rough"))
        self.assertTrue(all(one["similar"] == 0 and one["window"] is None for one in judged.values() if one["basis"] == "rough"))
        self.assertEqual({one["window"] for one in judged.values() if one["basis"] == "close"}, {(2, 30000)})
        self.assertGreater(sum(1 for one in judged.values() if one["basis"] == "close"), 250)

    def test_typical_is_a_round_number_of_dollars(self):
        judged = value.judge(market(), YEAR)
        self.assertTrue(all(isinstance(one["typical"], int) and one["typical"] % 100 == 0 for one in judged.values()))

    def test_a_model_with_too_few_similar_cars_gets_a_rough_figure_from_the_model_alone(self):
        rare = [car(9100 + n, "Roadster", 2019, 40000 + n, price=25000) for n in range(2)]
        judged = value.judge(market() + rare, YEAR)
        self.assertEqual([(judged[key]["basis"], judged[key]["similar"]) for key in ("lot:9100", "lot:9101")],
                         [("rough", 0), ("rough", 0)])
        self.assertGreater(judged["lot:9100"]["typical"], 0)

    def test_cars_far_off_in_years_or_miles_are_not_similar(self):
        loner = car(9200, "Camry", 2003, 280000, price=3000)        # the market's Camrys are 2016 on, under 150,000
        self.assertEqual(value.judge(market() + [loner], YEAR)["lot:9200"]["basis"], "rough")

    def test_with_none_close_the_window_widens_a_step_at_a_time_and_says_how_far(self):
        # three Stratus within four years and 60,000 miles of the one judged, none nearer
        wide = [car(9400, "Stratus", 2016, 100000, price=6000), car(9401, "Stratus", 2012, 60000, price=5000),
                car(9402, "Stratus", 2013, 150000, price=4000), car(9403, "Stratus", 2019, 45000, price=9000)]
        judged = value.judge(market() + wide, YEAR)["lot:9400"]
        self.assertEqual((judged["basis"], judged["window"], judged["similar"]), ("wide", (4, 60000), 3))

    def test_every_figure_carries_the_range_most_asking_prices_fall_in(self):
        judged = value.judge(market(), YEAR)
        one = next(found for found in judged.values() if found["basis"] == "close")
        self.assertEqual((one["low"], one["high"]), (round(one["typical"] * 0.96, -2), round(one["typical"] * 1.13, -2)))

    def private_market(self):
        """The dealers' market, and 90 private sellers asking 3% less for each year of the car's age."""
        cars = []
        for at, model in enumerate(BASE):
            for n in range(30):
                year, miles = 2008 + (n * 5 + at) % 14, 60000 + (n * 41 % 100) * 1500
                noise = 1 + ((n * 11 + at * 3) % 9 - 4) / 100
                asks = fair(model, year, miles) * (1 - 0.03 * (YEAR + 1 - year)) * noise
                cars.append(car(5000 + at * 100 + n, model, year, miles, round(asks), seller="private"))
        return market() + cars

    def test_a_private_sellers_car_is_set_beside_what_private_sellers_ask(self):
        # 2026-11-21: private sellers asked 6% under dealers on a two-year-old car and 31% under on one of eleven
        cars = self.private_market()
        judged = value.judge(cars, YEAR)
        off = sorted(judged[one["id"]]["typical"] / one["price"] - 1 for one in cars if one.get("seller") == "private")
        self.assertLess(abs(off[len(off) // 2]), 0.08)              # neither all "under" nor all "over"
        dealers = sorted(abs(judged[one["id"]]["typical"] / one["price"] - 1) for one in cars if not one.get("seller"))
        self.assertLess(dealers[len(dealers) // 2], 0.06)           # and the dealers' cars are judged as well as before

    def test_a_private_cars_figure_has_the_wider_range_private_asking_prices_show(self):
        cars = self.private_market()
        judged = value.judge(cars, YEAR)
        one = next(judged[found["id"]] for found in cars if found.get("seller") == "private" and judged[found["id"]]["basis"] == "close")
        self.assertEqual((one["low"], one["high"]), (round(one["typical"] * 0.90, -2), round(one["typical"] * 1.25, -2)))

    def test_a_car_kept_apart_is_priced_but_is_nobodys_neighbour_and_teaches_nothing(self):
        target = car(9500, "Camry", 2020, 60000)
        branded = [car(9510 + n, "Camry", 2020, 60000 + n, price=900, apart=True) for n in range(6)]
        alone = value.judge(market() + [target], YEAR)["lot:9500"]
        beside = value.judge(market() + [target] + branded, YEAR)
        self.assertEqual(beside["lot:9500"], alone)
        self.assertGreater(beside["lot:9510"]["typical"], 10000)    # what a sound one asks, not what the six ask

    def test_a_missing_engine_drive_or_body_is_taken_from_the_cars_own_model(self):
        known = [{"make": "ford", "model": "F-150", "body": "pickup", "drive": "4wd", "cylinders": 8.0},
                 {"make": "ford", "model": "F-150", "body": "pickup", "drive": "rwd", "cylinders": 8.0},
                 {"make": "ford", "model": "F-150", "body": "pickup", "drive": "4wd", "cylinders": 6.0},
                 {"make": "ford", "model": "F-150", "body": "pickup", "drive": "rwd", "cylinders": 6.0}]
        bare = {"make": "ford", "model": "F-150", "body": None, "drive": "", "cylinders": None, "litres": None}
        said = {"make": "ford", "model": "F-150", "body": "truck", "drive": "rwd", "cylinders": 8.0}
        other = {"make": "ford", "model": "Pinto", "body": None}
        filled = value._filled([bare, said, other], known)
        self.assertEqual((filled[0]["body"], filled[0]["drive"], filled[0]["cylinders"], filled[0]["litres"]),
                         ("pickup", "4wd", 6.0, None))                 # at a tie, the smaller as text
        self.assertEqual((filled[1]["body"], filled[1]["drive"]), ("truck", "rwd"))     # what a car states is kept
        self.assertIsNone(filled[2]["body"])

    def test_an_odometer_or_an_age_beyond_belief_is_capped_where_the_curve_is_made(self):
        # a dealer's odometer of 1,824,979 bent the mileage curve for every car on 2026-11-21
        counts = {}
        typo = value._features(car(1, "Camry", 2012, 1824979), YEAR, counts)
        capped = value._features(car(1, "Camry", 2012, 300000), YEAR, counts)
        self.assertEqual(typo, capped)
        self.assertEqual(value._features(car(1, "Camry", 1947, 60000), YEAR, counts)["age"], 30)

    def test_too_small_a_market_judges_nothing(self):
        self.assertEqual(value.judge(market(each=10), YEAR), {})

    def test_cars_without_a_year_mileage_or_price_are_left_out(self):
        odd = [car(9300, "Camry", None, 60000, price=15000), car(9301, "Camry", 2020, None, price=15000),
               {**car(9302, "Camry", 2020, 60000), "price": None}]
        judged = value.judge(market() + odd, YEAR)
        self.assertFalse({"lot:9300", "lot:9301", "lot:9302"} & set(judged))

    def test_the_same_cars_give_the_same_judgement_whatever_their_order(self):
        cars = market()
        self.assertEqual(value.judge(cars, YEAR), value.judge(cars[::-1], YEAR))


if __name__ == "__main__":
    unittest.main()
