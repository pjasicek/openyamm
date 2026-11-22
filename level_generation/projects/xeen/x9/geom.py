"""X9's drawing geometry (A5, 2026-11-20): island outlines from the design's `at`/`extent`, rim-to-rim link lengths,
the cloud's area. For the review only; the studio draws its own platforms at L2-L4 (X8's 13-16 point outlines)."""
import math

import numpy as np
from PIL import Image, ImageDraw

import design as D

SPACE = {s['id']: s for s in D.SPACES}


def castle_cloud(space, per_arc=5):
    """The castle's own cloud: a rounded rectangle 1,024 beyond the shell on every side, wobbled outward only."""
    import random
    cx, cy = space['at']
    w, h = space['extent']
    x0, y0, x1, y1 = cx - w / 2 - 1024, cy - h / 2 - 1024, cx + w / 2 + 1024, cy + h / 2 + 1024
    r = 1536
    rnd = random.Random(space['seed'])
    pts = []
    for ox, oy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for k in range(per_arc + 1):
            a = math.radians(a0 + 90 * k / per_arc)
            rr = r + rnd.uniform(0, 192)
            pts.append((ox + rr * math.cos(a), oy + rr * math.sin(a)))
    return pts


def blob(space, points=24):
    """A cloud outline: a squarish ellipse with a fixed-seed wobble (X8's platforms); the castle's a rounded rectangle."""
    if space['kind'] == 'castle':
        return castle_cloud(space)
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


def castle_walls(space):
    cx, cy = space['at']
    w, h = space['extent']
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


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
    if link['id'] == 'link:unseen_way':
        # due north from the 9N sign's line (x of the brink) to the landing
        x = a['at'][0]
        start = ray_exit(pa, (x, a['at'][1]), (x, b['at'][1]))
        end = ray_exit(pb, (x, b['at'][1]), (x, a['at'][1]))
        return start, end
    if link['style'] == 'road':
        # the Xeen road runs due north on x 0 from the landing to the gate
        start = ray_exit(pa, (0, a['at'][1]), (0, b['at'][1]))
        end = ray_exit(pb, (0, b['at'][1]), (0, a['at'][1]))
        return start, end
    if link['style'] == 'gate':
        g = place_at(next(p for p in D.PLACES if p['id'] == 'poi:castle_gate'), polys)
        return (g[0], g[1] - 512), g
    return ray_exit(pa, a['at'], b['at']), ray_exit(pb, b['at'], a['at'])


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


def cloud_mask(polys, include=('cloud',), with_necks=True):
    w, h = int(2 * D.HALF[0] / RES), int(2 * D.HALF[1] / RES)
    img = Image.new('L', (w, h), 0)
    dr = ImageDraw.Draw(img)
    for s in D.SPACES:
        if s['kind'] in include:
            dr.polygon([to_px(p) for p in polys[s['id']]], fill=255)
    if with_necks:
        for l in D.LINKS:
            if l['style'] in ('neck', 'causeway') and SPACE[l['a']]['kind'] in include:
                p, q = link_ends(l, polys)
                dr.polygon([to_px(v) for v in capsule(p, q, l['width'] if l['style'] == 'neck' else max(l['width'], 768))],
                           fill=255)
    return np.array(img) > 0


def rim_point(poly, at, side):
    """The rim of an outline straight north or south of its middle."""
    far = {'n': (at[0], at[1] + 40000), 's': (at[0], at[1] - 40000)}[side]
    return ray_exit(poly, at, far)


def place_at(p, polys):
    s = SPACE[p['space']]
    if 'gate_off' in p:
        cx, cy = s['at']
        return (cx, cy - s['extent'][1] / 2 + p['gate_off'])
    dx, dy = p.get('off', (0, 0))
    if 'rim' in p:
        rx, ry = rim_point(polys[s['id']], s['at'], p['rim'])
        return (rx + dx, ry + dy)
    return (s['at'][0] + dx, s['at'][1] + dy)


def floor_of(sid):
    return SPACE[sid]['floor']
