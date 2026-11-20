#!/usr/bin/env python3
"""Bring the approved pebbled hide back on the 4K paint's layout (2026-10-30). The texture pass kept the approved tone
but not the pebbles: at 3-20 texels the approved paint has 1.3-2 times the energy of the matched one and the new paint's
pattern there is a different one (fine stipple and long veins, correlation 0.10-0.18), so the Basilisk's match_tone.py,
which keeps the new detail, could not bring them back. Here the approved colours supply everything down to the pebble
scale and the 4K paint only its finest band:

    hide = approved below SIGMA + DETAIL * (4K paint's luminance above SIGMA) * the approved tint there

both inside each UV island (mask-normalised Gaussians), SIGMA scaled by the island's density so the surface scale is the
same on the denser core. Mesh parts decide what is hide: the eyeball and teeth pieces keep match_approved.py's texels
byte for byte, and no colour class is read, so compose.py can pick the mouth region from the final colours.

The pebbles are relief too: with the 4K paint's normal map the colour cells look flat and streaky, and its stipple and
veins fight them. So the approved normal map moves with the colour (work/normal_pebbled_1k.png, which compose.py
installs): resampled through the old UVs, its XY turned by each triangle's rotation from the old UV frame to the new one
(a tangent-space normal is not a colour), below NORMAL SIGMA, plus NORMAL DETAIL * the 4K normal's band above it.

Run after match_approved.py, before compose.py, which keeps the 4K normal on the eye and teeth pieces and pins their ramps
(textures/eye_kept_ramps.json). It reads work/approved_graded_on_new.png (approved_on_new.py), the fresh grade textures/eye_basecolor_graded_meshy.png and match_approved.py's textures/eye_basecolor_graded.png, which it
overwrites through a temporary file.
Usage: restore_pebbles.py [sigma 0.5] [detail 0.5] [pebble gain 1.06] [pebble sigma 11] [normal sigma 0.35] [normal detail 0.5]
PEBBLE GAIN > 1 lifts the approved band between SIGMA and PEBBLE SIGMA, which the resampling softened a little.
"""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texture_quality as TQ

W, T = HERE / 'work', HERE / 'textures'
SIGMA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
DETAIL = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
GAIN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.06
PEBBLE = float(sys.argv[4]) if len(sys.argv) > 4 else 11.0
NORMAL_SIGMA = float(sys.argv[5]) if len(sys.argv) > 5 else 0.35
NORMAL_DETAIL = float(sys.argv[6]) if len(sys.argv) > 6 else 0.5
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
TINT_FLOOR = 8.0                     # keeps the tint finite on near-black texels
S = 2048


def load(path):
    return np.asarray(Image.open(path).convert('RGB'), np.float32)


approved, paint, matched = load(W / 'approved_graded_on_new.png'), load(T / 'eye_basecolor_graded_meshy.png'), \
    load(T / 'eye_basecolor_graded.png')
d, old_dump = np.load(W / 'uv3d_eye_v2.npz'), np.load(W / 'uv3d_eye.npz')
assert len(old_dump['uv']) == len(d['uv'])
old_uv = old_dump['uv'].astype(np.float64)
uv, xyz = d['uv'].astype(np.float64), d['xyz'].astype(np.float64)
kept_part = np.isin(d['part'] % 10, (2, 3))     # compose.py: eyes and teeth are these pieces, by mesh part
tri_id = np.full((S, S), -1, np.int32)
for t, tn in enumerate(uv):
    p = np.stack([tn[:, 0] * S, (1 - tn[:, 1]) * S], 1)
    lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    M = np.array([p[1] - p[0], p[2] - p[0]]).T
    if not xs.size or abs(np.linalg.det(M)) < 1e-9:
        continue
    st = (np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1) - p[0]) @ np.linalg.inv(M).T
    w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
    inside = (w >= -0.02).all(1)
    tri_id[ys.ravel()[inside], xs.ravel()[inside]] = t
isl = TQ.islands(uv, xyz)
_, isl = np.unique(isl, return_inverse=True)
area_3d = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
area_uv = np.abs((uv[:, 1, 0] - uv[:, 0, 0]) * (uv[:, 2, 1] - uv[:, 0, 1])
                 - (uv[:, 2, 0] - uv[:, 0, 0]) * (uv[:, 1, 1] - uv[:, 0, 1])) / 2
density = np.sqrt(np.bincount(isl, area_uv) / np.maximum(np.bincount(isl, area_3d), 1e-12))
median = float(np.median(density[isl]))
island_map = np.where(tri_id >= 0, isl[np.maximum(tri_id, 0)], -1)
surface = (tri_id >= 0) & ~kept_part[np.maximum(tri_id, 0)]
result = matched.copy()
paint_lum = paint @ LUMA
for i in range(int(isl.max()) + 1):
    ys, xs = np.nonzero((island_map == i) & surface)
    if not ys.size:
        continue
    scale = float(density[i] / median)
    sigma, pebble = SIGMA * scale, PEBBLE * scale
    pad = int(3 * pebble) + 2
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, S), max(xs.min() - pad, 0), min(xs.max() + pad + 1, S)
    m = ((island_map[y0:y1, x0:x1] == i) & surface[y0:y1, x0:x1]).astype(np.float32)

    def blur(img, s):
        den = np.maximum(ndimage.gaussian_filter(m, s, mode='constant'), 1e-4)
        if img.ndim == 2:
            return ndimage.gaussian_filter(img * m, s, mode='constant') / den
        return np.stack([ndimage.gaussian_filter(img[..., c] * m, s, mode='constant') / den for c in range(3)], -1)

    crop = approved[y0:y1, x0:x1]
    low = blur(crop, sigma)
    if GAIN != 1.0:
        low = low + (GAIN - 1.0) * (low - blur(crop, pebble))
    fine = paint_lum[y0:y1, x0:x1] - blur(paint_lum[y0:y1, x0:x1], sigma)
    tint = (low + TINT_FLOOR) / (low @ LUMA + TINT_FLOOR)[..., None]
    out = low + DETAIL * fine[..., None] * tint
    result[y0:y1, x0:x1][m > 0] = out[m > 0]
covered = tri_id >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
result = result[iy, ix]
target = T / 'eye_basecolor_graded.png'
temporary = target.with_suffix('.tmp.png')
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(temporary)
os.replace(temporary, target)

# ---- the relief: approved normal map on the new layout, 1K
N = 1024
old_normal = np.asarray(Image.open(W / 'before_texpass/textures/eye_normal_1k.png').convert('RGB'), np.float32) / 127.5 - 1
coeff = [ndimage.spline_filter(old_normal[..., c], order=3, mode='nearest') for c in range(3)]
moved = np.zeros((N, N, 3), np.float32)
moved[..., 2] = 1
tri_n = np.full((N, N), -1, np.int32)
for t, (tn, to) in enumerate(zip(uv, old_uv)):
    p = np.stack([tn[:, 0] * N, (1 - tn[:, 1]) * N], 1)
    lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], N)), np.arange(max(lo[1], 0), min(hi[1], N)))
    M = np.array([p[1] - p[0], p[2] - p[0]]).T
    if not xs.size or abs(np.linalg.det(M)) < 1e-9:
        continue
    st = (np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1) - p[0]) @ np.linalg.inv(M).T
    w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
    inside = (w >= -0.02).all(1)
    if not inside.any():
        continue
    yy, xx = ys.ravel()[inside], xs.ravel()[inside]
    q = w[inside] @ to
    x, y = q[:, 0] * old_normal.shape[1] - 0.5, (1 - q[:, 1]) * old_normal.shape[0] - 0.5
    sample = np.stack([ndimage.map_coordinates(c, [y, x], order=3, mode='nearest', prefilter=False) for c in coeff], -1)
    # old edges -> new edges; the nearest rotation (or reflection) turns the normal's XY with the chart. In IMAGE axes (y
    # down): Meshy's normal follows its paint's gradient there (r -0.976), so in Blender's v-up frame the angle comes out
    # inverted and xatlas's 90 degree charts flip their relief.
    flip = np.array([1.0, -1.0])
    e_old = np.array([(to[1] - to[0]) * flip, (to[2] - to[0]) * flip]).T
    e_new = np.array([(tn[1] - tn[0]) * flip, (tn[2] - tn[0]) * flip]).T
    if abs(np.linalg.det(e_old)) < 1e-12:
        continue
    A, _, B = np.linalg.svd(e_new @ np.linalg.inv(e_old))
    sample[:, :2] = sample[:, :2] @ (A @ B).T.astype(np.float32)
    moved[yy, xx] = sample
    tri_n[yy, xx] = t
normal_2k = np.asarray(Image.open(HERE / 'meshy/eye_retexture_v2/texture_urls_0_normal.png').convert('RGB')
                       .resize((S, S), Image.LANCZOS), np.float32) / 255
_, (iy, ix) = ndimage.distance_transform_edt(tri_id < 0, return_indices=True)
paint_normal = np.asarray(Image.fromarray((normal_2k[iy, ix] * 255).astype(np.uint8)).resize((N, N), Image.LANCZOS),
                          np.float32) / 127.5 - 1
island_n = np.where(tri_n >= 0, isl[np.maximum(tri_n, 0)], -1)
surface_n = (tri_n >= 0) & ~kept_part[np.maximum(tri_n, 0)]
normal = paint_normal.copy()
for i in range(int(isl.max()) + 1):
    ys, xs = np.nonzero((island_n == i) & surface_n)
    if not ys.size:
        continue
    sigma = NORMAL_SIGMA * float(density[i] / median)
    pad = int(3 * sigma) + 2
    y0, y1, x0, x1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, N), max(xs.min() - pad, 0), min(xs.max() + pad + 1, N)
    m = ((island_n[y0:y1, x0:x1] == i) & surface_n[y0:y1, x0:x1]).astype(np.float32)
    den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-4)
    for c in range(2):
        low = ndimage.gaussian_filter(moved[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
        crop = paint_normal[y0:y1, x0:x1, c]
        fine = crop - ndimage.gaussian_filter(crop * m, sigma, mode='constant') / den
        normal[y0:y1, x0:x1, c][m > 0] = (low + NORMAL_DETAIL * fine)[m > 0]
    normal[y0:y1, x0:x1, 2][m > 0] = 1.0
normal /= np.linalg.norm(normal, axis=2, keepdims=True)
encoded = np.clip((normal + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)
_, (iy, ix) = ndimage.distance_transform_edt(tri_n < 0, return_indices=True)
Image.fromarray(encoded[iy, ix]).save(W / 'normal_pebbled_1k.png')
hide = surface & (np.asarray(Image.open(W / 'approved_cover_on_new.png')) > 0)
print('PEBBLES', json.dumps({'sigma': SIGMA, 'detail': DETAIL, 'gain': GAIN, 'scale_core': round(float(density.max() / median), 2),
                             'hide_mean': result[hide].mean(0).round(1).tolist(),
                             'approved_mean': approved[hide].mean(0).round(1).tolist(),
                             'hide_lum_sd': round(float((result[hide] @ LUMA).std()), 1),
                             'approved_lum_sd': round(float((approved[hide] @ LUMA).std()), 1)}))
