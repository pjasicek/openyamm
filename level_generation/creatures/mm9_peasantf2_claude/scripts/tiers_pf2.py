#!/usr/bin/env python3
"""Tier ramps on the one body paint (PF2, from tiers_pf7.py). MM9's skins: A (rows 31, 38) a rust-orange dress; B (rows 32, 39) a teal-green
dress and a necklace of green and blue stones; the gold brocade neckline and bell cuffs, chemise, belt, apron, hands and shoes the same.
Regions: R the dress cloth (rust by hue; gold brocade, chemise, apron and skin left out), G the necklace beads (the geometry part).
Ramps map our luminance quantiles to MM9's texels of the region (the projected skins, project_mm9_skin.py), tier by tier.
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
for k, v in dict(dress=1, skirt=2, lining=3, hands=8, legs=9, necklace=11, buckle=12).items():
    if k in pid: lab[fc == pid[k]] = v
L = raster(lab); cov = L > 0
fz = raster(np.round((co[tri].mean(1)[:, 2] + 1.0) * 1000).astype(int)) / 1000.0 - 1.0      # face centre height (MM9 frame) per texel
base = load(T / 'pf_body_final.png'); B = lin(base)
hsv = np.asarray(Image.fromarray((base * 255).astype('u1')).convert('HSV'), np.float32) / 255
hue, sat, val = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
cloth0 = np.isin(L, (1, 2, 3)) & (hue > 8) & (hue < 33) & (sat > 0.45) & (val > 0.18)
cloth = ni.binary_fill_holes(ni.binary_closing(ni.binary_opening(cloth0, iterations=1), iterations=3)) & np.isin(L, (1, 2, 3)) & ~((sat < 0.3) & (val > 0.5)) & ~((hue > 33) & (val > 0.55))
beads = L == 11
PJ = {t: np.asarray(Image.open(f'work/mm9skin_{t}.png').convert('RGB').resize((W, W), Image.LANCZOS), np.float32) / 255 for t in 'ab'}
PH = {t: np.asarray(Image.fromarray((PJ[t] * 255).astype('u1')).convert('HSV'), np.float32) / 255 for t in 'ab'}
dress = cloth
# ---- NECK (user review 2026-11-04): the upper chest inside the neckline is skin in MM9 (both skins), but its paint passed the rust-hue test
# and took the dress ramp (A orange, B green) - the "warm orange chest" under the pale neck. Skin = dress texels in front of the shoulders,
# within 17 cm of the head/dress seam, skin-coloured (blue channel up, not the white trim, not the rust cloth). It leaves R and becomes its own
# region (B channel) whose per-tier ramp maps its luminance onto that tier's neck skin (the head paint 0.5-5.5 cm above the seam, after
# head_fix_pf2.py), and within NECK_FEATHER of the seam its paint's low frequencies are flattened to the chest median: the seam meets the
# neck's median skin from both sides.
import os, sys as _sys
_sys.path.insert(0, 'scripts'); from texpos import texel_maps
from scipy.spatial import cKDTree
_k = np.round(co, 5); _, _iv = np.unique(_k, axis=0, return_inverse=True); _iv = _iv.ravel(); _PP = np.zeros((_iv.max() + 1, 3)); _PP[_iv] = co
_hw = np.zeros(len(_PP), bool); _hw[_iv[comp == pid['head']]] = True; _dw = np.zeros(len(_PP), bool); _dw[_iv[comp == pid['dress']]] = True
_S = _PP[_hw & _dw]; _C = np.array([0.0, -0.001]); _az = np.arctan2(_S[:, 1] - _C[1], _S[:, 0] - _C[0]); _o = np.argsort(_az); _S = _S[_o]; _az = _az[_o]
_ad = np.linspace(-np.pi, np.pi, 720); _SD = np.stack([np.interp(_ad, _az, _S[:, i], period=2 * np.pi) for i in range(3)], -1)
BM = texel_maps(D, 0, W); BX, BY, BZ = [BM['pos'][..., i] for i in range(3)]
dseam = np.full((W, W), 9.0); _cv = BM['cov']; dseam[_cv] = cKDTree(_SD).query(BM['pos'][_cv])[0]
bl = base[..., 2]
skin0 = (L == 1) & (BY < 0.02) & (BZ > 0.30) & (dseam < 0.17) & (hue > 4) & (hue < 40) & (bl > 0.28) & (sat > 0.22) & (sat < 0.72) & (val > 0.6)
skin = ni.binary_opening(skin0, iterations=1); skin = ni.binary_closing(skin, iterations=2) & (L == 1) & (BY < 0.02) & (BZ > 0.30) & (dseam < 0.17)
# holes in the skin region near the seam (a small gold tick Meshy painted at the throat, specks) become skin and are painted over below
holes = ni.binary_fill_holes(skin) & ~skin & (dseam < 0.05) & (L == 1)
holes |= (L == 1) & ~skin & (dseam < 0.015) & (BY < 0.0) & (np.abs(BX) < 0.05)      # the throat strip between the seam and the beads is skin
skin |= holes
dress = cloth & ~skin
NF = float(os.environ.get('NECK_FEATHER', '0.032'))
print('texels', {k: int((L == k).sum()) for k in (1, 2, 3, 8, 9, 11, 12)}, 'cloth', int(dress.sum()), 'beads', int(beads.sum()))
tone = base.copy()
if holes.any():
    # cloned from the skin 1.5 cm aside (away from the midline) at the same height: real skin texture, no flat patch
    _hm = ni.binary_dilation(holes, iterations=3) & skin; _src = skin & ~ni.binary_dilation(holes, iterations=6)
    _q = BM['pos'][_hm] + np.c_[np.where(BX[_hm] >= 0, 0.015, -0.015), np.zeros((int(_hm.sum()), 2))]
    _, _j = cKDTree(BM['pos'][_src]).query(_q); _sk = np.zeros_like(tone); _sk[_hm] = tone[_src][_j]
    _wh = np.clip(ni.gaussian_filter(_hm.astype(np.float32), 1.0) * 1.6, 0, 1)[..., None] * _hm[..., None]
    tone = tone * (1 - _wh) + _sk * _wh
# the mirror-seam line in the chest paint (head_fix_pf2 9b, body side): skin texels |x| < 1.6 mm take a gain to the skin at |x| 2-4 mm
_ln = skin & (np.abs(BX) < 0.0016); _rg = skin & (np.abs(BX) > 0.002) & (np.abs(BX) < 0.004)
if _ln.any() and _rg.sum() > 20:
    _qq = np.c_[BY[_ln], BZ[_ln]]; _, _ii = cKDTree(np.c_[BY[_rg], BZ[_rg]]).query(_qq, k=24); _, _jj = cKDTree(_qq).query(_qq, k=24)
    tone[_ln] = np.clip(tone[_ln] * np.clip(tone[_rg][_ii].mean(1) / np.maximum(tone[_ln][_jj].mean(1), 1e-3), 0.75, 1.25), 0, 1)
print('NECK chest midline texels', int(_ln.sum()))
print('NECK skin holes painted', int(holes.sum()))
_sm = skin.astype(np.float32); _num = np.stack([ni.gaussian_filter(tone[..., c] * _sm, 8) for c in range(3)], -1); _den = ni.gaussian_filter(_sm, 8)[..., None]
_low = _num / np.maximum(_den, 1e-3); _med = np.median(tone[skin & (dseam < 0.08)], 0)
_g = np.clip(_med / np.maximum(_low, 1e-3), 0.6, 1.6); _w = np.clip((NF - dseam) / NF, 0, 1); _w = (_w * _w * (3 - 2 * _w)) * skin
tone = np.clip(tone * (1 - _w[..., None]) + tone * _g * _w[..., None], 0, 1)
# padding round the skin region's islands: the ramp also colours the uncovered texels the GPU filter reads at an island edge (a dark
# Meshy gap there drew a thin dark line along the graft): they take their nearest covered texel's colour
_ni = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); _pad = ~cov & ni.binary_dilation(skin, iterations=8)
tone[_pad] = tone[_ni[0][_pad], _ni[1][_pad]]
print('NECK skin texels', int(skin.sum()), 'padding', int(_pad.sum()), 'feathered', int((_w > 0).sum()), 'chest median', np.round(_med * 255).tolist())
Image.fromarray((np.clip(tone, 0, 1) * 255 + .5).astype('u1')).save(T / 'pf_body_tone.png')
reg = np.zeros_like(L); reg[dress] = 1; reg[beads] = 2; reg[skin] = 3
idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True); Rp = reg[idx[0], idx[1]]
def soft(m, s=0.8): return np.clip(ni.gaussian_filter(m.astype(np.float32), s), 0, 1)
masks = [soft(Rp == 1), soft(Rp == 2, 0.5), soft(Rp == 3, 1.2)]
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
pa_h, pa_s = PH['a'][..., 0] * 360, PH['a'][..., 1]; pb_h, pb_s = PH['b'][..., 0] * 360, PH['b'][..., 1]
rust_a = (pa_h > 6) & (pa_h < 32) & (pa_s > 0.45)
teal_b = (pb_h > 120) & (pb_h < 200) & (pb_s > 0.2)
VAR = ['pf2_a', 'pf2_b']; ramps = {v: [] for v in VAR}
ramps['pf2_a'].append(ramp(masks[0], tgt('a', masks[0], rust_a))); ramps['pf2_b'].append(ramp(masks[0], tgt('b', masks[0], teal_b)))
cop_a = tgt('a', ni.binary_dilation(beads, iterations=6).astype(np.float32), ((pa_h > 5) & (pa_h < 35) & (pa_s > 0.45)))
ramps['pf2_a'].append(ramp(masks[1], cop_a if len(cop_a) > 30 else lin(np.array([[0.45, 0.15, 0.05], [0.7, 0.3, 0.1]]))))
gem_b = tgt('b', ni.binary_dilation(beads, iterations=6).astype(np.float32), ((pb_h > 100) & (pb_h < 260) & (pb_s > 0.25)))
ramps['pf2_b'].append(ramp(masks[1], gem_b if len(gem_b) > 30 else lin(np.array([[0.12, 0.45, 0.35], [0.15, 0.3, 0.6]]))))
HM = texel_maps(D, 1, 1024); HX, HY, HZ = [HM['pos'][..., i] for i in range(3)]
_ha = np.arctan2(HY - _C[1], HX - _C[0]); _hs = HZ - np.interp(_ha, _az, _S[:, 2], period=2 * np.pi)
_nk = HM['cov'] & (HM['part'] == pid['head']) & (HZ < 0.60) & (_hs > 0.005) & (_hs < 0.055)
for v_ in VAR:
    _hi = load(T / f'pf_head_{v_[-1]}_fix.png'); ramps[v_].append(ramp(masks[2], lin(_hi[_nk])))
    print('skin ramp', v_, 'neck texels', int(_nk.sum()), 'mid', np.round(unlin(np.array(ramps[v_][2]['colors'][8])) * 255).tolist())
for k, nm in enumerate(('dress', 'beads')):
    print(nm, {v: np.round(unlin(np.array(ramps[v][k]['colors'][8])) * 255).tolist() for v in VAR}, 'B target texels', len(gem_b) if k else '')
chs = [Image.fromarray((x * 255 + .5).astype('u1')).resize((1024, 1024), Image.LANCZOS) for x in masks] + [Image.new('L', (1024, 1024), 0)] * (4 - len(masks))
Image.merge('RGBA', chs).save(T / 'pf_body_mask.png')
json.dump({'variants': VAR, 'materials': [{'base': 'PeasantF2', 'prefix': 'PeasantF2', 'mask': 'pf_body_mask.png', 'ramps': ramps}]}, open(T / 'pf_ramps.json', 'w'))
cls = np.zeros_like(L); cls[cov] = 8; cls[(L == 8)] = 1; cls[L == 11] = 11; cls[L == 12] = 9
Image.fromarray(cls.astype('u1')).resize((1024, 1024), Image.NEAREST).save(T / 'pf_material_classes.png')
pv = (base * 120).astype('u1'); pv[masks[0] > .5] = (40, 200, 40); pv[masks[1] > .5] = (40, 40, 255); pv[masks[2] > .5] = (240, 200, 160)
Path('review').mkdir(exist_ok=True); Image.fromarray(pv).resize((1024, 1024)).save('review/tier_mask_preview.png')
print('TIERS')
