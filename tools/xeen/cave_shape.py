"""Cave shape for a Xeen dungeon's L4 (D-89 identity; lane A7, 2026-11-22).

The rooms of a cave or mine are drawn as boxes by the generators; shipped caves (MM8 d17, d12, d13, MM7 7d07, 7d08)
have broken outlines, rough walls, floors that rise and fall and vaulted roofs. `oymap audit` warns
(`identity.cave_shape`) when a map whose `identity.shape` is cave or mine falls below their numbers. This pass, called
by a map's gen.py after it has written L4, reshapes the natural rooms of `rooms.yml` in place, deterministically:

- **corners:** an axis-aligned rectangle loses each corner on a slant with a break pushed in (up to 12 sides); a
  corner stays square where another room comes near it (a shared wall may carry an opening) or where an object of the
  room stands in the cut;
- **rough walls** (`rough`), unless the room has its own;
- **floor:** points inside the room rise and fall (`floor_points`, at most `floor` up or down); the walls' feet, so
  every opening's sill, stay at the room's floor; under each object, level, platform and hole the floor is pinned at
  the room's floor (an anchor point) so nothing floats or sinks;
- **roof:** points inside the room rise above `ceiling` (`ceiling_points`, never lower);
- **stalactites** in rooms high enough.

Rooms with their own shape stay as they are: paths, `slope`, `section`, `walls`, `ceiling_slope`, `ceiling_levels`,
`beams`, `floor_points`/`ceiling_points` already given (each part is skipped on its own).

Usage from gen.py, after L4 is written:
    sys.path.insert(0, str(ROOT / 'tools' / 'xeen')); import cave_shape
    cave_shape.shape_l4(BRIEF / 'L4', CAVES)
CAVES maps room ids to dicts of: cut (corner cut, 0 none), keep (corners kept square: 'sw', 'se', 'ne', 'nw'),
floor (floor amplitude), roof (roof rise), stalactites ((count, length) or None), rough (dict or None for the map's
default), step (point grid), path_rough (True: a `path` room without slope or section takes rough walls; paths are
otherwise left).  Missing keys take DEFAULTS.

Wall-hung objects (`wall:` decorations, torches): oymap hangs them on the plan's wall, so a rough wall's pushed-in
faces can cover them (audit `lights.in_solid`); keep rough off a room whose wall torches the audit then finds in rock.
"""
import hashlib
import math
from pathlib import Path

import yaml

DEFAULTS = {'cut': 256, 'keep': (), 'floor': 64, 'roof': 192, 'stalactites': None, 'rough': None, 'step': 320}
ROUGH = {'step': 192, 'depth': 48}
NOT_OBSTACLES = ('lights', 'sounds', 'format', 'fog', 'notes')


def _h(*k):
    return int(hashlib.md5(repr(k).encode()).hexdigest()[:8], 16) / 0xffffffff


def _bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _room_boxes(room):
    """Boxes (x0, y0, x1, y1) covering a room's plan: its outline's box, or each path leg widened by half its width."""
    if 'outline' in room:
        return [_bbox(room['outline'])]
    if 'path' in room:
        w = (room.get('width') or 256) / 2
        p = room['path']
        out = []
        for a, b in zip(p, p[1:]):
            out.append((min(a[0], b[0]) - w, min(a[1], b[1]) - w, max(a[0], b[0]) + w, max(a[1], b[1]) + w))
        return out
    return []


def _hit(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _is_rect(outline):
    if len(outline) != 4:
        return False
    x0, y0, x1, y1 = _bbox(outline)
    return all(p[0] in (x0, x1) and p[1] in (y0, y1) for p in outline)


def _inside(pt, poly):
    x, y = pt
    c = False
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def _wall_dist(pt, poly):
    return min(_seg_dist(pt, a, b) for a, b in zip(poly, poly[1:] + poly[:1]))


# Objects that stand on whatever floor is under them (the studio drops them onto it): they keep a cut corner off
# them but not the floor's rises. Everything else (levels, plates, liquids, ladders, lifts, exits, arrivals, objects
# at a given height, holes) needs the floor level round it.
STANDS = ('decorations', 'chests', 'monsters', 'spawns', 'destructibles', 'placeholders')


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _proper_cross(a, b, c, d):
    d1, d2, d3, d4 = _cross(c, d, a), _cross(c, d, b), _cross(a, b, c), _cross(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and 0 not in (d1, d2, d3, d4)


def _triangles(poly, pts):
    """The studio's triangulation of an uneven floor, as its validator describes it: between the outline's corners
    and the points, the shortest lines first. Returns triangles as index triples into poly + pts."""
    allp = [tuple(q[:2]) for q in poly] + [tuple(q[:2]) for q in pts]
    n = len(allp)
    edges = []
    ring = list(zip(range(len(poly)), list(range(1, len(poly))) + [0]))
    accepted = set(tuple(sorted(e)) for e in ring)
    cand = []
    for i in range(n):
        for j in range(i + 1, n):
            if (i, j) in accepted:
                continue
            a, b = allp[i], allp[j]
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if not _inside(mid, [list(q) for q in poly]):
                continue
            cand.append((math.hypot(a[0] - b[0], a[1] - b[1]), i, j))
    cand.sort()
    edges = [(allp[i], allp[j]) for i, j in accepted]
    for _, i, j in cand:
        a, b = allp[i], allp[j]
        if any(_proper_cross(a, b, c, d) for c, d in edges):
            continue
        accepted.add((i, j))
        edges.append((a, b))
    adj = {i: set() for i in range(n)}
    for i, j in accepted:
        adj[i].add(j)
        adj[j].add(i)
    tris = []
    for i in range(n):
        for j in adj[i]:
            if j <= i:
                continue
            for k in adj[i] & adj[j]:
                if k <= j:
                    continue
                a, b, c = allp[i], allp[j], allp[k]
                area = _cross(a, b, c)
                if area == 0:
                    continue
                inside = False
                for m in range(n):
                    if m in (i, j, k):
                        continue
                    p_ = allp[m]
                    s1, s2, s3 = _cross(a, b, p_), _cross(b, c, p_), _cross(c, a, p_)
                    if (s1 > 0 and s2 > 0 and s3 > 0) or (s1 < 0 and s2 < 0 and s3 < 0):
                        inside = True
                        break
                if not inside:
                    tris.append((i, j, k))
    return tris


def _slope(a, b, c):
    """Rise per unit of run of the plane through three [x, y, z] points."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    if nz == 0:
        return 99.0
    return math.hypot(nx, ny) / abs(nz)


def tame(poly, base, pts, limit):
    """Drop the points whose triangles are steeper than `limit` (the worst first) until none is."""
    pts = [list(q) for q in pts]
    for _ in range(len(pts) + 1):
        if not pts:
            return pts
        corners = [[q[0], q[1], base] for q in poly]
        allp = corners + pts
        worst = None
        for t in _triangles(poly, pts):
            sl = _slope(*(allp[i] for i in t))
            if sl > limit and (worst is None or sl > worst[0]):
                worst = (sl, t)
        if worst is None:
            return pts
        movable = [i - len(poly) for i in worst[1] if i >= len(poly)]
        if not movable:
            return pts
        drop = max(movable, key=lambda m: abs(pts[m][2] - base))
        pts.pop(drop)
    return pts


def _cover(add, rid, outline):
    """Small circles over a plan (a block, a plate) every 128 or less, its corners among them."""
    x0, y0, x1, y1 = _bbox(outline)
    nx, ny = max(1, round((x1 - x0) / 128)), max(1, round((y1 - y0) / 128))
    add(rid, (x0 + x1) / 2, (y0 + y1) / 2, 96)
    for i in range(nx + 1):
        for j in range(ny + 1):
            add(rid, x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, 96)
    if len(outline) > 2:  # and its own corners and rim, so the floor is level exactly along its edge
        for a, b in zip(outline, outline[1:] + outline[:1]):
            n = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / 128))
            for i in range(n):
                add(rid, a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, 64)


def obstacles(rooms_doc, objects, level_only=False):
    """Per room: (x, y, radius) of everything that stands on its floor (level_only: that needs it level)."""
    ob = {}

    def add(rid, x, y, r):
        ob.setdefault(rid, []).append((x, y, r))
    for key, items in (objects or {}).items():
        if key in NOT_OBSTACLES or not isinstance(items, list):
            continue
        for o in items:
            if not isinstance(o, dict) or 'room' not in o:
                continue
            if level_only and key in STANDS and 'floor_height' not in o:
                continue
            if 'at' in o and len(o['at']) >= 2:
                size = o.get('size') or [128, 128]
                if level_only and isinstance(size, list) and len(size) >= 2:
                    h = max(size[:2]) / 2  # either way round (a facing turns it)
                    x, y = o['at'][0], o['at'][1]
                    _cover(add, o['room'], [[x - h, y - h], [x + h, y + h]])
                    continue
                r = max(size[:2]) / 2 + 48 if isinstance(size, list) else 112
                add(o['room'], o['at'][0], o['at'][1], max(r, 96))
            elif 'outline' in o and level_only:
                _cover(add, o['room'], o['outline'])
            elif 'outline' in o:
                x0, y0, x1, y1 = _bbox(o['outline'])
                add(o['room'], (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 + 64)
    for r in rooms_doc['rooms']:
        for key in ('platforms', 'levels', 'pillars', 'stalagmites'):
            for p in r.get(key, []) or []:
                # under a block the floor stays level (its top follows the floor under it): the block's plan is
                # covered with small circles so no rise lands inside it
                if level_only and 'outline' in p:
                    bank = p.get('bank') or 0
                    m = max(bank) if isinstance(bank, list) else bank
                    if m:  # a level's banks widen its rim
                        x0, y0, x1, y1 = _bbox(p['outline'])
                        _cover(add, r['id'], [[x0 - m, y0 - m], [x1 + m, y0 - m], [x1 + m, y1 + m], [x0 - m, y1 + m]])
                    _cover(add, r['id'], p['outline'])
                    continue
                if 'outline' in p:
                    x0, y0, x1, y1 = _bbox(p['outline'])
                    add(r['id'], (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 + 96)
                elif 'at' in p:
                    size = p.get('size') or [p.get('radius', 96) * 2] * 2
                    add(r['id'], p['at'][0], p['at'][1], max(size[:2]) / 2 + 96)
    for o in rooms_doc.get('openings', []):
        if o.get('in') in ('floor', 'ceiling') and 'at' in o:
            size = o.get('size') or [256, 256]
            for rid in (o['from'], o['to']):
                add(rid, o['at'][0], o['at'][1], max(size) / 2 + 96)
    return ob


def cut_corners(room, cmax, keep, others, obst):
    """The room's rectangle with each corner cut on a slant up to cmax, a break pushed in; corners near another room
    or an object stay square (or are cut less)."""
    x0, y0, x1, y1 = _bbox(room['outline'])
    corners = {'sw': (x0, y0, 1, 1), 'se': (x1, y0, -1, 1), 'ne': (x1, y1, -1, -1), 'nw': (x0, y1, 1, -1)}
    rid = room['id']
    cut = {}
    for name, (cx, cy, sx, sy) in corners.items():
        c = 0 if name in keep else min(cmax, (x1 - x0) // 3, (y1 - y0) // 3)
        for ox, oy, orad in obst:
            c = min(c, abs(ox - cx) + abs(oy - cy) - int(orad * 1.42) - 32)
        while c >= 96:
            # a neighbour's plan within the cut's legs (plus room for an opening's jamb) keeps the corner
            zx = sorted((cx - sx * 64, cx + sx * (c + 160)))
            zy = sorted((cy - sy * 64, cy + sy * (c + 160)))
            zone = (zx[0], zy[0], zx[1], zy[1])
            if not any(_hit(zone, b) for b in others):
                break
            c -= 64
        c = max(0, c) // 32 * 32
        cut[name] = c if c >= 96 else 0
    pts = []
    for name in ('sw', 'se', 'ne', 'nw'):
        cx, cy, sx, sy = corners[name]
        c = cut[name]
        if not c:
            pts.append([cx, cy])
            continue
        k = 0.12 + 0.14 * _h(rid, name)
        mid = [round(cx + sx * c * (0.5 + k)), round(cy + sy * c * (0.5 + k))]
        if name == 'sw':
            pts += [[cx, cy + c], mid, [cx + c, cy]]
        elif name == 'se':
            pts += [[cx - c, cy], mid, [cx, cy + c]]
        elif name == 'ne':
            pts += [[cx, cy - c], mid, [cx - c, cy]]
        else:
            pts += [[cx + c, cy], mid, [cx, cy - c]]
    room['outline'] = pts
    return cut


def _grid(room, step, margin):
    x0, y0, x1, y1 = _bbox(room['outline'])
    out = []
    nx = max(1, int((x1 - x0 - 2 * margin) // step) + 1)
    ny = max(1, int((y1 - y0 - 2 * margin) // step) + 1)
    if x1 - x0 < 2 * margin or y1 - y0 < 2 * margin:
        return out
    ox = x0 + (x1 - x0 - (nx - 1) * step) / 2
    oy = y0 + (y1 - y0 - (ny - 1) * step) / 2
    for i in range(nx):
        for j in range(ny):
            out.append((round(ox + i * step), round(oy + j * step)))
    return out


def floor_bumps(room, amp, step, obst, below=()):
    poly = room['outline']
    x0, y0, x1, y1 = _bbox(poly)
    margin = max(160, min(384, min(x1 - x0, y1 - y0) / 4))
    f = room['floor']
    pts = []
    for x, y in _grid(room, step, margin):
        if not _inside((x, y), poly) or _wall_dist((x, y), poly) < margin - 32:
            continue
        if any(math.hypot(x - ox, y - oy) < orad + 48 for ox, oy, orad in obst):
            continue
        dz = round((_h(room['id'], 'fz', x, y) * 2 - 1) * amp / 16) * 16
        for b, top in below:  # a room under this one: no dip toward its roof
            if _hit((x - 96, y - 96, x + 96, y + 96), b):
                dz = max(dz, 0)
        if abs(dz) >= 16:
            pts.append([x, y, f + dz])
    if not pts:
        return 0
    # pin the floor at its height under everything that needs it level
    for ox, oy, orad in obst:
        if not _inside((ox, oy), poly):
            continue
        pts.append([round(ox), round(oy), f])
    # the walls' feet at the floor, a point every two thirds of a step along each wall: the triangles then run from
    # the wall to the nearest rise, never in slivers from far corners
    feet = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        n = int(length // (step * 0.66))
        for i in range(1, n + 1):
            t = i / (n + 1)
            x, y = a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])
            # 96 inside the wall (not on it: a point on a wall is a corner of it, and rough walls break only long
            # stretches)
            nx, ny = -(b[1] - a[1]) / length, (b[0] - a[0]) / length
            q = (round(x + nx * 96), round(y + ny * 96))
            if not _inside(q, poly):
                q = (round(x - nx * 96), round(y - ny * 96))
            if _inside(q, poly) and _wall_dist(q, poly) >= 80:
                feet.append([q[0], q[1], f])
    seen, uniq = set(), []
    for q in pts + feet:  # one height per place: a rise wins over a foot or an anchor at the same spot
        if (q[0], q[1]) not in seen and all(math.hypot(q[0] - u[0], q[1] - u[1]) >= 48 for u in uniq):
            seen.add((q[0], q[1]))
            uniq.append(q)
    pts = tame(poly, f, uniq[:190], 0.8)  # the studio takes up to 192 points
    if any(q[2] != f for q in pts):
        room['floor_points'] = pts
    return len([q for q in pts if q[2] != f])


def vault(room, rise, step, above=()):
    poly = room['outline']
    x0, y0, x1, y1 = _bbox(poly)
    margin = max(160, min(448, min(x1 - x0, y1 - y0) / 4))
    pts = []
    for x, y in _grid(room, int(step * 1.5), margin):
        if not _inside((x, y), poly) or _wall_dist((x, y), poly) < margin - 32:
            continue
        dz = round((0.45 + 0.55 * _h(room['id'], 'cz', x, y)) * rise / 16) * 16
        for b, bottom in above:  # a room over this one: the roof stays under its floor
            if _hit((x - 160, y - 160, x + 160, y + 160), b):
                dz = min(dz, (bottom - 48 - room['ceiling']) // 16 * 16)
        if dz >= 16:
            pts.append([x, y, room['ceiling'] + dz])
    pts = tame(poly, room['ceiling'], pts, 3.0)
    if pts:
        room['ceiling_points'] = pts
    return len(pts)


def stalactites(room, n, length, obst, surface):
    poly = room['outline']
    x0, y0, x1, y1 = _bbox(poly)
    out = []
    for i in range(n * 3):
        if len(out) >= n:
            break
        x = round(x0 + 256 + _h(room['id'], 'sx', i) * (x1 - x0 - 512))
        y = round(y0 + 256 + _h(room['id'], 'sy', i) * (y1 - y0 - 512))
        if not _inside((x, y), poly) or _wall_dist((x, y), poly) < 192:
            continue
        if any(math.hypot(x - ox, y - oy) < orad + 160 for ox, oy, orad in obst):
            continue
        if any(math.hypot(x - q['at'][0], y - q['at'][1]) < 320 for q in out):
            continue
        s = {'at': [x, y], 'radius': 64 + round(_h(room['id'], 'sr', i) * 2) * 16, 'length': length}
        if surface:
            s['surface'] = surface
        out.append(s)
    if out:
        room['stalactites'] = out
    return len(out)


def shape_rooms(rooms_doc, objects, caves, rough=None):
    """Reshape the rooms named in `caves` in place; returns a short report per room."""
    obst = obstacles(rooms_doc, objects)
    level = obstacles(rooms_doc, objects, level_only=True)
    themes = {t['id']: t for t in rooms_doc.get('themes', [])}
    default_theme = (rooms_doc.get('defaults') or {}).get('theme')
    by_id = {r['id']: r for r in rooms_doc['rooms']}
    # a room with a hole in its floor or roof keeps both level (the studio's rule for `in: floor` openings)
    # (`in: floor`: the upper room is `from`, its floor level, the lower `to`, its roof level; `in: ceiling` the
    # other way round)
    ops = rooms_doc.get('openings', [])
    level_floor = {o['from'] if o['in'] == 'floor' else o['to'] for o in ops if o.get('in') in ('floor', 'ceiling')}
    level_roof = {o['to'] if o['in'] == 'floor' else o['from'] for o in ops if o.get('in') in ('floor', 'ceiling')}
    report = {}
    for rid, spec in caves.items():
        sp = dict(DEFAULTS, **(spec or {}))
        r = by_id[rid]
        if 'outline' not in r:
            # a tunnel (`path`) takes rough walls when its spec asks (`path_rough: True`); never with a slope or a
            # cross-section of its own (A7 s29: XD-05's upper ledge),
            # nor with a hole in its floor or roof (the studio cuts a hole clear of the walls: DD-11B's gallery)
            if rid in level_floor or rid in level_roof:
                report[rid] = 'path with a hole: left'
            elif (spec or {}).get('path_rough') and 'path' in r and not any(k in r for k in ('rough', 'slope', 'section')):
                r['rough'] = dict(sp['rough'] or rough or ROUGH)
                report[rid] = 'path: rough'
            else:
                report[rid] = 'no outline: left'
            continue
        done = []
        others = [b for o in rooms_doc['rooms'] if o['id'] != rid for b in _room_boxes(o)]
        ob = obst.get(rid, [])
        # an opening that names this room's wall by its number keeps the outline's corners where they are
        numbered = any((o.get('from') == rid and isinstance(o.get('from_wall'), int))
                       or (o.get('to') == rid and isinstance(o.get('to_wall'), int))
                       for o in rooms_doc.get('openings', []))
        if sp['cut'] and _is_rect(r['outline']) and 'walls' not in r and not numbered:
            c = cut_corners(r, sp['cut'], sp['keep'], others, ob)
            done.append('cut ' + '/'.join(f'{k}{v}' for k, v in c.items() if v))
        if 'rough' not in r and 'slope' not in r:
            r['rough'] = dict(sp['rough'] or rough or ROUGH)
            done.append('rough')
        if sp['floor'] and rid not in level_floor and 'floor_points' not in r and 'slope' not in r and 'floor_plane' not in r:
            below = [(b, o['ceiling']) for o in rooms_doc['rooms'] if o['id'] != rid and o['ceiling'] <= r['floor']
                     for b in _room_boxes(o)]
            n = floor_bumps(r, sp['floor'], sp['step'], level.get(rid, []), below)
            done.append(f'floor {n}')
        free_roof = not any(k in r for k in ('ceiling_points', 'ceiling_slope', 'ceiling_levels', 'ceiling_plane',
                                              'beams', 'section'))
        if sp['roof'] and free_roof and rid not in level_roof:
            above = [(b, o['floor']) for o in rooms_doc['rooms'] if o['id'] != rid and o['floor'] >= r['ceiling']
                     for b in _room_boxes(o)]
            n = vault(r, sp['roof'], sp['step'], above)
            done.append(f'roof {n}')
        if sp['stalactites'] and 'stalactites' not in r:
            th = themes.get(r.get('theme') or default_theme) or {}
            n = stalactites(r, sp['stalactites'][0], sp['stalactites'][1], ob, th.get('ceiling'))
            done.append(f'stalactites {n}')
        report[rid] = ', '.join(done)
    for rid, n in flat_behind_panels(rooms_doc, objects).items():
        report[rid] = (report.get(rid) or 'own rough') + f', flat behind {n} exit/switch'
    return report


PANEL_KINDS = ('exits', 'switches')
PANEL_MARGIN = 32
COMPASS = {'east': 0.0, 'north': 90.0, 'west': 180.0, 'south': 270.0}


def _find_edge(outline, wall):
    """The outline edge a `wall:` names, as the studio's findWall: an edge number, or the edge whose outward side
    looks most nearly toward the compass side (the first of equals)."""
    if isinstance(wall, int):
        return wall
    if wall not in COMPASS:
        return None
    a = math.radians(COMPASS[wall])
    best, fit = None, -2.0
    for i, p in enumerate(outline):
        q = outline[(i + 1) % len(outline)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(dx, dy)
        f = (dy * math.cos(a) - dx * math.sin(a)) / length  # outward of a counter-clockwise outline: (dy, -dx)
        if f > fit + 1e-6:
            best, fit = i, f
    return best


def flat_behind_panels(rooms_doc, objects):
    """A rough wall keeps flat behind an exit or switch on it (the Discord report of 2026-11-23, XD-05: the studio
    hangs a wall object 2 in front of the plan's wall line, and a rough wall's joints stand up to `depth` into the
    room, so the black exit of the Orc Caves' mouth lay wholly behind rock and no click reached it). Each such object
    on a wall of a room with `rough` walls gets a wall panel (`walls[].panels`) under it, its width and 32 more each
    side: the studio builds a panelled stretch flat. Objects placed by a point (`at`) are left to the check
    (`tools/xeen/check_exits.py`, `exits.hidden`). Returns {room id: count}."""
    by_id = {r['id']: r for r in rooms_doc['rooms']}
    themes = {t['id']: t for t in rooms_doc.get('themes', [])}
    default_theme = (rooms_doc.get('defaults') or {}).get('theme')
    out = {}
    for kind in PANEL_KINDS:
        for o in (objects or {}).get(kind) or []:
            r = by_id.get(o.get('room'))
            if not r or 'rough' not in r or 'outline' not in r or 'wall' not in o or 'at' in o:
                continue
            edge = _find_edge(r['outline'], o['wall'])
            if edge is None:
                continue
            p, q = r['outline'][edge], r['outline'][(edge + 1) % len(r['outline'])]
            length = math.hypot(q[0] - p[0], q[1] - p[1])
            width = (o.get('size') or [192, 256])[0]
            centre = round(o.get('along', 0.5) * length)
            low = max(0.0, centre - width // 2 - PANEL_MARGIN)
            high = min(length, centre - width // 2 + width + PANEL_MARGIN)
            walls = r.setdefault('walls', [])
            entry = next((w for w in walls if w.get('wall') == o['wall']), None)
            # the wall's own picture (its `walls` entry, the room's `wall`, else its theme's)
            surface = ((entry or {}).get('surface') or r.get('wall')
                       or (themes.get(r.get('theme') or default_theme) or {}).get('wall'))
            if not surface:
                continue
            panel = {'offset': int(math.floor(low)), 'length': int(math.floor(high - low)), 'surface': dict(surface),
                     'notes': f'flat behind {o["id"]} (a rough wall would stand in front of it)'}
            if entry is None:
                entry = {'wall': o['wall']}
                walls.append(entry)
            if any(pn.get('notes', '').startswith(f'flat behind {o["id"]} ') for pn in entry.get('panels') or []):
                continue
            entry.setdefault('panels', []).append(panel)
            out[r['id']] = out.get(r['id'], 0) + 1
    return out


def flat_panels_l4(l4, log=True):
    """For an L4 whose rough walls come from its own generator, not from shape_l4 (XD-18): flat_behind_panels on
    its rooms.yml."""
    l4 = Path(l4)
    text = (l4 / 'rooms.yml').read_text()
    head = ''.join(line for line in text.splitlines(True)[:40] if line.startswith('#'))
    rooms_doc = yaml.safe_load(text)
    objects = yaml.safe_load((l4 / 'objects.yml').read_text()) if (l4 / 'objects.yml').exists() else {}
    report = flat_behind_panels(rooms_doc, objects)
    if report:
        (l4 / 'rooms.yml').write_text(head + yaml.safe_dump(rooms_doc, sort_keys=False, allow_unicode=True,
                                                             width=120))
    if log:
        for rid, n in report.items():
            print(f'cave_shape {rid}: flat behind {n} exit/switch')
    return report


def shape_l4(l4, caves, rough=None, log=True, cut=None, step=None):
    """Read L4's rooms.yml and objects.yml, reshape the cave rooms, write rooms.yml back."""
    l4 = Path(l4)
    text = (l4 / 'rooms.yml').read_text()
    head = ''.join(line for line in text.splitlines(True)[:40] if line.startswith('#'))
    rooms_doc = yaml.safe_load(text)
    objects = yaml.safe_load((l4 / 'objects.yml').read_text()) if (l4 / 'objects.yml').exists() else {}
    if cut is not None:  # one corner cut for every room (0: none)
        caves = {k: dict(v or {}, cut=cut) for k, v in caves.items()}
    if step is not None:  # the point grid of every room that names none
        caves = {k: dict({'step': step}, **(v or {})) for k, v in caves.items()}
    report = shape_rooms(rooms_doc, objects, caves, rough)
    (l4 / 'rooms.yml').write_text(head + yaml.safe_dump(rooms_doc, sort_keys=False, allow_unicode=True, width=120))
    if log:
        for rid, what in report.items():
            print(f'cave_shape {rid}: {what}')
    return report
