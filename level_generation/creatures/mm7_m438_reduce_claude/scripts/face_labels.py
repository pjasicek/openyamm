#!/usr/bin/env python3
"""Per-face labels of the welded source (dump_mesh.py order) for the m438 groups -> work/face_labels.npz:
piece / garment / finger (majority of the master's vertex labels, nearest rest vertex), head set (u > 0.5),
wound share (crimson texels of the base colour sampled at 10 points of the face's UV triangle), region share
(region mask R > 0.5: trousers, headband), z min (world, rest), dominant bone."""
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d = np.load('work/mesh_in.npz'); f = d['faces']; wuv = d['wuv'].reshape(-1, 3, 2)
m = np.load('work/master_pieces.npz'); sw = np.load('work/source_world.npy')
_, near = cKDTree(m['co']).query(sw)
lab = {k: m[k][near] for k in ('piece', 'garment', 'finger')}
maj = lambda a: np.array([np.bincount(r).argmax() for r in a[f]])
bc = np.asarray(Image.open('work/m438_basecolor_1k_head_atlas.png').convert('RGB'), np.float32)
rm = np.asarray(Image.open('work/m438_region_mask_head_atlas.png').convert('RGBA'), np.float32)
H, W = bc.shape[:2]
bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1/3, 1/3, 1/3], [.5, .5, 0], [0, .5, .5], [.5, 0, .5],
                 [2/3, 1/6, 1/6], [1/6, 2/3, 1/6], [1/6, 1/6, 2/3]])
uv = np.einsum('sk,fkc->fsc', bary, wuv)
px = np.clip((uv[..., 0] * W).astype(int), 0, W - 1); py = np.clip(((1 - uv[..., 1]) * H).astype(int), 0, H - 1)
c = bc[py, px]; r, g, b = c[..., 0], c[..., 1], c[..., 2]
crimson = (r > 1.7 * g + 4) & (r > 1.7 * b + 4) & (r > 25)
dark = c.max(-1) < 30
info = np.load('work/faces_info.npz')
np.savez('work/face_labels.npz', piece=maj(lab['piece']), garment=maj(lab['garment']),
         finger=np.max(lab['finger'][f], 1), head=wuv[..., 0].mean(1) > 0.5, wound=crimson.mean(1),
         dark=dark.mean(1), region=(rm[py, px, 0] > 127).mean(1), zmin=sw[f][..., 2].min(1), dom=info['dom'])
L = np.load('work/face_labels.npz')
for p in np.unique(L['piece']):
    s = L['piece'] == p
    print('PIECE', p, 'faces', int(s.sum()), 'garment', np.bincount(L['garment'][s]).argmax(), 'head', int(L['head'][s].sum()),
          'wound>0.3', int((L['wound'][s] > .3).sum()), 'anywound', int((L['wound'][s] > 0).sum()), 'region', int((L['region'][s] > .5).sum()),
          'finger', int((L['finger'][s] > 0).sum()), 'z<6cm', int((L['zmin'][s] < .06).sum()))
