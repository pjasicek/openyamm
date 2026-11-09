#!/usr/bin/env python3
"""Tier ramps on the one body paint (PF1, after PF8's tiers_pf.py). MM9's two skins differ in the bodice (B rust-orange laced, A black with
gold embroidery) and the skirt (B maroon, A olive-brown); blouse, apron, arms and shoes are the same and keep the paint. The hood is in the
head set (one head paint per tier). Regions: R bodice (lacing left out), G skirt (apron left out; lining at the bottom of the ramp),
A the tier-A embroidery: MM9's own skin A projected onto our bodice (project_mm9_skin.py), its gold texels; tier B gives that channel the
bodice ramp, so B shows plain cloth there. Ramps map our luminance quantiles to MM9's texels of the region, tier by tier.
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
fc = comp[tri[:, 0]]; cx = np.abs(co[tri].mean(1)[:, 0])
lab = np.zeros(len(tri), int)
lab[fc == pid['dress']] = 1; lab[(fc == pid['dress']) & (cx > 0.175)] = 3          # bodice/blouse, sleeves
fz = co[tri].mean(1)[:, 2] + 0.9297
lab[(fc == pid['dress']) & (fz > 1.385) & (cx < 0.075)] = 12      # collar
lab[fc == pid['skirt']] = 2; lab[fc == pid['hands']] = 8; lab[fc == pid['legs']] = 9; lab[fc == pid['lining']] = 10
L = raster(lab); cov = L > 0
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
apron = (L == 2) & (sat < 0.38) & (val > 0.45)
apron = ni.binary_opening(apron, iterations=2); apron = ni.binary_fill_holes(ni.binary_closing(apron, iterations=6)) & (L == 2)
cc, ncc = ni.label(L == 2)
fr = ni.mean(apron.astype(float), cc, range(1, ncc + 1))
for k_, f_ in enumerate(fr, 1):
    if f_ > 0.6: apron |= cc == k_
# bodice: the rust-orange cloth of the dress part (the lacing, eyelets and blouse are not)
red = ((hue < 28) | (hue > 340)) & (sat > 0.42) & (val > 0.25)
bod = ni.binary_opening(np.isin(L, (1, 12)) & red, iterations=1)
bod = ni.binary_fill_holes(ni.binary_closing(bod, iterations=3)) & np.isin(L, (1, 12))
lace = bod & ((sat < 0.35) | (val < 0.22))
bod &= ~ni.binary_dilation(lace, iterations=1)
print('texels', {k: int((L == k).sum()) for k in (1, 2, 3, 8, 9, 10)}, 'apron', int(apron.sum()), 'bodice', int(bod.sum()), 'lacing', int(lace.sum()))
# ---- base: the lining dark (the inside of the skirt), feathered
dk = ni.gaussian_filter((L == 10).astype(np.float32), 1.5)[..., None]
Bc = B.copy()
# the collar: Meshy put an orange spot of bodice paint at the front of the cream collar
col = L == 12; ora0 = np.isin(L, (1, 12)) & (hue < 32) & (sat > 0.45)
lab_o, n_o = ni.label(ora0); sz_o = ni.sum(ora0, lab_o, range(1, n_o + 1))
small = np.isin(lab_o, 1 + np.where(sz_o < 6000)[0]) & (lab_o > 0)          # isolated spots, not the bodice
ora = small & col
ora = ni.binary_dilation(ora, iterations=2) & col
if ora.any():
    cream = np.median(B[col & ~ora & (sat < 0.3)], 0); ko = np.clip(ni.gaussian_filter(ora.astype(np.float32), 1.0) * 1.5, 0, 1)[..., None] * col[..., None]
    lB = B @ LUMA; det = (lB - ni.gaussian_filter(lB, 2.0))[..., None]
    Bc = B * (1 - ko) + np.clip(cream + det * 0.5, 0, 1) * ko
print('collar orange texels', int(ora.sum()))
# the standing collar up to the neck seam: Meshy painted skin in jagged teeth into it (a zigzag at the head seam); cream throughout
fz_l = raster(np.where(lab == 12, 1, 0))
skn = (fz_l == 1) & (hue > 2) & (hue < 40) & (sat > 0.18) & (sat < 0.62) & (val > 0.38)
skn = ni.binary_dilation(skn, iterations=1) & (fz_l == 1)
if skn.any():
    cr2 = np.median(Bc[(fz_l == 1) & ~skn & (sat < 0.25) & (val > 0.6)], 0); kc = np.clip(ni.gaussian_filter(skn.astype(np.float32), 1.0) * 1.5, 0, 1)[..., None] * (fz_l == 1)[..., None]
    lB = Bc @ LUMA; det = (lB - ni.gaussian_filter(lB, 2.0))[..., None]
    Bc = Bc * (1 - kc) + np.clip(cr2 + det * 0.5, 0, 1) * kc
print('collar skin texels', int(skn.sum()))
# apron: Meshy splashed skirt-red specks on the apron's lower part; they kept tier B's red on the olive tier A. The apron's own cream instead.
ap_cl = ni.binary_fill_holes(ni.binary_closing(apron, iterations=14)) & (L == 2)      # the ragged hem's skirt-red blobs closed into the apron
spk = ap_cl & (((hue < 30) | (hue > 330)) & (sat > 0.28) | ~apron)
spk = ni.binary_dilation(spk, iterations=1) & ap_cl
if spk.any():
    ac = np.median(B[ap_cl & ~spk], 0); ks = np.clip(ni.gaussian_filter(spk.astype(np.float32), 0.8) * 1.5, 0, 1)[..., None] * ap_cl[..., None]
    lB = Bc @ LUMA; det = (lB - ni.gaussian_filter(lB, 2.0))[..., None]
    Bc = Bc * (1 - ks) + np.clip(ac + det * 0.5, 0, 1) * ks
print('apron specks', int(spk.sum()))
apron = ap_cl
tone = unlin(Bc * (1 - dk) + (Bc * 0.30) * dk)
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
# ---- tier-A embroidery from MM9's skin A on our bodice
PA = np.asarray(Image.open('work/proj_a.png').convert('RGB').resize((W, W), Image.LANCZOS))
ph = np.asarray(Image.fromarray(PA).convert('HSV'), np.float32) / 255
gold = np.clip((ph[..., 1] - 0.22) / 0.12, 0, 1) * np.clip((ph[..., 2] - 0.26) / 0.10, 0, 1) * ((ph[..., 0] * 360 > 16) & (ph[..., 0] * 360 < 58))
gold = ni.gaussian_filter(gold.astype(np.float32), 1.2)
gold = np.clip((gold - 0.48) / 0.22, 0, 1) * 0.9 * ni.binary_dilation(bod, iterations=2)
# ---- masks, labels padded into the gutters first
reg = np.zeros_like(L); reg[bod] = 1; reg[((L == 2) & ~apron) | (L == 10)] = 2
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]; Gp = gold[idx[0], idx[1]]
def soft(m): return np.clip(ni.gaussian_filter(m.astype(np.float32), 0.8), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2), np.zeros((W, W), np.float32), np.clip(Gp, 0, 1)]
# ---- MM9 texels (256 skin coordinates): bodice lower left, skirt the right strip, gold embroidery on A
SK = {t: load(f'source/mm9/skins/pf1{t}.png') for t in 'ab'}
HS = {t: np.asarray(Image.open(f'source/mm9/skins/pf1{t}.png').convert('RGB').convert('HSV'), np.float32) / 255 for t in 'ab'}
yy, xx = np.mgrid[0:256, 0:256]; brect = (xx > 18) & (xx < 125) & (yy > 120) & (yy < 245)
def goldm(h): return (h[..., 0] * 360 > 18) & (h[..., 0] * 360 < 55) & (h[..., 1] > 0.28) & (h[..., 2] > 0.28)
M9 = {'b': {'bodice': brect & ((HS['b'][..., 0] * 360 < 20) | (HS['b'][..., 0] * 360 > 340)) & (HS['b'][..., 1] > 0.5), 'skirt': xx > 205},
      'a': {'bodice': brect & (HS['a'][..., 2] < 0.32) & ~ni.binary_dilation(goldm(HS['a']), iterations=1), 'skirt': xx > 205, 'gold': brect & goldm(HS['a'])}}
print('MM9 texels', {t: {k: [int(m.sum()), np.round(np.median(SK[t][m], 0) * 255).tolist()] for k, m in M9[t].items()} for t in 'ab'})
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
for key, m, lb in (('bodice', masks[0], (1, 12)), ('skirt', masks[1], (2, 10))):
    wgt = m * np.isin(L, lb)
    for v in VAR:
        ramps[v].append(ramp(wgt, lin(SK[v[-1]][M9[v[-1]][key]])))
    print(key, 'ours median', np.round(unlin(np.median(BT[wgt > .5], 0)) * 255).tolist())
for v in VAR: ramps[v].append({'range': [0.0, 1.0], 'colors': [[0.5, 0.5, 0.5]] * STOPS})      # B channel unused (no mask)
ramps['pf1_b'].append(dict(ramps['pf1_b'][0]))                                                # embroidery channel = plain bodice on B
ramps['pf1_a'].append(ramp(masks[3] * np.isin(L, (1, 12)), lin(SK['a'][M9['a']['gold']]) * 0.72))
print('gold texels', int((masks[3] > 0.5).sum()))
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks]
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF1', 'prefix': 'PeasantF1', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
# ---- material classes (1 skin, 8 cloth/leather), 1K, nearest
cls = np.zeros_like(L); cls[cov] = 8; cls[L == 8] = 1
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = np.zeros((W, W, 3), np.uint8); pv[..., 0] = (masks[0] * 255).astype('u1'); pv[..., 1] = (masks[1] * 255).astype('u1'); pv[apron] = (255, 255, 255); pv[masks[3] > 0.5] = (255, 220, 0)
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
