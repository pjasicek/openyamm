#!/usr/bin/env python3
"""Job 8 (user review 2026-11-04: "the arm part from elbow down has like transparent parts or like holes in the sleeve").
Cause: add_parts_pf4.py built each sleeve tube's rings in a local frame (axis a_, ref = a_ x Z). The upper rings (f <= 0: inside F1's short
sleeve down to the elbow) used the upper-arm axis -au, the forearm rings the forearm axis af; the two axes point opposite ways, so ref
flips and the upper rings' vertex order runs the other way round the arm (a mirror image). The upper five rings' faces were therefore
wound inward (a one-sided viewer culls them: the near wall vanishes and the far wall's inside shows, the "transparent" patches), and the
band from ring 4 (f = 0) to ring 5 (f = 0.11) was twisted, its triangles crossing through the tube (the jagged dark-green fragments).
Fix, positions only (UVs, faces and every other part unchanged): each upper ring's vertices are permuted round the ring into the forearm
rings' order (the permutation that makes the ring 4 -> 5 band shortest; it is a reflection j -> c - j), so every tube face faces out.
Args: <asm npz in> <asm npz out>"""
import sys
import numpy as np
A = dict(np.load(sys.argv[1], allow_pickle=True)); co = A['co'].copy(); comp = A['comp']; tri = A['tri']
names = [str(x) for x in A['names']]; ks = names.index('sleeve4'); par = A['f4_param']; side = A['f4_side']
MS = 12
for sgn in (1, -1):
    q = np.where((comp == ks) & (side == sgn))[0]
    base = q.min(); NR = 13
    ring = lambda i: base + i * MS + np.arange(MS)
    fr = [float(par[ring(i)[0], 0]) for i in range(NR)]
    assert all(abs(par[ring(i), 0] - fr[i]).max() < 1e-6 for i in range(NR)), 'ring layout'
    up = [i for i in range(NR) if fr[i] <= 1e-6]
    i5 = max(up) + 1
    best = None
    for c in range(MS):
        perm = (c - np.arange(MS)) % MS
        L = np.linalg.norm(co[ring(max(up))][perm] - co[ring(i5)], axis=1).sum()
        best = min(best, (L, c)) if best else (L, c)
    L0 = np.linalg.norm(co[ring(max(up))] - co[ring(i5)], axis=1).sum()
    perm = (best[1] - np.arange(MS)) % MS
    for i in up:
        r = ring(i); co[r] = A['co'][r][perm]
    print('SIDE', sgn, 'upper rings', up, 'f', [fr[i] for i in up], 'band 4-5 edge sum cm before', round(L0 * 100, 1), 'after',
          round(best[0] * 100, 1), 'c', best[1])
# check: every outer tube face faces away from its ring centre line
inner = A['f4_inner']; rim = A['f4_rim']
fsel = np.where((comp[tri[:, 0]] == ks) & ~inner & ~rim)[0]
bad = 0
for sgn in (1, -1):
    q = np.where((comp == ks) & (side == sgn))[0]; base = q.min()
    cen = np.array([co[base + i * MS: base + (i + 1) * MS].mean(0) for i in range(13)])
    fl = fsel[side[tri[fsel, 0]] == sgn]
    t = tri[fl]; n = np.cross(co[t[:, 1]] - co[t[:, 0]], co[t[:, 2]] - co[t[:, 0]])
    ri = ((t - base) // MS).clip(0, 12)
    c_ = cen[ri].mean(1); rel = co[t].mean(1) - c_
    bad += int(((n * rel).sum(1) < 0).sum())
print('OUTER tube faces facing in:', bad, 'of', len(fsel))
A['co'] = co; np.savez(sys.argv[2], **A)
