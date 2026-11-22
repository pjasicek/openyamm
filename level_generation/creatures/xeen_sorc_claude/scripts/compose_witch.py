#!/usr/bin/env python3
"""Witch body texture set from meshy/retexture_v1 (4K on the uv_atlas layout): 2K colour (downsampled once, Lanczos),
1K normal, ORM 1K (R baked AO, G roughness clamped 0.45-0.95, B 0), region mask R = the robe (red hue within 22 deg
of 0, saturation >= 0.45, value >= 0.12: the coat-robe, its tatters and the right wrist wrap; the gold mask, pale skin,
white mane, black panel, brown cord and boots, blue beads and gems stay out), padded into the gutters by the final
gutter_fill.py step; material classes (texture doc labels: 8 cloth for the robe and panel, 2 hair for the mane, 9 metal
for the gold mask, 1 skin, 11 other) from the texel's garment (work/uv_garment_2k.png, uv_raster) and hue.
Grading and the gutter fill follow in build_runtime.sh."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
base = Image.open(f'{SRC}_base_color.png').convert('RGB')
print('COMPOSE Meshy colour', base.size)
base = base.resize((2048, 2048), Image.LANCZOS)
base.save(OUT / 'witch_basecolor.png')
Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'witch_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
ao = np.asarray(Image.open(OUT / 'witch_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)) / 255.0
orm = np.stack([ao, np.clip(rough, 0.45, 0.95), np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).save(OUT / 'witch_mr_1k.png')
rgb = np.asarray(base, np.float64) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); c = mx - mn
sat = np.where(mx > 1e-4, c / np.maximum(mx, 1e-4), 0)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
gar = np.asarray(Image.open(ROOT / 'work/uv_garment_2k.png').convert('L'), np.int32)       # 255 = no face (gutter)
robe = ((hue < 22) | (hue > 338)) & (sat >= 0.45) & (mx >= 0.12) & np.isin(gar, (0, 7))
robe = ndimage.binary_opening(robe, iterations=1)
robe = ndimage.binary_closing(robe, iterations=2) & (gar != 255)
w = ndimage.gaussian_filter(robe.astype(np.float32), 1.0)
mask = Image.fromarray((w * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
Image.merge('RGBA', [mask] + [Image.new('L', (1024, 1024), 0)] * 3).save(OUT / 'witch_region_mask.png')
gold = (hue > 30) & (hue < 65) & (sat > 0.35) & (mx > 0.35)
cls = np.full(gar.shape, 11, np.uint8)
cls[gar == 0] = 1
cls[robe] = 8
cls[gar == 3] = 8
cls[gar == 1] = 2
cls[(gar == 2) | ((gar == 0) & gold)] = 9
cls[gar == 6] = 4
cls[gar == 255] = 0
Image.fromarray(cls, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'witch_material_classes.png')
print('COMPOSED robe share of the islands', round(float(robe.sum() / max((gar != 255).sum(), 1)), 3))
