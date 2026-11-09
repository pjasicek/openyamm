#!/usr/bin/env python3
"""Tier ramps on the one body paint (PeasantF6, after PeasantF5's tiers_pf5.py). MM9's two skins differ in the gown (A ochre-brown, B orange)
and the bodice front (A a dark laced vest over a black belt, B the plain orange gown); chemise, lacing, apron, cuffs, hands, shoes are the same.
Regions on the A paint (pf_body_final.png):
  R gown: the saturated ochre-brown wool on the dress, sleeves, arms and skirt (apron left out), the skirt lining at the bottom of the ramp;
  G vest + belt: the dark panels of the bodice front (vest, its floral borders) and the black belt; in tier B they take MM9 B's orange bodice
    (MM9 B has no vest; the cream lacing, chemise and the belt clips stay: deviation).
Tier A's ramps are fitted to our own paint (keeps the approved Codex/Meshy look), tier B's map our luminance quantiles onto MM9 B's texels of
the region (skirt+sleeve gown texels for R, bodice texels for G). Also: the lining darkened, shins under the skirt to a dark stocking.
Writes textures/pf_body_tone.png, pf_body_mask.png, pf_ramps.json, pf_material_classes.png, review/tier_mask_preview.png. Project folder."""
import json, os
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
LABS = dict(dress=1, skirt=2, arms=7, hands=8, legs=9, lining=10, bracelets=11, buckle=12)
lab = np.zeros(len(tri), int)
for k, v in LABS.items():
    if k in pid: lab[fc == pid[k]] = v
L = raster(lab); cov = L > 0
# per-texel face index -> 3D centroid (front/back, height)
fidx = raster(np.arange(len(tri)) + 1) - 1
cen = co[tri].mean(1); CY = np.where(fidx >= 0, cen[np.maximum(fidx, 0), 1], 0); CZ = np.where(fidx >= 0, cen[np.maximum(fidx, 0), 2], 0)
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
cloth = np.isin(L, (1, 2, 7, 10))
gown = cloth & (hue > 22) & (hue < 55) & (sat > 0.42) & (val > 0.16)
gown = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(gown, iterations=1), iterations=2)) & cloth & ~((sat < 0.30) & (val > 0.55))
# apron: the linen on the skirt shell; its fold shadows are saturated ochre like the gown, so a chart that is mostly linen is all apron, and
# elsewhere the linen texels and a 4 px rim round them stay out of the gown
creamy = np.isin(L, (1, 2)) & (sat < 0.32) & (val > 0.42)
cc, ncc = ni.label(L == 2); fr = ni.mean(creamy.astype(float), cc, range(1, ncc + 1))
apron = ni.binary_dilation(creamy, iterations=4) & np.isin(L, (1, 2))
for k_, f_ in enumerate(fr, 1):
    if f_ > 0.5: apron |= cc == k_
gown &= ~apron
# vest + belt: dark texels on the bodice front (y < -0.03, 0.17 < z < 0.47) and the belt band all round (0.16 < z < 0.225)
front = (L == 1) & (CY < -0.03) & (CZ > 0.17) & (CZ < 0.47)
floral = (sat > 0.5) & (val > 0.45)                                                  # the borders' red and gold flowers stay out
vest = front & ~gown & (val < 0.60) & ~floral & ~((sat < 0.25) & (val > 0.35))
belt = (L == 1) & (CZ > 0.165) & (CZ < 0.225) & (val < 0.22)                         # on the bodice shell only (the apron's shadows below stay)
dark = ni.binary_closing(vest | belt, iterations=2) & (L == 1) & ~gown
print('texels', {k: int((L == v).sum()) for k, v in LABS.items()}, 'gown', int(gown.sum()), 'vest', int(vest.sum()), 'belt', int(belt.sum()))
# ---- base: the lining dark (the inside of the skirt), feathered
dk = ni.gaussian_filter((L == 10).astype(np.float32), 1.5)[..., None]
tone = unlin(B * (1 - dk) + (B * 0.30) * dk)
lum_ = base.mean(2, keepdims=True); lb_ = ni.gaussian_filter(lum_, (6, 6, 0)) + 1e-3
# shins: bare skin painted under the skirt -> a dark wool stocking (shows in the fall and the corpse)
shin = (L == 9) & (hue > 5) & (hue < 40) & (sat > 0.3) & (val > 0.45)
shin = ni.binary_closing(ni.binary_opening(shin, iterations=1), iterations=3) & (L == 9)
shw = ni.gaussian_filter(shin.astype(np.float32), 1.2)[..., None]
tone = tone * (1 - shw) + np.array([0.20, 0.16, 0.14]) * np.clip(lum_ / lb_, 0.75, 1.2) * shw
print('shin texels', int(shin.sum()))
# neck: F5's standing collar (the bodice shell's top round the neck, above the chemise) was painted a greyish skin; MM9 F6 shows the bare
# neck there: it takes the head's neck skin (head paint, front of the neck) with its own shading, blended in over 1 cm of height
NECK = np.array([223, 146, 96.]) / 255
nk = (L == 1) & (CZ > 0.525)
nw = (np.clip((CZ - 0.525) / 0.012, 0, 1) * nk).astype(np.float32); nw = ni.gaussian_filter(nw, 1.0)[..., None]
tone = tone * (1 - nw) + np.clip(NECK * np.clip(lum_ / (lb_ + 1e-3), 0.85, 1.1), 0, 1) * nw
print('neck texels', int(nk.sum()))
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
# ---- masks, labels padded into the gutters first
reg = np.zeros_like(L); reg[gown | (L == 10)] = 1; reg[dark] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2)]
# ---- MM9 B texels
ML = np.load('work/mm9_regions.npy'); SKB = load('source/mm9/skins/pf6b.png')
hb = np.asarray(Image.open('source/mm9/skins/pf6b.png').convert('HSV'), np.float32) / 255
gownB = np.isin(ML, (2, 3)) & (hb[..., 1] > 0.45) & (hb[..., 0] * 360 < 40)
bodB = (ML == 1) & (hb[..., 1] > 0.45) & (hb[..., 0] * 360 < 40)
print('MM9 B texels gown', int(gownB.sum()), np.round(np.median(SKB[gownB], 0) * 255).tolist(), 'bodice', int(bodB.sum()), np.round(np.median(SKB[bodB], 0) * 255).tolist())
BT = lin(tone)
GAIN = float(os.environ.get('GAIN', '1.0'))
BG = float(os.environ.get('B_GREEN', '1.15'))      # MM9 B's orange read crimson under the viewer's light: a touch more green in B's ramps
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
def self_ramp(weight):
    """Tier A: the ramp that best reproduces our own paint in the region (mean colour per luminance stop)."""
    l = BT @ LUMA; w = weight > 0.5; lv = l[w]; cv = BT[w]
    lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    t = np.clip((lv - lo) / (hi - lo), 0, 1) * (STOPS - 1); cols = []
    for k in range(STOPS):
        m = np.abs(t - k) < 0.75
        cols.append(cv[m].mean(0) if m.sum() > 20 else cv[np.argsort(np.abs(t - k))[:50]].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
VAR = ['pf6_a', 'pf6_b']; ramps = {v: [] for v in VAR}
for key, m, tgt in (('gown', masks[0], gownB), ('vest', masks[1], bodB)):
    wgt = m * cov
    ramps['pf6_a'].append(self_ramp(wgt))
    ramps['pf6_b'].append(ramp(wgt, np.clip(lin(SKB[tgt]) * GAIN * np.array([1.0, BG, 1.0]), 0, 1)))
    # fit error of tier A against our own paint (8-bit levels, region full-weight texels)
    r = ramps['pf6_a'][-1]; l = BT @ LUMA; w = wgt > 0.9; t = np.clip((l[w] - r['range'][0]) / (r['range'][1] - r['range'][0]), 0, 1) * 15
    i0 = np.floor(t).astype(int).clip(0, 14); f = (t - i0)[:, None]; C = np.array(r['colors']); pred = C[i0] * (1 - f) + C[i0 + 1] * f
    err = np.abs(unlin(pred) - unlin(BT[w])).mean() * 255
    print(key, 'ours median', np.round(unlin(np.median(BT[wgt > .5], 0)) * 255).tolist(), 'B mid', np.round(unlin(np.array(ramps['pf6_b'][-1]['colors'][8])) * 255).tolist(), 'A fit err', round(float(err), 2))
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks] + [Image.new('L', (1024, 1024), 0)] * 2
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF6', 'prefix': 'PeasantF6', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
# ---- material classes (1 skin, 8 cloth/leather, 9 metal), 1K, nearest
cls = np.zeros_like(L); cls[cov] = 8; cls[np.isin(L, (8,))] = 1; cls[np.isin(L, (12,))] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = (np.clip(tone, 0, 1) * 120).astype('u1'); pv[..., 0] = np.maximum(pv[..., 0], (masks[0] * 255).astype('u1')); pv[..., 1] = np.maximum(pv[..., 1], (masks[1] * 255).astype('u1'))
Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
