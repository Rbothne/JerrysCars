// The Facebook capture's choosing and merging, against made-up responses shaped as research/11-facebook-capture.md
// reports them. Real responses hold other people's data and stay out of the repository.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const capture = createRequire(import.meta.url)("../../extension/facebook/capture.js");
const NOW = new Date("2026-11-22T15:00:00Z");
const LATER = new Date("2026-11-23T09:30:00Z");

const card = {
  __typename: "GroupCommerceProductItem", id: "1234567890123456", marketplace_listing_title: "2012 Honda Civic LX",
  listing_price: { amount: "4500.00", formatted_amount: "$4,500", currency: "USD" },
  strikethrough_price: { amount: "5200.00", formatted_amount: "$5,200" },
  custom_sub_titles_with_rendering_flags: [{ subtitle: "142K miles" }],
  location: { reverse_geocode: { city: "Memphis", state: "TN", city_page: { display_name: "Memphis, Tennessee" } } },
  is_sold: false, is_pending: false, primary_listing_photo: { image: { uri: "https://scontent.example/civic.jpg" } },
  marketplace_listing_seller: { __typename: "User", id: "100001", name: "Jane Q Public" },
};
const view = {
  id: "1234567890123456", marketplace_listing_title: "2012 Honda Civic LX", listing_price: { amount: "4300.00", currency: "USD" },
  creation_time: 1795269060, vehicle_make_display_name: "Honda", vehicle_model_display_name: "Civic",
  vehicle_odometer_data: { value: 142350, unit: "MILES" }, vehicle_transmission_type: "AUTOMATIC", vehicle_fuel_type: "GASOLINE",
  vehicle_exterior_color: "Silver", vehicle_condition: "GOOD", vehicle_seller_type: "PRIVATE_SELLER",
  vehicle_identification_number: "1hgcm82633a004352", vehicle_title_status: "CLEAN",
  redacted_description: { text: "Runs great. Call me at 901-555-0100" }, seller_phone_number: "9015550100",
  location: { latitude: 35.11234, longitude: -89.94567, reverse_geocode: { city: "Memphis", state: "TN" },
              reverse_geocode_detailed: { postal_code_trimmed: "38111" } },
  is_sold: false, is_pending: true, listing_photos: [{ image: { uri: "https://scontent.example/driveway.jpg" } }],
};
const sofa = { id: "999", marketplace_listing_title: "Grey sofa, like new", listing_price: { amount: "150" } };

test("listings are found by their shape wherever they sit in a response", () => {
  const response = { data: { marketplace_search: { feed_units: { edges: [{ node: { listing: card } }, { node: { listing: sofa } }] } } } };
  assert.deepEqual(capture.listings(response).map((one) => one.id), ["1234567890123456", "999"]);
});

test("a search card gives what a card shows, and a sofa is no car", () => {
  const [civic] = capture.rows({ edges: [card, sofa] }, NOW);
  assert.deepEqual(capture.rows({ edges: [sofa] }, NOW), []);
  assert.equal(civic.id, "1234567890123456");
  assert.deepEqual([civic.title, civic.price, civic.was, civic.miles, civic.miles_how], ["2012 Honda Civic LX", 4500, 5200, 142000, "card"]);
  assert.deepEqual([civic.city, civic.state, civic.status, civic.year, civic.posted, civic.detail_seen], ["Memphis", "TN", "live", 2012, null, null]);
  assert.deepEqual([civic.seen, civic.first_seen, civic.photo], ["2026-11-22T15:00", "2026-11-22T15:00", "https://scontent.example/civic.jpg"]);
});

test("nothing about the seller, the description, other photos or the person browsing is kept", () => {
  const kept = JSON.stringify(capture.file(Object.fromEntries(capture.rows([card, view], NOW).map((one) => [one.id, one])), NOW));
  for (const word of ["Jane", "100001", "555", "Runs great", "driveway", "marketplace_listing_seller", "redacted"]) {
    assert.ok(!kept.includes(word), word);
  }
});

test("the listing's own view adds the odometer, the listing time and the vehicle's fields", () => {
  const [civic] = capture.rows(view, NOW);
  assert.deepEqual([civic.miles, civic.miles_how, civic.posted, civic.seller_type], [142350, "detail", "2026-11-21T13:51", "private"]);
  assert.deepEqual([civic.make, civic.model, civic.vin, civic.title_status, civic.transmission], ["Honda", "Civic", "1HGCM82633A004352", "clean", "AUTOMATIC"]);
  assert.deepEqual([civic.zip, civic.lat, civic.lon, civic.status, civic.detail_seen], ["38111", 35.11, -89.95, "pending", "2026-11-22T15:00"]);
});

test("merging a later card into a viewed listing keeps the odometer and the view's fields", () => {
  const [viewed] = capture.rows(view, NOW);
  const [carded] = capture.rows({ ...card, listing_price: { amount: "3900" }, is_sold: true }, LATER);
  const merged = capture.merge(viewed, carded);
  assert.deepEqual([merged.miles, merged.miles_how, merged.make, merged.posted], [142350, "detail", "Honda", "2026-11-21T13:51"]);
  assert.deepEqual([merged.price, merged.status, merged.status_seen, merged.seen, merged.first_seen],
    [3900, "sold", "2026-11-23T09:30", "2026-11-23T09:30", "2026-11-22T15:00"]);
});

test("the status's time is when it was first seen so, not every time since", () => {
  const [first] = capture.rows(card, NOW);
  const [again] = capture.rows(card, LATER);
  assert.equal(capture.merge(first, again).status_seen, "2026-11-22T15:00");
});

test("the file holds what was seen in the last three weeks, without the diagnostics", () => {
  const [civic] = capture.rows(view, NOW);
  const old = { ...civic, id: "1", seen: "2026-10-01T10:00" };
  const out = capture.file({ [civic.id]: civic, 1: old }, NOW);
  assert.deepEqual([out.format, out.written, out.horizon_days], [1, "2026-11-22T15:00", 21]);
  assert.deepEqual(out.listings.map((one) => one.id), ["1234567890123456"]);
  assert.equal("_keys" in out.listings[0], false);
});

test("a response of several documents, one a line after for (;;);, is read whole", () => {
  const body = `for (;;);${JSON.stringify({ a: card })}\n${JSON.stringify({ b: sofa })}\nnot json`;
  assert.equal(capture.parseAll(body).length, 2);
});
