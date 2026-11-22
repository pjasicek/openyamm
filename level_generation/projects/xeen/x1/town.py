"""X1 second pass: Vertigo as a town grown together, not rows of one barn (the user's walk and the by-eye review,
output/studio_cal/x1/review/REVIEW.md). Imported by gen.py.

What is here: a small kit of house shapes said in the studio's words (parts, roofs, porches, signs, round parts,
tiers, upper storeys that reach out), the town's plots (turned 5-30 degrees to their streets, in clusters round
yards and lanes), its streets (only straight runs and 45-degree steps: the classic road tiles tear on any other
slope), a path from every door to a road, the town wall as a fortification (thick crenellated runs on a footing
course, round towers at the corners and every 2,500-3,500, gatehouses of two towers and a passage), wells, fences,
stalls, gardens, trees and flowers, and a check that no road or path runs under a building.
Coordinates: cells [x, y], x east, y south.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys as _sys
_sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import kit_pieces as KIT   # D-94/D-95: the shared water end and sunken entrance
import os


_CLASSES = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../../assets_dev/engine/models/texture_classes.yml')


def sign_size(texture, default=(96, 96)):
    """A sign board as large as its picture (texture_classes.yml `size`), so the picture shows once (texture fit;
    A6's classes of 21:58 made the shop signs pictures meant once)."""
    import re
    for line in open(_CLASSES):
        if line.startswith('  %s: ' % texture):
            m = re.search(r'size: \[(\d+), (\d+)\]', line)
            if m:
                return [int(m.group(1)), int(m.group(2))]
    return list(default)

# ---------------------------------------------------------------------------------------------------------------
# House shapes. Local frame: u along the front (0..F map units), v from the front wall back (0..D). Turned into the
# plot's frame by its facing (a plot's parts are named before its `turn`).
# ---------------------------------------------------------------------------------------------------------------
ALONG = {'n': 'ew', 's': 'ew', 'e': 'ns', 'w': 'ns'}
ACROSS = {'n': 'ns', 's': 'ns', 'e': 'ew', 'w': 'ew'}

def plot_extent(facing, fp):
    f, d = fp[0] * 512, fp[1] * 512
    return (f, d) if facing in ('n', 's') else (d, f)

def rect(facing, fp, u0, v0, du, dv):
    W, H = plot_extent(facing, fp)
    if facing == 's':
        return [u0, H - v0 - dv], [du, dv]
    if facing == 'n':
        return [u0, v0], [du, dv]
    if facing == 'e':
        return [W - v0 - dv, u0], [dv, du]
    return [v0, u0], [dv, du]

def centre(facing, fp, uc, vc):
    W, H = plot_extent(facing, fp)
    return {'s': [uc, H - vc], 'n': [uc, vc], 'e': [W - vc, uc], 'w': [vc, uc]}[facing]

def box(pid, facing, fp, u0, v0, du, dv, **kw):
    at, size = rect(facing, fp, u0, v0, du, dv)
    p = {'id': pid, 'at': [round(a) for a in at], 'size': [round(s) for s in size]}
    p.update(kw)
    return p

THATCH = 'hhp2rf'
ROOFS = {'plaster': 'hhm2rf', 'timber': 'hhm1rf', 'grey': 'hhm3rf', 'poor': 'hhp2rf', 'rich': '7hhr1rf',
         'stone': '7hhr1rf'}

def shape(kind, facing, fp, kit, sign=None, roof_tex=None):
    """The parts (and the door) of one house of `kind` on a plot of `fp` cells facing `facing`."""
    F, D = fp[0] * 512, fp[1] * 512
    tex = {'roof': roof_tex} if roof_tex else None
    parts = []
    door = {'part': 'body', 'wall': facing}
    def signs(wall_len):
        if not sign:
            return {}
        return {'signs': [{'wall': facing, 'bay': 0, 'texture': sign, 'hang': True, 'size': sign_size(sign), 'out': 48,
                           'bottom': 120}]}
    if kind == 'cottage':
        # a small house with a hip roof (Harmondale's 1x1 cottages, Ravenshore's stone huts)
        b = box('body', facing, fp, 64, 64, F - 128, D - 128, roof='hip', roof_pitch=38)
        b.update(signs(F - 128))   # A4 2026-11-22: a cottage hangs its sign too (it was dropped)
        if tex: b['textures'] = dict(tex)
        parts.append(b)
    elif kind == 'gable_porch':
        # gable end to the street, a porch on posts over the door
        b = box('body', facing, fp, 64, 160, F - 128, D - 224, roof='gable', ridge_along=ACROSS[facing],
                roof_pitch=48, porches=[{'wall': facing, 'depth': 128, 'posts': 24, 'height': 224, 'floor': 16}])
        b.update(signs(F - 128))
        if tex: b['textures'] = dict(tex)
        parts.append(b)
    elif kind == 'L':
        # a front range along the street and a wing back from one end
        a = box('body', facing, fp, 48, 48, F - 96, int(D * 0.5), roof='gable', ridge_along=ALONG[facing],
                roof_pitch=45)
        a.update(signs(F - 96))
        w = box('wing', facing, fp, int(F * 0.5), int(D * 0.5) - 32, int(F * 0.5) - 112, int(D * 0.5) - 32,
                roof='gable', ridge_along=ACROSS[facing], roof_pitch=45)
        if tex:
            a['textures'] = dict(tex); w['textures'] = dict(tex)
        parts += [a, w]
    elif kind == 'jetty':
        # a shop of two storeys, the upper one reaching out over the lower
        a = box('body', facing, fp, 96, 112, F - 192, D - 192, roof='none')
        a.update(signs(F - 192))
        u = box('upper', facing, fp, 48, 64, F - 96, D - 112, bottom=256, wall_height=256, roof='gable',
                ridge_along=ALONG[facing], roof_pitch=50)
        if tex:
            a['textures'] = dict(tex); u['textures'] = dict(tex)
        parts += [a, u]
    elif kind == 'tower_house':
        # a round tower with a cone roof behind a small gabled entry
        r = int(min(F, D) * 0.34)
        c = centre(facing, fp, F / 2, D - r - 48)
        t = {'id': 'tower', 'shape': 'round', 'at': [round(c[0]), round(c[1])], 'radius': r, 'sides': 10,
             'wall_height': 512, 'roof': 'cone', 'roof_pitch': 62, 'windows': 'alternate'}
        b = box('body', facing, fp, int(F * 0.22), 48, int(F * 0.56), int(D * 0.42), roof='gable',
                ridge_along=ACROSS[facing], roof_pitch=48)
        b.update(signs(int(F * 0.56)))
        if tex:
            t['textures'] = dict(tex); b['textures'] = dict(tex)
        parts += [t, b]
    elif kind == 'barn':
        # a long low barn with a lean-to along one side
        b = box('body', facing, fp, 48, 48, F - 96, int(D * 0.62), roof='gable', ridge_along=ALONG[facing],
                roof_pitch=40)
        b.update(signs(F - 96))
        l = box('shed', facing, fp, 96, int(D * 0.62) + 48 - 16, F - 256, int(D * 0.38) - 64, roof='lean_to',
                wall_height=192, windows='none')
        if tex:
            b['textures'] = dict(tex); l['textures'] = dict(tex)
        parts += [b, l]
    elif kind == 'forge':
        # stone smithy: a gabled shop, a chimney through its roof, an open lean-to shed on posts at the side
        b = box('body', facing, fp, 48, 96, int(F * 0.7), D - 160, roof='gable', ridge_along=ACROSS[facing],
                roof_pitch=45)
        b.update(signs(int(F * 0.7)))
        ch = box('chimney', facing, fp, int(F * 0.7) - 64, D - 240, 96, 96, wall_height=512, roof='flat',
                 windows='none')
        sh = box('shed', facing, fp, int(F * 0.7) + 48, 128, F - int(F * 0.7) - 96, D - 256, roof='lean_to',
                 wall_height=256, posts=24, windows='none')
        parts += [b, ch, sh]
    elif kind == 'round_hut':
        if sign:
            raise ValueError('a round hut has no flat wall for its sign %s: give the house another shape' % sign)
        r = int(min(F, D) * 0.42)
        parts.append({'id': 'body', 'shape': 'round', 'at': [F // 2, D // 2], 'radius': r, 'sides': 10,
                      'wall_height': 256, 'roof': 'cone', 'tiers': [[48, 128], [80, 96], [96, 64]],
                      'textures': {'roof': roof_tex or THATCH}})
        door = {'part': 'body'}
    else:
        raise ValueError(kind)
    return parts, door

TURN_OF = {'s': 0, 'w': 90, 'n': 180, 'e': 270}

# ---------------------------------------------------------------------------------------------------------------
# The town's plots. (plan id, title, house, at [x, y] (NW corner), facing, [front, depth], kit, shape, turn, extra)
# extra: sign (texture), roof (texture), index, storeys ...
# ---------------------------------------------------------------------------------------------------------------
CORE = [
    # Pass three (town feel, measured): every house squared to the compass axes; the irregularity is in the plots
    # (sizes, setbacks, gaps). The north row of shops backs onto the upper town's terrace (`against: slope`).
    # north side of the main street: shops in front, homes round two lanes behind
    # Pass four: the shops stand on the street's level (floor 640) in front of the terrace's retaining wall
    # (REVIEW_PASS3 1), 1.5 cells deep, not dug into a slope.
    ('building:weapon_shop', "Norman's Ironworks", 9, 42.5, 42, 's', [1.5, 1.5], 'grey', 'forge', 0,
     {'sign': 'sgweapon', 'floor': 640}),
    ('building:armour_shop', 'Vertigo Armoury', 47, 45.0, 42, 's', [1, 1.5], 'timber', 'jetty', 0,
     {'sign': '7sgarm', 'floor': 640}),
    # the town hall stands up on the terrace, a flight of steps down to the main street (gen.py)
    ('building:town_hall', 'Vertigo Town Hall', 203, 47.5, 39, 's', [2.5, 2], 'rich', 'town_hall', 0, {}),
    ('building:magic_shop', "Gilbert's Hexes", 85, 52.5, 42, 's', [1.5, 1.5], 'plaster', 'tower_house', 0,
     {'sign': 'sgmagi', 'floor': 640}),
    # the tavern looks onto the square where the party arrives (TOWN_FEEL 4: the first house from the arrival)
    ('building:tavern', "Lady Geraldine's Tavern", 240, 54.5, 42, 's', [1.5, 1.5], 'plaster', 'gable_porch', 0,
     {'sign': '7sgtvrn', 'storeys': 2, 'floor': 640}),
    ('building:bank', 'Bank of Vertigo', 286, 57.0, 42, 's', [1.5, 1.5], 'stone', 'cottage', 0,
     {'sign': '7sgbank', 'big': True, 'floor': 640}),
    # homes behind (doors onto the lanes, up on the terrace)
    ('building:core_houses', None, None, 42.5, 39, 'e', [1, 1], 'plaster', 'cottage', 0, {'index': 3, 'roof': THATCH}),
    ('building:core_houses', None, None, 45.5, 39, 'w', [1, 1], 'poor', 'round_hut', 0, {'index': 4}),
    ('building:core_houses', None, None, 55, 39, 'e', [1, 1], 'plaster', 'gable_porch', 0, {'index': 5}),
    ('building:core_houses', None, None, 57.5, 39, 'w', [1, 1.5], 'plaster', 'L', 0, {'index': 6}),
    ('building:core_houses', None, None, 60, 42.5, 's', [1, 1], 'grey', 'cottage', 0, {'index': 2, 'floor': 640}),
    # south side of the main street
    # the inn by the west gate, for travellers off the west road; the alchemist a street from the magic shop
    # the Adventurer's Inn hangs MM6-MM8's key and heart, never the tavern's mug (A4 2026-11-22, house_signs.py)
    ('building:inn', "The Adventurer's Inn", 1607, 42.5, 45, 'n', [2.5, 2], 'timber', 'L', 0,
     {'sign': 'sginn', 'storeys': 2}),
    ('building:alchemist', 'Philters of Vertigo', 117, 47.0, 44.5, 'n', [2, 2], 'plaster', 'jetty', 0,
     {'sign': '7sgalch'}),
    ('building:core_houses', None, None, 49.5, 44, 'n', [1, 1], 'poor', 'round_hut', 0, {'index': 1}),
    ('building:temple', 'Temple of Vertigo', 311, 57.5, 46.5, 'n', [2.5, 2.5], 'stone', 'temple', 0,
     {'sign': 'sgtempl'}),
    ('building:core_houses', None, None, 60.5, 46.5, 'n', [1, 1], 'plaster', 'cottage', 0,
     {'index': 7, 'roof': THATCH}),
    ('building:core_houses', None, None, 44, 47.5, 'e', [1, 1], 'plaster', 'gable_porch', 0, {'index': 8}),
    ('building:core_houses', None, None, 46.5, 47.5, 'w', [1, 1.5], 'timber', 'L', 0, {'index': 9}),
]
SOUTH = [
    ('building:guild_fire', 'Fire Guild of Vertigo', 129, 42.5, 56, 'n', [2, 2], 'stone', 'tower_house', 0,
     {'sign': 'sgfire'}),
    ('building:guild_air', 'Air Guild of Vertigo', 135, 45.5, 56, 'n', [2, 2], 'plaster', 'L', 0,
     {'sign': 'sgair'}),
    ('building:guild_water', 'Water Guild of Vertigo', 140, 53, 56, 'n', [2, 2], 'grey', 'jetty', 0,
     {'sign': 'sgwater'}),
    ('building:guild_earth', 'Earth Guild of Vertigo', 146, 55.5, 56, 'n', [2, 2], 'plaster', 'gable_porch', 0,
     {'sign': 'sgearth'}),
    ('building:joes_shop', "Joe the Exterminator", None, 60, 55.5, 'w', [1.5, 1.5], 'poor', 'barn', 0, {}),
    ('building:bank_houses', None, None, 48, 56, 'n', [1, 1], 'poor', 'round_hut', 0, {'index': 1}),
    ('building:bank_houses', None, None, 49, 58, 'e', [1, 1], 'plaster', 'cottage', 0,
     {'index': 2, 'roof': THATCH}),
    ('building:bank_houses', None, None, 55, 58.5, 'w', [1, 1], 'plaster', 'gable_porch', 0, {'index': 3}),
]
SUBURB_W = [
    ('building:training', "Thylon's Training", 1571, 39, 40.5, 's', [2, 2], 'timber', 'barn', 0,
     {'sign': '7sgtrain'}),
    ('building:west_houses', None, None, 35, 43, 's', [1, 1], 'plaster', 'cottage', 0,
     {'index': 1, 'roof': THATCH}),
    ('building:west_houses', None, None, 35.5, 47, 'n', [1, 1], 'poor', 'round_hut', 0, {'index': 2}),
    ('building:west_houses', None, None, 36, 41, 's', [1.5, 1], 'timber', 'barn', 0, {'index': 3}),
]
SUBURB_E = [
    ('building:stables', 'Vertigo Stables', 461, 64, 46.5, 'n', [3, 2], 'timber', 'barn', 0,
     {'sign': '7sgstabl'}),
    ('building:east_houses', None, None, 64, 41, 's', [1, 1], 'plaster', 'gable_porch', 0, {'index': 1}),
    ('building:east_houses', None, None, 66.5, 41, 's', [1, 1.5], 'plaster', 'L', 0, {'index': 2}),
    ('building:east_houses', None, None, 68.5, 45, 'n', [1, 1], 'poor', 'round_hut', 0, {'index': 3}),
]

# Town density pass: homes enlarged where the ground round them is free (1 x 1 to 1.5 x 1.5) and fourteen plain homes
# (no door event) on the fringe, placed by a clearance search against the built map (0.7 cell from every model, 1.1-3
# from a road, 3 from the creek). Kinds and kits rotate so pass two's variety holds.
ENLARGE = {('building:core_houses', 2): ([1.5, 1.5], 59.0, 42), ('building:bank_houses', 2): ([1.5, 1.5], 48.5, 58),
           ('building:east_houses', 1): ([1.5, 1.5], 64, 41), ('building:east_houses', 2): ([1.5, 1.5], 66.5, 41)}
for _lst in (CORE, SOUTH, SUBURB_W, SUBURB_E):
    for _i, _e in enumerate(_lst):
        _k = (_e[0], _e[10].get('index'))
        if _k in ENLARGE:
            _fp, _x, _y = ENLARGE[_k]
            _lst[_i] = _e[:3] + (_x, _y) + (_e[5], _fp) + _e[7:]
_FRINGE_AT = [(33, 43, 1, 1, 's'), (70.5, 47, 1.5, 1.5, 'n'), (68.5, 41, 1.5, 1.5, 's'), (71, 41, 1, 1.5, 's'),
              (54, 35, 1.5, 1.5, 'n'), (60, 34, 1.5, 1.5, 'n'),
              (49, 33.5, 1.5, 1.5, 'e'), (56.5, 34.5, 1.5, 1.5, 'n'),
              (55.5, 62, 1.5, 1.5, 'w'), (57.5, 64, 1.5, 1.5, 's'), (56.5, 60, 1.5, 1, 'w')]
_KINDS = [('cottage', 'plaster', THATCH), ('gable_porch', 'timber', None), ('L', 'grey', None), ('barn', 'poor', None),
          ('jetty', 'plaster', None), ('cottage', 'stone', None), ('gable_porch', 'poor', THATCH)]
# pass three: at most one house in five turned (TOWN_FEEL 2): four plain fringe homes keep a turn
_TURNS = [0, 0, 0, 0, 8, -13, 0, 0, 6, 0, -9]
FRINGE = []
for _i, (_x, _y, _w, _h, _f) in enumerate(_FRINGE_AT):
    _kind, _kit, _roof = _KINDS[_i % len(_KINDS)]
    if _kind == 'L' and (_w, _h) == (1, 1):
        _kind = 'cottage'
    _fp = [_w, _h] if _f in ('n', 's') else [_h, _w]
    _ex = {'index': _i + 1, 'plain': True}
    if _roof:
        _ex['roof'] = _roof
    FRINGE.append(('building:fringe_houses', None, None, _x, _y, _f, _fp, _kit, _kind, _TURNS[_i], _ex))
# Pass six (the user: "the town too stretched out beyond the walls"; town_feel's town spread): the four plain homes
# farthest out (beyond the stables at x 68.5-71 and west of the training hall at 33) dropped; the training hall 2 x 2
# at x 39 by the west gate (was 2.5 x 2 at 36), west_houses#3 in the hall's old place (was 32, 47), east_houses#3
# just south of the orchard road east of the stables (was 68.5, 46.5). Kinds and turns of the others unchanged.
FRINGE = [e for e in FRINGE if e[10]['index'] not in (1, 2, 3, 4)]

def fringe_space(e):
    x, y = e[3], e[4]
    for space, (x0, y0, x1, y1) in (('district:vertigo_outer', (31, 38, 41, 50)), ('district:vertigo_east', (63, 38, 71, 50)),
                                    ('district:vertigo_south', (42, 53, 63, 62))):
        if x0 <= x and x + 1.5 <= x1 and y0 <= y and y + 1.5 <= y1:
            return space
    return 'zone:meadows'

# ---------------------------------------------------------------------------------------------------------------
# Streets: straight runs and 45-degree steps only (the classic road tiles join at no other slope: the rips the
# user found on the north road were 2:7 slopes).
# ---------------------------------------------------------------------------------------------------------------
GATE_W, GATE_N, GATE_E, GATE_S = (41.5, 44), (52, 38), (62.5, 46), (52, 49.5)
# Pass three (TOWN_FEEL 3: straight runs of 2-6 cells, offset junctions, right-angle turns and 45-degree jogs): the
# main street is broken by the lanes, which are cobbled now and meet it at offset junctions (the smiths' lane at x
# 44.5 north, the inn lane at 45.5 south; the bank lane at 57); the west road leaves the gate in a right-angle dog-leg,
# the orchard road in two 45-degree jogs round the east houses.
MAIN = [[41.5, 44], [46.5, 44], [47.5, 43], [51, 43], [52, 44], [57, 44], [57, 46], [62.5, 46]]
NORTH_ST = [[51, 43], [51, 40], [52, 39], [52, 38]]
SOUTH_ST = [[52, 44], [52, 49.5]]
GUILD_LANE = [[42, 55], [59, 55]]
WEST_ROAD = [[41.5, 44], [38.5, 44], [38.5, 46], [0, 46]]   # to the map edge, as shipped roads to neighbours
NORTH_ROAD = [[52, 38], [52, 35], [54, 33], [59, 33], [60, 32], [65, 27], [67, 25], [69, 23], [69, 0]]   # to the map edge
ORCHARD_ROAD = [[62.5, 46], [63.5, 46], [66, 43.5], [73, 43.5], [73, 45.5], [81, 45.5]]
SOUTH_ROAD = [[52, 55], [52, 58], [54, 60], [54, 64], [57, 67], [57, 70], [60, 73], [62, 73]]
TOAD_LANE = [[62, 73], [63.5, 74.5], [80, 74.5]]
SMITH_LANE = [[44.5, 44], [44.5, 43]]         # behind the ironworks and the armoury, to the steps up
BANK_LANE = [[56.5, 44], [56.5, 43]]          # between the tavern and the bank, to the steps up
INN_LANE = [[45.5, 44], [45.5, 48.5]]         # between the alchemist and the inn, to the homes by the south wall

# Dirt lanes (laid as ground strips): on the upper terrace, from the lanes' steps to the back houses (a cobbled
# road's bed would cut the terrace and the shops' backs)
LANES = [[[44.5, 41], [44.5, 39.5]], [[56.5, 41], [56.5, 39.5]]]

# The upper town: a terrace behind the north row of shops (TOWN_FEEL 8: 500-1000 of relief; Harmondale's houses on
# levels). The shops back onto its slope; the lanes and the north street climb it on ramps.
UPPER = [[42.5, 39], [61.5, 39], [61.5, 41], [42.5, 41]]
UPPER_H = 1152      # pass four: 512 over the street, held by a retaining wall (was 1280 on a two-cell slope)
UPPER_SLOPE = 0     # a step at the outline (row 41 to 42), hidden by the retaining wall

# ---------------------------------------------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------------------------------------------
def rot(px, py, cx, cy, deg):
    a = math.radians(deg)            # clockwise seen from above; y runs south, so this is the usual rotation
    dx, dy = px - cx, py - cy
    return (cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))

def footprint(x, y, facing, fp, turn):
    W, H = plot_extent(facing, fp)
    w, h = W / 512.0, H / 512.0
    cx, cy = x + w / 2, y + h / 2
    return [rot(px, py, cx, cy, turn) for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]

def door_cell(x, y, facing, fp, turn, out=0.0):
    W, H = plot_extent(facing, fp)
    w, h = W / 512.0, H / 512.0
    px, py = {'s': (x + w / 2, y + h + out), 'n': (x + w / 2, y - out), 'e': (x + w + out, y + h / 2),
              'w': (x - out, y + h / 2)}[facing]
    return rot(px, py, x + w / 2, y + h / 2, turn)

def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)

def inside(p, poly):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c

def line_hits_poly(line, poly, clearance):
    """Does a polyline come within `clearance` cells of a polygon (or run through it)? Pass three: plots stand on half
    cells, so a building may stand against an axis-aligned road's cell (0.5 from its line); diagonals keep `clearance`."""
    base = clearance
    for a, b in zip(line, line[1:]):
        clearance = min(base, 0.5) if (a[0] == b[0] or a[1] == b[1]) else base
        for i in range(len(poly)):
            p, q = poly[i], poly[(i + 1) % len(poly)]
            if min(seg_dist(p, a, b), seg_dist(q, a, b), seg_dist(a, p, q), seg_dist(b, p, q)) < clearance:
                return True
        steps = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) * 4))
        for k in range(steps + 1):
            t = k / float(steps)
            if inside((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), poly):
                return True
    return False

def nearest_on(lines, p):
    best = None
    for line in lines:
        for a, b in zip(line, line[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = dx * dx + dy * dy
            t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
            q = (a[0] + t * dx, a[1] + t * dy)
            d = math.hypot(p[0] - q[0], p[1] - q[1])
            if best is None or d < best[0]:
                best = (d, q)
    return best

# ---------------------------------------------------------------------------------------------------------------
# The town wall: runs between towers, gatehouses at the gates
# ---------------------------------------------------------------------------------------------------------------
WALL_T = 256          # the wall's thickness
WALL_H = 512          # to the walk (pass four: 576 to 512, the ring dominated every view); merlons 96 above it
FOOT = 64             # the batter's reach on each side
TOWER_R = 352
GATE_GAP = 640        # the passage between a gatehouse's towers
GATE_TR = 288
FOLLOW_RUNS = (5, 12)   # tower NE to the east gate, the west gate to tower NW
# Pass four (REVIEW_PASS3 5): dressed grey stone instead of one dark rock texture everywhere, the towers in a second,
# coursed stone (Ironfist: lighter dressed stone, towers apart); a visible batter; arched gate openings (the gate
# wall's `gates` with `arch`); the creek side left open (the ring closed all round dominated every outside view: no
# shipped start town is so enclosed), its two corner towers standing as the wall's ends.
RUN_TEX = 'cwb'
TOWER_TEX = 'cnb'
OPEN_SEGMENTS = (6, 7, 8, 9)   # ring segments RING[i] to RING[i + 1] left out: the south side along the creek
CREEK_IN = 51.75      # F19: where the creek walls end, 0.75 into the water below the end towers
CREEK_BANK = 51.0     # D-94: the creek's water starts at row 51 below the end towers

# the ring, clockwise from the north-west corner: ('t', point) tower, ('g', point) gatehouse
RING = [('t', (42.0, 38.5)), ('t', (47.0, 38.2)), ('g', GATE_N), ('t', (57.0, 38.2)), ('t', (62.2, 38.6)),
        ('g', GATE_E), ('t', (62.0, 49.5)), ('t', (57.0, 49.6)), ('g', GATE_S), ('t', (47.0, 49.6)),
        ('t', (42.0, 49.5)), ('g', GATE_W)]

def wall_structures():
    out = []
    n = len(RING)
    # where each run ends at a node: a tower's middle, or a gatehouse tower's middle on that side
    def ends(i):
        kind, p = RING[i]
        if kind == 't':
            return p, p
        a, b = RING[i - 1][1], RING[(i + 1) % n][1]
        ux, uy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        off = (GATE_GAP / 2 + GATE_TR) / 512.0
        return (p[0] - ux * off, p[1] - uy * off), (p[0] + ux * off, p[1] + uy * off)
    used = set()
    for i in range(n):
        if (i - 1) % n not in OPEN_SEGMENTS or i not in OPEN_SEGMENTS:
            used.add(i)
    run = 0
    for i in range(n):
        run += 1
        if i in OPEN_SEGMENTS:
            continue
        a = ends(i)[1]
        b = ends((i + 1) % n)[0]
        wall = {'id': 'thing:wall_run_%d' % run, 'kind': 'wall',
                'line': [[round(a[0], 3), round(a[1], 3)], [round(b[0], 3), round(b[1], 3)]],
                'height': WALL_H, 'thickness': WALL_T + 2 * FOOT, 'batter': 128, 'batter_height': 320,
                'textures': {'wall': RUN_TEX}, 'title': 'Town wall'}
        if run in FOLLOW_RUNS:
            wall['top'] = 'follow'
            wall['notes'] = 'Climbs from the street to the upper town: its top follows the land.'
        else:
            wall['parapet'] = 96
            wall['battlements'] = True
        out.append(wall)
    t = 0
    for i, (kind, p) in enumerate(RING):
        if i not in used:
            if kind == 't':
                t += 1
            continue
        if kind == 't':
            t += 1
            size = (2 * TOWER_R + 64) / 512.0
            corner = t in (1, 4, 5, 8)  # the four corners
            part = {'id': 'tower', 'shape': 'round', 'at': [round(size * 256), round(size * 256)],
                    'radius': TOWER_R, 'sides': 12, 'wall_height': WALL_H + 320, 'windows': 'none',
                    'textures': {'wall': TOWER_TEX}}
            if corner:
                part.update({'roof': 'cone', 'roof_pitch': 58, 'eaves': 32,
                             'textures': {'wall': TOWER_TEX, 'roof': '7hhr1rf'}})
            else:
                part.update({'roof': 'flat', 'parapet': 96, 'battlements': True})
            out.append({'id': 'thing:wall_tower_%d' % t, 'kind': 'building',
                        'at': [round(p[0] - size / 2, 3), round(p[1] - size / 2, 3)], 'size': [round(size, 3)] * 2,
                        'kit': 'castle', 'door': 'none', 'title': 'Wall tower', 'parts': [part]})
        else:
            a, b = RING[i - 1][1], RING[(i + 1) % len(RING)][1]
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            W = GATE_GAP + 4 * GATE_TR
            Dp = 2 * GATE_TR + 128
            upright = 45 < abs(ang) < 135
            name = {GATE_N: 'north', GATE_E: 'east', GATE_S: 'south', GATE_W: 'west'}[p]
            towers = []
            tw = {'shape': 'round', 'radius': GATE_TR, 'sides': 12, 'wall_height': WALL_H + 384, 'roof': 'cone',
                  'roof_pitch': 58, 'eaves': 32, 'windows': 'none', 'textures': {'wall': TOWER_TEX, 'roof': '7hhr1rf'}}
            if upright:
                ang = ang - 90 if ang > 0 else ang + 90
                w, h = Dp / 512.0, W / 512.0
                for side, cy in (('l', GATE_TR), ('r', W - GATE_TR)):
                    towers.append(dict(tw, id='tower_' + side, at=[Dp // 2, cy]))
            else:
                w, h = W / 512.0, Dp / 512.0
                for side, cx in (('l', GATE_TR), ('r', W - GATE_TR)):
                    towers.append(dict(tw, id='tower_' + side, at=[cx, Dp // 2]))
            out.append({'id': 'thing:gatehouse_' + name, 'kind': 'building',
                        'at': [round(p[0] - w / 2, 3), round(p[1] - h / 2, 3)], 'size': [round(w, 3), round(h, 3)],
                        'turn': round(ang, 1), 'kit': 'castle', 'door': 'none', 'title': 'Vertigo %s gate' % name.title(),
                        'parts': towers,
                        'notes': 'Two round towers under cone roofs; the wall between them carries the arched gate.'})
            ea, eb = ends(i)
            # a gate keeps the wall's thickness clear of both ends: the gate wall runs on 0.2 cell into each tower
            dx, dy = eb[0] - ea[0], eb[1] - ea[1]
            L = math.hypot(dx, dy)
            ea = (ea[0] - dx / L * 0.2, ea[1] - dy / L * 0.2)
            eb = (eb[0] + dx / L * 0.2, eb[1] + dy / L * 0.2)
            out.append({'id': 'thing:gate_arch_' + name, 'kind': 'wall',
                        'line': [[round(ea[0], 3), round(ea[1], 3)], [round(eb[0], 3), round(eb[1], 3)]],
                        # 16 over the runs' parapet: the run's last 0.2 cell inside the arch flickered (audit, MP5)
                        'height': WALL_H + 112, 'thickness': 448, 'parapet': 96, 'battlements': True,
                        'gates': [{'at': [p[0], p[1]], 'width': 448, 'height': 416, 'arch': 'round', 'sides': 8}],
                        'textures': {'wall': TOWER_TEX}, 'title': 'Vertigo %s gate' % name.title(),
                        'notes': 'Pass four: the gate passage under a round arch (was a level passage 448 over the road).'})
    # F19 (the user 2026-11-22: "move to the water so that person cant just walk around it from the river"): the open
    # creek side's two end towers each close down to Pitchfork Creek, past the walkable bank into water the party
    # cannot enter, so the creek closes the ring between them and the bridge is the way in (wall_check.py).
    # D-94 (the user: "a little too much ... some 'end water piece'"): not a crenellated curtain run into the creek but
    # the kit's water end, a low battered pier from the tower's foot that slopes down into the water to a round nose.
    for k, i in enumerate((OPEN_SEGMENTS[0], OPEN_SEGMENTS[-1] + 1)):
        p = RING[i][1]
        out.append(KIT.water_end('thing:water_end_%d' % (k + 1), (p[0], p[1] + 0.4), (p[0], CREEK_IN),
                                 bank=CREEK_BANK, ground=576, texture=RUN_TEX, title='Pier',
                                 notes='D-94: the ring ends in the creek in a low pier from its end tower (the water '
                                       'starts at row 51).'))
    return out

# Pass four (REVIEW_PASS3 1): the terrace's front is a stone retaining wall over the one-cell step (row 41 to 42),
# its face 512 high behind the north row of shops, broken by the flights of steps and the north street's ramp.
RETAIN_Y = 41.5
RETAIN_GAPS = [(44.1, 44.9), (48.35, 49.15), (50.3, 51.7), (56.1, 56.9)]
RETAIN_TEX = 'chb1'

def retaining_walls():
    out = []
    xs = [UPPER[0][0]] + [v for g in RETAIN_GAPS for v in g] + [UPPER[1][0]]
    for k in range(0, len(xs), 2):
        out.append({'id': 'thing:terrace_wall_%d' % (k // 2 + 1), 'kind': 'wall',
                    'line': [[xs[k], RETAIN_Y], [xs[k + 1], RETAIN_Y]], 'height': 48, 'thickness': 512,
                    'textures': {'wall': RETAIN_TEX}, 'title': 'Terrace wall',
                    'notes': "Pass four: the upper town's retaining wall (Harmondale's fieldstone, chb1)."})
    return out

def gate_cut(p):
    return p

# ---------------------------------------------------------------------------------------------------------------
# Small structures: wells, stalls, sheds, fences, a cart
# ---------------------------------------------------------------------------------------------------------------
def well(wid, at, roofed=False, title='Well'):
    w = {'id': wid, 'kind': 'well', 'at': list(at), 'title': title, 'frame': {'height': 200}}
    if roofed:
        w['frame'] = {'height': 224, 'roof': 'gable', 'roof_height': 64}
    w['effects'] = [{'text': 'Cool water.'}]
    return w

def stall(sid, at, turn, kit='timber', roof_tex=None):
    s = {'id': sid, 'kind': 'building', 'at': list(at), 'size': [1, 0.75], 'turn': turn, 'kit': kit, 'door': 'none',
         'title': 'Market stall',
         'parts': [{'id': 'stall', 'at': [64, 64], 'size': [384, 256], 'wall_height': 224, 'posts': 24, 'sill': 80,
                    'sill_walls': ['n', 'e', 'w'], 'roof': 'hip', 'roof_pitch': 30, 'windows': 'none'}]}
    # pass four (REVIEW_PASS3 4): a low hip roof on the posts; the lean-to's high back wall read as a broken building
    if roof_tex:
        s['parts'][0]['textures'] = {'roof': roof_tex}
    return s

def shed(sid, at, size_cells, turn, kit='poor', open_=False, roof='lean_to', title='Shed'):
    W, H = size_cells[0] * 512, size_cells[1] * 512
    p = {'id': 'shed', 'at': [48, 48], 'size': [W - 96, H - 96], 'wall_height': 256, 'roof': roof,
         'windows': 'none'}
    if open_:
        p['posts'] = 24
    return {'id': sid, 'kind': 'building', 'at': list(at), 'size': list(size_cells), 'turn': turn, 'kit': kit,
            'door': 'none', 'title': title, 'parts': [p]}

def fence(fid, line, closed=False):
    f = {'id': fid, 'kind': 'fence', 'line': [list(p) for p in line],
         'notes': 'A fence round a garden or pen (pass three: the fence word, posts and rails following the ground).'}
    if closed:
        f['closed'] = True
    return f
