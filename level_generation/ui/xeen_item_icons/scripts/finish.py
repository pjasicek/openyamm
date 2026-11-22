"""Keys the magenta background of each Codex paint (items/<file>/paint_<c>.png), trims it and fits it into the
target's x2 box (manifest box_x2, the MM6-MM8 restored icon scale). Output: items/<file>/icon_<c>_x2.png.
The keyer is the MM9 icon pass's (level_generation/ui/mm9_item_icons_20261104/scripts/finish.py).
Usage: python3 -I finish.py [<key> ...]"""
import os
import sys

import numpy as np
import yaml
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key(path):
    rgb = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    border = np.concatenate([rgb[:8].reshape(-1, 3), rgb[-8:].reshape(-1, 3),
                             rgb[:, :8].reshape(-1, 3), rgb[:, -8:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - 45.0) / (120.0 - 45.0), 0.0, 1.0)
    # Drop specks: keep connected parts of at least 0.2 % of the object's area.
    labels, count = ndimage.label(alpha > 0.5)
    if count > 1:
        sizes = ndimage.sum(np.ones_like(alpha), labels, range(1, count + 1))
        keep = np.isin(labels, 1 + np.flatnonzero(sizes >= 0.002 * sizes.sum()))
        keep = ndimage.binary_dilation(keep, iterations=3)
        alpha *= keep
    # Despill magenta on the semi-transparent rim and the 3 px inside it.
    rim = ndimage.binary_dilation(alpha < 0.999, iterations=3) & (alpha > 0)
    low = np.minimum(rgb[..., 0], rgb[..., 2])
    spill = np.clip(low - rgb[..., 1], 0, None) * rim
    rgb[..., 0] -= spill
    rgb[..., 2] -= spill
    # Unmix the background from partially covered pixels.
    a = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.where(alpha[..., None] < 0.999, (rgb - bg * (1 - a)) / a, rgb)
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def fit(image, box):
    image = image.crop(image.getbbox())
    scale = min(box[0] / image.width, box[1] / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    premul = image.convert('RGBa').resize(size, Image.LANCZOS).convert('RGBA')
    sharp = premul.filter(ImageFilter.UnsharpMask(radius=0.8, percent=45, threshold=1))
    sharp.putalpha(premul.getchannel('A'))
    return sharp


def main():
    manifest = yaml.safe_load(open(os.path.join(HERE, 'manifest.yml')))
    wanted = set(sys.argv[1:])
    for target in manifest['targets']:
        if wanted and target['key'] not in wanted:
            continue
        folder = os.path.join(HERE, 'items', target['file'])
        for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if not (name.startswith('paint_') and name.endswith('.png')):
                continue
            candidate = name[len('paint_'):-len('.png')]
            icon = fit(key(os.path.join(folder, name)), target['box_x2'])
            icon.save(os.path.join(folder, f'icon_{candidate}_x2.png'))
            print(target['key'], candidate, icon.size)


if __name__ == '__main__':
    main()
