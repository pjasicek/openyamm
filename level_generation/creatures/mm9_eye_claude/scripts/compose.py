#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the MM9 Eye (CLAUDE_CREATURE_TEXTURES.md; ported from
mm9_lobber_claude/scripts/compose.py). Usage: compose.py
Eye regions (R hide, G eyes, B mouth flesh, A teeth): eyes = the big eyeball and the five stalk eyeballs (fit pieces),
teeth = the other small pieces, mouth = red flesh hues on the body shell (socket rim, lips, mouth), hide = the rest.
On the MM9 skins (256x256, shared UVs): eyes = the two painted eyes (UV discs), mouth = red/pink flesh hues, the rest
hide. Teeth keep their colour in every tier (identity ramps).
Original Lobber notes follow.

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

BODY = 'eye'
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
# Texture-quality pass (2026-10-30): retexture v2 is a 4K Meshy paint on the xatlas UVs of work/uv_v2.blend
# (claude_shared/TEXTURE_QUALITY_PASS.md); v1 was 2K on the Smart UV Project layout.
M = HERE / 'meshy' / 'eye_retexture_v2'
UV3D = HERE / 'work' / f'uv3d_{BODY}_v2.npz'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'eye_a': 'tier1/skins/orbus1.png', 'eye_b': 'tier2/skins/orbus2.png', 'eye_c': 'tier3/skins/orbus3.png'}
TIER_A = next(iter(TIERS))
REGIONS = ('hide', 'eyes', 'mouth', 'teeth')
IDENTITY = {'teeth'}
MAT = 'Eye'


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
tri, f, dbody = raster(UV3D, S, ['limb', 'head'])
covered = tri >= 0
part = np.where(covered, dbody['part'][np.maximum(tri, 0)], -1)


def load_2k(path, mode='RGB'):
    """Meshy's map at 2K: a 4K return is downsampled once (Lanczos), never re-baked."""
    image = Image.open(path).convert(mode)
    if image.size != (2048, 2048):
        image = image.resize((2048, 2048), Image.LANCZOS)
    return np.asarray(image, np.float32) / 255


base2k = load_2k(M / 'texture_urls_0_base_color.png')
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
# Regions are picked from the final colours (the graded texture), never from an earlier paint's mask: the mouth hue below
# reads restore_pebbles.py's output, whose broad colour is the approved one, so reddish patches of the 4K paint are gone.
final = RV.load_srgb(T / f'{BODY}_basecolor_graded.png', S) if (T / f'{BODY}_basecolor_graded.png').exists() else base
h, s, v = hsv(final)
HUES = ((320, 20), (20, 150), (150, 250), (250, 320))  # red/magenta, olive/brown/yellow, teal/blue, violet


def hue_classes(h, covered, sigma):
    """Per-texel hue bin, smoothed (indicator maps blurred, argmax) so scale patterns do not flicker between bins."""
    ind = []
    for lo, hi in HUES:
        m = ((h >= lo) | (h < hi)) if lo > hi else ((h >= lo) & (h < hi))
        ind.append(ndimage.gaussian_filter((m & covered).astype(np.float32), sigma))
    return np.argmax(np.stack(ind), 0)


pc = np.where(covered, part % 10, -1)
limb = f['limb'] > 0.5
eyes = covered & ((pc == 3) | ((pc == 2) & limb))
teeth = covered & (pc == 2) & ~limb
redh = ((h >= 330) | (h < 18)) & (s > 0.35)
redness = ndimage.gaussian_filter((redh & covered).astype(np.float32), 2.0)
# Hysteresis: only solid flesh (at least 300 texels above 0.7) seeds the region, which then grows to the 0.5 edge. Hide hue
# sits next to the 18 degree limit, so a plain threshold on the graded colours spreads flecks of the mouth ramp over the
# hide (227 pieces, pink on tier B, copper on tier C).
weak = (redness > 0.5) & covered & (pc == 0)
seed = (redness > 0.7) & weak
seed_labels, seed_count = ndimage.label(seed, np.ones((3, 3)))
seed_sizes = ndimage.sum(seed, seed_labels, range(1, seed_count + 1))
seed = np.isin(seed_labels, np.nonzero(seed_sizes >= 300)[0] + 1)
mouth = ndimage.binary_propagation(seed, structure=np.ones((3, 3)), mask=weak)
hide = covered & ~eyes & ~teeth & ~mouth
flesh, green, violet = hide, eyes, teeth
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((hide, eyes, mouth, teeth)):
    classes[m] = k + 1
regions = [feather(m, covered) for m in (hide, eyes, mouth, teeth)]
RV.write_mask(regions, T / f'{BODY}_region_mask.png')
Image.fromarray(classes * 80).save(T / f'{BODY}_material_classes.png')
tri2, _, _ = raster(UV3D, 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / f'{BODY}_basecolor.png')
nrm = load_2k(M / 'texture_urls_0_normal.png')
nrm = np.array(Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS))
pebbled = HERE / 'work' / 'normal_pebbled_1k.png'             # restore_pebbles.py: the approved relief on this layout
if pebbled.exists():
    outside = ~(eyes | teeth)                                 # the eye and teeth pieces keep the 4K normal
    nrm[outside] = np.asarray(Image.open(pebbled).convert('RGB'))[outside]
Image.fromarray(nrm).save(T / f'{BODY}_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255            # 4K -> 1K once
rough = np.where(eyes, 0.25, np.where(mouth | teeth, 0.4, np.clip(rough, 0.5, 0.8)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / f'{BODY}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / f'{BODY}_metal_rough_1k.png')

# ---------------- MM9 skin regions (256x256 skins; the same UVs for every tier)
ms = 256
mtri, mf, dmm = raster(HERE / 'work' / f'uv3d_mm9_{BODY}.npz', ms, ['head'])
mcov = mtri >= 0
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
mh, msat, mv = hsv(skins[TIER_A])
yy, xx = np.mgrid[0:ms, 0:ms] / ms
m_eyes = mcov & ((((xx - 0.04) ** 2 + (yy - 0.51) ** 2) < 0.19 ** 2) | (((xx - 0.73) ** 2 + (yy - 0.90) ** 2) < 0.085 ** 2))
m_red = mcov & ~m_eyes & ((mh >= 330) | (mh < 18)) & (msat > 0.35)
m_teeth = np.zeros_like(mcov)
m_hide = mcov & ~m_eyes & ~m_red
mm9_sets = {'hide': m_hide, 'eyes': m_eyes, 'mouth': m_red, 'teeth': m_teeth}
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


kept_path = T / f'{BODY}_kept_ramps.json'                     # the ramps of the approved eye and teeth, tier -> region
kept_ramps = json.load(open(kept_path)) if kept_path.exists() else {}
graded = RV.load_srgb(T / f'{BODY}_basecolor_graded.png', S) if (T / f'{BODY}_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, mm9_sets[name]) if name not in IDENTITY else {k: graded.copy() for k in TIERS}
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        # restore_pebbles.py leaves the eye and teeth texels alone, but a refit reads their gutter fringe and would shift them
        ramps[k].append(kept_ramps[k][name] if name in kept_ramps.get(k, {}) else fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': f'{BODY}_region_mask.png', 'ramps': ramps}]},
          open(T / f'{BODY}_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[hide] = (0.6, 0.45, 0.3)
prev[eyes] = (0.9, 0.9, 0.95)
prev[mouth] = (0.9, 0.2, 0.3)
prev[teeth] = (0.3, 0.8, 0.9)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / f'{BODY}_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
