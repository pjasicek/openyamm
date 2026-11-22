#!/usr/bin/env python3
"""XD-27 dressing check against the walking lines (DRESSING.md: a floor prop's centre at least its radius + 64 from the
line between two openings of its room). Reads the generated objects.yml; the lines are the rooms' openings (from the
built portals), the start, and the things the party walks to (chests, the seat, the rack). Lines across the cooking pit
are left out (the party walks round it). Usage: walk_lines.py <objects.yml>"""
import math, sys, yaml
P = lambda *a: a
LINES = {
    'room:mouth': [((0, 448), (0, 1120)), ((0, 448), (-672, 544)), ((-672, 544), (0, 1120)), ((0, 448), (0, 0))],
    'room:midden': [((-672, 544), (-1280, 544)), ((-1280, 544), (-1664, 800)), ((-1664, 800), (-1856, 1280)),
                    ((-1856, 1280), (-1856, 1888))],
    'room:bone_den': [((-1856, 1888), (-1344, 2752)), ((-1856, 1888), (-2752, 2880))],
    'room:feast_cave': [((-672, 2752), (32, 2048)), ((-672, 2752), (-1376, 3616)), ((-672, 2752), (-192, 4064)),
                        ((32, 2048), (928, 3168)), ((32, 2048), (-1376, 3616)), ((928, 3168), (-192, 4064)),
                        ((-1376, 3616), (-192, 4064)), ((32, 2048), (-192, 4064)), ((928, 3168), (-1376, 3616)),
                        ((-672, 2752), (928, 3168))],
    'room:gate_yard': [((0, 1120), (32, 2048)), ((0, 1300), (0, 1148))],
    'room:kennel': [((928, 3168), (1700, 3168))],
    'room:chief_den': [((-1376, 3616), (-3168, 3776)), ((-1376, 3616), (-2752, 3740)), ((-1376, 3616), (-2336, 4150))],
    'room:larder': [((-3168, 3776), (-3808, 3820)), ((-3168, 3776), (-3900, 4128))],
    'room:quarry_ramp': [((-192, 4064), (-192, 4544)), ((-192, 4544), (-64, 4928)), ((-64, 4928), (-64, 5152))],
    'room:quarry': [((-64, 5152), (864, 5920))],
    'room:chute': [((864, 5920), (1472, 5920)), ((1472, 5920), (1888, 6080)), ((1888, 6080), (2208, 6080))],
    'room:river_ledge': [((2208, 6080), (2752, 5800)), ((2208, 6080), (2752, 6400)), ((2208, 6080), (2960, 6560))],
}
PIT, PIT_R = (-192, 3136), 352
RADIUS = {'sklplrev': 80, 'trasheap': 80, '7dec01': 64, '7dec10': 64, '7dec11': 64, 'dec05': 64, 'Corpse04': 64,
          'Corpse02': 64, 'bigbarel': 40, 'smlbarel': 32, '7dec32': 52, '7dec21': 52, 'dec03': 40, 'floursac': 32,
          'bag01': 32, 'bag_A': 32, 'Bucket': 24, 'foodbowl': 16, 'dec29': 32, '7dec18': 32, 'dec19': 32,
          '7dec20': 24, 'torskul0': 24, 'torch01': 0}
ROCK = 56

def dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)

objs = yaml.safe_load(open(sys.argv[1]))
bad = 0
for o in objs.get('decorations', []):
    if o.get('wall') or o.get('inside') or o.get('floor_height'):
        continue  # hung on a wall, inside another, or standing on a bench
    r = RADIUS.get(o['decoration'], ROCK if 'rock' in o['decoration'] else 32)
    lines = [l for l in LINES.get(o['room'], []) if dist(PIT, *l) >= PIT_R]
    if not lines:
        continue
    dd = min(dist(o['at'], a, b) for a, b in lines)
    need = r + 64
    if dd < need:
        bad += 1
        print(f"{o['id']:24s} {o['decoration']:9s} at {o['at']} line {dd:5.0f} < {need}")
print('offenders', bad)
