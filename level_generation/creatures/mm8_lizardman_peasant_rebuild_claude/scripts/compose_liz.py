#!/usr/bin/env python3
"""Lizardman peasant maps from the 4K Meshy body paint on the uv_atlas layout (texture quality pass recipe):
colour 4K -> 2K once (Lanczos), gentle grade (grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5
--contrast 1.06 --saturation 1.15, AO baked on the layout), normal and roughness to 1K.
Classes by colour on the graded paint (and the rest position for the arm bands): garment (green tunic and skirt),
trim (orange collar, belt, hem and apron checks: the regions the native palettes 401/402/403 change), gold (arm bands),
ivory (claws, teeth, fringe), membrane (tan fins), skin (teal scales). Region mask R garment, G trim (padded into
the gutters, blurred 0.7 px). Metal/rough: R per-class specular mask (openyamm_specular_mask), G roughness, B 0.
Writes textures/liz_{basecolor,normal,metal_rough,region_mask}.png and textures/liz_classes.png (preview)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]; T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy/retex_body_v1'; S = 2048
raw = Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((S, S), Image.Resampling.LANCZOS)
raw.save(T / 'liz_raw.png')
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared/grade_basecolor.py'), '--ao', str(HERE / 'work/ao_v1.png'),
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                str(T / 'liz_raw.png')], check=True)
base = np.asarray(Image.open(T / 'liz_raw_graded.png').convert('RGB')).astype(np.float64) / 255
R = np.load(HERE / 'work/raster_v1.npz'); cov = R['cov']; pos = R['pos']
r, g, b = base.transpose(2, 0, 1); mx = base.max(-1); mn = base.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
green = (hue > 85) & (hue < 160) & (sat > 0.25)
warm = (hue < 50) | (hue > 340)
orange = warm & (sat > 0.45) & (hue < 38)
gold = warm & (sat > 0.4) & (hue >= 38) & (hue < 60)
ivory = (sat < 0.30) & (mx > 0.55) & ~green
teal = (hue >= 160) & (hue < 260)
# arm bands: gold-coloured texels on the upper arms (rest position) are gold, never trim
# rest positions (glTF, fitted bind): the upper-arm bands sit at |x| >= 0.19, 0.2 < y < 0.5 -> all warm texels there
# are gold (native: the arm bands keep their colour in every tier); gold-looking texels at the collar are trim
uparm = (np.abs(pos[..., 0]) >= 0.19) & (pos[..., 1] > 0.2) & (pos[..., 1] < 0.5)
gold = (gold | (orange & uparm)) & uparm | (gold & ~uparm & (pos[..., 1] < 0.4))
orange = (orange & ~uparm) | (warm & (sat > 0.4) & (hue < 60) & ~uparm & (pos[..., 1] >= 0.4))
membrane = warm & (sat < 0.45) & (sat >= 0.15) & (pos[..., 1] > 0.55)
cls = np.zeros(base.shape[:2], np.uint8)                 # 0 skin/other
for k, m in ((1, green), (2, orange), (3, gold), (4, ivory), (5, membrane)):
    cls[m & cov] = k
# clean specks: majority filter per class inside the islands
cls_s = ndimage.median_filter(cls, 3)
cls = np.where(cov, cls_s, cls)
garment = (cls == 1); trim = (cls == 2)
idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
def soft(m):
    return ndimage.gaussian_filter(m.astype(float)[idx[0], idx[1]], 0.7)
gw, tw = soft(garment), soft(trim)
mask = np.zeros((S, S, 4), np.uint8); mask[..., 0] = np.uint8(np.clip(gw * 255 + 0.5, 0, 255)); mask[..., 1] = np.uint8(np.clip(tw * 255 + 0.5, 0, 255)); mask[..., 3] = 255
Image.fromarray(mask, 'RGBA').resize((1024, 1024), Image.BOX).save(T / 'liz_region_mask.png')
np.save(HERE / 'work/region_weights.npy', np.stack([gw, tw]).astype(np.float16))
spec = np.choose(cls, [0.55, 0.12, 0.18, 0.9, 0.5, 0.3])
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.Resampling.LANCZOS)).astype(np.float64) / 255
mr = np.stack([spec, rough, np.zeros_like(rough)], -1)
Image.fromarray(np.uint8(np.clip(mr * 255 + 0.5, 0, 255))).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'liz_metal_rough.png')
nrm = Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.Resampling.LANCZOS)
nrm.save(T / 'liz_normal.png')
Image.fromarray(np.uint8(np.clip(base * 255 + 0.5, 0, 255))).save(T / 'liz_basecolor.png')
pal = np.array([[0, 110, 130], [40, 170, 60], [230, 120, 20], [240, 210, 40], [245, 245, 230], [180, 140, 100]], np.uint8)
prev = np.where(cov[..., None], pal[cls], 0).astype(np.uint8)
Image.fromarray(prev).resize((1024, 1024), Image.NEAREST).save(T / 'liz_classes.png')
print('COMPOSE', {['skin', 'garment', 'trim', 'gold', 'ivory', 'membrane'][k]: int(((cls == k) & cov).sum()) for k in range(6)})
