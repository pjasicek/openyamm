"""Texture pass step 5: the runtime maps on the new layout from the two 4K Meshy returns, by the production method
(compose_textures.py): paints crossfaded across the neck, subtle AO, native-palette regions and ramps, wet nonmetal
response. Colour and normal 4K -> 2K once (Lanczos), metal/roughness and region mask 1K.

Changes from the production compose, all for the new single atlas:
- head-set charts take the body paint below the gills and the head paint above (same 1.54-1.66 m crossfade); body
  charts take the body paint only, so the head/body chart seam joins two body-paint texels;
- the fin region is limited to where the approved mask had fins (dilated 4 texels at 2K), and approved-masked
  texels the new hue test leaves out keep their approved region (no unrecoloured specks);
- normal maps crossfade like the colour (no flattened neck band: there is no paint seam on the neck any more);
- the eyes keep the approved paint (2026-11-01 review: the 4K head paint drew thin, off-centre slit pupils and lost
  the dark iris rim): approved base colour at the same surface points within EYE_RIM of the approved yellow eye
  texels, feathered over EYE_FEATHER, with a flat normal under the eyeball.
Writes textures/m500_tp_*.png, textures/m500_tp_ramps.json and texpass/compose_report.json.
Usage: texpass_compose.py [grade]   grade: production (AO 0.15 multiply, default) | none
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from texpass_glb import BEFORE, PROJECT, ROOT, TP, read_glb  # noqa: E402
from transfer_textures import image as glb_image, sample  # noqa: E402

sys.path.insert(0, str(PROJECT.parent / 'claude_shared'))
import region_variants as R  # noqa: E402
from normal_map_convention import measure  # noqa: E402

GRADE = sys.argv[1] if len(sys.argv) > 1 else 'production'
T = PROJECT / 'textures'
MESHY = PROJECT / 'meshy'
N2, N1 = 2048, 1024
EYE_RIM, EYE_FEATHER = .0025, .0025  # metres on the model surface
MM8_SPRITES = ROOT / 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites'


def load(path, size, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode).resize((size, size), Image.Resampling.LANCZOS), float) / 255


def save(a, path):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(path, optimize=True)


def pad(a, cov):
    return a[tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))]


def hsv(img):
    v = np.asarray(Image.fromarray(np.uint8(np.clip(img, 0, 1) * 255)).convert('HSV'), float) / 255
    return v[..., 0] * 360, v[..., 1], v[..., 2]


def fade(raster):
    f = np.clip((raster['pos'][..., 1] - 1.54) / .12, 0, 1)
    return np.where(raster['head'], f * f * (3 - 2 * f), 0.0)


def paints(name, size, mode='RGB'):
    body = load(MESHY / f'body_retexture_tp/texture_urls_0_{name}.png', size, mode)
    head = load(MESHY / f'head_retexture_tp/texture_urls_0_{name}.png', size, mode)
    return body, head


r2 = dict(np.load(TP / 'raster_2048.npz'))
r1 = dict(np.load(TP / 'raster_1024.npz'))
cov2, cov1 = r2['triangle'] >= 0, r1['triangle'] >= 0
f2, f1 = fade(r2)[..., None], fade(r1)

# ---- base colour
body, head = paints('base_color', N2)
img = body * (1 - f2) + head * f2
raw = img.copy()
ao = ndimage.gaussian_filter(pad(np.asarray(Image.open(TP / 'ao_2048.png').convert('L'), float) / 255, cov2), 1)
if GRADE == 'production':
    img = img * (.85 + .15 * np.maximum(ao, .4))[..., None]

# ---- regions: production hue test, limited to the approved regions
doc, binary = read_glb(BEFORE)
old_mask = glb_image(doc, binary, doc['materials'][0]['extras']['openyamm_region_mask']['index'], 'RGBA') / 255
old_uv = r2['old_uv'].reshape(-1, 2)
approved = sample(old_mask, old_uv, nearest=True).reshape(N2, N2, 4)[..., :3] * cov2[..., None]
pos = r2['pos']
old_base = sample(glb_image(doc, binary, doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index'])
                  / 255, old_uv).reshape(N2, N2, 3)
eye_zone = cov2 & r2['head'] & (pos[..., 1] > 1.64) & (np.abs(pos[..., 0]) > .035)
oh, os_, _ = hsv(old_base)
eye = eye_zone & (oh > 32) & (oh < 72) & (os_ > .5)
distance = np.full((N2, N2), np.inf)
distance[eye_zone] = cKDTree(pos[eye]).query(pos[eye_zone])[0]
eye_blend = np.clip(1 - (distance - EYE_RIM) / EYE_FEATHER, 0, 1)[..., None]
img = img * (1 - eye_blend) + old_base * eye_blend
h, s, v = hsv(img)
fin = cov2 & ((h > 285) | (h < 25)) & (s > .16) & (v > .25)
pale = cov2 & (s < .28) & (v > .25) & ~eye & ~fin
scale = cov2 & ~pale & ~fin & ~eye & (h > 125) & (h < 290)
hue = [scale, pale, fin]
approved_class = approved > .5
near = [ndimage.binary_dilation(a, iterations=4) for a in approved_class.transpose(2, 0, 1)]
# Scales and ventral follow the new paint (its ventral edge follows the HD masters, not the approved paint's); only
# the fin hue is held to the approved fins, so reddish flecks on the scales are not picked up as fins.
regions = [scale, pale, fin & near[2]]
assigned = regions[0] | regions[1] | regions[2] | eye
leftover = approved_class.any(-1) & ~assigned
best = approved.argmax(-1)
for c in range(3):
    regions[c] |= leftover & (best == c)
report = {'grade': GRADE,
          'hue_texels': [int(m.sum()) for m in hue], 'region_texels': [int(m.sum()) for m in regions],
          'hue_outside_approved': [int((m & ~n).sum()) for m, n in zip(hue, near)],
          'leftover_from_approved': int(leftover.sum()), 'eye_texels': int(eye.sum()),
          'eye_carried_texels': int((eye_blend > 0).sum()),
          'unmasked_texels': int((cov2 & ~(regions[0] | regions[1] | regions[2])).sum()),
          'approved_unmasked_texels': int((cov2 & ~approved_class.any(-1)).sum())}
classes = np.zeros((N2, N2), np.uint8)
classes[cov2] = 1
classes[regions[1]] = 2
classes[regions[2]] = 3
classes[eye] = 6
Image.fromarray(classes).save(T / 'm500_tp_material_classes.png')
img = pad(img, cov2)
save(img, T / 'm500_tp_basecolor_2k.png')
save(pad(raw, cov2), TP / 'basecolor_raw_2k.png')
R.write_mask([ndimage.gaussian_filter(pad(m.astype(float), cov2), .5) for m in regions],
             T / 'm500_tp_region_mask_1k.png', size=N1)

# ---- normal (Meshy +y down -> glTF, measured)
normals, corr = [], []
for kind in ('body', 'head'):
    raw_n = np.asarray(Image.open(MESHY / f'{kind}_retexture_tp/texture_urls_0_normal.png').convert('RGB')).copy()
    c = measure(raw_n)
    corr.append(float(c))
    if c <= -.15:
        raw_n[..., 1] = 255 - raw_n[..., 1]
    n = np.asarray(Image.fromarray(raw_n).resize((N2, N2), Image.Resampling.LANCZOS), float) / 255 * 2 - 1
    normals.append(n)
n = normals[0] * (1 - f2) + normals[1] * f2
n = n * (1 - eye_blend) + np.array([0., 0., 1.]) * eye_blend
n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
save(pad(n * .5 + .5, cov2), T / 'm500_tp_normal_2k.png')
report['normal_correlation'] = corr

# ---- metal/roughness at 1K: R specular mask, G roughness, B zero metallic
rb, rh = paints('roughness', N1, 'L')
rough = rb * (1 - f1) + rh * f1
c1 = np.asarray(Image.fromarray(classes).resize((N1, N1), Image.Resampling.NEAREST))
rg = np.clip(.49 + .16 * (rough - .5), .40, .60)
spec = np.full((N1, N1), .33)
for cls, r, sp in ((2, .52, .28), (3, .53, .22), (6, .22, .85)):
    rg[c1 == cls] = r
    spec[c1 == cls] = sp
save(np.stack([pad(spec, cov1), pad(rg, cov1), np.zeros((N1, N1))], -1), T / 'm500_tp_metal_rough_1k.png')

# ---- ramps from the native palettes (production method), range and mid from the new paint
pals = {n: np.frombuffer((ROOT / f'assets_dev/worlds/mm8/textures/pal{n}.act').read_bytes()[:768],
                         np.uint8).reshape(256, 3) / 255 for n in (501, 502)}
ids = np.concatenate([np.asarray(Image.open(MM8_SPRITES / f'm500sa{k}.bmp')).ravel() for k in range(5)])
ids = ids[ids != 0]
nh, ns, nv = hsv(pals[501][ids][:, None])
nh, ns, nv = nh[:, 0], ns[:, 0], nv[:, 0]
select = [(nh > 155) & (nh < 285) & (ns > .2), (ns < .25) & (nv > .25), ((nh > 285) | (nh < 20)) & (ns > .15) & (nv > .2)]
# Contrast pin: the 4K paint spreads each region's luminance wider around its median than the approved paint
# (fins and palms most); k scales the ramp's slope so the approved tier A's p10-p90 spread (lum / median, same
# surface points) is kept while the median stays on the native target.
old_lum = R.luminance(np.clip(old_base, 0, 1))
ramps, stats = {}, []
for c in range(3):
    lum = R.luminance(img[regions[c]])
    lo, hi = np.percentile(lum, [1, 99])
    mid = float(np.median(lum))
    both = regions[c] & approved_class[..., c]
    old_range = doc['materials'][0]['extras']['openyamm_region_ramps'][c]['range']
    # The approved render is linear in luminance over its range too, so its spread is the base luminance spread.
    a = np.clip(old_lum[both], old_range[0], old_range[1])
    b = R.luminance(img[both])
    spread = lambda v: (np.percentile(v, 90) - np.percentile(v, 10)) / np.median(v)  # noqa: E731
    k = float(min(1.0, spread(a) / spread(b)))
    stats.append({'lo': float(lo), 'hi': float(hi), 'mid': mid, 'contrast_k': round(k, 3),
                  'spread_approved': round(float(spread(a)), 3), 'spread_new': round(float(spread(b)), 3)})
for variant, palette in (('water_a', 501), ('water_b', 502), ('water_c', 501)):
    ramps[variant] = []
    for c in range(3):
        cols = pals[palette][ids[select[c]]]
        target = np.clip(np.median(cols, axis=0) * [1.65, 1.14, 1.12][c], 0, 1)
        lo, hi, mid, k = stats[c]['lo'], stats[c]['hi'], stats[c]['mid'], stats[c]['contrast_k']
        ramps[variant].append({'range': [lo, hi], 'colors': [
            np.clip(R.srgb_to_linear(target) * (1 + k * ((lo + i / 15 * (hi - lo)) / mid - 1)), 0, 1).tolist()
            for i in range(16)]})
old_ramps = doc['materials'][0]['extras']['openyamm_region_ramps']
report['ranges_new'] = stats
report['ranges_installed'] = [r['range'] for r in old_ramps]
cfg = {'variants': list(ramps), 'palettes': {'water_a': 501, 'water_b': 502, 'water_c': 501},
       'materials': [{'base': 'WaterElemental_A', 'prefix': 'WaterElemental', 'mask': 'm500_tp_region_mask_1k.png',
                      'regions': ['scales', 'ventral', 'fins'], 'ramps': ramps}]}
(T / 'm500_tp_ramps.json').write_text(json.dumps(cfg, indent=2) + '\n')
(TP / 'compose_report.json').write_text(json.dumps(report, indent=1) + '\n')
print(json.dumps(report, indent=1))
