"""The warglaives' energy seams as strokes, for the glow ribbons (warglaive_texture.py glow): in each face painting
(warglaives/<key>/paint/paint_{front,back}.png) the seam texels (bright, saturated orange to orange-white: red > 0.9,
red >= green >= blue, red - blue > 0.3, saturation > 0.3), grouped into connected strokes (8-connected, at least
MIN_PX texels and twice as long as wide); per stroke a centre line along its principal axis, sampled every STEP px
(the mean of its texels across, and their spread as the width). Writes warglaives/<key>/paint/seams.json
{view: {size, strokes: [[[x, y, width], ...], ...]}} in painting pixels. Args: <key> [...]"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_PX, STEP = 400, 14


def strokes(path):
    rgba = np.array(Image.open(path).convert('RGBA')).astype(np.float32) / 255
    r, g, b, a = rgba[..., 0], rgba[..., 1], rgba[..., 2], rgba[..., 3]
    mx, mn = rgba[..., :3].max(-1), rgba[..., :3].min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    mask = (a > .5) & (r > .9) & (r >= g) & (g >= b) & (r - b > .3) & (sat > .3)
    mask = ndimage.binary_opening(mask, iterations=1)
    labels, n = ndimage.label(mask, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(labels == i)
        if len(xs) < MIN_PX:
            continue
        pts = np.c_[xs, ys].astype(np.float64); c = pts.mean(0)
        w, v = np.linalg.eigh(np.cov((pts - c).T)); axis, across = v[:, 1], v[:, 0]
        t, s = (pts - c) @ axis, (pts - c) @ across
        if t.max() - t.min() < 2 * (s.max() - s.min()):
            continue
        line = []
        for t0 in np.arange(t.min() + STEP / 2, t.max(), STEP):
            sel = np.abs(t - t0) < STEP / 2
            if sel.sum() < 3:
                continue
            m = s[sel].mean(); width = max(2.0, (s[sel].max() - s[sel].min()) * 0.8)
            p = c + axis * t0 + across * m
            line.append([round(float(p[0]), 1), round(float(p[1]), 1), round(float(width), 1)])
        if len(line) >= 3:
            out.append(line)
    return {'size': list(rgba.shape[1::-1]), 'strokes': out}


for key in sys.argv[1:]:
    folder = os.path.join(HERE, 'warglaives', key, 'paint')
    data = {v: strokes(os.path.join(folder, f'paint_{v}.png')) for v in ('front', 'back')}
    json.dump(data, open(os.path.join(folder, 'seams.json'), 'w'), indent=1)
    print('SEAMS', key, {v: [len(s) for s in d['strokes']] for v, d in data.items()})
