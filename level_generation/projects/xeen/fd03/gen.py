#!/usr/bin/env python3
"""FD-03 Darkstone Tower: writes the L1-L4 project folders of devdocs/xeen/briefs/fd03 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by lane A7's FD-03 sub-agent (seventeenth session, 2026-11-21) after DD-24's gen.py, on D-57
(devdocs/xeen/mockups/act6_a7_decisions.md) and output/studio_cal/a7/phase6_maps.md.

Frame: x east, y north, z up. Four storeys 768 apart (z 0, 768, 1536, 2304) inside a tower of radius 2,048, every
storey three octagonal rings round the open well (a floor hole of apothem 384 through each rotunda's floor, a parapet
192 high round it): the rotunda (apothem 896, 640 high), a wall 192 thick (the gong niches are cut into it), the ring
gallery (apothem 1,088 to 1,440) cut into two arcs and a gap, a wall 64 thick, the outer ring (apothem 1,504 to 2,048)
with the door hall, the stairwells and the side rooms. Octagons have exact 45-degree diagonals (|x|, |y| <= a,
|x| + |y| <= s, s = round(a * sqrt 2)), so facing walls of two rings are parallel. Stairs alternate south (L1-L2,
L3-L4) and north (L2-L3, the south one turned 180 degrees). Each stairwell is open from its storey's floor to the
storey above's ceiling: the flight of 24 steps of 32 climbs the outer wall to its top step, and beside it the 512 x 512
gap where the landing belongs is the slab (a mover: a dais 128 high on the stairwell's floor until its gong raises it
640, flush with the storey above). L3's twin gongs: a riser (the dais, raised 320 by the first gong rung) and a slab
sunk in the floor under it (raised to the top when both are rung)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/fd03'
SQ2 = math.sqrt(2.0)


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.SafeDumper.add_representer(Flow, flow_rep)


def F(*a):
    return Flow(a)


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ surfaces
# MM8 Castle of Fire (d29, A6's towers.yml): gston1wl grey-green granite ashlar (rotundas, landings, the door hall),
# gtrlwal1 dark rubble (the ring galleries, the stairwells, the side rooms), gkp2ceil and gcav1flr floors, gston1fl and
# gcst2cel ceilings, gcstdoor single leaves, gkp4-bs (tan stone) on the parapets and the slabs; X5's hkm3b frieze once
# round the door hall; XD-03's xngong gongs; MM8 gkp103a/gkp103b wings for the two pairs; xafield (D-51) the vault's
# force; three new (Codex, output/studio_cal/fd03/tex): xdplaque, xdhead, xdseal.
# D-89 identity (A7 s27): Darkstone is dark: d29's dark rubble (gtrlwal2) in place of the pale granite ashlar
# (gston1wl), the riveted dark iron ceiling (gcst2cel) in place of the pale fan paving, steel leaves (crsmdr1) on the
# pairs in place of the plank wings.
ASHLAR = S('gtrlwal2', 128, 256, scale=2)   # at twice its size, as RUBBLE: its dark hollows repeat less
RUBBLE = S('gtrlwal1', 128, 256, scale=2)
FLOOR = S('gkp2ceil', 128, 128, scale=2)
FLOOR2 = S('gcav1flr', 256, 256)
CEIL = S('gcst2cel', 128, 128, scale=2)
CEIL2 = S('gcst2cel', 128, 128, scale=2)
DOOR1 = S('gcstdoor', 128, 256, fit=True)
TAN = S('gkp4-bs', 128, 256)
TAN_TOP = S('gkp4-bs', 128, 256, scale=2)
FRIEZE = S('hkm3b', 128, 256)
GONG = S('xngong', 128, 128, fit=True)
PLAQUE = S('xdplaque', 128, 128, fit=True)
HEAD = S('xdhead', 128, 256, fit=True)
FIELD = S('xafield', 128, 256, translucent=0.5)
SEAL_ALPHA = 0.3
SEAL = S('xdseal', 128, 256, fit=True, translucent=SEAL_ALPHA)
WING_L = S('crsmdr1', 128, 256)
WING_R = S('crsmdr1', 128, 256)
TRIM = S('trim9_32', 32, 64)
SKY = S('gston1fl', 128, 128, sky=True)
PIT = S('gcav1flr', 256, 256)

themes = [
    {'id': 'theme:ashlar', 'wall': ASHLAR, 'floor': FLOOR, 'ceiling': CEIL, 'reveal': ASHLAR, 'door': DOOR1,
     'notes': "The tower's halls: d29's grey-green granite ashlar, worn slab floors, fan-paved ceilings."},
    {'id': 'theme:rubble', 'wall': RUBBLE, 'floor': FLOOR2, 'ceiling': CEIL2, 'reveal': ASHLAR, 'door': DOOR1,
     'notes': "The ring galleries, the stairwells and the side rooms: d29's dark rubble walls, flag floors."},
]

# ------------------------------------------------------------------------------------------------ geometry


def sval(a):
    return round(a * SQ2)


def octo(a):
    """The octagon of apothem a, counter-clockwise from the east edge's south end."""
    b = sval(a) - a
    return [(a, -b), (a, b), (b, a), (-b, a), (-a, b), (-a, -b), (-b, -a), (b, -a)]


def hit(a, cut):
    """Where a cut line meets the octagon of apothem a: ('x', c, +1) is the line x = c met toward north (-1 south),
    ('y', c, +1) the line y = c met toward east (-1 west)."""
    axis, c, d = cut
    s = sval(a)
    h = a if abs(c) <= s - a else s - abs(c)
    assert h > 0, (a, cut)
    return (c, d * h) if axis == 'x' else (d * h, c)


def ang(p):
    return math.atan2(p[1], p[0])


def between(poly, p0, p1):
    a0 = ang(p0)
    span = (ang(p1) - a0) % (2 * math.pi)
    out = []
    for v in poly:
        t = (ang(v) - a0) % (2 * math.pi)
        if 1e-9 < t < span - 1e-9:
            out.append((t, v))
    return [v for _, v in sorted(out)]


def clean(pts):
    pts = [tuple(int(round(c)) for c in p) for p in pts]
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    if out[0] == out[-1]:
        out.pop()
    changed = True
    while changed:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) == 0:
                out.pop(i)
                changed = True
                break
    area = sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1]
               for i in range(len(out)))
    assert area > 0, pts
    return out


def ring_piece(ain, aout, cut0, cut1):
    """The piece of the ring between the octagons ain and aout, counter-clockwise from cut0 to cut1."""
    O, I = octo(aout), octo(ain)
    p0o, p1o, p0i, p1i = hit(aout, cut0), hit(aout, cut1), hit(ain, cut0), hit(ain, cut1)
    return clean([p0o] + between(O, p0o, p1o) + [p1o, p1i] + list(reversed(between(I, p0i, p1i))) + [p0i])


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def notch(poly, edge, intervals, depth):
    """Cuts niches (rectangles `depth` deep, outward) into edge `edge` of a counter-clockwise polygon."""
    a, b = poly[edge], poly[(edge + 1) % len(poly)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (u[1], -u[0])
    ins = []
    for t0, t1 in intervals:
        p0 = (a[0] + u[0] * t0, a[1] + u[1] * t0)
        p1 = (a[0] + u[0] * t1, a[1] + u[1] * t1)
        ins += [p0, (p0[0] + n[0] * depth, p0[1] + n[1] * depth), (p1[0] + n[0] * depth, p1[1] + n[1] * depth), p1]
    return poly[:edge + 1] + ins + poly[edge + 1:]


def edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def on_edge(poly, p, tol=1.5):
    """The edge of poly that p lies on, and the distance of p from the edge's start."""
    for i, (a, b) in enumerate(edges(poly)):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        t = (p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1]
        d = abs((p[0] - a[0]) * u[1] - (p[1] - a[1]) * u[0])
        if d <= tol and -tol <= t <= L + tol:
            return i, t
    raise ValueError(f'{p} lies on no edge of {poly}')


def inside(poly, p):
    x, y = p
    c = False
    for (x0, y0), (x1, y1) in edges(poly):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def facing(pa, ia, pb):
    """The edge of polygon pb that faces edge ia of pa across a wall (anti-parallel, 8-520 away, overlapping)."""
    a, b = edges(pa)[ia]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = (u[1], -u[0])
    best = None
    for j, (c, d) in enumerate(edges(pb)):
        M = math.hypot(d[0] - c[0], d[1] - c[1])
        v = ((d[0] - c[0]) / M, (d[1] - c[1]) / M)
        if abs(u[0] * v[0] + u[1] * v[1] + 1) > 1e-6:
            continue
        dist = (c[0] - a[0]) * n[0] + (c[1] - a[1]) * n[1]
        if not 8 <= dist <= 520:
            continue
        tc = (c[0] - a[0]) * u[0] + (c[1] - a[1]) * u[1]
        td = (d[0] - a[0]) * u[0] + (d[1] - a[1]) * u[1]
        lo, hi = max(0, min(tc, td)), min(L, max(tc, td))
        if hi - lo < 16:
            continue
        if best is None or dist < best[1]:
            best = (j, dist, lo, hi)
    assert best, ('no facing wall', ia)
    return best


# ------------------------------------------------------------------------------------------------ the plan
Z = {1: 0, 2: 768, 3: 1536, 4: 2304}
ROT, GIN, GOUT, OIN, OUT = 896, 1088, 1440, 1504, 2048
WELL, PARAPET = 384, 416
rooms, openings, R_ = [], [], {}


def room(id, name, outline, floor, ceiling, theme='theme:rubble', **kw):
    d = {'id': id, 'name': name, 'outline': [list(p) for p in outline], 'floor': floor, 'ceiling': ceiling,
         'theme': theme}
    d.update(kw)
    rooms.append(d)
    R_[id] = d
    return d


def poly(rid):
    return [tuple(p) for p in R_[rid]['outline']]


def op(id, frm, to, at, width, height, link=None, **kw):
    """An opening in the wall of `frm` centred at the point `at` on that wall."""
    pa, pb = poly(frm), poly(to)
    ia, t = on_edge(pa, at)
    jb, _, lo, hi = facing(pa, ia, pb)
    along = (t - lo) / (hi - lo)
    assert width / 2 + 8 <= t - lo and width / 2 + 8 <= hi - t, (id, t, lo, hi, width)
    d = {'id': id, 'from': frm, 'to': to, 'from_wall': ia, 'to_wall': jb, 'along': round(along, 4), 'width': width,
         'height': height}
    if link:
        d['link'] = link
    d.update(kw)
    openings.append(d)


def wall_panel(rid, at, pid, length, bottom, height, surface, notes=None):
    ia, t = on_edge(poly(rid), at)
    p = {'id': pid, 'offset': round(t - length / 2), 'length': length, 'bottom': bottom, 'height': height,
         'surface': surface}
    if notes:
        p['notes'] = notes
    for w in R_[rid].setdefault('walls', []):
        if w['wall'] == ia:
            w['panels'].append(p)
            return
    R_[rid]['walls'].append({'wall': ia, 'panels': [p]})


def inward(rid, at, d):
    """The point d inside the room from the wall point `at`."""
    pa = poly(rid)
    ia, _ = on_edge(pa, at)
    a, b = edges(pa)[ia]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)
    return [round(at[0] + n[0] * d), round(at[1] + n[1] * d)]


def rot180(pts):
    return [(-x, -y) for x, y in pts]


# The rotunda: notches for the gongs' guards (128 deep into the wall, 192 wide) on its east (edge 0) or west
# (edge 4) side, the gong between them.
NOTCH = [(27, 219), (523, 715)]


def rotunda(gongs):
    p = octo(ROT)
    for e in sorted(gongs, reverse=True):
        p = notch(p, e, NOTCH, 128)
    return clean(p)


EAST_GONG = (ROT, 0)
WEST_GONG = (-ROT, 0)
NICHES_E = [(960, -248), (960, 248)]
NICHES_W = [(-960, 248), (-960, -248)]


def parapet():
    o = octo(PARAPET)
    return [{'path': [list(p) for p in o + [o[0]]], 'height': 192, 'thickness': 32, 'surface': ASHLAR,
             'notes': "The well's parapet, 192 high."}]


# The south stairwell's parts (L1-L2 and L3-L4); the north one (L2-L3) is the same turned 180 degrees.
STAIR_S = ring_piece(OIN, OUT, ('x', -1088, -1), ('x', 592, -1))
STAIR_N = clean(rot180(STAIR_S))
TOP_S = rect(-112, -2000, 16, -1776)
SLAB_AT_S = (272, -1760)
FLIGHT_S = ((-832, -1888), (-112, -1888))
PASS_OPEN_S = (-336, -OIN)     # L1 / L3: the passage's way into the stairwell (west of the dais)
LAND_OPEN_S = (272, -OIN)      # L2 / L4: the landing's way onto the slab


def south_gap(ain, aout):
    return ring_piece(ain, aout, ('x', -512, -1), ('x', 512, -1))


def north_gap(ain, aout):
    return ring_piece(ain, aout, ('x', 512, 1), ('x', -512, 1))


def stairwell(rid, name, storey, north, notes):
    z = Z[storey]
    outline = STAIR_N if north else STAIR_S
    sgn = -1 if north else 1
    top = rect(-16, 1776, 112, 2000) if north else TOP_S
    f0, f1 = FLIGHT_S
    if north:
        f0, f1 = (-f0[0], -f0[1]), (-f1[0], -f1[1])
    r = room(rid, name, outline, z, z + 1408, ambient=12, notes=notes)
    r['platforms'] = [{'id': f'platform:top{storey}', 'outline': [list(p) for p in clean(top)], 'rise': 768,
                       'surface': RUBBLE, 'top_surface': FLOOR2,
                       'notes': "The flight's top step (768): its plate gives the voice's line before the gong."}]
    r['flights'] = [{'from': list(f0), 'to': list(f1), 'width': 224, 'steps': 24,
                     'notes': "24 steps of 32 up the outer wall to the top step."}]
    return r


# ------------------------------------------------------------------------------------------------ L1 (z 0)
DOOR_HALL = ring_piece(OIN, OUT, ('x', 512, 1), ('x', -512, 1))
room('room:door_hall', 'Door hall', DOOR_HALL, 0, 640, theme='theme:ashlar', ambient=18,
     bands=[{'height': 192, 'surface': ASHLAR}, {'height': 448, 'surface': FRIEZE}],
     notes="Inside the tower door (north wall): granite ashlar with X5's skull frieze round the walls once; the inner "
           "gate (two leaves) south-west into the west arc, a single door south-east into the east arc. The arrival "
           "from X5 (entrance:x5_door). Quiet: both ways are shut doors (D-57).")
room('room:l1_west', 'West arc (L1)', ring_piece(GIN, GOUT, ('x', -32, 1), ('x', -576, -1)), 0, 512, ambient=14,
     notes="The ring gallery's west half, 352 wide; two plaques on its outer wall (aazex113:3-4).")
room('room:l1_east', 'East arc (L1)', ring_piece(GIN, GOUT, ('x', 576, -1), ('x', 32, 1)), 0, 512, ambient=14,
     notes="The ring gallery's east half; two plaques (aazex113:5-6); the forge door in its outer wall.")
r = room('room:l1_gong', 'Gong rotunda (L1)', rotunda([0]), 0, 640, theme='theme:ashlar', ambient=16,
         notes="The rotunda round the well's foot: the parapet round a pit; the gong on the east wall between two "
               "niches (its two hidden Sentries).")
r['parapets'] = parapet()
r['levels'] = [{'id': 'level:well_foot', 'outline': [list(p) for p in octo(368)], 'floor': -192, 'edge': PIT,
                'surface': PIT, 'notes': "The well's foot, sunk 192 inside the parapet."}]
room('room:l1_pass', 'South passage (L1)', south_gap(GIN, GOUT), 0, 512, ambient=12,
     notes="From the rotunda to the south stairwell, under L2's landing.")
stairwell('room:l1_stair', 'South stair (L1-L2)', 1, False,
          "A stairwell open from L1's floor to L2's ceiling: the flight up the outer wall, the top step, and beside it "
          "the gap where the landing belongs: the slab, a dais 128 high until the L1 gong raises it 640.")
room('room:l1_forge', 'Onyx forge', ring_piece(OIN, OUT, ('y', -512, 1), ('y', 512, 1)), 0, 512, ambient=14,
     notes="A dead end off the east arc: a cold forge where the golems were cut, black blocks by the walls, a T6 chest.")
R_['room:l1_forge']['platforms'] = [
    {'id': 'platform:anvil', 'at': [1792, -320], 'size': [192, 96], 'rise': 112, 'surface': ASHLAR,
     'top_surface': CEIL2, 'notes': "A black anvil block."},
    {'id': 'platform:hearth', 'at': [1984, 192], 'size': [96, 320], 'rise': 64, 'surface': ASHLAR,
     'top_surface': CEIL2, 'notes': "The cold forge's hearth against the outer wall."}]

# ------------------------------------------------------------------------------------------------ L2 (z 768)
z = Z[2]
room('room:l2_landing', 'Landing (L2)', south_gap(GIN, GOUT), z, z + 512, ambient=14,
     notes="The slab's head: when it is up, the way from the south stair; ways west and east into both arcs.")
room('room:l2_west', 'West arc (L2)', ring_piece(GIN, GOUT, ('x', -576, 1), ('x', -576, -1)), z, z + 512, ambient=14,
     notes="Ring gallery, two plaques (aazex114:3-4); the library door in its outer wall.")
room('room:l2_east', 'East arc (L2)', ring_piece(GIN, GOUT, ('x', 576, -1), ('x', 576, 1)), z, z + 512, ambient=14,
     notes="Ring gallery, two plaques (aazex114:5-6).")
r = room('room:l2_gong', 'Gong rotunda (L2)', rotunda([4]), z, z + 640, theme='theme:ashlar', ambient=16,
         notes="The well's second ring; the gong on the west wall between its two niches (two hidden Wardens).")
r['parapets'] = parapet()
room('room:l2_pass', 'North passage (L2)', north_gap(GIN, GOUT), z, z + 512, ambient=12,
     notes="From the rotunda to the north stairwell, under L3's landing.")
stairwell('room:l2_stair', 'North stair (L2-L3)', 2, True,
          "The same stairwell on the north side, its slab sunk until the L2 gong.")
room('room:l2_library', "Mason's library", ring_piece(OIN, OUT, ('y', 512, -1), ('y', -512, -1)), z, z + 512,
     ambient=14, notes="A dead end off the west arc: the builders' plans on tables by the walls, shelves; a T6 chest.")
R_['room:l2_library']['platforms'] = [
    {'id': f'platform:shelf_{i}', 'at': [-1984, y], 'size': [64, 256], 'rise': 320, 'surface': S('gkp1ceil', 128, 128),
     'top_surface': S('gkp1ceil', 128, 128), 'notes': "A shelf of plans against the outer wall."} for i, y in
    ((1, -352), (2, 352))] + [
    {'id': 'platform:plan_table', 'at': [-1800, 0], 'size': [160, 320], 'rise': 96, 'surface': S('gkp1ceil', 128, 128),
     'top_surface': S('gkp1ceil', 128, 128), 'notes': "The builders' plan table."}]

# ------------------------------------------------------------------------------------------------ L3 (z 1536)
z = Z[3]
room('room:l3_landing', 'Landing (L3)', north_gap(GIN, GOUT), z, z + 512, ambient=14,
     notes="The north slab's head; ways west and east into both arcs.")
room('room:l3_west', 'West arc (L3)', ring_piece(GIN, GOUT, ('x', -576, 1), ('x', -576, -1)), z, z + 512, ambient=14,
     notes="Ring gallery, two plaques (aazex115:3-4).")
room('room:l3_east', 'East arc (L3)', ring_piece(GIN, GOUT, ('x', 576, -1), ('x', 576, 1)), z, z + 512, ambient=14,
     notes="Ring gallery, two plaques (aazex115:5-6); the cistern door in its outer wall.")
r = room('room:l3_gong', 'Twin gongs (L3)', rotunda([0, 4]), z, z + 640, theme='theme:ashlar', ambient=16,
         notes="The source's two gongs, on the rotunda's east and west walls, each between two niches: each rung "
               "shows its two Wardens and lifts the south ground 320; both rung, it is up.")
r['parapets'] = parapet()
room('room:l3_pass', 'South passage (L3)', south_gap(GIN, GOUT), z, z + 512, ambient=12,
     notes="From the rotunda to the last stairwell, under L4's landing.")
stairwell('room:l3_stair', 'South stair (L3-L4)', 3, False,
          "The last stairwell: the ground in two stages (a riser raised 320 by the first gong, the slab raised to "
          "the top by the second).")
r = room('room:l3_cistern', 'Rain cistern', ring_piece(OIN, OUT, ('y', -512, 1), ('y', 512, 1)), z, z + 640,
         ambient=12, notes="A dead end: a cistern sunk 128 with sloping sides to step down and out, fed from the roof "
                           "by a shaft of grey light; the Sky Golems; a T6 chest on its rim.")
r['levels'] = [{'id': 'level:cistern', 'outline': [[1744, -160], [1840, -160], [1840, 160], [1744, 160]],
                'floor': z - 128, 'bank': 160, 'surface': PIT, 'edge': TAN,
                'notes': "The cistern's bottom, 128 down, its sides sloping (walked)."}]
r['ceiling_levels'] = [{'outline': [[1712, -128], [1872, -128], [1872, 128], [1712, 128]], 'ceiling': z + 1024,
                        'edge': RUBBLE, 'surface': CEIL2, 'notes': "The rain shaft over the cistern."}]

# ------------------------------------------------------------------------------------------------ L4 (z 2304)
z = Z[4]
room('room:l4_landing', 'Landing (L4)', south_gap(GIN, GOUT), z, z + 512, ambient=14,
     notes="The last slab's head under the top storey's vault; ways west and east into both arcs.")
room('room:l4_west', 'West arc (L4)', ring_piece(GIN, GOUT, ('y', 512, -1), ('x', -576, -1)), z, z + 512, ambient=14,
     notes="Ring gallery: two speaking heads on its outer wall (aazex116:3-4); the hall of the skull's double "
           "doors in its inner wall.")
room('room:l4_east', 'East arc (L4)', ring_piece(GIN, GOUT, ('x', 576, -1), ('x', 576, 1)), z, z + 512, ambient=14,
     notes="Ring gallery: the other two heads (aazex116:5-6); open into the hall of the skull.")
r = room('room:skull_hall', 'Hall of the skull', rotunda([]), z, z + 640, theme='theme:ashlar', ambient=18,
         notes="The top rotunda round the well's head: double doors from the west arc, open from the east arc; the "
               "skull on its plinth by the south wall ('The skull is silent.'); the vault's force north-west, the "
               "seal's room north. The Onyx Golem stands between the well and the seal.")
r['parapets'] = parapet()
r['platforms'] = [{'id': 'platform:skull', 'at': [0, -824], 'size': [160, 144], 'rise': 160, 'surface': ASHLAR,
                   'top_surface': CEIL2, 'notes': "The skull's plinth against the south wall (F3, 2026-11-21: 160 by "
                   "144 and flush with the wall, the skull 64 from every edge; it was 128 by 96, 48 off the wall)."}]
room('room:vault', "The skull's vault", ring_piece(GIN, GOUT, ('x', -576, 1), ('y', 576, -1)), z, z + 512,
     ambient=12, notes="Behind the force ('A force repels you.'): the source's prize as a T6 chest; the force drops "
                       "with the Onyx Golem.")
room('room:seal', 'Foot of the roof stair', north_gap(GIN, GOUT), z, z + 768, theme='theme:ashlar', ambient=16,
     notes="A tall room north of the hall of the skull; in its north wall the roof stair's mouth, closed by the "
           "seal (a translucent leaf, xdseal).")
ROOF = ring_piece(OIN, OUT, ('x', 704, 1), ('x', -704, 1))
r = room('room:roof_stair', 'The roof stair', ROOF, z, z + 1280, ambient=12,
         notes="A tall stair hall in the outer north: through the seal, west along the floor, then the flight of 24 "
               "steps east up the outer wall to the top landing (3,072) under the open hatch.")
r['platforms'] = [{'id': 'platform:roof_head', 'outline': [[128, 1792], [672, 1792], [672, 2048], [128, 2048]],
                   'rise': 768, 'surface': RUBBLE, 'top_surface': FLOOR2,
                   'notes': "The roof stair's head (3,072): entrance:p5_stair on its top step, facing down (west)."}]
r['flights'] = [{'from': [-600, 1904], 'to': [128, 1904], 'width': 224, 'steps': 24,
                 'notes': "24 steps of 32 up the outer wall to the head."}]
r['ceiling_levels'] = [{'outline': [[256, 1824], [544, 1824], [544, 1984], [256, 1984]], 'ceiling': z + 1536,
                        'edge': RUBBLE, 'surface': SKY,
                        'notes': "The open hatch over the head: P5's cloud sky (atmosphere.yml)."}]

# ------------------------------------------------------------------------------------------------ openings


def gap_side(storey, side, north):
    """The point on a gap room's cut wall (west side -1, east side +1) at mid-depth of the gallery."""
    y = -1300 if not north else 1300
    return (side * 512, y)


# L1
op('open:hall_west', 'room:door_hall', 'room:l1_west', (-272, OIN), 384, 384, 'link:door_west')
op('open:hall_east', 'room:door_hall', 'room:l1_east', (288, OIN), 256, 384, 'link:door_east')
op('open:l1w_gong', 'room:l1_west', 'room:l1_gong', (-GIN, 0), 320, 448, 'link:l1w_gong')
op('open:l1e_gong', 'room:l1_east', 'room:l1_gong', (769.5, 769.5), 320, 448, 'link:l1e_gong')
op('open:l1_gong_pass', 'room:l1_gong', 'room:l1_pass', (0, -ROT), 320, 448, 'link:l1_gong_stair')
op('open:l1_pass_stair', 'room:l1_pass', 'room:l1_stair', (-336, -GOUT), 320, 384, 'link:l1_gong_stair')
op('open:l1e_forge', 'room:l1_east', 'room:l1_forge', (GOUT, 0), 256, 384, 'link:l1e_forge')
# L2
op('open:l2_land_stair', 'room:l2_landing', 'room:l1_stair', (272, -GOUT), 448, 448, 'link:l1_up')
op('open:l2_land_w', 'room:l2_landing', 'room:l2_west', (-512, -1234), 288, 384, 'link:l2_land_w')
op('open:l2_land_e', 'room:l2_landing', 'room:l2_east', (512, -1234), 288, 384, 'link:l2_land_e')
op('open:l2w_gong', 'room:l2_west', 'room:l2_gong', (-769.5, -769.5), 320, 448, 'link:l2w_gong')
op('open:l2e_gong', 'room:l2_east', 'room:l2_gong', (GIN, 0), 320, 448, 'link:l2e_gong')
op('open:l2_gong_pass', 'room:l2_gong', 'room:l2_pass', (0, ROT), 320, 448, 'link:l2_gong_stair')
op('open:l2_pass_stair', 'room:l2_pass', 'room:l2_stair', (336, GOUT), 320, 384, 'link:l2_gong_stair')
op('open:l2w_lib', 'room:l2_west', 'room:l2_library', (-GOUT, 0), 256, 384, 'link:l2w_lib')
# L3
op('open:l3_land_stair', 'room:l3_landing', 'room:l2_stair', (-272, GOUT), 448, 448, 'link:l2_up')
op('open:l3_land_w', 'room:l3_landing', 'room:l3_west', (-512, 1234), 288, 384, 'link:l3_land_w')
op('open:l3_land_e', 'room:l3_landing', 'room:l3_east', (512, 1234), 288, 384, 'link:l3_land_e')
op('open:l3w_gong', 'room:l3_west', 'room:l3_gong', (-769.5, 769.5), 320, 448, 'link:l3w_gong')
op('open:l3e_gong', 'room:l3_east', 'room:l3_gong', (769.5, 769.5), 320, 448, 'link:l3e_gong')
op('open:l3_gong_pass', 'room:l3_gong', 'room:l3_pass', (0, -ROT), 320, 448, 'link:l3_gong_stair')
op('open:l3_pass_stair', 'room:l3_pass', 'room:l3_stair', (-336, -GOUT), 320, 384, 'link:l3_gong_stair')
op('open:l3e_cistern', 'room:l3_east', 'room:l3_cistern', (GOUT, 0), 256, 384, 'link:l3e_cistern')
# L4
op('open:l4_land_stair', 'room:l4_landing', 'room:l3_stair', (272, -GOUT), 448, 448, 'link:l3_up')
op('open:l4_land_w', 'room:l4_landing', 'room:l4_west', (-512, -1234), 288, 384, "link:l4_land_w")
op('open:l4_land_e', 'room:l4_landing', 'room:l4_east', (512, -1234), 288, 384, 'link:l4_land_e')
op('open:l4w_skull', 'room:l4_west', 'room:skull_hall', (-GIN, 0), 384, 448, 'link:l4w_skull')
op('open:l4e_skull', 'room:l4_east', 'room:skull_hall', (GIN, 0), 320, 448, 'link:l4e_skull')
op('open:skull_vault', 'room:skull_hall', 'room:vault', (-633.5, 633.5), 256, 384, 'link:skull_vault')
op('open:skull_seal', 'room:skull_hall', 'room:seal', (0, ROT), 384, 448, 'link:skull_seal')
op('open:seal_stair', 'room:seal', 'room:roof_stair', (0, GOUT), 224, 384, 'link:seal_stair')
# The well: a hole through each rotunda's floor onto the one below.
HOLE = [list(p) for p in octo(WELL)]
for up, down, k in (('room:l2_gong', 'room:l1_gong', 1), ('room:l3_gong', 'room:l2_gong', 2),
                    ('room:skull_hall', 'room:l3_gong', 3)):
    openings.append({'id': f'open:well_{k}', 'from': up, 'to': down, 'in': 'floor', 'outline': HOLE,
                     'notes': "The open well (radius 384) through the floor, parapet round it."})

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:rubble', 'ambient': 14}, 'rooms': rooms,
             'openings': openings,
             'notes': "FD-03 Darkstone Tower: x east, y north; four storeys 768 apart round an open well, the door "
                      "from X5 in the north wall of L1, the roof stair in the outer north of L4. Written by "
                      "output/studio_cal/fd03/tools/gen.py."}

# ------------------------------------------------------------------------------------------------ wall panels
for storey, rid, gongs in ((1, 'room:l1_gong', ['E']), (2, 'room:l2_gong', ['W']), (3, 'room:l3_gong', ['W', 'E'])):
    for side in gongs:
        pid = f'panel:gong{storey}' + (side.lower() if storey == 3 else '')
        wall_panel(rid, EAST_GONG if side == 'E' else WEST_GONG, pid, 288, 96, 288, GONG,
                   "A bronze gong on the wall between two niches (XD-03's great gong picture).")

# Plaques (L1-L3) and heads (L4): on the arcs' outer walls, at the middle of the diagonal edges.
D = (GOUT + (sval(GOUT) - GOUT)) / 2   # the diagonal edge's middle: (D, D) up to signs
PLAQUES = {
    1: [('room:l1_west', (-D, D)), ('room:l1_west', (-D, -D)), ('room:l1_east', (D, -D)), ('room:l1_east', (D, D))],
    2: [('room:l2_west', (-D, D)), ('room:l2_west', (-D, -D)), ('room:l2_east', (D, -D)), ('room:l2_east', (D, D))],
    3: [('room:l3_west', (-D, D)), ('room:l3_west', (-D, -D)), ('room:l3_east', (D, -D)), ('room:l3_east', (D, D))],
    4: [('room:l4_west', (-GOUT, -256)), ('room:l4_west', (-D, -D)), ('room:l4_east', (D, -D)),
        ('room:l4_east', (D, D))],
}
# The sixteen rows verbatim from dark/aazex113-116.txt.json lines 3-6 (D-63 9: the source's form, trailing '-' kept,
# nothing added). Read down, each storey gives one message (NEW WORLD THANKS YOU FOR PLAYING ..., ..., TYPE "COMPUTER"
# ON LEVEL 4 OF THE DUNGEON OF DEATH SEE YA SOON!).
ROW_LINES = {
    1: ['A plaque reads: NWDA---Y-HNA', 'A plaque reads: EO-NYFPIMTDG', 'A plaque reads: WRTKOOLNI--I',
        'A plaque reads: -LHSURAGGAMC'],
    2: ['A plaque reads: SNTS-CKDEM', 'A plaque reads: ODHAOO--L!', 'A plaque reads: -SEGFRAST-',
        'A plaque reads: E--A-ANHE-'],
    3: ['A plaque reads: 1-ITN-HNA-A', 'A plaque reads: 9BNHEMTDGS!', 'A plaque reads: 9ESEXI--IA-',
        'A plaque reads: 4G--TGAMCG-'],
    4: ['Head 13 speaks: T-MEOE-FENN-TEAO', 'Head 14 speaks: Y"PRNV4--G-DHE-N', 'Head 15 speaks: PCU"-E-TDEOE--S!',
        'Head 16 speaks: EOT-LLOHUOFASYO-'],
}
for storey, places in PLAQUES.items():
    for i, (rid, at) in enumerate(places, 1):
        if storey < 4:
            wall_panel(rid, at, f'panel:plaque{storey}_{i}', 256, 160, 192, PLAQUE,
                       f"A bronze letter plaque (row {i} of L{storey}).")
        else:
            wall_panel(rid, at, f'panel:head_{i}', 192, 128, 256, HEAD, f"A speaking head of black stone (head {i}).")

# ------------------------------------------------------------------------------------------------ plan.yml
FLOORS = {r['id']: r['floor'] for r in rooms}
SPACES = [
    ('room:door_hall', 'room', 'M', "The arrival (entrance:x5_door): inside the tower door, X5's skull frieze; the inner gate (two leaves) and a single door. Quiet (D-11.3, D-57)."),
    ('room:l1_west', 'corridor', 'M', "The ring gallery's west half; two plaques."),
    ('room:l1_east', 'corridor', 'M', "The east half, two plaques; the forge door."),
    ('room:l1_gong', 'room', 'L', "Set piece: the rotunda round the well's foot; the gong (m41.gong_voice) shows its two hidden Sentries and raises the south slab (118120)."),
    ('room:l1_pass', 'corridor', 'S', "From the rotunda to the south stairwell."),
    ('room:l1_stair', 'stair', 'M', "The stairwell L1-L2: 24 steps of 32 up the outer wall, the top step's plate (the voice before the gong), the slab sunk as a dais until the gong."),
    ('room:l1_forge', 'room', 'M', "A dead end: a cold forge, a T6 chest."),
    ('room:l2_landing', 'stair', 'S', "The slab's head; ways round both arcs."),
    ('room:l2_west', 'corridor', 'M', "Ring gallery, two plaques; the library door."),
    ('room:l2_east', 'corridor', 'M', "Ring gallery, two plaques."),
    ('room:l2_gong', 'room', 'L', "The well's second ring; the gong (118121) shows two hidden Wardens and raises the north slab."),
    ('room:l2_pass', 'corridor', 'S', "From the rotunda to the north stairwell."),
    ('room:l2_stair', 'stair', 'M', "The stairwell L2-L3 (north), the same flight and slab."),
    ('room:l2_library', 'room', 'M', "A dead end: the builders' plans, a T6 chest."),
    ('room:l3_landing', 'stair', 'S', "The north slab's head."),
    ('room:l3_west', 'corridor', 'M', "Ring gallery, two plaques."),
    ('room:l3_east', 'corridor', 'M', "Ring gallery, two plaques; the cistern door."),
    ('room:l3_gong', 'room', 'L', "The twin gongs (118122 west, 118123 east): each shows its two Wardens and lifts the south ground 320."),
    ('room:l3_pass', 'corridor', 'S', "From the rotunda to the last stairwell."),
    ('room:l3_stair', 'stair', 'M', "The stairwell L3-L4: the ground in two stages (riser and slab)."),
    ('room:l3_cistern', 'room', 'M', "A dead end: the rain cistern sunk 128, two Sky Golems, a T6 chest on its rim."),
    ('room:l4_landing', 'stair', 'S', "The last slab's head."),
    ('room:l4_west', 'corridor', 'M', "Ring gallery, two speaking heads; the hall of the skull's double doors."),
    ('room:l4_east', 'corridor', 'M', "Ring gallery, two speaking heads; open into the hall of the skull."),
    ('room:skull_hall', 'room', 'L', "The boss room: the Onyx Golem (85) between the well and the seal; the skull is silent."),
    ('room:vault', 'room', 'S', "Behind the force (xafield 0.5): a T6 chest; the force drops with the Onyx Golem (118124)."),
    ('room:seal', 'room', 'M', "Set piece: the seal (xdseal) across the roof stair's mouth; m41.seal with the Chime."),
    ('room:roof_stair', 'stair', 'M', "The roof stair: 24 steps up to the head under the open hatch; entrance:p5_stair on the top step facing down; the hatch's Yes/No up to P5 (D-66)."),
]
LINKS = [
    ('link:door_west', 'room:door_hall', 'room:l1_west', 'double_door'),
    ('link:door_east', 'room:door_hall', 'room:l1_east', 'door'),
    ('link:l1w_gong', 'room:l1_west', 'room:l1_gong', 'open'),
    ('link:l1e_gong', 'room:l1_east', 'room:l1_gong', 'open'),
    ('link:l1e_forge', 'room:l1_east', 'room:l1_forge', 'door'),
    ('link:l1_gong_stair', 'room:l1_gong', 'room:l1_stair', 'open'),
    ('link:l1_up', 'room:l1_stair', 'room:l2_landing', 'stairs'),
    ('link:l2_land_w', 'room:l2_landing', 'room:l2_west', 'open'),
    ('link:l2_land_e', 'room:l2_landing', 'room:l2_east', 'open'),
    ('link:l2w_gong', 'room:l2_west', 'room:l2_gong', 'open'),
    ('link:l2e_gong', 'room:l2_east', 'room:l2_gong', 'open'),
    ('link:l2w_lib', 'room:l2_west', 'room:l2_library', 'door'),
    ('link:l2_gong_stair', 'room:l2_gong', 'room:l2_stair', 'open'),
    ('link:l2_up', 'room:l2_stair', 'room:l3_landing', 'stairs'),
    ('link:l3_land_w', 'room:l3_landing', 'room:l3_west', 'open'),
    ('link:l3_land_e', 'room:l3_landing', 'room:l3_east', 'open'),
    ('link:l3w_gong', 'room:l3_west', 'room:l3_gong', 'open'),
    ('link:l3e_gong', 'room:l3_east', 'room:l3_gong', 'open'),
    ('link:l3e_cistern', 'room:l3_east', 'room:l3_cistern', 'door'),
    ('link:l3_gong_stair', 'room:l3_gong', 'room:l3_stair', 'open'),
    ('link:l3_up', 'room:l3_stair', 'room:l4_landing', 'stairs'),
    ('link:l4_land_w', 'room:l4_landing', 'room:l4_west', 'open'),
    ('link:l4_land_e', 'room:l4_landing', 'room:l4_east', 'open'),
    ('link:l4w_skull', 'room:l4_west', 'room:skull_hall', 'double_door'),
    ('link:l4e_skull', 'room:l4_east', 'room:skull_hall', 'open'),
    ('link:skull_vault', 'room:skull_hall', 'room:vault', 'door'),
    ('link:skull_seal', 'room:skull_hall', 'room:seal', 'open'),
    ('link:seal_stair', 'room:seal', 'room:roof_stair', 'door'),
]
SENTRY, WARDEN, SKY, ONYX = 11585, 11586, 11594, 11584
NAMES = {SENTRY: 'Onyx Sentry', WARDEN: 'Onyx Warden', SKY: 'Sky Golem', ONYX: 'Onyx Golem'}
LEVELS = {SENTRY: 62, WARDEN: 72, SKY: 75, ONYX: 85}
# Placed monsters: room, group, [(row, at, facing)], hidden. Groups 21, 22, 31, 32: the gongs' guards.
PLACED = [
    ('l1_west', 11, [(SENTRY, (-1264, 300), 90), (SENTRY, (-1264, -300), 270), (SENTRY, (-950, 950), 315)], False),
    ('l1_east', 12, [(SENTRY, (1264, 300), 90), (SENTRY, (1264, -300), 270), (SENTRY, (950, -950), 135)], False),
    ('l1_forge', 13, [(SENTRY, (1680, -128), 180), (SENTRY, (1680, 256), 180)], False),
    ('l1_gong', 21, [(SENTRY, NICHES_E[0], 180), (SENTRY, NICHES_E[1], 180)], True),
    ('l2_west', 14, [(SENTRY, (-1264, 300), 270), (SENTRY, (-950, -950), 45), (WARDEN, (-950, 950), 315)], False),
    ('l2_east', 15, [(SENTRY, (1264, -300), 90), (SENTRY, (950, 950), 225), (WARDEN, (950, -950), 135)], False),
    ('l2_library', 16, [(SENTRY, (-1620, -330), 0), (SENTRY, (-1620, 330), 0)], False),
    ('l2_gong', 22, [(WARDEN, NICHES_W[0], 0), (WARDEN, NICHES_W[1], 0)], True),
    ('l3_west', 17, [(SENTRY, (-1264, 300), 270), (SENTRY, (-950, -950), 45), (WARDEN, (-1264, -300), 90)], False),
    ('l3_east', 18, [(SENTRY, (1264, 300), 270), (SENTRY, (950, -950), 135), (WARDEN, (1264, -300), 90)], False),
    ('l3_cistern', 19, [(SKY, (1600, -380), 180), (SKY, (1600, 380), 180)], False),
    ('l3_gong', 31, [(WARDEN, NICHES_W[0], 0), (WARDEN, NICHES_W[1], 0)], True),
    ('l3_gong', 32, [(WARDEN, NICHES_E[0], 180), (WARDEN, NICHES_E[1], 180)], True),
    ('l4_west', 41, [(WARDEN, (-1264, -300), 90), (WARDEN, (-950, -950), 45), (SKY, (-1264, 300), 270),
                     (SKY, (-760, -1150), 90)], False),
    ('l4_east', 42, [(WARDEN, (1264, -300), 90), (WARDEN, (950, 950), 225), (SKY, (1264, 300), 270),
                     (SKY, (760, -1150), 90)], False),
    ('skull_hall', 43, [(ONYX, (-200, 680), 270), (WARDEN, (-640, -300), 0), (WARDEN, (640, -300), 180)], False),
    ('seal', 44, [(SKY, (-380, 1180), 270), (SKY, (380, 1180), 270)], False),
]
for rid, _, ms, _ in PLACED:
    for _, at, _ in ms:
        assert inside(poly(f'room:{rid}'), at), (rid, at)


def plan_doc(level):
    pops = {}
    for rid, _, ms, hidden in PLACED:
        for mon, _, _ in ms:
            pops.setdefault(f'room:{rid}', {}).setdefault((mon, hidden), 0)
            pops[f'room:{rid}'][(mon, hidden)] += 1
    spaces = []
    for sid, kind, size, purpose in SPACES:
        kind = {'stair': 'corridor'}.get(kind, kind)
        s = {'id': sid, 'name': R_[sid]['name'], 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if sid in pops:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [LEVELS[m], LEVELS[m]],
                                'notes': f"{n} {NAMES[m]} {LEVELS[m]} (placed" + (", hidden until the gong)" if h else ")")}
                               for (m, h), n in pops[sid].items()]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [{'id': i, 'from': f, 'to': t, 'kind': k} for i, f, t, k in LINKS]
    for l in links:
        if l['id'] in ('link:l1_up', 'link:l2_up', 'link:l3_up'):
            l['notes'] = "Up the flight and over the slab, once its gong has raised it."
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "A black tower of four storeys round an open well. 'No Sound No Ground!': on every storey a gong must be rung before the next flight has its top; on the top storey the Onyx Golem guards the roof stair, closed by an invisible seal that only the Chime of Opening breaks.",
        'purpose': "M41 Darkstone Tower: the gongs (m41.gong_voice) raise the ground to each next storey; the Onyx Golem; the seal (m41.seal) and the roof stair to the Clouds of the Ancients (P5). Party 60 to 63; onyx golems 62/72, Sky Golem 75, Onyx Golem 85 (45 placed, D-57 Q14); treasure 6.",
        'mood': "Cold black stone, a hum in the walls, a gong's note that hangs too long; the dark well running up through every floor.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:l1_ring', 'spaces': ['room:door_hall', 'room:l1_west', 'room:l1_gong', 'room:l1_east'],
             'notes': "Round the L1 rotunda by either arc."},
            {'id': 'loop:l2_ring', 'spaces': ['room:l2_landing', 'room:l2_west', 'room:l2_gong', 'room:l2_east'],
             'notes': "Round L2."},
            {'id': 'loop:l3_ring', 'spaces': ['room:l3_landing', 'room:l3_west', 'room:l3_gong', 'room:l3_east'],
             'notes': "Round L3."},
            {'id': 'loop:l4_ring', 'spaces': ['room:l4_landing', 'room:l4_west', 'room:skull_hall', 'room:l4_east'],
             'notes': "Round L4: into the hall of the skull by its double doors or the open east way."}],
        'entrances': [
            {'id': 'entrance:x5_door', 'space': 'room:door_hall', 'kind': 'both', 'facing': 's',
             'how': "From X5's Darkstone Tower door (A6): 256 inside the door, facing south into the tower."},
            {'id': 'entrance:p5_stair', 'space': 'room:roof_stair', 'kind': 'both', 'facing': 'w',
             'how': "From P5's stair house (A5): on the roof stair's top step, facing down the stair (west)."}],
        'critical_path': ['room:door_hall', 'room:l1_west', 'room:l1_gong', 'room:l1_pass', 'room:l1_stair',
                          'room:l2_landing', 'room:l2_west', 'room:l2_gong', 'room:l2_pass', 'room:l2_stair',
                          'room:l3_landing', 'room:l3_west', 'room:l3_gong', 'room:l3_pass', 'room:l3_stair',
                          'room:l4_landing', 'room:l4_west', 'room:skull_hall', 'room:seal', 'room:roof_stair'],
        'return_path': ['room:roof_stair', 'room:seal', 'room:skull_hall', 'room:l4_east', 'room:l4_landing',
                        'room:l3_stair', 'room:l3_pass', 'room:l3_gong', 'room:l3_east', 'room:l3_landing',
                        'room:l2_stair', 'room:l2_pass', 'room:l2_gong', 'room:l2_east', 'room:l2_landing',
                        'room:l1_stair', 'room:l1_pass', 'room:l1_gong', 'room:l1_east', 'room:door_hall'],
        'goals': [{'id': 'goal:seal', 'space': 'room:seal', 'kind': 'use', 'story': 'M41',
                   'what': "The seal (m41.seal): with the Chime of Opening it breaks (seal_broken 111820, 27,000)."}],
        'set_pieces': [
            {'id': 'set:gong_well', 'kind': 'scripted', 'spaces': ['room:l1_gong', 'room:l2_gong', 'room:l3_gong',
                                                                  'room:l1_stair', 'room:l2_stair', 'room:l3_stair'],
             'rule': "A gong rung: the voice, its two hidden guards shown, and the slab of the next flight grinds up out of the dark (map qbits 118120-118123, kept on load)."},
            {'id': 'set:seal', 'kind': 'scripted', 'spaces': ['room:seal'],
             'rule': "The seal: a faint ripple across the roof stair's mouth; the Chime cracks it (m41.seal)."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(rooms), 'sectors': len(rooms), 'monsters_about': 45, 'chests': 4, 'doors': 13,
                   'loops': 4, 'floor_area_munits2': 38},
        'notes': "Size M (20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From act6_graphs/fd03.graph.yml and D-57 (FD-03, Q14-Q21, Q35): the review graph's rooms with geometric names (the L2 and L4 arcs are west and east); the roof stair's head is the top landing of room:roof_stair.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """FD-03 Darkstone Tower (not to scale; plan, north up; four storeys 768 apart round the well)
  L4 2304     [VAULT]-force-.  [FOOT OF THE ROOF STAIR]=seal=[ROOF STAIR -> head 3072, hatch (P5, Yes/No)]
                             [HALL OF THE SKULL: Onyx Golem]  ||pair from [WEST ARC]  open from [EAST ARC]
                                         [LANDING] <- slab (L3 twin gongs: riser 320 + slab)
  L3 1536     [LANDING] <- north slab                      [TWIN GONGS] -> [S. PASSAGE] -> [S. STAIR L3-L4]
              [WEST ARC] [EAST ARC]--door--[RAIN CISTERN]
  L2  768     [N. PASSAGE] -> [N. STAIR L2-L3]   [GONG ROTUNDA L2]   [WEST ARC]--door--[LIBRARY]  [EAST ARC]
              [LANDING] <- south slab
  L1    0     [DOOR HALL] =exit= (X5)  ||inner gate -> [WEST ARC]   door -> [EAST ARC]--door--[FORGE]
              [GONG ROTUNDA L1: well's foot] -> [S. PASSAGE] -> [S. STAIR L1-L2: flight, top step, slab]
"""

# ================================================================================================ objects
ARRIVAL = [0, OUT - 256]
P5_STAIR = [224, 1904]
objects = {'format': 0}
objects['start'] = {'room': 'room:door_hall', 'at': ARRIVAL, 'facing': 's',
                    'notes': "entrance:x5_door: 256 inside the tower door, facing south into the tower."}
objects['arrivals'] = [
    {'entrance': 'entrance:x5_door', 'room': 'room:door_hall', 'at': ARRIVAL, 'facing': 's',
     'notes': "X5's Darkstone Tower door (A6): 256 inside the door, facing south (1536). Quiet: both ways shut."},
    {'entrance': 'entrance:p5_stair', 'room': 'room:roof_stair', 'at': P5_STAIR, 'floor_height': Z[4] + 768,
     'facing': 'w', 'notes': "P5's stair house (A5, D-56): on the roof stair's top step (3,072), facing down (west)."},
]
PAIR = {'pictures': [[WING_L, WING_R]], 'back_pictures': [[WING_L, WING_R]]}
objects['doors'] = [
    dict({'id': 'door:inner_gate', 'opening': 'open:hall_west', 'kind': 'hinged', 'leaves': 2, 'thickness': 32,
          'speed': 96, 'edge_surface': TRIM,
          'notes': "The inner gate: two iron-bound leaves (MM8 gkp103a/gkp103b), swinging apart."}, **PAIR),
    {'id': 'door:east_way', 'opening': 'open:hall_east', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM,
     'notes': "The door hall's east way into the east arc (D-57: a door, so the arc's Sentries cannot reach the arrival)."},
    {'id': 'door:forge', 'opening': 'open:l1e_forge', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The forge's iron door."},
    {'id': 'door:library', 'opening': 'open:l2w_lib', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The library's iron door."},
    {'id': 'door:cistern', 'opening': 'open:l3e_cistern', 'kind': 'hinged', 'thickness': 24, 'surface': DOOR1,
     'back_surface': DOOR1, 'edge_surface': TRIM, 'notes': "The cistern's iron door."},
    dict({'id': 'door:skull_pair', 'opening': 'open:l4w_skull', 'kind': 'hinged', 'leaves': 2, 'thickness': 32,
          'speed': 96, 'edge_surface': TRIM, 'notes': "The hall of the skull's double doors (gkp103a/gkp103b)."},
         **PAIR),
    {'id': 'door:force', 'opening': 'open:skull_vault', 'kind': 'slide_down', 'fold': True, 'thickness': 8,
     'speed': 160, 'surface': FIELD, 'tile': True,
     'notes': "The vault's force (xafield, translucent 0.5, D-51): down when the Onyx Golem dies (118124)."},
    {'id': 'door:seal', 'opening': 'open:seal_stair', 'kind': 'slide_up', 'thickness': 8,
     'speed': 96, 'surface': SEAL,
     'notes': f"The invisible seal (xdseal, translucent {SEAL_ALPHA}): m41.seal with the Chime opens it (111820)."},
]


def slab(mid, storey, north, **kw):
    x, y = SLAB_AT_S
    if north:
        x, y = -x, -y
    d = {'id': mid, 'room': f'room:l{storey}_stair', 'at': [x, y], 'size': [512, 512], 'bottom': 0, 'height': 128,
         'travel': [0, 0, 640], 'speed': 128, 'surface': TAN, 'top_surface': FLOOR2}
    d.update(kw)
    return d


objects['movers'] = [
    slab('mover:slab1', 1, False, notes="L1's slab: a dais 128 high on the stairwell's floor; the L1 gong (118120) "
                                        "raises it 640, flush with L2."),
    slab('mover:slab2', 2, True, notes="L2's slab (north): raised by the L2 gong (118121)."),
    slab('mover:riser3', 3, False, travel=[0, 0, 320],
         notes="L3's riser: the dais, raised 320 by the first of the twin gongs (118122 or 118123): half height 448."),
    slab('mover:slab3', 3, False, bottom=-130, travel=[0, 0, 770],
         notes="L3's slab: sunk in the floor under the riser; raised to 768 (flush with L4) when both twin gongs are "
               "rung (118122 and 118123)."),
]
objects['chests'] = [
    {'id': 'chest:forge', 'room': 'room:l1_forge', 'at': [1980, -320], 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The forge's chest (T6)."},
    {'id': 'chest:library', 'room': 'room:l2_library', 'at': [-1980, 0], 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The mason's chest (T6)."},
    {'id': 'chest:cistern', 'room': 'room:l3_cistern', 'at': [1990, -400], 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The cistern's chest on its rim (T6)."},
    {'id': 'chest:vault', 'room': 'room:vault', 'at': [-1050, 820], 'treasure_level': 6,
     'random_items': 4, 'gold': 6000, 'notes': "The skull's vault: the source's prize as a T6 chest."},
]
objects['monsters'] = []
for rid, group, ms, hidden in PLACED:
    for n, (mon, at, facing) in enumerate(ms, 1):
        mid = f'monster:{rid}_{group}_{n}' if rid in ('l3_gong',) else f'monster:{rid}_{n}'
        if mon == ONYX:
            mid = 'monster:onyx'
        m = {'id': mid, 'room': f'room:{rid}', 'monster': mon, 'at': list(at), 'facing': facing, 'hostile': True,
             'group': group}
        if hidden:
            m['hidden'] = True
            m['notes'] = "A gong's guard in its niche, hidden until the gong is rung (D-18, D-57 Q16)."
        objects['monsters'].append(m)


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [235, 160, 90]
COLD = [150, 160, 190]
CLOUD = [190, 200, 220]
# Wall torches: (room, a point on its wall). Each gets a torch12 in from the wall and a light at it.
TORCHES = [
    ('room:door_hall', (-512, 1760)), ('room:door_hall', (512, 1760)),
    ('room:l1_west', (-GOUT, 300)), ('room:l1_east', (GOUT, -300)), ('room:l1_forge', (OUT, -300)),
    ('room:l1_pass', (-512, -1300)), ('room:l1_stair', (-1088, -1400)),
    ('room:l2_landing', (-300, -GIN)), ('room:l2_west', (-GOUT, -300)), ('room:l2_east', (GOUT, 300)),
    ('room:l2_library', (-OIN, -300)), ('room:l2_pass', (512, 1300)), ('room:l2_stair', (1088, 1400)),
    ('room:l3_landing', (300, GIN)), ('room:l3_west', (-GOUT, -300)), ('room:l3_east', (GOUT, 300)),
    ('room:l3_cistern', (OIN, 300)), ('room:l3_pass', (-512, -1300)), ('room:l3_stair', (-1088, -1400)),
    ('room:l4_landing', (-300, -GIN)), ('room:l4_west', (-GOUT, 300)), ('room:l4_east', (GOUT, -300)),
    ('room:vault', (-D, D)), ('room:seal', (-300, GIN)), ('room:seal', (300, GIN)), ('room:roof_stair', (-400, OIN)),
    ('room:l1_gong', (0, ROT)), ('room:l1_gong', (-633.5, -633.5)), ('room:l2_gong', (0, -ROT)),
    ('room:l2_gong', (633.5, 633.5)), ('room:l3_gong', (-633.5, -633.5)), ('room:l3_gong', (633.5, -633.5)),
    ('room:skull_hall', (-633.5, -633.5)), ('room:skull_hall', (633.5, -633.5)), ('room:skull_hall', (633.5, 633.5)),
]
objects['decorations'] = []
objects['lights'] = []
for i, (rid, at) in enumerate(TORCHES, 1):
    p = inward(rid, at, 12)
    fl = R_[rid]['floor']
    objects['decorations'].append({'id': f'deco:torch_{i:02d}', 'room': rid, 'decoration': 'torch01', 'at': p,
                                   'height': 224})
    objects['lights'].append(light(f'light:torch_{i:02d}', rid, p, 256, 800, FIRE))
objects['lights'] += [
    light('light:hatch', 'room:roof_stair', [400, 1904], 400, 1400, CLOUD, notes="Cloud light down the hatch."),
    light('light:cistern_shaft', 'room:l3_cistern', [1792, 0], 900, 900, COLD, notes="Grey light down the rain shaft."),
    light('light:seal', 'room:seal', [0, 1264], 700, 900, COLD, notes="A cold light at the foot of the roof stair."),
]
objects['decorations'] += [
    {'id': 'deco:skull', 'room': 'room:skull_hall', 'decoration': 'dec29', 'at': [0, -824], 'floor_height': Z[4] + 160,
     'notes': "The skull on its plinth."},
    {'id': 'deco:block_1', 'room': 'room:l1_forge', 'decoration': '7rock03', 'at': [1960, -470]},
    {'id': 'deco:block_2', 'room': 'room:l1_forge', 'decoration': '7rock03', 'at': [1960, 440]},
    {'id': 'deco:bones_1', 'room': 'room:vault', 'decoration': '7dec18', 'at': [-820, 1110]},
    {'id': 'deco:sack_1', 'room': 'room:l2_library', 'decoration': 'bag01', 'at': [-1700, 450]},
    {'id': 'deco:sack_2', 'room': 'room:l2_library', 'decoration': 'bag01', 'at': [-1700, -450]},
]
objects['exits'] = [
    {'id': 'exit:door', 'room': 'room:door_hall', 'wall': 'n', 'size': [224, 448], 'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x5_door',
     'notes': "The tower door's inner face: out onto Darkstone's rock (X5)."},
    {'id': 'exit:hatch', 'room': 'room:roof_stair', 'at': [400, OUT], 'floor_height': Z[4] + 768,
     'size': [192, 320], 'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:p5_roof',
     'notes': "The hatch's ladder under the open sky, up to P5 (its own Yes/No, D-66)."},
]
objects['sounds'] = [
    {'id': 'sound:hum_1', 'room': 'room:l1_gong', 'at': [0, 640], 'sound': 'humming', 'radius': 2600,
     'inner_radius': 800, 'volume': 0.4, 'pan': False, 'notes': "The dungeon bed (D-48), heard centred."},
    {'id': 'sound:hum_3', 'room': 'room:l3_gong', 'at': [0, 640], 'sound': 'humming', 'radius': 2600,
     'inner_radius': 800, 'volume': 0.4, 'pan': False, 'notes': "The dungeon bed (D-48)."},
    {'id': 'sound:hatch_wind', 'room': 'room:roof_stair', 'at': [400, 1904], 'sound': 'whistling wind',
     'radius': 1800, 'inner_radius': 500, 'volume': 0.4, 'pan': False, 'notes': "Wind down the open hatch."},
]

# ================================================================================================ wiring
QB = {'ground_l1': 118120, 'ground_l2': 118121, 'ground_l3w': 118122, 'ground_l3e': 118123, 'vault_open': 118124,
      'seal_broken': 111820}


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def gong_sound(x, y, z):
    return {'lua': f'evt.PlaySoundName("xeen_gong", {x}, {y}, {z})'}


VARS = [f'plaque{s}_{i}' for s in range(1, 5) for i in range(1, 5)] + [f'summary{s}' for s in range(1, 5)] + \
       ['slab3_sent']
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 6,
     'text': "Darkstone Tower: black stone, polished like a mirror. Far above, the stair to the Clouds of the Ancients.",
     'notes': "The arrival line (a new map line, no source text): the errand (M41) and where it goes."},
    {'id': 'evt:way_out', 'preset': 'exit', 'source': 'exit:door', 'title': 'Exit Darkstone Tower',
     'notes': "Out to X5 (installed, A6) through the game's leave window (D-24; meaning aazex113:0 'Exit Darkstone "
              "Tower?'), at X5's entrance:fd03_door's coordinates (-4608, 2560, 1504) facing 512 until the name is in "
              "X5's scene (A6)."},
    {'id': 'evt:door_inner_gate', 'preset': 'door', 'source': 'door:inner_gate', 'title': 'Gate'},
    {'id': 'evt:door_east_way', 'preset': 'door', 'source': 'door:east_way', 'title': 'Door'},
    {'id': 'evt:door_forge', 'preset': 'door', 'source': 'door:forge', 'title': 'Door'},
    {'id': 'evt:door_library', 'preset': 'door', 'source': 'door:library', 'title': 'Door'},
    {'id': 'evt:door_cistern', 'preset': 'door', 'source': 'door:cistern', 'title': 'Door'},
    {'id': 'evt:door_skull', 'preset': 'door', 'source': 'door:skull_pair', 'title': 'Doors'},
    {'id': 'evt:chest_forge', 'preset': 'chest', 'source': 'chest:forge', 'title': 'Chest'},
    {'id': 'evt:chest_library', 'preset': 'chest', 'source': 'chest:library', 'title': 'Chest'},
    {'id': 'evt:chest_cistern', 'preset': 'chest', 'source': 'chest:cistern', 'title': 'Chest'},
    {'id': 'evt:chest_vault', 'preset': 'chest', 'source': 'chest:vault', 'title': 'Chest'},
]
GONGS = [  # event, panel, qbit, mover, group, sound point
    ('gong1', 'panel:gong1', 'ground_l1', 'mover:slab1', 21, (896, 0, 256)),
    ('gong2', 'panel:gong2', 'ground_l2', 'mover:slab2', 22, (-896, 0, 1024)),
    ('gong3w', 'panel:gong3w', 'ground_l3w', 'mover:riser3', 31, (-896, 0, 1792)),
    ('gong3e', 'panel:gong3e', 'ground_l3e', 'mover:riser3', 32, (896, 0, 1792)),
]
for key, panel, bit, mover, group, (sx, sy, sz) in GONGS:
    events.append({'id': f'evt:{key}', 'preset': 'script', 'source': panel, 'title': 'Gong',
                   'condition': {'not': {'qbit': bit}}, 'opens': [mover],
                   'effects': [{'qbit': bit}, gong_sound(sx, sy, sz), {'show_actors': group}, hook('m41.gong_voice'),
                               {'lua': f'evt.PlaySoundName("6stone door0101", {sx}, {sy}, {sz})'}],
                   'else_effects': [gong_sound(sx, sy, sz), hook('m41.gong_voice')],
                   'notes': f"The gong (hover 'Gong', aazex113-116:1): m41.gong_voice, its two hidden guards shown "
                            f"(group {group}, D-18), and {mover} raised (map qbit {QB[bit]}, D-57 Q15). A second "
                            "ring: the voice only."})
    events.append({'id': f'evt:{key}_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': bit},
                   'opens': [mover], 'effects': [{'show_actors': group}],
                   'notes': f"With {QB[bit]} the ground stays up and the guards shown on every load (D-56, D-57)."})
events += [
    {'id': 'evt:slab3', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'qbit': 'ground_l3w'}, {'qbit': 'ground_l3e'}, {'not': {'map_var': 'slab3_sent'}}]},
     'opens': ['mover:slab3'], 'sets': {'map_var': 'slab3_sent'},
     'notes': "Both twin gongs rung: the slab rises out of the floor to the top in the same visit (a second after "
              "the second gong; movers are named only by presets, so the gongs' own handlers cannot test the other bit)."},
    {'id': 'evt:slab3_load', 'preset': 'switch', 'trigger': 'load',
     'condition': {'all': [{'qbit': 'ground_l3w'}, {'qbit': 'ground_l3e'}]}, 'opens': ['mover:slab3'],
     'sets': {'map_var': 'slab3_sent'}, 'notes': "Both bits: the L3 slab is up on every load."},
]
for storey, bits in ((1, ['ground_l1']), (2, ['ground_l2']), (3, ['ground_l3w', 'ground_l3e'])):
    cond = {'not': {'qbit': bits[0]}} if len(bits) == 1 else {'not': {'all': [{'qbit': b} for b in bits]}}
    events.append({'id': f'evt:top{storey}', 'preset': 'script', 'trigger': 'step', 'source': f'platform:top{storey}',
                   'condition': cond, 'effects': [hook('m41.gong_voice')],
                   'notes': "The top step's plate before the gong: the voice's line (aazex113:2, A3's m41.gong_voice "
                            "called, not re-typed), so the party knows what is missing."})
# Plaques and heads: each click shows its row (map text); the click that completes a storey's four also calls A3's
# summary hook (m41.plaques_lN; plaques_l4 writes autonote 4720).
for storey in range(1, 5):
    for i in range(1, 5):
        var = f'plaque{storey}_{i}'
        line = ROW_LINES[storey][i - 1]
        lua_line = line.replace('"', '\\"')
        others = [f'plaque{storey}_{j}' for j in range(1, 5)]
        test = ' and '.join(f'IsAtLeast(MapVar({v}), 1)' for v in others)
        body = (f'if {test} and not IsAtLeast(MapVar(summary{storey}), 1) then\n'
                f'    SetValue(MapVar(summary{storey}), 1)\n'
                f'    evt.StatusText("{lua_line}", 6)\n'
                f'    XeenQuests.hook("m41.plaques_l{storey}")\n'
                f'else\n'
                f'    evt.SimpleMessage("{lua_line}")\n'
                f'end')
        ev = {'id': f'evt:plaque{storey}_{i}' if storey < 4 else f'evt:head_{i}', 'preset': 'script',
              'source': f'panel:plaque{storey}_{i}' if storey < 4 else f'panel:head_{i}',
              'title': 'Plaque' if storey < 4 else 'Head',
              'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}, {'lua': body}],
              'notes': f"aazex11{2 + storey}:{2 + i} verbatim (the row, map text; D-57 Q17, D-63 9): a window; the click that completes "
                       f"the storey's four shows the row in the status line and A3's m41.plaques_l{storey} window "
                       "(two windows in one handler show only the first)."}
        events.append(ev)
events += [
    {'id': 'evt:skull', 'preset': 'text', 'source': 'platform:skull', 'title': 'Skull', 'text': 'The skull is silent.',
     'notes': "aazex116:15 (the riddle 9-14 dropped by A3; D-57 Q18)."},
    {'id': 'evt:force', 'preset': 'text', 'source': 'door:force', 'title': 'Force field',
     'text': 'A force repels you.',
     'notes': "aazex116:0, while the force is up."},
    {'id': 'evt:vault_open', 'preset': 'switch', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'not': {'qbit': 'vault_open'}},
                           {'lua': 'evt.IsMapActorDead(ActorIndex("monster:onyx"))'}]},
     'opens': ['door:force'], 'effects': [{'qbit': 'vault_open'}],
     'notes': "The Onyx Golem's death drops the vault's force in the same visit (map qbit 118124, D-57 Q18)."},
    {'id': 'evt:vault_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'vault_open'},
     'opens': ['door:force'], 'notes': "The force stays down on every load with 118124."},
    {'id': 'evt:seal', 'preset': 'script', 'source': 'door:seal', 'title': 'Shimmering air', 'touch': True,
     'condition': {'lua': 'XeenQuests.can("m41.seal")'}, 'opens': ['door:seal'],
     'effects': [hook('m41.seal'), {'lua': 'evt.PlaySoundName("xeen_mirror_shatter", 0, 1472, 2400)'}],
     'else_effects': [hook('m41.seal')],
     'notes': "Clicked or walked into: A3's m41.seal (with the Chime: taken, seal_broken 111820, 27,000; without: "
              "'An invisible seal prevents passage.'; after: the else_text); the leaf opens in the same visit."},
    {'id': 'evt:seal_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'seal_broken'},
     'opens': ['door:seal'], 'notes': "With seal_broken the roof stair is open on every load (D-57 Q21)."},
    {'id': 'evt:hatch', 'preset': 'script', 'source': 'exit:hatch', 'title': 'Climb to the Clouds of the Ancients',
     'lua': 'evt.MoveToMap(4608, -3968, 0, 512, 0, 0, 0, 1, "xeen_p5.blv")',
     'notes': "F16 (2026-11-22): the game's standard entrance window (OK/Close) in place of the map's old Yes/No. Was: Up to P5 (A5's open-air BLV, installed 06:41 with entrance:fd03_roof): the map's own Yes/No with A3's "
              "m41.roof_exit question 'Climb to the Clouds of the Ancients?' (D-66: a roof or hatch exit into a BLV "
              "asks, as DD-15, DD-08 and FD-04 do; no hook, so no text before it, D-65), then on Yes at once to P5's "
              "entrance:fd03_roof [4608, -3968, 0] facing north (the coordinates are P5's named arrival, written out "
              "because the move waits on the answer)."},
]
wiring = {'format': 0, 'variables': VARS, 'events': events}

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_cloud_sea'},
              'notes': "The hatch over the roof stair's head (its ceiling level's top, sky: true) shows P5's cloud sky "
                       "by the preset's own name (D-56 Q9; P5's alias xeencloud maps to it)."}

project = {
    'identity': {'shape': 'tower', 'family': 'd29',
                 'seen': ["a black tower round an open well through every storey",
                          "dark rubble walls under riveted iron ceilings, steel doors",
                          "the gongs that raise each storey's floor, and the invisible seal on the roof stair"]},
    'format': 0, 'id': 'xeen_fd03', 'name': 'Darkstone Tower', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'FD-03', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [8, 8], 'climbs': 'n'},
    'map_stats': {'id': 9181, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 10,
                  'perception_difficulty': 20, 'refill_days': 672, 'music': 43, 'environment': 'stoneroom',
                  'lock_difficulty': 20, 'bolster': 'LowerToEqual', 'slots': []},
    'neighbours': [
        {'id': 'exit:x5_door', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': 'entrance:fd03_door',
         'arrival_hint': "On X5's Darkstone rock before the tower door: entrance:fd03_door (-4608, 2560, 1504) facing "
                         "north (512), A6's corrected point (the cell it shares with entrance:p5_fall).",
         'notes': "X5 installed (A6) with its named arrival entrance:fd03_door. X5's door:fd03 (thing:darkstone, "
                  "m41.tower_door) names this map's arrival entrance:x5_door: (0, 1792, 0) facing south."},
        {'id': 'exit:p5_roof', 'to': 'xeen_p5.blv', 'kind': 'door', 'arrival': 'entrance:fd03_roof',
         'arrival_hint': "P5's entrance:fd03_roof (4608, -3968, 0) facing north, out of the stair house's door.",
         'notes': "P5 (A5) installed 06:41: the hatch asks its own Yes/No, then moves (wiring evt:hatch). P5's "
                  "door:fd03 names this map's arrival entrance:p5_stair: (224, 1904, 3072) facing west."}],
    'qbits': QB,
    'notes': "Xeen design brief, level L4: FD-03 Darkstone Tower on X5 (M41). D-57: Onyx Sentry 11585 x20, Onyx "
             "Warden 11586 x16, Sky Golem 11594 x8, Onyx Golem 11584 x1 (A2's rows), 45 placed, 60.70k per member; "
             "8 of them the gongs' hidden guards. Rest encounters 0 (D-57). Hooks m41.gong_voice, m41.seal, "
             "m41.plaques_l1-l4 (A3). Map qbits 118120-118124. Music 43. Exits: X5 by name, P5 by the hatch's Yes/No.",
}


def write(folder, docs):
    folder.mkdir(parents=True, exist_ok=True)
    for name, doc in docs:
        if isinstance(doc, str):
            (folder / name).write_text(doc)
        else:
            (folder / name).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


if '--levels' in sys.argv:
    p = dict(project)
    for lv in ('L1', 'L2'):
        p['notes'] = f"Xeen design brief, level {lv}: FD-03 Darkstone Tower (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: FD-03 Darkstone Tower, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
print('written L4')
