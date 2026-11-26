#!/usr/bin/env python3
"""XD-13 Newcastle Keep (staged): writes the L1-L4 project folders of devdocs/xeen/briefs/xd13 (agent:xeen-a7-xd13).

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd13/cycle.sh); never hand-edit the written files.

Frame: x east, y north, z up. The keep at z 0 (the gate, where the party arrives from X3's Newcastle site, the great
hall, the pantry, the statue court and the head of the dungeon stair); the foundation pit, the rubble ramp, the
flooded cellar, the old laboratory and the sword vault at -640. Rooms stand 128 apart (the walls' thickness).

Stages (QUESTS 4.1, A3's qbits, Xeen.stageOf("newcastle")): the map is BUILT as stage 0 (the ruin, the deed bought) and
its load events turn it into stage 2 (m11.keep) and stage 3 (m22.dungeon): faces hidden and shown, doors and the pit's
lift moved, actor groups hidden and shown, textures swapped (ROADMAP 7, E6)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd13'

# X3 (installed, lane A5, briefs/x3/DOORS.md): X3's thing:xd13_stair (the hatch at about (10496, 15616)) leads in to this
# map's start; this map's gate leads out to A5's arrival 400 south of the hatch, facing south.
X3_STEM = 'xeen_x3.odm'
X3_ARRIVAL = [10496, 15216, 1760]


def S(t, w=None, h=None, **kw):
    d = {'texture': t}
    if w is not None:
        d['size'] = [w, h]
    d.update(kw)
    return d


# The keep: MM7 Castle Harmondale (7d29), the shipped castle that is rebuilt from a ruin: its fieldstone (chb1), green
# flags (tfb09), warm marble ceilings (7tws1h), oak doors (chb1dl); the darker ruined stone of Harmondale's ruin pieces
# (ch1b1, ch1b1dl) for what the stages repair; Harmondale's own shop signs on the services' doors; the royal kit's
# Newcastle arms (xkncscrst) and banner (xkncsban) from stage 2.
CHB1 = S('chb1', 128, 256)
CHB1S = S('chb1s', 128, 256)
RUIN = S('ch1b1', 128, 256)
RUIN_FIT = S('ch1b1', 128, 256, fit=True)
RUIN_DOOR = S('ch1b1dl', 128, 256, fit=True)
CHALK = S('xnchalk', 64, 64, fit=True)
OAK_DOOR = S('chb1dl', 128, 256, fit=True)
FLAGS = S('tfb09', 128, 128)
CEIL = S('7tws1h', 128, 128)
PLANK = S('7gt002a', 64, 64)
BOARDS = S('7gt003a', 64, 64)
BANNER = 'xkncsban'
CREST = 'xkncscrst'
SIGNS = {'smithy': 'sgweapon', 'training': '7sgtrain', 'chapel': 'sgtempl', 'counting': '7sgbank'}
# Below: the foundations' rough rust stone (cwb1) and earth (cfb1) under the hall's boards (7gt003a); the old dungeon in
# Harmondale's grey castle brick (cwb) on the same flags; the lagoon water (7wtrtyl, the game's liquid); the
# scientists' shelves and books (7t1cabs, 7t1books); the vault's riveted iron door (t5d1) and XD-02's grille (xngrille).
ROUGH = S('cwb1', 128, 256)
EARTH = S('cfb1', 128, 128)
BRICK = S('cwb', 128, 256)
WATER = {'texture': '7wtrtyl', 'liquid': 'water'}
CABS = S('7t1cabs', 64, 128)
BOOKS = S('7t1books', 128, 256, fit=True)
IRON = S('t5d1', 128, 256, fit=True)
GRILLE = S('xngrille', 128, 256, fit=True)
HOLE = S('7solid01', 128, 256, fit=True)    # F71: black, the hole behind the speaking grille

themes = [
    {'id': 'theme:keep', 'wall': CHB1, 'floor': FLAGS, 'ceiling': CEIL, 'door': OAK_DOOR, 'reveal': CHB1,
     'notes': "The keep: Castle Harmondale's fieldstone (chb1), green flags (tfb09) and warm marble ceilings (7tws1h)."},
    {'id': 'theme:foundation', 'wall': ROUGH, 'floor': EARTH, 'ceiling': BOARDS, 'door': BOARDS, 'reveal': ROUGH,
     'notes': "Under the great hall: rough rust-stained footings (cwb1), earth (cfb1), the hall's boards overhead (7gt003a)."},
    {'id': 'theme:dungeon', 'wall': BRICK, 'floor': FLAGS, 'ceiling': ROUGH, 'door': IRON, 'reveal': BRICK,
     'notes': "The old dungeon: Harmondale's grey castle brick (cwb) on the keep's flags, rough vaults (cwb1)."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


RECTS = {}
rooms = []
openings = []


def room(id, name, r=None, **kw):
    d = {'id': id, 'name': name}
    if r is not None:
        RECTS[id] = r
        d['outline'] = rect(*r)
    d.update(kw)
    rooms.append(d)
    return d


def op(id, frm, to, **kw):
    d = {'id': id, 'from': frm, 'to': to}
    d.update(kw)
    openings.append(d)


def off(rid, wall, centre, length):
    """Offset of a panel of `length` centred on map coordinate `centre` along `wall` of rectangular room rid."""
    x0, y0, x1, y1 = RECTS[rid]
    near = {'south': centre - length / 2 - x0, 'east': centre - length / 2 - y0,
            'north': x1 - (centre + length / 2), 'west': y1 - (centre + length / 2)}[wall]
    return int(near)


def panel(rid, wall, pid, centre, length, bottom, height, surface, notes=None):
    d = {'offset': off(rid, wall, centre, length), 'length': length, 'bottom': bottom, 'height': height,
         'surface': surface}
    if pid:
        d = {'id': pid, **d}
    if notes:
        d['notes'] = notes
    return d


def block(id, at, size, rise, side, top=None, notes=None, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': side}
    if id:
        d = {'id': id, **d}
    if top:
        d['top_surface'] = top
    if notes:
        d['notes'] = notes
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ the keep (z 0)
GATE = (-448, 0, 448, 768)
HALL = (-1152, 896, 1152, 3072)
PANTRY = (-2816, 2560, -1280, 3328)
COURT = (1280, 896, 3072, 2560)
STAIR_HEAD = (2304, 256, 2752, 768)
DSTAIR = (2304, -1024, 2752, 128)
PIT = (-1664, 1152, -256, 2048)
CELLAR = (1792, -2560, 3328, -1152)
LAB = (256, -2560, 1664, -1280)
VDOOR = (-640, -2112, 128, -1728)
VAULT = (-1664, -2432, -768, -1408)
HOLE_AT, HOLE_SIZE = [-704, 1600], [512, 384]
ROOF = (-448, 1792, 448, 2560)               # the fallen part of the hall's roof (a lantern up to the rafters)
RECTS.update({'room:gate': GATE, 'room:great_hall': HALL, 'room:pantry': PANTRY, 'room:statue_court': COURT,
              'room:stair_head': STAIR_HEAD, 'room:dungeon_stair': DSTAIR, 'room:foundation_pit': PIT,
              'room:cellar': CELLAR, 'room:old_lab': LAB, 'room:vault_door': VDOOR, 'room:sword_vault': VAULT})

room('room:gate', 'Keep gate', GATE, floor=0, ceiling=512, theme='theme:keep', ambient=18,
     walls=[{'wall': 'west', 'panels': [
                panel('room:gate', 'west', 'door:smithy', 384, 160, 0, 320, RUIN_DOOR,
                      "The smithy's door (A4's house 4141, opens with the keep, m11.keep): Harmondale's ruined arched "
                      "door until then, its oak door after."),
                panel('room:gate', 'west', 'panel:sign_smithy', 384, 96, 352, 96, CHALK,
                      "Above the smithy's door: Emerson's chalk mark (xnchalk), Harmondale's weapon sign from stage 2.")]},
            {'wall': 'east', 'panels': [
                panel('room:gate', 'east', 'panel:crest', 384, 128, 160, 256, RUIN_FIT,
                      "Newcastle's arms (xkncscrst) from stage 2; a patch of fallen stone before.")]}],
     notes="Inside the gate from X3's Newcastle site (896 by 768): the smithy's door in the west wall, the arms in the east "
           "wall, the arch north into the great hall.")
room('room:great_hall', 'Great hall', HALL, floor=0, ceiling=768, theme='theme:keep', ambient=16,
     ceiling_levels=[{'outline': rect(*ROOF), 'ceiling': 1152, 'surface': dict(BOARDS, sky=True), 'edge': RUIN,
                      'notes': "Where the roof fell in: the open sky over the bare rafters (D-22.6; the stage-2 roof "
                               "patch hides it)."}],
     beams=[{'path': [[HALL[0], y], [HALL[2], y]], 'width': 32, 'depth': 32, 'bottom': 704, 'surface': BOARDS,
             'notes': "A tie beam across the hall, wall to wall, blackened."} for y in (1984, 2368)],
     platforms=[
         block('platform:roof_patch', [0, (ROOF[1] + ROOF[3]) // 2], [ROOF[2] - ROOF[0], ROOF[3] - ROOF[1]], 16, CEIL,
               CEIL, "Stage 2: the new roof under the old rafters (hidden by the load event while the keep stands "
               "unbuilt).", base=752, bottom_surface=CEIL),
         block('platform:rubble_ne', [896, 2816], [384, 320], 56, RUIN, RUIN,
               "Rubble: fallen roof stone in the north-east corner (gone at stage 2)."),
         block('platform:rubble_se', [928, 1184], [320, 384], 40, RUIN, RUIN,
               "Rubble against the east wall south of the court's arch (gone at stage 2)."),
         # face.in_doorway (2026-11-24): at y 2880 it ran across the pantry door (y 2736-2896); now south of it.
         block('platform:woodpile', [-896, 2240], [384, 256], 72, BOARDS, BOARDS,
               "The woodpile: the old roof's beams, sawn and stacked against the west wall (gone at stage 2)."),
     ],
     walls=[{'wall': 'north', 'panels': [
                panel('room:great_hall', 'north', 'panel:banner_w', -576, 128, 256, 256, RUIN_FIT,
                      "Newcastle's banner (xkncsban) from stage 2; cracked ruined stone before."),
                panel('room:great_hall', 'north', 'panel:banner_e', 576, 128, 256, 256, RUIN_FIT,
                      "The second banner."),
                panel('room:great_hall', 'north', 'panel:la', 0, 128, 96, 128, CHB1,
                      "The first syllable scratched into the stone (A3's m23.syllable_la).")]}],
     notes="The great hall, 2,304 by 2,176, 768 high: at stage 0 the roof has fallen in over its middle (bare rafters), "
           "rubble lies in the east corners, the woodpile against the west wall, and the floor has broken through into "
           "the foundation pit west of the middle. From stage 2 the roof is mended, the hole floored over, the rubble "
           "gone, Newcastle's banners hang on the north wall. Doors: the gate (south), the pantry (west), the statue "
           "court (east, an open arch).")
room('room:pantry', 'Pantry', PANTRY, floor=0, ceiling=384, theme='theme:keep', ambient=20, store=True,
     platforms=[block('platform:larder', [-2048, 3232], [512, 128], 64, CABS, BOARDS,
                      "The larder bin against the north wall: 'Food. Fill pack?'")],
     notes="The keep's pantry, 1,536 by 768 (a storeroom: sacks and barrels along the walls): the larder bin, the second "
           "syllable under a sack; the rubble ramp up from the foundation pit comes in through the south wall (walled up "
           "from stage 2).")
room('room:statue_court', 'Statue court', COURT, floor=0, ceiling=640, theme='theme:keep', ambient=16,
     platforms=[
         block('platform:statue_plinth', [2176, 1728], [256, 256], 48, CHB1S, FLAGS,
               "The statue's plinth with its plaque."),
         block('platform:well', [2752, 1216], [224, 224], 56, CHB1S, WATER,
               "YOUR well: a stone curb round the water (the water only from stage 3, under the rubble cap)."),
         block('platform:well_cap', [2752, 1216], [192, 192], 24, RUIN, RUIN,
               "The rubble that chokes the well until Emerson's diggers clear it (hidden at stage 3).", base=56),
     ],
     walls=[{'wall': 'east', 'panels': [
                panel('room:statue_court', 'east', 'door:training', 1856, 160, 0, 320, RUIN_DOOR,
                      "The training hall's door (house 4142, m11.keep)."),
                panel('room:statue_court', 'east', 'panel:sign_training', 1856, 96, 352, 96, CHALK)]},
            {'wall': 'north', 'panels': [
                panel('room:statue_court', 'north', 'door:chapel', 1792, 160, 0, 320, RUIN_DOOR,
                      "The chapel's door (house 4143, m22.dungeon)."),
                panel('room:statue_court', 'north', 'panel:sign_chapel', 1792, 96, 352, 96, CHALK),
                panel('room:statue_court', 'north', 'door:counting', 2560, 160, 0, 320, RUIN_DOOR,
                      "The counting room's door (house 4144, m22.dungeon)."),
                panel('room:statue_court', 'north', 'panel:sign_counting', 2560, 96, 352, 96, CHALK)]},
            {'wall': 'south', 'panels': [
                panel('room:statue_court', 'south', 'panel:ra', 2176, 128, 96, 128, CHB1,
                      "The third syllable, on the wall beside the dungeon stair (A3's m23.syllable_ra).")]}],
     notes="The statue court, 1,792 by 1,664: the statue of the Great Adventurers on its plinth in the middle, YOUR well "
           "in the south-east corner; the training hall's door (east), the chapel's and the counting room's (north), "
           "the dungeon stair (south).")
room('room:stair_head', 'Head of the dungeon stair', STAIR_HEAD, floor=0,
     slope={'to': -128, 'toward': 'south', 'steps': 4, 'riser': CHB1S, 'tread': FLAGS},
     ceiling=384, ceiling_slope={'to': 256, 'toward': 'south'}, theme='theme:keep', ambient=22,
     notes="Four steps down south from the statue court to where the old dungeon stair is choked with rubble.")
room('room:dungeon_stair', 'Dungeon stair', DSTAIR, floor=-128,
     slope={'to': -640, 'toward': 'south', 'steps': 16, 'riser': BRICK, 'tread': FLAGS},
     ceiling=256, ceiling_slope={'to': -256, 'toward': 'south'}, theme='theme:dungeon', ambient=22,
     notes="Sixteen steps of 32 down south into the old dungeon, dug out by Emerson's men at stage 3.")

# ------------------------------------------------------------------------------------------------ below (z -640)
room('room:foundation_pit', 'Foundation pit', PIT, floor=-640, ceiling=-128, theme='theme:foundation', ambient=20,
     beams=[{'path': [[PIT[0], 1792], [PIT[2], 1792]], 'width': 32, 'depth': 48, 'bottom': -224, 'surface': BOARDS,
             'notes': "One of the hall's old floor joists, still in place."}],
     notes="Under the great hall's west half, 1,408 by 896: where the hall's floor fell in. Wood golems grown out of the "
           "old beams; the scientists' strongbox. The rubble ramp climbs west and north to the pantry.")
room('room:rubble_ramp', 'Rubble ramp', None, path=[[-1792, 1408, -640], [-2560, 1408, -384], [-2560, 2432, 0]],
     width=320, floor=-640, ceiling=-256, theme='theme:foundation', ambient=22,
     notes="A ramp of fallen masonry from the pit up into the pantry: 768 west rising 256, then 1,024 north rising 384.")
room('room:cellar', 'Flooded cellar', CELLAR, floor=-640, ceiling=-192, theme='theme:dungeon', ambient=14,
     levels=[{'id': 'level:flood', 'outline': rect(2048, -2432, 3200, -1536), 'floor': -680, 'edge': BRICK,
              'surface': WATER, 'notes': "Lagoon water seeped in: a sunken floor under 40 of standing water."}],
     platforms=[block('platform:shelf', [3248, -1856], [128, 384], 96, CABS, CABS,
                      "A shelf against the east wall: the fourth syllable lies on it.")],
     notes="The flooded cellar at the stair's foot, 1,536 by 1,408: lagoon water standing in its middle; swamp things. "
           "The old laboratory west.")
room('room:old_lab', 'Old laboratory', LAB, floor=-640, ceiling=-224, theme='theme:dungeon', ambient=16,
     platforms=[block('platform:workbench', [960, -2432], [640, 160], 72, CABS, CABS,
                      "The scientists' workbench against the south wall, their notebooks on it.")],
     walls=[{'wall': 'north', 'panels': [
                panel('room:old_lab', 'north', None, 576, 128, 0, 256, BOOKS),
                panel('room:old_lab', 'north', None, 704, 128, 0, 256, BOOKS),
                panel('room:old_lab', 'north', None, 1216, 128, 0, 256, BOOKS),
                panel('room:old_lab', 'north', None, 1344, 128, 0, 256, BOOKS)]},
            {'wall': 'west', 'panels': [
                panel('room:old_lab', 'west', 'panel:ry', -1472, 128, 96, 128, BRICK,
                      "The fifth syllable, the last wall before the vault (A3's m23.syllable_ry).")]}],
     notes="The scientists' wrecked workshop, 1,408 by 1,280: bookshelves on the north wall, the workbench on the south, a "
           "cauldron in a corner; the way west to the vault door.")
# F71 (the player's pin XD-13 p2, 2026-11-26 "is here something missing?"): the grille was a wall panel in xngrille, a
# cutout (XD-02's hoist gate, with the shaft behind it): on a solid wall its open texels showed the sky between the
# bars. The grille is now a thin iron frame 4 off the wall, the bars on its face, in front of a black speaking hole
# (7solid01, a panel in the wall) (tools/xeen/check_cutout_backing.py).
room('room:vault_door', 'Vault door', VDOOR, floor=-640, ceiling=-224, theme='theme:dungeon', ambient=18,
     walls=[{'wall': 'north', 'panels': [
                panel('room:vault_door', 'north', None, -448, 128, 64, 224, HOLE,
                      "The speaking hole behind the grille.")]}],
     platforms=[block('platform:grille', [-448, VDOOR[3] - 8], [128, 8], 224, GRILLE, BRICK,
                      "The speaking grille beside the vault door, 4 off the wall over its hole.", base=64,
                      end_surface=BRICK, bottom_surface=BRICK)],
     notes="A short passage, 768 by 384, to the vault's steel door with its speaking grille: 'What is the password?'")
room('room:sword_vault', 'Sword vault', VAULT, floor=-640, ceiling=-192, theme='theme:dungeon', ambient=12,
     platforms=[block('platform:pedestal', [-1216, -1920], [192, 192], 72, CHB1S, FLAGS,
                      "The pedestal in the middle of the vault."),
                block('platform:sword_rack', [-1216, -1488], [512, 96], 160, CABS, CABS,
                      "A rack of tools nobody remembers how to use, against the north wall: the sword's box on it (chest:sword, D-90).")],
     notes="The deepest room, 896 by 1,024: the pedestal, the scientists' rack and the vault's own hoard.")

# ------------------------------------------------------------------------------------------------ openings
op('open:gate_hall', 'room:gate', 'room:great_hall', link='link:gate_hall', width=384, height=352, shape='arch',
   apex=416)
op('open:hall_pantry', 'room:great_hall', 'room:pantry', link='link:hall_pantry', width=160, height=320)
op('open:hall_court', 'room:great_hall', 'room:statue_court', link='link:hall_court', width=512, height=416,
   shape='arch', apex=512)
op('open:hall_pit', 'room:great_hall', 'room:foundation_pit', in_='floor', at=HOLE_AT, size=HOLE_SIZE,
   link='link:hall_pit')
op('open:court_stair', 'room:statue_court', 'room:stair_head', link='link:court_stair', width=320, height=320)
op('open:stair_rubble', 'room:stair_head', 'room:dungeon_stair', link='link:stair_cellar', width=320, height=224)
op('open:stair_cellar', 'room:dungeon_stair', 'room:cellar', link='link:stair_cellar', width=320, height=256)
op('open:cellar_lab', 'room:cellar', 'room:old_lab', link='link:cellar_lab', width=384, height=320)
op('open:lab_vaultdoor', 'room:old_lab', 'room:vault_door', link='link:lab_vaultdoor', width=320, height=320)
op('open:vault', 'room:vault_door', 'room:sword_vault', link='link:vault', width=192, height=384)
op('open:pit_ramp', 'room:foundation_pit', 'room:rubble_ramp', link='link:pit_pantry', width=256, height=320)
op('open:ramp_pantry', 'room:rubble_ramp', 'room:pantry', link='link:pit_pantry', width=256, height=320)
for o in openings:                     # 'in' is a Python keyword
    if 'in_' in o:
        o['in'] = o.pop('in_')

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:keep', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-13 Newcastle Keep: the keep at z 0, the foundations and the old dungeon at -640; x east, y "
                      "north. Built as stage 0 (the ruin); the load events make stages 2 and 3. Written by "
                      "output/studio_cal/xd13/tools/gen.py."}

# ================================================================================================ plan.yml
FLOOR0 = {'room:gate', 'room:great_hall', 'room:pantry', 'room:statue_court', 'room:stair_head'}
PLAN_SPACES = [
    ('room:gate', 'Keep gate', 'room', 'S', "Inside the gate from X3's Newcastle site; the smithy's door (stage 2).", 0),
    ('room:great_hall', 'Great hall', 'hall', 'L', "Stage 0 a ruin (roof fallen in, rubble, woodpile, the floor broken into the pit), stage 2 the lord's hall with Newcastle's banners. Syllable 1 'la'.", 6),
    ('room:pantry', 'Pantry', 'room', 'S', "'Food. Fill pack?'; syllable 2 'bo' under a sack.", 0),
    ('room:statue_court', 'Statue court', 'room', 'M', "The statue of the Great Adventurers; YOUR well (stage 3); the training hall (stage 2), chapel and counting room (stage 3) doors; syllable 3 'ra'.", 4),
    ('room:stair_head', 'Head of the dungeon stair', 'stair', 'S', "Until stage 3: 'A short distance down the stairs you find the way blocked with rubble.'", 0),
    ('room:dungeon_stair', 'Dungeon stair', 'stair', 'S', "Dug out at stage 3: down to the old dungeon.", 0),
    ('room:foundation_pit', 'Foundation pit', 'cave', 'M', "Stage 0-1: where the hall's floor fell in; wood golems; the scientists' strongbox.", 5),
    ('room:rubble_ramp', 'Rubble ramp', 'corridor', 'S', "The way back up from the pit into the pantry (walled up at stage 2).", 0),
    ('room:cellar', 'Flooded cellar', 'cave', 'M', "Stage 3: lagoon water seeped in; swamp things; syllable 4 'to' on a shelf.", 6),
    ('room:old_lab', 'Old laboratory', 'room', 'M', "Stage 3: the scientists' wrecked workshop and notebooks; syllable 5 'ry'; two iron golems.", 2),
    ('room:vault_door', 'Vault door', 'corridor', 'S', "The steel door with a speaking grille: 'What is the password?'; two iron golems.", 2),
    ('room:sword_vault', 'Sword vault', 'room', 'S', "The pedestal and the experimental Xeen Slayer Sword (M23).", 0),
]
STAGE_KEEP = {'any': [{'qbit': 'keep'}, {'qbit': 'dungeon'}]}
STAGE_RUIN = {'not': STAGE_KEEP}
STAGE_DUNGEON = {'qbit': 'dungeon'}


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, n in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': {'hall': 'room', 'stair': 'corridor', 'cave': 'room'}.get(kind, kind), 'size': size, 'floor': 0 if sid in FLOOR0 else -640,
             'purpose': purpose}
        if n:
            fam = {'room:great_hall': 'Wood Golem', 'room:statue_court': 'Wood Golem', 'room:foundation_pit': 'Wood Golem',
                   'room:cellar': 'Bog Thing and Marsh Horror', 'room:old_lab': 'Iron Golem',
                   'room:vault_door': 'Iron Golem'}[sid]
            lv = {'Wood Golem': [18, 18], 'Bog Thing and Marsh Horror': [26, 32], 'Iron Golem': [40, 40]}[fam]
            s['population'] = [{'slot': 1 if 'Golem' in fam else 2, 'groups': 1, 'per_marker': [n, n], 'levels': lv,
                                'notes': f"{n} {fam}s placed ({'stage 0-1' if fam == 'Wood Golem' else 'stage 3'})."}]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:gate_hall', 'from': 'room:gate', 'to': 'room:great_hall', 'kind': 'open'},
        {'id': 'link:hall_pantry', 'from': 'room:great_hall', 'to': 'room:pantry', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:hall_court', 'from': 'room:great_hall', 'to': 'room:statue_court', 'kind': 'open'},
        {'id': 'link:hall_pit', 'from': 'room:great_hall', 'to': 'room:foundation_pit', 'kind': 'drop',
         'condition': STAGE_RUIN, 'notes': "The broken floor; floored over at stage 2 (the pit's lift rises into the hole)."},
        {'id': 'link:pit_pantry', 'from': 'room:foundation_pit', 'to': 'room:pantry', 'kind': 'stairs',
         'condition': STAGE_RUIN, 'notes': "The rubble ramp; walled up at stage 2 (a door shut by the load event)."},
        {'id': 'link:court_stair', 'from': 'room:statue_court', 'to': 'room:stair_head', 'kind': 'stairs'},
        {'id': 'link:stair_cellar', 'from': 'room:stair_head', 'to': 'room:cellar', 'kind': 'door', 'motion': 'slide',
         'condition': STAGE_DUNGEON, 'notes': "The rubble in the stair, cleared at stage 3 (m22.dungeon)."},
        {'id': 'link:cellar_lab', 'from': 'room:cellar', 'to': 'room:old_lab', 'kind': 'open'},
        {'id': 'link:lab_vaultdoor', 'from': 'room:old_lab', 'to': 'room:vault_door', 'kind': 'open'},
        {'id': 'link:vault', 'from': 'room:vault_door', 'to': 'room:sword_vault', 'kind': 'door', 'motion': 'slide',
         'condition': {'qbit': 'vault_opened'}, 'notes': "Password 'laboratory' (A3's m23.vault_door)."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Newcastle, the castle the bolt from the sky destroyed, bought as a ruin from Ebenezer and rebuilt in stages by the King's engineer Emerson. At first the party finds a roofless great hall full of rubble and wood golems grown out of the old beams, a floor broken into the foundation pit, and the dungeon stair choked with rubble. With the keep built the hall is the lord's, the smith and the training hall open; with the dungeon dug the chapel and the counting room open, YOUR well flows, and the stair leads down past a flooded cellar and the scientists' old laboratory to the sword vault, whose door wants a word.",
        'purpose': "The party's Cloudside home and its staged services (A4's houses 4141-4144); story M8 (the deed), M11 (the keep), M22 (the dungeon), M23 (the Xeen Slayer Sword behind the password 'laboratory'). Party 14-16 for stage 0, about 33-36 for stage 3 (D-4: a quiet stage 3).",
        'mood': "Stage 0: grey daylight through the broken roof, dust, rubble, timber. Stage 2: torchlight, banners. Below: cold brick, standing lagoon water, a hum behind a steel door.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [{'id': 'loop:pit', 'spaces': ['room:great_hall', 'room:foundation_pit', 'room:pantry'],
                   'closed_until': STAGE_KEEP,
                   'notes': "Stage 0-1: down through the hall's broken floor, up the rubble ramp into the pantry. Gone at stage 2."}],
        'entrances': [{'id': 'entrance:x3_site', 'space': 'room:gate', 'kind': 'both', 'facing': 'n',
                       'neighbour': 'exit:x3_site',
                       'how': "Inside the keep's gate, from X3's hatch at the Newcastle site (thing:xd13_stair); the gate leads back out."}],
        'critical_path': ['room:gate', 'room:great_hall', 'room:statue_court', 'room:stair_head', 'room:dungeon_stair',
                          'room:cellar', 'room:old_lab', 'room:vault_door', 'room:sword_vault'],
        'goals': [
            {'id': 'goal:sword', 'space': 'room:sword_vault', 'kind': 'take', 'story': 'M23',
             'what': "The Xeen Slayer Sword on the scientists' rack (A3's m23.sword).", 'gives': {'qbit': 'sword_done'}},
        ],
        'keys': [{'id': 'key:password', 'grants': {'qbit': 'vault_opened'}, 'found_in': 'room:old_lab',
                  'how': "The word 'laboratory': its five syllables on numbered notes (hall, pantry, court, cellar, laboratory); Crodo says it outright when freed (M21, autonote 4121)."}],
        'points_of_interest': [
            {'id': 'poi:well', 'space': 'room:statue_court', 'kind': 'well', 'condition': STAGE_DUNGEON,
             'behaviour': "Drink: every member's temporary armour class bonus raised to 20 until rest (D-4)",
             'notes': "YOUR well; dry and choked with rubble until stage 3."},
            {'id': 'poi:larder', 'space': 'room:pantry', 'kind': 'larder',
             'behaviour': "'Food. Fill pack?' Yes: the party's food at least 20."},
            {'id': 'poi:statue', 'space': 'room:statue_court', 'kind': 'statue',
             'behaviour': "The plaque: 'Built in honor of Great Adventurers.'"},
        ],
        'states': [
            {'id': 'state:stage0', 'condition': STAGE_RUIN,
             'shows': ['the fallen roof', 'rubble and the woodpile', 'the hole into the foundation pit',
                       'wood golems in the hall, court and pit'],
             'notes': "The deed is bought (m8.deed; X3's hatch lets the party in). Walls (m9.walls) change nothing inside."},
            {'id': 'state:stage2', 'condition': STAGE_KEEP,
             'hides': ['the wood golems', 'the rubble', 'the woodpile', 'the broken roof'],
             'opens': ['door:smithy', 'door:training'], 'seals': ['room:foundation_pit', 'room:rubble_ramp'],
             'notes': "m11.keep: the roof mended, the hole floored over (the pit's lift), the ramp walled up, banners and arms, the smith and the training hall."},
            {'id': 'state:stage3', 'condition': STAGE_DUNGEON,
             'shows': ['YOUR well', 'the swamp things and the iron golems below'],
             'opens': ['door:chapel', 'door:counting', 'link:stair_cellar'],
             'notes': "m22.dungeon: the stair dug out, the chapel and the bank open, the well flows."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 12, 'sectors': 12, 'monsters_about': 25, 'chests': 3, 'doors': 4, 'loops': 1,
                   'floor_area_munits2': 17.5},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors), staged. From the MU-6 graph devdocs/xeen/mockups/act2_graphs/xd13.graph.yml and D-4 (act2_dungeon_decisions.md, XD-13): stage 3 quiet (6 swamp things, 4 iron golems; 25 monsters over all stages), Crodo gives the word, numbered syllables, the services as house doors, YOUR well +20 AC until rest. The four services are house doors (A4's houses 4141-4144) in the gate and the court, not walk-in rooms; the dungeon stair is two rooms (the head with the rubble, the stair).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    else:                              # no rooms.yml yet: the house doors are named in words
        for st in doc['states']:
            if 'opens' in st:
                st['effects'] = [f"opens {o}" for o in st['opens'] if not o.startswith('link:')]
                st['opens'] = [o for o in st['opens'] if o.startswith('link:')] or None
                if st['opens'] is None:
                    del st['opens']
    return doc


DIAGRAM = """XD-13 Newcastle Keep (not to scale; north up). Stage 0 ruin -> stage 2 keep -> stage 3 dungeon.

  the keep, z 0
   [pantry]--door--[GREAT HALL]--arch--[STATUE COURT]==house doors: training (2), chapel (3), counting (3)
     ^ ramp          |  hole (0-1)        |  statue, YOUR well (3)
     |               |                  [stair head] =rubble (until 3)
   [gate]=smithy(2)--'                    |
   (X3: Newcastle site)                [dungeon stair]
  below, z -640                           |
   [foundation pit] (0-1, under the hall) [flooded cellar]--[old laboratory]--[vault door]=password=[SWORD VAULT]
"""

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:gate', 'at': [0, 320], 'facing': 90,
                    'notes': "Inside the keep's gate, facing the great hall (north): where X3's hatch (thing:xd13_stair) arrives."}
objects['exits'] = [
    {'id': 'exit:gate_door', 'room': 'room:gate', 'wall': 'south', 'size': [256, 320], 'surface': S('7solid01', 128, 256, fit=True),
     'to': 'exit:x3_site', 'notes': "The keep's gate out to X3's Newcastle site."}]
objects['doors'] = [
    {'id': 'door:pantry', 'opening': 'open:hall_pantry', 'kind': 'hinged', 'thickness': 16, 'surface': OAK_DOOR,
     'notes': "The pantry's oak door."},
    {'id': 'door:ramp_wall', 'opening': 'open:ramp_pantry', 'kind': 'slide_down', 'state': 'open', 'tile': True,
     'thickness': 32, 'speed': 400, 'surface': CHB1, 'back_surface': ROUGH,
     'notes': "Stage 2: the masonry Emerson's men lay across the ramp's mouth (sunk in the floor until then; the load "
              "event shuts it)."},
    {'id': 'door:stair_rubble', 'opening': 'open:stair_rubble', 'kind': 'slide_down', 'tile': True, 'thickness': 48,
     'speed': 400, 'surface': RUIN, 'back_surface': RUIN,
     'notes': "The rubble that chokes the dungeon stair until stage 3 (the load event sinks it)."},
    {'id': 'door:vault', 'opening': 'open:vault', 'kind': 'slide_left', 'thickness': 24, 'speed': 64,
     'surface': IRON, 'back_surface': IRON, 'notes': "The vault's steel door: opens to the word 'laboratory'."},
]
objects['lifts'] = [
    {'id': 'lift:pit_floor', 'room': 'room:foundation_pit', 'at': HOLE_AT, 'size': HOLE_SIZE, 'travel': 640,
     'speed': 2000, 'thickness': 32, 'surface': FLAGS,
     'notes': "Stage 2: the hole in the hall's floor floored over. Drawn down, it is the pit's floor under the hole; the "
              "load event raises it 640 so its top is the hall's floor."}]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 190, 120]
DAY = [200, 205, 215]
COLD = [170, 185, 210]
objects['lights'] = [
    light('light:gate', 'room:gate', [0, 384], 384, 1000, FIRE),
    light('light:hall_day', 'room:great_hall', [0, 2176], 132, 1800, DAY,  # over the rafter top (768) it stands on: z 900
          notes="Grey daylight through the fallen roof (off from stage 2)."),
    light('light:hall_w', 'room:great_hall', [-640, 1600], 560, 1200, FIRE),
    light('light:hall_e', 'room:great_hall', [640, 2560], 560, 1200, FIRE),
    light('light:hall_lord_w', 'room:great_hall', [-512, 2688], 600, 1300, FIRE, on=False,
          notes="Stage 2: the lord's hall is lit."),
    light('light:hall_lord_e', 'room:great_hall', [512, 1280], 600, 1300, FIRE, on=False),
    light('light:pantry', 'room:pantry', [-2048, 2944], 300, 900, FIRE),
    light('light:court_w', 'room:statue_court', [1700, 1728], 500, 1300, DAY),
    light('light:court_e', 'room:statue_court', [2700, 1900], 500, 1300, FIRE),
    light('light:stair_head', 'room:stair_head', [2528, 640], 300, 600, FIRE),
    light('light:stair', 'room:dungeon_stair', [2528, -500], 0, 700, COLD),
    light('light:pit', 'room:foundation_pit', [-960, 1600], 400, 1000, DAY,
          notes="Daylight falling through the hole."),
    light('light:ramp', 'room:rubble_ramp', [-2560, 1900], 0, 900, [220, 180, 140]),
    light('light:ramp_low', 'room:rubble_ramp', [-2176, 1408], 0, 700, [220, 180, 140]),
    light('light:cellar', 'room:cellar', [2560, -1984], 360, 1200, COLD),
    light('light:lab', 'room:old_lab', [960, -1920], 340, 1100, FIRE),
    light('light:vault_door', 'room:vault_door', [-256, -1920], 280, 700, [150, 170, 255],
          pulse={'intensity': [0.8, 1.0], 'frequency': 0.8}, notes="The door's hum."),
    light('light:vault', 'room:sword_vault', [-1216, -1920], 320, 900, [210, 220, 255]),
]
objects['chests'] = [
    {'id': 'chest:strongbox', 'room': 'room:foundation_pit', 'at': [-1520, 1960], 'treasure_level': 2,
     'random_items': 2, 'gold': 300, 'trap_level': 1,
     'notes': "The scientists' strongbox, fallen with the floor (stage 0-1 only)."},
    {'id': 'chest:lab', 'room': 'room:old_lab', 'at': [1550, -1400], 'facing': 'w', 'treasure_level': 2,
     'random_items': 2, 'gold': 400, 'trap_level': 2, 'notes': "The scientists' locker."},
    {'id': 'chest:vault', 'room': 'room:sword_vault', 'at': [-1550, -2320], 'facing': 'e', 'treasure_level': 3,
     'random_items': 2, 'gold': 800, 'trap_level': 2,
     'notes': "The vault's own hoard (the map's hoard, a level up); the sword is in its own box on the rack."},
    {'id': 'chest:sword', 'room': 'room:sword_vault', 'at': [-1216, -1488], 'floor_height': -640 + 160, 'facing': 'w',
     'kind': 'gt002', 'size': [192, 64, 56], 'random_items': 0, 'gold': 0, 'items': ['xeen_slayer_sword'],
     'notes': "The sword's long box on the scientists' rack, its front to the vault (south): the Xeen Slayer Sword is its "
              "item (D-90, 2026-11-22: a find in a container is a chest item); A3's m23.sword sets done, the autonote and "
              "10,000 experience after it opens."},
]
# A2's rows (assets_dev/worlds/xeen/source/monsters.yml): material golems block 11580 (A Wood Golem 18, C Iron Golem 40),
# swamp things block 11460 (B Bog Thing 26, C Marsh Horror 32). Placed, so every stage's count is exact (D-4).
WOOD, IRON_G, BOG, MARSH = 11580, 11582, 11461, 11462
G_RUIN, G_DUNGEON = 10, 30
monsters = []


def mon(id, rm, kind, at, facing, group, **kw):
    d = {'id': id, 'room': rm, 'monster': kind, 'at': at, 'facing': facing, 'hostile': True, 'group': group}
    if group == G_DUNGEON:
        d['hidden'] = True
    d.update(kw)
    monsters.append(d)


# D-130 (2026-11-24): 1-3 and 6 out of sight of the gate's landing (0, 320) (hide.py's spots; 1 north of the woodpile).
for n, at in enumerate([[-960, 2560], [-768, 2560], [704, 2432], [640, 2176], [-384, 1408], [448, 1600]], 1):
    mon(f'monster:hall_golem_{n}', 'room:great_hall', WOOD, at, 270, G_RUIN,
        notes="Stage 0-1: a wood golem grown out of the fallen roof timbers.")
for n, at in enumerate([[1664, 1216], [1664, 2240], [2688, 2240], [2688, 1600]], 1):
    mon(f'monster:court_golem_{n}', 'room:statue_court', WOOD, at, 180, G_RUIN)
for n, at in enumerate([[-1408, 1344], [-1408, 1856], [-576, 1280], [-448, 1920], [-960, 1856]], 1):
    mon(f'monster:pit_golem_{n}', 'room:foundation_pit', WOOD, at, 0, G_RUIN,
        notes="Stage 0-1: wood golems grown out of the old beams.")
for n, at in enumerate([[2176, -1408], [3072, -1408], [2176, -2304], [3072, -2304]], 1):
    mon(f'monster:cellar_bog_{n}', 'room:cellar', BOG, at, 90, G_DUNGEON,
        notes="Stage 3: a Bog Thing seeped in with the lagoon water (D-4).")
for n, at in enumerate([[2560, -1792], [2560, -2176]], 1):
    mon(f'monster:cellar_marsh_{n}', 'room:cellar', MARSH, at, 90, G_DUNGEON, floor_height=-680,
        notes="Stage 3: a Marsh Horror in the standing water (D-4).")
for n, at in enumerate([[640, -1792], [640, -2176]], 1):
    mon(f'monster:lab_golem_{n}', 'room:old_lab', IRON_G, at, 0, G_DUNGEON,
        notes="Stage 3: the scientists' iron golem (one group of four with the vault door's, D-4).")
for n, at in enumerate([[-128, -1824], [-128, -2016]], 1):
    mon(f'monster:vault_golem_{n}', 'room:vault_door', IRON_G, at, 0, G_DUNGEON,
        notes="Stage 3: an iron golem guarding the vault door.")
objects['monsters'] = monsters


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


def torch(id, rm, wall, along=None, **kw):
    x = {'id': id, 'room': rm, 'decoration': 'torch01', 'wall': wall, 'height': 176}
    if along is not None:
        x['along'] = along
    x.update(kw)
    return x


objects['decorations'] = [
    torch('deco:gate_torch_w', 'room:gate', 'north', 0.15),
    torch('deco:gate_torch_e', 'room:gate', 'north', 0.85),
    torch('deco:hall_torch_w', 'room:great_hall', 'west', 0.75),
    torch('deco:hall_torch_e', 'room:great_hall', 'east', 0.15),
    torch('deco:pantry_torch', 'room:pantry', 'north', 0.15),
    torch('deco:court_torch_s', 'room:statue_court', 'south', 0.6),  # lamp rule: 0.75 stood in the stair head's opening
    torch('deco:court_torch_w', 'room:statue_court', 'west', 0.9),
    torch('deco:stair_torch', 'room:stair_head', 'east'),
    torch('deco:cellar_torch', 'room:cellar', 'north', 0.15),
    torch('deco:lab_torch', 'room:old_lab', 'east', 0.2),
    torch('deco:vault_torch', 'room:sword_vault', 'east', 0.2),
    deco('deco:statue', 'room:statue_court', '7dec55', [2176, 1728], floor_height=48,
         notes="The statue of the Great Adventurers on its plinth."),
    # The pantry (a storeroom): sacks and barrels along the walls, the second syllable under a sack.
    deco('deco:sack_bo', 'room:pantry', 'floursac', [-2720, 3232], notes="The sack with the note 'bo' under it."),
    deco('deco:pantry_sack_2', 'room:pantry', 'bag01', [-2720, 3088]),
    deco('deco:pantry_sack_3', 'room:pantry', 'floursac', [-2592, 3232]),
    deco('deco:pantry_barrel_1', 'room:pantry', '7dec32', [-1408, 3232]),
    deco('deco:pantry_barrel_2', 'room:pantry', '7dec32', [-1536, 3232]),
    deco('deco:pantry_barrel_3', 'room:pantry', '7dec32', [-1664, 3232]),
    deco('deco:pantry_keg_1', 'room:pantry', 'smlbarel', [-2720, 2944]),
    deco('deco:pantry_keg_2', 'room:pantry', 'smlbarel', [-2464, 3232]),
    # The pit: the bones of the castle's last defenders, fallen with the floor.
    deco('deco:bones', 'room:foundation_pit', '7dec18', [-1536, 1600], notes="Bones (aaze0072:5)."),
    deco('deco:pit_skull', 'room:foundation_pit', '7dec20', [-384, 1280]),
    # The cellar: a pair of barrels against the north wall.
    deco('deco:cellar_barrel_1', 'room:cellar', '7dec32', [1920, -1280]),
    deco('deco:cellar_barrel_2', 'room:cellar', '7dec32', [2048, -1280]),
    # The laboratory: the cauldron in the north-west corner.
    deco('deco:lab_cauldron', 'room:old_lab', 'cauld00', [416, -1440], notes="The scientists' cauldron, cold."),
]
objects['sounds'] = [
    {'id': 'sound:drip', 'room': 'room:cellar', 'at': [2560, -1984], 'sound': 'drip02', 'radius': 1500,
     'wait': [3, 9], 'volume': 0.5, 'notes': "Water dripping into the flooded cellar."},
    {'id': 'sound:hum', 'room': 'room:vault_door', 'at': [-448, -1920], 'sound': 'humming', 'radius': 1600,
     'inner_radius': 400, 'volume': 0.5, 'notes': "The vault door hums (Emerson: NOT MY DEPARTMENT)."},
]

# ================================================================================================ wiring
QBITS = {'deed': 111160, 'walls': 111181, 'keep': 111221, 'dungeon': 111441, 'vault_opened': 111461,
         'sword_done': 111462}
RUBBLE = ['platform:rubble_ne', 'platform:rubble_se', 'platform:woodpile']
WELL_LUA = ("for _, i in ipairs(PartyMembers()) do evt.ForPlayer(i); "
            "if not IsAtLeast(ArmorClassBonus, 20) then SetValue(ArmorClassBonus, 20) end end")
FOOD_LUA = "if not IsAtLeast(Food, 20) then SetValue(Food, 20) end"
# Hidden actors still block the party (engine, 2026-11-20): the wood golems, dead or alive, are moved into the sealed
# foundation pit when they are hidden at stage 2. Actor indices follow objects.yml's monsters sorted by id (6-15 the
# court's and hall's golems, 18-22 the pit's); the build's order, checked by the playtest's actor_visible steps.
_PARK = [(x, y) for y in (1250, 1450, 1650, 1850, 1950) for x in (-1536, -1312, -1100)][:15]
PARK_LUA = ("local spots = {" + ", ".join(f"{{{x}, {y}}}" for x, y in _PARK) + "}; local ids = {6, 7, 8, 9, 10, 11, "
            "12, 13, 14, 15, 18, 19, 20, 21, 22}; for n, i in ipairs(ids) do evt.SetMapActorPosition(i, spots[n][1], "
            "spots[n][2], -640) end")
HOUSES = [('smithy', 4141, 'Newcastle Smithy', STAGE_KEEP,
           "A cold hearth under a missing roof. Emerson's chalk mark on the wall reads: SMITHY (KEEP)."),
          ('training', 4142, 'Newcastle Training Hall', STAGE_KEEP,
           "Rubble and an old practice dummy. Emerson's chalk mark reads: TRAINING (KEEP)."),
          ('chapel', 4143, 'Chapel of Newcastle', STAGE_DUNGEON,
           "An empty chapel with no altar. Emerson's chalk mark reads: CHAPEL (DUNGEON STAGE, DON'T ASK)."),
          ('counting', 4144, 'Newcastle Counting Room', STAGE_DUNGEON,
           "A bare room with an iron ring in the floor. Emerson's chalk mark reads: BANK (DUNGEON STAGE).")]

events = [
    # ---- arrival lines, one per stage
    {'id': 'evt:arrive_ruin', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True, 'condition': STAGE_RUIN,
     'effects': [{'message': "The ruins of Newcastle. Beyond the gate the great hall's roof has fallen in, and among the old timbers something heavy creaks and moves."}],
     'notes': "Stage 0-1 arrival (a one-shot timer, XD-07's method)."},
    {'id': 'evt:arrive_keep', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'all': [{'qbit': 'keep'}, {'not': {'qbit': 'dungeon'}}]},
     'effects': [{'message': "Newcastle Keep. Fresh mortar, a new roof, and Newcastle's banners over the hall. The smith and the master at arms have moved in."}]},
    {'id': 'evt:arrive_dungeon', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': STAGE_DUNGEON,
     'effects': [{'message': "Emerson's diggers have been and gone: the old dungeon stair beyond the statue court is open, the chapel and the counting room have their doors, and water stands in YOUR well."}]},
    # ---- the stages (load events)
    {'id': 'evt:stage_ruin', 'preset': 'script', 'trigger': 'load', 'condition': STAGE_RUIN,
     'effects': [{'hide': 'platform:roof_patch'}, {'passable': 'platform:roof_patch'}],
     'notes': "Stage 0-1: the roof is still open to the rafters (the built map holds the stage-2 patch)."},
    {'id': 'evt:stage_keep', 'preset': 'script', 'trigger': 'load', 'condition': STAGE_KEEP,
     'opens': ['lift:pit_floor'], 'closes': ['door:ramp_wall'],
     'effects': [{'hide_actors': G_RUIN}, {'show': 'platform:roof_patch'},
                 {'solid': 'platform:roof_patch'}]
                + [{'hide': p} for p in RUBBLE] + [{'passable': p} for p in RUBBLE]
                + [{'set_texture': {'of': 'panel:banner_w', 'to': BANNER}},
                   {'set_texture': {'of': 'panel:banner_e', 'to': BANNER}},
                   {'set_texture': {'of': 'panel:crest', 'to': CREST}},
                   {'set_texture': {'of': 'door:smithy', 'to': 'chb1dl'}},
                   {'set_texture': {'of': 'panel:sign_smithy', 'to': SIGNS['smithy']}},
                   {'set_texture': {'of': 'door:training', 'to': 'chb1dl'}},
                   {'set_texture': {'of': 'panel:sign_training', 'to': SIGNS['training']}},
                   {'lights_off': 'light:hall_day'},
                   {'lights_on': ['light:hall_lord_w', 'light:hall_lord_e']}],
     'notes': "Stage 2 (m11.keep): the wood golems gone, the hole floored over (the pit's lift up), the ramp walled up, "
              "the rubble and woodpile cleared, the roof mended (the patch stays), banners and arms, the smithy's and "
              "training hall's doors and signs."},
    {'id': 'evt:park_golems', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'condition': STAGE_KEEP,
     'effects': [{'lua': PARK_LUA}],
     'notes': "Stage 2: the hidden wood golems (dead or alive) are moved into the sealed foundation pit, since hidden "
              "actors still block the party (a load event runs before the actors can be moved, so a timer does it)."},
    {'id': 'evt:stage_dungeon', 'preset': 'script', 'trigger': 'load', 'condition': STAGE_DUNGEON,
     'opens': ['door:stair_rubble'],
     'effects': [{'show_actors': G_DUNGEON}, {'hide': 'platform:well_cap'}, {'passable': 'platform:well_cap'},
                 {'set_texture': {'of': 'door:chapel', 'to': 'chb1dl'}},
                 {'set_texture': {'of': 'panel:sign_chapel', 'to': SIGNS['chapel']}},
                 {'set_texture': {'of': 'door:counting', 'to': 'chb1dl'}},
                 {'set_texture': {'of': 'panel:sign_counting', 'to': SIGNS['counting']}}],
     'notes': "Stage 3 (m22.dungeon): the stair's rubble gone, the swamp things and iron golems below, the well "
              "flows, the chapel's and counting room's doors and signs."},
    {'id': 'evt:vault_state', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'vault_opened'},
     'opens': ['door:vault'], 'effects': [{'lua': '-- the vault stays open once its word was said'}],
     'notes': "Once opened, the vault stays open."},
    # ---- the way out
    {'id': 'evt:gate_door', 'preset': 'exit', 'source': 'exit:gate_door', 'title': "To the Newcastle site",
     'notes': "Out to X3's Newcastle site, in front of the hatch (A5's arrival, facing south)."},
    # ---- the house doors (A4's towns/xd13.yml)
]
for key, house, name, cond, closed in HOUSES:
    events.append({'id': f'evt:{key}', 'preset': 'script', 'source': f'door:{key}', 'title': name, 'condition': cond,
                   'effects': [{'lua': f'evt.EnterHouse({house})'}], 'else_effects': [{'message': closed}],
                   'notes': f"A4's house {house} ({name}), opens on {'m11.keep' if cond is STAGE_KEEP else 'm22.dungeon'}; "
                            "its closed text before."})
for pid in ('panel:sign_smithy', 'panel:sign_training', 'panel:sign_chapel', 'panel:sign_counting'):
    key = pid.split('_', 1)[1]
    events.append({'id': f'evt:{pid.split(":")[1]}', 'preset': 'script', 'source': pid,
                   'title': dict((h[0], h[2]) for h in HOUSES)[key],
                   'effects': [{'text': dict((h[0], h[2]) for h in HOUSES)[key]}]})
events += [
    {'id': 'evt:crest', 'preset': 'script', 'source': 'panel:crest', 'title': "Arms of Newcastle",
     'condition': STAGE_KEEP, 'effects': [{'text': "A white tower on blue: the arms of Newcastle. Yours."}],
     'else_effects': [{'text': "A patch of fallen facing stone where a coat of arms once hung."}]},
    {'id': 'evt:pantry_door', 'preset': 'door', 'source': 'door:pantry', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:ramp_wall', 'preset': 'text', 'source': 'door:ramp_wall', 'title': 'New masonry',
     'text': "Fresh masonry closes the old rubble slope. Emerson's men left a chalk mark: FILLED IN (KEEP)."},
    # ---- the ruin's dressing (aaze0072:1, 3, 5)
    {'id': 'evt:woodpile', 'preset': 'text', 'source': 'platform:woodpile', 'title': 'Woodpile',
     'text': "Woodpile: the old roof's beams, sawn and stacked. Some of the stack has arms.",
     'notes': "Original label (aaze0072:1)."},
    {'id': 'evt:rubble_ne', 'preset': 'text', 'source': 'platform:rubble_ne', 'title': 'Rubble',
     'text': "Rubble: fallen roof stone.", 'notes': "Original label (aaze0072:3)."},
    {'id': 'evt:rubble_se', 'preset': 'text', 'source': 'platform:rubble_se', 'title': 'Rubble',
     'text': "Rubble: fallen roof stone."},
    {'id': 'evt:bones', 'preset': 'text', 'source': 'deco:bones', 'title': 'Bones',
     'text': "Bones: whoever stood in the hall when the bolt struck.", 'notes': "Original label (aaze0072:5)."},
    # ---- the five syllables (A3's hooks; D-4 numbers them)
    {'id': 'evt:la', 'preset': 'script', 'source': 'panel:la', 'title': 'Scratches',
     'effects': [{'lua': 'XeenQuests.hook("m23.syllable_la")'}], 'notes': "Syllable 1 (aaze0073:1)."},
    {'id': 'evt:bo', 'preset': 'script', 'source': 'deco:sack_bo', 'title': 'Sack',
     'effects': [{'lua': 'XeenQuests.hook("m23.syllable_bo")'}], 'notes': "Syllable 2 under a sack (aaze0073:4)."},
    {'id': 'evt:ra', 'preset': 'script', 'source': 'panel:ra', 'title': 'Scratches',
     'effects': [{'lua': 'XeenQuests.hook("m23.syllable_ra")'}], 'notes': "Syllable 3 by the stair (aaze0073:2)."},
    {'id': 'evt:to', 'preset': 'script', 'source': 'platform:shelf', 'title': 'Shelf',
     'effects': [{'lua': 'XeenQuests.hook("m23.syllable_to")'}], 'notes': "Syllable 4 on a shelf (aaze0074:0)."},
    {'id': 'evt:ry', 'preset': 'script', 'source': 'panel:ry', 'title': 'Scratches',
     'effects': [{'lua': 'XeenQuests.hook("m23.syllable_ry")'}], 'notes': "Syllable 5 before the vault (aaze0074:1)."},
    # ---- the pantry, the statue, the well
    {'id': 'evt:larder', 'preset': 'script', 'source': 'platform:larder', 'title': 'Larder',
     'question': {'ask': 'Fill pack (Yes/No)?', 'answers': ['Yes', 'Y'], 'message': "Food.  Fill pack?"},
     'effects': [{'lua': FOOD_LUA}, {'text': "You fill your packs from the larder."}],
     'notes': "The source's line (aaze0073:0): the party's food raised to 20, any number of times."},
    {'id': 'evt:statue', 'preset': 'text', 'source': 'platform:statue_plinth', 'title': 'Plaque',
     'text': "A plaque at the base of the statue reads: Built in honor of Great Adventurers.", 'window': True,
     'notes': "Original line (aaze0073:3)."},
    {'id': 'evt:well', 'preset': 'script', 'source': 'platform:well', 'title': 'YOUR well',
     'condition': STAGE_DUNGEON,
     'effects': [{'lua': WELL_LUA}, {'text': "Even your well's water is cool and refreshing. (Armour class +20 until you rest.)"}],
     'else_effects': [{'text': "YOUR well. Dry, and choked with rubble: the diggers have not reached it yet."}],
     'notes': "D-4: +20 AC temporary, raised to 20 if lower, until rest; free and repeatable. Original lines aaze0073:8, 9."},
    {'id': 'evt:well_cap', 'preset': 'script', 'source': 'platform:well_cap', 'title': 'YOUR well',
     'effects': [{'text': "YOUR well. Dry, and choked with rubble: the diggers have not reached it yet."}]},
    # ---- the dungeon stair
    {'id': 'evt:stair_rubble', 'preset': 'script', 'source': 'door:stair_rubble', 'title': 'Rubble',
     'condition': {'not': STAGE_DUNGEON}, 'locked_text': "The way down is clear now.",
     'effects': [{'message': "A short distance down the stairs you find the way blocked with rubble. You are unable to continue down, so you come back up."}],
     'notes': "Original line (aaze0073:7); the load event clears the rubble at stage 3."},
    {'id': 'evt:cellar_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:cellar', 'once': True,
     'text': "Lagoon water has seeped into the old cellar and stands black between the walls. Something in it breathes.",
     'seconds': 6},
    {'id': 'evt:notebooks', 'preset': 'text', 'source': 'platform:workbench', 'title': 'Notebooks',
     'text': "The scientists' notebooks, swollen with damp. One page survives: 'Blade tempered. Edge holds against the undead sample. Do NOT tell the castle. Password changed to something we will all remember.'",
     'window': True},
    # ---- the vault
    {'id': 'evt:vault_door', 'preset': 'script', 'source': 'door:vault', 'title': 'Vault door',
     'condition': {'not': {'qbit': 'vault_opened'}},
     'question': {'ask': 'What is the password?', 'answers': ['laboratory'],
                  'wrong_text': "Incorrect! The door hums a little louder. Nothing else happens."},
     'opens': ['door:vault'], 'effects': [{'lua': 'XeenQuests.hook("m23.vault_door")'}],
     'else_effects': [{'lua': 'XeenQuests.hook("m23.vault_door")'}],
     'notes': "A3's m23.vault_door on the right answer (sets vault_opened 111461, its text) and the door slides open. "
              "The source's 'What is the password?' / 'Incorrect!' (aaze0073:15, 16); the wrong answer's line is "
              "A3's m23.vault_wrong text (a question's wrong answer runs no effects)."},
    {'id': 'evt:grille', 'preset': 'text', 'source': 'platform:grille', 'title': 'Speaking grille',
     'text': "A brass grille in the wall beside the steel door. When you lean close, a dry voice asks: \"What is the password?\""},
    {'id': 'evt:pedestal', 'preset': 'text', 'source': 'platform:pedestal', 'title': 'Pedestal',
     'text': "The pedestal is cool to the touch.", 'notes': "Original line (aaze0073:12)."},
    {'id': 'evt:sword', 'preset': 'chest', 'source': 'chest:sword', 'title': 'Chest',
     'effects': [{'lua': 'XeenQuests.hook("m23.sword")'}],
     'notes': "goal:sword (D-90): the Xeen Slayer Sword 12500 is the box's item; A3's m23.sword (once) sets done 111462, "
              "autonote 4123 and 10,000 experience on the status line. The vault door is the gate."},
]
for name, eid in [('chest:strongbox', 'evt:chest_strongbox'), ('chest:lab', 'evt:chest_lab'),
                  ('chest:vault', 'evt:chest_vault')]:
    events.append({'id': eid, 'preset': 'chest', 'source': name, 'title': 'Chest'})
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd13', 'name': 'Newcastle Keep', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'XD-13', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [13, 12], 'climbs': 'n'},
    'map_stats': {'id': 9128, 'encounter_chance': 0, 'treasure_level': 2, 'trap_dice': 1,
                  'perception_difficulty': 2, 'refill_days': 672, 'music': 49, 'environment': 'stone hall',
                  'lock_difficulty': 2, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Golem', 'tier': 0, 'per_marker': [1, 2], 'weight': 60},
                            {'monster': 'Xeen Swamp Thing', 'tier': 1, 'per_marker': [1, 2], 'weight': 40}]},
    'neighbours': [
        {'id': 'exit:x3_site', 'to': X3_STEM, 'kind': 'door', 'arrival': X3_ARRIVAL,
         'arrival_hint': "On X3's Newcastle site, 400 south of the keep's hatch (thing:xd13_stair), facing away from it.",
         'direction': 270,
         'notes': "A5's points (briefs/x3/DOORS.md). X3's hatch leads in to this map's start (0, 320, 0) facing north."}],
    'qbits': QBITS,
    'items': {'xeen_slayer_sword': 12500},
    'notes': "Xeen design brief, level L4: XD-13 Newcastle Keep (staged), the party's castle on X3 (story M8, M9, M11, "
             "M22, M23; QUESTS 4.1). Built as stage 0; load events make stage 2 (m11.keep 111221) and stage 3 "
             "(m22.dungeon 111441). Monsters placed (A2's rows): 15 Wood Golems 11580 (group 10, stage 0-1), 4 Bog Things "
             "11461 and 2 Marsh Horrors 11462 and 4 Iron Golems 11582 (group 30, stage 3; D-4). Slots for the map card: "
             "1 Xeen Golem, 2 Xeen Swamp Thing (no spawn points; no rest encounters in the party's own castle). A3's "
             "quest bits by name; the map's own block 110800-110839 is unused (its once-flags are map variables). "
             "Hooks m23.syllable_la/bo/ra/to/ry, m23.vault_door, m23.sword. A4's houses 4141-4144 as house doors. Music "
             "49. The gate leads out to X3 (A5's arrival).",
}


# ------------------------------------------------------------------------------------------------ D-89 identity
# What makes XD-13 read as the party's own staged castle (D-89, reviews/DESIGN_GATING_AND_IDENTITY.md 2.2; lane A7 s27,
# 2026-11-22): at stage 0 the great hall is Castle Harmondale's ruin (7d29): a base course and a string course of
# squared stone (chb1s), the cobble (chb1) to 384 and above it the smoke-blackened, broken ruin stone (ch1b1); the roof
# fallen in over a broken hole open to the sky (a lantern 128 thick, its edge the broken ruin stone) over the bare tie
# beams; a breach in the north-east corner where the wall fell, rubble heaped outside it against the sky; rubble
# mounds sloping up to the corners (platforms with sloped tops, hidden at stage 2); a fallen rafter. Stage 2 (m11.keep)
# closes the roof (the patch, the hole's own shape), bricks up the breach (a plug of chb1 shown behind it) and clears
# the rubble. Stage 3: a working laboratory (benches of glass, candles and crystals, a green alchemist's glow) and a
# heavy riveted steel vault door of two leaves in an iron frame.
CHB1S_COURSE = S('chb1s', 128, 256)     # chb1s's squared course at its top: a band hangs from its top
SKYFACE = dict(BOARDS, sky=True)
themes.append({'id': 'theme:keep_hall', 'wall': RUIN, 'floor': FLAGS, 'ceiling': CEIL, 'door': OAK_DOOR,
               'reveal': CHB1,
               'notes': "The great hall: Castle Harmondale's ruin stone (ch1b1) above its string course (D-89)."})
themes.append({'id': 'theme:open_sky', 'wall': SKYFACE, 'floor': RUIN, 'ceiling': SKYFACE, 'door': RUIN,
               'reveal': RUIN, 'notes': "Outside the breach (seen, never walked): the open sky over the fallen rubble."})
ROOMS = {r['id']: r for r in rooms}
hall = ROOMS['room:great_hall']
hall['theme'] = 'theme:keep_hall'
hall['bands'] = [{'height': 64, 'surface': CHB1S_COURSE}, {'height': 384, 'surface': CHB1},
                 {'height': 448, 'surface': CHB1S_COURSE}]
for _rid in ('room:gate', 'room:statue_court'):
    ROOMS[_rid]['bands'] = [{'height': 64, 'surface': CHB1S_COURSE}]


def ccw(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if a > 0 else pts[::-1]


def ccw_first(pts, hs):
    """Counter-clockwise, keeping the first point (the heap's peak, where the top's triangles fan from) first."""
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    if a > 0:
        return pts, hs
    return [pts[0]] + pts[:0:-1], [hs[0]] + hs[:0:-1]


# The roof's broken hole over the hall's middle, open to the sky (the lantern 128 thick).
ROOF_HOLE = ccw([[-416, 1856], [-224, 1760], [-64, 1840], [160, 1760], [416, 1824], [512, 2000], [448, 2176],
                 [544, 2336], [480, 2496], [224, 2464], [64, 2592], [-160, 2496], [-416, 2528], [-544, 2400],
                 [-480, 2240], [-576, 2048]])   # clear of the floor's hole into the pit and of the golems' places
hall['ceiling_levels'] = [{'outline': ROOF_HOLE, 'ceiling': 896, 'surface': SKYFACE, 'edge': RUIN,
                           'notes': "Where the roof fell in: a broken hole open to the sky over the bare tie beams "
                                    "(D-22.6, D-89); the stage-2 roof patch closes it."}]
_plats = [p for p in hall['platforms'] if p.get('id') not in ('platform:rubble_ne', 'platform:rubble_se')]
for p in _plats:
    if p.get('id') == 'platform:roof_patch':
        for k in ('at', 'size'):
            p.pop(k, None)
        p['outline'] = ROOF_HOLE
_ne, _ne_h = ccw_first([[1152, 3072], [512, 3072], [512, 2816], [800, 2560], [1152, 2624]], [144, 48, 0, 0, 0])
_se, _se_h = ccw_first([[1152, 896], [1152, 1344], [832, 1280], [704, 896]], [112, 0, 0, 0])
_plats += [
    {'id': 'platform:rubble_ne', 'outline': _ne, 'rise': 0, 'top_heights': _ne_h, 'surface': RUIN, 'top_surface': RUIN,
     'notes': "Rubble: the fallen corner's stone heaped up to the breach (gone at stage 2)."},
    {'id': 'platform:rubble_se', 'outline': _se, 'rise': 0, 'top_heights': _se_h, 'surface': RUIN, 'top_surface': RUIN,
     'notes': "Rubble heaped into the south-east corner (gone at stage 2)."},
    {'id': 'platform:fallen_rafter', 'outline': ccw([[-96, 2048], [256, 2304], [232, 2336], [-120, 2080]]), 'rise': 32,
     'surface': BOARDS, 'top_surface': BOARDS, 'notes': "A rafter fallen with the roof, lying where it landed (gone at "
                                                         "stage 2)."},
]
hall['platforms'] = _plats
RUBBLE.append('platform:fallen_rafter')
light_by = {l['id']: l for l in objects['lights']}
light_by['light:hall_day']['height'] = 64      # over the roof patch's top (768): z 832, inside the 128 of roof
# The breach in the north wall's east end: the corner fell outward; rubble heaped outside it under the open sky.
BREACH = (608, 3200, 1120, 3456)
RECTS['room:breach'] = BREACH
# F58/F60 (the player's pin XD-13 p1, 2026-11-25, "z-fighting": a flat white face beside a pillar): the breach's walls
# were sky from the floor up, and from the heap (a jump from the rubble) the sky below the eye drew as the preset's
# flat fog. The fallen corner's own walls now stand in ruin stone to 352 over the heap's top (BREACH_WALL), the sky
# only above them and overhead (tools/xeen/check_parapet_gaps.py `sky.low`).
BREACH_WALL = 832   # 80 over the stage-2 plug's top (752) too
room('room:breach', 'The breach', BREACH, floor=0, ceiling=1024, theme='theme:open_sky', ambient=18, steep_floor=True,
     space='room:great_hall', bands=[{'height': BREACH_WALL, 'surface': RUIN}],
     platforms=[block('platform:breach_ledge', [864, 3248], [512, 96], 224, RUIN, RUIN,
                      "The fallen stone level with the breach's sill."),
                block('platform:breach_heap', [864, 3376], [512, 160], 224, dict(RUIN, uneven=True), dict(RUIN, uneven=True),
                      "The heap of fallen stone rising away under the sky.", top_slope={'to': 480, 'toward': 'north'}),
                block('platform:breach_plug', [864, 3248], [512, 96], 528, CHB1, CHB1,
                      "Stage 2: Emerson's masonry closing the breach (hidden while the keep is unbuilt).", base=224)],
     notes="Outside the breach in the hall's north wall (seen, never walked): the fallen corner's rubble heaped under "
           "the open sky. Stage 2 bricks it up.")
op('open:hall_breach', 'room:great_hall', 'room:breach', width=384, height=320, sill=224, shape='gable', apex=448,
   reveal=RUIN, notes="The breach: a jagged gap where the hall's north-east corner fell, 224 over the floor.")
for e in events:
    if e['id'] == 'evt:stage_ruin':
        e['effects'] += [{'hide': 'platform:breach_plug'}, {'passable': 'platform:breach_plug'}]
        e['notes'] += " The breach stays open (its plug hidden)."
    if e['id'] == 'evt:stage_keep':
        e['effects'] += [{'hide': 'platform:fallen_rafter'}, {'passable': 'platform:fallen_rafter'},
                         {'show': 'platform:breach_plug'}, {'solid': 'platform:breach_plug'}]
        e['notes'] += " The fallen rafter cleared; the breach bricked up (the plug stays)."
# The laboratory at work (stage 3): benches of glass and brass along the south wall, glassware, candles and a crystal
# on them, a green alchemist's glow; the steel vault door heavy: two riveted leaves in an iron frame, 320 wide.
lab = ROOMS['room:old_lab']
lab['platforms'] += [block('platform:bench_w', [448, -2496], [256, 96], 88, CABS, BOARDS,
                           "A bench of glassware against the south wall."),
                     block('platform:bench_e', [1472, -2496], [256, 96], 88, CABS, BOARDS,
                           "A bench of glassware against the south wall.")]
for o in openings:
    if o['id'] == 'open:vault':
        o.update(width=320, height=320, reveal=S('t5d1', 128, 256))
for d in objects['doors']:
    if d['id'] == 'door:vault':
        d.update(thickness=48, leaves=2, pictures=[[S('t5d1', 128, 256)] * 2], back_pictures=[[S('t5d1', 128, 256)] * 2], notes="The vault's heavy steel door: two riveted leaves in an iron frame that "
                                               "part to the word 'laboratory'.")
LABTOP = -640 + 88
objects['decorations'] += [
    deco('deco:lab_glass_1', 'room:old_lab', 'dec35', [384, -2496], floor_height=LABTOP),
    deco('deco:lab_glass_2', 'room:old_lab', 'dec35', [512, -2480], floor_height=LABTOP),
    deco('deco:lab_candle_w', 'room:old_lab', 'cndlab0', [448, -2520], floor_height=LABTOP),
    deco('deco:lab_goblet', 'room:old_lab', '7dec46', [1408, -2496], floor_height=LABTOP),
    deco('deco:lab_crystal', 'room:old_lab', 'crystl0', [1536, -2496], floor_height=LABTOP,
         notes="A glowing crystal the scientists were cutting."),
    deco('deco:lab_glass_3', 'room:old_lab', 'dec35', [800, -2464], floor_height=-640 + 72),
    deco('deco:lab_candle_c', 'room:old_lab', 'cndlab0', [1120, -2464], floor_height=-640 + 72),
]
objects['lights'].append(light('light:breach_day', 'room:breach', [864, 3360], 320, 900, DAY,
                               notes="Daylight on the fallen stone outside the breach."))
objects['lights'].append(light('light:lab_glow', 'room:old_lab', [960, -2400], 160, 700, [120, 255, 150],
                               pulse={'intensity': [0.85, 1.0], 'frequency': 0.5},
                               notes="The alchemist's green glow over the benches."))
project['identity'] = {
    'shape': 'castle', 'family': '7d29',
    'seen': ["Castle Harmondale's ruin: the great hall's roof fallen in on the sky, a breach in its corner and rubble "
             "heaped up the walls, wood golems among the beams",
             "the keep mended by stages: Newcastle's banners and arms, the chalk marks turned to shop signs, the "
             "breach bricked up and the roof closed",
             "the scientists' laboratory at work below, and the heavy steel vault door that wants a word"]}


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
        p['notes'] = f"Xeen design brief, level {lv}: XD-13 Newcastle Keep (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-13 Newcastle Keep, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

# D-22.6: the sky over the hall's fallen roof, X3's day preset (worlds/xeen/rendering/sky/sky.yml: xeen_x3.odm
# swamp); no daylight block, no weather (Frosgard City's one-room case).
atmosphere = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'swamp'},
              'notes': "Stage 0-1: the great hall's fallen roof is open to X3's sky (its sky faces); the rest of the "
                       "keep is lit by its own lights. From stage 2 the roof patch closes it."}
write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM),
                     ('atmosphere.yml', atmosphere)])
print('written L4')
