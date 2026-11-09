#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep.npy).
MM7 Genie (m238, faces -y, 1.79 m). Pieces (connected components of the welded source): the body (torso, arms,
hands, head, ponytail, inner core; ~7.2k faces), the spiral vortex shell (~2.4k) and small head pieces: circlet,
two earrings, eyes, forehead jewel and gem settings (~1.4k).
Labels:
- keep exactly: the small pieces but the earrings (circlet, eyes, jewels) and the fingers (finger-weighted faces);
- protected (work/protect_face.npy, decimated on its own at REA_PROTECT_RATIO): the face (B_Head faces of the body
  below the hairline FACE_TOP and in front of the head's centre plane, ears included);
- 1 hair cap and ponytail (the rest of the B_Head faces) without its gold bands;
- 2 gold trims on the body (base colour gold at the face's UV centroid: ponytail bands, collar, cuff and top trims);
- 3 the vortex shell; 4 the palms (B_*_Hand); 5 the earrings; 6 the fingers when KEEP_FINGERS=0;
- 0 torso, arms, neck and inner core: the rest of the ladder budget.
Env: FACE_TOP (default 1.63 m)."""
import os
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); order = np.argsort(-sizes)
body, vortex = order[0], order[1]
dom = info['dom'].astype(str)
cen = v[f].mean(1)
small = (pc != body) & (pc != vortex)
head = (pc == body) & (dom == 'B_Head')
FACE_TOP = float(os.environ.get('FACE_TOP', '1.63'))
hy = float(np.median(cen[head, 1]))
face = head & (cen[:, 2] < FACE_TOP) & (cen[:, 1] < hy + 0.01)
fingers = (pc == body) & np.array(['Finger' in b for b in dom])
palms = (pc == body) & np.isin(dom, ['B_L_Hand', 'B_R_Hand'])
hands = fingers | palms
# gold by the base colour at each face's UV centroid
img = np.asarray(Image.open('work/src_basecolor.png').convert('HSV'), float) / 255
H, W = img.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2).mean(1)
px = np.clip((uv[:, 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1)
hh, ss, vv = img[py, px, 0] * 360, img[py, px, 1], img[py, px, 2]
gold = (pc == body) & (hh > 30) & (hh < 62) & (ss > 0.4) & (vv > 0.45) & ~face & ~hands
ear = small & (np.abs(cen[:, 0]) > 0.05) & (cen[:, 2] < 1.53)
keep = (small & ~ear) | (fingers & (os.environ.get('KEEP_FINGERS', '1') == '1'))
g = np.zeros(len(f), int)
g[head & ~face] = 1
g[gold] = 2
g[pc == vortex] = 3
g[palms] = 4
g[ear] = 5
g[fingers & ~keep] = 6
np.save('work/groups.npy', g); np.save('work/keep.npy', keep); np.save('work/protect_face.npy', face & ~keep)
print('GROUPS kept', int(keep.sum()), '(small', int((small & ~ear).sum()), 'fingers', int(fingers.sum()), ') face', int(face.sum()),
      {k: int(((g == k) & ~keep & ~face).sum()) for k in range(7)}, 'head centre y', round(hy, 3))
