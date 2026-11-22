#!/usr/bin/env python3
"""XD-23 Troll Warren: writes the L1-L4 project folders of devdocs/xeen/briefs/xd23 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd23/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-xd23 after XD-26's gen.py (level_generation/projects/xeen/xd26/gen.py).

Frame: x east, y north, z up. The mouth's exit wall is y 0 (X5's cave mouth faces north, so the warren runs south
into the mound). Three floors: 0 (under the mound), -512 (sleeping tunnels), -1024 (the Matron's hearth). Rooms stand
128 apart (the walls' thickness); the chimney rises from the hearth's floor to the smoke hole at floor 0."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd23'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One texture family, the assigned shipped BLV's (D-89 identity, A7 s29): MM8 d13's troll caves, gtrlwal1 on the walls,
# gtrlrf3 on the roofs, gtrlflr on the floors (until s28 MM7's red-brown dirt, 7dirttyl, the drift D-89 named). Hides (xohide,
# XD-05's), straw (MM6 straw), bark (xdbark, D2's) and bones (xobones, XD-05's) are the trolls' things; the fire burns
# in xoburn and leaves xochar (XD-05's drums). The exits show X5's snow (MM8 snow, XD-10's mouths); poles for the
# chimney's root ladder (t66abc10a, XD-05's and XD-26's ladders); the spring's water (wtrtyl, XD-05's pool).
DIRT = S('gtrlwal1', 128, 256)
ROOF = S('gtrlrf3', 128, 128)
DIRTFLR = S('gtrlflr', 128, 128)
HIDE = S('xohide', 128, 256)
# The texture-fit rule (2026-11-20, merge point 16): xohide (and its burnt xosoot) is a picture meant once: one
# patchwork hide on its pole. Each hung hide is its own panel with the picture laid once over it (`fit`), about as
# wide as half its height (the picture's 128 x 256), the hides of a wall hung apart with the dirt wall between them.
HIDE_FIT = S('xohide', 128, 256, fit=True, uneven=True)
# The hide curtains: two leaves that part sideways, each one whole hide (the right one turned over), stretched over
# a leaf 96 wide (a 192 doorway: the trolls are 160 across, so the doorway stays as wide).
CURTAIN = [[{'texture': 'xohide', 'size': [128, 256]}, {'texture': 'xohide', 'size': [128, 256], 'mirror': True}]]


def hides(first_id, offset, count, width, gap, bottom, height, notes):
    """`count` hung hides along a wall, each its own panel `width` wide (the picture fitted once), `gap` of the dirt
    wall between them. The first keeps `first_id` (its number in ids.lock.yml); the others are `<first_id>_2` on."""
    return [{'id': first_id if i == 0 else f'{first_id}_{i + 1}', 'offset': offset + i * (width + gap),
             'length': width, 'bottom': bottom, 'height': height, 'surface': HIDE_FIT, 'notes': notes}
            for i in range(count)]
STRAW = S('straw', 256, 256)
BARK = S('xdbark', 128, 256)
BONES = S('xobones', 128, 256)
CHAR = S('xochar', 128, 128)
BURN = S('xoburn', 128, 128)
SNOW = S('snow', 128, 128, fit=True, uneven=True)
RUNGS = S('t66abc10a', 32, 128, uneven=True)
WATER = {'texture': 'wtrtyl'}

themes = [
    {'id': 'theme:dirt', 'wall': DIRT, 'floor': DIRTFLR, 'ceiling': ROOF, 'door': HIDE, 'reveal': DIRT,
     'notes': "The warren: MM8 d13's troll caves (D-89), gtrlwal1 walls, gtrlrf3 roofs, gtrlflr floors; hide curtains (xohide) for doors."},
    {'id': 'theme:straw', 'wall': DIRT, 'floor': STRAW, 'ceiling': ROOF, 'door': HIDE, 'reveal': DIRT,
     'notes': "The sleeping hollows and the whelping den: the same dirt, the floor deep in old straw (MM6 straw)."},
]

ROUGH = {'step': 224, 'depth': 72}


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octo(cx, cy, r, ry=None):
    ry = ry or r
    c, cy_ = int(r * 0.41), int(ry * 0.41)
    return [[cx - c, cy - ry], [cx + c, cy - ry], [cx + r, cy - cy_], [cx + r, cy + cy_], [cx + c, cy + ry],
            [cx - c, cy + ry], [cx - r, cy + cy_], [cx - r, cy - cy_]]


def blob(cx, cy, rx, ry):
    """A lumpy hexagon: a heap of bark strips or a straw bed scooped into the floor."""
    return [[cx - rx, cy - ry // 3], [cx - rx // 3, cy - ry], [cx + rx // 2, cy - ry], [cx + rx, cy - ry // 4],
            [cx + rx // 2, cy + ry], [cx - rx // 2, cy + ry]]


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


def bed(id, at, rx, ry, notes):
    return {'id': id, 'outline': blob(at[0], at[1], rx, ry), 'rise': 24, 'surface': STRAW, 'top_surface': STRAW,
            'notes': notes}


def bark(id, at, rx, ry, notes, rise=40):
    return {'id': id, 'outline': blob(at[0], at[1], rx, ry), 'rise': rise, 'surface': BARK, 'top_surface': BARK,
            'notes': notes}


# The chimney: a shaft 768 by 640 east of the hearth, from the hearth's floor (-1024) up to the smoke hole (floor 0)
CH = (2048, -6144, 2816, -5504)
CH_MID_Y = (CH[1] + CH[3]) // 2      # -5824
PLUG_BASE = 480                       # the hide plug's underside above the chimney's floor (-544)
PIT = (2300, CH_MID_Y)                # the fire pit under the chimney

# ------------------------------------------------------------------------------------------------ floor 0
room('room:mouth', 'Warren mouth', outline=rect(-320, -768, 320, 0), floor=0, ceiling=416, theme='theme:dirt',
     ambient=24,
     platforms=[bark('platform:barricade', [180, -120], 96, 64,
                     "What is left of the barricade: frozen hides and gnawed poles dragged aside from the mouth.",
                     rise=32)],
     notes="Inside the mouth, 640 by 768: the barricade of bones and frozen hides the party dragged aside, and the stench. Daylight and snow behind; the gnawing hall opens south, a hide flap west.")
room('room:bone_hall', 'Gnawing hall', outline=rect(-640, -2176, 640, -896), floor=0, ceiling=448,
     ceiling_points=[[0, -1536, 640]], theme='theme:dirt', ambient=18, rough=ROUGH,
     platforms=[bark('platform:bark_gnawed', [-440, -1300], 120, 96,
                     "Strips of the forest's bark, gnawed and spat out (Thickbark's complaint)."),
                bark('platform:bark_hall', [430, -1900], 112, 88, "More gnawed bark, chewed to splinters.")],
     notes="A low hall of beaten dirt, 1,280 square, littered with bones and strips of gnawed bark; the tunnel down leaves its south wall.")
room('room:larder', 'Larder', outline=rect(-1664, -768, -448, 0), floor=0, ceiling=384, theme='theme:dirt',
     ambient=16, rough=ROUGH,
     walls=[{'wall': 'north', 'panels': hides('panel:larder_hides', 224, 3, 136, 40, 64, 256,
                                              "A hide hung up to dry over the carcasses.")}],
     notes="Behind the hide flap, 1,216 by 768: frozen carcasses and hides; the crawlway down leaves its south wall.")
room('room:tunnel_down', 'Tunnel down', path=[[0, -2304], [0, -3328]], width=256, floor=0, slope={'to': -512},
     ceiling=320, ceiling_slope={'to': -192}, theme='theme:dirt', ambient=18,
     notes="A dug tunnel falling 512 south from the gnawing hall to the sleeping hollows.")
room('room:crawl', 'Crawlway', path=[[-1200, -896], [-1200, -1920]], width=224, floor=0, slope={'to': -512},
     ceiling=288, ceiling_slope={'to': -224}, theme='theme:dirt', ambient=16,
     notes="A low crawlway falling 512 south from the larder to the cold spring.")
# ------------------------------------------------------------------------------------------------ floor -512
room('room:spring', 'Cold spring', outline=rect(-1792, -3328, -768, -2048), floor=-512, ceiling=-64,
     ceiling_points=[[-1440, -2560, 64]],
     theme='theme:dirt', ambient=18, rough=ROUGH,
     levels=[{'id': 'level:spring_pool', 'outline': octo(-1440, -2560, 224, 192), 'floor': -560,
              'edge': DIRT, 'surface': WATER,
              'notes': "The meltwater pool where the trolls lick their wounds."}],
     notes="A cave 1,024 by 1,280 round a meltwater pool; the crawlway from the larder comes down its north wall, the slope down to the deep leaves its west wall, the sleeping hollows open south-east.")
room('room:sleeping', 'Sleeping hollows', outline=rect(-1280, -5120, 1024, -3456), floor=-512, ceiling=-96,
     ceiling_points=[[-128, -4288, 160]],
     theme='theme:straw', ambient=16, rough=ROUGH,
     platforms=[
         bed('platform:bed_1', [-1000, -4880], 150, 110, "A straw bed scooped into the floor."),
         bed('platform:bed_2', [-560, -4900], 150, 110, "A straw bed."),
         bed('platform:bed_3', [-100, -4880], 150, 110, "A straw bed."),
         bed('platform:bed_4', [740, -4870], 150, 110, "A straw bed."),
         bed('platform:bed_5', [-1050, -4200], 110, 150, "A straw bed against the west wall."),
         bark('platform:bark_sleeping', [780, -3700], 110, 80, "A gnawed bark pile for the morning."),
     ],
     walls=[{'wall': 'south', 'panels': hides('panel:hides_sleep_s', 880, 3, 160, 32, 32, 320,
                                              "A hide hung on the wall for warmth.")},
            {'wall': 'west', 'panels': hides('panel:hides_sleep_w', 896, 2, 160, 64, 32, 320,
                                             "A hide hung on the wall for warmth.")}],
     notes="The great sleeping cave, 2,304 by 1,664: straw beds scooped into the floor along its walls, hides hung for warmth; the tunnel from the gnawing hall comes in from the north, the cold spring opens north-west, the rock store east.")
room('room:rock_pile', 'Rock store', outline=rect(1152, -4608, 1792, -3968), floor=-512, ceiling=-128,
     theme='theme:dirt', ambient=18, rough=ROUGH,
     notes="A dead-end hollow, 640 square, of what trolls find valuable: fist-sized rocks, bones, hides and a dead hunter's pack.")
room('room:slope', 'Slope down', path=[[-1920, -2688], [-2304, -2688], [-2304, -3712]], width=256, floor=-512,
     slope={'to': -1024}, ceiling=-192, ceiling_slope={'to': -704}, theme='theme:dirt', ambient=16,
     notes="A tunnel falling 512 west and then south from the cold spring to the guard tunnel.")
# ------------------------------------------------------------------------------------------------ floor -1024
room('room:guard_tunnel', 'Guard tunnel', path=[[-2304, -3840], [-2304, -5632], [0, -5632]], width=384,
     floor=-1024, ceiling=-608, theme='theme:dirt', ambient=16,
     notes="The Matron's guards' tunnel, 384 wide: south from the slope, then east to her hearth's hide curtain; the whelping den's curtain in its south side.")
room('room:nursery', 'Whelping den', outline=rect(-1792, -6912, -768, -5952), floor=-1024, ceiling=-608,
     theme='theme:straw', ambient=16, rough=ROUGH,
     platforms=[bed('platform:nest', [-1280, -6560], 220, 150, "A nest of rags and straw for the young trolls.")],
     notes="A dead-end den, 1,024 by 960, behind a hide curtain: the young trolls' nest of rags and straw, and the heap of shiny things they play with.")
room('room:hearth', "The Matron's hearth", outline=rect(128, -6656, 1920, -5248), floor=-1024, ceiling=-448,
     ceiling_points=[[1024, -5952, -224]],
     theme='theme:dirt', ambient=14, rough=ROUGH,
     platforms=[
         bed('platform:matron_bed', [700, -6380], 260, 150, "The Matron's bedding of straw."),
         bark('platform:bark_hearth_1', [1180, -6420], 120, 90, "Bark heaped round her bedding."),
         bark('platform:bark_hearth_2', [300, -6300], 100, 110, "Bark heaped round her bedding."),
     ],
     walls=[{'wall': 'north', 'panels': hides('panel:hides_hearth_n', 384, 3, 224, 48, 32, 416,
                                              "One of the Matron's hides, hung along the north wall.")},
            {'wall': 'south', 'panels': hides('panel:hides_hearth_s', 896, 2, 224, 64, 32, 416,
                                              "A hide hung behind her bedding.")}],
     notes="The deepest hall, 1,792 by 1,408, 1,024 under the mouth: the Matron's bedding of straw and bark along the south wall, her hides hung on the walls, her hoard; the chimney's mouth in the east wall over the fire pit.")
room('room:chimney', 'Smoke chimney', outline=rect(*CH), floor=-1024, ceiling=384, theme='theme:dirt', ambient=12,
     platforms=[
         {'id': 'platform:fire_pit', 'outline': octo(PIT[0], PIT[1], 150), 'rise': 24, 'surface': DIRT,
          'top_surface': BURN, 'notes': "The trolls' fire pit under the chimney."},
         {'id': 'platform:plug', 'outline': rect(CH[0] + 16, CH[1] + 16, CH[2] - 16, CH[3] - 16), 'base': PLUG_BASE,
          'rise': 48, 'surface': BARK, 'top_surface': BARK, 'bottom_surface': BARK,
          'notes': "Frozen hides and gnawed poles rammed up the chimney over the fire pit: the burn takes them out (a destructible). Bark (xdbark), as the mouth's barricade: the hide picture is meant once and a floor-like face does not take `fit`."},
     ],
     notes="The chimney, 768 by 640, rising 1,408 from the fire pit to the smoke hole in the mound's crown; until the burn its hides plug it over the fire. Roots on its east wall make a ladder up.")
room('room:crown', 'Smoke hole', outline=rect(2944, -6080, 3584, -5568), floor=0, ceiling=320, theme='theme:dirt',
     ambient=26,
     notes="The top of the chimney, 640 by 512, under the mound's crown: the smoke hole opens east to the snow.")
# ------------------------------------------------------------------------------------------------ openings
op('open:mouth_bone', 'room:mouth', 'room:bone_hall', link='link:mouth_bone', width=384, height=352)
op('open:mouth_larder', 'room:mouth', 'room:larder', link='link:mouth_larder', width=192, height=256,
   notes="The hide flap into the larder.")
op('open:bone_tunnel', 'room:bone_hall', 'room:tunnel_down', link='link:bone_sleeping', width=224, height=288)
op('open:tunnel_sleeping', 'room:tunnel_down', 'room:sleeping', link='link:bone_sleeping', width=224, height=288)
op('open:larder_crawl', 'room:larder', 'room:crawl', link='link:larder_spring', width=192, height=256)
op('open:crawl_spring', 'room:crawl', 'room:spring', link='link:larder_spring', width=192, height=256)
op('open:spring_sleeping', 'room:spring', 'room:sleeping', link='link:sleeping_spring', width=384, height=384,
   notes="The spring's cave runs into the sleeping hollows.")
op('open:sleeping_rocks', 'room:sleeping', 'room:rock_pile', link='link:sleeping_rocks', width=256, height=320)
op('open:spring_slope', 'room:spring', 'room:slope', link='link:spring_guard', width=224, height=288,
   from_wall='west', to_wall=5)
op('open:slope_guard', 'room:slope', 'room:guard_tunnel', link='link:spring_guard', width=224, height=288)
op('open:guard_nursery', 'room:guard_tunnel', 'room:nursery', link='link:guard_nursery', width=192, height=256,
   notes="The whelping den's hide curtain.")
op('open:guard_hearth', 'room:guard_tunnel', 'room:hearth', link='link:guard_hearth', width=192, height=288,
   notes="The hide curtain over the way into the Matron's hearth.")
op('open:hearth_chimney', 'room:hearth', 'room:chimney', link='link:hearth_fire', width=512, height=448,
   notes="The chimney's mouth over the fire pit.")
op('open:chimney_crown', 'room:chimney', 'room:crown', link='link:hearth_chimney', width=192, height=256,
   notes="The top of the root ladder: a hole 1,024 up into the smoke hole.")
rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:dirt', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-23 Troll Warren: three floors under X5's barrow mound (0, -512, -1024), the chimney from the hearth up to the smoke hole at 0; x east, y north. Written by output/studio_cal/xd23/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {'room:mouth': 0, 'room:bone_hall': 0, 'room:larder': 0, 'room:tunnel_down': 0, 'room:crawl': 0,
          'room:spring': -512, 'room:sleeping': -512, 'room:rock_pile': -512, 'room:slope': -512,
          'room:guard_tunnel': -1024, 'room:nursery': -1024, 'room:hearth': -1024, 'room:chimney': -1024,
          'room:crown': 0}
# (id, name, kind, size, purpose, population [(rank, count)], chest)
PLAN_SPACES = [
    ('room:mouth', 'Warren mouth', 'room', 'S', "Inside the barricade of bones and frozen hides the party pulled aside; the stench.", [('a', 2)], None),
    ('room:bone_hall', 'Gnawing hall', 'room', 'M', "Strips of gnawed bark everywhere (Thickbark's complaint), bones, a tunnel down.", [('a', 4)], None),
    ('room:larder', 'Larder', 'room', 'M', "Frozen carcasses behind a hide flap; a crawlway down to the spring.", [('a', 3)], None),
    ('room:tunnel_down', 'Tunnel down', 'corridor', 'S', "The dug tunnel from the gnawing hall down to the sleeping hollows.", [], None),
    ('room:crawl', 'Crawlway', 'corridor', 'S', "The larder's crawlway down to the cold spring.", [], None),
    ('room:spring', 'Cold spring', 'room', 'M', "A meltwater pool where the trolls lick their wounds; the way down to the deep.", [('a', 2), ('b', 1)], None),
    ('room:sleeping', 'Sleeping hollows', 'room', 'L', "Straw beds in scooped hollows (destructibles that burn); hides hung for warmth.", [('a', 5)], None),
    ('room:rock_pile', 'Rock store', 'room', 'S', "What trolls find valuable: fist-sized rocks, hides, bones, and a dead hunter's pack among them.", [('b', 1)], 3),
    ('room:slope', 'Slope down', 'corridor', 'S', "The tunnel from the cold spring down to the guard tunnel.", [], None),
    ('room:guard_tunnel', 'Guard tunnel', 'corridor', 'M', "The Matron's guards; hide curtains across the tunnel to her hearth and the den.", [('b', 3)], None),
    ('room:nursery', 'Whelping den', 'room', 'M', "Young trolls in a nest of rags; a heap of shiny things they play with (a chest).", [('a', 4)], 3),
    ('room:hearth', "The Matron's hearth", 'room', 'L', "The Matron's bedding of straw and bark round her hearth; her hoard (tier 4). After her death: 'Destroy the lair?'", [('b', 2)], 4),
    ('room:chimney', 'Smoke chimney', 'room', 'S', "The fire pit under a chimney stuffed with hides; roots for handholds up its east wall once the hides burn.", [], None),
    ('room:crown', 'Smoke hole', 'room', 'S', "The top of the chimney, a hole in the mound's crown: out on to X5.", [], None),
]
LEVELS = {'a': [18, 18], 'b': [28, 28]}
TOTAL_ROOMS = len(PLAN_SPACES)


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop, chest in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if pop:
            s['population'] = [{'actor': 11070 if rank == 'a' else 11071, 'groups': n, 'levels': LEVELS[rank],
                                'notes': f"{n} placed {'Trolls' if rank == 'a' else 'Troll Guards'} (rank {rank})."}
                               for rank, n in pop]
        elif sid != 'room:hearth':
            s['empty'] = True
        if sid == 'room:hearth':
            s['population'].append({'actor': 11074, 'role': 'boss', 'groups': 1, 'levels': [32, 32], 'notes': "The Troll Matron 11074 (boss row, frenzy below half health), placed."})
        spaces.append(s)
    links = [
        {'id': 'link:mouth_bone', 'from': 'room:mouth', 'to': 'room:bone_hall', 'kind': 'open'},
        {'id': 'link:mouth_larder', 'from': 'room:mouth', 'to': 'room:larder', 'kind': 'door', 'motion': 'slide',
         'notes': "The hide flap (a destructible door: the burn takes it)."},
        {'id': 'link:bone_sleeping', 'from': 'room:bone_hall', 'to': 'room:sleeping', 'kind': 'ramp',
         'notes': "By the tunnel down (its own room)."},
        {'id': 'link:larder_spring', 'from': 'room:larder', 'to': 'room:spring', 'kind': 'ramp',
         'notes': "By the crawlway (its own room)."},
        {'id': 'link:sleeping_spring', 'from': 'room:sleeping', 'to': 'room:spring', 'kind': 'open'},
        {'id': 'link:sleeping_rocks', 'from': 'room:sleeping', 'to': 'room:rock_pile', 'kind': 'open'},
        {'id': 'link:spring_guard', 'from': 'room:spring', 'to': 'room:guard_tunnel', 'kind': 'ramp',
         'notes': "By the slope down (its own room)."},
        {'id': 'link:guard_nursery', 'from': 'room:guard_tunnel', 'to': 'room:nursery', 'kind': 'door',
         'motion': 'slide', 'notes': "A hide curtain (a destructible door)."},
        {'id': 'link:guard_hearth', 'from': 'room:guard_tunnel', 'to': 'room:hearth', 'kind': 'door',
         'motion': 'slide', 'notes': "A hide curtain (a destructible door)."},
        {'id': 'link:hearth_fire', 'from': 'room:hearth', 'to': 'room:chimney', 'kind': 'open',
         'notes': "The chimney's mouth over the fire pit."},
        {'id': 'link:hearth_chimney', 'from': 'room:chimney', 'to': 'room:crown', 'kind': 'ladder',
         'condition': {'qbit': 'lair_burnt'},
         'notes': "chimney: lair burnt. The hide plug burns out with the lair (a destructible broken by the burn); the root ladder up the chimney's east wall to the smoke hole. Climb only: from above it is the way back down to the hearth."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Tunnels dug under X5's barrow mound, three levels down to the Troll Matron's hearth. Gnawed bark and bones in the halls under the mound, straw beds and hung hides in the sleeping hollows, a cold spring, and at the bottom the Matron by her fire pit under a chimney stuffed with hides. Kill her, and her hearth asks the source's question: destroy the lair? Yes burns it from inside: the beds, the curtains and the bark go up, smoke fills the tunnels, and the burnt-out plug opens the chimney's root ladder to the mound's crown.",
        'purpose': "Q-C15 Troll Problem (Thickbark, X5): A3's hook q-c15.lair at the hearth sets q-c15.lair_burnt (112301). Party 25 to 29, Trolls 18 and Troll Guards 28 (Ice Troll left out), the Troll Matron 32, 28 monsters, treasure level 3 with the hearth's hoard at 4.",
        'mood': "A cave of beaten dirt that stinks of trolls; dim light from the trolls' fires, daylight and snow at the mouth; after the burn, grey smoke and charred hides.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:upper', 'spaces': ['room:mouth', 'room:bone_hall', 'room:tunnel_down', 'room:sleeping',
                                            'room:spring', 'room:crawl', 'room:larder'],
             'notes': "Down the tunnel or down the larder's crawlway."},
            {'id': 'loop:chimney', 'spaces': ['room:mouth', 'room:bone_hall', 'room:tunnel_down', 'room:sleeping',
                                              'room:spring', 'room:slope', 'room:guard_tunnel', 'room:hearth',
                                              'room:chimney', 'room:crown'],
             'notes': "Out up the chimney once the lair burns, back in at the mouth over X5."},
        ],
        'entrances': [
            {'id': 'entrance:x5_mouth', 'space': 'room:mouth', 'kind': 'both', 'neighbour': 'exit:x5_mouth',
             'facing': 's',
             'how': "From and to X5's thing:warren, the barrow mound's mouth in the Troll Forest: just inside the mouth, facing in (south); snow behind."},
            {'id': 'entrance:x5_crown', 'space': 'room:crown', 'kind': 'exit', 'neighbour': 'exit:x5_crown',
             'how': "One way out through the smoke hole, on to the mound's crown on X5 (no way back in)."},
        ],
        'critical_path': ['room:mouth', 'room:bone_hall', 'room:tunnel_down', 'room:sleeping', 'room:spring',
                          'room:slope', 'room:guard_tunnel', 'room:hearth', 'room:chimney'],
        'return_path': ['room:chimney', 'room:crown'],
        'goals': [
            {'id': 'goal:burn', 'space': 'room:hearth', 'kind': 'use', 'story': 'Q-C15',
             'what': "After the Troll Matron's death her fire pit asks 'Destroy the lair?' (aaze0008:2); yes calls A3's hook q-c15.lair.",
             'gives': {'qbit': 'lair_burnt'}},
        ],
        'keys': [{'id': 'key:burn', 'grants': {'qbit': 'lair_burnt'}, 'found_in': 'room:hearth',
                  'how': "Burning the lair at the fire pit (after the Matron) burns the chimney's hide plug out."}],
        'set_pieces': [
            {'id': 'set:burn', 'kind': 'scripted', 'spaces': ['room:hearth', 'room:chimney', 'room:sleeping'],
             'rule': "Yes at the fire pit: the pit and the hearth's hides blaze up and char, every bed, curtain and bark pile of the warren breaks, grey smoke thickens over a minute, the chimney's plug burns out. Every later load: charred, no beds, curtains or bark, no smoke, no trolls."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': TOTAL_ROOMS, 'sectors': TOTAL_ROOMS, 'monsters_about': 28, 'chests': 3, 'doors': 3,
                   'loops': 2, 'floor_area_munits2': 15},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/xd23.graph.yml and D-25 (mockups/act3_a7_decisions.md: the burn's one message, the capped smoke mist, the chimney exit kept). The three slopes are rooms of their own; the graph's chimney is the shaft from the hearth (room:chimney) and its top (room:crown, the smoke hole). 14 rooms and sectors.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-23 Troll Warren (not to scale; side view, north left, south right)

      0   (X5: mound mouth)=exit= [WARREN MOUTH] -- [GNAWING HALL: gnawed bark]          [SMOKE HOLE] =exit, one way= (X5: crown)
                                     |hide flap         | tunnel down                         ^ root ladder (after the burn)
                                  [LARDER]              |                                      |
                                     | crawlway         v                                      |
   -512                        [COLD SPRING] ---- [SLEEPING HOLLOWS: straw beds] -- [rock store, T3]   |
                                     | slope down                                              |
  -1024                        [GUARD TUNNEL] =curtain= [THE MATRON'S HEARTH: Matron, T4] -- [CHIMNEY: fire pit, hide plug]
                                     =curtain= [whelping den, T3]
"""

# ================================================================================================ objects.yml
QBITS = {'matron_dead': 110930, 'lair_burnt': 112301}
HEARTH_FIRE = [2300, CH_MID_Y]
objects = {
    'format': 0,
    'start': {'room': 'room:mouth', 'at': [0, -256], 'facing': 's',
              'notes': "Just inside the mouth from X5's thing:warren, facing in (south); the exit's snow behind."},
    'doors': [
        {'id': 'door:larder_flap', 'opening': 'open:mouth_larder', 'kind': 'slide_left', 'leaves': 2,
         'thickness': 16, 'speed': 192, 'pictures': CURTAIN, 'edge_surface': BARK,
         'notes': "The hide flap over the larder's doorway."},
        {'id': 'door:nursery_curtain', 'opening': 'open:guard_nursery', 'kind': 'slide_left', 'leaves': 2,
         'thickness': 16, 'speed': 192, 'pictures': CURTAIN, 'edge_surface': BARK,
         'notes': "The hide curtain over the whelping den."},
        {'id': 'door:hearth_curtain', 'opening': 'open:guard_hearth', 'kind': 'slide_left', 'leaves': 2,
         'thickness': 16, 'speed': 192, 'pictures': CURTAIN, 'edge_surface': BARK,
         'notes': "The hide curtain over the way into the Matron's hearth."},
    ],
    'ladders': [
        {'id': 'ladder:chimney', 'room': 'room:chimney', 'at': [CH[2] - 8, CH_MID_Y], 'facing': 'e', 'height': 1024, 'floor_height': -1024,
         'exit': [3070, CH_MID_Y], 'grab_at_top': True, 'surface': RUNGS,
         'notes': "Roots for handholds up the chimney's east wall to the smoke hole; the hide plug stops the climb until the burn."},
    ],
    'floors': [
        {'id': 'floor:spring_pool', 'of': 'level:spring_pool', 'kind': 'water',
         'notes': "The cold spring's water (wtrtyl, the fluid bit)."},
    ],
    'destructibles': [],
    'sounds': [
        {'id': 'sound:wind', 'room': 'room:mouth', 'at': [0, -100], 'sound': 'whistling wind', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.5, 'notes': "The wind over the snow at the mouth."},
        {'id': 'sound:drip', 'room': 'room:spring', 'at': [-1440, -2560], 'sound': 'drip01', 'radius': 1400,
         'inner_radius': 400, 'volume': 0.6, 'loop': False, 'wait': [2, 6], 'notes': "Meltwater dripping into the pool."},
        {'id': 'sound:hearth_fire', 'room': 'room:chimney', 'at': HEARTH_FIRE, 'sound': 'campfire', 'radius': 2400,
         'inner_radius': 700, 'volume': 0.7,
         'notes': "The trolls' fire in its pit (off once the lair is burnt: AmbientSound<n> = 2)."},
        {'id': 'sound:blaze', 'room': 'room:hearth', 'at': [1100, -5900], 'sound': 'raging fire loop', 'radius': 3600,
         'inner_radius': 1200, 'volume': 0.9, 'on': False,
         'notes': "The lair burning: on with the burn, off when the hearth's fire has burnt out."},
    ],
    'lights': [
        {'id': 'light:mouth', 'room': 'room:mouth', 'at': [0, -120], 'height': 260, 'radius': 1000,
         'color': [205, 212, 228], 'notes': "Grey snow light from the mouth."},
        {'id': 'light:bone_hall', 'room': 'room:bone_hall', 'at': [0, -1536], 'height': 400, 'radius': 1200,
         'color': [150, 135, 120]},
        {'id': 'light:larder', 'room': 'room:larder', 'at': [-1056, -384], 'height': 300, 'radius': 900,
         'color': [150, 150, 165], 'notes': "Cold light through the frozen hides."},
        {'id': 'light:spring', 'room': 'room:spring', 'at': [-1280, -2688], 'height': 360, 'radius': 1100,
         'color': [140, 155, 175]},
        {'id': 'light:sleeping_w', 'room': 'room:sleeping', 'at': [-640, -4288], 'height': 360, 'radius': 1300,
         'color': [170, 130, 95]},
        {'id': 'light:sleeping_e', 'room': 'room:sleeping', 'at': [512, -4288], 'height': 360, 'radius': 1300,
         'color': [170, 130, 95]},
        {'id': 'light:rock_pile', 'room': 'room:rock_pile', 'at': [1472, -4288], 'height': 300, 'radius': 800,
         'color': [150, 135, 120]},
        {'id': 'light:guard_n', 'room': 'room:guard_tunnel', 'at': [-2304, -4600], 'height': 320, 'radius': 1100,
         'color': [160, 120, 90]},
        {'id': 'light:guard_e', 'room': 'room:guard_tunnel', 'at': [-1000, -5632], 'height': 320, 'radius': 1200,
         'color': [160, 120, 90]},
        {'id': 'light:nursery', 'room': 'room:nursery', 'at': [-1280, -6432], 'height': 320, 'radius': 1000,
         'color': [160, 125, 95]},
        {'id': 'light:hearth', 'room': 'room:hearth', 'at': [1024, -5952], 'height': 450, 'radius': 1500,
         'color': [150, 110, 80]},
        {'id': 'light:hearth_fire', 'room': 'room:chimney', 'at': HEARTH_FIRE, 'height': 120, 'radius': 1500,
         'color': [255, 140, 60], 'pulse': {'intensity': [0.75, 1], 'frequency': 0.9},
         'notes': "The trolls' fire in the pit (a pulsing light: not baked; off once the lair is burnt)."},
        {'id': 'light:blaze_pit', 'room': 'room:chimney', 'at': HEARTH_FIRE, 'height': 200, 'radius': 2400,
         'color': [255, 150, 60], 'on': False, 'pulse': {'intensity': [0.7, 1], 'frequency': 1.6},
         'notes': "The burn: the pit and the chimney's hides ablaze."},
        {'id': 'light:blaze_hearth', 'room': 'room:hearth', 'at': [800, -6200], 'height': 200, 'radius': 2000,
         'color': [255, 140, 50], 'on': False, 'pulse': {'intensity': [0.7, 1], 'frequency': 1.3},
         'notes': "The burn: the Matron's bedding and hides ablaze."},
        {'id': 'light:embers', 'room': 'room:chimney', 'at': HEARTH_FIRE, 'height': 60, 'radius': 700,
         'color': [220, 80, 30], 'on': False, 'pulse': {'intensity': [1, 1], 'frequency': 0.1},
         'notes': "Embers in the pit after the burn (that visit only)."},
        {'id': 'light:chimney_top', 'room': 'room:chimney', 'at': [2432, CH_MID_Y], 'height': 836, 'radius': 900,
         'color': [190, 195, 210], 'notes': "Daylight down the chimney from the smoke hole (above the plug)."},
        {'id': 'light:crown', 'room': 'room:crown', 'at': [3264, -5824], 'height': 260, 'radius': 900,
         'color': [210, 215, 230], 'notes': "Snow light from the smoke hole."},
    ],
    'chests': [
        {'id': 'chest:hunter', 'room': 'room:rock_pile', 'at': [1720, -4500], 'treasure_level': 3,
         'random_items': 2, 'gold': 350, 'notes': "A dead hunter's pack among the trolls' rocks."},
        {'id': 'chest:shiny', 'room': 'room:nursery', 'at': [-860, -6820], 'facing': 'e', 'treasure_level': 3,
         'random_items': 2, 'gold': 400, 'notes': "The heap of shiny things the young trolls play with."},
        {'id': 'chest:hoard', 'room': 'room:hearth', 'at': [1840, -6560], 'treasure_level': 4,
         'random_items': 2, 'gold': 1200, 'trap_level': 3,
         'notes': "The Matron's hoard (the map's hoard, a level up)."},
    ],
    'monsters': [],
    'decorations': [],
    'exits': [
        {'id': 'exit:mouth', 'room': 'room:mouth', 'wall': 'north', 'size': [384, 320], 'surface': S('7solid01', 128, 128, fit=True, uneven=True),
         'to': 'exit:x5_mouth', 'notes': "The mouth onto the Troll Forest's snow (X5)."},
        {'id': 'exit:smoke_hole', 'room': 'room:crown', 'wall': 'east', 'size': [256, 288], 'surface': S('7solid01', 128, 128, fit=True, uneven=True),
         'to': 'exit:x5_crown', 'notes': "The smoke hole: out on to the mound's crown (X5), one way."},
    ],
}

# Monsters: placed, one group per room (shown at stage 0, hidden on every load once the lair is burnt).
TROLL, GUARD, MATRON = 11070, 11071, 11074
PLACED = [
    # room, group, [(monster, at, facing)]
    ('room:mouth', 10, [(TROLL, [-160, -640], 90), (TROLL, [160, -660], 90)]),
    ('room:bone_hall', 11, [(TROLL, [-300, -1100], 90), (TROLL, [300, -1150], 90), (TROLL, [-200, -1800], 90),
                             (TROLL, [250, -1700], 90)]),
    ('room:larder', 12, [(TROLL, [-1400, -200], 0), (TROLL, [-1100, -550], 0), (TROLL, [-800, -250], 0)]),
    ('room:spring', 13, [(TROLL, [-1100, -2400], 90), (TROLL, [-1600, -3050], 90), (GUARD, [-1000, -3000], 90)]),
    ('room:sleeping', 14, [(TROLL, [-800, -4300], 90), (TROLL, [-300, -4500], 90), (TROLL, [200, -4200], 90),
                            (TROLL, [600, -4500], 90), (TROLL, [-100, -3900], 90)]),
    ('room:rock_pile', 15, [(GUARD, [1400, -4250], 180)]),
    ('room:nursery', 16, [(TROLL, [-1500, -6300], 90), (TROLL, [-1050, -6300], 90), (TROLL, [-1650, -6780], 90),
                           (TROLL, [-930, -6560], 90)]),
    ('room:guard_tunnel', 17, [(GUARD, [-2304, -4500], 90), (GUARD, [-1500, -5632], 180), (GUARD, [-500, -5632], 180)]),
    ('room:hearth', 18, [(GUARD, [500, -5600], 180), (GUARD, [500, -6000], 180)]),
]
for room_id, group, ms in PLACED:
    key = room_id.split(':')[1]
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{key}_{n}', 'room': room_id, 'monster': mon, 'at': at,
                                    'facing': facing, 'hostile': True, 'group': group})
objects['monsters'].append({'id': 'monster:matron', 'room': 'room:hearth', 'monster': MATRON, 'at': [1150, -5900],
                            'facing': 180, 'hostile': True, 'group': 19,
                            'notes': "The Troll Matron 32 (A2's boss row 11074, frenzy below half health), by her fire."})
GROUPS = [g for _, g, _ in PLACED] + [19]

# Decorations: bones, skulls, rocks and stalagmites against the walls (D-7 dressing: nothing on a walking line).
DECOS = [
    ('mouth_bones', 'room:mouth', '7dec18', [-240, -100]),
    ('mouth_skull', 'room:mouth', '7dec20', [250, -500]),
    ('bone_bones_1', 'room:bone_hall', '7dec18', [-560, -980]),
    ('bone_bones_2', 'room:bone_hall', 'dec29', [560, -1000]),
    ('bone_skulls', 'room:bone_hall', 'sklplrev', [-560, -2080]),
    ('bone_bones_3', 'room:bone_hall', '7dec18', [560, -1450]),
    ('bone_mite', 'room:bone_hall', 'stlmite2', [-560, -1650]),
    ('larder_bones_1', 'room:larder', 'dec29', [-1580, -80]),
    ('larder_bones_2', 'room:larder', '7dec18', [-1580, -680]),
    ('larder_skull', 'room:larder', '7dec20', [-540, -90]),
    ('spring_mite_1', 'room:spring', 'stlmite1', [-1710, -2130]),
    ('spring_mite_2', 'room:spring', 'stlmite2', [-860, -2140]),
    ('spring_bones', 'room:spring', 'dec29', [-1710, -3250]),
    ('sleep_bones_1', 'room:sleeping', '7dec18', [960, -5050]),
    ('sleep_bones_2', 'room:sleeping', 'dec29', [-1200, -3540]),
    ('sleep_skulls', 'room:sleeping', 'sklplrev', [-1200, -4650]),
    ('rock_1', 'room:rock_pile', '6rock01', [1230, -4040]),
    ('rock_2', 'room:rock_pile', '6rock03', [1330, -4050]),
    ('rock_3', 'room:rock_pile', '6rock05', [1720, -4060]),
    ('rock_bones', 'room:rock_pile', '7dec18', [1230, -4530]),
    ('rock_corpse', 'room:rock_pile', 'Corpse05', [1600, -4520]),
    ('nursery_bones', 'room:nursery', 'dec29', [-1710, -6020]),
    ('nursery_skull', 'room:nursery', '7dec20', [-850, -6030]),
    ('guard_bones', 'room:guard_tunnel', '7dec18', [-2420, -4000]),
    ('guard_skulls', 'room:guard_tunnel', 'sklplrev', [-2420, -5500]),
    ('hearth_bones_1', 'room:hearth', '7dec18', [210, -5330]),
    ('hearth_skulls', 'room:hearth', 'sklplrev', [1840, -5330]),
    ('hearth_bones_2', 'room:hearth', 'dec29', [1500, -6580]),
    ('crown_bones', 'room:crown', 'dec29', [3020, -6010]),
]
for key, room_id, deco, at in DECOS:
    objects['decorations'].append({'id': f'deco:{key}', 'room': room_id, 'decoration': deco, 'at': at,
                                   'floor_height': FLOORS[room_id]})

# Destructibles: the beds, bark piles and hide curtains that the burn breaks (evt.DamageDestructible), and the
# chimney's hide plug (only the burn breaks it).
BEDS = ['platform:bed_1', 'platform:bed_2', 'platform:bed_3', 'platform:bed_4', 'platform:bed_5', 'platform:nest',
        'platform:matron_bed']
BARKS = ['platform:bark_gnawed', 'platform:bark_hall', 'platform:bark_sleeping', 'platform:bark_hearth_1',
         'platform:bark_hearth_2', 'platform:barricade']
CURTAINS = ['door:larder_flap', 'door:nursery_curtain', 'door:hearth_curtain']
BURNABLE = []
for of in BEDS:
    BURNABLE.append({'id': 'destructible:' + of.split(':')[1], 'of': of, 'hp': 20, 'material': 'wood',
                     'notes': "A straw bed: burns with the lair."})
for of in BARKS:
    BURNABLE.append({'id': 'destructible:' + of.split(':')[1], 'of': of, 'hp': 25, 'material': 'wood',
                     'notes': "A pile of gnawed bark: burns with the lair."})
for of in CURTAINS:
    BURNABLE.append({'id': 'destructible:' + of.split(':')[1], 'of': of, 'hp': 30, 'material': 'wood',
                     'notes': "A hide curtain: burns with the lair."})
objects['destructibles'] = BURNABLE + [
    {'id': 'destructible:plug', 'of': 'platform:plug', 'hp': 100, 'material': 'wood', 'trigger_only': True,
     'effect_scale': 2, 'notes': "The chimney's hide plug: only the burn takes it out."}]

# ================================================================================================ wiring.yml
# Every hung hide is its own panel (texture fit, merge point 16): the panels of these walls, read from rooms.
def panel_ids(*firsts):
    ids = [p['id'] for r in rooms for w in r.get('walls', []) for p in w.get('panels', [])]
    return [i for f in firsts for i in ids if i == f or i.startswith(f + '_')]


HIDE_PANELS = panel_ids('panel:hides_sleep_s', 'panel:hides_sleep_w', 'panel:larder_hides')
HEARTH_PANELS = panel_ids('panel:hides_hearth_n', 'panel:hides_hearth_s')
assert len(HIDE_PANELS) == 8 and len(HEARTH_PANELS) == 5
QUESTION = ("The stench of this cave tells you that Trolls have been living in it. It is filled with things that "
            "Trolls find valuable:  Bones, straw beds, fist-sized rocks and hides.  Destroy the lair?")
burn_effects = [{'lua': 'XeenQuests.hook("q-c15.lair")'}]
burn_effects += [{'damage_destructible': {'of': d['id'], 'amount': 1000}} for d in BURNABLE]
burn_effects += [{'destroy': 'destructible:plug'}]
burn_effects += [{'set_texture': {'of': p, 'to': 'xoburn'}} for p in HEARTH_PANELS]
burn_effects += [{'set_texture': {'of': p, 'to': 'xosoot'}} for p in HIDE_PANELS]  # D-33 (6): smoked, not charred
burn_effects += [
    {'lights_off': 'light:hearth_fire'},
    {'lights_on': ['light:blaze_pit', 'light:blaze_hearth']},
    {'set': {'var': {'map_var': 'burning'}, 'value': 1}},
    {'set': {'var': {'map_var': 'smoke'}, 'value': 1}},
    {'lua': "evt.SetMist(1, 60); evt.SetMapVar('AmbientSound{blaze}', 1); evt.SetMapVar('AmbientSound{fire}', 2)"},
]
stage_effects = [{'hide_actors': g} for g in GROUPS]
stage_effects += [{'destroy': d['id']} for d in objects['destructibles']]
stage_effects += [{'set_texture': {'of': p, 'to': 'xosoot'}} for p in HIDE_PANELS]  # D-33 (6)
stage_effects += [{'set_texture': {'of': p, 'to': 'xochar'}} for p in HEARTH_PANELS]
stage_effects += [{'set_texture': {'of': 'platform:fire_pit', 'to': 'xochar', 'face': 'top'}},
                  {'lights_off': 'light:hearth_fire'},
                  {'lua': "evt.SetMapVar('AmbientSound{fire}', 2)"}]

events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "The stench of this cave tells you that Trolls have been living in it.", 'seconds': 5,
     'notes': "The mouth's line (aaze0008:2, its first sentence), as the party comes in (a one-shot timer: the party arrives standing in the mouth)."},
    {'id': 'evt:smoke_clear', 'preset': 'script', 'trigger': 'load',
     'effects': [{'set': {'var': {'map_var': 'smoke'}, 'value': 0}}, {'lua': 'evt.SetMist(0)'}],
     'notes': "D-25 Q5: the smoke mist (atmosphere.yml) is drawn at share 0 on every load; only the burn draws it (evt.SetMist(1, 60)). The map variable smoke mirrors it for the playtest."},
    {'id': 'evt:stage_burnt', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'lair_burnt'},
     'effects': stage_effects,
     'notes': "Stage q-c15.lair_burnt (112301) on every later load: no trolls (every group hidden), every bed, curtain, bark pile and the plug broken (they stay broken in the map's state; broken again here in case), the hung hides smoked black (xosoot, D-33), the hearth's hides and the fire pit charred, the trolls' fire out, no smoke (evt:smoke_clear)."},
    {'id': 'evt:mouth_exit', 'preset': 'exit', 'source': 'exit:mouth', 'title': 'Troll Forest',
     'notes': "Out to X5 in front of the barrow mound's mouth (exit:x5_mouth); the game's leave window (D-24)."},
    {'id': 'evt:smoke_hole', 'preset': 'exit', 'source': 'exit:smoke_hole', 'title': "The mound's crown",
     'notes': "One way out to X5 on the mound's crown (exit:x5_crown, A6's point)."},
    {'id': 'evt:larder_flap', 'preset': 'door', 'source': 'door:larder_flap', 'title': 'Hide flap', 'action': 'open'},
    {'id': 'evt:nursery_curtain', 'preset': 'door', 'source': 'door:nursery_curtain', 'title': 'Hide curtain',
     'action': 'open'},
    {'id': 'evt:hearth_curtain', 'preset': 'door', 'source': 'door:hearth_curtain', 'title': 'Hide curtain',
     'action': 'open'},
    {'id': 'evt:chest_hunter', 'preset': 'chest', 'source': 'chest:hunter', 'title': 'Bag'},
    {'id': 'evt:chest_shiny', 'preset': 'chest', 'source': 'chest:shiny', 'title': 'Chest'},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest'},
    {'id': 'evt:bark', 'preset': 'text', 'source': 'platform:bark_gnawed', 'title': 'Gnawed bark', 'window': True,
     'text': "Strips of the Troll Forest's bark, gnawed and spat out. Thickbark said it: \"They gnaw on our bark to sharpen their teeth in a most uncivilized fashion. Friends don't gnaw on friend's bark.\"",
     'notes': "Thickbark's line (aaze0007:6) on the gnawed bark (D-25 brief)."},
    {'id': 'evt:larder_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:larder', 'once': True,
     'text': "Frozen carcasses lie stacked under the hides: deer, a horse, and things you would rather not name.",
     'seconds': 6},
    {'id': 'evt:rocks_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:rock_pile', 'once': True,
     'text': "This hollow is filled with things that Trolls find valuable: bones, fist-sized rocks and hides. A hunter's pack lies among them.",
     'seconds': 6, 'notes': "aaze0008:2, its second sentence adapted (the trolls' valuables)."},
    {'id': 'evt:hearth_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:hearth', 'once': True,
     'text': "A great hall under the mound, hot and reeking. The Troll Matron rises from her bedding by the fire.",
     'seconds': 6},
    {'id': 'evt:plug', 'preset': 'text', 'source': 'platform:plug', 'title': 'Hides in the chimney',
     'text': "Frozen hides and gnawed poles are rammed up the chimney over the fire. The smoke seeps out round them; nothing else could.",
     'seconds': 6},
    {'id': 'evt:matron_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2,
     'condition': {'kills': {'monster': 'monster:matron'}}, 'once': True,
     'effects': [{'set': {'var': {'map_var': 'matron_dead'}, 'value': 1}}, {'qbit': 'matron_dead'}],
     'text': "The Troll Matron falls. Her fire still burns in its pit under the chimney.", 'seconds': 6,
     'notes': "state:matron (a kill timer, XD-05's drums): her death makes the fire pit ask its question. Sets the map qbit matron_dead (110930) too."},
    {'id': 'evt:fire_pit', 'preset': 'script', 'source': 'platform:fire_pit', 'title': 'Fire pit',
     'condition': {'all': [{'map_var': 'matron_dead'}, {'not': {'qbit': 'lair_burnt'}}]},
     'question': {'message': QUESTION, 'ask': 'Destroy (Yes/No)?', 'answers': ['Yes', 'Y', 'yes', 'y'],
                  'wrong_text': 'You leave the lair as it is, for now.'},
     'effects': burn_effects,
     'else_effects': [{'lua': "if IsQBitSet(QBit(112301)) then evt.StatusText('Ash and charred bones fill the fire pit.', 4) else evt.StatusText(\"The trolls' fire burns in its pit. The Matron is near.\", 4) end"}],
     'notes': "goal:burn / state:burn: after the Matron, the source's question (aaze0008:2) is a real choice (D-25). Yes: A3's hook q-c15.lair (sets lair_burnt 112301, its one message), every bed, curtain and bark pile broken (evt.DamageDestructible), the chimney's plug destroyed, the hearth's hides and pit ablaze (4 s later charred, evt:burn_out), the other hides smoked black (xosoot, D-33), the grey smoke drawn in over 60 s (evt.SetMist(1, 60))."},
    {'id': 'evt:burn_out', 'preset': 'script', 'trigger': 'timer', 'every': 4,
     'condition': {'map_var': {'name': 'burning', 'equals': 1}},
     'effects': [{'set': {'var': {'map_var': 'burning'}, 'value': 2}}]
                + [{'set_texture': {'of': p, 'to': 'xochar'}} for p in HEARTH_PANELS]
                + [{'set_texture': {'of': 'platform:fire_pit', 'to': 'xochar', 'face': 'top'}},
                   {'lights_off': ['light:blaze_pit', 'light:blaze_hearth']}, {'lights_on': 'light:embers'},
                   {'lua': "evt.SetMapVar('AmbientSound{blaze}', 2)"}],
     'notes': "A few seconds after the burn the hearth's hides and the pit are charred; embers glow in the pit."},
]
wiring = {'format': 0, 'variables': ['matron_dead', 'burning', 'smoke'], 'events': events}

atmosphere = {
    'format': 0,
    'mist': {'layer': {'color_rgb': [118, 116, 114], 'base_height': 320, 'falloff_height': 300,
                       'visibility': 1500, 'max_opacity': 0.6, 'noise': 0.45, 'noise_size': 900,
                       'drift': [10, -6], 'follow_daylight': False}},
    'notes': "D-25 Q5: the burn's smoke, a harmless grey mist over all three floors (densest at and below 320). It is drawn at share 0 on every load (evt:smoke_clear) and only the burn draws it in, over 60 s (evt.SetMist(1, 60)). Capped: visibility 1,500 and at most 60 % cover, so a lit wall 1,500 away stays visible (about 38 % covered at the player's 100 %, 52 % at 200 %).",
}

project = {
    'format': 0, 'id': 'xeen_xd23', 'name': 'Troll Warren', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon',
    'identity': {'shape': 'cave', 'family': 'd13', 'seen': [  # D-89 (A7 s29)
        "a dug warren under the barrow mound in MM8's troll-cave rock, rough walls, floors that rise and fall",
        "straw beds and hides hung for warmth in the sleeping hollows, gnawed bark and bones everywhere",
        "the Matron's hearth under the chimney stuffed with hides, the fire pit that burns the lair"]},
    'map_code': 'XD-23', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [12, 14], 'climbs': 'n'},
    'map_stats': {'id': 9146, 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 8, 'environment': 'cave',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Troll', 'tier': 1, 'per_marker': [2, 3], 'weight': 100}]},
    'neighbours': [
        {'id': 'exit:x5_mouth', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [768, -14595, 1210],
         'direction': 90,
         'arrival_hint': "X5's Troll Forest, 400 north of thing:warren's mouth face (768, -14995), facing away from it (north); the ground there is 1,201 (measured 2026-11-20).",
         'notes': "X5 (Winterkill Tundra, A6's): the barrow mound's mouth, thing:warren at cells [65.5, 94.5], turn 180 (its mouth faces north)."},
        {'id': 'exit:x5_crown', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [768, -15616, 1631],
         'direction': 270,
         'arrival_hint': "A6's crown point (2026-11-20): on the mound's crown over its middle, facing south, away from the mouth and the smoke hole (X5 cells [65.5, 94.5]).",
         'notes': "One way out (the smoke hole)."},
    ],
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: XD-23 Troll Warren under X5's barrow mound in the Troll Forest (Q-C15 Troll Problem). Monsters: A2's Trolls, all placed (20 Troll 11070 18, 7 Troll Guard 11071 28; Ice Troll left out) in groups 10-18 by room, and the Troll Matron 11074 (32, boss row, group 19). Slot 1 Xeen Troll for the map card (no rest encounters: encounter 0, the burnt warren stays empty). Map qbits 110930-110939 (used: matron_dead 110930); A3's q-c15.lair_burnt 112301 named. Hook q-c15.lair called from the fire pit's question. Music 8. Neighbours on X5 (installed): the mouth (exit:mouth → exit:x5_mouth, in front of thing:warren) and the one-way smoke hole (exit:smoke_hole → exit:x5_crown, A6's point); the map's start is the arrival from X5's thing:warren.",
}


def fix_sounds(doc):
    """Put the sound numbers of ids.lock.yml into the Lua lines that switch the blaze and the fire sounds."""
    lock = BRIEF / 'L4' / 'ids.lock.yml'
    nums = {}
    if lock.exists():
        L = yaml.safe_load(lock.read_text()) or {}
        nums = L.get('sounds', {}) or {}
    blaze = nums.get('sound:blaze', 0)
    fire = nums.get('sound:hearth_fire', 0)
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    return text.replace('{blaze}', str(blaze)).replace('{fire}', str(fire))


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
        p['notes'] = f"Xeen design brief, level {lv}: XD-23 Troll Warren (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-23 Troll Warren, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', fix_sounds(wiring)),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', atmosphere)])
CAVES = {  # D-89 cave shape (A7 s29, tools/xeen/cave_shape.py): floors that rise and fall, broken corners where no
    # hide hangs (rooms with hung hides keep their walls), vaulted roofs where none is drawn; the tunnels (paths with
    # slopes), the chimney (plug, root ladder) and the smoke hole (exit) stay as they are
    'room:mouth': {'floor': 32, 'roof': 96, 'keep': ('ne', 'nw')},
    'room:bone_hall': {'floor': 64},
    'room:larder': {'floor': 48, 'roof': 96},
    'room:spring': {'floor': 48, 'keep': ('se',)},  # its south wall's opening into the hollows takes 384 of 512
    'room:sleeping': {'floor': 64},
    'room:rock_pile': {'floor': 48, 'roof': 128},
    'room:nursery': {'floor': 48, 'roof': 128},
    'room:hearth': {'floor': 64},
    'room:guard_tunnel': {'path_rough': True},  # 384 wide, level: rough walls (the sloping tunnels stay)
}
sys.path.insert(0, str(R / 'tools' / 'xeen'))
import cave_shape  # noqa: E402
cave_shape.shape_l4(BRIEF / 'L4', CAVES)
print('written L4')
