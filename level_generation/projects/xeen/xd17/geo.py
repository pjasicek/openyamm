"""XD-17 Shangri-La: the valley's shape (A5, 2026-11-21). One room open to the sky whose uneven floor (rooms.yml
`floor_points`) is the whole basin: the flat town floor, terraces with banks and ramps, the black cliffs rising to a
jagged crest, the back slope behind it and Mount Firestone's summit over the north-east rim. Two sheer bluffs stand
out of the room's outline into the valley: the south one holds the cave throat (to XD-16), the north-west one the back
passage (to X7's cleft). The ceiling (`ceiling_points`) is sky: just over the crest round the rim, high over the summit.
"""
import math

import places_l2 as L

STEP = 64


def H(*a):
    """A small deterministic jitter in [-1, 1] from integers."""
    v = 0
    for x in a:
        v = (v * 1103515245 + int(x) * 2654435761 + 12345) & 0x7fffffff
    v ^= v >> 13
    v = (v * 1274126177) & 0x7fffffff
    return (v % 2001) / 1000.0 - 1.0


def ccw(poly):
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
    return poly if a > 0 else list(reversed(poly))


# ---------------------------------------------------------------- the foot of the cliffs
def foot_ring():
    """The cliff foot, counter-clockwise, with the bluffs' fronts on it, densified to at most 768 a segment."""
    ring = list(L.FLOOR)                                   # clockwise from the west
    i = ring.index((-6016, 2816))
    ring[i + 1:i + 1] = [L.WEDGE_FRONT[1], L.WEDGE_FRONT[0]]   # on the foot's straight segment to (-4864, 4224)
    j = ring.index((-1024, -5248))
    ring[j:j + 1] = [L.BLUFF_S[1], L.BLUFF_S[0]]
    ring = ccw(ring)
    fronts = {frozenset([L.BLUFF_S[0], L.BLUFF_S[1]]), frozenset([L.WEDGE_FRONT[0], L.WEDGE_FRONT[1]])}
    out = []
    for a, b in zip(ring, ring[1:] + ring[:1]):
        out.append(a)
        if frozenset([a, b]) in fronts:
            continue
        n = int(math.ceil(math.dist(a, b) / 1536))
        for k in range(1, n):
            out.append((round((a[0] + (b[0] - a[0]) * k / n) / 16) * 16, round((a[1] + (b[1] - a[1]) * k / n) / 16) * 16))
    return out


FOOT = foot_ring()


def ray_foot(theta):
    """Distance from the datum to the foot ring along the bearing theta (radians)."""
    dx, dy = math.cos(theta), math.sin(theta)
    best = None
    for (x0, y0), (x1, y1) in zip(FOOT, FOOT[1:] + FOOT[:1]):
        ex, ey = x1 - x0, y1 - y0
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = (x0 * ey - y0 * ex) / den
        s = (x0 * dy - y0 * dx) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best


def crest_of(theta, notch=True):
    hc = L.crest_height(math.cos(theta), math.sin(theta))
    if not notch:
        return hc
    # the falls' notch: the crest dips to about 1,900 over the lip (bearing about 21 degrees)
    fall = math.degrees(math.atan2(L.FALL['lip'][1], L.FALL['lip'][0]))
    d = abs((math.degrees(theta) - fall + 180) % 360 - 180)
    if d < 6:
        hc -= (hc - 1900) * (1 - d / 6)
    return hc


def reach_of(hc):
    return max(1536.0, hc / 1.35)


BACK = 640
# Profile from the foot outward: (share of the reach, share of the crest height).
PROFILE = [(0.0, 0.0), (0.45, 0.42), (1.0, 1.0)]


def cliff_height(x, y):
    """The cliff's height (no jitter) at a point beyond the foot; 0 inside."""
    th = math.atan2(y, x)
    rf = ray_foot(th)
    r = math.hypot(x, y)
    d = r - rf
    if d <= 0:
        return 0.0
    hc = crest_of(th)
    rc = reach_of(hc)
    t = d / rc
    if t >= 1:
        back = min(1.0, (d - rc) / BACK)
        h0 = crest_of(th, False) - 500
        return hc + (h0 - hc) * back
    for (t0, z0), (t1, z1) in zip(PROFILE, PROFILE[1:]):
        if t0 <= t <= t1:
            return hc * (z0 + (z1 - z0) * (t - t0) / (t1 - t0))
    return hc


S = L.SUMMIT['at']
SUMMIT_RINGS = [(0, 5376), (448, 5632), (1280, 4480), (2304, 3200)]   # (radius, height); the crater in the middle
SUMMIT_OUT = 3072                                                      # the outline round it, at 2,400


def summit_height(x, y):
    r = math.dist((x, y), S)
    if r >= SUMMIT_OUT:
        return 0.0
    pts = SUMMIT_RINGS + [(SUMMIT_OUT, 2400)]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if r0 <= r <= r1:
            return z0 + (z1 - z0) * (r - r0) / (r1 - r0)
    return 0.0


def height(x, y):
    return max(cliff_height(x, y), summit_height(x, y))


# ---------------------------------------------------------------- the rings and the outline
def rings():
    """Points of the cliff by ring: for each ring (mid, crest) a list per foot point, None where the point is left
    out (round the summit)."""
    out = {n: [] for n in range(1, len(PROFILE))}
    for k, (fx, fy) in enumerate(FOOT):
        th = math.atan2(fy, fx)
        hc = crest_of(th)
        rc = reach_of(hc)
        ux, uy = math.cos(th), math.sin(th)
        for n, (t, z) in enumerate(PROFILE[1:], 1):
            jr = 128 * H(k, n, 1) if t < 1 else 96 * H(k, n, 1)
            jz = 0.04 * H(k, n, 2)
            d = t * rc + jr
            p = (round(fx + ux * d), round(fy + uy * d), round(hc * (z + jz)))
            if math.dist(p[:2], S) < SUMMIT_RINGS[-1][0] + 256:
                p = None
            out[n].append(p)
    return out


def outline_r(th):
    rf = ray_foot(th)
    r = rf + reach_of(crest_of(th, False)) + BACK
    dx, dy = math.cos(th), math.sin(th)
    b = dx * S[0] + dy * S[1]
    c = S[0] ** 2 + S[1] ** 2 - SUMMIT_OUT ** 2
    disc = b * b - c
    if disc > 0:
        r = max(r, b + math.sqrt(disc))
    return r


def outline_base():
    """The back of the crest, star-shaped from the datum, swollen round the summit (finer where it swells)."""
    ths = [math.radians(k * 10) for k in range(36)]
    for _ in range(3):
        out = []
        for i, t in enumerate(ths):
            out.append(t)
            t2 = ths[(i + 1) % len(ths)] + (2 * math.pi if i == len(ths) - 1 else 0)
            if abs(outline_r(t) - outline_r(t2)) > 700:
                out.append((t + t2) / 2)
        ths = out
    pts = []
    for th in ths:
        r = outline_r(th)
        pts.append((round(math.cos(th) * r / 16) * 16, round(math.sin(th) * r / 16) * 16))
    return pts


def seg_hit(a, b, c, d):
    """Intersection of segment ab with segment cd (point and the share along ab) or None."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a, b, c, d
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1)), t
    return None


def notch(poly, path_in, path_out):
    """Cut a notch into the outline: `path_in` runs from outside the outline inward to the notch's front (the first
    side, met first going counter-clockwise), `path_out` from the front back out. Each side's last leg is extended
    outward until it meets the outline."""
    def far(p0, p1):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        return (p1[0] + dx / n * 30000, p1[1] + dy / n * 30000)

    def hit(p0, p1):
        """Step from p1 along the leg's primitive direction (p0 to p1) until outside the outline."""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        gg = math.gcd(dx, dy)
        px, py = dx // gg, dy // gg
        q = p1
        while inside(poly, q):
            q = (q[0] + px, q[1] + py)
        best = None
        for i, (a, b) in enumerate(zip(poly, poly[1:] + poly[:1])):
            h = seg_hit(p0, far(p0, p1), a, b)
            if h and (best is None or h[1] < best[1]):
                best = (h[1], i)
        return best[0], best[1], q
    _, ia, pa = hit(path_in[1], path_in[0])
    _, ib, pb = hit(path_out[-2], path_out[-1])
    # keep the outline from just after ib round to ia, then the notch
    n = len(poly)
    keep = []
    k = (ib + 1) % n
    while True:
        keep.append(poly[k])
        if k == ia:
            break
        k = (k + 1) % n
    path = [q for q in list(path_in) + list(path_out) if inside(poly, q)]
    keep = [q for q in keep if math.dist(q, pa) > 600 and math.dist(q, pb) > 600]
    return keep + [pa] + path + [pb]


def outline():
    poly = outline_base()
    # the south bluff: west side in, front west to east, east side out
    poly = notch(poly, [L.BLUFF_S_SIDES[0], L.BLUFF_S[0]], [L.BLUFF_S[1], L.BLUFF_S_SIDES[1]])
    # the north-west wedge: north side in, front north to south, south side out
    poly = notch(poly, [L.WEDGE_N[1], L.WEDGE_N[0], L.WEDGE_FRONT[0]],
                 [L.WEDGE_FRONT[1], L.WEDGE_S[0], L.WEDGE_S[1]])
    # drop points closer than 64 to the next
    out = []
    for p in poly:
        if not out or math.dist(out[-1], p) >= 64:
            out.append(p)
    if math.dist(out[0], out[-1]) < 64:
        out.pop()
    # drop corners that lie (nearly) on the line through their neighbours
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cross) < 0.02 * math.dist(a, b) * math.dist(b, c) and b not in (L.BLUFF_S + L.WEDGE_FRONT):
                del out[i]
                changed = True
                break
    return out


def edge_dist(poly, p):
    best = 1e18
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ex, ey = b[0] - a[0], b[1] - a[1]
        L2 = ex * ex + ey * ey
        t = max(0.0, min(1.0, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / L2)) if L2 else 0.0
        best = min(best, math.hypot(p[0] - a[0] - t * ex, p[1] - a[1] - t * ey))
    return best


def inside(poly, p):
    x, y = p
    c = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


# ---------------------------------------------------------------- the town floor: lanes, the square, terraces
def terrace_geometry(t):
    """Points (x, y, z), lines and region points of one terrace (TIN): top ring at h, bank ring at 0, ramp."""
    x0, y0, x1, y1 = t['top']
    h, b, w, ln = t['h'], t['bank'], t['width'], t['length']
    bs = int(math.ceil(h / 1.5 / 16) * 16)              # the ramp's side banks
    c = t['at']
    if t['side'] == 'e':
        # local u along y (south to north), v outward east from x1
        def P(u, v):
            return (x1 + v, u)
        top_ring = [(x0, y0), (x1, y0), (x1, c - w // 2), (x1, c + w // 2), (x1, y1), (x0, y1)]
    else:  # 's': u along x (west to east), v outward south from y0
        def P(u, v):
            return (u, y0 - v)
        top_ring = [(x0, y0), (c - w // 2, y0), (c + w // 2, y0), (x1, y0), (x1, y1), (x0, y1)]
    top_ring = ccw(top_ring)
    # the bank ring: the top grown by b, with the ramp's foot pushed out
    if t['side'] == 'e':
        ring = [(x0 - b, y0 - b), (x1 + b, y0 - b), P(c - w // 2 - bs, b), P(c - w // 2 - bs, ln), P(c - w // 2, ln),
                P(c + w // 2, ln), P(c + w // 2 + bs, ln), P(c + w // 2 + bs, b), (x1 + b, y1 + b), (x0 - b, y1 + b)]
    else:
        ring = [(x0 - b, y0 - b), P(c - w // 2 - bs, b), P(c - w // 2 - bs, ln), P(c - w // 2, ln), P(c + w // 2, ln),
                P(c + w // 2 + bs, ln), P(c + w // 2 + bs, b), (x1 + b, y0 - b), (x1 + b, y1 + b), (x0 - b, y1 + b)]
    ring = ccw(ring)
    pts = [(x, y, h) for x, y in top_ring] + [(x, y, 0) for x, y in ring]
    lines = [top_ring + [top_ring[0]], ring + [ring[0]],
             [P(c - w // 2, 0), P(c - w // 2, ln)], [P(c + w // 2, 0), P(c + w // 2, ln)]]
    regions = {'top': ((x0 + x1) // 2, (y0 + y1) // 2), 'ramp': P(c, ln // 2),
               'bank': ((x0 + x1) // 2, y1 + b // 2) if t['side'] == 'e' else (x0 - b // 2, (y0 + y1) // 2)}
    foot = ring
    return pts, lines, regions, foot


def grid_lines(rects_by_label, bbox):
    """The floor's lines round the lanes and the square, cut on a 64 grid: (points, 2-point lines, region points)."""
    gx0, gy0, gx1, gy1 = bbox
    nx, ny = (gx1 - gx0) // STEP, (gy1 - gy0) // STEP
    lab = [[0] * ny for _ in range(nx)]
    for label, rects in rects_by_label:
        for (x0, y0, x1, y1) in rects:
            for i in range((x0 - gx0) // STEP, (x1 - gx0) // STEP):
                for j in range((y0 - gy0) // STEP, (y1 - gy0) // STEP):
                    lab[i][j] = label
    def L_(i, j):
        if 0 <= i < nx and 0 <= j < ny:
            return lab[i][j]
        return 0
    # boundary edges: horizontal at grid y j between cells (i, j-1) and (i, j); vertical at grid x i
    hor = {(i, j) for i in range(nx) for j in range(ny + 1) if L_(i, j - 1) != L_(i, j)}
    ver = {(i, j) for i in range(nx + 1) for j in range(ny) if L_(i - 1, j) != L_(i, j)}
    deg = {}
    for (i, j) in hor:
        for v in ((i, j), (i + 1, j)):
            deg.setdefault(v, []).append('h')
    for (i, j) in ver:
        for v in ((i, j), (i, j + 1)):
            deg.setdefault(v, []).append('v')
    def through(v, d):
        e = deg.get(v, [])
        return len(e) == 2 and e[0] == d and e[1] == d
    lines, seen = [], set()
    for (i, j) in sorted(hor):
        if (i, j) in seen:
            continue
        a = i
        while (a - 1, j) in hor and through((a, j), 'h'):
            a -= 1
        b = a
        while (b, j) in hor:
            seen.add((b, j))
            b += 1
            if not through((b, j), 'h'):
                break
        lines.append(((a, j), (b, j)))
    for (i, j) in sorted(ver):
        if (i, j) in seen:
            continue
        a = j
        while (i, a - 1) in ver and through((i, a), 'v'):
            a -= 1
        b = a
        while (i, b) in ver:
            seen.add((i, b))
            b += 1
            if not through((i, b), 'v'):
                break
        lines.append(((i, a), (i, b)))
    W = lambda v: (gx0 + v[0] * STEP, gy0 + v[1] * STEP)
    seg = [(W(a), W(b)) for a, b in lines]
    pts = sorted({p for s in seg for p in s})
    # one region point per connected group of each label
    regions = []
    done = set()
    for i in range(nx):
        for j in range(ny):
            if lab[i][j] and (i, j) not in done:
                stack, comp = [(i, j)], []
                done.add((i, j))
                while stack:
                    c = stack.pop()
                    comp.append(c)
                    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        q = (c[0] + d[0], c[1] + d[1])
                        if q not in done and 0 <= q[0] < nx and 0 <= q[1] < ny and lab[q[0]][q[1]] == lab[i][j]:
                            done.add(q)
                            stack.append(q)
                ci, cj = min(comp)
                regions.append((lab[i][j], (gx0 + ci * STEP + STEP // 2, gy0 + cj * STEP + STEP // 2)))
    return pts, seg, regions


def ellipse(c, r, n):
    return [(round(c[0] + r[0] * math.cos(2 * math.pi * k / n)), round(c[1] + r[1] * math.sin(2 * math.pi * k / n)))
            for k in range(n)]


def water_outline():
    """The pool and its stream as one sunken outline: the pool's ellipse with the stream leaving its south rim."""
    cx, cy = L.POOL['at']
    rx, ry = L.POOL['radii']
    hw = L.STREAM_WIDTH // 2
    path = L.STREAM
    # left (east) and right (west) offsets of the stream, going south
    def offs(sign):
        out = []
        for k, p in enumerate(path):
            if k == 0:
                d = (path[1][0] - p[0], path[1][1] - p[1])
            elif k == len(path) - 1:
                d = (p[0] - path[k - 1][0], p[1] - path[k - 1][1])
            else:
                a = (p[0] - path[k - 1][0], p[1] - path[k - 1][1])
                b = (path[k + 1][0] - p[0], path[k + 1][1] - p[1])
                na, nb = math.hypot(*a), math.hypot(*b)
                d = (a[0] / na + b[0] / nb, a[1] / na + b[1] / nb)
            n = math.hypot(*d)
            nx, ny = d[1] / n * sign, -d[0] / n * sign      # sign 1: to the left of travel (east, going south)
            out.append((round(p[0] - nx * hw), round(p[1] - ny * hw)))
        return out
    east = offs(1)
    west = offs(-1)
    # the rim: counter-clockwise from just east of the stream round to just west of it
    pts = []
    for k in range(19):
        a = math.radians(-82 + k * (344 / 18))
        pts.append((round(cx + rx * math.cos(a)), round(cy + ry * math.sin(a))))
    east[0] = (round(cx + rx * math.cos(math.radians(-86))), round(cy + ry * math.sin(math.radians(-86))) - 32)
    west[0] = (round(cx + rx * math.cos(math.radians(-94))), round(cy + ry * math.sin(math.radians(-94))) - 32)
    poly = pts + [west[0]] + west[1:] + list(reversed(east[1:])) + [east[0]]
    return ccw(poly)
