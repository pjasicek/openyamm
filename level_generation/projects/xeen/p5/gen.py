#!/usr/bin/env python3
"""P5 Clouds of the Ancients: writes the L3 and L4 rooms.yml (A5 sub-agent `agent:a5-p5`, 2026-11-21), after X9's gen.py.

One open-air room (room:air) from the safety floor at -6000 to the sky at 6400; its walls, floor and ceiling are sky
faces. Every cloud is a hanging platform with its L1 outline (geom.blob), a cloud top (xccloud), cloud sides
(xccloudsd) and flared roots. The ring road and the causeway are cloud slabs with a dashed centre line of cloud-stone
flags (7tws1f). Boards stand on lobes of cloud off the road. The stair house is a small black copy of X5's Darkstone
crown; the observatory a pale-stone tower with a stepped dome on the north road's widening; the shrine a gold-paved
disc with the dais; the wedding pavilion and the disc are hidden until m42.done (wiring), the gift chest rides a mover
sunk in the shrine's cloud (objects).

    python3 level_generation/projects/xeen/p5/gen.py     # writes devdocs/xeen/briefs/p5/L3 and L4 rooms.yml (+ L3's start)
"""
import math
import os
import random
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design as D  # noqa: E402
import geom as G  # noqa: E402

ROOT = HERE.parents[3]
BRIEF = ROOT / 'devdocs/xeen/briefs/p5'

FLOOR = -6000          # the safety floor (a fall the one-second check misses ends here and runs the same fall)
CEIL = 6400
SLAB = 256             # cloud slab thickness under its top

# ------------------------------------------------------------------------------------------------ textures
# The lettered boards (A5's lane, D-56 change 8; installed 2026-11-21): one table, so a rename is one line.
BOARD_TEX = {
    'poi:board_nwc': 'xp5nwc', 'poi:board_kings_bounty': 'xp5kb', 'poi:board_inherit': 'xp5ite',
    'poi:board_empire': 'xp5emp', 'poi:board_spaceward': 'xp5sho', 'poi:board_planets': 'xp5pe',
    'poi:board_vegas': 'xp5vg', 'poi:board_tunnels': 'xp5tt', 'poi:board_nuclear': 'xp5nw', 'poi:board_mm': 'xp5mm',
}
BLANK_BOARD = 'xp5brd'
REST_SIGN = 'xp5rest'

CLOUD_TOP = {'texture': 'xccloud', 'size': [256, 256], 'scale': 2}
CLOUD_SIDE = {'texture': 'xccloudsd', 'size': [256, 256], 'scale': 2, 'uneven': True}
SKY = {'texture': 'xccloud', 'size': [256, 256], 'scale': 32, 'sky': True}
FLAG = {'texture': '7tws1f', 'size': [128, 128]}                # X9's cloud-stone flags
PLANK = {'texture': 't66floor', 'size': [128, 128]}             # posts, legs, hut walls, the bench (X9's deck)
SHINGLE = {'texture': 'pxshings', 'size': [128, 128], 'scale': 2}           # the huts' roofs (MM6)
NOTE = {'texture': 'wood012', 'size': [128, 32]}                # the note's plank
BLACK = {'texture': 'gtrlwal1', 'size': [128, 256], 'scale': 2}  # X5's Darkstone black stone (MM8), once up 512
SKULLS = {'texture': 'hkm3b', 'size': [128, 256]}               # X5's skull frieze: one band 256 high
SLATE = {'texture': 'xtslate', 'size': [128, 128], 'scale': 2}              # X5's slate cone
DARK_DOOR = {'texture': '7solid01', 'size': [16, 16]}          # X5's door: a plain dark leaf
PALE = {'texture': 'gtempw1', 'size': [128, 256], 'scale': 4}  # the observatory's pale stone (MM8 temple ashlar; s16: 7tws2 read brown)
DOME = {'texture': 'gn_mtl03', 'size': [128, 128], 'scale': 2}              # the dome: weathered green metal (MM8)
OBS_DOOR = {'texture': 'cwdr', 'size': [128, 256], 'fit': True}  # MM7's stone-framed door with the orb
GOLD = {'texture': '7tws1h', 'size': [128, 128], 'scale': 2}                # pale gold paving (MM7 Celeste): no xp5gold needed
TRIM = {'texture': '7tws1g', 'size': [32, 32], 'scale': 2}                  # the dais's medallion trim, one band 64 high
CANVAS_ROOF = {'texture': 'tentrf1', 'size': [256, 256], 'scale': 2}   # white canvas with its scalloped hem
CANVAS = {'texture': 'tentwal1', 'size': [256, 512], 'scale': 2}       # white-and-grey canvas walls
GILT = {'texture': 'ctflor5', 'size': [128, 128], 'scale': 0.5}                 # the pavilion's gilt posts (MM6 Forge gold)


WORLD = ROOT / 'assets_dev/worlds/xeen'
# S's decorations (D-56 S): placed once their rows exist in the world's decoration_data.txt (names to confirm with S;
# one line each). Until then the dais and the huts stand without them (no stand-ins).
DECO_NAMES = {'cube': 'xeen_cube', 'scepter': 'xeen_scepter', 'hands': 'xeen_stonehand', 'cake': 'xeen_cake',
              'bench': 'xeen_bench'}


def deco_rows():
    names = set()
    for line in open(WORLD / 'models/decoration_data.txt'):
        f = line.split('\t')
        if len(f) > 1 and f[0].strip().isdigit():
            names.add(f[1].strip())
    return names


# P5_DECO=0 keeps them out: S's rows exist since 2026-11-21 03:34, but the indoor studio (merge point 24) reads only
# engine/data_tables/decoration_data.txt and engine/models/indoor_decorations.yml, not the world's `decorations`
# contribution and bindings (request to A1); until then the scratch build runs without them.
DECO = {} if os.environ.get('P5_DECO') == '0' else {k: v for k, v in DECO_NAMES.items() if v in deco_rows()}
BENCH_DECO = 'bench' in DECO


def board_face(tex, size=(256, 128)):
    # the lettered textures are 256 x 128 (REST STOP 256 x 64) at x4: once per face, stretched 4x (2x) on purpose
    return {'texture': tex, 'size': list(size), 'fit': True, 'uneven': True}


SPACE = G.SPACE
POLYS = G.outlines()
OUTLINES = {k: [[int(round(x)), int(round(y))] for x, y in v] for k, v in POLYS.items()}
PLACE = {p['id']: p for p in D.PLACES}
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


SINK = 4               # how far a block standing on the ground is sunk into it (X8's, F62)


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


def prism(pid, outline, z, rise, surface, top=None, notes=None, sink=0, **kw):
    # `sink`: SINK for a prism lying on the cloud (the shrine's paving, the disc; F62, as block())
    e = {'id': pid, 'outline': [[int(round(x)), int(round(y))] for x, y in outline],
         'base': int(round(z - sink - FLOOR)), 'rise': int(round(rise + sink)), 'surface': surface,
         'top_surface': top or surface}
    e.update(kw)
    if notes:
        e['notes'] = notes
    return e


def platform_slab(pid, a, b, z0, z1, width, surface, top_surface, thickness, notes=None, bottom=None):
    """A hanging slab from point a (top z0) to b (top z1), `width` wide (X8's, X9's)."""
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    facing = math.degrees(math.atan2(by - ay, bx - ax))
    low = min(z0, z1) - thickness
    if int(z0) == int(z1) or int(z0 - low) == int(z1 - low):   # level (or within a unit: the studio wants `rise`)
        e = block(pid, ((ax + bx) / 2, (ay + by) / 2), (length, width), low, thickness, surface, top_surface,
                  facing=facing, bottom_surface=bottom or surface)
        if notes:
            e['notes'] = notes
        return e
    entry = {
        'id': pid,
        'at': [int(round((ax + bx) / 2)), int(round((ay + by) / 2))],
        'size': [int(round(length)), width],
        'facing': round(facing, 2),
        'base': int(low - FLOOR),
        'rise': int(min(z0, z1) - low),
        'top_heights': [int(z0 - low), int(z1 - low), int(z1 - low), int(z0 - low)],
        'thickness': thickness,
        'surface': surface,
        'top_surface': top_surface,
        'bottom_surface': bottom or surface,
    }
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


# ------------------------------------------------------------------------------------------------ the road

def link_cut(link, into):
    """The link's two rim points, run `into` each cloud along its line."""
    p, q = G.link_ends(link, POLYS)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    return (p[0] - ux * into, p[1] - uy * into), (q[0] + ux * into, q[1] + uy * into), d, (ux, uy)


ROAD_INTO = 320


def landing_end(poly, start, u, width, margin=24):
    """Where a deck of `width` leaving `start` (on its cloud) along `u` is past the cloud across its whole width: the
    point on the centre line `margin` beyond the furthest bit of cloud under the deck (X8's, F62)."""
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
    """F62 (the player's pins 2026-11-25, X8 "bridge is clipping"; ported to P5 the same day): a road sloping straight
    from inside one cloud to inside the other dipped under the higher cloud's top before its rim. It lies level at
    each cloud's height out to where it is past that cloud across its whole width and slopes only between; where the
    clouds leave no room, level on the higher only. [(p, q, z0, z1)] from a to b."""
    if l['id'] in _SPANS:
        return _SPANS[l['id']]
    a, b, d, (ux, uy) = link_cut(l, ROAD_INTO)
    za8, zb8 = floor_of(l['a']) + 8, floor_of(l['b']) + 8
    width = l['width']

    def along(p, q):
        return (q[0] - p[0]) * ux + (q[1] - p[1]) * uy
    pa = landing_end(POLYS[l['a']], a, (ux, uy), width)
    pb = landing_end(POLYS[l['b']], b, (-ux, -uy), width)
    # a lobe of cloud beside the road (a board's, lobes()) is level: the road lies level across it too, at the height
    # the straight slope had there (else the lobe's top and the road's cross, check_floor_cross floor.cross)
    stretches = []
    for pid in BOARD_TEX:
        if not needs_lobe(pid):
            continue
        f = lobe_front(pid)
        t = along(a, f)
        off = abs((f[0] - a[0]) * uy - (f[1] - a[1]) * ux)
        if off <= width / 2 + 64 and along(pa, f) > -672 and along(f, pb) > -672:
            stretches.append((t - 672, t + 672))
    if za8 == zb8:
        spans = [(a, b, za8, zb8)]
    elif along(pa, pb) >= 64:
        ta, tb = along(a, pa), along(a, pb)

        def point(t):
            return (a[0] + ux * t, a[1] + uy * t)

        def z_at(t):
            return za8 + (zb8 - za8) * (t - ta) / (tb - ta)
        spans = [(a, pa, za8, za8)]
        t0, z0 = ta, za8
        end = [(pb, b, zb8, zb8)]
        for s0, s1 in sorted(stretches):
            if s1 >= tb - 64:
                # the lobe reaches the far landing: the landing runs back across it, at the far cloud's height
                end = [(point(min(s0, tb)), b, zb8, zb8)]
                tb = min(s0, tb)
                break
            if s0 <= t0 + 64:
                # the lobe reaches the near landing (or the last stretch): that level piece runs on across it
                p0, _, zp, _ = spans.pop()
                spans.append((p0, point(s1), zp, zp))
                t0 = s1
                continue
            zl = z_at((s0 + s1) / 2)
            spans += [(point(t0), point(s0), z0, zl), (point(s0), point(s1), zl, zl)]
            t0, z0 = s1, zl
        spans += [(point(t0), point(tb), z0, zb8)] + end
    elif zb8 > za8 and along(a, pb) >= 64 and along(pb, b) >= 64:
        spans = [(a, pb, za8, zb8), (pb, b, zb8, zb8)]
    elif za8 > zb8 and along(a, pa) >= 64 and along(pa, b) >= 64:
        spans = [(a, pa, za8, za8), (pa, b, za8, zb8)]
    else:
        spans = [(a, b, za8, zb8)]
    _SPANS[l['id']] = spans
    return spans


def span_top(spans, pt):
    """The road's top (as laid by link_spans) over the point's projection on the link's line, or None off its ends."""
    for p, q, z0, z1 in spans:
        dx, dy = q[0] - p[0], q[1] - p[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - p[0]) * dx + (pt[1] - p[1]) * dy) / L2 if L2 else 0
        if -1e-6 <= t <= 1 + 1e-6:
            return z0 + (z1 - z0) * t
    return None


def road_slabs():
    """Each link a cloud slab with a cloud top (the cloud road), 8 over its pads' tops at its ends (F62: level over
    each cloud, link_spans)."""
    out = []
    for l in D.LINKS:
        a, b, d, _ = link_cut(l, ROAD_INTO)
        za, zb = floor_of(l['a']), floor_of(l['b'])
        what = 'the causeway (cloud road)' if l['style'] == 'causeway' else 'the cloud road'
        for k, (p, q, z0, z1) in enumerate(link_spans(l)):
            out.append(platform_slab(f"platform:{key(l['id'])}" if k == 0 else f"platform:{key(l['id'])}_{k + 1}", p, q,
                                     z0, z1, l['width'], CLOUD_SIDE, CLOUD_TOP, 192,
                                     f"{l['id']}: {what}, {int(d)} rim to rim, rising {zb - za}" if k == 0 else None))
    return out


def height_at(pt):
    """The walkable top under a point: a road slab, a pad, or None."""
    for l in D.LINKS:
        a, b, _, _ = link_cut(l, ROAD_INTO)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2
        off = abs((pt[0] - a[0]) * dy - (pt[1] - a[1]) * dx) / math.sqrt(L2)
        if 0 <= t <= 1 and off <= l['width'] / 2:
            return span_top(link_spans(l), pt)
    for s in D.SPACES:
        if inside(POLYS[s['id']], pt):
            return s['floor'] + (PAVE_RISE if s['id'] == 'room:shrine' and inside(PAVING, pt) else 0)
    return None


# the shrine's gold paving: a 16-sided disc round the dais, the Pharaoh on it, the pavilion on the cloud behind
PAVE_RISE = 8
SHRINE = PLACE['poi:shrine']['at']
PAVING = ring(SHRINE[0], SHRINE[1], 768, 16, math.pi / 16)


def walk_points():
    return [D.ARRIVAL] + list(D.WALK[1:])


def flags():
    """The dashed centre line: flags 256 long and 128 wide, one every 512 along the walk from the crown's road start
    to the shrine's paving (none across a corner), each a thin slab following the road, 6 over it."""
    out = []
    pts = list(D.WALK[1:])
    k = 0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        n = int((L - 128) // 512)
        for j in range(n):
            s = 192 + 512 * j
            p = (a[0] + ux * s, a[1] + uy * s)
            q = (a[0] + ux * (s + 256), a[1] + uy * (s + 256))
            zp, zq = height_at(p), height_at(q)
            if zp is None or zq is None or inside(PAVING, p) or inside(PAVING, q):
                continue
            zm = height_at(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2))
            if zm is None or abs(zm - (zp + zq) / 2) > 1:
                continue    # F62: a flag over a bend in the road's slope would cut into it (a dash left out)
            k += 1
            # 24 deep (F62: at 16 a flag's bottom lay 2 under a cloud's top where the road runs into it)
            out.append(platform_slab(f'platform:flag_{k}', p, q, zp + 6, zq + 6, 128, FLAG, FLAG, 24))
    return out


# ------------------------------------------------------------------------------------------------ clouds

CLOUDS = D.SPACES


def clouds():
    out = []
    for i, s in enumerate(CLOUDS):
        sid = s['id']
        fl = s['floor']
        out.append({
            'id': f'platform:{key(sid)}', 'outline': OUTLINES[sid], 'base': fl - SLAB - FLOOR, 'rise': SLAB,
            'surface': CLOUD_SIDE, 'top_surface': CLOUD_TOP, 'bottom_surface': CLOUD_SIDE,
            'notes': f"{s['name']}: a cloud, its top at {fl}." + (" Its underside shows from the ring (D-56 9)."
                                                                 if sid == 'room:shrine' else ''),
        })
        ex, ey = s['extent']
        cx, cy = s['at']
        rnd = random.Random(100 + i)
        roots = 3 if ex * ey > 6e6 else 2
        for r in range(roots):
            ox = rnd.uniform(-0.08, 0.08) * ex
            oy = rnd.uniform(-0.08, 0.08) * ey
            top_w = int(0.5 * ex) // 16 * 16
            top_d = int(0.5 * ey) // 16 * 16
            depth = int(rnd.uniform(700, 1300)) // 16 * 16
            out.append({
                'id': f'platform:{key(sid)}_root{r + 1}', 'at': [int(cx + ox), int(cy + oy)],
                'size': [max(160, top_w // 5), max(160, top_d // 5)], 'top_size': [top_w, top_d],
                'base': fl - SLAB + 8 * (r + 1) - depth - FLOOR, 'rise': depth,
                'surface': CLOUD_SIDE, 'top_surface': CLOUD_SIDE, 'bottom_surface': CLOUD_SIDE,
            })
    return out


# ------------------------------------------------------------------------------------------------ boards

BOARD_W, BOARD_H, BOARD_LIFT = 1024, 512, 256
LEG = 384           # legs at +-384 along the board


def ring_point(at):
    x, y = at
    r = D.RING
    if abs(abs(x) - r) < abs(abs(y) - r):
        return (r if x > 0 else -r, y)
    return (x, r if y > 0 else -r)


def board_legs(pid):
    p = PLACE[pid]
    phi = math.radians(COMPASS[p['face']])
    # three legs under both panels (the build stands a block on three or more legs round its middle)
    return [frame(p['at'], phi, u, 4) for u in (-LEG, 0, LEG)]


def ccw(poly):
    area = sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))
    return poly if area > 0 else poly[::-1]


def lobes():
    """A board whose spot or legs lie off every cloud (or within 96 of a rim) stands on a lobe of cloud, 1,280 wide,
    from 640 before its face (onto the road or pad it faces) to 384 behind it. Returns (board id, outline, top)."""
    out = []
    for pid in BOARD_TEX:
        if not needs_lobe(pid):
            continue
        p = PLACE[pid]
        front = lobe_front(pid)
        phi = math.radians(COMPASS[p['face']])
        f = (math.cos(phi), math.sin(phi))
        back = (p['at'][0] - f[0] * 384, p['at'][1] - f[1] * 384)
        z = height_at(front)
        if z is None:
            z = height_at(p['at'])
        a, b, c, e = G.capsule(front, back, 1280)
        oct_ = []
        for u, v in ((a, b), (b, c), (c, e), (e, a)):
            oct_.append((u[0] + (v[0] - u[0]) * 0.18, u[1] + (v[1] - u[1]) * 0.18))
            oct_.append((u[0] + (v[0] - u[0]) * 0.82, u[1] + (v[1] - u[1]) * 0.82))
        out.append((pid, ccw(oct_), int(round(z)) - 4))     # 4 under the pad or road it joins: no faces in one plane
    return out


def needs_lobe(pid):
    """Whether the board's spot or legs lie off every cloud (or within 96 of a rim): it stands on a lobe."""
    pts = [PLACE[pid]['at']] + board_legs(pid)
    return not all(any(inside(POLYS[s['id']], q) for s in D.SPACES) and rim_distance_any(q) > 96 for q in pts)


def lobe_front(pid):
    """The lobe's front end: 640 before the board's face, on the road or pad it faces."""
    p = PLACE[pid]
    phi = math.radians(COMPASS[p['face']])
    return (p['at'][0] + math.cos(phi) * 640, p['at'][1] + math.sin(phi) * 640)


def rim_distance_any(q):
    return max((rim_distance(POLYS[s['id']], q) for s in D.SPACES if inside(POLYS[s['id']], q)), default=0)


LOBES = None


def lobe_of(pid):
    for b, poly, z in LOBES:
        if b == pid:
            return poly, z
    return None


def board_floor(pid):
    lb = lobe_of(pid)
    if lb:
        return lb[1]
    return height_at(PLACE[pid]['at'])


def boards():
    out = []
    for pid, poly, z in LOBES:
        out.append(prism(f'platform:{key(pid)}_lobe', poly, z - 160, 160, CLOUD_SIDE, CLOUD_TOP,
                         bottom_surface=CLOUD_SIDE, notes=f"The lobe of cloud under '{PLACE[pid]['text']}'."))
    for pid, tex in BOARD_TEX.items():
        p = PLACE[pid]
        z = board_floor(pid)
        deg = COMPASS[p['face']]
        phi = math.radians(deg)
        along = deg - 90
        k = key(pid)
        for i, leg in enumerate(board_legs(pid)):
            out.append(block(f'platform:{k}_leg{i + 1}', leg, (32, 32), z, BOARD_LIFT, PLANK, PLANK, facing=along))
        # the lettered front and the blank back, 4 apart (no faces in one plane); their ends plain planks
        out.append(block(f'platform:{k}', frame(p['at'], phi, 0, 10), (BOARD_W, 8), z + BOARD_LIFT, BOARD_H,
                         board_face(tex), PLANK, facing=along, end_surface=dict(PLANK, fit=False),
                         notes=f"'{p['text']}': the lettered front ({tex}), once, whole (fit)."))
        out.append(block(f'platform:{k}_back', frame(p['at'], phi, 0, -2), (BOARD_W, 8), z + BOARD_LIFT, BOARD_H,
                         board_face(BLANK_BOARD), PLANK, facing=along, end_surface=dict(PLANK, fit=False),
                         notes='The blank board behind it.'))
    return out


# ------------------------------------------------------------------------------------------------ the crown

SH = D.STAIR_HOUSE
SH_APOTHEM = SH['radius'] * math.cos(math.pi / 16)
STAIR_DOOR = (SH['at'][0], SH['at'][1] + SH_APOTHEM + 4)


def stair_house():
    """A small black copy of X5's Darkstone crown (A6's thing:darkstone top and top_band): 16 sides of radius 448,
    black stone 512 up (192 sunk into the cloud), the skull frieze 256, a slate cone of 1,562 (three square pyramids
    turned 30 degrees apart round one apex). Its door on the north face (7solid01, once)."""
    cx, cy = SH['at']
    z0 = floor_of('room:crown')
    r = SH['radius']
    outline = ring(cx, cy, r, 16, math.pi / 16)
    P = [prism('platform:stair_house', outline, z0 - 192, SH['wall'] + 192, BLACK,
               notes="The stair house: Darkstone Tower's crown standing up through the cloud (X5's gtrlwal1)."),
         prism('platform:stair_house_frieze', outline, z0 + SH['wall'], SH['band'], SKULLS, BLACK,
               notes="Its skull frieze (X5's hkm3b), one band."),
         ]
    top = z0 + SH['wall'] + SH['band']
    # two square pyramids, one turned 45 degrees: sizes whose turned corners fall on whole units (891 / sqrt 2 =
    # 630.03, 17 / sqrt 2 = 12.02), so every face stays flat
    for k, (turn, base, tip) in enumerate(((0, 890, 18), (45, 891, 17))):
        P.append(block(f'platform:stair_house_cone{k + 1}', (cx, cy), (base, base), top + 8 * k, SH['cone'], SLATE, SLATE,
                       facing=turn, top_size=[tip, tip], notes="The slate cone (X5's xtslate)." if k == 0 else None))
    P.append(block('platform:stair_door', STAIR_DOOR, (256, 8), z0, 448, DARK_DOOR, BLACK,
                   end_surface=dict(BLACK, fit=False),
                   notes="The stair house's door, the way down into Darkstone Tower (aazex129:14): FD-03's "
                         "entrance:p5_stair, sealed until FD-03 is installed."))
    # the Pharaoh's note on a post by the door (the source's (29,7))
    nx, ny = PLACE['poi:pharaoh_note']['at']
    P.append(block('platform:note_post', (nx, ny), (24, 24), z0, 232, PLANK, PLANK))
    P.append(block('platform:note_board', (nx, ny + 16), (192, 8), z0 + 136, 112, NOTE, NOTE,
                   end_surface=dict(NOTE, fit=False), notes="The Pharaoh's note (m42.pharaoh_note)."))
    return P


# ------------------------------------------------------------------------------------------------ Rest Stops

HUTS = ['poi:rest_1', 'poi:rest_2', 'poi:rest_3']


def hut(pid):
    """An open-fronted plank hut at the plan's scale (back wall 768 x 384, sides 512 deep, a shingle roof), a plank
    bench along its back, the REST STOP sign 512 x 128 over its front on the roof's edge."""
    p = PLACE[pid]
    k = key(pid)
    deg = COMPASS[p['face']]
    phi = math.radians(deg)
    along = deg - 90
    z = height_at(p['at'])
    o = p['at']
    P = [block(f'platform:{k}_back', frame(o, phi, 0, -248), (768, 16), z, 384, PLANK, PLANK, facing=along,
               end_surface=dict(PLANK, fit=False), notes=f"{p['text']}: the hut's back wall (clicked)."),
         block(f'platform:{k}_side1', frame(o, phi, -376, 0), (16, 480), z, 384, PLANK, PLANK, facing=along),
         block(f'platform:{k}_side2', frame(o, phi, 376, 0), (16, 480), z, 384, PLANK, PLANK, facing=along),
         block(f'platform:{k}_roof', frame(o, phi, 0, 16), (864, 608), z + 384, 24, SHINGLE, SHINGLE, facing=along,
               bottom_surface=PLANK, end_surface=dict(PLANK, fit=False), notes='The shingle roof.'),
         block(f'platform:{k}_sign', frame(o, phi, 0, 316), (512, 8), z + 408, 128, board_face(REST_SIGN, (256, 64)),
               PLANK, facing=along, end_surface=dict(PLANK, fit=False),
               notes="The REST STOP sign over the front (xp5rest, once, fit)."),
         block(f'platform:{k}_sign_back', frame(o, phi, 0, 302), (512, 8), z + 408, 128, PLANK, PLANK, facing=along,
               end_surface=dict(PLANK, fit=False)),
         ]
    if not BENCH_DECO:
        P.append(block(f'platform:{k}_bench', frame(o, phi, 0, -176), (576, 96), z, 112, PLANK, PLANK, facing=along,
                       notes='A plank bench along the back wall.'))
    return P


# ------------------------------------------------------------------------------------------------ the observatory

OBS = PLACE['landmark:observatory']['at']
OBS_R = 576
OBS_WALL = 960            # with the 64 sunk in the cloud, one 1,024 face: the pale stone once up
OBS_APOTHEM = OBS_R * math.cos(math.pi / 16)


def observatory():
    """A round pale-stone tower (radius 576, 1,024 high) on the north road's widening, a stepped dome of weathered
    metal, its door on the south face (cwdr, once): A3's m42.observatory, never opens. Drawn once, no banners."""
    z = floor_of('room:observatory')
    cx, cy = OBS
    P = [prism('platform:observatory_tower', ring(cx, cy, OBS_R, 16, math.pi / 16), z - 64, OBS_WALL + 64, PALE, DOME,
               notes="The observatory's tower: MM8's pale temple ashlar, once up its 1,024.")]
    zz = z + OBS_WALL
    for i, (r, h) in enumerate(((600, 48), (544, 112), (464, 104), (360, 96), (232, 80), (112, 56))):
        P.append(prism(f'platform:observatory_dome{i + 1}', ring(cx, cy, r, 16, math.pi / 16), zz, h, DOME,
                       notes='The stepped dome (weathered metal).' if i == 0 else None))
        zz += h
    P.append(block('platform:observatory_door', (cx, cy - OBS_APOTHEM - 4), (256, 8), z, 512, OBS_DOOR, PALE,
                   end_surface=dict(PALE, fit=False), notes="The observatory's door: 'The observatory is closed.'"))
    return P


# ------------------------------------------------------------------------------------------------ the shrine

PAV = PLACE['thing:pavilion']['at']
PAV_W, PAV_D, PAV_H = 1536, 1024, 512


def shrine():
    z = floor_of('room:shrine')
    sx, sy = SHRINE
    P = [prism('platform:paving', PAVING, z, PAVE_RISE, GOLD, sink=SINK,
               notes="The shrine's pale gold paving round the dais (MM7's 7tws1h; no new stone, D-56 8)."),
         block('platform:dais', (sx, sy), (1024, 704), z + PAVE_RISE, 64, TRIM, GOLD,
               notes="The Pharaoh's shrine: the dais, 1,024 x 704 and 64 high, facing south (m42.shrine).")]
    return P


def pavilion():
    """The wedding pavilion (state:wedding): four gilt posts, a white canvas roof 1,536 x 1,024 at 576, canvas walls on
    the north, west and east, open to the south. Hidden until m42.done (wiring evt:wedding_hide)."""
    z = floor_of('room:shrine')
    cx, cy = PAV
    hw, hd = PAV_W / 2, PAV_D / 2
    P = []
    for i, (ox, oy) in enumerate(((-hw + 24, -hd + 24), (hw - 24, -hd + 24), (hw - 24, hd - 24), (-hw + 24, hd - 24))):
        P.append(block(f'platform:pavilion_post{i + 1}', (cx + ox, cy + oy), (40, 40), z, PAV_H, GILT, GILT))
    P.append(block('platform:pavilion_roof', (cx, cy), (PAV_W + 64, PAV_D + 64), z + PAV_H, 24, CANVAS_ROOF,
                   CANVAS_ROOF, bottom_surface=CANVAS_ROOF, end_surface=dict(CANVAS_ROOF, fit=False),
                   notes='The pavilion: white canvas roof on four gilt posts (state:wedding).'))
    P.append(block('platform:pavilion_back', (cx, cy + hd - 8), (PAV_W - 96, 16), z, PAV_H, CANVAS, CANVAS,
                   end_surface=dict(CANVAS, fit=False), notes='Its back wall (north).'))
    for nm, sx in (('west', -1), ('east', 1)):
        P.append(block(f'platform:pavilion_{nm}', (cx + sx * (hw - 8), cy + 128), (16, PAV_D - 352), z, PAV_H, CANVAS,
                       CANVAS, end_surface=dict(CANVAS, fit=False)))
    return P


def pavilion_ids():
    return [p['id'] for p in pavilion()]


DISC = PLACE['poi:disc']['at']


def disc():
    z = floor_of('room:shrine')
    return [prism('platform:disc', ring(DISC[0], DISC[1], 192, 12), z, 24, FLAG, FLAG, sink=SINK,
                  notes="The cloud-stone disc back to the crown (state:wedding; D-56 7).")]


# ------------------------------------------------------------------------------------------------ the room

def room_outline():
    hx, hy = D.HALF
    return [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]


def build_rooms():
    global LOBES
    LOBES = lobes()
    platforms = clouds() + road_slabs() + flags() + boards() + stair_house()
    for h in HUTS:
        platforms += hut(h)
    platforms += observatory() + shrine() + pavilion() + disc()
    room = {
        'id': 'room:air', 'space': 'void:sky', 'name': 'Clouds of the Ancients', 'outline': room_outline(),
        'floor': FLOOR, 'ceiling': CEIL, 'platforms': platforms,
        'notes': ("The open air above Darkstone Tower: one room from the safety floor at -6000 to the sky at 6400, "
                  "every wall, floor and ceiling face a sky face. The ring of cloud road, its pads, the boards, the "
                  "Rest Stop huts, the observatory, the stair house and the Pharaoh's shrine hang in it."),
    }
    return {'format': 0, 'themes': [{'id': 'theme:air', 'wall': SKY, 'floor': SKY, 'ceiling': SKY}],
            'defaults': {'theme': 'theme:air', 'ambient': 30}, 'rooms': [room]}


LOBES = lobes()


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
    print('platforms', len(ps), 'flags', sum(1 for p in ps if p['id'].startswith('platform:flag_')),
          'lobes', [key(b) for b, _, _ in LOBES])
    for l in D.LINKS:
        print(f"{l['id']:20s} {int(link_cut(l, 0)[2]):6d}")
