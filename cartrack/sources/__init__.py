"""Readers for places that are not one dealer's website: classifieds first, auctions and lenders to come.

Each reader is `read(place, get, seen, known=())` and gives back `(listings, complete)`, like a dealer reader.
`place` is a row of sources.json. `known` holds the source ids the catalogue already has in full, so a reader
that needs a page per listing asks for each one once and afterwards only for what the list page says: price,
title and whether it is still there. The catalogue keeps what an earlier read gave wherever a later one is
silent. For an auction, `known` holds the lots already recorded as over, so a finished sale is read once."""

from . import auctioneersoftware, craigslist, facebook, liennotices, offerup

SOURCES = {
    "auctioneersoftware": auctioneersoftware.read,
    "craigslist": craigslist.read,
    "facebook": facebook.read,
    "liennotices": liennotices.read,
    "offerup": offerup.read,
}
