"""Shared paperdoll geometry for the Hesper equipment: the engine's tables, icons and doll renders at the engine's
physical (x2) scale, through the table-driven previewer (tools/mm9_import_discovery/render_paperdoll_equipment_preview).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
import render_paperdoll_equipment_preview as preview  # noqa: E402

PROJECT = ROOT / 'level_generation/ui/hesper_paperdoll'
SCALE = preview.PHYSICAL_SCALE
WIDTH, HEIGHT = preview.PAPERDOLL_WIDTH * SCALE, preview.PAPERDOLL_HEIGHT * SCALE
TABLES = preview.ENGINE_TABLE_ROOT
ASSETS = preview.AssetIndex(preview.declared_icon_roots())
DOLLS = preview.representative_dolls(preview.read_character_dolls(TABLES / 'character_data.txt'))
DOLL_TYPES = preview.read_doll_types(TABLES / 'doll_types.txt')
ENGINE_ITEMS = preview.read_items(TABLES / 'items.txt', 'engine')
ENGINE_POINTS = preview.read_complex_picture_offsets(TABLES / 'complex_item_pictures.txt')
DOLL_NAMES = {0: 'human male', 1: 'human female', 2: 'minotaur', 3: 'troll', 4: 'dwarf'}
NO_ITEM = preview.Item(id=0, icon_name='__no_item__', name='', equip_stat='Armor', source='engine')


def layer(name):
    """An engine icon at physical scale (RGBA), or None."""
    path = ASSETS.find(name)
    return None if path is None else preview.load_layer(path, color_key=True, tier=ASSETS.tier(path))


def doll(doll_type, weapon=False):
    """The unarmoured representative doll of a type, at physical scale."""
    image, _ = preview.render_preview(NO_ITEM, DOLLS[doll_type], DOLL_TYPES[doll_type], None, (0, 0), weapon,
                                      'runtime', ASSETS)
    return image


def place(mask, point):
    """A layer-local boolean mask pasted at a logical table point onto a physical full-doll canvas."""
    canvas = np.zeros((HEIGHT, WIDTH), dtype=bool)
    x, y = point[0] * SCALE, point[1] * SCALE
    left, top = max(0, x), max(0, y)
    right, bottom = min(WIDTH, x + mask.shape[1]), min(HEIGHT, y + mask.shape[0])
    if left < right and top < bottom:
        canvas[top:bottom, left:right] = mask[top - y:bottom - y, left - x:right - x]
    return canvas


def alpha(image):
    return np.asarray(image.convert('RGBA'))[:, :, 3] > 0
