#!/usr/bin/env python3
"""Paint the medallion into the body atlas from the HD head master, and turn the male's chain to silver (run from the project folder).
Args: <prefix> <master png> <cx,cy,r in master pixels> <u,v,r_uv> [mirror_lower=1] [chain=<comp id in uv npz>] [uv=<npz>] [collar=.. floor=.. silver=1]
Sources stay in textures/<prefix>_*_v7.png; the working maps are rewritten from them, so this can be rerun."""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
pre, master, circ, atl = sys.argv[1:5]
opt = dict(a.split('=', 1) for a in sys.argv[5:])
cx, cy, r = [float(x) for x in circ.split(',')]
uc, vc, ruv = [float(x) for x in atl.split(',')]
T = Path('textures')
files = {k: T / f'{pre}_{k}.png' for k in ('basecolor', 'basecolor_graded', 'normal_1k', 'metal_rough_1k', 'region_mask')}
for p in files.values():
    b = p.with_name(p.stem + '_v7.png')
    if not b.exists():
        shutil.copy2(p, b)
src = np.asarray(Image.open(master).convert('RGB'), np.float32)
N = 512
yy, xx = np.mgrid[0:N, 0:N]
dx, dy = (xx + .5) / N * 2 - 1, (yy + .5) / N * 2 - 1       # -1..1 across the disc
rad = np.hypot(dx, dy)
ang = np.arctan2(dy, dx)
if opt.get('mirror_lower') == '1':
    # the master's frame cuts the lower disc: the upper half is used twice, and the top of the rim (a notch in the master) is taken
    # from 24 degrees to its side
    sdy = -np.abs(dy)
    sdx = dx.copy()
    top = (rad > 0.62) & (np.abs(ang + np.pi / 2) < np.radians(14)) | (rad > 0.62) & (np.abs(ang - np.pi / 2) < np.radians(14))
    sdx[top] = rad[top] * np.cos(-np.pi / 2 + np.radians(24))
    sdy[top] = rad[top] * np.sin(-np.pi / 2 + np.radians(24))
else:
    sdx, sdy = dx, dy
sx, sy = cx + sdx * r, cy + sdy * r
ix, iy = np.clip(sx, 0, src.shape[1] - 2), np.clip(sy, 0, src.shape[0] - 2)
x0, y0 = ix.astype(int), iy.astype(int)
fx, fy = (ix - x0)[..., None], (iy - y0)[..., None]
img = src[y0, x0] * (1 - fx) * (1 - fy) + src[y0, x0 + 1] * fx * (1 - fy) + src[y0 + 1, x0] * (1 - fx) * fy + src[y0 + 1, x0 + 1] * fx * fy
# outside the rim the texels are never drawn, but mips and the LOD's bleed read them: the rim's colour
rim = img[(rad > 0.93) & (rad < 0.98)].mean(0)
img[rad > 0.985] = rim
disc = Image.fromarray(np.uint8(np.clip(img, 0, 255)))
base = Image.open(files['basecolor'].with_name(f'{pre}_basecolor_v7.png')).convert('RGB')
grad = Image.open(files['basecolor_graded'].with_name(f'{pre}_basecolor_graded_v7.png')).convert('RGB')
Sz = base.size[0]
rpx = ruv * Sz
box_c = (uc * Sz, (1 - vc) * Sz)
D = int(round(rpx * 2 * 1.08))
tile = disc.resize((int(round(rpx * 2)), int(round(rpx * 2))), Image.LANCZOS)
pad = Image.new('RGB', (D, D), tuple(int(x) for x in rim))
pad.paste(tile, ((D - tile.size[0]) // 2, (D - tile.size[1]) // 2))
xy = (int(round(box_c[0] - D / 2)), int(round(box_c[1] - D / 2)))
base = base.copy(); grad = grad.copy()
base.paste(pad, xy); grad.paste(pad, xy)
# chain
if 'chain' in opt:
    D_ = np.load(opt['uv'])
    m = D_['comp'] == int(opt['chain'])
    mask = Image.new('L', (Sz, Sz), 0)
    dr = ImageDraw.Draw(mask)
    for uv in D_['uv'][m]:
        dr.polygon([(u * Sz, (1 - v) * Sz) for u, v in uv], fill=255)
    mask = mask.filter(ImageFilter.MaxFilter(5))
    mk = np.asarray(mask, np.float32)[..., None] / 255
    for name, im in (('base', base), ('grad', grad)):
        a = np.asarray(im, np.float32) / 255
        L = a @ np.array([.299, .587, .114])
        L = np.asarray(Image.fromarray(np.uint8(L * 255)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
        Lm = 0.30 + 0.55 * L
        silver = np.stack([Lm * 0.96, Lm * 0.98, Lm * 1.03], -1)
        a = a * (1 - mk) + silver * mk
        out = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
        if name == 'base':
            base = out
        else:
            grad = out
# collar: Meshy's paint around the neck. Flecks of the painted chain go silver and soft; flesh blotches beyond the neckline become linen
# (nearest linen texel). collar=<cx,cy,neck_r,outer_r,hmin> in Blender metres, heights above the floor; needs uv=<npz>; floor=<z>
if 'collar' in opt:
    from scipy import ndimage
    cx_, cy_, rn, ro, hm = [float(x) for x in opt['collar'].split(',')]
    fl = float(opt['floor'])
    D_ = np.load(opt['uv'])
    Sm = 1024
    pos = np.full((Sm, Sm, 3), np.nan, np.float32)
    for uv, x, h, k in zip(D_['uv'], D_['xyz'], D_['head'], D_['hand']):
        if h or k:
            continue
        p = uv * Sm
        p = np.c_[p[:, 0], Sm - p[:, 1]]
        lo = np.floor(p.min(0)).astype(int); hi = np.ceil(p.max(0)).astype(int) + 1
        xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], Sm)), np.arange(max(lo[1], 0), min(hi[1], Sm)))
        if xs.size == 0:
            continue
        q = np.stack([xs + .5, ys + .5], -1)
        Tm = np.array([p[1] - p[0], p[2] - p[0]]).T
        if abs(np.linalg.det(Tm)) < 1e-9:
            continue
        st = (q - p[0]) @ np.linalg.inv(Tm).T
        ins = (st[..., 0] >= -.02) & (st[..., 1] >= -.02) & (st.sum(-1) <= 1.02)
        w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
        pos[ys[ins], xs[ins]] = w[ins] @ x
    r_ = np.hypot(pos[..., 0] - cx_, pos[..., 1] - cy_)
    h_ = pos[..., 2] - fl
    zone = (r_ < ro) & (h_ > hm)
    zone = np.asarray(Image.fromarray(np.uint8(zone) * 255).resize((Sz, Sz), Image.NEAREST)) > 0
    r2 = np.asarray(Image.fromarray(np.nan_to_num(r_, nan=9.0)).resize((Sz, Sz), Image.NEAREST))
    for name in ('base', 'grad'):
        a = np.asarray(base if name == 'base' else grad, np.float32) / 255
        mx, mn = a.max(2), a.min(2)
        sat = (mx - mn) / np.maximum(mx, 1e-6)
        rr, gg, bb = a[..., 0], a[..., 1], a[..., 2]
        hue = np.degrees(np.arctan2(np.sqrt(3) * (gg - bb), 2 * rr - gg - bb)) % 360
        L = a @ np.array([.299, .587, .114])
        olive = (hue > 42) & (hue < 80) & (sat > .33)
        flesh = zone & ((hue < 34) | (hue > 340)) & (sat > .36) & (L > .3) & (r2 > rn)
        flesh = ndimage.binary_dilation(flesh, iterations=2) & zone
        if 'old_medal' in opt:
            # Meshy's medallion is painted on the robe under the new disc too, and shows from low angles
            mx_, my_, mz_, mr_ = [float(v) for v in opt['old_medal'].split(',')]
            dm = np.sqrt((pos[..., 0] - mx_) ** 2 + (pos[..., 1] - my_) ** 2 + (pos[..., 2] - mz_) ** 2)
            om = np.nan_to_num(dm, nan=9.0) < mr_
            om = np.asarray(Image.fromarray(np.uint8(om) * 255).resize((Sz, Sz), Image.NEAREST)) > 0
            flesh = flesh | om
        fleck = zone & ~olive & ~flesh & ((L < .42) | (L > .9)) & (sat < .3)
        linen = (sat < .3) & (L > .55) & (L < .86) & ~flesh & ~fleck & (hue > 25) & (hue < 90)
        idx = ndimage.distance_transform_edt(~linen, return_distances=False, return_indices=True)
        # low frequencies from the nearest linen, the weave from a clean linen tile
        low = ndimage.gaussian_filter(a[idx[0], idx[1]], (5, 5, 0))
        clean = ndimage.binary_erosion(linen, iterations=48)
        ty, tx = np.argwhere(clean)[len(np.argwhere(clean)) // 2]
        tile = a[ty - 48:ty + 48, tx - 48:tx + 48]
        tile = tile - ndimage.gaussian_filter(tile, (5, 5, 0))
        yy_, xx_ = np.mgrid[0:Sz, 0:Sz]
        fill = low + tile[np.abs((yy_ % 190) - 95) % 96, np.abs((xx_ % 190) - 95) % 96]
        m = ndimage.gaussian_filter(np.float32(flesh), 1.0)[..., None]
        a = a * (1 - m) + fill * m
        if 'silver' in opt:
            Lb = ndimage.gaussian_filter(L, 0.8)
            Lm = 0.34 + 0.46 * Lb
            sv = np.stack([Lm * 0.96, Lm * 0.98, Lm * 1.03], -1)
            k = ndimage.gaussian_filter(np.float32(fleck), 0.8)[..., None]
            a = a * (1 - k) + sv * k
        out = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
        if name == 'base':
            base = out
        else:
            grad = out
    print('COLLAR flesh px', int(flesh.sum()), 'fleck px', int(fleck.sum()))
# neckline: one smooth curve in place of Meshy's ragged skin patch. neckline=<cx,h,a,b> (Blender x, height above the floor, half width, half height): skin inside
# the front ellipse, linen outside it round the neck, a thin soft shadow along the curve. Needs collar=
neck_mask = None
if 'neckline' in opt:
    from scipy import ndimage
    nx, nh, na, nb = [float(x) for x in opt['neckline'].split(',')]
    e_ = np.sqrt(((pos[..., 0] - nx) / na) ** 2 + ((pos[..., 2] - fl - nh) / nb) ** 2)
    e_ = np.where((pos[..., 1] < cy_) & ~np.isnan(e_), e_, 9.0)
    e_ = np.asarray(Image.fromarray(np.float32(e_)).resize((Sz, Sz), Image.BILINEAR))
    inside = np.clip((1.0 - e_) / 0.04 + 0.5, 0, 1)
    z2 = zone
    for name in ('base', 'grad'):
        a = np.asarray(base if name == 'base' else grad, np.float32) / 255
        mx, mn = a.max(2), a.min(2)
        sat = (mx - mn) / np.maximum(mx, 1e-6)
        hue = np.degrees(np.arctan2(np.sqrt(3) * (a[..., 1] - a[..., 2]), 2 * a[..., 0] - a[..., 1] - a[..., 2])) % 360
        L = a @ np.array([.299, .587, .114])
        olive = (hue > 42) & (hue < 80) & (sat > .33)
        core = (e_ < 0.8) & (sat > .2) & (hue < 40)
        skin = np.median(a[core], 0) if core.sum() > 20 else np.array([.86, .68, .55], np.float32)
        shade = ndimage.gaussian_filter(L, 8)
        shade = np.clip(shade / max(float(np.median(shade[core])), 1e-3), 0.9, 1.08) if core.sum() > 20 else 1.0
        sk = skin * (shade[..., None] if core.sum() > 20 else 1.0)
        linen = (sat < .3) & (L > .55) & (L < .86) & (hue > 25) & (hue < 90) & ~(e_ < 1.15)
        idx = ndimage.distance_transform_edt(~linen, return_distances=False, return_indices=True)
        low = ndimage.gaussian_filter(a[idx[0], idx[1]], (5, 5, 0))
        clean = ndimage.binary_erosion(linen, iterations=48)
        ty, tx = np.argwhere(clean)[len(np.argwhere(clean)) // 2]
        tile = a[ty - 48:ty + 48, tx - 48:tx + 48]
        tile = tile - ndimage.gaussian_filter(tile, (5, 5, 0))
        yy_, xx_ = np.mgrid[0:Sz, 0:Sz]
        cloth = low + tile[np.abs((yy_ % 190) - 95) % 96, np.abs((xx_ % 190) - 95) % 96]
        # the band round the neck: everything that is not olive trim goes to linen; inside the ellipse, to skin
        zone_c = ndimage.binary_dilation(z2, iterations=2) & ~ndimage.binary_dilation(olive, iterations=1)
        zm = ndimage.gaussian_filter(np.float32(zone_c), 1.0)[..., None]
        ins = inside[..., None]
        seam = np.clip(1 - np.abs(e_ - 1.0) / 0.035, 0, 1)[..., None] * 0.28
        fillc = cloth * (1 - ins) + sk * ins
        fillc = fillc * (1 - seam)
        a = a * (1 - zm) + fillc * zm
        out = Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255))
        if name == 'base':
            base = out
        else:
            grad = out
    neck_mask = inside
# a plain dark patch for the robe lining and cap: dark_patch=<u,v>
if 'dark_patch' in opt:
    du, dv = [float(x) for x in opt['dark_patch'].split(',')]
    pc = (du * Sz, (1 - dv) * Sz); R_ = 10
    for im in (base, grad):
        ImageDraw.Draw(im).ellipse([pc[0] - R_, pc[1] - R_, pc[0] + R_, pc[1] + R_], fill=tuple(int(x) for x in opt.get('dark_rgb', '26,22,20').split(',')))
base.save(files['basecolor']); grad.save(files['basecolor_graded'])
# ---- maps: the disc's texels are not ramped, are matt metal-free, and take a gentle relief from the art
mk = Image.open(files['region_mask'].with_name(f'{pre}_region_mask_v7.png')).convert('RGBA')
s = mk.size[0] / Sz
dr = ImageDraw.Draw(mk)
Rb = rpx * 1.1 * s
cxm, cym = box_c[0] * s, box_c[1] * s
dr.ellipse([cxm - Rb, cym - Rb, cxm + Rb, cym + Rb], fill=(0, 0, 0, 0))
if 'dark_patch' in opt:
    ImageDraw.Draw(mk).ellipse([pc[0] * s - 8, pc[1] * s - 8, pc[0] * s + 8, pc[1] * s + 8], fill=(0, 0, 0, 0))
if 'chain' in opt:
    arr = np.asarray(mk, np.float32)
    mm = np.asarray(mask.resize(mk.size, Image.BILINEAR), np.float32)[..., None] / 255
    arr = arr * (1 - mm)
    mk = Image.fromarray(np.uint8(arr), 'RGBA')
if 'chest_refit' in opt:
    # the chest window of the Elder's blue was a hue test on the old paint: redo it on this paint, closed and smooth
    from scipy import ndimage
    arr = np.asarray(mk, np.float32).copy()
    Sm = mk.size[0]
    a = np.asarray(grad.resize((Sm, Sm), Image.LANCZOS), np.float32) / 255
    mx, mn = a.max(2), a.min(2)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (a[..., 1] - a[..., 2]), 2 * a[..., 0] - a[..., 1] - a[..., 2])) % 360
    keep = (arr[..., 1] > 40) & (hue > 5) & (hue < 36) & (sat > .36)
    keep = ndimage.binary_opening(ndimage.binary_closing(keep, iterations=3), iterations=2)
    lab, n_ = ndimage.label(keep)
    if n_:
        keep = lab == (np.bincount(lab.ravel())[1:].argmax() + 1)
    arr[..., 1] = ndimage.gaussian_filter(np.float32(keep) * 255, 1.5)
    if neck_mask is not None:
        arr[..., 1] = np.asarray(Image.fromarray(np.uint8(np.clip(neck_mask, 0, 1) * 255)).resize((Sm, Sm), Image.BILINEAR), np.float32)
    mk = Image.fromarray(np.uint8(np.clip(arr, 0, 255)), 'RGBA')
mk.save(files['region_mask'])
orm = Image.open(files['metal_rough_1k'].with_name(f'{pre}_metal_rough_1k_v7.png')).convert('RGB')
s = orm.size[0] / Sz
ImageDraw.Draw(orm).ellipse([box_c[0] * s - rpx * 1.1 * s, box_c[1] * s - rpx * 1.1 * s, box_c[0] * s + rpx * 1.1 * s, box_c[1] * s + rpx * 1.1 * s], fill=(255, 120, 0))
if 'dark_patch' in opt:
    s_ = orm.size[0] / Sz
    ImageDraw.Draw(orm).ellipse([pc[0] * s_ - 7, pc[1] * s_ - 7, pc[0] * s_ + 7, pc[1] * s_ + 7], fill=(255, 255, 0))
orm.save(files['metal_rough_1k'])
nrm = Image.open(files['normal_1k'].with_name(f'{pre}_normal_1k_v7.png')).convert('RGB')
s = nrm.size[0] / Sz
dn = int(round(rpx * 2 * s * 1.08))
g = np.asarray(disc.convert('L').resize((dn, dn), Image.LANCZOS), np.float32) / 255
gy, gx = np.gradient(g)
k = 2.2
n = np.stack([-gx * k, gy * k, np.ones_like(g)], -1)
n /= np.linalg.norm(n, axis=2, keepdims=True)
nim = Image.fromarray(np.uint8((n * .5 + .5) * 255))
nrm.paste(nim, (int(round(box_c[0] * s - dn / 2)), int(round(box_c[1] * s - dn / 2))))
if 'dark_patch' in opt:
    s_ = nrm.size[0] / Sz
    ImageDraw.Draw(nrm).ellipse([pc[0] * s_ - 7, pc[1] * s_ - 7, pc[0] * s_ + 7, pc[1] * s_ + 7], fill=(128, 128, 255))
nrm.save(files['normal_1k'])
print('PAINTED', pre, 'disc px', int(rpx * 2), 'at', xy)
