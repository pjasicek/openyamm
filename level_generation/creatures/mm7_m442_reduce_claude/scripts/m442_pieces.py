#!/usr/bin/env python3
"""Per-face labels of the m442 rest mesh (work/mesh_in.npz) from the production master's 'piece' attribute
(work/master_pieces.npz, nearest rest vertex, face majority) -> work/pieces.npy. Smart Topology shells: 0 the fused body
(head, ponytail, vest, blouse with the wide sleeves, sash, trousers, boots), 1/2 hands L/R, 3 fringe, 4/5 eyes, 6/7/8
ribbon bow and tails, 9.. eyelets and toggles (< 120 faces each), 45 ribbon part. Also work/soles.npy (body faces below
6 cm), work/handw.npy (faces touching a vertex with hand + finger weight > 0.3), work/headset.npy (faces in the head
texture set: merged atlas u > 0.51), work/regmask.npy (region mask R cloth, G hair per face, 4 samples) and
work/armw.npy (arm share of the face's vertices: upper arm, forearm and twist bones)."""
import io, json, struct
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
m = np.load('work/master_pieces.npz'); dist, idx = cKDTree(m['co']).query(v)
print('MAP max vertex distance mm', round(float(dist.max()) * 1000, 4))
vp = m['piece'][idx]; fp = np.array([np.bincount(vp[t]).argmax() for t in f])
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if 'Hand' in n or 'Finger' in n]].sum(1)
arm = W[:, [i for i, n in enumerate(names) if 'UpperArm' in n or 'Forearm' in n]].sum(1)
handw = (hand[f] > 0.3).any(1); armw = arm[f].mean(1)
soles = (fp == 0) & (v[f][:, :, 2].max(1) < 0.06)
uv = d['wuv'].reshape(-1, 3, 2); headset = uv[:, :, 0].mean(1) > 0.51
np.save('work/pieces.npy', fp); np.save('work/soles.npy', soles); np.save('work/handw.npy', handw)
np.save('work/headset.npy', headset); np.save('work/armw.npy', armw)
for p in sorted(set(fp.tolist())):
    if p < 9 or p == 45:
        print('PIECE', p, int((fp == p).sum()))
print('SMALL pieces (eyelets/toggles)', int(((fp >= 9) & (fp != 45)).sum()), 'faces')
print('SOLES', int(soles.sum()), 'HANDW', int(handw.sum()), 'HEADSET', int(headset.sum()))
raw = open('work/mm7_m442_source_pre_reduce.glb', 'rb').read()
nj = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + nj]); binary = raw[28 + nj:]
ti = doc['materials'][0]['extras']['openyamm_region_mask']['index']; im = doc['images'][doc['textures'][ti]['source']]
bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
mask = np.asarray(Image.open(io.BytesIO(binary[o:o + bv['byteLength']])).convert('RGB'), np.float32) / 255
H, Wd = mask.shape[:2]
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
pts = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((pts[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
rm = mask[py, px].mean(1); np.save('work/regmask.npy', rm)
print('REGMASK cloth faces', int((rm[:, 0] > .5).sum()), 'hair faces', int((rm[:, 1] > .5).sum()))
