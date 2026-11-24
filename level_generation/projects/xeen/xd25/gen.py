#!/usr/bin/env python3
"""XD-25 Asp Undercroft: writes the L1-L4 project folders of devdocs/xeen/briefs/xd25 from the plan below.

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd25/v.sh); never hand-edit the written files.

Frame: x east, y north, z up. The cellars under Asp at z 0 (the stair's top, where the party arrives from Asp's
square, at 256); the machine level at -640. Rooms stand 128 apart (the walls' thickness)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd25'
# X4 (Burlock Savannah, lane A5): once xeen_x4.odm is installed, the cellar door leads up to Asp's square at A5's
# arrival (briefs/x4/DOORS.md, door:xd25: hatch at (-11520, -8960, 1056), arrival 400 south, facing south); until then
# it stays sealed. XD25_X4=1 or 0 overrides the test (scratch builds).
X4_STEM = 'xeen_x4.odm'
X4_IN = os.environ.get('XD25_X4', '1' if (R / 'assets_dev/worlds/xeen/maps' / X4_STEM).exists() else '0') == '1'
X4_ARRIVAL = [-11520, -9448, 1056]


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# Cellars under Asp: MM8 Ancient Troll Home (d43, Ravage Roaming's desert): sandstone rubble walls, carved sandstone
# floor tiles, sandy plaster, dark slab vaults, plank doors.
RUBBLE = S('gkp2-bs1', 128, 256)
SANDTILE = S('gkp2flr', 128, 128)
SLAB = S('tfb11', 128, 128)
PLANK = S('trim9_32a', 64, 32)
ASHLAR = S('t01a01a', 128, 256)
PLASTER = S('hhr1bwall', 128, 256)
SAND = S('hhr1p', 128, 128)
# The machine level: MM8 Naga Vault (d18, the snake people's vault): green-grey granite, a floor of snake-scale arcs,
# a scale frieze at the top of the walls, warm slabs.
GRANITE = S('gston1wl', 128, 256)
SCALES = S('gston1fl', 128, 128)
FRIEZE = S('gstn1tp1', 128, 256)
WARMSLAB = S('tfb1', 128, 128)
# The machine: the world's bronze, iron and crystal (XD-03's gong strips, XD-02's rusted iron, XD-04's iron, XD-03's
# quartz, XD-02's grille), and the one new texture, the field of light (xufield, a cut-out).
BRONZE = S('xngong1', 128, 32)
RUST = S('xnrustirn', 64, 64)
IRON = S('xwiron', 128, 128)
QUARTZ = S('xnquartz', 256, 256)
# Bars that run along a cage or a gate (texture fit, merge point 16): XD-04's cage band (trim_u), one picture up.
BARS = S('xwcage', 128, 256)
FIELD = S('xufield', 256, 256, translucent=1)  # merge point 12: a see-through leaf
DAYLIGHT = S('xodaylt', 256, 128)

VAULT_BANDS = [{'height': 256, 'surface': GRANITE}]

themes = [
    {'id': 'theme:cellar', 'wall': RUBBLE, 'floor': SANDTILE, 'ceiling': SLAB, 'door': PLANK, 'reveal': ASHLAR,
     'notes': "The cellars under Asp: MM8 Ancient Troll Home's sandstone rubble walls (gkp2-bs1), carved sandstone tiles (gkp2flr), dark slab vaults (tfb11), plank doors (trim9_32a)."},
    {'id': 'theme:plaster', 'wall': PLASTER, 'floor': SAND, 'ceiling': SLAB, 'door': PLANK, 'reveal': ASHLAR,
     'notes': "The snake men's own rooms upstairs: sandy plaster (hhr1bwall) over a gravelly sand floor (hhr1p)."},
    {'id': 'theme:vault', 'wall': FRIEZE, 'floor': SCALES, 'ceiling': SLAB, 'door': PLANK, 'reveal': WARMSLAB,
     'notes': "The machine level: MM8 Naga Vault's granite (gston1wl) under a scale frieze (gstn1tp1), the snake-scale floor (gston1fl), warm slabs (tfb1) in the doorways."},
]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


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


def block(at, size, rise, side, top, notes, **kw):
    d = {'at': at, 'size': size, 'rise': rise, 'surface': side, 'top_surface': top, 'notes': notes}
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ the cellars (z 0)
room('room:stair', 'Cellar stair', outline=rect(-2304, 1536, -1408, 1984), floor=256,
     slope={'to': 0, 'toward': 'east', 'steps': 8, 'riser': ASHLAR, 'tread': SANDTILE},
     ceiling=640, ceiling_slope={'to': 448, 'toward': 'east'}, theme='theme:cellar', ambient=22,
     walls=[{'wall': 'west', 'panels': [{'id': 'panel:asp_door', 'at': 'centre', 'length': 192, 'bottom': 0,
                                         'height': 256, 'surface': S('xodaylt', 256, 128, fit=True, uneven=True),
                                         'notes': "The cellar door up to Asp's square, daylight round it (XD-05's daylight picture): sealed while X4 is not built."}]}],
     notes="Eight steps of 32 down east from the cellar door on Asp's square (the arrival) to the old cistern's door; sloughed snakeskins on the treads.")
CIS = rect(-1280, 1024, 640, 2560)
room('room:cistern', 'Old cistern', outline=CIS, floor=0, ceiling=512, theme='theme:cellar', ambient=16,
     ceiling_levels=[{'ceiling': 704, 'top_scale': [1, 0], 'edge': SLAB, 'notes': "A sandstone barrel vault east-west."}],
     levels=[{'id': 'level:basin', 'outline': rect(-896, 2048, 256, 2432), 'floor': -192, 'edge': ASHLAR,
              'surface': SAND, 'notes': "The cistern's dry basin: sand and silt where the town's water stood."}],
     flights=[{'from': [-320, 2280], 'to': [-320, 2048], 'from_height': -192, 'to_height': 0, 'width': 256,
               'steps': 6, 'riser': ASHLAR, 'tread': SANDTILE,
               'notes': "Six steps down into the dry basin from its south side."}],
     platforms=[block([-1024, 1280], [128, 128], 512, ASHLAR, ASHLAR, "Pier"),
                block([-1024, 2304], [128, 128], 512, ASHLAR, ASHLAR, "Pier")],
     walls=[{'wall': 'north', 'panels': [{'id': 'panel:spout', 'at': 'centre', 'length': 128, 'bottom': 192,
                                          'height': 128, 'surface': ASHLAR, 'notes': "The old inflow, dry."}]}],
     notes="Asp's old cistern, 1,920 by 1,536 under a sandstone vault: the dry basin in its north half (192 deep, six steps down), two piers by the west wall. The snake men's hall: the stair's door on the west, an arch east to the moulting room, a door south to the holding pens, a loose slab low in the west wall (the hidden cache).")
room('room:hidden_cache', 'Hidden cache', outline=rect(-1920, 1024, -1408, 1408), floor=0, ceiling=320,
     theme='theme:cellar', ambient=24,
     notes="A townsman's hiding hole behind a loose slab of the cistern's west wall, 512 by 384.")
room('room:moulting', 'Moulting room', outline=rect(768, 1280, 2176, 2304), floor=0, ceiling=448,
     theme='theme:plaster', ambient=18,
     beams=[{'path': [[768, 1600], [2176, 1600]], 'width': 16, 'depth': 16, 'bottom': 320, 'surface': PLANK,
             'notes': "A drying pole for shed skins."},
            {'path': [[768, 2000], [2176, 2000]], 'width': 16, 'depth': 16, 'bottom': 320, 'surface': PLANK,
             'notes': "A second drying pole."}],
     notes="Where the snake men shed: two drying poles across the room hung with papery skins, 1,408 by 1,024; a chest of the townsfolk's belongings in the north-east corner.")
room('room:pens', 'Holding pens', outline=rect(-1024, -256, 640, 896), floor=0, ceiling=512,
     theme='theme:cellar', ambient=18,
     notes="Three barred cages against the west wall, half-turned townsfolk in them; the cistern's door north, an arch east to the brood hall, the drain's grate low in the south wall (the way back up from the machine).")
CAGES = [(592, 880), (224, 512), (-144, 144)]          # y ranges of the three cages (x from -1008 to -720)
pens = rooms[-1]
pens['platforms'] = []
for n, (y0, y1) in enumerate(CAGES, 1):
    pens['platforms'] += [
        block([-864, y0 + 4], [288, 8], 256, BARS, IRON, f"Cage {n}: bars, south side", end_surface=S('xwiron', 128, 128, fit=False)),
        block([-864, y1 - 4], [288, 8], 256, BARS, IRON, f"Cage {n}: bars, north side", end_surface=S('xwiron', 128, 128, fit=False)),
    ]
pens['platforms'].append(block([-864, 0 + 896 - 8], [288, 16], 32, IRON, IRON, "The cages' iron sill under the north cage"))
pens['platforms'].pop()   # no sill: kept simple (the bars stand on the floor)
room('room:brood', 'Brood hall', outline=rect(768, -512, 2560, 1152), floor=0, ceiling=576, theme='theme:plaster',
     ambient=18,
     ceiling_levels=[{'ceiling': 768, 'top_scale': [0, 1], 'edge': SLAB, 'notes': "A vault north-south."}],
     platforms=[block([x, y], [128, 128], 576, ASHLAR, ASHLAR, "Pier") for x in (1280, 2048) for y in (128, 640)],
     notes="The new snake men's hall, 1,792 by 1,664, four piers under a vault: straw where they lie fresh from the machine; the stair down in the south-east corner.")
room('room:brood_stair', 'Brood stair', outline=rect(2144, -1920, 2464, -640), floor=0,
     slope={'to': -640, 'toward': 'south', 'steps': 20, 'riser': ASHLAR, 'tread': SANDTILE},
     ceiling=384, ceiling_slope={'to': -256, 'toward': 'south'}, theme='theme:cellar', ambient=22,
     notes="Twenty steps of 32 down south from the brood hall to the machine level: the air grows warm and starts to hum.")

# ------------------------------------------------------------------------------------------------ the machine level (z -640)
room('room:coil', 'Coil passage', path=[[2304, -2048], [2304, -3584], [320, -3584]], width=320, floor=-640,
     ceiling=-256, theme='theme:vault', ambient=18,
     notes="The warm passage round two sides of the machine hall, 320 wide: from the brood stair south, then west to the field of light; the keeper's door in its east wall.")
room('room:keeper', "Keeper's cell", outline=rect(2592, -3328, 3360, -2560), floor=-608, ceiling=-224,
     theme='theme:vault', ambient=20, bands=VAULT_BANDS,
     platforms=[{'id': 'platform:straw_bed', 'at': [3184, -2720], 'size': [256, 384], 'rise': 24, 'surface': PLANK,
                 'top_surface': SAND, 'notes': "The keeper's straw bed."}],
     notes="The machine's keeper's cell, one step up from the passage, 768 by 768: his straw bed, his hoard.")
room('room:field_gate', 'Field gate', outline=rect(-448, -3744, 192, -3424), floor=-640, ceiling=-256,
     theme='theme:vault', ambient=16,
     notes="A short passage at the coil passage's west end; the field of light across the doorway north into the transformer hall, the pedestals' second rhyme cut in the stone over it.")
MCX, MCY = 384, -2560         # the transformer's middle
room('room:machine_hall', 'Transformer hall', outline=rect(-1024, -3296, 1024, -1920), floor=-640, ceiling=-128,
     theme='theme:vault', ambient=14, bands=VAULT_BANDS,
     ceiling_levels=[{'ceiling': 128, 'top_scale': [0.5, 0.5], 'edge': GRANITE, 'notes': "A stepped granite lantern over the machine."}],
     platforms=[
         block([MCX, MCY], [640, 640], 32, WARMSLAB, WARMSLAB, "The machine's plinth."),
         block([MCX - 224, MCY - 224], [128, 128], 448, BRONZE, RUST, "Coil, south-west", base=32),
         block([MCX + 224, MCY - 224], [128, 128], 448, BRONZE, RUST, "Coil, south-east", base=32),
         block([MCX - 224, MCY + 224], [128, 128], 448, BRONZE, RUST, "Coil, north-west", base=32),
         block([MCX + 224, MCY + 224], [128, 128], 448, BRONZE, RUST, "Coil, north-east", base=32),
         {'id': 'platform:transformer', 'at': [MCX, MCY], 'size': [192, 192], 'rise': 288, 'base': 32,
          'surface': S('xwcage', 128, 256, scale=1.125), 'top_surface': IRON,
          'end_surface': S('xwcage', 128, 256, scale=1.125),
          'notes': "The transformer's chamber: a cage of bars between the coils, an empty socket shaped like a scarab in its face."},
         {'id': 'platform:crown', 'at': [MCX, MCY], 'size': [320, 320], 'rise': 64, 'base': 320, 'surface': BRONZE,
          'top_surface': QUARTZ, 'notes': "The crown over the chamber, its crystals glowing blue."},
     ],
     notes="The set piece: a granite hall 2,048 by 1,376 under a stepped lantern; the transformer in its east half (four bronze coils round a chamber of bars on a slab plinth, a crown of crystal on top). The field of light south, the crystal housing's iron door north behind the machine, the drain's mouth north-west.")
room('room:crystal_niche', 'Crystal housing', outline=rect(128, -1792, 640, -1408), floor=-640, ceiling=-320,
     theme='theme:vault', ambient=20,
     platforms=[{'id': 'platform:housing', 'at': [384, -1504], 'size': [256, 128], 'rise': 96, 'surface': IRON,
                 'top_surface': IRON, 'notes': "The crystal housing: an iron box the machine fed from."}],
     notes="A small iron-doored niche behind the transformer, 512 by 384: the housing where Falagar's crystals sit.")
room('room:drain', 'Drain tunnel', outline=rect(-512, -1792, -256, -384), floor=-640,
     slope={'to': 0, 'toward': 'north', 'steps': 20, 'riser': GRANITE, 'tread': SCALES},
     ceiling=-320, ceiling_slope={'to': 320, 'toward': 'north'}, theme='theme:vault', ambient=24,
     notes="The machine's run-off channel climbing north in twenty steps to a grate under the holding pens: bolted on this side, the way back up.")

# ------------------------------------------------------------------------------------------------ openings
op('open:stair_cistern', 'room:stair', 'room:cistern', link='link:stair_cistern', width=256, height=256)
op('open:cistern_cache', 'room:cistern', 'room:hidden_cache', link='link:cistern_cache', width=192, height=224,
   notes="The loose slab low in the cistern's west wall.")
op('open:cistern_moulting', 'room:cistern', 'room:moulting', link='link:cistern_moulting', width=384, height=320,
   along=0.3)
op('open:cistern_pens', 'room:cistern', 'room:pens', link='link:cistern_pens', width=256, height=256, along=0.86)
op('open:pens_brood', 'room:pens', 'room:brood', link='link:pens_brood', width=448, height=320)
op('open:moulting_brood', 'room:moulting', 'room:brood', link='link:moulting_brood', width=384, height=320,
   along=0.6)
op('open:brood_stair', 'room:brood', 'room:brood_stair', link='link:brood_coil', width=256, height=320)
op('open:stair_coil', 'room:brood_stair', 'room:coil', link='link:brood_coil', width=256, height=320)
op('open:coil_keeper', 'room:coil', 'room:keeper', link='link:coil_keeper', width=256, height=256)
op('open:coil_field', 'room:coil', 'room:field_gate', link='link:coil_field', width=288, height=320)
op('open:field_machine', 'room:field_gate', 'room:machine_hall', link='link:field_machine', width=256,
   height=256, reveal=WARMSLAB)
op('open:machine_crystal', 'room:machine_hall', 'room:crystal_niche', link='link:machine_crystal', width=192,
   height=256)
op('open:machine_drain', 'room:machine_hall', 'room:drain', link='link:machine_drain', width=192, height=256)
op('open:drain_pens', 'room:drain', 'room:pens', link='link:drain_pens', width=192, height=224)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:cellar', 'ambient': 18}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-25 Asp Undercroft: the cellars under Asp (z 0) and the machine level (z -640); x east, y north. Written by output/studio_cal/xd25/tools/gen.py."}

# ================================================================================================ plan.yml
PLAN_SPACES = [
    ('room:stair', 'Cellar stair', 'room', 'S', "Down from Asp's square by the well; sloughed skins on the steps.", 0),
    ('room:cistern', 'Old cistern', 'room', 'M', "The town's dry cistern, now the snake men's hall; hissing in the dark.", 4),
    ('room:moulting', 'Moulting room', 'room', 'M', "Shed skins hung like washing; a chest of townsfolk's belongings.", 4),
    ('room:hidden_cache', 'Hidden cache', 'room', 'S', "Behind a loose cistern slab: a townsman's hidden savings.", 0),
    ('room:pens', 'Holding pens', 'room', 'M', "Three cages of half-turned townsfolk (freed when the machine dies); the drain's grate.", 3),
    ('room:brood', 'Brood hall', 'room', 'L', "The new snake men, fresh from the machine; the stair down.", 7),
    ('room:brood_stair', 'Brood stair', 'corridor', 'S', "Twenty steps down to the machine level.", 0),
    ('room:coil', 'Coil passage', 'corridor', 'M', "A warm, humming passage round the machine hall.", 4),
    ('room:keeper', "Keeper's cell", 'room', 'S', "The keeper's straw bed and his hoard (one step up).", 2),
    ('room:field_gate', 'Field gate', 'corridor', 'S', "A wall of humming light across the way; the pedestals' rhyme cut over it.", 0),
    ('room:machine_hall', 'Transformer hall', 'room', 'L', "The transformer: brass coils, a chamber of bars, an empty scarab socket, the crystals in its crown. Destroy it.", 3),
    ('room:crystal_niche', 'Crystal housing', 'room', 'S', "The Crystals of Piezoelectricity, loose once the machine is broken (Q-C11).", 0),
    ('room:drain', 'Drain tunnel', 'corridor', 'S', "The machine's run-off channel climbing to the grate under the pens (the way back).", 0),
]


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, n in PLAN_SPACES:
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size,
             'floor': 0 if sid in ('room:stair', 'room:cistern', 'room:moulting', 'room:hidden_cache', 'room:pens', 'room:brood') else -640,
             'purpose': purpose}
        if n:
            s['population'] = [{'slot': 1, 'groups': 1, 'per_marker': [2, 3], 'levels': [16, 26], 'notes': f"About {n} snake men."}]
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:stair_cistern', 'from': 'room:stair', 'to': 'room:cistern', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:cistern_cache', 'from': 'room:cistern', 'to': 'room:hidden_cache', 'kind': 'secret_door',
         'motion': 'slide', 'notes': "A slab that sinks."},
        {'id': 'link:cistern_moulting', 'from': 'room:cistern', 'to': 'room:moulting', 'kind': 'open'},
        {'id': 'link:cistern_pens', 'from': 'room:cistern', 'to': 'room:pens', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:pens_brood', 'from': 'room:pens', 'to': 'room:brood', 'kind': 'open'},
        {'id': 'link:moulting_brood', 'from': 'room:moulting', 'to': 'room:brood', 'kind': 'open'},
        {'id': 'link:brood_coil', 'from': 'room:brood', 'to': 'room:coil', 'kind': 'stairs',
         'notes': "By the brood stair (its own room)."},
        {'id': 'link:coil_keeper', 'from': 'room:coil', 'to': 'room:keeper', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:coil_field', 'from': 'room:coil', 'to': 'room:field_gate', 'kind': 'open'},
        {'id': 'link:field_machine', 'from': 'room:field_gate', 'to': 'room:machine_hall', 'kind': 'door',
         'motion': 'slide', 'condition': {'qbit': 'q_c5_pedestals'},
         'notes': "The field of light (a see-through leaf, xufield) sinks once the pedestals round Asp's well are set (q-c5.pedestals, X4)."},
        {'id': 'link:machine_crystal', 'from': 'room:machine_hall', 'to': 'room:crystal_niche', 'kind': 'door',
         'motion': 'slide', 'condition': {'qbit': 'q_c5_done'}, 'notes': "Opens when the transformer is destroyed."},
        {'id': 'link:machine_drain', 'from': 'room:machine_hall', 'to': 'room:drain', 'kind': 'open'},
        {'id': 'link:drain_pens', 'from': 'room:drain', 'to': 'room:pens', 'kind': 'door', 'motion': 'slide',
         'condition': {'map_var': 'drain_reached'},
         'notes': "The grate: bolted on the drain side; opened from below, then both ways."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "Under the desert town of Asp, whose people are turning into snakes, a cellar stair by the well leads down into the old dry cistern, now the snake men's hall. Past their moulting room and the pens where half-turned townsfolk wait in cages, a stair from the brood hall goes down to a granite level that hums: round the corner a wall of coloured light bars the way to the transformer, the machine that makes snake men. The light drops only when the pedestals round Asp's well are set. Behind the machine lie Falagar's stolen crystals; break it and the cages open.",
        'purpose': "Q-C5 The Snakes of Asp (destroy the transformer: Asp is liberated, its services open) and Q-C11 the Crystals of Piezoelectricity for Falagar. Party 14 to 16, Snake men 16/20/26, 28 monsters, treasure level 2 with the keeper's hoard at 3.",
        'mood': "Dry sandstone cellars, hissing in the dark, shed skins; then warm granite, a hum through the floor, blue light from the machine's crown.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:upper', 'spaces': ['room:cistern', 'room:moulting', 'room:brood', 'room:pens'],
             'notes': "Round the cellars."},
            {'id': 'loop:return', 'spaces': ['room:pens', 'room:brood', 'room:coil', 'room:field_gate',
                                             'room:machine_hall', 'room:drain'],
             'closed_until': {'map_var': 'drain_reached'},
             'notes': "Down the brood stair, back up the drain: closed until the grate is opened from below."},
        ],
        'entrances': [{'id': 'entrance:x4_asp', 'space': 'room:stair', 'kind': 'arrival', 'facing': 'e',
                       'how': "At the top of the cellar stair under Asp's square (X4's door:xd25); the door back up is sealed until X4 is built."}],
        'critical_path': ['room:stair', 'room:cistern', 'room:moulting', 'room:brood', 'room:brood_stair', 'room:coil',
                          'room:field_gate', 'room:machine_hall', 'room:crystal_niche'],
        'return_path': ['room:crystal_niche', 'room:machine_hall', 'room:drain', 'room:pens', 'room:cistern', 'room:stair'],
        'goals': [
            {'id': 'goal:transformer', 'space': 'room:machine_hall', 'kind': 'use', 'story': 'Q-C5',
             'what': "Destroy the transformer (\"You have found the transformer! Do you wish to destroy it?\").",
             'gives': {'qbit': 'q_c5_done'}},
            {'id': 'goal:crystals', 'space': 'room:crystal_niche', 'kind': 'take', 'story': 'Q-C11',
             'what': "The Crystals of Piezoelectricity in the housing behind the machine.", 'gives': {'qbit': 'q_c11_crystals'}},
        ],
        'keys': [{'id': 'key:pedestals', 'grants': {'qbit': 'q_c5_pedestals'}, 'found_in': 'room:stair',
                  'how': "X4: the eight pedestals round Asp's well set red/blue from the south-west (A5's map; q-c5.pedestals)."}],
        'set_pieces': [
            {'id': 'set:field', 'kind': 'puzzle', 'spaces': ['room:field_gate'],
             'rule': "The field of light holds until the pedestals round Asp's well are set; the stone over it gives the second rhyme, Eve says the rule outright."},
            {'id': 'set:transformer', 'kind': 'scripted', 'spaces': ['room:machine_hall', 'room:pens', 'room:crystal_niche'],
             'rule': "A click (F47: no question): the machine dies (q-c5.done), the crystal housing and the cages open; the freed townsfolk thank the party in the pens and are gone on the next entry."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 13, 'sectors': 13, 'monsters_about': 28, 'chests': 3, 'doors': 8, 'loops': 2,
                   'floor_area_munits2': 15},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act2_graphs/xd25.graph.yml and D-4's decisions (act2_dungeon_decisions.md, XD-25): pedestals on X4, Guardian Asps left out, caged townsfolk kept, the door of light as XD-04's ward. The brood stair is its own room (13 rooms); the drain's grate is in the pens' south wall at the top of a stepped culvert (not a floor hatch with a ladder).",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-25 Asp Undercroft (not to scale; north up)

  cellars, z 0
                      [cistern] ---- open ---- [moulting]
   (X4: Asp) =door= /   |  basin  \\               |
   [stair]------door  secret       door           open
                     [cache]        |              |
                                  [pens] ---open--[brood]
                                    ^ grate          | stairs
  machine level, z -640             | (drain)     [brood stair]
                                 [drain]             |
   [crystal niche]=door(machine)= [TRANSFORMER HALL]  [coil] =door= [keeper's cell]
                                    ||  field of light   |
                                 [field gate] ---------- '
"""

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:stair', 'at': [-2208, 1760], 'facing': 0,
                    'notes': "At the top of the cellar stair, just inside the door from Asp's square (X4's door:xd25), facing down (east)."}
if X4_IN:
    objects['exits'] = [
        {'id': 'exit:asp_door', 'room': 'room:stair', 'wall': 'west', 'size': [192, 256],
         'surface': S('7solid01', 256, 128, fit=True, uneven=True), 'to': 'exit:asp_square',
         'notes': "The cellar door up to Asp's square on X4 (door:xd25), daylight round it."}]
objects['doors'] = [
    {'id': 'door:stair', 'opening': 'open:stair_cistern', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'thickness': 16, 'speed': 160, 'surface': PLANK, 'notes': "The plank door at the foot of the stair."},
    {'id': 'door:cache', 'opening': 'open:cistern_cache', 'kind': 'slide_down', 'secret': True, 'tile': True,
     'thickness': 32, 'speed': 80, 'surface': RUBBLE, 'back_surface': RUBBLE,
     'notes': "The loose slab: the cistern's own rubble stone, sinking into the floor (secret)."},
    {'id': 'door:pens', 'opening': 'open:cistern_pens', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'thickness': 16, 'speed': 160, 'surface': PLANK},
    {'id': 'door:keeper', 'opening': 'open:coil_keeper', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'thickness': 16, 'speed': 160, 'surface': PLANK},
    {'id': 'door:field', 'opening': 'open:field_machine', 'kind': 'slide_down', 'fold': True, 'tile': True,
     'speed': 96, 'surface': FIELD,
     'notes': "The field of light: a see-through leaf of red and blue light (xufield, cut-out) that sinks into the floor once the pedestals are set (XD-04's ward)."},
    {'id': 'door:crystal', 'opening': 'open:machine_crystal', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'thickness': 24, 'speed': 64, 'surface': IRON, 'notes': "The crystal housing's iron door: opens when the machine dies."},
    {'id': 'door:grate', 'opening': 'open:drain_pens', 'kind': 'slide_up', 'fold': True, 'tile': True,
     'thickness': 16, 'speed': 96, 'surface': BARS,
     'notes': "The drain grate (XD-02's grille, see-through): bolted on the drain side."},
]
# The plank doors show a door (the orchestrator's F12(b) decision, A7 s27): the Ancient Troll Home kit's plank door pair
# (gkp103a/b), one wing on each of two leaves 128 by 256 parting sideways (the keeper's doorway widened to 256).
_PAIR = [[S('gkp103a', 128, 256), S('gkp103b', 128, 256)]]
for _d in objects['doors']:
    if _d['id'] in ('door:stair', 'door:pens', 'door:keeper'):
        _d.update(kind='slide_left', leaves=2, pictures=_PAIR, back_pictures=_PAIR)
gate_parts = []
for n, (y0, y1) in enumerate(CAGES, 1):
    if n == 1:
        continue
    gate_parts.append({'at': [-716, (y0 + y1) / 2], 'size': [8, y1 - y0 - 16], 'bottom': 0, 'height': 256,
                       'surface': BARS, 'top_surface': IRON, 'notes': f"Gate of cage {n}"})
y0, y1 = CAGES[0]
objects['plates'] = [
    {'id': 'plate:pens_entry', 'room': 'room:pens', 'at': [400, 700], 'size': [384, 256],
     'notes': "Inside the door from the cistern (the pens' first sight; drawn as the floor)."},
]
objects['movers'] = [
    {'id': 'mover:cage_gates', 'room': 'room:pens', 'at': [-716, (y0 + y1) / 2], 'size': [8, y1 - y0 - 16],
     'bottom': 0, 'height': 256, 'travel': [0, 0, 232], 'speed': 64, 'surface': BARS, 'top_surface': IRON,
     'parts': gate_parts,
     'notes': "The three cages' barred gates, one mover: wired to the machine below, they lift together when it dies."},
]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 170, 90]
DAY = [210, 200, 170]
BLUE = [120, 170, 255]
objects['lights'] = [
    light('light:stair_day', 'room:stair', [-2240, 1760], 220, 600, DAY, notes="Daylight round the cellar door."),
    light('light:cistern_w', 'room:cistern', [-1100, 1700], 260, 900, FIRE),
    light('light:cistern_e', 'room:cistern', [450, 1900], 260, 900, FIRE),
    light('light:cache', 'room:hidden_cache', [-1664, 1216], 160, 350, [200, 150, 100]),
    light('light:moulting', 'room:moulting', [1472, 2200], 260, 900, FIRE),
    light('light:pens', 'room:pens', [0, 320], 260, 1000, FIRE),
    light('light:brood_n', 'room:brood', [1664, 1000], 300, 1000, FIRE),
    light('light:brood_s', 'room:brood', [1664, -300], 300, 1000, FIRE),
    light('light:brood_stair', 'room:brood_stair', [2304, -1500], 0, 600, [180, 160, 255],
          notes="A cold glow coming up from below."),
    light('light:coil_n', 'room:coil', [2304, -2600], 240, 800, BLUE, pulse={'intensity': [0.8, 1.0], 'frequency': 0.7}),
    light('light:coil_s', 'room:coil', [1300, -3584], 240, 800, BLUE, pulse={'intensity': [0.8, 1.0], 'frequency': 0.7}),
    light('light:keeper', 'room:keeper', [2976, -2944], 260, 700, FIRE),
    light('light:field', 'room:field_gate', [-128, -3500], 200, 700, [255, 120, 150],
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.5}, notes="The field's red-blue glow."),
    light('light:machine', 'room:machine_hall', [MCX, MCY], 520, 1800, BLUE,
          pulse={'intensity': [0.7, 1.0], 'frequency': 1.2}, notes="The crown's crystals: off when the machine dies."),
    light('light:machine_w', 'room:machine_hall', [-700, -2600], 300, 900, FIRE),
    light('light:wreck', 'room:machine_hall', [MCX, MCY], 200, 900, [255, 110, 60],
          pulse={'intensity': [0.3, 0.8], 'frequency': 2.5}, on=False,
          notes="The wreck's dying sparks, after the machine is destroyed."),
    light('light:crystal', 'room:crystal_niche', [384, -1504], 200, 500, BLUE),
    light('light:drain', 'room:drain', [-384, -1100], 0, 600, [160, 170, 200]),
]
objects['chests'] = [
    {'id': 'chest:moulting', 'room': 'room:moulting', 'at': [2040, 2190], 'facing': 'w', 'treasure_level': 2,
     'random_items': 2, 'gold': 250, 'trap_level': 2,
     'notes': "A chest of the townsfolk's belongings, taken from them in the pens."},
    {'id': 'chest:cache', 'room': 'room:hidden_cache', 'at': [-1800, 1300], 'treasure_level': 2,
     'random_items': 1, 'gold': 400, 'notes': "A townsman's hidden savings."},
    {'id': 'chest:keeper', 'room': 'room:keeper', 'at': [3240, -3200], 'treasure_level': 3,
     'random_items': 2, 'gold': 700, 'trap_level': 3, 'notes': "The keeper's hoard (the map's hoard, a level up)."},
]
# A2's Snake men (assets_dev/worlds/xeen/source/monsters.yml, block 11500): A Snake Man 16 (11500), B Snake Warrior 20
# (11501), C Snake Lord 26 (11502). One slot; every marker fixes its tier.
objects['spawns'] = [
    {'id': 'spawn:cistern_basin', 'room': 'room:cistern', 'at': [-320, 2300], 'floor_height': -192, 'slot': 1,
     'tier': 'a', 'notes': "Hissing in the dry basin."},
    {'id': 'spawn:cistern_s', 'room': 'room:cistern', 'at': [-200, 1400], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:moulting', 'room': 'room:moulting', 'at': [1500, 1800], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:pens', 'room': 'room:pens', 'at': [200, 300], 'slot': 1, 'tier': 'a', 'notes': "The cages' guards."},
    {'id': 'spawn:brood_n', 'room': 'room:brood', 'at': [1664, 900], 'slot': 1, 'tier': 'b'},
    {'id': 'spawn:brood_s', 'room': 'room:brood', 'at': [1664, -200], 'slot': 1, 'tier': 'b'},
    {'id': 'spawn:brood_w', 'room': 'room:brood', 'at': [1000, 400], 'slot': 1, 'tier': 'a',
     'notes': "Fresh from the machine, on the straw."},
    {'id': 'spawn:coil_e', 'room': 'room:coil', 'at': [2304, -2900], 'slot': 1, 'tier': 'b'},
    {'id': 'spawn:coil_s', 'room': 'room:coil', 'at': [1300, -3584], 'slot': 1, 'tier': 'a'},
    {'id': 'spawn:machine', 'room': 'room:machine_hall', 'at': [-500, -2300], 'slot': 1, 'tier': 'b',
     'notes': "The machine's guard."},
]
TOWNSFOLK = [(358, CAGES[0]), (352, CAGES[1]), (355, CAGES[2])]
objects['monsters'] = [
    {'id': 'monster:machine_lord', 'room': 'room:machine_hall', 'monster': 11502, 'at': [-300, -2900], 'facing': 90,
     'hostile': True, 'group': 2, 'notes': "A Snake Lord (26) tending the machine."},
    {'id': 'monster:keeper', 'room': 'room:keeper', 'monster': 11502, 'at': [2900, -2800], 'facing': 180,
     'hostile': True, 'group': 3, 'notes': "The machine's keeper: a Snake Lord (26; D-4: no Guardian Asps)."},
    {'id': 'monster:keeper_guard', 'room': 'room:keeper', 'monster': 11502, 'at': [2900, -3100], 'facing': 180,
     'hostile': True, 'group': 3, 'notes': "His guard, a Snake Lord (26)."},
]
for n, (kind, (y0, y1)) in enumerate(TOWNSFOLK, 1):
    objects['monsters'].append(
        {'id': f'monster:townsfolk_{n}', 'room': 'room:pens', 'monster': kind, 'at': [-880, (y0 + y1) // 2],
         'facing': 0, 'hostile': False, 'group': 20, 'immobile': True,
         'notes': f"A half-turned townsman in cage {n} (an engine peasant, peaceful); hidden on the next entry once freed."})
objects['relations'] = [
    {'of': [11500, 11501, 11502], 'toward': kind, 'relation': 'friendly', 'both_ways': True}
    for kind, _ in TOWNSFOLK
]


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


def torch(id, rm, at, wall, **kw):
    return deco(id, rm, 'torch01', at, wall=wall, height=160, **kw)


objects['decorations'] = [
    torch('deco:stair_torch', 'room:stair', [-1700, 1984], 'north'),
    deco('deco:stair_bones', 'room:stair', 'dec29', [-1900, 1600]),
    torch('deco:cistern_torch_w', 'room:cistern', [-1280, 1900], 'west'),
    torch('deco:cistern_torch_e', 'room:cistern', [640, 2100], 'east'),
    deco('deco:basin_bones', 'room:cistern', 'dec29', [-700, 2350], floor_height=-192),
    deco('deco:basin_trash', 'room:cistern', 'trasheap', [84, 2300], floor_height=-192),
    deco('deco:cistern_sack_1', 'room:cistern', 'bag01', [540, 2460]),
    deco('deco:cistern_sack_2', 'room:cistern', 'bag01', [400, 2470]),
    deco('deco:cache_sack', 'room:hidden_cache', 'bag01', [-1820, 1130]),
    torch('deco:moulting_torch', 'room:moulting', [1472, 2304], 'north'),
    deco('deco:moulting_trash', 'room:moulting', 'trasheap', [2060, 1400]),
    torch('deco:pens_torch', 'room:pens', [640, -100], 'east'),
    deco('deco:pens_bucket', 'room:pens', 'Bucket', [530, -160]),
    torch('deco:brood_torch_w', 'room:brood', [768, -300], 'west'),
    torch('deco:brood_torch_e', 'room:brood', [2560, 700], 'east'),
    deco('deco:brood_trash', 'room:brood', 'trasheap', [900, -400]),
    deco('deco:brood_sack_1', 'room:brood', 'bag01', [2450, 1050]),
    deco('deco:brood_sack_2', 'room:brood', 'bag01', [2310, 1060]),
    deco('deco:brood_bones', 'room:brood', 'dec29', [2420, 300]),
    torch('deco:coil_torch', 'room:coil', [2464, -3200], 'east'),
    torch('deco:keeper_torch', 'room:keeper', [2700, -2560], 'north'),
    deco('deco:keeper_bones', 'room:keeper', 'dec29', [3250, -3020]),
    torch('deco:machine_torch_w', 'room:machine_hall', [-1024, -2600], 'west'),
    deco('deco:machine_corpse', 'room:machine_hall', 'Corpse03', [-600, -3100],
         notes="A townsman who did not finish turning."),
    deco('deco:crystals', 'room:crystal_niche', 'crclstr', [384, -1504], floor_height=-544,
         notes="Falagar's crystals in their housing."),
    deco('deco:drain_bones', 'room:drain', 'dec29', [-440, -1650]),
]
objects['sounds'] = [
    {'id': 'sound:hum', 'room': 'room:machine_hall', 'at': [MCX, MCY], 'sound': 'humming', 'radius': 4000,
     'inner_radius': 900, 'volume': 0.8, 'notes': "The transformer's hum, heard through the machine level."},
    {'id': 'sound:hiss_cistern', 'room': 'room:cistern', 'at': [-320, 2240], 'sound': 'snake rattle01',
     'radius': 1600, 'wait': [6, 14], 'volume': 0.6, 'notes': "Hissing in the dark."},
    {'id': 'sound:hiss_brood', 'room': 'room:brood', 'at': [1664, 300], 'sound': 'snake rattle03',
     'radius': 1800, 'wait': [5, 12], 'volume': 0.6},
    {'id': 'sound:drip', 'room': 'room:drain', 'at': [-384, -1500], 'sound': 'drip02', 'radius': 1200,
     'wait': [3, 9], 'volume': 0.5},
]

# ================================================================================================ wiring
QBITS = {'townsfolk_thanked': 110840, 'q_c5_pedestals': 112101, 'q_c5_done': 112102, 'q_c11_crystals': 112222}
events = [
    {'id': 'evt:arrive', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'text': "Stone steps lead down from Asp's square into the dark. Sloughed snakeskins lie on every tread, and from below comes a dry hissing.",
     'seconds': 7},
    {'id': 'evt:townsfolk_gone', 'preset': 'script', 'trigger': 'load',
     'lua': ('if IsQBitSet(QBit(110840)) and not IsAtLeast(MapVar(in_visit), 1) then\n'
             '    evt.SetMonGroupBit(20, MonsterBits.Invisible, 1)\n'
             'end\n'
             'SetValue(MapVar(in_visit), 1)'),
     'notes': "D-4: the freed townsfolk (townsfolk_thanked 110840) are gone on the next entry (they went home). A load "
              "inside a visit (a saved game) finds in_visit set (saved with the map) and leaves them; leaving clears "
              "it (evt:visit_end), so only a fresh entry hides them (A8's DD-09 fix)."},
    {'id': 'evt:visit_end', 'preset': 'script', 'trigger': 'leave',
     'effects': [{'set': {'var': {'map_var': 'in_visit'}, 'value': 0}}],
     'notes': "Leaving ends the visit: the next load is a fresh entry (evt:townsfolk_gone)."},
    {'id': 'evt:asp_door', 'preset': 'exit', 'source': 'exit:asp_door', 'title': "Door to Asp's square",
     'text': "You climb out into Asp's square.",
     'notes': "Up to X4's door:xd25 in Asp's square (A5's arrival, facing south)."} if X4_IN else
    {'id': 'evt:asp_door', 'preset': 'text', 'source': 'panel:asp_door', 'title': "Door to Asp's square",
     'text': "The door at the head of the stair will not move: the snake men have wedged it from the square with beams. There is no way up here for now.",
     'notes': "Sealed exit (X4 is not built): the arrival from X4 is the map's start; when X4 exists this panel becomes an exit to its door:xd25."},
    {'id': 'evt:stair_door', 'preset': 'door', 'source': 'door:stair', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:cistern_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:cistern', 'once': True,
     'text': "Asp's old cistern, dry for years. Something long and scaled moves in the basin.", 'seconds': 5},
    {'id': 'evt:cache_door', 'preset': 'door', 'source': 'door:cache', 'title': 'Loose slab', 'action': 'open',
     'text': "The slab grinds down into the floor. Behind it, a hiding hole."},
    {'id': 'evt:pens_door', 'preset': 'door', 'source': 'door:pens', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:moulting_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:moulting', 'once': True,
     'text': "Shed snakeskins hang from poles across the room like washing, grey and papery. In a corner stands a chest of things that once belonged to people.",
     'seconds': 6},
    {'id': 'evt:pens_seen', 'preset': 'text', 'trigger': 'step', 'source': 'plate:pens_entry', 'once': True,
     'condition': {'not': {'qbit': 'q_c5_done'}},
     'text': "Three barred cages stand against the west wall. The people in them are half turned: scales on their arms, eyes gone yellow. One whispers: \"Don't let them take us down to the machine.\"",
     'seconds': 7},
    {'id': 'evt:cages', 'preset': 'script', 'source': 'mover:cage_gates', 'title': 'Barred cage',
     'condition': {'not': {'qbit': 'q_c5_done'}},
     'else_effects': [{'text': "The cage gates stand open."}],
     'effects': [{'text': "The gates are held by brass wires that run down through the floor to something below. They will not open while it works."}],
     'notes': "The cages open only when the machine dies (evt:transformer opens the gates)."},
    {'id': 'evt:thanks', 'preset': 'script', 'trigger': 'step', 'source': 'room:pens', 'once': True,
     'condition': {'all': [{'qbit': 'q_c5_done'}, {'not': {'qbit': 'townsfolk_thanked'}}]},
     'sets': {'qbit': 'townsfolk_thanked'},
     'effects': [{'message': "The cages stand open. The townsfolk, their scales already flaking away, crowd round you: \"Thank you for saving us!\" Then they hurry up the stair toward the daylight."}],
     'notes': "Adam's line (aaze0031:22), said by the freed townsfolk; next entry they are gone (evt:townsfolk_gone)."},
    {'id': 'evt:brood_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:brood', 'once': True,
     'text': "Straw, shed skin and the reek of snake: the brood hall, where new snake men lie fresh from the machine below.",
     'seconds': 5},
    {'id': 'evt:keeper_door', 'preset': 'door', 'source': 'door:keeper', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:straw_bed', 'preset': 'text', 'source': 'platform:straw_bed', 'title': 'Straw Bed',
     'text': "There is nothing on, in, or under the bed.", 'notes': "Original line and name (aaze0031:12, :15)."},
    {'id': 'evt:field_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:field_gate', 'once': True,
     'text': "A message appears in the stone over the wall of light: Alternate the colors around the well / Then the machine can no longer repel.",
     'seconds': 8, 'notes': "Original line (aaze0031:7): the second rhyme, so the party knows to look round Asp's well."},
    {'id': 'evt:field', 'preset': 'door', 'source': 'door:field', 'title': 'Field of light',
     'condition': {'qbit': 'q_c5_pedestals'}, 'action': 'open',
     'effects': [{'lua': 'XeenQuests.hook("q-c5.field_gate")'}],
     'else_effects': [{'lua': 'XeenQuests.hook("q-c5.field_gate")'}],
     'text': "The coloured light falters, flickers and sinks into the floor with a dying hum.",
     'notes': "link:field_machine. A3's hook q-c5.field_gate: its fail text while the pedestals (q-c5.pedestals 112101, set on X4) are not set; the map opens the leaf."},
    {'id': 'evt:machine_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:machine_hall', 'once': True,
     'text': "The transformer: four bronze coils taller than a man round a chamber of bars, an empty socket shaped like a scarab in its face, and in its crown a cluster of crystals pulsing blue. The floor hums under your feet.",
     'seconds': 8},
    {'id': 'evt:transformer', 'preset': 'script', 'source': 'platform:transformer', 'title': 'Transformer',
     'condition': {'not': {'qbit': 'q_c5_done'}},
     'opens': ['door:crystal', 'mover:cage_gates'],
     'effects': [
         {'lua': 'XeenQuests.hook("q-c5.transformer")'},
         {'lights_off': 'light:machine'},
         {'lights_on': 'light:wreck'},
         {'set_texture': {'of': 'platform:crown', 'to': 'xnrustirn'}},
         {'lua': "evt.SetMapVar('AmbientSound4', 2)"},
     ],
     'else_effects': [{'lua': 'XeenQuests.hook("q-c5.transformer")'}],
     'notes': "goal:transformer. A click destroys it (F47 2026-11-24: no Yes/No; the source asked, aaze0031:4): A3's hook q-c5.transformer (q-c5.done 112102, its text), stops the hum, darkens the crown, opens the crystal housing and the cages upstairs. Later clicks: the hook's else text."},
    {'id': 'evt:crystal_door', 'preset': 'door', 'source': 'door:crystal', 'title': 'Iron door',
     'condition': {'qbit': 'q_c5_done'}, 'action': 'open',
     'else_effects': [{'lua': 'XeenQuests.hook("q-c11.crystals")'}],
     'notes': "link:machine_crystal: shut while the machine works (the hook q-c11.crystals' fail text)."},
    {'id': 'evt:crystals', 'preset': 'script', 'source': 'platform:housing', 'title': 'Crystal housing',
     'effects': [{'lua': 'XeenQuests.hook("q-c11.crystals")'}],
     'notes': "goal:crystals: A3's hook q-c11.crystals gives the Crystals of Piezoelectricity (12313) once and sets crystals_found 112222."},
    {'id': 'evt:drain_reached', 'preset': 'script', 'trigger': 'step', 'source': 'room:drain', 'once': True,
     'effects': [{'set': {'var': {'map_var': 'drain_reached'}, 'value': 1}}],
     'text': "The channel climbs toward a grate. On this side, a heavy bolt holds it.",
     'notes': "Reaching the drain from below makes its bolt reachable (the grate opens from this side first)."},
    {'id': 'evt:grate', 'preset': 'door', 'source': 'door:grate', 'title': 'Drain grate',
     'condition': {'map_var': 'drain_reached'}, 'action': 'open',
     'locked_text': "An iron grate over a drain, bolted fast from the other side.",
     'text': "You draw the bolt and the grate swings up.",
     'notes': "link:drain_pens: bolted from below; once opened, both ways."},
]
for n in range(1, 4):
    pass
for name, ids in [('chest:moulting', 'evt:chest_moulting'), ('chest:cache', 'evt:chest_cache'), ('chest:keeper', 'evt:chest_keeper')]:
    events.append({'id': ids, 'preset': 'chest', 'source': name, 'title': 'Chest'})
wiring = {'format': 0, 'variables': ['drain_reached', 'in_visit'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd25', 'name': 'Asp Undercroft', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'XD-25', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [12, 13], 'climbs': 'n'},
    'map_stats': {'id': 9148, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 3,
                  'perception_difficulty': 6, 'refill_days': 672, 'music': 44, 'environment': 'stone hall',
                  'lock_difficulty': 6, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Snake Man', 'tier': 2, 'per_marker': [2, 3], 'weight': 100}]},
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: the Asp Undercroft under the town of Asp on X4 (Q-C5 The Snakes of Asp, Q-C11 the Crystals of Piezoelectricity). Monsters: A2's Snake men (slot 1 Xeen Snake Man: A Snake Man 11500 16, B Snake Warrior 11501 20; placed Snake Lords 11502 26 in the machine hall and the keeper's cell); the caged townsfolk engine peasants 358, 352, 355. Map qbits 110840-110879 (used: townsfolk_thanked 110840); A3's q-c5.pedestals 112101, q-c5.done 112102 and q-c11.crystals_found 112222 read by name. Hooks q-c5.field_gate, q-c5.transformer, q-c11.crystals called from lua effects. Music 44. No neighbour: X4 is not built, so the cellar door up to Asp is sealed (panel:asp_door) and the map's start is the arrival from X4's door:xd25.",
}

if X4_IN:
    project['neighbours'] = [
        {'id': 'exit:asp_square', 'to': X4_STEM, 'kind': 'door', 'arrival': X4_ARRIVAL,
         'arrival_hint': "On Asp's square on X4, in front of the undercroft hatch (door:xd25), facing away from it.",
         'direction': 270,
         'notes': "A5's points (briefs/x4/DOORS.md); X4's door:xd25 arrives here at the map's start (-2208, 1760, 256) "
                  "facing east."}]

PROJECT_LEVEL = dict(project)
PROJECT_LEVEL.pop('qbits')


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
        p['notes'] = f"Xeen design brief, level {lv}: XD-25 Asp Undercroft (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-25 Asp Undercroft, the plan and the to-scale shell (rooms.yml)."
    shell = dict(rooms_doc)
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', shell)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM)])
print('written L4')
