#!/usr/bin/env python3
"""Mirror-symmetric paint for a set whose mesh is exactly mirror-symmetric (assemble_pf.py mirrors every shell): each texel of a face on the
dropped side takes the colour of the same barycentric point on its mirror partner face. Meshy paints the two halves from different views, so
the midline seam showed as a light nose strip and a dark line down the lip and chin. Faces crossing the midline keep their own paint.
Args: <uv npz> <material index> <in png> <out png> [keep: +x|-x, raw ABC side]"""
import sys
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
UVN, MAT, SRC, DST = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]; KEEP = sys.argv[5] if len(sys.argv) > 5 else '+x'
D = np.load(UVN); co, tri, uv, mat = D['co'], D['tri'], D['uv'], D['mat']
F = np.where(mat == MAT)[0]; T = tri[F]; C = co[T].mean(1)
src = np.asarray(Image.open(SRC).convert('RGB'), np.float32); H, W = src.shape[:2]; out = src.copy()
sgn = 1 if KEEP == '+x' else -1
# partner faces: the face whose mirrored centroid matches, vertex order matched by mirrored position
kd = cKDTree(C * [-1, 1, 1]); d, part = kd.query(C)
moved = 0; skipped = 0; written = np.zeros((H, W), bool)
for i, f in enumerate(F):
    if C[i, 0] * sgn > -1e-4:            # kept side (or on the midline)
        continue
    j = part[i]
    if d[i] > 2e-3: skipped += 1; continue
    tv = T[i]; pv = T[j]
    # match each target vertex to the partner vertex at its mirrored position
    m = [int(np.argmin(np.linalg.norm(co[pv] - co[v] * [-1, 1, 1], axis=1))) for v in tv]
    pu = uv[pv[m]]; tu = uv[tv]
    px = np.c_[tu[:, 0] * W, (1 - tu[:, 1]) * H]; qx = np.c_[pu[:, 0] * W, (1 - pu[:, 1]) * H]
    x0, y0 = np.floor(px.min(0)).astype(int) - 1; x1, y1 = np.ceil(px.max(0)).astype(int) + 1
    xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, W)), np.arange(max(y0, 0), min(y1, H)))
    P = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    a, b, c = px; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
    if abs(den) < 1e-9: continue
    w1 = ((P[:, 0] - a[0]) * v1[1] - v1[0] * (P[:, 1] - a[1])) / den; w2 = (v0[0] * (P[:, 1] - a[1]) - (P[:, 0] - a[0]) * v0[1]) / den; w0 = 1 - w1 - w2
    k = (w0 > -0.02) & (w1 > -0.02) & (w2 > -0.02)
    if not k.any(): continue
    Q = w0[k, None] * qx[0] + w1[k, None] * qx[1] + w2[k, None] * qx[2]
    # bilinear sample of the source at Q
    qx_, qy_ = np.clip(Q[:, 0] - 0.5, 0, W - 1.001), np.clip(Q[:, 1] - 0.5, 0, H - 1.001); ix, iy = qx_.astype(int), qy_.astype(int); fx, fy = (qx_ - ix)[:, None], (qy_ - iy)[:, None]
    s = src[iy, ix] * (1 - fx) * (1 - fy) + src[iy, ix + 1] * fx * (1 - fy) + src[iy + 1, ix] * (1 - fx) * fy + src[iy + 1, ix + 1] * fx * fy
    yy, xx = P[k, 1].astype(int), P[k, 0].astype(int)
    out[yy, xx] = s; written[yy, xx] = True; moved += 1
# gutters next to rewritten charts: pad from the rewritten texels outward by 4 px
from PIL import ImageDraw
cv = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cv)
for t in T: dr.polygon([(float(uv[v, 0] * W), float((1 - uv[v, 1]) * H)) for v in t], fill=255)
cov = np.asarray(cv) > 0
near = ndimage.binary_dilation(written, iterations=4) & ~written & ~cov          # only the empty gutters
idx = ndimage.distance_transform_edt(~written, return_distances=False, return_indices=True)
out[near] = out[idx[0], idx[1]][near]
Image.fromarray(np.clip(out, 0, 255).astype('u1')).save(DST)
print('SYM', SRC, 'faces mirrored', moved, 'skipped', skipped, 'of', len(F))
# ---- the midline band: texels within BAND of x = 0 take the colour 1.5 x BAND off the midline (Meshy darkens a seam's own texels)
BAND = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
if BAND > 0:
    out2 = np.asarray(Image.open(DST).convert('RGB'), np.float32).copy()
    TX = []; TP = []
    for f in F:
        tv = tri[f]; tu = uv[tv]; px = np.c_[tu[:, 0] * W, (1 - tu[:, 1]) * H]
        x0, y0 = np.floor(px.min(0)).astype(int); x1, y1 = np.ceil(px.max(0)).astype(int) + 1
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, W)), np.arange(max(y0, 0), min(y1, H)))
        P = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]; a, b, c = px; v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12: continue
        w1 = ((P[:, 0] - a[0]) * v1[1] - v1[0] * (P[:, 1] - a[1])) / den; w2 = (v0[0] * (P[:, 1] - a[1]) - (P[:, 0] - a[0]) * v0[1]) / den; w0 = 1 - w1 - w2
        k = (w0 > -0.01) & (w1 > -0.01) & (w2 > -0.01)
        if not k.any(): continue
        X = w0[k, None] * co[tv[0]] + w1[k, None] * co[tv[1]] + w2[k, None] * co[tv[2]]
        TX.append(P[k].astype(int)); TP.append(X)
    TX = np.vstack(TX); TP = np.vstack(TP)
    band = np.abs(TP[:, 0]) < BAND; far = np.abs(TP[:, 0]) >= 1.5 * BAND
    kd2 = cKDTree(TP[far])
    tgt = TP[band].copy(); tgt[:, 0] = np.where(tgt[:, 0] >= 0, 1.5 * BAND, -1.5 * BAND)
    _, nn = kd2.query(tgt)
    src_px = TX[far][nn]; dst_px = TX[band]
    out2[dst_px[:, 1], dst_px[:, 0]] = out2[src_px[:, 1], src_px[:, 0]]
    Image.fromarray(np.clip(out2, 0, 255).astype('u1')).save(DST)
    print('BAND', int(band.sum()), 'texels replaced')
