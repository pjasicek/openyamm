#!/usr/bin/env python3
"""Paint the grafted hands into the Titan's LOD0 atlas (after compose_headhand.py's hand part).

Inside each hand rectangle (graft_ttn.json `rects`): the baked MakeHuman skin (work/hands/) graded so its median and
spread per channel match the Titan's own hand skin (texels under the installed LOD0's hand faces), times a soft baked
AO; metal/rough and the region mask take the old hand texels' medians (skin: no tier region); normal flat. Edge-padded
inside the rectangles only. Reads work/src_tex/ (dump_glb.py of the installed GLB), writes textures/<same names>.png."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
PROJ = Path(__file__).resolve().parents[1]
S, H, T = PROJ / 'work' / 'src_tex', PROJ / 'work' / 'hands', PROJ / 'textures'
T.mkdir(exist_ok=True)
cfg = json.load(open(PROJ / 'scripts' / 'graft_ttn.json'))
AO_STRENGTH, SPREAD = cfg.get('ao_strength', 0.45), 0.45   # follow-up 2026-11-11: config keys ao_strength, grain, grain_normal
names = {'base': 'ttn_a_basecolor_1k_head_atlas', 'mr': 'ttn_metal_rough_1k_head_atlas',
         'normal': 'ttn_normal_1k_head_atlas', 'mask': 'ttn_region_mask_head_atlas'}
img = {k: np.asarray(Image.open(S / f'{v}.png')).astype(np.float32) for k, v in names.items()}
Hh, Ww = img['base'].shape[:2]
# old hand texels
d = np.load(S / 'lod0.npz'); jn = list(d['names']); uv = d['uv']; tri = d['idx'].reshape(-1, 3)
hw = sum(((d['j'] == jn.index(b)) * d['w']).sum(1) for b in ('LeftHand', 'RightHand'))
om = Image.new('L', (Ww, Hh), 0); dr = ImageDraw.Draw(om)
for t in tri:
    if hw[t].mean() > 0.8:
        dr.polygon([(uv[k][0] * Ww, uv[k][1] * Hh) for k in t], fill=255)
old = ndimage.binary_erosion(np.asarray(om) > 0, iterations=1)
ref = img['base'][old]
lum = ref @ np.array([0.299, 0.587, 0.114])
ref = ref[(lum > np.percentile(lum, 15)) & (lum < np.percentile(lum, 92))]
med = {k: np.median(img[k][old], 0) for k in ('mr', 'mask')}
skin = np.asarray(Image.open(H / 'hand_skin.png').convert('RGB')).astype(np.float32)
mask = np.asarray(Image.open(H / 'hand_mask.png').convert('L')) > 127
ao = np.asarray(Image.open(H / 'hand_ao.png').convert('L').filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
region = np.zeros((Hh, Ww), bool)
for x0, y0, rw, rh in cfg['rects'].values():
    region[y0:y0 + rh, x0:x0 + rw] = True
hand = mask & region
src = skin[hand]
graded = (skin - np.median(src, 0)) * (np.std(ref, 0) / np.maximum(np.std(src, 0), 1e-3)) * SPREAD + np.median(ref, 0)
aof = 1 - AO_STRENGTH + AO_STRENGTH * np.clip(ao / max(np.percentile(ao[hand], 90), 1e-3), 0, 1)
graded *= (aof / np.median(aof[hand]))[..., None]
# the Titan's granite grain: high-pass of a clean stone-skin swatch of the atlas (forearm skin, region mask 0),
# mirror-tiled over the rectangles, on colour and normal (user review: hands must read as the same stone skin)
SW = cfg.get('swatch', [97, 869, 40])
def grain(arr, flat):
    x, y, r = SW
    sw = arr[y - r:y + r, x - r:x + r].astype(np.float32)
    hp = sw - ndimage.gaussian_filter(sw, (6, 6, 0))
    tile = np.concatenate([hp, hp[:, ::-1]], 1); tile = np.concatenate([tile, tile[::-1]], 0)
    reps = (Hh // tile.shape[0] + 1, Ww // tile.shape[1] + 1, 1)
    return np.tile(tile, reps)[:Hh, :Ww]
graded = graded + grain(img['base'], None) * cfg.get('grain', 1.0)
graded = np.clip(graded, 0, 255)


def pad(arr, iters=8):
    idx = ndimage.distance_transform_edt(~hand, return_distances=False, return_indices=True)
    grown = ndimage.binary_dilation(hand, iterations=iters) & region
    out = arr.copy()
    out[grown & ~hand] = arr[idx[0], idx[1]][grown & ~hand]
    return out


out = {}
b = img['base'].copy(); b[hand] = graded[hand]; out['base'] = pad(b)
m = img['mr'].copy(); m[hand] = med['mr']; out['mr'] = pad(m)
n = img['normal'].copy(); n[hand] = (np.array([128.0, 128.0, 255.0]) + grain(img['normal'], None) * cfg.get('grain_normal', 0.8))[hand]; out['normal'] = pad(n)
k = img['mask'].copy(); k[hand] = med['mask']; out['mask'] = pad(k)
for key, arr in out.items():
    Image.fromarray(np.uint8(np.round(np.clip(arr, 0, 255)))).save(T / f'{names[key]}.png')
print('COMPOSE hand texels', int(hand.sum()), 'old hand texels', int(old.sum()), 'ref median', np.median(ref, 0).round(1),
      'std', np.std(ref, 0).round(1), 'graded median', np.median(graded[hand], 0).round(1), 'mr', med['mr'].round(1),
      'mask', med['mask'].round(1))
