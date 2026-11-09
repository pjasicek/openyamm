#!/usr/bin/env python3
"""Hand faces by local thickness: from each hand face centroid a ray goes inward (against the face normal) and the first hand face hit
gives the thickness. Fingers are thin (< THICK m: each finger keeps its full shape), palm and back of hand thick. Adds 'hthin' (bool)
and 'hthick_m' to work/labels.npz; 'hseg' from hand_labels.py is not used further (fist.json's chains are from before fist.py r5)."""
import os
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
d = np.load(HERE / 'work/mesh_in.npz'); L = dict(np.load(HERE / 'work/labels.npz')); V, F = d['verts'], d['faces']
TH = float(os.environ.get('THICK', .045))
hand = np.where(L['reg'] == 2)[0]
T = V[F[hand]]; c = T.mean(1); n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1)[:, None]
e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
th = np.full(len(hand), np.inf)
for i in range(len(hand)):
    o = c[i] - n[i] * 1e-4; dirv = -n[i]
    p = np.cross(dirv, e2); det = (e1 * p).sum(1); ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0); s = o - T[:, 0]; u = (s * p).sum(1) * inv
    q = np.cross(s, e1); v = (q @ dirv) * inv; t = (e2 * q).sum(1) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4); hit[i] = False
    if hit.any(): th[i] = t[hit].min()
thin = np.zeros(len(F), bool); thin[hand] = th < TH
tk = np.full(len(F), np.nan); tk[hand] = th
L['hthin'] = thin; L['hthick_m'] = tk
print('hand', len(hand), 'thin', int(thin.sum()), 'thickness p10/50/90', np.percentile(th[np.isfinite(th)], [10, 50, 90]).round(3), 'no hit', int((~np.isfinite(th)).sum()))
np.savez(HERE / 'work/labels.npz', **L)
