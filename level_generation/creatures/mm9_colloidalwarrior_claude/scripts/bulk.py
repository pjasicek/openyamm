#!/usr/bin/env python3
"""Bulk toward MM9's slab (second pass): on the exported body GLB, same topology and UVs, only POSITION and NORMAL rewritten.
- arms: vertices carried by UpperArm/Forearm (and their helpers) are pushed out from the bone axis by ARM (x radius), weighted by
  that arm share and faded out over the shoulder (near the UpperArm joint) and the wrist, so the armpit and the graft keep their shape;
- head: vertices carried by Head/Head_h move down by HEAD metres times their head share (the throat rolls take the difference);
  move the joint with head_pivot.py 0 -HEAD 0 afterwards.
Normals are recomputed (area weighted, welded by position). Args: <in glb> <out glb>  env ARM (1.15), HEAD (0.04)"""
import os, sys
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared', 'floor'))
from glb_pose import Glb, Model
IN, OUT = sys.argv[1:3]
ARM, HEAD = float(os.environ.get('ARM', 1.15)), float(os.environ.get('HEAD', 0.04))
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
names = [g.nodes[j].name for j in g.skins[0].joints]; ix = {n: i for i, n in enumerate(names)}
m = Model(Glb(IN)); W0 = m.world({}); nn = [n.get('name') for n in m.glb.json['nodes']]
J = {n: W0[nn.index(n)][:3, 3] for n in names}
def acc(i, dt):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(bytes(blob), dt, a.count * k, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, k).copy()
def put(arr, ctype, typ, minmax=False):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    a = Accessor(bufferView=len(g.bufferViews) - 1, componentType=ctype, count=len(arr), type=typ)
    if minmax: a.min = arr.min(0).tolist(); a.max = arr.max(0).tolist()
    g.accessors.append(a); return len(g.accessors) - 1
sm = lambda a, b, v: (lambda u: u * u * (3 - 2 * u))(np.clip((v - a) / (b - a), 0, 1))
prims = [p for mesh in g.meshes for p in mesh.primitives if p.attributes.JOINTS_0 is not None]
prims = prims[:max(1, sum(1 for mesh in g.meshes[:1] for p in mesh.primitives))]        # LOD0 mesh only (LODs are built later)
Ps, Qs, Ns, Ts, off = [], [], [], [], 0
for p in prims:
    P = acc(p.attributes.POSITION, 'f4').astype(float); Jt = acc(p.attributes.JOINTS_0, 'u1' if g.accessors[p.attributes.JOINTS_0].componentType == 5121 else 'u2').astype(int)
    Wt = acc(p.attributes.WEIGHTS_0, 'f4').astype(float)
    def share(keys):
        ids = [ix[k] for k in keys if k in ix]; return (np.isin(Jt, ids) * Wt).sum(1)
    Q = P.copy()
    for s_ in 'LR':
        B = 'Bip01 ' + s_ + ' '
        wa = share([B + k for k in ('UpperArm', 'UpperArm_h', 'Forearm', 'Forearm_h')])
        a, b, c = J[B + 'UpperArm'], J[B + 'Forearm'], J[B + 'Hand']
        for p0, p1, f0 in ((a, b, True), (b, c, False)):
            d = p1 - p0; L = np.linalg.norm(d); d = d / L
            t = (P - p0) @ d; foot = p0 + np.outer(np.clip(t, 0, L), d); r = P - foot
            along = np.clip(t / L, 0, 1)
            fade = (sm(0.10, 0.35, along) if f0 else 1 - sm(0.75, 0.98, along))
            inseg = (t > -0.05) & (t < L + 0.05)
            k = wa * fade * inseg
            Q += r * ((ARM - 1) * k)[:, None] * (np.linalg.norm(r, axis=1) < 0.3)[:, None]
    wh = share(['Bip01 Head', 'Bip01 Head_h'])
    Q[:, 1] -= HEAD * wh
    T = acc(p.indices, {5123: 'u2', 5125: 'u4'}[g.accessors[p.indices].componentType]).reshape(-1, 3).astype(int)
    Ps.append(P); Qs.append(Q); Ns.append(acc(p.attributes.NORMAL, 'f4').astype(float)); Ts.append(T + off); off += len(P)
P, Q, N0, T = np.vstack(Ps), np.vstack(Qs), np.vstack(Ns), np.vstack(Ts)
_, uid = np.unique(np.round(P, 5), axis=0, return_inverse=True); uid = uid.ravel()
fn = np.cross(Q[T[:, 1]] - Q[T[:, 0]], Q[T[:, 2]] - Q[T[:, 0]])
Nu = np.zeros((uid.max() + 1, 3))
for c in range(3): np.add.at(Nu, uid[T[:, c]], fn)
moved = np.zeros(uid.max() + 1, bool); np.logical_or.at(moved, uid, np.linalg.norm(Q - P, axis=1) > 1e-6)
near = moved.copy()
for c in range(3):
    for c2 in range(3): np.logical_or.at(near, uid[T[:, c]], moved[uid[T[:, c2]]])
N = Nu[uid]; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
N = np.where(near[uid][:, None], N, N0)          # unmoved skin keeps its exported normals
o = 0
for p, Pp in zip(prims, Ps):
    k = len(Pp)
    p.attributes.POSITION = put(Q[o:o + k].astype('f4'), 5126, 'VEC3', True)
    p.attributes.NORMAL = put(N[o:o + k].astype('f4'), 5126, 'VEC3'); o += k
print('BULK', len(P), 'max move', round(float(np.linalg.norm(Q - P, axis=1).max()), 3), 'moved', int(moved.sum()))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
