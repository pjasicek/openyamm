#!/usr/bin/env python3
"""Carry the 4K Meshy paint of the v1 layout (meshy/foot_retexture_v1) onto the v2 layout (work/uv_v2.npz: the same
surface triangles, new UVs) by UV correspondence: every texel of a v2 triangle takes the bilinear sample of the 4K
map at the same barycentric point of the triangle's v1 UVs. One resample from the 4K source straight to the final
size, as the plain downsample would be (colour 2K, normal/roughness/metallic 1K; the box filter of an S x S
supersample replaces the Lanczos). The normal map is re-expressed per triangle from the v1 tangent frame (dP/du,
dP/dv of the v1 UVs) into the v2 one, keeping Meshy's green convention (prepare_actor_glb.py flips it later).
Texels outside every triangle are left black: gutter_fill.py fills them last.
Writes textures/v2_basecolor.png, v2_normal_1k.png, v2_roughness_1k.png, v2_metallic_1k.png."""
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'work/v1_filled/texture_urls_0'   # the 4K Meshy maps, gutters re-filled on the v1 layout first
d = np.load(ROOT / 'work/uv_v2.npz'); OLD, NEW, XYZ = d['old'].astype(np.float64), d['new'].astype(np.float64), d['xyz'].astype(np.float64)
Image.MAX_IMAGE_PIXELS = None


def bilinear(img, u, v):
    h, w = img.shape[:2]
    x = np.clip(u * w - 0.5, 0, w - 1.0001); y = np.clip((1 - v) * h - 0.5, 0, h - 1.0001)
    x0 = x.astype(int); y0 = y.astype(int); fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    a = img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx
    b = img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def frames(uv, xyz):
    """Per triangle: orthonormal T (along +u), B (along +v), N from the UV map of each triangle."""
    e1, e2 = xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    T = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]
    B = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
    N = np.cross(e1, e2); N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    T -= N * np.einsum('ij,ij->i', T, N)[:, None]; T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-12
    B -= N * np.einsum('ij,ij->i', B, N)[:, None] + T * np.einsum('ij,ij->i', B, T)[:, None]
    B /= np.linalg.norm(B, axis=1, keepdims=True) + 1e-12
    return T, B, N


def transfer(img, size, ss=3, normal=False):
    out = np.zeros((size, size, img.shape[2]), np.float64); cnt = np.zeros((size, size), np.float64)
    if normal:
        To, Bo, No = frames(OLD, XYZ); Tn, Bn, Nn = frames(NEW, XYZ)
    off = (np.arange(ss) + 0.5) / ss
    for t in range(len(NEW)):
        p = NEW[t] * [size, -size] + [0, size]                     # texel coordinates (y down)
        x0, y0 = np.floor(p.min(0) - 1).astype(int); x1, y1 = np.ceil(p.max(0) + 1).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, size), min(y1, size)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        sx = (gx[..., None, None] + off[None, None, :, None]).reshape(-1)
        sy = (gy[..., None, None] + off[None, None, None, :]).reshape(-1)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (sx - c[0]) + (c[0] - b[0]) * (sy - c[1])) / den
        l1 = ((c[1] - a[1]) * (sx - c[0]) + (a[0] - c[0]) * (sy - c[1])) / den
        l2 = 1 - l0 - l1
        ok = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not ok.any():
            continue
        uvo = l0[ok, None] * OLD[t, 0] + l1[ok, None] * OLD[t, 1] + l2[ok, None] * OLD[t, 2]
        val = bilinear(img, uvo[:, 0], uvo[:, 1])
        if normal:
            n = val * 2 - 1                                        # Meshy: red along +u, green along -v
            w = n[:, :1] * To[t] - n[:, 1:2] * Bo[t] + n[:, 2:3] * No[t]
            val = np.stack([w @ Tn[t], -(w @ Bn[t]), w @ Nn[t]], 1)
            val /= np.linalg.norm(val, axis=1, keepdims=True) + 1e-12
            val = val * 0.5 + 0.5
        px = (sx[ok]).astype(int); py = (sy[ok]).astype(int)
        np.add.at(out, (py, px), val); np.add.at(cnt, (py, px), 1)
    hit = cnt > 0
    out[hit] /= cnt[hit, None]
    # texels touched by a triangle but holding no sub-sample stay empty here, yet gutter_fill counts them as island:
    # fill every empty texel from the nearest filled one (else they stay black: dark hairlines along every v2 seam)
    _, (iy, ix) = ndimage.distance_transform_edt(~hit, return_indices=True)
    out = out[iy, ix]
    print('TRANSFER', size, 'coverage', round(float(hit.mean()), 3), flush=True)
    return out


# Meshy's texels on the last 2-3 texels of each v1 island are half-covered bake edges (dark/odd normals): they drew
# crack lines along the old seams once those seams fell inside v2 islands. Treat them as gutter: the v1 island mask
# (kept faces' v1 UVs, 4K) eroded by ERODE texels, everything outside it re-filled from the nearest inner texel.
from PIL import ImageDraw
from scipy import ndimage
ERODE = 3
_m = Image.new('L', (4096, 4096), 0); _d = ImageDraw.Draw(_m)
for t in OLD:
    _d.polygon([(float(u) * 4096 - 0.5, (1 - float(v)) * 4096 - 0.5) for u, v in t], fill=1)
INNER = ndimage.binary_erosion(np.asarray(_m) > 0, iterations=ERODE)
_, (IY, IX) = ndimage.distance_transform_edt(~INNER, return_indices=True)
del _m, _d


def load(name, mode):
    img = np.asarray(Image.open(f'{SRC}_{name}.png').convert(mode), np.float64) / 255.0
    k = 4096 // img.shape[0]                 # roughness/metallic come at 2K
    return img[IY[::k, ::k] // k, IX[::k, ::k] // k]


OUT = ROOT / 'textures'
col = transfer(load('base_color', 'RGB'), 2048)
Image.fromarray((np.clip(col, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'v2_basecolor.png')
nrm = transfer(load('normal', 'RGB'), 1024, ss=4, normal=True)
Image.fromarray((np.clip(nrm, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'v2_normal_1k.png')
for name in ('roughness', 'metallic'):
    m = transfer(load(name, 'L')[..., None], 1024, ss=4)[..., 0]
    Image.fromarray((np.clip(m, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(OUT / f'v2_{name}_1k.png')
print('DONE')
