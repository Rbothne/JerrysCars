// Runs in the Marketplace page's own world, before its scripts, and only looks: it reads copies of the answers the
// page itself asks Facebook for, and the data the page arrives with. It never asks Facebook for anything itself,
// opens nothing, and waits for nothing. Whatever it finds goes through CarCapture.rows (capture.js), which copies
// out the car's own fields and nothing else, and is handed to relay.js.

(function () {
  "use strict";
  const capture = globalThis.CarCapture;
  if (!capture) return;
  const onMarketplace = () => location.pathname.startsWith("/marketplace");

  function hand(rows, looked) {
    document.dispatchEvent(new CustomEvent("carcapture:rows", { detail: JSON.stringify({ rows, looked }) }));
  }

  function look(body) {
    if (!onMarketplace()) return;
    const documents = capture.parseAll(body);
    if (!documents.length) return;
    const rows = documents.flatMap((one) => capture.rows(one));
    hand(rows, documents.reduce((sum, one) => sum + capture.listings(one).length, 0));
  }

  // The answers to the page's own requests, read from a copy so the page's own reading is untouched.
  const fetched = window.fetch;
  window.fetch = function (...args) {
    const answer = fetched.apply(this, args);
    answer.then((response) => {
      const address = String((args[0] && args[0].url) || args[0] || "");
      if (onMarketplace() && /\/api\/graphql/.test(address)) response.clone().text().then(look, () => {});
    }, () => {});
    return answer;
  };
  const opened = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, address, ...rest) {
    if (/\/api\/graphql/.test(String(address))) {
      this.addEventListener("load", () => { try { look(this.responseText); } catch (error) { /* not text */ } });
    }
    return opened.call(this, method, address, ...rest);
  };

  // The data a Marketplace page arrives with, in its own script blocks.
  function embedded() {
    if (!onMarketplace()) return;
    for (const block of document.querySelectorAll('script[type="application/json"]')) {
      if (block.dataset.carcapture) continue;
      block.dataset.carcapture = "read";
      look(block.textContent);
    }
  }
  document.addEventListener("DOMContentLoaded", embedded);
  new MutationObserver(embedded).observe(document, { childList: true, subtree: true });
})();
