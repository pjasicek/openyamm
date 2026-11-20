#!/usr/bin/env python3
"""Keep set and region groups for the m218 Elf Spearman ladder (work/pieces.npy, soles.npy, visible_head.npy,
groups.npz).
Kept exactly: both hands (the spear fists are solved), every face touching a vertex with hand + finger weight > 0.3
(bracer ends), eyes and mouth pieces, the crown leaves (thin leaf cards), belt, loincloth panels with their tabs, the
ponytail, every other small piece (tabs, necklace, pouch flap), the soles (faces below 6 cm), head skin within
M218_SOCKET_R (default 0.02 m) of the eye/mouth pieces (sockets and lips), and the face features: patches of
M218_FEATURE_R (default 0.022 m) around eyes, nose and mouth (M218_KEEP_FACE=1 keeps the whole visible face front).
Groups (decimated on their own): 1 face front (visible head skin in front of y = M218_FRONT_Y, below 1.64 m),
2 visible rest of the head skin (hair, ears, jaw sides, neck), 3 hidden head skin, 4 bracers, 5 back shaft, 6 pouch,
7 hidden eye/mouth faces (M218_EYE_HIDDEN=1);
label 0 (body skin) takes the rest of the ladder budget. M218_EXTRA_KEEP adds a bool .npy (patches, drift lock).
Usage: m218_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); seen = np.load('work/visible_head.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 1; vis = head & (seen > 0)
front = vis & (c[:, 1] < float(os.environ.get('M218_FRONT_Y', '-0.03'))) & (c[:, 2] < 1.64)
fv = np.unique(f[p == 4]); feat_v = v[fv]
socket = head & (cKDTree(feat_v).query(c)[0] < float(os.environ.get('M218_SOCKET_R', '0.02')))
# feature centres: the two eyes, the nose tip (front-most head-skin vertex near 1.53 m) and the mouth
eyes = [v[np.unique(f[(p == 4) & (c[:, 2] > 1.54) & (np.sign(c[:, 0] + 0.004) == s)])].mean(0) for s in (-1, 1)]
hv = np.unique(f[head]); band = hv[(v[hv, 2] > 1.50) & (v[hv, 2] < 1.56) & (np.abs(v[hv, 0]) < 0.02)]
nose = v[band[np.argmin(v[band, 1])]]
mouth = v[np.unique(f[(p == 4) & (c[:, 2] < 1.53)])].mean(0)
R = float(os.environ.get('M218_FEATURE_R', '0.022'))
feat = np.zeros(len(f), bool)
for q in (*eyes, nose, mouth):
    feat |= head & (np.linalg.norm(v - q, axis=1) < R)[f].any(1)
keep = (np.isin(p, [3, 4, 5, 7, 8, 11, 12]) | (hand[f] > 0.3).any(1) | soles | socket | feat)
if os.environ.get('M218_KEEP_FACE') == '1':
    keep |= front
extra = os.environ.get('M218_EXTRA_KEEP')
if extra:
    keep |= np.load(extra)
groups = np.zeros(len(f), int)
groups[front] = 1; groups[vis & ~front] = 2; groups[head & ~vis] = 3
for lab, piece in ((4, 6), (5, 9), (6, 10)):
    groups[p == piece] = lab
# M218_EYE_HIDDEN=1: the never-visible faces of the eye and mouth pieces (backs of the eyeballs, inside of the mouth;
# work/visible_all.npy, 2-pixel views) leave the keep set as group 7; every visible face of those pieces stays kept
if os.environ.get('M218_EYE_HIDDEN') == '1':
    hid = (p == 4) & (np.load('work/visible_all.npy') == 0)
    keep &= ~hid
    groups[hid] = 7
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('features eyes', np.round(eyes, 3).tolist(), 'nose', np.round(nose, 3).tolist(), 'mouth', np.round(mouth, 3).tolist())
print('KEEP', int(keep.sum()), '(features', int(feat.sum()), 'sockets', int(socket.sum()), ')',
      {k: int((groups == k).sum()) for k in range(8)})
