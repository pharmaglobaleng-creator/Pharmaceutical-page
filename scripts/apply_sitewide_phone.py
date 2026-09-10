#!/usr/bin/env python3
"""Add a consistent, professional click-to-call CTA to every public HTML page.

The injection is idempotent and intentionally skips verification/build files that
must not be altered. Styling is shared from one CSS file to keep every page lean.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHONE_DISPLAY = "(732) 439-7849"
# Keep the contact page international without reformatting other pages.
PHONE_DISPLAY_OVERRIDES = {"contact.html": "+1 (732) 439-7849"}
PHONE_TEL = "+17324397849"
PHONE_CSS_HREF = "/assets/css/pge-phone.css"

SKIP_PREFIXES = ("_next/", "next-app/")
SKIP_FILES = {"googleb09af90219443617.html"}

START_MARKER = "<!-- PGE-SITEWIDE-PHONE:START -->"
END_MARKER = "<!-- PGE-SITEWIDE-PHONE:END -->"
CSS_MARKER = "data-pge-sitewide-phone-css"

PHONE_BLOCK = f'''{START_MARKER}
<a class="pge-sitewide-phone" href="tel:{PHONE_TEL}" aria-label="Call PharmaGlobalEng at {PHONE_DISPLAY}">
  <span class="pge-sitewide-phone__icon" aria-hidden="true">☎</span>
  <span class="pge-sitewide-phone__text">
    <span class="pge-sitewide-phone__label">Call PharmaGlobalEng</span>
    <span class="pge-sitewide-phone__number">{PHONE_DISPLAY}</span>
  </span>
</a>
{END_MARKER}'''

CSS_LINK = f'<link rel="stylesheet" href="{PHONE_CSS_HREF}" {CSS_MARKER}="true">'


def is_public_html(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if not rel.endswith(".html"):
        return False
    if rel in SKIP_FILES:
        return False
    if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    return True


def ensure_stylesheet(text: str) -> str:
    if CSS_MARKER in text or re.search(
        r'<link[^>]+href=["\']' + re.escape(PHONE_CSS_HREF) + r'["\'][^>]*>',
        text,
        flags=re.I,
    ):
        return text

    if not re.search(r"</head\s*>", text, flags=re.I):
        raise ValueError("Public HTML page has no </head> for the sitewide phone stylesheet")

    return re.sub(
        r"</head\s*>",
        CSS_LINK + "\n</head>",
        text,
        count=1,
        flags=re.I,
    )


def inject_phone(text: str, phone_display: str = PHONE_DISPLAY) -> str:
    text = ensure_stylesheet(text)
    phone_block = PHONE_BLOCK.replace(PHONE_DISPLAY, phone_display)

    marker_pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.S,
    )
    if marker_pattern.search(text):
        return marker_pattern.sub(phone_block, text, count=1)

    if re.search(r"</body\s*>", text, flags=re.I):
        return re.sub(
            r"</body\s*>",
            "\n" + phone_block + "\n</body>",
            text,
            count=1,
            flags=re.I,
        )

    if re.search(r"</html\s*>", text, flags=re.I):
        return re.sub(
            r"</html\s*>",
            "\n" + phone_block + "\n</html>",
            text,
            count=1,
            flags=re.I,
        )

    return text.rstrip() + "\n" + phone_block + "\n"


def main() -> None:
    pages = sorted(p for p in ROOT.rglob("*.html") if is_public_html(p))
    changed = 0

    for path in pages:
        original = path.read_text(encoding="utf-8", errors="strict")
        display = PHONE_DISPLAY_OVERRIDES.get(path.relative_to(ROOT).as_posix(), PHONE_DISPLAY)
        updated = inject_phone(original, display)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    # Verify every intended public page has exactly one current phone CTA and CSS link.
    for path in pages:
        text = path.read_text(encoding="utf-8", errors="strict")
        if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
            raise ValueError(f"Phone CTA marker coverage failed: {path}")
        display = PHONE_DISPLAY_OVERRIDES.get(path.relative_to(ROOT).as_posix(), PHONE_DISPLAY)
        expected_block = PHONE_BLOCK.replace(PHONE_DISPLAY, display)
        if expected_block not in text:
            raise ValueError(f"Phone CTA content failed: {path}")
        if PHONE_CSS_HREF not in text:
            raise ValueError(f"Phone CTA stylesheet coverage failed: {path}")

    print(f"Phone CTA checked on {len(pages)} public HTML pages; {changed} page(s) changed.")


if __name__ == "__main__":
    main()
