#!/usr/bin/env python3
"""Per-face groups and keep masks for the m438 Zombie ladder (work/face_labels.npz from face_labels.py; faces -y,
1.75 m). Master pieces: 0 skin (head, torso, arms, right stump), 1 trousers, 2/3 feet, 4 rope belt, 5 rope ends,
6 stump bone shafts, 10-12 right-shin bone rods, 13 teeth, 14/15 eyes, 16 lathe right shin.
work/keep.npy (exact): left fingers (the fist round the held forearm), teeth, eyes, stump bone shafts, shin rods,
the lathe shin, rope and its ends (thin tubes), soles (faces below 6 cm), the headband (head-set faces of region R)
with one ring, the face front (head-set skin within FACE_R of the face centre, in front of the ears), the stump
(B_R_Forearm-dominated skin).
work/groups.npy: 1 trousers, 2 the rest of the head set (scalp, back of the head, ears, neck), 3 feet above the
soles, 4 left hand back/palm (B_L_Hand, not finger), 0 torso and arms (the ladder's remaining budget).
Usage: make_groups.py [FACE_R metres, default 0.075] [suffix]"""
import sys
import numpy as np
L = np.load('work/face_labels.npz', allow_pickle=True); d = np.load('work/mesh_in.npz'); f = d['faces']
sw = np.load('work/source_world.npy'); cen = sw[f].mean(1)
FACE_R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.075; suf = sys.argv[2] if len(sys.argv) > 2 else ''
P, dom = L['piece'], L['dom'].astype(str)
skin = P == 0; hs = skin & L['head']
eyes = np.isin(P, [14, 15]); fc = np.array([cen[eyes].mean(0)[0], cen[eyes].mean(0)[1], 1.60])


def ring(mask, n=1):
    for _ in range(n):
        vs = np.unique(f[mask]); mask = mask | np.isin(f, vs).any(1)
    return mask


face = hs & (np.linalg.norm(cen - fc, axis=1) < FACE_R) & (cen[:, 1] < fc[1] + 0.035)
band = ring(hs & (L['region'] > .5)) & hs
keep = ((L['finger'] > 0) | np.isin(P, [4, 5, 6, 10, 11, 12, 13, 14, 15, 16]) | (L['zmin'] < .06) | band | face
        | (skin & (dom == 'B_R_Forearm')))
g = np.zeros(len(f), int)
g[P == 1] = 1
g[hs] = 2
g[np.isin(P, [2, 3])] = 3
g[skin & (dom == 'B_L_Hand')] = 4
g[keep] = -1
np.save(f'work/keep{suf}.npy', keep); np.save(f'work/groups{suf}.npy', g)
print('KEEP', int(keep.sum()), {k: int(v.sum()) for k, v in dict(finger=L['finger'] > 0, face=face, band=band, soles=L['zmin'] < .06,
      stump=skin & (dom == 'B_R_Forearm'), rope=np.isin(P, [4, 5]), bones=np.isin(P, [6, 10, 11, 12, 16])).items()})
print('GROUPS', {k: int((g == k).sum()) for k in (0, 1, 2, 3, 4)}, 'face centre', fc.round(3).tolist())
