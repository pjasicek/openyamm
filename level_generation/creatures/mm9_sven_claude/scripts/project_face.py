#!/usr/bin/env python3
"""Project a repainted front face render back onto the head set (face fix, 2026-11-01; user: "looks like he has 2
eyebrows? and like weird eye area?"). render_face.py made the unlit front orthographic render of the head (camera
centre CX, CZ in Blender/GLB-up metres, ORTHO wide); Codex repainted only its eye area (references_face/). Every head
texel whose rest point is visible from the front (z-buffer over the head and body triangles, 2 mm) takes the repaint's
colour at its projected pixel, weighted by the eye-area window (|x| < 7.5 cm, height 1.612-1.692 m, 8 mm ramps) times a facing ramp (0.05-0.3: the brow ridge underside faces down but shows from the front) instead of
facing^2; the normal map is flattened by the same weight x 0.85 inside the window (the band's painted relief).
Writes textures/<prefix>_head_basecolor.png and _head_normal_1k.png (backups *_preface.png on the first run).
Usage (project folder): project_face.py <export glb> <prefix> <repaint png> [cx cz ortho]"""
import os, sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from pygltflib import GLTF2
glb, prefix, paint = sys.argv[1:4]
CX, CZ, ORTHO = (float(v) for v in (sys.argv[4:7] if len(sys.argv) > 6 else (0.0, 1.635, 0.2)))
g = GLTF2().load(glb); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)


prims = {g.materials[p.material].name: p for m in g.meshes[:1] for p in m.primitives}
img = Image.open(paint).convert('RGB'); R = img.size[0]
pimg = np.asarray(img, float)
# z-buffer of the front view over every LOD0 triangle (head and body)
Z = np.full((R, R), -1e9)
for p in prims.values():
    P = acc(p.attributes.POSITION); T = acc(p.indices).astype(int).reshape(-1, 3)
    px = ((P[:, 0] - CX) / ORTHO + 0.5) * R; py = (0.5 - (P[:, 1] - CZ) / ORTHO) * R
    for t in T:
        x, y, z = px[t], py[t], P[t, 2]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        c = 1 - a - b; m = (a >= 0) & (b >= 0) & (c >= 0)
        zz = a * z[0] + b * z[1] + c * z[2]
        sub = Z[y0:y1 + 1, x0:x1 + 1]
        upd = m & (zz > sub); sub[upd] = zz[upd]
# texel raster of the head primitive: position, normal
hp = prims[next(k for k in prims if k.endswith('Head'))]
P = acc(hp.attributes.POSITION); NRM = acc(hp.attributes.NORMAL); UV = acc(hp.attributes.TEXCOORD_0)
T = acc(hp.indices).astype(int).reshape(-1, 3)
f = Path(f'textures/{prefix}_head_basecolor.png'); fn = Path(f'textures/{prefix}_head_normal_1k.png')
for src in (f, fn):
    bk = src.with_name(src.stem + '_preface.png')
    if not bk.exists():
        shutil.copyfile(src, bk)
base = np.asarray(Image.open(f.with_name(f.stem + '_preface.png')).convert('RGB'), float)
N = base.shape[0]
pos = np.full((N, N, 3), np.nan); nor = np.zeros((N, N, 3))
for t in T:
    uv = UV[t] * N
    x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a_, b_, c_ = uv
    den = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b_[1] - c_[1]) * (gx - c_[0]) + (c_[0] - b_[0]) * (gy - c_[1])) / den
    l1 = ((c_[1] - a_[1]) * (gx - c_[0]) + (a_[0] - c_[0]) * (gy - c_[1])) / den
    L = np.stack([l0, l1, 1 - l0 - l1], -1); ins = (L >= -1e-3).all(-1)
    if ins.any():
        yy, xx = (gy[ins] - 0.5).astype(int), (gx[ins] - 0.5).astype(int)
        pos[yy, xx] = L[ins] @ P[t]; nor[yy, xx] = L[ins] @ NRM[t]
cov = ~np.isnan(pos[..., 0])
x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3))
nor /= np.maximum(np.linalg.norm(nor, axis=-1, keepdims=True), 1e-9)
facing = np.clip(nor[..., 2], 0, 1)
px = ((x - CX) / ORTHO + 0.5) * R; py = (0.5 - (y - CZ) / ORTHO) * R
ix = np.clip(px.astype(int), 0, R - 1); iy = np.clip(py.astype(int), 0, R - 1)
visible = cov & (z > Z[iy, ix] - 0.002) & (px >= 0) & (px < R) & (py >= 0) & (py < R)


def ramp(v, a, b):
    return np.clip((v - a) / (b - a), 0, 1)


win = ramp(y, 1.612, 1.620) * (1 - ramp(y, 1.690, 1.700)) * (1 - ramp(np.abs(x), 0.088, 0.105))   # to the temples: the old band reached past the brow ends
# mm9_sven: FACE_WINDOWS="y0,y1,xmax;..." replaces the window by the union of several (8 mm ramps in y, xmax..xmax+17 mm in x)
if os.environ.get('FACE_WINDOWS'):
    win = np.zeros_like(y)
    for spec in os.environ['FACE_WINDOWS'].split(';'):
        a_, b_, xm = (float(t) for t in spec.split(','))
        win = np.maximum(win, ramp(y, a_, a_ + 0.008) * (1 - ramp(y, b_ - 0.008, b_)) * (1 - ramp(np.abs(x), xm, xm + 0.017)))
w = win * ramp(facing, -0.05, 0.15) * visible     # full weight on every front-facing texel (facing^2 left a ghost of the old band)
w = ndimage.gaussian_filter(w, 1.0) * cov
# bilinear sample of the repaint
fx, fy = np.clip(px - 0.5, 0, R - 1.001), np.clip(py - 0.5, 0, R - 1.001)
x0, y0 = fx.astype(int), fy.astype(int); ax, ay = (fx - x0)[..., None], (fy - y0)[..., None]
samp = (pimg[y0, x0] * (1 - ax) * (1 - ay) + pimg[y0, x0 + 1] * ax * (1 - ay) + pimg[y0 + 1, x0] * (1 - ax) * ay
        + pimg[y0 + 1, x0 + 1] * ax * ay)
out = base * (1 - w[..., None]) + samp * w[..., None]
near = ndimage.binary_dilation(w > 0.02, iterations=8) & ~cov
_, (jy, jx) = ndimage.distance_transform_edt(~cov, return_indices=True)
out[near] = out[jy[near], jx[near]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(f)
nm = np.asarray(Image.open(fn.with_name(fn.stem + '_preface.png')).convert('RGB'), float)
w1 = np.asarray(Image.fromarray(np.uint8(np.clip(w, 0, 1) * 255)).resize(nm.shape[1::-1], Image.BILINEAR), float)[..., None] / 255 * 0.85
nm = nm * (1 - w1) + np.array([128, 128, 255.0]) * w1
Image.fromarray(np.uint8(np.clip(nm, 0, 255))).save(fn)
print('PROJECT_FACE', prefix, 'texels', int((w > 0.5).sum()), 'visible', int(visible.sum()))
