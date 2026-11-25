/* Verlinkt Glossar-Begriffe im Text (je Begriff einmal pro Seite) und zeigt eine Kurzerklärung.
   Daten: /assets/glossar-data.js (wird von build/build.py aus build/glossar.json erzeugt). */
(() => {
  const G = window.GLOSSAR;
  if (!G || location.pathname.startsWith("/glossar")) return;
  const SKIP = "a,button,h1,h2,h3,h4,h5,h6,summary,script,style,input,select,textarea,label,code,svg,figure,nav,footer," +
    ".cite,.crumbs,.meta,.k,.mmenu,.goal,.st,.step,.chips,.tag,th,.toc,.more,.dl,.lede,[data-nogl]";
  const L = "A-Za-zÄÖÜäöüß0-9_";
  let re;
  try { re = new RegExp(`(?<![${L}-])(?:${G.map(g => `(${g.p})`).join("|")})(?![${L}])`, "g"); }
  catch (e) { return; } // sehr alte Browser ohne Lookbehind: Seite bleibt einfach ohne Glossar-Links

  function link() {
    const root = document.querySelector("main") || document.body;
    const done = new Set();
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.nodeValue.length < 3 || n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    const nodes = [];
    while (tw.nextNode()) nodes.push(tw.currentNode);
    for (const node of nodes) {
      const s = node.nodeValue;
      let m, last = 0, frag = null;
      re.lastIndex = 0;
      while ((m = re.exec(s))) {
        const i = m.slice(1).findIndex(x => x !== undefined);
        if (i < 0 || done.has(i)) continue;
        done.add(i);
        frag = frag || document.createDocumentFragment();
        frag.append(s.slice(last, m.index));
        const a = document.createElement("a");
        a.className = "gl"; a.href = "/glossar/#" + G[i].id; a.dataset.gl = i; a.textContent = m[0];
        frag.append(a);
        last = m.index + m[0].length;
      }
      if (frag) { frag.append(s.slice(last)); node.replaceWith(frag); }
    }
  }

  let pop, cur = null, hideT;
  function show(a) {
    clearTimeout(hideT);
    const g = G[+a.dataset.gl];
    if (!pop) {
      pop = document.createElement("div");
      pop.className = "glpop"; pop.id = "glpop"; pop.setAttribute("role", "tooltip");
      pop.addEventListener("pointerenter", () => clearTimeout(hideT));
      pop.addEventListener("pointerleave", hide);
      document.body.append(pop);
    }
    pop.innerHTML = `<b>${g.t}</b>${g.k}<a href="/glossar/#${g.id}">Im Glossar lesen →</a>`;
    if (cur) cur.removeAttribute("aria-describedby");
    cur = a; a.setAttribute("aria-describedby", "glpop");
    pop.classList.add("on");
    const r = a.getBoundingClientRect(), w = Math.min(300, innerWidth - 24);
    pop.style.width = w + "px";
    const left = Math.max(12, Math.min(r.left + scrollX, scrollX + innerWidth - w - 12));
    pop.style.left = left + "px";
    const below = r.bottom + 8 + pop.offsetHeight < innerHeight;
    pop.style.top = (below ? r.bottom + scrollY + 8 : r.top + scrollY - pop.offsetHeight - 8) + "px";
  }
  function hide() {
    clearTimeout(hideT);
    hideT = setTimeout(() => { if (pop) pop.classList.remove("on"); if (cur) cur.removeAttribute("aria-describedby"); cur = null; }, 150);
  }

  function wire() {
    document.addEventListener("pointerover", e => { const a = e.target.closest("a.gl"); if (a && e.pointerType === "mouse") show(a); });
    document.addEventListener("pointerout", e => { const a = e.target.closest("a.gl"); if (a && e.pointerType === "mouse") hide(); });
    document.addEventListener("focusin", e => { const a = e.target.closest("a.gl"); if (a) show(a); });
    document.addEventListener("focusout", e => { if (e.target.closest("a.gl")) hide(); });
    // Touch: erster Tipp zeigt die Erklärung, der Link darin führt zum Glossar
    document.addEventListener("click", e => {
      const a = e.target.closest("a.gl");
      if (a && matchMedia("(hover: none)").matches && cur !== a) { e.preventDefault(); show(a); return; }
      if (!a && pop && !e.target.closest(".glpop")) { pop.classList.remove("on"); cur = null; }
    });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && pop) { pop.classList.remove("on"); cur = null; } });
  }

  const go = () => { link(); wire(); };
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", go) : go();
})();
