// The auction page: the lots build.py wrote to data/auctions.json. Choosing and ordering are in logic.js.

import { amount, lotAllIn, lotCost, lotsSorted, visible } from "./logic.js";

const STEP = 120;                                  // lots drawn at a time
const dollars = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const whole = new Intl.NumberFormat("en-US");
const day = new Intl.DateTimeFormat([], { weekday: "short", month: "short", day: "numeric" });
const hour = new Intl.DateTimeFormat([], { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const form = document.getElementById("filters");
const list = document.getElementById("cars");
const more = document.getElementById("more");
let data = { lots: [], results: [], notices: [], places: [] };
let shown = STEP;

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;       // text only: titles come from someone else's website
  return node;
}

const web = (address) => (/^https?:\/\//.test(address || "") ? address : null);
const when = (stamp) => new Date(`${stamp}:00Z`);  // the build keeps times in UTC, to the minute
const NAMES = { bmw: "BMW", gmc: "GMC", mini: "MINI" };
const named = (word) => NAMES[word] || (word || "").replace(/(^|[\s-])([a-z])/g, (all, gap, letter) => gap + letter.toUpperCase());

function card(lot, over) {
  const item = make("li", "car");
  const photo = web(lot.photo) ? make("img", "photo") : make("div", "photo");
  if (web(lot.photo)) Object.assign(photo, { src: lot.photo, alt: "", loading: "lazy", referrerPolicy: "no-referrer" });
  const body = make("div", "body");
  const heading = make("h2");
  const link = make("a", "", lot.title);
  if (web(lot.url)) Object.assign(link, { href: lot.url, rel: "noopener noreferrer", target: "_blank" });
  heading.append(link);
  body.append(heading);

  const bids = lot.bids ? ` · ${lot.bids} bid${lot.bids === 1 ? "" : "s"}` : "";
  if (over) {
    body.append(make("div", "price", lot.price ? dollars.format(lot.price) : "no figure"));
    body.append(make("p", "total", `${lot.sold ? "sold" : "not sold: the last bid"}${bids} · ${day.format(when(lot.ends))}`));
  } else {
    body.append(make("div", "price", lot.kind === "bid" ? dollars.format(lot.price) : "No bids yet"));
    const cost = lotCost(lot.price, data.places.find((place) => place.key === lot.place));
    body.append(make("p", "total", lot.kind === "bid"
      ? `bid so far${bids}${cost ? ` · costs about ${dollars.format(cost)} before tax` : ""}`
      : `opens at ${dollars.format(lot.price || 0)}`));
    if (lot.ends) body.append(make("p", "sale", `Sale starts ${hour.format(when(lot.ends))}${lot.lot ? ` · lot ${lot.lot}` : ""}`));
  }
  const place = data.places.find((one) => one.key === lot.place);
  const allIn = (over ? lot.sold : lot.kind === "bid") ? lotAllIn(lot.price, place, data.assume) : null;
  if (allIn) {
    body.append(make("p", "beside", `All in about ${dollars.format(Math.round(allIn / 50) * 50)}: what it must sell for to get the money back`));
  }
  if (lot.parts_only) body.append(make("div", "branded", "For parts only: cannot be registered"));
  if (lot.back) {
    body.append(make("div", "cut", lot.back.sold
      ? `Back again: sold for ${dollars.format(lot.back.price)} on ${day.format(new Date(`${lot.back.when}T12:00:00Z`))}`
      : `Back again: not sold on ${day.format(new Date(`${lot.back.when}T12:00:00Z`))}`));
  }
  if (lot.before) {
    const spread = lot.before.count > 1 ? `, from ${dollars.format(lot.before.low)} to ${dollars.format(lot.before.high)}` : "";
    body.append(make("p", "beside", `Sold here before: about ${dollars.format(lot.before.median)}${spread} (${lot.before.count} like it)`));
  }
  if (lot.asks) {
    body.append(make("p", "beside", `For sale around Memphis, such cars ask about ${dollars.format(lot.asks.median)} (${lot.asks.count})`));
  }
  if (lot.vin) {
    body.append(make("p", "vin", lot.vin));
    const checks = make("p", "checks");
    checks.append(Object.assign(make("a", "", "Recall check"), { rel: "noopener noreferrer", target: "_blank",
      href: `https://www.nhtsa.gov/recalls?vin=${encodeURIComponent(lot.vin)}` }));
    body.append(checks);
  }
  item.append(photo, body);
  return item;
}

/** A car in a lien-sale notice: no price, a day, an hour and a place. */
function noticeCard(car) {
  const item = make("li", "car");
  const body = make("div", "body");
  const heading = make("h2");
  const link = make("a", "", car.title);
  if (web(car.url)) Object.assign(link, { href: car.url, rel: "noopener noreferrer", target: "_blank" });
  heading.append(link);
  body.append(heading);
  const decoded = [car.year, named(car.make), car.model].filter(Boolean).join(" ");
  if (decoded && decoded.toLowerCase() !== car.title.toLowerCase()) body.append(make("p", "facts", `By its VIN: ${decoded}`));
  const sale = car.ends ? day.format(new Date(`${car.ends.slice(0, 10)}T12:00:00Z`)) : "day not read";
  body.append(make("div", "price", sale));
  body.append(make("p", "total", [car.hour ? `at ${car.hour}` : "hour not given", car.address || "address not read"].join(" · ")));
  if (car.seller) body.append(make("p", "dealer", car.seller));
  if (car.before) body.append(make("p", "beside", `At the impound auction such cars sold for about ${dollars.format(car.before.median)} (${car.before.count})`));
  if (car.asks) body.append(make("p", "beside", `For sale around Memphis, such cars ask about ${dollars.format(car.asks.median)} (${car.asks.count})`));
  if (car.vin) {
    body.append(make("p", "vin", car.vin));
    const checks = make("p", "checks");
    checks.append(Object.assign(make("a", "", "Recall check"), { rel: "noopener noreferrer", target: "_blank",
      href: `https://www.nhtsa.gov/recalls?vin=${encodeURIComponent(car.vin)}` }));
    body.append(checks);
  }
  item.append(body);
  return item;
}

function choices(select, lots) {
  const counts = new Map();
  for (const lot of lots) if (lot.make) counts.set(lot.make, (counts.get(lot.make) || 0) + 1);
  const options = [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const kept = select.value;
  select.replaceChildren(select.options[0], ...options.map(([value, count]) => new Option(`${named(value)} (${count})`, value)));
  select.value = counts.has(kept) ? kept : "";
}

const listed = () => ({ results: data.results, notices: data.notices || [] })[form.elements.view.value] || data.lots;

function draw() {
  const view = form.elements.view.value;
  const over = view === "results";
  const all = view === "notices" ? data.notices || [] : over ? data.results : data.lots;
  const picked = new FormData(form);
  const matching = lotsSorted(visible(all, { text: picked.get("text"), make: picked.get("make"),
    maxPrice: amount(picked.get("maxPrice")) }), form.elements.order.value);
  list.replaceChildren(...matching.slice(0, shown).map((lot) => (view === "notices" ? noticeCard(lot) : card(lot, over))));
  document.getElementById("count").textContent = `${whole.format(matching.length)} of ${whole.format(all.length)} ${view === "notices" ? "cars" : over ? "results" : "lots"}`;
  const empty = document.getElementById("empty");
  empty.hidden = matching.length > 0;
  empty.textContent = all.length ? "No lots match those filters."
    : over ? "No results on record yet." : "No lots are posted for the next sale yet. The list goes up the Monday evening before each Wednesday sale.";
  more.hidden = matching.length <= shown;
}

form.addEventListener("input", (event) => {
  if (event.target === form.elements.view) {
    form.elements.order.value = form.elements.view.value === "results" ? "newest" : "sale";
    choices(form.elements.make, listed());
  }
  shown = STEP;
  draw();
});
more.addEventListener("click", () => { shown += STEP; draw(); });

try {
  const answer = await fetch("data/auctions.json", { cache: "no-cache" });
  if (!answer.ok) throw new Error(`data/auctions.json answered ${answer.status}`);
  data = await answer.json();
  const asked = location.hash.slice(1);              // auctions.html#notices opens on that view
  if (["lots", "results", "notices"].includes(asked)) form.elements.view.value = asked;
  else if (!data.lots.length && data.results.length) form.elements.view.value = "results";
  form.elements.order.value = form.elements.view.value === "results" ? "newest" : "sale";
  choices(form.elements.make, listed());
  const sold = data.results.filter((lot) => lot.sold);
  const built = new Date(`${data.built}:00Z`).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  document.getElementById("built").textContent =
    `${whole.format(data.lots.length)} lots coming up, ${whole.format(sold.length)} sold lots on record, and `
    + `${whole.format((data.notices || []).length)} cars in lien-sale notices. Last read ${built}.`;
  draw();
} catch (error) {
  document.getElementById("built").textContent = `The auction list could not be loaded (${error.message}).`;
}
