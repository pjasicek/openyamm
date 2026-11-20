#!/usr/bin/env python3
"""Fre (2026-11-04, viewer r2: a thin dark line along the hair edge over the forehead and cheeks): along the face opening the hair cap hugs
the skin 1.5 mm out, so its lining (2.5 mm inside the outer shell) lies inside the head and the rim strip joining them crosses the skin as a
visible line. Rim and lining faces whose columns hug the face (|alpha| on the opening side, f4_param) are dropped from the asm and from the
uv npz (rows matched by their asm vertex triple; every other face and the paid layout unchanged). Runs once after uv_fre.py.
Args: <asm in> <uv in> <asm out> <uv out>"""
import sys
import numpy as np
A = dict(np.load(sys.argv[1])); U = dict(np.load(sys.argv[2]))
co, tri, comp = A['co'], A['tri'], A['comp']; names = [str(x) for x in A['names']]; K4 = names.index('hood4')
par = A['f4_param']; inner, rim, twf = A['f4_inner'], A['f4_rim'], A['f4_twin_face']
fal = par[tri, 1].mean(1); cap = (comp[tri] == K4).all(1)
# the opening side: alpha in (-165, -15) as add_parts_fre.py's wopen > 0.5 (period-safe mean: all corners of a face are close in alpha)
a0 = par[tri[:, 0], 1]
opening = (a0 > -163) & (a0 < -17)
drop = cap & (inner | rim) & opening
keep = ~drop; newidx = -np.ones(len(tri), int); newidx[keep] = np.arange(keep.sum())
assert not drop[twf[twf >= 0]].any()
A['tri'] = tri[keep]
for k in ('f4_inner', 'f4_rim'): A[k] = A[k][keep]
A['f4_twin_face'] = np.where(twf[keep] >= 0, newidx[np.maximum(twf[keep], 0)], -1)
np.savez(sys.argv[3], **A)
keys = {tuple(sorted(t)) for t in tri[drop]}
ukeep = np.array([tuple(sorted(U['orig'][t])) not in keys for t in U['tri']])
U['tri'] = U['tri'][ukeep]; U['mat'] = U['mat'][ukeep]; U['inner'] = U['inner'][ukeep]
used = np.unique(U['tri']); remap = -np.ones(len(U['co']), int); remap[used] = np.arange(len(used))
for k in ('co', 'uv', 'orig', 'comp'): U[k] = U[k][used]
U['tri'] = remap[U['tri']]
np.savez(sys.argv[4], **U)
print('OPENLINING dropped', int(drop.sum()), '(rim', int((drop & rim).sum()), ', lining', int((drop & inner).sum()), ') uv faces dropped', int((~ukeep).sum()), 'tris', len(A['tri']))
