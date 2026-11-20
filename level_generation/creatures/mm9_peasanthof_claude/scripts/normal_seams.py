#!/usr/bin/env python3
"""Vertex-normal clean-up of a runtime GLB's head (user review r7, 2026-11-04: thin light lines down the cheek near the ear and on
the chin, also with the normal map flattened, so they are vertex normals split at UV seams; and "a dark wedge under the chin").
1. SEAMS: in every mesh node, the vertices of the head material primitive and the vertices of any other primitive of the same node
   that lie within 0.1 mm of a head vertex (KD-tree groups; r9: rounding buckets missed pairs on a cell edge) get one normal, the normalized mean of the group (UV seams inside the
   head shell, and the head/body seam at the neck).
2. UNDER-CHIN (FINISH_BRIEF rule: a smooth falloff over several cm, never a hard region): head vertices take
   n' = normalize(n + K * w * u), u = normalize(0, UP, FWD) (up and forward), w = exp(-d^2 / (2 S^2)) for the distance d to the
   under-chin point (nose-tip x, height CHY, the chin front minus 2 cm) times a facing factor smoothstep(-n_y, 0.0, 0.6) (only
   down-facing normals turn, fading out smoothly as they level off).
3. NOSE (--nose-s > 0, HOF2 r9: the nostrils read as dark blots in top light): the same turn round a point 12 mm below and behind
   the nose tip, Gaussian sigma NOSE_S, strength NOSE_K, down-facing normals only.
Positions, UVs, weights untouched. Args: <in glb> <out glb> [--chy 1.665] [--s 0.03] [--k 0.7] [--material PeasantHOFHead]
[--headset PeasantHOFHead,PeasantHOFHead_phof1_b]"""
import argparse
import numpy as np
from pygltflib import GLTF2, Accessor, BufferView
ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out')
ap.add_argument('--chy', type=float, default=1.665); ap.add_argument('--s', type=float, default=0.03); ap.add_argument('--k', type=float, default=0.7)
ap.add_argument('--headset', default='PeasantHOFHead,PeasantHOFHead_phof1_b')
ap.add_argument('--nose-s', type=float, default=0.0); ap.add_argument('--nose-k', type=float, default=0.6)   # r9 (HOF2 nostril blots): 0 = off
o = ap.parse_args()
g = GLTF2().load(o.inp); blob = bytearray(g.binary_blob()); heads = set(o.headset.split(','))
def read(i, n):
    a = g.accessors[i]; v = g.bufferViews[a.bufferView]; off = (v.byteOffset or 0) + (a.byteOffset or 0)
    assert a.componentType == 5126 and not v.byteStride or v.byteStride == 4 * n
    return np.frombuffer(bytes(blob[off:off + 4 * n * a.count]), '<f4').reshape(a.count, n).astype(float)
def read_idx(i):
    a = g.accessors[i]; v = g.bufferViews[a.bufferView]; off = (v.byteOffset or 0) + (a.byteOffset or 0)
    dt = {5123: '<u2', 5125: '<u4', 5121: 'u1'}[a.componentType]
    return np.frombuffer(bytes(blob[off:off + np.dtype(dt).itemsize * a.count]), dt).astype(int)
def add(arr):
    while len(blob) % 4: blob.append(0)
    off = len(blob); b = arr.astype('<f4').tobytes(); blob.extend(b)
    g.bufferViews.append(BufferView(buffer=0, byteOffset=off, byteLength=len(b), target=34962))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC3',
                                min=arr.min(0).tolist(), max=arr.max(0).tolist()))
    return len(g.accessors) - 1
done = {}; rep = []
for mi, mesh in enumerate(g.meshes):
    prims = [p for p in mesh.primitives if p.attributes.NORMAL is not None]
    hp = [p for p in prims if g.materials[p.material].name in heads]
    if not hp: continue
    Ps = {id(p): read(p.attributes.POSITION, 3) for p in prims}; Ns = {id(p): read(p.attributes.NORMAL, 3) for p in prims}
    # groups of coincident vertices (within TOL, KD-tree: rounding buckets split pairs that straddle a cell edge, r9)
    from scipy.spatial import cKDTree
    allP = np.vstack([Ps[id(p)] for p in prims]); offs = np.cumsum([0] + [len(Ps[id(p)]) for p in prims])
    ishead = np.zeros(len(allP), bool)
    for p, o_ in zip(prims, offs[:-1]):
        if p in hp: ishead[o_:o_ + len(Ps[id(p)])] = True
    pairs = cKDTree(allP).query_pairs(1e-4, output_type='ndarray')
    par = np.arange(len(allP))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a_, b_ in pairs:
        if ishead[a_] or ishead[b_]:
            ra, rb = find(a_), find(b_)
            if ra != rb: par[rb] = ra
    root = np.array([find(i) for i in range(len(allP))])
    allN = np.vstack([Ns[id(p)] for p in prims]); sumN = np.zeros_like(allN); np.add.at(sumN, root, allN)
    cnt = np.bincount(root, minlength=len(allP))
    grouped = cnt[root] > 1
    acc = None
    nseam = int((cnt > 1).sum())
    # under-chin point from the head's nose tip
    HP = np.vstack([Ps[id(p)] for p in hp]); fr = HP[(HP[:, 1] > 1.66) & (HP[:, 1] < 1.80)]
    nose = fr[np.argmax(fr[:, 2])] if len(fr) else HP[np.argmax(HP[:, 2])]
    chin_front = HP[(HP[:, 1] > o.chy - 0.01) & (HP[:, 1] < o.chy + 0.02) & (np.abs(HP[:, 0] - nose[0]) < 0.02)]
    cz = (chin_front[:, 2].max() if len(chin_front) else nose[2] - 0.02) - 0.02
    C = np.array([nose[0], o.chy, cz]); u = np.array([0, 0.6, 0.4]); u /= np.linalg.norm(u)
    turned = 0
    for p, o_ in zip(prims, offs[:-1]):
        P, N = Ps[id(p)], Ns[id(p)]; out = N.copy(); sl = slice(o_, o_ + len(P))
        g_ = grouped[sl]; out[g_] = sumN[root[sl][g_]]
        out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)
        if p in hp:
            d = np.linalg.norm(P - C, axis=1); w = np.exp(-0.5 * (d / o.s) ** 2)
            f = np.clip(-out[:, 1] / 0.6, 0, 1); f = f * f * (3 - 2 * f); w = w * f
            out = out + o.k * w[:, None] * u[None]; out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)
            turned += int((w > 0.05).sum())
            if o.nose_s > 0:                          # nose underside: the same smooth turn round a point 1 cm below and behind the tip
                Cn = nose + np.array([0, -0.012, -0.012]); dn = np.linalg.norm(P - Cn, axis=1)
                wn = np.exp(-0.5 * (dn / o.nose_s) ** 2); fn = np.clip(-out[:, 1] / 0.6, 0, 1); wn = wn * fn * fn * (3 - 2 * fn)
                out = out + o.nose_k * wn[:, None] * u[None]; out /= np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)
                turned += int((wn > 0.05).sum())
        if np.abs(out - N).max() > 1e-6:
            p.attributes.NORMAL = add(out)
    rep.append(f'{mesh.name}: seam groups {nseam}, under-chin turned {turned}')
while len(blob) % 4: blob.append(0)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(o.out)
print('NORMALSEAMS', '; '.join(rep))
