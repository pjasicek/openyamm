#!/usr/bin/env python3
"""Chest skin in the shirt opening toned to the neck (PeasantM5, 2026-11-02, head close-ups r2: the body retexture painted the
skin in the V opening much paler and pinker than the head set's neck, a flat "bib" under the jaw; face lessons: feather both
textures to one tone at the head/body seam). Body-set skin texels (warm low-saturation pink-orange, not the shirt) above
YMIN (glTF bind, metres) take a low-frequency gain (Gaussian SIG px, linear light, per channel) toward the median of the
head set's neck skin (YN0..YN1), at full strength above YFULL and fading to none at YMIN; detail stays. Reads
textures/<p>_basecolor_graded_prechest.png (made on the first run), writes textures/<p>_basecolor_graded.png.
Usage (project folder): chest_match.py <body_tex glb> <prefix> <body material> <head material> [YMIN 1.28] [YFULL 1.36]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2
GLB, pre, BM, HM = sys.argv[1:5]
YMIN = float(sys.argv[5]) if len(sys.argv) > 5 else 1.28
YFULL = float(sys.argv[6]) if len(sys.argv) > 6 else 1.36
YN0, YN1, SIG = 1.40, 1.48, 10
g = GLTF2().load(GLB); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
def raster(mat, N):
    p = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == mat)
    P, UV, I = acc(p.attributes.POSITION), acc(p.attributes.TEXCOORD_0), acc(p.indices).reshape(-1, 3).astype(int)
    y = np.full((N, N), np.nan)
    for t in I:
        uv = UV[t] * N; x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)) + 0.5, np.arange(max(y0, 0), min(y1, N)) + 0.5)
        if xs.size == 0: continue
        a, b, c = uv; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12: continue
        l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l2 = 1 - l0 - l1; ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
        y[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = (np.stack([l0, l1, l2], -1)[ins] @ P[t])[:, 1]
    return y
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
def skin(img):
    mx, mn = img.max(2), img.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.degrees(np.arctan2(np.sqrt(3) * (img[..., 1] - img[..., 2]), 2 * img[..., 0] - img[..., 1] - img[..., 2])) % 360
    return ((hue < 32) | (hue > 345)) & (sat > 0.12) & (sat < 0.6) & (img @ [0.299, 0.587, 0.114] > 0.3)
T = Path('textures'); src = T / f'{pre}_basecolor_graded.png'; bak = T / f'{pre}_basecolor_graded_prechest.png'
if not bak.exists(): shutil.copy(src, bak)
B = np.asarray(Image.open(bak).convert('RGB'), np.float64) / 255; NB = B.shape[0]
H = np.asarray(Image.open(T / f'{pre}_head_basecolor.png').convert('RGB'), np.float64) / 255; NH = H.shape[0]
yh = raster(HM, NH); neck = skin(H) & (np.nan_to_num(yh) > YN0) & (np.nan_to_num(yh) < YN1)
ref = np.median(lin(H[neck]), 0)
yb = raster(BM, NB); cov = ~np.isnan(yb); chest = skin(B) & cov & (np.nan_to_num(yb) > YMIN)
# solid skin only (the warm shirt weave has skin-coloured specks): opened, holes filled, components over 1500 texels
chest = ndi.binary_fill_holes(ndi.binary_opening(chest, iterations=3))
lab, n = ndi.label(chest); sizes = ndi.sum(chest, lab, range(1, n + 1)); chest = np.isin(lab, 1 + np.where(sizes > 1500)[0]) & cov
w = np.clip((np.nan_to_num(yb) - YMIN) / (YFULL - YMIN), 0, 1) * chest
w = ndi.gaussian_filter(w, 1.5) * cov
L = lin(B); m = chest.astype(float)
low = np.stack([ndi.gaussian_filter(L[..., k] * m, SIG) for k in range(3)], 2) / np.maximum(ndi.gaussian_filter(m, SIG), 1e-6)[..., None]
gain = np.clip(ref / np.maximum(low, 1e-4), 0.4, 2.5)
out = L * (1 + (gain - 1) * w[..., None])
res = np.where(w[..., None] > 0, srgb(out), B)
Image.fromarray((np.clip(res, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
print('CHEST_MATCH neck ref (sRGB)', (srgb(ref) * 255).round().tolist(), 'chest before', (srgb(np.median(L[chest], 0)) * 255).round().tolist(),
      'texels', int(chest.sum()), 'neck texels', int(neck.sum()))
