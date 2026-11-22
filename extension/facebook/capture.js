// What the extension keeps of a Facebook Marketplace listing, and how two sightings of one are merged. No browser
// API is used here, so tests/js/capture.test.mjs runs it under node. research/11-facebook-capture.md has the plan.
//
// Listings are found by their shape, anywhere in whatever Facebook sends the page: an object with a string `id`
// and a `marketplace_listing_title` or a `listing_price`. Query names, response paths and page layout are never
// relied on, because those are what Facebook changes. Only the fields named in FIELDS are copied out; the seller,
// the description, further photos and anything about the person browsing are never copied, so they never reach
// storage, let alone the public file the build reads.

(function (root) {
  "use strict";

  const HORIZON_DAYS = 21;                         // a listing not seen for this long is dropped from the file

  const minute = (date) => date.toISOString().slice(0, 16);
  const text = (value) => (typeof value === "string" && value.trim() ? value.trim() : null);
  const number = (value) => {
    const found = String(value ?? "").replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
    return found ? Number(found[0]) : null;
  };

  /** Every object anywhere in `value` that looks like a Marketplace listing. */
  function listings(value, found = [], depth = 0) {
    if (!value || typeof value !== "object" || depth > 40) return found;
    if (Array.isArray(value)) {
      for (const item of value) listings(item, found, depth + 1);
      return found;
    }
    if (typeof value.id === "string" && (value.marketplace_listing_title || value.listing_price)) found.push(value);
    for (const key of Object.keys(value)) {
      if (value[key] && typeof value[key] === "object") listings(value[key], found, depth + 1);
    }
    return found;
  }

  /** "120K miles" is 120000, "84,500 miles" 84500. Null when the text says nothing of miles. */
  function cardMiles(listing) {
    for (const line of listing.custom_sub_titles_with_rendering_flags || []) {
      const said = text(line && line.subtitle) || "";
      const thousands = said.match(/(\d+(?:\.\d+)?)\s*K\s*(?:mi|miles)\b/i);
      if (thousands) return Math.round(Number(thousands[1]) * 1000);
      const whole = said.match(/(\d[\d,]*)\s*(?:mi|miles)\b/i);
      if (whole) return number(whole[1]);
    }
    return null;
  }

  /** The value of the first key on `listing` whose name matches `pattern`, as text. Names are not settled. */
  function keyed(listing, pattern) {
    const key = Object.keys(listing).find((name) => pattern.test(name) && text(listing[name]));
    return key ? text(listing[key]) : null;
  }

  const SELLERS = { PRIVATE_SELLER: "private" };
  const TITLES = [["salvage", "salvage"], ["rebuilt", "rebuilt"], ["reconstruct", "rebuilt"], ["lien", "lien"], ["clean", "clean"]];

  /** One capture row from a listing object, at `now`, or null when it is not a vehicle. */
  function row(listing, now) {
    const title = text(listing.marketplace_listing_title) || text(listing.custom_title);
    if (!title) return null;
    const vehicleKeys = Object.keys(listing).filter((name) => name.startsWith("vehicle_"));
    const year = number((title.match(/^\s*((?:19|20)\d\d)\b/) || [])[1]);
    const miles = cardMiles(listing);
    if (!vehicleKeys.length && !year && miles == null) return null;          // a sofa, a phone, a puppy
    const price = listing.listing_price || {};
    const was = listing.strikethrough_price || {};
    const place = listing.location || {};
    const geocode = place.reverse_geocode || {};
    const detailed = place.reverse_geocode_detailed || {};
    const odometer = listing.vehicle_odometer_data || {};
    const detail = vehicleKeys.length > 0;
    const exact = detail && odometer.value != null ? number(odometer.value) * (/km/i.test(odometer.unit || "") ? 0.621371 : 1) : null;
    const vin = (keyed(listing, /vin|identification/i) || "").toUpperCase();
    const titled = (keyed(listing, /^vehicle_.*title/i) || "").toLowerCase();
    const seller = text(listing.vehicle_seller_type);
    const at = minute(now);
    const status = listing.is_sold ? "sold" : listing.is_pending ? "pending" : "live";
    const round = (value) => (number(value) == null ? null : Math.round(number(value) * 100) / 100);
    const photo = ((listing.primary_listing_photo || {}).image || {}).uri || null;
    return {
      id: listing.id, first_seen: at, seen: at, detail_seen: detail ? at : null, status, status_seen: at,
      title, price: number(price.amount), currency: text(price.currency) || "USD", was: number(was.amount),
      miles: exact != null ? Math.round(exact) : miles, miles_how: exact != null ? "detail" : miles != null ? "card" : null,
      posted: listing.creation_time ? minute(new Date(Number(listing.creation_time) * 1000)) : null,
      seller_type: seller ? SELLERS[seller] || "dealer" : null,
      year, make: text(listing.vehicle_make_display_name), model: text(listing.vehicle_model_display_name),
      vin: vin.length === 17 ? vin : null,
      title_status: (TITLES.find(([word]) => titled.includes(word)) || [])[1] || null,
      transmission: text(listing.vehicle_transmission_type), fuel: text(listing.vehicle_fuel_type),
      color: text(listing.vehicle_exterior_color), condition: text(listing.vehicle_condition),
      city: text(geocode.city), state: text(geocode.state), zip: text(detailed.postal_code_trimmed),
      lat: round(place.latitude), lon: round(place.longitude),
      photo: typeof photo === "string" && /^https:\/\//.test(photo) ? photo : null,
      _keys: vehicleKeys,
    };
  }

  /** Every capture row in a response Facebook sent the page (already parsed), at `now`. */
  function rows(value, now = new Date()) {
    const seen = new Map();
    for (const listing of listings(value)) {
      const made = row(listing, now);
      if (made) seen.set(made.id, seen.has(made.id) ? merge(seen.get(made.id), made) : made);
    }
    return [...seen.values()];
  }

  /** One listing from what was known of it and a new sighting. A card's rounded mileage never replaces the
   *  odometer read from the listing's own view, and a field the new sighting lacks keeps its old value. */
  function merge(old, fresh) {
    if (!old) return fresh;
    const out = { ...old };
    for (const [name, value] of Object.entries(fresh)) {
      if (value != null && !["first_seen", "status_seen", "miles", "miles_how", "detail_seen", "_keys"].includes(name)) out[name] = value;
    }
    out.first_seen = old.first_seen < fresh.first_seen ? old.first_seen : fresh.first_seen;
    out.seen = old.seen > fresh.seen ? old.seen : fresh.seen;
    out.detail_seen = fresh.detail_seen || old.detail_seen;
    out.status_seen = fresh.status === old.status ? old.status_seen : fresh.status_seen;
    if (fresh.miles_how === "detail" || (old.miles_how !== "detail" && fresh.miles != null)) {
      out.miles = fresh.miles;
      out.miles_how = fresh.miles_how;
    }
    out._keys = [...new Set([...(old._keys || []), ...(fresh._keys || [])])];
    return out;
  }

  /** The whole file the build reads: every listing seen in the last HORIZON_DAYS, without the diagnostics. */
  function file(store, now = new Date(), version = "0.1.0") {
    const cutoff = minute(new Date(now.getTime() - HORIZON_DAYS * 86400000));
    const kept = Object.values(store).filter((one) => one.seen >= cutoff).sort((a, b) => (a.id < b.id ? -1 : 1));
    return { format: 1, written: minute(now), extension: version, horizon_days: HORIZON_DAYS,
             listings: kept.map(({ _keys, ...one }) => one) };
  }

  /** Facebook answers some requests with several JSON documents, one a line, sometimes after "for (;;);". */
  function parseAll(body) {
    const out = [];
    for (const line of String(body || "").replace(/^for \(;;\);/, "").split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || (trimmed[0] !== "{" && trimmed[0] !== "[")) continue;
      try { out.push(JSON.parse(trimmed)); } catch (error) { /* not JSON: not ours */ }
    }
    return out;
  }

  const api = { HORIZON_DAYS, listings, row, rows, merge, file, parseAll };
  if (typeof module === "object" && module.exports) module.exports = api;
  root.CarCapture = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
