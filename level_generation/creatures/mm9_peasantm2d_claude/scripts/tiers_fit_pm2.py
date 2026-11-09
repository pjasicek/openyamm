#!/usr/bin/env python3
"""Tier ramps for the shared torso set (project folder). Regions (RGBA mask): R tunic body and skirt, G sleeves, B collar braid, A cuff braid.
Sleeves by arm weight (faces.npz 'arm' > 0.5), braids by paint: texels in the neckline / cuff zones that differ from the woven cloth.
Tier A = our paint (ramp fitted to itself). Tier B = a target built texel by texel: each region's base luminance quantile q takes MM9's PEASANTM2B colour at that
quantile of the same skin region, scaled by our luminance over PEASANTM2A's at q (our shading kept, B's colour; linear RGB); braid
regions flattened toward their median (B's collar is plain cream, its cuffs plain brown). Writes textures/pm2_torso_mask.png,
textures/pm2_ramps.json, review/tier_b_torso_preview.png. Belt, buckle, strap, limbs set: shared, no region."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures'); S = 1024
Z = np.load('work/faces.npz'); UV, MAT, PART, CO, ARM = Z['uv'], Z['mat'], Z['part'], Z['co'], Z['arm']
J = json.load(open('work/fit_v1.blend.joints.json'))
base = np.asarray(Image.open(T / 'pm2_torso_final.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float64) / 255
def raster(mask):
    m = Image.new('L', (S, S)); d = ImageDraw.Draw(m)
    for t in UV[mask]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
    return np.asarray(m) > 0
cen = CO.mean(1)
torso = MAT == 1
cloth = torso & np.isin(PART, (1, 7, 9))
sleeve_f = cloth & (ARM > 0.5) & (PART == 1)
body_f = cloth & ~sleeve_f
neck_f = cloth & (cen[:, 2] > 0.42) & (np.abs(cen[:, 0]) < 0.17)
def dist_hand(c):
    return np.minimum(np.linalg.norm(c - np.array(J['Bip01 L Hand']), axis=1), np.linalg.norm(c - np.array(J['Bip01 R Hand']), axis=1))
cuff_f = sleeve_f & (dist_hand(cen) < 0.19)
mb, ms, mn, mc = raster(body_f), raster(sleeve_f), raster(neck_f), raster(cuff_f)
# cloth reference: the median of the plain sleeve/body texels; braid = far from it (gold thread, dark border)
lin = RV.srgb_to_linear(base)
ref = np.median(base[(mb | ms) & ~mn & ~mc], 0)
dev = np.linalg.norm(base - ref, axis=2)
devs = np.asarray(Image.fromarray((np.clip(dev, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float64) / 255
braid = devs > 0.16
wn = (braid & mn).astype(np.float64); wc = (braid & mc).astype(np.float64)
def soft(w, k=3):
    im = Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.GaussianBlur(1.2))
    return np.asarray(im, np.float64) / 255
wn, wc = soft(wn), soft(wc)
# woven cloth by chromaticity (folds keep it, leather belt/strap and the buckle do not); near-black texels are not cloth
chrom = base / np.maximum(base.sum(2, keepdims=True), 1e-3); rch = ref / ref.sum()
cl = (np.linalg.norm(chrom[..., :2] - rch[:2], axis=2) < 0.06) & (base.max(2) > 0.06)
cl = np.asarray(Image.fromarray((cl * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.0)), np.float64) / 255
# sleeve edge: an armhole plane through each shoulder joint, normal along the upper arm (smooth on top of the shoulder, where the arm-weight
# face boundary is jagged), times the arm-weight faces softened by 3 px (under the arm)
TP = np.load('work/texpos_torso.npz'); tpos = TP['pos']
plane = np.zeros((S, S))
for s_ in 'LR':
    ua, fa = np.array(J[f'Bip01 {s_} UpperArm']), np.array(J[f'Bip01 {s_} Forearm']); d = (fa - ua) / np.linalg.norm(fa - ua)
    t = (tpos - ua) @ d; side = np.sign(tpos[..., 0]) == np.sign(ua[0])
    k = np.clip((t + 0.012) / 0.024, 0, 1); plane = np.where(side, k * k * (3 - 2 * k), plane)
msb = np.asarray(Image.fromarray((ms * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float64) / 255
cloth_t = (mb | ms).astype(np.float64)
wgs = np.clip(msb * plane, 0, 1) * cloth_t
wr = cloth_t * (1 - wgs) * cl * (1 - np.maximum(wn, wc)); wg = wgs * cl * (1 - np.maximum(wn, wc))
# MM9 skins: region rectangles (256 px skins, measured on review/skin_regions_*.png)
A9 = np.asarray(Image.open('source/true/skins/pm2_a.png').convert('RGB'), np.float64) / 255
B9 = np.asarray(Image.open('source/true/skins/pm2_b.png').convert('RGB'), np.float64) / 255
RECT = {'tunic': [(20, 130, 105, 185), (20, 130, 205, 247)], 'sleeve': [(172, 250, 10, 75)], 'collar': [(40, 135, 81, 92)], 'cuff': [(158, 167, 2, 78)]}
def px(im, k): return np.concatenate([im[y0:y1, x0:x1].reshape(-1, 3) for x0, x1, y0, y1 in RECT[k]])
Q = np.linspace(0, 1, 33)
def qcol(p):
    o = np.argsort(RV.luminance(p)); s = RV.srgb_to_linear(p[o])
    idx = np.clip((Q * (len(s) - 1)).astype(int), 0, len(s) - 1)
    return np.array([s[max(0, i - len(s) // 40):i + len(s) // 40 + 1].mean(0) for i in idx])
tierB = base.copy()
lum = RV.luminance(base); report = {}
for name, w, flat in (('tunic', wr, 0), ('sleeve', wg, 0), ('collar', wn, 0.65), ('cuff', wc, 0.65)):
    core = w > 0.5
    qa, qb = qcol(px(A9, name)), qcol(px(B9, name))
    q = np.searchsorted(np.sort(lum[core]), lum, side='left') / max(core.sum(), 1)
    bq = np.stack([np.interp(q, Q, qb[:, c]) for c in range(3)], -1)
    la = np.interp(q, Q, qa @ RV.LUMA); lb = np.interp(q, Q, qb @ RV.LUMA)
    tgt = np.clip(bq * (lum / np.maximum(la, 1e-4))[..., None], 0, 1)     # B's colour at the quantile, our shading relative to MM9 A
    ratio = lb / np.maximum(la, 1e-4)
    if flat:
        med = np.median(tgt[core], 0); tgt = med + (tgt - med) * (1 - flat)
    enc = np.where(tgt <= 0.0031308, tgt * 12.92, 1.055 * np.maximum(tgt, 0) ** (1 / 2.4) - 0.055)
    tierB = tierB * (1 - w[..., None]) + enc * w[..., None]
    report[name] = {'core': int(core.sum()), 'mm9_lum_ratio_median': round(float(np.median(ratio[core])), 2),
                    'B_median_srgb': np.round(np.median(enc[core], 0) * 255).tolist()}
ramps_all = {'pm2_a': [], 'pm2_b': []}
for w in (wr, wg, wn, wc):
    rp, rep = RV.fit_ramps(base, {'pm2_a': base, 'pm2_b': tierB}, w)
    for v in rp: ramps_all[v].append(rp[v])
    print('RAMPFIT', rep)
RV.write_mask([wr, wg, wn, wc], T / 'pm2_torso_mask.png', 1024)
json.dump({'variants': ['pm2_a', 'pm2_b'], 'materials': [{'base': 'Pm2Torso', 'prefix': 'Pm2Torso', 'mask': 'pm2_torso_mask.png', 'ramps': ramps_all}]},
          open(T / 'pm2_ramps.json', 'w'), indent=0)
Image.fromarray((np.clip(np.concatenate([base, tierB], 1), 0, 1) * 255).astype(np.uint8)).save('review/tier_b_torso_preview.png')
print('TIERS', json.dumps(report), 'cloth ref', np.round(ref * 255).tolist())
