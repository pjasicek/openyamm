#!/usr/bin/env python3
"""Shared texture set, region mask and per-tier ramps for the Dagrell (CLAUDE_CREATURE_TEXTURES.md; from
mm9_nagate_claude/scripts/compose_nagate.py). Usage: compose_dagrell.py

Inputs: meshy/dagrell_retexture_v4 4K maps (our UVs, texture quality pass 2026-10-30; colour downsampled once to 2K,
normal and roughness to 1K), textures/dagrell_ao_2k.png, work/uv3d_dagrell_v8.npz (texpass_uv3d.py: uv_v5 bind-pose
triangles on the new UVs) and work/uv3d_mm9_dagrell.npz (the grounded MM9 meshes, same space), the three MM9 skins.
Regions: each of our texels is carried in 3D (bind pose) to the nearest point of the MM9 mesh and so to an MM9 skin
texel (one UV layout for all tiers). R bone: everything but the eyes and the spikes; G spikes: texels whose MM9 texel
is red/orange in the tier-2 skin (Venomous and Spectre Dagrell have red-orange spikes and fins, the Dagrell grey);
the eyes (our saturated red texels) keep the base colour. Tier colours as the dragonfly: tier A (DAGRELL1) keeps the
HD look, B (green) and C (blue steel) take chroma by luminance percentile from their skin's region texels.
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
M = HERE / 'meshy' / 'dagrell_retexture_v4'  # texture pass: on the installed uv_v6 mesh, left limbs share the right's texels
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = {'dagrell_a': 'tier1/skins/dagrell1.png', 'dagrell_b': 'tier2/skins/dagrell2.png', 'dagrell_c': 'tier3/skins/dagrell3.png'}
TIER_A = 'dagrell_a'
REGIONS = ('bone', 'spikes')
MAT = 'Dagrell'
ALBEDO_SCALE = 0.7


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
tri, bary, dbody = raster(HERE / 'work' / 'uv3d_dagrell_v8.npz', S)
covered = tri >= 0
tt = np.maximum(tri, 0)
xyz = (dbody['xyz'][tt] * bary[..., :, None]).sum(2)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255
# retexture v2 came back lighter (median 0.34, v1 0.29) than the MM9 charcoal skin and the HD masters (~0.2):
# scale the albedo toward them
base2k = base2k * ALBEDO_SCALE
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
eye = covered & ((h < 20) | (h > 340)) & (s > 0.55) & (v > 0.3)
eye = ndimage.binary_opening(eye, iterations=1)
# the approved v2 paint had no eye texels (the sockets are dark in every tier); the v3 paint has a few red ones, which
# would stay red in every tier: they go through the bone ramps, so the tiers keep the approved look
eye[:] = False

# ---------------- MM9 surface samples with their skin UVs
dm = np.load(HERE / 'work' / 'uv3d_mm9_dagrell.npz')
k = 12
ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
keep = ii + jj <= k
b1, b2 = ii[keep] / k, jj[keep] / k
bw = np.stack([b1, b2, 1 - b1 - b2], -1)
mm_xyz = np.einsum('sk,tkc->tsc', bw, dm['xyz']).reshape(-1, 3)
mm_uv = np.einsum('sk,tkc->tsc', bw, dm['uv']).reshape(-1, 2)
tree = cKDTree(mm_xyz)
tex = covered & ~eye
dist, idx = tree.query(xyz[tex])
uvs = mm_uv[idx]
ux, uy = uvs[:, 0], 1 - uvs[:, 1]
_imgs = {k_: Image.open(HERE / 'source' / p).convert('RGB') for k_, p in TIERS.items()}
ms = max(im.width for im in _imgs.values())
skins = {k_: np.asarray(im.resize((ms, ms), Image.BICUBIC), np.float32) / 255 for k_, im in _imgs.items()}
sh2, ss2, sv2 = hsv(skins['dagrell_b'])
spike_skin = ((sh2 < 40) | (sh2 > 330)) & (ss2 > 0.4) & (sv2 > 0.25)
spike_skin = ndimage.binary_opening(spike_skin, iterations=1)
spike_soft = ndimage.gaussian_filter(spike_skin.astype(np.float32), 1.2 * ms / 256)
in_spike = ndimage.map_coordinates(spike_soft, [uy * ms - 0.5, ux * ms - 0.5], order=1) > 0.45
spikes = np.zeros((S, S), bool)
spikes[tex] = in_spike
bone = covered & ~eye & ~spikes
classes = np.zeros((S, S), np.uint8)
classes[bone] = 1
classes[spikes] = 2
classes[eye] = 3
regions = [feather(m, covered) for m in (bone, spikes)]
RV.write_mask(regions, T / 'dagrell_region_mask.png')
Image.fromarray(classes * 80).save(T / 'dagrell_material_classes.png')

# ---------------- shared maps
tri2, _, _ = raster(HERE / 'work' / 'uv3d_dagrell_v8.npz', 2048)
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'dagrell_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((S, S), Image.LANCZOS))
Image.fromarray(pad(nrm, covered)).save(T / 'dagrell_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
# glossy chitin: wing cases and eyes shinier than the legs
rough = np.where(eye, 0.3, np.clip(rough, 0.45, 0.8))  # dry bone, wet eyes
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'dagrell_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'dagrell_metal_rough_1k.png')

# ---------------- MM9 skin texel sets per region (one shared MM9 UV layout)
covered_mm = np.zeros((ms, ms), bool)
for t in range(len(dm['uv'])):
    for q in np.einsum('sk,kc->sc', bw, dm['uv'][t]):
        covered_mm[np.clip(int((1 - q[1]) * ms), 0, ms - 1), np.clip(int(q[0] * ms), 0, ms - 1)] = True
sh1, ss1, sv1 = hsv(skins[TIER_A])
eye_skin = ((sh1 < 20) | (sh1 > 340)) & (ss1 > 0.55) & (sv1 > 0.3)
eye_skin = ndimage.binary_dilation(eye_skin, iterations=2)
mm9_sets = {
    'bone': {k_: covered_mm & ~spike_skin & ~eye_skin for k_ in TIERS},
    'spikes': {k_: covered_mm & spike_skin for k_ in TIERS},
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


graded = RV.load_srgb(T / 'dagrell_basecolor_graded.png', S) if (T / 'dagrell_basecolor_graded.png').exists() else base
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
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'dagrell_region_mask.png', 'ramps': ramps}]},
          open(T / 'dagrell_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[bone] = (0.6, 0.6, 0.65)
prev[spikes] = (1.0, 0.45, 0.1)
prev[eye] = (0.9, 0.1, 0.2)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k_] for k_ in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'dagrell_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report, 'texels': {
    'bone': int(bone.sum()), 'spikes': int(spikes.sum()), 'eye': int(eye.sum())}}))
