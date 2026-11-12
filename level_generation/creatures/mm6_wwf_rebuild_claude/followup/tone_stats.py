#!/usr/bin/env python3
"""Fur tone statistics (follow-up 2026-11-11): native MM6 werewolf sprite fur (palette 831, walk and fight frames,
low-saturation pixels without claws/eyes) by normalised height (feet 0, head top 1), against the rebuilt texture's fur
texels (class 'fur' of compose_wwf.py) by rest height. Prints luminance mean/p10/p50/p90 per band (sRGB 0-255)."""
import glob, sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
W = np.array([0.2126, 0.7152, 0.0722])
BANDS = [(0, .12, 'feet/shins'), (.12, .33, 'legs'), (.33, .55, 'shorts band'), (.55, .74, 'chest/arms'),
         (.74, .86, 'shoulders/neck'), (.86, 1.01, 'head')]


def native_fur():
    hs, ls = [], []
    for f in sorted(glob.glob(str(HERE.parent / 'mm6_wfigt1/native_variants/w[wf][ai]*_831.png'))):
        a = np.asarray(Image.open(f).convert('RGBA')).astype(float) / 255
        al = a[..., 3] > 0.5; ys = np.nonzero(al.any(1))[0]; top, bot = ys.min(), ys.max()
        rgb = a[..., :3]; mx, mn = rgb.max(-1), rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        fur = al & (sat < 0.22) & (mx < 0.62)
        yy = np.repeat(np.arange(a.shape[0])[:, None], a.shape[1], 1)
        hs.append((bot - yy[fur]) / (bot - top)); ls.append(rgb[fur] @ W)
    return np.concatenate(hs), np.concatenate(ls)


def model_fur(base_path):
    R = np.load(HERE / 'work/raster_v1.npz'); cov = R['cov']; pos = R['pos']
    cls = np.asarray(Image.open(HERE / 'textures/wwf_classes.png').convert('RGB').resize((2048, 2048), Image.NEAREST))
    fur = cov & (cls[..., 0] == 60) & (cls[..., 1] == 60)
    base = np.asarray(Image.open(base_path).convert('RGB')).astype(float) / 255
    y = pos[..., 1]; h = (y - y[cov].min()) / (y[cov].max() - y[cov].min())
    return h[fur], base[fur] @ W


def table(h, l):
    rows = []
    for a, b, name in BANDS:
        s = (h >= a) & (h < b); v = l[s] * 255
        rows.append((name, int(s.sum()), round(v.mean(), 1), *[round(np.percentile(v, q), 1) for q in (10, 50, 90)]))
    return rows


if __name__ == '__main__':
    nh, nl = native_fur(); mh, ml = model_fur(sys.argv[1] if len(sys.argv) > 1 else HERE / 'textures/wwf_basecolor.png')
    print('band | native n mean p10 p50 p90 | model n mean p10 p50 p90')
    for a, b in zip(table(nh, nl), table(mh, ml)):
        print(a[0], '|', *a[1:], '|', *b[1:])
