#!/usr/bin/env python3
"""P1 Plane of Fire of Xeen: writes L2, L3 and L4 (A6's planes sub-agent, sixteenth session, 2026-11-21), after X9's
and P5's gen*.py (A5's open-air BLV route; nothing of theirs edited).

The plan is L1's (planes_design.py with D-58 applied); this file turns it into the studio's rooms, objects and wiring:

- room:crater, one open-air room: its floor the lava lake (lavtyl, the floor's `lava` kind, burning) at LAVA, its
  walls the crater's ragged cliffs to the sky at CEIL, a notch in the north-west for the Sleeper's Hall;
- the shelves as prisms standing in the lava (their L1 outlines, planes_geom.blob), floor-0 ground stepping straight
  out of the lava (40, a bank), every raised shelf with ramps down into it (D-58 Q1); the causeways as crust wedges;
- the Crucible: a ring of black glass on its rise round a pool of lava (the pit, burning), the test's plate at its
  south gate, the guardians (11623 and two 11622) a hidden group in the pit;
- room:hall, the Sleeper's Hall, its own open-air room behind the crater's wall, reached only through the gate (a
  hinged pair of black-glass leaves in the wall, opened by the test's qbit 111764): P-2 by construction;
- the nine vents as PressurePlate platforms (xpfvent), the basalt columns and the spire's red seam, the lava falls.

S's pieces (the statue and plaque, the sleeper and couch, the pedestal, the dais, the Ember Font, the camp, the way-up
column) are spots by name, blocked (C7: no stand-ins). D7 is not installed: the way up is sealed with a line until
xeen_d7.blv is in the world and lists entrance:p1_return (P1_D7_LIVE=1 forces it; D4's dungeon_live pattern).

    python3 level_generation/projects/xeen/p1/gen.py      # writes devdocs/xeen/briefs/p1/L2, L3, L4
"""
import copy
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

BRIEF = ROOT / 'devdocs/xeen/briefs/p1'
WORLD = ROOT / 'assets_dev/worlds/xeen'
PL = PG.Plane('p1')
D = PL.d
SPACE = PL.space
PLACE = PL.place

LAVA = -40            # the lava lake: the crater room's floor (L1 -64; 40 under the floor-0 shelves, a step out)
CEIL = 2960           # the sky over the crater's middle (its rim: RIM_LOW-RIM_HIGH over the lava, ceiling_points)
HALL_CEIL = 2760      # the Sleeper's Hall's sky: the tallest spire (the notch's corners 2,800 over the lava)
RIM_LOW, RIM_HIGH = 1400, 2800                       # the cliffs' tops over the lava (D-58 P-4, the lead's review)
HALL_FLOOR = SPACE['room:chamber']['floor']           # 384
WALL = 32             # the wall between the crater's notch and the hall
TEST_QBIT = PD.TEST_QBITS['fire']                     # 111764
SLEEPER_QBIT = PD.SLEEPER_QBITS['fire']               # 111760
GUARD_GROUP = 60
COMPASS = {'e': 0, 'ne': 45, 'n': 90, 'nw': 135, 'w': 180, 'sw': 225, 's': 270, 'se': 315}

# ------------------------------------------------------------------------------------------------ textures
LAVA_FLOOR = {'texture': 'lavtyl', 'size': [128, 128], 'scale': 2, 'liquid': 'lava'}
CRUST = {'texture': 'gcav2flr', 'size': [128, 128], 'scale': 2}          # MM8 Plane of Fire's black lava rock
VOLCANIC = {'texture': '6voltyl', 'size': [128, 128], 'scale': 2}        # MM6 Gharik's Forge volcanic floor
# the cliffs (look pass, D-58 P-4): three shipped rock faces, by band and by stretch of the rim
GRANITE = {'texture': 'vlcwl3a', 'size': [128, 256], 'scale': 4}         # MM6 grey-black crystalline rock
CLIFF = {'texture': 'vlcwl1', 'size': [128, 256], 'scale': 4}            # MM6 volcanic wall with lava seams
STRATA = {'texture': 'gcav2wal', 'size': [128, 256], 'scale': 4}         # MM8 Plane of Fire's black rock strata
COLUMNS = {'texture': 'vlcwl2', 'size': [128, 256], 'scale': 3}          # MM6 basalt columns (the spurs)
BASALT = {'texture': 'vlcwl3a', 'size': [128, 256], 'scale': 2}          # MM6 dark volcanic rock
HALL_WALL = {'texture': 'gnecwal1', 'size': [256, 256], 'scale': 2}      # MM8 Plane of Fire's crackled dark stone
HALL_FLOOR_S = {'texture': 'gcav1flr', 'size': [256, 256], 'scale': 1}   # MM8 Plane of Fire's dark rock floor
MOLTEN = {'texture': 'orfyrlga', 'size': [256, 256], 'scale': 2, 'flow': 'down'}   # falls: running down, no fluid bit
POOL = {'texture': 'lavtyl', 'size': [128, 128], 'scale': 2, 'liquid': 'lava'}
GLOW = {'texture': 'orfyrlga', 'size': [256, 256], 'scale': 2}   # a fall's pool: its picture drawn (burns by floors)
GLASS = {'texture': 'xpfglass', 'size': [128, 128], 'scale': 2}          # new (xtex.py, map_textures/p1)
VENT = {'texture': 'xpfvent', 'size': [128, 128], 'fit': True}  # s33: size is the picture's own (xpfvent 128); fit stretches it over the plate            # new, once per vent face
GLASS_LEAF = {'texture': 'xpfglass', 'size': [128, 128], 'fit': True, 'uneven': True}
RUBY = {'texture': 'xdvruby', 'size': [128, 256], 'fit': True}            # DD-10's ruby vein (A6)
SKY = {'texture': 'gcav1wal', 'size': [128, 128], 'scale': 32, 'sky': True}     # sky faces (plane_fire draws)


def live_d7():
    if os.environ.get('P1_D7_LIVE') == '1':
        return True
    studio = WORLD / 'maps/xeen_d7.studio.yml'
    return (WORLD / 'maps/xeen_d7.blv').exists() and studio.exists() and 'entrance:p1_return' in studio.read_text()


D7_LIVE = live_d7()


def key(sid):
    return sid.split(':', 1)[1]


def ipt(p):
    return [int(round(p[0])), int(round(p[1]))]


def ccw(poly):
    area = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))
    return poly if area > 0 else poly[::-1]


def ring(cx, cy, r, sides=16, phase=0.0, ry=None):
    ry = r if ry is None else ry
    return [(cx + r * math.cos(phase + 2 * math.pi * k / sides), cy + ry * math.sin(phase + 2 * math.pi * k / sides))
            for k in range(sides)]


def block(pid, at, size, z, rise, surface, top=None, facing=None, top_size=None, notes=None, floor=LAVA, **kw):
    e = {'id': pid, 'at': ipt(at), 'size': [int(round(size[0])), int(round(size[1]))],
         'base': int(round(z - floor)), 'rise': int(round(rise)), 'surface': surface}
    if top:
        e['top_surface'] = top
    if facing is not None:
        e['facing'] = round(facing, 4)
    if top_size:
        e['top_size'] = top_size
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def prism(pid, outline, z, rise, surface, top=None, notes=None, floor=LAVA, **kw):
    e = {'id': pid, 'outline': [ipt(p) for p in ccw(list(outline))], 'base': int(round(z - floor)),
         'rise': int(round(rise)), 'surface': surface, 'top_surface': top or surface}
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def slab(pid, a, b, z0, z1, width, surface, top, bottom_z, notes=None):
    """A wedge from a (top z0) to b (top z1), `width` wide, its underside flat at bottom_z (P5's platform_slab)."""
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    facing = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    low = bottom_z
    e = {'id': pid, 'at': ipt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)), 'size': [int(round(length)), int(width)],
         'facing': round(facing, 2), 'base': int(round(low - LAVA)), 'rise': int(round(min(z0, z1) - low)),
         'surface': surface, 'top_surface': top, 'bottom_surface': surface}
    if int(z0) != int(z1):
        e['top_heights'] = [int(round(z0 - low)), int(round(z1 - low)), int(round(z1 - low)), int(round(z0 - low))]
        e['thickness'] = int(round(min(z0, z1) - low))
    if notes:
        e['notes'] = notes
    return e


# ------------------------------------------------------------------------------------------------ the crater
HALL_RECT = (-5376, 3456, -2816, 5504)        # the Sleeper's Hall (L1 at (-4096, 4480), 2,560 x 2,048)
NOTCH_X = HALL_RECT[2] + WALL                 # the crater's notch wall facing the hall's east side
NOTCH_Y = HALL_RECT[1] - WALL                 # and its south side


def rim_radius(theta):
    rx, ry = PL.half[0] - 384, PL.half[1] - 384
    c, s = math.cos(theta), math.sin(theta)
    return (abs(c) ** 3.2 / rx ** 3.2 + abs(s) ** 3.2 / ry ** 3.2) ** (-1 / 3.2)


# ------------------------------------------------------------------------------------------------ shelves
SHELF_TOP = {'room:landing': CRUST, 'room:statue': VOLCANIC, 'room:islet': CRUST, 'room:spires': BASALT,
             'room:west_shelf': GLASS, 'room:vents': VOLCANIC}
SHELVES = [s for s in D['spaces'] if s['id'] not in ('room:chamber', 'room:arena')]


def shelf_outline(sid):
    return [ipt(p) for p in PG.blob(SPACE[sid], points=20)]


def shelves():
    out = []
    for s in SHELVES:
        out.append(prism(f"platform:{key(s['id'])}", shelf_outline(s['id']), LAVA, s['floor'] - LAVA, BASALT,
                         SHELF_TOP[s['id']], notes=f"{s['name']}: {s['shape']} (floor {s['floor']})."))
    return out


# the ramps up every raised shelf (D-58 Q1): two each where no causeway leaves, the arena three
RAMP_SLOPE = 0.3
RAMP_W = 384
RAMPS = {'room:statue': [150, 330], 'room:islet': [110, 250], 'room:spires': [30, 280],
         'room:west_shelf': [200, 140], 'room:arena': [10, 160, 330]}


def ramp(sid, deg, k):
    s = SPACE[sid]
    c = s['at']
    th = math.radians(deg)
    if sid == 'room:arena':
        r = arena_r(th)
    else:
        rim = PG.ray_exit(PL.polys[sid], c, (c[0] + 20000 * math.cos(th), c[1] + 20000 * math.sin(th)))
        r = math.hypot(rim[0] - c[0], rim[1] - c[1])
    top = s['floor'] + 4
    run = (top - (LAVA + 32)) / RAMP_SLOPE
    a = (c[0] + (r - 128) * math.cos(th), c[1] + (r - 128) * math.sin(th))
    b = (c[0] + (r + run) * math.cos(th), c[1] + (r + run) * math.sin(th))
    return slab(f"platform:{key(sid)}_ramp{k}", a, b, top, LAVA + 32, RAMP_W, BASALT, CRUST, LAVA + 8,
                notes=f"A crust ramp out of the lava up to {s['name']} (D-58 Q1), its foot 32 over the lava.")


def ramps():
    return [ramp(sid, deg, k + 1) for sid, degs in RAMPS.items() for k, deg in enumerate(degs)]


# ------------------------------------------------------------------------------------------------ causeways
INTO = 192


def link_cut(l):
    p, q = PL.link_ends(l)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * INTO, p[1] - uy * INTO), (q[0] + ux * INTO, q[1] + uy * INTO), d


def causeways():
    out = []
    for l in D['links']:
        if l.get('gate'):
            continue
        a, b, d = link_cut(l)
        za, zb = SPACE[l['a']]['floor'] + 4, SPACE[l['b']]['floor'] + 4
        out.append(slab(f"platform:{key(l['id'])}", a, b, za, zb, l['width'], BASALT, CRUST, LAVA + 8,
                        f"{l['id']}: a causeway of cooled black crust, {int(d):,} rim to rim, rising {zb - za}."))
    return out


GATE_Y = 4096                                  # the gate's middle on the hall's east wall


def bridge():
    """The obsidian bridge from the Crucible's west rim to the gate in the crater's notch wall; its deck meets the
    doorway's sill (the hall's floor, 384) at the wall."""
    c = SPACE['room:arena']['at']
    th = math.atan2(GATE_Y - c[1], NOTCH_X - c[0])
    r = arena_r(th)
    a = (c[0] + (r - INTO) * math.cos(th), c[1] + (r - INTO) * math.sin(th))
    b = (NOTCH_X + 2, GATE_Y)
    return [slab('platform:bridge', a, b, SPACE['room:arena']['floor'] + 4, HALL_FLOOR, 640, BASALT, GLASS, LAVA + 8,
                 "The obsidian bridge to the Sleeper's Gate (link:sleepers_gate): its deck meets the doorway's sill.")]


# ------------------------------------------------------------------------------------------------ the Crucible
ARENA_R = (1600, 1472)        # half the L1 extent less 64
PIT_R = 448
ARENA_SPLIT = (-92, 92)       # the east half's angles; the west half 88-272, its top 2 higher (no faces in one plane)


def arena_r(th):
    return 1.0 / math.sqrt((math.cos(th) / ARENA_R[0]) ** 2 + (math.sin(th) / ARENA_R[1]) ** 2)


def half_ring(a0, a1, steps=10):
    c = SPACE['room:arena']['at']
    outer, inner = [], []
    for k in range(steps + 1):
        th = math.radians(a0 + (a1 - a0) * k / steps)
        r = arena_r(th)
        outer.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
        inner.append((c[0] + PIT_R * math.cos(th), c[1] + PIT_R * math.sin(th)))
    return outer + inner[::-1]


PIT_AT = SPACE['room:arena']['at']


def crucible():
    z = SPACE['room:arena']['floor']
    return [
        prism('platform:arena_east', half_ring(*ARENA_SPLIT), LAVA, z - LAVA, BASALT, GLASS,
              notes="The Crucible: a ring of black glass on its basalt rise (D-58 P-4), the east half."),
        prism('platform:arena_west', half_ring(88, 272), LAVA, z + 2 - LAVA, BASALT, GLASS,
              notes="The Crucible's west half (2 higher where the halves overlap)."),
        prism('platform:pit', ring(PIT_AT[0], PIT_AT[1], PIT_R + 16, 24), LAVA, z - 24 - LAVA, BASALT, POOL,
              notes="The pit: lava welling in the ring, 24 under the glass (burning, floors); the guardians rise here."),
        block('platform:test_plate', PLACE['poi:test']['at'], (256, 256), z + 2, 4, GLASS, GLASS,
              notes="The test's floor before S's pedestal (poi:test): stepping on asks 'Accept the test of Fire?'."),
    ]


# ------------------------------------------------------------------------------------------------ vents, spires
def vents():
    out = []
    for i, c in enumerate(D['hazard']['cells']):
        z = PL.floor_at(c)
        out.append(block(f'platform:vent{i + 1}', c, (192, 192), z, 4, CRUST, VENT,
                         notes="A vent (D-58 P1 Q2): a PressurePlate face, xpfvent, planes.vent." if i == 0 else None))
    return out


SPIRE_COLUMNS = [((3200, 384), 160, 900), ((4608, 2176), 160, 1500), ((3008, 1408), 128, 700),
                 ((4864, 640), 176, 1200), ((4480, 1920), 224, 1700), ((3712, 2304), 144, 1000)]


def spires():
    out = []
    z = SPACE['room:spires']['floor']
    poly = shelf_outline('room:spires')
    for i, (at, r, h) in enumerate(SPIRE_COLUMNS):
        if not all(PG.point_in(q, poly) and min_edge(poly, q) > 64 for q in ring(at[0], at[1], r, 6, 0.3 * i)):
            continue
        out.append(prism(f'platform:column{i + 1}', ring(at[0], at[1], r, 6, 0.3 * i), z - 8, h + 8, BASALT, BASALT,
                         notes="Basalt columns among the spires." if i == 0 else None))
    sx, sy = PLACE['poi:spire_glass']['at']
    out.append(block('platform:spire_seam', (sx - 224 * math.cos(math.pi / 6) - 6, sy), (8, 192), z, 480, RUBY,
                     BASALT, end_surface=dict(BASALT, uneven=True), notes="The seam of red crystal in the tallest spire (poi:spire_glass, planes.spire), "
                                   "on its west face."))
    return out


# ------------------------------------------------------------------------------------------------ geometry helpers
def foot(e):
    """A platform's footprint: its outline, or its block's rectangle turned by `facing`."""
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


def area2(poly):
    return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


# places the playtests stand on in the lava (the burn, the step out, the P-2 proof): no rock within the radius
KEEP_CLEAR = [((0, -4800), 560), ((2560, -4480), 460), ((-2650, 5150), 420), ((-3600, 3150), 460),
              ((-2700, 4600), 300)]


def kept_clear(p, pad=0):
    return any(math.hypot(p[0] - c[0], p[1] - c[1]) < r + pad for c, r in KEEP_CLEAR)


# ------------------------------------------------------------------------------------------------ crust aprons
def lanes():
    """The centre lines walked onto the shelves (ramps, causeways, the bridge): (a, b, half width)."""
    out = []
    for e in ramps() + causeways() + bridge():
        f = foot(e)
        out.append((((f[0][0] + f[3][0]) / 2, (f[0][1] + f[3][1]) / 2),
                    ((f[1][0] + f[2][0]) / 2, (f[1][1] + f[2][1]) / 2), e['size'][1] / 2, e['id']))
    return out


def near_lane(pts, lane_list, pad, skip=None):
    return any(seg_dist(p, a, b) < hw + pad for a, b, hw, lid in lane_list if lid != skip for p in pts)


def apron(pid, p, q, n, zp, zq, run_p, run_q, out_p, out_q):
    """A sloping skirt of crust from a top edge p-q (heights zp, zq over the lava) out along n to the lava (out_*):
    the shelf's side read as rough crust, not an extruded plate."""
    ip, iq = (p[0] - n[0] * 16, p[1] - n[1] * 16), (q[0] - n[0] * 16, q[1] - n[1] * 16)
    op, oq = (p[0] + n[0] * run_p, p[1] + n[1] * run_p), (q[0] + n[0] * run_q, q[1] + n[1] * run_q)
    pts, hs = [ip, iq, oq, op], [zp, zq, out_q, out_p]
    if area2(pts) < 0:
        pts, hs = pts[::-1], hs[::-1]
    hs = [int(round(h)) for h in hs]
    steep = max(zp, zq) / max(1.0, min(run_p, run_q)) > 0.9
    # a steep skirt's crust is drawn out down its slope (the studio lays a top by x and y): meant, not a mistake
    return {'id': pid, 'outline': [ipt(v) for v in pts], 'base': 0, 'rise': min(hs), 'top_heights': hs,
            'surface': BASALT, 'top_surface': dict(CRUST, uneven=True) if steep else CRUST}


def edge_runs(rnd, rise):
    """Outer runs and foot heights of one skirt piece: floor-0 banks walkable (under 0.6), raised shelves steep
    (1.15-1.75: steep_floor, the party slides back into the lava)."""
    out_p, out_q = rnd.randint(4, 20), rnd.randint(4, 20)
    if rise <= 48:
        return rnd.randint(72, 128), rnd.randint(72, 128), out_p, out_q
    s1, s2 = rnd.uniform(1.15, 1.75), rnd.uniform(1.15, 1.75)
    return max(48, (rise - out_p) / s1), max(48, (rise - out_q) / s2), out_p, out_q


def within_rim(p, margin):
    return math.hypot(p[0], p[1]) < rim_radius(math.atan2(p[1], p[0])) - margin


def shelf_aprons():
    rnd = random.Random(4242)
    L = lanes()
    out = []
    rings = [(s['id'], ccw([tuple(v) for v in shelf_outline(s['id'])]), s['floor'] - LAVA) for s in SHELVES]
    c = SPACE['room:arena']['at']
    rings.append(('room:arena', [(c[0] + arena_r(t) * math.cos(t), c[1] + arena_r(t) * math.sin(t))
                                 for t in (2 * math.pi * k / 28 for k in range(28))], SPACE['room:arena']['floor'] - LAVA))
    for sid, poly, rise in rings:
        k = 0
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            d = math.hypot(q[0] - p[0], q[1] - p[1])
            n = ((q[1] - p[1]) / d, -(q[0] - p[0]) / d)          # outward (the ring runs counter-clockwise)
            run_p, run_q, out_p, out_q = edge_runs(rnd, rise)
            far = [(p[0] + n[0] * run_p, p[1] + n[1] * run_p), (q[0] + n[0] * run_q, q[1] + n[1] * run_q)]
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if near_lane([p, q, mid] + far, L, 96) or any(kept_clear(v, 64) for v in [p, q] + far):
                continue
            if not all(within_rim(v, 320) for v in far) or math.hypot(mid[0] - 4864, mid[1] + 4864) < 900:
                continue                                          # under the rim, and the way up's corner
            k += 1
            out.append(apron(f"platform:{key(sid)}_crust{k}", p, q, n, rise - 4, rise - 4, run_p, run_q, out_p, out_q))
    return out


def causeway_aprons():
    rnd = random.Random(5151)
    L = lanes()
    shelves_polys = [shelf_outline(s['id']) for s in SHELVES] + [half_ring(-92, 92), half_ring(88, 272)]
    out = []
    for l in D['links']:
        if l.get('gate'):
            continue
        a, b, _ = link_cut(l)
        za, zb = SPACE[l['a']]['floor'] + 4 - LAVA, SPACE[l['b']]['floor'] + 4 - LAVA
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
        k = 0
        for sgn in (1, -1):
            n = (-u[1] * sgn, u[0] * sgn)
            t = rnd.uniform(0.0, 120.0)
            while t < length:
                t1 = min(length, t + rnd.uniform(380, 620))
                p = (a[0] + u[0] * t + n[0] * l['width'] / 2, a[1] + u[1] * t + n[1] * l['width'] / 2)
                q = (a[0] + u[0] * t1 + n[0] * l['width'] / 2, a[1] + u[1] * t1 + n[1] * l['width'] / 2)
                zp, zq = za + (zb - za) * t / length - 4, za + (zb - za) * t1 / length - 4
                run_p, _, out_p, _ = edge_runs(rnd, zp)
                run_q, _, out_q, _ = edge_runs(rnd, zq)
                if sgn < 0:
                    p, q, zp, zq, run_p, run_q, out_p, out_q = q, p, zq, zp, run_q, run_p, out_q, out_p
                far = [(p[0] + n[0] * run_p, p[1] + n[1] * run_p), (q[0] + n[0] * run_q, q[1] + n[1] * run_q)]
                ok = (not any(poly_dist(v, sp) < 200 for v in (p, q) for sp in shelves_polys)
                      and not near_lane([p, q] + far, L, 64, skip=f"platform:{key(l['id'])}")
                      and not any(kept_clear(v, 64) for v in [p, q] + far))
                if ok:
                    k += 1
                    out.append(apron(f"platform:{key(l['id'])}_crust{k}", p, q, n, zp, zq, run_p, run_q, out_p,
                                     out_q))
                t = t1 + rnd.uniform(0, 64)
    return out


# ------------------------------------------------------------------------------------------------ the gate's frame
JAMB = (160, 176)             # depth out of the wall, width beside the doorway
GATE_W, GATE_H = 640, 512


def gate_frame():
    """The Sleeper's Gate framed: jambs of black glass, a basalt lintel, a rough gable of glass over it and two
    obsidian shards beside it, all against the notch wall on the crater's side (the leaves swing into the hall)."""
    x0 = NOTCH_X
    top = HALL_FLOOR + GATE_H                                   # the doorway's head, 896
    out = []
    for k, sgn in enumerate((-1, 1)):
        y = GATE_Y + sgn * (GATE_W / 2 + JAMB[1] / 2)
        out.append(block(f'platform:gate_jamb{k + 1}', (x0 + JAMB[0] / 2, y), JAMB, LAVA, top + 160 - LAVA, GLASS,
                         BASALT, end_surface=dict(BASALT, fit=False),
                         notes="The Sleeper's Gate's frame: jambs of black glass from the lava to over the lintel."
                         if k == 0 else None))
    span = GATE_W + 2 * JAMB[1] + 96
    out.append(block('platform:gate_lintel', (x0 + 92, GATE_Y), (176, span), top, 192, BASALT, BASALT,
                     bottom_surface=GLASS, notes="The lintel: basalt over the doorway, its underside glass."))
    half = span / 2
    for k, (sgn, toward) in enumerate(((-1, 'north'), (1, 'south'))):
        out.append(block(f'platform:gate_gable{k + 1}', (x0 + 64, GATE_Y + sgn * half / 2), (128, half), top + 192, 0,
                         GLASS, GLASS, top_slope={'to': 384, 'toward': toward},
                         notes="A rough gable of black glass over the lintel (two wedges)." if k == 0 else None))
    for k, sgn in enumerate((-1, 1)):
        y = GATE_Y + sgn * (GATE_W / 2 + JAMB[1] + 120)
        out.append(block(f'platform:gate_shard{k + 1}', (x0 + 112, y), (192, 176), LAVA, 1560 - LAVA, GLASS, GLASS,
                         top_size=[24, 40], end_surface=dict(BASALT, fit=False),
                         notes="Obsidian shards either side of the gate." if k == 0 else None))
    return out


# ------------------------------------------------------------------------------------------------ the rim
MAX_POINTS = 64              # the studio's limit on an outline
MAX_TEETH = 8
GRID = 16                    # rim corners on a 16 grid: points on the walls between them fall on whole units
FALLS = (166, 52)             # the two lava falls (degrees): the Glass Shelf's (landmark:lava_fall), the north-east's
WAY_UP_DEG = -45
NOTCH_CORNERS = [(NOTCH_X, NOTCH_Y)]


def skyline(t):
    """The cliffs' tops over the lava along the rim: a slow swell of massifs (RIM_LOW-RIM_HIGH)."""
    return 2060 + 430 * math.sin(2 * t + 1.3) + 240 * math.sin(5 * t + 0.4)


def landing_edge(t):
    """How far from the middle the Cinder Shelf reaches along the ray at t (the way up's fissure stands just past)."""
    poly = shelf_outline('room:landing')
    r_hit = 0
    for r in range(4000, 7200, 16):
        if PG.point_in((r * math.cos(t), r * math.sin(t)), poly):
            r_hit = r
    return r_hit


def rim_entries(clear, rim_n):
    rnd = random.Random(2511)
    feats = []                                    # (t0, half span in radians, entries)
    # the falls: a gully into the cliff, its back wall the molten fall, its lip a dip in the skyline
    for deg in FALLS:
        t0 = math.radians(deg)
        R = rim_radius(t0)
        mouth = 150
        while mouth > 0 and clear.dist(((R - mouth) * math.cos(t0), (R - mouth) * math.sin(t0))) < 300:
            mouth -= 16
        e = [{'t': t0 - 420 / R, 'inset': mouth, 'kind': 'fall_side', 'h': 2420},
             {'t': t0 - 224 / R, 'inset': mouth - 448, 'kind': 'fall_back', 'h': 1720},
             {'t': t0 + 224 / R, 'inset': mouth - 448, 'kind': 'fall_back', 'h': 1780},
             {'t': t0 + 420 / R, 'inset': mouth, 'kind': 'fall_side', 'h': 2480}]
        feats.append((t0, 420 / R, e))
    # the way up: a narrow fissure just past the Cinder Shelf's corner, its back wall the heat column
    t0 = math.radians(WAY_UP_DEG)
    R = rim_radius(t0)
    r_mouth = min(landing_edge(t0) + 128, R - 32)
    mouth = R - r_mouth
    e = [{'t': t0 - 240 / R, 'inset': mouth, 'kind': 'way_side', 'h': 2200},
         {'t': t0 - 150 / R, 'inset': mouth - 176, 'kind': 'way_back', 'h': 1980},
         {'t': t0 + 150 / R, 'inset': mouth - 176, 'kind': 'way_back', 'h': 2040},
         {'t': t0 + 240 / R, 'inset': mouth, 'kind': 'way_side', 'h': 2260}]
    feats.append((t0, 240 / R, e))
    # the spurs: teeth of the outline reaching into the lava, their noses lower (a ridge running down)
    taken = [f[0] for f in feats]
    teeth = 0
    for k in range(22):
        t0 = 2 * math.pi * (k + rnd.uniform(-0.3, 0.3)) / 22
        R = rim_radius(t0)
        if teeth >= MAX_TEETH or any(abs(angdiff(t0, t)) < math.radians(15) for t in taken):
            continue
        rim_pt = ((R - 200) * math.cos(t0), (R - 200) * math.sin(t0))
        if rim_pt[0] < NOTCH_X + 900 and rim_pt[1] > NOTCH_Y - 900:
            continue
        w = rnd.uniform(380, 600)
        base = rnd.uniform(90, 200)
        depth = rnd.uniform(560, 960)
        skew = rnd.uniform(-90, 90)
        while depth >= 400:
            pts = [(t0 - w / R, base), (t0 + skew / R, base + depth), (t0 + w / R, base + rnd.uniform(-40, 60))]
            xy = [((rim_radius(t) - i) * math.cos(t), (rim_radius(t) - i) * math.sin(t)) for t, i in pts]
            if all(clear.seg(xy[j], xy[j + 1]) >= 320 for j in range(2)) and not any(kept_clear(v, 160) for v in xy):
                break
            depth -= 64
        else:
            continue
        hf = max(1900, skyline(t0) + rnd.uniform(-100, 300))
        e = [{'t': pts[0][0], 'inset': pts[0][1], 'kind': 'tooth_flank', 'h': hf + rnd.uniform(-80, 160)},
             {'t': pts[1][0], 'inset': pts[1][1], 'kind': 'tooth_nose', 'h': hf - rnd.uniform(400, 700)},
             {'t': pts[2][0], 'inset': pts[2][1], 'kind': 'tooth_flank', 'h': hf + rnd.uniform(-80, 160)}]
        feats.append((t0, w / R, e))
        taken.append(t0)
        teeth += 1
    # the ragged rim between: every point its own inset (facets, no long straight runs) and its own top
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
    # clear of every shelf, skirt, ramp and causeway: plain rim points step back toward the outer limit
    xy = lambda e: ((rim_radius(e['t']) - e['inset']) * math.cos(e['t']), (rim_radius(e['t']) - e['inset']) * math.sin(e['t']))
    for e in entries:
        while e['kind'] == 'rim' and e['inset'] > 16 and clear.dist(xy(e)) < 200:
            e['inset'] -= 24
    n = len(entries)
    for _ in range(30):
        moved = False
        for i in range(n):
            a, b = entries[i], entries[(i + 1) % n]
            if clear.seg(xy(a), xy(b)) < 160:
                for e in (a, b):
                    if e['kind'] == 'rim' and e['inset'] > 16:
                        e['inset'] = max(16, e['inset'] - 24)
                        moved = True
        if not moved:
            break
    for e in entries:
        e['xy'] = xy(e)
    return entries


def crater_rim():
    """The crater's outline with the notch for the hall cut out (the notch's corners the tallest rock, RIM_HIGH),
    each point's top over the lava, and its kind (rim, tooth, fall, way up, notch)."""
    for rim_n in range(60, 8, -1):
        out = cut_notch(rim_entries(CLEAR, rim_n))
        if len(out) <= MAX_POINTS:
            break
    return finish_rim(out)


def cut_notch(pts):
    n = len(pts)
    inside = [p['xy'][0] < NOTCH_X and p['xy'][1] > NOTCH_Y for p in pts]
    first = next(i for i in range(n) if inside[i] and not inside[i - 1])
    last = next(i for i in range(n) if inside[i] and not inside[(i + 1) % n])
    a, b = pts[first - 1]['xy'], pts[first]['xy']
    t = (NOTCH_X - a[0]) / (b[0] - a[0])
    north = (NOTCH_X, a[1] + (b[1] - a[1]) * t)
    c, d = pts[last]['xy'], pts[(last + 1) % n]['xy']
    t = (NOTCH_Y - c[1]) / (d[1] - c[1])
    west = (c[0] + (d[0] - c[0]) * t, NOTCH_Y)
    out = []
    i = (last + 1) % n
    while i != first:
        out.append(pts[i])
        i = (i + 1) % n
    out += [{'xy': north, 'h': RIM_HIGH, 'kind': 'notch'}, {'xy': (NOTCH_X, NOTCH_Y), 'h': RIM_HIGH, 'kind': 'notch'},
            {'xy': west, 'h': RIM_HIGH, 'kind': 'notch'}]
    return out


def finish_rim(out):
    north, west = out[-3]['xy'], out[-1]['xy']
    # the hall is cut into the tallest spire: the rock near the notch rises to it
    for e in out:
        dn = min(math.hypot(e['xy'][0] - q[0], e['xy'][1] - q[1]) for q in (north, west))
        if e['kind'] != 'notch' and dn < 2200:
            e['h'] = max(e['h'], RIM_HIGH - 300 * dn / 2200 - (120 if out.index(e) % 2 else 0))
    # no top rises more than 1.8 for each unit along the rim (the ceiling stays a ceiling, under the limit of 2)
    m = len(out)
    for _ in range(40):
        for i in range(m):
            a, b = out[i], out[(i + 1) % m]
            lim = 1.8 * math.hypot(a['xy'][0] - b['xy'][0], a['xy'][1] - b['xy'][1])
            if abs(a['h'] - b['h']) > lim:
                hi, lo = (a, b) if a['h'] > b['h'] else (b, a)
                if hi['kind'] == 'notch':
                    lo['h'] = hi['h'] - lim
                else:
                    hi['h'] = lo['h'] + lim
    for e in out:
        e['h'] = int(round(max(RIM_LOW, min(RIM_HIGH, e['h']))))
        e['xy'] = [int(round(e['xy'][0] / GRID)) * GRID, int(round(e['xy'][1] / GRID)) * GRID]
    return out


def notch_edges():
    """Edge numbers of the crater's notch walls (edge k runs from point k to k + 1)."""
    n = len(CRATER)
    east = next(k for k in range(n) if CRATER[k][0] == NOTCH_X and CRATER[(k + 1) % n] == [NOTCH_X, NOTCH_Y])
    return east, (east + 1) % n


def greedy_triangles(pts, n_rim, poly):
    """The ceiling's triangles as the studio makes them (the shortest lines first, inside the room, the walls kept):
    used to drop the points that would make a sliver steeper than a ceiling may be."""
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
        C, D = P[[e[0] for e in E]], P[[e[1] for e in E]]
        cr = lambda o, a, b: (a[..., 0] - o[..., 0]) * (b[..., 1] - o[..., 1]) - (a[..., 1] - o[..., 1]) * (b[..., 0] - o[..., 0])
        d1, d2 = cr(C, D, A[None]), cr(C, D, B[None])
        d3, d4 = cr(A[None], B[None], C), cr(A[None], B[None], D)
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


def tri_rise(p, q, r):
    """The rise for each unit of run of the plane through three points [x, y, z]."""
    ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
    vx, vy, vz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    return float('inf') if nz == 0 else math.hypot(nx, ny) / abs(nz)


def ceiling_points():
    """The sky over the crater: every rim corner at its cliff's top, one to three more points on each rim wall between
    (the walls end on that line: a jagged skyline, not flat-topped slabs), and a ring at CEIL over the middle, so
    nothing in the crater stands near the sky."""
    rnd = random.Random(77)
    poly = [tuple(p) for p in CRATER]
    n = len(CRATER)
    inner = []
    for k in range(12):
        t = 2 * math.pi * (k + 0.5) / 12
        r = 0.68 * rim_radius(t)
        q = (r * math.cos(t), r * math.sin(t))
        if PG.point_in(q, poly) and poly_dist_outline(q, poly) > 700:
            inner.append([int(q[0]), int(q[1]), CEIL])
    inner.append([0, 0, CEIL])
    budget = int((192 - len(inner)) / 1.5) - n             # rim points, and a near ring of half as many
    lens = [math.hypot(CRATER[(k + 1) % n][0] - CRATER[k][0], CRATER[(k + 1) % n][1] - CRATER[k][1]) for k in range(n)]
    want = {k: 0 for k in range(n)}
    for _ in range(3):                                     # one each to the longest walls first, then a second ...
        for k in sorted(range(n), key=lambda k: -lens[k]):
            if budget and lens[k] >= 360 * (want[k] + 1) and RIM_KIND[k] not in ('fall_back', 'way_back'):
                want[k] += 1
                budget -= 1
    pts = []
    for k in range(n):
        a, b = CRATER[k], CRATER[(k + 1) % n]
        ha, hb = CRATER_H[k], CRATER_H[(k + 1) % n]
        pts.append([a[0], a[1], LAVA + ha])
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
        for _ in range(6):                                 # 1.8 for each unit along the wall at most
            for i in range(1, len(line) - 1):
                f, h = line[i]
                for g2 in (line[i - 1], line[i + 1]):
                    lim = 1.8 * abs(f - g2[0]) * lens[k]
                    h = max(g2[1] - lim, min(g2[1] + lim, h))
                line[i] = (f, max(RIM_LOW, min(RIM_HIGH, h)))
        for (f, h), s in zip(line[1:-1], steps):
            pts.append([a[0] + dx * s // g, a[1] + dy * s // g, LAVA + int(round(h))])
    # a near ring, 360 inside every other rim point and higher than it: the triangles stay broad (no slivers along
    # a slightly bent wall, which would stand steeper than a ceiling may)
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
    # drop the ring points (then the rim's points on walls) that make a triangle steeper than 3.8
    for _ in range(60):
        n_rim = sum(1 for p in pts[:m])
        bad = [t for t in greedy_triangles(pts, m, poly) if tri_rise(*(pts[i] for i in t)) > 3.8]
        if not bad:
            break
        drop = set()
        for t in bad:
            free = [i for i in t if i >= m and pts[i][2] != CEIL] or [i for i in t if i >= m]
            if free:
                drop.add(max(free))
            else:
                onwall = [i for i in t if list(pts[i][:2]) not in CRATER]
                if onwall:
                    drop.add(onwall[0])
        if not drop:
            break
        m -= sum(1 for i in drop if i < m)
        pts = [p for i, p in enumerate(pts) if i not in drop]
    assert len(pts) <= 192, len(pts)
    return pts, m


def poly_dist_outline(q, poly):
    return min(seg_dist(q, poly[i - 1], poly[i]) for i in range(len(poly)))


def wall_surfaces():
    """The walls that are not the theme's lava-seamed rock: black strata on every other stretch of the rim and the
    notch, basalt columns on the spurs, the molten falls and the heat column (no bands: molten to the foot)."""
    out = []
    n = len(CRATER)
    for k in range(n):
        a, b = RIM_KIND[k], RIM_KIND[(k + 1) % n]
        if a == b == 'fall_back' or a == b == 'way_back':
            out.append({'wall': k, 'surface': MOLTEN})
        elif 'tooth_nose' in (a, b) or a == b == 'tooth_flank':
            out.append({'wall': k, 'surface': COLUMNS})
        elif 'notch' in (a, b) or 'fall_side' in (a, b) or 'way_side' in (a, b):
            out.append({'wall': k, 'surface': STRATA})
        else:
            mx, my = (CRATER[k][0] + CRATER[(k + 1) % n][0]) / 2, (CRATER[k][1] + CRATER[(k + 1) % n][1]) / 2
            sec = int((math.atan2(my, mx) + math.pi) / (2 * math.pi / 11)) % 3
            if sec:
                out.append({'wall': k, 'surface': (STRATA, GRANITE)[sec - 1]})
    return out


# ------------------------------------------------------------------------------------------------ ledges, needles
def local_top(p, reach=1100):
    """The lowest cliff top within reach of p (absolute): what stands by the wall stays under the sky there."""
    return min(q[2] for q in SKYPTS[:SKY_RIM] if math.hypot(q[0] - p[0], q[1] - p[1]) < reach)


def inside_by(poly_pts, margin):
    crater = [tuple(p) for p in CRATER]
    return all(PG.point_in(v, crater) and poly_dist_outline(v, crater) >= margin for v in poly_pts)


# directions whose sines and cosines are whole-number ratios (Pythagorean triples): a tapered block turned to one
# of them, with its sizes multiples of twice the triple's long side, keeps whole-unit corners and flat leaning faces
PYTH = [(1, 0, 1), (24, 7, 25), (12, 5, 13), (15, 8, 17), (4, 3, 5), (21, 20, 29)]


def snap_facing(deg):
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


def tiers():
    """Stepped ledges against the cliff where the lava is wide: a tapered block leaning back (its face slopes in),
    a ledge on it with a jagged top that juts past its front (leaning out), sometimes a rock needle before it."""
    rnd = random.Random(909)
    out = []
    n = len(CRATER)
    last = None
    k = 0
    sites = []
    for i in range(n):
        if RIM_KIND[i] not in ('rim', 'notch') or RIM_KIND[(i + 1) % n] not in ('rim', 'notch'):
            continue
        a, b = CRATER[i], CRATER[(i + 1) % n]
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        m = max(1, int(ln // 900))                            # long walls (the notch's) take more than one
        for s in range(m):
            f0, f1 = s / m, (s + 1) / m
            sites.append(((a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0),
                          (a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1)))
    for a, b in sites:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if last is not None and math.hypot(mid[0] - last[0], mid[1] - last[1]) < 1300:
            continue
        if CLEAR.dist(mid) < 720 or kept_clear(mid, 900) or rnd.random() < 0.15:
            continue
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nin = (-u[1], u[0])                                   # into the crater (the outline runs counter-clockwise)
        fac, q = snap_facing(math.degrees(math.atan2(u[1], u[0])))
        u = (math.cos(math.radians(fac)), math.sin(math.radians(fac)))
        nin = (-u[1], u[0])
        la, da = mult(rnd.uniform(560, 860), q), mult(rnd.uniform(300, 440), q)
        tla, tda = mult(la * 0.86, q), mult(da * 0.5, q)
        off = 12
        while off < 260:
            ca = (mid[0] + nin[0] * (da / 2 + off), mid[1] + nin[1] * (da / 2 + off))
            ea = {'at': ipt(ca), 'size': [int(la), int(da)], 'facing': fac}
            if inside_by(foot(ea), 8):
                break
            off += 16
        else:
            continue
        cap = local_top(mid) - 160 - LAVA
        ha = rnd.uniform(420, 860)
        hb_back, hb_front = rnd.uniform(380, 820), rnd.uniform(160, 420)
        if ha + 200 > cap:
            continue
        sc = min(1.0, (cap - ha) / hb_back)
        hb_back, hb_front = hb_back * sc, min(hb_front, hb_back * sc - 40)
        k += 1
        last = mid
        out.append(block(f'platform:spur{k}', ca, (la, da), LAVA, ha, STRATA, BASALT, facing=fac,
                         top_size=[tla, tda], end_surface=dict(STRATA, fit=False),
                         notes="Ledges against the cliff (D-58 P-4: the wall stepped back, leaning in and out)."
                         if k == 1 else None))
        # the ledge on it: from the wall to past the tapered block's front, its top jagged
        back = off + 4
        front = off + da * 0.86
        lb = la * rnd.uniform(0.5, 0.7)
        sh = rnd.uniform(-0.12, 0.12) * la
        loc = [(-lb / 2 + sh, back), (lb / 2 + sh, back), (lb / 2 * 0.8 + sh, front), (-lb / 2 * 0.9 + sh, front)]
        pts = [(mid[0] + x * u[0] + y * nin[0], mid[1] + x * u[1] + y * nin[1]) for x, y in loc]
        hs = [hb_back * rnd.uniform(0.8, 1.0), hb_back, hb_front, hb_front * rnd.uniform(0.6, 1.0)]
        if inside_by(pts, 8):
            if area2(pts) < 0:
                pts, hs = pts[::-1], hs[::-1]
            out.append({'id': f'platform:spur{k}_ledge', 'outline': [ipt(p) for p in pts], 'base': int(round(ha)),
                        'rise': int(min(hs)), 'top_heights': [int(round(h)) for h in hs], 'surface': CLIFF,
                        'top_surface': dict(BASALT, uneven=True), 'bottom_surface': STRATA})
        # a needle of rock before it
        if rnd.random() < 0.55:
            dn = off + da + rnd.uniform(140, 320)
            cn = (mid[0] + nin[0] * dn + u[0] * rnd.uniform(-200, 200), mid[1] + nin[1] * dn + u[1] * rnd.uniform(-200, 200))
            nf, nq = snap_facing(fac + rnd.uniform(-30, 30))
            nsz = (mult(200, nq), mult(180, nq))
            en = {'at': ipt(cn), 'size': list(nsz), 'facing': nf}
            hn = min(cap - 80, rnd.uniform(520, 1100))
            if CLEAR.dist(cn) > 480 and inside_by(foot(en), 64) and hn > 300:
                out.append(block(f'platform:spur{k}_needle', cn, nsz, LAVA, hn, COLUMNS, BASALT,
                                 facing=nf, top_size=[mult(40, nq), mult(52, nq)]))
    return out


def seg_cross(p, q, poly):
    """True when p-q crosses an edge of poly (not at a shared end)."""
    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    for i in range(len(poly)):
        c, d = poly[i - 1], poly[i]
        if (cr(c, d, p) * cr(c, d, q) < 0) and (cr(p, q, c) * cr(p, q, d) < 0):
            return True
    return False


def talus():
    """Scree at the cliffs' foot: a steep wedge along each rim wall, 240-640 up the wall, so the cliff leans out at
    its foot and no wall stands as a flat slab from the lava (not on the notch's walls, nor in the gullies)."""
    rnd = random.Random(616)
    out = []
    n = len(CRATER)
    poly = [tuple(p) for p in CRATER]
    plain = ('rim', 'tooth_flank', 'tooth_nose')
    for k in range(n):
        if RIM_KIND[k] not in plain or RIM_KIND[(k + 1) % n] not in plain:
            continue
        a, b = CRATER[k], CRATER[(k + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 240:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nin = (-u[1], u[0])
        a1 = (a[0] + u[0] * 24 + nin[0] * 6, a[1] + u[1] * 24 + nin[1] * 6)
        b1 = (b[0] - u[0] * 24 + nin[0] * 6, b[1] - u[1] * 24 + nin[1] * 6)
        ha = rnd.uniform(260, 620)
        hb = ha * rnd.uniform(0.75, 1.3)
        ra, rb = ha / rnd.uniform(1.1, 1.45), hb / rnd.uniform(1.1, 1.45)
        for _ in range(5):
            sq = min(1.0, (L - 112) / max(1.0, 0.5 * (ra + rb)))      # the wedge's foot stays wider than nothing
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
                  and min(CLEAR.dist(v) for v in (a2, b2, ((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2))) >= 160
                  and not any(kept_clear(v, 120) for v in quad))
            if ok:
                break
            ha, hb, ra, rb = ha * 0.75, hb * 0.75, ra * 0.8, rb * 0.8
        else:
            continue
        out.append({'id': f'platform:scree{len(out) + 1}', 'outline': [ipt(v) for v in quad], 'base': 0,
                    'rise': min(hs), 'top_heights': hs, 'surface': BASALT, 'top_surface': dict(CRUST, uneven=True),
                    'notes': "Scree at the cliff's foot (D-58 P-4)." if not out else None})
    for e in out:
        if e['notes'] is None:
            e.pop('notes')
    return out


# ------------------------------------------------------------------------------------------------ the batter (s28)
# the tiers' rock (s28, G3 review row 57): the textures the cliffs already use, at a finer scale than the walls
FOOT_SIDE = {'texture': 'vlcwl3a', 'size': [128, 256], 'scale': 2}
TIER_STRATA = {'texture': 'gcav2wal', 'size': [128, 256], 'scale': 2}
TIER_GRANITE = {'texture': 'vlcwl3a', 'size': [128, 256], 'scale': 3}
TIER_CLIFF = {'texture': 'vlcwl1', 'size': [128, 256], 'scale': 2}
RIB = {'texture': 'vlcwl2', 'size': [128, 256], 'scale': 2}


def convex_ccw(pts):
    """True when the polygon turns left at every corner (a convex outline, counter-clockwise)."""
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) <= 0:
            return False
    return True


def wall_surface(k):
    for w in wall_surfaces():
        if w['wall'] == k:
            return w['surface']['texture']
    return CLIFF['texture']


def fan_steep(pts, hs):
    """How steep a top is as the studio measures it: the triangles fanned from its first corner."""
    return max(tri_rise((pts[0][0], pts[0][1], hs[0]), (pts[i][0], pts[i][1], hs[i]),
                        (pts[i + 1][0], pts[i + 1][1], hs[i + 1])) for i in range(1, len(pts) - 1))


def wall_cap(p):
    """The lowest sky point near p over the lava (the rim's points within 900, else within 1,400)."""
    near = [q[2] for q in SKYPTS[:SKY_RIM] if math.hypot(q[0] - p[0], q[1] - p[1]) < 900]
    return (min(near) if near else local_top(p, 1400)) - LAVA


def batter():
    """The cliffs' batter (G3 review row 57: flat planes straight out of the lava read as cardboard): along every
    plain rim wall, pieces 420-760 long, each a stack of rock tiers rising toward the wall: a steep scree foot
    (sloping 1.15-1.5 from the lava to 300-640 up the wall), a ledge set back on it with an upright face and a top
    leaning back, often a third step higher and narrower; every piece its own depth, heights and front line (bent,
    the ends cut back), so no line runs on along a wall. Ribs (basalt columns) stand at some joints between pieces
    and climb most of the way up the cliff. All under the sky's lowest point near them (less 200), clear of every
    shelf, skirt, ramp, causeway, the falls' pools, the ledges, the way up and the playtests' spots."""
    rnd = random.Random(2828)
    out = []
    n = len(CRATER)
    poly = [tuple(p) for p in CRATER]
    plain = ('rim', 'tooth_flank', 'tooth_nose', 'notch')
    avoid = Clear([foot(e) for e in tiers() + fall_pools() + way_up_vent()])
    way_mouth = way_up_spot()[0]
    count = [0, 0]

    def place(local, a, u, nin):
        return [tuple(ipt((a[0] + u[0] * s + nin[0] * d, a[1] + u[1] * s + nin[1] * d))) for s, d in local]

    def fits(pts, front, clear_min):
        return (all(PG.point_in(v, poly) for v in pts)
                and not any(seg_cross(pts[i - 1], pts[i], poly) for i in range(len(pts)))
                and min(CLEAR.dist(v) for v in front) >= clear_min
                and min(avoid.dist(v) for v in pts) >= 48
                and not any(kept_clear(v, 150) for v in pts)
                and min(math.hypot(v[0] - way_mouth[0], v[1] - way_mouth[1]) for v in pts) > 760)

    def platform(pid, pts, hs, base, side, top, bottom=None):
        """The first two points stand at the wall, the rest at the front; the top is kept under 1.9 for each unit
        of run as the studio measures it (triangles fanned from the first corner)."""
        pts, hs = list(pts), list(hs)
        assert area2(pts) > 0
        if fan_steep(pts, hs) > 1.9:
            back, front = sum(hs[:2]) / 2, sum(hs[2:]) / (len(hs) - 2)
            hs = [back, back] + [front] * (len(hs) - 2)
            lo, hi = 0.0, 1.0
            for _ in range(20):
                f = (lo + hi) / 2
                if fan_steep(pts, [front + (back - front) * f] * 2 + hs[2:]) > 1.9:
                    hi = f
                else:
                    lo = f
            hs = [front + (back - front) * lo] * 2 + hs[2:]
        e = {'id': pid, 'outline': [ipt(v) for v in pts], 'base': int(round(base - LAVA)),
             'rise': int(round(min(hs) - base)), 'top_heights': [int(round(h - base)) for h in hs],
             'surface': side, 'top_surface': top}
        if bottom:
            e['bottom_surface'] = bottom
        return e

    for k in range(n):
        ka, kb = RIM_KIND[k], RIM_KIND[(k + 1) % n]
        if ka not in plain and kb not in plain:
            continue
        if ka in ('fall_back', 'way_back') or kb in ('fall_back', 'way_back'):
            continue
        a, b = CRATER[k], CRATER[(k + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        nin = (-u[1], u[0])
        s0 = 24 if ka in plain else 340                       # a gully's flank keeps its mouth open
        s1 = L - (24 if kb in plain else 340)
        if s1 - s0 < 300:
            continue
        own = wall_surface(k)
        m = max(1, int(round((s1 - s0) / rnd.uniform(460, 720))))
        cuts = [s0] + [s0 + (s1 - s0) * (j + rnd.uniform(-0.18, 0.18)) / m for j in range(1, m)] + [s1]
        built = []
        for j in range(m):
            p0, p1 = cuts[j] - (20 if j else 0), cuts[j + 1]
            W = p1 - p0
            mid_xy = (a[0] + u[0] * (p0 + p1) / 2 + nin[0] * 200, a[1] + u[1] * (p0 + p1) / 2 + nin[1] * 200)
            cap = wall_cap(mid_xy) - 220
            # the foot: scree from the lava up the wall
            hb = min(rnd.uniform(480, 900), cap * 0.5)     # S29: higher, to read from the arrival
            slope = rnd.uniform(1.15, 1.5)
            foot_pts = None
            # S29: each tier's back stands its own distance off the wall (a ledge 2, touching it, a rib 9, the feet
            # 16 and 23 in turn, as neighbours overlap at the joints, a step 30), so no two back faces share a plane
            fb = 16 if j % 2 == 0 else 23
            for _ in range(5):
                d1 = hb / slope
                cut0, cut1 = min(d1 * 0.45, W * 0.3), min(d1 * 0.45, W * 0.3)
                local = [(p0, fb), (p1, fb), (p1 - cut1 * rnd.uniform(0.8, 1.2), d1 * rnd.uniform(0.85, 0.98)),
                         (p0 + W * rnd.uniform(0.4, 0.6), d1 * rnd.uniform(1.02, 1.15)),
                         (p0 + cut0 * rnd.uniform(0.8, 1.2), d1 * rnd.uniform(0.85, 0.98))]
                pts = place(local, a, u, nin)
                if convex_ccw(pts if area2(pts) > 0 else pts[::-1]) and fits(pts, pts[2:], 160):
                    foot_pts = (local, pts)
                    break
                hb *= 0.8
            if not foot_pts:
                continue
            local, pts = foot_pts
            hf = [rnd.randint(8, 18) for _ in range(3)]
            hs = [LAVA + hb * rnd.uniform(0.9, 1.0), LAVA + hb * rnd.uniform(0.9, 1.0),
                  LAVA + hf[0], LAVA + hf[1], LAVA + hf[2]]
            count[0] += 1
            pk = count[0]
            tri = [(pts[0] + (hs[0],), pts[i] + (hs[i],), pts[i + 1] + (hs[i + 1],)) for i in range(1, 4)]
            if max(tri_rise(*t) for t in tri) > 1.8:
                hs[0] = hs[1] = LAVA + hb * 0.85
            out.append(platform(f'platform:batter{pk}', pts, hs, LAVA, FOOT_SIDE, dict(CRUST, uneven=True)))
            d1 = min(v[1] for v in local[2:])                  # the foot's shallowest front
            foot_at = lambda x: hb * max(0.0, 1 - x / d1) + 18  # (over the lava) the scree's height x from the wall
            # the ledge: an upright face rising out of the scree, its top leaning back to the wall
            d2 = d1 * rnd.uniform(0.42, 0.58)
            e0, e1 = rnd.uniform(40, 150), rnd.uniform(40, 150)
            if W - e0 - e1 < 200:
                built.append(pk)
                continue
            h2f = foot_at(d2) + rnd.uniform(300, 600)
            h2b = h2f + rnd.uniform(60, 220)
            if h2b > cap:
                h2f, h2b = cap - 120, cap
            if h2f < foot_at(d2) + 160:
                built.append(pk)
                continue
            f0, f1 = rnd.uniform(30, 100), rnd.uniform(30, 100)
            loc2 = [(p0 + e0, 2), (p1 - e1, 2), (p1 - e1 - f1, d2 * rnd.uniform(0.88, 1.0)),
                    (p0 + e0 + (W - e0 - e1) * rnd.uniform(0.35, 0.65), d2 * rnd.uniform(1.04, 1.14)),
                    (p0 + e0 + f0, d2 * rnd.uniform(0.88, 1.0))]
            pts2 = place(loc2, a, u, nin)
            if not convex_ccw(pts2 if area2(pts2) > 0 else pts2[::-1]) or not fits(pts2, pts2[2:], 160):
                built.append(pk)
                continue
            side2 = TIER_GRANITE if own == 'gcav2wal' else TIER_STRATA
            hs2 = [LAVA + h2b - rnd.uniform(0, 30), LAVA + h2b - rnd.uniform(0, 30),
                   LAVA + h2f - rnd.uniform(0, 12), LAVA + h2f, LAVA + h2f - rnd.uniform(0, 12)]
            out.append(platform(f'platform:batter{pk}_ledge', pts2, hs2, LAVA, side2,   # S29: from the lava, as a rib
                                dict(BASALT, uneven=True), bottom=side2))
            # the step: higher and narrower again, two pieces in three
            if rnd.random() < 0.67:
                d3 = d2 * rnd.uniform(0.42, 0.62)
                g0, g1 = e0 + rnd.uniform(40, 160), e1 + rnd.uniform(40, 160)
                top2 = lambda x: h2b + (h2f - h2b) * x / d2
                h3f = top2(d3) + rnd.uniform(260, 520)
                h3b = h3f + rnd.uniform(60, 240)
                if W - g0 - g1 >= 160 and h3b <= cap and d3 >= 90:
                    loc3 = [(p0 + g0, 30), (p1 - g1, 30), (p1 - g1 - rnd.uniform(20, 70), d3 * rnd.uniform(0.9, 1.0)),
                            (p0 + g0 + rnd.uniform(20, 70), d3 * rnd.uniform(0.9, 1.0))]
                    pts3 = place(loc3, a, u, nin)
                    if fits(pts3, pts3[2:], 160):
                        side3 = TIER_CLIFF if own != 'vlcwl1' else TIER_STRATA
                        hs3 = [LAVA + h3b, LAVA + h3b - rnd.uniform(0, 40), LAVA + h3f,
                               LAVA + h3f - rnd.uniform(0, 12)]
                        out.append(platform(f'platform:batter{pk}_step', pts3, hs3, LAVA, side3,
                                            dict(CRUST, uneven=True), bottom=side3))
            built.append(pk)
        # ribs: basalt columns at some joints between pieces, climbing most of the way up the cliff
        for j in range(1, m):
            if rnd.random() > 0.55:
                continue
            c = cuts[j]
            w, dr = rnd.uniform(150, 250), rnd.uniform(150, 230)
            if c - w / 2 < s0 + 40 or c + w / 2 > s1 - 40:
                continue
            locr = [(c - w / 2, 9), (c + w / 2, 9), (c + w * 0.28, dr * rnd.uniform(0.78, 0.9)),
                    (c + w * rnd.uniform(-0.1, 0.1), dr), (c - w * 0.3, dr * rnd.uniform(0.78, 0.9))]
            ptsr = place(locr, a, u, nin)
            mid_xy = (a[0] + u[0] * c + nin[0] * 120, a[1] + u[1] * c + nin[1] * 120)
            cap = wall_cap(mid_xy) - 200
            hw = cap - rnd.uniform(0, 260)
            hn = hw - dr * rnd.uniform(1.3, 1.7)
            if hn < 700 or not convex_ccw(ptsr if area2(ptsr) > 0 else ptsr[::-1]) or not fits(ptsr, ptsr[2:], 200):
                continue
            count[1] += 1
            hsr = [LAVA + hw, LAVA + hw - rnd.uniform(0, 50), LAVA + hn + rnd.uniform(0, 10), LAVA + hn,
                   LAVA + hn + rnd.uniform(0, 10)]
            out.append(platform(f'platform:rib{count[1]}', ptsr, hsr, LAVA, RIB, dict(BASALT, uneven=True)))
    out[0]['notes'] = ("The cliffs' batter (s28, G3 review row 57): scree, a ledge and a step rising toward each rim "
                       "wall, every piece its own depth, heights and front line; ribs of basalt columns at joints.")
    return out


# ------------------------------------------------------------------------------------------------ falls, the way up
def recess(kind):
    """The back corners of each gully of the kind (fall_back, way_back): pairs of rim indices."""
    n = len(CRATER)
    return [(k, (k + 1) % n) for k in range(n) if RIM_KIND[k] == RIM_KIND[(k + 1) % n] == kind]


def fall_pools():
    """At each fall's foot a glowing pool (bright molten rock, burning) filling the gully's mouth, ringed by crust
    boulders."""
    rnd = random.Random(31)
    out = []
    n = len(CRATER)
    for j, (k1, k2) in enumerate(recess('fall_back')):
        ba, bb = CRATER[k1], CRATER[k2]
        ma, mb = CRATER[k1 - 1], CRATER[(k2 + 1) % n]           # the gully's mouth corners
        mm = ((ma[0] + mb[0]) / 2, (ma[1] + mb[1]) / 2)
        w = math.hypot(mb[0] - ma[0], mb[1] - ma[1])
        u = ((mb[0] - ma[0]) / w, (mb[1] - ma[1]) / w)
        nin = (-u[1], u[0])
        rad = min(w / 2 - 24, CLEAR.dist(mm) - 120)
        cent = lambda p: (p[0] + (mm[0] - p[0]) * 0.06 + nin[0] * 20, p[1] + (mm[1] - p[1]) * 0.06 + nin[1] * 20)
        pts = [cent(ba), cent(bb)]
        for s in range(0, 9):
            t = math.pi * s / 8
            x, y = rad * math.cos(t), rad * math.sin(t)
            pts.append((mm[0] + x * u[0] + y * nin[0], mm[1] + x * u[1] + y * nin[1]))
        pts = ccw(pts)
        out.append({'id': f'platform:fall{j + 1}_pool', 'outline': [ipt(p) for p in pts], 'base': 0, 'rise': 10,
                    'surface': BASALT, 'top_surface': GLOW,
                    'notes': "A lava fall's glowing pool (burning: objects.yml floors)." if j == 0 else None})
        for s in range(5):
            t = math.pi * (0.1 + 0.8 * s / 4) + rnd.uniform(-0.12, 0.12)
            r = rad + rnd.uniform(40, 110)
            c = (mm[0] + r * math.cos(t) * u[0] + r * math.sin(t) * nin[0],
                 mm[1] + r * math.cos(t) * u[1] + r * math.sin(t) * nin[1])
            if CLEAR.dist(c) < 200 or kept_clear(c, 200):
                continue
            rr = rnd.uniform(60, 110)
            poly = ccw(ring(c[0], c[1], rr, 6, rnd.uniform(0, 1)))
            h0 = rnd.uniform(70, 150)
            hs = [int(h0 + rnd.uniform(-0.4, 0.4) * rr) for _ in poly]
            out.append({'id': f'platform:fall{j + 1}_rock{s + 1}', 'outline': [ipt(p) for p in poly], 'base': 0,
                        'rise': min(hs), 'top_heights': hs, 'surface': BASALT, 'top_surface': CRUST})
    for e in out:
        if e.get('notes') is None:
            e.pop('notes', None)
    return out


def way_up_exit():
    """D7 live (A6 s16): the way up as an exit object (the `exit` preset needs one) on the gully's back wall, its molten
    sheet the panel's surface, to D7's entrance:p1_return (project neighbour exit:d7_way_up)."""
    (k1, k2), = recess('way_back')
    a, b = CRATER[k1], CRATER[k2]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    return [{'id': 'exit:way_up', 'room': 'room:crater', 'at': ipt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)),
             'size': [int(L - 48), 900], 'surface': {'texture': 'orfyrlga', 'size': [256, 256]},
             'to': 'exit:d7_way_up',
             'notes': "The heat column's fissure past the Cinder Shelf (D-58 C5): the game's leave window, then D7."}]


def way_up():
    """The heat column's fissure past the Cinder Shelf's corner: a molten sheet on the gully's back wall (the way up's
    source; S's shimmer over it is blocked)."""
    if D7_LIVE:     # the exit panel on the gully's back wall is the molten sheet itself (way_up_exit)
        return []
    (k1, k2), = recess('way_back')
    a, b = CRATER[k1], CRATER[k2]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nin = (-u[1], u[0])
    c = ((a[0] + b[0]) / 2 + nin[0] * 12, (a[1] + b[1]) / 2 + nin[1] * 12)
    return [block('platform:way_up', c, (16, L - 48), LAVA, 900, MOLTEN, BASALT,
                  facing=math.degrees(math.atan2(nin[1], nin[0])),
                  notes="The heat column's fissure in the cliff past the Cinder Shelf's corner (exit:way_up; S's "
                        "shimmer effect over it is blocked).")]


VENT_R, VENT_OFF, VENT_TOP = 160, 172, 24      # the way up's vent: radius, centre off the back wall, top (absolute)


def vent_frame():
    """The way up's gully: the back wall's middle, along the wall, into the crater; the mouth's corners."""
    (k1, k2), = recess('way_back')
    a, b = CRATER[k1], CRATER[k2]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nin = (-u[1], u[0])
    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return m, u, nin, CRATER[k1 - 1], CRATER[(k2 + 1) % len(CRATER)]


def vent_centre():
    m, u, nin, _, _ = vent_frame()
    return (m[0] + nin[0] * VENT_OFF, m[1] + nin[1] * VENT_OFF)


def way_up_vent():
    """s28 (G3 review row 34: the heat column is invisible against the molten sheet): the way up made findable. A vent
    at the column's foot, a disc of molten rock (burning, objects.yml floors) in a lip of black glass open to the wall,
    the column rising from it; two obsidian shards flank the fissure's mouth, seen across the crater; a pulsing warm
    light over the vent (lights). The exit panel on the back wall and S's column are where they were."""
    rnd = random.Random(3434)
    m, u, nin, ma, mb = vent_frame()
    poly = [tuple(p) for p in CRATER]
    c = (m[0] + nin[0] * VENT_OFF, m[1] + nin[1] * VENT_OFF)
    out = [prism('platform:way_up_vent', ring(c[0], c[1], VENT_R, 14, 0.1), LAVA, VENT_TOP - LAVA, BASALT, GLOW,
                 notes="The way up's vent (s28): molten rock welling at the heat column's foot (burning: floors), "
                       "ringed by a lip of black glass; the column rises from it.")]
    # the lip: the crater side of the ring, in stones of black glass, open toward the wall (the column)
    segs = 6
    span = math.radians(84)
    base_dir = math.atan2(nin[1], nin[0])
    for s in range(segs):
        t0 = base_dir - span + 2 * span * s / segs + math.radians(2)
        t1 = base_dir - span + 2 * span * (s + 1) / segs - math.radians(2)
        r0, r1 = VENT_R - 6, VENT_R + rnd.uniform(70, 100)
        pts = [(c[0] + r0 * math.cos(t0), c[1] + r0 * math.sin(t0)), (c[0] + r1 * math.cos(t0), c[1] + r1 * math.sin(t0)),
               (c[0] + r1 * math.cos(t1), c[1] + r1 * math.sin(t1)), (c[0] + r0 * math.cos(t1), c[1] + r0 * math.sin(t1))]
        pts = [tuple(ipt(p)) for p in pts]
        if not all(PG.point_in(p, poly) for p in pts):
            continue
        # S29: a low lip (16-32 over the disc), so the glowing disc shows from the shelves
        hs = [VENT_TOP + rnd.uniform(24, 32), VENT_TOP + rnd.uniform(16, 24), VENT_TOP + rnd.uniform(16, 24),
              VENT_TOP + rnd.uniform(24, 32)]
        if area2(pts) < 0:
            pts, hs = pts[::-1], hs[::-1]
        out.append({'id': f'platform:way_up_lip{s + 1}', 'outline': [list(p) for p in pts], 'base': 0,
                    'rise': int(min(hs) - LAVA), 'top_heights': [int(round(h - LAVA)) for h in hs],
                    'surface': GLASS, 'top_surface': dict(GLASS, uneven=True)})
    # the shards: tall black glass either side of the fissure's mouth (as the gate's), a mark across the crater
    cap = min(q[2] for q in SKYPTS[:SKY_RIM] if math.hypot(q[0] - m[0], q[1] - m[1]) < 1200) - 260
    for k, (corner, sgn) in enumerate(((ma, -1), (mb, 1))):
        for push in range(170, 520, 30):
            at = (corner[0] + nin[0] * push + u[0] * sgn * 70, corner[1] + nin[1] * push + u[1] * sgn * 70)
            e = block(f'platform:way_up_shard{k + 1}', at, (160, 144), LAVA, cap - 120 * k - LAVA, GLASS, GLASS,
                      top_size=[24, 32], end_surface=dict(BASALT, fit=False),
                      notes="Obsidian shards either side of the heat column's fissure (s28)." if k == 0 else None)
            if all(PG.point_in(v, poly) and poly_dist_outline(v, poly) > 24 for v in foot(e)):
                out.append(e)
                break
    return out




# ------------------------------------------------------------------------------------------------ rooms.yml
DAIS_AT = PLACE['exit:dais']['at']             # (-4864, 3904): the return dais in the Sleeper's Hall


def hall_platforms():
    """Session 20: the return dais as on P2-P4 (S's xeen_dais_fire over it), hidden until the Fire Sleeper wakes."""
    return [prism('platform:dais', ring(DAIS_AT[0], DAIS_AT[1], 224, 12), HALL_FLOOR, 8, GLASS, GLASS,
                  floor=HALL_FLOOR,
                  notes="The return dais (exit:dais): a disc of black glass, shown once the Fire Sleeper is awake "
                        "(qbit 111760).")]


def way_up_spot():
    """S's heat column at the foot of the molten sheet's middle, its flat back to the wall, facing out (on the lava)."""
    (k1, k2), = recess('way_back')
    a, b = CRATER[k1], CRATER[k2]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    nin = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)
    m = ((a[0] + b[0]) / 2 + nin[0] * 4, (a[1] + b[1]) / 2 + nin[1] * 4)
    return m, math.degrees(math.atan2(nin[1], nin[0])), LAVA


def pieces():
    """S's pieces (D-58 C7, session 20; level_generation/decorations/xeen_planes_claude/README.md)."""
    sl = PLACE['poi:sleeper']['at']
    tp = PLACE['poi:test']['at']
    decos = PC.decorations(
        'fire', 'room:crater',
        sleeper=(sl, COMPASS['se'], HALL_FLOOR), statue=(PLACE['poi:statue']['at'], COMPASS['se'], None),
        pedestal=((tp[0] + 208, tp[1]), 180, None), dais=(DAIS_AT, 0, None), way_up=way_up_spot(),
        extra=(PC.deco('font', 'room:crater', 'xeen_emberfont', PLACE['poi:font']['at'], 0, 96,
                       notes=("The Ember Font (S, row 4056; radius 90, solid) on the islet: a basalt font of liquid "
                              "fire; clicked, A3's planes.font (once a day, +20 Fire resistance until rest).")),
               PC.deco('camp', 'room:crater', 'xeen_firecamp', PLACE['poi:camp']['at'], 90, 0,
                       notes=("The fire-walker's burnt camp (S, row 4057; radius 0, walked over): bedroll, kettle, "
                              "dead fire; clicked, A3's planes.camp (the note). The find lies by the bedroll."))))
    for d in decos:
        if d['id'] in ('deco:sleeper', 'deco:dais'):
            d['room'] = 'room:hall'
    return decos


def hall_outline():
    x0, y0, x1, y1 = HALL_RECT
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def build_rooms():
    platforms = FIXED + tiers() + batter() + fall_pools() + way_up() + way_up_vent()   # s28: batter for talus
    east, south = notch_edges()
    crater = {
        'id': 'room:crater', 'space': 'zone:lava', 'name': 'The Plane of Fire', 'outline': CRATER, 'floor': LAVA,
        'steep_floor': True, 'ceiling': CEIL, 'ceiling_points': SKYPTS, 'theme': 'theme:crater',
        'walls': wall_surfaces(), 'platforms': platforms,
        'notes': ("The crater: one open-air room, its floor the lava lake (burning), its walls ragged cliffs to the "
                  f"sky, their tops {RIM_LOW:,}-{RIM_HIGH:,} over the lava (ceiling_points on every rim corner: the "
                  "walls end on that jagged line), spurs reaching into the lava, ledges, two lava falls in gullies; "
                  "shelves, causeways and the Crucible stand in the lava, their sides skirted with steep crust. A "
                  "notch in the north-west holds the Sleeper's Hall behind a wall, the gate framed in glass and "
                  "basalt."),
    }
    hall = {
        'id': 'room:hall', 'space': 'room:chamber', 'name': "The Sleeper's Hall", 'outline': hall_outline(),
        'floor': HALL_FLOOR, 'ceiling': HALL_CEIL, 'theme': 'theme:hall', 'platforms': hall_platforms(),
        'notes': ("The Sleeper's Hall, cut into the tallest spire, open to the sky: its own room behind the crater's "
                  "wall, reached only through the gate (P-2: walls to the sky on every side)."),
    }
    openings = [{'id': 'open:gate', 'from': 'room:crater', 'to': 'room:hall', 'from_wall': east, 'to_wall': 1,
                 'link': 'link:sleepers_gate', 'width': GATE_W, 'height': GATE_H,
                 'along': round((HALL_RECT[3] - GATE_Y) / (HALL_RECT[3] - HALL_RECT[1]), 4),
                 'reveal': HALL_WALL, 'notes': "The Sleeper's Gate: a hinged pair of black-glass leaves."}]
    return {'format': 0,
            'themes': [{'id': 'theme:crater', 'wall': CLIFF, 'floor': LAVA_FLOOR, 'ceiling': SKY},
                       {'id': 'theme:hall', 'wall': HALL_WALL, 'floor': HALL_FLOOR_S, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:crater', 'ambient': 30},
            'rooms': [crater, hall], 'openings': openings}


# ------------------------------------------------------------------------------------------------ objects.yml
MOVE_GROUP = {'pop:vents_golems': (-4224, -4096), 'pop:spires_golems': (3840, -256)}


def min_edge(poly, q):
    return PG.length(q, PG.nearest_on_poly(poly, q))


def spread(at, n, r=192):
    if n == 1:
        return [at]
    return [(at[0] + r * math.cos(2 * math.pi * k / n), at[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def objects():
    arr = PLACE['entrance:d7_fall']
    start = {'room': 'room:crater', 'at': ipt(arr['at']), 'floor_height': 0, 'facing': arr['face'],
             'notes': "entrance:d7_fall on the Cinder Shelf, facing north-west (Xeen.PlaneArrivals.fire)."}
    monsters = []
    for gi, g in enumerate(D['groups']):
        row = PD.ROWS[g['row']]
        z = PL.floor_at(g['at'])
        poly = shelf_outline(g['space'])
        pts = []
        centre = MOVE_GROUP.get(g['id'], g['at'])
        for p in spread(centre, g['count'], 320 if g['row'] == 'lava_golem' else 224):
            c = SPACE[g['space']]['at']
            for t in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
                q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
                if PG.point_in(q, poly) and PG.poly_distance(poly, q) == 0 and min_edge(poly, q) > 96:
                    break
            pts.append(q)
        for k, p in enumerate(pts):
            e = {'id': f"monster:{key(g['id'])}_{k + 1}", 'room': 'room:crater', 'monster': row['id'], 'at': ipt(p),
                 'floor_height': int(z), 'facing': 0, 'hostile': True, 'group': gi + 1}
            if k == 0:
                e['notes'] = f"{g['id']}: {g['count']} {row['short']} ({row['level']})."
            monsters.append(e)
    pit_z = SPACE['room:arena']['floor'] - 24
    k = 0
    for g in D['test_group']:
        row = PD.ROWS[g['row']]
        for j in range(g['count']):
            k += 1
            at = PIT_AT if k == 1 else (PIT_AT[0] + (k - 2.5) * 2 * 224, PIT_AT[1] + 192)
            monsters.append({'id': f'monster:guardian_{k}', 'room': 'room:crater', 'monster': row['id'],
                             'at': ipt(at), 'floor_height': pit_z, 'facing': 270, 'hostile': True,
                             'group': GUARD_GROUP, 'hidden': True,
                             'notes': (f"{row['short']} ({row['level']}): the test's hidden group {GUARD_GROUP} in "
                                       "the pit, shown by evt:test (D-58 C3).")})
    chests = [
        {'id': 'chest:test', 'room': 'room:hall', 'at': ipt(PLACE['poi:test_chest']['at']), 'kind': 'ch3',
         'facing': 's', 'treasure_level': 6, 'random_items': 3, 'gold': 2500,
         'notes': "The test's chest (aaze0025:5 'Chest'): the source's gold and three items, behind the gate."},
        {'id': 'chest:ember_cache', 'room': 'room:crater', 'at': ipt(PLACE['poi:ember_cache']['at']),
         'floor_height': 0, 'kind': 'ch1', 'facing': 'ne', 'treasure_level': 6, 'random_items': 2, 'gold': 1200,
         'trap_level': 8, 'notes': "The ember cache: the fire-walker's iron box by his burnt camp (trapped)."},
    ]
    cx, cy = PLACE['poi:camp']['at']
    items = [{'id': f'item:camp_potion{i + 1}', 'room': 'room:crater', 'item': 256, 'at': [cx + dx, cy + dy],
              'floor_height': 0, 'notes': "The camp's find: Fire Resistance (256)." if i == 0 else None}
             for i, (dx, dy) in enumerate(((96, 64), (160, 0)))]
    for it in items:
        if it['notes'] is None:
            it.pop('notes')
    door = {'id': 'door:sleeper', 'opening': 'open:gate', 'kind': 'hinged', 'leaves': 2, 'thickness': 16,
            'speed': 80, 'surface': GLASS_LEAF, 'back_surface': GLASS_LEAF,
            'notes': ("The Sleeper's Gate: two hinged leaves of black glass (xpfglass, once per leaf, the right "
                      "mirrored), swinging into the hall; shut until qbit 111764 (m38.test_fire_passed).")}
    return {
        'format': 1, 'start': start,
        # AU's plane bed (devdocs/xeen/AUDIO.md session 5, "The lines to paste"; D-48 `pan: false`)
        'sounds': [{'id': 'sound:plane_bed', 'room': 'room:crater', 'at': [-256, 0], 'height': 512, 'sound': 'xeen_amb_plane_fire', 'radius': 12000, 'inner_radius': 8000, 'volume': 0.4, 'pan': False}],
        'arrivals': [{'entrance': 'entrance:d7_fall', 'room': 'room:crater', 'at': ipt(arr['at']), 'floor_height': 0,
                      'facing': arr['face'], 'notes': "The drop from D7's north-west corner (Xeen.toPlane('fire'))."}],
        'doors': [door],
        'floors': [{'id': 'floor:lava', 'of': 'room:crater', 'kind': 'lava'},
                   {'id': 'floor:pit', 'of': 'platform:pit', 'kind': 'lava'}]
                  + [{'id': f"floor:{key(e['id'])}", 'of': e['id'], 'kind': 'lava'} for e in fall_pools()
                     if e['id'].endswith('_pool')]
                  + [{'id': 'floor:way_up_vent', 'of': 'platform:way_up_vent', 'kind': 'lava'}],
        'chests': chests, 'items': items, 'monsters': monsters, 'decorations': pieces(), 'lights': lights(),
        **({'exits': way_up_exit()} if D7_LIVE else {}),
        'notes': ("P1 L4 objects (generated by output/studio_cal/p1/tools/gen.py): 27 placed hostiles in 10 groups "
                  f"and the test's three in the hidden group {GUARD_GROUP}; two chests at treasure 6; the camp's "
                  "find; the gate; S's pieces (session 20): the sleeper on his couch, the statue on its own plinth, the "
                  "pedestal, the return dais (hidden until the sleeper wakes) and the heat column; S's Ember Font "
                  "and burnt camp (session 25) with the font's warm light."),
    }


def lights():
    """The Ember Font's glow (session 25): S's font has no decoration light; a warm pulsing light over its fire."""
    return [{'id': 'light:font', 'room': 'room:crater', 'at': list(PLACE['poi:font']['at']), 'floor_height': 96,
             'height': 200, 'radius': 800, 'color': [255, 120, 40],
             'pulse': {'intensity': [0.75, 1], 'radius': [720, 800], 'frequency': 0.6, 'phase': 0.2},
             'notes': "The Ember Font's glow: 200 over the islet, 93 over the font's shimmer (none of S's pieces "
                      "carries a light)."},
            {'id': 'light:way_up', 'room': 'room:crater', 'at': ipt(vent_centre()), 'floor_height': 0,
             'height': 280, 'radius': 1100, 'color': [255, 110, 30],
             'pulse': {'intensity': [0.7, 1], 'radius': [960, 1100], 'frequency': 0.45, 'phase': 0.6},
             'notes': "s28: the way up's vent glowing on the cliff and the Cinder Shelf, seen across the crater."}]


# ------------------------------------------------------------------------------------------------ wiring.yml
def wiring():
    ev = []
    ev.append({'id': 'evt:test', 'preset': 'script', 'trigger': 'step', 'source': 'platform:test_plate',
               'condition': {'all': [{'not': {'qbit': 'm38_fire_test'}}, {'not': {'map_var': 'test_accepted'}}]},
               'question': {'ask': 'Accept the test of Fire?', 'answers': ['Yes', 'Y']},
               'effects': [{'lua': 'XeenQuests.hook("m38.test_fire")'}, {'show_actors': GUARD_GROUP},
                           {'set': {'var': {'map_var': 'test_accepted'}, 'value': 1}}],
               'notes': ("D-58 C3: the test (aaze0025:6). Yes: A3's m38.test_fire line, the guardians rise (group "
                         f"{GUARD_GROUP} shown); any other answer does nothing. Not asked again while they live.")})
    ev.append({'id': 'evt:test_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'map_var': 'test_accepted'}, {'not': {'qbit': 'm38_fire_test'}}]},
               'lua': f'Xeen.planeTestCheck("fire", {GUARD_GROUP})',
               'notes': ("A3's killed-group check (xeen_common.lua): once the three guardians are dead it runs "
                         "m38.test_fire_passed, which sets qbit 111764 (P-1) with its line.")})
    ev.append({'id': 'evt:gate_open', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'qbit': 'm38_fire_test'}, {'not': {'map_var': 'gate_open'}}]},
               'opens': ['door:sleeper'], 'effects': [{'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': 'The gate opens the second the qbit is set (C4).'})
    ev.append({'id': 'evt:passed_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm38_fire_test'},
               'opens': ['door:sleeper'],
               'effects': [{'hide_actors': GUARD_GROUP}, {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': ("P-1: the load event reads qbit 111764: the gate open, the guardians hidden, the pit quiet "
                         "(through refills and the reset after a map rebuild).")})
    ev.append({'id': 'evt:gate', 'preset': 'script', 'source': 'door:sleeper', 'title': "The Sleeper's Gate",
               'condition': {'not': {'qbit': 'm38_fire_test'}},
               'effects': [{'text': 'The gate of black glass does not move.'}],
               'else_effects': [{'text': 'The gate stands open.'}],
               'notes': 'Clicked: the gate never moves by hand (it opens on the test).'})
    ev.append({'id': 'evt:vents', 'preset': 'script', 'trigger': 'step', 'source': 'platform:vent1',
               'sources': [f'platform:vent{i}' for i in range(2, 10)],
               'lua': 'XeenQuests.hook("planes.vent")',
               'notes': "D-58 P1 Q2: A3's planes.vent (one time in three, 50 fire to each member, 'A vent flares!')."})
    ev.append({'id': 'evt:spire', 'preset': 'script', 'source': 'platform:spire_seam',
               'title': 'A seam of red crystal', 'lua': 'XeenQuests.hook("planes.spire")',
               'notes': "A3's planes.spire: the first time a ruby (map variable p1_spire)."})
    ev.append({'id': 'evt:font', 'preset': 'script', 'source': 'deco:font', 'title': 'The Ember Font',
               'lua': 'XeenQuests.hook("planes.font")',
               'notes': ("A3's planes.font: once a day for the party (Xeen.usedToday), +20 Fire resistance until "
                         "rest, every member.")})
    ev.append({'id': 'evt:camp', 'preset': 'script', 'source': 'deco:camp', 'title': 'A burnt camp',
               'lua': 'XeenQuests.hook("planes.camp")',
               'notes': "A3's planes.camp: the fire-walker's note by the burnt bedroll."})
    ev.append({'id': 'evt:plaque', 'preset': 'script', 'source': 'deco:statue', 'title': 'Plaque',
               'lua': 'XeenQuests.hook("m38.plaque_fire")',
               'notes': ("A3's m38.plaque_fire: 'Step One' on the plaque of the statue's own black plinth (S's "
                         "decoration, radius 224, solid and clickable).")})
    ev.append(PC.sleeper_event('fire'))
    ev.append({'id': 'evt:dais_hide', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': 'm38_fire'}},
               'effects': [{'hide': 'platform:dais'}, {'passable': 'platform:dais'}],
               'notes': "C5: the return dais shows once the Fire Sleeper is awake (qbit 111760, m38.sleeper_fire)."})
    ev += PC.dais_events('fire', 'm38_fire')
    ev.append({'id': 'evt:chest_test', 'preset': 'chest', 'source': 'chest:test', 'title': 'Chest',
               'notes': "The test's chest (aaze0025:5)."})
    ev.append({'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:ember_cache', 'title': 'Chest',
               'notes': 'The ember cache (trapped).'})
    if D7_LIVE:
        # session 18: the `exit` preset moved at once (no leave window between two BLVs), so the question never
        # showed; A3's m38.way_up_fire question asked first, as P2-P4's ways up
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'exit:way_up', 'title': 'The heat column',
                   'effects': [{'lua': PC.d7_return_lua('fire')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': "D-58 C5: the way up to D7's entrance:p1_return; A3's m38.way_up_fire is its question."})
        ev.append(PC.copy_for(ev[-1], 'way_up', 'evt:way_up_column'))
        dais = {'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': 'The return dais',
                'condition': {'qbit': 'm38_fire'}, 'locked_text': 'The dais is dark and still.',
                'effects': [{'lua': PC.d7_return_lua('fire')}],   # s32 (F16): the entrance window, no Yes/No
                'notes': "D-58 C5: the dais after the sleeper, to D7's entrance:p1_return (A3's m38.dais_fire)."}
        ev += [dais, PC.copy_for(dais, 'dais', 'evt:dais_disc')]
    else:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The heat column',
                   'effects': [{'text': 'The heat rises past you into the smoke. (The Skyroads are not open yet.)'}],
                   'notes': ("D-58 C5's way up, sealed until xeen_d7.blv is installed and lists entrance:p1_return "
                             "(then the `exit` preset, A3's m38.way_up_fire).")})
    return {'format': 0, 'variables': ['test_accepted', 'gate_open', 'dais_shown'], 'events': ev}


# ------------------------------------------------------------------------------------------------ plan, project
def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan(level):
    p = load('L1', 'plan.yml')
    p['level'] = level
    for l in p['links']:
        if l['id'] == 'link:sleepers_gate':
            l['kind'] = 'door'
            l['notes'] = ("an obsidian bridge over the lava from the Crucible's west rim to the Sleeper's Gate, a hinged "
                          "pair of black-glass leaves in the Sleeper's Hall's wall; the gate opens on qbit 111764")
    p['notes'] = (p['notes'] + " L2-L4 (A6's planes sub-agent, sixteenth session, 2026-11-21): built by "
                  "output/studio_cal/p1/tools/gen.py; the Sleeper's Hall is its own open-air room behind the crater's "
                  "wall, the gate a hinged pair in that wall (P-2 by construction); the lava at -40 (L1 -64: the "
                  "floor-0 shelves step out of it); S's pieces blocked by name.")
    return p


def project(level):
    p = load('L1', 'project.yml')
    for n in p['neighbours']:
        if n['id'] in ('exit:d7_way_up', 'exit:d7_dais') and not D7_LIVE:
            n.pop('arrival', None)
            n.pop('arrival_hint', None)
            n['notes'] = n['notes'] + " Sealed until xeen_d7.blv is installed and names entrance:p1_return."
    p['new'] = False     # the arrival's word is D7's corner ('You step off.'), m38.corner_fire
    p['notes'] = (f"Xeen design brief, level {level}: P1 Plane of Fire of Xeen, an open-air BLV (devdocs/"
                  "INDOOR_OPEN_SKY.md; X9's and P5's route) built with the studio (profile region): the crater room "
                  "(lava floor, ragged cliffs, open sky plane_fire) and the Sleeper's Hall behind its gate. map_stats "
                  "9115 (A2's row, landed 2026-11-21), music 10, treasure 6; Fire rows 11620-11623 and Lava Golem "
                  "11593; hooks: A3's m38.*_fire, planes.vent, planes.spire, planes.font, planes.camp, Xeen.planeTestCheck.")
    return p


def atmosphere():
    a = load('L1', 'atmosphere.yml')
    a['notes'] = a['notes'] + " L4: as L1 (D-58 Q3)."
    return a


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    with open(BRIEF / level / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


# ------------------------------------------------------------------------------------------------ the crater, built
APRONS = shelf_aprons() + causeway_aprons()
FIXED = shelves() + ramps() + causeways() + bridge() + crucible() + vents() + spires() + APRONS + gate_frame()
CLEAR = Clear([foot(e) for e in FIXED])
_RIM = crater_rim()
CRATER = [e['xy'] for e in _RIM]
CRATER_H = [e['h'] for e in _RIM]
RIM_KIND = [e['kind'] for e in _RIM]
SKYPTS, SKY_RIM = ceiling_points()


if __name__ == '__main__':
    rooms = build_rooms()
    objs = objects()
    for level in ('L2', 'L3', 'L4'):
        write(level, 'plan.yml', plan(level if level != 'L4' else 'L3'))
        write(level, 'project.yml', project(level))
    for level in ('L3', 'L4'):
        write(level, 'rooms.yml', rooms)
        write(level, 'atmosphere.yml', atmosphere())
    write('L3', 'objects.yml', {'format': 1, 'start': objs['start']})
    write('L4', 'objects.yml', objs)
    write('L4', 'wiring.yml', wiring())
    ps = rooms['rooms'][0]['platforms']
    print('crater points', len(CRATER), 'platforms', len(ps), 'monsters', len(objs['monsters']), 'D7 live', D7_LIVE)
