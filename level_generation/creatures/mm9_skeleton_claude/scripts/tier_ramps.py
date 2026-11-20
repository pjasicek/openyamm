#!/usr/bin/env python3
"""Region masks and ramps for the two tiers on one shared paint.
Tier skel_a = Skeleton, Bone Thrasher (MM9 SKELETON2: brown leather, ochre bone, one green eye, the other socket empty), the paint itself.
Tier skel_r = Skeletoid, Skull Thrower (SKELETONRED: red tunic, blue leg cloth, paler bone, two red eyes).
Regions, per texel, in each set's own UV layout, on the parts named. Body: R vest leather (hue on the vest panels and back panel), G leg leather (hue on the femurs and hip scraps), B bone (everything else that is not dark, not rope).
Head: R eyes, G bone. Ramps: tier A is the paint fitted to itself; tier R takes MM9's own colours: the SKELETONRED skin at the texels of the same tile where SKELETON2 is brown, sorted by luminance, matched
by quantiles. Writes textures/skel[_head]_region_mask.png, textures/skel_ramps.json and the eye emission masks."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures')
F = np.load('work/faces.npz')
S = 1024
SCR = [52, 142, 134, 109, 144, 127]
VEST = [2, 47, 300, 124]
LEG = [65] + SCR


def raster(uv, ids):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    keep = np.isin(F['pid'], ids) & (F['lining'] == 0)
    for t in uv[keep]:
        d.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=255)
    return ndimage.binary_dilation(np.asarray(im) > 0, iterations=2)


def hsv(rgb):
    mx, mn = rgb.max(2), rgb.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, sat, mx


def soft(m):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float32), 0.8) * 1.25, 0, 1)


m2 = np.asarray(Image.open('source/skel/skins/skel2.png').convert('RGB'), np.float64) / 255
mr = np.asarray(Image.open('source/red/skins/skelred.png').convert('RGB').resize((256, 256), Image.BICUBIC), np.float64) / 255
h2, s2, v2 = hsv(m2); hr, sr, vr = hsv(mr)
yy, xx = np.mgrid[0:256, 0:256]
body9 = (xx < 150) & (yy > 140)                     # vest tile
leg9 = (xx > 148) & (yy > 84) & (xx < 212)          # leg tile
pelvis9 = (xx > 124) & (yy < 90)
red9 = body9 & ((hr < 12) | (hr > 345)) & (sr > 0.55) & (vr > 0.15)
blue9 = (leg9 | pelvis9) & (hr > 185) & (hr < 245) & (sr > 0.25) & (vr > 0.1)
bone9 = (s2 < 0.45) & (v2 > 0.3) & (sr < 0.45) & (vr > 0.3)
print('MM9 texels red', red9.sum(), 'blue', blue9.sum(), 'bone', bone9.sum())


def mm9_ramp(sel, img):
    px = RV.srgb_to_linear(img[sel]); lum = px @ RV.LUMA
    o = np.argsort(lum); px = px[o]
    q = np.linspace(0, len(px) - 1, 16).astype(int)
    return np.array([px[max(0, i - 6):i + 7].mean(0) for i in q])


def quantile_target(base, w, ramp, gain):
    lum = RV.luminance(base); core = w > 0.5
    order = np.sort(lum[core]); rank = np.searchsorted(order, lum) / max(1, len(order) - 1)
    t = np.clip(rank, 0, 1) * 15
    i = np.minimum(t.astype(int), 14); f = (t - i)[..., None]
    lin = np.clip((ramp[i] * (1 - f) + ramp[i + 1] * f) * gain, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


cfg = {'variants': ['skel_a', 'skel_r'], 'materials': []}
reports = {}
# body
base = RV.load_srgb(T / 'skel_basecolor_final.png', S)
hue, sat, val = hsv(base)
leather = ((hue < 42) | (hue > 345)) & (val < 0.62)
dark = val < 0.16
v_ = raster(F['ub'], VEST) & leather; l_ = raster(F['ub'], LEG) & leather
all_b = raster(F['ub'], [p for p in np.unique(F['pid']) if p < 2000 and p != 301 and p != 13 and p != 14 and p != 95 and p not in (41, 54, 11, 1041, 1054, 1011)])
bone = all_b & ~ndimage.binary_dilation(v_ | l_, iterations=1) & (val > 0.25)
w = [soft(ndimage.binary_closing(v_, iterations=1)), soft(ndimage.binary_closing(l_, iterations=1)), soft(bone)]
targets = [quantile_target(base, w[0], mm9_ramp(red9, mr), 0.95), quantile_target(base, w[1], mm9_ramp(blue9, mr), 1.0), quantile_target(base, w[2], mm9_ramp(bone9, mr), 1.0)]
ramps = {'skel_a': [], 'skel_r': []}; rep = []
for i, wi in enumerate(w):
    fitted, r = RV.fit_ramps(base, {'skel_r': targets[i], 'skel_a': base}, wi)
    ramps['skel_r'].append(fitted['skel_r']); ramps['skel_a'].append(fitted['skel_a']); rep.append(r)
RV.write_mask(w, T / 'skel_region_mask.png', S)
cfg['materials'].append({'base': 'Skel', 'prefix': 'Skel', 'mask': 'skel_region_mask.png', 'ramps': ramps})
reports['body'] = rep
print('body %', [round(float((x > .5).mean() * 100), 1) for x in w])
# head
base = RV.load_srgb(T / 'skel_head_basecolor_final.png', S)
hue, sat, val = hsv(base)
eyes = raster(F['uh'], [2002, 2003]); bone = raster(F['uh'], [p for p in np.unique(F['pid']) if p in (78, 123, 25) or p in (2000, 2001) or p >= 2010]) & (val > 0.22)
w = [soft(eyes), soft(bone & ~eyes)]
t_eye = np.ones_like(base) * np.array([0.95, 0.10, 0.06])
targets = [t_eye, quantile_target(base, w[1], mm9_ramp(bone9, mr), 1.0)]
ramps = {'skel_a': [], 'skel_r': []}; rep = []
for i, wi in enumerate(w):
    fitted, r = RV.fit_ramps(base, {'skel_r': targets[i], 'skel_a': base}, wi)
    ramps['skel_r'].append(fitted['skel_r']); ramps['skel_a'].append(fitted['skel_a']); rep.append(r)
RV.write_mask(w, T / 'skel_head_region_mask.png', S)
cfg['materials'].insert(1, {'base': 'SkelHead', 'prefix': 'SkelHead', 'mask': 'skel_head_region_mask.png', 'ramps': ramps})
reports['head'] = rep
print('head %', [round(float((x > .5).mean() * 100), 1) for x in w])
json.dump(cfg, open(T / 'skel_ramps.json', 'w')); json.dump(reports, open('work/ramps_report.json', 'w'), indent=1)
