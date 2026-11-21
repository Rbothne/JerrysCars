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
 *  maxMiles, body, drive ("four" or "two"), fuel, dealer, localOnly, droppedOnly, underOnly. */
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
    return true;
  });
}

const last = Number.POSITIVE_INFINITY;          // where a car with no mileage goes when sorting by mileage
const share = (car) => (car.drop && car.was ? car.drop / car.was : 0);
const value = (car) => (car.typical ? (car.typical - car.price) / car.typical : -last);   // never judged: last

const orders = {
  value: (a, b) => value(b) - value(a) || 0,    // two cars never judged tie (their difference is not a number)
  drop: (a, b) => b.drop - a.drop,
  share: (a, b) => share(b) - share(a),
  new: (a, b) => a.days - b.days,
  old: (a, b) => b.days - a.days,
  price: (a, b) => a.price - b.price,
  miles: (a, b) => (a.miles ?? last) - (b.miles ?? last),
  year: (a, b) => (b.year || 0) - (a.year || 0),
};

/** A new list in the order named by `how`; cars that tie keep the order they came in. */
export function sorted(cars, how) {
  return [...cars].sort(orders[how] || orders.value);
}
