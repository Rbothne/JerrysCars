const $ = (id) => document.getElementById(id);
const ext = globalThis.browser || globalThis.chrome;
// Firefox may leave site access to be granted by hand; Chrome grants it at install, so the button stays hidden.
const SITES = { origins: ["https://www.facebook.com/*", "https://api.github.com/*"] };
const ago = (stamp) => {
  if (!stamp) return "never";
  const minutes = Math.round((Date.now() - new Date(stamp)) / 60000);
  return minutes < 60 ? `${minutes} min ago` : minutes < 2880 ? `${Math.round(minutes / 60)} h ago` : `${Math.round(minutes / 1440)} days ago`;
};

async function show() {
  const { store = {}, health = {}, lastUpload, repo = "", token, paused = false, who = "" } =
    await ext.storage.local.get(["store", "health", "lastUpload", "repo", "token", "paused", "who"]);
  $("allow").hidden = !ext.permissions || (await ext.permissions.contains(SITES));
  const all = Object.values(store);
  $("count").textContent = `${all.length} vehicles kept, ${all.filter((one) => one.detail_seen).length} of them opened.`;
  const isToday = health.day === new Date().toISOString().slice(0, 10);
  $("today").textContent = isToday ? `Today: ${health.looked} listings looked at, ${health.kept} vehicle sightings kept.` : "Nothing seen today.";
  $("blind").hidden = !(isToday && health.answers >= 5 && health.looked === 0);   // read Facebook's answers, found no listing in any
  $("upload").textContent = !repo || !token ? "No repository and token yet: nothing is sent anywhere."
    : lastUpload ? `Last upload ${ago(lastUpload.at)}: ${lastUpload.ok ? "done" : `refused (${lastUpload.status})`}.` : "Not uploaded yet.";
  $("upload").className = lastUpload && !lastUpload.ok ? "warn" : "";
  $("repo").value = repo;
  $("who").value = who;
  $("where").textContent = repo && who ? `Writes ${repo}/captures/${who}.json` : "";
  $("token").placeholder = token ? "saved (type to replace)" : "kept in this browser only";
  $("paused").checked = paused;
  $("keys").textContent = (health.keys || []).join(", ") || "none yet";
}

$("save").addEventListener("click", async () => {
  const values = { repo: $("repo").value.trim() };
  const who = $("who").value.trim().replace(/[^a-z0-9-]/gi, "").toLowerCase();
  if (who) values.who = who;
  if ($("token").value.trim()) values.token = $("token").value.trim();
  await ext.storage.local.set(values);
  $("token").value = "";
  show();
});
$("paused").addEventListener("change", async () => { await ext.storage.local.set({ paused: $("paused").checked }); show(); });
$("allow").addEventListener("click", async () => { await ext.permissions.request(SITES); show(); });
$("now").addEventListener("click", async () => {
  $("upload").textContent = "Uploading...";
  await ext.runtime.sendMessage({ kind: "upload" });
  show();
});
show();
