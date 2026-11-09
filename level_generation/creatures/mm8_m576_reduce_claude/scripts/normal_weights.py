#!/usr/bin/env python3
"""Skin weights for the new vertices of each decimated mesh (work/mesh_rNN.npz) from the nearest source surface point
whose face normal agrees with the vertex normal (dot > 0.2), interpolated barycentrically, 4 influences.
MM8 Naga: the tail coils touch in the rest pose, and nearest-vertex/nearest-face weights took the next coil's
Serpent bones (50-80 mm errors in Standing and Death at 85 %). Usage: normal_weights.py <ratio,...>
-> work/weights_rNN.npz (bone index into work/groups.npz names, weight; 4 per vertex)."""
import sys
import numpy as np
from scipy.spatial import cKDTree
s = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']
sv, sf = s['verts'], s['faces']
fn = np.cross(sv[sf[:, 1]] - sv[sf[:, 0]], sv[sf[:, 2]] - sv[sf[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
B = np.vstack([np.eye(3), np.random.default_rng(0).dirichlet((1, 1, 1), 30)])
pts = np.einsum('sk,fkc->fsc', B, sv[sf]).reshape(-1, 3)
pf = np.repeat(np.arange(len(sf)), len(B)); pb = np.tile(B, (len(sf), 1))
tree = cKDTree(pts)
for r in sys.argv[1].split(','):
    tag = int(float(r) * 100); c = np.load(f'work/mesh_r{tag}.npz'); cv, cf = c['verts'], c['faces']
    vn = np.zeros_like(cv); n = np.cross(cv[cf[:, 1]] - cv[cf[:, 0]], cv[cf[:, 2]] - cv[cf[:, 0]])
    for k in range(3):
        np.add.at(vn, cf[:, k], n)
    vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-12
    _, idx = tree.query(cv, 48)
    ok = np.einsum('vkc,vc->vk', fn[pf[idx]], vn) > .2
    first = np.where(ok.any(1), ok.argmax(1), 0); pick = idx[np.arange(len(cv)), first]
    w = np.einsum('vk,vkb->vb', pb[pick], W[sf[pf[pick]]])
    top = np.argsort(-w, 1)[:, :4]; tw = np.take_along_axis(w, top, 1); tw /= tw.sum(1, keepdims=True)
    np.savez(f'work/weights_r{tag}.npz', bones=top, weights=tw, face=pf[pick], bary=pb[pick])
    print('WEIGHTS', tag, len(cv), 'verts, no agreeing normal for', int((~ok.any(1)).sum()))
