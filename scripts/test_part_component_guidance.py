"""Regressions for guidance derived from component names, not assembly words."""
import unittest

from build_part_pages import Part, application_guidance, guidance_component


class ComponentGuidanceTests(unittest.TestCase):
    def guidance(self, name):
        return application_guidance(Part(
            sku="PGE-TEST-001", name=name, brand="Korsch", brand_slug="korsch",
            model="PH230", image="", family="Catalog components",
        ))

    def test_stripping_and_clamping_do_not_match_pin(self):
        for name in ("TABLET STRIPPING DEVICE", "COMPLETE TABLET STRIPPING DEVICE W/SINGLE SORTING ASSEMBLY",
                     "DUCTOR FOR MATERIAL STRIPPING DEVICE", "CLAMPING FLANGE"):
            with self.subTest(name=name):
                self.assertIsNone(guidance_component(name))
                function, _, checks = self.guidance(name)
                self.assertIn(name, function)
                self.assertNotIn("Shaft, spindle, and pin", function)
                self.assertEqual(checks[0], "Critical dimensions and component geometry")

    def test_bearings_do_not_inherit_cam_or_compression_function(self):
        for name in ("Main Roller Bearing", "Journal Bearing Upper Pre-Compression",
                     "DEEP GROOVE BALL BEARING - CAM SUSTAINER", "CYLINDRICAL ROLLER BEARING",
                     "THRUST ROLLER BEARING", "TAPERED ROLLER BEARING"):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name)
                self.assertEqual(guidance_component(name), "bearing")
                self.assertIn("Bearing and bushing components support", function)
                self.assertIn("Shaft and housing fit", checks)
                self.assertNotIn("Roller diameter and working-face geometry", checks)
                self.assertNotIn("Working profile and follower contact area", checks)

    def test_accessories_and_unclear_hardware_remain_neutral(self):
        for name in ("FEEDER BASE PLATE BRACKET", "FEEDER COVER", "Feeder Cover Window",
                     "COVER STRIP FOR ROTARY FEEDER - TAIL OVER DIE", "CAM COVER BLUE",
                     "SPRING RECEIVER", "HOLDER FOR BUSH", "FILL CAM LUBE HARDWARE",
                     "Guide Dosing Cam Bolt", "Discharge Chute Sensor Holder", "Hopper Sensor Holder",
                     "Sensor Cover Discharge Area", "Sensor Cover Hopper Area", "Lower Gear Guard", "Belt Guard",
                     "COVER STRIP FOR MATERIAL STRIPPING DEVICE-PEEK(TAIL OVER DIE)"):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name)
                self.assertIsNone(guidance_component(name))
                self.assertIn("is a cataloged component", function)
                self.assertEqual(checks, ("Critical dimensions and component geometry",
                                         "Mounting method and installed orientation",
                                         "Mating components and operating clearance"))

    def test_primary_component_takes_precedence_over_assembly_context(self):
        cases = {
            "SPRING FOR FEEDER PAN INSERT SPRING (ALL SERIES)": "spring",
            "SCRAPER SPRING": "spring",
            "Feeder Paddle Gear": "drive",
            "Fill Cam Rail Pin": "shaft",
            "CENTERING PIN FOR DISCHARGE CHUTE": "shaft",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(guidance_component(name), expected)

    def test_pan_and_plate_with_sealing_are_not_seals(self):
        for name in ("FEEDER PAN WITH SEALING - 30 MM", "FEEDER PLATE 15 MM W/ SEALING"):
            with self.subTest(name=name):
                function, _, checks = self.guidance(name)
                self.assertIsNone(guidance_component(name))
                self.assertIn(name, function)
                self.assertNotIn("Seal cross-section and installed diameter", checks)

    def test_spring_guidance_does_not_assume_a_coil_or_wire_form(self):
        for name in ("SPRING FOR FEEDER PAN INSERT SPRING (ALL SERIES)", "SCRAPER SPRING", "LEAF SPRING"):
            with self.subTest(name=name):
                function, context, checks = self.guidance(name)
                self.assertIn("Spring components apply or return force", function)
                self.assertEqual(checks, ("Spring form and installed dimensions",
                                         "Attachment arrangement and installed orientation",
                                         "Specified load and working travel requirements"))
                self.assertNotRegex(" ".join((context, *checks)).lower(), r"\b(?:coil|wire)\b")

    def test_mating_components_after_for_with_and_abbreviations_do_not_override_identity(self):
        cases = {
            "BEARING FOR CAM FOLLOWER": "bearing",
            "PIN FOR FEEDER COVER": "shaft",
            "BUSHING FOR SPINDLE (CAP FOR ROTOR SHAFT)": "bearing",
            "COMPRESSION ROLLER WITH BEARING": "compression",
            "COMPRESSION ROLLER W/BEARING": "compression",
            "COMPRESSION ROLLER W/O BEARING": "compression",
            "CAM (WITH MOUNTING SCREW)": "cam",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(guidance_component(name), expected)

    def test_known_components_keep_their_existing_guidance(self):
        cases = (
            ("Fill Cam", "Cam and track components establish", "Working profile and follower contact area"),
            ("Compression Roller", "Compression-component geometry supports", "Roller diameter and working-face geometry"),
            ("Ball Bearing", "Bearing and bushing components support", "Shaft and housing fit"),
            ("O-Ring", "Sealing components help", "Seal cross-section and installed diameter"),
            ("Feeder Paddle", "Feed-system components participate", "Product-contact geometry and clearances"),
            ("Scraper", "Take-off and discharge components help", "Working-edge profile and installed angle"),
            ("Drive Gear", "Drive components transfer", "Tooth, groove, or pitch geometry"),
            ("Centering Pin", "Shaft, spindle, and pin components locate", "Critical diameters, shoulders, and lengths"),
            ("Spring", "Spring components apply", "Specified load and working travel requirements"),
            ("Handwheel", "Adjustment components provide", "Adjustment direction and usable travel"),
        )
        for name, function_start, checkpoint in cases:
            with self.subTest(name=name):
                function, _, checks = self.guidance(name)
                self.assertTrue(function.startswith(function_start))
                self.assertIn(checkpoint, checks)

    def test_unknown_or_unspecified_roller_does_not_acquire_a_function(self):
        for name in ("CAMSHAFT", "OUTER SHANK FELT", "Feed Roller", "Roller"):
            with self.subTest(name=name):
                self.assertIsNone(guidance_component(name))


if __name__ == "__main__":
    unittest.main()
