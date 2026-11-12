#!/usr/bin/env python3
"""Follow-up 2 (2026-11-12): new weights (weights.py on the un-turned bodice) only where the bodice moved, the installed weights elsewhere,
so the face, neck, hands and skirt keep their installed skinning. Args: <new weights npz> <installed weights npz> <asm npz> <out npz> [z max]"""
import sys
import numpy as np
NEW, OLD, ASM, OUT = sys.argv[1:5]; ZMAX = float(sys.argv[5]) if len(sys.argv) > 5 else 0.47
a, b, A = np.load(NEW), np.load(OLD), np.load(ASM)
assert list(a['wnames']) == list(b['wnames'])
names = [str(x) for x in A['names']]
take = (A['comp'] == names.index('dress')) & (A['co'][:, 2] < ZMAX)
wj, ww = b['wj'].copy(), b['ww'].copy(); wj[take] = a['wj'][take]; ww[take] = a['ww'][take]
np.savez(OUT, wj=wj, ww=ww, wnames=a['wnames'])
print('WEIGHTS merged: new on', int(take.sum()), 'bodice vertices below z', ZMAX)
