#!/usr/bin/env python3
"""Shared texture set, region mask and tier ramps for the MM9 cow (CLAUDE_CREATURE_TEXTURES.md).
Inputs: meshy/cow_retexture_v1 maps (our UVs), textures/cow_ao_2k.png, work/uv3d_cow.npz (dump_uv3d.py with
ATTRS=cav_t,cav_low,cav_x), work/uv3d_mm9_cow.npz, the MM9 skins COW and COWBROWN.
Outputs in textures/: cow_basecolor.png, cow_normal_1k.png, cow_metal_rough_1k.png, cow_material_classes.png,
cow_region_mask.png, cow_ramps.json.
Regions: R white hide, G black hide (split by the paint's luminance), B udder and inner ears (pink), A muzzle.
Hooves, eyes and the mouth cavity are in no region (same in both tiers).
Tier A (Cow) keeps the HD look. Tier B (Brown Cow): MM9's COWBROWN has no patches, so R and G both map to its plain
coat (each region's luminance rank onto a trimmed coat palette, albedo x ALBEDO), B to its udder tan and A to its dark
muzzle. Both skins share the MM9 UVs, so the MM9 classes come from the COW skin."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
sys.path.insert(0, str(HERE / 'scripts'))
import region_variants as RV
from compose_common import W, hsv, raster, pad, feather, paint_cavity, write_maps

T = HERE / 'textures'
M = HERE / 'meshy' / 'cow_retexture_v1'
TIERS = {'cow_a': 'cow/skins/cow.png', 'cow_b': 'cowbrown/skins/cowbrown.png'}
REGIONS = ('white', 'black', 'pink', 'muzzle')
MAT = 'Cow'
ALBEDO = 1.3
HOOF_TOP = 0.135     # z of the hoof top in the bind pose
S = 1024


def lin(c):
    return RV.srgb_to_linear(c)


def encode(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


src4k = Image.open(M / 'texture_urls_0_base_color.png').convert('RGB')
base2k_img = src4k if src4k.size == (2048, 2048) else src4k.resize((2048, 2048), Image.LANCZOS)
base2k = np.asarray(base2k_img, np.float32) / 255
FIELDS = ['head', 'jaw', 'attr_cav_t', 'attr_cav_low', 'attr_cav_x']
tri, f, dbody = raster(HERE / 'work' / 'uv3d_cow.npz', 2048, FIELDS)
cov2 = tri >= 0
ti = np.maximum(tri, 0)
cav2 = cov2 & (dbody['cavity'][ti] == 1)
base2k = paint_cavity(base2k, cov2, cav2, f['attr_cav_t'], f['attr_cav_low'], f['attr_cav_x'])
Image.fromarray((pad(base2k, cov2) * 255).astype(np.uint8)).save(T / 'cow_basecolor.png')

base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
tri1, f1, _ = raster(HERE / 'work' / 'uv3d_cow.npz', S, ['head'])
covered = tri1 >= 0
ti1 = np.maximum(tri1, 0)
part = np.where(covered, dbody['part'][ti1], -1)
cen = dbody['xyz'].mean(1)[ti1]
cavity = covered & (dbody['cavity'][ti1] == 1)
piece = covered & (part % 10 == 2)
hsvh, hsvs, hsvv = hsv(base)
L = lin(base) @ W
eyes = piece & (f1['head'] > 0.5) & (cen[..., 2] > 1.1)
teats = piece & (cen[..., 2] < 0.75) & (np.abs(cen[..., 0]) < 0.25) & (cen[..., 1] > 0.3) & (cen[..., 1] < 1.0)
hoof = covered & (cen[..., 2] < HOOF_TOP) & ~piece & (L < 0.18)
skin_body = covered & ~cavity & ~eyes & ~hoof
pinkish = ((hsvh < 32) | (hsvh > 335)) & (hsvs > 0.10) & (hsvv > 0.42)
pinkish = ndimage.binary_opening(pinkish, iterations=1)
headm = f1['head'] > 0.5
muzzle = skin_body & headm & pinkish & (cen[..., 1] < -1.05)
pink = skin_body & ~muzzle & (pinkish | teats)
coat = skin_body & ~muzzle & ~pink
vals = np.sort(L[coat])
# two-class threshold (Otsu) on the coat's luminance
hist, edges = np.histogram(L[coat], bins=128)
mids = (edges[1:] + edges[:-1]) / 2
w0 = np.cumsum(hist); w1 = w0[-1] - w0
m0 = np.cumsum(hist * mids) / np.maximum(w0, 1); m1 = (np.cumsum((hist * mids)[::-1])[::-1] - hist * mids) / np.maximum(w1, 1)
th = float(mids[np.argmax(w0 * w1 * (m0 - m1) ** 2)])
wh = np.clip((L - th * 0.75) / (th * 0.5), 0, 1)
wh = wh * wh * (3 - 2 * wh)
# The shader mixes the channels in turn, so two soft neighbours leak the base colour between them (white lines on
# the Brown Cow): the R channel covers the whole skin and the later channels lie over it. Ramps are still fitted on
# each region's own texels (`regions`).
regions = [feather(wh * coat, covered), feather((1 - wh) * coat, covered), feather(pink, covered),
           feather(muzzle, covered)]
RV.write_mask([feather(coat | pink | muzzle, covered)] + regions[1:], T / 'cow_region_mask.png')
classes = np.zeros((S, S), np.uint8)
classes[coat] = 2                  # fur/hide
classes[muzzle | pink] = 1         # bare skin
classes[hoof] = 4
classes[eyes] = 6
classes[cavity] = 7
Image.fromarray(classes).save(T / 'cow_material_classes.png')
if (T / 'cow_ao_2k.png').exists():
    def cls_rough(r):
        r = np.where(coat, np.clip(r, 0.7, 0.9), r)
        r = np.where(muzzle | pink, 0.5, r)
        r = np.where(hoof, 0.5, r)
        r = np.where(eyes, 0.2, r)
        return np.where(cavity, 0.4, r)
    write_maps(M, T, 'cow', covered, cls_rough, S, cov2)

# ---------------- MM9 skin classes (COW skin; COWBROWN shares the UVs)
ms = 128
mtri, _, dmm = raster(HERE / 'work' / 'uv3d_mm9_cow.npz', ms, [])
mcov = mtri >= 0
skins = {k: np.asarray(Image.open(HERE / 'source' / p).convert('RGB'), np.float32) / 255 for k, p in TIERS.items()}
mh, ms_, mv = hsv(skins['cow_a'])
mcen = dmm['xyz'].mean(1)[np.maximum(mtri, 0)]
mpink = mcov & ((mh < 32) | (mh > 335)) & (ms_ > 0.08) & (mv > 0.55)
m_muzzle = mpink & (mcen[..., 1] < -1.0)
m_pink = mpink & ~m_muzzle
m_coat = mcov & ~mpink & (mcen[..., 2] > 0.2)
bcoat = lin(skins['cow_b'][m_coat])
bcoat = bcoat[np.argsort(bcoat @ W)]
bcoat = bcoat[int(0.1 * len(bcoat)):int(0.9 * len(bcoat))]
bpink = lin(skins['cow_b'][m_pink]); bpink = bpink[np.argsort(bpink @ W)]
bmuz = lin(skins['cow_b'][m_muzzle]); bmuz = bmuz[np.argsort(bmuz @ W)]
if len(bmuz) < 16:
    bmuz = np.tile(np.array([[0.03, 0.02, 0.015], [0.08, 0.05, 0.04]]), (8, 1))
print('MM9 texels coat', len(bcoat), 'pink', len(bpink), 'muzzle', len(bmuz))
PAL = {'white': bcoat, 'black': bcoat, 'pink': bpink, 'muzzle': bmuz}
GAIN = {'white': ALBEDO, 'black': ALBEDO, 'pink': ALBEDO, 'muzzle': 1.0}
graded = RV.load_srgb(T / 'cow_basecolor_graded.png', S) if (T / 'cow_basecolor_graded.png').exists() else base


def target_b(name, weight):
    core = weight > 0.5
    tgt = graded.copy()
    if core.sum() < 12:
        return tgt
    lum = lin(graded[core]) @ W
    rank = np.empty(lum.size)
    rank[np.argsort(lum)] = (np.arange(lum.size) + 0.5) / lum.size
    pal = PAL[name]
    # black and white meet at the palette's middle, or the old patch borders stay as a pale contour on the brown coat
    if name == 'black':
        rank = rank * 0.55
    elif name == 'white':
        rank = 0.45 + rank * 0.55
    tgt[core] = encode(np.clip(pal[(rank * (len(pal) - 1)).astype(int)] * GAIN[name], 0, 1))
    return tgt


report, ramps = [], {k: [] for k in TIERS}
previews = {k: graded.copy() for k in TIERS}
for name, weight in zip(REGIONS, regions):
    tgt_a = graded.copy()
    if name == 'white':     # the grade blows the white hide past albedo 243 (Khronos): keep it under that
        tgt_a = encode(lin(graded) * 0.84)
    targets = {'cow_a': tgt_a, 'cow_b': target_b(name, weight)}
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in TIERS:
        ramps[k].append(fitted[k])
        core = weight > 0.5
        previews[k][core] = targets[k][core]
    report.append({'region': name, **{k: v.get('mean_abs_8bit') if isinstance(v, dict) else v for k, v in rep.items()}})
json.dump({'variants': list(TIERS), 'otsu_luminance': th, 'report': report,
           'sources': {k: f'source/{p}' for k, p in TIERS.items()},
           'materials': [{'base': MAT, 'prefix': MAT, 'mask': 'cow_region_mask.png', 'ramps': ramps}]},
          open(T / 'cow_ramps.json', 'w'), indent=1)
prev = np.zeros((S, S, 3))
prev[coat] = np.stack([wh, wh, wh], -1)[coat] * 0.8 + 0.1
prev[pink] = (0.9, 0.5, 0.6)
prev[muzzle] = (0.9, 0.2, 0.3)
prev[hoof] = (0.2, 0.8, 0.3)
prev[eyes] = (1.0, 0.8, 0.1)
prev[cavity] = (0.2, 0.3, 1.0)
row = [prev] + [previews[k] for k in TIERS]
Image.fromarray((np.concatenate(row, 1) * 255).astype(np.uint8)).resize((512 * len(row), 512)).save(
    HERE / 'review' / 'cow_texture_classes_tiers.png')
print('COMPOSED', json.dumps({'otsu': th, 'fit': report, 'texels': {'coat': int(coat.sum()), 'pink': int(pink.sum()),
      'muzzle': int(muzzle.sum()), 'hoof': int(hoof.sum()), 'eyes': int(eyes.sum()), 'cavity': int(cavity.sum())}}))
