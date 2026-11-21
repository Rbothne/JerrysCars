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

/** The cars that pass every filter set in `filters`: text, make, model, minPrice, maxPrice, minYear, maxYear,
 *  maxMiles, body, drive ("four" or "two"), fuel, dealer, localOnly, droppedOnly, underOnly, oneOwnerOnly,
 *  certifiedOnly, historyOnly. */
export function visible(cars, filters) {
  const words = (filters.text || "").toLowerCase().split(/\s+/).filter(Boolean);
  return cars.filter((car) => {
    const title = (car.title || "").toLowerCase();
    if (!words.every((word) => title.includes(word))) return false;
    if (filters.make && car.make !== filters.make) return false;
    if (filters.model && car.model !== filters.model) return false;
    if (filters.minPrice && car.price < filters.minPrice) return false;
    if (filters.maxPrice && car.price > filters.maxPrice) return false;
    if (filters.minYear && !(car.year >= filters.minYear)) return false;
    if (filters.maxYear && !(car.year <= filters.maxYear)) return false;
    if (filters.maxMiles && (car.miles == null || car.miles > filters.maxMiles)) return false;
    if (filters.body && car.body !== filters.body) return false;
    if (filters.drive && !(DRIVES[filters.drive] || []).includes(car.drive)) return false;
    if (filters.fuel && car.fuel !== filters.fuel) return false;
    if (filters.dealer && car.dealer_key !== filters.dealer) return false;
    if (filters.localOnly && car.kind === "online") return false;
    if (filters.droppedOnly && !car.drop) return false;
    if (filters.underOnly && !((under(car) || {}).share >= NOTABLE)) return false;
    if (filters.oneOwnerOnly && car.one_owner !== true) return false;
    if (filters.certifiedOnly && car.certified !== true) return false;
    if (filters.historyOnly && !car.history) return false;
    return true;
  });
}

const share = (car) => (car.drop && car.was ? car.drop / car.was : 0);

// What each sort field measures. Null means the car lacks the figure, and it then goes last either way.
const figures = {
  value: (car) => (car.typical ? (car.typical - car.price) / car.typical : null),
  price: (car) => car.price,
  total: (car) => car.total ?? car.price,
  drop: (car) => car.drop || 0,
  share,
  year: (car) => car.year ?? null,
  miles: (car) => car.miles ?? null,
  peryear: (car) => car.per_year ?? null,
  days: (car) => car.days ?? null,
};

/** The direction each field starts in: the one a buyer usually wants (cheapest, newest, biggest cut). */
export const DIRECTIONS = { value: "desc", price: "asc", total: "asc", drop: "desc", share: "desc",
  year: "desc", miles: "asc", peryear: "asc", days: "asc" };

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
