"""Class maps for xaenergy and xafield (A6, session 14), drawn from the masters' colours.

xafield: a force-field curtain, glowing throughout. xaenergy: the cyan energy strips and green indicator lights glow
(class glowing, glow always); the red-copper conduits are bright metal; everything else (plates, frames, brackets,
vents, rivets) is iron. Writes candidates/<stem>_m.png and candidates/check_<stem>_m.png.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import surface_materials  # noqa: E402

CLASSES = {entry['name']: entry['key'] for entry in surface_materials.load_classes()}
OUT = HERE / 'candidates'
OUT.mkdir(exist_ok=True)


def hsv(rgb):
    image = Image.fromarray(rgb).convert('HSV')
    array = np.asarray(image).astype(np.float32)
    return array[..., 0] * 360.0 / 255.0, array[..., 1] / 255.0, array[..., 2] / 255.0


def clean(mask, size=2):
    mask = ndimage.binary_opening(mask, iterations=1)
    return ndimage.binary_closing(mask, iterations=size)


def drop_specks(mask, smallest):
    labels, count = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, count + 1))
    keep = np.zeros(count + 1, bool)
    keep[1:] = sizes >= smallest
    return keep[labels]


def save(stem, index_map):
    rgb = np.zeros(index_map.shape + (3,), np.uint8)
    for name, key in CLASSES.items():
        rgb[index_map == name] = key
    Image.fromarray(rgb).save(OUT / f'{stem}_m.png')
    master = np.asarray(Image.open(ROOT / f'assets_source/worlds/xeen/textures_x4/{stem}.png').convert('RGB'))
    blend = (0.5 * master + 0.5 * rgb).astype(np.uint8)
    Image.fromarray(np.concatenate([master, rgb, blend], axis=1)).save(OUT / f'check_{stem}_m.png')


def xaenergy():
    master = np.asarray(Image.open(ROOT / 'assets_source/worlds/xeen/textures_x4/xaenergy.png').convert('RGB'))
    hue, sat, val = hsv(master)
    cyan = (hue > 150) & (hue < 205) & (sat > 0.3) & (val > 0.32)
    green = (hue > 85) & (hue < 150) & (sat > 0.4) & (val > 0.35)
    # The strips run down the outer columns, the lights down the next ones in; the teal plates between share the
    # strips' hue, so each colour counts only in its own columns.
    u = np.arange(master.shape[1])[None, :] / master.shape[1]
    cyan &= (u < 0.075) | (u > 0.925)
    green &= ((u > 0.09) & (u < 0.2)) | ((u > 0.8) & (u < 0.91))
    copper = ((hue < 25) | (hue > 340)) & (sat > 0.55) & (val > 0.45)
    glow = drop_specks(clean(cyan, 2), 40) | drop_specks(ndimage.binary_closing(green, iterations=1), 6)
    copper = clean(copper, 2) & ~glow
    names = np.full(master.shape[:2], 'iron', dtype=object)
    names[copper] = 'bright_metal'
    names[glow] = 'glowing'
    print('xaenergy shares: glowing %.3f bright_metal %.3f' % (glow.mean(), copper.mean()))
    save('xaenergy', names)


def xafield():
    master = np.asarray(Image.open(ROOT / 'assets_source/worlds/xeen/textures_x4/xafield.png').convert('RGB'))
    save('xafield', np.full(master.shape[:2], 'glowing', dtype=object))


if __name__ == '__main__':
    xaenergy()
    xafield()
