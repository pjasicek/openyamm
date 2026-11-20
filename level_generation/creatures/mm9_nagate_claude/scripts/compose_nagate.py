#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Nagate (CLAUDE_CREATURE_TEXTURES.md; from
mm9_lobber_claude/scripts/compose.py). Usage: compose_nagate.py

Inputs: meshy/nagate_retexture_v2 4K maps (our UVs, texture quality pass 2026-10-30; colour downsampled once to 2K,
normal and roughness to 1K), textures/nagate_ao_2k.png, work/uv3d_nagate_v2.npz (our bind-pose triangles) and work/uv3d_mm9_nagate.npz (the grounded MM9 meshes, same space), the three MM9 skins.
Outputs in textures/: nagate_basecolor.png (2K, gutters padded; graded separately by grade_basecolor.py),
nagate_normal_1k.png, nagate_metal_rough_1k.png (R AO, G roughness, B metallic 0), nagate_material_classes.png,
nagate_region_mask.png, nagate_ramps.json.

Regions (the MM9 tiers differ in their wing-case pattern, so the regions come partly from MM9 itself):
- each of our body texels is carried in 3D (bind pose) to the nearest point of the MM9 mesh and so to an MM9 skin
  texel (all three MM9 skins share one UV layout);
- R wing cases: body texels whose MM9 texel lies in the two elytra panels of the skin, minus the bands;
- A bands: the same, where the tier-2 skin (Nagate) has its orange/red bands (so tier B shows bands, tiers A and C
  repeat their wing-case colour there);
- B claws and mandibles: our gold texels (hue 25-65, saturated) on the legs and mandibles;
- G chitin: everything else; the eyes (piece 2) keep the base colour in every tier.
Tier colours (dragonfly method): tier A keeps the HD look (identity); B and C take hue from their own MM9 skin region
(chroma by luminance percentile), saturation scaled by how much more vivid our A is than MM9's A, brightness by the
MM9 tier/A ratio.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
M = HERE / 'meshy' / 'nagate_retexture_v2'
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'nagate_a': 'tier1/skins/nagate1.png', 'nagate_b': 'tier2/skins/nagate2.png', 'nagate_c': 'tier3/skins/nagate3.png'}
TIER_A = 'nagate_a'
REGIONS = ('wings', 'chitin', 'gold', 'bands')
MAT = 'Nagate'
PANEL = (0.02, 0.04, 0.47, 0.86)  # MM9 skin elytra panels (x0, y0, x1, y1; image coords, top-down)


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


def raster(npz, size):
    """Per texel: triangle id and barycentric weights (rows top-down)."""
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    bary = np.zeros((size, size, 3), np.float32)
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
        bary[rows, cols] = np.stack([l1[inside], l2[inside], l3[inside]], -1)
    return tri, bary, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


# ---------------- our texels (1K): 3D position, part, limb flag
S = 1024
tri, bary, dbody = raster(HERE / 'work' / 'uv3d_nagate_v2.npz', S)
covered = tri >= 0
tt = np.maximum(tri, 0)
xyz = (dbody['xyz'][tt] * bary[..., :, None]).sum(2)
limb = (dbody['limb'][tt] * bary).sum(-1) > 0.5
part = np.where(covered, dbody['part'][tt], -1)
eye = covered & (part % 10 == 2)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)

# ---------------- MM9 surface samples with their skin UVs (dense barycentric samples of every MM9 triangle)
dm = np.load(HERE / 'work' / 'uv3d_mm9_nagate.npz')
k = 12
ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
keep = ii + jj <= k
b1, b2 = ii[keep] / k, jj[keep] / k
bw = np.stack([b1, b2, 1 - b1 - b2], -1)
mm_xyz = np.einsum('sk,tkc->tsc', bw, dm['xyz']).reshape(-1, 3)
mm_uv = np.einsum('sk,tkc->tsc', bw, dm['uv']).reshape(-1, 2)
mm_part = np.repeat(dm['part'] // 10, len(bw))
# our body texels look only at the MM9 body/head meshes (legs etc. are classified separately)
sel = np.isin(mm_part, [1, 2])
tree = cKDTree(mm_xyz[sel])
body_tex = covered & ~limb & ~eye
dist, idx = tree.query(xyz[body_tex])
uvs = mm_uv[sel][idx]
ux, uy = uvs[:, 0], 1 - uvs[:, 1]   # skin image coords, top-down
in_panel = (ux >= PANEL[0]) & (ux <= PANEL[2]) & (uy >= PANEL[1]) & (uy <= PANEL[3])
_imgs = {k_: Image.open(HERE / 'source' / p).convert('RGB') for k_, p in TIERS.items()}
ms = max(im.width for im in _imgs.values())  # tier 1 is 128 px, tiers 2/3 256 px: one common grid
skins = {k_: np.asarray(im.resize((ms, ms), Image.BICUBIC), np.float32) / 255 for k_, im in _imgs.items()}
sh2, ss2, sv2 = hsv(skins['nagate_b'])
band_skin = ((sh2 < 50) | (sh2 > 340)) & (ss2 > 0.45) & (sv2 > 0.35)
yy, xx = np.mgrid[0:ms, 0:ms]
panel_skin = (xx / ms >= PANEL[0]) & (xx / ms <= PANEL[2]) & (yy / ms >= PANEL[1]) & (yy / ms <= PANEL[3])
band_skin &= panel_skin
band_skin = ndimage.binary_opening(band_skin, iterations=1)
px = np.clip((ux * ms).astype(int), 0, ms - 1)
py = np.clip((uy * ms).astype(int), 0, ms - 1)
band_soft = ndimage.gaussian_filter(band_skin.astype(np.float32), 1.2 * ms / 256)
in_band = in_panel & (ndimage.map_coordinates(band_soft, [uy * ms - 0.5, ux * ms - 0.5], order=1) > 0.45)
wings = np.zeros((S, S), bool)
bands = np.zeros((S, S), bool)
wings[body_tex] = in_panel & ~in_band
bands[body_tex] = in_band
gold = covered & ~eye & limb & (h >= 25) & (h <= 65) & (s > 0.4) & (v > 0.25)  # the 4K paint also speckles the belly gold
gold = ndimage.binary_opening(gold, iterations=1)
wings &= ~gold
bands &= ~gold
chitin = covered & ~eye & ~wings & ~bands & ~gold
classes = np.zeros((S, S), np.uint8)
for kk, m in enumerate((wings, chitin, gold, bands)):
    classes[m] = kk + 1
classes[eye] = 5
regions = [feather(m, covered) for m in (wings, chitin, gold, bands)]
RV.write_mask(regions, T / 'nagate_region_mask.png')
Image.fromarray(classes * 50).save(T / 'nagate_material_classes.png')

# ---------------- shared maps
tri2, _, _ = raster(HERE / 'work' / 'uv3d_nagate_v2.npz', 2048)
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'nagate_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((S, S), Image.LANCZOS))
Image.fromarray(pad(nrm, covered)).save(T / 'nagate_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
# glossy chitin: wing cases and eyes shinier than the legs
rough = np.where(eye, 0.3, np.where(wings | bands, np.clip(rough, 0.35, 0.6), np.clip(rough, 0.45, 0.75)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'nagate_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'nagate_metal_rough_1k.png')

# ---------------- MM9 skin texel sets per region (one shared MM9 UV layout)
covered_mm = np.zeros((ms, ms), bool)
for t in range(len(dm['uv'])):
    for q in np.einsum('sk,kc->sc', bw, dm['uv'][t]):
        covered_mm[np.clip(int((1 - q[1]) * ms), 0, ms - 1), np.clip(int(q[0] * ms), 0, ms - 1)] = True
sh1, ss1, sv1 = hsv(skins[TIER_A])
gold_skin = covered_mm & (((xx / ms < 0.22) & (yy / ms > 0.78)) | ((xx / ms > 0.84) & (yy / ms > 0.7)))
eye_skin = covered_mm & (yy / ms > 0.75) & (((xx / ms > 0.3) & (xx / ms < 0.47)) | ((xx / ms > 0.7) & (xx / ms < 0.86)))
mm9_sets = {
    'wings': {k_: panel_skin & covered_mm & ~band_skin for k_ in TIERS},
    'chitin': {k_: covered_mm & ~panel_skin & ~gold_skin & ~eye_skin for k_ in TIERS},
    'gold': {k_: gold_skin for k_ in TIERS},
    # bands: tier B samples its bands; A and C sample their own wing panel (no bands)
    'bands': {'nagate_a': panel_skin & covered_mm, 'nagate_b': band_skin, 'nagate_c': panel_skin & covered_mm},
}
counts = {r: {k_: int(m.sum()) for k_, m in d.items()} for r, d in mm9_sets.items()}


def chroma_targets(graded, weight, masks, region):
    core = weight > 0.5
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size
    ours = lin(graded[core])
    our_sat = float(np.abs(ours / np.maximum(glum, 1e-3)[:, None] - 1).mean())

    def bands_of(k_):
        pal = lin(skins[k_][masks[k_]])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
        return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])

    pal_a, band_a = bands_of(TIER_A)
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.8))
    targets = {TIER_A: graded.copy()}
    for k_ in TIERS:
        if k_ == TIER_A:
            continue
        pal, band = bands_of(k_)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        chroma = 1 + (chroma - 1) * k_sat
        gain = float((pal @ W).mean()) / float((pal_a @ W).mean())
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k_] = tgt
    return targets


graded = RV.load_srgb(T / 'nagate_basecolor_graded.png', S) if (T / 'nagate_basecolor_graded.png').exists() else base
report, ramps = [], {k_: [] for k_ in TIERS}
previews = {k_: graded.copy() for k_ in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, mm9_sets[name], name)
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k_ in TIERS:
        ramps[k_].append(fitted[k_])
        core = weight > 0.5
        previews[k_][core] = targets[k_][core]
    report.append({'region': name, **{k_: v_.get('mean_abs_8bit') if isinstance(v_, dict) else v_
                                      for k_, v_ in rep.items()}})
json.dump({'variants': list(TIERS), 'mm9_region_texels': counts, 'report': report,
           'sources': {k_: f'source/{p}' for k_, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'nagate_region_mask.png', 'ramps': ramps}]},
          open(T / 'nagate_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[wings] = (0.9, 0.3, 0.3)
prev[chitin] = (0.4, 0.4, 0.5)
prev[gold] = (0.9, 0.8, 0.2)
prev[bands] = (1.0, 0.6, 0.1)
prev[eye] = (0.9, 0.1, 0.6)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k_] for k_ in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'nagate_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report, 'texels': {
    'wings': int(wings.sum()), 'bands': int(bands.sum()), 'gold': int(gold.sum()), 'chitin': int(chitin.sum()),
    'eye': int(eye.sum())}}))
