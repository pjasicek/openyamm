#!/usr/bin/env python3
"""Tier A ears and beard edge (user note 2026-11-02, "on his ear some leaked wrong textures"; review/user_notes/).

1. Ears. Both head turnarounds (references_head/, references_head_b/) wear a silver knotwork bead at the end of each
   temple braid, right where the ear is; the mesh has no bead, and the tier A head retexture projected the bead (white
   metal, black engraving, also embossed in its normal and ORM) onto the ear islands, while tier B's retexture put its
   bead on the braid below the ear and painted the ears as skin. The UV islands lying wholly inside the ear box
   (|x| > EAR_X, |z| < EAR_Z, EAR_Y; 3 islands, 94 faces) take tier B's paint times a per-channel gain (tier A cheek
   skin median / tier B cheek skin median, the cheek of fix_neck_pdm1.py), so the ear keeps B's ear shading in A's
   skin tone; tier A's head normal and ORM (tier B's head material uses A's ORM) take B's maps on the same islands.
2. Beard edge. Meshy painted the lower and back edge of the beard on the neck as a dark net (thin crossing lines on
   skin, like a hair net) and a few fainter thin lines below it. On the neck under the jaw (y < NET_TOP, z < NET_Z,
   |x| < NET_X) and outside the dense beard (luminance blurred 4 px < BEARD_LUM), texels darker than their grey
   closing (CLOSE px) by more than NET_DROP whose closed colour is skin (cheek chroma within 0.05 and green < 0.68
   red, so the hair bob's yellow strands stay) take the mean of the line-free skin around them, with a soft brown
   fringe of the local beard colour within FRINGE px of the beard.
Gutters next to changed texels are refilled from the nearest covered texel. Reads the *_preear.png backups (written on
the first run from the current maps), so a rerun repeats the same result.
Order (README step 6): compose -> fix_neck -> hand_clean (A, B) -> fix_collar -> wrist_band -> fix_ear -> tiers.
Usage (project folder): fix_ear_pdm1.py <export glb> [A prefix pdm1_tp] [B prefix pdm1b_tp]"""
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from pygltflib import GLTF2
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions

EAR_X, EAR_Z, EAR_Y = 0.065, 0.05, (0.98, 1.10)       # m, export GLB rest pose (y up, z forward)
NET_TOP, NET_Z, NET_X, NET_DROP = 1.035, 0.045, 0.10, 8.0
CLOSE, FRINGE, BEARD_LUM = 5, 6.0, 100                # px at 2K: closing window, beard fringe; beard luminance
MAT = 'PeasantDM1Head'
glb = sys.argv[1]
A = sys.argv[2] if len(sys.argv) > 2 else 'pdm1_tp'
B = sys.argv[3] if len(sys.argv) > 3 else 'pdm1b_tp'
T = Path('textures')


def backup(name):
    f, bk = T / f'{name}.png', T / f'{name}_preear.png'
    if not bk.exists():
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


def ear_island_mask(n):
    """Raster (n x n, glTF v down) of the head UV islands lying wholly inside the ear box."""
    g = GLTF2().load(glb)
    blob = g.binary_blob()

    def acc(i):
        a = g.accessors[i]
        bv = g.bufferViews[a.bufferView]
        k = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a.componentType]
        return np.frombuffer(blob, dt, a.count * k, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, k)
    prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name == MAT)
    P = acc(prim.attributes.POSITION).astype(float)
    UV = acc(prim.attributes.TEXCOORD_0).astype(float)
    tri = acc(prim.indices).reshape(-1, 3).astype(int)
    _, inv = np.unique(np.round(np.c_[P, UV], 5), axis=0, return_inverse=True)
    f = inv.ravel()[tri]
    nv = f.max() + 1
    r, c = np.r_[f[:, 0], f[:, 1], f[:, 2]], np.r_[f[:, 1], f[:, 2], f[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
    isl = lab[f[:, 0]]
    cen = P[tri].mean(1)
    inside = (np.abs(cen[:, 0]) > EAR_X) & (np.abs(cen[:, 2]) < EAR_Z) & (cen[:, 1] > EAR_Y[0]) & (cen[:, 1] < EAR_Y[1])
    ears = [k for k in np.unique(isl) if inside[isl == k].all()]
    mask = np.zeros((n, n), bool)
    for t in tri[np.isin(isl, ears)]:
        uv = UV[t] * n
        x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0)
        x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), n - 1)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, cc = uv
        den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
        if abs(den) < 1e-12:
            continue
        l0 = ((b[1] - cc[1]) * (xs - cc[0]) + (cc[0] - b[0]) * (ys - cc[1])) / den
        l1 = ((cc[1] - a[1]) * (xs - cc[0]) + (a[0] - cc[0]) * (ys - cc[1])) / den
        ins = (np.stack([l0, l1, 1 - l0 - l1], -1) >= -1e-3).all(-1)
        mask[(ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)] = True
    return mask, [int((isl == k).sum()) for k in ears]


def refill_gutter(out, changed, cov):
    near = ndimage.binary_dilation(changed, iterations=8) & ~cov
    _, (iy, ix) = ndimage.distance_transform_edt(~cov, return_indices=True)
    out[near] = out[iy[near], ix[near]]


N = 2048
pos, cov = texel_positions(glb, MAT, N)
x, y, z = (np.nan_to_num(pos[..., i]) for i in range(3))
cheek = cov & (y > 1.06) & (y < 1.09) & (z > 0.05)
fa, imgA = backup(f'{A}_head_basecolor')
imgB = np.asarray(Image.open(T / f'{B}_head_basecolor.png').convert('RGB'), float)
refA, refB = np.median(imgA[cheek], 0), np.median(imgB[cheek], 0)
gain = refA / refB

# 1. ears
ear, faces = ear_island_mask(N)
out = imgA.copy()
out[ear] = np.clip(imgB[ear] * gain, 0, 255)

# 2. beard-edge net and thin lines on the neck skin
lum = out @ [0.299, 0.587, 0.114]
zone = cov & (y < NET_TOP) & (z < NET_Z) & (np.abs(x) < NET_X) & ~ear
beard = cov & (ndimage.gaussian_filter(lum, 4.0) < BEARD_LUM) & ~ear      # the dense beard (and hair): kept
cand = zone & ~beard
cl = ndimage.grey_closing(lum, size=(CLOSE, CLOSE))
clc = ndimage.grey_closing(out, size=(CLOSE, CLOSE, 1))
chroma = clc / np.maximum(clc.sum(-1, keepdims=True), 1)
# skin under the lines: the closed colour has the cheek's chroma and skin's green/red (hair is yellower, g/r ~0.75)
skin = (np.linalg.norm(chroma - refA / refA.sum(), axis=-1) < 0.05) & (clc[..., 1] < 0.68 * clc[..., 0])
net = cand & skin & (cl - lum > NET_DROP)
net = ndimage.binary_dilation(net, iterations=1) & cand


def local_mean(valid, sigma):
    """Gaussian mean of `out` over the valid texels (normalised convolution) and the valid weight."""
    wv = ndimage.gaussian_filter(valid.astype(float), sigma)
    return np.stack([ndimage.gaussian_filter(out[..., i] * valid, sigma) for i in range(3)], -1) / \
        np.maximum(wv, 1e-6)[..., None], wv


# fill: the mean of the line-free skin around, at the finest of 3 / 6 / 12 px that has enough of it (the net is dense
# next to the beard); within FRINGE px of the beard half the local beard colour, so the beard ends on a soft edge
fill, wf = local_mean(cand & skin & ~net, 12.0)
for sg in (6.0, 3.0):
    f2, w2 = local_mean(cand & skin & ~net, sg)
    fill = np.where((w2 > 0.15)[..., None], f2, fill)
bcol, _ = local_mean(beard, 3.0)
k = (np.clip(1 - ndimage.distance_transform_edt(~beard) / FRINGE, 0, 1) * 0.5)[..., None]
fill = fill * (1 - k) + bcol * k
w = np.clip(ndimage.gaussian_filter(net.astype(float), 1.0) * 1.6, 0, 1) * cand * (wf > 0.01)
out = out * (1 - w[..., None]) + fill * w[..., None]
refill_gutter(out, ear | (w > 0.02), cov)
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fa)

# normal and ORM (1K): tier B's maps on the ear islands
ear1k = np.asarray(Image.fromarray(np.uint8(ear) * 255).resize((1024, 1024), Image.BILINEAR)) > 0
cov1k = np.asarray(Image.fromarray(np.uint8(cov) * 255).resize((1024, 1024), Image.BILINEAR)) > 0
for kind in ('head_normal_1k', 'head_metal_rough_1k'):
    f, a = backup(f'{A}_{kind}')
    b = np.asarray(Image.open(T / f'{B}_{kind}.png').convert('RGB'), float)
    a = a.copy()
    a[ear1k] = b[ear1k]
    refill_gutter(a, ear1k, cov1k)
    Image.fromarray(np.uint8(np.clip(np.round(a), 0, 255))).save(f)
print('FIXEAR', A, 'from', B, 'ear islands (faces)', faces, 'texels', int(ear.sum()), 'gain', gain.round(3),
      'net texels', int((w > 0.5).sum()))
