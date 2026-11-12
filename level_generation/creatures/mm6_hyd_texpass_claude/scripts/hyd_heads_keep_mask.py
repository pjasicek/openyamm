"""keep_mask for the heads compose (texpass_heads.json): texels with no region (raw colour in every tier: mouths,
teeth, eyes, ivory) keep the approved colour, except large pale pieces (horns, throat plates), which take the new
paint like the skin. Reason: the compose's approved low band (sigma 4 texels) tints small features from their
neighbours, so the repaints' teeth turned red and head 5's mouth blotchy (review/shots, first compose).
Usage: hyd_heads_keep_mask.py [min pale texels 400] -> work/heads_keep_mask.png"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import hyd_heads

P = hyd_heads.PROJECT
MIN_PALE = int(sys.argv[1]) if len(sys.argv) > 1 else 400
MOUTH_GROW = 3
S = 2048
m = np.asarray(Image.open(P / 'textures/approved/heads_region_mask.png').convert('RGBA').resize((S, S), Image.NEAREST),
               np.float32) / 255
r = np.load(P / 'textures/approved/heads_raster2048.npz')
cov = r['tri_id'] >= 0
d = np.load(P / 'work/lod0_before_heads.npz')
prim = np.where(cov, d['prim'][np.maximum(r['tri_id'], 0)], -1)
mx = np.where(prim == 4, m[..., :3].max(-1), m.max(-1))     # HeadsC has three ramps: its alpha is no region
unmasked = cov & (mx < 0.5)
a = np.asarray(Image.open(P / 'textures/approved/heads_basecolor.png').convert('RGB'), np.float32)
mxc, mnc = a.max(-1), a.min(-1)
pale = unmasked & ((mxc - mnc) < 0.25 * np.maximum(mxc, 1)) & (mxc > 110)
lab, n = ndimage.label(pale)
size = np.bincount(lab.ravel())
big_pale = (lab > 0) & (size[lab] >= MIN_PALE)
keep = unmasked & ~big_pale
# red mouths inside ramped regions (head 3's gums): approved strongly red texels on every head but the red head 4,
# holes filled (teeth) and grown by MOUTH_GROW texels over the lip edge, within the same head
head_t, _ = hyd_heads.head_of_triangle(d)
hm = np.where(cov, head_t[np.maximum(r['tri_id'], 0)], 0)
red = cov & (hm != 4) & (a[..., 0] > 110) & (a[..., 0] > 1.7 * a[..., 1]) & (a[..., 0] > 1.7 * a[..., 2])
lab_r, _ = ndimage.label(red)
size_r = np.bincount(lab_r.ravel())
red = (lab_r > 0) & (size_r[lab_r] >= 30)
mouth = np.zeros_like(red)
for k in (1, 2, 3, 5):
    mk = ndimage.binary_fill_holes(red & (hm == k))
    mouth |= ndimage.binary_dilation(mk, iterations=MOUTH_GROW) & (hm == k)
keep |= mouth
Image.fromarray((keep * 255).astype(np.uint8)).save(P / 'work/heads_keep_mask.png')
print('MOUTH', round(float(mouth.sum() / cov.sum()), 3))
print('KEEP', round(float(keep.sum() / cov.sum()), 3), 'of heads texels; large pale left to the paint',
      round(float(big_pale.sum() / cov.sum()), 3), {k: round(float((keep & (hm == k)).sum() / (hm == k).sum()), 3)
                                                     for k in range(1, 6)})
