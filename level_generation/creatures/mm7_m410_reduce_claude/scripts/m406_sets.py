#!/usr/bin/env python3
"""Keep set and region groups for the m406 Swordsman ladder (work/pieces.npy, soles.npy, visible_head.npy,
groups.npz).
Kept exactly: the helmet rim (M406_RIM_H above its lowest edge), both gauntlets (hands and fingers; the sword grip is fitted), every face touching a vertex with hand +
finger weight > 0.3 (the vambrace ends beside the gauntlets), the eyes, the boot soles (faces below 6 cm), the helmet
spike (faces above 1.585 m) and the face features: patches around both eyes, the nose and the mouth/beard front
(M406_FEATURE_R, default 0.022 m; M406_KEEP_FACE=1 keeps the whole visible face front instead).
Groups (decimated on their own): 1 face front (visible head-piece faces in front of y = -0.035), 2 visible rest of the
head piece (ears, jaw sides, under the chin), 3 hidden head skin (scalp under the helmet, neck under the coif and
collar: no view from above -0.25 sees them), 4 helmet dome, 5 mail coif, 6 knee discs, 7 belt buckle, 8 arms,
9 legs; label 0 (torso with the tabard) takes the rest of the ladder budget.
Usage: m406_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); seen = np.load('work/visible_head.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 1; vis = head & (seen > 0)
front = vis & (c[:, 1] < -0.035)
R = float(os.environ.get('M406_FEATURE_R', '0.022'))
feat = np.zeros(len(f), bool)
for q in ((-0.034, -0.069, 1.459), (0.022, -0.070, 1.459), (-0.006, -0.100, 1.432), (-0.006, -0.088, 1.398),
          (-0.006, -0.080, 1.370)):  # eyes, nose, mouth, beard front (chin)
    feat |= head & (np.linalg.norm(v - np.array(q), axis=1) < R)[f].any(1)
# helmet rim (a closed shell): faces whose vertices lie within M406_RIM_H (default 0.025 m) of the helmet's lowest
# point in their azimuth sector about the helmet axis (a 60 % cut made the rolled rim wavy and lifted it off the coif
# at the back)
hv = np.unique(f[p == 2]); axis = v[hv, :2].mean(0)
az = np.arctan2(*(v[:, :2] - axis).T[::-1]); sector = ((az + np.pi) / (2 * np.pi) * 24).astype(int) % 24
low = np.full(24, 9.0)
np.minimum.at(low, sector[hv], v[hv, 2])
near = v[:, 2] < low[sector] + float(os.environ.get('M406_RIM_H', '0.025'))
rim = (p == 2) & near[f].all(1)
keep = rim | (p == 7) | (hand[f] > 0.3).any(1) | (p == 4) | soles | ((p == 2) & (c[:, 2] > 1.585)) | feat
if os.environ.get('M406_KEEP_FACE') == '1':
    keep |= front
extra = os.environ.get('M406_EXTRA_KEEP')  # e.g. a drift lock or patch set on top
if extra:
    keep |= np.load(extra)
groups = np.zeros(len(f), int)
groups[front] = 1; groups[vis & ~front] = 2; groups[head & ~vis] = 3
for lab, piece in ((4, 2), (5, 3), (6, 10), (7, 9), (8, 8), (9, 6)):
    groups[p == piece] = lab
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(features', int(feat.sum()), 'rim', int(rim.sum()), ')', {k: int((groups == k).sum()) for k in range(10)})
