#!/usr/bin/env python3
"""Kept pieces of the reduced GLB against the source, per piece label (work/pieces.npy): every LOD0 vertex of the
source at a rest position of a vertex of that piece in work/mesh_in.npz must exist in the reduced LOD0 at the same bind
position (< 0.01 mm) with the same weights (< 0.002). The dagger sheath matters most: the Dagger bone follows the
sheath's deformed vertices in every clip, so an unchanged sheath keeps the sheathed dagger and its track valid.
Usage: kept_check.py <source.glb> <reduced.glb> [node, default M442]"""
import sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __import__('os').path.dirname(__file__))
from grip_check import lod0  # noqa: E402  (same GLB reader; NODE from argv[3])
sp, sw, names = lod0(sys.argv[1]); cp, cw, _ = lod0(sys.argv[2])
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; p = np.load('work/pieces.npy')
blender_to_gltf = lambda x: np.stack([x[:, 0], x[:, 2], -x[:, 1]], 1)
tree = cKDTree(cp)
for lab, name in ((9, 'sheath'), (10, 'bands'), (11, 'belt+strap'), (12, 'buckle'), (13, 'mask'), (14, 'eyes'), (15, 'boot ornament')):
    pts = blender_to_gltf(v[np.unique(f[p == lab])])
    _, si = cKDTree(sp).query(pts); sel = np.unique(si)
    dist, ci = tree.query(sp[sel]); wd = np.abs(sw[sel] - cw[ci]).max(1)
    print(f'KEPT {name:14s} vertices {len(sel):4d} max position diff mm {dist.max() * 1000:.4f} weight diffs > 0.002: {int((wd > .002).sum())}')
