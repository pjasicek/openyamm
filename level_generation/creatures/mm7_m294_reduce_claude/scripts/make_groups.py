#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Necromancer (faces -y). Labels come from the production master's garment and piece attributes
(work/master_labels.npz, master_labels.py; matched per vertex, majority per face), rest-pose visibility
(work/visible.npy, vis_faces.py), dominant bones (work/faces_info.npz) and the runtime maps at each face's UV (merged
atlas 2080x1024: body set at x 0-1024, head set at 1056-2080; body material class 9 = gold).
Garments: 0 head skin (piece 1), 1 tunic + sleeves + fused hands (piece 0 above the cape split), 2 cape (piece 0 below
0.96 m reaching the floor, panels and lining 4, 5, 10, 11, 15, 16), 3 circlet (6, 7), 4 eyes (8, 9), 5 lips (12, 13),
12 hair shell (3), 15 legs and boots (2), 17 tight hem and front flap (14).
Labels: 0 tunic (rest), 1 visible face/neck skin outside the kept face front, 2 head skin hidden in the rest pose
(scalp under the hair, inside of the head), 3 hands (rigid open claws; palm and back), 4 fingers and claws, 5 cape interior, 6 hair, 7 legs and boots,
8 other faces hidden in the rest pose, 9 face front outside the core (cheeks, temples, jaw sides).
Kept exactly: the face front (lips, nose, eyes, brows, chin), eyes, lips, circlet, pieces of up to 300 faces, the
cape's open-edge ring (ragged panel edges and strip tips), the tight hem and front flap (garment 17), gold texels
(knee chevrons) and the soles (faces below 6 cm)."""
import numpy as np
from PIL import Image
from scipy import stats
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
T = '../mm7_m294_claude/textures/'
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom'].astype(str); vis = np.load('work/visible.npy')
m = np.load('work/master_labels.npz'); _, idx = cKDTree(m['co']).query(v)
gf = stats.mode(m['garment'][idx][f], axis=1).mode.ravel(); pf = stats.mode(m['piece'][idx][f], axis=1).mode.ravel()
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
E = np.sort(e, 1); fe = np.tile(np.arange(len(f)), 3)
_, inv, cnt = np.unique(E, axis=0, return_inverse=True, return_counts=True)
openf = np.zeros(len(f), bool); openf[fe[cnt[inv.ravel()] == 1]] = True
uv = d['wuv'].reshape(-1, 3, 2); p = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)
ua = p[..., 0]; head = ua.mean(1) > 0.5
us = np.where(head[:, None], (ua * 2080 - 1056) / 1024, ua * 2080 / 1024)
x = np.clip((us * 1024).astype(int), 0, 1023); y = np.clip(((1 - p[..., 1]) * 1024).astype(int), 0, 1023)
bc = np.asarray(Image.open(T + 'm294_material_classes.png'))
gold = (~head) & ((bc[y, x] == 9).sum(1) >= 1)
hand = np.isin(dom, ['B_L_Hand', 'B_R_Hand'])
skin = (gf == 0)
front = skin & (c[:, 1] < -0.13) & (c[:, 2] > 1.47) & (c[:, 2] < 1.61)        # the face front: brows to chin
# the face core (2.8 cm around the lips, 2.2 cm around each eye, the nose ridge; face centre x = -0.035) stays exact; the rest of the front
# (cheeks, temples, jaw sides) is its own gentle group 9 (keep_base keeps it too; keep variants drop it)
dist = lambda q: np.linalg.norm(c - np.array(q), axis=1)
core = front & ((dist((-0.035, -0.168, 1.513)) < 0.028) | (dist((-0.059, -0.162, 1.569)) < 0.022)
                | (dist((-0.011, -0.163, 1.569)) < 0.022)
                | ((np.abs(c[:, 0] + 0.035) < 0.016) & (c[:, 2] > 1.52) & (c[:, 2] < 1.585)))   # lips, eyes, nose
g = np.zeros(len(f), int)
g[skin & vis] = 1
g[skin & ~vis] = 2
g[(gf == 2)] = 5
g[gf == 12] = 6
g[gf == 15] = 7
g[~vis & ~skin & (gf != 12)] = 8
g[hand & (gf == 1)] = 3
# fingers and claws (hand faces over 7.5 cm from the wrist joint, ../mm7_m294_claude/work/joints_final.json): own
# gentler group 4; at 40 % with the hand the finger tips and thumb came back blunt and jagged
wrists = np.array([(0.31096, -0.15895, 0.87573), (-0.35699, -0.15711, 0.88982)])
g[(g == 3) & (np.linalg.norm(c[:, None] - wrists[None], axis=2).min(1) > 0.075)] = 4
g[front & ~core] = 9
soles = (c[:, 2] < 0.06) & (gf == 15)
keep = (front | np.isin(gf, [3, 4, 5, 17]) | (size <= 300) | ((gf == 2) & openf) | gold | soles)
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
np.save('work/face_front.npy', front); np.save('work/face_core.npy', core); np.save('work/garment_face.npy', gf)
print('GROUPS free', {k: int(((g == k) & ~keep).sum()) for k in range(10)}, 'keep', int(keep.sum()), 'of', len(f),
      '| front', int(front.sum()), 'core', int(core.sum()), 'cape edge', int(((gf == 2) & openf).sum()), 'gold', int(gold.sum()),
      'soles', int(soles.sum()), 'small', int((size <= 300).sum()))
