"""Behavioral checks for spill cleanup without changing accepted fitting."""
import unittest

import numpy as np
from PIL import Image

from repair_spill import inspect_background, repair


class RepairTests(unittest.TestCase):
    def cutout(self):
        pixels = np.zeros((40, 40, 4), dtype=np.uint8)
        pixels[5:35, 5:35] = [90, 100, 110, 255]
        return pixels

    def test_edge_repair_keeps_alpha_geometry_and_interior(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[5:35, 5] = [200, 30, 190, 128]
        image, operation, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items')
        result = np.asarray(image)
        self.assertTrue(changed.any())
        np.testing.assert_array_equal(result[:, :, 3], pixels[:, :, 3])
        np.testing.assert_array_equal(result[10:30, 10:30], pixels[10:30, 10:30])
        np.testing.assert_array_equal(result[~changed], pixels[~changed])
        self.assertEqual(operation['unresolved_pixels'], 0)

    def test_native_purple_gems_and_green_material_are_preserved(self):
        for rgb in ([180, 70, 170], [40, 180, 30], [30, 180, 170]):
            native = self.cutout()
            native[5:35, 5:35, :3] = rgb
            image, _, changed = repair(Image.fromarray(native), Image.fromarray(native), 'inventory_items',
                                       {'magenta', 'green', 'cyan'})
            self.assertFalse(changed.any())
            np.testing.assert_array_equal(image, native)

    def test_master_key_not_original_key_controls_interior_cleanup(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[19:21, 19:21, :3] = [220, 10, 210]
        _, _, no_master = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items')
        _, _, wrong_master = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items', {'cyan'})
        output, _, confirmed = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items', {'magenta'})
        self.assertFalse(no_master.any())
        self.assertFalse(wrong_master.any())
        self.assertEqual(int(confirmed.sum()), 4)
        np.testing.assert_array_equal(np.asarray(output)[:, :, 3], pixels[:, :, 3])

    def test_opaque_panel_repairs_border_without_cutting_holes(self):
        native = np.full((40, 40, 4), [90, 85, 70, 255], dtype=np.uint8)
        pixels = native.copy()
        pixels[:, 0, :3] = [255, 0, 255]
        pixels[19:21, 19:21, :3] = [255, 0, 255]  # Interior art is out of scope.
        output, operation, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'player_portrait_frames')
        self.assertEqual(operation['geometry'], 'opaque_canvas_border')
        self.assertEqual(int(changed.sum()), 40)
        np.testing.assert_array_equal(np.asarray(output)[:, 1:], pixels[:, 1:])
        self.assertTrue((np.asarray(output)[:, :, 3] == 255).all())

    def test_spell_energy_is_not_green_screen(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[5:35, 5:8, :3] = [10, 245, 30]
        output, _, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'spell_icon_pair', {'green'})
        self.assertFalse(changed.any())
        np.testing.assert_array_equal(output, pixels)

    def test_spell_animation_keeps_cyan_glow_and_highlights(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[5:35, 5:8] = [0, 220, 255, 100]
        output, _, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'legacy_ui_art',
                                    protected_effect=True)
        self.assertFalse(changed.any())
        np.testing.assert_array_equal(output, pixels)

    def test_unsupported_region_is_left_for_review(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[5:35, 5:35, :3] = [255, 0, 255]
        output, operation, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items', {'magenta'})
        self.assertFalse(changed.any())
        self.assertGreater(operation['unresolved_pixels'], 0)
        np.testing.assert_array_equal(output, pixels)

    def test_actual_master_keys_are_measured_separately(self):
        for color, rgb in [('magenta', (248, 5, 249)), ('green', (2, 253, 4)), ('cyan', (0, 252, 252))]:
            image = Image.new('RGBA', (40, 40), (*rgb, 255))
            image.paste((100, 100, 100, 255), (8, 8, 32, 32))
            evidence = inspect_background(image)
            self.assertEqual(evidence['mode'], 'keyed_' + color)
            self.assertEqual(evidence['keys'][color]['median_rgb'], list(rgb))

    def test_hidden_rgb_does_not_turn_true_alpha_into_keyed_master(self):
        image = Image.new('RGBA', (40, 40), (255, 0, 255, 0))
        image.paste((100, 100, 100, 255), (8, 8, 32, 32))
        evidence = inspect_background(image)
        self.assertEqual(evidence['mode'], 'true_alpha')
        self.assertEqual(evidence['keys'], {})

    def test_inspected_string_tint_preserves_thin_feature_alpha(self):
        native = self.cutout()
        pixels = native.copy()
        pixels[10:30, 5, :] = [80, 5, 70, 160]
        output, operation, changed = repair(Image.fromarray(pixels), Image.fromarray(native), 'inventory_items',
            regions=[{'method':'native_brown_string_tint','box':[5,10,6,30]}])
        result = np.asarray(output)
        np.testing.assert_array_equal(result[:,:,3],pixels[:,:,3])
        self.assertTrue(changed[10:30,5].all())
        self.assertTrue((result[10:30,5,0] >= result[10:30,5,1]).all())
        self.assertTrue((result[10:30,5,1] >= result[10:30,5,2]).all())
        self.assertEqual(operation['unresolved_pixels'],0)


if __name__ == '__main__':
    unittest.main()
