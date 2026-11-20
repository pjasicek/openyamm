#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_thrall.glb) from the finished master (work/final_parts.npz,
dump_final_parts.py): matched by rest centroid (Blender z-up -> glTF y-up). Primitive order Highwayman_A (limbs),
HwTorso_A, HwHead_A, HwWeapon_A. Writes work/glb_parts.npz: per GLB face mat (prim index), part, lining, weapon, cen (glTF)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(sys.argv[1] if len(sys.argv) > 1 else HERE / 'before' / 'mm9_thrall.glb', 'Thrall')
f = np.load(HERE / 'work' / 'final_parts.npz')
fc = f['cen'][:, [0, 2, 1]] * [1, 1, -1]; fc[:, 1] -= f['co'][:, 2].min()          # the export stands the lowest point on y = 0
tree = cKDTree(fc)
out = dict(mat=[], part=[], partmax=[], hand=[], graft_s=[], cen=[])
PR = ['Thrall_A', 'ThrallTorso', 'ThrallHead']
for k, name in enumerate(PR):
    P, T = D[name]['P'], D[name]['T']; gc = P[T].mean(1)
    dist, nn = tree.query(gc)
    print(name, len(T), 'max dist', dist.max(), 'dup', len(nn) - len(np.unique(nn)))
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    for key in ('part', 'partmax', 'hand', 'graft_s'):
        out[key].append(f[key][nn])
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
for p in np.unique(res['part']):
    s = res['part'] == p; print(f'part {p:3d} {s.sum():6d} hand {int(res["hand"][s].sum()):5d} mats {np.unique(res["mat"][s]).tolist()}')
# Thrall parts -> the Nobleman codes make_sets/seam_keeps use: MPFB hands 0, body skin 1, head-set skin bridge 2 (kept), sandals 6,
# skirt 7, collar 8, belt+knot+rope ends 9, face skin 10 -> 20, hair 11 -> 21, eyes 13 -> 22 (original label kept as tpart)
t = res['part'].copy(); res['tpart'] = t
q = np.full(len(t), 1); q[(t == 0) & (res['hand'] == 1)] = 0; q[(t == 0) & (res['mat'] == 2)] = 2
for a, b in ((5, 6), (1, 7), (6, 8), (3, 9), (10, 20), (11, 21), (13, 22)): q[t == a] = b
res['part'] = q; print('REMAP', {int(k): int((q == k).sum()) for k in np.unique(q)})
res['lining'] = np.zeros(len(res['part']), np.int32); res['weapon'] = np.zeros(len(res['part']), np.int32)
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
