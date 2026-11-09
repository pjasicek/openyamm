#!/usr/bin/env python3
"""Head + hands texture set, 1K (CLAUDE_CREATURE_TEXTURES.md "Head detail"; after mm6_cle_claude hand_texture_set.py).

- Head: the Meshy head-only retexture (meshy/<job>/texture_urls_0_*.png, laid out on HeadUV 0..1) resampled into
  the lower-left HEAD_SCALE square (head_split.py scaled the head islands by the same factor, so this is exact),
  times an optional seam gain (body/head luminance across the neck seam; 1 for a separate head shell).
- Hands: their squares (graft_hands.py) take the baked MakeHuman skin (bake_hands.py), graded so its median and
  spread per channel match the character's own skin (the body texture's skin-class texels, class 1), times a soft
  baked AO normalised to keep that median.
- Base colour 2K (matches the 2K body base colour for merge_head_material.py); normal and ORM 1K.
- Normal: Meshy's head normal; flat on the hands. ORM: R 1, G roughness (Meshy head; hands the body skin median), B 0.
Every map is edge-padded around the islands.
Writes textures/<p>_head_basecolor.png, <p>_head_normal_1k.png, <p>_head_metal_rough_1k.png.
Usage: compose_headhand.py <prefix> <meshy head job dir> <body basecolor png> <body classes png> <body orm png>
       [--seam-gain G] [--hand-gain G] [--hand-squares JSON]"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ap = argparse.ArgumentParser()
for a in ('prefix', 'job', 'body', 'classes', 'orm'):
    ap.add_argument(a)
ap.add_argument('--seam-gain', type=float, default=1.0)
ap.add_argument('--hand-gain', type=float, default=1.0)
ap.add_argument('--ref-head', action='store_true', help='grade the hands to the face skin of the head retexture (Yrsa: her old body skin texels were darker than her face)')
ap.add_argument('--ref-lum-min', type=float, default=0.0, help='with --ref-head: only face texels brighter than this (mm9_peasantdm1: the ginger beard and hair passed the reddish test and turned the hands orange-brown)')
ap.add_argument('--head-scale', type=float, default=0.8)
ap.add_argument('--squares', default='{"L": [0.8, 0.8, 0.2], "R": [0.8, 0.6, 0.2]}')
o = ap.parse_args()
PROJ = Path(__file__).resolve().parents[1]
T, H = PROJ / 'textures', PROJ / 'work' / 'hands'
N = 2048                  # composed at the base colour's 2K (the body base is 2K; merge_head_material needs equal sizes)
S = o.head_scale
AO_STRENGTH = 0.45
job = Path(o.job)


def scaled(img, fill):
    out = Image.new(img.mode, (N, N), fill)
    k = int(round(N * S))
    out.paste(img.resize((k, k), Image.LANCZOS), (0, N - k))
    return np.asarray(out).astype(np.float32)


def pad(arr, mask, iters=24):
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    grown = ndimage.binary_dilation(mask, iterations=iters)
    out = arr.copy()
    out[grown & ~mask] = arr[idx[0], idx[1]][grown & ~mask]
    return out


hb = Image.open(job / 'texture_urls_0_base_color.png').convert('RGB')
base = scaled(hb, (0, 0, 0)) * o.seam_gain
normal = scaled(Image.open(job / 'texture_urls_0_normal.png').convert('RGB'), (128, 128, 255))
rough = scaled(Image.open(job / 'texture_urls_0_roughness.png').convert('L'), 200)
metal = scaled(Image.open(job / 'texture_urls_0_metallic.png').convert('L'), 0)
headcov = scaled(Image.open(job / 'texture_urls_0_base_color.png').convert('L').point(lambda v: 255), 0) > 0
orm = np.stack([np.full((N, N), 255.0), np.maximum(rough, 128), np.zeros((N, N))], -1)   # metallic 0 (skin, cloth)

# character skin reference: body texture texels of class 1 (skin)
bodyc = np.asarray(Image.open(o.body).convert('RGB')).astype(np.float32)
cls = np.asarray(Image.open(o.classes).convert('L').resize(bodyc.shape[1::-1], Image.NEAREST))
ref = bodyc[cls == 1]
if len(ref):          # mm9_peasantm1: the body set has no skin texels (use --ref-head)
    lum = ref @ np.array([0.299, 0.587, 0.114])
    ref = ref[(lum > np.percentile(lum, 20)) & (lum < np.percentile(lum, 90))]
if o.ref_head:
    hf = np.asarray(hb).astype(np.float32).reshape(-1, 3)
    r_, g_, b_ = hf.T
    ref = hf[(r_ > g_ * 1.15) & (g_ > b_ * 1.05) & (r_ > 80) & (hf @ np.array([0.299, 0.587, 0.114]) > o.ref_lum_min)]
ormb = np.asarray(Image.open(o.orm).convert('RGB').resize(bodyc.shape[1::-1]))
ref_rough = float(np.median(ormb[cls == 1][:, 1])) if (cls == 1).any() else float(np.median(np.maximum(rough[headcov], 128)))

skin = np.asarray(Image.open(H / 'hand_skin.png').convert('RGB')).astype(np.float32)
mask = np.asarray(Image.open(H / 'hand_mask.png').convert('L')) > 127
ao = np.asarray(Image.open(H / 'hand_ao.png').convert('L').filter(ImageFilter.GaussianBlur(1.6))).astype(np.float32) / 255
src = skin[mask]
graded = (skin - np.median(src, 0)) * (np.std(ref, 0) / np.maximum(np.std(src, 0), 1e-3)) * 0.6 + np.median(ref, 0)
graded *= o.hand_gain
aof = 1 - AO_STRENGTH + AO_STRENGTH * np.clip(ao / np.percentile(ao[mask], 90), 0, 1)
graded *= (aof / np.median(aof[mask]))[..., None]
graded = np.clip(graded, 0, 255)
region = np.zeros((N, N), bool)
for u0, v0, side in json.loads(o.squares).values():
    x0, x1 = int(u0 * N), int(round((u0 + side) * N)); y0, y1 = N - int(round((v0 + side) * N)), N - int(v0 * N)
    region[y0:y1, x0:x1] = True
hand = mask & region
base[region] = 0
base[hand] = graded[hand]
normal[region] = (128, 128, 255)
orm[region] = (255, ref_rough, 0)
cover = hand | (headcov & ~region)
base = pad(np.clip(base, 0, 255), cover); normal = pad(normal, cover); orm = pad(orm, cover)
Image.fromarray(np.uint8(np.round(base))).save(T / f'{o.prefix}_head_basecolor.png')
Image.fromarray(np.uint8(np.round(normal))).resize((1024, 1024), Image.LANCZOS).save(T / f'{o.prefix}_head_normal_1k.png')
Image.fromarray(np.uint8(np.round(orm))).resize((1024, 1024), Image.LANCZOS).save(T / f'{o.prefix}_head_metal_rough_1k.png')
print('HEADHAND', o.prefix, 'hand texels', int(hand.sum()), 'skin ref median', np.median(ref, 0).round(1),
      'graded median', np.median(base[hand], 0).round(1), 'roughness', round(ref_rough, 1), 'seam gain', o.seam_gain)
