#!/usr/bin/env python3
"""Tier ramps on the one body paint. Upper set regions: R plate field (enamel), G filigree inside the plates, B sleeves and collar, A tunic. Lower set: R panel, flap and greave field, G gems. Trims, belt, hands, legs unmapped.
Every region's ramp maps OUR luminance quantiles to the MM9 tier's own texels of that region (same skin layout in all three skins), so tone and contrast follow MM9 while our sharper detail stays; tier B keeps our paint (identity, with a tone pull towards MM9 by TONE_B).
Writes textures/es_{up,low}_mask.png (1024x512 RGBA), textures/es_ramps.json. Project folder."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ni
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures'); STOPS = 16
D = np.load('work/uv_tex.npz'); uv, tri, mat, comp = D['uv'], D['tri'], D['mat'], D['comp']; names = [str(x) for x in D['names']]; co = D['co']
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
def lin(a): return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
def hsv(a):
    mx, mn = a.max(2), a.min(2); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360, (mx - mn) / np.maximum(mx, 1e-6), mx
LUMA = np.array([0.2126, 0.7152, 0.0722])
def raster(m, W, H, label):
    """per-texel label image from a per-face label"""
    im = Image.new('I', (W, H), 0); dr = ImageDraw.Draw(im)
    fi = np.where(mat == m)[0]
    for f in fi:
        t = tri[f]; dr.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * H)) for i in t], fill=int(label[f]))
    return np.asarray(im)
fcomp = comp[tri[:, 0]]; cen = co[tri].mean(1)
W, H = 2048, 1024
def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]; return x * x + y * y <= r * r
pid = {n: i for i, n in enumerate(names)}
# ---- MM9 texels: masks from skin B, same layout in A and C
SK = {t: load(f'source/es{i}/skins/es{i}.png') for t, i in (('a', 1), ('b', 2), ('c', 3))}
h, s, v = hsv(SK['b']); red = ((h < 18) | (h > 340)) & (s > 0.55) & (v > 0.25)
yy, xx = np.mgrid[0:256, 0:256]
up_rect = (xx < 135) & (yy > 62) & (yy < 180) | ((xx >= 75) & (xx < 135) & (yy > 0) & (yy < 80) & (yy > 15))
closed = ni.binary_closing(red, structure=disk(3))
M9 = {'up_field': red & up_rect, 'up_filig': closed & ~red & up_rect,
      'sleeve': (xx > 100) & (xx < 178) & (yy < 60) & (yy > 5) & (s < 0.32),
      'tunic': (xx < 125) & (yy > 128) & (yy < 208) & (v < 0.38),
      'low_field': red & (xx > 158), 'gem': red & (xx > 120) & (xx < 172) & (yy > 70) & (yy < 118),
      'legs': (xx > 182) & (xx < 232) & (yy > 48) & (yy < 150) & (v < 0.42) & ~red}
print('MM9 texels', {k: int(m.sum()) for k, m in M9.items()})
GAIN = {'legs': 1.4, 'tunic': 2.2, 'sleeve': 1.3}
CONTR = {'legs': 0.6}                                   # the paint's quilting would read as stripes through a full-range ramp       # MM9's flat renders read lighter than its texels do under the viewer's and game's light (compared side by side)
def ramp(base_lin, weight, target):
    """16 stops: our luminance quantile -> mean target colour at that quantile. target: N x 3 linear"""
    l = base_lin @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n))
        cols.append(ts[a:b].mean(0))
    cols = np.array(cols); med = np.median(ts @ LUMA)
    lum = cols @ LUMA; floor = 0.22 * med                 # no black halo round the ornament
    cols = cols * (np.maximum(lum, floor) / np.maximum(lum, 1e-5))[:, None]
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
def cont(r, key):
    k = CONTR.get(key)
    if k is None: return r
    c = np.array(r['colors']); mean = c.mean(0); r['colors'] = (mean + (c - mean) * k).tolist(); return r
def pad_mask(m, cov):
    idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    return m[idx[0], idx[1]]
out = {'variants': ['es_a', 'es_b', 'es_c'], 'materials': []}
# ---- upper
base = load(T / 'es_up_tone.png'); B = lin(base)
lab = np.where(fcomp == pid['torso'], 1, 0)
lab[(fcomp == pid['torso']) & ((np.abs(cen[:, 0]) > 0.215) | (cen[:, 2] > 1.585))] = 2
lab[np.isin(fcomp, [pid['yokeF'], pid['yokeB'], pid['pauldrons']])] = 3
lab[(fcomp == pid['torso']) & (np.abs(cen[:, 0]) < 0.215) & (cen[:, 2] > 1.47)] = 3      # Meshy carried the plate paint past the sheet's edge, up to the collar
L = raster(0, W, H, lab + 1) - 1; cov = L >= 0
hb, sb, vb = hsv(base)
pred = ((hb < 20) | (hb > 335)) & (sb > 0.5) & (vb > 0.18) & (L == 3)
inter = ni.binary_closing(pred, structure=disk(9), iterations=1) & (L == 3)
inter = ni.binary_opening(inter, structure=disk(3))
# the rim is the bright gold round a plate: what closing does not bridge
# gold inside a plate that tier A's paint does not keep gold: the filigree. The rims and the demon face stay gold in every tier
aa = load(T / 'esa_up_tone.png'); ha, sa, va = hsv(aa)
agold = (ha > 18) & (ha < 70) & (sa > 0.3) & (va > 0.22)
agold = ni.binary_dilation(agold, structure=disk(1))
field = pred; filig = (L == 3) & ~pred & ~agold
gold_up = ni.binary_dilation((hb > 18) & (hb < 75) & (sb > 0.28) & (vb > 0.16), structure=disk(1))
sleeve = (L == 2) & ~gold_up; tunic = (L == 1) & ~gold_up      # Meshy's gold smears under the pauldrons stay gold, a ramp turned them pale
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [pad_mask(soft(x), cov) for x in (field, filig, sleeve, tunic)]
print('up shares', [round(float(m.mean()), 3) for m in masks])
AA = lin(aa)
ramps = {'es_a': [], 'es_b': [], 'es_c': []}
for name, m, key in (('field', masks[0], 'up_field'), ('filig', masks[1], 'up_filig'), ('sleeve', masks[2], 'sleeve'), ('tunic', masks[3], 'tunic')):
    w = m > 0.5
    ramps['es_a'].append(ramp(B, m, AA[w]))                  # tier A's own paint at the same texels: pattern place and tone
    ramps['es_c'].append(ramp(B, m, lin(SK['c'][M9[key]]) * GAIN.get(key, 1.0)))
    ramps['es_b'].append(ramp(B, m, lin(SK['b'][M9[key]]) * GAIN.get(key, 1.0)) if key in ('up_field', 'tunic', 'sleeve') else ramp(B, m, B[w]))
    print(name, 'ours', np.round(np.median(B[w], 0), 3), {t: np.round(np.median(lin(SK[t][M9[key]]), 0), 3) for t in 'abc'})
def write_mask(ms, path):
    chs = [Image.fromarray((m * 255 + .5).astype('u1')).resize((1024, 512), Image.LANCZOS) for m in ms + [np.zeros_like(ms[0])] * (4 - len(ms))]
    Image.merge('RGBA', chs).save(path)      # channels resized alone: an RGBA resize premultiplies by alpha
write_mask(masks, T / 'es_up_mask.png')
out['materials'].append({'base': 'SorcererUp', 'prefix': 'SorcererUp', 'mask': 'es_up_mask.png', 'ramps': ramps})
# ---- lower
base = load(T / 'es_low_tone.png'); B = lin(base)
lab = np.zeros(len(tri), int); lab[np.isin(fcomp, [pid['panelF'], pid['panelB'], pid['flapF'], pid['flapB'], pid['greaves']])] = 1; lab[fcomp == pid['bracers']] = 2; lab[np.isin(fcomp, [pid['legs'], pid['boots']])] = 3
L = raster(1, W, H, lab + 1) - 1; cov = L >= 0
hb, sb, vb = hsv(base)
pred = ((hb < 20) | (hb > 335)) & (sb > 0.5) & (vb > 0.18)
gold = (hb > 18) & (hb < 75) & (sb > 0.28) & (vb > 0.16)
gold = ni.binary_dilation(gold, structure=disk(1))
field = pred & ((L == 1) | (L == 3)); gem = pred & (L == 2); legs = (L == 3) & ~gold & ~pred      # Meshy's red spills on the trousers beside the flaps
masks = [pad_mask(soft(x), cov) for x in (field, gem, legs)]
print('low shares', [round(float(m.mean()), 3) for m in masks])
ramps = {'es_a': [], 'es_b': [], 'es_c': []}
for name, m, key in (('field', masks[0], 'low_field'), ('gem', masks[1], 'gem'), ('legs', masks[2], 'legs')):
    w = m > 0.5
    for t, v_ in (('a', 'es_a'), ('c', 'es_c')): ramps[v_].append(cont(ramp(B, m, lin(SK[t][M9[key]]) * GAIN.get(key, 1.0)), key))
    ramps['es_b'].append(cont(ramp(B, m, lin(SK['b'][M9[key]]) * GAIN.get(key, 1.0)), key) if key != 'gem' else ramp(B, m, B[w]))
    print(name, 'ours', np.round(np.median(B[w], 0), 3), {t: np.round(np.median(lin(SK[t][M9[key]]), 0), 3) for t in 'abc'})
write_mask(masks, T / 'es_low_mask.png')
out['materials'].append({'base': 'SorcererLow', 'prefix': 'SorcererLow', 'mask': 'es_low_mask.png', 'ramps': ramps})
json.dump(out, open(T / 'es_ramps.json', 'w'))
print('TIERS done')
