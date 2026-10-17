# Blok website

Landing page, privacy policy and support for Blok: Parental Control, served by GitHub Pages in 15 languages.

Edit the bilingual sources in `src/` (every text in Swedish and English), then build:

```
python3 build.py
```

This writes the Swedish pages at the root (`index.html`, `privacy.html`, `support.html`), English in `en/` and
the other 13 languages in their own folders (`da/`, `de/`, `el/`, `es/`, `fr/`, `hr/`, `it/`, `hu/`, `nl/`,
`no/`, `pl/`, `fi/`, `tr/`), plus `sitemap.xml`, `robots.txt` and `llms.txt` (from `src/llms.txt`).
Commit everything and push; Pages publishes in about a minute.

## Translations

The other languages are translated from the English text: `i18n/<lang>.json` maps each English string to its
translation. The build writes every English string to `i18n/strings.json` and reports per language how many are
untranslated (those show in English). After changing English text in `src/`, add the new strings to each
`i18n/<lang>.json` and check a language with `python3 i18n/check.py de`.

## Settings in build.py

- `DOMAIN`: the custom domain; switches every URL and writes `CNAME`.
- `APP_STORE_ID`: set at launch (or when pre-orders open). The "Coming soon" buttons then become links to each
  language's App Store storefront, and the Smart App Banner and JSON-LD download links are added.
- `CAMPAIGN_PROVIDER_TOKEN`: optional; tags App Store links with `ct=web-<lang>` for App Store Connect Analytics.

The search, App Store and AI visibility plan is in `marketing/SEO-PLAN.md`; proposed App Store metadata per
country is in `marketing/aso/`.
