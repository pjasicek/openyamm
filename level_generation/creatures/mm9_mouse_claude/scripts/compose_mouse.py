#!/usr/bin/env python3
"""Shared texture set, region mask and ramps for the MM9 mouse (rows 299 mouse, 300 evil mouse; ported from
mm9_crow_claude/scripts/compose_crow.py). Usage: compose_mouse.py

MM9 names mouse1.dtx (mouse) and mouse3.dtx (evil mouse) but ships neither skin (no MOUSE*.dtx anywhere in the game
data; MOUSE.abc is also never placed in a DAT world), so there is no MM9 colour to measure. Tier A keeps the HD
master look (a grey-brown house mouse, identity ramps). Tier C, the evil mouse, is our design in the spirit of the
"mouse C" row: a sooty charcoal coat, dusky grey-pink skin and red eyes (the same body; MONSTERS.txt gives it
Special 1 and 2D4 instead of 2D3, nothing else). Regions:
  R fur   - every texel outside the others;
  G skin  - the naked tail (past its furred root), the paws, and pink texels (inner ears, nose, lips);
  B eyes  - the two eye beads.
Outputs in textures/: mouse_basecolor.png (2K, padded; graded by grade_basecolor.py), mouse_normal_1k.png,
mouse_metal_rough_1k.png (R AO, G roughness, B metallic 0), mouse_material_classes.png, mouse_region_mask.png,
mouse_ramps.json; review/mouse_texture_classes_tiers.png.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
sys.path.insert(0, str(HERE / 'scripts'))
import fur_detail

T = HERE / 'textures'
M = HERE / 'meshy' / 'mouse_retexture_v1'   # 4K paint on the xatlas UVs
W = np.array([0.2126, 0.7152, 0.0722])
TIERS = ('mouse_a', 'mouse_c')
REGIONS = ('fur', 'skin', 'eyes')
MAT = 'Mouse'


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
tri, f, dbody = raster(HERE / 'work' / 'uv3d_mouse.npz', S, ['tail_t', 'leg', 'head'])
covered = tri >= 0
ti = np.maximum(tri, 0)
part = np.where(covered, dbody['part'][ti], -1)
base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                    np.float32) / 255   # 4K -> 2K once (the creature cook caps colour at 2048)
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s_, v = hsv(np.asarray(Image.fromarray((base * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)),
                          np.float32) / 255)   # (blurred: the ripple's dark lines must not cut the pink regions up)
eyes = covered & (part == 1)
pink = (((h < 22) | (h > 330)) & (s_ > 0.2) & (v > 0.4))
pink = ndimage.binary_closing(ndimage.binary_opening(pink, iterations=2), iterations=3)
lab, n = ndimage.label(pink)
pink &= np.isin(lab, np.nonzero(ndimage.sum(pink, lab, range(1, n + 1)) >= 300)[0] + 1)   # no specks on the fur
pink = ndimage.binary_fill_holes(pink)
# the nose: only its tip is bare (Meshy painted the whole end chart pink, a hard patch on the muzzle)
tri0, _, d0 = tri, None, dbody
cen = np.where(covered[..., None], d0['xyz'].mean(1)[ti], 0)
NOSE = np.array([0.0, -0.1116, 0.0105])
muzzle = cen[..., 1] < -0.098
pink &= ~(muzzle & (np.linalg.norm(cen - NOSE, axis=-1) > 0.0045))
skin = covered & ~eyes & ((f['tail_t'] > 0.13) | (f['leg'] > 0.5) | (pink & (f['tail_t'] < 0)))
fur = covered & ~(eyes | skin)
classes = np.zeros((S, S), np.uint8)
classes[fur] = 2
classes[skin] = 1
classes[eyes] = 6
regions = [feather(m, covered) for m in (fur, skin, eyes)]
# the tail's fur root fades out along the tail instead of ending in a line
fade = np.clip((f['tail_t'] - 0.10) / 0.06, 0, 1)
on_tail = covered & (f['tail_t'] >= 0)
regions[1] = np.where(on_tail, fade, regions[1]).astype(np.float32)
regions[0] = np.where(on_tail, 1 - fade, regions[0]).astype(np.float32)
RV.write_mask(regions, T / 'mouse_region_mask.png')
Image.fromarray(classes).save(T / 'mouse_material_classes.png')
tri2, f2, d2 = raster(HERE / 'work' / 'uv3d_mouse.npz', 2048, ['tail_t', 'leg'])
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                 np.float32) / 255
# fur: Meshy's colours, our hair strokes (fur_detail.py); the 2K masks come from the 1K classes
# (classes padded first, so island borders the 1K raster missed do not keep the raw ripple as pale stitches)
cls2 = np.asarray(Image.fromarray(pad(classes, covered)).resize((2048, 2048), Image.NEAREST))
ear2 = (cls2 == 1) & (tri2 >= 0) & (f2['tail_t'] < 0) & (f2['leg'] < 0.5)
fur2 = (cls2 == 2) & (tri2 >= 0)
base2k, nrm = fur_detail.apply(base2k, nrm, tri2, d2, fur2, ear2, None)
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / 'mouse_basecolor.png')
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(
    T / 'mouse_normal_1k.png')
rough = np.where(fur, 0.78, np.where(skin, 0.55, np.where(eyes, 0.15, 0.7)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / 'mouse_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'mouse_metal_rough_1k.png')


# ---------------- tier C targets (evil mouse: our design, no MM9 skin exists)
def rank_of(lum):
    r = np.empty(lum.size)
    r[np.argsort(lum)] = (np.arange(lum.size) + 0.5) / lum.size
    return r


def targets_for(graded, weight, name):
    core = weight > 0.5
    out = {'mouse_a': graded.copy()}
    tgt = graded.copy()
    lin_g = lin(graded[core])
    lum = lin_g @ W
    if name == 'fur':
        # sooty charcoal coat: luminance at 34 %, the hue pulled to a cold grey-brown, a little chroma kept
        grey = lum[:, None] * np.array([1.0, 0.96, 0.93])
        tgt[core] = encode(np.clip((0.8 * grey + 0.2 * lin_g) * 0.34, 0, 1))
    elif name == 'skin':
        # dusky grey-pink
        grey = lum[:, None] * np.array([1.0, 0.8, 0.8])
        tgt[core] = encode(np.clip((0.75 * grey + 0.25 * lin_g) * 0.55, 0, 1))
    else:
        # red eyes: dark ruby beads
        r = rank_of(lum)[:, None]
        tgt[core] = encode(np.clip(np.array([0.11, 0.002, 0.002]) + r ** 2 * np.array([0.35, 0.03, 0.02]), 0, 1))
    out['mouse_c'] = tgt
    return out


graded = RV.load_srgb(T / 'mouse_basecolor_graded.png', S) if (T / 'mouse_basecolor_graded.png').exists() else base
report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    targets = targets_for(graded, weight, name)
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'report': report,
           'sources': {'mouse_a': 'HD masters (MM9 ships no mouse1.dtx)',
                       'mouse_c': 'our design: charcoal coat, dusky skin, red eyes (MM9 ships no mouse3.dtx)'},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'mouse_region_mask.png', 'ramps': ramps}]},
          open(T / 'mouse_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[fur] = (0.55, 0.4, 0.25)
prev[skin] = (0.95, 0.6, 0.65)
prev[eyes] = (0.1, 0.1, 0.9)
(HERE / 'review').mkdir(exist_ok=True)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'mouse_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'fit': report, 'texels': {k: int(m.sum()) for k, m in zip(REGIONS, (fur, skin, eyes))}}))
