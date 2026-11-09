#!/usr/bin/env python3
"""Wing knuckles (the bumps on the leading-edge tube at each spar joint, flattened by the r82 cut, review/sheet_body_*:
wing_knuckle): wing front faces with a vertex within R m of a spar joint (YwingA-E heads, bind space from the inverse
binds) are kept exactly. Usage: knuckle_lock.py <R> <out .npy>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
R, out = float(sys.argv[1]), sys.argv[2]
m = Model(Glb(str(HERE / 'before' / 'mm9_wingedmutant.glb'))); names = [m.glb.json['nodes'][j]['name'] for j in m.joints]
bind = np.linalg.inv(m.inverse_binds)
pts = np.array([bind[i][:3, 3] for i, n in enumerate(names) if n.startswith('Ywing') and n[5:6] in 'ABCDE' and len(n) in (6, 8)])
pts = np.stack([pts[:, 0], -pts[:, 2], pts[:, 1]], 1)   # glTF y-up -> Blender mesh-local (mesh_in.npz)
s = np.load(HERE / 'work' / 'mesh_in.npz'); S = np.load(HERE / 'work' / 'sets.npz'); v, f = s['verts'], s['faces']
d, _ = cKDTree(pts).query(v)
lock = (d < R)[f].any(1) & (S['group'] == 2) & ~S['back']
print('KNUCKLES', len(pts), 'joints;', int(lock.sum()), 'wing faces,', int((lock & ~S['keep']).sum()), 'not yet kept')
np.save(out, lock)
