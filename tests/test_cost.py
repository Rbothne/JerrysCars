import unittest

from cartrack import cost


class TennesseeTax(unittest.TestCase):
    def test_matches_the_worked_table_for_memphis(self):
        # research/07-tennessee.md: 7% state, 2.75% local on the first $1,600, 2.75% single-article on the next $1,600
        self.assertEqual(cost.tennessee_tax(3000), 292.5)
        self.assertEqual(cost.tennessee_tax(6000), 508)
        self.assertEqual(cost.tennessee_tax(10000), 788)

    def test_a_car_under_1600_pays_local_tax_on_all_of_it_and_no_single_article_tax(self):
        self.assertEqual(cost.tennessee_tax(1000), 97.5)

    def test_another_locality_changes_only_the_first_1600(self):
        self.assertEqual(cost.tennessee_tax(10000, local=0.0225), 780)


class Pay(unittest.TestCase):
    """research/11-profit-estimate.md: resale less 8%, tax on the purchase, $180 title, $500 ready, $5, $60."""

    def test_paying_that_price_leaves_the_sum_wanted(self):
        for resale in (2500, 4000, 6500, 12000, 30000):
            price = cost.pay(resale)
            self.assertIn(cost.left(price, resale), (1000, 1001), resale)      # whole dollars: within one

    def test_the_worked_example_of_a_terrain_asked_4850(self):
        # resale $4,254 after the 8% (an asking price of $4,624): pay about $2,300 to have $1,000 left
        self.assertEqual(round(cost.pay(4624), -2), 2300)
        self.assertEqual(round(cost.left(4850, 4624), -2), -1800)

    def test_the_price_falls_in_the_right_tax_band(self):
        self.assertLess(cost.pay(2600), 1600)             # all of it taxed at 9.75%
        self.assertTrue(1600 < cost.pay(4000) <= 3200)    # still 9.75%: the second slice
        self.assertGreater(cost.pay(9000), 3200)          # 7% and the $88 the two slices come to

    def test_a_car_worth_too_little_to_leave_the_sum_has_no_price_to_pay(self):
        self.assertIsNone(cost.pay(1500))
        self.assertIsNone(cost.pay(0))

    def test_the_sum_wanted_and_the_costs_can_be_set(self):
        lean = {**cost.ASSUME, "left": 0, "ready": 150}
        self.assertGreater(cost.pay(6000, lean), cost.pay(6000) + 1200)


if __name__ == "__main__":
    unittest.main()
