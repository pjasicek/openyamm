"""Texture-pass maps of the Troll from the two 4K Meshy paints on our layout, keeping the approved look.

1. Paint: body retexture (full-figure masters) and head retexture (head masters, head-set faces only), both on the
   same layout; colour and normal 4K -> 2K once (Lanczos). The head paint covers the approved head set, blended into
   the body paint across the boundary triangles (per-vertex share of head faces, interpolated).
2. Gentle grade (claude_shared/grade_basecolor.py, recipe values) with AO baked on the layout.
3. Tone: per approved region (skin, wrap, crest, mottled back), one curve per sRGB channel maps the graded paint's
   area-weighted distribution onto the approved one at the same surface points (the approved maps carried onto the
   layout by resample_approved.py). Then, island by island, the approved colour below SIGMA texels (scaled by the
   island's density, so the surface scale is the same on the denser head) plus the paint's luminance detail above it
   x DETAIL, tinted by the approved colour (as mm9_basilisk_claude/scripts/match_tone.py). The approved colours,
   mottling and tier ramps hold; the sharpness is the 4K paint's.
4. Normal: the paint's, +y down -> glTF +y up, its tilt x0.3 as the approved build (mm8_m480_claude
   compose_textures.py softnormal); the cook's normal_relief lifts it in game as for every creature.
5. Region mask and metal/roughness: the approved ones carried onto the layout (resample_approved.py).

Usage: compose.py <layout npz> <approved prefix> <ao png> <out prefix> [sigma 4] [detail 0.9]
Writes <out prefix>_{basecolor,normal,metal_rough,region_mask}.png, <out prefix>_raw.png (paint before grade),
<out prefix>_tone.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texlib  # noqa: E402
import texture_quality as TQ  # noqa: E402

layout_path, approved, ao_path, out = sys.argv[1:5]
SIGMA = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
DETAIL = float(sys.argv[6]) if len(sys.argv) > 6 else 0.9
S = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
REGIONS = ('skin', 'wrap', 'crest', 'back')
M = HERE / 'meshy'


def load(path, size=S, mode='RGB'):
    img = Image.open(path).convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, np.float32)


layout = np.load(layout_path)
before = np.load(HERE / 'work' / 'lod0_before.npz')
r = np.load(f'{approved}_raster{S}.npz')
tri_id, bary = r['tri_id'], r['bary']
cov = tri_id >= 0
tri = before['tri']
weld = before['weld']

# ---- 1. paint
body = load(M / 'body_retexture_v2' / 'texture_urls_0_base_color.png')
head = load(M / 'head_retexture_v2' / 'texture_urls_0_base_color.png')
nweld = int(weld.max()) + 1
count = np.bincount(weld[tri].ravel(), minlength=nweld).astype(np.float32)
hcount = np.bincount(weld[tri[before['head_face']]].ravel(), minlength=nweld).astype(np.float32)
head_w_vert = hcount / np.maximum(count, 1)
hw = np.zeros((S, S), np.float32)
t = tri_id[cov]
hw[cov] = (head_w_vert[weld[tri[t]]] * bary[cov]).sum(1)
hw = np.clip(hw, 0, 1)
paint = body * (1 - hw[..., None]) + head * hw[..., None]
paint = texlib.pad(paint, cov)
raw_path = f'{out}_raw.png'
Image.fromarray(np.clip(paint + 0.5, 0, 255).astype(np.uint8)).save(raw_path)

# ---- 2. gentle grade
subprocess.run([sys.executable, str(HERE.parent / 'claude_shared' / 'grade_basecolor.py'), '--ao', ao_path,
                '--fine', '1.0', '--local', '0.3', '--ao-strength', '0.5', '--contrast', '1.06', '--saturation', '1.15',
                raw_path], check=True)
graded = np.asarray(Image.open(f'{out}_raw_graded.png').convert('RGB'), np.float32)

# ---- 3. tone
appr = np.asarray(Image.open(f'{approved}_basecolor.png').convert('RGB'), np.float32)
# each channel on its own: an RGBA resize premultiplies alpha (the mottled-back channel)
mask = np.stack([np.asarray(ch.resize((S, S), Image.BILINEAR), np.float32)
                 for ch in Image.open(f'{approved}_region_mask.png').convert('RGBA').split()], -1) / 255
uv, xyz = layout['uv'], layout['xyz']
area3 = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area2 = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
               - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
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


toned = np.zeros_like(graded)
total = np.zeros((S, S), np.float32)
for k, name in enumerate(REGIONS):
    sel = cov & (mask[..., k] > 0.5)
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
    toned += mapped * mask[..., k:k + 1]
    total += mask[..., k]
rest = np.clip(1 - total, 0, 1)
toned += np.stack([np.interp(graded[..., c], levels, curves['skin'][c]) for c in range(3)], -1) * rest[..., None]

isl = TQ.islands(uv.astype(np.float64), xyz.astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
island_density = np.sqrt(np.bincount(isl, area2) / np.maximum(np.bincount(isl, area3), 1e-12))
median = float(np.median(island_density[isl]))
island_map = np.where(cov, isl[np.maximum(tri_id, 0)], -1)
result = toned.copy()
objs = ndimage.find_objects(island_map + 1)
for i, sl in enumerate(objs):
    if sl is None:
        continue
    scale = island_density[i] / median
    sigma = SIGMA * scale
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
result = texlib.pad(result, cov)
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_basecolor.png')
for name in REGIONS:
    sel = cov & (mask[..., REGIONS.index(name)] > 0.5)
    w = weight[sel]
    report[name]['result'] = [round(float(np.average(result[sel, c], weights=w)), 1) for c in range(3)]
    report[name]['result_luma_sd'] = round(float(np.sqrt(np.cov(result[sel] @ LUMA, aweights=w))), 1)

# ---- 4. normal
normals = []
for src in ('body', 'head'):
    n = load(M / f'{src}_retexture_v2' / 'texture_urls_0_normal.png') / 127.5 - 1
    n[..., 1] *= -1                                                   # Meshy +y down -> glTF +y up
    normals.append(n)
n = normals[0] * (1 - hw[..., None]) + normals[1] * hw[..., None]
tilt = np.linalg.norm(n[..., :2], axis=-1)
old_n = np.asarray(Image.open(HERE / 'work' / 'before_texpass' / 'normal_installed.png').convert('RGB'),
                   np.float32) / 127.5 - 1
target = float(np.percentile(np.linalg.norm(old_n[..., :2], axis=-1), 90))
current = float(np.percentile(tilt[cov], 90))
k_tilt = 0.3
n[..., :2] *= k_tilt
n[..., 2] = np.sqrt(np.clip(1 - (n[..., :2] ** 2).sum(-1), 0.0025, 1))
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n = texlib.pad(n, cov)
Image.fromarray(np.clip((n + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(f'{out}_normal.png')
report['normal'] = {'approved_p90_tilt': round(target, 3), 'paint_p90_tilt': round(current, 3),
                    'scale': round(k_tilt, 3)}

# ---- 5. approved region mask and metal/roughness
for kind in ('region_mask', 'metal_rough'):
    shutil.copyfile(f'{approved}_{kind}.png', f'{out}_{kind}.png')
json.dump({'sigma': SIGMA, 'detail': DETAIL, 'report': report,
           'curves': {k: [c.round(2).tolist() for c in v] for k, v in curves.items()}},
          open(f'{out}_tone.json', 'w'), indent=1)
print('COMPOSED', out, json.dumps(report))
