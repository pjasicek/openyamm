#!/usr/bin/env python3
"""Head sets by projection of the Codex paints made on our own clay (no credits): ortho cameras known exactly (head_clay.py), so each view maps straight onto HeadUV, after a small shift and scale from the alpha silhouette against the clay's.
Per texel: visible views (z-buffer on the head), weight = facing^3 x distance from the view's silhouette; each view is first brought to the tone of the views already placed (low-frequency gain in the overlap). Gaps filled from nearby texels.
Writes textures/nb_head_{t}_raw.png (S), textures/nb_head_{t}_normal.png (1K, from luminance). Args: <tiers> [S]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
tiers = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 1792
Z = np.load('work/head_faces.npz'); CO, NO, UV, PART = Z['co'], Z['nor'], Z['uv'], Z['part']
ORTHO = 0.5
C = np.array([0.0, 0.04263773187994957, 0.7820000052452087])
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d)      # d: from the target to the camera
    up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return d, r, u
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15)}
# Silhouette boxes shifted the Codex features up to 2.9 cm off the mesh (double noses, beards on the neck; user 2026-10-31, as the Gezzampt). The front view is placed by measured landmarks, full-size pixels, clay -> paint:
# eyes, nose wings, nose base, mouth corners, mouth centre, chin, jaw sides, neck. A thin-plate warp of the box mapping's error, zero at the hairline and in the hair. Viscount's mouth corners go wider on the clay: his smile is wider than the closed mesh mouth.
from scipy.interpolate import RBFInterpolator
CLAY = [(560, 497), (693, 497), (595, 600), (660, 600), (627, 618), (585, 672), (670, 672), (627, 668), (627, 785), (520, 760), (735, 760), (627, 900)]
LM = {'a': [(547, 477), (717, 477), (595, 605), (673, 605), (633, 623), (570, 683), (693, 685), (632, 685), (635, 838), (510, 790), (760, 790), (635, 950)],
      'b': [(563, 583), (715, 583), (605, 692), (680, 692), (642, 712), (550, 760), (730, 758), (640, 772), (645, 937), (505, 870), (785, 870), (645, 1050)],
      'c': [(555, 537), (705, 537), (595, 640), (672, 640), (635, 665), (572, 723), (690, 723), (632, 720), (630, 862), (500, 810), (762, 810), (630, 975)]}
BMOUTH = [(567, 672), (687, 672)]
ANCHOR = [(627, 395), (545, 420), (710, 420), (430, 480), (825, 480), (415, 640), (840, 640), (405, 720), (850, 720)]
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
FACE = np.clip((0.098 - np.abs(Pv[:, 0])) / 0.02, 0, 1) * np.clip((-0.005 - Pv[:, 1]) / 0.02, 0, 1) * np.clip((Pv[:, 2] - 0.70) / 0.02, 0, 1)      # front of the face
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
        if name == '01_front':
            cl_ = list(CLAY)
            if t == 'b': cl_[5:7] = BMOUTH
            src = np.array(cl_ + ANCHOR, float); dst = np.array(LM[t], float)
            boxed = np.c_[(src[:len(dst), 0] / CW * kx + ox) * W, (src[:len(dst), 1] / CH * ky + oy) * H]
            err = np.r_[dst - boxed, np.zeros((len(ANCHOR), 2))]
            print('LANDMARK', t, 'box error px at chin', np.round(err[8], 0), 'eyes', np.round(err[0], 0))
            f = RBFInterpolator(src, err, kernel='thin_plate_spline', smoothing=1.0)
            q = np.c_[V['sx'] * CW, V['sy'] * CH]; dd = np.vstack([f(q[i:i + 200000]) for i in range(0, len(q), 200000)])
            ix = ix + dd[:, 0]; iy = iy + dd[:, 1]
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
    cl = Pp >= 20
    good = cl & (wt > 0.2)                     # one skin with the hair: the nearest seen point in 3D, whichever it is
    src = np.where(good)[0]; dst = np.where(cl & (wt <= 0.2))[0]
    if len(src) and len(dst):
        sub = src[:: max(1, len(src) // 60000)]
        d_, nn = cKDTree(Pv[sub]).query(Pv[dst], k=12)
        w_ = 1 / (d_ + 0.004) ** 2; fill = (tmp[sub[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
        k_ = np.clip(wt[dst] / 0.2, 0, 1)[:, None]
        tmp[dst] = tmp[dst] * k_ + fill * (1 - k_); ok[dst] = True
    # the beard ends at the jaw edge: under it, plain neck skin from the paint's own neck, a touch darker just under the jaw
    im = np.asarray(Image.open(f'references_head/{t}_01_front_clean.png').convert('RGB'), np.float32) / 255
    cx_, cy_ = LM[t][11]; skin = np.median(im[cy_ - 25:cy_ + 25, cx_ - 40:cx_ + 40].reshape(-1, 3), 0)
    below = np.where(Pv[:, 1] < 0.03, 0.725 + 0.55 * (Pv[:, 1] + 0.085), 0.74) - Pv[:, 2]     # the jaw edge, then level under the hair's rim at the back
    rn = np.hypot(Pv[:, 0] / 0.085, (Pv[:, 1] - 0.052) / 0.10); tube = np.clip((1.0 - rn) / 0.1, 0, 1); tube = tube * tube * (3 - 2 * tube)      # the neck itself: the hair beside it stays hair
    u_ = np.clip(below / 0.006, 0, 1); u_ = u_ * u_ * (3 - 2 * u_); u_ = u_ * tube
    shade = 0.84 + 0.16 * np.clip(below / 0.04, 0, 1)
    tmp = tmp * (1 - u_[:, None]) + (skin[None] * shade[:, None]) * u_[:, None]; ok = ok | (u_ > 0)
    print('NECK', t, 'skin', np.round(skin * 255), 'texels', int((u_ > 0.5).sum()))
    col[cov] = tmp; have[cov] = ok
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    col = col[idx[0], idx[1]]
    Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype('u1')).save(f'textures/nb_head_{t}_raw.png')
    # normal from luminance: fine strand and pore relief only
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ndimage.gaussian_filter(im1k, 6)
    gx = ndimage.sobel(hp, axis=1) * 2.0; gy = ndimage.sobel(hp, axis=0) * 2.0
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(f'textures/nb_head_{t}_normal.png')
    print('HEAD', t, 'done')
