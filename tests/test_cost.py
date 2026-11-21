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


if __name__ == "__main__":
    unittest.main()
