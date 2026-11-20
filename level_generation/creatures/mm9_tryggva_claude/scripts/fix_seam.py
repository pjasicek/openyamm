#!/usr/bin/env python3
"""One skin from jaw to collar (neck fix r17, 2026-11-02; coordinator on r16: a straight seam with a tone step where
the head set meets the body set, a rust patch below it on tier B, and a flat hard-edged skin "bib" between jaw and
collar). Normals are continuous across the head/body boundary (checked on the export: shared positions, 0 deg), so
the cause is paint: head_split.py's level cut (z 0.62) runs through the neck shell, and below it the body retexture
painted the shell's flange collar-olive and pale chest skin; the olive went into the jacket region mask, so tier B
draws it rust.
Body texels on the head shell's connected part (the neck/shirt shell, found by welding both primitives), within
REACH of the head set's texels in 3D and not cream shirt, take the low-frequency colour of the nearest head-set neck
texel (Gaussian 6 texels, island-normalised; tier A's head set) plus 60 % of their own fine luminance detail; the
weight eases from 1 at the cut to 0 at REACH. Their region-mask channels are zeroed by the same weight (no ramp: skin).
Replaces fix_chest.py. Reads textures/pm1_tp_basecolor_graded_prechest.png and pm1_region_mask_preseam.png (made on
the first run). Usage (project folder): fix_seam.py <export glb (unmirrored)> [reach m 0.25: the whole flange, incl. the chest skin in the shirt opening]"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from pygltflib import GLTF2
glb = sys.argv[1]; REACH = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25
g = GLTF2().load(glb); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]
    dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[a.componentType]
    return np.frombuffer(blob, dt, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)


prims = {g.materials[p.material].name: p for p in g.meshes[0].primitives}
B, H = prims['PeasantM1'], prims['PeasantM1Head']
PB, UB, TB = acc(B.attributes.POSITION), acc(B.attributes.TEXCOORD_0), acc(B.indices).astype(int).reshape(-1, 3)
PH, UH, TH = acc(H.attributes.POSITION), acc(H.attributes.TEXCOORD_0), acc(H.indices).astype(int).reshape(-1, 3)
# weld both primitives, connected components over triangles
allP = np.vstack([PB, PH])
key, inv = np.unique(np.round(allP, 5), axis=0, return_inverse=True); inv = inv.ravel()
tris = np.vstack([inv[TB], inv[TH + len(PB)]])
parent = np.arange(len(key))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a


for t in tris:
    ra, rb, rc = find(t[0]), find(t[1]), find(t[2])
    parent[rb] = ra; parent[find(rc)] = ra
root = np.array([find(i) for i in range(len(key))])
tb_root, th_root = root[tris[:len(TB), 0]], root[tris[len(TB):, 0]]
neck_h = PH[TH].mean(1)
low_neck = (neck_h[:, 1] < 1.53) & (neck_h[:, 1] > 1.35) & (np.abs(neck_h[:, 0]) < 0.15)   # not the hands (also in the head set)
shell = np.bincount(th_root[low_neck]).argmax()          # the head shell's part (it continues into the shirt shell)
flange = tb_root == shell
print('body tris on the head shell part', int(flange.sum()), 'of', len(TB))


def raster(P, U, T, sel, N):
    pos = np.full((N, N, 3), np.nan)
    for t in T[sel]:
        uv = U[t] * N
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0); x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = uv
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        L = np.stack([l0, l1, 1 - l0 - l1], -1); ins = (L >= -1e-3).all(-1)
        if ins.any():
            pos[(gy[ins] - 0.5).astype(int), (gx[ins] - 0.5).astype(int)] = L[ins] @ P[t]
    return pos


T = Path('textures')
src = T / 'pm1_tp_basecolor_graded_prechest.png'
body = np.asarray(Image.open(src).convert('RGB'), float); N = body.shape[0]
bpos = raster(PB, UB, TB, flange, N); bcov = ~np.isnan(bpos[..., 0])
allb = raster(PB, UB, TB, np.ones(len(TB), bool), N); allcov = ~np.isnan(allb[..., 0])
hd = np.asarray(Image.open(T / 'pm1_tp_head_basecolor.png').convert('RGB'), float); NH = hd.shape[0]
hsel = np.ones(len(TH), bool)
hpos = raster(PH, UH, TH, hsel, NH); hcov = ~np.isnan(hpos[..., 0])
hm = hcov & (np.nan_to_num(hpos[..., 1]) < 1.53) & (np.nan_to_num(hpos[..., 1]) > 1.35) & (np.abs(np.nan_to_num(hpos[..., 0])) < 0.15)
hl = ndimage.gaussian_filter(hd * hcov[..., None], (6, 6, 0)) / np.maximum(ndimage.gaussian_filter(hcov.astype(float), 6), 1e-3)[..., None]
tree = cKDTree(hpos[hm]); hcol = hl[hm]
d, idx = tree.query(np.nan_to_num(bpos[bcov]))
mx, mn = body.max(-1), body.min(-1); sat = (mx - mn) / np.maximum(mx, 1)
shirt = (sat < 0.3) & (body.mean(-1) > 150)
# r17b: every non-shirt texel of the flange is neck skin (a distance feather left collar-olive texels under the jacket
# collar, drawn rust on tier B); only the shirt keeps its paint
w = np.zeros((N, N)); w[bcov] = (d < REACH).astype(float)
w[shirt] = 0
w = np.clip(ndimage.gaussian_filter(w, 1.5) / np.maximum(ndimage.gaussian_filter(allcov.astype(float), 1.5), 1e-3), 0, 1) * allcov
target = np.zeros_like(body); target[bcov] = hcol[idx]
target = ndimage.grey_dilation(target, size=(3, 3, 1)) * (target.sum(-1, keepdims=True) == 0) + target
lum = body @ [0.299, 0.587, 0.114]
detail = np.clip(lum - ndimage.gaussian_filter(lum, 3), -10, 10)[..., None] * 0.6
out = body * (1 - w[..., None]) + (target + detail) * w[..., None]
near = ndimage.binary_dilation(w > 0.02, iterations=6) & ~allcov
_, (iy, ix) = ndimage.distance_transform_edt(~allcov, return_indices=True)
out[near] = out[iy[near], ix[near]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(T / 'pm1_tp_basecolor_graded.png')
mk = T / 'pm1_region_mask.png'; mb = T / 'pm1_region_mask_preseam.png'
if not mb.exists():
    shutil.copyfile(mk, mb)
mask = np.asarray(Image.open(mb).convert('RGBA'), float)
wm = np.asarray(Image.fromarray(np.uint8(w * 255)).resize(mask.shape[1::-1], Image.BILINEAR), float)[..., None] / 255
mask[..., :3] *= (1 - wm)
mask[..., 3] = np.maximum(mask[..., 3] * (1 - wm[..., 0]), wm[..., 0] * 255)      # A = the neck flange region
Image.fromarray(np.uint8(np.clip(mask, 0, 255)), 'RGBA').save(mk)
# region 4 ramps: tier A reproduces the repainted flange, tier B scales it to tier B's own neck tone (head sets differ)
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
rj = T / 'pm1_ramps.json'; rb = T / 'pm1_ramps_preseam.json'
if not rb.exists():
    shutil.copyfile(rj, rb)
doc = json.load(open(rb))
hb = np.asarray(Image.open(T / 'pm1b_tp_head_basecolor.png').convert('RGB'), float)
refA = np.median(hl[hm], 0)
hlb = ndimage.gaussian_filter(hb * hcov[..., None], (6, 6, 0)) / np.maximum(ndimage.gaussian_filter(hcov.astype(float), 6), 1e-3)[..., None]
refB = np.median(hlb[hm], 0)
base = np.clip(out, 0, 255) / 255
w1 = np.asarray(Image.fromarray(np.uint8(w * 255)).resize((1024, 1024), Image.BILINEAR), float) / 255
b1 = np.asarray(Image.fromarray(np.uint8(base * 255)).resize((1024, 1024), Image.LANCZOS), float) / 255
lin = RV.srgb_to_linear(b1) * (RV.srgb_to_linear(refB / 255) / RV.srgb_to_linear(refA / 255))[None, None]
tB = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0, 1), 1 / 2.4) - 0.055)
ramps, err = RV.fit_ramps(b1, {'pm1_a': b1, 'pm1_b': tB}, w1)
for v in doc['variants']:
    doc['materials'][0]['ramps'][v] = doc['materials'][0]['ramps'][v][:3] + [ramps[v]]
doc['regions'] = doc.get('regions', [])[:3] + ['A neck flange below the head cut (fix_seam.py): A as painted, B at tier B neck tone']
doc.setdefault('report', {})['neck_flange'] = {'refA': refA.round(1).tolist(), 'refB': refB.round(1).tolist(), 'fit_8bit': err}
json.dump(doc, open(rj, 'w'), indent=1)
print('FIXSEAM ramps', err)
print('FIXSEAM texels', int((w > 0.5).sum()), 'reach', REACH, 'head neck ref', np.median(hcol, 0).round())
