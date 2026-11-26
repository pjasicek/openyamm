#!/usr/bin/env python3
"""XD-12 Darzog's Tower: the geometry (rooms, levels, openings) shared by L3 and L4.

The tower is a square keep 6,144 across (interior -3072..3072) round a central octagonal shaft 1,792 across that rises
from the gate floor to the open sky. Four floors 768 apart (0, 768, 1536, 2304; rooms 640 high) and a battlemented roof
at 3072. Each floor is a double ring: four galleries in a pinwheel round the shaft, and outside them four side rooms
and four corner rooms. The stairs are two-storey halls in the west and east side rooms, alternating (west 0-768, east
768-1536, west 1536-2304, east 2304-roof), so every floor is crossed. Outside the keep a band of open air 1,024 wide
(the island's shore and Lake Darzog, under the open sky) is seen from the windows and the roof.
"""
import math

A = 3072      # tower interior half size
B = 1920      # outer ring's inner edge
G = 1792      # galleries' outer edge
I = 1024      # galleries' inner edge
S = 896       # shaft half size (octagon)
C = 512       # shaft chamfer: octagon corners at (+-C, +-S), (+-S, +-C)
W = 3328      # outside band's inner edge (the keep's outer wall is 256 thick)
O = 16384     # outside band's outer edge (the lake out to the haze: the view distance)
FL = [0, 768, 1536, 2304]      # floor heights
CE = [640, 1408, 2176, 2944]   # ceilings of ordinary rooms
ROOF = 3072
SKY = 4224


def S_(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------- surfaces (families)
# Castle Gloaming (MM7 d03): the keep's dark stone, its red rock, green-black ceiling blocks, rusty flags, the inlaid rug.
CNB = S_('cnb', 128, 256)
CNBL = S_('cnb1el', 128, 256)
CNBR = S_('cnb1er', 128, 256)
CWB1 = S_('cwb1', 128, 256)
CWB = S_('cwb', 128, 256)
CKB = S_('ckb', 128, 256)
T4 = S_('t4s1fl', 128, 128)
TFB03 = S_('tfb03', 128, 128)
CFB1 = S_('cfb1', 128, 128)
PLANKS = S_('7trimd', 128, 256)
PLANKSA = S_('7trimda', 256, 128)
LAVA = {'texture': 'lava', 'size': [256, 256], 'liquid': 'lava', 'flow': 'left'}
PORT = [S_('cnbport-%d' % i, 128, 256) for i in (1, 2, 3, 4)]
BANNER_A = S_('necro-a', 128, 256)
BANNER_B = S_('necro-b', 128, 256)
TAPESTRY = S_('tap10', 128, 256)
RUG = {k: S_('tfb1r4' + k, 128, 128) for k in 'abcdefgh'}
RUGF = S_('tfb1r4j', 64, 64)
RUGM = S_('tfb1r4i', 64, 64)
# The School of Sorcery (MM7 7d14): the library floor.
TWB2 = S_('twb2', 128, 256)
TFB7 = S_('7tfb1', 128, 128)
TFB2 = S_('tfb2', 128, 128)
S2B = S_('7t1s2b', 128, 256)
BOOKS = S_('7t1books', 128, 256)
BOOKS2 = S_('7t1books2', 128, 256)
WOOD = S_('7t1books1', 128, 128)
CRACK = S_('c1t1fl', 128, 128)
TFS1 = S_('tfs1', 128, 128)
TWB3 = S_('twb3', 128, 256)
CIRCLE = S_('td1', 512, 512)
GRATE = S_('c1d1', 128, 256)
SOSDOOR = S_('hhm1d2', 128, 256)
TRIM5 = S_('trim5_32', 32, 64)
TRIM7 = S_('trim7_32', 32, 64)
# Outside: the island's grass, the lake, the sky (the generated sky of XD-04 as the stand-in picture of sky faces).
GRASS = S_('7grastyl', 128, 128)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
SKYS = {'texture': 'xwsky', 'size': [512, 512], 'scale': 2, 'sky': True}
# The cloud stair: X8's cloud tiles (seamless, 256 square): walkable cloud tops, cloud sides on the risers.
CLOUD_TOP = S_('xccloud', 256, 256)
CLOUD_SIDE = S_('xccloudsd', 256, 256)

THEMES = [
    {'id': 'theme:gate', 'wall': CNB, 'floor': TFB03, 'ceiling': T4, 'reveal': CWB, 'door': PLANKS,
     'notes': "Gate floor (0): Castle Gloaming (MM7 d03) as that map lays it: grey keep stone cnb on the walls, its green-black blocks t4s1fl overhead, its rusty flags tfb03 underfoot, brick cwb in the doorways, plank leaves 7trimd."},
    {'id': 'theme:works', 'wall': CWB1, 'floor': CFB1, 'ceiling': T4, 'reveal': CNB, 'door': PLANKS,
     'notes': "The construct works (768): Castle Gloaming's red rock cwb1 (its lower halls' walls and ceilings), red granite cfb1 floors, the same ceiling blocks; lava channels as Gloaming has them."},
    {'id': 'theme:library', 'wall': TWB2, 'floor': TFB7, 'ceiling': TFB2, 'reveal': S2B, 'door': SOSDOOR,
     'notes': "The library (1536): the School of Sorcery (MM7 7d14) as it lays it: block walls twb2, flags 7tfb1, plaster ceilings tfb2, its carved doors hhm1d2, bookcases 7t1books, its cracked flags c1t1fl (the trapdoors' tell) and its summoning circle td1."},
    {'id': 'theme:darzog', 'wall': CNB, 'floor': TFB03, 'ceiling': T4, 'reveal': CWB, 'door': PLANKS,
     'notes': "Darzog's floor (2304): Castle Gloaming's state rooms: keep stone with its portraits cnbport, banners necro-a/b and the tapestry tap10, the inlaid rug tfb1r4 in the hall."},
    {'id': 'theme:sky_stair', 'wall': SKYS, 'floor': TFB03, 'ceiling': SKYS, 'reveal': CWB, 'door': PLANKS,
     'notes': "The sky stair: Darzog's floor's keep stone (the band, up to the roof's parapet) under the open sky."},
    {'id': 'theme:shaft', 'wall': SKYS, 'floor': CFB1, 'ceiling': SKYS, 'reveal': CWB,
     'notes': "The Well: Gloaming's keep stone from the gate floor to the sky, brick courses (cwb) at every floor, open to the sky above the roof."},
    {'id': 'theme:roof', 'wall': SKYS, 'floor': TFB03, 'ceiling': SKYS, 'reveal': CNB,
     'notes': "The roof: Gloaming's flags under the open sky; every wall a parapet of keep stone (the band) with sky above it."},
    {'id': 'theme:outside', 'wall': SKYS, 'floor': GRASS, 'ceiling': SKYS, 'reveal': CNB,
     'notes': "Outside the keep (seen, never walked): the keep's outer wall in Gloaming's stone, the island's grass (7grastyl), Lake Darzog (7wtrtyl), the open sky beyond."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octagon_shaft():
    return [[-C, -S], [C, -S], [S, -C], [S, C], [C, S], [-C, S], [-S, C], [-S, -C]]


# ------------------------------------------------------------------------------------------- rooms and openings
ROOMS = {}
ORDER = []
OPENINGS = []


def room(rid, name, outline, floor, ceiling, theme, **kw):
    d = {'id': rid, 'name': name, 'outline': outline, 'floor': floor, 'ceiling': ceiling, 'theme': theme}
    d.update(kw)
    ROOMS[rid] = d
    ORDER.append(rid)
    return d


def _edges(outline):
    n = len(outline)
    for i in range(n):
        a = outline[i]
        b = outline[(i + 1) % n]
        yield i, a, b


def _side(a, b):
    # facing of a CCW edge (outward normal)
    if a[1] == b[1]:
        return 's' if b[0] > a[0] else 'n'
    if a[0] == b[0]:
        return 'e' if b[1] > a[1] else 'w'
    return None


OPP = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}


def shared(frm, to, side):
    """The stretch the from-room's walls facing `side` share with the to-room's opposite walls: (lo, hi, edge index,
    edge index of to) along the wall's axis, the first such pair (nearest in thickness)."""
    best = None
    fo = ROOMS[frm]['outline']
    tt = ROOMS[to]['outline']
    for i, a, b in _edges(fo):
        if _side(a, b) != side:
            continue
        for j, c, d in _edges(tt):
            if _side(c, d) != OPP[side]:
                continue
            if side in 'ns':
                gap = (c[1] - a[1]) if side == 'n' else (a[1] - c[1])
                lo = max(min(a[0], b[0]), min(c[0], d[0]))
                hi = min(max(a[0], b[0]), max(c[0], d[0]))
            else:
                gap = (c[0] - a[0]) if side == 'e' else (a[0] - c[0])
                lo = max(min(a[1], b[1]), min(c[1], d[1]))
                hi = min(max(a[1], b[1]), max(c[1], d[1]))
            if gap < 0 or gap > 512 or hi - lo <= 0:
                continue
            if best is None or gap < best[4]:
                best = (lo, hi, i, j, gap)
    if best is None:
        raise SystemExit(f'no shared wall {frm} -> {to} facing {side}')
    return best


SPANS = {}     # (room, edge index) -> list of (from, to) distances from the edge's start that openings take


def _span(rid, idx, axis_lo, axis_hi):
    o = ROOMS[rid]['outline']
    a = o[idx]
    b = o[(idx + 1) % len(o)]
    k = 0 if a[1] == b[1] else 1
    if b[k] > a[k]:
        s, e = axis_lo - a[k], axis_hi - a[k]
    else:
        s, e = a[k] - axis_hi, a[k] - axis_lo
    SPANS.setdefault((rid, idx), []).append((s, e))


def op(oid, frm, to, side, centre=None, width=None, height=None, sill=None, **kw):
    """An opening from `frm` through its wall facing `side` into `to`; `centre` the coordinate of its middle along
    the wall (x for n/s walls, y for e/w walls)."""
    lo, hi, i, j, gap = shared(frm, to, side)
    d = {'id': oid, 'from': frm, 'to': to}
    if width == 'full':
        d['width'] = 'full'
    else:
        if centre is None:
            centre = (lo + hi) / 2
        if width is not None and (centre - width / 2 < lo + 16 - 1e-6 or centre + width / 2 > hi - 16 + 1e-6):
            raise SystemExit(f'{oid}: opening {centre}+-{width / 2} outside shared stretch {lo}..{hi}')
        # along runs counter-clockwise along the from-room's wall: +x on a south wall, +y on an east wall, -x on a
        # north wall, -y on a west wall.
        t = (centre - lo) / (hi - lo)
        if side in ('n', 'w'):
            t = 1 - t
        d['along'] = round(t, 4)
        d['width'] = width
    if width == 'full':
        _span(frm, i, lo, hi)
        _span(to, j, lo, hi)
    else:
        _span(frm, i, centre - width / 2, centre + width / 2)
        _span(to, j, centre - width / 2, centre + width / 2)
    if height is not None:
        d['height'] = height
    if sill is not None:
        d['sill'] = sill
    d['from_wall'] = i
    d['to_wall'] = j
    d.update(kw)
    OPENINGS.append(d)
    return d


def floor_rooms(f, prefix, theme, names):
    """The double ring of one floor: galleries (pinwheel) and corners and the side rooms named in `names`
    (n, s, e, w: None leaves the side out: a stair hall stands there)."""
    z = FL[f]
    c = CE[f]
    gal = {
        'n': rect(-G, I, I, G),
        'e': rect(I, -I, G, G),
        's': rect(-I, -G, G, -I),
        'w': rect(-G, -G, -I, I),
    }
    for k in 'nesw':
        gid, gname = names['g' + k]
        room(gid, gname, gal[k], z, c, theme)
    corner = {
        'ne': rect(B, B, A, A), 'nw': rect(-A, B, -B, A), 'se': rect(B, -A, A, -B), 'sw': rect(-A, -A, -B, -B),
    }
    for k in ('ne', 'nw', 'se', 'sw'):
        if names.get(k):
            cid, cname = names[k]
            room(cid, cname, corner[k], z, c, theme)
    side = {'n': rect(-G, B, G, A), 's': rect(-G, -A, G, -B), 'e': rect(B, -G, A, G), 'w': rect(-A, -G, -B, G)}
    for k in 'nsew':
        if names.get(k):
            sid, sname = names[k]
            room(sid, sname, side[k], z, c, theme)
    # the gallery ring's four joins (no wall: one ring)
    gn, ge, gs, gw = names['gn'][0], names['ge'][0], names['gs'][0], names['gw'][0]
    op(f'open:{prefix}_ring_ne', gn, ge, 'e', width='full', height='full')
    op(f'open:{prefix}_ring_se', ge, gs, 's', width='full', height='full')
    op(f'open:{prefix}_ring_sw', gs, gw, 'w', width='full', height='full')
    op(f'open:{prefix}_ring_nw', gw, gn, 'n', width='full', height='full')


def stair_hall(rid, name, side, f, ceiling, theme, rising, solid=None, **kw):
    """A two-storey hall in the west or east side room from floor f to floor f+1: a hanging gallery at the upper
    floor along the end it rises to and along its inner wall, and one long flight up the outer wall. `solid`: the
    surface of the flight's risers and the gallery's sides (default the room's wall, which is the sky in an open-air
    hall)."""
    z = FL[f]
    up = z + 768
    if side == 'w':
        x0, x1 = -A, -B
        outer_x = (-A + 64, -A + 448)      # the flight's strip along the west wall
        inner = (-B - 384, -B)             # gallery strip along the east wall
    else:
        x0, x1 = B, A
        outer_x = (A - 448, A - 64)
        inner = (B, B + 384)
    if rising == 'n':
        end = (1152, G)                    # the gallery across the north end
        bal = [[x0, end[0]], [x1, end[0]], [x1, end[1]], [x0, end[1]]]
        strip = [[inner[0], -G], [inner[1], -G], [inner[1], end[0]], [inner[0], end[0]]]
        ffrom, fto = -1408, 1152
    else:
        end = (-G, -1152)
        bal = [[x0, end[0]], [x1, end[0]], [x1, end[1]], [x0, end[1]]]
        strip = [[inner[0], end[1]], [inner[1], end[1]], [inner[1], G], [inner[0], G]]
        ffrom, fto = 1408, -1152
    # one L-shaped hanging gallery: the end and the inner strip as one outline (CCW)
    if side == 'w' and rising == 'n':
        out = [[-A, 1152], [inner[0], 1152], [inner[0], -G], [-B, -G], [-B, G], [-A, G]]
    elif side == 'w' and rising == 's':
        out = [[-A, -G], [-B, -G], [-B, G], [inner[0], G], [inner[0], -1152], [-A, -1152]]
    elif side == 'e' and rising == 'n':
        out = [[B, -G], [inner[1], -G], [inner[1], 1152], [A, 1152], [A, G], [B, G]]
    else:
        out = [[B, -G], [A, -G], [A, -1152], [inner[1], -1152], [inner[1], G], [B, G]]
    fx = (outer_x[0] + outer_x[1]) // 2
    r = room(rid, name, rect(x0, -G, x1, G), z, ceiling, theme, **kw)
    r.setdefault('platforms', []).append(
        {'id': f'platform:{rid.split(":")[1]}_gallery', 'outline': out, 'base': up - z - 32, 'rise': 32,
         'notes': 'The hanging gallery at the upper floor, along the end the stair rises to and the inner wall.'})
    r.setdefault('flights', []).append(
        {'from': [fx, ffrom], 'to': [fx, fto], 'to_height': up, 'width': 384, 'steps': 24, 'open_below': 32,
         'notes': 'One long flight up the outer wall, 24 steps of 32, open underneath.'})
    if solid:
        r['platforms'][-1]['surface'] = solid
        r['flights'][-1]['riser'] = solid
    return r

TRAPDOORS = [
    # (id, upper room, lower room, centre)
    ('trap1', 'room:library_n', 'room:works_n', (-1152, 1408)),
    ('trap2', 'room:reading_room', 'room:forge', (1216, 2496)),
    ('trap3', 'room:library_w', 'room:works_w', (-1408, -1152)),
    ('trap4', 'room:study_se', 'room:parts_store', (2240, -2560)),
    ('trap5', 'room:study_nw', 'room:scrap_hall', (-2496, 2304)),
]


def edge_len(rid, idx):
    o = ROOMS[rid]['outline']
    a = o[idx]
    b = o[(idx + 1) % len(o)]
    return abs(b[0] - a[0]) + abs(b[1] - a[1])


def free_alongs(rid, idx, count, clear=112, extra=()):
    """`count` places along the wall (as `along`, 0..1 from its start corner), evenly spread over the free stretches
    (clear of the wall's openings and of `extra` spans by `clear`)."""
    L = edge_len(rid, idx)
    taken = sorted(SPANS.get((rid, idx), []) + list(extra))
    free = []
    cur = clear
    for s, e in taken:
        if s - clear > cur:
            free.append((cur, s - clear))
        cur = max(cur, e + clear)
    if L - clear > cur:
        free.append((cur, L - clear))
    free = [f for f in free if f[1] - f[0] >= 32]
    if not free:
        return []
    total = sum(f[1] - f[0] for f in free)
    out = []
    for n in range(count):
        t = (n + 0.5) / count * total
        for s, e in free:
            if t <= e - s:
                out.append(round((s + t) / L, 4))
                break
            t -= e - s
    return out
