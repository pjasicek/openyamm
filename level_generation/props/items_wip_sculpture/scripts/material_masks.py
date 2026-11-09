"""Binary material regions for this sculpture batch's painted PBR maps."""
import numpy as np


def gold_colours(rgb):
    red, green, blue = np.moveaxis(rgb, -1, 0)
    saturation = (rgb.max(axis=-1) - rgb.min(axis=-1)) / np.maximum(rgb.max(axis=-1), 1e-6)
    return ((saturation > 0.35) & (red > green * 1.03) & (red < green * 2.3)
            & (green > blue * 1.12))


def metal_mask(design, base, pixels, positions):
    if design.get('material_mask') == 'gold_colours':
        return gold_colours(base).astype(np.float32)
    result = np.full(base.shape[:2], design['metallic'], np.float32)
    if design.get('stone_top_fraction'):
        low, high = positions[:, 2].min(), positions[:, 2].max()
        stone_top = low + (high - low) * design['stone_top_fraction']
        result[pixels[:, 1], pixels[:, 0]] = (positions[:, 2] > stone_top).astype(np.float32)
    return result


if __name__ == '__main__':
    palette = np.array([[210, 155, 60], [45, 65, 180], [220, 207, 175], [190, 25, 20]], dtype=float) / 255
    assert gold_colours(palette).tolist() == [True, False, False, False]
    base = np.ones((2, 2, 3))
    pixels = np.array([[0, 0], [1, 1]])
    positions = np.array([[0, 0, 0], [0, 0, 1]])
    mask = metal_mask({'metallic': 1, 'stone_top_fraction': 0.2}, base, pixels, positions)
    assert mask[0, 0] == 0 and mask[1, 1] == 1
    print('Sculpture material masks passed.')
