#!/usr/bin/env python3
"""Closed-mouth strip fix (wave-2 face lesson: no second lip layer, no dark slot). PeasantM2's closed mouth (face_fix.py) leaves a strip
of faces between the upper and the lower lip, 1-2 mm tall from the front, plus the hidden pocket behind it. The head paints put a grey-brown
band with a pale centre line there: from the party it read as a second lip / an open dark slot.
Every face-shell texel in the mouth box (|x| < 3 cm, z 0.712-0.738 m) that the front z-buffer sees and that is darker than 0.86 of the
lips or greyer than them (saturation < 0.8 of the lips') is the strip. Per 1 mm column of x: the strip's z range; its texels take the
colour between the lower lip (median of the visible lip texels within 2.5 mm below the strip) and the upper lip (above) by height, with a
thin soft contact line at the strip's middle (x0.72 at the centre, Gaussian sigma 0.45 mm). Hidden pocket texels in the box (behind the
lips, not seen from the front) take the lower lip x0.85. Args: <in head png> <out head png>  (project folder)"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage
sys.argv += [] 
src, dst = sys.argv[1:3]
sys.path.insert(0, 'scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('ff', 'scripts/face_front.py')
R = 1254; CX, CZ, ORTHO = 0.0, 0.775, 0.30
Z = np.load('work/faces.npz'); CO, MAT, PART = Z['co'], Z['mat'], Z['part']
TP = np.load('work/texpos_head.npz'); pos, ok, fid = TP['pos'], TP['ok'], TP['face']
im = np.asarray(Image.open(src).convert('RGB'), float); N = im.shape[0]
head = np.where(MAT == 2)[0]
Zb = np.full((R, R), -1e9)
for f in head:
    c = CO[f]; x = ((c[:, 0] - CX) / ORTHO + 0.5) * R; y = (0.5 - (c[:, 2] - CZ) / ORTHO) * R; z = -c[:, 1]
    x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
    if x1 < x0 or y1 < y0: continue
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d; b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    cc = 1 - a - b; m = (a >= 0) & (b >= 0) & (cc >= 0); zz = a * z[0] + b * z[1] + cc * z[2]
    sub = Zb[y0:y1 + 1, x0:x1 + 1]; upd = m & (zz > sub); sub[upd] = zz[upd]
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
shell = ok & (PART[np.maximum(fid, 0)] == 20)
px = np.clip((((x - CX) / ORTHO + 0.5) * R).astype(int), 0, R - 1); py = np.clip(((0.5 - (z - CZ) / ORTHO) * R).astype(int), 0, R - 1)
vis = shell & (-y > Zb[py, px] - 0.0015)
box = shell & (np.abs(x) < 0.030) & (z > 0.700) & (z < 0.750) & (y < -0.04)
lum = im.mean(2); sat = (im.max(2) - im.min(2)) / np.maximum(im.max(2), 1)
XC = 0.0245    # the lips' corners (after mouth_close.py the groove ends there; wider fills drew lip bands onto the cheeks)
inner = box & (z > 0.712) & (z < 0.738) & (np.abs(x) < XC)
lips = vis & box & ~inner
lipl, lips_s = np.median(lum[lips & (np.abs(x) < 0.015)]), np.median(sat[lips & (np.abs(x) < 0.015)])
strip = vis & inner & ((lum < 0.86 * lipl) | (sat < 0.8 * lips_s))
strip = ndimage.binary_closing(strip, iterations=2) & vis & inner
out = im.copy(); n = 0
cols = []
for xb in np.arange(-0.030, 0.030, 0.001):
    s = strip & (x >= xb) & (x < xb + 0.001)
    if s.sum() < 3: continue
    cols.append((xb + 0.0005, np.percentile(z[s], 3), np.percentile(z[s], 97)))
cols = np.array(cols)
# smooth strip bounds over x (quadratic fits): a per-column fit made the contact line jagged
plo = np.polyfit(cols[:, 0], cols[:, 1], 2); phi = np.polyfit(cols[:, 0], cols[:, 2], 2)
zlo_x, zhi_x = np.polyval(plo, x), np.polyval(phi, x)
xmin, xmax = cols[:, 0].min() - 0.001, cols[:, 0].max() + 0.001
band = inner & (x > xmin) & (x < xmax) & (z > zlo_x - 0.0006) & (z < zhi_x + 0.0006) & shell
band = band & ndimage.binary_dilation(vis, iterations=2)
# the pocket's deep faces that the front sees through the small gap at the lips' centre (a dark speck) join the strip
deep = shell & inner & (y > -0.07) & (np.abs(x) < 0.013)
band |= deep
# lip colours above and below, smoothed along x (+-3 mm windows)
def lipcol(sel, xc):
    m = sel & (np.abs(x - xc) < 0.003)
    return np.median(im[m], 0) if m.sum() > 5 else None
xs = np.arange(xmin, xmax + 0.001, 0.001); CL = []; CH = []
for xc in xs:
    lo = vis & box & ~band & (z < zlo_x - 0.0006) & (z > zlo_x - 0.0035)
    hi = vis & box & ~band & (z > zhi_x + 0.0006) & (z < zhi_x + 0.0035)
    CL.append(lipcol(lo, xc)); CH.append(lipcol(hi, xc))
fill = lambda L: np.array([v if v is not None else np.nanmedian(np.array([u for u in L if u is not None]), 0) for v in L])
CL, CH = fill(CL), fill(CH)
bi = np.clip(((x[band] - xmin) / 0.001).astype(int), 0, len(xs) - 1)
cl, ch = CL[bi], CH[bi]
zl, zh = zlo_x[band], zhi_x[band]; zc = 0.5 * (zl + zh)
t = np.clip((z[band] - zl) / np.maximum(zh - zl, 1e-4), 0, 1)[:, None]
c = cl * (1 - t) + ch * t
# the contact line: soft, fading toward the corners
fade = np.clip((xmax - np.abs(x[band])) / 0.006, 0, 1) if False else np.clip(1 - (np.abs(x[band]) / max(abs(xmin), xmax)) ** 4, 0, 1)
c *= (1 - 0.22 * fade * np.exp(-((z[band] - zc) / 0.0006) ** 2))[:, None]
out[band] = c; n = int(band.sum())
# gutter and seam texels next to the strip (not covered by texel_pos's raster) take the nearest strip texel's colour: the renderer
# samples them at triangle edges (dark specks otherwise)
near = ndimage.binary_dilation(band, iterations=4) & ~band & ~(ok & ~inner)
_, (iy, ix) = ndimage.distance_transform_edt(~band, return_indices=True)
out[near] = out[iy[near], ix[near]]
pocket = box & inner & ~vis & (y > -0.085)
lower = np.median(im[lips & (z < 0.712)], 0)
out[pocket] = lower * 0.85    # hidden; light enough that edge sampling from the strip shows no dark specks
# dark specks left inside the lips' box (a few texels of Meshy's old slit dot): a texel darker than 0.78 or lighter than 1.18 of its
# 7 px median takes it
zone = ndimage.binary_dilation(box & (z > 0.708) & (z < 0.742), iterations=3)
med = np.stack([ndimage.median_filter(out[..., k], size=7) for k in range(3)], -1)
sp = zone & ((out.mean(2) < 0.78 * med.mean(2)) | (out.mean(2) > 1.18 * med.mean(2)))
out[sp] = med[sp]
print('MOUTH specks', int(sp.sum()))
# gutters of the many tiny islands round the lips (the renderer samples them at island edges): nearest island texel's colour
okz = ok & zone
g = ndimage.binary_dilation(okz, iterations=3) & ~ok
_, (gy_, gx_) = ndimage.distance_transform_edt(~okz, return_indices=True)
out[g] = out[gy_[g], gx_[g]]
print('MOUTH gutter texels', int(g.sum()))
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
print('MOUTH strip texels', n, 'pocket', int(pocket.sum()), 'lip lum', round(float(lipl), 1), 'sat', round(float(lips_s), 3))
