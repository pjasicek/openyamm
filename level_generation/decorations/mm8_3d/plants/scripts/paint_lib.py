"""Procedural painting for the MM8 plant atlases (system Python: numpy, scipy, PIL; no external images).

A Canvas is one atlas cell, painted at 2x supersampling. Shapes are strips along a (possibly bent) spine, rasterised
as triangles that carry two coordinates per texel: t along the spine (0 base .. 1 tip) and s across it (-1 left edge ..
+1 right edge). A style function turns (t, s, position, per-shape random) into colour and height, so leaves, petals,
fronds and blades share one rasteriser and get veins, midribs, margins, bands, speckles and highlights from their
own parameters. Later shapes paint over earlier ones (back to front). Normals come from the height field, with no
gradient across the boundary of two shapes (overlaps do not draw ridges). Colour is box-filtered premultiplied and
dilated into transparent texels of the cell, so mips never pick up a dark halo."""
import math
import numpy as np
from PIL import Image
from scipy import ndimage

SS = 2


def smooth_noise(rng, h, w, sigma):
    n = ndimage.gaussian_filter(rng.normal(0, 1, (h, w)).astype(np.float32), sigma, mode='wrap')
    return n / max(float(n.std()), 1e-6)


def lin(c):
    return np.asarray(c, np.float32)


def mix(a, b, f):
    f = np.asarray(f, np.float32)
    if f.ndim == 1:
        f = f[:, None]
    return a * (1 - f) + b * f


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


class Canvas:
    def __init__(self, w, h, seed=0, wrap_u=False):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.rgb = np.zeros((self.H, self.W, 3), np.float32)
        self.alpha = np.zeros((self.H, self.W), np.float32)
        self.height = np.zeros((self.H, self.W), np.float32)
        self.ident = np.zeros((self.H, self.W), np.int32)
        self.rng = np.random.default_rng(seed)
        self.lo = smooth_noise(self.rng, self.H, self.W, max(self.W, self.H) / 40)
        self.mid = smooth_noise(self.rng, self.H, self.W, 3.0 * SS)
        self.hi = smooth_noise(self.rng, self.H, self.W, 0.8 * SS)
        self.next_id = 1
        self.wrap_u = wrap_u

    # ------------------------------------------------------------ rasteriser
    def _tri(self, P, A):
        x0 = int(max(math.floor(P[:, 0].min()), 0)); x1 = int(min(math.ceil(P[:, 0].max()) + 1, self.W))
        y0 = int(max(math.floor(P[:, 1].min()), 0)); y1 = int(min(math.ceil(P[:, 1].max()) + 1, self.H))
        if x1 <= x0 or y1 <= y0:
            return None
        ys, xs = np.mgrid[y0:y1, x0:x1]
        px = xs + 0.5; py = ys + 0.5
        (ax, ay), (bx, by), (cx, cy) = P
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            return None
        l0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
        l1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            return None
        att = l0[m][:, None] * A[0] + l1[m][:, None] * A[1] + l2[m][:, None] * A[2]
        return ys[m], xs[m], att

    def strip(self, spine, half, style, rnd=None, z=0.0, sides=(-1.0, 1.0)):
        """spine: (n, 2) points in cell pixels (x right, y down); half: (n,) half widths in pixels (may differ per
        side as (n, 2)). style(t, s, x, y, rnd, canvas) -> (rgb (k, 3), height (k,), alpha (k,) or None)."""
        spine = np.asarray(spine, np.float64) * SS
        half = np.asarray(half, np.float64) * SS
        if half.ndim == 1:
            half = np.stack([half, half], 1)
        n = len(spine)
        tang = np.gradient(spine, axis=0)
        tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
        perp = np.stack([-tang[:, 1], tang[:, 0]], 1)            # points to the right of the spine direction
        seg = np.linalg.norm(np.diff(spine, axis=0), axis=1)
        tt = np.concatenate([[0], np.cumsum(seg)]); tt /= max(tt[-1], 1e-9)
        left = spine - perp * half[:, :1]; right = spine + perp * half[:, 1:]
        ys_all, xs_all, at_all = [], [], []
        for i in range(n - 1):
            for (pa, sa), (pb, sb) in (((left, -1.0), (spine, 0.0)), ((spine, 0.0), (right, 1.0))):
                quad = [(pa[i], tt[i], sa), (pb[i], tt[i], sb), (pb[i + 1], tt[i + 1], sb), (pa[i + 1], tt[i + 1], sa)]
                for tri in ((0, 1, 2), (0, 2, 3)):
                    P = np.array([quad[k][0] for k in tri]); A = np.array([[quad[k][1], quad[k][2]] for k in tri])
                    r = self._tri(P, A)
                    if r is not None:
                        ys_all.append(r[0]); xs_all.append(r[1]); at_all.append(r[2])
        if not ys_all:
            return
        ys = np.concatenate(ys_all); xs = np.concatenate(xs_all); at = np.concatenate(at_all)
        rgb, hgt, alp = style(at[:, 0], at[:, 1], xs, ys, rnd if rnd is not None else {}, self)
        if alp is None:
            alp = np.ones(len(ys), np.float32)
        keep = alp > 0.5
        ys, xs, rgb, hgt = ys[keep], xs[keep], rgb[keep], hgt[keep]
        self.rgb[ys, xs] = np.clip(rgb, 0, 1)
        self.alpha[ys, xs] = 1.0
        self.height[ys, xs] = hgt + z
        self.ident[ys, xs] = self.next_id
        self.next_id += 1

    def leaf(self, base, angle, length, width, shape, style, bend=0.0, segs=18, rnd=None, z=0.0, wave=0.0,
             asym=0.0):
        """Leaf from base (pixels) pointing along angle (0 = up, + clockwise), bending by `bend` radians over its
        length; shape(t) -> 0..1 relative half width; width = full width at shape 1."""
        pts, hw = [], []
        x, y = base; a = angle
        for k in range(segs + 1):
            t = k / segs
            pts.append((x, y))
            w = width * 0.5 * shape(t)
            hw.append((w * (1 - asym), w * (1 + asym)))
            a = angle + bend * t + wave * math.sin(t * 6.0)
            x += math.sin(a) * length / segs; y -= math.cos(a) * length / segs
        self.strip(pts, np.array(hw), style, rnd, z)

    def disc(self, centre, radius, colour_fn, z=0.0, squash=1.0):
        """Filled circle; colour_fn(r (0..1), x, y, canvas) -> (rgb, height)."""
        cx, cy = centre[0] * SS, centre[1] * SS; R = radius * SS
        x0, x1 = int(max(cx - R - 1, 0)), int(min(cx + R + 2, self.W))
        y0, y1 = int(max(cy - R * squash - 1, 0)), int(min(cy + R * squash + 2, self.H))
        if x1 <= x0 or y1 <= y0:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1]
        r = np.hypot((xs + 0.5 - cx) / R, (ys + 0.5 - cy) / (R * squash))
        m = r <= 1
        ys, xs, r = ys[m], xs[m], r[m]
        rgb, hgt = colour_fn(r, xs, ys, self)
        self.rgb[ys, xs] = np.clip(rgb, 0, 1); self.alpha[ys, xs] = 1.0
        self.height[ys, xs] = hgt + z; self.ident[ys, xs] = self.next_id; self.next_id += 1

    def fill(self, colour_fn):
        """Whole cell opaque (tiling textures): colour_fn(x, y, canvas) on the full grid."""
        ys, xs = np.mgrid[0:self.H, 0:self.W]
        rgb, hgt = colour_fn(xs.ravel(), ys.ravel(), self)
        self.rgb[:] = np.clip(rgb.reshape(self.H, self.W, 3), 0, 1)
        self.height[:] = hgt.reshape(self.H, self.W); self.alpha[:] = 1.0; self.ident[:] = 1

    # ------------------------------------------------------------ output
    def finish(self, normal_strength=5.0):
        """-> (rgba uint8 (h, w, 4), normal uint8 (h, w, 3)) at the cell resolution."""
        a = self.alpha.reshape(self.h, SS, self.w, SS).mean((1, 3))
        pre = (self.rgb * self.alpha[..., None]).reshape(self.h, SS, self.w, SS, 3).mean((1, 3))
        rgb = pre / np.maximum(a[..., None], 1e-4)
        h = self.height
        same_x = self.ident[:, 2:] == self.ident[:, :-2]
        same_y = self.ident[2:, :] == self.ident[:-2, :]
        gx = np.zeros_like(h); gy = np.zeros_like(h)
        gx[:, 1:-1] = np.where(same_x & (self.ident[:, 2:] > 0), (h[:, 2:] - h[:, :-2]) * 0.5, 0)
        gy[1:-1, :] = np.where(same_y & (self.ident[2:, :] > 0), (h[2:, :] - h[:-2, :]) * 0.5, 0)
        if self.wrap_u:
            gx[:, 0] = (h[:, 1] - h[:, -1]) * 0.5; gx[:, -1] = (h[:, 0] - h[:, -2]) * 0.5
        gx = gx.reshape(self.h, SS, self.w, SS).mean((1, 3)) * SS
        gy = gy.reshape(self.h, SS, self.w, SS).mean((1, 3)) * SS
        n = np.stack([-gx * normal_strength, gy * normal_strength, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        covered = a > 0.02
        if covered.any() and not covered.all():
            _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
            rgb = rgb[iy, ix]; n = n[iy, ix]
        rgba = np.dstack([(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8),
                          (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)])
        nrm = ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)
        return rgba, nrm


# ------------------------------------------------------------ leaf shapes (relative half width over t)
def shape_ellipse(p=0.8, tip=0.35, base=0.0):
    def f(t):
        return max(base * (1 - t), math.sin(math.pi * min(t * 1.0, 1.0)) ** p * (1 - tip * t))
    return f


def shape_ovate(peak=0.35, p=0.9):
    """Widest at `peak`, rounded base, pointed tip."""
    def f(t):
        if t < peak:
            return math.sin(0.5 * math.pi * t / peak) ** 0.55
        u = (t - peak) / (1 - peak)
        return max(0.0, math.cos(0.5 * math.pi * u)) ** p
    return f


def shape_heart(peak=0.22):
    def f(t):
        if t < peak:
            return 0.55 + 0.45 * math.sin(0.5 * math.pi * t / peak)
        u = (t - peak) / (1 - peak)
        return max(0.0, math.cos(0.5 * math.pi * u)) ** 1.1
    return f


def shape_sword(base=0.75, tip_from=0.7):
    def f(t):
        w = base + (1 - base) * min(t / 0.25, 1.0)
        if t > tip_from:
            w *= max(0.0, 1 - ((t - tip_from) / (1 - tip_from))) ** 0.8
        return w
    return f


def shape_blade(p=1.0):
    def f(t):
        return max(0.0, (1 - t)) ** p * min(1.0, 0.6 + t * 4)
    return f


def shape_petal(peak=0.6, base=0.25, p=0.6, tip_round=0.5):
    """Rounded petal: narrow claw at the base, widest at `peak`, rounded (tip_round 1) or pointed (0) tip."""
    def f(t):
        if t < peak:
            return base + (1 - base) * math.sin(0.5 * math.pi * t / peak) ** p
        u = (t - peak) / (1 - peak)
        return max(0.0, 1 - u ** (1.5 + 2.5 * tip_round)) ** (0.5 + 0.5 * (1 - tip_round))
    return f


# ------------------------------------------------------------ styles
def leaf_style(base, tip, rib=None, rib_w=0.05, vein=None, veins=7, vein_slant=0.55, vein_amt=0.35,
               edge=None, edge_w=0.0, edge_noise=0.3, spots=None, spot_amt=0.0, spot_scale='mid', spot_thr=1.0,
               bands=None, band_freq=0.0, band_amt=0.0, gloss=0.2, mottle=0.12, dark_edge=0.25, serr=0.0, serr_n=12,
               centre=None, centre_w=0.0, groove=0.25, dome=0.6, light_side=1.0, tip_dry=None):
    base, tip = lin(base), lin(tip)

    def style(t, s, x, y, rnd, cv):
        k = len(t)
        br = rnd.get('bright', 1.0)
        a = np.abs(s)
        col = mix(base, tip, np.clip(t, 0, 1) ** 0.8)
        lo = cv.lo[y, x]; mid = cv.mid[y, x]; hi = cv.hi[y, x]
        col = col * (1 + mottle * lo)[:, None]
        alpha = None
        if serr > 0:
            # serrated margin: notches cut into the edge
            tooth = np.abs(np.mod(t * serr_n + 0.5 * (s > 0), 1.0) - 0.5) * 2
            alpha = (a < 1 - serr * tooth).astype(np.float32)
        if centre is not None:
            m = smoothstep(centre_w + 0.12, centre_w - 0.05, a + 0.08 * mid) * smoothstep(0.98, 0.7, t)
            col = mix(col, lin(centre), m * 0.85)
        if bands is not None:
            ph = band_freq * t + 0.9 * a + 0.18 * mid + rnd.get('phase', 0.0)
            b = smoothstep(0.25, 0.65, 0.5 + 0.5 * np.sin(2 * math.pi * ph))
            col = mix(col, lin(bands), b * band_amt)
        vm = np.zeros(k, np.float32)
        if vein is not None:
            ph = np.mod(veins * t - vein_slant * a * veins / 6.0 + rnd.get('phase', 0.0), 1.0)
            vm = smoothstep(0.08, 0.0, np.abs(ph - 0.5) - 0.42) * smoothstep(0.98, 0.6, a) * smoothstep(0.02, 0.12, t)
            col = mix(col, lin(vein), vm * vein_amt)
        if spots is not None:
            field = {'mid': mid, 'hi': hi, 'lo': lo}[spot_scale]
            sm = smoothstep(spot_thr, spot_thr + 0.35, field) * smoothstep(0.98, 0.75, a)
            col = mix(col, lin(spots), sm * spot_amt)
        if edge is not None and edge_w > 0:
            ew = edge_w * (1 + edge_noise * lo)
            em = smoothstep(1 - ew - 0.06, 1 - ew + 0.02, a)
            col = mix(col, lin(edge), em)
        if tip_dry is not None:
            col = mix(col, lin(tip_dry), smoothstep(0.8, 1.0, t + 0.05 * mid) * 0.8)
        rm = np.zeros(k, np.float32)
        if rib is not None:
            rm = smoothstep(rib_w, rib_w * 0.4, a) * smoothstep(1.0, 0.6, t)
            col = mix(col, lin(rib), rm * 0.8)
        side = np.where(s * light_side > 0, 1.0, 0.0)
        hl = gloss * side * smoothstep(0.05, 0.3, a) * smoothstep(0.95, 0.45, a) * smoothstep(0.0, 0.25, t) * \
            smoothstep(1.0, 0.6, t) * (0.7 + 0.3 * mid)
        col = col * (1 - dark_edge * a ** 4)[:, None] + hl[:, None] * 0.35
        col = col * br
        h = dome * np.sqrt(np.clip(1 - a * a, 0, 1)) - groove * smoothstep(rib_w * 1.5, 0, a) + 0.12 * vm + \
            0.03 * hi
        return col, h, alpha
    return style


def petal_style(inner, mid_c, outer, edge=None, edge_w=0.0, veins=None, vein_n=7, vein_amt=0.3, inner_t=0.25,
                outer_t=0.75, cup=0.4, mottle=0.08, dark_edge=0.12, spots=None, spot_amt=0.0, stripe=None,
                stripe_w=0.25):
    inner, mid_c, outer = lin(inner), lin(mid_c), lin(outer)

    def style(t, s, x, y, rnd, cv):
        a = np.abs(s)
        col = np.where((t < inner_t)[:, None], mix(inner, mid_c, smoothstep(0, inner_t, t)),
                       mix(mid_c, outer, smoothstep(inner_t, outer_t, t)))
        lo = cv.lo[y, x]; mid = cv.mid[y, x]
        col = col * (1 + mottle * lo)[:, None]
        if stripe is not None:   # a central stripe up the petal (tulip flame, impatiens eye)
            m = smoothstep(stripe_w + 0.1, stripe_w - 0.05, a + 0.1 * mid) * smoothstep(0.95, 0.5, t)
            col = mix(col, lin(stripe), m * 0.8)
        if veins is not None:
            ph = np.mod(s * vein_n * 0.5 + 0.08 * mid, 1.0)
            vm = smoothstep(0.12, 0.0, np.abs(ph - 0.5) - 0.38) * smoothstep(0.95, 0.4, t)
            col = mix(col, lin(veins), vm * vein_amt)
        if spots is not None:
            sm = smoothstep(1.0, 1.4, cv.hi[y, x]) * smoothstep(0.7, 0.2, t)
            col = mix(col, lin(spots), sm * spot_amt)
        if edge is not None:
            em = smoothstep(1 - edge_w - 0.05, 1 - edge_w + 0.03, np.maximum(a, t ** 3) + 0.08 * mid)
            col = mix(col, lin(edge), em)
        col = col * (1 - dark_edge * a ** 3)[:, None] * rnd.get('bright', 1.0)
        h = cup * (1 - a * a) * smoothstep(0, 0.3, t) + 0.04 * mid
        return col, h, None
    return style


def flat_style(rgb, jitter=0.0):
    rgb = lin(rgb)

    def style(t, s, x, y, rnd, cv):
        col = np.repeat(rgb[None], len(t), 0) * (1 + jitter * cv.mid[y, x])[:, None] * rnd.get('bright', 1.0)
        return col, 0.5 * np.sqrt(np.clip(1 - s * s, 0, 1)), None
    return style


def stem_style(dark, light, knots=0.0):
    dark, light = lin(dark), lin(light)

    def style(t, s, x, y, rnd, cv):
        col = mix(dark, light, smoothstep(0.9, -0.3, s)) * (1 + 0.1 * cv.mid[y, x])[:, None]
        col = col * rnd.get('bright', 1.0)
        return col, 0.8 * np.sqrt(np.clip(1 - s * s, 0, 1)), None
    return style
