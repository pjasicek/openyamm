"""Step 1: Meshy Smart Topology -> labelled parts, metres, Blender frame (faces -Y, z up, soles at 0), mirror symmetric: of each L/R pair the figure's LEFT (+x) part is kept and mirrored;
single parts (torso with arms, legs, yokes, belt, panels) are bisected and their left half mirrored. Raw uv/normals dropped. Args: <meshy glb> <out npz>"""
import sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
HEIGHT = 1.605   # MM9 crown top over soles (LICHKING bind, raw units)
g = GLTF2().load(IN); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]; ct = {5126: 'f4', 5123: 'u2', 5125: 'u4'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(float)
p = g.meshes[0].primitives[0]; P = acc(p.attributes.POSITION); T = acc(p.indices).astype(int).reshape(-1, 3)
P = np.c_[P[:, 0], -P[:, 2], P[:, 1]]
key = np.round(P, 5); _, inv, = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
n = inv.max() + 1; Q = np.zeros((n, 3)); Q[inv] = P; T = inv[T]
T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
par = np.arange(n)
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in T: a = f(t[0]); par[f(t[1])] = a; par[f(t[2])] = a
root = np.array([f(i) for i in range(n)])
S = HEIGHT / np.ptp(Q[:, 2]); Q = Q * S; Q[:, 2] -= Q[:, 2].min()
Q[:, 0] -= 0.5 * (Q[:, 0].min() + Q[:, 0].max())
comp = {}
for r in np.unique(root):
    ids = np.where(root == r)[0]; comp[r] = ids
order = sorted(comp, key=lambda r: -len(comp[r]))
out = {}
for k, r in enumerate(order):
    ids = comp[r]; q = Q[ids]
    print(k, len(ids), np.round(q.mean(0), 3).tolist(), 'min', np.round(q.min(0), 3).tolist(), 'max', np.round(q.max(0), 3).tolist())
np.savez(OUT, co=Q, tri=T, comp=np.searchsorted(np.array(order), root) if False else np.array([order.index(r) for r in root]))
