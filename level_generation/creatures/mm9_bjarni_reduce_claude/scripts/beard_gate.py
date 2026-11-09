#!/usr/bin/env python3
"""PeasantDM2 beard gate (reduction; after mm9_dwarf_reduce_claude/scripts/beard_gate.py): over the head-shell faces of the
beard (PeasantM5Head vertices below the mouth, y < 0.975 m at rest, above the collar), per clip at 48 fps (every clip
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
prim = g.json['meshes'][next(n['mesh'] for n in g.json['nodes'] if n.get('name') == 'Bjarni' and 'mesh' in n)]['primitives']
mats = [g.json['materials'][p['material']]['name'] for p in prim]
kb, kh = mats.index('Bjarni'), mats.index('BjarniHead')
rest = m.skinned_positions(m.world({}))
rb, rh = rest[kb][0], rest[kh][0]
T = np.asarray(m.primitives[kh]['triangles']).reshape(-1, 3)
c = rh[T].mean(1)
hand = np.abs(c[:, 0]) > 0.3
beard_f = ~hand & (c[:, 1] < 0.975) & (c[:, 1] > 0.80)
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
print('BEARD faces', int(beard_f.sum()), 'edges', len(E_), 'contact verts', len(cv))
json.dump({'beard_faces': int(beard_f.sum()), 'contact_verts': int(len(cv)), 'clips': res}, open(sys.argv[2], 'w'), indent=1)
