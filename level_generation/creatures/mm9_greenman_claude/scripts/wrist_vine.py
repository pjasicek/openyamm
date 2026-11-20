#!/usr/bin/env python3
"""Twisted vine bracelets over the hand-graft seams (mm9_greenman r2). The Green Man's forearms are bare: where the body's
forearm rim (cuff_trim.py, s = -2 cm from the hand joint) meets the grafted MPFB stub the two surfaces cross in a jagged
line, and the hand set (MakeHuman skin graded to the green forearm) never quite matches the Meshy forearm paint. Like
his twisted-vine belt, a vine wraps each wrist: body texels and hand texels with s (along forearm -> hand, from the
hand joint) in [S0, S1] within 9 cm of the forearm axis are painted as two twisted brown strands (helical stripes of
the belt's browns with a dark crease between turns and a faint green moss tint), feathered 1 px, gutters padded.
Usage (project folder): wrist_vine.py <export glb> <body png> <head png>   (edit in place; run on fresh copies)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2
sys.path.insert(0, 'scripts')
from headpos import texel_positions
S0, S1 = -0.065, 0.012
DARK, MID, LIGHT = np.array([48.0, 30, 18]), np.array([92.0, 60, 36]), np.array([132.0, 96, 60])
glb, body_png, head_png = sys.argv[1:4]
g = GLTF2().load(glb); blob = g.binary_blob()
sk = g.skins[0]; names = [g.nodes[j].name for j in sk.joints]
a_ = g.accessors[sk.inverseBindMatrices]; bv = g.bufferViews[a_.bufferView]
IBM = np.frombuffer(blob, np.float32, a_.count * 16, (bv.byteOffset or 0) + (a_.byteOffset or 0)).reshape(-1, 4, 4)
J = {n: np.linalg.inv(IBM[k].T)[:3, 3] for k, n in enumerate(names)}
def band(material, path):
    img = np.asarray(Image.open(path).convert('RGB')).astype(np.float32); N = img.shape[0]
    pos, cov = texel_positions(glb, material, N)
    P = np.nan_to_num(pos); col = np.zeros_like(img); m = np.zeros(cov.shape, bool)
    for s in 'LR':
        h, fa = J[f'Bip01 {s} Hand'], J[f'Bip01 {s} Forearm']
        ax = (h - fa) / np.linalg.norm(h - fa)
        u = np.cross(ax, [0, 1.0, 0]); u /= np.linalg.norm(u); w = np.cross(ax, u)
        r = P - h; ss = r @ ax; q = r - ss[..., None] * ax
        rad = np.linalg.norm(q, axis=-1); th = np.arctan2(q @ w, q @ u)
        sel = cov & (np.sign(P[..., 0]) == np.sign(h[0])) & (ss > S0) & (ss < S1) & (rad < 0.09)
        # two strands: phase = 2 turns over the band's length, wrapped once around per turn
        ph = (th / (2 * np.pi) * 2 + (ss - S0) / (S1 - S0) * 3.0) % 1.0
        strand = np.sin(ph * np.pi) ** 0.6                  # 0 at the crease between strands, 1 on a strand's crown
        t = np.clip(strand, 0, 1)[..., None]
        c = DARK * (1 - t) + (MID * (1 - t) + LIGHT * t) * t
        # bark grain along the strand and a faint moss tint
        grain = np.sin(ph * 40 + rad * 300) * 6
        c = c + grain[..., None] + np.array([-4.0, 6, -2]) * (np.sin(th * 3 + ss * 90) > 0.6)[..., None]
        # the ends taper into the skin
        edge = np.minimum((ss - S0) / 0.008, (S1 - ss) / 0.008).clip(0, 1)
        col[sel] = c[sel]; m |= sel
        m_soft = edge
    wgt = ndimage.gaussian_filter(m.astype(np.float32), 1.0) * cov
    out = img * (1 - wgt[..., None]) + col * wgt[..., None]
    gut = ndimage.binary_dilation(wgt > 0.02, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[gut] = out[iy[gut], ix[gut]]
    Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(path)
    return int(m.sum())
nb = band('GreenMan', body_png); nh = band('GreenManHead', head_png)
print('WRISTVINE body texels', nb, 'hand texels', nh)
