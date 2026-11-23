# Playbook Passives Einkommen

Statische Website: kritische Auswertung von 95 YouTube-Videos zu passivem Einkommen, mit Modellen, Selbsttests, Rechnern, Warnsignalen und einem 90-Tage-Plan.

- `index.html` – das Playbook (eine Datei, kein Build-Schritt)
- `impressum.html`, `datenschutz.html`, `legal.css` – Rechtliches
- `fonts/`, `fonts.css` – lokal ausgelieferte Schriften (SIL Open Font License 1.1)

Gehostet über GitHub Pages. Keine Cookies, kein Tracking, keine externen Ressourcen.

Keine Anlage-, Steuer- oder Rechtsberatung.

## Unterseiten bauen

Themenseiten, Bücherseite, Arbeitsheft-PDF, Vorschaubilder und `sitemap.xml` entstehen aus `build/`:

```
python build/build.py            # alles inkl. Bilder und PDF (braucht Chrome oder Edge)
python build/build.py --no-images  # nur HTML und Sitemap
```

- Themenseiten: `build/pages/<slug>.html` (JSON-Kopf + HTML-Inhalt, `[[VIDEO-ID|Text]]` wird zum YouTube-Link)
- Bücher: `build/books.json`
- Amazon-Partner-Tag: `build/config.json` → `"amazon_tag"`. Ist er gesetzt, werden die Links gekennzeichnet und der Pflichthinweis erscheint.
