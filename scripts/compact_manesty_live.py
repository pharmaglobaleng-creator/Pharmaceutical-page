#!/usr/bin/env python3
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "next-app" / "data" / "parts-catalog.json"
PUBLIC_JSON = ROOT / "catalog-data" / "manesty.json"
ORIGINAL_DIR = ROOT / "assets" / "images" / "parts" / "manesty"
OPT_DIR = ROOT / "assets" / "images" / "catalog-thumbs" / "manesty-light-v1"
TEXT_SUFFIXES = {".html", ".json", ".xml", ".txt", ".js", ".jsx", ".mjs", ".css", ".csv", ".md", ".yml", ".yaml"}
OLD_PREFIX = "/assets/images/parts/manesty/"
NEW_PREFIX = "/assets/images/catalog-thumbs/manesty-light-v1/"

def fail(msg):
    raise SystemExit(msg)

if not DATA.exists():
    fail(f"Missing catalog data: {DATA}")
if not ORIGINAL_DIR.exists():
    print("Manesty originals already compacted; nothing to do.")
    raise SystemExit(0)
if not OPT_DIR.exists():
    fail(f"Missing optimized Manesty directory: {OPT_DIR}")

data = json.loads(DATA.read_text())
parts = [p for p in data.get("parts", []) if p.get("brand") == "manesty"]
if len(parts) != 1000:
    fail(f"Expected 1000 Manesty records, found {len(parts)}")

mapping = {}
for p in parts:
    old = p.get("image")
    digest = p.get("imageHash")
    if not old or not old.startswith(OLD_PREFIX):
        fail(f"Unexpected Manesty image path for {p.get('sku')}: {old}")
    if not digest or len(digest) < 24:
        fail(f"Missing imageHash for {p.get('sku')}")
    new = f"{NEW_PREFIX}{digest[:24]}-full.webp"
    new_file = ROOT / new.lstrip("/")
    if not new_file.exists():
        fail(f"Missing optimized full image for {p.get('sku')}: {new}")
    mapping[old] = new
    p["image"] = new

if len(mapping) != 1000:
    fail(f"Expected 1000 distinct Manesty image mappings, found {len(mapping)}")

# Update generated public Manesty JSON from the canonical data.
DATA.write_text(json.dumps(data, indent=2) + "\n")
PUBLIC_JSON.write_text(json.dumps(parts, separators=(",", ":")))

# Rewrite only exact Manesty image URLs throughout textual site files.
pattern = re.compile(r"/assets/images/parts/manesty/[^\s\"'<>),]+")
changed = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    if ".git" in path.parts or "node_modules" in path.parts:
        continue
    if path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    try:
        raw = path.read_text()
    except UnicodeDecodeError:
        continue
    new_raw = pattern.sub(lambda m: mapping.get(m.group(0), m.group(0)), raw)
    if new_raw != raw:
        path.write_text(new_raw)
        changed.append(path)

# Confirm every old URL has been removed from public/textual output.
leftovers = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    if ".git" in path.parts or "node_modules" in path.parts:
        continue
    if path.suffix.lower() not in TEXT_SUFFIXES:
        continue
    try:
        raw = path.read_text()
    except UnicodeDecodeError:
        continue
    if OLD_PREFIX in raw:
        leftovers.append(str(path.relative_to(ROOT)))
if leftovers:
    fail("Old Manesty image references remain: " + ", ".join(leftovers[:25]))

# Ensure every replacement file exists before removing originals.
missing = [new for new in mapping.values() if not (ROOT / new.lstrip("/")).exists()]
if missing:
    fail("Missing replacement files: " + ", ".join(missing[:10]))

subprocess.run(["git", "rm", "-r", "--", str(ORIGINAL_DIR.relative_to(ROOT))], cwd=ROOT, check=True)

# Conservative published-tree budget. The prior Pages artifact was ~1.53 GB.
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
size = 0
for rel in tracked:
    if not rel:
        continue
    p = ROOT / rel.decode()
    if p.exists() and p.is_file():
        size += p.stat().st_size
print(json.dumps({
    "manesty_records": len(parts),
    "rewritten_text_files": len(changed),
    "tracked_worktree_bytes_after_compaction": size,
    "tracked_worktree_mb_after_compaction": round(size / 1_000_000, 1),
}, indent=2))
if size >= 950_000_000:
    fail(f"Compacted worktree is still too large: {size} bytes")

# Basic integrity checks on representative surfaces.
checks = [
    ROOT / "parts" / "manesty" / "index.html",
    ROOT / "catalog-data" / "manesty.json",
    ROOT / "next-app" / "data" / "parts-catalog.json",
]
for p in checks:
    if not p.exists() or p.stat().st_size == 0:
        fail(f"Integrity check failed: {p}")

print("Manesty compaction validation passed.")
