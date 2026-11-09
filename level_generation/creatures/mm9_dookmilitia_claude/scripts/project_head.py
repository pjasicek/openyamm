#!/usr/bin/env python3
"""Head sets by projection of the Codex paints made on our own clay (no credits): ortho cameras known exactly (head_clay.py), so each view maps straight onto HeadUV, after a small shift and scale from the alpha silhouette against the clay's.
Per texel: visible views (z-buffer on the head), weight = facing^3 x distance from the view's silhouette; each view is first brought to the tone of the views already placed (low-frequency gain in the overlap). Gaps filled from nearby texels.
Writes textures/dook_head_{t}_raw.png (S), textures/dook_head_{t}_normal.png (1K, from luminance). Args: <tiers> [S]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
tiers = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 1792
Z = np.load('work/head_faces.npz'); CO, NO, UV, PART = Z['co'], Z['nor'], Z['uv'], Z['part']
ORTHO = 0.5
C = np.array([0.0, 0.01788879930973053, 0.7927634119987488])
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d)      # d: from the target to the camera
    up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return d, r, u
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15)}
ORDER = ['01_front', '03_left', '04_right', '05_top', '02_back']      # no 3/4 views: their features drift against the front (Honk's doubled irises)
# texel raster
pos = np.zeros((S, S, 3), np.float32); nor = np.zeros((S, S, 3), np.float32); cov = np.zeros((S, S), bool); prt = np.zeros((S, S), np.uint8); tid = np.zeros((S, S), np.int32)
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
    cov[y0:y1 + 1, x0:x1 + 1][m] = True; prt[y0:y1 + 1, x0:x1 + 1][m] = PART[t]; tid[y0:y1 + 1, x0:x1 + 1][m] = t
nor /= np.maximum(np.linalg.norm(nor, axis=2, keepdims=True), 1e-6)
print('COVER', cov.mean())
# the cheek bars are their own layer: thin plates standing off the cheek, on which a side view drifted (skin and strap side by side on the right bar, tiers A and C). Connected pieces of part 21 by shared position
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
q = np.nonzero(PART == 21)[0]; kp = np.round(CO[q].reshape(-1, 3), 4); _, inv = np.unique(kp, axis=0, return_inverse=True); inv = inv.ravel().reshape(-1, 3)
adj = coo_matrix((np.ones(len(inv) * 2), (np.r_[inv[:, 0], inv[:, 1]], np.r_[inv[:, 1], inv[:, 2]])), shape=(inv.max() + 1, inv.max() + 1))
nc, lab = connected_components(adj, directed=False); tl = lab[inv[:, 0]]
BAR = {}
for l in range(nc):
    t_ = q[tl == l]; c_ = CO[t_].reshape(-1, 3)
    if len(t_) < 60 and np.ptp(c_[:, 2]) > 0.12 and 0.07 < abs(c_[:, 0].mean()) < 0.14: BAR['L' if c_[:, 0].mean() > 0 else 'R'] = t_
print('BARS', {k: len(v) for k, v in BAR.items()})
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
FACE = np.clip((0.078 - np.abs(Pv[:, 0])) / 0.02, 0, 1) * np.clip((-0.055 - Pv[:, 1]) / 0.02, 0, 1) * np.clip((Pv[:, 2] - 0.67) / 0.02, 0, 1)      # front of the face
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
        rgb = bilinear(im[..., :3], ix, iy)
        inner = ndimage.distance_transform_edt(al)
        edge = np.clip(bilinear(inner, ix, iy)[:, 0] / (0.012 * W), 0, 1)
        w = (V['face'] ** 3) * edge * V['vis'] * (bilinear(al.astype(np.float32), ix, iy)[:, 0] > 0.9)
        if name != '01_front': w = w * (1 - FACE)                 # eyes, nose, mouth come from the front view alone
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
    # the fill under the jaw has colour but no pores: band-passed noise, fading out where a view has seen the skin (a tiled patch of real cheek brought its wrinkles and seams along)
    fillm = np.isin(Pp, (2, 20)) & (wt <= 0.2)
    rng = np.random.RandomState(5); nz = rng.randn(S, S).astype(np.float32); nz = ndimage.gaussian_filter(nz, 1.0) - ndimage.gaussian_filter(nz, 3.0); nz /= nz.std()
    k2 = 1 - np.clip(wt[fillm] / 0.2, 0, 1)
    tmp[fillm] = tmp[fillm] * (1 + nz[cov][fillm] * 0.07 * k2)[:, None]
    # each layer from its good side, per texel by position and normal. Left bar onto the right bar; the left cheek, jaw and ear onto the right: the right side view had drifted, its strap lay on the cheek behind the bar and its bar on the skin (the Guard's fault). The middle of the face keeps the front view
    Tv = tid[cov]; barL = np.isin(Tv, BAR['L']); barR = np.isin(Tv, BAR['R'])
    def key(P_, N_): return np.c_[P_, N_ * 0.03]
    mir = np.array([-1.0, 1.0, 1.0], np.float32)
    _, nn = cKDTree(key(Pv[barL], Nv[barL])).query(key(Pv[barR] * mir, Nv[barR] * mir))
    tmp[barR] = tmp[barL][nn]; ok[barR] = True
    skin = np.isin(Pp, (2, 20)); skL = skin & (Pv[:, 0] > 0.055); skR = np.where(skin & (Pv[:, 0] < -0.055))[0]
    _, nn = cKDTree(key(Pv[skL], Nv[skL])).query(key(Pv[skR] * mir, Nv[skR] * mir))
    ramp = np.clip((-Pv[skR, 0] - 0.055) / 0.03, 0, 1); ramp = (ramp * ramp * (3 - 2 * ramp))[:, None]
    tmp[skR] = tmp[skR] * (1 - ramp) + tmp[skL][nn] * ramp; ok[skR] = True
    print('MIRROR bars', int(barR.sum()), 'skin', len(skR))
    col[cov] = tmp; have[cov] = ok
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    col = col[idx[0], idx[1]]
    Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype('u1')).save(f'textures/dook_head_{t}_raw.png')
    # normal from luminance: fine strand and pore relief only
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ndimage.gaussian_filter(im1k, 6)
    gx = ndimage.sobel(hp, axis=1) * 2.0; gy = ndimage.sobel(hp, axis=0) * 2.0
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(f'textures/dook_head_{t}_normal.png')
    print('HEAD', t, 'done')
