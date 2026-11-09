#!/usr/bin/env python3
"""Ears in skin (orchestrator review 2026-11-02, viewer light: the ears poke out of the hair painted in the hair colour, a
blond / brown lump on both tiers; the head turnarounds hid them under the hair, so Meshy painted the face shell's ears as
hair). Face-shell texels (not the hair shell: fringe_fix.py's rule, the loose part with most faces above the eyes) in the ear
zone (|x| > 5.8 cm, rest z 0.755-0.825, y -0.03..0.05) take the tier's cheek skin x 0.93 with the paint's form shading
(broad luminance ^0.3) and a little of its fine detail, feathered over 2 texels.
Usage (project folder): ear_skin_pm3.py <export glb> <prefix> [...]"""
import os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pygltflib import GLTF2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from headpos import texel_positions
glb, prefixes = sys.argv[1], sys.argv[2:]
N = 2048
g = GLTF2().load(glb)
blob = g.binary_blob()


def acc(i):
    a = g.accessors[i]
    bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}[a.type]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16}[a.componentType]
    return np.frombuffer(blob, dtype=dt, count=a.count * n, offset=(bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)


prim = next(p for m in g.meshes for p in m.primitives if g.materials[p.material].name.startswith('PeasantM3Head'))
P = acc(prim.attributes.POSITION).astype(np.float64)
UV = acc(prim.attributes.TEXCOORD_0).astype(np.float64)
I = acc(prim.indices).reshape(-1, 3).astype(np.int64)
# weld by position, then loose parts
_, weld = np.unique(np.round(P, 5), axis=0, return_inverse=True)
weld = weld.ravel()
F = weld[I]
rows = np.concatenate([F[:, 0], F[:, 1], F[:, 2]])
cols = np.concatenate([F[:, 1], F[:, 2], F[:, 0]])
n = weld.max() + 1
_, lab = connected_components(coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)), directed=False)
face_part = lab[F[:, 0]]
cy = P[I].mean(1)[:, 1]
eye_y = 1.66                                       # glTF y up, metres (eyes at about 1.67 on this body)
parts, counts = np.unique(face_part[cy > eye_y], return_counts=True)
hair_part = parts[np.argmax(counts)]
hair_faces = np.where(face_part == hair_part)[0]
print('EARSKIN hair part', int(hair_part), 'faces', len(hair_faces), 'of', len(I))

# rasterise the hair shell's islands
cover = np.zeros((N, N), bool)
for f in hair_faces:
    uv = UV[I[f]] * N
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
    ok = (l >= -0.02).all(1) & (l.sum(1) <= 1.02)
    cover[q[ok, 1].astype(int), q[ok, 0].astype(int)] = True
hair = ndi.binary_dilation(cover, iterations=1)
pos, cov = texel_positions(glb, 'PeasantM3Head', N)
bx = np.nan_to_num(pos[..., 0]); by = -np.nan_to_num(pos[..., 2]); bz = np.nan_to_num(pos[..., 1]) - 0.855
zone0 = cov & ~hair & (np.abs(bx + 0.005) > 0.055) & (bz > 0.75) & (bz < 0.83) & (by > -0.02) & (by < 0.06)
# r2g: the ear is what stands out of the skull: per side, the smallest |x| of face-shell texels within +-1 cm in (y, z) is the
# skull there; texels more than 7 mm further out are ear (the sideburns painted on the skull in front of it stay hair)
ear = np.zeros_like(zone0)
C = 0.002
for sg in (-1, 1):
    m = zone0 & (sg * (bx + 0.005) > 0)
    ax = np.abs(bx[m] + 0.005)
    gy = ((by[m] + 0.02) / C).astype(int); gz = ((bz[m] - 0.75) / C).astype(int)
    grid = np.full((gy.max() + 1, gz.max() + 1), np.inf)
    np.minimum.at(grid, (gy, gz), ax)
    skull = ndi.minimum_filter(grid, size=(11, 11), mode='nearest')[gy, gz]
    sel = ax - skull > 0.007
    iy, ix = np.nonzero(m)
    ear[iy[sel], ix[sel]] = True
ear = ndi.binary_closing(ear, iterations=2) & zone0   # the rim too (r2g: B kept a dark outline)
soft = ndi.gaussian_filter(ear.astype(float), 2.5) * cov * ~hair
cheek = cov & (bz > 0.775) & (bz < 0.79) & (np.abs(bx) > 0.03) & (np.abs(bx) < 0.055) & (by < -0.04)
ear0 = ear
for p in prefixes:
    # r3: rim dilation only for B (its dark outline); on A 4 texels reached the sideburn and left a light patch
    ear = ndi.binary_dilation(ear0, iterations=4 if (p == 'pm3b_tp' and os.environ.get('R5') != '1') else 1) & zone0
    f = Path(f'textures/{p}_head_basecolor.png')
    img = np.asarray(Image.open(f).convert('RGB'), float)
    ref = np.median(img[cheek], 0)
    lum = img @ [0.299, 0.587, 0.114]
    lref = ref @ [0.299, 0.587, 0.114]
    # r2f: only the hair-coloured texels of the zone are repainted, each with the LOCAL skin colour round it (normalised
    # convolution of the skin-like face-shell texels within ~8 texels); a single tone left a lighter rectangle on B's cheek
    chroma = img / np.maximum(img.sum(-1, keepdims=True), 1)
    cref = ref / ref.sum()
    skinlike = cov & ~hair & (np.linalg.norm(chroma - cref, axis=-1) < 0.035) & (lum > 0.55 * lref)
    zone = ndi.binary_dilation(ear, iterations=30)
    src = skinlike & zone
    w = ndi.gaussian_filter(src.astype(float), 8)
    local = np.stack([ndi.gaussian_filter(np.where(src, img[..., c], 0), 8) for c in range(3)], -1) / np.maximum(w, 1e-3)[..., None]
    local = np.where((w > 0.02)[..., None], local, ref[None, None, :] * 0.86)
    paint = ear & ~skinlike
    soft = ndi.gaussian_filter(paint.astype(float), 1.5) * cov * ~hair
    broad = ndi.gaussian_filter(lum, 6)
    m = broad[paint].mean() if paint.any() else 1.0
    shade = (np.clip(broad / max(m, 1), 0.5, 1.6) ** 0.25) * (np.clip(lum / np.maximum(broad, 1), 0.6, 1.6) ** 0.15)
    skin = local * shade[..., None]
    out = img * (1 - soft[..., None]) + skin * soft[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f)
    print('EARSKIN', p, 'ear zone texels', int(ear.sum()), 'repainted', int(paint.sum()), 'ear mean before', img[paint].mean(0).round() if paint.any() else None)
