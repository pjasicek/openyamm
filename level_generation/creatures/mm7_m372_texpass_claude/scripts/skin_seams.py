"""Face seam measurements per skin, engine colour (region ramps applied as the engine does, viewer_variants.bake):
- mean sRGB of skin at the face front, the neck, the chest in the neckline, the ears/temples and the hands, and the
  largest difference of those means from the face (one continuous tone);
- every UV seam on skin: for each 3D edge whose two triangles sit on different charts, colours sampled on both sides
  at 5 points along the edge; mean / p95 / max of the colour difference (sRGB Euclidean);
- ramp leakage onto skin: share of skin texels whose region mask exceeds 0.02 and the largest change the ramps make
  on face skin.
Usage: skin_seams.py <glb> [label]; prints one JSON line per skin."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
path = sys.argv[1]
g = Glb(path)
doc = g.doc
pr = doc['meshes'][0]['primitives'][0]
uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
tri = g.accessor(pr['indices']).reshape(-1, 3)
pos = g.accessor(pr['attributes']['POSITION']).astype(np.float64)
before = np.load(HERE / 'work' / 'lod0_before.npz')
piece = np.load(HERE / 'work' / 'face_piece_lod0.npy')
region = before['region']
assert len(tri) == len(piece)
mat0 = doc['materials'][0]
base = g.image(doc['textures'][mat0['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
mask = g.image(doc['textures'][mat0['extras']['openyamm_region_mask']['index']]['source'])
size = base.size[0]
mask_arr = np.stack([np.asarray(Image.fromarray(np.asarray(mask.convert('RGBA'))[..., k]).resize(base.size, Image.BILINEAR),
                                np.float32) / 255 for k in range(3)], -1)
c = pos[tri].mean(1)
hair_face = (piece == 9) | ((piece == 1) & (region == 3))
skin_face = np.isin(piece, [1, 2, 3]) & ~hair_face & ~((piece == 1) & (region == 2) & ~((c[:, 0] > 0) & (c[:, 2] < 0.05)))
zones = {'face': skin_face & (piece == 1) & (c[:, 2] > 0.07) & (c[:, 1] > 1.48) & (c[:, 1] < 1.60),
         'neck': skin_face & (piece == 1) & (c[:, 1] > 1.43) & (c[:, 1] < 1.48),
         'chest': skin_face & (piece == 1) & (c[:, 1] <= 1.43),
         'sides': skin_face & (piece == 1) & (c[:, 2] <= 0.07) & (c[:, 1] > 1.48),
         'hands': skin_face & np.isin(piece, [2, 3])}
# skin texels (for leakage) and area-weighted sample points per zone
rng = np.random.default_rng(0)
a3 = np.linalg.norm(np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]]), axis=1)


def samples(faces, n=20000):
    f = np.nonzero(faces)[0]
    pick = rng.choice(f, n, p=a3[f] / a3[f].sum())
    b = rng.dirichlet((1, 1, 1), n)
    return (uv[tri[pick]] * b[:, :, None]).sum(1)


# UV seams on skin
edges = {}
for f in np.nonzero(skin_face)[0]:
    for k in range(3):
        a, b = tri[f, k], tri[f, (k + 1) % 3]
        key = tuple(sorted((tuple(np.round(pos[a], 6)), tuple(np.round(pos[b], 6)))))
        edges.setdefault(key, []).append((f, a, b))
seam_pairs = []
for key, lst in edges.items():
    if len(lst) != 2:
        continue
    (f1, a1, b1), (f2, a2, b2) = lst
    # same 3D edge: match corners by position
    if np.allclose(pos[a1], pos[b2], atol=1e-6):
        a2, b2 = b2, a2
    if np.allclose(uv[a1], uv[a2], atol=1e-6) and np.allclose(uv[b1], uv[b2], atol=1e-6):
        continue                                            # not a UV seam
    seam_pairs.append((uv[a1], uv[b1], uv[a2], uv[b2], f1, f2))
ts = np.linspace(0.1, 0.9, 5)
if seam_pairs:
    U1 = np.concatenate([p[0] + (p[1] - p[0]) * ts[:, None] for p in seam_pairs])
    U2 = np.concatenate([p[2] + (p[3] - p[2]) * ts[:, None] for p in seam_pairs])
    # step half a texel into each triangle (towards its centroid)
    C1 = np.repeat(np.array([uv[tri[p[4]]].mean(0) for p in seam_pairs]), len(ts), 0)
    C2 = np.repeat(np.array([uv[tri[p[5]]].mean(0) for p in seam_pairs]), len(ts), 0)
    step = 0.75 / size

    def inward(U, C):
        d = C - U
        return U + d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9) * step
    U1, U2 = inward(U1, C1), inward(U2, C2)
out = {}
for mi, m in enumerate(doc['materials'][:6]):
    baked = bake(base, mask, m['extras']['openyamm_region_ramps']).astype(np.float32)
    raw = np.asarray(base, np.float32)
    res = {}
    means = {}
    for z, faces in zones.items():
        col = texlib.bilinear(baked, samples(faces))
        means[z] = col.mean(0)
        res[z] = [round(float(x), 1) for x in means[z]]
    res['max_zone_diff_from_face'] = round(float(max(np.linalg.norm(means[z] - means['face']) for z in means)), 1)
    if seam_pairs:
        d = np.linalg.norm(texlib.bilinear(baked, U1) - texlib.bilinear(baked, U2), axis=1)
        res['skin_uv_seams'] = {'edges': len(seam_pairs), 'mean': round(float(d.mean()), 2),
                                'p95': round(float(np.percentile(d, 95)), 2), 'max': round(float(d.max()), 1)}
    fs = samples(zones['face'] | zones['neck'] | zones['chest'])
    mk = texlib.bilinear(mask_arr, fs)
    change = np.linalg.norm(texlib.bilinear(baked, fs) - texlib.bilinear(raw, fs), axis=1)
    res['ramp_leak'] = {'masked_share': round(float((mk.max(1) > 0.02).mean()), 4),
                        'max_change': round(float(change.max()), 1), 'p99_change': round(float(np.percentile(change, 99)), 2)}
    out[m['name']] = res
    print(json.dumps({'glb': Path(path).name, 'label': sys.argv[2] if len(sys.argv) > 2 else '', 'skin': m['name'], **res}))
