#!/usr/bin/env python3
"""Tier ramps (project folder). Tiers: eb (Ebora, row 301, own paint), s1 (Concubine, row 302, siren1: own paint),
s2..s4 (EBORACONCUBINE.scr's random skins siren2-4: the siren paint + region mask + ramps).
- Body sets (torso, head, legs) on the siren paint, four regions: R hair (hair/fringe charts), G skin (peach texels),
  B suit (everything else), A black (boots, horns, dark trim). Ramps for s2..s4: quantile matching of our region's
  luminance to MM9's siren<k> texels of the same region (regions classified on siren1, read at the same texels of
  siren<k>: the four skins share one layout), fitted with region_variants.fit_ramps.
- Wing (one paint, Ebora's red): R membrane, G bone. s1..s4 membrane from MM9's siren<k> wing strip; bone keeps its own
  grey.
Writes textures/eb_tiers.json and the masks textures/sr_{set}_mask.png, eb_wing_mask.png."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, '../claude_shared')
import region_variants as RV
LUM = np.array([0.2126, 0.7152, 0.0722])
lin = RV.srgb_to_linear
def hsv(a):
    mx = a.max(-1); mn = a.min(-1); d = mx - mn + 1e-9
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    return h, d / (mx + 1e-9), mx
def ndimage_idx(mask):
    return ndi.distance_transform_edt(mask, return_distances=False, return_indices=True)
load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float64) / 255
# MM9 regions on the siren skins (128x128, top origin)
SK = {k: load(f'source/siren{k}/skins/siren{k}.png') for k in (1, 2, 3, 4)}
s1 = SK[1]; Hs, Ws = s1.shape[:2]; yy, xx = np.mgrid[0:Hs, 0:Ws] / np.array([Hs, Ws])[:, None, None]
h, s, v = hsv(s1)
wing_rect = (yy > 0.765) & (yy < 0.90) & (xx < 0.585)
m_wing = wing_rect & (v > 0.18)
m_hair = ~wing_rect & (xx < 0.42) & (yy < 0.42) & ((h < 0.06) | (h > 0.95)) & (s > 0.6) & (v > 0.3)
m_skin = ~wing_rect & (h > 0.02) & (h < 0.12) & (s > 0.15) & (s < 0.62) & (v > 0.5)
m_black = ~wing_rect & ~m_skin & ~m_hair & ((v < 0.16) | ((h > 0.45) & (h < 0.75)))
m_suit = ~wing_rect & ~m_skin & ~m_hair & ~m_black
MM = {'hair': m_hair, 'skin': m_skin, 'suit': m_suit, 'black': m_black, 'memb': m_wing}
print('MM9 region texels', {k: int(v_.sum()) for k, v_ in MM.items()})
def region_colour(k, region):
    """median linear colour of MM9 siren<k>'s texels of a region, filtered to that region's material in that skin
    (siren1's suit positions show bare skin on siren3/4; its dark lace turns orange brocade on siren2)"""
    src = SK[k][MM[region]]; h_, s_, v_ = hsv(src)
    if region == 'black': keep = v_ < 0.28
    elif region == 'suit': keep = ~((s_ < 0.32) & (v_ > 0.55)) & (v_ > 0.06)
    elif region == 'skin': keep = v_ > 0.45
    else: keep = np.ones(len(src), bool)
    if keep.sum() < 20: keep = np.ones(len(src), bool)
    return np.median(lin(src[keep]), 0)
def target_image(base, weight, k, region, shoulder=False):
    """the region's MM9 colour times our relative luminance (keeps our detail and contrast). shoulder (head skin, ear sweep
    2026-11-02): where the scaled colour passes 1 in a channel it is scaled back to max 1 (hue and saturation kept);
    per-channel clipping turned the brightest skin (the lightened chin underside) yellow, which read as an olive throat on s2
    from below. Lifting it toward white to its own luminance instead read as a pale grey-white patch: dropped. Only s2: s3/s4
    skin goes to white at the top, as MM9's pale sirens, and was not faulty"""
    c = region_colour(k, region); L = lin(base) @ LUM
    if region == 'hair':      # dark hair keeps its strand sheen: median no darker than sRGB ~40 (Ebora's painted black hair)
        floor = lin(np.array(40 / 255.0)); lc = c @ LUM
        if lc < floor: c = c * (floor / max(lc, 1e-5))
    Lm = np.median(L[weight > 0.5]) if (weight > 0.5).any() else L.mean()
    t = np.clip(L / max(Lm, 1e-4), 0, 3)[..., None] * c[None, None, :]
    if shoulder:
        t = t / np.maximum(t.max(-1, keepdims=True), 1)
    enc = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
    return np.clip(enc(np.clip(t, 0, 1)), 0, 1)
# our body regions on the siren paint
D = np.load('work/uv_frozen.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']
NAMES = ['body', 'hair', 'belt', 'horns', 'fringe', 'emblem', 'eyes', 'ears', 'spikes', 'mouth', 'drop']
out = {'variants': ['eb', 's1', 's2', 's3', 's4'], 'materials': {}}
report = {}
SETS = {'torso': (0, lambda u: (u[0], u[1] * 2)), 'head': (1, lambda u: (u[0] * 2, (u[1] - 0.5) * 2)), 'legs': (2, lambda u: ((u[0] - 0.5) * 2, (u[1] - 0.5) * 2))}
for name, (mi, f) in SETS.items():
    base = load(f'textures/sr_{name}_tone.png'); Hh, Ww = base.shape[:2]
    hairm = Image.new('L', (Ww, Hh), 0); dr = ImageDraw.Draw(hairm)
    for t, m_ in zip(tri, mat):
        if m_ != mi or comp[t[0]] not in (NAMES.index('hair'), NAMES.index('fringe')): continue
        dr.polygon([(float(f(uv[i])[0] * Ww), float((1 - f(uv[i])[1]) * Hh)) for i in t], fill=255)
    hair = ndi.binary_dilation(np.asarray(hairm) > 0, iterations=3).astype(float)
    h, s, v = hsv(base)
    if name == 'head':        # scalp charts under the hair shell carry hair paint too
        copper = (h > 0.018) & (h < 0.08) & (s > 0.55) & (v > 0.12)      # orange copper only: crimson lips stay out
        facem = Image.new('L', (Ww, Hh), 0); dr2 = ImageDraw.Draw(facem)     # face front charts: lips stay out of the hair
        for t, m_ in zip(tri, mat):
            c3 = D['co'][t].mean(0) if 'co' in D.files else None
            if m_ != mi or comp[t[0]] != NAMES.index('body') or c3 is None or not (c3[1] < 0.02 and 0.78 < c3[2] < 0.92): continue
            dr2.polygon([(float(f(uv[i])[0] * Ww), float((1 - f(uv[i])[1]) * Hh)) for i in t], fill=255)
        copper &= ~ndi.binary_dilation(np.asarray(facem) > 0, iterations=4)
        hair = np.maximum(hair, ndi.binary_opening(copper, iterations=1).astype(float))
    skin = ((h > 0.02) & (h < 0.13) & (s > 0.12) & (s < 0.6) & (v > 0.45)).astype(float) * (1 - hair)
    black = ((v < 0.17) | ((h > 0.5) & (h < 0.8) & (v < 0.5))).astype(float) * (1 - hair) * (1 - skin)
    sm = lambda x: np.clip(ndi.gaussian_filter(x, 1.0), 0, 1)
    hair, skin, black = sm(hair), sm(skin), sm(black)
    suit = np.clip(1 - hair - skin - black, 0, 1)
    if name == 'head':   # head pass 2026-11-01: regions from the mesh parts (the painted shading broke the colour test)
        HF = np.load('work/head_faces.npz'); pim = Image.new('L', (Ww, Hh), 255); dp = ImageDraw.Draw(pim)
        for uvt, pt in zip(HF['uv'], HF['part']):
            dp.polygon([(float(u_[0] * Ww), float((1 - u_[1]) * Hh)) for u_ in uvt], fill=int(pt))
        pa = np.asarray(pim); pa = pa[tuple(ndimage_idx(pa == 255))] if (pa == 255).any() else pa
        sm2 = lambda x: np.clip(ndi.gaussian_filter(x.astype(float), 1.0), 0, 1)
        hair = sm2(np.isin(pa, (1, 4))); black = sm2(pa == 3); skin = sm2(np.isin(pa, (0, 7, 9, 6)))
        suit = np.zeros_like(hair)
    W = [hair, skin, suit, black]
    if name == 'head':   # lips and eyes keep the siren1 paint on every tier (all four MM9 skins have dark red lips)
        eyem = Image.new('L', (Ww, Hh), 0); dr3 = ImageDraw.Draw(eyem)
        for t, m_ in zip(tri, mat):
            if m_ != mi or comp[t[0]] != NAMES.index('eyes'): continue
            dr3.polygon([(float(f(uv[i])[0] * Ww), float((1 - f(uv[i])[1]) * Hh)) for i in t], fill=255)
        mouthm = Image.new('L', (Ww, Hh), 0); dr4 = ImageDraw.Draw(mouthm)       # the mouth area only (the hairline's copper paint matched the lip test)
        HF2 = np.load('work/head_faces.npz')
        for uvt, cot in zip(HF2['uv'], HF2['co']):
            c3 = cot.mean(0)
            if abs(c3[0]) < 0.035 and 0.805 < c3[2] < 0.848 and c3[1] < 0.02:
                dr4.polygon([(float(u_[0] * Ww), float((1 - u_[1]) * Hh)) for u_ in uvt], fill=255)
        lips = (np.asarray(mouthm) > 0) & ((h > 0.93) | (h < 0.035)) & (s > 0.28) & (v < 0.85) & (v > 0.12)
        lips = ndi.binary_opening(lips, iterations=1)
        keep = np.clip(ndi.gaussian_filter((lips | (np.asarray(eyem) > 0)).astype(float), 1.0) * 1.5, 0, 1)
        W = [w * (1 - keep) for w in W]
        print('head: lips + eyes kept from the paint', int((keep > 0.5).sum()), 'texels')
    RV.write_mask(W, f'textures/sr_{name}_mask.png', size=(Ww // 2, Hh // 2))
    ramps = {}
    for ri, (rn, w) in enumerate(zip(('hair', 'skin', 'suit', 'black'), W)):
        if (w >= 0.9).sum() < 100:
            ramps[ri] = None; continue
        tiers = {f's{k}': target_image(base, w, k, rn, shoulder=(name == 'head' and rn == 'skin' and k == 2)) for k in (2, 3, 4)}
        r_, rep = RV.fit_ramps(base, tiers, w)
        ramps[ri] = r_; report[f'{name}/{rn}'] = rep
    # regions too small to fit: flat ramp of the region's own colour range (identity in luminance)
    per_variant = {}
    for vname in ('s2', 's3', 's4'):
        lst = []
        for ri in range(4):
            if ramps[ri] is None:
                lst.append(RV.tint_ramp(base, W[ri] if W[ri].sum() > 0 else np.ones(base.shape[:2]), [1, 1, 1]))
            else:
                lst.append(ramps[ri][vname])
        per_variant[vname] = lst
    out['materials'][f'Ebora{name.capitalize()}'] = {'mask': f'sr_{name}_mask.png', 'base': f'sr_{name}_tone.png', 'ramps': per_variant}
# wing
wb = load('textures/eb_wing_base.png'); R = np.load('work/wing_regions.npz'); memb, bone = R['memb'], R['bone']
RV.write_mask([memb, bone], 'textures/eb_wing_mask.png', size=(1024, 512))
tiers = {f's{k}': target_image(wb, memb, k, 'memb') for k in (1, 2, 3, 4)}
r_m, rep = RV.fit_ramps(wb, tiers, memb); report['wing/membrane'] = rep
r_b, rep = RV.fit_ramps(wb, {f's{k}': wb for k in (1, 2, 3, 4)}, bone); report['wing/bone'] = rep
out['materials']['EboraWing'] = {'mask': 'eb_wing_mask.png', 'base': 'eb_wing_base.png', 'ramps': {f's{k}': [r_m[f's{k}'], r_b[f's{k}']] for k in (1, 2, 3, 4)}}
json.dump(out, open('textures/eb_tiers.json', 'w'))
json.dump(report, open('textures/eb_tiers_report.json', 'w'), indent=1)
print('TIERS', {k: v_ for k, v_ in report.items()})
