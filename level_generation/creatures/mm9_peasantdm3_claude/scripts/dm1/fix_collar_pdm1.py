#!/usr/bin/env python3
"""Tunic collar rim and forearm skin (second part below) (2026-11-01, head close-ups): the body retexture painted the inner rim of the tunic's neckline
(body set, round the neck above 0.88 m) neck-skin pink, which read as a pale band between the beard and the tunic.
Skin-coloured body texels there take the tunic's own navy wool (median of the blue tunic texels just below the
neckline), shaded darker (inside the collar), with 35 % of the paint's fine detail; soft mask, gutters refilled.
Then tiers_pdm1.py picks them up in the tunic region. Rewrites textures/pdm1_tp_basecolor_graded.png (backup
textures/pdm1_tp_basecolor_graded_precollar.png on the first run). Usage (project folder): fix_collar_pdm1.py <export glb>"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 2048
pos, cov = texel_positions(sys.argv[1], 'PeasantDM1', N)
y = np.nan_to_num(pos[..., 1]); x = np.nan_to_num(pos[..., 0])
f = Path('textures/pdm1_tp_basecolor_graded.png')
bk = Path('textures/pdm1_tp_basecolor_graded_precollar.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB'), float)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
lum = img @ [0.299, 0.587, 0.114]
near = cov & (np.abs(x) < 0.2) & (y > 0.86)
# pink skin only (lum > 125, blue > 60): the medallion's brown leather cord has the same chroma but is darker
skin = near & (r > 110) & (r > g * 1.2) & (g > b * 1.05) & (lum > 125) & (b > 60)
skin = ndimage.binary_dilation(ndimage.binary_closing(skin, iterations=2), iterations=2) & near
blue = cov & (np.abs(x) < 0.2) & (y > 0.82) & (y < 0.88) & (b > r) & (b > 30)
ref = np.median(img[blue], 0) * 0.75
w = ndimage.gaussian_filter(skin.astype(float), 1.5) * near
detail = np.clip(lum - ndimage.gaussian_filter(lum, 3), -8, 8)[..., None] * 0.35
out = img * (1 - w[..., None]) + (ref[None, None] + detail) * w[..., None]
gut = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
print('FIXCOLLAR navy ref', ref.round(), 'texels', int((w > 0.5).sum()))

# ---- forearm skin (2026-11-01, hand sheet): the body retexture painted the bare forearms (between the linen undersleeve
# and the hand) nearly white-pink ([255, 179, 137] after grading) where the face is [208, 124, 89], so the grafted hands
# (graded to the face) met a pale forearm at a visible wrist seam, with a dark wedge of the painted wrist band left on
# the cuff faces. Forearm skin texels (t 0.45-1.15 along forearm -> hand, skin chroma, bright) and the dark cuff texels
# within 3 cm of the hand joint take the tier-A face skin (median cheek colour of textures/pdm1_tp_head_basecolor.png's
# source paint), keeping 50 % of their own luminance detail; written as textures/pdm1_forearm_skin_mask.png for
# tiers_pdm1.py (region B: tier B's darker face skin).
from pygltflib import GLTF2
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
a_ = g.accessors[sk.inverseBindMatrices]; bv = g.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
J = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}
img = out.copy()
r, g_, b = img[..., 0], img[..., 1], img[..., 2]
lum = img @ [0.299, 0.587, 0.114]
P = np.nan_to_num(pos)
fore = np.zeros(cov.shape, bool)
for s in 'LR':
    h, fa = J[f"Bip01 {s} Hand"], J[f"Bip01 {s} Forearm"]
    L = np.linalg.norm(h - fa); ax = (h - fa) / L
    t = (P - fa) @ ax / L
    d = np.linalg.norm(P - h, axis=-1)
    side = np.sign(P[..., 0]) == np.sign(h[0])
    skin_s = cov & side & (t > 0.45) & (t < 1.15) & (r > g_ * 1.3) & (g_ > b * 1.15) & (lum > 110)
    cuff = cov & side & (d < 0.03) & (lum < 90)
    fore |= skin_s | cuff
fore = ndimage.binary_opening(ndimage.binary_closing(fore, iterations=2), iterations=1) & cov
FACE = np.array([208.0, 124.0, 89.0])
lf = lum[fore & (lum > 110)]
rel = np.clip(lum / max(np.median(lf), 1), 0.6, 1.25) ** 0.5
w2 = ndimage.gaussian_filter(fore.astype(float), 1.0) * cov
skin_col = FACE[None, None] * rel[..., None]
out = img * (1 - w2[..., None]) + skin_col * w2[..., None]
gut = ndimage.binary_dilation(w2 > 0.02, iterations=8) & ~cov
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
Image.fromarray(np.uint8(np.clip(w2, 0, 1) * 255)).save('textures/pdm1_forearm_skin_mask.png')
print('FIXFOREARM texels', int((w2 > 0.5).sum()), 'paint median was', np.median(img[fore & (lum > 110)], 0).round())
