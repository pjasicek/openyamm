#!/usr/bin/env python3
"""Read-only probe: per head-shell face, hair weight (head region mask R) and collar weight (G) sampled at the UV centroid and
corners; prints counts by region and position to size the exact face set."""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_phom1.glb', 'PHOM1')
def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))
M = {m['name']: m for m in doc['materials']}
mask = np.asarray(image(M['PHOM1Head_A']['extras']['openyamm_region_mask']['index']).convert('RGBA'), float) / 255
print('mask', mask.shape, 'channel means', mask.reshape(-1, 4).mean(0).round(3))
d = D['PHOM1Head_A']; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]; cs = np.bincount(fl); shell = fl == cs.argmax()
H, W_ = mask.shape[:2]
def samp(uv):
    x = np.clip((uv[..., 0] * W_).astype(int), 0, W_ - 1); y = np.clip((uv[..., 1] * H).astype(int), 0, H - 1)
    return mask[y, x]
bary = np.array([[1/3, 1/3, 1/3], [.7, .15, .15], [.15, .7, .15], [.15, .15, .7]])
uvs = np.einsum('kc,fcd->fkd', bary, U[T])
s = samp(uvs)            # F x 4 x 4
hair = s[..., 0].max(1); hairmin = s[..., 0].min(1); col = s[..., 1].max(1)
C = P[T].mean(1)
S = shell
print('shell faces', S.sum())
for th in (0.05, 0.2, 0.5, 0.8):
    print(f' hair max>{th}: {(S & (hair > th)).sum()}  hair min>{th}: {(S & (hairmin > th)).sum()}')
print(' collar>0.2', (S & (col > 0.2)).sum())
hm = S & (hairmin > 0.5)
for name, m in (('front z>0.05', C[:, 2] > 0.05), ('back z<-0.05', C[:, 2] < -0.05), ('top y>2.1', C[:, 1] > 2.1), ('sides |x|>0.13', np.abs(C[:, 0]) > 0.13)):
    print(f' hair(all>.5) & {name}: {(hm & m).sum()}   skin(<.05) & {name}: {(S & (hair < 0.05) & m).sum()}')
print('shell y range', C[S, 1].min().round(3), C[S, 1].max().round(3), 'neck below 1.9', (S & (C[:, 1] < 1.9)).sum())
np.save(HERE / 'work' / 'head_hair.npy', np.c_[hair, hairmin, col])
