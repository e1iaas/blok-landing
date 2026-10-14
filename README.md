# Blok website

Landing page, privacy policy and support for Blok, served by GitHub Pages.

Edit the bilingual sources in `src/` (every text in Swedish and English), then build:

```
python3 build.py
```

This writes the Swedish pages at the root (`index.html`, `privacy.html`, `support.html`), the English
ones in `en/`, plus `sitemap.xml` and `robots.txt`. Commit everything and push; Pages publishes in about a minute.
`llms.txt` (a plain summary for AI search) is edited by hand.
