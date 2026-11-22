import assert from "node:assert/strict";
import test from "node:test";

import { DIRECTIONS, amount, lotCost, lotsSorted, sorted, under, visible } from "../../site/logic.js";

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

const crv = { id: "c:4", title: "2019 Honda CR-V EX", make: "honda", model: "CR-V", price: 18000 };
const truck = { id: "c:5", title: "2017 Ford F150 SuperCrew Cab Lariat", make: "ford", model: "F-150", price: 21000 };
const tesla = { id: "c:6", title: "2020 Tesla Model 3 Long Range", make: "tesla", model: "Model 3", price: 19000 };
const rogue = { id: "c:7", title: "2018 Nissan Rogue SV", make: "nissan", model: "Rogue", price: 12000 };
const vogue = { id: "c:8", title: "2016 Land Rover Range Rover Vogue", make: "land rover", model: "Range Rover", price: 30000 };
const corolla = { id: "c:9", title: "2015 Toyota Corolla L", make: "toyota", model: "Corolla", price: 8000 };
const scion = { id: "c:10", title: "2016 Scion iM base", make: "toyota", model: "iM", price: 9000 };

test("search ignores the hyphens and spaces inside a model name", () => {
  const list = [f150, crv, truck, tesla, camry];
  for (const typed of ["f150", "F-150", "f 150"]) assert.deepEqual(ids(visible(list, { text: typed })), ["b:2", "c:5"], typed);
  for (const typed of ["crv", "cr-v"]) assert.deepEqual(ids(visible(list, { text: typed })), ["c:4"], typed);
  assert.deepEqual(ids(visible(list, { text: "model3" })), ["c:6"]);
});

test("a name typed as letters then a number is read as one name when some car has it", () => {
  const van = { id: "e", title: "2014 Ford E-150 Cargo", make: "ford", model: "E-150" };       // has an "f" and a "150"
  assert.deepEqual(ids(visible([f150, truck, van], { text: "f 150" })), ["b:2", "c:5"]);
  assert.deepEqual(ids(visible([f150, truck, van], { text: "xlt f 150" })), ["b:2"]);
});

test("a word and a number that are no car's name stay two words", () => {
  assert.deepEqual(ids(visible(cars, { text: "camry 2012" })), ["a:1"]);
});

test("letters typed across two words of a title are not a match", () => {
  assert.deepEqual(ids(visible([corolla, camry], { text: "taco" })), []);      // "toyoTA COrolla"
});

test("search knows the common nicknames for a make", () => {
  assert.deepEqual(ids(visible(cars, { text: "chevy cruze" })), ["b:3"]);
  assert.deepEqual(ids(visible([{ id: "v", title: "2014 Volkswagen Jetta SE" }, camry], { text: "vw" })), ["v"]);
});

test("a misspelled word finds the names one slip away", () => {
  assert.deepEqual(ids(visible(cars, { text: "camery" })), ["a:1"]);          // a letter too many
  assert.deepEqual(ids(visible(cars, { text: "chevorlet" })), ["b:3"]);       // two letters swapped
  assert.deepEqual(ids(visible(cars, { text: "toyta 2012" })), ["a:1"]);      // a letter missing
  assert.deepEqual(ids(visible([{ id: "v", title: "2014 Volkswagen Jetta SE" }, camry], { text: "volkswagon" })), ["v"]);
});

test("a misspelling still matches while the word is only half typed", () => {
  assert.deepEqual(ids(visible(cars, { text: "chevor" })), ["b:3"]);
});

test("a word spelled right is not widened to its near misses", () => {
  assert.deepEqual(ids(visible([rogue, vogue], { text: "rogue" })), ["c:7"]);
});

test("a misspelling is not matched to a word that starts with another letter", () => {
  assert.deepEqual(ids(visible([vogue], { text: "rogue" })), []);
});

test("years and other numbers are never guessed at", () => {
  assert.deepEqual(ids(visible(cars, { text: "2014" })), []);
});

test("short words are never guessed at", () => {
  assert.deepEqual(ids(visible([{ id: "k", title: "2018 Kia Soul Base" }], { text: "kio" })), []);
});

test("search reads the make and model as well as the title", () => {
  assert.deepEqual(ids(visible([scion, crv], { text: "toyota" })), ["c:10"]);
  assert.deepEqual(ids(visible([truck, crv], { text: "f-150" })), ["c:5"]);
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

test("days listed runs newest first, and longest first when turned round", () => {
  assert.deepEqual(ids(sorted(cars, "days")), ["a:1", "b:3", "b:2"]);
  assert.deepEqual(ids(sorted(cars, "days", "desc")), ["b:2", "b:3", "a:1"]);
});

test("every field can be turned round", () => {
  assert.deepEqual(ids(sorted(cars, "price", "desc")), ["b:2", "a:1", "b:3"]);
  assert.deepEqual(ids(sorted(cars, "drop", "asc")), ["a:1", "b:3", "b:2"]);
  assert.deepEqual(ids(sorted(cars, "year", "asc")), ["a:1", "b:3", "b:2"]);
});

test("a car that lacks the figure goes last whichever way the order runs", () => {
  assert.deepEqual(ids(sorted(cars, "miles", "asc")), ["b:2", "a:1", "b:3"]);
  assert.deepEqual(ids(sorted(cars, "miles", "desc")), ["a:1", "b:2", "b:3"]);
  assert.deepEqual(ids(sorted(cars, "value", "asc")), ["b:2", "a:1", "b:3"]);
});

test("cars that tie keep the order they came in, whichever way the order runs", () => {
  const twin = { ...camry, id: "z:9" };
  assert.deepEqual(ids(sorted([camry, twin, f150], "price", "asc")), ["a:1", "z:9", "b:2"]);
  assert.deepEqual(ids(sorted([camry, twin, f150], "price", "desc")), ["b:2", "a:1", "z:9"]);
});

test("each field starts in the direction a buyer usually wants", () => {
  assert.deepEqual(DIRECTIONS, { value: "desc", price: "asc", drop: "desc", share: "desc",
    year: "desc", miles: "asc", peryear: "asc", days: "asc", away: "asc" });
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

test("an amount typed with a dollar sign, commas or spaces is read as its whole dollars", () => {
  assert.equal(amount("$12,500"), 12500);
  assert.equal(amount(" 8 000 "), 8000);
  assert.equal(amount("12500.75"), 12500);
  assert.equal(amount("2019"), 2019);
});

test("an amount left empty or with no digits is no limit", () => {
  assert.equal(amount(""), 0);
  assert.equal(amount(null), 0);
  assert.equal(amount("any"), 0);
});

test("fewest miles for its age first, unknown last", () => {
  const list = [{ ...camry, per_year: 8946 }, { ...f150, per_year: 8166 }, { ...cruze, per_year: null }];
  assert.deepEqual(ids(sorted(list, "peryear")), ["b:2", "a:1", "b:3"]);
});

test("one owner only, certified only and history report only each keep the cars that say so", () => {
  const list = [{ ...camry, one_owner: true, certified: null, history: "https://www.carfax.com/vehiclehistory/x" },
    { ...f150, one_owner: false, certified: true, history: null }, { ...cruze, one_owner: null, certified: false, history: null }];
  assert.deepEqual(ids(visible(list, { oneOwnerOnly: true })), ["a:1"]);
  assert.deepEqual(ids(visible(list, { certifiedOnly: true })), ["b:2"]);
  assert.deepEqual(ids(visible(list, { historyOnly: true })), ["a:1"]);
});

test("sold by keeps private sellers' cars, or dealers' cars", () => {
  const mine = { ...camry, id: "p:1", seller: "private", kind: "private" };
  const list = [mine, { ...f150, seller: "dealer" }, { ...cruze, seller: "dealer" }];
  assert.deepEqual(ids(visible(list, { seller: "private" })), ["p:1"]);
  assert.deepEqual(ids(visible(list, { seller: "dealer" })), ["b:2", "b:3"]);
  assert.deepEqual(ids(visible(list, { seller: "" })), ["p:1", "b:2", "b:3"]);
});

test("local lots only keeps private sellers' cars", () => {
  const mine = { ...camry, id: "p:1", seller: "private", kind: "private" };
  assert.deepEqual(ids(visible([mine, cruze], { localOnly: true })), ["p:1"]);
});

test("clean titles only leaves out a car whose seller names another title, and keeps one that says nothing", () => {
  const rebuilt = { ...camry, id: "p:2", seller: "private", title_status: "rebuilt" };
  const clean = { ...camry, id: "p:3", seller: "private", title_status: "clean" };
  assert.deepEqual(ids(visible([rebuilt, clean, f150], { cleanOnly: true })), ["p:3", "b:2"]);
  assert.deepEqual(ids(visible([rebuilt, clean, f150], {})), ["p:2", "p:3", "b:2"]);
});

test("a dealer's cars include the ones shown under another dealer that lists them too", () => {
  const shared = { ...camry, id: "a:9", dealer_key: "a", also: ["b", "c"] };
  assert.deepEqual(ids(visible([shared, f150, cruze], { dealer: "c" })), ["a:9"]);
  assert.deepEqual(ids(visible([shared, f150, cruze], { dealer: "b" })), ["a:9", "b:2", "b:3"]);
  assert.deepEqual(ids(visible([shared, f150, cruze], { dealer: "a" })), ["a:9"]);
});

test("within so many miles leaves out cars known to be farther, and keeps one whose distance is not known", () => {
  const near = { ...camry, id: "n", dealer_miles: 12.4 };
  const far = { ...camry, id: "f", dealer_miles: 113.1 };
  const delivered = { ...camry, id: "d", dealer_miles: null };
  assert.deepEqual(ids(visible([near, far, delivered], { maxAway: 60 })), ["n", "d"]);
  assert.deepEqual(ids(visible([near, far, delivered], { maxAway: 0 })), ["n", "f", "d"]);
});

test("nearest first, cars of unknown distance last", () => {
  const near = { ...camry, id: "n", dealer_miles: 12.4 };
  const far = { ...camry, id: "f", dealer_miles: 113.1 };
  const delivered = { ...camry, id: "d", dealer_miles: null };
  assert.deepEqual(ids(sorted([far, delivered, near], "away")), ["n", "f", "d"]);
  assert.equal(DIRECTIONS.away, "asc");
});

// ---- auction lots ------------------------------------------------------------------------------------------------

const impound = { key: "v", premium: 0.1, fee: 10, card: 0.04 };
const lotA = { id: "v:1-1", title: "2012 TOYOTA CAMRY LE", make: "toyota", model: "Camry", price: 450, kind: "bid", ends: "2026-11-25T15:30", lot: "2",
  asks: { median: 7500, count: 3 } };
const lotB = { id: "v:1-2", title: "2009 SCION TC", make: "scion", model: "tC", price: 10, kind: "starting", ends: "2026-11-25T15:30", lot: "10", asks: null };
const lotC = { id: "v:0-9", title: "2015 FORD F-150", make: "ford", model: "F-150", price: 2600, kind: "sold", ends: "2026-11-18T16:02", lot: "1",
  asks: { median: 14000, count: 5 } };

test("what a winning bid costs adds the buyer's premium and the fee per lot", () => {
  assert.equal(lotCost(575, impound), 642.5);                 // the auction's own example: $575 is $642.50 in cash
  assert.equal(lotCost(0, impound), null);
  assert.equal(lotCost(575, undefined), null);
  assert.equal(lotCost(575, { key: "w" }), 575);
});

test("lots run in sale order: the sale first, then the lot number as a number", () => {
  assert.deepEqual(ids(lotsSorted([lotB, lotC, lotA], "sale")), ["v:0-9", "v:1-1", "v:1-2"]);
});

test("results run newest first", () => {
  assert.deepEqual(ids(lotsSorted([lotC, lotA, lotB], "newest")), ["v:1-1", "v:1-2", "v:0-9"]);
});

test("lots by price, and by how far the bid sits under what such cars ask, unknown last", () => {
  assert.deepEqual(ids(lotsSorted([lotA, lotB, lotC], "price")), ["v:1-2", "v:1-1", "v:0-9"]);
  assert.deepEqual(ids(lotsSorted([lotB, lotA, lotC], "gap")), ["v:0-9", "v:1-1", "v:1-2"]);
});

test("the search and make filters work on lots as they do on cars", () => {
  assert.deepEqual(ids(visible([lotA, lotB, lotC], { text: "camry" })), ["v:1-1"]);
  assert.deepEqual(ids(visible([lotA, lotB, lotC], { make: "ford" })), ["v:0-9"]);
  assert.deepEqual(ids(visible([lotA, lotB, lotC], { maxPrice: 1000 })), ["v:1-1", "v:1-2"]);
});
