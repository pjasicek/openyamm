#!/usr/bin/env python3
"""F70 (the player's pins 2026-11-26, X9 p5-p10, "the side rails stop in the air"): beam ends that hang in the air.

A rope bridge's rails on the sky maps (X8, X9, D7) were two beams 80 over the deck from one end of the deck to the
other; at both ends they stopped in mid-air, tied to nothing. A beam end is held when, within GAP of it and at its
height, there is:
- another beam's end or body (a rail meeting a post's crossbar, a continuing rail span),
- a platform or pillar (its footprint, its height from `base` to its highest top; `top_size` tapers ignored), or
- a wall (the end within GAP of the outline of its room or of any room of the map, or of a path room's sides), or
- the floor (its underside within GAP of the room's floor).
A beam whose top reaches the room's ceiling hangs from it; a beam that is part of a clicked platform (`part_of`, a
capstan's bar) is that platform's. Anything else is an end in the air (`beam.loose`).

Reads the map projects (`devdocs/xeen/briefs/<key>/L4/rooms.yml`): beams are the generators' words, so the finding
names the beam (`rooms[i].beams[j]`, its path and heights). Rooms with `levels` use the room's floor for platforms'
`base`, as the studio does.

On the open-air maps (OPEN_AIR: the sky maps and the planes, whose rails and beams have only the sky round them) a
loose end is an error; in a dungeon it is a warning (a timber lying across a wall's corner or a pillar the check does
not read is common there: look at it).

Usage: tools/xeen/check_beam_ends.py [<key> ...]   (default every Xeen project with beams)   Exit 1 on an error."""
import glob
import math
import os
import sys

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAP = 12.0
OPEN_AIR = {'x8', 'x9', 'd7', 'p1', 'p2', 'p3', 'p4', 'p5'}


def pip(poly, x, y):
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy), t


def poly_dist(poly, p):
    return min(seg_dist(p, poly[i - 1], poly[i])[0] for i in range(len(poly)))


def footprint(e):
    if e.get('outline'):
        return [tuple(c) for c in e['outline']]
    if 'at' not in e or 'size' not in e:
        return None
    (cx, cy) = e['at']
    size = e['size']
    sx, sy = (size, size) if not isinstance(size, list) else size
    f = math.radians(e.get('facing', 0) or 0)
    c, s = math.cos(f), math.sin(f)
    return [(cx + u * c - v * s, cy + u * s + v * c) for u, v in ((-sx / 2, -sy / 2), (sx / 2, -sy / 2),
                                                                  (sx / 2, sy / 2), (-sx / 2, sy / 2))]


def zrange(e, floor):
    base = floor + (e.get('base') or 0)
    rise = e.get('rise', e.get('height', 0)) or 0
    top = base + max([rise] + list(e.get('top_heights') or []))
    return base, top


def beam_z(b, end):
    lo = b.get('bottom', 0) if end == 0 else b.get('bottom_end', b.get('bottom', 0))
    hi = b['top'] if 'top' in b else lo + b.get('depth', 32)
    return lo, hi


def check_room(key, ri, room, walls, paths):
    floor = room.get('floor', 0)
    ceiling = room.get('ceiling', 1e9)
    solids = []
    for kind in ('platforms', 'pillars'):
        for e in room.get(kind) or []:
            fp = footprint(e)
            if fp:
                solids.append((e.get('id', kind), fp, zrange(e, floor)))
    beams = room.get('beams') or []
    out = []
    for bj, b in enumerate(beams):
        path = b.get('path') or []
        if len(path) < 2 or b.get('part_of'):
            continue
        for end, p in ((0, path[0]), (1, path[-1])):
            lo, hi = beam_z(b, end)
            if hi >= ceiling - 2 or lo <= floor + GAP:
                continue
            held = any(poly_dist(w, p) <= GAP for w in walls) or any(
                abs(min(seg_dist(p, line[k - 1], line[k])[0] for k in range(1, len(line))) - half) <= GAP
                for line, half in paths)
            for sid, fp, (zlo, ztop) in solids if not held else ():
                if zlo - GAP <= hi and lo <= ztop + GAP and (pip(fp, p[0], p[1]) or poly_dist(fp, p) <= GAP):
                    held = True
                    break
            for bk, o in enumerate(beams) if not held else ():
                if bk == bj or len(o.get('path') or []) < 2:
                    continue
                op = o['path']
                for i in range(1, len(op)):
                    d, t = seg_dist(p, op[i - 1], op[i])
                    if d > GAP + o.get('width', 8) / 2:
                        continue
                    olo0, ohi0 = beam_z(o, 0)
                    olo1, ohi1 = beam_z(o, 1)
                    frac = ((i - 1) + t) / (len(op) - 1)
                    olo, ohi = olo0 + (olo1 - olo0) * frac, ohi0 + (ohi1 - ohi0) * frac
                    if olo - GAP <= hi and lo <= ohi + GAP:
                        held = True
                        break
                if held:
                    break
            if not held:
                level = 'error' if key in OPEN_AIR else 'warning'
                out.append(f'{level}: {key}: beam.loose rooms[{ri}].beams[{bj}] ({room.get("id")}) end {end} at '
                           f'({p[0]}, {p[1]}, {lo:.0f}-{hi:.0f}) holds to nothing (no post, block, beam or wall '
                           f'within {GAP:.0f})')
    return out


def main(argv):
    keys = argv or sorted(os.path.basename(os.path.dirname(os.path.dirname(f)))
                          for f in glob.glob(f'{R}/devdocs/xeen/briefs/*/L4/rooms.yml'))
    found = []
    for key in keys:
        path = f'{R}/devdocs/xeen/briefs/{key}/L4/rooms.yml'
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        walls = [[tuple(c) for c in r['outline']] for r in data.get('rooms') or [] if r.get('outline')]
        paths = [([tuple(c[:2]) for c in r['path']], r.get('width', 0) / 2) for r in data.get('rooms') or []
                 if len(r.get('path') or []) > 1]       # a path room's walls: width / 2 either side of its line
        for ri, room in enumerate(data.get('rooms') or []):
            found += check_room(key, ri, room, walls, paths)
    for line in found:
        print(line)
    per = {}
    for line in found:
        k = line.split(': ')[1]
        per[k] = per.get(k, 0) + 1
    errors = sum(1 for line in found if line.startswith('error'))
    print(f'beam ends in the air: {errors} error(s), {len(found) - errors} warning(s)'
          + (' (' + ', '.join(f'{k} {v}' for k, v in sorted(per.items())) + ')' if per else ''))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
