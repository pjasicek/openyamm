"""Texture-pass maps from the 4K Meshy paint(s) on our layout, keeping the approved look (the Troll's compose.py made
generic through texpass.json).

1. Paint: meshy/body_retexture_v2 (and, with head_upload, meshy/head_retexture_v2 blended in by the per-vertex head
   weight), colour and normal 4K -> 2K once (Lanczos).
2. Gentle grade (claude_shared/grade_basecolor.py, recipe values) with AO baked on the layout; meshes listed in
   no_ao_meshes (thin wings) take no AO.
3. Tone: per class (each region-mask channel, then the unmasked rest of each layout mesh) one curve per sRGB channel
   maps the graded paint's area-weighted distribution onto the approved one at the same surface points. Then, island
   by island, the approved colour below SIGMA texels (scaled by the island's density) plus the paint's luminance
   detail above it x DETAIL, tinted by the approved colour. Approved colours and tier ramps hold; sharpness is new.
4. Normal: the paint's, converted to +y up when it measures +y down (tools/normal_map_convention.py), its tilt scaled
   so the p90 tilt matches the approved map's (never above 1); written at the installed normal size.
5. Region mask and metal/roughness: the approved ones carried onto the layout (resample.py).

Usage: compose.py [out prefix textures/tp] [sigma 4] [detail 0.9] [detail limit] [approved prefix work/approved]
"""
import json
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import tp
import texlib
import texture_quality as TQ

sys.path.insert(0, str(tp.REPO / 'tools'))
import normal_map_convention as NM  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else str(tp.HERE / 'textures' / 'tp')
SIGMA = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
DETAIL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9
LIMIT = float(sys.argv[4]) if len(sys.argv) > 4 else tp.CFG.get('detail_limit', 0.0)   # 0 = off
approved = sys.argv[5] if len(sys.argv) > 5 else str(tp.HERE / 'work' / 'approved')
S = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
M = tp.HERE / 'meshy'


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


layout = np.load(tp.HERE / tp.CFG['layout'])
before = np.load(tp.HERE / 'work' / 'lod0_before.npz')
parts = [str(p) for p in before['parts']]
r = np.load(f'{approved}_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
t = tri_id[cov]
tri, weld = before['tri'], before['weld']
part_px = np.asarray(Image.open(f'{approved}_part.png'), np.int32) - 1      # -1 outside

# ---- 1. paint
body = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png')
hw = np.zeros((S, S), np.float32)
if tp.CFG.get('head_upload'):
    head = load(M / 'head_retexture_v2' / 'texture_urls_0_base_color.png')
    head_face = before['head_w'][tri].mean(1) > 0.5
    nweld = int(weld.max()) + 1
    count = np.bincount(weld[tri].ravel(), minlength=nweld).astype(np.float32)
    hcount = np.bincount(weld[tri[head_face]].ravel(), minlength=nweld).astype(np.float32)
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
ao = np.asarray(Image.open(tp.HERE / 'textures' / 'tp_ao_2k.png').convert('L'), np.float32)
for name in tp.CFG.get('no_ao_meshes', []):
    for k, p in enumerate(parts):
        if p.split('#')[0] == name:
            ao[part_px == k] = 255
ao_used = f'{out}_ao_used.png'
Image.fromarray(ao.astype(np.uint8)).save(ao_used)
subprocess.run([sys.executable, str(tp.CREATURES / 'claude_shared' / 'grade_basecolor.py'), '--ao', ao_used,
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)

# ---- 3. tone
appr = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.float32)
regions = tp.CFG.get('regions', [])
if regions:
    mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                     for ch in Image.open(f'{approved}_region_mask.png').convert('RGBA').split()], -1)[..., :len(regions)] / 255
else:
    mask = np.zeros((S, S, 0), np.float32)
uv, xyz = layout['uv'], layout['xyz']
area3 = tp.tri_area3(xyz)
area2 = tp.tri_area2(uv)
tri_density = np.sqrt(area2 / np.maximum(area3, 1e-12))
weight = np.zeros((S, S), np.float32)
weight[cov] = 1.0 / np.maximum(tri_density[t], 1e-9) ** 2          # texels -> surface area
Q = np.linspace(0, 100, 257)
levels = np.arange(256, dtype=np.float32)
curves, report = {}, {}


def wpercentile(v, w, q):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    c /= c[-1]
    return np.interp(q / 100, c, v[o])


total = mask.sum(-1) if mask.shape[-1] else np.zeros((S, S), np.float32)
rest = np.clip(1 - total, 0, 1)
classes = []                       # tone classes: each region channel and the unmasked rest, per layout primitive
for kp, p in enumerate(parts):
    pm = part_px == kp
    for k, name in enumerate(regions):
        label = name if len(parts) == 1 else f'{name} {p}'
        classes.append((label, cov & (mask[..., k] > 0.5) & pm, mask[..., k] * pm))
    classes.append((f'rest {p}', cov & (total < 0.5) & pm, rest * pm))
toned = np.zeros_like(graded)
cover = np.zeros((S, S), np.float32)
for name, sel, share in classes:
    if weight[sel].sum() <= 0 or sel.sum() < 50:
        continue
    w = weight[sel]
    curves[name] = []
    for c in range(3):
        qa = wpercentile(appr[sel, c], w, Q)
        qn = wpercentile(graded[sel, c], w, Q)
        qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-4)
        curves[name].append(np.clip(np.interp(levels, qn, qa), 0, 255))
    report[name] = {'share': round(float(w.sum() / weight[cov].sum()), 4),
                    'approved': [round(float(np.average(appr[sel, c], weights=w)), 1) for c in range(3)],
                    'paint': [round(float(np.average(graded[sel, c], weights=w)), 1) for c in range(3)],
                    'approved_luma_sd': round(float(np.sqrt(np.cov(appr[sel] @ LUMA, aweights=w))), 1),
                    'paint_luma_sd': round(float(np.sqrt(np.cov(graded[sel] @ LUMA, aweights=w))), 1)}
    mapped = np.stack([np.interp(graded[..., c], levels, curves[name][c]) for c in range(3)], -1)
    toned += mapped * share[..., None]
    cover += share
toned = np.where(cover[..., None] > 1e-3, toned / np.maximum(cover, 1e-3)[..., None], graded)

isl = TQ.islands(uv.astype(np.float64), xyz.astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
island_density = np.sqrt(np.bincount(isl, area2) / np.maximum(np.bincount(isl, area3), 1e-12))
median = float(np.median(island_density[isl]))
island_map = np.where(cov, isl[np.maximum(tri_id, 0)], -1)
result = toned.copy()
LOWA = np.zeros_like(toned)
FINE = np.zeros((S, S), np.float32)
TINT = np.ones_like(toned)
HEAD_SIGMA = tp.CFG.get('head_sigma')            # head islands: approved colour to a finer scale (faces, eyes)
HEAD_DETAIL = tp.CFG.get('head_detail')          # and less of the paint's detail (Genie m238: grainy face, pale iris)
head_face = before['head_w'][tri].mean(1) > 0.5
for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
    if sl is None:
        continue
    is_head = bool(head_face[tri_id[sl][island_map[sl] == i]].mean() > 0.5)
    sigma = SIGMA * island_density[i] / median           # the paint's band split
    sigma_a = (HEAD_SIGMA if is_head and HEAD_SIGMA is not None else SIGMA) * island_density[i] / median
    pad_px = int(3 * sigma) + 2
    y0, y1 = max(sl[0].start - pad_px, 0), min(sl[0].stop + pad_px, S)
    x0, x1 = max(sl[1].start - pad_px, 0), min(sl[1].stop + pad_px, S)
    m = (island_map[y0:y1, x0:x1] == i).astype(np.float32)
    den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-4)
    if sigma_a > 0:            # approved colour below sigma_a; 0 keeps it unblurred (head islands, crisp edges)
        den_a = np.maximum(ndimage.gaussian_filter(m, sigma_a, mode='constant'), 1e-4)
        low_a = np.stack([ndimage.gaussian_filter(appr[y0:y1, x0:x1, c] * m, sigma_a, mode='constant') / den_a
                          for c in range(3)], -1)
    else:
        low_a = appr[y0:y1, x0:x1].copy()
    low_n = np.stack([ndimage.gaussian_filter(toned[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
                      for c in range(3)], -1)
    fine = (toned[y0:y1, x0:x1] - low_n) @ LUMA
    tint = (low_a + 8.0) / (low_a @ LUMA + 8.0)[..., None]
    detail = HEAD_DETAIL if is_head and HEAD_DETAIL is not None else DETAIL
    band = low_a + detail * fine[..., None] * tint
    inside = m > 0
    result[y0:y1, x0:x1][inside] = band[inside]
    LOWA[y0:y1, x0:x1][inside] = low_a[inside]
    FINE[y0:y1, x0:x1][inside] = (fine * detail / max(DETAIL, 1e-6))[inside]
    TINT[y0:y1, x0:x1][inside] = tint[inside]
if LIMIT > 0:
    # detail limiter: where the paint's local detail contrast (sd over ~6 texels) is above LIMIT x its median over the
    # surface, scale it down to that level: damps patches the new paint invents (Bat nose camouflage) and keeps fur
    c = cov.astype(np.float32)
    s_loc = np.sqrt(ndimage.gaussian_filter(FINE ** 2 * c, 6) / np.maximum(ndimage.gaussian_filter(c, 6), 1e-4))
    med = float(np.median(s_loc[cov]))
    gain = np.clip(LIMIT * med / np.maximum(s_loc, 1e-6), 0, 1)
    result = np.where(cov[..., None], LOWA + DETAIL * (FINE * gain)[..., None] * TINT, result)
    report['detail_limit'] = {'limit': LIMIT, 'median_local_sd': round(med, 2),
                              'damped_share': round(float((gain[cov] < 0.95).mean()), 4)}
for name in tp.CFG.get('keep_approved_regions', []):
    # identity pieces (eyes): the approved colour as it is, feathered by the mask
    keep = mask[..., regions.index(name)] > 0.3
    grow = int(tp.CFG.get('keep_approved_grow', 0))      # texels: also take the pupil/rim the region does not cover
    if grow:
        keep = ndimage.binary_fill_holes(ndimage.binary_dilation(keep, iterations=grow)) & cov
    k = ndimage.gaussian_filter(keep.astype(np.float32), 1.0)[..., None]
    result = result * (1 - k) + appr * k
near = tp.CFG.get('keep_approved_near')          # [[x, y, z, radius], ...] bind-pose metres: eyeballs and other
if near:                                         # identity pieces without a region (Genie m238 eyes)
    cen = layout['xyz'].mean(1)
    keep_tri = np.zeros(len(cen), bool)
    for x, y, z, rad in near:
        keep_tri |= np.linalg.norm(cen - np.array([x, y, z]), axis=1) < rad
    keep = cov & keep_tri[np.maximum(tri_id, 0)]
    k = ndimage.gaussian_filter(ndimage.binary_dilation(keep, iterations=2).astype(np.float32), 1.0)[..., None]
    result = result * (1 - k) + appr * k
    report['keep_approved_near'] = int(keep_tri.sum())
result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')
for name, sel, _ in classes:
    if name not in report:
        continue
    w = weight[sel]
    report[name]['result'] = [round(float(np.average(result[sel, c], weights=w)), 1) for c in range(3)]
    report[name]['result_luma_sd'] = round(float(np.sqrt(np.cov(result[sel] @ LUMA, aweights=w))), 1)

# ---- 4. normal
g = tp.Glb(tp.before_glb())
nsize = min(max(g.image(tp.body_images(g.doc)['normal']).size), 2048)   # square; a 2080x1024 body|head atlas -> 2048


def meshy_normal(src):
    img = Image.open(M / f'{src}_retexture_v2' / 'texture_urls_0_normal.png').convert('RGB')
    rgb = np.asarray(img.resize((S, S), Image.Resampling.LANCZOS), np.float32)
    return rgb / 127.5 - 1


n = meshy_normal('body')
if tp.CFG.get('head_upload'):
    n = n * (1 - hw[..., None]) + meshy_normal('head') * hw[..., None]
convention = NM.measure(np.clip((n + 1) * 127.5, 0, 255).astype(np.uint8))
if convention < -0.1:
    n[..., 1] *= -1                                                   # +y down -> glTF +y up
old_n = np.asarray(Image.open(f'{approved}_normal_installed.png').convert('RGB'), np.float32) / 127.5 - 1
target = float(np.percentile(np.linalg.norm(old_n[..., :2], axis=-1)[cov], 90))
current = float(np.percentile(np.linalg.norm(n[..., :2], axis=-1)[cov], 90))
k_tilt = min(1.0, target / max(current, 1e-6))
n[..., :2] *= k_tilt
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
nimg = Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8))
if nsize != S:
    nimg = nimg.resize((nsize, nsize), Image.Resampling.LANCZOS)
nimg.save(f'{out}_normal.png')
report['normal'] = {'meshy_convention': round(convention, 3), 'out_convention': round(NM.measure(np.asarray(nimg)), 3),
                    'approved_p90_tilt': round(target, 3), 'paint_p90_tilt': round(current, 3),
                    'scale': round(k_tilt, 3), 'size': nsize}

# ---- 5. approved region mask and metal/roughness
for kind in ('region_mask', 'metal_rough', 'emissive', 'occlusion', 'burn'):
    try:
        shutil.copyfile(f'{approved}_{kind}.png', f'{out}_{kind}.png')
    except FileNotFoundError:
        pass
json.dump({'sigma': SIGMA, 'detail': DETAIL, 'report': report,
           'curves': {k: [c.round(2).tolist() for c in v] for k, v in curves.items()}},
          open(f'{out}_tone.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
