#!/usr/bin/env python3
"""Meshy auto-rig joints mapped onto work/placed.npz (bounding boxes matched: uniform scale from the height, x/y box
centre, floor). Writes work/meshy_joints.json (Meshy bone name -> Blender-space point)."""
import sys, json
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
import glb_pose as gp
g = gp.Glb(HERE / 'meshy/rig_v1/result_rigged_character_glb_url.glb')
for n in g.json['nodes']:
    if 'matrix' in n:
        M = np.array(n.pop('matrix')).reshape(4, 4).T; sc = np.linalg.norm(M[:3, :3], axis=0)
        n['translation'] = M[:3, 3].tolist(); n['scale'] = sc.tolist(); n['rotation'] = gp.matrix_quaternion(M[:3, :3] / sc).tolist()
m = gp.Model(g); w = m.world({}); names = [n.get('name') for n in g.json['nodes']]
pal = w[m.joints] @ m.inverse_binds
V = []
for pr in m.primitives:
    p = pr['positions']; h = np.c_[p, np.ones(len(p))]
    M = np.einsum('vk,vkij->vij', pr['weights'], pal[pr['joints']]) if pr['skinned'] else np.repeat(w[pr['node']][None], len(p), 0)
    V.append(np.einsum('vij,vj->vi', M, h)[:, :3])
V = np.concatenate(V)
tob = lambda a: np.stack([a[:, 0], -a[:, 2], a[:, 1]], 1)
Vb = tob(V); Jb = tob(np.array([w[j][:3, 3] for j in m.joints]))
D = np.load(HERE / ('work/placed_tail.npz' if (HERE / 'work/placed_tail.npz').exists() else 'work/placed.npz')); B = D['co']
s = (B[:, 2].max() - B[:, 2].min()) / (Vb[:, 2].max() - Vb[:, 2].min())
cen = lambda c: np.array([(c[:, 0].max() + c[:, 0].min()) / 2, (c[:, 1].max() + c[:, 1].min()) / 2, c[:, 2].min()])
t = cen(B) - cen(Vb) * s
out = {names[j]: (Jb[k] * s + t).round(4).tolist() for k, j in enumerate(m.joints)}
json.dump(out, open(HERE / 'work/meshy_joints.json', 'w'), indent=0)
for k, v in out.items(): print(k, v)
