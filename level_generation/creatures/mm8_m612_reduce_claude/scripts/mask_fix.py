#!/usr/bin/env python3
"""Gog region-mask spill at the claw bases, heel spurs and spine bases: the gold, dotted keratin band where each claw, toe claw,
heel spur and shoulder/back/tail spine meets the skin carries the skin mask, so tiers B and C ramp it to pale blue /
pink (the installed model too). Clears the mask on gold texels (hue 25-62 degrees, soft edge to 70) of the faces
next to non-head keratin faces (two rings) and of every hand and foot face (heel spurs are skin-class faces; head excluded, its skin has yellow-green tones that must stay ramped).
Pale keratin (spur tips) is cleared too, on limb, shoulder and tail faces only. Base colour unchanged. -> work/mask_fixed.png (prints texel counts). Run uv_faceid.py first."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); f = d['faces']; n = len(d['verts'])
fb = np.load('work/face_bones.npz'); names = [str(x) for x in fb['names']]; bone = np.array([names[i] for i in fb['dom']])
spec = np.load('work/face_spec.npy'); ker = (spec > 190) & (bone != 'B_Head')
near = ker.copy()
for _ in range(2):
    vs = np.zeros(n, bool); vs[f[near].ravel()] = True; near = vs[f].any(1)
near &= bone != 'B_Head'
fid = np.load('work/uv_faceid.npy')
img = Image.open('work/img3.png'); mk = np.asarray(img).astype(np.float32)
bc = np.asarray(Image.open('work/img0.png').convert('RGB'), np.float32) / 255
r, g, b = bc[..., 0], bc[..., 1], bc[..., 2]; mx = bc.max(2); dd = mx - bc.min(2) + 1e-6
hue = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60
gold = np.clip((70 - hue) / 8, 0, 1) * (hue > 25)
# pale, unsaturated keratin (spur and claw tips) only on limbs, shoulders and tail: the belly plates on the pelvis
# and spine are pale too and stay ramped
sat = dd / (mx + 1e-6)
pale = np.clip((.45 - sat) / .1, 0, 1) * np.clip((mx - .4) / .1, 0, 1)
limbish = (np.char.find(bone, 'Finger') >= 0) | np.char.startswith(bone, 'Tail') | np.isin(bone, [
    'B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0', 'B_L_Clavicle', 'B_R_Clavicle',
    'B_L_UpperArmTwist', 'B_R_UpperArmTwist'])
limb = (np.char.find(bone, 'Finger') >= 0) | np.isin(bone, ['B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0',
                                                             'B_R_Toe0'])
# the heel spurs are beige keratin painted on skin-class faces (specular 64), away from any keratin face: on the hands
# and feet (green skin, hue above 70) every gold texel is keratin
zone = (fid >= 0) & (near | limb)[np.clip(fid, 0, None)]
pzone = zone & limbish[np.clip(fid, 0, None)]
gold = np.maximum(gold, np.where(pzone, pale, 0))
# texels of the gutter next to zone texels follow them (bilinear filtering and mips read across the chart edge)
from scipy.ndimage import binary_dilation
zone_d = binary_dilation(zone, iterations=3) & (fid < 0) | zone
w = np.where(zone_d, gold, 0)
before = mk[..., 0].copy()
mk[..., 0] = mk[..., 0] * (1 - w)
changed = (before - mk[..., 0]) > 8
Image.fromarray(np.clip(mk + .5, 0, 255).astype(np.uint8), img.mode).save('work/mask_fixed.png')
print('MASKFIX faces near keratin', int(near.sum()), 'texels changed', int(changed.sum()), 'of which inside faces', int((changed & (fid >= 0)).sum()))
