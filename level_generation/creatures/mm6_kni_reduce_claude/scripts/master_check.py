#!/usr/bin/env python3
"""Colour check of the HD masters against the restored x2 standing frames (and native palette 760): per image, the
chrome (everything that is not violet trim) luminance and the trim saturation, plus a side-by-side sheet at equal
figure height on mid grey. Trim: hue 200-320 deg and saturation >= 0.25. Usage: master_check.py [masters dir]
-> review/retex/master_check.png, printed table."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
MD = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'references_hd'
SP = HERE.parent / 'mm6_kni'
PAIRS = [('knistaa0', '01_front.png'), ('knistaa1', '00_three_quarter.png'), ('knistaa2', '03_left.png'),
         ('knistaa4', '02_back.png')]


def stats(path):
    a = np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255
    fg = a[..., 3] > .5
    hsv = np.asarray(Image.fromarray((a[..., :3] * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
    trim = fg & (h > 200) & (h < 320) & (s >= .25); chrome = fg & ~trim
    lum = a[..., :3] @ np.array([.2126, .7152, .0722])
    return {'chrome_lum_med': np.median(lum[chrome]), 'chrome_lum_p90': np.percentile(lum[chrome], 90),
            'trim_frac': trim.sum() / fg.sum(), 'trim_sat_med': np.median(s[trim]) if trim.any() else 0,
            'trim_val_med': np.median(v[trim]) if trim.any() else 0}, a


def tile(a, H=640):
    ys, xs = np.nonzero(a[..., 3] > .5)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    im = Image.fromarray((a * 255).astype(np.uint8)); w = max(1, round(im.width * H / im.height))
    im = im.resize((w, H), Image.Resampling.LANCZOS)
    bg = Image.new('RGBA', (w + 40, H + 40), (128, 128, 128, 255)); bg.alpha_composite(im, (20, 20))
    return bg


cols, rows = [], []
print(f"{'image':42s} chrome lum med / p90   trim share  trim sat  trim val")
for sprite, master in PAIRS:
    col = []
    for label, path in (('native 760', SP / 'native_variants' / f'{sprite}_760.png'),
                        ('restored x2', SP / 'aligned_2x' / f'{sprite}.png'), ('HD master', MD / master)):
        s, a = stats(path); col.append(tile(a))
        print(f"{label + ' ' + path.name:42s} {s['chrome_lum_med']:.3f} / {s['chrome_lum_p90']:.3f}"
              f"          {s['trim_frac']:.3f}     {s['trim_sat_med']:.2f}      {s['trim_val_med']:.2f}")
    cols.append(col)
W = sum(max(t.width for t in col) for col in cols); sheet = Image.new('RGBA', (W, 3 * 680), (128, 128, 128, 255))
x = 0
for col in cols:
    for r, t in enumerate(col):
        sheet.alpha_composite(t, (x, r * 680))
    x += max(t.width for t in col)
out = HERE / 'review' / 'retex' / 'master_check.png'; sheet.convert('RGB').save(out); print('SHEET', out)
