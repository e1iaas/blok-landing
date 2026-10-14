#!/usr/bin/env python3
"""Builds the static site from src/ (bilingual pages) into one page per language.

    src/index.html  ->  index.html (sv)  and  en/index.html (en)
    src/privacy.html -> privacy.html     and  en/privacy.html
    src/support.html -> support.html     and  en/support.html

In src/, any element with lang="sv" or lang="en" (other than <html>) belongs to that language only;
<span lang="..."> wrappers are unwrapped in the output, other elements keep their lang attribute.
<img data-alt-en="..."> replaces alt on the English pages. The FAQ <details> become FAQPage JSON-LD.
Also writes sitemap.xml (with hreflang alternates), robots.txt and llms.txt. Standard library only:

    python3 build.py
"""
import datetime
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://e1iaas.github.io/blok-landing/"
LANGS = ["sv", "en"]
PAGES = ["index.html", "privacy.html", "support.html"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
ROOT = Path(__file__).parent


class LanguageFilter(HTMLParser):
    """Re-emits the source HTML, dropping elements in the other language."""

    def __init__(self, lang):
        super().__init__(convert_charrefs=False)
        self.lang, self.out, self.stack, self.skipping = lang, [], [], 0

    def emit(self, text):
        if not self.skipping:
            self.out.append(text)

    def other_language(self, tag, attrs):
        lang = dict(attrs).get("lang")
        return tag != "html" and lang in LANGS and lang != self.lang

    def start_tag_text(self, tag, attrs):
        if tag != "img":
            return self.get_starttag_text()
        a = dict(attrs)
        english_alt = a.pop("data-alt-en", None)
        if self.lang == "en" and english_alt is not None:
            a["alt"] = english_alt
        parts = [k if v is None else f'{k}="{html.escape(v, quote=True)}"' for k, v in a.items()]
        return "<img " + " ".join(parts) + ">"

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if "data-src-only" in dict(attrs):  # noindex on the unbuilt sources only
                return
            if not self.skipping and not self.other_language(tag, attrs):
                self.emit(self.start_tag_text(tag, attrs))
            return
        if self.skipping:
            self.stack.append((tag, "inner"))
        elif self.other_language(tag, attrs):
            self.stack.append((tag, "skip"))
            self.skipping += 1
        elif tag == "span" and dict(attrs).get("lang") == self.lang:
            self.stack.append((tag, "unwrap"))
        else:
            self.stack.append((tag, "keep"))
            self.emit(self.start_tag_text(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            open_tag, mode = self.stack.pop()
            if mode == "skip":
                self.skipping -= 1
            elif mode == "keep":
                self.emit(f"</{open_tag}>")
            if open_tag == tag:
                break

    def handle_data(self, data): self.emit(data)
    def handle_entityref(self, name): self.emit(f"&{name};")
    def handle_charref(self, name): self.emit(f"&#{name};")
    def handle_comment(self, data): self.emit(f"<!--{data}-->")
    def handle_decl(self, decl): self.emit(f"<!{decl}>")


def url(lang, page):
    path = "" if page == "index.html" else page
    return BASE + ("" if lang == "sv" else "en/") + path


def relative(from_lang, to_lang, page):
    target = "./" if page == "index.html" else page
    if from_lang == to_lang:
        return target
    return ("en/" if to_lang == "en" else "../") + (target if page != "index.html" else "")


def strip_tags(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s))).strip()


def faq_jsonld(page_html, lang):
    pairs = re.findall(r"<details[^>]*>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", page_html, re.S)
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


def build_page(page, lang):
    source = (ROOT / "src" / page).read_text(encoding="utf-8")
    source = re.sub(r"<!--\s*Source page\..*?-->\n", "", source, count=1, flags=re.S)
    f = LanguageFilter(lang)
    f.feed(source)
    f.close()
    out = "".join(f.out)
    switch = "".join(
        f'<a href="{relative(lang, l, page)}" hreflang="{l}" lang="{l}"'
        + (' aria-current="page"' if l == lang else "")
        + f' aria-label="{"Svenska" if l == "sv" else "English"}">{l.upper()}</a>'
        for l in LANGS
    )
    values = {
        "{{LANG}}": lang,
        "{{ROOT}}": "" if lang == "sv" else "../",
        "{{BASE}}": BASE,
        "{{CANON}}": url(lang, page),
        "{{ALT_SV}}": url("sv", page),
        "{{ALT_EN}}": url("en", page),
        "{{LANG_SWITCH}}": switch,
    }
    for key, value in values.items():
        out = out.replace(key, value)
    out = out.replace("<!--FAQ_JSONLD-->", faq_jsonld(out, lang))
    out = re.sub(r"\n[ \t]*(?=\n)", "\n", out)          # whitespace-only lines left by removed elements
    out = re.sub(r"\n{3,}", "\n\n", out)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    assert not leftover, f"{page} ({lang}): unreplaced {leftover}"
    target = ROOT / ("" if lang == "sv" else "en") / page
    target.parent.mkdir(exist_ok=True)
    target.write_text(out, encoding="utf-8")
    return target


def sitemap():
    today = datetime.date.today().isoformat()
    rows = []
    for page in PAGES:
        for lang in LANGS:
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{url(l, page)}"/>' for l in LANGS
            ) + f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{url("en", page)}"/>'
            priority = "1.0" if page == "index.html" else "0.5"
            rows.append(f"  <url>\n    <loc>{url(lang, page)}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{priority}</priority>{alts}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


if __name__ == "__main__":
    for page in PAGES:
        for lang in LANGS:
            print("wrote", build_page(page, lang).relative_to(ROOT))
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    ai_bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot", "Google-Extended", "Applebot-Extended"]
    robots = "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ai_bots)
    (ROOT / "robots.txt").write_text(robots + f"Sitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print("wrote sitemap.xml, robots.txt")
