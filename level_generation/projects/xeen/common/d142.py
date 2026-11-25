"""D-142 (2026-11-25, F64: monsters too near arrivals and roads) for the outdoor generators.

The rule (devdocs/xeen/DECISIONS.md D-142, checked on the built map by tools/xeen/check_arrivals.py `first_fight()`
through x2/check_d85.py and common/d85.py): from a map-edge arrival, a new game's start and (on the maps rebuilt under
the rule, check_arrivals.D142_EXITS) a dungeon exit, no spawn marker nearer than 4,096 (2D, less its radius), 5,888 if
any row its slot can roll shoots or casts; town arrivals keep D-15's 2,000; marker centres 1,024 from a road's
centreline (the sketch's `roads`: roads, lanes and paths).

A sketch's encounter area is a circle (`at`, `r` in cells); the studio puts its markers anywhere inside it, so a
circle passes when its nearest edge does: (centre distance - r) * 512 - the scene radius (32) >= the floor.

`arrivals(stem)`: the map's arrival points in cells with their kind, read from the installed map (its studio file,
the world tables and every Lua that moves the party onto it: x2/check_d85.arrival_points), plus `extra` points.
`floor_cells(stem, slot, kind)`: the floor of a slot's markers from an arrival of that kind, in cells.
`spot_ok(...)`: a circle's centre meets every floor, the road setback and D-85's 5,888 from the talking givers.
`enforce(stem, areas, roads, slot_of, ok)`: moves each failing encounter circle to the nearest spot (whole cells,
that passes and that the map's own `ok(x, y, r)` accepts, at least 2 cells from the other circles; prints each move
and stops the build when none is found.
"""
from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]


def _load(name, path):
    """Import a checker by path, leaving sys.path as it was (the maps' own modules share names with tools/xeen's)."""
    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path[:] = saved


CA = _load('check_arrivals', REPO / 'tools' / 'xeen' / 'check_arrivals.py')
CD = _load('check_d85', REPO / 'level_generation' / 'projects' / 'xeen' / 'x2' / 'check_d85.py')

ASSETS = REPO / 'assets_dev'
MAPS = ASSETS / 'worlds' / 'xeen' / 'maps'
SCENE_RADIUS = 32
GIVER_RANGE = 5888.0
MARGIN = 0.1            # cells on top of every floor
SPACING = 2.0           # cells between the circles' centres, as the samplers keep them
Loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
_WORLD = None


def world():
    global _WORLD
    if _WORLD is None:
        _WORLD = CA.World(str(ASSETS))
    return _WORLD


def cells(p):
    return (p[0] / 512.0 + 64.0, 64.0 - p[1] / 512.0)


def arrivals(stem, extra=()):
    """[(labels, (x, y) cells, kind)] of the installed map, plus `extra` [(label, (x, y) cells, kind)]."""
    fname = stem + '.odm'
    scene_path = MAPS / (stem + '.scene.yml')
    scene = yaml.load(open(scene_path), Loader=Loader)
    map_id = world().map_ids.get(fname)
    out = []
    for names, p in CD.arrival_points(scene, scene_path, stem, fname, map_id):
        out.append((names, cells(p), CA.arrival_kind(world(), names, fname)))
    out += [([n], tuple(p), k) for n, p, k in extra]
    return out


def givers(stem):
    scene = yaml.load(open(MAPS / (stem + '.scene.yml')), Loader=Loader)
    return [cells((a['position']['x'], a['position']['y'])) for a in scene['initial_state'].get('actors') or []
            if a.get('npc_id')]


def ranged(stem, slot):
    return any(world().shoots(m) for m in world().slot_rows(stem + '.odm', slot))


def floor_units(stem, slot, kind):
    if kind in ('edge', 'start') or (kind == 'exit' and stem in CA.D142_EXITS):
        return CA.EDGE_FLOOR_RANGED if ranged(stem, slot) else CA.EDGE_FLOOR
    return CA.FIRST_FIGHT


def floor_cells(stem, slot, kind):
    return (floor_units(stem, slot, kind) + SCENE_RADIUS) / 512.0 + MARGIN


def road_cells(sketch_path):
    """A sketch's `roads` lines (roads, lanes, paths) in cells."""
    return [r['line'] for r in (yaml.load(open(sketch_path), Loader=Loader).get('roads') or []) if r.get('line')]


def line_dist(x, y, line):
    best = 1e9
    for a, b in zip(line, line[1:]):
        best = min(best, CA.segment_distance((x, y), a, b))
    return best


class Rule:
    """The floors of one map, precomputed: `ok(x, y, r, slot)`."""

    def __init__(self, stem, roads, extra=(), giver_range=GIVER_RANGE):
        self.stem = stem
        self.arr = arrivals(stem, extra)
        self.roads = [ln for ln in roads if len(ln) >= 2]
        self.givers = givers(stem)
        self.giver_cells = (giver_range + SCENE_RADIUS) / 512.0 + MARGIN
        self.floors = {}

    def floor(self, slot, kind):
        key = (slot, kind)
        if key not in self.floors:
            self.floors[key] = floor_cells(self.stem, slot, kind)
        return self.floors[key]

    def why_not(self, x, y, r, slot, givers=True):
        """'' when a circle at (x, y) of radius r cells of this slot meets D-142 (and, with `givers`, D-85's range to
        the talking givers: a moved circle keeps it; one that stays is D-85's checker's business)."""
        for names, a, kind in self.arr:
            d = math.hypot(x - a[0], y - a[1]) - r
            if d < self.floor(slot, kind):
                return '%s arrival %s %.0f < %.0f' % (kind, names[0], d * 512 - SCENE_RADIUS,
                                                      floor_units(self.stem, slot, kind))
        for line in self.roads:
            d = line_dist(x, y, line) - r
            if d < CA.ROAD_SETBACK / 512.0 + MARGIN:
                return 'road %.0f' % (d * 512)
        for g in self.givers if givers else ():
            if math.hypot(x - g[0], y - g[1]) - r < self.giver_cells:
                return 'giver at %s' % (g,)
        return ''


def _slot(a, slot_of):
    """An encounter circle's slot (1-3): its own `slot`, else `slot_of` (a dict or a function of the population id)."""
    if 'circle' not in a or a.get('kind') not in (None, 'encounter'):
        return None
    if a.get('slot'):
        return a['slot']
    if slot_of is None:
        return None
    return slot_of.get(a['id']) if isinstance(slot_of, dict) else slot_of(a['id'])


def enforce(stem, areas, roads, slot_of, ok, extra=(), giver_range=GIVER_RANGE, lo=19, hi=109, step=1,
            fixed=(), also=None):
    """Move each encounter circle of `areas` that fails D-142 to the nearest passing spot `ok(x, y, r)` accepts.
    `slot_of`: {pop: slot} or a function of the population id -> 1-3 or None (not a slotted population: left alone);
    an area's own `slot` wins. `fixed`: circles that stay (a failure
    stops the build). `also(x, y, r)`: a further reason to move a circle ('' when none; e.g. hull_reason()'s F63
    clearance), its new spot is held to `ok` as any other. Returns the moves [(pop, index, old, new, reason)]."""
    rule = Rule(stem, roads, extra, giver_range)
    enc = [a for a in areas if _slot(a, slot_of)]
    moves = []
    for a in enc:
        c = a['circle']
        x, y = c['at']
        r = c['r']
        slot = _slot(a, slot_of)
        why = rule.why_not(x, y, r, slot, givers=False) or (also(x, y, r) if also else '')
        if not why:
            continue
        if (a['id'], a.get('index')) in fixed:
            raise SystemExit('D-142: %s %s at %s: %s' % (a['id'], a.get('index'), (x, y), why))
        others = [b['circle'] for b in areas if b is not a and 'circle' in b and b.get('kind') in (None, 'encounter')]
        best = None
        gy = lo
        while gy <= hi:
            gx = lo
            while gx <= hi:
                d = math.hypot(gx - x, gy - y)
                if (best is None or d < best[0]) and \
                        all(math.hypot(gx - o['at'][0], gy - o['at'][1]) >= SPACING + max(0.0, o['r'] + r - 1.0)
                            for o in others) and \
                        not rule.why_not(gx, gy, r, slot) and ok(gx, gy, r):
                    best = (d, gx, gy)
                gx += step
            gy += step
        if best is None:
            raise SystemExit('D-142: no place for %s %s (%s): %s' % (a['id'], a.get('index'), (x, y), why))
        new = [best[1], best[2]]
        new = [int(v) if float(v).is_integer() else v for v in new]
        print('D-142: %s %s %s -> %s (%s)' % (a['id'], a.get('index'), [x, y], new, why))
        moves.append((a['id'], a.get('index'), (x, y), tuple(new), why))
        c['at'] = new
    return moves


def _inside(poly, x, y):
    hit = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def _poly_dist(poly, x, y):
    return line_dist(x, y, list(poly) + [poly[0]])


def standard_ok(sketch_path, height=None, keep_off=(), steep=300.0, hull=1.5, wet=None):
    """A map's `ok(x, y, r)` for a moved circle, from its last sketch (the L4 being replaced: the void, the water, the
    structures barely move between runs) and the generator's own `height(x, y)` (cells -> units): inside the bounds and
    `hull` cells plus r from the void's edge (check_spawn_clear's 768), off the water and its rivers, a cell and a half
    from the structures (two from a building's box, the districts' houses too), no 4-corner rise over `steep` at the
    middle or r out, and outside `keep_off` polygons (cells) by r. `wet(x, y)`: the generator's own water test, if any."""
    rim = sys.modules.get('rim') or _load('rim', Path(__file__).resolve().parent / 'rim.py')
    sk = yaml.load(open(sketch_path), Loader=Loader)
    voids = rim.void_polygons(sk)
    water = [b['polygon'] for b in (sk.get('water') or {}).get('bodies') or [] if b.get('polygon')]
    rivers = [(r['line'], (r.get('width') or 1.0) / 2.0) for r in (sk.get('water') or {}).get('rivers') or []
              if r.get('line')]
    points, boxes, lines = [], [], []
    for st in sk.get('structures') or []:
        if 'line' in st:
            lines.append([p[:2] for p in st['line']])   # a line's points may carry a height (D2's rope walks)
        elif 'size' in st and 'at' in st:
            size = st['size'] if isinstance(st['size'], (list, tuple)) else [st['size'], st['size']]
            half = max(size[0], size[-1]) / 2.0
            boxes.append((st['at'], half / 512.0 if half > 16 else half))   # units (a model's size) or cells
        elif 'at' in st:
            points.append(st['at'])
    # the houses of the districts' plots (2026-11-25: X2's moved rangers' circle stood on farmstead 1, F63): `at` is
    # the plot's corner (cells), each part's `at` and `size` units within it
    for district in sk.get('districts') or []:
        for b in district.get('plots') or []:
            for part in b.get('parts') or []:
                if 'at' in b and 'size' in part:
                    pa, ps = part.get('at') or [0, 0], part['size']
                    mid = [b['at'][0] + (pa[0] + ps[0] / 2.0) / 512.0, b['at'][1] + (pa[1] + ps[1] / 2.0) / 512.0]
                    boxes.append((mid, max(ps) / 1024.0))
    lo, hi = -23143 / 512.0 + 64 + 37 / 512.0, 23143 / 512.0 + 64 - 37 / 512.0

    def ok(x, y, r):
        m = hull + r
        if not (lo + m <= x <= hi - m and lo + m <= y <= hi - m):
            return False
        if voids and (rim.in_void(voids, x, y) or (rim.nearest_edge(voids, x, y) or (1e9,))[0] < m):
            return False
        if any(_inside(w, x, y) or _poly_dist(w, x, y) < r + 0.5 for w in water):
            return False
        if any(line_dist(x, y, ln) < r + w + 0.75 for ln, w in rivers):
            return False
        if any(math.hypot(x - q[0], y - q[1]) < r + 1.5 for q in points):
            return False
        if any(math.hypot(x - q[0], y - q[1]) < r + h + 2.0 for q, h in boxes):
            return False
        if any(line_dist(x, y, ln) < r + 1.0 for ln in lines):
            return False
        if any(_inside(k, x, y) or _poly_dist(k, x, y) < r for k in keep_off):
            return False
        if wet and any(wet(x + dx, y + dy) for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))):
            return False
        if height:
            for px, py in ((x, y), (x + r, y), (x - r, y), (x, y + r), (x, y - r)):
                hs = [height(px + dx, py + dy) for dx in (-0.5, 0.5) for dy in (-0.5, 0.5)]
                if max(hs) - min(hs) > steep:
                    return False
        return True
    return ok


def hull_reason(sketch_path, hull=1.5):
    """F63 (2026-11-25, tools/xeen/check_spawn_clear.py `spawn.at_hull`): a function (x, y, r) -> '' when a circle's
    markers stand 768 from the map's bounds and the void's edge wherever the studio puts them in it, else the reason
    (for enforce()'s `also`)."""
    rim = sys.modules.get('rim') or _load('rim', Path(__file__).resolve().parent / 'rim.py')
    voids = rim.void_polygons(yaml.load(open(sketch_path), Loader=Loader))
    bound = 23143 / 512.0

    def why(x, y, r):
        edge = bound - max(abs(x - 64.0), abs(64.0 - y)) - r
        if edge < hull:
            return 'F63 bounds %.0f' % (edge * 512)
        if voids:
            if rim.in_void(voids, x, y):
                return 'F63 in the void'
            near = (rim.nearest_edge(voids, x, y) or (1e9,))[0] - r
            if near < hull:
                return 'F63 hull %.0f' % (near * 512)
        return ''
    return why


def check(stem, areas, roads, slot_of, extra=(), giver_range=GIVER_RANGE):
    """The failing encounter circles, [(pop, index, (x, y), reason)] (no move)."""
    rule = Rule(stem, roads, extra, giver_range)
    out = []
    for a in areas:
        if _slot(a, slot_of):
            c = a['circle']
            why = rule.why_not(c['at'][0], c['at'][1], c['r'], _slot(a, slot_of), givers=False)
            if why:
                out.append((a['id'], a.get('index'), tuple(c['at']), why))
    return out
