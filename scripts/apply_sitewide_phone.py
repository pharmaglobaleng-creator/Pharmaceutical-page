#!/usr/bin/env python3
"""Add a consistent, professional click-to-call CTA to every public HTML page.

The injection is idempotent and intentionally skips verification/build files that
must not be altered. Future runs replace the marked block instead of duplicating it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHONE_DISPLAY = "(732) 439-7849"
PHONE_TEL = "+17324397849"

SKIP_PREFIXES = ("_next/", "next-app/")
SKIP_FILES = {"googleb09af90219443617.html"}

START_MARKER = "<!-- PGE-SITEWIDE-PHONE:START -->"
END_MARKER = "<!-- PGE-SITEWIDE-PHONE:END -->"

PHONE_BLOCK = f'''{START_MARKER}
<style id="pge-sitewide-phone-style">
  .pge-sitewide-phone {{
    position: fixed;
    right: 22px;
    bottom: 22px;
    z-index: 2147483000;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    border: 1px solid rgba(96, 165, 250, .48);
    border-radius: 999px;
    background: linear-gradient(135deg, rgba(8, 15, 35, .97), rgba(17, 24, 55, .97));
    box-shadow: 0 12px 34px rgba(0, 0, 0, .34), 0 0 0 1px rgba(157, 53, 255, .16) inset;
    color: #fff;
    font-family: Inter, Arial, Helvetica, sans-serif;
    text-decoration: none;
    line-height: 1.15;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
  }}
  .pge-sitewide-phone:hover,
  .pge-sitewide-phone:focus-visible {{
    transform: translateY(-2px);
    border-color: rgba(34, 211, 238, .8);
    box-shadow: 0 16px 40px rgba(0, 0, 0, .42), 0 0 24px rgba(34, 211, 238, .14);
    outline: none;
  }}
  .pge-sitewide-phone__icon {{
    display: inline-grid;
    place-items: center;
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7c3aed, #0284c7);
    font-size: 17px;
    box-shadow: 0 0 18px rgba(34, 211, 238, .18);
  }}
  .pge-sitewide-phone__text {{
    display: grid;
    gap: 2px;
  }}
  .pge-sitewide-phone__label {{
    color: #b9c7df;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .09em;
    text-transform: uppercase;
  }}
  .pge-sitewide-phone__number {{
    color: #fff;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: .01em;
    white-space: nowrap;
  }}
  @media (max-width: 640px) {{
    .pge-sitewide-phone {{
      right: 12px;
      bottom: calc(12px + env(safe-area-inset-bottom, 0px));
      padding: 9px 13px;
      gap: 8px;
    }}
    .pge-sitewide-phone__icon {{
      width: 31px;
      height: 31px;
      flex-basis: 31px;
      font-size: 15px;
    }}
    .pge-sitewide-phone__label {{ font-size: 9px; }}
    .pge-sitewide-phone__number {{ font-size: 14px; }}
  }}
  @media print {{
    .pge-sitewide-phone {{ display: none !important; }}
  }}
</style>
<a class="pge-sitewide-phone" href="tel:{PHONE_TEL}" aria-label="Call PharmaGlobalEng at {PHONE_DISPLAY}">
  <span class="pge-sitewide-phone__icon" aria-hidden="true">☎</span>
  <span class="pge-sitewide-phone__text">
    <span class="pge-sitewide-phone__label">Call PharmaGlobalEng</span>
    <span class="pge-sitewide-phone__number">{PHONE_DISPLAY}</span>
  </span>
</a>
{END_MARKER}'''


def is_public_html(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if not rel.endswith(".html"):
        return False
    if rel in SKIP_FILES:
        return False
    if any(rel.startswith(prefix) for prefix in SKIP_PREFIXES):
        return False
    return True


def inject_phone(text: str) -> str:
    marker_pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        flags=re.S,
    )
    if marker_pattern.search(text):
        return marker_pattern.sub(PHONE_BLOCK, text, count=1)

    if re.search(r"</body\s*>", text, flags=re.I):
        return re.sub(
            r"</body\s*>",
            "\n" + PHONE_BLOCK + "\n</body>",
            text,
            count=1,
            flags=re.I,
        )

    if re.search(r"</html\s*>", text, flags=re.I):
        return re.sub(
            r"</html\s*>",
            "\n" + PHONE_BLOCK + "\n</html>",
            text,
            count=1,
            flags=re.I,
        )

    return text.rstrip() + "\n" + PHONE_BLOCK + "\n"


def main() -> None:
    pages = sorted(p for p in ROOT.rglob("*.html") if is_public_html(p))
    changed = 0

    for path in pages:
        original = path.read_text(encoding="utf-8", errors="strict")
        updated = inject_phone(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed += 1

    # Verify every intended public page has exactly one current phone block.
    for path in pages:
        text = path.read_text(encoding="utf-8", errors="strict")
        if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
            raise ValueError(f"Phone CTA marker coverage failed: {path}")
        if f'href="tel:{PHONE_TEL}"' not in text or PHONE_DISPLAY not in text:
            raise ValueError(f"Phone CTA content failed: {path}")

    print(f"Phone CTA checked on {len(pages)} public HTML pages; {changed} page(s) changed.")


if __name__ == "__main__":
    main()
