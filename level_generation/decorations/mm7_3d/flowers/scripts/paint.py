"""Procedural atlas painting (numpy, no external images), adapted from the MM6 flower atlas
(../mm6_new_sorpigal_3d/flowers/scripts/make_atlas.py): polygons stamped back to front into named atlas regions with a
colour gradient and a height (ridge, cup) from which the tangent-space normal map is derived. Region-local coordinates
run 0..1 with v down. Every painter takes the canvas, a region name and a numpy random generator."""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from common import ATLAS, REGIONS

SS = 2


class Canvas:
    def __init__(self):
        n = ATLAS * SS
        self.color = np.zeros((n, n, 3), np.float32)
        self.alpha = np.zeros((n, n), np.float32)
        self.height = np.zeros((n, n), np.float32)
        self.tags = {}

    def stamp(self, region, points, rgb_top, rgb_base, ridge=0.0, cup=0.0, alpha=1.0, base_h=0.4, grad=None):
        """Polygon (region-local, 0..1, v down) with colour blended from rgb_base at the bottom of its bounding box to
        rgb_top at the top; ridge raises its spine, cup its middle."""
        rx0, ry0, rx1, ry1 = [c * SS for c in REGIONS[region]]
        w, h = rx1 - rx0, ry1 - ry0
        pts = [(rx0 + x * w, ry0 + y * h) for x, y in points]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, x1 = int(max(min(xs) - 2, rx0)), int(min(max(xs) + 2, rx1))
        y0, y1 = int(max(min(ys) - 2, ry0)), int(min(max(ys) + 2, ry1))
        if x1 <= x0 or y1 <= y0:
            return
        image = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(image).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
        mask = np.asarray(image, np.float32) / 255.0 * alpha
        if mask.max() == 0:
            return
        if grad is None:
            top, bottom = min(ys), max(ys)
            yy = np.clip((np.arange(y0, y1)[:, None] - top) / max(bottom - top, 1.0), 0, 1) * np.ones((1, x1 - x0))
        else:                           # along the axis from grad[0] (rgb_base) to grad[1] (rgb_top)
            (bx, by), (tx, ty) = [(rx0 + x * w, ry0 + y * h) for x, y in grad]
            dx, dy = tx - bx, ty - by
            ll = max(dx * dx + dy * dy, 1.0)
            gx = np.arange(x0, x1)[None, :] - bx
            gy = np.arange(y0, y1)[:, None] - by
            yy = 1.0 - np.clip((gx * dx + gy * dy) / ll, 0, 1)
        rgb = (np.array(rgb_top, np.float32)[None, None] * (1 - yy[..., None])
               + np.array(rgb_base, np.float32)[None, None] * yy[..., None])
        distance = ndimage.distance_transform_edt(mask > 0.5)
        dmax = max(distance.max(), 1.0)
        hh = base_h + ridge * (distance / dmax) + cup * (1 - (distance / dmax - 0.5) ** 2 * 4)
        region_slice = (slice(y0, y1), slice(x0, x1))
        self.color[region_slice] = self.color[region_slice] * (1 - mask[..., None]) + rgb * mask[..., None]
        self.alpha[region_slice] = np.maximum(self.alpha[region_slice], mask)
        self.height[region_slice] = self.height[region_slice] * (1 - mask) + hh * mask

    def ellipse(self, region, centre, rx, ry, rgb_top, rgb_base, n=24, angle=0.0, **kw):
        cx, cy = centre
        ca, sa = math.cos(angle), math.sin(angle)
        pts = []
        for t in np.linspace(0, 2 * math.pi, n, endpoint=False):
            x, y = math.cos(t) * rx, math.sin(t) * ry
            pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
        self.stamp(region, pts, rgb_top, rgb_base, **kw)

    def grade(self, region, gain):
        x0, y0, x1, y1 = [c * SS for c in REGIONS[region]]
        self.color[y0:y1, x0:x1] = np.clip(self.color[y0:y1, x0:x1] * np.array(gain, np.float32), 0, 1)

    def save(self, base_path, normal_path):
        def down(a):
            return np.asarray(Image.fromarray(a.astype(np.float32)).resize((ATLAS, ATLAS), Image.BOX))
        premult = [down(self.color[..., c] * self.alpha) for c in range(3)]
        a = down(self.alpha)
        rgb = np.stack([p / np.maximum(a, 1e-4) for p in premult], -1)
        h = down(self.height * self.alpha)
        gy, gx = np.gradient(ndimage.gaussian_filter(h, 0.8))
        n = np.stack([-gx * 6.0, gy * 6.0, np.ones_like(h)], -1)          # image rows go down: green = up
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        covered = a > 0.02
        _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
        rgb = np.clip(rgb[iy, ix], 0, 1)
        nrm = n[iy, ix]
        Image.fromarray(np.dstack([(rgb * 255 + 0.5).astype(np.uint8),
                                   (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)]), 'RGBA').save(base_path)
        Image.fromarray(((nrm * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8), 'RGB').save(normal_path)


def jitter(rng, rgb, amount):
    return [min(max(c * (1 + rng.uniform(-amount, amount)), 0.0), 1.0) for c in rgb]


def mix(a, b, t):
    return [x * (1 - t) + y * t for x, y in zip(a, b)]


def scale(rgb, k):
    return [min(c * k, 1.0) for c in rgb]


# --- foliage ---------------------------------------------------------------------------------------------------------

def leaf(cv, region, base, angle, length, width, bend, rgb_top, rgb_base, ridge=0.6, steps=12, shape='lance', **kw):
    """Leaf from `base` along `angle` (radians, 0 = up the image), curving by `bend`. Shapes: lance (pointed, widest
    low), oval (rounded), strap (grass blade, even width), needle."""
    left, right = [], []
    px, py = base
    a_prev = angle
    for k in range(steps + 1):
        t = k / steps
        a = angle + bend * t
        if k:
            px += math.sin(a_prev) * length / steps
            py -= math.cos(a_prev) * length / steps
        a_prev = a
        if shape == 'oval':
            w = width * math.sin(math.pi * min(t * 0.98 + 0.02, 1.0)) ** 0.55
        elif shape == 'strap':
            w = width * (1.0 if t < 0.8 else max((1 - t) / 0.2, 0.0) ** 0.8) * (0.75 if t < 0.04 else 1.0)
        elif shape == 'needle':
            w = width * (1 - t)
        else:
            w = width * (math.sin(math.pi * min(t * 1.05, 1.0)) ** 0.7) * (1 - 0.35 * t)
        nx, ny = math.cos(a), math.sin(a)
        left.append((px - nx * w * 0.5, py - ny * w * 0.5))
        right.append((px + nx * w * 0.5, py + ny * w * 0.5))
    kw.setdefault('grad', (base, (px, py)))
    cv.stamp(region, left + right[::-1], rgb_top, rgb_base, ridge=ridge, **kw)
    return left, right


def veined_leaf(cv, rng, region, base, angle, length, width, bend, body, dark, vein, shape='oval', veins=5):
    """Broad leaf with a pale midrib and side veins."""
    left, right = leaf(cv, region, base, angle, length, width, bend, jitter(rng, body, 0.06), jitter(rng, dark, 0.08),
                       ridge=0.5, steps=14, shape=shape)
    mid = [((l[0] + r[0]) / 2, (l[1] + r[1]) / 2) for l, r in zip(left, right)]
    thin = width * 0.035
    for a_, b_ in zip(mid[:-3], mid[1:-2]):
        cv.stamp(region, [(a_[0] - thin, a_[1]), (a_[0] + thin, a_[1]), (b_[0] + thin, b_[1]), (b_[0] - thin, b_[1])],
                 vein, vein, ridge=0.1, base_h=0.9)
    for k in range(1, veins + 1):
        i = int(k / (veins + 1) * (len(mid) - 3))
        for side in (left, right):
            m, e = mid[i], side[min(i + 2, len(side) - 1)]
            ex, ey = m[0] + (e[0] - m[0]) * 0.85, m[1] + (e[1] - m[1]) * 0.85
            cv.stamp(region, [(m[0], m[1] - thin), (ex, ey - thin * 0.5), (ex, ey + thin * 0.5), (m[0], m[1] + thin)],
                     mix(vein, body, 0.4), mix(vein, body, 0.4), base_h=0.8)


def blade_strip(cv, rng, region, body, edge, base, stripe, tip=0.12, stripes=1, speckle=None, light_side=0.12):
    """One grass blade filling a long strip region: u across the blade (opaque to the region edges so strip
    segments meet without gaps), v from the pointed tip (0) to the base (1). Darker edges, pale midrib stripe(s),
    the left half a little lighter; optional pale speckles (flower03)."""
    outline = [(0.0, 1.0), (1.0, 1.0), (1.0, tip * 1.4), (0.56, 0.006), (0.44, 0.006), (0.0, tip * 1.4)]
    cv.stamp(region, outline, edge, mix(edge, base, 0.7), ridge=0.0)
    inner = [(0.12, 1.0), (0.88, 1.0), (0.88, tip * 1.6), (0.53, 0.03), (0.47, 0.03), (0.12, tip * 1.6)]
    cv.stamp(region, inner, body, base, ridge=0.6)
    lit = [(0.12, 1.0), (0.5, 1.0), (0.5, 0.03), (0.47, 0.03), (0.12, tip * 1.6)]
    cv.stamp(region, lit, scale(body, 1 + light_side), scale(base, 1 + light_side), ridge=0.6, alpha=0.6)
    centres = [0.5] if stripes == 1 else [0.3, 0.5, 0.7]
    for c in centres:
        w = 0.05 if c == 0.5 else 0.03
        cv.stamp(region, [(c - w, 1.0), (c + w, 1.0), (c + w * 0.4, 0.06), (c - w * 0.4, 0.06)], stripe,
                 mix(stripe, base, 0.6), ridge=0.2, base_h=0.95, alpha=0.85 if c == 0.5 else 0.5)
    if speckle is not None:
        for k in range(160):
            x, y = rng.uniform(0.15, 0.85), rng.uniform(0.12, 0.95)
            cv.ellipse(region, (x, y), 0.06, 0.004, speckle, speckle, n=8, alpha=0.7, base_h=0.9)


def tuft(cv, rng, region, count, body, base, stripe, spread=1.2, length=(0.6, 0.95), width=(0.035, 0.06), droop=0.6,
         origin=0.5, shape='strap'):
    """Many blades fanning from the bottom centre of a card (for crossed tuft cards and fill)."""
    for k in range(count):
        side = rng.uniform(-1, 1)
        angle = side * spread * 0.6 + rng.normal(0, 0.1)
        bx = origin + rng.normal(0, 0.05)
        ln = rng.uniform(*length) * (1 - 0.3 * abs(side))
        wd = rng.uniform(*width)
        depth = 0.75 + 0.5 * rng.uniform()
        bend = side * droop + rng.normal(0, 0.12)
        leaf(cv, region, (bx, 1.0), angle, ln, wd, bend, jitter(rng, scale(body, depth), 0.06),
             jitter(rng, base, 0.1), ridge=0.8, steps=12, shape=shape)
        leaf(cv, region, (bx, 1.0), angle, ln * 0.93, wd * 0.18, bend, scale(stripe, depth), base, ridge=0.2,
             steps=12, shape=shape, alpha=0.7)


def stem(cv, region, top, base, x0=0.02, x1=0.10):
    cv.stamp(region, [(x0, 0.0), (x1, 0.0), (x1, 1.0), (x0, 1.0)], top, base, ridge=0.5)


# --- flower heads (centred at 0.5, 0.5; petals within radius R so that a 5-gon over the slot still holds them) -------

R = 0.40


def ray_head(cv, rng, region, rays, petal, petal_base, centre, centre_dark, ray_len=1.0, ray_w=0.24, notch=False,
             pointed=False, disc=0.22, disc_dots=None, layers=1, edge=None, cup=0.3, rot=0.0, tips_light=None):
    """Radial flower seen face on: `rays` petals (rounded, notched or pointed), a disc of `disc` x R."""
    cx = cy = 0.5
    for layer in range(layers):
        off = (layer * 0.5 + rot) / rays
        shrink = 1.0 - 0.14 * layer
        for k in range(rays):
            a = (k + off) / rays * 2 * math.pi + rng.normal(0, 0.04)
            length = R * ray_len * shrink * rng.uniform(0.9, 1.0)
            w = R * ray_w
            pts = []
            for s in np.linspace(0, 1, 11):
                r = R * disc * 0.6 + (length - R * disc * 0.6) * s
                if pointed:
                    ww = w * math.sin(math.pi * min(s * 0.9 + 0.1, 1.0)) ** 0.8 * (1 - 0.15 * s)
                else:
                    ww = w * math.sin(math.pi * min(s * 0.62 + 0.12, 1.0)) ** 0.5
                    if s > 0.9:
                        ww *= math.sqrt(max(1 - (s - 0.9) / 0.1, 0.0)) * 0.6 + 0.4
                pts.append((r, ww))
            if notch:
                tip = [(length * 0.93, 0.0)]
                outline = [(p[0], -p[1]) for p in pts] + tip + [(p[0], p[1]) for p in pts[::-1]]
            else:
                outline = [(p[0], -p[1]) for p in pts] + [(length + (R * 0.04 if not pointed else 0), 0.0)] + \
                          [(p[0], p[1]) for p in pts[::-1]]
            ca, sa = math.cos(a), math.sin(a)
            poly = [(cx + r * ca - q * sa, cy + r * sa + q * ca) for r, q in outline]
            k_light = 1.0 - 0.1 * layer + rng.uniform(-0.05, 0.05)
            tipxy = (cx + length * ca, cy + length * sa)
            cv.stamp(region, poly, jitter(rng, scale(petal, k_light), 0.04), jitter(rng, petal_base, 0.05), cup=cup,
                     grad=((cx, cy), tipxy))
            if edge is not None:            # darker rim (flower09 star petals)
                rim = [(cx + r * ca - q * sa, cy + r * sa + q * ca) for r, q in outline]
                inner = [(cx + (r * 0.98) * ca - (q * 0.62) * sa, cy + (r * 0.98) * sa + (q * 0.62) * ca)
                         for r, q in outline]
                cv.stamp(region, rim, edge, edge, cup=cup, alpha=0.9)
                cv.stamp(region, inner, jitter(rng, scale(petal, k_light), 0.03), petal_base, cup=cup,
                         grad=((cx, cy), tipxy))
            # veins: a few thin darker lines from the root
            for dv in (-0.25, 0.0, 0.25):
                q0 = w * dv
                cv.stamp(region, [(cx + r * ca - q * sa, cy + r * sa + q * ca) for r, q in
                                  ((R * disc, q0 - 0.002), (length * 0.8, q0 * 1.6 - 0.001),
                                   (length * 0.8, q0 * 1.6 + 0.001), (R * disc, q0 + 0.002))],
                         mix(petal_base, petal, 0.3), petal_base, alpha=0.35)
    if disc > 0:
        cv.ellipse(region, (cx, cy), R * disc, R * disc, centre, centre_dark, n=30, cup=0.5, base_h=0.6)
        if disc_dots is not None:
            for k in range(int(60 * disc / 0.2)):
                r = R * disc * 0.9 * math.sqrt(rng.uniform())
                a = rng.uniform(0, 2 * math.pi)
                cv.ellipse(region, (cx + math.cos(a) * r, cy + math.sin(a) * r), R * 0.022, R * 0.022, disc_dots,
                           disc_dots, n=7, base_h=0.9)


def rosette(cv, rng, region, outer, inner, core, rings=4, per_ring=(9, 8, 7, 5), frill=0.0, edge=None, radius=R):
    """Double flower seen from above: rings of rounded overlapping petals from outer (light) to inner (darker) and a
    tight spiral core; optional tinted outer edge (flower04)."""
    cx = cy = 0.5
    for ring in range(rings):
        count = per_ring[min(ring, len(per_ring) - 1)]
        r0 = radius * (0.72 - 0.17 * ring)
        w = radius * (0.40 - 0.05 * ring)
        turn = rng.uniform(0, 2 * math.pi)
        t = ring / max(rings - 1, 1)
        for k in range(count):
            a = turn + 2 * math.pi * k / count
            px, py = cx + math.cos(a) * r0, cy + math.sin(a) * r0
            pts = []
            for q in np.linspace(0, 2 * math.pi, 18, endpoint=False):
                wob = 1.0 + frill * math.sin(q * 5 + rng.uniform(0, 6))
                pts.append((px + math.cos(q) * w * wob, py + math.sin(q) * w * 0.85 * wob))
            col = mix(outer, inner, t)
            if edge is not None and ring == 0:
                cv.stamp(region, pts, jitter(rng, edge, 0.06), jitter(rng, scale(edge, 0.7), 0.06), cup=0.5,
                         grad=((cx, cy), (px + math.cos(a) * w, py + math.sin(a) * w)))
                pts = [(px + (x - px) * 0.8 - math.cos(a) * w * 0.15, py + (y - py) * 0.8 - math.sin(a) * w * 0.15)
                       for x, y in pts]
            cv.stamp(region, pts, jitter(rng, col, 0.05), jitter(rng, scale(col, 0.62), 0.05), cup=0.6,
                     grad=((cx, cy), (px + math.cos(a) * w, py + math.sin(a) * w)))
    for k in range(12):
        t = k / 12
        a = t * 4 * math.pi
        r = radius * 0.16 * (1 - t)
        cv.ellipse(region, (cx + math.cos(a) * r, cy + math.sin(a) * r), radius * 0.08, radius * 0.065,
                   scale(core, 1.1), scale(core, 0.6), n=10, cup=0.3)


def petal_band(cv, rng, region, top, bottom, rows=2, count=7, frill=0.0, edge=None, tint_bottom=None):
    """Side of a double bloom, wrapped round a lathe: rows of rounded petal backs across the strip (tileable in u),
    their tops scalloped into the alpha (v 0 = top of the bloom side, 1 = bottom)."""
    for row in range(rows):
        y_top = 0.05 + row * 0.38
        off = 0.5 * row
        for k in range(-1, count + 1):
            cx = (k + off + rng.uniform(-0.08, 0.08)) / count
            w = 0.62 / count
            pts = [(cx - w, 1.0), (cx + w, 1.0)]
            for q in np.linspace(0, math.pi, 12):
                wob = 1.0 + frill * math.sin(q * 6 + rng.uniform(0, 6))
                pts.append((cx + math.cos(q) * w * wob, y_top + (1 - math.sin(q)) * 0.25 + 0.02 * wob))
            col_top = jitter(rng, top, 0.05)
            col_bottom = jitter(rng, bottom if tint_bottom is None or row == 0 else tint_bottom, 0.06)
            cv.stamp(region, [(min(max(x, 0.0), 1.0), y) for x, y in pts], col_top, col_bottom, cup=0.6)
            if edge is not None:
                cv.stamp(region, [(min(max(cx + math.cos(q) * w * 0.98, 0.0), 1.0),
                                   y_top + (1 - math.sin(q)) * 0.25 + 0.01) for q in np.linspace(0, math.pi, 12)]
                         + [(cx + w * 0.8, y_top + 0.2), (cx - w * 0.8, y_top + 0.2)], edge, edge, alpha=0.6)


def bells(cv, rng, region, colour, inner, spots, rows=10, card=False):
    """Foxglove spike, painted near white (tinted per spike through COLOR_0). card=True: the spike's silhouette for the
    far crossed cards (rows of bells hanging left, right and facing out, green buds at the tip); card=False: the
    core wrapped round a thin lathe (rows of bells all round, tileable in u)."""
    green, green_dark = [0.42, 0.62, 0.30], [0.16, 0.30, 0.12]
    if card:
        cv.stamp(region, [(0.49, 0.0), (0.51, 0.0), (0.515, 1.0), (0.485, 1.0)], green, green_dark)
    else:
        cv.stamp(region, [(0, 0.1), (1, 0.1), (1, 1), (0, 1)], scale(colour, 0.55), scale(colour, 0.42))
    for row in range(rows):
        grow = 0.5 + 0.5 * (row + 1) / rows
        y = 0.12 + row * (0.84 / rows)
        h = 0.84 / rows * 1.45 * grow
        if card:
            half = 0.1 + 0.3 * grow ** 1.3
            for side in (-1, 1):
                bell(cv, rng, region, 0.5 + side * half * 0.62, y, half * 0.95, h, colour, inner, spots,
                     lean=side * 0.25)
            bell(cv, rng, region, 0.5 + rng.uniform(-0.04, 0.04), y + h * 0.15, half * 0.9, h * 0.9, colour, inner,
                 spots)
        else:
            for k in range(-1, 6):
                bell(cv, rng, region, (k + 0.5 * (row % 2)) / 5, y, 0.24, h, colour, inner, spots)
    for k in range(9):                                           # green buds at the top
        y = 0.005 + k * 0.014
        if card:
            cv.ellipse(region, (0.5 + rng.normal(0, 0.02), y + 0.01), 0.03 + 0.008 * k, 0.012, green, green_dark,
                       n=10, cup=0.4)
        else:
            for j in range(5):
                cv.ellipse(region, ((j + 0.5 * (k % 2)) / 5, y + 0.01), 0.07, 0.012, green, green_dark, n=10)


def ruffled_petal(cv, rng, region, colour, base, streak, frill=0.08, width=0.86, veins=None):
    """Iris petal from the bottom centre (its root) to the top of the slot: broad ruffled blade, pale streak."""
    pts_l, pts_r = [], []
    for s in np.linspace(0, 1, 22):
        w = width * 0.5 * math.sin(math.pi * min(0.08 + s * 0.92, 1.0)) ** 0.6 * (0.3 + 0.7 * min(s * 2.2, 1.0))
        wob = 1.0 + frill * math.sin(s * 37 + rng.uniform(0, 6)) * min(s * 2, 1)
        y = 0.99 - s * 0.97
        pts_l.append((0.5 - w * wob, y))
        pts_r.append((0.5 + w * (2 - wob), y))
    cv.stamp(region, pts_l + pts_r[::-1], jitter(rng, colour, 0.04), jitter(rng, base, 0.05), cup=0.5)
    for k in range(9):                           # darker veins and lighter ruffle highlights
        x = 0.5 + rng.uniform(-0.3, 0.3)
        y0, y1 = rng.uniform(0.45, 0.7), rng.uniform(0.18, 0.32)
        col = scale(colour, 1.25) if k % 2 else (veins or scale(base, 0.9))
        cv.stamp(region, [(x - 0.012, y0), (x + 0.012, y0), (0.5 + (x - 0.5) * 1.2 + 0.02, y1),
                          (0.5 + (x - 0.5) * 1.2 - 0.02, y1)], col, col, alpha=0.45)
    cv.stamp(region, [(0.47, 0.98), (0.53, 0.98), (0.56, 0.35), (0.5, 0.2), (0.44, 0.35)], streak,
             mix(streak, base, 0.4), ridge=0.3, alpha=0.85)


def frond(cv, rng, region, base, angle, length, rgb, dark, leaflets=14, leaflet=0.05, bend=0.3):
    """Fern / needle spray: a thin rachis with paired needle leaflets."""
    left, right = leaf(cv, region, base, angle, length, 0.012, bend, rgb, dark, steps=10, shape='strap', ridge=0.2)
    mid = [((l[0] + r[0]) / 2, (l[1] + r[1]) / 2) for l, r in zip(left, right)]
    for k in range(leaflets):
        t = (k + 1) / (leaflets + 1)
        i = int(t * (len(mid) - 1))
        a = angle + bend * t
        ln = leaflet * (1 - 0.6 * t) * rng.uniform(0.8, 1.2)
        for side in (-1, 1):
            leaf(cv, region, mid[i], a + side * 1.0, ln, ln * 0.25, side * 0.2, jitter(rng, rgb, 0.08),
                 jitter(rng, dark, 0.1), steps=4, shape='needle', ridge=0.3)


def pad(cv, rng, region, body, dark, vein, notch=0.3):
    """Water-lily pad seen from above: a disc of radius R with a wedge slit toward the bottom, mottled with darker
    and lighter patches, branching veins, a glossy lighter rim and a few rust-tinged edges."""
    cx = cy = 0.5

    def wedge(r0, r1, a0, a1, n=40):
        return [(cx + math.cos(t) * r0, cy + math.sin(t) * r0) for t in np.linspace(a0, a1, n)][::-1] + \
               [(cx + math.cos(t) * r1, cy + math.sin(t) * r1) for t in np.linspace(a0, a1, n)]
    a0, a1 = math.pi / 2 + notch, math.pi / 2 + 2 * math.pi - notch
    cv.stamp(region, [(cx, cy)] + [(cx + math.cos(t) * R, cy + math.sin(t) * R) for t in np.linspace(a0, a1, 48)],
             jitter(rng, body, 0.05), jitter(rng, dark, 0.05), cup=0.25, grad=((cx, cy), (cx, cy - R)))
    for k in range(34):                                   # mottling
        t = rng.uniform(a0 + 0.1, a1 - 0.1)
        r = R * math.sqrt(rng.uniform(0.02, 0.85))
        px, py = cx + math.cos(t) * r, cy + math.sin(t) * r
        col = scale(body, rng.choice([0.6, 0.72, 1.25, 1.35]))
        cv.ellipse(region, (px, py), R * rng.uniform(0.06, 0.16), R * rng.uniform(0.04, 0.1), col, col, n=12,
                   angle=rng.uniform(0, 3.2), alpha=0.35)
    for k in range(13):                                   # radial veins with side branches
        t = a0 + (a1 - a0) * (k + 0.5) / 13
        ex, ey = cx + math.cos(t) * R * 0.93, cy + math.sin(t) * R * 0.93
        nx, ny = -math.sin(t) * 0.005, math.cos(t) * 0.005
        cv.stamp(region, [(cx + nx, cy + ny), (ex + nx * 0.5, ey + ny * 0.5), (ex - nx * 0.5, ey - ny * 0.5),
                          (cx - nx, cy - ny)], vein, vein, alpha=0.55, base_h=0.7)
        for f in (0.45, 0.7):
            bx, by = cx + math.cos(t) * R * f, cy + math.sin(t) * R * f
            for side in (-1, 1):
                tb = t + side * 0.35
                fx, fy = bx + math.cos(tb) * R * 0.18, by + math.sin(tb) * R * 0.18
                cv.stamp(region, [(bx, by - 0.002), (fx, fy - 0.0015), (fx, fy + 0.0015), (bx, by + 0.002)],
                         vein, vein, alpha=0.35, base_h=0.7)
    cv.stamp(region, wedge(R * 0.86, R, a0, a1), scale(body, 1.35), scale(body, 1.2), alpha=0.5)   # glossy rim
    for k in range(3):                                    # rust-tinged edge patches
        t = rng.uniform(a0, a1)
        cv.stamp(region, wedge(R * 0.93, R, t, t + rng.uniform(0.3, 0.7), 10), [0.52, 0.36, 0.16],
                 [0.40, 0.28, 0.12], alpha=0.45)
    # the slit: a darker line along each cut edge
    for t in (a0, a1):
        cv.stamp(region, [(cx, cy), (cx + math.cos(t) * R, cy + math.sin(t) * R),
                          (cx + math.cos(t + (0.04 if t == a0 else -0.04)) * R,
                           cy + math.sin(t + (0.04 if t == a0 else -0.04)) * R)], dark, dark, alpha=0.6)


def bell(cv, rng, region, cx, top, w, h, colour, inner, spots, lean=0.0):
    """One foxglove bell seen from three-quarters below: a tube from its stalk at (cx, top) widening down to a flared
    mouth with a spotted throat and a longer lower lip; painted near white for COLOR_0 tints. lean tilts it sideways."""
    def P(x, y):                      # bell-local (x across -0.5..0.5, y 0 top..1 mouth) -> region
        return (cx + (x + lean * y) * w, top + y * h)
    outline = [(-0.14, 0.0), (0.14, 0.0), (0.26, 0.35), (0.36, 0.7), (0.5, 0.9), (0.3, 1.0), (0.0, 0.97),
               (-0.3, 1.0), (-0.5, 0.88), (-0.36, 0.7), (-0.26, 0.35)]
    col = jitter(rng, colour, 0.03)
    cv.stamp(region, [P(x, y) for x, y in outline], col, scale(col, 0.7), cup=0.6, grad=(P(0, 0), P(0, 1)))
    cv.stamp(region, [P(x, y) for x, y in [(-0.06, 0.05), (0.04, 0.05), (0.02, 0.8), (-0.16, 0.8)]],
             scale(col, 1.08), scale(col, 0.95), alpha=0.5)                                   # light ridge
    throat = [(-0.36, 0.86), (-0.2, 0.74), (0.0, 0.71), (0.2, 0.74), (0.36, 0.86), (0.16, 0.92), (-0.16, 0.92)]
    cv.stamp(region, [P(x, y) for x, y in throat], inner, scale(inner, 0.75), cup=-0.3)
    for k in range(7):
        x, y = rng.uniform(-0.24, 0.24), rng.uniform(0.76, 0.9)
        sx, sy = P(x, y)
        cv.ellipse(region, (sx, sy), w * 0.03, h * 0.02, spots, spots, n=6, alpha=0.9)
    cv.stamp(region, [P(x, y) for x, y in [(-0.3, 0.97), (0.0, 0.94), (0.3, 0.97), (0.0, 1.0)]],
             scale(col, 1.05), col, alpha=0.8)                                                # lower lip highlight


