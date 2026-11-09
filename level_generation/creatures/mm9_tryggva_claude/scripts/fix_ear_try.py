#!/usr/bin/env python3
"""Ears (ear sweep 2026-11-02, `claude_shared/mm9_overview/ear_sweep_20261102.png` row 21: dark jagged hair-coloured patches on
and around both ears). Last step of scripts/head_chain.sh.

Cause. Meshy fused both ears into the hair shell (the head primitive's loose part with the most faces above the eyes; the ears
are a few dozen of its faces lying under the hair's side edge). Two faults on those faces:
1. fringe_fix.py's first step (hair-shell texels that are skin-coloured, y > HAIR_MIN_Y 1.56, take the nearest hair texel;
   meant for the forehead rim) also took the ears' skin for a painted fringe rim and stamped hair texels over most of the
   right ear and parts of the left: the jagged dark patches on the ears.
2. Meshy's paid head paint (meshy/head_retexture_tp/) already had hair-coloured jagged triangles on the lower ear and on the
   small hair-shell faces just behind / below each ear (the head turnaround's long hair falls past the ears).
Fix. Ear faces = hair-shell faces with the centroid in the ear box (|x| > EAR_X, EAR_Y, EAR_Z; glTF metres, rest pose) whose
composed paint (work/try_tp_head_basecolor_composed.png, before fringe_fix) is at least SKIN_FRAC skin-coloured; all of them
take the composed paint back (undoing fringe_fix there), then per class (see below): core faces (the ear proper) keep their
skin texels and their hair texels take the 3D-neighbourhood mean of the skin around them (FILL_R) plus a little of the ear's
skin grain; lower faces (hanging below the ear onto the cheek) take the face shell's cheek skin under them; flap faces (the
ear's top edge reaching into the hair, and faces on the hair locks behind the ear) take the nearest hair texel on their skin
texels, so the hair still frames the ear. Filled texels are softened 1 px; the head normal map is smoothed on them (Meshy
embossed hair strands there too). Gutters next to changed texels are refilled from the nearest covered texel. Tried and
dropped: painting whole ear faces as skin (skin-coloured flaps poked up into the hair) and filling face-shell texels around
the ear (skin showed through the hair's gaps above and behind the ear); a faint dark crease remains in the left ear where the
face shell shows between its faces.
Reads the *_preear.png backups (made from the current maps on the first run; head_chain.sh deletes them first so a re-run
repeats this on the fresh chain), writes textures/try_tp_head_basecolor.png, textures/try_tp_head_normal_1k.png and
review/fix_ear_mask.png. Usage (project folder): fix_ear_try.py [export glb, default work/try_body_tex.glb]"""
import os
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from pygltflib import GLTF2
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

EAR_X, EAR_Y, EAR_Z = 0.04, (1.57, 1.70), (-0.08, 0.045)
SKIN_FRAC = 0.10                    # ear faces: at least this share of skin in the composed paint
CORE_FRAC = 0.40                    # the ear proper: at least this share of skin
LOWER_Y, LOWER_Z = 1.635, -0.04     # below the ear (y below, z in front of): faces lying on the cheek / neck
FILL_R, GRAIN = 0.006, 0.4          # m: 3D fill radius; share of the ear's skin grain added
MAT = 'TryggvaHead'
glb = sys.argv[1] if len(sys.argv) > 1 else 'work/try_body_tex.glb'
T = Path('textures')
COMPOSED = Path('work/try_tp_head_basecolor_composed.png')


def backup(name):
    f, bk = T / f'{name}.png', T / f'{name}_preear.png'
    if not bk.exists():
        shutil.copyfile(f, bk)
    return f, np.asarray(Image.open(bk).convert('RGB'), float)


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
I = acc(prim.indices).reshape(-1, 3).astype(int)
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True)
F = weld.ravel()[I]
r, c = np.r_[F[:, 0], F[:, 1], F[:, 2]], np.r_[F[:, 1], F[:, 2], F[:, 0]]
nv = F.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(nv, nv)), directed=False)
part = lab[F[:, 0]]
cen = P[I].mean(1)
ids, cnt = np.unique(part[cen[:, 1] > 1.66], return_counts=True)       # the hair shell (as fringe_fix.py)
hair = ids[np.argmax(cnt)]
ids, cnt = np.unique(part[(cen[:, 2] > 0.08) & (cen[:, 1] > 1.6) & (cen[:, 1] < 1.7)], return_counts=True)
face = ids[np.argmax(cnt)]                                             # the face shell (front of the head)

comp = np.asarray(Image.open(COMPOSED).convert('RGB'), float)
N = comp.shape[0]
faceR = np.full((N, N), -1, int)
pos = np.full((N, N, 3), np.nan)
for k, t in enumerate(I):
    uv = UV[t] * N
    x0, y0 = np.maximum(np.floor(uv.min(0)).astype(int), 0)
    x1, y1 = np.minimum(np.ceil(uv.max(0)).astype(int), N - 1)
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, cc = uv
    den = (b[1] - cc[1]) * (a[0] - cc[0]) + (cc[0] - b[0]) * (a[1] - cc[1])
    if abs(den) < 1e-12:
        continue
    l0 = ((b[1] - cc[1]) * (xs - cc[0]) + (cc[0] - b[0]) * (ys - cc[1])) / den
    l1 = ((cc[1] - a[1]) * (xs - cc[0]) + (a[0] - cc[0]) * (ys - cc[1])) / den
    L = np.stack([l0, l1, 1 - l0 - l1], -1)
    ins = (L >= -1e-3).all(-1)
    iy, ix = (ys[ins] - 0.5).astype(int), (xs[ins] - 0.5).astype(int)
    faceR[iy, ix] = k
    pos[iy, ix] = L[ins] @ P[t]
cov = faceR >= 0


def skin_of(im):
    lum = im @ [0.299, 0.587, 0.114]
    return (lum > 80) & (im[..., 0] > 1.3 * im[..., 2])


skin = skin_of(comp)
tot = np.bincount(faceR[cov], minlength=len(I))
frac = np.bincount(faceR[cov], weights=skin[cov], minlength=len(I)) / np.maximum(tot, 1)
box = (np.abs(cen[:, 0]) > EAR_X) & (cen[:, 1] > EAR_Y[0]) & (cen[:, 1] < EAR_Y[1]) & \
      (cen[:, 2] > EAR_Z[0]) & (cen[:, 2] < EAR_Z[1])
ear_faces = (part == hair) & box & (frac >= SKIN_FRAC)
# three classes of ear face:
#  core  - the ear proper: mostly skin in the paint (frac >= CORE_FRAC), plus ear faces whose edge neighbours are mostly
#          core (hair-painted faces inside the ear); skin texels keep the composed paint, the rest takes the ear's skin
#  lower - below the ear (centroid y < LOWER_Y, z > LOWER_Z, not core), lying on the cheek / neck: the cheek skin under
#          them (faces further back lie on the hair locks behind the ear and count as flaps)
#  flap  - the rest: faces at the ear's top edge reaching into the hair; their skin texels take the nearest hair texel
core = ear_faces & (frac >= CORE_FRAC)
edges = {}
for k in np.nonzero(ear_faces)[0]:
    for e0, e1 in ((0, 1), (1, 2), (2, 0)):
        edges.setdefault(tuple(sorted((F[k, e0], F[k, e1]))), []).append(k)
nbr = {k: set() for k in np.nonzero(ear_faces)[0]}
for fs in edges.values():
    for f1 in fs:
        nbr[f1].update(f2 for f2 in fs if f2 != f1)
for _ in range(3):
    grow = [k for k in nbr if not core[k] and sum(core[q] for q in nbr[k]) >= 2]
    if not grow:
        break
    core[grow] = True
lower = ear_faces & ~core & (cen[:, 1] < LOWER_Y) & (cen[:, 2] > LOWER_Z)
flap = ear_faces & ~core & ~lower
cls = np.zeros(len(I), int)
cls[core], cls[lower], cls[flap] = 1, 2, 3
ear = cov & ear_faces[np.clip(faceR, 0, None)]
tcls = np.where(cov, cls[np.clip(faceR, 0, None)], 0)

fa, img = backup('try_tp_head_basecolor')
base = img.copy()
base[ear] = comp[ear]                        # undo fringe_fix.py on the ear faces
X, Y = np.abs(np.nan_to_num(pos[..., 0])), np.nan_to_num(pos[..., 1])
zone = cov & (X > EAR_X - 0.02) & (Y > EAR_Y[0] - 0.04) & (Y < EAR_Y[1] + 0.02)


def fill3d(target, source, radius):
    """Gaussian-weighted mean colour (base) of the source texels within radius (m, 3D) of each target texel."""
    tree = cKDTree(pos[source])
    cols = base[source]
    d, j = tree.query(pos[target], k=64, distance_upper_bound=radius)
    ok = np.isfinite(d)
    j = np.where(ok, j, 0)
    w = ok * np.exp(-(np.where(ok, d, 0) / (radius / 2)) ** 2)
    out = (cols[j] * w[..., None]).sum(1) / np.maximum(w.sum(1), 1e-6)[:, None]
    miss = w.sum(1) < 1e-6
    if miss.any():
        out[miss] = np.median(cols, 0)
    return out


grain = comp - ndimage.gaussian_filter(comp, (3, 3, 0))
gstd = grain[ear & skin].std(0)
noise = ndimage.gaussian_filter(np.random.default_rng(11).normal(0, 1, (N, N)), 0.7)
noise /= max(noise.std(), 1e-6)
skin_b = skin_of(base)
bad_core = (tcls == 1) & ~skin
low = tcls == 2
cheek = zone & skin_b & ~ear & (part[np.clip(faceR, 0, None)] == face)      # the face shell's skin
out = base.copy()
out[bad_core] = fill3d(bad_core, zone & skin_b & ~bad_core & ~low, FILL_R) + noise[bad_core][:, None] * gstd * GRAIN
out[low] = fill3d(low, cheek, 2 * FILL_R) + noise[low][:, None] * gstd * GRAIN
# flap: skin texels take the nearest hair texel in 3D (non-ear hair-shell texels that are not skin)
fl = (tcls == 3) & skin
hairsrc = zone & ~skin_b & (part[np.clip(faceR, 0, None)] == hair) & ~fl
if fl.any():
    _, j = cKDTree(pos[hairsrc]).query(pos[fl])
    out[fl] = base[hairsrc][j]
bad = bad_core | low | fl
soft = ndimage.gaussian_filter(out, (0.8, 0.8, 0))
edge = ndimage.binary_dilation(bad, iterations=1) & ear
out[edge] = soft[edge]
if os.environ.get('FIXEAR_DEBUG'):
    np.save(os.environ['FIXEAR_DEBUG'], cls)


def refill_gutter(a, changed, covered):
    near = ndimage.binary_dilation(changed, iterations=8) & ~covered
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    a[near] = a[iy[near], ix[near]]


refill_gutter(out, ear, cov)
Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(fa)
vis = img.astype(np.uint8).copy()
vis[tcls == 1] = (0, 255, 0)
vis[tcls == 2] = (0, 128, 255)
vis[tcls == 3] = (255, 0, 255)
Image.fromarray(vis).resize((1024, 1024), Image.NEAREST).save('review/fix_ear_mask.png')

def local_mean(src, valid, sigma):
    wv = ndimage.gaussian_filter(valid.astype(float), sigma)
    return np.stack([ndimage.gaussian_filter(src[..., i] * valid, sigma) for i in range(3)], -1) / \
        np.maximum(wv, 1e-6)[..., None], wv


# normal (1K): smooth the filled texels (Meshy embossed hair strands on them)
fn, nrm = backup('try_tp_head_normal_1k')
M = nrm.shape[0]
bad1k = np.asarray(Image.fromarray(np.uint8(ndimage.binary_dilation(bad, iterations=2)) * 255).resize((M, M), Image.BILINEAR)) > 0
cov1k = np.asarray(Image.fromarray(np.uint8(cov) * 255).resize((M, M), Image.BILINEAR)) > 0
ear1k = np.asarray(Image.fromarray(np.uint8(ear) * 255).resize((M, M), Image.BILINEAR)) > 0
sm, _ = local_mean(nrm, ear1k & cov1k, 4.0)
nrm = nrm.copy()
nrm[bad1k & ear1k] = sm[bad1k & ear1k]
refill_gutter(nrm, ear1k, cov1k)
Image.fromarray(np.uint8(np.clip(np.round(nrm), 0, 255))).save(fn)
print('FIXEAR hair part', int(hair), 'ear faces', int(ear_faces.sum()), 'core/lower/flap', int(core.sum()), int(lower.sum()), int(flap.sum()), 'texels', int(ear.sum()), 'filled', int(bad.sum()),
      'grain', gstd.round(1))
