#!/usr/bin/env python3
"""Plainer upper sleeves (orchestrator review 2026-11-02: MM9's F4 has plain fitted long sleeves; ours kept F1's puffed short sleeve over
the new sleeve tube). Positions only, after the paint (UVs unchanged; F1's weights unchanged): every dress vertex of the upper sleeve
(beyond 4 cm out from the shoulder joint along the upper arm) moves radially toward the arm axis, keeping KEEP of its distance beyond an
inner bound (the arm stub and the sleeve tube under it at that point + 5 mm), eased in over 4 cm from the shoulder. Rows of the same asm
vertex move together. Args: <uv_tex2 npz in> <out npz> <rig json> [KEEP]"""
import sys, json
import numpy as np
U = dict(np.load(sys.argv[1])); RJ = json.load(open(sys.argv[3])); KEEP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.35
co, comp, orig = U['co'].copy(), U['comp'], U['orig']; names = [str(x) for x in U['names']]
J = {k: np.array(v) for k, v in RJ['mm9'].items()}
kd, ka, ks = names.index('dress'), names.index('hands'), names.index('sleeve4')
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
moved = 0
for sgn in (1, -1):
    S_ = J['FHP R UpperArm'] * [sgn, 1, 1]; E_ = J['FHP R Forearm'] * [sgn, 1, 1]; L = np.linalg.norm(E_ - S_); a = (E_ - S_) / L
    def tr(P):
        q = P - S_; t = q @ a; r = np.linalg.norm(q - np.outer(t, a), axis=1); return t, r
    inner = np.where(np.isin(comp, [ka, ks]) & (co[:, 0] * sgn > 0.10))[0]; ti, ri = tr(co[inner])
    dv = np.where((comp == kd) & (co[:, 0] * sgn > 0.10))[0]; td, rd = tr(co[dv])
    sel = (td > 0.02) & (td < L * 1.05) & (rd < 0.12)
    for k in np.where(sel)[0]:
        m = np.abs(ti - td[k]) < 0.015
        if not m.any(): continue
        rin = ri[m].max() + 0.005
        if rd[k] <= rin: continue
        w = ss(td[k], 0.04, 0.08)
        rn = rd[k] - (rd[k] - rin) * (1 - KEEP) * w
        q = co[dv[k]] - S_; ax = (q @ a) * a; rad = q - ax
        co[dv[k]] = S_ + ax + rad / max(np.linalg.norm(rad), 1e-9) * rn; moved += 1
# rows of one asm vertex: their mean
grp = {}
for i in range(len(co)): grp.setdefault(int(orig[i]), []).append(i)
for o, rows in grp.items():
    if len(rows) > 1: co[rows] = co[rows].mean(0)
U['co'] = co; np.savez(sys.argv[2], **U); print('PUFF dress rows moved', moved)
