#!/usr/bin/env python3
"""Relaxed eyes in geometry (orchestrator review 2026-11-02: large staring eyes, whites showing, heavy lower-lid bags with pale steps), after
mm9_wyrde_claude/scripts/tweak_wy.py: the lid skin round each eyeball (F1's head: ball centre +-2.88 / -9.53 / 68.39 cm asm, r 1.18 cm) is
rotated about the eye's horizontal axis like a closing lid: the upper lid down UPDEG, the lower lid up LODEG, full within 1.5 mm of the ball,
fading out by 8 mm (brow and cheek stay) and toward the corners; the eyeball pieces and part seams do not move; every moved vertex stays
0.6 mm outside the ball. The lower lid's skin below the rotation (the pale steps of F1's lid shelf) is Laplacian-smoothed (at most 1.5 mm).
Positions only (UVs unchanged), every row of an asm vertex together. Args: <uv_tex2 npz in> <out npz>"""
import sys, os
import numpy as np
U = dict(np.load(sys.argv[1])); co, tri, comp, orig = U['co'].copy(), U['tri'], U['comp'], U['orig']; names = [str(x) for x in U['names']]
kh = names.index('head')
UPDEG, LODEG = float(os.environ.get('UPDEG', '10')), float(os.environ.get('LODEG', '6'))
EC = np.array([0.0288, -0.0953, 0.6839]); ER = 0.0118
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
cnt = np.zeros(inv.max() + 1, int); np.add.at(cnt, inv, 1)
# positions used by other parts (seams) stay; eyeball pieces (small welded pieces) stay
hf = np.where(comp[tri[:, 0]] == kh)[0]; par = np.arange(inv.max() + 1)
def fnd(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in tri[hf]:
    r = fnd(inv[t[0]]); par[fnd(inv[t[1]])] = r; par[fnd(inv[t[2]])] = r
roots = np.array([fnd(i) for i in range(len(par))]); rc = np.bincount(roots[inv[np.unique(tri[hf])]], minlength=len(par))
ball = (rc[roots[inv]] < 600) & (comp == kh)
other = np.zeros(inv.max() + 1, bool); other[inv[comp != kh]] = True
mov = (comp == kh) & ~ball & ~other[inv]
P = np.zeros((inv.max() + 1, 3)); P[inv] = co; isM = np.zeros(len(P), bool); isM[inv[mov]] = True
moved = 0
for sx in (1, -1):
    c = EC * [sx, 1, 1]; q = P - c; d = np.linalg.norm(q, axis=1)
    cand = isM & (d < ER + 0.008) & (np.abs(d - ER) > 0.0003) & (q[:, 1] < 0.003)
    phi = np.arctan2(q[:, 2], -q[:, 1]); th = np.arctan2(q[:, 0] * sx, -q[:, 1])
    w = np.clip((ER + 0.008 - d) / 0.0065, 0, 1) * np.clip(np.cos(th) ** 2, 0, 1)
    up = np.clip((np.degrees(phi) + 5) / 15, 0, 1); lo = np.clip((-10 - np.degrees(phi)) / 15, 0, 1)
    ang = np.radians(-UPDEG * up + LODEG * lo) * w
    i = np.where(cand & (np.abs(ang) > 1e-5))[0]
    yz = q[i][:, [1, 2]]; ca, sa = np.cos(ang[i]), np.sin(ang[i])
    f, u = -yz[:, 0], yz[:, 1]; f2 = f * ca - u * sa; u2 = f * sa + u * ca
    newp = c + np.c_[q[i, 0], -f2, u2]
    dn = np.linalg.norm(newp - c, axis=1); push = dn < ER + 0.0006
    newp[push] = c + (newp[push] - c) / dn[push, None] * (ER + 0.0006)
    P[i] = newp; moved += len(i)
# the lower lid's shelf below the eye (pale steps): light Laplacian smoothing, at most 1.5 mm
T = inv[tri[hf]]; e = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
P0 = P.copy(); zone = np.zeros(len(P), bool)
for sx in (1, -1):
    c = EC * [sx, 1, 1]; q = P0 - c; d = np.linalg.norm(q, axis=1)
    zone |= isM & (d > ER + 0.0008) & (d < ER + 0.010) & (q[:, 2] < -0.003) & (q[:, 1] < 0.0)
for _ in range(6):
    acc = np.zeros_like(P); dg = np.zeros(len(P)); np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(dg, e[:, 0], 1); np.add.at(dg, e[:, 1], 1)
    L = acc / np.maximum(dg, 1)[:, None]; P[zone] = P[zone] + 0.5 * (L[zone] - P[zone])
    dd = P - P0; n = np.linalg.norm(dd, axis=1, keepdims=True); P = np.where(zone[:, None], P0 + dd * np.minimum(1, 0.0015 / np.maximum(n, 1e-12)), P)
for sx in (1, -1):
    c = EC * [sx, 1, 1]; dn = np.linalg.norm(P - c, axis=1); push = zone & (dn < ER + 0.0006)
    P[push] = c + (P[push] - c) / dn[push, None] * (ER + 0.0006)
co[mov] = P[inv[mov]]
U['co'] = co; np.savez(sys.argv[2], **U)
print('EYELIDS rotated', moved, 'positions, upper', UPDEG, 'lower', LODEG, '; lower-lid shelf smoothed', int(zone.sum()))
