#!/usr/bin/env python3
"""Tier ramps on the one body paint (PF7, after PF1's tiers_pf1.py). MM9's skins: A (row 18) a yellow-green pinafore dress and skirt, cream
chemise, belt and apron; B (row 20) a red dress whose front is an open red vest over a dark brown laced corset, a dark belt; chemise, apron,
arms and shoes the same. Regions (masks from our paint and MM9's own skin B projected onto our UVs, project_mm9_skin.py):
  R dress cloth (the green of the pinafore and skirt, apron and chemise left out, corset panel left out)
  G the corset panel (MM9 B's dark front panel inside our cloth): tier A takes the R ramp (plain green), tier B MM9 B's corset browns
  B the lacing cords on the corset (MM9 B's pale cords): tier A the R ramp, tier B MM9 B's cord cream
  A the belt (our pale band at the waist): tier A its own cream (MM9 A belt), tier B MM9 B's dark belt
Ramps map our luminance quantiles to MM9's texels of the region (the projected skins), tier by tier.
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
lab = np.zeros(len(tri), int)
for k, v in dict(dress=1, skirt=2, hands=8, legs=9, bracelets=11).items():
    if k in pid: lab[fc == pid[k]] = v
L = raster(lab); cov = L > 0
fz = raster(np.round((co[tri].mean(1)[:, 2] + 1.0) * 1000).astype(int)) / 1000.0 - 1.0      # face centre height (MM9 frame) per texel
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
cloth0 = np.isin(L, (1, 2)) & (hue > 40) & (hue < 100) & (sat > 0.30)
cloth = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(cloth0, iterations=1), iterations=3)) & np.isin(L, (1, 2)) & ~((sat < 0.22) & (val > 0.5))
# belt: the pale band round the waist (MM9 frame z 0.15..0.23)
belt = np.isin(L, (1, 2)) & (fz > 0.14) & (fz < 0.24) & (sat < 0.28) & (val > 0.45)
belt = ni.binary_opening(belt, iterations=1); belt = ni.binary_closing(belt, iterations=2) & np.isin(L, (1, 2)) & (fz > 0.13) & (fz < 0.25)
# MM9 skins projected onto our UVs
PJ = {t: np.asarray(Image.open(f'work/mm9skin_{t}.png').convert('RGB').resize((W, W), Image.LANCZOS), np.float32) / 255 for t in 'ab'}
PH = {t: np.asarray(Image.fromarray((PJ[t] * 255).astype('u1')).convert('HSV'), np.float32) / 255 for t in 'ab'}
pb_v, pb_s, pb_h = PH['b'][..., 2], PH['b'][..., 1], PH['b'][..., 0] * 360
corset = cloth & (L == 1) & (pb_v < 0.36) & ~((pb_h < 12) | (pb_h > 340)) & (fz > 0.15)
corset = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(corset, iterations=2), iterations=4)) & cloth & (L == 1)
lace = ni.binary_dilation(corset, iterations=2) & (pb_v > 0.50) & (pb_s < 0.45) & (L == 1)
corset_all = corset | lace
dress = cloth & ~corset_all & ~belt
print('texels', {k: int((L == k).sum()) for k in (1, 2, 8, 9, 11)}, 'cloth', int(dress.sum()), 'corset', int(corset.sum()), 'lace', int(lace.sum()), 'belt', int(belt.sum()))
tone = base.copy()
# ---- NECK (user review 2026-11-04, "the same" as F2): the chest skin inside the neckline (body paint, no region) was darker than the neck
# (head paint): 208,130,90 vs 244,157,106 (A) / 235,168,115 (B). Skin = dress texels in front, within 17 cm of the head/dress seam, skin-
# coloured; its low frequencies are pulled to NECK_TARGET (the shared neck skin the heads' bottoms are feathered to, head_fix_pf7.py (11)),
# detail kept; skin-island padding takes the nearest covered texel (the GPU filter reads it at island edges).
import os, sys as _sys
_sys.path.insert(0, 'scripts'); from texpos import texel_maps
from scipy.spatial import cKDTree
if os.environ.get('NECK_TARGET'):
    _k = np.round(co, 5); _, _iv = np.unique(_k, axis=0, return_inverse=True); _iv = _iv.ravel(); _PP = np.zeros((_iv.max() + 1, 3)); _PP[_iv] = co
    _hw = np.zeros(len(_PP), bool); _hw[_iv[comp == pid['head']]] = True; _dw = np.zeros(len(_PP), bool); _dw[_iv[comp == pid['dress']]] = True
    _S = _PP[_hw & _dw]
    BM = texel_maps(D, 0, W); BX, BY, BZ = [BM['pos'][..., i] for i in range(3)]
    dseam = np.full((W, W), 9.0); _cv = BM['cov']; dseam[_cv] = cKDTree(_S).query(BM['pos'][_cv])[0]
    bl = base[..., 2]
    skin0 = (L == 1) & ~cloth & ~belt & (BY < 0.02) & (BZ > 0.30) & (dseam < 0.17) & (hue > 4) & (hue < 40) & (bl > 0.22) & (sat > float(os.environ.get('SKIN_SAT', '0.30'))) & (sat < 0.75) & (val > 0.45)
    skin = ni.binary_closing(ni.binary_opening(skin0, iterations=1), iterations=2) & (L == 1) & ~cloth & (BY < 0.02) & (BZ > 0.30) & (dseam < 0.17)
    # pale V marks on both shoulders and an M under the necklace (Meshy painted outlines of the old graft's geometry there; user:
    # "pale V / M marks on the chest"): skin texels within MARK_R of each mark centre take the skin MARK_DZ lower at the same x, feathered
    MR = float(os.environ.get('MARK_R', '0.011')); DZm = float(os.environ.get('MARK_DZ', '0.024'))
    _src = skin & (BZ < 0.49)
    for _c in [[float(v) for v in c.split(',')] for c in os.environ.get('MARKS', '-0.050,-0.08,0.496;0.050,-0.08,0.496;0.0,-0.08,0.470').split(';')]:
        _d = np.hypot(BX - _c[0], BZ - _c[2]); _m = skin & (_d < MR + 0.003) & (BY < -0.02)
        if not _m.any(): continue
        _, _j = cKDTree(BM['pos'][_src]).query(BM['pos'][_m] - [0, 0, DZm]); _w = np.clip((MR + 0.003 - _d[_m]) / 0.003, 0, 1)[:, None]
        tone[_m] = tone[_m] * (1 - _w) + tone[_src][_j] * _w
        print('NECK mark cloned', _c, int(_m.sum()))
    tgt = np.array([float(v) for v in os.environ['NECK_TARGET'].split(',')]) / 255
    _sm = skin.astype(np.float32); _low = np.stack([ni.gaussian_filter(tone[..., c] * _sm, 10) for c in range(3)], -1) / np.maximum(ni.gaussian_filter(_sm, 10), 1e-3)[..., None]
    _g = np.clip(tgt / np.maximum(_low, 1e-3), 0.6, 1.6); _w = np.clip(ni.gaussian_filter(_sm, 1.5) * 1.3, 0, 1) * skin
    tone = np.clip(tone * (1 - _w[..., None]) + tone * _g * _w[..., None], 0, 1)
    _ln = skin & (np.abs(BX) < 0.0016); _rg = skin & (np.abs(BX) > 0.002) & (np.abs(BX) < 0.004)      # the chest's mirror-seam line (as F2)
    if _ln.any() and _rg.sum() > 20:
        _qq = np.c_[BY[_ln], BZ[_ln]]; _, _ii = cKDTree(np.c_[BY[_rg], BZ[_rg]]).query(_qq, k=24); _, _jj = cKDTree(_qq).query(_qq, k=24)
        tone[_ln] = np.clip(tone[_ln] * np.clip(tone[_rg][_ii].mean(1) / np.maximum(tone[_ln][_jj].mean(1), 1e-3), 0.75, 1.25), 0, 1)
    _ni = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); _pad = ~cov & ni.binary_dilation(skin, iterations=8)
    tone[_pad] = tone[_ni[0][_pad], _ni[1][_pad]]
    print('NECK chest skin texels', int(skin.sum()), 'median before', np.round(np.median(base[skin], 0) * 255).tolist(), 'after', np.round(np.median(tone[skin], 0) * 255).tolist())
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
reg = np.zeros_like(L); reg[dress] = 1; reg[corset] = 2; reg[lace] = 3; reg[belt] = 4
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m, s=0.8): return np.clip(ni.gaussian_filter(m.astype(np.float32), s), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), soft(Rp == 3, 0.6), soft(Rp == 4)]
BT = lin(tone)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
def tgt(t, m, extra=None):
    q = (m > 0.5) & (PJ[t].sum(-1) > 0.02)
    if extra is not None: q &= extra
    return lin(PJ[t][q])
pa_h, pa_s = PH['a'][..., 0] * 360, PH['a'][..., 1]
green_a = (pa_h > 40) & (pa_h < 100) & (pa_s > 0.25)
red_b = ((pb_h < 20) | (pb_h > 335)) & (pb_s > 0.4)
VAR = ['pf7_a', 'pf7_b']; ramps = {v: [] for v in VAR}
# MM9 is brighter than its texels suggest under its own lighting; the albedo keeps MM9's texel colours (1.0)
rA = ramp(masks[0], tgt('a', masks[0], green_a)); rB = ramp(masks[0], tgt('b', masks[0], red_b))
ramps['pf7_a'].append(rA); ramps['pf7_b'].append(rB)
ramps['pf7_a'].append(ramp(masks[1], tgt('a', masks[0], green_a))); ramps['pf7_b'].append(ramp(masks[1], tgt('b', masks[1])))
ramps['pf7_a'].append(ramp(masks[2], tgt('a', masks[0], green_a))); ramps['pf7_b'].append(ramp(masks[2], tgt('b', masks[2], pb_v > 0.45)))
ramps['pf7_a'].append(ramp(masks[3], lin(tone[belt])))
belt_b = tgt('b', ni.binary_dilation(belt, iterations=3).astype(np.float32), pb_v < 0.30)
ramps['pf7_b'].append(ramp(masks[3], belt_b if len(belt_b) > 50 else lin(np.array([[0.16, 0.11, 0.08]]))))
for k, nm in enumerate(('dress', 'corset', 'lace', 'belt')):
    print(nm, {v: np.round(unlin(np.array(ramps[v][k]['colors'][8])) * 255).tolist() for v in VAR})
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks]
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF7', 'prefix': 'PeasantF7', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
cls = np.zeros_like(L); cls[cov] = 8; cls[(L == 8)] = 1; cls[L == 11] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = (base * 120).astype('u1'); pv[masks[0] > .5] = (40, 200, 40); pv[masks[1] > .5] = (120, 70, 30); pv[masks[2] > .5] = (255, 240, 200); pv[masks[3] > .5] = (40, 40, 255)
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
