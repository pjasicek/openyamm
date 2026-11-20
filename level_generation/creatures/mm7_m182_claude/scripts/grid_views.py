"""Orthographic vertex projections with a labelled 5 cm grid (side y-z, top x-y, front x-z) for reading joints."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]
co = np.load(P / 'work/rest_co.npy') if len(sys.argv) < 2 else np.load(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else P / 'review'
PX = 1400  # pixels per metre
for name, (a, b), depth in [('side', (1, 2), 0), ('top', (0, 1), 2), ('front', (0, 2), 1)]:
    lo = co[:, [a, b]].min(0) - .05; hi = co[:, [a, b]].max(0) + .05
    w, h = ((hi - lo) * PX).astype(int)
    im = Image.new('RGB', (w, h), (20, 20, 20)); d = ImageDraw.Draw(im)
    for value in np.arange(np.ceil(lo[0] / .05) * .05, hi[0], .05):
        x = (value - lo[0]) * PX; d.line([(x, 0), (x, h)], fill=(70, 70, 90) if abs(value) > 1e-6 else (160, 60, 60))
        d.text((x + 2, 2), f'{value:.2f}', fill=(200, 200, 120))
    for value in np.arange(np.ceil(lo[1] / .05) * .05, hi[1], .05):
        y = h - (value - lo[1]) * PX; d.line([(0, y), (w, y)], fill=(70, 70, 90) if abs(value) > 1e-6 else (160, 60, 60))
        d.text((2, y + 2), f'{value:.2f}', fill=(200, 200, 120))
    dep = co[:, depth]; t = (dep - dep.min()) / max(np.ptp(dep), 1e-6)
    order = np.argsort(dep if name != 'top' else dep)
    xy = np.c_[(co[:, a] - lo[0]) * PX, h - (co[:, b] - lo[1]) * PX]
    pix = np.asarray(im).copy()
    for i in order:
        x, y = int(xy[i, 0]), int(xy[i, 1])
        if 0 <= x < w and 0 <= y < h:
            pix[y, x] = (int(80 + 175 * t[i]), int(200 - 120 * t[i]), int(120 + 100 * (1 - t[i])))
    Image.fromarray(pix).save(out / f'grid_{name}.png')
    print(name, w, h)
