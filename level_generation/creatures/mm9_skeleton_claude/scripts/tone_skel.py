#!/usr/bin/env python3
"""Tone of the paint, part by part (work/faces.npz). Eyes: the sockets are too deep for the projected paint, so both eye spheres get their colour here, interpolated over the sphere: right eye green with a bright middle (MM9's SKELETON2),
left eye a dark dead ball; the emission masks follow (textures/skel_eye_mask_a.png right eye, _r both). Reads textures/*_basecolor_graded.png, writes *_basecolor_final.png."""
import numpy as np
from PIL import Image
F = np.load('work/faces.npz')
from scipy import ndimage
from PIL import ImageDraw
SCR = [52, 142, 134, 109, 144, 127]
LUM = np.array([0.3, 0.59, 0.11])


def raster(uv, ids, S):
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    keep = np.isin(F['pid'], ids) & (F['lining'] == 0)
    for t in uv[keep]:
        d.polygon([(float(u * S), float((1 - v) * S)) for u, v in t], fill=255)
    return ndimage.binary_dilation(np.asarray(im) > 0, iterations=3)


# --- body: bone blobs the projection left on the leather (thin parts catch the ribs behind them), rope to tan, bone to the skull's ochre
b = np.asarray(Image.open('textures/skel_basecolor_graded.png').convert('RGB'), np.float32) / 255
S = b.shape[0]
h_ = np.asarray(Image.open('textures/skel_head_basecolor_graded.png').convert('RGB'), np.float32) / 255
cr = raster(F['uh'], [2000], S)
vest = raster(F['ub'], [2, 47, 300, 124] + SCR, S); strap = raster(F['ub'], [14, 95], S); rope = raster(F['ub'], [13, 301], S); cuff = raster(F['ub'], [41, 54, 11], S)
lum = b @ LUM
out = b.copy()
for mask, top, name in ((vest, 0.27, 'vest'), (strap, 0.22, 'strap')):
    core = mask & (lum < top * 0.8)
    med = np.median(b[core], 0)
    bad = mask & (lum > top)
    bad = ndimage.binary_dilation(ndimage.binary_opening(bad, iterations=2), iterations=3) & mask
    # leather of the neighbours flows in: distance transform from the good texels of the part
    good = mask & ~bad & (lum < top)
    _, (iy, ix) = ndimage.distance_transform_edt(~good, return_indices=True)
    fill = b[iy, ix]
    w = np.clip(ndimage.gaussian_filter(bad.astype(np.float32), 1.5) * 1.4, 0, 1)[..., None]
    out = out * (1 - w) + fill * w
    print(name, 'bone blobs %', round(float(bad.sum()) / max(1, mask.sum()) * 100, 1), 'median', np.round(med * 255))
# ribs and hip balls: the projection put the vest and the master's grey strap on the bones behind them; those texels take the neighbouring bone (no leather or grey on a rib)
rb = raster(F['ub'], [18, 57, 100, 82, 50, 3, 97, 64, 68, 92, 102, 31, 38, 115, 126], S)
mx_, mn_ = out.max(2), out.min(2); sat_ = (mx_ - mn_) / np.maximum(mx_, 1e-5); L_ = out @ LUM
badr = rb & ((L_ < 0.24) | (sat_ < 0.2))
badr = ndimage.binary_dilation(ndimage.binary_opening(badr, iterations=1), iterations=2) & rb
goodr = rb & ~badr
_, (iy, ix) = ndimage.distance_transform_edt(~goodr, return_indices=True)
fill = ndimage.gaussian_filter(out[iy, ix], (2.0, 2.0, 0))
w = np.clip(ndimage.gaussian_filter(badr.astype(np.float32), 1.5) * 1.4, 0, 1)[..., None]
out = out * (1 - w) + fill * w
print('ribs repainted %', round(float(badr.sum()) / rb.sum() * 100, 1))
# flat patches: faces no master view showed (tops of the metatarsals, under the rope) came back one even colour; neighbouring bone flows in
lf = out @ LUM
cov = np.asarray(Image.open('textures/skel_normal_1k.png').convert('L').resize((S, S)), np.float32) > -1
m1 = ndimage.uniform_filter(lf, 7); m2 = ndimage.uniform_filter(lf * lf, 7); sd = np.sqrt(np.maximum(m2 - m1 * m1, 0))
allp = raster(F['ub'], [p_ for p_ in np.unique(F['pid']) if p_ < 2000], S)
flat = allp & (sd < 0.0035) & (lf > 0.25)
flat = ndimage.binary_opening(flat, iterations=3)
flat = ndimage.binary_dilation(flat, iterations=4) & allp
good = allp & ~flat & (lf > 0.25)
_, (iy, ix) = ndimage.distance_transform_edt(~good, return_indices=True)
fill = ndimage.gaussian_filter(out[iy, ix], (1.5, 1.5, 0))
w = np.clip(ndimage.gaussian_filter(flat.astype(np.float32), 2.0) * 1.3, 0, 1)[..., None]
out = out * (1 - w) + fill * w
print('flat patches %', round(float(flat.sum()) / allp.sum() * 100, 2))
# strap: very dark, with its highlights kept down
L = out @ LUM
k = np.where(strap, np.minimum(1.0, 0.17 / np.maximum(L, 1e-3)), 1.0)[..., None]
out = out * k
rp = np.clip(ndimage.gaussian_filter(rope.astype(np.float32), 1.0), 0, 1)[..., None]
out = out * (1 - rp) + out * np.array([0.82, 0.66, 0.46]) * rp
bone = ~(vest | strap | rope | cuff) & (lum > 0.3)
hb = np.median(h_[cr & ((h_ @ LUM) > 0.3)], 0); bb = np.median(out[bone], 0)
gain = hb / bb
print('bone median body', np.round(bb * 255), 'skull', np.round(hb * 255), 'gain', np.round(gain, 3))
bw = np.clip(ndimage.gaussian_filter((~(vest | strap | rope | cuff)).astype(np.float32), 2.0), 0, 1)[..., None]
g2 = gain ** 0.8
out = out * (1 - bw) + np.clip(out * g2, 0, 1) * bw
Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8)).save('textures/skel_basecolor_final.png')
a = np.asarray(Image.open('textures/skel_head_basecolor_graded.png').convert('RGB'), np.float32) / 255
# green specks of the master's eye on the cranium: the neighbouring bone
crb = raster(F['uh'], [2000, 2001], a.shape[0])
hx, hn = a.max(2), a.min(2); hr = a[..., 0]; hg = a[..., 1]; hb_ = a[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (hg - hb_), 2 * hr - hg - hb_)) % 360
gs = crb & (hue > 75) & (hue < 190) & ((hx - hn) > 0.03)
gs = ndimage.binary_dilation(gs, iterations=4) & crb
gd = crb & ~gs
_, (iy, ix) = ndimage.distance_transform_edt(~gd, return_indices=True)
a = np.where(gs[..., None], a[iy, ix], a)
print('green specks', int(gs.sum()))
S = a.shape[0]
mask_r = np.zeros((S, S), np.float32); mask_l = np.zeros((S, S), np.float32)
cols = {2002: (np.array([0.02, 0.16, 0.03]), np.array([0.62, 1.0, 0.25])), 2003: (np.array([0.012, 0.01, 0.01]), np.array([0.05, 0.045, 0.04]))}
for pid_, (dark, hot) in cols.items():
    f = np.where((F['pid'] == pid_) & (F['lining'] == 0))[0]
    uv = F['uh'][f]; co = F['fco'][f]; c = co.reshape(-1, 3).mean(0); fw = np.array([0, -1.0, 0])
    n = (co - c); n /= np.linalg.norm(n, axis=2, keepdims=True)
    k = np.clip(n @ fw, 0, 1)
    for t, kk in zip(uv, k):
        p = np.c_[t[:, 0] * S, (1 - t[:, 1]) * S]
        lo = np.floor(p.min(0)).astype(int) - 1; hi = np.ceil(p.max(0)).astype(int) + 2
        lo = np.maximum(lo, 0); hi = np.minimum(hi, S)
        yy, xx = np.mgrid[lo[1]:hi[1], lo[0]:hi[0]]
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-9: continue
        l0 = ((p[1, 1] - p[2, 1]) * (xx + .5 - p[2, 0]) + (p[2, 0] - p[1, 0]) * (yy + .5 - p[2, 1])) / d
        l1 = ((p[2, 1] - p[0, 1]) * (xx + .5 - p[2, 0]) + (p[0, 0] - p[2, 0]) * (yy + .5 - p[2, 1])) / d
        l2 = 1 - l0 - l1
        m = (l0 > -0.1) & (l1 > -0.1) & (l2 > -0.1) & ~crb[yy, xx]
        v = np.clip(l0 * kk[0] + l1 * kk[1] + l2 * kk[2], 0, 1)
        g = np.clip((v - 0.45) / 0.55, 0, 1) ** 1.5
        a[yy[m], xx[m]] = dark * (1 - g[m, None]) + hot * g[m, None]
        tgt = mask_r if pid_ == 2002 else mask_l
        tgt[yy[m], xx[m]] = np.clip(g[m] * 1.1, 0, 1)
Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save('textures/skel_head_basecolor_final.png')
Image.fromarray((mask_r * 255).astype(np.uint8)).save('textures/skel_eye_mask_a.png')
Image.fromarray((np.maximum(mask_r, mask_l) * 255).astype(np.uint8)).save('textures/skel_eye_mask_r.png')
print('TONE eyes', int((mask_r > 0.3).sum()), 'texels')
