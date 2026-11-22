#!/usr/bin/env python3
"""Shared texture set, region masks and tier ramps for the Killer Sprite (CLAUDE_CREATURE_TEXTURES.md,
claude_shared/TEXTURE_QUALITY_PASS.md). Plain python (numpy, PIL, scipy).
Inputs: meshy/retexture_v1/texture_urls_0_{base_color,normal,roughness}.png (4K on our uv_atlas layout),
work/uv3d.npz (dump_uv3d.py), textures/sprite_ao_2k.png (bake_ao_sprite.py), textures/sprite_wing_basecolor.png and
sprite_wing_region_mask.png (prep_wings.py).
Body outputs: sprite_basecolor_2k.png (4K downsampled once, Lanczos) -> grade_basecolor.py (gentle) ->
sprite_basecolor_2k_graded.png; sprite_normal_1k.png; sprite_orm_1k.png (R baked AO, G roughness, B 0);
sprite_region_mask.png (1K RGBA: R skin, G hair, B dress; eyes in no region), sprite_material_classes.png
(1K, 1 skin, 2 hair, 6 eye, 8 cloth). Regions: pieces by UV raster (hair = piece 1, eyes = 3/4), skin vs dress vs
painted hairline on the body shell by hue (blue / magenta / pale teal), unsure texels (low saturation) by the
majority of their neighbourhood; each mask padded into the gutters before a 1-texel feather.
Tiers (lane S design): sprite_a Medusa Sprite = olive-green skin, dark green hair, green dress, green-tinted wings;
sprite_b Killer Sprite = the native colours (the paint itself, ramps fitted to the base); sprite_c Sprite Queen =
pale violet skin, gold-white hair, deep purple dress, lilac wings. A/C targets keep each texel's luminance relative
to its region's median and take the tier colour (sRGB mid-tones in TIERS); region_variants.fit_ramps fits the 16-stop
ramps to them. Writes textures/sprite_ramps.json (+ fit report) and review/tier_targets.png.
Args: none (run gutter_fill.py on every map afterwards: build_runtime.sh)."""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *p: os.path.join(HERE, *p)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
import region_variants as RV
M = P('meshy', 'retexture_v1')
T = P('textures')
TIERS = {   # sRGB mid-tone per region: skin, hair, dress, wing
    'sprite_a': {'skin': (104, 132, 62), 'hair': (40, 78, 42), 'dress': (54, 126, 50), 'wing': (128, 196, 120)},
    'sprite_c': {'skin': (182, 152, 216), 'hair': (238, 224, 172), 'dress': (74, 26, 104), 'wing': (196, 166, 236)},
}


def lin(c):
    return RV.srgb_to_linear(np.asarray(c, np.float64) / 255.0)


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - 0.055)


# ---------------------------------------------------------------- maps
base4 = Image.open(os.path.join(M, 'texture_urls_0_base_color.png')).convert('RGB')
print('MESHY base', base4.size)
base4.resize((2048, 2048), Image.LANCZOS).save(P('textures', 'sprite_basecolor_2k.png'))
Image.open(os.path.join(M, 'texture_urls_0_normal.png')).convert('RGB').resize((1024, 1024), Image.LANCZOS).save(P('textures', 'sprite_normal_1k.png'))
rough = np.asarray(Image.open(os.path.join(M, 'texture_urls_0_roughness.png')).convert('L').resize((1024, 1024), Image.LANCZOS))
ao = np.asarray(Image.open(P('textures', 'sprite_ao_2k.png')).convert('L').resize((1024, 1024), Image.LANCZOS))
subprocess.run([sys.executable, os.path.join(os.path.dirname(HERE), 'claude_shared', 'grade_basecolor.py'), '--ao', P('textures', 'sprite_ao_2k.png'),
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                P('textures', 'sprite_basecolor_2k.png')], check=True)
graded_path = P('textures', 'sprite_basecolor_2k_graded.png')
G = np.asarray(Image.open(graded_path).convert('RGB'), np.float64) / 255
# roughness: skin/dress matte, hair a touch softer sheen (specular is off on the creature anyway)
D = np.load(P('work', 'uv3d.npz'))
S = 2048


def raster(size, values, tris_uv):
    img = Image.new('I', (size, size), 0); dr = ImageDraw.Draw(img)
    for uv, v in zip(tris_uv, values):
        dr.polygon([tuple(p) for p in (uv * size)], fill=int(v), outline=int(v))
    return np.asarray(img)


piece = raster(S, D['piece'] + 1, D['uv']) - 1                     # -1 outside the islands
inside = piece >= 0
hsv = np.asarray(Image.fromarray((G * 255).astype(np.uint8)).convert('HSV'), np.float64)
hue, sat = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255
CLS = {'skin': 1, 'hair': 2, 'dress': 3}
lab = np.zeros((S, S), np.int32)
body = inside & np.isin(piece, (0, 2))
sure = body & (sat > 0.18)
lab[sure & (hue >= 185) & (hue < 262)] = CLS['skin']
lab[sure & ((hue >= 262) | (hue < 20))] = CLS['dress']
lab[sure & (hue >= 120) & (hue < 185) & (piece == 0)] = CLS['hair']
lab[inside & (piece == 1)] = CLS['hair']
lab[inside & (piece == 2) & (lab == 0)] = CLS['skin']             # legs: bare skin
# unsure body texels: majority of the labelled texels within 6 px
unsure = body & (lab == 0)
for k in (1, 2, 3):
    pass
votes = np.stack([ndimage.uniform_filter((lab == k).astype(np.float32), 13) for k in (1, 2, 3)])
lab[unsure] = (np.argmax(votes, 0) + 1)[unsure]
lab[unsure & (votes.max(0) < 1e-3)] = CLS['skin']
eyes = inside & np.isin(piece, (3, 4))
lab[eyes] = 0
print('REGIONS texels', {k: int((lab == v).sum()) for k, v in CLS.items()}, 'eyes', int(eyes.sum()), 'unsure', int(unsure.sum()))
# padded, feathered weights at 2K, mask written at 1K
idx = ndimage.distance_transform_edt(~inside, return_distances=False, return_indices=True)
labp = lab[idx[0], idx[1]]
weights = []
for k in (1, 2, 3):
    w = (labp == k).astype(np.float32)
    w = ndimage.gaussian_filter(w, 0.8)
    weights.append(w)
small = lambda w: np.asarray(Image.fromarray((w * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)) / 255
RV.write_mask([small(w) for w in weights], P('textures', 'sprite_region_mask.png'))
cls = np.zeros((S, S), np.uint8)
cls[lab == 1] = 1; cls[lab == 2] = 2; cls[lab == 3] = 8; cls[eyes] = 6
Image.fromarray(cls).resize((1024, 1024), Image.NEAREST).save(P('textures', 'sprite_material_classes.png'))
orm = np.zeros((1024, 1024, 3), np.uint8)
orm[..., 0] = ao; orm[..., 1] = np.clip(rough.astype(np.float64) * 0.9 + 20, 0, 255).astype(np.uint8); orm[..., 2] = 0
Image.fromarray(orm).save(P('textures', 'sprite_orm_1k.png'))


# ---------------------------------------------------------------- ramps
def recolour(base, w, mid):
    L = RV.luminance(base)
    core = w > 0.9
    Lm = float(np.median(L[core]))
    tgt_lin = lin(mid)[None, None, :] * (L / max(Lm, 1e-4))[..., None]
    t = to_srgb(tgt_lin)
    return np.where(w[..., None] > 0, t, base)


report = {}
body_ramps = {'sprite_a': [], 'sprite_b': [], 'sprite_c': []}
names = ['skin', 'hair', 'dress']
previews = {}
for k, (nm, w) in enumerate(zip(names, weights)):
    tiers = {'sprite_b': G, 'sprite_a': recolour(G, w, TIERS['sprite_a'][nm]), 'sprite_c': recolour(G, w, TIERS['sprite_c'][nm])}
    ramps, err = RV.fit_ramps(G, tiers, w)
    for v in body_ramps:
        body_ramps[v].append(ramps[v])
    report[nm] = err
    for v, im in tiers.items():
        previews.setdefault(v, G.copy())
        previews[v] = np.where(w[..., None] > 0.5, im, previews[v])
WB = np.asarray(Image.open(P('textures', 'sprite_wing_basecolor.png')).convert('RGB'), np.float64) / 255
ww = np.asarray(Image.open(P('textures', 'sprite_wing_region_mask.png')))[..., 0] / 255.0
wt = {'sprite_b': WB, 'sprite_a': recolour(WB, ww, TIERS['sprite_a']['wing']), 'sprite_c': recolour(WB, ww, TIERS['sprite_c']['wing'])}
wing_ramps, werr = RV.fit_ramps(WB, wt, ww)
report['wing'] = werr
print('RAMPFIT', json.dumps(report)[:900])
out = {'variants': ['sprite_a', 'sprite_b', 'sprite_c'],
       'materials': [{'base': 'Sprite_A', 'prefix': 'Sprite', 'mask': 'sprite_region_mask.png',
                      'regions': names, 'ramps': body_ramps},
                     {'base': 'Wing_A', 'prefix': 'Wing', 'mask': 'sprite_wing_region_mask.png',
                      'regions': ['membrane'], 'ramps': {v: [wing_ramps[v]] for v in wing_ramps}}],
       'tiers': {'sprite_a': 'Medusa Sprite', 'sprite_b': 'Killer Sprite', 'sprite_c': 'Sprite Queen'},
       'tier_colours_srgb': TIERS, 'fit_report': report}
json.dump(out, open(P('textures', 'sprite_ramps.json'), 'w'), indent=1)
sheet = np.concatenate([previews[v] for v in ('sprite_a', 'sprite_b', 'sprite_c')], 1)
Image.fromarray((sheet * 255).astype(np.uint8)).resize((1536, 512), Image.LANCZOS).save(P('review', 'tier_targets.png'))
wsheet = np.concatenate([wt[v] for v in ('sprite_a', 'sprite_b', 'sprite_c')], 1)
Image.fromarray((wsheet * 255).astype(np.uint8)).resize((1536, 512), Image.LANCZOS).save(P('review', 'tier_targets_wing.png'))
print('COMPOSED')
