import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_mm9_destructible_brush_inventory


class GenerateMm9DestructibleBrushInventoryTests(unittest.TestCase):
    def test_parser_retains_positions_identity_and_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "sample.mm9.yml").write_text(
                "source:\n  coordinate_scale: 2.56\n", encoding="utf-8")
            (root / "sample.raw_objects.yml").write_text(
                "source_dat: \"sample.dat\"\n"
                "objects:\n"
                "  - object_index: 7\n"
                "    name: \"DestructableBrush\"\n"
                "    properties:\n"
                "      - name: \"Name\"\n"
                "        value_json: \"\\\"BreakableWall\\\"\"\n"
                "      - name: \"Pos\"\n"
                "        value_json: \"[10.0, 20.0, -30.0]\"\n"
                "      - name: \"HitPoints\"\n"
                "        value_json: \"25.0\"\n"
                "      - name: \"Stone\"\n"
                "        value_json: \"1\"\n"
                "      - name: \"Exploding\"\n"
                "        value_json: \"1\"\n"
                "      - name: \"ExplodeDamage\"\n"
                "        value_json: \"40.0\"\n"
                "      - name: \"DamageRadius\"\n"
                "        value_json: \"80.0\"\n",
                encoding="utf-8",
            )

            brushes = generate_mm9_destructible_brush_inventory.read_destructible_brushes(
                root / "sample.raw_objects.yml", root / "sample.mm9.yml")
            self.assertEqual(len(brushes), 1)
            self.assertEqual(brushes[0].source_name, "BreakableWall")
            self.assertEqual(brushes[0].source_position, (10.0, 20.0, -30.0))
            self.assertEqual(brushes[0].openyamm_position, (26, -77, 51))
            self.assertIn("debris=Stone", generate_mm9_destructible_brush_inventory.source_identity(brushes[0]))
            self.assertIn("explodes damage=40 radius=80",
                          generate_mm9_destructible_brush_inventory.source_behavior(brushes[0]))

    def test_checked_in_inventory_is_complete_and_current(self) -> None:
        root = Path(__file__).resolve().parents[2]
        expected = generate_mm9_destructible_brush_inventory.generate_document(
            root / "assets_editor_dev/worlds/mm9/maps")
        actual = (root / "devdocs/mm9/MM9_DESTRUCTIBLE_BRUSH_INVENTORY.md").read_text(encoding="utf-8")
        self.assertEqual(actual, expected)
        self.assertIn("## Map coverage", actual)
        self.assertIn("OpenYAMM position", actual)


if __name__ == "__main__":
    unittest.main()
