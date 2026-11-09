"""Point plots of work/raw_<tag>.npz with a labelled 5 cm grid (PIL): top (x,y), front (x,z), side (y,z).
Main piece white, pieces 1-3 green, others red. Args: tag out_prefix [px_per_m] [xmin]."""
import sys
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
P = Path(__file__).resolve().parents[1]
tag, out = sys.argv[1], sys.argv[2]
S = float(sys.argv[3]) if len(sys.argv) > 3 else 1200
xmin = float(sys.argv[4]) if len(sys.argv) > 4 else -9
d = np.load(P / f'work/raw_{tag}.npz'); co, part = d['co'], d['part']
keep = co[:, 0] >= xmin; co, part = co[keep], part[keep]
col = np.where(part[:, None] == 0, [230, 230, 230], np.where((part[:, None] >= 1) & (part[:, None] <= 3), [60, 200, 60], [255, 60, 60]))
for name, (a, b, flip) in {'top': (0, 1, True), 'front': (0, 2, True), 'side': (1, 2, True)}.items():
    u, v = co[:, a], co[:, b]
    lo_u, hi_u, lo_v, hi_v = u.min() - .03, u.max() + .03, v.min() - .03, v.max() + .03
    W, H = int((hi_u - lo_u) * S), int((hi_v - lo_v) * S)
    im = Image.new('RGB', (W, H), (25, 25, 30)); dr = ImageDraw.Draw(im)
    X = lambda x: (x - lo_u) * S; Y = lambda y: (hi_v - y) * S
    for g in np.arange(np.ceil(lo_u / .05) * .05, hi_u, .05):
        dr.line([(X(g), 0), (X(g), H)], fill=(70, 70, 90) if abs(g) > 1e-6 else (140, 60, 60)); dr.text((X(g) + 2, 2), f'{g:.2f}', fill=(200, 200, 90))
    for g in np.arange(np.ceil(lo_v / .05) * .05, hi_v, .05):
        dr.line([(0, Y(g)), (W, Y(g))], fill=(70, 70, 90) if abs(g) > 1e-6 else (140, 60, 60)); dr.text((2, Y(g) + 2), f'{g:.2f}', fill=(200, 200, 90))
    order = np.argsort(part)[::-1]
    for i in order:
        x, y = X(u[i]), Y(v[i]); dr.point((x, y), fill=tuple(int(c) for c in col[i]))
    im.save(f'{out}_{name}.png'); print(name, im.size)
