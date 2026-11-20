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
before = np.load(C.PROJECT / 'work' / 'lod0_before.npz')
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
head_sigma = cfg.get('head_sigma', 0)
head_island = np.bincount(isl, before['head_face'].astype(float), minlength=isl.max() + 1) \
    / np.maximum(np.bincount(isl, minlength=isl.max() + 1), 1) > 0.5
head_px = cov & before['head_face'][np.maximum(tri_id, 0)]
result = toned.copy()
LOWA = np.zeros_like(toned)
FINE = np.zeros((S, S), np.float32)
TINT = np.ones_like(toned)
for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
    if sl is None:
        continue
    sigma = SIGMA * island_density[i] / median
    if head_sigma and head_island[i]:
        sigma = head_sigma                      # face: the approved colour down to this scale (eyes, brows, lids)
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
    LOWA[y0:y1, x0:x1][inside] = low_a[inside]
    FINE[y0:y1, x0:x1][inside] = fine[inside]
    TINT[y0:y1, x0:x1][inside] = tint[inside]
gain = np.ones((S, S), np.float32)
LIMIT = cfg.get('detail_limit', 0.0)
if LIMIT > 0:
    # detail limiter (texpass-2's, mm7_m158_texpass_claude): where the paint's local detail contrast (sd over ~6
    # texels) exceeds LIMIT x its median over the surface, scale it down to that level
    c = cov.astype(np.float32)
    s_loc = np.sqrt(ndimage.gaussian_filter(FINE ** 2 * c, 6) / np.maximum(ndimage.gaussian_filter(c, 6), 1e-4))
    med = float(np.median(s_loc[cov]))
    gain = np.clip(LIMIT * med / np.maximum(s_loc, 1e-6), 0, 1)
    if head_sigma:
        gain[head_px] = 1.0                     # the face keeps its approved detail; the limiter would flatten it
    report['detail_limit'] = {'limit': LIMIT, 'median_local_sd': round(med, 2),
                              'damped_share': round(float((gain[cov] < 0.95).mean()), 4)}
if cfg.get('ornament_faces'):
    # no paint detail within ornament_radius [r0, r1] m (3D) of modelled ornaments (cord, chain, pendant, clasp,
    # buckles): Meshy paints a ghost of them onto the cloth beside them (a second necklace, spirals at the clasp)
    from scipy.spatial import cKDTree
    # ornament_sets: further [faces npy, r0, r1] with their own radius (the clasp ends' painted spirals reach 6 cm)
    sets = [[cfg['ornament_faces']] + list(cfg.get('ornament_radius', [0.012, 0.03]))] + cfg.get('ornament_sets', [])
    px = (bary[cov][:, :, None] * xyz[t]).sum(1)
    og = np.ones(len(px), np.float32)
    for faces_path, r0, r1 in sets:
        orn = np.load(C.PROJECT / faces_path)
        oxyz = xyz[orn]
        samples = np.concatenate([oxyz.reshape(-1, 3), oxyz.mean(1)] +
                                 [(oxyz[:, k] + oxyz[:, (k + 1) % 3]) / 2 for k in range(3)])
        dist, _ = cKDTree(samples).query(px, k=1)
        og = np.minimum(og, np.clip((dist - r0) / (r1 - r0), 0, 1).astype(np.float32))
    orn = np.load(C.PROJECT / cfg['ornament_faces'])
    og[orn[t]] = 1.0                                       # the ornaments themselves: their own rule
    gain[cov] *= og
    orn_gain = np.ones((S, S), np.float32)
    orn_gain[cov] = og
    report['ornament_damped_share'] = round(float((og < 0.95).mean()), 4)
result = np.where(cov[..., None], LOWA + DETAIL * (FINE * gain)[..., None] * TINT, result)
if cfg.get('ornament_faces') and cfg.get('ornament_keep_approved'):
    # near the ornaments the approved colour as it is, not its low-pass (natm: the lower teeth of the necklace are
    # painted on the chest skin, and a 4-texel low-pass smeared them)
    result = result * orn_gain[..., None] + appr * (1 - orn_gain[..., None])
if cfg.get('keep_approved_faces'):
    # faces painted as flat colour by design (modelled cord, chain, pendant: the approved flat squares) keep the
    # approved colour exactly; the paint's detail would only add noise on them
    keep_faces = np.load(C.PROJECT / cfg['keep_approved_faces'])
    keep_px = cov & keep_faces[np.maximum(tri_id, 0)]
    result[keep_px] = appr[keep_px]
    report['keep_approved_faces'] = {'faces': int(keep_faces.sum()), 'texels': int(keep_px.sum())}
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
if cfg.get('keep_approved_faces') and appr_normal.exists():
    # kept faces keep the approved normal too (a paint normal on tiny ornament islands can be any tilt)
    a = np.asarray(Image.open(appr_normal).convert('RGB'), np.float32) / 127.5 - 1
    n[keep_px] = a[keep_px]
if cfg.get('ornament_faces') and appr_normal.exists():
    # the paint's relief of the ghost ornaments goes too: the approved normal near them
    a = np.asarray(Image.open(appr_normal).convert('RGB'), np.float32) / 127.5 - 1
    n[..., :2] = n[..., :2] * orn_gain[..., None] + a[..., :2] * (1 - orn_gain[..., None])
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
if cfg.get('mask_harden') and Path(f'{out}_region_mask.png').exists():
    # the resampled 1K mask spreads a soft edge onto neighbouring skin (Centaur: a green halo beside the harness
    # rim); harden the ramped channels between lo and hi
    lo, hi = cfg['mask_harden']
    mk = np.asarray(Image.open(f'{out}_region_mask.png').convert('RGBA'), np.float32) / 255
    nr = len(_mat.get('extras', {}).get('openyamm_region_ramps', []))
    mk[..., :nr] = np.clip((mk[..., :nr] - lo) / (hi - lo), 0, 1)
    Image.fromarray(np.round(mk * 255).astype(np.uint8), 'RGBA').save(f'{out}_region_mask.png')
    report['mask_harden'] = [lo, hi]
json.dump({'sigma': SIGMA, 'detail': DETAIL, 'report': report,
           'curves': {k: [c.round(2).tolist() for c in v] for k, v in curves.items()}},
          open(f'{out}_tone.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
