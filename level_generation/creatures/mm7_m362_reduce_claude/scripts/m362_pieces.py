#!/usr/bin/env python3
"""Per-face piece labels of the m362 rest mesh (work/mesh_in.npz) from the production master's Smart Topology 'piece'
attribute (work/master_pieces.npz, nearest rest vertex, majority per face) -> work/pieces.npy: 1 head/neck/chest skin
P00, 2 doublet P04, 3 left hand P01, 4 right hand P02, 5 hair P07 + strands, 6 breeches P03, 7 boots P05/P06, 8 shirt
sleeves P10/P11 + cuffs P27/P30, 9 shoulder rolls P08/P09, 10 doublet skirt P12, shirt collar P14, belt P15, boot cuffs
P21/P22, 11 sheathed rapier (hilt P13/P24/P25/P31/P32, scabbard P17), 12 eyes and mouth P16/P18/P29/P45, 13 fittings
(belt studs P37/P38, chest laces P41-P44); work/soles.npy: boot faces below 6 cm; work/regmask.npy: per-face mean
region mask (R doublet and shoulder rolls, G hair, B stubble) sampled at 4 points per face from the GLB's region mask."""
import io, json, struct, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']
m = np.load('work/master_pieces.npz'); dist, idx = cKDTree(m['co']).query(v)
print('MAP master -> mesh: max vertex distance mm', round(float(dist.max()) * 1000, 4))
pv = m['piece'][idx][f]
fp = np.array([np.bincount(r).argmax() for r in pv])
LAB = {0: 1, 4: 2, 1: 3, 2: 4, 7: 5, 19: 5, 20: 5, 23: 5, 26: 5, 28: 5, 33: 5, 34: 5, 35: 5, 36: 5, 39: 5, 40: 5,
       3: 6, 5: 7, 6: 7, 10: 8, 11: 8, 27: 8, 30: 8, 8: 9, 9: 9, 12: 10, 14: 10, 15: 10, 21: 10, 22: 10,
       13: 11, 17: 11, 24: 11, 25: 11, 31: 11, 32: 11, 16: 12, 18: 12, 29: 12, 45: 12, 37: 13, 38: 13, 41: 13, 42: 13,
       43: 13, 44: 13}
reg = np.array([LAB[int(x)] for x in fp])
soles = (reg == 7) & (v[f].mean(1)[:, 2] < 0.06)
raw = open(sys.argv[1] if len(sys.argv) > 1 else 'work/mm7_m362_source_pre_reduce.glb', 'rb').read()
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
nm = {1: 'skin head/chest', 2: 'doublet', 3: 'hand L', 4: 'hand R', 5: 'hair', 6: 'breeches', 7: 'boots', 8: 'sleeves',
      9: 'shoulder rolls', 10: 'skirt/collar/belt/cuffs', 11: 'rapier', 12: 'eyes/mouth', 13: 'fittings'}
print({nm[k]: int((reg == k).sum()) for k in nm}, 'soles', int(soles.sum()))
print('mask: doublet R>0.5', int((rm[:, 0] > .5).sum()), 'hair G>0.5', int((rm[:, 1] > .5).sum()), 'stubble B>0.5', int((rm[:, 2] > .5).sum()),
      'R edges', int(((rm[:, 0] > .1) & (rm[:, 0] < .9)).sum()), 'G edges', int(((rm[:, 1] > .1) & (rm[:, 1] < .9)).sum()),
      'B edges', int(((rm[:, 2] > .1) & (rm[:, 2] < .9)).sum()))
