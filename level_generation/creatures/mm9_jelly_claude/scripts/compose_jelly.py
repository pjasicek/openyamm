#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Jellyspore (CLAUDE_CREATURE_TEXTURES.md; from
mm9_lobber_claude/scripts/compose.py, regions by part instead of hue). Usage: compose_jelly.py

Regions (structural): R the bell (both shells), G the 'red joints' (collar, collar rings, leg roots, lower stinger:
red in tiers B/C), B the rest of the legs, A stalk/upper stinger/spikes. Tier colours per region come from the MM9
skins projected onto our texels through the fitted bind pose (nearest MM9 surface point):
A JELLYSPORE1 (Jellyspore), B JELLYSPORE2 (Gelatinous Spore), C the mean of the eight NettleSpore.spr frames
(JELLYSPOREBANI1-8, an animated skin; the flicker itself is not reproduced).

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

BODY = 'jelly'
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / f'{BODY}_retexture_v1'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'jelly_a': 'tier1/skins/jelly1.png', 'jelly_b': 'tier2/skins/jelly2.png', 'jelly_c': 'nettle_mean.png'}
TIER_A = next(iter(TIERS))
REGIONS = ('bell', 'red', 'legs', 'stinger')
MAT = 'Jelly'


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


tri_c = np.maximum(tri, 0)
chain_t = dbody['chain'][tri_c]
comp_t = dbody['comp'][tri_c]
zc = dbody['xyz'].mean(1)[:, 2]
shells = [c for c in np.unique(dbody['comp']) if (dbody['comp'] == c).sum() > 300 and
          zc[dbody['comp'] == c].mean() > 0.25 and (dbody['chain'][dbody['comp'] == c] < 0).all()]
# per-texel bind position and 'red' group weight (collar, leg roots, lower stinger: the red joints of tiers B/C)
tmp = HERE / 'work' / 'uv3d_jelly_fields.npz'
np.savez(tmp, **{k: dbody[k] for k in dbody.files}, px=dbody['xyz'][..., 0], py=dbody['xyz'][..., 1],
         pz=dbody['xyz'][..., 2])
_, fx, _ = raster(tmp, S, ['px', 'py', 'pz', 'grp'])
bellm = covered & np.isin(comp_t, shells)
red = covered & ~bellm & (fx['grp'] > 0.5)
legs = covered & ~bellm & ~red & (chain_t >= 0) & (chain_t <= 3)
stinger = covered & ~bellm & ~red & ~legs
flesh, green, mouth, violet = bellm, red, legs, stinger
classes = np.zeros((S, S), np.uint8)
for k, m in enumerate((flesh, green, mouth, violet)):  # bell, red joints, legs, stinger
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
rough = np.where(flesh, np.clip(rough, 0.25, 0.5), np.clip(rough, 0.35, 0.6))  # glossy jelly
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / f'{BODY}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / f'{BODY}_metal_rough_1k.png')

# ---------------- MM9 tier colours on our texels: every texel's bind position takes the colour of the nearest point
# of the MM9 model's surface (our mesh is fitted to the MM9 bind pose), sampled in each tier's MM9 skin. Only colour
# statistics per region are taken from it (bands below); the mask stays structural.
from scipy.spatial import cKDTree
dmm = np.load(HERE / 'work' / f'uv3d_mm9_{BODY}.npz')
rng = np.random.default_rng(0)
pts, uvs = [], []
for t in range(len(dmm['xyz'])):
    X, U = dmm['xyz'][t], dmm['uv'][t]
    area = 0.5 * np.linalg.norm(np.cross(X[1] - X[0], X[2] - X[0]))
    n = max(8, int(area * 4e5))
    r = rng.random((n, 2)); flip = r.sum(1) > 1; r[flip] = 1 - r[flip]
    w = np.column_stack([1 - r.sum(1), r])
    pts.append(w @ X); uvs.append(w @ U)
pts, uvs = np.concatenate(pts), np.concatenate(uvs)
P3 = np.stack([fx['px'], fx['py'], fx['pz']], -1)[covered]
_, nn = cKDTree(pts).query(P3)
muv = uvs[nn]
ms = 256
col = np.clip((muv[:, 0] * ms).astype(int), 0, ms - 1)
row = np.clip(((1 - muv[:, 1]) * ms).astype(int), 0, ms - 1)
mean_nettle = np.mean([np.asarray(Image.open(HERE / 'work' / 'nettle_frames' / f'f{k}.png').convert('RGB'),
                               np.float32) for k in range(1, 9)], 0)
Image.fromarray(mean_nettle.astype(np.uint8)).save(HERE / 'source' / 'nettle_mean.png')
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
proj = {}
for k in TIERS:
    img = np.zeros((S, S, 3), np.float32)
    img[covered] = skins[k][row, col]
    proj[k] = img
Image.fromarray((np.concatenate([proj[k] for k in TIERS], 1) * 255).astype(np.uint8)).save(
    HERE / 'work' / 'mm9_projected_tiers.png')
mm9_sets = {'bell': flesh, 'red': green, 'legs': mouth, 'stinger': violet}
# the bell takes its tier colours from the MM9 bell's own upward faces in each skin (our bell sits lower than MM9's,
# so its nearest MM9 points mix in the rim and underside)
mtri, _, _ = raster(HERE / 'work' / f'uv3d_mm9_{BODY}.npz', ms, [])
mbell = (mtri >= 0) & (dmm['part'][np.maximum(mtri, 0)] // 10 == 1) & (dmm['normal'][np.maximum(mtri, 0)][..., 2] > 0.3)
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, mm9_mask):
    core = weight > 0.5
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands(k):
        pal = lin(skins[k][mbell]) if mm9_mask is flesh else lin(proj[k][mm9_mask & (weight > 0.5)])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        out = []
        for b in np.array_split(mid, 6):
            c = b / np.maximum(b @ W, 1e-3)[:, None]
            m = c.mean(0)
            # multi-hue skins (the iridescent bell: purple darks, lavender-blue mids, teal lights) average toward
            # grey: keep each luminance band's mean hue but restore the texels' own mean saturation
            dev = m - 1
            target = 1.0 * float(np.linalg.norm(c - 1, axis=1).mean())
            n = float(np.linalg.norm(dev))
            out.append(1 + dev * (max(target, n) / max(n, 1e-6)) if n > 1e-6 else m)
        return pal, np.array(out)

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
prev[flesh] = (0.2, 0.8, 0.7)
prev[green] = (0.9, 0.2, 0.2)
prev[mouth] = (0.6, 0.8, 0.2)
prev[violet] = (0.2, 0.4, 0.9)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / f'{BODY}_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
