#!/usr/bin/env python3
"""DD-06 Southern Tower: writes the L1-L4 project folders of devdocs/xeen/briefs/dd06 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/dd06/cycle.sh); never hand-edit the written files.
Written by agent:xeen-a7-dd06 after XD-23's gen.py (phase 3) and XD-11's geo.py (the stacked tower, its stair halls).

Frame: x east, y north, z up. A square tower 4,096 across inside (-2048..2048 on x and y), four floors 640 apart
(0 the front, 640 the den, 1280 the practice floor, 1920 the inner circle); rooms 544 high (slabs 96), the counting
room 640 under the cone's beams; walls between rooms 128 (the gap between their outlines). The tower's door is in the
north wall (D2's door faces north). The stairs up are two-storey halls along the outer walls, each behind a gong door,
alternating west (0-640), east (640-1280), west (1280-1920): a flight of 20 steps of 32 along the outer wall and a
gallery at the upper floor. The west strip (x -2048..-1408, y -2048..1024) holds the first and third stair halls one
above the other; the east strip (x 1408..2048, y -1024..2048) the second."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/dd06'

FL = [0, 640, 1280, 1920]
H = 544
# D-58 (decider, 2026-11-21): a roof stair from the top floor to a trapdoor up to D7's entrance:dd06_roof, one way up,
# open after m30.done (A3's hook d7.roof_dd06). A stair hall north of the getaway room: one flight of 16 steps of 32
# up the east wall to a head at 2,432, and over the head a framed hatch in the ceiling closed by a plank trapdoor.
ROOF_STAIR = (1024, 768, 1536, 2048)
ROOF_HEAD = 1920 + 512            # the head's floor
ROOF_CEIL = ROOF_HEAD + 288       # the stair hall's ceiling over the head
ROOF_HATCH_TOP = ROOF_CEIL + 64   # the hatch's frame rises 64 into the ceiling; the leaf closes its top
ROOF_HATCH = (1184, 1760, 1376, 1952)
# The Strongroom key (a fixed item in the fence's lockbox, opening the strongroom's iron door) has no item row yet
# (A2). Until it has, the lockbox holds no key and the iron door stays locked (BLOCKED, NOTES.md). When A2 gives the
# row, put its id here (or DD06_STRONGROOM_KEY=<id>) and rerun: the lockbox, the door, plan and project follow.
import os
STRONGROOM_KEY = int(os.environ.get('DD06_STRONGROOM_KEY', '12262')) or None  # A2's Strongroom Key (2026-11-20)


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One family: the Towers of Mok's stone (A6's towers kit: MM8 Castle of Air d27, green-grey ashlar, scale-pattern
# flags, panelled ceilings, grey cobble on stairs, stone doors), with the thieves' timber where they built (MM7
# Bracada's planks and black beams: the den's boards, the cone's beams, furniture). Reused world textures: XD-03's
# great gong (xngong), XD-04's riveted iron (xwiron, the strongroom door) and cage bars (xngrille, the kennel gate).
ASHLAR = S('gston1wl', 128, 256)
FLAGS = S('gston1fl', 128, 128)
PANELC = S('gstn1cl', 128, 128)
COBBLE = S('gcstflor', 128, 256)
TILEV = S('gstntilev', 64, 128)
STONEDOOR = S('gcstdoor', 128, 256)
PLANKS = S('7trimd', 128, 256)
BEAMS = S('hwm2rf', 128, 128)
POST = S('trim11_32', 32, 64)
DESK = S('7t1books1', 128, 128)
BOOKS = S('7t1books', 128, 256)
CABS = S('7t1cabs', 64, 128)
SHEET = S('t2bedsht', 128, 256)
STRAW = S('straw', 256, 256)
GONG = S('xngong', 128, 128, fit=True)
MEMO = S('scroll', 64, 64, fit=True)
TAPESTRY_A = S('tap4', 128, 256, fit=True)
TAPESTRY_B = S('tap3', 128, 256, fit=True)
IRON = S('xwiron', 128, 128)
GRILLE = S('xngrille', 128, 256)
# Bars that run along a wall or a gate (texture fit, merge point 16): XD-04's cage band, one storey of 320 high.
BARS = S('xwcage', 128, 256, scale=1.25)
# A folding leaf takes its picture at one texel a unit: the gate's bars at 256 high show 1.25 times up.
BARS_GATE = S('xwcage', 128, 256)

themes = [
    {'id': 'theme:tower', 'wall': ASHLAR, 'floor': FLAGS, 'ceiling': PANELC, 'reveal': ASHLAR, 'door': STONEDOOR,
     'bands': [{'height': 32, 'surface': TILEV}],
     'notes': "The Mok tower's own rooms (the front, the practice floor): green-grey ashlar (MM8 gston1wl) over a green marble skirting (gstntilev), scale-pattern flags (gston1fl), panelled stone ceilings (gstn1cl), the tower's stone doors (gcstdoor)."},
    {'id': 'theme:stair', 'wall': ASHLAR, 'floor': COBBLE, 'ceiling': PANELC, 'reveal': ASHLAR, 'door': STONEDOOR,
     'notes': "The stair halls: the same ashlar, grey cobbles (gcstflor) underfoot."},
    {'id': 'theme:den', 'wall': ASHLAR, 'floor': PLANKS, 'ceiling': BEAMS, 'reveal': ASHLAR, 'door': PLANKS,
     'bands': [{'height': 32, 'surface': TILEV}],
     'notes': "Where the thieves live (the den floor, the inner circle): the tower's ashlar over boards the guild laid (7trimd) under black beams (hwm2rf), plank doors."},
    {'id': 'theme:kennel', 'wall': ASHLAR, 'floor': STRAW, 'ceiling': PANELC, 'reveal': ASHLAR, 'door': BARS_GATE,
     'notes': "The kennel: the ashlar, old straw (straw) on the floor, a barred gate (xngrille)."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def blob(cx, cy, rx, ry):
    return [[cx - rx, cy - ry // 3], [cx - rx // 3, cy - ry], [cx + rx // 2, cy - ry], [cx + rx, cy - ry // 4],
            [cx + rx // 2, cy + ry], [cx - rx // 2, cy + ry]]


# id: (name, (x0, y0, x1, y1), floor, ceiling, theme)
ROOMS = {
    # floor 0, the front
    'door_hall': ("Entrance hall", (-128, 1152, 2048, 2048), 0, H, 'theme:tower'),
    'guardroom': ("Lookouts' room", (-2048, 1152, -256, 2048), 0, H, 'theme:tower'),
    'gong1': ("First gong", (-1280, -1024, -256, 1024), 0, H, 'theme:tower'),
    'tapestry': ("Tapestry hall", (-128, -1024, 1152, 1024), 0, H, 'theme:tower'),
    'stash': ("Behind the tapestry", (1280, -512, 2048, 512), 0, H, 'theme:tower'),
    'kennel': ("Kennel", (-1280, -2048, 1152, -1152), 0, H, 'theme:kennel'),
    'stair1': ("First stair", (-2048, -2048, -1408, 1024), 0, FL[1] + H, 'theme:stair'),
    # floor 1, the den
    'landing2': ("Den landing", (-1280, -2048, -512, -1152), 640, 640 + H, 'theme:den'),
    'mess': ("Mess hall", (-384, -2048, 512, -1152), 640, 640 + H, 'theme:den'),
    'fence': ("Fence's room", (640, -2048, 1280, -1152), 640, 640 + H, 'theme:den'),
    'alibaba': ("Treasury", (1408, -2048, 2048, -1152), 640, 640 + H, 'theme:den'),
    'gong2': ("Second gong", (384, -1024, 1280, 512), 640, 640 + H, 'theme:den'),
    'bunks': ("Bunkroom", (-1280, -1024, 256, 512), 640, 640 + H, 'theme:den'),
    'stair2': ("Second stair", (1408, -1024, 2048, 2048), 640, FL[2] + H, 'theme:stair'),
    # floor 2, the practice floor
    'landing3': ("Practice landing", (256, 1280, 1280, 2048), 1280, 1280 + H, 'theme:tower'),
    'trap_walk': ("Trap walk", (768, -2048, 1280, 1152), 1280, 1280 + H, 'theme:tower'),
    'strongroom': ("Strongroom", (1408, -2048, 2048, -1152), 1280, 1280 + H, 'theme:tower'),
    'practice': ("Practice hall", (-384, -1536, 640, 1152), 1280, 1280 + H, 'theme:tower'),
    'gong3': ("Third gong", (-1280, 128, -512, 1152), 1280, 1280 + H, 'theme:tower'),
    'stair3': ("Third stair", (-2048, -2048, -1408, 1024), 1280, FL[3] + H, 'theme:stair'),
    # floor 3, the inner circle
    'landing4': ("Top landing", (-1280, -2048, -512, -1152), 1920, 1920 + H, 'theme:den'),
    'library': ("Thieves' library", (-384, -2048, 1280, -1152), 1920, 1920 + H, 'theme:den'),
    'counting': ("Counting room", (-1280, -1024, 768, 896), 1920, 1920 + 640, 'theme:den'),
    'bedchamber': ("Master's bedchamber", (-512, 1024, 768, 2048), 1920, 1920 + H, 'theme:den'),
    'getaway': ("Getaway hatch", (896, -256, 1536, 640), 1920, 1920 + H, 'theme:den'),
    # D-58 (2026-11-21, seventeenth session): the roof stair north of the getaway room, up to a trapdoor to D7.
    'roof_stair': ("Roof stair", ROOF_STAIR, 1920, ROOF_CEIL, 'theme:stair'),
}
FLOOR_OF = {k: v[2] for k, v in ROOMS.items()}


def outline(rid):
    return rect(*ROOMS[rid][1])


def walls_of(rid):
    o = outline(rid)
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def shared(a, b):
    best = None
    for i, (p0, p1) in enumerate(walls_of(a)):
        for j, (q0, q1) in enumerate(walls_of(b)):
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
            if hi - lo <= 0 or gap > 512:
                continue
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            nx, ny = dy, -dx
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


def opening(oid, a, b, at, width=256, height=320, link=None, **kw):
    gap, i, j, lo, hi, ax, p0, p1 = shared(a, b)
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
    # floor 0
    opening('open:hall_guard', 'door_hall', 'guardroom', 1600, 256, 256, 'link:door_guard'),
    opening('open:guard_gong1', 'guardroom', 'gong1', -768, 512, 384, 'link:guard_gong1'),
    opening('open:gong1_stair', 'gong1', 'stair1', 768, 256, 320, 'link:gong1_up'),
    opening('open:gong1_kennel', 'gong1', 'kennel', -768, 256, 320, 'link:gong1_kennel'),
    opening('open:kennel_tapestry', 'kennel', 'tapestry', 512, 384, 384, 'link:kennel_tapestry'),
    opening('open:tapestry_hall', 'tapestry', 'door_hall', 512, 512, 384, 'link:tapestry_door'),
    opening('open:tapestry_stash', 'tapestry', 'stash', -320, 256, 320, 'link:tapestry_stash',
            notes="The false wall behind the tapestry's south end: a secret door of the hall's own ashlar."),
    # floor 1
    opening('open:stair_landing2', 'stair1', 'landing2', -1792, 320, 384, 'link:gong1_up',
            notes="The head of the first stair: its gallery opens east on to the den landing."),
    opening('open:landing2_mess', 'landing2', 'mess', -1600, 384, 384, 'link:l2_mess'),
    opening('open:mess_fence', 'mess', 'fence', -1600, 256, 256, 'link:mess_fence'),
    opening('open:fence_treasury', 'fence', 'alibaba', -1600, 256, 320, 'link:fence_treasury'),
    opening('open:fence_gong2', 'fence', 'gong2', 960, 384, 384, 'link:fence_gong2'),
    opening('open:gong2_bunks', 'gong2', 'bunks', 0, 256, 256, 'link:gong2_bunks'),
    opening('open:bunks_landing2', 'bunks', 'landing2', -896, 384, 384, 'link:bunks_l2'),
    opening('open:gong2_stair', 'gong2', 'stair2', -768, 256, 320, 'link:gong2_up'),
    # floor 2
    opening('open:stair_landing3', 'stair2', 'landing3', 1792, 320, 384, 'link:gong2_up',
            notes="The head of the second stair: its gallery opens west on to the practice landing."),
    opening('open:landing3_trap', 'landing3', 'trap_walk', 1024, 320, 384, 'link:l3_trap'),
    opening('open:landing3_practice', 'landing3', 'practice', 448, 320, 384, 'link:l3_practice'),
    opening('open:trap_practice', 'trap_walk', 'practice', -512, 256, 256, 'link:trap_practice'),
    opening('open:trap_strong', 'trap_walk', 'strongroom', -1600, 256, 320, 'link:trap_strong'),
    opening('open:practice_gong3', 'practice', 'gong3', 640, 384, 384, 'link:practice_gong3'),
    opening('open:gong3_stair', 'gong3', 'stair3', 768, 256, 320, 'link:gong3_up'),
    # floor 3
    opening('open:stair_landing4', 'stair3', 'landing4', -1792, 320, 384, 'link:gong3_up',
            notes="The head of the third stair: its gallery opens east on to the top landing."),
    opening('open:landing4_library', 'landing4', 'library', -1600, 384, 384, 'link:l4_library'),
    opening('open:landing4_counting', 'landing4', 'counting', -896, 256, 256, 'link:l4_counting'),
    opening('open:counting_bed', 'counting', 'bedchamber', 128, 256, 256, 'link:counting_bed'),
    opening('open:counting_getaway', 'counting', 'getaway', 192, 320, 384, 'link:counting_getaway'),
    opening('open:getaway_roof', 'getaway', 'roof_stair', 1168, 256, 320, 'link:getaway_roof',
            notes="From the getaway room north into the roof stair (D-58)."),
]


def plat(id, at, size, rise, surface, top=None, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': surface}
    if id:
        d = {'id': id, **d}
    if top:
        d['top_surface'] = top
    d.update(kw)
    return d


def gallery(id, b, notes):
    return {'id': id, 'rise': 32, 'outline': rect(*b), 'base': 608, 'surface': ASHLAR, 'top_surface': COBBLE,
            'bottom_surface': PANELC, 'notes': notes}


def panel(id, offset, length, bottom, height, surface, notes):
    return {'id': id, 'offset': offset, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface,
            'notes': notes}


def hatch_frame(b):
    """The four beams of a hatch's frame, centred on the rectangle's edges, the ends of two of them overlapping the
    others' (a frame of black beams; the trapdoor leaf hangs inside it)."""
    x0, y0, x1, y1 = b
    return [[[x0 - 16, y0], [x1 + 16, y0]], [[x0 - 16, y1], [x1 + 16, y1]], [[x0, y0 + 16], [x0, y1 - 16]],
            [[x1, y0 + 16], [x1, y1 - 16]]]


GONG_PANEL = (384, 320)          # the gong's face, 320 square, its foot 96 above the floor


def gong_wall(wall, offset, gid):
    return {'wall': wall, 'panels': [panel(f'panel:{gid}', offset, 320, 96, 320, GONG,
                                           "A bronze gong on the wall by the stair door (XD-03's great gong picture).")]}


def bunk(i, x, y0, y1):
    """A bunk of two tiers along a wall: a low bed and a hanging upper bed over it."""
    return [plat(f'platform:bunk_{i}', [x, (y0 + y1) // 2], [192, y1 - y0], 48, PLANKS, SHEET,
                 notes="The lower bunk, a straw tick under a grey blanket."),
            {'id': f'platform:bunk_{i}_top', 'outline': rect(x - 96, y0, x + 96, y1), 'base': 256, 'rise': 32,
             'surface': PLANKS, 'top_surface': SHEET, 'bottom_surface': PLANKS,
             'notes': "The upper bunk over it."},
            plat(None, [x - 80, y0 - 16], [32, 32], 352, POST, POST, notes="The bunk's post."),
            plat(None, [x + 80, y0 - 16], [32, 32], 352, POST, POST, notes="The bunk's post.")]


EXTRA = {
    'door_hall': {
        'platforms': [{'id': 'platform:straw_heap', 'outline': blob(1760, 1780, 200, 170), 'rise': 32, 'surface': STRAW,
                       'top_surface': STRAW, 'notes': "A heap of straw in the north-east corner: where the getaway chute lets out."}],
        'notes': "Inside the tower's door, 2,176 by 896: the stone hall the thieves keep their lookouts beside; a heap of straw in the north-east corner where the getaway chute ends.",
    },
    'guardroom': {
        'platforms': [plat('platform:card_table', [-1500, 1700], [256, 192], 64, DESK, DESK,
                           notes="A table with a card game left in the middle of a hand.")],
        'notes': "The lookouts' room: arrow slits on the clearing, a bell rope, a card game left on a table.",
    },
    'gong1': {
        'walls': [{'wall': 'west', 'panels': [
            panel('panel:gong1', 464, 320, 96, 320, GONG, "A bronze gong on the wall south of the stair door (XD-03's great gong picture)."),
            panel('panel:memo', 832, 128, 128, 160, MEMO, "The guild memo pinned up beside the first gong.")]}],
        'notes': "The first gong on the west wall beside the stair door, and the guild memo pinned up beside it.",
    },
    'tapestry': {
        'walls': [{'wall': 'east', 'panels': [
            panel('panel:tapestry_a', 1100, 224, 64, 448, TAPESTRY_A, "A Mok procession in faded wool (left half)."),
            panel('panel:tapestry_b', 1340, 224, 64, 448, TAPESTRY_B, "A Mok procession in faded wool (right half)."),
        ]}],
        'notes': "A long hall, 1,280 by 2,048: a tapestry of a Mok procession on the east wall, left from the tower's priests; a button at its end; the false wall behind its south end.",
    },
    'stash': {'notes': "A thief's private stash behind the illusion: a chest and two sacks."},
    'kennel': {
        'walls': [{'wall': 'south', 'panels': [panel('panel:pens', 512, 1024, 0, 320, BARS,
                                                     "Iron pens along the south wall.")]}],
        'notes': "The guild's hounds and two sabertooths among iron pens along the south wall; old straw and gnawed boots.",
    },
    'stair1': {
        'platforms': [gallery('platform:gallery1', (-2048, -2048, -1408, -1536),
                              "The head of the first stair at the den (640), across the south end.")],
        'flights': [{'from': [-1760, 448], 'to': [-1760, -1536], 'open_below': 32, 'to_height': 640, 'width': 384,
                     'steps': 20, 'notes': "One flight up the west wall, 20 steps of 32, rising south."}],
        'notes': "From the front to the den (0 to 640), two storeys high, behind the first gong's door: the flight along the west wall rises south to a gallery at the den landing.",
    },
    'mess': {
        'platforms': [plat('platform:table_n', [64, -1300], [576, 128], 64, DESK, DESK, notes="A long table."),
                      plat('platform:table_s', [64, -1900], [576, 128], 64, DESK, DESK, notes="A long table.")],
        'notes': "Long tables either side of the way through; dice, bowls, a stew pot in the corner.",
    },
    'fence': {
        'platforms': [plat('platform:sorting_table', [960, -1930], [256, 96], 72, DESK, DESK,
                           notes="The fence's sorting table by the south wall: tagged loot.")],
        'notes': "Where the loot is sorted and tagged: the sorting table, sacks, and the fence's lockbox.",
    },
    'alibaba': {
        'levels': [{'id': 'level:dais', 'outline': rect(1600, -1984, 1984, -1600), 'floor': 680, 'edge': COBBLE,
                    'surface': COBBLE, 'notes': "The chest's dais."}],
        'notes': "A small treasury, one great iron-bound chest on a dais against the east wall.",
    },
    'gong2': {
        'walls': [gong_wall('east', 448, 'gong2')],
        'notes': "The second gong on the east wall beside the stair door.",
    },
    'bunks': {
        'platforms': sum((bunk(i, x, 64, 512) for i, x in enumerate((-1100, -760, -420, -80), 1)), []),
        'notes': "Two tiers of bunks along the north wall, every pillow with a purse under it.",
    },
    'stair2': {
        'platforms': [gallery('platform:gallery2', (1408, 1536, 2048, 2048),
                              "The head of the second stair at the practice floor (1280), across the north end.")],
        'flights': [{'from': [1760, -448], 'to': [1760, 1536], 'open_below': 32, 'to_height': 1280, 'width': 384,
                     'steps': 20, 'notes': "One flight up the east wall, 20 steps of 32, rising north."}],
        'notes': "From the den to the practice floor (640 to 1280), behind the second gong's door: the flight along the east wall rises north to a gallery at the practice landing.",
    },
    'practice': {
        'platforms': [plat(f'platform:dummy_{i}', [x, y], [64, 64], 288, STRAW, STRAW,
                           notes="A practice dummy hung with bells, for pickpockets.")
                      for i, (x, y) in enumerate(((-128, -1200), (192, -1200), (-128, -900)), 1)]
        + [plat('platform:target_1', [-300, 300], [48, 192], 224, STRAW, STRAW,
                notes="A straw target against the west wall, for knife throwers."),
           plat('platform:target_2', [-300, -300], [48, 192], 224, STRAW, STRAW,
                notes="A straw target against the west wall, for knife throwers.")],
        'walls': [{'wall': 'south', 'panels': [panel('panel:locks', 384, 512, 96, 192, CABS,
                                                     "A row of practice locks on boards.")]}],
        'notes': "Where thieves train: dummies hung with bells, straw targets, a row of practice locks.",
    },
    'trap_walk': {
        'beams': [{'path': [[768, -400], [1280, -400]], 'width': 48, 'bottom': 1280 + 400, 'depth': 48,
                   'surface': POST, 'notes': "A swinging log's beam (the log tied up)."}],
        'notes': "A corridor of practice traps, all disarmed by the thieves who live here and armed for everyone else.",
    },
    'strongroom': {'notes': "Behind the iron door: the guild's best takings and two Energy Disks."},
    'gong3': {
        'walls': [gong_wall('west', 576, 'gong3')],
        'notes': "The last gong before the stair to the top, on the west wall beside the stair door.",
    },
    'stair3': {
        'platforms': [gallery('platform:gallery3', (-2048, -2048, -1408, -1536),
                              "The head of the third stair at the top floor (1920), across the south end.")],
        'flights': [{'from': [-1760, 448], 'to': [-1760, -1536], 'open_below': 32, 'to_height': 1920, 'width': 384,
                     'steps': 20, 'notes': "One flight up the west wall, 20 steps of 32, rising south."}],
        'notes': "From the practice floor to the top (1280 to 1920), behind the third gong's door; above the first stair.",
    },
    'library': {
        'walls': [{'wall': 'south', 'panels': [panel('panel:shelves_s', 128, 1408, 0, 448, BOOKS,
                                                     "Shelves of other people's diaries.")]},
                  {'wall': 'east', 'panels': [panel('panel:shelves_e', 128, 640, 0, 448, BOOKS,
                                                    "More shelves.")]}],
        'platforms': [plat('platform:manual', [256, -1500], [96, 64], 96, DESK, BOOKS,
                           notes="A lectern with the Manual of Master Thievery."),
                      plat('platform:prince_book', [640, -1500], [96, 64], 96, DESK, BOOKS,
                           notes="A lectern with the Prince Book.")],
        'notes': "Shelves of other people's diaries; two lecterns: the Manual of Master Thievery and the Prince Book.",
    },
    'counting': {
        'platforms': [plat('platform:desk', [-256, 300], [576, 192], 80, DESK, DESK,
                           notes="The big desk: the ledger, scales, sacks of coin."),
                      plat('platform:high_chair', [-256, 560], [128, 128], 96, PLANKS, DESK,
                           notes="The Master Thief's high chair behind his desk.")],
        'beams': [{'path': [[-1280, y], [768, y]], 'width': 64, 'bottom': 1920 + 560, 'depth': 64, 'surface': BEAMS,
                   'notes': "The slate cone's beams."} for y in (-448, 384)],
        'notes': "The top floor's centre, 2,048 by 1,920 under the cone's beams: desks, scales, sacks of coin; the Master Thief in a high chair behind the big desk.",
    },
    'bedchamber': {
        'platforms': [plat('platform:bed', [128, 1800], [320, 384], 56, PLANKS, SHEET,
                           notes="A bed with velvet hangings.")]
        + [plat(None, [x, y], [32, 32], 384, POST, POST, notes="A bedpost; the velvet hangings between.")
           for x, y in ((-48, 1592), (304, 1592))],
        'notes': "The Master Thief's bedchamber: a bed with velvet hangings; his strongbox beside it, the tower's hoard.",
    },
    'getaway': {
        'platforms': [plat('platform:hatch', [1280, 192], [192, 192], 8, BEAMS, BEAMS,
                           notes="A trapdoor in the floor over a polished chute down the tower's inside wall.")],
        'notes': "Off the counting room: the thieves' trapdoor down the getaway chute, and north the roof stair (D-58).",
    },
    'roof_stair': {
        'platforms': [
            {'id': 'platform:roof_head', 'outline': rect(1024, 1664, 1536, 2048), 'rise': ROOF_HEAD - 1920,
             'surface': ASHLAR, 'top_surface': COBBLE,
             'notes': "The roof stair's head (2,432), across the north end under the hatch."},
            {'id': 'platform:roof_hatch', 'outline': rect(ROOF_HATCH[0] + 16, ROOF_HATCH[1] + 16, ROOF_HATCH[2] - 16,
                                                          ROOF_HATCH[3] - 16),
             'base': ROOF_CEIL - 16 - 1920, 'rise': 16, 'surface': PLANKS, 'top_surface': PLANKS,
             'bottom_surface': PLANKS,
             'notes': "The roof trapdoor: a plank leaf hung shut against the top of its frame (D-58: up to D7 after m30.done)."}],
        'beams': [
            {'path': path, 'width': 32, 'bottom': ROOF_CEIL - 40, 'depth': 40, 'surface': BEAMS,
             'notes': "The roof hatch's frame: black beams round the trapdoor under the ceiling."}
            for path in hatch_frame(ROOF_HATCH)],
        'flights': [{'from': [1376, 896], 'to': [1376, 1664], 'width': 320, 'steps': 16,
                     'notes': "One flight up the east wall, 16 steps of 32, rising north to the head."}],
        'notes': "The roof stair (D-58): north of the getaway room, a flight up the east wall to a head under the roof trapdoor (to D7 after m30.done).",
    },
    'landing2': {'notes': "The first stair arrives here, on the tower's west side."},
    'landing3': {'notes': "The second stair arrives here, on the tower's east side."},
    'landing4': {'notes': "The third stair arrives here, on the west side, under the cone's beams."},
}


def room_doc(rid):
    name, b, fl, ce, theme = ROOMS[rid]
    d = {'id': 'room:' + rid, 'name': name, 'outline': outline(rid), 'floor': fl, 'ceiling': ce, 'theme': theme}
    d.update(EXTRA.get(rid, {}))
    return d


rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:tower', 'ambient': 20},
             'rooms': [room_doc(r) for r in ROOMS], 'openings': OPENINGS,
             'notes': "DD-06 Southern Tower: four floors stacked 640 apart (0, 640, 1280, 1920) inside a tower 4,096 square; x east, y north. Written by output/studio_cal/dd06/tools/gen.py."}

# ================================================================================================ plan.yml
ROGUE, THIEF, MASTER, GUARD, BOSS = 11110, 11111, 11112, 11115, 11114
WOLF, SABRE = 11410, 11411
NAMES = {ROGUE: 'Rogue', THIEF: 'Thief', MASTER: 'Master Thief', GUARD: 'Inner Circle Guard', BOSS: 'The Master Thief',
         WOLF: 'Dark Wolf', SABRE: 'Sabertooth'}
LEVEL = {ROGUE: 12, THIEF: 18, MASTER: 30, GUARD: 30, BOSS: 32, WOLF: 16, SABRE: 22}

# room, group, [(monster, at, facing)]
PLACED = [
    ('guardroom', 10, [(ROGUE, [-1700, 1400], 0), (ROGUE, [-1100, 1850], 0), (THIEF, [-700, 1500], 0),
                       (THIEF, [-1300, 1400], 0)]),
    ('gong1', 11, [(ROGUE, [-600, 300], 90), (ROGUE, [-900, -500], 90)]),
    ('tapestry', 12, [(ROGUE, [60, 680], 90), (ROGUE, [1068, -380], 90), (THIEF, [988, 20], 90)]),
    ('kennel', 13, [(WOLF, [-700, -1700], 90), (WOLF, [-300, -1750], 90), (SABRE, [200, -1700], 90),
                    (SABRE, [716, -1606], 90)]),
    ('mess', 14, [(THIEF, [-200, -1700], 0), (THIEF, [300, -1700], 0), (THIEF, [-200, -1450], 0),
                  (THIEF, [300, -1450], 0), (THIEF, [50, -1580], 0)]),
    ('bunks', 15, [(THIEF, [-1000, -300], 0), (THIEF, [-600, -600], 0), (THIEF, [-200, -300], 0),
                   (THIEF, [-900, -800], 0)]),
    ('fence', 16, [(THIEF, [800, -1800], 0), (THIEF, [800, -1350], 0), (MASTER, [950, -1600], 180)]),
    ('gong2', 17, [(THIEF, [700, -600], 0), (THIEF, [700, 200], 0), (THIEF, [1000, -200], 0)]),
    ('practice', 18, [(THIEF, [0, 300], 270), (THIEF, [300, 700], 270), (THIEF, [100, -400], 270),
                      (MASTER, [400, 0], 180), (MASTER, [-150, 700], 180)]),
    ('trap_walk', 19, [(THIEF, [1024, 500], 270), (THIEF, [1024, -800], 270), (THIEF, [1024, -1500], 270)]),
    ('gong3', 20, [(THIEF, [-900, 400], 0), (THIEF, [-700, 900], 0), (MASTER, [-1000, 700], 0)]),
    ('library', 21, [(THIEF, [0, -1700], 90), (MASTER, [900, -1700], 90)]),
]
GUARDS = [[-800, 300], [300, 300], [-800, -300], [300, -300]]
BOSS_AT = [-256, 720]

# plan spaces: (id, name, kind, size, purpose, chest)
PLAN_SPACES = [
    ('door_hall', 'room', 'M', "Inside the iron-bound door (NO THIEVES on its brass plate outside). A straw heap in the corner where the getaway chute ends.", None),
    ('guardroom', 'room', 'M', "Arrow slits on the clearing, a bell rope, a card game left in the middle.", None),
    ('gong1', 'room', 'M', "A bronze gong by the stair door, and the guild memo pinned beside it (q-d19.guild_memo).", None),
    ('tapestry', 'room', 'M', "A long tapestry of a Mok procession, left from the tower's priests; a button at its end ('Button').", None),
    ('stash', 'room', 'S', "The wall behind the tapestry is not there: 'An illusion!' A thief's private stash (the chest).", 3),
    ('kennel', 'room', 'M', "The guild's hounds and two sabertooths among iron pens; gnawed boots.", None),
    ('stair1', 'corridor', 'M', "The first stair hall, behind the first gong's door: up the west wall from the front to the den.", None),
    ('landing2', 'room', 'S', "The first stair arrives here, on the west side.", None),
    ('mess', 'room', 'M', "Long tables, dice, a stew pot; thieves at dinner.", None),
    ('fence', 'room', 'M', "Where the loot is sorted and tagged; the fence's lockbox (the chest) holds the Strongroom key.", 3),
    ('alibaba', 'room', 'S', "One great iron-bound chest on a dais: 'Ali Baba Chest. What's the password?' (q-d19.ali_baba).", 3),
    ('gong2', 'room', 'M', "The second gong at the stair door up.", None),
    ('bunks', 'room', 'M', "Two tiers of bunks, every pillow with a purse under it ('Bed', 'Nothing here.').", None),
    ('stair2', 'corridor', 'M', "The second stair hall, behind the second gong's door: up the east wall from the den to the practice floor.", None),
    ('landing3', 'room', 'S', "The second stair arrives here, on the east side.", None),
    ('practice', 'room', 'L', "Where thieves train: dummies hung with bells, practice locks, straw targets.", None),
    ('trap_walk', 'corridor', 'M', "A corridor of practice traps, disarmed for the thieves who live here.", None),
    ('strongroom', 'room', 'S', "Behind a locked iron door: the guild's best takings (the chest) and 2 Energy Disks (q-d19.l3_disks).", 3),
    ('gong3', 'room', 'M', "The last gong before the stair to the top.", None),
    ('stair3', 'corridor', 'M', "The third stair hall, behind the third gong's door: up the west wall from the practice floor to the top.", None),
    ('landing4', 'room', 'S', "The third stair arrives here under the slate cone's beams.", None),
    ('library', 'room', 'M', "The Manual of Master Thievery and the Prince Book on two lecterns, and shelves of other people's diaries.", None),
    ('counting', 'room', 'L', "Desks, scales, sacks of coin; the ledger on the big desk (q-d19.ledger); the Master Thief (NPC 5109) in a high chair, his four bodyguards.", None),
    ('bedchamber', 'room', 'M', "A bed with velvet hangings ('Bed', 'Nothing here.'); beside it the Master Thief's own strongbox, the tower's hoard (tier 4).", 4),
    ('getaway', 'room', 'S', "A trapdoor in the floor over a polished chute down the tower's inside wall: the thieves' way out; north, the roof stair.", None),
    ('roof_stair', 'corridor', 'S', "The roof stair (D-58): one flight up to a trapdoor in the ceiling, one way up to D7's entrance:dd06_roof after m30.done (A3's d7.roof_dd06: 'The trapdoor is shut fast.' before); live since D7's install.", None),
]
POP = {}
for rid, group, ms in PLACED:
    for mon, _, _ in ms:
        POP.setdefault(rid, {}).setdefault(mon, 0)
        POP[rid][mon] += 1


def plan_doc(level):
    spaces = []
    for sid, kind, size, purpose, chest in PLAN_SPACES:
        s = {'id': 'room:' + sid, 'name': ROOMS[sid][0], 'kind': kind, 'size': size, 'floor': FLOOR_OF[sid],
             'purpose': purpose}
        pop = POP.get(sid, {})
        if sid == 'counting':
            s['population'] = [
                {'actor': GUARD, 'groups': 4, 'levels': [30, 30],
                 'notes': "The Master Thief's bodyguards, Inner Circle Guard 11115 (faction inner_circle, peaceful until he or they are attacked)."},
                {'actor': BOSS, 'role': 'boss', 'groups': 1, 'levels': [32, 32],
                 'notes': "The Master Thief 11114 (A2's boss row, faction inner_circle, friendly), NPC 5109: clicked while peaceful, he talks."}]
        elif pop:
            s['population'] = [{'actor': m, 'groups': n, 'levels': [LEVEL[m], LEVEL[m]],
                                'notes': f"{n} placed {NAMES[m]}{'s' if n > 1 else ''}."} for m, n in pop.items()]
        else:
            s['empty'] = True
        spaces.append(s)
    L = lambda id, f, t, kind, **kw: {'id': id, 'from': 'room:' + f, 'to': 'room:' + t, 'kind': kind, **kw}
    links = [
        L('link:door_guard', 'door_hall', 'guardroom', 'door'),
        L('link:guard_gong1', 'guardroom', 'gong1', 'open'),
        L('link:gong1_kennel', 'gong1', 'kennel', 'door', notes="The kennel's barred gate."),
        L('link:kennel_tapestry', 'kennel', 'tapestry', 'open'),
        L('link:tapestry_door', 'tapestry', 'door_hall', 'open'),
        L('link:tapestry_stash', 'tapestry', 'stash', 'door', condition={'map_var': 'illusion'},
          notes="button: the false wall vanishes ('An illusion!')."),
        L('link:gong1_up', 'gong1', 'landing2', 'door', condition={'map_var': 'gong1'},
          notes="gong 1: three rings open the stair door; the stair hall (its own room) climbs to the den."),
        L('link:l2_mess', 'landing2', 'mess', 'open'),
        L('link:mess_fence', 'mess', 'fence', 'door'),
        L('link:fence_treasury', 'fence', 'alibaba', 'door'),
        L('link:fence_gong2', 'fence', 'gong2', 'open'),
        L('link:gong2_bunks', 'gong2', 'bunks', 'door'),
        L('link:bunks_l2', 'bunks', 'landing2', 'open'),
        L('link:gong2_up', 'gong2', 'landing3', 'door', condition={'map_var': 'gong2'},
          notes="gong 2: the stair door; the stair hall climbs to the practice floor."),
        L('link:l3_practice', 'landing3', 'practice', 'open'),
        L('link:l3_trap', 'landing3', 'trap_walk', 'open'),
        L('link:trap_practice', 'trap_walk', 'practice', 'door'),
        L('link:trap_strong', 'trap_walk', 'strongroom', 'door',
          **({'condition': {'item': 'strongroom_key'}} if STRONGROOM_KEY else {}),
          notes="The strongroom's iron door: the Strongroom key from the fence's lockbox." + ("" if STRONGROOM_KEY else " BLOCKED until A2's item row exists: the door stays locked.")),
        L('link:practice_gong3', 'practice', 'gong3', 'open'),
        L('link:gong3_up', 'gong3', 'landing4', 'door', condition={'map_var': 'gong3'},
          notes="gong 3: the stair door; the stair hall climbs to the top."),
        L('link:l4_counting', 'landing4', 'counting', 'door'),
        L('link:l4_library', 'landing4', 'library', 'open'),
        L('link:counting_bed', 'counting', 'bedchamber', 'door'),
        L('link:counting_getaway', 'counting', 'getaway', 'open'),
        L('link:getaway_roof', 'getaway', 'roof_stair', 'open',
          notes="The roof stair (D-58); its trapdoor leads one way up to D7 (exit:d7_roof), live to D7 after m30.done."),
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "A lone Mok tower in the Southern Woods, taken over by the Thieves' Guild: four storeys stacked in one map. Each floor's stair up is behind a door that a bronze gong opens (three rings: the guild's memo by the first gong says so, and the Ali Baba chest's word); the stairs alternate sides so every floor is crossed. The front: lookouts, hounds, a tapestry with a false wall. The den: mess, bunks, the fence and the treasury with the Ali Baba chest. The practice floor: dummies, a trap walk, the strongroom. The inner circle under the cone: the library, the counting room where the Master Thief sits behind his ledger, his bedchamber, and the getaway chute down to the front.",
        'purpose': "Q-D19 The Southern Tower: the ledger (q-d19.ledger), the Ali Baba chest (q-d19.ali_baba: the Eastern Tower key), 2 Energy Disks in the strongroom (q-d19.l3_disks, M18), the Master Thief (NPC 5109: the Dark promotion, q-d19.master_thief). Party 22 to 26, Outlaws 12/18/30 and the guild's hounds 16/22, The Master Thief 32, 45 monsters and the boss, treasure level 3 with the bedchamber's hoard at 4.",
        'mood': "Green-grey Mok stone the thieves have made comfortable: boards, beams, bunks, loot sorted on tables, lamps; a hushed, watchful house of crooks.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:front', 'spaces': ['room:door_hall', 'room:guardroom', 'room:gong1', 'room:kennel', 'room:tapestry'],
             'notes': "Round the ground floor."},
            {'id': 'loop:den', 'spaces': ['room:landing2', 'room:mess', 'room:fence', 'room:gong2', 'room:bunks'],
             'notes': "Round the den floor."},
            {'id': 'loop:practice', 'spaces': ['room:landing3', 'room:practice', 'room:trap_walk'],
             'notes': "Through the practice hall or the trap walk."},
            {'id': 'loop:getaway', 'spaces': ['room:door_hall', 'room:gong1', 'room:stair1', 'room:landing2', 'room:gong2',
                                              'room:stair2', 'room:landing3', 'room:practice', 'room:gong3', 'room:stair3',
                                              'room:landing4', 'room:counting', 'room:getaway'],
             'notes': "Up by the gong stairs, down by the getaway chute."},
        ],
        'entrances': [
            {'id': 'entrance:d2_door', 'space': 'room:door_hall', 'kind': 'both', 'neighbour': 'exit:d2_door', 'facing': 's',
             'how': "From D2's door:dd06 (the tower's iron-bound door, facing north in its clearing; the Southern Tower key): just inside the door in the hall's north wall, facing in (south); the same door leads back out (the exit preset, D-24)."}],
        'critical_path': ['room:door_hall', 'room:guardroom', 'room:gong1', 'room:stair1', 'room:landing2', 'room:mess',
                          'room:fence', 'room:alibaba', 'room:fence', 'room:gong2', 'room:stair2', 'room:landing3',
                          'room:trap_walk', 'room:strongroom', 'room:trap_walk', 'room:practice', 'room:gong3',
                          'room:stair3', 'room:landing4', 'room:counting'],
        'return_path': ['room:counting', 'room:getaway', 'room:door_hall'],
        'goals': [
            {'id': 'goal:ledger', 'space': 'room:counting', 'kind': 'use', 'story': 'Q-D19',
             'what': "The ledger on the big desk (A3's hook q-d19.ledger: ledger_read 113381, the autonote).",
             'gives': {'qbit': 113381}},
            {'id': 'goal:alibaba', 'space': 'room:alibaba', 'kind': 'use', 'story': 'Q-D19',
             'what': "'What's the password?' open sesame (A3's hook q-d19.ali_baba: the Eastern Tower key 12340, chest_opened 113383).",
             'gives': {'qbit': 113383}},
            {'id': 'goal:disks', 'space': 'room:strongroom', 'kind': 'use', 'story': 'M18',
             'what': "The strongroom's chest: 2 Energy Disks (q-d19.l3_disks, tower_disks 113382).",
             'gives': {'qbit': 113382}},
            {'id': 'goal:master', 'space': 'room:counting', 'kind': 'use', 'story': 'Q-D19',
             'what': "The Master Thief (NPC 5109): his Inner circle topic promotes Rogues and Warrior Mages (Dark)."},
        ],
        'keys': [
            {'id': 'key:gong1', 'grants': {'map_var': 'gong1'}, 'found_in': 'room:gong1',
             'how': "'Ring gong how many times?' 3 or three (the memo beside it)."},
            {'id': 'key:gong2', 'grants': {'map_var': 'gong2'}, 'found_in': 'room:gong2', 'how': "The same answer."},
            {'id': 'key:gong3', 'grants': {'map_var': 'gong3'}, 'found_in': 'room:gong3', 'how': "The same answer."},
            {'id': 'key:button', 'grants': {'map_var': 'illusion'}, 'found_in': 'room:tapestry',
             'how': "The button at the tapestry's end."},
        ] + ([{'id': 'key:strongroom', 'grants': {'item': 'strongroom_key'}, 'found_in': 'room:fence',
               'how': "The Strongroom key, a fixed item in the fence's lockbox."}] if STRONGROOM_KEY else []),
        'set_pieces': [
            {'id': 'set:gongs', 'kind': 'scripted', 'spaces': ['room:gong1', 'room:gong2', 'room:gong3'],
             'rule': "Each gong asks 'Ring gong how many times?': 3 or three opens its stair door (A3's q-d19.gongs line); any other answer: 'The gong booms, and the echo dies away.', the door stays shut and the next click asks again."},
            {'id': 'set:alibaba', 'kind': 'scripted', 'spaces': ['room:alibaba'],
             'rule': "'Ali Baba Chest. What's the password?': open sesame or opensesame opens it, once; then it opens like any chest."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 46, 'chests': 5, 'doors': 13,
                   'loops': 4, 'floor_area_munits2': 40},
        'notes': "Size M (MAPS: 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/dd06.graph.yml and D-25 (mockups/act3_a7_decisions.md: the bodyguards Inner Circle Guards 11115, the Master Thief's boss row 11114 at 32, no mirror, the wrong gong answer's line). The three stair halls are rooms of their own (the graph's gong-to-landing stair links). The roof stair (D-58) up to D7's entrance:dd06_roof. " + f"{len(ROOMS)} rooms.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """DD-06 Southern Tower (not to scale; floors stacked 640 apart, north up within each floor)

 1920 inner circle   [BEDCHAMBER: bed, T4 hoard]
                                |door
                                                                  [ROOF STAIR] ==trapdoor, one way up (D-58)==> D7
                                                                        |
                     [COUNTING ROOM: desk, ledger, the Master Thief + 4 guards] -- [getaway hatch] ==chute==> entrance hall
                         |door          |
       (stair 3 head) [TOP LANDING] -- [LIBRARY: Manual, Prince Book]
                ^ west stair (gong 3's door)
 1280 practice       [GONG 3] -- [PRACTICE HALL: dummies, targets] -- [PRACTICE LANDING] <- (stair 2 head)
                                       |door                             |
                                 [TRAP WALK] =iron door, Strongroom key= [STRONGROOM: 2 disks, T3]
                                                                         ^ east stair (gong 2's door)
  640 den            [BUNKROOM] --door-- [GONG 2] ---------------------------+
                         |                  |
       (stair 1 head) [DEN LANDING] -- [MESS] --door-- [FENCE: lockbox, key] --door-- [TREASURY: Ali Baba chest]
                ^ west stair (gong 1's door)
    0 front          [LOOKOUTS] --door-- [ENTRANCE HALL: straw heap] =front door, sealed= (D2)
                         |                   |
                     [GONG 1: memo] -- [TAPESTRY HALL] =false wall= [stash, T3]
                         |gate              |
                     [KENNEL: hounds] ------+
"""

# ================================================================================================ objects.yml
START = [640, 1700]
STRAW_AT = [1760, 1780]
objects = {
    'format': 0,
    'start': {'room': 'room:door_hall', 'at': START, 'facing': 's',
              'notes': "Inside the tower's door from D2 (the door in the north wall at x 640), facing in (south)."},
    'doors': [],
    'exits': [
        {'id': 'exit:front_door', 'room': 'room:door_hall', 'at': [640, 2048], 'size': [192, 384],
         'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:d2_door',
         'notes': "The tower's iron-bound door in the hall's north wall, out to D2 (Sprite Forest, the Southern Woods)."}],
    'switches': [
        {'id': 'switch:button', 'room': 'room:tapestry', 'kind': 'button', 'at': [1152, 830], 'height': 112,
         'notes': "The button at the tapestry's north end ('Button')."},
    ],
    'chests': [
        {'id': 'chest:stash', 'room': 'room:stash', 'at': [1950, 0], 'kind': 'ch3', 'facing': 'n',
         'treasure_level': 3, 'random_items': 2, 'gold': 450, 'notes': "A thief's private stash behind the illusion."},
        {'id': 'chest:lockbox', 'room': 'room:fence', 'at': [1220, -1990], 'kind': 'ch1', 'facing': 'n',
         'treasure_level': 3, 'random_items': 2, 'gold': 300, **({'items': ['strongroom_key']} if STRONGROOM_KEY else {}),
         'notes': "The fence's lockbox: the Strongroom key and the week's takings."},
        {'id': 'chest:alibaba', 'room': 'room:alibaba', 'at': [1792, -1792], 'kind': '7gt002', 'size': [192, 96, 80], 'treasure_level': 3, 'random_items': 3, 'gold': 800,
         'notes': "The Ali Baba chest on its dais (its password at evt:alibaba): the thieves' takings (D-89, 2026-11-22: the Eastern Tower is open, so no key; A3's receipt line says where the jewel went)."},
        {'id': 'chest:strongroom', 'room': 'room:strongroom', 'at': [1950, -1600], 'kind': '7gt002', 'facing': 'n',
         'treasure_level': 3, 'random_items': 2, 'gold': 600, 'items': ['energy_disk', 'energy_disk'],
         'notes': "The guild's best takings and 2 Energy Disks wrapped in an invoice made out to nobody (q-d19.l3_disks)."},
        {'id': 'chest:hoard', 'room': 'room:bedchamber', 'at': [480, 1950], 'kind': '7gt002', 'facing': 'w',
         'treasure_level': 4, 'random_items': 3, 'gold': 1500, 'trap_level': 3,
         'notes': "The Master Thief's own strongbox beside his bed: the tower's hoard (a level up)."},
    ],
    'monsters': [],
    'decorations': [],
    'lights': [],
    'sounds': [
        {'id': 'sound:stew', 'room': 'room:mess', 'at': [-300, -1220], 'sound': 'campfire', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "The stew pot's fire."},
        {'id': 'sound:wind', 'room': 'room:counting', 'at': [-256, -64], 'sound': 'whistling wind', 'radius': 2400,
         'inner_radius': 800, 'volume': 0.35, 'notes': "Wind round the slate cone."},
    ],
}

doors = [
    ('door:hall_guard', 'open:hall_guard', PLANKS, 'slide_left', "The lookouts' plank door."),
    ('door:gong1', 'open:gong1_stair', STONEDOOR, 'slide_up', "The first stair door: shut until the gong is rung three times."),
    ('door:kennel_gate', 'open:gong1_kennel', BARS_GATE, 'slide_up', "The kennel's barred gate."),
    ('door:mess_fence', 'open:mess_fence', PLANKS, 'slide_left', "The fence's door."),
    ('door:treasury', 'open:fence_treasury', IRON, 'slide_left', "The treasury's iron-bound door."),
    ('door:bunks', 'open:gong2_bunks', PLANKS, 'slide_left', "The bunkroom door."),
    ('door:gong2', 'open:gong2_stair', STONEDOOR, 'slide_up', "The second stair door, opened by its gong."),
    ('door:trap_practice', 'open:trap_practice', PLANKS, 'slide_left', "The door from the trap walk to the practice hall."),
    ('door:strongroom', 'open:trap_strong', IRON, 'slide_left', "The strongroom's iron door: the Strongroom key."),
    ('door:gong3', 'open:gong3_stair', STONEDOOR, 'slide_up', "The third stair door, opened by its gong."),
    ('door:counting', 'open:landing4_counting', PLANKS, 'slide_left', "The counting room's door."),
    ('door:bedchamber', 'open:counting_bed', PLANKS, 'slide_left', "The bedchamber's door."),
]
for did, op, surf, kind, notes in doors:
    objects['doors'].append({'id': did, 'opening': op, 'kind': kind, 'fold': True, 'surface': surf, 'tile': True,
                             'speed': 192, 'notes': notes})
# The plank doors show a door (the orchestrator's F12(b) decision, A7 s27): MM8's plank door pair (gkp103a/b), one
# wing on each of two leaves 128 by 256 at their own size (the doorways 256 high).
PLANK_PAIR = [[S('gkp103a', 128, 256), S('gkp103b', 128, 256)]]
for d in objects['doors']:
    if d['surface'] is PLANKS:
        d.update(leaves=2, pictures=PLANK_PAIR, back_pictures=PLANK_PAIR)
objects['doors'].append({'id': 'door:illusion', 'opening': 'open:tapestry_stash', 'kind': 'slide_down', 'fold': True,
                         'surface': ASHLAR, 'tile': True, 'secret': True, 'speed': 1200,
                         'notes': "The false wall: the hall's own ashlar, a secret face; the button drops it at once ('An illusion!')."})

for rid, group, ms in PLACED:
    for n, (mon, at, facing) in enumerate(ms, 1):
        objects['monsters'].append({'id': f'monster:{rid}_{n}', 'room': 'room:' + rid, 'monster': mon, 'at': at,
                                    'facing': facing, 'hostile': True, 'group': group})
for n, at in enumerate(GUARDS, 1):
    objects['monsters'].append({'id': f'monster:guard_{n}', 'room': 'room:counting', 'monster': GUARD, 'at': at,
                                'facing': 270, 'group': 30, 'immobile': True,
                                'notes': "An Inner Circle Guard (11115, faction inner_circle, friendly until attacked)."})
objects['monsters'].append({'id': 'monster:master_thief', 'room': 'room:counting', 'monster': BOSS, 'at': BOSS_AT,
                            'facing': 270, 'group': 31, 'immobile': True, 'npc': 5109,
                            'notes': "The Master Thief (A2's boss row 11114, level 32, faction inner_circle, friendly until attacked) by his high chair; he is NPC 5109: clicked while peaceful, he talks (merge point 22, monsters[].npc)."})

# Lights: one or two lamps per room (warm thieves' lamps), the stair halls dimmer.
LAMP = [230, 180, 120]
COOL = [170, 175, 185]
for rid, (name, b, fl, ce, theme) in ROOMS.items():
    x0, y0, x1, y1 = b
    w, d = x1 - x0, y1 - y0
    pts = [[(x0 + x1) // 2, (y0 + y1) // 2]]
    if max(w, d) > 1800:
        if w >= d:
            pts = [[x0 + w // 4, (y0 + y1) // 2], [x1 - w // 4, (y0 + y1) // 2]]
        else:
            pts = [[(x0 + x1) // 2, y0 + d // 4], [(x0 + x1) // 2, y1 - d // 4]]
    if rid == 'roof_stair':
        # The roof stair: a lamp over the foot beside the flight, and one over the head under the hatch (each measured
        # from the floor under it; the room's middle is over the steps).
        objects['lights'] += [
            {'id': 'light:roof_stair_1', 'room': 'room:roof_stair', 'at': [1120, 1100], 'floor_height': 1920,
             'height': 460, 'radius': 1200, 'color': LAMP},
            {'id': 'light:roof_stair_2', 'room': 'room:roof_stair', 'at': [1120, 1900], 'floor_height': ROOF_HEAD,
             'height': 200, 'radius': 900, 'color': LAMP}]
        continue
    for i, at in enumerate(pts, 1):
        stair = rid.startswith('stair')
        objects['lights'].append({'id': f'light:{rid}_{i}', 'room': 'room:' + rid, 'at': at,
                                  'height': min(ce - fl - 96, 460),
                                  'radius': 1400 if max(w, d) > 1000 else 1000,
                                  'color': COOL if stair else LAMP})

# Decorations (D-7: containers by walls in pairs, nothing on a walking line).
DECOS = [
    # front
    ('hall_barrel_1', 'door_hall', 'bigbarel', [-60, 1990]), ('hall_barrel_2', 'door_hall', 'bigbarel', [30, 1990]),
    ('hall_torch_1', 'door_hall', 'torch01', [380, 1990]), ('hall_torch_2', 'door_hall', 'torch01', [900, 1990]),
    ('guard_keg_1', 'guardroom', 'smlbarel', [-1990, 1500]), ('guard_keg_2', 'guardroom', 'smlbarel', [-1990, 1590]),
    ('guard_candle', 'guardroom', 'cndlab0', [-1500, 1700]), ('guard_plates', 'guardroom', 'dec36', [-1440, 1660]),
    ('guard_torch', 'guardroom', 'torch01', [-310, 1990]),
    ('gong1_torch_1', 'gong1', 'torch01', [-1230, 300]), ('gong1_torch_2', 'gong1', 'torch01', [-1230, -400]),
    ('tap_torch_1', 'tapestry', 'torch01', [-80, 700]), ('tap_torch_2', 'tapestry', 'torch01', [-80, -700]),
    ('stash_sack_1', 'stash', 'bag01', [1960, 400]), ('stash_sack_2', 'stash', 'bag01', [1960, 300]),
    ('kennel_bones_1', 'kennel', '7dec18', [-1220, -1220]), ('kennel_bones_2', 'kennel', 'dec29', [1090, -1220]),
    ('kennel_bucket', 'kennel', 'Bucket', [-1220, -1990]),
    # den
    ('mess_pot', 'mess', 'cauld00', [-300, -1220]), ('mess_bowl', 'mess', 'foodbowl', [-100, -1290]),
    ('mess_plates', 'mess', 'dec36', [200, -1300]), ('mess_goblet', 'mess', '7dec48', [150, -1900]),
    ('mess_cask_1', 'mess', '7dec21', [445, -2000]), ('mess_cask_2', 'mess', '7dec21', [448, -1888]),
    ('fence_sack_1', 'fence', 'floursac', [700, -1990]), ('fence_sack_2', 'fence', 'bag_A', [800, -1995]),
    ('fence_plates', 'fence', 'dec39', [960, -1930]),
    ('treasury_torch_1', 'alibaba', 'torch01', [1460, -1990]), ('treasury_torch_2', 'alibaba', 'torch01', [1460, -1210]),
    ('bunks_trash', 'bunks', 'trasheap', [-1140, -880]), ('bunks_sack_1', 'bunks', 'bag01', [200, -950]),
    ('bunks_sack_2', 'bunks', 'bag01', [80, -950]),
    ('gong2_torch_1', 'gong2', 'torch01', [440, -960]), ('gong2_torch_2', 'gong2', 'torch01', [440, 450]),
    # practice floor
    ('strong_barrel_1', 'strongroom', 'bigbarel', [1470, -1210]), ('strong_barrel_2', 'strongroom', 'bigbarel', [1560, -1210]),
    ('gong3_torch_1', 'gong3', 'torch01', [-560, 190]), ('gong3_torch_2', 'gong3', 'torch01', [-560, 1090]),
    ('trap_torch_1', 'trap_walk', 'torch01', [1230, 0]), ('trap_torch_2', 'trap_walk', 'torch01', [1230, -1200]),
    # inner circle
    ('count_coins_1', 'counting', 'bag_A', [700, 840]), ('count_coins_2', 'counting', 'bag_A', [610, 840]),
    ('count_candle_1', 'counting', 'cndlab0', [-430, 300]), ('count_candle_2', 'counting', 'cndlab0', [-80, 300]),
    ('count_chandelier', 'counting', 'dec27', [-256, -64]),
    ('count_cask_1', 'counting', '7dec21', [-1212, 836]), ('count_cask_2', 'counting', '7dec21', [-1220, 725]),
    ('lib_candle', 'library', 'dec02', [-330, -1210]),
    ('bed_candle', 'bedchamber', 'dec02', [-150, 1960]), ('bed_goblet', 'bedchamber', '7dec46', [700, 1100]),
    ('roof_torch', 'roof_stair', 'torch01', [1036, 1180]),
]
WALL_TORCH_HEIGHT = 176   # the lamp rule (the user, 2026-11-20): a wall torch on its wall, not standing on the floor


def on_wall(rid, at, inset=12):
    """The point moved onto the nearest side of its room's rectangle, `inset` inside it (a bracket's depth)."""
    x0, y0, x1, y1 = ROOMS[rid][1]
    x, y = at
    side = min((x - x0, 'w'), (x1 - x, 'e'), (y - y0, 's'), (y1 - y, 'n'))[1]
    return {'w': [x0 + inset, y], 'e': [x1 - inset, y], 's': [x, y0 + inset], 'n': [x, y1 - inset]}[side]


for key, rid, deco, at in DECOS:
    d = {'id': f'deco:{key}', 'room': 'room:' + rid, 'decoration': deco, 'at': at}
    if deco == 'torch01':
        d.update(at=on_wall(rid, at), height=WALL_TORCH_HEIGHT)
    objects['decorations'].append(d)

# ================================================================================================ wiring.yml
GONG_ASK = "Ring gong how many times?"
GONG_WRONG = "The gong booms, and the echo dies away."


# AU's gong (devdocs/xeen/AUDIO.md, A7's row): struck on every answer, at the gong's face (A7, eighth session).
GONG_AT = {1: (-1270, -400, 256), 2: (1270, -96, 896), 3: (-1270, 864, 1536)}


def gong_sound(n):
    x, y, z = GONG_AT[n]
    return {'lua': f'evt.PlaySoundName("xeen_gong", {x}, {y}, {z})'}


def gong_events(n, door):
    return [
        {'id': f'evt:gong{n}', 'preset': 'script', 'source': f'panel:gong{n}', 'title': 'Gong',
         'condition': {'not': {'map_var': f'gong{n}'}},
         'question': {'ask': GONG_ASK, 'answers': ['3', 'three'], 'wrong_text': GONG_WRONG,
                      'wrong_effects': [gong_sound(n)]},
         'opens': [door],
         'effects': [gong_sound(n), {'set': {'var': {'map_var': f'gong{n}'}, 'value': 1}},
                     {'lua': 'XeenQuests.hook("q-d19.gongs")'}],
         'else_effects': [{'text': "The gong still hums. The stair door beside it stands open."}],
         'notes': f"state:gong{n} (aaze0062:2, answers :3-4): 3 or three opens the stair door (A3's q-d19.gongs line); D-25 Q13: any other answer '{GONG_WRONG}', the door stays shut, the next click asks again."},
        {'id': f'evt:stair_door{n}', 'preset': 'door', 'source': door, 'title': 'Stair door', 'action': 'open',
         'condition': {'map_var': f'gong{n}'},
         'locked_text': "The stone door will not move. A bronze gong hangs on the wall beside it.",
         'notes': f"The stair door: shut until gong {n} is answered; then it opens and stays open."},
    ]


# The Prince Book: A3's q-d19.prince_book decides by q-c9's throne bit 11302 itself (the lane lead, 2026-11-20: one hook
# for every member; the map reads and sets no player bit of its own for it).
PRINCE_LUA = 'XeenQuests.hook("q-d19.prince_book")'

events = []
events += gong_events(1, 'door:gong1') + gong_events(2, 'door:gong2') + gong_events(3, 'door:gong3')
events += [
    {'id': 'evt:front_door', 'preset': 'exit', 'source': 'exit:front_door', 'title': 'Tower door',
     'text': "You step out into the tower's clearing.",
     'notes': "Out to D2's clearing in front of door:dd06 (A6's point; D-24: the exit preset, the source's 'Exit the Great Southern Tower?' is not used)."},
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 6,
     'text': "The Great Southern Tower. Someone has chalked a fresh mark on the inside of the door: the guild's sign.",
     'notes': "Arrival line (one-shot timer: the party arrives standing in the hall)."},
    {'id': 'evt:memo', 'preset': 'script', 'source': 'panel:memo', 'title': 'Memo',
     'lua': 'XeenQuests.hook("q-d19.guild_memo")',
     'notes': "The answer-giver for the gongs and the chest (A3's q-d19.guild_memo; 'A note reads: Three's the charm.', aaze0064:9)."},
    {'id': 'evt:tapestry', 'preset': 'text', 'source': 'panel:tapestry_a', 'title': 'Tapestry',
     'text': "Tapestry. A procession of Mok priests winds round the tower, faded almost to grey. At its north end, half hidden by the cloth, a button.",
     'seconds': 5, 'notes': "aaze0061:4."},
    {'id': 'evt:tapestry_b', 'preset': 'text', 'source': 'panel:tapestry_b', 'title': 'Tapestry',
     'text': "Tapestry. A procession of Mok priests winds round the tower, faded almost to grey. At its north end, half hidden by the cloth, a button.",
     'seconds': 5, 'notes': "aaze0061:4."},
    {'id': 'evt:button', 'preset': 'switch', 'source': 'switch:button', 'title': 'Button',
     'opens': ['door:illusion'], 'effects': [{'set': {'var': {'map_var': 'illusion'}, 'value': 1}}],
     'text': "Click. The wall beside the tapestry is gone. An illusion!", 'seconds': 5,
     'notes': "state:button (aaze0061:5, :7): the false wall drops at once."},
    {'id': 'evt:illusion', 'preset': 'door', 'source': 'door:illusion', 'title': 'Wall', 'action': 'open',
     'condition': {'map_var': 'illusion'}, 'locked_text': "Cold stone.",
     'notes': "The false wall itself: clicked before the button, plain stone."},
    {'id': 'evt:hall_guard', 'preset': 'door', 'source': 'door:hall_guard', 'title': 'Door'},
    {'id': 'evt:kennel_gate', 'preset': 'door', 'source': 'door:kennel_gate', 'title': 'Kennel gate'},
    {'id': 'evt:mess_fence', 'preset': 'door', 'source': 'door:mess_fence', 'title': 'Door'},
    {'id': 'evt:treasury', 'preset': 'door', 'source': 'door:treasury', 'title': 'Door'},
    {'id': 'evt:bunks', 'preset': 'door', 'source': 'door:bunks', 'title': 'Door'},
    {'id': 'evt:trap_practice', 'preset': 'door', 'source': 'door:trap_practice', 'title': 'Door'},
    {'id': 'evt:strongroom', 'preset': 'door', 'source': 'door:strongroom', 'title': 'Iron door', 'action': 'open',
     'condition': {'item': 'strongroom_key'} if STRONGROOM_KEY else {'lua': 'false'},
     'locked_text': "The iron door is locked. The keyhole is cut for a heavy key.",
     'notes': "state:strong_key: the Strongroom key from the fence's lockbox (A2's item 12262)."},
    {'id': 'evt:counting', 'preset': 'door', 'source': 'door:counting', 'title': 'Door'},
    {'id': 'evt:bedchamber', 'preset': 'door', 'source': 'door:bedchamber', 'title': 'Door'},
    {'id': 'evt:chest_stash', 'preset': 'chest', 'source': 'chest:stash', 'title': 'Chest'},
    {'id': 'evt:chest_lockbox', 'preset': 'chest', 'source': 'chest:lockbox', 'title': 'Chest'},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest'},
    {'id': 'evt:chest_strongroom', 'preset': 'chest', 'source': 'chest:strongroom', 'title': 'Chest',
     'effects': [{'lua': 'XeenQuests.hook("q-d19.l3_disks")'}],
     'notes': "goal:disks: the chest holds the 2 Energy Disks (q-d19.l3_disks map_gives); the hook sets tower_disks 113382 and says 'Energy Disc ...' (aaze0063:0) once."},
    {'id': 'evt:alibaba', 'preset': 'chest', 'source': 'chest:alibaba', 'title': 'Chest',
     'condition': {'not': {'map_var': 'sesame'}},
     'question': {'message': "Ali Baba Chest. What's the password?", 'ask': "What's the password?",
                  'answers': ['open sesame', 'opensesame']},
     'effects': [{'set': {'var': {'map_var': 'sesame'}, 'value': 1}}, {'lua': 'XeenQuests.hook("q-d19.ali_baba")'}],
     'else_effects': [{'open_chest': 'chest:alibaba'}],
     'notes': "state:alibaba (aaze0063:6, answers :7-8): the password once, then the chest opens (the Eastern Tower key 12340 is its item, F15; A3's q-d19.ali_baba sets chest_opened 113383 and its status line); once the word is given it opens like any chest (else_effects); a wrong word does nothing."},
    {'id': 'evt:ledger', 'preset': 'script', 'source': 'platform:desk', 'title': 'Ledger',
     'lua': 'XeenQuests.hook("q-d19.ledger")',
     'notes': "goal:ledger (aaze0062:1, A3's text): ledger_read 113381 and the autonote; later 'The ledger. The prices are obscene.'"},
    {'id': 'evt:master_slain', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:master_thief'}},
     'lua': 'XeenQuests.hook("q-d19.master_thief")',
     'notes': "A3's q-d19.master_thief on his death (master_slain 113384; the Dark promotion lost if not taken)."},
    {'id': 'evt:master_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 113384},
     'effects': [{'hide_actors': 31}],
     'notes': "A slain Master Thief stays dead after a refill: his group is hidden on entry once master_slain is set."},
    {'id': 'evt:manual', 'preset': 'script', 'source': 'platform:manual', 'title': 'Manual of Master Thievery',
     'condition': {'not': {'player_bit': 11295}},
     'effects': [{'lua': 'XeenQuests.hook("q-d19.thievery_manual")'}, {'add': {'var': 'Experience', 'value': 1500}},
                 {'player_bit': 11295}],
     'else_effects': [{'lua': 'XeenQuests.hook("q-d19.thievery_manual_again")'}],
     'notes': "D-25 Q11 (aaze0064:0-1): 1,500 experience to the reading member once (player bit 11295); again: 'You learn nothing new'."},
    {'id': 'evt:prince_book', 'preset': 'script', 'source': 'platform:prince_book', 'title': 'Prince Book',
     'lua': PRINCE_LUA,
     'notes': "D-25 (aaze0064:3-4): A3's q-d19.prince_book decides: a member with q-c9's throne_thieves (11302) reads it once for +2 Luck; others 'For the eyes of the prince only!'."},
    {'id': 'evt:bed', 'preset': 'text', 'source': 'platform:bed', 'title': 'Bed', 'text': "Nothing here.",
     'notes': "aaze0064:7-8."},
    {'id': 'evt:hatch', 'preset': 'teleport', 'source': 'platform:hatch', 'title': 'Trapdoor',
     'to': [STRAW_AT[0], STRAW_AT[1], 32], 'direction': 180,
     'text': "You drop through the trapdoor and slide down the polished chute, round and round inside the tower's wall, into a heap of straw.",
     'seconds': 6,
     'notes': "The getaway chute (one way down, no fall damage): from the top floor to the entrance hall's straw heap."},
    {'id': 'evt:roof_trapdoor', 'preset': 'script', 'source': 'platform:roof_hatch', 'title': 'Roof trapdoor',
     'lua': ('if not XeenQuests.hook("d7.roof_dd06") then\n'
             '    return\n'
             'end\n'
             'evt.MoveToMap(5632, -14848, 710, 1536, 0, 0, 0, 1, "xeen_d7.blv")'),
     'notes': "D-58: A3's d7.roof_dd06 checked first (needs m30.done; else its 'The trapdoor is shut fast.'), then (F16, 2026-11-22) the game's standard entrance window (OK/Close) in place of the old Yes/No; OK goes one way up to D7's entrance:dd06_roof (5632, -14848, 710) facing 1536 at once (D7 is indoor: no leave window; the coordinates are D7's named arrival, written out because the move waits on the answer)."},
    {'id': 'evt:straw', 'preset': 'text', 'source': 'platform:straw_heap', 'title': 'Straw',
     'text': "A heap of straw, flattened in the middle. A polished chute opens in the wall above it.", 'seconds': 4},
    {'id': 'evt:cards', 'preset': 'text', 'source': 'platform:card_table', 'title': 'Card table',
     'text': "A card game left in the middle of a hand. Every hand holds five aces.", 'seconds': 4},
    {'id': 'evt:trap_plate_1', 'preset': 'text', 'trigger': 'step', 'source': 'plate:trap_1',
     'text': "Click. A pressure plate, disarmed. Somebody here trusts you less than that.", 'seconds': 4},
    {'id': 'evt:trap_plate_2', 'preset': 'text', 'trigger': 'step', 'source': 'plate:trap_2',
     'text': "Click. Another pressure plate. Nothing happens, this time.", 'seconds': 4},
    {'id': 'evt:locks', 'preset': 'text', 'source': 'panel:locks', 'title': 'Practice locks',
     'text': "A row of practice locks, each picked open and left hanging.", 'seconds': 4},
]
for i in range(1, 5):
    events.append({'id': f'evt:bunk_{i}', 'preset': 'text', 'source': f'platform:bunk_{i}', 'title': 'Bed',
                   'text': "Nothing here.", 'notes': "aaze0064:7-8 (the purse under the pillow is long gone)."})

objects['plates'] = [
    {'id': 'plate:trap_1', 'room': 'room:trap_walk', 'at': [1024, 200], 'size': [256, 128], 'rise': 4,
     'surface': COBBLE, 'notes': "A disarmed pressure plate."},
    {'id': 'plate:trap_2', 'room': 'room:trap_walk', 'at': [1024, -1150], 'size': [256, 128], 'rise': 4,
     'surface': COBBLE, 'notes': "A disarmed pressure plate."},
]

wiring = {'format': 0, 'variables': ['gong1', 'gong2', 'gong3', 'illusion', 'sesame'], 'events': events}

QBITS = {'ledger_read': 113381, 'tower_disks': 113382, 'chest_opened': 113383, 'master_slain': 113384,
         'inner_circle': 113385}
project = {
    'format': 0, 'id': 'xeen_dd06', 'name': 'Southern Tower', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-06', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [8, 8], 'climbs': 'n'},
    'map_stats': {'id': 9155, 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
                  'perception_difficulty': 7, 'refill_days': 672, 'music': 34, 'environment': 'stone hall',
                  'lock_difficulty': 7, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Outlaw', 'tier': 1, 'per_marker': [2, 3], 'weight': 85},
                            {'monster': 'Xeen Wolf', 'tier': 1, 'per_marker': [1, 2], 'weight': 15}]},
    'neighbours': [
        {'id': 'exit:d2_door', 'to': 'xeen_d2.odm', 'kind': 'door', 'arrival': [15872, -7680, 1056], 'direction': 90,
         'arrival_hint': "D2's Southern Woods, in front of door:dd06 in the tower's clearing, facing away from the tower (north).",
         'notes': "A6's point (2026-11-20, D2 event 20). D2's door:dd06 leads in to this map's start (640, 1700, 0) facing south."},
        {'id': 'exit:d7_roof', 'to': 'xeen_d7.blv', 'kind': 'roof', 'one_way': True, 'arrival': 'entrance:dd06_roof',
         'arrival_hint': "D7 The Skyroads, by the Southern Tower's hatch (A6's entrance:dd06_roof (5632, -14848, 710) facing 1536).",
         'notes': "D-58: the roof trapdoor (evt:roof_trapdoor), one way up after m30.done; D7 installed (A6), live."}],
    'qbits': QBITS,
    'items': {'energy_disk': 12334, **({'strongroom_key': STRONGROOM_KEY} if STRONGROOM_KEY else {})},
    'notes': "Xeen design brief, level L4: DD-06 the Great Southern Tower in D2's Southern Woods, the Thieves' Guild's den (Q-D19). Monsters: A2's Outlaws (6 Rogue 11110 12, 26 Thief 11111 18, 5 Master Thief 11112 30), the guild's hounds (2 Dark Wolf 11410 16, 2 Sabertooth 11411 22), all placed and hostile in groups 10-21 by room; the Master Thief's four bodyguards Inner Circle Guard 11115 (group 30) and The Master Thief 11114 (32, boss row, group 31), faction inner_circle, friendly until attacked; he is NPC 5109 (monsters[].npc: clicked while peaceful, he talks). Map card slots Xeen Outlaw and Xeen Wolf (no rest encounters). Map qbits 110950-110959: none used; A3's Q-D19 bits named (113381-113385). Hooks: q-d19.gongs, guild_memo, ali_baba, l3_disks, ledger, master_thief, thievery_manual(_again), prince_book(_refused). Music 34. Exit: the tower's door to D2 (A6's point (15872, -7680, 1056) facing north); the start is inside it, (640, 1700, 0) facing south.",
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
        p['notes'] = f"Xeen design brief, level {lv}: DD-06 Southern Tower (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: DD-06 Southern Tower, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM)])
print('written L4')
