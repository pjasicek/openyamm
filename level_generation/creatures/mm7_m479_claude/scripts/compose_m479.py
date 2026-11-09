#!/usr/bin/env python3
"""Textures for the Treant (CLAUDE_CREATURE_TEXTURES.md). Run after uv_raster.py (work/rig_v2.blend at 1024 and 2048,
tag v2) and bake_ao.py (work/ao_UVMap.png).

Tiers: descriptors 451/452/453 (Treant A/B/C) all draw sprite group m480 with palette 530 (native manifest: one
variant, recolour 'identity', masks zero). Every tier looks the same, so there is ONE material and no region mask or
ramps (the texture guide's tiers-as-ramps rule has nothing to recolour here).
- Bark: Meshy retexture_v2 base colour graded by the rest-pose AO (0.6 + 0.4 AO), then its median scaled to the
  native median x ALBEDO_GAIN (sprites carry baked shading; native m479sa0 median 56/44/32) with half of its chroma
  pulled to the native hue (Meshy's bark is a little yellower).
- Teeth (part 1/2: our peg teeth): Meshy painted them tan-brown with dark roots; repainted ivory, darker toward the
  gum (by the texel's distance from the tooth root along the row's axis), keeping Meshy's luminance detail at 30 %.
- Eyes (part 3: our almonds in their own UV square, work/eyes.json): painted procedurally: green iris glowing toward
  the centre (native eye pixels 56/93/39 median, 141/213/86 peak), vertical slit pupil, dark rim, small highlight.
- Mouth interior (cavity pieces 3 and 99): kept, darkened 0.8.
Outputs (textures/): m479_basecolor_2k.png, m479_normal_1k.png, m479_metal_rough_1k.png (R specular mask, G
roughness, B 0 metal), m479_material_classes.png (10 wood, 5 tooth, 6 eye, 7 mouth interior)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
HERE = Path(__file__).resolve().parents[1]
T = HERE / 'textures'; T.mkdir(exist_ok=True)
M = HERE / 'meshy' / 'retexture_v2'
NATIVE = np.array([56.0, 44.0, 32.0]) / 255
ALBEDO_GAIN = 1.35
IVORY = np.array([200, 186, 162]) / 255.0
SPEC = {'wood': 0.1, 'tooth': 0.5, 'eye': 0.9, 'mouth': 0.3}
ROUGH = {'wood': 0.85, 'tooth': 0.45, 'eye': 0.2, 'mouth': 0.6}
CLS = {'wood': 10, 'tooth': 5, 'eye': 6, 'mouth': 7}


def load(path, n, mode='RGB'):
    im = Image.open(path).convert(mode)
    return np.asarray(im.resize((n, n), Image.LANCZOS) if im.size != (n, n) else im, np.float64) / 255


def save(a, path):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path, optimize=True)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out = img[iy, ix]; out[cov] = img[cov]; return out


def classes(R):
    piece, part = R['piece'], R['part']; cov = piece >= 0
    mouth = cov & np.isin(piece, [3, 99])
    return {'tooth': cov & np.isin(part, [1, 2]), 'eye': cov & (part == 3), 'mouth': mouth,
            'wood': cov & (part == 0) & ~mouth}, cov


EYES = json.load(open(HERE / 'work' / 'eyes.json'))


def paint_eyes(img, n):
    u0, v0, side = EYES['uv_square']
    ys, xs = np.mgrid[0:n, 0:n]
    u = (xs + 0.5) / n; v = 1 - (ys + 0.5) / n
    a = (u - u0) / side; b = (v - v0) / side                     # 0..1 inside the square
    inside = (a >= 0) & (a <= 1) & (b >= 0) & (b <= 1)
    x = (a - 0.5) / 0.45; y = (b - 0.5) / 0.45                     # -1..1 over the eye front (eyes_add: 0.9 span)
    r = np.sqrt(x * x + (y / 0.85) ** 2)
    iris_c, iris_e = np.array([150, 220, 85]) / 255, np.array([45, 105, 30]) / 255
    t = np.clip(r, 0, 1)[..., None]
    col = iris_c * (1 - t) + iris_e * t
    pupil = np.clip(1 - (np.abs(x) - 0.05 * np.sqrt(np.clip(1 - y * y, 0, 1))) / 0.04, 0, 1)[..., None]
    col = col * (1 - pupil) + np.array([12, 18, 8]) / 255 * pupil
    rim = np.clip((r - 0.78) / 0.15, 0, 1)[..., None]
    col = col * (1 - rim) + np.array([30, 22, 12]) / 255 * rim
    hl = np.clip(1 - np.hypot(x + 0.35, y - 0.35) / 0.12, 0, 1)[..., None]
    col = col * (1 - hl) + np.array([235, 255, 210]) / 255 * hl
    img[inside] = col[inside]
    return img


R2 = np.load(HERE / 'work' / 'uvraster_v2_2048.npz'); R1 = np.load(HERE / 'work' / 'uvraster_v2_1024.npz')
C2, cov2 = classes(R2); C1, cov1 = classes(R1)
base = load(M / 'texture_urls_0_base_color.png', 2048)
ao = load(HERE / 'work' / 'ao_UVMap.png', 2048, 'L')
g = base * (0.6 + 0.4 * np.maximum(ao, 0.35))[..., None]
w = C2['wood']
med = np.median(g[w], 0)
lum = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
target = NATIVE * ALBEDO_GAIN
k = lum(target) / lum(med)
hue_fix = (target / lum(target)) / (med / lum(med))                 # per-channel chroma correction
g[w] = g[w] * k * (1 + 0.5 * (hue_fix - 1))
# teeth: ivory, darker toward the root (root = the end nearest the gum: upper teeth top, lower teeth bottom)
pos = R2['pos']; part = R2['part']
for kind, sgn in ((1, 1.0), (2, -1.0)):
    m = C2['tooth'] & (part == kind)
    z = pos[..., 2][m]
    gum = np.percentile(z, 97) if kind == 1 else np.percentile(z, 3)
    d = np.abs(z - gum)
    shade = 0.45 + 0.55 * np.clip(d / 0.12, 0, 1) ** 0.7
    L = lum(base[m]); detail = 0.7 + 0.3 * L / max(np.median(L), 1e-3)
    g[m] = IVORY[None] * (shade * detail)[:, None]
g[C2['mouth']] *= 0.8
g = paint_eyes(g, 2048)
save(pad(g, cov2), T / 'm479_basecolor_2k.png')
print('BASE wood median', np.round(np.median(g[w], 0) * 255), 'target', np.round(target * 255),
      'teeth median', np.round(np.median(g[C2['tooth']], 0) * 255))
normal = load(M / 'texture_urls_0_normal.png', 1024); rough_m = load(M / 'texture_urls_0_roughness.png', 1024, 'L')
flat = C1['eye'] | C1['tooth']
normal[flat] = [0.5, 0.5, 1.0]                                          # our own geometry: no Meshy normal detail
cls = np.zeros((1024, 1024), np.uint8); spec = np.zeros((1024, 1024)); rgh = np.full((1024, 1024), 0.85)
for name, m in C1.items():
    cls[m] = CLS[name]; spec[m] = SPEC[name]
    if m.any():
        rgh[m] = np.clip(ROUGH[name] + (rough_m[m] - np.median(rough_m[m])) * 0.5, 0.1, 1)
save(pad(normal, cov1), T / 'm479_normal_1k.png')
save(np.stack([pad(spec, cov1), pad(rgh, cov1), np.zeros((1024, 1024))], -1), T / 'm479_metal_rough_1k.png')
Image.fromarray(cls).save(T / 'm479_material_classes.png')
print('CLASSES', {n: int(m.sum()) for n, m in C1.items()}, 'covered', int(cov1.sum()))
