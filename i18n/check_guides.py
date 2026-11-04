#!/usr/bin/env python3
"""Checks the translated guides src/guides/<lang>/*.html against the English originals:

    python3 i18n/check_guides.py de
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "guides"
lang = sys.argv[1]
problems = []


def shape(s):
    """What a translation must keep: placeholders, links, and the count of each structural tag."""
    tags = re.findall(r"<(h1|h2|ol|ul|li|details|summary|table|tr|td|th|a|script|strong)\b", s)
    return (sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", s))), sorted(re.findall(r'href="([^"]*)"', s)),
            {t: tags.count(t) for t in set(tags)})


for original in sorted((SRC / "en").glob("*.html")):
    path = SRC / lang / original.name
    if not path.exists():
        problems.append(f"missing: {path}")
        continue
    s, en = path.read_text(encoding="utf-8"), original.read_text(encoding="utf-8")
    for label, a, b in zip(("placeholders", "links", "tag counts"), shape(s), shape(en)):
        if a != b:
            problems.append(f"{original.name}: {label} differ from English: {a} vs {b}")
    title = re.search(r"<title>(.*?)</title>", s, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)
    if len(title) > 65:
        problems.append(f"{original.name}: title over 65 characters ({len(title)})")
    if not 110 <= len(desc) <= 165:
        problems.append(f"{original.name}: description should be 110–165 characters ({len(desc)})")
    article = json.loads(re.sub(r"\{\{[A-Z_]+\}\}", "x", re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1)))
    if article.get("inLanguage") != lang:
        problems.append(f'{original.name}: JSON-LD inLanguage should be "{lang}"')

print("\n".join(problems) or f"{lang}: guides OK")
sys.exit(1 if problems else 0)
