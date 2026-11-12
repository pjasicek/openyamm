"""Carries the approved (installed) normal map onto the texture-pass layout, after mm9_eye_claude/scripts/
restore_pebbles.py: per texel the same surface point's normal through the old UVs (each primitive's own image), its XY
turned by the triangle's rotation (or reflection) from the old UV frame to the new one; a tangent-space normal is not a
colour. Then, island by island, the moved normal below SIGMA texels (density-scaled) plus DETAIL x the pass normal's
band above it (textures/<prefix>_normal.png from compose.py). Use it when the installed relief carries the creature's
look (ADragon m182: the snout's spot relief; compose.py's tilt-matched Meshy normal turned it into a crack network).

The rotation is computed in image axes with v pointing up or down; both are built and the one whose result measures the
stronger relief convention (tools/normal_map_convention.measure, glTF +y up is positive) is kept and reported.
Usage: normal_carry.py [prefix textures/tp] [sigma 3] [detail 0.5]  -> overwrites <prefix>_normal.png (the compose
output is kept as <prefix>_normal_meshy.png)"""
import json
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

import tp
import texlib
import texture_quality as TQ

sys.path.insert(0, str(tp.REPO / 'tools'))
import normal_map_convention as NM  # noqa: E402

prefix = sys.argv[1] if len(sys.argv) > 1 else str(tp.HERE / 'textures' / 'tp')
SIGMA = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
DETAIL = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
layout = np.load(tp.HERE / tp.CFG['layout'])
before = np.load(tp.HERE / 'work' / 'lod0_before.npz')
old_uv = before['uv'][before['tri']]
new_uv = layout['uv']
g = tp.Glb(tp.before_glb())
sets = tp.part_images(g.doc)
meshy = f'{prefix}_normal_meshy.png'
try:
    open(meshy, 'rb').close()
except FileNotFoundError:
    shutil.copyfile(f'{prefix}_normal.png', meshy)
paint_img = Image.open(meshy).convert('RGB')
N = paint_img.size[0]
paint = np.asarray(paint_img, np.float32) / 127.5 - 1
tri_id, bary = texlib.raster(new_uv, N)
cov, uvo = texlib.corresponding_uv(tri_id, bary, old_uv)
t = tri_id[cov]
part = layout['part'][t]
sampled = np.zeros((int(cov.sum()), 3), np.float32)
for k, s in enumerate(sets):
    sel = part == k
    img = np.asarray(g.image(s['normal']).convert('RGB'), np.float32) / 127.5 - 1
    sampled[sel] = texlib.bilinear(img, uvo[sel])


def rotations(vflip):
    f = np.array([1.0, vflip])
    eo = np.stack([(old_uv[:, 1] - old_uv[:, 0]) * f, (old_uv[:, 2] - old_uv[:, 0]) * f], 2)   # (T, 2, 2) columns
    en = np.stack([(new_uv[:, 1] - new_uv[:, 0]) * f, (new_uv[:, 2] - new_uv[:, 0]) * f], 2)
    ok = np.abs(np.linalg.det(eo)) > 1e-14
    M = np.zeros_like(eo)
    M[ok] = en[ok] @ np.linalg.inv(eo[ok])
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt
    R[~ok] = np.eye(2)
    return R


isl = TQ.islands(new_uv.astype(np.float64), layout['xyz'].astype(np.float64))
_, isl = np.unique(isl, return_inverse=True)
a2, a3 = tp.tri_area2(new_uv), tp.tri_area3(layout['xyz'])
density = np.sqrt(np.bincount(isl, a2) / np.maximum(np.bincount(isl, a3), 1e-12))
median = float(np.median(density[isl]))
island_map = np.where(tri_id >= 0, isl[np.maximum(tri_id, 0)], -1)
best = None
for vflip in (1.0, -1.0):
    R = rotations(vflip)[t]
    moved = np.zeros((N, N, 3), np.float32)
    mv = sampled.copy()
    mv[:, :2] = np.einsum('nij,nj->ni', R, sampled[:, :2])
    moved[cov] = mv
    out = paint.copy()
    for i, sl in enumerate(ndimage.find_objects(island_map + 1)):
        if sl is None:
            continue
        sigma = SIGMA * density[i] / median
        pad = int(3 * sigma) + 2
        y0, y1 = max(sl[0].start - pad, 0), min(sl[0].stop + pad, N)
        x0, x1 = max(sl[1].start - pad, 0), min(sl[1].stop + pad, N)
        m = (island_map[y0:y1, x0:x1] == i).astype(np.float32)
        den = np.maximum(ndimage.gaussian_filter(m, sigma, mode='constant'), 1e-4)
        inside = m > 0
        for c in range(2):
            low = ndimage.gaussian_filter(moved[y0:y1, x0:x1, c] * m, sigma, mode='constant') / den
            crop = paint[y0:y1, x0:x1, c]
            fine = crop - ndimage.gaussian_filter(crop * m, sigma, mode='constant') / den
            out[y0:y1, x0:x1, c][inside] = (low + DETAIL * fine)[inside]
    out[..., 2] = np.sqrt(np.clip(1 - (out[..., :2] ** 2).sum(-1), 0.0025, 1))
    out /= np.linalg.norm(out, axis=-1, keepdims=True)
    out = texlib.pad(out, cov)
    enc = np.clip((out + 1) * 127.5 + 0.5, 0, 255).astype(np.uint8)
    score = NM.measure(enc)
    print('vflip', vflip, 'convention', round(score, 3))
    if best is None or score > best[0]:
        best = (score, vflip, enc)
Image.fromarray(best[2]).save(f'{prefix}_normal.png')
appr_tilt = float(np.percentile(np.linalg.norm(sampled[:, :2], axis=1), 90))
res = best[2].astype(np.float32)[cov] / 127.5 - 1
report = {'sigma': SIGMA, 'detail': DETAIL, 'vflip': best[1], 'convention': round(best[0], 3),
          'approved_p90_tilt': round(appr_tilt, 3), 'result_p90_tilt': round(float(np.percentile(
              np.linalg.norm(res[:, :2], axis=1), 90)), 3),
          'approved_convention': round(NM.measure(np.asarray(g.image(sets[0]['normal']).convert('RGB'))), 3)}
json.dump(report, open(f'{prefix}_normal_carry.json', 'w'), indent=1)
print('NORMAL_CARRY', json.dumps(report))
