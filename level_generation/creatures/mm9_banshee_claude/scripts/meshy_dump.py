#!/usr/bin/env python3
"""Meshy body GLB -> work/meshy_body.npz (Blender axes, main part only). Usage: meshy_dump.py glb out.npz"""
import sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb
g = Glb(sys.argv[1]); doc = g.json
p = doc['meshes'][0]['primitives'][0]
P = g.accessor(p['attributes']['POSITION']); T = g.accessor(p['indices']).astype(int).reshape(-1, 3)
node = next(n for n in doc['nodes'] if 'mesh' in n); print({k: node.get(k) for k in ('matrix', 'rotation', 'scale', 'translation')})
co = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)
np.savez(sys.argv[2], co=co, tri=T)
print(co.min(0), co.max(0), len(T))
