"""What a car costs beyond its asking price, for a buyer who titles it in Tennessee.

Sales tax on a vehicle (Tennessee Department of Revenue; worked through in research/07-tennessee.md): 7% state on
the whole price, the local rate on the first $1,600, and a 2.75% state single-article tax on the next $1,600.
It is paid at the county clerk when the car is titled, wherever the car was bought. Title and registration
fees are extra and are not counted here.

What buying a car to sell it again costs, and what to pay for one (research/11-profit-estimate.md). The tax
is known. The rest are assumptions, each a round figure with its source, and the page prints them:

- `give`: what comes off between asking and selling. 8%, a Consumer Reports survey's median.
- `title`: title and a new plate at the Shelby County Clerk. $180, built from other counties' schedules and
  news reports, because the clerk's own page would not load.
- `ready`: a check before buying, a clean, small parts. $500, an estimate; anything really wrong costs more.
- `advert` and `hold`: $5 for a Craigslist post, $60 for a month's insurance.
- `left`: what the buyer wants over when it is all done. $1,000.

Tennessee taxes every change of owner on the price paid, and gives nothing back when the car is sold on."""

STATE = 0.07
SINGLE_ARTICLE = 0.0275
MEMPHIS = 0.0275                   # the local rate in Memphis since 1 January 2020; other localities run from 1.5%
STEP = 1600


def tennessee_tax(price, local=MEMPHIS):
    """Sales tax in dollars on a vehicle sold for `price`."""
    return round(STATE * price + local * min(price, STEP) + SINGLE_ARTICLE * min(max(price - STEP, 0), STEP), 2)


ASSUME = {"give": 0.08, "title": 180, "ready": 500, "advert": 5, "hold": 60, "left": 1000}
FAR_UNDER = 0.4                    # asking under this share of what such cars ask: a fault or a bait advert, not a bargain


def pay(resale, assume=ASSUME, local=MEMPHIS):
    """The most to pay for a car that should then be asked `resale` for, so that `left` remains after tax on
    the purchase, the title, getting it ready, the advert, holding it, and what comes off the asking price.
    Whole dollars; None when no price would leave that much."""
    room = resale * (1 - assume["give"]) - sum(assume[name] for name in ("left", "title", "ready", "advert", "hold"))
    bands = (room / (1 + STATE + local),                                               # all of it under $1,600
             (room - (local - SINGLE_ARTICLE) * STEP) / (1 + STATE + SINGLE_ARTICLE),  # from there to $3,200
             (room - (local + SINGLE_ARTICLE) * STEP) / (1 + STATE))                   # above: 7% and the two slices
    price = next((found for found in bands if found > 0 and abs(found + tennessee_tax(found, local) - room) < 0.01), None)
    return int(price) if price else None


def left(price, resale, assume=ASSUME, local=MEMPHIS):
    """What is over after buying at `price` and selling for what an asking price of `resale` fetches. May be negative."""
    out = price + tennessee_tax(price, local) + sum(assume[name] for name in ("title", "ready", "advert", "hold"))
    return int(round(resale * (1 - assume["give"]) - out))
