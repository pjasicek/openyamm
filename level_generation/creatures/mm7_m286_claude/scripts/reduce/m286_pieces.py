#!/usr/bin/env python3
"""Per-face source shell of the m286 v2c rest mesh (work/mesh_in.npz) from work/source_pieces.npz (rig_v6 Body 'piece'
and 'garment', mapped by nearest rest position) -> work/pieces.npy (majority per face), work/garments.npy (per face),
work/piece_v.npy, work/garment_v.npy, work/soles.npy (hoof faces below 6 cm), work/headset.npy (head texture set:
merged-atlas u > 0.505), work/horns.npy (the fused horns: body-shell faces above the skull's sides, weights_fix.py rule).
v2 part map (step1_clean.py): 0 body shell (skin, head, horns, arms, hands, goat legs), 1 kilt, 12 front flap,
2 mane sheet, 3 nose ring, 4/5 wrist bands, 6 belt, 13 buckle, 7/8 ears, 9 forelock, 10/11 eyes, 14 snout piece,
19/20 brow tufts; garment 4 beads, 8 band spikes, 1 crown cards, 7 mane cards."""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; s = np.load('work/source_pieces.npz')
dist, i = cKDTree(s['co']).query(v)
pv, gv = s['piece'][i], s['garment'][i]
fp = np.array([np.bincount(x, minlength=100).argmax() for x in pv[f]])
fg = np.array([np.bincount(x, minlength=10).argmax() for x in gv[f]])
c = v[f].mean(1)
soles = (fp == 0) & (v[f][..., 2].max(1) < 0.06)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); headset = u > 0.505
sk = v[(pv == 0) & (np.abs(v[:, 0]) < 0.04), 2].max()
hv = (pv == 0) & ((((v[:, 2] > sk - 0.10) & (np.abs(v[:, 0]) > 0.125)) | (v[:, 2] > sk + 0.025)))
horns = (fp == 0) & hv[f].all(1)
np.save('work/pieces.npy', fp); np.save('work/garments.npy', fg); np.save('work/piece_v.npy', pv); np.save('work/garment_v.npy', gv)
np.save('work/soles.npy', soles); np.save('work/headset.npy', headset); np.save('work/horns.npy', horns)
print('MAP max dist mm', round(float(dist.max()) * 1000, 4), 'mixed faces', int((pv[f] != fp[:, None]).any(1).sum()),
      'soles', int(soles.sum()), 'headset', int(headset.sum()), 'horns', int(horns.sum()), 'skull top', round(float(sk), 3))
for p in sorted(set(fp.tolist())):
    m = fp == p
    if m.sum() > 60:
        print(f'  piece {p:2d} faces {int(m.sum()):5d} centre {np.round(c[m].mean(0), 3)}')
print('  small pieces (<= 60 faces):', int(sum((fp == p).sum() for p in set(fp.tolist()) if (fp == p).sum() <= 60)))
