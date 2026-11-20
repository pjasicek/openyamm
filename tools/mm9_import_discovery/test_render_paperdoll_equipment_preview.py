#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render_paperdoll_equipment_preview as preview


class PaperdollEquipmentPreviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.assets = preview.AssetIndex(preview.declared_icon_roots())
        cls.items = preview.read_items(preview.ENGINE_TABLE_ROOT / "items.txt", "engine")
        cls.items.update(preview.read_items(preview.MM9_TABLE_ROOT / "items.txt", "mm9"))
        cls.dolls = preview.representative_dolls(
            preview.read_character_dolls(preview.ENGINE_TABLE_ROOT / "character_data.txt")
        )
        cls.doll_types = preview.read_doll_types(preview.ENGINE_TABLE_ROOT / "doll_types.txt")
        cls.offsets = preview.read_complex_picture_offsets(
            preview.ENGINE_TABLE_ROOT / "complex_item_pictures.txt"
        )
        cls.offsets.update(
            preview.read_complex_picture_offsets(
                preview.REPOSITORY_ROOT / "assets_dev/worlds/mm9/data_tables/complex_item_pictures.txt"
            )
        )

    def test_representatives_cover_equippable_doll_types(self) -> None:
        self.assertTrue(set(range(5)).issubset(self.dolls))

    def test_complete_mode_selects_fitted_dwarf_variant(self) -> None:
        item = self.items[109]
        name, path, suffix = preview.resolve_item_asset(item, 4, False, "complete", self.assets)
        self.assertEqual(name, "item109v5")
        self.assertEqual(suffix, "v5")
        self.assertIsNotNone(path)

    def test_runtime_mode_selects_fitted_minotaur_belt(self) -> None:
        item = self.items[117]
        runtime_name, _runtime_path, _runtime_suffix = preview.resolve_item_asset(
            item, 2, False, "runtime", self.assets
        )
        complete_name, _complete_path, _complete_suffix = preview.resolve_item_asset(
            item, 2, False, "complete", self.assets
        )
        self.assertEqual(runtime_name, "item117v3")
        self.assertEqual(complete_name, "item117v3")

    def test_armor_pose_uses_alternate_asset_without_weapon(self) -> None:
        item = self.items[84]
        name, path, suffix = preview.resolve_item_asset(item, 3, False, "complete", self.assets)
        self.assertEqual(name, "item084v4a")
        self.assertEqual(suffix, "v4a")
        self.assertIsNotNone(path)

    def test_minotaur_cannot_equip_helm_or_boots(self) -> None:
        self.assertFalse(self.doll_types[2].can_equip["Helm"])
        self.assertFalse(self.doll_types[2].can_equip["Boots"])
        self.assertTrue(self.doll_types[2].can_equip["Armor"])
        self.assertTrue(self.doll_types[2].can_equip["Belt"])

    def test_cloak_hangs_behind_body_and_reuses_human_variant(self) -> None:
        item = next(item for item in self.items.values() if item.icon_name.casefold() == "item124")
        self.assertEqual(preview.runtime_suffixes(item, 3, False), ["v1a"])
        self.assertEqual(preview.expected_suffixes(item, 4, True), ["v5a"])
        self.assertLess(preview.ITEM_Z_INDEX["Cloak"], preview.BODY_Z_INDEX)

    def test_portrait_specific_adjustment_table_is_loaded(self) -> None:
        adjustments = preview.read_portrait_picture_adjustments(
            preview.ENGINE_TABLE_ROOT / "complex_item_picture_offsets.txt"
        )
        self.assertEqual(adjustments[(26, 908)], (4, -3))

    def test_mm9_armor_resolves_fitted_art_and_offset(self) -> None:
        item = self.items[10086]
        image, diagnostic = preview.render_preview(
            item,
            self.dolls[0],
            self.doll_types[0],
            self.offsets[item.id][0],
            (0, 0),
            False,
            "complete",
            self.assets,
        )
        self.assertEqual(
            image.size,
            (preview.PAPERDOLL_WIDTH * preview.PHYSICAL_SCALE, preview.PAPERDOLL_HEIGHT * preview.PHYSICAL_SCALE),
        )
        self.assertEqual(diagnostic.selected_asset, "mm9_item_10086v1a")
        self.assertEqual(diagnostic.complex_picture_offset, (47, 78))
        self.assertEqual(diagnostic.issues, ())

    def test_armor_sleeve_renders_above_open_arm(self) -> None:
        item = self.items[10115]
        doll = self.dolls[0]
        doll_type = self.doll_types[0]
        item_point = self.offsets[item.id][0]
        image, diagnostic = preview.render_preview(
            item,
            doll,
            doll_type,
            item_point,
            (0, 0),
            False,
            "complete",
            self.assets,
        )
        self.assertEqual(diagnostic.selected_asset, "mm9_item_10115v1a")

        armor_path = self.assets.find(diagnostic.selected_asset)
        hand_path = self.assets.find(doll.right_hand_open_asset)
        self.assertIsNotNone(armor_path)
        self.assertIsNotNone(hand_path)
        armor = preview.load_layer(armor_path, color_key=True, tier=self.assets.tier(armor_path))
        hand = preview.load_layer(hand_path, color_key=True, tier=self.assets.tier(hand_path))
        hand_origin = preview.physical(doll_type.right_hand_open)
        armor_origin = preview.physical(item_point)
        overlap_pixel = None

        for hand_y in range(hand.height):
            for hand_x in range(hand.width):
                canvas_x = hand_origin[0] + hand_x
                canvas_y = hand_origin[1] + hand_y
                armor_x = canvas_x - armor_origin[0]
                armor_y = canvas_y - armor_origin[1]

                if not (0 <= armor_x < armor.width and 0 <= armor_y < armor.height):
                    continue

                hand_pixel = hand.getpixel((hand_x, hand_y))
                armor_pixel = armor.getpixel((armor_x, armor_y))

                if hand_pixel[3] == 255 and armor_pixel[3] == 255 and hand_pixel != armor_pixel:
                    overlap_pixel = (canvas_x, canvas_y, armor_pixel)
                    break

            if overlap_pixel is not None:
                break

        self.assertIsNotNone(overlap_pixel)
        canvas_x, canvas_y, armor_pixel = overlap_pixel
        self.assertEqual(image.getpixel((canvas_x, canvas_y)), armor_pixel)


if __name__ == "__main__":
    unittest.main()
