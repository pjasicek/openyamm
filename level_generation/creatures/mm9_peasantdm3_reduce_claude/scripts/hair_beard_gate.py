#!/usr/bin/env python3
"""PeasantDM3 hair and beard gate v2 (reduction): beard_gate.py's selection (SEL=beard: head shell below the mouth; SEL=hair:
the hair shell + 2 mm twin below 1.0 m), per clip at 48 fps:
- stretch: largest posed/rest length ratio over the part's edges (all edges; and edges >= 5 mm at rest, since the all-edge
  maximum sits on 1.6 mm edges at the hair's weight blend in the installed model as well) and the largest elongation in mm;
- torso contact against the posed body SURFACE (closest point on the 8 nearest body triangles by centroid), not the nearest
  body vertex (the reduced body has fewer vertices, so vertex distances change without any geometry change): over the
  contact vertices = rest within 2 cm of the body surface AND present (by position) in REF (the reduced candidate, so the
  installed and reduced runs measure the same vertices): largest gap opening and deepest approach (cm) vs rest.
Usage: hair_beard_gate.py <glb> <out json> <ref glb>   (env SEL beard|hair)"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
SEL = os.environ.get('SEL', 'beard')
m = Model(Glb(Path(sys.argv[1]))); ref = Model(Glb(Path(sys.argv[3]))); src = Model(Glb(HERE / 'before' / 'mm9_peasantdm3.glb'))
kb, kh = 0, 1
sp = src.primitives[kh]; SP = np.asarray(sp['positions']); ST = np.asarray(sp['triangles']).reshape(-1, 3)
_, w = np.unique(np.round(SP, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[ST]; n_ = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
comp = lab[FT[:, 0]]; cnt = np.bincount(comp)
want = (comp == cnt.argmax()) if SEL == 'beard' else np.isin(comp, [k for k in range(len(cnt)) if cnt[k] in (1060, 483)])
okp = {tuple(x) for x in np.round(SP[np.unique(ST[want])], 6)}
refp = {tuple(x) for x in np.round(np.asarray(ref.primitives[kh]['positions']), 6)}
HP = np.asarray(m.primitives[kh]['positions']); T = np.asarray(m.primitives[kh]['triangles']).reshape(-1, 3)
BT = np.asarray(m.primitives[kb]['triangles']).reshape(-1, 3)
key = [tuple(x) for x in np.round(HP, 6)]
inpart = np.array([k in okp for k in key]); inref = np.array([k in refp for k in key])
rest = m.skinned_positions(m.world({})); rb, rh = rest[kb][0], rest[kh][0]
c = rh[T].mean(1); hand = np.abs(c[:, 0]) > 0.3
f = ~hand & inpart[T].all(1) & (((c[:, 1] < 0.975) & (c[:, 1] > 0.80)) if SEL == 'beard' else (c[:, 1] < 1.0))
E_ = np.unique(np.sort(np.vstack([T[f][:, [0, 1]], T[f][:, [1, 2]], T[f][:, [2, 0]]]), 1), axis=0)
L0 = np.linalg.norm(rh[E_[:, 0]] - rh[E_[:, 1]], axis=1); E_ = E_[L0 > 1e-4]; L0 = L0[L0 > 1e-4]; big = L0 >= 0.005


def surf(pb, q):
    cen = pb[BT].mean(1); _, idx = cKDTree(cen).query(q, k=8); best = np.full(len(q), np.inf)
    for j in range(8):
        tt = BT[idx[:, j]]; cp, _ = closest_on_triangles(q, pb[tt[:, 0]], pb[tt[:, 1]], pb[tt[:, 2]])
        best = np.minimum(best, np.linalg.norm(cp - q, axis=1))
    return best


pv = np.unique(T[f]); pv = pv[inref[pv]]; d0 = surf(rb, rh[pv]); cv = pv[d0 < 0.02]; d0 = d0[d0 < 0.02]
res = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; st, stb, el, gap, app = 0.0, 0.0, 0.0, 0.0, 0.0
    for t in np.append(np.arange(0, t1, 1 / 48), t1):
        pz = m.skinned_positions(m.world(m.sample(clip, t))); ph, pb = pz[kh][0], pz[kb][0]
        L = np.linalg.norm(ph[E_[:, 0]] - ph[E_[:, 1]], axis=1)
        st = max(st, float((L / L0).max())); stb = max(stb, float((L[big] / L0[big]).max())); el = max(el, float((L - L0).max()))
        d = surf(pb, ph[cv]); gap = max(gap, float((d - d0).max())); app = max(app, float((d0 - d).max()))
    res[clip] = {'stretch': round(st, 3), 'stretch_5mm': round(stb, 3), 'elong_mm': round(el * 1000, 2),
                 'gap_cm': round(gap * 100, 2), 'approach_cm': round(app * 100, 2)}
    print(f'{clip:12s} stretch {st:.3f} (>=5mm {stb:.3f}) elong {el * 1000:.2f} mm  surface gap +{gap * 100:.2f} cm  approach {app * 100:.2f} cm')
print(SEL.upper(), 'faces', int(f.sum()), 'edges', len(E_), 'contact verts', len(cv))
json.dump({'faces': int(f.sum()), 'contact_verts': int(len(cv)), 'clips': res}, open(sys.argv[2], 'w'), indent=1)
