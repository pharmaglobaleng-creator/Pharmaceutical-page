"""The reference audit must retain the current concise-title policy."""
import unittest
from finish_parts_audit import ROOT, polish
from enforce_unique_part_titles import get_title, set_title_fields


class AuditTitleTests(unittest.TestCase):
    def setUp(self):
        self.sku = 'PGE-STK-002'
        self.page = (ROOT / 'parts/pge-stk-002/index.html').read_text()

    def test_legacy_title_is_shortened_by_current_policy(self):
        legacy = set_title_fields(self.page, 'Dc Motor Controller | Stokes Replacement Part | PGE-STK-002')
        result = polish(legacy, self.sku)
        self.assertEqual(get_title(result), 'Dc Motor Controller | Stokes')
        self.assertIn('property="og:title" content="Dc Motor Controller | Stokes"', result)
        self.assertIn('name="twitter:title" content="Dc Motor Controller | Stokes"', result)
        self.assertEqual(polish(result, self.sku), result)

    def test_published_page_is_unchanged(self):
        self.assertEqual(polish(self.page, self.sku), self.page)


if __name__ == '__main__':
    unittest.main()
