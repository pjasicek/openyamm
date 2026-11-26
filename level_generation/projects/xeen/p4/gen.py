#!/usr/bin/env python3
"""P4 Plane of Water of Xeen: writes L2, L3 and L4 (A6's planes sub-agent, seventeenth session, 2026-11-21), after
P2's gen.py (level_generation/projects/xeen/p2/, its helpers copied, nothing of theirs edited).

The plan is L1's (planes_design.py with D-58 applied); this file turns it into the studio's rooms, objects and wiring:

- room:sea, one open-air room from the sea bed (FLOOR) to the sky (CEIL): its walls and ceiling sky faces
  (xeen_plane_water draws), its floor the dark rock of the bed;
- the sea: MM9 water volumes (objects.yml `water`): the inner sea with no current and four edge bands past the ring of
  sea stacks, each with a constant inward current of 256 (D-58); the surface the party sees is one untouchable
  7wtrtyl face at -64 over the whole room (the party sinks in and swims);
- each terrace and court a drowned temple floor standing out of the sea: its L1 outline with a ragged rim (marble
  sides, flagstone top), on a wider foot of rough rock under the water; broken wall stubs and fallen drums on the rims
  off every walking line;
- the colonnade walks as marble slabs from the bed, broken columns along both edges; steps down into the sea at the
  middle of every walk and at one rim of every terrace (none at the Whirlpool Court or the Grotto, D-58 P-2);
- the Whirlpool Court: a ring of broken columns round the whirlpool (a 7wtrtyl disc where the guardians rise) and a
  ring of mosaic slabs (gtemprf, once per face); the test's floor at the east gate;
- the Veil: a falling sheet of water (a translucent xcwisp platform, flowing down, solid) across the head of the
  colonnade to the Grotto, between two broken wall stubs 384 over the court; qbit 111767 makes it passable and hides
  it (P2's curtain);
- the Sleeper's Grotto: a raised shelf under a sea arch (two rock piers and a hanging span), the return dais (shown on
  m38.water, 111763);
- the Wreck: a ship's hull of MM8's ship planks (bwoodb1) across the south court, its hold half flooded (a water
  volume 40 deep, waded) through a breach with a sill, a raised stern deck with the ship's log, two broken masts;
- the Sea Statue's fountain (a curb, its water, the plinth with the plaque), the Drowned Bell's fallen frame, the Tide
  Pool in the coral, the waterspout (a translucent column flowing up) at the Spray Terrace;
- a ring of sea stacks with three broken arches near the room's edge, open sea and fog beyond;
- nine wave plates (xpwspray, A3's planes.wave), none on the critical path.

S's pieces (the statue of Water, the sleeper and couch, the test's pedestal, the bell) are spots by name, blocked (C7:
no stand-ins).

    python3 level_generation/projects/xeen/p4/gen.py      # writes devdocs/xeen/briefs/p4/L2, L3, L4
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
import spans as SP  # noqa: E402

BRIEF = ROOT / 'devdocs/xeen/briefs/p4'
WORLD = ROOT / 'assets_dev/worlds/xeen'
PL = PG.Plane('p4')
D = PL.d
SPACE = PL.space
PLACE = PL.place

FLOOR = -1024          # the sea bed (L1: bottom about -1,024)
WATER = -64            # the sea's surface (L1)
CEIL = 4096
HALF = PL.half[0]      # 6656
BAND = 1024            # the edge bands' width (current 256 inward)
CURRENT = 256
UPPER = -320           # the marble body's foot; the rough rock foot below it (a ledge under the swimmers' feet)
STEP_LOW = -288        # the lowest step of a flight out of the water
TEST_QBIT = PD.TEST_QBITS['water']                      # 111767
SLEEPER_QBIT = PD.SLEEPER_QBITS['water']                # 111763
GUARD_GROUP = 60

# ------------------------------------------------------------------------------------------------ textures
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}           # sky faces (the preset draws)
BED = {'texture': 'gwspinwl', 'size': [256, 256], 'scale': 4}        # MM8 Plane of Air's darker rock: the sea bed
FLAGS = {'texture': 'gtempflr', 'size': [128, 128], 'scale': 2}      # MM8 temple flagstones: terraces, walks
MARBLE = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 2}      # MM8 temple marble: the temple's walls
MOSAIC = {'texture': 'gtemprf', 'size': [128, 128], 'fit': True}     # MM8 gold-blue mosaic, once per face
ROCK = {'texture': 'gwspotwl', 'size': [256, 256], 'scale': 2}       # MM8 Plane of Air's blue-grey rough rock
ROCK_DARK = {'texture': 'gwspinwl', 'size': [256, 256], 'scale': 2}
BRICK = {'texture': 'cdb', 'size': [128, 256], 'scale': 2}           # MM8 Plane of Air's brick: the wreck court
PLANKS = {'texture': 'bwoodb1', 'size': [256, 256], 'scale': 2}      # MM8 elemw's ship planks: the hull (xpwhull)
DECK = {'texture': 'bmplnk', 'size': [256, 256], 'scale': 2}         # MM6 plank floor: the stern deck
MAST = {'texture': 'bwooda1', 'size': [256, 256], 'scale': 1}        # MM8 upright planks: masts, frame
SEA = {'texture': '7wtrtyl', 'liquid': 'water'}                      # MM7 water (the liquid shader)
CORAL = {'texture': 'xpwcoral', 'size': [128, 128], 'scale': 2}      # new (xtex.py, map_textures/p4), seamless
SPRAY = {'texture': 'xpwspray', 'size': [128, 128], 'fit': True}  # s33: the picture's own size (128)     # new, once per wave plate
VEIL = {'texture': 'xcwisp', 'size': [256, 256], 'scale': 2, 'flow': 'down',
        'translucent': {'opacity': 0.72, 'tint': [0.55, 0.95, 1.05], 'two_sided': False}}
SPOUT = {'texture': 'xcwisp', 'size': [256, 256], 'scale': 2, 'flow': 'up',
         'translucent': {'opacity': 0.7, 'tint': [0.55, 0.98, 1.0], 'two_sided': False}}
TINT = [0.35, 0.78, 0.74]                                            # the view under the sea-green water
# the fog under the water (merge point 29; A1's values): deep teal, the far side of the sea lost at 1,500
FOG = {'color_rgb': [20, 70, 80], 'near_distance': 64, 'far_distance': 1500, 'sky': 1}


def live_d7():
    if os.environ.get('P4_D7_LIVE') == '1':
        return True
    studio = WORLD / 'maps/xeen_d7.studio.yml'
    return (WORLD / 'maps/xeen_d7.blv').exists() and studio.exists() and 'entrance:p4_return' in studio.read_text()


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
    """A rectangular block whose foot stands at absolute z."""
    e = {'id': pid, 'at': ipt(at), 'size': [int(round(size[0])), int(round(size[1]))],
         'base': int(round(z - FLOOR)), 'rise': int(round(rise)), 'surface': surface}
    if top:
        e['top_surface'] = top
    if facing is not None:
        e['facing'] = round(facing, 4)
    if top_size:
        e['top_size'] = [int(top_size[0]), int(top_size[1])]
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def prism(pid, outline, z, rise, surface, top=None, notes=None, **kw):
    e = {'id': pid, 'outline': [ipt(p) for p in ccw(list(outline))], 'base': int(round(z - FLOOR)),
         'rise': int(round(rise)), 'surface': surface, 'top_surface': top or surface}
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def slab(pid, a, b, z0, z1, width, surface, top, thickness, bottom=None, notes=None, **kw):
    """A slab from a (top z0) to b (top z1), `width` wide, `thickness` under its lower top (P2's)."""
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    facing = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    low = min(z0, z1) - thickness
    e = {'id': pid, 'at': ipt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)), 'size': [int(round(length)), int(width)],
         'facing': round(facing, 2), 'base': int(round(low - FLOOR)), 'rise': int(round(min(z0, z1) - low)),
         'surface': surface, 'top_surface': top, 'bottom_surface': bottom or surface}
    if int(round(z0)) != int(round(z1)):
        e['top_heights'] = [int(round(z0 - low)), int(round(z1 - low)), int(round(z1 - low)), int(round(z0 - low))]
        e['thickness'] = int(thickness)
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def seg_dist(q, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / l2))
    return math.hypot(q[0] - a[0] - t * dx, q[1] - a[1] - t * dy)


def poly_dist_outline(q, poly):
    return min(seg_dist(q, poly[i - 1], poly[i]) for i in range(len(poly)))


def inside_by(q, poly, margin):
    return PG.point_in(q, poly) and poly_dist_outline(q, poly) >= margin


def rect(at, size, facing):
    cx, cy = at
    L, W = size
    f = math.radians(facing)
    ux, uy, vx, vy = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    return [(cx + sx * L / 2 * ux + sy * W / 2 * vx, cy + sx * L / 2 * uy + sy * W / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def foot(e):
    """A platform's footprint: its outline, or its block's rectangle turned by `facing`."""
    if 'outline' in e:
        return [tuple(p) for p in e['outline']]
    size = e['size']
    if e.get('top_size') and e['top_size'][0] > size[0]:
        size = e['top_size']
    return rect(e['at'], size, e.get('facing', 0))


# directions whose sines and cosines are whole-number ratios (Pythagorean triples): a tapered block turned to one of
# them, with its sizes multiples of twice the triple's long side, keeps whole-unit corners and flat leaning faces (P1)
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


# ------------------------------------------------------------------------------------------------ the walk's keep-outs
SPACES = [s['id'] for s in D['spaces']]
FLOOR_OF = {s['id']: s['floor'] for s in D['spaces']}
NO_STEPS = ('room:arena', 'room:chamber')     # L1, D-58 P-2: no steps out of the water at the court or the Grotto
OBSTACLES = set()                             # platform ids monsters, plates and props keep out of


def walk_lines():
    """Lines a party walks (L1's walk and every colonnade) with their half widths."""
    out = [(a, b, 192) for a, b, _, _ in PL.walk_segments()[0]]
    for l in D['links']:
        p, q = PL.link_ends(l)
        out.append((p, q, l['width'] / 2 + 64))
    return out


def near_walk(q, pad):
    return any(seg_dist(q, a, b) < hw + pad for a, b, hw in WALK)


KEEP = []        # (point, radius): places, groups, plates, link ends: no stub or prop within


def kept(q, pad=0):
    return any(math.hypot(q[0] - c[0], q[1] - c[1]) < r + pad for c, r in KEEP)


# ------------------------------------------------------------------------------------------------ outlines
def link_ends_of(sid):
    pts = []
    for l in D['links']:
        p, q = PL.link_ends(l)
        if l['a'] == sid:
            pts.append(p)
        if l['b'] == sid:
            pts.append(q)
    return pts


def rough_outline(sid, scale=1.0, seed=0, points=24, out_amp=(0, 150), hold=560):
    """The space's L1 outline (blob) with a ragged rim: each point pushed out by its own amount (never where a walk
    lands), scaled about the middle (P2's)."""
    s = SPACE[sid]
    base = PG.blob(s, points=points)
    cx, cy = s['at']
    rnd = random.Random(1000 * s['seed'] + seed)
    holds = link_ends_of(sid)
    out = []
    for i, (x, y) in enumerate(base):
        dx, dy = x - cx, y - cy
        r = math.hypot(dx, dy)
        push = rnd.uniform(*out_amp) * (1 if i % 2 else 0.45)
        if any(math.hypot(x - h[0], y - h[1]) < hold for h in holds):
            push = 0
        k = scale * (r + push) / r
        out.append((cx + dx * k, cy + dy * k))
    return [ipt(p) for p in ccw(out)]


# ------------------------------------------------------------------------------------------------ terraces
def terrace(sid):
    """The temple floor standing out of the sea: marble sides, a flagstone (or coral) top, on a rough rock foot under
    the water (its top a ledge below a swimmer's feet)."""
    s = SPACE[sid]
    fl = s['floor']
    top = CORAL if sid == 'room:reef' else FLAGS
    out = [prism(f'platform:{key(sid)}', TOPS[sid], UPPER, fl - UPPER, MARBLE, top, bottom_surface=ROCK,
                 notes=f"{s['name']}: {s['shape']} (floor {fl}); marble out of the sea, a ragged rim.")]
    footline = rough_outline(sid, 1.0, seed=7, points=20, out_amp=(60, 220), hold=0)
    out.append(prism(f'platform:{key(sid)}_foot', footline, FLOOR, UPPER + 8 - FLOOR, ROCK, ROCK_DARK,
                     notes=("The terrace's foot: rough rock under the water, its top 248 under the surface (below "
                            "a swimmer's feet).") if sid == SPACES[0] else None))
    return out


def stubs(sid):
    """Broken wall stubs and fallen drums standing on the rim, off every walking line, place and plate."""
    s = SPACE[sid]
    if sid == 'room:chamber':
        return []
    poly = TOPS[sid]
    rnd = random.Random(77 * s['seed'])
    side, top = {'room:wreck': (BRICK, FLAGS), 'room:reef': (ROCK, CORAL)}.get(sid, (MARBLE, FLAGS))
    out = []
    cand = PG.outline_samples([tuple(p) for p in poly], 300)
    rnd.shuffle(cand)
    for (p, n) in cand:
        if len(out) >= 6:
            break
        at = (p[0] - n[0] * 70, p[1] - n[1] * 70)
        if near_walk(at, 260) or kept(at, 240) or any(math.hypot(at[0] - c['at'][0], at[1] - c['at'][1]) < 560
                                                      for c in out):
            continue
        fac, q = snap_facing(math.degrees(math.atan2(n[1], n[0])) + 90 + rnd.uniform(-15, 15))
        w, d = mult(rnd.uniform(220, 420), q), mult(rnd.uniform(100, 170), q)
        h = rnd.uniform(110, 380) if sid != 'room:reef' else rnd.uniform(70, 200)
        pid = f'platform:{key(sid)}_stub{len(out) + 1}'
        out.append(block(pid, at, (w, d), s['floor'] - 40, h + 40, side, top, facing=fac,
                         top_size=[mult(w * 0.8, q), mult(d * 0.75, q)],
                         notes=("Broken wall stubs on the rim (the look: no flat slab), off the walking lines."
                                if not out and sid == SPACES[0] else None)))
        OBSTACLES.add(pid)
    return out


# ------------------------------------------------------------------------------------------------ the colonnades
INTO = 192
SINK = 4               # the test's plate, the dais: sunk into the top they lie on (X8's, F62: no lid)


def link_cut(l):
    p, q = PL.link_ends(l)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * INTO, p[1] - uy * INTO), (q[0] + ux * INTO, q[1] + uy * INTO), d


def link_spans(l):
    """F62 (2026-11-25): the walk level across each terrace until past its rim, sloping between (SP.link_spans; it
    sloped straight from inside one to inside the other and rose through the lower one's top or dipped under the
    higher one's: check_floor_cross floor.cross)."""
    a, b, _ = link_cut(l)
    return SP.link_spans(a, b, FLOOR_OF[l['a']] + 4, FLOOR_OF[l['b']] + 4, l['width'],
                         [tuple(v) for v in TOPS[l['a']]], [tuple(v) for v in TOPS[l['b']]])


def walk_z(l, t):
    """The walk's top at t along the rim-to-rim line (link_ends)."""
    p, q = PL.link_ends(l)
    return slab_z(l, (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))


def slab_z(l, pt):
    """The walk slab's top at pt (the slabs run from link_cut's a to b, link_spans)."""
    return int(round(SP.span_top(link_spans(l), pt)))


def flight(pid, edge, normal, along, z_top, width=384, first=-56):
    """Steps of 32 from z_top down into the sea (to STEP_LOW), going out along `normal` from `edge`; each a block from
    the bed."""
    out = []
    fac = math.degrees(math.atan2(along[1], along[0]))
    k = 0
    z = z_top - 32
    while z >= STEP_LOW:
        d = first + 64 * k + 32
        at = (edge[0] + normal[0] * d, edge[1] + normal[1] * d)
        if abs(z - WATER) < 4:
            z = WATER - 6          # never in the sea surface's plane
        out.append(block(f'{pid}_{k + 1}', at, (width, 64), FLOOR, z - FLOOR, MARBLE, FLAGS, facing=fac,
                         notes=("Steps of 32 down into the sea (D-58 P4 Q1: steps out of the water at every walk)."
                                if k == 0 else None)))
        k += 1
        z -= 32
    return out


def colonnades():
    out = []
    rnd = random.Random(404)
    for li, l in enumerate(D['links']):
        a, b, d = link_cut(l)
        za, zb = FLOOR_OF[l['a']] + 4, FLOOR_OF[l['b']] + 4
        lid = key(l['id'])
        veil = l.get('gate')
        spans = link_spans(l)
        ids = [f'platform:{lid}'] if len(spans) == 1 else (
            [f'platform:{lid}_a', f'platform:{lid}', f'platform:{lid}_b'] if len(spans) == 3 else
            ([f'platform:{lid}_a', f'platform:{lid}'] if spans[0][2] == spans[0][3] else
             [f'platform:{lid}', f'platform:{lid}_b']))
        for pid, (sp, sq, z0, z1) in zip(ids, spans):
            out.append(slab(pid, sp, sq, z0, z1, l['width'], MARBLE, FLAGS, min(z0, z1) - FLOOR, bottom=ROCK,
                            notes=(f"{l['id']}: the colonnade on the drowned temple's wall top, {int(d):,} rim to "
                                   f"rim, rising {zb - za}; marble from the bed; level over each terrace (F62).")
                            if pid == f'platform:{lid}' else None))
        p, q = PL.link_ends(l)
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        u = ((q[0] - p[0]) / L, (q[1] - p[1]) / L)
        n = (-u[1], u[0])
        hw = l['width'] / 2
        # the flight out of the water at the middle, on a side that alternates (none on the Veil)
        mid_t = 0.5
        m = (p[0] + u[0] * L * mid_t, p[1] + u[1] * L * mid_t)

        def room_for(sg):
            probe = (m[0] + n[0] * sg * 1100, m[1] + n[1] * sg * 1100)
            homes = [g['at'] for g in D['groups'] if g.get('swims')]
            return min([math.hypot(probe[0] - h[0], probe[1] - h[1]) for h in homes]
                       + [PG.poly_distance([tuple(v) for v in TOPS[o]], probe) * 2 for o in SPACES])
        side = 1 if room_for(1) >= room_for(-1) else -1
        if not veil:
            e = (p[0] + u[0] * L * mid_t + n[0] * side * hw, p[1] + u[1] * L * mid_t + n[1] * side * hw)
            out += flight(f'platform:{lid}_steps', e, (n[0] * side, n[1] * side), u, walk_z(l, mid_t))
        # broken columns along both edges (off the walking line), none by the flight
        k = 0
        for t_along in range(320, int(L) - 320, 480):
            t = t_along / L
            for sgn in (-1, 1):
                if not veil and sgn == side and abs(t - mid_t) * L < 360:
                    continue
                if veil and t_along < 900:
                    continue        # the Veil's head: the flank stubs stand there
                c = (p[0] + u[0] * t_along + n[0] * sgn * (hw - 76), p[1] + u[1] * t_along + n[1] * sgn * (hw - 76))
                roll = rnd.random()
                h = rnd.uniform(110, 280) if roll < 0.4 else (rnd.uniform(380, 560) if roll < 0.9 else 720)
                k += 1
                pid = f'platform:{lid}_col{k}'
                zc = slab_z(l, c)
                ph = rnd.uniform(0, 0.6)
                out.append(prism(pid, ring(c[0], c[1], 56, 10, ph), FLOOR, zc + int(h) - FLOOR, MARBLE, FLAGS,
                                 notes="Broken columns along the walk's edges." if k == 1 and li == 0 else None))
                OBSTACLES.add(pid)
                if h >= 700:
                    out.append(prism(f'{pid}_cap', ring(c[0], c[1], 70, 10, ph), zc + int(h), 40, MARBLE, FLAGS))
    return out


def room_flights():
    """One flight out of the water at a rim of every terrace but the court and the Grotto: the rim point facing the
    most open sea, away from the walks and places."""
    out = []
    for sid in SPACES:
        if sid in NO_STEPS:
            continue
        poly = [tuple(p) for p in TOPS[sid]]
        best = None
        for (pt, n) in PG.outline_samples(poly, 96):
            probe = (pt[0] + n[0] * 900, pt[1] + n[1] * 900)
            if abs(probe[0]) > HALF - BAND - 200 or abs(probe[1]) > HALF - BAND - 200:
                continue
            if any(PG.point_in(probe, [tuple(v) for v in TOPS[o]]) for o in SPACES):
                continue
            if near_walk(pt, 420) or kept(pt, 80):
                continue
            score = min(seg_dist(pt, a, b) for a, b, _ in WALK)
            if best is None or score > best[0]:
                best = (score, pt, n)
        if best is None:
            raise SystemExit(f'no flight for {sid}')
        _, pt, n = best
        out += flight(f'platform:{key(sid)}_steps', pt, n, (-n[1], n[0]), FLOOR_OF[sid], width=448)
        FLIGHTS[sid] = (pt, n)
    return out


FLIGHTS = {}


# ------------------------------------------------------------------------------------------------ the court, the Veil
ARENA = SPACE['room:arena']
ARENA_AT = ARENA['at']
ARENA_FL = ARENA['floor']
CHAMBER = SPACE['room:chamber']
CHAMBER_FL = CHAMBER['floor']
VEIL_LINK = next(l for l in D['links'] if l.get('gate'))
GATE_P, GATE_Q = PL.link_ends(VEIL_LINK)
GATE_X = GATE_P[0]                          # -4096: the Veil runs straight south
GATE_Y = GATE_P[1]                          # the court's south rim: the Veil's line
VEIL_W = VEIL_LINK['width']                 # 640
FLANK_T = 120
FLANK_X = VEIL_W / 2 + 8 + FLANK_T / 2      # an 8 gap between the walk's side and the stub (no shared plane)
FLANK_IN, FLANK_OUT = 256, 832              # into the court, along the Veil beyond its line
FLANK_H = 384                               # over the court's floor (P-2)
POOL_R = 448
TEST_PLATE = (-2880, 1664)                  # off the walk line from the east gate (poi:test (-2688, 1280))


def court():
    out = []
    rnd = random.Random(1212)
    # the whirlpool and the mosaic ring
    out.append(prism('platform:whirlpool', ring(ARENA_AT[0], ARENA_AT[1], POOL_R, 20), ARENA_FL, 2, MARBLE, SEA,
                     notes="The whirlpool (landmark:whirlpool): the pool where the water turns and the guardians rise."))
    for k in range(8):
        th = 2 * math.pi * (k + 0.5) / 8
        c = (ARENA_AT[0] + 820 * math.cos(th), ARENA_AT[1] + 820 * math.sin(th))
        out.append(block(f'platform:mosaic{k + 1}', c, (288, 288), ARENA_FL, 2, MARBLE, MOSAIC,
                         facing=math.degrees(th),
                         notes="The court's ring of mosaic slabs (gtemprf, once per face)." if k == 0 else None))
    # the ring of broken columns
    k = 0
    for deg in range(0, 360, 24):
        th = math.radians(deg + 12)
        c = (ARENA_AT[0] + 1330 * math.cos(th), ARENA_AT[1] + 1260 * math.sin(th))
        if any(math.hypot(c[0] - e[0], c[1] - e[1]) < 560 for e in link_ends_of('room:arena')) or \
                math.hypot(c[0] - TEST_PLATE[0], c[1] - TEST_PLATE[1]) < 420:
            continue
        if not inside_by(c, TOPS['room:arena'], 140) or any(math.hypot(c[0] - w[0], c[1] - w[1]) < 320 for w in WAVES):
            continue
        k += 1
        roll = rnd.random()
        h = rnd.uniform(140, 320) if roll < 0.45 else (rnd.uniform(420, 640) if roll < 0.85 else 880)
        pid = f'platform:court_col{k}'
        ph = rnd.uniform(0, 0.5)
        out.append(prism(pid, ring(c[0], c[1], 88, 12, ph), ARENA_FL, int(h), MARBLE, FLAGS,
                         notes="The court's ring of broken columns." if k == 1 else None))
        OBSTACLES.add(pid)
        if h > 800:
            out.append(prism(f'{pid}_cap', ring(c[0], c[1], 106, 12, ph), ARENA_FL + int(h), 48, MARBLE, FLAGS))
    # the Veil's flank stubs and the Veil
    for k, sgn in enumerate((-1, 1)):
        x = GATE_X + sgn * FLANK_X
        a, b = GATE_Y + FLANK_IN, GATE_Y - FLANK_OUT
        pid = f'platform:veil_flank{k + 1}'
        seg = (a - b) / 3
        for j, extra in enumerate((0, 112, 48)):
            ya, yb = a - seg * j, a - seg * (j + 1)
            sid = f'{pid}_{j + 1}'
            out.append(block(sid, (x, (ya + yb) / 2), (FLANK_T, seg), FLOOR + 2 * j,
                             ARENA_FL + FLANK_H + extra - FLOOR - 2 * j, MARBLE, FLAGS,
                             top_size=[FLANK_T - 32, int(seg) - 48],
                             notes=(f"The Veil's flank (P-2): broken walls {FLANK_H} or more over the court, "
                                    f"{FLANK_IN + FLANK_OUT} along the colonnade's head, either side of the falling "
                                    "water.") if k == 0 and j == 0 else None))
            OBSTACLES.add(sid)
        # a broken column head on each flank
        out.append(prism(f'{pid}_col', ring(x, GATE_Y + 80, 100, 12), ARENA_FL + FLANK_H - 8, 168, MARBLE, FLAGS))
    out.append(block('platform:veil_water', (GATE_X, GATE_Y), (VEIL_W + 16, 32), ARENA_FL + 4, 576, VEIL, VEIL,
                     bottom_surface=VEIL,
                     notes=("The Veil (gate:sleeper): a falling sheet of water across the colonnade's head; solid "
                            "until qbit 111767, then passable and hidden (evt:gate_open, evt:passed_load).")))
    # the test's floor (S's pedestal beside it)
    out.append(block('platform:test_plate', TEST_PLATE, (256, 256), ARENA_FL - SINK, 4 + SINK, MARBLE, FLAGS,
                     notes="The test's floor before S's pedestal (poi:test): stepping on asks 'Accept the test of Water?'."))
    return out


# ------------------------------------------------------------------------------------------------ the Grotto
def grotto():
    out = []
    cx, cy = CHAMBER['at']
    poly = TOPS['room:chamber']
    # the sea arch: two rock piers outside the rim (east and west), a hanging span over the grotto
    piers = []
    for k, sgn in enumerate((-1, 1)):
        rim = PG.ray_exit([tuple(p) for p in poly], (cx, cy - 300), (cx + sgn * 20000, cy - 300))
        at = (rim[0] + sgn * 260, rim[1])
        fac, q = snap_facing(90 + 8 * sgn)
        w, d = mult(520, q), mult(640, q)
        pid = f'platform:arch_pier{k + 1}'
        out.append(block(pid, at, (w, d), FLOOR, 1500 - FLOOR, ROCK, ROCK_DARK, facing=fac,
                         top_size=[mult(360, q), mult(480, q)],
                         notes="The sea arch's piers: rough rock from the bed, outside the Grotto's rim." if k == 0
                         else None))
        out.append(block(f'{pid}_head', at, (mult(400, q), mult(500, q)), 1492, 260, ROCK, ROCK_DARK, facing=fac,
                         top_size=[mult(220, q), mult(300, q)]))
        piers.append(at)
    out.append(slab('platform:arch_span', piers[0], piers[1], 1330, 1330, 420, ROCK, ROCK_DARK, 300,
                    bottom=ROCK_DARK, notes="The sea arch's span over the Grotto (hanging; nothing stands on it)."))
    # the shelf of shell and stone under the couch (S's couch and sleeper on it)
    sp = PLACE['poi:sleeper']['at']
    out.append(block('platform:shelf', sp, (768, 512), CHAMBER_FL - SINK, 40 + SINK, MARBLE, CORAL, facing=0,
                     notes="The raised shelf of shell and stone under the sleeper's couch (S: the couch, blocked)."))
    OBSTACLES.add('platform:shelf')
    dp = DAIS
    out.append(prism('platform:dais', ring(dp[0], dp[1], 224, 12), CHAMBER_FL - SINK, 8 + SINK, MARBLE, FLAGS,
                     notes="The return dais (exit:dais): shown once the Water Sleeper is awake (qbit 111763)."))
    return out


# ------------------------------------------------------------------------------------------------ the wreck
SHIP_A = (-230, -3800)          # the stern tip (north-west)
SHIP_B = (1330, -4760)          # the bow tip (south-east)
SHIP_BEAM = 640
HULL_T = 64
HULL_H = 224                    # the gunwale over the court
HOLD_TOP = 40                   # the hold's water (waded)
DECK_TOP = 96
SHIP_LEN = math.hypot(SHIP_B[0] - SHIP_A[0], SHIP_B[1] - SHIP_A[1])
SHIP_U = ((SHIP_B[0] - SHIP_A[0]) / SHIP_LEN, (SHIP_B[1] - SHIP_A[1]) / SHIP_LEN)
SHIP_N = (-SHIP_U[1], SHIP_U[0])        # to the north-east side
SHIP_FACING = math.degrees(math.atan2(SHIP_U[1], SHIP_U[0]))
SHIP_MID = ((SHIP_A[0] + SHIP_B[0]) / 2, (SHIP_A[1] + SHIP_B[1]) / 2)


def ship_pt(s, w):
    """s along the keel from -1 (stern) to 1 (bow), w across from the keel (positive north-east)."""
    return (SHIP_MID[0] + SHIP_U[0] * s * SHIP_LEN / 2 + SHIP_N[0] * w,
            SHIP_MID[1] + SHIP_U[1] * s * SHIP_LEN / 2 + SHIP_N[1] * w)


def half_beam(s, beam):
    s = max(-1.0, min(1.0, s))
    if s < 0:   # a rounder stern
        return beam / 2 * (1 - abs(s) ** 3.0) ** 0.5
    return beam / 2 * (1 - s ** 1.8) ** 0.7


def hull_outline(beam, inset=0.0, n=11):
    side = [(-1 + 2 * k / (n - 1)) for k in range(n)]
    pts = [ship_pt(s * (1 - inset), half_beam(s, beam)) for s in side]
    pts += [ship_pt(s * (1 - inset), -half_beam(s, beam)) for s in reversed(side)][1:-1]
    return pts


BREACH = (-0.08, 0.16)          # the breach in the north-east side (s range)


def wreck():
    out = []
    outer = hull_outline(SHIP_BEAM)
    n = len(outer)
    k = 0
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        rel = ((mid[0] - SHIP_MID[0]) * SHIP_U[0] + (mid[1] - SHIP_MID[1]) * SHIP_U[1]) / (SHIP_LEN / 2)
        across = (mid[0] - SHIP_MID[0]) * SHIP_N[0] + (mid[1] - SHIP_MID[1]) * SHIP_N[1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 8:
            continue
        h = HULL_H
        if across > 0 and BREACH[0] <= rel <= BREACH[1]:
            continue
        if across < 0 and -0.3 < rel < 0.2:
            h = HULL_H - 64       # sagging on the south-west side
        if rel > 0.75:
            h = HULL_H + 64       # the bow stands higher
        k += 1
        pid = f'platform:hull{k}'
        out.append(block(pid, mid, (L + 20, HULL_T), -2 - 2 * (k % 7), h + 2 + 4 * (k % 7), PLANKS, PLANKS,
                         facing=math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])),
                         notes=("The wreck's hull: MM8's ship planks (bwoodb1, D-58's xpwhull: a shipped plank texture "
                                "first), its hold half flooded.") if k == 1 else None))
        OBSTACLES.add(pid)
    # the breach: a sill holding the water in, a step on each side
    s0, s1 = BREACH
    a, b = ship_pt(s0, half_beam(s0, SHIP_BEAM)), ship_pt(s1, half_beam(s1, SHIP_BEAM))
    wlen = math.hypot(b[0] - a[0], b[1] - a[1])
    fac = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    nn = (-(b[1] - a[1]) / wlen, (b[0] - a[0]) / wlen)
    if nn[0] * SHIP_N[0] + nn[1] * SHIP_N[1] < 0:
        nn = (-nn[0], -nn[1])
    out.append(block('platform:breach_sill', mid, (wlen + 24, HULL_T), -9, 65, PLANKS, PLANKS, facing=fac,
                     notes="The breach in the hull: a sill of 56 keeps the hold's water in; a step each side."))
    for name, sgn in (('out', 1), ('in', -1)):
        c = (mid[0] + nn[0] * sgn * (HULL_T / 2 + 48), mid[1] + nn[1] * sgn * (HULL_T / 2 + 48))
        out.append(block(f'platform:breach_step_{name}', c, (wlen - 16, 96), -11 - 2 * sgn, 39 + 2 * sgn, PLANKS, PLANKS,
                         facing=fac))
    # the stern deck and its steps (inside the hull)
    inner = hull_outline(SHIP_BEAM - 2 * HULL_T - 8, inset=0.03)
    deck_end = -0.42
    bw = SHIP_BEAM - 2 * HULL_T - 8
    ss = [-0.97 + (deck_end + 0.97) * k / 6 for k in range(7)]
    deck_poly = [ship_pt(x, half_beam(x, bw)) for x in ss] + [ship_pt(x, -half_beam(x, bw)) for x in reversed(ss)]
    out.append(prism('platform:deck', deck_poly, -13, DECK_TOP + 13, PLANKS, DECK,
                     notes="The stern deck (96 over the hold), the ship's log on it; steps up from the hold."))
    for j, (s, top) in enumerate(((deck_end + 0.06, 64), (deck_end + 0.12, 32))):
        w = 2 * half_beam(s, SHIP_BEAM - 2 * HULL_T - 8) - 48
        out.append(block(f'platform:deck_step{j + 1}', ship_pt(s - 0.03, 0), (0.06 * SHIP_LEN / 2 + 2, w), -15 - 2 * j,
                         top + 15 + 2 * j,
                         PLANKS, DECK, facing=SHIP_FACING))
    # the hold's water face (the volume is objects.yml water:hold)
    out.append(prism('platform:hold_water', inner, HOLD_TOP - 2, 2, SEA, SEA, solid=False,
                     notes="The hold's water face (untouchable): 40 deep over the hold's floor, waded."))
    # masts: a broken one on the deck, a stump amidships; a fallen one lying outside on the south-west
    m1 = ship_pt(-0.62, 0)
    out.append(block('platform:mast1', m1, (64, 64), DECK_TOP - 8, 1180, MAST, MAST, facing=SHIP_FACING,
                     notes="The masts: one broken on the deck, a stump amidships, one fallen."))
    out.append(block('platform:mast1_yard', ship_pt(-0.62, 0), (40, 520), DECK_TOP + 760, 40, MAST, MAST,
                     facing=SHIP_FACING + 12))
    m2 = ship_pt(0.2, 0)
    out.append(block('platform:mast2', m2, (72, 72), -8, 340, MAST, MAST, facing=SHIP_FACING))
    fa = ship_pt(-0.35, -SHIP_BEAM / 2 - 210)
    fb = ship_pt(0.55, -SHIP_BEAM / 2 - 330)
    out.append(slab('platform:mast3', fa, fb, 52, 52, 56, MAST, MAST, 56))
    for pid in ('platform:mast1', 'platform:mast2', 'platform:mast3', 'platform:deck', 'platform:deck_step1',
                'platform:deck_step2', 'platform:breach_sill'):
        OBSTACLES.add(pid)
    # the ship's log on the deck (planes.log)
    out.append(block('platform:log', LOG, (96, 72), DECK_TOP - SINK, 44 + SINK, PLANKS, MAST, facing=SHIP_FACING,
                     notes="The ship's log on its sea chest (poi:log, planes.log)."))
    return out


# ------------------------------------------------------------------------------------------------ devices
def fountain():
    out = []
    c = STATUE
    fl = FLOOR_OF['room:statue']
    for k in range(12):
        th = 2 * math.pi * k / 12
        at = (c[0] + 500 * math.cos(th), c[1] + 500 * math.sin(th))
        out.append(block(f'platform:basin{k + 1}', at, (96, 2 * 500 * math.tan(math.pi / 12) + 26), fl - 4 - 2 * (k % 5),
                         60 + 4 * (k % 5), MARBLE,
                         FLAGS, facing=math.degrees(th),
                         notes="The fountain basin round the statue of Water (S's statue on the plinth)." if k == 0
                         else None))
        OBSTACLES.add(f'platform:basin{k + 1}')
    out.append(prism('platform:basin_water', ring(c[0], c[1], 470, 16), fl - 9, 33, MARBLE, SEA))
    out.append(block('platform:plinth', c, (384, 384), fl - 11, 107, MARBLE, FLAGS,
                     notes="The plinth of the statue of Water in the middle of the forecourt (S's statue on it)."))
    OBSTACLES.add('platform:plinth')
    return out


def bell():
    """The Drowned Bell's fallen frame: one post standing broken, the beam leaning from the floor to its head."""
    out = []
    fl = FLOOR_OF['room:statue']
    bx, by = BELL
    post = (bx + 220, by + 60)
    out.append(block('platform:bell_post', post, (96, 96), fl - 8, 400, MAST, MAST, facing=0, top_size=[80, 80]))
    a, b = (bx - 300, by - 40), (post[0] - 60, post[1])
    out.append(slab('platform:bell_frame', a, b, fl + 40, fl + 330, 72, MAST, MAST, 56,
                    notes="The Drowned Bell's fallen frame (poi:bell, planes.bell; S: the bell, blocked)."))
    for pid in ('platform:bell_post', 'platform:bell_frame'):
        OBSTACLES.add(pid)
    return out


def tide_pool():
    out = []
    c = POOL
    fl = FLOOR_OF['room:reef']
    rnd = random.Random(99)
    for k in range(9):
        th = 2 * math.pi * k / 9 + 0.2
        at = (c[0] + 300 * math.cos(th), c[1] + 300 * math.sin(th))
        fac, q = snap_facing(math.degrees(th))
        pid = f'platform:pool_rock{k + 1}'
        out.append(block(pid, at, (mult(120, q), mult(200, q)), fl - 8 - 2 * (k % 3), rnd.uniform(56, 96), ROCK, CORAL,
                         facing=fac, top_size=[mult(80, q), mult(150, q)],
                         notes="The Tide Pool's ring of coral rock." if k == 0 else None))
        OBSTACLES.add(pid)
    out.append(prism('platform:tide_pool', ring(c[0], c[1], 260, 14), fl - 13, 29, ROCK, SEA,
                     notes="The Tide Pool (poi:tide_pool, planes.tide_pool): clicked, it is drunk from."))
    OBSTACLES.add('platform:tide_pool')
    return out


def spout():
    out = []
    wx, wy = WAY_UP
    fl = FLOOR_OF['room:landing']
    for k in range(10):
        th = 2 * math.pi * (k + 0.5) / 10
        at = (wx + 300 * math.cos(th), wy + 300 * math.sin(th))
        pid = f'platform:spout_curb{k + 1}'
        out.append(block(pid, at, (64, 2 * 300 * math.tan(math.pi / 10) + 20), fl - 4 - 2 * (k % 4),
                         44 + 4 * (k % 4), MARBLE, FLAGS,
                         facing=math.degrees(th)))
        OBSTACLES.add(pid)
    out.append(prism('platform:spout_basin', ring(wx, wy, 272, 14), fl - 9, 25, MARBLE, SEA))
    out.append(prism('platform:way_up', ring(wx, wy, 150, 14), fl + 16, 2600, SPOUT, SPOUT, bottom_surface=SPOUT,
                     notes=("The waterspout (exit:way_up): a column of water rising from its basin into the sky; "
                            "clicked, the way up to the Skyroads.")))
    OBSTACLES.add('platform:way_up')
    return out


def wave_plates():
    out = []
    for i, c in enumerate(WAVES):
        sid = PL.space_of(c)
        z = FLOOR_OF[sid]
        # F62: a plate on a walk's level landing stands 4 over it (it lay in the landing's plane: geometry.coplanar)
        d = SP.deck_top([e for e in colonnades() if '_col' not in e['id'] and '_steps' not in e['id']], c, 96, FLOOR)
        top = max(z, d if d is not None else z) + 4
        out.append(block(f'platform:wave{i + 1}', c, (192, 192), z - 3, top - (z - 3), MARBLE, SPRAY,
                         notes="A freezing wave (D-58 P4, the source's nine): a PressurePlate face, xpwspray, planes.wave."
                         if i == 0 else None))
    return out


# ------------------------------------------------------------------------------------------------ the sea stacks
def stacks():
    out = []
    rnd = random.Random(2468)
    placed = []
    for k in range(28):
        ang = 2 * math.pi * k / 28 + rnd.uniform(-0.05, 0.05)
        c, s = math.cos(ang), math.sin(ang)
        # a squircle near the room's edge
        rr = (abs(c) ** 4 / 6000 ** 4 + abs(s) ** 4 / 6000 ** 4) ** (-1 / 4) * rnd.uniform(0.96, 1.02)
        at = (rr * c, rr * s)
        at = (max(-HALF + 420, min(HALF - 420, at[0])), max(-HALF + 420, min(HALF - 420, at[1])))
        if any(PG.poly_distance([tuple(v) for v in TOPS[o]], at) < 700 for o in SPACES) or near_walk(at, 500) \
                or math.hypot(at[0] - WAY_UP[0], at[1] - WAY_UP[1]) < 1200:
            continue
        if rnd.random() < 0.22:
            continue                              # gaps in the ring
        fac, q = snap_facing(math.degrees(ang) + rnd.uniform(-30, 30))
        w, d = mult(rnd.uniform(560, 960), q), mult(rnd.uniform(480, 820), q)
        h1 = rnd.uniform(500, 900)
        h2 = rnd.uniform(400, 900) if rnd.random() < 0.7 else 0
        j = len(placed) + 1
        pid = f'platform:stack{j}'
        out.append(block(pid, at, (w, d), FLOOR, h1 - FLOOR, ROCK, ROCK_DARK, facing=fac,
                         top_size=[mult(w * 0.7, q), mult(d * 0.72, q)],
                         notes="The ring of sea stacks near the room's edge (open sea and fog beyond)." if j == 1
                         else None))
        top = h1
        if h2:
            off = (rnd.uniform(-60, 60), rnd.uniform(-60, 60))
            out.append(block(f'{pid}_top', (at[0] + off[0], at[1] + off[1]), (mult(w * 0.62, q), mult(d * 0.6, q)),
                             h1 - 16, h2 + 16, ROCK, ROCK_DARK, facing=fac,
                             top_size=[mult(w * 0.3, q), mult(d * 0.34, q)]))
            top = h1 + h2
        placed.append((at, top, w))
    # three broken arches between neighbours close enough
    arches = 0
    for i in range(len(placed)):
        if arches >= 3:
            break
        a, ta, wa = placed[i]
        b, tb, wb = placed[(i + 1) % len(placed)]
        gap = math.hypot(b[0] - a[0], b[1] - a[1])
        if gap > 1700 or min(ta, tb) < 900 or i % 2:
            continue
        arches += 1
        z = min(ta, tb) - 220 - 8 * arches
        out.append(slab(f'platform:arch{arches}', a, b, z, z, 320, ROCK, ROCK_DARK, 260, bottom=ROCK_DARK,
                        notes="A broken arch between two stacks." if arches == 1 else None))
    return out


# ------------------------------------------------------------------------------------------------ rooms.yml
def sea_surface():
    h = HALF - 2
    return {'id': 'platform:sea', 'outline': [[-h, -h], [h, -h], [h, h], [-h, h]], 'base': WATER - 2 - FLOOR,
            'rise': 2, 'surface': SEA, 'top_surface': SEA, 'bottom_surface': SEA, 'solid': False,
            'notes': ("The sea's surface (untouchable, MM7 water): the party sinks in and swims in the water volumes "
                      "under it (objects.yml water).")}


def build_rooms():
    platforms = []
    for sid in SPACES:
        platforms += terrace(sid) + stubs(sid)
    platforms += colonnades() + room_flights() + court() + grotto() + wreck() + fountain() + bell() + tide_pool()
    platforms += spout() + wave_plates() + stacks() + [sea_surface()]
    for p in platforms:
        if p.get('notes') is None:
            p.pop('notes', None)
    room = {
        'id': 'room:sea', 'space': 'zone:sea', 'name': 'The Plane of Water', 'outline': [[-HALF, -HALF], [HALF, -HALF],
                                                                                          [HALF, HALF], [-HALF, HALF]],
        'floor': FLOOR, 'ceiling': CEIL, 'theme': 'theme:water', 'platforms': platforms,
        'notes': ("The open sky of the Plane of Water: one room from the sea bed at -1,024 to the sky at 4,096, its walls "
                  "and ceiling sky faces. The drowned temple's terraces and colonnades stand out of the sea (surface "
                  "-64) on rough rock; a ring of sea stacks near the edge."),
    }
    return {'format': 0, 'themes': [{'id': 'theme:water', 'wall': SKY, 'floor': BED, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:water', 'ambient': 30}, 'rooms': [room]}


# ------------------------------------------------------------------------------------------------ objects.yml
def spread(at, n, r=224):
    if n == 1:
        return [at]
    return [(at[0] + r * math.cos(2 * math.pi * k / n), at[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def obstacle_feet():
    return [[tuple(v) for v in foot(p)] for p in ROOMS['rooms'][0]['platforms'] if p['id'] in OBSTACLES]


def clear_spot(q, obs, pad=128):
    return all(not PG.point_in(q, o) and poly_dist_outline(q, o) > pad for o in obs)


def in_water(q, pad=300):
    """Open sea: no terrace, walk or stack within `pad`."""
    if abs(q[0]) > HALF - BAND - pad or abs(q[1]) > HALF - BAND - pad:
        return False
    for p in ROOMS['rooms'][0]['platforms']:
        if p['id'] == 'platform:sea' or p.get('solid') is False:
            continue
        f = [tuple(v) for v in foot(p)]
        if PG.point_in(q, f) or poly_dist_outline(q, f) < pad:
            return False
    return True


def water_volumes():
    i = HALF - BAND
    h = HALF
    bands = [
        ('north', [[-h, h], [-i, i], [i, i], [h, h]], [0, -CURRENT, 0]),
        ('south', [[-h, -h], [h, -h], [i, -i], [-i, -i]], [0, CURRENT, 0]),
        ('east', [[h, -h], [h, h], [i, i], [i, -i]], [-CURRENT, 0, 0]),
        ('west', [[-h, -h], [-i, -i], [-i, i], [-h, h]], [CURRENT, 0, 0]),
    ]
    out = [{'id': 'water:sea', 'outline': [[-i, -i], [i, -i], [i, i], [-i, i]], 'top': WATER, 'bottom': FLOOR,
            'tint': TINT, 'fog': FOG,
            'notes': ("The inner sea (D-58 P4 Q1): surface swimming free, 15 s of breath under, no falling damage "
                      "into it; no current.")}]
    for name, outline, cur in bands:
        out.append({'id': f'water:edge_{name}', 'outline': [list(map(int, p)) for p in ccw([tuple(p) for p in outline])],
                    'top': WATER, 'bottom': FLOOR, 'tint': TINT, 'fog': FOG, 'current': cur,
                    'notes': (f"The outer sea's {name} band past the stacks: a constant inward current of {CURRENT} "
                              "(D-58; no radial current).")})
    out.append({'id': 'water:hold', 'outline': [ipt(p) for p in ccw(hull_outline(SHIP_BEAM - 2 * HULL_T - 8, 0.03))],
                'top': HOLD_TOP, 'bottom': 0, 'tint': TINT, 'fog': FOG,
                'notes': "The wreck's hold, half flooded: 40 deep over its floor, waded (D-58 P4 Q2: no diving)."})
    return out


OCTOPOD_DEEP = 11474     # A2's Great Octopod on S's foam-free xeen_octopod_deep.glb (11471's numbers; session 20)


def pieces():
    """S's pieces (D-58 C7, session 20; level_generation/decorations/xeen_planes_claude/README.md). The couch on the shelf
    (its top named: the sea arch's span over the Grotto is a higher floor there) along
    the shelf's 768 (facing n: at ne it overhangs the 512 side); the Drowned Bell on the dry forecourt by its frame."""
    bell = PC.deco('bell', 'room:sea', 'xeen_drownedbell', (BELL[0] + 23, BELL[1] - 108), 282, FLOOR_OF['room:statue'],
                   notes="The Drowned Bell (S): on its side by the fallen frame, its back 8 clear of the beam; clicked, "
                         "A3's planes.bell.")
    return PC.decorations(
        'water', 'room:sea',
        sleeper=(PLACE['poi:sleeper']['at'], 90, CHAMBER_FL + 40), statue=(STATUE, 45, None),
        pedestal=((TEST_PLATE[0], TEST_PLATE[1] + 208), 270, None), dais=(DAIS, 0, None), extra=[bell])


def objects():
    arr = PLACE['entrance:d7_fall']
    start = {'room': 'room:sea', 'at': ipt(arr['at']), 'floor_height': 0, 'facing': arr['face'],
             'notes': "entrance:d7_fall on the Spray Terrace, facing south-west (Xeen.PlaneArrivals.water)."}
    obs = obstacle_feet()
    monsters = []
    for gi, g in enumerate(D['groups']):
        row = PD.ROWS[g['row']]
        swims = g.get('swims')
        if swims:
            # D-200 (3): the leash plus the octopods' notice range (A2's relation `short`; no `hostile`, so no Aggressor
            # bit that would widen it to 5,120) stays off the Whirlpool Court and the arrival
            home = g['at']
            court = PG.poly_distance([tuple(v) for v in TOPS['room:arena']], home)
            arrival = math.dist(home, PLACE['entrance:d7_fall']['at'])
            if min(court, arrival) < OCTO_LEASH + OCTO_NOTICE:
                raise SystemExit(f"{g['id']}: home {court:.0f} from the court, {arrival:.0f} from the arrival: under "
                                 f"the leash {OCTO_LEASH} plus the notice range {OCTO_NOTICE} (D-200)")
            pts = spread(g['at'], g['count'], 420)
            for k, q in enumerate(pts):
                assert in_water(q), (g['id'], q)
                e = {'id': f"monster:{key(g['id'])}_{k + 1}", 'room': 'room:sea', 'monster': OCTOPOD_DEEP, 'at': ipt(q),
                     'floor_height': FLOOR, 'above_floor': OCTO_RISE, 'leash': OCTO_LEASH, 'facing': 0,
                     'group': gi + 1}
                if k == 0:
                    e['notes'] = (f"{g['id']}: {g['count']} {row['short']} ({row['level']}; A2's {OCTOPOD_DEEP} Xeen "
                                  "Octopod E, the foam-free swimmer, session 20), swimmers in the inner sea "
                                  f"(D-58 Q4), bound to it (the Swimmer kind, D-200); they start mid-sea ({OCTO_RISE} "
                                  f"over the bed, merge point 27's `above_floor`), keep within {OCTO_LEASH} of home "
                                  "(session 18) and shoot their ink at a party within reach (D-200).")
                monsters.append(e)
            continue
        z = FLOOR_OF[g['space']]
        poly = TOPS[g['space']]
        c = SPACE[g['space']]['at']
        for k, p in enumerate(spread(g['at'], g['count'])):
            cands = [p] + [(p[0] + r * math.cos(2 * math.pi * j / 12), p[1] + r * math.sin(2 * math.pi * j / 12))
                           for r in range(96, 1400, 96) for j in range(12)]
            q = None
            for q in cands:
                if inside_by(q, poly, 160) and clear_spot(q, obs) and \
                        all(math.hypot(q[0] - m['at'][0], q[1] - m['at'][1]) > 200 for m in monsters) and \
                        all(math.hypot(q[0] - w[0], q[1] - w[1]) > 200 for w in WAVES):
                    break
            else:
                raise SystemExit(f"no spot for {g['id']} {k}")
            e = {'id': f"monster:{key(g['id'])}_{k + 1}", 'room': 'room:sea', 'monster': row['id'], 'at': ipt(q),
                 'floor_height': int(z), 'facing': 0, 'hostile': True, 'group': gi + 1}
            if k == 0:
                e['notes'] = f"{g['id']}: {g['count']} {row['short']} ({row['level']})."
            monsters.append(e)
    k = 0
    for g in D['test_group']:
        row = PD.ROWS[g['row']]
        for j in range(g['count']):
            k += 1
            at = ARENA_AT if k == 1 else (ARENA_AT[0] + (k - 2.5) * 2 * 240, ARENA_AT[1] - 160)
            monsters.append({'id': f'monster:guardian_{k}', 'room': 'room:sea', 'monster': row['id'], 'at': ipt(at),
                             'floor_height': ARENA_FL + 2, 'facing': 90, 'hostile': True, 'group': GUARD_GROUP,
                             'hidden': True,
                             'notes': (f"{row['short']} ({row['level']}): the test's hidden group {GUARD_GROUP} in the "
                                       "whirlpool, shown by evt:test (D-58 C3).")})
    chests = [
        {'id': 'chest:test', 'room': 'room:sea', 'at': ipt(TEST_CHEST), 'floor_height': CHAMBER_FL,
         'kind': 'ch3', 'facing': 'n', 'treasure_level': 6, 'random_items': 3, 'gold': 2500,
         'notes': "The test's chest (aaze0028:4 'Chest'): the source's gold and three items, in the Grotto past the Veil."},
        {'id': 'chest:wreck_cache', 'room': 'room:sea', 'at': ipt(CACHE), 'floor_height': 0, 'kind': 'ch1',
         'facing': 'ne', 'treasure_level': 6, 'random_items': 2, 'gold': 1200, 'trap_level': 8,
         'notes': "The ship's strongbox in the half-flooded hold (trapped; waded to, D-58 P4 Q2)."},
    ]
    items = [{'id': f'item:log_potion{i + 1}', 'room': 'room:sea', 'item': 258,
              'at': ipt(ship_pt(-0.80 + 0.05 * i, -90 + 180 * i)), 'floor_height': DECK_TOP}
             for i in range(2)]
    items[0]['notes'] = "The log's find: Water Resistance (258), on the stern deck."
    return {
        'format': 1, 'start': start,
        # AU's plane bed (devdocs/xeen/AUDIO.md session 5, "The lines to paste"; D-48 `pan: false`)
        'sounds': [{'id': 'sound:plane_bed', 'room': 'room:sea', 'at': [0, 0], 'height': 1100, 'sound': 'xeen_amb_plane_water', 'radius': 12000, 'inner_radius': 8000, 'volume': 0.45, 'pan': False}],
        'arrivals': [{'entrance': 'entrance:d7_fall', 'room': 'room:sea', 'at': ipt(arr['at']), 'floor_height': 0,
                      'facing': arr['face'], 'notes': "The drop from D7's south-west corner (Xeen.toPlane('water'))."}],
        'chests': chests, 'items': items, 'monsters': monsters, 'water': water_volumes(), 'decorations': pieces(),
        'notes': ("P4 L4 objects (generated by output/studio_cal/p4/tools/gen.py): 27 placed hostiles in 10 groups (5 "
                  f"Great Octopods swimming) and the test's three in the hidden group {GUARD_GROUP}; two chests at "
                  "treasure 6; the log's find; the sea's water volumes; S's pieces (session 20): sleeper and couch, statue, "
                  "pedestal, return dais (hidden until he wakes), the Drowned Bell. No lights."),
    }


# ------------------------------------------------------------------------------------------------ wiring.yml
def wiring():
    ev = []
    ev.append({'id': 'evt:test', 'preset': 'script', 'trigger': 'step', 'source': 'platform:test_plate',
               'condition': {'all': [{'not': {'qbit': 'm38_water_test'}}, {'not': {'map_var': 'test_accepted'}}]},
               'question': {'ask': 'Accept the test of Water?', 'answers': ['Yes', 'Y']},
               'effects': [{'lua': 'XeenQuests.hook("m38.test_water")'}, {'show_actors': GUARD_GROUP},
                           {'set': {'var': {'map_var': 'test_accepted'}, 'value': 1}}],
               'notes': ("D-58 C3: the test (aaze0028:5). Yes: A3's m38.test_water line, the guardians rise from the "
                         f"whirlpool (group {GUARD_GROUP} shown); any other answer does nothing. Not asked again while "
                         "they live.")})
    ev.append({'id': 'evt:test_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'map_var': 'test_accepted'}, {'not': {'qbit': 'm38_water_test'}}]},
               'lua': f'Xeen.planeTestCheck("water", {GUARD_GROUP})',
               'notes': ("A3's killed-group check (xeen_common.lua): once the three guardians are dead it runs "
                         "m38.test_water_passed, which sets qbit 111767 (P-1) with its line.")})
    still = [{'passable': 'platform:veil_water'}, {'hide': 'platform:veil_water'}]
    ev.append({'id': 'evt:gate_open', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'qbit': 'm38_water_test'}, {'not': {'map_var': 'gate_open'}}]},
               'effects': still + [{'text': 'The falling water stills and parts.'},
                                   {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': 'The Veil stills the second the qbit is set (C4).'})
    ev.append({'id': 'evt:passed_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm38_water_test'},
               'effects': still + [{'hide_actors': GUARD_GROUP}, {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': ("P-1: the load event reads qbit 111767: the Veil stilled, the guardians hidden, the whirlpool "
                         "quiet (through refills and the reset after a map rebuild).")})
    ev.append({'id': 'evt:gate', 'preset': 'script', 'source': 'platform:veil_water', 'title': 'The Veil',
               'effects': [{'text': 'The falling water throws you back.'}],
               'notes': 'Clicked: the Veil does not let anyone through before the test.'})
    ev.append({'id': 'evt:dais_hide', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': 'm38_water'}},
               'effects': [{'hide': 'platform:dais'}, {'passable': 'platform:dais'}],
               'notes': "C5: the return dais shows once the Water Sleeper is awake (qbit 111763, m38.sleeper_water)."})
    ev += PC.dais_events('water', 'm38_water')
    ev.append(PC.sleeper_event('water'))
    ev.append({'id': 'evt:wave', 'preset': 'script', 'trigger': 'step', 'source': 'platform:wave1',
               'sources': [f'platform:wave{i}' for i in range(2, 10)],
               'lua': 'XeenQuests.hook("planes.wave")',
               'notes': ("D-58 P4: A3's planes.wave (one time in three, 50 water damage to each member, 'A freezing "
                         "wave breaks over you!').")})
    ev.append({'id': 'evt:bell', 'preset': 'script', 'source': 'platform:bell_frame', 'title': 'The Drowned Bell',
               'lua': 'XeenQuests.hook("planes.bell")',
               'notes': "A3's planes.bell: it tolls under the waves; the first time an emerald (map variable p4_bell)."})
    ev.append(PC.copy_for(ev[-1], 'bell', 'evt:bell_deco'))
    ev.append({'id': 'evt:tide_pool', 'preset': 'script', 'source': 'platform:tide_pool', 'title': 'The Tide Pool',
               'lua': 'XeenQuests.hook("planes.tide_pool")',
               'notes': "A3's planes.tide_pool: once a day, +20 Water resistance until rest (the buff device)."})
    ev.append({'id': 'evt:log', 'preset': 'script', 'source': 'platform:log', 'title': "The ship's log",
               'lua': 'XeenQuests.hook("planes.log")',
               'notes': "A3's planes.log: the log's lines; its find (Water Resistance) lies beside it."})
    ev.append({'id': 'evt:plaque', 'preset': 'script', 'source': 'platform:plinth', 'title': 'Plaque',
               'lua': 'XeenQuests.hook("m38.plaque_water")',
               'notes': "A3's m38.plaque_water: 'Step Four' at the base of the statue (the statue on it is S's)."})
    ev.append(PC.copy_for(ev[-1], 'statue', 'evt:plaque_statue'))
    ev.append({'id': 'evt:chest_test', 'preset': 'chest', 'source': 'chest:test', 'title': 'Chest',
               'notes': "The test's chest (aaze0028:4)."})
    ev.append({'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:wreck_cache', 'title': 'Chest',
               'notes': "The ship's strongbox (trapped)."})
    if D7_LIVE:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The waterspout',
                   'effects': [{'lua': PC.d7_return_lua('water')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': ("D-58 C5: the way up, always open, to D7's entrance:p4_return; A3's m38.way_up_water is "
                             "its question.")})
        ev.append({'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': 'The return dais',
                   'condition': {'qbit': 'm38_water'}, 'locked_text': 'The dais is dark and still.',
                   'effects': [{'lua': PC.d7_return_lua('water')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': "D-58 C5: the dais after the sleeper, to D7's entrance:p4_return (A3's m38.dais_water)."})
        ev.append(PC.copy_for(ev[-1], 'dais', 'evt:dais_disc'))
    else:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The waterspout',
                   'effects': [{'text': 'The spout roars up into the sky. (The Skyroads are not open yet.)'}],
                   'notes': "Sealed until xeen_d7.blv is installed and lists entrance:p4_return."})
    return {'format': 0, 'variables': ['test_accepted', 'gate_open', 'dais_shown'], 'events': ev}


# ------------------------------------------------------------------------------------------------ plan, project
def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan(level):
    p = load('L1', 'plan.yml')
    p['level'] = level
    p['notes'] = (p['notes'] + " L2-L4 (A6's planes sub-agent, seventeenth session, 2026-11-21): built by "
                  "output/studio_cal/p4/tools/gen.py; the terraces and colonnades marble on rough rock out of MM9 water "
                  "volumes (edge bands with an inward current of 256); steps out of the sea at every walk and terrace "
                  "but the court and the Grotto; the gate a falling veil of water made passable on qbit 111767; S's "
                  "pieces blocked by name.")
    return p


def project(level):
    p = load('L1', 'project.yml')
    for n in p['neighbours']:
        if n['id'] in ('exit:d7_way_up', 'exit:d7_dais') and not D7_LIVE:
            n.pop('arrival', None)
            n.pop('arrival_hint', None)
            n['notes'] = n['notes'] + " Sealed until xeen_d7.blv is installed and names entrance:p4_return."
    p['new'] = False
    p['notes'] = (f"Xeen design brief, level {level}: P4 Plane of Water of Xeen, an open-air BLV (devdocs/"
                  "INDOOR_OPEN_SKY.md; X9's and P5's route) built with the studio (profile region): one room of open "
                  "sky (xeen_plane_water) over a sea of MM9 water volumes with a drowned temple standing out of it. "
                  "map_stats 9118 (A2's row), music 7, treasure 6; Water rows 11625, 11710-11712, Great Octopod 11471; "
                  "hooks: A3's m38.*_water, planes.wave, planes.bell, planes.tide_pool, planes.log, Xeen.planeTestCheck.")
    return p


def atmosphere():
    a = load('L1', 'atmosphere.yml')
    a['notes'] = a['notes'] + " L4: as L1 (D-58 Q3)."
    return a


def write(level, name, data):
    (BRIEF / level).mkdir(parents=True, exist_ok=True)
    with open(BRIEF / level / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


# ------------------------------------------------------------------------------------------------ built
def nudge_in(p, sid, margin):
    """p moved toward its space's middle until it stands `margin` inside the rim."""
    c = SPACE[sid]['at']
    poly = TOPS[sid]
    for t in [i / 40 for i in range(41)]:
        q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
        if inside_by(q, poly, margin):
            return ipt(q)
    return ipt(c)


TOPS = {sid: rough_outline(sid) for sid in SPACES}
STATUE = tuple(SPACE['room:statue']['at'])                      # D-58: the statue in the middle of its forecourt
WAY_UP = nudge_in(PLACE['exit:way_up']['at'], 'room:landing', 420)
BELL = nudge_in(PLACE['poi:bell']['at'], 'room:statue', 420)
POOL = nudge_in(PLACE['poi:tide_pool']['at'], 'room:reef', 420)
DAIS = nudge_in(PLACE['exit:dais']['at'], 'room:chamber', 300)
TEST_CHEST = nudge_in(PLACE['poi:test_chest']['at'], 'room:chamber', 260)
LOG = ipt(ship_pt(-0.72, 0))                                     # on the stern deck
CACHE = ipt(ship_pt(0.42, -60))                                  # in the hold
OCTO_LEASH = 1280
OCTO_NOTICE = 2560     # D-200: an unengaged octopod notices a party within its relation's range (`short`)
OCTO_RISE = 512        # mid-sea: the bed at -1,024, the surface at -64
WAVES = []
for _c in D['hazard']['cells']:
    _sid = PL.space_of(_c)
    WAVES.append(nudge_in(_c, _sid, 200))
WALK = walk_lines()
KEEP = ([(p['at'], 380) for p in PLACE.values()] + [(g['at'], 360) for g in D['groups'] if not g.get('swims')]
        + [(c, 240) for c in WAVES] + [(WAY_UP, 520), (STATUE, 700), (BELL, 520), (POOL, 480), (TEST_PLATE, 420),
                                        (SHIP_MID, 1150), (DAIS, 380), (TEST_CHEST, 300)])
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
    print('platforms', len(ps), 'monsters', len(objs['monsters']), 'D7 live', D7_LIVE, 'gate y', round(GATE_Y),
          'way up', WAY_UP, 'flights', {k: ipt(v[0]) for k, v in FLIGHTS.items()}, 'waves', WAVES)
