/* Mitscrollendes Inhaltsverzeichnis.
   Playbook (index.html): nutzt die Links aus dem vorhandenen Inhalt-Menü.
   Unterseiten: baut das Verzeichnis aus den h2-Überschriften des Artikels. */
/* Knopf „Nach oben“ – auf allen Seiten, erscheint nach etwas Scrollen. */
(function () {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "totop";
  b.setAttribute("aria-label", "Nach oben");
  b.title = "Nach oben";
  b.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 5l-7 7m7-7l7 7M12 5v14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  b.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    if (history.replaceState && location.hash) history.replaceState(null, "", location.pathname + location.search);
  });
  document.body.appendChild(b);
  const show = () => b.classList.toggle("show", scrollY > 700);
  addEventListener("scroll", show, { passive: true });
  show();
})();

(function () {
  const nav = document.querySelector("nav.top");
  if (!nav) return;
  const slug = s => s.toLowerCase().replace(/[äöüß]/g, c => ({ "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss" }[c]))
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);

  let items = [];       // {id, label, el}
  let details = nav.querySelector("details.toc");
  const panelLinks = () => details ? [...details.querySelectorAll(".tocpanel a[href^='#']")] : [];

  if (details) {
    // Playbook: Abschnitte aus dem Menü übernehmen
    items = panelLinks().map(a => {
      const id = a.getAttribute("href").slice(1);
      return { id, label: a.textContent.trim(), el: document.getElementById(id) };
    }).filter(x => x.el);
  } else {
    // Unterseite: h2 im Artikel
    const hs = [...document.querySelectorAll("article h2")];
    if (hs.length < 3) return;
    const used = new Set();
    items = hs.map(h => {
      let id = h.id || slug(h.textContent);
      while (used.has(id) || (!h.id && document.getElementById(id))) id += "-2";
      used.add(id); h.id = id; h.style.scrollMarginTop = "80px";
      return { id, label: h.textContent.trim(), el: h };
    });
    details = document.createElement("details");
    details.className = "toc auto";
    details.innerHTML = '<summary><span class="lbl">Auf dieser Seite</span></summary><div class="tocpanel"></div>';
    details.querySelector(".tocpanel").innerHTML = items.map(x => `<a href="#${x.id}">${x.label.replace(/</g, "&lt;")}</a>`).join("");
    const wrap = nav.querySelector(".wrap");
    const cta = wrap.querySelector("a.cta");
    wrap.insertBefore(details, cta || null);
  }
  if (!items.length) return;

  const summary = details.querySelector("summary");
  const defaultLabel = details.classList.contains("auto") ? "Auf dieser Seite" : "Inhalt";

  // Seitenleiste
  const side = document.createElement("aside");
  side.className = "sidetoc";
  side.setAttribute("aria-label", "Inhaltsverzeichnis");
  side.innerHTML = "<b>" + (details.classList.contains("auto") ? "Auf dieser Seite" : "Inhalt") + "</b>" +
    items.map(x => `<a href="#${x.id}">${x.label.replace(/</g, "&lt;")}</a>`).join("");
  document.body.appendChild(side);
  const sideLinks = [...side.querySelectorAll("a")];

  // Fortschrittsbalken
  const bar = document.createElement("div");
  bar.className = "readbar";
  nav.appendChild(bar);

  // Position von Seitenleiste und Menü-Panel
  const content = document.querySelector("main") || document.body;
  function place() {
    const nb = nav.getBoundingClientRect().bottom;
    const panel = details.querySelector(".tocpanel");
    if (panel) {
      panel.style.top = (nb + 6) + "px";
      if (innerWidth < 700) { panel.style.left = "16px"; panel.style.right = "16px"; }
      else {
        const r = summary.getBoundingClientRect();
        panel.style.left = ""; panel.style.right = Math.max(16, innerWidth - r.right) + "px";
      }
    }
    const m = content.getBoundingClientRect();
    const wrapEl = document.querySelector("main .wrap, main.wrap, main .read, main.read") || content;
    const w = wrapEl.getBoundingClientRect();
    side.style.top = (nb + 28) + "px";
    side.style.left = (w.left - 250) + "px";
    // Seitenleiste nur, wenn links neben dem Inhalt genug Platz ist; sonst bleibt das Menü oben
    const room = innerWidth >= 1240 && w.left >= 250;
    side.style.display = room ? "" : "none";
    if (details.classList.contains("auto")) details.style.display = room ? "none" : "block";
  }

  // Aktiven Abschnitt bestimmen
  let current = -1;
  function update() {
    const off = nav.getBoundingClientRect().bottom + 40;
    let idx = -1;
    for (let i = 0; i < items.length; i++) if (items[i].el.getBoundingClientRect().top <= off) idx = i;
    if (idx !== current) {
      current = idx;
      panelLinks().concat([...details.querySelectorAll(".tocpanel a")]).forEach(a => a.classList.toggle("on", idx >= 0 && a.getAttribute("href") === "#" + items[idx].id));
      sideLinks.forEach((a, i) => a.classList.toggle("on", i === idx));
      summary.innerHTML = idx >= 0
        ? '<span class="lbl pre">' + defaultLabel + ':</span> ' + items[idx].label.replace(/</g, "&lt;")
        : '<span class="lbl">' + defaultLabel + "</span>";
      if (idx >= 0 && sideLinks[idx]) {
        const a = sideLinks[idx], sr = side.getBoundingClientRect(), ar = a.getBoundingClientRect();
        if (ar.top < sr.top || ar.bottom > sr.bottom) side.scrollTop += ar.top - sr.top - 40;
      }
    }
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.width = (max > 0 ? Math.min(100, scrollY / max * 100) : 0) + "%";
  }

  let ticking = false;
  addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(() => { update(); ticking = false; }); } }, { passive: true });
  addEventListener("resize", () => { place(); update(); });
  details.addEventListener("toggle", place);
  details.querySelectorAll(".tocpanel a").forEach(a => a.addEventListener("click", () => details.removeAttribute("open")));
  document.addEventListener("click", e => { if (details.open && !details.contains(e.target)) details.removeAttribute("open"); });
  place(); update();
})();
