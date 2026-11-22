#!/usr/bin/env python3
"""Dressing check (Xeen rule, 2026-11-20): every decoration of the built map against its sector's portals (doorways),
the walking lines between them (and the start in the mouth), and its nearest wall. Usage: dress_check.py <export.json>
Prints, per decoration: sector, distance to the nearest doorway span, to the nearest walking line, to the nearest wall.
Flags: within 192 of a doorway span, within 128 of a walking line, a container (barrel, cask, sack, crate) more than
256 from a wall."""
import json, math, sys
d = json.load(open(sys.argv[1]))['map']
V = d['vertices']; F = d['faces']; S = d['sectors']
CONT = ('barel', 'dec21', 'dec03', 'dec32', 'sac', 'bag', 'crate', 'keg')

def seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def span(face):
    pts = [V[i] for i in face['vertices']]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    # the doorway's footprint: the horizontal extent of the vertical face
    if max(xs) - min(xs) >= max(ys) - min(ys):
        return (min(xs), (min(ys) + max(ys)) / 2), (max(xs), (min(ys) + max(ys)) / 2)
    return ((min(xs) + max(xs)) / 2, min(ys)), ((min(xs) + max(xs)) / 2, max(ys))

portals = {}   # sector -> [(a, b)]
walls = {}     # sector -> [(a, b)]
for i, f in enumerate(F):
    if abs(f['plane_normal'][2]) > 0.3 if isinstance(f['plane_normal'][2], (int, float)) else False:
        continue
    pts = [V[k] for k in f['vertices']]
    if max(p[2] for p in pts) - min(p[2] for p in pts) < 8:
        continue
    a, b = span(f)
    for s in {f['room'], f['room_behind']}:
        (portals if f['is_portal'] else walls).setdefault(s, []).append((a, b))

def sector_of(pos):
    best = None
    for i, s in enumerate(S):
        if i == 0:
            continue
        mn, mx = s['min'], s['max']
        if mn[0] - 1 <= pos[0] <= mx[0] + 1 and mn[1] - 1 <= pos[1] <= mx[1] + 1 and mn[2] - 64 <= pos[2] <= mx[2]:
            area = (mx[0] - mn[0]) * (mx[1] - mn[1])
            if best is None or area < best[0]:
                best = (area, i)
    return best[1] if best else -1

for e in d['entities']:
    p = e['position']; s = sector_of(p); xy = (p[0], p[1])
    ps = portals.get(s, [])
    centres = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in ps]
    if s == 1:
        centres.append((0, 448))  # the party's start in the mouth
    dpor = min((seg_dist(xy, a, b) for a, b in ps), default=9999)
    lines = [(centres[i], centres[j]) for i in range(len(centres)) for j in range(i + 1, len(centres))]
    dline = min((seg_dist(xy, a, b) for a, b in lines), default=9999)
    dwall = min((seg_dist(xy, a, b) for a, b in walls.get(s, [])), default=9999)
    name = e['name']
    flags = []
    if dpor < 192: flags.append('DOORWAY')
    if dline < 128: flags.append('LINE')
    if any(c in name.lower() for c in CONT) and dwall > 256: flags.append('OFFWALL')
    print(f"{name:10s} ({p[0]:6d},{p[1]:6d},{p[2]:4d}) sector {s:2d} doorway {dpor:6.0f} line {dline:6.0f} wall {dwall:5.0f} {' '.join(flags)}")
