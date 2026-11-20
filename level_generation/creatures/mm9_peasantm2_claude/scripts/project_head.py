#!/usr/bin/env python3
"""Njam (from mm9_nobleman_claude/scripts/project_head.py, one tier `a`; landmarks, head centre and jaw/neck lines measured on
Njam's clay and paint; textures/nj_head_a_raw.png). The z-buffer covers both head layers (face skin and hair helmet), so no view paints
through the helmet onto the face or the reverse.
Head sets by projection of the Codex paints made on our own clay (no credits): ortho cameras known exactly (head_clay.py), so each view maps straight onto HeadUV, after a small shift and scale from the alpha silhouette against the clay's.
Per texel: visible views (z-buffer on the head), weight = facing^3 x distance from the view's silhouette; each view is first brought to the tone of the views already placed (low-frequency gain in the overlap). Gaps filled from nearby texels.
Writes textures/nj_head_{t}_raw.png (S), textures/nj_head_{t}_normal.png (1K, from luminance). Args: <tiers> [S]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, 'scripts')
tiers = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 1792
Z = np.load('work/head_faces.npz'); CO, NO, UV, PART = Z['co'], Z['nor'], Z['uv'], Z['part']
ORTHO = 0.5
C = np.array([8.275359869003296e-05, 0.06300007551908493, 0.7860000133514404])   # head_clay.py's centre after the head pass
FACE_C = np.array([0.0, 0.0, 0.808]); FACE_ORTHO = 0.24      # the close face view (08_face): the face's only paint source
VC = lambda name: (FACE_C, FACE_ORTHO) if name == '08_face' else (C, ORTHO)
def cam(d):
    d = np.array(d, float); d /= np.linalg.norm(d)      # d: from the target to the camera
    up = np.array([0, 0, 1.0])
    if abs(d @ up) > 0.99: up = np.array([0, 1.0, 0])
    r = np.cross(up, d); r /= np.linalg.norm(r); u = np.cross(d, r)
    return d, r, u
VIEWS = {'01_front': (0, -1, 0), '03_left': (1, 0, 0), '02_back': (0, 1, 0), '04_right': (-1, 0, 0), '05_top': (0, 0.0001, 1), '06_q34r': (-1, -1.2, 0.15), '07_q34l': (1, -1.2, 0.15), '08_face': (0, -1, 0)}
# Silhouette boxes shifted the Codex features up to 2.9 cm off the mesh (double noses, beards on the neck; user 2026-10-31, as the Gezzampt). The front view is placed by measured landmarks, full-size pixels, clay -> paint:
# eyes, nose wings, nose base, mouth corners, mouth centre, chin, jaw sides, neck. A thin-plate warp of the box mapping's error, zero at the hairline and in the hair. Viscount's mouth corners go wider on the clay: his smile is wider than the closed mesh mouth.
from scipy.interpolate import RBFInterpolator
# landmarks on the close face view 08_face (1254 px, ortho 0.24): clay positions from the mesh (eye caps, the mid-face profile) and
# the clay render; paint positions read on a_08_face. Pairs: eyes, nose wings, nose base, mouth corners, mouth centre, chin, jaw sides,
# neck, fringe edge (3). The smirk is kept: the paint's corners move with the mouth centre, scaled to the clay's mouth width.
CLAY = [(496, 425), (758, 425), (575, 650), (680, 650), (627, 660), (510, 780), (744, 737), (627, 775), (627, 1000), (400, 950), (855, 950), (627, 1150), (500, 305), (627, 300), (750, 305)]
LM = {'a': [(490, 457), (778, 455), (575, 670), (705, 670), (640, 685), (505, 795), (795, 752), (650, 790), (640, 1010), (405, 950), (890, 950), (627, 1150), (500, 355), (627, 350), (750, 355)]}
BMOUTH = []
ANCHOR = [(627, 120), (300, 450), (954, 450), (290, 700), (964, 700)]
NECKPT = (627, 1170)                    # plain neck skin in a_08_face below the chin (the neck tone sample: the face's own tone)
ORDER = ['08_face', '01_front', '06_q34r', '07_q34l', '03_left', '04_right', '05_top', '02_back']   # head pass: the 3/4 views paint the cheek sides and the side locks only (features stay with 08_face)      # no 3/4 views: their features drift against the front (Honk's doubled irises)
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
def zbuffer(d, r, u, R=700, C=C, ORTHO=ORTHO):
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
FACE = np.clip((0.135 - np.abs(Pv[:, 0])) / 0.02, 0, 1) * np.clip((0.06 - Pv[:, 1]) / 0.02, 0, 1) * np.clip((Pv[:, 2] - 0.715) / 0.02, 0, 1) * np.clip((0.915 - Pv[:, 2]) / 0.02, 0, 1)      # the face out to the cheeks and jaw, inside the close view's frame (head pass: the side views drew their own profile's eye and jaw on the cheeks)
views = {}
for name, dv in VIEWS.items():
    d, r, u = cam(dv)
    Cv, Ov = VC(name)
    zb = zbuffer(d, r, u, C=Cv, ORTHO=Ov)
    sx = ((Pv - Cv) @ r / Ov + 0.5); sy = (0.5 - (Pv - Cv) @ u / Ov)
    ix = np.clip((sx * 700).astype(int), 0, 699); iy = np.clip((sy * 700).astype(int), 0, 699)
    ZZ = ndimage.maximum_filter(zb, 3)
    vis = (Pv - Cv) @ d >= ZZ[iy, ix] - 0.006
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
        if name == '08_face': kx = ky = 1.0; ox = oy = 0.0        # the close view crops the head: no silhouette box, the landmarks place it
        rep[name] = (round(kx, 3), round(ky, 3), round(ox, 3), round(oy, 3))
        ix = (V['sx'] * kx + ox) * W - 0.5; iy = (V['sy'] * ky + oy) * H - 0.5
        if name == '08_face':
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
        # hair texels never take skin-coloured paint (a paint's face reached past our hair's front edge: a pale strip on the hair beside
        # each cheek); skin = light, warm, moderately saturated
        lum_ = rgb @ np.array([0.2126, 0.7152, 0.0722]); mx_ = rgb.max(1); sat_ = (mx_ - rgb.min(1)) / np.maximum(mx_, 1e-4)
        skinlike = (lum_ > 0.42) & (sat_ > 0.18) & (sat_ < 0.62) & (rgb[:, 0] > rgb[:, 2] * 1.15)
        hue_ = np.degrees(np.arctan2(np.sqrt(3) * (rgb[:, 1] - rgb[:, 2]), 2 * rgb[:, 0] - rgb[:, 1] - rgb[:, 2])) % 360
        hairlike = (lum_ < 0.34) & (sat_ > 0.35) & (hue_ > 12) & (hue_ < 45)     # and skin texels never take the paint's hair (a brown band on the cheek along our hair edge)
        inner = ndimage.distance_transform_edt(al)
        edge = np.clip(bilinear(inner, ix, iy)[:, 0] / (0.012 * W), 0, 1)
        w = (V['face'] ** 3) * edge * V['vis'] * (bilinear(al.astype(np.float32), ix, iy)[:, 0] > 0.9) * (prt[cov] != 23) * ~(skinlike & (prt[cov] == 21)) * ~(hairlike & (prt[cov] == 20))   # the hair lip takes the outer hair below
        if name != '08_face': w = w * (1 - FACE)                  # eyes, nose, mouth come from the close face view alone
        else: w = w * FACE                                        # and it paints nothing else
        if name == '01_front': w = w * np.where(prt[cov] == 21, np.clip((Pv[:, 2] - 0.84) / 0.03, 0.15, 1), 1)   # hair: the front view paints the fringe and crown; the side locks come from the side views
        if name in ('06_q34r', '07_q34l'): w = w * 0.8 * np.where(prt[cov] == 20, np.clip((np.abs(Pv[:, 0]) - 0.115) / 0.02, 0, 1), 1)
        if name in ('03_left', '04_right'): w = w * np.where(prt[cov] == 20, np.maximum(np.clip((Pv[:, 1] - 0.04) / 0.03, 0, 1), np.clip((np.abs(Pv[:, 0]) - 0.115) / 0.02, 0, 1)), 1)   # skin from the side views only behind or beside the cheek
        if name == '05_top': w = w * (Pv[:, 2] > 0.86)
        # tone: gain per channel in the overlap with what is placed
        ov = (w > 0.15) & (wt > 0.15)
        if ov.sum() > 500:
            g = np.clip((acc[ov] / wt[ov, None]).mean(0) / np.maximum(rgb[ov].mean(0), 1e-3), 0.8, 1.25)   # head pass: wider, the 3/4 and side views' skin read paler than the close face
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
    lipd = np.where(Pp == 23)[0]; dst = np.setdiff1d(dst, lipd)
    hs = np.where((Pp == 21) & (wt > 0.2))[0]
    if len(hs) and len(lipd):                  # the hair lip: the nearest outer hair, lifted 1.6x: it faces down, and the viewer and game light leave it in shade (r13: still a dark band under the fringe)
        sub = hs[:: max(1, len(hs) // 60000)]
        d_, nn = cKDTree(Pv[sub]).query(Pv[lipd], k=12)
        w_ = 1 / (d_ + 0.004) ** 2; tmp[lipd] = 1.6 * (tmp[sub[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True); ok[lipd] = True
    if len(src) and len(dst):
        sub = src[:: max(1, len(src) // 60000)]
        d_, nn = cKDTree(Pv[sub]).query(Pv[dst], k=12)
        w_ = 1 / (d_ + 0.004) ** 2; fill = (tmp[sub[nn]] * w_[..., None]).sum(1) / w_.sum(1, keepdims=True)
        k_ = np.clip(wt[dst] / 0.2, 0, 1)[:, None]
        tmp[dst] = tmp[dst] * k_ + fill * (1 - k_); ok[dst] = True
    # the beard ends at the jaw edge: under it, plain neck skin from the paint's own neck, a touch darker just under the jaw
    im = np.asarray(Image.open(f'references_head/{t}_08_face_clean.png').convert('RGB'), np.float32) / 255
    cx_, cy_ = NECKPT; skin = np.median(im[cy_ - 25:cy_ + 25, cx_ - 40:cx_ + 40].reshape(-1, 3), 0)
    below = np.where(Pv[:, 1] < 0.03, 0.73 + 0.45 * (Pv[:, 1] + 0.035), 0.759) - Pv[:, 2]     # the jaw edge, then level under the hair's rim at the back
    rn = np.hypot(Pv[:, 0] / 0.065, (Pv[:, 1] - 0.06) / 0.075); tube = np.clip((1.0 - rn) / 0.1, 0, 1); tube = tube * tube * (3 - 2 * tube)      # the neck itself: the hair beside it stays hair
    u_ = np.clip(below / 0.006, 0, 1); u_ = u_ * u_ * (3 - 2 * u_); u_ = u_ * tube
    shade = 0.84 + 0.16 * np.clip(below / 0.04, 0, 1)
    tmp = tmp * (1 - u_[:, None]) + (skin[None] * shade[:, None]) * u_[:, None]; ok = ok | (u_ > 0)
    print('NECK', t, 'skin', np.round(skin * 255), 'texels', int((u_ > 0.5).sum()))
    col[cov] = tmp; have[cov] = ok
    idx = ndimage.distance_transform_edt(~have, return_distances=False, return_indices=True)
    col = col[idx[0], idx[1]]
    Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype('u1')).save(f'textures/nj_head_{t}_raw.png')
    # normal from luminance: fine strand and pore relief only
    lum = col @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    im1k = np.asarray(Image.fromarray((lum * 255).astype('u1')).resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    hp = im1k - ndimage.gaussian_filter(im1k, 6)
    gx = ndimage.sobel(hp, axis=1) * 2.0; gy = ndimage.sobel(hp, axis=0) * 2.0
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + .5).astype('u1')).save(f'textures/nj_head_{t}_normal.png')
    print('HEAD', t, 'done')
