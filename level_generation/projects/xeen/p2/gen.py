#!/usr/bin/env python3
"""P2 Plane of Air of Xeen: writes L2, L3 and L4 (A6's planes sub-agent, sixteenth session, 2026-11-21), after P1's
gen.py (level_generation/projects/xeen/p1/, its look-pass helpers) and X9's clouds (A5's open-air BLV route; nothing of
theirs edited).

The plan is L1's (planes_design.py with D-58 applied); this file turns it into the studio's rooms, objects and wiring:

- room:air, one open-air room from the safety floor (FLOOR) to the sky (CEIL), every wall, floor and ceiling face a
  sky face (plane_air draws);
- each island a rough floating rock from the start (the look pass): its L1 outline (planes_geom.blob) with a ragged
  rim as a thin top slab, two shrinking tiers of rock under it with outlines of their own (ledges on the underside),
  tapered roots hanging from the lowest tier on Pythagorean directions (leaning faces stay flat, corners whole) to a
  jagged underside, crags standing on the rim off every walking line, and skirts of cloud wreathing the rock under the
  rim (untouchable: drawn, nothing stands on them, a party walking off the edge falls through them);
- the Wind Statue's island packed cloud (its top xccloud, its body cloud);
- bridges as cloud-stone slabs (7tws1f) with wisps of cloud under them;
- the Eye of the Winds: twelve standing stones, two of them the gate at the Eye's north rim; between them a curtain of
  wind (a translucent xcwisp platform, solid) that qbit 111765 makes passable and hides (no door: P-2 by the Stair of
  Wind's cheeks, t09a01, at least 192 over its steps and 256 over the Eye's floor);
- the Stair of Wind: sixteen cloud-stone steps of 32 to the Sleeper's Aerie (768), the highest island, under its open
  dome of six columns;
- nine storm plates (xpascorch, A3's planes.storm), none on a bridge or in the Eye; the Singing Stones (gwspout, A3's
  planes.singing_stones); the storm cairn (planes.cairn); the way up (an updraft disc in a ring of white stones, the
  `exit` preset to D7's entrance:p2_return); the return dais (shown on m38.air, the `exit` preset);
- falls: a party under -1,500 (and the safety floor) goes through A3's Xeen.skyFallTo("p2") to the Gale Landing.

S's pieces (the statue of Air, the sleeper and couch, the test's pedestal, the basket) are spots by name, blocked (C7:
no stand-ins).

    python3 level_generation/projects/xeen/p2/gen.py      # writes devdocs/xeen/briefs/p2/L2, L3, L4
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

BRIEF = ROOT / 'devdocs/xeen/briefs/p2'
WORLD = ROOT / 'assets_dev/worlds/xeen'
PL = PG.Plane('p2')
D = PL.d
SPACE = PL.space
PLACE = PL.place

FLOOR = -6000          # the safety floor: a fall the one-second check misses lands here and runs the same fall
CEIL = 4096
FALL_Z = -1500         # D-58 P2 Q1
TEST_QBIT = PD.TEST_QBITS['air']                      # 111765
SLEEPER_QBIT = PD.SLEEPER_QBITS['air']                # 111761
GUARD_GROUP = 60
SLAB = 160             # the island's top slab (the rim's thickness)
SINK = 4               # plates, the eye, the dais, the updraft: sunk into the top they lie on (X8's, F62: no lid)

# ------------------------------------------------------------------------------------------------ textures
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}           # sky faces (plane_air draws)
TOP = {'texture': 'gwsphlfl', 'size': [128, 128], 'scale': 2}        # MM8 Plane of Air's pale wind-carved stone
RIM = {'texture': 'gwsphlwl', 'size': [128, 128], 'scale': 2}        # MM8 Plane of Air's wind-streaked stone
ROCK = {'texture': 'gwspotwl', 'size': [256, 256], 'scale': 2}       # MM8 Plane of Air's blue-grey rough rock
UNDER = {'texture': 'gwspinwl', 'size': [256, 256], 'scale': 2}      # its darker rock: the undersides
CLOUD_TOP = {'texture': 'xccloud', 'size': [256, 256], 'scale': 2}   # X8's walkable cloud top (A6)
CLOUD_SIDE = {'texture': 'xccloudsd', 'size': [256, 256], 'scale': 2, 'uneven': True}
MARBLE = {'texture': '7tws1f', 'size': [128, 128], 'scale': 2}       # X9's cloud-stone (MM7 marble)
MARBLE_FIT = {'texture': '7tws1f', 'size': [128, 128], 'fit': True}
BRICK = {'texture': 't09a01', 'size': [128, 256], 'scale': 2}        # MM8 Plane of Air's pale brick: cheeks, dome base
MENHIR = {'texture': 'gn_mtl01', 'size': [128, 128], 'scale': 2}     # MM8 Plane of Air's grey stone: standing stones
HOLLOW = {'texture': 'gwspout', 'size': [256, 256], 'fit': True}     # MM8 Plane of Air's pierced rock: Singing Stones
WIND = {'texture': 'xcwisp', 'size': [256, 256], 'scale': 2, 'translucent': 0.55}   # X9's wisp: the updraft
CURTAIN_OPACITY = float(os.environ.get('P2_CURTAIN_OPACITY', '0.80'))
CURTAIN_TINT = [float(v) for v in os.environ.get('P2_CURTAIN_TINT', '0.72,0.86,1.15').split(',')]
WIND_CURTAIN = {'texture': 'xcwisp', 'size': [256, 256], 'scale': 2, 'flow': 'up',   # D-64: streams upward
                'translucent': {'opacity': CURTAIN_OPACITY, 'tint': CURTAIN_TINT, 'two_sided': False}}
SCORCH = {'texture': 'xpascorch', 'size': [128, 128], 'fit': True}  # s33: the picture's own size (128)   # new (xtex.py, map_textures/p2), once per plate


def live_d7():
    if os.environ.get('P2_D7_LIVE') == '1':
        return True
    studio = WORLD / 'maps/xeen_d7.studio.yml'
    return (WORLD / 'maps/xeen_d7.blv').exists() and studio.exists() and 'entrance:p2_return' in studio.read_text()


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
    """A rectangular block whose foot stands at absolute z (P1's, on the safety floor)."""
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
    """A hanging slab from a (top z0) to b (top z1), `width` wide, `thickness` under its top (X9's platform_slab)."""
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


def foot(e):
    """A platform's footprint: its outline, or its block's rectangle turned by `facing` (its foot; top_size aside)."""
    if 'outline' in e:
        return [tuple(p) for p in e['outline']]
    cx, cy = e['at']
    L, W = e.get('top_size', e['size']) if e.get('top_size') and e['top_size'][0] > e['size'][0] else e['size']
    f = math.radians(e.get('facing', 0))
    ux, uy, vx, vy = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    return [(cx + sx * L / 2 * ux + sy * W / 2 * vx, cy + sx * L / 2 * uy + sy * W / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def rect(at, size, facing):
    cx, cy = at
    L, W = size
    f = math.radians(facing)
    ux, uy, vx, vy = math.cos(f), math.sin(f), -math.sin(f), math.cos(f)
    return [(cx + sx * L / 2 * ux + sy * W / 2 * vx, cy + sx * L / 2 * uy + sy * W / 2 * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


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
ISLANDS = [s['id'] for s in D['spaces']]
FLOOR_OF = {s['id']: s['floor'] for s in D['spaces']}
CLOUD_ISLES = ('room:statue',)            # the Wind Statue's island is packed cloud (L1)


def link_ends(l):
    if l['id'] == 'link:stair_of_wind':
        return STAIR_FOOT, STAIR_HEAD
    return PL.link_ends(l)


def walk_lines():
    """Lines a party walks (L1's walk, every bridge, the stair) with their half widths: crags, plates and props keep off
    them."""
    out = [(a, b, 192) for a, b, _, _ in PL.walk_segments()[0]]
    for l in D['links']:
        p, q = PL.link_ends(l)
        out.append((p, q, l['width'] / 2 + 96))
    return out


def near_walk(q, pad):
    return any(seg_dist(q, a, b) < hw + pad for a, b, hw in WALK)


KEEP = []        # (point, radius): places, groups, plates, link ends: no crag or prop within


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
    if sid == 'room:arena':
        pts.append(PLACE['gate:sleeper']['at'])
    return pts


def rough_outline(sid, scale=1.0, seed=0, points=24, out_amp=(0, 150), hold=560):
    """The island's L1 outline (blob) with a ragged rim: each point pushed out by its own amount (never in where a
    bridge lands, the gate or a place stands), scaled about the middle for the tiers under it."""
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
        if scale < 1:
            k *= rnd.uniform(0.94, 1.04)
        out.append((cx + dx * k, cy + dy * k))
    return [ipt(p) for p in ccw(out)]


def top_outline(sid):
    return TOPS[sid]


# ------------------------------------------------------------------------------------------------ islands
TIERS = [(0.84, (220, 340)), (0.60, (320, 480))]       # (scale, depth) under the top slab


def island(sid):
    s = SPACE[sid]
    fl = s['floor']
    cloud = sid in CLOUD_ISLES
    rnd = random.Random(31 * s['seed'])
    side, top, under = (CLOUD_SIDE, CLOUD_TOP, CLOUD_SIDE) if cloud else (RIM, TOP, UNDER)
    out = [prism(f'platform:{key(sid)}', TOPS[sid], fl - SLAB, SLAB, side, top, bottom_surface=under,
                 notes=f"{s['name']}: {s['shape']} (floor {fl}); the top slab with a ragged rim.")]
    z = fl - SLAB
    polys = []
    for t, (scale, dep) in enumerate(TIERS):
        poly = rough_outline(sid, scale, seed=t + 1, points=20 - 4 * t, out_amp=(-60, 120), hold=0)
        h = rnd.uniform(*dep)
        body = CLOUD_SIDE if cloud else (RIM if t == 0 else ROCK)
        out.append(prism(f'platform:{key(sid)}_tier{t + 1}', poly, z - h, h + 8, body, body,
                         bottom_surface=CLOUD_SIDE if cloud else UNDER,
                         notes="The rock under the rim, stepping in (a ledge on the underside)." if t == 0 and sid ==
                         ISLANDS[0] else None))
        z -= h
        polys.append(poly)
    out += roots(sid, polys[-1], z, rnd, cloud)
    return out


def roots(sid, poly, ztop, rnd, cloud):
    """Tapered roots hanging from the lowest tier: wide at the top (hidden in the tier), narrowing to a jagged foot."""
    s = SPACE[sid]
    cx, cy = s['at']
    ex, ey = s['extent']
    n = 7 if ex * ey > 7e6 else 6
    out = []
    tries = 0
    while len(out) < n and tries < 200:
        tries += 1
        ang = rnd.uniform(0, 360)
        fac, q = snap_facing(ang)
        rr = rnd.uniform(0.0, 0.42) * min(ex, ey) * 0.6
        th = rnd.uniform(0, 2 * math.pi)
        at = (cx + rr * math.cos(th), cy + rr * math.sin(th))
        tw, td = mult(rnd.uniform(0.22, 0.42) * ex * 0.6, q), mult(rnd.uniform(0.22, 0.42) * ey * 0.6, q)
        if not all(inside_by(v, poly, 24) for v in rect(at, (tw, td), fac)):
            continue
        fw, fd = mult(rnd.uniform(48, 160), q), mult(rnd.uniform(48, 160), q)
        depth = int(rnd.uniform(420, 1500) // 16 * 16)
        if len(out) == 0:
            depth = int(rnd.uniform(1300, 1700) // 16 * 16)       # the deepest under the middle
        body = CLOUD_SIDE if cloud else (ROCK if len(out) % 2 else UNDER)
        out.append(block(f'platform:{key(sid)}_root{len(out) + 1}', ipt(at), (fw, fd), ztop + 24 + 8 * len(out) - depth, depth, body,
                         body, facing=fac, top_size=[tw, td], bottom_surface=body,
                         notes="Tapered roots: the island's jagged underside (Pythagorean facings)." if not out and
                         sid == ISLANDS[0] else None))
    return out


def crags(sid):
    """Rocks standing on the rim, half over the edge, off every walking line, place and plate: a broken skyline."""
    s = SPACE[sid]
    if sid in CLOUD_ISLES or sid == 'room:chamber':
        return []
    poly = TOPS[sid]
    rnd = random.Random(77 * s['seed'])
    out = []
    cand = PG.outline_samples([tuple(p) for p in poly], 340)
    rnd.shuffle(cand)
    for (p, n) in cand:
        if len(out) >= 6:
            break
        at = (p[0] - n[0] * 40, p[1] - n[1] * 40)
        if near_walk(at, 260) or kept(at, 260) or any(math.hypot(at[0] - c['at'][0], at[1] - c['at'][1]) < 520
                                                      for c in out):
            continue
        fac, q = snap_facing(math.degrees(math.atan2(n[1], n[0])) + rnd.uniform(-20, 20))
        w, d = mult(rnd.uniform(160, 300), q), mult(rnd.uniform(140, 260), q)
        h = rnd.uniform(140, 420)
        out.append(block(f'platform:{key(sid)}_crag{len(out) + 1}', at, (w, d), s['floor'] - 120, h + 120, RIM, TOP,
                         facing=fac, top_size=[mult(w * 0.45, q), mult(d * 0.5, q)],
                         notes="Crags on the rim (the look pass: no flat plate)." if not out and sid == ISLANDS[0]
                         else None))
    return out


def skirts(sid):
    """Cloud wreathing the rock under the rim: puffs along the rim, their tops 90-260 under the island's floor,
    untouchable (solid: false: drawn, and a party walking off the edge falls through them)."""
    s = SPACE[sid]
    poly = [tuple(p) for p in TOPS[sid]]
    rnd = random.Random(53 * s['seed'])
    out = []
    # F62 (2026-11-25): two overlapping skirts' tilted tops (or a skirt's and the first tier's ledge) crossed at a
    # shallow angle, a flickering seam (check_floor_cross floor.cross): a skirt whose height band meets one it
    # overlaps goes under it. (outline, lowest top, highest top) of what is laid.
    laid = island_layers(sid)
    for k, (p, n) in enumerate(PG.outline_samples(poly, 520)):
        if rnd.random() < 0.18:
            continue
        r = rnd.uniform(200, 380)
        c = (p[0] + n[0] * rnd.uniform(-40, 140), p[1] + n[1] * rnd.uniform(-40, 140))
        top = s['floor'] - rnd.uniform(90, 260) - 3 * k - 0.5   # odd offsets: no two skirts share a plane
        rise = rnd.uniform(140, 300)
        pts = ccw(ring(c[0], c[1], r, 10, rnd.uniform(0, 1), ry=r * rnd.uniform(0.7, 1.0)))
        ph = rnd.uniform(0, 2 * math.pi)
        hs = [int(rise * (0.92 + 0.08 * math.cos(2 * math.pi * j / len(pts) + ph))) for j in range(len(pts))]   # a tilted top
        top = clear_band(pts, top, max(hs) - min(hs), laid)
        laid.append((pts, top - (max(hs) - min(hs)), top))
        out.append({'id': f'platform:{key(sid)}_cloud{len(out) + 1}', 'outline': [ipt(v) for v in pts],
                    'base': int(round(top - rise - FLOOR)), 'rise': min(hs), 'top_heights': hs,
                    'surface': CLOUD_SIDE, 'top_surface': CLOUD_TOP, 'bottom_surface': CLOUD_SIDE, 'solid': False})
    if out:
        out[0]['notes'] = "Cloud skirts under the rim (untouchable: a party falls through them)."
    return out


def island_layers(sid):
    """(outline, lowest, highest) of an island's flat faces a cloud must keep clear of: the top slab's bottom and the
    first tier's ledge (F62)."""
    fl = SPACE[sid]['floor']
    tier = [tuple(v) for v in rough_outline(sid, TIERS[0][0], seed=1, points=20, out_amp=(-60, 120), hold=0)]
    return [([tuple(v) for v in TOPS[sid]], fl - SLAB, fl - SLAB), (tier, fl - SLAB + 8, fl - SLAB + 8)]


def clear_band(pts, top, band, laid):
    """Lower a cloud's top (its tilted top spans `band` under it) under anything laid it overlaps whose heights its
    own meet within 8: two crossing tops flicker (F62, check_floor_cross floor.cross)."""
    for _ in range(len(laid)):
        hit = [lo for q, lo, hi in laid if lo - 8 < top and top - band < hi + 8 and polys_meet(pts, q)]
        if not hit:
            break
        top = min(hit) - 8.5
    return top


def skirt_layers():
    """Every island's layers and skirts (outline, lowest, highest), for the bridges' wisps."""
    out = []
    for sid in ISLANDS:
        out += island_layers(sid)
        for e in skirts(sid):
            z = e['base'] + FLOOR
            out.append(([tuple(v) for v in e['outline']], z + min(e['top_heights']), z + max(e['top_heights'])))
    return out


def polys_meet(a, b):
    """Two outlines overlap (a corner of one inside the other, or their middles inside each other)."""
    ca = (sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a))
    cb = (sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b))
    return (any(PG.point_in(p, b) for p in a) or any(PG.point_in(p, a) for p in b) or PG.point_in(ca, b)
            or PG.point_in(cb, a))


# ------------------------------------------------------------------------------------------------ bridges
INTO = 192


def link_cut(l):
    p, q = PL.link_ends(l)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * INTO, p[1] - uy * INTO), (q[0] + ux * INTO, q[1] + uy * INTO), d


def bridges():
    out = []
    rnd = random.Random(808)
    laid = skirt_layers()
    for l in D['links']:
        if l.get('gate'):
            continue
        a, b, d = link_cut(l)
        za, zb = FLOOR_OF[l['a']] + 4, FLOOR_OF[l['b']] + 4
        # F62: level across each island until past its rim, sloping between (it dipped under the higher island's
        # top before the rim: check_floor_cross floor.cross)
        spans = SP.link_spans(a, b, za, zb, l['width'], [tuple(v) for v in TOPS[l['a']]],
                              [tuple(v) for v in TOPS[l['b']]])
        base = f"platform:{key(l['id'])}"
        ids = [base] if len(spans) == 1 else ([base + '_a', base, base + '_b'] if len(spans) == 3 else
                                              ([base + '_a', base] if spans[0][2] == spans[0][3] else [base, base + '_b']))
        for pid, (p, q, z0, z1) in zip(ids, spans):
            out.append(slab(pid, p, q, z0, z1, l['width'], MARBLE, MARBLE, 96,
                            notes=f"{l['id']}: a bridge of cloud-stone over the sky, {int(d):,} rim to rim, rising "
                                  f"{zb - za}; level over each island (F62)." if pid == base else None))
        # wisps of cloud under the deck (untouchable)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        for k in range(3):
            t = (k + 1) / 4 + rnd.uniform(-0.08, 0.08)
            c = (a[0] + u[0] * L * t - u[1] * rnd.uniform(-120, 120), a[1] + u[1] * L * t + u[0] * rnd.uniform(-120, 120))
            zt = SP.span_top(spans, (a[0] + u[0] * L * t, a[1] + u[1] * L * t)) - 96 - rnd.uniform(60, 200) - 5 * k - 1.5
            r = rnd.uniform(240, 380)
            pts = ccw(ring(c[0], c[1], r, 10, rnd.uniform(0, 1), ry=r * 0.7))
            rise = rnd.uniform(120, 220)
            ph = rnd.uniform(0, 2 * math.pi)
            hs = [int(rise * (0.92 + 0.08 * math.cos(2 * math.pi * j / len(pts) + ph))) for j in range(len(pts))]   # a tilted top
            zt = clear_band(pts, zt, max(hs) - min(hs), laid)
            laid.append((pts, zt - (max(hs) - min(hs)), zt))
            out.append({'id': f"platform:{key(l['id'])}_wisp{k + 1}", 'outline': [ipt(v) for v in pts],
                        'base': int(round(zt - rise - FLOOR)), 'rise': min(hs), 'top_heights': hs,
                        'surface': CLOUD_SIDE, 'top_surface': CLOUD_TOP, 'bottom_surface': CLOUD_SIDE, 'solid': False})
    return out


# ------------------------------------------------------------------------------------------------ the Eye, the stair
EYE = SPACE['room:arena']
EYE_AT = EYE['at']
EYE_FL = EYE['floor']
AERIE = SPACE['room:chamber']
AERIE_FL = AERIE['floor']
STAIR_X = PLACE['gate:sleeper']['at'][0]          # 3968: straight north from the gate
STAIR_W = 768                                      # L1 (cheeks included)
CHEEK_W = 64
GATE_W = STAIR_W - 2 * CHEEK_W                     # 640 between the cheeks
STEPS = 16                                         # 32 each, 256 -> 768
CHEEK_OVER = 224                                   # the cheeks' tops over the stair's line


def rim_y_north(sid, x):
    s = SPACE[sid]
    poly = PG.blob(s, points=48)
    p = PG.ray_exit(poly, (x, s['at'][1]), (x, s['at'][1] + 20000))
    return p[1]


def rim_y_south(sid, x):
    s = SPACE[sid]
    poly = PG.blob(s, points=48)
    p = PG.ray_exit(poly, (x, s['at'][1]), (x, s['at'][1] - 20000))
    return p[1]


GATE_Y = int(rim_y_north('room:arena', STAIR_X)) - 48      # the curtain's line, just inside the Eye's rim
HEAD_Y = int(rim_y_south('room:chamber', STAIR_X)) + INTO  # the last step runs into the aerie
STAIR_FOOT = (STAIR_X, GATE_Y)
STAIR_HEAD = (STAIR_X, HEAD_Y)


def stair():
    """The Stair of Wind: sixteen steps of 32, cheeks of pale brick on both sides (P-2), from the curtain north."""
    out = []
    y0 = GATE_Y + 16
    run = (HEAD_Y - y0) / STEPS
    for k in range(STEPS):
        top = EYE_FL + 32 * (k + 1) + (4 if k == STEPS - 1 else 0)
        ya, yb = y0 + run * k, y0 + run * (k + 1)    # abutting (no coplanar overlap)
        out.append(block(f'platform:stair{k + 1}', (STAIR_X, (ya + yb) / 2), (GATE_W, yb - ya), top - 120, 120,
                         MARBLE, MARBLE, bottom_surface=CLOUD_SIDE,
                         notes="The Stair of Wind: cloud-stone steps of 32 to the Sleeper's Aerie." if k == 0 else None))
    for k, sgn in enumerate((-1, 1)):
        x = STAIR_X + sgn * (GATE_W / 2 + CHEEK_W / 2)
        a, b = (x, GATE_Y - 16), (x, HEAD_Y - INTO)
        z0 = EYE_FL + 32 + CHEEK_OVER + 32
        z1 = AERIE_FL + CHEEK_OVER
        out.append(slab(f'platform:stair_cheek{k + 1}', a, b, z0, z1, CHEEK_W, BRICK, MARBLE, CHEEK_OVER + 160 + 32,
                        bottom=CLOUD_SIDE,
                        notes=(f"The stair's cheeks (P-2): {CHEEK_OVER - 32} or more over every step, "
                               f"{z0 - EYE_FL} over the Eye's floor at the foot.") if k == 0 else None))
    return out


GATE_STONE = (256, 448)          # across, along the stair (overhanging the rim)
GATE_STONE_H = 640
CURTAIN_H = 576


def gate():
    out = []
    for k, sgn in enumerate((-1, 1)):
        x = STAIR_X + sgn * (GATE_W / 2 + GATE_STONE[0] / 2 - 32)
        out.append(block(f'platform:gate_stone{k + 1}', (x, GATE_Y + GATE_STONE[1] / 2 - 160), GATE_STONE,
                         EYE_FL - 96, GATE_STONE_H + 96, MENHIR, MENHIR, top_size=[208, 384],
                         notes="The gate's standing stones, two of the Eye's twelve, either side of the stair's foot."
                         if k == 0 else None))
    out.append(block('platform:wind_curtain', (STAIR_X, GATE_Y - 32), (GATE_W, 32), EYE_FL, CURTAIN_H, WIND_CURTAIN,
                     WIND_CURTAIN, bottom_surface=WIND_CURTAIN,
                     notes=("The curtain of wind between the gate's stones (gate:sleeper): solid until qbit 111765, then "
                            "passable and hidden (evt:gate_open, evt:passed_load).")))
    return out


RING_R = 1380
RING_DEG = [200, 228, 256, 284, 312, 340, 8, 36, 62, 150]


def standing_stones():
    out = []
    rnd = random.Random(1212)
    for k, deg in enumerate(RING_DEG):
        th = math.radians(deg)
        at = (EYE_AT[0] + RING_R * math.cos(th), EYE_AT[1] + RING_R * math.sin(th))
        fac, q = snap_facing(deg + 90)
        w, d = mult(224, q), mult(150, q)
        h = rnd.uniform(420, 600)
        out.append(block(f'platform:eye_stone{k + 1}', at, (w, d), EYE_FL - 64, h + 64, MENHIR, MENHIR, facing=fac,
                         top_size=[mult(w * 0.75, q), mult(d * 0.8, q)],
                         notes="The Eye's standing stones (twelve with the gate's two)." if k == 0 else None))
    out.append(block('platform:eye', EYE_AT, (768, 768), EYE_FL - SINK, 2 + SINK, MARBLE, MARBLE, facing=0,
                     notes="The eye: a calm circle of cloud-stone where the guardians form (landmark:eye)."))
    tp = PLACE['poi:test']['at']
    out.append(block('platform:test_plate', (tp[0] + 96, tp[1]), (256, 256), EYE_FL - SINK,
                     plate_top((tp[0] + 96, tp[1]), EYE_FL, 128) - EYE_FL + SINK, MARBLE, MARBLE,
                     notes="The test's floor before S's pedestal (poi:test): stepping on asks 'Accept the test of Air?'."))
    return out


# ------------------------------------------------------------------------------------------------ the aerie
DOME_AT = (4736, 3712)           # over the couch (poi:sleeper (4864, 3840)), pulled in from the rim


def dome():
    out = []
    poly = TOPS['room:chamber']
    for k in range(6):
        th = math.radians(30 + 60 * k)
        at = (DOME_AT[0] + 512 * math.cos(th), DOME_AT[1] + 512 * math.sin(th))
        if not inside_by(at, poly, 96):
            continue
        out.append(block(f'platform:dome_column{k + 1}', at, (96, 96), AERIE_FL, 704, BRICK, BRICK,
                         notes="The aerie's open dome: six columns of pale brick." if k == 0 else None))
    z = AERIE_FL + 704
    for k, (r, h) in enumerate(((672, 64), (544, 96), (400, 96), (224, 80))):
        out.append(prism(f'platform:dome{k + 1}', ring(DOME_AT[0], DOME_AT[1], r, 16, 0.2), z, h, BRICK, TOP,
                         bottom_surface=MARBLE,
                         notes="The dome, stepping in (open on all sides)." if k == 0 else None))
        z += h - 8
    dp = PLACE['exit:dais']['at']
    out.append(prism('platform:dais', ring(dp[0], dp[1], 224, 12), AERIE_FL - SINK, 8 + SINK, MARBLE, MARBLE,
                     notes="The return dais (exit:dais): shown once the Air Sleeper is awake (qbit 111761)."))
    return out


# ------------------------------------------------------------------------------------------------ devices
def nudge_in(p, sid, margin):
    """p moved toward its island's middle until it stands `margin` inside the rim."""
    c = SPACE[sid]['at']
    poly = TOPS[sid]
    for t in [i / 40 for i in range(41)]:
        q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
        if inside_by(q, poly, margin):
            return ipt(q)
    return ipt(c)


WAY_UP = None
CAIRN = None


def devices():
    out = []
    # the updraft: a disc of wind in a ring of white stones
    wx, wy = WAY_UP
    out.append(prism('platform:way_up', ring(wx, wy, 176, 12), -SINK, 4 + SINK, MARBLE, WIND,
                     notes="The updraft (exit:way_up): wind blowing straight up in a ring of white stones."))
    for k in range(8):
        th = 2 * math.pi * (k + 0.5) / 8
        at = (wx + 288 * math.cos(th), wy + 288 * math.sin(th))
        fac, q = snap_facing(math.degrees(th))
        out.append(block(f'platform:way_up_stone{k + 1}', at, (mult(80, q), mult(80, q)), -40, 200 + 40 * (k % 3),
                         MARBLE, MARBLE, facing=fac, top_size=[mult(48, q), mult(48, q)]))
    # the Singing Stones
    sx, sy = PLACE['poi:singing_stones']['at']
    for k in range(7):
        th = 2 * math.pi * k / 7 + 0.3
        at = (sx + 560 * math.cos(th), sy + 560 * math.sin(th))
        out.append(block(f'platform:singing{k + 1}', at, (448, 128), FLOOR_OF['room:stones'] - 32, 448 + 64 * (k % 2),
                         HOLLOW, MENHIR, facing=math.degrees(th) + 90, end_surface=dict(MENHIR, fit=False),
                         notes="The Singing Stones: a ring of hollow stones (MM8's pierced gwspout, once per face)."
                         if k == 0 else None))
    # the storm cairn: three stones fused into one
    cx, cy = CAIRN
    fl = FLOOR_OF['room:statue']
    for k, (s, h, dx, dy) in enumerate(((300, 180, 0, 0), (220, 160, 30, -20), (130, 140, 10, 10))):
        fac, q = snap_facing(25 * k + 10)
        z = fl - 24 + sum(x[1] - 24 for x in ((300, 180), (220, 160), (130, 140))[:k])
        out.append(block(f'platform:cairn{k + 1}', (cx + dx, cy + dy), (mult(s, q), mult(s * 0.9, q)), z, h, UNDER,
                         UNDER, facing=fac, top_size=[mult(s * 0.7, q), mult(s * 0.6, q)],
                         notes="The storm cairn: three stones fused by lightning (poi:storm_cairn)." if k == 0 else None))
    # the statue of Air's plinth (the statue itself is S's)
    out.append(block('platform:plinth', PLACE['poi:statue']['at'], (448, 448), fl, 96, MARBLE, MARBLE,
                     notes="The plinth of the statue of Air in the middle of its island (S's statue stands on it)."))
    return out


def deck_top(c, half):
    """The highest bridge deck top over a square of `half` round c, or None (F62: a plate on a bridge's landing lay in
    its plane: geometry.coplanar)."""
    best = None
    for e in bridges():
        if 'size' not in e:
            continue
        f = math.radians(e['facing'])
        for dx in (-half, 0, half):
            for dy in (-half, 0, half):
                pt = (c[0] + dx, c[1] + dy)
                if not PG.point_in(pt, foot(e)):
                    continue
                z = FLOOR + e['base'] + e['rise']
                if 'top_heights' in e:
                    u = ((pt[0] - e['at'][0]) * math.cos(f) + (pt[1] - e['at'][1]) * math.sin(f)) / e['size'][0] + 0.5
                    h = e['top_heights']
                    z = FLOOR + e['base'] + h[0] + (h[1] - h[0]) * u
                best = z if best is None else max(best, z)
    return best


def plate_top(c, z, half):
    """A plate's top: 4 over its island, or over a bridge's landing it lies on."""
    d = deck_top(c, half)
    return max(z, d if d is not None else z) + 4


def storm_plates():
    out = []
    for i, c in enumerate(D['hazard']['cells']):
        z = FLOOR_OF[PL.space_of(c)]
        out.append(block(f'platform:storm{i + 1}', c, (192, 192), z - SINK, plate_top(c, z, 96) - z + SINK, RIM, SCORCH,
                         notes="A storm cell (D-58 P2 Q2): a PressurePlate face, xpascorch, planes.storm." if i == 0
                         else None))
    return out


# ------------------------------------------------------------------------------------------------ rooms.yml
def room_outline():
    hx, hy = PL.half
    return [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]


def build_rooms():
    platforms = []
    for sid in ISLANDS:
        platforms += island(sid) + crags(sid) + skirts(sid)
    platforms += bridges() + stair() + gate() + standing_stones() + dome() + devices() + storm_plates()
    for p in platforms:
        if p.get('notes') is None:
            p.pop('notes', None)
    room = {
        'id': 'room:air', 'space': 'void:sky', 'name': 'The Plane of Air', 'outline': room_outline(),
        'floor': FLOOR, 'ceiling': CEIL, 'theme': 'theme:air', 'platforms': platforms,
        'notes': ("The open sky of the Plane of Air: one room from the safety floor at -6,000 to the sky at 4,096, every "
                  "wall, floor and ceiling face a sky face. The islands hang in it as rough floating rock (ragged rims, "
                  "tiers and roots under them, crags on the rims, cloud skirts), linked by cloud-stone bridges and the "
                  "Stair of Wind."),
    }
    return {'format': 0, 'themes': [{'id': 'theme:air', 'wall': SKY, 'floor': SKY, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:air', 'ambient': 30}, 'rooms': [room]}


# ------------------------------------------------------------------------------------------------ objects.yml
def spread(at, n, r=224):
    if n == 1:
        return [at]
    return [(at[0] + r * math.cos(2 * math.pi * k / n), at[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def obstacles():
    """Footprints a monster must not stand in (stones, columns, crags, devices)."""
    out = []
    for p in ROOMS['rooms'][0]['platforms']:
        pid = p['id']
        if any(w in pid for w in ('_stone', 'crag', 'singing', 'cairn', 'column', 'plinth', 'way_up')):
            out.append([tuple(v) for v in foot(p)])
    return out


def clear_spot(q, obs, pad=128):
    return all(not PG.point_in(q, o) and poly_dist_outline(q, o) > pad for o in obs)


def objects():
    arr = PLACE['entrance:d7_fall']
    start = {'room': 'room:air', 'at': ipt(arr['at']), 'floor_height': 0, 'facing': arr['face'],
             'notes': "entrance:d7_fall on the Gale Landing, facing north-east (Xeen.PlaneArrivals.air, Xeen.SkyFalls.p2)."}
    obs = obstacles()
    monsters = []
    for gi, g in enumerate(D['groups']):
        row = PD.ROWS[g['row']]
        z = FLOOR_OF[g['space']]
        poly = TOPS[g['space']]
        c = SPACE[g['space']]['at']
        for k, p in enumerate(spread(g['at'], g['count'])):
            q = p
            for t in [i / 20 for i in range(21)]:
                q = (p[0] + (c[0] - p[0]) * t, p[1] + (c[1] - p[1]) * t)
                if inside_by(q, poly, 128) and clear_spot(q, obs) and all(math.hypot(q[0] - m['at'][0], q[1] - m['at'][1]) > 180 for m in monsters):
                    break
            e = {'id': f"monster:{key(g['id'])}_{k + 1}", 'room': 'room:air', 'monster': row['id'], 'at': ipt(q),
                 'floor_height': int(z), 'facing': 0, 'hostile': True, 'group': gi + 1}
            if k == 0:
                e['notes'] = f"{g['id']}: {g['count']} {row['short']} ({row['level']})."
            monsters.append(e)
    k = 0
    for g in D['test_group']:
        row = PD.ROWS[g['row']]
        for j in range(g['count']):
            k += 1
            at = EYE_AT if k == 1 else (EYE_AT[0] + (k - 2.5) * 2 * 256, EYE_AT[1] - 160)
            monsters.append({'id': f'monster:guardian_{k}', 'room': 'room:air', 'monster': row['id'], 'at': ipt(at),
                             'floor_height': EYE_FL + 2, 'facing': 180, 'hostile': True, 'group': GUARD_GROUP,
                             'hidden': True,
                             'notes': (f"{row['short']} ({row['level']}): the test's hidden group {GUARD_GROUP} in the "
                                       "eye, shown by evt:test (D-58 C3).")})
    chests = [
        {'id': 'chest:test', 'room': 'room:air', 'at': ipt(PLACE['poi:test_chest']['at']), 'floor_height': AERIE_FL,
         'kind': 'ch3', 'facing': 's', 'treasure_level': 6, 'random_items': 3, 'gold': 2500,
         'notes': "The test's chest (aaze0026:4 'Chest'): the source's gold and three items, in the aerie past the gate."},
        {'id': 'chest:basket_cache', 'room': 'room:air', 'at': ipt(PLACE['poi:basket_cache']['at']),
         'floor_height': FLOOR_OF['room:kite_isle'], 'kind': 'ch1', 'facing': PLACE['poi:basket_cache']['face'],
         'treasure_level': 6, 'random_items': 2, 'gold': 1200, 'trap_level': 8,
         'notes': ("The balloonist's cache: his strongbox wedged in the basket's rocks (trapped), 209 north-west of "
                   "the basket's middle, off the way from the bridge (session 25; it stood 1,400 away before).")},
    ]
    bx, by = PLACE['poi:basket']['at']
    items = [{'id': f'item:basket_potion{i + 1}', 'room': 'room:air', 'item': 257, 'at': [bx + dx, by + dy],
              'floor_height': FLOOR_OF['room:kite_isle']} for i, (dx, dy) in enumerate(((96, -64), (160, 0)))]
    items[0]['notes'] = "The basket's find: Air Resistance (257)."
    return {
        'format': 1, 'start': start,
        # AU's plane bed (devdocs/xeen/AUDIO.md session 5, "The lines to paste"; D-48 `pan: false`)
        'sounds': [{'id': 'sound:plane_bed', 'room': 'room:air', 'at': [0, 0], 'height': 512, 'sound': 'xeen_amb_plane_air', 'radius': 16000, 'inner_radius': 11000, 'volume': 0.4, 'pan': False}],
        'arrivals': [{'entrance': 'entrance:d7_fall', 'room': 'room:air', 'at': ipt(arr['at']), 'floor_height': 0,
                      'facing': arr['face'], 'notes': "The drop from D7's north-east corner (Xeen.toPlane('air')); "
                                                      "falls land here too (Xeen.skyFallTo('p2'))."}],
        'chests': chests, 'items': items, 'monsters': monsters, 'decorations': pieces(),
        'notes': ("P2 L4 objects (generated by output/studio_cal/p2/tools/gen.py): 27 placed hostiles in 10 groups "
                  f"and the test's three in the hidden group {GUARD_GROUP}; two chests at treasure 6; the basket's "
                  "find; S's pieces (session 20): sleeper and couch, statue, pedestal, return dais (hidden until he wakes), "
                  "updraft; S's wrecked basket (session 25). No lights."),
    }


def pieces():
    """S's pieces (D-58 C7, session 20; level_generation/decorations/xeen_planes_claude/README.md). The couch stands
    on the aerie's floor under the dome (the dome's rings are floors over it)."""
    tp = PLACE['poi:test']['at']
    return PC.decorations(
        'air', 'room:air',
        sleeper=(DOME_AT, 225, AERIE_FL), statue=(PLACE['poi:statue']['at'], 225, None),
        pedestal=((tp[0] + 96, tp[1] + 208), 270, None), dais=(PLACE['exit:dais']['at'], 0, None),
        way_up=(WAY_UP, 0, None),
        extra=(PC.deco('basket', 'room:air', 'xeen_balloonbasket', PLACE['poi:basket']['at'], 0,
                       FLOOR_OF['room:kite_isle'],
                       notes=("The wrecked basket (S, row 4058; radius 64, solid) on Kite Isle, its raised side on the "
                              "rocks to the north; clicked, A3's planes.basket (the logbook). The find lies 115 and "
                              "160 from its middle, the cache 209 north-west.")),))


# ------------------------------------------------------------------------------------------------ wiring.yml
def wiring():
    ev = []
    ev.append({'id': 'evt:test', 'preset': 'script', 'trigger': 'step', 'source': 'platform:test_plate',
               'condition': {'all': [{'not': {'qbit': 'm38_air_test'}}, {'not': {'map_var': 'test_accepted'}}]},
               'question': {'ask': 'Accept the test of Air?', 'answers': ['Yes', 'Y']},
               'effects': [{'lua': 'XeenQuests.hook("m38.test_air")'}, {'show_actors': GUARD_GROUP},
                           {'set': {'var': {'map_var': 'test_accepted'}, 'value': 1}}],
               'notes': ("D-58 C3: the test (aaze0026:5). Yes: A3's m38.test_air line, the guardians form in the eye "
                         f"(group {GUARD_GROUP} shown); any other answer does nothing. Not asked again while they live.")})
    ev.append({'id': 'evt:test_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'map_var': 'test_accepted'}, {'not': {'qbit': 'm38_air_test'}}]},
               'lua': f'Xeen.planeTestCheck("air", {GUARD_GROUP})',
               'notes': ("A3's killed-group check (xeen_common.lua): once the three guardians are dead it runs "
                         "m38.test_air_passed, which sets qbit 111765 (P-1) with its line.")})
    still = [{'passable': 'platform:wind_curtain'}, {'hide': 'platform:wind_curtain'}]
    ev.append({'id': 'evt:gate_open', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'condition': {'all': [{'qbit': 'm38_air_test'}, {'not': {'map_var': 'gate_open'}}]},
               'effects': still + [{'text': 'The wind between the stones falls still.'},
                                   {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': 'The curtain of wind stills the second the qbit is set (C4).'})
    ev.append({'id': 'evt:passed_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm38_air_test'},
               'effects': still + [{'hide_actors': GUARD_GROUP}, {'set': {'var': {'map_var': 'gate_open'}, 'value': 1}}],
               'notes': ("P-1: the load event reads qbit 111765: the curtain stilled, the guardians hidden, the eye "
                         "quiet (through refills and the reset after a map rebuild).")})
    ev.append({'id': 'evt:gate', 'preset': 'script', 'source': 'platform:wind_curtain', 'title': 'A wall of wind',
               'effects': [{'text': 'The wind between the stones roars and throws you back.'}],
               'notes': 'Clicked: the curtain of wind does not let anyone through before the test.'})
    ev.append({'id': 'evt:dais_hide', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': 'm38_air'}},
               'effects': [{'hide': 'platform:dais'}, {'passable': 'platform:dais'}],
               'notes': "C5: the return dais shows once the Air Sleeper is awake (qbit 111761, m38.sleeper_air)."})
    ev += PC.dais_events('air', 'm38_air')
    ev.append(PC.sleeper_event('air'))
    ev.append({'id': 'evt:storm', 'preset': 'script', 'trigger': 'step', 'source': 'platform:storm1',
               'sources': [f'platform:storm{i}' for i in range(2, 10)],
               'lua': 'XeenQuests.hook("planes.storm")',
               'notes': ("D-58 P2 Q2: A3's planes.storm (one time in three, 50 electrical to each member, 'Lightning "
                         "strikes from a clear sky!').")})
    for k in range(7):
        ev.append({'id': f'evt:singing{k + 1}', 'preset': 'script', 'source': f'platform:singing{k + 1}',
                   'title': 'The Singing Stones', 'lua': 'XeenQuests.hook("planes.singing_stones")',
                   'notes': "A3's planes.singing_stones (once a day, +20 Air resistance and +10 Speed)." if k == 0
                   else 'The same, another stone.'})
    ev.append({'id': 'evt:cairn', 'preset': 'script', 'source': 'platform:cairn1', 'title': 'A cairn of fused stones',
               'lua': 'XeenQuests.hook("planes.cairn")',
               'notes': "A3's planes.cairn: the first time a blue gem in the glass (map variable p2_cairn)."})
    ev.append({'id': 'evt:plaque', 'preset': 'script', 'source': 'platform:plinth', 'title': 'Plaque',
               'lua': 'XeenQuests.hook("m38.plaque_air")',
               'notes': "A3's m38.plaque_air: 'Step Two' at the base of the statue (the statue on it is S's)."})
    ev.append(PC.copy_for(ev[-1], 'statue', 'evt:plaque_statue'))
    ev.append({'id': 'evt:chest_test', 'preset': 'chest', 'source': 'chest:test', 'title': 'Chest',
               'notes': "The test's chest (aaze0026:4)."})
    ev.append({'id': 'evt:basket', 'preset': 'script', 'source': 'deco:basket', 'title': 'The basket with no balloon',
               'lua': 'XeenQuests.hook("planes.basket")',
               'notes': "A3's planes.basket: the balloonist's logbook."})
    ev.append({'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:basket_cache', 'title': 'Chest',
               'notes': "The balloonist's cache (trapped)."})
    ev.append({'id': 'evt:fall_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'lua': f'local x, y, z = evt.GetPartyPosition()\nif z > {FALL_Z} then return end\nXeen.skyFallTo("p2")',
               'notes': ("set:fall (D-58 P2 Q1): a party under -1,500 has fallen off the islands; A3's "
                         "Xeen.skyFallTo('p2') sets it down on the Gale Landing (entrance:d7_fall) from 850 above, "
                         "with falling damage.")})
    ev.append({'id': 'evt:fall_floor', 'preset': 'script', 'trigger': 'step', 'source': 'room:air',
               'lua': 'Xeen.skyFallTo("p2")',
               'notes': "The safety floor at -6,000: a fall the one-second check missed lands the same way."})
    if D7_LIVE:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The updraft',
                   'effects': [{'lua': PC.d7_return_lua('air')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': ("D-58 C5: the way up, always open, to D7's entrance:p2_return; A3's m38.way_up_air is "
                             "its question.")})
        ev.append({'id': 'evt:dais', 'preset': 'script', 'source': 'platform:dais', 'title': 'The return dais',
                   'condition': {'qbit': 'm38_air'}, 'locked_text': 'The dais is dark and still.',
                   'effects': [{'lua': PC.d7_return_lua('air')}],   # s32 (F16): the entrance window, no Yes/No
                   'notes': "D-58 C5: the dais after the sleeper, to D7's entrance:p2_return (A3's m38.dais_air)."})
        ev.append(PC.copy_for(ev[-1], 'dais', 'evt:dais_disc'))
        ev.append(PC.copy_for(next(e for e in ev if e['id'] == 'evt:way_up'), 'way_up', 'evt:way_up_column'))
    else:
        ev.append({'id': 'evt:way_up', 'preset': 'script', 'source': 'platform:way_up', 'title': 'The updraft',
                   'effects': [{'text': 'The wind blows straight up into the blue. (The Skyroads are not open yet.)'}],
                   'notes': "Sealed until xeen_d7.blv is installed and lists entrance:p2_return."})
    return {'format': 0, 'variables': ['test_accepted', 'gate_open', 'dais_shown'], 'events': ev}


# ------------------------------------------------------------------------------------------------ plan, project
def load(level, name):
    return yaml.safe_load(open(BRIEF / level / name))


def plan(level):
    p = load('L1', 'plan.yml')
    p['level'] = level
    p['notes'] = (p['notes'] + " L2-L4 (A6's planes sub-agent, sixteenth session, 2026-11-21): built by "
                  "output/studio_cal/p2/tools/gen.py; the islands rough floating rock with cloud skirts; the gate a "
                  "curtain of wind between two standing stones made passable on qbit 111765; the Stair of Wind's "
                  "cheeks keep P-2; S's pieces blocked by name.")
    return p


def project(level):
    p = load('L1', 'project.yml')
    for n in p['neighbours']:
        if n['id'] in ('exit:d7_way_up', 'exit:d7_dais') and not D7_LIVE:
            n.pop('arrival', None)
            n.pop('arrival_hint', None)
            n['notes'] = n['notes'] + " Sealed until xeen_d7.blv is installed and names entrance:p2_return."
    p['new'] = False
    p['notes'] = (f"Xeen design brief, level {level}: P2 Plane of Air of Xeen, an open-air BLV (devdocs/"
                  "INDOOR_OPEN_SKY.md; X9's and P5's route) built with the studio (profile region): one room of open "
                  "sky (plane_air) with six floating islands, bridges and the Stair of Wind. map_stats 9116 (A2's row), "
                  "music 9, treasure 6; Air rows 11624, 11700-11702; hooks: A3's m38.*_air, planes.storm, "
                  "planes.singing_stones, planes.cairn, planes.basket, Xeen.planeTestCheck, Xeen.skyFallTo('p2').")
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
TOPS = {sid: rough_outline(sid) for sid in ISLANDS}
WAY_UP = nudge_in(PLACE['exit:way_up']['at'], 'room:landing', 400)
CAIRN = nudge_in(PLACE['poi:storm_cairn']['at'], 'room:statue', 320)
WALK = walk_lines() + [(STAIR_FOOT, STAIR_HEAD, STAIR_W / 2 + 64)]
KEEP = ([(p['at'], 420) for p in PLACE.values()] + [(g['at'], 400) for g in D['groups']]
        + [(c, 260) for c in D['hazard']['cells']] + [(WAY_UP, 480), (CAIRN, 360), (DOME_AT, 760)]
        + [(PLACE['poi:test']['at'], 500)])
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
    print('platforms', len(ps), 'monsters', len(objs['monsters']), 'D7 live', D7_LIVE, 'gate y', GATE_Y, 'head y',
          HEAD_Y, 'way up', WAY_UP, 'cairn', CAIRN)
