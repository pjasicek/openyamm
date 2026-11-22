#!/usr/bin/env python3
"""XD-21 Rivercity Robbers' Den, L4 (and L3's rooms.yml): writes rooms.yml, objects.yml, wiring.yml and project.yml
of devdocs/xeen/briefs/xd21/L4 from the plan below. Rerun after every change here (v.sh); never hand-edit the
written files while this generator is in use.

Frame: x east, y north, z up; the quay door (the X2 exit) in the south wall at y 0; heights from the quay cellar's
floor. The great bridge runs east-west over the undercroft; the race (a mill race taken off the river) runs
north-south under it, in through the sluice chamber's river grate, out through the undercroft's south grate."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd21'
SHELL_ONLY = '--l3' in sys.argv          # L3: rooms.yml only (the shell), into L3
L4 = BRIEF / ('L3' if SHELL_ONLY else 'L4')


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# One family: MM7 The Erathian Sewers (d01.blv, "Thief guild and sewers"): Steadwick's thieves under the city's
# streets, damp brick and stone, slimy water, plank doors with trim. Measured with texture_use.py --map mm7/d01.blv.
BRICK = S('wall', 128, 256)          # d01's commonest wall: small dark brick
STONE = S('twb2', 128, 256)          # d01's big dressed stone blocks (the bridge's piers and the quay wall)
FLAGS = S('cfb1', 128, 128)          # d01's rough wet floor
SLAB = S('7tfb11', 128, 128)         # the Wine Cellar's grey flags: the strongroom's dart slabs
TILES = S('tfb07', 128, 128)         # d01's big brown flagstones: the robbers' rooms
ROUGH = S('cwb', 128, 256)           # d01's rough stone (vault ceilings)
DOOR = S('7trimda', 256, 128)        # the Tidewater Caverns' and Wine Cellar's weathered planks (MM7): the den's plank doors


def PLANKPAIR():
    """The den's plank doors (F12, A8 session 26): a sliding pair (each leaf into its jamb) of MM7's weathered
    Z-braced plank wings (hhm1d | hhm1d2, the grey of the den's 7trimda planks), each leaf 128 of the 256 opening,
    instead of the plank strip laid across (a hinged pair's open leaves lay their edges on the walls: 8 coplanar
    warnings)."""
    return [[S('hhm1d', 128, 256), S('hhm1d2', 128, 256)]]
TRIM = S('7trim9_32', 32, 64)        # d01's door trim
POST = S('wordwal2', 32, 128)        # d01's wooden post strip
WATER = S('7slimywtr', 128, 128, liquid='water')   # d01's water (MM7 slime water, the liquid shader)
GRILLE = S('xngrille', 128, 256)     # the Xeen dungeons' generated iron grille (XD-02's hoist gate), a cut-out
WOOD = S('7trimda', 256, 128)        # weathered planks (MM7 Tidewater Caverns 7d17, Wine Cellar 7d16): tables, bunks, crates, the bridge
WOODTOP = S('7t1books1', 128, 128)   # the Wine Cellar's dark furniture wood: table tops
LINEN = S('7t1beds2', 128, 256)      # the Wine Cellar's bed linen: the bunks' blankets

themes = [
    {'id': 'theme:brick', 'wall': BRICK, 'floor': TILES, 'ceiling': BRICK, 'door': DOOR, 'reveal': TRIM,
     'notes': "The robbers' rooms: d01's brick walls (wall), flagstone floors (cfb1), rough stone vaults (cwb), its plank doors (twb1a) and trim."},
    {'id': 'theme:stone', 'wall': STONE, 'floor': FLAGS, 'ceiling': STONE, 'door': DOOR, 'reveal': TRIM,
     'notes': "The bridge's own masonry (the quay cellar, the undercroft, the sluice chamber): d01's big dressed blocks (twb2)."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def octagon(cx, cy, r):
    k = round(r * math.tan(math.pi / 8))
    return [[cx - k, cy - r], [cx + k, cy - r], [cx + r, cy - k], [cx + r, cy + k], [cx + k, cy + r], [cx - k, cy + r],
            [cx - r, cy + k], [cx - r, cy - k]]


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


def SILL(x, y, length, notes):
    """The stone sill between a wall and the end of a sunken race or basin (48 deep, 48 high)."""
    return {'at': [x, y], 'size': [length, 48], 'rise': 48, 'surface': STONE, 'top_surface': FLAGS, 'notes': notes}


def GRATE_PANEL(id, size, notes, bottom=0):
    """A round iron culvert grate set in the wall (MM6 Free Haven Sewer's d1lggrt: bars over darkness)."""
    return {'id': id, 'at': 'centre', 'length': size, 'bottom': bottom, 'height': size,
            'surface': S('d1lggrt', 256, 256, fit=True), 'notes': notes}


def GRATE(x, y, length, rise, notes):
    """An iron grille (xngrille, a cut-out) 48 deep, filling the strip between a wall and a sunken race or basin."""
    return {'at': [x, y], 'size': [length, 48], 'rise': rise, 'surface': GRILLE,
            'end_surface': S('twb2', 128, 256, fit=False), 'top_surface': STONE, 'notes': notes}


def table(at, size, h=72, top=WOODTOP, side=WOOD, notes='Table'):
    return {'at': at, 'size': size, 'rise': h, 'surface': side, 'top_surface': top, 'notes': notes}


# ------------------------------------------------------------------------------------------------ the way in
room('room:quay_cellar', 'Quay cellar', outline=rect(-3200, 0, -1920, 1024), floor=0, ceiling=448,
     theme='theme:stone', ambient=20,
     ceiling_levels=[{'ceiling': 576, 'top_scale': [0, 1], 'notes': "A low barrel vault east-west under the quay."}],
     levels=[{'id': 'level:drain', 'outline': rect(-2272, 48, -1952, 416), 'floor': -96, 'surface': WATER,
              'edge': STONE, 'notes': "The drain basin: river water lapping in under the quay wall."}],
     parapets=[{'path': [[-2288, 32], [-2288, 432], [-1936, 432]], 'height': 48, 'thickness': 16, 'surface': STONE, 'notes': "The basin's kerb."}],
     platforms=[SILL(-2112, 24, 320, "The basin's sill against the quay wall.")],
     walls=[{'wall': 'south', 'panels': [{'id': 'panel:drain_grate', 'offset': 960, 'length': 256, 'bottom': 0, 'height': 256, 'surface': S('d1lggrt', 256, 256, fit=True), 'notes': "The drain grate over the basin (MM6 Free Haven Sewer's round culvert grate): the river comes in under the quay through it."}]}],
     notes="A disused cellar behind Rivercity's south quay wall, 1,280 by 1,024 under a low barrel vault: the quay door (the X2 exit) in the south wall, the river lapping into a drain basin in the south-east corner through a low grate. It looks like a dead end; wet footprints lead to the north wall.")
room('room:crawl', "Robbers' crawl", path=[[-2560, 1152], [-2560, 2304], [-2560, 3456]], width=320,
     floor=0, ceiling=288, theme='theme:brick', ambient=24,
     notes="The hidden way: a brick passage 256 wide and 2,300 long behind the cellar's secret block, a tripwire halfway along.")

# ------------------------------------------------------------------------------------------------ the den
room('room:dicing_room', 'Dicing room', outline=rect(-3200, 3584, -1664, 4864), floor=0, ceiling=448,
     theme='theme:brick', ambient=18,
     ceiling_levels=[{'ceiling': 576, 'top_scale': [1, 0], 'notes': "Brick barrel vault north-south."}],
     platforms=[
         {'id': 'platform:dice_table', 'at': [-2944, 3968], 'size': [384, 224], 'rise': 72, 'surface': WOOD,
          'top_surface': WOODTOP, 'notes': "The dicing table, plank on trestles, in the south-west of the room (off the ways between the three doors): dice, cups and coins on it."},
         table([-2944, 4192], [320, 64], 40, notes='Bench'),
         table([-2944, 3744], [320, 64], 40, notes='Bench'),
         table([-1856, 3776], [192, 96], 64, notes='Side table (the lamp)'),
     ],
     walls=[{'wall': 'west', 'panels': [{'id': 'panel:dues_box', 'offset': 336, 'length': 96, 'bottom': 112,
                                         'height': 96, 'surface': S('7gt002c', 64, 64, fit=True),
                                         'notes': "The gang's dues box nailed to the wall, its slot scratched round with words."}]}],
     notes="The robbers' common room, 1,536 by 1,280: a plank dicing table with benches in the south-west, kegs and a barrel in the north corners, the dues box on the west wall north of the table. Arches east into the undercroft; a door north to the bunks.")
room('room:bunk_room', 'Bunk room', outline=rect(-3200, 5120, -1664, 6144), floor=0, ceiling=416,
     theme='theme:brick', ambient=22,
     platforms=[
         {'id': 'platform:bunk_1', 'at': [-3072, 5376], 'size': [192, 384], 'rise': 48, 'surface': WOOD, 'top_surface': LINEN, 'notes': 'Bunk'},
         {'id': 'platform:bunk_2', 'at': [-3072, 5888], 'size': [192, 384], 'rise': 48, 'surface': WOOD, 'top_surface': LINEN, 'notes': 'Bunk'},
         {'id': 'platform:bunk_3', 'at': [-2560, 6016], 'size': [384, 192], 'rise': 48, 'surface': WOOD, 'top_surface': LINEN, 'notes': 'Bunk'},
         {'id': 'platform:bunk_4', 'at': [-2048, 6016], 'size': [384, 192], 'rise': 48, 'surface': WOOD, 'top_surface': LINEN, 'notes': 'Bunk'},
     ],
     walls=[{'wall': 'north', 'panels': [{'id': 'panel:loose_stone', 'offset': 160, 'length': 64, 'bottom': 32,
                                          'height': 64, 'surface': BRICK, 'secret': True,
                                          'notes': "A loose brick low in the north wall behind the bunks: somebody's purse (secret)."}]}],
     notes="Bunks of planks round the walls, 1,536 by 1,024, the robbers asleep; a loose brick behind one bunk hides a purse.")

# ------------------------------------------------------------------------------------------------ under the bridge
RACE_W = 256           # half the race's width
UNDER = rect(-1408, 3072, 1408, 4864)
room('room:undercroft', 'Undercroft of the great bridge', outline=UNDER, floor=0, ceiling=640,
     theme='theme:stone', ambient=18,
     ceiling_levels=[{'ceiling': 1088, 'top_scale': [0, 1], 'notes': "The bridge's great arch: a barrel vault east-west from 640 at the walls to 1,088 at the crown."}],
     levels=[{'id': 'level:race_under', 'outline': rect(-RACE_W, 3072 + 48, RACE_W, 4864 - 48), 'floor': -224, 'surface': WATER,
              'edge': STONE, 'notes': "The race: river water 224 below the floor, flowing north to south under the bridge."}],
     flights=[{'from': [RACE_W - 32, 3248], 'to': [-RACE_W, 3248], 'from_height': -224, 'to_height': 0, 'width': 192,
               'steps': 7, 'riser': STONE, 'tread': FLAGS,
               'notes': "Water stairs: seven steps up out of the race onto the west bank, at its south end (the way out for anyone who falls in)."}],
     platforms=[
         {'id': 'platform:winch', 'at': [576, 3712], 'size': [96, 96], 'rise': 160, 'surface': WOOD, 'top_surface': WOODTOP,
          'notes': "The bridge winch's post on the east bank, its lever facing the race."},
         {'at': [-1216, 3264], 'size': [256, 256], 'rise': 640, 'surface': STONE, 'top_surface': STONE, 'notes': 'Pier buttress, south-west'},
         {'at': [1216, 3264], 'size': [256, 256], 'rise': 640, 'surface': STONE, 'top_surface': STONE, 'notes': 'Pier buttress, south-east'},
         {'at': [-1216, 4672], 'size': [256, 256], 'rise': 640, 'surface': STONE, 'top_surface': STONE, 'notes': 'Pier buttress, north-west'},
         {'at': [1216, 4672], 'size': [256, 256], 'rise': 640, 'surface': STONE, 'top_surface': STONE, 'notes': 'Pier buttress, north-east'},
         SILL(0, 3072 + 24, 2 * RACE_W, "The sill where the race runs out under the south wall."),
         SILL(0, 4864 - 24, 2 * RACE_W, "The sill where the race comes in under the north wall."),
     ],
     walls=[{'wall': 'south', 'panels': [GRATE_PANEL('panel:race_out', 384, "The race's outfall grate: the water runs on under the quay into the dark.")]},
            {'wall': 'north', 'panels': [GRATE_PANEL('panel:race_in', 384, "The grate where the race comes in from the sluice chamber.")]}],
     notes="The set piece: the hollow of the great bridge's south abutment, 2,816 by 1,792 under one tall barrel arch, four pier buttresses in its corners. The race cuts it north to south, 512 wide and 224 down, through grates at either end; the robbers keep their plank bridge drawn back to the east bank, its winch beside it. The dicing room opens on the west bank; the boss's stair and the sluice chamber's door on the east.")
room('room:sluice', 'Sluice chamber', outline=rect(-1408, 5120, 768, 6144), floor=0, ceiling=512,
     theme='theme:stone', ambient=18,
     ceiling_levels=[{'ceiling': 704, 'top_scale': [1, 0], 'notes': "Barrel vault north-south over the race."}],
     levels=[{'id': 'level:race_sluice', 'outline': rect(-RACE_W, 5120 + 48, RACE_W, 6144 - 48), 'floor': -224, 'surface': WATER,
              'edge': STONE, 'notes': "The race where it comes in from the river."}],
     platforms=[
         {'id': 'platform:catwalk', 'at': [0, 5760], 'size': [2 * RACE_W, 160], 'rise': 224,
          'surface': STONE, 'top_surface': WOODTOP, 'notes': "The sluice wall across the race, planked on top: the catwalk."},
         {'at': [0, 5688], 'size': [2 * RACE_W, 16], 'base': 224, 'rise': 48, 'surface': WOOD, 'top_surface': WOOD, 'notes': 'Catwalk rail, south'},
         {'at': [0, 5832], 'size': [2 * RACE_W, 16], 'base': 224, 'rise': 48, 'surface': WOOD, 'top_surface': WOOD, 'notes': 'Catwalk rail, north'},
         SILL(0, 6144 - 24, 2 * RACE_W, "The sill under the river grate."),
         SILL(0, 5120 + 24, 2 * RACE_W, "The sill where the race runs on south into the undercroft."),
     ],
     walls=[{'wall': 'north', 'panels': [GRATE_PANEL('panel:river_grate', 512, "The river grate: the race pours in from the Great River through iron bars.")]},
            {'wall': 'south', 'panels': [GRATE_PANEL('panel:race_down', 384, "The grate where the race runs on south under the wall into the undercroft.")]}],
     notes="Where the race is taken off the river: a vaulted chamber 2,176 by 1,024, the race pouring in through the tall river grate in the north wall and crossed by the old sluice wall, planked over as a catwalk. The bunk room's door on the west; on the east bank an arch south into the undercroft and the fence's locked door.")
room('room:fence_store', "Fence's store", outline=rect(1024, 5120, 2048, 6144), floor=0, ceiling=384,
     theme='theme:brick', ambient=20,
     store=True,  # D-7 (2026-11-20): the fence's store is a storeroom (its barrel and sacks stand together in a corner)
     platforms=[
         table([1856, 5888], [256, 128], 64, notes='Counting table'),
         {'at': [1232, 5232], 'size': [192, 192], 'rise': 128, 'surface': WOOD, 'top_surface': WOODTOP, 'notes': 'Crate of stolen goods'},
         {'at': [1232, 5232], 'size': [128, 128], 'rise': 96, 'base': 128, 'surface': WOOD, 'top_surface': WOODTOP, 'notes': 'Crate on the crate'},
         {'at': [1480, 5216], 'size': [256, 128], 'rise': 96, 'surface': WOOD, 'top_surface': WOODTOP, 'notes': 'Crate'},
     ],
     notes="The fence's store behind a good lock: crates and sacks of goods stolen in Rivercity, a counting table, the fence's chest.")

# ------------------------------------------------------------------------------------------------ the boss's wing
room('room:boss_stair', "Boss's stair", outline=rect(1664, 3712, 2944, 4224), floor=0,
     slope={'to': 256, 'toward': 'east', 'steps': 8, 'tread': FLAGS, 'riser': STONE}, ceiling=448,
     ceiling_slope={'to': 704, 'toward': 'east'}, theme='theme:brick', ambient=20,
     notes="Eight steps of 32 up east from the undercroft's east arch to the boss's door.")
room('room:boss_quarters', "Robber Boss's quarters", outline=rect(3200, 3328, 4608, 4608), floor=256, ceiling=832,
     theme='theme:brick', ambient=16,
     ceiling_levels=[{'ceiling': 960, 'top_scale': [1, 0], 'notes': "Barrel vault north-south."}],
     platforms=[
         {'id': 'platform:desk', 'at': [4352, 3968], 'size': [128, 320], 'rise': 72, 'surface': WOOD, 'top_surface': WOODTOP,
          'notes': "The boss's desk: his ledger open on it."},
         {'id': 'platform:hearth', 'at': [3392, 4544], 'size': [320, 128], 'rise': 32, 'surface': STONE, 'top_surface': FLAGS,
          'notes': "The hearth against the north wall, west of the strongroom passage."},
         {'at': [3392, 3520], 'size': [256, 384], 'rise': 56, 'surface': WOOD, 'top_surface': WOODTOP, 'notes': "The boss's bed"},
         table([4096, 3520], [256, 192], 72, notes='Supper table'),
     ],
     notes="The boss's own rooms, 1,408 by 1,280 and 256 up: a desk with his ledger, a bed with his chest beside it, a supper table in the south-east, a hearth on the north wall west of the strongroom passage with the catch between them; the passage leaves the north wall.")
room('room:strongroom_walk', 'Strongroom passage', path=[[3904, 4736], [3904, 5376], [3904, 6016]], width=320,
     floor=256, ceiling=576, theme='theme:stone', ambient=22,
     notes="A straight stone passage 1,280 long to the vault: three slabs in its floor fire darts from the walls unless the catch in the boss's room is thrown.")
room('room:vault', 'Vault', outline=rect(3456, 6144, 4352, 6912), floor=256, ceiling=704,
     theme='theme:stone', ambient=20,
     ceiling_levels=[{'ceiling': 800, 'top_scale': [0, 1]}],
     platforms=[{'id': 'platform:plinth', 'at': [3904, 6656], 'size': [256, 192], 'rise': 32, 'surface': STONE,
                 'top_surface': SLAB, 'notes': "The plinth the strongbox stands on."}],
     notes="The gang's strongroom, 896 by 768 behind an iron door with three locks: the strongbox with Princess Roxanne's tiara on a plinth, the gang's takings stacked round it.")

# ------------------------------------------------------------------------------------------------ openings
op('open:secret', 'room:quay_cellar', 'room:crawl', link='link:cellar_crawl', width=256, height=256,
   notes="The secret block in the cellar's north wall.")
op('open:den', 'room:crawl', 'room:dicing_room', link='link:crawl_dicing', width=256, height=256)
op('open:dicing_under', 'room:dicing_room', 'room:undercroft', link='link:dicing_undercroft', width=448, height=384,
   reveal=STONE)
op('open:bunks', 'room:dicing_room', 'room:bunk_room', link='link:dicing_bunks', width=256, height=256)
op('open:sluice_door', 'room:bunk_room', 'room:sluice', link='link:bunks_sluice', width=256, height=256)
op('open:sluice_under', 'room:sluice', 'room:undercroft', link='link:sluice_undercroft', width=320, height=384,
   along=0.85, reveal=STONE, notes="East of the race: from the sluice chamber's east bank down into the undercroft's east half.")
op('open:fence', 'room:sluice', 'room:fence_store', link='link:sluice_fence', width=256, height=256)
op('open:stair', 'room:undercroft', 'room:boss_stair', link='link:undercroft_stair', width=384, height=384, reveal=STONE)
op('open:boss', 'room:boss_stair', 'room:boss_quarters', link='link:stair_boss', width=256, height=256)
op('open:strongroom', 'room:boss_quarters', 'room:strongroom_walk', link='link:boss_strongroom', width=256, height=288)
op('open:vault', 'room:strongroom_walk', 'room:vault', link='link:strongroom_vault', width=256, height=256)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:brick', 'ambient': 16}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-21 Robbers' Den at L4: the den in the south abutment of Rivercity's great bridge (x east, y north; the quay door at y 0; heights from the cellar's floor). Written by output/studio_cal/xd21/tools/gen.py."}

if SHELL_ONLY:
    # L3: the shell only, without the objects' platforms that need ids for wiring kept (they are part of the shell).
    L4.mkdir(parents=True, exist_ok=True)
    (L4 / 'rooms.yml').write_text(yaml.safe_dump(rooms_doc, sort_keys=False, allow_unicode=True, width=120))
    print('written L3 rooms')
    sys.exit(0)

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:quay_cellar', 'at': [-2560, 320], 'facing': 90,
                    'notes': "Just inside the quay door, facing in (north)."}
objects['doors'] = [
    {'id': 'door:secret', 'opening': 'open:secret', 'kind': 'slide_left', 'secret': True, 'tile': True, 'thickness': 32, 'speed': 80,
     'surface': STONE, 'back_surface': BRICK,
     'notes': "The hidden way in: a block of the cellar's own dressed stone that slides aside (secret: pulses for a party with the Perception to see it)."},
    {'id': 'door:den', 'opening': 'open:den', 'kind': 'slide_left', 'leaves': 2, 'pictures': PLANKPAIR(), 'back_pictures': PLANKPAIR(), 'notes': "The plank door at the head of the crawl (d01's door)."},
    {'id': 'door:bunks', 'opening': 'open:bunks', 'kind': 'slide_left', 'leaves': 2, 'pictures': PLANKPAIR(), 'back_pictures': PLANKPAIR()},
    {'id': 'door:sluice', 'opening': 'open:sluice_door', 'kind': 'slide_left', 'leaves': 2, 'pictures': PLANKPAIR(), 'back_pictures': PLANKPAIR()},
    {'id': 'door:fence', 'opening': 'open:fence', 'kind': 'slide_left', 'leaves': 2, 'pictures': PLANKPAIR(), 'back_pictures': PLANKPAIR(), 'notes': "The fence's locked door."},
    {'id': 'door:boss', 'opening': 'open:boss', 'kind': 'slide_left', 'leaves': 2, 'pictures': PLANKPAIR(), 'back_pictures': PLANKPAIR()},
    {'id': 'door:vault', 'opening': 'open:vault', 'kind': 'slide_up', 'thickness': 24, 'speed': 60,
     'fold': True, 'tile': True, 'surface': S('xwiron', 128, 256),
     'notes': "The vault's iron door (XD-04's generated studded iron, xwiron): three locks, the boss's ring of keys."},
]
objects['movers'] = [
    {'id': 'mover:drawbridge', 'room': 'room:undercroft', 'at': [392, 3968], 'size': [256, 256], 'bottom': -14,
     'height': 16, 'travel': [-2 * RACE_W - 8, 0, 0], 'stretch': True, 'speed': 128, 'surface': WOOD, 'top_surface': WOODTOP,
     'kerbs': {'height': 24, 'width': 16},
     'notes': "The robbers' plank bridge, drawn back onto the east bank; the winch runs it out across the race to the west bank."},
]
objects['plates'] = [
    {'id': 'plate:tripwire', 'room': 'room:crawl', 'at': [-2560, 2304], 'size': [288, 32], 'secret': True,
     'notes': "The tripwire across the crawl (secret: pulses for a perceptive party)."},
    {'id': 'plate:dart_1', 'room': 'room:strongroom_walk', 'at': [3904, 5056], 'size': [288, 192], 'surface': SLAB, 'secret': True},
    {'id': 'plate:dart_2', 'room': 'room:strongroom_walk', 'at': [3904, 5440], 'size': [288, 192], 'surface': SLAB, 'secret': True},
    {'id': 'plate:dart_3', 'room': 'room:strongroom_walk', 'at': [3904, 5824], 'size': [288, 192], 'surface': SLAB, 'secret': True},
    {'id': 'plate:footprints', 'room': 'room:quay_cellar', 'at': [-2560, 832], 'size': [384, 192],
     'notes': "Where the wet footprints end at the north wall (the clue's step event; drawn as the floor)."},
]
objects['switches'] = [
    {'id': 'switch:winch', 'room': 'room:undercroft', 'kind': 'lever', 'block': 'platform:winch', 'side': 'w',
     'height': 112, 'reach': 48, 'size': [12, 40], 'base': WOOD,
     'notes': "The bridge winch's lever on its post, facing the race."},
    {'id': 'switch:catch', 'room': 'room:boss_quarters', 'kind': 'lever', 'at': [3680, 4608], 'height': 130,
     'reach': 56, 'size': [16, 64], 'base': S('7trim9_32', 32, 64),
     'notes': "The strongroom catch: a lever on the north wall between the hearth and the passage."},
]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 170, 90]
DAY = [190, 210, 230]
lights = [
    light('light:quay_door', 'room:quay_cellar', [-2560, 120], 200, 525, DAY, notes="Grey daylight round the quay door."),
    light('light:drain', 'room:quay_cellar', [-2112, 220], 40, 450, [140, 190, 170], pulse={'intensity': [0.7, 1.0], 'frequency': 0.3},
          notes="Light off the water in the drain basin."),
    light('light:crawl', 'room:crawl', [-2560, 3200], 200, 450, FIRE),
    light('light:dice_lamp', 'room:dicing_room', [-2944, 3968], 200, 900, FIRE, pulse={'intensity': [0.8, 1.0], 'frequency': 1.1},
          notes="Candles on the dicing table."),
    light('light:dicing_side', 'room:dicing_room', [-1856, 3776], 180, 525, FIRE),
    light('light:bunks', 'room:bunk_room', [-2432, 5632], 160, 675, [230, 150, 80]),
    light('light:under_w', 'room:undercroft', [-1000, 3968], 300, 1050, FIRE),
    light('light:under_e', 'room:undercroft', [1000, 3968], 300, 1050, FIRE),
    light('light:race', 'room:undercroft', [0, 3968], -100, 825, [120, 180, 170], pulse={'intensity': [0.7, 1.0], 'frequency': 0.25},
          notes="The race's water, catching the torchlight."),
    light('light:sluice_day', 'room:sluice', [0, 6040], 300, 1125, DAY, notes="Daylight through the river grate."),
    light('light:sluice_w', 'room:sluice', [-1000, 5632], 250, 600, FIRE),
    light('light:fence', 'room:fence_store', [1856, 5888], 200, 675, FIRE),
    light('light:stair', 'room:boss_stair', [2300, 3968], 300, 525, FIRE),
    light('light:hearth', 'room:boss_quarters', [3392, 4500], 60, 900, [255, 140, 60], pulse={'intensity': [0.75, 1.0], 'frequency': 1.3}),
    light('light:boss_desk', 'room:boss_quarters', [4352, 3968], 140, 600, FIRE),
    light('light:strongroom', 'room:strongroom_walk', [3904, 5440], 200, 525, [200, 160, 110]),
    light('light:vault', 'room:vault', [3904, 6528], 300, 675, [255, 220, 150], notes="A lamp over the strongbox."),
]
objects['lights'] = lights

objects['chests'] = [
    {'id': 'chest:fence', 'room': 'room:fence_store', 'at': [1856, 5280], 'facing': 'n', 'kind': '7gt002',
     'treasure_level': 2, 'random_items': 2, 'gold': 350, 'trap_level': 2,
     'notes': "The fence's chest: takings and two stolen pieces (trapped)."},
    {'id': 'chest:boss', 'room': 'room:boss_quarters', 'at': [3600, 3440], 'kind': '7gt002',
     'treasure_level': 2, 'random_items': 2, 'gold': 400, 'trap_level': 2,
     'notes': "The boss's own chest beside his bed (trapped), clear of the door."},
    {'id': 'chest:vault', 'room': 'room:vault', 'at': [3904, 6656], 'facing': 's', 'kind': '7gt002',
     'floor_height': 288, 'treasure_level': 3, 'random_items': 2, 'gold': 800, 'items': ['roxannes_tiara'],
     'trap_level': 3, 'notes': "The gang's strongbox: the gang's takings (the map's hoard, one level up; trapped) and Princess Roxanne's tiara, an ordinary chest item (F15, 2026-11-21: quest items are looted, MM6-MM8 style; A3's q-c3.vault map_gives it)."},
]

# Xeen rows (A2, devdocs/xeen/lanes/A2.md "Rows for the map lanes"; NOTES.md "Rebase, phase 0"): slot 1 Outlaws
# (Xeen Outlaw: A Rogue 11110 level 12, B Thief 11111 level 18), slot 2 Evil rangers (Xeen Ranger: B Evil Ranger 11131
# level 12, the robbers' crossbowmen where they shoot across the race). Every marker carries its tier. One of the
# dicing room's two markers went at the rebase (kill experience inside 15 % of MAPS 0).
objects['spawns'] = [
    {'id': 'spawn:dicing_1', 'room': 'room:dicing_room', 'at': [-2800, 4450], 'slot': 1, 'tier': 'a',
     'notes': "Rogues at the dicing table."},
    {'id': 'spawn:under_w', 'room': 'room:undercroft', 'at': [-800, 4400], 'slot': 2, 'tier': 'b',
     'notes': "Evil rangers on the west bank: crossbows across the race."},
    {'id': 'spawn:under_e', 'room': 'room:undercroft', 'at': [800, 4400], 'slot': 1, 'tier': 'a',
     'notes': "Rogues on the east bank."},
    {'id': 'spawn:bunks_1', 'room': 'room:bunk_room', 'at': [-2700, 5500], 'slot': 1, 'tier': 'a', 'notes': "Asleep."},
    {'id': 'spawn:bunks_2', 'room': 'room:bunk_room', 'at': [-2100, 5700], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:sluice', 'room': 'room:sluice', 'at': [-800, 5600], 'slot': 2, 'tier': 'b',
     'notes': "Evil rangers guarding the catwalk."},
    {'id': 'spawn:fence', 'room': 'room:fence_store', 'at': [1500, 5700], 'slot': 1, 'tier': 'a',
     'notes': "The fence's men."},
    {'id': 'spawn:stair', 'room': 'room:boss_stair', 'at': [1900, 3968], 'slot': 2, 'tier': 'b',
     'notes': "Evil rangers at the foot of the boss's stair."},
    {'id': 'spawn:boss', 'room': 'room:boss_quarters', 'at': [3700, 3700], 'slot': 1, 'tier': 'b',
     'notes': "Thieves, the boss's lieutenants."},
]
objects['monsters'] = [
    {'id': 'monster:robber_boss', 'room': 'room:boss_quarters', 'monster': 11113, 'at': [4100, 4000], 'facing': 180,
     'hostile': True, 'group': 2, 'carries': 'ring_of_keys',
     'notes': "The Robber Boss: the world's boss row 11113 (level 22, boss hit points; the row is named Robber Boss, so the scene names nothing). He carries the vault's ring of keys."},
    {'id': 'monster:bodyguard_1', 'room': 'room:boss_quarters', 'monster': 11111, 'at': [3600, 4300], 'facing': 180,
     'hostile': True, 'group': 2, 'notes': "A bodyguard: an Outlaws Thief (11111, level 18)."},
    {'id': 'monster:bodyguard_2', 'room': 'room:boss_quarters', 'monster': 11111, 'at': [3600, 3700], 'facing': 180,
     'hostile': True, 'group': 2, 'notes': "The second bodyguard."},
]
# Relations: the world's own (assets_dev/worlds/xeen/relations.yml, A2) make the Outlaws (11110-11113) and the Evil
# rangers (11130-11132) the party's foes and leave the two families at peace with each other, so the map says none.


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


def torch(id, rm, at, wall, **kw):
    return deco(id, rm, 'torch01', at, wall=wall, height=160, **kw)


decos = [
    # quay cellar
    deco('deco:cellar_barrel', 'room:quay_cellar', 'bigbarel', [-3050, 150]),
    deco('deco:cellar_trash', 'room:quay_cellar', '7dec10', [-3000, 800]),
    deco('deco:cellar_bucket', 'room:quay_cellar', 'Bucket', [-2016, 504]),  # D-7 (2026-11-20): from mid-floor (480 from a wall) to the east wall by the basin's kerb
    torch('deco:cellar_torch', 'room:quay_cellar', [-2900, 0], 'south'),
    # crawl
    torch('deco:crawl_torch', 'room:crawl', [-2688, 3200], 'west'),
    deco('deco:crawl_bones', 'room:crawl', 'dec29', [-2470, 1700]),
    # dicing room
    torch('deco:dicing_torch_w', 'room:dicing_room', [-3200, 3900], 'west'),
    torch('deco:dicing_torch_n', 'room:dicing_room', [-2000, 4864], 'north'),
    deco('deco:dice_candle_1', 'room:dicing_room', 'cndlab0', [-3072, 3968], floor_height=72),
    deco('deco:dice_goblet_1', 'room:dicing_room', '7dec46', [-2862, 4024], floor_height=72),
    deco('deco:dice_goblet_2', 'room:dicing_room', '7dec48', [-2794, 3924], floor_height=72),
    deco('deco:dice_plate', 'room:dicing_room', 'dec36', [-3094, 3904], floor_height=72),
    deco('deco:side_candle', 'room:dicing_room', 'cndlab0', [-1856, 3776], floor_height=64),
    deco('deco:dicing_keg_1', 'room:dicing_room', 'smlbarel', [-3100, 4760]),
    deco('deco:dicing_keg_2', 'room:dicing_room', 'smlbarel', [-2990, 4770]),
    deco('deco:dicing_cask', 'room:dicing_room', '7dec21', [-1880, 4800]),
    deco('deco:dicing_barrel', 'room:dicing_room', '7dec32', [-1740, 4790]),
    # bunks
    deco('deco:bunk_sack_1', 'room:bunk_room', 'bag01', [-2900, 5190]),
    deco('deco:bunk_bowl', 'room:bunk_room', 'foodbowl', [-2870, 5300]),
    deco('deco:bunk_trash', 'room:bunk_room', 'trasheap', [-1800, 5250]),
    deco('deco:bunk_candle', 'room:bunk_room', 'dec02', [-2432, 5632]),
    # undercroft
    torch('deco:under_torch_sw', 'room:undercroft', [-700, 3072], 'south'),
    torch('deco:under_torch_se', 'room:undercroft', [700, 3072], 'south'),
    torch('deco:under_torch_nw', 'room:undercroft', [-700, 4864], 'north'),
    torch('deco:under_torch_ne', 'room:undercroft', [700, 4864], 'north'),
    deco('deco:under_barrels_1', 'room:undercroft', 'bigbarel', [-900, 3250]),
    deco('deco:under_barrels_2', 'room:undercroft', '7dec32', [-780, 3220]),
    deco('deco:under_sacks', 'room:undercroft', 'floursac', [900, 3300]),
    deco('deco:under_bag', 'room:undercroft', 'bag_A', [1000, 3250]),
    deco('deco:under_trash', 'room:undercroft', '7dec01', [-1000, 4600]),
    deco('deco:under_crate_cask', 'room:undercroft', '7dec21', [900, 4650]),
    # sluice
    torch('deco:sluice_torch_w', 'room:sluice', [-1408, 5500], 'west'),
    torch('deco:sluice_torch_e', 'room:sluice', [768, 5500], 'east'),
    deco('deco:sluice_trash', 'room:sluice', '7dec10', [-1100, 6000]),
    # fence store
    deco('deco:fence_sack_1', 'room:fence_store', 'floursac', [1250, 6040]),
    deco('deco:fence_sack_2', 'room:fence_store', 'bag01', [1350, 6020]),
    deco('deco:fence_bag', 'room:fence_store', 'bag_A', [1950, 5500]),
    deco('deco:fence_barrel', 'room:fence_store', 'bigbarel', [1130, 6070]),
    deco('deco:fence_candle', 'room:fence_store', 'cndlab0', [1856, 5888], floor_height=64),
    deco('deco:fence_plates', 'room:fence_store', 'dec39', [1800, 5880], floor_height=64),
    # stair
    torch('deco:stair_torch', 'room:boss_stair', [2300, 4224], 'north'),
    # boss quarters
    deco('deco:boss_fire', 'room:boss_quarters', 'ckfyr00', [3392, 4544], floor_height=288),
    torch('deco:boss_torch_w', 'room:boss_quarters', [3200, 4100], 'west'),
    torch('deco:boss_torch_e', 'room:boss_quarters', [4608, 3600], 'east'),
    deco('deco:boss_desk_candle', 'room:boss_quarters', 'cndlab0', [4352, 4060], floor_height=328),
    deco('deco:boss_goblet', 'room:boss_quarters', '7dec46', [4096, 3520], floor_height=328),
    deco('deco:boss_fruit', 'room:boss_quarters', '7dec08', [4036, 3496], floor_height=328),
    deco('deco:boss_cask', 'room:boss_quarters', '7dec21', [4500, 3400]),
    # lights audit (merge point 14): hung from the barrel vault's crown (960), not its springing (832); its top 2 into
    # the vault (127 high, drawn 39 down)
    deco('deco:boss_chandelier', 'room:boss_quarters', 'dec27', [3904, 3968], hangs=True, height=618),
    # strongroom passage
    torch('deco:strong_torch', 'room:strongroom_walk', [3744, 5632], 'west'),
    deco('deco:strong_corpse', 'room:strongroom_walk', 'Corpse03', [4000, 5480],
         notes="A robber who forgot the catch."),
    # vault
    torch('deco:vault_torch_w', 'room:vault', [3456, 6528], 'west'),
    torch('deco:vault_torch_e', 'room:vault', [4352, 6528], 'east'),
    deco('deco:vault_bag_1', 'room:vault', 'bag01', [3600, 6800]),
    deco('deco:vault_bag_2', 'room:vault', 'bag_A', [4200, 6800]),
    deco('deco:vault_barrel', 'room:vault', '7dec32', [4270, 6420]),
]
objects['decorations'] = decos
objects['sounds'] = [
    {'id': 'sound:drain', 'room': 'room:quay_cellar', 'at': [-2112, 64], 'sound': 'water lapping loop', 'radius': 2200,
     'inner_radius': 500, 'volume': 0.7, 'notes': "The river lapping at the drain grate."},
    {'id': 'sound:crawl_drip', 'room': 'room:crawl', 'at': [-2560, 2000], 'sound': 'drip02', 'radius': 1200,
     'wait': [3, 9], 'volume': 0.6},
    {'id': 'sound:river', 'room': 'room:sluice', 'at': [0, 6100], 'sound': 'rushing water loop', 'radius': 5000,
     'inner_radius': 1200, 'volume': 0.9, 'notes': "The river pouring in through the grate: heard through the undercroft."},
    {'id': 'sound:race_out', 'room': 'room:undercroft', 'at': [0, 3120], 'sound': 'rushing water loop', 'radius': 2600,
     'inner_radius': 600, 'volume': 0.5, 'notes': "The race running out through its grate."},
    {'id': 'sound:vault_drip', 'room': 'room:vault', 'at': [3904, 6300], 'sound': 'drip01', 'radius': 1000,
     'wait': [4, 12], 'volume': 0.5},
]
objects['exits'] = [
    {'id': 'exit:quay', 'room': 'room:quay_cellar', 'at': [-2560, 0], 'size': [256, 256],
     'surface': S('7solid01', 256, 128, uneven=True), 'to': 'door:xd21',
     'notes': "The quay door: the way out onto Rivercity's south quay under the great bridge (X2)."},
]
# F14 (feedback 2026-11-21): ladders out of the race and the quay drain, so a party that drops in climbs back.
objects['ladders'] = [
    {'id': 'ladder:drain', 'room': 'room:quay_cellar', 'at': [-2112, 400], 'facing': 'n', 'height': 96,
     'exit': [-2112, 480], 'grab_at_top': True, 'surface': {'texture': 'bemv', 'size': [32, 256], 'uneven': True},
     'notes': "F14: rungs out of the quay drain's basin."},
    {'id': 'ladder:race_sluice', 'room': 'room:sluice', 'at': [248, 6000], 'facing': 'e', 'height': 224,
     'exit': [352, 6000], 'grab_at_top': True, 'surface': {'texture': 'bemv', 'size': [32, 256], 'uneven': True},
     'notes': "F14: iron rungs up the race's east wall, so a party in the race climbs back onto the bank."},
    {'id': 'ladder:race_under', 'room': 'room:undercroft', 'at': [248, 4400], 'facing': 'e', 'height': 224,
     'exit': [352, 4400], 'grab_at_top': True, 'surface': {'texture': 'bemv', 'size': [32, 256], 'uneven': True},
     'notes': "F14: iron rungs up the race's east wall under the bridge."},
]
objects['placeholders'] = [
    {'id': 'placeholder:dice', 'room': 'room:dicing_room', 'stands_for': "Dice and cups on the dicing table",
     'at': [-2944, 3968], 'size': [96, 64, 16]},
]

# ================================================================================================ wiring
var = lambda n: {'map_var': n}
events = [
    # Hooks and dressing, D-7 (2026-11-20): the arrival window on the first arrival only (qbit arrived_once 110304)
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'not': {'qbit': 'arrived_once'}},
     'effects': [{'lua': 'XeenQuests.hook("q-c3.arrival")'}, {'qbit': 'arrived_once'}],
     'notes': "A3's hook q-c3.arrival (its window; a one-shot timer: a load event's window is not shown), on the first arrival only (arrived_once)."},
    {'id': 'evt:exit_quay', 'preset': 'exit', 'source': 'exit:quay', 'title': 'Quay door'},
    {'id': 'evt:footprints', 'preset': 'text', 'trigger': 'step', 'source': 'plate:footprints', 'once': True,
     'text': "Wet footprints lead from the drain to the north wall and stop dead at the stones. One block is cleaner than the rest, worn smooth by hands.",
     'seconds': 6, 'notes': "The clue to the hidden way in."},
    {'id': 'evt:secret_door', 'preset': 'door', 'source': 'door:secret', 'title': 'Worn block', 'action': 'open',
     'sets': {'qbit': 'robbers_den_found'},
     'text': "You push the worn block: it slides aside on greased runners. A brick passage runs north into the dark.",
     'notes': "link:cellar_crawl: the hidden way in. A3's hook q-c3.secret_door has no call: the map sets robbers_den_found itself."},
    {'id': 'evt:tripwire', 'preset': 'script', 'source': 'plate:tripwire', 'trigger': 'step', 'once': True,
     'effects': [{'damage': {'amount': 12, 'kind': 'physical', 'who': 'current'}}],
     'text': "A tripwire! A crossbow bolt whips out of the wall.",
     'notes': "set:tripwire: once."},
    {'id': 'evt:den_door', 'preset': 'door', 'source': 'door:den', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:bunks_door', 'preset': 'door', 'source': 'door:bunks', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:sluice_door', 'preset': 'door', 'source': 'door:sluice', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:boss_door', 'preset': 'door', 'source': 'door:boss', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:fence_door', 'preset': 'door', 'source': 'door:fence', 'title': "Fence's door", 'action': 'open',
     'condition': {'any': [{'item': 'ring_of_keys'}, {'stat': {'name': 'DisarmTrapSkill', 'at_least': 3}}]},
     'locked_text': "Locked: a good lock from Rivercity Smithing. A thief who can disarm traps (skill 3) could pick it; the boss's keys would open it.",
     'text': "The lock gives with a click.",
     'notes': "link:sluice_fence: the boss's ring of keys or a thief's skill (Disarm Traps 3, the game's skill for Xeen's Thievery)."},
    {'id': 'evt:dues_box', 'preset': 'text', 'source': 'panel:dues_box', 'title': 'Dues box',
     'text': "The gang's dues box. Empty. Scratched beside the slot: WHAT DID YOU EXPECT, MONEY?",
     'notes': "Original line, Rivercity (aaze0030 #33)."},
    {'id': 'evt:dicing_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:dicing_room', 'once': True,
     'text': "Scratched over the dicing table: NOW THIS IS A WILD TOWN.",
     'notes': "Original line, Rivercity's tavern (aaze0030 #23)."},
]
for n in range(1, 5):
    events.append({'id': f'evt:bunk_{n}', 'preset': 'text', 'source': f'platform:bunk_{n}', 'title': 'Bed',
                   'text': "There is nothing on, in, or under the bed.",
                   'notes': "Original line, Rivercity (aaze0030 #24)."})
events += [
    {'id': 'evt:loose_stone', 'preset': 'script', 'source': 'panel:loose_stone', 'title': 'Loose brick',
     'condition': {'not': {'map_var': 'purse_taken'}},
     'effects': [{'set': {'var': var('purse_taken'), 'value': 1}}, {'add': {'var': 'Gold', 'value': 150}}],
     'text': "Behind the loose brick: a robber's purse. 150 gold.",
     'else_effects': [{'text': "An empty hole behind a loose brick."}]},
    {'id': 'evt:undercroft_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:undercroft', 'once': True,
     'text': "You stand inside the great bridge. Carts rumble overhead; the race runs dark and fast beneath. The robbers' plank bridge is drawn back to the far bank.",
     'seconds': 6},
    {'id': 'evt:sluice_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:sluice', 'once': True,
     'text': "The river roars in through the grate. The old sluice wall makes a catwalk across the race."},
    {'id': 'evt:winch', 'preset': 'switch', 'source': 'switch:winch', 'title': 'Bridge winch',
     'condition': {'not': {'map_var': 'bridge_out'}}, 'opens': ['mover:drawbridge'], 'sets': {'map_var': 'bridge_out'},
     'effects': [{'lua': 'evt.PlaySoundName("xeen_winch", 576, 3712, 192)'}],
     'text': "The winch clanks round: the plank bridge rolls out across the race to the west bank.",
     'else_effects': [{'text': "The bridge is out across the race."}],
     'notes': "set:drawbridge: once out it stays out; the short way back west."},
    {'id': 'evt:stair_voices', 'preset': 'text', 'trigger': 'step', 'source': 'room:boss_stair', 'once': True,
     'text': "Voices above: \"...a royal tiara won't fence in Rivercity, boss. Too hot.\" \"Then it stays in the strongroom till it cools.\"",
     'seconds': 7},
    {'id': 'evt:ledger', 'preset': 'text', 'source': 'platform:desk', 'title': "Boss's ledger", 'window': True,
     'text': "The Robber Boss's ledger. Takings by the week; a royal tiara, 'not to be fenced'; and at the foot, underlined twice: STRONGROOM - throw the catch by the hearth BEFORE you walk the passage. Darts for anyone who forgets. That means you, Weasel.",
     'notes': "The clue to the strongroom passage's traps."},
    {'id': 'evt:catch', 'preset': 'switch', 'source': 'switch:catch', 'title': 'Catch',
     'condition': {'not': {'map_var': 'catch_thrown'}}, 'sets': {'map_var': 'catch_thrown'},
     'text': "You throw the catch. Deep in the wall of the passage something ratchets and locks.",
     'else_effects': [{'text': "The catch is thrown: the passage's darts are locked."}],
     'notes': "set:strongroom_traps: throws once and stays."},
    {'id': 'evt:darts', 'preset': 'script', 'trigger': 'step', 'source': 'plate:dart_1',
     'sources': ['plate:dart_2', 'plate:dart_3'],
     'condition': {'not': {'map_var': 'catch_thrown'}},
     'effects': [{'damage': {'amount': 10, 'kind': 'physical', 'who': 'all'}}],
     'text': "Click. Darts hiss out of the walls!",
     'notes': "set:strongroom_traps: every slab fires until the catch is thrown."},
    {'id': 'evt:vault_door', 'preset': 'door', 'source': 'door:vault', 'title': 'Iron door', 'action': 'open',
     'condition': {'item': 'ring_of_keys'},
     'locked_text': "An iron door with three locks. The Robber Boss carries the keys on a ring at his belt.",
     'sets': {'qbit': 'robbers_vault_opened'},
     'text': "The three keys turn one after another, and the iron door grinds up.",
     'notes': "link:strongroom_vault: the boss's ring of keys. A3's hook q-c3.vault_door has no call: the map sets robbers_vault_opened itself."},
    {'id': 'evt:chest_fence', 'preset': 'chest', 'source': 'chest:fence', 'title': 'Chest'},
    {'id': 'evt:chest_boss', 'preset': 'chest', 'source': 'chest:boss', 'title': 'Chest'},
    {'id': 'evt:chest_vault', 'preset': 'chest', 'source': 'chest:vault', 'title': 'Chest',
     # F15 (the user, 2026-11-21): the tiara is in the strongbox with the takings; the hook only sets tiara_recovered
     # once (no window, which would close the chest).
     'effects': [{'lua': 'XeenQuests.hook("q-c3.vault")'}],
     'notes': "goal:tiara: the strongbox opens on the gang's takings and Princess Roxanne's tiara (a chest item); A3's hook q-c3.vault sets tiara_recovered on the first opening."},
    {'id': 'evt:boss_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:robber_boss'}},
     'effects': [{'lua': 'XeenQuests.hook("q-c3.boss")'}],
     'notes': "set:robber_boss: A3's hook q-c3.boss sets robber_boss_slain and says his death on the status line (the ring of keys at his belt); he carries the vault's keys, looted from his corpse."},
]
wiring = {'format': 0, 'variables': ['bridge_out', 'catch_thrown', 'purse_taken'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd21', 'name': "Robbers' Den", 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-21', 'migrated': ['ceiling_level_sides', 'platform_in_sunken_level'], 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [16, 14], 'climbs': 's'},
    'map_stats': {'id': 9137, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 3, 'perception_difficulty': 5,
                  'refill_days': 672, 'music': 18, 'environment': 'stone hall', 'lock_difficulty': 5, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Outlaw', 'tier': 1, 'per_marker': [2, 3], 'weight': 60},
                            {'monster': 'Xeen Ranger', 'tier': 2, 'per_marker': [2, 3], 'weight': 40}]},
    'neighbours': [
        {'id': 'door:xd21', 'to': 'xeen_x2.odm', 'kind': 'door', 'arrival': [1280, 4172, 640], 'direction': 90,
         'arrival_hint': "On Rivercity's south quay under the great bridge's south end, in front of the den's door in the quay's retaining wall, facing away from it (north, toward the river).",
         'notes': "X2 (Rivercity): the final outside arrival of devdocs/xeen/briefs/x2/DOORS.md (door at 1280, 3772, 640 in the south quay's wall; arrival X 1280, Y 4172, Z 640, facing north)."},
    ],
    'qbits': {'tiara_recovered': 110300, 'robber_boss_slain': 110301, 'robbers_den_found': 110302,
              'robbers_vault_opened': 110303, 'arrived_once': 110304},
    'items': {'roxannes_tiara': 12150, 'ring_of_keys': 12151},
    'notes': "Xeen design brief, level L4: the Robbers' Den under Rivercity's great bridge (Q-C3 Princess Roxanne's tiara, promotion T1-E), a playable map (NOTES.md), installed in the Xeen world (assets_dev/worlds/xeen/maps). Monsters are the world's rows (A2): slot 1 Outlaws (Xeen Outlaw: Rogue 11110 at tier a, Thief 11111 at the lieutenants' marker), slot 2 Evil rangers (Xeen Ranger, Evil Ranger 11131 at tier b); the Robber Boss is the boss row 11113, his bodyguards Thieves 11111. The map_stats row 9137 is the world's (A2's source/map_rows.yml); this card matches it. Items: roxannes_tiara 12150, ring_of_keys 12151. Quest bits 110300-110303 (Q-C3's names); A3's hooks q-c3.arrival, q-c3.boss and q-c3.vault (which gives the tiara) are called from lua effects, q-c3.secret_door and q-c3.vault_door have no call and the map sets their bits. Music: dungeon track 18. The one neighbour is X2's door:xd21 (devdocs/xeen/briefs/x2/DOORS.md, final arrival).",
}

L4.mkdir(parents=True, exist_ok=True)
for name, doc in [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring), ('project.yml', project)]:
    text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
    (L4 / name).write_text(text)
print('written')
