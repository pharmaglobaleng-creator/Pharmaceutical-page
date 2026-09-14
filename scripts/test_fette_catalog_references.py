"""Guard against assigning an OEM reference to the wrong part or unreviewed row."""
import copy
import json
import unittest

from sync_fette_catalog_references import ROOT, confirmed_references


class FetteReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads((ROOT / 'data/fette-first-200.json').read_text())
        cls.catalog = json.loads((ROOT / 'catalog-data/fette.json').read_text())

    def detail(self, sku):
        return (ROOT / 'parts' / sku.lower() / 'index.html').read_text()

    def test_only_108_source_supplied_matching_references_are_selected(self):
        refs = confirmed_references(self.source, self.catalog, self.detail)
        self.assertEqual(len(refs), 108)
        self.assertEqual(refs['PGE-FET-005'], '3115546')
        self.assertEqual(refs['PGE-FET-007'], '3126487')
        self.assertNotIn('PGE-FET-003', refs)
        self.assertTrue(all(int(sku[-3:]) <= 200 for sku in refs))

    def test_catalog_name_or_model_mismatch_is_rejected(self):
        for field in ['name', 'model']:
            rows = copy.deepcopy(self.catalog)
            next(row for row in rows if row['sku'] == 'PGE-FET-005')[field] = 'Different part identity'
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'identity mismatch: PGE-FET-005'):
                confirmed_references(self.source, rows, self.detail)

    def test_conflicting_detail_reference_is_rejected(self):
        def detail(sku):
            html = self.detail(sku)
            return html.replace('Replacement Part for OEM 3115546', 'Replacement Part for OEM 0000000') if sku == 'PGE-FET-005' else html
        with self.assertRaisesRegex(ValueError, 'detail reference mismatch: PGE-FET-005'):
            confirmed_references(self.source, self.catalog, detail)

    def test_correct_badge_on_a_different_detail_identity_is_rejected(self):
        def detail(sku):
            html = self.detail(sku)
            return html.replace('<h1>PUNCH SEALS LOWER', '<h1>UNRELATED LOWER') if sku == 'PGE-FET-005' else html
        with self.assertRaisesRegex(ValueError, 'detail identity mismatch: PGE-FET-005'):
            confirmed_references(self.source, self.catalog, detail)

    def test_conflicting_catalog_reference_is_not_silently_replaced(self):
        rows = copy.deepcopy(self.catalog)
        next(row for row in rows if row['sku'] == 'PGE-FET-005')['oem'] = 'DIFFERENT'
        with self.assertRaisesRegex(ValueError, 'Conflicting catalog reference: PGE-FET-005'):
            confirmed_references(self.source, rows, self.detail)

    def test_scope_does_not_expand_to_later_published_identifiers(self):
        before = copy.deepcopy(self.catalog)
        refs = confirmed_references(self.source, self.catalog, self.detail)
        self.assertNotIn('PGE-FET-201', refs)
        self.assertEqual(self.catalog, before)


if __name__ == '__main__':
    unittest.main()
