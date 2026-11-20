#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_nobleman.glb) from the finished master (work/final_parts.npz,
dump_final_parts.py): matched by rest centroid (Blender z-up -> glTF y-up). Primitive order Highwayman_A (limbs),
HwTorso_A, HwHead_A, HwWeapon_A. Writes work/glb_parts.npz: per GLB face mat (prim index), part, lining, weapon, cen (glTF)."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(sys.argv[1] if len(sys.argv) > 1 else HERE / 'before' / 'mm9_nobleman.glb', 'Nobleman')
f = np.load(HERE / 'work' / 'final_parts.npz')
fc = f['cen'][:, [0, 2, 1]] * [1, 1, -1]; fc[:, 1] -= f['co'][:, 2].min()          # the export stands the lowest point on y = 0
tree = cKDTree(fc)
out = dict(mat=[], part=[], lining=[], weapon=[], cen=[])
PR = ['Nobleman_A', 'NbTorso', 'NbHead']
for k, name in enumerate(PR):
    P, T = D[name]['P'], D[name]['T']; gc = P[T].mean(1)
    dist, nn = tree.query(gc)
    print(name, len(T), 'max dist', dist.max(), 'dup', len(nn) - len(np.unique(nn)))
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    for key in ('part', 'lining', 'weapon'):
        out[key].append(f[key][nn])
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
for p in np.unique(res['part']):
    s = res['part'] == p; print(f'part {p:3d} {s.sum():6d} lining {int(res["lining"][s].sum()):5d} mats {np.unique(res["mat"][s]).tolist()}')
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
