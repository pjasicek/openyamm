#!/usr/bin/env python3
"""Tunic collar rim (DM1 lesson, head close-ups): the body retexture painted the inner rim of the tunic's neckline (body
set, round the neck: within 16 cm of the neck joint's vertical axis, above 0.86 m) neck-skin pink, which reads as a pale
band between the beard and the tunic. Skin-coloured body texels there take the tunic's own dark knit (median of the
tunic texels just below the neckline), shaded darker (inside the collar), with 35 % of the paint's fine detail; soft
mask, gutters refilled. tiers_pdm2.py then picks them up in the tunic region. Rewrites
textures/pdm2_tp_basecolor_graded.png (backup textures/pdm2_tp_basecolor_graded_precollar.png on the first run; run
after sleeve_paint_fix.py, which writes the same file). Usage (project folder): fix_collar_pdm2.py <export glb>"""
import os, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
N = 2048
pos, cov = texel_positions(sys.argv[1], 'PeasantDM2', N)
y = np.nan_to_num(pos[..., 1]); x = np.nan_to_num(pos[..., 0]); z = np.nan_to_num(pos[..., 2])
from pygltflib import GLTF2
GL = GLTF2().load(sys.argv[1]); blob = GL.binary_blob()
sk = GL.skins[0]; names = [GL.nodes[j].name for j in sk.joints]
a_ = GL.accessors[sk.inverseBindMatrices]; bv = GL.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
NK = np.linalg.inv(IBM[names.index('Bip01 Neck')].T)[:3, 3]
rad = np.hypot(x - NK[0], z - NK[2])
f = Path('textures/pdm2_tp_basecolor_graded.png')
bk = Path('textures/pdm2_tp_basecolor_graded_precollar.png')
if not bk.exists():
    shutil.copyfile(f, bk)
img = np.asarray(Image.open(bk).convert('RGB'), float)
r, g, b = img[..., 0], img[..., 1], img[..., 2]
lum = img @ [0.299, 0.587, 0.114]
from scipy.spatial import cKDTree
def _acc(i):
    a = GL.accessors[i]; bv_ = GL.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    return np.frombuffer(blob, np.float32, a.count * n, (bv_.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
hp = np.concatenate([_acc(pr.attributes.POSITION) for m in GL.meshes for pr in m.primitives
                     if GL.materials[pr.material].name == 'PeasantDM2Head'][:1])
ring = hp[(hp[:, 1] < float(os.environ.get('NECK_BASE', 0.935))) & (np.abs(hp[:, 0]) < 0.17)]
BAND = float(os.environ.get('BAND', 0.03))
dist = np.full(cov.shape, 9.0)
dist[cov] = cKDTree(ring).query(np.nan_to_num(pos)[cov])[0]
near = cov & (dist < float(os.environ.get('NEAR', 0.05)))   # (a 16 cm ring round the neck axis took knit highlights on the chest: a dark yoke)
skin = near & (r > 110) & (r > g * 1.2) & (g > b * 1.05) & (lum > 100) & (b > 50)
skin = ndimage.binary_dilation(ndimage.binary_closing(skin, iterations=2), iterations=2) & near
# the knitted neckline band was painted with bright orange specks ("leopard" rim, head close-ups): body texels within
# BAND m of the neck opening (the head set's lowest neck vertices, where the neck meets the tunic) take the dark knit
# too. (A 14.5 cm ring round the neck axis took the knit's own light yarns on the chest: a dark yoke.)
mx_, mn_ = img.max(-1), img.min(-1)
sat_ = np.where(mx_ > 0, (mx_ - mn_) / np.maximum(mx_, 1), 0)
speck = cov & (dist < BAND) & (lum > 55) & (sat_ > 0.35) & (r > b * 1.4)
band = ndimage.binary_closing(speck, iterations=3) & cov & (dist < BAND)
skin = skin | band
print('FIXCOLLAR ring verts', len(ring), 'band texels', int(band.sum()))
knit = cov & (rad < 0.2) & (y > 0.80) & (y < 0.86) & (lum < 70)
ref = np.median(img[knit], 0) * 0.8
w = ndimage.gaussian_filter(skin.astype(float), 1.5) * near
detail = np.clip(lum - ndimage.gaussian_filter(lum, 3), -8, 8)[..., None] * 0.35
out = img * (1 - w[..., None]) + (ref[None, None] + detail) * w[..., None]
gut = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
print('FIXCOLLAR knit ref', ref.round(), 'texels', int((w > 0.5).sum()))

