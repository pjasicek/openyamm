"""Keys the magenta background of each Codex candidate (items/<id>/paint_<a|b>.png), trims it and fits it into the
family's x2 canvas (the MM7/MM8 restored icon scale), then halves it for MM9's native x1 icon scope.
Outputs per candidate: items/<id>/icon_<c>_x2.png and icon_<c>_x1.png.
Usage: python3 -I finish.py [<id> ...]"""
import json
import os
import sys
import numpy as np
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
    m = np.minimum(rgb[..., 0], rgb[..., 2])
    spill = np.clip(m - rgb[..., 1], 0, None) * rim
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
    items = json.load(open(os.path.join(HERE, 'designs.json')))
    wanted = set(sys.argv[1:])
    for item in items:
        item_id = str(item['design_id'])
        if wanted and item_id not in wanted:
            continue
        folder = os.path.join(HERE, 'items', item_id)
        for c in 'ab':
            src = os.path.join(folder, f'paint_{c}.png')
            if not os.path.exists(src):
                continue
            keyed = key(src)
            x2 = fit(keyed, item['target_x2'])
            x2.save(os.path.join(folder, f'icon_{c}_x2.png'))
            x1 = fit(keyed, (max(1, x2.width // 2), max(1, x2.height // 2)))
            x1.save(os.path.join(folder, f'icon_{c}_x1.png'))
            print(item_id, c, x2.size, x1.size)


if __name__ == '__main__':
    main()
