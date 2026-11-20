#!/usr/bin/env python3
"""Texture sets from the Meshy returns on our UVs (TEXTURE_QUALITY_PASS.md): body per tier (colour 4K -> 2K Lanczos once, normal and roughness 1K, padded into the gutters), head sets
from the one job with two heads. The job's side views came back swapped against its front and back views, so each head holds its tier from the front and back and the OTHER tier from the
sides (the Meshy views are not what the two-head composite assumed). Salvage: both copies share one layout, so per texel the true tier is taken from copy 0 or 1 by the surface normal.
Lining dark patch and metal 0, as compose_texpass.py. Run in the project folder. Writes textures/guard_{a,c}_*, guard_head{a,c}_*."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from pygltflib import GLTF2
from scipy import ndimage
T = Path('textures'); J = json.load(open('work/dark_texel.json'))


def glb(path):
    g = GLTF2().load(path); b = g.binary_blob(); pr = g.meshes[0].primitives[0]
    def acc(i, n, dt):
        a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; off = (bv.byteOffset or 0) + (a.byteOffset or 0)
        return np.frombuffer(b, dt, a.count * n, off).reshape(a.count, n)
    ia = g.accessors[pr.indices]
    return acc(pr.attributes.POSITION, 3, np.float32), acc(pr.attributes.NORMAL, 3, np.float32), acc(pr.attributes.TEXCOORD_0, 2, np.float32), acc(pr.indices, 1, {5123: np.uint16, 5125: np.uint32}[ia.componentType]).reshape(-1, 3)


def coverage(uv, idx, size):
    im = Image.new('L', (size, size)); d = ImageDraw.Draw(im)
    for t in idx: d.polygon([(float(uv[i, 0] * size), float(uv[i, 1] * size)) for i in t], fill=255)
    return np.asarray(im) > 0


def pad(img, cov):
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    return img[iy, ix]


def load(job, name, mode):
    return Image.open(f'meshy/{job}/texture_urls_0_{name}.png').convert(mode)


def write(out, col, nrm, rough, cov2, cov1, ao, key):
    """col 2048 RGB array, nrm 1024 RGB, rough 1024 L 0..1"""
    d = J[key]
    col = pad(col, cov2).copy(); nrm = pad(nrm, cov1).copy(); rough = pad(rough, cov1).copy(); ao1 = pad(ao, cov1).copy()
    for arr, s in ((col, 2048), (nrm, 1024), (rough, 1024), (ao1, 1024)):
        x, y, r = int(d['u'] * s), int(d['v'] * s), int(s / 1024 * 8)
        yy, xx = np.ogrid[:s, :s]
        m = (xx - x) ** 2 + (yy - y) ** 2 < r * r
        if arr.ndim == 3 and arr is col: arr[m] = (22, 18, 16)
        elif arr.ndim == 3: arr[m] = (128, 128, 255)
        elif arr is rough: arr[m] = 0.9
    Image.fromarray(col).save(T / f'{out}_basecolor.png')
    Image.fromarray(nrm).save(T / f'{out}_normal_1k.png')
    Image.merge('RGB', [Image.fromarray(ao1), Image.fromarray((np.maximum(rough, 0.5) * 255).astype(np.uint8)), Image.new('L', (1024, 1024), 0)]).save(T / f'{out}_metal_rough_1k.png')


P, N, UV, IDX = glb('texturing/guard_body_upload.glb')
c2, c1 = coverage(UV, IDX, 2048), coverage(UV, IDX, 1024)
ao = np.asarray(Image.open(T / 'guard_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
for t, job in (('a', 'retexture_body_a'), ('c', 'retexture_body_c')):
    col = np.asarray(load(job, 'base_color', 'RGB').resize((2048, 2048), Image.LANCZOS))
    nrm = np.asarray(load(job, 'normal', 'RGB').resize((1024, 1024), Image.LANCZOS))
    rough = np.asarray(load(job, 'roughness', 'L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    write(f'guard_{t}', col, nrm, rough, c2, c1, ao, 'body')
    print('BODY', t)
# heads
P, N, UV, IDX = glb('texturing/guard_heads_upload.glb')
keep = (UV[IDX, 0] < 0.5).all(1)
uvh = np.c_[UV[:, 0] * 2, (UV[:, 1] - 0.25) * 2]
idx = IDX[keep]
S = 2048
ns = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
for t in idx:
    q = uvh[t] * S
    x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, S - 1), min(y1, S - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = q
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-9: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1
    m = (l0 >= -0.01) & (l1 >= -0.01) & (l2 >= -0.01)
    ny, nx = ys[m].astype(int), xs[m].astype(int)
    ns[ny, nx] = l0[m, None] * N[t[0]] + l1[m, None] * N[t[1]] + l2[m, None] * N[t[2]]; cov[ny, nx] = True
ns = pad(ns, cov)
for k in range(3): ns[..., k] = ndimage.gaussian_filter(ns[..., k], 6)
ns /= np.maximum(np.linalg.norm(ns, axis=2, keepdims=True), 1e-6)
ratio = np.abs(ns[..., 0]) / np.maximum(np.abs(ns[..., 0]) + np.abs(ns[..., 2]), 1e-6)
t_ = np.clip((ratio - 0.40) / 0.2, 0, 1); side = t_ * t_ * (3 - 2 * t_)
Image.fromarray((side * 255).astype(np.uint8)).save('work/head_side_mask.png')
bc = np.asarray(load('retexture_heads', 'base_color', 'RGB'), np.float32); nr = np.asarray(load('retexture_heads', 'normal', 'RGB'), np.float32); rg = np.asarray(load('retexture_heads', 'roughness', 'L'), np.float32) / 255
crop = lambda a, c: a[1024:3072, 2048 * c:2048 * (c + 1)]
cov1 = np.asarray(Image.fromarray(cov).resize((1024, 1024), Image.BILINEAR)) > 0
ao_h = np.asarray(Image.open(T / 'guard_head_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS))
s1 = np.asarray(Image.fromarray((side * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR), np.float32) / 255
for t, own in (('a', 0), ('c', 1)):
    oth = 1 - own
    A, B = crop(bc, own), crop(bc, oth)
    col = (A * (1 - side[..., None]) + B * side[..., None]).astype(np.uint8)
    nA = np.asarray(Image.fromarray(crop(nr, own).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32); nB = np.asarray(Image.fromarray(crop(nr, oth).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32)
    nrm = (nA * (1 - s1[..., None]) + nB * s1[..., None]).astype(np.uint8)
    rA = np.asarray(Image.fromarray((crop(rg, own) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32) / 255; rB = np.asarray(Image.fromarray((crop(rg, oth) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    write(f'guard_head{t}', col, nrm, rA * (1 - s1) + rB * s1, cov, cov1, ao_h, 'head')
    print('HEAD', t)
