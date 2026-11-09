#!/usr/bin/env python3
"""r2 skull placement on an existing asm npz (asm3 / asm4), equal to assemble_lk.py's new defaults (scale 0.82, top 1.545, y +0.017) applied
to the r1 skull (0.88, top 1.565, y 0): the cranium sits inside the crown ring under the new crown cap; no other vertex moves, so the frozen
body atlas (indices into asm3) stays valid. Args: <in npz> <out npz>"""
import sys, numpy as np
D = dict(np.load(sys.argv[1])); co = D['co'].copy(); names = [str(x) for x in D['names']]
v = D['comp'] == names.index('skull'); k = 0.82 / 0.88
p = co[v]; co[v] = np.c_[p[:, 0] * k, p[:, 1] * k + 0.017, (p[:, 2] - 1.565) * k + 1.545]
print('skull', co[v].min(0).round(3), co[v].max(0).round(3))
D['co'] = co; np.savez(sys.argv[2], **D)
