#!/usr/bin/env python3
"""Keep set and region groups for the m226 ladder (work/regions.npy, work/soles.npy, work/groups.npz).
Kept exactly: both hand shells (fitted falchion grip, fingers), small pieces (studs, spikes, buckles, eyes, face
strands), boot soles (faces below 6 cm), the front of the face (M226_KEEP_FACE=1, default) and the sleeve ends (skin
faces touching a vertex with hand + finger weight > 0.3). Groups (own ratios via REA_GROUP_RATIOS): 2 rest of the head
skin (neck, ears, scalp under the hair), 3 hair cap, 5 ponytail, 6 yoke, 7 dagger + sheath, 8 scabbard, 9 belt +
buckle, 10 thigh strap; label 0 (skin) takes the ladder budget. Usage: m226_sets.py <name> -> work/keep_<name>.npy,
work/groups_<name>.npy
Review fixes (M226_EXTRA=1, default; the first pick r76 of config c): the belt buckle (piece of 142 faces, its relief
knot broke at 60 %), the skin within 3 cm of the chest placket strip (skin poked through the strip's lower edge) and
with M226_EARS=1 both ears (head faces beyond |x| 6.2 cm between 1.50 and 1.64 m) are kept exactly."""
import os, sys
import numpy as np
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
reg = np.load('work/regions.npy'); soles = np.load('work/soles.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = reg == 2
front = head & (c[:, 1] < -0.035) & (c[:, 2] > 1.46) & (c[:, 2] < 1.68)
cuff = (reg == 1) & (hand[f] > 0.3).any(1)
keep = (reg == 4) | (reg == 11) | soles | cuff
if os.environ.get('M226_KEEP_FACE', '1') == '1':
    keep |= front
if os.environ.get('M226_EXTRA', '1') == '1':
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    from scipy.spatial import cKDTree
    n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    fl = lab[f[:, 0]]; sizes = np.bincount(fl)
    buckle = np.zeros(len(f), bool)
    for p in np.unique(fl[reg == 9]):  # belt (243) and buckle (142): the smaller piece in front
        if sizes[p] < 200:
            buckle |= fl == p
    strip = np.zeros(len(f), bool)
    for p in np.unique(fl[reg == 11]):  # placket: the long thin strip down the chest front
        m = fl == p; pv = v[np.unique(f[m])]
        if np.ptp(pv[:, 2]) > .2 and abs(pv[:, 0].mean()) < .04 and pv[:, 1].mean() < -.08:
            strip |= m
    near = np.zeros(len(f), bool)
    near[(reg == 1)] = cKDTree(v[np.unique(f[strip])]).query(c[reg == 1])[0] < 0.03
    ears = head & (np.abs(c[:, 0]) > 0.062) & (c[:, 2] > 1.50) & (c[:, 2] < 1.64)
    keep |= buckle | near
    if os.environ.get('M226_EARS', '0') == '1':
        keep |= ears
    print('EXTRA buckle', int(buckle.sum()), 'strip', int(strip.sum()), 'skin near strip', int(near.sum()), 'ears', int(ears.sum()))
groups = np.zeros(len(f), int)
for r in (2, 3, 5, 6, 7, 8, 9, 10):
    groups[(reg == r) & ~keep] = r
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(front', int(front.sum()), 'cuff', int(cuff.sum()), 'soles', int(soles.sum()), ')',
      {k: int((groups == k).sum()) for k in (0, 2, 3, 5, 6, 7, 8, 9, 10)})
