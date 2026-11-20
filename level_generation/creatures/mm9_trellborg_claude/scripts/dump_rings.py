"""Rings of the Meshy body along arm and leg (x>0 half), Blender axes. Args: <glb>"""
import sys, numpy as np, pygltflib
sys.path.insert(0, '../mm9_gezzampt_claude/scripts')
from clips_mm9 import read
g = pygltflib.GLTF2().load(sys.argv[1])
p = g.meshes[0].primitives[0]; V = read(g, p.attributes.POSITION)
n = g.nodes[[i for i, x in enumerate(g.nodes) if x.mesh is not None][0]]
print('NODE', n.translation, n.rotation, n.scale)
P = np.c_[V[:, 0], -V[:, 2], V[:, 1]]
print(P.min(0), P.max(0))
L = P[(P[:, 0] > 0)]
print('LEG rings')
for z in np.arange(-0.5, 0.06, 0.03):
    q = L[(np.abs(L[:, 2] - z) < 0.015) & (L[:, 0] < 0.17)]
    if len(q) > 3: print(round(z, 3), np.round(0.5 * (q.min(0) + q.max(0))[:2], 3), np.round(np.ptp(q, 0)[:2], 3), len(q))
print('ARM rings')
for z in np.arange(-0.15, 0.4, 0.03):
    q = L[(np.abs(L[:, 2] - z) < 0.015) & (L[:, 0] > 0.135)]
    if len(q) > 3: print(round(z, 3), np.round(0.5 * (q.min(0) + q.max(0))[:2], 3), np.round(np.ptp(q, 0)[:2], 3), len(q))
print('TORSO')
for z in np.arange(0.0, 0.5, 0.03):
    q = P[(np.abs(P[:, 2] - z) < 0.012) & (np.abs(P[:, 0]) < 0.13)]
    if len(q) > 3: print(round(z, 3), np.round(0.5 * (q.min(0) + q.max(0))[:2], 3), np.round(np.ptp(q, 0)[:2], 3), len(q))
