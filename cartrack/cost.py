"""What a car costs beyond its asking price, for a buyer who titles it in Tennessee.

Sales tax on a vehicle (Tennessee Department of Revenue; worked through in research/07-tennessee.md): 7% state on
the whole price, the local rate on the first $1,600, and a 2.75% state single-article tax on the next $1,600.
It is paid at the county clerk when the car is titled, wherever the car was bought. Title and registration
fees are extra and are not counted here."""

STATE = 0.07
SINGLE_ARTICLE = 0.0275
MEMPHIS = 0.0275                   # the local rate in Memphis since 1 January 2020; other localities run from 1.5%
STEP = 1600


def tennessee_tax(price, local=MEMPHIS):
    """Sales tax in dollars on a vehicle sold for `price`."""
    return round(STATE * price + local * min(price, STEP) + SINGLE_ARTICLE * min(max(price - STEP, 0), STEP), 2)
