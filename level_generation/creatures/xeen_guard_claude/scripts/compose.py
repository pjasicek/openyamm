#!/usr/bin/env python3
"""Guard texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the four
Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade and gutter fill follow in
scripts/build_runtime.sh.

Classes per texel (paint hue limited by plate part, work/uv3d.npz):
  red     the dome's seam and side stripes, the forearm band, the boots' stripes (saturated red)
  cyan    the hip tubes (part 6 wholly) and the waist ring (saturated cyan)
  green   the chest rivets and palm dots: keep their paint, in no region
  black   boots, briefs, waist band, knee rings, soles (part 7): dark, unsaturated
  chrome  every other texel of the shell, the hands and the dome
  joint   the hidden joint spheres (part 2) and cut caps (part 3): Meshy painted them white where its views saw
          through the gaps; they are dark gunmetal (the paint's luminance detail at a quarter, plus 0.05), region black
  gem     part 1: a procedural ruby lit by its normal (as the Guardian's), region red
Writes into textures/:
  guard_basecolor.png         2K base colour (4K paint downsampled once, Lanczos), chrome x CHROME_GAIN
  guard_normal_1k.png         Meshy normal; flat on the gem and the joints
  guard_mr_1k.png             ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  guard_region_mask.png       1K RGBA: R chrome, G red, B cyan, A black; padded into the gutters
  guard_emission_mask.png     1K grey: the gem (brighter on lit facets); claude_shared/emission.py colours it red
  guard_material_classes.png  1K labels: 9 metal (chrome), 11 gem/red, 10 rubber-black, 12 cyan, 6 green dots"""
import sys, json
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
CHROME_GAIN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
data = np.load(ROOT / 'work/uv3d.npz')
tri_map, xyz = C.rasterise(data, values=np.arange(len(data['part'])))
valid = tri_map >= 0
part = np.where(valid, data['part'][np.maximum(tri_map, 0)], -1)
nrm = data['normal'][np.maximum(tri_map, 0)]


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.LANCZOS)
    image.save(path, optimize=True)


base = np.asarray(Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
r, g, b = base[..., 0], base[..., 1], base[..., 2]
mx, mn = base.max(-1), base.min(-1)
sat = np.where(mx > 1e-3, (mx - mn) / np.maximum(mx, 1e-3), 0)
lum = base @ np.array([0.299, 0.587, 0.114], np.float32)
shell = valid & np.isin(part, (0, 4, 5, 6, 7))
red = shell & (sat > 0.35) & (r > 1.5 * g) & (r > 1.5 * b) & (mx > 0.22)
cyan = shell & (sat > 0.3) & (b > 1.3 * r) & (g > 1.2 * r) & (mx > 0.25)
green = shell & (sat > 0.3) & (g > 1.25 * r) & (g > 1.1 * b) & ~cyan
cyan |= valid & (part == 6)
# soft edges of the coloured strokes: one texel ring of the class around it, if it is not dark/grey chrome
red = ndimage.binary_closing(red, iterations=1) & shell & ~cyan
black = shell & ~red & ~cyan & ~green & (mx < 0.2) & (sat < 0.4)
black = ndimage.binary_opening(black, iterations=1) | (valid & (part == 7))
black = ndimage.binary_closing(black, iterations=1) & shell & ~red & ~cyan & ~green
joint = valid & np.isin(part, (2, 3))
# the knee rings' upper rim (calf plates above z 0.655 at rest) came out as a white smear: dark ribbed metal there,
# like the rest of the ring
bones = json.load(open(ROOT / 'work/seg_info.json'))['bones']
bone = np.where(valid, data['bone'][np.maximum(tri_map, 0)], -1)
calf = np.isin(bone, [bones.index('B_L_Calf'), bones.index('B_R_Calf')])
rim = valid & calf & (part == 0) & (xyz[..., 2] > 0.655)
print('KNEE RIM texels', int(rim.sum()))
gem = valid & (part == 1)
black = black | rim
chrome = shell & ~red & ~cyan & ~green & ~black
print('CLASSES texels chrome', int(chrome.sum()), 'red', int(red.sum()), 'cyan', int(cyan.sum()), 'green',
      int(green.sum()), 'black', int(black.sum()), 'joint', int(joint.sum()), 'gem', int(gem.sum()))
print('PAINT chrome lum p10/p50/p90', np.round(np.percentile(lum[chrome], [10, 50, 90]), 3).tolist(),
      'black p50', round(float(np.median(lum[black])), 3))
base = np.where(chrome[..., None], np.clip(base * CHROME_GAIN, 0, 0.95), base)
# joints and caps: dark gunmetal with the paint's detail
jl = (0.05 + 0.25 * lum)[..., None] * np.array([1.0, 1.0, 1.06], np.float32)
base = np.where(joint[..., None], jl, base)
base = np.where(rim[..., None], (0.04 + 0.3 * lum)[..., None] * np.ones(3, np.float32), base)
# gem: deep ruby, each facet lit by its normal (light from above the camera)
light = np.array([0.25, -0.75, 0.6]); light /= np.linalg.norm(light)
facing = np.clip(nrm @ light, 0, 1)
dark = np.array([0.30, 0.01, 0.02]); mid = np.array([0.72, 0.04, 0.05]); hi = np.array([1.0, 0.45, 0.35])
k = (0.35 + 0.65 * facing)[..., None]
gemcol = dark + (mid - dark) * np.clip(k * 1.4, 0, 1)
gemcol = gemcol + (hi - gemcol) * (np.clip((facing - 0.85) / 0.15, 0, 1) * 0.8)[..., None]
base = np.where(gem[..., None], gemcol, base)
save(base, OUT / 'guard_basecolor.png')

normal = np.asarray(Image.open(f'{SRC}_normal.png').convert('RGB').resize((N, N), Image.LANCZOS), np.float32) / 255
normal = np.where((gem | joint)[..., None], np.array([0.5, 0.5, 1.0], np.float32), normal)
save(normal, OUT / 'guard_normal_1k.png', 1024)
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS), np.float32) / 255
ao = np.asarray(Image.open(OUT / 'guard_ao_2k.png').convert('L'), np.float32) / 255
for name, m in (('chrome', chrome), ('black', black), ('cyan', cyan)):
    print('ROUGHNESS', name, 'p10/p50/p90', np.round(np.percentile(rough[m], [10, 50, 90]), 3).tolist())
rough = np.where(chrome, np.clip(rough, 0.25, 0.5), np.where(black, np.clip(rough, 0.3, 0.55),
                 np.where(cyan, np.clip(rough, 0.2, 0.4), np.where(red, np.clip(rough, 0.25, 0.45), rough))))
rough = np.where(gem, 0.12, np.where(joint, 0.5, rough))
ao = np.where(gem, 1.0, ao)
save(np.stack([ao, rough, np.zeros_like(ao)], -1), OUT / 'guard_mr_1k.png', 1024)

chan = np.zeros((N, N, 4), np.float32)
chan[..., 0] = chrome; chan[..., 1] = red; chan[..., 2] = cyan; chan[..., 3] = black | joint   # the gem keeps its ruby paint
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
padded = chan[iy, ix]
padded[valid] = chan[valid]
for c in range(4):
    padded[..., c] = np.where(valid, ndimage.gaussian_filter(padded[..., c], 0.7), padded[..., c])
chans = [Image.fromarray((padded[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'guard_region_mask.png')

emis = np.where(gem, 0.55 + 0.45 * facing, 0.0).astype(np.float32)
emis_p = emis[iy, ix]; emis_p[valid] = emis[valid]
save(emis_p, OUT / 'guard_emission_mask.png', 1024, 'L')

classes = np.zeros((N, N), np.uint8)
classes[chrome] = 9; classes[red | gem] = 11; classes[black | joint] = 10; classes[cyan] = 12; classes[green] = 6
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'guard_material_classes.png')
np.save(ROOT / 'work/part_map_2k.npy', part.astype(np.int8))
json.dump({'chrome_gain': CHROME_GAIN}, open(ROOT / 'work/compose_info.json', 'w'))
