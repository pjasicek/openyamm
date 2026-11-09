"""MM7 dragonfly textures from meshy/retexture_v1 (Codex HD masters) on our UVs (work/uv3d.npz, piece ids).
- base colour 2K: Meshy colour padded into the gutters, AO-graded (textures/dfly_ao.png, 0.6), mild contrast and
  saturation (no local contrast: small Smart UV islands);
- region mask R = green spine crest (green texels outside the wings), padded and feathered;
- tier ramps (textures/dfly_ramps.json): crest texels ranked by luminance take the native crest colours of the same
  rank (palette indices 228-255 of the fly frames m186w*) in palettes 187 / 188 / 189, gain GAIN; everything else
  (chitin, eyes, mandibles, bristles, claw, wings) is the same in every tier, as in the native palettes;
- metal/rough 1K (R specular mask, G roughness, B 0), material classes 1K, normal 1K (+Y up)."""
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
GAIN = 1.25
part, xyz = C.rasterise(np.load(P / 'work/uv3d.npz'), tol=0)
valid = part >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
pad = lambda a: np.where(valid[..., None] if a.ndim == 3 else valid, a, a[iy, ix])
base = pad(C.load(S / 'texture_urls_0_base_color.png'))
h, s, v = C.hsv(base)
wing = valid & np.isin(part, [1, 2, 4, 5])
crest = valid & ~wing & (h >= 75) & (h <= 170) & (s > 0.25)
eye = valid & ~wing & ((h < 25) | (h > 345)) & (s > 0.55) & (v > 0.45)
ivory = valid & ~wing & ~crest & (s < 0.25) & (v > 0.55)
bristle = valid & ~wing & ~crest & ~eye & (h >= 35) & (h < 60) & (s > 0.35) & (v > 0.45)
chitin = valid & ~wing & ~crest & ~eye & ~ivory & ~bristle
ao = ndimage.gaussian_filter(pad(np.asarray(Image.open(T / 'dfly_ao.png').convert('L'), np.float32) / 255), 1.5)
g = base * (0.4 + 0.6 * ao)[..., None]
g = np.where(wing[..., None], base, g)                       # thin wings: no AO darkening
mean = (g @ RV.LUMA)[valid].mean()
g = np.clip((g - mean) * 1.08 + mean, 0, 1); grey = (g @ RV.LUMA)[..., None]
g = pad(np.clip(grey + (g - grey) * 1.12, 0, 1))
Image.fromarray((g * 255 + .5).astype(np.uint8)).save(T / 'dfly_basecolor.png')
RV.write_mask([ndimage.gaussian_filter(pad(crest.astype(np.float32)), 1.0)], T / 'dfly_region_mask.png')
classes = np.zeros(part.shape, np.uint8)
classes[chitin] = 1; classes[bristle] = 2; classes[wing] = 3; classes[crest] = 4; classes[ivory] = 5; classes[eye] = 6
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'dfly_material_classes.png')
pc = pad(classes)
rough = np.array([.8, .55, .75, .35, .5, .4, .15, .6, .8, .3, .8, .8], np.float32)[pc]
spec = np.array([0, .35, .05, .6, .4, .5, .9, .2, .05, 1, .05, .05], np.float32)[pc]
orm = np.dstack([spec, rough, np.zeros_like(rough)])
Image.fromarray((orm * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'dfly_metal_rough.png')
normal = np.array(Image.open(S / 'texture_urls_0_normal.png').convert('RGB'))
normal = np.array(Image.fromarray((pad(normal.astype(np.float32) / 255) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1: normal[..., 1] = 255 - normal[..., 1]
Image.fromarray(normal).save(T / 'dfly_normal.png')
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8)
       .reshape(256, 3) / 255 for pid in (187, 188, 189)}
idx = np.concatenate([np.asarray(Image.open(f)).ravel() for f in sorted(glob.glob(str(REPO / 'assets_dev/engine/sprites/m186w?[0-4].bmp')))])
ids = idx[(idx >= 228)]
gs = RV.load_srgb(T / 'dfly_basecolor.png', 1024)
mk = np.asarray(Image.open(T / 'dfly_region_mask.png').split()[0], np.float32) / 255
core = mk >= .9; L = RV.luminance(gs)
order = np.argsort(L[core]); rank = np.empty(order.size); rank[order] = (np.arange(order.size) + .5) / order.size
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)
variants = {'m186_a': 187, 'm186_b': 188, 'm186_c': 189}
targets = {}
for name, pid in variants.items():
    cols = RV.srgb_to_linear(np.clip(pal[pid][ids] * GAIN, 0, 1)); cols = cols[np.argsort(cols @ RV.LUMA)]
    q = .03 + .95 * rank; t = gs.copy()
    t[core] = encode(np.clip(cols[np.minimum((q * len(cols)).astype(int), len(cols) - 1)], 0, 1)); targets[name] = t
fitted, report = RV.fit_ramps(gs, targets, mk)
(T / 'dfly_ramps.json').write_text(json.dumps(dict(
    variants=list(variants), palettes=variants, regions=['green spine crest'],
    materials=[dict(base='Dragonfly_A', prefix='Dragonfly', mask='dfly_region_mask.png', ramps={n: [fitted[n]] for n in variants})],
    gain=GAIN, native_samples=int(len(ids)), report=report), indent=2) + '\n')
(P / 'review/texture_audit.json').write_text(json.dumps(dict(normal_before=before, normal_after=NM.measure(normal),
    texels={k: int(x.sum()) for k, x in dict(wing=wing, crest=crest, eye=eye, ivory=ivory, bristle=bristle, chitin=chitin).items()},
    region_fit=report), indent=2) + '\n')
print('COMPOSED', report, round(before, 3), {k: int(x.sum()) for k, x in dict(crest=crest, eye=eye, ivory=ivory, bristle=bristle).items()})
