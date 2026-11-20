#!/usr/bin/env python3
"""Texture set for the MM9 hen / rooster (project name from the folder; ported from mm9_crow_claude/scripts/
compose_crow.py). One MM9 skin each (HEN.dtx, ROOSTER.dtx): no tiers, so no region mask or ramps (as the Isle of Ashes
NPCs, mm9_annud_claude). Usage: compose_chicken.py

Inputs: meshy/<name>_retexture_v1 (4K paint on our xatlas UVs), work/uv3d_<name>.npz (dump_uv3d.py), textures/
<name>_ao_2k.png (bake_ao.py). Outputs in textures/: <name>_basecolor.png (2K, padded; graded by grade_basecolor.py
into <name>_basecolor_graded.png), <name>_normal_1k.png, <name>_metal_rough_1k.png (R AO, G roughness, B metallic 0),
<name>_material_classes.png (1K labels: 2 feathers, 1 bare skin (comb, wattles, face, legs), 4 beak/claws, 6 eyes).
Classes by colour inside the bound regions: red = comb/wattle/face skin, yellow-orange = beak (head) or legs (below the
leg exit), the eye pieces from the graft (part 2 near the eye height), the rest feathers.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
NAME = HERE.name.split('_')[1]
T = HERE / 'textures'
M = HERE / 'meshy' / f'{NAME}_retexture_v1'
CFG = json.load(open(HERE / 'work' / 'rig_v1.cfg.json'))


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


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


S = 1024
tri, f, dbody = raster(HERE / 'work' / f'uv3d_{NAME}.npz', S, ['head'])
covered = tri >= 0
ti = np.maximum(tri, 0)
cen = dbody['xyz'].mean(1)[ti]
part = dbody['part'][ti]
base4 = Image.open(M / 'texture_urls_0_base_color.png').convert('RGB')
base2k = np.asarray(base4.resize((2048, 2048), Image.LANCZOS), np.float32) / 255   # 4K -> 2K once
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
h, s, v = hsv(base)
legs = covered & (cen[..., 2] < CFG['leg_exit_z']) & (np.abs(cen[..., 0]) > 0.01)
head = covered & (f['head'] > 0.5)
red = (s > 0.45) & ((h < 20) | (h > 330))
yellow = (s > 0.3) & (h >= 20) & (h < 70)
eyes = covered & (part % 10 == 2) & head & ((v < 0.35) | ((h >= 15) & (h < 45) & (s > 0.5) & ~yellow))
beak = head & yellow & ~eyes
skin = covered & ~eyes & ~beak & (red | legs)
feathers = covered & ~(eyes | beak | skin)
claws = legs & (v > 0.7) & (s < 0.25)
classes = np.zeros((S, S), np.uint8)
classes[feathers] = 2
classes[skin] = 1
classes[beak | claws] = 4
classes[eyes] = 6
Image.fromarray(classes).save(T / f'{NAME}_material_classes.png')
tri2, _, _ = raster(HERE / 'work' / f'uv3d_{NAME}.npz', 2048, [])
Image.fromarray((pad(base2k, tri2 >= 0) * 255).astype(np.uint8)).save(T / f'{NAME}_basecolor.png')
nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize((2048, 2048), Image.LANCZOS),
                 np.float32) / 255
Image.fromarray((pad(nrm, tri2 >= 0) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(
    T / f'{NAME}_normal_1k.png')
rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = np.where(feathers, np.clip(rough, 0.6, 0.85), np.where(beak | claws, 0.45, np.where(eyes, 0.15, 0.6)))
rough = pad(rough, covered)
ao = np.asarray(Image.open(T / f'{NAME}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / f'{NAME}_metal_rough_1k.png')
# the throat under the beak: Meshy paints this hidden pocket dark (texels of luminance 0.04-0.4 between the wattles),
# which reads as an open mouth from the front and below (viewer review 2026-10-30). Dark texels of the head shell below
# the beak root and off the midline by less than THROAT_X take the feathers' median colour (soft mask, 85 %); the red
# skin at the beak base and the beak stay. Final colour: <name>_basecolor_final.png, read by build_export.py.
THROAT_X = CFG.get('throat_x', 0.05)
G = T / f'{NAME}_basecolor_graded.png'
if G.exists():
    gp = json.load(open(HERE / 'work' / 'graft_v1.json'))['placement']
    tri2b, f2, _ = raster(HERE / 'work' / f'uv3d_{NAME}.npz', 2048, ['head'])
    ti2 = np.maximum(tri2b, 0)
    cen2 = dbody['xyz'].mean(1)[ti2]
    part2 = dbody['part'][ti2]
    gr = np.asarray(Image.open(G).convert('RGB'), np.float32) / 255
    cls2 = np.asarray(Image.fromarray(classes).resize((2048, 2048), Image.NEAREST))
    lum = gr @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    feat = (cls2 == 2) & (tri2b >= 0)
    med = np.median(gr[feat], axis=0)
    h2, s2, v2 = hsv(gr)
    bright_red = (s2 > 0.55) & (v2 > 0.45) & ((h2 < 20) | (h2 > 330))
    throat = (tri2b >= 0) & (part2 % 10 != 2) & (cen2[..., 2] < gp['beak_root'][2] + 0.005) \
        & (np.abs(cen2[..., 0]) < THROAT_X) & (cen2[..., 1] < gp['eye'][1] + 0.03) & (cls2 != 4) & ~bright_red
    dark = np.clip((0.82 * np.median(lum[feat]) - lum) / (0.3 * np.median(lum[feat])), 0, 1)
    m = ndimage.gaussian_filter((throat * dark).astype(np.float32), 2.0) * 0.85 * (tri2b >= 0)
    fin = gr * (1 - m[..., None]) + med * m[..., None]
    # the wattles: the paint leaves dark maroon blotches on these separate lobes (seen from the front); dark texels of
    # the red skin on the head's small pieces rise to the lobes' own bright red, keeping their fine detail
    lobes = (tri2b >= 0) & (f2['head'] > 0.5) & (part2 % 10 == 2) & (cls2 == 1) & (cen2[..., 2] < gp['beak_root'][2] + 0.01)
    if lobes.sum() > 100:
        vl = v2[lobes]
        ref = float(np.percentile(vl, 70))
        red = np.median(gr[lobes & (v2 > ref * 0.9)], axis=0)
        ml = ndimage.gaussian_filter((lobes & (v2 < 0.8 * ref)).astype(np.float32), 1.5) * lobes
        detail = (gr / np.maximum(ndimage.gaussian_filter(gr, (6, 6, 0)), 1e-3))
        fin = fin * (1 - ml[..., None]) + np.clip(red * np.clip(detail, 0.7, 1.3), 0, 1) * ml[..., None]
        print('WATTLE texels', int((ml > 0.3).sum()), 'red', np.round(red, 3).tolist())
    Image.fromarray((np.clip(fin, 0, 1) * 255).astype(np.uint8)).save(T / f'{NAME}_basecolor_final.png')
    print('THROAT texels', int((throat & (dark > 0)).sum()))
prev = np.zeros((S, S, 3))
prev[feathers] = (0.85, 0.85, 0.9)
prev[skin] = (0.9, 0.2, 0.2)
prev[beak | claws] = (0.95, 0.75, 0.2)
prev[eyes] = (0.1, 0.6, 1.0)
(HERE / 'review').mkdir(exist_ok=True)
Image.fromarray((np.concatenate([prev, base], 1) * 255).astype(np.uint8)).save(
    HERE / 'review' / f'{NAME}_texture_classes.png')
print('COMPOSED', json.dumps({'texels': {k: int(m.sum()) for k, m in
                                         (('feathers', feathers), ('skin', skin), ('beak_claws', beak | claws),
                                          ('eyes', eyes))}}))
