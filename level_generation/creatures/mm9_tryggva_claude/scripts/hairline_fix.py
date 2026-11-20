#!/usr/bin/env python3
"""Hairline of the face shell under the centre-parted hair (mm9_tryggva face pass, 2026-11-02; brief lesson "fringe and
hairline edge"). The hair shell's front edge lies at y 1.70-1.72 (glTF, metres) across the forehead, but it parts in the
middle and Meshy painted the face shell above that edge as skin, so a broad skin wedge showed up through the parting.
Face-shell texels on the front of the head (z > ZF) above Y0 take the colour of the nearest hair-shell texel in 3D (so
they carry the hair's strands), blended in over Y0..Y1 (smoothstep), then a 1 px soften inside the blend band.
Runs after fringe_fix.py on textures/try_tp_head_basecolor.png (kept as work/try_tp_head_basecolor_prehairline.png on the
first run and read from there). Writes review/hairline_fix_mask.png.
Usage (project folder): hairline_fix.py [y0 1.712] [y1 1.735] [zf 0.02]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pygltflib import GLTF2

Y0 = float(sys.argv[1]) if len(sys.argv) > 1 else 1.712
Y1 = float(sys.argv[2]) if len(sys.argv) > 2 else 1.735
ZF = float(sys.argv[3]) if len(sys.argv) > 3 else 0.02
SRC = Path('work/try_tp_head_basecolor_prehairline.png')
OUT = Path('textures/try_tp_head_basecolor.png')
if not SRC.exists():
    shutil.copyfile(OUT, SRC)
img = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
g = GLTF2().load('work/try_body_tex.glb')
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('TryggvaHead'))
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True)
weld = weld.ravel()
F = weld[I]
rows = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
cols = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
n = weld.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)), directed=False)
face_part = lab[F[:, 0]]
cy = P[I].mean(1)[:, 1]
parts, counts = np.unique(face_part[cy > 1.66], return_counts=True)
order = parts[np.argsort(-counts)]
hair_part = order[0]
# the face shell: the part with the most faces in front of the eyes (z far forward, eye height)
cz = P[I].mean(1)[:, 2]
fparts, fcounts = np.unique(face_part[(cy > 1.62) & (cy < 1.70) & (cz > 0.07)], return_counts=True)
face_shell = fparts[np.argmax(fcounts)]
print('HAIRLINE hair part', int(hair_part), 'face shell', int(face_shell))


def raster(faces):
    pos = np.full((N, N, 3), np.nan)
    for f in faces:
        tri = I[f]
        uv = UV[tri] * N
        x0, y0 = np.floor(uv.min(0)).astype(int)
        x1, y1 = np.ceil(uv.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, c = uv
        m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-12:
            continue
        l = np.linalg.solve(m, (q - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -0.02).all(1)
        pos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
    return pos


hpos = raster(np.where(face_part == hair_part)[0])
fpos = raster(np.where(face_part == face_shell)[0])
hcov = ~np.isnan(hpos[..., 0])
fcov = ~np.isnan(fpos[..., 0])
hy, hx = np.nonzero(hcov)
tree = cKDTree(hpos[hy, hx])
fy_, fz_ = np.nan_to_num(fpos[..., 1]), np.nan_to_num(fpos[..., 2])
region = fcov & (fz_ > ZF) & (fy_ > Y0 - 0.002)
ry, rx = np.nonzero(region)
_, j = tree.query(fpos[ry, rx])
t = np.clip((fy_[ry, rx] - Y0) / (Y1 - Y0), 0, 1)
t = t * t * (3 - 2 * t)
out = img.copy()
out[ry, rx] = img[ry, rx] * (1 - t[:, None]) + img[hy[j], hx[j]] * t[:, None]
band = np.zeros((N, N), bool)
band[ry, rx] = (t > 0) & (t < 1)
band = ndi.binary_dilation(band, iterations=1) & fcov
blur = ndi.gaussian_filter(out, (0.8, 0.8, 0))
out[band] = blur[band]
# gutters: dilate the repainted texels one step so bilinear reads stay on the new colour
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
vis = (img * 255).astype(np.uint8).copy()
vis[region & (fy_ > Y0)] = (255, 0, 255)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/hairline_fix_mask.png')
print('HAIRLINE repainted', int((t > 0).sum()), 'texels; full hair', int((t >= 1).sum()))
