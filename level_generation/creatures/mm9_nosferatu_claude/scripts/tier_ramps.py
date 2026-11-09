#!/usr/bin/env python3
"""Tier ramps on the one paint (tier B's costume). Body regions: R robe field (and the centre panel, chest and sleeve damask), G linen (collar, bib, wrist tubes), B skin (hands), A braided cord. Claws, gem, belt leather and clasp stay as painted.
Head regions: R skin, G eyes, B gums and lips. Every region's ramp maps OUR luminance quantiles to the MM9 tier's own texels of that region (same skin layout in all three skins).
Writes textures/nos_mask.png, nos_head_mask.png (1K RGBA), textures/nos_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
T = Path('textures'); STOPS = 16
D = np.load('work/uv_tex.npz'); uv, tri, mat, comp = D['uv'], D['tri'], D['mat'], D['comp']; names = [str(x) for x in D['names']]; co = D['co']
pid = {n: i for i, n in enumerate(names)}
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def hsv(a):
    mx, mn = a.max(2), a.min(2); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1e-6), mx
LUMA = np.array([0.2126, 0.7152, 0.0722])
SK = {t: load(f'source/n{i}/skins/nosferatu{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
yy, xx = np.mgrid[0:256, 0:256]
def rect(x0, y0, x1, y1): return (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
vb = SK['b'].max(2)
M9 = {'robe': rect(158, 92, 250, 238), 'cord': rect(142, 90, 148, 240), 'linen': rect(62, 44, 108, 54) & (SK['b'].max(2) > 0.62) & (SK['b'].min(2) > 0.35),
      'hand': rect(160, 30, 204, 44) & (vb > 0.35), 'face': rect(5, 3, 65, 35) & (vb > 0.42), 'eye': rect(17, 41, 28, 47), 'gum': rect(0, 68, 16, 74)}
CONTR = {'linen': 0.45, 'cord': 0.7}
FACE_GAIN, CORD_GAIN, LINEN_GAIN = 0.62, 0.62, 0.7
GAIN = {'robe': {'a': 1.25, 'b': 1.35, 'c': 1.5}}
print({k: int(v.sum()) for k, v in M9.items()})
for k, m in M9.items(): print(k, {t: np.round(np.median(SK[t][m], 0), 2).tolist() for t in 'abc'})
def ramp(base_lin, weight, target):
    l = base_lin @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n))
        cols.append(ts[a:b].mean(0))
    cols = np.array(cols); med = np.median(ts @ LUMA); lum = cols @ LUMA; floor = 0.22 * med
    cols = cols * (np.maximum(lum, floor) / np.maximum(lum, 1e-5))[:, None]
    return {'range': [lo, hi], 'colors': np.clip(cols, 0, 1).tolist()}
def raster(m, W, H, label):
    im = Image.new('I', (W, H), 0); dr = ImageDraw.Draw(im)
    for f in np.where(mat == m)[0]:
        dr.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * H)) for i in tri[f]], fill=int(label[f]))
    return np.asarray(im)
fcomp = comp[tri[:, 0]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
def pad_mask(m, cov):
    idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); return m[idx[0], idx[1]]
def write_mask(ms, path):
    chs = [Image.fromarray((m * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for m in ms + [np.zeros_like(ms[0])] * (4 - len(ms))]
    Image.merge('RGBA', chs).save(path)
out = {'variants': ['nos_a', 'nos_b', 'nos_c'], 'materials': []}
# ---- body
base = load(T / 'nos_final.png'); B = lin(base); h, s, v = hsv(base)
LB = raster(0, 2048, 2048, comp[tri[:, 0]] + 1) - 1; cov = LB >= 0
lk = lambda *n: np.isin(LB, [pid[x] for x in n])
red = ((h < 27) | (h > 335)) & (s > 0.45) & ~((h > 22) & (h < 60) & (v > 0.6))
gold = (h > 22) & (h < 62) & (s > 0.38) & (v > 0.30) & ~red
pale = (h > 20) & (h < 75) & (s < 0.38) & (v > 0.55)
olive = (h > 40) & (h < 100) & (v < 0.34)
dark = v < 0.16
cloth = lk('robe', 'torso', 'sleeves', 'trim', 'neckin', 'cuffs')
px, py, pr = json.load(open('work/patch.json'))
cen0 = co[tri].mean(1); lab0 = np.zeros(len(tri), int)
lab0[(fcomp == pid['robe']) & ~((cen0[:, 1] < -0.02) & (np.abs(cen0[:, 0]) < 0.135))] = 1
S_ = np.array([0.211, -0.02, 1.487]); W_ = np.array([0.475, -0.101, 1.026]); a_ = (W_ - S_) / np.linalg.norm(W_ - S_)
tsl = ((cen0 * [np.sign(1), 1, 1]) * 0)[:, 0] + ((np.c_[np.abs(cen0[:, 0]), cen0[:, 1], cen0[:, 2]] - S_) @ a_)
lab0[(fcomp == pid['sleeves']) & (tsl < 0.33)] = 1
FIELD = raster(0, 2048, 2048, lab0 + 1) - 1 == 1          # the robe outside the centre panel: Meshy's stray gold threads take the robe's ramp
robe = cloth & (red | olive | dark) & ~lk('hands')
robe[py - pr:py + pr, px - pr:px + pr] = True
lab1 = np.zeros(len(tri), int); lab1[np.isin(fcomp, [pid['torso'], pid['neckin']]) & (cen0[:, 2] > 1.60)] = 1
COLLAR = raster(0, 2048, 2048, lab1 + 1) - 1 == 1
linen = (cloth & ni.binary_closing(pale, iterations=3) & ~FIELD) | COLLAR
cord = ni.binary_dilation((cloth & gold) | (cloth & (h > 30) & (h < 70) & (s > 0.22) & (v > 0.34) & ~pale), iterations=1) & cloth & ~FIELD & ~linen
# braid and bib are finer than the 1K mask: small linen islands join the cord, or two half-weights in a row leave the paint's gold showing
big = ni.binary_opening(linen, iterations=3) & ~lk('robe', 'sleeves', 'trim')
cord = ni.binary_closing((cord | (linen & ~big)) & cloth & ~FIELD, iterations=2) & ~big & ~FIELD
linen = big | COLLAR; cord = cord & ~linen
robe = (robe | FIELD) & ~cord & ~linen
skin = lk('hands') & (v > 0.34)
# the robe's texels go neutral at their own luminance: a mask's soft edge at a chart border then cannot leak the paint's red into tiers A and C
lum_ = B @ LUMA; gray_ = ni.binary_dilation(robe, iterations=3) & ~ni.binary_dilation(cord | linen | lk('hands'), iterations=1)
B = np.where(gray_[..., None], lum_[..., None], B)
out_srgb = np.where(B <= 0.0031308, B * 12.92, 1.055 * np.maximum(B, 1e-9) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(out_srgb, 0, 1) * 255 + .5).astype('u1')).save(T / 'nos_final.png')
idx_ = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); B = B[idx_[0], idx_[1]]        # the gutters too: Meshy's red sat in them
out_srgb = np.where(B <= 0.0031308, B * 12.92, 1.055 * np.maximum(B, 1e-9) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(out_srgb, 0, 1) * 255 + .5).astype('u1')).save(T / 'nos_final.png')
masks = [soft(pad_mask(x.astype(np.float32), cov)) for x in (robe, linen, skin, cord)]     # padded first: a blur at the chart edge left the red showing along every seam
print('body shares', [round(float(m.mean()), 3) for m in masks])
ramps = {'nos_a': [], 'nos_b': [], 'nos_c': []}
for name, m, key in (('robe', masks[0], 'robe'), ('linen', masks[1], 'linen'), ('skin', masks[2], 'face'), ('cord', masks[3], 'cord')):
    for t, vn in (('a', 'nos_a'), ('b', 'nos_b'), ('c', 'nos_c')):
        tg = lin(SK[t][M9[key]]) * (FACE_GAIN if key == 'face' else CORD_GAIN if key == 'cord' else LINEN_GAIN if key == 'linen' else GAIN.get(key, {}).get(t, 1.0))
        r_ = ramp(B, m, tg)
        if key == 'robe':
            # one smooth curve, not MM9's few dark levels: the damask's relief must not posterise
            l_ = np.array(r_['range']); stops = l_[0] + (l_[1] - l_[0]) * np.arange(STOPS) / (STOPS - 1); med = float(np.median((B[m > 0.5] @ LUMA)))
            top = tg[(tg @ LUMA) >= np.percentile(tg @ LUMA, 60)].mean(0)
            r_['colors'] = np.clip(top[None] * (0.42 + 0.58 * np.clip((stops / max(med, 1e-4)) ** 0.75, 0, 2.4))[:, None], 0, 1).tolist()
        if key in CONTR:
            c_ = np.array(r_['colors']); mean = c_.mean(0); r_['colors'] = (mean + (c_ - mean) * CONTR[key]).tolist()
        if key == 'cord' and t == 'c':                     # MM9's Vampir has no gold: its cords are the robe's near-black with a faint sheen
            r_['colors'] = (np.linspace(0.004, 0.024, STOPS)[:, None] * np.array([0.8, 1.0, 1.05])).tolist()
        ramps[vn].append(r_)
    print(name, 'ours', np.round(np.median(B[m > 0.5], 0), 3), {t: np.round(np.median(lin(SK[t][M9[key]]), 0), 3).tolist() for t in 'abc'})
write_mask(masks, T / 'nos_mask.png')
out['materials'].append({'base': 'Nosferatu', 'prefix': 'Nosferatu', 'mask': 'nos_mask.png', 'ramps': ramps})
# ---- head
base = load(T / 'nos_head_final.png'); B = lin(base); h, s, v = hsv(base); S = base.shape[0]
LH = raster(1, S, S, comp[tri[:, 0]] + 1) - 1; cov = LH >= 0
headp = LH == pid['head']
reddish = ((h < 22) | (h > 340)) & (s > 0.5)
cen = co[tri].mean(1); lab = np.zeros(len(tri), int)
mouthf = (np.abs(cen[:, 0]) < 0.062) & (cen[:, 1] < -0.09) & (cen[:, 2] > 1.585) & (cen[:, 2] < 1.675); lab[mouthf] = 1
MO = raster(1, S, S, lab + 1) - 1
gums = headp & reddish & (MO == 1) & (v < 0.75)
eyes = (LH == pid['eyes']) | (headp & (h > 18) & (h < 42) & (s > 0.85) & (v > 0.5) & (MO != 1) & False)
skin = headp & ~gums & (v > 0.2)
masks = [soft(pad_mask(x.astype(np.float32), cov)) for x in (skin, eyes, gums)]
print('head shares', [round(float(m.mean()), 3) for m in masks])
ramps = {'nos_a': [], 'nos_b': [], 'nos_c': []}
for name, m, key in (('skin', masks[0], 'face'), ('eyes', masks[1], 'eye'), ('gums', masks[2], 'gum')):
    for t, vn in (('a', 'nos_a'), ('b', 'nos_b'), ('c', 'nos_c')):
        if key == 'face': ramps[vn].append(ramp(B, m, lin(SK[t][M9[key]]) * FACE_GAIN))
        elif key == 'eye':
            tx = SK[t][M9[key]]; sc_ = (tx.max(1) - tx.min(1)) * tx.max(1); tx = tx[sc_ >= np.percentile(sc_, 70)]
            ramps[vn].append(ramp(B, m, lin(tx)))
        elif t != 'b': ramps[vn].append(ramp(B, m, lin(SK[t][M9[key]])))
        else: ramps[vn].append(ramp(B, m, B[m > 0.5]))
    print(name, 'ours', np.round(np.median(B[m > 0.5], 0), 3), {t: np.round(np.median(lin(SK[t][M9[key]]), 0), 3).tolist() for t in 'abc'})
write_mask(masks, T / 'nos_head_mask.png')
out['materials'].append({'base': 'NosferatuHead', 'prefix': 'NosferatuHead', 'mask': 'nos_head_mask.png', 'ramps': ramps})
json.dump(out, open(T / 'nos_ramps.json', 'w'))
print('RAMPS')
