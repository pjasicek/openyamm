#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Cleric of the Sun (faces -y, no prop). After the weld: the main piece (head and face on the head atlas, arms,
open hands, robe top and sleeves), the gold sun mantle (yoke round the shoulders), the robe skirt, and small pieces:
nine crown rays, the neck/collar band, the teal stole (the tier region), eyes, belt medallion, two wrist bands.
Labels: 0 rest of the main piece (robe top, sleeves, arms), 1 face (head-atlas part of the main piece),
3 left hand, 4 right hand (B_*_Hand dominated faces of the main piece), 5 robe skirt, 6 gold mantle.
Kept exactly: pieces of up to 250 faces (crown rays: thin spikes; stole: painted stripes and the tier mask; eyes,
collar band, medallion, wrist bands) and the skirt hem band (faces below 12 cm)."""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); u = info['u']; dom = info['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
big = sorted([p for p in np.unique(pc) if sizes[p] > 250], key=lambda p: -sizes[p])
main = max(big, key=lambda p: (u[pc == p] > .505).sum())
skirt = min(big, key=lambda p: c[pc == p, 2].mean())
mantle = [p for p in big if p not in (main, skirt)][0]
g = np.zeros(len(f), int)
m = pc == main
g[m & (u > .505)] = 1
g[m & (dom == 'B_L_Hand')] = 3; g[m & (dom == 'B_R_Hand')] = 4
g[pc == skirt] = 5; g[pc == mantle] = 6
keep = (size <= 250) | ((pc == skirt) & (c[:, 2] < .12))
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in (0, 1, 3, 4, 5, 6)}, 'keep', int(keep.sum()))
