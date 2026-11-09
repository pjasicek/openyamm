#!/usr/bin/env python3
"""One skin tone for face, neck, chest and hands (2026-11-02): the Codex face repaint is pale pink (cheek ~198/149/124) while Meshy's body
paint is orange (hands ~242/154/108, chest at the neckline ~248/169/108): a hard line where the head's neck meets the chest skin of the
neckline, and orange hands under a pale face. Both meet half way: every skin texel (warm hue < 40 deg, saturation 0.12-0.75, value > 0.35)
of the given set and parts is scaled per channel toward TARGET (the mean of the two medians), the scale eased in by skin-ness; hair, lips,
eyes and cloth are left out by hue and value. Args: <set: head|body> <in png> <out png> (project folder)"""
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw
SET, SRC, DST = sys.argv[1:4]
TARGET = np.array([236.0, 140.0, 88.0])      # review 2026-11-02: the v2 face repaint's warm tan (MM9 F4's skin is a strong orange tan)
# second review pass (r20): the face read light peach in the viewer's bright light; TAN deepens the head's skin and the body follows the
# tanned head (work/head_skin.json, written by the head pass); BLUSH adds rosy cheek apples (MM9 F4a: tanned, rosy)
TAN = np.array([float(x) for x in os.environ.get('TAN', '1,1,1').split(',')]); BLUSH = float(os.environ.get('BLUSH', '0'))
if SET == 'body' and os.environ.get('BODYFROMHEAD') and os.path.exists('work/head_skin.json'):
    TARGET = np.array(json.load(open('work/head_skin.json'))['median'])
D = np.load('work/uv.npz'); tri, uv, mat, comp = D['tri'], D['uv'], D['mat'], D['comp']; names = [str(x) for x in D['names']]
im = np.asarray(Image.open(SRC).convert('RGB'), np.float32); S = im.shape[0]
M = 1 if SET == 'head' else 0
parts = [names.index('head')] if SET == 'head' else [names.index('hands'), names.index('dress')]
lab = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(lab)
for f in np.where((mat == M) & np.isin(comp[tri[:, 0]], parts))[0]: dr.polygon([(float(uv[v, 0] * S), float((1 - uv[v, 1]) * S)) for v in tri[f]], fill=255)
part = np.asarray(lab) > 0
hsv = np.asarray(Image.fromarray(im.astype('u1')).convert('HSV'), np.float32) / 255
h, s, v = hsv[..., 0] * 360, hsv[..., 1], hsv[..., 2]
skin = part & ((h < 40) | (h > 350)) & (s > 0.12) & (s < 0.75) & (v > 0.35)
lips = (h < 12) | (h > 340)
skin &= ~(lips & (s > 0.35))
if SET == 'head':
    # the neck (below the projected face window, 1.53 m over the soles) first takes the face's tone, eased in over 2 cm
    U2 = np.load('work/uv_tex2.npz'); Z0 = -0.9297; ZS = np.full((S, S), np.nan, np.float32); XY = np.full((S, S, 2), np.nan, np.float32)
    for f in np.where((U2['mat'] == 1) & (U2['comp'][U2['tri'][:, 0]] == names.index('head')))[0]:
        q = U2['uv'][U2['tri'][f]] * [S, -S] + [0, S]; x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), S - 1)
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
        if abs(np.linalg.det(T_)) < 1e-12: continue
        l_ = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l_, 1 - l_.sum(1)]; ins = (L3 >= -0.01).all(1)
        ZS[(gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)] = L3[ins] @ U2['co'][U2['tri'][f]][:, 2] - Z0
        XY[(gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)] = L3[ins] @ U2['co'][U2['tri'][f]][:, :2]
    zz = np.nan_to_num(ZS, nan=0.0); xy = np.nan_to_num(XY, nan=0.0)
    face = skin & (zz > 1.56) & (zz < 1.66); neck = skin & (zz > 1.40) & (zz < 1.52)
    if face.sum() > 100 and neck.sum() > 100:
        gn = np.median(im[face], 0) / np.median(im[neck], 0)
        wn = (np.clip((1.555 - zz) / 0.03, 0, 1) * (zz > 1.38))[..., None] * skin[..., None]
        im = im * (1 - wn) + np.clip(im * gn, 0, 255) * wn
        print('SKINMATCH neck to face gains', np.round(gn, 3).tolist())
med = np.median(im[skin], 0); g = TARGET / med
if SET == 'head': g = TAN      # v2: the face keeps the repaint's own warm tone (times TAN); the body follows it
w = np.clip((s - 0.12) / 0.08, 0, 1) * np.clip((v - 0.35) / 0.1, 0, 1) * skin
out = im * (1 - w[..., None]) + np.clip(im * g, 0, 255) * w[..., None]
if SET == 'head' and BLUSH > 0:
    # cheek apples: 4.2 cm off the midline, 1.590 m over the soles (2.4 cm under the eye centres), front-facing skin, soft 1.6 cm blobs
    bl = np.zeros((S, S), np.float32)
    for sx in (1, -1):
        dd = ((xy[..., 0] - 0.042 * sx) ** 2 + (zz - 1.590) ** 2) / 0.016 ** 2
        bl = np.maximum(bl, np.exp(-dd) * (xy[..., 1] < -0.06))
    bl = ndimage.gaussian_filter(bl * skin, 1.0) * BLUSH
    out = out * (1 - bl[..., None]) + out * np.array([1.03, 0.86, 0.84]) * bl[..., None]
    print('SKINMATCH blush texels', int((bl > 0.2 * BLUSH).sum()))
if SET == 'head':
    json.dump({'median': np.median(out[skin & (zz > 1.56) & (zz < 1.66)], 0).tolist()}, open('work/head_skin.json', 'w'))
Image.fromarray(np.clip(out + 0.5, 0, 255).astype('u1')).save(DST); print('SKINMATCH', SET, 'median', np.round(med).tolist(), 'gains', np.round(g, 3).tolist(), 'texels', int(skin.sum()))
