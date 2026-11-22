// Which cars the page shows and in what order. No page, no network: tests/js runs this under node.

export const NOTABLE = 0.1;                     // under typical by less than this is within the estimate's noise
const DRIVES = { four: ["4wd", "awd"], two: ["2wd", "fwd", "rwd"] };

/** The whole number someone typed into a price, year or mileage box ("$12,500" is 12500). Nothing usable is 0: no limit. */
export function amount(text) {
  return Number(String(text ?? "").split(".")[0].replace(/\D/g, "")) || 0;
}

/** How far a car sits below what similar cars ask: {amount, share}. Null when it was never judged or is not below. */
export function under(car) {
  if (!car.typical || car.price >= car.typical) return null;
  return { amount: car.typical - car.price, share: (car.typical - car.price) / car.typical };
}

// How far under its figure a car must ask before the page marks it: about one and a half times how far off such
// a figure usually is. A figure from the model alone ("rough") is never enough, whatever it says.
const MARKS = { dealer: { close: NOTABLE, wide: 0.15 }, private: { close: 0.3, wide: 0.3 } };
const clean = (car) => !car.title_status || car.title_status === "clean";

/** `under(car)` when the car is far enough under to be worth a mark, given who is selling and what its figure
 *  stands on; null otherwise. A car whose title is not clean is set beside clean cars and never marked. */
export function marked(car) {
  const below = under(car);
  const need = MARKS[car.seller === "private" ? "private" : "dealer"][car.basis || "close"];
  return below && need && clean(car) && below.share >= need ? below : null;
}

// ---- search ----------------------------------------------------------------------------------------------------
// A typed word matches a car when the car's title, make or model contains it, punctuation aside ("crv" finds
// CR-V). A word with letters and digits also matches across a space ("f150" finds "F 150"); plain letters do
// not, or "taco" would find every Toyota Corolla. A word that matches no car at all is taken for a misspelling
// and matched to names one slip away; a word that does match some car is never widened.

const NICKNAMES = { chevy: "chevrolet", vw: "volkswagen", caddy: "cadillac", bimmer: "bmw", beemer: "bmw",
  beamer: "bmw", subie: "subaru", benz: "mercedes" };
const GUESS_FROM = 4;                           // shorter words have too many neighbours to guess at
const TWO_SLIPS_FROM = 8;                       // a word this long may be two slips out, a shorter one only one

const bare = (text) => text.toLowerCase().replace(/[^a-z0-9\s]/g, "");
const read = new WeakMap();

/** What search looks at in one car, worked out once: its words run together as typed, and each name in it. */
function reading(car) {
  if (!read.has(car)) {
    const all = `${car.title || ""} ${car.make || ""} ${car.model || ""}`;
    const plain = bare(all).replace(/\s+/g, " ");
    read.set(car, { plain, joined: plain.replace(/ /g, ""),
      names: [...new Set(all.toLowerCase().split(/[^a-z]+/).filter((name) => name.length >= GUESS_FROM))] });
  }
  return read.get(car);
}

function contains(seen, word) {
  return [word, NICKNAMES[word]].some((form) => form && (seen.plain.includes(form)
    || (/[a-z]/.test(form) && /\d/.test(form) && seen.joined.includes(form))));
}

/** How many slips turn one word into the other: a letter added, dropped or changed, or two neighbours swapped. */
function slips(a, b) {
  let [before, last] = [[], Array.from({ length: b.length + 1 }, (_, at) => at)];
  for (let i = 1; i <= a.length; i++) {
    const row = [i];
    for (let j = 1; j <= b.length; j++) {
      row[j] = Math.min(last[j] + 1, row[j - 1] + 1, last[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) row[j] = Math.min(row[j], before[j - 2] + 1);
    }
    [before, last] = [last, row];
  }
  return last[b.length];
}

/** Whether `word` could be a misspelling of `name`, or of its start (the word may be only half typed). */
function near(word, name) {
  if (word[0] !== name[0]) return false;         // people rarely get the first letter wrong
  const allowed = word.length < TWO_SLIPS_FROM ? 1 : 2;
  for (let length = Math.max(word.length - allowed, 1); length <= Math.min(word.length + allowed, name.length); length++) {
    if (slips(word, name.slice(0, length)) <= allowed) return true;
  }
  return false;
}

/** The words typed, with letters and a number after them made one word when some car carries them as one name
 *  ("f 150" is "f150", "model 3" is "model3"; "camry 2012" stays two). */
function typed(text, cars) {
  const words = [];
  for (const word of bare(text || "").split(/\s+/).filter(Boolean)) {
    const one = (words[words.length - 1] || "") + word;
    if (/^[a-z]+\d+$/.test(one) && /^\d/.test(word) && cars.some((car) => reading(car).joined.includes(one))) words[words.length - 1] = one;
    else words.push(word);
  }
  return [...new Set(words)];
}

/** One test per typed word, each taking a car's reading. */
function sought(text, cars) {
  return typed(text, cars).map((word) => {
    const guess = word.length >= GUESS_FROM && /^[a-z]+$/.test(word) && !cars.some((car) => contains(reading(car), word));
    return guess ? (seen) => seen.names.some((name) => near(word, name)) : (seen) => contains(seen, word);
  });
}

/** The cars that pass every filter set in `filters`: text, make, model, minPrice, maxPrice, minYear, maxYear,
 *  maxMiles, maxAway (miles from home; a car whose distance is not known stays), body, drive ("four" or "two"),
 *  fuel, dealer, seller ("private" or "dealer"), localOnly, droppedOnly,
 *  underOnly, oneOwnerOnly, certifiedOnly, historyOnly, cleanOnly (hides a car whose seller names a title that
 *  is not clean; a car that says nothing of its title stays). */
export function visible(cars, filters) {
  const words = sought(filters.text, cars);
  return cars.filter((car) => {
    if (words.length && !words.every((matches) => matches(reading(car)))) return false;
    if (filters.make && car.make !== filters.make) return false;
    if (filters.model && car.model !== filters.model) return false;
    if (filters.minPrice && car.price < filters.minPrice) return false;
    if (filters.maxPrice && car.price > filters.maxPrice) return false;
    if (filters.minYear && !(car.year >= filters.minYear)) return false;
    if (filters.maxYear && !(car.year <= filters.maxYear)) return false;
    if (filters.maxMiles && (car.miles == null || car.miles > filters.maxMiles)) return false;
    if (filters.maxAway && car.dealer_miles != null && car.dealer_miles > filters.maxAway) return false;
    if (filters.body && car.body !== filters.body) return false;
    if (filters.drive && !(DRIVES[filters.drive] || []).includes(car.drive)) return false;
    if (filters.fuel && car.fuel !== filters.fuel) return false;
    if (filters.dealer && car.dealer_key !== filters.dealer && !(car.also || []).includes(filters.dealer)) return false;
    if (filters.seller && car.seller !== filters.seller) return false;
    if (filters.cleanOnly && car.title_status && car.title_status !== "clean") return false;
    if (filters.localOnly && car.kind === "online") return false;
    if (filters.droppedOnly && !car.drop) return false;
    if (filters.underOnly && !marked(car)) return false;
    if (filters.oneOwnerOnly && car.one_owner !== true) return false;
    if (filters.certifiedOnly && car.certified !== true) return false;
    if (filters.historyOnly && !car.history) return false;
    return true;
  });
}

const share = (car) => (car.drop && car.was ? car.drop / car.was : 0);

// What each sort field measures. Null means the car lacks the figure, and it then goes last either way.
const figures = {
  value: (car) => (car.typical && car.basis !== "rough" && clean(car) ? (car.typical - car.price) / car.typical : null),
  price: (car) => car.price,
  drop: (car) => car.drop || 0,
  share,
  year: (car) => car.year ?? null,
  miles: (car) => car.miles ?? null,
  peryear: (car) => car.per_year ?? null,
  days: (car) => car.days ?? null,
  away: (car) => car.dealer_miles ?? null,
  room: (car) => (car.pay != null ? car.pay - car.price : null),       // asking least above, or furthest under, what to pay
};

/** The direction each field starts in: the one a buyer usually wants (cheapest, newest, biggest cut). */
export const DIRECTIONS = { value: "desc", price: "asc", drop: "desc", share: "desc",
  year: "desc", miles: "asc", peryear: "asc", days: "asc", away: "asc", room: "desc" };

/** A new list ordered by the field `how`, "asc" or "desc" (the field's own direction when not given).
 *  Cars that tie keep the order they came in; cars that lack the figure go last. */
export function sorted(cars, how, direction) {
  const field = figures[how] ? how : "value";
  const figure = figures[field];
  const turn = (direction || DIRECTIONS[field]) === "desc" ? -1 : 1;
  return [...cars].sort((a, b) => {
    const [left, right] = [figure(a), figure(b)];
    if (left == null || right == null) return (left == null) - (right == null);
    return turn * (left - right);
  });
}

// ---- auction lots ------------------------------------------------------------------------------------------------
// A lot has a bid, not an asking price, and nobody states its mileage: it is never ranked with the cars for sale.

/** What winning a lot at `price` costs before tax: the auction's premium on top, and its fee per lot.
 *  Null without a price or without the auction's charges. */
export function lotCost(price, place) {
  if (!price || !place) return null;
  return price * (1 + (place.premium || 0)) + (place.fee || 0);
}

/** Tennessee sales tax on a vehicle bought in Memphis, as cartrack/cost.py works it out. */
export function tennesseeTax(price) {
  return Math.round((0.07 * price + 0.0275 * Math.min(price, 1600) + 0.0275 * Math.min(Math.max(price - 1600, 0), 1600)) * 100) / 100;
}

/** What a lot won at `price` has cost by the time it is for sale again: the auction's charges, tax on them,
 *  the title, the advert, a month's insurance, and what the auction's own row assumes for getting an impounded
 *  car away and running (`place.ready`). It is also what the car must sell for to get the money back. */
export function lotAllIn(price, place, assume) {
  const paid = lotCost(price, place);
  if (paid == null || !assume) return null;
  return paid + tennesseeTax(paid) + assume.title + (place.ready ?? assume.ready) + assume.advert + assume.hold;
}

// What each lot order measures; a lot that lacks the figure goes last.
const lotFigures = {
  price: (lot) => lot.price ?? null,
  gap: (lot) => (lot.asks && lot.price ? lot.price - lot.asks.median : null),      // furthest under first
};

/** A new list of lots: "sale" (each sale in turn, lots in the order they are called), "newest" (latest result
 *  first), "price" (lowest first) or "gap" (the bid furthest under what such cars ask first). */
export function lotsSorted(lots, how) {
  if (lotFigures[how]) {
    const figure = lotFigures[how];
    return [...lots].sort((a, b) => {
      const [left, right] = [figure(a), figure(b)];
      if (left == null || right == null) return (left == null) - (right == null);
      return left - right;
    });
  }
  const turn = how === "newest" ? -1 : 1;
  return [...lots].sort((a, b) => turn * (a.ends || "").localeCompare(b.ends || "")
    || (how === "newest" ? 0 : (Number(a.lot) || 0) - (Number(b.lot) || 0)));
}
