#!/usr/bin/env python3
"""Codex face onto the head paint (Njam's route, simplified): the close front view references_head/05_face.png is projected straight along
the view axis (+y) onto the face skin and eyeball texels (parts 20, 22), placed by three landmarks measured on both sides: the iris
centres and the mouth centre (on our mesh: the eyeball centroids and the lip crease on the midline). The two scales differ (x 1.29 x
z): our face is narrower than the Codex face, so the projected features follow our geometry. Weight = frontness smoothstep(0.35, 0.8) x an ellipse round the face in the image x not Codex hair
(dark, desaturated) x not below the jaw line; the Codex colours get the Meshy face's mean in the blend band, so the cheek seam does not
show. Removes Meshy's dark midline marks under the lip and on the chin. Args: <in head colour 2K> <out png>"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
IN, OUT = sys.argv[1:3]
D = np.load('work/uv_dump.npz'); co, tri, uvc, mat, part = D['co'], D['tri'], D['uvc'], D['mat'], D['part']
S = 2048
sel = np.nonzero((mat == 1) & np.isin(part, (20, 22)))[0]
P3 = np.zeros((S, S, 3), np.float32); N3 = np.zeros((S, S, 3), np.float32); PART = np.zeros((S, S), np.uint8)
for f in sel:
    uv = uvc[f] * [S, S]; uv[:, 1] = S - uv[:, 1]
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = uv
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12: continue
    l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
    l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
    l3 = 1 - l1 - l2
    m = (l1 >= -0.02) & (l2 >= -0.02) & (l3 >= -0.02)
    if not m.any(): continue
    v = co[tri[f]]
    p = l1[m, None] * v[0] + l2[m, None] * v[1] + l3[m, None] * v[2]
    n = np.cross(v[1] - v[0], v[2] - v[0]); n /= max(np.linalg.norm(n), 1e-12)
    yy, xx = np.nonzero(m); yy += y0; xx += x0
    P3[yy, xx] = p; N3[yy, xx] = n; PART[yy, xx] = part[f]
src = np.asarray(Image.open(IN).convert('RGB'), np.float32) / 255
cov = PART > 0
# landmarks on the mesh, geometric (the mesh is mirror-symmetric; the paint's irises came out 1.3 cm apart in height): the eyeball
# centroids and the mouth line on the midline profile (the crease between the lips, measured: z 0.711)
D22 = co[np.unique(tri[part == 22])]
eyes = [D22[np.sign(D22[:, 0]) == s_].mean(0) for s_ in (-1, 1)]
mouth = np.array([0.0, -0.068, 0.711])
print('EYE3D', np.round(eyes, 4).tolist(), 'MOUTH3D', mouth.tolist())
# landmarks in the Codex image (pixels: col, row), measured on references_head/05_face.png
E_L, E_R, MO = np.array([457.0, 636.0]), np.array([813.0, 636.0]), np.array([635.0, 1015.0])
ax_ = (E_R[0] - E_L[0]) / (eyes[1][0] - eyes[0][0]); bx = E_L[0] - ax_ * eyes[0][0]
ez = 0.5 * (eyes[0][2] + eyes[1][2])
az = (MO[1] - E_L[1]) / (mouth[2] - ez); bz = E_L[1] - az * ez
print('MAP', round(ax_, 1), round(az, 1), 'x scale / z scale', round(abs(ax_ / az), 3))
img = np.asarray(Image.open('references_head/05_face.png').convert('RGBA'), np.float32) / 255
H, W = img.shape[:2]
u = ax_ * P3[..., 0] + bx; v = az * P3[..., 2] + bz
smp = np.stack([ndimage.map_coordinates(img[..., k], [v, u], order=1, mode='nearest') for k in range(4)], -1)
def sst(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
front = sst(-N3[..., 1], 0.35, 0.8)
cx, cy = 635.0, 800.0; rx, ry = 330.0, 470.0
ell = 1 - sst(np.hypot((u - cx) / rx, (v - cy) / ry), 0.85, 1.0)
mx = smp[..., :3].max(-1); mn = smp[..., :3].min(-1)
hair = sst(0.36 - mx, 0.0, 0.08) * sst(0.45 - (mx - mn) / np.maximum(mx, 1e-3), 0.0, 0.2)      # dark, not saturated skin shadow
hair = ndimage.grey_dilation(hair, size=5)
w = front * ell * (1 - hair) * smp[..., 3] * cov * (1 - sst(v, 1160, 1230))
w = ndimage.gaussian_filter(w, 1.0) * cov
band = cov & (w > 0.15) & (w < 0.6) & (PART == 20)
core = cov & (w > 0.6) & (PART == 20)
gain = src[band].mean(0) / np.maximum(smp[band, :3].mean(0), 1e-3)
print('GAIN', np.round(gain, 3).tolist(), 'band', int(band.sum()), 'core', int(core.sum()))
col = np.clip(smp[..., :3] * gain, 0, 1)
out = src * (1 - w[..., None]) + col * w[..., None]
Image.fromarray((out * 255 + 0.5).astype('u1')).save(OUT)
Image.fromarray((w * 255).astype('u1')).save('work/face_proj_weight.png')
print('PROJECTED', OUT, 'texels', int((w > 0.5).sum()))
