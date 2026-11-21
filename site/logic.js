// Which cars the page shows and in what order. No page, no network: tests/js runs this under node.

/** The cars that pass every filter set in `filters` ({text, maxPrice, maxMiles, dealer, droppedOnly}). */
export function visible(cars, filters) {
  const words = (filters.text || "").toLowerCase().split(/\s+/).filter(Boolean);
  return cars.filter((car) => {
    const title = (car.title || "").toLowerCase();
    if (!words.every((word) => title.includes(word))) return false;
    if (filters.maxPrice && car.price > filters.maxPrice) return false;
    if (filters.maxMiles && (car.miles == null || car.miles > filters.maxMiles)) return false;
    if (filters.dealer && car.dealer_key !== filters.dealer) return false;
    if (filters.droppedOnly && !car.drop) return false;
    return true;
  });
}

const last = Number.POSITIVE_INFINITY;          // where a car with no mileage goes when sorting by mileage
const share = (car) => (car.drop && car.was ? car.drop / car.was : 0);

const orders = {
  drop: (a, b) => b.drop - a.drop,
  share: (a, b) => share(b) - share(a),
  new: (a, b) => a.days - b.days,
  old: (a, b) => b.days - a.days,
  price: (a, b) => a.price - b.price,
  miles: (a, b) => (a.miles ?? last) - (b.miles ?? last),
};

/** A new list in the order named by `how`; cars that tie keep the order they came in. */
export function sorted(cars, how) {
  return [...cars].sort(orders[how] || orders.drop);
}
