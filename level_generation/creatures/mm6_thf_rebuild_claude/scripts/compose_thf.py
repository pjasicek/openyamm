#!/usr/bin/env python3
"""Texture sets from the 4K Meshy paints on our uv_atlas layouts (TEXTURE_QUALITY_PASS.md; mm6_gua_rebuild_claude/scripts/compose_gua.py):
body colour 4K -> 2K Lanczos once, head colour 4K -> 1K, normal and roughness 1K, padded into the gutters; ORM = (AO, roughness, 0).
Gentle grade (grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15) on both sets.
The approved dagger paint (old body atlas column u 0.925..0.995, 2026-10-14) turned into the top strip (v 0.935..0.995 Blender) of the body
colour, normal and ORM after the grade.
Tier region (as the installed thief: one cloth region, palettes 825/826/827, the installed ramp colours): the cloak and hood (part 14), the
green undershirt texels of the torso and jerkin skirt (hue 70..200, saturation > 0.12). Range refitted to the new paint (p2..p98).
Run in the project folder with the gltf venv python: --stage raw, then --stage final."""
import json, sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
T = Path('textures'); D = np.load('work/final_v1_uv.npz')
STAGE = sys.argv[sys.argv.index('--stage') + 1]
part, head = D['part'], D['head'].astype(bool)
STRIP = (0.935, 0.06); OLD_COL = (0.925, 0.07)


def raster(uv, faces, values, size):
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


def paste_daggers(img, old):
    """img: target array (H, W[, C]); old: the old 1K body image array. Strip rows <- old column, turned (along the old v -> new u)."""
    Hn, Wn = img.shape[:2]; Ho, Wo = old.shape[:2]
    y0 = int(np.floor((1 - (STRIP[0] + STRIP[1])) * Hn)) - 2; y1 = int(np.ceil((1 - STRIP[0]) * Hn)) + 2
    ys, xs = np.mgrid[y0:y1, 0:Wn]
    vb = 1 - (ys + 0.5) / Hn; ub = (xs + 0.5) / Wn
    across = np.clip((vb - STRIP[0]) / STRIP[1], 0, 1); along = np.clip((ub - 0.005) / 0.99, 0, 1)
    xo = np.clip(((OLD_COL[0] + across * OLD_COL[1]) * Wo).astype(int), 0, Wo - 1); yo = np.clip((along * Ho).astype(int), 0, Ho - 1)
    img[y0:y1] = old[yo, xo]
    return img


bf = np.nonzero(~head)[0]; hf = np.nonzero(head)[0]
if STAGE == 'raw':
    for key, job, faces, uvk, csize in (('thf', 'retexture_body_v1', bf, 'UV', 2048), ('thf_head', 'retexture_head_v1', hf, 'HU', 1024)):
        lab = raster(D[uvk], faces, part[faces] + 1, csize); cov = lab > 0
        lab1 = raster(D[uvk], faces, part[faces] + 1, 1024); cov1 = lab1 > 0
        col = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_base_color.png').convert('RGB').resize((csize, csize), Image.LANCZOS))
        nrm = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
        rgh = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        Image.fromarray(pad(col, cov)).save(T / f'{key}_raw.png')
        nrm = pad(nrm, cov1); ao = np.asarray(Image.open(T / f'{key}_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        orm = np.dstack([pad(ao, cov1), pad(np.maximum(rgh, 128), cov1), np.zeros((1024, 1024), np.uint8)])
        if key == 'thf':
            nrm = paste_daggers(nrm, np.asarray(Image.open('textures/old/old_body_normal.png').convert('RGB')))
            orm = paste_daggers(orm, np.asarray(Image.open('textures/old/old_body_orm.png').convert('RGB')))
        Image.fromarray(nrm).save(T / f'{key}_normal_1k.png')
        Image.fromarray(orm.astype(np.uint8)).save(T / f'{key}_metal_rough_1k.png')
        np.save(f'work/{key}_labels.npy', lab)
        print('RAW', key, 'atlas', round(float(cov.mean()) * 100, 1))
    for key in ('thf', 'thf_head'):
        subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / f'{key}_ao.png'), '--fine', '1.0', '--local', '0.3',
                               '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15', str(T / f'{key}_raw.png')])
    sys.exit()
# ---- final: dagger strip, region and ramps from the graded colour
OLD = json.load(open('../mm6_thf_reduce_claude/textures/thf_ramps.json'))['materials'][0]
key = 'thf'
col = np.asarray(Image.open(T / f'{key}_raw_graded.png').convert('RGB')).copy()
col = paste_daggers(col, np.asarray(Image.open('textures/old/old_body_color.png').convert('RGB')))
lab = np.load(f'work/{key}_labels.npy') - 1
p = np.where(lab >= 0, lab, -1)
# the grafted hands (part 0) and wrist skin (part 4): Meshy painted them near white; their median goes to the face's skin median (head set)
hcol = np.asarray(Image.open(T / 'thf_head_raw_graded.png').convert('RGB')).astype(float)
hhsv = np.asarray(Image.open(T / 'thf_head_raw_graded.png').convert('HSV')).astype(float)
hl = np.load('work/thf_head_labels.npy') - 1
sk = (hl >= 0) & (hhsv[..., 0] < 30) & (hhsv[..., 1] > 50) & (hhsv[..., 2] > 90)
hand = np.isin(p, [0, 4])
_d, (_iy, _ix) = ndimage.distance_transform_edt(p < 0, return_indices=True)
hand = hand | ((p < 0) & (_d <= 6) & np.isin(p[_iy, _ix], [0, 4]))          # the islands' unrasterised rims and gutters too (pale seams otherwise)
gain = np.median(hcol[sk], 0) / np.maximum(np.median(col[np.isin(p, [0, 4])].astype(float), 0), 1)
col = col.astype(float); col[hand] = np.clip(col[hand] * gain, 0, 255); col = col.astype(np.uint8)
print('HANDS gain', gain.round(3).tolist())
hsv = np.asarray(Image.fromarray(col.astype(np.uint8)).convert('HSV')).astype(float)
h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
green = (h > 70) & (h < 200) & (s > 0.12) & np.isin(p, [1, 7])
green = ndimage.binary_opening(green, iterations=1)
R = ((p == 14) | green).astype(float)
cov = lab >= 0
cls = np.where(lab < 0, 0, np.where(np.isin(p, [4]), 1, np.where(np.isin(p, [30, 12]), 9, 8)))
L = lum(col.astype(float))
vals = L[(R > 0.5) & cov]
rng = [float(np.percentile(vals, 2)), float(np.percentile(vals, 98))]
ramps = {t: [dict(range=[round(rng[0], 6), round(rng[1], 6)], colors=OLD['ramps'][t][0]['colors'])] for t in ('thf_a', 'thf_b', 'thf_c')}
sys.path.insert(0, '../claude_shared')
import region_variants as RV
m = pad(R, cov); m = ndimage.gaussian_filter(m, 2.0)
m[: int(np.ceil((1 - STRIP[0]) * 2048)) + 4] = 0                      # never the daggers
RV.write_mask([np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)) / 255.0], T / f'{key}_region_mask.png', size=1024)
Image.fromarray(np.asarray(Image.fromarray(cls.astype(np.uint8)).resize((1024, 1024), Image.NEAREST))).save(T / f'{key}_material_classes.png')
Image.fromarray(col.astype(np.uint8)).save(T / f'{key}_basecolor.png')
hc = np.asarray(Image.open(T / 'thf_head_raw_graded.png').convert('RGB')).astype(float)
# Meshy painted the skull and temples inside the hood as the hood's grey-green cloth (the references show the hood); the masters show dark
# brown hair there: grey-green texels (hue 40..140) become hair, their luminance detail kept
hh = np.asarray(Image.open(T / 'thf_head_raw_graded.png').convert('HSV')).astype(float)
hue = hh[..., 0] * 360 / 255
cloth = (hue > 40) & (hue < 140)
cloth = ndimage.binary_opening(cloth, iterations=1)
Lh = hc @ np.array([0.299, 0.587, 0.114]); ref = np.median(Lh[cloth]) if cloth.any() else 1
HAIR = np.array([40.0, 28.0, 21.0])
hc[cloth] = np.clip(HAIR[None] * (Lh[cloth] / ref)[:, None], 0, 255)
print('HEAD cloth->hair texels %', round(100 * float(cloth.mean()), 1))
Image.fromarray(hc.astype(np.uint8)).save(T / 'thf_head_basecolor.png')
mats = [dict(base='Thief_A', prefix='Thief', mask=f'{key}_region_mask.png', regions=['cloth'], palettes=OLD['palettes'], ramps=ramps)]
json.dump(dict(variants=['thf_a', 'thf_b', 'thf_c'], materials=mats, note='colours: the installed thief ramps (palettes 825/826/827); range refitted p2..p98'),
          open(T / 'thf_ramps.json', 'w'), indent=1)
print('FINAL mask cover %', round(float((m > 0.5).mean()) * 100, 1), 'range', [round(x, 4) for x in rng], 'old range', OLD['ramps']['thf_a'][0]['range'])
