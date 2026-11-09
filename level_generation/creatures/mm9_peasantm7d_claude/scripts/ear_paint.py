#!/usr/bin/env python3
"""Elf ear paint (both tiers). The head retextures painted the new ear islands from the head views; tier D's came out as
blond hair strands (the views show the ears against the hair) and tier C's half skin, half hair. MM9's elf ears are plain
skin, so the ear islands are painted procedurally from the tier's own face skin: one colour (the median of the tier's
clean cheek/forehead skin, the hand_clean.py test with blond hair excluded by hue) x shading in the ear's own coordinates
(the add_ears.py grid: u root->tip, v across): the front cup darker and a little redder toward its centre, the rolled rim
lighter, the root (inside the hair) darker, a slightly pinker tip, the back face a little darker; plus fine two-scale skin
noise (+-2.5 %). Normal flat (the geometry carries the cup and rim), ORM R 255 / G the face skin's roughness / B 0. Texels are
found by rasterising the ear triangles of work/ear_faces.npz (scripts/ear_dump.py) into the 2K head set; islands padded 6 px.
Then the pressed human ears (press_weight below). Reads <prefix>_head_*_preear.png when present (made on the first run), writes <prefix>_head_*.png.
Usage (project folder): ear_paint.py <prefix> [<prefix> ...]"""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

T = Path('textures')
D = np.load('work/ear_faces.npz')
# add_ears.py report (work/ears_v3.blend; v2's root was 2.6 cm further back): midline, root, tip, width, FWD 0.45
MID, ROOT, TIP, EW, FWD = -0.0111, np.array([0.075, 0.004, 0.779]), np.array([0.141, 0.042, 0.863]), 0.046, 0.45
eu = TIP - ROOT; EL = np.linalg.norm(eu); eu /= EL
en = np.array([1.0, -FWD, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)
ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
PAD, U0 = 6 / 2048, 0.004
STEP = (D['UV'][..., 0].max() + PAD - U0) / 4     # one island + its two pads (4 islands in a row)


def raster(N):
    """Per texel: ear id (0 none), local u, v, front flag."""
    E = np.zeros((N, N), np.int8); U = np.zeros((N, N)); V = np.zeros((N, N)); F = np.zeros((N, N), bool)
    for uv, p, e in zip(D['UV'], D['P'], D['E']):
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        if not ok.any():
            continue
        pos = w[ok] @ p
        lx = pos.copy(); lx[:, 0] = (pos[:, 0] - MID) * (1 if e == 1 else -1)
        r = lx - ROOT
        u = np.clip((r @ eu) / EL, 0, 1)
        wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
        v = np.clip((r @ ev) / np.maximum(wid * 0.5, 1e-4), -1, 1)
        isl = int(np.floor((uv[:, 0].mean() - U0) / STEP))   # island index: 2 * ear + side
        yy, xx = c[ok, 1].astype(int), c[ok, 0].astype(int)
        E[yy, xx] = e; U[yy, xx] = u; V[yy, xx] = v; F[yy, xx] = (isl % 2 == 0)
    return E, U, V, F


def press_weight(N):
    """Weight raster of the pressed human ears (work/press_faces.npz, press_dump.py): the moved vertices' corner weights
    interpolated over their faces and one ring, raised (w ** 0.5) and blurred 2 px; 0 outside those faces."""
    PD = np.load('work/press_faces.npz')
    Wr = np.zeros((N, N)); cov = np.zeros((N, N), bool)
    for uv, wc in zip(PD['UV'], PD['W']):
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        yy, xx = c[ok, 1].astype(int), c[ok, 0].astype(int)
        Wr[yy, xx] = np.maximum(Wr[yy, xx], np.clip(w[ok] @ wc, 0, 1)); cov[yy, xx] = True
    Wr = np.sqrt(Wr)
    return np.where(cov, ndi.gaussian_filter(Wr, 2.0), 0.0), cov


def hair_zone(N):
    """Texels of the hair shell within 8 cm of an elf ear root (work/press_faces_hair.npz), with the 3D distance."""
    H = np.load('work/press_faces_hair.npz')
    Dr = np.full((N, N), np.inf)
    for uv, dc in zip(H['UV'], H['D']):
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        yy, xx = c[ok, 1].astype(int), c[ok, 0].astype(int)
        Dr[yy, xx] = np.minimum(Dr[yy, xx], w[ok] @ dc)
    return Dr


def neck_z(N):
    """Rest height of the face shell's neck texels (work/press_faces_neck.npz), NaN elsewhere."""
    H = np.load('work/press_faces_neck.npz')
    Z = np.full((N, N), np.nan)
    for uv, zc in zip(H['UV'], H['Z']):
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        Z[c[ok, 1].astype(int), c[ok, 0].astype(int)] = w[ok] @ zc
    return Z


def panel_raster(N):
    """Texels of the flat throat panel (work/panel_faces.npz, scripts/panel_find.py): PeasantM7's undershirt collar piece."""
    H = np.load('work/panel_faces.npz')
    M = np.zeros((N, N), bool)
    for uv in H['UV']:
        q = uv * N; q[:, 1] = N - q[:, 1]
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(max(x0, 0), min(x1, N)), np.arange(max(y0, 0), min(y1, N)))
        if xs.size == 0:
            continue
        c = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
        a, b, d = q
        m = np.array([[b[0] - a[0], d[0] - a[0]], [b[1] - a[1], d[1] - a[1]]])
        if abs(np.linalg.det(m)) < 1e-9:
            continue
        l = np.linalg.solve(m, (c - a).T).T
        w = np.column_stack([1 - l.sum(1), l])
        ok = (w >= -1e-3).all(1)
        M[c[ok, 1].astype(int), c[ok, 0].astype(int)] = True
    return M


def skin_ref(img):
    N = img.shape[0]; k = int(round(N * 0.8))
    face = img[N - k:, :k].reshape(-1, 3) / 255
    mx, mn = face.max(1), face.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    lum = face @ np.array([0.299, 0.587, 0.114])
    hue = (face[:, 1] - face[:, 2]) / np.maximum(face[:, 0] - face[:, 2], 1e-6)
    sk = face[(lum > 0.45) & (sat > 0.25) & (sat < 0.6) & (face[:, 0] > face[:, 1]) & (face[:, 1] > face[:, 2]) & (hue < 0.5)]
    return np.median(sk, 0) * 255


def load(prefix, kind):
    cur = T / f'{prefix}_head_{kind}.png'; pre = T / f'{prefix}_head_{kind}_preear.png'
    if not pre.exists():
        shutil.copyfile(cur, pre)
    return np.asarray(Image.open(pre).convert('RGB')).astype(np.float64), cur


rng = np.random.default_rng(7)
for prefix in sys.argv[1:]:
    img, cur = load(prefix, 'basecolor')
    N = img.shape[0]
    E, U, V, F = raster(N)
    ear = E > 0
    ref = skin_ref(img)
    cup = (1 - V ** 2) * np.sin(np.pi * np.minimum(U * 1.1, 1))
    rim = np.clip((np.abs(V) - 0.7) / 0.3, 0, 1) * (1 - U)
    shade = np.where(F, 1 - 0.20 * cup + 0.05 * rim, 0.93 - 0.03 * (1 - U))
    shade *= 0.88 + 0.12 * np.clip(U / 0.25, 0, 1)            # root inside the hair
    tint = np.stack([1 + 0.06 * cup * F + 0.04 * np.clip((U - 0.8) / 0.2, 0, 1),
                     1 - 0.03 * cup * F, 1 - 0.03 * cup * F], -1)
    noise = ndi.gaussian_filter(rng.standard_normal((N, N)), 0.8) * 0.9 + ndi.gaussian_filter(rng.standard_normal((N, N)), 2.5) * 1.6
    noise = 1 + 0.025 * noise / max(noise.std(), 1e-6)
    col = ref[None, None, :] * (shade * noise)[..., None] * tint
    out = img.copy()
    out[ear] = np.clip(col[ear], 0, 255)
    grown = ndi.binary_dilation(ear, iterations=6) & ~ear
    band = np.zeros_like(ear); band[: int(N * 0.2), : int(N * 0.8)] = True   # only the free band above the head islands
    idx = ndi.distance_transform_edt(~ear, return_distances=False, return_indices=True)
    pad = grown & band
    out[pad] = out[idx[0], idx[1]][pad]
    # pressed human ears (add_ears.py press=1): Meshy painted a human ear there (D) or a pink ear shape (C); those texels take
    # the surrounding skin (normalised convolution of skin-hued texels outside the moved vertices' faces, sigma 12 px) x
    # the same fine noise, by the press weight; the elf ear's root covers most of it
    pw, pcov = press_weight(N)
    f = out / 255
    hue = (f[..., 1] - f[..., 2]) / np.maximum(f[..., 0] - f[..., 2], 1e-6)
    lumf = f @ np.array([0.299, 0.587, 0.114])
    skinpx = (~pcov) & (f[..., 0] > f[..., 1]) & (f[..., 1] > f[..., 2]) & (hue < 0.5) & (lumf > 0.4) & ~ear
    num = np.stack([ndi.gaussian_filter(out[..., c] * skinpx, 12) for c in range(3)], -1)
    den = ndi.gaussian_filter(skinpx.astype(float), 12)[..., None]
    fill = np.where(den > 0.02, num / np.maximum(den, 1e-6), ref[None, None, :]) * noise[..., None]
    out = out * (1 - pw[..., None]) + fill * pw[..., None]
    # hair shell next to the ear roots: skin-hued texels there (the views' elf ear base painted onto the hair's side edge)
    # take hair (below), feathered 1 px
    Dr = hair_zone(N)
    zone = np.isfinite(Dr)
    f = out / 255
    hue = (f[..., 1] - f[..., 2]) / np.maximum(f[..., 0] - f[..., 2], 1e-6)
    mx, mn = f.max(-1), f.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    skinish = zone & (f[..., 0] > f[..., 1]) & (f[..., 1] > f[..., 2]) & (hue < 0.40) & (sat > 0.25) & (sat < 0.70)   # skin hue ~0.26-0.30, blond hair 0.48-0.53
    skinish = ndi.binary_dilation(ndi.binary_opening(skinish, iterations=1), iterations=2) & zone
    # mirror fill: each such texel takes the hair texel mirrored across the nearest hair border (strand texture kept; a
    # normalised convolution could not reach the middle of the 100 px pink patches), else the nearest hair texel
    hairpx = ndi.binary_dilation(zone, iterations=40) & ~skinish & ~ear & (f.sum(-1) > 0.05) & (hue > 0.40)
    iy, ix = ndi.distance_transform_edt(~hairpx, return_distances=False, return_indices=True)
    yy, xx = np.nonzero(skinish)
    my, mx_ = np.clip(2 * iy[yy, xx] - yy, 0, N - 1), np.clip(2 * ix[yy, xx] - xx, 0, N - 1)
    good = hairpx[my, mx_]
    sy, sx = np.where(good, my, iy[yy, xx]), np.where(good, mx_, ix[yy, xx])
    fillh = out.copy(); fillh[yy, xx] = out[sy, sx]
    hw = ndi.gaussian_filter(skinish.astype(float), 1.0) * zone
    out = out * (1 - hw[..., None]) + fillh * hw[..., None]
    # neck: the head views wear a high gold brocade collar; Meshy painted it onto the neck skin (the body's collar is lower).
    # Face-shell texels below z 0.715 that are not skin-hued take the skin colour around them (20 px normalised convolution
    # of the skin texels, nearest beyond its reach) x the fine noise, faded in over z 0.715..0.70
    Z = neck_z(N)
    f = out / 255
    hue = (f[..., 1] - f[..., 2]) / np.maximum(f[..., 0] - f[..., 2], 1e-6)
    mx, mn = f.max(-1), f.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    lumf = f @ np.array([0.299, 0.587, 0.114])
    nz = np.isfinite(Z)
    skin_n = nz & (f[..., 0] > f[..., 1]) & (f[..., 1] > f[..., 2]) & (hue < 0.42) & (sat > 0.15) & (sat < 0.6) & (lumf > 0.35)
    skin_n = ndi.binary_opening(skin_n, iterations=2)
    bad = nz & (np.nan_to_num(Z, nan=1) < 0.715) & ~skin_n
    bad = ndi.binary_dilation(bad, iterations=2) & nz & (np.nan_to_num(Z, nan=1) < 0.72)
    den = ndi.gaussian_filter(skin_n.astype(float), 20)
    sb = np.stack([ndi.gaussian_filter(out[..., c] * skin_n, 20) for c in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
    okd = den > 0.03
    iy, ix = ndi.distance_transform_edt(~okd, return_distances=False, return_indices=True)
    fill = sb[iy, ix] * noise[..., None]      # smooth skin colour (20 px normalised convolution), nearest where too far
    nw = ndi.gaussian_filter(bad.astype(float), 1.5) * nz * np.clip((0.72 - np.nan_to_num(Z, nan=1)) / 0.015, 0, 1)
    out = out * (1 - nw[..., None]) + fill * nw[..., None]
    # throat panel: PeasantM7's undershirt collar piece in the tunic's V. The views painted it as skin, which read as a pale
    # flat plate under the chin. The head UVs are PeasantM7's (the ears were appended), so the panel takes PeasantM7's own
    # approved paint there: its non-skin texels on the face shell below z 0.70 (closed 3 px), feathered 1 px
    m7 = np.asarray(Image.open('textures/pm7_tp_head_basecolor.png').convert('RGB')).astype(np.float64)
    g7 = m7 / 255
    h7 = (g7[..., 1] - g7[..., 2]) / np.maximum(g7[..., 0] - g7[..., 2], 1e-6)
    mx7, mn7 = g7.max(-1), g7.min(-1); s7 = (mx7 - mn7) / np.maximum(mx7, 1e-6)
    l7 = g7 @ np.array([0.299, 0.587, 0.114])
    skin7 = (g7[..., 0] > g7[..., 1]) & (g7[..., 1] > g7[..., 2]) & (h7 < 0.45) & (s7 > 0.15) & (l7 > 0.33)
    pm = np.isfinite(Z) & (np.nan_to_num(Z, nan=1) < 0.70) & ~skin7   # 0.72 took the M7 beard under the chin
    pm = ndi.binary_closing(ndi.binary_opening(pm, iterations=1), iterations=3) & np.isfinite(Z)
    pw_ = ndi.gaussian_filter(pm.astype(float), 1.0) * np.isfinite(Z)
    out = out * (1 - pw_[..., None]) + m7 * pw_[..., None]
    Image.fromarray(np.uint8(np.clip(np.round(out), 0, 255))).save(cur)
    rep = dict(prefix=prefix, panel_texels=int(pm.sum()), neck_texels=int((nw > 0.5).sum()), pressed_texels=int((pw > 0.5).sum()), hair_rim_texels=int((hw > 0.5).sum()), ear_texels=int(ear.sum()), front=int((ear & F).sum()), skin_ref=ref.round(1).tolist())
    # normal and ORM (1K)
    for kind, flat in (('normal_1k', None), ('metal_rough_1k', None)):
        im, path = load(prefix, kind)
        n = im.shape[0]
        e = np.asarray(Image.fromarray(ear.astype(np.uint8) * 255).resize((n, n), Image.NEAREST)) > 0
        e = ndi.binary_dilation(e, iterations=3) & np.asarray(Image.fromarray(band.astype(np.uint8) * 255).resize((n, n), Image.NEAREST)) > 0
        if kind == 'normal_1k':
            im[e] = (128, 128, 255)
            pwn = np.asarray(Image.fromarray(np.uint8(pw * 255)).resize((n, n), Image.BILINEAR)).astype(float)[..., None] / 255
            im = im * (1 - pwn) + np.array([128, 128, 255.0]) * pwn
        else:
            skin_px = (np.asarray(Image.fromarray(np.uint8(img)).resize((n, n))).astype(float))
            r_ = np.median(im[..., 1][(np.abs(skin_px - ref).sum(-1) < 30)]) if (np.abs(skin_px - ref).sum(-1) < 30).any() else 200
            im[e] = (255, r_, 0)
            rep['roughness'] = float(r_)
        Image.fromarray(np.uint8(np.round(im))).save(path)
    print('EAR_PAINT', json.dumps(rep))
