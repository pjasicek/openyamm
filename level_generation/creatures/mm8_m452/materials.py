"""Rat Form has one native palette; preserve its base pixels exactly."""
import numpy as np

PALETTES = [452]


def settings():
    return {'base_palette': 452, 'base_exact_bypass': True, 'operation': 'identity',
            'regions': [], 'protected': 'All native fur, skin, paws, tail, eyes and teeth.',
            'mask_method': 'Zero coverage: no native palette changes exist for this family.',
            'palette_deltas': {'452': []}, 'color_space': 'sRGB RGB8, linear coverage'}


def masks(image, config):
    return np.zeros((image.height, image.width), dtype=np.uint8)


def recolor(image, mask, palette, config):
    assert int(palette) == 452
    assert not np.any(mask)
    return image.copy()
