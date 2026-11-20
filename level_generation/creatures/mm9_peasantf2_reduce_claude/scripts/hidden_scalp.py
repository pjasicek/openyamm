#!/usr/bin/env python3
"""Head-part faces hidden under the hair cap or braid: every one of 7 rays from the face (centroid and 6 tilted by 35 deg
round the normal) hits a hair face within 4 cm, and the face is MARGIN away from any face that is not hidden.
Writes work/hidden_scalp.npy (bool per GLB face). Usage: hidden_scalp.py"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402
from scipy.spatial import cKDTree
import os
MARGIN = float(os.environ.get('MARGIN', '0.012'))
doc, b = g.read(HERE / 'before' / 'mm9_peasantf2.glb'); node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantF2' and 'mesh' in n)
pr = g.prims(doc, b, node['mesh']); TRI = np.concatenate([p['POSITION'].astype(float)[p['T']] for p in pr])
L = np.load(HERE / 'work' / 'glb_parts.npz'); names = list(L['names']); part, inner, mat = L['part'], L['inner'], L['mat']
head = (mat == 1) & (part == names.index('head')) & ~inner
hair = (mat == 1) & (part == names.index('hair'))
H = TRI[hair]; A = H[:, 0]; E1 = H[:, 1] - A; E2 = H[:, 2] - A


def hits(o, d, maxt=0.04):
    pv = np.cross(d, E2); det = (E1 * pv).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); tv = o - A; u = (tv * pv).sum(1) * inv
    qv = np.cross(tv, E1); v = (qv @ d) * inv if False else (qv * d).sum(1) * inv; t = (qv * E2).sum(1) * inv
    return bool((ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-5) & (t < maxt)).any())


idx = np.flatnonzero(head); hid = np.zeros(len(TRI), bool)
for f in idx:
    p = TRI[f]; c = p.mean(0); n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n) + 1e-20
    a = np.cross(n, [0, 1, 0] if abs(n[1]) < .9 else [1, 0, 0]); a /= np.linalg.norm(a); bb = np.cross(n, a)
    dirs = [n] + [np.cos(.61) * n + np.sin(.61) * (np.cos(t) * a + np.sin(t) * bb) for t in np.arange(6) * np.pi / 3]
    hid[f] = all(hits(c, d) for d in dirs)
vis = head & ~hid
d, _ = cKDTree(TRI[vis].reshape(-1, 3)).query(TRI[hid].reshape(-1, 3))
core = np.zeros(len(TRI), bool); core[np.flatnonzero(hid)] = d.reshape(-1, 3).min(1) > MARGIN
np.save(HERE / 'work' / 'hidden_scalp.npy', core)
print('HEAD faces', int(head.sum()), 'hidden', int(hid.sum()), 'hidden beyond margin', int(core.sum()))
