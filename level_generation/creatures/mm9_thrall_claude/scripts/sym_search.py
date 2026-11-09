"""Mirror plane and yaw of the Meshy body: least mirror residual of the main part below the neck. Args: <meshy glb>"""
import sys, numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC3': 3}[a.type]; ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
pr = g.meshes[0].primitives[0]
P = acc(pr.attributes.POSITION); P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
Q = P[(P[:, 2] > -0.1) & (P[:, 2] < 0.32) & (np.abs(P[:, 0]) < 0.2)]   # torso
best = None
for yaw in np.radians(np.arange(-10, 10.5, 1)):
    c, s = np.cos(yaw), np.sin(yaw); R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    q = Q @ R.T
    for x0 in np.arange(-0.02, 0.0201, 0.002):
        a = q.copy(); a[:, 0] -= x0
        b = a * [-1, 1, 1]
        d = cKDTree(a).query(b)[0]
        r = np.percentile(d, 90)
        if best is None or r < best[0]: best = (r, np.degrees(yaw), x0)
print('SYM p90 %.4f yaw %.1f x0 %.3f' % best)
