#!/usr/bin/env python3
"""Keep sets and region groups of the welded rest mesh (work/mesh_in.npz, work/groups.npz) -> work/keep_c.npy,
work/groups_c.npy. Kept exactly: small separate pieces (REA_SMALL, tail strips, eyes), both hands with their fingers
(hand + finger weight > 0.3 on any corner: the bow grip and the arrow-drawing fingers), the bowstring and nocked
arrow (String*/Arrow weights). Groups: 1 = head texture set (face, hair, ears; merged atlas u > 1184/2208),
2 = tail-strip pieces up to REA_TAIL faces (Tail* dominated), 0 = the rest. Prints counts."""
import os
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
f, v, uv = d['faces'], d['verts'], d['wuv'].reshape(-1, 3, 2)
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; sizes = np.bincount(fl)
col = lambda pred: W[:, [i for i, x in enumerate(names) if pred(x)]].sum(1)
fingers = ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
hand = col(lambda x: x in ('LHand', 'RHand') or any(k in x for k in fingers))
string = col(lambda x: x.startswith('String') or x == 'Arrow')
tail = col(lambda x: x.startswith('Tail'))
keep = sizes[fl] <= int(os.environ.get('REA_SMALL', '80'))
nk = {'small': int(keep.sum())}
finger = col(lambda x: any(k in x for k in fingers)); palm = col(lambda x: x in ('LHand', 'RHand'))
hoof = col(lambda x: 'Hoof' in x)
if os.environ.get('REA_PALMS_GROUP') == '1':  # fingers exact, palm/back of hand as group 3
    keep |= finger[f].mean(1) > .5
else:
    keep |= hand[f].mean(1) > float(os.environ.get("REA_HAND", ".5"))
nk['+hands'] = int(keep.sum())
if os.environ.get('REA_KEEP_HOOVES') == '1':  # hoof rims and soles (floor contact) lose their edges first
    keep |= hoof[f].mean(1) > .5; nk['+hooves'] = int(keep.sum())
keep |= (string[f] > .3).any(1); nk['+string/arrow'] = int(keep.sum())
groups = np.zeros(len(f), int)
head_set = uv[:, :, 0].mean(1) % 2 > 1184 / 2208
groups[head_set] = 1
straps = (sizes[fl] > int(os.environ.get('REA_SMALL', '80'))) & (sizes[fl] < sizes.max()) & ~head_set & (tail[f].mean(1) <= .5)
if float(os.environ.get('REA_STRAP_SKIN', '0')) > 0:  # body skin under the straps is painted strap green; a cut
    # moves that paint out past the strap edges as green slivers on the chest, so keep the skin within this radius
    from scipy.spatial import cKDTree
    sv = np.unique(f[straps]); near = cKDTree(v[sv]).query(v)[0] < float(os.environ['REA_STRAP_SKIN'])
    keep |= (sizes[fl] == sizes.max()) & near[f].any(1); nk['+strap skin'] = int(keep.sum())
if os.environ.get('REA_STRAPS') == 'keep':  # harness straps: painted studs and edges go wavy under a cut
    keep |= straps
elif os.environ.get('REA_STRAPS') == 'group':
    groups[straps] = 4
if os.environ.get('REA_PALMS_GROUP') == '1':
    groups[(hand[f].mean(1) > .5) & ~(finger[f].mean(1) > .5)] = 3
groups[(sizes[fl] <= int(os.environ.get('REA_TAIL', '260'))) & (tail[f].mean(1) > .5)] = 2
if os.environ.get('REA_KEEP_TAIL', '1') == '1':  # tail strips thin out into gaps at any cut (6 cm at 75 %)
    keep |= groups == 2; nk['+tail strips'] = int(keep.sum())
if os.environ.get('REA_KEEP_FACE', '1') == '1':  # face skin (head set on the main surface, facing forward): eyes, lips
    # and beard edge smear under any cut (0.55-0.8 tried); scalp and ears under the hair stay in group 1
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    face = head_set & (sizes[fl] == sizes.max()) & (fn[:, 1] < -float(os.environ.get('REA_FACE_DOT', '0.2')))
    keep |= face; nk['+face'] = int(keep.sum())
np.save('work/keep_c.npy', keep); np.save('work/groups_c.npy', groups)
print('KEEP', nk, 'of', len(f))
for k in range(5):
    print('group', k, int((groups == k).sum()), 'faces,', int(((groups == k) & ~keep).sum()), 'not kept')
