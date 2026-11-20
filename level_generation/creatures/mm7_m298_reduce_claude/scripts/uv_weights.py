#!/usr/bin/env python3
"""Skin weights for decimated meshes through the preserved UVs (REA_WEIGHTS=component in reduce_ladder.py reads the
output). MM8 Nightmare: its slime lumps interpenetrate and its rest pose differs from the bind pose, so a nearest-face
transfer took weights from a neighbouring lump and new vertices flew off in every pose. The texture-aware collapse
keeps each vertex's UV on its own chart, so the source triangle containing that UV (barycentric weights) is the
surface the vertex came from. A vertex whose UV hit lies over 1 cm away in 3D (or misses every triangle) falls back to
the nearest source vertex with a similar normal. Source vertices keep their weights exactly.
MM7 Ooze: the pod and globule UVs lie on a disc of the blob's underside island (they have no texels of their own), so
a UV hit is searched only among source faces of the vertex's own region (REA_GROUPS / REA_GROUP_RATIOS, as given to
decimate_tex.py): a pod vertex never takes underside lump weights.
Usage: uv_weights.py <ratio,...>  (work/mesh_in.npz, work/src_weights.npz, work/mesh_r<NN>.npz -> work/weights_r<NN>.npz)"""
import sys
import numpy as np
from scipy.spatial import cKDTree

s = np.load('work/mesh_in.npz'); sw = np.load('work/src_weights.npz'); W = sw['weights']
sv, sf = s['verts'], s['faces']; suv = s['wuv'].reshape(-1, 3, 2)
import os
sg = np.load(os.environ['REA_GROUPS']) if os.environ.get('REA_GROUPS') else np.zeros(len(sf), int)
gkeys = {int(kv.split(':')[0]) for kv in os.environ.get('REA_GROUP_RATIOS', '').split(',') if kv}
src_label = np.where(np.isin(sg, list(gkeys)), sg, 0)  # decimate_tex labels: 0 = the free part
if os.environ.get('REA_KEEP_FACES'):  # kept faces keep their source vertices (exact weights)
    src_label[np.load(os.environ['REA_KEEP_FACES'])] = -1
utrees = {L: (np.flatnonzero(src_label == L), cKDTree(suv[src_label == L].mean(1))) for L in np.unique(src_label) if L >= 0}
vtree = cKDTree(sv)


def vnormals(v, f):
    n = np.zeros_like(v); fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)


sn = vnormals(sv, sf)
for r in [float(x) for x in sys.argv[1].split(',')]:
    tag = int(r * 100); d = np.load(f'work/mesh_r{tag}.npz'); v, f = d['verts'], d['faces']
    cuv = d['wuv'].reshape(-1, 3, 2); cn = vnormals(v, f)
    first = np.full(len(v), -1); corner = np.repeat(np.arange(len(f)), 3); fv = f.reshape(-1)
    first[fv[::-1]] = np.arange(len(fv))[::-1]  # one wedge per vertex
    uv = cuv.reshape(-1, 2)[first]
    out = np.zeros((len(v), W.shape[1]), np.float32); hit = np.zeros(len(v), bool)
    flab = d['group']; vlab = np.full(len(v), -1)
    for k in range(3):
        sel = flab >= 0; vlab[f[sel, k]] = flab[sel]
    cand = np.zeros((len(v), 16), int)
    for L, (ids, t) in utrees.items():
        m = vlab == L
        if m.any():
            cand[m] = ids[t.query(uv[m], min(16, len(ids)))[1]]
    for i in range(len(v)):
        if vlab[i] < 0:
            continue
        for t in cand[i]:
            a, b, c = suv[t]; m = np.array([b - a, c - a]).T
            try:
                l1, l2 = np.linalg.solve(m, uv[i] - a)
            except np.linalg.LinAlgError:
                continue
            l0 = 1 - l1 - l2
            if min(l0, l1, l2) < -1e-4:
                continue
            bary = np.clip([l0, l1, l2], 0, 1); bary /= bary.sum()
            if np.linalg.norm(bary @ sv[sf[t]] - v[i]) > .01:
                continue
            out[i] = bary @ W[sf[t]]; hit[i] = True
            break
    miss = np.where(~hit & (vlab >= 0))[0]
    for L in np.unique(vlab[miss]):  # nearest source vertex of the same region with a similar normal
        mi = miss[vlab[miss] == L]; ids = np.unique(sf[src_label == L])
        dd, nn = cKDTree(sv[ids]).query(v[mi], 12); nn = ids[nn]
        ok = (sn[nn] * cn[mi][:, None]).sum(-1) > .3
        pick = np.where(ok.any(1), nn[np.arange(len(mi)), ok.argmax(1)], nn[:, 0])
        out[mi] = W[pick]
    sidx = d['src_index'] if 'src_index' in d.files else np.full(len(v), -1)
    out[sidx >= 0] = W[sidx[sidx >= 0]]
    np.savez(f'work/weights_r{tag}.npz', weights=out, names=sw['names'])
    print('UVWEIGHTS', tag, len(v), 'exact', int((sidx >= 0).sum()), 'uv hits', int(hit.sum()), 'fallback', len(miss))
