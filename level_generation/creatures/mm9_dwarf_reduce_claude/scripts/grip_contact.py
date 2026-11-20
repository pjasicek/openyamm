#!/usr/bin/env python3
"""Hand faces in grip contact with the axe, posed: the rest pose holds an open hand (finger_keys.py closes the fist in
the clips), so contact is measured on the installed GLB over every 4th key time of every clip. A hand face within
CONTACT_CM (1) of an axe vertex in any sampled frame is contact. work/mesh_in.npz keeps the GLB's face order (checked:
mesh_in = (x, -z, y - 0.636) of the GLB rest, residual 2e-6). -> work/grip_contact.npy (bool per mesh_in face)."""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(str(HERE / 'before' / 'mm9_dwarf.glb')))
P = [p['positions'] for p in m.primitives]; T = [p['triangles'] for p in m.primitives]
off = np.cumsum([0] + [len(p) for p in P]); allT = np.vstack([t + o for t, o in zip(T, off)])
rest = np.vstack(P)
mi = np.load(HERE / 'work' / 'mesh_in.npz'); L = np.load(HERE / 'work' / 'labels.npz')
e1 = np.linalg.norm(rest[allT[:, 0]] - rest[allT[:, 1]], axis=1); e2 = np.linalg.norm(mi['verts'][mi['faces'][:, 0]] - mi['verts'][mi['faces'][:, 1]], axis=1)
assert len(allT) == len(mi['faces']) and np.abs(e1 - e2).max() < 1e-5, 'face order differs'
nn = np.arange(len(allT))
part = L['part']; gpart = np.full(len(allT), -1); gpart[nn] = part
hand = np.flatnonzero(gpart == 0); axe_v = np.unique(allT[gpart == 30])
R = float(os.environ.get('CONTACT_CM', '1')) / 100
hit = np.zeros(len(allT), bool)
for clip in m.clips:
    for t in m.clip_times(clip)[::4]:
        pos = np.vstack([p for p, _ in m.skinned_positions(m.world(m.sample(clip, t)))])
        tree = cKDTree(pos[axe_v]); dd, _ = tree.query(pos[allT[hand]].reshape(-1, 3))
        hit[hand[(dd.reshape(-1, 3) < R).any(1)]] = True
out = hit[nn]; np.save(HERE / 'work' / 'grip_contact.npy', out)
print('CONTACT faces', int(out.sum()))
