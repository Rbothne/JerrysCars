// Keeps one record per listing seen, and every half hour, when something has changed, writes the whole list as
// one file to the GitHub repository named in the popup or in a packed config.local.json, with its token. Each
// install writes a file of its own, captures/<who>.json, so that several people can run it side by side without
// writing over each other; the build reads them all.

// Chrome runs this as a service worker and loads capture.js here; Firefox runs it as an event page whose manifest
// loads capture.js first. `browser` is Firefox's name for the extension API, `chrome` Chrome's.
if (!globalThis.CarCapture && typeof importScripts === "function") importScripts("capture.js");
const capture = globalThis.CarCapture;
const ext = globalThis.browser || globalThis.chrome;
const VERSION = ext.runtime.getManifest().version;
const DIRECTORY = "captures";

ext.storage.local.setAccessLevel?.({ accessLevel: "TRUSTED_CONTEXTS" });      // Chrome: content scripts may not read the token
ext.alarms.create("upload", { periodInMinutes: 30 });

const get = (keys) => ext.storage.local.get(keys);
const set = (values) => ext.storage.local.set(values);
const today = () => new Date().toISOString().slice(0, 10);

/** The repository, token and name to upload with. A copy handed out ready to run carries them in
 *  config.local.json ({"repo", "token", "who"}), which git ignores; what is typed into the popup wins. An install
 *  with no name of its own gets a random one, so two copies of one package still write two files. */
async function configured() {
  const have = await get(["repo", "token", "who"]);
  if (have.repo && have.token && have.who) return have;
  let packed = {};
  try {
    const answer = await fetch(ext.runtime.getURL("config.local.json"));
    if (answer.ok) packed = await answer.json();
  } catch (error) { /* no packed config: set it in the popup */ }
  const who = have.who || (packed.who ? `${packed.who}-` : "") + crypto.randomUUID().slice(0, 8);
  const values = { repo: have.repo || packed.repo || "", token: have.token || packed.token || "", who: who.replace(/[^a-z0-9-]/gi, "").toLowerCase() };
  await set(values);
  return values;
}
configured();

let queue = Promise.resolve();
const inTurn = (work) => (queue = queue.then(work, work));       // one change to the store at a time

ext.runtime.onMessage.addListener((message) => {
  if (message.kind !== "rows") return;
  inTurn(async () => {
    const { store = {}, paused = false, health = {} } = await get(["store", "paused", "health"]);
    const day = health.day === today() ? health : { day: today(), answers: 0, looked: 0, kept: 0 };
    day.answers += 1;                                 // answers from Facebook read on Marketplace pages today
    day.looked += message.looked || 0;
    if (!paused) {
      for (const fresh of message.rows) store[fresh.id] = capture.merge(store[fresh.id], fresh);
      day.kept += message.rows.length;
    }
    const keys = new Set(health.keys || []);
    for (const one of message.rows) for (const name of one._keys || []) keys.add(name);
    await set({ store, health: { ...day, keys: [...keys].sort() }, ...(!paused && message.rows.length ? { dirty: true } : {}) });
  });
});

/** UTF-8 text as base64, as GitHub's contents API wants it. */
function base64(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (let at = 0; at < bytes.length; at += 0x8000) binary += String.fromCharCode(...bytes.subarray(at, at + 0x8000));
  return btoa(binary);
}

async function upload(force = false) {
  const { token, repo, who } = await configured();
  const { store = {}, dirty, paused } = await get(["store", "dirty", "paused"]);
  if (!token || !repo || paused || (!dirty && !force)) return { skipped: true };
  const address = `https://api.github.com/repos/${repo}/contents/${DIRECTORY}/${who}.json`;
  const headers = { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" };
  const current = await fetch(address, { headers });
  const sha = current.ok ? (await current.json()).sha : undefined;
  const body = JSON.stringify(capture.file(store, new Date(), VERSION), null, 1) + "\n";
  const answer = await fetch(address, {
    method: "PUT", headers: { ...headers, "Content-Type": "application/json" },
    body: JSON.stringify({ message: `Listings seen by ${who}, ${new Date().toISOString().slice(0, 16)}`, content: base64(body), sha }),
  });
  const result = { at: new Date().toISOString(), status: answer.status, ok: answer.ok };
  if (answer.ok) {
    const pruned = Object.fromEntries(Object.entries(store).filter(([, one]) => capture.file({ x: one }).listings.length));
    await set({ store: pruned, dirty: false, lastUpload: result });
  } else {
    await set({ lastUpload: result });
  }
  return result;
}

ext.alarms.onAlarm.addListener((alarm) => { if (alarm.name === "upload") inTurn(() => upload()); });
ext.runtime.onMessage.addListener((message, sender, reply) => {
  if (message.kind !== "upload") return;
  inTurn(() => upload(true)).then(reply, (error) => reply({ ok: false, error: String(error) }));
  return true;                                       // the reply comes later
});
