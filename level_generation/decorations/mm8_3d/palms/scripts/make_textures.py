#!/usr/bin/env python3
"""Procedural textures for the MM8 palms (no external images), adapted from the MM6 desert painter
(../../mm6_new_sorpigal_3d/desert/scripts/make_textures.py):

- textures/tropical_basecolor.png (2048², RGBA) + tropical_normal.png (1024²): four pinnate frond cells (palm_common.
  ATLAS) seen from above, rachis along the cell's centre from the bottom (frond base) to the top (tip), leaflets
  slanting toward the tip on both sides, plus two petiole stalk strips. textures/tropical_env.json: the painted
  leaflet reach per cell along the rachis (fraction of the cell half-width, 129 samples), so the frond geometry hugs
  the texels.
- textures/ringbark_* (coconut trunk: leaf-scar rings) and bootbark_* (leaf-base lattice), 512 x 1024, tileable.

Leaves are painted as strokes (a centre line with a width profile) at twice the resolution and box-filtered; each
stroke carries a height (leaflet midrib ridge) for the normal map. Colours are natural but bright: every model
grades them through COLOR_0. Seeded; reruns reproduce the same bytes. Usage: make_textures.py [atlas] [barks]"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc

os.makedirs(pc.TEX, exist_ok=True)
SS = 2          # supersampling


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


class Canvas:
    """one atlas cell painted at SS x its output size (w x h output pixels)"""
    def __init__(self, w, h):
        self.w, self.h = w * SS, h * SS
        self.rgb = np.zeros((self.h, self.w, 3)); self.a = np.zeros((self.h, self.w)); self.ht = np.zeros((self.h, self.w))

    def stroke(self, pts, half_width, colour, height=None, z=0.0, opacity=1.0):
        """pts: (N, 2) canvas pixels (x right, y down); half_width (N,); colour(t, s) -> (M, 3) linear with t along
        0..1 and s across -1..1; height(t, s) -> (M,)"""
        pts = np.asarray(pts, np.float64); hw = np.maximum(np.asarray(half_width, np.float64), 0.0)
        n = len(pts)
        tt = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); tt /= max(tt[-1], 1e-9)
        pad = hw.max() + 2
        x0 = int(max(math.floor(pts[:, 0].min() - pad), 0)); x1 = int(min(math.ceil(pts[:, 0].max() + pad), self.w))
        y0 = int(max(math.floor(pts[:, 1].min() - pad), 0)); y1 = int(min(math.ceil(pts[:, 1].max() + pad), self.h))
        if x1 <= x0 or y1 <= y0:
            return
        H, W = y1 - y0, x1 - x0
        best = np.full((H, W), np.inf); bt = np.zeros((H, W)); bs = np.zeros((H, W))
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]; pw = max(hw[i], hw[i + 1]) + 2
            sx0 = int(max(math.floor(min(a[0], b[0]) - pw), x0)); sx1 = int(min(math.ceil(max(a[0], b[0]) + pw), x1))
            sy0 = int(max(math.floor(min(a[1], b[1]) - pw), y0)); sy1 = int(min(math.ceil(max(a[1], b[1]) + pw), y1))
            if sx1 <= sx0 or sy1 <= sy0:
                continue
            yy, xx = np.mgrid[sy0:sy1, sx0:sx1] + 0.5
            d = b - a; L2 = max(d @ d, 1e-9)
            u = np.clip(((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / L2, 0, 1)
            px = xx - (a[0] + u * d[0]); py = yy - (a[1] + u * d[1])
            dist = np.hypot(px, py)
            w = hw[i] + (hw[i + 1] - hw[i]) * u
            sd = dist - w
            side = np.sign(px * d[1] - py * d[0])
            s = np.clip(side * dist / np.maximum(w, 1e-6), -1, 1)
            sl = (slice(sy0 - y0, sy1 - y0), slice(sx0 - x0, sx1 - x0))
            better = sd < best[sl]
            best[sl] = np.where(better, sd, best[sl])
            bt[sl] = np.where(better, tt[i] + (tt[i + 1] - tt[i]) * u, bt[sl])
            bs[sl] = np.where(better, s, bs[sl])
        cov = np.clip(0.5 - best, 0, 1) * opacity
        m = cov > 0
        if not m.any():
            return
        sl = (slice(y0, y1), slice(x0, x1))
        c = cov[m][:, None]
        col = colour(bt[m], bs[m])
        rgb = self.rgb[sl]; a = self.a[sl]; h = self.ht[sl]
        rgb[m] = rgb[m] * (1 - c) + col * c
        a[m] = a[m] + cov[m] * (1 - a[m])
        hh = z + (height(bt[m], bs[m]) if height else 0.0)
        h[m] = h[m] * (1 - cov[m]) + hh * cov[m]

    def down(self, x):
        return x.reshape(self.h // SS, SS, self.w // SS, SS, *x.shape[2:]).mean((1, 3))

    def finish(self):
        """output-size premultiplied colour, alpha and height"""
        a = self.down(self.a)
        rgb = self.down(self.rgb * self.a[..., None]) / np.maximum(a, 1e-4)[..., None]
        return rgb, a, self.down(self.ht * self.a)


def jitter(rng, colour, amount):
    return np.asarray(colour) * np.exp(rng.normal(0, amount, 3))


def blend(t, stops):
    ts = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops])
    return np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], -1)


# ------------------------------------------------------------------------------------------------ fronds
FROND = {
    # leaflets per side, leaflet half-width (output px), slant from the rachis (deg, base -> tip), curl (deg along
    # the leaflet: + toward the frond tip), reach profile [(t, reach)], green, tip colour, warm-tip fraction,
    # missing / broken fraction, rachis colour
    'frondA': dict(n=92, lw=10.0, slant=(58, 40), curl=15, reach=[(0, 0.55), (0.1, 0.92), (0.4, 1.0), (0.62, 0.9), (0.85, 0.55), (1.0, 0.06)],
                   green=[0.14, 0.30, 0.045], tip=[0.075, 0.15, 0.03], warm=0.08, warm_col=[0.42, 0.30, 0.06],
                   broken=0.04, rachis=[0.36, 0.40, 0.12], seed=11),
    'frondB': dict(n=88, lw=10.0, slant=(58, 40), curl=16, reach=[(0, 0.5), (0.1, 0.9), (0.4, 1.0), (0.62, 0.9), (0.85, 0.55), (1.0, 0.06)],
                   green=[0.16, 0.32, 0.045], tip=[0.10, 0.18, 0.03], warm=0.45, warm_col=[0.55, 0.30, 0.05],
                   broken=0.07, rachis=[0.42, 0.42, 0.12], seed=23),
    'frondC': dict(n=104, lw=9.0, slant=(48, 36), curl=4, reach=[(0, 0.25), (0.15, 0.85), (0.35, 1.0), (0.75, 0.75), (0.92, 0.4), (1.0, 0.08)],
                   green=[0.12, 0.27, 0.045], tip=[0.45, 0.48, 0.18], warm=1.0, warm_col=[0.50, 0.50, 0.18],
                   broken=0.02, rachis=[0.40, 0.42, 0.14], seed=37, tip_len=(0.18, 0.35)),
    # strong orange leaflet tips (tree06, tree09): most leaflets warm over their outer third to half
    'frondD': dict(n=88, lw=10.0, slant=(58, 40), curl=16, reach=[(0, 0.5), (0.1, 0.9), (0.4, 1.0), (0.62, 0.9), (0.85, 0.55), (1.0, 0.06)],
                   green=[0.15, 0.31, 0.04], tip=[0.12, 0.16, 0.025], warm=0.85, warm_col=[0.62, 0.27, 0.03],
                   broken=0.06, rachis=[0.44, 0.40, 0.12], seed=52, tip_len=(0.3, 0.55)),
}


UNDERLAY = 0.55        # inner fraction of each leaflet with the dark underlay beneath
LEAF_BRIGHT = 2.0     # leaflets painted brighter than natural: COLOR_0 then grades them down with headroom for the
                       # sunlit highlights (a COLOR_0 above 1 would clip)


def leaflet_ridge(t, s):
    return (1 - np.abs(s)) * 0.7 + 0.15 * t


def paint_frond(name, w, h):
    p = FROND[name]; rng = np.random.default_rng(p['seed'])
    cv = Canvas(w, h)
    margin = 8 * SS
    cx = cv.w / 2; half = cv.w / 2 - margin
    yb, yt = cv.h - margin, margin; L = yb - yt
    reach = lambda t: np.interp(t, [r[0] for r in p['reach']], [r[1] for r in p['reach']])
    leaflets = []
    for side in (-1, 1):
        for i in range(p['n']):
            g = (i % 3 - 1) * 0.28                              # leaflets in loose groups of three
            ta = (i - g + 0.3 + rng.uniform(0, 0.4)) / p['n']
            leaflets.append((ta, side))
    # paint from the frond tip down so lower leaflets overlap upper ones (as seen from above on a real frond)
    leaflets.sort(key=lambda x: -x[0])
    strokes = []
    for k, (ta, side) in enumerate(leaflets):
        if rng.uniform() < p['broken'] * 0.4:
            continue                                            # missing leaflet: a gap
        slant = math.radians(np.interp(ta, [0, 1], p['slant']) + rng.normal(0, 3))
        curl = math.radians(p['curl'] + rng.normal(0, 5))
        r = reach(ta) * rng.uniform(0.9, 1.0)
        broken = rng.uniform() < p['broken']
        if broken:
            r *= rng.uniform(0.45, 0.8)
        # centre line: angle from the rachis' forward (up the cell) direction grows/shrinks by curl along the leaflet
        ss = np.linspace(0, 1, 18)
        ang = slant - curl * ss ** 1.3
        dx = np.sin(ang); dy = -np.cos(ang)
        seg = np.ones_like(ss); seg[0] = 0
        xs = np.cumsum(dx * seg); ys = np.cumsum(dy * seg)
        scale = r * half / max(abs(xs[-1]), 1e-6)            # outer end reaches r x half-width across
        rachis_w = (3.5 - 2.0 * ta) * SS
        x0 = cx + side * rachis_w * 0.6; y0 = yb - ta * L
        pts = np.stack([x0 + side * xs * scale, y0 + ys * scale], -1)
        if pts[:, 1].min() < yt * 0.5:
            pts[:, 1] = np.maximum(pts[:, 1], yt * 0.5)
        lw = p['lw'] * SS * rng.uniform(0.85, 1.15) * (0.75 + 0.35 * min(ta / 0.2, 1.0)) * (1.0 - 0.35 * ta)
        width = lw * np.minimum(1.0, 0.45 + ss / 0.18 * 0.55) * np.clip(1 - ss, 0, 1) ** 0.75 + 0.35
        if broken:
            width = np.maximum(width, lw * 0.5)
        base = jitter(rng, p['green'], 0.1) * rng.uniform(0.68, 1.3)
        light = base * np.array([1.9, 1.5, 1.5])
        tipc = jitter(rng, p['tip'], 0.12)
        warm = rng.uniform() < p['warm']
        wl = rng.uniform(*p.get('tip_len', (0.15, 0.4)))
        wc = jitter(rng, p['warm_col'], 0.15)

        def colour(t, s, base=base, light=light, tipc=tipc, warm=warm, wl=wl, wc=wc):
            c = blend(t, [(0.0, light), (0.15, base * 1.35), (0.5, base * 1.05), (1.0, tipc if not warm else wc)])
            if warm:
                f = np.clip((t - (1 - wl)) / wl, 0, 1)[:, None] ** 0.8
                c = c * (1 - f) + wc[None] * f
            mid = np.exp(-(s / 0.25) ** 2)
            edge = np.clip(np.abs(s) - 0.6, 0, 1) / 0.4
            return c * (1 + 0.35 * mid[:, None] - 0.25 * edge[:, None]) * LEAF_BRIGHT
        strokes.append((pts, width, lw, colour, 0.2 + 0.5 * (1 - ta)))
    # dark underlay first: the shaded leaflets beneath, a near-black green filling the gaps over the inner part of
    # every leaflet (the sprites' dark mass between lit leaflets); the outer tips stay open and feathery
    dark = np.array([0.022, 0.055, 0.011]) * LEAF_BRIGHT      # deep green, not black (seen from below too)
    for pts, width, lw, colour, z in strokes:
        n = max(3, int(len(pts) * UNDERLAY))
        cv.stroke(pts[:n], np.full(n, lw * 2.0) * np.linspace(1.0, 0.6, n),
                  lambda t, s: dark[None] * (0.8 + 0.4 * (1 - np.abs(s)))[:, None], None, z=0.0)
    for pts, width, lw, colour, z in strokes:
        cv.stroke(pts, width, colour, leaflet_ridge, z=z)
    # rachis on top
    ts = np.linspace(0, 1, 40)
    pts = np.stack([np.full_like(ts, cx), yb - ts * L], -1)
    rc = np.asarray(p['rachis'])
    cv.stroke(pts, (4.0 - 2.8 * ts) * SS, lambda t, s: rc[None] * (0.8 + 0.45 * (1 - np.abs(s)))[:, None] * (1 - 0.2 * t)[:, None],
              lambda t, s: (1 - s * s) * 1.2, z=1.0)
    rgb, a, ht = cv.finish()
    # painted reach along the rachis (output px rows), 129 samples, conservative (max over each sample's band)
    ys = np.arange(h); tt = ((yb / SS) - (ys + 0.5)) / (L / SS)
    cols = np.abs(np.arange(w) + 0.5 - cx / SS)
    row_reach = np.where(a > 0.12, cols[None, :], 0).max(1) / (half / SS)
    env = []
    for k in range(129):
        t = k / 128
        band = (tt >= t - 1 / 128) & (tt <= t + 1 / 128)
        env.append(round(float(row_reach[band].max()) + 0.01, 4) if band.any() else 0.05)
    return rgb, a, ht, env


def stalk(name, w, h, top, bottom):
    cv = Canvas(w, h)
    rng = np.random.default_rng(91 if name == 'stalk' else 92)
    yy = np.arange(cv.h); t = yy / cv.h                          # 0 top (toward the frond) .. 1 bottom (trunk)
    col = blend(t, [(0.0, top), (1.0, bottom)])
    s = (np.arange(cv.w) + 0.5 - cv.w / 2) / (cv.w / 2)
    shade = 0.7 + 0.4 * np.sqrt(np.clip(1 - s ** 2, 0, 1))
    streak = 1 + 0.12 * np.sin(np.arange(cv.w) * 0.9 + rng.uniform(0, 6)) * rng.uniform(0.5, 1.0)
    cv.rgb[:] = col[:, None, :] * (shade * streak)[None, :, None]
    cv.a[:] = 1.0
    cv.ht[:] = (1 - s ** 2)[None, :] * 0.4
    return cv.finish()


def atlas():
    N = pc.ATLAS_SIZE
    rgb = np.zeros((N, N, 3)); a = np.zeros((N, N)); ht = np.zeros((N, N))
    envs = {}
    for name in pc.FRONDS:
        u0, v0, u1, v1 = pc.ATLAS[name]
        x0, y0, x1, y1 = round(u0 * N), round(v0 * N), round(u1 * N), round(v1 * N)
        c_rgb, c_a, c_h, env = paint_frond(name, x1 - x0, y1 - y0)
        rgb[y0:y1, x0:x1] = c_rgb; a[y0:y1, x0:x1] = c_a; ht[y0:y1, x0:x1] = c_h
        envs[name] = env
        print('FROND', name, 'coverage', round(float((c_a > 0.5).mean()), 3), 'max reach', max(env))
    for name, top, bottom in (('stalk', [0.24, 0.27, 0.08], [0.30, 0.22, 0.10]),
                              ('stalkGold', [0.50, 0.44, 0.12], [0.45, 0.30, 0.09])):
        u0, v0, u1, v1 = pc.ATLAS[name]
        x0, y0, x1, y1 = round(u0 * N), round(v0 * N), round(u1 * N), round(v1 * N)
        c_rgb, c_a, c_h = stalk(name, x1 - x0, y1 - y0, top, bottom)
        rgb[y0:y1, x0:x1] = c_rgb; a[y0:y1, x0:x1] = c_a; ht[y0:y1, x0:x1] = c_h
    covered = a > 0.02
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    rgb = np.clip(rgb[iy, ix], 0, 1)
    Image.fromarray(np.dstack([(srgb(rgb) * 255 + 0.5).astype(np.uint8), (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)]),
                    'RGBA').save(os.path.join(pc.TEX, 'tropical_basecolor.png'), optimize=True)
    # normal map at half size: height filtered, gradient, dilated
    h2 = ht.reshape(N // 2, 2, N // 2, 2).mean((1, 3)); a2 = a.reshape(N // 2, 2, N // 2, 2).mean((1, 3))
    gy, gx = np.gradient(ndimage.gaussian_filter(h2, 0.7))
    nrm = np.stack([-gx * 5.0, gy * 5.0, np.ones_like(h2)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    _, (iy, ix) = ndimage.distance_transform_edt(~(a2 > 0.02), return_indices=True)
    nrm = nrm[iy, ix]
    Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(pc.TEX, 'tropical_normal.png'),
                                                                                  optimize=True)
    json.dump(envs, open(pc.ENV, 'w'))
    print('ATLAS tropical', N, 'coverage', round(float((a >= 0.5).mean()), 3))


# ------------------------------------------------------------------------------------------------ barks
def noise(rng, shape, beta=2.0, scale=(1.0, 1.0)):
    """periodic 1/f^beta noise, 0..1"""
    field = rng.normal(size=shape)
    fy, fx = np.meshgrid(np.fft.fftfreq(shape[0]) * scale[0], np.fft.fftfreq(shape[1]) * scale[1], indexing='ij')
    radius = np.sqrt(fx * fx + fy * fy); radius[0, 0] = 1.0
    spec = np.fft.fft2(field) / radius ** beta; spec[0, 0] = 0
    v = np.real(np.fft.ifft2(spec))
    return (v - v.min()) / (v.max() - v.min())


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def save_bark(name, colour, height, strength):
    Image.fromarray((srgb(colour) * 255 + 0.5).astype(np.uint8)).save(os.path.join(pc.TEX, f'{name}_basecolor.png'),
                                                                       optimize=True)
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        os.path.join(pc.TEX, f'{name}_normal.png'), optimize=True)
    print('BARK', name, 'mean sRGB', (srgb(colour).reshape(-1, 3).mean(0) * 255).round(1))


def barks():
    W, H = 512, 1024
    rng = np.random.default_rng(3801)
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    # coconut trunk: 26 leaf-scar rings per tile (2.4 m), wavy and slightly tilted; fine vertical fissures; grey-brown
    # noise scale (sy, sx): a large sx suppresses variation across x (horizontal features), a large sy vertical ones
    wob = noise(rng, (H, W), 2.2, (1.0, 1.0)) - 0.5
    spacing = noise(rng, (H, W), 2.0, (1.0, 8.0)) - 0.5                       # uneven ring spacing along the trunk
    ringpos = (yy / H * 20 + 0.5 * wob + 2.0 * spacing + 1.0 * xx / W) % 1.0   # one full tilt step per round: periodic
    gw = 0.035 + 0.035 * noise(rng, (H, W), 2.4)
    scar = np.exp(-((ringpos - 0.12) / gw) ** 2)                               # dark groove, uneven width
    band = np.clip(np.sin(np.pi * np.clip((ringpos - 0.16) / 0.84, 0, 1)), 0, 1) ** 0.6   # raised band between grooves
    fiss = noise(rng, (H, W), 1.3, (4.0, 0.3)); blot = noise(rng, (H, W), 2.4)
    crack = np.clip((0.07 - np.abs(noise(rng, (H, W), 1.2, (2.5, 0.15)) - 0.5)) * 12, 0, 1)
    height = band * 0.55 - scar * 0.7 + fiss * 0.35 - crack * 0.5
    base = np.array([0.30, 0.20, 0.085])
    tone = (0.28 + 1.2 * band[..., None]) * (0.7 + 0.55 * fiss[..., None]) * (0.85 + 0.3 * blot[..., None])
    col = base * tone * (1 - 0.95 * scar[..., None]) * (1 - 0.45 * crack[..., None])
    grey = np.array([0.17, 0.16, 0.14]) * (0.8 + 0.4 * fiss[..., None])
    m = np.clip((blot - 0.55) * 3, 0, 1)[..., None] * 0.25
    col = col * (1 - m) + grey * m
    save_bark('ringbark', col, height, 7.0)
    # leaf-base lattice (date / boot palms): rows of overlapping boots, each a diamond plate (a cut leaf base) rising to
    # its ragged upper edge, which stands proud of the plate above and leaves a dark shadow gap; fibres in the gaps
    nx, ny = 7, 11
    a = xx / W * nx + yy / H * ny; b = xx / W * nx - yy / H * ny
    fa, fb = a - np.floor(a), b - np.floor(b)
    ia, ib = np.floor(a).astype(int), np.floor(b).astype(int)
    cellrand = rng.uniform(size=(2, 64, 64))
    r = cellrand[0][ia % 64, ib % 64]; r2 = cellrand[1][ia % 64, ib % 64]
    v = ((fa - 0.5) - (fb - 0.5)) / 2              # -0.5 at the plate's upper corner .. 0.5 at its lower corner
    hz = (fa + fb - 1) / 2                         # across the plate
    up = 0.5 - v                                   # 0 bottom .. 1 top
    edge_n = noise(rng, (H, W), 1.6, (0.5, 0.5)) - 0.5
    lip = np.clip((up - 0.78 - 0.12 * edge_n - 0.06 * r2) / 0.08, 0, 1)        # the shadowed rim above the cut edge
    across = np.abs(hz) * 2
    gap = np.minimum(np.minimum(fa, 1 - fa), np.minimum(fb, 1 - fb))
    fib = noise(rng, (H, W), 1.2, (6.0, 0.3)); fib2 = noise(rng, (H, W), 1.0, (8.0, 0.25))
    plate = (0.25 + 0.75 * up) * (1 - lip) * np.clip(gap * 10, 0, 1) * (1 - 0.3 * across ** 2)
    height = plate + 0.2 * fib - 0.25 * lip
    tone = 0.6 + 0.55 * r[..., None]
    col = np.asarray([0.34, 0.25, 0.13])[None, None] * tone * (0.45 + 0.8 * plate[..., None]) * (0.7 + 0.5 * fib[..., None])
    cut = np.clip((up - 0.68) / 0.1, 0, 1) * (1 - lip)                            # pale fibrous cut face at the top
    col = col * (1 - 0.45 * cut[..., None]) + np.asarray([0.42, 0.33, 0.19]) * (0.8 + 0.4 * fib2[..., None]) * 0.45 * cut[..., None]
    dark = np.clip(np.maximum(1 - gap * 9, lip), 0, 1)[..., None]
    hair = np.asarray([0.10, 0.07, 0.04]) * (0.6 + 0.8 * fib2[..., None])
    col = col * (1 - 0.92 * dark) + hair * 0.7 * dark
    save_bark('bootbark', col, height, 9.0)


if __name__ == '__main__':
    which = sys.argv[1:] or ['atlas', 'barks']
    for w in which:
        {'atlas': atlas, 'barks': barks}[w]()
