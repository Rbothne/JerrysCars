// The page: load the cars build.py wrote, and show the ones the filters allow. The choosing is in logic.js.

import { DIRECTIONS, amount, marked, sorted, visible } from "./logic.js";

const STEP = 120;                                  // cars drawn at a time
const dollars = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const whole = new Intl.NumberFormat("en-US");
const form = document.getElementById("filters");
const list = document.getElementById("cars");
const more = document.getElementById("more");
let cars = [];
let shown = STEP;

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;       // text only: titles come from other people's websites
  return node;
}

const NAMES = { bmw: "BMW", gmc: "GMC", mini: "MINI", suv: "SUV" };
const named = (word) => NAMES[word] || (word || "").replace(/(^|[\s-])([a-z])/g, (all, gap, letter) => gap + letter.toUpperCase());

/** Fill a select with the values of `field` found in `list`, commonest first, each with its count. */
function choices(select, list, field, label = named) {
  const counts = new Map();
  for (const car of list) if (car[field]) counts.set(car[field], (counts.get(car[field]) || 0) + 1);
  const options = [...counts].sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
  select.replaceChildren(select.options[0], ...options.map(([value, count]) => new Option(`${label(value)} (${count})`, value)));
}

function models() {
  const make = form.elements.make.value;
  choices(form.elements.model, make ? cars.filter((car) => car.make === make) : [], "model", (model) => model);
  form.elements.model.disabled = !make;
}

const web = (address) => (/^https?:\/\//.test(address || "") ? address : null);
const TITLES = { rebuilt: "Rebuilt title", salvage: "Salvage title", lien: "Lien on the title", missing: "No title",
  parts_only: "Parts only", lemon: "Lemon title" };

/** One line on what similar cars ask and what that figure stands on. */
function footing(car) {
  const about = dollars.format(car.typical);
  if (car.title_status && car.title_status !== "clean") return `A clean-title one asks about ${about}`;
  const range = car.low && car.high ? `, most ${dollars.format(car.low)} to ${dollars.format(car.high)}` : "";
  const who = car.seller === "private" ? "Private sellers ask" : "Similar cars ask";
  if (car.basis === "rough") return `Rough figure: ${who.toLowerCase()} about ${about}${range}. None like it for sale.`;
  const near = car.window ? ` within ${car.window[0]} years and ${whole.format(car.window[1])} miles` : "";
  return `${who} about ${about}${range} · ${car.similar} like it${near}`;
}

function card(car) {
  const item = make("li", "car");
  const photo = web(car.photo) ? make("img", "photo") : make("div", "photo");
  if (web(car.photo)) Object.assign(photo, { src: car.photo, alt: "", loading: "lazy", referrerPolicy: "no-referrer" });
  const body = make("div", "body");
  const heading = make("h2");
  const link = make("a", "", car.title);
  if (web(car.url)) Object.assign(link, { href: car.url, rel: "noopener noreferrer", target: "_blank" });
  heading.append(link);
  body.append(heading, make("div", "price", dollars.format(car.price)));
  const fee = car.seller === "private" ? "private sale, no dealer fee"
    : car.fees ? `includes ${dollars.format(car.fees)} dealer fee` : "dealer fee not stated";
  body.append(make("p", "total", car.total ? `${fee} · about ${dollars.format(car.total)} with tax` : fee));
  if (TITLES[car.title_status]) body.append(make("div", "branded", `${TITLES[car.title_status]}, the seller says`));
  if ((car.cautions || []).length) body.append(make("div", "branded", `The seller's title says: ${car.cautions.join(", ")}`));
  const below = marked(car);
  if (below) {
    const badge = make("div", "under", `${dollars.format(below.amount)} under similar cars`);
    badge.title = `Similar cars ask about ${dollars.format(car.typical)}, going by ${car.similar} of them.`;
    body.append(badge);
  }
  if (car.typical) body.append(make("p", "beside", footing(car)));
  if (car.drop) body.append(make("div", "cut", `was ${dollars.format(car.was)}, down ${dollars.format(car.drop)}`));
  const marks = [];
  if (car.one_owner === true) marks.push("One owner (Carfax)");
  if (car.carfax_value) marks.push(`Carfax: ${car.carfax_value} value`);
  if (car.certified === true) marks.push("Certified");
  const cover = car.warranty && (car.warranty.basic || car.warranty.drivetrain);
  if (cover) marks.push(`${car.warranty.basic ? "Warranty" : "Drivetrain warranty"}: ${cover[0]} mo or ${whole.format(cover[1])} mi left`);
  if (car.waiting) marks.push("Not ready for delivery yet");
  if (marks.length) {
    const row = make("div", "marks");
    row.append(...marks.map((mark) => make("span", "mark", mark)));
    body.append(row);
  }
  const miles = car.miles == null ? "mileage not given" : `${whole.format(car.miles)} miles`;
  const yearly = car.per_year == null ? "" : ` (${whole.format(car.per_year)} a year)`;
  const economy = car.mpg ? ` · ${car.mpg[0]}/${car.mpg[1]} mpg` : "";
  body.append(make("p", "facts", `${miles}${yearly}${economy} · listed ${car.days} day${car.days === 1 ? "" : "s"}`));
  const away = car.dealer_miles == null ? "" : ` · ${Math.round(car.dealer_miles)} mi away`;
  const also = car.places <= 1 ? "" : (car.also || []).length ? ` · on ${car.places} sites` : ` · posted ${car.places} times`;
  const where = car.where ? ` · ${car.where}` : "";
  body.append(make("p", "dealer", `${car.dealer || car.dealer_key}${where}${away}${also}`));
  if (car.vin) body.append(make("p", "vin", car.vin));
  const checks = make("p", "checks");
  const outside = (text, href) => Object.assign(make("a", "", text), { href, rel: "noopener noreferrer", target: "_blank" });
  if (web(car.history)) checks.append(outside("Carfax report", car.history));
  if (car.vin) checks.append(outside("Recall check", `https://www.nhtsa.gov/recalls?vin=${encodeURIComponent(car.vin)}`));
  if (checks.childNodes.length) body.append(checks);
  item.append(photo, body);
  return item;
}

function filters() {
  const data = new FormData(form);
  return {
    text: data.get("text"),
    make: data.get("make"),
    model: data.get("model"),
    minPrice: amount(data.get("minPrice")),
    maxPrice: amount(data.get("maxPrice")),
    minYear: amount(data.get("minYear")),
    maxYear: amount(data.get("maxYear")),
    maxMiles: amount(data.get("maxMiles")),
    maxAway: amount(data.get("maxAway")),
    body: data.get("body"),
    drive: data.get("drive"),
    fuel: data.get("fuel"),
    dealer: data.get("dealer"),
    seller: data.get("seller"),
    cleanOnly: data.get("cleanOnly") === "on",
    localOnly: data.get("localOnly") === "on",
    droppedOnly: data.get("droppedOnly") === "on",
    underOnly: data.get("underOnly") === "on",
    oneOwnerOnly: data.get("oneOwnerOnly") === "on",
    certifiedOnly: data.get("certifiedOnly") === "on",
    historyOnly: data.get("historyOnly") === "on",
  };
}

function draw() {
  const matching = sorted(visible(cars, filters()), form.elements.order.value, form.elements.direction.value);
  list.replaceChildren(...matching.slice(0, shown).map(card));
  document.getElementById("count").textContent = `${whole.format(matching.length)} of ${whole.format(cars.length)} cars`;
  document.getElementById("empty").hidden = matching.length > 0;
  more.hidden = matching.length <= shown;
}

form.addEventListener("input", (event) => {
  if (event.target === form.elements.make) models();                 // the old model no longer applies
  if (event.target === form.elements.order) form.elements.direction.value = DIRECTIONS[form.elements.order.value];
  shown = STEP;
  draw();
});
document.getElementById("clear").addEventListener("click", () => { form.reset(); models(); shown = STEP; draw(); });
more.addEventListener("click", () => { shown += STEP; draw(); });

try {
  const answer = await fetch("data/cars.json", { cache: "no-cache" });
  if (!answer.ok) throw new Error(`data/cars.json answered ${answer.status}`);
  const data = await answer.json();
  cars = data.cars;
  choices(form.elements.make, cars, "make");
  choices(form.elements.body, cars, "body");
  const select = form.elements.dealer;
  for (const dealer of [...data.dealers].sort((a, b) => (a.name || a.key).localeCompare(b.name || b.key))) {
    if (dealer.cars) select.append(new Option(`${dealer.name || dealer.key} (${dealer.cars})`, dealer.key));
  }
  const read = data.dealers.filter((dealer) => dealer.ok).length;
  const built = new Date(`${data.built}:00Z`).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  document.getElementById("built").textContent =
    `${whole.format(cars.length)} cars from ${read} of ${data.dealers.length} sources near ${data.area.name}, `
    + `${whole.format(cars.filter((car) => car.seller === "private").length)} of them from private sellers. Last read ${built}.`;
  draw();
} catch (error) {
  document.getElementById("built").textContent = `The car list could not be loaded (${error.message}).`;
}
