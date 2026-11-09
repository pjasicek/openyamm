#!/usr/bin/env python3
"""1K head texture set for the Medusa by projecting the Codex head masters onto the head faces (python3).
The Meshy head-only retexture (head_retexture_v1) painted snake scales over the whole face (the reference heads are
mostly snakes), so it is not used for colour. Instead every head texel (work/uvraster_HEAD_1024.npz: rest position and
normal) samples:
  - references_head/00_front.png through an orthographic front mapping fitted to landmarks (eye spacing horizontally;
    eyes, nose base, mouth and chin piecewise vertically: the Smart Topology face is shorter than the master's),
  - references_head/02_profile.png (her left profile; mirrored for the right side) through the same landmarks,
weighted by how squarely the surface faces each camera (cubed) and only where the surface is the front-most one along
that camera's ray (a z-buffer over the head texels: without it the front view's eyes repeated on the temples); pixels that show hair snakes (green/olive/orange, saturated)
and texels facing back/up (the scalp under the snakes) take the face's median skin colour. The neck seam is matched to
the body texture's skin luminance just below it. Normal map flat, ORM by class (skin, eye).
Writes textures/m282_head_basecolor_1k.png, _head_normal_1k.png, _head_metal_rough_1k.png, _head_material_classes.png,
textures/m282_head.json."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P = Path(__file__).resolve().parents[1]
T = P / 'textures'; T.mkdir(exist_ok=True)
R = np.load(P / 'work' / 'uvraster_HEAD_1024.npz')
piece, pos, nrm = R['piece'], R['pos'], R['nrm']
cov = piece >= 0
n = nrm / np.maximum(np.linalg.norm(nrm, axis=-1, keepdims=True), 1e-9)
EYES = (28, 30)
# ---- landmarks: 3D (z of eyes, nose base, mouth, chin, neck) and image rows
# landmarks, measured (review 2): mesh midline profile (min y per z) vs the masters' rows - jaw bottom 1.505, mouth
# line 1.548, subnasal 1.562, nose tip 1.575, eyes 1.607; front rows (midline luminance: nostril shadow, lip line, jaw
# shadow) 720 / 638 / 592 / 578 / 487; profile rows (silhouette: tip, subnasal, stomion, jaw) 785 / 680 / 638 / 600 / 500.
# The first build mapped the nose to z 1.555 (2 cm low): the painted bridge sat on the modelled tip ("double nose").
Z3 = [1.47, 1.505, 1.548, 1.562, 1.575, 1.607, 1.70, 1.76]
FRONT_V = [800, 720, 638, 592, 578, 487, 255, 105]
PROF_V = [830, 785, 680, 638, 600, 500, 221, 40]
EYE_I = 5
X_EYE_C, FRONT_U_C, FRONT_SU = -0.008, 639.0, 1916.0          # eye midpoint x, image column, px per metre
Y_EYE, PROF_U_EYE, PROF_SU = 0.13, 355.0, 2500.0     # eye column 355 (first build read 205 off a crop: ghost eyes)


def load(name):
    im = np.asarray(Image.open(P / 'references_head' / name).convert('RGBA'), np.float64) / 255
    return im


def sample(im, u, v):
    h, w = im.shape[:2]
    u = np.clip(u, 0, w - 1.001); v = np.clip(v, 0, h - 1.001)
    x0, y0 = np.floor(u).astype(int), np.floor(v).astype(int); fx, fy = (u - x0)[..., None], (v - y0)[..., None]
    c = (im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy
         + im[y0 + 1, x0 + 1] * fx * fy)
    return c


def hsv(rgb):
    h = np.asarray(Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
    return h[..., 0] * 360, h[..., 1], h[..., 2]


F, S = load('00_front.png'), load('02_profile.png')
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
vf = np.interp(z, Z3, FRONT_V); uf = FRONT_U_C + (x - X_EYE_C) * FRONT_SU
vs = np.interp(z, Z3, PROF_V); us = PROF_U_EYE + (y - Y_EYE) * PROF_SU
cf = sample(F, uf, vf); cs = sample(S, us, vs)


def snake_mask(im):
    """image-space mask of hair-snake pixels (green/olive/orange, saturated, or background), dilated 8 px so the
    shadowed snake edges and roots next to the skin are not projected either (they left grey speckles)"""
    h, s_, v = hsv(im[..., :3])
    m = ((h > 18) & (h < 160) & (s_ > 0.20)) | (im[..., 3] < 0.5)
    return ndimage.binary_dilation(m, iterations=8)


SM_F, SM_S = snake_mask(F), snake_mask(S)


def at(mask, u, v):
    hgt, wid = mask.shape
    return mask[np.clip(np.round(v).astype(int), 0, hgt - 1), np.clip(np.round(u).astype(int), 0, wid - 1)]


def snake(c):
    h, s_, v = hsv(c[..., :3])
    return ((h > 18) & (h < 160) & (s_ > 0.20)) | (c[..., 3] < 0.5)


def visible(u, v, depth, tol=0.008, cell=4):
    """z-buffer over the head texels in image space: a texel takes a camera's pixel only if it is the front-most
    surface along that camera's ray (else the front view's eye repeats on the temple behind it)"""
    m = cov.copy(); cu = np.clip((u / cell).astype(int), 0, 4096 // cell); cv = np.clip((v / cell).astype(int), 0, 4096 // cell)
    zb = np.full((4096 // cell + 1, 4096 // cell + 1), np.inf)
    np.minimum.at(zb, (cv[m], cu[m]), depth[m])
    return depth <= zb[cv, cu] + tol


face_core = (np.abs(x - X_EYE_C) < 0.065) & (z < 1.665) & (z > 1.49)


def dark_hair(c):                                                  # shadowed snake roots/hair outside the face proper
    h, s_, v = hsv(c[..., :3])
    return (v < 0.42) & ~face_core


vis_f = visible(uf, vf, y)                                         # front camera looks along +Y: smaller y is nearer
vis_s = visible(us, vs, -np.abs(x))                                # profile camera on each side: larger |x| is nearer
wf = np.clip(-n[..., 1], 0, 1) ** 3 * ~snake(cf) * ~at(SM_F, uf, vf) * ~dark_hair(cf) * vis_f
prof_eye = (((us - PROF_U_EYE) ** 2 / 55 ** 2 + (vs - PROF_V[EYE_I]) ** 2 / 38 ** 2) < 1) | \
    (((us - 530) ** 2 / 85 ** 2 + (vs - 520) ** 2 / 135 ** 2) < 1)    # + the profile's ear (the mesh has none)
# the profile's eye: our eyes face more
ws = np.clip(np.abs(n[..., 0]), 0, 1) ** 3 * ~snake(cs) * ~at(SM_S, us, vs) * ~dark_hair(cs) * vis_s * ~prof_eye * 0.8   # forward, so it would
                                                                                         # land on the temple
# median face skin from the front master (the cheeks/forehead window)
fw = F[420:700, 560:720, :3].reshape(-1, 3); fh, fs, fv = hsv(fw[None])[0], hsv(fw[None])[1], hsv(fw[None])[2]
skinpx = fw[(fs[0] < 0.25) & (fv[0] > 0.45)]
SKIN = np.median(skinpx, 0)
hair = np.clip((z - 1.665) / 0.02, 0, 1)                         # above the hairline the masters show snake roots
wf = wf * (1 - hair); ws = ws * (1 - hair)
wsum = wf + ws
col = (cf[..., :3] * wf[..., None] + cs[..., :3] * ws[..., None]) / np.maximum(wsum[..., None], 1e-6)
lum = lambda c: c @ np.array([0.2126, 0.7152, 0.0722])
eyes = np.isin(piece, EYES)
# the projected face's own skin (cheeks, nose, forehead) is the fill and neck colour, so fills and the neck carry the
# same colour as the painted face (the first fix used the master's brighter window median: a grey/white step)
pm = cov & (piece == 0) & (wsum > 0.5) & (z > 1.55) & (z < 1.64) & (np.abs(x - X_EYE_C) < 0.06) & ~eyes
pm &= lum(col) > np.percentile(lum(col[pm]), 30)
SKIN = np.median(col[pm], 0)
fill = np.clip(1 - wsum / 0.15, 0, 1)[..., None]
SCALP = np.array([0.30, 0.31, 0.24])                          # above the hairline: the shadowed gaps between the snakes
fillc = SKIN * (1 - hair[..., None]) + SCALP * hair[..., None]
col = col * (1 - fill) + fillc * fill
neck = np.clip((1.535 - z) / 0.05, 0, 1)[..., None]               # the masters shade the neck under the jaw (baked
col = col * (1 - neck) + SKIN * neck                              # shadow, a dark band in the viewer): plain skin there
# the master's nostril shadow lands on the low-poly nose's underside, which faces the camera: lift it to soft shading
nos = (z > 1.553) & (z < 1.578) & (np.abs(x - X_EYE_C) < 0.03)
floor = 0.55 * SKIN
col[nos] = np.maximum(col[nos], floor)
col[eyes] = cf[eyes, :3]                                         # the eye pieces take the front master's eyes
# ---- seam (review 2): the head skin must equal the body skin it meets. Reference = the body's own graded upper-chest
# skin in the 1K base colour (what renders below the collar); the collar choker and the neck band take the same colour
# (compose_m282.py reads neck_rgb), so head -> collar -> chest carry one skin tone.
bodyg = np.asarray(Image.open(T / 'm282_basecolor_1k.png').convert('RGB'), np.float64) / 255
B = np.load(P / 'work' / 'uvraster_BODY_1024.npz')
bh = np.asarray(Image.fromarray((bodyg * 255).astype(np.uint8)).convert('HSV'), np.float64) / 255
bp = B['pos']
bm = (B['piece'] == 0) & (bp[..., 2] > 1.30) & (bp[..., 2] < 1.40) & (np.abs(bp[..., 0]) < 0.10) & (bp[..., 1] < 0.2) & (bh[..., 1] < 0.24)
CHEST = np.median(bodyg[bm], 0)
gain = float(np.clip(lum(CHEST) / max(lum(SKIN), 1e-4), 0.7, 1.3))
measured = gain
col[~eyes] = col[~eyes] * gain
col = np.clip(col, 0, 1)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out = col[iy, ix]
Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(T / 'm282_head_basecolor_1k.png')
nm = np.zeros((1024, 1024, 3)); nm[...] = (0.5, 0.5, 1.0)
Image.fromarray((nm * 255 + 0.5).astype(np.uint8)).save(T / 'm282_head_normal_1k.png')
spec = np.where(eyes, 0.8, 0.15); rough = np.where(eyes, 0.2, 0.62)       # skin = the body's skin class
mr = np.stack([spec, rough, np.zeros_like(spec)], -1)[iy, ix]
Image.fromarray((mr * 255 + 0.5).astype(np.uint8)).save(T / 'm282_head_metal_rough_1k.png')
cls = np.where(cov, np.where(eyes, 6, 1), 0).astype(np.uint8)
Image.fromarray(cls).save(T / 'm282_head_material_classes.png')
(T / 'm282_head.json').write_text(json.dumps({'seam_gain': gain, 'chest_rgb': CHEST.tolist(), 'neck_rgb': (SKIN * gain).tolist(), 'skin_rgb': SKIN.tolist(), 'front_weight_mean':
                                               float(wf[cov].mean()), 'side_weight_mean': float(ws[cov].mean())}, indent=1))
print('HEAD seam gain', round(gain, 3), 'skin', np.round(SKIN * 255), 'front/side/fill texel share',
      round(float((wf[cov] > ws[cov]).mean()), 2), round(float((ws[cov] >= wf[cov]).mean()), 2), round(float((fill[cov] > 0.5).mean()), 2))
