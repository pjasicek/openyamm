#!/usr/bin/env python3
"""Cobra textures (CLAUDE_CREATURE_TEXTURES.md: shared skin + region mask + per-tier ramps, material classes, AO in R).

Per texel the rest-pose 3D position (work/uv3d.npz) and the baked base colour (bake_reduced.py) decide:
  - fangs (ivory, mouth area) and mouth interior (red/pink, head) stay out of every region,
  - G "pale front hood-side scales": hood flap texels on the front (belly) side, beside the belly scute strip,
  - B "pale back-of-hood rings": pale texels on the back of the hood (the spectacle),
  - R "blue-grey body, belly plates and tail spots": all other skin (the native regions of mm6_cob/manifest.json).
Ramps: each tier's own native palette (677 A, 678 B, 679 C) per region, from the native frames' masks_2x channels.
Per tier a target texture is made by histogram matching (a texel's luminance percentile in its region picks the
native colour at the same percentile, times ALBEDO for the sprites' baked shading); region_variants.fit_ramps then
fits the 16 stops to it with the shader's exact lookup and reports the 8-bit error.
Writes textures/cob_basecolor_graded.png (2K; grade_basecolor.py must run first), cob_region_mask.png (1K RGBA),
cob_metal_rough_1k.png (R AO, G roughness, B 0), cob_normal_1k.png, cob_material_classes.png (1K L, nearest),
cob_ramps.json (region_variants.py format) and review/texture_classes.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
T = ROOT / 'textures'; NATIVE = ROOT.parent / 'mm6_cob'
FRAMES = ['cobstaa0', 'cobstaa1', 'cobstaa2', 'cobstaa3', 'cobstaa4', 'cobwalc2', 'cobattc0', 'cobfidc0']
PALETTES = {'cob_a': '677', 'cob_b': '678', 'cob_c': '679'}
STOPS = 16
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

rig = json.load(open(ROOT / 'work' / 'rig.json')); Jn = np.array(rig['joints'])
neck = Jn[rig['root']:-1]                                    # raised centreline joints (root .. neck top)
part_map, xyz = C.rasterise(np.load(ROOT / 'work' / 'uv3d.npz'))
valid = part_map >= 0
base = C.load(str(T / 'body_base_color.png'))
h, s, v = C.hsv(base)
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
cy = np.interp(z, neck[:, 2], neck[:, 1])                    # neck centre y at the texel's height
head = valid & (y < -0.06) & (z > 0.74)
fang = head & (v > 0.6) & (s < 0.3) & (z < 0.86)
mouth = head & ((h < 25) | (h > 320)) & (s > 0.3) & ~fang
hood = valid & (z > 0.45) & (y < 0.2) & ~head & (np.abs(x) > 0.045)
front = hood & (y < cy)
G = front
B = hood & ~front & (v > 0.42) & (s < 0.4)
R = valid & ~fang & ~mouth & ~G & ~B
classes = np.zeros(base.shape[:2], np.uint8)
classes[valid] = 1; classes[fang] = 5; classes[mouth] = 7


def feather(m):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    return np.asarray(im.resize((1024, 1024), Image.LANCZOS), np.float32) / 255


regions = [feather(R), feather(G), feather(B)]
Image.fromarray(np.stack([(r * 255 + 0.5).astype(np.uint8) for r in regions] + [np.zeros((1024, 1024), np.uint8)], 2),
                'RGBA').save(T / 'cob_region_mask.png')
Image.fromarray(classes).resize((1024, 1024), Image.NEAREST).save(T / 'cob_material_classes.png')
ao = Image.open(T / 'cob_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)
rough = Image.open(T / 'body_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)
Image.merge('RGB', (ao, rough, Image.new('L', (1024, 1024), 0))).save(T / 'cob_metal_rough_1k.png')
Image.open(T / 'body_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'cob_normal_1k.png')

# ---- ramps ----------------------------------------------------------------------------------------------------------
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import region_variants as RV
ALBEDO = 1.35                       # sprites carry baked shading; albedo is brighter than the native pixels
graded = RV.load_srgb(T / 'cob_basecolor_graded.png', 1024)
glum = RV.luminance(graded)
encode = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def native(palette, channel):
    out = []
    for f in FRAMES:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{f}_{palette}.png').convert('RGBA'), np.float32) / 255
        m = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{f}.png').convert('RGBA').resize(
            (nv.shape[1], nv.shape[0]), Image.NEAREST), np.float32) / 255
        out.append(nv[(nv[..., 3] > 0.5) & (m[..., channel] > 0.5), :3])
    return lin(np.concatenate(out))


ramps = {k: [] for k in PALETTES}; report = []
for c, weight in enumerate(regions):
    core = weight > 0.5
    rank = np.zeros(glum.shape); order = np.argsort(glum[core])
    r = np.empty(order.size); r[order] = (np.arange(order.size) + 0.5) / order.size; rank[core] = r
    targets = {}
    for k, p in PALETTES.items():
        pal = native(p, c); pal = pal[np.argsort(pal @ W)]     # histogram match: texel percentile -> native colour
        if c == 2:                  # native B also covers the dark scales round the rings; our B is the pale ring only
            pal = pal[len(pal) // 2:]
        tgt = graded.copy()
        tgt[core] = encode(np.clip(pal[np.minimum((rank[core] * len(pal)).astype(int), len(pal) - 1)] * ALBEDO, 0, 1))
        targets[k] = tgt
    fitted, rep = RV.fit_ramps(graded, targets, weight)
    for k in PALETTES:
        ramps[k].append(fitted[k])
    report.append({'region': 'RGB'[c], **rep})
json.dump({'variants': list(PALETTES), 'palettes': PALETTES, 'albedo': ALBEDO, 'report': report,
           'materials': [{'base': 'Cobra', 'prefix': 'Cobra', 'mask': 'cob_region_mask.png', 'ramps': ramps}]},
          open(T / 'cob_ramps.json', 'w'), indent=1)
preview = base * 0.3
preview[R] = (0.30, 0.45, 0.50); preview[G] = (0.85, 0.85, 0.40); preview[B] = (1.0, 1.0, 1.0)
preview[fang] = (1.0, 0.6, 0.2); preview[mouth] = (0.9, 0.1, 0.1)
(ROOT / 'review').mkdir(exist_ok=True)
Image.fromarray((preview * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'texture_classes.png')
print('COMPOSED', json.dumps(report), 'fang', int(fang.sum()), 'mouth', int(mouth.sum()))
