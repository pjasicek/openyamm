#!/usr/bin/env python3
"""Tier ramps on the one body paint (from the Monk's tiers_mk.py). MM9's two skins differ only in the bodice (B red, A brown) and the skirt
(B red-brown, A olive-brown); apron, band, shoes and hands are the same, so they keep the paint; scarf and sleeves take one shared ochre ramp (MM9 tone). Regions: R bodice (embroidery
left out), G skirt (apron left out), lining in G at the bottom of the ramp. The lining is darkened in the base. Ramps map our luminance quantiles
to MM9's texels of that region, tier by tier. Writes textures/pf_body_tone.png, pf_body_mask.png, pf_ramps.json, pf_material_classes.png. Project folder."""
import json, colorsys
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
fc = comp[tri[:, 0]]; cx = np.abs(co[tri].mean(1)[:, 0])
lab = np.zeros(len(tri), int)
lab[fc == pid['dress']] = 1; lab[(fc == pid['dress']) & (cx > 0.175)] = 3          # bodice, sleeves
lab[fc == pid['cuffs']] = 3; lab[fc == pid['scarf']] = 4; lab[fc == pid['skirt']] = 2; lab[fc == pid['band']] = 6
lab[fc == pid['hands']] = 8; lab[fc == pid['legs']] = 9; lab[fc == pid['lining']] = 10
# cuff interiors (faces turned toward the arm axis): Meshy painted the hand into them, pale spikes round the wrist. Darkened like the lining.
A_ = np.load('work/asm_frozen.npz'); sh_, ax_ = A_['sh'], A_['ax']
fcen = co[tri].mean(1); fn_ = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
for sg in (1, -1):
    a_ = ax_ * [sg, 1, 1]; o_ = sh_ * [sg, 1, 1]; rv_ = fcen - o_; rv_ -= ((rv_ @ a_)[:, None]) * a_
    inner_cuff = (fc == pid['cuffs']) & (fcen[:, 0] * sg > 0) & ((fn_ * rv_).sum(1) < 0)
    lab[inner_cuff] = 11
print('cuff interior faces', int((lab == 11).sum()))
L = raster(lab); cov = L > 0
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
apron = (L == 2) & (sat < 0.38) & (val > 0.45)
apron = ni.binary_opening(apron, iterations=2); apron = ni.binary_fill_holes(ni.binary_closing(apron, iterations=6)) & (L == 2)   # dirt specks on the apron stay apron
cc, ncc = ni.label(L == 2)
fr = ni.mean(apron.astype(float), cc, range(1, ncc + 1))
for k_, f_ in enumerate(fr, 1):
    if f_ > 0.6: apron |= cc == k_          # a chart that is mostly apron is all apron (its dirt patches touch the chart edge)
embro = (L == 1) & (((hue > 18) & (hue < 80)) | (val > 0.62) | (sat < 0.35))
embro = ni.binary_dilation(ni.binary_opening(embro, iterations=1), iterations=2)
print('texels', {k: int((L == k).sum()) for k in range(11)}, 'apron', int(apron.sum()), 'embroidery', int(embro.sum()))
# ---- base: the lining dark (the inside of the skirt), feathered
dark = (L == 10) | (L == 11)
dk = ni.gaussian_filter(dark.astype(np.float32), 1.5)[..., None]
Bs = B.copy()
cloth3 = np.isin(L, (3, 4)).astype(np.float32)
blur = np.stack([ni.gaussian_filter(B[..., c], 2.2) for c in range(3)], -1)
k3 = ni.gaussian_filter(cloth3, 1.5)[..., None] * 0.55        # Meshy's chunky knit on the scarf and sleeves: 55 % of its fine detail goes
Bs = B * (1 - k3) + blur * k3
tone = unlin(Bs * (1 - dk) + (Bs * 0.30) * dk)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
# ---- masks, labels padded into the gutters first
red = ((hue < 16) | (hue > 335)) & (sat > 0.45)
bod = ni.binary_fill_holes(ni.binary_closing((L == 1) & ~embro & red, iterations=2)) & (L == 1) & ~embro
reg = np.zeros_like(L); reg[bod] = 1; reg[((L == 2) & ~apron) | (L == 10)] = 2; reg[np.isin(L, (3, 4, 11))] = 3
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), soft(Rp == 3)]
# ---- MM9 texels: bodice (label 1, the red/brown cloth only), skirt (label 2 in the skirt strip)
ML = np.load('work/mm9_regions.npy'); SK = {t: load(f'source/mm9/skins/pf1{t}.png') for t in 'ab'}
hb = np.asarray(Image.open('source/mm9/skins/pf1b.png').convert('HSV'), np.float32) / 255
yy, xx = np.mgrid[0:256, 0:256]
M9 = {'bodice': (ML == 1) & ((hb[..., 0] * 360 < 15) | (hb[..., 0] * 360 > 340)) & (hb[..., 1] > 0.5) & (yy > 100),
      'skirt': (ML == 2) & (xx > 205), 'ochre': np.isin(ML, (3, 4)) & (xx > 40) & (yy < 175)}
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
VAR = ['pf1_b', 'pf1_a']; ramps = {v: [] for v in VAR}
for key, m, lb in (('bodice', masks[0], 1), ('skirt', masks[1], 2), ('ochre', masks[2], (3, 4))):
    wgt = m * np.isin(L, lb)
    for v in VAR:
        ramps[v].append(ramp(wgt, lin(SK[v[-1]][M9[key]])))
    print(key, 'ours median', np.round(unlin(np.median(BT[wgt > .5], 0)) * 255).tolist())
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks] + [Image.new('L', (1024, 1024), 0)]
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF1', 'prefix': 'PeasantF1', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
# ---- material classes (1 skin, 8 cloth/leather), 1K, nearest
cls = np.zeros_like(L); cls[cov] = 8; cls[L == 8] = 1
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = np.zeros((W, W, 3), np.uint8); pv[..., 0] = (masks[0] * 255).astype('u1'); pv[..., 1] = (masks[1] * 255).astype('u1'); pv[..., 2] = (masks[2] * 255).astype('u1'); pv[apron] = (255, 255, 255); pv[embro & (L == 1)] = (255, 220, 0)
Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
