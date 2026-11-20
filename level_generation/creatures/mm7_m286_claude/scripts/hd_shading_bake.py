#!/usr/bin/env python3
"""v2c muscle definition from the HD masters (user review 2026-10-21: "muscles need to stand out more ... chest, abs,
arms"). The masters (references_hd/01_front, 02_back, 03_left, 04_right) show the defined pecs, six-pack, serratus and
arm muscles in the same rest A-pose as the mesh; Meshy's retexture smeared them into patches and the 10k mesh carries
them only softly. This bakes their muscle-scale shading onto the skin texels by orthographic projection:
1. registration per view: scale and height from the hoof soles and horn tips (master alpha rows vs the rest mesh,
   work/rest_v6.npz), the horizontal offset by the silhouette IoU (closed vertex splats);
2. per view a muscle-detail image: log(linear luminance blurred 0.006 m / blurred 0.06 m) - fine paint grain and the
   broad lighting removed, centred on its median;
3. per texel (rest position and normal from the nearest mesh vertices): visible views (z-buffer of the projected mesh,
   2 cm tolerance), weighted by facing^2, averaged.
Writes work/hdshade_UVMap.npy and work/hdshade_HeadUV.npy (log ratio, 0 where no view sees the texel) and
work/hdshade_preview.png. compose_m286.py multiplies the skin albedo by exp(HD_GAIN * value)."""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

P = Path(__file__).resolve().parents[1]
W = P / 'work'
d = np.load(W / 'rest_v6.npz')
co, tris, piece, gar = d['co'], d['tris'], d['piece'], d['garment']
body = piece < 1000
fn = np.cross(co[tris[:, 1]] - co[tris[:, 0]], co[tris[:, 2]] - co[tris[:, 0]])
vn = np.zeros_like(co)
for k in range(3):
    np.add.at(vn, tris[:, k], fn)
vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
tb = body[tris].all(1)
TR = tris[tb]
import os
HAIR_S, HAIR_V = float(os.environ.get('HAIR_S', '2')), float(os.environ.get('HAIR_V', '0'))   # colour mask off (it caught shadowed skin)
Z_TOP = float(os.environ.get('HD_ZTOP', '1.42'))
# view: (file, horizontal axis expression (u = h . p), camera direction toward the viewer)
VIEWS = {'front': ('01_front.png', np.array([1.0, 0, 0]), np.array([0, -1.0, 0])),
         'back': ('02_back.png', np.array([-1.0, 0, 0]), np.array([0, 1.0, 0])),
         'left': ('03_left.png', np.array([0, 1.0, 0]), np.array([1.0, 0, 0])),      # faces image left
         'right': ('04_right.png', np.array([0, -1.0, 0]), np.array([-1.0, 0, 0]))}  # faces image right


def raster(uv, depth, shape):
    """Silhouette and z-buffer (larger depth = nearer the camera) of the body triangles."""
    zb = np.full(shape, -np.inf); H_, W_ = shape
    for t in TR:
        p = uv[t]; z = depth[t]
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W_ - 1), min(y1, H_ - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
        zz = l1 * z[0] + l2 * z[1] + l3 * z[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (zz > sub)
        sub[upd] = zz[upd]
    return zb


def project(view, s, tx, tz, sole):
    _, h, cam = VIEWS[view]
    u = co @ h * s + tx
    v = sole - co[:, 2] * s + tz
    return np.stack([u, v], 1), co @ cam


reg = {}
details = {}
for view, (fname, h, cam) in VIEWS.items():
    im = np.asarray(Image.open(P / 'references_hd' / fname).convert('RGBA'), np.float64) / 255
    alpha = im[..., 3] > 0.5
    rows = np.flatnonzero(alpha.any(1))
    sole = float(rows[-1])
    band = np.zeros(alpha.shape, bool)
    # initial scale: the master's body height (sole to the alpha top below the horns is unknown): from the front fit
    s0 = (rows[-1] - rows[0]) / (co[body, 2].max() - co[body, 2].min())
    cols = np.flatnonzero(alpha[int(sole - 1.1 * s0)])
    tx0 = float(cols.mean()) - float(np.median(co[body] @ h)) * s0 if len(cols) else alpha.shape[1] / 2
    small = 4                                                       # IoU on a 1/4 grid
    A = alpha[::small, ::small]
    bodyc = co[body]

    def iou(s_, tx_, tz_):
        u = (bodyc @ h * s_ + tx_) / small; v = (sole - bodyc[:, 2] * s_ + tz_) / small
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (ui >= 0) & (ui < A.shape[1]) & (vi >= 0) & (vi < A.shape[0])
        M = np.zeros(A.shape, bool); M[vi[ok], ui[ok]] = True
        M = ndimage.binary_closing(ndimage.binary_dilation(M, iterations=1), iterations=3)
        return (M & A).sum() / max((M | A).sum(), 1)
    # scale and height from two landmarks (hoof soles <-> z 0, horn tips <-> the mesh's horn tips): the silhouette IoU
    # preferred a shrunken fit because the mesh's hips/arms were slimmed (reshape.py) and its horns lengthened
    s = (sole - rows[0]) / (co[body, 2].max() - co[body, 2].min()); tz = 0.0
    best = (-1, (s, tx0, tz))
    for tx_ in np.linspace(-80, 80, 41) + tx0:
        sc_ = iou(s, tx_, tz)
        if sc_ > best[0]:
            best = (sc_, (s, tx_, tz))
    s, tx, tz = best[1]
    reg[view] = {'scale_px_per_m': round(float(s), 2), 'tx': round(float(tx), 1), 'tz': round(float(tz), 1),
                 'score': round(float(best[0]), 3), 'sole_row': sole}
    uv, depth = project(view, s, tx, tz, sole)
    zb = raster(uv, depth, alpha.shape)
    lin = np.where(im[..., :3] <= 0.04045, im[..., :3] / 12.92, ((im[..., :3] + 0.055) / 1.055) ** 2.4)
    L = lin @ np.array([0.2126, 0.7152, 0.0722])
    # the masters' mane frames the neck and shoulders (dark, saturated brown): not skin shading, so it neither supports
    # the projection nor enters the normalising blur (it stamped dark blotches on the traps and shoulder caps)
    hsv = np.asarray(Image.open(P / 'references_hd' / fname).convert('RGB').convert('HSV'), np.float64) / 255
    hair = alpha & (hsv[..., 1] > HAIR_S) & (hsv[..., 2] < HAIR_V)
    hair = ndimage.binary_dilation(ndimage.binary_opening(hair, iterations=1), iterations=6)
    alpha = alpha & ~hair
    wgt = alpha.astype(float)
    sf, sb = 0.006 * s, 0.06 * s
    Lf = ndimage.gaussian_filter(L * wgt, sf) / np.maximum(ndimage.gaussian_filter(wgt, sf), 1e-4)
    Lb = ndimage.gaussian_filter(L * wgt, sb) / np.maximum(ndimage.gaussian_filter(wgt, sb), 1e-4)
    det = np.where(alpha, np.log(np.maximum(Lf, 1e-4) / np.maximum(Lb, 1e-4)), 0)
    det = np.where(alpha, det - np.median(det[alpha]), 0)        # neutral on average: no brightness step where it fades
    details[view] = (det, zb, alpha, s, tx, tz, sole, h, cam)
    reg[view]['hair_px'] = int(hair.sum())
    print('HDSHADE', view, json.dumps(reg[view]), 'detail p5/p95', np.round(np.percentile(det[alpha], [5, 95]), 3))

skinv = np.where(body & (gar == 0))[0]
tree = cKDTree(co[skinv])
for layer in ('UVMap', 'HeadUV'):
    R = np.load(W / f'uvraster_{layer}.npz'); pc, pos = R['piece'], R['pos']
    m = pc == 0
    P3 = pos[m].astype(np.float64)
    dist, idx = tree.query(P3, k=4); w = 1 / np.maximum(dist, 1e-4)
    N = (vn[skinv[idx]] * w[..., None]).sum(1); N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    acc = np.zeros(len(P3)); wsum = np.zeros(len(P3))
    for view, (det, zb, alpha, s, tx, tz, sole, h, cam) in details.items():
        facing = np.clip(N @ cam, 0, 1) ** 2
        u = P3 @ h * s + tx; v = sole - P3[:, 2] * s + tz; dep = P3 @ cam
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (ui >= 0) & (ui < det.shape[1]) & (vi >= 0) & (vi < det.shape[0]) & (facing > 0.05)
        vis = np.zeros(len(P3), bool)
        vis[ok] = (zb[vi[ok], ui[ok]] - dep[ok] < 0.02) & alpha[vi[ok], ui[ok]]
        acc[vis] += facing[vis] * det[vi[vis], ui[vis]]; wsum[vis] += facing[vis]
    val = np.where(wsum > 0.05, acc / np.maximum(wsum, 1e-6), 0) * np.clip(wsum / 0.3, 0, 1)
    # the masters' mane frames the neck, traps and shoulder tops: fade the projection out above the shoulder line
    zt = np.clip((Z_TOP - P3[:, 2]) / 0.06, 0, 1); val *= zt * zt * (3 - 2 * zt)
    out = np.zeros(pc.shape, np.float32); out[m] = val
    np.save(W / f'hdshade_{layer}.npy', out)
    if layer == 'UVMap':
        Image.fromarray((np.clip(out * 1.5 + 0.5, 0, 1) * 255).astype(np.uint8)).save(W / 'hdshade_preview.png')
    print('HDSHADE', layer, 'texels', int(m.sum()), 'seen', int((wsum > 0.05).sum()), 'p5/p95', np.round(np.percentile(val, [5, 95]), 3))
(W / 'hdshade_registration.json').write_text(json.dumps(reg, indent=1) + '\n')
