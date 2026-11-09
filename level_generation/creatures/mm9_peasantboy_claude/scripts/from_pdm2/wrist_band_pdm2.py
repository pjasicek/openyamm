#!/usr/bin/env python3
"""Leather wrist bands over the hand graft seam (2026-11-01, hand close-ups): the grafted MPFB hand meets the body's
forearm at a jagged cut (body faces end 0-5 cm past the hand joint along the forearm, the hand's stub starts inside
them), which showed as a pale toothed rim with dark notches. MM9's PeasantDM2 (and the HD master) wear a dark leather
band at each wrist, so both sides of the seam are painted one dark leather band: body texels with s (along forearm ->
hand, from the hand joint) in [S0, S1] and hand texels (head set) in [S0, S1H], within 8 cm of the arm axis. Colour:
LEATHER plus 40 % of the paint's own fine luminance detail (from the untouched backups, so a rerun does not compound).
Body: textures/pdm2_tp_basecolor_graded.png (run after fix_collar_pdm2.py); heads: <prefix>_head_basecolor.png (after
fix_neck_pdm2.py). Writes textures/pdm2_wrist_band_mask.png (body) for tiers_pdm2.py.
Usage (project folder): wrist_band_pdm2.py <export glb> <head prefix> [...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
S0, S1, S1H = -0.04, 0.06, 0.015      # S0 covers the cuff_trim.py ring (-0.03)
LEATHER = np.array([66.0, 38.0, 24.0])
glb, prefixes = sys.argv[1], sys.argv[2:]
g = GLTF2().load(glb); blob = g.binary_blob()
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
a_ = g.accessors[sk.inverseBindMatrices]; bv = g.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
J = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}


def band(material, s1, N=2048):
    pos, cov = texel_positions(glb, material, N)
    P = np.nan_to_num(pos)
    m = np.zeros(cov.shape, bool)
    for s in 'LR':
        h, fa = J[f'Bip01 {s} Hand'], J[f'Bip01 {s} Forearm']
        ax = (h - fa) / np.linalg.norm(h - fa)
        ss = (P - h) @ ax
        rad = np.linalg.norm(P - h - ss[..., None] * ax, axis=-1)
        m |= cov & (np.sign(P[..., 0]) == np.sign(h[0])) & (ss > S0) & (ss < s1) & (rad < 0.08)
    return m, cov


def paint(path, backup, m, cov):
    img = np.asarray(Image.open(path).convert('RGB'), float)
    src = np.asarray(Image.open(backup).convert('RGB'), float)
    lum = src @ [0.299, 0.587, 0.114]
    detail = np.clip(lum - ndimage.gaussian_filter(lum, 3), -10, 10)[..., None] * 0.4
    w = ndimage.gaussian_filter(m.astype(float), 0.8) * cov
    out = img * (1 - w[..., None]) + (LEATHER[None, None] + detail) * w[..., None]
    gut = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[gut] = out[iy[gut], ix[gut]]
    Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(path)
    return w


mb, cb = band('PeasantDM2', S1)
w = paint('textures/pdm2_tp_basecolor_graded.png', 'textures/pdm2_tp_basecolor_graded_precollar.png', mb, cb)
Image.fromarray(np.uint8(np.clip(w, 0, 1) * 255)).save('textures/pdm2_wrist_band_mask.png')
mh, ch = band('PeasantDM2Head', S1H)
for p in prefixes:
    paint(f'textures/{p}_head_basecolor.png', f'textures/{p}_head_basecolor_preneck.png', mh, ch)
print('WRISTBAND body texels', int(mb.sum()), 'hand texels', int(mh.sum()))
