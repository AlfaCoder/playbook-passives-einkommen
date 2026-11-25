/* Teilen-Button: auf Touch-Geräten das Teilen-Menü des Telefons, sonst WhatsApp, Facebook, E-Mail, Link kopieren.
   Reine Links, keine Skripte von Drittanbietern. */
(() => {
  const url = (document.querySelector('link[rel="canonical"]') || {}).href || location.href.split("#")[0];
  const title = document.title.replace(/\s*·\s*Playbook( Passives Einkommen)?\s*$/, "");
  const e = encodeURIComponent;
  const links = {
    wa: `https://wa.me/?text=${e(title + " " + url)}`,
    fb: `https://www.facebook.com/sharer/sharer.php?u=${e(url)}`,
    mail: `mailto:?subject=${e(title)}&body=${e(title + "\n\n" + url)}`
  };
  const native = () => navigator.share && matchMedia("(pointer: coarse)").matches;

  document.querySelectorAll(".share").forEach(box => {
    const btn = box.querySelector(".share-btn"), alt = box.querySelector(".share-alt"), copy = box.querySelector("[data-copy]");
    alt.querySelectorAll("a[data-k]").forEach(a => (a.href = links[a.dataset.k]));
    btn.addEventListener("click", async () => {
      if (native()) {
        try { await navigator.share({ title, url }); return; }
        catch (err) { if (err && err.name === "AbortError") return; }
      }
      const open = alt.hidden;
      alt.hidden = !open;
      btn.setAttribute("aria-expanded", open);
    });
    copy.addEventListener("click", async () => {
      let ok = false;
      try { await navigator.clipboard.writeText(url); ok = true; } catch (_) {
        const t = document.createElement("textarea"); t.value = url; document.body.append(t); t.select();
        try { ok = document.execCommand("copy"); } catch (_) {} t.remove();
      }
      const old = copy.textContent;
      copy.textContent = ok ? "Link kopiert ✓" : url;
      setTimeout(() => (copy.textContent = old), 2200);
    });
  });
})();
