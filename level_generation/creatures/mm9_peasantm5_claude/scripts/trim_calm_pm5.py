#!/usr/bin/env python3
"""PeasantM5 neckline braid (2026-11-02, viewer face sheet r1): Meshy painted MM9's narrow braided neckline trim over the whole
raised collar of Markel's body (a wide band over the shoulders) as a stark yellow-and-black leopard print. Body texels above YMIN
(glTF bind, m) that hold near-black next to near-white within 9 px (the print; the linen weave never does), closed, hole-filled,
blobs over 150 texels, dilated 2 px: their local mean (Gaussian 6 px) is pulled toward the braid brown BRAID (weight TINT) and
their deviation scaled by CONTRAST, feathered. Reads textures/pm5_tp_basecolor_graded_pretrim.png (made on the first run), writes
textures/pm5_tp_basecolor_graded.png. Run after chest_match.py. Usage (project folder): trim_calm_pm5.py [YMIN 1.30] [CONTRAST 0.35] [TINT 0.6]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, str(Path(__file__).resolve().parent))
YMIN = float(sys.argv[1]) if len(sys.argv) > 1 else 1.30
CON = float(sys.argv[2]) if len(sys.argv) > 2 else 0.35
TINT = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
BRAID = np.array([110, 70, 40]) / 255.0
import importlib.util
spec = importlib.util.spec_from_file_location('cm', str(Path(__file__).resolve().parent / 'chest_match.py'))
src = Path('textures/pm5_tp_basecolor_graded.png'); bak = Path('textures/pm5_tp_basecolor_graded_pretrim.png')
if not bak.exists(): shutil.copy(src, bak)
img = np.asarray(Image.open(bak).convert('RGB'), np.float64) / 255; N = img.shape[0]
# raster of glTF y per body texel (same rule as chest_match.py)
from pygltflib import GLTF2
g = GLTF2().load('work/pm5_body_tex.glb'); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
p = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == 'PeasantM5')
P, UV, I = acc(p.attributes.POSITION), acc(p.attributes.TEXCOORD_0), acc(p.indices).reshape(-1, 3).astype(int)
yt = np.full((N, N), np.nan)
for t in I:
    uv = UV[t] * N; x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)) + 0.5, np.arange(max(y0, 0), min(y1, N)) + 0.5)
    if xs.size == 0: continue
    a, b, c = uv; den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12: continue
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    l2 = 1 - l0 - l1; ins = (l0 >= -1e-3) & (l1 >= -1e-3) & (l2 >= -1e-3)
    yt[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = (np.stack([l0, l1, l2], -1)[ins] @ P[t])[:, 1]
upper = np.nan_to_num(yt, nan=-9) > YMIN
lum = img @ [0.299, 0.587, 0.114]
locmax = ndi.maximum_filter(lum, 9); locmin = ndi.minimum_filter(lum, 9)
spread = np.sqrt(np.maximum(ndi.uniform_filter(lum ** 2, 7) - ndi.uniform_filter(lum, 7) ** 2, 0))
cand = upper & (spread > 0.12) & (locmax > 0.62) & (locmin < 0.2)
cand = ndi.binary_fill_holes(ndi.binary_closing(cand, iterations=4)); cand = ndi.binary_opening(cand, iterations=1)
lab, n = ndi.label(cand); sizes = ndi.sum(cand, lab, range(1, n + 1))
mask = ndi.binary_dilation(np.isin(lab, 1 + np.where(sizes > 150)[0]), iterations=2) & upper
al = ndi.gaussian_filter(mask.astype(float), 1.2)
mean = np.stack([ndi.gaussian_filter(img[..., k], 6) for k in range(3)], 2)
calm = (mean * (1 - TINT) + BRAID * TINT) + CON * (img - mean)
out = img * (1 - al[..., None]) + np.clip(calm, 0, 1) * al[..., None]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(src)
Image.fromarray((mask * 255).astype(np.uint8)).save('work/trim_mask_pm5.png')
print('TRIM_CALM texels', int(mask.sum()), 'blobs', int((sizes > 150).sum()))
