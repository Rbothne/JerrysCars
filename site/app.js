// The page: load the cars build.py wrote, and show the ones the filters allow. The choosing is in logic.js.

import { sorted, visible } from "./logic.js";

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

const web = (address) => (/^https?:\/\//.test(address || "") ? address : null);

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
  if (car.drop) body.append(make("div", "cut", `was ${dollars.format(car.was)}, down ${dollars.format(car.drop)}`));
  const miles = car.miles == null ? "mileage not given" : `${whole.format(car.miles)} miles`;
  body.append(make("p", "facts", `${miles} · listed ${car.days} day${car.days === 1 ? "" : "s"}`));
  const away = car.dealer_miles == null ? "" : ` · ${Math.round(car.dealer_miles)} mi away`;
  const also = car.places > 1 ? ` · on ${car.places} sites` : "";
  body.append(make("p", "dealer", `${car.dealer || car.dealer_key}${away}${also}`));
  if (car.vin) body.append(make("p", "vin", car.vin));
  item.append(photo, body);
  return item;
}

function filters() {
  const data = new FormData(form);
  return {
    text: data.get("text"),
    maxPrice: Number(data.get("maxPrice")) || 0,
    maxMiles: Number(data.get("maxMiles")) || 0,
    dealer: data.get("dealer"),
    droppedOnly: data.get("droppedOnly") === "on",
  };
}

function draw() {
  const matching = sorted(visible(cars, filters()), new FormData(form).get("order"));
  list.replaceChildren(...matching.slice(0, shown).map(card));
  document.getElementById("count").textContent = `${whole.format(matching.length)} of ${whole.format(cars.length)} cars`;
  document.getElementById("empty").hidden = matching.length > 0;
  more.hidden = matching.length <= shown;
}

form.addEventListener("input", () => { shown = STEP; draw(); });
more.addEventListener("click", () => { shown += STEP; draw(); });

try {
  const answer = await fetch("data/cars.json", { cache: "no-cache" });
  if (!answer.ok) throw new Error(`data/cars.json answered ${answer.status}`);
  const data = await answer.json();
  cars = data.cars;
  const select = form.elements.dealer;
  for (const dealer of [...data.dealers].sort((a, b) => (a.name || a.key).localeCompare(b.name || b.key))) {
    if (dealer.cars) select.append(new Option(`${dealer.name || dealer.key} (${dealer.cars})`, dealer.key));
  }
  const read = data.dealers.filter((dealer) => dealer.ok).length;
  const built = new Date(`${data.built}:00Z`).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  document.getElementById("built").textContent =
    `${whole.format(cars.length)} cars from ${read} of ${data.dealers.length} dealers near ${data.area.name}. Last read ${built}.`;
  draw();
} catch (error) {
  document.getElementById("built").textContent = `The car list could not be loaded (${error.message}).`;
}
