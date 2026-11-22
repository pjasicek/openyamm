#!/usr/bin/env python3
"""DD-13 Ogre Forts: writes the L1-L4 project folders of devdocs/xeen/briefs/dd13 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/dd13/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-dd13 after XD-23's gen.py (level_generation/projects/xeen/xd23/gen.py).

Frame: x east, y north, z up. Two forts on floor 0: the west fort (north of D2's pass road, its gate on its south side,
x about 0) and the east fort (south of the road, its gate on its north side, x about 7,600). Their cellars and the
ogres' run under the road at floor -512. Rooms of one floor stand 128 apart (the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/dd13'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One family: XD-05's MM8 Ogre Fortress (d12): plank-and-post timber (gkp1ceil) for the blockhouses' walls and roofs,
# beaten dark earth (gcav2flr) for their floors, straw (gkp1flr) in the bunks, the kennel and Graalg's quarters, the
# log palisade (xopalis) in the gateways, cave rock (gcav1flr) in the cellars and the run, timber beams (t66abc11a) and
# pole ladders (t66abc10a), MM8's plank door leaves gkp103a/gkp103b (a mirrored pair: the two wings of the gates),
# hides (xohide), bars (xopoles), and XD-05's burning and burnt-out timber (xoburn, xochar).
PLANK = S('gkp1ceil', 256, 256)
EARTH = S('gcav2flr', 128, 128)
STRAW = S('gkp1flr', 128, 128)
PALIS = S('xopalis', 128, 256)
ROCK = S('gcav1flr', 256, 256)
ROCKFLR = S('gcav2flr', 128, 128)
STONE = S('gkp1-bs1', 128, 256)
HIDE = S('xohide', 128, 256, fit=True)
CHAR = S('xochar', 128, 128)
BURN = S('xoburn', 128, 128)
BONES = S('xobones', 128, 256)
POLES = S('t66abc10a', 32, 128, uneven=True)
BEAM = S('t66abc11a', 128, 32)
BARS = S('xopoles', 128, 128)
DAYLIGHT = S('xddaylt', 256, 128, fit=True)   # D-34 (3): D2's pass under the Darkside's dim sky
LEAF_L = S('gkp103a', 128, 256)
LEAF_R = S('gkp103b', 128, 256)
# The narrow single doors: MM6's small plank door (one leaf's picture), not one wing of the gates' pair (A1's door
# check, devdocs/xeen/formats/DOORS.md: doors.half_wing).
PLANK_DOOR = S('d2smldor', 128, 256)

themes = [
    {'id': 'theme:timber', 'wall': PLANK, 'floor': EARTH, 'ceiling': PLANK, 'door': LEAF_L, 'reveal': PLANK,
     'notes': "The blockhouses: plank walls on posts (MM8's gkp1ceil), beaten earth floors, plank roofs."},
    {'id': 'theme:straw', 'wall': PLANK, 'floor': STRAW, 'ceiling': PLANK, 'door': LEAF_L, 'reveal': PLANK,
     'notes': "Bunks, kennel, Graalg's quarters: the same timber, the floor deep in straw (gkp1flr)."},
    {'id': 'theme:palisade', 'wall': PALIS, 'floor': EARTH, 'ceiling': PLANK, 'door': LEAF_L, 'reveal': PALIS,
     'notes': "The gateways through the palisade: lashed logs (xopalis)."},
    {'id': 'theme:cave', 'wall': ROCK, 'floor': ROCKFLR, 'ceiling': ROCK, 'door': LEAF_L, 'reveal': ROCK,
     'notes': "The cellars dug into the knolls and the run: d12's cave rock."},
]
ROUGH = {'step': 224, 'depth': 64}


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octo(cx, cy, r, ry=None):
    ry = ry or r
    c, cy_ = int(r * 0.41), int(ry * 0.41)
    return [[cx - c, cy - ry], [cx + c, cy - ry], [cx + r, cy - cy_], [cx + r, cy + cy_], [cx + c, cy + ry],
            [cx - c, cy + ry], [cx - r, cy + cy_], [cx - r, cy - cy_]]


def blob(cx, cy, rx, ry):
    return [[cx - rx, cy - ry // 3], [cx - rx // 3, cy - ry], [cx + rx // 2, cy - ry], [cx + rx, cy - ry // 4],
            [cx + rx // 2, cy + ry], [cx - rx // 2, cy + ry]]


# ------------------------------------------------------------------------------------------------ the plan in numbers
# West fort (floor 0)
GWY_W = (-384, -576, 384, -320)
GATE_W = (-512, -192, 512, 512)
HALL_W = (-896, 640, 896, 2240)
BUNKS_W = (1024, 832, 2176, 1984)
PLUNDER_W = (-2176, 832, -1024, 1984)
# West cellar (floor -512)
CELLAR_W = (-1984, 1152, 1984, 1792)
# East fort (floor 0)
GWY_E = (7168, 320, 7936, 576)
GATE_E = (7040, -512, 8064, 192)
HALL_E = (6656, -2240, 8448, -640)
KENNEL_E = (5376, -2240, 6528, -1472)
GRAALG = (5376, -1344, 6528, -320)
# East cellar (floor -512): an L, west of the kennel's low end and under Graalg's quarters
CELLAR_E = [[4096, -2240], [5248, -2240], [5248, -1344], [5760, -1344], [5760, -896], [4096, -896]]
RUN = [[1536, 1024], [1536, 384], [1728, 0], [2176, -192], [3712, -192], [4096, -320], [4352, -576], [4352, -768]]
LOOT = (2560, 96, 3328, 832)

PIT_W = (0, 1856)
PIT_E = (7552, -1856)
LADDER_BUNKS = (1984, 1472)
LADDER_PLUNDER = (-1984, 1472)
LADDER_GRAALG = (5760, -1120)
HOLE = 192

rooms = []
openings = []


def room(id, name, **kw):
    d = {'id': id, 'name': name}
    d.update(kw)
    rooms.append(d)
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


def walls_of(key, r, surface=PLANK):
    """Every wall of a rectangular fort room as one full panel with an id, so the burn can set its texture."""
    x0, y0, x1, y1 = r
    out = []
    for side, length in (('south', x1 - x0), ('east', y1 - y0), ('north', x1 - x0), ('west', y1 - y0)):
        p = {'id': f'panel:{key}_{side}', 'offset': 0, 'length': length, 'surface': surface}
        out.append({'wall': side, 'panels': [p]})
    return out


def roof(key, r, low, peak, surface=PLANK):
    """A low pitched roof (one peak over the middle) whose whole ceiling is a region with an id (charred by event)."""
    x0, y0, x1, y1 = r
    return {'ceiling': low, 'ceiling_points': [[(x0 + x1) // 2, (y0 + y1) // 2, peak]],
            'ceiling_surfaces': [{'steeper_than': 0.001, 'id': f'region:{key}_roof', 'surface': surface}]}


# D-34 (2): the halls' roofs are gables whose ridge runs north-south over the fire pit (both pits stand on their hall's
# centre line), with a smoke hole at the ridge: a raised ring HOLE_OUT across (on the roof planes) up to a flat top
# HOLE_TOP across at HOLE_Z, whose faces are the sky (atmosphere.yml open_sky). While the fort stands a plank patch
# closes the hole just under its top (shown by evt:standing_*); the burn sets it alight, burn_out and the burned
# stage hide it, and the sky shows over two smoke-blackened tie beams.
HOLE_OUT, HOLE_TOP, HOLE_Z = 224, 176, 880
SKY = dict(PLANK, sky=True)


def hall_roof(key, r, pit, low=512, peak=768):
    """A gable roof with its ridge north-south through the pit's x, and the smoke hole ring round the pit."""
    x0, y0, x1, y1 = r
    cx, (px, py) = (x0 + x1) // 2, pit
    assert px == cx, 'the pit stands on the ridge'
    half = (x1 - x0) // 2
    at_ring = peak - (peak - low) * HOLE_OUT // half          # the roof's height on the ring's sides
    o, t = HOLE_OUT, HOLE_TOP
    outer = [[cx - o, py - o, at_ring], [cx, py - o, peak], [cx + o, py - o, at_ring],
             [cx + o, py + o, at_ring], [cx, py + o, peak], [cx - o, py + o, at_ring]]
    inner = [[cx - t, py - t, HOLE_Z], [cx + t, py - t, HOLE_Z], [cx + t, py + t, HOLE_Z], [cx - t, py + t, HOLE_Z]]
    points = [[cx, y0, peak], [cx, y1, peak]] + outer + inner
    lines = [[[cx, y0], [cx, py - o]], [[cx, py + o], [cx, y1]],
             [[p[0], p[1]] for p in outer] + [[outer[0][0], outer[0][1]]],
             [[p[0], p[1]] for p in inner] + [[inner[0][0], inner[0][1]]]]
    return {'ceiling': low, 'ceiling_points': points, 'ceiling_lines': lines,
            'ceiling_surfaces': [{'steeper_than': 0.001, 'id': f'region:{key}_roof', 'surface': PLANK},
                                 {'at': [px, py], 'id': f'region:{key}_sky', 'surface': SKY}]}


def hole_parts(k, pit, r):
    """The roof patch under the hole's top and the two tie beams across the hole (D-34 (2))."""
    px, py = pit
    t = HOLE_TOP
    patch = {'id': f'platform:roof_patch_{k}', 'outline': rect(px - t, py - t, px + t, py + t), 'base': HOLE_Z - 17,
             'rise': 16, 'surface': PLANK, 'top_surface': PLANK, 'bottom_surface': PLANK,
             'notes': "The plank patch over the smoke hole while the fort stands (shown by evt:standing; burns, then "
                      "gone: the sky over the tie beams)."}
    # Two tie beams across the hole just under its rim (D-34: seen against the sky), each reaching 96 past the ring
    # into the roof on both sides, its top where the roof plane is at its ends (the roof is higher over the rest).
    half = (r[2] - r[0]) // 2
    reach = HOLE_OUT + 96
    top = 768 - (768 - 512) * reach // half
    beams = [{'path': [[px - reach, y], [px + reach, y]], 'bottom': top - 32, 'width': 32, 'depth': 32,
              'surface': CHAR, 'notes': "A tie beam across the smoke hole under its rim, black with the fire's smoke."}
             for y in (py - 80, py + 80)]
    return patch, beams


def hide(id, side, offset, notes="A hide hung on the wall."):
    """A hide: a `cover` panel 128 x 256 hung 2 in front of the hall's wall (merge point 24: a cover may stand over the
    whole-wall panel the burn retextures, which is built whole behind it), xohide fitted once; a destructible `of` it
    burns it away to the wall."""
    return side, {'id': id, 'offset': offset, 'length': 128, 'bottom': 64, 'height': 256, 'surface': HIDE,
                  'cover': True, 'notes': notes}


def with_covers(walls, covers):
    """The rooms' whole-wall panels with the cover panels added to their walls."""
    for side, p in covers:
        next(w for w in walls if w['wall'] == side)['panels'].append(p)
    return walls


def heap(id, at, rx, ry, rise, notes):
    return {'id': id, 'outline': blob(at[0], at[1], rx, ry), 'rise': rise, 'surface': CHAR, 'top_surface': CHAR,
            'notes': notes}


def pit(id, at, r, notes):
    return {'id': id, 'outline': octo(at[0], at[1], r), 'rise': 24, 'surface': ROCK, 'top_surface': CHAR,
            'notes': notes}


# Hides hung on the halls' walls: cover panels (they burn away and leave the wall). Offsets from each wall's start
# corner (counter-clockwise: south from x0, east from y0, north from x1, west from y1); the same spots as the slabs.
HIDES_W = [hide('panel:hide_w1', 'north', 896 - -512), hide('panel:hide_w2', 'north', 896 - -256),
           hide('panel:hide_w3', 'north', 896 - 384), hide('panel:hide_w4', 'north', 896 - 640),
           hide('panel:hide_w5', 'west', 2240 - 1728), hide('panel:hide_w6', 'east', 1600 - 640)]
HIDES_E = [hide('panel:hide_e1', 'south', 6912 - 6656), hide('panel:hide_e2', 'south', 7168 - 6656),
           hide('panel:hide_e3', 'south', 7808 - 6656), hide('panel:hide_e4', 'south', 8064 - 6656),
           hide('panel:hide_e5', 'east', -2048 - -2240), hide('panel:hide_e6', 'east', -1600 - -2240)]
# The roof down round each fire pit after the burn: heaps of charred timber, hidden until then (a path stays open
# from the hall's door to the pit and between the side doors).
RUBBLE_W = [heap('platform:rubble_w1', [560, 1760], 180, 140, 64, "Fallen roof timbers, charred."),
            heap('platform:rubble_w2', [-560, 1640], 150, 160, 56, "Fallen roof timbers, charred."),
            heap('platform:rubble_w3', [150, 2090], 150, 70, 48, "Fallen roof timbers, charred."),
            heap('platform:rubble_w4', [-200, 2070], 90, 60, 40, "Charred rafters fallen through the smoke hole.")]
RUBBLE_E = [heap('platform:rubble_e1', [8050, -1950], 190, 140, 64, "Fallen roof timbers, charred."),
            heap('platform:rubble_e2', [7650, -2165], 160, 55, 48, "Fallen roof timbers, charred."),
            heap('platform:rubble_e3', [8050, -1500], 150, 120, 56, "Fallen roof timbers, charred."),
            heap('platform:rubble_e4', [7350, -2090], 90, 50, 40, "Charred rafters fallen through the smoke hole.")]
PATCH_W, BEAMS_W = hole_parts('w', PIT_W, HALL_W)
PATCH_E, BEAMS_E = hole_parts('e', PIT_E, HALL_E)

# The west hall's long table: a plank top on four legs set in from its corners (a block on three or more legs round
# its middle rests on them, merge point 21); each a destructible that burns with the hall.
TABLE_W = [{'id': 'platform:table_w', 'outline': rect(-720, 2016, -240, 2144), 'base': 56, 'rise': 12,
            'surface': PLANK, 'top_surface': PLANK, 'bottom_surface': PLANK, 'notes': "A long table of stolen plates."}]
TABLE_W += [{'id': f'platform:table_leg_{n}', 'outline': rect(x, y, x + 16, y + 16), 'rise': 56,
             'surface': S('t66abc10a', 32, 128), 'top_surface': PLANK, 'notes': "A leg of the long table."}
            for n, (x, y) in enumerate([(-680, 2040), (-296, 2040), (-680, 2104), (-296, 2104)], 1)]

# ------------------------------------------------------------------------------------------------ floor 0, west fort
room('room:gateway_w', 'West gateway', outline=rect(*GWY_W), floor=0, ceiling=448, theme='theme:palisade', ambient=22,
     walls=walls_of('gateway_w', GWY_W, PALIS),
     notes="The way through the west fort's palisade, 768 by 256: the log gate's two leaves north, the yard and the pass south (the exit to D2).")
room('room:gate_w', 'West fort gate', outline=rect(*GATE_W), floor=0, theme='theme:timber', ambient=18,
     walls=walls_of('gate_w', GATE_W), **roof('gate_w', GATE_W, 448, 512),
     notes="Inside the west fort's log gate, 1,024 by 704: the gate's two leaves behind (south), the blockhouse's double door ahead (north). The party's start (from D2's entrance:dd13_west).")
room('room:hall_w', 'West fort hall', outline=rect(*HALL_W), floor=0, theme='theme:timber', ambient=16,
     walls=with_covers(walls_of('hall_w', HALL_W), HIDES_W), **hall_roof('hall_w', HALL_W, PIT_W), beams=BEAMS_W,
     platforms=[pit('platform:pit_w', PIT_W, 176, "The west hall's fire pit under the smoke hole."), PATCH_W]
     + TABLE_W + RUBBLE_W,
     notes="The west blockhouse's hall, 1,792 by 1,600 under a pitched plank roof: a fire pit under the smoke hole, hides on the walls, a long table of stolen plates. Empty: the ogres are out hunting. 'Burn?' at the pit.")
room('room:bunks_w', 'West bunkhouse', outline=rect(*BUNKS_W), floor=0, theme='theme:straw', ambient=16,
     walls=walls_of('bunks_w', BUNKS_W), **roof('bunks_w', BUNKS_W, 448, 512),
     platforms=[{'id': f'platform:bunk_{n}', 'outline': rect(*b), 'rise': 32, 'surface': PLANK, 'top_surface': STRAW,
                 'notes': "A bunk of logs and furs."}
                for n, b in enumerate([(1088, 1792, 1344, 1952), (1408, 1792, 1664, 1952), (1088, 864, 1344, 1024),
                                       (1472, 864, 1728, 1024)], 1)],
     notes="Bunks of logs and furs along the walls, 1,152 square; the ladder's hole down to the west cellar by the east wall.")
room('room:plunder_w', 'Plunder store', outline=rect(*PLUNDER_W), floor=0, theme='theme:timber', ambient=16, store=True,
     walls=walls_of('plunder_w', PLUNDER_W), **roof('plunder_w', PLUNDER_W, 448, 512),
     notes="Kramer's stolen cargo in heaps, 1,152 square: bolts of cloth, sacks, his caravan's barrels, a strongbox (the chest); the trapdoor's hole down to the west cellar by the west wall.")
# ------------------------------------------------------------------------------------------------ floor 0, east fort
room('room:gateway_e', 'East gateway', outline=rect(*GWY_E), floor=0, ceiling=448, theme='theme:palisade', ambient=22,
     walls=walls_of('gateway_e', GWY_E, PALIS),
     notes="The way through the east fort's palisade: the log gate's two leaves south, the yard and the pass north (the exit to D2).")
room('room:gate_e', 'East fort gate', outline=rect(*GATE_E), floor=0, theme='theme:timber', ambient=18,
     walls=walls_of('gate_e', GATE_E), **roof('gate_e', GATE_E, 448, 512),
     notes="Inside the east fort's log gate: the gate north, Graalg's hall's double door south. The arrival from D2's entrance:dd13_east.")
room('room:hall_e', 'East fort hall', outline=rect(*HALL_E), floor=0, theme='theme:timber', ambient=16,
     walls=with_covers(walls_of('hall_e', HALL_E), HIDES_E), **hall_roof('hall_e', HALL_E, PIT_E), beams=BEAMS_E,
     platforms=[pit('platform:pit_e', PIT_E, 208, "Graalg's fire pit, the bigger one."), PATCH_E,
                {'id': 'platform:seat', 'outline': blob(8250, -1100, 150, 120), 'rise': 96, 'surface': BONES,
                 'top_surface': BONES, 'notes': "Graalg's seat: a heap of antlers and bones."}]
     + RUBBLE_E,
     notes="Graalg's own hall, 1,792 by 1,600: a bigger fire pit, his seat of antlers by the east wall, hides on the walls. Empty: out hunting. 'Burn?' at the pit.")
room('room:kennel_e', 'Kennel', outline=rect(*KENNEL_E), floor=0, slope={'to': -512, 'toward': 'west'},
     ceiling=448, ceiling_slope={'to': -64, 'toward': 'west'}, theme='theme:straw', ambient=14,
     walls=walls_of('kennel_e', KENNEL_E),
     notes="A pen of chewed logs behind the barred gate, its floor a ramp of trampled straw falling 512 west to the east cellar; the ogres' sabertooths.")
room('room:graalg', "Graalg's quarters", outline=rect(*GRAALG), floor=0, theme='theme:straw', ambient=16,
     walls=walls_of('graalg', GRAALG), **roof('graalg', GRAALG, 448, 512),
     platforms=[{'id': 'platform:graalg_bed', 'outline': rect(6048, -704, 6464, -416), 'rise': 40, 'surface': PLANK,
                 'top_surface': STRAW, 'notes': "Graalg's bed, the size of a cart."}],
     notes="Furs, a bed the size of a cart and Graalg's strongbox, 1,152 by 1,024; the trapdoor's hole down to the east cellar by the west wall.")
# ------------------------------------------------------------------------------------------------ floor -512
room('room:cellar_w', 'West cellar', outline=rect(*CELLAR_W), floor=-512, ceiling=-128, theme='theme:cave', ambient=14,
     notes="Dug into the knoll under the west blockhouse, 3,968 by 640: barrels, smoked meat; the two ladders up at its ends, the run's mouth south.")
room('room:run', "The ogres' run", path=RUN, width=320, floor=-512, ceiling=-128, theme='theme:cave', ambient=12,
     beams=[{'path': [[x, -352], [x, -32]], 'bottom': -208, 'width': 32, 'depth': 48, 'surface': BEAM}
            for x in (2432, 2944, 3456)],
     notes="A timbered tunnel under the pass road, 320 wide and about 4,000 long, from the west cellar to the east cellar; the Sardaj loot cave off its north side.")
room('room:loot_cave', 'Sardaj loot', outline=rect(*LOOT), floor=-512, ceiling=-96, theme='theme:cave', ambient=14,
     platforms=[{'id': 'platform:disk_case', 'outline': rect(3136, 640, 3232, 704), 'rise': 32, 'surface': PLANK,
                 'top_surface': CHAR, 'notes': "A broken disk case, empty, with Graalg's boast scratched on it."}],
     notes="A side cave off the run, 768 by 736: barbarian shields and bead-strung spears taken from Yog's Sardaj, the brutes' pile (the chest), and a broken disk case, empty.")
room('room:cellar_e', 'East cellar', outline=CELLAR_E, floor=-512, ceiling=-128, theme='theme:cave', ambient=14,
     notes="Under the east blockhouse: Graalg's beer, a rack of clubs; the run comes in from the north, the kennel's ramp east, the ladder up to Graalg's quarters in its north-east arm.")

# ------------------------------------------------------------------------------------------------ openings
op('open:gate_w', 'room:gate_w', 'room:gateway_w', link='link:gate_w', width=384, height=352,
   notes="The west fort's log gate: two leaves.")
op('open:gatew_hall', 'room:gate_w', 'room:hall_w', link='link:gatew_hall', width=320, height=352,
   notes="The blockhouse's double door.")
op('open:hallw_bunks', 'room:hall_w', 'room:bunks_w', link='link:hallw_bunks', width=192, height=288, along=0.25)
op('open:hallw_plunder', 'room:hall_w', 'room:plunder_w', link='link:hallw_plunder', width=192, height=288, along=0.75)
op('open:bunks_cellar', 'room:bunks_w', 'room:cellar_w', link='link:bunks_cellar', **{'in': 'floor'},
   at=[LADDER_BUNKS[0] - 16 - HOLE // 2, LADDER_BUNKS[1]], size=[HOLE, HOLE], reveal=PLANK,
   notes="The bunkhouse's ladder hole.")
op('open:plunder_cellar', 'room:plunder_w', 'room:cellar_w', link='link:plunder_cellar', **{'in': 'floor'},
   at=[LADDER_PLUNDER[0] + 16 + HOLE // 2, LADDER_PLUNDER[1]], size=[HOLE, HOLE], reveal=PLANK,
   notes="The plunder store's trapdoor hole.")
op('open:cellarw_run', 'room:cellar_w', 'room:run', link='link:cellarw_run', width=288, height=320)
op('open:run_loot', 'room:run', 'room:loot_cave', link='link:run_loot', width=288, height=320)
op('open:run_cellare', 'room:run', 'room:cellar_e', link='link:run_cellare', width=288, height=320)
op('open:cellare_kennel', 'room:cellar_e', 'room:kennel_e', link='link:cellare_kennel', width=288, height=320,
   from_wall=1, to_wall='west',
   notes="The foot of the kennel's ramp.")
op('open:halle_kennel', 'room:hall_e', 'room:kennel_e', link='link:kennel_hall', width=256, height=288,
   notes="The kennel's barred gate.")
op('open:halle_graalg', 'room:hall_e', 'room:graalg', link='link:halle_graalg', width=192, height=288, along=0.5)
op('open:graalg_cellar', 'room:graalg', 'room:cellar_e', link='link:graalg_cellar', **{'in': 'floor'},
   at=[LADDER_GRAALG[0] - 16 - HOLE // 2, LADDER_GRAALG[1]], size=[HOLE, HOLE], reveal=PLANK,
   notes="Graalg's trapdoor hole.")
op('open:halle_gate', 'room:hall_e', 'room:gate_e', link='link:halle_gate', width=320, height=352,
   notes="The blockhouse's double door.")
op('open:gate_e', 'room:gate_e', 'room:gateway_e', link='link:gate_e', width=384, height=352,
   notes="The east fort's log gate: two leaves.")

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:timber', 'ambient': 16}, 'rooms': rooms,
             'openings': openings,
             'notes': "DD-13 Ogre Forts: two blockhouses on floor 0 (west fort north of D2's pass road, east fort south of it), their cellars and the ogres' run under the road at -512; x east, y north. Written by output/studio_cal/dd13/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {r['id']: r['floor'] for r in rooms}
OGRE, BRUTE, CHIEF, CAT = 11066, 11067, 11068, 11413
# (id, kind, size, purpose, population [(monster, count)], chest)
PLAN_SPACES = [
    ('room:gateway_w', 'corridor', 'S', "The way through the west palisade: the log gate's two leaves, the yard and D2 beyond.", [], None),
    ('room:gate_w', 'room', 'S', "Inside the west fort's log gate: the yard's noise behind, the blockhouse door ahead. Burned: charred.", [], None),
    ('room:hall_w', 'room', 'L', "The west blockhouse's hall: a fire pit, hides on the walls, a long table of stolen plates. Empty: the ogres are out hunting. 'Burn?'", [], None),
    ('room:bunks_w', 'room', 'M', "Bunks of logs and furs, snoring ogres; a ladder down to the cellar.", [(OGRE, 4)], None),
    ('room:plunder_w', 'room', 'M', "Kramer's stolen cargo in heaps, a strongbox (the chest); a trapdoor to the cellar.", [(OGRE, 2)], 3),
    ('room:gateway_e', 'corridor', 'S', "The way through the east palisade: the log gate's two leaves, the yard and D2 beyond.", [], None),
    ('room:gate_e', 'room', 'S', "Inside the east fort's log gate. Burned: charred.", [], None),
    ('room:hall_e', 'room', 'L', "Graalg's own hall: a bigger fire pit, his seat of antlers. Empty: out hunting. 'Burn?'", [], None),
    ('room:kennel_e', 'room', 'M', "A pen of chewed logs behind a barred gate; sabertooths; its floor a ramp down to the east cellar.", [(CAT, 4)], None),
    ('room:graalg', 'room', 'M', "Furs, a bed the size of a cart, and Graalg's strongbox: the Sardaj's 2 Energy Disks (q-d11.fort_search, barred after a peace). A trapdoor to the cellar.", [(CHIEF, 2)], 3),
    ('room:cellar_w', 'room', 'M', "Dug into the knoll under the blockhouse: barrels, smoked meat, the run's mouth.", [(OGRE, 3)], None),
    ('room:run', 'corridor', 'L', "A long timbered tunnel under the pass between the forts; cart wheels rumble overhead.", [(OGRE, 2), (BRUTE, 2)], None),
    ('room:loot_cave', 'room', 'S', "Barbarian shields and spears taken from Yog's Sardaj, a broken disk case with Graalg's boast; brutes on the pile (the chest).", [(BRUTE, 3)], 3),
    ('room:cellar_e', 'room', 'M', "Under the east blockhouse: Graalg's beer, a rack of clubs; the kennel's ramp and the trapdoor to his quarters.", [(OGRE, 1), (BRUTE, 2)], None),
]
LEVEL = {OGRE: 18, BRUTE: 22, CHIEF: 30, CAT: 22}
NAME = {OGRE: 'Ogre', BRUTE: 'Ogre Brute', CHIEF: 'Ogre Chief', CAT: 'Kennel Sabertooth'}
LINKS = [
    ('link:gate_w', 'room:gate_w', 'room:gateway_w', 'door', "The west fort's log gate: two leaves that part in the middle."),
    ('link:gatew_hall', 'room:gate_w', 'room:hall_w', 'door', "The blockhouse's double door."),
    ('link:hallw_bunks', 'room:hall_w', 'room:bunks_w', 'door', None),
    ('link:hallw_plunder', 'room:hall_w', 'room:plunder_w', 'door', None),
    ('link:bunks_cellar', 'room:bunks_w', 'room:cellar_w', 'ladder', "The bunkhouse's ladder through a hole in its floor."),
    ('link:plunder_cellar', 'room:plunder_w', 'room:cellar_w', 'ladder', "The trapdoor (a hinged plank leaf) and its ladder."),
    ('link:cellarw_run', 'room:cellar_w', 'room:run', 'open', None),
    ('link:run_loot', 'room:run', 'room:loot_cave', 'open', None),
    ('link:run_cellare', 'room:run', 'room:cellar_e', 'open', None),
    ('link:cellare_kennel', 'room:cellar_e', 'room:kennel_e', 'open', "The kennel's floor is the ramp (512 up to the east)."),
    ('link:kennel_hall', 'room:kennel_e', 'room:hall_e', 'door', "The kennel's barred gate, opened from either side."),
    ('link:halle_graalg', 'room:hall_e', 'room:graalg', 'door', None),
    ('link:graalg_cellar', 'room:graalg', 'room:cellar_e', 'ladder', "Graalg's trapdoor (a hinged plank leaf) and its ladder."),
    ('link:halle_gate', 'room:hall_e', 'room:gate_e', 'door', "The blockhouse's double door."),
    ('link:gate_e', 'room:gate_e', 'room:gateway_e', 'door', "The east fort's log gate: two leaves that part in the middle."),
]


def plan_doc(level):
    spaces = []
    for sid, kind, size, purpose, pop, chest in PLAN_SPACES:
        r = next(x for x in rooms if x['id'] == sid)
        s = {'id': sid, 'name': r['name'], 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'actor': m, 'groups': 1, 'levels': [LEVEL[m], LEVEL[m]],
                                'notes': f"{n} placed {NAME[m]} ({m})."} for m, n in pop]
        else:
            s['empty'] = True
        spaces.append(s)
    links = []
    for lid, a, b, kind, notes in LINKS:
        d = {'id': lid, 'from': a, 'to': b, 'kind': kind}
        if notes:
            d['notes'] = notes
        links.append(d)
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Two ogre forts on their knolls either side of D2's pass road, each a timber blockhouse round a fire-pit hall over a cellar dug into the knoll, the cellars joined by the ogres' run under the road. The halls are empty ('the Ogres are out hunting'); the stay-behinds sleep in the bunks, guard the plunder and the cellars, and Graalg's two chiefs sit by his strongbox. Each hall's fire pit asks the source's 'Burn?': yes sets the hall ablaze round the party, and the fort stands charred and empty on every later visit.",
        'purpose': "Q-D11 Graalg's Ogres, the war route: A3's hooks q-d11.fort_west and q-d11.fort_east at the two fire pits (west_burned 113224 / east_burned 113225 and hostile 113222), q-d11.fort_search at Graalg's strongbox (2 Energy Disks, barred after a peace 113223). Party 22-26, the pass ogres 11066-11068 (18, 22, 30) and the Kennel Sabertooth 11413 (22), 25 placed, treasure 3.",
        'mood': "Smoky timber halls lit by fire pits and wall torches, straw and hides; cold rock under them. After a burn: black timber, fallen roof, ash.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:west', 'spaces': ['room:hall_w', 'room:bunks_w', 'room:cellar_w', 'room:plunder_w'],
             'notes': "Round the west blockhouse and its cellar."},
            {'id': 'loop:east', 'spaces': ['room:hall_e', 'room:kennel_e', 'room:cellar_e', 'room:graalg'],
             'notes': "Round the east blockhouse and its cellar."},
            {'id': 'loop:pass', 'spaces': ['room:gate_w', 'room:hall_w', 'room:bunks_w', 'room:cellar_w', 'room:run',
                                           'room:cellar_e', 'room:graalg', 'room:hall_e', 'room:gate_e'],
             'notes': "In at one gate, through the run, out at the other, back over the pass road on D2."},
        ],
        'entrances': [
            {'id': 'entrance:d2_west', 'space': 'room:gate_w', 'kind': 'both', 'neighbour': 'exit:d2_west',
             'facing': 'n', 'how': "From and to D2's entrance:dd13_west, the west fort's gate on its knoll north of the road: inside the gate, facing in (north)."},
            {'id': 'entrance:d2_east', 'space': 'room:gate_e', 'kind': 'both', 'neighbour': 'exit:d2_east',
             'facing': 's', 'how': "From and to D2's entrance:dd13_east, the east fort's gate on its knoll south of the road: inside the gate, facing in (south); D2 arrives here by explicit coordinates (D-25 Q10)."},
        ],
        'critical_path': ['room:gate_w', 'room:hall_w', 'room:bunks_w', 'room:cellar_w', 'room:run', 'room:cellar_e',
                          'room:graalg', 'room:hall_e'],
        'return_path': ['room:hall_e', 'room:gate_e', 'room:gateway_e'],
        'goals': [
            {'id': 'goal:burn_w', 'space': 'room:hall_w', 'kind': 'use', 'story': 'Q-D11',
             'what': "'Burn?' at the west hall's fire pit (aaze0015:7): A3's q-d11.fort_west.", 'gives': {'qbit': 'west_burned'}},
            {'id': 'goal:burn_e', 'space': 'room:hall_e', 'kind': 'use', 'story': 'Q-D11',
             'what': "'Burn?' at the east hall's fire pit: A3's q-d11.fort_east.", 'gives': {'qbit': 'east_burned'}},
            {'id': 'goal:disks', 'space': 'room:graalg', 'kind': 'take', 'story': 'Q-D11',
             'what': "Graalg's strongbox: 2 Energy Disks (q-d11.fort_search, aaze0015:23), barred after a peace.",
             'gives': {'qbit': 'fort_disks'}},
        ],
        'set_pieces': [
            {'id': 'set:burn', 'kind': 'scripted', 'spaces': ['room:hall_w', 'room:hall_e'],
             'rule': "Yes at a hall's fire pit: the hall's walls and roof burn (xoburn), fire lights pulse, the hides and the table burn away; 4 s later every timber face of that fort is charred (xochar), the roof is down round the pit, embers glow. Every later load with that fort's qbit: charred, the roof down, that fort's ogres (and the kennel's cats) gone."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 25, 'chests': 3,
                   'doors': 10, 'loops': 3, 'floor_area_munits2': 19},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/dd13.graph.yml with D-25 (mockups/act3_a7_decisions.md: the party stays in the burning hall; the kennel's cats a row in the ogres' faction; a peace-then-burn playtest; the east gate by explicit coordinates). The two gateways are rooms of their own (the gates are two-leaf doors, the user's rule of 2026-11-20); the kennel's floor is the graph's ramp; the trapdoors are hinged plank leaves over pole ladders (merge point 22). 14 rooms.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-13 Ogre Forts (not to scale; plan, north up)

   floor 0      (D2: pass road, north side)                          (D2: east gate, north)
                    =exit= GATEWAY W                                    =exit= GATEWAY E
                         ||gate (2 leaves)                                     ||gate (2 leaves)
   [PLUNDER T3] -- [WEST HALL: pit, Burn?] -- [BUNKS]       [GRAALG T3+disks]-- [EAST HALL: pit, Burn?]
        |hole          ||door (2 leaves)        |hole       |hole   [KENNEL]== (ramp down west)
        |              [WEST GATE: start]       |           |          |
   floor -512  [============ WEST CELLAR ============]      [EAST CELLAR]--+
                                    \\                         /
                                     [THE OGRES' RUN under the road]
                                           |
                                      [SARDAJ LOOT T3]
"""

# ================================================================================================ objects.yml
QBITS = {'friends': 113221, 'hostile': 113222, 'peace': 113223, 'west_burned': 113224, 'east_burned': 113225,
         'fort_disks': 113226}


def gate(id, opening, notes):
    return {'id': id, 'opening': opening, 'kind': 'slide_left', 'leaves': 2, 'thickness': 32, 'speed': 128,
            'pictures': [[LEAF_L, LEAF_R]], 'back_pictures': [[LEAF_L, LEAF_R]],
            'edge_surface': S('t66abc10a', 32, 128), 'notes': notes}


# Merge point 22: the trapdoors over the plunder store's and Graalg's ladder holes, one plank leaf (gkp1ceil, the walls'
# planks, at its size) 16 thick filling the hole, its top flush with the floor. It turns on the side of the hole away
# from the ladder's top and swings down into the cellar (TRAP_SWING > 0), so the open leaf hangs on the far side of the
# hole from the ladder. TRAP_SWING's sign: see NOTES ("Trapdoors").
TRAP_SWING = 95


def trapdoor(id, opening, hinge, notes):
    return {'id': id, 'opening': opening, 'kind': 'hinged', 'hinge': hinge, 'swing': TRAP_SWING, 'thickness': 16,
            'surface': PLANK, 'back_surface': PLANK, 'edge_surface': S('t66abc10a', 32, 128), 'notes': notes}


def single(id, opening, picture, notes):
    return {'id': id, 'opening': opening, 'kind': 'hinged', 'thickness': 24,
            'surface': dict(picture, fit=True), 'back_surface': dict(picture, fit=True),
            'edge_surface': S('t66abc10a', 32, 128), 'notes': notes}


objects = {
    'format': 0,
    'start': {'room': 'room:gate_w', 'at': [0, -64], 'facing': 'n',
              'notes': "Inside the west fort's gate from D2's entrance:dd13_west, facing in (north): the blockhouse's double door ahead."},
    'doors': [
        gate('door:gate_w', 'open:gate_w', "The west fort's log gate: two plank leaves (gkp103a/gkp103b, a mirrored pair) that part in the middle."),
        gate('door:hall_w', 'open:gatew_hall', "The west blockhouse's double door: two leaves that part in the middle."),
        single('door:bunks_w', 'open:hallw_bunks', PLANK_DOOR, "The bunkhouse's plank door."),
        single('door:plunder_w', 'open:hallw_plunder', PLANK_DOOR, "The plunder store's plank door."),
        {'id': 'door:kennel', 'opening': 'open:halle_kennel', 'kind': 'slide_up', 'fold': True, 'thickness': 16,
         'speed': 160, 'surface': PALIS, 'tile': True, 'notes': "The kennel's gate of lashed logs (xopalis): it folds up into the lintel. (The see-through pole gate xopoles shows magenta speckle through its holes, as in XD-05: not used.)"},
        single('door:graalg', 'open:halle_graalg', PLANK_DOOR, "Graalg's plank door."),
        # The plunder store's ladder comes up on the hole's west side: hinged east. Graalg's on its east side: west.
        trapdoor('door:plunder_trap', 'open:plunder_cellar', 'east',
                 "The plunder store's trapdoor: hinged on the hole's east side, it swings down into the west cellar "
                 "clear of the ladder on the west."),
        trapdoor('door:graalg_trap', 'open:graalg_cellar', 'west',
                 "Graalg's trapdoor: hinged on the hole's west side, it swings down into the east cellar clear of the "
                 "ladder on the east."),
        gate('door:hall_e', 'open:halle_gate', "Graalg's hall's double door: two leaves that part in the middle."),
        gate('door:gate_e', 'open:gate_e', "The east fort's log gate: two plank leaves that part in the middle."),
    ],
    'ladders': [
        {'id': 'ladder:bunks', 'room': 'room:cellar_w', 'at': [LADDER_BUNKS[0] - 26, LADDER_BUNKS[1]], 'facing': 'e',
         'height': 512, 'floor_height': -512, 'exit': [LADDER_BUNKS[0] + 96, LADDER_BUNKS[1]], 'grab_at_top': True,
         'surface': POLES, 'notes': "A pole ladder up the cellar's east wall into the bunkhouse."},
        {'id': 'ladder:plunder', 'room': 'room:cellar_w', 'at': [LADDER_PLUNDER[0] + 26, LADDER_PLUNDER[1]],
         'facing': 'w', 'height': 512, 'floor_height': -512, 'exit': [LADDER_PLUNDER[0] - 96, LADDER_PLUNDER[1]],
         'grab_at_top': True, 'surface': POLES, 'notes': "A pole ladder up the cellar's west wall to the plunder store's trapdoor."},
        {'id': 'ladder:graalg', 'room': 'room:cellar_e', 'at': [LADDER_GRAALG[0] - 26, LADDER_GRAALG[1]], 'facing': 'e',
         'height': 512, 'floor_height': -512, 'exit': [LADDER_GRAALG[0] + 96, LADDER_GRAALG[1]], 'grab_at_top': True,
         'surface': POLES, 'notes': "A pole ladder up the cellar's north-east arm to Graalg's trapdoor."},
    ],
    'sounds': [],
    'lights': [],
    'chests': [
        {'id': 'chest:plunder', 'room': 'room:plunder_w', 'at': [-2064, 1900], 'kind': 'gt002',
         'treasure_level': 3, 'random_items': 2, 'gold': 600, 'notes': "Kramer's strongbox among his stolen cargo."},
        {'id': 'chest:strongbox', 'room': 'room:graalg', 'at': [5520, -416], 'kind': 'gt002',
         'treasure_level': 3, 'random_items': 1, 'gold': 800, 'items': ['energy_disk', 'energy_disk'],
         'notes': "Graalg's strongbox: the Sardaj's 2 Energy Disks (q-d11.fort_search), barred after a peace."},
        {'id': 'chest:loot', 'room': 'room:loot_cave', 'at': [2720, 740], 'kind': 'gt002',
         'treasure_level': 3, 'random_items': 2, 'gold': 500, 'notes': "The Sardaj's spoils the brutes sit on."},
    ],
    'monsters': [],
    'decorations': [],
    'destructibles': [],
    'exits': [
        {'id': 'exit:gate_w', 'room': 'room:gateway_w', 'wall': 'south', 'size': [512, 256], 'surface': S('7solid01', 256, 128, fit=True),
         'to': 'exit:d2_west', 'notes': "The open gateway onto the yard and the pass road (D2)."},
        {'id': 'exit:gate_e', 'room': 'room:gateway_e', 'wall': 'north', 'size': [512, 256], 'surface': S('7solid01', 256, 128, fit=True),
         'to': 'exit:d2_east', 'notes': "The open gateway onto the yard and the pass road (D2)."},
    ],
}

# Monsters: placed, one group per room; the pass ogres' rows (faction pass: hostile at load, friendly on q-d11.friends,
# hostile again on q-d11.hostile) and the kennel's cats on the same faction. No `hostile` key: their attitude is the
# world's relations', so a peace turns them friendly and a burn turns them back.
PLACED = [
    ('room:bunks_w', 10, [(OGRE, [1250, 1200], 90), (OGRE, [1600, 1250], 180), (OGRE, [1300, 1600], 270),
                          (OGRE, [1700, 1650], 180)]),
    ('room:plunder_w', 11, [(OGRE, [-1650, 1150], 90), (OGRE, [-1500, 1650], 0)]),
    ('room:cellar_w', 12, [(OGRE, [-1100, 1500], 0), (OGRE, [0, 1400], 90), (OGRE, [900, 1550], 180)]),
    ('room:run', 13, [(OGRE, [1536, 650], 90), (OGRE, [2700, -192], 180), (BRUTE, [3200, -192], 180),
                      (BRUTE, [4352, -680], 90)]),
    ('room:cellar_e', 14, [(OGRE, [4600, -1200], 90), (BRUTE, [4500, -1800], 0), (BRUTE, [4900, -2000], 0)]),
    ('room:loot_cave', 15, [(BRUTE, [2800, 450], 270), (BRUTE, [3100, 500], 270), (BRUTE, [2950, 250], 270)]),
    ('room:kennel_e', 16, [(CAT, [5750, -1700], 0), (CAT, [6050, -1950], 0), (CAT, [6250, -1700], 0),
                           (CAT, [5850, -2050], 0)]),
    ('room:graalg', 17, [(CHIEF, [6100, -900], 180), (CHIEF, [6250, -1150], 180)]),
]
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                                    'facing': facing, 'group': group})
WEST_GROUPS, EAST_GROUPS = [10, 11, 12], [14, 16, 17]


def deco(key, room_id, name, at, **kw):
    d = {'id': f'deco:{key}', 'room': room_id, 'decoration': name, 'at': at}
    d.update(kw)
    objects['decorations'].append(d)
    return d


# Wall torches (torch01 in its iron bracket at 160 over the floor, MM7's height) with their light just in front of the
# flame (at 24 from the wall, 184 up): every light hangs on a wall, stands on a floor fixture, or is a fire pit's.
TORCHES = {'w': [], 'e': [], 'deep': []}
lights = objects['lights']


def torch(key, room_id, wall, x, y, fort, floor=0):
    nx, ny = {'north': (0, -24), 'south': (0, 24), 'east': (-24, 0), 'west': (24, 0)}[wall]
    fl = {} if floor is None else {'floor_height': floor}
    deco(f'torch_{key}', room_id, 'torch01', [x, y], wall=wall, height=160, **fl)
    lights.append({'id': f'light:torch_{key}', 'room': room_id, 'at': [x + nx, y + ny], 'height': 184, **fl,
                   'radius': 900, 'color': [255, 170, 90], 'notes': "The wall torch's flame."})
    TORCHES[fort].append(key)


# west fort
torch('gwy_w_e', 'room:gateway_w', 'east', 384, -448, 'w')
torch('gwy_w_w', 'room:gateway_w', 'west', -384, -448, 'w')
torch('gate_w_e', 'room:gate_w', 'east', 512, 160, 'w')
torch('gate_w_w', 'room:gate_w', 'west', -512, 160, 'w')
torch('hall_w_e', 'room:hall_w', 'east', 896, 1900, 'w')
torch('hall_w_w', 'room:hall_w', 'west', -896, 1900, 'w')
torch('hall_w_se', 'room:hall_w', 'south', 600, 640, 'w')
torch('hall_w_sw', 'room:hall_w', 'south', -600, 640, 'w')
torch('bunks_w', 'room:bunks_w', 'north', 1900, 1984, 'w')
torch('bunks_s', 'room:bunks_w', 'south', 1900, 832, 'w')
torch('plunder_n', 'room:plunder_w', 'north', -1600, 1984, 'w')
torch('plunder_e', 'room:plunder_w', 'east', -1024, 1700, 'w')
# east fort
torch('gwy_e_e', 'room:gateway_e', 'east', 7936, 448, 'e')
torch('gwy_e_w', 'room:gateway_e', 'west', 7168, 448, 'e')
torch('gate_e_e', 'room:gate_e', 'east', 8064, -160, 'e')
torch('gate_e_w', 'room:gate_e', 'west', 7040, -160, 'e')
torch('hall_e_ne', 'room:hall_e', 'north', 8160, -640, 'e')
torch('hall_e_nw', 'room:hall_e', 'north', 6944, -640, 'e')
torch('hall_e_e', 'room:hall_e', 'east', 8448, -1800, 'e')
torch('hall_e_w', 'room:hall_e', 'west', 6656, -2050, 'e')
torch('graalg_n', 'room:graalg', 'north', 5800, -320, 'e')
torch('graalg_e', 'room:graalg', 'east', 6528, -500, 'e')
torch('kennel_e', 'room:kennel_e', 'north', 6300, -1472, 'e', None)
# cellars, run, loot cave (they do not burn)
torch('cellar_w_n1', 'room:cellar_w', 'north', -1200, 1792, 'deep', -512)
torch('cellar_w_n2', 'room:cellar_w', 'north', 300, 1792, 'deep', -512)
torch('cellar_w_s', 'room:cellar_w', 'south', -400, 1152, 'deep', -512)
torch('run_n1', 'room:run', 'north', 2700, -32, 'deep', -512)
torch('run_s1', 'room:run', 'south', 3500, -352, 'deep', -512)
torch('loot_w', 'room:loot_cave', 'west', 2560, 500, 'deep', -512)
torch('cellar_e_w', 'room:cellar_e', 'west', 4096, -1600, 'deep', -512)
torch('cellar_e_s', 'room:cellar_e', 'south', 4700, -2240, 'deep', -512)

# The fire pits: a fire on each pit (the floor fixture) with its light 64 over the pit's top; the burn's lights.
for k, (px, py), room_id in (('w', PIT_W, 'room:hall_w'), ('e', PIT_E, 'room:hall_e')):
    # floor_height 24: the pit's top (the roof patch over the smoke hole is the highest floor there, D-34).
    deco(f'fire_{k}', room_id, 'ckfyr00', [px, py], floor_height=24, notes="The ogres' fire in its pit.")
    lights.append({'id': f'light:pit_{k}', 'room': room_id, 'at': [px, py], 'floor_height': 24, 'height': 88, 'radius': 1600,
                   'color': [255, 150, 70], 'pulse': {'intensity': [0.75, 1], 'frequency': 0.9},
                   'notes': "The fire in the pit (off once the fort has burned)."})
    lights.append({'id': f'light:blaze_{k}', 'room': room_id, 'at': [px, py], 'floor_height': 24, 'height': 120, 'radius': 2600,
                   'color': [255, 140, 50], 'on': False, 'pulse': {'intensity': [0.7, 1], 'frequency': 1.5},
                   'notes': "The burn: the pit's fire roaring up into the burning roof."})
    lights.append({'id': f'light:embers_{k}', 'room': room_id, 'at': [px, py], 'floor_height': 24, 'height': 48, 'radius': 800,
                   'color': [220, 80, 30], 'on': False, 'pulse': {'intensity': [0.8, 1], 'frequency': 0.3},
                   'notes': "Embers in the pit after the burn."})
# The burning walls' lights: on each long wall of the hall, 24 in front of it, 240 up (on the burning wall).
for k, (x0, y0, x1, y1), room_id in (('w', HALL_W, 'room:hall_w'), ('e', HALL_E, 'room:hall_e')):
    for side, at in (('n', [(x0 + x1) // 2, y1 - 24]), ('s', [(x0 + x1) // 2 + 400, y0 + 24]),
                     ('ea', [x1 - 24, (y0 + y1) // 2]), ('we', [x0 + 24, (y0 + y1) // 2])):
        lights.append({'id': f'light:blaze_{k}_{side}', 'room': room_id, 'at': at, 'height': 240, 'radius': 1400,
                       'color': [255, 130, 40], 'on': False,
                       'pulse': {'intensity': [0.6, 1], 'frequency': 1.2 + 0.2 * len(side)},
                       'notes': "The burn: the wall ablaze (a light on the burning wall)."})
# Daylight at each gateway's exit: on the exit wall, 24 in front of it.
# D-34 (3): the Darkside's dim amber-grey day (xeendark1), not a meadow's noon.
DARK_DAY = [96, 88, 76]
lights.append({'id': 'light:day_w', 'room': 'room:gateway_w', 'at': [0, GWY_W[1] + 24], 'height': 200, 'radius': 420,
               'color': DARK_DAY, 'notes': "The Darkside's dim daylight from the open gateway (on its wall)."})
lights.append({'id': 'light:day_e', 'room': 'room:gateway_e', 'at': [7552, GWY_E[3] - 24], 'height': 200,
               'radius': 420, 'color': DARK_DAY, 'notes': "The Darkside's dim daylight from the open gateway (on its wall)."})

# Daylight through the burnt roofs: off while the forts stand, on once a fort has burned (each under its room's roof
# peak, 24 below the ceiling: a hole in the roof, not a lamp).
DAYROOF = {'w': [], 'e': []}
for k, key, r, h in (('w', 'gateway_w', GWY_W, 424), ('w', 'gate_w', GATE_W, 488), ('w', 'hall_w', HALL_W, 744),
                     ('w', 'bunks_w', BUNKS_W, 488), ('w', 'plunder_w', PLUNDER_W, 488),
                     ('e', 'gateway_e', GWY_E, 424), ('e', 'gate_e', GATE_E, 488), ('e', 'hall_e', HALL_E, 744),
                     ('e', 'graalg', GRAALG, 488), ('e', 'kennel_e', KENNEL_E, 424)):
    at = [(r[0] + r[2]) // 2, (r[1] + r[3]) // 2]
    radius, notes = 1000, "The Darkside's dim daylight through the burnt roof (the burned stage)."
    if key == 'kennel_e':
        at = [6300, (r[1] + r[3]) // 2]
    if key in ('hall_w', 'hall_e'):
        # D-34 (2): under the smoke hole's rim, 24 below the ring's lowest point.
        at, h, radius = list(PIT_W if key == 'hall_w' else PIT_E), 680, 1700
        notes = "The Darkside's dim daylight down through the open smoke hole (the burned stage)."
    fl = {'floor_height': 0} if key in ('hall_w', 'hall_e') else {}
    lights.append({'id': f'light:sky_{key}', 'room': f'room:{key}', 'at': at, **fl, 'height': h, 'radius': radius,
                   'color': [128, 120, 108] if key in ('hall_w', 'hall_e') else [118, 110, 100], 'on': False,
                   'notes': notes})
    DAYROOF[k].append(f'light:sky_{key}')

objects['sounds'] = [
    {'id': 'sound:pit_w', 'room': 'room:hall_w', 'at': list(PIT_W), 'floor_height': 24, 'sound': 'campfire', 'radius': 2000,
     'inner_radius': 600, 'volume': 0.7, 'notes': "The west hall's fire."},
    {'id': 'sound:pit_e', 'room': 'room:hall_e', 'at': list(PIT_E), 'floor_height': 24, 'sound': 'campfire', 'radius': 2000,
     'inner_radius': 600, 'volume': 0.7, 'notes': "Graalg's fire."},
    {'id': 'sound:blaze_w', 'room': 'room:hall_w', 'at': list(PIT_W), 'floor_height': 24, 'sound': 'raging fire loop', 'radius': 3600,
     'inner_radius': 1400, 'volume': 0.9, 'on': False, 'notes': "The west fort burning."},
    {'id': 'sound:blaze_e', 'room': 'room:hall_e', 'at': list(PIT_E), 'floor_height': 24, 'sound': 'raging fire loop', 'radius': 3600,
     'inner_radius': 1400, 'volume': 0.9, 'on': False, 'notes': "The east fort burning."},
    {'id': 'sound:wind_w', 'room': 'room:gateway_w', 'at': [0, -500], 'sound': 'whistling wind', 'radius': 1200,
     'inner_radius': 300, 'volume': 0.4, 'notes': "The wind over the pass at the gateway."},
    {'id': 'sound:wind_e', 'room': 'room:gateway_e', 'at': [7552, 500], 'sound': 'whistling wind', 'radius': 1200,
     'inner_radius': 300, 'volume': 0.4, 'notes': "The wind over the pass at the gateway."},
    {'id': 'sound:drip', 'room': 'room:run', 'at': [2944, -192], 'sound': 'drip01', 'radius': 1400,
     'inner_radius': 400, 'volume': 0.5, 'loop': False, 'wait': [3, 8], 'notes': "Water through the run's timbers."},
]

# Dressing (D-7): barrels in pairs by the walls, the plunder store a storeroom (clumps allowed), bones and trash in the
# kennel and bunks, plates on the table, nothing on a walking line.
D = deco
D('table_plates_1', 'room:hall_w', 'dec37', [-640, 2080], floor_height=68)
D('table_plates_2', 'room:hall_w', 'dec36', [-460, 2090], floor_height=68)
D('table_plates_3', 'room:hall_w', 'dec39', [-320, 2070], floor_height=68)
D('hall_w_bones', 'room:hall_w', '7dec18', [800, 2160])
D('bunks_trash', 'room:bunks_w', 'trasheap', [2080, 1900])
D('bunks_bones', 'room:bunks_w', 'dec29', [2110, 1000])
D('plunder_sack_1', 'room:plunder_w', 'floursac', [-2100, 1200])
D('plunder_sack_2', 'room:plunder_w', 'bag01', [-2090, 1320])
D('plunder_sack_3', 'room:plunder_w', 'floursac', [-1980, 1160])
D('plunder_barrel_1', 'room:plunder_w', 'bigbarel', [-1500, 1920])
D('plunder_barrel_2', 'room:plunder_w', 'bigbarel', [-1420, 1920])
D('plunder_barrel_3', 'room:plunder_w', 'smlbarel', [-1460, 1850])
D('plunder_bag_1', 'room:plunder_w', 'bag_A', [-1700, 900])
D('plunder_bag_2', 'room:plunder_w', 'bag01', [-1800, 900])
D('plunder_plates', 'room:plunder_w', 'dec39', [-1880, 1920])
D('cellar_w_barrel_1', 'room:cellar_w', 'bigbarel', [-1700, 1730], floor_height=-512)
D('cellar_w_barrel_2', 'room:cellar_w', 'bigbarel', [-1620, 1730], floor_height=-512)
D('cellar_w_barrel_3', 'room:cellar_w', 'smlbarel', [700, 1730], floor_height=-512)
D('cellar_w_barrel_4', 'room:cellar_w', 'smlbarel', [780, 1730], floor_height=-512)
D('cellar_w_meat', 'room:cellar_w', 'trasheap', [-600, 1720], floor_height=-512)
D('run_bones', 'room:run', '7dec18', [3900, -300], floor_height=-512)
D('loot_bones', 'room:loot_cave', 'dec29', [3240, 160], floor_height=-512)
D('loot_skull', 'room:loot_cave', 'sklplrev', [2620, 160], floor_height=-512)
D('cellar_e_barrel_1', 'room:cellar_e', 'bigbarel', [4170, -2170], floor_height=-512)
D('cellar_e_barrel_2', 'room:cellar_e', 'bigbarel', [4250, -2170], floor_height=-512)
D('cellar_e_cask_1', 'room:cellar_e', '7dec21', [4170, -1700], floor_height=-512)
D('cellar_e_cask_2', 'room:cellar_e', '7dec21', [4170, -1780], floor_height=-512)
D('kennel_bones_1', 'room:kennel_e', 'dec29', [5450, -2160])
D('kennel_bones_2', 'room:kennel_e', '7dec18', [6000, -2170])
D('kennel_bowl', 'room:kennel_e', 'foodbowl', [6460, -2160])
D('graalg_bones', 'room:graalg', '7dec18', [6440, -1250])
D('graalg_goblet', 'room:graalg', '7dec46', [6400, -560], floor_height=40)
D('hall_e_bones', 'room:hall_e', 'dec29', [6750, -720])
D('hall_e_skull', 'room:hall_e', 'sklplrev', [8360, -2160])

# Merge point 21: decorations hidden and shown by events. The pit fires, the fort's wall torches and the table's plates
# are hidden by `{hide: deco:x}` (they were trigger-only destructibles before the word). EMBERS_DECO: the burnt-out
# logs in each pit (dec24x, MM7's burned out fire, its ends still red), `hidden: true` and shown when the fort has
# burned, inside the pit's fire; off until dec24x has a dungeon binding (engine/models/indoor_decorations.yml: the
# build says it draws nothing in this world's dungeons; NOTES "Words needed").
EMBERS_DECO = True
if EMBERS_DECO:
    for k, (px, py), room_id in (('w', PIT_W, 'room:hall_w'), ('e', PIT_E, 'room:hall_e')):
        deco(f'embers_{k}', room_id, 'dec24x', [px, py], floor_height=24, hidden=True, inside=f'deco:fire_{k}',
             notes="The fire burnt down to charred logs, their ends still glowing (shown once the fort has burned).")

# Destructibles: the hides and the west table burn away with their hall.
DESTR = objects['destructibles']
for k, hides in (('w', HIDES_W), ('e', HIDES_E)):
    for _, h in hides:
        DESTR.append({'id': 'destructible:' + h['id'].split(':')[1], 'of': h['id'], 'hp': 20, 'material': 'wood',
                      'notes': "A hide on the hall's wall: burns away with the hall."})
PLATES = ['deco:table_plates_1', 'deco:table_plates_2', 'deco:table_plates_3']
for t in TABLE_W:
    DESTR.append({'id': 'destructible:' + t['id'].split(':')[1], 'of': t['id'], 'hp': 40, 'material': 'wood',
                  'notes': "The long table: burns with the west hall."})

# ================================================================================================ wiring.yml
LINE7 = "You've found an Ogre fort, but the Ogres are out hunting. Burn?"
FORT_ROOMS = {'w': ['gateway_w', 'gate_w', 'hall_w', 'bunks_w', 'plunder_w'],
              'e': ['gateway_e', 'gate_e', 'hall_e', 'kennel_e', 'graalg']}
ROOFED = {'w': ['gate_w', 'hall_w', 'bunks_w', 'plunder_w'], 'e': ['gate_e', 'hall_e', 'graalg']}
SIDES = ['south', 'east', 'north', 'west']
HALL = {'w': 'hall_w', 'e': 'hall_e'}
HIDES = {'w': HIDES_W, 'e': HIDES_E}
RUBBLE = {'w': RUBBLE_W, 'e': RUBBLE_E}
QBIT = {'w': 'west_burned', 'e': 'east_burned'}
HOOK = {'w': 'q-d11.fort_west', 'e': 'q-d11.fort_east'}
GATES = {'w': ['door:gate_w', 'door:hall_w'], 'e': ['door:gate_e', 'door:hall_e']}


def tex(of, to, face=None):
    d = {'of': of, 'to': to}
    if face:
        d['face'] = face
    return {'set_texture': d}


def char_fort(k):
    """Every timber face of the fort charred: walls, roofs, the pit's top, the two double doors."""
    out = [tex(f'panel:{r}_{s}', 'xochar') for r in FORT_ROOMS[k] for s in SIDES]
    out += [tex(f'region:{r}_roof', 'xochar') for r in ROOFED[k]]
    out += [tex(g, 'xochar') for g in GATES[k]]
    return out


def burn_k(k):
    h = HALL[k]
    eff = [{'lua': f'XeenQuests.hook("{HOOK[k]}")'}]
    eff += [tex(f'panel:{h}_{s}', 'xoburn') for s in SIDES] + [tex(f'region:{h}_roof', 'xoburn')]
    eff += [tex(f'platform:roof_patch_{k}', 'xoburn')]
    eff += [{'damage_destructible': {'of': 'destructible:' + x['id'].split(':')[1], 'amount': 1000}}
            for _, x in HIDES[k]]
    if k == 'w':
        eff += [{'damage_destructible': {'of': 'destructible:' + t['id'].split(':')[1], 'amount': 1000}}
                for t in TABLE_W]
        eff += [{'hide': d} for d in PLATES]
    eff += [{'lights_on': [f'light:blaze_{k}'] + [f'light:blaze_{k}_{s}' for s in ('n', 's', 'ea', 'we')]},
            {'lights_off': f'light:pit_{k}'},
            {'set': {'var': {'map_var': f'burning_{k}'}, 'value': 1}},
            {'lua': f"evt.SetMapVar('AmbientSound{{blaze_{k}}}', 1); evt.SetMapVar('AmbientSound{{pit_{k}}}', 2)"}]
    return eff


def burnt_k(k):
    """What a burned fort shows: charred, the roof down round the pit, its fire and torches out (shared by the burn's
    end and the load stage)."""
    eff = char_fort(k) + [tex(f'platform:pit_{k}', 'xochar', 'top')]
    eff += [{'hide': f'platform:roof_patch_{k}'}, {'passable': f'platform:roof_patch_{k}'}]
    for r in RUBBLE[k]:
        eff += [{'show': r['id']}, {'solid': r['id']}]
    eff += [{'hide': f'deco:fire_{k}'}] + ([{'show': f'deco:embers_{k}'}] if EMBERS_DECO else [])
    eff += [{'hide': f'deco:torch_{t}'} for t in TORCHES[k]]
    eff += [{'lights_off': [f'light:pit_{k}'] + [f'light:torch_{t}' for t in TORCHES[k]]},
            {'lights_on': DAYROOF[k]}]
    return eff


events = []
for k, title in (('w', 'Fire pit'), ('e', 'Fire pit')):
    q = QBIT[k]
    events.append(
        {'id': f'evt:pit_{k}', 'preset': 'script', 'source': f'platform:pit_{k}', 'title': title,
         'condition': {'not': {'qbit': q}},
         'question': {'message': LINE7, 'ask': 'Burn (Yes/No)?', 'answers': ['Yes', 'Y', 'yes', 'y'],
                      'wrong_text': "You leave the fort standing, for now."},
         'effects': burn_k(k),
         'else_effects': [{'lua': f'XeenQuests.hook("{HOOK[k]}")'}],
         'notes': f"goal:burn_{k}: the source's question (aaze0015:7) at the hall's fire pit, a real choice. Yes: A3's {HOOK[k]} (sets {q} and hostile 113222, shows aaze0015:7-8), the hall's walls and roof to burning timber (xoburn), its hides{' and table' if k == 'w' else ''} burn away, the fire roars (blaze lights on the walls and the pit); 4 s later evt:burn_out_{k}. Again later: the hook's else line."})
    events.append(
        {'id': f'evt:burn_out_{k}', 'preset': 'script', 'trigger': 'timer', 'every': 4,
         'condition': {'map_var': {'name': f'burning_{k}', 'equals': 1}},
         'effects': [{'set': {'var': {'map_var': f'burning_{k}'}, 'value': 2}}] + burnt_k(k)
         + [{'lights_off': [f'light:blaze_{k}'] + [f'light:blaze_{k}_{s}' for s in ('n', 's', 'ea', 'we')]},
            {'lights_on': f'light:embers_{k}'},
            {'lua': f"evt.SetMapVar('AmbientSound{{blaze_{k}}}', 2)"}],
         'notes': "A few seconds after the burn: the whole fort charred (xochar), the roof down round the pit (the rubble heaps shown and solid), the fire burnt out to embers, the fort's torches gone."})
    events.append(
        {'id': f'evt:stage_{k}', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': q},
         'effects': [{'hide_actors': g} for g in (WEST_GROUPS if k == 'w' else EAST_GROUPS)]
         + [{'destroy': 'destructible:' + x['id'].split(':')[1]} for _, x in HIDES[k]]
         + ([{'destroy': 'destructible:' + t['id'].split(':')[1]} for t in TABLE_W] if k == 'w' else [])
         + ([{'hide': d} for d in PLATES] if k == 'w' else [])
         + burnt_k(k) + [{'lua': f"evt.SetMapVar('AmbientSound{{pit_{k}}}', 2)"}],
         'notes': f"Stage {q} ({QBITS[q]}) on every load (D-23): that fort's rooms charred, the hall's roof down round the pit, its fire and torches out, its ogres{' and the kennel cats' if k == 'e' else ''} gone (groups {WEST_GROUPS if k == 'w' else EAST_GROUPS}). The run and the Sardaj loot cave keep theirs."})
    events.append(
        {'id': f'evt:standing_{k}', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': q}},
         'effects': [e for r in RUBBLE[k] for e in ({'hide': r['id']}, {'passable': r['id']})]
         + [{'show': f'platform:roof_patch_{k}'}, {'solid': f'platform:roof_patch_{k}'}],
         'notes': "The fort still stands: the fallen-roof heaps are not there (hidden and passable), the plank patch "
                  "closes the smoke hole (D-34)."})

events += [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'effects': [{'message': "Ogre Pass: a fort of the ogres on its knoll, timber and hides inside a log palisade, and another across the road joined to it under the pass. Kramer pays for burned forts; Graalg keeps what he takes in his own quarters in the east fort."}],
     'notes': "The errand on arrival (either gate): the two forts, the burn (Kramer's bounty, Q-D11) and Graalg's strongbox."},
    {'id': 'evt:exit_w', 'preset': 'exit', 'source': 'exit:gate_w', 'title': 'Ogre Pass',
     'notes': "Out to D2 in front of the west fort's gate (exit:d2_west); the game's leave window (D-24)."},
    {'id': 'evt:exit_e', 'preset': 'exit', 'source': 'exit:gate_e', 'title': 'Ogre Pass',
     'notes': "Out to D2 in front of the east fort's gate (exit:d2_east); the game's leave window (D-24)."},
    {'id': 'evt:door_gate_w', 'preset': 'door', 'source': 'door:gate_w', 'title': 'Gate', 'action': 'open'},
    {'id': 'evt:door_hall_w', 'preset': 'door', 'source': 'door:hall_w', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_bunks_w', 'preset': 'door', 'source': 'door:bunks_w', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_plunder_w', 'preset': 'door', 'source': 'door:plunder_w', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_kennel', 'preset': 'door', 'source': 'door:kennel', 'title': 'Kennel gate', 'action': 'open'},
    {'id': 'evt:door_graalg', 'preset': 'door', 'source': 'door:graalg', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:trap_plunder', 'preset': 'door', 'source': 'door:plunder_trap', 'title': 'Trapdoor', 'action': 'open'},
    {'id': 'evt:trap_graalg', 'preset': 'door', 'source': 'door:graalg_trap', 'title': 'Trapdoor', 'action': 'open'},
    {'id': 'evt:door_hall_e', 'preset': 'door', 'source': 'door:hall_e', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_gate_e', 'preset': 'door', 'source': 'door:gate_e', 'title': 'Gate', 'action': 'open'},
    {'id': 'evt:chest_plunder', 'preset': 'chest', 'source': 'chest:plunder', 'title': 'Chest'},
    {'id': 'evt:chest_loot', 'preset': 'chest', 'source': 'chest:loot', 'title': 'Chest'},
    {'id': 'evt:strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest',
     'condition': {'not': {'qbit': 'peace'}},
     'effects': [{'lua': 'XeenQuests.hook("q-d11.fort_search")'}],
     'else_effects': [{'lua': 'XeenQuests.hook("q-d11.fort_search")'}],
     'notes': "goal:disks: the strongbox holds the 2 Energy Disks (q-d11.fort_search map_gives); the hook sets fort_disks 113226 and says aaze0015:23 once ('The strongbox is empty.' later). After a peace (113223) it stays shut: the hook's 'Graalg would notice.'"},
    {'id': 'evt:disk_case', 'preset': 'text', 'source': 'platform:disk_case', 'title': 'Broken disk case',
     'window': True,
     'text': "A disk case of Sardaj beadwork, smashed open and empty. Scratched into its lid in a big ogre hand: \"We are Ogres! We take what we want. Yesterday, we took the Sardaj's Energy disks!\"",
     'notes': "Graalg's boast (aaze0015:16) on the empty case (the graph's line)."},
    {'id': 'evt:seat', 'preset': 'text', 'source': 'platform:seat', 'title': "Graalg's seat", 'window': True,
     'text': "Graalg's seat, a heap of antlers and bones. Above it a fat purse of Alamar's gold hangs on a hook, nailed there for every ogre to see."},
    {'id': 'evt:hall_w_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:hall_w', 'once': True,
     'text': "A timber hall round a fire pit, hides on the walls, a long table of stolen plates. Nobody is home.",
     'seconds': 6},
    {'id': 'evt:hall_e_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:hall_e', 'once': True,
     'text': "Graalg's hall: a bigger fire, a seat of antlers. Nobody is home.", 'seconds': 6},
    {'id': 'evt:run_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:run', 'once': True,
     'text': "A long tunnel shored with timber. Cart wheels rumble overhead: the pass road runs above you.",
     'seconds': 6},
    {'id': 'evt:kennel_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:kennel_e', 'once': True,
     'text': "The ogres' kennel. Sabertooths lift their heads from the gnawed logs.", 'seconds': 6},
]
wiring = {'format': 0, 'variables': ['burning_w', 'burning_e'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_dd13', 'name': 'Ogre Forts', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-13', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [22, 10], 'climbs': 'n'},
    'map_stats': {'id': 9166, 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 13, 'environment': 'cave',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Ogre', 'tier': 1, 'per_marker': [2, 3], 'weight': 100}]},
    'neighbours': [
        {'id': 'exit:d2_west', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [4096, 13824, 2016], 'direction': 270,
         'arrival_hint': "A6's point on D2 in front of the west fort's gate (entrance:dd13_west), facing south toward the pass road.",
         'notes': "D2 Sprite Forest and Ogre Pass (A6's): the west fort's gate in its palisade on the knoll north of the road."},
        {'id': 'exit:d2_east', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [11776, 11776, 2048], 'direction': 90,
         'arrival_hint': "A6's point on D2 in front of the east fort's gate (entrance:dd13_east), facing north toward the pass road.",
         'notes': "D2: the east fort's gate on its knoll south of the road. D2's door into DD-13 here arrives by explicit coordinates (gate_e, facing south)."},
    ],
    'qbits': QBITS,
    'items': {'energy_disk': 12334},
    'notes': "Xeen design brief, level L4: DD-13 Ogre Forts on D2's Ogre Pass (Q-D11 Graalg's Ogres, the war route). Monsters: A2's pass ogres, all placed (12 Ogre 11066 at 18, 7 Ogre Brute 11067 at 22, 2 Ogre Chief 11068 at 30) and 4 Kennel Sabertooth 11413 (22), faction pass (hostile at load, friendly on q-d11.friends 113221, hostile on q-d11.hostile 113222), groups 10-17 by room; no rest encounters (encounter 0: the forts are empty or burned, and a rest spawn would ignore the peace). Hooks q-d11.fort_west and q-d11.fort_east at the halls' fire pits, q-d11.fort_search at Graalg's strongbox (the 2 Energy Disks 12334 in it). Map qbits 110990-110999: none used. Music 13. Neighbours on D2 (installed): the west gate (the map's start) and the east gate (inside point (7552, 32, 0) facing south, explicit coordinates for D2's door).",
}


def fix_sounds(doc):
    """Put the sound numbers of ids.lock.yml into the Lua lines that switch the blaze and the pit sounds."""
    lock = BRIEF / 'L4' / 'ids.lock.yml'
    nums = {}
    if lock.exists():
        L = yaml.safe_load(lock.read_text()) or {}
        nums = L.get('sounds', {}) or {}
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    for k in ('w', 'e'):
        text = text.replace('{blaze_%s}' % k, str(nums.get(f'sound:blaze_{k}', 0)))
        text = text.replace('{pit_%s}' % k, str(nums.get(f'sound:pit_{k}', 0)))
    return text


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
        p['notes'] = f"Xeen design brief, level {lv}: DD-13 Ogre Forts (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-13 Ogre Forts, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

# D-34 (2): the halls' smoke holes open to the Darkside's sky (xeendark1); no daylight block, no weather.
# The preset by its own name: `xeendark1` is sky.yml's alias (a sky texture name) of xeen_darkside_day, and the
# indoor open sky's `preset` takes preset names only (an alias falls back to the clear default sky).
atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_day'},
              'notes': "The two halls' smoke holes (their region:hall_*_sky faces) show the Darkside's day (xeendark1), D2's preset "
                       "(worlds/xeen/rendering/sky/sky.yml); the plank patches close them while the forts stand. No "
                       "daylight block and no weather: the light under the holes is the burned stage's dim map lights."}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', fix_sounds(wiring)),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', atmosphere)])
print('written L4')
