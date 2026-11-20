#!/usr/bin/env python3
"""Tier ramps on the one PF3 body paint (2026-11-02, after tiers_pf1.py). The body paint is skin A (Meshy 4K from the PF3a masters: blue
dress, white apron, white chemise edges, red lacing, red necklace). MM9's two skins differ in the dress (A mid-blue linen, B brown dirty
linen with tears) and the apron (A white, B dirty beige); arms, chest skin, lacing, necklace, shoes keep the paint.
Regions: R the blue dress cloth (bodice, sleeves, skirt; by hue inside the dress/skirt parts, lacing and chemise edges left out),
G the apron (pale, low-saturation cloth on the skirt part). Ramps map our luminance quantiles to MM9's texels of the region per tier
(dress: the skin's right strip, the skirt; apron B: MM9 B's pale apron texels, apron A: the paint's own colours).
Writes textures/pf_body_tone.png (the lining darkened), pf_body_mask.png, pf3_ramps.json, pf_material_classes.png, review/tier_mask_preview.png."""
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
lab = np.zeros(len(tri), int)
lab[fc == pid['dress']] = 1; lab[fc == pid['skirt']] = 2; lab[fc == pid['hands']] = 8; lab[fc == pid['legs']] = 9; lab[fc == pid['lining']] = 10
L = raster(lab); cov = L > 0
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
blue = np.isin(L, (1, 2)) & (hue > 185) & (hue < 250) & (sat > 0.18)
blue = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(blue, iterations=1), iterations=3)) & np.isin(L, (1, 2))
blue &= ~(((hue < 30) | (hue > 330)) & (sat > 0.35))                 # the red lacing stays
apron = (L == 2) & (sat < 0.40) & (val > 0.45) & ~blue
apron = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(apron, iterations=2), iterations=6)) & (L == 2) & ~blue
lab_a, n_a = ni.label(apron); sz_a = ni.sum(apron, lab_a, range(1, n_a + 1)); apron = np.isin(lab_a, 1 + np.where(sz_a > 20000)[0])   # the two apron panels
print('texels', {k: int((L == k).sum()) for k in (1, 2, 8, 9, 10)}, 'blue', int(blue.sum()), 'apron', int(apron.sum()))
dk = ni.gaussian_filter((L == 10).astype(np.float32), 1.5)[..., None]
tone = unlin(B * (1 - dk) + (B * 0.30) * dk)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
reg = np.zeros_like(L); reg[blue | ((L == 10) & False)] = 1; reg[apron] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), np.zeros((W, W), np.float32), np.zeros((W, W), np.float32)]
# ---- MM9 texels (256 skin): the skirt strip at the right; B's apron: pale low-saturation texels of the apron area (centre top of the sheet)
SK = {t: load(f'source/mm9/skins/pf3{t}.png') for t in 'ab'}
HS = {t: np.asarray(Image.open(f'source/mm9/skins/pf3{t}.png').convert('RGB').convert('HSV'), np.float32) / 255 for t in 'ab'}
yy, xx = np.mgrid[0:256, 0:256]
skirt = xx > 210
M9 = {'a': skirt & (HS['a'][..., 0] * 360 > 185) & (HS['a'][..., 0] * 360 < 250) & (HS['a'][..., 1] > 0.18),
      'b': skirt & (HS['b'][..., 0] * 360 > 12) & (HS['b'][..., 0] * 360 < 45) & (HS['b'][..., 1] > 0.3)}
apB = (xx > 125) & (xx < 205) & (yy < 60) & (HS['b'][..., 1] < 0.35) & (HS['b'][..., 2] > 0.35)
print('MM9 texels', {t: [int(m.sum()), np.round(np.median(SK[t][m], 0) * 255).tolist()] for t, m in M9.items()}, 'apron B', int(apB.sum()), np.round(np.median(SK['b'][apB], 0) * 255).tolist())
BT = lin(tone)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
VAR = ['pf3_b', 'pf3_a']; ramps = {v: [] for v in VAR}
wd = masks[0] * np.isin(L, (1, 2)); wa = masks[1] * (L == 2)
own_ap = BT[wa > 0.5]
for v in VAR:
    t = v[-1]
    ramps[v].append(ramp(wd, lin(SK[t][M9[t]])))
    ramps[v].append(ramp(wa, lin(SK['b'][apB]) if t == 'b' else own_ap))
    ramps[v].append({'range': [0.0, 1.0], 'colors': [[0.5, 0.5, 0.5]] * STOPS})
    ramps[v].append({'range': [0.0, 1.0], 'colors': [[0.5, 0.5, 0.5]] * STOPS})
print('dress ours median', np.round(unlin(np.median(BT[wd > .5], 0)) * 255).tolist(), 'apron', np.round(unlin(np.median(own_ap, 0)) * 255).tolist())
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks[:2]] + [Image.new('L', (1024, 1024), 0)] * 2
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF3', 'prefix': 'PeasantF3', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf3_ramps.json', 'w'))
cls = np.zeros_like(L); cls[cov] = 8; cls[L == 8] = 1
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = np.zeros((W, W, 3), np.uint8); pv[..., 2] = (masks[0] * 255).astype('u1'); pv[..., 1] = (masks[1] * 255).astype('u1')
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
