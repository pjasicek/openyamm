#!/usr/bin/env python3
"""Band depths from the gate's hole map: each body face with hole pixels (hole_faces.py *_glbfaces.npz) is assigned to the open
loop (by centre, as line.py ops) whose farthest face vertex is nearest, and per loop the hole-weighted depth percentiles plus
the band size (faces of the loop's piece within that depth) are printed. Usage: hole_depth.py <glb> <glbfaces npz> <ops json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
glb, hz, opsf = sys.argv[1:4]
doc, b, nd, prims, jn = C.load(glb); d = prims['PeasantM1_A']; n = len(d['T'])
H = np.load(hz)['PeasantM1_A'][:n]
inv = C.weld(d['P']); TT = inv[d['T']]; WP = np.zeros((inv.max() + 1, 3)); WP[inv] = d['P']; loops, bnd, ec = C.boundary_loops(TT)
pc = C.pieces(TT, inv.max() + 1); fp = pc[TT[:, 0]]
ops = [o for o in json.load(open(opsf)) if o['op'] == 'band' and o.get('prim', 'PeasantM1_A') == 'PeasantM1_A']
D, names = [], []
for o in ops:
    lv = sorted({v for c in o['loops'] for v in min(loops, key=lambda lp: np.linalg.norm(WP[lp].mean(0) - np.array(c)))})
    dd = cKDTree(WP[lv]).query(WP)[0][TT].max(1); dd[~np.isin(fp, [pc[lv[0]]])] = 9
    D.append(dd); names.append(o['name'])
D = np.array(D); a = D.argmin(0); m = H > 0
print('hole px total', int(H.sum()), 'unassigned (other pieces)', int(H[m & (D.min(0) > 8)].sum()))
for k, nm in enumerate(names):
    s = m & (a == k) & (D[k] < 8); w = H[s].astype(int)
    if not w.sum():
        continue
    q = [float(np.percentile(np.repeat(D[k][s], w), x)) for x in (50, 90, 95, 99)]
    print(f'{nm:10s} px {int(w.sum()):7d}  depth p50/90/95/99 {q[0]:.3f} / {q[1]:.3f} / {q[2]:.3f} / {q[3]:.3f}  '
          + '  '.join(f'{dep}: {int((D[k] < dep).sum())} f {H[s & (D[k] < dep)].sum() / max(1, H[s].sum()):.2f}' for dep in (0.07, 0.1, 0.13, 0.16, 0.2, 0.3)))
