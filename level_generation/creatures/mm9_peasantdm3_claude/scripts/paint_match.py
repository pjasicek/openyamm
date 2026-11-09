#!/usr/bin/env python3
"""Shared-paint correction (MM9-vs-ours sheet r2: our boots bright tan suede and belt bright red, both MM9 skins dark brown
leather): boot and belt texels of the body paint take MM9 PEASANTDM3B's own boot / belt colours at the texel's luminance
quantile, times the gain that maps MM9 B's tunic onto our tunic (median linear luminance), feathered 1 px. Neither region
differs between the tiers in MM9 enough to need a ramp, so this is a base-paint fix, not a per-tier bake.
Reads textures/<prefix>_basecolor_graded_prematch.png (made on the first run; run after neck_body_fix.py).
Usage (project folder): paint_match.py <export glb> <prefix>"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_variants as RV
from headpos import texel_positions
glb, prefix = sys.argv[1:3]
T = Path(f'textures/{prefix}_basecolor_graded.png'); B = Path(f'textures/{prefix}_basecolor_graded_prematch.png')
if not B.exists(): shutil.copy(T, B)
img = np.asarray(Image.open(B).convert('RGB'), np.float64) / 255
N = img.shape[0]
pos, cov = texel_positions(glb, 'PeasantDM3', N)
Y, X = np.nan_to_num(pos[..., 1], nan=-1), np.nan_to_num(pos[..., 0])
W = np.array([0.2126, 0.7152, 0.0722])
lin = RV.srgb_to_linear(img); lum = lin @ W
mx, mn = img.max(2), img.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
hue = np.degrees(np.arctan2(np.sqrt(3) * (img[..., 1] - img[..., 2]), 2 * img[..., 0] - img[..., 1] - img[..., 2])) % 360
mask = np.asarray(Image.open('textures/pdm3_region_mask.png').convert('RGBA').resize((N, N), Image.BILINEAR), np.float64) / 255
cls = np.asarray(Image.open(f'textures/{prefix}_material_classes.png').convert('L').resize((N, N), Image.NEAREST))
skin = np.asarray(Image.open('source/mm9/skins/pdm3b.png').convert('RGB'), np.float64) / 255
sl = RV.srgb_to_linear(skin)
def px(x0, x1, y0, y1): return sl[y0:y1, x0:x1].reshape(-1, 3)
mm9_tunic = px(125, 170, 85, 195)
tunic_core = (mask[..., 0] > 0.9) & cov
gain = np.median(lum[tunic_core]) / np.median(mm9_tunic @ W)
boots = cov & (Y < 0.315) & (Y > 0.0) & (mask[..., 3] < 0.2) & (cls != 9) & (sat > 0.25) & (hue > 10) & (hue < 50)
belt = cov & (Y > 0.595) & (Y < 0.66) & (np.abs(X) < 0.35) & (cls != 9) & (sat > 0.45) & ((hue < 25) | (hue > 330))
boots = ndimage.binary_opening(boots, iterations=1); belt = ndimage.binary_opening(belt, iterations=1)
out = lin.copy(); rep = {'gain': round(float(gain), 3)}
# STRENGTH: our tunic paint is a high-contrast stripe whose median sits in the dark stripes, so the full transfer made
# the boots near black; half way keeps them clearly darker leather than the bright suede
for name, m, src, STRENGTH in (('boots', boots, px(200, 255, 165, 250), 0.5), ('belt', belt, px(10, 120, 234, 252), 0.6)):
    order = np.argsort(src @ W)
    rank = np.argsort(np.argsort(lum[m])); q = rank / max(len(rank) - 1, 1)
    idx = np.clip((q * (len(order) - 1)).astype(int), 0, len(order) - 1)
    tgt = np.clip(src[order[idx]] * gain, 0, 1)
    # keep a share of our own fine luminance detail (the MM9 skin is 256 px)
    det = np.clip(lum[m] / np.maximum(ndimage.gaussian_filter(lum * m, 2)[m] / np.maximum(ndimage.gaussian_filter(m.astype(float), 2)[m], 1e-3), 1e-4), 0.7, 1.3)
    tgt = tgt * det[:, None] ** 0.6
    w = ndimage.gaussian_filter(m.astype(float), 0.7) * STRENGTH
    o = out.copy(); o[m] = tgt
    out = out * (1 - w[..., None]) + o * w[..., None]
    rep[name] = {'texels': int(m.sum()), 'median_before': np.round(np.median(img[m], 0) * 255).astype(int).tolist()}
s = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
Image.fromarray(np.uint8(np.clip(s, 0, 1) * 255 + 0.5)).save(T)
for name, m in (('boots', boots), ('belt', belt)):
    rep[name]['median_after'] = np.round(np.median(s[m], 0) * 255).astype(int).tolist()
print('PAINTMATCH', rep)
