#!/usr/bin/env python3
"""Sabertooth texture set from the Meshy retexture (meshy/retexture_v1: 4K paint on our uv_atlas layout from the
four Codex HD masters). Run after scripts/dump_uv3d.py and scripts/bake_ao.py; grade, ramps and gutter fill follow
in build_runtime.sh.

Writes into textures/:
  saber_basecolor.png          2K base colour (4K Meshy paint downsampled once, Lanczos); the mouth cavity (body
                               texels inside the lips, on Head/Jaw) painted a dark gum red so the snarl reads as in
                               the native attack frames
  saber_normal_1k.png          Meshy normal (+y down; tools/prepare_actor_glb.py converts it)
  saber_mr_1k.png              ORM: R baked AO, G roughness (Meshy, clamped per class), B 0
  saber_region_mask.png        1K RGBA: R tawny fur, G pale fur (muzzle, chin, chest ruff, belly, inner legs: soft
                               split by lightness), B fangs and claws, A eye irises (green); pupils and dark lids keep their paint; the dark red
                               nose and the mouth cavity are in no region. Padded into the gutters.
  saber_material_classes.png   1K labels: 1 skin (nose), 2 fur, 4 claw, 5 tooth, 6 eye, 7 mouth
Classes per texel from the paint's hue and lightness, limited by geometry (part attribute: 1 eyes, 2 fangs, 3 claws;
painted golden claw tips only on the paw bones, green only on the head and eyeballs)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C   # noqa: E402  (rasterise: 2048 label/xyz maps)

SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
N = 2048
data = np.load(ROOT / 'work/uv3d.npz')
bones = [str(b) for b in data['bones']]
code = data['bone'] * 8 + data['mpart']
label, xyz = C.rasterise(data, values=code)
valid = label >= 0
bone_map = np.where(valid, label // 8, -1); mpart = np.where(valid, label % 8, -1)
bidx = {b: i for i, b in enumerate(bones)}


def on(*names):
    return np.isin(bone_map, [bidx[n] for n in names if n in bidx])


base_img = Image.open(f'{SRC}_base_color.png').convert('RGB').resize((N, N), Image.LANCZOS)
rgb = np.asarray(base_img, np.float32) / 255.0
mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
sat = np.where(mx > 1e-4, d / np.maximum(mx, 1e-4), 0)
h = np.zeros_like(mx)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
m = d > 1e-5
hr = m & (mx == r); hg = m & (mx == g) & ~hr; hb = m & ~hr & ~hg
h[hr] = ((g - b)[hr] / d[hr]) % 6; h[hg] = (b - r)[hg] / d[hg] + 2; h[hb] = (r - g)[hb] / d[hb] + 4
hue = h * 60
X, Yc, Zc = xyz[..., 0], xyz[..., 1], xyz[..., 2]

paw = on('FrontPaw_L', 'FrontPaw_R', 'HindPaw_L', 'HindPaw_R')
head = on('Head', 'Jaw')
body = valid & (mpart == 0)
fangs = valid & (mpart == 2)
claws = valid & ((mpart == 3) | (paw & body & (hue > 36) & (hue < 64) & (sat > 0.45) & (mx > 0.42)))
green = (hue > 70) & (hue < 175) & (sat > 0.28)
eye = valid & ((mpart == 1) | (head & green & (Zc > 1.02)))
eye = ndimage.binary_closing(eye, iterations=2) & valid & (head | (mpart == 1))
eye |= valid & ndimage.binary_dilation(eye, iterations=2) & (mx < 0.16) & (head | (mpart == 1))
redc = ((hue < 16) | (hue > 335)) & (sat > 0.40)
nose = valid & head & redc & (Yc < -1.06) & (Zc > 0.97)
nose = ndimage.binary_dilation(nose, iterations=1) & valid & head & (sat > 0.25) & ~eye
# mouth cavity: body texels inside the lips (behind the lip surface: within 5.5 cm of the midline, between the jaws)
zm = 0.967 + 0.221 * (Yc + 0.987)
tri_idx, _ = C.rasterise(data, values=np.arange(len(data['uv'])))
tx = data['xyz']; tn = np.cross(tx[:, 1] - tx[:, 0], tx[:, 2] - tx[:, 0])
tn /= np.maximum(np.linalg.norm(tn, axis=1, keepdims=True), 1e-12)
nz = np.where(tri_idx >= 0, tn[np.maximum(tri_idx, 0), 2], 0.0)
ny = np.where(tri_idx >= 0, tn[np.maximum(tri_idx, 0), 1], 0.0)
# palate faces look down, the floor of the mouth looks up; the outer lips look forward and out
mouth = (body & head & (np.abs(X) < 0.06) & (Yc < -0.95) & (Yc > -1.10) & (np.abs(Zc - zm) < 0.014)
         & (np.abs(nz) > 0.6) & (ny > -0.5) & ~nose)
tail = valid & (mpart == 4)
fur_all = valid & ~eye & ~nose & ~mouth & ~claws & ~fangs & (mpart != 5)
# pale fur: lighter and less saturated than the tawny coat, as a soft weight (smoothed over 3 texels)
lum = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
pale_score = np.clip((lum - 0.50) / 0.16, 0, 1) * np.clip((0.62 - sat) / 0.14, 0, 1)
pale = ndimage.gaussian_filter(pale_score * fur_all, 3.0) / np.maximum(ndimage.gaussian_filter(fur_all.astype(np.float32), 3.0), 1e-3)
pale = np.clip(pale * 1.25, 0, 1) * fur_all
print('CLASSES texels', {'fur': int(fur_all.sum()), 'pale>0.5': int((pale > 0.5).sum()), 'claws': int(claws.sum()),
                         'fangs': int(fangs.sum()), 'eye': int(eye.sum()), 'nose': int(nose.sum()),
                         'mouth': int(mouth.sum()), 'valid': int(valid.sum())})

# mouth cavity: dark gum red, keeping the paint's brightness detail
gum = np.array([0.34, 0.08, 0.07], np.float32)
mw = ndimage.gaussian_filter(mouth.astype(np.float32), 1.2) * (body & head)
rgb2 = rgb * (1 - mw[..., None]) + (gum * (0.6 + 0.8 * lum[..., None])) * mw[..., None]
# mouth bag (part 5, scripts/mouth.py): gum red darkening toward the throat, a row of ivory teeth along its front
# top and bottom (the native attack frames show both rows); painted from each texel's rest position
bag = valid & (mpart == 5)
BC = np.array([0.0, -1.012, 0.948]); BR = np.array([0.046, 0.062, 0.020])
pb = (xyz - BC) / BR
depth = np.clip(-pb[..., 1], 0, 1)
gumc = np.array([0.66, 0.12, 0.10], np.float32) * (0.50 + 0.50 * depth[..., None])
teeth = bag & (pb[..., 1] < -0.55) & (np.abs(pb[..., 2]) > 0.40) & (np.mod(xyz[..., 0] / 0.011 + 0.5, 1.0) < 0.72)
rgb2[bag] = gumc[bag]
rgb2[teeth] = np.array([0.90, 0.86, 0.76], np.float32) * (0.75 + 0.25 * depth[teeth, None])
# the grade's AO would blacken the cavity: scripts/apply_bag.py puts these texels back after the grade
np.savez_compressed(ROOT / 'work/bag_paint.npz', mask=bag, rgb=np.clip(rgb2, 0, 1).astype(np.float32)[bag])
Image.fromarray((np.clip(rgb2, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'saber_basecolor.png', optimize=True)

iris = eye & green & (mx > 0.18)                    # the ramp recolours the green iris; pupils and lids keep their paint
keep_out_eye = eye & ~iris
chan = [fur_all * (1 - pale), pale, (claws | fangs).astype(np.float32), iris.astype(np.float32)]
_, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
mask = np.zeros((N, N, 4), np.float32)
keep_out = nose | mouth | keep_out_eye | (valid & (mpart == 5))
for c, sel in enumerate(chan):
    w = ndimage.gaussian_filter(np.asarray(sel, np.float32), 0.8)
    w[keep_out] = 0.0
    w = w * valid
    padded = w[iy, ix]; padded[valid] = w[valid]
    mask[..., c] = padded
mask[~valid & keep_out[iy, ix]] = 0.0
total = mask.sum(-1, keepdims=True)
mask = np.where(total > 1.0, mask / np.maximum(total, 1e-6), mask)
chans = [Image.fromarray((mask[..., c] * 255 + 0.5).astype(np.uint8), 'L').resize((1024, 1024), Image.LANCZOS)
         for c in range(4)]
Image.merge('RGBA', chans).save(OUT / 'saber_region_mask.png')

Image.open(f'{SRC}_normal.png').convert('RGB').resize((1024, 1024), Image.LANCZOS).save(OUT / 'saber_normal_1k.png')
rough = np.asarray(Image.open(f'{SRC}_roughness.png').convert('L').resize((N, N), Image.LANCZOS)) / 255.0
rough = np.where(claws | fangs | teeth, np.clip(rough, 0.35, 0.6), np.where(eye, 0.2, np.where(nose | mouth | bag, np.clip(rough, 0.45, 0.7),
                 np.clip(rough, 0.6, 0.95))))
ao = np.asarray(Image.open(OUT / 'saber_ao_2k.png').convert('L'), np.float32) / 255.0
orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
Image.fromarray((orm * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(OUT / 'saber_mr_1k.png')

classes = np.zeros((N, N), np.uint8)
classes[valid] = 2
classes[nose] = 1
classes[claws] = 4
classes[fangs] = 5
classes[eye] = 6
classes[mouth] = 7
classes[valid & (mpart == 5)] = 7
classes[teeth] = 5
Image.fromarray(classes, 'L').resize((1024, 1024), Image.NEAREST).save(OUT / 'saber_material_classes.png')
pv = np.zeros((N, N, 3), np.float32)
pv[fur_all] = np.array([0.75, 0.45, 0.2]) * (1 - pale[fur_all, None]) + np.array([1.0, 0.95, 0.75]) * pale[fur_all, None]
for sel, col in ((claws, (1, 0.85, 0)), (fangs, (1, 1, 1)), (eye, (0, 0.9, 0)), (nose, (1, 0, 0)), (mouth, (1, 0, 1)),
                 (tail & False, (0, 0, 1))):
    pv[sel] = col
Image.fromarray((pv * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(ROOT / 'review' / 'region_classes.png')
print('COMPOSED')
