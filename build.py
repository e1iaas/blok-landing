#!/usr/bin/env python3
"""Builds the static site from src/ into one folder per language.

    src/index.html   ->  index.html (sv), en/index.html, da/index.html, de/index.html, ...
    src/privacy.html ->  privacy.html,    en/privacy.html, ...   (served as /privacy, /en/privacy)
    src/support.html ->  support.html,    en/support.html, ...   (served as /support, /en/support)

Swedish and English are written in src/ itself: any element with lang="sv" or lang="en" (other than
<html>) belongs to that language only; <span lang="..."> wrappers are unwrapped in the output, other
elements get the page's language. <img data-alt-en="..."> replaces alt outside Swedish.

Every other language is translated from the English text, gettext style: i18n/<lang>.json maps each
English string (the inner HTML of a lang="en" element, a lang="en" meta content, a data-alt-en, or a
JSON-LD text) to its translation. `python3 build.py` also writes i18n/strings.json, the list of every
English string with where it is used; a missing translation falls back to English and is reported.

Elements with data-when="soon" / "launched" are kept only before / after the App Store launch
(APP_STORE_ID below), data-when="translated" only on the translated (not sv/en) pages.
The FAQ <details> become FAQPage JSON-LD. Also writes sitemap.xml (with hreflang alternates),
llms.txt (from src/llms.txt), robots.txt and CNAME. Standard library only:

    python3 build.py
"""
import datetime
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# The site's domain, served by Vercel (vercel.json redirects www and blokapp.vercel.app here). Also written
# to CNAME, so GitHub Pages redirects the old e1iaas.github.io/blok-landing/ URLs here. None: github.io.
DOMAIN = "blokapp.app"
BASE = f"https://{DOMAIN}/" if DOMAIN else "https://e1iaas.github.io/blok-landing/"
# The numeric App Store id (apps.apple.com/.../id1234567890). Set at launch: the CTAs become App Store
# links to each language's storefront, and the Smart App Banner and JSON-LD downloadUrl are added.
APP_STORE_ID = None
# App Store Connect's campaign provider token (Analytics > Campaigns). Set: the website's buttons carry
# ct=web-<lang>, so App Store Connect shows installs per language page.
CAMPAIGN_PROVIDER_TOKEN = None

# code: (native name, folder, og:locale, App Store storefront)
LANGS = {
    "sv": ("Svenska", "", "sv_SE", "se"),
    "en": ("English", "en/", "en_US", "us"),
    "da": ("Dansk", "da/", "da_DK", "dk"),
    "de": ("Deutsch", "de/", "de_DE", "de"),
    "el": ("Ελληνικά", "el/", "el_GR", "gr"),
    "es": ("Español", "es/", "es_ES", "es"),
    "fr": ("Français", "fr/", "fr_FR", "fr"),
    "hr": ("Hrvatski", "hr/", "hr_HR", "hr"),
    "it": ("Italiano", "it/", "it_IT", "it"),
    "hu": ("Magyar", "hu/", "hu_HU", "hu"),
    "nl": ("Nederlands", "nl/", "nl_NL", "nl"),
    "no": ("Norsk", "no/", "nb_NO", "no"),
    "pl": ("Polski", "pl/", "pl_PL", "pl"),
    "fi": ("Suomi", "fi/", "fi_FI", "fi"),
    "tr": ("Türkçe", "tr/", "tr_TR", "tr"),
}
SOURCE_LANGS = ("sv", "en")
PAGES = ["index.html", "privacy.html", "support.html"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
JSONLD_TEXT = {"alternateName", "description", "applicationSubCategory", "operatingSystem", "featureList"}
ROOT = Path(__file__).parent


def normalize(s):
    return re.sub(r"\s+", " ", s).strip()


class Translator:
    """English -> target language lookups; records every English string it is asked for."""

    def __init__(self, lang):
        self.lang = lang
        path = ROOT / "i18n" / f"{lang}.json"
        self.table = json.loads(path.read_text(encoding="utf-8")) if lang not in SOURCE_LANGS and path.exists() else {}
        self.missing, self.seen = [], {}

    def __call__(self, english, where):
        key = normalize(english)
        if not key:
            return english
        self.seen.setdefault(key, where)
        if self.lang == "en":
            return english
        value = self.table.get(key)
        if not value:
            self.missing.append(key)
            return english
        if tags(value) != tags(key):
            sys.exit(f"i18n/{self.lang}.json: markup differs from the English for {key!r}")
        return value


def tags(s):
    """The tags and link targets of an HTML snippet, which a translation has to keep."""
    return sorted(re.findall(r"</?[a-z]+|href=\"[^\"]*\"", s))


class LanguageFilter(HTMLParser):
    """Re-emits the source HTML for one language, dropping and translating as described above."""

    def __init__(self, lang, translate, page, every_variant=False):
        super().__init__(convert_charrefs=False)
        self.lang, self.t, self.page, self.every_variant = lang, translate, page, every_variant
        self.text_lang = "sv" if lang == "sv" else "en"     # which source text this language starts from
        self.out, self.stack, self.skipping = [[]], [], 0

    def emit(self, text):
        if not self.skipping:
            self.out[-1].append(text)

    def drop(self, tag, attrs):
        a = dict(attrs)
        lang, when = a.get("lang"), a.get("data-when")
        if tag != "html" and lang in SOURCE_LANGS and lang != self.text_lang:
            return True
        if self.every_variant:   # collecting strings: keep the before- and after-launch texts both
            return False
        if when == "launched" and not APP_STORE_ID or when == "soon" and APP_STORE_ID:
            return True
        return when == "translated" and self.lang in SOURCE_LANGS

    def start_tag_text(self, tag, attrs, close=False):
        a = dict(attrs)
        a.pop("data-when", None)
        english_alt = a.pop("data-alt-en", None)
        if a.get("lang") in SOURCE_LANGS:
            if a.get("property") == "og:locale":
                a["content"] = LANGS[self.lang][2]
            elif tag == "meta" and "content" in a and self.lang != "sv":
                a["content"] = self.t(a["content"], f"{self.page} <meta {a.get('name') or a.get('property')}>")
            a["lang"] = self.lang
        if english_alt is not None and self.lang != "sv":
            a["alt"] = self.t(english_alt, f"{self.page} image alt")
        if a == dict(attrs):
            return self.get_starttag_text()
        parts = [k if v is None else f'{k}="{html.escape(v, quote=True)}"' for k, v in a.items()]
        return f"<{tag}" + "".join(" " + p for p in parts) + ("/>" if close else ">")

    def handle_starttag(self, tag, attrs, close=False):
        a = dict(attrs)
        if tag in VOID or close:
            if "data-src-only" in a:  # noindex on the unbuilt sources only
                return
            if not self.skipping and not self.drop(tag, attrs):
                self.emit(self.start_tag_text(tag, attrs, close))
            return
        if self.skipping:
            self.stack.append((tag, "inner"))
        elif self.drop(tag, attrs):
            self.stack.append((tag, "skip"))
            self.skipping += 1
        elif a.get("lang") == self.text_lang and tag != "script":
            # A text in the source language: unwrap a <span>, keep other tags; translate the content.
            self.stack.append((tag, "translate"))
            self.out.append([] if tag == "span" else [self.start_tag_text(tag, attrs)])
        else:
            self.stack.append((tag, "keep"))
            self.emit(self.start_tag_text(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, close=True)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            open_tag, mode = self.stack.pop()
            if mode == "skip":
                self.skipping -= 1
            elif mode == "keep":
                self.emit(f"</{open_tag}>")
            elif mode == "translate":
                parts = self.out.pop()
                opening = parts.pop(0) if open_tag != "span" else ""
                text = "".join(parts)
                if self.lang not in SOURCE_LANGS:
                    text = self.t(text, f"{self.page} <{open_tag}>")
                elif self.lang == "en":
                    self.t(text, f"{self.page} <{open_tag}>")
                self.emit(opening + text + (f"</{open_tag}>" if opening else ""))
            if open_tag == tag:
                break

    def handle_data(self, data): self.emit(data)
    def handle_entityref(self, name): self.emit(f"&{name};")
    def handle_charref(self, name): self.emit(f"&#{name};")
    def handle_comment(self, data): self.emit(f"<!--{data}-->")
    def handle_decl(self, decl): self.emit(f"<!{decl}>")


def path(lang, page):
    """The page's public path. Vercel serves privacy.html as /privacy (cleanUrls in vercel.json)."""
    return LANGS[lang][1] + ("" if page == "index.html" else page.removesuffix(".html"))


def url(lang, page):
    return BASE + path(lang, page)


def relative(from_lang, to_lang, page):
    target = ("../" if LANGS[from_lang][1] else "") + path(to_lang, page)
    return target or "./"


def store_url(lang, campaign=False):
    link = f"https://apps.apple.com/{LANGS[lang][3]}/app/id{APP_STORE_ID}"
    if campaign and CAMPAIGN_PROVIDER_TOKEN:
        link += f"?pt={CAMPAIGN_PROVIDER_TOKEN}&ct=web-{lang}&mt=8"
    return link


def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s))).strip()


def faq_jsonld(page_html, lang):
    pairs = re.findall(r"<details(?! class=\"lang\")[^>]*>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", page_html, re.S)
    if not pairs:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "inLanguage": lang,
        "mainEntity": [
            {"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
            for q, a in pairs
        ],
    }
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"


def finish_jsonld(out, lang, translate, page):
    """Translates the JSON-LD texts and, after launch, adds the App Store link to the app."""

    def walk(node, key=None):
        if isinstance(node, dict):
            return {k: walk(v, k) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v, key) for v in node]
        if isinstance(node, str) and key in JSONLD_TEXT and lang != "sv":
            return translate(node, f"{page} JSON-LD {key}")
        return node

    def fix(match):
        data = walk(json.loads(match.group(2)))
        for node in data.get("@graph", []):
            if node.get("@type") == "MobileApplication":
                node["inLanguage"] = list(SOURCE_LANGS)          # the app's own languages
                if APP_STORE_ID:
                    node["downloadUrl"] = node["installUrl"] = store_url(lang)
                    node["sameAs"] = [store_url(lang)]
        return match.group(1) + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"

    return re.sub(r'(<script type="application/ld\+json"[^>]*>)(.*?)</script>', fix, out, flags=re.S)


def build_page(page, lang, translate):
    source = (ROOT / "src" / page).read_text(encoding="utf-8")
    source = re.sub(r"<!--\s*Source page\..*?-->\n", "", source, count=1, flags=re.S)
    f = LanguageFilter(lang, translate, page)
    f.feed(source)
    f.close()
    out = "".join(f.out[0])
    switch = "".join(
        f'<a href="{relative(lang, l, page)}" hreflang="{l}" lang="{l}"'
        + (' aria-current="page"' if l == lang else "")
        + f">{LANGS[l][0]}</a>"
        for l in LANGS
    )
    hreflang = "\n".join(f'<link rel="alternate" hreflang="{l}" href="{url(l, page)}">' for l in LANGS)
    hreflang += f'\n<link rel="alternate" hreflang="x-default" href="{url("en", page)}">'
    values = {
        "{{LANG}}": lang,
        "{{LANG_CODE}}": lang.upper(),
        "{{ROOT}}": "../" if LANGS[lang][1] else "",
        "{{BASE}}": BASE,
        "{{HOME}}": url(lang, "index.html"),
        "{{CANON}}": url(lang, page),
        "{{HREFLANG}}": hreflang,
        "{{OG_LANG}}": lang if lang in SOURCE_LANGS else "en",
        "{{LANG_SWITCH}}": switch,
        "{{APP_STORE_ID}}": str(APP_STORE_ID or ""),
        "{{STORE_URL}}": html.escape(store_url(lang, campaign=True)) if APP_STORE_ID else "",
    }
    for key, value in values.items():
        out = out.replace(key, value)
    out = re.sub(r'href="([^":#]*?)(privacy|support)\.html', r'href="\1\2', out)   # clean URLs in src links
    out = finish_jsonld(out, lang, translate, page)
    out = out.replace("<!--FAQ_JSONLD-->", faq_jsonld(out, lang))
    out = re.sub(r"\n[ \t]*(?=\n)", "\n", out)          # whitespace-only lines left by removed elements
    out = re.sub(r"\n{3,}", "\n\n", out)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    assert not leftover, f"{page} ({lang}): unreplaced {leftover}"
    target = ROOT / LANGS[lang][1] / page
    target.parent.mkdir(exist_ok=True)
    target.write_text(out, encoding="utf-8")
    return target


def sitemap():
    today = datetime.date.today().isoformat()
    rows = []
    for page in PAGES:
        alts = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l, page)}"/>' for l in LANGS)
        alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url("en", page)}"/>'
        priority = "1.0" if page == "index.html" else "0.5"
        for lang in LANGS:
            rows.append(f"  <url>\n    <loc>{url(lang, page)}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{priority}</priority>{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


if __name__ == "__main__":
    english = Translator("en")
    for page in PAGES:   # every English string, including texts not shown yet (data-when)
        collect = LanguageFilter("en", english, page, every_variant=True)
        collect.feed((ROOT / "src" / page).read_text(encoding="utf-8"))
        collect.close()
    for lang in LANGS:
        t = english if lang == "en" else Translator(lang)
        for page in PAGES:
            build_page(page, lang, t)
        missing = sorted(set(t.missing))
        print(f"{lang}: built" + (f", {len(missing)} strings untranslated (English shown)" if missing else ""))
    (ROOT / "i18n").mkdir(exist_ok=True)
    (ROOT / "i18n" / "strings.json").write_text(
        json.dumps(english.seen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    llms = (ROOT / "src" / "llms.txt").read_text(encoding="utf-8").replace("{{BASE}}", BASE)
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot",
               "Google-Extended", "Applebot-Extended", "Bingbot", "DuckAssistBot", "MistralAI-User"]
    robots = "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ai_bots)
    (ROOT / "robots.txt").write_text(robots + f"Sitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    cname = ROOT / "CNAME"
    if DOMAIN:
        cname.write_text(DOMAIN + "\n", encoding="utf-8")
    elif cname.exists():
        cname.unlink()
    print("wrote i18n/strings.json, sitemap.xml, llms.txt, robots.txt" + (", CNAME" if DOMAIN else ""))
