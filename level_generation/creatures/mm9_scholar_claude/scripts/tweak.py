#!/usr/bin/env python3
"""Small moves on the frozen mesh (UVs unchanged): the waist narrowed towards MM9's narrow, deep body (MM9's stand rests the hands where Meshy's body was 12 cm wider), the shins shortened to the robe's hem. asm1 -> asm2, uv_tex keeps its UVs. Project folder."""
import numpy as np
A = dict(np.load('work/asm1.npz')); co = A['co'].copy(); names = [str(x) for x in A['names']]; comp = A['comp']
def ss(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
K = float(__import__('os').environ.get('WAIST', '0.80'))
w = ss(co[:, 2], -0.45, 0.02) * (1 - ss(co[:, 2], 0.24, 0.40))
body = np.isin(comp, [names.index(n) for n in ('robe', 'belt')])
near = np.abs(co[:, 0]) < 0.30          # not the sleeves
fall = 1 - ss(np.abs(co[:, 0]), 0.24, 0.30)
co[:, 0] = np.where(body & near, co[:, 0] * (1 - (1 - K) * w * fall), co[:, 0])
sh = comp == names.index('shins'); top = co[sh, 2].max()
co[sh, 2] = np.where(co[sh, 2] > -0.70, -0.70 + (co[sh, 2] + 0.70) * 0.35, co[sh, 2])
print('TWEAK waist', K, 'shin top', co[sh, 2].max())
# belt down to MM9's waist (our belt sat 7 cm over MM9's and over the chains' bases; the hands of the clips meet it there): robe warped by height, rope moved
Zb0, Zb1 = 0.19, 0.125
rob = comp == names.index('robe')
z = co[:, 2]
zn = np.interp(z, [-1.0, -0.30, Zb0, 0.34, 1.0], [-1.0, -0.30, Zb1, 0.34, 1.0])
near2 = np.abs(co[:, 0]) < 0.30
co[:, 2] = np.where(rob & near2, z + (zn - z) * fall, z)
rope = np.isin(comp, [names.index(n) for n in ('belt', 'cords', 'knots')])
co[rope, 2] -= Zb0 - Zb1
# cords apart, as MM9's (0.05 from the middle at the tips; ours 0.03, the knots touched)
cc = np.isin(comp, [names.index(n) for n in ('cords', 'knots')])
co[cc, 0] += np.sign(co[cc, 0]) * 0.024 * ss(co[cc, 2], Zb1 - 0.02, Zb1 - 0.3)
# sleeves slimmer between the shoulder and the cuff: bent, the solid sleeve read as a bodybuilder's arm
sh_, ax = A['sh'], A['ax']
for s_ in (1, -1):
    a = ax * [s_, 1, 1]; o = sh_ * [s_, 1, 1]; t = (co - o) @ a; p = co - o - t[:, None] * a
    m = rob & (co[:, 0] * s_ > 0.2) & (t > -0.12) & (np.linalg.norm(p, axis=1) < 0.15)
    k = 1 - float(__import__('os').environ.get('SLV', '0.20')) * ss(t, -0.05, 0.10) * (1 - ss(t, 0.28, 0.44))
    co[m] = (o + t[:, None] * a + p * k[:, None])[m]
A['co'] = co; np.savez('work/asm2.npz', **A)
U = dict(np.load('work/uv_tex.npz')); U['co'] = co[U['orig']] if len(U['orig']) else U['co']
np.savez('work/uv_tex.npz', **U)
