#!/usr/bin/env python3
"""Picked configuration i on top of m568_sets.py: group 3 = the front of the serpent bend (free faces with centroid
z 0.15-0.65 m, y < 0.05; the uniform maximum sat there in Dead), the torso (B_Pelvis/B_Spine* faces) kept exactly,
group 4 = the arms. Writes work/groups_b.npy, work/keep_i.npy, work/groups_i.npy."""
import numpy as np
d = np.load('work/mesh_in.npz'); gr = np.load('work/groups.npz'); W = gr['W']; names = list(gr['names']); f = d['faces']
g = np.load('work/groups_s.npy'); k = np.load('work/keep_s.npy'); c = d['verts'][f].mean(1)
free = (g == 0) & ~k
bend = free & (c[:, 2] > 0.15) & (c[:, 2] < 0.65) & (c[:, 1] < 0.05)
g[bend] = 3; np.save('work/groups_b.npy', g)
idx = lambda p: [i for i, n in enumerate(names) if p(n)]
fm = lambda a: a[f].mean(1)
torso = fm(W[:, idx(lambda n: n in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2'))].sum(1)) > .5
arm = fm(W[:, idx(lambda n: 'Arm' in n or 'Forearm' in n or 'Clavicle' in n)].sum(1)) > .5
free = (g == 0) & ~k
g[free & arm] = 4
np.save('work/keep_i.npy', k | (free & torso)); np.save('work/groups_i.npy', g)
print('BEND', int(bend.sum()), 'TORSO kept', int((free & torso).sum()), 'ARMS', int((free & arm).sum()))
