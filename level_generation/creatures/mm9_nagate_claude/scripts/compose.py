#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Lobber or the Lobber Pod (CLAUDE_CREATURE_TEXTURES.md;
ported from mm9_dfly_claude/scripts/compose_dfly.py). Usage: compose.py lobber|pod

Inputs: meshy/<body>_retexture_v1 maps (our UVs), textures/<body>_ao_2k.png, work/uv3d_<body>.npz and
work/uv3d_mm9_<body>.npz (dump_uv3d.py), the MM9 skins of every tier.
Outputs in textures/: <body>_basecolor.png (2K, gutters padded; graded separately by grade_basecolor.py),
<body>_normal_1k.png, <body>_metal_rough_1k.png (R AO, G roughness, B metallic 0), <body>_material_classes.png,
<body>_region_mask.png, <body>_ramps.json. Regions are hue families, so one luminance ramp can reproduce tier A:
R red/magenta flesh, G olive/brown/yellow (stalk, limbs, the head's back), B teal/blue (mouth interior, tendrils),
A violet (lid edges); bins smoothed (blurred indicators, argmax). The same bins on the MM9 tier-1 skin pick the
texels sampled in every tier skin (all tiers share the MM9 UVs; an empty MM9 bin falls back to the whole skin).
Tier colours (dragonfly method): tier A keeps the HD look (identity ramps); the others take hue from their own MM9
skin (chroma by luminance percentile), saturation scaled by how much more vivid our A is than MM9's A, brightness
by the MM9 tier/A ratio.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

BODY = sys.argv[1]
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / f'{BODY}_retexture_v1'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'lobber': {'lobber_a': 'lobber/skins/lobber.png', 'lobber_b': 'icelobber/skins/icelobber.png'},
         'pod': {'pod_a': 'pod/skins/pod.png', 'pod_b': 'pod2/skins/pod2.png', 'pod_c': 'icepod/skins/icepod.png'}}[BODY]
TIER_A = next(iter(TIERS))
REGIONS = ('flesh', 'green', 'mouth', 'violet')
MAT = {'lobber': 'Lobber', 'pod': 'Pod'}[BODY]


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
tri, f, dbody = raster(HERE / 'work' / f'uv3d_{BODY}.npz', S, ['limb', 'head'])
covered = tri >= 0
part = np.where(covered, dbody['part'][np.maximum(tri, 0)], -1)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'), np.float32) / 255
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
HUES = ((320, 20), (20, 150), (150, 250), (250, 320))  # red/magenta, olive/brown/yellow, teal/blue, violet


def hue_classes(h, covered, sigma):
    """Per-texel hue bin, smoothed (indicator maps blurred, argmax) so scale patterns do not flicker between bins."""
    ind = []
    for lo, hi in HUES:
        m = ((h >= lo) | (h < hi)) if lo > hi else ((h >= lo) & (h < hi))
        ind.append(ndimage.gaussian_filter((m & covered).astype(np.float32), sigma))
    return np.argmax(np.stack(ind), 0)


hc = hue_classes(h, covered, 2.0)
flesh, green, mouth, violet = [(hc == k) & covered for k in range(4)]
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((flesh, green, mouth, violet)):
    classes[m] = k + 1
regions = [feather(m, covered) for m in (flesh, green, mouth, violet)]
RV.write_mask(regions, T / f'{BODY}_region_mask.png')
Image.fromarray(classes * 80).save(T / f'{BODY}_material_classes.png')
tri2, _, _ = raster(HERE / 'work' / f'uv3d_{BODY}.npz', 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / f'{BODY}_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(
    T / f'{BODY}_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(mouth, 0.4, np.where(green, np.clip(rough, 0.6, 0.85), np.clip(rough, 0.5, 0.75)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / f'{BODY}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / f'{BODY}_metal_rough_1k.png')

# ---------------- MM9 skin regions (128x128 skins; classes from the tier-1 skin, same UVs for every tier)
ms = 128
mtri, mf, dmm = raster(HERE / 'work' / f'uv3d_mm9_{BODY}.npz', ms, ['head'])
mcov = mtri >= 0
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
mh, msat, mv = hsv(skins[TIER_A])
mhc = hue_classes(mh, mcov, 0.7)
m_flesh, m_green, m_mouth, m_violet = [(mhc == k) & mcov for k in range(4)]
mm9_sets = {'flesh': m_flesh, 'green': m_green, 'mouth': m_mouth, 'violet': m_violet}
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, mm9_mask):
    core = weight > 0.5
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands(k):
        pal = lin(skins[k][mm9_mask if mm9_mask.sum() >= 12 else mcov])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])

    pal_a, band_a = bands(TIER_A)
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.8))
    targets = {TIER_A: graded.copy()}
    for k in TIERS:
        if k == TIER_A:
            continue
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * k_sat
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean())
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / f'{BODY}_basecolor_graded.png', S) if (T / f'{BODY}_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, mm9_sets[name])
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': f'{BODY}_region_mask.png', 'ramps': ramps}]},
          open(T / f'{BODY}_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[flesh] = (0.9, 0.3, 0.4)
prev[green] = (0.5, 0.7, 0.2)
prev[mouth] = (0.2, 0.8, 0.9)
prev[violet] = (0.6, 0.3, 0.9)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / f'{BODY}_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
