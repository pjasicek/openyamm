#!/usr/bin/env python3
"""Copper hair with strand texture (coordinator review 2026-11-02, HOF1: the hair read as a smooth dark-brown leather helmet;
MM9's is a copper-red bob). Hair texels of a head set: the hair parts (HAIR: shell and braids, by headpart.py rank) plus
hair-coloured texels of the skin shell (saturation > 0.45, value < 0.8, hue 5-40 deg) above the brows or at the sides.
Per texel: hue pulled HUE_PULL of the way to HUE (copper), value x GAIN, saturation x SAT; the fine strand detail (luminance
minus its 3-texel blur) x DETAIL. ORM green (roughness) on the hair set to 1 (no sheen). Reads *_prehair.png backups.
Usage (project folder): hair_color.py <export glb> <head prefix> [--hair 3,4,5,6,7] [--gain 1.35] [--hue 22] [--hue-pull 0.5]
[--detail 1.7] [--sat 1.05]"""
import argparse, os, shutil, sys, colorsys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpart import texel_parts
ap = argparse.ArgumentParser(); ap.add_argument('glb'); ap.add_argument('head')
ap.add_argument('--hair', default='3,4,5,6,7'); ap.add_argument('--gain', type=float, default=1.35)
ap.add_argument('--hue', type=float, default=22); ap.add_argument('--hue-pull', type=float, default=0.5)
ap.add_argument('--detail', type=float, default=1.7); ap.add_argument('--sat', type=float, default=1.05)
ap.add_argument('--brow-y', type=float, default=1.82)
ap.add_argument('--side-x', type=float, default=0.075); ap.add_argument('--side-y', type=float, default=1.755)
o = ap.parse_args()
def load(name):
    f = Path(f'textures/{o.head}_{name}.png'); bk = f.with_name(f.stem + '_prehair.png')
    if not bk.exists() or os.environ.get('RESET') == '1': shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)
fh, H = load('head_basecolor'); N = H.shape[0]
pos, part, _ = texel_parts(o.glb, 'PeasantHOFHead', N); P = np.nan_to_num(pos)
r, g, b = H[..., 0] / 255, H[..., 1] / 255, H[..., 2] / 255
mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
hairp = np.isin(part, [int(x) for x in o.hair.split(',') if x])
shell_hair = (part == 0) & (sat > 0.45) & (mx < 0.8) & (hue > 5) & (hue < 40) & \
    ((P[..., 1] > o.brow_y) | (np.abs(P[..., 0] + 0.009) > 0.075))
# temples and the sides of the head (skin shell, |x| > SIDE_X from the face centre, above SIDE_Y, behind the face front):
# the hair bowl covers them in MM9; Meshy left pale grey-beige transition texels there that framed the face as a light band
# once the hair was brightened: they take the nearest hair texels' colour (k-nn in 3D) with their own luminance detail
side = (part == 0) & (np.abs(P[..., 0] + 0.009) > o.side_x) & (P[..., 1] > o.side_y) & (P[..., 2] < 0.035) & ~shell_hair
good = hairp | shell_hair
if side.any() and good.any():
    from scipy.spatial import cKDTree
    gi = np.nonzero(good); step = max(1, len(gi[0]) // 150000)
    tree = cKDTree(P[gi][::step]); gc = H[gi][::step]
    si = np.nonzero(side)
    _, nn = tree.query(P[si], 8)
    col = gc[nn].mean(1); l0 = H[si].mean(-1, keepdims=True); lc = col.mean(-1, keepdims=True)
    H = H.copy(); H[si] = col * np.clip(l0 / np.maximum(lc, 1), 0.7, 1.3) ** 0.4
    r, g, b = H[..., 0] / 255, H[..., 1] / 255, H[..., 2] / 255
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
m = hairp | shell_hair | side
w = ndimage.gaussian_filter(m.astype(float), 1.0) * (part >= 0)
# HSV edit, vectorised
hsv_h = np.where(hue > 180, hue - 360, hue)
nh = hsv_h + (o.hue - hsv_h) * o.hue_pull
lum = 0.299 * r + 0.587 * g + 0.114 * b
low = ndimage.gaussian_filter(lum, 3)
v2 = np.clip(mx * o.gain + (lum - low) * (o.detail - 1) * o.gain, 0, 1)
s2 = np.clip(sat * o.sat, 0, 1)
hh = (nh % 360) / 60.0; i = np.floor(hh).astype(int) % 6; f = hh - np.floor(hh)
p_ = v2 * (1 - s2); q_ = v2 * (1 - s2 * f); t_ = v2 * (1 - s2 * (1 - f))
R = np.choose(i, [v2, q_, p_, p_, t_, v2]); G = np.choose(i, [t_, v2, v2, q_, p_, p_]); B = np.choose(i, [p_, p_, t_, v2, v2, q_])
new = np.stack([R, G, B], -1) * 255
out = H * (1 - w[..., None]) + new * w[..., None]
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fh)
fo, O = load('head_metal_rough_1k')
w1 = np.asarray(Image.fromarray(np.uint8(w * 255)).resize((O.shape[1], O.shape[0]), Image.BILINEAR), float) / 255
O2 = O.copy(); O2[..., 1] = O[..., 1] * (1 - w1) + 255 * w1
Image.fromarray(np.uint8(np.clip(np.round(O2), 0, 255))).save(fo)
print('HAIRCOLOR', o.head, 'texels', int(m.sum()), 'side fill', int(side.sum()), 'median before', np.median(H[m], 0).round().tolist(), 'after', np.median(out[m], 0).round().tolist())
