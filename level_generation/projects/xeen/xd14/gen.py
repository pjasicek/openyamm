#!/usr/bin/env python3
"""XD-14 Castle Basenji: writes the L1-L4 project folders of devdocs/xeen/briefs/xd14 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan, project and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd14/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-xd14 (lane A7, phase 4) after DD-13's and XD-07's gen.py.

Frame: x east, y north, z up. The castle's front faces south, onto X6's terrace (the gate's two wings in the gatehouse's south wall are the way out). Four floors:
the dungeon at -512 (cut into the crag east of the kennels), L1 at 0 (gatehouse, great hall, kennels, scriptorium,
kitchen, the two tower feet), L2 at 640 (the two tower landings, the battlement walk over the gate between them, the
cult's wing over the gatehouse: hall of scrolls and dormitory) and L3 at 1280 (the keep's top over the great hall and
the kennels: landing, the Cult Leader's study, the roof walk and the moon tower). Rooms of one floor stand 128 apart
(the walls' thickness); a room over another keeps a slab of at least 96. The stairs are straight flights of 20 steps
of 32 (16 for the dungeon stair). Under open sky (atmosphere.yml, X6's clear preset): the battlement walk, the roof walk
and the moon tower (their ceilings are sky faces)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd14'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# ------------------------------------------------------------------------------------------------ textures
# One family: MM6's Castle Alamos (cd1), dungeon_families castles ("Castle Basenji's kennels and halls"): the grey-green
# block stone d1wcntr in the halls, the small block d1smbw in the towers and the kennels, cd1's beamed ceilings d1ceil1
# dark plank ceilings and furniture d1ceil1, flagstones d2flor5 and d2flor1, the dark dungeon stone d2wlcctr under the rough rock
# d2ceil3; the sun-bleached outer block ctwl5 on the walks under the sky. Doors: MM8's wolf-headed dark double door
# cddl/cddr (the great hall), the plank gate wings ckdl/ckdr, cd1's plank door beemdorc, the stone door with a grille
# d8dorb (the password door), the black-and-gold ctdor4 (the cult's heavy doors), the iron d2lgdor (the dungeon), the
# Xeen cage bars xwcage (the cells). The gate's wings ckdl/ckdr are its exits. Furniture: scroll (the readable scrolls), bookcas1/bookcas2, straw (the beds).
BLOCK = S('d1wcntr', 128, 256)
SMALL = S('d1smbw', 128, 128)
OUTER = S('ctwl5', 256, 256)
DARK = S('d2wlcctr', 256, 256)
ROCK = S('d2ceil3', 256, 256)
FLAGS = S('d2flor5', 128, 128)
FLAGS2 = S('d2flor1', 256, 256)
BEAMS = S('d1ceil1', 256, 256)
PLANKS = S('d1ceil1', 256, 256)
SKY = dict(S('d1ceil1', 256, 256), sky=True)
PLANK_DOOR = S('beemdorc', 128, 256, fit=True)
GRILLE_DOOR = S('d8dorb', 128, 256, fit=True)
CULT_DOOR = S('ctdor4', 128, 256, fit=True)
IRON_DOOR = S('d2lgdor', 256, 256, fit=True)
WOLF_L, WOLF_R = S('cddl', 128, 256), S('cddr', 128, 256)
GATE_L, GATE_R = S('ckdl', 128, 256), S('ckdr', 128, 256)
BARS = S('xwcage', 128, 256)
SCROLL = S('scroll', 64, 64, fit=True)
BOOKS1, BOOKS2 = S('bookcas1', 256, 256), S('bookcas2', 256, 256)
STRAW = S('straw', 256, 256)
POST = S('bemv', 32, 256)
BEAM = S('bemh', 256, 32)

themes = [
    {'id': 'theme:castle', 'wall': BLOCK, 'floor': FLAGS, 'ceiling': BEAMS, 'door': PLANK_DOOR, 'reveal': SMALL,
     'notes': "The keep's halls and rooms (Castle Alamos): grey-green block stone, purple flags, beamed ceilings."},
    {'id': 'theme:tower', 'wall': SMALL, 'floor': FLAGS2, 'ceiling': PLANKS, 'door': PLANK_DOOR, 'reveal': SMALL,
     'notes': "The towers, their stairs and landings, the kennels: the small block, worn flags, plank ceilings."},
    {'id': 'theme:wing', 'wall': BLOCK, 'floor': FLAGS2, 'ceiling': PLANKS, 'door': CULT_DOOR, 'reveal': SMALL,
     'notes': "The cult's wing and the keep's top: block stone, worn flags, plank ceilings."},
    {'id': 'theme:dungeon', 'wall': DARK, 'floor': FLAGS2, 'ceiling': ROCK, 'door': IRON_DOOR, 'reveal': DARK,
     'notes': "The dungeon cut into the crag: dark block stone under rough rock."},
    {'id': 'theme:cave', 'wall': ROCK, 'floor': FLAGS2, 'ceiling': ROCK, 'door': IRON_DOOR, 'reveal': ROCK,
     'notes': "The werewolves' den and the bone pit, dug out of the crag's rock."},
    {'id': 'theme:sky', 'wall': OUTER, 'floor': FLAGS, 'ceiling': SKY, 'door': PLANK_DOOR, 'reveal': OUTER,
     'notes': "The walks and the moon tower under X6's sky: the sun-bleached outer block, the ceiling is sky."},
]

# ------------------------------------------------------------------------------------------------ the plan in numbers
FLOOR = {'dungeon': -512, 'l1': 0, 'l2': 640, 'l3': 1280}
# L1
GATEHOUSE = (-640, -1536, 640, -512)
HALL = (-1408, -384, 1408, 1152)
WEST_FOOT = (-2688, -384, -1536, 384)
WEST_STAIR = (-2560, -1536, -2176, -512)
SCRIPT = (-2944, 512, -1536, 1536)
STORES = (-2944, 1664, -1536, 2688)
KENNELS = (1536, 512, 3456, 2048)
EAST_FOOT = (1536, -384, 2688, 384)
EAST_STAIR = (2176, -1536, 2560, -512)
DSTAIR = (3584, 1024, 4608, 1408)
# dungeon
GUARD = (4736, 768, 5504, 1664)
DEN = (5632, -384, 6912, 1664)
CELLS = (3328, 128, 5504, 640)
CELL = (3456, -640, 4096, 0)
BONES_PIT = (7040, 512, 7808, 1280)
# L2
WLAND = (-2688, -2432, -1536, -1664)
BATTLE = (-1408, -2304, 1408, -1792)
ELAND = (1536, -2432, 2688, -1664)
SCROLLS = (-2048, -1536, -384, -512)
DORM = (-256, -1536, 2048, -512)
KSTAIR = (1536, -384, 1920, 640)
# L3
KLAND = (1280, 768, 2176, 1536)
STUDY = (-128, 768, 1152, 1664)
ROOF = (512, 1792, 2816, 2176)
MOON = (2304, 640, 3200, 1664)

ARRIVAL = (0, -1280)          # 256 inside the gate's leaves (the gatehouse's south wall at y -1536), facing north
PIT_FLOOR = -64

rooms = []
openings = []


def room(id, name, r, floor, ceiling, theme, **kw):
    d = {'id': id, 'name': name, 'outline': rect(*r), 'floor': floor}
    if 'slope' in kw:
        d['slope'] = kw.pop('slope')
    d['ceiling'] = ceiling
    if 'ceiling_slope' in kw:
        d['ceiling_slope'] = kw.pop('ceiling_slope')
    d['theme'] = theme
    d.update(kw)
    rooms.append(d)
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


def panel(pid, r, wall, c, length, bottom, height, surface, notes=None):
    """A panel centred at c along a wall of the rectangle r (x for south/north, y for east/west)."""
    x0, y0, x1, y1 = r
    off = {'south': c - x0, 'east': c - y0, 'north': x1 - c, 'west': y1 - c}[wall] - length // 2
    d = {'id': pid, 'offset': off, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if notes:
        d['notes'] = notes
    return d


def block(pid, x0, y0, x1, y1, rise, surface, top=None, notes=None, base=None, end=None):
    d = {}
    if pid:
        d['id'] = pid
    d['outline'] = rect(x0, y0, x1, y1)
    if base is not None:
        d['base'] = base
    d['rise'] = rise
    d['surface'] = surface
    if end:
        d['end_surface'] = end
    if top:
        d['top_surface'] = top
    if notes:
        d['notes'] = notes
    return d


# ---- scrolls (names on hover; A3's hooks decide for the reading member)
SCRIPT_RACK = ['fire', 'electricity', 'depression', 'confusion', 'insanity', 'weakness']
MOON_RACK = ['energy', 'faded', 'depression', 'confusion', 'death', 'insanity']
PIT_LEDGE = ['death', 'insanity']
LECTERNS = ['intellect', 'personality', 'speed', 'magic', 'aging']
SCROLL_NAME = {'fire': 'Scroll of Fire', 'electricity': 'Scroll of Electricity', 'depression': 'Scroll of Depression',
               'confusion': 'Scroll of Confusion', 'insanity': 'Scroll of Insanity', 'weakness': 'Scroll of Weakness',
               'energy': 'Scroll of Energy', 'faded': 'Scroll of Magic', 'death': 'Scroll of Death',
               'intellect': 'Scroll of Intellect', 'personality': 'Scroll of Personality', 'speed': 'Scroll of Speed',
               'magic': 'Scroll of Magic', 'aging': 'Scroll of Aging'}
SCROLLS_PLACED = []      # (source id, kind, where)


def rack(prefix, r, wall, centre, kinds, step=176, bottom=112):
    out = []
    first = centre - step * (len(kinds) - 1) // 2
    for n, k in enumerate(kinds):
        pid = f'panel:{prefix}_{n + 1}'
        out.append(panel(pid, r, wall, first + n * step, 96, bottom, 128, SCROLL,
                         f"{SCROLL_NAME[k]} pinned to the rack (clicked: A3's q-c8.scroll_{k})."))
        SCROLLS_PLACED.append((pid, k, prefix))
    return out


# ------------------------------------------------------------------------------------------------ L1
room('room:gatehouse', 'Gatehouse', GATEHOUSE, 0, 512, 'theme:castle', ambient=18,
     platforms=[block('platform:bench', -640, -1280, -544, -896, 48, PLANKS, PLANKS,
                      "The guards' bench along the west wall.")],
     notes="Inside the gate, 1,280 by 1,024: the arrival (entrance:x6_gate), quiet; the great hall's double doors north with a sconce either side, a guard bench west.")
# The long tables stand clear of the hall's three side doors (the west arch at y 0, the scriptorium's and the kennels'
# doors at y 832): run across them, 64 high and 64 off the wall, they stopped the party in each doorway like an
# invisible wall and the route planner found no way in (P3 2026-11-24, studio audit `face.in_doorway`).
HALL_TABLES = [block(f'platform:table_{s}', x0, y0, x1, y1, 64, PLANKS, PLANKS, "A long table against the wall.")
               for s, (x0, y0, x1, y1) in (('w', (-1344, 224, -1184, 656)), ('e', (1184, -128, 1344, 656)))]
room('room:great_hall', 'Great hall', HALL, 0, 960, 'theme:castle', ambient=18,
     bands=[{'height': 64, 'surface': SMALL}],
     platforms=[block('platform:hearth', -320, 1040, 320, 1152, 32, SMALL, FLAGS,
                      "The hearth against the north wall; werewolves lie by its fire like dogs.")] + HALL_TABLES,
     pillars=[{'at': [x, y], 'size': [128, 128], 'surface': SMALL}
              for x in (-640, 640) for y in (128, 640)],
     notes="The cult's hall, 2,816 by 1,536 under a beamed ceiling 960 up: four timber posts, long tables against the walls, a hearth north, iron chandeliers; the west tower's arch and the scriptorium's door west, the kennels' door east.")
room('room:west_foot', 'West tower foot', WEST_FOOT, 0, 512, 'theme:tower', ambient=16,
     notes="The foot of the west tower behind its arch off the great hall: the stair up to the west landing goes south.")
room('room:west_stair', 'West tower stair', WEST_STAIR, 0, 448, 'theme:tower', ambient=14,
     slope={'to': 640, 'toward': 'south', 'steps': 20, 'riser': SMALL, 'tread': FLAGS2},
     ceiling_slope={'to': 1088, 'toward': 'south'},
     notes="Twenty steps of 32 up south to the west landing (L2).")
room('room:scriptorium', 'Lower scriptorium', SCRIPT, 0, 512, 'theme:castle', ambient=16,
     walls=[{'wall': 'west', 'panels': rack('script_rack', SCRIPT, 'west', 1024, SCRIPT_RACK)}],
     platforms=[block(f'platform:desk_{n}', x0, y0, x1, y1, 72, PLANKS, PLANKS, "A copying desk.")
                for n, (x0, y0, x1, y1) in enumerate([(-2880, 1376, -2624, 1472), (-1888, 1376, -1632, 1472),
                                                      (-2496, 576, -2240, 672), (-2112, 576, -1856, 672)], 1)],
     notes="Copying desks along the walls and the rack of six scrolls on the west wall (names on hover): Fire, Electricity, Depression, Confusion, Insanity, Weakness.")
room('room:stores', 'Kitchen and stores', STORES, 0, 448, 'theme:tower', ambient=14, store=True,
     platforms=[block('platform:kitchen_table', -2368, 1984, -2112, 2112, 72, PLANKS, PLANKS, "The kitchen table.")],
     notes="A dead end: the cult's kitchen and stores, barrels and sacks in the corners (a storeroom), meat for the kennels; the steward's strongbox.")
# The kennels: three pens along the north wall (cage-bar partitions and fronts with an open gate each), a straw bed in
# each, and the sunken feeding pit in the middle, off the walking lines from the hall's door to the tower and the stair.
PEN_X = [1536, 2112, 2688, 3264]
PEN_Y0 = 1664
PENS = []
for x in PEN_X[1:]:
    PENS.append(block(None, x - 8, PEN_Y0, x + 8, 2048, 256, BARS, SMALL, "A pen's partition of iron bars."))
for n in range(3):
    a, b = PEN_X[n], PEN_X[n + 1]
    PENS.append(block(None, a + (8 if n else 0), PEN_Y0 - 16, a + 192, PEN_Y0, 256, BARS, SMALL, "A pen's front bars."))
    PENS.append(block(None, b - 192, PEN_Y0 - 16, b - 8, PEN_Y0, 256, BARS, SMALL, "A pen's front bars; its gate stands open."))
KENNEL_BEDS = []
for n in range(3):
    cx = (PEN_X[n] + PEN_X[n + 1]) // 2
    KENNEL_BEDS.append(block(f'platform:bed_k{n + 1}', cx - 128, 1856, cx + 128, 2016, 24, PLANKS, STRAW,
                             "A werewolf's straw bed in its pen (clicked: 'Werewolf Bed', a find once)."))
room('room:kennels', 'The kennels', KENNELS, 0, 544, 'theme:tower', ambient=14,
     levels=[{'id': 'level:pit', 'outline': rect(2304, 1216, 2816, 1472), 'floor': PIT_FLOOR, 'bank': 96,
              'edge': FLAGS2, 'surface': STRAW, 'notes': "The sunken feeding pit, its floor in soiled straw."}],
     platforms=PENS + KENNEL_BEDS,
     notes="The set piece, 1,920 by 1,536: three iron pens with open gates along the north wall, a straw bed in each, round a sunken feeding pit; bones and bowls. The hall's door west, the east tower's arch south, the dungeon stair east.")
room('room:east_foot', 'East tower foot', EAST_FOOT, 0, 512, 'theme:tower', ambient=16,
     notes="The foot of the east tower off the kennels: the stair up to the east landing goes south.")
room('room:east_stair', 'East tower stair', EAST_STAIR, 0, 448, 'theme:tower', ambient=14,
     slope={'to': 640, 'toward': 'south', 'steps': 20, 'riser': SMALL, 'tread': FLAGS2},
     ceiling_slope={'to': 1088, 'toward': 'south'},
     notes="Twenty steps of 32 up south to the east landing (L2): the second way up.")
room('room:dungeon_stair', 'Dungeon stair', DSTAIR, 0, 448, 'theme:dungeon', ambient=12,
     slope={'to': -512, 'toward': 'east', 'steps': 16, 'riser': DARK, 'tread': FLAGS2},
     ceiling_slope={'to': -64, 'toward': 'east'},
     notes="Sixteen steps of 32 down east from the kennels' far end to the jailers' room; the smell comes up.")
# ------------------------------------------------------------------------------------------------ the dungeon (-512)
room('room:guard_room', "Jailers' room", GUARD, -512, -96, 'theme:dungeon', ambient=12,
     platforms=[block('platform:jail_table', 4864, 1408, 5120, 1568, 72, PLANKS, PLANKS, "The jailers' table.")],
     notes="The foot of the dungeon stair: a table, the cell lever on the north wall; the den opens east, the cell row's iron door south.")
DEN_BEDS = [block('platform:bed_d1', 6528, 1408, 6784, 1600, 24, ROCK, STRAW,
                  "A straw bed against the den's north wall (clicked: 'Werewolf Bed', a find once)."),
            block('platform:bed_d2', 6592, 128, 6848, 320, 24, ROCK, STRAW,
                  "A straw bed in the den's south-east corner (clicked: 'Straw Bed', a find once).")]
room('room:den', 'Werewolf den', DEN, -512, -96, 'theme:cave', ambient=10, rough={'step': 224, 'depth': 48},
     platforms=DEN_BEDS,
     notes="A cellar dug out into the crag's rock, 1,280 by 1,664: straw beds and bones, the kennels' overflow; the bone pit east.")
CELL_FRONT_N = [panel(f'panel:shut_n{n}', CELLS, 'north', x, 192, 0, 256, IRON_DOOR, "A shut, empty cell's iron door.")
                for n, x in enumerate((3584, 3968, 4352), 1)]
CELL_FRONT_S = [panel(f'panel:shut_s{n}', CELLS, 'south', x, 192, 0, 256, IRON_DOOR, "A shut, empty cell's iron door.")
                for n, x in enumerate((4480, 4864, 5248), 1)]
room('room:cells', 'Cell row', CELLS, -512, -128, 'theme:dungeon', ambient=10,
     walls=[{'wall': 'north', 'panels': CELL_FRONT_N}, {'wall': 'south', 'panels': CELL_FRONT_S}],
     notes="A passage of barred cells, 2,176 long: the empty ones behind their bars, the one that is shut (the peasant's) on the south side at the west end.")
room('room:cell', "The peasant's cell", CELL, -512, -128, 'theme:dungeon', ambient=10,
     platforms=[block('platform:chain_post', 3744, -640, 3808, -592, 160, POST, SMALL,
                      "The post the Trapped Peasant's chain is fixed to (clicked once the bars are up: freed).")],
     notes="A cell behind iron bars: the Trapped Peasant chained to a post (peaceful). The jailers' lever raises the bars.")
room('room:bone_pit', 'Bone pit', BONES_PIT, -512, -128, 'theme:cave', ambient=10,
     walls=[{'wall': 'east', 'panels': rack('pit_ledge', BONES_PIT, 'east', 896, PIT_LEDGE, step=192, bottom=96)}],
     notes="A dead end off the den where the cult throws what the kennels leave: a box under the bones (the chest), two scrolls on a ledge (Death, Insanity).")
# ------------------------------------------------------------------------------------------------ L2 (640)
room('room:west_landing', 'West landing', WLAND, 640, 1184, 'theme:tower', ambient=16,
     notes="The west tower's landing at the stair's head: the battlement door east and, north, the cult's stone door with a grille that asks 'STOP!  What is the password?'")
# D-97 (F21, the user 2026-11-22 here: "I don't see the roof"): the open walks open on their outer sides, sky over a
# parapet (the wall stays solid and draws as sky, as XD-22's moon gallery); 448-high walls on both sides of a 512-wide
# walk read as a corridor whose roof is missing.
PARAPET_H = 160


def sky_side(r, wall):
    """An outer wall drawn as sky over a parapet 32 in from it: (the wall's entry, the parapet)."""
    x0, y0, x1, y1 = r
    path = {'south': [[x0 + 32, y0 + 32], [x1 - 32, y0 + 32]], 'north': [[x0 + 32, y1 - 32], [x1 - 32, y1 - 32]],
            'west': [[x0 + 32, y0 + 32], [x0 + 32, y1 - 32]], 'east': [[x1 - 32, y0 + 32], [x1 - 32, y1 - 32]]}[wall]
    return ({'wall': wall, 'surface': dict(OUTER, sky=True), 'bands': False},
            {'path': path, 'height': PARAPET_H, 'thickness': 32, 'surface': OUTER,
             'notes': f"The {wall} parapet, X6's sky beyond it (D-97)."})


BATTLE_SIDES = [sky_side(BATTLE, 'south')]   # the north side backs onto the cult's wing
room('room:battlements', 'Battlement walk', BATTLE, 640, 1088, 'theme:sky', ambient=30,
     walls=[w for w, _ in BATTLE_SIDES], parapets=[p for _, p in BATTLE_SIDES],
     notes="The walk over the gate between the two towers, open to X6's sky over its south parapet; werewolves on watch.")
room('room:east_landing', 'East landing', ELAND, 640, 1184, 'theme:tower', ambient=16,
     notes="The east tower's landing at the stair's head: the battlement door west, the dormitory's heavy door north (barred from the dormitory's side).")
LECTERN_X = [-1920, -1632, -1344, -1056, -768]
LECTERN_PLATFORMS = [block(f'platform:lectern_{k}', x, -768, x + 96, -672, 104, PLANKS, S('scroll', 64, 64, scale=1.5),
                           f"A lectern with the {SCROLL_NAME[k]} (clicked: A3's q-c8.scroll_{k}).")
                     for x, k in zip(LECTERN_X, LECTERNS)]
for x, k in zip(LECTERN_X, LECTERNS):
    SCROLLS_PLACED.append((f'platform:lectern_{k}', k, 'lectern'))
room('room:scroll_hall', 'Hall of scrolls', SCROLLS, 640, 1184, 'theme:wing', ambient=16,
     walls=[{'wall': 'west', 'panels': [panel('panel:books_w', SCROLLS, 'west', -1024, 768, 0, 384, BOOKS1)]}],
     platforms=LECTERN_PLATFORMS,
     notes="Behind the password door: five lecterns along the north wall with their scrolls (names on hover): Intellect, Personality, Speed, Magic, Aging; shelves on the west wall. The dormitory opens east.")
DORM_BEDS = [block(f'platform:bunk_{n}', x0, y0, x1, y1, 48, PLANKS, STRAW, "A wizard's cot.")
             for n, (x0, y0, x1, y1) in enumerate([(0, -704, 160, -576), (320, -704, 480, -576), (640, -704, 800, -576),
                                                   (0, -1472, 160, -1344), (320, -1472, 480, -1344),
                                                   (640, -1472, 800, -1344)], 1)]
room('room:dormitory', "Wizards' dormitory", DORM, 640, 1184, 'theme:wing', ambient=16,
     platforms=DORM_BEDS,
     notes="Cots and robes, the chest of the wizards' pay; the bar on the door to the east landing (lifted from here: the loop back) and the keep stair north.")
room('room:keep_stair', 'Keep stair', KSTAIR, 640, 1088, 'theme:tower', ambient=14,
     slope={'to': 1280, 'toward': 'north', 'steps': 20, 'riser': SMALL, 'tread': FLAGS2},
     ceiling_slope={'to': 1728, 'toward': 'north'},
     notes="Twenty steps of 32 up north from the dormitory to the keep's top (L3).")
# ------------------------------------------------------------------------------------------------ L3 (1280)
room('room:keep_landing', 'Keep landing', KLAND, 1280, 1792, 'theme:wing', ambient=16,
     notes="The top of the keep stair: the study's door west, the moon tower east.")
room('room:study', "Cult Leader's study", STUDY, 1280, 1792, 'theme:wing', ambient=16,
     walls=[{'wall': 'west', 'panels': [panel('panel:books_s1', STUDY, 'west', 1024, 384, 0, 384, BOOKS1),
                                         panel('panel:books_s2', STUDY, 'west', 1408, 384, 0, 384, BOOKS2)]}],
     platforms=[block('platform:desk', 256, 1088, 512, 1216, 80, PLANKS, PLANKS,
                      "The Cult Leader's desk; his writing box on it holds the Scroll of Insight (chest:desk, D-90)."),
                block('platform:study_hearth', 320, 1600, 704, 1664, 32, SMALL, FLAGS, "The study's hearth.")],
     notes="Books, a hearth, the Cult Leader and his two sorcerers; the Scroll of Insight on the desk, his chest beside it; a second door north to the roof walk.")
ROOF_SIDE = sky_side(ROOF, 'north')
room('room:roof_walk', 'Roof walk', ROOF, 1280, 1728, 'theme:sky', ambient=30,
     walls=[ROOF_SIDE[0]], parapets=[ROOF_SIDE[1]],
     notes="A walk on the keep's leads under open sky from the study's back door to the moon tower, a parapet on its north side.")
MOON_SIDE = sky_side(MOON, 'south')
room('room:moon_tower', 'Moon tower', MOON, 1280, 1792, 'theme:sky', ambient=30,
     walls=[{'wall': 'east', 'panels': rack('moon_rack', MOON, 'east', 1152, MOON_RACK)}, MOON_SIDE[0]],
     parapets=[MOON_SIDE[1]],
     notes="The tower top where the cult calls the moon, open to the sky: the rack of six scrolls on the east wall, a brazier on the floor by the south parapet.")

# ------------------------------------------------------------------------------------------------ openings
op('open:gate_hall', 'room:gatehouse', 'room:great_hall', link='link:gate_hall', width=320, height=384,
   notes="The great hall's double doors (cddl/cddr, the wolf-headed wings).")
op('open:hall_kennels', 'room:great_hall', 'room:kennels', link='link:hall_kennels', width=224, height=320)
op('open:hall_script', 'room:great_hall', 'room:scriptorium', link='link:hall_script', width=224, height=320)
op('open:script_stores', 'room:scriptorium', 'room:stores', link='link:script_stores', width=224, height=320)
op('open:hall_westfoot', 'room:great_hall', 'room:west_foot', link='link:hall_westtower', width=320, height=384,
   notes="The west tower's arch.")
op('open:westfoot_stair', 'room:west_foot', 'room:west_stair', width=320, height=384)
op('open:weststair_landing', 'room:west_stair', 'room:west_landing', link='link:westtower_up', width=320, height=384)
op('open:kennels_eastfoot', 'room:kennels', 'room:east_foot', link='link:kennels_easttower', width=320, height=384,
   notes="The east tower's arch.")
op('open:eastfoot_stair', 'room:east_foot', 'room:east_stair', width=320, height=384)
op('open:eaststair_landing', 'room:east_stair', 'room:east_landing', link='link:easttower_up', width=320, height=384)
op('open:kennels_dstair', 'room:kennels', 'room:dungeon_stair', link='link:kennels_dstair', width=320, height=384)
op('open:dstair_guard', 'room:dungeon_stair', 'room:guard_room', link='link:dstair_down', width=320, height=384)
op('open:guard_den', 'room:guard_room', 'room:den', link='link:guard_den', width=384, height=352)
op('open:guard_cells', 'room:guard_room', 'room:cells', link='link:cells_guard', width=256, height=288,
   notes="The cell row's iron door.")
op('open:cells_den', 'room:cells', 'room:den', link='link:den_cells', width=320, height=352)
op('open:cells_cell', 'room:cells', 'room:cell', link='link:cells_cell', width=256, height=256,
   notes="The bars of the peasant's cell (the jailers' lever raises them).")
op('open:den_bones', 'room:den', 'room:bone_pit', link='link:den_bones', width=320, height=352)
op('open:west_battle', 'room:west_landing', 'room:battlements', link='link:west_battle', width=224, height=320)
op('open:battle_east', 'room:battlements', 'room:east_landing', link='link:battle_east', width=224, height=320)
op('open:password', 'room:west_landing', 'room:scroll_hall', link='link:password_door', width=192, height=320,
   notes="The cult's stone door with a grille (d8dorb): it asks for the password.")
op('open:scroll_dorm', 'room:scroll_hall', 'room:dormitory', link='link:scroll_dorm', width=512, height=416)
op('open:dorm_east', 'room:dormitory', 'room:east_landing', link='link:dorm_east', width=224, height=320,
   notes="The dormitory's heavy door, barred on the dormitory's side.")
op('open:dorm_keep', 'room:dormitory', 'room:keep_stair', link='link:dorm_keep', width=320, height=384)
op('open:keep_up', 'room:keep_stair', 'room:keep_landing', link='link:keep_up', width=320, height=384)
op('open:landing_study', 'room:keep_landing', 'room:study', link='link:landing_study', width=224, height=320)
op('open:study_roof', 'room:study', 'room:roof_walk', link='link:study_roof', width=224, height=320)
op('open:roof_moon', 'room:roof_walk', 'room:moon_tower', link='link:roof_moon', width=320, height=384)
op('open:moon_landing', 'room:moon_tower', 'room:keep_landing', link='link:moon_landing', width=384, height=416)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:castle', 'ambient': 16}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-14 Castle Basenji: the dungeon at -512, L1 at 0, L2 at 640, L3 at 1280; x east, y north, the gate south. Written by output/studio_cal/xd14/tools/gen.py."}

ROOM_RECT = {r['id']: (r['outline'][0][0], r['outline'][0][1], r['outline'][2][0], r['outline'][2][1]) for r in rooms}
ROOM_FLOOR = {r['id']: r['floor'] for r in rooms}

# ================================================================================================ monsters
ACOLYTE, WEREWOLF, GREATER, WIZARD, SORCERER, LEADER, PEASANT = 11197, 11421, 11422, 11190, 11191, 11198, 11233
LEVEL = {ACOLYTE: 24, WEREWOLF: 30, GREATER: 40, WIZARD: 36, SORCERER: 45, LEADER: 45, PEASANT: 4}
NAME = {ACOLYTE: 'Cult Acolyte', WEREWOLF: 'Werewolf', GREATER: 'Greater Werewolf', WIZARD: 'Wizard',
        SORCERER: 'Sorcerer', LEADER: 'Basenji Cult Leader', PEASANT: 'Trapped Peasant'}
# (room, group, [(monster, at, facing)])
PLACED = [
    ('room:great_hall', 10, [(WEREWOLF, [-420, 880], 270), (WEREWOLF, [420, 900], 270),
                             (ACOLYTE, [-700, 300], 90), (ACOLYTE, [760, 420], 180)]),
    ('room:kennels', 11, [(WEREWOLF, [1824, 1760], 270), (WEREWOLF, [2400, 1800], 270), (WEREWOLF, [2976, 1760], 270),
                          (WEREWOLF, [2560, 1100], 180), (WEREWOLF, [3200, 800], 180), (GREATER, [2000, 1350], 0)]),
    ('room:scriptorium', 12, [(ACOLYTE, [-2368, 1250], 270), (ACOLYTE, [-1984, 1250], 270), (ACOLYTE, [-2200, 820], 90)]),
    ('room:stores', 13, [(ACOLYTE, [-2240, 1840], 90), (ACOLYTE, [-1900, 2250], 270)]),
    ('room:guard_room', 14, [(ACOLYTE, [5000, 1250], 180), (ACOLYTE, [5300, 1000], 180)]),
    ('room:den', 15, [(WEREWOLF, [6000, 1300], 180), (WEREWOLF, [6400, 900], 180), (WEREWOLF, [6100, 500], 180),
                      (WEREWOLF, [6700, 700], 180)]),
    ('room:cells', 16, [(WEREWOLF, [3700, 384], 270), (WEREWOLF, [4000, 384], 270)]),
    ('room:bone_pit', 17, [(WEREWOLF, [7424, 1000], 180)]),
    ('room:west_landing', 18, [(WEREWOLF, [-2300, -2150], 0), (WEREWOLF, [-1900, -2250], 90)]),
    ('room:battlements', 19, [(WEREWOLF, [-500, -2048], 0), (WEREWOLF, [500, -2048], 180), (GREATER, [0, -2100], 270)]),
    ('room:east_landing', 20, [(ACOLYTE, [1900, -2150], 180), (ACOLYTE, [2300, -2250], 90)]),
    ('room:scroll_hall', 21, [(WIZARD, [-1400, -1100], 270), (WIZARD, [-900, -1250], 270),
                              (ACOLYTE, [-1700, -1350], 90), (ACOLYTE, [-700, -900], 180)]),
    ('room:dormitory', 22, [(WIZARD, [1200, -1000], 180), (WIZARD, [1700, -800], 180),
                            (ACOLYTE, [300, -1000], 0), (ACOLYTE, [900, -1250], 90), (ACOLYTE, [1500, -1300], 90)]),
    ('room:keep_landing', 23, [(WIZARD, [1728, 1300], 270)]),
    ('room:study', 24, [(LEADER, [384, 1400], 270), (SORCERER, [100, 1000], 0), (SORCERER, [900, 1450], 180)]),
    ('room:moon_tower', 25, [(WIZARD, [2750, 1150], 180)]),
]
PEASANT_GROUP = 30
LEADER_GROUP = 24
monsters = []
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        monsters.append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                         'floor_height': ROOM_FLOOR[room_id], 'facing': facing, 'group': group})
monsters.append({'id': 'monster:peasant', 'room': 'room:cell', 'monster': PEASANT, 'at': [3776, -460],
                 'floor_height': -512, 'facing': 90, 'group': PEASANT_GROUP, 'immobile': True,
                 'notes': "The Trapped Peasant (11233, peaceful by the world's relation basenji_prisoner): talks through the bars (q-c8.peasant); freed once the lever has raised them (q-c8.peasant_freed), hidden from then on."})
COUNT = {}
for _, _, ms in PLACED:
    for mon, _, _ in ms:
        COUNT[mon] = COUNT.get(mon, 0) + 1
assert COUNT == {ACOLYTE: 16, WEREWOLF: 18, GREATER: 2, WIZARD: 6, SORCERER: 2, LEADER: 1}, COUNT
KILL_XP = sum(LEVEL[m] * (LEVEL[m] + 10) * n for m, n in COUNT.items())

# ================================================================================================ objects.yml
QBITS = {'password': 112161, 'scroll_found': 112162, 'peasant_freed': 112164,
         'dorm_bar': 118000, 'cell_lever': 118001}

decorations = []
lights = []


def deco(key, room_id, name, at, **kw):
    d = {'id': f'deco:{key}', 'room': room_id, 'decoration': name, 'at': at}
    if 'floor_height' not in kw and ROOM_FLOOR.get(room_id) is not None:
        kw['floor_height'] = ROOM_FLOOR[room_id]
    d.update(kw)
    decorations.append(d)
    return d


def light(key, room_id, at, height, radius, color, **kw):
    d = {'id': f'light:{key}', 'room': room_id, 'at': at, 'floor_height': ROOM_FLOOR[room_id], 'height': height,
         'radius': radius, 'color': color}
    d.update(kw)
    lights.append(d)


def torch(key, room_id, wall, c, floor=None):
    """A wall torch (torch01 in its bracket 160 up) and its light 24 in front of the flame. c: x on a south or north wall,
    y on an east or west one."""
    x0, y0, x1, y1 = ROOM_RECT[room_id]
    at = {'south': [c, y0], 'north': [c, y1], 'east': [x1, c], 'west': [x0, c]}[wall]
    nx, ny = {'north': (0, -24), 'south': (0, 24), 'east': (-24, 0), 'west': (24, 0)}[wall]
    fl = ROOM_FLOOR[room_id] if floor is None else floor
    deco(f'torch_{key}', room_id, 'torch01', at, wall=wall, height=160, floor_height=fl)
    lights.append({'id': f'light:torch_{key}', 'room': room_id, 'at': [at[0] + nx, at[1] + ny], 'floor_height': fl,
                   'height': 184, 'radius': 900, 'color': [255, 170, 90], 'notes': "The wall torch's flame."})


def sconce(key, room_id, wall, c):
    x0, y0, x1, y1 = ROOM_RECT[room_id]
    at = {'south': [c, y0], 'north': [c, y1], 'east': [x1, c], 'west': [x0, c]}[wall]
    nx, ny = {'north': (0, -24), 'south': (0, 24), 'east': (-24, 0), 'west': (24, 0)}[wall]
    deco(f'sconce_{key}', room_id, 'scon100', at, wall=wall, height=200)
    lights.append({'id': f'light:sconce_{key}', 'room': room_id, 'at': [at[0] + nx, at[1] + ny],
                   'floor_height': ROOM_FLOOR[room_id], 'height': 230, 'radius': 800, 'color': [255, 180, 110],
                   'notes': "A wall sconce's candles."})


# Torches and sconces on the walls (each clear of the room's openings).
sconce('gate_w', 'room:gatehouse', 'north', -320)
sconce('gate_e', 'room:gatehouse', 'north', 320)
torch('gate_e', 'room:gatehouse', 'east', -1024)
torch('gate_w', 'room:gatehouse', 'west', -700)
torch('hall_s1', 'room:great_hall', 'south', -900)
torch('hall_s2', 'room:great_hall', 'south', 900)
torch('hall_n1', 'room:great_hall', 'north', -900)
torch('hall_n2', 'room:great_hall', 'north', 900)
torch('westfoot', 'room:west_foot', 'west', 0)
torch('script_e', 'room:scriptorium', 'east', 1300)
torch('script_s', 'room:scriptorium', 'south', -2600)
torch('stores', 'room:stores', 'east', 2200)
torch('kennels_s', 'room:kennels', 'south', 3000)
torch('kennels_w', 'room:kennels', 'west', 1400)
torch('kennels_e', 'room:kennels', 'east', 700)
torch('eastfoot', 'room:east_foot', 'east', 0)
torch('guard_w', 'room:guard_room', 'west', 1550)
torch('cells_w', 'room:cells', 'west', 384)
torch('cells_n', 'room:cells', 'north', 4800)
torch('cell', 'room:cell', 'east', -320)
torch('bones', 'room:bone_pit', 'north', 7424)
torch('wland', 'room:west_landing', 'west', -2048)
torch('eland', 'room:east_landing', 'east', -2048)
torch('scroll_s', 'room:scroll_hall', 'south', -1100)
torch('dorm_n', 'room:dormitory', 'north', 600)
torch('dorm_s', 'room:dormitory', 'south', 900)
torch('kland', 'room:keep_landing', 'north', 1728)
torch('study_e', 'room:study', 'east', 1600)
torch('study_s', 'room:study', 'south', 0)

# Chandeliers in the great hall (iron rings of candles hung from the beams) with their lights 120 under the ceiling.
for n, (x, y) in enumerate([(-640, 384), (640, 384)], 1):
    deco(f'chandelier_{n}', 'room:great_hall', 'dec27', [x, y], hangs=True)
    light(f'chandelier_{n}', 'room:great_hall', [x, y], 780, 1400, [255, 200, 140],
          notes="A chandelier's candles, hung from the beams.")
# Fires: the hall's hearth and the study's, the moon tower's brazier on its feet by the parapet.
deco('hearth_fire', 'room:great_hall', 'ckfyr00', [0, 1096], floor_height=32)
light('hearth', 'room:great_hall', [0, 1080], 96, 1500, [255, 150, 70], floor_height=32,
      pulse={'intensity': [0.8, 1], 'frequency': 0.8}, notes="The hearth's fire.")
deco('study_fire', 'room:study', 'ckfyr00', [502, 1606], floor_height=1312)
light('study_fire', 'room:study', [512, 1620], 96, 1100, [255, 150, 70], floor_height=1312,
      pulse={'intensity': [0.8, 1], 'frequency': 0.8}, notes="The study's fire.")
deco('den_brazier', 'room:den', 'flamb00', [6240, 1480])
light('den_brazier', 'room:den', [6240, 1480], 150, 1300, [255, 150, 70],
      pulse={'intensity': [0.8, 1], 'frequency': 1.1}, notes="A brazier on its feet by the den's north wall.")
deco('moon_brazier', 'room:moon_tower', 'flamb00', [2752, 768])
light('moon_brazier', 'room:moon_tower', [2752, 768], 150, 1000, [255, 160, 80],
      pulse={'intensity': [0.8, 1], 'frequency': 1.1}, notes="The brazier's fire by the moon tower's south parapet.")
# Daylight in the rooms open to the sky and at the gate.
DAY = [210, 205, 190]
light('day_battle', 'room:battlements', [0, -2048], 400, 1800, DAY, notes="The sky over the battlement walk.")
light('day_roof', 'room:roof_walk', [1664, 1984], 400, 1500, DAY, notes="The sky over the roof walk.")
light('day_moon', 'room:moon_tower', [2752, 1152], 460, 1300, DAY, notes="The sky over the moon tower.")
# Candles on the scriptorium's desks and the study's desk.
for n, (x, y) in enumerate([(-2752, 1424), (-1984, 624)], 1):
    deco(f'desk_candle_{n}', 'room:scriptorium', 'dec02', [x, y], floor_height=72)
deco('study_candle', 'room:study', 'dec02', [288, 1152], floor_height=1360)

# Dressing (D-7): containers by the walls in singles and pairs; the kitchen is a storeroom (clumps there).
D = deco
D('hall_bones_1', 'room:great_hall', '7dec18', [-560, 1000])
D('hall_bones_2', 'room:great_hall', 'dec29', [520, 1010])
D('hall_plates_w1', 'room:great_hall', 'dec37', [-1264, 320], floor_height=64)
D('hall_plates_w2', 'room:great_hall', 'dec39', [-1264, 560], floor_height=64)
D('hall_plates_e1', 'room:great_hall', 'dec36', [1264, 240], floor_height=64)
D('hall_goblet_e', 'room:great_hall', '7dec46', [1264, 560], floor_height=64)
D('gate_barrel_1', 'room:gatehouse', 'smlbarel', [520, -1400])
D('gate_barrel_2', 'room:gatehouse', 'smlbarel', [520, -1280])
D('kennel_bowl_1', 'room:kennels', 'foodbowl', [2200, 1980])
D('kennel_bowl_2', 'room:kennels', 'foodbowl', [3350, 1980])
D('kennel_bones_1', 'room:kennels', '7dec18', [2560, 1344], floor_height=PIT_FLOOR)
D('kennel_bones_2', 'room:kennels', 'dec29', [2700, 1300], floor_height=PIT_FLOOR)
D('kennel_bones_3', 'room:kennels', 'dec19', [1600, 1760])
D('kennel_skull', 'room:kennels', '7dec20', [3380, 1720])
D('stores_barrel_1', 'room:stores', 'bigbarel', [-2840, 2330])
D('stores_barrel_2', 'room:stores', 'bigbarel', [-2740, 2330])
D('stores_barrel_3', 'room:stores', 'bigbarel', [-2840, 2230])
D('stores_barrel_4', 'room:stores', 'smlbarel', [-1640, 2330])
D('stores_barrel_5', 'room:stores', 'smlbarel', [-1740, 2330])
D('stores_sack_1', 'room:stores', 'floursac', [-2840, 1780])
D('stores_sack_2', 'room:stores', 'bag01', [-2840, 1900])
D('stores_sack_3', 'room:stores', 'bag_a', [-2730, 1770])
D('stores_meat', 'room:stores', 'trasheap', [-1660, 1780])
D('stores_bowl', 'room:stores', '7dec08', [-2240, 2048], floor_height=72)
D('guard_goblet', 'room:guard_room', '7dec46', [4992, 1488], floor_height=-440)
D('guard_bucket', 'room:guard_room', 'bucket', [5420, 1580])
D('den_bones_1', 'room:den', '7dec18', [5900, 1500])
D('den_bones_2', 'room:den', 'dec19', [5800, 200])
D('den_trash', 'room:den', 'trasheap', [6300, 130])
D('cell_bucket', 'room:cell', 'bucket', [3540, -560])
D('pit_bones_1', 'room:bone_pit', 'sklplrev', [7600, 640])
D('pit_bones_2', 'room:bone_pit', '7dec18', [7250, 1150])
D('pit_bones_3', 'room:bone_pit', 'dec29', [7650, 1150])
D('dorm_barrel_1', 'room:dormitory', 'smlbarel', [1950, -1060])
D('dorm_barrel_2', 'room:dormitory', 'smlbarel', [1950, -1180])
D('moon_skull', 'room:moon_tower', '7dec20', [3100, 760])

sounds = [
    {'id': 'sound:hearth', 'room': 'room:great_hall', 'at': [0, 1080], 'floor_height': 32, 'sound': 'campfire',
     'radius': 1800, 'inner_radius': 500, 'volume': 0.6, 'notes': "The hall's hearth."},
    {'id': 'sound:study_fire', 'room': 'room:study', 'at': [512, 1620], 'floor_height': 1312, 'sound': 'campfire',
     'radius': 1200, 'inner_radius': 400, 'volume': 0.5, 'notes': "The study's fire."},
    {'id': 'sound:wind_battle', 'room': 'room:battlements', 'at': [0, -2048], 'floor_height': 640,
     'sound': 'whistling wind', 'radius': 1800, 'inner_radius': 600, 'volume': 0.45, 'notes': "Wind over the walk."},
    {'id': 'sound:wind_moon', 'room': 'room:moon_tower', 'at': [2752, 1152], 'floor_height': 1280,
     'sound': 'whistling wind', 'radius': 1600, 'inner_radius': 500, 'volume': 0.45, 'notes': "Wind on the tower top."},
    {'id': 'sound:drip', 'room': 'room:cells', 'at': [4400, 384], 'floor_height': -512, 'sound': 'drip01',
     'radius': 1400, 'inner_radius': 400, 'volume': 0.5, 'loop': False, 'wait': [3, 8],
     'notes': "Water through the crag into the cell row."},
    {'id': 'sound:drip_den', 'room': 'room:den', 'at': [6272, 832], 'floor_height': -512, 'sound': 'drip01',
     'radius': 1400, 'inner_radius': 400, 'volume': 0.5, 'loop': False, 'wait': [4, 10],
     'notes': "Water down the den's rock."},
]


def leaves(id, opening, left, right, notes):
    return {'id': id, 'opening': opening, 'kind': 'slide_left', 'leaves': 2, 'thickness': 24, 'speed': 160,
            'pictures': [[left, right]], 'back_pictures': [[left, right]], 'edge_surface': POST, 'notes': notes}


def single(id, opening, picture, notes, back=None):
    return {'id': id, 'opening': opening, 'kind': 'hinged', 'thickness': 24, 'surface': picture,
            'back_surface': back or picture, 'edge_surface': POST, 'notes': notes}


doors = [
    leaves('door:hall_doors', 'open:gate_hall', WOLF_L, WOLF_R,
           "The great hall's double doors: dark iron-bound wings with carved wolves' heads (MM8's cddl/cddr)."),
    single('door:kennels', 'open:hall_kennels', PLANK_DOOR, "The kennels' plank door."),
    single('door:scriptorium', 'open:hall_script', PLANK_DOOR, "The scriptorium's plank door."),
    single('door:stores', 'open:script_stores', PLANK_DOOR, "The kitchen's plank door."),
    single('door:battle_w', 'open:west_battle', PLANK_DOOR, "The west tower's door onto the battlement walk."),
    single('door:battle_e', 'open:battle_east', PLANK_DOOR, "The east tower's door onto the battlement walk."),
    single('door:password', 'open:password', GRILLE_DOOR,
           "The cult's stone door with a grille (d8dorb): 'STOP!  What is the password?'"),
    single('door:dorm_bar', 'open:dorm_east', CULT_DOOR,
           "The dormitory's heavy door, barred on the dormitory's side (lifted from there: the loop back)."),
    single('door:study', 'open:landing_study', CULT_DOOR, "The Cult Leader's study door."),
    single('door:study_roof', 'open:study_roof', PLANK_DOOR, "The study's back door onto the roof walk."),
    {'id': 'door:cells', 'opening': 'open:guard_cells', 'kind': 'slide_up', 'thickness': 24, 'speed': 160,
     'surface': IRON_DOOR, 'notes': "The cell row's iron door."},
    {'id': 'door:cell_bars', 'opening': 'open:cells_cell', 'kind': 'slide_up', 'thickness': 16, 'speed': 64,
     'surface': BARS, 'tile': True,
     'notes': "The bars of the peasant's cell (Xeen's cage bars): raised by the jailers' lever."},
]

chests = [
    {'id': 'chest:stores', 'room': 'room:stores', 'at': [-1660, 2000], 'floor_height': 0, 'facing': 'w', 'kind': 'ch1',
     'treasure_level': 4, 'random_items': 2, 'gold': 900, 'notes': "The steward's strongbox in the kitchen."},
    {'id': 'chest:bone_pit', 'room': 'room:bone_pit', 'at': [7200, 640], 'floor_height': -512, 'facing': 'e',
     'kind': 'ch1', 'treasure_level': 4, 'random_items': 3, 'gold': 600, 'notes': "The box under the bones."},
    {'id': 'chest:dormitory', 'room': 'room:dormitory', 'at': [-216, -576], 'floor_height': 640, 'kind': 'ch1', 'treasure_level': 4, 'random_items': 2, 'gold': 1500, 'notes': "The chest of the wizards' pay."},
    {'id': 'chest:study', 'room': 'room:study', 'at': [640, 1152], 'floor_height': 1280, 'facing': 's',
     'kind': 'ch1', 'treasure_level': 4, 'random_items': 4, 'gold': 2500,
     'notes': "The Cult Leader's chest beside his desk."},
    {'id': 'chest:desk', 'room': 'room:study', 'at': [384, 1152], 'floor_height': 1280 + 80, 'facing': 'w',
     'kind': 'gt002', 'random_items': 0, 'gold': 0, 'items': ['scroll_of_insight'],
     'notes': "The Cult Leader's writing box on his desk, its front to the room (south): the Scroll of Insight is its "
              "item (D-90, 2026-11-22: a find in a container is a chest item; A3's q-c8.scroll sets scroll_found)."},
]

switches = [
    {'id': 'switch:cell_lever', 'room': 'room:guard_room', 'kind': 'lever',
     'at': [5376, 1664], 'floor_height': -512, 'notes': "The jailers' lever: it raises the bars of the shut cell."},
]

objects = {
    'format': 0,
    'start': {'room': 'room:gatehouse', 'at': list(ARRIVAL), 'facing': 'n',
              'notes': "Inside the gate (X6's door, entrance:x6_gate): 256 inside the leaves, facing the great hall's doors."},
    'arrivals': [{'entrance': 'entrance:x6_gate', 'room': 'room:gatehouse', 'at': list(ARRIVAL), 'facing': 'n',
                  'notes': "From X6's Castle Basenji door (thing:castle_basenji): in the gatehouse 256 inside the gate's leaves, facing north to the great hall's double doors."}],
    'doors': doors,
    'switches': switches,
    'chests': chests,
    'monsters': monsters,
    'decorations': decorations,
    'lights': lights,
    'sounds': sounds,
    'exits': [
        # The castle gate in the gatehouse's south wall: two wings, each its own picture (MM7's ckdl/ckdr, a mirrored
        # pair; seen from inside facing south the left wing is east), each a way out to X6's terrace.
        {'id': 'exit:gate_left', 'room': 'room:gatehouse', 'at': [96, -1536], 'size': [192, 352],
         'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x6_gate',
         'notes': "The gate's left wing (seen from inside): out to X6's terrace in front of the gatehouse."},
        {'id': 'exit:gate_right', 'room': 'room:gatehouse', 'at': [-96, -1536], 'size': [192, 352],
         'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x6_gate',
         'notes': "The gate's right wing (seen from inside): out to X6's terrace in front of the gatehouse."},
    ],
}

# ================================================================================================ wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


BEDS = [('platform:bed_k1', 'Werewolf Bed', 150), ('platform:bed_k2', 'Werewolf Bed', 220),
        ('platform:bed_k3', 'Werewolf Bed', 180), ('platform:bed_d1', 'Werewolf Bed', 260),
        ('platform:bed_d2', 'Straw Bed', 120)]
events = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'effects': [{'message': "Castle Basenji: the wizard cult's keep on its crag over the rim. Somewhere above is Arie's master's Scroll of Insight; somewhere below, the dogs that are not dogs. The gate is the way back out."}],
     'notes': "Why the party is here (Q-C8), once, on the first arrival."},
    {'id': 'evt:exit_left', 'preset': 'exit', 'source': 'exit:gate_left', 'title': 'Gate',
     'notes': "The gate's left wing: out to X6 as evt:exit_right."},
    {'id': 'evt:exit_right', 'preset': 'exit', 'source': 'exit:gate_right', 'title': 'Gate',
     'notes': "Out to X6 on the terrace in front of the gatehouse (-13312, 15104, 2592) facing south; the game's leave window (D-24; 'Leave Castle Basenji?', aaze0068:14, is its meaning)."},
    {'id': 'evt:door_hall', 'preset': 'door', 'source': 'door:hall_doors', 'title': 'Great hall'},
    {'id': 'evt:door_kennels', 'preset': 'door', 'source': 'door:kennels', 'title': 'Kennels'},
    {'id': 'evt:door_scriptorium', 'preset': 'door', 'source': 'door:scriptorium', 'title': 'Scriptorium'},
    {'id': 'evt:door_stores', 'preset': 'door', 'source': 'door:stores', 'title': 'Kitchen'},
    {'id': 'evt:door_battle_w', 'preset': 'door', 'source': 'door:battle_w', 'title': 'Battlements'},
    {'id': 'evt:door_battle_e', 'preset': 'door', 'source': 'door:battle_e', 'title': 'Battlements'},
    {'id': 'evt:door_study', 'preset': 'door', 'source': 'door:study', 'title': 'Study'},
    {'id': 'evt:door_study_roof', 'preset': 'door', 'source': 'door:study_roof', 'title': 'Roof walk'},
    {'id': 'evt:door_cells', 'preset': 'door', 'source': 'door:cells', 'title': 'Cell row'},
    # The password door (D-39 XD-14; graph state:password): the question from the landing; open for good once answered.
    {'id': 'evt:password', 'preset': 'script', 'source': 'door:password', 'side': 'room:west_landing',
     'title': 'Door', 'condition': {'not': {'qbit': 'password'}},
     'question': {'message': "STOP!  What is the password?", 'ask': 'Password:',
                  'answers': ['There wolf', 'therewolf', 'There-wolf'],
                  'wrong_effects': [hook('q-c8.l2_wrong')]},
     'opens': ['door:password'], 'effects': [hook('q-c8.l2_door')],
     'else_effects': [hook('q-c8.l2_door')],
     'notes': "state:password: the source's prompt (aaze0069:10). 'There wolf' or 'therewolf' (aaze0069:8, :16): A3's q-c8.l2_door (password 112161), the door opens and stays open; any other answer q-c8.l2_wrong (its first word the source's 'Wrong!', aaze0069:9), and the next click asks again. Once answered: the hook's else line, 'The door stands open.'"},
    {'id': 'evt:password_in', 'preset': 'door', 'source': 'door:password', 'side': 'room:scroll_hall', 'title': 'Door',
     'action': 'open', 'notes': "From the hall of scrolls the door simply opens."},
    # The dormitory's barred door (D-39 XD-14 Q5).
    {'id': 'evt:dorm_landing', 'preset': 'door', 'source': 'door:dorm_bar', 'side': 'room:east_landing',
     'title': 'Door', 'action': 'open', 'condition': {'qbit': 'dorm_bar'},
     'locked_text': "The door is barred from the other side.",
     'notes': "From the east landing: barred until the bar is lifted in the dormitory (dorm_bar 118000)."},
    {'id': 'evt:dorm_inside', 'preset': 'door', 'source': 'door:dorm_bar', 'side': 'room:dormitory', 'title': 'Door',
     'action': 'open', 'sets': {'qbit': 'dorm_bar'},
     'text': "You lift the heavy bar out of its brackets, and the door swings open onto the east landing.",
     'notes': "From the dormitory: the bar lifted, the door opens and stays open (the wing's loop back)."},
    # The dungeon: the jailers' lever, the peasant's bars, his chain.
    {'id': 'evt:cell_lever', 'preset': 'switch', 'source': 'switch:cell_lever', 'title': 'Lever',
     'condition': {'not': {'qbit': 'cell_lever'}}, 'opens': ['door:cell_bars'], 'sets': {'qbit': 'cell_lever'},
     'text': "The lever creaks down. Out in the cell row, bars grind up into the ceiling.",
     'else_effects': [{'text': "The lever is down. The shut cell stands open."}],
     'notes': "state:cell_lever (cell_lever 118001): raises the bars of the peasant's cell for good."},
    {'id': 'evt:bars', 'preset': 'script', 'source': 'door:cell_bars', 'side': 'room:cells', 'title': 'Trapped Peasant',
     'effects': [hook('q-c8.peasant')],
     'notes': "The Trapped Peasant talks through the bars at any time (A3's q-c8.peasant: 'There wolf', and the Sphinx is Golux)."},
    {'id': 'evt:free_peasant', 'preset': 'script', 'source': 'platform:chain_post', 'title': 'Trapped Peasant',
     'condition': {'qbit': 'cell_lever', 'not': {'qbit': 'peasant_freed'}},
     'effects': [hook('q-c8.peasant_freed'), {'hide_actors': PEASANT_GROUP}],
     'else_effects': [{'text': "An empty chain hangs from the post."}],
     'notes': "state:freed: once the lever has raised the bars, a click on his chain frees him (A3's q-c8.peasant_freed: 'Thank you for saving me!', 500 experience per member, peasant_freed 112164) and he is gone (group 30 hidden)."},
    {'id': 'evt:stage_peasant', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'peasant_freed'},
     'effects': [{'hide_actors': PEASANT_GROUP}],
     'notes': "The freed peasant stays gone on every later load (D-39 XD-14 Q4)."},
    {'id': 'evt:stage_doors', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'password'},
     'lua': '-- the event opens the door', 'opens': ['door:password'], 'notes': "The password door stays open once answered."},
    {'id': 'evt:stage_bar', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'dorm_bar'},
     'lua': '-- the event opens the door', 'opens': ['door:dorm_bar'], 'notes': "The dormitory's door stays open once its bar is lifted."},
    {'id': 'evt:stage_lever', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'cell_lever'},
     'lua': '-- the event opens the door', 'opens': ['door:cell_bars'], 'notes': "The shut cell stays open once the lever is down."},
    # The Scroll of Insight (q-c8.scroll) and the chests.
    {'id': 'evt:desk', 'preset': 'chest', 'source': 'chest:desk', 'title': 'Chest',
     'effects': [hook('q-c8.scroll')],
     'notes': "The writing box on the desk (D-90): the Scroll of Insight (12316) is its item; A3's q-c8.scroll (once) "
              "sets scroll_found 112162 and says so on the status line."},
    {'id': 'evt:chest_stores', 'preset': 'chest', 'source': 'chest:stores', 'title': 'Chest'},
    {'id': 'evt:chest_bone_pit', 'preset': 'chest', 'source': 'chest:bone_pit', 'title': 'Box'},
    {'id': 'evt:chest_dormitory', 'preset': 'chest', 'source': 'chest:dormitory', 'title': 'Chest'},
    {'id': 'evt:chest_study', 'preset': 'chest', 'source': 'chest:study', 'title': 'Chest'},
    # Step lines (once).
    {'id': 'evt:kennels_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:kennels', 'once': True,
     'text': "The kennels: iron pens round a feeding pit, the straw soiled. What sleeps here is not a dog.", 'seconds': 6},
    {'id': 'evt:dungeon_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:guard_room', 'once': True,
     'text': "The jailers' room. Somewhere along the cells a chain rattles, and someone coughs.", 'seconds': 6},
    {'id': 'evt:battle_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:battlements', 'once': True,
     'text': "The battlement walk over the gate: the desert lies white under the sun below the crag.", 'seconds': 6},
]
for pid, title, gold in BEDS:
    var = 'find_' + pid.split('_')[-1]
    events.append({'id': f'evt:{pid.split(":")[1]}', 'preset': 'script', 'source': pid, 'title': title,
                   'condition': {'map_var': {'name': var, 'equals': 0}},
                   'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}, {'gold': gold},
                               {'text': f"Under the straw: {gold} gold."}],
                   'else_effects': [{'text': "Nothing here."}],
                   'notes': f"The source's '{title}' (aaze0067:0-1, aaze0068:0-1): a find once, then 'Nothing here.' (aaze0067:10)."})
for pid, kind, where in SCROLLS_PLACED:
    events.append({'id': f'evt:{pid.split(":")[1]}', 'preset': 'script', 'source': pid, 'title': SCROLL_NAME[kind],
                   'effects': [hook(f'q-c8.scroll_{kind}')],
                   'notes': f"A3's q-c8.scroll_{kind} (D-39 XD-14 Q3: blessings once per character, curses on the reading member)."})
VARIABLES = sorted({'find_' + pid.split('_')[-1] for pid, _, _ in BEDS})
wiring = {'format': 0, 'variables': VARIABLES, 'events': events}

# ================================================================================================ plan.yml
# (id, kind, size, purpose, population [(monster, count)], chest tier)
PLAN_SPACES = [
    ('room:gatehouse', 'room', 'M', "The arrival (entrance:x6_gate), quiet (D-11.3): a guard bench, two sconces either side of the great hall's double doors.", [], None),
    ('room:great_hall', 'room', 'L', "The cult's hall behind wolf-headed double doors: long tables, a hearth with werewolves lying by it like dogs, chandeliers.", [(WEREWOLF, 2), (ACOLYTE, 2)], None),
    ('room:kennels', 'room', 'L', "The set piece: iron pens with open gates round a sunken feeding pit, straw beds ('Werewolf Bed', a find each); the dungeon stair east.", [(WEREWOLF, 5), (GREATER, 1)], None),
    ('room:scriptorium', 'room', 'M', "Copying desks and the rack of six scrolls (Fire, Electricity: blessings; Depression, Confusion, Insanity, Weakness: curses).", [(ACOLYTE, 3)], None),
    ('room:stores', 'room', 'M', "A dead end: the kitchen and stores (a storeroom), the steward's strongbox.", [(ACOLYTE, 2)], 4),
    ('room:west_foot', 'room', 'S', "The west tower's foot off the great hall.", [], None),
    ('room:west_stair', 'stair', 'S', "Twenty steps up to the west landing.", [], None),
    ('room:east_foot', 'room', 'S', "The east tower's foot off the kennels.", [], None),
    ('room:east_stair', 'stair', 'S', "Twenty steps up to the east landing (the second way up).", [], None),
    ('room:dungeon_stair', 'stair', 'S', "Down from the kennels' far end to the jailers' room.", [], None),
    ('room:guard_room', 'room', 'M', "A table and the cell lever (it raises the bars of the peasant's cell).", [(ACOLYTE, 2)], None),
    ('room:den', 'room', 'M', "A cellar dug into the crag: straw beds ('Werewolf Bed', 'Straw Bed') and bones.", [(WEREWOLF, 4)], None),
    ('room:cells', 'corridor', 'M', "A passage of barred cells; two werewolves watch the shut one.", [(WEREWOLF, 2)], None),
    ('room:cell', 'room', 'S', "The Trapped Peasant in a chain: he talks through the bars (q-c8.peasant); freed after the lever (q-c8.peasant_freed).", [], None),
    ('room:bone_pit', 'room', 'S', "A dead end: a box under the bones (chest), the scrolls of Death and Insanity on a ledge.", [(WEREWOLF, 1)], 4),
    ('room:west_landing', 'room', 'M', "The west tower's landing: the battlement door, and the cult's door that asks 'STOP!  What is the password?'", [(WEREWOLF, 2)], None),
    ('room:battlements', 'corridor', 'L', "The walk over the gate between the towers, open to the sky.", [(WEREWOLF, 2), (GREATER, 1)], None),
    ('room:east_landing', 'room', 'M', "The east tower's landing; the dormitory's heavy door, barred from the dormitory's side.", [(ACOLYTE, 2)], None),
    ('room:scroll_hall', 'room', 'L', "Lecterns with five scrolls: Intellect, Personality, Speed (+2 once), Magic (+5 Mind once), Aging (a curse).", [(WIZARD, 2), (ACOLYTE, 2)], None),
    ('room:dormitory', 'room', 'L', "Cots and robes, the chest of the wizards' pay; the barred door (lifted from here) and the keep stair.", [(WIZARD, 2), (ACOLYTE, 3)], 4),
    ('room:keep_stair', 'stair', 'S', "Twenty steps up to the keep's top.", [], None),
    ('room:keep_landing', 'room', 'M', "The keep stair's head: the study's door west, the moon tower east.", [(WIZARD, 1)], None),
    ('room:study', 'room', 'M', "The Cult Leader and his two sorcerers; the Scroll of Insight on the desk (q-c8.scroll), his chest beside it; a door to the roof walk.", [(LEADER, 1), (SORCERER, 2)], 4),
    ('room:roof_walk', 'corridor', 'M', "A walk on the keep's leads under open sky, the study's back door to the moon tower.", [], None),
    ('room:moon_tower', 'room', 'M', "The tower top open to the sky: the rack of six scrolls (Energy; a faded Magic; Depression, Confusion, Death, Insanity), a brazier.", [(WIZARD, 1)], None),
]
LINKS = [
    ('link:gate_hall', 'room:gatehouse', 'room:great_hall', 'door', "Double doors: two wolf-headed wings."),
    ('link:hall_kennels', 'room:great_hall', 'room:kennels', 'door', None),
    ('link:hall_script', 'room:great_hall', 'room:scriptorium', 'door', None),
    ('link:script_stores', 'room:scriptorium', 'room:stores', 'door', None),
    ('link:hall_westtower', 'room:great_hall', 'room:west_foot', 'open', None),
    ('link:westfoot_stair', 'room:west_foot', 'room:west_stair', 'open', None),
    ('link:westtower_up', 'room:west_stair', 'room:west_landing', 'stairs', None),
    ('link:kennels_easttower', 'room:kennels', 'room:east_foot', 'open', None),
    ('link:eastfoot_stair', 'room:east_foot', 'room:east_stair', 'open', None),
    ('link:easttower_up', 'room:east_stair', 'room:east_landing', 'stairs', None),
    ('link:kennels_dstair', 'room:kennels', 'room:dungeon_stair', 'open', None),
    ('link:dstair_down', 'room:dungeon_stair', 'room:guard_room', 'stairs', None),
    ('link:guard_den', 'room:guard_room', 'room:den', 'open', None),
    ('link:den_cells', 'room:den', 'room:cells', 'open', None),
    ('link:cells_guard', 'room:cells', 'room:guard_room', 'door', "The cell row's iron door."),
    ('link:cells_cell', 'room:cells', 'room:cell', 'door', "Bars, raised by the jailers' lever (state:cell_lever)."),
    ('link:den_bones', 'room:den', 'room:bone_pit', 'open', None),
    ('link:west_battle', 'room:west_landing', 'room:battlements', 'door', None),
    ('link:battle_east', 'room:battlements', 'room:east_landing', 'door', None),
    ('link:password_door', 'room:west_landing', 'room:scroll_hall', 'door', "'There wolf' (state:password)."),
    ('link:scroll_dorm', 'room:scroll_hall', 'room:dormitory', 'open', None),
    ('link:dorm_east', 'room:dormitory', 'room:east_landing', 'door', "Barred on the dormitory's side: one way until lifted."),
    ('link:dorm_keep', 'room:dormitory', 'room:keep_stair', 'open', None),
    ('link:keep_up', 'room:keep_stair', 'room:keep_landing', 'stairs', None),
    ('link:landing_study', 'room:keep_landing', 'room:study', 'door', None),
    ('link:study_roof', 'room:study', 'room:roof_walk', 'door', None),
    ('link:roof_moon', 'room:roof_walk', 'room:moon_tower', 'open', None),
    ('link:moon_landing', 'room:moon_tower', 'room:keep_landing', 'open', None),
]
AREA = sum((r[2] - r[0]) * (r[3] - r[1]) for r in ROOM_RECT.values())


def plan_doc(level):
    spaces = []
    for sid, kind, size, purpose, pop, chest in PLAN_SPACES:
        r = next(x for x in rooms if x['id'] == sid)
        fl = r['floor'] if 'slope' not in r else [min(r['floor'], r['slope']['to']), max(r['floor'], r['slope']['to'])]
        s = {'id': sid, 'name': r['name'], 'kind': 'room' if kind == 'stair' else kind, 'size': size, 'floor': fl,
             'purpose': purpose}
        if pop:
            s['population'] = [{'actor': m, 'groups': 1, 'levels': [LEVEL[m], LEVEL[m]],
                                'notes': f"{n} placed {NAME[m]} ({m})."} for m, n in pop]
        else:
            s['empty'] = True
        if chest:
            s['treasure'] = [{'kind': 'chest', 'count': 1, 'tier': chest}]
        spaces.append(s)
    links = []
    for lid, a, b, kind, notes in LINKS:
        d = {'id': lid, 'from': a, 'to': b, 'kind': kind}
        if notes:
            d['notes'] = notes
        links.append(d)
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The fortress of a wizard cult on its crag at X6's north rim. The gate opens on a gatehouse and the cult's great hall, where werewolves lie by the fire like dogs; the cult keeps them in iron pens round a feeding pit beside the hall, and the overflow in a den cut into the crag below, by the cell row where a peasant waits in a chain. Two towers climb to a battlement walk over the gate; between them the cult's own wing (the hall of scrolls and the wizards' dormitory) lies behind a stone door that asks for a password, and the keep stair climbs from the dormitory to the Cult Leader's study, the roof walk and the moon tower. Readable scrolls everywhere: blessings and curses, their names on hover.",
        'purpose': "Q-C8 The Scroll of Insight: the Scroll of Insight on the Cult Leader's desk (q-c8.scroll); the L2 door's password 'There wolf' (Arie's note; the Trapped Peasant, q-c8.peasant), q-c8.l2_door / q-c8.l2_wrong; the peasant freed after the jailers' lever (q-c8.peasant_freed, 500 experience). Party 31-34, monsters 24-45 (the Basenji Cult Leader 45), 45 placed, treasure 4.",
        'mood': "Dark block stone and black timber lit by torches and the hall's fire; the reek of the kennels; cold dark stone and dripping rock in the dungeon; the white desert light on the walks over the gate and the tower tops.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:towers', 'spaces': ['room:great_hall', 'room:west_foot', 'room:west_stair', 'room:west_landing',
                                             'room:battlements', 'room:east_landing', 'room:east_stair', 'room:east_foot',
                                             'room:kennels'],
             'notes': "Up one tower, over the battlement walk, down the other: open from the start."},
            {'id': 'loop:wing', 'spaces': ['room:west_landing', 'room:scroll_hall', 'room:dormitory', 'room:east_landing',
                                           'room:battlements'],
             'notes': "Through the cult's wing and out by its barred door (lifted from inside), back over the battlements."},
            {'id': 'loop:dungeon', 'spaces': ['room:guard_room', 'room:den', 'room:cells'],
             'notes': "Round the dungeon: the jailers' room, the den, the cell row."},
            {'id': 'loop:keep', 'spaces': ['room:keep_landing', 'room:study', 'room:roof_walk', 'room:moon_tower'],
             'notes': "Round the keep's top through the study's two doors."},
        ],
        'entrances': [
            {'id': 'entrance:x6_gate', 'space': 'room:gatehouse', 'kind': 'both', 'neighbour': 'exit:x6_gate',
             'facing': 'n', 'notes': "From and to X6's Castle Basenji door ('Castle Basenji.  Enter?', aaze0001:19): in the gatehouse 256 inside the gate's wings, facing north. Out by either wing (the game's leave window; 'Leave Castle Basenji?', aaze0068:14)."},
        ],
        'critical_path': ['room:gatehouse', 'room:great_hall', 'room:west_foot', 'room:west_stair', 'room:west_landing',
                          'room:scroll_hall', 'room:dormitory', 'room:keep_stair', 'room:keep_landing', 'room:study'],
        'return_path': ['room:study', 'room:keep_landing', 'room:keep_stair', 'room:dormitory', 'room:east_landing',
                        'room:east_stair', 'room:east_foot', 'room:kennels', 'room:great_hall', 'room:gatehouse'],
        'goals': [
            {'id': 'goal:scroll', 'space': 'room:study', 'kind': 'take', 'story': 'Q-C8',
             'what': "The Scroll of Insight on the Cult Leader's desk (q-c8.scroll).", 'gives': {'qbit': 'scroll_found'}},
            {'id': 'goal:password', 'space': 'room:west_landing', 'kind': 'use', 'story': 'Q-C8',
             'what': "'STOP!  What is the password?' 'There wolf' (q-c8.l2_door).", 'gives': {'qbit': 'password'}},
            {'id': 'goal:peasant', 'space': 'room:cell', 'kind': 'use', 'story': 'Q-C8',
             'what': "The Trapped Peasant: his hint through the bars (q-c8.peasant); freed after the jailers' lever (q-c8.peasant_freed).",
             'gives': {'qbit': 'peasant_freed'}},
        ],
        'set_pieces': [
            {'id': 'set:kennels', 'kind': 'scripted', 'spaces': ['room:kennels'],
             'rule': "Iron pens with open gates round a sunken feeding pit; each pen's straw bed is a find once ('Werewolf Bed', then 'Nothing here.')."},
            {'id': 'set:password', 'kind': 'scripted', 'spaces': ['room:west_landing'],
             'rule': "The cult's door asks 'STOP!  What is the password?': 'There wolf' opens it for good; any other answer laughs at you and asks again next time."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 45, 'chests': 4,
                   'doors': len(doors), 'loops': 4, 'floor_area_munits2': round(AREA / 1e6, 1)},
        'notes': "Size M (MAPS: 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From the MU-6 graph devdocs/xeen/mockups/act4_graphs/xd14.graph.yml with D-39 (mockups/act4_a7_decisions.md: 16 Cult Acolytes 11197, the Basenji Cult Leader 11198, the Trapped Peasant 11233 freed by q-c8.peasant_freed, scrolls once per character and curses on the reader, the dormitory door barred from inside, the interior larger than the shell). The gate is the gatehouse's south wall (two exit wings, each its own picture); the two tower stairs and the keep stair are rooms of their own (straight flights); the battlement walk runs over the gate between the towers (not over the hall, which is open to its high beamed ceiling); the cult's wing stands over the gatehouse.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = r"""XD-14 Castle Basenji (not to scale; plan, north up; the gate south onto X6's terrace)

 L3 1280   [STUDY: Leader 45 + 2 sorcerers, desk = Scroll of Insight, chest T4]--door--[KEEP LANDING]--[MOON TOWER sky: rack]
              | door (back)                                                                         |
           [=============== ROOF WALK (sky) ===============================================]--------+
                                                              ^ keep stair (from the dormitory)
 L2  640   [HALL OF SCROLLS: 5 lecterns]==open==[WIZARDS' DORMITORY: chest T4]--keep stair--^
                | PASSWORD DOOR ("There wolf")         | BARRED (from inside)
           [WEST LANDING]--door--[ BATTLEMENT WALK over the gate (sky) ]--door--[EAST LANDING]
                ^ west stair                                                        ^ east stair
 L1    0   [KITCHEN T4]
             | door
           [SCRIPTORIUM: rack]--door--[ GREAT HALL: hearth, tables ]--door--[ KENNELS: pens, pit ]--dungeon stair-->
           [WEST FOOT]=====arch=====      ||double doors (wolves)           [EAST FOOT] (arch from the kennels)
             west stair (S)          [GATEHOUSE: arrival]                     east stair (S)
                                          ||gate (two wings) =exit= X6 terrace
 dungeon -512                         [JAILERS' ROOM: LEVER]--open--[WEREWOLF DEN]--open--[BONE PIT T4]
                                           | iron door                   |
                                      [========== CELL ROW ===========]--+
                                         | bars (lever)
                                      [PEASANT'S CELL]
"""

project = {
    'format': 0, 'id': 'xeen_xd14', 'name': 'Castle Basenji', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'XD-14', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [22, 10], 'climbs': 'n'},
    'map_stats': {'id': 9129, 'encounter_chance': 10, 'treasure_level': 4, 'trap_dice': 4,
                  'perception_difficulty': 8, 'refill_days': 672, 'music': 42, 'environment': 'castle',
                  'lock_difficulty': 8, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Werewolf', 'tier': 5, 'per_marker': [1, 2], 'weight': 60},
                            {'monster': 'Xeen Wizard', 'tier': 0, 'per_marker': [1, 2], 'weight': 40}]},
    'neighbours': [
        {'id': 'exit:x6_gate', 'to': 'xeen_x6.odm', 'kind': 'door', 'arrival': [-13312, 15104, 2592], 'direction': 270,
         'arrival_hint': "On X6's terrace in front of Castle Basenji's gatehouse, facing south (away from the gate).",
         'notes': "X6 Desert of the Sphinx (A5's, installed): its thing:castle_basenji door (-13312, 15507, 2592), 384 x 256, two leaves, facing south, leads in to entrance:x6_gate."},
    ],
    'qbits': QBITS,
    'items': {'scroll_of_insight': 12316},
    'notes': f"Xeen design brief, level L4: XD-14 Castle Basenji on X6's north-rim crag (Act IV, Q-C8 The Scroll of Insight). Monsters, all placed (45): 16 Cult Acolyte 11197 (24), 18 Werewolf 11421 (30), 2 Greater Werewolf 11422 (40), 6 Wizard 11190 (36), 2 Sorcerer 11191 (45) and the Basenji Cult Leader 11198 (45, the study); kill XP {KILL_XP / 4:,.0f} per member. The Trapped Peasant 11233 (peaceful, not counted) in the dungeon's cell. Rest encounters 10 %: Xeen Werewolf (Dif 5: Werewolf, Greater Werewolf, a few Wolfmen) and Xeen Wizard (Dif 0: Wizard 36 only). Hooks: q-c8.peasant, q-c8.peasant_freed, q-c8.l2_door, q-c8.l2_wrong, q-c8.scroll and the 14 scroll hooks. A3's qbits password 112161, scroll_found 112162, peasant_freed 112164; the map's own 118000-118009 (two used: dorm_bar 118000, cell_lever 118001). Music 42. The gate leads out to X6 (installed) at A5's point (-13312, 15104, 2592) facing south.",
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
        p['notes'] = f"Xeen design brief, level {lv}: XD-14 Castle Basenji (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-14 Castle Basenji, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'clear'},
              'notes': "The battlement walk, the roof walk and the moon tower (their sky ceilings) show X6's clear sky (X6's preset: plansky2 is its alias). No daylight block and no weather: the light there is the rooms' own daylight lights."}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', atmosphere)])
print('written L4; area %.1f M units^2; kill XP %d (%.0f per member)' % (AREA / 1e6, KILL_XP, KILL_XP / 4))
