#!/usr/bin/env python3
"""Tier ramps on the one body paint (PeasantF5, from PeasantF8's tiers_pf.py). MM9's two skins differ in the pinafore bodice and the skirt
(B slate teal, A maroon / red); coif, blouse, collar, waist band, apron, arms, hands, shoes and bracelets are the same, so they keep the paint
(A's embroidered blouse front is a pattern the ramps cannot give: left as the plain blouse). Regions: R pinafore (the teal cloth of the bodice,
picked by hue on the B-look paint), G skirt (apron left out) with the lining at the bottom of the ramp. The lining is darkened in the base.
Ramps map our luminance quantiles to MM9's texels of that region, tier by tier (MM9 texels picked on skin B by hue, read in both skins).
Writes textures/pf_body_tone.png, pf_body_mask.png, pf_ramps.json, pf_material_classes.png, review/tier_mask_preview.png. Project folder."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures'); STOPS = 16; W = 2048
D = np.load('work/uv.npz'); uv, tri, mat, comp, co = D['uv'], D['tri'], D['mat'], D['comp'], D['co']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def unlin(a): return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 0) ** (1 / 2.4) - 0.055)
LUMA = np.array([0.2126, 0.7152, 0.0722])
def raster(label):
    im = Image.new('I', (W, W), 0); dr = ImageDraw.Draw(im)
    for f in np.where(mat == 0)[0]:
        dr.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * W)) for i in tri[f]], fill=int(label[f]))
    return np.asarray(im)
fc = comp[tri[:, 0]]
LABS = dict(dress=1, skirt=2, coif=4, arms=7, hands=8, legs=9, lining=10, bracelets=11, ornaments=12, buckle=12)
lab = np.zeros(len(tri), int)
for k, v in LABS.items():
    if k in pid: lab[fc == pid[k]] = v
L = raster(lab); cov = L > 0
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
# apron: the linen on the skirt, everything that is not the slate-teal cloth (its fold shadows are saturated ochre); a chart that is mostly
# apron is all apron
apron = (L == 2) & (((hue < 120) | (hue > 300)) | (sat < 0.10)) & (val > 0.22)
apron = ni.binary_opening(apron, iterations=2); apron = ni.binary_fill_holes(ni.binary_closing(apron, iterations=6)) & (L == 2)
cc, ncc = ni.label(L == 2)
fr = ni.mean(apron.astype(float), cc, range(1, ncc + 1))
for k_, f_ in enumerate(fr, 1):
    if f_ > 0.6: apron |= cc == k_
    elif f_ < 0.08: apron &= ~(cc == k_)
# pinafore: the slate-teal cloth of the bodice (embroidered trims, blouse, collar and band keep the paint)
teal = (L == 1) & (hue > 150) & (hue < 250) & (sat > 0.12) & (val < 0.62) & (val > 0.06)
pin = ni.binary_opening(teal, iterations=1); pin = ni.binary_fill_holes(ni.binary_closing(pin, iterations=2)) & (L == 1)
print('texels', {k: int((L == v).sum()) for k, v in LABS.items()}, 'apron', int(apron.sum()), 'pinafore', int(pin.sum()))
# ---- base: the lining dark (the inside of the skirt), feathered
dark = (L == 10)
dk = ni.gaussian_filter(dark.astype(np.float32), 1.5)[..., None]
tone = unlin(B * (1 - dk) + (B * 0.30) * dk)
# coif: Meshy painted skin and hair tones (orange streaks) on the inner flaps beside the face; they take the coif's cream with their own shading
coif = L == 4
streak = coif & (((hue > 5) & (hue < 38) & (sat > 0.30)) | (hue < 5) | (hue > 340)) & (sat > 0.22)
streak = ni.binary_dilation(streak, iterations=2) & coif
cream = np.median(base[coif & ~streak], 0); lum_ = base.mean(2, keepdims=True); lb_ = ni.gaussian_filter(lum_, (6, 6, 0)) + 1e-3
sw = ni.gaussian_filter(streak.astype(np.float32), 1.2)[..., None]
tone = tone * (1 - sw) + np.clip(cream * np.clip(lum_ / lb_, 0.7, 1.15) * 0.97, 0, 1) * sw
# shins: Meshy painted bare orange skin under the skirt (it shows in the fall and the corpse); a dark wool stocking like MM9's dark leg texels
shin = (L == 9) & (hue > 5) & (hue < 40) & (sat > 0.3) & (val > 0.45)
shin = ni.binary_closing(ni.binary_opening(shin, iterations=1), iterations=3) & (L == 9)
shw = ni.gaussian_filter(shin.astype(np.float32), 1.2)[..., None]
stock = np.array([0.20, 0.16, 0.14]) * np.clip(lum_ / lb_, 0.75, 1.2)
tone = tone * (1 - shw) + stock * shw
print('shin texels', int(shin.sum()))
# forearm next to the bracelet: Meshy painted its own bracelet band on the arm a little up-arm of ours (a dark sliver above the bracelet);
# arm texels within 3 cm of the wrist that are not skin take the forearm's skin tone
A_ = np.load('work/asm_frozen.npz'); wr_, fd_ = A_['wr'], A_['ax']
arm_f = np.where(lab == LABS['arms'])[0]
fcen = co[tri[arm_f]].mean(1); sg_ = np.sign(fcen[:, 0]); al_ = ((fcen - wr_ * np.c_[sg_, np.ones_like(sg_), np.ones_like(sg_)]) * (fd_ * np.c_[sg_, np.ones_like(sg_), np.ones_like(sg_)])).sum(1)
lab2 = np.zeros(len(tri), int); lab2[arm_f[al_ > -0.035]] = 1
near = raster(lab2) > 0
skin_arm = np.median(base[(L == 7) & ~near & (sat > 0.25) & (val > 0.55)], 0)
lab3 = np.zeros(len(tri), int); lab3[arm_f[al_ > -0.016]] = 1
strip = raster(lab3) > 0                          # the last 1.6 cm: Meshy's braided band, replaced whole (its pattern showed through a blend)
dirty = (near & ((val < 0.62) | (sat > 0.62) | (hue > 40))) | strip
dirty = ni.binary_dilation(dirty, iterations=2) & near
dw = ni.gaussian_filter(dirty.astype(np.float32), 1.2)[..., None]
tone = tone * (1 - dw) + np.clip(skin_arm * np.clip(lb_ / np.median(lb_[near & ~dirty]), 0.9, 1.05), 0, 1) * dw
print('wrist sliver texels', int(dirty.sum()), 'arm skin', np.round(skin_arm * 255).tolist())
print('coif streak texels', int(streak.sum()), 'cream', np.round(cream * 255).tolist())
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
# ---- masks, labels padded into the gutters first
reg = np.zeros_like(L); reg[pin] = 1; reg[((L == 2) & ~apron) | (L == 10)] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2)]
# ---- MM9 texels (picked on skin B by hue, read in both skins at the same texels)
ML = np.load('work/mm9_regions.npy'); SK = {t: load(f'source/mm9/skins/pf5{t}.png') for t in 'ab'}
hb = np.asarray(Image.open('source/mm9/skins/pf5b.png').convert('HSV'), np.float32) / 255
yy, xx = np.mgrid[0:256, 0:256]
ha = np.asarray(Image.open('source/mm9/skins/pf5a.png').convert('HSV'), np.float32) / 255
pinB = (ML == 1) & (hb[..., 0] * 360 > 160) & (hb[..., 0] * 360 < 240) & (hb[..., 1] > 0.2) & (hb[..., 2] < 0.6)
redA = ((ha[..., 0] * 360 < 20) | (ha[..., 0] * 360 > 330)) & (ha[..., 1] > 0.35) & (ha[..., 2] < 0.6)
M9 = {'pinafore': pinB, 'skirt': (ML == 2) & (xx > 205)}
M9T = {('pinafore', 'a'): pinB & redA}          # A's embroidered blouse front lies where B has pinafore: only A's red cloth
print('MM9 texels', {k: int(m.sum()) for k, m in M9.items()}, {t: {k: np.round(np.median(SK[t][m], 0) * 255).tolist() for k, m in M9.items()} for t in 'ab'})
BT = lin(tone)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
VAR = ['pf5_b', 'pf5_a']; ramps = {v: [] for v in VAR}
GAIN = float(__import__('os').environ.get('GAIN', '1.0'))       # albedo above MM9's shaded skin texels
for key, m, lb in (('pinafore', masks[0], (1,)), ('skirt', masks[1], (2,))):
    wgt = m * np.isin(L, lb)
    for v in VAR:
        ramps[v].append(ramp(wgt, np.clip(lin(SK[v[-1]][M9T.get((key, v[-1]), M9[key])]) * GAIN, 0, 1)))
    print(key, 'ours median', np.round(unlin(np.median(BT[wgt > .5], 0)) * 255).tolist(),
          {v: np.round(unlin(np.array(ramps[v][-1]['colors'][8])) * 255).tolist() for v in VAR})
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks] + [Image.new('L', (1024, 1024), 0)] * 2
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF5', 'prefix': 'PeasantF5', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
# ---- material classes (1 skin, 8 cloth/leather, 9 metal), 1K, nearest
cls = np.zeros_like(L); cls[cov] = 8; cls[np.isin(L, (7, 8))] = 1; cls[np.isin(L, (11, 12))] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = (np.clip(tone, 0, 1) * 120).astype('u1'); pv[..., 0] = np.maximum(pv[..., 0], (masks[0] * 255).astype('u1')); pv[..., 1] = np.maximum(pv[..., 1], (masks[1] * 255).astype('u1')); pv[apron] = (255, 255, 255)
Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
