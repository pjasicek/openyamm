#!/usr/bin/env python3
"""Texture sets from the 4K Meshy paints on our uv_atlas layouts (TEXTURE_QUALITY_PASS.md): body colour 4K -> 2K Lanczos once, head
colour 4K -> 1K, normal and roughness 1K, padded into the gutters; ORM = (AO, roughness, 0). Then the gentle grade
(grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15), region mask and ramps.
Regions (as the approved mm6_gua_claude tiers): R blue sleeves (hue-picked inside the shirt/forearm parts), G trousers, B mail shirt,
skirt, coif, belt and shoes. Ramp colours per tier are the approved ones (mm6_gua_claude/textures/gua_ramps.json, palettes 748/749/750);
each region's luminance range is refitted to the new paint (texel luminance p2..p98 over body and head together).
Material classes (1 skin, 8 cloth/leather, 9 metal) to textures/gua_material_classes.png and gua_head_material_classes.png.
Run in the project folder with the gltf venv python. Steps: --stage raw (writes *_raw.png for the grade), --stage final."""
import json, sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
T = Path('textures'); D = np.load('work/final_v1_uv.npz')
STAGE = sys.argv[sys.argv.index('--stage') + 1]
part, garm, head = D['part'], D['garm'], D['head'].astype(bool)


def raster(uv, faces, values, size):
    """per-texel face value (0 = empty) for the given faces"""
    im = Image.new('I', (size, size)); d = ImageDraw.Draw(im)
    for f, v in zip(faces, values):
        d.polygon([(float(u * size), float((1 - w) * size)) for u, w in uv[f]], fill=int(v))
    return np.asarray(im)


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def lum(rgb):
    lin = (rgb / 255.0) ** 2.2
    return lin @ np.array([0.2126, 0.7152, 0.0722])


bf = np.nonzero(~head)[0]; hf = np.nonzero(head)[0]
code = part * 100 + np.where(garm == 16, 16, 0)
if STAGE == 'raw':
    for key, job, faces, uvk, csize in (('gua', 'retexture_body_v1', bf, 'UV', 2048), ('gua_head', 'retexture_head_v1', hf, 'HU', 1024)):
        lab = raster(D[uvk], faces, code[faces] + 1, csize); cov = lab > 0
        lab1 = raster(D[uvk], faces, code[faces] + 1, 1024); cov1 = lab1 > 0
        col = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_base_color.png').convert('RGB').resize((csize, csize), Image.LANCZOS))
        nrm = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
        rgh = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        Image.fromarray(pad(col, cov)).save(T / f'{key}_raw.png')
        Image.fromarray(pad(nrm, cov1)).save(T / f'{key}_normal_1k.png')
        ao = np.asarray(Image.open(T / f'{key}_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        Image.merge('RGB', [Image.fromarray(pad(ao, cov1)), Image.fromarray(pad(np.maximum(rgh, 128), cov1)), Image.new('L', (1024, 1024), 0)]).save(T / f'{key}_metal_rough_1k.png')
        np.save(f'work/{key}_labels.npy', lab)
        print('RAW', key, 'atlas', round(float(cov.mean()) * 100, 1))
    sys.exit()
# ---- final: regions and ramps from the graded colour
OLD = json.load(open('../mm6_gua_claude/textures/gua_ramps.json'))['materials'][0]
sets = {}
for key, csize in (('gua', 2048), ('gua_head', 1024)):
    col = np.asarray(Image.open(T / f'{key}_raw_graded.png').convert('RGB')).astype(float)
    lab = np.load(f'work/{key}_labels.npy') - 1
    p = np.where(lab >= 0, lab // 100, 0); coif = (lab % 100) == 16
    hsv = np.asarray(Image.fromarray(col.astype(np.uint8)).convert('HSV')).astype(float)
    h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    blue = (h > 185) & (h < 265) & (s > 0.25) & np.isin(p, [1, 17])
    blue = ndimage.binary_opening(blue, iterations=1)
    R = blue.astype(float)
    G = (p == 5).astype(float)
    B = ((np.isin(p, [1, 7, 9, 6]) & ~blue) | ((p == 2) & coif)).astype(float)
    cls = np.where(lab < 0, 0, np.where(np.isin(p, [0, 2, 4, 17]) & ~coif, 1, np.where(np.isin(p, [3]) | ((p == 2) & coif) | (np.isin(p, [1, 7]) & ~blue), 9, 8)))
    cls = np.where((p == 17) & blue, 8, cls)
    hue_ok = [blue, (h > 140) & (h < 230), (h < 70) | (h > 330)]          # ranges from each region's own hue (Meshy paints skin specks on cloth)
    sets[key] = dict(col=col, lab=lab, masks=[R, G, B], cov=lab >= 0, cls=cls, hue_ok=hue_ok)
L = {key: lum(s['col']) for key, s in sets.items()}
ranges = []
for k in range(3):
    vals = np.concatenate([L[key][(s['masks'][k] > 0.5) & s['cov'] & s['hue_ok'][k]] for key, s in sets.items()])
    ranges.append([float(np.percentile(vals, 2)), float(np.percentile(vals, 99.7 if k == 1 else 98))])   # trousers: seam highlights hit the red/green top stops of B and C at p98
ramps = {t: [dict(range=[round(r[0], 6), round(r[1], 6)], colors=OLD['ramps'][t][k]['colors']) for k, r in enumerate(ranges)] for t in ('gua_a', 'gua_b', 'gua_c')}
sys.path.insert(0, '../claude_shared')
import region_variants as RV
mats = []
for key, base, prefix in (('gua', 'Guard_A', 'Guard'), ('gua_head', 'GuardHead_A', 'GuardHead')):
    s = sets[key]; size = s['cov'].shape[0]
    ms = []
    for m in s['masks']:
        m = pad(m, s['cov']); m = ndimage.gaussian_filter(m, 1.0 * size / 1024)
        ms.append(np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)) / 255.0)
    RV.write_mask(ms, T / f'{key}_region_mask.png', size=1024)
    Image.fromarray(np.asarray(Image.fromarray(s['cls'].astype(np.uint8)).resize((1024, 1024), Image.NEAREST))).save(T / f'{key}_material_classes.png')
    Image.fromarray(s['col'].astype(np.uint8)).save(T / f'{key}_basecolor.png')
    mats.append(dict(base=base, prefix=prefix, mask=f'{key}_region_mask.png', regions=['sleeves', 'trousers', 'mail'],
                     palettes=OLD['palettes'], ramps=ramps))
    print('FINAL', key, 'mask cover %', [round(float((m > 0.5).mean()) * 100, 1) for m in s['masks']])
json.dump(dict(variants=['gua_a', 'gua_b', 'gua_c'], materials=mats, note='colours: approved mm6_gua_claude ramps; ranges refitted p2..p98'), open(T / 'gua_ramps.json', 'w'), indent=1)
print('RANGES', [[round(x, 4) for x in r] for r in ranges])
