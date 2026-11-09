"""Wyvern maps for the rebuilt reduction from its Meshy retexture (meshy/retexture_r1), the creature's own contract
(mm8_m560_claude/scripts/compose_textures.py): AO-graded base colour, red iris on the eyes, membrane/body region
mask, native palette ramps for tiers A/B/C, 1K normal and ORM, material classes for the ORM step.
New here: the rebuilt teeth and dorsal spikes (part labels from build_parts.py) are painted ivory, darker at the
root and brighter toward the tip, with a little of Meshy's luminance detail; the Meshy paint on such small islands
is noise (the old teeth came back green).
Usage: compose.py  (work/uv3d.npz, work/rebuild.json, textures/wyvern_ao.png -> textures/*)"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]; T = P / 'textures'; S = P / 'meshy/retexture_r1/texture_urls_0'
M = P.parent / 'mm8_m560_claude'
sys.path[:0] = [str(P.parent / 'claude_shared'), str(P.parent / 'mm6_gob_claude/scripts')]
import region_variants as R  # noqa: E402
from material_classes_to_orm import accessor  # noqa: E402
import compose_textures_v2 as C  # noqa: E402

# Meshy recentres and doubles the static upload; its UVs and indexed surface must match exactly
a, ab = R.read_glb(P / 'texturing/wyvern_upload.glb'); b, bb = R.read_glb(P / 'meshy/retexture_r1/model_urls_glb.glb')
ap = a['meshes'][0]['primitives'][0]; bp = b['meshes'][0]['primitives'][0]
x = accessor(a, ab, ap['attributes']['POSITION']); y = accessor(b, bb, bp['attributes']['POSITION'])
u = accessor(a, ab, ap['attributes']['TEXCOORD_0']); v = accessor(b, bb, bp['attributes']['TEXCOORD_0'])
i = accessor(a, ab, ap['indices']).astype(int).ravel(); j = accessor(b, bb, bp['indices']).astype(int).ravel()
assert len(i) == len(j), (len(i), len(j))
centre = (x.max(0) + x.min(0)) * .5; scale = (y.max(0) - y.min(0)).max() / (x.max(0) - x.min(0)).max()
source = np.c_[(x - centre) * scale, u][i]; returned = np.c_[y - (y.max(0) + y.min(0)) * .5, v][j]
parity = (float(cKDTree(source).query(returned)[0].max()), float(cKDTree(returned).query(source)[0].max()))
assert max(parity) < 2e-6, parity
print('PARITY return scale', round(float(scale), 4), 'max corner error', parity)

data = np.load(P / 'work/uv3d.npz'); part, xyz = C.rasterise(data, tol=0)
valid = part >= 0; interior = ndimage.binary_erosion(valid, iterations=1)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(img):
    out = img[iy, ix]; out[interior] = img[interior]; return out


base = pad(C.load(str(S) + '_base_color.png')); h, s, val = C.hsv(base)
# material classes of the creature's ORM contract: 1 hide, 3 membrane, 4 horn/claw, 5 tooth, 6 eye, 7 mouth
classes = np.ones(part.shape, np.uint8)
for p, c in {1: 3, 2: 6, 3: 7, 4: 4, 5: 5}.items():
    classes[part == p] = c
# claws and the tail-tip horn are part of the body surface: bright, unsaturated paint there (creature rule)
classes[(part == 0) & (((xyz[..., 2] < .025) & (xyz[..., 1] > -.06)) | (xyz[..., 1] > .465)) & (s < .35) & (val > .45)] = 4
eye = classes == 6; eye_lum = base.mean(-1)
base[eye] = np.clip(np.array([.8, .07, .025]) * np.clip(eye_lum[eye, None] / .35, .25, 1.4), 0, 1)

# ivory teeth and spikes, root to tip
reb = json.loads((P / 'work/rebuild.json').read_text())
roots = np.array([t['gum'] for t in reb['teeth']] + [sp['root'] for sp in reb['spikes']])
lengths = np.array([t['length'] for t in reb['teeth']] + [sp['length'] for sp in reb['spikes']])
ivory = (part == 4) | (part == 5)
k = cKDTree(roots).query(xyz[ivory])[1]
t = np.clip(np.linalg.norm(xyz[ivory] - roots[k], axis=1) / lengths[k], 0, 1) ** .7
root_col, tip_col = np.array([.60, .54, .43]), np.array([.93, .89, .80])
lum = base[ivory].mean(-1); detail = np.clip(1 + .5 * (lum / max(float(np.median(lum)), 1e-3) - 1), .9, 1.1)
base[ivory] = np.clip((root_col * (1 - t[:, None]) + tip_col * t[:, None]) * detail[:, None], 0, 1)

ao = pad(C.load(T / 'wyvern_ao.png', 'L')); ao = ndimage.gaussian_filter(ao, 1)
base *= (.65 + .35 * ao)[..., None]
membrane = (classes == 3) & (h < 65) & (s > .2)
body = np.isin(classes, [1, 3]) & ~membrane
weights = [pad(ndimage.gaussian_filter(sel.astype(np.float32), .6)) for sel in [membrane & valid, body & valid]]
for w in weights:
    assert int((w > .9).sum()) > 1000
R.write_mask(weights, T / 'wyvern_region_mask.png')


def save(img, path, size=None):
    im = Image.fromarray(np.clip(img * 255 + .5, 0, 255).astype(np.uint8))
    if size:
        im = im.resize((size, size), Image.Resampling.LANCZOS)
    im.save(path)


save(pad(base), T / 'wyvern_basecolor.png')
save(pad(C.load(str(S) + '_normal.png')), T / 'wyvern_normal_1k.png', 1024)
rough = pad(C.load(str(S) + '_roughness.png', 'L'))
save(np.stack([ao, rough, np.zeros_like(rough)], -1), T / 'wyvern_orm_1k.png', 1024)
Image.fromarray(pad(classes)).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'wyvern_material_classes.png')

# native palette ramps: identical native pixels across the tier palettes (creature's own method)
native = P.parent / 'mm8_m560/native_variants'
sources = json.loads((P.parent / 'mm8_m560/sources.json').read_text())['sources']
regions = []; pixels = {n: [] for n in [561, 562, 563]}
for key, item in sources.items():
    if not key.startswith(('m560s', 'm560w')):
        continue
    path = native / (key + '_561.png')
    if not path.exists():
        continue
    rgb = C.load(path); hh, ss, vv = C.hsv(rgb); opaque = np.asarray(Image.open(P.parents[2] / item['path'])) != 0
    wing = opaque & (hh > 20) & (hh < 65) & (ss > .35)
    skin = opaque & (hh >= 65) & (hh < 170) & (ss > .18)
    yy, xx = np.nonzero(wing | skin); regions.append(np.where(wing[yy, xx], 0, 1))
    for pal in pixels:
        pixels[pal].append(C.load(native / (key + f'_{pal}.png'))[yy, xx])
regions = np.concatenate(regions); pixels = {k2: np.concatenate(v2) for k2, v2 in pixels.items()}
ramps = {f'm560_{tier}': [] for tier in 'abc'}; lumb = R.luminance(base)
for ri, w in enumerate(weights):
    values = np.sort(lumb[(w > .9) & valid]); lo, hi = np.percentile(values, [.5, 99.5])
    quant = np.searchsorted(values, np.linspace(lo, hi, 16)) / len(values)
    sel = regions == ri; assert sel.sum() > 500
    order = np.argsort(R.luminance(pixels[561][sel])); half = max(2, len(order) // 100)
    for tier, pal in zip('abc', [561, 562, 563]):
        native_rgb = pixels[pal][sel][order]; colors = []
        for q in quant:
            c0 = int(q * (len(order) - 1)); rgb = np.median(native_rgb[max(0, c0 - half):c0 + half + 1], axis=0)
            colors.append(R.srgb_to_linear(np.clip(rgb * 1.15, 0, 1)).tolist())
        ramps['m560_' + tier].append({'range': [float(lo), float(hi)], 'colors': colors})
config = {'variants': ['m560_a', 'm560_b', 'm560_c'], 'materials': [{'base': 'Wyvern_A', 'prefix': 'Wyvern',
          'mask': 'wyvern_region_mask.png', 'regions': ['membrane', 'body'],
          'palettes': {'m560_a': 561, 'm560_b': 562, 'm560_c': 563}, 'ramps': ramps}]}
(T / 'wyvern_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
report = {'parity_max_corner_error': parity, 'classes': {str(c): int(((classes == c) & valid).sum()) for c in np.unique(classes)},
          'atlas_coverage': float(valid.mean()), 'ivory_texels': int(ivory.sum())}
(P / 'review/texture_report.json').write_text(json.dumps(report, indent=2) + '\n'); print('COMPOSED', report)
