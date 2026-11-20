#!/usr/bin/env python3
"""Tiers: Lich A keeps the paint (one ramp, the trim, so its material has a mask); Power Lich B recolours by region from
MM9's own pair of skins. Each region's B ramp follows the texels of LICH1 and LICH2 at the same skin position: for every
luminance rank of our paint, the LICH2 colour of the LICH1 texels of that rank, scaled by the brightness ratio of our paint
to LICH1. Writes textures/lich_ramps.json, lich_region_mask.png, lich_head_region_mask.png, lich_eye_mask.png,
lich_material_classes.png, lich_head_material_classes.png. Run from the project folder."""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, '../claude_shared')
import region_variants as RV
LUMA = np.array([0.2126, 0.7152, 0.0722])


def lin(a):
    a = np.asarray(a, np.float64) / 255
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def hsv(a):
    a = np.asarray(a, np.float64) / 255
    mx, mn = a.max(2), a.min(2)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    return hue, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), mx


L1 = np.asarray(Image.open('source/mm9/skins/lich1.png').convert('RGB'))
L2 = np.asarray(Image.open('source/mm9/skins/lich2.png').convert('RGB'))
h1, s1, v1 = hsv(L1); h2, s2, v2 = hsv(L2)
A1, A2 = lin(L1), lin(L2)
yy, xx = np.mgrid[0:256, 0:256]
changed = (A2[..., 2] > 1.15 * A2[..., 0]) & (A1[..., 0] > 1.1 * A1[..., 2])
trim_m = changed & (v1 > 0.42) & (h1 > 22) & (h1 < 55)
belt_m = (yy > 175) & (xx < 135) & (A1[..., 0] > 1.3 * A1[..., 1]) & (v1 > 0.12)
cloth_m = changed & ~trim_m & ~belt_m
wraps_m = ((xx >= 205) & (yy >= 20) & (yy <= 150) & (v1 > 0.35)) | ((xx >= 125) & (xx < 205) & (yy >= 168) & (yy <= 205))
skull_m = (xx < 45) & (yy > 25) & (yy < 95) & (s1 < 0.45) & (v1 > 0.45)
print('MM9 texels', {k: int(v.sum()) for k, v in dict(trim=trim_m | belt_m, cloth=cloth_m, wraps=wraps_m, skull=skull_m).items()})


def b_ramp(base_lin, mask, mm9_mask, gain_cap=4.0, sat=1.0):
    lum = base_lin @ LUMA
    v = lum[mask > 0.9]
    lo, hi = np.percentile(v, [2, 98])
    src = A1[mm9_mask] @ LUMA
    order = np.argsort(src)
    colours = []
    for i in range(16):
        q = i / 15
        ours = lo + q * (hi - lo)
        k0 = int(max(0, (q - 0.08)) * (len(order) - 1)); k1 = int(min(1, (q + 0.08)) * (len(order) - 1)) + 1
        idx = order[k0:k1]
        c = A2[mm9_mask][idx].mean(0)
        g = min(gain_cap, ours / max(src[idx].mean(), 1e-3))
        c = c * g
        grey = c @ LUMA
        colours.append(np.clip(grey + (c - grey) * sat, 0, 1).tolist())
    return {'range': [float(max(lo, 0)), float(min(hi, 1))], 'colors': colours}


def a_ramp(base_lin, mask):
    lum = base_lin @ LUMA
    v = lum[mask > 0.9]
    lo, hi = np.percentile(v, [2, 98])
    colours = []
    for i in range(16):
        c = lo + (i / 15) * (hi - lo)
        m = (mask > 0.9) & (np.abs(lum - c) < (hi - lo) / 15 + 1e-4)
        colours.append((base_lin[m].mean(0) if m.any() else (base_lin[mask > 0.9].mean(0) * c / max(v.mean(), 1e-4))).tolist())
    return {'range': [float(lo), float(hi)], 'colors': colours}


def soft(m, sigma=1.0):
    return np.clip(ndimage.gaussian_filter(m.astype(np.float32), sigma), 0, 1)


def pad_mask(mask, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return mask[iy, ix]


# ---- body
base = np.asarray(Image.open('textures/lich_basecolor_graded.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
pm = np.load('work/part_map_1k.npy')
covered = pm >= 0
hue, sat, val = hsv(base); Bl = lin(base)
cloth_parts = np.isin(pm, (2, 8, 40, 41))
blue = Bl[..., 2] > 0.95 * Bl[..., 0]                               # corset and apron stay navy
trim = cloth_parts & (val > 0.46) & (hue > 22) & (hue < 52) & (sat > 0.3) | ((pm == 6) & (sat > 0.25) & (val > 0.1))
trim = ndimage.binary_dilation(trim, iterations=1)                  # thin braids: the 1K mask must cover them whole
cloth = cloth_parts & ~blue & ~trim & (val > 0.05)
wraps = (pm == 1) | (np.isin(pm, (3, 10)) & (val < 0.42) & (sat > 0.25) & (hue < 40))
print('body texels', dict(trim=int(trim.sum()), cloth=int(cloth.sum()), wraps=int(wraps.sum())))
Mt, Mc, Mw = (pad_mask(soft(m, 0.7), covered) for m in (trim, cloth, wraps))
mask_arr = np.stack([Mt, Mc, Mw, np.zeros_like(Mt)], -1)
Image.fromarray((mask_arr * 255 + 0.5).astype(np.uint8), 'RGBA').save('textures/lich_region_mask.png')
ramps_a = [a_ramp(Bl, Mt)]
ramps_b = [b_ramp(Bl, Mt, trim_m | belt_m, 3.0), b_ramp(Bl, Mc, cloth_m, 5.0), b_ramp(Bl, Mw, wraps_m, 2.0)]

# ---- skull
hb = np.asarray(Image.open('textures/lich_head_basecolor_graded.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
hh, hs, hv = hsv(hb); Hl = lin(hb)
hcov = np.ones_like(hv, bool)
eye = (Hl[..., 0] > 0.18) & (Hl[..., 0] > 3.0 * Hl[..., 1]) & (hs > 0.6)
eye = ndimage.binary_opening(eye, iterations=1)
lab, n = ndimage.label(eye)
sizes = ndimage.sum(eye, lab, range(1, n + 1)); print('eye blobs', sorted(sizes.astype(int).tolist())[-6:])
keep = np.isin(lab, 1 + np.argsort(sizes)[-2:])
keep = ndimage.binary_dilation(keep, iterations=3)
mouth = (hs > 0.45) & ~keep
bone = (hs < 0.5) & (hv > 0.3)
Me, Mb = soft(keep, 1.5), soft(bone & ~keep)
Image.fromarray((np.stack([Me, Mb, 0 * Me, 0 * Me], -1) * 255 + 0.5).astype(np.uint8), 'RGBA').save('textures/lich_head_region_mask.png')
glow = np.clip((Hl[..., 0] - 0.05) / 0.6, 0, 1) ** 0.8 * Me
Image.fromarray((glow * 255).astype(np.uint8)).save('textures/lich_eye_mask.png')
print('eye texels', int(keep.sum()), 'glow max', float(glow.max()))
eye_b = {'range': [0.0, 0.9], 'colors': [[0.003 + 0.25 * (t ** 1.6), 0.02 + 0.98 * t ** 0.9, 0.006 + 0.3 * t ** 1.6] for t in np.linspace(0, 1, 16)]}
eye_a = a_ramp(Hl, Me)
hramps_a = [eye_a]
hramps_b = [eye_b, b_ramp(Hl, Mb, skull_m, 2.0)]
cfg = {'variants': ['lich_a', 'lich_b'],
       'materials': [{'base': 'Lich', 'prefix': 'Lich', 'mask': 'lich_region_mask.png', 'ramps': {'lich_a': ramps_a, 'lich_b': ramps_b}},
                     {'base': 'LichHead', 'prefix': 'LichHead', 'mask': 'lich_head_region_mask.png', 'ramps': {'lich_a': hramps_a, 'lich_b': hramps_b}}]}
json.dump(cfg, open('textures/lich_ramps.json', 'w'), indent=1)
# ---- classes (1 skin n/a; 5 bone, 6 eye, 7 mouth, 8 cloth/leather, 9 metal)
cl = np.full(pm.shape, 8, np.uint8); cl[~covered] = 0
cl[np.isin(pm, (3, 10)) & (val > 0.42)] = 5
cl[(pm == 14)] = 9
Image.fromarray(cl).save('textures/lich_material_classes.png')
hc = np.full(hv.shape, 5, np.uint8); hc[mouth] = 7; hc[keep] = 6
Image.fromarray(hc).save('textures/lich_head_material_classes.png')
print('RAMPS written')
