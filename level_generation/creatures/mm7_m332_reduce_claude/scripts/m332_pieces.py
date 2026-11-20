#!/usr/bin/env python3
"""Per-face piece labels of the m332 rest mesh (work/mesh_in.npz) from the production master's Smart Topology 'piece'
attribute (work/master_pieces.npz, nearest rest vertex, majority per face) -> work/pieces.npy: 1 skin shell P00 (body,
head with painted hair, bracers, shoes), 2 vest P01, 3 left hand P02, 4 right hand P03, 5 ponytail P04, 6 belt P05,
7 buckle P15, 8 dagger and sheath P06/P07/P08/P23/P25/P31, 9 right upper-arm band P09, 10 vest studs, 11 lacing
crosses, 12 eyes P28/P29; work/soles.npy: skin-shell faces below 6 cm (the shoes); work/regmask.npy: per-face mean
region mask (R tights, G hair) sampled at 4 points per face from the GLB's region mask."""
import io, json, struct, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
m = np.load('work/master_pieces.npz'); dist, idx = cKDTree(m['co']).query(v)
print('MAP master -> mesh: max vertex distance mm', round(float(dist.max()) * 1000, 4))
pv = m['piece'][idx][f]
fp = np.array([np.bincount(r).argmax() for r in pv])
LAB = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 15: 7, 6: 8, 7: 8, 8: 8, 23: 8, 25: 8, 31: 8, 9: 9,
       10: 10, 11: 10, 12: 10, 13: 10, 14: 10, 16: 10, 17: 10, 19: 10, 18: 11, 20: 11, 21: 11, 22: 11, 24: 11, 26: 11,
       27: 11, 30: 11, 28: 12, 29: 12}
reg = np.array([LAB[int(x)] for x in fp])
soles = (reg == 1) & (v[f].mean(1)[:, 2] < 0.06)
raw = open(sys.argv[1] if len(sys.argv) > 1 else 'work/mm7_m332_source_pre_reduce.glb', 'rb').read()
nj = struct.unpack_from('<I', raw, 12)[0]; doc = json.loads(raw[20:20 + nj]); binary = raw[28 + nj:]
ti = doc['materials'][0]['extras']['openyamm_region_mask']['index']; im = doc['images'][doc['textures'][ti]['source']]
bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
mask = np.asarray(Image.open(io.BytesIO(binary[o:o + bv['byteLength']])).convert('RGB'), np.float32) / 255
H, Wd = mask.shape[:2]; uv = d['wuv'].reshape(-1, 3, 2)
bc = np.array([[1 / 3, 1 / 3, 1 / 3], [.6, .2, .2], [.2, .6, .2], [.2, .2, .6]])
pts = np.einsum('kj,fjc->fkc', bc, uv)
px = np.clip((pts[..., 0] % 1) * Wd, 0, Wd - 1).astype(int); py = np.clip((1 - pts[..., 1]) * H, 0, H - 1).astype(int)
rm = mask[py, px].mean(1)
np.save('work/pieces.npy', reg); np.save('work/soles.npy', soles); np.save('work/regmask.npy', rm)
nm = {1: 'skin shell', 2: 'vest', 3: 'hand L', 4: 'hand R', 5: 'ponytail', 6: 'belt', 7: 'buckle', 8: 'dagger',
      9: 'arm band', 10: 'studs', 11: 'lacing', 12: 'eyes'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'soles', int(soles.sum()))
print('skin faces: tights (R>0.5)', int(((reg == 1) & (rm[:, 0] > .5)).sum()), 'hair paint (G>0.5)', int(((reg == 1) & (rm[:, 1] > .5)).sum()),
      'mixed R edge (0.1<R<0.9)', int(((reg == 1) & (rm[:, 0] > .1) & (rm[:, 0] < .9)).sum()),
      'mixed G edge', int(((reg == 1) & (rm[:, 1] > .1) & (rm[:, 1] < .9)).sum()))
