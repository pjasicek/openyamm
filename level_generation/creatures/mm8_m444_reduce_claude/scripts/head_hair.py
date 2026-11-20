#!/usr/bin/env python3
"""Smuggler facial-hair colour fix (user review 2026-10-19: "his head facial hair color and beard dont agree"; also in
the installed model). The beard mesh is ginger brown (head class 2: linear RGB 0.165/0.065/0.014, luminance 0.08), but
the head texture paints the moustache, chin/cheek stubble, sideburns and the short scalp hair on the sides and back as
pale skin-tone strands (skin luminance 0.31). Hair texels are found by their strand texture: the local contrast of
fine luminance detail (high-pass at sigma 2 px, RMS over sigma 3 px) is high in painted hair and low on smooth skin.
hair = smoothstep(REA_HAIR_LO, REA_HAIR_HI) of that contrast on skin texels, feathered (Gaussian sigma
REA_HAIR_FEATHER px) and kept off the eyes, mouth, cloth classes and the region mask (tiers B/C stay consistent: the
head is not ramped outside the collar). Each hair texel moves towards the beard colour at its own strand detail:
target = beard median * (luminance / local mean luminance over sigma 6 px), weight = hair * REA_HAIR_STRENGTH.
Rest positions per texel (head_posmap.py) shape three zones: texels within 1.2 cm of the beard mesh go to the full
weight (the chin and jaw where the beard meets the face: no seam), the moustache (a soft drooping arc over the mouth,
3.4 cm half-width) gets at least weight 0.8, and hair fades out down the back of the neck below the nape
(z 1.53 -> 1.50), where the painted strands ran into the collar. Skin-pale patches painted on the beard mesh itself
(local mean luminance 1.6-2.6x the beard's) take the beard colour too. The lips (the mouth pieces, guarded by 2-4 mm
at the chin junction) stay skin. The atlas gutter around each chart takes the weight of its nearest chart texel, so
mips and seams match.
Usage: head_hair.py <atlas basecolor.png> <out.png> -> also work/head_hair_weight.png"""
import os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X0 = 1056                                                           # head image origin in the 2080x1024 atlas
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
W = np.array([.2126, .7152, .0722])
env = lambda k, d: float(os.environ.get(k, d))
atlas = np.asarray(Image.open(sys.argv[1]).convert('RGB')).copy()
H = lin(atlas[:, X0:].astype(np.float64) / 255)
cls = np.asarray(Image.open(os.path.join(HERE, '..', 'mm8_m444_claude', 'textures', 'smuggler_head_material_classes.png')))
mask = np.asarray(Image.open(os.path.join(HERE, 'work', 'regionmask.png')).convert('RGBA'))[:, X0:, 0]
L = H @ W
hp = L - gaussian_filter(L, 2); contrast = np.sqrt(gaussian_filter(hp ** 2, 3))
lo, hi = env('REA_HAIR_LO', '0.04'), env('REA_HAIR_HI', '0.09')
u = np.clip((contrast - lo) / (hi - lo), 0, 1); hair = u * u * (3 - 2 * u)
skin = (cls == 1) & (mask == 0)
hair = gaussian_filter(hair * skin, env('REA_HAIR_FEATHER', '3')) * gaussian_filter(skin.astype(float), 1.5)
hair[~((cls == 1) | (cls == 2)) & (cls != 0)] = 0
hair[mask > 0] = 0
P = np.load(os.path.join(HERE, 'work', 'head_posmap.npz')); pos, valid, fcls = P['pos'], P['valid'], P['fcls']
_, (vy, vx) = distance_transform_edt(~valid, return_indices=True); pos = pos[vy, vx]; fcls = fcls[vy, vx]
from scipy.spatial import cKDTree
sm = lambda x, a, b: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
d = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); fv = d['verts'][d['faces']]; fuv = d['wuv'].reshape(-1, 3, 2)
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
f = d['faces']; e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]); n = len(d['verts'])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; hd = (fuv[..., 0] * 2080 >= X0 - 1).all(1); sizes = np.bincount(pc)
mouth = np.unique(f[hd & (sizes[pc] < 100) & (fv[:, :, 2].mean(1) < 1.53)])        # the two mouth pieces
lips = cKDTree(d['verts'][mouth]).query(pos.reshape(-1, 3))[0].reshape(pos.shape[:2])
beard_pts = pos[valid & (fcls == 2)][::7]
db = cKDTree(beard_pts).query(pos.reshape(-1, 3))[0].reshape(pos.shape[:2])
cx = -0.0085; x, y, z = pos[..., 0] - cx, pos[..., 1], pos[..., 2]
junction = (1 - sm(db, .006, .012)) * (fcls == 1) * sm(lips, .002, .004)
mx = (x + .0065) / .034; mz = (z - (1.527 - .012 * mx ** 2)) / .0085      # drooping arc over the mouth (centre x -6.5 mm)
moustache = .8 * (1 - sm(np.sqrt(mx ** 2 + mz ** 2), .55, 1.25)) * sm(-y, .065, .075) * sm(lips, .004, .007)
nape = 1 - sm(y, 0, .04) * (1 - sm(z, 1.50, 1.53))
zone_ok = ((cls == 1) | (cls == 2) | (cls == 0)) & (mask == 0)
beard_lum = np.median(L[cls == 2])
pale_beard = gaussian_filter((cls == 2) * sm(gaussian_filter(L, 3) / beard_lum, 1.6, 2.6), 1.5) * (cls == 2)
hair = np.maximum(hair * nape, np.maximum(np.maximum(junction, moustache), pale_beard) * zone_ok)
used = cls != 0
_, (iy, ix) = distance_transform_edt(~used, return_indices=True)
hair = np.where(used, hair, hair[iy, ix])
beard = np.median(H[cls == 2], 0)
detail = L / np.maximum(gaussian_filter(L, 6), 1e-4)
target = beard[None, None] * np.clip(detail, 0.4, 2.0)[..., None]
w = (np.clip(hair, 0, 1) * env('REA_HAIR_STRENGTH', '0.9'))[..., None]
out = H * (1 - w) + target * w
atlas[:, X0:] = (np.clip(srgb(out), 0, 1) * 255 + .5).astype(np.uint8)
Image.fromarray(atlas).save(sys.argv[2])
Image.fromarray((np.clip(hair, 0, 1) * 255).astype(np.uint8)).save(os.path.join(HERE, 'work', 'head_hair_weight.png'))
print('HEADHAIR texels weighted > 0.5:', int((hair > .5).sum()), 'beard', beard.round(3), 'strength', w.max().round(2))
