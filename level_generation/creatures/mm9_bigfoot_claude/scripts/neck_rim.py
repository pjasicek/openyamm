#!/usr/bin/env python3
"""Neck rim of the head set (run 2 follow-up, 2026-10-31): the head shell's lower rim, where it meets the body, read as a
smooth reddish band without fur grain on A and B (the head paint is stretched there and its hood ramp is redder than the
body's fur), and the face region reached down to the collar beside the chin, where its pale skin ramp drew grey-white
patches on every tier.
Per head texel: w = 1 near the body surface (3D distance to the nearest body texel under NEAR), fading out by FAR, and
kept off the face above the chin. There the head base takes the body base of the nearest body texel (the body's own
grain), the head mask's fourth channel (unused so far, drawn last) takes w, and that region's ramps are fitted per tier
to the body's final colour at the same texels (body ramps applied as the shader does). The Yeti's own head image takes
the body's tier C colour there. Writes textures/bf_head_final.png, bf_head_region_mask.png, bf_head_c_final.png and the
head material's ramps in bf_ramps.json, in place (run after seam_fix.py; keeps copies in work/neck_rim_in/)."""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared')
import region_variants as RV
NEAR, FAR = 0.03, 0.10
T = Path('textures'); keep = Path('work/neck_rim_in'); keep.mkdir(parents=True, exist_ok=True)
for f in ('bf_head_final.png', 'bf_head_region_mask.png', 'bf_head_c_final.png', 'bf_ramps.json'):
    if not (keep / f).exists(): shutil.copy(T / f, keep / f)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float64) / 255
s2l = RV.srgb_to_linear
l2s = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
R = json.load(open(keep / 'bf_ramps.json'))
body_m, head_m = R['materials'][0], R['materials'][1]


def shade(base, mask, ramps):
    """the shader's region mix (fs_model.sc): linear base, each channel in order mixes in its ramp at the base luminance"""
    lin = s2l(base); L = lin @ RV.LUMA; out = lin.copy()
    for i, rp in enumerate(ramps):
        lo, hi = rp['range']; c = np.array(rp['colors'])
        x = np.clip((L - lo) / max(hi - lo, 1e-4), 0, 1) * 15; i0 = np.minimum(np.floor(x).astype(int), 14); f = (x - i0)[..., None]
        col = c[i0] * (1 - f) + c[i0 + 1] * f
        out = out * (1 - mask[..., i:i + 1]) + col * mask[..., i:i + 1]
    return out


Zb, Zh = np.load('work/body_pos.npz'), np.load('work/head_pos.npz')
bb, hb = Zb['cov'], Zh['cov']
Bb = load(T / 'bf_body_final.png'); Mb = np.asarray(Image.open(T / 'bf_body_region_mask.png'), np.float64) / 255
Mb = Mb.repeat(Bb.shape[0] // Mb.shape[0], 0).repeat(Bb.shape[1] // Mb.shape[1], 1)
H0 = load(keep / 'bf_head_final.png'); Hc0 = load(keep / 'bf_head_c_final.png')
Mh0 = np.asarray(Image.open(keep / 'bf_head_region_mask.png'), np.float64) / 255
up = H0.shape[0] // Mh0.shape[0]
Mh = Mh0.repeat(up, 0).repeat(up, 1)
# body texels near the neck, their final colour per tier
nb = bb & (Zb['pos'][..., 2] > 0.45)
Pb = Zb['pos'][nb]; base_b = Bb[nb]; mask_b = Mb[nb]
final = {v: l2s(np.clip(shade(base_b, mask_b, body_m['ramps'][v]), 0, 1)) for v in ('bf_a', 'bf_b', 'bf_c')}
tree = cKDTree(Pb)
Ph = Zh['pos'][hb]; d, ix = tree.query(Ph)
u = np.clip((FAR - d) / (FAR - NEAR), 0, 1); w = u * u * (3 - 2 * u)
face = Mh[hb][:, 2]; zh = Ph[:, 2]
v = np.clip((zh - 0.70) / 0.05, 0, 1); cx = np.clip((0.13 - np.abs(Ph[:, 0])) / 0.05, 0, 1)
w = w * (1 - face * v * v * (3 - 2 * v) * cx * cx * (3 - 2 * cx))     # the chin and the face above it stay; the face ramp beside the chin goes
w = w * (Zh['prt'][hb] < 13)                                                           # eyeballs
W = np.zeros(hb.shape); W[hb] = w
H = H0.copy(); H[hb] = H0[hb] * (1 - w[:, None]) + base_b[ix] * w[:, None]
Hc = Hc0.copy()
cw = W if Hc0.shape[:2] == H0.shape[:2] else np.asarray(Image.fromarray((W * 255).astype('u1')).resize(Hc0.shape[:2][::-1], Image.BILINEAR), np.float64) / 255
# the Yeti head: texel by texel at its own resolution, body tier C colour at the nearest body texel
Zc = {k: (np.asarray(Image.fromarray(Zh['pos'][..., i].astype(np.float32)).resize(Hc0.shape[:2][::-1], Image.NEAREST)) if Hc0.shape[:2] != H0.shape[:2] else Zh['pos'][..., i]) for i, k in enumerate('xyz')}
Pc = np.dstack([Zc['x'], Zc['y'], Zc['z']]); mc = cw > 1e-3
_, ic = tree.query(Pc[mc]); Hc[mc] = Hc0[mc] * (1 - cw[mc][:, None]) + final['bf_c'][ic] * cw[mc][:, None]
# ramps of the fourth region, fitted to the body's final colour on the new base
tgt = {k: np.zeros_like(H) for k in ('bf_a', 'bf_b', 'bf_c')}
for k in tgt: tgt[k][hb] = final[k][ix]
rp, err = RV.fit_ramps(H, tgt, W, core_threshold=0.8)
print('RIM ramps', json.dumps(err))
for k in ('bf_a', 'bf_b', 'bf_c'):
    head_m['ramps'][k] = head_m['ramps'][k][:3] + [rp[k]]
Mn = Mh0.copy(); Mn[..., 3] = np.asarray(Image.fromarray((W * 255 + .5).astype('u1')).resize(Mh0.shape[:2][::-1], Image.BOX), np.float64) / 255
Image.fromarray((np.clip(H, 0, 1) * 255 + .5).astype('u1')).save(T / 'bf_head_final.png')
Image.fromarray((np.clip(Hc, 0, 1) * 255 + .5).astype('u1')).save(T / 'bf_head_c_final.png')
Image.fromarray((np.clip(Mn, 0, 1) * 255 + .5).astype('u1'), 'RGBA').save(T / 'bf_head_region_mask.png', optimize=True)
json.dump(R, open(T / 'bf_ramps.json', 'w'))
# check: the rim drawn per tier against the body colour it copies
for k in ('bf_a', 'bf_b'):
    drawn = l2s(np.clip(shade(H[hb][w > 0.9], Mh[hb][w > 0.9] * 0 + np.c_[Mh[hb][w > 0.9][:, :3], np.ones((int((w > 0.9).sum()), 1))], head_m['ramps'][k]), 0, 1))
    print('RIM', k, 'texels w>0.9', int((w > 0.9).sum()), 'mean abs 8bit vs body', round(float(np.abs(drawn - final[k][ix][w > 0.9]).mean() * 255), 2))
