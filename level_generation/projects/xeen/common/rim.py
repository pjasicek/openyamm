"""The world rim as a void, and the world as a ship (U-12; agent xeen-rim, 2026-11-23).

Every Xeen outdoor map ends on one or two sides in the world rim. `apply(sketch, key)` (called from `wild.apply`, which
every outdoor gen.py calls on its finished sketch) does three things:

- **The void.** The sea that stood for the stars under the rim (`water:sky` / `water:rim_sea` at level 0, and X6's
  level-0 cove) becomes the sketch's `void`: cells the game does not draw, the stars below the horizon through them
  (devdocs/xeen/reviews/WORLD_RIM_VOID_20261123.md section 3). Only once the studio reads `void` (its sketch schema
  lists the key); until then the sea stays and the rest still applies.
- **The hull.** Along every edge between the land and the void, the Ancients' hull stands on the land's edge (D-109):
  `xeen_hull4` (2,048 wide) and `xeen_hull1` (512) pieces end to end, a `xeen_hullc` corner piece at every land corner
  the void wraps round; burnt plating (`*bn`) mixed in on D6. A piece is left out where a fall pours over the edge
  (studio waterfalls, the sand-falls and lava falls), so the fall drops through the gap into the void.
- **The falls.** A studio waterfall whose foot is at the void's level (0) builds no foot pool (`pool: 0`) once the void
  is in: nothing floats in empty space.

`tools/xeen/check_rim.py` checks the built maps (TODO when the void is built: void cells, hull runs, no pool).
"""
from __future__ import annotations

import json
import math
import os

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', '..', '..'))
RIM_SEAS = {'water:sky', 'water:rim_sea', 'water:cove'}
FALL_DECORATIONS = {'xeen_sandfall', 'xeen_lavafall'}
PIECE_LONG, PIECE_SHORT = 4, 1          # cells
BURNT_MAPS = {'d6'}
# turn (the studio's decoration facing, degrees): the way the hull's front (glTF +Z) points
# D-109 (agent xeen-rim3): the studio keeps the land's height on the void's outline, so the land runs level to its
# edge; the pieces stand a hair inside it and take the land's height there (their kerb 150 over the grass).
INTO = -0.02                            # cells the pieces stand out into the void (negative: on the land)
VOID_FALL_FOOT = -2400                  # a fall's foot over the void: past the hull's deck (-1,000) toward its underside
# D-112 (agent xeen-rim4): seen from the land a sheet hanging from the lip is hidden by the land's own edge, so a rim
# water fall runs down a spillway in the hull first: a chute on the deck's slope (the hull's flare: 1,760 out, 976
# down), a little past the deck's lip, then the free sheet `lean` out to its foot. The studio builds the spillway's
# plate under the chute (`textures: {deck}`); the hull runs on to the spillway's sides.
VOID_FALL_CHUTE = [1900, 1050]          # out, drop: the deck's slope, leaping 100 past the plate's end
VOID_FALL_LEAN = 300                    # the free sheet's foot beyond the chute's end
FALL_WIDTH = 768                        # a fall's width when the sketch gives none (the studio takes the river's)
DECK_MARGIN = 96                        # the spillway plate beyond the water each side (OutdoorFalls DeckMargin)
# D-109/D-114 (agent xeen-rimmap-b, 2026-11-23): a run shorter than this that ends in an inner corner of the land (a
# notch's wall: X7's lava cove) takes the deckless pieces (`xeen_hull4n`/`1n`, kerb and face straight down), whose
# decks would otherwise close the notch; no corner piece beside it. A sand or lava fall's gap (decorations pouring from
# the lip, no spillway: D-114) holds plain kerbless faces (`xeen_hullf`, burnt `xeen_hullfbn`) instead of nothing.
NOTCH_RUN = 6.0
# F60 X5 p4 (2026-11-25, agent xeen-fb4-outdoor2): a piece stands on the land at its middle, so a long piece over land
# that varies along its span hung its ends over a dip or buried them in a rise (162 long pieces on the 13 maps varied
# more than 160; X5's fen fell 600 under one). A long piece over land varying more than HULL_STEP along its span (the
# installed map's land, as common/wild.py reads it) is four short pieces, each on its own land.
HULL_STEP = 128


def studio_reads_void():
    try:
        schema = json.load(open(os.path.join(REPO, 'openyamm-studio', 'schema', 'sketch.schema.json')))
    except OSError:
        return False
    return 'void' in (schema.get('properties') or {})


def _inside(poly, x, y):
    hit = False
    for i, (x1, y1) in enumerate(poly):
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def void_polygons(sketch):
    """The rim's polygons in cells: the sketch's `void` once converted, else the rim seas."""
    polygons = [v['polygon'] for v in sketch.get('void') or []]
    polygons += [b['polygon'] for b in (sketch.get('water') or {}).get('bodies') or []
                 if b.get('id') in RIM_SEAS and (b.get('level') or 0) <= 0]
    return polygons


def in_void(polygons, x, y):
    return any(_inside(p, x, y) for p in polygons)


def nearest_edge(polygons, x, y):
    """The nearest point on the land's edge to the void (cells) and that edge's outward unit vector, or None."""
    best = None
    for a, b, normal in boundary_edges(polygons):
        ax, ay = a
        dx, dy = b[0] - ax, b[1] - ay
        length = dx * dx + dy * dy
        t = 0.0 if length == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / length))
        px, py = ax + dx * t, ay + dy * t
        distance = math.hypot(x - px, y - py)
        if best is None or distance < best[0]:
            best = (distance, (px, py), normal)
    return best


def _pours_into_void(polygons, x, y, dx, dy):
    """A fall at (x, y) pouring along (dx, dy) reaches the void within a cell and a half."""
    length = math.hypot(dx, dy) or 1.0
    return any(in_void(polygons, x + dx / length * t, y + dy / length * t) for t in (0.25, 0.5, 1.0, 1.5))


def turn_of(dx, dy):
    """The studio turn of a direction in cells (y grows south): degrees clockwise seen from above, 0 north, 90 east,
    180 south, -90 west (the schema's -180..180; the studio writes facing = -turn, the binding's 270 east)."""
    turn = round(math.degrees(math.atan2(dx, -dy)))
    return turn - 360 if turn > 180 else turn


def boundary_edges(polygons):
    """Runs of edge between land and void: (a, b, outward unit vector in cells), on no map border. Polygon edges are
    walked a cell at a time, so a stretch where two void bodies meet (X6's cove mouth) drops out and runs split there."""
    runs = []
    for poly in polygons:
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            if a == b:
                continue
            if (a[0] == b[0] and a[0] in (0, 128)) or (a[1] == b[1] and a[1] in (0, 128)):
                continue        # the map's own border
            length = math.dist(a, b)
            ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
            steps = max(1, math.ceil(length - 1e-6))
            current = None
            for k in range(steps):
                t0, t1 = length * k / steps, length * (k + 1) / steps
                mx, my = a[0] + ux * (t0 + t1) / 2, a[1] + uy * (t0 + t1) / 2
                normal = None
                for nx, ny in ((uy, -ux), (-uy, ux)):
                    if in_void(polygons, mx + nx * 0.5, my + ny * 0.5) and \
                            not in_void(polygons, mx - nx * 0.5, my - ny * 0.5):
                        normal = (nx, ny)
                p0 = (round(a[0] + ux * t0, 3), round(a[1] + uy * t0, 3))
                p1 = (round(a[0] + ux * t1, 3), round(a[1] + uy * t1, 3))
                if normal is not None and current is not None and current[2] == normal and current[1] == p0:
                    current = (current[0], p1, normal)
                    continue
                if current is not None:
                    runs.append(current)
                current = (p0, p1, normal) if normal is not None else None
            if current is not None:
                runs.append(current)
    return runs


def fall_spots(sketch):
    """((x, y) cells, clearance in cells) where a fall pours over the rim: the hull keeps that far from it. A studio
    waterfall with a spillway (`chute`): its lip, the water's half width and the plate's margin; one without, and the
    sand and lava falls (decorations): 1.6 cells round each end. The third item is True for a decoration fall."""
    spots = []
    for thing in sketch.get('structures') or []:
        if thing.get('kind') == 'waterfall' and thing.get('line'):
            if thing.get('chute'):
                spots.append((tuple(thing['line'][0]),
                              ((thing.get('width') or FALL_WIDTH) / 2.0 + DECK_MARGIN) / 512.0, False))
            else:
                spots.append((tuple(thing['line'][0]), 1.6, False))
                spots.append((tuple(thing['line'][-1]), 1.6, False))
        elif thing.get('kind') == 'decoration' and thing.get('decoration') in FALL_DECORATIONS and thing.get('at'):
            spots.append((tuple(thing['at']), 1.6, True))
    return spots


def _inner_corner(polygons, p):
    """The land wraps round this end of a run (a notch's inner corner), off the map's border."""
    if p[0] in (0, 128) or p[1] in (0, 128):
        return False
    return sum(in_void(polygons, p[0] + math.cos(q) * 0.3, p[1] + math.sin(q) * 0.3)
               for q in (math.radians(a) for a in range(0, 360, 30))) < 6


def _segment_distance(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / length))
    return math.hypot(p[0] - ax - dx * t, p[1] - ay - dy * t)


def hull_pieces(sketch, key):
    polygons = void_polygons(sketch)
    edges = boundary_edges(polygons)
    falls = fall_spots(sketch)
    burnt = key in BURNT_MAPS
    pieces = []
    count = 0
    notch_ends = set()
    terrain = None
    try:
        import wild  # noqa: E402 (beside this file)
        terrain = wild._export('xeen_%s' % key)
    except Exception:       # no installed map yet (a first build): long pieces as before
        terrain = None

    def uneven(p0, p1):
        if not terrain:
            return False
        lands = [wild._terrain_at(terrain, p0[0] + (p1[0] - p0[0]) * f - nx * 0.25, p0[1] + (p1[1] - p0[1]) * f - ny * 0.25)
                 for f in (0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1)]
        return max(lands) - min(lands) > HULL_STEP
    for a, b, (nx, ny) in edges:
        length = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        turn = turn_of(nx, ny)
        notch = length < NOTCH_RUN and (_inner_corner(polygons, a) or _inner_corner(polygons, b))
        if notch:
            notch_ends.update((a, b))
        at = 0.0
        while at < length - 0.25:
            size = PIECE_LONG if length - at >= PIECE_LONG - 0.01 else PIECE_SHORT
            if size == PIECE_SHORT and length - at < 0.75:
                break
            if size == PIECE_LONG and any(
                    _segment_distance(f, (a[0] + ux * at, a[1] + uy * at),
                                      (a[0] + ux * (at + size), a[1] + uy * (at + size))) < reach
                    for f, reach, _ in falls):
                size = PIECE_SHORT      # short pieces up to the fall's sides
            if size == PIECE_LONG and uneven((a[0] + ux * at, a[1] + uy * at),
                                             (a[0] + ux * (at + size), a[1] + uy * (at + size))):
                size = PIECE_SHORT      # F60: short pieces over uneven land, each on its own land
            mid = at + size / 2.0
            cx, cy = a[0] + ux * mid + nx * INTO, a[1] + uy * mid + ny * INTO
            s0 = (a[0] + ux * at, a[1] + uy * at)
            s1 = (a[0] + ux * (at + size), a[1] + uy * (at + size))
            at += size
            if not (0 <= cx <= 127 and 0 <= cy <= 127):
                continue        # the map's last cell (a run ending on the border): the schema refuses it (rimmap-b)
            blocking = [deco for f, reach, deco in falls if _segment_distance(f, s0, s1) < reach - 1e-6]
            if blocking and not all(blocking):
                continue        # a water fall pours through here (its spillway, or its gap)
            count += 1
            if blocking:
                kind = 'xeen_hullf' + ('bn' if burnt else '')   # D-114: a plain face behind a sand or lava fall
            elif notch:
                kind = 'xeen_hull4n' if size == PIECE_LONG else 'xeen_hull1n'
            else:
                kind = 'xeen_hull4' if size == PIECE_LONG else 'xeen_hull1'
                if burnt and count % 3 == 0:
                    kind += 'bn'
            pieces.append({'id': 'thing:hull_%03d' % count, 'kind': 'decoration', 'at': [round(cx, 3), round(cy, 3)],
                           'turn': turn, 'decoration': kind,
                           'notes': 'U-12 (rim agent, 2026-11-23): the world\'s hull under the rim (common/rim.py).'})
    # land corners the void wraps round: where two edges meet and the diagonal between their normals is void
    ends = {}
    for a, b, normal in edges:
        for p in (a, b):
            ends.setdefault(p, []).append(normal)
    for p, normals in sorted(ends.items()):
        if len(normals) != 2:
            continue
        (n1x, n1y), (n2x, n2y) = normals
        if abs(n1x * n2x + n1y * n2y) > 0.5:
            continue        # a straight join, not a corner
        dx, dy = n1x + n2x, n1y + n2y
        around = sum(in_void(polygons, p[0] + math.cos(q) * 0.3, p[1] + math.sin(q) * 0.3)
                     for q in (math.radians(a) for a in range(0, 360, 30)))
        if around < 7:
            continue        # the land wraps round here (a notch's inner corner): the runs' decks meet by themselves
        if any(math.dist(p, f) < reach for f, reach, _ in falls):
            continue
        if p in notch_ends:
            continue        # a notch wall's deckless pieces meet the run's deck end by themselves
        count += 1
        kind = 'xeen_hullc' + ('bn' if burnt and count % 3 == 0 else '')
        pieces.append({'id': 'thing:hull_%03d' % count, 'kind': 'decoration',
                       'at': [round(p[0] + dx * INTO, 3), round(p[1] + dy * INTO, 3)],
                       'turn': turn_of(dx, dy), 'decoration': kind,
                       'notes': 'U-12 (rim agent, 2026-11-23): the hull\'s corner piece (common/rim.py).'})
    return pieces


def to_void(sketch, burnt=False):
    """The rim seas become the sketch's `void` (once the studio reads it); returns notes."""
    water = sketch.get('water') or {}
    bodies = water.get('bodies') or []
    keep, voids = [], list(sketch.get('void') or [])
    for body in bodies:
        if body.get('id') in RIM_SEAS and (body.get('level') or 0) <= 0:
            voids.append({'id': body['id'].replace('water:', 'void:'), 'polygon': body['polygon'],
                          'notes': 'U-12: the void under the world rim (was %s, the sea that stood for the stars).'
                                   % body['id']})
        else:
            keep.append(body)
    if len(voids) == len(sketch.get('void') or []):
        return []
    water['bodies'] = keep
    sketch['void'] = voids
    notes = ['void: %s' % ', '.join(v['id'] for v in voids)]
    polygons = [v['polygon'] for v in voids]
    for thing in sketch.get('structures') or []:
        line = thing.get('line') or []
        edge = nearest_edge(polygons, *line[0]) if thing.get('kind') == 'waterfall' and len(line) == 2 else None
        # A rim fall: its foot at the old sea's level, or its lip on (or within a cell of) the void's edge.
        if thing.get('kind') == 'waterfall' and ((thing.get('foot') or 0) <= 0
                                                 or (edge is not None and (edge[0] <= 1.0
                                                                           or in_void(polygons, *line[0])))):
            thing['pool'] = 0
            # The sheet pours past the hull's deck into the void (rim decider Q4), not onto a floor at 0.
            thing['foot'] = VOID_FALL_FOOT
            if edge is not None and (in_void(polygons, *line[0]) or not _pours_into_void(
                    polygons, line[0][0], line[0][1], line[1][0] - line[0][0], line[1][1] - line[0][1])):
                # The lip stands in the void or the line runs along the edge (D3's Wrath Falls, written for the sea):
                # the lip on the nearest edge, pouring straight out (agent xeen-rim4).
                (px, py), (nx, ny) = edge[1], edge[2]
                line = thing['line'] = [[round(px - nx * 0.5, 2), round(py - ny * 0.5, 2)],
                                        [round(px + nx * 0.5, 2), round(py + ny * 0.5, 2)]]
            if len(line) == 2 and not in_void(polygons, *line[0]):
                # D-109: the lip on the land's edge itself (the studio's land runs level to it), so the sheet hangs
                # free in the void past the land instead of inside the land's last cell; the crags stand on the land
                # beside it (`edge`).
                (x0, y0), (x1, y1) = line
                length = math.hypot(x1 - x0, y1 - y0)
                ux, uy = (x1 - x0) / length, (y1 - y0) / length
                t = 0.0
                while t < 4.0 and not in_void(polygons, x0 + ux * (t + 0.005), y0 + uy * (t + 0.005)):
                    t += 0.005
                if t < 4.0:
                    lip = [round(x0 + ux * t, 2), round(y0 + uy * t, 2)]
                    thing['line'] = [lip, [round(lip[0] + ux, 2), round(lip[1] + uy, 2)]]
                    thing['edge'] = True
                    # D-112: down the spillway in the hull's deck (seen from the land), then free into the void.
                    thing['chute'] = list(VOID_FALL_CHUTE)
                    thing['lean'] = VOID_FALL_LEAN
                    # No crags: the hull's pieces bound the spillway, and crags hid it from the banks.
                    thing['rocks'] = False
                    textures = dict(thing.get('textures') or {})
                    textures['deck'] = 'xahullbn' if burnt else 'xahull'
                    thing['textures'] = textures
            notes.append('%s pours into the void (lip %s, foot %d, no pool)' % (thing['id'], thing['line'][0],
                                                                              VOID_FALL_FOOT))
    # Sand and lava falls (decorations, origin at the lip): on the land's edge, a hair inside it as the hull, pouring
    # out; a designed turn is kept while it still pours into the void (X7's falls toward the signature camera).
    for thing in sketch.get('structures') or []:
        if thing.get('kind') == 'decoration' and thing.get('decoration') in FALL_DECORATIONS and thing.get('at'):
            edge = nearest_edge(polygons, *thing['at'])
            if edge is None or edge[0] > 3.0:
                continue
            (px, py), (nx, ny) = edge[1], edge[2]
            at = [round(px + nx * INTO, 3), round(py + ny * INTO, 3)]
            turn = thing.get('turn')
            if turn is None or not _pours_into_void(polygons, at[0], at[1], math.sin(math.radians(turn)),
                                                    -math.cos(math.radians(turn))):
                turn = turn_of(nx, ny)
            if at != thing['at'] or turn != thing.get('turn'):
                notes.append('%s on the edge at %s turn %s (was %s turn %s)' % (thing.get('id'), at, turn,
                                                                                 thing['at'], thing.get('turn')))
                thing['at'], thing['turn'] = at, turn
    # Decorations left standing in the void from the sea (rocks in the surf): nothing but the hull, the falls and
    # sounds stand in empty space.
    kept = []
    for thing in sketch.get('structures') or []:
        at = thing.get('at')
        if thing.get('kind') == 'decoration' and at and in_void(polygons, at[0], at[1]) \
                and thing.get('decoration') not in FALL_DECORATIONS \
                and not str(thing.get('decoration', '')).lower().startswith(('snd_', 'xeen_hull')):
            notes.append('dropped %s (%s) from the void' % (thing.get('id'), thing.get('decoration')))
            continue
        kept.append(thing)
    sketch['structures'] = kept
    return notes


def apply(sketch, key):
    """Nothing changes until the studio reads `void` (a hull over the sea would show its deck at the waterline);
    XEEN_RIM_HULL=1 in the environment places the hull anyway, for test builds."""
    notes = []
    if studio_reads_void():
        notes += to_void(sketch, key in BURNT_MAPS)
    elif os.environ.get('XEEN_RIM_HULL') != '1':
        return ['rim: waiting for the studio\'s void (U-12); no change']
    structures = [t for t in sketch.get('structures') or [] if not str(t.get('id', '')).startswith('thing:hull_')]
    pieces = hull_pieces(sketch, key)
    sketch['structures'] = structures + pieces
    notes.append('hull: %d pieces' % len(pieces))
    return notes
