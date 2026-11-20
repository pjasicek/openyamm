#!/usr/bin/env python3
"""Werewolf maps from the 4K Meshy body paint on the uv_atlas layout (texture quality pass recipe; after
mm8_lizardman_peasant_rebuild_claude/scripts/compose_liz.py): colour 4K -> 2K once, gentle grade with AO, normal and
roughness 1K. Classes by colour: shorts (rust orange/brown cloth: the tier region R), gem (turquoise: tier region G),
gold (chain and pendant ring), ivory (claws, teeth), eyes (yellow, small), fur (the rest). Region mask R shorts, G gem;
MR red = per-class specular mask, G roughness, B 0. Writes textures/wwf_{basecolor,normal,metal_rough,region_mask}.png."""
import subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy/retex_body_v1'; S = 2048
Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((S, S), Image.Resampling.LANCZOS).save(T / 'wwf_raw.png')
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared/grade_basecolor.py'), '--ao', str(HERE / 'work/ao_v1.png'),
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                str(T / 'wwf_raw.png')], check=True)
base = np.asarray(Image.open(T / 'wwf_raw_graded.png').convert('RGB')).astype(np.float64) / 255
R = np.load(HERE / 'work/raster_v1.npz'); cov = R['cov']; pos = R['pos']
r, g, b = base.transpose(2, 0, 1); mx = base.max(-1); mn = base.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
# shorts: waist to knee (rest height), warm brown/orange; gem: cyan on the chest; gold: yellow-orange saturated
inshorts = (pos[..., 1] < 0.16) & (pos[..., 1] > -0.40)
shorts = inshorts & ((hue < 45) | (hue > 340)) & (sat > 0.25) & (mx > 0.12)
gem = (hue > 150) & (hue < 210) & (sat > 0.3) & (pos[..., 1] > 0.25)
gold = (hue >= 30) & (hue < 65) & (sat > 0.45) & (pos[..., 1] > 0.25)
ivory = (sat < 0.25) & (mx > 0.6)
cls = np.zeros(base.shape[:2], np.uint8)
for k, m in ((1, shorts), (2, gem), (3, gold), (4, ivory)):
    cls[m & cov] = k
cls = np.where(cov, ndimage.median_filter(cls, 3), cls)
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
soft = lambda m: ndimage.gaussian_filter(m.astype(float)[idx[0], idx[1]], 0.7)
sw, gw = soft(cls == 1), soft(cls == 2)
mask = np.zeros((S, S, 4), np.uint8); mask[..., 0] = np.uint8(np.clip(sw * 255 + .5, 0, 255)); mask[..., 1] = np.uint8(np.clip(gw * 255 + .5, 0, 255)); mask[..., 3] = 255
Image.fromarray(mask, 'RGBA').resize((1024, 1024), Image.BOX).save(T / 'wwf_region_mask.png')
np.save(HERE / 'work/region_weights.npy', np.stack([sw, gw]).astype(np.float16))
spec = np.choose(cls, [0.35, 0.12, 0.8, 0.9, 0.55])
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.Resampling.LANCZOS)).astype(np.float64) / 255
Image.fromarray(np.uint8(np.clip(np.stack([spec, rough, np.zeros_like(rough)], -1) * 255 + .5, 0, 255))).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'wwf_metal_rough.png')
Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'wwf_normal.png')
Image.fromarray(np.uint8(np.clip(base * 255 + .5, 0, 255))).save(T / 'wwf_basecolor.png')
pal = np.array([[60, 60, 60], [200, 110, 50], [40, 200, 200], [240, 200, 40], [245, 245, 230]], np.uint8)
Image.fromarray(np.where(cov[..., None], pal[cls], 0).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(T / 'wwf_classes.png')
print('COMPOSE', {['fur', 'shorts', 'gem', 'gold', 'ivory'][k]: int(((cls == k) & cov).sum()) for k in range(5)})
