#!/usr/bin/env python3
"""Keep the approved Basilisk's look on the sharper 4K paint (texture pass 2026-10-30). The fresh paint drifted: frill and
mouth from red-orange to amber, dark scale outlines raised the contrast (legs luminance sd 42 -> 64, p5 33 -> 6), and
the broad pattern changed (mottling, red back patches, red snout and the frill's rays gone or replaced). Two steps:

1. Tone: per region (work/region_mask_paint.png: compose.py's mask of the raw paint), one curve per sRGB channel maps the new distribution onto the approved
   one, measured at the same area-weighted surface points through each layout's UVs. STRENGTH scales the contrast part.
2. Bands: the approved paint is resampled onto the new layout at the same surface points, and every UV island takes the
   approved colour below SIGMA texels (a mask-normalised Gaussian inside the island, SIGMA scaled by the island's own
   density so the surface scale is the same on the denser head) plus the new paint's luminance detail above it x DETAIL,
   tinted by the approved colour there (detail in RGB kept new hue in fine marks: olive horn tips, yellow frill specks).
   The look (colours, mottling, patches) is the approved one, the sharpness is the 4K paint's.

   The red region (frill, mouth) has its own SIGMA and DETAIL: the frill's rays are finer than the mottling and belong
   to the approved look, so more of the approved band stays there.

Usage: match_tone.py <gentle graded png> <out png> [strength 1.0] [sigma 4] [detail 0.8] [red sigma 1.8] [red detail 0.7]
Writes the curves to textures/basilisk_tone_curves.json. Run once on the graded paint; it never reads its own output.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
W, T = HERE / 'work', HERE / 'textures'
OLD = W / 'before_texpass' / 'textures'
src, dst = sys.argv[1], sys.argv[2]
STRENGTH = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
SIGMA = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
DETAIL = float(sys.argv[5]) if len(sys.argv) > 5 else 0.8
RED_SIGMA = float(sys.argv[6]) if len(sys.argv) > 6 else 1.8
RED_DETAIL = float(sys.argv[7]) if len(sys.argv) > 7 else 0.7
N = 1500000
REGIONS = ('red', 'scales')


def bilinear(img, uv):
    h, w = img.shape[:2]
    x, y = uv[:, 0] * w - 0.5, (1 - uv[:, 1]) * h - 0.5
    x0, y0 = np.clip(np.floor(x).astype(int), 0, w - 2), np.clip(np.floor(y).astype(int), 0, h - 2)
    fx, fy = np.clip(x - x0, 0, 1)[:, None], np.clip(y - y0, 0, 1)[:, None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)


old, new = np.load(W / 'uv3d_basilisk.npz'), np.load(W / 'uv3d_basilisk_v2.npz')
assert np.allclose(old['xyz'], new['xyz'], atol=1e-5), 'triangles differ between the layouts'
xyz = old['xyz']
area = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
rng = np.random.default_rng(1)
tri = rng.choice(len(area), N, p=area / area.sum())
b = rng.dirichlet((1, 1, 1), N)[:, :, None]
uv_old, uv_new = (old['uv'][tri] * b).sum(1), (new['uv'][tri] * b).sum(1)
approved = np.asarray(Image.open(OLD / 'basilisk_basecolor_graded.png').convert('RGB'), np.float32)
paint = np.asarray(Image.open(src).convert('RGB'), np.float32)
mask_old = np.asarray(Image.open(OLD / 'basilisk_region_mask.png').convert('RGBA'), np.float32) / 255
mask_new_full = np.stack([np.asarray(ch.resize(paint.shape[1::-1], Image.BILINEAR), np.float32) / 255
                          for ch in Image.open(W / 'region_mask_paint.png').convert('RGBA').split()], -1)
a_s, n_s = bilinear(approved, uv_old), bilinear(paint, uv_new)
m_o, m_n = bilinear(mask_old, uv_old), bilinear(mask_new_full, uv_new)
Q = np.linspace(0, 100, 257)
levels = np.arange(256, dtype=np.float32)
curves, report = {}, {}
for k, name in enumerate(REGIONS):
    sel = (m_o[:, k] > 0.5) & (m_n[:, k] > 0.5)
    report[name] = {'points': int(sel.sum())}
    curves[name] = []
    for c in range(3):
        qa, qn = np.percentile(a_s[sel, c], Q), np.percentile(n_s[sel, c], Q)
        qn = np.maximum.accumulate(qn + np.arange(len(qn)) * 1e-4)
        lut = np.interp(levels, qn, qa)
        # the new mean is moved fully; STRENGTH only scales how far the spread around it follows the approved one
        shift = float(a_s[sel, c].mean() - n_s[sel, c].mean())
        lut = STRENGTH * lut + (1 - STRENGTH) * (levels + shift)
        curves[name].append(np.clip(lut, 0, 255).tolist())
    report[name]['approved'] = a_s[sel].mean(0).round(1).tolist()
    report[name]['new'] = n_s[sel].mean(0).round(1).tolist()
out = np.zeros_like(paint)
weight = np.zeros(paint.shape[:2], np.float32)
for k, name in enumerate(REGIONS):
    w = mask_new_full[..., k]
    mapped = np.stack([np.interp(paint[..., c], levels, curves[name][c]) for c in range(3)], -1)
    out += mapped * w[..., None]
    weight += w
# regions sum to 1 inside the islands; elsewhere (gutter corners) the curve of the larger region applies
rest = np.clip(1 - weight, 0, 1)
if rest.any():
    mapped = np.stack([np.interp(paint[..., c], levels, curves['scales'][c]) for c in range(3)], -1)
    out += mapped * rest[..., None]
# ---- step 2: approved broad colour + new detail, island by island
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import texture_quality as TQ
S = paint.shape[0]
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)
TINT_FLOOR = 8.0                     # keeps the tint finite on near-black texels
tri_id = np.full((S, S), -1, np.int32)
remap = np.zeros_like(paint)
for t, (tn, to) in enumerate(zip(new['uv'], old['uv'])):
    p = np.stack([tn[:, 0] * S, (1 - tn[:, 1]) * S], 1).astype(np.float64)
    lo, hi = np.floor(p.min(0)).astype(int), np.ceil(p.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    M = np.array([p[1] - p[0], p[2] - p[0]]).T
    if not xs.size or abs(np.linalg.det(M)) < 1e-9:
        continue
    st = (np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1) - p[0]) @ np.linalg.inv(M).T
    w = np.stack([1 - st.sum(1), st[:, 0], st[:, 1]], 1)
    inside = (w >= -0.02).all(1)
    if inside.any():
        yy, xx = ys.ravel()[inside], xs.ravel()[inside]
        tri_id[yy, xx] = t
        remap[yy, xx] = bilinear(approved, w[inside] @ to)
isl = TQ.islands(new['uv'].astype(np.float64), new['xyz'].astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
tri_area_uv = np.abs((new['uv'][:, 1, 0] - new['uv'][:, 0, 0]) * (new['uv'][:, 2, 1] - new['uv'][:, 0, 1])
                     - (new['uv'][:, 2, 0] - new['uv'][:, 0, 0]) * (new['uv'][:, 1, 1] - new['uv'][:, 0, 1])) / 2
density = np.sqrt(np.bincount(isl, tri_area_uv) / np.maximum(np.bincount(isl, area), 1e-12))
median = float(np.median(density[isl]))
island_map = np.where(tri_id >= 0, isl[np.maximum(tri_id, 0)], -1)
result = out.copy()
for i in range(int(isl.max()) + 1):
    ys, xs = np.nonzero(island_map == i)
    if not ys.size:
        continue
    scale = density[i] / median
    pad_px = int(3 * max(SIGMA, RED_SIGMA) * scale) + 2
    y0, y1, x0, x1 = max(ys.min() - pad_px, 0), min(ys.max() + pad_px + 1, S), max(xs.min() - pad_px, 0), min(xs.max() + pad_px + 1, S)
    m = (island_map[y0:y1, x0:x1] == i).astype(np.float32)
    red = mask_new_full[y0:y1, x0:x1, 0]
    bands = []
    for sigma, detail in ((SIGMA * scale, DETAIL), (RED_SIGMA * scale, RED_DETAIL)):
        den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-4)
        low_a = np.stack([ndimage.gaussian_filter(remap[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
                          for c in range(3)], -1)
        low_n = np.stack([ndimage.gaussian_filter(out[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
                          for c in range(3)], -1)
        fine = (out[y0:y1, x0:x1] - low_n) @ LUMA
        tint = (low_a + TINT_FLOOR) / (low_a @ LUMA + TINT_FLOOR)[..., None]
        bands.append(low_a + detail * fine[..., None] * tint)
    band = bands[0] * (1 - red[..., None]) + bands[1] * red[..., None]
    result[y0:y1, x0:x1][m > 0] = band[m > 0]
covered = island_map >= 0
_, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
result = result[iy, ix]
Image.fromarray(np.clip(result + 0.5, 0, 255).astype(np.uint8)).save(dst)
json.dump({'strength': STRENGTH, 'sigma': SIGMA, 'detail': DETAIL, 'red_sigma': RED_SIGMA, 'red_detail': RED_DETAIL,
           'report': report, 'curves': curves},
          open(T / 'basilisk_tone_curves.json', 'w'))
print('MATCHED', dst, json.dumps(report))
