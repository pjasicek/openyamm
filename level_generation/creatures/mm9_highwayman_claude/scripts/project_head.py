#!/usr/bin/env python3
"""Head sets by projection of the Codex paints made on our own clay (no credits): ortho cameras known exactly (head_clay.py), so each view maps straight onto HeadUV, after a small shift and scale from the alpha silhouette against the clay's.
Per texel: visible views (z-buffer on the head), weight = facing^3 x distance from the view's silhouette; each view is first brought to the tone of the views already placed (low-frequency gain in the overlap). Gaps filled from nearby texels.
Writes textures/hw_head_{t}_raw.png (S), textures/hw_head_{t}_normal.png (1K, from luminance). Args: <tiers> [S]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
tiers = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 1792
Z = np.load('work/head_faces.npz'); CO, NO, UV, PART = Z['co'], Z['nor'], Z['uv'], Z['part']
ORTHO = 0.5
C = np.array([0.0, 0.0058703310787677765, 0.7325705289840698])
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d)      # d: from the target to the camera
    up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return d, r, u
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15)}
ORDER = ['01_front', '03_left', '04_right', '05_top', '02_back']      # no 3/4 views: their features drift against the front (Honk's doubled irises)
# texel raster
pos = np.zeros((S, S, 3), np.float32); nor = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool); prt = np.zeros((S, S), np.uint8)
for t in range(len(CO)):
    u = UV[t]; x = u[:, 0] * S; y = (1 - u[:, 1]) * S
    x0, x1 = int(max(np.floor(x.min()) - 1, 0)), int(min(np.ceil(x.max()) + 1, S - 1)); y0, y1 = int(max(np.floor(y.min()) - 1, 0)), int(min(np.ceil(y.max()) + 1, S - 1))
    if x1 < x0 or y1 < y0: continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
    if abs(d) < 1e-9: continue
    a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
    b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
    g = 1 - a - b
    m = (a >= -0.02) & (b >= -0.02) & (g >= -0.02)
    pos[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * CO[t, 0] + b[..., None] * CO[t, 1] + g[..., None] * CO[t, 2])[m]
    nor[y0:y1 + 1, x0:x1 + 1][m] = (a[..., None] * NO[t, 0] + b[..., None] * NO[t, 1] + g[..., None] * NO[t, 2])[m]
    cov[y0:y1 + 1, x0:x1 + 1][m] = True; prt[y0:y1 + 1, x0:x1 + 1][m] = PART[t]
nor /= np.maximum(np.linalg.norm(nor, axis=2, keepdims=True), 1e-6)
print('COVER', cov.mean())
def zbuffer(d, r, u, R=700):
    """depth along d (bigger = nearer the camera) per pixel of an R x R view"""
    Z_ = np.full((R, R), -1e9, np.float32)
    px = ((CO - C) @ r / ORTHO + 0.5) * R; py = (0.5 - (CO - C) @ u / ORTHO) * R; dz = (CO - C) @ d
    for t in range(len(CO)):
        x, y, z = px[t], py[t], dz[t]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), R - 1)); y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), R - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        det = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(det) < 1e-9: continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / det
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / det
        g = 1 - a - b
        m = (a >= 0) & (b >= 0) & (g >= 0)
        zz = a * z[0] + b * z[1] + g * z[2]
        sub = Z_[y0:y1 + 1, x0:x1 + 1]
        sub[m] = np.maximum(sub[m], zz[m])
    return Z_
Pv = pos[cov]; Nv = nor[cov]
PTv = prt[cov]
FRONT_ONLY = np.where(np.isin(PTv, (2, 20, 22)), np.clip((-Nv[:, 1] + 0.05) / 0.2, 0, 1), 0.0)
FRONT_ONLY = np.maximum(FRONT_ONLY, np.isin(PTv, (2, 20, 22)) * (Pv[:, 1] < 0.0))      # front of the face
views = {}
for name, dv in VIEWS.items():
    d, r, u = cam(dv)
    zb = zbuffer(d, r, u)
    sx = ((Pv - C) @ r / ORTHO + 0.5); sy = (0.5 - (Pv - C) @ u / ORTHO)
    ix = np.clip((sx * 700).astype(int), 0, 699); iy = np.clip((sy * 700).astype(int), 0, 699)
    ZZ = ndimage.maximum_filter(zb, 3)
    vis = (Pv - C) @ d >= ZZ[iy, ix] - 0.006
    face = np.clip(Nv @ d, 0, 1)
    clay = np.asarray(Image.open(f'references_head/clay_{name}.png').convert('RGBA'))[..., 3] > 128
    views[name] = dict(d=d, r=r, u=u, sx=sx, sy=sy, vis=vis, face=face, clay=clay)
def bbox(m):
    ys, xs = np.nonzero(m); return xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
def bilinear(im, x, y):
    h, w = im.shape[:2]
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    im = im.reshape(h, w, -1)
    return im[y0, x0] * (1 - fx) * (1 - fy) + im[y0, x0 + 1] * fx * (1 - fy) + im[y0 + 1, x0] * (1 - fx) * fy + im[y0 + 1, x0 + 1] * fx * fy
# The Codex fronts are not pixel-aligned to the clay: the face sits lower and wider, so a box fit from the silhouette put a second nose, mouth and beard on the geometry (user, 2026-10-31). Features read off the clay and each paint, as image fractions: x centre, half eye spacing, half jaw width; y eyes, nostrils, mouth, chin.
CLAY = dict(cx=0.5, eye=0.0685, jaw=0.13, y=(0.347, 0.429, 0.475, 0.575))
PAINT = {'a': dict(cx=0.4985, eye=0.071, jaw=0.146, y=(0.348, 0.446, 0.492, 0.617)), 'b': dict(cx=0.5095, eye=0.063, jaw=0.1435, y=(0.3725, 0.467, 0.51, 0.621)), 'c': dict(cx=0.5065, eye=0.0645, jaw=0.1375, y=(0.347, 0.433, 0.479, 0.592))}
def front_map(t, sx, sy, bx, by):
    p = PAINT[t]
    cy = np.r_[by[0], CLAY['y'], by[1]]; py = np.r_[by[2], p['y'], by[3]]
    Y = np.interp(sy, cy, py)
    dx = np.abs(sx - CLAY['cx']); kx_ = np.r_[0, CLAY['eye'], CLAY['jaw'], bx[0], 1]; px_ = np.r_[0, p['eye'], p['jaw'], bx[1], 1 + bx[1] - bx[0]]
    X = p['cx'] + np.sign(sx - CLAY['cx']) * np.interp(dx, kx_, px_)
    return X, Y
for t in tiers:
    acc = np.zeros((len(Pv), 3), np.float32); wt = np.zeros(len(Pv), np.float32); rep = {}
    for name in ORDER:
        V = views[name]
        p = Path(f'references_head/{t}_{name}_clean.png')
        if not p.exists(): print('MISSING', p); continue
        im = np.asarray(Image.open(p).convert('RGBA'), np.float32) / 255
        H, W = im.shape[:2]
        al = im[..., 3] > 0.5
        ax0, ax1, ay0, ay1 = bbox(al)
        cl = V['clay']; CH, CW = cl.shape
        bx0, bx1, by0, by1 = bbox(cl)
        # clay fractions -> image pixels, per axis, from the two silhouette boxes
        kx = (ax1 - ax0) / W / ((bx1 - bx0) / CW); ky = (ay1 - ay0) / H / ((by1 - by0) / CH)
        ox = ax0 / W - bx0 / CW * kx; oy = ay0 / H - by0 / CH * ky
        rep[name] = (round(kx, 3), round(ky, 3), round(ox, 3), round(oy, 3))
        ix = (V['sx'] * kx + ox) * W - 0.5; iy = (V['sy'] * ky + oy) * H - 0.5
        if name == '01_front':
            hc = max(0.5 - bx0 / CW, bx1 / CW - 0.5); hp_ = max(PAINT[t]['cx'] - ax0 / W, ax1 / W - PAINT[t]['cx'])
            X_, Y_ = front_map(t, V['sx'], V['sy'], (hc, hp_), (by0 / CH, by1 / CH, ay0 / H, ay1 / H))
            ix = X_ * W - 0.5; iy = Y_ * H - 0.5
        rgb = bilinear(im[..., :3], ix, iy)
        inner = ndimage.distance_transform_edt(al)
        edge = np.clip(bilinear(inner, ix, iy)[:, 0] / (0.012 * W), 0, 1)
        w = (V['face'] ** 3) * edge * V['vis'] * (bilinear(al.astype(np.float32), ix, iy)[:, 0] > 0.9)
        if name != '01_front': w = w * (1 - FRONT_ONLY)           # one source per region: all skin that faces forward, eyes, nose, mouth, beard, comes from the front view alone
        if name in ('06_q34r', '07_q34l'): w = w * 0.8
        if name == '05_top': w = w * (Pv[:, 2] > 0.86)
        # tone: gain per channel in the overlap with what is placed
        ov = (w > 0.15) & (wt > 0.15)
        if ov.sum() > 500:
            g = np.clip((acc[ov] / wt[ov, None]).mean(0) / np.maximum(rgb[ov].mean(0), 1e-3), 0.9, 1.12)
            rgb = rgb * g; rep[name] = rep[name] + tuple(np.round(g, 2).tolist())
        acc += rgb * w[:, None]; wt += w
    print('VIEWS', t, rep, 'unseen', float((wt < 1e-3).mean()))
    col = np.zeros((S, S, 3), np.float32); have = np.zeros((S, S), bool)
    ok = wt > 1e-3
    tmp = np.zeros_like(acc); tmp[ok] = acc[ok] / wt[ok, None]
    # unseen or barely seen texels (under the jaw, behind the hair) take the nearest SEEN point of their own kind in 3D, never a UV neighbour: the headband bled black onto the neck otherwise
    Pp = prt[cov]; lum_ = tmp @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    from scipy.spatial import cKDTree
    rgb_ = tmp
    for kinds, thr in (((2, 20), 0.28), ((21,), 0.0)):
        cl = np.isin(Pp, kinds)
        good = cl & (wt > 0.2) & (lum_ > thr)
        if kinds[0] == 2: good &= (rgb_[:, 0] > rgb_[:, 2] * 1.25) & (rgb_[:, 0] > rgb_[:, 1])     # skin only: not an iris, not an eye white, not the headband
        src = np.where(good)[0]; dst = np.where(cl & (wt <= 0.2))[0]
        if len(src) and len(dst):
            sub = src[:: max(1, len(src) // 60000)]
            d_, nn = cKDTree(Pv[sub]).query(Pv[dst], k=48)
            w_ = 1 / (d_ + 0.004) ** 2; fill = (tmp[sub[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
            k_ = np.clip(wt[dst] / 0.2, 0, 1)[:, None]
            tmp[dst] = tmp[dst] * k_ + fill * (1 - k_); ok[dst] = True
    col[cov] = tmp; have[cov] = ok
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    col = col[idx[0], idx[1]]
    # the neck and the V of the chest: one even skin tone from the paint's own chest, fine detail kept; no dark patches, no beard, no hard edge under the jaw
    Cn = np.array([0.0, -0.03, 0.668]); Nk = np.array([0.0, -0.45, 0.893]); Nk /= np.linalg.norm(Nk)
    hh = (pos - Cn) @ Nk
    ske = cov & np.isin(prt, (2, 20))
    m = ske & (pos[..., 2] > 0.55) & (pos[..., 2] < 0.62) & (pos[..., 1] < -0.04) & (np.abs(pos[..., 0]) < 0.04)
    base = np.median(col[m], axis=0)
    u = np.clip((hh - 0.004) / 0.03, 0, 1); n_ = (1 - u * u * (3 - 2 * u)) * ske
    n_ = ndimage.gaussian_filter(n_.astype(np.float32), 3.0) * ske
    lo = np.stack([ndimage.gaussian_filter(col[..., c], 22) for c in range(3)], -1)
    hp = np.clip(col - lo, -0.06, 0.06) * 0.8
    shade = (0.8 + 0.2 * np.clip((0.665 - pos[..., 2]) / 0.05, 0, 1))[..., None]
    neck = base * shade + hp
    col = col * (1 - n_[..., None]) + neck * n_[..., None]
    # the hair's lower lip beside the neck: the paint has neck and shoulder there, so it read as skin flaps with a dark crescent (user's neck patches). Strands from just above hang down over it, darkening toward the rim
    lip = cov & (prt == 21) & (pos[..., 2] < 0.75) & (pos[..., 1] < 0.08)
    hsrc = cov & (prt == 21) & (pos[..., 2] > 0.70) & (pos[..., 2] < 0.84) & (pos[..., 1] > 0.05) & (col[..., 0] > col[..., 2] * 1.15)      # real strands on the back of the head, unstretched
    lq = np.argwhere(lip); sq = np.argwhere(hsrc)
    sub = sq[:: max(1, len(sq) // 120000)]
    sc_ = np.c_[pos[sub[:, 0], sub[:, 1], 0], pos[sub[:, 0], sub[:, 1], 2]]
    _, nn = cKDTree(sc_).query(np.c_[pos[lq[:, 0], lq[:, 1], 0] * 0.9, pos[lq[:, 0], lq[:, 1], 2] + 0.08])
    zz = pos[lq[:, 0], lq[:, 1], 2]; shade2 = (0.55 + 0.45 * np.clip((zz - 0.66) / 0.08, 0, 1))[:, None]
    fade = np.clip((0.75 - zz) / 0.02, 0, 1)[:, None]
    col[lq[:, 0], lq[:, 1]] = col[lq[:, 0], lq[:, 1]] * (1 - fade) + col[sub[nn, 0], sub[nn, 1]] * shade2 * fade
    Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype('u1')).save(f'textures/hw_head_{t}_raw.png')
    # normal from luminance: fine strand and pore relief only
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ndimage.gaussian_filter(im1k, 6)
    gx = ndimage.sobel(hp, axis=1) * 2.0; gy = ndimage.sobel(hp, axis=0) * 2.0
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(f'textures/hw_head_{t}_normal.png')
    print('HEAD', t, 'done')
