"""Keep reviewed product copy while retaining the existing quality checks."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import normalize_part_pages_for_search as normalize
import polish_part_page_copy as polish


class EditorialProductTests(unittest.TestCase):
    def setUp(self):
        self.path = normalize.ROOT / 'parts/pge-cre-001/index.html'
        self.text = self.path.read_text()

    def test_reviewed_content_survives_normalization(self):
        self.assertEqual(normalize.normalize_page(self.path, self.text), self.text)

    def test_editorial_page_still_receives_structural_audit(self):
        errors = normalize.totals([normalize.audit_page(self.path, self.text)])
        self.assertFalse(any(errors.values()), errors)
        broken = self.text.replace('rel="canonical"', 'rel="alternate"')
        self.assertTrue(normalize.audit_page(self.path, broken)['missing_canonical'])
        broken = self.text.replace('index,follow', 'noindex,follow')
        self.assertTrue(normalize.audit_page(self.path, broken)['noindex'])

    def test_copy_polisher_preserves_page_and_still_rejects_bad_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.html'
            path.write_text(self.text)
            with patch.object(polish, 'pages', return_value=[path]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(polish.main(), 0)
                self.assertEqual(path.read_text(), self.text)
                path.write_text(self.text.replace('name="description"', 'name="removed-description"', 1))
                self.assertEqual(polish.main(), 1)

    def test_ordinary_catalog_pages_still_normalize(self):
        ordinary = self.text.replace(' data-pge-content="editorial"', '')
        self.assertNotEqual(normalize.normalize_page(self.path, ordinary), ordinary)


if __name__ == '__main__':
    unittest.main()
