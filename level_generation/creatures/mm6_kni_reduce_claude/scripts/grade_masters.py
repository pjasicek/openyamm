#!/usr/bin/env python3
"""Grade the HD masters onto the restored x2 standing frames' colours (user: "the armor being really dark, and the
coloured areas much more saturated"; the masters were silver steel, ~2x the sprites' chrome luminance).
Chrome (all but trim): luminance quantile-matched to the sprites' chrome, RGB scaled by the luminance ratio (hue and
detail kept). Trim (soft weight from hue 200-320 deg and saturation 0.15-0.3): hue shifted to the sprites' median,
saturation and value quantile-matched to the sprites' trim. Sprite pixels exclude the sword (views 0-2: grey and bright
below the waist). Usage: grade_masters.py [out dir] [source masters dir, default references_hd] -> references_hd/graded/*.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
SP = HERE.parent / 'mm6_kni' / 'aligned_2x'
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'references_hd' / 'graded'
SRC = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / 'references_hd'
OUT.mkdir(parents=True, exist_ok=True)
L = np.array([.2126, .7152, .0722])
MASTERS = ['00_three_quarter.png', '01_front.png', '02_back.png', '03_left.png', '04_right.png']


def load(p):
    a = np.asarray(Image.open(p).convert('RGBA'), np.float64) / 255
    hsv = np.asarray(Image.fromarray((a[..., :3] * 255).round().astype(np.uint8)).convert('HSV'), np.float64) / 255
    return a, hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]


def trim_weight(h, s):
    return ((h > 200) & (h < 320)) * np.clip((s - .15) / .15, 0, 1)


ch_lum, tr = [], []
for i in range(5):
    a, h, s, v = load(SP / f'knistaa{i}.png'); fg = a[..., 3] > .5
    if i < 3:
        rows = np.nonzero(fg.any(1))[0]
        fg &= ~((s < .15) & (v > .55) & (np.arange(a.shape[0])[:, None] > rows.min() + .45 * np.ptp(rows)))
    w = trim_weight(h, s)
    ch_lum.append((a[..., :3] @ L)[fg & (w < .5)]); tr.append(np.stack([h, s, v], -1)[fg & (w >= .5)])
ch_lum = np.sort(np.concatenate(ch_lum)); tr = np.concatenate(tr)
hue_t = np.median(tr[:, 0]); sat_t = np.sort(tr[:, 1]); val_t = np.sort(tr[:, 2])
print('TARGET chrome lum med %.3f p90 %.3f | trim hue %.0f sat med %.2f val med %.2f'
      % (np.median(ch_lum), np.percentile(ch_lum, 90), hue_t, np.median(sat_t), np.median(val_t)))


def qmap(x, target):
    r = np.argsort(np.argsort(x)) / max(len(x) - 1, 1)
    return np.interp(r, np.linspace(0, 1, len(target)), target)


for name in MASTERS:
    a, h, s, v = load(SRC / name); fg = a[..., 3] > .5
    w = trim_weight(h, s) * fg; out = a[..., :3].copy()
    # chrome: luminance by rank onto the sprites' chrome
    lum = a[..., :3] @ L; m = fg & (w < .5)
    new = lum.copy(); new[m] = qmap(lum[m], ch_lum)
    chrome = a[..., :3] * (new / np.maximum(lum, 1e-4))[..., None]
    # trim: hue to the sprites' median, saturation and value by rank onto the sprites' trim
    t = fg & (w > 0); hm = h.copy(); sm = s.copy(); vm = v.copy()
    tm = fg & (w >= .5)
    dh = hue_t - np.median(h[tm]); hm[t] = (h[t] + dh) % 360
    sm[t] = np.interp(s[t], np.sort(s[tm]), qmap(np.sort(s[tm]), sat_t))
    vm[t] = np.interp(v[t], np.sort(v[tm]), qmap(np.sort(v[tm]), val_t))
    hsv = np.stack([hm / 360, sm, vm], -1)
    trim = np.asarray(Image.fromarray((np.clip(hsv, 0, 1) * 255).round().astype(np.uint8), 'HSV').convert('RGB'),
                      np.float64) / 255
    out = chrome * (1 - w[..., None]) + trim * w[..., None]
    res = np.concatenate([np.clip(out, 0, 1), a[..., 3:]], -1)
    Image.fromarray((res * 255).round().astype(np.uint8)).save(OUT / name)
    print('GRADED', name, 'hue shift %.0f' % dh)
