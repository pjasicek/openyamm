"""F62 on the elemental planes (the player's pins 2026-11-25; X8's `landing_end`, ported by xeen-fb4-dungeon5): a deck
(causeway, bridge, ramp, walk) sloping straight from inside one shelf, isle or sheet to inside another dipped under
the higher one's top before its rim, or rose through the lower one's (tools/xeen/check_floor_cross.py `floor.cross`).
Each deck lies level at its shelf's height out to where it is past that shelf across its whole width, and slopes only
between. Shared by P1-P4's gen.py.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../xeen_art/phase6'))
import planes_geom as PG  # noqa: E402


def landing_end(poly, start, u, width, margin=24):
    """Where a deck of `width` leaving `start` (on its shelf) along `u` is past the shelf across its whole width: the
    point on the centre line `margin` beyond the furthest bit of shelf under the deck (X8's)."""
    ux, uy = u
    nx, ny = -uy, ux
    far = 0
    for k in range(9):
        o = (k / 8 - 0.5) * width
        t = 0
        while t < 20000:
            if PG.point_in((start[0] + ux * t + nx * o, start[1] + uy * t + ny * o), poly):
                far = max(far, t)
            t += 8
            if t > far + 2000:
                break
    far += margin
    return (start[0] + ux * far, start[1] + uy * far)


def along(a, u, p):
    return (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]


def link_spans(a, b, za, zb, width, poly_a, poly_b, margin=24):
    """[(p, q, z0, z1)] from a (inside poly_a, top za) to b (inside poly_b, top zb): level across each shelf, sloping
    between. Where the shelves leave under 64 between the landings, level on the higher shelf only, then the slope."""
    if int(round(za)) == int(round(zb)):
        return [(a, b, za, zb)]
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / d, (b[1] - a[1]) / d)
    pa = landing_end(poly_a, a, u, width, margin) if poly_a else a
    pb = landing_end(poly_b, b, (-u[0], -u[1]), width, margin) if poly_b else b
    ta, tb = along(a, u, pa), along(a, u, pb)
    out = []
    if tb - ta >= 64:
        if ta > 1:
            out.append((a, pa, za, za))
        out.append((pa if ta > 1 else a, pb if d - tb > 1 else b, za, zb))
        if d - tb > 1:
            out.append((pb, b, zb, zb))
    elif zb > za and 64 <= tb <= d - 64:
        out = [(a, pb, za, zb), (pb, b, zb, zb)]
    elif za > zb and 64 <= ta <= d - 64:
        out = [(a, pa, za, za), (pa, b, za, zb)]
    else:
        out = [(a, b, za, zb)]
    return out


def ramp_spans(a, u, top, foot_z, run, poly, width, margin=24):
    """A ramp leaving its shelf at a (inside it) along u: level at `top` until past the shelf, then `run` down to
    foot_z. [(p, q, z0, z1)]."""
    pa = landing_end(poly, a, u, width, margin)
    b = (pa[0] + u[0] * run, pa[1] + u[1] * run)
    return [(a, pa, top, top), (pa, b, top, foot_z)]


def span_top(spans, pt):
    """The deck's top over the point's projection on its line, or None off its ends."""
    for p, q, z0, z1 in spans:
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2 if L2 else 0
        if -1e-6 <= t <= 1 + 1e-6:
            return z0 + (z1 - z0) * t
    return None


def deck_top(decks, c, half, floor):
    """The highest top of the deck blocks (`at`/`size`/`facing`, `base` over the room's `floor`, `top_heights` along
    their length) over a square of `half` round c, or None. A plate laid on a deck's landing stands on it (it lay in
    the landing's plane: geometry.coplanar)."""
    best = None
    for e in decks:
        if 'size' not in e:
            continue
        f = math.radians(e.get('facing', 0))
        cf, sf = math.cos(f), math.sin(f)
        L, W = e['size']
        for dx in (-half, 0, half):
            for dy in (-half, 0, half):
                x, y = c[0] + dx - e['at'][0], c[1] + dy - e['at'][1]
                u, v = x * cf + y * sf, -x * sf + y * cf
                if abs(u) > L / 2 or abs(v) > W / 2:
                    continue
                z = floor + e['base'] + e['rise']
                if 'top_heights' in e:
                    h = e['top_heights']
                    z = floor + e['base'] + h[0] + (h[1] - h[0]) * (u / L + 0.5)
                best = z if best is None else max(best, z)
    return best
