#!/usr/bin/env python3
"""Checks a translation file against i18n/strings.json (and its App Store texts, if any):

    python3 i18n/check.py de
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def tags(s):
    return sorted(re.findall(r"</?[a-z]+|href=\"[^\"]*\"", s))


lang = sys.argv[1]
strings = json.loads((ROOT / "strings.json").read_text(encoding="utf-8"))
table = json.loads((ROOT / f"{lang}.json").read_text(encoding="utf-8"))
problems = []
for key, where in strings.items():
    value = table.get(key)
    if not value:
        problems.append(f"missing: {key[:70]!r}")
    elif tags(value) != tags(key):
        problems.append(f"markup differs: {key[:70]!r}")
    elif "<title>" in where and len(value) > 65:
        problems.append(f"title over 65 characters ({len(value)}): {value!r}")
    elif "meta description" in where and len(value) > 165:
        problems.append(f"description over 165 characters ({len(value)}): {value!r}")
problems += [f"not in strings.json (stale): {k[:70]!r}" for k in table if k not in strings]

aso_path = ROOT.parent / "marketing" / "aso" / f"{lang}.json"
if aso_path.exists():
    aso = json.loads(aso_path.read_text(encoding="utf-8"))
    for field, limit in [("name", 30), ("subtitle", 30), ("keywords", 100), ("promotional_text", 170)]:
        if len(aso.get(field, "")) > limit:
            problems.append(f"App Store {field} over {limit} characters ({len(aso[field])})")
    if " ," in aso.get("keywords", "") or ", " in aso.get("keywords", ""):
        problems.append("App Store keywords: no spaces around commas (they waste characters)")

print("\n".join(problems) or f"{lang}: OK, {len(strings)} strings")
sys.exit(1 if problems else 0)
