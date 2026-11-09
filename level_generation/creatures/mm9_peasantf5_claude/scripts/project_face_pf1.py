#!/usr/bin/env python3
"""Project a repainted flat front face render back onto the head set (face fix 2026-11-02, after mm9_peasantm1_claude/scripts/project_face.py;
orchestrator review: swollen pout, chin smudge, staring eyes, tier A not elderly). view_uvtex.py rendered the unlit front orthographic
view of work/uv_tex2.npz (Blender frame, camera from -y, centre x CX, z CZ, ORTHO wide, R px); Codex repainted the face (references_face/).
Every head texel whose rest point is visible from the front (z-buffer over all triangles, 2 mm) takes the repaint's colour at its
projected pixel, weighted by the face window (|x| < 7 cm, 1.495-1.690 m over the soles, 6 mm ramps) times a facing ramp.
Also, for the shared head set: the normal map flattened by the same window x 0.85 (Meshy's relief of the old lips and eyes) and fully
inside the ear zone beside the cheeks (a corrupt normal there drew a grey speck at the hood edge).
Args: <tier> <repaint png> <in base png> <out base png> [--normal <in normal> <out normal>]   (project folder)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
t, paint, src, dst = sys.argv[1:5]
CX, CZ, ORTHO = 0.0, 0.6703, 0.26; Z0 = -0.9297
D = np.load('work/uv_tex2.npz'); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
img = np.asarray(Image.open(paint).convert('RGB'), float); R = img.shape[0]
assert img.shape[0] == img.shape[1] == 1254, img.shape
# front z-buffer: depth = -y (the camera looks along +y)
Zb = np.full((R, R), -1e9)
px_v = ((co[:, 0] - CX) / ORTHO + 0.5) * R; py_v = (0.5 - (co[:, 2] - CZ) / ORTHO) * R; dz_v = -co[:, 1]
for f in tri:
    x, y, z = px_v[f], py_v[f], dz_v[f]
    x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-12: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d; b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    c = 1 - a - b; m = (a >= 0) & (b >= 0) & (c >= 0); zz = a * z[0] + b * z[1] + c * z[2]
    sub = Zb[y0:y1 + 1, x0:x1 + 1]; upd = m & (zz > sub); sub[upd] = zz[upd]
# head texels: position and normal
fn_ = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]])
key = np.round(co, 5); _, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
Nv = np.zeros((inv.max() + 1, 3)); [np.add.at(Nv, inv[tri[:, k]], fn_) for k in range(3)]; Nv = Nv[inv]; Nv /= np.maximum(np.linalg.norm(Nv, axis=1, keepdims=True), 1e-12)
base = np.asarray(Image.open(src).convert('RGB'), float); N = base.shape[0]
pos = np.full((N, N, 3), np.nan); nor = np.zeros((N, N, 3))
for f in np.where(mat == 1)[0]:
    q = uv[tri[f]] * [N, -N] + [0, N]
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(q.max(0)).astype(int), N - 1)
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    T_ = np.array([[q[0, 0] - q[2, 0], q[1, 0] - q[2, 0]], [q[0, 1] - q[2, 1], q[1, 1] - q[2, 1]]])
    if abs(np.linalg.det(T_)) < 1e-12: continue
    l = np.linalg.solve(T_, (np.c_[gx.ravel(), gy.ravel()] - q[2]).T).T; L3 = np.c_[l, 1 - l.sum(1)]; ins = (L3 >= -1e-3).all(1)
    if ins.any():
        yy, xx = (gy.ravel()[ins] - 0.5).astype(int), (gx.ravel()[ins] - 0.5).astype(int)
        pos[yy, xx] = L3[ins] @ co[tri[f]]; nor[yy, xx] = L3[ins] @ Nv[tri[f]]
cov = ~np.isnan(pos[..., 0]); x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3)); zs = z - Z0
nor /= np.maximum(np.linalg.norm(nor, axis=-1, keepdims=True), 1e-9); facing = np.clip(-nor[..., 1], 0, 1)
px = ((x - CX) / ORTHO + 0.5) * R; py = (0.5 - (z - CZ) / ORTHO) * R
ix = np.clip(px.astype(int), 0, R - 1); iy = np.clip(py.astype(int), 0, R - 1)
visible = cov & (-y > Zb[iy, ix] - 0.002) & (px >= 0) & (px < R) & (py >= 0) & (py < R)
def ramp(v, a, b): return np.clip((v - a) / (b - a), 0, 1)
win = ramp(zs, 1.495, 1.501) * (1 - ramp(zs, 1.684, 1.690)) * (1 - ramp(np.abs(x), 0.064, 0.070))
# the nose keeps the earlier paint: the repaint's nostrils and highlights fall on the front of our nose tip (a dark pig-nose patch)
nose = ramp(zs, 1.574, 1.580) * (1 - ramp(zs, 1.636, 1.644)) * (1 - ramp(np.abs(x), 0.020, 0.026)) * (1 - ramp(y, -0.112, -0.106))
w = win * ramp(facing, 0.05, 0.25) * visible * (1 - nose)
w = ndimage.gaussian_filter(w, 1.0) * cov
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = img[y0, x0] * (1 - ax) * (1 - ay) + img[y0, x0 + 1] * ax * (1 - ay) + img[y0 + 1, x0] * (1 - ax) * ay + img[y0 + 1, x0 + 1] * ax * ay
out = base * (1 - w[..., None]) + samp * w[..., None]
near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
_, (jy, jx) = ndimage.distance_transform_edt(~cov, return_indices=True); out[near] = out[jy[near], jx[near]]
Image.fromarray(np.uint8(np.clip(out + 0.5, 0, 255))).save(dst)
print('PROJECT_FACE', t, 'texels', int((w > 0.5).sum()), 'visible', int(visible.sum()))
if '--normal' in sys.argv:
    i = sys.argv.index('--normal'); nsrc, ndst = sys.argv[i + 1:i + 3]
    nm = np.asarray(Image.open(nsrc).convert('RGB'), float); M = nm.shape[0]
    ear = cov & (np.abs(x) > 0.052) & (zs > 1.53) & (zs < 1.625) & (y > -0.075) & (y < 0.02)
    wn = np.clip(w * 0.85 + ndimage.gaussian_filter(ear.astype(float), 1.5), 0, 1)
    w1 = np.asarray(Image.fromarray(np.uint8(wn * 255)).resize((M, M), Image.BILINEAR), float)[..., None] / 255
    nm = nm * (1 - w1) + np.array([128, 128, 255.0]) * w1
    Image.fromarray(np.uint8(np.clip(nm, 0, 255))).save(ndst); print('NORMAL flattened', ndst)
