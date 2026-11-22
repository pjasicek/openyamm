#!/usr/bin/env python3
"""A6's spots for the sky-barges and the celestial boat in D7, from D7's own build script (gen.py) and design data.

Barges: each lies along its island's rim edge (where the stand-in's ray from the island's middle leaves the cloud),
fully over the void, its port (gangway) side to the island with CLEAR units between the gunwale and the rim, the
gangplank resting on the island. Facing = the way the prow points, port side to the island (outward + 90 deg).
Boat: alongside the jetty's end on the side given by BOAT_SIDE, parallel to it, prow out to the void.
Writes work/placement.json and prints the table. Usage: python3 placement.py"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'output/studio_cal/d7/tools'))
import gen  # noqa: E402

H = json.loads((HERE / 'hulls.json').read_text())
CLEAR = 16
# the north crossing's merchant stands at the mouth of the Olympus causeway (D-58's move put the causeway there): its
# barge goes on the island's north rim instead, clear of every road (A6 moves poi:merchant_dust to `merchant_spot`)
MOVE = {'dust': (-1536, 21000)}
ELEMENT = {'smoke': 'fire', 'dust': 'air', 'steam': 'water', 'mud': 'earth'}   # see README (which tint is which)


def half_width(h, t):
    return max(h['tip'], h['beam'] / 2 * max(0.0, 1 - abs(t) ** h['pe']) ** h['pq'])


def plan_outline(h, cx, cy, fdeg, n=64):
    """The gunwale outline in the map (prow along fdeg)."""
    f = math.radians(fdeg)
    fx, fy = math.cos(f), math.sin(f)
    lx, ly = -fy, fx                                    # port (left of the prow)
    pts = []
    for i in range(n + 1):
        t = -1 + 2 * i / n                              # -1 prow .. +1 stern
        along = -t * h['length'] / 2
        w = half_width(h, t)
        for side in (1, -1):
            pts.append((cx + fx * along + lx * w * side, cy + fy * along + ly * w * side))
    return pts


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def clearance(poly, pts):
    """Smallest distance from the outline to the island; negative when a point lies inside it."""
    best = 1e9
    for p in pts:
        d = min(seg_dist(p, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))
        best = min(best, -d if gen.inside(poly, p) else d)
    return best


def walkable_under(h, at, fdeg):
    """Points of the hull's plan (gunwale, half and centre lines) over anything walkable (should be 0)."""
    f = math.radians(fdeg)
    fx, fy, lx, ly = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    n = 0
    for frac in (0.0, 0.5, 1.0):
        for i in range(41):
            t = -1 + 2 * i / 40
            w = half_width(h, t) * frac
            for side in (1, -1):
                p = (at[0] - fx * t * h['length'] / 2 + lx * w * side, at[1] - fy * t * h['length'] / 2 + ly * w * side)
                n += gen.height_at(p) is not None
    return n


def barges():
    out = []
    h = H['barge']
    for p in gen.D.POINTS:
        if p['kind'] != 'merchant':
            continue
        s = gen.SPACE[p['space']]
        poly = gen.P[s['id']]
        c = s['at']
        k = gen.key(p['id']).replace('merchant_', '')
        deg = gen.toward_deg(c, MOVE.get(k, p['at']))
        rim = gen.G.ray_exit(poly, c, (c[0] + 20000 * math.cos(math.radians(deg)),
                                        c[1] + 20000 * math.sin(math.radians(deg))))
        # the rim edge at the exit point, oriented so the island lies to its left (its right normal points out)
        edge = min(range(len(poly)), key=lambda i: seg_dist(rim, poly[i], poly[(i + 1) % len(poly)]))
        a, b = poly[edge], poly[(edge + 1) % len(poly)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        el = math.hypot(ex, ey)
        ex, ey = ex / el, ey / el
        nx, ny = ey, -ex                                 # right of the edge
        if (nx * math.cos(math.radians(deg)) + ny * math.sin(math.radians(deg))) < 0:
            ex, ey, nx, ny = -ex, -ey, -ny, nx
        facing = math.degrees(math.atan2(ey, ex))
        lo, hi = 0.0, 1200.0
        for _ in range(40):
            mid = (lo + hi) / 2
            cx, cy = rim[0] + nx * mid, rim[1] + ny * mid
            if clearance(poly, plan_outline(h, cx, cy, facing)) >= CLEAR:
                hi = mid
            else:
                lo = mid
        cx, cy = rim[0] + nx * hi, rim[1] + ny * hi
        plank = (cx - nx * (h['beam'] / 2 + h['plank_reach']), cy - ny * (h['beam'] / 2 + h['plank_reach']))
        out.append({'cargo': k, 'element': ELEMENT[k], 'island': s['id'], 'island_floor': s['floor'],
                    'merchant_poi': list(p['at']), 'rim': [round(rim[0]), round(rim[1])],
                    'at': [round(cx), round(cy)], 'floor_height': s['floor'], 'facing': round(facing % 360, 1),
                    'stand_in_facing': round((deg + 87) % 360, 1), 'offset_from_rim': round(hi),
                    'gangplank_end_on_island': [round(plank[0]), round(plank[1])],
                    'gangplank_end_height': gen.height_at(plank),
                    'merchant_spot': [round(plank[0] - nx * 96), round(plank[1] - ny * 96)],
                    'walkable_under_hull': walkable_under(h, (cx, cy), facing)})
    return out


def boat(side=1):
    h = H['boat']
    jet = gen.jetty()[0]
    L, W = jet['size']
    f = math.radians(jet['facing'])
    ux, uy = math.cos(f), math.sin(f)
    jx, jy = jet['at']
    end = (jx + ux * L / 2, jy + uy * L / 2)
    top = jet['base'] + gen.FLOOR + jet['rise']
    nx, ny = -uy * side, ux * side
    off = W / 2 + h['beam'] / 2 + 24
    back = h['length'] / 2 + 64
    at = (end[0] - ux * back + nx * off, end[1] - uy * back + ny * off)
    return {'jetty_end': [round(end[0]), round(end[1])], 'jetty_top': top, 'jetty_facing': jet['facing'],
            'jetty_width': W, 'side': 'north-east' if side > 0 else 'south-west',
            'at': [round(at[0]), round(at[1])], 'floor_height': top - h['deck_below_jetty'],
            'facing': round(jet['facing'] % 360, 1), 'clear_of_jetty_edge': 24,
            'stern_from_jetty_end': round(back + h['length'] / 2),
            'walkable_under_hull': walkable_under(h, at, jet['facing'])}


def main():
    res = {'barges': barges(), 'boat': boat(1), 'boat_other_side': boat(-1)}
    (PROJECT / 'work' / 'placement.json').write_text(json.dumps(res, indent=1))
    for b in res['barges']:
        print(b)
    print(res['boat'])
    print(res['boat_other_side'])


if __name__ == '__main__':
    main()
