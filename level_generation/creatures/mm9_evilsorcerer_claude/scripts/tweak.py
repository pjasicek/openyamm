#!/usr/bin/env python3
"""Small moves after the paint (no UV change): the hip flaps pulled in towards the thigh, or the hanging hand of MM9's stand rests in them. asm2 -> asm3, uv_v1 co updated through orig (uv_v1b.npz). Project folder."""
import numpy as np
D = dict(np.load('work/asm2.npz')); co = D['co'].copy(); comp = D['comp']; names = [str(x) for x in D['names']]
for nm in ('flapF', 'flapB'):
    m = comp == names.index(nm)
    x = np.abs(co[m, 0]); s = np.sign(co[m, 0]); z = co[m, 2]
    t = np.clip((1.16 - z) / 0.12, 0, 1)
    co[m, 0] = s * (0.115 + (x - 0.115) * (1 - 0.30 * t))
# the back panel's top tucks under the belt
m = comp == names.index('panelB'); z = co[m, 2]; t = np.clip((z - 1.0) / 0.14, 0, 1); t = t * t * (3 - 2 * t)
co[m, 1] -= 0.045 * t
D['co'] = co; np.savez('work/asm3.npz', **D)
U = dict(np.load('work/uv_v1.npz')); U['co'] = co[U['orig']]; np.savez('work/uv_v1b.npz', **U)
print('TWEAK', co[comp == names.index('flapB')][:, 0].max())
