#!/usr/bin/env python3
"""Head sets from the four Codex views, one source per layer (third pass, 2026-10-31; the first version projected every view through the helmet onto every layer, so the side views' eyes landed on
the cheek plates and their helmet on the throat).
- Helmet texels take a view only where a z-buffer of the whole head says the texel is seen from that side and the view's pixel is helmet (head_masks.face_mask); never skin.
- Skin texels take the FRONT view only, its pixels outside the face filled from the nearest skin, so no helmet can land on the face or the neck; the sides and back of the neck are the nearest skin, soft.
- Both layers are then darkened by exposure: the share of a dome of viewpoints that sees the texel past the helmet and the front plate (make_plate.py). Hidden skin and the helmet's inside go dark.
Normal: leather and steel relief from the luminance. Writes textures/guard_head{a,c}_basecolor.png, _normal_1k.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, 'scripts')
from head_masks import face_mask, view_fit
from head_zbuf import zbuffer, basis
S = 2048
Dz = np.load('work/head_faces.npz')
P3, N3, U3, PT = Dz['p'], Dz['n'], Dz['u'], Dz['part']
pos = np.zeros((S, S, 3), np.float32); nrm = np.zeros((S, S, 3), np.float32); part = np.zeros((S, S), np.uint8); cov = np.zeros((S, S), bool)
for k in range(len(P3)):
    q = np.c_[U3[k, :, 0], 1 - U3[k, :, 1]] * S                 # image rows
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int) - 1, 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int) + 1, S - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = q
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1
    m = (l0 >= -0.02) & (l1 >= -0.02) & (l2 >= -0.02)
    ny, nx = ys[m].astype(int), xs[m].astype(int)
    pos[ny, nx] = l0[m, None] * P3[k, 0] + l1[m, None] * P3[k, 1] + l2[m, None] * P3[k, 2]
    nrm[ny, nx] = l0[m, None] * N3[k, 0] + l1[m, None] * N3[k, 1] + l2[m, None] * N3[k, 2]
    part[ny, nx] = PT[k]; cov[ny, nx] = True
nrm /= np.maximum(np.linalg.norm(nrm, axis=2, keepdims=True), 1e-6)
helm = P3[PT == 3].reshape(-1, 3)
lo, hi = helm.min(0), helm.max(0)
top = hi[2]
print('helmet', lo.round(3), hi.round(3), 'covered', cov.mean().round(3))
VIEWS = {'01_front': (0, 0, 1), '02_back': (180, 0, -1), '03_left': (90, 1, 1), '04_right': (-90, 1, -1)}
valid = np.where(cov)
Pv, Nv, Tv = pos[valid], nrm[valid], part[valid]
Ct = (0.0, 0.02, 0.78); HALF = 0.2; RES = 800
isface = Tv == 2


def seen(Ps, az, el):
    """Texels of Pv a camera at (az, el) sees: depth within 5 mm of the z-buffer."""
    F, Z, (r, u, d) = zbuffer(Ps, az, el, RES, HALF, Ct)
    Q = Pv - np.array(Ct)
    sx = np.clip(((Q @ r) / HALF + 1) * RES / 2, 0, RES - 1).astype(int); sy = np.clip((1 - (Q @ u) / HALF) * RES / 2, 0, RES - 1).astype(int)
    return (Z[sy, sx] - (Q @ d) < 0.005) & (F[sy, sx] >= 0), d


def bilinear(im, x, y):
    h, w = im.shape[:2]
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy


for t in 'ac':
    PL = np.load(f'work/plate_{t}.npz')['p']
    Pall = np.concatenate([P3, PL])
    acc = np.zeros((len(Pv), 3), np.float32); wt = np.zeros(len(Pv), np.float32)
    for name, (az, axis, sign) in VIEWS.items():
        im = np.asarray(Image.open(f'references_head/{t}_{name}.png').convert('RGBA'), np.float32) / 255
        fit = view_fit(im, lo, hi, axis)
        c0, c1, y0, y1, pxm = fit['c0'], fit['c1'], fit['y0'], fit['y1'], fit['pxm']
        al = im[..., 3] > 0.5
        fm = face_mask(im, name)
        hm = al & ~ndimage.binary_dilation(fm, iterations=6)                 # the view's helmet pixels, exactly
        m0 = lo[axis]
        coord = Pv[:, axis]
        col = (c0 + (coord - m0) * pxm) if sign > 0 else (c1 - (coord - m0) * pxm)   # side views: y grows to IMAGE RIGHT on 03_left
        rw = y0 + (top - Pv[:, 2]) * pxm
        rgb = bilinear(im, col, rw)[:, :3]
        inh = hm[np.clip(rw.astype(int), 0, hm.shape[0] - 1), np.clip(col.astype(int), 0, hm.shape[1] - 1)]
        vis, d = seen(P3, az, 0)
        w = np.clip(Nv @ d - 0.12, 0, 1) ** 3.5 * vis * inh * (~isface)
        acc += rgb * w[:, None]; wt += w
        if name == '01_front':                                               # skin plate: the face's pixels, the rest filled from the nearest skin
            core = ndimage.binary_erosion(fm, iterations=4)
            _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
            skin = im[..., :3][iy, ix]
            if t == 'c':                                                     # skin behind the plate: only a shadow from an angle
                skin = skin * (1 - 0.7 * ndimage.gaussian_filter(np.load('work/plate_c.npz')['region'].astype(np.float32), 5))[..., None]
            f_rgb = bilinear(skin, col, rw)
            wf = (isface & (Nv @ d > 0.22) & (rw < y1 - 10)).astype(np.float32)
            acc += f_rgb * wf[:, None]; wt += wf
    good = wt > 1e-4
    col = np.zeros_like(acc); col[good] = acc[good] / wt[good, None]
    for pid in np.unique(Tv):                                               # gaps: nearest surface point of the same layer
        m = (Tv == pid); g_ = m & good; b_ = m & ~good
        if b_.sum() and g_.sum():
            _, ii = cKDTree(Pv[g_]).query(Pv[b_])
            col[b_] = col[g_][ii]
    print(t, 'unseen texels', round(float((~good).mean()), 3), 'skin', round(float((~good[isface]).mean()), 3), 'helmet', round(float((~good[~isface]).mean()), 3))
    # exposure: a dome of viewpoints past the helmet and the plate
    Ec = np.zeros(len(Pv), np.float32); En = np.zeros(len(Pv), np.float32)
    for el in (-50, -25, 0, 25):
        for az in range(-150, 181, 30):
            v, d = seen(Pall, az, el)
            fr = Nv @ d > 0.05
            Ec += v & fr; En += fr
    Ex = np.zeros((S, S), np.float32); Ex[valid] = Ec / np.maximum(En, 1)
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    Ex = ndimage.gaussian_filter(Ex[iy, ix], 2.5); Es = ndimage.gaussian_filter(Ex, 7)
    print(t, 'exposure of skin p10/50/90', np.percentile(Ex[valid][isface], [10, 50, 90]).round(3))
    sstep = lambda a, b, x: (lambda u: u * u * (3 - 2 * u))(np.clip((x - a) / (b - a), 0, 1))
    out = np.zeros((S, S, 3), np.float32); out[valid] = col
    out = out[iy, ix]
    # helmet tone toward the MM9 skins (leather darker, steel a little)
    gh_ = {'a': 0.7, 'c': 0.86}[t]
    hk = ndimage.gaussian_filter((part != 2).astype(np.float32), 1.5)[..., None]
    out = out * (1 - hk) + out * gh_ * hk
    # the jaw's underside: front pixels at a grazing angle, soft
    nf = np.zeros((S, S), np.float32); nf[valid] = -Nv[:, 1]; nf = nf[iy, ix]
    wj = ndimage.gaussian_filter(((part == 2) & (nf < 0.4)).astype(np.float32), 3)[..., None]
    bj = np.dstack([ndimage.gaussian_filter(out[..., k], 6) for k in range(3)])
    out = out * (1 - wj) + bj * wj
    # the neck: soft plain skin, no streaks
    low = (part == 2) & (pos[..., 2] < 0.70)
    bl = np.dstack([ndimage.gaussian_filter(out[..., k], 7) for k in range(3)])
    wl = ndimage.gaussian_filter(low.astype(np.float32), 3)[..., None]
    out = out * (1 - wl) + bl * wl
    fsk = 0.18 + 0.82 * sstep(0.02, 0.15, Es); fhm = 0.14 + 0.86 * sstep(0.0, 0.1, Ex)
    fall = np.where(part == 2, fsk, fhm)
    out = out * ndimage.gaussian_filter(fall, 1.5)[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(f'textures/guard_head{t}_proj.png')
    # relief from the colour's fine luminance, tangent space (glTF: +y up the image)
    lum = (out @ np.array([0.2126, 0.7152, 0.0722], np.float32))
    hp = lum - ndimage.gaussian_filter(lum, 8)
    gy, gx = np.gradient(ndimage.gaussian_filter(hp, 0.9))
    k = 7.0
    n_ = np.dstack([-gx * k, gy * k, np.ones_like(gx)]); n_ /= np.linalg.norm(n_, axis=2, keepdims=True)
    nim = Image.fromarray(((n_ * 0.5 + 0.5) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
    nim.save(f'textures/guard_head{t}_normal_1k.png')
    # basecolor with the lining's dark patch
    J = json.load(open('work/dark_texel.json'))['head']
    arr = (np.clip(out, 0, 1) * 255).astype(np.uint8).copy()
    yy, xx = np.ogrid[:S, :S]; arr[(xx - int(J['u'] * S)) ** 2 + (yy - int(J['v'] * S)) ** 2 < 256] = (22, 18, 16)
    Image.fromarray(arr).save(f'textures/guard_head{t}_basecolor.png')
