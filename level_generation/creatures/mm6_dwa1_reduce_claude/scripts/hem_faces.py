"""Hem bands of the dwarf's cloth: faces within two rings of an open boundary edge of the tunic/sleeve shells
(components with more than 80 faces outside the head set), excluding boundary loops above the belt line
(REA_HEM_ZMAX, default 0.95 m: the yoke edge and neck stay free). -> work/hem.npy"""
import os, numpy as np
from collections import Counter
d = np.load('work/mesh_in.npz'); V, F = d['verts'], d['faces']
comp = np.load('work/comp.npy'); hs = np.load('work/headset.npy'); small = np.bincount(comp)[comp] <= 80
ZMAX = float(os.environ.get('REA_HEM_ZMAX', '0.95'))
e = Counter(tuple(sorted((a, b))) for f in F for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])))
bv = np.zeros(len(V), bool)
for (a, b), n in e.items():
    if n == 1: bv[a] = bv[b] = True
band = bv[F].any(1) & ~hs & ~small & (V[F][:, :, 2].mean(1) < ZMAX)
for _ in range(1):
    vm = np.zeros(len(V), bool); vm[F[band].ravel()] = True; band = vm[F].any(1) & ~hs & ~small
np.save('work/hem.npy', band)
print('hem faces', int(band.sum()), {int(c): int((band & (comp == c)).sum()) for c in np.unique(comp[band])})
