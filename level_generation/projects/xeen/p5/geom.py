"""P5's drawing geometry (A5 sub-agent, 2026-11-21; copied from X9's geom.py): island outlines from the design's `at`/`extent`, rim-to-rim link lengths,
the cloud's area. For the review only; the studio draws its own platforms at L2-L4 (X8's 13-16 point outlines)."""
import math

import numpy as np
from PIL import Image, ImageDraw

import design as D

SPACE = {s['id']: s for s in D.SPACES}


def blob(space, points=24):
    """A cloud outline: a squarish ellipse with a fixed-seed wobble (X8's platforms); the castle's a rounded rectangle."""
    cx, cy = space['at']
    w, h = space['extent']
    rng = np.random.default_rng(space['seed'] * 7919)
    wob = rng.uniform(0.86, 1.10, points)
    wob = (wob + np.roll(wob, 1) + np.roll(wob, -1)) / 3.0
    out = []
    for i in range(points):
        a = 2 * math.pi * i / points + space['seed'] * 0.13
        c, s = math.cos(a), math.sin(a)
        # superellipse (n = 2.6) for a fuller cloud than an ellipse
        r = (abs(c) ** 2.6 / (w / 2) ** 2.6 + abs(s) ** 2.6 / (h / 2) ** 2.6) ** (-1 / 2.6)
        out.append((cx + r * c * wob[i], cy + r * s * wob[i]))
    return out


def ray_exit(poly, origin, target):
    """Where the segment origin->target leaves the polygon (origin inside); the last crossing toward the target."""
    ox, oy = origin
    dx, dy = target[0] - ox, target[1] - oy
    best = None
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - ox) * ey - (ay - oy) * ex) / den
        u = ((ax - ox) * dy - (ay - oy) * dx) / den
        if 0 <= t <= 1 and 0 <= u <= 1:
            if best is None or t < best:
                best = t
    if best is None:
        return origin
    return (ox + dx * best, oy + dy * best)


def outlines():
    return {s['id']: blob(s) for s in D.SPACES}


def link_ends(link, polys):
    a, b = SPACE[link['a']], SPACE[link['b']]
    pa, pb = polys[link['a']], polys[link['b']]
    if link['style'] == 'causeway':
        # straight north on x 0 from the last Rest Stop to the shrine's south rim
        start = ray_exit(pa, (0, a['at'][1]), (0, b['at'][1]))
        end = ray_exit(pb, (0, b['at'][1]), (0, a['at'][1]))
        return start, end
    # the cloud road runs along the ring's middle line, from each pad's anchor on it to the next one's
    return ray_exit(pa, a['anchor'], b['anchor']), ray_exit(pb, b['anchor'], a['anchor'])


def length(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def capsule(p, q, width, steps=8):
    """A rounded band from p to q (a cloud neck or a causeway) as a polygon."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / d * width / 2, dx / d * width / 2
    return [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]


RES = 32  # units per pixel for areas


def to_px(pt):
    return ((pt[0] + D.HALF[0]) / RES, (D.HALF[1] - pt[1]) / RES)


def point_in(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def bulges(polys):
    """A board off every pad stands on a small lobe of cloud pushed out from the road's outer edge: a capsule from
    the road's middle line to 160 past the board, 640 wide. Returns (board id, polygon, floor)."""
    out = []
    for p in D.PLACES:
        if p['kind'] != 'board' or any(point_in(p['at'], polys[s['id']]) for s in D.SPACES):
            continue
        x, y = p['at']
        # the nearest point on the ring's middle line
        r = D.RING
        if abs(abs(x) - r) < abs(abs(y) - r):
            q = (r if x > 0 else -r, y)
        else:
            q = (x, r if y > 0 else -r)
        dx, dy = x - q[0], y - q[1]
        d = math.hypot(dx, dy)
        tip = (x + dx / d * 160, y + dy / d * 160)
        out.append((p['id'], capsule(q, tip, 640), None))
    return out


def cloud_mask(polys):
    """Walkable cloud: the pads and the road ribbons between them."""
    w, h = int(2 * D.HALF[0] / RES), int(2 * D.HALF[1] / RES)
    img = Image.new('L', (w, h), 0)
    dr = ImageDraw.Draw(img)
    for s in D.SPACES:
        dr.polygon([to_px(p) for p in polys[s['id']]], fill=255)
    for l in D.LINKS:
        p, q = link_ends(l, polys)
        dr.polygon([to_px(v) for v in capsule(p, q, l['width'])], fill=255)
    for _, poly, _ in bulges(polys):
        dr.polygon([to_px(v) for v in poly], fill=255)
    return np.array(img) > 0


def rim_point(poly, at, side):
    """The rim of an outline straight north or south of its middle."""
    far = {'n': (at[0], at[1] + 40000), 's': (at[0], at[1] - 40000)}[side]
    return ray_exit(poly, at, far)


def place_at(p, polys=None):
    return p['at']


def floor_of(sid):
    return SPACE[sid]['floor']
