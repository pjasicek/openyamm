#!/usr/bin/env python3
"""Tier ramps on the one body paint. Regions: R cloth, G shoes. Rope and hands are the same in MM9's three skins, so they keep the paint. Inner faces (hood lining, cups, hem cap) are darkened in the base. Ramps map our luminance quantiles to MM9's texels of that
region, tier by tier, so tone and contrast follow MM9 and our sharper weave stays. Writes textures/mk_body_tone.png, mk_body_mask.png, mk_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures'); STOPS = 16
D = np.load('work/uv_tex.npz'); uv, tri, mat, comp, inner = D['uv'], D['tri'], D['mat'], D['comp'], D['inner']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def unlin(a): return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.maximum(a, 0) ** (1 / 2.4) - 0.055)
LUMA = np.array([0.2126, 0.7152, 0.0722]); W = 2048
def raster(label):
    im = Image.new('I', (W, W), 0); dr = ImageDraw.Draw(im)
    for f in np.where(mat == 0)[0]:
        dr.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * W)) for i in tri[f]], fill=int(label[f]))
    return np.asarray(im)
fcomp = comp[tri[:, 0]]
lab = np.ones(len(tri), int)                       # 1 cloth
lab[fcomp == pid['shoes']] = 2; lab[fcomp == pid['shins']] = 3; lab[np.isin(fcomp, [pid['belt'], pid['knots'], pid['cords']])] = 4; lab[fcomp == pid['hands']] = 5
lab[inner] = 6
L = raster(lab); cov = L > 0
SK = {t: load(f'source/mk{i}/skins/mk{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
yy, xx = np.mgrid[0:256, 0:256]
cl = (yy < 228) & ~((xx < 62) & (yy < 105)) & ~((xx > 118) & (yy > 45) & (yy < 90)) & ~((xx > 225) & (yy < 45)) & ~((yy > 195) & (xx > 118))
shoe = (yy >= 232) & (yy < 250) & (xx > 130) & (xx < 212)
rope = (yy >= 243) & (xx < 118); hand = (xx > 125) & (xx < 250) & (yy > 50) & (yy < 84) & (SK['a'][..., 0] > 0.55)
M9 = {'cloth': cl, 'shoes': shoe, 'rope': rope, 'hand': hand}
print('MM9 texels', {k: int(m.sum()) for k, m in M9.items()}, {t: lin(SK[t][cl]).mean(0).round(3).tolist() for t in 'abc'})
# ---- base: inner dark, feathered at the rims; shins plain dark
base = load(T / 'mk_body_final.png'); B = lin(base)
dark = (L == 6) | (L == 3)
dk = ni.gaussian_filter(dark.astype(np.float32), 2.0)[..., None]
B2 = B * (1 - dk) + (B * 0.28) * dk
tone = unlin(B2)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'mk_body_tone.png')
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Lp = L[idx[0], idx[1]]      # labels into the gutters first: a mask soft at a chart's edge left the brown paint as pale stitches on the navy tier
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft((Lp == 1) | (Lp == 6)), soft((Lp == 2) | (Lp == 3)), soft(Lp == 4), soft(Lp == 5)]
GAIN = {}
def ramp(base_lin, weight, target):
    l = base_lin @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
out = {'variants': ['mk_a', 'mk_b', 'mk_c'], 'materials': []}
BT = lin(tone); ramps = {v: [] for v in out['variants']}
G = dict(a=float(sys.argv[1]) if len(sys.argv) > 1 else 1.0, b=float(sys.argv[2]) if len(sys.argv) > 2 else 1.0, c=float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
for key, m, lb in (('cloth', masks[0], 1), ('shoes', masks[1], 2), ('rope', masks[2], 4), ('hand', masks[3], 5)):
    # the lit weave only: the dark inner faces keep the bottom of the ramp
    wgt = m * (L == lb)
    for t in 'abc':
        tg = lin(SK[t][M9[key]])
        if key == 'shoes': tg = tg[(tg @ LUMA) < np.percentile(tg @ LUMA, 90)]      # the skin's pale notch beside the shoe is not leather
        ramps[f'mk_{t}'].append(ramp(BT, wgt, tg * G[t] * (np.array([0.93, 1.0, 1.12]) if (key == 'cloth' and t == 'a') else 1.0) * (1.2 if (key == 'cloth' and t == 'c') else 1.0)))
    print(key, 'ours', np.round(np.median(BT[wgt > .5], 0), 3), {t: np.round(np.median(lin(SK[t][M9[key]]), 0), 3).tolist() for t in 'abc'})
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks]
Image.merge('RGBA', chs).save(T / 'mk_body_mask.png')
out['materials'].append({'base': 'Monk', 'prefix': 'Monk', 'mask': 'mk_body_mask.png', 'ramps': ramps})
json.dump(out, open(T / 'mk_ramps.json', 'w'))
print('TIERS')
