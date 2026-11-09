#!/usr/bin/env python3
"""Per-face region labels for the Angel (m150) ladder (work/groups.npy) and the exact-keep mask (work/keep.npy), from
the accepted master's labels (work/src_labels.npz: piece, garment, head set; match_labels.py) and the atlas base
colour (gold trims).
Kept exactly (user-reviewed over seven rounds): eyes (garment 1), fittings (4: buckle, belt rings, studs), leather
tabs (7), shoulder straps (piece 3), the belt band of the skin shell (z 0.95-1.11, |x| < 0.3), hands and fingers
(fingers, dominant B_*_Finger*: the fitted sword fist and shield hand; the palms, group 6, are cut gently), and the painted gold trims of the cuirass
and greaves (skin-shell faces whose UV centre samples saturated gold: thin lines bend under any collapse).
Feather cards (wing components under 60 faces) are kept too. Groups: 5 face (head set in front of and below the brow),
1 scalp, back hair and neck under the helmet, 2 wing shells (garment 5), 3 bracers (garment 2),
4 skirt (garment 6), 6 palms, 7 sandals (P09/P10), 0 the rest (torso, arms, legs, greaves) takes the ladder's remaining budget."""
import numpy as np, colorsys
from PIL import Image
d = np.load('work/mesh_in.npz'); L = np.load('work/src_labels.npz'); info = np.load('work/faces_info.npz')
f, v = d['faces'], d['verts']; n = len(f)
pc, gm, hd = L['piece'], L['garment'], L['head']
dom = info['dom'].astype(str)
cen = v[f].mean(1)
img = np.asarray(Image.open('work/atlas_basecolor.png').convert('RGB'), np.float64) / 255; H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2).mean(1)
px = np.clip((uv[:, 0] % 1) * W, 0, W - 1).astype(int); py = np.clip((1 - uv[:, 1] % 1) * H, 0, H - 1).astype(int)
c = img[py, px]; mx, mn = c.max(1), c.min(1); s = (mx - mn) / np.maximum(mx, 1e-3)
hue = np.array([colorsys.rgb_to_hsv(*x)[0] * 360 for x in c])
gold = (gm == 0) & (pc == 0) & (hd == 0) & (hue > 30) & (hue < 65) & (s > 0.4) & (mx > 0.45)
hand = np.array([('Hand' in x) or ('Finger' in x) for x in dom])
belt = (gm == 0) & (pc == 0) & (cen[:, 2] > 0.95) & (cen[:, 2] < 1.11) & (np.abs(cen[:, 0]) < 0.3)
finger = np.array(['Finger' in x for x in dom])
palm = hand & ~finger & (gm == 0)
keep = np.isin(gm, [1, 7]) | (pc == 3) | belt | gold | (pc == 24)          # P24: the belt buckle disc
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
nv = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nv, nv)), directed=False)
comp = lab[f[:, 0]]; csize = np.bincount(comp)
cards = (gm == 5) & (csize[comp] < 60)                         # feather cards: ~15 triangles each, already minimal
keep |= (csize[comp] < 60) & ~cards & (gm != 4)              # small pieces: hair locks, sandal straps, soles (ends taper at any cut)
# head set: the face (front, below the brow at z 1.64) gently; scalp, back hair and the neck under the helmet (hidden
# by the helmet attachment) harder
face = (hd == 1) & (cen[:, 2] < 1.64) & (cen[:, 1] < -0.02)
g = np.zeros(n, int)
g[(hd == 1) & ~face] = 1; g[face] = 5; g[gm == 5] = 2; g[gm == 2] = 3; g[gm == 6] = 4; g[palm] = 6; g[np.isin(pc, [9, 10]) & (gm == 0)] = 7   # sandals
g[gm == 4] = 8; g[cards] = 9; g[finger & (gm == 0)] = 10    # fittings (studs, rings), feather cards, fingers: own gentle ratios
np.save('work/groups.npy', g); np.save('work/keep.npy', keep)
print('KEEP', int(keep.sum()), {'eyes/tabs': int(np.isin(gm, [1, 7]).sum()), 'straps': int((pc == 3).sum()),
      'belt': int(belt.sum()), 'gold trims': int(gold.sum())})
print('KEEP total with feather cards', int(keep.sum()), 'cards', int(cards.sum()))
print('GROUPS (not kept)', {k: int(((g == k) & ~keep).sum()) for k in range(11)}, 'total', n)
