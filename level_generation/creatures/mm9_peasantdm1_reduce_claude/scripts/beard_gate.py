#!/usr/bin/env python3
"""PeasantDM1 beard gate (reduction; after mm9_dwarf_reduce_claude/scripts/beard_gate.py): over the head-shell faces of the
beard (PeasantDM1Head vertices below the mouth, y < 0.975 m at rest, above the collar), per clip at 48 fps (every clip
sampled at 1/48 s): (1) edge stretch, the largest posed/rest length ratio of a beard edge; (2) beard-torso contact, for the
beard vertices within 2 cm of a body vertex at rest, the largest gap opening (posed distance to the nearest posed body vertex
minus the rest distance, cm) and the deepest approach (rest minus posed, cm). Usage: beard_gate_dm4.py <glb> <out json>"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
g = Glb(Path(sys.argv[1])); m = Model(g)
prim = g.json['meshes'][next(n['mesh'] for n in g.json['nodes'] if n.get('name') == 'PeasantDM1' and 'mesh' in n)]['primitives']
mats = [g.json['materials'][p['material']]['name'] for p in prim]
kb, kh = mats.index('PeasantDM1_A'), mats.index('PeasantDM1Head')
rest = m.skinned_positions(m.world({}))
rb, rh = rest[kb][0], rest[kh][0]
T = np.asarray(m.primitives[kh]['triangles']).reshape(-1, 3)
c = rh[T].mean(1)
hand = np.abs(c[:, 0]) > 0.3
# PeasantDM1: two parts, by the installed head prim's welded components (positions): SEL=beard -> the head shell (face, beard,
# neck) below the mouth; SEL=hair -> the hair shell and its 2 mm twin below 1.0 m (the long hair on the shoulders)
import os
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
src = Model(Glb(HERE / 'before' / 'mm9_peasantdm1.glb')); sp = src.primitives[kh]
SP = np.asarray(sp['positions']); ST = np.asarray(sp['triangles']).reshape(-1, 3)
_, w = np.unique(np.round(SP, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[ST]; n_ = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n_, n_)), directed=False)
comp = lab[FT[:, 0]]; cnt = np.bincount(comp)
SEL = os.environ.get('SEL', 'beard')
want = (comp == cnt.argmax()) if SEL == 'beard' else np.isin(comp, [k for k in range(len(cnt)) if cnt[k] in (1060, 483)])
okp = {tuple(x) for x in np.round(SP[np.unique(ST[want])], 6)}
inpart = np.array([tuple(x) in okp for x in np.round(np.asarray(m.primitives[kh]['positions']), 6)])
sel_f = inpart[T].all(1)
beard_f = ~hand & sel_f & ((c[:, 1] < 0.975) & (c[:, 1] > 0.80) if SEL == 'beard' else (c[:, 1] < 1.0))
E_ = np.vstack([T[beard_f][:, [0, 1]], T[beard_f][:, [1, 2]], T[beard_f][:, [2, 0]]])
L0 = np.linalg.norm(rh[E_[:, 0]] - rh[E_[:, 1]], axis=1); E_ = E_[L0 > 1e-4]; L0 = L0[L0 > 1e-4]
bv = np.unique(T[beard_f]); d0, _ = cKDTree(rb).query(rh[bv]); cv = bv[d0 < 0.02]; d0 = d0[d0 < 0.02]
res = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; st, gap, app = 0.0, 0.0, 0.0
    for t in np.append(np.arange(0, t1, 1 / 48), t1):
        pz = m.skinned_positions(m.world(m.sample(clip, t)))
        ph, pb = pz[kh][0], pz[kb][0]
        st = max(st, float((np.linalg.norm(ph[E_[:, 0]] - ph[E_[:, 1]], axis=1) / L0).max()))
        d, _ = cKDTree(pb).query(ph[cv]); gap = max(gap, float((d - d0).max())); app = max(app, float((d0 - d).max()))
    res[clip] = {'stretch': round(st, 3), 'contact_gap_cm': round(gap * 100, 2), 'contact_approach_cm': round(app * 100, 2)}
    print(f'{clip:12s} stretch {st:.3f}  contact gap +{gap * 100:.2f} cm  approach {app * 100:.2f} cm')
print(SEL.upper(), 'faces', int(beard_f.sum()), 'edges', len(E_), 'contact verts', len(cv))
json.dump({'beard_faces': int(beard_f.sum()), 'contact_verts': int(len(cv)), 'clips': res}, open(sys.argv[2], 'w'), indent=1)
