"""Skin tone as the engine shows it (each variant's region ramps applied to the base colour, viewer_variants.bake), at
the same surface points of the installed and the texture-pass GLB:
- patches (face, neck, crossfade, shoulders, hands): median sRGB; the largest chroma difference (CIE a*b*, lightness
  left out: shading is meant to vary) between face patches and across the head/body crossfade; how much of each patch
  the region mask covers (hair or dress ramp on skin);
- edge steps: for every LOD0 edge of the face and neck skin (shell above 1.43 m, front), the colour 2 mm inside each
  of its two triangles; CIE76 dE between the sides, split into UV-seam edges and interior edges. Patchy paint (flat
  facets of different tone) and chart seams show up here.
Points: area-weighted random points on LOD0 skin-shell and hand triangles inside each box, kept where the pass classes
them as skin (textures/m342_tp_classes.npz).

Usage: face_tone.py <before glb> <after glb> [out json]"""
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
before = np.load(HERE / 'work' / 'lod0_before.npz')
lay = np.load(HERE / 'work' / 'uv_cc4_fine.npz')
cls = np.load(HERE / 'textures' / 'm342_tp_classes.npz')['skin']
xyz = lay['xyz']
centre = xyz.mean(1)
piece = before['piece']
X, Y, Z = centre[:, 0], centre[:, 1], centre[:, 2]
SHELL = piece == 1
BOXES = {
    'forehead': SHELL & (abs(X) < 0.03) & (Y > 1.60) & (Y < 1.625) & (Z > 0.08),
    'cheek_r': SHELL & (X < -0.035) & (X > -0.06) & (Y > 1.535) & (Y < 1.57) & (Z > 0.05),
    'cheek_l': SHELL & (X > 0.035) & (X < 0.06) & (Y > 1.535) & (Y < 1.57) & (Z > 0.05),
    'nose': SHELL & (abs(X) < 0.012) & (Y > 1.55) & (Y < 1.58) & (Z > 0.10),
    'chin': SHELL & (abs(X) < 0.02) & (Y > 1.495) & (Y < 1.515) & (Z > 0.07),
    'jaw_r': SHELL & (X < -0.035) & (Y > 1.49) & (Y < 1.53) & (Z > 0.0),
    'jaw_l': SHELL & (X > 0.025) & (Y > 1.49) & (Y < 1.53) & (Z > 0.0),     # the head sits ~1 cm right
    'neck': SHELL & (abs(X) < 0.035) & (Y > 1.44) & (Y < 1.48) & (Z > 0.02),
    'xfade_mid': SHELL & (abs(X) < 0.07) & (Y > 1.36) & (Y < 1.40) & (Z > 0.02),
    'chest': SHELL & (abs(X) < 0.10) & (Y > 1.33) & (Y < 1.36) & (Z > 0.02),
    'shoulder_r': SHELL & (X < -0.13) & (X > -0.19) & (Y > 1.36) & (Y < 1.42),
    'shoulder_l': SHELL & (X > 0.13) & (X < 0.19) & (Y > 1.36) & (Y < 1.42),
    'hand_r': (piece == 0) & (Y < 0.95),
    'hand_l': (piece == 41) & (Y < 0.95),
}
FACE = ['forehead', 'cheek_r', 'cheek_l', 'nose', 'chin', 'jaw_r', 'jaw_l']
XFADE = ['neck', 'xfade_mid', 'chest']
rng = np.random.default_rng(1)
a3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1)
points = {}
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
for name, sel in BOXES.items():
    faces = np.nonzero(sel)[0]
    assert len(faces), f'no triangles in box {name}'
    t = rng.choice(faces, 4000, p=a3[faces] / a3[faces].sum())
    b = rng.dirichlet((1, 1, 1), 4000)
    uvn = (lay['uv'][t] * b[:, :, None]).sum(1)
    keep = texlib.nearest(cls[..., None].astype(np.float32), uvn)[:, 0] > 0.5
    points[name] = (t[keep], b[keep])


# ---- edges of the face/neck skin: for every edge between two skin triangles, a point 1 mm inside each triangle from
# the edge midpoint (2 mm apart across the edge) and a point 2 mm further in, in the first triangle (2 mm apart within
# one triangle). Edges whose triangles are under 3.5 mm high are skipped.
SKIN_FACES = SHELL & (Y > 1.43) & (Z > 0.0) & (abs(X) < 0.08)
wtri = before['weld'][before['tri']]
edge_of = {}
for fi in np.nonzero(SKIN_FACES)[0]:
    for k in range(3):
        key = tuple(sorted((wtri[fi, k], wtri[fi, (k + 1) % 3])))
        edge_of.setdefault(key, []).append((fi, k))
lay_uv = lay['uv']


def bary_of(fi, q):
    p = xyz[fi]
    st = np.linalg.lstsq(np.array([p[1] - p[0], p[2] - p[0]]).T, q - p[0], rcond=None)[0]
    return np.array([1 - st.sum(), st[0], st[1]])


EDGES = {'seam': [[], [], [], [], []], 'interior': [[], [], [], [], []]}
for key, sides in edge_of.items():
    if len(sides) != 2:
        continue
    (fa, ka), (fb, kb) = sides
    pts, ok = [], True
    for fi, k in sides:
        p = xyz[fi]
        mid = (p[k] + p[(k + 1) % 3]) / 2
        inward = p[(k + 2) % 3] - mid
        height = np.linalg.norm(inward)
        if height < 0.0035:
            ok = False
            break
        u = inward / height
        pts.append((bary_of(fi, mid + u * 0.001), bary_of(fi, mid + u * 0.003)))
    if not ok:
        continue
    ua = {tuple(np.round(lay_uv[fa][j], 6)) for j in (ka, (ka + 1) % 3)}
    ub = {tuple(np.round(lay_uv[fb][j], 6)) for j in (kb, (kb + 1) % 3)}
    kind = 'interior' if ua == ub else 'seam'
    keep = all(texlib.nearest(cls[..., None].astype(np.float32), (lay_uv[fi] * w[:, None]).sum(0)[None])[0, 0] > 0.5
               for fi, w in ((fa, pts[0][0]), (fb, pts[1][0]), (fa, pts[0][1])))
    if keep:
        for lst, val in zip(EDGES[kind], (fa, fb, pts[0][0], pts[1][0], pts[0][1])):
            lst.append(val)
EDGES = {k: tuple(np.array(x) for x in v) for k, v in EDGES.items()}


def lab(rgb):
    c = rgb / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz_ = c @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz_ > 0.008856, np.cbrt(xyz_), 7.787 * xyz_ + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def measure(path):
    g = Glb(path)
    doc = g.doc
    pr = doc['meshes'][0]['primitives'][0]
    uv = g.accessor(pr['attributes']['TEXCOORD_0']).astype(np.float64)
    f = g.accessor(pr['indices']).reshape(-1, 3)
    assert len(f) == len(before['tri'])
    mat0 = doc['materials'][0]
    base = g.image(doc['textures'][mat0['pbrMetallicRoughness']['baseColorTexture']['index']]['source']).convert('RGB')
    mask_img = g.image(doc['textures'][mat0['extras']['openyamm_region_mask']['index']]['source'])
    # each channel on its own: an RGBA resize premultiplies alpha
    mask = np.stack([np.asarray(ch.resize(base.size, Image.BILINEAR), np.float32)
                     for ch in mask_img.convert('RGBA').split()], -1) / 255
    out = {}
    for mi in range(9):
        mat = doc['materials'][mi]
        img = bake(base, mask_img, mat['extras']['openyamm_region_ramps']).astype(np.float32)
        rec = {}
        for name, (t, b) in points.items():
            u = (uv[f[t]] * b[:, :, None]).sum(1)
            col = texlib.bilinear(img, u)
            m = texlib.bilinear(mask, u)
            rec[name] = {'median': np.median(col, 0).round(1).tolist(),
                         'mask_dress': round(float(m[:, 0].mean()), 3), 'mask_hair': round(float(m[:, 1].mean()), 3)}
        med = {k: lab(np.array(v['median']))[1:] for k, v in rec.items()}
        face_de = max(np.linalg.norm(med[a] - med[b]) for a in FACE for b in FACE)
        xfade_de = max(np.linalg.norm(med[a] - med[b]) for a in XFADE for b in XFADE)
        all_de = max(np.linalg.norm(med[a] - med[b]) for a in med for b in med)
        steps = {}
        for kind, (ea, eb, pa, pb, pa2) in EDGES.items():
            ca = lab(texlib.bilinear(img, (uv[f[ea]] * pa[:, :, None]).sum(1)))
            cb = lab(texlib.bilinear(img, (uv[f[eb]] * pb[:, :, None]).sum(1)))
            ca2 = lab(texlib.bilinear(img, (uv[f[ea]] * pa2[:, :, None]).sum(1)))
            across = np.linalg.norm(ca - cb, axis=1)
            within = np.linalg.norm(ca - ca2, axis=1)
            steps[kind] = {'edges': int(len(across)), 'across_mean_dE': round(float(across.mean()), 2),
                           'within_mean_dE': round(float(within.mean()), 2),
                           'ratio': round(float(across.mean() / max(within.mean(), 1e-6)), 2),
                           'across_p95_dE': round(float(np.percentile(across, 95)), 2)}
        out[mat['name']] = {'face_max_dab': round(float(face_de), 1), 'crossfade_max_dab': round(float(xfade_de), 1),
                            'all_patches_max_dab': round(float(all_de), 1), 'edge_steps': steps,
                            'max_mask_on_skin': round(max(max(v['mask_dress'], v['mask_hair']) for v in rec.values()), 3),
                            'patches': rec}
    return out


result = {'points': {k: int(len(v[0])) for k, v in points.items()},
          'before': measure(sys.argv[1]), 'after': measure(sys.argv[2])}
if len(sys.argv) > 3:
    json.dump(result, open(sys.argv[3], 'w'), indent=1)
print('points', result['points'])
print('installed -> pass; dab = chroma difference between patch medians; edge steps = across-edge / within-triangle '
      'mean dE (2 mm apart) and their ratio')
for k in result['after']:
    b, a = result['before'][k], result['after'][k]
    es = lambda r, kind: (f"{r['edge_steps'][kind]['across_mean_dE']}/{r['edge_steps'][kind]['within_mean_dE']}"
                          f"={r['edge_steps'][kind]['ratio']}")
    print(f"{k}: face dab {b['face_max_dab']} -> {a['face_max_dab']}, crossfade dab {b['crossfade_max_dab']} -> "
          f"{a['crossfade_max_dab']}, all patches dab {b['all_patches_max_dab']} -> {a['all_patches_max_dab']}, "
          f"seam steps {es(b, 'seam')} -> {es(a, 'seam')}, interior steps {es(b, 'interior')} -> {es(a, 'interior')}, "
          f"mask on skin {b['max_mask_on_skin']} -> {a['max_mask_on_skin']}")
print('edges', {k: len(v[0]) for k, v in EDGES.items()})
a = result['after']['M342_AA']['patches']
b = result['before']['M342_AA']['patches']
for k in a:
    print(f"  {k:16s} before {b[k]['median']}  after {a[k]['median']}")
