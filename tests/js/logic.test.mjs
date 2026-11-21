import assert from "node:assert/strict";
import test from "node:test";

import { sorted, under, visible } from "../../site/logic.js";

const camry = { id: "a:1", title: "2012 Toyota Camry LE", make: "toyota", model: "Camry", year: 2012, body: "sedan", drive: "fwd", fuel: "hybrid", kind: "lot",
  price: 6500, was: null, drop: 0, miles: 134200, days: 4, dealer_key: "a", typical: 8000, similar: 6 };
const f150 = { id: "b:2", title: "2015 Ford F-150 XLT", make: "ford", model: "F-150", year: 2015, body: "pickup", drive: "4wd", fuel: "gas", kind: "lot",
  price: 14900, was: 16400, drop: 1500, miles: 98000, days: 40, dealer_key: "b", typical: 15000, similar: 9 };
const cruze = { id: "b:3", title: "2013 Chevrolet Cruze LS", make: "chevrolet", model: "Cruze", year: 2013, body: "sedan", drive: null, fuel: "gas", kind: "online",
  price: 3740, was: 3990, drop: 250, miles: null, days: 28, dealer_key: "b", typical: null, similar: null };
const cars = [camry, f150, cruze];
const ids = (list) => list.map((car) => car.id);

test("no filters shows every car", () => {
  assert.deepEqual(ids(visible(cars, {})), ["a:1", "b:2", "b:3"]);
});

test("search matches every word typed, in any order and case", () => {
  assert.deepEqual(ids(visible(cars, { text: "camry TOYOTA" })), ["a:1"]);
  assert.deepEqual(ids(visible(cars, { text: "toyota ford" })), []);
});

test("a top price leaves out dearer cars", () => {
  assert.deepEqual(ids(visible(cars, { maxPrice: 7000 })), ["a:1", "b:3"]);
});

test("a top mileage leaves out cars over it and cars whose mileage is unknown", () => {
  assert.deepEqual(ids(visible(cars, { maxMiles: 140000 })), ["a:1", "b:2"]);
});

test("a dealer shows only that dealer's cars", () => {
  assert.deepEqual(ids(visible(cars, { dealer: "b" })), ["b:2", "b:3"]);
});

test("price cuts only leaves out cars never repriced down", () => {
  assert.deepEqual(ids(visible(cars, { droppedOnly: true })), ["b:2", "b:3"]);
});

test("filters combine", () => {
  assert.deepEqual(ids(visible(cars, { dealer: "b", maxPrice: 5000, droppedOnly: true })), ["b:3"]);
});

test("biggest cut first", () => {
  assert.deepEqual(ids(sorted(cars, "drop")), ["b:2", "b:3", "a:1"]);
});

test("biggest cut as a share of the first price", () => {
  assert.deepEqual(ids(sorted(cars, "share")), ["b:2", "b:3", "a:1"]);
  const small = { ...cruze, id: "c:9", price: 2000, was: 3000, drop: 1000 };
  assert.deepEqual(ids(sorted([f150, small], "share")), ["c:9", "b:2"]);
});

test("newest first and longest listed first", () => {
  assert.deepEqual(ids(sorted(cars, "new")), ["a:1", "b:3", "b:2"]);
  assert.deepEqual(ids(sorted(cars, "old")), ["b:2", "b:3", "a:1"]);
});

test("lowest price first", () => {
  assert.deepEqual(ids(sorted(cars, "price")), ["b:3", "a:1", "b:2"]);
});

test("lowest mileage first, unknown mileage last", () => {
  assert.deepEqual(ids(sorted(cars, "miles")), ["b:2", "a:1", "b:3"]);
});

test("sorting leaves the list it was given alone", () => {
  sorted(cars, "price");
  assert.deepEqual(ids(cars), ["a:1", "b:2", "b:3"]);
});

test("a make, and a model within it, show only those cars", () => {
  assert.deepEqual(ids(visible(cars, { make: "ford" })), ["b:2"]);
  assert.deepEqual(ids(visible(cars, { make: "toyota", model: "Camry" })), ["a:1"]);
  assert.deepEqual(ids(visible(cars, { make: "toyota", model: "Corolla" })), []);
});

test("a lowest price leaves out cheaper cars", () => {
  assert.deepEqual(ids(visible(cars, { minPrice: 5000 })), ["a:1", "b:2"]);
});

test("years from and to bound the model year, either alone or both", () => {
  assert.deepEqual(ids(visible(cars, { minYear: 2013 })), ["b:2", "b:3"]);
  assert.deepEqual(ids(visible(cars, { maxYear: 2013 })), ["a:1", "b:3"]);
  assert.deepEqual(ids(visible(cars, { minYear: 2013, maxYear: 2013 })), ["b:3"]);
});

test("a body style shows only that style", () => {
  assert.deepEqual(ids(visible(cars, { body: "sedan" })), ["a:1", "b:3"]);
});

test("four-wheel drive means 4WD or AWD, two-wheel means the rest that say so", () => {
  const awd = { ...camry, id: "d:4", drive: "awd" };
  assert.deepEqual(ids(visible([...cars, awd], { drive: "four" })), ["b:2", "d:4"]);
  assert.deepEqual(ids(visible([...cars, awd], { drive: "two" })), ["a:1"]);
});

test("a fuel shows only cars that run on it", () => {
  assert.deepEqual(ids(visible(cars, { fuel: "hybrid" })), ["a:1"]);
});

test("local lots only leaves out cars sold online", () => {
  assert.deepEqual(ids(visible(cars, { localOnly: true })), ["a:1", "b:2"]);
});

test("under tells how far a car sits below what similar cars ask", () => {
  assert.deepEqual(under(camry), { amount: 1500, share: 0.1875 });
  assert.equal(under(cruze), null);                              // never judged
  assert.equal(under({ ...camry, price: 8200 }), null);          // above typical
});

test("below typical only keeps cars a tenth or more under", () => {
  assert.deepEqual(ids(visible(cars, { underOnly: true })), ["a:1"]);
});

test("best value puts the car furthest under typical first and cars never judged last", () => {
  const dear = { ...camry, id: "e:5", price: 9000 };
  assert.deepEqual(ids(sorted([cruze, dear, f150, camry], "value")), ["a:1", "b:2", "e:5", "b:3"]);
});

test("newest model year first", () => {
  assert.deepEqual(ids(sorted(cars, "year")), ["b:2", "b:3", "a:1"]);
});

test("an order nobody named falls back to best value", () => {
  assert.deepEqual(ids(sorted(cars, "")), ["a:1", "b:2", "b:3"]);
});
