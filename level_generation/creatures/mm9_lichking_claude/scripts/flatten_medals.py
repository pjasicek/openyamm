"""Medallions as low reliefs, not domes (Meshy's read as breasts): each medallion piece is squashed along its outward direction to FLAT of its depth,
about the torso surface under it (2026-10-31: about its innermost plane sank the chest medallions). Pairs stay mirror images. Args: <in npz> <out npz>"""
import sys, numpy as np
IN, OUT = sys.argv[1:3]; FLAT = 0.42
D = dict(np.load(IN)); co = D['co'].copy(); comp = D['comp']; names = [str(x) for x in D['names']]
for nm in ('medal', 'medalsF', 'medalsB', 'kneemed'):
    k = names.index(nm); idx = np.where(comp == k)[0]
    for side in ((-1, 1) if nm != 'medal' else (0,)):
        sel = idx if side == 0 else idx[np.sign(co[idx, 0]) == side]
        p = co[sel]; c = p.mean(0)
        if nm == 'kneemed': ctr = np.array([np.sign(c[0]) * 0.15, -0.03, c[2]])
        else: ctr = np.array([0.0, 0.0, c[2]])
        n = c - ctr; n[2] = 0; n /= np.linalg.norm(n)
        d = (p - c) @ n
        # base = the torso's outer surface on the medallion's line (outermost torso point within 3 cm of it); squash only what stands proud of it
        tv = co[comp == names.index('boots' if nm == 'kneemed' else 'torso')]; rel = tv - c; lat = np.linalg.norm(rel - np.outer(rel @ n, n), axis=1)
        near = (lat < 0.03) & (np.abs(rel @ n) < 0.08)
        base = float((rel[near] @ n).max()) if near.any() else d.min()
        proud = np.maximum(d - base, 0)
        p = p - np.outer(proud * (1 - FLAT), n)
        print('   base', round(base, 3), 'proud before', round(float(proud.max()), 3))
        co[sel] = p
        print(nm, side, 'depth', round(float(np.ptp(d)), 3), '->', round(float(np.ptp(d)) * FLAT, 3))
D['co'] = co; np.savez(OUT, **D)
