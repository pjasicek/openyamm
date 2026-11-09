"""Rest world positions of every node of a GLB (and mesh bounds). Usage: joints_rest.py in.glb [filter]"""
import sys, numpy as np
from pygltflib import GLTF2
from scipy.spatial.transform import Rotation as R
g = GLTF2().load(sys.argv[1]); flt = sys.argv[2] if len(sys.argv) > 2 else ''
par = {}
for i, n in enumerate(g.nodes):
    for c in n.children or []: par[c] = i
def local(n):
    m = np.eye(4)
    if n.matrix: return np.array(n.matrix).reshape(4, 4).T
    t = n.translation or [0, 0, 0]; q = n.rotation or [0, 0, 0, 1]; s = n.scale or [1, 1, 1]
    m[:3, :3] = R.from_quat(q).as_matrix() * s; m[:3, 3] = t; return m
W = {}
def world(i):
    if i in W: return W[i]
    m = local(g.nodes[i]); W[i] = (world(par[i]) @ m) if i in par else m; return W[i]
for i, n in enumerate(g.nodes):
    if flt in (n.name or ''):
        p = world(i)[:3, 3]; print(f'{n.name:28s} {p[0]:8.3f} {p[1]:8.3f} {p[2]:8.3f}')
