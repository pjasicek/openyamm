#!/usr/bin/env python3
"""Texture set for the Dragon King (one MM9 skin, GREENDRAGONLT: no colour tiers, so no region mask or ramps).

Inputs: meshy/retexture_v2 maps (our UVs: enable_original_uv), work/uv3d_body_v3.npz (dump_uv3d.py on work/uv_v3m.blend: xatlas layout + mouth patch),
textures/dragonking_ao_2k.png (bake_ao.py).
Outputs in textures/:
- dragonking_basecolor.png: 2K Meshy base colour, gutters padded (graded separately by grade_basecolor.py);
- dragonking_normal_1k.png: Meshy normal, padded, 1K;
- dragonking_metal_rough_1k.png: R baked AO, G Meshy roughness (clamped 0.45-0.9), B metallic 0 (runtime:
  claude_shared/material_classes_to_orm.py replaces R/G/B from the class map, keeping the AO as specular occlusion);
- dragonking_material_classes.png: 1K labels (CLAUDE_CREATURE_TEXTURES.md): 1 skin, 3 membrane, 4 claw/horn,
  5 tooth, 6 eye, 7 mouth interior.
Classes: from the texel's triangle (bind-pose rig group, head/jaw weight, small piece) and its HD colour:
membrane = wing-group texels that are dark (the spars are lighter green and stay skin); eye = saturated yellow-orange
on the head; mouth = saturated red on the head; tooth = pale low-saturation texels on the head or small pieces;
claw/horn = low-saturation grey/ivory texels on the head (horns, crest), hands, feet, wing claws and the tail tip.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
T = HERE / 'textures'
M = HERE / 'meshy' / 'retexture_v2'
S = 1024


def raster(npz, size):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
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
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (1 - l1 - l2 >= -1e-4)
        iy, ix = np.nonzero(inside)
        tri[size - 1 - (iy + y0), ix + x0] = t
    return tri, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, (mx - mn) / (mx + 1e-9), mx


base2k = np.asarray(Image.open(M / 'texture_urls_0_base_color.png').convert('RGB'), np.float32) / 255
tri2, d = raster(HERE / 'work' / 'uv3d_body_v3.npz', 2048)
# mouth patch (mouth_uv.py): the lip faces open into the mouth when the MM9 jaw drops; paint them a wet red
# interior, darker toward the throat (patch middle) and pinker at both lips, with fine noise.
PATCH = json.load(open(T / 'dragonking_mouth_patch.json'))['patch_uv']


def patch_rect(size):
    u0, v0, w, h = PATCH
    return (int(round((1 - v0 - h) * size)), int(round((1 - v0) * size)), int(round(u0 * size)),
            int(round((u0 + w) * size)))


def paint_mouth(img, size):
    r0, r1, c0, c1 = patch_rect(size)
    hh, ww = r1 - r0, c1 - c0
    fy = np.linspace(1, 0, hh)[:, None]            # 1 upper lip (top row) -> 0 lower lip
    fx = np.linspace(0, 1, ww)[None, :]            # front -> back
    lipness = np.abs(fy - 0.5) * 2                 # 1 at the lips, 0 mid-mouth
    deep = np.array([0.22, 0.03, 0.03]); lipc = np.array([0.62, 0.16, 0.14])
    col = deep + (lipc - deep) * (lipness ** 1.5)[..., None]
    col = col * (1.0 - 0.35 * fx)[..., None]
    rng = np.random.default_rng(3)
    col = col * (0.9 + 0.2 * rng.random((hh, ww, 1)))
    img[r0:r1, c0:c1] = np.clip(col, 0, 1)
    return img


based = paint_mouth(pad(base2k, tri2 >= 0), 2048)
Image.fromarray((based * 255).astype(np.uint8)).save(T / 'dragonking_basecolor.png')
nrm = pad(np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB'), np.float32) / 255, tri2 >= 0)
r0, r1, c0, c1 = patch_rect(2048)
nrm[r0:r1, c0:c1] = (0.5, 0.5, 1.0)
Image.fromarray((nrm * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(T / 'dragonking_normal_1k.png')

tri, _ = raster(HERE / 'work' / 'uv3d_body_v3.npz', S)
cov = tri >= 0
t = np.maximum(tri, 0)
chain = d['limb'].max(1)[t]            # rig group of the triangle (max over its corners)
head = d['head'].mean(1)[t] > 0.5
jaw = d['jaw'].mean(1)[t] > 0.5
piece = d['part'][t] == 2
z = d['xyz'][:, :, 2].mean(1)[t]
base = np.asarray(Image.fromarray((base2k * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS), np.float32) / 255
sm = ndimage.uniform_filter(base, (3, 3, 1))
h, s, v = hsv(sm)
wing = np.isin(chain, (5, 6))
limb_tip = np.isin(chain, (1, 2, 3, 4)) & (z < 3.0) | np.isin(chain, (1, 2)) & (s < 0.25)
classes = np.ones((S, S), np.uint8)
membrane = wing & (v < 0.30)
classes[membrane] = 3
grey = (s < 0.22) & (v > 0.12) & ~membrane
horn = grey & (head | limb_tip | wing | (chain == 7) | piece)
classes[horn] = 4
tooth = (head | piece) & (s < 0.25) & (v > 0.62)
classes[tooth] = 5
mouth = (head | jaw | piece) & (s > 0.4) & ((h < 18) | (h > 335)) & (v > 0.25)
classes[mouth] = 7
eye = (head | piece) & (h > 28) & (h < 62) & (s > 0.55) & (v > 0.45)
classes[eye] = 6
r0, r1, c0, c1 = patch_rect(S)
classes[r0:r1, c0:c1] = 7
classes[~cov] = 0
Image.fromarray(classes).save(T / 'dragonking_material_classes.png')

rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                   np.float32) / 255
rough = pad(np.clip(rough, 0.45, 0.9), cov)
rough[r0:r1, c0:c1] = 0.4
ao = np.asarray(Image.open(T / 'dragonking_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
ao = pad(ao, cov)
Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                    Image.new('L', (S, S), 0)]).save(T / 'dragonking_metal_rough_1k.png')
names = {0: 'empty', 1: 'skin', 3: 'membrane', 4: 'claw_horn', 5: 'tooth', 6: 'eye', 7: 'mouth'}
share = {names[k]: round(float((classes == k).mean()), 4) for k in names}
pal = {0: (0, 0, 0), 1: (110, 160, 70), 3: (200, 120, 200), 4: (240, 240, 120), 5: (255, 255, 230), 6: (60, 200, 255),
       7: (200, 40, 60)}
prev = np.zeros((S, S, 3), np.uint8)
for k, c in pal.items():
    prev[classes == k] = c
(HERE / 'review').mkdir(exist_ok=True)
Image.fromarray(np.concatenate([(base * 255).astype(np.uint8), prev], 1)).resize((1024, 512)).save(
    HERE / 'review' / 'texture_classes.png')
json.dump({'class_share': share}, open(T / 'dragonking_compose.json', 'w'), indent=1)
print('COMPOSED', share)
