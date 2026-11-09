#!/usr/bin/env python3
"""Finish on the graded 2K paints, in place of a repaint:
- the 1.2-7 px band cut (Meshy's pebbled hide and knitted leather), hair left alone; normals softened;
- the front of the belt projected from the front master (neat bands, skull disc, woven plate): Meshy scattered white blobs over it, and the plate and studs came out as lumps;
- claws: pale at the root, black at the point as in MM9 (Meshy painted skin over our longer fingers).
Writes textures/ghoul_basecolor_final.png, ghoul_head_basecolor_final.png, ghoul_normal_soft.png, ghoul_head_normal_soft.png, ghoul_claw_mask.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
import project_lib as PL
TX = Path('textures'); Image.MAX_IMAGE_PIXELS = None
F = np.load('work/faces.npz'); J = np.load('work/pose_v1.blend.joints.npz')
S = 2048


def sstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def band_cut(img, mask, k=0.5):
    g1 = np.stack([ndimage.gaussian_filter(img[..., c], 1.2) for c in range(3)], -1)
    g7 = np.stack([ndimage.gaussian_filter(img[..., c], 7) for c in range(3)], -1)
    return np.clip(img - (k * mask)[..., None] * (g1 - g7), 0, 1)


def soft_normal(path, out, kmap):
    n = np.asarray(Image.open(path).convert('RGB'), np.float32) / 127.5 - 1
    k = np.asarray(Image.fromarray((kmap * 255).astype('u1')).resize((n.shape[1], n.shape[0]), Image.BILINEAR), np.float32)[..., None] / 255
    fl = np.array([0, 0, 1.0])
    r = n * k + fl * (1 - k)
    r /= np.maximum(np.linalg.norm(r, axis=2, keepdims=True), 1e-6)
    Image.fromarray(((r + 1) * 127.5).astype('u1')).save(out)


# ---- body
sel = (F['head'] == 0) & (F['part'] != 3)        # the belt lumps are gone from the mesh and keep their old UVs
pos, nor, cov, bar, fid = PL.raster(F['uvb'][sel], F['co'][sel], S)
parts = F['part'][sel]
base = np.asarray(Image.open(TX / 'ghoul_basecolor_graded.png').convert('RGB'), np.float32) / 255
_lz = (pos[..., 2] > -0.17) & (pos[..., 2] < 0.32) & (np.abs(pos[..., 0]) < 0.32)
out = band_cut(base, cov * np.where(_lz, 0.75, 0.97).astype(np.float32), 1.0)
# leather: Meshy's knit, a second, wider cut on the flaps and shorts
lea = (np.isin(parts[fid], (6, 7)) | ((pos[..., 2] > -0.16) & (pos[..., 2] < 0.12) & (np.abs(pos[..., 0]) < 0.3))) & cov
lea = ndimage.gaussian_filter(lea.astype(np.float32), 2.0)
g05 = np.stack([ndimage.gaussian_filter(out[..., c], 1.0) for c in range(3)], -1); g12 = np.stack([ndimage.gaussian_filter(out[..., c], 12) for c in range(3)], -1)
out = np.clip(out - (0.55 * lea)[..., None] * (g05 - g12) * (out.max(2, keepdims=True) < 0.42), 0, 1)
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
# belt front
M = np.asarray(Image.open('references_hd/01_front_clean.png').convert('RGB'), np.float32) / 255
TOPZ, BOTZ, TOPY, BOTY = 0.318, 0.122, 497.0, 601.0
sx = 680.0                           # master px per metre across the belt
px = 512 + x * sx
zw = z + 0.014 * (x / 0.15) ** 2     # our bands curve up at the centre
py = TOPY + (TOPZ - zw) * (BOTY - TOPY) / (TOPZ - BOTZ)
samp = np.stack([ndimage.map_coordinates(M[..., c], [py, px], order=3, mode='nearest') for c in range(3)], -1)
w = (1 - sstep(np.abs(x), 0.125, 0.17)) * sstep(zw, BOTZ - 0.006, BOTZ + 0.002) * (1 - sstep(zw, TOPZ - 0.002, TOPZ + 0.006)) * (y < 0) * cov
w = ndimage.gaussian_filter(w.astype(np.float32), 0.8)
out = out * (1 - w[..., None]) + samp * w[..., None]
# side blobs of the belt: near-white texels go back to the band's leather
belt = cov & (z > 0.12) & (z < 0.31) & (w < 0.5) & (y < 0.03)
hsvv = out.max(2); hsvs = (out.max(2) - out.min(2)) / np.maximum(out.max(2), 1e-4)
blob = belt & (hsvv > 0.62) & (hsvs < 0.38)
blob = ndimage.binary_dilation(blob, iterations=2) & cov & (z > 0.12) & (z < 0.31)
# the painted disc stood above the belt's top edge at the centre: hide there
disc = cov & (zw > TOPZ + 0.002) & (zw < 0.37) & (np.abs(x) < 0.12) & (y < 0)
bdisc = ndimage.binary_dilation(disc, iterations=3)
_, (dy, dx) = ndimage.distance_transform_edt(bdisc | ~cov, return_indices=True)
print('belt blobs', int(blob.sum()))
_, (iy, ix) = ndimage.distance_transform_edt(blob | ~cov, return_indices=True)
fill = out[iy, ix]
fill = np.stack([ndimage.gaussian_filter(fill[..., c], 2.0) for c in range(3)], -1)
sb = ndimage.gaussian_filter(blob.astype(np.float32), 1.0)[..., None]
out = out * (1 - sb) + fill * sb
# disc above the belt: a straight down-the-chest fill from the skin just above it
near = cov & (zw > 0.34) & (zw < 0.385) & (np.abs(x) < 0.15) & (np.abs(x) > 0.04) & (y < 0)
from scipy.spatial import cKDTree
np_ = np.argwhere(near); tree = cKDTree(np.c_[x[near], y[near]]); hit = np.argwhere(disc)
_, ii = tree.query(np.c_[x[disc], y[disc]])
df = out.copy(); df[disc] = out[np_[ii, 0], np_[ii, 1]]
df = np.stack([ndimage.gaussian_filter(df[..., c], 1.5) for c in range(3)], -1)
sd = ndimage.gaussian_filter(disc.astype(np.float32), 1.5)[..., None]
out = out * (1 - sd) + df * sd
# claws
claw = np.zeros((S, S), np.float32)
for sgn, s in ((1, 'L'), (-1, 'R')):
    hd = (sgn * x > 0.7) & cov
    for lastj, prevj in (('Finger02', 'Finger01'), ('Finger12', 'Finger11'), ('Finger22', 'Finger21'), ('Finger32', 'Finger31'), ('Finger42', 'Finger41')):
        j = J[f'{s} {lastj}']; k = J[f'{s} {prevj}']; u = (j - k) / np.linalg.norm(j - k)
        p = pos[hd] - j
        a = p @ u; d = np.linalg.norm(p - a[:, None] * u, axis=1)
        m = (d < 0.028) & (a > -0.05)
        if m.sum() < 5: continue
        amax = a[m].max()
        t = sstep(a, amax - 0.095, amax - 0.03) * m
        c = np.zeros_like(claw); c[hd] = t
        claw = np.maximum(claw, c)
claw = ndimage.gaussian_filter(claw, 0.8)
ink = np.array([0.045, 0.037, 0.034])
out = out * (1 - claw[..., None]) + ink * claw[..., None]
Image.fromarray((claw * 255).astype('u1')).save(TX / 'ghoul_claw_mask.png')
out = np.where(cov[..., None], out, out)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out = out[iy, ix]
Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).save(TX / 'ghoul_basecolor_final.png')
soft_normal(TX / 'ghoul_normal_1k.png', TX / 'ghoul_normal_soft.png', np.clip(0.3 - 0.3 * w, 0, 1) * np.ones((S, S)))
# ---- head: the skin only
sel = F['head'] != 0
pos, nor, cov, bar, fid = PL.raster(F['uvh'][sel], F['co'][sel], S)
parts = F['part'][sel]
base = np.asarray(Image.open(TX / 'ghoul_head_basecolor_graded.png').convert('RGB'), np.float32) / 255
hair = (cov & np.isin(parts[fid], (11,)))
m = cov & ~hair & ~np.isin(parts[fid], (12, 13))
m = ndimage.gaussian_filter(m.astype(np.float32), 1.0)
out = band_cut(base, m, 0.55)
_, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
out = out[iy, ix]
Image.fromarray((np.clip(out, 0, 1) * 255).astype('u1')).save(TX / 'ghoul_head_basecolor_final.png')
soft_normal(TX / 'ghoul_head_normal_1k.png', TX / 'ghoul_head_normal_soft.png', np.clip(1 - 0.55 * m, 0, 1))
print('FINISH')
