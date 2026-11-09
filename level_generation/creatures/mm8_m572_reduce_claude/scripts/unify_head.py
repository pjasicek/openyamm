#!/usr/bin/env python3
"""Phoenix head colour fix (local, no Meshy). The HD masters gave the bird a brown golden-eagle head: on the plumage
ramp (region mask channel 0) the head texels sat at linear luminance 0.048 / 0.076 / 0.133 (p10/50/90) against the
neck's 0.174 / 0.378 / 0.551, and the brown brow, lores and eye surround were outside every mask, so the head stayed
dark brown on the gold, pink-white and red tiers. The native sprites colour the head like the body.

- Head plumage (mask 0) is quantile-matched to the neck's mask-0 luminance; each texel is scaled by matched/original
  luminance, so hue and feather detail stay.
- Brown head texels outside every mask (hue 5-45 deg, value 0.12-0.55, saturation > 0.25: brow, lores, eye surround)
  join mask 0 and take the same match.
- The face stays a little darker, as in the native frames: up to 45 % darker around the eyes (Gaussian, 9 mm) and up
  to 30 % on the lores in front of the plumage-mask boundary (y < -0.170 -> -0.184).
- Only extension patches connected (in UV) to the existing plumage region are kept, so isolated brownish specks on
  the beak and hook stay as painted.
- Upper brow away from the eyes also takes darker / greyer browns (value 0.04-0.12, saturation 0.15-0.25), which
  otherwise stay as dark specks on the tier colour.
- Unchanged: iris and pupils, mouth, the beak (yellow keratin and grey hook, saturation < 0.2) and a 1.5 mm cere band around it, kept
  out of mask 0. The original mask's few beak and gape texels are cleared, so no tier tint shows on the beak.
Texel positions come from scripts/head_texels.py (work/retex/head_texels.npz). Only the base colour and the region
mask images change; materials, variants, LODs and shadow meshes reference them unchanged.
Usage: unify_head.py <in.glb> <out.glb>"""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
EYES = np.array([[0.0194, -0.1581, 0.1745], [-0.0193, -0.1587, 0.1745]])
EYE_SIGMA, EYE_DARK = 0.009, 0.45
LORE_Y0, LORE_Y1, LORE_DARK = -0.170, -0.184, 0.30
CERE_BAND = 0.0015
lin = lambda c: np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= .0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - .055)
LW = np.array([.2126, .7152, .0722])

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
mat = doc['materials'][0]
base_img = doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
mask_img = doc['textures'][mat['extras']['openyamm_region_mask']['index']]['source']


def load(i):
    v = doc['bufferViews'][doc['images'][i]['bufferView']]; s = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(bytes(binary[s:s + v['byteLength']])))


def store(i, im, suffix):
    buf = io.BytesIO(); im.save(buf, 'PNG'); binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(buf.getvalue())})
    binary.extend(buf.getvalue())
    doc['images'][i] = {'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png',
                        'name': doc['images'][i].get('name', 'image') + suffix}


rgba = np.asarray(load(base_img).convert('RGBA'), np.float32) / 255
mask_full = np.asarray(load(mask_img)).copy()
H, W = rgba.shape[:2]; MH, MW = mask_full.shape[:2]
mask = np.stack([np.asarray(Image.fromarray(mask_full[..., k]).resize((W, H), Image.Resampling.BILINEAR), np.float32)
                 / 255 for k in range(3)], -1)
t = np.load(HERE / 'work/retex/head_texels.npz'); lab, pos = t['lab'], t['pos']
head = lab == 1; neck = lab == 2
rgb = rgba[..., :3]; mx = rgb.max(2); mn = rgb.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360

# beak: yellow keratin and the dark hook; the cere band is every head texel within CERE_BAND of it (3D)
un = head & (mask.max(2) < .5)
yellow = head & (hue > 40) & (hue < 65) & (sat > .5) & (mx > .5)
hook = head & (pos[..., 1] < -.183) & (sat < .2) & (mx < .5)
beak = yellow | hook
near = np.zeros_like(head); hidx = np.flatnonzero(head)
near.flat[hidx] = cKDTree(pos[beak]).query(pos.reshape(-1, 3)[hidx])[0] < CERE_BAND
cere = near & head
p = pos.reshape(-1, 3)
deye = np.min(np.linalg.norm(p[:, None, :] - EYES[None], axis=2), 1).reshape(H, W)
brown = un & ~cere & (hue >= 5) & (hue <= 45) & (mx >= .12) & (mx < .55) & (sat > .25)
# upper brow away from the eyes: darker and greyer browns too (isolated dark specks on the tier colour otherwise)
brow = un & ~cere & (pos[..., 2] > .170) & (deye > .005) & (hue <= 50) & (mx >= .04) & (mx < .55) & (sat > .15)
brown = ndimage.binary_opening(brown | brow, iterations=1)
# keep only patches that touch the existing plumage region: isolated brownish specks on the beak and hook stay paint
labels, n = ndimage.label(brown)
touch = np.unique(labels[ndimage.binary_dilation(head & (mask[..., 0] > .5), iterations=2) & brown])
brown = np.isin(labels, touch[touch > 0])
plume = np.maximum(mask[..., 0], brown.astype(np.float32))
# gutter texels around the head islands follow the head (bilinear filtering and mips)
headish = ndimage.binary_dilation(head, iterations=4) & ~neck
w = plume * headish

L = lin(rgb); Y = L @ LW
hsel, nsel = head & (plume > .5), neck & (mask[..., 0] > .5)
q = np.linspace(0, 100, 201)
hq = np.maximum.accumulate(np.percentile(Y[hsel], q) + np.arange(len(q)) * 1e-9); nq = np.percentile(Y[nsel], q)
ratio = np.where(Y > 1e-5, np.interp(Y, hq, nq) / np.maximum(Y, 1e-5), 1.0)
# darker face: eye ring and lores
dark = EYE_DARK * np.exp(-(deye / EYE_SIGMA) ** 2)
lore = np.clip((pos[..., 1] - LORE_Y0) / (LORE_Y1 - LORE_Y0), 0, 1); lore = lore * lore * (3 - 2 * lore)
dark = np.maximum(dark, LORE_DARK * lore) * head
# gutters take the nearest head texel's darkening
_, nearest = ndimage.distance_transform_edt(~head, return_indices=True)
dark = dark[nearest[0], nearest[1]]
gain = 1 + (ratio * (1 - dark) - 1) * w
new = np.clip(L * gain[..., None], 0, 1)
after = new @ LW
print('head plumage Y p10/50/90 before', np.percentile(Y[hsel], [10, 50, 90]).round(4),
      'after', np.percentile(after[hsel], [10, 50, 90]).round(4), 'neck', np.percentile(Y[nsel], [10, 50, 90]).round(4))
print('mask 0 extended by', int(brown.sum()), 'texels; cere band kept', int(cere.sum()), 'texels; beak', int(beak.sum()), 'texels')
out = np.concatenate([np.clip(srgb(new), 0, 1), rgba[..., 3:]], -1)
store(base_img, Image.fromarray((out * 255 + .5).astype(np.uint8)), '_head_unified')
# region mask: channel 0 takes the extended texels (max over each block of the base-colour resolution)
ext = brown.reshape(MH, H // MH, MW, W // MW).max((1, 3))
mask_full[..., 0] = np.maximum(mask_full[..., 0], ext.astype(np.uint8) * 255)
# the original mask reached a few beak and gape texels (pink / red specks at the beak base): clear every channel there
beak_block = beak.reshape(MH, H // MH, MW, W // MW).mean((1, 3)) >= .5
mask_full[beak_block, :3] = 0
print('mask cleared on', int(beak_block.sum()), 'beak texels (1K)')
store(mask_img, Image.fromarray(mask_full), '_head_extended')
# drop the replaced images' bytes: keep only buffer views that accessors or images still reference
used = sorted({a['bufferView'] for a in doc['accessors'] if 'bufferView' in a}
              | {im['bufferView'] for im in doc['images'] if 'bufferView' in im})
vmap, packed, views = {}, bytearray(), []
for new_index, old in enumerate(used):
    v = dict(doc['bufferViews'][old]); s = v.get('byteOffset', 0)
    packed.extend(b'\0' * (-len(packed) % 4)); v['byteOffset'] = len(packed)
    packed.extend(binary[s:s + v['byteLength']]); views.append(v); vmap[old] = new_index
doc['bufferViews'] = views
for a in doc['accessors']:
    if 'bufferView' in a:
        a['bufferView'] = vmap[a['bufferView']]
for im in doc['images']:
    if 'bufferView' in im:
        im['bufferView'] = vmap[im['bufferView']]
write_glb(dst, doc, bytes(packed)); print('WROTE', dst, f'{len(packed) / 1e6:.1f} MB')
