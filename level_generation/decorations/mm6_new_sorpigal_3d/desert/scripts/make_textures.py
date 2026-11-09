#!/usr/bin/env python3
"""Procedural textures for the desert palms (no external images): textures/<atlas>_basecolor.png (RGBA) +
<atlas>_normal.png for the foliage atlases palm, banana and yucca (cells in desert_common.ATLAS), and tileable
<bark>_basecolor.png + _normal.png bark maps. Leaves are painted as strokes (a centre line with a width profile)
at twice the resolution and box-filtered down; each stroke carries a height (fold ridge, pleat) for the normal map.
Colours are painted fairly bright and neutral: every model grades them through COLOR_0. Seeded; rerunning
reproduces the same bytes. Usage: make_textures.py"""
import math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc

os.makedirs(dc.TEX, exist_ok=True)
SS = 2          # supersampling


def srgb(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def lin(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


class Canvas:
    def __init__(self, size):
        self.n = size * SS
        self.rgb = np.zeros((self.n, self.n, 3)); self.a = np.zeros((self.n, self.n)); self.h = np.zeros((self.n, self.n))

    def stroke(self, pts, half_width, colour, height=None, z=0.0, opacity=1.0):
        """pts: (N, 2) in canvas pixels (x right, y down); half_width (N,) pixels; colour(t, s) -> (M, 3) linear,
        t along the stroke 0..1, s across -1..1; height(t, s) -> (M,)."""
        pts = np.asarray(pts, np.float64); hw = np.maximum(np.asarray(half_width, np.float64), 0.0)
        n = len(pts)
        tt = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]); tt /= max(tt[-1], 1e-9)
        pad = hw.max() + 2
        x0 = int(max(math.floor(pts[:, 0].min() - pad), 0)); x1 = int(min(math.ceil(pts[:, 0].max() + pad), self.n))
        y0 = int(max(math.floor(pts[:, 1].min() - pad), 0)); y1 = int(min(math.ceil(pts[:, 1].max() + pad), self.n))
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
        rgb = self.rgb[sl]; a = self.a[sl]; h = self.h[sl]
        rgb[m] = rgb[m] * (1 - c) + col * c
        a[m] = a[m] + cov[m] * (1 - a[m])
        hh = z + (height(bt[m], bs[m]) if height else 0.0)
        h[m] = h[m] * (1 - cov[m]) + hh * cov[m]

    def cut(self, mask):
        self.a = np.where(mask, 0.0, self.a)

    def finish(self, strength=6.0, blur=0.8):
        """box-filter to the output size; colour dilated into transparent texels; normal from the height."""
        def down(x):
            return x.reshape(self.n // SS, SS, self.n // SS, SS).mean((1, 3))
        a = down(self.a)
        rgb = np.stack([down(self.rgb[..., k] * self.a) for k in range(3)], -1) / np.maximum(a, 1e-4)[..., None]
        h = down(self.h * self.a)
        gy, gx = np.gradient(ndimage.gaussian_filter(h, blur))
        nrm = np.stack([-gx * strength, gy * strength, np.ones_like(h)], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        covered = a > 0.02
        _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
        return np.clip(rgb[iy, ix], 0, 1), a, nrm[iy, ix]


def save_atlas(name, canvas, strength=6.0):
    rgb, a, nrm = canvas.finish(strength)
    Image.fromarray(np.dstack([(srgb(rgb) * 255 + 0.5).astype(np.uint8), (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)]),
                    'RGBA').save(os.path.join(dc.TEX, f'{name}_basecolor.png'))
    Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(dc.TEX, f'{name}_normal.png'))
    print('ATLAS', name, 'coverage', round(float((a >= 0.5).mean()), 3))


def cell_px(cell):
    """cell (u0, v0, u1, v1) -> canvas pixel box (x0, y0, x1, y1)"""
    n = dc.ATLAS_SIZE * SS
    return cell[0] * n, cell[1] * n, cell[2] * n, cell[3] * n


def jitter(rng, colour, amount):
    return np.asarray(colour) * np.exp(rng.normal(0, amount, 3))


def blend(t, stops):
    """piecewise-linear colour ramp over t: stops [(t, rgb), ...] -> (M, 3)"""
    ts = np.array([s[0] for s in stops]); cs = np.array([s[1] for s in stops])
    return np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], -1)


def ridge(t, s):
    return (1 - np.abs(s)) * 0.6


# ------------------------------------------------------------------------------------------------ palm atlas
def fan(cv, rng, cell, variant):
    """Washingtonia fan seen from above, petiole entering at the bottom of the cell: ~46 pleated segments over 250°,
    joined in the inner half (the costa and hastula pale), split toward drooping pointed tips with a few threads."""
    x0, y0, x1, y1 = cell_px(cell); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = (x1 - x0) * 0.49
    segs = 46; span = math.radians(125)
    green = {'A': [0.17, 0.42, 0.08], 'B': [0.15, 0.36, 0.07], 'C': [0.26, 0.40, 0.08]}[variant]
    tip = {'A': [0.07, 0.17, 0.035], 'B': [0.06, 0.15, 0.03], 'C': [0.32, 0.30, 0.10]}[variant]
    order = rng.permutation(segs)
    for k in order:
        f = (k + 0.5) / segs
        theta = -span + 2 * span * f + rng.normal(0, 0.008)
        reach = rng.uniform(0.86, 1.0) * (1 - 0.18 * abs(2 * f - 1) ** 3)
        split = rng.uniform(0.48, 0.62)
        bend = rng.normal(0, 0.08)
        pitch = 2 * span / segs
        rs = np.linspace(0.04, reach, 24)
        ang = theta + bend * np.clip((rs - split) / (1 - split), 0, None) ** 1.5
        pts = np.stack([cx + np.sin(ang) * rs * R, cy - np.cos(ang) * rs * R], -1)
        joined = pitch * rs * R * 0.64
        frac = np.clip((rs - split) / max(reach - split, 1e-3), 0, 1)
        hw = np.where(rs < split, joined, joined * (1 - frac) ** 0.85 * 0.85 + 0.6)
        light = 1.0 + (0.16 if k % 2 else -0.16) + rng.normal(0, 0.06)
        base = jitter(rng, green, 0.06) * light; tipc = jitter(rng, tip, 0.1)
        hast = base * np.array([1.5, 1.25, 1.6])

        def colour(t, s, base=base, tipc=tipc, hast=hast, reach=reach):
            r = 0.04 + t * (reach - 0.04)
            c = blend(r, [(0.0, hast), (0.1, hast), (0.3, base * 1.15), (0.7, base), (1.0, tipc)])
            mid = np.exp(-(s / 0.22) ** 2)
            return c * (1 + 0.25 * mid[:, None])
        cv.stroke(pts, hw, colour, ridge, z=rng.uniform(0, 0.2))
        if rng.uniform() < 0.25:                    # loose threads between the tips
            a2 = theta + pitch * 0.5 + rng.normal(0, 0.05)
            r2 = np.linspace(split, min(reach + 0.08, 1.0), 10)
            p2 = np.stack([cx + np.sin(a2 + 0.15 * (r2 - split)) * r2 * R, cy - np.cos(a2) * r2 * R], -1)
            cv.stroke(p2, np.full(10, 0.9), lambda t, s: np.tile([0.55, 0.52, 0.40], (len(t), 1)), None, z=0.3)
    # costa (rib) entering from the petiole
    pts = np.array([[cx, cy + 0.12 * R], [cx, cy - 0.18 * R]])
    cv.stroke(pts, [0.03 * R, 0.006 * R], lambda t, s: np.tile([0.40, 0.48, 0.20], (len(t), 1)), ridge, z=0.6)


def skirt(cv, rng, cell):
    """dead fans hanging against the trunk: straw-brown segments falling from the top edge, slightly splayed"""
    x0, y0, x1, y1 = cell_px(cell); W, H = x1 - x0, y1 - y0
    for k in range(70):
        bx = x0 + W * (0.5 + rng.normal(0, 0.16)); by = y0 + H * rng.uniform(0.0, 0.08)
        length = H * rng.uniform(0.6, 0.95)
        ang = rng.normal(0, 0.12) + (bx - (x0 + W / 2)) / W * 0.6
        ts = np.linspace(0, 1, 16)
        curl = rng.normal(0, 0.06)
        pts = np.stack([bx + np.sin(ang + curl * ts) * ts * length, by + np.cos(ang + curl * ts) * ts * length], -1)
        pts[:, 0] = np.clip(pts[:, 0], x0 + 3, x1 - 3)
        hw = W * rng.uniform(0.018, 0.03) * (1 - 0.8 * ts) + 0.6
        dark = rng.uniform(0.45, 1.0)
        col = jitter(rng, [0.30, 0.22, 0.12], 0.12) * dark

        def colour(t, s, col=col):
            return col[None] * (0.8 + 0.3 * (1 - np.abs(s)))[:, None] * (1 - 0.35 * t)[:, None]
        cv.stroke(pts, hw, colour, ridge, z=k / 70)


def stalk(cv, cell, top, bottom):
    x0, y0, x1, y1 = cell_px(cell)
    yy = np.arange(int(y0), int(y1)); t = (yy - y0) / (y1 - y0)
    col = blend(t, [(0.0, top), (1.0, bottom)])
    s = (np.arange(int(x0), int(x1)) - (x0 + x1) / 2) / ((x1 - x0) / 2)
    shade = 0.75 + 0.35 * np.sqrt(np.clip(1 - s ** 2, 0, 1))
    cv.rgb[int(y0):int(y1), int(x0):int(x1)] = col[:, None, :] * shade[None, :, None]
    cv.a[int(y0):int(y1), int(x0):int(x1)] = 1.0
    cv.h[int(y0):int(y1), int(x0):int(x1)] = (1 - s ** 2)[None, :] * 0.3


def palm_atlas():
    rng = np.random.default_rng(2101)
    cv = Canvas(dc.ATLAS_SIZE)
    fan(cv, rng, dc.ATLAS['palm']['fanA'], 'A')
    fan(cv, rng, dc.ATLAS['palm']['fanB'], 'B')
    fan(cv, rng, dc.ATLAS['palm']['fanC'], 'C')
    skirt(cv, rng, dc.ATLAS['palm']['skirt'])
    stalk(cv, dc.ATLAS['palm']['stalk'], [0.30, 0.34, 0.12], [0.22, 0.17, 0.08])
    save_atlas('palm', cv)


# ------------------------------------------------------------------------------------------------ banana atlas
VEIN = 0.07           # lateral veins rise this much in t (leaf length) from the midrib to the edge


def slit(xx, yy, p0, p1, w0, w1):
    """coverage of a tapered slit from p0 (half-width w0 px) to p1 (w1)"""
    d = np.subtract(p1, p0); L2 = max(d @ d, 1e-9)
    u = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / L2, 0, 1)
    dist = np.hypot(xx - p0[0] - u * d[0], yy - p0[1] - u * d[1])
    return np.clip(w0 + (w1 - w0) * u - dist + 0.5, 0, 1)


def banana_leaf(cv, rng, cell, kind):
    """Leaf along v (base at the bottom of the cell, tip at the top), u across: the geometry follows the outline
    (desert_build.banana_profile), so the texture fills the cell width; tears are transparent slits along the
    lateral veins, ragged dry edges brown."""
    x0, y0, x1, y1 = cell_px(cell); W, H = int(x1 - x0), int(y1 - y0)
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    t = 1 - yy / H                                  # 0 base .. 1 tip
    s = (xx - W / 2) / (W / 2)                       # -1 .. 1 across
    vein = np.sin((t - np.abs(s) * VEIN) * 95 * math.pi)
    green = {'A': [0.10, 0.25, 0.075], 'B': [0.09, 0.21, 0.066], 'C': [0.15, 0.24, 0.07], 'D': [0.26, 0.17, 0.07]}[kind]
    col = np.asarray(green)[None, None] * (1 + 0.06 * vein[..., None])
    n1 = ndimage.gaussian_filter(rng.normal(size=(H, W)), (H / 60, W / 30)); n1 /= n1.std()
    col = col * (1 + 0.10 * n1[..., None])
    mid = np.exp(-(s / 0.05) ** 2)[..., None]
    col = col * (1 - mid) + np.asarray([0.38, 0.40, 0.14] if kind != 'D' else [0.35, 0.25, 0.10])[None, None] * mid
    # torn strips catch the light differently: piecewise-constant brightness along the veins, stronger to the edge
    phase = t - np.abs(s) * VEIN
    edges = np.sort(rng.uniform(0, 1, 70)); strip = np.searchsorted(edges, phase)
    bright = rng.normal(0, 0.32, 72)[np.clip(strip, 0, 71)]
    col = col * np.exp(bright * np.clip(np.abs(s) * 1.6 - 0.15, 0, 1))[..., None]
    # dry brown edge and blotches
    edge = np.clip((np.abs(s) - 0.82) / 0.18, 0, 1) * (0.5 + 0.5 * (n1 > 0.3))
    blotch = np.clip(ndimage.gaussian_filter(rng.normal(size=(H, W)), (H / 40, W / 12)) * 12 - 0.9, 0, 1) * (np.abs(s) > 0.4)
    dry = np.clip(edge + blotch * {'A': 0.4, 'B': 0.6, 'C': 0.9, 'D': 0.0}[kind], 0, 1)[..., None]
    col = col * (1 - dry) + np.asarray([0.30, 0.20, 0.08])[None, None] * dry
    alpha = np.ones((H, W))
    # tears: wedge slits from the edge toward the midrib along the lateral veins (t rises toward the edge)
    tears = {'A': 12, 'B': 22, 'C': 17, 'D': 34}[kind]
    for side in (-1, 1):
        for k in range(tears):
            tv = rng.uniform(0.06, 0.96)
            depth = rng.uniform(0.3, 0.97) if kind != 'D' else rng.uniform(0.6, 0.97)
            ex, ey = W / 2 + side * W / 2 * 1.03, (1 - tv) * H
            ix_, iy_ = W / 2 + side * (1.0 - depth) * W / 2, (1 - (tv - depth * VEIN)) * H
            open_ = rng.uniform(2.0, 6.0) * SS
            alpha *= 1 - slit(xx, yy, (ex, ey), (ix_, iy_), open_, 0.8)
    # outline ragged by a little noise at the edges and the very tip
    rag = np.abs(s) > 0.985 - 0.03 * (n1 > 0.8)
    alpha[rag] = 0.0
    alpha[t > 0.995] = 0.0
    height = (1 - np.abs(s)) * 0.3 + mid[..., 0] * 0.6 + 0.04 * vein
    sl = (slice(int(y0), int(y0) + H), slice(int(x0), int(x0) + W))
    cv.rgb[sl] = col; cv.a[sl] = alpha; cv.h[sl] = height


def bunch(cv, rng, cell):
    """banana hand rows wrapped round a cone (u around, v from the top of the bunch down)"""
    x0, y0, x1, y1 = cell_px(cell); W, H = int(x1 - x0), int(y1 - y0)
    sl = (slice(int(y0), int(y0) + H), slice(int(x0), int(x0) + W))
    cv.rgb[sl] = [0.05, 0.08, 0.02]; cv.a[sl] = 1.0; cv.h[sl] = 0.0
    rows, cols = 7, 9
    for r in range(rows):
        for c in range(cols):
            bx = x0 + (c + 0.5 + 0.5 * (r % 2)) / cols * W; by = y0 + (r + 0.15) / rows * H
            ts = np.linspace(0, 1, 10)
            pts = np.stack([bx + np.sin(ts * 1.2) * W * 0.02, by + ts * H / rows * 1.05], -1)
            col = jitter(rng, [0.16, 0.26, 0.05], 0.08)
            cv.stroke(pts, W / cols * 0.42 * np.sin(np.pi * (0.15 + 0.85 * ts)) ** 0.5 + 0.5,
                      lambda t, s, col=col: col[None] * (0.7 + 0.45 * (1 - s ** 2))[:, None], ridge, z=r * 0.1)


def banana_atlas():
    rng = np.random.default_rng(1901)
    cv = Canvas(dc.ATLAS_SIZE)
    for name, kind in (('leafA', 'A'), ('leafB', 'B'), ('leafC', 'C'), ('dead', 'D')):
        banana_leaf(cv, rng, dc.ATLAS['banana'][name], kind)
    bunch(cv, rng, dc.ATLAS['banana']['bunch'])
    stalk(cv, dc.ATLAS['banana']['stalk'], [0.22, 0.30, 0.08], [0.16, 0.20, 0.06])
    stalk(cv, dc.ATLAS['banana']['sheath'], [0.30, 0.22, 0.10], [0.22, 0.16, 0.07])
    save_atlas('banana', cv, 4.0)


# ------------------------------------------------------------------------------------------------ yucca atlas
def spray(cv, rng, cell, count, spread, green, tipc, width, dry=0.0, z=0.0, length=(0.6, 0.97)):
    """stiff pointed leaves fanning from the bottom centre of the cell"""
    x0, y0, x1, y1 = cell_px(cell); W, H = x1 - x0, y1 - y0
    bx, by = x0 + W / 2, y1 - H * 0.02
    angles = np.sort(rng.uniform(-spread, spread, count))
    for k in rng.permutation(count):
        a = angles[k]
        L = H * rng.uniform(*length) * (1 - 0.25 * (a / spread) ** 2)
        L = min(L, (W / 2 - 4) / max(abs(math.sin(a)), 1e-3), H * 0.97)
        ts = np.linspace(0, 1, 14)
        bend = rng.normal(0, 0.05)
        ang = a + bend * ts ** 2
        pts = np.stack([bx + np.sin(ang) * ts * L, by - np.cos(ang) * ts * L], -1)
        hw = W * width * rng.uniform(0.8, 1.2) * np.clip(np.minimum(ts / 0.12, 1.0) * (1 - ts) ** 0.9, 0.08, 1) + 0.5
        base = jitter(rng, green, 0.10) * rng.uniform(0.8, 1.15); tc = jitter(rng, tipc, 0.15)
        drytip = rng.uniform() < dry

        def colour(t, s, base=base, tc=tc, drytip=drytip):
            c = blend(t, [(0, base * 0.55), (0.25, base), (0.8, base * 1.1), (1.0, tc if drytip else base * 1.25)])
            mid = np.exp(-(s / 0.25) ** 2)
            edge = np.clip(np.abs(s) - 0.7, 0, 1) / 0.3
            return c * (1 + 0.35 * mid - 0.25 * edge)[:, None]
        cv.stroke(pts, hw, colour, ridge, z=z + k / count * 0.3)


def hanging(cv, rng, cell, count):
    """dead leaves hanging from the top of the cell (orange-brown, curling)"""
    x0, y0, x1, y1 = cell_px(cell); W, H = x1 - x0, y1 - y0
    for k in range(count):
        bx = x0 + W * (0.5 + rng.normal(0, 0.12)); by = y0 + H * rng.uniform(0.0, 0.05)
        L = H * rng.uniform(0.55, 0.95)
        a = rng.normal(0, 0.18)
        ts = np.linspace(0, 1, 16); curl = rng.normal(0, 0.15)
        pts = np.stack([bx + np.sin(a + curl * ts) * ts * L, by + np.cos(a + curl * ts) * ts * L], -1)
        pts[:, 0] = np.clip(pts[:, 0], x0 + 3, x1 - 3)
        hw = W * rng.uniform(0.016, 0.026) * (1 - 0.85 * ts) + 0.6
        col = jitter(rng, [0.42, 0.20, 0.07], 0.14) * rng.uniform(0.55, 1.1)

        def colour(t, s, col=col):
            return col[None] * (0.8 + 0.35 * (1 - np.abs(s)))[:, None] * (1 - 0.3 * t)[:, None]
        cv.stroke(pts, hw, colour, ridge, z=k / count)


def blade(cv, rng, cell, green, stripe):
    """one sword leaf filling the cell (the geometry follows its outline): dark margins, pale centre stripe and
    lengthwise streaks, a brown spine tip"""
    x0, y0, x1, y1 = cell_px(cell); W, H = int(x1 - x0), int(y1 - y0)
    yy, xx = np.mgrid[0:H, 0:W] + 0.5
    t = 1 - yy / H; s = (xx - W / 2) / (W / 2)
    streak = ndimage.gaussian_filter(rng.normal(size=(H, W)), (H / 8, 1.5)); streak /= streak.std()
    c = np.asarray(green)[None, None] * (1 + 0.12 * streak[..., None])
    band = np.exp(-((np.abs(s) - 0.35) / 0.16) ** 2)[..., None]
    c = c * (1 - 0.8 * band) + np.asarray(stripe)[None, None] * 0.8 * band * (1 + 0.25 * streak[..., None])
    c = c * (0.55 + 0.45 * (1 - np.clip(np.abs(s) - 0.75, 0, 1) / 0.25))[..., None]
    c = c * (0.6 + 0.4 * np.clip(t / 0.15, 0, 1))[..., None]
    tip = np.clip((t - 0.93) / 0.07, 0, 1)[..., None]
    c = c * (1 - tip) + np.asarray([0.20, 0.12, 0.05]) * tip
    sl = (slice(int(y0), int(y0) + H), slice(int(x0), int(x0) + W))
    cv.rgb[sl] = c; cv.a[sl] = 1.0; cv.h[sl] = (1 - np.abs(s)) * 0.4


def yucca_atlas():
    rng = np.random.default_rng(1701)
    cv = Canvas(dc.ATLAS_SIZE)
    A = dc.ATLAS['yucca']
    spray(cv, rng, A['sprayA'], 15, math.radians(58), [0.10, 0.25, 0.10], [0.40, 0.30, 0.12], 0.022, dry=0.15)
    spray(cv, rng, A['sprayB'], 19, math.radians(62), [0.09, 0.22, 0.09], [0.42, 0.28, 0.10], 0.020, dry=0.25)
    hanging(cv, rng, A['dead'], 45)
    spray(cv, rng, A['strands'], 26, math.radians(26), [0.14, 0.22, 0.08], [0.36, 0.33, 0.12], 0.020, dry=0.3,
          length=(0.75, 0.98))
    spray(cv, rng, A['strandsB'], 24, math.radians(30), [0.16, 0.24, 0.08], [0.40, 0.32, 0.12], 0.016, dry=0.4,
          length=(0.7, 0.98))
    blade(cv, rng, A['bladeA'], [0.10, 0.26, 0.07], [0.30, 0.50, 0.18])
    blade(cv, rng, A['bladeB'], [0.08, 0.22, 0.06], [0.22, 0.42, 0.14])
    save_atlas('yucca', cv)


# ------------------------------------------------------------------------------------------------ barks
def noise(rng, shape, beta=2.0, scale=(1.0, 1.0)):
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
    Image.fromarray((srgb(colour) * 255 + 0.5).astype(np.uint8)).save(os.path.join(dc.TEX, f'{name}_basecolor.png'))
    Image.fromarray((normal_from_height(height, strength) * 255 + 0.5).astype(np.uint8)).save(
        os.path.join(dc.TEX, f'{name}_normal.png'))
    print('BARK', name, 'mean sRGB', (srgb(colour).reshape(-1, 3).mean(0) * 255).round(1))


def barks():
    S = 512
    rng = np.random.default_rng(3301)
    yy, xx = np.mgrid[0:S, 0:S] + 0.5
    # palm boots: a diagonal lattice of cut leaf bases, each a plate whose upper edge stands out (period 8 x 8 cells)
    n = 8
    a = (xx / S * n + yy / S * n) ; b = (xx / S * n - yy / S * n)
    fa, fb = a - np.floor(a), b - np.floor(b)
    ia, ib = np.floor(a).astype(int), np.floor(b).astype(int)
    cellrand = rng.uniform(size=(64, 64))
    r = cellrand[ia % 64, ib % 64]
    up = (fa + fb) / 2                             # 0 at the cell's lower corner .. 1 at the upper corner
    across = np.abs(fa - fb)
    plate = np.clip(1 - across * 1.1, 0, 1) ** 0.5
    gap = np.minimum(np.minimum(fa, 1 - fa), np.minimum(fb, 1 - fb))
    fib = noise(rng, (S, S), 1.2, (6.0, 0.3))
    height = plate * (0.3 + 0.7 * up) * np.clip(gap * 14, 0, 1) + 0.15 * fib
    tone = 0.6 + 0.5 * r[..., None]
    col = np.asarray([0.40, 0.33, 0.23])[None, None] * tone * (0.45 + 0.75 * up[..., None]) * (0.8 + 0.4 * fib[..., None])
    dark = np.clip(1 - gap * 10, 0, 1)[..., None]
    col = col * (1 - 0.8 * dark) + np.asarray([0.03, 0.025, 0.02]) * 0.8 * dark
    save_bark('palmboot', col, height, 9.0)
    # banana pseudostem: overlapping sheaths, vertical fibres, green-brown with dry patches
    fib = noise(rng, (S, S), 1.4, (5.0, 0.25)); patch = noise(rng, (S, S), 2.4)
    sheath = (xx / S * 5 + 0.3 * noise(rng, (S, S), 2.6)) % 1.0
    green = np.asarray([0.16, 0.20, 0.07]); brown = np.asarray([0.30, 0.20, 0.09])
    m = np.clip((patch - 0.45) * 4, 0, 1)[..., None]
    col = (green * (1 - m) + brown * m) * (0.7 + 0.5 * fib[..., None]) * (0.75 + 0.25 * sheath[..., None])
    height = fib * 0.5 + sheath * 0.6
    save_bark('bananastem', col, height, 5.0)
    # dragon / Joshua tree bark: grey-brown, long shallow furrows and scaly patches
    furrow = noise(rng, (S, S), 1.6, (3.0, 0.2)); scale_ = noise(rng, (S, S), 2.0)
    ridge_ = 1 - np.abs(furrow - 0.5) * 2
    crack = np.clip((0.06 - np.abs(noise(rng, (S, S), 1.15, (3.0, 0.6)) - 0.5)) * 18, 0, 1)
    height = ridge_ ** 2 * 0.6 + scale_ * 0.3 - crack * 0.5
    col = np.asarray([0.21, 0.16, 0.10])[None, None] * (0.45 + 0.75 * height[..., None]) * (0.85 + 0.3 * scale_[..., None])
    col = col * (1 - 0.75 * crack[..., None])
    save_bark('dragonbark', col, height, 7.0)
    # yucca / cordyline stem: pale tan, horizontal leaf-scar rings over fine vertical streaks
    streak = noise(rng, (S, S), 1.4, (6.0, 0.2)); jit = noise(rng, (S, S), 2.5)
    ring = (yy / S * 22 + 0.6 * jit) % 1.0
    scar = np.exp(-((ring - 0.5) / 0.08) ** 2)
    height = streak * 0.4 - scar * 0.6
    col = np.asarray([0.34, 0.26, 0.17])[None, None] * (0.75 + 0.35 * streak[..., None]) * (1 - 0.35 * scar[..., None])
    save_bark('yuccastem', col, height, 6.0)


if __name__ == '__main__':
    which = sys.argv[1:] or ['palm', 'banana', 'yucca', 'barks']
    for w in which:
        {'palm': palm_atlas, 'banana': banana_atlas, 'yucca': yucca_atlas, 'barks': barks}[w]()
