#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder and the exact-keep masks of the MM7 Goblin (m246, faces -y,
1.70 m with the crest). Garment labels come from the mm7_m246_claude master (work/vattrs.npz, dump_attrs.py):
0 skin (body shell + both hand shells), 1 rigid head (crest, helmet, eyes, cheek pieces, goatee, helmet studs),
2 hip panels (ten strips), 3 hair, 4 spikes and studs (<= 40 faces), 5 vest/strap/belt, 6 bracers, upper-arm plate,
shin guards, 7 pauldron. Visibility (visibility.py): work/visible_all.npy (whole body, 42 directions),
work/visible_head.npy and work/visible_front.npy (head band, all / frontal directions only).
Labels (work/groups_<set>.npy): -1 kept or protected, 0 rest (torso, arms, trousers, boots), 1 hair, 2 crest,
3 helmet shell, 4 vest/strap/belt, 5 plates (bracers, arm plate, shin guards, pauldron), 6 visible head sides
(ears, jaw, neck: head-set skin seen from some direction but not the face front), 7 hidden skin (never seen: scalp
under the helmet, torso under the vest), 8 left hand (back and palm, fingers excluded), 9 hip panels.
work/keep_<set>.npy (exact): the right hand (sword grip), left-hand fingers, spikes and studs, the small rigid head
pieces (eyes, cheek pieces, goatee, helmet studs, crest base), the visible face front, the soles (faces below 6 cm),
the belt, the back strap and the shin guards (K_BANDS=0 to cut them),
plus per set: G_LHAND=1 the whole left hand as group 8 (not kept), K_PANELS=1 hip panels exact, K_LHAND=1 the whole left hand exact, M246_EXTRA_KEEP=<npy> extra faces.
Usage: make_groups.py <set>"""
import os, sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
tag = sys.argv[1]
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); A = np.load('work/vattrs.npz')
f, v = d['faces'], d['verts']; n = len(v)
e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); psize = sizes[pc]
gar = A['garment'][f[:, 0]]; finger = (A['finger'][f] > 0).any(1)
dom = info['dom'].astype(str); head = info['u'] > 0.505
cen = v[f].mean(1)
skin = gar == 0
hands = skin & np.char.endswith(dom, '_Hand') | finger
hands |= skin & (psize < 1000) & (psize > 600)           # the two separate hand shells (726 / 697 faces)
rhand = hands & (cen[:, 0] < 0); lhand = hands & (cen[:, 0] > 0)
vis_all = np.load('work/visible_all.npy'); vis_head = np.load('work/visible_head.npy'); vis_front = np.load('work/visible_front.npy')
headskin = skin & head
face_front = headskin & (vis_front >= int(os.environ.get('M246_FRONT_VIEWS', '3')))
hidden = skin & ~hands & (np.where(head, vis_head, vis_all) == 0)
sole = v[f][:, :, 2].max(1) < 0.06
crest = (gar == 1) & (psize > 500)
helmet = (gar == 1) & (psize > 200) & (psize <= 500)
small_rigid = (gar == 1) & (psize <= 200)
g = np.zeros(len(f), int)
g[gar == 3] = 1; g[crest] = 2; g[helmet] = 3; g[gar == 5] = 4; g[(gar == 6) | (gar == 7)] = 5
g[headskin & ~face_front] = 6; g[hidden] = 7; g[lhand & ~finger] = 8; g[gar == 2] = 9
# thin bands (belt, the back strap: wavy at any cut) and the shin guards (their rim ring bent at 80 %)
band = (gar == 5) & (psize < 300)
shin = (gar == 6) & (psize < 120) & (cen[:, 2] < 0.6)
keep = rhand | (lhand & finger) | (gar == 4) | small_rigid | face_front | sole
if os.environ.get('K_BANDS', '1') == '1':
    keep |= band | shin
if os.environ.get('G_LHAND') == '1':      # the whole left hand (fingers too) as group 8: it holds nothing
    g[lhand] = 8; keep &= ~(lhand & ~sole)
if os.environ.get('K_PANELS') == '1':
    keep |= gar == 2
if os.environ.get('K_LHAND') == '1':
    keep |= lhand
if os.environ.get('M246_EXTRA_KEEP'):
    keep |= np.load(os.environ['M246_EXTRA_KEEP'])
g[keep] = -1
np.save(f'work/groups_{tag}.npy', g); np.save(f'work/keep_{tag}.npy', keep)
names = ['rest', 'hair', 'crest', 'helmet', 'vest/belt', 'plates', 'head sides', 'hidden skin', 'left hand', 'hip panels']
print('GROUPS', tag, {f'{k} {names[k]}': int((g == k).sum()) for k in range(10)}, 'kept', int(keep.sum()),
      '(right hand', int(rhand.sum()), 'left fingers', int((lhand & finger).sum()), 'spikes', int((gar == 4).sum()),
      'small rigid', int(small_rigid.sum()), 'face front', int(face_front.sum()), 'soles', int(sole.sum()), ')')
