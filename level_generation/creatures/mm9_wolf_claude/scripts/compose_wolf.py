#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the MM9 wolf (CLAUDE_CREATURE_TEXTURES.md; ported from
mm9_lobber_claude/scripts/compose.py). Usage: compose_wolf.py

Inputs: meshy/wolf_retexture_v2 maps (our UVs), textures/wolf_ao_2k.png, work/uv3d_wolf.npz and
work/uv3d_mm9_wolf.npz (dump_uv3d.py), the three MM9 skins (WOLF, WOLFRED, WOLFBLACK; MONSTERS.txt rows 114-116).
Outputs in textures/: wolf_basecolor.png (2K, gutters padded; graded separately by grade_basecolor.py),
wolf_normal_1k.png, wolf_metal_rough_1k.png (R AO, G roughness, B metallic 0), wolf_material_classes.png,
wolf_region_mask.png, wolf_ramps.json.
Regions (from the mesh, not from colour alone):
  R fur      - every body texel outside the other regions;
  G mouth    - head texels with a red/pink hue (gums, tongue, inner lips);
  B eyes     - the two separate eye pieces;
  A teeth    - the separate tooth and claw pieces (identity ramps in every tier: white teeth, dark claws).
MM9 skin texels: the same classes on the MM9 grey-wolf skin (mouth by hue in the head; the rest fur; eyes by their
amber hue in the head), sampled in every tier skin (all three share the MM9 UVs).
Tier colours (dragonfly method): tier A keeps the HD look (identity ramps); B/C take hue from their own MM9 skin
(chroma by luminance percentile), saturation scaled by how much more vivid our A is than MM9's A, brightness by the
MM9 tier/A ratio.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / 'wolf_retexture_v2'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'wolf_a': 'wolf/skins/wolf.png', 'wolf_b': 'wolfred/skins/wolfred.png',
         'wolf_c': 'wolfblack/skins/wolfblack.png'}
TIER_A = 'wolf_a'
REGIONS = ('fur', 'mouth', 'eyes', 'teeth')
IDENTITY = {'teeth'}
MAT = 'Wolf'


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size, fields):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    out = {f: np.zeros((size, size), np.float32) for f in fields}
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        for f in fields:
            v = d[f][t]
            out[f][rows, cols] = l1[inside] * v[0] + l2[inside] * v[1] + l3[inside] * v[2]
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


# ---------------- our texel classes (1K)
S = 1024
tri, f, dbody = raster(HERE / 'work' / 'uv3d_wolf.npz', S, ['head'])
covered = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(covered, dbody['part'][ti], -1)
cen = dbody['xyz'].mean(1)[ti]
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'), np.float32) / 255
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
piece = covered & (part % 10 == 2)
eyes = piece & (cen[..., 2] > 1.85) & (cen[..., 1] < -1.2)
teeth = piece & ~eyes
head = covered & ~piece & (f['head'] > 0.5)
red = ((h < 25) | (h > 330)) & (s > 0.25) & (v > 0.12)
mouth = head & ndimage.binary_opening(red, iterations=1)
fur = covered & ~(eyes | teeth | mouth)
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((fur, mouth, eyes, teeth)):
    classes[m] = k + 1
regions = [feather(m, covered) for m in (fur, mouth, eyes, teeth)]
RV.write_mask(regions, T / 'wolf_region_mask.png')
Image.fromarray(classes * 60).save(T / 'wolf_material_classes.png')
tri2, _, _ = raster(HERE / 'work' / 'uv3d_wolf.npz', 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'wolf_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'wolf_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
# fur matte, wet mouth, glossy eyes, enamel/keratin in between
rough = np.where(fur, np.clip(rough, 0.72, 0.92), np.where(mouth, 0.42, np.where(eyes, 0.2, 0.45)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'wolf_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'wolf_metal_rough_1k.png')

# ---------------- MM9 skin regions (256x256 skins; classes from the tier-1 skin, same UVs for every tier)
ms = 256
mtri, mf, dmm = raster(HERE / 'work' / 'uv3d_mm9_wolf.npz', ms, ['head'])
mcov = mtri >= 0
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
mh, msat, mv = hsv(skins[TIER_A])
mhead = mcov & (mf['head'] > 0.5)
m_mouth = mhead & ((mh < 25) | (mh > 330)) & (msat > 0.3) & (mv > 0.15)
m_eyes = mhead & (mh > 25) & (mh < 60) & (msat > 0.45) & (mv > 0.35)
m_teeth = mhead & (msat < 0.15) & (mv > 0.8)
m_fur = mcov & ~(m_mouth | m_eyes | m_teeth)
mm9_sets = {'fur': m_fur, 'mouth': m_mouth, 'eyes': m_eyes, 'teeth': m_teeth}
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, name):
    core = weight > 0.5
    targets = {TIER_A: graded.copy()}
    mm9_mask = mm9_sets[name]
    if name in IDENTITY or mm9_mask.sum() < 12 or core.sum() < 12:
        for k in TIERS:
            targets[k] = graded.copy()
        return targets
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands(k):
        pal = lin(skins[k][mm9_mask])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])

    pal_a, band_a = bands(TIER_A)
    # our tier A is a near-grey wolf: its saturation ratio to the grey MM9 skin says nothing about B/C, keep MM9 chroma
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.0))
    for k in TIERS:
        if k == TIER_A:
            continue
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * k_sat
        # MM9 tier/A brightness ratio, partly restoring MM9's absolute level (our HD tier A is darker than MM9's A)
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean()) * (float((pal_a @ W).mean()) / max(
            float(glum.mean()), 1e-4)) ** 0.5
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'wolf_basecolor_graded.png', S) if (T / 'wolf_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, name)
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'wolf_region_mask.png', 'ramps': ramps}]},
          open(T / 'wolf_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[fur] = (0.6, 0.6, 0.6)
prev[mouth] = (0.9, 0.3, 0.4)
prev[eyes] = (1.0, 0.8, 0.1)
prev[teeth] = (0.2, 0.8, 0.9)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'wolf_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report,
                              'our_texels': {k: int(m.sum()) for k, m in zip(REGIONS, (fur, mouth, eyes, teeth))}}))
