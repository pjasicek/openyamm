#!/usr/bin/env python3
"""Per-face piece labels of the 7m452 rest mesh (work/mesh_in.npz) from the production master's 'piece' attribute
(work/master_pieces.npz, nearest rest vertex, face majority) -> work/pieces.npy (Smart Topology shells: 0 torso+arms,
1 head with topknot and ears, 2 trousers, 3 tunic skirt with belt, 4/5 hands, 6/7 boots, 8/9 bracers, 10 buckle,
11/12 eyes, 13 mouth, 14 neck bead), work/soles.npy (boot faces below 6 cm), work/handw.npy (faces touching a vertex
with hand + finger weight > 0.3)."""
import numpy as np
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
m = np.load('work/master_pieces.npz'); dist, idx = cKDTree(m['co']).query(v)
print('MAP max vertex distance mm', round(float(dist.max()) * 1000, 4))
vp = m['piece'][idx]; fp = np.array([np.bincount(vp[t]).argmax() for t in f])
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if 'Hand' in n or 'Finger' in n]].sum(1)
handw = (hand[f] > 0.3).any(1)
soles = np.isin(fp, [6, 7]) & (v[f][:, :, 2].max(1) < 0.06)
np.save('work/pieces.npy', fp); np.save('work/soles.npy', soles); np.save('work/handw.npy', handw)
NAMES = ['torso+arms', 'head', 'trousers', 'skirt+belt', 'hand L', 'hand R', 'boot L', 'boot R', 'bracer L', 'bracer R',
         'buckle', 'eye', 'eye', 'mouth', 'bead']
for p in sorted(set(fp.tolist())):
    print('PIECE', p, NAMES[p] if p < len(NAMES) else '?', int((fp == p).sum()))
print('SOLES', int(soles.sum()), 'HANDW', int(handw.sum()))
# region mask (material extras openyamm_region_mask: R tunic, G trousers, B hair) sampled per face at 4 points
import io, json, struct
from PIL import Image
raw = open('work/mm7_7m452_source_pre_reduce.glb', 'rb').read()
nj = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + nj]); binary = raw[28 + nj:]
ti = doc['materials'][0]['extras']['openyamm_region_mask']['index']; im = doc['images'][doc['textures'][ti]['source']]
bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
mask = np.asarray(Image.open(io.BytesIO(binary[o:o + bv['byteLength']])).convert('RGB'), np.float32) / 255
H, Wd = mask.shape[:2]; uv = d['wuv'].reshape(-1, 3, 2)
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
pts = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((pts[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
rm = mask[py, px].mean(1); np.save('work/regmask.npy', rm)
print('REGMASK tunic faces', int((rm[:, 0] > .5).sum()), 'of torso piece', int(((rm[:, 0] > .5) & (fp == 0)).sum()))
