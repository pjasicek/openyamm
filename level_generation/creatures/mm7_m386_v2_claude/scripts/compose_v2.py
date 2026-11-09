"""MM7 robot textures on the hard-surface UV layout (uv_hardsurface.py) from meshy/retexture_v2uv.

Replaces compose_robot.py (Smart UV layout): no luminance-ramp recolour of the body and Meshy's metal maps are kept.
- Base colour: Meshy's, padded into the gutters, lightly AO-graded (glows untouched). Tier A shows it unchanged.
- Metal/roughness (glTF packing): R = baked AO (engine specular occlusion "orm"), G = Meshy roughness, B = Meshy
  metallic (capped at METAL_MAX = 0.3, see below); glows non-metallic and glossy.
- Tiers: all three descriptors use palette 386; the original engine multiplies B and C by the descriptor TintColor
  (Sentinel 0x93c4ba, Assassin 0xd8c462). That multiply is the material's baseColorFactor (linear tint), exact and
  smooth. The green optics (mask R) and blue coils (mask G) keep their own colour: per-tier region ramps fitted from
  the tinted luminance back to the untinted glow colour. Tier A carries no region ramps (build drops them).
- Normal 1K (Meshy +y-down converted; the contract's size), material classes 1K (metal 9, rubber 11, glow 6).
Writes textures/robot_{basecolor,metal_rough,normal,region_mask,material_classes}.png, textures/robot_ramps.json
(region ramps + "tint_factors"), review/texture_audit.json."""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; REPO = P.parents[2]
sys.path[:0] = [str(P.parent / 'mm6_gob_claude/scripts'), str(P.parent / 'claude_shared'), str(REPO / 'tools')]
import compose_textures_v2 as C
import region_variants as RV
import normal_map_convention as NM
T = P / 'textures'; S = P / 'meshy/retexture_v2uv'
# In game (2026-10-21, review/ingame/): Meshy's metallic (~0.95 everywhere) left only the blurred sky reflection in
# daylight (spikes blue-black, brass murky); a cap of 0.5 still made the robot darker than the old non-metal one in the
# dim Lincoln (indoor ambient reaches a metallic texel only as 1 - metallic, fs_model.sc). 0.3 matches the old
# brightness in both and keeps the brass and steel sheen.
METAL_MAX = float(os.environ.get('METAL_MAX', 0.3))
AO_GRADE = float(os.environ.get('AO_GRADE', 0.25))
TINT = {'m386_a': (1.0, 1.0, 1.0), 'm386_b': (0x93 / 255, 0xc4 / 255, 0xba / 255), 'm386_c': (0xd8 / 255, 0xc4 / 255, 0x62 / 255)}
lin = RV.srgb_to_linear
enc = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)


def meshy(name, mode='RGB'):
    f = next(S.glob(f'*{name}*.png'))
    return C.load(f, mode)


part, _ = C.rasterise(np.load(P / 'work/uv3d.npz'), tol=0)
valid = part >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
pad = lambda a: np.where(valid[..., None] if a.ndim == 3 else valid, a, a[iy, ix])
base = pad(meshy('base_color'))
h, s, v = C.hsv(base)
eye = valid & (h > 80) & (h < 160) & (s > 0.5) & (v > 0.45)
emitter = valid & (h > 200) & (h < 280) & (s > 0.35) & (v > 0.3)
# glows keep their colour in every tier: saturated texels only (a dilated mask also caught the grey coil housing,
# whose luminance overlaps the blue and broke the ramp fit); a 1-texel dilation for metal/roughness only
eye_r = eye; emitter_r = emitter & ~eye
glow = ndimage.binary_dilation(eye | emitter, iterations=1) & valid
ao = ndimage.gaussian_filter(pad(np.asarray(Image.open(T / 'robot_ao.png').convert('L').resize(valid.shape[::-1]),
                                            np.float32) / 255), 1.0)
g = base * ((1 - AO_GRADE) + AO_GRADE * ao)[..., None]
g = pad(np.where(glow[..., None], base, g))
Image.fromarray((np.clip(g, 0, 1) * 255 + .5).astype(np.uint8)).save(T / 'robot_basecolor.png')

metal = pad(meshy('metallic', 'L'))
rough = pad(meshy('roughness', 'L'))
metal = np.minimum(metal, METAL_MAX)
metal[glow] = 0.0
rough[glow] = 0.35
rubber = valid & ~glow & (metal < 0.35) & (v < 0.2)
orm = np.dstack([pad(ao), rough, metal])
Image.fromarray((np.clip(orm, 0, 1) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS) \
    .save(T / 'robot_metal_rough.png')
classes = np.zeros(part.shape, np.uint8); classes[valid] = 9; classes[rubber] = 11; classes[glow] = 6
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'robot_material_classes.png')

normal = np.array(Image.open(next(S.glob('*normal*.png'))).convert('RGB'))
normal = (pad(normal.astype(np.float32) / 255) * 255 + .5).astype(np.uint8)
before = NM.measure(normal)
if before < -.1:
    normal[..., 1] = 255 - normal[..., 1]
Image.fromarray(normal).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'robot_normal.png')

# region mask: R green optics, G blue coils (padded into the gutters like the colour)
weights = [ndimage.gaussian_filter(pad(m.astype(np.float32)), 0.5) for m in (eye_r, emitter_r)]
RV.write_mask(weights, T / 'robot_region_mask.png')
gs = RV.load_srgb(T / 'robot_basecolor.png', 1024)
mk = np.stack([np.asarray(c, np.float32) / 255 for c in Image.open(T / 'robot_region_mask.png').split()], -1)
ramps = {n: [] for n in TINT}; reports = []
for ch in range(2):
    rep = {}
    for n, t in TINT.items():
        tinted = enc(lin(gs) * lin(np.array(t)))
        fitted, r = RV.fit_ramps(tinted, {n: gs}, mk[..., ch])
        ramps[n].append(fitted[n]); rep[n] = r[n]
    reports.append(rep)
factors = {n: [round(float(x), 6) for x in lin(np.array(t))] + [1.0] for n, t in TINT.items()}
(T / 'robot_ramps.json').write_text(json.dumps(dict(
    variants=list(TINT), tints=TINT, tint_factors=factors, regions=['green optics', 'blue coils'],
    materials=[dict(base='Robot_A', prefix='Robot', mask='robot_region_mask.png', ramps=ramps)], report=reports),
    indent=2) + '\n')
mv = metal[valid]
(P / 'review/texture_audit.json').write_text(json.dumps(dict(
    source='meshy/retexture_v2uv', normal_before=before, normal_after=NM.measure(normal),
    texels={k: int(x.sum()) for k, x in dict(valid=valid, eye=eye, emitter=emitter, rubber=rubber).items()},
    metallic=dict(mean=float(mv.mean()), p10=float(np.percentile(mv, 10)), p50=float(np.median(mv)),
                  p90=float(np.percentile(mv, 90)), cap=METAL_MAX),
    roughness=dict(mean=float(rough[valid].mean()), p10=float(np.percentile(rough[valid], 10)),
                   p90=float(np.percentile(rough[valid], 90))),
    glow_ramp_fit=reports), indent=2) + '\n')
print('COMPOSED', json.dumps(reports), round(before, 3), 'metal mean', round(float(mv.mean()), 3))
