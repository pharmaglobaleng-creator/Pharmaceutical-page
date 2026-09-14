"""Regression coverage for component identity and safe, limited page repairs."""
import unittest
from html import unescape

from build_fette_pages import ROOT, application_guidance
from repair_fette_component_guidance import content_blocks, outside_guidance, repair_page


class ComponentIdentityTests(unittest.TestCase):
    def guidance(self, name, category):
        return application_guidance({"part_name": name, "category": category})

    def test_seal_in_turret_category_keeps_seal_identity(self):
        function, _, checks = self.guidance('PUNCH SEALS LOWER “B”', 'Turret Hardware')
        self.assertIn('sealing component', function)
        self.assertNotIn('turret', function)
        self.assertIn('Cross-section and installed diameter', checks)
        self.assertNotIn('Station count and tooling configuration', checks)

    def test_felt_in_cam_category_does_not_claim_to_be_a_cam(self):
        function, _, checks = self.guidance('OUTER SHANK FELT 66.3x26x5', 'Upper Cam Tracks')
        self.assertIn('felt component', function)
        self.assertIn('must be confirmed', function)
        self.assertNotIn('motion profile', function)
        self.assertIn('Shape, dimensions, and thickness', checks)

    def test_recognizable_cam_and_turret_ignore_conflicting_categories(self):
        cam = self.guidance('12MM FILL CAM - IPT 19', 'Turret Hardware')
        turret = self.guidance('24 STATION TURRET ASSEMBLY', 'Lower Cam Tracks')
        self.assertIn('guided motion profile', cam[0])
        self.assertIn('Station count and tooling configuration', turret[2])

    def test_mating_part_is_not_component_identity(self):
        bearing = self.guidance('BEARING FOR PRESSURE ROLL', 'Miscellaneous')
        roll = self.guidance('PRESSURE ROLL W/BEARING', 'Pressure Rolls & Components')
        no_bearing_roll = self.guidance('PRESSURE ROLL W/O BEARING', 'Pressure Rolls & Components')
        self.assertIn('bearing or bushing component', bearing[0])
        for guidance in (roll, no_bearing_roll):
            self.assertIn('is cataloged in', guidance[0])
            self.assertNotIn('This bearing', guidance[0])

    def test_unclear_and_composite_names_use_neutral_guidance(self):
        for name in ('CAMSHAFT', 'BEARING RETAINER PLATE', 'PUNCH GUIDE SEAL', 'PRESSURE LEDGE'):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name, 'Lower Cam Tracks')
                self.assertIn(f'The {name} is cataloged in', function)
                self.assertIn('Critical dimensions and component geometry', checks)

    def test_accessories_do_not_inherit_the_component_function(self):
        examples = (
            ('LUBE CAM COVER IPT 1”', 'Upper Cam Tracks'),
            ('LUBE CAM COVER IPT 19 - DELRIN', 'Upper Cam Tracks'),
            ('PUNCH HEAD FELT HOLDER', 'Upper Cam Tracks'),
            ('FELT HOLDER FOR SHAFT LUBRICATION', 'Upper Cam Tracks'),
            ('FEED FRAME BRACKET', 'Product Control'),
            ('COVER PLATE', 'Product Control'),
        )
        for name, category in examples:
            with self.subTest(name=name):
                function, _, checks = self.guidance(name, category)
                self.assertIn(f'The {name} is cataloged in', function)
                self.assertIn('Critical dimensions and component geometry', checks)
                self.assertNotIn('guided motion profile', function)
                self.assertNotIn('identifies a felt component', function)

    def test_an_accessory_mentioned_after_for_does_not_replace_primary_identity(self):
        function, _, checks = self.guidance('BUSHING FOR SPINDLE (CAP FOR ROTOR SHAFT)', 'Drive Components')
        self.assertIn('bearing or bushing component', function)
        self.assertIn('Shaft and housing fit', checks)

    def test_product_control_wheels_do_not_inherit_drive_geometry(self):
        for name in ('FILLING WHEEL - PLOW', 'REVERSE DOSING WHEEL W/ FLAT RODS',
                     'METERING WHEEL W/FLAT RODS', 'STAINLESS STEEL DISTRIBUTING WHEEL'):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name, 'Product Control')
                self.assertIn(f'The {name} is cataloged in', function)
                self.assertNotIn('drive component', function)
                self.assertNotIn('Tooth, groove, or pitch geometry', checks)

    def test_known_drive_components_keep_drive_guidance(self):
        for name in ('TOOTHED BELT', 'DRIVE GEAR', 'DRIVE WHEEL'):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name, 'Drive Components')
                self.assertIn('drive component', function)
                self.assertIn('Tooth, groove, or pitch geometry', checks)


class ExistingPageRepairTests(unittest.TestCase):
    def test_real_pages_preserve_every_byte_outside_authorized_blocks(self):
        paths = sorted((ROOT / 'parts').glob('pge-fet-*/index.html'))
        self.assertEqual(len(paths), 769)
        for path in paths:
            with self.subTest(path=path.parent.name):
                before = path.read_text(encoding='utf-8')
                after = repair_page(before)
                self.assertEqual(outside_guidance(before), outside_guidance(after))
                self.assertEqual(before.split('</head>', 1)[0], after.split('</head>', 1)[0])
                self.assertEqual(repair_page(after), after)

    def test_known_live_component_examples(self):
        for sku, phrase in (('003', 'cam or track component'), ('005', 'sealing component'), ('007', 'felt component')):
            with self.subTest(sku=sku):
                source = (ROOT / 'parts' / f'pge-fet-{sku}' / 'index.html').read_text(encoding='utf-8')
                self.assertIn(phrase, unescape(content_blocks(repair_page(source))[0]))

    def test_real_accessory_pages_use_neutral_copy(self):
        for sku in ('237', '260', '265', '341', '694', '698'):
            with self.subTest(sku=sku):
                source = (ROOT / 'parts' / f'pge-fet-{sku}' / 'index.html').read_text(encoding='utf-8')
                self.assertIn('is cataloged in', unescape(content_blocks(repair_page(source))[0]))

    def test_unrecognized_editorial_copy_and_missing_blocks_are_not_overwritten(self):
        source = (ROOT / 'parts/pge-fet-005/index.html').read_text(encoding='utf-8')
        function = content_blocks(source)[0]
        with self.assertRaisesRegex(ValueError, 'manual review required'):
            repair_page(source.replace(function, 'Verified custom description from the manufacturer.', 1))
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            repair_page(source.replace('What does this part do?', 'Reviewed component purpose'))


if __name__ == '__main__':
    unittest.main()
