#!/usr/bin/env python3
"""Tier C face (0 credits): flat unlit FRONT orthographic render of the head set and its projection back (after PeasantF1's
view_uvtex.py / project_face_pf1.py, simplified for PeasantM2's head). Project folder.
  render  <head colour png> <out png>            1254 px, centre x 0, z CZ, ORTHO m wide; head faces (mat 2) z-buffered
  project <repaint png> <in head png> <out head png> [--report json]
Projection: every face-shell texel (part 20) visible from the front (z-buffer over all head faces, 2 mm) inside the face window
(|x| < XW, ZLO < z < ZHI; 6 mm ramps) with its normal facing the camera (ramp 0.05..0.25 of -ny) takes the repaint's colour at its
projected pixel (bilinear). Edge texels the raster missed grow 2 px over covered texels; the weight is normalised over the island
coverage (no half-weighted seams). Then the repaint's skin is matched to the base's skin outside the window by per-channel gains
measured on a ring 6-12 mm outside the window (so the neck, ears and hair line keep their colour)."""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
R = 1254; CX, CZ, ORTHO = 0.0, 0.775, 0.30
XW, ZLO, ZHI = 0.068, 0.655, 0.852
Z = np.load('work/faces.npz'); CO, UV, MAT, PART = Z['co'], Z['uv'], Z['mat'], Z['part']
head = np.where(MAT == 2)[0]
def zbuffer(colour=None):
    Zb = np.full((R, R), -1e9); img = np.full((R, R, 3), 102.0)
    if colour is not None: tex = np.asarray(Image.open(colour).convert('RGB'), float); N = tex.shape[0]
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
        if colour is not None and upd.any():
            u = a * UV[f, 0, 0] + b * UV[f, 1, 0] + cc * UV[f, 2, 0]; v = a * UV[f, 0, 1] + b * UV[f, 1, 1] + cc * UV[f, 2, 1]
            px = np.clip((u * N).astype(int), 0, N - 1); py = np.clip(((1 - v) * N).astype(int), 0, N - 1)
            img[y0:y1 + 1, x0:x1 + 1][upd] = tex[py[upd], px[upd]]
    return Zb, img
if sys.argv[1] == 'render':
    _, img = zbuffer(sys.argv[2]); Image.fromarray(img.astype(np.uint8)).save(sys.argv[3]); print('FRONT', sys.argv[3]); sys.exit()
paint, src, dst = sys.argv[2:5]
rep = np.asarray(Image.open(paint).convert('RGB').resize((R, R), Image.LANCZOS), float)
base = np.asarray(Image.open(src).convert('RGB'), float); N = base.shape[0]
TP = np.load('work/texpos_head.npz'); pos, ok, fid = TP['pos'], TP['ok'], TP['face']
assert pos.shape[0] == N, (pos.shape, N)
Zb, _ = zbuffer()
# vertex normals of the head faces per texel: face normal (flat) is enough for the facing ramp
fn = np.cross(CO[:, 1] - CO[:, 0], CO[:, 2] - CO[:, 0]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
f_ = np.maximum(fid, 0); shell = ok & (PART[f_] == 20)
x, y, z = pos[..., 0], pos[..., 1], pos[..., 2]
px = ((x - CX) / ORTHO + 0.5) * R; py = (0.5 - (z - CZ) / ORTHO) * R
ix, iy = np.clip(px.astype(int), 0, R - 1), np.clip(py.astype(int), 0, R - 1)
vis = shell & (-y > Zb[iy, ix] - 0.002)
ramp = lambda v, a, b: np.clip((v - a) / (b - a), 0, 1)
win = ramp(z, ZLO, ZLO + 0.006) * (1 - ramp(z, ZHI - 0.006, ZHI)) * (1 - ramp(np.abs(x), XW - 0.006, XW))
facing = ramp(-fn[f_][..., 1], 0.05, 0.25)
w = win * facing * vis
w = np.maximum(w, ndimage.grey_dilation(w, size=5) * win * shell)
w = ndimage.gaussian_filter(w * ok, 1.0) / np.maximum(ndimage.gaussian_filter(ok.astype(float), 1.0), 1e-6) * shell
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001); x0, y0 = fx.astype(int), fy.astype(int)
ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = rep[y0, x0] * (1 - ax) * (1 - ay) + rep[y0, x0 + 1] * ax * (1 - ay) + rep[y0 + 1, x0] * (1 - ax) * ay + rep[y0 + 1, x0 + 1] * ax * ay
# skin gain: ring just outside the window, visible face-shell texels; repaint sampled there vs the base there
ring = shell & vis & (facing > 0.5) & (win < 0.01) & (np.abs(x) < XW + 0.012) & (z > ZLO - 0.012) & (z < ZHI + 0.012)
lum = base.mean(2); skin = ring & (lum > 60)
gain = np.clip(np.median(base[skin], 0) / np.maximum(np.median(samp[skin], 0), 1), 0.8, 1.25) if skin.sum() > 50 else np.ones(3)
out = base * (1 - w[..., None]) + np.clip(samp * gain, 0, 255) * w[..., None]
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(dst)
r = {'texels_full': int((w > 0.99).sum()), 'texels_any': int((w > 0.01).sum()), 'ring': int(skin.sum()), 'gain': np.round(gain, 3).tolist()}
if '--report' in sys.argv: json.dump(r, open(sys.argv[sys.argv.index('--report') + 1], 'w'))
print('PROJECT', r)
