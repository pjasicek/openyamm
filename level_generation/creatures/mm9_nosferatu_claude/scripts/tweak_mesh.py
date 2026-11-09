#!/usr/bin/env python3
"""Vertex moves after the paint (no topology or UV change): the cuff narrower still, MM9's sleeve end is 20 cm across. Writes work/asm_final.npz, work/uv_final.npz; finish_nos.py and rebuild.sh read these."""
import numpy as np
S = np.array([0.211, -0.02, 1.487]); W = np.array([0.475, -0.101, 1.026]); a = (W - S) / np.linalg.norm(W - S)
def ss(x, a_, b):
    t = np.clip((x - a_) / (b - a_), 0, 1); return t * t * (3 - 2 * t)
for src, dst in (('work/asm_frozen.npz', 'work/asm_final.npz'), ('work/uv_v2.npz', 'work/uv_final.npz')):
    D = dict(np.load(src)); co = D['co'].copy(); comp = D['comp']; names = [str(x) for x in D['names']]
    m = np.isin(comp, [names.index('sleeves'), names.index('slining')])
    sg = np.sign(co[:, 0]); q = co * np.c_[sg, np.ones(len(co)), np.ones(len(co))]
    t = (q - S) @ a; c = S + t[:, None] * a; k = 1 - 0.28 * ss(t, 0.34, 0.60)
    n = c + (q - c) * k[:, None]
    co[m] = (n * np.c_[sg, np.ones(len(co)), np.ones(len(co))])[m]
    f = comp == names.index('feet'); z = co[:, 2]                    # the shin stubs end low, inside the hem at any stride
    co[f, 2] = np.where(z[f] > 0.15, 0.15 + (z[f] - 0.15) * 0.35, z[f])
    h = comp == names.index('head'); u = np.clip((1.625 - co[:, 2]) / 0.05, 0, 1)    # the neck stays inside the collar's V
    co[h, 0] *= (1 - 0.22 * u[h]); co[h, 1] = co[h, 1] + (-0.015 - co[h, 1]) * 0.22 * u[h] + 0.018 * u[h]
    D['co'] = co; np.savez(dst, **D)
print('TWEAK')
