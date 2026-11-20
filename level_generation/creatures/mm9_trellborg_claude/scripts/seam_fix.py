#!/usr/bin/env python3
"""Neck seam: the head set and the body set meet on a jagged line across the throat. The head's band above the line takes the body's tone there, in ramped luminance (each set has its own ramp), its own grain kept. In place on textures/gezz_head_final.png; the ramps and mask stay."""
import json, sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared')
import region_variants as RV
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
C = np.array([0.0, -0.03, 0.755]); Nk = np.array([0.0, -0.35, 0.937]); Nk /= np.linalg.norm(Nk)
BAND = 0.075
R = json.load(open('textures/gezz_ramps.json'))
def curve(entry):
    rp = entry['ramps']['gezz_a'][0]; lo, hi = rp['range']; c = np.array(rp['colors'], np.float32)
    return np.linspace(lo, hi, 16), c @ LUM
xb, yb = curve(R['materials'][0]); xh, yh = curve(R['materials'][1])
s2l = lambda a: np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
l2s = lambda a: np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 1e-6) ** (1 / 2.4) - 0.055)
B = np.asarray(Image.open('textures/gezz_body_final.png').convert('RGB'), np.float32) / 255
H = np.asarray(Image.open('textures/gezz_head_final.png').convert('RGB'), np.float32) / 255
zb = np.load('work/body_pos.npz'); zh = np.load('work/head_pos.npz')
hb = (zb['pos'] - C) @ Nk; hh = (zh['pos'] - C) @ Nk
mb = zb['cov'] & (hb > -0.09) & (hb < 0.03)
mh = zh['cov'] & (zh['prt'] < 13) & (hh < BAND + 0.04)
Pb = zb['pos'][mb][::3]; Lb = (s2l(B[mb]) @ LUM)[::3]
Ph = zh['pos'][mh]; Lh = s2l(H[mh]) @ LUM
tb = cKDTree(Pb); th = cKDTree(Ph[::3])
_, ib = tb.query(Ph, k=60); Lb_near = Lb[ib].mean(1)
_, ih = th.query(Ph, k=60); Lh_near = Lh[::3][ih].mean(1)
y = np.interp(Lb_near, xb, yb)                                 # the body's tone there, as drawn for tier A
o = np.argsort(yh); tgt = np.interp(y, yh[o], xh[o])           # the head base luminance that draws the same
d = hh[mh]
w = np.clip(1 - (d - 0.012) / BAND, 0, 1); w = w * w * (3 - 2 * w)
grain = np.clip(Lh / np.maximum(Lh_near, 1e-3), 0.55, 1.5)
Lnew = tgt * grain
lin = s2l(H[mh]); Ln = np.maximum(lin @ LUM, 1e-4)
# the region ramp draws from luminance alone, so the band's hue does not matter
new = lin * (1 - w[:, None]) + (lin * (Lnew / Ln)[:, None]).clip(0, 1) * w[:, None] * (Ln > 0.02)[:, None] + Lnew[:, None] * w[:, None] * (Ln <= 0.02)[:, None]
out = H.copy()
out[mh] = np.clip(l2s(np.clip(new, 0, 1)), 0, 1)
ratio = tgt / np.maximum(Lh_near, 1e-4)
Image.fromarray((out * 255 + .5).astype('u1')).save('textures/gezz_head_final.png')
print('SEAM', int(mh.sum()), 'ratio p5/50/95', np.round(np.percentile(ratio[w > 0.5], [5, 50, 95]), 2))
