"""Focused geometry checks for transparent portrait master extraction."""

import json
import unittest

from PIL import Image, ImageDraw

import extract_transparent_portraits as extraction


class PortraitExtractionTests(unittest.TestCase):
    def test_detects_compressed_grid_from_alpha_gutters(self):
        image = Image.new("RGBA", (1465, 1073))
        draw = ImageDraw.Draw(image)
        for row in range(4):
            for column in range(7):
                left = 40 + 201 * column
                top = 28 + 253 * row
                draw.rectangle((left, top, left + 175, top + 220), fill=(80, 40, 20, 255))
        columns, rows, issues = extraction.sheet_geometry(image)
        self.assertFalse(issues)
        self.assertTrue(all(left + 175 < edge < left + 201 for left, edge in
                            zip((40 + 201 * column for column in range(6)), columns[1:7])))
        self.assertTrue(all(top + 220 < edge < top + 253 for top, edge in
                            zip((28 + 253 * row for row in range(3)), rows[1:4])))

    def test_uniform_fit_preserves_native_partial_pose_offset(self):
        cell = Image.new("RGBA", (200, 260))
        ImageDraw.Draw(cell).rectangle((80, 140, 160, 230), fill=(130, 70, 40, 255))
        frame = {"cell": cell, "master_box": [80, 140, 161, 231], "native_box": [25, 39, 49, 66]}
        output, issues = extraction.fit_frame(frame, .6)
        self.assertFalse(issues)
        self.assertEqual(output.size, (118, 158))
        self.assertEqual(output.mode, "RGBA")
        self.assertEqual(output.getpixel((0, 0))[3], 0)
        self.assertLess(output.getchannel("A").getbbox()[1], 100)
        self.assertGreater(output.getchannel("A").getbbox()[1], 65)

    def test_each_sheet_uses_native_anchored_scale_without_pose_pumping(self):
        def frame(width):
            return {"master_box": [0, 0, width, 230], "native_box": [1, 1, 58, 78],
                    "main_pixels": 10000, "detached_pixels": 0}
        sheets = [{"records": [frame(180) for _ in range(28)]},
                  {"records": [frame(195) for _ in range(28)]}]
        for index, sheet in enumerate(sheets):
            sheet["id"] = "A" if index == 0 else "B"
        scales, candidates = extraction.sheet_scales(sheets)
        self.assertEqual(len(candidates), 56)
        self.assertAlmostEqual(scales["A"], min(114 / 180, 154 / 230), places=5)
        self.assertAlmostEqual(scales["B"], min(114 / 195, 154 / 230), places=5)

    def test_previous_background_candidates_match_native_frames(self):
        manifest = json.loads((extraction.INPUT / "manifest.json").read_text())
        families = {family["id"]: family for family in manifest["families"]}
        previous = extraction.previous_background(families["7pc01"])
        self.assertEqual(len(previous["frames"]), 56)
        self.assertEqual(previous["frames"][0],
                         {"status": "existing_x2_diagnostic", "rect": [8, 24, 118, 158]})
        self.assertEqual(previous["frames"][6]["status"], "provisional_raw_preview")
        self.assertIsNone(extraction.previous_background(families["girlc"])["frames"][26]["rect"])


if __name__ == "__main__":
    unittest.main()
