# Geometry helpers for the XD-02 L4 generator (gen.py). Numbers only; no project data here.
import math


def r(v):
    return int(round(v))


def pt(p):
    return [r(p[0]), r(p[1])]


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def length(a):
    return math.hypot(a[0], a[1])


def unit(a):
    l = length(a)
    return (a[0] / l, a[1] / l)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def left_normal(d):
    """Inward normal of a counter-clockwise polygon edge with direction d."""
    return (-d[1], d[0])


def line_intersect(p1, d1, p2, d2):
    den = d1[0] * d2[1] - d1[1] * d2[0]
    t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
    return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)


def inset_polygon(poly, w):
    """Each edge of a convex counter-clockwise polygon moved inward by w; returns the new corners."""
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        d = unit(sub(b, a))
        nrm = left_normal(d)
        lines.append((add(a, mul(nrm, w)), d))
    out = []
    for i in range(n):
        p1, d1 = lines[i - 1]
        p2, d2 = lines[i]
        out.append(line_intersect(p1, d1, p2, d2))
    return out


def rect_outline(cx, cy, w, h, angle_deg=0.0):
    """Counter-clockwise rectangle of width w (along the angle) and depth h, centred on (cx, cy)."""
    a = math.radians(angle_deg)
    u = (math.cos(a), math.sin(a))
    v = (-u[1], u[0])
    pts = []
    for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = (cx + u[0] * su * w / 2 + v[0] * sv * h / 2, cy + u[1] * su * w / 2 + v[1] * sv * h / 2)
        pts.append(pt(p))
    return pts


def ngon(cx, cy, radius, n, start_deg=0.0):
    return [pt((cx + radius * math.cos(math.radians(start_deg + 360.0 * k / n)),
                cy + radius * math.sin(math.radians(start_deg + 360.0 * k / n)))) for k in range(n)]
