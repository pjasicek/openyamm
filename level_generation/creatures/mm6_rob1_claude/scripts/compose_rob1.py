#!/usr/bin/env python3
"""Patrol Unit texture set from the Meshy retexture (meshy/retexture_v1, painted from the Codex HD masters).

Writes textures/rob1_a_basecolor.png (Meshy base colour, islands padded), rob1_normal_1k.png,
rob1_metal_rough_1k.png (R 1 until the AO bake, G roughness and B metallic by class), rob1_material_classes.png and
rob1_region_weights.npz with four regions, which all change between the native palettes 810/811/812:
  caps   etched steel of the core sphere above and below the belt, and the sensor head box
  rings  the two bronze rings and the pale sensor post
  belt   the recessed equator band of the core sphere (|elevation| < 6.5 degrees)
  eye    the lens (its own part, it slides along the belt in the clips)
The eye glow Meshy painted onto the belt behind the lens is replaced by the belt's own median colour, because the
lens moves along the belt in the clips. Parts come from the face attribute 'part' (work/uv3d.npz).
Fixes after the in-game review (2026-10-08, test_img/2155-2156):
- the sensor head is sensor_rebuild.py geometry (parts 41..45) painted here with flat metal colours (no Meshy paint);
- the rings' lip and inner faces (closer to the centre than the outer face) take a dark ring tone; Meshy painted them
  light and the ramps turned that into white lines along the rims;
- third review (test_img/2158, indoors: flat, washed out, no outlines): core and rings take the native brightness at
  their elevation (claude_shared/native_shading.py, config native_shading.json) with Meshy's detail on top, dark lips, a bright line on the rings'
  rounded outer edge; glossy, not metallic;
- the belt keeps only its broad shading (Meshy's grainy streaks read as fabric);
- texels within SEAM_PX of a UV island edge are blended with their 3D neighbours (same part, any island), so
  neighbouring islands agree across seams.
Next: bake AO, grade, then scripts/tier_ramps.py (ramps from the native palette sprites)."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import native_shading as NS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
CENTRE_Z = 0.4239
BELT_HALF = 0.400 * np.sin(np.radians(6.5))
RING_OUTER = 0.423
SEAM_PX = 6
# Sensor head colours (tier A sRGB, from the HD masters): post pale tan, block pale steel, nozzle steel, lens dark
# glass with a dark steel rim, vents dark.
SENSOR = {41: (0.66, 0.58, 0.50), 42: (0.62, 0.68, 0.72), 43: (0.50, 0.55, 0.59), 44: (0.22, 0.24, 0.26),
          45: (0.30, 0.33, 0.36)}
LENS_GLASS = (0.05, 0.05, 0.07)
data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o


def save(array, path, size=None, mode=None):
    image = Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode)
    if size:
        image = image.resize((size, size), Image.NEAREST if mode == 'L' else Image.LANCZOS)
    image.save(path, optimize=True)


base = C.load(str(SRC) + '_base_color.png')
normal = C.load(str(SRC) + '_normal.png')
rough = C.load(str(SRC) + '_roughness.png', 'L')
h, s, v = C.hsv(base)
valid = part_map >= 0
z = xyz[..., 2] - CENTRE_Z
core = part_map == 0
belt = core & (np.abs(z) < BELT_HALF)
caps = core & ~belt
rings = (part_map == 1) | (part_map == 2)
eye = part_map == 3
sensor = part_map >= 41
post = part_map == 41
lens = part_map == 44
caps |= sensor & ~post & ~lens
rings |= post

# Glow painted on the belt (yellow/orange, bright) -> the belt's median colour, keeping Meshy's luminance detail.
glow = belt & (((h > 15) & (h < 70) & (v > 0.55)) | (v > 0.85))
glow = ndimage.binary_dilation(glow, iterations=3) & belt
plain = belt & ~glow
median = np.median(base[plain], 0)
base[glow] = median
# The belt is a smooth glossy band in the sprites; Meshy painted grainy streaks. Keep only its broad shading.
for c in range(3):
    channel = base[..., c]
    blurred = ndimage.gaussian_filter(np.where(belt, channel, 0.0), 8.0)
    norm = ndimage.gaussian_filter(belt.astype(np.float64), 8.0)
    channel[belt] = (blurred / np.maximum(norm, 1e-6))[belt]

# Native shading transfer (claude_shared/native_shading.py, ../NATIVE_SHADING_TRANSFER.md; third review): the
# sprites are lit from above, so the top cap and upper ring are bright and the belt, lower ring and lower cap dark;
# that contrast is much of why the sprite reads as 3D. Core and ring texels take the native brightness at their
# elevation as a grey, times the base's local detail (full strength on the caps for the etching, weaker on the smooth
# rings and belt). Rings x0.62: the sprite's rings are dark warm chrome whose shine is in highlights, not in their
# mid tone (the median per elevation of the side views averages the highlights in). The tier ramps recolour.
dist = np.linalg.norm(xyz - np.array([0.0, 0.0, CENTRE_Z]), axis=-1)
profile = json.loads((ROOT / 'work' / 'native_shading' / 'profile.json').read_text())
elevation = NS.texel_coordinate(xyz, 'elevation', centre=(0.0, 0.0, CENTRE_Z))
detail = NS.detail_of(base)
ring_parts = (part_map == 1) | (part_map == 2)
for region, strength, scale in ((core & ~belt, 1.0, 0.95), (ring_parts, 0.5, 0.62), (belt, 0.3, 1.0)):
    NS.shade(base, elevation, region, profile, scale=scale, detail_strength=strength, detail=detail)
# Ring lips and inner faces dark; the rounded outer edge of each ring a bright line above the dark gap, which
# outlines the parts like the sprite's lit rims.
lip = ring_parts & (dist < RING_OUTER - 0.007)   # outer face 0.420..0.423 after decimation sag, bevel to 0.417
base[lip] = 0.08
bevel = ring_parts & (dist >= RING_OUTER - 0.007) & (dist < RING_OUTER - 0.0025)
base[bevel] = np.clip(base[bevel] * 1.5 + 0.08, 0, 1)

# Sensor head: flat metal colours, a little value noise so it is not plastic-flat.
rng = np.random.default_rng(6)
noise = ndimage.gaussian_filter(rng.standard_normal(part_map.shape), 2.0)
noise = 1.0 + 0.06 * noise / max(np.abs(noise).max(), 1e-6)
for label, colour in SENSOR.items():
    m = part_map == label
    base[m] = np.array(colour) * noise[m, None]
glass = lens & (xyz[..., 1] < -0.166)
base[glass] = LENS_GLASS

# Seam blending: texels near an island edge take the mean of their 3D neighbours (same part, all islands).
edge_dist = ndimage.distance_transform_edt(strict >= 0)
for parts in ((0,), (1,), (2,)):
    region = np.isin(part_map, parts) & (strict >= 0)
    if not region.any():
        continue
    ys, xs = np.nonzero(region)
    sample = (ys % 2 == 0) & (xs % 2 == 0)
    tree = cKDTree(xyz[ys[sample], xs[sample]])
    colours = base[ys[sample], xs[sample]]
    band = region & (edge_dist <= SEAM_PX)
    by, bx = np.nonzero(band)
    _, idx = tree.query(xyz[by, bx], k=48)
    mean = colours[idx].mean(1)
    w = np.clip(1.0 - (edge_dist[by, bx] - 1.0) / SEAM_PX, 0.0, 1.0)[:, None]
    base[by, bx] = base[by, bx] * (1 - w) + mean * w
base = pad(base)

regions = {'caps': caps, 'rings': rings, 'belt': belt, 'eye': eye}
weights = {k: pad(ndimage.gaussian_filter(m.astype(np.float32), 1.0) * valid) for k, m in regions.items()}
classes = np.zeros(part_map.shape, np.uint8)
classes[valid] = 9                 # metal
classes[eye] = 6                   # eye (glowing lens)
normal[sensor] = (0.5, 0.5, 1.0)
normal = pad(normal)
# Glossy, not metallic: a metallic texel loses its diffuse colour and depended on the sky reflection (chalky and
# uneven indoors in the second try). Glossy rings and belt still catch small highlights from the lights.
r = np.clip(rough * 0.15 + 0.38, 0.3, 0.55)
metal = np.zeros_like(r)
r[rings] = 0.3; r[belt] = 0.4; r[lip] = 0.7
r[caps] = np.clip(rough[caps] * 0.15 + 0.42, 0.38, 0.55)
r[eye] = 0.2; r[sensor] = 0.4; r[glass] = 0.12
r, metal = pad(r), pad(metal)
save(base, OUT / 'rob1_a_basecolor.png')
save(normal, OUT / 'rob1_normal_1k.png', 1024)
save(np.stack([np.ones_like(r), r, metal], -1), OUT / 'rob1_metal_rough_1k.png', 1024)
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'rob1_material_classes.png')
np.savez_compressed(OUT / 'rob1_region_weights.npz', names=np.array(list(regions)), **weights)
print('COMPOSED', {k: int(m.sum()) for k, m in regions.items()}, 'glow', int(glow.sum()), 'lip', int(lip.sum()),
      'belt median', np.round(median, 3).tolist())
