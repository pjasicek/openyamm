#!/usr/bin/env python3
"""Per-tier head base colour: Codex repaints of the tier A head (renders from head_views.py) are registered to those renders
and projected onto the head set (a face differs between tiers, CLAUDE_CREATURE_TEXTURES.md: the one case for a separate base colour).
Views: front, q34, side and their mirrors (the mirrored image from the mirrored camera). Depth test per view on the rest mesh.
Texels outside the views keep tier A, optionally recoloured (--hair-from: the hair luminance mapped to a target's colours).
Usage: head_tier_project.py <tier name> <A head png> <out png> --centre x y z --ortho o [--view-dir v2/tier_heads] [--hair-from <png> ...]"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage, optimize
ap = argparse.ArgumentParser()
ap.add_argument('tier'); ap.add_argument('a_png'); ap.add_argument('out')
ap.add_argument('--centre', nargs=3, type=float, required=True); ap.add_argument('--ortho', type=float, required=True)
ap.add_argument('--npz', default='v2/work/uv_head.npz'); ap.add_argument('--view-dir', default='v2/tier_heads')
ap.add_argument('--hair-grey', action='store_true')
ap.add_argument('--power', type=float, default=5.0)
ap.add_argument('--y-fade', nargs=2, type=float, default=[0.02, 0.07], help='behind this rest y band the repaint fades out')
ap.add_argument('--z-max', nargs=2, type=float, default=None, help='rest z band above which the repaint fades out (the hat stays tier A)')
ap.add_argument('--veil-dark', action='store_true', help='the loose head part reaching furthest back (the veil) becomes dark brown hair by luminance')
ap.add_argument('--no-front', action='store_true')
o = ap.parse_args()
VD = Path(o.view_dir); S = 2048
c = np.array(o.centre); ortho = o.ortho
D = np.load(o.npz)
UV, X, HEAD, HAND = D['uv'], D['xyz'], D['head'].astype(bool), D['hand'].astype(bool)
A = np.asarray(Image.open(o.a_png).convert('RGB'), np.float32)
# texel xyz + normal of head faces
P = np.zeros((S, S, 3), np.float32); N = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool)
for uv, x, h, k in zip(UV, X, HEAD, HAND):
    if not h or k:
        continue
    p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
    lo = np.floor(p.min(0)).astype(int) - 1; hi = np.ceil(p.max(0)).astype(int) + 2
    xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], S)), np.arange(max(lo[1], 0), min(hi[1], S)))
    if not xs.size:
        continue
    q = np.stack([xs + .5, ys + .5], -1)
    T = np.array([p[1] - p[0], p[2] - p[0]]).T
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    st = (q - p[0]) @ np.linalg.inv(T).T
    ins = (st[..., 0] >= -.03) & (st[..., 1] >= -.03) & (st.sum(-1) <= 1.03)
    w = np.stack([1 - st.sum(-1), st[..., 0], st[..., 1]], -1)
    P[ys[ins], xs[ins]] = w[ins] @ x
    n = np.cross(x[1] - x[0], x[2] - x[0]); n /= max(np.linalg.norm(n), 1e-9)
    N[ys[ins], xs[ins]] = n
    cov[ys[ins], xs[ins]] = True
print('texels', int(cov.sum()))
vis_tris = X
def view_axes(deg):
    r = np.radians(deg); Dv = np.array([-np.sin(r), -np.cos(r), 0.0])
    U = np.array([0, 0, 1.0]); R = np.cross(-Dv, U); R /= np.linalg.norm(R)   # camera right
    return Dv, R, U
SZ = 1254
def depth_map(Dv, R, U):
    d = np.full((SZ, SZ), -9.0, np.float32)
    rel = vis_tris - c
    px = (rel @ R / ortho + .5) * SZ; py = (.5 - rel @ U / ortho) * SZ; dep = rel @ Dv
    for a, b, z in zip(px, py, dep):
        lo = np.floor([a.min(), b.min()]).astype(int); hi = np.ceil([a.max(), b.max()]).astype(int) + 1
        if hi[0] < 0 or hi[1] < 0 or lo[0] >= SZ or lo[1] >= SZ:
            continue
        xs, ys = np.meshgrid(np.arange(max(lo[0], 0), min(hi[0], SZ)), np.arange(max(lo[1], 0), min(hi[1], SZ)))
        if not xs.size:
            continue
        T = np.array([[a[1] - a[0], a[2] - a[0]], [b[1] - b[0], b[2] - b[0]]])
        if abs(np.linalg.det(T)) < 1e-9:
            continue
        st = (np.stack([xs + .5 - a[0], ys + .5 - b[0]], -1)) @ np.linalg.inv(T).T
        ins = (st[..., 0] >= 0) & (st[..., 1] >= 0) & (st.sum(-1) <= 1)
        zz = z[0] + st[..., 0] * (z[1] - z[0]) + st[..., 1] * (z[2] - z[0])
        m = ins & (zz > d[ys, xs])
        d[ys[m], xs[m]] = zz[m]
    return d
def load(p):
    return np.asarray(Image.open(p).convert('RGBA').resize((SZ, SZ), Image.LANCZOS), np.float32)
def edges(a):
    g = a[..., :3].mean(-1) * (a[..., 3] > 128)
    g = ndimage.gaussian_filter(g, 2)
    return np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1))
def warp(img, p, order=1):
    s, tx, ty = p
    cen = SZ / 2
    M = np.eye(2) / s
    off = np.array([cen, cen]) - M @ np.array([cen + ty, cen + tx])
    return np.stack([ndimage.affine_transform(img[..., k], M, off, order=order, mode='nearest') for k in range(img.shape[-1])], -1)
def register(src, tgt):
    """Scale and shift taking tgt onto src: alpha boxes first, then edge correlation."""
    def box(a):
        ys, xs = np.nonzero(a[..., 3] > 128)
        ys2 = ys[ys < SZ * .62]; xs2 = xs[ys < SZ * .62]
        return ys2.min(), xs2.min(), xs2.max()
    t0, l0, r0 = box(src); t1, l1, r1 = box(tgt)
    s = (r0 - l0) / max(r1 - l1, 1)
    # after the scale about the centre, the top must match
    p0 = np.array([s, (l0 + r0) / 2 - SZ / 2 - s * ((l1 + r1) / 2 - SZ / 2), t0 - SZ / 2 - s * (t1 - SZ / 2)])
    es = edges(src); et = edges(tgt)
    sm = 0.25
    es4 = ndimage.zoom(es, sm, order=1); et_ = et
    def f(p):
        w = warp(et_[..., None], p, 1)[..., 0]
        w4 = ndimage.zoom(w, sm, order=1)
        r = np.corrcoef(es4.ravel(), w4.ravel())[0, 1]
        return -r
    r = optimize.minimize(f, p0, method='Powell', options={'xtol': .2, 'ftol': 1e-4, 'maxiter': 8, 'direc': np.diag([.01, 4, 4])})
    print('  register', np.round(p0, 3), '->', np.round(r.x, 3), 'ncc', round(-f(p0), 3), round(-r.fun, 3))
    return r.x
def flow(src, img, step=36, patch=20, rng=14):
    """Local displacement of a repaint against the render: block matching on edge maps at half size, smoothed (image paint moves
    features by a few pixels; a similarity alone leaves double eyes where views meet)."""
    a = ndimage.zoom(edges(src), .5, order=1); b = ndimage.zoom(edges(img), .5, order=1)
    H, W = a.shape
    pts, dsp, wts = [], [], []
    ys, xs = np.nonzero(ndimage.zoom((src[..., 3] > 128).astype(np.float32), .5, order=0) > .5)
    y0, y1, x0, x1 = ys.min(), int(ys.min() + 0.68 * (ys.max() - ys.min())), xs.min(), xs.max()
    for y in range(y0, y1, step // 2):
        for x in range(x0, x1, step // 2):
            if y - patch - rng < 0 or y + patch + rng >= H or x - patch - rng < 0 or x + patch + rng >= W:
                continue
            P = a[y - patch:y + patch, x - patch:x + patch]
            if P.std() < 1.0:
                continue
            P = (P - P.mean()) / P.std()
            best, bd = -1, (0, 0)
            for dy in range(-rng, rng + 1):
                for dx in range(-rng, rng + 1):
                    Q = b[y + dy - patch:y + dy + patch, x + dx - patch:x + dx + patch]
                    s = Q.std()
                    if s < 1e-3:
                        continue
                    r = (P * (Q - Q.mean())).mean() / s
                    if r > best:
                        best, bd = r, (dy, dx)
            if best > 0.45:
                pts.append((y, x)); dsp.append(bd); wts.append(best)
    pts = np.array(pts, float); dsp = np.array(dsp, float); wts = np.array(wts)
    print('  flow matches', len(pts), 'mean |d| px', round(float(np.linalg.norm(dsp, axis=1).mean() * 2), 1), 'max', round(float(np.linalg.norm(dsp, axis=1).max() * 2), 1))
    # robust smooth field: Gaussian weighted median-ish (two passes of weighted mean with outlier rejection)
    gy, gx = np.mgrid[0:SZ:8, 0:SZ:8] / 2.0
    F = np.zeros(gy.shape + (2,), np.float32)
    sigma = 40.0
    keep = np.ones(len(pts), bool)
    for _ in range(2):
        for i in range(gy.shape[0]):
            for j in range(gy.shape[1]):
                d2 = ((pts[keep] - (gy[i, j], gx[i, j])) ** 2).sum(1)
                w = wts[keep] * np.exp(-d2 / (2 * sigma * sigma)) + 1e-9
                F[i, j] = (dsp[keep] * w[:, None]).sum(0) / (w.sum() + 0.3)
        Fi = np.stack([ndimage.map_coordinates(F[..., k], [pts[:, 0] / 4, pts[:, 1] / 4], order=1) for k in range(2)], 1)
        keep = np.linalg.norm(dsp - Fi, axis=1) < 5
    F = ndimage.gaussian_filter(F, (2, 2, 0)) * 2
    Fu = ndimage.zoom(F, (8, 8, 1), order=1)[:SZ, :SZ]
    yy, xx = np.mgrid[0:SZ, 0:SZ].astype(np.float32)
    return np.stack([ndimage.map_coordinates(img[..., k], [yy + Fu[..., 0], xx + Fu[..., 1]], order=1, mode='nearest') for k in range(img.shape[-1])], -1)


VIEWS = (('front', 0, False), ('q34', 40, False), ('side', 90, False), ('q34', -40, True), ('side', -90, True))
if o.no_front:
    VIEWS = VIEWS[1:]
acc = np.zeros((S, S, 3), np.float32); wsum = np.zeros((S, S), np.float32)
vis_any = cov.copy()
report = {}; flows = {}
for name, deg, mir in VIEWS:
    src = load(VD / f'{name}.png'); tgt = load(VD / f'{o.tier}_{name}.png')
    print(name, deg)
    p = register(src, tgt) if not mir else report[name]
    report[name] = p
    if mir:
        img = flows[name][:, ::-1]
    else:
        img = flow(src, warp(tgt, p))
        flows[name] = img
    Dv, R, U = view_axes(deg)
    dm = depth_map(Dv, R, U)
    rel = P - c
    px = (rel @ R / ortho + .5) * SZ; py = (.5 - rel @ U / ortho) * SZ; dep = rel @ Dv
    ix = np.clip(px.astype(int), 0, SZ - 1); iy = np.clip(py.astype(int), 0, SZ - 1)
    vis = cov & (dep > dm[iy, ix] - 0.006)
    w = np.clip(N @ Dv, 0, 1) ** o.power * vis
    col = np.stack([ndimage.map_coordinates(img[..., k], [py - .5, px - .5], order=1, mode='nearest') for k in range(3)], -1)
    alpha = ndimage.map_coordinates(img[..., 3], [py - .5, px - .5], order=1, mode='nearest') / 255
    w = w * np.clip((alpha - .5) * 2, 0, 1)
    acc += col * w[..., None]; wsum += w
proj = acc / np.maximum(wsum, 1e-4)[..., None]
m = np.clip(wsum / 0.25, 0, 1)
m = m * m * (3 - 2 * m)
y0, y1 = o.y_fade
fade = 1 - np.clip((P[..., 1] - y0) / (y1 - y0), 0, 1)
m = m * fade * cov
if o.z_max:
    m = m * (1 - np.clip((P[..., 2] - o.z_max[0]) / (o.z_max[1] - o.z_max[0]), 0, 1))
base = A.copy()
if o.hair_grey:
    # tier A hair (everything but skin) mapped by luminance to a silver grey, the repaint's own hair sets the level
    lum = base @ np.array([.299, .587, .114])
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    skin = (r > 120) & (g > 70) & (lum > 110)
    hair = cov & ~skin
    ref = proj[(m > .9) & hair]
    lo, hi = np.percentile(lum[hair], 2), np.percentile(lum[hair], 98)
    t = np.clip((lum - lo) / (hi - lo), 0, 1)[..., None]
    grey = np.array([120, 116, 108.]) * (1 - t) + np.array([225, 220, 208.]) * t
    base[hair] = grey[hair]
if o.veil_dark:
    comps = D['comp'][HEAD & ~HAND]; xy = X[HEAD & ~HAND]
    vc = comps[np.argmax(xy[:, :, 1].max(1))]
    print('veil comp', vc)
    vm = np.zeros((S, S), bool)
    for uv in UV[(D['comp'] == vc) & HEAD]:
        p = uv * S; p = np.stack([p[:, 0], S - p[:, 1]], 1)
        from PIL import ImageDraw
        pass
    im = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(im)
    for uv in UV[(D['comp'] == vc) & HEAD]:
        dr.polygon([(u * S, (1 - v) * S) for u, v in uv], fill=255)
    vm = ndimage.binary_dilation(np.asarray(im) > 0, iterations=2)
    lum = base @ np.array([.299, .587, .114])
    lo, hi = np.percentile(lum[vm & cov], 5), np.percentile(lum[vm & cov], 98)
    t = np.clip((lum - lo) / (hi - lo), 0, 1)[..., None]
    brown = np.array([40, 27, 21.]) * (1 - t) + np.array([96, 70, 52.]) * t
    base[vm] = brown[vm]
out = base * (1 - m[..., None]) + proj * m[..., None]
# gutters: nearest covered texel inside the head islands
need = ~cov
idx = ndimage.distance_transform_edt(need, return_distances=False, return_indices=True)
near = ndimage.binary_dilation(cov, iterations=14) & need
out[near] = out[idx[0][near], idx[1][near]]
Image.fromarray(np.uint8(np.clip(out, 0, 255))).save(o.out)
print('TIERHEAD', o.tier, 'texels replaced', int((m > .5).sum()))
