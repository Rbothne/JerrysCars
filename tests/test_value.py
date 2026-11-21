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

    def test_the_judgement_says_how_many_similar_cars_it_rests_on(self):
        judged = value.judge(market(), YEAR)
        self.assertTrue(all(one["similar"] >= 3 for one in judged.values()))

    def test_typical_is_a_round_number_of_dollars(self):
        judged = value.judge(market(), YEAR)
        self.assertTrue(all(isinstance(one["typical"], int) and one["typical"] % 100 == 0 for one in judged.values()))

    def test_a_model_with_too_few_similar_cars_gets_no_judgement(self):
        rare = [car(9100 + n, "Roadster", 2019, 40000 + n, price=25000) for n in range(2)]
        judged = value.judge(market() + rare, YEAR)
        self.assertNotIn("lot:9100", judged)
        self.assertNotIn("lot:9101", judged)

    def test_cars_far_off_in_years_or_miles_are_not_similar(self):
        loner = car(9200, "Camry", 2003, 280000, price=3000)        # the market's Camrys are 2016 on, under 150,000
        self.assertNotIn("lot:9200", value.judge(market() + [loner], YEAR))

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
