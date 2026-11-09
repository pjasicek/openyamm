"""Icon textures and the manifest of one item family -> textures/<icon>.png, work/<family>_manifest.json.

Reads the merged item table (assets_dev/engine/data_tables/items.txt), keeps the family's real items (an icon, not
a placeholder) and, per distinct icon, copies its restored x2 icon (assets_dev/engine/icons_x2/) into the top left of
a power-of-two canvas with its colours pushed outward into the transparent pixels (the relief's outline can sample
just outside the painting, and mips never reach the background). The manifest records per icon: the items using it,
its canvas and opaque box in x2 pixels, and its world length: the opaque height in logical pixels x LENGTH_PER_PIXEL
(1.25 x the swords' ground sprites, for readability lying on the ground: longsword about 161 world units, claymore
195, cutlass 116).
Usage: python3 -I make_icon_textures.py <family>     (families: see FAMILIES)"""
import json
import os
import sys

import numpy as np
from scipy import ndimage
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
ITEMS = os.path.join(REPO, 'assets_dev', 'engine', 'data_tables', 'items.txt')
ICONS = os.path.join(REPO, 'assets_dev', 'engine', 'icons_x2')
LENGTH_PER_PIXEL = 0.9
# Families whose icons are drawn at another scale than the others (a wand's icon is as tall as a sword's, a cloak's
# smaller than a shield's).
FAMILY_SCALE = {'wands': 0.6, 'cloaks': 1.4, 'rings': 0.55, 'gems': 0.7, 'amulets': 0.8, 'armour': 1.3}
# family: item table predicate
FAMILIES = {
    'swords': lambda row, idx: row[idx['Skill Group']].strip() == 'Sword',
    'daggers': lambda row, idx: row[idx['Skill Group']].strip() == 'Dagger',
    'spears': lambda row, idx: row[idx['Skill Group']].strip() == 'Spear',
    'axes': lambda row, idx: row[idx['Skill Group']].strip() == 'Axe',
    'maces': lambda row, idx: row[idx['Skill Group']].strip() in ('Mace', 'Club'),
    'staves': lambda row, idx: row[idx['Skill Group']].strip() == 'Staff',
    'bows': lambda row, idx: row[idx['Skill Group']].strip() == 'Bow',
    'blasters': lambda row, idx: row[idx['Skill Group']].strip() == 'Blaster',
    'wands': lambda row, idx: row[idx['Equip Stat']].strip() == 'WeaponW',
    'shields': lambda row, idx: row[idx['Equip Stat']].strip() == 'Shield',
    'armour': lambda row, idx: row[idx['Equip Stat']].strip().lower() == 'armor',
    'cloaks': lambda row, idx: row[idx['Equip Stat']].strip().lower() == 'cloak',
    'belts': lambda row, idx: row[idx['Equip Stat']].strip() == 'Belt',
    'books': lambda row, idx: row[idx['Equip Stat']].strip() == 'Book',
    'scrolls': lambda row, idx: row[idx['Equip Stat']].strip() in ('Sscroll', 'Mscroll'),
    'bottles': lambda row, idx: row[idx['Equip Stat']].strip() == 'Bottle',
    'rings': lambda row, idx: row[idx['Equip Stat']].strip() == 'Ring',
    'amulets': lambda row, idx: row[idx['Equip Stat']].strip() == 'Amulet',
    'helms': lambda row, idx: row[idx['Equip Stat']].strip() == 'Helm',
    'boots': lambda row, idx: row[idx['Equip Stat']].strip() == 'Boots',
    'gauntlets': lambda row, idx: row[idx['Equip Stat']].strip() == 'Gauntlets',
    'gems': lambda row, idx: row[idx['Equip Stat']].strip() == 'Gem',
    'lumps': lambda row, idx: row[idx['Equip Stat']].strip() in ('Ore', 'Reagent', 'Herb', '0'),
    'gold': lambda row, idx: row[idx['Equip Stat']].strip().lower() == 'gold',
    'misc': lambda row, idx: row[idx['Equip Stat']].strip() == 'N / A',
}
# Built as solids whose height comes from the icon's height (build_oblique.py): their length is the icon's width.
WIDTH_LENGTH = {'cloaks', 'belts', 'books', 'bottles', 'rings', 'helms', 'boots', 'gold'}


def items_of(family):
    rows = [line.rstrip('\n').split('\t') for line in open(ITEMS, encoding='utf-8', errors='replace')]
    idx = {name: i for i, name in enumerate(rows[1])}
    found = []
    for row in rows[2:]:
        if len(row) <= idx['Sprite Index'] or not row[0].strip().isdigit():
            continue
        icon = row[idx['Pic File']].strip().lower()
        if not icon or icon == 'null' or row[2].strip() in ('', '0'):
            continue
        if FAMILIES[family](row, idx):
            found.append((int(row[0]), row[2].strip(), icon))
    return found


def dilate(rgba, known, rings=8):
    """Colours pushed outward: averaged ring by ring for the first rings (the outline samples them), then the
    nearest coloured pixel."""
    rgb = rgba[:, :, :3].astype(np.float32)
    known = known.copy()
    for _ in range(rings):
        if known.all():
            break
        total = np.zeros_like(rgb)
        count = np.zeros(known.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            shifted = np.roll(np.roll(known, dy, 0), dx, 1)
            total += np.roll(np.roll(rgb * known[:, :, None], dy, 0), dx, 1) * shifted[:, :, None]
            count += shifted
        grow = ~known & (count > 0)
        rgb[grow] = total[grow] / count[grow][:, None]
        known |= grow
    if not known.all():
        _, (rows, columns) = ndimage.distance_transform_edt(~known, return_indices=True)
        rgb = rgb[rows, columns]
    return rgb


def main():
    family = sys.argv[1]
    os.makedirs(os.path.join(HERE, 'textures'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'work'), exist_ok=True)
    icons = {}
    for item_id, name, icon in items_of(family):
        icons.setdefault(icon, []).append({'id': item_id, 'name': name})
    # An icon belongs to one family: the first manifest that took it (families sharing icons, such as a scroll
    # icon also used by a quest item, keep their first model).
    taken = set()
    for name in os.listdir(os.path.join(HERE, 'work')):
        if name.endswith('_manifest.json') and name != f'{family}_manifest.json':
            taken.update(json.load(open(os.path.join(HERE, 'work', name))))
    icons = {icon: users for icon, users in icons.items() if icon not in taken}
    manifest = {}
    for icon, users in sorted(icons.items()):
        image = np.array(Image.open(os.path.join(ICONS, icon + '.png')).convert('RGBA'))
        height, width = image.shape[:2]
        canvas = np.zeros((1 << (height - 1).bit_length(), 1 << (width - 1).bit_length(), 4), np.uint8)
        canvas[:height, :width] = image
        opaque = canvas[:, :, 3] >= 128
        rgb = dilate(canvas, opaque)
        Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8), 'RGB').save(
            os.path.join(HERE, 'textures', icon + '.png'))
        ys, xs = np.nonzero(image[:, :, 3] >= 128)
        box = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        manifest[icon] = {'items': users, 'icon_size': [width, height], 'canvas': [canvas.shape[1], canvas.shape[0]],
                          'opaque_box': box,
                          'length': round((box[2] - box[0] if family in WIDTH_LENGTH
                                          else max(box[2] - box[0], box[3] - box[1])) / 2 * LENGTH_PER_PIXEL
                                         * FAMILY_SCALE.get(family, 1.0), 1)}
    with open(os.path.join(HERE, 'work', f'{family}_manifest.json'), 'w') as handle:
        json.dump(manifest, handle, indent=1)
    print(family, 'items', sum(len(v['items']) for v in manifest.values()), 'icons', len(manifest))


main()
