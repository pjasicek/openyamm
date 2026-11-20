#!/usr/bin/env python3
"""Wyrde geometry tweaks after the paint (positions only: UVs unchanged, the paint moves with the mesh).
1. Mantle back midline: the mirrored +x half meets itself at x = 0 in a V with a deep diamond pocket (Meshy's fold), shaded as a line
   down the back. Vertices within BAND of the midline on the back of the mantle are relaxed (Laplacian, falling off with |x|, at most CAP),
   midline vertices kept on x = 0; part seams (positions shared with another part) stay.
Writes <out asm npz> (rig and weights) and <out mesh npz> (the uv npz with co = tweaked asm co[orig]).
Args: <asm npz> <uv npz> <out asm npz> <out mesh npz>"""
import sys
import numpy as np
A, U, OA, OU = sys.argv[1:5]
S = dict(np.load(A)); co, tri, comp = S['co'].copy(), S['tri'], S['comp']; names = [str(x) for x in S['names']]
_k0 = np.round(co, 5); _u0, _i0, _c0 = np.unique(_k0, axis=0, return_inverse=True, return_counts=True); shared = _c0[_i0.ravel()] > 1
def relax(part, sel, w, passes, cap, keep_x0=True):
    global co
    k = names.index(part); t = tri[comp[tri[:, 0]] == k]
    e = np.unique(np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1), axis=0)
    P = co.copy(); mid = (comp == k) & (np.abs(co[:, 0]) < 1e-5)
    for _ in range(passes):
        acc = np.zeros_like(P); deg = np.zeros(len(P))
        np.add.at(acc, e[:, 0], P[e[:, 1]]); np.add.at(acc, e[:, 1], P[e[:, 0]]); np.add.at(deg, e[:, 0], 1); np.add.at(deg, e[:, 1], 1)
        Lp = acc / np.maximum(deg, 1)[:, None]
        P[sel] = P[sel] + ((Lp - P) * 0.5 * w[:, None])[sel]
        d = P - co; n = np.linalg.norm(d, axis=1); P = co + d * (np.minimum(n, cap) / np.maximum(n, 1e-12))[:, None]
        if keep_x0: P[mid, 0] = 0
    d = np.linalg.norm(P - co, axis=1); print('TWEAK', part, 'moved', int((d > 1e-5).sum()), 'max mm', round(float(d.max()) * 1000, 2)); co = P
BAND = 0.06
m = names.index('mantle')
sel = (comp == m) & (np.abs(co[:, 0]) < BAND) & (co[:, 1] > 0.0) & ~shared
relax('mantle', sel, np.clip(1 - np.abs(co[:, 0]) / BAND, 0, 1) ** 0.5, 30, 0.02)
# 2. Eyelids (review 2026-11-02: both women stared, white all round the iris): the lid skin round each eyeball is rotated about the eye's
#    horizontal axis like a closing lid: the upper lid down UPDEG, the lower lid up LODEG, full within 1.5 mm of the ball and fading out by
#    9 mm (the brow and cheek stay), fading toward the corners (cos of the azimuth); the eyeball itself and part seams do not move; every
#    moved vertex is kept 0.6 mm outside the ball.
import os
UPDEG, LODEG = float(os.environ.get('UPDEG', '9')), float(os.environ.get('LODEG', '5'))
EC = np.array([0.0226, -0.0943, 0.6803]); ER = 0.0143
hk = names.index('head'); moved = 0
for sx in (1, -1):
    c = EC * [sx, 1, 1]; q = co - c; d = np.linalg.norm(q, axis=1)
    cand = (comp == hk) & (d < ER + 0.009) & (np.abs(d - ER) > 0.0003) & (q[:, 1] < 0.003) & ~shared
    phi = np.arctan2(q[:, 2], -q[:, 1]); th = np.arctan2(q[:, 0] * sx, -q[:, 1])
    w = np.clip((ER + 0.009 - d) / 0.0075, 0, 1) * np.clip(np.cos(th) ** 2, 0, 1)
    up = np.clip((np.degrees(phi) + 5) / 15, 0, 1); lo = np.clip((-10 - np.degrees(phi)) / 15, 0, 1)
    ang = np.radians(-UPDEG * up + LODEG * lo) * w
    i = np.where(cand & (np.abs(ang) > 1e-5))[0]
    yz = q[i][:, [1, 2]]; ca, sa = np.cos(ang[i]), np.sin(ang[i])
    # rotation in the (forward = -y, up = z) plane: positive angle raises a point
    f, u = -yz[:, 0], yz[:, 1]; f2 = f * ca - u * sa; u2 = f * sa + u * ca
    newp = c + np.c_[q[i, 0], -f2, u2]
    dn = np.linalg.norm(newp - c, axis=1); push = dn < ER + 0.0006
    newp[push] = c + (newp[push] - c) / dn[push, None] * (ER + 0.0006)
    co[i] = newp; moved += len(i)
print('EYELIDS rotated', moved, 'vertices, upper', UPDEG, 'lower', LODEG)
# (3. r9-r14 relaxed the nose underside; r15: dropped, it erased the nostrils and the wings: Meshy's nose is kept)
# (r11 tried relaxing the mouth area: it pulled Meshy's mouth cavity forward and opened the mouth; dropped, the cavity is painted instead)
S['co'] = co; np.savez(OA, **S)
D = dict(np.load(U)); D['co'] = co[D['orig']]; np.savez(OU, **D); print('TWEAKED', OA, OU)
