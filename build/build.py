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

NAV = [("/themen/", "Themen"), ("/rechner-kapital-passives-einkommen/", "Rechner"), ("/buecher/", "Bücher")]

def nav(current):
    items = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == current else ""}>{t}</a>' for h, t in NAV)
    return f'<nav class="top" aria-label="Navigation"><div class="wrap"><a class="brand" href="/" aria-label="Playbook Passives Einkommen, Startseite"><svg class=\"logo\" viewBox=\"0 0 64 64\" width=\"30\" height=\"30\" aria-hidden=\"true\"><rect width=\"64\" height=\"64\" rx=\"14\" fill=\"#0E6A4E\"/><path d=\"M16 44h8V32h-8z\" fill=\"#fff\" opacity=\".55\"/><path d=\"M28 44h8V24h-8z\" fill=\"#fff\" opacity=\".8\"/><path d=\"M40 44h8V16h-8z\" fill=\"#fff\"/></svg><span class=\"bt\"><b>Playbook</b><small>Passives Einkommen</small></span></a>{items}<a class="cta" href="/arbeitsheft/">Gratis-Arbeitsheft</a></div></nav>'

FOOTER = ('<footer class="read">Zusammenfassung und Einordnung öffentlich zugänglicher YouTube-Videos. Keine Anlage-, Steuer- oder Rechtsberatung. '
          'Zahlen der Creator sind nicht unabhängig geprüft.'
          '<div class="links"><a href="/">Playbook</a><a href="/themen/">Alle Themen</a><a href="/buecher/">Bücher</a>'
          '<a href="/arbeitsheft/">Arbeitsheft</a><a href="/impressum.html">Impressum</a><a href="/datenschutz.html">Datenschutz</a></div></footer>')

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
        body += '<h2>Offizielle Quellen</h2><p class="src">Rechtliche Angaben und Grenzwerte haben wir am 23. November 2026 an diesen Stellen geprüft:</p><ul class="src">' + "".join(
            f'<li><a href="{esc(u)}" rel="noopener">{esc(t)}</a></li>' for t, u in p["quellen"]) + "</ul>"
    out = head(p["title"], p["description"], url, og, extra) + nav("") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / <a href="/themen/">Themen</a> / {esc(p["short_crumb"] if "short_crumb" in p else p["h1"])}</p>
<article>
<h1>{esc(p["h1"])}</h1>
<p class="lede">{p["lede"]}</p>
<p class="meta">Stand: November 2026 · Ausgewertet aus {p.get("n_sources","mehreren")} YouTube-Videos · keine Anlageberatung</p>
{body}
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
               "Rechner, Modelle und Selbsttests: zehn Themenseiten zu passivem Einkommen, Nebenjob und Geldanlage, ausgewertet aus 95 YouTube-Videos.",
               url, DOMAIN + "/og.png") + nav("/themen/") + f'''
<main class="read">
<p class="crumbs"><a href="/">Playbook</a> / Themen</p>
<article>
<h1>Alle Themen</h1>
<p class="lede">Jede Seite beantwortet eine konkrete Frage zu passivem Einkommen, mit den Zahlen aus 95 ausgewerteten YouTube-Videos und den Links zu den Quellen.</p>
<div class="more">{cards}<a href="/buecher/"><b>Bücher aus den Videos</b><span>Welche Bücher die Creator empfehlen, nach Thema sortiert.</span></a></div>
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
               url, url + "og.png") + nav("") + f'''
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
    if h2 == h and "<!--TOPICS-->" not in h:
        sys.exit("TOPICS-Marker fehlt in index.html")
    wr(p, h2)

def sitemap():
    urls = ["/", "/themen/", "/buecher/", "/arbeitsheft/"] + [f'/{p["slug"]}/' for p in PAGES]
    body = "".join(f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls)
    wr(os.path.join(ROOT, "sitemap.xml"), f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n')

if __name__ == "__main__":
    for p in PAGES:
        render_page(p)
    render_hub(); render_books(); render_workbook_page(); render_404(); update_index_topics(); sitemap()
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
