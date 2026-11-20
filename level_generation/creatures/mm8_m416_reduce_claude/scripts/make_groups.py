#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy),
MM8 Pirate Crossbowman (female). Head texture set = u > 0.5 of the merged 2080x1024 atlas.
Labels: 0 rest (vest, trousers, boots, sash, arms, gauntlet), 1 face skin (head set, B_Head, front of FACE_Y, above
FACE_Z), 2 neck, ears and scalp (rest of the head-set skin piece), 3 bandanna (the body-set B_Head piece on top),
4 hair (the two body-set B_Head pieces at the back), 5 hands (B_*_Hand dominant: back of hand, palm, gauntlet cuff).
Kept exactly: the fingers (B_*_Finger* dominant faces; both hands hold the crossbow), small pieces of up to REA_SMALL
faces (eyes, bandanna knot tails, sash tails, buckle), and the soles (faces below 6 cm; foot-yaw gates).
Faces appended after the source (scalp cap, patch_scalp.py) are kept and labelled 0."""
import os, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); nsrc = len(info['dom']); dom = np.concatenate([info['dom'], ['cap'] * (len(f) - nsrc)])
head = np.concatenate([info['u'] > .5, np.ones(len(f) - nsrc, bool)])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
big = np.bincount(pc).argsort()[::-1]
g = np.zeros(len(f), int)
skin = [p for p in big[:3] if head[pc == p].mean() > .9]
assert len(skin) == 1, skin
skin = (pc == skin[0])
# bandanna and hair: body-set pieces of over 180 faces that are all B_Head; the bandanna is the one on top
bh = [p for p in big if np.bincount(pc)[p] > 180 and not head[pc == p].any() and (dom[pc == p] == 'B_Head').all()]
top = max(bh, key=lambda p: c[pc == p][:, 2].mean())
FACE_Y, FACE_Z = float(os.environ.get('FACE_Y', '-0.02')), float(os.environ.get('FACE_Z', '1.56'))
face = skin & (dom == 'B_Head') & (c[:, 1] < FACE_Y) & (c[:, 2] > FACE_Z)
g[skin & ~face] = 2; g[face] = 1; g[pc == top] = 3
for p in bh:
    if p != top:
        g[pc == p] = 4
hand = np.array([x.endswith('_Hand') for x in dom])
g[hand & (g == 0)] = 5
fing = np.array(['Finger' in x for x in dom])
small = size <= int(os.environ.get('REA_SMALL', '180'))
sole = c[:, 2] < .06
cap = np.arange(len(f)) >= nsrc
g[cap] = 0
keep = fing | small | sole | cap
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int((g == k).sum()) for k in range(6)}, 'keep', int(keep.sum()), 'fingers', int(fing.sum()),
      'small', int(small.sum()), 'sole', int(sole.sum()), 'cap', int(cap.sum()), 'bandanna/hair pieces', [int(np.bincount(pc)[p]) for p in bh])
