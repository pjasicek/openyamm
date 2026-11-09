#!/usr/bin/env python3
"""PeasantM2d tier ramps for the shared torso set (project folder; after tiers_fit_pm2.py of PeasantM2). The torso paint is skin D's
design (Meshy 4K on PeasantM2's frozen layout): a sleeveless forest-green tunic over cream sleeves, brown-gold braid trims, brown belt,
silver buckle and brooch. Tier pm2d_d (row 26, PEASANTM2D) = the paint itself (ramps fitted to itself). Tier pm2d_c (row 24, PEASANTM2C)
= the same art with a teal tunic AND teal sleeves (MM9's C skin; its trims, trousers and boots are D's).
Regions by paint class, not geometry (both regions turn teal on C, so the vest/sleeve boundary is wherever Meshy painted it):
R = green tunic cloth (chromaticity within 0.05 of the median of the torso-cloth faces), G = cream sleeve cloth (same, median of the
arm-weighted sleeve faces). Braids, belt, buckle, brooch and dark linings fall outside both. Target per texel = C's colour at the texel's
luminance quantile in its region, scaled by our luminance over D's at that quantile (MM9 skin rectangles, 256 px), as tiers_fit_pm2.py.
Writes textures/pm2d_torso_mask.png, textures/pm2d_ramps.json, review/tier_c_torso_preview.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, '../claude_shared')
import region_variants as RV
T = Path('textures'); S = 1024
Z = np.load('work/faces.npz'); UV, MAT, PART, CO, ARM = Z['uv'], Z['mat'], Z['part'], Z['co'], Z['arm']
base = np.asarray(Image.open(T / 'pm2d_torso_final.png').convert('RGB').resize((S, S), Image.LANCZOS), np.float64) / 255
def raster(mask):
    m = Image.new('L', (S, S)); d = ImageDraw.Draw(m)
    for t in UV[mask]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
    return np.asarray(m) > 0
cloth = (MAT == 1) & np.isin(PART, (1, 7, 9))
sleeve_f = cloth & (ARM > 0.5) & (PART == 1)
body_f = cloth & ~sleeve_f
mb, ms, mall = raster(body_f), raster(sleeve_f), raster(MAT == 1)
chrom = base / np.maximum(base.sum(2, keepdims=True), 1e-3)
def cls(ref_mask, tol):
    ref = np.median(chrom[ref_mask], 0)
    c = (np.linalg.norm(chrom[..., :2] - ref[:2], axis=2) < tol) & (base.max(2) > 0.06) & mall
    c = np.asarray(Image.fromarray((c * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.0)), np.float64) / 255
    return c, ref
TOL = float(sys.argv[1]) if len(sys.argv) > 1 else 0.045
THR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.38     # luminance (sRGB 0..1, Rec.709) between the dark tunic and the cream sleeves
lum0 = base @ np.array([0.2126, 0.7152, 0.0722])
core_t = mb & (lum0 < THR - 0.08); core_s = ms & (lum0 > THR + 0.08)
rg = np.median(chrom[core_t], 0); rc = np.median(chrom[core_s], 0)
def near(ref): return np.linalg.norm(chrom[..., :2] - ref[:2], axis=2) < TOL
sm = lambda m: np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.GaussianBlur(1.0)), np.float64) / 255
k = np.clip((lum0 - (THR - 0.06)) / 0.12, 0, 1); k = k * k * (3 - 2 * k)
ok = (base.max(2) > 0.06) & mall
wr = sm(near(rg) & ok & (k < 0.5)) * (1 - k) * 2 * np.minimum(1 - k, 0.5)
wg = sm(near(rc) & ok & (k >= 0.5)) * k * 2 * np.minimum(k, 0.5)
wr, wg = np.clip(wr * 2, 0, 1), np.clip(wg * 2, 0, 1)
# pad into the gutters (texels outside every island take the largest neighbouring weight), so filtering draws no tier-D seam lines on C
from scipy import ndimage
wr = np.where(mall, wr, ndimage.grey_dilation(wr, size=9)); wg = np.where(mall, wg, ndimage.grey_dilation(wg, size=9))
C9 = np.asarray(Image.open('source/true/skins/pm2d_c.png').convert('RGB'), np.float64) / 255
D9 = np.asarray(Image.open('source/true/skins/pm2d_d.png').convert('RGB'), np.float64) / 255
RECT = {'tunic': [(14, 130, 100, 185), (14, 130, 210, 245)], 'sleeve': [(172, 250, 8, 72)]}
def px(im, k): return np.concatenate([im[y0:y1, x0:x1].reshape(-1, 3) for x0, x1, y0, y1 in RECT[k]])
Q = np.linspace(0, 1, 33)
def qcol(p):
    o = np.argsort(RV.luminance(p)); s = RV.srgb_to_linear(p[o])
    idx = np.clip((Q * (len(s) - 1)).astype(int), 0, len(s) - 1)
    return np.array([s[max(0, i - len(s) // 40):i + len(s) // 40 + 1].mean(0) for i in idx])
lum = RV.luminance(base); tierC = base.copy(); report = {}
for name, w in (('tunic', wr), ('sleeve', wg)):
    core = w > 0.5
    qd, qc = qcol(px(D9, name)), qcol(px(C9, name))
    q = np.searchsorted(np.sort(lum[core]), lum, side='left') / max(core.sum(), 1)
    cq = np.stack([np.interp(q, Q, qc[:, c]) for c in range(3)], -1)
    ld = np.interp(q, Q, qd @ RV.LUMA)
    tgt = np.clip(cq * (lum / np.maximum(ld, 1e-4))[..., None], 0, 1)
    enc = np.where(tgt <= 0.0031308, tgt * 12.92, 1.055 * np.maximum(tgt, 0) ** (1 / 2.4) - 0.055)
    tierC = tierC * (1 - w[..., None]) + enc * w[..., None]
    report[name] = {'core_texels': int(core.sum()), 'C_median_srgb': np.round(np.median(enc[core], 0) * 255).tolist(),
                    'D_paint_median_srgb': np.round(np.median(base[core], 0) * 255).tolist()}
ramps_all = {'pm2d_d': [], 'pm2d_c': []}
for w in (wr, wg):
    rp, rep = RV.fit_ramps(base, {'pm2d_d': base, 'pm2d_c': tierC}, w)
    for v in rp: ramps_all[v].append(rp[v])
    print('RAMPFIT', rep)
RV.write_mask([wr, wg], T / 'pm2d_torso_mask.png', 1024)
json.dump({'variants': ['pm2d_d', 'pm2d_c'], 'materials': [{'base': 'Pm2dTorso', 'prefix': 'Pm2dTorso', 'mask': 'pm2d_torso_mask.png', 'ramps': ramps_all}]},
          open(T / 'pm2d_ramps.json', 'w'), indent=0)
Image.fromarray((np.clip(np.concatenate([base, tierC], 1), 0, 1) * 255).astype(np.uint8)).save('review/tier_c_torso_preview.png')
print('TIERS', json.dumps(report), 'refs green', np.round(rg, 3).tolist(), 'cream', np.round(rc, 3).tolist())
