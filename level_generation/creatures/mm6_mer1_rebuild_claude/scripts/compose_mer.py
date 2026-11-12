#!/usr/bin/env python3
"""MM6 merchant copy of mm6_thf_rebuild_claude/scripts/compose_thf.py (no weapon strip: the club keeps its own GLB).
Texture sets from the 4K Meshy paints on our uv_atlas layouts: body colour 4K -> 2K Lanczos once, head colour 4K -> 1K, normal and roughness
1K, padded into the gutters; ORM = (AO, roughness, 0). Gentle grade (grade_basecolor.py --fine 1.0 --local 0.3 --ao-strength 0.5
--contrast 1.06 --saturation 1.15) on both sets. Hands toned to the face's skin. Tier region as the installed merchant (one `tunic` region,
palettes 252/253/770, the installed ramp colours): the green tunic texels of the torso/sleeves and the skirt (hue 70..200, saturation > 0.12).
Range refitted to the new paint (p2..p98). Run in the project folder with the gltf venv python: --stage raw, then --stage final."""
import json, sys, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
T = Path('textures'); D = np.load('work/final_v1_uv.npz')
STAGE = sys.argv[sys.argv.index('--stage') + 1]
part, head = D['part'], D['head'].astype(bool)


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


bf = np.nonzero(~head)[0]; hf = np.nonzero(head)[0]
if STAGE == 'raw':
    for key, job, faces, uvk, csize in (('mer', 'retexture_body_v1', bf, 'UV', 2048), ('mer_head', 'retexture_head_v1', hf, 'HU', 1024)):
        lab = raster(D[uvk], faces, part[faces] + 1, csize); cov = lab > 0
        lab1 = raster(D[uvk], faces, part[faces] + 1, 1024); cov1 = lab1 > 0
        col = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_base_color.png').convert('RGB').resize((csize, csize), Image.LANCZOS))
        nrm = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS))
        rgh = np.asarray(Image.open(f'meshy/{job}/texture_urls_0_roughness.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        Image.fromarray(pad(col, cov)).save(T / f'{key}_raw.png')
        nrm = pad(nrm, cov1); ao = np.asarray(Image.open(T / f'{key}_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
        orm = np.dstack([pad(ao, cov1), pad(np.maximum(rgh, 128), cov1), np.zeros((1024, 1024), np.uint8)])
        Image.fromarray(nrm).save(T / f'{key}_normal_1k.png')
        Image.fromarray(orm.astype(np.uint8)).save(T / f'{key}_metal_rough_1k.png')
        np.save(f'work/{key}_labels.npy', lab)
        print('RAW', key, 'atlas', round(float(cov.mean()) * 100, 1))
    for key in ('mer', 'mer_head'):
        subprocess.check_call([sys.executable, '../claude_shared/grade_basecolor.py', '--ao', str(T / f'{key}_ao.png'), '--fine', '1.0', '--local', '0.3',
                               '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15', str(T / f'{key}_raw.png')])
    sys.exit()
# ---- final: dagger strip, region and ramps from the graded colour
OLD = json.load(open('../mm6_mer1_codex/textures/mer1_ramps.json'))['materials'][0]
key = 'mer'
col = np.asarray(Image.open(T / f'{key}_raw_graded.png').convert('RGB')).copy()
lab = np.load(f'work/{key}_labels.npy') - 1
p = np.where(lab >= 0, lab, -1)
# the grafted hands (part 0) and wrist skin (part 4): Meshy painted them near white; their median goes to the face's skin median (head set)
hcol = np.asarray(Image.open(T / 'mer_head_raw_graded.png').convert('RGB')).astype(float)
hhsv = np.asarray(Image.open(T / 'mer_head_raw_graded.png').convert('HSV')).astype(float)
hl = np.load('work/mer_head_labels.npy') - 1
sk = (hl >= 0) & (hhsv[..., 0] < 30) & (hhsv[..., 1] > 50) & (hhsv[..., 2] > 90)
hand = np.isin(p, [0, 4])
_d, (_iy, _ix) = ndimage.distance_transform_edt(p < 0, return_indices=True)
hand = hand | ((p < 0) & (_d <= 6) & np.isin(p[_iy, _ix], [0, 4]))          # the islands' unrasterised rims and gutters too (pale seams otherwise)
gain = np.median(hcol[sk], 0) / np.maximum(np.median(col[np.isin(p, [0, 4])].astype(float), 0), 1)
col = col.astype(float); col[hand] = np.clip(col[hand] * gain, 0, 255); col = col.astype(np.uint8)
print('HANDS gain', gain.round(3).tolist())
# skirt stains: Meshy painted a few brown streaks on the plain green skirt (the masters show none); above the gold hem band, non-green
# skirt texels take the nearest clean green (detail kept as a luminance ratio, softened)
bidx = raster(D['UV'], bf, np.arange(len(bf)) + 1, col.shape[0]) - 1
okb = bidx >= 0
bz = np.full(bidx.shape, np.nan); bz[okb] = D['P'][bf[bidx[okb]]].mean(1)[:, 2]
hsv0 = np.asarray(Image.fromarray(col.astype(np.uint8)).convert('HSV')).astype(float)
h0, s0, v0 = hsv0[..., 0] * 360 / 255, hsv0[..., 1] / 255, hsv0[..., 2] / 255
zhem = float(D['P'][part == 7][..., 2].min())
skirt = okb & (p == 7) & (bz > zhem + 0.14) & (bz < 0.0)
stain = skirt & ((h0 < 65) | (h0 > 200)) & (s0 > 0.15)          # not green (a wood-brown streak under the pouch, Meshy's)
stain = ndimage.binary_dilation(ndimage.binary_opening(stain, iterations=1), iterations=3) & skirt
if stain.any():
    good = skirt & ~stain
    _, (iy, ix_) = ndimage.distance_transform_edt(~good, return_indices=True)
    # nearest clean texel, softened by a normalised blur over clean skirt texels only (a plain blur pulled the dark gutters in)
    fill = col[iy, ix_].astype(float); wgt = (skirt & ~stain) | stain
    num = np.dstack([ndimage.gaussian_filter(fill[..., k] * wgt, 2.0) for k in range(3)]); den = ndimage.gaussian_filter(wgt.astype(float), 2.0)[..., None]
    fill = num / np.maximum(den, 1e-6)
    col = col.astype(float); col[stain] = fill[stain]; col = np.clip(col, 0, 255).astype(np.uint8)
# weave detail where Meshy left the skirt smooth (areas the hands hid in the masters): a high-pass patch of well-textured skirt weave,
# tiled, added where the local detail is under 45 % of the skirt's median
L0 = col.astype(float) @ np.array([0.299, 0.587, 0.114])
hp = L0 - ndimage.gaussian_filter(L0, 3.0)
sd = np.sqrt(np.maximum(ndimage.uniform_filter(hp ** 2, 15), 0))
allsk = okb & (p == 7) & (bz > zhem + 0.14)
med = float(np.median(sd[allsk])); smooth = allsk & (sd < 0.45 * med)
smooth = ndimage.binary_opening(smooth, iterations=2)
yy, xx = np.nonzero(allsk & (sd > med) & ~smooth)
best = None
for k in range(0, len(yy), max(1, len(yy) // 400)):
    y_, x_ = yy[k], xx[k]
    if y_ + 96 > hp.shape[0] or x_ + 96 > hp.shape[1]: continue
    if allsk[y_:y_ + 96, x_:x_ + 96].mean() > 0.99: best = (y_, x_); break
if best is not None and smooth.any():
    patch = hp[best[0]:best[0] + 96, best[1]:best[1] + 96]
    tile = np.tile(patch, (hp.shape[0] // 96 + 1, hp.shape[1] // 96 + 1))[:hp.shape[0], :hp.shape[1]]
    w_ = ndimage.gaussian_filter(smooth.astype(float), 3.0) * allsk
    col = col.astype(float); col += (tile * w_ * 0.9)[..., None] * (col / np.maximum(L0[..., None], 1)); col = np.clip(col, 0, 255).astype(np.uint8)
print('SKIRT stain texels', int(stain.sum()), 'hem z', round(zhem, 3), 'smooth texels', int(smooth.sum()), 'patch', best)
hsv = np.asarray(Image.fromarray(col.astype(np.uint8)).convert('HSV')).astype(float)
h, s, v = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
green = (h > 70) & (h < 200) & (s > 0.12) & np.isin(p, [1, 7])
green = ndimage.binary_opening(green, iterations=1)
R = green.astype(float)
cov = lab >= 0
cls = np.where(lab < 0, 0, np.where(np.isin(p, [4]), 1, np.where(np.isin(p, [12]), 9, 8)))
L = lum(col.astype(float))
vals = L[(R > 0.5) & cov]
rng = [float(np.percentile(vals, 2)), float(np.percentile(vals, 98))]
ramps = {t: [dict(range=[round(rng[0], 6), round(rng[1], 6)], colors=OLD['ramps'][t][0]['colors'])] for t in ('mer1_a', 'mer1_b', 'mer1_c')}
sys.path.insert(0, '../claude_shared')
import region_variants as RV
m = pad(R, cov); m = ndimage.gaussian_filter(m, 2.0)
RV.write_mask([np.asarray(Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)) / 255.0], T / f'{key}_region_mask.png', size=1024)
Image.fromarray(np.asarray(Image.fromarray(cls.astype(np.uint8)).resize((1024, 1024), Image.NEAREST))).save(T / f'{key}_material_classes.png')
Image.fromarray(col.astype(np.uint8)).save(T / f'{key}_basecolor.png')
# face paint fixes by texel position (head set): Meshy painted a dark zigzag hair fringe on the forehead just under the cap rim (the masters
# show no fringe there) and a few blue specks on the face above the collar; both become the surrounding skin (nearest clean skin texel,
# softened)
hc = np.asarray(Image.open(T / 'mer_head_raw_graded.png').convert('RGB')).astype(float)
HS = hc.shape[0]
fidx = raster(D['HU'], hf, np.arange(len(hf)) + 1, HS) - 1
Pc = D['P'].mean(1)
cap = D['P'][part == 3].reshape(-1, 3); cap_front = cap[cap[:, 1] < -0.04]
zcap = float(np.percentile(cap_front[:, 2], 2))
cen = np.where(fidx >= 0, 0, 0).astype(float)
cx = np.full(fidx.shape, np.nan); cy = cx.copy(); cz = cx.copy(); pp = np.full(fidx.shape, -1)
okf = fidx >= 0
cx[okf], cy[okf], cz[okf] = Pc[hf[fidx[okf]]].T; pp[okf] = part[hf[fidx[okf]]]
hsv_ = np.asarray(Image.fromarray(hc.astype(np.uint8)).convert('HSV')).astype(float)
hue_, sat_, val_ = hsv_[..., 0] * 360 / 255, hsv_[..., 1] / 255, hsv_[..., 2] / 255
Lh_ = hc @ np.array([0.299, 0.587, 0.114])
fore = okf & (pp == 2) & (cz > zcap - 0.035) & (cy < -0.02) & (np.abs(cx) < 0.075)
skin_ref = np.median(Lh_[fore]) if fore.any() else 150
fringe = fore & (Lh_ < 0.62 * skin_ref)
fringe = ndimage.binary_dilation(fringe, iterations=2) & fore
eyes = okf & (np.abs(np.abs(cx) - 0.0355) < 0.022) & (cy > -0.085) & (cy < -0.035) & (cz > 0.67) & (cz < 0.72)    # eyeballs and lids: kept
blue = okf & (pp == 2) & (cz > 0.63) & (cy < 0.0) & (hue_ > 180) & (hue_ < 270) & (sat_ > 0.2)
blue = ndimage.binary_dilation(blue, iterations=2) & okf & (pp == 2)
Image.fromarray(np.dstack([fringe * 255, blue * 255, eyes * 255]).astype(np.uint8)).save('work/face_fix_masks.png')
bad = fringe | blue
if bad.any():
    good = okf & (pp == 2) & ~bad
    _, (iy, ix_) = ndimage.distance_transform_edt(~good, return_indices=True)
    fill = hc[iy, ix_]
    fill = np.dstack([ndimage.gaussian_filter(fill[..., k], 2.0) for k in range(3)])
    hc[bad] = fill[bad]
# the cap's own rim faces carry the same fringe paint (brown, saturated): back to the cap's grey felt
rim = okf & (pp == 3) & (cz < zcap + 0.03) & (cy < 0.0)
capfr = rim & (sat_ > 0.22) & (hue_ < 60)
capfr = ndimage.binary_dilation(capfr, iterations=2) & rim
if capfr.any():
    good = okf & (pp == 3) & ~capfr & (sat_ < 0.18)
    _, (iy, ix_) = ndimage.distance_transform_edt(~good, return_indices=True)
    fill = hc[iy, ix_]; fill = np.dstack([ndimage.gaussian_filter(fill[..., k], 1.5) for k in range(3)])
    hc[capfr] = fill[capfr]
print('CAP rim texels', int(capfr.sum()))
print('FACE fixes: fringe texels', int(fringe.sum()), 'blue texels', int(blue.sum()), 'cap rim z', round(zcap, 3))
Image.fromarray(np.clip(hc, 0, 255).astype(np.uint8)).save(T / 'mer_head_basecolor.png')
mats = [dict(base='Merchant_A', prefix='Merchant', mask=f'{key}_region_mask.png', regions=['tunic'], palettes=OLD['palettes'], ramps=ramps)]
json.dump(dict(variants=['mer1_a', 'mer1_b', 'mer1_c'], materials=mats, note='colours: the installed merchant ramps (palettes 252/253/770); range refitted p2..p98'),
          open(T / 'mer_ramps.json', 'w'), indent=1)
print('FINAL mask cover %', round(float((m > 0.5).mean()) * 100, 1), 'range', [round(x, 4) for x in rng], 'old range', OLD['ramps']['mer1_a'][0]['range'])
