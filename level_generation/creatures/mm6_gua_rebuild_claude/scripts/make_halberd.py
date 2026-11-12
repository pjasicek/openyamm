#!/usr/bin/env python3
"""Halberd from MM9's own pole (no Codex master: the image tool refused the weapon prompt, see README). Outline = the MM9 vertices in
the plane of the blades, a sharp double-bevelled plate per blade, socket, octagonal shaft, spike and butt cap as rings. Procedural PBR
paint for both MM9 poles: guardpole (pale steel sheath, leather grip) and guardpole2 (blued blades, studded dark wood). Frame: L along
the shaft (0 = spike tip, + toward the butt), W across (big blade at -W), D through the plate. Writes work/halberd.npz and
textures/halberd_{a,c}_{basecolor,normal,orm}.png. Run in the project folder."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage

L0 = -0.534                                   # MM9 tip in the PCA frame of the pole
SIZE = (2048, 512)                            # texture: top 340 px the plates, bottom strip the shaft
BIG = np.array([(-0.262, -0.020), (-0.282, -0.075), (-0.405, -0.068), (-0.290, -0.226), (-0.135, -0.098), (0.045, -0.072), (-0.125, -0.064), (-0.152, -0.020)])
TOP = np.array([(-0.262, 0.020), (-0.258, 0.098), (-0.378, 0.086), (-0.217, 0.152), (-0.046, 0.096), (-0.166, 0.084), (-0.166, 0.020)])
RS, RG = 0.0165, 0.0175                       # shaft and grip radius, m
RINGS = [(0.0, 0.0005), (0.070, 0.0085), (0.147, 0.021), (0.152, 0.0235), (0.158, 0.0235), (0.163, 0.021), (0.375, 0.021), (0.380, 0.0235), (0.388, 0.0235), (0.395, RS),
         (1.360, RS), (1.366, 0.0195), (1.378, 0.0195), (1.384, RG), (1.900, RG), (1.906, 0.020), (1.920, 0.020), (1.926, RS), (2.015, RS), (2.022, 0.0185), (2.034, 0.0150), (2.046, 0.0015)]
SIDES = 8


def inset(poly, d):
    """Miter inset of a polygon (counter-clockwise), clamped."""
    n = len(poly); out = []
    for i in range(n):
        a, b, c = poly[i - 1], poly[i], poly[(i + 1) % n]
        u = (b - a) / np.linalg.norm(b - a); v = (c - b) / np.linalg.norm(c - b)
        nu = np.array([-u[1], u[0]]); nv = np.array([-v[1], v[0]])
        m = nu + nv; m /= max(np.linalg.norm(m), 1e-9)
        k = d / max(m @ nu, 0.35)
        out.append(b + m * k)
    return np.array(out)


def area(p):
    return 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])


def earclip(p):
    idx = list(range(len(p))); tri = []
    def inside(q, a, b, c):
        s = lambda u, v, w: (v[0] - u[0]) * (w[1] - u[1]) - (v[1] - u[1]) * (w[0] - u[0])
        return s(a, b, q) >= 0 and s(b, c, q) >= 0 and s(c, a, q) >= 0
    while len(idx) > 3:
        for k in range(len(idx)):
            i, j, m = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = p[i], p[j], p[m]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue
            if any(inside(p[o], a, b, c) for o in idx if o not in (i, j, m)):
                continue
            tri.append((i, j, m)); idx.pop(k); break
        else:
            raise SystemExit('ear clip failed')
    tri.append(tuple(idx))
    return tri


V, UV, F, KIND = [], [], [], []


def uv_plate(l, w):
    return np.array([(l + 0.0) / 0.62 * 0.97 + 0.015, 0.34 + (w + 0.235) / 0.40 * 0.65])


def uv_shaft(l, a):
    return np.array([l / 2.05 * 0.985 + 0.0075, 0.02 + a * 0.28])


def plate(poly):
    p = poly.copy(); p[:, 0] -= L0
    if area(p) < 0: p = p[::-1]
    q = inset(p, 0.016)
    i0 = len(V)
    n = len(p)
    for s in (1, -1):
        b = len(V)
        for x in p: V.append((x[0], x[1], 0.0)); UV.append(uv_plate(*x))
        for x in q: V.append((x[0], x[1], s * 0.0065)); UV.append(uv_plate(*x))
        for i in range(n):
            j = (i + 1) % n
            f = [(b + i, b + j, b + n + j), (b + i, b + n + j, b + n + i)]
            F.extend(f if s > 0 else [t[::-1] for t in f])
        for t in earclip(q):
            f = tuple(b + n + k for k in t)
            F.append(f if s > 0 else f[::-1])


plate(BIG); plate(TOP)
b = len(V)
nr = len(RINGS)
for r_i, (l, r) in enumerate(RINGS):
    for s in range(SIDES + 1):
        a = s / SIDES * 2 * np.pi + np.pi / SIDES
        V.append((l, r * np.cos(a), r * np.sin(a))); UV.append(uv_shaft(l, s / SIDES))
for r_i in range(nr - 1):
    for s in range(SIDES):
        p, q = b + r_i * (SIDES + 1) + s, b + (r_i + 1) * (SIDES + 1) + s
        F.append((p, q, q + 1)); F.append((p, q + 1, p + 1))
V = np.array(V); UV = np.array(UV); F = np.array(F)
np.savez('work/halberd.npz', v=V, uv=UV, f=F, L0=L0)
print('HALBERD tris', len(F), 'verts', len(V))

# ---------------------------------------------------------------- paint
W, H = SIZE
rng = np.random.default_rng(9)


def noise(sig, sx=1.0):
    n = ndimage.gaussian_filter(rng.normal(size=(H, W)), (sig, sig * sx), mode='wrap')
    return n / n.std()


def rasterise(poly):
    from PIL import ImageDraw
    p = poly.copy(); p[:, 0] -= L0
    im = Image.new('L', (W, H)); d = ImageDraw.Draw(im)
    d.polygon([tuple(np.array([(uv_plate(*x))[0] * W, (1 - uv_plate(*x)[1]) * H])) for x in p], fill=255)
    return np.asarray(im) > 0


mask = rasterise(BIG) | rasterise(TOP)
dist = ndimage.distance_transform_edt(mask, sampling=(0.40 / 0.65 / H, 0.62 / 0.97 / W))      # metres from the outline
fine, mid, big = noise(1.2), noise(6), noise(40)
grain = noise(1.0, 12.0)                                              # along the shaft
scr = np.clip(noise(0.8, 30) - 2.1, 0, 1)
SR = (1 - 0.34) * H                                                    # image row of the strip's top


def paint(t):
    rows = np.arange(H)[:, None]; cols = np.arange(W)[None, :]
    l = (cols - 0.0075 * W) / (0.985 * W) * 2.05                       # shaft length coordinate
    a = ((H - rows) / H - 0.02) / 0.28                                  # around
    img = np.zeros((H, W, 3)); rough = np.full((H, W), 0.5); metal = np.zeros((H, W)); hgt = np.zeros((H, W))
    # plates
    edge = np.clip(1 - dist / 0.016, 0, 1)
    if t == 'a':
        steel = np.array([150, 150, 142.]) + (fine * 7 + mid * 9 + big * 10)[..., None] + (grain * 5)[..., None]
        steel = steel * (1 + 0.28 * edge[..., None] ** 2)
    else:
        steel = np.array([66, 68, 72.]) + (fine * 5 + mid * 7 + big * 7)[..., None] + (grain * 3)[..., None]
        steel = steel + (edge[..., None] ** 2.2) * np.array([120, 122, 124.])
    pit = np.clip(mid - 1.4, 0, 1)
    img[mask] = (steel * (1 - 0.35 * pit[..., None]))[mask]
    rough[mask] = (0.38 + 0.08 * noise(3) - 0.16 * edge + 0.25 * pit)[mask]
    metal[mask] = 1
    hgt[mask] = (0.5 * pit * -1 + 0.08 * fine + 0.8 * np.clip(dist / 0.016, 0, 1))[mask]
    # shaft strip: by length bands
    strip = rows >= 0.68 * H
    band = np.zeros_like(l + a)
    ll = np.repeat(l, H, 0); aa = np.repeat(a, W, 1)
    socket = ll < 0.395; collar1 = (ll >= 1.360) & (ll < 1.384); grip = (ll >= 1.384) & (ll < 1.900); collar2 = (ll >= 1.900) & (ll < 1.926)
    pole = (ll >= 0.395) & (ll < 1.360); tail = (ll >= 1.926) & (ll < 2.015); cap = ll >= 2.015
    if t == 'a':
        c_pole = np.array([168, 170, 168.]) + (grain * 9 + big * 6)[..., None]; m_pole = 1; r_pole = 0.36 + 0.05 * grain
        c_sock = np.array([140, 140, 132.]) + (fine * 6 + mid * 8)[..., None]
    else:
        wood = 0.5 + 0.5 * np.sin(aa * 34 + 0.7 * grain + ll * 3)
        c_pole = np.array([54, 33, 22.]) + wood[..., None] * np.array([30, 18, 10.]) + (grain * 6)[..., None]; m_pole = 0; r_pole = 0.62 + 0.04 * grain
        c_sock = np.array([70, 72, 76.]) + (fine * 5 + mid * 6)[..., None]
    wrap = 0.5 + 0.5 * np.sign(np.sin((ll * 46 + aa * 2 * np.pi)))     # spiral leather strap
    c_grip = np.array([66, 40, 24.]) * (0.72 + 0.38 * wrap[..., None]) + (fine * 6 + grain * 4)[..., None]
    c_col = np.array([170, 170, 164.]) + (fine * 6 + mid * 6)[..., None]
    for m_, c_, r_, me_ in ((socket, c_sock, 0.42, 1), (pole, c_pole, r_pole, m_pole), (collar1, c_col, 0.34, 1), (grip, c_grip, 0.72, 0),
                            (collar2, c_col, 0.34, 1), (tail, c_pole if t == 'c' else c_col * 0.8, r_pole if t == 'c' else 0.4, m_pole), (cap, c_col, 0.34, 1)):
        k = m_ & strip
        img[k] = c_[k]; rough[k] = (r_ * np.ones((H, W)))[k]; metal[k] = me_
    hgt[strip & grip] = (0.9 * wrap + 0.1 * fine)[strip & grip]
    hgt[strip & (collar1 | collar2)] = 1
    if t == 'c':                                                        # round steel studs along the pole
        st = (ll - 0.46) % 0.135; sa = (aa * 4) % 1
        d_ = np.sqrt(((st - 0.02) / 0.012) ** 2 + ((sa - 0.5) / 0.20) ** 2)
        k = strip & pole & (d_ < 1)
        img[k] = (np.array([176, 178, 180.]) * (1.1 - 0.3 * d_[..., None]))[k]; rough[k] = 0.3; metal[k] = 1
        hgt[k] = (1 - d_ ** 2)[k]
    img = img + scr[..., None] * 60 * (metal[..., None] > 0)
    img = np.clip(img, 0, 255)
    # pad into the gutters
    used = mask | strip
    idx = ndimage.distance_transform_edt(~used, return_distances=False, return_indices=True)
    img = img[idx[0], idx[1]]; rough = rough[idx[0], idx[1]]; metal = metal[idx[0], idx[1]]; hgt = hgt[idx[0], idx[1]]
    Image.fromarray(img.astype(np.uint8)).save(f'textures/halberd_{t}_basecolor.png')
    gy, gx = np.gradient(ndimage.gaussian_filter(hgt, 0.8))
    k = 2.2
    n = np.dstack([-gx * k, gy * k, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8)).resize((1024, 256), Image.LANCZOS).save(f'textures/halberd_{t}_normal.png')
    orm = np.dstack([np.full((H, W), 1.0), np.clip(rough, 0.05, 1), metal])
    Image.fromarray((orm * 255).astype(np.uint8)).resize((1024, 256), Image.LANCZOS).save(f'textures/halberd_{t}_orm.png')


for t in 'ac':
    paint(t)
print('PAINTED')
