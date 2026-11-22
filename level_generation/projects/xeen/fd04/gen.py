#!/usr/bin/env python3
"""FD-04 Dragon Tower and the Dungeon of Death: writes the L1-L4 project folders of devdocs/xeen/briefs/fd04.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, atmosphere.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same), L3 (plan and the shell rooms.yml)

Rerun after every change here; never hand-edit the written files (diff L4 against L4/.oymap/last first).
Written by lane A7's FD-04 sub-agent (seventeenth session, 2026-11-21) after FD-03's gen.py, on D-57
(devdocs/xeen/mockups/act6_a7_decisions.md) and output/studio_cal/a7/phase6_maps.md.

Frame: x east, y north, z up; z 0 is the gate hall's floor (X7's crag top 2,600). The tower: four floors 1,280 apart
(z 0, 1280, 2560, 3840) inside a square of 3,072 (|x|, |y| <= 1536), and round it a ring 288 wide (centre 1744) where
the stair winds up: three ramps (path rooms, 288 high, slope about 0.5), the first up the west side, the second along
the north, the third down the east side, each from a landing in a corner of its floor to the next floor's landing.
Every opening between a dragon hall and a landing, a ramp, an alcove or a gallery is 256 x 288 (D-32, D-57 Q29).
The Dungeon of Death lies north of the tower and under it: the crossword (z -1024) under the cellar stair from the gate
hall, Sandro's halls (z -1792) beyond the descent, the gongs and the machine (z -2560) beyond the bone stair."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/fd04'

# Shipped decorations S is to supply (D-57 Q27, RELAYS S): the lizard in Alister's alcove and the nest's eggs. None
# until S names their rows; then set the names and rerun: the lizard is placed hidden and shown with Alister's going,
# the three eggs placed and one hidden with the egg taken (118146).
S_LIZARD = 'xeen_lizard'  # lane S's row 4049: MM8's Thunder Lizard, still, 50 tall (origin at its feet)
S_EGG = 'xeen_dragonegg'   # lane S's row 4048: the Dragon Egg item's own ground model at 2.34x (58 x 40)


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.SafeDumper.add_representer(Flow, flow_rep)


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ surfaces
# The tower: MM6 Hall of the Fire Lord 6d04's black vlc block (the kit of X7's shell). Sandro's halls and the
# crossword: MM8 Necromancers' Guild d19. The machine floor: MM6 Control Center sci-fi.blv with XD-19's four cores.
# New (Codex, output/studio_cal/fd04/tex): xfgrid (a crossword cell), xfword (the same cell lit).
BASALT = S('vlcwl2', 128, 256)
BASALT_FOOT = S('vlcwl2b', 128, 256)
VEINED = S('vlcwl4', 128, 256)
GRAVEL = S('vlcflore', 128, 128, scale=2)
TOWER_CEIL = S('vlcgnrc1', 256, 256)
RUNE = S('vlctrm4', 128, 128, fit=True)
LAVA_RUNE = S('vlctrm8', 128, 128, fit=True)
TOWER_DOOR = S('vlcdora', 256, 256)
GATE = S('vlcdora', 256, 256, fit=True)
NSTONE = S('gnecwal1', 256, 256)
NDARK = S('gnecwal3', 128, 256)
NFLOOR = S('gnecflr', 128, 128, scale=2)
NCEIL = S('gnecclg2', 128, 256)
SLATE = S('gn_mtl03', 128, 128)
MARBLE = S('tws1f', 128, 128, scale=2)
MARBLE_TAN = S('tws1f', 128, 128, scale=2)
NDOOR = S('gnecdr2', 128, 256, fit=True)
WING_L = S('gnecdr1l', 128, 256)
WING_R = S('gnecdr1r', 128, 256)
BEDS = S('t1beds2', 128, 256)
WOOD = S('t1books1', 128, 128)
STEP_F = S('gnecstpf', 128, 32)
TRIM = S('trim9_32', 32, 64)
SWALL = S('swll4dk', 128, 256)
SWALL2 = S('swll4dk', 128, 256)
SFLOOR = S('swfloor2b', 128, 128, scale=2)
SCEIL = S('swceilf', 256, 256)
SDOOR = S('swdoora', 256, 256, fit=True)
SPANEL = S('swpnl', 128, 256, fit=True)
SCREEN = S('trekscrn', 128, 64, fit=True)
GIRDER = S('swfloor2b', 128, 128)
GONG = S('xngong', 128, 128, fit=True)
PLAQUE = S('xdplaque', 128, 128, fit=True)
CELL = S('xfgrid', 128, 128)
CORES = {'fire': 'xcorefire', 'water': 'xcorewater', 'air': 'xcoreair', 'earth': 'xcoreearth'}
SKY = S('vlcgnrc1', 256, 256, sky=True)

themes = [
    {'id': 'theme:tower', 'wall': BASALT, 'floor': GRAVEL, 'ceiling': TOWER_CEIL, 'reveal': BASALT,
     'door': TOWER_DOOR, 'notes': "The Dragon Tower: 6d04's black basalt columns, grey gravel floors, dark granite "
                                  "ceilings, statue doors."},
    {'id': 'theme:tower_hall', 'wall': VEINED, 'floor': GRAVEL, 'ceiling': TOWER_CEIL, 'reveal': BASALT,
     'door': TOWER_DOOR, 'notes': "The dragons' halls: 6d04's black rock with glowing veins."},
    {'id': 'theme:necro', 'wall': NSTONE, 'floor': NFLOOR, 'ceiling': NCEIL, 'reveal': NSTONE, 'door': NDOOR,
     'notes': "Sandro's halls and the crossword: d19's grey stone, paved floors with bronze lines."},
    {'id': 'theme:necro_dark', 'wall': NDARK, 'floor': SLATE, 'ceiling': NCEIL, 'reveal': NSTONE, 'door': NDOOR,
     'notes': "The crypt and the bone stair: d19's dark lumpy stone, slate floors."},
    {'id': 'theme:crossword', 'wall': NSTONE, 'floor': SLATE, 'ceiling': NCEIL, 'reveal': NSTONE, 'door': NDOOR,
     'notes': "The crossword hall: d19's grey stone over a dark slate floor (the crossword's black squares)."},
    {'id': 'theme:ballroom', 'wall': NSTONE, 'floor': MARBLE, 'ceiling': NCEIL, 'reveal': NSTONE, 'door': NDOOR,
     'notes': "The ballroom: white marble under grey stone."},
    {'id': 'theme:game', 'wall': NSTONE, 'floor': MARBLE_TAN, 'ceiling': NCEIL, 'reveal': NSTONE, 'door': NDOOR,
     'notes': "The game rooms: tan marble."},
    {'id': 'theme:machine', 'wall': SWALL, 'floor': SFLOOR, 'ceiling': SCEIL, 'reveal': SWALL2, 'door': SDOOR,
     'notes': "The machine floor: the Control Center's dark steel panels, grated floors, riveted ceilings."},
]

# ------------------------------------------------------------------------------------------------ geometry


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def edges(poly):
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def on_edge(poly, p, tol=1.5):
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


rooms, openings, R_ = [], [], {}


def room(id, name, outline, floor, ceiling, theme='theme:tower', **kw):
    d = {'id': id, 'name': name, 'outline': [list(p) for p in outline], 'floor': floor, 'ceiling': ceiling,
         'theme': theme}
    d.update(kw)
    rooms.append(d)
    R_[id] = d
    return d


def ramp(id, name, path, notes):
    d = {'id': id, 'name': name, 'path': [list(p) for p in path], 'width': 288, 'floor': path[0][2],
         'ceiling': path[0][2] + 288, 'theme': 'theme:tower', 'ambient': 12, 'notes': notes}
    rooms.append(d)
    R_[id] = d
    return d


def poly(rid):
    return [tuple(p) for p in R_[rid]['outline']]


def op(id, frm, to, at, width, height, **kw):
    """An opening in the wall of `frm` centred at the point `at` on that wall."""
    pa, pb = poly(frm), poly(to)
    ia, t = on_edge(pa, at)
    jb, _, lo, hi = facing(pa, ia, pb)
    along = (t - lo) / (hi - lo)
    assert width / 2 + 8 <= t - lo and width / 2 + 8 <= hi - t, (id, t, lo, hi, width)
    d = {'id': id, 'from': frm, 'to': to, 'from_wall': ia, 'to_wall': jb, 'along': round(along, 4), 'width': width,
         'height': height}
    d.update(kw)
    openings.append(d)


def op_ramp(id, rid, at, ramp_id, cap, width=256, height=288, ramp_first=False, **kw):
    """An opening between an outline room's wall (at `at`) and a ramp's end cap (3: its top end, 7: its foot)."""
    ia, _ = on_edge(poly(rid), at)
    if ramp_first:
        d = {'id': id, 'from': ramp_id, 'to': rid, 'from_wall': cap, 'to_wall': ia}
    else:
        d = {'id': id, 'from': rid, 'to': ramp_id, 'from_wall': ia, 'to_wall': cap}
    d.update({'width': width, 'height': height})
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
    pa = poly(rid)
    ia, _ = on_edge(pa, at)
    a, b = edges(pa)[ia]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = (-(b[1] - a[1]) / L, (b[0] - a[0]) / L)
    return [round(at[0] + n[0] * d), round(at[1] + n[1] * d)]


def plat(rid, pid, at, size, rise, surface, top, notes, **kw):
    d = {'id': pid, 'at': list(at), 'size': list(size), 'rise': rise, 'surface': surface, 'top_surface': top,
         'notes': notes}
    d.update(kw)
    R_[rid].setdefault('platforms', []).append(d)
    return d


# ================================================================================================ the tower
Z = {0: 0, 1: 1280, 2: 2560, 3: 3840}
DRAGON_OPEN = (256, 288)

# ---------------------------------------------------------------- floor 0 (z 0): the gate hall
room('room:gate_hall', 'Gate hall', rect(-768, -1536, 768, -512), 0, 640, ambient=18,
     bands=[{'height': 160, 'surface': VEINED}, {'height': 480, 'surface': BASALT}],
     notes="Inside the tower's gate (south wall): black basalt columns glowing at their feet. The arrival from X7 "
           "(entrance:x7_gate), quiet; Alister's alcove west, the stair's foot south-west, Sandro's black iron door "
           "north at the head of the cellar stair, the short passage east to the scorched hall.")
room('room:alcove', "Alister's alcove", rect(-1152, -960, -832, -576), 0, 448, ambient=16,
     notes="A shallow alcove off the gate hall's west wall where Alister the druid stands (a placed talking monster, "
           "peaceful, unkillable); hidden when his paying talk closes (118147).")
room('room:landing0', "Stair's foot", rect(-1536, -1536, -832, -1088), 0, 448, ambient=14,
     notes="The foot of the stair that winds up inside the tower's wall; the first ramp leaves it west.")
room('room:scorch_pass', 'Scorched passage',
     [(800, -848), (1360, -848), (1360, -288), (1072, -288), (1072, -560), (800, -560)], 0, 288, ambient=12,
     notes="A low passage (288) from the gate hall east, then north round a turn: the scorched hall's opening is out "
           "of sight of the gate (D-57 'quiet gate hall').")
r = room('room:scorched_hall', 'Scorched hall', rect(320, -224, 1536, 1536), 0, 1024, theme='theme:tower_hall',
         ambient=12, notes="The tower's old stable, scorched to the stone; an Acid pair at its north end, more than "
                           "1,024 from its low opening. Bones and a broken lance-rack by the walls.")
plat('room:scorched_hall', 'platform:stall_1', (384, 500), (128, 640), 160, BASALT, GRAVEL,
     "A stall's low wall of black stone.")
plat('room:scorched_hall', 'platform:stall_2', (1436, 400), (128, 640), 160, BASALT, GRAVEL,
     "A stall's low wall of black stone.")
r = room('room:cellar_stair', 'The cellar well', rect(-224, -448, 224, 1088), -1024, 512, theme='theme:necro_dark',
         ambient=12, notes="Behind Sandro's black iron door: a stair well down 1,024 into the Dungeon of Death, its "
                           "head a landing at the gate hall's floor.")
r['platforms'] = [{'id': 'platform:cellar_head', 'outline': [list(p) for p in rect(-224, -448, 224, -128)],
                   'rise': 1024, 'surface': NDARK, 'top_surface': SLATE,
                   'notes': "The well's head (z 0) behind Sandro's door."}]
r['flights'] = [{'from': [0, 960], 'to': [0, -128], 'width': 256, 'steps': 32,
                 'notes': "32 steps of 32 down to the crossword's floor (z -1,024)."}]

ramp('room:ramp01', 'The stair (first turn)', [(-1568, -1312, 0), (-1744, -1312, 0), (-1744, 1280, 1280),
                                               (-1568, 1280, 1280)],
     "The stair in the tower's wall, a ramp 288 wide and 288 high up the west side from the foot (z 0) to the "
     "first landing (z 1,280): no dragon passes it.")

# ---------------------------------------------------------------- floor 1 (z 1280): the ring hall
z = Z[1]
room('room:landing1', 'First landing', rect(-1536, 1024, -512, 1536), z, z + 448, ambient=14,
     notes="The stair's first landing: the ramp in from the west, the next ramp out north, a low opening south into "
           "the ring hall and the dormitory's door.")
r = room('room:ring_hall', 'Ring hall', rect(-960, -1536, 1536, 960), z, z + 1152, theme='theme:tower_hall',
         ambient=12, notes="A hall 2,496 across and 1,152 high round a thick central pier; three pairs of dragons. "
                           "Low openings (256 x 288) to the landing, the dormitory and the bone alcove.")
r['pillars'] = [{'at': [288, -288], 'size': [768, 768], 'surface': VEINED}]
room('room:dormitory', 'Old dormitory', rect(-1536, -512, -1024, 960), z, z + 512, ambient=14,
     notes="The tower keepers' old beds by the walls, a chest: a door to the landing and a low opening to the ring "
           "hall (the floor-1 loop).")
for i, y in enumerate((-288, 32, 352, 672), 1):
    plat('room:dormitory', f'platform:bed_{i}', (-1460, y), (128, 224), 64, BEDS, BEDS, "An old bed by the wall.")
room('room:bone_alcove', 'Bone alcove', rect(768, 1024, 1536, 1536), z, z + 512, ambient=12,
     notes="A dead end off the ring hall: two dead adventurers' bones and their diaries (q-f1.note_fraud, "
           "q-f1.note_forever).")
ramp('room:ramp12', 'The stair (second turn)', [(-1280, 1568, 1280), (-1280, 1744, 1280), (1280, 1744, 2560),
                                                (1280, 1568, 2560)],
     "The stair along the north side, from the first landing (z 1,280) to the second (z 2,560).")

# ---------------------------------------------------------------- floor 2 (z 2560): the nest
z = Z[2]
room('room:landing2', 'Second landing', rect(384, 1024, 1536, 1536), z, z + 448, ambient=14,
     notes="The stair's second landing: low openings to the nest and the hatchery; the last ramp out east.")
r = room('room:nest', 'The nest', rect(-1536, -1536, 704, 960), z, z + 1152, theme='theme:tower_hall', ambient=12,
         notes="Set piece: a hall 2,240 by 2,496 and 1,152 high round a bowl of black rock where the eggs lie warm "
               "(q-f1.egg). Fire and Frost Dragons over it.")
r['levels'] = [{'id': 'level:bowl', 'outline': [[-800, -672], [-32, -672], [-32, 96], [-800, 96]], 'floor': z - 96,
                'bank': 128, 'surface': S('vlcceila', 128, 128), 'edge': BASALT,
                'notes': "The bowl of black rock, 96 down, its sides sloping."}]
plat('room:nest', 'platform:eggs', (-416, -288), (192, 192), 48, S('vlcceila', 128, 128), S('vlcceila', 128, 128),
     "The warm rock in the bowl's middle where the eggs lie.")
room('room:hatchery', 'Hatchery', rect(768, -768, 1536, 960), z, z + 1024, theme='theme:tower_hall', ambient=12,
     notes="Shell shards and scorched straw in a vault 1,024 high, two pairs; joins the landing and the nest (the "
           "floor-2 loop). A third dead climber's bones (q-f1.note_balls).")
room('room:last_climber', 'The last climber', rect(-1536, 1024, -512, 1536), z, z + 512, ambient=12,
     notes="A dead end off the nest: the last climber's bones and note (q-f1.note_eye), the potion on a shelf "
           "(q-f1.endurance), a chest.")
plat('room:last_climber', 'platform:potion_shelf', (-1472, 1280), (96, 256), 192, WOOD, WOOD,
     "A shelf against the wall with one flask on it.")
ramp('room:ramp23', 'The stair (third turn)', [(1568, 1280, 2560), (1744, 1280, 2560), (1744, -1280, 3840),
                                               (1568, -1280, 3840)],
     "The stair down the east side, from the second landing (z 2,560) to the top floor (z 3,840).")

# ---------------------------------------------------------------- floor 3 (z 3840): the crown
z = Z[3]
room('room:landing3', 'Third landing', rect(320, -1536, 1536, -1024), z, z + 448, ambient=14,
     notes="The stair's top: low openings west into the high hall and north into the Wyrm's gallery.")
room('room:high_hall', 'High hall', rect(-1536, -1536, 256, -192), z, z + 1152, theme='theme:tower_hall',
     ambient=12, notes="The dragons of the Clouds come down to roost here (Phase Dragons) beside a Frost pair; a low "
                       "arch (256 x 288) north into the crown keeps the halls' flyers apart.")
room('room:wyrm_gallery', "Wyrm's gallery", rect(1024, -960, 1536, 1536), z, z + 384, ambient=14,
     notes="A gallery 384 high along the outer wall with the Wyrm's Hall's great door (door:wyrm_hall, house 4853: "
           "Ashkaroth). Quiet; joins the landing and the crown (the floor-3 loop).")
r = room('room:crown', 'The crown', rect(-1024, -128, 960, 1536), z, z + 2048, theme='theme:tower_hall',
         ambient=12, notes="Set piece and the tower's boss: the top hall, 2,048 high, the Energy Dragon and two Phase "
                           "Dragons before the roof stair's door. Every way out is low (256 x 288).")
r['bands'] = [{'height': 1152, 'surface': VEINED}, {'height': 896, 'surface': BASALT}]
room('room:tome_room', 'Tome room', rect(-1536, 768, -1088, 1536), z, z + 512, ambient=14,
     notes="A dead end behind a door off the crown: a bed, the Tome of Great Experience on its stand "
           "(q-f1.tome), a chest.")
plat('room:tome_room', 'platform:tome_stand', (-1312, 1440), (160, 96), 128, WOOD, WOOD,
     "The Tome of Great Experience on a stand of black stone.")
plat('room:tome_room', 'platform:tome_bed', (-1460, 976), (128, 256), 64, BEDS, BEDS, "A bed.")
r = room('room:roof_stair', 'Roof stair', rect(-1536, -128, -1088, 704), z, z + 768, ambient=14,
         notes="Behind the crown's low door: steps up to a head under the open hatch onto the Dragon Clouds (X9). "
               "Its head is entrance:x9_clouds. Quiet.")
r['platforms'] = [{'id': 'platform:roof_head', 'outline': [list(p) for p in rect(-1536, 448, -1088, 704)],
                   'rise': 384, 'surface': BASALT, 'top_surface': GRAVEL,
                   'notes': "The roof stair's head (z 4,224) under the hatch: entrance:x9_clouds."}]
r['flights'] = [{'from': [-1312, 96], 'to': [-1312, 448], 'width': 256, 'steps': 12,
                 'notes': "12 steps of 32 up to the head."}]
r['ceiling_levels'] = [{'outline': [[-1440, 512], [-1184, 512], [-1184, 672], [-1440, 672]], 'ceiling': z + 1280,
                        'edge': BASALT, 'surface': SKY,
                        'notes': "The open hatch over the head: the Dragon Clouds' sky (atmosphere.yml)."}]

# ================================================================================================ the dungeon
# ---------------------------------------------------------------- floor -1 (z -1024): the crossword
ZC, ZS, ZM = -1024, -1792, -2560
r = room('room:crossword', 'The crossword', rect(-1536, 1152, 1536, 3200), ZC, ZC + 768,
         theme='theme:crossword', ambient=14,
         notes="Set piece: a hall 3,072 by 2,048 floored with dark slate, and on it twelve word strips of pale cells "
               "(xfgrid) that cross where their letters match; twelve clue plaques round the walls. A solved word "
               "lights (xfword and a light under it). Two Lich Lords keep it.")
r = room('room:descent', 'The descent', rect(-224, 3264, 224, 4352), ZS, ZS + 1216, theme='theme:necro_dark',
         ambient=12, notes="The stair down beyond the crossword's gate (768 down to Sandro's halls).")
r['platforms'] = [{'id': 'platform:descent_head', 'outline': [list(p) for p in rect(-224, 3264, 224, 3584)],
                   'rise': 768, 'surface': NDARK, 'top_surface': SLATE, 'notes': "The descent's head (z -1,024)."}]
r['flights'] = [{'from': [0, 4288], 'to': [0, 3584], 'width': 256, 'steps': 24,
                 'notes': "24 steps of 32 down to Sandro's halls."}]

# ---------------------------------------------------------------- floor -2 (z -1792): Sandro's halls
H2 = ZS + 640
room('room:welcome', 'Welcome hall', rect(-768, 4416, 768, 5184), ZS, H2, theme='theme:necro', ambient=14,
     notes="A necromancer's front hall ('Welcome', aazex122:0): the double doors north to the ballroom, Do Not "
           "Disturb west; two Lich Lords.")
r = room('room:crypt', 'Do Not Disturb', rect(-1792, 4416, -832, 5184), ZS, ZS + 512, theme='theme:necro_dark',
         ambient=10, notes="Behind the door signed 'Do Not Disturb' (aazex122:4): four coffins that stay shut and a "
                           "chest (D-57 Q34).")
COFFINS = [(-1696, 4640), (-1696, 4960), (-1248, 5088), (-1472, 5088)]
for i, (x, y) in enumerate(COFFINS, 1):
    size = (96, 224) if i <= 2 else (192, 96)
    plat('room:crypt', f'platform:coffin_{i}', (x, y), size, 96, NDARK, SLATE,
         "A coffin, its lid shut (aazex122:5).")
r = room('room:ballroom', 'Ballroom', rect(-1024, 5248, 1024, 6272), ZS, ZS + 768, theme='theme:ballroom',
         ambient=14,
         notes="'Ballroom' (aazex122:1): a long hall of white marble under dead chandeliers; four Skeletal Liches; "
               "open west and east into the two game rooms (the ring).")
for side, x0 in (('west', -2048), ('east', 1088)):
    room(f'room:game_{side}', 'Game room', rect(x0, 5248, x0 + 960, 6272), ZS, H2, theme='theme:game', ambient=14,
         notes="'Game Room' (aazex122:2-3): card tables by the walls.")
    xs = x0 + 96 if side == 'west' else x0 + 864
    plat(f'room:game_{side}', f'platform:table_{side}_1', (xs, 5600), (128, 256), 96, WOOD, S('gnecstpt', 128, 64),
         "A card table by the wall.")
    plat(f'room:game_{side}', f'platform:table_{side}_2', (xs, 5952), (128, 256), 96, WOOD, S('gnecstpt', 128, 64),
         "A card table by the wall.")
room('room:shrines_lesser', 'Shrines of Lesser Evil', rect(-2048, 6336, -1088, 7616), ZS, H2, theme='theme:necro',
     ambient=12, notes="The Shrines of Minor and Lesser Evil (q-f2.shrine_minor, shrine_lesser): destructibles "
                       "against the west wall.")
room('room:shrines_great', 'Shrines of Great Evil', rect(1088, 6336, 2048, 7616), ZS, H2, theme='theme:necro',
     ambient=12, notes="The Shrine of Great Evil and the Shrine of Ultimate Evil (q-f2.shrine_great, "
                       "shrine_ultimate): destructibles against the east wall.")
SHRINES = {'minor': ('room:shrines_lesser', (-1952, 7300)), 'lesser': ('room:shrines_lesser', (-1952, 6650)),
           'great': ('room:shrines_great', (1952, 6650)), 'ultimate': ('room:shrines_great', (1952, 7300))}
for key, (rid, (x, y)) in SHRINES.items():
    plat(rid, f'platform:shrine_{key}', (x, y), (160, 160), 320, NDOOR, S('gnecstpt', 128, 64),
         f"The Shrine of {key.title()} Evil: a black altar stone with a robed figure.")
r = room('room:throne', 'Throne of the Dead', rect(-1024, 6336, 1024, 7616), ZS, ZS + 768, theme='theme:necro',
         ambient=14, notes="Two thrones on a dais (the Throne of the Dead and the Master's Throne, aazex122:8-10), "
                           "two Doom Knights; Sandro's note on the table (q-f2.note). Both shrine galleries meet here.")
r['platforms'] = [
    {'id': 'platform:dais', 'at': [0, 6496], 'size': [1024, 256], 'rise': 64, 'surface': NSTONE, 'top_surface': MARBLE,
     'notes': "The thrones' dais against the south wall."},
    {'id': 'platform:throne_dead', 'at': [-256, 6432], 'size': [192, 128], 'rise': 224, 'surface': NDARK,
     'top_surface': SLATE, 'base': 64, 'notes': "The Throne of the Dead."},
    {'id': 'platform:throne_master', 'at': [256, 6432], 'size': [192, 128], 'rise': 224, 'surface': NDARK,
     'top_surface': SLATE, 'base': 64, 'notes': "The Master's Throne."},
    {'id': 'platform:note_table', 'at': [-928, 7400], 'size': [128, 256], 'rise': 96, 'surface': WOOD,
     'top_surface': S('gnecstpt', 128, 64), 'notes': "A table by the west wall with Sandro's note."}]
r = room('room:bone_stair', 'Bone stair', rect(-224, 7680, 224, 8768), ZM, ZM + 1216, theme='theme:necro_dark',
         ambient=12, notes="A stair of fused bone down 768 to the gongs.")
r['platforms'] = [{'id': 'platform:bone_head', 'outline': [list(p) for p in rect(-224, 7680, 224, 8000)],
                   'rise': 768, 'surface': NDARK, 'top_surface': SLATE, 'notes': "The bone stair's head."}]
r['flights'] = [{'from': [0, 8704], 'to': [0, 8000], 'width': 256, 'steps': 24,
                 'notes': "24 steps of 32 down to the gong hall."}]

# ---------------------------------------------------------------- floor -3 (z -2560): the gongs and the machine
H3 = ZM + 704
room('room:gong_hall', 'Gong hall', rect(-1024, 8832, 1024, 9984), ZM, H3, theme='theme:necro', ambient=14,
     notes="Four gongs on the walls (aazex123:0), a lamp under each that lights when it is rung; the lever by the "
           "iron shutter north; a chest. 'Touch any treasure and you'll have to start over!'")
r = room('room:fountain', 'Fountain', rect(1088, 8960, 1792, 9600), ZM, ZM + 512, theme='theme:necro', ambient=14,
         notes="A dead end with a fountain: 'Ahh, refreshing!' (aazex123:5), any time.")
room('room:maintenance', 'Maintenance', rect(-768, 10048, 768, 10816), ZM, H3, theme='theme:machine', ambient=16,
     notes="'Maintenance' (aazex124:12): racks and a table with papers; two Autobots; ways north to the machine and "
           "west to the control room.")
plat('room:maintenance', 'platform:papers', (672, 10432), (128, 320), 96, SWALL2, S('swfloor2b', 128, 128),
     "A steel table with papers.")
room('room:control', 'Control room', rect(-1856, 10048, -832, 10816), ZM, H3, theme='theme:machine', ambient=16,
     notes="'Control Room' (aazex124:13): the main terminal on the west wall, a computer; two Doom Knights.")
r = room('room:machine', 'The Lord Xeen Machine', rect(-1280, 10880, 1280, 13440), ZM, ZM + 1024,
         theme='theme:machine', ambient=12,
         notes="Set piece: a hall 2,560 square and 1,024 high round a black and brass engine, an elemental core at "
               "each quarter with a terminal. 'Lord Xeen Machine. Destroy?' (aazex124:0).")
r['platforms'] = [
    {'id': 'platform:machine', 'at': [0, 12160], 'size': [384, 384], 'rise': 640, 'surface': SPANEL,
     'top_surface': GIRDER, 'notes': "The Lord Xeen Machine's engine (the destructible)."},
    {'id': 'platform:machine_base', 'outline': [[-352, 11808], [352, 11808], [352, 12512], [-352, 12512]],
     'rise': 32, 'surface': SWALL2, 'top_surface': GIRDER, 'notes': "The engine's plinth."}]
CORE_AT = {'fire': (0, 11520), 'water': (640, 12160), 'air': (0, 12800), 'earth': (-640, 12160)}
TERM_AT = {'fire': (256, 11520), 'water': (640, 12416), 'air': (-256, 12800), 'earth': (-640, 11904)}
for k, (x, y) in CORE_AT.items():
    r['platforms'].append({'id': f'platform:core_{k}', 'at': [x, y], 'size': [192, 192], 'rise': 448,
                           'surface': S(CORES[k], 128, 256, fit=True), 'top_surface': GIRDER,
                           'notes': f"The {k} core (XD-19's {CORES[k]})."})
    tx, ty = TERM_AT[k]
    r['platforms'].append({'id': f'platform:term_{k}', 'at': [tx, ty], 'size': [192, 64], 'rise': 96,
                           'surface': SCREEN, 'end_surface': SWALL2, 'top_surface': GIRDER,
                           'notes': f"The {k} core's terminal."})
# The machine hall's platforms: the plinth must not cover the engine (the engine stands on it).
r['platforms'][1], r['platforms'][0] = r['platforms'][0], r['platforms'][1]
r['platforms'][1]['base'] = 32

# ================================================================================================ openings
op('open:gate_alcove', 'room:gate_hall', 'room:alcove', (-768, -768), 256, 384, link='link:gate_alcove')
op('open:gate_foot', 'room:gate_hall', 'room:landing0', (-768, -1312), 256, 288, link='link:gate_up')
op('open:gate_pass', 'room:gate_hall', 'room:scorch_pass', (768, -704), 256, 288, link='link:gate_scorched')
op('open:pass_scorched', 'room:scorch_pass', 'room:scorched_hall', (1216, -288), 256, 288, link='link:scorch_hall')
op('open:gate_cellar', 'room:gate_hall', 'room:cellar_stair', (0, -512), 256, 384, link='link:gate_crossword')
op_ramp('open:foot_ramp', 'room:landing0', (-1536, -1312), 'room:ramp01', 7, link='link:foot_ramp')
op_ramp('open:ramp_l1', 'room:landing1', (-1536, 1280), 'room:ramp01', 3, ramp_first=True, link='link:ramp_l1')
op('open:l1_ring', 'room:landing1', 'room:ring_hall', (-736, 1024), *DRAGON_OPEN, link='link:l1_ring')
op('open:l1_dorm', 'room:landing1', 'room:dormitory', (-1280, 1024), 256, 256, link='link:dorm_l1')
op('open:dorm_ring', 'room:dormitory', 'room:ring_hall', (-1024, 224), *DRAGON_OPEN, link='link:ring_dorm')
op('open:ring_bones', 'room:ring_hall', 'room:bone_alcove', (1152, 960), *DRAGON_OPEN, link='link:ring_bones')
op_ramp('open:l1_ramp', 'room:landing1', (-1280, 1536), 'room:ramp12', 7, link='link:l1_ramp')
op_ramp('open:ramp_l2', 'room:landing2', (1280, 1536), 'room:ramp12', 3, ramp_first=True, link='link:ramp_l2')
op('open:l2_nest', 'room:landing2', 'room:nest', (544, 1024), *DRAGON_OPEN, link='link:l2_nest')
op('open:l2_hatch', 'room:landing2', 'room:hatchery', (1152, 1024), *DRAGON_OPEN, link='link:hatch_l2')
op('open:hatch_nest', 'room:hatchery', 'room:nest', (768, 224), *DRAGON_OPEN, link='link:nest_hatch')
op('open:nest_dead', 'room:nest', 'room:last_climber', (-1024, 960), *DRAGON_OPEN, link='link:nest_dead')
op_ramp('open:l2_ramp', 'room:landing2', (1536, 1280), 'room:ramp23', 7, link='link:l2_ramp')
op_ramp('open:ramp_l3', 'room:landing3', (1536, -1280), 'room:ramp23', 3, ramp_first=True, link='link:ramp_l3')
op('open:l3_high', 'room:landing3', 'room:high_hall', (320, -1280), *DRAGON_OPEN, link='link:l3_high')
op('open:l3_gallery', 'room:landing3', 'room:wyrm_gallery', (1280, -1024), 256, 288, link='link:l3_gallery')
op('open:high_crown', 'room:high_hall', 'room:crown', (-384, -192), *DRAGON_OPEN, link='link:high_crown')
op('open:gallery_crown', 'room:wyrm_gallery', 'room:crown', (1024, 768), *DRAGON_OPEN, link='link:gallery_crown')
op('open:crown_tome', 'room:crown', 'room:tome_room', (-1024, 1152), 256, 256, link='link:crown_tome')
op('open:crown_roof', 'room:crown', 'room:roof_stair', (-1024, 24), 256, 256, link='link:crown_roof')
op('open:cellar_crossword', 'room:cellar_stair', 'room:crossword', (0, 1088), 384, 512, link='link:cellar_down')
op('open:crossword_descent', 'room:crossword', 'room:descent', (0, 3200), 256, 384, link='link:crossword_descent')
op('open:descent_welcome', 'room:descent', 'room:welcome', (0, 4352), 256, 384, link='link:descent_welcome')
op('open:welcome_crypt', 'room:welcome', 'room:crypt', (-768, 4800), 256, 384, link='link:welcome_crypt')
op('open:welcome_ball', 'room:welcome', 'room:ballroom', (0, 5184), 384, 448, link='link:welcome_ball')
op('open:ball_west', 'room:ballroom', 'room:game_west', (-1024, 5760), 320, 448, link='link:ball_west')
op('open:ball_east', 'room:ballroom', 'room:game_east', (1024, 5760), 320, 448, link='link:ball_east')
op('open:west_lesser', 'room:game_west', 'room:shrines_lesser', (-1568, 6272), 320, 448, link='link:west_lesser')
op('open:east_great', 'room:game_east', 'room:shrines_great', (1568, 6272), 320, 448, link='link:east_great')
op('open:lesser_throne', 'room:shrines_lesser', 'room:throne', (-1088, 6976), 320, 448, link='link:lesser_throne')
op('open:great_throne', 'room:shrines_great', 'room:throne', (1088, 6976), 320, 448, link='link:great_throne')
op('open:throne_stair', 'room:throne', 'room:bone_stair', (0, 7616), 256, 384, link='link:throne_stair')
op('open:stair_gongs', 'room:bone_stair', 'room:gong_hall', (0, 8768), 256, 384, link='link:stair_gongs')
op('open:gongs_fountain', 'room:gong_hall', 'room:fountain', (1024, 9280), 256, 384, link='link:gongs_fountain')
op('open:gongs_maint', 'room:gong_hall', 'room:maintenance', (0, 9984), 384, 448, link='link:gongs_maint')
op('open:maint_machine', 'room:maintenance', 'room:machine', (0, 10816), 384, 448, link='link:maint_machine')
op('open:maint_control', 'room:maintenance', 'room:control', (-768, 10432), 256, 384, link='link:maint_control')
op('open:control_machine', 'room:control', 'room:machine', (-1056, 10816), 256, 448, link='link:control_machine')

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:tower', 'ambient': 14}, 'rooms': rooms,
             'openings': openings,
             'notes': "FD-04 Dragon Tower and the Dungeon of Death: x east, y north; the tower's four floors 1,280 "
                      "apart (z 0 to 3,840) in a square of 3,072 with the stair winding up in its wall; the Dungeon "
                      "of Death north of it and under it (z -1,024, -1,792, -2,560). Written by "
                      "output/studio_cal/fd04/tools/gen.py."}

# ================================================================================================ the crossword
# Grid cells of 128 in the hall (x -1536..1536, y 1152..3200): column c, row r (row 0 at the north wall).
WORDS = [  # key, clue number, direction, answer, column, row, hook's answers
    ('1a', 1, 'Across', 'SCEPTER', 12, 6, "King's Staff",
     ['Scepter', 'Sceptre', "Xeen's Scepter", "Xeen's Sceptre", 'Xeens Scepter', 'Scepter of Temporal Distortion']),
    ('5a', 5, 'Across', 'VAMPIRE', 14, 12, 'Count Blackfang', ['Vampire', 'Vampires', 'A vampire']),
    ('6a', 6, 'Across', 'KALINDRA', 14, 3, 'Imprisoned Queen', ['Kalindra', "Kalindra's", 'Kalindras', 'Queen Kalindra']),
    ('13a', 13, 'Across', 'CORAK', 6, 2, 'Freed from spaceship', ['Corak']),
    ('21a', 21, 'Across', 'ALAMAR', 2, 13, 'Castle beyond the Forbidden Zone', ['Alamar', 'Castle Alamar']),
    ('24a', 24, 'Across', 'NECROPOLIS', 1, 8, 'City of the undead', ['Necropolis']),
    ('40a', 40, 'Across', 'SANDCASTER', 2, 4, 'City of sorcerers', ['Sandcaster']),
    ('44d', 44, 'Down', 'CASTLEVIEW', 9, 1, "Ellinger's Tower is located here", ['Castleview', 'Castle View']),
    ('45d', 45, 'Down', 'WINTERKILL', 18, 1, 'City of Ghosts', ['Winterkill']),
    ('47d', 47, 'Down', 'SPHINX', 15, 5, 'You need an amulet to gain entry',
     ['Sphinx', 'Southern Sphinx', 'The Southern Sphinx']),
    ('76d', 76, 'Down', 'MIRROR', 4, 6, 'Way of transportation in the Land of Xeen', ['Mirror', 'Mirrors']),
    ('77d', 77, 'Down', 'XEEN', 20, 11, 'He had a pet dragon', ['Xeen', 'Lord Xeen']),
]
CW_X0, CW_YT = -1536, 3200
cells = {}
for key, _, d, ans, c, r_, _, _ in WORDS:
    for i, ch in enumerate(ans):
        cc, rr = (c + i, r_) if d == 'Across' else (c, r_ + i)
        assert 1 <= cc <= 22 and 1 <= rr <= 14, (key, cc, rr)
        if (cc, rr) in cells:
            assert cells[(cc, rr)][0] == ch, ('letters differ', key, cc, rr, cells[(cc, rr)], ch)
            cells[(cc, rr)][1].append(key)
        else:
            cells[(cc, rr)] = [ch, [key]]
# No closed-off floor and no plates touching only at a corner (the build cuts the plates out of the floor).
FREE = {(cc, rr) for cc in range(24) for rr in range(16)} - set(cells)
seen, todo = set(), [(0, 0)]
while todo:
    p0 = todo.pop()
    if p0 in seen or p0 not in FREE:
        continue
    seen.add(p0)
    todo += [(p0[0] + 1, p0[1]), (p0[0] - 1, p0[1]), (p0[0], p0[1] + 1), (p0[0], p0[1] - 1)]
assert seen == FREE, ('floor closed off', sorted(FREE - seen))
for (cc, rr) in cells:
    for dc, dr in ((1, 1), (1, -1)):
        if (cc + dc, rr + dr) in cells:
            assert (cc + dc, rr) in cells or (cc, rr + dr) in cells, ('corner touch', (cc, rr), (cc + dc, rr + dr))
# Plates: maximal runs along each word of cells with the same set of words (crossings are plates of their own).
plates = []
for key, _, d, ans, c, r_, _, _ in WORDS:
    run = []
    for i in range(len(ans)):
        cc, rr = (c + i, r_) if d == 'Across' else (c, r_ + i)
        ws = tuple(sorted(cells[(cc, rr)][1]))
        if len(ws) > 1 and d == 'Down':
            if run:
                plates.append((key, d, run, (key,)))
                run = []
            continue  # the crossing cell is the across word's plate of its own
        if len(ws) > 1:
            if run:
                plates.append((key, d, run, (key,)))
                run = []
            plates.append((key, d, [(cc, rr)], ws))
            continue
        run.append((cc, rr))
    if run:
        plates.append((key, d, run, (key,)))
PLATE_IDS = []
CELL_PLATES = {k[0]: [] for k in WORDS}
objects_plates = []
for n, (key, d, run, ws) in enumerate(plates, 1):
    xs = [CW_X0 + 128 * cc for cc, _ in run]
    ys = [CW_YT - 128 * (rr + 1) for _, rr in run]
    x0, x1 = min(xs), max(xs) + 128
    y0, y1 = min(ys), max(ys) + 128
    pid = f'plate:cw_{key}_{n}' if len(ws) == 1 else f'plate:cw_x_{"_".join(ws)}'
    objects_plates.append({'id': pid, 'room': 'room:crossword',
                           'outline': [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], 'surface': CELL,
                           'notes': (f"Cells of {key}" if len(ws) == 1 else f"The cell where {' and '.join(ws)} cross")
                                    + " (xfgrid; xfword when solved)."})
    for w in ws:
        CELL_PLATES[w].append(pid)

# The clue plaques: across words on the west or east wall at their rows, down words on the north or south wall at
# their columns.
CLUE_AT = {}
for key, num, d, ans, c, r_, clue, _ in WORDS:
    if d == 'Across':
        y = CW_YT - 128 * r_ - 64
        CLUE_AT[key] = (-1536, y) if c < 12 else (1536, y)
    else:
        x = CW_X0 + 128 * c + 64
        CLUE_AT[key] = (x, 3200) if r_ <= 5 else (x, 1152)
for key, num, d, ans, c, r_, clue, _ in WORDS:
    wall_panel('room:crossword', CLUE_AT[key], f'panel:clue_{key}', 112, 144, 144, PLAQUE,
               f"The clue plaque {num} {d} (xdplaque, FD-03's bronze plaque reused).")

# ================================================================================================ gong hall panels
GONGS = {1: (-1024, 8992), 2: (-1024, 9568), 3: (1024, 9568), 4: (1024, 8992)}
for i, at in GONGS.items():
    wall_panel('room:gong_hall', at, f'panel:gong_{i}', 256, 192, 256, GONG, f"Gong {i} (XD-03's xngong).")
wall_panel('room:control', (-1856, 10432), 'panel:terminal', 256, 128, 128, SCREEN,
           "The main terminal's screen (trekscrn).")
wall_panel('room:control', (-1344, 10816), 'panel:computer', 192, 0, 384, SPANEL, "A computer cabinet (swpnl).")
wall_panel('room:wyrm_gallery', (1536, 512), 'panel:wyrm_door', 256, 0, 320, S('vlcdora', 256, 256, fit=True),
           "The Wyrm's Hall's great door (house 4853, Ashkaroth).")

# ================================================================================================ objects
ARRIVAL = [0, -1280]
X9_HEAD = [-1312, 608]
objects = {'format': 0}
objects['start'] = {'room': 'room:gate_hall', 'at': ARRIVAL, 'facing': 'n',
                    'notes': "entrance:x7_gate: 256 inside the tower's gate, facing north into the tower."}
objects['arrivals'] = [
    {'entrance': 'entrance:x7_gate', 'room': 'room:gate_hall', 'at': ARRIVAL, 'facing': 'n',
     'notes': "X7's Dragon Tower gate (door:fd04, A5): 256 inside the gate, facing north (512). Quiet: Alister is "
              "peaceful, the scorched hall's Acid pair round a turn and more than 1,024 from its low opening."},
    {'entrance': 'entrance:x9_clouds', 'room': 'room:roof_stair', 'at': X9_HEAD, 'floor_height': Z[3] + 384,
     'facing': 's', 'notes': "X9's way down from the Dragon Clouds (A5): on the roof stair's head under the hatch "
                            "(z 4,224), facing down the stair (south). Quiet: the crown's door is shut."},
]
PAIR = {'pictures': [[WING_L, WING_R]], 'back_pictures': [[WING_L, WING_R]]}
objects['doors'] = [
    {'id': 'door:sandro', 'opening': 'open:gate_cellar', 'kind': 'hinged', 'thickness': 24,
     'surface': S('gnecdr6', 128, 256, fit=True), 'back_surface': S('gnecdr6', 128, 256, fit=True),
     'edge_surface': TRIM, 'notes': "Sandro's black iron door (q-f2.door, item 12354): open for good with 118130."},
    {'id': 'door:dorm', 'opening': 'open:l1_dorm', 'kind': 'hinged', 'thickness': 24, 'surface': TOWER_DOOR,
     'back_surface': TOWER_DOOR, 'edge_surface': TRIM, 'notes': "The dormitory's door from the landing."},
    {'id': 'door:tome', 'opening': 'open:crown_tome', 'kind': 'hinged', 'thickness': 24, 'surface': TOWER_DOOR,
     'back_surface': TOWER_DOOR, 'edge_surface': TRIM, 'notes': "The tome room's door off the crown."},
    {'id': 'door:roof', 'opening': 'open:crown_roof', 'kind': 'hinged', 'thickness': 24, 'surface': TOWER_DOOR,
     'back_surface': TOWER_DOOR, 'edge_surface': TRIM, 'notes': "The crown's low door to the roof stair."},
    {'id': 'door:descent', 'opening': 'open:crossword_descent', 'kind': 'slide_up', 'thickness': 24,
     'speed': 128, 'surface': S('gnecdr3', 256, 256, fit=True), 'back_surface': S('gnecdr3', 256, 256, fit=True),
     'notes': "The descent's gate: up when the twelve words are lit (q-f2.crossword, 118143)."},
    {'id': 'door:crypt', 'opening': 'open:welcome_crypt', 'kind': 'hinged', 'thickness': 24, 'surface': NDOOR,
     'back_surface': NDOOR, 'edge_surface': TRIM, 'notes': "'Do Not Disturb' (aazex122:4)."},
    dict({'id': 'door:ballroom', 'opening': 'open:welcome_ball', 'kind': 'hinged', 'leaves': 2, 'thickness': 32,
          'speed': 96, 'edge_surface': TRIM,
          'notes': "The welcome hall's double doors (gnecdr1l/gnecdr1r) into the ballroom."}, **PAIR),
    {'id': 'door:shutter', 'opening': 'open:gongs_maint', 'kind': 'slide_up', 'thickness': 24, 'speed': 96,
     'surface': SDOOR, 'back_surface': SDOOR,
     'notes': "The iron shutter: up when the lever is pulled after the four gongs (118144)."},
    {'id': 'door:control', 'opening': 'open:maint_control', 'kind': 'slide_up', 'thickness': 24, 'surface': SDOOR,
     'back_surface': SDOOR, 'notes': "The control room's door."},
]
GONG_CHEST_AT = [600, 9850]
objects['chests'] = [
    {'id': 'chest:dorm', 'room': 'room:dormitory', 'at': [-1250, -440], 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The keepers' chest (aazex118:5, T6)."},
    {'id': 'chest:climber', 'room': 'room:last_climber', 'at': [-620, 1440], 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The last climber's chest (aazex119:7, T6)."},
    {'id': 'chest:tome', 'room': 'room:tome_room', 'at': [-1280, 824], 'facing': 'e', 'treasure_level': 6,
     'random_items': 3, 'gold': 4000, 'notes': "The tome room's chest (aazex120:5, T6), its back to the south wall "
                                               "between the bed and the corner, its front to the room (A7 s28: was "
                                               "96 from the door's swing, merge point 42's chest.entrance)."},
    {'id': 'chest:crypt', 'room': 'room:crypt', 'at': [-1300, 4500], 'treasure_level': 6,
     'random_items': 4, 'gold': 5000, 'notes': "The crypt's chest among the coffins (T6)."},
    {'id': 'chest:gongs', 'room': 'room:gong_hall', 'at': GONG_CHEST_AT, 'treasure_level': 6,
     'random_items': 4, 'gold': 6000,
     'notes': "The gong hall's chest: opened before the shutter is up, it silences the gongs (aazex123:3)."},
]
AC, FI, FR, PH, EN = 11641, 11642, 11643, 11652, 11653
LL, PL, SL, DK, AB = 11282, 11284, 11285, 11152, 11612
ALISTER = 11923
NAMES = {AC: 'Acid Dragon', FI: 'Fire Dragon', FR: 'Frost Dragon', PH: 'Phase Dragon', EN: 'Energy Dragon',
         LL: 'Lich Lord', PL: 'Power Lich', SL: 'Skeletal Lich', DK: 'Doom Knight', AB: 'Autobot', ALISTER: 'Alister'}
LEVELS = {AC: 66, FI: 75, FR: 85, PH: 90, EN: 100, LL: 65, PL: 75, SL: 85, DK: 75, AB: 75, ALISTER: 40}
# Placed monsters: room, group, [(row, at, facing)].
PLACED = [
    ('scorched_hall', 11, [(AC, (760, 1150), 270), (AC, (1260, 1150), 270)]),
    ('ring_hall', 12, [(AC, (-560, -1100), 90), (AC, (-560, 500), 0)]),
    ('ring_hall', 13, [(AC, (1100, 500), 180), (AC, (1100, -1100), 90)]),
    ('ring_hall', 14, [(FI, (288, -1150), 90), (FI, (288, 560), 270)]),
    ('nest', 21, [(FI, (-1150, -1150), 45), (FI, (-1150, 560), 315)]),
    ('nest', 22, [(FI, (330, 560), 225), (FI, (330, -1150), 135)]),
    ('nest', 23, [(FR, (-416, -1150), 90), (FR, (-1150, -288), 0)]),
    ('hatchery', 24, [(FI, (1000, -480), 90), (FR, (1300, -100), 90)]),
    ('hatchery', 25, [(FI, (1000, 280), 270), (FR, (1300, 660), 270)]),
    ('high_hall', 31, [(FR, (-1150, -1150), 45), (FR, (-1150, -560), 315)]),
    ('high_hall', 32, [(PH, (-500, -1150), 90), (PH, (-500, -560), 90), (PH, (-20, -860), 180)]),
    ('crown', 33, [(EN, (0, 900), 270), (PH, (-600, 1100), 270), (PH, (600, 1100), 270)]),
    ('crossword', 41, [(LL, (-900, 2600), 0), (LL, (900, 1700), 180)]),
    ('welcome', 42, [(LL, (-400, 4950), 270), (LL, (400, 4950), 270)]),
    ('ballroom', 43, [(SL, (-600, 5600), 90), (SL, (-300, 5600), 90)]),
    ('ballroom', 44, [(SL, (300, 5950), 270), (SL, (600, 5950), 270)]),
    ('game_west', 45, [(LL, (-1750, 5500), 0), (LL, (-1400, 5500), 0), (PL, (-1568, 6000), 270)]),
    ('game_east', 46, [(LL, (1750, 5500), 180), (LL, (1400, 5500), 180), (PL, (1568, 6000), 270)]),
    ('shrines_lesser', 47, [(LL, (-1400, 6700), 90), (LL, (-1750, 6950), 90), (SL, (-1568, 7300), 270)]),
    ('shrines_great', 48, [(PL, (1400, 6700), 90), (PL, (1750, 6950), 90), (SL, (1568, 7300), 270)]),
    ('throne', 49, [(DK, (-400, 7050), 270), (DK, (400, 7050), 270)]),
    ('gong_hall', 51, [(AB, (-600, 9500), 270), (AB, (600, 9400), 270)]),
    ('maintenance', 52, [(AB, (-400, 10432), 270), (AB, (300, 10432), 270)]),
    ('control', 53, [(DK, (-1500, 10300), 0), (DK, (-1150, 10600), 0)]),
    ('machine', 54, [(AB, (-800, 11300), 90), (AB, (800, 11300), 90)]),
    ('machine', 55, [(PL, (-800, 13000), 270), (PL, (800, 13000), 270)]),
    ('machine', 56, [(SL, (-950, 12160), 0), (SL, (950, 12160), 180)]),
]
for rid, _, ms in PLACED:
    for _, at, _ in ms:
        assert inside(poly(f'room:{rid}'), at), (rid, at)
COUNTS = {}
for _, _, ms in PLACED:
    for mon, _, _ in ms:
        COUNTS[mon] = COUNTS.get(mon, 0) + 1
assert COUNTS == {AC: 6, FI: 8, FR: 6, PH: 5, EN: 1, LL: 10, PL: 6, SL: 8, DK: 4, AB: 6}, COUNTS
KILL_XP = sum(LEVELS[m] * (LEVELS[m] + 10) * n for m, n in COUNTS.items()) / 4
objects['monsters'] = [
    {'id': 'monster:alister', 'room': 'room:alcove', 'monster': ALISTER, 'at': [-1040, -768], 'facing': 0,
     'hostile': False, 'group': 60, 'immobile': True, 'npc': 5705,
     'notes': "Alister the Druid (A2's peaceful placed-only row 11923, A4's npc 5705): talks from his body (Q-F1's "
              "topics); unkillable (evt:alister_load); hidden when his paying talk closes and on every load with "
              "118147 (D-57 Q27)."}]
if S_LIZARD:   # the lizard he becomes stands where he stood, hidden till he is gone
    objects['monsters'][0]['inside'] = 'deco:lizard'
for rid, group, ms in PLACED:
    for n, (mon, at, f) in enumerate(ms, 1):
        mid = 'monster:energy_dragon' if mon == EN else f'monster:{rid}_{group}_{n}'
        objects['monsters'].append({'id': mid, 'room': f'room:{rid}', 'monster': mon, 'at': list(at), 'facing': f,
                                    'hostile': True, 'group': group})
objects['plates'] = objects_plates


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': list(at), 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [235, 150, 80]
EMBER = [240, 110, 60]
COLD = [170, 175, 200]
GOLD = [255, 200, 110]
TUBE = [150, 200, 220]
CLOUD = [190, 200, 220]
# Wall torches (tower and Sandro's halls): a torch01 12 in from the wall and its light.
TORCHES = [
    ('room:gate_hall', (-768, -1100)), ('room:gate_hall', (768, -1100)), ('room:gate_hall', (-400, -512)),
    ('room:gate_hall', (400, -512)), ('room:landing0', (-1184, -1536)), ('room:scorched_hall', (320, 300)),
    ('room:scorched_hall', (1536, 1000)), ('room:landing1', (-1024, 1536)), ('room:ring_hall', (-960, -700)),
    ('room:ring_hall', (1536, -300)), ('room:ring_hall', (600, -1536)), ('room:ring_hall', (300, 960)),
    ('room:dormitory', (-1024, -300)), ('room:bone_alcove', (1536, 1280)), ('room:landing2', (900, 1536)),
    ('room:nest', (-1536, -800)), ('room:nest', (704, -800)), ('room:nest', (-600, -1536)), ('room:nest', (-300, 960)),
    ('room:hatchery', (1536, -500)), ('room:last_climber', (-900, 1536)), ('room:landing3', (900, -1536)),
    ('room:high_hall', (-1536, -860)), ('room:high_hall', (-600, -192)), ('room:wyrm_gallery', (1536, -500)),
    ('room:wyrm_gallery', (1536, 1200)), ('room:crown', (-1024, 600)), ('room:crown', (960, 300)),
    ('room:crown', (0, 1536)), ('room:tome_room', (-1536, 1250)), ('room:roof_stair', (-1088, 400)),
    ('room:crossword', (-800, 1152)), ('room:crossword', (800, 3200)), ('room:welcome', (-400, 4416)),
    ('room:welcome', (400, 4416)), ('room:crypt', (-832, 4600)), ('room:ballroom', (-1024, 5450)),
    ('room:ballroom', (1024, 6100)), ('room:game_west', (-1600, 5248)), ('room:game_east', (1600, 5248)),
    ('room:shrines_lesser', (-1088, 6600)), ('room:shrines_great', (1088, 7350)), ('room:throne', (-700, 7616)),
    ('room:throne', (700, 7616)), ('room:gong_hall', (-500, 8832)), ('room:gong_hall', (500, 8832)),
    ('room:fountain', (1440, 9600)),
]
objects['decorations'] = []
objects['lights'] = []
for i, (rid, at) in enumerate(TORCHES, 1):
    p = inward(rid, at, 12)
    objects['decorations'].append({'id': f'deco:torch_{i:02d}', 'room': rid, 'decoration': 'torch01', 'at': p,
                                   'height': 224})
    objects['lights'].append(light(f'light:torch_{i:02d}', rid, p, 256, 900, FIRE))
# The machine floor: cold strip lights (no fixture) high on the walls.
for i, (rid, at, h) in enumerate([('room:maintenance', (0, 10432), 560), ('room:control', (-1344, 10432), 560),
                                  ('room:machine', (-900, 11300), 900), ('room:machine', (900, 11300), 900),
                                  ('room:machine', (-900, 13000), 900), ('room:machine', (900, 13000), 900)], 1):
    objects['lights'].append(light(f'light:tube_{i}', rid, at, h, 1400, TUBE))
for k, (x, y) in CORE_AT.items():
    objects['lights'].append(light(f'light:core_{k}', 'room:machine', (x, y), 560, 700,
                                   {'fire': [255, 120, 60], 'water': [80, 150, 255], 'air': [220, 230, 255],
                                    'earth': [150, 200, 90]}[k], notes=f"The {k} core's glow (out when the machine "
                                                                       "breaks)."))
for i, (x, y) in GONGS.items():
    objects['lights'].append(light(f'light:gong_{i}', 'room:gong_hall', inward('room:gong_hall', (x, y), 48), 120,
                                   520, GOLD, on=False,
                                   notes=f"The lamp-glow under gong {i}: lit when it is rung, out when the chest "
                                         "silences the gongs (D-43, D-57)."))
for key, *_ in WORDS:
    cs = [cc for cc, rr in cells if key in cells[(cc, rr)][1]]
    rs = [rr for cc, rr in cells if key in cells[(cc, rr)][1]]
    mx = CW_X0 + 128 * (sum(cs) / len(cs)) + 64
    my = CW_YT - 128 * (sum(rs) / len(rs)) - 64
    objects['lights'].append(light(f'light:word_{key}', 'room:crossword', (round(mx), round(my)), 48, 560, GOLD,
                                   on=False, notes=f"The glow over {key} once it is solved."))
objects['lights'] += [
    light('light:hatch', 'room:roof_stair', (-1312, 592), 600, 1200, CLOUD, notes="Cloud light down the hatch."),
    light('light:bowl', 'room:nest', (-416, -288), 160, 900, EMBER, notes="The warm glow of the eggs' rock."),
    light('light:crown', 'room:crown', (0, 700), 1700, 2400, [200, 170, 230], notes="A violet glow under the crown."),
]
objects['decorations'] += [
    {'id': 'deco:bones_fraud', 'room': 'room:bone_alcove', 'decoration': '7dec18', 'at': [1000, 1440],
     'notes': "The first dead adventurer (q-f1.note_fraud)."},
    {'id': 'deco:bones_forever', 'room': 'room:bone_alcove', 'decoration': 'dec19', 'at': [1400, 1120],
     'notes': "The second (q-f1.note_forever)."},
    {'id': 'deco:bones_balls', 'room': 'room:hatchery', 'decoration': 'dec29', 'at': [1450, 880],
     'notes': "A climber who got as far as the hatchery (q-f1.note_balls)."},
    {'id': 'deco:bones_eye', 'room': 'room:last_climber', 'decoration': 'dec05', 'at': [-1300, 1150],
     'notes': "The last climber (q-f1.note_eye)."},
    {'id': 'deco:scorched_bones', 'room': 'room:scorched_hall', 'decoration': '7dec18', 'at': [1450, -100]},
    {'id': 'deco:scorched_skull', 'room': 'room:scorched_hall', 'decoration': '7dec20', 'at': [390, 100],
     'notes': "On the floor by the west wall, south of the stall (F3, 2026-11-21: at (400, 200) it stood on the "
              "stall wall's end, half over its edge)."},
    {'id': 'deco:fountain', 'room': 'room:fountain', 'decoration': 'sta1a', 'at': [1600, 9280],
     'notes': "The fountain (aazex123:4-5)."},
    {'id': 'deco:candles_1', 'room': 'room:throne', 'decoration': 'dec02', 'at': [-700, 6560]},
    {'id': 'deco:candles_2', 'room': 'room:throne', 'decoration': 'dec02', 'at': [700, 6560]},
    {'id': 'deco:skulls_crypt', 'room': 'room:crypt', 'decoration': 'sklplrev', 'at': [-920, 5080]},
]
for i, x in enumerate((-512, 0, 512), 1):
    objects['decorations'].append({'id': f'deco:chandelier_{i}', 'room': 'room:ballroom', 'decoration': 'ChndLir0',
                                   'at': [x, 5760], 'hangs': True, 'notes': "A dead chandelier."})
if S_LIZARD:
    objects['decorations'].append({'id': 'deco:lizard', 'room': 'room:alcove', 'decoration': S_LIZARD,
                                   'at': [-1040, -768], 'facing': 0, 'hidden': True,
                                   'notes': "The small lizard Alister became (shown with 118147, D-57 Q27)."})
if S_EGG:
    for i, (x, y, f) in enumerate(((-456, -300, 20), (-380, -320, 140), (-416, -240, 260)), 1):
        objects['decorations'].append({'id': f'deco:egg_{i}', 'room': 'room:nest', 'decoration': S_EGG, 'at': [x, y],
                                       'facing': f, 'floor_height': Z[2] - 48, 'notes': "A dragon egg in the nest."})
objects['switches'] = [
    {'id': 'switch:lever', 'room': 'room:gong_hall', 'kind': 'lever', 'reach': 48, 'at': [-500, 9984],
     'notes': "The lever by the iron shutter (aazex123:1)."}]
objects['destructibles'] = [
    {'id': f'destructible:shrine_{k}', 'of': f'platform:shrine_{k}', 'hp': 200, 'material': 'stone',
     'on_destroyed': f'evt:shrine_{k}_down', 'notes': f"The Shrine of {k.title()} Evil: the question breaks it, "
                                                      "blows and spells too."} for k in SHRINES] + [
    {'id': 'destructible:machine', 'of': 'platform:machine', 'hp': 600, 'material': 'metal',
     'on_destroyed': 'evt:machine_down', 'notes': "The Lord Xeen Machine's engine: the question breaks it, blows and "
                                                 "spells too (D-47 Q8)."}]
objects['exits'] = [
    {'id': 'exit:gate', 'room': 'room:gate_hall', 'wall': 's', 'size': [384, 384], 'surface': S('7solid01', 256, 256, fit=True),
     'to': 'exit:x7_gate', 'notes': "The tower gate's inner face: out onto X7's crag (aazex117:4)."},
    {'id': 'exit:hatch', 'room': 'room:roof_stair', 'at': [-1312, 704], 'floor_height': Z[3] + 384,
     'size': [192, 320], 'surface': S('7solid01', 256, 256, fit=True, uneven=True), 'to': 'exit:x9_roof',
     'notes': "The hatch's ladder under the open sky, up onto the Dragon Clouds (X9). The black exit picture "
              "(F12) is one flat black, fitted to the hatch's 192 by 320 (uneven: no picture to squash)."},
]
objects['sounds'] = [
    {'id': 'sound:tower_1', 'room': 'room:ring_hall', 'at': [288, 400], 'sound': 'xeen_amb_tower', 'radius': 3000,
     'inner_radius': 1000, 'volume': 0.3, 'pan': False, 'notes': "The tower's bed (AU)."},
    {'id': 'sound:tower_2', 'room': 'room:nest', 'at': [-416, -288], 'sound': 'xeen_amb_tower', 'radius': 3000,
     'inner_radius': 1000, 'volume': 0.3, 'pan': False},
    {'id': 'sound:hum_cw', 'room': 'room:crossword', 'at': [0, 2176], 'sound': 'humming', 'radius': 2400,
     'inner_radius': 800, 'volume': 0.3, 'pan': False, 'notes': "The dungeon bed (D-48)."},
    {'id': 'sound:hum_halls', 'room': 'room:ballroom', 'at': [0, 5760], 'sound': 'humming', 'radius': 3000,
     'inner_radius': 1000, 'volume': 0.3, 'pan': False},
    {'id': 'sound:machine', 'room': 'room:machine', 'at': [0, 12160], 'sound': 'xeen_machine_stamp_loop',
     'radius': 3600, 'inner_radius': 900, 'volume': 0.45, 'pan': False,
     'notes': "The Lord Xeen Machine running; off when it breaks (AmbientSound<n> 2)."},
]

# ================================================================================================ wiring
QB = {'door_open': 118130, 'crossword_done': 118143, 'shutter_up': 118144, 'machine_broken': 118145,
      'egg_taken': 118146, 'alister_gone': 118147, 'ultimate_broken': 118148, 'code_entered': 118149}
WORD_BIT = {'1a': 118131, '5a': 118132, '6a': 118133, '13a': 118134, '21a': 118135, '24a': 118136, '40a': 118137,
            '44d': 118138, '45d': 118139, '47d': 118140, '76d': 118141, '77d': 118142}
for k, v in WORD_BIT.items():
    QB[f'word_{k}'] = v


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def snd(name, x, y, z):
    return {'lua': f'evt.PlaySoundName("{name}", {x}, {y}, {z})'}


def variants(names):
    """Every accepted way of typing the names (the game already ignores case and outer spaces): with and without the
    apostrophe (straight or curly), Scepter or Sceptre, with or without 'The ', with or without a trailing full stop.
    Only the listed names in those spellings: a wrong word stays wrong (s19)."""
    out = []
    for n in names:
        forms = [n]
        for f in list(forms):
            forms += [f.replace("'", ''), f.replace("'", '’')]
        for f in list(forms):
            forms += [f.replace('Scepter', 'Sceptre'), f.replace('Sceptre', 'Scepter')]
        for f in list(forms):
            forms.append(f if f.startswith(('The ', 'A ')) else 'The ' + f)
        for f in list(forms):
            forms.append(f + '.')
        for v in forms:
            if v not in out:
                out.append(v)
    return out


VARS = ['alister_hidden', 'gong1', 'gong2', 'gong3', 'gong4', 'reset_pending']
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True, 'seconds': 6,
     'text': "The Dragon Tower: warm black stone, and somewhere far above, something very large breathing.",
     'notes': "The arrival line (a new map line, no source text): the tower and its dragons."},
    {'id': 'evt:way_out', 'preset': 'exit', 'source': 'exit:gate', 'title': 'Exit Dragon Tower',
     'notes': "Out to X7 (installed) at its named arrival entrance:fd04_door (-17920, 16384, 2592) facing south "
              "through the game's leave window (D-24; meaning aazex117:4 'Exit Dragon Tower?')."},
    {'id': 'evt:hatch', 'preset': 'script', 'source': 'exit:hatch', 'title': 'Climb onto the Dragon Clouds',
     'lua': 'evt.MoveToMap(20352, 17280, 2048, 512, 0, 0, 0, 1, "xeen_x9.blv")',
     'notes': "F16 (2026-11-22): the game's standard entrance window (OK/Close) in place of the map's old Yes/No. Was: Up onto X9 (A5's BLV, installed with entrance:fd04_roof, 03:49): the map's own Yes/No 'Climb up "
              "through the hatch?' (D-66: a roof or hatch exit into a BLV asks, as DD-15 and DD-08 do; no hook, so no "
              "text before it, D-65), then on Yes at once to entrance:fd04_roof [20352, 17280, 2048] facing north "
              "(D-57 Q36; the coordinates are X9's named arrival, written out because the move waits on the answer)."},
    {'id': 'evt:door_dorm', 'preset': 'door', 'source': 'door:dorm', 'title': 'Door'},
    {'id': 'evt:door_tome', 'preset': 'door', 'source': 'door:tome', 'title': 'Door'},
    {'id': 'evt:door_roof', 'preset': 'door', 'source': 'door:roof', 'title': 'Door'},
    {'id': 'evt:door_crypt', 'preset': 'door', 'source': 'door:crypt', 'title': 'Do Not Disturb'},
    {'id': 'evt:door_ballroom', 'preset': 'door', 'source': 'door:ballroom', 'title': 'Doors'},
    {'id': 'evt:door_control', 'preset': 'door', 'source': 'door:control', 'title': 'Door'},
    # Sandro's door (D-57 Q24): from above A3's q-f2.door (the key kept); from below it always opens.
    {'id': 'evt:sandro', 'preset': 'script', 'source': 'door:sandro', 'side': 'room:gate_hall',
     'title': 'Black iron door', 'condition': {'lua': 'XeenQuests.can("q-f2.door")'}, 'opens': ['door:sandro'],
     'effects': [hook('q-f2.door')], 'else_effects': [hook('q-f2.door')],
     'notes': "A3's q-f2.door: with item 12354 the door opens for good (118130, the key kept); without it the "
              "refusal names the key; after it, the hook's else line."},
    {'id': 'evt:sandro_below', 'preset': 'door', 'source': 'door:sandro', 'side': 'room:cellar_stair',
     'title': 'Black iron door', 'notes': "From below the door always opens (D-57 Q24)."},
    {'id': 'evt:sandro_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'door_open'},
     'opens': ['door:sandro'], 'notes': "Open for good with 118130."},
    # Alister (D-57 Q27): peaceful, unkillable; hidden when his paying talk closes and on every load.
    {'id': 'evt:alister_load', 'preset': 'script', 'trigger': 'load',
     'lua': 'evt.SetMm9ActorCanReceiveDamage(ActorIndex("monster:alister"), false)',
     'notes': "Alister cannot be killed: every hit on him is zeroed, on every load (D-52's word)."},
    {'id': 'evt:alister_gone', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'qbit': 'alister_gone'}, {'not': {'map_var': 'alister_hidden'}}]},
     'effects': [{'hide_actors': 60}, {'set': {'var': {'map_var': 'alister_hidden'}, 'value': 1}}]
                + ([{'show': 'deco:lizard'}] if S_LIZARD else []),
     'notes': "The paying talk sets 118147 (A3's q-f1 topic 'Dragon egg'); the second after it closes he is hidden"
              + (" and the lizard shown" if S_LIZARD else " (the lizard: blocked on S's decoration)")
              + " in the same visit (D-57 Q27)."},
    {'id': 'evt:alister_gone_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'alister_gone'},
     'effects': [{'hide_actors': 60}, {'set': {'var': {'map_var': 'alister_hidden'}, 'value': 1}}]
                + ([{'show': 'deco:lizard'}] if S_LIZARD else []),
     'notes': "Gone on every load with 118147."},
    # The tower's finds (A3's q-f1 hooks).
    {'id': 'evt:bones_fraud', 'preset': 'script', 'source': 'deco:bones_fraud', 'title': 'Bones',
     'effects': [hook('q-f1.note_fraud')], 'notes': "aazex118:2-3 (A3's q-f1.note_fraud)."},
    {'id': 'evt:bones_forever', 'preset': 'script', 'source': 'deco:bones_forever', 'title': 'Bones',
     'effects': [hook('q-f1.note_forever')], 'notes': "aazex118:4 (A3's q-f1.note_forever: the Eye's answer hinted)."},
    {'id': 'evt:bones_balls', 'preset': 'script', 'source': 'deco:bones_balls', 'title': 'Bones',
     'effects': [hook('q-f1.note_balls')], 'notes': "aazex119:5 (A3's q-f1.note_balls)."},
    {'id': 'evt:bones_eye', 'preset': 'script', 'source': 'deco:bones_eye', 'title': 'Bones',
     'effects': [hook('q-f1.note_eye')], 'notes': "aazex119:6 (A3's q-f1.note_eye)."},
    {'id': 'evt:potion', 'preset': 'script', 'source': 'platform:potion_shelf', 'title': 'Potion',
     'effects': [hook('q-f1.endurance')], 'notes': "aazex119:2-3: A3's q-f1.endurance decides for the clicking member "
                                                   "(+2 Endurance once per character)."},
    {'id': 'evt:tome', 'preset': 'script', 'source': 'platform:tome_stand', 'title': 'Tome of Great Experience',
     'effects': [hook('q-f1.tome')], 'notes': "aazex120:2-4: A3's q-f1.tome (4,000 once per character)."},
    {'id': 'evt:egg', 'preset': 'script', 'source': 'platform:eggs', 'title': 'Dragon eggs',
     'effects': [hook('q-f1.egg')] + ([{'hide': 'deco:egg_3'}] if S_EGG else []),
     'notes': "A3's q-f1.egg: the Dragon Egg once (118146)."},
    {'id': 'evt:wyrm_hall', 'preset': 'script', 'source': 'panel:wyrm_door', 'title': "The Wyrm's Hall",
     'effects': [{'lua': 'evt.EnterHouse(4853)'}],
     'notes': "A4's house 4853 (The Wyrm's Hall, Ashkaroth 5703, flavour only, D-5.2): the great door opens the house."},
]
for i, (x, y) in enumerate(((-1460, -288), (-1460, 32), (-1460, 352), (-1460, 672)), 1):
    events.append({'id': f'evt:bed_{i}', 'preset': 'text', 'source': f'platform:bed_{i}', 'title': 'Bed',
                   'text': 'Nothing here.', 'notes': "aazex118:0-1."})
events.append({'id': 'evt:tome_bed', 'preset': 'text', 'source': 'platform:tome_bed', 'title': 'Bed',
               'text': 'Nothing here.', 'notes': "aazex120:1, :0."})
if S_EGG:
    events.append({'id': 'evt:egg_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'egg_taken'},
                   'effects': [{'hide': 'deco:egg_3'}], 'notes': "Two eggs left on every load with 118146."})
# The crossword (D-57 Q25): each plaque asks its clue; the right answer lights its cells and their glow.
for key, num, d, ans, c, r_, clue, answers in WORDS:
    bit = f'word_{key}'
    lit = [{'set_texture': {'of': p, 'to': 'xfword'}} for p in CELL_PLATES[key]] + [{'lights_on': f'light:word_{key}'}]
    events.append({'id': f'evt:clue_{key}', 'preset': 'script', 'source': f'panel:clue_{key}',
                   'title': f'{num} {d}', 'condition': {'not': {'qbit': bit}},
                   'question': {'ask': f"{num} {d}: {clue}. Answer?", 'answers': variants(answers),
                                'wrong_effects': [hook('q-f2.clue_wrong')]},
                   'effects': [hook(f'q-f2.clue_{key}')] + lit + [snd('xeen_mirror_touch', 0, 2176, -900)],
                   'else_effects': [{'text': f"{num} {d}: {clue}. {ans.title()}."}],
                   'notes': f"aazex121:11-188's {num} {d} (A3's q-f2.clue_{key}; 'Correct!' / 'Wrong!', aazex121:7-8): "
                            f"the word ({ans}) lights across the floor ({QB[bit]})."})
    events.append({'id': f'evt:clue_{key}_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': bit},
                   'effects': lit, 'notes': f"{ans} lit on every load with {QB[bit]}."})
events += [
    {'id': 'evt:descent', 'preset': 'script', 'source': 'door:descent', 'side': 'room:crossword', 'title': 'Gate',
     'condition': {'lua': 'XeenQuests.can("q-f2.crossword")'}, 'opens': ['door:descent'],
     'effects': [hook('q-f2.crossword')], 'else_effects': [hook('q-f2.crossword')],
     'notes': "A3's q-f2.crossword: with the twelve words lit it pays once (118143) and the gate rises; before, "
              "'Sorry, the crossword puzzle is not done yet.  You may not descend!' (aazex121:1)."},
    {'id': 'evt:descent_below', 'preset': 'door', 'source': 'door:descent', 'side': 'room:descent', 'title': 'Gate',
     'notes': "From below the gate always opens."},
    {'id': 'evt:descent_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'crossword_done'},
     'opens': ['door:descent'], 'notes': "Open for good with 118143."},
    # Signs (aazex122:0-3, aazex124:12-13) as the source shows them: on the way in.
    {'id': 'evt:sign_welcome', 'preset': 'text', 'trigger': 'step', 'source': 'room:welcome', 'text': 'Welcome',
     'notes': "aazex122:0."},
    {'id': 'evt:sign_ballroom', 'preset': 'text', 'trigger': 'step', 'source': 'room:ballroom', 'text': 'Ballroom',
     'notes': "aazex122:1."},
    {'id': 'evt:sign_game_west', 'preset': 'text', 'trigger': 'step', 'source': 'room:game_west', 'text': 'Game Room',
     'notes': "aazex122:3."},
    {'id': 'evt:sign_game_east', 'preset': 'text', 'trigger': 'step', 'source': 'room:game_east', 'text': 'Game Room',
     'notes': "aazex122:2."},
    {'id': 'evt:sign_maintenance', 'preset': 'text', 'trigger': 'step', 'source': 'room:maintenance',
     'text': 'Maintenance', 'notes': "aazex124:12."},
    {'id': 'evt:sign_control', 'preset': 'text', 'trigger': 'step', 'source': 'room:control', 'text': 'Control Room',
     'notes': "aazex124:13."},
]
for i in range(1, 5):
    events.append({'id': f'evt:coffin_{i}', 'preset': 'script', 'source': f'platform:coffin_{i}', 'title': 'Coffin',
                   'effects': [hook('q-f2.coffin')], 'notes': "aazex122:5-7 (A3's q-f2.coffin): it stays shut (Q34)."})
events += [
    {'id': 'evt:throne_dead', 'preset': 'text', 'source': 'platform:throne_dead', 'title': 'Throne of the Dead',
     'text': 'You feel strange.', 'notes': "aazex122:8, :10."},
    {'id': 'evt:throne_master', 'preset': 'text', 'source': 'platform:throne_master', 'title': "The Master's Throne",
     'text': 'You feel strange.', 'notes': "aazex122:9-10."},
    {'id': 'evt:note', 'preset': 'script', 'source': 'platform:note_table', 'title': 'Table',
     'effects': [hook('q-f2.note')], 'notes': "aazex122:24 (A3's q-f2.note)."},
]
SHRINE_ASK = {'minor': "Shrine of Minor Evil.  Destroy?", 'lesser': "Shrine of Lesser Evil.  Destroy?",
              'great': "Shrine of Great Evil.  Destroy?",
              'ultimate': "Shrine of Ultimate Evil. The walls seem to lean on it, and dust runs from the ceiling. "
                          "Destroy?"}
SHRINE_REF = {'minor': 'aazex122:17', 'lesser': 'aazex122:15', 'great': 'aazex122:13',
              'ultimate': "aazex122:11 with A3's tell (D-57 Q26)"}
for k in SHRINES:
    cond = {'not': {'destroyed': f'destructible:shrine_{k}'}}
    if k == 'ultimate':
        cond = {'all': [cond, {'not': {'qbit': 'ultimate_broken'}}]}
    events.append({'id': f'evt:shrine_{k}', 'preset': 'script', 'source': f'platform:shrine_{k}',
                   'title': f'Shrine of {k.title()} Evil', 'condition': cond,
                   'question': {'message': SHRINE_ASK[k], 'ask': 'Destroy (Yes/No)?', 'answers': ['Yes', 'Y']},
                   'effects': [{'destroy': f'destructible:shrine_{k}'}],
                   'else_effects': [{'text': 'The shrine lies broken.'}],
                   'notes': f"{SHRINE_REF[k]}: a real choice; Yes breaks it (its on_destroyed does the rest); blows "
                            "and spells too."})
    down = [hook(f'q-f2.shrine_{k}'), snd('6stone door0101', *SHRINES[k][1], ZS + 160)]
    if k == 'ultimate':
        down += [{'shake': {'strength': 2, 'seconds': 3}}, {'leave': 'exit:x7_gate'}]
    events.append({'id': f'evt:shrine_{k}_down', 'preset': 'script', 'trigger': 'call', 'effects': down,
                   'notes': f"The Shrine of {k.title()} Evil broken (the question, a blow or a spell): A3's "
                            f"q-f2.shrine_{k}" + (" (Fire damage about 20 %, the source's line, 118148), the camera "
                                                  "shake, and out through X7's gate at once, no window (D-57 Q26, D-63 13)." if k == 'ultimate'
                                                  else " (its experience once).")})
events.append({'id': 'evt:shrine_ultimate_load', 'preset': 'script', 'trigger': 'load',
               'condition': {'qbit': 'ultimate_broken'},
               'effects': [{'hide': 'platform:shrine_ultimate'}, {'passable': 'platform:shrine_ultimate'}],
               'notes': "The Shrine of Ultimate Evil stays broken on every load with 118148 (D-57 Q26)."})
# The gongs (D-43, D-57): each ring lights its lamp; the lever after all four raises the shutter; the chest before
# the shutter is up silences them (A3's q-f2.gongs_reset).
for i, (x, y) in GONGS.items():
    events.append({'id': f'evt:gong_{i}', 'preset': 'script', 'source': f'panel:gong_{i}', 'title': 'Gong',
                   'condition': {'not': {'map_var': f'gong{i}'}},
                   'effects': [{'set': {'var': {'map_var': f'gong{i}'}, 'value': 1}}, {'lights_on': f'light:gong_{i}'},
                               snd('xeen_gong' if i % 2 else 'xeen_gong_low', x, y, ZM + 320),
                               {'text': 'The gong rings, and the lamp under it flares up.'}],
                   'else_effects': [snd('xeen_gong' if i % 2 else 'xeen_gong_low', x, y, ZM + 320),
                                    {'text': 'The gong rings again. Its lamp is already lit.'}],
                   'notes': "aazex123:0 'Gong' (the hover); the lines are new map lines. Map variable "
                            f"gong{i}, its lamp light:gong_{i} (D-43: the state shows)."})
    events.append({'id': f'evt:gong_{i}_load', 'preset': 'script', 'trigger': 'load',
                   'condition': {'map_var': f'gong{i}'}, 'effects': [{'lights_on': f'light:gong_{i}'}],
                   'notes': f"Gong {i}'s lamp lit on every load while it is rung."})
ALL_GONGS = {'all': [{'map_var': f'gong{i}'} for i in range(1, 5)]}
events += [
    {'id': 'evt:lever', 'preset': 'switch', 'source': 'switch:lever', 'title': 'Lever',
     'condition': {'all': [ALL_GONGS, {'not': {'qbit': 'shutter_up'}}]}, 'opens': ['door:shutter'],
     'effects': [{'qbit': 'shutter_up'}, snd('6stone door0101', 0, 9984, ZM + 200),
                 {'text': 'The lever moves. Somewhere in the wall chains run, and the iron shutter rises.'}],
     'else_effects': [{'lua': 'if IsQBitSet(QBit(118144)) then evt.StatusText("The lever is down.") else '
                              'evt.SimpleMessage("The lever won\'t budge.\\nA voice booms: Ring the four gongs and then '
                              'pull the lever. Touch any treasure and you\'ll have to start over!") end'}],
     'notes': "aazex123:1-3: before the four gongs 'The lever won't budge.' and the voice (one window); after them it "
              "raises the shutter for good (118144, D-43 one-way)."},
    {'id': 'evt:shutter_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'shutter_up'},
     'opens': ['door:shutter'], 'notes': "Up on every load with 118144."},
    {'id': 'evt:chest_gongs', 'preset': 'chest', 'source': 'chest:gongs', 'title': 'Chest',
     'effects': [{'lua': 'if not IsQBitSet(QBit(118144)) and (IsAtLeast(MapVar(gong1), 1) or IsAtLeast(MapVar(gong2), '
                         '1) or IsAtLeast(MapVar(gong3), 1) or IsAtLeast(MapVar(gong4), 1)) then '
                         'SetValue(MapVar(gong1), 0); SetValue(MapVar(gong2), 0); SetValue(MapVar(gong3), 0); '
                         'SetValue(MapVar(gong4), 0); SetValue(MapVar(reset_pending), 1) end'}],
     'notes': "The source's 'Touch any treasure and you'll have to start over!' (aazex123:3): opened before the shutter "
              "is up with any gong rung, it clears the four gongs; evt:gongs_reset puts their lamps out."},
    {'id': 'evt:gongs_reset', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'map_var': 'reset_pending'},
     'effects': [{'lights_off': [f'light:gong_{i}' for i in range(1, 5)]},
                 {'set': {'var': {'map_var': 'reset_pending'}, 'value': 0}}, hook('q-f2.gongs_reset')],
     'notes': "The lamps go out with A3's 'The gongs fall silent.' (q-f2.gongs_reset, a status line)."},
    {'id': 'evt:fountain', 'preset': 'script', 'source': 'deco:fountain', 'title': 'Fountain',
     'effects': [{'lua': 'for _, i in ipairs(PartyMembers()) do evt.ForPlayer(i); AddValue(HP, 1000); '
                         'AddValue(SP, 1000) end'}, snd('xeen_well_drink', 1600, 9280, ZM + 100),
                 {'text': 'Ahh, refreshing!'}],
     'notes': "aazex123:4-5: hit points and spell points restored, any time (D-4: a free fountain)."},
    {'id': 'evt:papers', 'preset': 'text', 'source': 'platform:papers', 'title': 'Table',
     'text': "You find some papers that tell of the World of Xeen maintenance schedules...",
     'notes': "aazex124:1-2."},
    {'id': 'evt:computer', 'preset': 'text', 'source': 'panel:computer', 'title': 'Computer',
     'text': "Its lights blink in an order you cannot follow.",
     'notes': "aazex124:8 'Computer' (the hover; a new map line)."},
    # The main terminal (D-57 Q35): the source's prompt; 'Computer' pays once (A3's q-f2.terminal).
    {'id': 'evt:terminal', 'preset': 'script', 'source': 'panel:terminal', 'title': 'Main Terminal',
     'condition': {'not': {'qbit': 'code_entered'}},
     'question': {'message': "Main Terminal\nEnter Code", 'ask': 'Code?',
                  'answers': ['Computer', '"Computer"'], 'wrong_effects': [hook('q-f2.terminal_wrong')]},
     'effects': [hook('q-f2.terminal')],
     'else_effects': [hook('q-f2.terminal')],
     'notes': "aazex124:7, :10-11 (A3's q-f2.terminal and terminal_wrong: Goober, then SUPER Goober). The code is "
              "FD-03's heads' (m41.plaques_l4)."},
    {'id': 'evt:machine', 'preset': 'script', 'source': 'platform:machine', 'title': 'Lord Xeen Machine',
     'condition': {'not': {'destroyed': 'destructible:machine'}},
     'question': {'message': 'Lord Xeen Machine. Destroy?', 'ask': 'Destroy (Yes/No)?', 'answers': ['Yes', 'Y']},
     'effects': [{'destroy': 'destructible:machine'}], 'else_effects': [hook('q-f2.machine')],
     'notes': "aazex124:0: a real choice; Yes breaks it (its on_destroyed does the rest); blows and spells too."},
    {'id': 'evt:machine_down', 'preset': 'script', 'trigger': 'call',
     'effects': [hook('q-f2.machine'), {'shake': {'strength': 1.5, 'seconds': 3}},
                 {'lights_off': [f'light:core_{k}' for k in CORE_AT]},
                 {'lua': 'evt.SetMapVar("AmbientSound5", 2)'}]
                + [{'set_texture': {'of': f'platform:core_{k}', 'to': 'swll4dk'}} for k in CORE_AT],
     'notes': "The machine broken: A3's q-f2.machine (118145, Q-F2 done), the hall shakes, the cores go dark and "
              "the machine's sound stops."},
    {'id': 'evt:machine_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'machine_broken'},
     'effects': [{'lights_off': [f'light:core_{k}' for k in CORE_AT]}, {'lua': 'evt.SetMapVar("AmbientSound5", 2)'}]
                + [{'set_texture': {'of': f'platform:core_{k}', 'to': 'swll4dk'}} for k in CORE_AT],
     'notes': "Dark on every load with 118145."},
]
for k, (x, y) in CORE_AT.items():
    events.append({'id': f'evt:term_{k}', 'preset': 'script', 'source': f'platform:term_{k}', 'title': 'Terminal',
                   'condition': {'not': {'qbit': 'machine_broken'}},
                   'effects': [{'message': f"A message flashes on the terminal screen:\n{k.title()} Core Operational"}],
                   'else_effects': [{'message': f"A message flashes on the terminal screen:\n{k.title()} Core Offline"}],
                   'notes': f"aazex124:{ {'fire': 3, 'water': 4, 'air': 5, 'earth': 6}[k] } ('Offline' after the "
                            "machine: a new map line)."})
for cid in ('dorm', 'climber', 'tome', 'crypt'):
    events.append({'id': f'evt:chest_{cid}', 'preset': 'chest', 'source': f'chest:{cid}', 'title': 'Chest'})
wiring = {'format': 0, 'variables': VARS, 'events': events}

atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_cloud_sea'},
              'notes': "The roof hatch over the roof stair's head (its ceiling level's top, sky: true) shows the "
                       "Dragon Clouds' sky (X9's xeencloud, the preset xeen_cloud_sea)."}

project = {
    'format': 0, 'id': 'xeen_fd04', 'name': 'Dragon Tower and the Dungeon of Death', 'world': 'xeen',
    'kind': 'indoor', 'profile': 'dungeon', 'map_code': 'FD-04', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [8, 34], 'climbs': 'n'},
    'map_stats': {'id': 9182, 'encounter_chance': 0, 'treasure_level': 6, 'trap_dice': 10,
                  'perception_difficulty': 20, 'refill_days': 672, 'music': 13, 'environment': 'stoneroom',
                  'lock_difficulty': 20, 'bolster': 'LowerToEqual', 'slots': []},
    'neighbours': [
        {'id': 'exit:x7_gate', 'to': 'xeen_x7.odm', 'kind': 'door', 'arrival': 'entrance:fd04_door',
         'arrival_hint': "On X7's crag before the Dragon Tower's gate: entrance:fd04_door (-17920, 16384, 2592) "
                         "facing south (A5).",
         'notes': "X7 installed (A5). X7's door:fd04 (thing:fd04_gate, the key check q-f1.tower_door) names this "
                  "map's arrival entrance:x7_gate: (0, -1280, 0) facing north."},
        {'id': 'exit:x9_roof', 'to': 'xeen_x9.blv', 'kind': 'door', 'arrival': 'entrance:fd04_roof',
         'arrival_hint': "X9's Dragon Clouds: entrance:fd04_roof [20352, 17280, 2048] facing north (D-57 Q36).",
         'notes': "X9 rebuilt and installed by A5 (03:49) with entrance:fd04_roof. X9's door in the dragon-head rock "
                  "('Descend into Dragon Tower?', aazex128:0) names this map's arrival entrance:x9_clouds: "
                  "(-1312, 608, 4224) facing south."}],
    'qbits': QB,
    'notes': "Xeen design brief, level L4: FD-04 Dragon Tower and the Dungeon of Death on X7 (Q-F1, Q-F2). D-57: "
             "tower 26 (Acid 6, Fire 8, Frost 6, Phase 5, Energy Dragon 100), dungeon 34 (Lich Lord 10, Power Lich 6, "
             "Skeletal Lich 8, Doom Knight 4, Autobot 6): 60 placed, 100.22k per member. Rest encounters 0. Hooks "
             "q-f1.*, q-f2.* (A3). Map qbits 118130-118149. Music 13. Exits: X7 live, X9 live.",
}

# ================================================================================================ plan.yml
FLOORS = {r['id']: r['floor'] for r in rooms}
SPACES = [
    ('room:gate_hall', 'room', 'L', "The arrival (entrance:x7_gate), quiet: Alister's alcove, the stair's foot, Sandro's door (q-f2.door), the passage to the scorched hall."),
    ('room:alcove', 'room', 'S', "Alister the druid (npc 5705, q-f1 topics): peaceful, unkillable; hidden with 118147."),
    ('room:landing0', 'stair', 'S', "The stair's foot."),
    ('room:scorch_pass', 'corridor', 'S', "A low passage round a turn (the quiet gate hall)."),
    ('room:scorched_hall', 'room', 'L', "The old stable: two Acid Dragons."),
    ('room:cellar_stair', 'stair', 'M', "Behind Sandro's door: the stair down 1,024 to the crossword."),
    ('room:ramp01', 'stair', 'M', "The stair in the wall (z 0 to 1,280)."),
    ('room:landing1', 'stair', 'M', "The first landing."),
    ('room:ring_hall', 'room', 'L', "Three dragon pairs round a pier."),
    ('room:dormitory', 'room', 'M', "Beds and a chest (T6)."),
    ('room:bone_alcove', 'room', 'S', "Two dead adventurers' notes (q-f1.note_fraud, note_forever)."),
    ('room:ramp12', 'stair', 'M', "The stair (z 1,280 to 2,560)."),
    ('room:landing2', 'stair', 'M', "The second landing."),
    ('room:nest', 'room', 'L', "Set piece: the bowl with the eggs (q-f1.egg); six dragons."),
    ('room:hatchery', 'room', 'M', "Four dragons; a note (q-f1.note_balls)."),
    ('room:last_climber', 'room', 'S', "The note (q-f1.note_eye), the potion (q-f1.endurance), a chest (T6)."),
    ('room:ramp23', 'stair', 'M', "The stair (z 2,560 to 3,840)."),
    ('room:landing3', 'stair', 'M', "The stair's top."),
    ('room:high_hall', 'room', 'L', "Frost pair and three Phase Dragons."),
    ('room:wyrm_gallery', 'corridor', 'M', "The Wyrm's Hall's door (house 4853)."),
    ('room:crown', 'room', 'L', "Boss: the Energy Dragon and two Phase Dragons."),
    ('room:tome_room', 'room', 'S', "The Tome (q-f1.tome) and a chest (T6)."),
    ('room:roof_stair', 'stair', 'S', "The hatch onto X9 (entrance:x9_clouds on its head)."),
    ('room:crossword', 'room', 'L', "Set piece: the walk-in crossword (twelve clues, q-f2.clue_*)."),
    ('room:descent', 'stair', 'M', "Beyond the gate (q-f2.crossword): 768 down."),
    ('room:welcome', 'room', 'M', "'Welcome': two Lich Lords."),
    ('room:crypt', 'room', 'M', "Do Not Disturb: four coffins (q-f2.coffin), a chest (T6)."),
    ('room:ballroom', 'room', 'L', "Four Skeletal Liches under dead chandeliers."),
    ('room:game_west', 'room', 'M', "Game room: three liches."),
    ('room:game_east', 'room', 'M', "Game room: three liches."),
    ('room:shrines_lesser', 'room', 'M', "The Shrines of Minor and Lesser Evil."),
    ('room:shrines_great', 'room', 'M', "The Shrines of Great and Ultimate Evil."),
    ('room:throne', 'room', 'L', "Two thrones, Sandro's note (q-f2.note), two Doom Knights."),
    ('room:bone_stair', 'stair', 'M', "768 down to the gongs."),
    ('room:gong_hall', 'room', 'L', "Four gongs with lamps, the lever, the chest (T6): the iron shutter."),
    ('room:fountain', 'room', 'S', "The fountain."),
    ('room:maintenance', 'room', 'M', "Papers; two Autobots."),
    ('room:control', 'room', 'M', "The main terminal (q-f2.terminal); two Doom Knights."),
    ('room:machine', 'room', 'L', "Set piece: the Lord Xeen Machine (q-f2.machine) and its six guards."),
]
LINKS = [
    ('link:gate_alcove', 'room:gate_hall', 'room:alcove', 'open'),
    ('link:gate_up', 'room:gate_hall', 'room:landing0', 'open'),
    ('link:gate_scorched', 'room:gate_hall', 'room:scorch_pass', 'open'),
    ('link:scorch_hall', 'room:scorch_pass', 'room:scorched_hall', 'open'),
    ('link:gate_crossword', 'room:gate_hall', 'room:cellar_stair', 'door'),
    ('link:cellar_down', 'room:cellar_stair', 'room:crossword', 'stairs'),
    ('link:foot_ramp', 'room:landing0', 'room:ramp01', 'stairs'),
    ('link:ramp_l1', 'room:ramp01', 'room:landing1', 'stairs'),
    ('link:l1_ring', 'room:landing1', 'room:ring_hall', 'open'),
    ('link:dorm_l1', 'room:landing1', 'room:dormitory', 'door'),
    ('link:ring_dorm', 'room:ring_hall', 'room:dormitory', 'open'),
    ('link:ring_bones', 'room:ring_hall', 'room:bone_alcove', 'open'),
    ('link:l1_ramp', 'room:landing1', 'room:ramp12', 'stairs'),
    ('link:ramp_l2', 'room:ramp12', 'room:landing2', 'stairs'),
    ('link:l2_nest', 'room:landing2', 'room:nest', 'open'),
    ('link:hatch_l2', 'room:landing2', 'room:hatchery', 'open'),
    ('link:nest_hatch', 'room:nest', 'room:hatchery', 'open'),
    ('link:nest_dead', 'room:nest', 'room:last_climber', 'open'),
    ('link:l2_ramp', 'room:landing2', 'room:ramp23', 'stairs'),
    ('link:ramp_l3', 'room:ramp23', 'room:landing3', 'stairs'),
    ('link:l3_high', 'room:landing3', 'room:high_hall', 'open'),
    ('link:l3_gallery', 'room:landing3', 'room:wyrm_gallery', 'open'),
    ('link:high_crown', 'room:high_hall', 'room:crown', 'open'),
    ('link:gallery_crown', 'room:wyrm_gallery', 'room:crown', 'open'),
    ('link:crown_tome', 'room:crown', 'room:tome_room', 'door'),
    ('link:crown_roof', 'room:crown', 'room:roof_stair', 'door'),
    ('link:crossword_descent', 'room:crossword', 'room:descent', 'portcullis'),
    ('link:descent_welcome', 'room:descent', 'room:welcome', 'stairs'),
    ('link:welcome_crypt', 'room:welcome', 'room:crypt', 'door'),
    ('link:welcome_ball', 'room:welcome', 'room:ballroom', 'double_door'),
    ('link:ball_west', 'room:ballroom', 'room:game_west', 'open'),
    ('link:ball_east', 'room:ballroom', 'room:game_east', 'open'),
    ('link:west_lesser', 'room:game_west', 'room:shrines_lesser', 'open'),
    ('link:east_great', 'room:game_east', 'room:shrines_great', 'open'),
    ('link:lesser_throne', 'room:shrines_lesser', 'room:throne', 'open'),
    ('link:great_throne', 'room:shrines_great', 'room:throne', 'open'),
    ('link:throne_stair', 'room:throne', 'room:bone_stair', 'open'),
    ('link:stair_gongs', 'room:bone_stair', 'room:gong_hall', 'stairs'),
    ('link:gongs_fountain', 'room:gong_hall', 'room:fountain', 'open'),
    ('link:gongs_maint', 'room:gong_hall', 'room:maintenance', 'portcullis'),
    ('link:maint_machine', 'room:maintenance', 'room:machine', 'open'),
    ('link:maint_control', 'room:maintenance', 'room:control', 'door'),
    ('link:control_machine', 'room:control', 'room:machine', 'open'),
]


def plan_doc(level):
    pops = {}
    for rid, _, ms in PLACED:
        for mon, _, _ in ms:
            pops.setdefault(f'room:{rid}', {}).setdefault(mon, 0)
            pops[f'room:{rid}'][mon] += 1
    spaces = []
    for sid, kind, size, purpose in SPACES:
        kind = {'stair': 'corridor'}.get(kind, kind)
        s = {'id': sid, 'name': R_[sid]['name'], 'kind': kind, 'size': size, 'floor': FLOORS[sid], 'purpose': purpose}
        if sid in pops:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [n, n], 'levels': [LEVELS[m], LEVELS[m]],
                                'notes': f"{n} {NAMES[m]} {LEVELS[m]} (placed)"} for m, n in pops[sid].items()]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [{'id': i, 'from': f, 'to': t, 'kind': k} for i, f, t, k in LINKS]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "A black tower on Mount Firestone's crag where the dragons nest, and under it Sandro's old home: a "
                 "walk-in crossword, a ballroom of liches, four Shrines of Evil, the gongs and the Lord Xeen Machine.",
        'purpose': "Optional finale. Q-F1: Alister's egg (the nest), the dead climbers' notes, the Tome, the roof to "
                   "X9's Dragon Clouds. Q-F2: Sandro's door, the crossword, the shrines, the gongs and the lever, the "
                   "main terminal (COMPUTER), the machine. Party 62 to 66; 60 placed at 65-100; treasure 6.",
        'mood': "Warm black basalt that ticks as it cools, the smell of scorched straw; below, dust, incense and a "
                "machine that has run for a thousand years.",
        'datum': 'arrival', 'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:ring1', 'spaces': ['room:landing1', 'room:ring_hall', 'room:dormitory'],
             'notes': "Floor 1: into the ring hall from the landing or through the dormitory."},
            {'id': 'loop:nest', 'spaces': ['room:landing2', 'room:nest', 'room:hatchery'],
             'notes': "Floor 2: the nest directly or through the hatchery."},
            {'id': 'loop:top', 'spaces': ['room:landing3', 'room:high_hall', 'room:crown', 'room:wyrm_gallery'],
             'notes': "Floor 3: the crown through the high hall or along the Wyrm's gallery."},
            {'id': 'loop:sandro', 'spaces': ['room:ballroom', 'room:game_east', 'room:shrines_great', 'room:throne',
                                             'room:shrines_lesser', 'room:game_west'],
             'notes': "Sandro's halls: a ring from the ballroom through either game room and its shrines to the "
                      "thrones."},
            {'id': 'loop:machine', 'spaces': ['room:maintenance', 'room:machine', 'room:control'],
             'notes': "The machine floor: from maintenance directly or through the control room."}],
        'entrances': [
            {'id': 'entrance:x7_gate', 'space': 'room:gate_hall', 'kind': 'both', 'facing': 'n',
             'how': "From X7's Dragon Tower gate (A5, door:fd04 with the key): 256 inside the gate, facing north."},
            {'id': 'entrance:x9_clouds', 'space': 'room:roof_stair', 'kind': 'both', 'facing': 's',
             'how': "From X9's door in the dragon-head rock (A5): on the roof stair's head, facing down the stair."}],
        'critical_path': ['room:gate_hall', 'room:landing0', 'room:ramp01', 'room:landing1', 'room:ring_hall',
                          'room:landing1', 'room:ramp12', 'room:landing2', 'room:nest', 'room:landing2', 'room:ramp23',
                          'room:landing3', 'room:high_hall', 'room:crown', 'room:roof_stair'],
        'return_path': ['room:roof_stair', 'room:crown', 'room:wyrm_gallery', 'room:landing3', 'room:ramp23',
                        'room:landing2', 'room:ramp12', 'room:landing1', 'room:ramp01', 'room:landing0',
                        'room:gate_hall', 'room:cellar_stair', 'room:crossword', 'room:descent', 'room:welcome',
                        'room:ballroom', 'room:game_east', 'room:shrines_great', 'room:throne', 'room:bone_stair',
                        'room:gong_hall', 'room:maintenance', 'room:machine'],
        'goals': [
            {'id': 'goal:egg', 'space': 'room:nest', 'kind': 'use', 'story': 'Q-F1', 'what': "The Dragon Egg (q-f1.egg) for Alister."},
            {'id': 'goal:crossword', 'space': 'room:crossword', 'kind': 'use', 'story': 'Q-F2',
             'what': "Twelve words (q-f2.clue_*); the descent (q-f2.crossword)."},
            {'id': 'goal:machine', 'space': 'room:machine', 'kind': 'use', 'story': 'Q-F2',
             'what': "The Lord Xeen Machine (q-f2.machine)."}],
        'set_pieces': [
            {'id': 'set:nest', 'kind': 'scripted', 'spaces': ['room:nest'], 'rule': "The bowl of black rock and the eggs."},
            {'id': 'set:crown', 'kind': 'boss', 'spaces': ['room:crown'], 'rule': "The Energy Dragon before the roof stair."},
            {'id': 'set:crossword', 'kind': 'scripted', 'spaces': ['room:crossword'],
             'rule': "A solved word lights across the floor (xfword, a glow)."},
            {'id': 'set:machine', 'kind': 'scripted', 'spaces': ['room:machine'],
             'rule': "The machine breaks: the hall shakes, the cores go dark."}],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': len(rooms), 'sectors': len(rooms), 'monsters_about': 60, 'chests': 5, 'doors': 9,
                   'loops': 5, 'floor_area_munits2': 60},
        'notes': "Size M (20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors). From "
                 "act6_graphs/fd04.graph.yml and D-57 (FD-04, Q22-Q35): the graph's rooms plus the stair's landings "
                 "and three ramps, the scorched hall's passage and Alister's alcove.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """FD-04 Dragon Tower and the Dungeon of Death (not to scale; plan, north up)
TOWER (z 0 / 1280 / 2560 / 3840; the stair winds up in the wall: W side, N side, E side)
  F3 3840  [HIGH HALL]-arch-[CROWN: Energy Dragon]-door-[ROOF STAIR -> hatch (X9)]   [TOME]-door-[CROWN]
           [LANDING 3] <- ramp (E side) ; [WYRM'S GALLERY: house 4853] -> [CROWN]
  F2 2560  [LANDING 2] -> [NEST: bowl, eggs] / [HATCHERY]   [NEST] -> [LAST CLIMBER]
  F1 1280  [LANDING 1] -> [RING HALL: pier] / [DORMITORY]-door-[LANDING 1]   [RING HALL] -> [BONE ALCOVE]
  F0    0  (X7) =gate= [GATE HALL: Alister's alcove W] -> [STAIR'S FOOT] -> ramp (W side)
                       [GATE HALL] -> passage (turn) -> [SCORCHED HALL]   [GATE HALL] =Sandro's door= [CELLAR WELL]
DUNGEON (north of the tower)
  -1 -1024 [CELLAR WELL] -> [CROSSWORD: 12 words] =gate= [DESCENT]
  -2 -1792 [WELCOME]-door-[DO NOT DISTURB] ; [WELCOME]=pair=[BALLROOM] -> [GAME W]/[GAME E] -> [SHRINES L]/[SHRINES G]
           -> [THRONE OF THE DEAD] -> [BONE STAIR]
  -3 -2560 [GONG HALL: 4 gongs, lever, chest] -> [FOUNTAIN] ; =shutter= [MAINTENANCE] -> [MACHINE] / door [CONTROL]
"""


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
        p['notes'] = f"Xeen design brief, level {lv}: FD-04 Dragon Tower and the Dungeon of Death (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: FD-04, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('atmosphere.yml', atmosphere),
                     ('diagram.txt', DIAGRAM)])
print('written L4; kill xp per member', KILL_XP, 'plates', len(objects_plates), 'rooms', len(rooms))
