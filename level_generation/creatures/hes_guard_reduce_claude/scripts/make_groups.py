#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep masks.
Hesper Landfall Guard (hgd, faces -y, 1.70 m rest, 8,559 triangles in one HGD_A atlas: body set u < 0.5, head set
u > 0.5). Pieces (Smart Topology parts after the source project's own reduction): legs + boots with fused shin plates
(1,620), torso shell (coat, chest plate, tabard, belt; 1,603), head + neck (1,412), two arms with guards and rigid
fists (~640 each), helmet (566), shoulder plates (~190), knee plates (~130), pouches/holster/tubes (66-186), eyes,
chest rivets, buckle and helmet stud (34-113).
Labels: 0 torso, legs, arms (the rest); 1 head set outside the face front (neck, ears, scalp under the helmet);
2 fists (B_*_Hand dominated: kept exactly, the rifle's fitted pistol grip and handguard hold); 3 feet and boots
(B_*_Foot, B_*_Toe0); 4 helmet; 5 shoulder and knee plates; 6 pouches, holster and tubes (mid pieces); 7 face front
(head set in front of FRONT_Y between FRONT_ZMIN and FRONT_ZMAX: brows, eyes, nose, mouth, chin).
work/keep_small.npy: pieces of up to SMALL faces (eyes, rivets, buckle, stud) plus the SOLES (all three vertices within
SOLE_Z of the rest floor). work/keep_front.npy: keep_small + face front + fists."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
SOLE_Z = float(os.environ.get('SOLE_Z', '0.03'))
SMALL = int(os.environ.get('SMALL', '120'))
FRONT_Y = float(os.environ.get('FRONT_Y', '-0.045'))
FRONT_ZMIN = float(os.environ.get('FRONT_ZMIN', '1.45'))
FRONT_ZMAX = float(os.environ.get('FRONT_ZMAX', '1.64'))
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
dom = info['dom'].astype(str)
u = d['wuv'].reshape(-1, 3, 2)[:, :, 0].mean(1)
cen = v[f].mean(1)
small = sizes[pc] <= SMALL
g = np.zeros(len(f), int)
g[np.array(['Hand' in x or 'Finger' in x for x in dom])] = 2
g[np.array(['Foot' in x or 'Toe0' in x for x in dom])] = 3
head = (u > 0.5) & ~small
g[head] = 1
front = head & (cen[:, 1] < FRONT_Y) & (cen[:, 2] > FRONT_ZMIN) & (cen[:, 2] < FRONT_ZMAX)
g[front] = 7
# piece classes by size and place: the helmet is the head-dominated piece above the face in the body set
for p in np.unique(pc):
    m = pc == p
    if sizes[p] <= SMALL or sizes[p] > 1000:
        continue
    dm = dom[m]
    if (np.char.find(dm, 'Head') >= 0).mean() > .9 and (u[m] < .5).all():
        g[m] = 4
    elif sizes[p] < 300 and ((np.char.find(dm, 'Clavicle') >= 0) | (np.char.find(dm, 'Thigh') >= 0)
                             | (np.char.find(dm, 'UpperArm') >= 0)).mean() > .9:
        g[m] = 5
    elif sizes[p] < 300 and (dm == 'B_Pelvis').mean() > .9:
        g[m] = 6
# guard round 2 (close-ups of configs e/f): the coat skirt's gold hem and the tabard's gold border and glyph broke
# into zigzags at the torso piece's shared ratio: 8 = torso piece below WAIST_Z (skirt, tabard), 9 = torso piece above
torso = np.argmax(sizes * np.array([(np.char.find(dom[pc == p], 'Pelvis') >= 0).mean() + (np.char.find(dom[pc == p], 'Spine') >= 0).mean()
                                    if sizes[p] > 1000 else 0 for p in range(len(sizes))]))
WAIST_Z = float(os.environ.get('WAIST_Z', '0.93'))
g[(pc == torso) & (cen[:, 2] < WAIST_Z) & (g == 0)] = 8
g[(pc == torso) & (cen[:, 2] >= WAIST_Z) & (g == 0)] = 9
z = v[:, 2]; zmin = z.min()
soles = (z[f] < zmin + SOLE_Z).all(1) & (g == 3)
hands = g == 2
np.save('work/groups.npy', g); np.save('work/keep_small.npy', small | soles); np.save('work/keep_soles.npy', soles)
np.save('work/keep_front.npy', small | soles | front | hands)
print('GROUPS', {k: int(((g == k) & ~small).sum()) for k in range(10)}, 'small kept', int(small.sum()),
      'sole faces kept', int(soles.sum()), 'face front', int(front.sum()), 'fists', int(hands.sum()))
