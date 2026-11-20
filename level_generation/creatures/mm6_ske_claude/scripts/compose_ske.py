#!/usr/bin/env python3
"""Texture sets, region masks, material classes and A/B/C ramps for the MM6 skeleton (CLAUDE_CREATURE_TEXTURES.md).

Body (material Bone -> runtime Skeleton_A): Meshy retexture_v1 2K -> 1K, multiplied by the baked AO (work/ao_body.png,
strength AO_K); ORM (R AO, G Meshy roughness, B 0). Sword colour swatches are painted into free atlas texels
(native skesta2 sword: copper blade, lighter edge, brass guard and pommel, dark leather grip) and listed in
textures/ske_sword_swatches.json (u, v, radius) for export_runtime.py.
Head (material Head -> SkeletonHead_A): head_retexture_v1 2K -> 1K with work/ao_head.png. The eyes are a separate
red swatch in the head set (excluded from the tier mask).
Tiers: one region (all bone, body and head, teeth included) with ramps from the native bone pixels of the standing
views skesta0..4 in palettes 816 (A, ivory), 817 (B, yellow), 818 (C, dark red); bone pixels are the tier A pixels
with saturation < 0.3 (sword copper and red eyes excluded), the same pixel set in every palette. Each ramp is the
pixels' linear colours sorted by luminance at 16 quantiles times ALBEDO_GAIN (sprites carry baked shading); the
luminance range is the 2nd-98th percentile of the bone texels of both texture sets, so head and body share one ramp
(merge_head_material.py requires it)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as R

T = HERE / 'textures'; T.mkdir(exist_ok=True)
NAT = HERE.parent / 'mm6_ske' / 'native_variants'
N = 1024
AO_K = 0.8
ALBEDO_GAIN = 0.95
PALS = {'ske_a': 816, 'ske_b': 817, 'ske_c': 818}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def load(path, size=N, mode='RGB'):
    im = Image.open(path).convert(mode)
    return im.resize((size, size), Image.LANCZOS) if im.size != (size, size) else im


def save(arr, path):
    Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def coverage(polys, dilate):
    img = Image.new('L', (N, N), 0); d = ImageDraw.Draw(img)
    for pts in polys:
        d.polygon([(u * N, (1 - v) * N) for u, v in pts], fill=255, outline=255)
    m = np.asarray(img) > 0
    return ndimage.binary_dilation(m, iterations=dilate) if dilate else m


layout = json.loads((HERE / 'work' / 'uv_layout.json').read_text())
body_cov = coverage(layout['Bone'], 0)
head_cov = coverage(layout['Head'], 0)

# ---------------------------------------------------------------- body set
M = HERE / 'meshy' / 'retexture_v1'
base = np.asarray(load(M / 'texture_urls_0_base_color.png'), np.float64) / 255
ao = np.asarray(load(HERE / 'work' / 'ao_body.png', mode='L'), np.float64) / 255
base *= (1 - AO_K * (1 - ao))[..., None]
rough = np.asarray(load(M / 'texture_urls_0_roughness.png', mode='L'), np.float64) / 255
normal = np.asarray(load(M / 'texture_urls_0_normal.png'), np.float64) / 255

# sword swatches in free texels (6 px clear of any island)
occ = ndimage.binary_dilation(body_cov, iterations=6)
SW = {'blade': (132, 88, 56), 'edge': (182, 132, 92), 'brass': (176, 140, 64), 'grip': (64, 40, 26)}
swatches, r_px = {}, 5
y, x = N - 10, N - 10
for name, rgb in SW.items():
    while occ[y - r_px:y + r_px, x - r_px:x + r_px].any():
        x -= 4
        if x < 12:
            x, y = N - 10, y - 4
    base[y - r_px:y + r_px, x - r_px:x + r_px] = np.array(rgb) / 255
    rough[y - r_px:y + r_px, x - r_px:x + r_px] = 0.55 if name in ('blade', 'edge', 'brass') else 0.8
    normal[y - r_px:y + r_px, x - r_px:x + r_px] = (0.5, 0.5, 1.0)
    occ[y - r_px - 3:y + r_px + 3, x - r_px - 3:x + r_px + 3] = True
    swatches[name] = [(x + 0.5) / N, 1 - (y + 0.5) / N, (r_px - 2) / N]
(T / 'ske_sword_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')
save(base, T / 'ske_basecolor_1k.png')
save(normal, T / 'ske_normal_1k.png')
save(np.stack([ao, rough, np.zeros_like(ao)], -1), T / 'ske_metal_rough_1k.png')

# ---------------------------------------------------------------- head set
H = HERE / 'meshy' / 'head_retexture_v1'
hbase = np.asarray(load(H / 'texture_urls_0_base_color.png'), np.float64) / 255
hao = np.asarray(load(HERE / 'work' / 'ao_head.png', mode='L'), np.float64) / 255
hbase *= (1 - AO_K * (1 - hao))[..., None]
hrough = np.asarray(load(H / 'texture_urls_0_roughness.png', mode='L'), np.float64) / 255
hnormal = np.asarray(load(H / 'texture_urls_0_normal.png'), np.float64) / 255
# eye swatch (native: a bright red point in each socket) in free head texels; the eye spheres map into it
hocc = ndimage.binary_dilation(head_cov, iterations=6)
y, x = N - 10, N - 10
while hocc[y - r_px:y + r_px, x - r_px:x + r_px].any():
    x -= 4
    if x < 12:
        x, y = N - 10, y - 4
hbase[y - r_px:y + r_px, x - r_px:x + r_px] = np.array((255, 40, 20)) / 255
hrough[y - r_px:y + r_px, x - r_px:x + r_px] = 0.3
hnormal[y - r_px:y + r_px, x - r_px:x + r_px] = (0.5, 0.5, 1.0)
swatches['eyes'] = [(x + 0.5) / N, 1 - (y + 0.5) / N, (r_px - 2) / N]
(T / 'ske_sword_swatches.json').write_text(json.dumps(swatches, indent=1) + '\n')
save(hbase, T / 'ske_head_basecolor_1k.png')
save(hnormal, T / 'ske_head_normal_1k.png')
save(np.stack([hao, hrough, np.zeros_like(hao)], -1), T / 'ske_head_metal_rough_1k.png')

# ---------------------------------------------------------------- masks and classes
bw = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(body_cov, iterations=2).astype(float), 0.7), 0, 1)
for name, (u, v, r) in swatches.items():
    if name == 'eyes':
        continue
    cx, cy = int(u * N), int((1 - v) * N)
    bw[cy - 8:cy + 8, cx - 8:cx + 8] = 0
hw = np.clip(ndimage.gaussian_filter(ndimage.binary_dilation(head_cov, iterations=2).astype(float), 0.7), 0, 1)
ex, ey = int(swatches['eyes'][0] * N), int((1 - swatches['eyes'][1]) * N)
hw[ey - 8:ey + 8, ex - 8:ex + 8] = 0
R.write_mask([bw], T / 'ske_region_mask.png', size=N)
R.write_mask([hw], T / 'ske_head_region_mask.png', size=N)
cls = np.where(body_cov, 5, 0).astype(np.uint8)
for name, (u, v, r) in swatches.items():
    if name == 'eyes':
        continue
    cx, cy = int(u * N), int((1 - v) * N)
    cls[cy - r_px:cy + r_px, cx - r_px:cx + r_px] = 8 if name == 'grip' else 9
Image.fromarray(cls).save(T / 'ske_material_classes.png')
hcls = np.where(head_cov, 5, 0).astype(np.uint8); hcls[ey - r_px:ey + r_px, ex - r_px:ex + r_px] = 6
Image.fromarray(hcls).save(T / 'ske_head_material_classes.png')

# ---------------------------------------------------------------- ramps from native bone pixels
cols = {k: [] for k in PALS}
for i in range(5):
    ims = {k: np.asarray(Image.open(NAT / f'skesta{i}_{p}.png').convert('RGBA'), np.float64) / 255 for k, p in PALS.items()}
    a = ims['ske_a']; rgb = a[..., :3]; mx = rgb.max(-1); mn = rgb.min(-1)
    bone = (a[..., 3] > 0.5) & ((mx - mn) / np.maximum(mx, 1e-6) < 0.3) & (mx > 0.08)
    for k in PALS:
        cols[k].append(ims[k][..., :3][bone])
lin_a = R.srgb_to_linear(np.concatenate(cols['ske_a']))
order = np.argsort(lin_a @ LUMA)
qs = np.linspace(0.03, 0.97, 16)
bone_lum = np.concatenate([R.luminance(base)[bw > 0.9], R.luminance(hbase)[hw > 0.9]])
lo, hi = np.percentile(bone_lum, [2, 98])
ramps = {}
for k in PALS:
    lin = R.srgb_to_linear(np.concatenate(cols[k]))[order]          # same pixels, ordered by tier A luminance
    stops = []
    for q in qs:
        c = int(q * (len(lin) - 1)); w = max(4, len(lin) // 40)
        stops.append(np.clip(np.median(lin[max(0, c - w):c + w], 0) * ALBEDO_GAIN, 0, 1))
    ramps[k] = [{'range': [round(float(lo), 6), round(float(hi), 6)], 'colors': [[round(float(x), 6) for x in s] for s in stops]}]
report = {'bone_pixels': int(len(lin_a)), 'range': [float(lo), float(hi)], 'albedo_gain': ALBEDO_GAIN, 'ao_k': AO_K}
cfg = {'variants': list(PALS),
       'materials': [{'base': 'Skeleton_A', 'prefix': 'Skeleton', 'mask': 'ske_region_mask.png', 'regions': ['bone'],
                      'palettes': PALS, 'ramps': ramps, 'report': report},
                     {'base': 'SkeletonHead_A', 'prefix': 'SkeletonHead', 'mask': 'ske_head_region_mask.png',
                      'regions': ['bone'], 'palettes': PALS, 'ramps': ramps}]}
(T / 'ske_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('COMPOSED swatches', {k: [round(x, 4) for x in v] for k, v in swatches.items()}, 'range', np.round([lo, hi], 4),
      'A mid', np.round(np.array(ramps['ske_a'][0]['colors'][8]) ** (1 / 2.2) * 255))
