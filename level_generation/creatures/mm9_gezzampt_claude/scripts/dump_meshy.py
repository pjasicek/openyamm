"""Ring centres of the Meshy body along limbs in Blender axes. Args: <glb>"""
import sys, numpy as np, pygltflib
sys.path.insert(0, '../mm9_thrall_claude/scripts')
from clips_mm9 import read
g = pygltflib.GLTF2().load(sys.argv[1])
p = g.meshes[0].primitives[0]
V = read(g, p.attributes.POSITION)
n = g.nodes[[i for i, x in enumerate(g.nodes) if x.mesh is not None][0]]
print(n.translation, n.rotation, n.scale)
# node may rotate; blender axes = (x, -z, y) of world glTF
P = np.c_[V[:, 0], -V[:, 2], V[:, 1]]
print(P.min(0), P.max(0))
L = P[P[:, 0] > 0.0]
print('LEG rings z: cx cy dx dy n')
for z in np.arange(-0.5, 0.02, 0.025):
    m = (np.abs(L[:, 2] - z) < 0.0125)
    q = L[m]
    q = q[q[:, 0] < 0.2]
    if len(q) < 4: continue
    print(round(z, 3), np.round(0.5 * (q.min(0) + q.max(0))[:2], 3), np.round(np.ptp(q, 0)[:2], 3), len(q))
print('ARM rings x: cy cz dy dz n')
A = L[(L[:, 2] > -0.25) & (L[:, 2] < 0.36)]
for x in np.arange(0.06, 0.345, 0.02):
    q = A[np.abs(A[:, 0] - x) < 0.01]
    if len(q) < 4: continue
    print(round(x, 3), np.round(0.5 * (q.min(0) + q.max(0))[1:], 3), np.round(np.ptp(q, 0)[1:], 3), len(q))
print('TORSO rings z: dx dy cy')
for z in np.arange(-0.1, 0.46, 0.03):
    q = P[(np.abs(P[:, 2] - z) < 0.012) & (np.abs(P[:, 0]) < 0.17)]
    if len(q) < 4: continue
    print(round(z, 3), np.round(np.ptp(q, 0)[:2], 3), np.round(0.5 * (q[:, 1].min() + q[:, 1].max()), 3), 'x', round(0.5 * (q[:, 0].min() + q[:, 0].max()), 3))
