#!/usr/bin/env python3
"""Advisory check for the detached audit's new a60 note (R boot 'root lift' off the R boot cuff in AttackMelee): per clip at 30 fps,
the largest distance from any R-boot vertex that lies within 1 cm of the R cuff at rest to the posed cuff surface, installed vs candidate.
Usage: boot_cuff_gap.py <candidate.glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


def comps(P, T):
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    return connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1][FT[:, 0]]


def run(path):
    m = Model(Glb(path)); out = {}
    P0 = None
    for clip in m.clips:
        t1 = m.clip_times(clip)[-1]; worst = 0.0
        for t in np.append(np.arange(0, t1, 1 / 30), t1):
            posed = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
            if P0 is None:
                import bglbio
                doc, b = bglbio.read(path); node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM7' and 'mesh' in n)
                pr = bglbio.prims(doc, b, node['mesh'])[0]; P0 = pr['POSITION'].astype(np.float64); T = pr['T']
                fl = comps(P0, T); C = P0[T].mean(1)
                cand = [c for c in np.unique(fl) if (C[fl == c][:, 0] < 0).all()]
                boot = max((c for c in cand if C[fl == c][:, 1].min() < 0.05), key=lambda c: (fl == c).sum())
                cuff = [c for c in cand if 0.3 < C[fl == c][:, 1].mean() < 0.5 and (fl == c).sum() > 50][0]
                cT = T[fl == cuff]; bv = np.unique(T[fl == boot].ravel())
                A, B_, Cc = P0[cT[:, 0]], P0[cT[:, 1]], P0[cT[:, 2]]
                d0 = np.array([np.linalg.norm(closest_on_triangles(np.tile(P0[v], (len(A), 1)), A, B_, Cc) - P0[v], axis=-1).min() for v in bv])
                near = bv[d0 < 0.01]
            A, B_, Cc = posed[cT[:, 0]], posed[cT[:, 1]], posed[cT[:, 2]]
            d = max(np.linalg.norm(closest_on_triangles(np.tile(posed[v], (len(A), 1)), A, B_, Cc) - posed[v], axis=-1).min() for v in near)
            worst = max(worst, d)
        out[clip] = round(worst * 1000, 1)
    return len(near), out


for p in (str(HERE / 'before' / 'mm9_peasantm7.glb'), sys.argv[1]):
    print(Path(p).name, *run(p))
