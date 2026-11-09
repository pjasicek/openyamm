"""MM7 beholder textures from meshy/retexture_v1 (Codex HD masters) on our UVs (work/uv3d.npz, Meshy piece ids).
Regions (one shared skin; ramps in textures/bh_ramps.json):
  R tentacle tips (green texels on the tentacles): per tier, native tip colours (palette indices 141-239 that are
    green in palette 167) read in palettes 167 / 168 / 169, by luminance rank;
  G head flesh (head piece, not eye, tongue, teeth or drool): native brown flesh (indices 16-111), SAME in every
    tier, so the reddish Meshy flesh reads as the sprite's brown;
  B tentacle shafts (tentacle pieces, not green): native grey shafts (low-saturation indices), same in every tier.
Eyes (central iris and the stalk eyes), stalks, tongue, teeth and drool keep their own paint and are in no region.
Base colour 2K AO-graded, metal/rough 1K (R specular mask, G roughness), material classes 1K, normal 1K (+Y up)."""
import json, sys, glob, colorsys
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
GAIN = {'tips': 1.25, 'flesh': 1.4, 'shaft': 1.35}
TENT = [1, 2, 3, 4, 5, 6, 9, 10, 14]; STALK = [7, 8, 12, 13]
part, xyz = C.rasterise(np.load(P / 'work/uv3d.npz'), tol=0)
valid = part >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
pad = lambda a: np.where(valid[..., None] if a.ndim == 3 else valid, a, a[iy, ix])
base = pad(C.load(S / 'texture_urls_0_base_color.png'))
h, s, v = C.hsv(base)
iris = np.array(json.load(open(P / 'work/iris.json'))['iris_centre'])
tent = valid & np.isin(part, TENT); headp = valid & (part == 0); stalk = valid & np.isin(part, STALK)
tips = tent & (h >= 70) & (h <= 170) & (s > 0.25)
eye = headp & (np.linalg.norm(xyz - iris, axis=-1) < 0.055)
drool = valid & (h >= 38) & (h < 70) & (s > 0.45) & (v > 0.45)
teeth = valid & (part >= 15); tongue = valid & (part == 11)
flesh = headp & ~eye & ~drool
shaft = tent & ~tips
ao = ndimage.gaussian_filter(pad(np.asarray(Image.open(T / 'bh_ao.png').convert('L'), np.float32) / 255), 1.5)
g = base * (0.4 + 0.6 * ao)[..., None]
mean = (g @ RV.LUMA)[valid].mean()
g = np.clip((g - mean) * 1.08 + mean, 0, 1); grey = (g @ RV.LUMA)[..., None]
g = pad(np.clip(grey + (g - grey) * 1.1, 0, 1))
Image.fromarray((g * 255 + .5).astype(np.uint8)).save(T / 'bh_basecolor.png')
masks = [ndimage.gaussian_filter(pad(m.astype(np.float32)), 1.0) for m in (tips, flesh, shaft)]
RV.write_mask(masks, T / 'bh_region_mask.png')
classes = np.zeros(part.shape, np.uint8)
classes[flesh | shaft | stalk] = 1; classes[tips] = 1; classes[teeth] = 5; classes[tongue] = 7; classes[eye] = 6
classes[stalk & (s < 0.25) & (v > 0.6)] = 6; classes[drool] = 11
Image.fromarray(classes).resize((1024, 1024), Image.Resampling.NEAREST).save(T / 'bh_material_classes.png')
pc = pad(classes)
rough = np.array([.8, .45, .75, .7, .5, .35, .12, .35, .8, .3, .8, .2], np.float32)[pc]
spec = np.array([0, .55, .05, .2, .4, .6, 1, .7, .05, 1, .05, .9], np.float32)[pc]
orm = np.dstack([spec, rough, np.zeros_like(rough)])
Image.fromarray((orm * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS).save(T / 'bh_metal_rough.png')
normal = np.array(Image.open(S / 'texture_urls_0_normal.png').convert('RGB'))
normal = np.array(Image.fromarray((pad(normal.astype(np.float32) / 255) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.Resampling.LANCZOS))
before = NM.measure(normal)
if before < -.1: normal[..., 1] = 255 - normal[..., 1]
Image.fromarray(normal).save(T / 'bh_normal.png')
pal = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm7/textures/pal{pid}.act').read_bytes()[:768], np.uint8)
       .reshape(256, 3) / 255 for pid in (167, 168, 169)}
idx = np.concatenate([np.asarray(Image.open(f)).ravel() for f in sorted(glob.glob(str(REPO / 'assets_dev/engine/sprites/m166w?[0-4].bmp')))])
idx = idx[idx != 0]
hsv = np.array([colorsys.rgb_to_hsv(*c) for c in pal[167]])
IDS = {'tips': idx[(idx >= 141) & (idx <= 239) & (hsv[idx, 0] * 360 > 90) & (hsv[idx, 0] * 360 < 170) & (hsv[idx, 1] > .35)],
       'flesh': idx[(idx >= 16) & (idx <= 111) & (hsv[idx, 1] > .2)],
       'shaft': idx[(hsv[idx, 1] < .2) & (hsv[idx, 2] > .15) & ~((idx >= 141) & (idx <= 239) & (hsv[idx, 1] > .35))]}
gs = RV.load_srgb(T / 'bh_basecolor.png', 1024)
mk = np.stack([np.asarray(c, np.float32) / 255 for c in Image.open(T / 'bh_region_mask.png').split()], -1)
L = RV.luminance(gs)
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)
variants = {'m166_a': 167, 'm166_b': 168, 'm166_c': 169}
ramps = {n: [] for n in variants}; reports = []
for ch, region in enumerate(('tips', 'flesh', 'shaft')):
    core = mk[..., ch] >= .9
    order = np.argsort(L[core]); rank = np.empty(order.size); rank[order] = (np.arange(order.size) + .5) / order.size
    targets = {}
    for name, pid in variants.items():
        src = pid if region == 'tips' else 167
        cols = RV.srgb_to_linear(np.clip(pal[src][IDS[region]] * GAIN[region], 0, 1)); cols = cols[np.argsort(cols @ RV.LUMA)]
        q = .03 + .95 * rank; t = gs.copy()
        t[core] = encode(np.clip(cols[np.minimum((q * len(cols)).astype(int), len(cols) - 1)], 0, 1)); targets[name] = t
    fitted, rep = RV.fit_ramps(gs, targets, mk[..., ch])
    for n in variants: ramps[n].append(fitted[n])
    reports.append({'region': region, 'native_samples': int(len(IDS[region])), 'fit': rep})
(T / 'bh_ramps.json').write_text(json.dumps(dict(variants=list(variants), palettes=variants,
    regions=['tentacle tips (per tier)', 'head flesh (native brown, all tiers)', 'tentacle shafts (native grey, all tiers)'],
    materials=[dict(base='Beholder_A', prefix='Beholder', mask='bh_region_mask.png', ramps=ramps)], gain=GAIN, report=reports), indent=2) + '\n')
(P / 'review/texture_audit.json').write_text(json.dumps(dict(normal_before=before, normal_after=NM.measure(normal),
    texels={k: int(x.sum()) for k, x in dict(tips=tips, flesh=flesh, shaft=shaft, eye=eye, drool=drool).items()}, region_fit=reports), indent=2) + '\n')
print('COMPOSED', json.dumps(reports)[:900], round(before, 3))
