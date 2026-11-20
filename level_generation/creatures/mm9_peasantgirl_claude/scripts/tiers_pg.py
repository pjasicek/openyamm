#!/usr/bin/env python3
"""Tier ramps on the one body paint (PeasantGirl, from PeasantF5's tiers_pf5.py). MM9's three girls share the body; their skins differ in
the dress cloth (g2 rust-brown, g3 navy, g1e teal) and the bodice front (g2 a black vest with gold embroidery, g3 plain navy, g1e teal with
lacing). Undersleeves, apron, shoes and hands are the same, so they keep the paint. Regions on the g2 paint: R dress cloth (rust by hue on
the dress, sleeves and skirt; the lining at the bottom of the ramp), G vest (the dark and gold of the bodice front, the elbow trims and the
belt). Ramps map our luminance quantiles to MM9's texels of that region, tier by tier (MM9 texels picked on skin g2, read in every skin at
the same texels). The vest's embroidery is a pattern: on g3 / g1e it shows as a tone-on-tone pattern in their cloth (deviation).
Writes textures/pg_body_tone.png, pg_body_mask.png, pg_ramps.json, pg_material_classes.png, review/tier_mask_preview.png. Project folder."""
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
LABS = dict(dress=1, skirt=2, hands=8, legs=9, lining=10, buttons=12)
lab = np.zeros(len(tri), int)
for k, v in LABS.items():
    if k in pid: lab[fc == pid[k]] = v
# the bodice front of the dress part (vest candidates): above the waist, in front, inside the shoulders
cen = co[tri].mean(1); front = np.zeros(len(tri), int)
front[(fc == pid['dress']) & (cen[:, 1] < 0.02) & (np.abs(cen[:, 0]) < 0.13) & (cen[:, 2] > 0.20)] = 1
L = raster(lab); cov = L > 0; FR = raster(front) > 0
base = load(T / 'pg_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
cloth = np.isin(L, (1, 2, 10))
rust = cloth & ((hue < 35) | (hue > 340)) & (sat > 0.35) & (val > 0.06) & (val < 0.80)
rust = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(rust, iterations=1), iterations=2)) & cloth
dark = (L == 1) & (val < 0.22) & ~rust
gold = (L == 1) & (hue > 30) & (hue < 65) & (sat > 0.30) & (val > 0.25)
vest = ni.binary_closing(dark | gold, iterations=2) & (L == 1) & ~rust
vest = ni.binary_opening(vest, iterations=1)
# the vest front: a chart that is mostly vest is all vest except its cream (the blouse under the lacing stays)
cream = cloth & (sat < 0.28) & (val > 0.45)
print('texels', {k: int((L == v).sum()) for k, v in LABS.items()}, 'rust', int(rust.sum()), 'vest', int(vest.sum()), 'cream', int(cream.sum()))
# ---- base: the lining dark (the inside of the skirt), feathered
dk = ni.gaussian_filter((L == 10).astype(np.float32), 1.5)[..., None]
tone = unlin(B * (1 - dk) + (B * 0.35) * dk)
lum_ = base.mean(2, keepdims=True); lb_ = ni.gaussian_filter(lum_, (6, 6, 0)) + 1e-3
# shins: dark wool stockings where Meshy painted bare skin under the skirt (shows in the fall and the corpse)
shin = (L == 9) & (hue > 5) & (hue < 40) & (sat > 0.3) & (val > 0.45)
shin = ni.binary_closing(ni.binary_opening(shin, iterations=1), iterations=3) & (L == 9)
shw = ni.gaussian_filter(shin.astype(np.float32), 1.2)[..., None]
tone = tone * (1 - shw) + np.array([0.22, 0.17, 0.14]) * np.clip(lum_ / lb_, 0.75, 1.2) * shw
print('shin texels', int(shin.sum()))
# cuffs: Meshy painted skin-coloured wedges on the undersleeve cloth beside the hands (PeasantM7's fault); sleeve texels (dress faces
# more than 22 cm out from the midline) that are skin-like take the undersleeve cream with the paint's own shading
slv = np.zeros(len(tri), int); slv[(fc == pid['dress']) & (np.abs(cen[:, 0]) > 0.22)] = 1
SL = raster(slv) > 0
skinlike = SL & (hue > 3) & (hue < 30) & (sat > 0.28) & (val > 0.40)
skinlike = ni.binary_dilation(ni.binary_opening(skinlike, iterations=1), iterations=2) & SL
creamc = np.median(base[SL & (sat < 0.22) & (val > 0.55)], 0)
sw_ = ni.gaussian_filter(skinlike.astype(np.float32), 1.0)[..., None]
tone = tone * (1 - sw_) + np.clip(creamc * np.clip(lum_ / lb_, 0.7, 1.15), 0, 1) * sw_
print('cuff skin wedge texels', int(skinlike.sum()), 'cream', np.round(creamc * 255).tolist())
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pg_body_tone.png')
# ---- masks, labels padded into the gutters first
# skin (B): the neck and chest skin of the dress part and the hands take each girl's own head skin (the head colour is per tier; the
# level neck seam showed the shared body paint as a band of another skin tone)
skin_b = np.isin(L, (1, 8)) & (hue > 3) & (hue < 32) & (sat > 0.22) & (sat < 0.70) & (val > 0.42) & ~rust & ~vest
skin_b = ni.binary_opening(skin_b, iterations=1) & np.isin(L, (1, 8)) & ~skinlike
# dark specks inside the neckline skin (Meshy's paint of the lip-to-chest needle and stray vest flecks; navy dots on g3 at 128 px): texels
# enclosed by the chest skin that are not skin take the surrounding skin and join the skin region
encl = ni.binary_closing(skin_b, iterations=5) & (L == 1) & ~skin_b & ~vest_core if 'vest_core' in dir() else ni.binary_closing(skin_b, iterations=5) & (L == 1) & ~skin_b
encl &= ni.binary_erosion(ni.binary_closing(skin_b, iterations=5), iterations=1)
skn = np.where(skin_b[..., None], tone, 0); wsk = ni.gaussian_filter(skin_b.astype(np.float32), 3)[..., None]
fillc = ni.gaussian_filter(skn, (3, 3, 0)) / np.maximum(wsk, 1e-3)
tone = np.where(encl[..., None], fillc, tone)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pg_body_tone.png')
skin_b = skin_b | encl; vest = vest & ~encl; rust = rust & ~encl
print('chest specks filled', int(encl.sum()))
reg = np.zeros_like(L); reg[rust | (L == 10)] = 1; reg[vest] = 2; reg[skin_b] = 3
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), soft(Rp == 3)]
# ---- MM9 texels (picked on skin g2 by hue, read in every skin at the same texels)
ML = np.load('work/mm9_regions.npy'); SK = {t: load(f'source/mm9/{t}/skins/{t}.png') for t in ('pg2', 'pg3', 'pg1e')}
h2 = np.asarray(Image.open('source/mm9/pg2/skins/pg2.png').convert('HSV'), np.float32) / 255
H2, S2, V2 = h2[..., 0] * 360, h2[..., 1], h2[..., 2]
rust9 = ((H2 < 30) | (H2 > 340)) & (S2 > 0.4) & (V2 > 0.12)
M9 = {'dress': (ML == 2) & rust9, 'vest': (ML == 1) & ((V2 < 0.25) | ((H2 > 30) & (H2 < 65) & (S2 > 0.3))) & ~rust9}
print('MM9 texels', {k: int(m.sum()) for k, m in M9.items()}, {t: {k: np.round(np.median(SK[t][m], 0) * 255).tolist() for k, m in M9.items()} for t in SK})
BT = lin(tone)
def ramp(weight, target):
    l = BT @ LUMA; w = weight > 0.5
    lv = np.sort(l[w]); lo, hi = float(np.percentile(lv, 0.5)), float(np.percentile(lv, 99.5)); hi = max(hi, lo + 0.02)
    lt = target @ LUMA; order = np.argsort(lt); ts = target[order]; n = len(ts)
    stops = lo + (hi - lo) * np.arange(STOPS) / (STOPS - 1); cols = []
    for x in stops:
        q = np.searchsorted(lv, x) / len(lv); a = int(np.clip(q - 0.04, 0, 1) * n); b = max(a + 1, int(np.clip(q + 0.04, 0, 1) * n)); cols.append(ts[a:b].mean(0))
    return {'range': [lo, hi], 'colors': np.clip(np.array(cols), 0, 1).tolist()}
VAR = {'pg_g2': 'pg2', 'pg_g3': 'pg3', 'pg_g1e': 'pg1e'}; ramps = {v: [] for v in VAR}
GAIN = float(os.environ.get('GAIN', '1.0'))       # albedo above MM9's shaded skin texels
for key, m, lb in (('dress', masks[0], (1, 2, 10)), ('vest', masks[1], (1,))):
    wgt = m * np.isin(L, lb)
    for v, sk in VAR.items():
        # g3 / g1e have no vest: their bodice is the dress cloth (and g2's vest texels are their neckline skin and blouse there)
        tk = key if (key == 'dress' or sk == 'pg2') else 'dress'
        r_ = ramp(wgt, np.clip(lin(SK[sk][M9[tk]]) * GAIN, 0, 1))
        if key == 'vest' and sk != 'pg2':
            # user review 2026-11-04 (supersedes the 2026-11-02 plain bodice): keep g2's gold embroidery on g3 / g1e. The dark end of the
            # vest ramp (the vest's ground cloth) is the tier's own dress cloth, a little darker in the folds; the bright end (the
            # embroidery) blends to g2's gold at the same stops, so the pattern reads gold on navy / teal instead of vanishing.
            med = np.array(ramps[v][0]['colors'][8])         # the tier's own dress cloth at mid tone
            gold = np.array(ramps['pg_g2'][1]['colors'])     # g2's vest ramp (black ground -> gold embroidery)
            cols = []
            for i in range(STOPS):
                t = i / (STOPS - 1); w = float(np.clip((t - 0.25) / 0.45, 0, 1)); w = w * w * (3 - 2 * w)
                cols.append(np.clip(med * (0.82 + 0.26 * t) * (1 - w) + gold[i] * w, 0, 1).tolist())
            r_['colors'] = cols
        ramps[v].append(r_)
    print(key, 'ours median', np.round(unlin(np.median(BT[wgt > .5], 0)) * 255).tolist(),
          {v: np.round(unlin(np.array(ramps[v][-1]['colors'][8])) * 255).tolist() for v in VAR})
# skin ramps: each tier's lit face skin (work/headmap.npz, the fixed head paint)
HM = np.load('work/headmap.npz'); hpos, hcov = HM['pos'], HM['cov']
neck = hcov & (np.abs(hpos[..., 0]) < 0.018) & (hpos[..., 2] > 0.595) & (hpos[..., 2] < 0.612) & (hpos[..., 1] < -0.105)   # the lit chin (the neck under the chin carries Meshy's baked shadow, the cheeks are rosy, g3's forehead has a fringe)
for v, sk in VAR.items():
    hi_ = np.asarray(Image.open(f'textures/pg_head_{v[3:]}_fix.png').convert('RGB'), np.float32) / 255
    ramps[v].append(ramp(masks[2] * np.isin(L, (1, 8)), lin(hi_[neck])))
print('skin', 'ours median', np.round(unlin(np.median(BT[masks[2] > .5], 0)) * 255).tolist(), {v: np.round(unlin(np.array(ramps[v][-1]['colors'][8])) * 255).tolist() for v in VAR}, 'texels', int(skin_b.sum()))
# body skin colour at the neck seam per tier (the ramped body tone of the dress faces in the 2 cm below the level seam, front half), for
# head_fix_pg.py's neck blend (user review r15: a colour step at the seam)
neckf = np.zeros(len(tri), int); neckf[(fc == pid['dress']) & (cen[:, 2] > 0.5703 - 0.02) & (cen[:, 2] < 0.5703) & (cen[:, 1] < 0.0)] = 1
NK = (raster(neckf) > 0) & (masks[2] > 0.5)
bn = {}
for v in VAR:
    rr = ramps[v][2]; lo, hi = rr['range']; cols = np.array(rr['colors'])
    l = BT[NK] @ LUMA; tt = np.clip((l - lo) / (hi - lo), 0, 1) * (STOPS - 1); i0 = np.floor(tt).astype(int); i1 = np.minimum(i0 + 1, STOPS - 1); f = (tt - i0)[:, None]
    c = cols[i0] * (1 - f) + cols[i1] * f
    bn[v[3:]] = (unlin(np.median(c, 0)) * 255).round(1).tolist()
nbf = np.zeros(len(tri), int); nbf[(fc == pid['dress']) & (cen[:, 2] > 0.5703 - 0.03) & (cen[:, 2] < 0.5703 + 0.001)] = 1
NB = ni.gaussian_filter((raster(nbf) > 0).astype(np.float32), 3)
NMb = np.asarray(Image.open(T / 'pg_body_normal.png').convert('RGB'), np.float32); NBs = np.asarray(Image.fromarray((NB * 255).astype('u1')).resize(NMb.shape[:2][::-1], Image.BILINEAR), np.float32)[..., None] / 255
Image.fromarray(np.clip(NMb * (1 - NBs) + np.array([128, 128, 255.]) * NBs, 0, 255).astype('u1')).save(T / 'pg_body_normal_fix.png')
json.dump(bn, open(T / 'body_neck.json', 'w')); print('body neck colours', bn, 'texels', int(NK.sum()))
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks] + [Image.new('L', (1024, 1024), 0)]
Image.merge('RGBA', chs).save(T / 'pg_body_mask.png')
json.dump({'variants': list(VAR), 'materials': [{'base': 'PeasantGirl', 'prefix': 'PeasantGirl', 'mask': 'pg_body_mask.png', 'ramps': ramps}]}, open(T / 'pg_ramps.json', 'w'))
cls = np.zeros_like(L); cls[cov] = 8; cls[np.isin(L, (8,))] = 1; cls[L == 12] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pg_material_classes.png')
pv = (np.clip(tone, 0, 1) * 120).astype('u1'); pv[..., 0] = np.maximum(pv[..., 0], (masks[0] * 255).astype('u1')); pv[..., 1] = np.maximum(pv[..., 1], (masks[1] * 255).astype('u1')); pv[..., 2] = np.maximum(pv[..., 2], (masks[2] * 255).astype('u1'))
Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
