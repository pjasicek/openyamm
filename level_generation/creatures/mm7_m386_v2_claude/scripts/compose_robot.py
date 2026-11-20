"""MM7 robot textures from meshy/retexture_v1 (Codex HD masters) on our UVs (work/uv3d.npz).
Tiers: all three descriptors use palette 386; the original engine multiplies tiers B and C by the descriptor
TintColor (Sentinel 0x93c4ba, Assassin 0xd8c462; OpenEnroth BaseRenderer BlendColors), which OpenYAMM parses but does
not apply. The model reproduces that multiply with region ramps fitted to base x tint (linear) per material region:
R steel / gunmetal / orb (low saturation), G bronze and brass (vertebrae, sleeves, skull), B rust-red arm plates.
The green eye and the blue gun emitter stay out of every region (the glows keep their colour). Tier A ramps fit the
untinted base.
Also: AO grade, material classes (metal 9, rubber cables 11, eye/glow 6), metal/rough (R specular mask, G roughness,
B 0: glossy, not metallic, per the Patrol Unit), normal 1K."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]; REPO = P.parents[2]
sys.path[:0] = [str(P.parent / 'mm6_gob_claude/scripts'), str(P.parent / 'claude_shared'), str(REPO / 'tools')]
import compose_textures_v2 as C
import region_variants as RV
import normal_map_convention as NM
T = P / 'textures'; S = P / 'meshy/retexture_v1'
TINT = {'m386_a': (1.0, 1.0, 1.0), 'm386_b': (0x93 / 255, 0xc4 / 255, 0xba / 255), 'm386_c': (0xd8 / 255, 0xc4 / 255, 0x62 / 255)}
part, xyz = C.rasterise(np.load(P / 'work/uv3d.npz'), tol=0)
valid = part >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
pad = lambda a: np.where(valid[..., None] if a.ndim == 3 else valid, a, a[iy, ix])
base = pad(C.load(S / 'texture_urls_0_base_color.png'))
h, s, v = C.hsv(base)
eye = valid & (h > 80) & (h < 160) & (s > 0.5) & (v > 0.45)
emitter = valid & (h > 200) & (h < 280) & (s > 0.35) & (v > 0.3)
glow = ndimage.binary_dilation(eye | emitter, iterations=2) & valid
steel = valid & ~glow & (s <= 0.3)
bronze = valid & ~glow & ~steel & (h >= 20) & (h < 80)
rust = valid & ~glow & ~steel & ~bronze
rubber = steel & (v < 0.16)
ao = ndimage.gaussian_filter(pad(np.asarray(Image.open(T / 'robot_ao.png').convert('L'), np.float32) / 255), 1.5)
g = base * (0.45 + 0.55 * ao)[..., None]
g = np.where(glow[..., None], base, g)
mean = (g @ RV.LUMA)[valid].mean()
g = np.clip((g - mean) * 1.06 + mean, 0, 1); grey = (g @ RV.LUMA)[..., None]
g = pad(np.clip(grey + (g - grey) * 1.08, 0, 1))
Image.fromarray((g * 255 + .5).astype(np.uint8)).save(T / 'robot_basecolor.png')
weights = [ndimage.gaussian_filter(pad(m.astype(np.float32)), 0.8) for m in (steel, bronze, rust)]
for w in weights:
    w[ndimage.binary_dilation(glow, iterations=1)] = 0
RV.write_mask(weights, T / 'robot_region_mask.png')
classes = np.zeros(part.shape, np.uint8); classes[valid] = 9; classes[rubber] = 11; classes[glow] = 6
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'robot_material_classes.png')
pc = pad(classes)
rough = np.array([.8, .6, .8, .7, .45, .35, .15, .6, .8, .42, .8, .72], np.float32)[pc]
spec = np.array([0, .3, .05, .2, .5, .6, .9, .2, .05, .85, .05, .12], np.float32)[pc]
orm = np.dstack([spec, rough, np.zeros_like(rough)])
Image.fromarray((orm * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'robot_metal_rough.png')
normal = np.array(Image.open(S / 'texture_urls_0_normal.png').convert('RGB'))
normal = np.array(Image.fromarray((pad(normal.astype(np.float32) / 255) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1: normal[..., 1] = 255 - normal[..., 1]
Image.fromarray(normal).save(T / 'robot_normal.png')
gs = RV.load_srgb(T / 'robot_basecolor.png', 1024)
mk = np.stack([np.asarray(c, np.float32) / 255 for c in Image.open(T / 'robot_region_mask.png').split()], -1)
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)
lin = RV.srgb_to_linear(gs)
ramps = {n: [] for n in TINT}; reports = []
for ch in range(3):
    targets = {n: encode(np.clip(lin * np.array(t), 0, 1)) for n, t in TINT.items()}
    fitted, rep = RV.fit_ramps(gs, targets, mk[..., ch])
    for n in TINT: ramps[n].append(fitted[n])
    reports.append(rep)
(T / 'robot_ramps.json').write_text(json.dumps(dict(
    variants=list(TINT), tints=TINT, regions=['steel/gunmetal/orb', 'bronze/brass', 'rust-red plates'],
    materials=[dict(base='Robot_A', prefix='Robot', mask='robot_region_mask.png', ramps=ramps)], report=reports), indent=2) + '\n')
(P / 'review/texture_audit.json').write_text(json.dumps(dict(normal_before=before, normal_after=NM.measure(normal),
    texels={k: int(x.sum()) for k, x in dict(steel=steel, bronze=bronze, rust=rust, rubber=rubber, eye=eye, emitter=emitter).items()},
    region_fit=reports), indent=2) + '\n')
print('COMPOSED', reports, round(before, 3))
