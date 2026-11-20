#!/usr/bin/env python3
"""Per connected piece of the listed parts: reverse the piece's triangles when most of its face normals point toward the piece's centroid
(inward). For tubes (the necklace cord) the centroid is replaced by the nearest point of the piece's principal axis. Args: <in> <out> <parts,...>"""
import sys
import numpy as np
D = dict(np.load(sys.argv[1])); co, t, comp = D['co'], D['tri'].copy(), D['comp']; names = [str(x) for x in D['names']]
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
for part in sys.argv[3].split(','):
    fi = np.where(comp[t[:, 0]] == names.index(part))[0]; par = {}
    def fd(x):
        while par.setdefault(x, x) != x: x = par[x]
        return x
    for f in fi:
        a = fd(inv[t[f, 0]]); par[fd(inv[t[f, 1]])] = a; par[fd(inv[t[f, 2]])] = a
    r = np.array([fd(inv[t[f, 0]]) for f in fi]); nf = 0
    for rr in np.unique(r):
        ff = fi[r == rr]; c = co[t[ff]].mean(1); fn = np.cross(co[t[ff, 1]] - co[t[ff, 0]], co[t[ff, 2]] - co[t[ff, 0]])
        cc = c.mean(0); ax = np.linalg.svd(c - cc)[2][0]; foot = cc + np.outer((c - cc) @ ax, ax)
        if np.mean(np.sum(fn * (c - foot), 1) > 0) < 0.5: t[ff] = t[ff][:, ::-1]; nf += 1
    print('ORIENT', part, 'pieces', len(np.unique(r)), 'flipped', nf)
D['tri'] = t; np.savez(sys.argv[2], **D)
