#!/usr/bin/env python3
"""Head textures (meshy/head_v1): base colour kept, skin brought to the body's skin luminance so both materials take
the same ramps alike. Skin region = magenta skin hues (330-350 deg) fading out over 348-358 deg, so the red mouth
interior, gums and tongue keep their colour; horns/teeth (ivory, ~35 deg), eyes (cyan) and the grey chin are left out.
Writes textures/wdm_head_basecolor.png (1K; runtime memory), wdm_head_region_mask.png (1K RGBA, skin in R),
wdm_head_normal_1k.png, wdm_head_metal_rough_1k.png (R 255, G roughness, B 0) and review/head_texture_classes.png.
Run after compose_hd.py (reads wdm_skin_source.json)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
T = ROOT / 'textures'; SRC = ROOT / 'meshy' / 'head_v1'
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)

base = C.load(str(SRC / 'texture_urls_0_base_color.png'))
h, s, v = C.hsv(base)
hue_w = np.clip((358.0 - h) / 10.0, 0, 1) * (h > 315)
skin = hue_w * (s > 0.2) * (v > 0.08)
L = lin(base)
body_lum = json.load(open(T / 'wdm_skin_source.json'))['source_linear_luminance']
core = skin > 0.99
head_lum = float((L[core] @ W).mean())
gain = body_lum / head_lum
L = L * (1 + (gain - 1) * skin[..., None])
Image.fromarray((np.clip(srgb(L), 0, 1) * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    T / 'wdm_head_basecolor.png')
mask = Image.fromarray((skin * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)).resize((1024, 1024), Image.LANCZOS)
rough = Image.open(SRC / 'texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)
zero = Image.new('L', (1024, 1024), 0)
Image.merge('RGBA', (mask, zero, zero, zero)).save(T / 'wdm_head_region_mask.png')
Image.merge('RGB', (Image.new('L', (1024, 1024), 255), rough, zero)).save(T / 'wdm_head_metal_rough_1k.png')
Image.open(SRC / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'wdm_head_normal_1k.png')
prev = np.zeros(base.shape); prev[..., :] = base * 0.35; prev[skin > 0.5] = (0.7, 0.3, 0.7)
Image.fromarray((prev * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'head_texture_classes.png')
print(f'HEAD skin texels {int(core.sum())} head lum {head_lum:.4f} body lum {body_lum:.4f} gain {gain:.3f}')
