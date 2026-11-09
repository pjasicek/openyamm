"""Skin continuity of the Mage per tier as the engine shows it (region ramps applied to the base colour), installed
against the texture pass, on the same LOD0 triangles:
- seams: every welded edge between two face-skin triangles whose UVs differ (that GLB's own seams); colour sampled
  1.5 mm inside each triangle at three points along the edge; mean and p95 of |difference| (sRGB levels, channel
  mean); the same over the edges inside islands as the baseline of ordinary detail 3 mm apart;
- tone: area-weighted mean sRGB of face skin (forehead, cheeks, nose: head-set skin above the moustache) and of the
  hands, their difference, and the face skin's spread (sd of 8 mm-scale patch means over the face);
- mask: share of face-skin and hand texels that a tier region (robe, cape, hair) recolours by more than 10 %.
Face skin excludes the eye sockets (12 mm round each eyeball). Face-skin and hand triangles come from the texture pass class map (skin) at the triangle centre; every sample
is kept only where that class map says skin at the sample point (eyebrows and hairline left out).
Usage: skin_check.py <before glb> <after glb> <classes png> <layout npz> [json out]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
import texlib  # noqa: E402
from viewer_variants import bake  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
before_path, after_path, classes_path, layout_path = sys.argv[1:5]
d = np.load(HERE / 'work' / 'lod0_before.npz')
pos, tri, weld, head_face = d['pos'], d['tri'], d['weld'], d['head_face']
layout = np.load(layout_path)
classes = np.asarray(Image.open(classes_path))
cls_tri = texlib.nearest(classes[..., None], layout['uv'].mean(1))[:, 0]
centre = pos[tri].mean(1)
# eye sockets (within 12 mm of an eyeball centre: lids, lash lines, socket fragments) are reported apart
from scipy.sparse import coo_matrix  # noqa: E402
from scipy.sparse.csgraph import connected_components  # noqa: E402
nweld = int(weld.max()) + 1
wt0 = weld[tri]
_, part = connected_components(coo_matrix((np.ones(3 * len(tri)), (wt0.ravel(), np.roll(wt0, 1, 1).ravel())),
                                          shape=(nweld, nweld)), directed=False)
fp = part[wt0[:, 0]]
eyes = [centre[fp == k].mean(0) for k in np.unique(fp[head_face])
        if 40 <= (fp == k).sum() <= 100 and 1.46 < centre[fp == k].mean(0)[1] < 1.52]
near_eye = np.min([np.linalg.norm(centre - e, axis=1) for e in eyes], 0) < 0.012
face_all = head_face & (cls_tri == 1) & (centre[:, 1] > 1.47) & (centre[:, 2] > 0.06)
face_skin = face_all & ~near_eye
dom = d['joints'][np.arange(len(pos)), d['weights'].argmax(1)]
hand_bones = [i for i, n in enumerate(d['joint_names']) if 'Hand' in str(n) or 'Finger' in str(n)]
hands = ~head_face & (cls_tri == 1) & np.isin(dom[tri], hand_bones).all(1)
area = np.linalg.norm(np.cross(pos[tri[:, 1]] - pos[tri[:, 0]], pos[tri[:, 2]] - pos[tri[:, 0]]), axis=1) / 2

# seam edges between face-skin triangles
wt = weld[tri]
edges = {}
for f in np.nonzero(face_skin)[0]:
    for k in range(3):
        a, b = wt[f, k], wt[f, (k + 1) % 3]
        edges.setdefault((min(a, b), max(a, b)), []).append((f, k))
pairs = [v for v in edges.values() if len(v) == 2]

rng = np.random.default_rng(0)


def samples(sel, n=20000):
    p = area[sel] / area[sel].sum()
    f = np.nonzero(sel)[0][rng.choice(sel.sum(), n, p=p)]
    b = rng.dirichlet((1, 1, 1), n)
    return f, b


def skin_at(f, b):
    return texlib.nearest(classes[..., None], (layout['uv'][f] * b[:, :, None]).sum(1))[:, 0] == 1


def samples_skin(sel, n):
    f, b = samples(sel, n * 3)
    keep = skin_at(f, b)
    return f[keep][:n], b[keep][:n]


face_f, face_b = samples_skin(face_skin, 20000)
hand_f, hand_b = samples_skin(hands, 8000)
face_xyz = (pos[tri[face_f]] * face_b[:, :, None]).sum(1)


def measure(path):
    g = Glb(path)
    doc = g.doc
    mesh = next(m for m in doc['meshes'] if m['name'] == 'M274')
    pr = mesh['primitives'][0]
    uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
    idx = g.accessor(pr['indices']).reshape(-1, 3)
    assert len(idx) == len(tri)
    cuv = uv[idx]                                    # (T, 3, 2) per corner, same triangle order as LOD0
    m0 = doc['materials'][0]
    base = g.image(doc['textures'][m0['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    mask_img = g.image(doc['textures'][m0['extras']['openyamm_region_mask']['index']]['source'])
    # each channel on its own: an RGBA resize premultiplies alpha, and the mask's alpha is 0
    mask = np.stack([np.asarray(ch.resize(base.size, Image.BILINEAR), np.float32)
                     for ch in mask_img.convert('RGBA').split()], -1) / 255
    out = {}
    for mi in range(3):
        mat = doc['materials'][mi]
        img = bake(base, mask_img, mat['extras']['openyamm_region_ramps']).astype(np.float32)

        def colour(f, b):
            return texlib.bilinear(img, (cuv[f] * b[:, :, None]).sum(1))

        diffs, inner = [], []
        for (f1, k1), (f2, k2) in pairs:
            seam = not (np.allclose(cuv[f1, k1], cuv[f2, (k2 + 1) % 3])
                        and np.allclose(cuv[f1, (k1 + 1) % 3], cuv[f2, k2]))
            for tt in (0.2, 0.5, 0.8):
                cols, ok = [], []
                for f, k in ((f1, k1), (f2, k2)):
                    b = np.zeros(3)
                    u = tt if wt[f, k] == wt[f1, k1] else 1 - tt       # same point along the shared edge
                    b[k], b[(k + 1) % 3] = 1 - u, u
                    p_edge = (pos[tri[f]] * b[:, None]).sum(0)
                    opp = pos[tri[f, (k + 2) % 3]]
                    step = min(0.0015 / max(np.linalg.norm(opp - p_edge), 1e-6), 0.4)
                    b = b * (1 - step)
                    b[(k + 2) % 3] += step
                    cols.append(colour(np.array([f]), b[None])[0])
                    ok.append(skin_at(np.array([f]), b[None])[0])
                if all(ok):
                    (diffs if seam else inner).append(np.abs(cols[0] - cols[1]).mean())
        diffs = np.array(diffs)
        inner = np.array(inner)
        fc, hc = colour(face_f, face_b), colour(hand_f, hand_b)
        cell = np.floor(face_xyz / 0.008).astype(int)
        _, inv = np.unique(cell, axis=0, return_inverse=True)
        inv = inv.ravel()
        patch = np.stack([np.bincount(inv, fc[:, c]) / np.bincount(inv) for c in range(3)], 1)
        mface = texlib.bilinear(mask, (cuv[face_f] * face_b[:, :, None]).sum(1))[:, :3]
        mhand = texlib.bilinear(mask, (cuv[hand_f] * hand_b[:, :, None]).sum(1))[:, :3]
        out[mat['name']] = {
            'seam_samples': len(diffs), 'seam_diff_mean': round(float(diffs.mean()), 1),
            'seam_diff_p95': round(float(np.percentile(diffs, 95)), 1),
            'interior_samples': len(inner), 'interior_diff_mean': round(float(inner.mean()), 1),
            'interior_diff_p95': round(float(np.percentile(inner, 95)), 1),
            'face_srgb': [round(float(x), 1) for x in fc.mean(0)],
            'hand_srgb': [round(float(x), 1) for x in hc.mean(0)],
            'face_minus_hand': [round(float(x), 1) for x in fc.mean(0) - hc.mean(0)],
            'face_patch_sd': [round(float(x), 1) for x in patch.std(0)],
            'face_masked_pct': round(100 * float((mface.max(1) > 0.1).mean()), 2),
            'hand_masked_pct': round(100 * float((mhand.max(1) > 0.1).mean()), 2)}
    return out


result = {'before': measure(before_path), 'after': measure(after_path)}
for k in ('before', 'after'):
    for name, v in result[k].items():
        print(k, name, json.dumps(v))
if len(sys.argv) > 5:
    json.dump(result, open(sys.argv[5], 'w'), indent=1)
