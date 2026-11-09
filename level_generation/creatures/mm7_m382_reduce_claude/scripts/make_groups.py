#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 rat (m382, faces -y, 2.0 m long with the tail, 0.8 m high). Smart Topology pieces: five body pieces (head, neck,
front legs and fur in one, hind legs and tail, the left hind foot, two fur shells) and 71 small pieces: 16 claws
(~100-126 faces each, 5-6 cm), 7 whiskers (100-118 faces, 13-22 cm), ~27 teeth (38-78 faces, 2 cm), the spiky fur
ridge cards (17-89 faces, 18-67 cm long) and a few 1-6 face slivers.
Labels: 0 body (spine, neck, legs), 1 head (Head-dominated faces of the body), 2 paws (FrontPaw/HindPaw-dominated faces
of the body), 3 tail (Tail1-6), 4 fur shells (the two 188/335-face body pieces), 5 claws, 6 whiskers, 7 teeth.
Kept exactly: the fur ridge cards and slivers (any cut flattens the crest), the eye faces (region mask G, plus one
ring, so the eye ramp stays on the eye) and the faces within 3 cm of the source's worst stretch spots (inner left
hock, thigh/tail-root border; work/README)."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
dom = info['dom'].astype(str)
big = sizes[pc] > 150
g = np.zeros(len(f), int)
g[big & (dom == 'Head')] = 1
g[big & (np.char.find(dom, 'Paw') >= 0)] = 2
g[big & np.char.startswith(dom, 'Tail')] = 3
g[big & (sizes[pc] < 400)] = 4
keep = np.zeros(len(f), bool)
for c in np.where((sizes > 0) & (sizes <= 150))[0]:
    m = pc == c; p = v[f[m]].reshape(-1, 3); ext = float((p.max(0) - p.min(0)).max()); dm = dom[m][0]
    if 'Paw' in dm and ext < 0.07:
        g[m] = 5                                                         # claw
    elif dm == 'Head' and ext > 0.1:
        g[m] = 6                                                         # whisker
    elif dm == 'Head':
        g[m] = 7                                                         # tooth
    else:
        keep[m] = True                                                   # fur ridge cards, slivers
# eyes from the region mask (G), sampled at the corners and centroid of every face
mask = np.asarray(Image.open('../mm7_m382_claude/textures/m382_region_mask.png').convert('RGBA'), np.float32) / 255
H, W = mask.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2); pts = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)
px = np.clip((pts[..., 0] % 1) * W, 0, W - 1).astype(int); py = np.clip((1 - pts[..., 1] % 1) * H, 0, H - 1).astype(int)
eye = (mask[py, px, 1] > .3).any(1)
ring = np.isin(f, np.unique(f[eye])).any(1)
keep |= ring
SPOTS = np.array([(0.006, 0.274, 0.117), (0.001, 0.275, 0.124), (-0.018, 0.06, 0.205), (-0.211, 0.201, 0.24),
                  (0.222, 0.413, 0.108)])
cen = v[f].mean(1)
spot = (np.linalg.norm(cen[:, None] - SPOTS[None], axis=2) < .03).any(1)
keep |= spot
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(8)}, 'keep', int(keep.sum()), 'eye faces', int(eye.sum()),
      'eye+ring', int(ring.sum()), 'spot faces', int(spot.sum()))
