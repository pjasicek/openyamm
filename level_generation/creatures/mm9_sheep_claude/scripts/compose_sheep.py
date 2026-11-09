#!/usr/bin/env python3
"""Shared texture set, region mask and tier ramps for the MM9 sheep body (also used by the ram, whose body is the same
mesh: RAM.abc = SHEEP.abc + horns). Usage: compose_sheep.py

Inputs: meshy/sheep_retexture_v2 maps (4K on our xatlas UVs), textures/sheep_ao_2k.png, work/uv3d_sheep.npz (ours) and
work/uv3d_mm9_sheep.npz (dump_uv3d.py), MM9 skins SHEEP1.dtx (Ewe; Bori and Ratatosk name no skin and MM9 has no
SHEEP.dtx default, so they use it too) and SHEEP2.dtx (the Ram's body).
Outputs in textures/: sheep_basecolor.png (2K, colour downsampled once from Meshy's 4K, gutters padded; graded by
grade_basecolor.py), sheep_normal_1k.png, sheep_metal_rough_1k.png (R AO, G roughness, B 0), sheep_material_classes.png,
sheep_region_mask.png, sheep_ramps.json (variant sheep_a) and ../mm9_ram_claude/textures/ram_ramps.json (ram_a).

Regions (mask channels):
  R wool  - the fleece (everything not below);
  G skin  - the head (face, ears): dark in SHEEP2.dtx;
  B pink  - the inner ears and nose of the skin region (their own ramp, so the ewe keeps the hue);
  A leg   - the skin below KNEE_Z (brown in SHEEP2, the face near black);
  hooves, the painted eyes and the mouth cavity stay out of the mask (the same in every tier).
Painted here, not by Meshy: the mouth cavity (pink lips to a near-black throat, a lighter tongue ridge), which Meshy cannot see in the masters.
Tier colours (wolf method): tier A (sheep1) keeps the HD look (identity ramps); the ram takes hue and brightness from
SHEEP2 per region (chroma by luminance percentile, brightness by the MM9 sheep2/sheep1 ratio).
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent.parent
RAM = HERE.parent / 'mm9_ram_claude'
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

T = HERE / 'textures'
T.mkdir(exist_ok=True)
M = HERE / 'meshy' / 'sheep_retexture_v2'
W = np.array([0.2126, 0.7152, 0.0722])
SKINS = {'sheep_a': HERE / 'source/sheep1/skins/sheep1.png', 'ram_a': HERE / 'source/sheep2/skins/sheep2.png'}
TIER_A = 'sheep_a'
REGIONS = ('wool', 'skin', 'pink', 'leg')
HOOF_Z = 0.045         # model units above the floor (bind): the hooves
KNEE_Z = 0.29         # the dark legs end here


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
    out = {}
    ti = np.maximum(tri, 0)
    for f in fields:
        v = d[f][ti]                      # (S, S, 3[, k])
        out[f] = (bary[..., :, None] * v).sum(-2) if v.ndim == 4 else (bary * v).sum(-1)
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered, sigma=1.0):
    m = pad(m.astype(np.float32), covered)
    return ndimage.gaussian_filter(m, sigma)


# ---------------- our texels (1K for classes, 2K for colour)
S = 1024
tri, f, dbody = raster(HERE / 'work' / 'uv3d_sheep.npz', S, ['xyz', 'head'])
covered = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(covered, dbody['part'][ti], -1)
cav = covered & (dbody['cavity'][ti] == 1)
xyz = f['xyz']
# Meshy paints the eye (with lids) on the head surface; this paint's iris came out grey, so the iris texels (found from
# the first paint's amber, EYE_C) are tinted to MM9's amber below and stay out of the mask in every tier
mbase = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
hsv_h, hsv_s, hsv_v = hsv(mbase)
EYE_C = np.array([0.0585, -0.573, 0.893])
EYE_R = 0.0105


def eye_dist(p):
    return np.linalg.norm(np.abs(p) * np.array([1, 0, 0]) + p * np.array([0, 1, 1]) - EYE_C, axis=-1)


eyes = covered & (eye_dist(xyz) < EYE_R * 1.5)
hoof = covered & ~eyes & ~cav & (xyz[..., 2] < HOOF_Z + 0.012) & (hsv_v < 0.42)
hoof = ndimage.binary_closing(hoof, iterations=2) & covered & ~eyes & ~cav
# ---------------- MM9: sample both skins at the nearest MM9 surface point of every texel
dm = np.load(HERE / 'work' / 'uv3d_mm9_sheep.npz')
rng = np.random.default_rng(1)
pts, uvs = [], []
for t in range(len(dm['xyz'])):
    a, b, c = dm['xyz'][t], dm['uv'][t], None
    r = rng.random((24, 2))
    r[r.sum(1) > 1] = 1 - r[r.sum(1) > 1]
    w = np.c_[1 - r.sum(1), r]
    pts.append(w @ dm['xyz'][t]); uvs.append(w @ dm['uv'][t])
pts, uvs = np.concatenate(pts), np.concatenate(uvs)
skins = {k: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255 for k, p in SKINS.items()}
ms = skins[TIER_A].shape[0]


def sample(img, uv):
    x = np.clip((uv[:, 0] % 1) * ms, 0, ms - 1).astype(int)
    y = np.clip((1 - uv[:, 1] % 1) * ms, 0, ms - 1).astype(int)
    return img[y, x]


# SHEEP2 paints the whole head and the legs below the belly dark. The MM9 surface sampling of that pattern is noisy on
# our differently shaped ears and fetlocks (pale specks), so the pattern is the anatomy: head bones, and legs below
# KNEE_Z with a slightly wavy hairline; both MM9 skins' colours still drive the ramps below.
wave = ndimage.gaussian_filter(np.random.default_rng(3).normal(size=(S, S)), 9)
wave = wave / np.abs(wave).max() * 0.018
allowed = covered & ~eyes & ~cav & ~hoof
on_leg = ((xyz[..., 1] < -0.13) | (xyz[..., 1] > 0.37)) & (np.abs(xyz[..., 0]) > 0.055) | (xyz[..., 2] < 0.2)
skin = allowed & ((f['head'] > 0.5) | ((xyz[..., 2] + wave < KNEE_Z) & on_leg))
wool = covered & ~(skin | eyes | cav | hoof)
# the pink of the inner ears and nose keeps its hue in the ewe: a region of its own (the ram's is dark like its face)
pink = skin & ((hsv_h < 18) | (hsv_h > 335)) & (hsv_s > 0.13)
pink = ndimage.binary_closing(pink, iterations=2) & skin
skin = skin & ~pink
leg = skin & (f['head'] <= 0.5)
skin = skin & ~leg
keep = ~(eyes | cav | hoof)
regions = [feather(wool, covered, 1.0) * keep, feather(skin, covered, 1.0) * keep, feather(pink, covered, 1.0) * keep,
           feather(leg, covered, 1.0) * keep]
RV.write_mask(regions, T / 'sheep_region_mask.png')
classes = np.zeros((S, S), np.uint8)
classes[wool] = 2; classes[skin] = 1; classes[pink] = 1; classes[leg] = 1; classes[hoof] = 4; classes[eyes] = 6; classes[cav] = 7
Image.fromarray(classes).save(T / 'sheep_material_classes.png')

# ---------------- base colour 2K: Meshy 4K downsampled once, eyes and mouth painted
S2 = 2048
tri2, f2, _ = raster(HERE / 'work' / 'uv3d_sheep.npz', S2, ['xyz'])
cov2 = tri2 >= 0
ti2 = np.maximum(tri2, 0)
part2 = np.where(cov2, dbody['part'][ti2], -1)
cav2 = cov2 & (dbody['cavity'][ti2] == 1)
src = Image.open(M / 'texture_urls_0_base_color.png').convert('RGB')
src_size = src.size
base = np.asarray(src.resize((S2, S2), Image.LANCZOS), np.float32) / 255
p2 = f2['xyz']
# iris: centred on the paint's own pupil (the darkest texels near EYE_C, per side), its luminance kept (pupil,
# catchlight, lid shadow), amber hue from SHEEP1
lum_e = base @ np.array([0.2126, 0.7152, 0.0722])
amber = np.array([0.72, 0.46, 0.16])
w_eye = np.zeros((S2, S2), np.float32)
eye_c = {}
for sx in (1, -1):
    near = cov2 & (sx * p2[..., 0] > 0) & (eye_dist(p2) < 0.024)
    pupil = near & (lum_e < np.percentile(lum_e[near], 12))
    c = np.median(p2[pupil], axis=0)
    eye_c[sx] = c.round(4).tolist()
    ed = np.linalg.norm(p2 - c, axis=-1)
    w_eye = np.maximum(w_eye, (near & (ed < EYE_R)) * np.clip((EYE_R - ed) / 0.003, 0, 1))
base = base * (1 - w_eye[..., None]) + (amber * np.clip(lum_e * 1.7, 0.03, 1.0)[..., None]) * w_eye[..., None]
base = np.clip(base, 0, 1)
print('EYE_CENTRES', eye_c)
# mouth cavity: pink lips -> dark throat, tongue lighter
if cav2.any():
    q = p2[cav2]
    depth = np.clip((q[:, 1] - (-0.700)) / (-0.628 + 0.700), 0, 1)
    lower = q[:, 2] < 0.779 + 0.09 * (q[:, 1] + 0.70)
    lip = np.array([0.46, 0.27, 0.27]); throat = np.array([0.07, 0.03, 0.03]); tongue = np.array([0.55, 0.30, 0.31])
    t = depth[:, None] ** 0.8
    col = lip * (1 - t) + throat * t
    col[lower] = (tongue * (1 - t) + throat * t)[lower]
    noise = rng.normal(0, 0.012, col.shape)
    base[cav2] = np.clip(col + noise, 0, 1)
base = pad(base, cov2)
Image.fromarray((base * 255).astype(np.uint8)).save(T / 'sheep_basecolor.png')
nrm = Image.open(M / 'texture_urls_0_normal.png').convert('RGB')
nrm = np.asarray(nrm.resize((S2, S2), Image.LANCZOS), np.float32) / 255
nrm[cav2] = (0.5, 0.5, 1.0)
Image.fromarray((pad(nrm, cov2) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'sheep_normal_1k.png')
rough = np.full((S, S), 0.85, np.float32)
rough[skin] = 0.72; rough[pink] = 0.72; rough[leg] = 0.72; rough[hoof] = 0.5; rough[eyes] = 0.18; rough[cav] = 0.4
rough = pad(ndimage.gaussian_filter(rough, 0.7), covered)
aop = T / 'sheep_ao_2k.png'
ao = np.asarray(Image.open(aop).convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255 if aop.exists() \
    else np.ones((S, S), np.float32)
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'sheep_metal_rough_1k.png')

# ---------------- ramps: MM9 regions on the MM9 skin itself (both skins share MM9's UVs)
mlum1 = lin(skins['sheep_a']) @ W
mlum2 = lin(skins['ram_a']) @ W
mtri, mf, _ = raster(HERE / 'work' / 'uv3d_mm9_sheep.npz', ms, ['xyz', 'head'])
mcov = mtri >= 0
m_dark = mcov & (mlum2 / np.maximum(mlum1, 1e-3) < 0.45)
m_eye = mcov & (skins['sheep_a'][..., 0] - skins['sheep_a'][..., 2] > 0.35) & (mf['head'] > 0.5)
m_head = mf['head'] > 0.5
mm9_sets = {'skin': m_dark & ~m_eye & m_head, 'wool': mcov & ~m_dark & ~m_eye, 'pink': m_dark & ~m_eye & m_head,
            'leg': m_dark & ~m_head}
counts = {k: int(v.sum()) for k, v in mm9_sets.items()}


def chroma_targets(graded, weight, name):
    core = weight > 0.5
    targets = {TIER_A: graded.copy()}
    mm9_mask = mm9_sets[name]
    glum = lin(graded[core]) @ W
    rank = np.empty(glum.size)
    rank[np.argsort(glum)] = (np.arange(glum.size) + 0.5) / glum.size

    def bands(k):
        pal = lin(skins[k][mm9_mask])
        pal = pal[np.argsort(pal @ W)]
        mid = pal[int(0.10 * len(pal)):int(0.95 * len(pal))]
        return pal, np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 6)])

    for k in SKINS:
        if k == TIER_A:
            continue
        pal_a, _ = bands(TIER_A) if name == 'wool' else (lin(skins[TIER_A][mm9_mask]), None)
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        # brightness by the MM9 tier/A ratio of this region (the ram's face is near black, its wool as the ewe's)
        gain = float((pal @ W).mean()) / max(float((pal_a @ W).mean()), 1e-4)
        if name != 'wool':     # near black in MM9: absolute albedo (1.35 x the skin mean), not a ratio to our pale face
            gain = (0.6 if name == 'leg' else 1.2) * float((pal @ W).mean()) / max(float(glum.mean()), 1e-4)
        tgt = graded.copy()
        tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'sheep_basecolor_graded.png', S) if (T / 'sheep_basecolor_graded.png').exists() else \
    np.asarray(Image.fromarray((base * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float64) / 255
report, ramps = [], {k: [] for k in SKINS}
previews = {k: graded.copy() for k in SKINS}
for name, weight in zip(REGIONS, regions):
    targets = chroma_targets(graded, weight, name)
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in SKINS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': ['sheep_a'], 'mm9_region_texels': counts, 'report': report,
           'sources': {'sheep_a': 'source/sheep1/skins/sheep1.png (SHEEP1.dtx)'},
           'materials': [{'base': 'Sheep', 'prefix': 'Sheep', 'mask': 'sheep_region_mask.png',
                          'ramps': {'sheep_a': ramps['sheep_a']}}]},
          open(T / 'sheep_ramps.json', 'w'), indent=1)
(RAM / 'textures').mkdir(parents=True, exist_ok=True)
json.dump({'variants': ['ram_a'], 'mm9_region_texels': counts, 'report': report,
           'sources': {'ram_a': '../mm9_sheep_claude/source/sheep2/skins/sheep2.png (SHEEP2.dtx)'},
           'materials': [{'base': 'Ram', 'prefix': 'Ram', 'mask': '../../mm9_sheep_claude/textures/sheep_region_mask.png',
                          'ramps': {'ram_a': ramps['ram_a']}}]},
          open(RAM / 'textures' / 'ram_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[wool] = (0.85, 0.85, 0.8); prev[skin] = (0.4, 0.25, 0.2); prev[pink] = (0.9, 0.5, 0.6); prev[leg] = (0.3, 0.3, 0.2); prev[hoof] = (0.2, 0.2, 0.9)
prev[eyes] = (1.0, 0.8, 0.1); prev[cav] = (0.9, 0.3, 0.4)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in SKINS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'sheep_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'meshy_size': src_size, 'mm9_texels': counts, 'fit': report,
                              'our_texels': {k: int(m.sum()) for k, m in
                                             zip(('wool', 'skin', 'hoof', 'eyes', 'cavity'), (wool, skin, hoof, eyes, cav))}}))
