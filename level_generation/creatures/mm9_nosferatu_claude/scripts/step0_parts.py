"""Meshy Smart Topology -> metres, Blender frame (faces -Y, z up, floor 0), connected parts printed. Args: <meshy glb> <out npz> [height]"""
import sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
HEIGHT = float(sys.argv[3]) if len(sys.argv) > 3 else 1.90     # A pose: MM9 pelvis 1.098 straight legged, chain to the head joint 1.602, skull top + ear tips
g = GLTF2().load(IN); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]; ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
p = g.meshes[0].primitives[0]; Q0 = acc(p.attributes.POSITION); T = acc(p.indices).astype(int).reshape(-1, 3)
Q0 = np.c_[Q0[:, 0], -Q0[:, 2], Q0[:, 1]]
key = np.round(Q0, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
n = inv.max() + 1; Q = np.zeros((n, 3)); Q[inv] = Q0; T = inv[T]
T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
par = np.arange(n)
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in T:
    a = f(t[0]); par[f(t[1])] = a; par[f(t[2])] = a
root = np.array([f(i) for i in range(n)])
S = HEIGHT / np.ptp(Q[:, 2]); Q = Q * S; Q[:, 2] -= Q[:, 2].min()
Q[:, 0] -= 0.5 * (Q[:, 0].min() + Q[:, 0].max())
us, cnt = np.unique(root, return_counts=True); order = us[np.argsort(-cnt)]
remap = {r: k for k, r in enumerate(order)}; comp = np.array([remap[r] for r in root])
for k, r in enumerate(order[:50]):
    q = Q[comp == k]; ft = (comp[T[:, 0]] == k).sum()
    print(k, 'v', len(q), 'f', ft, 'min', np.round(q.min(0), 3).tolist(), 'max', np.round(q.max(0), 3).tolist())
print('parts', len(order), 'verts', n, 'tris', len(T))
np.savez(OUT, co=Q, tri=T, comp=comp)
