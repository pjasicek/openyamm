#!/usr/bin/env python3
"""Sea serpent textures (CLAUDE_CREATURE_TEXTURES.md: shared skin + region mask + per-tier ramps, material classes, AO in
R of the metal/roughness map), plus the foam collar's material.

Body regions (the native manifest's masks_2x channels): R olive scales (dorsal hide, head shell), G brown crest and
spikes, B grey-green belly rings. Per texel the rest-pose 3D position (work/uv3d.npz) and the baked base colour decide:
  - claws, teeth (ivory: low saturation, bright) and the mouth interior (red) stay out of every region,
  - B: belly = low-saturation grey-blue texels on the front (-Y) half of the column,
  - G: crest and spikes = brown/orange texels (hue 15-35, saturated),
  - R: everything else that is skin.
Foam: own material on the collar ring (textures/foam.png with alpha); its mask channel R is the whole foam (region
'foam', native channel A), ramped per tier from the foam palette.
Ramps: each tier's own native palette (813 A, 814 B, 815 C) per region: per texel the chroma of the native colour at
the same luminance percentile and the texel's own luminance (region mean matched to the native mean x ALBEDO; the
sprites' painted-shading range is not copied, which speckled the belly), then region_variants.fit_ramps (16 stops,
the shader's exact lookup).
Writes textures/seas_basecolor_graded.png (graded first by grade_basecolor.py), seas_region_mask.png,
seas_metal_rough_1k.png (R AO, G roughness, B 0), seas_normal_1k.png, seas_material_classes.png, foam_region_mask.png,
seas_ramps.json and review/texture_classes.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
sys.path.insert(0, str(ROOT.parent / 'claude_shared'))
import compose_textures_v2 as C
import region_variants as RV
T = ROOT / 'textures'; NATIVE = ROOT.parent / 'mm6_seas'
FRAMES = ['seassta0', 'seassta1', 'seassta2', 'seassta3', 'seassta4', 'seaswaa0', 'seaswad2', 'seasata0', 'seasfic0']
PALETTES = {'seas_a': '813', 'seas_b': '814', 'seas_c': '815'}
ALBEDO = 1.35
W = np.array([0.2126, 0.7152, 0.0722])
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
encode = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)

data = np.load(ROOT / 'work' / 'uv3d.npz')
part_map, xyz = C.rasterise(data)
valid = part_map >= 0
base = C.load(str(T / 'body_base_color.png'))
h, s, v = C.hsv(base)
x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
rig = json.load(open(ROOT / 'work' / 'rig.json')); Jn = np.array(rig['joints'])
cy = np.interp(z, Jn[:12, 2], Jn[:12, 1])                  # column centre y at the texel's height (lower column)
ivory = valid & (s < 0.32) & (v > 0.62) & ((h < 60) | (h > 300))
mouth = valid & ((h < 12) | (h > 335)) & (s > 0.45) & (y < -0.25)
belly = valid & ~ivory & (s < 0.25) & (y < cy) & (z < 0.8) & ((h > 150) & (h < 260) | (s < 0.12))
# grow the belly into its darker, more saturated ring creases (they kept the base green-grey in the other tiers)
grown = np.asarray(Image.fromarray((belly * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) > 0
belly = grown & valid & ~ivory & (y < cy + 0.02) & (z < 0.8) & ~(((h >= 15) & (h < 35) & (s > 0.45)))
crest = valid & ~ivory & ~mouth & ~belly & (h >= 15) & (h < 35) & (s > 0.45)
R = valid & ~ivory & ~mouth & ~belly & ~crest
classes = np.zeros(base.shape[:2], np.uint8)
classes[valid] = 1; classes[ivory] = 4; classes[mouth] = 7


def feather(m):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    return np.asarray(im.resize((1024, 1024), Image.LANCZOS), np.float32) / 255


regions = [feather(R), feather(crest), feather(belly)]
RV.write_mask(regions, T / 'seas_region_mask.png')
Image.fromarray(classes).resize((1024, 1024), Image.NEAREST).save(T / 'seas_material_classes.png')
ao = Image.open(T / 'seas_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)
rough = Image.open(T / 'body_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS)
Image.merge('RGB', (ao, rough, Image.new('L', (1024, 1024), 0))).save(T / 'seas_metal_rough_1k.png')
Image.open(T / 'body_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(T / 'seas_normal_1k.png')


def native(palette, channel):
    out = []
    for f in FRAMES:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{f}_{palette}.png').convert('RGBA'), np.float32) / 255
        m = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{f}.png').convert('RGBA').resize(
            (nv.shape[1], nv.shape[0]), Image.NEAREST), np.float32) / 255
        out.append(nv[(nv[..., 3] > 0.5) & (m[..., channel] > 0.5), :3])
    return lin(np.concatenate(out))


def fit(graded, weights, channels):
    glum = RV.luminance(graded); ramps = {k: [] for k in PALETTES}; report = []
    for weight, c in zip(weights, channels):
        core = weight > 0.5
        rank = np.zeros(glum.shape); order = np.argsort(glum[core])
        r = np.empty(order.size); r[order] = (np.arange(order.size) + 0.5) / order.size; rank[core] = r
        targets = {}
        texel_lum = RV.srgb_to_linear(graded[core]) @ W
        for k, p in PALETTES.items():
            pal = native(p, c); pal = pal[np.argsort(pal @ W)]
            pal_lum = pal @ W
            # Colour (chroma) from the native palette at the texel's luminance percentile; brightness from the texel
            # itself, scaled so the region's mean matches the native mean x ALBEDO. Full histogram matching mapped
            # the Meshy belly's narrow luminance (0.12-0.28) onto the sprite's painted-shading range (0.002-1.0) and
            # turned its fine pebbles into black/white speckles.
            # chroma from the palette's 15th-95th percentile (the darkest native pixels are painted shadow whose colour
            # is unreliable: near-black flecks), averaged into 8 luminance bands and interpolated by the texel's
            # percentile, so the hue changes smoothly with brightness (per-pixel picks gave coloured flecks)
            mid = pal[int(0.15 * len(pal)):int(0.95 * len(pal))]
            band = np.array([(b / np.maximum(b @ W, 1e-3)[:, None]).mean(0) for b in np.array_split(mid, 8)])
            x = np.clip(rank[core], 0, 1) * (len(band) - 1); i0 = np.minimum(x.astype(int), len(band) - 2)
            f = (x - i0)[:, None]
            chroma = band[i0] * (1 - f) + band[i0 + 1] * f
            gain = ALBEDO * float(pal_lum.mean()) / float(texel_lum.mean())
            tgt = graded.copy()
            tgt[core] = encode(np.clip(chroma * (texel_lum * gain)[:, None], 0, 1))
            targets[k] = tgt
        fitted, rep = RV.fit_ramps(graded, targets, weight)
        for k in PALETTES:
            ramps[k].append(fitted[k])
        report.append({'region': 'RGBA'[c], **rep})
    return ramps, report


body_ramps, body_report = fit(RV.load_srgb(T / 'seas_basecolor_graded.png', 1024), regions, [0, 1, 2])
foam_rgba = np.asarray(Image.open(T / 'foam.png').convert('RGBA').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
foam_weight = (foam_rgba[..., 3] > 0.5).astype(np.float64)
RV.write_mask([foam_weight], T / 'foam_region_mask.png')
foam_ramps, foam_report = fit(foam_rgba[..., :3].astype(np.float64), [foam_weight], [3])
json.dump({'variants': list(PALETTES), 'palettes': PALETTES, 'albedo': ALBEDO, 'report': body_report + foam_report,
           'materials': [{'base': 'Seas', 'prefix': 'Seas', 'mask': 'seas_region_mask.png', 'ramps': body_ramps},
                         {'base': 'Foam', 'prefix': 'Foam', 'mask': 'foam_region_mask.png', 'ramps': foam_ramps}]},
          open(T / 'seas_ramps.json', 'w'), indent=1)
preview = base * 0.3
preview[R] = (0.45, 0.45, 0.15); preview[crest] = (0.7, 0.4, 0.15); preview[belly] = (0.6, 0.7, 0.8)
preview[ivory] = (1, 1, 0.85); preview[mouth] = (0.9, 0.1, 0.1)
(ROOT / 'review').mkdir(exist_ok=True)
Image.fromarray((preview * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'texture_classes.png')
print('COMPOSED', json.dumps([{'region': r['region'], **{k: v['mean_abs_8bit'] for k, v in r.items() if k.startswith('seas')}}
                              for r in body_report + foam_report]),
      'texels R', int(R.sum()), 'crest', int(crest.sum()), 'belly', int(belly.sum()), 'ivory', int(ivory.sum()),
      'mouth', int(mouth.sum()))
