"""Baut die Unterseiten, Vorschaubilder, das Arbeitsheft-PDF und die Sitemap.

Aufruf (im Ordner site/):  python build/build.py
Konfiguration: build/config.json  (z. B. Amazon-Partner-Tag)
"""
import html, io, json, os, re, subprocess, sys, tempfile, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # site/
B = os.path.join(ROOT, "build")
DOMAIN = "https://playbook-passives-einkommen.de"
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium",
]
CFG = json.load(io.open(os.path.join(B, "config.json"), encoding="utf-8"))
TODAY = CFG.get("stand", "2026-11-23")

def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
def esc(s): return html.escape(s, quote=True)
def chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c) or not c.endswith(".exe"):
            return c
    sys.exit("Kein Chrome/Edge gefunden")

# --- Quellen aus dem Playbook übernehmen (Kanal + Titel je Video-ID) ---
idx = rd(os.path.join(ROOT, "index.html"))
SRC = {}
for m in re.finditer(r'"([\w-]{11})":\["([^"]*)","([^"]*)"', idx):
    SRC.setdefault(m.group(1), (m.group(2), m.group(3)))

def yt_links(body):
    def r(m):
        vid, label = m.group(1), m.group(2)
        if vid not in SRC:
            sys.exit(f"Unbekannte Video-ID {vid}")
        ch, title = SRC[vid]
        return f'<a href="https://www.youtube.com/watch?v={vid}" rel="noopener" title="{esc(ch)}: {esc(title)}">{label or esc(ch)}</a>'
    return re.sub(r"\[\[([\w-]{11})(?:\|([^\]]+))?\]\]", r, body)

# --- Seiten einlesen ---
PAGES = []
for fn in sorted(os.listdir(os.path.join(B, "pages"))):
    if not fn.endswith(".html"):
        continue
    raw = rd(os.path.join(B, "pages", fn))
    m = re.match(r"\s*<!--(.*?)-->\s*(.*)", raw, re.S)
    meta = json.loads(m.group(1)); meta["body"] = m.group(2); meta["slug"] = fn[:-5]
    PAGES.append(meta)
PAGES.sort(key=lambda p: p.get("order", 99))

NAV = [("/themen/", "Themen"), ("/rechner-kapital-passives-einkommen/", "Rechner"), ("/buecher/", "Bücher"), ("/glossar/", "Glossar")]

# --- Glossar ---
GL = json.load(io.open(os.path.join(B, "glossar.json"), encoding="utf-8"))
GL["begriffe"].sort(key=lambda g: g["term"].lower().replace("ä", "a").replace("ö", "o").replace("ü", "u"))

def nav(current):
    items = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{t}</a>' for h, t in NAV)
    return f'<nav class="top" aria-label="Navigation"><div class="wrap"><a class="brand" href="/" aria-label="Playbook Passives Einkommen, Startseite"><svg class=\"logo\" viewBox=\"0 0 64 64\" width=\"30\" height=\"30\" aria-hidden=\"true\"><rect width=\"64\" height=\"64\" rx=\"14\" fill=\"#0E6A4E\"/><path d=\"M16 44h8V32h-8z\" fill=\"#fff\" opacity=\".55\"/><path d=\"M28 44h8V24h-8z\" fill=\"#fff\" opacity=\".8\"/><path d=\"M40 44h8V16h-8z\" fill=\"#fff\"/></svg><span class=\"bt\"><b>Playbook</b><small>Passives Einkommen</small></span></a>{items}<a class="cta" href="/arbeitsheft/">Gratis-Arbeitsheft</a>{mmenu(current)}</div></nav>'

def mmenu(current=""):
    """Burger-Menü für kleine Bildschirme: alle Unterseiten auf einen Blick."""
    def a(href, text, cls=""):
        cur = ' aria-current="page"' if href == current else ""
        c = f' class="{cls}"' if cls else ""
        return f'<a href="{href}"{c}{cur}>{esc(text)}</a>'
    topics = "".join(a(f'/{x["slug"]}/', x["h1"]) for x in PAGES)
    return ('<button class="burger" type="button" aria-expanded="false" aria-controls="mmenu" aria-label="Menü öffnen">'
            '<span></span><span></span><span></span></button>'
            '<div class="mmenu" id="mmenu" hidden>'
            + a("/arbeitsheft/", "Gratis-Arbeitsheft (PDF)", "mcta")
            + '<p class="mh">Übersicht</p>' + a("/", "Playbook (Startseite)") + a("/themen/", "Alle Themen")
            + a("/rechner-kapital-passives-einkommen/", "Rechner: Kapitalbedarf") + a("/buecher/", "Bücher aus den Videos") + a("/glossar/", "Glossar: Begriffe erklärt")
            + '<p class="mh">Themen</p>' + topics
            + '<p class="mh">Rechtliches</p><div class="mlegal">' + a("/impressum.html", "Impressum") + a("/datenschutz.html", "Datenschutz") + '</div>'
            + '</div>')

FOOTER = ('<footer class="read">Zusammenfassung und Einordnung öffentlich zugänglicher YouTube-Videos. Keine Anlage-, Steuer- oder Rechtsberatung. '
          'Zahlen der Creator sind nicht unabhängig geprüft. Alle Angaben ohne Gewähr: Trotz Sorgfalt können Fehler oder veraltete Werte enthalten sein. '
          'Hinweise auf Fehler gern an <a href="mailto:info@playbook-passives-einkommen.de">info@playbook-passives-einkommen.de</a>.'
          '<div class="links"><a href="/">Playbook</a><a href="/themen/">Alle Themen</a><a href="/buecher/">Bücher</a><a href="/glossar/">Glossar</a>'
          '<a href="/arbeitsheft/">Arbeitsheft</a><a href="/impressum.html">Impressum</a><a href="/datenschutz.html">Datenschutz</a></div></footer>')

SHARE = '<div class="share"><p>Hilfreich? Teile die Seite mit jemandem, der gerade über passives Einkommen nachdenkt.</p><button type="button" class="share-btn" aria-expanded="false"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>Teilen</button><div class="share-alt" hidden><a data-k="wa" href="https://wa.me/" rel="noopener" target="_blank">WhatsApp</a><a data-k="fb" href="https://www.facebook.com/" rel="noopener" target="_blank">Facebook</a><a data-k="mail" href="mailto:">E-Mail</a><button type="button" data-copy>Link kopieren</button></div></div>'

DLBOX = ('<aside class="dl"><div class="cover" aria-hidden="true">90<small>TAGE</small></div><div>'
         '<h3>Kostenloses Arbeitsheft: 90-Tage-Startplan</h3>'
         '<p>Alle Schritte aus dem Playbook zum Ausdrucken: Ausgaben-Check, Freiheitszahl, Ideen-Test, Nachfrage-Test und 13-Wochen-Tracker. Ohne Anmeldung, ohne E-Mail.</p>'
         '<a class="btn" href="/arbeitsheft/">Zum Arbeitsheft</a></div></aside>')

def head(title, desc, url, og_img, extra_ld=None, robots=None):
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "description": desc,
           "url": url, "inLanguage": "de-DE", "image": og_img, "dateModified": TODAY,
           "author": {"@type": "Person", "name": "Dave Foksa"}, "publisher": {"@type": "Person", "name": "Dave Foksa"},
           "isPartOf": {"@type": "WebSite", "name": "Playbook Passives Einkommen", "url": DOMAIN + "/"}}]
    if extra_ld:
        ld += extra_ld
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    return f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Playbook Passives Einkommen</title>
<meta name="description" content="{esc(desc)}">
{f'<meta name="robots" content="{robots}">' if robots else ''}
<meta name="author" content="Dave Foksa">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Playbook Passives Einkommen">
<meta property="og:locale" content="de_DE">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og_img}">
<meta name="theme-color" content="#0E6A4E">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="stylesheet" href="/fonts.css">
<link rel="stylesheet" href="/assets/page.css">
<link rel="stylesheet" href="/assets/toc.css">
<link rel="stylesheet" href="/assets/charts.css">
<link rel="stylesheet" href="/assets/glossar.css">
<link rel="stylesheet" href="/assets/share.css">
<script src="/assets/toc.js" defer></script>
<script src="/assets/charts.js" defer></script>
<script src="/assets/glossar-data.js" defer></script>
<script src="/assets/glossar.js" defer></script>
<script src="/assets/share.js" defer></script>
{ld_html}</head>
<body>
'''

def related(slug, n=3):
    others = [p for p in PAGES if p["slug"] != slug]
    me = next((p for p in PAGES if p["slug"] == slug), None)
    pref = me.get("related", []) if me else []
    ordered = [p for s in pref for p in others if p["slug"] == s] + [p for p in others if p["slug"] not in pref]
    return '<div class="more">' + "".join(
        f'<a href="/{p["slug"]}/"><b>{esc(p["h1"])}</b><span>{esc(p["short"])}</span></a>' for p in ordered[:n]) + "</div>"

def render_page(p):
    url = f'{DOMAIN}/{p["slug"]}/'
    og = url + "og.png"
    extra = []
    faq_html = ""
    if p.get("faq"):
        extra.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in p["faq"]]})
        faq_html = "<h2>Häufige Fragen</h2>" + "".join(f'<details class="faq"><summary>{esc(q)}</summary><p>{a}</p></details>' for q, a in p["faq"])
    extra.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Playbook", "item": DOMAIN + "/"},
        {"@type": "ListItem", "position": 2, "name": "Themen", "item": DOMAIN + "/themen/"},
        {"@type": "ListItem", "position": 3, "name": p["h1"], "item": url}]})
    body = yt_links(p["body"])
    if p.get("quellen"):
        body += '<h2>Offizielle Quellen</h2><p class="src">Rechtliche Angaben und Grenzwerte haben wir am 23. November 2026 an diesen Stellen geprüft. Sie ändern sich regelmäßig, und Fehler sind trotz Sorgfalt möglich. Maßgeblich sind immer die Originalquellen; für deine persönliche Situation frag eine Steuerberaterin, einen Steuerberater oder die zuständige Stelle.</p><ul class="src">' + "".join(
            f'<li><a href="{esc(u)}" rel="noopener">{esc(t)}</a></li>' for t, u in p["quellen"]) + "</ul>"
    out = head(p["title"], p["description"], url, og, extra) + nav(f'/{p["slug"]}/') + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / <a href="/themen/">Themen</a> / {esc(p["short_crumb"] if "short_crumb" in p else p["h1"])}</p>
<article>
<h1>{esc(p["h1"])}</h1>
<p class="lede">{p["lede"]}</p>
<p class="meta">Stand: November 2026 · Ausgewertet aus {p.get("n_sources","mehreren")} YouTube-Videos · keine Anlageberatung · <a href="/impressum.html#gewaehr">Angaben ohne Gewähr</a></p>
{body}
{SHARE}
{DLBOX}
{faq_html}
<h2>Weiterlesen</h2>
{related(p["slug"])}
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, p["slug"], "index.html"), out)

# --- Themen-Übersicht ---
def render_hub():
    url = DOMAIN + "/themen/"
    cards = "".join(f'<a href="/{p["slug"]}/"><b>{esc(p["h1"])}</b><span>{esc(p["short"])}</span></a>' for p in PAGES)
    out = head("Alle Themen: passives Einkommen im Realitätscheck",
               "Rechner, Modelle und Selbsttests: zehn Themenseiten zu passivem Einkommen, Nebenjob und Geldanlage, ausgewertet aus 115 YouTube-Videos.",
               url, DOMAIN + "/og.png") + nav("/themen/") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / Themen</p>
<article>
<h1>Alle Themen</h1>
<p class="lede">Jede Seite beantwortet eine konkrete Frage zu passivem Einkommen, mit den Zahlen aus 115 ausgewerteten YouTube-Videos und den Links zu den Quellen.</p>
<div class="more">{cards}<a href="/buecher/"><b>Bücher aus den Videos</b><span>Welche Bücher die Creator empfehlen, nach Thema sortiert.</span></a></div>
{SHARE}
{DLBOX}
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, "themen", "index.html"), out)

# --- Bücher ---
def render_books():
    data = json.load(io.open(os.path.join(B, "books.json"), encoding="utf-8"))
    tag = (CFG.get("amazon_tag") or "").strip()
    url = DOMAIN + "/buecher/"
    sections = ""
    for cat in data["kategorien"]:
        cards = ""
        for bk in cat["buecher"]:
            q = urllib.parse.quote_plus(bk.get("suche", f'{bk["titel"]} {bk["autor"]}'))
            link = f"https://www.amazon.de/s?k={q}&i=stripbooks" + (f"&tag={urllib.parse.quote(tag)}" if tag else "")
            rel = 'rel="sponsored noopener"' if tag else 'rel="noopener"'
            star = " *" if tag else ""
            de = f'<div class="a">{esc(bk["de"])}</div>' if bk.get("de") else ""
            cards += (f'<div class="book"><div class="t">{esc(bk["titel"])}</div><div class="a">{esc(bk["autor"])}</div>{de}'
                      f'<p>{bk["text"]}</p><div class="from">Erwähnt bei: {yt_links(bk["quelle"])}</div>'
                      f'<a class="btn ghost" href="{link}" {rel}>Bei Amazon ansehen{star}</a></div>')
        sections += f'<h2>{esc(cat["name"])}</h2><p>{cat["intro"]}</p><div class="books">{cards}</div>'
    disc = ('<p class="disclosure">* Affiliate-Link: Als Amazon-Partner verdiene ich an qualifizierten Verkäufen. Für dich ändert sich am Preis nichts. '
            'Die Auswahl richtet sich danach, was in den Videos genannt wurde, nicht nach Provision.</p>') if tag else \
           '<p class="disclosure">Die Links führen zur Amazon-Suche. Es sind derzeit keine Affiliate-Links.</p>'
    out = head("Bücher aus den Videos: Was die Creator empfehlen",
               "Welche Bücher in 95 YouTube-Videos über passives Einkommen genannt werden: Geldanlage, Unternehmertum, Angebote und Verkauf, Kreativität – mit Einordnung.",
               url, url + "og.png") + nav("/buecher/") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / Bücher</p>
<article>
<h1>Bücher aus den Videos</h1>
<p class="lede">{data["intro"]}</p>
{disc}
{sections}
{SHARE}
{DLBOX}
<h2>Weiterlesen</h2>
{related("")}
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, "buecher", "index.html"), out)

# --- Arbeitsheft-Landingpage ---
def render_workbook_page():
    url = DOMAIN + "/arbeitsheft/"
    body = rd(os.path.join(B, "arbeitsheft-seite.html"))
    out = head("Kostenloses Arbeitsheft: 90-Tage-Startplan für passives Einkommen",
               "Gratis-PDF zum Ausdrucken: Ausgaben-Check, Freiheitszahl, Ideen-Test, Nachfrage-Test und 13-Wochen-Tracker. Ohne Anmeldung, ohne E-Mail.",
               url, url + "og.png") + nav("/arbeitsheft/") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / Arbeitsheft</p>
<article>
{body}
<h2>Weiterlesen</h2>
{related("")}
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, "arbeitsheft", "index.html"), out)

def glossar_data():
    data = [{"id": g["id"], "t": esc(g["term"]), "k": esc(g["kurz"]), "p": g["p"]} for g in GL["begriffe"]]
    for g in data:
        if re.search(r"\((?!\?)", g["p"]):
            sys.exit(f"Glossar-Muster {g['id']}: nur (?:...) verwenden, keine fangenden Gruppen")
    wr(os.path.join(ROOT, "assets", "glossar-data.js"),
       "/* erzeugt von build/build.py aus build/glossar.json */\nwindow.GLOSSAR=" + json.dumps(data, ensure_ascii=False) + ";\n")

def render_glossary():
    url = DOMAIN + "/glossar/"
    pages = {p["slug"]: p for p in PAGES}
    letters, body, cur = [], "", None
    for g in GL["begriffe"]:
        L = g["term"][0].upper()
        L = "0–9" if L.isdigit() else {"Ä": "A", "Ö": "O", "Ü": "U"}.get(L, L)
        if L != cur:
            cur = L; letters.append(L)
            body += f'<h2 class="gl-letter" id="buchstabe-{L.lower() if L != "0–9" else "0-9"}">{L}</h2>'
        links = ""
        if g.get("seite"):
            sp = pages[g["seite"]]
            links += f'<a href="/{g["seite"]}/">Mehr dazu: {esc(sp.get("short_crumb", sp["h1"]))}</a>'
        if g.get("wiki"):
            links += f'<a href="{esc(g["wiki"])}" rel="noopener">Wikipedia{" (englisch)" if "en.wikipedia" in g["wiki"] else ""} ↗</a>'
        body += (f'<div class="gl-entry" id="{g["id"]}" data-kat="{esc(g["kat"])}"><dfn>{esc(g["term"])}</dfn><span class="kat">{esc(g["kat"])}</span>'
                 f'<p>{esc(g["text"])}</p>' + (f'<div class="gl-links">{links}</div>' if links else '') + '</div>')
    az = "".join(f'<a href="#buchstabe-{x.lower() if x != "0–9" else "0-9"}">{x}</a>' for x in letters)
    cats = '<button type="button" aria-pressed="true" data-k="">Alle</button>' + "".join(
        f'<button type="button" aria-pressed="false" data-k="{esc(k)}">{esc(k)}</button>' for k in GL["kategorien"])
    ld = [{"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "Glossar Passives Einkommen", "url": url,
           "hasDefinedTerm": [{"@type": "DefinedTerm", "name": g["term"], "description": g["text"], "url": url + "#" + g["id"],
                               "inDefinedTermSet": url} for g in GL["begriffe"]]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Playbook", "item": DOMAIN + "/"},
              {"@type": "ListItem", "position": 2, "name": "Glossar", "item": url}]}]
    n = len(GL["begriffe"])
    out = head(f"Glossar: {n} Begriffe zu passivem Einkommen, ETFs und Steuern einfach erklärt",
               "Von 4-Prozent-Regel bis Zinseszins: ETF, Vorabpauschale, Teilfreistellung, Kleinunternehmerregelung, KDP, Dropshipping und mehr, kurz und verständlich erklärt.",
               url, DOMAIN + "/og.png", ld) + nav("/glossar/") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / Glossar</p>
<article>
<h1>Glossar</h1>
<p class="lede">{GL["intro"]}</p>
<p class="src">Die Erklärungen sind bewusst vereinfacht und ohne Gewähr. Gesetze, Grenzwerte und Freibeträge ändern sich, und trotz Sorgfalt können Fehler enthalten sein. Maßgeblich sind die verlinkten Gesetze und Behörden; für deine Situation frag eine Steuerberaterin oder einen Steuerberater. Fehler gefunden? Schreib an <a href="mailto:info@playbook-passives-einkommen.de">info@playbook-passives-einkommen.de</a>.</p>
<div class="gl-tools">
<input class="gl-search" id="glq" type="search" placeholder="Begriff suchen, z. B. Vorabpauschale" aria-label="Glossar durchsuchen">
<div class="gl-cats" role="group" aria-label="Kategorie">{cats}</div>
<nav class="gl-az" aria-label="Alphabet">{az}</nav>
</div>
<div id="gllist">{body}</div>
<p class="gl-empty" id="glnone" hidden>Kein Begriff gefunden.</p>
<script>
(()=>{{const q=document.getElementById("glq"),E=[...document.querySelectorAll(".gl-entry")],H=[...document.querySelectorAll(".gl-letter")],B=[...document.querySelectorAll(".gl-cats button")],az=document.querySelector(".gl-az");let k="";
const norm=s=>s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"");
function f(){{const t=norm(q.value.trim());let any=0;E.forEach(e=>{{const ok=(!k||e.dataset.kat===k)&&(!t||norm(e.textContent).includes(t));e.hidden=!ok;any|=ok}});
H.forEach(h=>{{let n=h.nextElementSibling,v=false;while(n&&!n.classList.contains("gl-letter")){{if(!n.hidden)v=true;n=n.nextElementSibling}}h.hidden=!v}});
document.getElementById("glnone").hidden=!!any;az.hidden=!!(t||k)}}
q.addEventListener("input",f);B.forEach(b=>b.onclick=()=>{{k=b.dataset.k;B.forEach(x=>x.setAttribute("aria-pressed",x===b));f()}});}})();
</script>
{SHARE}
{DLBOX}
<h2>Weiterlesen</h2>
{related("")}
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, "glossar", "index.html"), out)

# --- Vorschaubilder ---
CARD = rd(os.path.join(B, "og-card.html"))
def og_image(path, eyebrow, title, sub):
    t = tempfile.mkdtemp()
    page = CARD.replace("{{EYEBROW}}", esc(eyebrow)).replace("{{TITLE}}", title).replace("{{SUB}}", esc(sub)) \
               .replace("{{FONTS}}", "file:///" + os.path.join(ROOT, "fonts.css").replace("\\", "/"))
    src = os.path.join(t, "card.html"); wr(src, page)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=1200,630", "--virtual-time-budget=3000",
                    f"--screenshot={path}", "file:///" + src.replace("\\", "/")], check=True, capture_output=True)

def pdf(src_html, out_pdf):
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--no-pdf-header-footer",
                    "--virtual-time-budget=4000", f"--print-to-pdf={out_pdf}", "file:///" + src_html.replace("\\", "/")],
                   check=True, capture_output=True)

# --- 404-Seite ---
def render_404():
    cards = "".join(f'<a href="/{p["slug"]}/"><b>{esc(p["h1"])}</b><span>{esc(p["short"])}</span></a>' for p in PAGES[:6])
    out = head("Seite nicht gefunden", "Diese Seite gibt es nicht (mehr). Hier geht es zurück zum Playbook Passives Einkommen.",
               DOMAIN + "/404.html", DOMAIN + "/og.png", robots="noindex") + nav("") + f'''
<main class="read">
<article class="notfound">
<p class="crumbs">Fehler 404</p>
<h1>Diese Seite bringt leider kein Einkommen.</h1>
<p class="lede">Weder aktiv noch passiv: Unter dieser Adresse gibt es nichts. Vielleicht hat sich ein Tippfehler eingeschlichen, oder die Seite ist umgezogen.</p>
<p style="display:flex;flex-wrap:wrap;gap:10px;margin:22px 0 8px"><a class="btn" href="/">Zum Playbook</a><a class="btn ghost" href="/themen/">Alle Themen</a><a class="btn ghost" href="/arbeitsheft/">Gratis-Arbeitsheft</a></p>
<h2>Beliebte Themen</h2>
<div class="more">{cards}</div>
<p class="src">Du hast einen kaputten Link auf dieser Website gefunden? Schreib mir gern an <a href="mailto:info@playbook-passives-einkommen.de">info@playbook-passives-einkommen.de</a>.</p>
</article>
</main>
{FOOTER}
</body>
</html>
'''
    wr(os.path.join(ROOT, "404.html"), out)

# --- Themenliste im Playbook (index.html) aktualisieren ---
def update_index_topics():
    p = os.path.join(ROOT, "index.html")
    h = rd(p)
    cards = "".join(f'<a href="/{x["slug"]}/"><b>{esc(x["h1"])}</b><span>{esc(x["short"])}</span></a>' for x in PAGES)
    cards += '<a href="/buecher/"><b>Bücher aus den Videos</b><span>Was die Creator zu Geld, Business und Verkauf empfehlen.</span></a>'
    h2 = re.sub(r"<!--TOPICS-->.*?<!--/TOPICS-->", lambda m: "<!--TOPICS-->" + cards + "<!--/TOPICS-->", h, flags=re.S)
    h2 = re.sub(r"<!--MMENU-->.*?<!--/MMENU-->", lambda m: "<!--MMENU-->" + mmenu("/") + "<!--/MMENU-->", h2, flags=re.S)
    if h2 == h and "<!--TOPICS-->" not in h:
        sys.exit("TOPICS-Marker fehlt in index.html")
    wr(p, h2)

def sitemap():
    urls = ["/", "/themen/", "/buecher/", "/arbeitsheft/", "/glossar/"] + [f'/{p["slug"]}/' for p in PAGES]
    body = "".join(f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    wr(os.path.join(ROOT, "sitemap.xml"), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n')

if __name__ == "__main__":
    for p in PAGES:
        render_page(p)
    glossar_data(); render_glossary(); render_hub(); render_books(); render_workbook_page(); render_404(); update_index_topics(); sitemap()
    if "--no-images" not in sys.argv:
        for p in PAGES:
            og_image(os.path.join(ROOT, p["slug"], "og.png"), "Playbook · " + p.get("og_eyebrow", "Realitätscheck"), p["og_title"], p["og_sub"])
        og_image(os.path.join(ROOT, "buecher", "og.png"), "Playbook · Leseliste", "Bücher aus <em>95 Videos</em>", "Was Creator zu Geld, Business und Verkauf empfehlen – mit Einordnung.")
        og_image(os.path.join(ROOT, "arbeitsheft", "og.png"), "Kostenloses PDF", "90-Tage-Startplan <em>zum Ausdrucken</em>", "Ausgaben-Check, Freiheitszahl, Ideen-Test, 13-Wochen-Tracker. Ohne Anmeldung.")
        pdf(os.path.join(B, "arbeitsheft-pdf.html"), os.path.join(ROOT, "arbeitsheft", "Arbeitsheft-90-Tage-Startplan.pdf"))
        src = os.path.join(B, "arbeitsheft-pdf.html").replace("\\", "/")
        subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--force-device-scale-factor=1", "--window-size=794,1123", "--virtual-time-budget=3000",
                        "--screenshot=" + os.path.join(ROOT, "arbeitsheft", "cover.png"), "file:///" + src], check=True, capture_output=True)
    print(f"ok: {len(PAGES)} Themenseiten, Hub, Bücher, Arbeitsheft, Sitemap")
