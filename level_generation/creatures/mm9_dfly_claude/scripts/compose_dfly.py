#!/usr/bin/env python3
"""Shared texture set, region masks and per-tier ramps for the dragonfly (CLAUDE_CREATURE_TEXTURES.md).

Inputs: meshy/retexture_v1 maps (body, our UVs), textures/dfly_ao_2k.png, textures/dfly_wing_basecolor_src_v2.png and
work/wing_alpha_v2.png (compose_wing_v2.py, texture quality pass 2026-10-30; v1: dfly_wing_basecolor_src.png),
work/uv3d_body.npz and work/uv3d_mm9.npz (dump_uv3d.py), the three MM9 skins.
Outputs in textures/:
  dfly_basecolor.png (2K, gutters padded) -> graded separately by ../claude_shared/grade_basecolor.py
  dfly_normal_1k.png, dfly_metal_rough_1k.png (R AO, G roughness, B metallic 0), dfly_material_classes.png
  dfly_region_mask.png (R scales, G belly, B eyes, A mouth), dfly_wing_region_mask.png (R membrane)
  dfly_wing_basecolor.png, dfly_wing_metal_rough.png, dfly_ramps.json (both materials, tiers dfly_a/b/c)
Tier colours: the region texels of each MM9 skin (dragonfly1 Mite, dragonfly2 Dragonfly, dragonfly3 Fire Dragonfly),
chroma by luminance percentile, brightness from our texel scaled to the MM9 region mean x ALBEDO (compose_seas.py
method), fitted with region_variants.fit_ramps.
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
M = HERE / 'meshy' / 'retexture_v1'
W = np.array([0.2126, 0.7152, 0.0722])
ALBEDO = 1.2
TIERS = {'dfly_a': 1, 'dfly_b': 2, 'dfly_c': 3}


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
    """Per-texel triangle index (-1 empty) and barycentric-interpolated per-vertex fields."""
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    out = {f: np.zeros((size, size) + d[f].shape[2:], np.float32) for f in fields}
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = int(np.floor(p[:, 0].min())), int(np.ceil(p[:, 0].max()))
        y0, y1 = int(np.floor(p[:, 1].min())), int(np.ceil(p[:, 1].max()))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
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
        rows = size - 1 - (iy + y0)  # image row 0 is v = 1
        cols = ix + x0
        tri[rows, cols] = t
        for f in fields:
            v = d[f][t]
            out[f][rows, cols] = (l1[inside, None] * v[0] + l2[inside, None] * v[1] + l3[inside, None] * v[2]
                                  ).reshape((-1,) + v.shape[1:])
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


# ---------------- body texel classes (1K)
S = 1024
tri, f, dbody = raster(HERE / 'work' / 'uv3d_body.npz', S, ['xyz', 'head'])
covered = tri >= 0
part = np.where(covered, dbody['part'][np.maximum(tri, 0)], -1)
head = f['head'][..., 0] if f['head'].ndim == 3 else f['head']
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'), np.float32) / 255
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
eye = covered & (part == 1)
pinkred = ((h >= 325) | (h < 25)) & (s > 0.35)
tooth = covered & (part == 2) & ~pinkred                            # teeth; the jaw/tongue piece is mouth below
skin = covered & (part == 0)
spike = skin & (h > 35) & (h < 95) & (s > 0.25)                      # yellow-green tail needle
mouth = ((skin & (head > 0.5)) | (covered & (part == 2))) & pinkred
belly = skin & ~mouth & ~spike & (h >= 255) & (h < 335) & (s > 0.2)
scales = skin & ~mouth & ~spike & ~belly
classes = np.zeros((S, S), np.uint8)
classes[skin] = 1
classes[spike] = 4
classes[tooth] = 5
classes[eye] = 6
classes[mouth] = 7
regions = [feather(m, covered) for m in (scales, belly, eye, mouth)]
RV.write_mask(regions, T / 'dfly_region_mask.png')
Image.fromarray(classes).save(T / 'dfly_material_classes.png')

# base colour 2K: pad the gutters
tri2, _, _ = raster(HERE / 'work' / 'uv3d_body.npz', 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'dfly_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'), np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'dfly_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(eye, 0.2, np.where(tooth | spike, 0.4, np.maximum(rough, 0.55)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'dfly_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'dfly_metal_rough_1k.png')

# ---------------- wing texture (1K, from the HD top view; re-projected into the wing_uv_v2.py layout since 2026-10-30)
wing_rgb = np.asarray(Image.open(T / 'dfly_wing_basecolor_src_v2.png').convert('RGB'), np.float32) / 255
wing_alpha = np.asarray(Image.open(HERE / 'work' / 'wing_alpha_v2.png').convert('L'), np.float32) / 255 > 0.5
Image.fromarray((wing_rgb * 255).astype(np.uint8)).save(T / 'dfly_wing_basecolor.png')
wing_region = feather(wing_alpha, wing_alpha)
RV.write_mask([wing_region], T / 'dfly_wing_region_mask.png')
Image.merge('RGB', [Image.new('L', (S, S), 255), Image.new('L', (S, S), 150), Image.new('L', (S, S), 0)]).save(
    T / 'dfly_wing_metal_rough.png')

# ---------------- MM9 skin regions (texels of the original 128x128 skins, same UVs for all tiers)
ms = 128
mtri, mf, dmm = raster(HERE / 'work' / 'uv3d_mm9.npz', ms, ['xyz'])
mcov = mtri >= 0
mpart = np.where(mcov, dmm['part'][np.maximum(mtri, 0)], -1)
xyz = mf['xyz']
skins = {k: np.asarray(Image.open(HERE / 'source' / f'tier{t}' / 'skins' / f'dragonfly{t}.png').convert('RGB'),
                       np.float32) / 255 for k, t in TIERS.items()}
mh, msat, mv = hsv(skins['dfly_a'])
m_wing = mcov & (mpart == 20)
m_body = mcov & (mpart == 10)
m_headzone = m_body & (xyz[..., 1] < -0.17)
m_eye = m_headzone & (np.abs(xyz[..., 0]) > 0.05) & (xyz[..., 2] > 0.165) & (mv < 0.25)
m_mouth = m_headzone & ~m_eye & ((mh >= 300) | (mh < 30)) & (msat > 0.3)
m_belly = m_body & ~m_eye & ~m_mouth & (mh >= 250) & (mh < 320) & (msat > 0.2)
m_scales = m_body & ~m_eye & ~m_mouth & ~m_belly & (mv > 0.08)
mm9_sets = {'scales': m_scales, 'belly': m_belly, 'eye': m_eye, 'mouth': m_mouth, 'wing': m_wing}
counts = {k: int(m.sum()) for k, m in mm9_sets.items()}


def chroma_targets(graded, weight, mm9_mask, absolute=False):
    """Tier A keeps the HD (Meshy) look: its target is the base itself. Tiers B/C take hue from their own MM9 skin
    (chroma by luminance percentile, 15th-95th, in bands), saturation scaled by how much more vivid our A region is
    than MM9's A region, and brightness = our texel x (MM9 tier mean / MM9 A mean). absolute: the MM9 tier colour
    itself at the texel's percentile (eyes: black A to amber B, no usable brightness ratio)."""
    core = weight > 0.5
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

    pal_a, band_a = bands('dfly_a')
    k_sat = float(np.clip(our_sat / max(float(np.abs(band_a - 1).mean()), 1e-3), 0.8, 1.8))
    targets = {'dfly_a': graded.copy()}
    for k in TIERS:
        if k == 'dfly_a':
            continue
        pal, band = bands(k)
        x = np.clip(rank, 0, 1) * (len(band) - 1)
        i0 = np.minimum(x.astype(int), len(band) - 2)
        fr = (x - i0)[:, None]
        chroma = band[i0] * (1 - fr) + band[i0 + 1] * fr
        tgt = graded.copy()
        if absolute:
            q = pal[np.minimum((rank * len(pal)).astype(int), len(pal) - 1)] * ALBEDO
            tgt[core] = encode(np.clip(q, 0, 1))
        else:
            chroma = 1 + (chroma - 1) * k_sat
            gain = float((pal @ W).mean()) / float((pal_a @ W).mean())
            tgt[core] = encode(np.clip(chroma * (glum * gain)[:, None], 0, 1))
        targets[k] = tgt
    return targets


graded = RV.load_srgb(T / 'dfly_basecolor_graded.png', S) if (T / 'dfly_basecolor_graded.png').exists() else base
report, body_ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(('scales', 'belly', 'eye', 'mouth'), regions):
    targets = chroma_targets(graded, weight, mm9_sets[name], absolute=(name == 'eye'))
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        body_ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v
                                      for k, v in rep.items()}})
wtargets = chroma_targets(wing_rgb.astype(np.float64), wing_region, m_wing)
wfit, wrep = RV.fit_ramps(wing_rgb.astype(np.float64), wtargets, wing_region)
report.append({'region': 'wing', **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in wrep.items()}})
json.dump({'variants': list(TIERS), 'albedo': ALBEDO, 'mm9_region_texels': counts, 'report': report,
           'sources': {k: f'source/tier{t}/skins/dragonfly{t}.png (mm9/extracted/SKINS/SKINS/DRAGONFLY{t}.dtx)'
                       for k, t in TIERS.items()},
           'materials': [{'base': 'Dfly', 'prefix': 'Dfly', 'mask': 'dfly_region_mask.png', 'ramps': body_ramps},
                         {'base': 'Dfly_Wing', 'prefix': 'DflyWing', 'mask': 'dfly_wing_region_mask.png',
                          'ramps': json.load(open(T / 'dfly_wing_ramps_pin.json'))['ramps']}]},
          open(T / 'dfly_ramps.json', 'w'), indent=1)
# review: class map and the three tier targets
prev = np.zeros((S, S, 3))
prev[scales] = (0.2, 0.3, 0.8)
prev[belly] = (0.8, 0.3, 0.8)
prev[eye] = (1, 1, 1)
prev[mouth] = (1, 0.1, 0.1)
prev[tooth] = (1, 1, 0.6)
prev[spike] = (0.6, 0.9, 0.2)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((2048, 512)).save(
    HERE / 'review' / 'texture_classes_tiers.png')
print('COMPOSED', json.dumps({'mm9_texels': counts, 'fit': report}))
