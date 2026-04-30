/* -------------------------------------------------------------------------
 * Team Kudos Board — front-end JS.
 *
 * The page is server-rendered, so this file only handles the bits that feel
 * worse with a full page reload: clicking a reaction emoji updates the count
 * in place without reloading.
 *
 * Plain DOM APIs only — no framework, no build step. The whole file is
 * intentionally short so the project stays easy to read end-to-end.
 * ------------------------------------------------------------------------- */

(function () {
  "use strict";

  // Event delegation: one listener on document handles every reaction button,
  // even ones that haven't been added yet (we don't add any after load today,
  // but it future-proofs the code with no extra cost).
  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".reaction");
    if (!button) return;

    const container = button.closest(".reactions");
    const kudosId = container?.dataset.kudosId;
    const kind = button.dataset.kind;
    if (!kudosId || !kind) return;

    // Optimistic UI: bump the count immediately so the click feels instant,
    // then reconcile with the server's authoritative count when it responds.
    const countEl = button.querySelector(".reaction-count");
    const previous = parseInt(countEl.textContent, 10) || 0;
    countEl.textContent = previous + 1;
    button.classList.remove("bump");
    // Re-trigger the animation by forcing a reflow before re-adding the class.
    void button.offsetWidth;
    button.classList.add("bump");

    try {
      const response = await fetch(`/api/kudos/${kudosId}/react`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const counts = await response.json();
      // Update every reaction count for this kudos so the UI matches the
      // server. Cheap to do all four; saves a future bug if we ever change
      // the endpoint to also adjust other counters.
      container.querySelectorAll(".reaction-count").forEach((el) => {
        const k = el.dataset.kindCount;
        if (k && counts[k] !== undefined) el.textContent = counts[k];
      });
    } catch (err) {
      // Roll back the optimistic update so the count doesn't lie if the
      // request fails (offline, server error, etc).
      countEl.textContent = previous;
      console.error("Reaction failed:", err);
    }
  });
})();
