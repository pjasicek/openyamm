#!/usr/bin/env python3
"""Tier ramps on the one body paint (Wyrde, after PF1's tiers_pf1.py). MM9's two skins are the same design: Morgan (young, row 265) plum gown
and plain royal-blue mantle; Verdandi (mature, row 264) brown gown with a cord down the front panel and a moss-green damask mantle. Gold
trims, jewellery, the underskirt, hands and shoes are the same and keep the paint. Faces are the per-tier head sets (head_tiers_wy.py).
Regions (body paint = Morgan's clothes, from the Morgan HD masters):
  R mantle: our paint's blue cloth texels on the mantle part.
  G gown: our paint's plum texels on the gown part (gold trims, spirals, cuffs and jewels left out).
  B damask: MM9's mature skin projected onto our mantle (project_mm9_skin.py), its light motif (high-passed luminance). Morgan's B ramp = her
    R ramp (plain cloth), Verdandi's = MM9's lighter motif texels.
  A cord: texels gold in the projected mature skin but not in the projected young skin, on the gown (Verdandi's cord down the panel).
    Morgan's A ramp = her G ramp, Verdandi's = MM9's gold texels there.
Ramps map our luminance quantiles to MM9's projected texels of the region, tier by tier (the same ramp() as PF1).
Base fixes: the closed cuff caps (the hand stub passes through them) painted a dark lining colour, out of every region.
Writes textures/wy_body_tone.png, wy_body_mask.png, wy_ramps.json (+ the R ramps for head_tiers_wy.py), wy_material_classes.png,
review/tier_mask_preview.png. Project folder."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures'); STOPS = 16; W = 2048
D = np.load('work/uv.npz'); uv, tri, mat, comp, co = D['uv'], D['tri'], D['mat'], D['comp'], D['co']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
A_ = np.load('work/asm_frozen.npz'); sh, ax = A_['sh'], A_['ax']
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def unlin(a): return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 0) ** (1 / 2.4) - 0.055)
LUMA = np.array([0.2126, 0.7152, 0.0722])
def raster(label):
    im = Image.new('I', (W, W), 0); dr = ImageDraw.Draw(im)
    for f in np.where(mat == 0)[0]:
        dr.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * W)) for i in tri[f]], fill=int(label[f]))
    return np.asarray(im)
fc = comp[tri[:, 0]]; fcen = co[tri].mean(1)
lab = np.zeros(len(tri), int)
for k, n in enumerate(('mantle', 'dress', 'skirt', 'hands', 'legs', 'jewel'), 1): lab[fc == pid[n]] = k
# cuff caps: gown faces at the sleeve end round the arm axis (both sides)
for sgn in (1, -1):
    a = ax * [sgn, 1, 1]; s0 = sh * [sgn, 1, 1]; t = (fcen - s0) @ a; r = np.linalg.norm(fcen - s0 - t[:, None] * a, axis=1)
    lab[(fc == pid['dress']) & (fcen[:, 0] * sgn > 0.2) & (t > 0.440) & (r < 0.035)] = 7
L = raster(lab); cov = L > 0
base = load(T / 'wy_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
gold = (hue > 25) & (hue < 65) & (sat > 0.35) & (val > 0.35)
blue = (hue > 195) & (hue < 255) & (sat > 0.30)
plum = ((hue > 285) | (hue < 12)) & (sat > 0.25) & (val > 0.08) & ~gold
def clean(m, lbl, o=1, c=3):
    m = ni.binary_opening(m, iterations=o); return ni.binary_fill_holes(ni.binary_closing(m, iterations=c)) & np.isin(L, lbl)
mant = (L == 1) & ~ni.binary_dilation(gold & (L == 1), iterations=1)      # the whole mantle cloth (hue picks missed folds: blue patches on Verdandi)
mant |= clean((L == 2) & blue, (2,), 1, 2)      # Meshy painted the cowl's blue onto gown faces at the neckline: mantle colour there (it stayed blue on Verdandi)
gown = clean((L == 2) & plum, (2,)) & ~ni.binary_dilation(gold & (L == 2), iterations=1)
print('texels', {k: int((L == k).sum()) for k in range(1, 8)}, 'mantle', int(mant.sum()), 'gown', int(gown.sum()))
# ---- base fixes: cuff caps a dark lining colour (the gown's darkest tenth), feathered
cap = L == 7
dark = np.percentile(B[gown], 8, axis=0) * 0.6
kc = np.clip(ni.gaussian_filter(cap.astype(np.float32), 1.0) * 1.5, 0, 1)[..., None] * cap[..., None]
lB = B @ LUMA; det = (lB - ni.gaussian_filter(lB, 2.0))[..., None]
Bc = B * (1 - kc) + np.clip(dark + det * 0.3, 0, 1) * kc
print('cap texels', int(cap.sum()), 'dark', np.round(unlin(dark) * 255).tolist())
# hands: one clean skin colour (brown specks Meshy painted on the wrists and backs of the hands), broad shading and a gentle fine detail kept
hm_ = L == 4
if hm_.sum():
    hl = Bc @ LUMA; ml0 = float(np.median(hl[hm_ & (hl > np.percentile(hl[hm_], 30))]))
    med = lin(np.array([212, 148, 108]) / 255.0); ml = ml0      # between the two faces' skin (Morgan 211,145,103; Verdandi 195,121,85)
    broad = np.clip(ni.gaussian_filter(np.where(hm_, hl, ml), 6) / ml, 0.75, 1.05); fine = np.clip(hl / np.maximum(ni.gaussian_filter(np.where(hm_, hl, ml), 2), 1e-4), 0.9, 1.08)
    wh = hm_[..., None] * 1.0
    Bc = Bc * (1 - wh) + (med * (broad * fine)[..., None]) * wh
    print('HANDS clean texels', int(hm_.sum()), 'skin', np.round(unlin(med) * 255).tolist())
tone = unlin(Bc)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'wy_body_tone.png')
# ---- MM9 projections
PY = load('work/proj_young.png'); PM = load('work/proj_mature.png'); pcov = np.load('work/proj_young.cov.npy')
if pcov.shape[0] != W: pcov = np.asarray(Image.fromarray(pcov.astype('u1') * 255).resize((W, W), Image.NEAREST)) > 0
def hsvof(x): return np.asarray(Image.fromarray((x * 255).astype('u1')).convert('HSV'), np.float32) / 255
hy, hm = hsvof(PY), hsvof(PM)
def goldp(h): return np.clip((h[..., 1] - 0.30) / 0.15, 0, 1) * np.clip((h[..., 2] - 0.40) / 0.15, 0, 1) * ((h[..., 0] * 360 > 25) & (h[..., 0] * 360 < 60))
# texel rest positions (texel_pos.py)
TP = np.load('work/texel_pos.npy'); okp = ~np.isnan(TP[..., 0]); TPz = np.nan_to_num(TP)
# damask: MM9's own mature mantle pattern (the plain back strip of its skin, x 205-255, mirrored-repeat), mapped by arc length round the
# body (0.2 m radius) and height (5 mm per skin pixel); the light motif (luminance over its blur) on our mantle
SKM = np.asarray(Image.open('source/mm9/wyrd_mature/skins/wyrd_mature.png').convert('RGB'), np.float32)[:, 205:255] / 255
tl = lin(SKM) @ LUMA; tl = tl / ni.gaussian_filter(tl, 6, mode='wrap') - 1.0
# r5 (review: "a large mirrored blotch pattern, Rorschach, from behind"): the mirrored repeat mirrored the pattern at the back centre. Now the
# strip is made seamless (blended with its half-shifted copy toward its edges, both ways), repeated by plain wrap with a brick offset per
# column, at a smaller scale (6.5 x 4 mm per skin texel: about a 33 cm x 1 m tile)
PXU, PXV = 0.0065, 0.004
hN, wN = tl.shape
au = np.abs(np.arange(wN) - (wN - 1) / 2) / ((wN - 1) / 2); av = np.abs(np.arange(hN) - (hN - 1) / 2) / ((hN - 1) / 2)
t1 = tl * (1 - au[None, :]) + np.roll(tl, wN // 2, axis=1) * au[None, :]
tls = t1 * (1 - av[:, None]) + np.roll(t1, hN // 2, axis=0) * av[:, None]
uu = np.arctan2(TPz[..., 0], TPz[..., 1]) * 0.20 / PXU + 1000.3; vv = -(TPz[..., 2] - 0.9) / PXV + 1000.7
col_ = np.floor(uu / wN).astype(int); vv = vv + (col_ % 3) * (hN * 0.37)
dam_raw = tls[np.mod(np.floor(vv).astype(int), hN), np.mod(np.floor(uu).astype(int), wN)]
dam = 0.75 * np.clip((dam_raw - 0.06) / 0.12, 0, 1) * mant * okp
dam = np.clip(ni.gaussian_filter(dam, 0.7), 0, 1)
# cord: a braid hanging from the belt at the front centre of the panel (MM9 mature), |x| < 1.2 cm, front, 1.09 -> 0.80 m over the soles
zs = TPz[..., 2] + 0.9297; xr = TPz[..., 0]
band = (np.abs(xr) < 0.012) & (TPz[..., 1] < -0.05) & (zs < 1.09) & (zs > 0.80) & okp
braid = 0.55 + 0.45 * (np.sin((zs * 260 + np.abs(xr) * 300)) > -0.2)
edge = np.clip((0.012 - np.abs(xr)) / 0.003, 0, 1)
cord = band * braid * edge * ni.binary_dilation(gown, iterations=2)
cord = np.clip(ni.gaussian_filter(cord.astype(np.float32), 0.6), 0, 1)
print('damask texels', int((dam > 0.5).sum()), 'cord texels', int((cord > 0.5).sum()))
# ---- masks, padded into the gutters first
reg = np.zeros_like(L); reg[mant] = 1; reg[gown] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
Rp = reg[idx[0], idx[1]]; Dp = dam[idx[0], idx[1]]; Cp = cord[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), Dp * soft(Rp == 1), Cp * soft(Rp == 2)]
BT = lin(tone)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
VAR = ['wy_young', 'wy_mature']; PR = {'wy_young': PY, 'wy_mature': PM}; HP = {'wy_young': hy, 'wy_mature': hm}
ramps = {v: [] for v in VAR}
for v in VAR:
    notg = goldp(HP[v]) < 0.2
    tm = pcov & mant & notg
    if v == 'wy_mature': ramps[v].append(ramp(masks[0], lin(SKM.reshape(-1, 3)[tl.ravel() < 0.0])))      # the damask's ground (motif left to B)
    else: ramps[v].append(ramp(masks[0], lin(PR[v][tm])))
    tg = pcov & gown & notg
    ramps[v].append(ramp(masks[1], lin(PR[v][tg])))
ramps['wy_young'].append(dict(ramps['wy_young'][0]))
SKD = SKM.reshape(-1, 3); tlf = tl.ravel()
ramps['wy_mature'].append(ramp((masks[2] > 0.3) * 1.0, lin(SKD[tlf > 0.06])))
ramps['wy_young'].append(dict(ramps['wy_young'][1]))
SKC = np.asarray(Image.open('source/mm9/wyrd_mature/skins/wyrd_mature.png').convert('RGB'), np.float32)[140:202, 75:84].reshape(-1, 3) / 255
ramps['wy_mature'].append(ramp((masks[3] > 0.3) * masks[1], lin(SKC)))
for k_, m_ in (('mantle', masks[0]), ('gown', masks[1])):
    print(k_, 'ours median', np.round(unlin(np.median(BT[m_ > .5], 0)) * 255).tolist(),
          {v: np.round(unlin(np.array(ramps[v][0 if k_ == 'mantle' else 1]['colors'][8])) * 255).tolist() for v in VAR})
chs = [Image.fromarray((np.clip(x, 0, 1) * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks]
Image.merge('RGBA', chs).save(T / 'wy_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'Wyrde', 'prefix': 'Wyrde', 'mask': 'wy_body_mask.png', 'ramps': ramps}]}, open(T / 'wy_ramps.json', 'w'))
# ---- material classes (1 skin, 8 cloth, 9 metal/jewels), 1K, nearest
cls = np.zeros_like(L); cls[cov] = 8; cls[L == 4] = 1; cls[(L == 6) | (gold & cov)] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'wy_material_classes.png')
pv = np.zeros((W, W, 3), np.uint8); pv[..., 2] = (masks[0] * 200).astype('u1'); pv[..., 0] = (masks[1] * 200).astype('u1')
pv[masks[2] > 0.5] = (120, 255, 120); pv[masks[3] > 0.5] = (255, 220, 0); pv[cap] = (255, 255, 255)
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
