#!/usr/bin/env python3
"""PF4 (2026-11-02): tiers_pf3.py adapted to Fre's skins: R the olive-green dress (bodice, sleeves, sleeve tubes; embroidery left out by
hue), G the apron; MM9's dress texels (A olive green, B rust brown: skin x 10-120, y 110-230) and B's dirty apron (x 160-195, y 0-90).
Original F3 notes follow.
Tier ramps on the one PF3 body paint (2026-11-02, after tiers_pf1.py). The body paint is skin A (Meshy 4K from the PF3a masters: blue
dress, white apron, white chemise edges, red lacing, red necklace). MM9's two skins differ in the dress (A mid-blue linen, B brown dirty
linen with tears) and the apron (A white, B dirty beige); arms, chest skin, lacing, necklace, shoes keep the paint.
Regions: R the blue dress cloth (bodice, sleeves, skirt; by hue inside the dress/skirt parts, lacing and chemise edges left out),
G the apron (pale, low-saturation cloth on the skirt part). Ramps map our luminance quantiles to MM9's texels of the region per tier
(dress: the skin's right strip, the skirt; apron B: MM9 B's pale apron texels, apron A: the paint's own colours).
Writes textures/pf_body_tone.png (the lining darkened), pf_body_mask.png, fre_ramps.json, pf_material_classes.png, review/tier_mask_preview.png."""
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
lab[fc == pid['dress']] = 1; lab[fc == pid['sleeve4']] = 1; lab[fc == pid['skirt']] = 2; lab[fc == pid['hands']] = 8; lab[fc == pid['legs']] = 9; lab[fc == pid['lining']] = 10
L = raster(lab); cov = L > 0
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
blue = np.isin(L, (1, 2)) & (hue > 50) & (hue < 160) & (sat > 0.15)          # PF4: the olive-green dress cloth ('blue' kept as the name)
blue = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(blue, iterations=1), iterations=3)) & np.isin(L, (1, 2))
blue &= ~((hue < 45) & (sat > 0.25))                                         # the brown/cream embroidery stays
apron = (L == 2) & (sat < 0.40) & (val > 0.45) & ~blue
apron = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(apron, iterations=2), iterations=6)) & (L == 2) & ~blue
lab_a, n_a = ni.label(apron); sz_a = ni.sum(apron, lab_a, range(1, n_a + 1)); apron = np.isin(lab_a, 1 + np.where(sz_a > 20000)[0])   # the two apron panels
print('texels', {k: int((L == k).sum()) for k in (1, 2, 8, 9, 10)}, 'blue', int(blue.sum()), 'apron', int(apron.sum()))
dk = ni.gaussian_filter((L == 10).astype(np.float32), 1.5)[..., None]
tone = unlin(B * (1 - dk) + (B * 0.30) * dk)
# r24 (review: MM9's apron is dirty greyish linen): the clean apron paint gets grime before the ramps read it: soft blotches (two scales,
# up to -22 %) and a darker band toward its hem (-18 % over the lower 25 cm), so the ramps carry the variation into both tiers
_rng = np.random.default_rng(11)
_n = sum(ni.gaussian_filter(_rng.normal(0, 1, (W, W)).astype(np.float32), sg) * k for sg, k in ((18, 1.0), (6, 0.15)))
_n = (_n - _n.mean()) / (_n.std() + 1e-6)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
reg = np.zeros_like(L); reg[blue | ((L == 10) & False)] = 1; reg[apron] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
# PF4 (review 2026-11-02): MM9 F4b's apron is torn and dirty at the hem and a teal underskirt shows under the dark skirt: two more
# regions, each a jagged band at the bottom (a 3D position raster gives the height), identity ramps on tier A
POSZ = np.full((W, W), np.nan, np.float32); POSX = np.zeros((W, W), np.float32)
for f in np.where(mat == 0)[0]:
    q = uv[tri[f]] * [W, -W] + [0, W]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), W - 1)
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l_ = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l_, 1 - l_.sum(1)]; ins = (L3 >= -0.01).all(1)
    yy_, xx_ = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int); P3 = L3[ins] @ co[tri[f]]
    POSZ[yy_, xx_] = P3[:, 2]; POSX[yy_, xx_] = np.arctan2(P3[:, 0], P3[:, 1])
zz = np.nan_to_num(POSZ, nan=9.0)
rng = np.random.default_rng(7); ang = np.linspace(-np.pi, np.pi, 721)
def jag(scale):
    n = np.cumsum(rng.normal(0, 1, len(ang))); n = n - np.convolve(n, np.ones(41) / 41, 'same'); n = n / max(np.abs(n).max(), 1e-6)
    tooth = (np.abs(((ang * 40) % 2) - 1)) * 0.5
    return np.interp(POSX, ang, n * 0.6 + tooth) * scale
apz = zz[apron].min() if apron.any() else 0.0
hemdirt = apron & (zz < apz + 0.035 + jag(0.025))
skirt_only = (L == 2) & ~apron
skz = zz[skirt_only].min() if skirt_only.any() else 0.0
under = skirt_only & (zz < skz + 0.022 + jag(0.018))
print('PF4 hem bands: apron hem', int(hemdirt.sum()), 'underskirt', int(under.sum()), 'apron z', round(float(apz), 3), 'skirt z', round(float(skz), 3))
reg[hemdirt] = 3; reg[under] = 4; Rp = reg[idx[0], idx[1]]
_ga = apron & (zz < 8.0)
_grime = np.clip(0.08 * np.clip(_n, 0, 2.0) + 0.22 * np.clip((apz + 0.35 - zz) / 0.35, 0, 1), 0, 0.35) * _ga
tone = tone * (1 - _grime[..., None])
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
print('PF4 apron grime texels', int((_grime > 0.05).sum()))
masks = [soft(Rp == 1), soft(Rp == 2), soft(Rp == 3), soft(Rp == 4)]
# ---- MM9 texels (256 skin): the skirt strip at the right; B's apron: pale low-saturation texels of the apron area (centre top of the sheet)
SK = {t: load(f'source/mm9/skins/pf4{t}.png') for t in 'ab'}
HS = {t: np.asarray(Image.open(f'source/mm9/skins/pf4{t}.png').convert('RGB').convert('HSV'), np.float32) / 255 for t in 'ab'}
yy, xx = np.mgrid[0:256, 0:256]
dressA = (xx > 10) & (xx < 120) & (yy > 110) & (yy < 230)
M9 = {'a': dressA & (HS['a'][..., 0] * 360 > 50) & (HS['a'][..., 0] * 360 < 110) & (HS['a'][..., 1] > 0.15),
      'b': dressA & (HS['b'][..., 0] * 360 > 5) & (HS['b'][..., 0] * 360 < 40) & (HS['b'][..., 1] > 0.3)}
apB = (xx > 160) & (xx < 195) & (yy < 90) & (HS['b'][..., 1] < 0.40) & (HS['b'][..., 2] > 0.35)
apA = (xx > 160) & (xx < 195) & (yy < 90) & (HS['a'][..., 1] < 0.40) & (HS['a'][..., 2] > 0.35)      # PF4: MM9 A's greyish linen
dirtB = (xx > 160) & (xx < 195) & (yy > 40) & (yy < 95) & (HS['b'][..., 2] < 0.40)                    # B's dark stains and tears
tealB = (xx > 195) & (yy > 225) & (HS['b'][..., 0] * 360 > 160) & (HS['b'][..., 0] * 360 < 210) & (HS['b'][..., 1] > 0.35)
print('PF4 MM9 apron A', int(apA.sum()), 'dirt B', int(dirtB.sum()), 'teal B', int(tealB.sum()))
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
VAR = ['pf4_a', 'pf4_b']; ramps = {v: [] for v in VAR}
wd = masks[0] * np.isin(L, (1, 2)); wa = masks[1] * (L == 2)
own_ap = BT[wa > 0.5]
for v in VAR:
    t = v[-1]
    ramps[v].append(ramp(wd, lin(SK[t][M9[t]])))
    ramps[v].append(ramp(wa, lin(SK['b'][apB]) if t == 'b' else lin(SK['a'][apA])))
    wh = masks[2] * (L == 2); wu = masks[3] * (L == 2)
    ramps[v].append(ramp(wh, lin(SK['b'][dirtB]) if (t == 'b' and dirtB.sum() > 20) else (lin(SK['a'][apA]) if t == 'a' else BT[wh > 0.5])))
    ramps[v].append(ramp(wu, lin(SK['b'][tealB]) * 0.22 if (t == 'b' and tealB.sum() > 20) else BT[wu > 0.5]))      # MM9's cyan, darkened (it glows otherwise)
# second review pass (r21, coordinator: "apron clean bright cream; MM9's is dirty greyish linen", dress lighter than MM9's): MM9's texels
# are lit darker in game than the review viewer's bright key, so the ramps are graded in sRGB: dress x DRESSK, apron x APK and 35 %
# toward grey, tier A's apron hem band a darker dirty grey (A's hem was its own apron colour)
def grade(r, k, desat=0.0):
    c = unlin(np.array(r['colors'])); l = (c @ LUMA)[:, None]; c = (c * (1 - desat) + l * desat) * k
    r['colors'] = np.clip(lin(np.clip(c, 0, 1)), 0, 1).tolist()
import os
DRESSK = float(os.environ.get('DRESSK', '0.82')); APK = float(os.environ.get('APK', '0.60'))
for v in VAR:
    grade(ramps[v][0], DRESSK)
    grade(ramps[v][1], APK if v.endswith('a') else APK * 0.92, 0.35)
    if v.endswith('a'): grade(ramps[v][2], APK * 0.70, 0.45)
print('dress ours median', np.round(unlin(np.median(BT[wd > .5], 0)) * 255).tolist(), 'apron', np.round(unlin(np.median(own_ap, 0)) * 255).tolist())
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks]
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'Fre', 'prefix': 'Fre', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'fre_ramps.json', 'w'))
cls = np.zeros_like(L); cls[cov] = 8; cls[L == 8] = 1
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = np.zeros((W, W, 3), np.uint8); pv[..., 2] = (masks[0] * 255).astype('u1'); pv[..., 1] = (masks[1] * 255).astype('u1')
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
