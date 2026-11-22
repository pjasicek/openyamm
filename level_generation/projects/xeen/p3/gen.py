#!/usr/bin/env python3
"""P3 Plane of Earth of Xeen: writes L2, L3 and L4 (A6's planes sub-agent, seventeenth session, 2026-11-21), after P1's
and P2's gen.py (copied and adapted; nothing of theirs edited).

The plan is L1's (planes_design.py with D-58 applied); this file turns it into the studio's rooms, objects and wiring:

- room:bowl, one open-air room under the `xeen_plane_earth` sky: its floor the scree at SCREE (-1,024, rubble), its
  walls the bowl's ragged rock to the sky, 2,200-3,000 over the scree (ceiling_points on every rim corner: a jagged
  skyline), leaning in like a cavern's (steep hanging lean slabs high on the walls, talus at their foot, spurs);
- the terraces as rock prisms standing in the scree (their L1 outlines), each with one walkable scree slope back up
  (D-58 P3 Q1; none to the Anvil or the Hollow), the links as stone ramps over the scree and the Giants' Arch;
- the Anvil (-384): a round floor of bedrock, a crack at its middle where the guardians rise (the hidden group 60),
  ringed by twelve monoliths; the test's plate at its east gate (before S's pedestal);
- the Root Stair down to the Sleeper's Hollow (-768): steps between tall cheeks of rock, a slab across its head (a
  mover) that sinks on qbit 111766 (P-1): P-2 by construction (the cheeks and the Hollow's lip over the scree);
- the Hollow under an overhang of the south wall with roots of stone hanging from it; the return dais (shown on
  qbit 111762); the Pillar Field's petrified trees and the Echo Stone; the Geode Hall's split boulders and the
  Heart-geode; the quarry's cut steps, half-cut blocks, the last block and the quarrymen's hut;
- nine rockfall plates (PressurePlate, xperubble) calling A3's planes.rockfall.

S's pieces (the statue, the sleeper and couch, the pedestal, the dais model, the way-up effect) are spots by name,
blocked (C7: no stand-ins); the plinth, the dais disc and the way-up ring are geometry.

    python3 level_generation/projects/xeen/p3/gen.py      # writes devdocs/xeen/briefs/p3/L2, L3, L4
"""
import math
import os
import random
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'level_generation/xeen_art/phase6'))
import planes_design as PD  # noqa: E402
import planes_geom as PG  # noqa: E402
sys.path.insert(0, str(ROOT / 'level_generation/projects/xeen/common/planes'))
import pieces as PC  # noqa: E402

BRIEF = ROOT / 'devdocs/xeen/briefs/p3'
WORLD = ROOT / 'assets_dev/worlds/xeen'
PL = PG.Plane('p3')
D = PL.d
SPACE = PL.space
PLACE = PL.place

SCREE = -1024         # the bowl's floor (D-58 P3: 1,024 under the arrival)
CEIL = 2400           # the sky over the bowl's middle (absolute)
RIM_LOW, RIM_HIGH = 2200, 3000          # the walls' tops over the scree (L1: 2,200-3,000 high)
TEST_QBIT = PD.TEST_QBITS['earth']      # 111766
SLEEPER_QBIT = PD.SLEEPER_QBITS['earth']   # 111762
GUARD_GROUP = 60
FLOOR_OF = {s['id']: s['floor'] for s in D['spaces']}
ARENA_FL = FLOOR_OF['room:arena']       # -384
HOLLOW_FL = FLOOR_OF['room:chamber']    # -768

# ------------------------------------------------------------------------------------------------ textures
SKY = {'texture': 'gcav1wal', 'size': [256, 256], 'scale': 32, 'sky': True}      # sky faces (xeen_plane_earth draws)
SCREE_FLOOR = {'texture': 'vlcflore', 'size': [128, 128], 'scale': 2}            # MM6 broken grey rubble
SCREE_SLOPE = {'texture': 'vlcflora', 'size': [128, 128], 'scale': 2}            # MM6 brown rock floor: slopes
WALL_RED = {'texture': 'cwb1', 'size': [128, 256], 'scale': 4}                   # MM7 Nighon red-brown rock
WALL_BROWN = {'texture': 'gcav1wal', 'size': [256, 256], 'scale': 2}             # MM8 brown rough rock
WALL_GREY = {'texture': 'gwspotwl', 'size': [256, 256], 'scale': 2}              # MM8 blue-grey rough rock
STRATA = {'texture': 'vlcflorb', 'size': [128, 128], 'scale': 4}                 # MM6 layered brown rock
ROCK_FLOOR = {'texture': 'gcav1flr', 'size': [256, 256], 'scale': 1}             # MM8 grey-brown rock floor
EARTH = {'texture': 'dirttyl', 'size': [128, 128], 'scale': 2}                   # MM8 packed earth: the Dust Ledge
PALE = {'texture': 'gwsphlfl', 'size': [128, 128], 'scale': 2}                   # MM8 pale carved stone
HOLLOW_FLOOR = {'texture': 'cfb1', 'size': [128, 128], 'scale': 2}               # MM7 Nighon tunnel floor
BEDROCK = {'texture': 'gn_mtl03', 'size': [128, 128], 'scale': 2}                # MM8 dark grey stone: the Anvil
MONOLITH = {'texture': 'gwspotwl', 'size': [256, 256], 'scale': 2}              # MM8 blue-grey rough rock: monoliths
DAIS = {'texture': 'gn_mtl01', 'size': [128, 128], 'scale': 2}                   # MM8 grey stone: the dais, the plate
CRACK = {'texture': 'gcav2wal', 'size': [128, 256], 'scale': 1}                  # MM8 black strata: the crack
TRUNK = {'texture': 'gcav1wal', 'size': [256, 256], 'scale': 2}                  # the petrified trees' bark
ASHLAR = {'texture': 't19a02', 'size': [128, 128], 'scale': 2}                   # MM8 grey ashlar: the plinth
SAPPHIRE = {'texture': 'xdvsaph', 'size': [128, 256], 'fit': True}               # DD-10's sapphire vein (A6)
GEODE = {'texture': 'xpegeode', 'size': [128, 128], 'scale': 2}                  # new (xtex.py, map_textures/p3)
RUBBLE = {'texture': 'xperubble', 'size': [128, 128], 'fit': True}  # s33: the picture's own size (128)               # new, once per rockfall face

TOP_OF = {'room:landing': EARTH, 'room:statue': PALE, 'room:quarry': PALE, 'room:geodes': ROCK_FLOOR,
          'room:pillars': ROCK_FLOOR, 'room:west_ledge': ROCK_FLOOR, 'room:arena': BEDROCK,
          'room:chamber': HOLLOW_FLOOR}
SIDE_OF = {'room:landing': WALL_BROWN, 'room:statue': STRATA, 'room:quarry': STRATA, 'room:geodes': WALL_BROWN,
           'room:pillars': WALL_RED, 'room:west_ledge': WALL_RED, 'room:arena': WALL_GREY, 'room:chamber': WALL_RED}


def live_d7():
    if os.environ.get('P3_D7_LIVE') == '1':
        return True
    studio = WORLD / 'maps/xeen_d7.studio.yml'
    return (WORLD / 'maps/xeen_d7.blv').exists() and studio.exists() and 'entrance:p3_return' in studio.read_text()


D7_LIVE = live_d7()


def key(sid):
    return sid.split(':', 1)[1]


def ipt(p):
    return [int(round(p[0])), int(round(p[1]))]


def area2(poly):
    return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def ccw(poly):
    return poly if area2(poly) > 0 else poly[::-1]


def ring(cx, cy, r, sides=16, phase=0.0, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(phase + 2 * math.pi * k / sides), cy + ry * math.sin(phase + 2 * math.pi * k / sides))
            for k in range(sides)]


def block(pid, at, size, z, rise, surface, top=None, facing=None, top_size=None, notes=None, **kw):
    """A rectangular block whose foot stands at absolute z (its base over the scree)."""
    e = {'id': pid, 'at': ipt(at), 'size': [int(round(size[0])), int(round(size[1]))],
         'base': int(round(z - SCREE)), 'rise': int(round(rise)), 'surface': surface}
    if e['base'] == 0:
        e.pop('base')
    if top:
        e['top_surface'] = top
    if facing is not None:
        e['facing'] = round(facing, 4)
    if top_size:
        e['top_size'] = [int(round(top_size[0])), int(round(top_size[1]))]
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def prism(pid, outline, z, rise, surface, top=None, notes=None, **kw):
    e = {'id': pid, 'outline': [ipt(p) for p in ccw(list(outline))], 'base': int(round(z - SCREE)),
         'rise': int(round(rise)), 'surface': surface, 'top_surface': top or surface}
    if e['base'] == 0:
        e.pop('base')
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def slab(pid, a, b, z0, z1, width, surface, top, bottom_z, notes=None, thickness=None, **kw):
    """A wedge from a (top z0) to b (top z1), `width` wide, its underside flat at bottom_z (P5's platform_slab); with
    `thickness` a hanging slab of that thickness under its sloping top."""
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    facing = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    if thickness:
        low = min(z0, z1) - thickness
        e = {'id': pid, 'at': ipt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)), 'size': [int(round(length)), int(width)],
             'facing': round(facing, 2), 'base': int(round(low - SCREE)), 'rise': int(thickness),
             'surface': surface, 'top_surface': top, 'bottom_surface': kw.pop('bottom', surface)}
        if int(round(z0)) != int(round(z1)):
            e['top_heights'] = [int(round(z0 - low)), int(round(z1 - low)), int(round(z1 - low)), int(round(z0 - low))]
            e['thickness'] = int(thickness)
    else:
        low = bottom_z
        e = {'id': pid, 'at': ipt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)), 'size': [int(round(length)), int(width)],
             'facing': round(facing, 2), 'base': int(round(low - SCREE)), 'rise': int(round(min(z0, z1) - low)),
             'surface': surface, 'top_surface': top, 'bottom_surface': surface}
        if int(round(z0)) != int(round(z1)):
            e['top_heights'] = [int(round(z0 - low)), int(round(z1 - low)), int(round(z1 - low)), int(round(z0 - low))]
            e['thickness'] = int(round(min(z0, z1) - low))
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


# ------------------------------------------------------------------------------------------------ geometry helpers
def foot(e):
    if 'outline' in e:
        return [tuple(p) for p in e['outline']]
    cx, cy = e['at']
    L, W = e['size']
    f = math.radians(e.get('facing', 0))
    ux, uy, vx, vy = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    return [(cx + sx * L / 2 * ux + sy * W / 2 * vx, cy + sx * L / 2 * uy + sy * W / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def seg_dist(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / l2))
    return math.hypot(q[0] - a[0] - t * dx, q[1] - a[1] - t * dy)


def poly_dist(q, poly):
    if PG.point_in(q, poly):
        return 0.0
    return min(seg_dist(q, poly[i - 1], poly[i]) for i in range(len(poly)))


def poly_dist_outline(q, poly):
    return min(seg_dist(q, poly[i - 1], poly[i]) for i in range(len(poly)))


def inside_by(q, poly, margin):
    return PG.point_in(q, poly) and poly_dist_outline(q, poly) >= margin


class Clear:
    """Distances from points and segments to a set of footprints (bounding boxes cull the far ones)."""

    def __init__(self, polys):
        self.items = []
        for p in polys:
            xs, ys = [v[0] for v in p], [v[1] for v in p]
            self.items.append((min(xs), min(ys), max(xs), max(ys), p))

    def dist(self, q, cap=4000.0):
        best = cap
        for x0, y0, x1, y1, p in self.items:
            if math.hypot(max(x0 - q[0], 0, q[0] - x1), max(y0 - q[1], 0, q[1] - y1)) >= best:
                continue
            best = min(best, poly_dist(q, p))
        return best

    def seg(self, a, b, step=64):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        return min(self.dist((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)) for k in range(n + 1))


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


PYTH = [(1, 0, 1), (24, 7, 25), (12, 5, 13), (15, 8, 17), (4, 3, 5), (21, 20, 29)]


def snap_facing(deg):
    """The nearest direction whose sine and cosine are whole ratios (P1's): a tapered block turned to it keeps
    whole-unit corners when its sizes are multiples of the returned quantum."""
    best = None
    for a, b, h in PYTH:
        for x, y in ((a, b), (b, a)):
            for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                d = math.degrees(math.atan2(sy * y, sx * x))
                diff = abs((d - deg + 180) % 360 - 180)
                if best is None or diff < best[0]:
                    best = (diff, d, 2 * h)
    return round(best[1], 4), best[2]


def mult(x, q):
    return max(q, int(round(x / q)) * q)


def tri_rise(p, q, r):
    ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    return float('inf') if nz == 0 else math.hypot(nx, ny) / abs(nz)


def seg_cross(p, q, poly):
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    for i in range(len(poly)):
        c, d = poly[i - 1], poly[i]
        if (cr(c, d, p) * cr(c, d, q) < 0) and (cr(p, q, c) * cr(p, q, d) < 0):
            return True
    return False


# ------------------------------------------------------------------------------------------------ terraces
TERRACES = ['room:landing', 'room:statue', 'room:quarry', 'room:geodes', 'room:pillars', 'room:west_ledge']
ARENA_AT = SPACE['room:arena']['at']
ARENA_R = (1600, 1472)


def arena_r(th):
    return 1.0 / math.sqrt((math.cos(th) / ARENA_R[0]) ** 2 + (math.sin(th) / ARENA_R[1]) ** 2)


def arena_outline():
    out = []
    for k in range(24):
        th = 2 * math.pi * k / 24 + 0.07
        r = arena_r(th) * (1.0 + 0.025 * math.sin(5 * th + 1.0))
        out.append((ARENA_AT[0] + r * math.cos(th), ARENA_AT[1] + r * math.sin(th)))
    return out


def outline_of(sid):
    if sid == 'room:arena':
        return [tuple(ipt(p)) for p in arena_outline()]
    return [tuple(ipt(p)) for p in PG.blob(SPACE[sid], points=20)]


OUTLINE = {s['id']: outline_of(s['id']) for s in D['spaces']}


def terraces():
    out = []
    for s in D['spaces']:
        sid = s['id']
        if sid == 'room:chamber':
            continue
        out.append(prism(f"platform:{key(sid)}", OUTLINE[sid], SCREE, s['floor'] - SCREE, SIDE_OF[sid], TOP_OF[sid],
                         notes=f"{s['name']}: {s['shape']} (floor {s['floor']}, {s['floor'] - SCREE} over the scree)."))
    return out


# ------------------------------------------------------------------------------------------------ links
INTO = 192


def link_cut(l):
    p, q = PL.link_ends(l)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * INTO, p[1] - uy * INTO), (q[0] + ux * INTO, q[1] + uy * INTO), d


def ramps():
    """The links as natural bridges of rock over the scree (the scree passes under them: one scree, no pockets cut
    off from its slopes): each a run of slabs abutting exactly, thick at its feet, thin in its middle."""
    out = []
    for l in D['links']:
        if l.get('gate') or l['style'] == 'arch':
            continue
        out += span(l, f"platform:{key(l['id'])}_", WALL_BROWN, 180,
                    f"{l['id']}: a bridge of rock over the scree, the scree passing under it")
    return out


def span(l, prefix, side, crown, note):
    a, b, d = link_cut(l)
    za, zb = FLOOR_OF[l['a']] + 4, FLOOR_OF[l['b']] + 4
    segs = 7 if d > 1400 else 5
    out = []
    for k in range(segs):
        t0, t1 = k / segs, (k + 1) / segs
        p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        z0, z1 = za + (zb - za) * t0, za + (zb - za) * t1
        tm = (t0 + t1) / 2
        th = crown + int(round(640 * (1 - math.sin(math.pi * tm)) ** 1.6))
        th = int(min(th, min(z0, z1) - (SCREE + 24)))
        out.append(slab(f'{prefix}{k + 1}', p, q, z0, z1, l['width'], side, ROCK_FLOOR, None, thickness=th,
                        notes=f"{note}: thick at its feet, thin at its crown." if k == 0 else None))
    return out


def arch():
    """The Giants' Arch (link:arch_e): a natural arch of stone over the scree, grey, thin at its crown."""
    l = next(l for l in D['links'] if l['style'] == 'arch')
    return span(l, 'platform:arch', WALL_GREY, 192, "The Giants' Arch (link:arch_e): a natural arch of stone over the scree")


# ------------------------------------------------------------------------------------------------ scree slopes
SCREE_SLOPE_RISE = 0.62          # walkable (the party walks up at most 0.9 for each unit of run)
SCREE_W = 448


def squircle(th, r=6400.0, n=3.6):
    c, s = abs(math.cos(th)), abs(math.sin(th))
    return (c ** n / r ** n + s ** n / r ** n) ** (-1 / n)


def scree_slopes(avoid):
    """One walkable scree slope from the scree up to each terrace (D-58 P3 Q1), on its outer side away from the
    links and the other terraces; none to the Anvil or the Hollow."""
    out = []
    jobs = [(sid, f"platform:{key(sid)}_scree", (0, 360)) for sid in TERRACES]
    jobs += [('room:pillars', 'platform:pillars_south_scree', (215, 330)),      # the south scree's own ways up
             ('room:geodes', 'platform:geodes_south_scree', (200, 330))]
    for sid, pid, (d0, d1) in jobs:
        s = SPACE[sid]
        c = s['at']
        top = s['floor'] + 4
        run = (top - (SCREE + 6)) / SCREE_SLOPE_RISE
        best = None
        for deg in range(d0, d1, 5):
            th = math.radians(deg)
            rim = PG.ray_exit(list(OUTLINE[sid]), c, (c[0] + 20000 * math.cos(th), c[1] + 20000 * math.sin(th)))
            r = math.hypot(rim[0] - c[0], rim[1] - c[1])
            p = (c[0] + (r - 160) * math.cos(th), c[1] + (r - 160) * math.sin(th))
            q = (c[0] + (r + run) * math.cos(th), c[1] + (r + run) * math.sin(th))
            e = slab('x', p, q, top, SCREE + 6, SCREE_W, WALL_BROWN, SCREE_SLOPE, SCREE + 2)
            f = foot(e)
            if not all(math.hypot(*v) < squircle(math.atan2(v[1], v[0])) - 520 for v in f):
                continue
            # clearance from every other footprint along the slope's outer part
            outer = [(c[0] + (r + run * t) * math.cos(th), c[1] + (r + run * t) * math.sin(th)) for t in (0.3, 0.6, 1.0)]
            clear = min(avoid.dist(v) for v in outer) - SCREE_W / 2
            if best is None or clear > best[0]:
                best = (clear, deg, p, q)
        clear, deg, p, q = best
        avoid = Clear([t[4] for t in avoid.items] + [foot(slab('x', p, q, top, SCREE + 6, SCREE_W, WALL_BROWN,
                                                              SCREE_SLOPE, SCREE + 2))])
        out.append(slab(pid, p, q, top, SCREE + 6, SCREE_W, WALL_BROWN, SCREE_SLOPE,
                        SCREE + 2, notes=(f"A scree slope from the scree up to {s['name']} (D-58 P3 Q1: walkable, "
                                          f"{SCREE_SLOPE_RISE} for each unit; clear by {int(clear)}).")))
    return out


# ------------------------------------------------------------------------------------------------ the Anvil
MONO_DEG = [100, 130, 160, 190, 220, 250, 280, 0, 30, 70]      # ten; the two at the Root Stair's head are its flanks
RING_IN = 150                    # the ring stands this far inside the Anvil's edge


def anvil():
    out = []
    rnd = random.Random(2727)
    e_gate = math.degrees(math.atan2(ARENA_AT[1] - ARENA_AT[1], -2304 - ARENA_AT[0]))      # the east gate (0)
    for k, deg in enumerate(MONO_DEG):
        th = math.radians(deg)
        if abs(angdiff(th, math.radians(e_gate))) < math.radians(14) or abs(angdiff(th, STAIR_TH)) < math.radians(16):
            continue
        r = arena_r(th) - RING_IN
        at = (ARENA_AT[0] + r * math.cos(th), ARENA_AT[1] + r * math.sin(th))
        fac, q = snap_facing(deg + 90)
        w, dd = mult(rnd.uniform(280, 360), q), mult(rnd.uniform(200, 260), q)
        h = rnd.uniform(520, 760)
        out.append(block(f'platform:monolith{k + 1}', at, (w, dd), ARENA_FL - 16, h + 16, MONOLITH, MONOLITH,
                         facing=fac, top_size=[mult(w * 0.72, q), mult(dd * 0.78, q)],
                         notes="The Anvil's monoliths (twelve with the Root Stair's two)." if k == 0 else None))
    # the crack at the middle: a jagged split of black strata where the guardians rise
    pts = [(-760, -40), (-420, 60), (-160, -50), (120, 70), (430, -30), (760, 50)]
    for k in range(len(pts) - 1):
        a = (ARENA_AT[0] + pts[k][0], ARENA_AT[1] + pts[k][1])
        b = (ARENA_AT[0] + pts[k + 1][0], ARENA_AT[1] + pts[k + 1][1])
        w = 96 if k in (2, 3) else 64
        out.append(slab(f'platform:crack{k + 1}', a, b, ARENA_FL + 2 + k % 2, ARENA_FL + 2 + k % 2, w, CRACK, CRACK,
                        ARENA_FL - 6 - k % 2,
                        notes="The Anvil's crack (landmark:anvil): a split in the bedrock." if k == 0 else None))
    tp = PLACE['poi:test']['at']
    out.append(block('platform:test_plate', (tp[0] - 64, tp[1]), (256, 256), ARENA_FL, 4, DAIS, DAIS,
                     notes="The test's floor before S's pedestal (poi:test): stepping on asks 'Accept the test of Earth?'."))
    return out


# ------------------------------------------------------------------------------------------------ the Root Stair
STAIR_P, STAIR_Q = PL.link_ends(next(l for l in D['links'] if l.get('gate')))
STAIR_TH = math.atan2(STAIR_Q[1] - STAIR_P[1], STAIR_Q[0] - STAIR_P[0])
STAIR_FAC, STAIR_QUANT = snap_facing(math.degrees(STAIR_TH))
STAIR_U = (math.cos(math.radians(STAIR_FAC)), math.sin(math.radians(STAIR_FAC)))
STAIR_N = (-STAIR_U[1], STAIR_U[0])
STAIR_W = 640                       # between the cheeks
CHEEK_W = 128
STEPS = 12                          # 32 each, -384 -> -768
STEP_RUN = 112
HEAD = (ARENA_AT[0] + (arena_r(math.radians(STAIR_FAC)) - 96) * STAIR_U[0],
        ARENA_AT[1] + (arena_r(math.radians(STAIR_FAC)) - 96) * STAIR_U[1])      # the slab's line, on the Anvil
CHEEK_TOP = ARENA_FL + 256          # the cheeks' tops, level: 256 over the Anvil, 288+ over every step (P-2)
SLAB_H = 384                        # the slab across the head: 384 over the Anvil (P-2)


def along(t, off=0.0):
    return (HEAD[0] + STAIR_U[0] * t + STAIR_N[0] * off, HEAD[1] + STAIR_U[1] * t + STAIR_N[1] * off)


FIRST_STEP_T = 96                    # the first step begins this far past the slab's line
STAIR_END_T = FIRST_STEP_T + STEPS * STEP_RUN       # the Hollow's floor from here on


def stair():
    """The Root Stair: twelve rough steps of 32 down from the Anvil to the Hollow between tall cheeks of rock (their
    tops level at -128); the last step runs into the Hollow's floor."""
    out = []
    for k in range(STEPS):
        top = ARENA_FL - 32 * (k + 1) + (4 if k == STEPS - 1 else 0)
        t0, t1 = FIRST_STEP_T + STEP_RUN * k, FIRST_STEP_T + STEP_RUN * (k + 1)
        if k == STEPS - 1:
            t1 += 160
        out.append(block(f'platform:stair{k + 1}', along((t0 + t1) / 2), (t1 - t0, STAIR_W), SCREE, top - SCREE,
                         WALL_RED, HOLLOW_FLOOR, facing=STAIR_FAC,
                         notes="The Root Stair: rough steps of 32 down to the Sleeper's Hollow." if k == 0 else None))
    # the landing between the slab and the first step, level with the Anvil
    out.append(block('platform:stair_head', along(FIRST_STEP_T / 2 - 40), (FIRST_STEP_T + 80, STAIR_W), SCREE,
                     ARENA_FL + 2 - SCREE, WALL_RED, BEDROCK, facing=STAIR_FAC,
                     notes="The stair's head on the Anvil's rim, where the slab stands."))
    t_end = STAIR_END_T + 80
    for k, sgn in enumerate((-1, 1)):
        off = sgn * (STAIR_W / 2 + CHEEK_W / 2)
        a, b = along(-200, off), along(t_end, off)
        out.append(block(f'platform:stair_cheek{k + 1}', along((-200 + t_end) / 2, off), (t_end + 200, CHEEK_W),
                         SCREE, CHEEK_TOP - SCREE, WALL_RED, ROCK_FLOOR, facing=STAIR_FAC,
                         notes=(f"The Root Stair's cheeks (P-2): their tops level at {CHEEK_TOP}, 256 over the Anvil "
                                "and 288 or more over every step.") if k == 0 else None))
    return out


def stair_flanks():
    """Two monoliths of the Anvil's ring stand on the cheeks' heads either side of the slab (L1's gate flank)."""
    out = []
    for k, sgn in enumerate((-1, 1)):
        off = sgn * (STAIR_W / 2 + CHEEK_W / 2 + 40)
        at = along(-110, off)
        out.append(block(f'platform:stair_flank{k + 1}', at, (STAIR_QUANT * mult(220, STAIR_QUANT) // STAIR_QUANT,
                                                               mult(200, STAIR_QUANT)),
                         ARENA_FL - 24, 728, MONOLITH, MONOLITH, facing=STAIR_FAC,
                         top_size=[mult(160, STAIR_QUANT), mult(150, STAIR_QUANT)],
                         notes="The Root Stair's flanking monoliths (two of the Anvil's twelve)." if k == 0 else None))
    return out


# ------------------------------------------------------------------------------------------------ the Hollow
HOLLOW_AT = SPACE['room:chamber']['at']


def hollow():
    out = [prism('platform:chamber', OUTLINE['room:chamber'], SCREE, HOLLOW_FL - SCREE, WALL_RED, HOLLOW_FLOOR,
                 notes=("The Sleeper's Hollow: a hollow at the bowl's bottom, 256 over the scree on every side (P-2), "
                        "under the south wall's overhang."))]
    dp = PLACE['exit:dais']['at']
    out.append(prism('platform:dais', ring(dp[0], dp[1], 224, 12), HOLLOW_FL, 8, DAIS, DAIS,
                     notes="The return dais (exit:dais): a disc of grey granite, shown once the Earth Sleeper is awake "
                           "(qbit 111762)."))
    return out


# ------------------------------------------------------------------------------------------------ the statue, landing
def statue():
    pa = PLACE['poi:statue']['at']
    fl = FLOOR_OF['room:statue']
    return [block('platform:plinth', pa, (512, 512), fl, 112, ASHLAR, ASHLAR,
                  notes="The plinth of the statue of Earth (S's statue stands on it); its plaque (m38.plaque_earth).")]


WAY_UP = None


def way_up():
    wx, wy = WAY_UP
    out = [prism('platform:way_up', ring(wx, wy, 176, 12), 0, 4, MONOLITH, PALE,
                 notes="The dust shaft's foot (exit:way_up): a disc of pale stone in a ring of standing stones (S's "
                       "dust column over it is blocked).")]
    for k in range(8):
        th = 2 * math.pi * (k + 0.5) / 8
        at = (wx + 300 * math.cos(th), wy + 300 * math.sin(th))
        fac, q = snap_facing(math.degrees(th))
        out.append(block(f'platform:way_up_stone{k + 1}', at, (mult(96, q), mult(80, q)), -24, 220 + 48 * (k % 3),
                         MONOLITH, MONOLITH, facing=fac, top_size=[mult(56, q), mult(48, q)]))
    return out


# ------------------------------------------------------------------------------------------------ the Pillar Field
TREES = [((-128, -2048), 150, 1500), ((1600, -1024), 190, 1700), ((1792, -1920), 150, 1250), ((384, -640), 170, 1350),
         ((-256, -1856), 130, 1050), ((1408, -2304), 170, 1450), ((704, -896), 140, 1150), ((1856, -1472), 120, 950),
         ((-512, -2176), 160, 1200), ((128, -2304), 120, 900)]


def pillars():
    """The Pillar Field: rough pillars like petrified trees, each a tapering trunk on a flaring root foot, some
    broken off short; the Echo Stone (a hollow pillar with a sapphire vein) among them."""
    out = []
    rnd = random.Random(5353)
    fl = FLOOR_OF['room:pillars']
    poly = OUTLINE['room:pillars']
    keep = [PLACE['poi:echo']['at'], (896, -2048), (-384, -1152)]
    k = 0
    for at, r, h in TREES:
        if not inside_by(at, poly, r + 160) or any(math.hypot(at[0] - p[0], at[1] - p[1]) < 420 for p in keep):
            continue
        if WALK_CLEAR(at) < r + 220:
            continue
        k += 1
        fac, q = snap_facing(rnd.uniform(0, 90))
        w = mult(2 * r, q)
        out.append(block(f'platform:tree{k}_root', at, (mult(w * 1.7, q), mult(w * 1.55, q)), fl - 8, 168, TRUNK,
                         ROCK_FLOOR, facing=fac, top_size=[w, mult(w * 0.92, q)],
                         notes="The Pillar Field's petrified trees: a flaring root foot ..." if k == 1 else None))
        out.append(block(f'platform:tree{k}', at, (w, mult(w * 0.92, q)), fl + 160, h, TRUNK, TRUNK, facing=fac,
                         top_size=[mult(w * 0.62, q), mult(w * 0.55, q)],
                         notes="... and a trunk tapering to a broken top." if k == 1 else None))
        if rnd.random() < 0.5:        # a stub of a branch
            fac2, q2 = snap_facing(fac + 90)
            out.append(block(f'platform:tree{k}_knot', at, (mult(w * 1.25, q2), mult(w * 0.5, q2)), fl + 160 + h * 0.55,
                             mult(140, 4), TRUNK, TRUNK, facing=fac2, top_size=[mult(w * 0.9, q2), mult(w * 0.4, q2)]))
    ex, ey = PLACE['poi:echo']['at']
    fac, q = snap_facing(0)
    out.append(block('platform:echo_root', (ex, ey), (448, 416), fl - 8, 168, TRUNK, ROCK_FLOOR, facing=0,
                     top_size=[288, 272]))
    out.append(block('platform:echo', (ex, ey), (288, 272), fl + 160, 1100, TRUNK, TRUNK, facing=0,
                     top_size=[192, 176],
                     notes="The Echo Stone (poi:echo): a hollow pillar; clicked, A3's planes.echo."))
    out.append(block('platform:echo_vein', (ex - 144 - 4, ey), (8, 240), fl + 200, 480, SAPPHIRE, TRUNK,
                     end_surface=dict(TRUNK, fit=False), facing=0,
                     notes="The Echo Stone's sapphire vein on its west face."))
    return out


# ------------------------------------------------------------------------------------------------ the Geode Hall
BOULDERS = [((3712, 896), 340, 30), ((5056, -384), 300, 110), ((3584, -1024), 280, 160), ((5120, 1024), 260, 70),
            ((4096, 1280), 220, 120)]


def geodes():
    """Split boulders lined with amethyst: each two halves apart, their split faces the geode (xpegeode); the
    Heart-geode the largest, its halves wide apart."""
    out = []
    fl = FLOOR_OF['room:geodes']
    poly = OUTLINE['room:geodes']
    items = BOULDERS + [(tuple(PLACE['poi:geode']['at']), 400, 0)]
    k = 0
    for at, r, deg in items:
        heart = r == 400
        if not heart and (not inside_by(at, poly, r + 200) or WALK_CLEAR(at) < r + 260
                          or math.hypot(at[0] - 4608, at[1] - 256) < 900):
            continue
        k += 1
        fac, q = snap_facing(deg)
        u = (math.cos(math.radians(fac)), math.sin(math.radians(fac)))
        gap = 160 if heart else 72
        depth = mult(r * 0.9, q)
        for j, sgn in enumerate((-1, 1)):
            c = (at[0] + u[0] * sgn * (gap / 2 + depth / 2), at[1] + u[1] * sgn * (gap / 2 + depth / 2))
            h = r * (1.5 if heart else 1.25) * (1.0 if j else 0.9)
            pid = 'platform:heart_geode' if heart and j == 0 else (
                'platform:heart_geode2' if heart else f'platform:boulder{k}_{j + 1}')
            # the split face (the side toward the gap) is an end: the geode lining; the rest rough rock
            out.append(block(pid, c, (depth, mult(r * 1.8, q)), fl - 16, h, WALL_BROWN, WALL_BROWN, facing=fac,
                             top_size=[mult(depth * 0.55, q), mult(r * 1.2, q)], end_surface=GEODE,
                             notes=("The Heart-geode (poi:geode): a split boulder lined with amethyst; touched, A3's "
                                    "planes.geode.") if heart and j == 0 else (
                                 "Split boulders lined with amethyst (xpegeode on the split faces)." if k == 1 and j == 0
                                 else None)))
    return out


# ------------------------------------------------------------------------------------------------ the quarry
def quarry():
    """The Giants' Quarry: two cut steps along its north-east, half-cut blocks still standing, the last block with
    its slate, and the quarrymen's hut's ruin by their strongbox."""
    out = []
    fl = FLOOR_OF['room:quarry']
    poly = OUTLINE['room:quarry']
    # cut steps: low blocks of pale stone, stepped up toward the bowl's wall (sides cut square: a quarry)
    for k, (at, size, h) in enumerate((((4608, 4864), (1024, 448), 96), ((4800, 5056), (640, 256), 192),
                                       ((5056, 3840), (384, 1024), 96))):
        if all(inside_by(v, poly, 48) for v in foot({'at': at, 'size': size})):
            out.append(block(f'platform:quarry_step{k + 1}', at, size, fl, h, PALE, PALE,
                             notes="The quarry's cut steps." if k == 0 else None))
    for k, (at, size, h) in enumerate((((3328, 4352), (320, 256), 288), ((4096, 2944), (384, 224), 224),
                                       ((3456, 3712), (256, 256), 352))):
        if (inside_by(at, poly, 260) and WALK_CLEAR(at) > 300
                and all(math.hypot(at[0] - c[0], at[1] - c[1]) > 420 for c in D['hazard']['cells'])):
            out.append(block(f'platform:cut_block{k + 1}', at, size, fl, h, PALE, PALE,
                             notes="Half-cut blocks still standing." if k == 0 else None))
    lb = PLACE['poi:last_block']['at']
    out.append(block('platform:last_block', lb, (448, 320), fl, 256, PALE, PALE,
                     notes="The last block (poi:last_block): half-cut, a slate on it; clicked, A3's planes.last_block."))
    out.append(block('platform:last_block_cut', (lb[0], lb[1] + 160 + 24), (448, 48), fl, 64, PALE, PALE))
    # the hut's ruin: three low broken walls round the cache's corner
    cx, cy = PLACE['poi:quarry_cache']['at']
    for k, (dx, dy, sx, sy, h) in enumerate(((-320, 160, 64, 512, 160), (0, 384, 576, 64, 224), (288, 304, 64, 224, 96))):
        at = (cx + dx, cy + dy)
        if inside_by(at, poly, 64):
            out.append(block(f'platform:hut{k + 1}', at, (sx, sy), fl, h, ASHLAR, ASHLAR,
                             notes="The quarrymen's hut, fallen to its footings." if k == 0 else None))
    return out


# ------------------------------------------------------------------------------------------------ rockfall
def rockfall():
    out = []
    for i, c in enumerate(D['hazard']['cells']):
        z = FLOOR_OF[PL.space_of(c)]
        out.append(block(f'platform:rockfall{i + 1}', c, (192, 192), z, 4, ROCK_FLOOR, RUBBLE,
                         notes="A rockfall (D-58 P3 Q2): a PressurePlate face, xperubble, planes.rockfall." if i == 0
                         else None))
    return out


# ------------------------------------------------------------------------------------------------ walking lines
def walk_lines():
    """Centre lines the party walks (links, the stair, scree slopes) and the walk: (a, b, half width)."""
    out = []
    for l in D['links']:
        a, b, _ = link_cut(l)
        out.append((a, b, l['width'] / 2))
    w = D['walk']
    for a, b in zip(w, w[1:]):
        out.append((a, b, 256))
    return out


WALK = walk_lines()


def WALK_CLEAR(q):
    return min(seg_dist(q, a, b) - hw for a, b, hw in WALK)


# ------------------------------------------------------------------------------------------------ the rim
MAX_POINTS = 64
MAX_TEETH = 8
GRID = 16


def skyline(t):
    """The walls' tops over the scree along the rim: a slow swell of massifs (RIM_LOW-RIM_HIGH)."""
    return 2600 + 260 * math.sin(2 * t + 0.7) + 160 * math.sin(5 * t + 2.0)


RIM_TABLE = None


def rim_radius(t):
    """The bowl's rim: a squircle pushed out where a terrace comes near (each footprint 260 clear), inside the map."""
    k = int(round(math.degrees(t))) % 360
    return RIM_TABLE[k]


def build_rim_table():
    base = [squircle(math.radians(d)) for d in range(360)]
    need = [0.0] * 360
    for f in RIM_FEET:
        for v in f:
            r = math.hypot(*v)
            d = math.degrees(math.atan2(v[1], v[0]))
            for dd in range(-4, 5):
                k = int(round(d + dd)) % 360
                need[k] = max(need[k], r + 300)
    out = []
    for k in range(360):
        th = math.radians(k)
        cap = 6624 / max(abs(math.cos(th)), abs(math.sin(th)))
        out.append(min(cap, max(base[k], need[k])))
    for _ in range(3):           # a little smoothing (no notches)
        out = [max(out[k], (out[k - 1] + out[k] + out[(k + 1) % 360]) / 3) for k in range(360)]
    return out


def rim_entries(clear, rim_n):
    rnd = random.Random(3131)
    feats = []
    teeth = 0
    for k in range(20):
        t0 = 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / 20
        R = rim_radius(t0)
        if teeth >= MAX_TEETH or any(abs(angdiff(t0, f[0])) < math.radians(20) for f in feats):
            continue
        w = rnd.uniform(380, 620)
        base = rnd.uniform(90, 200)
        depth = rnd.uniform(560, 960)
        skew = rnd.uniform(-90, 90)
        while depth >= 400:
            pts = [(t0 - w / R, base), (t0 + skew / R, base + depth), (t0 + w / R, base + rnd.uniform(-40, 60))]
            xy = [((rim_radius(t) - i) * math.cos(t), (rim_radius(t) - i) * math.sin(t)) for t, i in pts]
            if all(clear.seg(xy[j], xy[j + 1]) >= 360 for j in range(2)):
                break
            depth -= 64
        else:
            continue
        hf = max(2300, skyline(t0) + rnd.uniform(-100, 300))
        e = [{'t': pts[0][0], 'inset': pts[0][1], 'kind': 'tooth_flank', 'h': hf + rnd.uniform(-80, 160)},
             {'t': pts[1][0], 'inset': pts[1][1], 'kind': 'tooth_nose', 'h': hf - rnd.uniform(400, 700)},
             {'t': pts[2][0], 'inset': pts[2][1], 'kind': 'tooth_flank', 'h': hf + rnd.uniform(-80, 160)}]
        feats.append((t0, w / R, e))
        teeth += 1
    step = 2 * math.pi / rim_n
    entries = []
    for i in range(rim_n):
        t = step * (i + rnd.uniform(-0.25, 0.25))
        if any(abs(angdiff(t, t0)) < span + 0.6 * step for t0, span, _ in feats):
            continue
        inset = 150 + 110 * math.sin(3 * t + 1.1) + 60 * math.sin(7 * t + 2.3) + rnd.uniform(-70, 70)
        h = skyline(t) + (1 if i % 2 else -1) * rnd.uniform(90, 330)
        entries.append({'t': t, 'inset': max(24.0, min(420.0, inset)), 'kind': 'rim', 'h': h})
    for _, _, e in feats:
        entries += e
    entries.sort(key=lambda e: e['t'] % (2 * math.pi))

    def xy(e):
        r = rim_radius(e['t']) - e['inset']
        return (r * math.cos(e['t']), r * math.sin(e['t']))
    for e in entries:
        while e['kind'] == 'rim' and e['inset'] > 16 and clear.dist(xy(e)) < 240:
            e['inset'] -= 24
    n = len(entries)
    for _ in range(30):
        moved = False
        for i in range(n):
            a, b = entries[i], entries[(i + 1) % n]
            if clear.seg(xy(a), xy(b)) < 200:
                for e in (a, b):
                    if e['kind'] == 'rim' and e['inset'] > 16:
                        e['inset'] = max(16, e['inset'] - 24)
                        moved = True
        if not moved:
            break
    for e in entries:
        e['xy'] = xy(e)
    return entries


def bowl_rim():
    for rim_n in range(60, 8, -1):
        out = rim_entries(CLEAR, rim_n)
        if len(out) <= MAX_POINTS:
            break
    m = len(out)
    for _ in range(40):
        for i in range(m):
            a, b = out[i], out[(i + 1) % m]
            lim = 1.8 * math.hypot(a['xy'][0] - b['xy'][0], a['xy'][1] - b['xy'][1])
            if abs(a['h'] - b['h']) > lim:
                hi, lo = (a, b) if a['h'] > b['h'] else (b, a)
                hi['h'] = lo['h'] + lim
    for e in out:
        e['h'] = int(round(max(RIM_LOW, min(RIM_HIGH, e['h']))))
        e['xy'] = [int(round(e['xy'][0] / GRID)) * GRID, int(round(e['xy'][1] / GRID)) * GRID]
    return out


def greedy_triangles(pts, n_rim, poly):
    """The ceiling's triangles as the studio makes them (P1's emulator: the shortest lines first, inside the room)."""
    import numpy as np
    P = np.array([[p[0], p[1]] for p in pts], dtype=float)
    m = len(pts)
    edges = [(i, (i + 1) % n_rim) for i in range(n_rim)]
    cand = []
    for i in range(m):
        for j in range(i + 1, m):
            if (j == i + 1 and j < n_rim) or (i == 0 and j == n_rim - 1):
                continue
            d = float(np.hypot(*(P[j] - P[i])))
            if d < 6000:
                cand.append((d, i, j))
    cand.sort()

    def crosses(i, j, E):
        if not E:
            return False
        A, B = P[i], P[j]
        C, Dd = P[[e[0] for e in E]], P[[e[1] for e in E]]
        cr = lambda o, a, b: (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])
        d1, d2 = cr(C, Dd, A[None]), cr(C, Dd, B[None])
        d3, d4 = cr(A[None], B[None], C), cr(A[None], B[None], Dd)
        share = np.array([i in e or j in e for e in E])
        hit = (d1 * d2 < 0) & (d3 * d4 < 0) & ~share
        return bool(hit.any())

    for d, i, j in cand:
        mid = ((P[i][0] + P[j][0]) / 2, (P[i][1] + P[j][1]) / 2)
        if not PG.point_in(mid, poly) or crosses(i, j, edges):
            continue
        edges.append((i, j))
    nb = {i: set() for i in range(m)}
    for i, j in edges:
        nb[i].add(j)
        nb[j].add(i)
    tris = set()
    for i, j in edges:
        for k in nb[i] & nb[j]:
            t = tuple(sorted((i, j, k)))
            c = ((P[i][0] + P[j][0] + P[k][0]) / 3, (P[i][1] + P[j][1] + P[k][1]) / 3)
            if PG.point_in(c, poly):
                tris.add(t)
    return tris


def ceiling_points():
    """The sky over the bowl (P1's): every rim corner at its wall's top, up to three more points on each wall between
    (a jagged skyline), a near ring higher than the rim, and a ring at CEIL over the middle."""
    rnd = random.Random(78)
    poly = [tuple(p) for p in BOWL]
    n = len(BOWL)
    inner = []
    for k in range(12):
        t = 2 * math.pi * (k + 0.5) / 12
        r = 0.68 * rim_radius(t)
        q = (r * math.cos(t), r * math.sin(t))
        if PG.point_in(q, poly) and poly_dist_outline(q, poly) > 700:
            inner.append([int(q[0]), int(q[1]), CEIL])
    inner.append([0, 0, CEIL])
    budget = int((192 - len(inner)) / 1.5) - n
    lens = [math.hypot(BOWL[(k + 1) % n][0] - BOWL[k][0], BOWL[(k + 1) % n][1] - BOWL[k][1]) for k in range(n)]
    want = {k: 0 for k in range(n)}
    for _ in range(3):
        for k in sorted(range(n), key=lambda k: -lens[k]):
            if budget and lens[k] >= 360 * (want[k] + 1):
                want[k] += 1
                budget -= 1
    pts = []
    for k in range(n):
        a, b = BOWL[k], BOWL[(k + 1) % n]
        ha, hb = BOWL_H[k], BOWL_H[(k + 1) % n]
        pts.append([a[0], a[1], SCREE + ha])
        m = want[k]
        if not m:
            continue
        dx, dy = b[0] - a[0], b[1] - a[1]
        g = math.gcd(abs(dx), abs(dy))
        steps = sorted({max(1, min(g - 1, round(g * j / (m + 1)))) for j in range(1, m + 1)})
        line = [(0.0, ha)]
        for j, s in enumerate(steps):
            f = s / g
            h = ha + (hb - ha) * f + (1 if (j + k) % 2 else -1) * rnd.uniform(160, 420)
            line.append((f, h))
        line.append((1.0, hb))
        for _ in range(6):
            for i in range(1, len(line) - 1):
                f, h = line[i]
                for g2 in (line[i - 1], line[i + 1]):
                    lim = 1.8 * abs(f - g2[0]) * lens[k]
                    h = max(g2[1] - lim, min(g2[1] + lim, h))
                line[i] = (f, max(RIM_LOW, min(RIM_HIGH, h)))
        for (f, h), s in zip(line[1:-1], steps):
            pts.append([a[0] + dx * s // g, a[1] + dy * s // g, SCREE + int(round(h))])
    m = len(pts)
    near = []
    for i in range(0, m, 2):
        p, a, b = pts[i], pts[i - 1], pts[(i + 1) % m]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty)
        nin = (-ty / tl, tx / tl)
        for d in (420, 360, 300):
            q = (p[0] + nin[0] * d, p[1] + nin[1] * d)
            if (PG.point_in(q, poly) and poly_dist_outline(q, poly) >= 280
                    and all(math.hypot(q[0] - r[0], q[1] - r[1]) > 240 for r in near)):
                near.append([int(q[0]), int(q[1]), min(CEIL, max(a[2], p[2], b[2]) + 240)])
                break
    pts += near
    pts += inner
    for _ in range(60):
        bad = [t for t in greedy_triangles(pts, m, poly) if tri_rise(*(pts[i] for i in t)) > 3.8]
        if not bad:
            break
        drop = set()
        for t in bad:
            free = [i for i in t if i >= m and pts[i][2] != CEIL] or [i for i in t if i >= m]
            if free:
                drop.add(max(free))
            else:
                onwall = [i for i in t if list(pts[i][:2]) not in BOWL]
                if onwall:
                    drop.add(onwall[0])
        if not drop:
            break
        m -= sum(1 for i in drop if i < m)
        pts = [p for i, p in enumerate(pts) if i not in drop]
    assert len(pts) <= 192, len(pts)
    return pts, m


def wall_surfaces():
    """Three shipped rocks by stretch of the rim (the theme's red-brown rock elsewhere), layered strata on the spurs."""
    out = []
    n = len(BOWL)
    for k in range(n):
        a, b = BOWL_KIND[k], BOWL_KIND[(k + 1) % n]
        if 'tooth_nose' in (a, b) or a == b == 'tooth_flank':
            out.append({'wall': k, 'surface': STRATA})
            continue
        mx, my = (BOWL[k][0] + BOWL[(k + 1) % n][0]) / 2, (BOWL[k][1] + BOWL[(k + 1) % n][1]) / 2
        sec = int((math.atan2(my, mx) + math.pi) / (2 * math.pi / 9)) % 3
        if sec:
            out.append({'wall': k, 'surface': (WALL_BROWN, WALL_GREY)[sec - 1]})
    return out


def local_top(p, reach=1100):
    return min([q[2] for q in SKYPTS[:SKY_RIM] if math.hypot(q[0] - p[0], q[1] - p[1]) < reach] or [SCREE + RIM_LOW])


def talus():
    """Scree at the walls' foot (P1's): a steep wedge along each rim wall, 240-640 up, so no wall rises from the scree
    as a flat slab."""
    rnd = random.Random(616)
    out = []
    n = len(BOWL)
    poly = [tuple(p) for p in BOWL]
    for k in range(n):
        a, b = BOWL[k], BOWL[(k + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 240:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nin = (-u[1], u[0])
        a1 = (a[0] + u[0] * 24 + nin[0] * 6, a[1] + u[1] * 24 + nin[1] * 6)
        b1 = (b[0] - u[0] * 24 + nin[0] * 6, b[1] - u[1] * 24 + nin[1] * 6)
        ha = rnd.uniform(300, 680)
        hb = ha * rnd.uniform(0.75, 1.3)
        ra, rb = ha / rnd.uniform(1.15, 1.5), hb / rnd.uniform(1.15, 1.5)
        for _ in range(5):
            sq = min(1.0, (L - 112) / max(1.0, 0.5 * (ra + rb)))
            a2 = (a1[0] + nin[0] * ra + u[0] * ra * 0.5 * sq, a1[1] + nin[1] * ra + u[1] * ra * 0.5 * sq)
            b2 = (b1[0] + nin[0] * rb - u[0] * rb * 0.5 * sq, b1[1] + nin[1] * rb - u[1] * rb * 0.5 * sq)
            quad = [a1, b1, b2, a2]
            hs = [int(ha), int(hb), rnd.randint(6, 18), rnd.randint(6, 18)]
            if area2(quad) < 0:
                quad, hs = quad[::-1], hs[::-1]
            fan = [(quad[0] + (hs[0],), quad[i] + (hs[i],), quad[i + 1] + (hs[i + 1],)) for i in (1, 2)]
            ok = (L > 160 and all(PG.point_in(v, poly) for v in quad)
                  and max(tri_rise(*t) for t in fan) <= 1.85
                  and not any(seg_cross(quad[i - 1], quad[i], poly) for i in range(4))
                  and min(CLEAR.dist(v) for v in (a2, b2, ((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2))) >= 160)
            if ok:
                break
            ha, hb, ra, rb = ha * 0.75, hb * 0.75, ra * 0.8, rb * 0.8
        else:
            continue
        out.append({'id': f'platform:talus{len(out) + 1}', 'outline': [ipt(v) for v in quad],
                    'rise': min(hs), 'top_heights': hs, 'surface': STRATA, 'top_surface': dict(SCREE_SLOPE, uneven=True)})
    out[0]['notes'] = "Scree at the walls' foot (talus wedges, steep: the party slides back)."
    return out


def leans():
    """The walls lean in like a cavern's (D-58 P3): along the longer rim walls a hanging slab of rock high on the wall,
    its underside rising from the wall to a ragged lip that juts 360-560 over the bowl (1.6-1.9 for each unit: a wall
    leaning in), its top falling back to the wall; the lip stays 280 under the skyline there."""
    rnd = random.Random(4545)
    out = []
    n = len(BOWL)
    poly = [tuple(p) for p in BOWL]
    for k in range(n):
        if BOWL_KIND[k] != 'rim' or BOWL_KIND[(k + 1) % n] != 'rim':
            continue
        a, b = BOWL[k], BOWL[(k + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 520:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nin = (-u[1], u[0])
        dd = rnd.uniform(360, 560)
        slope = rnd.uniform(1.6, 1.9)
        R = dd * slope
        t = rnd.uniform(160, 240)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        top = min(local_top(a, 500), local_top(b, 500)) - SCREE
        zw = top - 280 - R - t
        if zw < 700:
            continue
        a1 = (a[0] + u[0] * 40 + nin[0] * 4, a[1] + u[1] * 40 + nin[1] * 4)
        b1 = (b[0] - u[0] * 40 + nin[0] * 4, b[1] - u[1] * 40 + nin[1] * 4)
        Lw = math.hypot(b1[0] - a1[0], b1[1] - a1[1])
        # the lip: a bulging arc (convex), deepest near the middle, shallow at the ends, each point its own depth
        fr = [0.0, 0.16 + rnd.uniform(-0.04, 0.04), 0.38 + rnd.uniform(-0.06, 0.06), 0.62 + rnd.uniform(-0.06, 0.06),
              0.84 + rnd.uniform(-0.04, 0.04), 1.0]
        dep = [dd * (0.18 + 0.82 * math.sin(math.pi * f) ** 0.7) for f in fr]
        lip = [(a1[0] + u[0] * Lw * f + nin[0] * d, a1[1] + u[1] * Lw * f + nin[1] * d) for f, d in zip(fr, dep)]
        poly_pts = [a1, b1] + lip[::-1]
        hs = [t, t] + [d * slope + t for d in dep[::-1]]
        if not all(PG.point_in(v, poly) for v in poly_pts) or any(seg_cross(poly_pts[i - 1], poly_pts[i], poly)
                                                                    for i in range(len(poly_pts))):
            continue
        if min(CLEAR.dist(v) for v in lip) < 260:
            continue
        if area2(poly_pts) < 0:
            poly_pts, hs = poly_pts[::-1], hs[::-1]
        out.append({'id': f'platform:lean{len(out) + 1}', 'outline': [ipt(v) for v in poly_pts],
                    'base': int(round(zw)), 'rise': int(round(t)), 'top_heights': [int(round(h)) for h in hs],
                    'thickness': int(round(t)), 'surface': STRATA, 'top_surface': dict(WALL_BROWN, uneven=True),
                    'bottom_surface': dict(WALL_BROWN, uneven=True)})
    if out:
        out[0]['notes'] = ("The walls lean in (D-58 P3): a hanging slab high on the wall, its underside rising to a lip "
                           "over the bowl.")
    return out


def terrace_talus():
    """Rough rock at the terraces' foot: steep wedges (1.15-1.6: the party slides back) against each side, 240-620 up
    the cliff, so no terrace stands in the scree as an extruded plate; none under a link, a slope or the stair, none
    round the Hollow (P-2)."""
    rnd = random.Random(7171)
    lanes = Clear([foot(e) for e in FIXED if e['id'].startswith(('platform:arch', 'platform:stair'))
                   or e['id'].endswith('_scree') or any(e['id'].startswith(f"platform:{key(l['id'])}_") for l in D['links'])])
    others = {sid: Clear([OUTLINE[x] for x in OUTLINE if x != sid]) for sid in OUTLINE}
    out = []
    for sid in TERRACES + ['room:arena']:
        poly = ccw([tuple(v) for v in OUTLINE[sid]])
        rise = FLOOR_OF[sid] - SCREE
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            if d < 120:
                continue
            n = ((q[1] - p[1]) / d, -(q[0] - p[0]) / d)
            hp = min(rise - 120, rnd.uniform(240, 620))
            hq = min(rise - 120, hp * rnd.uniform(0.7, 1.3))
            rp, rq = hp / rnd.uniform(1.15, 1.6), hq / rnd.uniform(1.15, 1.6)
            ip, iq = (p[0] - n[0] * 8, p[1] - n[1] * 8), (q[0] - n[0] * 8, q[1] - n[1] * 8)
            op, oq = (p[0] + n[0] * rp, p[1] + n[1] * rp), (q[0] + n[0] * rq, q[1] + n[1] * rq)
            mid = ((op[0] + oq[0]) / 2, (op[1] + oq[1]) / 2)
            if min(lanes.dist(v) for v in (p, q, op, oq, mid)) < 96 or min(others[sid].dist(v) for v in (op, oq, mid)) < 96:
                continue
            if not all(math.hypot(*v) < rim_radius(math.atan2(v[1], v[0])) - 300 for v in (op, oq)):
                continue
            quad, hs = [ip, iq, oq, op], [int(hp), int(hq), rnd.randint(6, 18), rnd.randint(6, 18)]
            fan = [(quad[0] + (hs[0],), quad[k] + (hs[k],), quad[k + 1] + (hs[k + 1],)) for k in (1, 2)]
            if max(tri_rise(*t) for t in fan) > 1.85:
                continue
            if area2(quad) < 0:
                quad, hs = quad[::-1], hs[::-1]
            out.append({'id': f'platform:{key(sid)}_talus{i + 1}', 'outline': [ipt(v) for v in quad], 'rise': min(hs),
                        'top_heights': hs, 'surface': STRATA, 'top_surface': dict(SCREE_SLOPE, uneven=True)})
    out[0]['notes'] = "Rough rock at the terraces' foot (steep: the party slides back into the scree)."
    return out


# ------------------------------------------------------------------------------------------------ the overhang
def overhang():
    """The south wall's overhang over the Hollow (L1: 'under an overhang of the wall, roots of stone hanging from
    it'): a thick hanging slab from the wall over the Hollow's south half, and roots of stone hanging from it (blocks
    flaring upward to the slab), all well over the Hollow's floor."""
    out = []
    hx, hy = HOLLOW_AT
    poly = [tuple(p) for p in BOWL]
    # the wall south of the Hollow: from the rim at the Hollow's x straight north
    y_wall = None
    for y in range(int(hy) - 400, -6700, -16):
        if not PG.point_in((hx, y), poly):
            y_wall = y + 16
            break
    if y_wall is None:
        return out
    z0 = HOLLOW_FL + 880              # the underside's foot at the wall
    north = hy - 140                  # the lip over the Hollow's middle-south
    depth = north - (y_wall + 24)
    top = local_top((hx, y_wall), 1600) - 260
    w = 2400
    quad = [(hx - w / 2, y_wall + 24), (hx + w / 2, y_wall + 24), (hx + w / 2, north), (hx - w / 2, north)]
    if not all(PG.point_in(v, poly) for v in quad):
        # trim to the room: shrink the width until the slab lies inside the bowl
        for w in range(2400, 800, -64):
            quad = [(hx - w / 2, y_wall + 24), (hx + w / 2, y_wall + 24), (hx + w / 2, north), (hx - w / 2, north)]
            if all(PG.point_in(v, poly) for v in quad) and not any(seg_cross(quad[i - 1], quad[i], poly)
                                                                   for i in range(4)):
                break
    th = 320
    rise_under = min(1.2 * depth, top - z0 - th)
    hs = [th, th, int(rise_under + th), int(rise_under + th)]
    out.append({'id': 'platform:overhang', 'outline': [ipt(v) for v in quad], 'base': int(round(z0 - SCREE)),
                'rise': th, 'top_heights': hs, 'thickness': th, 'surface': STRATA,
                'top_surface': dict(WALL_BROWN, uneven=True), 'bottom_surface': dict(WALL_RED, uneven=True),
                'notes': ("The overhang of the south wall over the Sleeper's Hollow: its underside rises from "
                          f"{z0 - HOLLOW_FL} over the Hollow's floor at the wall to {int(z0 + rise_under - HOLLOW_FL)} "
                          "at its lip.")})
    rnd = random.Random(808)
    for k in range(9):
        fx = rnd.uniform(-0.42, 0.42) * (quad[1][0] - quad[0][0])
        fy = rnd.uniform(0.15, 0.85)
        at = (hx + fx, y_wall + 24 + depth * fy)
        if any(math.hypot(at[0] - p[0], at[1] - p[1]) < 300 for p in (PLACE['poi:sleeper']['at'],
                                                                     PLACE['exit:dais']['at'],
                                                                     PLACE['poi:test_chest']['at'])):
            pass
        under = z0 + rise_under * fy                    # the slab's underside over this point
        L = rnd.uniform(260, 560)
        fac, q = snap_facing(rnd.uniform(0, 90))
        w0 = mult(rnd.uniform(64, 112), q)
        out.append(block(f'platform:root{k + 1}', at, (w0, mult(w0 * 0.9, q)), under - L, L + 24, WALL_RED, WALL_RED,
                         facing=fac, top_size=[mult(w0 * 2.4, q), mult(w0 * 2.1, q)],
                         notes="Roots of stone hanging from the overhang." if k == 0 else None))
    return out


# ------------------------------------------------------------------------------------------------ rooms.yml
def build_rooms():
    platforms = FIXED + talus() + terrace_talus() + leans() + overhang()
    for p in platforms:
        if p.get('notes') is None:
            p.pop('notes', None)
    bowl = {
        'id': 'room:bowl', 'space': 'zone:scree', 'name': 'The Plane of Earth', 'outline': BOWL, 'floor': SCREE,
        'steep_floor': True, 'ceiling': CEIL, 'ceiling_points': SKYPTS, 'theme': 'theme:bowl',
        'walls': wall_surfaces(), 'platforms': platforms,
        'notes': ("The bowl: one open-air room under the xeen_plane_earth sky, its floor the scree at -1,024, its walls "
                  f"raw rock {RIM_LOW:,}-{RIM_HIGH:,} over the scree with a jagged skyline (ceiling_points), spurs, "
                  "talus at their foot and hanging slabs leaning in high on them; the terraces stand in the scree, "
                  "linked by ridges of rock and the Giants' Arch, each with a scree slope back up; the Root Stair "
                  "down to the Sleeper's Hollow between its cheeks under the south wall's overhang."),
    }
    return {'format': 0,
            'themes': [{'id': 'theme:bowl', 'wall': WALL_RED, 'floor': SCREE_FLOOR, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:bowl', 'ambient': 30}, 'rooms': [bowl]}


# ------------------------------------------------------------------------------------------------ objects.yml
def spread(at, n, r=224):
    if n == 1:
        return [at]
    return [(at[0] + r * math.cos(2 * math.pi * k / n), at[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def obstacles():
    out = []
    for p in ROOMS['rooms'][0]['platforms']:
        pid = p['id'].split(':', 1)[1]
        if any(pid.startswith(w) for w in ('monolith', 'tree', 'echo', 'boulder', 'heart_geode', 'cut_block',
                                           'last_block', 'hut', 'plinth', 'way_up', 'quarry_step', 'stair_flank')):
            out.append([tuple(v) for v in foot(p)])
    return out


AVOID_PTS = ([PLACE[i]['at'] for i in ('poi:quarry_cache', 'poi:test_chest', 'poi:last_block', 'poi:geode', 'poi:echo',
                                      'poi:statue', 'poi:test')] + list(D['hazard']['cells']))


def clear_spot(q, obs, pad=128):
    return all(not PG.point_in(q, o) and poly_dist_outline(q, o) > pad for o in obs)


def objects():
    arr = PLACE['entrance:d7_fall']
    start = {'room': 'room:bowl', 'at': ipt(arr['at']), 'floor_height': 0, 'facing': arr['face'],
             'notes': "entrance:d7_fall on the Dust Ledge, facing south-east (Xeen.PlaneArrivals.earth)."}
    obs = obstacles()
    monsters = []
    for gi, g in enumerate(D['groups']):
        row = PD.ROWS[g['row']]
        z = FLOOR_OF[g['space']]
        poly = OUTLINE[g['space']]
        c = SPACE[g['space']]['at']
        for k, p in enumerate(spread(g['at'], g['count'])):
            q = None
            for r in range(0, 1600, 48):
                for j in range(max(1, int(2 * math.pi * r / 96))):
                    th = 2 * math.pi * j / max(1, int(2 * math.pi * r / 96)) + 0.3 * k
                    cand = (p[0] + r * math.cos(th), p[1] + r * math.sin(th))
                    if (inside_by(cand, poly, 160) and clear_spot(cand, obs)
                            and all(math.hypot(cand[0] - x[0], cand[1] - x[1]) > 300 for x in AVOID_PTS)
                            and all(math.hypot(cand[0] - m['at'][0], cand[1] - m['at'][1]) > 220 for m in monsters)):
                        q = cand
                        break
                if q:
                    break
            assert q, (g['id'], k)
            e = {'id': f"monster:{key(g['id'])}_{k + 1}", 'room': 'room:bowl', 'monster': row['id'], 'at': ipt(q),
                 'floor_height': int(z), 'facing': 0, 'hostile': True, 'group': gi + 1}
            if k == 0:
                e['notes'] = f"{g['id']}: {g['count']} {row['short']} ({row['level']})."
            monsters.append(e)
    k = 0
    for g in D['test_group']:
        row = PD.ROWS[g['row']]
        for j in range(g['count']):
            k += 1
            at = ARENA_AT if k == 1 else (ARENA_AT[0] + (k - 2.5) * 2 * 300, ARENA_AT[1] + 260)
            monsters.append({'id': f'monster:guardian_{k}', 'room': 'room:bowl', 'monster': row['id'], 'at': ipt(at),
                             'floor_height': ARENA_FL + 2 if k == 1 else ARENA_FL, 'facing': 0, 'hostile': True, 'group': GUARD_GROUP,
                             'hidden': True,
                             'notes': (f"{row['short']} ({row['level']}): the test's hidden group {GUARD_GROUP} at the "
                                       "Anvil's crack, shown by evt:test (D-58 C3).")})
    chests = [
        {'id': 'chest:test', 'room': 'room:bowl', 'at': ipt(PLACE['poi:test_chest']['at']), 'floor_height': HOLLOW_FL,
         'kind': 'ch3', 'facing': 'n', 'treasure_level': 6, 'random_items': 3, 'gold': 2500,
         'notes': "The test's chest (aaze0027:4 'Chest'): the source's gold and three items, in the Hollow past the slab."},
        {'id': 'chest:quarry_cache', 'room': 'room:bowl', 'at': ipt(PLACE['poi:quarry_cache']['at']),
         'floor_height': FLOOR_OF['room:quarry'], 'kind': 'ch1', 'facing': 'sw', 'treasure_level': 6,
         'random_items': 2, 'gold': 1200, 'trap_level': 8,
         'notes': "The quarrymen's strongbox by their hut's ruin (trapped: a falling block)."},
    ]
    lx, ly = PLACE['poi:last_block']['at']
    items = [{'id': f'item:last_block_potion{i + 1}', 'room': 'room:bowl', 'item': 259, 'at': [lx + dx, ly + dy],
              'floor_height': FLOOR_OF['room:quarry']} for i, (dx, dy) in enumerate(((320, -96), (384, 0)))]
    items[0]['notes'] = "The last block's find: Earth Resistance (259)."
    sx = along(-24)
    movers = [{'id': 'mover:slab', 'room': 'room:bowl', 'outline': [ipt(v) for v in ccw([
        along(-48, -STAIR_W / 2 - 8), along(0, -STAIR_W / 2 - 8), along(0, STAIR_W / 2 + 8), along(-48, STAIR_W / 2 + 8)])],
        'floor_height': ARENA_FL + 2, 'height': SLAB_H, 'travel': [0, 0, -(SLAB_H + 4)], 'speed': 128,
        'surface': BEDROCK, 'top_surface': BEDROCK,
        'notes': ("The Root Stair's slab (gate:sleeper): a block of stone across the stair's head, 384 high; it sinks "
                  "into the rock on qbit 111766 (evt:gate_open, evt:passed_load).")}]
    return {
        'format': 1, 'start': start,
        # AU's plane bed (devdocs/xeen/AUDIO.md session 5, "The lines to paste"; D-48 `pan: false`)
        'sounds': [{'id': 'sound:plane_bed', 'room': 'room:bowl', 'at': [-128, 0], 'height': 512, 'sound': 'xeen_amb_plane_earth', 'radius': 12000, 'inner_radius': 8000, 'volume': 0.9, 'pan': False}],
        'arrivals': [{'entrance': 'entrance:d7_fall', 'room': 'room:bowl', 'at': ipt(arr['at']), 'floor_height': 0,
                      'facing': arr['face'], 'notes': "The drop from D7's south-east corner (Xeen.toPlane('earth'))."}],
        'movers': movers, 'chests': chests, 'items': items, 'monsters': monsters, 'decorations': pieces(),
        'notes': ("P3 L4 objects (generated by output/studio_cal/p3/tools/gen.py): 27 placed hostiles in 10 groups "
                  f"and the test's three in the hidden group {GUARD_GROUP}; two chests at treasure 6; the last block's "
                  "find; the slab; S's pieces (session 20): sleeper and couch, statue, pedestal, return dais (hidden "
                  "until he wakes), dust shaft. No lights."),
    }


def pieces():
    """S's pieces (D-58 C7, session 20; level_generation/decorations/xeen_planes_claude/README.md): the couch and the
    dais on the Hollow's floor under the overhang (its rock is a floor over them), the dust shaft on its disc."""
    tp = PLACE['poi:test']['at']
    return PC.decorations(
        'earth', 'room:bowl',
        sleeper=(PLACE['poi:sleeper']['at'], 90, HOLLOW_FL), statue=(PLACE['poi:statue']['at'], 135, None),
        pedestal=((tp[0] - 64, tp[1] + 208), 270, None), dais=(PLACE['exit:dais']['at'], 0, HOLLOW_FL + 8),
        way_up=(WAY_UP, 0, 4))


# ------------------------------------------------------------------------------------------------ wiring.yml
def wiring():
    ev = []
    ev.append({'id': 'evt:test', 'preset': 'script', 'trigger': 'step', 'source': 'platform:test_plate',
               'condition': {'all': [{'not': {'qbit': 'm38_earth_test'}}, {'not': {'map_var': 'test_accepted'}}]},
               'question': {'ask': 'Accept the test of Earth?', 'answers': ['Yes', 'Y']},
               'effects': [{'lua': 'XeenQuests.hook("m38.test_earth")'}, {'show_actors': GUARD_GROUP},
                           {'set': {'var': {'map_var': 'test_accepted'}, 'value': 1}}],
               'notes': ("D-58 C3: the test (aaze0027:5). Yes: A3's m38.test_earth line, the guardians rise from the "
                         f"crack (group {GUARD_GROUP} shown); any other answer does nothing. Not asked again while "
                         "they live.")})
    ev.append({'id': 'evt:test_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'map_var': 'test_accepted'}, {'not': {'qbit': 'm38_earth_test'}}]},
               'lua': f'Xeen.planeTestCheck("earth", {GUARD_GROUP})',
               'notes': ("A3's killed-group check (xeen_common.lua): once the three guardians are dead it runs "
                         "m38.test_earth_passed, which sets qbit 111766 (P-1) with its line.")})
    ev.append({'id': 'evt:gate_open', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'qbit': 'm38_earth_test'}, {'not': {'map_var': 'gate_open'}}]},
               'opens': ['mover:slab'],
               'effects': [{'text': 'The slab across the stair sinks into the rock.'},
                           {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': 'The slab sinks the second the qbit is set (C4).'})
    ev.append({'id': 'evt:gate_keep', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'qbit': 'm38_earth_test'}, 'opens': ['mover:slab'],
               'effects': [{'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': 'Once the test is passed the slab stays sunk (every second; a sunk slab does not move).'})
    ev.append({'id': 'evt:passed_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm38_earth_test'},
               'opens': ['mover:slab'],
               'effects': [{'hide_actors': GUARD_GROUP}, {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': ("P-1: the load event reads qbit 111766: the slab sunk, the guardians hidden, the crack quiet "
                         "(through refills and the reset after a map rebuild).")})
    ev.append({'id': 'evt:gate', 'preset': 'script', 'source': 'mover:slab', 'title': "The Root Stair's slab",
               'condition': {'not': {'qbit': 'm38_earth_test'}}, 'locked_text': 'The slab has sunk into the rock.',
               'effects': [{'text': 'The slab of stone does not move.'}],
               'notes': 'Clicked: the slab never moves by hand (it sinks on the test).'})
    ev.append({'id': 'evt:dais_hide', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': 'm38_earth'}},
               'effects': [{'hide': 'platform:dais'}, {'passable': 'platform:dais'}],
               'notes': "C5: the return dais shows once the Earth Sleeper is awake (qbit 111762, m38.sleeper_earth)."})
    ev += PC.dais_events('earth', 'm38_earth')
    ev.append(PC.sleeper_event('earth'))
    ev.append({'id': 'evt:rockfall', 'preset': 'script', 'trigger': 'step', 'source': 'platform:rockfall1',
               'sources': [f'platform:rockfall{i}' for i in range(2, 10)],
               'lua': 'XeenQuests.hook("planes.rockfall")',
               'notes': ("D-58 P3 Q2: A3's planes.rockfall (one time in three, 50 physical to each member, 'Rocks fall "
                         "from above!', a short camera shake).")})
    ev.append({'id': 'evt:geode', 'preset': 'script', 'source': 'platform:heart_geode', 'title': 'The Heart-geode',
               'lua': 'XeenQuests.hook("planes.geode")',
               'notes': "A3's planes.geode (once a day, +20 Earth resistance until rest, every member)."})
    ev.append({'id': 'evt:geode2', 'preset': 'script', 'source': 'platform:heart_geode2', 'title': 'The Heart-geode',
               'lua': 'XeenQuests.hook("planes.geode")', 'notes': 'The same, its other half.'})
    ev.append({'id': 'evt:echo', 'preset': 'script', 'source': 'platform:echo', 'title': 'The Echo Stone',
               'lua': 'XeenQuests.hook("planes.echo")',
               'notes': "A3's planes.echo: the first time a sapphire in its hollow (map variable p3_echo)."})
    ev.append({'id': 'evt:last_block', 'preset': 'script', 'source': 'platform:last_block', 'title': 'The last block',
               'lua': 'XeenQuests.hook("planes.last_block")',
               'notes': "A3's planes.last_block: the slate ('Nearly done. Back after lunch.')."})
    ev.append({'id': 'evt:plaque', 'preset': 'script', 'source': 'platform:plinth', 'title': 'Plaque',
               'lua': 'XeenQuests.hook("m38.plaque_earth")',
               'notes': "A3's m38.plaque_earth: 'Step three' at the base of the statue (the statue on it is S's)."})
    ev.append(PC.copy_for(ev[-1], 'statue', 'evt:plaque_statue'))
    ev.append({'id': 'evt:chest_test', 'preset': 'chest', 'source': 'chest:test', 'title': 'Chest',
               'notes': "The test's chest (aaze0027:4)."})
    ev.append({'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:quarry_cache', 'title': 'Chest',
               'notes': "The quarrymen's strongbox (trapped)."})
    if D7_LIVE:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The dust shaft',
                   'effects': [{'lua': PC.d7_return_lua('earth')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': ("D-58 C5: the way up, always open, to D7's entrance:p3_return; A3's m38.way_up_earth is "
                             "its question.")})
        ev.append({'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': 'The return dais',
                   'condition': {'qbit': 'm38_earth'}, 'locked_text': 'The dais is dark and still.',
                   'effects': [{'lua': PC.d7_return_lua('earth')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': "D-58 C5: the dais after the sleeper, to D7's entrance:p3_return (A3's m38.dais_earth)."})
        ev.append(PC.copy_for(ev[-1], 'dais', 'evt:dais_disc'))
        ev.append(PC.copy_for(next(e for e in ev if e['id'] == 'evt:way_up'), 'way_up', 'evt:way_up_column'))
    else:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The dust shaft',
                   'effects': [{'text': 'The dust streams up into the brown sky. (The Skyroads are not open yet.)'}],
                   'notes': "Sealed until xeen_d7.blv is installed and lists entrance:p3_return."})
    return {'format': 0, 'variables': ['test_accepted', 'gate_open', 'dais_shown'], 'events': ev}


# ------------------------------------------------------------------------------------------------ plan, project
def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan(level):
    p = load('L1', 'plan.yml')
    p['level'] = level
    for l in p['links']:
        if l['id'] == 'link:root_stair':
            l['notes'] = ("the Root Stair: twelve rough steps of 32 down the bowl's bottom between tall cheeks of rock; "
                          "a slab of stone across its head (a mover) sinks on qbit 111766")
    p['notes'] = (p['notes'] + " L2-L4 (A6's planes sub-agent, seventeenth session, 2026-11-21): built by "
                  "output/studio_cal/p3/tools/gen.py; one open-air room (the bowl, its floor the scree), the terraces "
                  "rock prisms in it each with a scree slope back up, the Root Stair walled by its cheeks and barred by "
                  "a sinking slab (P-2 by construction); S's pieces blocked by name.")
    return p


def project(level):
    p = load('L1', 'project.yml')
    for n in p['neighbours']:
        if n['id'] in ('exit:d7_way_up', 'exit:d7_dais') and not D7_LIVE:
            n.pop('arrival', None)
            n.pop('arrival_hint', None)
            n['notes'] = n['notes'] + " Sealed until xeen_d7.blv is installed and names entrance:p3_return."
    p['new'] = False
    p['notes'] = (f"Xeen design brief, level {level}: P3 Plane of Earth of Xeen, an open-air BLV (devdocs/"
                  "INDOOR_OPEN_SKY.md; X9's and P5's route) built with the studio (profile region): one room, a bowl "
                  "of rock open to the xeen_plane_earth sky, its terraces stepping down to the Anvil and the Sleeper's "
                  "Hollow. map_stats 9117 (A2's row), music 3, treasure 6; Earth rows 11626, 11720-11722; hooks: A3's "
                  "m38.*_earth, planes.rockfall, planes.geode, planes.echo, planes.last_block, Xeen.planeTestCheck.")
    return p


def atmosphere():
    a = load('L1', 'atmosphere.yml')
    a['notes'] = a['notes'] + " L4: as L1 (D-58 P3 Q1)."
    return a


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    with open(BRIEF / level / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


# ------------------------------------------------------------------------------------------------ built
def nudge_in(p, sid, margin):
    c = SPACE[sid]['at']
    poly = OUTLINE[sid]
    for t in [i / 40 for i in range(41)]:
        q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
        if inside_by(q, poly, margin):
            return ipt(q)
    return ipt(c)


WAY_UP = nudge_in(PLACE['exit:way_up']['at'], 'room:landing', 420)
CORE = (terraces() + ramps() + arch() + anvil() + stair() + stair_flanks() + hollow() + statue() + way_up()
        + pillars() + geodes() + quarry() + rockfall())
SLOPES = scree_slopes(Clear([foot(e) for e in CORE if not e['id'].startswith(('platform:rockfall', 'platform:test'))]))
FIXED = CORE + SLOPES
RIM_FEET = [foot(e) for e in FIXED]
RIM_TABLE = build_rim_table()
CLEAR = Clear(RIM_FEET)
_RIM = bowl_rim()
BOWL = [e['xy'] for e in _RIM]
BOWL_H = [e['h'] for e in _RIM]
BOWL_KIND = [e['kind'] for e in _RIM]
SKYPTS, SKY_RIM = ceiling_points()
ROOMS = build_rooms()


if __name__ == '__main__':
    objs = objects()
    for level in ('L2', 'L3', 'L4'):
        write(level, 'plan.yml', plan(level if level != 'L4' else 'L3'))
        write(level, 'project.yml', project(level))
    for level in ('L3', 'L4'):
        write(level, 'rooms.yml', ROOMS)
        write(level, 'atmosphere.yml', atmosphere())
    write('L3', 'objects.yml', {'format': 1, 'start': objs['start']})
    write('L4', 'objects.yml', objs)
    write('L4', 'wiring.yml', wiring())
    ps = ROOMS['rooms'][0]['platforms']
    print('rim points', len(BOWL), 'sky points', len(SKYPTS), 'platforms', len(ps), 'monsters', len(objs['monsters']),
          'D7 live', D7_LIVE, 'stair facing', STAIR_FAC, 'head', ipt(HEAD), 'way up', WAY_UP)
