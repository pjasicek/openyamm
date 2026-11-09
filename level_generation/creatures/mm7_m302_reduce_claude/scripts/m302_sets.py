#!/usr/bin/env python3
"""Keep set and region groups for the m302 peasant dwarf ladder (work/pieces.npy from m302_pieces.py, soles.npy,
facecol.npy (base colour per face), visible_all.npy, groups.npz). Shells: 0 skin (torso, arms, hands, face), 1 vest
(+ fleece trim), 2 beard, 3 trousers (+ belt), 4 cap, 5 nape hair, 6/7 boots (+ fleece cuffs), 8/9 eyes.
Kept exactly: the hands (every face touching a vertex with hand + finger weight > 0.3: the fist on the club); the eyes;
the boot soles (faces below 6 cm); the face front (head-set skin within M302_FACE_R, default 0.07 m, of the face
centre and in front of y = -0.11); the painted belt and buckle on the trousers (above 0.60 m, dark leather or grey
metal by base colour); the bracers painted on the forearm skin (forearm-dominant skin faces of dark leather colour);
and the faces of any M302_EXTRA_KEEP arrays (max-error patches).
Groups (decimated on their own when a ratio is given): 1 visible head set (beard, cap, hair, face rest), 2 hidden head
set, 3 fleece (vest trim and boot cuffs, by colour), 4 vest leather, 5 trousers, 6 boots, 8 hidden body faces, 9 visible
skin (torso, arms); label 0 takes the rest of the ladder budget.
Usage: m302_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import colorsys, os, sys
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); col = np.load('work/facecol.npy')
seen = np.load('work/visible_all.npy')
hsv = np.array([colorsys.rgb_to_hsv(*x) for x in col / 255]); hue, sat, val = hsv.T
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
fore = W[:, [i for i, n in enumerate(names) if 'Forearm' in n]].sum(1)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); headset = u > 0.51
face = headset & (p == 0) & (np.linalg.norm(c - np.array([-0.004, -0.15, 1.13]), axis=1) < E('M302_FACE_R', '0.07')) & (c[:, 1] < -0.11)
belt = (p == 3) & (v[f][..., 2].min(1) > E('M302_BELT_Z', '0.60')) & ((val < 0.42) | (sat < 0.18))
bracer = (p == 0) & (fore[f].mean(1) > 0.5) & (val < 0.45) & (hue < 0.15)
fleece = np.isin(p, (1, 6, 7)) & (sat < 0.3) & (val > 0.55)
keep = np.isin(p, (8, 9)) | (hand[f] > 0.3).any(1) | soles | face
if os.environ.get('M302_BELT', '1') == '1':
    keep |= belt
if os.environ.get('M302_BRACER', '1') == '1':
    keep |= bracer
if os.environ.get('M302_FLEECE_KEEP', '0') == '1':
    keep |= fleece
extra = os.environ.get('M302_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[headset & (seen > 0)] = 1; groups[headset & (seen == 0)] = 2
groups[(groups == 0) & fleece] = 3
groups[(groups == 0) & (p == 1)] = 4
groups[(groups == 0) & (p == 3)] = 5
groups[(groups == 0) & np.isin(p, (6, 7))] = 6
groups[(groups == 0) & (seen == 0)] = 8
groups[(groups == 0) & (p == 0)] = 9
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(hands', int(((hand[f] > 0.3).any(1)).sum()), 'face', int(face.sum()), 'belt', int(belt.sum()),
      'bracer', int(bracer.sum()), 'soles', int(soles.sum()), 'fleece', int(fleece.sum()), ')',
      {k: int(((groups == k) & ~keep).sum()) for k in range(10)})
