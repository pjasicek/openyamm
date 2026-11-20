#!/usr/bin/env python3
"""Per-face piece labels of the m322 rest mesh (work/mesh_in.npz): the production master's Smart Topology shells
(work/prod_pieces.npz from dump_prod_pieces.py, nearest rest vertex, majority per face), then the skin shell P00 split
by bone weights, the region mask (R trousers, G hair) and the base colour:
1 skin-shell rest (bare arms, shoulders, belly, neck), 2 head skin (B_Head/B_Neck dominated above the neck),
3 hair P01, 4 trousers (P00 faces with region mask R > 0.5), 5 boots (P00 below 0.42 m, not trousers),
6 vest (P00 torso faces painted dark leather), 7 hands P02/P03, 8 eyes and mouth bits P04/P05/P08/P09/P11,
9 vest lacing P06/P07/P10/P12 and every other small piece (studs, trouser grommets).
work/soles.npy: boot faces below 6 cm; work/regmask.npy: per-face mean region mask; work/facecol.npy: mean base colour.
Usage: m322_pieces.py [source glb]"""
import io, json, struct, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
P = np.load('work/prod_pieces.npz'); dist, idx = cKDTree(P['co']).query(v)
print('map max distance mm', round(float(dist.max()) * 1000, 4))
vp = P['piece'][idx]
fp = np.array([np.bincount(vp[t]).argmax() for t in f])
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
col = lambda keys: W[:, [i for i, n in enumerate(names) if any(k in n for k in keys)]].sum(1)
headw = col(('B_Head', 'B_Neck')); torso = col(('Spine', 'Clavicle')); legw = col(('Thigh', 'Calf', 'Foot', 'Toe'))
c = v[f].mean(1)
raw = open(sys.argv[1] if len(sys.argv) > 1 else 'work/mm7_m322_source_pre_reduce.glb', 'rb').read()
nj = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + nj]); binary = raw[28 + nj:]
def image(i):
    im = doc['images'][doc['textures'][i]['source']]; bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
    return Image.open(io.BytesIO(binary[o:o + bv['byteLength']]))
mat = doc['materials'][0]
mask = np.asarray(image(mat['extras']['openyamm_region_mask']['index']).convert('RGB'), np.float32) / 255
base = np.asarray(Image.open('work/basecolor.png').convert('RGB'), np.float32) / 255
uv = d['wuv'].reshape(-1, 3, 2)
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
pts = np.einsum('kj,fjc->fkc', bc, uv)
def sample(img):
    H, Wd = img.shape[:2]
    px = np.clip((pts[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
    return img[py, px].mean(1)
rm = sample(mask); fc = sample(base)
val = fc.max(1); sat = (fc.max(1) - fc.min(1)) / np.maximum(fc.max(1), 1e-6)
reg = np.full(len(f), 1)
skin = fp == 0
fh = headw[f].mean(1); ft = torso[f].mean(1); fl = legw[f].mean(1)
reg[skin & (fh > 0.5) & (c[:, 2] > 1.42)] = 2
reg[skin & (rm[:, 0] > 0.5)] = 4
reg[skin & (reg == 1) & (c[:, 2] < 0.42)] = 5
reg[skin & (reg == 1) & (ft > 0.5) & (val < 0.45) & (c[:, 2] > 0.85)] = 6
reg[fp == 1] = 3
reg[np.isin(fp, [2, 3])] = 7
reg[np.isin(fp, [4, 5, 8, 9, 11])] = 8
reg[~np.isin(fp, [0, 1, 2, 3, 4, 5, 8, 9, 11])] = 9
soles = (reg == 5) & (c[:, 2] < 0.06)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles); np.save('work/regmask.npy', rm); np.save('work/facecol.npy', fc)
np.save('work/prodpiece.npy', fp)
nm = {1: 'skin rest', 2: 'head skin', 3: 'hair', 4: 'trousers', 5: 'boots', 6: 'vest', 7: 'hands', 8: 'eyes+mouth', 9: 'lacing+small'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'soles', int(soles.sum()))
print('small pieces', len(set(fp[reg == 9].tolist())), 'trouser faces with partial mask (0.05-0.95):', int(((reg == 4) | (skin & (rm[:, 0] > 0.05))).sum() - ((rm[:, 0] > 0.95) & skin).sum()))
