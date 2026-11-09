#!/usr/bin/env python3
"""m536 face labels for decimate_tex.py (REA_GROUPS): 0 = head (protect flag; the free part, which takes the rest of
the ladder budget), 1 = finger-dominated faces, 2 = hand-dominated faces, 3 = torso, arms and neck (already cut to
81 % by the creature build) -> work/groups_m536.npy."""
import collections
import numpy as np
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); names = [str(n) for n in g['names']]
dom = g['W'].argmax(1)
fd = np.array([collections.Counter(dom[t]).most_common(1)[0][0] for t in d['faces']])
lab = np.where(d['protect'] > .5, 0, 3)
lab[[('Finger' in names[i]) for i in fd]] = 1
lab[[names[i].endswith('_Hand') for i in fd]] = 2
np.save('work/groups_m536.npy', lab); print('GROUPS fingers', int((lab == 1).sum()), 'hands', int((lab == 2).sum()), 'head', int((lab == 0).sum()), 'body', int((lab == 3).sum()))
