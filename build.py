#!/usr/bin/env python3
"""Build dist/birthday-picker.bundle.js: the component with all 141 avatars inlined.

Run after generate-avatars.py:
    python3 build.py
"""
import gzip
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "birthday-picker.js")
AVATARS = os.path.join(ROOT, "avatars")
OUT_DIR = os.path.join(ROOT, "dist")
OUT = os.path.join(OUT_DIR, "birthday-picker.bundle.js")
MAX_AGE = 140


def minify_svg(svg):
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"\s*\n\s*", "", svg)      # drop newlines and indentation
    svg = re.sub(r"\s{2,}", " ", svg)
    svg = re.sub(r">\s+<", "><", svg)
    return svg.strip()


def to_data_uri(svg):
    """Percent-encode only what a data: URI needs; UTF-8 text gzips far better than base64."""
    s = minify_svg(svg).replace('"', "'")
    s = (s.replace("%", "%25").replace("#", "%23").replace("<", "%3C")
          .replace(">", "%3E").replace("{", "%7B").replace("}", "%7D"))
    return "data:image/svg+xml," + s


def main():
    with open(SRC, encoding="utf-8") as fh:
        js = fh.read()
    marker = "/*__INLINE_AVATARS__*/ null"
    if marker not in js:
        raise SystemExit("placeholder not found in birthday-picker.js")

    uris = []
    for age in range(MAX_AGE + 1):
        path = os.path.join(AVATARS, f"age-{age:03d}.svg")
        with open(path, encoding="utf-8") as fh:
            uris.append(to_data_uri(fh.read()))

    bundle = js.replace(marker, json.dumps(uris, ensure_ascii=False, separators=(",", ":")))
    bundle = bundle.replace(
        "/*  <birthday-picker> — a self-contained birthday selector with an age avatar.",
        "/*  <birthday-picker> — single-file bundle (component + 141 inlined avatars). Built by build.py; edit the sources, not this file.",
        1,
    )

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(bundle)

    raw = len(bundle.encode("utf-8"))
    gz = len(gzip.compress(bundle.encode("utf-8"), 9))
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {raw / 1024:.0f} KB raw, {gz / 1024:.0f} KB gzipped")


if __name__ == "__main__":
    main()
