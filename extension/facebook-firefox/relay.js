// Passes what page.js found to the extension's background, where it is kept. Runs beside the page, in the
// extension's own world, because only that world may talk to the background.
document.addEventListener("carcapture:rows", (event) => {
  try {
    const found = JSON.parse(event.detail);
    const sent = (globalThis.browser || globalThis.chrome).runtime.sendMessage({ kind: "rows", rows: found.rows, looked: found.looked, on: location.pathname });
    sent?.catch?.(() => {});                       // no answer is expected
  } catch (error) { /* the extension was reloaded under the page: nothing to hand to */ }
});
