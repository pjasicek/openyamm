#!/usr/bin/env python3
"""Guardian texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade and gutter fill follow in
scripts/build_runtime.sh.

Writes into textures/:
  guardian_basecolor.png         2K base colour (4K Meshy paint downsampled once, Lanczos). Parts 0-4 (cranium, jaw,
                                 teeth, bezel) keep the paint, with any red or green that the masters' gem and eye
                                 glints projected onto them turned to its own grey; the gem (part 5) and the eye cores
                                 (parts 6, 7) are painted procedurally: a ruby whose facets shade by their normal, and
                                 an emerald core with a light green centre facing forward.
  guardian_normal_1k.png         Meshy normal (+y down; tools/prepare_actor_glb.py converts it); flat on gem and eyes
  guardian_mr_1k.png             ORM: R baked AO, G roughness (Meshy, chrome 0.28-0.55; gem 0.12, eyes 0.2), B 0
  guardian_region_mask.png       1K RGBA: R skull (parts 0-4), G gem, B eyes; padded into the gutters
  guardian_emission_rgb.png      1K RGB emission colour mask: the ruby red on the gem, green on the eye cores
  guardian_material_classes.png  1K labels: 9 metal (skull, teeth, bezel), 11 other (gem), 6 eye"""
import sys, colorsys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 part/xyz maps)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
data = np.load(ROOT / 'work/uv3d.npz')
tri_map, xyz = C.rasterise(data, values=np.arange(len(data['part'])))
valid = tri_map >= 0
part = np.where(valid, data['part'][np.maximum(tri_map, 0)], -1)
nrm = data['normal'][np.maximum(tri_map, 0)]
import json
info = json.load(open(ROOT / 'work/gem_info.json'))


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


base = np.asarray(Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
# --- skull parts: red/green specks projected from the gem and the eye glints -> their own grey
mx, mn = base.max(-1), base.min(-1)
sat = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
r, g, b = base[..., 0], base[..., 1], base[..., 2]
hued = (sat > 0.25) & (((r > g * 1.25) & (r > b * 1.25)) | ((g > r * 1.25) & (g > b * 1.1)))
skull = valid & (part <= 4)
fix = ndimage.binary_dilation(hued & skull, iterations=2) & skull
lum = (base @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
grey_fix = np.repeat(lum, 3, -1)
base = np.where(fix[..., None], grey_fix, base)
print('SKULL texels re-greyed', int(fix.sum()), 'of', int(skull.sum()))
# chrome brightness: the Meshy paint's median (105 of 255) is darker than the sprite's polished silver; sprites carry
# baked shading, so the albedo goes to about 1.45x the native grey median (92 -> ~135): gain 1.3 on the skull parts
SKULL_GAIN = 1.3
base = np.where(skull[..., None], np.clip(base * SKULL_GAIN, 0, 0.95), base)
# --- gem: deep ruby, each facet lit by its normal (light from above the camera), table brightest
gem = part == 5
gc = np.array(info['gem_centre']); ga = np.array(info['gem_axis'])
light = np.array([0.25, -0.75, 0.6]); light /= np.linalg.norm(light)
facing = np.clip(nrm @ light, 0, 1)
axial = np.clip(nrm @ ga, -1, 1)
dark = np.array([0.30, 0.01, 0.02]); mid = np.array([0.70, 0.04, 0.05]); hi = np.array([1.0, 0.42, 0.32])
k = (0.35 + 0.65 * facing)[..., None]
gemcol = dark + (mid - dark) * np.clip(k * 1.4, 0, 1)
gemcol = gemcol + (hi - gemcol) * (np.clip((facing - 0.82) / 0.18, 0, 1) * 0.8)[..., None]
gemcol = np.where((axial > 0.97)[..., None], gemcol * 0.9 + hi * 0.1, gemcol)
base = np.where(gem[..., None], gemcol, base)
# --- eyes: emerald core, light green centre toward the front (-Y)
eyes = (part == 6) | (part == 7)
ec = np.where((xyz[..., 0] > 0)[..., None], np.array(info['eye_left']), np.array(info['eye_right']))
d = xyz - ec; d /= np.maximum(np.linalg.norm(d, axis=-1, keepdims=True), 1e-6)
front = np.clip(-d[..., 1], 0, 1)
edge = np.array([0.02, 0.32, 0.06]); core = np.array([0.55, 1.0, 0.45])
eyecol = edge + (core - edge) * (np.clip((front - 0.35) / 0.65, 0, 1) ** 1.5)[..., None]
base = np.where(eyes[..., None], eyecol, base)
save(base, OUT / 'guardian_basecolor.png')

# --- normal: Meshy's, flat (128,128,255 in its +y-down convention is still flat) on gem and eyes
normal = np.asarray(Image.open(f'{SRC}_normal.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
normal = np.where((gem | eyes)[..., None], np.array([0.5, 0.5, 1.0], np.float32), normal)
save(normal, OUT / 'guardian_normal_1k.png', 1024)
# --- ORM
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS), np.float32) / 255
ao = np.asarray(Image.open(OUT / 'guardian_ao_2k.png').convert('L'), np.float32) / 255
print('ROUGHNESS skull p10/p50/p90', np.round(np.percentile(rough[skull], [10, 50, 90]), 3).tolist())
rough = np.clip(rough, 0.28, 0.55)
rough = np.where(gem, 0.12, np.where(eyes, 0.2, rough))
ao = np.where(gem | eyes, 1.0, ao)
save(np.stack([ao, rough, np.zeros_like(ao)], -1), OUT / 'guardian_mr_1k.png', 1024)

# --- region mask: R skull, G gem, B eyes; padded into the gutters (nearest island texel)
chan = np.zeros((N, N, 4), np.float32)
chan[..., 0] = skull; chan[..., 1] = gem; chan[..., 2] = eyes
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
padded = chan[iy, ix]
padded[valid] = chan[valid]
for c in range(3):
    padded[..., c] = np.where(valid, ndimage.gaussian_filter(padded[..., c], 0.7), padded[..., c])
chans = [Image.fromarray((padded[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'guardian_region_mask.png')

# --- emission colour mask (sRGB): ruby on the gem (brighter on lit facets), green on the eye cores (core brightest)
emis = np.zeros((N, N, 3), np.float32)
emis = np.where(gem[..., None], np.array([0.85, 0.06, 0.04]) * (0.55 + 0.45 * facing)[..., None], emis)
emis = np.where(eyes[..., None], np.array([0.25, 1.0, 0.25]) * (0.45 + 0.55 * front)[..., None], emis)
emis_p = emis[iy, ix]; emis_p[valid] = emis[valid]
save(emis_p, OUT / 'guardian_emission_rgb.png', 1024)

classes = np.zeros((N, N), np.uint8)
classes[skull] = 9; classes[gem] = 11; classes[eyes] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'guardian_material_classes.png')
np.save(ROOT / 'work/part_map_2k.npy', part.astype(np.int8))
print('COMPOSED skull', int(skull.sum()), 'gem', int(gem.sum()), 'eyes', int(eyes.sum()))
