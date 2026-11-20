#!/usr/bin/env python3
"""Bald crown (mm9_markel, 2026-11-02). MM9's Markel is bald on the crown with a high receding hairline (skin MARKEL.dtx,
head renders review/mm9_ref/head_*.png, the Codex head turnaround), but Smart Topology modelled a full hair cap and the
4K head retexture painted hair over it with only a jagged bald streak in the middle (a pale jagged hairline, the batch's
rejected fringe fault). Every head-set texel whose bind-pose surface point lies inside a top-view ellipse over the crown
(and above the temples) takes the forehead's skin: the forehead's median colour, a broad low-frequency mottle and the
forehead's own fine grain, feathered into the hair over FEATHER of ellipse radius with a strand-scale noise so the hairline
thins out naturally instead of ending in a line. The head normal map is flattened inside the same mask (hair-strand relief
would read on bare skin). Reads work/mk_body_tex.glb (head UVs, material MarkelHead) and the composed head colour (kept as
work/mk_tp_head_basecolor_composed.png on the first run) and the composed normal (work/mk_tp_head_normal_1k_composed.png);
writes textures/mk_tp_head_basecolor.png, textures/mk_tp_head_normal_1k.png, review/bald_mask.png.
Usage (project folder): bald_crown.py [ax 0.068] [az 0.080] [z0 0.012] [ymin 1.700]"""
import shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from pygltflib import GLTF2

AX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.068
AZ = float(sys.argv[2]) if len(sys.argv) > 2 else 0.080
Z0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.012
YMIN = float(sys.argv[4]) if len(sys.argv) > 4 else 1.700
FEATHER = 0.22
TONE = 0.93                 # the bare crown catches the top light: a little darker than the lit forehead's median
COMPOSED = Path('work/mk_tp_head_basecolor_composed.png'); OUT = Path('textures/mk_tp_head_basecolor.png')
NCOMP = Path('work/mk_tp_head_normal_1k_composed.png'); NOUT = Path('textures/mk_tp_head_normal_1k.png')
for a, b in ((OUT, COMPOSED), (NOUT, NCOMP)):
    if not b.exists():
        shutil.copyfile(a, b)
img = np.asarray(Image.open(COMPOSED).convert('RGB')).astype(np.float64) / 255
N = img.shape[0]
g = GLTF2().load('work/mk_body_tex.glb'); blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n,
                         offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('MarkelHead'))
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
hand = P[I].mean(1)[:, 1] < 1.3                       # the grafted hands' faces share the head set
pos = np.full((N, N, 3), np.nan)
for f in np.where(~hand)[0]:
    tri = I[f]; uv = UV[tri] * N
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    xs, ys = np.meshgrid(np.arange(max(x0 - 1, 0), min(x1 + 1, N)), np.arange(max(y0 - 1, 0), min(y1 + 1, N)))
    if xs.size == 0:
        continue
    q = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    a, b, c = uv
    m = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
    if abs(np.linalg.det(m)) < 1e-12:
        continue
    l = np.linalg.solve(m, (q - a).T).T
    w = np.column_stack([1 - l.sum(1), l])
    ok = (w >= -0.03).all(1)
    pos[q[ok, 1].astype(int), q[ok, 0].astype(int)] = w[ok] @ P[tri]
cov = ~np.isnan(pos[..., 0])
X, Y, Z = (np.nan_to_num(pos[..., k]) for k in range(3))
cx = float(np.median(P[:, 0][P[:, 1] > 1.6]))
d = np.sqrt(((X - cx) / AX) ** 2 + ((Z - Z0) / AZ) ** 2)
rng = np.random.default_rng(11)
# strand-scale hairline noise: elongated blobs (hair runs back over the head), so the edge thins in tufts
nz = ndi.gaussian_filter(rng.normal(0, 1, (N, N)), (1.2, 4.0)); nz /= nz.std()
edge = np.clip((1.0 - d) / FEATHER + 0.5 + 0.18 * nz, 0, 1)
ylim = np.clip((Y - YMIN) / 0.018, 0, 1)
alpha = np.where(cov, edge * ylim, 0.0)
alpha = alpha * alpha * (3 - 2 * alpha)
# forehead skin: face-shell-front texels between the brows and the top of the forehead
mx, mn = img.max(2), img.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
lum = img @ np.array([0.299, 0.587, 0.114])
fore = cov & (Y > 1.69) & (Y < 1.72) & (Z > 0.07) & (np.abs(X - cx) < 0.035) & (sat > 0.2) & (lum > 0.35)
skin = np.median(img[fore], 0)
grain = img - ndi.gaussian_filter(img, (2.5, 2.5, 0))
gstd = np.std(grain[fore], 0)
fine = ndi.gaussian_filter(rng.normal(0, 1, (N, N)), 0.7); fine /= fine.std()
# broad mottle as a function of the SURFACE point (a UV-space blur steps at every chart seam): a few 3D sinusoids, ~3-5 cm
kv = rng.normal(0, 1, (6, 3)); kv = kv / np.linalg.norm(kv, axis=1, keepdims=True) * rng.uniform(120, 210, (6, 1))
ph = rng.uniform(0, 2 * np.pi, 6)
broad = sum(np.sin(X * k[0] + Y * k[1] + Z * k[2] + p) for k, p in zip(kv, ph)); broad /= max(broad[cov].std(), 1e-6)
patch = TONE * skin[None, None, :] * (1 + 0.035 * broad[..., None]) + 0.8 * fine[..., None] * gstd[None, None, :]
out = img * (1 - alpha[..., None]) + patch * alpha[..., None]
# pad the repaint into the islands' gutters (bilinear filtering and mips read them): uncovered texels within 4 px take the
# nearest covered texel's result where that texel was repainted
dist, (iy, ix) = ndi.distance_transform_edt(~cov, return_indices=True)
gut = (~cov) & (dist <= 4) & (alpha[iy, ix] > 0)
out[gut] = out[iy[gut], ix[gut]]
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT)
nm = np.asarray(Image.open(NCOMP).convert('RGB')).astype(np.float64) / 255
alpha_p = alpha.copy(); alpha_p[gut] = alpha[iy[gut], ix[gut]]
a1 = np.asarray(Image.fromarray((alpha_p * 255).astype(np.uint8)).resize(nm.shape[1::-1], Image.BILINEAR)) / 255.0
flat = np.array([0.5, 0.5, 1.0])
nout = nm * (1 - a1[..., None]) + flat * a1[..., None]
Image.fromarray((np.clip(nout, 0, 1) * 255 + 0.5).astype(np.uint8)).save(NOUT)
vis = (img * 255).astype(np.uint8).copy()
vis[alpha > 0.5] = (vis[alpha > 0.5] * 0.4 + np.array([255, 0, 255]) * 0.6).astype(np.uint8)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/bald_mask.png')
print('BALD skin', (skin * 255).round().tolist(), 'texels', int((alpha > 0.5).sum()), 'forehead ref', int(fore.sum()))
