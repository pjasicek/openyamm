#!/usr/bin/env python3
"""Torso paint fixes on the frozen layout (project folder): Meshy never saw the bell sleeves' inner wall (faces whose normal points at the
arm axis) and painted it near black; where the deforming sleeve lets it through it read as black shards. Those faces' texels take the
sleeve's own cloth, darker (x0.7), with the outer paint's fine luminance detail. Also every near-black texel (luminance < 35) of the
tunic cloth outside the neckline and cuff zones (the flank under the arms and the inner faces Meshy never saw; where a lowered bell
sleeve meets the flank they showed as black shards) takes the cloth colour x0.75. Writes textures/pm2_torso_tone.png."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
T = Path('textures'); Z = np.load('work/faces.npz'); J = json.load(open('work/fit_v1.blend.joints.json'))
UV, MAT, CO, NOR = Z['uv'], Z['mat'], Z['co'], Z['nor']
im = np.asarray(Image.open(T / 'pm2_torso_raw_graded.png').convert('RGB'), np.float32); S = im.shape[0]
fn = np.cross(CO[:, 1] - CO[:, 0], CO[:, 2] - CO[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
cen = CO.mean(1); inner = np.zeros(len(CO), bool); outer = np.zeros(len(CO), bool)
for s in 'LR':
    a, b, c = (np.array(J[f'Bip01 {s} {x}']) for x in ('UpperArm', 'Forearm', 'Hand'))
    for p0, p1 in ((a, b), (b, c)):
        d = (p1 - p0) / np.linalg.norm(p1 - p0); t = np.clip((cen - p0) @ d, 0, np.linalg.norm(p1 - p0))
        foot = p0 + np.outer(t, d); r = cen - foot; rl = np.linalg.norm(r, axis=1)
        near = (MAT == 1) & (rl < 0.16) & (np.sign(cen[:, 0]) == np.sign(a[0])) & (np.abs(cen[:, 0]) > 0.24)
        dot = (fn * r).sum(1) / (rl + 1e-9)
        inner |= near & (dot < -0.2); outer |= near & (dot > 0.2)
def raster(mask):
    m = Image.new('L', (S, S)); d = ImageDraw.Draw(m)
    for t in UV[mask]: d.polygon([(x * S, (1 - y) * S) for x, y in t], fill=255)
    return np.asarray(m.filter(ImageFilter.MaxFilter(5))) > 0
mi, mo = raster(inner), raster(outer) 
mo &= ~mi
ref = np.median(im[mo], 0)
lum = im.mean(2); fine = lum - np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)
out = im.copy()
out[mi] = np.clip(ref * 0.7 + fine[mi, None] * 0.6, 0, 255)
PART = Z['part']; Jh = [np.array(J[f'Bip01 {s} Hand']) for s in 'LR']
zone = (cen[:, 2] > 0.42) & (np.abs(cen[:, 0]) < 0.17) | (np.minimum(*(np.linalg.norm(cen - h, axis=1) for h in Jh)) < 0.19)
mc = raster((MAT == 1) & np.isin(PART, (1, 7)) & ~zone)
blur = np.asarray(Image.fromarray(lum.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32)
dk = mc & (blur < 35) & ~mi
out[dk] = np.clip(ref * 0.75 + fine[dk, None] * 0.6, 0, 255)
print('TONE dark cloth texels', int(dk.sum()))
Image.fromarray(out.astype(np.uint8)).save(T / 'pm2_torso_tone.png')
print('TONE inner sleeve faces', int(inner.sum()), 'outer', int(outer.sum()), 'texels', int(mi.sum()), 'cloth ref', ref.round(1).tolist())
# limbs set: the hands' forearm stub inside the sleeve (graft) was never seen by Meshy and is dark; its texels take the hands' skin x0.85
L = np.asarray(Image.open(T / 'pm2_limbs_raw_graded.png').convert('RGB'), np.float32); SL = L.shape[0]
def rasterL(mask):
    m = Image.new('L', (SL, SL)); d = ImageDraw.Draw(m)
    for t in UV[mask]: d.polygon([(x * SL, (1 - y) * SL) for x, y in t], fill=255)
    return np.asarray(m.filter(ImageFilter.MaxFilter(3))) > 0
hand = (MAT == 0) & np.isin(PART, (0, 4))
mh = rasterL(hand); ll = L.mean(2)
skin = np.median(L[mh & (ll > 110)], 0)
bl = np.asarray(Image.fromarray(ll.astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32)
st = mh & (bl < 70)
fl = ll - bl
L2 = L.copy(); L2[st] = np.clip(skin * 0.85 + fl[st, None] * 0.5, 0, 255)
Image.fromarray(L2.astype(np.uint8)).save(T / 'pm2_limbs_tone.png')
print('TONE limbs stub texels', int(st.sum()), 'skin', skin.round(1).tolist())
