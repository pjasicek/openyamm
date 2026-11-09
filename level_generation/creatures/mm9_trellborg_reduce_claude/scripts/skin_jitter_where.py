#!/usr/bin/env python3
"""Where a shoulder-skin jitter excess comes from: per vertex of one side's Clavicle/UpperArm skin, the largest second difference
(mm/frame^2, 30 fps) in <clip> on <glb> minus the same vertex on <ref glb> (same mesh, reference clips: ref_swap.py); prints the top
vertices with their bind position (glTF, metres) and dominant joint. Usage: skin_jitter_where.py <glb> <ref glb> <clip> <L|R> [n]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, ref, clip, side = sys.argv[1:5]; N = int(sys.argv[5]) if len(sys.argv) > 5 else 15; tok = f' {side} '
def run(path):
    m = Model(Glb(Path(path))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
    P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']]
    dom = np.concatenate([np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in P])
    sv = np.where([tok in d and ('Clavicle' in d or 'UpperArm' in d) for d in dom])[0]
    ts = np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30)
    Y = np.array([np.vstack([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k < len(P)])[sv] for t in ts])
    acc = np.linalg.norm(Y[2:] - 2 * Y[1:-1] + Y[:-2], axis=2) * 1000
    return acc, sv, np.vstack([p['positions'] for p in P])[sv], dom[sv]
a, sv, X0, dm = run(glb); b, _, _, _ = run(ref)
ex = (a - b).max(0)
print('vertices', len(sv), 'excess p95', round(float(np.percentile(ex, 95)), 2), 'max', round(float(ex.max()), 2))
for i in np.argsort(-ex)[:N]:
    print(f'  v{sv[i]} excess {ex[i]:.2f} at frame {int(np.argmax(a[:, i] - b[:, i])) + 1} bind {np.round(X0[i], 3)} {dm[i]}')
