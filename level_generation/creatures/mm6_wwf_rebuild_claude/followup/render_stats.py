#!/usr/bin/env python3
"""Rendered fur luminance in a viewer shot: grey (low saturation) model pixels by normalised screen height of the
model's silhouette (background = the viewer's flat grey). Usage: render_stats.py <shot.png> ..."""
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, __import__('os').path.dirname(__file__))
import tone_stats as TS
W = np.array([0.2126, 0.7152, 0.0722])
for f in sys.argv[1:]:
    a = np.asarray(Image.open(f).convert('RGB')).astype(float)[30:-40] / 255
    bg = np.median(a[:20].reshape(-1, 3), 0)
    fg = np.abs(a - bg).max(-1) > 0.04
    mx, mn = a.max(-1), a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    ys = np.nonzero(fg.any(1))[0]; top, bot = ys.min(), ys.max()
    yy = np.repeat(np.arange(a.shape[0])[:, None], a.shape[1], 1); h = (bot - yy) / (bot - top)
    fur = fg & (sat < 0.22)
    l = a @ W * 255
    print(f.split('/')[-1], ' '.join(f'{n.split("/")[0]}:{np.percentile(l[fur & (h >= lo) & (h < hi)], 50):.0f}/{np.percentile(l[fur & (h >= lo) & (h < hi)], 90):.0f}'
                                      for lo, hi, n in TS.BANDS if (fur & (h >= lo) & (h < hi)).sum() > 50))
