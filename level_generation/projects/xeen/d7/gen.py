#!/usr/bin/env python3
"""D7 The Skyroads: writes the L3 and L4 rooms.yml (A6 sub-agent, sixteenth session, 2026-11-21), after X9's and
P5's gen.py (A5's open-air BLVs of clouds).

One open-air room (room:air) from the safety floor at -6000 to the sky at 6400; its walls, floor and ceiling are sky
faces. The design is the L1's with D-58 applied (level_generation/xeen_art/phase6/d7_design.py, its D-58 block) and the
outlines are the L1 review's own (d7_geom.cloud_poly), so the spans and the spacing measured at L1 are the ones built.

- Every island a hanging cloud (cloud top `xccloud`, sides `xccloudsd`) with two or three flared roots.
- The Skyroad's links cloud slabs with a paved band of cloud-stone flags (`7tws1f`) 256 wide down the middle (D-8);
  the spurs and the dragon road plain cloud; the causeways to Olympus marble-flagged (`7tws1f`) on a cloud tongue;
  rope bridges plank decks (`t66floor`) with rope rails (`hwm2rf`), as X8's and X9's.
- The four corners: a cloud spit out to the tip (corners.yml) ending in a marble disc where the sky asks.
- Olympus: a marble-paved cloud with a low balustrade, three gates of open gilded posts (D-8: no leaves, no griffin
  statues), the houses of A4's d7.yml on XD-17's town route (a block per house, its door a clicked block), the temple
  with its portico and gold dome on the square's north side, Soul Storage's vault, Lucio's jetty.
- Boards on P5's blank face `xp5brd`, the Rest Stop huts with P5's `xp5rest` sign (D-7: text on hover only).
- Roof hatches as flat plates of weathered metal (`gn_mtl03`), the Pyramid's capstone with its sky door (`xdpyrdor`), the
  Megadragon's crag, the Sky Lake's water, the scarab stalls, the merchants' barges, the toll booths.

    python3 level_generation/projects/xeen/d7/gen.py     # writes devdocs/xeen/briefs/d7/L3 and L4 rooms.yml (+ L3's start)
"""
import math
import random
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'level_generation/xeen_art/phase6'))
import d7_design as D  # noqa: E402
import d7_geom as G  # noqa: E402

BRIEF = ROOT / 'devdocs/xeen/briefs/d7'
WORLD = ROOT / 'assets_dev/worlds/xeen'

FLOOR = -6000          # the safety floor: a fall the one-second check misses ends here and runs the same fall
CEIL = 6400
SLAB = 256             # a cloud's slab under its top

# ------------------------------------------------------------------------------------------------ textures
CLOUD_TOP = {'texture': 'xccloud', 'size': [256, 256], 'scale': 2}
CLOUD_SIDE = {'texture': 'xccloudsd', 'size': [256, 256], 'scale': 2, 'uneven': True}
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}
FLAG = {'texture': '7tws1f', 'size': [128, 128]}                 # cloud-stone flags (X9's road, P5's band)
MARBLE = {'texture': '7tws1f', 'size': [128, 128], 'scale': 2}   # Olympus' paving and causeways
PLANK = {'texture': 't66floor', 'size': [128, 128]}
ROPE = {'texture': 'hwm2rf', 'size': [128, 128]}                 # X8's rope rails
WALL = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 3}    # pale temple ashlar (MM8; P5's observatory), once up 768
WALL_T = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 4}   # the temple's, once up 1,024
PLINTH = {'texture': 'hwm1b', 'size': [128, 256]}                # Celeste's footing band: balustrade, plinths
STONE = {'texture': 'gtempw1', 'size': [128, 256]}               # the same ashlar at its size: columns, jetties, ends
CANVAS_ROOF = {'texture': 'tentrf1', 'size': [256, 256], 'scale': 2}   # P5's white canvas roof (awnings, lean-to)
METAL = {'texture': 'gn_mtl03', 'size': [128, 128], 'scale': 2}  # the hatches' weathered metal (P5's dome)
PANEL = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 3}   # the vault
ROOF = {'texture': 'hwm2rf', 'size': [128, 128], 'scale': 2}
GOLD = {'texture': 'ctflor5', 'size': [128, 128], 'scale': 0.5}  # gilt (P5's pavilion posts): the gate posts
GOLD_BIG = {'texture': 'ctflor5', 'size': [128, 128], 'scale': 4}  # the capstone and the temple's dome
# Olympus' facades (S28, review row 57): MM8's temple marble (gtemp*) on a blue-grey ashlar plinth, gilt trim
O_WALL = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 2}  # the houses' walls, once up 512
O_PLINTH = {'texture': 'gtempflr', 'size': [128, 128]}           # the plinth: MM8 temple ashlar, blue-grey
O_GLASS = {'texture': 'gtempdor1', 'size': [128, 256], 'fit': True}   # a window of blue glass, once per window
O_PANEL = {'texture': 'gtempw2', 'size': [128, 256], 'fit': True}     # a carved blind panel, once per bay
O_ROOFTOP = {'texture': '7tws1f', 'size': [128, 128], 'scale': 2}     # the flat roof terraces (the paving's marble)
TRIM = {'texture': '7trimda', 'size': [256, 128]}                # one band 128 high
HOUSE_DOOR = {'texture': 'hwm2d', 'size': [128, 256], 'fit': True}
SKY_DOOR = {'texture': 'xdpyrdor', 'size': [128, 256], 'fit': True}
BLANK_BOARD = {'texture': 'xp5brd', 'size': [256, 128], 'fit': True, 'uneven': True}
REST_SIGN = {'texture': 'xp5rest', 'size': [256, 64], 'fit': True, 'uneven': True}
SHINGLE = {'texture': 'pxshings', 'size': [128, 128], 'scale': 2}
ROCK = {'texture': 'gcav1flr', 'size': [128, 128], 'scale': 2}
STRAW = {'texture': 'gkp1flr', 'size': [128, 128]}
CANVAS = {'texture': 'tentwal7b', 'size': [128, 256]}
WATER = {'texture': 'wtrtyl', 'size': [128, 128], 'scale': 2, 'liquid': 'water'}
SIGN = {'sgweapon': 'building:ol_smith', '7sgtvrn': 'building:ol_tavern', '7sgtrain': 'building:ol_training',
        'sglight': 'building:ol_guild_light', 'sgspirit': 'building:ol_guild_spirit'}

P = G.polys()
OUTLINES = {k: [[int(round(x)), int(round(y))] for x, y in v] for k, v in P.items()}
SPACE = D.SPACE
COMPASS = {'e': 0, 'ne': 45, 'n': 90, 'nw': 135, 'w': 180, 'sw': 225, 's': 270, 'se': 315}


def key(sid):
    return sid.split(':', 1)[1]


def floor_of(sid):
    return SPACE[sid]['floor']


def inside(poly, p):
    return G.point_in(p, poly)


def rim_distance(poly, p):
    best = 1e18
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy))
    return best


SINK = 4               # how far a block standing on the ground is sunk into it (X8's 8 would meet the hatches' foot)


def block(pid, at, size, z, rise, surface, top=None, facing=None, top_size=None, notes=None, **kw):
    # F62 (X8 p8 "you get stuck here", ported 2026-11-25): every block hangs from the room's floor at -6,000, so the
    # studio draws its bottom; a bottom lying on the cloud, a road or the paving is a ceiling at the party's feet. A
    # block whose foot is the walkable top under its middle (height_at) is sunk SINK into it, its top where it was
    # (tools/xeen/check_floor_cross.py floor.lid). Blocks on other blocks keep their foot (their sides would run on in
    # the plane of the sides under them and flicker).
    ground = height_at(at)
    sink = SINK if ground is not None and abs(ground - z) < 1 else 0
    e = {'id': pid, 'at': [int(round(at[0])), int(round(at[1]))], 'size': [int(round(size[0])), int(round(size[1]))],
         'base': int(round(z - sink - FLOOR)), 'rise': int(round(rise + sink)), 'surface': surface}
    if top:
        e['top_surface'] = top
    if facing is not None:
        e['facing'] = round(facing, 2)
    if top_size:
        e['top_size'] = top_size
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def prism(pid, outline, z, rise, surface, top=None, notes=None, **kw):
    e = {'id': pid, 'outline': [[int(round(x)), int(round(y))] for x, y in outline], 'base': int(round(z - FLOOR)),
         'rise': int(round(rise)), 'surface': surface, 'top_surface': top or surface}
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def platform_slab(pid, a, b, z0, z1, width, surface, top_surface, thickness, notes=None, bottom=None):
    """A hanging slab from point a (top z0) to b (top z1), `width` wide (X8's, X9's, P5's)."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    facing = math.degrees(math.atan2(by - ay, bx - ax))
    low = min(z0, z1) - thickness
    if int(z0) == int(z1):
        e = block(pid, ((ax + bx) / 2, (ay + by) / 2), (length, width), low, thickness, surface, top_surface,
                  facing=facing, bottom_surface=bottom or surface)
        if notes:
            e['notes'] = notes
        return e
    entry = {'id': pid, 'at': [int(round((ax + bx) / 2)), int(round((ay + by) / 2))],
             'size': [int(round(length)), width], 'facing': round(facing, 2), 'base': int(low - FLOOR),
             'rise': int(min(z0, z1) - low),
             'top_heights': [int(z0 - low), int(z1 - low), int(z1 - low), int(z0 - low)],
             'thickness': thickness, 'surface': surface, 'top_surface': top_surface,
             'bottom_surface': bottom or surface}
    if notes:
        entry['notes'] = notes
    return entry


def ring(cx, cy, r, sides=16, phase=0.0):
    return [(cx + r * math.cos(phase + 2 * math.pi * k / sides), cy + r * math.sin(phase + 2 * math.pi * k / sides))
            for k in range(sides)]


def frame(origin, phi, u, v):
    """A point u along a front facing out at phi (radians) and v out toward the front (X9's booth frame)."""
    ox, oy = origin
    cu, su = math.cos(phi - math.pi / 2), math.sin(phi - math.pi / 2)
    cv, sv = math.cos(phi), math.sin(phi)
    return (ox + u * cu + v * cv, oy + u * su + v * sv)


def toward_deg(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


# ------------------------------------------------------------------------------------------------ links

def link_cut(link, into):
    """The link's two rim points (Olympus: its gate), run `into` each island along its line."""
    p, q = G.link_ends(link, P)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * into, p[1] - uy * into), (q[0] + ux * into, q[1] + uy * into), d, (ux, uy)


ROAD_INTO = 320
BAND_W = 256


def landing_end(poly, start, u, width, margin=24):
    """Where a deck of `width` leaving `start` (on its island) along `u` is past the island across its whole width:
    the point on the centre line `margin` beyond the furthest bit of cloud under the deck (X8's, F62)."""
    ux, uy = u
    nx, ny = -uy, ux
    far = 0
    for k in range(9):
        o = (k / 8 - 0.5) * width
        t = 0
        while t < 20000:
            if inside(poly, (start[0] + ux * t + nx * o, start[1] + uy * t + ny * o)):
                far = max(far, t)
            t += 8
            if t > far + 2000:
                break
    far += margin
    return (start[0] + ux * far, start[1] + uy * far)


_SPANS = {}


def link_spans(l):
    """F62 (the player's pins 2026-11-25, X8 "bridge is clipping"; ported to D7 the same day): a deck sloping straight
    from inside one island to inside the other dipped under the higher island's top before its rim (or under both,
    where a bridge sags) and came out over the void. Each deck lies level at its island's height out to where it is
    past that island across its whole width (`landing_end`, the rims are crooked) and slopes or sags only between.
    Where the islands leave no room it lies level on the higher only. [(p, q, z0, z1)] from a to b."""
    if l['id'] not in _SPANS:
        _SPANS[l['id']] = _link_spans(l)
    return _SPANS[l['id']]


def _link_spans(l):
    bridge = l['style'] == 'bridge'
    a, b, d, (ux, uy) = link_cut(l, 160 if bridge else ROAD_INTO)
    za8, zb8 = floor_of(l['a']) + 8, floor_of(l['b']) + 8
    width = l['width']

    def along(p, q):
        return (q[0] - p[0]) * ux + (q[1] - p[1]) * uy
    pa = landing_end(P[l['a']], a, (ux, uy), width)
    pb = landing_end(P[l['b']], b, (-ux, -uy), width)
    room = along(pa, pb) >= 64
    if bridge:
        p, q = (pa, pb) if room else (a, b)
        sag = min(160, int(d / 25))
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        zm = (za8 + zb8) / 2 - sag
        spans = [(p, m, za8, zm), (m, q, zm, zb8)]
        return ([(a, pa, za8, za8)] if room else []) + spans + ([(pb, b, zb8, zb8)] if room else [])
    if za8 == zb8:
        return [(a, b, za8, zb8)]
    if room:
        return [(a, pa, za8, za8), (pa, pb, za8, zb8), (pb, b, zb8, zb8)]
    if zb8 > za8 and along(a, pb) >= 64 and along(pb, b) >= 64:
        return [(a, pb, za8, zb8), (pb, b, zb8, zb8)]
    if za8 > zb8 and along(a, pa) >= 64 and along(pa, b) >= 64:
        return [(a, pa, za8, za8), (pa, b, za8, zb8)]
    return [(a, b, za8, zb8)]


def span_top(spans, pt):
    """The deck's top (as laid by link_spans) over the point's projection on the link's line, or None off its ends."""
    for p, q, z0, z1 in spans:
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2 if L2 else 0
        if -1e-6 <= t <= 1 + 1e-6:
            return z0 + (z1 - z0) * t
    return None


RAIL_POST = 16         # the posts a rope bridge's rails are tied to at both ends (F70)


def rail_posts(lid, spans, u, width):
    """F70 (the player's pins 2026-11-26, X9 p5-p10 "the side rails stop in the air"; D7's bridges the same): a rope
    bridge's two rails are tied at each end to a post standing on the island just before the deck's end, its top 16
    over the rail (tools/xeen/check_beam_ends.py)."""
    ux, uy = u
    nx, ny = -uy * (width / 2 - 8), ux * (width / 2 - 8)
    out = []
    for tag, p, z, back in (('a', spans[0][0], spans[0][2], -1), ('b', spans[-1][1], spans[-1][3], 1)):
        cx, cy = p[0] + back * ux * RAIL_POST / 2, p[1] + back * uy * RAIL_POST / 2
        for k, side in enumerate((1, -1)):
            xy = (cx + side * nx, cy + side * ny)
            ground = height_at(xy)
            if ground is None or ground > z:
                raise SystemExit(f'{lid}: rail post {tag}{k + 1} at {xy} stands on no island under the deck ({ground})')
            out.append(block(f'platform:{lid}_post_{tag}{k + 1}', xy, (RAIL_POST, RAIL_POST), ground,
                             z + 88 + 16 - ground, ROPE, ROPE, facing=math.degrees(math.atan2(uy, ux))))
    return out


def links():
    platforms, beams = [], []
    for l in D.LINKS:
        za, zb = floor_of(l['a']), floor_of(l['b'])
        lid = key(l['id'])
        spans = link_spans(l)
        if l['style'] == 'bridge':
            a, b, d, (ux, uy) = link_cut(l, 160)
            width = l['width']
            for k, (p, q, z0, z1) in enumerate(spans):
                platforms.append(platform_slab(f'platform:{lid}_{k + 1}', p, q, int(z0), int(z1), width, ROPE, PLANK,
                                               24, f"{l['id']}: rope bridge, {int(d)} rim to rim" if k == 0 else None))
                nx, ny = -uy * (width / 2 - 8), ux * (width / 2 - 8)
                for side in (1, -1):
                    beams.append({'path': [[int(round(p[0] + side * nx)), int(round(p[1] + side * ny))],
                                           [int(round(q[0] + side * nx)), int(round(q[1] + side * ny))]],
                                  'width': 8, 'depth': 8, 'bottom': int(z0 + 80), 'bottom_end': int(z1 + 80),
                                  'surface': ROPE})
            platforms += rail_posts(lid, spans, (ux, uy), width)
            continue
        a, b, d, (ux, uy) = link_cut(l, ROAD_INTO)
        what = {'road': 'the Skyroad', 'causeway': 'a causeway', 'spur': 'a spur'}[l['style']]
        if lid == 'dragon_road':
            what = 'the dragon road'
        for k, (p, q, z0, z1) in enumerate(spans):
            platforms.append(platform_slab(f'platform:{lid}' if k == 0 else f'platform:{lid}_{k + 1}', p, q, z0, z1,
                                           l['width'], CLOUD_SIDE, CLOUD_TOP, 192,
                                           f"{l['id']}: {what}, cloud, {int(d)} rim to rim, rising {zb - za}"
                                           if k == 0 else None))
        # the paved band down the middle (D-8; the lead, 2026-11-21: every road, spur and causeway, a third of its
        # width): on the road exactly over its slab (the same ends and slope, 6 over it), and on into each island 416
        # further as a flat piece 6 over the island (not into Olympus: a causeway's band stops at the gate). 24 deep
        # (F62: at 16 its bottom lay 2 under the island's top where the road runs into it, check_floor_cross floor.lid)
        bw = max(160, int(round(l['width'] / 3 / 32)) * 32)
        for k, (p, q, z0, z1) in enumerate(spans):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            # 8 short of the road's two ends: no end face in the slab's plane; where two pieces meet, the band's joint
            # lies 16 past the slab's (in its own piece's slope), so no band end shares a plane with a slab end
            ka = 8 / L if k == 0 else 16 / L
            kb = 8 / L if k == len(spans) - 1 else -16 / L
            p8 = (p[0] + (q[0] - p[0]) * ka, p[1] + (q[1] - p[1]) * ka)
            q8 = (q[0] - (q[0] - p[0]) * kb, q[1] - (q[1] - p[1]) * kb)
            platforms.append(platform_slab(f'platform:{lid}_band' if k == 0 else f'platform:{lid}_band{k + 1}', p8, q8,
                                           z0 + 6 + (z1 - z0) * ka, z1 + 6 - (z1 - z0) * kb, bw, FLAG, FLAG, 24,
                                           "The paved band of cloud-stone flags down the road's middle."
                                           if k == 0 else None))
        for end, pt, sgn, z, sid in (('a', a, -1, za, l['a']), ('b', b, 1, zb, l['b'])):
            if SPACE[sid]['kind'] == 'town':
                continue
            pt = (pt[0] + sgn * ux * 8, pt[1] + sgn * uy * 8)
            far = (pt[0] + sgn * ux * 416, pt[1] + sgn * uy * 416)
            platforms.append(platform_slab(f'platform:{lid}_band_{end}', pt, far, z + 6, z + 6, bw, FLAG, FLAG, 16))
    return platforms, beams


def height_at(pt):
    """The walkable top under a point: Olympus' paving, a road or spur, an island, or None."""
    if inside(PAVING, pt):
        return floor_of('zone:olympus') + PAVE_RISE
    a, b = D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / (dx * dx + dy * dy)
    if 0 <= t <= 1 and abs((pt[0] - a[0]) * dy - (pt[1] - a[1]) * dx) / math.hypot(dx, dy) <= 288:
        return floor_of('zone:olympus') + 12
    for l in D.LINKS:
        if l['style'] == 'bridge':
            continue
        a, b, _, _ = link_cut(l, ROAD_INTO)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2
        off = abs((pt[0] - a[0]) * dy - (pt[1] - a[1]) * dx) / math.sqrt(L2)
        if 0 <= t <= 1 and off <= l['width'] / 2:
            band = 6 if off <= max(160, round(l['width'] / 3 / 32) * 32) / 2 else 0
            return span_top(link_spans(l), pt) + band
    for s in D.SPACES:
        if inside(P[s['id']], pt):
            return s['floor']
    for c, poly in TIPS.items():
        if inside(poly, pt):
            return floor_of(c)
    return None


# ------------------------------------------------------------------------------------------------ clouds

def clouds():
    out = []
    for i, s in enumerate(D.SPACES):
        sid = s['id']
        fl = s['floor']
        out.append({'id': f'platform:{key(sid)}', 'outline': OUTLINES[sid], 'base': fl - SLAB - FLOOR, 'rise': SLAB,
                    'surface': CLOUD_SIDE, 'top_surface': CLOUD_TOP, 'bottom_surface': CLOUD_SIDE,
                    'notes': f"{s['name']}: a cloud, its top at {fl}."})
        ex, ey = s['extent']
        cx, cy = s['at']
        rnd = random.Random(100 + i)
        roots = 3 if ex * ey > 12e6 else 2
        for r in range(roots):
            ox = rnd.uniform(-0.08, 0.08) * ex
            oy = rnd.uniform(-0.08, 0.08) * ey
            top_w = int(0.5 * ex) // 16 * 16
            top_d = int(0.5 * ey) // 16 * 16
            depth = int(rnd.uniform(900, 1700)) // 16 * 16
            out.append({'id': f'platform:{key(sid)}_root{r + 1}', 'at': [int(cx + ox), int(cy + oy)],
                        'size': [max(160, top_w // 5), max(160, top_d // 5)], 'top_size': [top_w, top_d],
                        'base': fl - SLAB + 8 * (r + 1) - depth - FLOOR, 'rise': depth,
                        'surface': CLOUD_SIDE, 'top_surface': CLOUD_SIDE, 'bottom_surface': CLOUD_SIDE})
    return out


# ------------------------------------------------------------------------------------------------ the corners

CORNERS = {p['space']: p for p in D.POINTS if p['kind'] == 'corner'}
TIP_DISC = 320


def tip_spit(space):
    c = SPACE[space]
    tip = CORNERS[space]['at']
    start = (c['at'][0] + 0.4 * (tip[0] - c['at'][0]), c['at'][1] + 0.4 * (tip[1] - c['at'][1]))
    return start, tip


TIPS = {}
for _c in CORNERS:
    _a, _b = tip_spit(_c)
    _d = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
    _ux, _uy = (_b[0] - _a[0]) / _d, (_b[1] - _a[1]) / _d
    _nx, _ny = -_uy * 384, _ux * 384
    TIPS[_c] = [(_a[0] + _nx, _a[1] + _ny), (_b[0] + _nx, _b[1] + _ny), (_b[0] - _nx, _b[1] - _ny),
                (_a[0] - _nx, _a[1] - _ny)]


def corners():
    out = []
    for space, poi in CORNERS.items():
        el = space.split(':')[1].split('_')[0]
        a, b = tip_spit(space)
        fl = floor_of(space)
        ux, uy = (b[0] - a[0]), (b[1] - a[1])
        L = math.hypot(ux, uy)
        b2 = (b[0] + ux / L * 256, b[1] + uy / L * 256)
        out.append(platform_slab(f'platform:{el}_spit', a, b2, fl + 4, fl + 4, 768, CLOUD_SIDE, CLOUD_TOP, 160,
                                 f"The {el.capitalize()} Corner's spit out to the tip: it ends in nothing."))
        out.append(prism(f'platform:tip_{el}', ring(b[0], b[1], TIP_DISC, 16), fl + 4, 16, FLAG,
                         notes=(f"The {el.capitalize()} Corner's tip (corners.yml {tuple(b)}): stepping on it, the sky "
                                f"asks 'What do you seek?' ({poi['text']})."),
                         bottom_surface=FLAG))
    return out


# ------------------------------------------------------------------------------------------------ boards and huts

BOARD_W, BOARD_H, BOARD_LIFT = 768, 384, 224
LEG = 288


def board_facing(p):
    """A board faces its island's middle (or the rope, for the Skyroad board); a board at the middle faces south."""
    if p['id'] == 'board:skyroad_board':
        return toward_deg(p['at'], next(q for q in D.POINTS if q['id'] == 'poi:rope')['at'])
    c = SPACE[p['space']]['at']
    if math.hypot(c[0] - p['at'][0], c[1] - p['at'][1]) < 256:
        return 270.0
    return toward_deg(p['at'], c)


BOARDS = [p for p in D.POINTS if p['kind'] == 'board' and not p['id'].startswith('board:rest_')]
RESTS = [p for p in D.POINTS if p['id'].startswith('board:rest_')]
ZONE_BOARDS = {'fire': "'Fire Zone' (aaze0089:0)", 'air': "'Air Zone' (aazex109:0)",
               'earth': "'Earth Zone' (aazex112:0)", 'water': "'Water Zone' (aaze0092:0)"}


def board_line(text):
    """The board's words from the design's text: the first quoted line."""
    i = text.find("'")
    j = text.find("'", i + 1)
    while j > 0 and j + 1 < len(text) and text[j + 1].isalpha():     # an apostrophe inside the line (Joe's)
        j = text.find("'", j + 1)
    return text[i + 1:j] if i >= 0 and j > i else text


def zone_board_at(space):
    a, b = tip_spit(space)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    # beside the spit's root, 512 off its line, facing back along it
    return (a[0] + 640 * ux - 640 * uy, a[1] + 640 * uy + 640 * ux), math.degrees(math.atan2(-uy, -ux))


def all_boards():
    """(id, at, facing deg, words) for the 18 boards and the four zone boards at the tips."""
    out = [(key(p['id']), p['at'], board_facing(p), board_line(p['text'])) for p in BOARDS]
    for space in CORNERS:
        el = space.split(':')[1].split('_')[0]
        at, deg = zone_board_at(space)
        out.append((f'zone_{el}', at, deg, board_line(ZONE_BOARDS[el])))
    return out


def board(bid, at, deg, z):
    phi = math.radians(deg)
    along = deg - 90
    out = []
    for i, u in enumerate((-LEG, LEG)):
        out.append(block(f'platform:board_{bid}_leg{i + 1}', frame(at, phi, u, 4), (32, 32), z, BOARD_LIFT,
                         PLANK, PLANK, facing=along))
    out.append(block(f'platform:board_{bid}', frame(at, phi, 0, 10), (BOARD_W, 8), z + BOARD_LIFT, BOARD_H,
                     BLANK_BOARD, PLANK, facing=along, end_surface=dict(PLANK, fit=False), notes='A blank board (xp5brd): its words '
                     'show on hover only (D-7).'))
    out.append(block(f'platform:board_{bid}_back', frame(at, phi, 0, -2), (BOARD_W, 8), z + BOARD_LIFT, BOARD_H,
                     BLANK_BOARD, PLANK, facing=along, end_surface=dict(PLANK, fit=False)))
    return out


def boards():
    out = []
    for bid, at, deg, _ in all_boards():
        z = height_at(at)
        assert z is not None, ('board off the clouds', bid, at)
        out += board(bid, at, deg, z)
    return out


def hut_place(p):
    """A Rest Stop's hut: on a corner on the side away from both roads, else at its board's spot, facing the middle."""
    s = SPACE[p['space']]
    c = s['at']
    if s['kind'] == 'corner':
        sx = 1 if c[0] > 0 else -1
        sy = 1 if c[1] > 0 else -1
        at = (c[0] - sx * 1280, c[1] + sy * 1024)
    else:
        at = p['at']
    return at, toward_deg(at, c)


def hut(p):
    """P5's open-fronted plank hut (back wall 768 x 384, sides 480 deep, a shingle roof) with the REST STOP sign 512 x
    128 over its front (xp5rest, once, fit)."""
    k = key(p['id']).replace('rest_', '')
    at, deg = hut_place(p)
    phi = math.radians(deg)
    along = deg - 90
    z = height_at(at)
    o = at
    return [block(f'platform:hut_{k}_back', frame(o, phi, 0, -248), (768, 16), z, 384, PLANK, PLANK, facing=along,
                  end_surface=dict(PLANK, fit=False), notes="A Rest Stop hut's back wall."),
            block(f'platform:hut_{k}_side1', frame(o, phi, -376, 0), (16, 480), z, 384, PLANK, PLANK, facing=along),
            block(f'platform:hut_{k}_side2', frame(o, phi, 376, 0), (16, 480), z, 384, PLANK, PLANK, facing=along),
            block(f'platform:hut_{k}_post1', frame(o, phi, -376, 272), (24, 24), z, 384, PLANK, PLANK, facing=along),
            block(f'platform:hut_{k}_post2', frame(o, phi, 376, 272), (24, 24), z, 384, PLANK, PLANK, facing=along),
            block(f'platform:hut_{k}_roof', frame(o, phi, 0, 16), (864, 608), z + 384, 24, SHINGLE, SHINGLE,
                  facing=along, bottom_surface=PLANK, end_surface=dict(PLANK, fit=False), notes='The shingle roof.'),
            block(f'platform:hut_{k}_sign', frame(o, phi, 0, 316), (512, 8), z + 408, 128, REST_SIGN, PLANK,
                  facing=along, end_surface=dict(PLANK, fit=False), notes="The REST STOP sign (P5's xp5rest, D-7)."),
            block(f'platform:hut_{k}_sign_back', frame(o, phi, 0, 302), (512, 8), z + 408, 128, PLANK, PLANK,
                  facing=along, end_surface=dict(PLANK, fit=False))]


def hut_benches(p):
    """S's two benches (xeen_bench, 92 x 50) against a Rest Stop hut's back wall, facing out of the open front
    (gen_objects.py places them; world decorations in a BLV since merge point 26)."""
    at, deg = hut_place(p)
    phi = math.radians(deg)
    z = height_at(at)
    return [(frame(at, phi, u, -190), deg % 360, z) for u in (-168, 168)]


# ------------------------------------------------------------------------------------------------ Olympus

OLY = SPACE['zone:olympus']
OLY_Z = OLY['floor']
PAVE_RISE = 16
OX, OY = OLY['at']
PAVING = [(OX + 0.94 * (x - OX), OY + 0.94 * (y - OY)) for x, y in P['zone:olympus']]
HOUSE_H = 768
TEMPLE_H = 1024
FACING_VEC = {'n': (0, 1), 's': (0, -1), 'e': (1, 0), 'w': (-1, 0)}


def building_box(b):
    """(centre, (size x, size y)) of a house: its door on the front wall, the house behind it."""
    bid, house, service, door, f, fp, zone, note = b
    nx, ny = FACING_VEC[f]
    w, d = fp[0] * 512, fp[1] * 512
    if f in ('n', 's'):
        size = (w, d)
    else:
        size = (d, w)
    centre = (door[0] - nx * d / 2, door[1] - ny * d / 2)
    return centre, size


def in_building(p, pad=128):
    for b in D.BUILDINGS:
        (cx, cy), (sx, sy) = building_box(b)
        if abs(p[0] - cx) <= sx / 2 + pad and abs(p[1] - cy) <= sy / 2 + pad:
            return True
    vx, vy = D.SOUL_STORAGE['room_at']
    rw, rd = D.SOUL_STORAGE['room']
    return abs(p[0] - vx) <= rw / 2 + pad and abs(p[1] - vy) <= rd / 2 + pad


def gate_points():
    out = [g for _, g, _ in D.OLYMPUS_GATES]
    out.append(D.OLYMPUS_DOCK_START)
    return out


def olympus():
    z = OLY_Z + PAVE_RISE
    out = [prism('platform:olympus_paving', PAVING, OLY_Z, PAVE_RISE, MARBLE,
                 notes="Olympus' white marble paving on its cloud (7tws1f, as X9's flags).")]
    # the balustrade round the rim (Celeste's marble base), open at the gates and Lucio's jetty
    bal = [(OX + 0.925 * (x - OX), OY + 0.925 * (y - OY)) for x, y in P['zone:olympus']]   # on the paving's rim
    gates = gate_points()
    k = 0
    for i in range(len(bal)):
        a, b = bal[i - 1], bal[i]
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) // 640))
        for j in range(n):
            p = (a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n)
            q = (a[0] + (b[0] - a[0]) * (j + 1) / n, a[1] + (b[1] - a[1]) * (j + 1) / n)
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            if (min(math.hypot(m[0] - g[0], m[1] - g[1]) for g in gates) < 1100 or in_building(m, 320)
                    or math.hypot(m[0] - D.ANTS_LOOKOUT[0], m[1] - D.ANTS_LOOKOUT[1]) < 640):
                continue
            k += 1
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            out.append(block(f'platform:balustrade_{k}', m, (L - 40, 32), z - 8, 120, PLINTH, STONE,
                             end_surface=dict(STONE, fit=False), bottom_surface=STONE,
                             facing=toward_deg(p, q), notes="Olympus' low balustrade." if k == 1 else None))
    # the gates: an open propylon each (D-8: no leaves, no griffin statues): two marble columns each side of the
    # causeway's end on one pedestal, gilt capitals, and a marble lintel with a gilt frieze across the road (S28)
    for name, (gx, gy), _ in D.OLYMPUS_GATES:
        out += gate_parts(name, (gx, gy), z)
    # the houses (A4's d7.yml; XD-17's route: a block, the door a clicked block), dressed as temples' houses (S28)
    for b in D.BUILDINGS:
        bid, house, service, door, f, fp, zone, note = b
        k = key(bid)
        (cx, cy), (sx, sy) = building_box(b)
        temple = k == 'ol_temple'
        h = TEMPLE_H if temple else HOUSE_H - (LOWER_H if k in LOWER else 0)
        out.append(block(f'platform:{k}', (cx, cy), (sx, sy), OLY_Z - 32, h + PAVE_RISE + 32, O_WALL, O_ROOFTOP,
                         notes=f"{service} (house {house}){': ' + note if note else ''}."))
        out += facade_parts(b, z, h)
        nx, ny = FACING_VEC[f]
        dsize = (16, 192) if f in ('e', 'w') else (192, 16)
        out.append(block(f'door:{k}', (door[0] + nx * 8, door[1] + ny * 8), dsize, z, 384, HOUSE_DOOR, STONE,
                         end_surface=dict(STONE, fit=False), notes=f"{service}'s door (house {house}): evt.EnterHouse({house})."))
        for tex, sb in SIGN.items():
            if sb == bid:
                ssize = (8, 160) if f in ('e', 'w') else (160, 8)
                out.append(block(f'platform:{k}_sign', (door[0] + nx * 4, door[1] + ny * 4), ssize, z + 448, 160,
                                 {'texture': tex, 'size': [64, 64], 'fit': True}, dict(STONE, fit=False), end_surface=dict(STONE, fit=False),
                                 notes=f'The sign over the door ({tex}, once).'))
    out += vault(z) + jetty() + lookout(z)
    return out


SIDES = (('n', (0, 1)), ('s', (0, -1)), ('e', (1, 0)), ('w', (-1, 0)))
# S29: a house that touches another (the dock against the Training Grounds, Hermes' house corner to corner with
# Athena's) stands lower, so their friezes, cornices and parapets do not share planes (no z-fighting)
LOWER, LOWER_H = ('ol_dock', 'ol_hermes'), 96
PLINTH_H = 96          # the plinth over the paving
PLINTH_OUT = 32        # how far it stands proud of the wall
PIL_W, PIL_OUT = 96, 48     # a pilaster's width and how far it stands proud
CAP_H = 48             # a pilaster's or column's gilt capital
FRIEZE_H, CORNICE_H, PARAPET_H = 64, 48, 144
CORNICE_OUT = 64       # the cornice's overhang past the wall
DOOR_FRAME_W, DOOR_FRAME_H = 256, 448


def near_other(k, p, pad):
    """Another house (or the vault) within `pad` of point p: the face there is hidden or crowded, so not dressed."""
    for b in D.BUILDINGS:
        if key(b[0]) == k:
            continue
        (cx, cy), (sx, sy) = building_box(b)
        if abs(p[0] - cx) <= sx / 2 + pad and abs(p[1] - cy) <= sy / 2 + pad:
            return True
    vx, vy = D.SOUL_STORAGE['room_at']
    rw, rd = D.SOUL_STORAGE['room']
    return abs(p[0] - vx) <= rw / 2 + pad and abs(p[1] - vy) <= rd / 2 + pad


def clear_runs(k, c, t, n, a, b, step=16, pad=40):
    """The parts of a plinth run (u from a to b along a face) not against another house: where a house touches this
    one, its plinth and this one's would lie in one plane (S29)."""
    out, start = [], None
    us = [a + i * step for i in range(int((b - a) // step) + 1)] + [b]
    for u in us:
        free = not near_other(k, (c[0] + t[0] * u + n[0] * 48, c[1] + t[1] * u + n[1] * 48), pad)
        if free and start is None:
            start = u
        elif not free and start is not None:
            out.append((start, u - step))
            start = None
    if start is not None:
        out.append((start, b))
    return [(x, y) for x, y in out if y - x > 8]


def face_block(pid, c, t, n, u, out, width, depth, z0, rise, surface, top=None, **kw):
    """A block on a house face: `u` along the face from its middle c, its middle `out` in front of the wall plane,
    `width` along the face and `depth` across it."""
    at = (c[0] + t[0] * u + n[0] * out, c[1] + t[1] * u + n[1] * out)
    size = (width, depth) if t[0] else (depth, width)
    return block(pid, at, size, z0, rise, surface, top, **kw)


def facade_parts(b, z, h):
    """A house's dressing (S28, review row 57): a blue-grey plinth (open at the door), gilt-capped marble pilasters at
    the corners and between the bays, a window of blue glass in a gilt frame in each bay (the temple: carved blind
    panels), the door in a gilt frame under a marble hood, a gilt frieze, a marble cornice, a parapet with a gilt
    coping round the roof terrace and gilt finials on its corners."""
    bid, house, service, door, f, fp, zone, note = b
    k = key(bid)
    temple = k == 'ol_temple'
    (cx, cy), (sx, sy) = building_box(b)
    out = []
    edge = dict(STONE, fit=False)
    for side, n in SIDES:
        L = sx if side in ('n', 's') else sy
        t = (1, 0) if side in ('n', 's') else (0, 1)
        c = (cx + n[0] * sx / 2, cy + n[1] * sy / 2)
        front = side == f
        tag = f'{k}_{side}'
        u_door = (door[0] - c[0]) * t[0] + (door[1] - c[1]) * t[1] if front else None
        # the plinth: corners on the north and south strips; the front strip open round the door
        u0, u1 = (-L / 2 - PLINTH_OUT, L / 2 + PLINTH_OUT) if side in ('n', 's') else (-L / 2 + PLINTH_OUT,
                                                                                          L / 2 - PLINTH_OUT)
        probe = (c[0] + n[0] * 160, c[1] + n[1] * 160)
        crowded = near_other(k, probe, 0)     # a face against another house or the vault: no plinth, no dressing
        runs = [(u0, u1)]
        if front:
            runs = [(u0, u_door - DOOR_FRAME_W / 2), (u_door + DOOR_FRAME_W / 2, u1)]
        runs = [r for a, bb in runs for r in clear_runs(k, c, t, n, a, bb)]
        for j, (a, bb) in enumerate(runs):
            if bb - a > 8 and not crowded:
                out.append(face_block(f'platform:{tag}_plinth{j + 1}', c, t, n, (a + bb) / 2, (PLINTH_OUT - 32) / 2,
                                      bb - a, PLINTH_OUT + 32, z, PLINTH_H, O_PLINTH, STONE,
                                      notes="Olympus' houses: a blue-grey plinth (MM8 temple ashlar)."
                                      if k == 'ol_smith' and side == 'n' and j == 0 else None))
        if crowded:
            continue
        # pilasters and window positions along the face
        if front:
            pils = [u for s_ in (-1, 1) for u in (u_door + s_ * 192, u_door + s_ * 656) if abs(u) <= L / 2 - 150]
            wins = [u for s_ in (-1, 1) for u in (u_door + s_ * 416, u_door + s_ * 896) if abs(u) <= L / 2 - 150]
            wins = [u for u in wins if all(abs(u - p) >= 150 for p in pils)]
        else:
            nb = max(1, int(round(L / 512)))
            pils = [-L / 2 + i * L / nb for i in range(1, nb)]
            wins = [-L / 2 + (i + 0.5) * L / nb for i in range(nb)]
        free = [r for r in runs if not front] or [(u0, u1)]     # the stretches of this face not against a house
        free = clear_runs(k, c, t, n, u0, u1) if not front else free
        pils = [u for u in pils if any(a + 80 <= u <= bb - 80 for a, bb in free)]
        wins = [u for u in wins if any(a + 120 <= u <= bb - 120 for a, bb in free)]
        for i, u in enumerate(pils):
            out.append(face_block(f'platform:{tag}_pilaster{i + 1}', c, t, n, u, (PIL_OUT - 16) / 2, PIL_W,
                                  PIL_OUT + 16, z + PLINTH_H, h - PLINTH_H - CAP_H - 16, STONE, STONE,
                                  notes="Olympus' houses: a marble pilaster." if k == 'ol_smith' and side == 'n'
                                  and i == 0 else None))
            out.append(face_block(f'platform:{tag}_pilcap{i + 1}', c, t, n, u, (PIL_OUT + 8 - 20) / 2, PIL_W + 32,
                                  PIL_OUT + 8 + 20, z + h - CAP_H - 16, CAP_H, GOLD, GOLD))
        for i, u in enumerate(wins):
            if temple:     # the temple's sides: tall carved blind panels in gilt frames
                gw, gh, gz = 192, 384, z + 256
                glass = O_PANEL
            else:
                gw, gh, gz = 128, 256, z + 256
                glass = O_GLASS
            out.append(face_block(f'platform:{tag}_winframe{i + 1}', c, t, n, u, (12 - 8) / 2, gw + 48, 12 + 8,
                                  gz - 24, gh + 48, GOLD, GOLD, end_surface=dict(GOLD, fit=False),
                                  notes="Olympus' houses: a gilt window frame." if k == 'ol_smith' and side == 'n'
                                  and i == 0 else None))
            out.append(face_block(f'platform:{tag}_window{i + 1}', c, t, n, u, (20 - 4) / 2, gw, 20 + 4, gz, gh, glass,
                                  edge, end_surface=edge,
                                  notes=("Olympus' houses: a window of blue glass (gtempdor1, once)." if not temple
                                         else "The temple's carved blind panel (gtempw2, once).")
                                  if (k in ('ol_smith', 'ol_temple')) and side in ('n', 'e') and i == 0 else None))
        if front:     # the door's gilt frame and the marble hood over it
            out.append(face_block(f'platform:{tag}_doorframe', c, t, n, u_door, (8 - 6) / 2, DOOR_FRAME_W, 8 + 6, z - 6,
                                  DOOR_FRAME_H - 12 + 6, GOLD, GOLD, end_surface=dict(GOLD, fit=False),
                                  notes="The door's gilt frame." if k == 'ol_smith' else None))
            out.append(face_block(f'platform:{tag}_doorhood', c, t, n, u_door, (64 - 12) / 2, DOOR_FRAME_W + 64, 64 + 12,
                                  z + DOOR_FRAME_H - 40, 40, STONE, GOLD, bottom_surface=STONE,
                                  notes="The door's marble hood." if k == 'ol_smith' else None))
    # corner pilasters
    for i, (ex, ey) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        p = (cx + ex * sx / 2, cy + ey * sy / 2)
        if near_other(k, p, 176):
            continue
        out.append(block(f'platform:{k}_corner{i + 1}', p, (128, 128), z + PLINTH_H, h - PLINTH_H - CAP_H - 16, STONE,
                         STONE, notes="Olympus' houses: a marble corner pilaster." if k == 'ol_smith' and i == 0
                         else None))
        out.append(block(f'platform:{k}_cornercap{i + 1}', p, (160, 160), z + h - CAP_H - 16, CAP_H, GOLD, GOLD))
    # frieze, cornice, parapet, finials
    zf = z + h
    out.append(block(f'platform:{k}_frieze', (cx, cy), (sx + 16, sy + 16), zf - 16, FRIEZE_H + 16, GOLD, GOLD,
                     notes="Olympus' houses: a gilt frieze under the cornice." if k == 'ol_smith' else None))
    zc = zf + FRIEZE_H
    out.append(block(f'platform:{k}_cornice', (cx, cy), (sx + 2 * CORNICE_OUT, sy + 2 * CORNICE_OUT), zc,
                     CORNICE_H, STONE, O_ROOFTOP, bottom_surface=STONE,
                     notes="Olympus' houses: the marble cornice." if k == 'ol_smith' else None))
    zp = zc + CORNICE_H
    hx, hy = sx / 2 + 8, sy / 2 + 8     # the parapet's outer face over the frieze's
    pt = 48
    for side, (ax, ay, bx, by) in (('n', (-hx, hy - pt, hx, hy)), ('s', (-hx, -hy, hx, -hy + pt)),
                                    ('e', (hx - pt, -hy + pt, hx, hy - pt)), ('w', (-hx, -hy + pt, -hx + pt, hy - pt))):
        out.append(block(f'platform:{k}_parapet_{side}', (cx + (ax + bx) / 2, cy + (ay + by) / 2), (bx - ax, by - ay),
                         zp, PARAPET_H, STONE, GOLD, end_surface=edge,
                         notes="Olympus' houses: a parapet with a gilt coping round the roof terrace."
                         if k == 'ol_smith' and side == 'n' else None))
    for i, (ex, ey) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        p = (cx + ex * (hx - 40), cy + ey * (hy - 40))
        out.append(block(f'platform:{k}_finial{i + 1}', p, (112, 112), zp + PARAPET_H, 160, GOLD, GOLD,
                         top_size=[24, 24], notes="Olympus' houses: a gilt finial." if k == 'ol_smith' and i == 0
                         else None))
    if temple:
        out += temple_parts(b, z)
    return out


def column(pid, p, z, shaft, r=64, notes=None):
    """A round marble column (a 12-sided shaft) on a square base under a gilt capital; `shaft` its shaft's height."""
    return [block(f'{pid}_base', p, (2 * r + 48, 2 * r + 48), z, 48, STONE, STONE, notes=notes),
            prism(f'{pid}', ring(p[0], p[1], r, 12, math.pi / 12), z + 48, shaft, STONE, STONE),
            block(f'{pid}_cap', p, (2 * r + 64, 2 * r + 64), z + 48 + shaft, CAP_H, GOLD, GOLD,
                  top_size=[2 * r + 64, 2 * r + 64])]


def temple_parts(b, z):
    """The temple's portico of six round columns under a marble architrave, a gilt frieze, a cornice and a pediment
    (two raking halves), and its gold dome on a marble drum over the parapet (S28)."""
    bid, house, service, door, f, fp, zone, note = b
    (cx, cy), (sx, sy) = building_box(b)
    out = []
    depth = 608                       # the portico's depth in front of the wall
    yc = door[1] - 512                # the columns' line
    shaft = TEMPLE_H - 96 - 48 - CAP_H          # base, shaft and capital meet the architrave
    for i, u in enumerate((-1024, -640, -320, 320, 640, 1024)):
        out += column(f'platform:temple_column{i + 1}', (door[0] + u, yc), z, shaft,
                      notes='The portico: six round marble columns with gilt capitals.' if i == 0 else None)
    za = z + TEMPLE_H - 96
    y0 = door[1] - depth - 32       # the portico's front under the architrave
    W = 2304
    out.append(block('platform:temple_architrave', (door[0], (y0 + door[1]) / 2), (W, door[1] - y0), za, 96, STONE, STONE,
                     bottom_surface=STONE, notes="The portico's marble architrave."))
    out.append(block('platform:temple_portico_frieze', (door[0], (y0 - 8 + door[1] - 8) / 2), (W + 16, door[1] - y0),
                     za + 96, FRIEZE_H, GOLD, GOLD))
    zc = za + 96 + FRIEZE_H
    yc0, yc1 = y0 - 64, door[1] - 64
    out.append(block('platform:temple_portico_cornice', (door[0], (yc0 + yc1) / 2), (W + 128, yc1 - yc0), zc, CORNICE_H,
                     STONE, STONE, bottom_surface=STONE))
    zp = zc + CORNICE_H
    for side, toward in ((-1, 'east'), (1, 'west')):
        out.append(block(f'platform:temple_pediment{1 if side < 0 else 2}', (door[0] + side * (W + 64) / 4, (yc0 + yc1) / 2),
                         ((W + 64) / 2, yc1 - yc0), zp, 0, STONE, GOLD, end_surface=edge_stone(),
                         top_slope={'to': 384, 'toward': toward},
                         notes="The portico's pediment and its gilt roof." if side < 0 else None))
    # the drum and the dome over the parapet
    zd = z + TEMPLE_H + FRIEZE_H + CORNICE_H
    out.append(prism('platform:temple_drum', ring(cx, cy, 736, 16, math.pi / 16), zd, 256, STONE, STONE,
                     notes="The dome's marble drum."))
    zz = zd + 256
    for i, (r, hh) in enumerate(((704, 96), (640, 160), (544, 160), (416, 128), (256, 96), (96, 64))):
        out.append(prism(f'platform:temple_dome{i + 1}', ring(cx, cy, r, 16, math.pi / 16), zz, hh, GOLD_BIG,
                         notes='The gold dome.' if i == 0 else None))
        zz += hh
    return out


def edge_stone():
    return dict(STONE, fit=False)


def gate_parts(name, g, z):
    """A gate as an open propylon: on each side of the causeway's end a pedestal with two round marble columns
    (one behind the other along the road), and a marble lintel with a gilt frieze across the road on top."""
    gx, gy = g
    l = next(x for x in D.LINKS if x.get('gate') == (gx, gy))
    _, _, _, (ux, uy) = link_cut(l, 0)
    if not inside(PAVING, (gx + ux * 300, gy + uy * 300)):     # the propylon stands on the paving, inside the gate
        ux, uy = -ux, -uy
    gx, gy = gx + ux * 192, gy + uy * 192
    half = l['width'] / 2 + 112
    tag = name.split()[0].replace('-', '_')
    out = []
    shaft = 712     # S29: the entablature's planes clear the houses' frieze, cornice and parapet levels
    for s_ in (-1, 1):
        px, py = gx - uy * half * s_, gy + ux * half * s_
        side = 1 if s_ < 0 else 2
        # a column whose base would stand in a house (the north gate, between the temple and the Spirit Guild) is
        # left out: the lintel rests on that house's wall there (S29)
        vs = [v for v in (-160, 160) if not near_other('', (px + ux * v, py + uy * v), 104)]
        if not vs:
            continue
        pv = sum(vs) / len(vs)
        out.append(block(f'platform:gate_{tag}_pedestal{side}', (px + ux * pv, py + uy * pv),
                         (224 + 256 * (len(vs) - 1), 224), z - 6, 70, O_PLINTH, STONE,
                         facing=toward_deg((0, 0), (ux, uy)),
                         notes=f"Olympus' {name}: marble columns on a pedestal each side." if s_ < 0 else None))
        for v in vs:
            j = 0 if v < 0 else 1
            out += column(f'platform:gate_{tag}_col{side}{j + 1}', (px + ux * v, py + uy * v), z + 64, shaft, r=56)
    zt = z + 64 + 48 + shaft + CAP_H
    span = 2 * half + 240
    face = toward_deg((0, 0), (-uy, ux))
    out.append(block(f'platform:gate_{tag}_lintel', (gx, gy), (span, 480), zt, 96, STONE, STONE, facing=face,
                     bottom_surface=STONE, notes=f"Olympus' {name}: the marble lintel over the road."))
    out.append(block(f'platform:gate_{tag}_frieze', (gx, gy), (span + 16, 496), zt + 96, FRIEZE_H, GOLD, GOLD,
                     facing=face))
    out.append(block(f'platform:gate_{tag}_cornice', (gx, gy), (span + 96, 560), zt + 96 + FRIEZE_H, CORNICE_H,
                     STONE, GOLD, facing=face, bottom_surface=STONE))
    return out


def vault(z):
    """Soul Storage: a small walk-in vault between the Light guild and the temple, its door to the south; shelves
    along its back, the true-name plaque by the last shelf (A3's m31.soul_storage, m31.true_name_plaque)."""
    vx, vy = D.SOUL_STORAGE['room_at']
    rw, rd = D.SOUL_STORAGE['room']
    dx, dy = D.SOUL_STORAGE['door']
    h, t = 640, 64
    x0, x1, y0, y1 = vx - rw / 2, vx + rw / 2, vy - rd / 2, vy + rd / 2
    half_door = 160
    return [
        block('platform:vault_wall_n', (vx, y1 - t / 2), (rw, t), z, h, PANEL, ROOF),
        block('platform:vault_wall_w', (x0 + t / 2, vy), (t, rd - 2 * t), z, h, PANEL, ROOF),
        block('platform:vault_wall_e', (x1 - t / 2, vy), (t, rd - 2 * t), z, h, PANEL, ROOF),
        block('platform:vault_wall_sw', ((x0 + dx - half_door) / 2, y0 + t / 2), (dx - half_door - x0, t), z, h, PANEL,
              ROOF),
        block('platform:vault_wall_se', ((x1 + dx + half_door) / 2, y0 + t / 2), (x1 - dx - half_door, t), z, h, PANEL,
              ROOF),
        block('platform:vault_lintel', (dx, y0 + t / 2), (2 * half_door, t), z + 448, h - 448, PANEL, ROOF,
              bottom_surface=STONE),
        block('platform:vault_roof', (vx, vy), (rw + 64, rd + 64), z + h, 48, TRIM, ROOF, bottom_surface=STONE,
              notes="Soul Storage's roof."),
        block('platform:vault_door', (dx, y0 + 8), (2 * half_door, 16), z, 448, {'texture': 'cwdr', 'size': [128, 256],
              'fit': True}, STONE, end_surface=dict(STONE, fit=False),
              notes="Soul Storage's door: open for the Chosen Ones (m30.done), shut to anyone else."),
        block('platform:vault_shelf', (vx - 128, y1 - t - 96), (rw - 2 * t - 320, 128), z, 448, PLANK, PLANK,
              notes='The empty shelves; the last holds the Soul Box (m31.soul_storage).'),
        block('platform:true_name_plaque', (x1 - t - 128, y1 - t - 4), (96, 8), z + 192, 192,
              {'texture': 't3s2b', 'size': [128, 256], 'fit': True}, STONE, end_surface=dict(STONE, fit=False),
              notes="The plaque by the last shelf (m31.true_name_plaque)."),
    ]


def jetty():
    a, b = D.OLYMPUS_DOCK_START, D.OLYMPUS_DOCK_END
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    out = [platform_slab('platform:olympus_jetty', a, b, OLY_Z + 12, OLY_Z + 12, 640, STONE, MARBLE, 96,
                         "Lucio's marble jetty out over the void (entrance:olympus_dock on its town end).")]
    for side in (1, -1):
        nx, ny = -uy * 304 * side, ux * 304 * side
        cut = D.SKYBOAT_RAIL_OPEN if side > 0 else 0     # rail1 stops short by the moored boat (A6 s24)
        p, q = (a[0] + ux * 1024 + nx, a[1] + uy * 1024 + ny), (b[0] - ux * cut + nx, b[1] - uy * cut + ny)
        out.append(platform_slab(f'platform:olympus_jetty_rail{1 if side > 0 else 2}', p, q, OLY_Z + 12 + 96,
                                 OLY_Z + 12 + 96, 32, STONE, STONE, 96))
    return out


def lookout(z):
    x, y = D.ANTS_LOOKOUT
    return [block('platform:ants_lookout', (x, y), (640, 640), z, 16, MARBLE, MARBLE,
                  notes="The ants' lookout terrace on the west rim (Adonis's line, aaze0037:17).")]


# ------------------------------------------------------------------------------------------------ set pieces

PT = {p['id']: p for p in D.POINTS}


def hatch_plates():
    out = []
    for p in D.POINTS:
        if p['kind'] != 'hatch':
            continue
        z = floor_of(p['space'])
        out.append(block(f"platform:{key(p['id'])}", p['at'], (512, 512), z - 8, 24, STONE, METAL,
                         notes=f"A roof hatch of cloud-stone ({p['text']})."))
    return out


def capstone():
    s = SPACE['room:pyramid_cap']
    cx, cy = s['at']
    z = s['floor']
    door = PT['poi:sky_door']['at']
    return [block('platform:capstone', (cx, cy), (1792, 1792), z + 64, 1536, GOLD_BIG, GOLD_BIG, top_size=[64, 64],
                  bottom_surface=GOLD_BIG, notes="The Great Pyramid's golden capstone, floating a little over its "
                                                 "cloud (D-8)."),
            block('platform:sky_door_frame', (cx + 800, cy), (320, 448), z, 576, GOLD_BIG, GOLD_BIG,
                  notes="The sky door's porch in the capstone's east face."),
            block('platform:sky_door', (cx + 968, cy), (16, 256), z, 512, SKY_DOOR, GOLD_BIG, end_surface=dict(GOLD_BIG, fit=False),
                  notes=f"The Great Pyramid's sky door (xdpyrdor, once): DD-15's top ({PT['poi:sky_door']['text']})."),
            block('platform:sky_door_step', (door[0] - 128, door[1]), (256, 512), z, 16, MARBLE, MARBLE)]


def roost():
    s = SPACE['room:roost']
    cx, cy = s['at']
    z = s['floor']
    return [block('platform:crag', (cx - 1536, cy + 1024), (1152, 896), z - 64, 896, ROCK, ROCK, top_size=[256, 192],
                  notes="The black crag on the roost."),
            block('platform:crag_2', (cx - 1856, cy + 448), (640, 512), z - 48, 496, ROCK, ROCK, top_size=[128, 96])]


def launch():
    """The Broken Launch: a plain marble jetty out over the north rim, no boat (D-8)."""
    s = SPACE['room:broken_launch']
    cx, cy = s['at']
    z = s['floor']
    return [platform_slab('platform:launch_jetty', (cx - 384, cy + 1280), (cx - 384, cy + 3328), z + 12, z + 12, 512,
                          STONE, MARBLE, 96, "The gods' old launch: a plain marble jetty with no boat (D-8).")]


def genie_rock():
    x, y = PT['poi:lamp_angry']['at']
    z = floor_of('room:genie_rock')
    return [block('platform:genie_lamp_rock', (x, y), (384, 320), z, 96, ROCK, ROCK, top_size=[288, 224],
                  notes="The angry genie's rock; his lamp lies on it.")]


def lean_to():
    x, y = PT['poi:chest_stranded_south']['at']
    z = floor_of('room:stranded_south')
    return [block('platform:lean_to', (x, y + 288), (640, 32), z, 320, PLANK, PLANK, notes="The castaway's lean-to."),
            block('platform:lean_to_post1', (x - 320, y - 96), (24, 24), z, 320, PLANK, PLANK),
            block('platform:lean_to_post2', (x + 320, y - 96), (24, 24), z, 320, PLANK, PLANK),
            block('platform:lean_to_roof', (x, y + 96), (704, 448), z + 320, 16, CANVAS_ROOF, CANVAS_ROOF,
                  bottom_surface=CANVAS_ROOF, end_surface=dict(CANVAS_ROOF, fit=False))]


LAKE = SPACE['room:sky_lake']
LAKE_WATER = [(LAKE['at'][0] + 400 + 2400 * math.cos(t), LAKE['at'][1] - 200 + 1900 * math.sin(t))
              for t in [i * math.pi / 12 for i in range(24)]]


def lake():
    z = LAKE['floor']
    cx, cy = LAKE['at']
    out = [prism('platform:lake_water', LAKE_WATER, z - 48, 52, CLOUD_SIDE, WATER,
                 notes='The Sky Lake: shallow water in the cloud bowl (the engine\'s indoor water).')]
    out.append(prism('platform:lake_isle', ring(cx + 400, cy - 200, 448, 12), z, 24, CLOUD_SIDE, CLOUD_TOP,
                     notes='The island of cloud in the lake.'))
    # the scarab stalls: four counters with canvas awnings, their customers on the shore toward the lake
    for p in D.POINTS:
        if p['kind'] != 'scarab':
            continue
        k = key(p['id']).replace('scarab_', '')
        deg = toward_deg(p['at'], (cx + 400, cy - 200))
        phi = math.radians(deg)
        back = frame(p['at'], phi, 0, -224)
        out.append(block(f'platform:stall_{k}', back, (288, 128), z, 112, CANVAS, PLANK, facing=deg - 90,
                         end_surface=dict(CANVAS, fit=False), notes=f"A scarab seller's stall ({p['text']})."))
        out.append(block(f'platform:stall_{k}_awning', frame(back, phi, 0, -48), (320, 288), z + 448, 16, CANVAS_ROOF,
                         CANVAS_ROOF, facing=deg - 90, bottom_surface=CANVAS_ROOF,
                         end_surface=dict(CANVAS_ROOF, fit=False)))
        for i, (u, v) in enumerate(((-144, -176), (144, -176), (-144, 80), (144, 80))):
            out.append(block(f'platform:stall_{k}_post{i + 1}', frame(back, phi, u, v), (16, 16), z, 448, PLANK,
                             PLANK))
    return out


def barges():
    """The merchants' sky-barges are S's decorations now (D.BARGES, gen_objects.decorations(); A6 s24): no blocks."""
    return []


def toll_booths():
    """A plank booth beside the road at each toll, off the walking line (on the island's outer side)."""
    out = []
    for p in D.POINTS:
        if p['kind'] != 'toll':
            continue
        k = key(p['id']).replace('toll_', '')
        at = toll_booth_at(p)
        z = height_at(at)
        out.append(block(f'platform:toll_{k}', at, (384, 384), z, 448, PLANK, PLANK,
                         notes=f"The {k} toll's booth ({p['text']})."))
        out.append(block(f'platform:toll_{k}_roof', at, (512, 512), z + 448, 24, SHINGLE, SHINGLE,
                         bottom_surface=PLANK, end_surface=dict(PLANK, fit=False)))
        # the toll's line: a strip of flags across the island where the road passes the booth (A3's Xeen.toll runs
        # when the party steps on it)
        (ax, ay), (cx, cy) = _toll_axes(p)
        span = toll_span(p)
        x, y = p['at']
        out.append(block(f'platform:toll_{k}_line', (x, y), (span, 256) if ax == 0 else (256, span),
                         height_at(p['at']), 10, FLAG, FLAG,
                         notes=f"The {k} toll's line across the road: stepping on it, the bandits ask (Xeen.toll)."))
    return out


def _toll_axes(p):
    """(along the road, across it toward the room's edge) at a toll."""
    x, y = p['at']
    if abs(abs(y) - D.RING['y']) < 2048:
        return (1, 0), (0, math.copysign(1, y))
    return (0, 1), (math.copysign(1, x), 0)


def toll_booth_at(p):
    """The booth stands 1,024 off the walking line and 512 along the road from the toll, on the side whose cloud holds
    it; the two bandits stand either side of the road (bandit_spots)."""
    (ax, ay), (cx, cy) = _toll_axes(p)
    x, y = p['at']
    for across in (1024, -1024, 896, -896):
        for along in (-512, 512):
            b = (x + ax * along + cx * across, y + ay * along + cy * across)
            if all(inside(P[p['space']], (b[0] + dx, b[1] + dy)) for dx in (-240, 240) for dy in (-240, 240)):
                return b
    raise ValueError(('no room for the toll booth', p['id']))


def toll_span(p):
    """The toll line's length across the walking direction: the island's width there, 192 short of each rim."""
    (ax, ay), (cx, cy) = _toll_axes(p)
    x, y = p['at']
    poly = P[p['space']]
    far = [G.ray_exit(poly, (x, y), (x + sgn * cx * 20000, y + sgn * cy * 20000)) for sgn in (1, -1)]
    return min(1536, int(min(math.hypot(f[0] - x, f[1] - y) for f in far) * 2 - 384) // 32 * 32)


def bandit_spots(p):
    (ax, ay), (cx, cy) = _toll_axes(p)
    x, y = p['at']
    return [(x + cx * 640, y + cy * 640), (x - cx * 640, y - cy * 640)]


def rope():
    x, y = PT['poi:rope']['at']
    z = floor_of('room:rope_head')
    return [block('platform:rope_frame_1', (x, y - 224), (32, 32), z, 640, PLANK, PLANK),
            block('platform:rope_frame_2', (x, y + 224), (32, 32), z, 640, PLANK, PLANK),
            block('platform:rope_beam', (x, y), (48, 480), z + 640, 48, PLANK, PLANK, notes='The rope\'s frame.'),
            block('platform:rope', (x, y), (24, 24), z - 3000, 3640, ROPE, ROPE,
                  notes="The Dark Grove rope, hanging from its frame through the cloud to D1 ('Bucket o' Darkness').")]


def sewer_grate():
    x, y = PT['poi:sewer_stair']['at']
    return [block('platform:sewer_grate', (x, y), (384, 384), OLY_Z + PAVE_RISE, 12, STONE,
                  METAL,
                  notes="The marble grate over the Olympus Sewer's stair (DD-26).")]


def statue_plinths():
    out = []
    for k in range(1, 5):
        x, y = PT[f'poi:statue_{k}']['at']
        out.append(block(f'platform:statue_{k}_plinth', (x, y), (192, 192), OLY_Z + PAVE_RISE, 48, PLINTH, STONE))
    return out


def mirror():
    x, y = PT['poi:mirror']['at']
    z = OLY_Z + PAVE_RISE
    # A6 s30: a gilt frame on all four sides (sill, two posts standing 4 proud, the head) round the silvered glass,
    # placed once, uncut (texture-fit rule); the glass (sunk 4) and the posts (sunk 6) stand in the sill, the head
    # rests on both (no coplanar faces). Was a 384 x 384 slab tiling xkmirror at scale 3 under a head bar only.
    g = dict(GOLD, fit=False)
    return [block('platform:mirror_base', (x, y), (512, 192), z, 64, STONE, STONE),
            block('platform:mirror_sill', (x, y), (448, 48), z + 64, 32, GOLD, GOLD, end_surface=g),
            block('platform:mirror', (x, y), (356, 24), z + 92, 356, {'texture': 'xmirror', 'size': [128, 128],
                  'fit': True}, GOLD, end_surface=g, notes='The Mirror of Olympus (house 4807).'),
            block('platform:mirror_post_w', (x - 200, y), (44, 56), z + 90, 358, GOLD, GOLD, end_surface=g),
            block('platform:mirror_post_e', (x + 200, y), (44, 56), z + 90, 358, GOLD, GOLD, end_surface=g),
            block('platform:mirror_frame', (x, y), (448, 48), z + 448, 48, GOLD, GOLD, end_surface=g,
                  bottom_surface=g)]


# ------------------------------------------------------------------------------------------------ the room

def room_outline():
    hx, hy = min(D.HALF[0], 32640), D.HALF[1]      # the BLV's coordinates are int16: 128 short of 32,768 each side
    return [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]


def build_rooms():
    platforms = clouds()
    lp, beams = links()
    platforms += lp + corners() + boards()
    for p in RESTS:
        platforms += hut(p)
    platforms += olympus() + hatch_plates() + capstone() + roost() + launch() + genie_rock() + lean_to() + lake()
    platforms += barges() + toll_booths() + rope() + sewer_grate() + statue_plinths() + mirror()
    room = {'id': 'room:air', 'space': 'void:cloud_sea', 'name': 'The Skyroads', 'outline': room_outline(),
            'floor': FLOOR, 'ceiling': CEIL, 'platforms': platforms, 'beams': beams,
            'notes': ("The open air over the whole Darkside: one room from the safety floor at -6000 to the sky at "
                      "6400, every wall, floor and ceiling face a sky face. The ring of cloud road and its islands, the "
                      "inner road, Olympus, the corners, the roost and the Sky Lake hang in it.")}
    return {'format': 0, 'themes': [{'id': 'theme:air', 'wall': SKY, 'floor': SKY, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:air', 'ambient': 30}, 'rooms': [room]}


def write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    import gen_objects
    rooms = build_rooms()
    for level in ('L3', 'L4'):
        write_yaml(BRIEF / level / 'rooms.yml', rooms)
    write_yaml(BRIEF / 'L3' / 'objects.yml', {'format': 1, 'start': gen_objects.objects()['start']})
    ps = rooms['rooms'][0]['platforms']
    print('platforms', len(ps), 'beams', len(rooms['rooms'][0]['beams']))
