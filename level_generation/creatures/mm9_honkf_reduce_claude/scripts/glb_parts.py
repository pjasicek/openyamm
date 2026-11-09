#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_zombie.glb) from the creature project's rest faces
(../mm9_zombie_claude/work/faces3.npz, the faces cloth_gate.py reads: part per face, Blender z-up before the export lift).
Map Blender -> glTF: (x, z + LIFT, -y), LIFT 0.7566 (export_zombie.py lifts the rig so the lowest point is y = 0).
Parts (rig_zombie.py / graft_head.py / fit_pose.py): 0 skin (limbs, hands, chest), 1 trousers, 2 tatter, 3 rope, 4 shin bone,
5 bony right foot, 10 face/head skin with neck, 11 hair locks, 12 teeth, 13 eyes; added here: 20 skull plug (export_zombie's
icosphere inside the head, not in faces3), and `lining` (export_zombie's reversed tatter copies 1.5 mm inside: same centroid
as an outer tatter face within ~2 mm, opposite normal).
Writes work/glb_parts.npz: per GLB face (primitive order Zombie_A, ZombieHead_A, ZombieTorso) mat, part, lining, torso, cen."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
LIFT = 0.7566
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_zombie.glb', 'Zombie')
f = np.load(HERE.parent / 'mm9_zombie_claude' / 'work' / 'faces3.npz')
co = f['co']; co = np.stack([co[..., 0], co[..., 2] + LIFT, -co[..., 1]], -1)
fc = co.mean(1); fn = np.cross(co[:, 1] - co[:, 0], co[:, 2] - co[:, 0])
tree = cKDTree(fc)
PR = ['Zombie_A', 'ZombieHead_A', 'ZombieTorso']
out = dict(mat=[], part=[], lining=[], torso=[], cen=[], dist=[])
for k, name in enumerate(PR):
    P, T = D[name]['P'], D[name]['T']; gc = P[T].mean(1)
    gn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    dist, nn = tree.query(gc, 4)
    # nearest source face with the same orientation; a lining face only finds its outer twin reversed
    same = (fn[nn] * gn[:, None]).sum(-1) > 0
    pick = np.where(same.any(1), same.argmax(1), 0)
    j = nn[np.arange(len(T)), pick]; dj = dist[np.arange(len(T)), pick]
    part = f['part'][j].copy()
    lining = ~same.any(1) & (dist[:, 0] < 0.004) & (f['part'][nn[:, 0]] == 2)
    part[lining] = 2
    plug = (k == 1) & (dj > 0.004) & ~lining
    part[plug] = 20
    out['mat'] += [k] * len(T); out['cen'].append(gc); out['part'].append(part); out['lining'].append(lining)
    out['torso'].append(f['torso'][j]); out['dist'].append(dj)
    print(name, len(T), 'match p99', round(float(np.percentile(dj[~plug & ~lining], 99)), 6), 'max', round(float(dj[~plug & ~lining].max()), 6),
          'lining', int(lining.sum()), 'plug', int(plug.sum()))
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
for p in np.unique(res['part']):
    s = res['part'] == p
    print(f'part {p:3d} {s.sum():6d} lining {int(res["lining"][s].sum()):5d} mats {np.unique(res["mat"][s]).tolist()}')
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
