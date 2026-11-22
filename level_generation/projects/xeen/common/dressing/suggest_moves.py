#!/usr/bin/env python3
import pathlib
"""Suggest wall or corner spots for the floor props check_dressing.py flags (lane A7, the move of XD-01..04, 2026-11-20).

Usage: suggest_moves.py <L4> <export.json> <deco id>[@floor z] [...]
For each prop: the spots along the walls of its own sector (its radius + 60 off the wall, every 32 units) on the
same floor height, not under a platform top, that keep DRESSING.md's numbers (containers: 200 from a door face, 330
from a portal, 210 from any other container outside a storeroom; every prop: radius + 72 off the line between two
openings of its sector, clear of the other props by both radii + 24), nearest to where it stands first. Prints the
best three. Nothing is written: the moves are edited into objects.yml by hand (or a script) after a look."""
import json, math, os, sys, collections, yaml
STRICT = bool(os.environ.get('STRICT'))

R = str(pathlib.Path(__file__).resolve().parents[5]) + '/assets_dev/engine/data_tables/decoration_data.txt'
DD = {}
for line in open(R, encoding='latin-1'):
    c = line.rstrip('\n').split('\t')
    if len(c) > 5 and c[0].isdigit():
        DD[c[1].lower()] = (c[2].lower(), int(c[4] or 0))
CONT = ('barrel', 'cask', 'keg', 'sack', 'bag', 'crate', 'box')
STORE = ('store', 'cache', 'larder', 'hold', 'cellar', 'pantry', 'granary', 'stock')

L4, EXP, ids = sys.argv[1], sys.argv[2], sys.argv[3:]
d = json.load(open(EXP)); m = d['map']; V = m['vertices']; F = m['faces']
objs = yaml.safe_load(open(L4 + '/objects.yml'))
rooms = {r['id']: r for r in (yaml.safe_load(open(L4 + '/rooms.yml')).get('rooms') or [])}
doorfaces = set(f for dr in d.get('doors', []) for f in dr['faces'])


def seg(face):
    pts = [V[i] for i in face['vertices']]
    a, b = max(((p, q) for p in pts for q in pts), key=lambda t: (t[0][0]-t[1][0])**2 + (t[0][1]-t[1][1])**2)
    return a[:2], b[:2], min(p[2] for p in pts), max(p[2] for p in pts)


def dist(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]; L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dy) / L))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


def planeDist(p, o):
    (ax, ay), (bx, by) = o[3], o[4]; L = math.hypot(bx-ax, by-ay) or 1
    return abs((bx-ax)*(ay-p[1]) - (ax-p[0])*(by-ay)) / L


walls, portals, doors = [], [], []
secwalls = collections.defaultdict(list)
opens = collections.defaultdict(list)
for i, f in enumerate(F):
    if f['plane_normal'][2] != 0:
        continue
    s = seg(f)
    mid = ((s[0][0]+s[1][0])/2, (s[0][1]+s[1][1])/2, s[2], s[0], s[1])
    if i in doorfaces:
        doors.append(s)
    elif f['is_portal']:
        portals.append(s)
        for r in (f['room'], f['room_behind']):
            opens[r].append(mid)
    else:
        walls.append(s); secwalls[f['room']].append(s)


def inpoly(x, y, pts):
    c = False
    for k in range(len(pts)):
        (x1, y1), (x2, y2) = pts[k][:2], pts[k-1][:2]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            c = not c
    return c


floors = [(f['room'], [V[i] for i in f['vertices']]) for f in F if f['plane_normal'][2] > 0 and not f['is_portal']]


def floor_at(x, y, z):
    best = None
    for r, pts in floors:
        fz = max(p[2] for p in pts)
        if fz <= z + 24 and inpoly(x, y, pts) and (best is None or fz > best[0]):
            best = (fz, r)
    return best


def under_top(x, y, z):
    return any(z + 24 < max(p[2] for p in pts) < z + 400 and inpoly(x, y, pts) for r, pts in floors)


def near(lst, p, z):
    c = [dist(p, a, b) for a, b, z0, z1 in lst if z0 - 40 <= z + 30 <= z1 + 40]
    return min(c) if c else 1e9


ent = {e['name']: e for e in m['entities']}
props = {}
for o in objs.get('decorations') or []:
    kind = str(o.get('decoration') or o.get('kind') or '').lower()
    hint, rad = DD.get(kind, ('', 32))
    e = ent.get(o['id'].split(':', 1)[1])
    if e is None:
        continue
    room = o.get('room', ''); rname = (rooms.get(room, {}).get('name') or '').lower()
    props[o['id']] = dict(id=o['id'], kind=kind, r=rad, pos=tuple(e['position']), room=room,
                          store=any(w in room.lower() or w in rname for w in STORE),
                          cont=any(w in hint or w in kind for w in CONT), hung=bool(o.get('height')))

for arg in ids:
    pid, _, zo = arg.partition('@')  # deco:x@-192: as if it stood on the floor at -192 (off a deck or table)
    p = props[pid]; x0, y0, z = p['pos']; r = p['r']
    if zo:
        z = int(zo)
    fs = floor_at(x0, y0, z); sec = fs[1] if fs else None
    o = [c for c in opens.get(sec, []) if abs(c[2] - z) < 300]
    pairs = [(o[i], o[j]) for i in range(len(o)) for j in range(i+1, len(o))
             if not (planeDist(o[j], o[i]) < 64 and planeDist(o[i], o[j]) < 64)]
    tall = [(a, b, z0, z1) for a, b, z0, z1 in secwalls.get(sec, []) if z0 <= z + 30 and z1 >= z + 160]

    def ok(cx, cy):
        f2 = floor_at(cx, cy, z)
        if not f2 or f2[1] != sec or abs(f2[0] - z) > 8 or under_top(cx, cy, z):
            return None
        c = (cx, cy)
        if near(walls, c, z) < r + 40:
            return None
        wall = min([dist(c, a, b) for a, b, z0, z1 in tall] or [1e9])
        if p['cont'] and (wall > (300 if p['store'] else 230) or near(doors, c, z) < 200 or near(portals, c, z) < 330):
            return None
        if near(doors, c, z) < 200:  # no prop of any kind in front of a door leaf (the lead's rule, 2026-11-20)
            return None
        if STRICT and near(portals, c, z) < 330:  # STRICT=1: any prop as far from an open doorway as a container
            return None
        if any(dist(c, A[:2], B[:2]) < r + 72 for A, B in pairs):
            return None
        for q in props.values():
            if q['id'] == pid or q['hung'] or abs(q['pos'][2] - z) >= 200:
                continue
            dq = math.hypot(q['pos'][0]-cx, q['pos'][1]-cy)
            if dq < r + q['r'] + 24 or (p['cont'] and q['cont'] and not p['store'] and dq < 210):
                return None
        return (math.hypot(cx-x0, cy-y0), round(cx), round(cy), round(wall))

    pts = []
    for a, b, z0, z1 in tall:  # along the walls, radius + 60 off them
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        if L < 2*r + 40:
            continue
        ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        t = r + 30
        while t <= L - r - 30:
            for sgn in (1, -1):
                pts.append((a[0] + ux*t - sgn*uy*(r+60), a[1] + uy*t + sgn*ux*(r+60)))
            t += 32
    for rr in range(16, 417, 16):  # and rings round where it stands (a nudge off a walking line)
        for k in range(24):
            pts.append((x0 + rr*math.cos(k*math.pi/12), y0 + rr*math.sin(k*math.pi/12)))
    cands = [c for c in (ok(cx, cy) for cx, cy in pts) if c]
    cands.sort()
    if cands:  # the next prop of the call sees this one at its new spot (a row of sacks placed one by one)
        p['pos'] = (cands[0][1], cands[0][2], z)
    print(pid, p['kind'], 'r', r, 'at', (x0, y0, z), 'sector', sec, 'best:', cands[:3] if cands else 'NONE')
