#!/usr/bin/env python3
"""Rim of the head set (colloidal warrior, from mm9_bigfoot_claude/neck_rim.py): where the head set meets the body set (jagged line
across the throat rolls and the hood), the head base takes the body base of the nearest body texel (the body's own grain), the
head mask's fourth channel takes the weight, and that region's ramps are fitted per tier to the body's final colour there. The
face above the chin stays. Run after tier_ramps_cw.py; in place on cw_head_final.png, cw_head_region_mask.png, cw_ramps.json
(inputs kept in work/neck_rim_in/)."""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared')
import region_variants as RV
NEAR, FAR = 0.03, 0.10
TIERS = ('cw_a', 'cw_b', 'cw_c')
T = Path('textures'); keep = Path('work/neck_rim_in'); keep.mkdir(parents=True, exist_ok=True)
for f in ('cw_head_final.png', 'cw_head_region_mask.png', 'cw_ramps.json'):
    shutil.copy(T / f, keep / f)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float64) / 255
s2l = RV.srgb_to_linear
l2s = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
R = json.load(open(keep / 'cw_ramps.json'))
body_m, head_m = R['materials'][0], R['materials'][1]
def shade(base, mask, ramps):
    lin = s2l(base); L = lin @ RV.LUMA; out = lin.copy()
    for i, rp in enumerate(ramps):
        lo, hi = rp['range']; c = np.array(rp['colors'])
        x = np.clip((L - lo) / max(hi - lo, 1e-4), 0, 1) * 15; i0 = np.minimum(np.floor(x).astype(int), 14); f = (x - i0)[..., None]
        col = c[i0] * (1 - f) + c[i0 + 1] * f
        out = out * (1 - mask[..., i:i + 1]) + col * mask[..., i:i + 1]
    return out
Zb, Zh = np.load('work/body_pos.npz'), np.load('work/head_pos.npz')
bb, hb = Zb['cov'], Zh['cov']
Bb = load(T / 'cw_body_final.png'); Mb = np.asarray(Image.open(T / 'cw_body_region_mask.png'), np.float64) / 255
Mb = Mb.repeat(Bb.shape[0] // Mb.shape[0], 0).repeat(Bb.shape[1] // Mb.shape[1], 1)
H0 = load(keep / 'cw_head_final.png')
Mh0 = np.asarray(Image.open(keep / 'cw_head_region_mask.png'), np.float64) / 255
up = H0.shape[0] // Mh0.shape[0]; Mh = Mh0.repeat(up, 0).repeat(up, 1)
nb = bb & (Zb['pos'][..., 2] > 0.25)
Pb = Zb['pos'][nb]; base_b = Bb[nb]; mask_b = Mb[nb]
final = {v: l2s(np.clip(shade(base_b, mask_b, body_m['ramps'][v]), 0, 1)) for v in TIERS}
tree = cKDTree(Pb)
Ph = Zh['pos'][hb]; d, ix = tree.query(Ph)
u = np.clip((FAR - d) / (FAR - NEAR), 0, 1); w = u * u * (3 - 2 * u)
fz = np.clip((Ph[:, 2] - 0.52) / 0.05, 0, 1) * np.clip((-0.24 - Ph[:, 1]) / 0.04, 0, 1) * np.clip((0.30 - np.abs(Ph[:, 0])) / 0.04, 0, 1)
w = w * (1 - fz)
W = np.zeros(hb.shape); W[hb] = w
H = H0.copy(); H[hb] = H0[hb] * (1 - w[:, None]) + base_b[ix] * w[:, None]
tgt = {k: np.zeros_like(H) for k in TIERS}
for k in tgt: tgt[k][hb] = final[k][ix]
rp, err = RV.fit_ramps(H, tgt, W, core_threshold=0.8)
print('RIM ramps', json.dumps(err))
for k in TIERS:
    head_m['ramps'][k] = head_m['ramps'][k][:3] + [rp[k]]
from scipy import ndimage
Wd = np.maximum(W, ndimage.grey_dilation(W * hb, size=7) * ~hb)      # into the gutters
Mn = Mh0.copy(); Mn[..., 3] = np.asarray(Image.fromarray((Wd * 255 + .5).astype('u1')).resize(Mh0.shape[:2][::-1], Image.BOX), np.float64) / 255
Image.fromarray((np.clip(H, 0, 1) * 255 + .5).astype('u1')).save(T / 'cw_head_final.png')
Image.fromarray((np.clip(Mn, 0, 1) * 255 + .5).astype('u1'), 'RGBA').save(T / 'cw_head_region_mask.png', optimize=True)
json.dump(R, open(T / 'cw_ramps.json', 'w'))
for k in TIERS:
    sel = w > 0.9
    drawn = l2s(np.clip(shade(H[hb][sel], np.c_[Mh[hb][sel][:, :3], np.ones((int(sel.sum()), 1))], head_m['ramps'][k]), 0, 1))
    print('RIM', k, 'texels w>0.9', int(sel.sum()), 'mean abs 8bit vs body', round(float(np.abs(drawn - final[k][ix][sel]).mean() * 255), 2))
