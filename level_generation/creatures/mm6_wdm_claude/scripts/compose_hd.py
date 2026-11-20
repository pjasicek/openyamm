#!/usr/bin/env python3
"""Body textures for the HD model: the base colour baked from Meshy's 20k body (bake_reduced.py; Meshy painted it
from the Codex HD references) is kept. Skin region = purple skin texels (hue/saturation) outside the wing membrane.
Writes textures/wdm_basecolor.png, wdm_region_mask.png (1K RGBA, skin in R, G/B/A unused), wdm_normal_1k.png,
wdm_metal_rough_1k.png (R 255, G roughness, B metallic 0), wdm_skin_source.json (masked linear luminance, used by
compose_head.py) and review/texture_classes.png. Tier colours come from compose_ramps.py."""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
T = ROOT / 'textures'
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


data = np.load(ROOT / 'work/uv3d.npz')
part_map, _ = C.rasterise(data)
base = C.load(str(T / 'body_base_color.png'))
if part_map.shape != base.shape[:2]:
    raise ValueError('uv3d raster size must match the base colour texture')
h, s, v = C.hsv(base)
valid = part_map >= 0
skin = valid & (part_map != 1) & ((h > 255) | (h < 20)) & (s > 0.15) & (v > 0.08)
shutil.copy(T / 'body_base_color.png', T / 'wdm_basecolor.png')
L = lin(base)
src_lum = float((L[skin] @ W).mean())
json.dump({'mask_texels': int(skin.sum()), 'source_linear_luminance': round(src_lum, 4)},
          open(T / 'wdm_skin_source.json', 'w'), indent=1)
mask = Image.fromarray((skin * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
mask = np.asarray(mask.resize((1024, 1024), Image.LANCZOS))
zero = np.zeros_like(mask)
Image.fromarray(np.stack([mask, zero, zero, zero], 2), 'RGBA').save(T / 'wdm_region_mask.png')
rough = np.asarray(Image.open(T / 'body_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS))
Image.fromarray(np.stack([np.full_like(rough, 255), rough, np.zeros_like(rough)], 2)).save(T / 'wdm_metal_rough_1k.png')
Image.open(T / 'body_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'wdm_normal_1k.png')
preview = np.zeros(base.shape, np.float32); preview[valid] = (0.25, 0.25, 0.25); preview[skin] = (0.7, 0.3, 0.7)
preview[valid & (part_map == 1)] = (0.2, 0.5, 0.8)
(ROOT / 'review').mkdir(exist_ok=True)
Image.fromarray((preview * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'texture_classes.png')
print('COMPOSED skin texels', int(skin.sum()), 'source luminance', round(src_lum, 4))
