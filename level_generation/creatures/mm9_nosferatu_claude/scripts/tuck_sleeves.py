#!/usr/bin/env python3
"""The sleeve from the shoulder to the elbow, redrawn on the same grid (no topology or UV change). Its top end stood 4.7 cm outside the yoke as an open ring, with a notch and a blocky puff below it
(user, 2026-10-31); MM9's sleeve is a straight tube from a square shoulder. Row 0 goes under the yoke corner, rows 1-5 loft to row 6 with a little fullness. The front near the shoulder stays behind the chest plate. Run after tweak_mesh.py and finish_nos.py;
keeps its input as work/*_pre_tuck.npz so a rerun starts from the same mesh."""
import os
import numpy as np
SHIFT = np.array([-0.058, 0.0, -0.022]); FULL = 0.016; LAST = 6
base = np.load('work/asm_pre_tuck.npz' if os.path.exists('work/asm_pre_tuck.npz') else 'work/asm_final.npz')
names = [str(x) for x in base['names']]; idx = np.where(base['comp'] == names.index('sleeves'))[0]; half = len(idx) // 2
moves = {}
for part, sign in ((idx[:half], 1), (idx[half:], -1)):
    assert (base['co'][part, 0] * sign > 0).all()
    X = base['co'][part].reshape(12, 22, 3); N = X.copy(); s = SHIFT * [sign, 1, 1]
    N[0] = X[0] + s
    for j in range(1, LAST):
        u = j / LAST; ring = N[0] * (1 - u) + X[LAST] * u; c = ring.mean(0); d = ring - c
        N[j] = ring + d / np.linalg.norm(d, axis=1, keepdims=True) * FULL * np.sin(np.pi * u)
    N[LAST] = 0.5 * X[LAST] + 0.25 * (N[LAST - 1] + X[LAST + 1])
    # the chest plate's slope carried outward: the sleeve's front stays behind it near the shoulder, else it lies on the chest as a flap (user, 2026-10-31)
    x = np.abs(N[:, :, 0]); plate = -0.102 + 0.75 * (x - 0.13) + 0.48 * (N[:, :, 2] - 1.5) + np.array([0.05, 0.045, 0.035, 0.03, 0.03, 0, 0, 0, 0, 0, 0, 0])[:, None]   # margin: the Standing pose rolls the shoulder forward
    push = np.maximum(plate - N[:, :, 1], 0.0) * np.array([1, 1, 1, 0.6, 0.3, 0, 0, 0, 0, 0, 0, 0])[:, None]
    N[:, :, 1] += push
    for j in range(5):
        N[j, :, 1] = 0.75 * N[j, :, 1] + 0.125 * (np.roll(N[j, :, 1], 1) + np.roll(N[j, :, 1], -1))
    for j in range(LAST + 1):
        for p, q in zip(X[j], N[j]):
            moves[tuple(np.round(p, 5))] = q - p
for nm in ('asm_final', 'uv_final', 'uv_tex'):
    src = f'work/{nm}_pre_tuck.npz'.replace('asm_final_pre', 'asm_pre')
    if not os.path.exists(src):
        os.replace(f'work/{nm}.npz', src)
    D = dict(np.load(src)); co = D['co'].copy(); n = [str(x) for x in D['names']]; hit = 0
    for i in np.where(D['comp'] == n.index('sleeves'))[0]:
        d = moves.get(tuple(np.round(co[i], 5)))
        if d is not None:
            co[i] += d; hit += 1
    D['co'] = co; np.savez(f'work/{nm}.npz', **D); print('TUCK', nm, hit)
