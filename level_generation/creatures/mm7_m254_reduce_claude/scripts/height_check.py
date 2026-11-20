#!/usr/bin/env python3
"""Crown top and horn tips of every colour LOD (rest pose, mesh-local glTF positions converted to Blender z-up):
each LOD vertex takes the piece label (work/pieces.npy) of the nearest source vertex (work/mesh_in.npz, within 6 mm;
LODs are collapses of LOD0, so their vertices stay on the source surface); crown = piece 5, horns = piece 9. In game
units at the binding scale 152.29 the source crown top is 258.9. Usage: height_check.py <glb> [<glb> ...]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
S = 152.29
d = np.load('work/mesh_in.npz'); v, f = d['verts'], d['faces']; p = np.load('work/pieces.npy')
vl = np.zeros(len(v), int)
for k in (5, 9):
    vl[np.unique(f[p == k])] = k
tree = cKDTree(v)
for path in sys.argv[1:]:
    D, B = read_glb(Path(path)); node = next(n for n in D['nodes'] if n.get('name') == 'Golem')
    levels = [node['mesh']] + D['meshes'][node['mesh']]['extras']['openyamm_lods']
    for lvl, mi in enumerate(levels):
        acc = D['meshes'][mi]['primitives'][0]['attributes']['POSITION']
        q = np.frombuffer(accessor_bytes(D, B, acc), np.float32).reshape(-1, 3)
        q = np.stack([q[:, 0], -q[:, 2], q[:, 1]], 1)
        dist, i = tree.query(q); lab = np.where(dist < 0.006, vl[i], 0)
        crest = q[lab == 5, 2].max(); helm = q[lab == 9, 2].max()
        print(f'{Path(path).name} LOD{lvl} top {q[:, 2].max():.4f} m ({q[:, 2].max() * S:.1f} u) crown top {crest:.4f} '
              f'({crest * S:.1f} u) horn tip {helm:.4f} ({helm * S:.1f} u) unmatched {int((dist >= 0.006).sum())}')
