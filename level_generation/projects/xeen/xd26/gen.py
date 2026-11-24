#!/usr/bin/env python3
"""XD-26 Gargoyle Eyrie: writes the L1-L4 project folders of devdocs/xeen/briefs/xd26 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd26/v.sh or cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-xd26 after XD-25's gen.py (level_generation/projects/xeen/xd25/gen.py).

Frame: x east, y north, z up. One tall shaft (x 0..2048, y 0..2048, floor 0) with ledge rooms opening onto it at their
own floor heights (512, 1024, 1536); the roost and the sky crack at 2048 north of the high ledge. Rooms stand 128 apart
(the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd26'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# The eyrie: MM7's natural caves (7d36, the dragon's cave): red-brown rock (cwb1) on walls and roofs, its rock floor
# (cfb1); the nests floored with straw (MM6 straw) and bones (the world's xobones).
ROCK = S('cwb1', 128, 256)
ROCKFLR = S('cfb1', 128, 128, scale=2)
STRAW = S('straw', 256, 256)
BONES = S('xobones', 128, 256)
# The fence's cache: MM7's dry brown cave rock (ch1b1), MM8 Ogre Fortress planks (gkp1ceil) on the floor and its plank
# doors (gkp103a); timber (t66abc10a, XD-05's ladder poles) for the bridge's rails, posts and every ladder.
DRYROCK = S('ch1b1', 128, 256)
PLANKFLR = S('gkp1ceil', 128, 128)
# The fence's single plank door: MM6's small plank door, its picture once over the leaf (A1's door check, merge point
# 15: gkp103a is one wing of a pair and showed 1.5 times across the 192-wide leaf).
PLANKDOOR = S('d2smldor', 128, 256, fit=True)
POLE = S('t66abc10a', 32, 128)
DECK = S('7t1beds', 256, 64)
DAYLIGHT = S('xodaylt', 256, 128, fit=True, uneven=True)
SKY = S('xwsky', 512, 512)
CRATE = S('crate_w64', 64, 64)
RUNGS = S('t66abc10a', 32, 128, uneven=True)   # the ladders' rails and rungs (as XD-05's pit ladder)

themes = [
    {'id': 'theme:rock', 'wall': ROCK, 'floor': ROCKFLR, 'ceiling': ROCK, 'door': PLANKDOOR, 'reveal': ROCK,
     'notes': "The eyrie's caves: MM7's dragon-cave rock (cwb1) on walls and roofs, its rock floor (cfb1)."},
    {'id': 'theme:nest', 'wall': ROCK, 'floor': STRAW, 'ceiling': ROCK, 'door': PLANKDOOR, 'reveal': ROCK,
     'notes': "The nesting caves: the same rock, the floor deep in old straw (MM6 straw)."},
    {'id': 'theme:fence', 'wall': DRYROCK, 'floor': PLANKFLR, 'ceiling': DRYROCK, 'door': PLANKDOOR, 'reveal': DRYROCK,
     'notes': "The fence's dry cave: MM7's brown rock (ch1b1), a plank floor (gkp1ceil), plank doors (gkp103a)."},
    {'id': 'theme:sky', 'wall': ROCK, 'floor': ROCKFLR, 'ceiling': SKY, 'door': PLANKDOOR, 'reveal': ROCK,
     'notes': "The sky crack: the rock open to the sky (the world's xwsky clouds overhead)."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octo(cx, cy, r):
    c = int(r * 0.41)
    return [[cx - c, cy - r], [cx + c, cy - r], [cx + r, cy - c], [cx + r, cy + c], [cx + c, cy + r], [cx - c, cy + r],
            [cx - r, cy + c], [cx - r, cy - c]]


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


def nest(at, r, notes, top=STRAW, **kw):
    d = {'outline': octo(at[0], at[1], r), 'rise': 24, 'surface': POLE, 'top_surface': top, 'notes': notes}
    d.update(kw)
    return d


# The bridge across the shaft (x 0..2048) at y 1440..1632, its deck's top at 1024; rails 16 wide 64 over the deck,
# posts every 512; a gap in the south rail (x 896..1152) where a plank is missing: the fall.
BY0, BY1, BZ = 1376, 1696, 1024
SHAFT_CEIL = 2560
MOUTH_X = 1344             # the mouth's middle (x)
HOIST = (2624, 2176, 3008, 2560)   # the hoist's foot under the high ledge's east end
HX, HY = 2816, 2368                 # the hoist deck's middle (the notch in the high ledge)
HOIST_DECK = S('gkp1ceil', 128, 128)

# ------------------------------------------------------------------------------------------------ floor 0
room('room:mouth', 'Cave mouth', outline=rect(1024, -1152, 1664, -128), floor=0, ceiling=512, theme='theme:rock',
     ambient=26,
     notes="The way in from the bare peaks of the Gargoyle Range, 640 by 1,024: droppings and bones; daylight behind.")
room('room:shaft_floor', 'Shaft floor', outline=rect(0, 0, 2048, 2048), floor=0, ceiling=SHAFT_CEIL,
     theme='theme:rock', ambient=14,
     platforms=[
         {'id': 'platform:bridge', 'at': [1024, (BY0 + BY1) // 2], 'size': [2048, BY1 - BY0], 'rise': 24,
          'base': BZ - 24, 'surface': POLE, 'top_surface': DECK,
          'notes': "The rope bridge across the shaft, 1,024 over its floor: a plank deck from the west ledge to the east nests."},
     ] + [
         {'at': [x, y], 'size': [16, 16], 'rise': 64, 'base': BZ, 'surface': POLE, 'top_surface': POLE,
          'notes': "Bridge post under the rail"} for x in (256, 768, 1280, 1792) for y in (BY0 + 8, BY1 - 8)
     ] + [nest([1500, 700], 160, "A fallen nest on the shaft floor.", top=BONES)],
     beams=[{'path': [[0, BY1 - 8], [2048, BY1 - 8]], 'width': 16, 'depth': 16, 'bottom': BZ + 64, 'surface': POLE,
             'notes': "The bridge's north rail (rope on poles)."},
            {'path': [[0, BY0 + 8], [896, BY0 + 8]], 'width': 16, 'depth': 16, 'bottom': BZ + 64, 'surface': POLE,
             'notes': "The south rail, west part."},
            {'path': [[1152, BY0 + 8], [2048, BY0 + 8]], 'width': 16, 'depth': 16, 'bottom': BZ + 64, 'surface': POLE,
             'notes': "The south rail, east part: between them the rail is torn away (the fall)."}],
     notes="The bottom of the vertical cave, 2,048 square and 2,560 high: every ledge opens on it, the bridge crosses it at 1,024, the high ledge runs along its north side at 1,536. A pole ladder climbs its west wall to the first ledge.")

# ------------------------------------------------------------------------------------------------ the low ledges (512)
room('room:ledge_low', 'First ledge', outline=rect(-1024, 0, -128, 896), floor=512, ceiling=1536,
     theme='theme:rock', ambient=16,
     platforms=[nest([-760, 300], 128, "A nest of sticks and straw.")],
     notes="The first shelf up the shaft's west wall, 896 square, open to the shaft along its whole east side; a ladder on its north wall up to the west ledge.")
room('room:low_nests', 'Low nests', outline=rect(-2048, 0, -1152, 896), floor=512, ceiling=1024,
     theme='theme:nest', ambient=18,
     platforms=[nest([-1800, 220], 144, "A young gargoyles' nest."), nest([-1450, 700], 128, "A nest.")],
     notes="Where the young gargoyles nest, 896 square, straw underfoot; the rock ramp climbs out of its north side.")
room('room:rock_ramp', 'Rock ramp', path=[[-1600, 1024], [-1600, 1600], [-1152, 1600]], width=256, floor=512,
     slope={'to': 1024}, ceiling=832, ceiling_slope={'to': 1344}, theme='theme:rock', ambient=20,
     notes="A rock ramp climbing 512 north and then east from the low nests to the west ledge.")

# ------------------------------------------------------------------------------------------------ the bridge level (1024)
room('room:ledge_w', 'West ledge', outline=rect(-1024, 1024, -128, 2048), floor=1024, ceiling=1920,
     theme='theme:rock', ambient=16,
     notes="Where the climb from below arrives, 896 by 1,024, open to the shaft along its east side; the bridge starts here. The high ledge's lip is overhead to the north (the drop).")
room('room:ledge_e', 'East nests', outline=rect(2176, 1024, 3072, 2048), floor=1024, ceiling=1920,
     theme='theme:nest', ambient=16,
     platforms=[nest([2560, 1250], 144, "A nest of sticks and bones.", top=BONES),
                nest([2850, 1800], 128, "A nest.")],
     notes="The east nests, 896 by 1,024, open to the shaft along its west side, where the bridge lands: nests of sticks and bones; the fence's door in its east wall, the way to the hoist's foot in its north wall.")
room('room:fence_cache', "The fence's cache", outline=rect(3200, 1024, 3712, 1664), floor=1024, ceiling=1344,
     theme='theme:fence', ambient=20,
     walls=[{'wall': 'south', 'panels': [{'id': 'panel:tagged_crates', 'at': 'centre', 'length': 192, 'bottom': 0,
                                          'height': 128, 'surface': S('crate_w64', 64, 64),
                                          'notes': "Crates stacked against the wall, tags on strings (D-4)."}]}],
     notes="A dry cave of crates tagged for buyers, 512 by 640: whoever hires the gargoyles to steal keeps his goods here. His winch in the north-east corner works the hoist up the wall.")
room('room:hoist_foot', 'Hoist foot', outline=rect(*HOIST), floor=1024, ceiling=1504, theme='theme:rock',
     ambient=20,
     platforms=[{'at': [x, HY], 'size': [8, 8], 'rise': 480, 'surface': POLE, 'top_surface': POLE,
                 'notes': "A hoist rope beside the deck's way."} for x in (HX - 136, HX + 136)],
     notes="A low cave under the high ledge's east end, 384 square, off the east nests: the fence's hoist comes down here through a notch in the ledge above.")

# ------------------------------------------------------------------------------------------------ the high ledge (1536)
room('room:high_ledge', 'High ledge', outline=rect(-1024, 2176, 3072, 2560), floor=1536, ceiling=2432,
     theme='theme:rock', ambient=16,
     platforms=[{'at': [x, HY], 'size': [8, 8], 'rise': 736, 'surface': POLE, 'top_surface': POLE,
                 'notes': "A hoist rope up to the beam."} for x in (HX - 136, HX + 136)],
     beams=[{'path': [[2560, HY], [3072, HY]], 'width': 32, 'depth': 32, 'bottom': 2272, 'surface': POLE,
             'notes': "The hoist beam over the notch, wedged into the east wall."}],
     notes="A narrow shelf 384 wide along the shaft's north side, 4,096 long: open to the shaft in the middle, a gap over the west ledge (a 512 drop), the fence's hoist in a notch at its east end under a hoist beam; the roost ladder on its north wall, hanging moss at its west end.")
room('room:hidden_ledge', 'Hidden ledge', outline=rect(-1024, 2688, -384, 3200), floor=1536, ceiling=1856,
     theme='theme:rock', ambient=22,
     notes="Behind the hanging moss, 640 by 512: a dead climber's pack.")

# ------------------------------------------------------------------------------------------------ the roost (2048)
room('room:roost', "Matriarch's roost", outline=rect(512, 2688, 2048, 3712), floor=2048, ceiling=2688,
     theme='theme:nest', ambient=14,
     platforms=[nest([1280, 3300], 224, "The great nest: sticks, bones and the gargoyles' shiny things.", top=BONES,
                     id='platform:great_nest'),
                nest([800, 3500], 128, "A nest."), nest([1800, 3000], 128, "A nest.")],
     notes="The biggest nest under the peak, 1,536 by 1,024: the great nest of sticks and bones heaped with stolen silver; the sky crack opens east.")
room('room:sky_crack', 'Sky crack', outline=rect(2176, 2944, 2688, 3456), floor=2048, ceiling=2816,
     theme='theme:sky', ambient=30,
     notes="Daylight through a split in the peak, 512 square, open to the sky: the quick way out to a ledge high on the same peak.")

# ------------------------------------------------------------------------------------------------ openings
op('open:mouth_shaft', 'room:mouth', 'room:shaft_floor', link='link:mouth_shaft', width=384, height=448)
op('open:shaft_ledgelow', 'room:shaft_floor', 'room:ledge_low', link='link:shaft_ledgelow', width='full',
   height='full', notes="The first ledge's lip: open along its whole east side, 512 over the shaft floor.")
op('open:ledgelow_nests', 'room:ledge_low', 'room:low_nests', link='link:ledgelow_nests', width=384, height=384)
op('open:ledgelow_ledgew', 'room:ledge_low', 'room:ledge_w', link='link:ledgelow_ledgew', width=192, height=256,
   along=0.5, notes="The top of the ladder from the first ledge: a hole in the rock 512 up.")
op('open:nests_ramp', 'room:low_nests', 'room:rock_ramp', link='link:nests_ledgew', width=224, height=288)
op('open:ramp_ledgew', 'room:rock_ramp', 'room:ledge_w', link='link:nests_ledgew', width=224, height=288)
op('open:shaft_ledgew', 'room:shaft_floor', 'room:ledge_w', link='link:ledgew_bridge', width='full', height='full',
   notes="The west ledge's lip, 1,024 over the shaft floor; the bridge starts here.")
op('open:shaft_ledgee', 'room:shaft_floor', 'room:ledge_e', link='link:bridge_ledgee', width='full', height='full',
   notes="The east nests' lip, 1,024 over the shaft floor; the bridge lands here.")
op('open:ledgee_fence', 'room:ledge_e', 'room:fence_cache', link='link:ledgee_fence', width=192, height=256)
op('open:ledgee_hoist', 'room:ledge_e', 'room:hoist_foot', link='link:ledgee_hoist', width=256, height=320,
   notes="Into the hoist's foot under the high ledge.")
op('open:hoist_notch', 'room:high_ledge', 'room:hoist_foot', link='link:hoist_high', at=[HX, HY], size=[256, 256],
   notes="The notch in the high ledge the hoist's deck rides through.", **{'in': 'floor'})
op('open:shaft_high', 'room:shaft_floor', 'room:high_ledge', link='link:high_shaft', width='full', height='full',
   notes="The high ledge's lip, 1,536 over the shaft floor.")
op('open:high_ledgew', 'room:high_ledge', 'room:ledge_w', link='link:high_drop', width=384, height=256,
   along=0.5, notes="A gap in the high ledge's rim over the west ledge: the 512 drop.")
op('open:high_hidden', 'room:high_ledge', 'room:hidden_ledge', link='link:high_hidden', width=160, height=224,
   along=0.5, notes="Behind the hanging moss.")
op('open:high_roost', 'room:high_ledge', 'room:roost', link='link:high_roost', width=192, height=256,
   notes="The top of the roost ladder: a hole in the rock 512 up.")
op('open:roost_crack', 'room:roost', 'room:sky_crack', link='link:roost_crack', width=256, height=384)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:rock', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-26 Gargoyle Eyrie: one tall shaft with ledges at 512, 1,024 and 1,536, the roost at 2,048; x east, y north. Written by output/studio_cal/xd26/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:mouth': 0, 'room:shaft_floor': 0, 'room:ledge_low': 512, 'room:low_nests': 512, 'room:rock_ramp': 512,
          'room:ledge_w': 1024, 'zone:bridge': 1024, 'room:ledge_e': 1024, 'room:fence_cache': 1024,
          'room:hoist_foot': 1024, 'room:high_ledge': 1536, 'room:hidden_ledge': 1536, 'room:roost': 2048,
          'room:sky_crack': 2048}
PLAN_SPACES = [
    ('room:mouth', 'Cave mouth', 'room', 'S', "From the bare peaks of the Gargoyle Range; droppings and bones.", None),
    ('room:shaft_floor', 'Shaft floor', 'room', 'L', "The bottom of the vertical cave: every ledge seen from here; gargoyles dive from above.", ('a', 5)),
    ('room:ledge_low', 'First ledge', 'room', 'M', "The first shelf up the wall; the ladder up to the west ledge.", ('a', 3)),
    ('room:low_nests', 'Low nests', 'room', 'M', "Young gargoyles; a rock ramp climbs on to the west ledge.", ('a', 3)),
    ('room:rock_ramp', 'Rock ramp', 'corridor', 'S', "The ramp from the low nests up to the west ledge.", None),
    ('room:ledge_w', 'West ledge', 'room', 'M', "Where the climb from below arrives; the rope bridge starts.", ('a', 3)),
    ('zone:bridge', 'Rope bridge', 'zone', 'M', "Across the open shaft, 1,024 above its floor; step off where the rail is torn and you fall.", ('b', 3)),
    ('room:ledge_e', 'East nests', 'room', 'M', "Nests of sticks and bones; the fence's door; the way to the hoist's foot.", ('b', 3)),
    ('room:fence_cache', "The fence's cache", 'room', 'S', "Crates tagged for buyers; the winch that lowers the hoist.", ('c', 1)),
    ('room:hoist_foot', 'Hoist foot', 'corridor', 'S', "Where the fence's hoist comes down from the high ledge once the winch has lowered it.", None),
    ('room:high_ledge', 'High ledge', 'corridor', 'M', "A narrow shelf; the roost ladder; hanging moss along the wall.", ('b', 3)),
    ('room:hidden_ledge', 'Hidden ledge', 'room', 'S', "Behind the moss: a dead climber's pack.", None),
    ('room:roost', "Matriarch's roost", 'room', 'L', "The great nest: the Scarab of Imaging among stolen silver.", ('c', 6)),
    ('room:sky_crack', 'Sky crack', 'room', 'S', "Daylight through a split in the peak: the quick way out.", None),
]
LEVELS = {'a': [16, 16], 'b': [22, 22], 'c': [28, 28]}


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if sid == 'zone:bridge':
            s['part_of'] = 'room:shaft_floor'
        if pop:
            rank, n = pop
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': LEVELS[rank],
                                'notes': f"About {n} gargoyles (rank {rank})."}]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:mouth_shaft', 'from': 'room:mouth', 'to': 'room:shaft_floor', 'kind': 'open'},
        {'id': 'link:shaft_ledgelow', 'from': 'room:shaft_floor', 'to': 'room:ledge_low', 'kind': 'ladder',
         'notes': "A pole ladder up the shaft's west wall under the first ledge's lip (D-17)."},
        {'id': 'link:ledgelow_nests', 'from': 'room:ledge_low', 'to': 'room:low_nests', 'kind': 'open'},
        {'id': 'link:ledgelow_ledgew', 'from': 'room:ledge_low', 'to': 'room:ledge_w', 'kind': 'ladder'},
        {'id': 'link:nests_ledgew', 'from': 'room:low_nests', 'to': 'room:ledge_w', 'kind': 'ramp',
         'notes': "By the rock ramp (its own room)."},
        {'id': 'link:ledgew_bridge', 'from': 'room:ledge_w', 'to': 'zone:bridge', 'kind': 'open'},
        {'id': 'link:bridge_ledgee', 'from': 'zone:bridge', 'to': 'room:ledge_e', 'kind': 'open'},
        {'id': 'link:bridge_drop', 'from': 'zone:bridge', 'to': 'room:shaft_floor', 'kind': 'drop',
         'notes': "Where the south rail is torn away: a fall of 1,024."},
        {'id': 'link:ledgee_fence', 'from': 'room:ledge_e', 'to': 'room:fence_cache', 'kind': 'door',
         'motion': 'slide'},
        {'id': 'link:ledgee_hoist', 'from': 'room:ledge_e', 'to': 'room:hoist_foot', 'kind': 'open'},
        {'id': 'link:hoist_high', 'from': 'room:hoist_foot', 'to': 'room:high_ledge', 'kind': 'lift',
         'condition': {'qbit': 'hoist_winched'},
         'notes': "hoist: winch. The fence's hoist (D-17): it hangs at the high ledge until the winch in the fence's cache lowers it; then its deck or a call rope at either stop sends it."},
        {'id': 'link:high_shaft', 'from': 'room:high_ledge', 'to': 'room:shaft_floor', 'kind': 'overlook',
         'notes': "The high ledge's lip over the shaft."},
        {'id': 'link:high_hidden', 'from': 'room:high_ledge', 'to': 'room:hidden_ledge', 'kind': 'secret_door',
         'motion': 'slide', 'notes': "Through the hanging moss."},
        {'id': 'link:high_roost', 'from': 'room:high_ledge', 'to': 'room:roost', 'kind': 'ladder'},
        {'id': 'link:high_drop', 'from': 'room:high_ledge', 'to': 'room:ledge_w', 'kind': 'drop',
         'notes': "A jump of 512 through the gap in the rim."},
        {'id': 'link:roost_crack', 'from': 'room:roost', 'to': 'room:sky_crack', 'kind': 'open'},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "A cave mouth high on the Gargoyle Range opens into one tall shaft. Ledges climb its walls, joined by ladders and a rope bridge 1,024 over the floor, and the gargoyles dive across the open air at whoever climbs. A fence who hires them to steal keeps his crates on the east side; his winch lowers the hoist from the high ledge. At the top, in the matriarch's roost, Carlawna's Scarab of Imaging lies among the stolen silver; a crack in the peak lets the daylight in.",
        'purpose': "Q-C10 The Scarab of Imaging (Carlawna, X4). Party 15 to 17, Gargoyles 16/22/28 (all three tiers; they fly across the shaft), about 28 monsters, treasure level 2 with the roost hoard at 3.",
        'mood': "Wind in a dark shaft, wingbeats overhead, straw and bones in the nests; daylight from the crack at the top.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:low', 'spaces': ['room:ledge_low', 'room:low_nests', 'room:rock_ramp', 'room:ledge_w'],
             'notes': "Two ways up from the first ledge: the ladder or the nests and the ramp."},
            {'id': 'loop:fall', 'spaces': ['room:shaft_floor', 'room:ledge_low', 'room:ledge_w', 'zone:bridge'],
             'notes': "Off the bridge where the rail is torn, and back up: the fall is the quick way down."},
        ],
        'entrances': [{'id': 'entrance:x4_range', 'space': 'room:mouth', 'kind': 'both', 'neighbour': 'exit:x4_range',
                       'facing': 'n',
                       'how': "From and to X4's door:xd26, the cave mouth on the Gargoyle Range: inside the mouth, facing in; daylight behind."},
                      {'id': 'entrance:x4_peak', 'space': 'room:sky_crack', 'kind': 'exit', 'neighbour': 'exit:x4_peak',
                       'how': "One way out through the split in the peak, onto A5's ledge platform high on the same peak (no way back in)."}],
        'critical_path': ['room:mouth', 'room:shaft_floor', 'room:ledge_low', 'room:ledge_w', 'zone:bridge',
                          'room:ledge_e', 'room:fence_cache', 'room:ledge_e', 'room:hoist_foot', 'room:high_ledge',
                          'room:roost'],
        'return_path': ['room:roost', 'room:sky_crack'],
        'goals': [
            {'id': 'goal:scarab', 'space': 'room:roost', 'kind': 'take', 'story': 'Q-C10',
             'what': "The Scarab of Imaging in the great nest (A3's hook q-c10.scarab).",
             'gives': {'qbit': 'scarab_found'}},
        ],
        'keys': [{'id': 'key:winch', 'grants': {'qbit': 'hoist_winched'}, 'found_in': 'room:fence_cache',
                  'how': "The fence's winch lowers his hoist from the high ledge."}],
        'set_pieces': [
            {'id': 'set:shaft', 'kind': 'vista', 'spaces': ['room:shaft_floor', 'zone:bridge'],
             'rule': "The shaft seen from every ledge; gargoyles fly across it to whoever is on a ledge or the bridge."},
            {'id': 'set:winch', 'kind': 'scripted', 'spaces': ['room:fence_cache', 'room:hoist_foot', 'room:high_ledge'],
             'rule': "The winch lowers the fence's hoist the first time; then the deck or a call rope at either stop sends it up or down."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 13, 'sectors': 13, 'monsters_about': 28, 'chests': 3, 'doors': 3, 'loops': 2,
                   'floor_area_munits2': 13},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act2_graphs/xd26.graph.yml and D-4 (act2_dungeon_decisions.md, XD-26). D-17: the graph's ladder from the shaft floor to the first ledge; the fence's winch drives a two-state hoist (XD-11's lift) between the east nests' hoist foot (1024) and the high ledge (1536). The bridge is a zone of the shaft (a platform), the rock ramp and the hoist's foot their own rooms (13).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-26 Gargoyle Eyrie (not to scale; side view of the shaft, west left, east right)

  2048   [hidden]   [ROOST: great nest, scarab] -- [sky crack] =exit, one way= (X4: peak ledge)
                         | ladder
  1536   moss=[====== HIGH LEDGE (along the shaft's north side) ======][notch]
                gap (drop 512)        |  lip                           | hoist (the winch lowers it first)
  1024   [ledge_w] ===== rope bridge (torn rail: fall) ===== [east nests]-[hoist foot]
            |  ^ramp                                             =door= [fence's cache: winch]
   512   [ledge_low]--[low nests]
            ^ ladder
     0   [SHAFT FLOOR] ---- [cave mouth] =exit= (X4: Gargoyle Range)
"""

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:mouth', 'at': [MOUTH_X, -1000], 'facing': 'n',
                    'notes': "Just inside the cave mouth from the Gargoyle Range (X4's door:xd26), facing in (north)."}
objects['doors'] = [
    {'id': 'door:fence', 'opening': 'open:ledgee_fence', 'kind': 'hinged',
     'thickness': 16, 'speed': 160, 'surface': PLANKDOOR, 'back_surface': PLANKDOOR,  # hinged: its picture fitted once
     # (a folding leaf lays a picture one texel to the unit: 1.5 times across; A1's door check, merge point 15)
     'notes': "The fence's plank door."},
    {'id': 'door:moss', 'opening': 'open:high_hidden', 'kind': 'slide_up', 'secret': True, 'tile': True,
     'thickness': 16, 'speed': 96, 'surface': ROCK, 'back_surface': ROCK,
     'notes': "The hanging moss over the hidden ledge's way (secret; drawn as the ledge's rock)."},
]


def light(id, rm, at, h, r, col, **kw):
    # The lamp rule (the user, 2026-11-20; A1's lights audit): the heights below were written absolute, but a light's
    # `height` is over its room's floor: the room's floor is taken off here.
    floor = next(x.get('floor', 0) for x in rooms if x['id'] == rm)
    d = {'id': id, 'room': rm, 'at': at, 'height': h - floor if h > floor > 0 else h, 'radius': r, 'color': col}
    d.update(kw)
    return d


DAY = [200, 205, 220]
FIRE = [255, 170, 90]
objects['lights'] = [
    light('light:mouth', 'room:mouth', [MOUTH_X, -1050], 240, 900, DAY, notes="Daylight from the mouth."),
    light('light:shaft_low', 'room:shaft_floor', [1024, 1024], 400, 1600, [150, 150, 170]),
    light('light:shaft_high', 'room:shaft_floor', [1024, 1800], 2200, 1800, DAY,
          notes="Grey daylight leaking down from the peak."),
    light('light:ledge_low', 'room:ledge_low', [-600, 450], 700, 700, [150, 150, 170]),
    light('light:low_nests', 'room:low_nests', [-1600, 450], 760, 700, [150, 150, 170]),
    light('light:ramp', 'room:rock_ramp', [-1600, 1500], 900, 700, [150, 150, 170]),
    light('light:ledge_w', 'room:ledge_w', [-576, 1536], 1250, 800, [150, 150, 170]),
    light('light:ledge_e', 'room:ledge_e', [2624, 1536], 1250, 800, [150, 150, 170]),
    light('light:fence', 'room:fence_cache', [3456, 1344], 1240, 600, FIRE, notes="The fence's lantern."),
    light('light:hoist', 'room:hoist_foot', [2816, 2250], 1400, 700, FIRE, notes="The fence's lantern at the hoist's foot."),
    light('light:hoist_top', 'room:high_ledge', [2816, 2368], 2100, 800, FIRE, notes="A lantern hung from the hoist beam."),
    light('light:high_w', 'room:high_ledge', [0, 2368], 1750, 900, [160, 160, 180]),
    light('light:high_e', 'room:high_ledge', [2600, 2368], 1750, 900, [160, 160, 180]),
    light('light:hidden', 'room:hidden_ledge', [-704, 2944], 1700, 450, [140, 140, 160]),
    light('light:roost', 'room:roost', [1280, 3200], 2400, 1300, DAY),
    light('light:sky', 'room:sky_crack', [2432, 3200], 2500, 900, [230, 230, 240], notes="Daylight through the crack."),
]
objects['exits'] = [
    {'id': 'exit:mouth', 'room': 'room:mouth', 'wall': 'south', 'size': [384, 320], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
     'to': 'exit:x4_range', 'notes': "The cave mouth onto the Gargoyle Range (daylight)."},
    {'id': 'exit:sky_crack', 'room': 'room:sky_crack', 'wall': 'east', 'size': [320, 384], 'surface': S('7solid01', 256, 128, fit=True, uneven=True),
     'to': 'exit:x4_peak', 'notes': "The split in the peak (daylight): one way out."},
]
objects['ladders'] = [
    {'id': 'ladder:ledge_low', 'room': 'room:shaft_floor', 'at': [4, 448], 'facing': 'w', 'height': 512,
     'exit': [-192, 448], 'grab_at_top': True, 'surface': RUNGS,
     'notes': "A pole ladder up the shaft's west wall to the first ledge's lip (the graph's ladder, D-17)."},
    {'id': 'ladder:ledge_w', 'room': 'room:ledge_low', 'at': [-576, 888], 'facing': 'n', 'height': 512,
     'exit': [-576, 1110], 'grab_at_top': True, 'surface': RUNGS,
     'notes': "A pole ladder up the first ledge's north wall to the west ledge."},
    {'id': 'ladder:roost', 'room': 'room:high_ledge', 'at': [1280, 2552], 'facing': 'n', 'height': 512,
     'exit': [1280, 2780], 'grab_at_top': True, 'surface': RUNGS, 'notes': "A pole ladder up the high ledge's north wall to the roost."},
]
objects['switches'] = [
    {'id': 'switch:winch', 'room': 'room:fence_cache', 'kind': 'lever', 'wall': 'north', 'along': 0.8,
     'base': S('t66abc10a', 32, 128), 'off': S('t66abc10a', 32, 128),
     'notes': "The fence's winch: its crank on the north wall, the rope running through the rock to the hoist."},
    {'id': 'switch:hoist_bottom', 'room': 'room:hoist_foot', 'kind': 'button', 'at': [2624, 2290], 'height': 112,
     'notes': "The hoist's call rope at its foot, on the west wall beside the deck."},
    {'id': 'switch:hoist_top', 'room': 'room:high_ledge', 'kind': 'button', 'at': [3072, 2260], 'height': 112,
     'notes': "The hoist's call rope at the high ledge, on the east wall beside the notch."},
]
objects['chests'] = [
    {'id': 'chest:fence', 'room': 'room:fence_cache', 'at': [3640, 1100], 'facing': 'e', 'treasure_level': 2,
     'random_items': 2, 'gold': 300, 'trap_level': 2, 'notes': "The fence's strongbox."},
    {'id': 'chest:climber', 'room': 'room:hidden_ledge', 'at': [-900, 3100], 'treasure_level': 2,
     'random_items': 1, 'gold': 200, 'notes': "A dead climber's pack."},
    {'id': 'chest:hoard', 'room': 'room:roost', 'at': [1950, 3620], 'facing': 'w', 'treasure_level': 3,
     'random_items': 2, 'gold': 800, 'trap_level': 2, 'notes': "The roost's hoard of stolen silver (the map's hoard, a level up)."},
]
# A2's Gargoyles (Cloudside), block 11540: A Gargoyle 16 (11540), B Gargoyle Lord 22 (11541), C Obsidian Gargoyle 28
# (11542). One slot `Xeen Gargoyle`; every marker fixes its tier. Markers stand well inside the ledges (D-4: none in a
# nook or a shelf opening).
objects['spawns'] = [
    {'id': 'spawn:shaft_w', 'room': 'room:shaft_floor', 'at': [700, 1100], 'slot': 1, 'tier': 'a',
     'notes': "They dive from above."},
    {'id': 'spawn:shaft_e', 'room': 'room:shaft_floor', 'at': [1756, 172], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:ledge_low', 'room': 'room:ledge_low', 'at': [-600, 600], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:low_nests', 'room': 'room:low_nests', 'at': [-1600, 450], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:ledge_w', 'room': 'room:ledge_w', 'at': [-600, 1300], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:bridge', 'room': 'room:shaft_floor', 'at': [1500, (BY0 + BY1) // 2], 'floor_height': BZ, 'slot': 1,
     'tier': 'b', 'notes': "On the bridge: they attack whoever crosses."},
    {'id': 'spawn:ledge_e', 'room': 'room:ledge_e', 'at': [2700, 1500], 'slot': 1, 'tier': 'b'},
    {'id': 'spawn:high', 'room': 'room:high_ledge', 'at': [600, 2368], 'slot': 1, 'tier': 'b'},
    {'id': 'spawn:roost_w', 'room': 'room:roost', 'at': [900, 3000], 'slot': 1, 'tier': 'c'},
    {'id': 'spawn:roost_e', 'room': 'room:roost', 'at': [1700, 3450], 'slot': 1, 'tier': 'c'},
]
objects['monsters'] = [
    {'id': 'monster:fence_guard', 'room': 'room:fence_cache', 'monster': 11542, 'at': [3450, 1250], 'facing': 180,
     'hostile': True, 'group': 2, 'notes': "An Obsidian Gargoyle (28) guarding the fence's goods."},
    {'id': 'monster:matriarch', 'room': 'room:roost', 'monster': 11542, 'at': [1280, 3100], 'facing': 270,
     'hostile': True, 'group': 3, 'notes': "The matriarch at her nest: an Obsidian Gargoyle (28)."},
]


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


objects['lifts'] = [
    {'id': 'lift:hoist', 'room': 'room:hoist_foot', 'at': [HX, HY], 'size': [256, 256], 'travel': 480,
     'thickness': 32, 'speed': 128, 'state': 'up', 'surface': HOIST_DECK,
     'notes': "The fence's hoist: a plank deck on ropes under the hoist beam. It starts at the upper stop, flush with the high ledge in its notch; the winch lowers it the first time, then its deck or a call rope at either stop sends it."},
]
objects['decorations'] = [
    deco('deco:mouth_bones', 'room:mouth', 'dec29', [1150, -700]),
    deco('deco:mouth_rock', 'room:mouth', '6rock02', [1506, -386]),
    deco('deco:shaft_bones_1', 'room:shaft_floor', '7dec18', [300, 1800], floor_height=0),
    deco('deco:shaft_bones_2', 'room:shaft_floor', 'dec29', [1850, 1200], floor_height=0),
    deco('deco:shaft_corpse', 'room:shaft_floor', 'Corpse03', [1000, 1150], floor_height=0,
         notes="Someone who fell from the bridge."),
    deco('deco:shaft_mite_1', 'room:shaft_floor', 'stlmite2', [1900, 150], floor_height=0),
    deco('deco:shaft_mite_2', 'room:shaft_floor', 'stlmite1', [150, 1900], floor_height=0),
    deco('deco:ledge_low_bones', 'room:ledge_low', 'dec29', [-900, 800], floor_height=512),
    deco('deco:low_nests_skulls', 'room:low_nests', 'sklplrev', [-1907, 762], floor_height=512),
    deco('deco:ledge_w_bones', 'room:ledge_w', '7dec18', [-950, 1950], floor_height=1024),
    deco('deco:ledge_e_skull', 'room:ledge_e', '7dec20', [3000, 1100], floor_height=1024),
    deco('deco:fence_sack_1', 'room:fence_cache', 'bag01', [3640, 1260], floor_height=1024),
    deco('deco:fence_sack_2', 'room:fence_cache', 'bag01', [3640, 1400], floor_height=1024),
    deco('deco:fence_keg', 'room:fence_cache', 'smlbarel', [3420, 1590], floor_height=1024),
    deco('deco:fence_lantern', 'room:fence_cache', 'torch01', [3712, 1344], wall='east', height=160),
    deco('deco:high_bones', 'room:high_ledge', 'dec29', [2200, 2500], floor_height=1536),
    deco('deco:hidden_corpse', 'room:hidden_ledge', 'Corpse05', [-500, 3080], floor_height=1536,
         notes="The climber, long dead."),
    deco('deco:roost_skulls', 'room:roost', 'sklplrev', [585, 3573], floor_height=2048),
    deco('deco:roost_bones', 'room:roost', '7dec18', [1950, 2800], floor_height=2048),
]
objects['sounds'] = [
    {'id': 'sound:wind', 'room': 'room:shaft_floor', 'at': [1024, 1024], 'sound': 'whistling wind', 'radius': 4000,
     'inner_radius': 1500, 'volume': 0.6, 'notes': "Wind in the shaft."},
]

# ================================================================================================ wiring
QBITS = {'hoist_winched': 110880, 'scarab_found': 112202}
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "The cave runs into the mountain and opens on a shaft so tall its top is lost in shadow. Wings beat somewhere far above.",
     'seconds': 7},
    {'id': 'evt:mouth', 'preset': 'exit', 'source': 'exit:mouth', 'title': 'Leave the Gargoyle Eyrie',
     'notes': "To X4's Gargoyle Range in front of its door:xd26 (exit:x4_range)."},
    {'id': 'evt:shaft_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:shaft_floor', 'once': True,
     'text': "Ledges climb the walls of the shaft, one above another, and a rope bridge sags across it high overhead. Grey shapes wheel between them.",
     'seconds': 6},
    {'id': 'evt:fence_door', 'preset': 'door', 'source': 'door:fence', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:fence_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:fence_cache', 'once': True,
     'text': "Crates and sacks stand along the walls, each with a tag on a string: \"Deliver to Asp: one silver mirror.\" \"Deliver to Asp: two candlesticks.\" Someone pays the gargoyles to steal, and keeps the goods here.",
     'seconds': 7},
    {'id': 'evt:tags', 'preset': 'script', 'source': 'panel:tagged_crates', 'title': 'Tagged crates',
     'effects': [{'message': "Each crate has a tag on a string. One tag is a scrap torn from a complaint to the Burlock watch, in a careful hand: \"I know not why they took it, only that gargoyles are hired to steal things for people.\" Under it someone has scrawled: \"Deliver to Asp. Quickly.\""}],
     'notes': "D-4: Carlawna's theft line (aaze0010:9) on the fence's tag."},
    {'id': 'evt:winch', 'preset': 'switch', 'source': 'switch:winch', 'title': 'Winch',
     'condition': {'not': {'qbit': 'hoist_winched'}}, 'closes': ['lift:hoist'], 'sets': {'qbit': 'hoist_winched'},
     'effects': [{'lua': 'evt.PlaySoundName("xeen_winch")'}, {'message': "You crank the winch. A rope runs out through a hole in the rock, and beyond the wall a plank platform comes creaking down on its ropes from the high ledge."}],
     'else_effects': [{'message': "The winch is wound out; the hoist answers its deck and its call ropes now."}],
     'notes': "link:hoist_high (hoist: winch): lowers the hoist the first time and sets hoist_winched."},
    {'id': 'evt:hoist', 'preset': 'switch', 'source': 'lift:hoist', 'title': 'Hoist',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'lua': 'evt.PlaySoundName("xeen_winch")'}, {'message': "The platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The platform hangs on its ropes at the ledge above. Its winch must be in the cave beside you."}]},
    {'id': 'evt:hoist_bottom', 'preset': 'switch', 'source': 'switch:hoist_bottom', 'title': 'Call rope',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'lua': 'evt.PlaySoundName("xeen_winch")'}, {'message': "You pull the rope; the platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The platform hangs on its ropes at the ledge above. Its winch must be in the cave beside you."}]},
    {'id': 'evt:hoist_top', 'preset': 'switch', 'source': 'switch:hoist_top', 'title': 'Call rope',
     'condition': {'qbit': 'hoist_winched'}, 'toggles': ['lift:hoist'],
     'effects': [{'lua': 'evt.PlaySoundName("xeen_winch")'}, {'message': "You pull the rope; the platform creaks on its ropes and moves."}],
     'else_effects': [{'message': "The rope will not run: the hoist's winch in the fence's cave below is still locked."}]},
    {'id': 'evt:moss', 'preset': 'door', 'source': 'door:moss', 'title': 'Hanging moss', 'action': 'open',
     'text': "You push the hanging moss aside. Behind it a crack opens on a hidden ledge."},
    {'id': 'evt:roost_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:roost', 'once': True,
     'text': "The matriarch's roost: a great nest of sticks and bones, heaped with things that glitter.",
     'seconds': 6},
    {'id': 'evt:nest', 'preset': 'script', 'source': 'platform:great_nest', 'title': 'Great nest',
     'effects': [{'lua': 'XeenQuests.hook("q-c10.scarab")'}],
     'notes': "goal:scarab: A3's hook q-c10.scarab gives its text and the Scarab of Imaging (12312) once (scarab_found 112202); later clicks its else text \"The chest is empty.\" (aaze0081:8)."},
    {'id': 'evt:sky_crack', 'preset': 'exit', 'source': 'exit:sky_crack', 'title': 'Climb out through the crack',
     'notes': "One way out to X4: A5's ledge platform high on the peak above the mouth (exit:x4_peak)."},
]
for name, ids in [('chest:fence', 'evt:chest_fence'), ('chest:climber', 'evt:chest_climber'),
                  ('chest:hoard', 'evt:chest_hoard')]:
    events.append({'id': ids, 'preset': 'chest', 'source': name, 'title': 'Chest'})
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd26', 'name': 'Gargoyle Eyrie', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': '7d21', 'seen': [  # D-89 (A7 s28); family s29: MM7's White Cliff Cave, the same cwb1/cfb1 rock
        "a cave mouth opening on a shaft 2,560 high in the peak",
        "rough rock walls round the shaft, ledges climbing it by ladders and a hoist, nests on the ledges",
        "the roost under the split in the peak, daylight through the crack"]},
    'map_code': 'XD-26', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [12, 10], 'climbs': 'n'},
    'map_stats': {'id': 9149, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 31, 'environment': 'cave',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Gargoyle', 'tier': 2, 'per_marker': [2, 3], 'weight': 100}]},
    'neighbours': [
        {'id': 'exit:x4_range', 'to': 'xeen_x4.odm', 'kind': 'door', 'arrival': 'entrance:xd26_eyrie',
         'arrival_hint': "X4's Gargoyle Range in front of door:xd26's cave mouth, facing away from it (south): A5's entrance:xd26_eyrie (-9216, 10752, 1792) facing 1536, moved in front of the mouth (2026-11-21); the ground there is about 1,824.",
         'notes': "X4 (Burlock Savannah), A5's door:xd26. The way out names X4's arrival entrance:xd26_eyrie; the facing comes with it."},
        {'id': 'exit:x4_peak', 'to': 'xeen_x4.odm', 'kind': 'door', 'arrival': [-7424, 14592, 3600],
         'direction': 270,
         'arrival_hint': "X4, A5's ledge platform high on the peak above the mouth, its top 3,593 (measured 2026-11-20), facing south; a path leads down.",
         'notes': "One way out (the sky crack)."},
    ],
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: the Gargoyle Eyrie on X4's Gargoyle Range (Q-C10 The Scarab of Imaging). Monsters: A2's Gargoyles (Cloudside) (slot 1 Xeen Gargoyle: A Gargoyle 11540 16, B Gargoyle Lord 11541 22, C Obsidian Gargoyle 11542 28; markers fix the tier; two placed Obsidian Gargoyles). Map qbits 110880-110919 (used: hoist_winched 110880); A3's q-c10.scarab_found 112202 named. Hook q-c10.scarab called from a lua effect. Music 31. Neighbours on X4 (installed 2026-11-20): the cave mouth (exit:mouth → exit:x4_range, in front of X4's door:xd26) and the one-way sky crack (exit:sky_crack → exit:x4_peak, A5's ledge platform); the map's start is the arrival from X4's door:xd26.",
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
        p['notes'] = f"Xeen design brief, level {lv}: XD-26 Gargoyle Eyrie (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-26 Gargoyle Eyrie, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM)])
# D-89 cave shape (A7 s28, tools/xeen/cave_shape.py): rough walls round the shaft and its ledges, floors that rise and
# fall between the nests, broken roofs; ladders, lifts and nests keep level floor round them. No corner is cut: the
# ledges share short walls with the shaft and with each other.
sys.path.insert(0, str(R / 'tools' / 'xeen'))
import cave_shape  # noqa: E402
cave_shape.shape_l4(BRIEF / 'L4', {
    'room:mouth': {'floor': 48, 'roof': 128},
    'room:shaft_floor': {'floor': 64, 'stalactites': None, 'step': 192},
    'room:low_nests': {'floor': 48, 'roof': 128, 'step': 192},  # s29: finer grids for D-89's 30 % (ledge_e level)
    'room:ledge_low': {'floor': 48, 'roof': 192, 'step': 192},
    'room:ledge_e': {'floor': 0, 'roof': 192},  # the playtest stands the party on it: level
    'room:ledge_w': {'floor': 48, 'roof': 192, 'step': 192},
    'room:hidden_ledge': {'floor': 32, 'roof': 96},
    'room:roost': {'floor': 64, 'roof': 192},
    'room:high_ledge': {'floor': 32},
    'room:sky_crack': {'floor': 32, 'roof': 0},
}, rough={'step': 192, 'depth': 48}, cut=0, step=256)
print('written L4')
