#!/usr/bin/env python3
"""XD-22 Ninja Pagoda: writes the L1-L4 project folders of devdocs/xeen/briefs/xd22 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt, atmosphere.yml
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd22/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-xd22 after XD-23's gen.py (phase 3) and DD-06's (stacked floors).

Frame: x east, y north, z up. The pagoda's north door (X5's thing:pagoda faces north) is the entry hall's north wall
at y 0; the storeys run south of it, all centred on (0, -1024) as X5's model stacks them, each smaller than the one
below (D-25: inside at most twice the outside in each direction):

  storey   floor   inside (x by y)          X5 outside
  ground       0   3,072 by 2,048 (max)     1,536 by 1,024
  second     512   2,688 by 1,664           1,344 by 832
  third    1,024   2,304 by 1,280           1,152 by 640
  fourth   1,536   1,920 by 896 (+ gallery)   960 by 448
  fifth    2,048   1,664 by 640               832 by 320
  cellar    -448   under the shrine

Rooms are 416 high (slabs 96), walls between rooms 128. Each stair is a stepped room under the storey above, open to
it through its whole ceiling (`in: floor`, XD-09's diamond stair), entered at its low end: east (ground to second),
west (second to third), east behind the crane screen (third to fourth), west (fourth to fifth). The kitchen ladder,
the clan's rope and the cellar ladder go through holes in the floors. The moon gallery runs round the fourth storey's
west and south sides outside its walls, on the third storey's roof under the eaves, open to the sky."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd22'
NEW = '--standin' not in sys.argv     # the two new paper textures, or shipped stand-ins (t2bedsht)


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One family: X5's pagoda shell, MM7's Deyja house timber (hkm2b: fieldstone between blackened beams; hkm2d: the
# plank door), with MM7 Clanker's Laboratory's black timber inside (hwm2rf boards, trim11_32 posts, 7trimd floor
# planks, 7t1cabs furniture, t2bedsht cloth). The cellar is that laboratory's plain stone (hwm2wall, 7tfb11).
# Paper (D-25 Q15): two new textures, xjshoji (a shoji panel) and xjcrane (the crane screen), laid translucent.
STONE = S('hkm2b', 128, 256)
BOARDS = S('hwm2rf', 128, 128)
POST = S('trim11_32', 32, 64)
PLANKS = S('7trimd', 128, 256)
DOOR = S('hkm2d', 160, 320)  # one size per texture in a map (merge point 17): the exit door's
# The 256-wide sliding doors: a pair of leaves with MM7's Deyja house double-door wings (hkm1dl/hkm1dr), one wing each
# (A1's door check, merge point 15: hkm2d is one door's picture and showed 2.5 times across a single leaf).
DOOR2 = [[S('hkm1dl', 128, 256), S('hkm1dr', 128, 256)]]
EXIT_DOOR = S('hkm2d', 160, 320)
CABS = S('7t1cabs', 64, 128)
CLOTH = S('t2bedsht', 128, 256)
STRAW = S('straw', 256, 256)
RUNGS = S('trim11_32', 32, 64, uneven=True)
ROPE = S('straw', 64, 64, uneven=True)
BRONZE = S('xngong', 128, 128, fit=True)
BANNER = S('tap11', 128, 256, fit=True)
CSTONE = S('hwm2wall', 128, 256)
CFLOOR = S('7tfb11', 128, 128)
SKY = dict(BOARDS, sky=True)
PAPER_T = 0.75  # D-33 (5): opacity 0.75 (0.7 if the Shadow Ninjas cannot be made out)
# Texture fit (merge point 16): xjshoji is one shoji panel (a picture meant once, frame top and bottom), so every
# panel of paper shows it once, stretched over a face near its own shape (about 192 x 384), and panels side by side are
# parted by posts of trim11_32 (the screens) or by a pier of the wall (the paper wall); `size` is the picture's own.
# The crane screen's back is one shoji stretched over the square leaf (uneven: seen only through the lit paper).
if NEW:
    PAPER = S('xjshoji', 128, 256, fit=True, uneven=True, translucent=PAPER_T)
    CRANE = S('xjcrane', 256, 256, fit=True, translucent=PAPER_T)
else:
    PAPER = S('t2bedsht', 128, 256, fit=True, uneven=True, translucent=PAPER_T)
    CRANE = S('t2bedsht', 128, 256, fit=True, uneven=True, translucent=PAPER_T)

themes = [
    {'id': 'theme:pagoda', 'wall': BOARDS, 'floor': PLANKS, 'ceiling': BOARDS, 'door': DOOR, 'reveal': BOARDS,
     'bands': [{'height': 256, 'surface': STONE}],
     'notes': "The pagoda's storeys: X5's shell inside out, fieldstone between blackened beams (MM7 hkm2b, the Deyja houses) to 256, black boards above and overhead (hwm2rf), plank floors (7trimd), the shell's plank doors (hkm2d)."},
    {'id': 'theme:stair', 'wall': BOARDS, 'floor': PLANKS, 'ceiling': BOARDS, 'door': DOOR, 'reveal': BOARDS,
     'notes': "The stairs: black boards, plank treads."},
    {'id': 'theme:gallery', 'wall': BOARDS, 'floor': PLANKS, 'ceiling': SKY, 'door': DOOR, 'reveal': BOARDS,
     'bands': [{'height': 256, 'surface': STONE}],
     'notes': "The moon gallery: the storey's timber on its inner walls, open to the sky over its outer walls and overhead."},
    {'id': 'theme:cellar', 'wall': CSTONE, 'floor': CFLOOR, 'ceiling': BOARDS, 'door': DOOR, 'reveal': CSTONE,
     'notes': "The clan's cellar: plain fieldstone (MM7 hwm2wall, Clanker's Laboratory) and dark flags (7tfb11) under the shrine's floor beams."},
]

FL = {0: 0, 1: 512, 2: 1024, 3: 1536, 4: 2048, -1: -448}
H = 416


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# id: (name, outline, storey, ceiling, theme)
ROOMS = {
    # ground storey (0)
    'porch': ("Entry hall", rect(-512, -1024, 512, 0), 0, 448, 'theme:pagoda'),
    'kitchen': ("Monks' kitchen", rect(-1536, -1024, -640, 0), 0, H, 'theme:pagoda'),
    'shrine': ("Shrine hall", rect(-1152, -2048, 1408, -1152), 0, 480, 'theme:pagoda'),
    'stair_e': ("East stair", rect(928, -1024, 1312, -224), 0, 512, 'theme:stair'),
    # cellar (-448)
    'cellar': ("Clan cellar", rect(-768, -2560, 768, -1600), -1, -64, 'theme:cellar'),
    # second storey (512)
    'dojo': ("Dojo", [[-576, -1856], [384, -1856], [384, -192], [-1344, -192], [-1344, -576], [-576, -576]], 1,
             512 + H, 'theme:pagoda'),
    'dorm': ("Sleeping loft", rect(512, -1856, 1344, -192), 1, 512 + H, 'theme:pagoda'),
    'stair_w': ("West stair", rect(-1088, -1600, -704, -704), 1, 1024, 'theme:stair'),
    # third storey (1024)
    'screens': ("Hall of Screens", [[-1152, -1664], [1152, -1664], [1152, -1408], [384, -1408], [384, -384],
                                    [-1152, -384]], 2, 1440, 'theme:pagoda'),
    'stair_c': ("Crane stair", rect(480, -1280, 864, -608), 2, 1536, 'theme:stair'),
    # fourth storey (1536)
    'armoury': ("Armoury", [[256, -1344], [960, -1344], [960, -576], [-768, -576], [-768, -928], [256, -928]], 3,
                1952, 'theme:pagoda'),
    'gallery': ("Moon gallery", [[-1152, -1664], [1152, -1664], [1152, -1472], [-896, -1472], [-896, -576],
                                 [-1152, -576]], 3, 2016, 'theme:gallery'),
    'stair_t': ("Top stair", rect(-768, -1312, 128, -1056), 3, 2048, 'theme:stair'),
    # fifth storey (2048)
    'master': ("Clan master's hall", rect(-832, -1344, 832, -704), 4, 2432, 'theme:pagoda'),
}
FLOOR_OF = {k: FL[v[2]] for k, v in ROOMS.items()}
STAIRS = {
    # room: (to height, toward, the room above)
    'stair_e': (512, 'north', 'dorm'),
    'stair_w': (1024, 'south', 'screens'),
    'stair_c': (1536, 'north', 'armoury'),
    'stair_t': (2048, 'east', 'master'),
}


def walls_of(rid):
    o = ROOMS[rid][1]
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def shared(a, b, walls=None):
    """The pair of facing walls of rooms a and b (DD-06's helper, for any outline); `walls` names the pair."""
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
            if walls and (i, j) != walls:
                continue
            if p0[0] == p1[0] and q0[0] == q1[0]:
                gap = abs(p0[0] - q0[0])
                lo = max(min(p0[1], p1[1]), min(q0[1], q1[1]))
                hi = min(max(p0[1], p1[1]), max(q0[1], q1[1]))
                ax = 1
            elif p0[1] == p1[1] and q0[1] == q1[1]:
                gap = abs(p0[1] - q0[1])
                lo = max(min(p0[0], p1[0]), min(q0[0], q1[0]))
                hi = min(max(p0[0], p1[0]), max(q0[0], q1[0]))
                ax = 0
            else:
                continue
            if hi - lo <= 0 or gap > 512 or gap == 0:
                continue
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx          # the outward normal of a counter-clockwise outline
            if ax == 1 and (q0[0] - p0[0]) * nx <= 0:
                continue
            if ax == 0 and (q0[1] - p0[1]) * ny <= 0:
                continue
            cand = (gap, i, j, lo, hi, ax, p0, p1)
            if best is None or gap < best[0]:
                best = cand
    if best is None:
        raise SystemExit(f'no facing walls between {a} and {b}')
    return best


def opening(oid, a, b, at, width, height, link=None, walls=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b, walls)
    forward = (p1[ax] - p0[ax]) > 0
    along = (at - lo) / (hi - lo) if forward else (hi - at) / (hi - lo)
    d = {'id': oid, 'from': 'room:' + a, 'to': 'room:' + b, 'from_wall': i, 'to_wall': j}
    if link:
        d['link'] = link
    if round(along, 4) != 0.5:
        d['along'] = round(along, 4)
    d['width'] = width
    d['height'] = height
    d.update(kw)
    return d


OPENINGS = [
    opening('open:porch_shrine', 'porch', 'shrine', 0, 256, 256, 'link:porch_shrine'),
    opening('open:porch_kitchen', 'porch', 'kitchen', -640, 256, 256, 'link:porch_kitchen'),
    opening('open:shrine_stair', 'shrine', 'stair_e', 1120, 320, 384, 'link:shrine_dorm',
            notes="The foot of the east stair, in the shrine hall's north wall."),
    {'id': 'open:stair_e_well', 'from': 'room:dorm', 'to': 'room:stair_e', 'in': 'floor', 'link': 'link:shrine_dorm',
     'notes': "The east stair's well: open to the sleeping loft over its whole length."},
    {'id': 'open:cellar_hatch', 'from': 'room:shrine', 'to': 'room:cellar', 'in': 'floor', 'at': [0, -1736],
     'size': [256, 240], 'link': 'link:shrine_cellar', 'reveal': BOARDS,
     'notes': "The trapdoor in front of the altar, under the mat (mover:hatch)."},
    {'id': 'open:kitchen_hatch', 'from': 'room:dojo', 'to': 'room:kitchen', 'in': 'floor', 'at': [-776, -384],
     'size': [240, 256], 'link': 'link:dojo_kitchen', 'reveal': BOARDS,
     'notes': "The kitchen's hatch: a hole in the dojo's floor over the kitchen ladder."},
    opening('open:dojo_dorm_door', 'dojo', 'dorm', -1400, 256, 256, 'link:dorm_dojo',
            notes="The sliding door between the dojo and the sleeping loft."),
    opening('open:dojo_dorm_paper', 'dojo', 'dorm', -448, 192, 384, 'link:dorm_dojo_paper',
            notes="The paper wall between the dojo and the sleeping loft, its north panel: a breakable screen (door:paper_dorm)."),
    opening('open:dojo_dorm_paper2', 'dojo', 'dorm', -672, 192, 384, 'link:dorm_dojo_paper',
            notes="The paper wall's south panel, a pier of the wall between (door:paper_dorm2)."),
    opening('open:dojo_stair', 'dojo', 'stair_w', -896, 320, 384, 'link:dojo_screens',
            notes="The foot of the west stair."),
    {'id': 'open:stair_w_well', 'from': 'room:screens', 'to': 'room:stair_w', 'in': 'floor',
     'link': 'link:dojo_screens', 'notes': "The west stair's well, open to the Hall of Screens."},
    opening('open:screens_crane', 'screens', 'stair_c', 672, 352, 352, 'link:screens_armoury', walls=(2, 0),
            notes="Behind the crane screen (door:crane): the stair up to the armoury."),
    {'id': 'open:stair_c_well', 'from': 'room:armoury', 'to': 'room:stair_c', 'in': 'floor',
     'link': 'link:screens_armoury', 'notes': "The crane stair's well, open to the armoury."},
    opening('open:armoury_gallery', 'armoury', 'gallery', -752, 160, 320, 'link:armoury_gallery', walls=(3, 3),
            notes="The armoury's door out to the moon gallery."),
    opening('open:gallery_stair', 'gallery', 'stair_t', -1184, 224, 320, 'link:gallery_master',
            notes="The foot of the top stair, off the gallery's west walk."),
    {'id': 'open:stair_t_well', 'from': 'room:master', 'to': 'room:stair_t', 'in': 'floor',
     'link': 'link:gallery_master', 'notes': "The top stair's well, open to the clan master's hall."},
    {'id': 'open:rope_slot', 'from': 'room:gallery', 'to': 'room:screens', 'in': 'floor', 'at': [1056, -1568],
     'size': [160, 160], 'link': 'link:gallery_rope', 'reveal': BOARDS,
     'notes': "The slot in the gallery's floor at its east end where the clan's rope hangs down into the Hall of Screens."},
]


def plat(id, at, size, rise, surface, top=None, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if id:
        d = {'id': id, **d}
    if top:
        d['top_surface'] = top
    d.update(kw)
    return d


def screen(name, axis, c, posts, notes, shared=()):
    """A free-standing paper screen of the Hall of Screens along x (axis 'x', at y = c) or y (at x = c): square black
    posts (trim11_32, 24 thick; `posts` = [(centre, length)] along the screen) with a panel of translucent paper 16
    thick between each two, the shoji laid once per panel. Each panel is its own platform and breaks alone; the posts
    stand. The first panel keeps the screen's id (platform:<name>), the others platform:<name>_2, _3 ...
    shared: the indices of posts that are another screen's (a corner or a T) and are not laid again."""
    def box(a, b, half):
        return rect(a, c - half, b, c + half) if axis == 'x' else rect(c - half, a, c + half, b)
    panels, frame = [], []
    for k, (p, ln) in enumerate(posts):
        if k not in shared:
            frame.append({'outline': box(p - ln // 2, p + ln // 2, 12), 'rise': 384, 'surface': POST,
                          'notes': f"A post of {name}'s frame."})
        if k:
            q, qn = posts[k - 1]
            pid = f'platform:{name}' if k == 1 else f'platform:{name}_{k}'
            a, b = q + qn // 2, p - ln // 2
            at, size = ([(a + b) // 2, c], [b - a, 16]) if axis == 'x' else ([c, (a + b) // 2], [16, b - a])
            panels.append({'id': pid, 'at': at, 'size': size, 'rise': 384, 'surface': PAPER,
                           'end_surface': dict(POST, fit=False), 'top_surface': POST, 'notes': notes if k == 1 else
                           f"{notes.split(':')[0].rstrip('.')}: panel {k}."})
    return panels, frame


def panel(id, offset, length, bottom, height, surface, notes):
    d = {'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface, 'notes': notes}
    if id:
        d = {'id': id, **d}
    return d


# The Hall of Screens' maze (third storey, floor 1024). The west stair comes up in the hall's west part; the crane
# screen closes the south-east alcove. Row A (y -1360) and the cross screen (x 0) close the straight way east along
# the south side; the way round runs north through the gap west of row A, east along the middle band (two Ninjas) and
# back south through row A's east gap. Two cells of screens on the north wall hold the Shadow Ninjas behind paper.
SCREENS = [
    # Row A from x -464 to 208; its post at x 0 is the cross screen's north end (a T).
    screen('screen_a', 'x', -1360, [(-452, 24), (-226, 24), (0, 24), (196, 24)],
           "Row A: a long paper screen across the hall's south side."),
    screen('screen_x', 'y', 0, [(-1620, 56), (-1360, 24)],
           "The cross screen: closes the hall's south walk at its middle.", (1,)),
    screen('screen_b', 'x', -1104, [(-660, 24), (-470, 24), (-280, 24), (-90, 24), (100, 24)],
           "Row B: a paper screen across the hall's middle."),
    screen('cell1_s', 'x', -784, [(-664, 24), (-448, 24), (-232, 24)],
           "Cell 1, its south side: shadows move behind it."),
    screen('cell1_e', 'y', -232, [(-784, 24), (-598, 24), (-412, 24)], "Cell 1, its east side.", (0,)),
    screen('cell1_w', 'y', -664, [(-784, 24), (-598, 24), (-412, 24)], "Cell 1, its west side over the stair well.",
           (0,)),
    screen('cell2_s', 'x', -784, [(-56, 24), (150, 24), (356, 24)],
           "Cell 2, its south side: shadows move behind it."),
    screen('cell2_w', 'y', -56, [(-784, 24), (-598, 24), (-412, 24)], "Cell 2, its west side.", (0,)),
]
MAZE = [p for panels, _ in SCREENS for p in panels]
MAZE_POSTS = [p for _, frame in SCREENS for p in frame]

EXTRA = {
    'porch': {
        'platforms': [
            plat('platform:bell', [400, -48], [96, 96], 112, BRONZE, POST, base=208,
                 notes="The monks' bronze bell, hung from a beam in the north-east corner."),
            plat(None, [400, -48], [16, 16], 128, POST, POST, base=320, notes="The bell's hanger, up to the beam."),
            plat('platform:broom', [-300, -560], [176, 12], 10, POST, POST,
                                              notes="Kai Wu's broom, dropped on the floor: the handle."),
            plat(None, [-180, -560], [48, 40], 14, STRAW, STRAW, notes="The broom's straw head."),
        ],
        'notes': "Inside the barred north door, 1,024 square: the monks' bell in the north-east corner, Kai Wu's broom where he dropped it. Doors to the kitchen (west) and the shrine hall (south).",
    },
    'kitchen': {
        'platforms': [plat('platform:hearth', [-1440, -880], [160, 192], 64, STONE, CFLOOR,
                           notes="The kitchen's cooking hearth against the west wall."),
                      plat('platform:kitchen_table', [-1120, -160], [320, 128], 72, CABS, CABS,
                           notes="A low table along the north wall, rice jars smashed on it.")],
        'notes': "Kai Wu's old kitchen: the hearth, the low table, smashed rice jars; a ladder up the east wall to a hatch into the dojo.",
    },
    'shrine': {
        'platforms': [plat('platform:altar', [0, -1968], [448, 128], 112, BOARDS, CABS,
                           notes="Kai Wu's altar against the south wall.")],
        'walls': [{'wall': 'south', 'panels': [panel('panel:clan_mark', 1072, 160, 128, 320, BANNER,
                                                     "The clan's mark hung over the altar: a black banner with a carrion bird.")]}],
        'notes': "Kai Wu's shrine, 2,560 by 896: the altar on the south wall under the clan's black banner, the mat in front of it over the cellar hatch; the east stair up leaves the north wall's east end.",
    },
    'stair_e': {'notes': "Sixteen steps up north from the shrine hall to the sleeping loft, open above."},
    'cellar': {
        'platforms': [plat('platform:cushion', [-380, -2360], [128, 128], 16, CLOTH, CLOTH,
                           notes="A cushion on the cellar floor: where Shinobu sits once the pagoda is Kai Wu's again."),
                      plat('platform:rope_coils', [640, -1720], [128, 128], 48, STRAW, STRAW,
                           notes="Coils of rope against the north wall."),
                      plat('platform:cloth_bolts', [640, -2440], [128, 192], 64, CLOTH, CLOTH,
                           notes="Bolts of black cloth (the clan's) stacked in the south-east corner.")],
        'notes': "The clan's storeroom under the shrine, 1,536 by 960: rope, black cloth, rice, a chest; the ladder up to the hatch on the north wall.",
    },
    'dojo': {
        'platforms': [plat(f'platform:target_{i}', at, [48, 48], 224, STRAW, STRAW,
                           notes="A straw target on a post, bristling with shuriken.")
                      for i, at in enumerate(([-240, -1700], [-40, -1700], [160, -1700]), 1)]
        + [plat('platform:weapon_wall', [360, -1100], [32, 384], 256, CABS, CABS,
                notes="The weapon wall: a rack of wooden practice blades along the east wall.")],
        'notes': "The training floor, an L 1,728 by 1,664: straw targets along the south wall, the weapon wall; the sliding door and the paper wall east to the sleeping loft, the west stair up in the north-west, the kitchen's hatch in the floor of the north wing.",
    },
    'dorm': {
        'platforms': [plat(f'platform:mat_{i}', [x, y], [128, 256], 8, CLOTH, CLOTH,
                           notes="A sleeping mat.")
                      for i, (x, y) in enumerate(((700, -1720), (880, -1720), (1060, -1720), (1240, -1720),
                                                  (700, -1300), (880, -1300)), 1)],
        'notes': "The sleeping loft, 832 by 1,664: rolled mats in rows at its south end; the east stair comes up in its east side; the sliding door and the paper wall west to the dojo.",
    },
    'stair_w': {'notes': "Sixteen steps up south from the dojo to the Hall of Screens, open above."},
    'screens': {
        'platforms': MAZE + MAZE_POSTS,
        'notes': "The middle storey, 2,304 by 1,280: a maze of paper screens lit from behind, so shapes move on the paper; the west stair comes up in its west side; the crane screen closes the stair up in the south-east alcove, where the clan's rope comes down.",
    },
    'stair_c': {'notes': "Sixteen steps up north from behind the crane screen to the armoury, open above."},
    'armoury': {
        'platforms': [plat(f'platform:rack_{i}', at, size, 192, CABS, POST,
                           notes="A rack of blades, bows and shuriken.")
                      for i, (at, size) in enumerate((([-600, -608], [256, 32]), ([-200, -608], [256, 32]),
                                                      ([300, -608], [64, 32])), 1)],
        'notes': "Racks of blades, bows and shuriken in the west wing; the crane stair comes up in the east part; the door west to the moon gallery.",
    },
    'gallery': {
        'walls': [{'wall': 0, 'surface': SKY, 'bands': False}, {'wall': 1, 'surface': SKY, 'bands': False},
                  {'wall': 5, 'surface': SKY, 'bands': False}],
        'parapets': [{'path': [[944, -1632], [-1120, -1632], [-1120, -608]], 'height': 112, 'thickness': 16,
                      'surface': BOARDS, 'notes': "The railing along the outer edge, the mere below."}],
        'notes': "A railed walk round the fourth storey's west and south sides under the eaves, open to the sky over the frozen mere: the armoury's door and the top stair off its west walk, the slot for the clan's rope at the south walk's east end.",
    },
    'stair_t': {'notes': "Sixteen steps up east from the gallery to the clan master's hall, open above."},
    'master': {
        'levels': [{'id': 'level:dais', 'outline': rect(-256, -960, 512, -720), 'floor': 2096, 'edge': BOARDS,
                    'surface': PLANKS, 'notes': "The dais along the north wall."}],
        'walls': [{'wall': 'north', 'panels': [panel('panel:gong', 592, 224, 160, 224, BRONZE,
                                                     "The clan's gong on the north wall behind the dais."),
                                               panel(None, 352, 160, 96, 320, BANNER, "The clan's banner."), panel(None, 912, 160, 96, 320, BANNER, "The clan's banner.")]}],
        'ceiling_levels': [{'ceiling': 2816, 'top_scale': [0.6, 0.2],
                            'notes': "The steep top roof's hipped ceiling."}],
        'notes': "Under the steep top roof, 1,664 by 640: a dais along the north wall under the clan's gong and banner; the clan master and his Ninja Master; the strongbox behind the dais. The top stair comes up in its south-west.",
    },
}


def room_doc(rid):
    name, outline, storey, ceiling, theme = ROOMS[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline, 'floor': FL[storey], 'ceiling': ceiling,
         'theme': theme}
    if rid in STAIRS:
        to, toward, _ = STAIRS[rid]
        d['slope'] = {'to': to, 'toward': toward, 'steps': 16, 'riser': BOARDS, 'tread': PLANKS}
    e = dict(EXTRA.get(rid, {}))
    notes = e.pop('notes', '')
    d.update(e)
    d['notes'] = notes
    return d


rooms = [room_doc(r) for r in ROOMS]
for r in rooms:
    if r['id'] == 'room:cellar':
        r['store'] = True
rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:pagoda', 'ambient': 22}, 'rooms': rooms,
             'openings': OPENINGS,
             'notes': "XD-22 Ninja Pagoda: five storeys 512 apart (0, 512, 1,024, 1,536, 2,048) and the cellar (-448), each storey smaller than the one below, centred on (0, -1024); x east, y north. Written by output/studio_cal/xd22/tools/gen.py."}

# ================================================================================================ plan.yml
# (id, name, kind, size, purpose, population [(rank, count)], chest)
PLAN_SPACES = [
    ('room:porch', 'Entry hall', 'room', 'S', "Inside the barred door: the monks' bell, Kai Wu's broom where he dropped it.", [('a', 2)], None),
    ('room:kitchen', "Monks' kitchen", 'room', 'S', "Kai Wu's old kitchen, the rice jars smashed; a ladder up through a hatch into the dojo.", [('a', 2)], None),
    ('room:shrine', 'Shrine hall', 'room', 'M', "Kai Wu's shrine, defiled: the clan's mark over the altar; the east stair up; a draught under the altar mat.", [('a', 3)], None),
    ('room:stair_e', 'East stair', 'corridor', 'S', "From the shrine hall up to the sleeping loft.", [], None),
    ('room:cellar', 'Clan cellar', 'room', 'M', "The clan's storeroom: rope, black cloth, rice, a chest. After q-c4.done Shinobu and the clan's survivors sit here (T2-CLAN).", [], 3),
    ('room:dorm', 'Sleeping loft', 'room', 'M', "Rolled mats in rows; a sliding door and a paper wall to the dojo, ninjas behind the paper.", [('a', 3)], None),
    ('room:dojo', 'Dojo', 'room', 'L', "The training floor: straw targets bristling with shuriken, a weapon wall; the west stair up and the kitchen hatch down.", [('a', 5)], None),
    ('room:stair_w', 'West stair', 'corridor', 'S', "From the dojo up to the Hall of Screens.", [], None),
    ('room:screens', 'Hall of Screens', 'room', 'L', "A maze of paper screens lit from behind, shapes moving on the paper; the stair up shows through the crane screen.", [('b', 4), ('a', 2)], None),
    ('room:stair_c', 'Crane stair', 'corridor', 'S', "Behind the crane screen, up to the armoury.", [], None),
    ('room:armoury', 'Armoury', 'room', 'M', "Racks of blades, bows and shuriken; a chest of the clan's best.", [('b', 2)], 3),
    ('room:gallery', 'Moon gallery', 'corridor', 'M', "A railed walk round the fourth storey under the eaves, open to the sky over the mere; the stair to the top and the clan's climbing rope down.", [('a', 2)], None),
    ('room:stair_t', 'Top stair', 'corridor', 'S', "From the gallery up to the clan master's hall.", [], None),
    ('room:master', "Clan master's hall", 'room', 'M', "Under the steep top roof: a dais, a gong, the clan's banner. The clan master and his Ninja Master; the clan's strongbox behind the dais.", [('c', 1)], 4),
]
LEVELS = {'a': [22, 22], 'b': [30, 30], 'c': [40, 40]}
ACTOR = {'a': 11120, 'b': 11121, 'c': 11122}
NAME = {'a': 'Ninja', 'b': 'Shadow Ninja', 'c': 'Ninja Master'}


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pop, chest in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': FLOOR_OF[sid.split(':')[1]],
             'purpose': purpose}
        if pop:
            s['population'] = [{'actor': ACTOR[rank], 'groups': n, 'levels': LEVELS[rank],
                                'notes': f"{n} placed {NAME[rank]} (rank {rank})."} for rank, n in pop]
        if sid == 'room:master':
            s['population'].append({'actor': 11123, 'role': 'boss', 'groups': 1, 'levels': [42, 42],
                                    'notes': "The Clan Master 11123 (boss row, blink on hit 0.2), placed."})
        if sid == 'room:cellar':
            s['population'] = [{'actor': 11124, 'groups': 5, 'levels': [22, 22],
                                'notes': "Shinobu (NPC 4530) and four Clan Survivors (11124, faction clan, friendly), placed hidden and shown only with q-c4.done; not counted."}]
        if 'population' not in s:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:porch_shrine', 'from': 'room:porch', 'to': 'room:shrine', 'kind': 'door', 'motion': 'slide'},
        {'id': 'link:porch_kitchen', 'from': 'room:porch', 'to': 'room:kitchen', 'kind': 'door', 'motion': 'slide'},
        {'id': 'link:shrine_cellar', 'from': 'room:shrine', 'to': 'room:cellar', 'kind': 'ladder',
         'notes': "The hatch under the altar mat (a mover that slides aside: 'A draught comes up between the floorboards.') and a ladder down."},
        {'id': 'link:shrine_dorm', 'from': 'room:shrine', 'to': 'room:dorm', 'kind': 'stairs',
         'notes': "The east stair (its own room, open above)."},
        {'id': 'link:dorm_dojo', 'from': 'room:dorm', 'to': 'room:dojo', 'kind': 'door', 'motion': 'slide',
         'notes': "The sliding door."},
        {'id': 'link:dorm_dojo_paper', 'from': 'room:dorm', 'to': 'room:dojo', 'kind': 'secret_door',
         'notes': "The paper wall: a breakable screen (D-25 Q15); ninjas wait behind it."},
        {'id': 'link:dojo_kitchen', 'from': 'room:dojo', 'to': 'room:kitchen', 'kind': 'ladder',
         'notes': "The kitchen ladder through a hatch in the dojo's floor."},
        {'id': 'link:dojo_screens', 'from': 'room:dojo', 'to': 'room:screens', 'kind': 'stairs',
         'notes': "The west stair (its own room, open above)."},
        {'id': 'link:screens_armoury', 'from': 'room:screens', 'to': 'room:armoury', 'kind': 'stairs',
         'notes': "Behind the crane screen (a breakable paper screen: struck or clicked it falls), the crane stair."},
        {'id': 'link:armoury_gallery', 'from': 'room:armoury', 'to': 'room:gallery', 'kind': 'door',
         'motion': 'slide'},
        {'id': 'link:gallery_master', 'from': 'room:gallery', 'to': 'room:master', 'kind': 'stairs',
         'notes': "The top stair (its own room, open above)."},
        {'id': 'link:gallery_rope', 'from': 'room:gallery', 'to': 'room:screens', 'kind': 'ladder',
         'notes': "The clan's climbing rope through a slot in the gallery's floor into the Hall of Screens' south-east alcove."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Kai Wu's pagoda on the frozen mere's shore, taken by the ninja clan: five storeys of dark timber, each smaller than the one below, stairs alternating sides. The defiled shrine, a dojo and a sleeping loft, the Hall of Screens where shadows move behind lit paper and the stair up shows through a screen painted with a crane, the armoury and a moon gallery under the eaves open to the sky, and at the top the clan master's hall. The clan's cellar lies under the shrine's altar mat.",
        'purpose': "Q-C4 The Ninja Pagoda (Kai Wu, X5; T1-D Monk to Initiate): the clan master's death runs A3's hook q-c4.clan_master (clan_master_slain 112081). T2-CLAN: after q-c4.done (112082) Shinobu (NPC 4530) and four Clan Survivors sit in the cellar. Party 25 to 29; Ninja 22, Shadow Ninja 30, Ninja Master 40 and the Clan Master 42; 27 monsters; treasure level 3, the strongbox 4.",
        'mood': "Dark timber and paper, lamp-lit; cold air from the gallery; the clan's black banners.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:lower', 'spaces': ['room:porch', 'room:shrine', 'room:stair_e', 'room:dorm', 'room:dojo',
                                            'room:kitchen'],
             'notes': "Up the east stair, down the kitchen ladder."},
            {'id': 'loop:upper', 'spaces': ['room:screens', 'room:stair_c', 'room:armoury', 'room:gallery'],
             'notes': "Up behind the crane, back down the clan's rope."},
        ],
        'entrances': [
            {'id': 'entrance:x5_door', 'space': 'room:porch', 'kind': 'both', 'neighbour': 'exit:x5_pagoda',
             'facing': 's', 'how': "From and to X5's thing:pagoda, its north door: just inside, facing in (south)."},
        ],
        'critical_path': ['room:porch', 'room:shrine', 'room:stair_e', 'room:dorm', 'room:dojo', 'room:stair_w',
                          'room:screens', 'room:stair_c', 'room:armoury', 'room:gallery', 'room:stair_t',
                          'room:master'],
        'return_path': ['room:master', 'room:stair_t', 'room:gallery', 'room:screens', 'room:stair_w', 'room:dojo',
                        'room:kitchen', 'room:porch'],
        'goals': [
            {'id': 'goal:clan_master', 'space': 'room:master', 'kind': 'kill', 'story': 'Q-C4',
             'what': "The clan master (11123): his death runs A3's q-c4.clan_master (a kill timer).",
             'gives': {'qbit': 112081}},
        ],
        'set_pieces': [
            {'id': 'set:screens', 'kind': 'ambush', 'spaces': ['room:screens', 'room:dorm'],
             'rule': "Paper screens (breakable, translucent): ninjas wait behind them, seen as shapes on the lit paper, and step out when a screen breaks."},
            {'id': 'set:clan_return', 'kind': 'scripted', 'spaces': ['room:cellar'],
             'rule': "On every load with q-c4.done (112082): the clan's surviving hostile ninjas hidden, the cellar hatch open, Shinobu and four Clan Survivors shown in the cellar."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(PLAN_SPACES), 'sectors': len(PLAN_SPACES), 'monsters_about': 27, 'chests': 3,
                   'doors': 7, 'loops': 2, 'floor_area_munits2': 15},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/xd22.graph.yml and D-25 (mockups/act3_a7_decisions.md: Shinobu's survivors a peaceful row, the done stage, inside at most twice the outside, the paper screens per Q15). The four stairs are rooms of their own (open above); 14 rooms.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-22 Ninja Pagoda (not to scale; side view, storeys stacked, each smaller than the one below)

  2048  fifth             [CLAN MASTER'S HALL: dais, gong, banner; Clan Master, Ninja Master; strongbox T4]
                                   ^ top stair (west)
  1536  fourth   [MOON GALLERY, open to the sky] =door= [ARMOURY: racks, T3]
                    | rope down (east end)                  ^ crane stair (east)
  1024  third            [HALL OF SCREENS: paper maze] ==crane screen==/
                                   ^ west stair
   512  second       [DOJO: targets] =sliding door / paper wall= [SLEEPING LOFT: mats]
                       | hatch, ladder down                          ^ east stair
     0  ground   [KITCHEN] =door= [ENTRY HALL: bell, broom] =exit= (X5: the pagoda's north door)
                                   =door=
                                 [SHRINE HALL: altar, mat] (east stair up)
                                   | hatch under the mat, ladder
  -448  cellar                   [CLAN CELLAR: T3; Shinobu after q-c4.done]
"""

# ================================================================================================ objects.yml
objects = {
    'format': 0,
    'start': {'room': 'room:porch', 'at': [0, -256], 'facing': 's',
              'notes': "Just inside the pagoda's north door from X5's thing:pagoda, facing in (south)."},
    'doors': [
        {'id': 'door:porch_shrine', 'opening': 'open:porch_shrine', 'kind': 'slide_left', 'leaves': 2,
         'pictures': DOOR2, 'speed': 192, 'notes': "A plank door (the shell's hkm2d) into the shrine hall."},
        {'id': 'door:porch_kitchen', 'opening': 'open:porch_kitchen', 'kind': 'slide_left', 'leaves': 2,
         'pictures': DOOR2, 'speed': 192, 'notes': "A plank door into the kitchen."},
        {'id': 'door:dojo_dorm', 'opening': 'open:dojo_dorm_door', 'kind': 'slide_left', 'leaves': 2,
         'pictures': DOOR2, 'speed': 192,
         'notes': "The sliding door between the dojo and the sleeping loft."},
        {'id': 'door:armoury', 'opening': 'open:armoury_gallery', 'kind': 'hinged',
         'surface': EXIT_DOOR, 'speed': 192, 'notes': "The armoury's plank door out to the gallery."},
        # The paper screens (D-25 Q15, the breakable-window route): a door leaf with no event, translucent paper,
        # and a destructible of it. They never open; breaking one takes its faces away.
        {'id': 'door:paper_dorm', 'opening': 'open:dojo_dorm_paper', 'kind': 'slide_right', 'travel': 16,
         'thickness': 16, 'surface': PAPER,
         'notes': "The paper wall between the dojo and the sleeping loft, its north panel: never opens; breaks (destructible:paper_dorm)."},
        {'id': 'door:paper_dorm2', 'opening': 'open:dojo_dorm_paper2', 'kind': 'slide_left', 'travel': 16,
         'thickness': 16, 'surface': PAPER,
         'notes': "The paper wall's south panel: never opens; breaks (destructible:paper_dorm2)."},
        {'id': 'door:crane', 'opening': 'open:screens_crane', 'kind': 'slide_right', 'travel': 64,
         'thickness': 16, 'surface': CRANE, 'back_surface': dict(PAPER, uneven=True),
         'notes': "The crane screen: the stair up shows through it; clicked or struck it breaks (destructible:crane)."},
    ],
    'movers': [
        {'id': 'mover:hatch', 'room': 'room:shrine', 'at': [0, -1736], 'size': [288, 272], 'floor_height': 0,
         'height': 24, 'travel': [-352, 0, 0], 'speed': 128, 'surface': BOARDS, 'top_surface': STRAW,
         'notes': "The altar mat over the cellar hatch: a straw mat on a plank lid, which slides aside west."},
    ],
    'ladders': [
        {'id': 'ladder:cellar', 'room': 'room:cellar', 'at': [0, -1626], 'facing': 'n', 'height': 448,
         'exit': [0, -1520], 'surface': RUNGS, 'notes': "The cellar ladder up to the hatch under the altar mat."},
        {'id': 'ladder:kitchen', 'room': 'room:kitchen', 'at': [-666, -384], 'facing': 'e', 'height': 512,
         'exit': [-520, -384], 'surface': RUNGS, 'notes': "The kitchen ladder up the east wall through the dojo's hatch."},
        {'id': 'ladder:rope', 'room': 'room:screens', 'at': [986, -1568], 'facing': 'w', 'height': 512,
         'exit': [900, -1568], 'grab_in_air': True, 'surface': RUNGS,
         'notes': "The clan's climbing ladder (black rope and rungs) from the gallery's slot down into the Hall of Screens' south-east alcove."},
    ],
    'floors': [],
    'destructibles': [],
    'sounds': [
        {'id': 'sound:wind', 'room': 'room:gallery', 'at': [0, -1568], 'sound': 'whistling wind', 'radius': 2400,
         'inner_radius': 800, 'volume': 0.5, 'notes': "The wind over the frozen mere at the gallery."},
    ],
    'lights': [],
    'chests': [
        {'id': 'chest:cellar', 'room': 'room:cellar', 'at': [-680, -2400], 'treasure_level': 3,
         'random_items': 2, 'gold': 400, 'notes': "The clan's stores: a chest among the rice sacks."},
        {'id': 'chest:armoury', 'room': 'room:armoury', 'at': [100, -872], 'treasure_level': 3,
         'random_items': 2, 'gold': 300, 'notes': "A chest of the clan's best blades."},
        {'id': 'chest:strongbox', 'room': 'room:master', 'at': [700, -800], 'facing': 'w', 'treasure_level': 4,
         'random_items': 2, 'gold': 1500, 'trap_level': 3, 'notes': "The clan's strongbox behind the dais (the hoard, a level up)."},
    ],
    'monsters': [],
    'decorations': [],
    'exits': [
        {'id': 'exit:north_door', 'room': 'room:porch', 'wall': 'north', 'size': [160, 320], 'surface': S('7solid01', 160, 320),
         'to': 'exit:x5_pagoda', 'notes': "The pagoda's north door, out to X5 (the mere's north-east shore)."},
    ],
}

NINJA, SHADOW, MASTER_N, CLAN_MASTER, SURVIVOR = 11120, 11121, 11122, 11123, 11124
PLACED = [
    # room, group, [(monster, at, facing)]
    ('porch', 10, [(NINJA, [-250, -760], 90), (NINJA, [250, -760], 90)]),
    ('kitchen', 11, [(NINJA, [-1200, -500], 0), (NINJA, [-900, -800], 0)]),
    ('shrine', 12, [(NINJA, [-700, -1500], 90), (NINJA, [600, -1500], 90), (NINJA, [-600, -1900], 90)]),
    ('dorm', 13, [(NINJA, [600, -420], 180), (NINJA, [640, -300], 180), (NINJA, [1150, -1500], 180)]),
    ('dojo', 14, [(NINJA, [-200, -1300], 0), (NINJA, [100, -1000], 0), (NINJA, [-300, -700], 0),
                  (NINJA, [0, -400], 0), (NINJA, [-1000, -380], 0)]),
    ('screens', 15, [(SHADOW, [-450, -560], 270), (SHADOW, [-450, -680], 270)]),
    ('screens', 16, [(SHADOW, [150, -560], 270), (SHADOW, [150, -680], 270)]),
    ('screens', 17, [(NINJA, [-200, -1230], 0), (NINJA, [200, -1230], 180)]),
    ('armoury', 18, [(SHADOW, [-400, -760], 0), (SHADOW, [0, -760], 180)]),
    ('gallery', 19, [(NINJA, [-1020, -1000], 270), (NINJA, [400, -1568], 180)]),
    ('master', 20, [(MASTER_N, [-300, -880], 270)]),
]
GROUP_NOTES = {15: "behind cell 1's paper", 16: "behind cell 2's paper", 13: "two behind the paper wall"}
for rid, group, ms in PLACED:
    for n, (mon, at, facing) in enumerate(ms, 1):
        key = f'{rid}_{group}_{n}' if rid == 'screens' else f'{rid}_{n}'
        m = {'id': f'monster:{key}', 'room': 'room:' + rid, 'monster': mon, 'at': at, 'facing': facing,
             'hostile': True, 'group': group}
        if group in GROUP_NOTES:
            m['notes'] = GROUP_NOTES[group]
        objects['monsters'].append(m)
objects['monsters'].append({'id': 'monster:clan_master', 'room': 'room:master', 'monster': CLAN_MASTER,
                            'at': [200, -840], 'floor_height': 2096, 'facing': 270, 'hostile': True, 'group': 21,
                            'notes': "The Clan Master 42 (A2's boss row 11123: look C, shuriken, blink on hit 0.2), on his dais."})
HOSTILE_GROUPS = sorted({g for _, g, _ in PLACED} | {21})
# The clan's survivors (D-25 Q14): a peaceful row in its own faction (11124, xeen_ninjas_clan, friendly), placed
# hidden, shown only with q-c4.done; Shinobu (NPC 4530) is the one by the cushion (her own group).
for n, at in enumerate(([200, -2200], [420, -2280], [200, -2420], [-60, -2460]), 1):
    objects['monsters'].append({'id': f'monster:survivor_{n}', 'room': 'room:cellar', 'monster': SURVIVOR,
                                'at': at, 'facing': 180, 'group': 30, 'hidden': True, 'immobile': True,
                                'notes': "A Clan Survivor (11124, faction clan, friendly), shown with q-c4.done."})
objects['monsters'].append({'id': 'monster:shinobu', 'room': 'room:cellar', 'monster': SURVIVOR, 'at': [-380, -2230],
                            'facing': 90, 'group': 31, 'hidden': True, 'immobile': True, 'npc': 4530,
                            'notes': "Shinobu, the clan master's heir (NPC 4530, look C) on a Clan Survivor (11124), by her cushion; shown with q-c4.done. She is NPC 4530 (merge point 22, monsters[].npc): clicked, she talks."})

# Lights: warm paper lanterns; the screens' cells lit inside (shapes on the paper); cold sky light on the gallery.
LAMP = [235, 190, 130]
COOL = [175, 185, 205]
LIGHTS = [
    ('porch', [0, -512], 380, 1300, LAMP), ('kitchen', [-1088, -512], 360, 1100, LAMP),
    ('shrine', [-500, -1600], 420, 1300, LAMP), ('shrine', [700, -1600], 420, 1300, LAMP),
    ('shrine', [0, -1880], 260, 700, [255, 170, 90]),
    ('stair_e', [1120, -900], 300, 900, LAMP),
    ('cellar', [0, -2080], 330, 1300, [200, 170, 130]),
    ('dojo', [-100, -1300], 380, 1400, LAMP), ('dojo', [-800, -380], 380, 1100, LAMP),
    ('dorm', [700, -1500], 380, 1200, LAMP), ('dorm', [700, -600], 380, 1000, LAMP),
    ('stair_w', [-896, -800], 300, 900, LAMP),
    ('screens', [-450, -600], 360, 700, [255, 200, 140]), ('screens', [150, -600], 360, 700, [255, 200, 140]),
    ('screens', [-200, -1500], 380, 1000, LAMP), ('screens', [700, -1540], 380, 900, LAMP),
    ('screens', [-300, -950], 380, 1000, LAMP),
    ('stair_c', [672, -1200], 300, 900, LAMP),
    ('armoury', [-250, -750], 380, 1000, LAMP), ('armoury', [700, -1300], 380, 900, LAMP),
    ('gallery', [-1024, -1000], 420, 1400, COOL), ('gallery', [100, -1568], 420, 1600, COOL),
    ('stair_t', [-600, -1184], 300, 900, LAMP),
    ('master', [-400, -1000], 340, 1300, LAMP), ('master', [400, -1000], 340, 1300, [255, 160, 90]),
]
for i, (rid, at, height, radius, color) in enumerate(LIGHTS, 1):
    objects['lights'].append({'id': f'light:{rid}_{i}', 'room': 'room:' + rid, 'at': at, 'height': height,
                              'radius': radius, 'color': color})

# Decorations (D-7: containers by walls in pairs, nothing on a walking line; candles and lanterns by the walls).
DECOS = [
    ('kitchen_bowl', 'kitchen', 'foodbowl', [-1450, -700]),
    ('kitchen_sack_1', 'kitchen', 'bag01', [-1470, -80]), ('kitchen_sack_2', 'kitchen', 'bag01', [-1470, -180]),
    ('shrine_candle_1', 'shrine', 'dec02', [-300, -1980]), ('shrine_candle_2', 'shrine', 'dec02', [300, -1980]),
    ('cellar_sack_1', 'cellar', 'floursac', [-690, -2130]), ('cellar_sack_2', 'cellar', 'floursac', [-690, -2230]),
    ('cellar_sack_3', 'cellar', 'bag01', [-560, -2490]), ('cellar_sack_4', 'cellar', 'bag01', [-460, -2490]),
    ('cellar_barrel_1', 'cellar', 'bigbarel', [690, -2050]), ('cellar_barrel_2', 'cellar', 'bigbarel', [690, -2160]),
    ('dorm_bowl', 'dorm', 'foodbowl', [560, -1800]),
]
for key, rid, deco, at in DECOS:
    objects['decorations'].append({'id': f'deco:{key}', 'room': 'room:' + rid, 'decoration': deco, 'at': at})
# Wall torches (the user's light rule, lanes/README.md 2026-11-20): each on a wall at 160, clear of doorways, panels and
# the screens; the rooms' point lights (objects.lights) stand inside their rooms' air, under the ceilings.
TORCHES = [
    ('porch_1', 'porch', 3, 0.2), ('porch_2', 'porch', 1, 0.5), ('kitchen', 'kitchen', 0, 0.5),
    ('shrine_1', 'shrine', 2, 0.25), ('shrine_2', 'shrine', 2, 0.75), ('cellar', 'cellar', 3, 0.5),
    ('dojo_1', 'dojo', 0, 0.15), ('dojo_2', 'dojo', 2, 0.5), ('dorm', 'dorm', 1, 0.2),
    ('screens_1', 'screens', 4, 0.5), ('screens_2', 'screens', 0, 0.3), ('armoury', 'armoury', 4, 0.3),
    ('master_1', 'master', 1, 0.5), ('master_2', 'master', 3, 0.5),
]
for key, rid, wall, along in TORCHES:
    objects['decorations'].append({'id': f'deco:torch_{key}', 'room': 'room:' + rid, 'decoration': 'torch01',
                                   'wall': wall, 'along': along, 'height': 160})

# Destructibles (D-25 Q15): the two paper doors and the maze's free-standing screens.
objects['destructibles'] = [
    {'id': 'destructible:paper_dorm', 'of': 'door:paper_dorm', 'hp': 20, 'material': 'wood', 'effect_scale': 0.6,
     'notes': "The paper wall between the dojo and the sleeping loft, its north panel."},
    {'id': 'destructible:paper_dorm2', 'of': 'door:paper_dorm2', 'hp': 20, 'material': 'wood', 'effect_scale': 0.6,
     'notes': "The paper wall's south panel."},
    {'id': 'destructible:crane', 'of': 'door:crane', 'hp': 20, 'material': 'wood', 'effect_scale': 0.6,
     'notes': "The crane screen: struck, shot or clicked (evt:crane) it falls; the stair up behind it."},
] + [{'id': 'destructible:' + p['id'].split(':')[1], 'of': p['id'], 'hp': 20, 'material': 'wood',
      'effect_scale': 0.6, 'notes': "A paper screen of the maze."} for p in MAZE]

# ================================================================================================ wiring.yml
QC4_DONE, QC4_SLAIN = 112082, 112081
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 6,
     'text': "The barred door gives way. The pagoda smells of cold incense and lamp oil, and somewhere above a floorboard creaks.",
     'notes': "Arrival line (a one-shot timer: the party arrives standing in the entry hall)."},
    {'id': 'evt:north_door', 'preset': 'exit', 'source': 'exit:north_door', 'title': 'Winterkill Tundra',
     'notes': "Out to X5 in front of the pagoda's north door (exit:x5_pagoda); the game's leave window (D-24)."},
    {'id': 'evt:door_shrine', 'preset': 'door', 'source': 'door:porch_shrine', 'title': 'Door'},
    {'id': 'evt:door_kitchen', 'preset': 'door', 'source': 'door:porch_kitchen', 'title': 'Door'},
    {'id': 'evt:door_dojo', 'preset': 'door', 'source': 'door:dojo_dorm', 'title': 'Sliding door'},
    {'id': 'evt:door_armoury', 'preset': 'door', 'source': 'door:armoury', 'title': 'Door'},
    {'id': 'evt:bell', 'preset': 'text', 'source': 'platform:bell', 'title': 'Bell', 'seconds': 6,
     'text': "The monks' bell, green with age. Kai Wu rang it every dawn, until the Evil Ninja clan drove him from his sacred home.",
     'notes': "Echoes Kai Wu, aaze0003:15 ('I am a peace loving old monk driven from my sacred home ... until the Evil Ninja clan drove me out')."},
    {'id': 'evt:broom', 'preset': 'text', 'source': 'platform:broom', 'title': 'Broom', 'seconds': 6,
     'text': "A broom, dropped where an old monk let it fall. \"There are still Ninja in my Pagoda,\" Kai Wu said. Nobody has swept since.",
     'notes': "Echoes Kai Wu, aaze0003:16 ('There are still Ninja in my Pagoda. I cannot go home until they are gone.')."},
    {'id': 'evt:altar', 'preset': 'text', 'source': 'platform:altar', 'title': 'Altar', 'seconds': 5,
     'text': "Kai Wu's altar. The clan has hung its black banner over it, and the incense bowls are full of shuriken."},
    {'id': 'evt:clan_mark', 'preset': 'text', 'source': 'panel:clan_mark', 'title': "The clan's banner", 'seconds': 4,
     'text': "A black banner with a carrion bird: the clan's mark, hung over a monk's altar."},
    {'id': 'evt:hatch', 'preset': 'switch', 'source': 'mover:hatch', 'title': 'Mat', 'opens': ['mover:hatch'],
     'text': "A draught comes up between the floorboards. The mat lifts: a trapdoor, and a ladder down into the dark.",
     'seconds': 5,
     'notes': "state:hatch (the graph's secret link): the altar mat slides aside over the cellar hatch."},
    {'id': 'evt:hearth', 'preset': 'text', 'source': 'platform:hearth', 'title': 'Hearth', 'seconds': 4,
     'text': "The kitchen hearth, cold. Rice is trodden into the ashes."},
    {'id': 'evt:kitchen_table', 'preset': 'text', 'source': 'platform:kitchen_table', 'title': 'Table', 'seconds': 4,
     'text': "Kai Wu's rice jars, smashed. Whoever did it was looking for something, or for nothing."},
    {'id': 'evt:weapon_wall', 'preset': 'text', 'source': 'platform:weapon_wall', 'title': 'Weapon wall', 'seconds': 4,
     'text': "Wooden practice blades, worn smooth at the grip."},
    {'id': 'evt:gong', 'preset': 'text', 'source': 'panel:gong', 'title': 'Gong', 'seconds': 4,
     'text': "The gong booms through all five storeys, and the pagoda falls silent to listen."},
    {'id': 'evt:crane', 'preset': 'script', 'source': 'door:crane', 'title': 'Crane screen',
     'effects': [{'destroy': 'destructible:crane'}],
     'text': "The paper tears from top to bottom, and the crane falls away. Behind it a stair climbs into the dark.",
     'seconds': 5,
     'notes': "D-25 Q15: clicking (or striking) the crane screen breaks it; the stair up stands behind it. No riddle."},
    {'id': 'evt:gallery_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:gallery', 'once': True,
     'seconds': 6,
     'text': "The moon gallery. Below, the frozen mere stretches away under the sky, and the wind pulls at your cloaks."},
    {'id': 'evt:cellar_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:cellar', 'once': True,
     'seconds': 6, 'text': "The clan's storeroom: coils of rope, bolts of black cloth, sacks of rice."},
    {'id': 'evt:screens_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:screens', 'once': True,
     'seconds': 6,
     'text': "Paper screens stand everywhere, lit from behind. Shadows move on the paper, and stop when you do."},
    {'id': 'evt:chest_cellar', 'preset': 'chest', 'source': 'chest:cellar', 'title': 'Chest'},
    {'id': 'evt:chest_armoury', 'preset': 'chest', 'source': 'chest:armoury', 'title': 'Chest'},
    {'id': 'evt:chest_strongbox', 'preset': 'chest', 'source': 'chest:strongbox', 'title': 'Chest'},
    {'id': 'evt:clan_master_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:clan_master'}},
     'lua': 'XeenQuests.hook("q-c4.clan_master")',
     'notes': "state:clan_master (a kill timer, XD-05's drums): A3's q-c4.clan_master sets clan_master_slain (112081) and gives 'The clan master falls. You have dishonored the Ninjas ...' (aaze0003:5)."},
    {'id': 'evt:stage_done', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': QC4_DONE},
     'opens': ['mover:hatch'],
     'effects': [{'hide_actors': g} for g in HOSTILE_GROUPS] + [{'show_actors': 30}, {'show_actors': 31}],
     'notes': "Stage q-c4.done (112082, D-25 Q14) on every load: the clan's surviving hostile ninjas hidden, the cellar hatch open, Shinobu and four Clan Survivors shown."},
    {'id': 'evt:shinobu', 'preset': 'text', 'source': 'platform:cushion', 'title': 'Cushion', 'seconds': 4,
     'text': "A worn cushion on the cellar floor, still warm.",
     'notes': "Shinobu's cushion (she talks when clicked herself, monsters[].npc): before the done stage the hint that someone lives here (Kai Wu's 'Someone lives in the cellar')."},
]
for i in range(1, 4):
    events.append({'id': f'evt:target_{i}', 'preset': 'text', 'source': f'platform:target_{i}',
                   'title': 'Straw target', 'seconds': 4, 'text': "A straw target, bristling with shuriken."})
for i in range(1, 4):
    events.append({'id': f'evt:rack_{i}', 'preset': 'text', 'source': f'platform:rack_{i}', 'title': 'Weapon rack',
                   'seconds': 4,
                   'text': "Racks of blades, bows and shuriken. The best of it is locked in the chest."})
wiring = {'format': 0, 'events': events}

atmosphere = {
    'format': 0,
    'open_sky': {'mode': 'open', 'preset': 'frozen'},
    'notes': "The moon gallery is the only place open to the sky (its outer walls and ceiling are sky faces): X5's preset (worlds/xeen/rendering/sky/sky.yml, xeen_x5.odm: frozen). Every other room is lit by its own lanterns.",
}

QBITS = {'clan_master_slain': QC4_SLAIN, 'done': QC4_DONE}
project = {
    'format': 0, 'id': 'xeen_xd22', 'name': 'Ninja Pagoda', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'XD-22', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [6, 5], 'climbs': 'n'},
    'map_stats': {'id': 9145, 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 12, 'environment': 'wood hall',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Ninja', 'tier': 1, 'per_marker': [2, 3], 'weight': 100}]},
    'neighbours': [
        {'id': 'exit:x5_pagoda', 'to': 'xeen_x5.odm', 'kind': 'door', 'arrival': [320, 9872, 1000],
         'direction': 90,
         'arrival_hint': "X5's mere shore, 400 north of thing:pagoda's door face (320, 9472), facing away from it (north); the ground there 993 (measured 2026-11-20, playtest_exit.yml).",
         'notes': "X5 (Winterkill Tundra, A6's): the Ninja Pagoda's north door, thing:pagoda at cells [62.5, 45] (event 61 'The Ninja Pagoda', its door panel on storey_1's north wall)."},
    ],
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: XD-22 Ninja Pagoda on X5's mere shore (Q-C4 The Ninja Pagoda; T2-CLAN). Monsters: A2's Ninjas, all placed (19 Ninja 11120 22, 6 Shadow Ninja 11121 30, 1 Ninja Master 11122 40) in groups 10-20 by room, and the Clan Master 11123 (42, boss row, group 21); Shinobu (NPC 4530) and four Clan Survivors 11124 (faction clan, friendly; groups 31 and 30) placed hidden in the cellar and shown with q-c4.done. Slot 1 Xeen Ninja for the map card (no rest encounters). Map qbits 110920-110929: none used; A3's q-c4 bits named (112081, 112082). Hook q-c4.clan_master from the kill timer. Music 12. Exit: the north door to X5 (installed), exit:x5_pagoda.",
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
        p['notes'] = f"Xeen design brief, level {lv}: XD-22 Ninja Pagoda (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-22 Ninja Pagoda, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', atmosphere)])
print('written L4')
