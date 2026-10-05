#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = ROOT / "parts"
# Conservative editorial target below Moz's 600px warning threshold.
# Rounded-up Nimbus Sans (Arial-compatible) glyph widths at 20px; no runtime
# font/Pillow dependency. Search engines may use other fonts/device widths.
LIMIT = 72
PIXEL_LIMIT = 580
GLYPH_WIDTHS = {'0': 12, '1': 12, '2': 12, '3': 12, '4': 12, '5': 12, '6': 12, '7': 12, '8': 12, '9': 12, 'a': 12, 'b': 12, 'c': 10, 'd': 12, 'e': 12, 'f': 6, 'g': 12, 'h': 12, 'i': 5, 'j': 5, 'k': 10, 'l': 5, 'm': 17, 'n': 12, 'o': 12, 'p': 12, 'q': 12, 'r': 7, 's': 10, 't': 6, 'u': 12, 'v': 10, 'w': 15, 'x': 10, 'y': 10, 'z': 10, 'A': 14, 'B': 14, 'C': 15, 'D': 15, 'E': 14, 'F': 13, 'G': 16, 'H': 15, 'I': 6, 'J': 10, 'K': 14, 'L': 12, 'M': 17, 'N': 15, 'O': 16, 'P': 14, 'Q': 16, 'R': 15, 'S': 14, 'T': 13, 'U': 15, 'V': 14, 'W': 19, 'X': 14, 'Y': 14, 'Z': 13, '!': 6, '"': 8, '#': 12, '$': 12, '%': 18, '&': 14, "'": 4, '(': 7, ')': 7, '*': 8, '+': 12, ',': 6, '-': 7, '.': 6, '/': 6, ':': 6, ';': 6, '<': 12, '=': 12, '>': 12, '?': 12, '@': 21, '[': 6, '\\': 6, ']': 6, '^': 10, '_': 12, '`': 7, '{': 7, '|': 6, '}': 7, '~': 12, ' ': 6}


def pixel_width(value: str) -> int:
    return sum(GLYPH_WIDTHS.get(c, 20) for c in value)


def fits(value: str) -> bool:
    return len(value) <= LIMIT and pixel_width(value) <= PIXEL_LIMIT


def concise_title(title: str, keep_sku: bool = False) -> str:
    if fits(title):
        return title
    chunks = [re.sub(r"\s+Replacement Parts?$", "", chunk.strip(), flags=re.I) for chunk in title.split(" | ")]
    chunks = [re.sub(r"\s+Not listed in source.*$", "", chunk, flags=re.I) for chunk in chunks]
    chunks = [chunk for chunk in chunks if chunk != "PGE"]
    # Prefer the descriptive part name and machine model over a supplier code.
    # Keep supplier codes in titles only when needed to distinguish duplicates;
    # every code remains present in the page, canonical URL and Product schema.
    if not keep_sku:
        chunks = [chunk for chunk in chunks if not re.fullmatch(r"PGE-[A-Z0-9]+-[A-Z0-9]+", chunk)]
    name = chunks[0]
    suffix = " | " + " | ".join(chunks[1:]) if len(chunks) > 1 else ""
    # Keep the existing machine/model intact; shorten the display name only.
    # Full technical wording and identifiers remain in H1 and page copy.
    words = name.split()
    while len(words) > 1 and not fits(" ".join(words).rstrip(" |–—-:,;") + suffix):
        words.pop()
    result = " ".join(words).rstrip(" |–—-:,;") + suffix
    if not fits(result):
        raise ValueError(f"Cannot shorten title without losing identity: {title}")
    return result



def clean(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def get_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return clean(match.group(1)) if match else ""


def part_name(text: str, sku: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    value = clean(match.group(1)) if match else sku
    value = re.split(r"\s+(?:for|—)\s+", value, maxsplit=1, flags=re.I)[0].strip()
    return value or sku


def trim_words(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    cut = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" |–—-:,;")
    return cut or value[:limit].rstrip()


def unique_title(text: str, sku: str) -> str:
    suffix = f" | {sku} | PGE"
    budget = max(18, LIMIT - len(suffix))
    return concise_title(trim_words(part_name(text, sku), budget) + suffix, keep_sku=True)


def set_title_fields(text: str, title: str) -> str:
    escaped = html.escape(title, quote=True)
    text = re.sub(r"<title[^>]*>.*?</title>", f"<title>{html.escape(title)}</title>", text, count=1, flags=re.I | re.S)
    for attr, key in (("property", "og:title"), ("name", "twitter:title")):
        pattern = rf'<meta(?=[^>]*\b{attr}=["\']{re.escape(key)}["\'])[^>]*>'
        replacement = f'<meta {attr}="{key}" content="{escaped}">'
        text = re.sub(pattern, replacement, text, count=1, flags=re.I)
    return text


def pages() -> list[Path]:
    return sorted(p for p in PARTS.glob("pge-*/index.html") if p.is_file())


def main() -> int:
    paths = pages()
    groups: dict[str, list[Path]] = defaultdict(list)
    texts: dict[Path, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        texts[path] = text
        groups[get_title(text).casefold()].append(path)

    duplicate_groups = [group for key, group in groups.items() if key and len(group) > 1]
    changed = 0
    for group in duplicate_groups:
        for path in group:
            sku = path.parent.name.upper()
            updated = set_title_fields(texts[path], unique_title(texts[path], sku))
            if updated != texts[path]:
                path.write_text(updated, encoding="utf-8")
                texts[path] = updated
                changed += 1

    for path in paths:
        current = get_title(texts[path])
        title = concise_title(current)
        if title != current:
            updated = set_title_fields(texts[path], title)
            path.write_text(updated, encoding="utf-8")
            texts[path] = updated
            changed += 1

    shortened_groups: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        shortened_groups[get_title(texts[path]).casefold()].append(path)
    for group in shortened_groups.values():
        if len(group) > 1:
            for path in group:
                title = unique_title(texts[path], path.parent.name.upper())
                updated = set_title_fields(texts[path], title)
                if updated != texts[path]:
                    path.write_text(updated, encoding="utf-8")
                    texts[path] = updated
                    changed += 1

    final_titles: dict[str, Path] = {}
    duplicates = []
    overlong = []
    for path in paths:
        title = get_title(path.read_text(encoding="utf-8"))
        key = title.casefold()
        if key in final_titles:
            duplicates.append((final_titles[key], path, title))
        else:
            final_titles[key] = path
        if not fits(title):
            overlong.append((path, title))

    print(f"Duplicate title groups found: {len(duplicate_groups)}; pages changed: {changed}.")
    if duplicates:
        for left, right, title in duplicates[:20]:
            print(f"DUPLICATE: {left} <> {right}: {title}")
        return 1
    if overlong:
        for path, title in overlong[:20]:
            print(f"OVERLONG: {path}: {len(title)} chars: {title}")
        return 1
    print(f"Verified {len(paths)} unique part-page titles, all <= {LIMIT} characters and <= {PIXEL_LIMIT} estimated pixels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
