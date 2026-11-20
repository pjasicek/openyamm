#!/usr/bin/env python3
"""Keep set and region groups for the m352 peasant (human male 1) ladder (work/pieces.npy from m352_pieces.py,
soles.npy, facecol.npy (base colour per face, facecol.py), visible_all.npy, groups.npz). Shells: 0 tunic (+ painted
belt), 1 trouser legs, 2 head + neck, 3/4 hands with forearms, 5 long hair, 6/7 shoes, 8 buckle, 9 strap end, 10/11 eyes,
12..68 brass studs.
Kept exactly: every finger face (any vertex with finger weight > 0.05; the playbook's dwarf: fingers in a cut come back
as jagged points); the brass studs and the buckle (small separate pieces); the soles (shoe faces below 6 cm); the visible
eye faces; the face front (head and neck skin within M352_FACE_R, default 0.085 m, of the face centre, in front of
y = -0.04); the painted belt (tunic faces between 0.97 and 1.09 m of leather colour); faces of M352_EXTRA_KEEP arrays.
Groups (decimated on their own when a ratio is given): 1 visible head set (hair, face rest, ears), 2 hidden faces of the
head set (scalp under the hair, eye backs), 3 palms and backs of the hands (hand-weighted, not finger), 4 tunic, 5 trouser
legs, 6 shoe uppers, 7 strap end, 8 hidden body faces; label 0 takes the rest.
Usage: m352_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import colorsys, os, sys
import numpy as np
E = lambda k, x: float(os.environ.get(k, x))
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); col = np.load('work/facecol.npy')
seen = np.load('work/visible_all.npy')
hsv = np.array([colorsys.rgb_to_hsv(*x) for x in col / 255]); hue, sat, val = hsv.T
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
fing = W[:, [i for i, n in enumerate(names) if 'Finger' in n]].sum(1)
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand')]].sum(1)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1); headset = u > 0.51
fingers = (fing[f] > 0.05).any(1)
palm = ((hand + fing)[f] > 0.3).any(1) & ~fingers
studs = p >= 12
eyes_vis = np.isin(p, (10, 11)) & (seen > 0)
face = (p == 2) & (np.linalg.norm(c - np.array([-0.005, -0.09, 1.53]), axis=1) < E('M352_FACE_R', '0.085')) & (c[:, 1] < -0.04)
belt = (p == 0) & (c[:, 2] > 0.97) & (c[:, 2] < 1.09) & (hue < 0.13) & (sat > 0.3)
keep = fingers | studs | (p == 8) | soles | eyes_vis | face | belt
extra = os.environ.get('M352_EXTRA_KEEP')
if extra:
    for e in extra.split(','):
        keep |= np.load(e)
groups = np.zeros(len(f), int)
groups[headset & (seen > 0)] = 1; groups[headset & (seen == 0)] = 2
groups[(groups == 0) & palm] = 3
groups[(groups == 0) & (p == 0) & (seen > 0)] = 4
groups[(groups == 0) & (p == 1) & (seen > 0)] = 5
groups[(groups == 0) & np.isin(p, (6, 7))] = 6
groups[(groups == 0) & (p == 9)] = 7
groups[(groups == 0) & (seen == 0)] = 8
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(fingers', int(fingers.sum()), 'studs', int(studs.sum()), 'face', int(face.sum()), 'belt',
      int(belt.sum()), 'soles', int(soles.sum()), 'eyes', int(eyes_vis.sum()), ')',
      {k: int(((groups == k) & ~keep).sum()) for k in range(10)})
