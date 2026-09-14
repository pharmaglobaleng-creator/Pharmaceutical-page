"""Preserve catalog identity through the publishing normalization chain."""
import ast
import contextlib
import io
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import enforce_unique_part_titles as titles
import normalize_part_pages_for_search as normalize
import polish_part_page_copy as polish


FETTE_SKUS = [f"PGE-FET-{number:03}" for number in (93, 94, 95, 100, 101, 144)]
EXTRA_METADATA_SKUS = [
    "PGE-KOR-051", "PGE-KOR-081", "PGE-KOR-144", "PGE-KOR-158", "PGE-KOR-245",
    "PGE-MAN-0293", "PGE-STK-0137", "PGE-STK-0138", "PGE-STK-0155", "PGE-STK-0156",
    "PGE-STK-0164", "PGE-STK-0250", "PGE-STK-0329", "PGE-STK-0392", "PGE-STK-0393",
    "PGE-STK-0404", "PGE-STK-0532", "PGE-STK-0614", "PGE-STK-1220", "PGE-STK-1221",
    "PGE-STK-1495", "PGE-STK-1496",
]
METADATA_SKUS = FETTE_SKUS + EXTRA_METADATA_SKUS
SOURCE_SCRIPT = normalize.ROOT / ".github/scripts/add_cremer_no_photo_batch.py"
CREMER = next(
    ast.literal_eval(node.value)
    for node in ast.parse(SOURCE_SCRIPT.read_text()).body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "parts" for target in node.targets)
)
EDITORIAL = [
    "pge-cre-001", "pge-cre-002", "pge-cre-003",
    "cremer-cf1220-dipping-nozzle-funnel-cone",
]


def product(text):
    for match in normalize.JSONLD_RE.finditer(text):
        data = json.loads(match.group(2))
        for item in data.get("@graph", [data]):
            if item.get("@type") == "Product":
                return item
    raise AssertionError("Product schema missing")


class IdentityNormalizationTests(unittest.TestCase):
    def read(self, sku):
        path = normalize.ROOT / "parts" / sku.lower() / "index.html"
        return path, path.read_text()

    def test_all_56_cremer_source_identities_survive(self):
        self.assertEqual(len(CREMER), 56)
        for row in CREMER:
            with self.subTest(sku=row["sku"]):
                path, original = self.read(row["sku"])
                truth = normalize.fallback_truth(path, original)
                self.assertEqual((truth.name, truth.brand, truth.model),
                                 (row["name"], "Cremer", row["model"]))
                updated = normalize.normalize_page(path, original)
                self.assertEqual(normalize.normalize_page(path, updated), updated)
                self.assertEqual(polish.polish_page(updated, row["sku"]), updated)
                schema = product(updated)
                self.assertEqual(schema["name"], f"{row['name']} for Cremer {row['model']}")
                self.assertEqual(schema["brand"], {"@type": "Brand", "name": "PharmaGlobalEng"})
                self.assertEqual(schema["manufacturer"], {"@id": normalize.ORG_ID})
                self.assertEqual(schema["isAccessoryOrSparePartFor"]["name"], f"Cremer {row['model']}")
                self.assertNotIn("identifier", schema)
                self.assertIn(row["name"], polish.get_meta_description(updated))
                self.assertIn(f"Cremer {row['model']}", polish.get_meta_description(updated))
                # Existing navigation spelling and factual data are not renamed.
                self.assertEqual(original.count("Creamer parts"), updated.count("Creamer parts"))
                facts = r'<div class="part-facts".*?</div>\s*</div>'
                self.assertEqual(re.search(facts, original, re.S).group(),
                                 re.search(facts, updated, re.S).group())

    def test_all_28_metadata_identities_and_references_survive_both_passes(self):
        for sku in METADATA_SKUS:
            with self.subTest(sku=sku):
                path, original = self.read(sku)
                updated = normalize.normalize_page(path, original)
                truth = normalize.TRUTH[sku]
                self.assertIn(truth.name, polish.get_meta_description(updated))
                self.assertIn(f"{truth.brand} {truth.model}", polish.get_meta_description(updated))
                self.assertLessEqual(len(polish.get_meta_description(updated)), 175)
                self.assertEqual(product(original)["identifier"], product(updated)["identifier"])
                badge = r'<span class="sku-badge">.*?</span>'
                self.assertEqual(re.findall(badge, original), re.findall(badge, updated))
                self.assertEqual(normalize.normalize_page(path, updated), updated)
                self.assertEqual(polish.polish_page(updated, sku), updated)

    def test_internal_for_and_decimal_punctuation_are_not_delimiters(self):
        heading = "Tilt Nozzle for 750 cc / 950 cc Bottles for Cremer CVC1220"
        description = polish.identity_description(heading, "PGE-CRE-043")
        self.assertTrue(description.startswith(heading + "."))
        heading = "SCREW 12.5 MM for Fette 1200i"
        self.assertIn(heading, polish.identity_description(heading, "PGE-FET-TEST"))
        fallback = '<h1>Tilt Nozzle for 750 cc / 950 cc Bottles for Cremer CVC1220</h1>'
        truth = normalize.fallback_truth(Path("pge-cre-043/index.html"), fallback)
        self.assertEqual(truth.name, "Tilt Nozzle for 750 cc / 950 cc Bottles")
        self.assertEqual(truth.model, "CVC1220")

    def test_all_four_editorial_pages_remain_byte_identical(self):
        for slug in EDITORIAL:
            with self.subTest(page=slug):
                path, original = self.read(slug)
                if slug.startswith("pge-"):
                    self.assertRegex(original, r'data-pge-content=["\']editorial["\']')
                    self.assertEqual(normalize.normalize_page(path, original), original)
                    self.assertEqual(polish.polish_page(original, slug.upper()), original)
                else:
                    # This editorial route is preserved by the pge-* discovery boundary.
                    self.assertNotIn(path, normalize.detail_paths())
                    self.assertNotIn(path, polish.pages())
                    self.assertNotIn(path, titles.pages())

    def test_targeted_publish_chain_is_stable_on_second_run(self):
        skus = [row["sku"] for row in CREMER] + METADATA_SKUS + EDITORIAL[:3]
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for sku in skus:
                _, original = self.read(sku)
                path = Path(directory) / sku.lower() / "index.html"
                path.parent.mkdir()
                path.write_text(original)
                paths.append(path)

            def chain():
                for path in paths:
                    path.write_text(normalize.normalize_page(path, path.read_text()))
                with patch.object(polish, "pages", return_value=paths), \
                        patch.object(titles, "pages", return_value=paths), \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(polish.main(), 0)
                    self.assertEqual(titles.main(), 0)
                    self.assertEqual(polish.main(), 0)
                    self.assertEqual(titles.main(), 0)
                return {path: path.read_text() for path in paths}

            first = chain()
            self.assertEqual(chain(), first)


if __name__ == "__main__":
    unittest.main()
