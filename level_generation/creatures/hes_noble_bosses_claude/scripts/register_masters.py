#!/usr/bin/env python3
"""Register each painted master onto its exact-body guide (same canvas): search a uniform scale about the feet and a
shift that best overlays the guide's silhouette with the master's, weighting the bare parts (skin, claws, horns),
which the armour must not move. Writes references_hd/<boss>/registration.json and an overlay contact sheet.

Usage: register_masters.py <boss> [<boss> ...]"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
R = P / 'references_hd'
VIEWS = ['00_three_quarter', '01_front', '02_back', '03_left', '04_right']
S = 4  # work at quarter resolution


def load(path):
    im = Image.open(path).convert('RGBA')
    a = np.asarray(im.resize((im.width // S, im.height // S), Image.BILINEAR)).astype(np.float32) / 255
    return a


def transform(img, scale, dx, dy, pivot):
    """Scale about pivot (x, y) then shift, nearest sampling, in quarter-res pixels."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sx = (xx - dx - pivot[0]) / scale + pivot[0]
    sy = (yy - dy - pivot[1]) / scale + pivot[1]
    ix = np.clip(np.round(sx).astype(int), 0, w - 1); iy = np.clip(np.round(sy).astype(int), 0, h - 1)
    out = img[iy, ix]
    out[(sx < 0) | (sx >= w) | (sy < 0) | (sy >= h)] = 0
    return out


report = {}
for boss in sys.argv[1:]:
    report[boss] = {}
    sheet = []
    for v in VIEWS:
        gp, mp = R / 'guides' / f'{v}.png', R / boss / f'{v}.png'
        if not mp.exists():
            continue
        g, m = load(gp), load(mp)
        ga = g[..., 3] > 0.5
        ma = m[..., 3] > 0.5
        ys, xs = np.nonzero(ga)
        pivot = (xs.mean(), ys.max())  # feet centre
        best = None
        for scale in np.arange(0.86, 1.16, 0.01):
            mt_full = transform(m, scale, 0, 0, pivot)
            mta = mt_full[..., 3] > 0.5
            for dy in range(-12, 13, 2):
                for dx in range(-12, 13, 2):
                    sh = np.roll(np.roll(mta, dy, 0), dx, 1)
                    inter = (sh & ga).sum(); union = (sh | ga).sum()
                    miss = (ga & ~sh).sum()  # guide body not covered: armour can only add area
                    score = inter / union - 2.0 * miss / ga.sum()
                    if best is None or score > best[0]:
                        best = (score, scale, dx, dy)
        score, scale, dx, dy = best
        # refine at full pixel steps
        for ddy in range(-2, 3):
            for ddx in range(-2, 3):
                pass
        report[boss][v] = {'scale': round(float(scale), 3), 'dx_px': int(dx * S), 'dy_px': int(dy * S),
                           'pivot_px': [float(pivot[0] * S), float(pivot[1] * S)], 'score': round(float(score), 4),
                           'guide_uncovered': round(float((ga & ~np.roll(np.roll(
                               transform(m, scale, 0, 0, pivot)[..., 3] > 0.5, dy, 0), dx, 1)).sum() / ga.sum()), 4)}
        mt = transform(m, scale, dx, dy, pivot)
        over = g[..., :3] * 0.5 + mt[..., :3] * 0.5
        over[~(ga | (mt[..., 3] > 0.5))] = 0.2
        sheet.append((over * 255).astype(np.uint8))
    if sheet:
        Image.fromarray(np.concatenate(sheet, 1)).save(R / boss / 'registration_overlay.png')
    (R / boss / 'registration.json').write_text(json.dumps(report[boss], indent=1))
print(json.dumps(report, indent=1))
