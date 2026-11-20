#!/usr/bin/env python3
"""Keep sets and region groups of the Lizardman Peasant rest mesh (work/mesh_in.npz, work/groups.npz):
hand = hand + digit + thumb weights > 0.5 (both four-digit hands), head = faces in the head texture set (u > 0.5077 of
the merged 2080x1024 atlas), foot = toe faces (LeftToeBase/RightToeBase + Foot weights > 0.5 below 8 cm).
Writes work/set_<name>.npy (bool per face) and prints counts."""
import numpy as np
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
f, v = d['faces'], d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
col = lambda pred: W[:, [i for i, n in enumerate(names) if pred(n)]].sum(1)
fm = lambda a: a[f].mean(1)
hand = fm(col(lambda n: 'Hand' in n or 'Digit' in n or 'Thumb' in n)) > .5
head = uv[:, :, 0].mean(1) > 1056 / 2080
c = v[f].mean(1)
foot = (fm(col(lambda n: 'Foot' in n or 'ToeBase' in n)) > .5) & (c[:, 2] < .08)
small = np.load('work/keep_small.npy')
for k, s in [('hand', hand), ('head', head), ('foot', foot), ('small', small)]:
    np.save(f'work/set_{k}.npy', s); print(k, int(s.sum()))
