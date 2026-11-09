"""MM7 bat textures from meshy/retexture_v1 (Codex HD masters) on our UVs (work/uv3d.npz).
- base colour 2K: Meshy colour padded into the gutters, graded with the rest-pose AO (textures/bat_ao.png):
  AO 0.6, mild contrast/saturation, no local contrast (the Smart UV atlas has many small islands);
- region mask (R = wing membrane: green texels), padded into the gutters, then feathered;
- tier ramps (textures/bat_ramps.json): the membrane's texels ranked by luminance take the native membrane colours of
  the same rank (palette indices 64-207 in the native fly frames m158w*), read in palettes 159 / 160 / 161, albedo
  gain GAIN; fur, ears, bones, eyes and teeth are the same in every tier (as the native palettes);
- metal/rough 1K: R engine specular mask, G roughness by material class, B 0; material classes 1K; normal 1K (+Y up)."""
import json, sys, glob
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
GAIN = 1.3
part, xyz = C.rasterise(np.load(P / 'work/uv3d.npz'), tol=0)
valid = part >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
pad = lambda a: np.where(valid[..., None] if a.ndim == 3 else valid, a, a[iy, ix])
base = pad(C.load(S / 'texture_urls_0_base_color.png'))
h, s, v = C.hsv(base)
membrane = valid & (h >= 60) & (h <= 180) & (s > 0.15)
eye = valid & (part == 2) & ((h < 12) | (h > 345)) & (s > 0.6) & (v > 0.35)
tooth = valid & (part == 2) & (s < 0.18) & (v > 0.62)
pink = valid & ~membrane & ~eye & (((h < 30) | (h > 330)) & (s > 0.22))
fur = valid & ~membrane & ~eye & ~tooth & ~pink
# grade: AO and mild global contrast / saturation
ao = np.asarray(Image.open(T / 'bat_ao.png').convert('L'), np.float32) / 255
ao = ndimage.gaussian_filter(pad(ao), 1.5)
graded = base * (1 - 0.6 + 0.6 * ao)[..., None]
lum = graded @ RV.LUMA
mean = lum[valid].mean()
graded = np.clip((graded - mean) * 1.08 + mean, 0, 1)
grey = (graded @ RV.LUMA)[..., None]
graded = np.clip(grey + (graded - grey) * 1.12, 0, 1)
graded = pad(graded)
Image.fromarray((graded * 255 + .5).astype(np.uint8)).save(T / 'bat_basecolor.png')
# region mask, padded then feathered
m = pad(membrane.astype(np.float32))
m = ndimage.gaussian_filter(m, 1.0)
RV.write_mask([m], T / 'bat_region_mask.png')
# classes and ORM
classes = np.zeros(part.shape, np.uint8)
classes[fur] = 2; classes[pink] = 1; classes[membrane] = 3; classes[tooth] = 5; classes[eye] = 6
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'bat_material_classes.png')
pc = pad(classes)
rough = np.array([.8, .62, .8, .7, .45, .35, .18, .6, .8, .3, .8, .8], np.float32)[pc]
spec = np.array([0, .25, .05, .2, .5, .6, .9, .2, .05, 1, .05, .05], np.float32)[pc]
orm = np.dstack([spec, rough, np.zeros_like(rough)])
Image.fromarray((orm * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'bat_metal_rough.png')
normal = np.array(Image.open(S / 'texture_urls_0_normal.png').convert('RGB'))
normal = (pad(normal.astype(np.float32) / 255) * 255 + .5).astype(np.uint8)
normal = np.array(Image.fromarray(normal).resize((1024, 1024), Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1:
    normal[..., 1] = 255 - normal[..., 1]
Image.fromarray(normal).save(T / 'bat_normal.png')
# ramps
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8)
       .reshape(256, 3) / 255 for pid in (159, 160, 161)}
idx = np.concatenate([np.asarray(Image.open(f)).ravel() for f in sorted(glob.glob(str(REPO / 'assets_dev/engine/sprites/m158w?[0-4].bmp')))])
ids = idx[(idx >= 64) & (idx <= 207)]
g = RV.load_srgb(T / 'bat_basecolor.png', 1024)
mk = np.asarray(Image.open(T / 'bat_region_mask.png').split()[0], np.float32) / 255
core = mk >= .9; L = RV.luminance(g)
order = np.argsort(L[core]); rank = np.empty(order.size); rank[order] = (np.arange(order.size) + .5) / order.size
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)
variants = {'m158_a': 159, 'm158_b': 160, 'm158_c': 161}
targets = {}
for name, pid in variants.items():
    cols = RV.srgb_to_linear(np.clip(pal[pid][ids] * GAIN, 0, 1)); cols = cols[np.argsort(cols @ RV.LUMA)]
    q = .03 + .95 * rank; t = g.copy()
    t[core] = encode(np.clip(cols[np.minimum((q * len(cols)).astype(int), len(cols) - 1)], 0, 1)); targets[name] = t
fitted, report = RV.fit_ramps(g, targets, mk)
config = dict(variants=list(variants), palettes=variants, regions=['wing membrane'],
              materials=[dict(base='Bat_A', prefix='Bat', mask='bat_region_mask.png',
                              ramps={n: [fitted[n]] for n in variants})], gain=GAIN, native_samples=int(len(ids)),
              report=report)
(T / 'bat_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
(P / 'review/texture_audit.json').write_text(json.dumps(dict(
    normal_before=before, normal_after=NM.measure(normal),
    texels={k: int(x.sum()) for k, x in dict(membrane=membrane, fur=fur, pink=pink, eye=eye, tooth=tooth).items()},
    region_fit=report), indent=2) + '\n')
print('COMPOSED', report, 'normal', round(before, 3))
