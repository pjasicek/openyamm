#!/usr/bin/env python3
"""Per-face region labels for the per-region ladder (work/groups.npy) and the exact-keep mask (work/keep_base.npy).
MM7 Warlock (faces -y, wand in the left fist). Meshy fused body, gown, cape, hands and hair into one shell; after the
weld the separate pieces are the bare feet, eyes, earrings, neck ring and the arm/wrist bands. Faces are labelled from
the source project's runtime maps at each face's UV (merged atlas 2080x1024: body set at x 0-1024, head set at
1056-2080): material classes (1 skin, 2 hair, 8 cloth, 9 gold; head: 6 eye), the gown region mask (R) and the
lavender cape edge (base colour). Labels: 0 rest, 1 face skin, 2 hair (head and body sets), 3 right hand (open),
4 left hand (wand fist), 5 gown, 6 cape, 7 body skin (chest, shoulders, arms), 8 faces hidden in the rest pose (linings; work/visible.npy from vis_faces.py), 9 leg-weighted surface (the legs
inside the gown: Meshy's leg weights; a collapse joining them to robe-chain vertices stretched faces in Death).
Kept exactly: pieces of up to 250 faces, the bare feet (foot/toe-weighted faces and anything below 12 cm outside gown and cape), the left hand, gold texels (bodice cords,
waist and hem bands: thin painted trims bend under any collapse) and the lavender cape edge strip."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
T = '../mm7_m426_claude/textures/'
d = np.load('work/mesh_in.npz'); info = np.load('work/faces_info.npz'); f, v = d['faces'], d['verts']
c = v[f].mean(1); dom = info['dom']
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc); size = sizes[pc]
uv = d['wuv'].reshape(-1, 3, 2); p = np.concatenate([uv, uv.mean(1, keepdims=True)], 1)    # 3 corners + centroid
ua = p[..., 0]; head = ua.mean(1) > 0.5
us = np.where(head[:, None], (ua * 2080 - 1056) / 1024, ua * 2080 / 1024)
x = np.clip((us * 1024).astype(int), 0, 1023); y = np.clip(((1 - p[..., 1]) * 1024).astype(int), 0, 1023)
bc = np.asarray(Image.open(T + 'm426_material_classes.png')); hc = np.asarray(Image.open(T + 'm426_head_material_classes.png'))
gm = np.asarray(Image.open(T + 'm426_region_mask.png'))[..., 0] / 255.0
base = np.asarray(Image.open(T + 'm426_basecolor_1k.png').convert('HSV')).astype(float) / 255
cls = np.where(head[:, None], hc[y, x], bc[y, x])
maj = lambda k: (cls == k).sum(1) >= 2
gold = (~head) & ((cls == 9).any(1)) & ~((cls == 2).sum(1) >= 2)
hb = base[y, x]; lav = (~head) & (((hb[..., 0] > 0.6) & (hb[..., 0] < 0.8) & (hb[..., 1] < 0.45) & (hb[..., 2] > 0.55)).sum(1) >= 2)
gown = (~head) & (gm[y, x].mean(1) > 0.5)
g = np.zeros(len(f), int)
g[head & maj(1)] = 1
g[maj(2)] = 2
g[(~head) & maj(8) & ~gown] = 6
g[gown] = 5
g[(~head) & maj(1)] = 7
copper = (~head) & (((hb[..., 0] > 0.01) & (hb[..., 0] < 0.11) & (hb[..., 1] > 0.5) & (hb[..., 2] > 0.2)).sum(1) >= 2)
g[(g == 0) & copper & (c[:, 2] > 0.9)] = 2                     # body-set hair the class map left unlabelled
vis = np.load('work/visible.npy')
g[~vis & (g != 2) & (g != 1)] = 8                              # hidden in the rest pose: the legs inside the gown, linings
legw = np.isin(dom, ['B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf'])
g[legw & (g != 1) & (g != 2)] = 9                              # leg-weighted surface (legs inside the gown, seen in the slit):
                                                               # its own group, collapses never join leg and robe-chain vertices
g[np.isin(dom, ['B_R_Hand']) | np.char.startswith(dom.astype(str), 'B_R_Finger')] = 3
lhand = np.isin(dom, ['B_L_Hand']) | np.char.startswith(dom.astype(str), 'B_L_Finger')
g[lhand] = 4
feet = (np.isin(dom, ['B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0']) | (c[:, 2] < 0.12)) & (g != 5) & (g != 6)
gold &= ~(copper & (c[:, 1] > 0.0))                             # hair highlights at the back are classed gold
keep = (size <= 250) | feet | lhand | gold | lav
np.save('work/groups.npy', g); np.save('work/keep_base.npy', keep)
print('GROUPS free', {k: int(((g == k) & ~keep).sum()) for k in range(10)}, 'keep', int(keep.sum()),
      'of', len(f), '| gold', int(gold.sum()), 'lavender', int(lav.sum()), 'feet', int(feet.sum()), 'small', int((size <= 250).sum()))
