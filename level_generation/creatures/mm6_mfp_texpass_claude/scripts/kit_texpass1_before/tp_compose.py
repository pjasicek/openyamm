"""Texture-pass maps from the 4K Meshy paint(s) on our layout, keeping the approved look (generalised from
mm8_m480_texpass_claude/scripts/compose.py).

1. Paint: body retexture and, if given, a head retexture (head faces only) on the same layout; colour and normal
   4K -> 2K once (Lanczos); the head paint is blended in over the head set's boundary (per-vertex head share).
2. Gentle grade (claude_shared/grade_basecolor.py: fine 1.0, local 0.3, AO 0.5, contrast 1.06, saturation 1.15).
3. Tone, per class at the same surface points (the approved maps carried by tp_resample.py): the main primitive's
   region-mask channels (above MIN_SHARE of the surface) and the rest of it, and every other atlas primitive on its own.
   One quantile curve per sRGB channel maps the graded paint's area-weighted distribution onto the approved one (mask
   channels blended by their weights). Then, island by island, the approved colour below SIGMA texels (scaled by the
   island's density) plus the paint's luminance detail above it x DETAIL, tinted by the approved colour.
4. Normal: the paint's (+y down -> glTF +y up), tilt scaled so its p90 matches the approved normal map's p90; an
   approved relief normal (p90 tilt above 0.3, a bake from a denser mesh; keep_normal in texpass.json overrides) is
   kept instead, carried by tp_resample.py, plus the paint's fine detail x0.5.
5. Region mask, metal/roughness and burn map: the approved ones carried onto the layout.

Usage: tp_compose.py <layout npz> <approved prefix> <ao png> <out prefix> <body job> [head job|-] [sigma 4]
                     [detail 0.9]
Writes <out prefix>_{basecolor,normal,metal_rough,region_mask,burn_map}.png, <out prefix>_raw.png, _tone.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

import tp_common as C
import texlib
import texture_quality as TQ

cfg = C.config()
layout_path, approved, ao_path, out, body_job = sys.argv[1:6]
head_job = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != '-' else None
SIGMA = float(sys.argv[7]) if len(sys.argv) > 7 else 4.0
DETAIL = float(sys.argv[8]) if len(sys.argv) > 8 else 0.9
S = cfg.get('size', 2048)
MIN_SHARE = 0.002
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
M = C.PROJECT / 'meshy'


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


layout = np.load(layout_path)
before = np.load(C.lod0_path())
r = np.load(f'{approved}_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = tri_id[cov]
tri, weld = before['tri'], before['weld']
prim_map = np.full((S, S), -1)
prim_map[cov] = before['prim'][t]
main = cfg['atlas_prims'][0]

# ---- 1. paint
body = load(M / body_job / 'texture_urls_0_base_color.png')
hw = np.zeros((S, S), np.float32)
if head_job:
    head = load(M / head_job / 'texture_urls_0_base_color.png')
    nweld = int(weld.max()) + 1
    count = np.bincount(weld[tri].ravel(), minlength=nweld).astype(np.float32)
    hcount = np.bincount(weld[tri[before['head_face']]].ravel(), minlength=nweld).astype(np.float32)
    head_w_vert = hcount / np.maximum(count, 1)
    hw[cov] = (head_w_vert[weld[tri[t]]] * bary[cov]).sum(1)
    hw = np.clip(hw, 0, 1)
    paint = body * (1 - hw[..., None]) + head * hw[..., None]
else:
    paint = body
paint = texlib.pad(paint, cov)
raw_path = f'{out}_raw.png'
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(raw_path)

# ---- 2. gentle grade
subprocess.run([sys.executable, str(C.CREATURES / 'claude_shared' / 'grade_basecolor.py'), '--ao', ao_path,
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)

# ---- 3. tone
appr = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.float32)
mask_path = Path(f'{approved}_region_mask.png')
if mask_path.exists():
    mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                     for ch in Image.open(mask_path).convert('RGBA').split()], -1) / 255
else:
    mask = np.zeros((S, S, 4), np.float32)
mask[prim_map != main] = 0
_g = C.Glb(C.before_glb(cfg))
_mat = _g.doc['materials'][_g.doc['meshes'][C.lod0_mesh_index(_g.doc, cfg['node'])]['primitives'][main]['material']]
mask[..., len(_mat.get('extras', {}).get('openyamm_region_ramps', [])):] = 0     # channels without a ramp (an RGB
                                                                                 # mask reads alpha 255) are no region
uv, xyz = layout['uv'], layout['xyz']
area3 = C.tri_area3(xyz)
area2 = C.tri_area2(uv)
tri_density = np.sqrt(area2 / np.maximum(area3, 1e-12))
weight = np.zeros((S, S), np.float32)
weight[cov] = 1.0 / np.maximum(tri_density[t], 1e-9) ** 2
Q = np.linspace(0, 100, 257)
levels = np.arange(256, dtype=np.float32)


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q / 100, c, v[o])


def fit(sel):
    w = weight[sel]
    curve = []
    for c in range(3):
        qa = wpercentile(appr[sel, c], w, Q)
        qn = wpercentile(graded[sel, c], w, Q)
        qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-4)
        curve.append(np.clip(np.interp(levels, qn, qa), 0, 255))
    return curve


def stats(img, sel):
    w = weight[sel]
    return {'mean': [round(float(np.average(img[sel, c], weights=w)), 1) for c in range(3)],
            'luma_sd': round(float(np.sqrt(np.cov(img[sel] @ LUMA, aweights=w))), 1)}


def apply(curve, img):
    return np.stack([np.interp(img[..., c], levels, curve[c]) for c in range(3)], -1)


total_w = weight[cov].sum()
classes, report = {}, {}
main_sel = cov & (prim_map == main)
rest = np.clip(1 - mask.sum(-1), 0, 1)
for k in range(4):
    sel = main_sel & (mask[..., k] > 0.5)
    if weight[sel].sum() / total_w >= MIN_SHARE:
        classes[f'region{k}'] = (sel, mask[..., k])
sel_rest = main_sel & (rest > 0.5)
classes['rest'] = (sel_rest if weight[sel_rest].sum() > 0 else main_sel, rest)
for pi in cfg['atlas_prims'][1:]:
    sel = cov & (prim_map == pi)
    classes[f'prim{pi}'] = (sel, (prim_map == pi).astype(np.float32))
toned = np.zeros_like(graded)
total = np.zeros((S, S), np.float32)
curves = {}
for name, (sel, w_map) in classes.items():
    curves[name] = fit(sel)
    report[name] = {'share': round(float(weight[sel].sum() / total_w), 4), 'approved': stats(appr, sel),
                    'paint': stats(graded, sel)}
    toned += apply(curves[name], graded) * w_map[..., None]
    total += w_map
leftover = np.clip(1 - total, 0, 1)                           # main-primitive regions too small for their own curve
toned += apply(curves['rest'], graded) * leftover[..., None]
toned = toned / np.maximum(total + leftover, 1e-6)[..., None]

isl = TQ.islands(uv.astype(np.float64), xyz.astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
island_density = np.sqrt(np.bincount(isl, area2) / np.maximum(np.bincount(isl, area3), 1e-12))
median = float(np.median(island_density[isl]))
island_map = np.where(cov, isl[np.maximum(tri_id, 0)], -1)
result = toned.copy()
for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
    if sl is None:
        continue
    sigma = SIGMA * island_density[i] / median
    pad_px = int(3 * sigma) + 2
    y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
    x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
    m = (island_map[y0:y1, x0:x1] == i).astype(np.float32)
    den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-4)
    low_a = np.stack([ndimage.gaussian_filter(appr[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
                      for c in range(3)], -1)
    low_n = np.stack([ndimage.gaussian_filter(toned[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
                      for c in range(3)], -1)
    fine = (toned[y0:y1, x0:x1] - low_n) @ LUMA
    tint = (low_a + 8.0) / (low_a @ LUMA + 8.0)[..., None]
    band = low_a + DETAIL * fine[..., None] * tint
    inside = m > 0
    result[y0:y1, x0:x1][inside] = band[inside]
# pin each class's area-weighted mean to the approved one (blended classes and small islands can leave a few levels)
for name, (sel, w_map) in classes.items():
    if not sel.any():
        continue
    shift = np.array([np.average(appr[sel, c] - result[sel, c], weights=weight[sel]) for c in range(3)], np.float32)
    result += np.clip(w_map, 0, 1)[..., None] * shift * (prim_map >= 0)[..., None]
    report[name]['pinned_shift'] = shift.round(1).tolist()
eyes = cfg.get('keep_eyes')
if eyes:
    # Keep the approved eye paint (texpass_mm678/HANDOFF.md: a head paint can move or dull the eyes): approved
    # texels of the eye colour rule on head faces, grouped in 3D; within each group's radius + margin the approved
    # colour replaces the pass, feathered over feather_m.
    from scipy.spatial import cKDTree
    head_map = np.zeros((S, S), bool)
    head_map[cov] = before['head_face'][t]
    R_, G_, B_ = appr[..., 0], appr[..., 1], appr[..., 2]
    if 'rule' in eyes:              # a numpy expression over the approved R, G, B (0..255), from texpass.json
        rule = head_map & eval(eyes['rule'], {'np': np, 'R': R_, 'G': G_, 'B': B_})
    else:
        rule = head_map & (R_ > eyes.get('min_r', 110)) & (R_ > G_ + eyes.get('r_minus_g', 40)) \
            & (B_ < eyes.get('b_max_ratio', 0.5) * R_)
    rule = ndimage.binary_opening(rule)
    xyz_map = np.zeros((S, S, 3))
    xyz_map[cov] = (bary[cov][:, :, None] * xyz[t]).sum(1)
    pts = xyz_map[rule]
    weight_eye = np.zeros((S, S), np.float32)
    if len(pts):
        tree = cKDTree(pts)
        pairs = tree.query_pairs(0.01, output_type='ndarray')
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        g_ = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(pts), len(pts)))
        _, lab = connected_components(g_, directed=False)
        groups = []
        for k in np.unique(lab):
            q = pts[lab == k]
            if len(q) < eyes.get('min_texels', 30) or len(q) > eyes.get('max_texels', 1e9):
                continue
            centre = q.mean(0)
            radius = float(np.linalg.norm(q - centre, axis=1).max()) + eyes.get('margin_m', 0.004)
            d_ = np.linalg.norm(xyz_map - centre, axis=-1)
            w_ = np.clip(1 - (d_ - radius) / eyes.get('feather_m', 0.004), 0, 1) * head_map
            weight_eye = np.maximum(weight_eye, w_)
            groups.append({'texels': int(len(q)), 'centre': centre.round(4).tolist(), 'radius_m': round(radius, 4)})
        result = result * (1 - weight_eye[..., None]) + appr * weight_eye[..., None]
    report['keep_eyes'] = groups if len(pts) else []
fresh = cfg.get('fresh_bones')
if fresh:
    # Parts whose approved paint the user rejected (Genie's left bracer): their texels keep the new paint after the
    # tone curves, without the approved low-frequency colour.
    names = [str(n) for n in before['joint_names']]
    fv = C.bone_weight(before['joints'], before['weights'], names, fresh)
    ftri = fv[tri].mean(1)
    fmap = np.zeros((S, S), np.float32)
    fmap[cov] = np.clip((ftri[t] - 0.3) / 0.4, 0, 1)
    fmap = ndimage.gaussian_filter(fmap, 1.0) * cov
    result = result * (1 - fmap[..., None]) + toned * fmap[..., None]
    report['fresh_texels'] = int((fmap > 0.5).sum())
result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')
for name, (sel, _w) in classes.items():
    report[name]['result'] = stats(result, sel)

# ---- 4. normal
normals = []
for job in [body_job] + ([head_job] if head_job else []):
    n = load(M / job / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[-1] * hw[..., None]
g = C.Glb(C.before_glb(cfg))
mesh = g.doc['meshes'][C.lod0_mesh_index(g.doc, cfg['node'])]
old_maps = C.material_maps(g.doc['materials'][mesh['primitives'][main]['material']])
current = float(np.percentile(np.linalg.norm(n[..., :2], axis=-1)[cov], 90))
if 'normal' in old_maps:
    old_n = np.asarray(g.image(g.doc['textures'][old_maps['normal']]['source']).convert('RGB'), np.float32) / 127.5 - 1
    old_tilt = np.linalg.norm(old_n[..., :2], axis=-1)
    target = float(np.percentile(old_tilt[old_tilt > 0.002], 90))
else:
    target = 0.3 * current
k_tilt = float(np.clip(target / max(current, 1e-6), 0.15, 1.0))
appr_normal = Path(f'{approved}_normal.png')
keep = cfg.get('keep_normal', 'auto')
if appr_normal.exists() and (keep is True or (keep == 'auto' and target > 0.3)):
    # a relief normal baked from a denser mesh: keep it (carried onto the layout by tp_resample.py) and add only the
    # paint's fine detail (above 4 texels) x0.5
    a = np.asarray(Image.open(appr_normal).convert('RGB'), np.float32) / 127.5 - 1
    fine = n[..., :2] - np.stack([ndimage.gaussian_filter(n[..., c], 4.0) for c in range(2)], -1)
    n = a.copy()
    n[..., :2] += 0.5 * fine
    k_tilt = 'approved + 0.5 x paint detail'
else:
    n[..., :2] *= k_tilt
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
report['normal'] = {'approved_p90_tilt': round(target, 3), 'paint_p90_tilt': round(current, 3),
                    'scale': k_tilt if isinstance(k_tilt, str) else round(k_tilt, 3)}

# ---- 5. approved region mask, metal/roughness, burn map
for kind in ('region_mask', 'metal_rough', 'burn_map'):
    if Path(f'{approved}_{kind}.png').exists():
        shutil.copyfile(f'{approved}_{kind}.png', f'{out}_{kind}.png')
json.dump({'sigma': SIGMA, 'detail': DETAIL, 'report': report,
           'curves': {k: [c.round(2).tolist() for c in v] for k, v in curves.items()}},
          open(f'{out}_tone.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
