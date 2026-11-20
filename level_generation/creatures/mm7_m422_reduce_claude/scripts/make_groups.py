#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Vampire (m422, faces -y, 1.70 m). Each source face takes the production master's piece and garment
(../mm7_m422_claude/work/rig_v6.blend via master_labels.py, matched by centroid, < 0.002 mm) and its classes from the
source project's runtime maps at the face's UV (merged atlas 2080x1024: body set at x 0-1024, head set at 1056-2080;
classes 1 skin, 2 hair, 6 eye, 8 cloth, 9 gold, 11 shirt linen).
Pieces: 0 coat top + sleeves, 1 head skin (head set), 2 trousers and shoes, 3 hair (head set), 4/5 hands (rigid open
claws), 6 belt buckle, 7/8 eyes, 9 jabot, 10 neck ornament, 11-25 clasps (13-24 on the skirt chains), 27 cape, 28
stand-up collar, 29 coat skirt.
Labels: 0 anything else (takes the rest of the ladder budget; empty), 10 coat top + sleeves, 1 visible face and head skin, 2 head skin hidden in
the rest pose (under the hair, inside the collar), 3 hair, 4 hands, 5 skirt, 6 cape, 7 collar, 8 visible trousers and
shoes, 9 hidden trousers (inside the coat skirt).
Kept exactly: pieces of up to 250 faces (eyes, buckle, jabot, ornament, every clasp), gold texels on the coat, skirt,
cape and collar (painted trims: placket, cuffs, hems, belt; thin painted lines bend under any collapse), the mouth with
the painted fang tips (MOUTH_R around the lips), the eye sockets (head skin within EYE_R of an eye), the soles (below SOLE_Z), the coat and cape hem bands, the front belt
band with the belt-end flaps (coat/skirt faces in BELT_Z, y < -0.10, |x| < 0.22) and the armpit band (ARMPIT box
|x| 0.14-0.30 m, z 1.22-1.42 m on the coat top, the inner part of the source's own reduce_protect_box: the armpit stretch
gate is borderline; ARMPIT=0 drops it)."""
import os
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
T = '../mm7_m422_claude/textures/'
E = lambda k, dflt: float(os.environ.get(k, dflt))
MOUTH = np.array([-0.01, -0.178, 1.497]); MOUTH_R = E('MOUTH_R', '0.025')
SOLE_Z = E('SOLE_Z', '0.06'); SKIRT_HEM_Z = E('SKIRT_HEM_Z', '0.36'); CAPE_HEM_Z = E('CAPE_HEM_Z', '0.47')
BELT_Z = (E('BELT_LO', '0.90'), E('BELT_HI', '1.08'))
ARMPIT = [float(t) for t in os.environ.get('ARMPIT', '0.14,0.30,1.22,1.42').split(',')] if os.environ.get('ARMPIT', '') != '0' else None
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
m = np.load('work/master_tris.npz'); dist, idx = cKDTree(m['cent']).query(c)
assert dist.max() < 1e-5, dist.max()
piece = m['piece'][idx]
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; size = np.bincount(pc)[pc]
uv = d['wuv'].reshape(-1, 3, 2); p = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)    # 3 corners + centroid
ua = p[..., 0]; head = ua.mean(1) > 0.5
us = np.where(head[:, None], (ua * 2080 - 1056) / 1024, ua * 2080 / 1024)
x = np.clip((us * 1024).astype(int), 0, 1023); y = np.clip(((1 - p[..., 1]) * 1024).astype(int), 0, 1023)
bc = np.asarray(Image.open(T + 'm422_material_classes.png')); hc = np.asarray(Image.open(T + 'm422_head_material_classes.png'))
cls = np.where(head[:, None], hc[y, x], bc[y, x])
vis = np.load('work/visible.npy')
cloth = np.isin(piece, [0, 27, 28, 29])
gold = cloth & (cls == 9).any(1)
g = np.zeros(len(f), int)
g[piece == 0] = 10                                  # coat top + sleeves (its own ratio; 0 = anything left)
g[(piece == 1) & vis] = 1
g[(piece == 1) & ~vis] = 2
g[piece == 3] = 3
g[np.isin(piece, [4, 5])] = 4
g[piece == 29] = 5
g[piece == 27] = 6
g[piece == 28] = 7
g[(piece == 2) & vis] = 8
g[(piece == 2) & ~vis] = 9
small = size <= 250
mouth = (piece == 1) & (np.linalg.norm(c - MOUTH, axis=1) < MOUTH_R)
EYE_R = E('EYE_R', '0')                     # eye sockets: head skin within EYE_R of an eye piece
sockets = (piece == 1) & (cKDTree(c[np.isin(piece, [7, 8])]).query(c)[0] < EYE_R) if EYE_R > 0 else np.zeros(len(f), bool)
soles = (piece == 2) & (c[:, 2] < SOLE_Z)
hems = ((piece == 29) & (c[:, 2] < SKIRT_HEM_Z)) | ((piece == 27) & (c[:, 2] < CAPE_HEM_Z))
belt = np.isin(piece, [0, 29]) & (c[:, 2] > BELT_Z[0]) & (c[:, 2] < BELT_Z[1]) & (c[:, 1] < -0.10) & (np.abs(c[:, 0]) < 0.22)
armpit = np.zeros(len(f), bool) if ARMPIT is None else ((piece == 0) & (np.abs(c[:, 0]) > ARMPIT[0]) & (np.abs(c[:, 0]) < ARMPIT[1])
                                                         & (c[:, 2] > ARMPIT[2]) & (c[:, 2] < ARMPIT[3]))
keep = small | gold | mouth | sockets | soles | hems | belt | armpit
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep); np.save('work/piece.npy', piece)
np.save('work/gold.npy', gold)
print('GROUPS free', {k: int(((g == k) & ~keep).sum()) for k in range(11)}, 'keep', int(keep.sum()), 'of', len(f))
print('KEEP parts', {k: int(s.sum()) for k, s in (('small', small), ('gold', gold), ('mouth', mouth), ('sockets', sockets), ('soles', soles),
                                                   ('hems', hems), ('belt', belt), ('armpit', armpit))})
