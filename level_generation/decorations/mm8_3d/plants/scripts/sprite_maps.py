#!/usr/bin/env python3
"""Sprite analysis for placement and colour checks: work/<id>/sprite.json with
  H, W            binding height / width in metres (inventory height x DSFT scale / 81.7)
  rows            64 rows from the ground up: [left, right] opaque extent in metres about the opaque box centre
  flower          48 x 48 grid (rows from the ground up) of flower-pixel fractions (hue rule below)
  leaf            the same grid for foliage pixels
  mean, mean_leaf, mean_flower   sRGB 0-255 means (all opaque, foliage, flower pixels)
Flower pixels: warm or purple or pale (r > 0.85 g and r > 110, or b > 0.85 g and b > 90, or min channel > 150);
foliage: the rest. Usage: sprite_maps.py <id>..."""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
INV = {e['name']: e for e in json.load(open(os.path.join(ROOT, 'level_generation/decorations/mm8_3d/inventory.json')))}
UNITS = 81.7


def classify(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return ((r > 0.85 * g) & (r > 110)) | ((b > 0.85 * g) & (b > 90)) | (rgb.min(-1) > 150)


def analyse(sid):
    e = INV[sid]
    im = np.asarray(Image.open(os.path.join(ROOT, 'assets_dev/engine/decorations_x2', e['files'][0])).convert('RGBA'))
    im = im.astype(np.float32)
    a = im[..., 3] > 128
    ys, xs = np.nonzero(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = im[y0:y1, x0:x1]; ca = a[y0:y1, x0:x1]
    h, w = ca.shape
    H = e['height'] / UNITS; Wm = e['width'] / UNITS
    mpp = H / h                                               # metres per pixel
    cx = w / 2
    rows = []
    for k in range(64):
        yb = h - int(round(k * h / 64)); yt = h - int(round((k + 1) * h / 64))
        band = ca[yt:yb]
        cols = np.nonzero(band.any(0))[0]
        rows.append([0.0, 0.0] if len(cols) == 0 else [round(float((cols.min() - cx) * mpp), 4),
                                                       round(float((cols.max() + 1 - cx) * mpp), 4)])
    rgb = crop[..., :3]
    fl = classify(rgb) & ca
    lf = ~classify(rgb) & ca

    def grid(mask):
        g = np.zeros((48, 48))
        for r in range(48):
            yb = h - int(round(r * h / 48)); yt = h - int(round((r + 1) * h / 48))
            for c in range(48):
                xl = int(round(c * w / 48)); xr = int(round((c + 1) * w / 48))
                cell = mask[yt:yb, xl:xr]
                g[r, c] = cell.mean() if cell.size else 0.0
        return g.round(3).tolist()
    out = {'id': sid, 'H': H, 'W': Wm, 'px': [w, h], 'rows': rows, 'flower': grid(fl), 'leaf': grid(lf),
           'mean': rgb[ca].mean(0).round(1).tolist(),
           'mean_leaf': rgb[lf].mean(0).round(1).tolist() if lf.any() else None,
           'mean_flower': rgb[fl].mean(0).round(1).tolist() if fl.any() else None,
           'flower_fraction': round(float(fl.sum() / ca.sum()), 3)}
    d = os.path.join(HERE, 'work', sid); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'sprite.json'), 'w') as fh:
        json.dump(out, fh)
    print('SPRITE', sid, 'H', round(H, 3), 'W', round(Wm, 3), 'mean', out['mean'], 'leaf', out['mean_leaf'],
          'flower', out['mean_flower'], 'flower_fraction', out['flower_fraction'])


if __name__ == '__main__':
    for sid in sys.argv[1:]:
        analyse(sid)
