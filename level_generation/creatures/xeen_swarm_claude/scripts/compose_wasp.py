#!/usr/bin/env python3
"""Stinger texture set from meshy/wasp_retexture_v1 (4K on the uv_atlas layout): 2K colour (downsampled once),
1K normal, ORM (R AO, G roughness, B 0), region mask R = the orange-brown hairy body (hue 8-50 deg, saturation >=
0.35), legs, eyes, stinger and wings outside it; material classes (2 hair, 4 legs/claws/stinger, 6 eyes, 3 wings by the
wing triangles). Grading and the gutter fill follow in build_runtime.sh."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/wasp_retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
base = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS)
base.save(OUT / 'wasp_basecolor.png')
Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'wasp_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
ao = np.asarray(Image.open(OUT / 'wasp_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
orm = np.stack([ao, np.clip(rough, 0.45, 0.95), np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(OUT / 'wasp_mr_1k.png')
rgb = np.asarray(base, np.float64) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); c = mx - mn
sat = np.where(mx > 1e-4, c / np.maximum(mx, 1e-4), 0)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
hair = (hue > 8) & (hue < 50) & (sat > 0.35) & (mx > 0.18)
hair = ndimage.binary_opening(hair, iterations=1)
w = ndimage.gaussian_filter(hair.astype(np.float32), 1.2)
chans = [Image.fromarray((w * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)] + \
        [Image.new('L', (1024, 1024), 0)] * 3
Image.merge('RGBA', chans).save(OUT / 'wasp_region_mask.png')
cls = np.where(hair, 2, np.where(mx < 0.2, 4, 3)).astype(np.uint8)
Image.fromarray(cls, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'wasp_material_classes.png')
print('COMPOSED hair share', round(float(hair.mean()), 3))
