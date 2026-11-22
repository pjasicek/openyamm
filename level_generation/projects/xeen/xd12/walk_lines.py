#!/usr/bin/env python3
"""XD-12 dressing check against the walking lines (devdocs/xeen/formats/DRESSING.md), after XD-27's walk_lines.py.

A floor prop's centre must stand at least its radius + 64 from the line between two openings of its room (and never on
it); a piece of furniture (a platform 32 or more high) at least 64 from the line. The lines join every pair of a room's
walkable openings on one level (doorways and arches without a sill, from the generator's openings; windows, railings,
battlements, the Well's upper rims and the trapdoor holes are not ways through) and each opening to the start and to
Darzog's disc (the Well's way up and down). With --targets also to the chests, lecterns, the journal and the switches
(stricter than DRESSING.md, which names only the openings; listed, not required).
Decoration radii from engine decoration_data.txt. Hung decorations (on a wall, a chandelier) and those standing on
furniture (`floor_height`) are left out, as are the island's trees and rocks (the backdrop) and the trapdoors' bones
(the hatches' tell: they lie at the hatch, which the party walks round).

Usage: walk_lines.py <L4 folder> [--all] [--targets]   (--all lists every prop's clearance)"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import shell  # noqa: E402,F401  (fills geo.ROOMS and geo.OPENINGS)
import geo  # noqa: E402

R = Path(_REPO_ROOT)
L4 = Path(sys.argv[1])
SHOW_ALL = '--all' in sys.argv
TARGETS = '--targets' in sys.argv
rooms = {r['id']: r for r in yaml.safe_load(open(L4 / 'rooms.yml'))['rooms']}
objs = yaml.safe_load(open(L4 / 'objects.yml'))

RADIUS = {}
for line in open(R / 'assets_dev/engine/data_tables/decoration_data.txt', encoding='latin-1'):
    c = line.rstrip('\n').split('\t')
    if len(c) > 4 and c[0].isdigit() and c[4].lstrip('-').isdigit():
        RADIUS.setdefault(c[1], int(c[4]))
HUNG = {'dec27'}                      # chandeliers
OUTSIDE = {'room:out_n', 'room:out_e', 'room:out_s', 'room:out_w'}


def wall_point(rid, idx, along):
    o = rooms[rid]['outline']
    a, b = o[idx], o[(idx + 1) % len(o)]
    return (a[0] + (b[0] - a[0]) * along, a[1] + (b[1] - a[1]) * along)


def wall_index(rid, wall):
    if isinstance(wall, int):
        return wall
    o = rooms[rid]['outline']
    for i in range(len(o)):
        if geo._side(o[i], o[(i + 1) % len(o)]) == wall:
            return i
    raise SystemExit(f'{rid}: no wall {wall}')


def opening_points():
    """(room, z, point, opening id) for every walkable opening, one point on each side."""
    out = []
    for o in geo.OPENINGS:
        if 'in' in o or o.get('sill') is not None:
            continue
        a, b = o['from'], o['to']
        if a in OUTSIDE or b in OUTSIDE or (a.startswith('room:roof') and b == 'room:well'):
            continue
        z = max(geo.ROOMS[a]['floor'], geo.ROOMS[b]['floor'])
        for rid, idx in ((a, o['from_wall']), (b, o['to_wall'])):
            if o['width'] == 'full':
                along = 0.5
                lo, hi = None, None
                # the shared stretch's middle: the opening spans all of it
                lo_, hi_, i, j, gap = geo.shared(a, b, geo._side(*_edge(a, o['from_wall'])))
                mid = (lo_ + hi_) / 2
                p = _on_wall(rid, idx, mid)
            else:
                along = o['along'] if rid == a else None
                if rid == a:
                    p = wall_point(a, idx, along)
                else:
                    pa = wall_point(a, o['from_wall'], o['along'])
                    p = _project(b, idx, pa)
            out.append((rid, z, p, o['id']))
    return out


def _edge(rid, idx):
    o = geo.ROOMS[rid]['outline']
    return o[idx], o[(idx + 1) % len(o)]


def _on_wall(rid, idx, coord):
    a, b = _edge(rid, idx)
    return (coord, a[1]) if a[1] == b[1] else (a[0], coord)


def _project(rid, idx, p):
    a, b = _edge(rid, idx)
    return (p[0], a[1]) if a[1] == b[1] else (a[0], p[1])


def dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def seg_rect(a, b, x0, y0, x1, y1):
    """Distance between a segment and an axis-aligned rectangle (0 when they touch)."""
    def inside(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    if inside(a) or inside(b):
        return 0.0
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    edges = [(corners[i], corners[(i + 1) % 4]) for i in range(4)]
    for c, d in edges:
        if _cross(a, b, c, d):
            return 0.0
    return min([dist(c, a, b) for c in corners] + [dist(a, c, d) for c, d in edges] + [dist(b, c, d) for c, d in edges])


def _cross(p1, p2, p3, p4):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(p3, p4, p1), o(p3, p4, p2), o(p1, p2, p3), o(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


# --------------------------------------------------------------------------------------------------- points and lines
points = {}   # (room, z) -> list of (point, name)
for rid, z, p, oid in opening_points():
    points.setdefault((rid, z), []).append((p, oid))


def floor_z(rid, fh=None):
    return fh if fh is not None else geo.ROOMS[rid]['floor']


targets = {}  # (room, z) -> list of (point, name)
for c in (objs.get('chests', []) if TARGETS else []):
    targets.setdefault((c['room'], floor_z(c['room'])), []).append((tuple(c['at']), c['id']))
for s in (objs.get('switches', []) if TARGETS else []):
    if s.get('at'):
        p = tuple(s['at'])
    else:
        p = wall_point(s['room'], wall_index(s['room'], s['wall']), s['along'])
    z = s.get('floor_height', floor_z(s['room']))
    if s['room'] == 'room:well' and z == 0 and s.get('height', 0) > 1000:
        continue  # the disc rider's button at the top of the Well
    targets.setdefault((s['room'], z), []).append((p, s['id']))
st = objs['start']
targets.setdefault((st['room'], floor_z(st['room'])), []).append((tuple(st['at']), 'start'))
for rid, r in rooms.items():
    for p in r.get('platforms', []):
        if TARGETS and p.get('id', '').startswith(('platform:lectern', 'platform:journal')):
            z = floor_z(rid)
            if rid.startswith('room:roof'):
                z = geo.ROOMS[rid]['floor']
            targets.setdefault((rid, z), []).append((tuple(p['at']), p['id']))
for m in objs.get('movers', []):
    targets.setdefault((m['room'], 0), []).append((tuple(m['at']), m['id']))

LINES = {}    # room -> list of (a, b, z, name a, name b)
for (rid, z), ops in points.items():
    tg = targets.get((rid, z), [])
    for i in range(len(ops)):
        for j in range(i + 1, len(ops)):
            LINES.setdefault(rid, []).append((ops[i][0], ops[j][0], z, ops[i][1], ops[j][1]))
        for p, n in tg:
            LINES.setdefault(rid, []).append((ops[i][0], p, z, ops[i][1], n))

# ------------------------------------------------------------------------------------------------------- the check
bad = 0
rows = []
for d in objs.get('decorations', []):
    if 'wall' in d or 'floor_height' in d or d['decoration'] in HUNG or d['room'] in OUTSIDE:
        continue
    if '_bones_' in d['id'] and d['id'].startswith('deco:trap'):
        continue
    r = RADIUS.get(d['decoration'], 32)
    z = floor_z(d['room'])
    lines = [ln for ln in LINES.get(d['room'], []) if ln[2] == z]
    if not lines:
        rows.append((d['id'], 'no lines'))
        continue
    dd, ln = min((dist(d['at'], ln[0], ln[1]), ln) for ln in lines)
    need = r + 64
    if dd < need:
        bad += 1
        print(f"{d['id']:28s} {d['decoration']:9s} at {d['at']} r {r}: {dd:5.0f} < {need} from {ln[3]} - {ln[4]}")
    elif SHOW_ALL:
        print(f"  ok {d['id']:28s} {d['decoration']:9s} {dd:5.0f} >= {need}")
for rid, r in rooms.items():
    for p in r.get('platforms', []):
        if p.get('rise', 0) < 32 or 'at' not in p or p.get('base'):
            continue
        pid = p.get('id', '')
        if pid.startswith('platform:cloud') or rid in OUTSIDE:
            continue
        if 'Merlon' in p.get('notes', '') or 'merlon' in p.get('notes', '').lower():
            continue
        w, h = p['size']
        x0, y0, x1, y1 = p['at'][0] - w / 2, p['at'][1] - h / 2, p['at'][0] + w / 2, p['at'][1] + h / 2
        lines = [ln for ln in LINES.get(rid, []) if ln[2] == geo.ROOMS[rid]['floor'] and pid not in (ln[3], ln[4])]
        if not lines:
            continue
        dd, ln = min((seg_rect(ln[0], ln[1], x0, y0, x1, y1), ln) for ln in lines)
        if dd < 64:
            bad += 1
            print(f"{rid:20s} platform {pid or p.get('notes', '')[:30]:32s} at {p['at']} {w}x{h} rise {p['rise']}: "
                  f"{dd:5.0f} < 64 from {ln[3]} - {ln[4]}")
        elif SHOW_ALL:
            print(f"  ok {rid:20s} platform {pid or p.get('notes', '')[:30]:32s} {dd:5.0f}")
for rid, msg in rows:
    if SHOW_ALL:
        print(f'  -- {rid} {msg}')
print('offenders', bad)
