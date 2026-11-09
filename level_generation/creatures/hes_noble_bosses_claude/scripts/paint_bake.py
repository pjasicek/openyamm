#!/usr/bin/env python3
"""Bake the painted masters onto the shell's xatlas UVs (run with work/venv/bin/python).

Every texel's surface point is projected through the exact guide cameras into the registered masters (01-04 ortho,
00 perspective at lower weight); visibility by a depth buffer of the aligned Meshy figure plus the shell; weight =
facing squared. Unseen texels take the nearest seen texel in 3D. Writes textures/<boss>_shell_base.png, a glow mask
(hot orange / violet energy pixels) textures/<boss>_shell_glow.png and a coverage image in work/<boss>/.

Usage: paint_bake.py <boss> [--res 2048] [--glow orange|violet|both]"""
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument('boss'); ap.add_argument('--res', type=int, default=2048)
ap.add_argument('--glow', default='orange')
a = ap.parse_args()
P = Path(__file__).resolve().parents[1]
W = P / 'work' / a.boss
R = a.res
sh = np.load(W / 'shell_tris.npz'); uvd = np.load(W / 'shell_uv.npz'); fg = np.load(W / 'figure_tris.npz')
V, T, N = sh['positions'].astype(np.float64), sh['triangles'], sh['normals'].astype(np.float64)
UV = uvd['uv'].astype(np.float64)                     # M x 3 x 2, v up
cams = json.loads((P / 'references_hd/guides/cameras.json').read_text())['cameras']
reg = json.loads((P / 'references_hd' / a.boss / 'registration.json').read_text())

# ---------------------------------------------------------------- texel rasterisation
tex_pos = np.zeros((R, R, 3)); tex_nrm = np.zeros((R, R, 3)); tex_ok = np.zeros((R, R), bool)
for t in range(len(T)):
    uv = UV[t] * R - 0.5
    uv[:, 1] = (R - 1) - (UV[t][:, 1] * R - 0.5)        # image rows top-down
    x0, y0 = np.floor(uv.min(0)).astype(int); x1, y1 = np.ceil(uv.max(0)).astype(int)
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, R - 1), min(y1, R - 1)
    if x1 < x0 or y1 < y0:
        continue
    yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    p = np.stack([xx.ravel(), yy.ravel()], 1).astype(np.float64)
    a0, b0, c0 = uv
    m = np.array([[b0[0] - a0[0], c0[0] - a0[0]], [b0[1] - a0[1], c0[1] - a0[1]]])
    det = np.linalg.det(m)
    if abs(det) < 1e-12:
        continue
    l12 = np.linalg.solve(m, (p - a0).T).T
    l0 = 1 - l12.sum(1)
    bary = np.stack([l0, l12[:, 0], l12[:, 1]], 1)
    inside = (bary > -0.02).all(1)
    if not inside.any():
        continue
    bary = np.clip(bary[inside], 0, None); bary /= bary.sum(1, keepdims=True)
    px = p[inside].astype(int)
    tex_pos[px[:, 1], px[:, 0]] = bary @ V[T[t]]
    n = bary @ N[T[t]]
    tex_nrm[px[:, 1], px[:, 0]] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
    tex_ok[px[:, 1], px[:, 0]] = True
print('texels', int(tex_ok.sum()))


# ---------------------------------------------------------------- depth buffers per view
def project(pts, cam, size):
    Pm = np.array(cam['projection'])
    h = np.concatenate([pts, np.ones((len(pts), 1))], 1) @ Pm.T
    ndc = h[:, :3] / h[:, 3:4]
    w_, h_ = size
    return np.stack([(ndc[:, 0] * 0.5 + 0.5) * w_, (1 - (ndc[:, 1] * 0.5 + 0.5)) * h_, ndc[:, 2]], 1)


def zbuffer(verts, tris, cam, size):
    w_, h_ = size
    zb = np.full((h_, w_), np.inf)
    s = project(verts, cam, size)
    for t in tris:
        q = s[t]
        x0, y0 = np.floor(q[:, :2].min(0)).astype(int); x1, y1 = np.ceil(q[:, :2].max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, w_ - 1), min(y1, h_ - 1)
        if x1 < x0 or y1 < y0:
            continue
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        pp = np.stack([xx.ravel() + 0.5, yy.ravel() + 0.5], 1)
        a0, b0, c0 = q[:, :2]
        m = np.array([[b0[0] - a0[0], c0[0] - a0[0]], [b0[1] - a0[1], c0[1] - a0[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l12 = np.linalg.solve(m, (pp - a0).T).T
        bary = np.stack([1 - l12.sum(1), l12[:, 0], l12[:, 1]], 1)
        ins = (bary >= -1e-6).all(1)
        if not ins.any():
            continue
        z = bary[ins] @ q[:, 2]
        yi, xi = yy.ravel()[ins], xx.ravel()[ins]
        np.minimum.at(zb, (yi, xi), z)
    return zb


occ_v = np.concatenate([fg['positions'].astype(np.float64), V])
occ_t = np.concatenate([fg['triangles'], T + len(fg['positions'])])
sel = tex_ok
pts = tex_pos[sel]; nrm = tex_nrm[sel]
acc = np.zeros((len(pts), 3)); wsum = np.zeros(len(pts))
views = [('01_front', 1.0), ('02_back', 1.0), ('03_left', 1.0), ('04_right', 1.0), ('00_three_quarter', 0.6)]
for view, vw in views:
    cam = cams[view]; r = reg[view]
    img = np.asarray(Image.open(P / 'references_hd' / a.boss / f'{view}.png').convert('RGBA')).astype(np.float64) / 255
    Hh, Ww = img.shape[:2]
    zb = zbuffer(occ_v, occ_t, cam, (Ww, Hh))
    s = project(pts, cam, (Ww, Hh))
    Mw = np.array(cam['matrix_world'])
    if cam['type'] == 'ORTHO':
        to_cam = np.tile(Mw[:3, 2], (len(pts), 1))
    else:
        to_cam = Mw[:3, 3] - pts
        to_cam /= np.linalg.norm(to_cam, axis=1, keepdims=True)
    facing = np.clip((nrm * to_cam).sum(1), 0, 1)
    xi = np.clip(s[:, 0].astype(int), 0, Ww - 1); yi = np.clip(s[:, 1].astype(int), 0, Hh - 1)
    zt = zb[yi, xi]
    # depth tolerance in NDC: from a 1.5 cm offset along the view direction
    s2 = project(pts + to_cam * 0.015, cam, (Ww, Hh))
    tol = np.abs(s[:, 2] - s2[:, 2])
    visible = s[:, 2] <= zt + tol
    piv = np.array(r['pivot_px'])
    mx = (s[:, 0] - piv[0]) * r['scale'] + piv[0] + r['dx_px']
    my = (s[:, 1] - piv[1]) * r['scale'] + piv[1] + r['dy_px']
    inb = (mx >= 0) & (mx < Ww - 1) & (my >= 0) & (my < Hh - 1)
    mxc = np.clip(mx, 0, Ww - 1.001); myc = np.clip(my, 0, Hh - 1.001)
    x0 = mxc.astype(int); y0 = myc.astype(int); fx = (mxc - x0)[:, None]; fy = (myc - y0)[:, None]
    col = (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy
           + img[y0 + 1, x0 + 1] * fx * fy)
    w = vw * facing ** 2 * visible * inb * (col[:, 3] > 0.6)
    acc += w[:, None] * col[:, :3]; wsum += w
    print(view, 'contributes to', int((w > 0.05).sum()), 'texels')
seen = wsum > 0.03
colour = np.zeros((len(pts), 3))
colour[seen] = acc[seen] / wsum[seen, None]
tree = cKDTree(pts[seen])
_, k = tree.query(pts[~seen], k=4)
colour[~seen] = colour[seen][k].mean(1)
print('seen fraction', round(float(seen.mean()), 3))
img = np.zeros((R, R, 3)); img[sel] = colour
cov = np.zeros((R, R)); cov[sel] = np.clip(wsum, 0, 1)
# gutter dilation
filled = sel.copy()
for _ in range(16):
    grow = ndimage.binary_dilation(filled) & ~filled
    if not grow.any():
        break
    for c in range(3):
        ch = img[..., c]
        s_ = ndimage.uniform_filter(np.where(filled, ch, 0), 3); n_ = ndimage.uniform_filter(filled.astype(float), 3)
        ch[grow] = s_[grow] / np.maximum(n_[grow], 1e-6)
    filled |= grow
# glow mask from the baked colour
mxv = img.max(-1); mnv = img.min(-1); sat = (mxv - mnv) / np.maximum(mxv, 1e-6)
dm = np.maximum(mxv - mnv, 1e-6); r_, g_, b_ = img[..., 0], img[..., 1], img[..., 2]
hue = np.where(mxv == r_, ((g_ - b_) / dm) % 6, np.where(mxv == g_, (b_ - r_) / dm + 2, (r_ - g_) / dm + 4)) * 60
orange = (hue < 42) & (sat > 0.55) & (mxv > 0.78)
violet = (hue > 255) & (hue < 300) & (mxv > 0.7) & (sat > 0.25)
glow = {'orange': orange, 'violet': violet, 'both': orange | violet}[a.glow]
glow = ndimage.gaussian_filter(glow.astype(float), 1.0)
out = P / 'textures'; out.mkdir(exist_ok=True)
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out / f'{a.boss}_shell_base.png')
Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8)).save(out / f'{a.boss}_shell_glow.png')
Image.fromarray((cov * 255).astype(np.uint8)).save(W / 'shell_coverage.png')
print('BAKED', out / f'{a.boss}_shell_base.png', 'glow fraction', round(float((glow > 0.5).sum() / sel.sum()), 4))
