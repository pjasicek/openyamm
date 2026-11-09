"""Where are green texels inside the gold chest and gold texels on green legs? Prints 3D clusters with old-reference
distance and part, from the final body texture."""
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[2] / 'mm6_drr1_claude'
sys.path.insert(0, str(P.parent / 'mm6_gob_claude/scripts'))
import compose_textures_v2 as C
D = np.load(P / 'work/uv3d_v3.npz'); part, xyz = C.rasterise(D, tol=0); valid = part >= 0
base = C.load(P / 'textures/wyrm_basecolor.png'); h, s, v = C.hsv(base)
gold = valid & (h > 20) & (h < 80) & (s > .25); green = valid & (h >= 80) & (h < 170) & (s > .2)
ys, xs = np.nonzero(valid); sel = slice(None, None, 20)
tree = cKDTree(xyz[ys[sel], xs[sel]]); cls = np.where(gold[ys[sel], xs[sel]], 1, np.where(green[ys[sel], xs[sel]], 2, 0))
for name, mask, other in (('green-in-gold', green, 1), ('gold-in-green', gold, 2)):
    cy, cx = np.nonzero(mask)
    _, nb = tree.query(xyz[cy, cx], k=40); frac = (cls[nb] == other).mean(1)
    hit = np.zeros(valid.shape, bool); hit[cy, cx] = frac > .6
    lab, n = ndimage.label(hit); sizes = ndimage.sum(hit, lab, range(1, n + 1))
    for c in np.argsort(-sizes)[:8]:
        yy, xx = np.nonzero(lab == c + 1)
        print(name, int(sizes[c]), 'texels at', np.round(xyz[yy, xx].mean(0), 3), 'part', np.unique(part[yy, xx]),
              'frac', round(float(np.mean(frac[np.isin(np.arange(len(cy)), np.nonzero(lab[cy, cx] == c + 1)[0])])), 2))
