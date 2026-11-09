#!/usr/bin/env python3
"""Tier B (Sergeant, MM9 GUARD2): chain as the Captain, the Guard's leather boots, a brown leather mantle over the shoulders, chest and back. No paint of its own: composed per texel from
tiers A and C on one UV layout, by garment and 3D position. The mantle is tier A's own texels plus a region mask and a colour ramp (the only colour-only difference between the tiers, so it stays a ramp,
16 stops from the leather of the MM9 GUARD2 skin at albedo x 1.15), brooches keep A's gold. The Captain's greaves go:
below the knee the chain is carried down the leg from the thigh (colour lookup at the same angle, 34 cm up; relief from the colour). Run in the project folder."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
S = 2048
D = np.load('work/body_faces.npz')
P3, U3, PT = D['p'], D['u'], D['part']
pos = np.zeros((S, S, 3), np.float32); part = np.zeros((S, S), np.uint8)
for k in range(len(P3)):
    q = np.c_[U3[k, :, 0], 1 - U3[k, :, 1]] * S
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 1, S - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = q
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1
    m = (l0 >= -0.03) & (l1 >= -0.03) & (l2 >= -0.03)
    ny, nx = ys[m].astype(int), xs[m].astype(int)
    pos[ny, nx] = l0[m, None] * P3[k, 0] + l1[m, None] * P3[k, 1] + l2[m, None] * P3[k, 2]
    part[ny, nx] = PT[k]
cov = part > 0
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
pos = pos[iy, ix]; part = part[iy, ix]
A = np.asarray(Image.open('textures/guard_a_basecolor_graded.png').convert('RGB'), np.float32)
C = np.asarray(Image.open('textures/guard_c_basecolor_graded.png').convert('RGB'), np.float32)
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]; ax = np.abs(x)
# the skin in the collar's V: Meshy painted it pale cream, the head set's neck is darker
skinv = (part == 1) & (y < 0) & (z > 0.585) & (ax < (z - 0.585) * 1.1 + 0.014)
for name, im in (('a', A), ('c', C)):
    m_ = skinv & (im[..., 0] > 190) & (im[..., 0] > im[..., 2] * 1.25)
    k_ = ndimage.gaussian_filter(m_.astype(np.float32), 1.0)[..., None]
    im[:] = im * (1 - k_) + im * np.array([0.745, 0.616, 0.664], np.float32) * k_
    # tone toward the MM9 skins, measured (albedo about 1.4 x a skin with baked shading): GUARD1 tunic 71,29,16, trousers 29,13,8, boots 47,29,20; GUARD2/3 chain 53. The paint came back twice as bright
    if name == 'a':
        gain = np.where(np.isin(part, [13, 10]), 0.85, 0.72)
    else:
        gain = np.where(part == 5, 0.76, np.where(np.isin(part, [1, 7]), 0.9, 1.0))
    gain = np.where(m_, 1.0, gain)[..., None]
    gain = gain * 1.0
    sat = 0.92 if name == 'a' else 1.0
    lm = (im @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    im[:] = (lm + (im - lm) * sat) * gain
    if name == 'c':                                                  # chain links: compress the speculars Meshy painted in, so the mail reads dark at distance as in GUARD2/3
        sat_ = (im.max(2) - im.min(2)) / np.maximum(im.max(2), 1)
        cm = np.isin(part, [1, 5, 7]) & (sat_ < 0.12)
        v_ = im.max(2)
        k_ = np.where(cm & (v_ > 95), (95 + (v_ - 95) * 0.45) / np.maximum(v_, 1), 1.0)[..., None]
        im[:] = im * k_
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(f'textures/guard_{name}_final.png')


def sstep(v, a, b):
    t = np.clip((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


# boots from A
boots = np.isin(part, [6, 15]) * (z < -0.4)
# mantle: chest V to z 0.40 at the centre, rising to the shoulder; upper arms to a third of their length
vee = sstep(z - (0.395 + 0.52 * ax), -0.006, 0.006)
arm = sstep(0.30 - ax, -0.006, 0.006) * sstep(ax, 0.2, 0.21)
mantle = (part == 1) * np.maximum(vee * (ax < 0.26), arm * (z > 0.3))
B = C.copy()
# lower legs: chain from the thigh of tier C
leg = (part == 5)
thigh = leg & (z > -0.24) & (z < -0.05)
low = leg & (z < -0.26)
tv = np.where(thigh)
tree = cKDTree(pos[tv])
lv = np.where(low)
q = pos[lv].copy()
q[:, 2] = -0.235 + ((q[:, 2] + 0.26) % 0.17)                         # the 17 cm band of thigh chain, tiled down the leg
q[:, 0] += np.sign(q[:, 0]) * 0.02 * 0 + (np.sign(q[:, 0]) * (0.125 + 0.2 * (-0.15 - q[:, 2])) - np.sign(q[:, 0]) * (0.147 + 0.094 * (-pos[lv][:, 2] - 0.37))) # shin axis onto the thigh axis
_, ii = tree.query(q)
B[lv] = C[tv[0][ii], tv[1][ii]]
blend = sstep(z, -0.30, -0.24)[..., None] * leg[..., None] + (~leg)[..., None]
B = B * blend + C * 0 + (1 - blend) * B
m3 = ndimage.gaussian_filter((mantle > 0.5).astype(np.float32), 1.2)[..., None]
B = B * (1 - m3) + A * m3
br = (part == 13)[..., None]
B = np.where(br, A, B)
bm = ndimage.gaussian_filter(boots.astype(np.float32), 1.0)[..., None]
B = B * (1 - bm) + A * bm
Image.fromarray(np.clip(B, 0, 255).astype(np.uint8)).save('textures/guard_b_final.png')
# region mask (R mantle) and ramp, engine contract CLAUDE_CREATURE_TEXTURES.md; pad the mask into the gutters first
import json, sys
sys.path.insert(0, '../claude_shared')
import region_variants as RV
mk = np.where(br[..., 0] | skinv, 0, (mantle > 0.5).astype(np.float32))
mk = ndimage.gaussian_filter(mk, 1.2)
Image.fromarray(np.dstack([(mk * 255).astype(np.uint8)] + [np.zeros((S, S), np.uint8)] * 2 + [np.full((S, S), 255, np.uint8)]), 'RGBA').resize((1024, 1024), Image.BILINEAR).save('textures/guard_b_region_mask.png')
lin = RV.srgb_to_linear(np.clip(B, 0, 255) / 255.0)
lum_l = lin @ RV.LUMA
lo, hi = np.percentile(lum_l[mk > 0.9], [4, 97])
sk = np.asarray(Image.open('source/g2/skins/guard2.png').convert('RGB'), np.float32)
leather = sk[(sk[..., 0] > sk[..., 1] * 1.25) & (sk[..., 0] > 40) & (sk[..., 0] < 170) & (np.arange(256)[:, None] > 70) & (np.arange(256)[:, None] < 165)]
lk = (leather @ np.array([0.2126, 0.7152, 0.0722], np.float32))
order = np.argsort(lk); leather = leather[order]
stops = np.array([leather[int(q * (len(leather) - 1))] for q in np.linspace(0.03, 0.97, 16)], np.float64)
stops = ndimage.gaussian_filter1d(stops, 1.0, axis=0, mode='nearest')
colors = RV.srgb_to_linear(np.clip(stops / 255.0 * 1.15, 0, 1))
json.dump(dict(range=[round(float(lo), 6), round(float(hi), 6)], colors=np.round(colors, 6).tolist()), open('textures/guard_b_ramp.json', 'w'))
print('RAMP', round(float(lo), 4), round(float(hi), 4), 'leather texels', len(leather), np.round(stops[[0, 8, 15]]).tolist())
# normal and ORM at 1K
down = lambda a: np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32) / 255
mA = down(np.maximum(m3[..., 0], bm[..., 0]))[..., None]
na = np.asarray(Image.open('textures/guard_a_normal_1k.png').convert('RGB'), np.float32); nc = np.asarray(Image.open('textures/guard_c_normal_1k.png').convert('RGB'), np.float32)
oa = np.asarray(Image.open('textures/guard_a_metal_rough_1k.png').convert('RGB'), np.float32); oc = np.asarray(Image.open('textures/guard_c_metal_rough_1k.png').convert('RGB'), np.float32)
lum = (B @ np.array([0.2126, 0.7152, 0.0722], np.float32)) / 255
hp = lum - ndimage.gaussian_filter(lum, 6)
gy, gx = np.gradient(ndimage.gaussian_filter(hp, 0.8))
nf = np.dstack([-gx * 5, gy * 5, np.ones_like(gx)]); nf /= np.linalg.norm(nf, axis=2, keepdims=True)
nf1 = np.asarray(Image.fromarray(((nf * 0.5 + 0.5) * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32)
ml = down((low & ~boots).astype(np.float32))[..., None]
N = nc * (1 - mA) + na * mA
N = N * (1 - ml) + nf1 * ml
Image.fromarray(N.astype(np.uint8)).save('textures/guard_b_normal_1k.png')
Image.fromarray((oc * (1 - mA) + oa * mA).astype(np.uint8)).save('textures/guard_b_metal_rough_1k.png')
print('TIER B', 'mantle', round(float((mantle > 0.5).mean()), 3), 'boots', round(float(boots.mean()), 3), 'low leg', round(float(low.mean()), 3))
np.savez_compressed('work/body_pos.npz', pos=pos.astype(np.float16), part=part)
