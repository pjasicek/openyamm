#!/usr/bin/env python3
"""XD-24 Nightshadow Crypt: writes the L1-L4 project folders of devdocs/xeen/briefs/xd24 (agent:xeen-a7-xd24).

  gen.py            L4: rooms.yml, objects.yml, wiring.yml, project.yml, plan.yml, diagram.txt
  gen.py --levels   L1 (plan, project, diagram), L2 (the same at L2), L3 (plan and the shell rooms.yml)

Rerun after every change here (level_generation/projects/xeen/xd24/cycle.sh); never hand-edit the written files.

Frame: x east, y north, z up. Three floors (MU-6 graph devdocs/xeen/mockups/act3_graphs/xd24.graph.yml, D-25):
  z 0      the town's crypt under Nightshadow's square: the coffin stair and its foot (the party's arrival from X3's
           thing:coffin_open, the exit back up), the ossuary, the gnome niches, the night chapel, the sexton's room;
  z -640   the Count's catacombs: west catacomb (the chapel stair's foot), Draco's gallery, east catacomb, feast hall;
  z -1280  Draco's resting vault behind the iron night door at the vault stair's foot, and the Count's own stair (a
           secret ramp, opened by his death) back up to the stair foot.
Rooms stand 128 apart (the walls' thickness). One texture family (MM7's grey castle stone cnb, Castle Navan's 7d15
kit: t3s2fl flags, cndl doors) on the crypt floor; the catacombs in the browner cwb brick with MM8's loculi (d2niche);
the Count's own rooms the same cnb stone on dark slabs (7tfb11) dressed with his portraits, plate and candles.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
BRIEF = R / 'devdocs/xeen/briefs/xd24'

# X3 (installed, lane A5, briefs/x3/DOORS.md): thing:coffin_open on Nightshadow's square (click face 17664, -4608, 992)
# leads in to this map's start; the coffin stair's top leads out to (17664, -5888, 992) facing south (1536).
X3_STEM = 'xeen_x3.odm'
X3_ARRIVAL = [17664, -5888, 992]  # F45 (2026-11-24): 0.75 cell south of the coffin's foot and its plinth

# New textures (output/studio_cal/xd24/tex, xtex.py): the Count's portrait and the chapel's painted moon window.
# Until they are installed in the scratch root the shipped stand-ins are used (NEW=0).
NEW = '--standin' not in sys.argv
PORTRAIT = 'xdracoport' if NEW else 'cnbport-2'
MOONWIN = 'xmoonwin' if NEW else 'cnbw'


def S(t, w=None, h=None, **kw):
    d = {'texture': t}
    if w is not None:
        d['size'] = [w, h]
    d.update(kw)
    return d


CNB = S('cnb', 128, 256)                 # grey castle stone (walls of the crypt and the Count's rooms)
CNB_S = S('cnb1s', 128, 256)             # the same stone with a lintel course (stair risers, plinths)
FLAGS = S('t3s2fl', 128, 128)            # grey flagstones
SLABS = S('7tfb11', 128, 128)            # dark slabs: the Count's floors, ceilings, altar
BRICK = S('cwb', 128, 256)               # the catacombs' older brick
ROUGH = S('cwb1', 128, 256)              # rough vaults over the catacombs
NICHE_EMPTY = S('d2niche3', 256, 256)    # loculi (MM8): empty, bones, bones, sealed
NICHES = ['d2niche1', 'd2niche2', 'd2niche4']
BONES = S('xobones', 128, 256)           # the ossuary's stacked bones (Xeen kit)
DOOR = S('cndl', 128, 256, fit=True)     # an oak door in a stone arch (7d15's own)
IRON = S('t5d1', 128, 256, fit=True)     # the iron door with the Count's gilt symbols
PLANK = S('7trimd', 128, 256)            # coffin wood, the feast table

themes = [
    {'id': 'theme:crypt', 'wall': CNB, 'floor': FLAGS, 'ceiling': CNB, 'door': DOOR, 'reveal': CNB,
     'notes': "The town's crypt: MM7's grey castle stone (cnb, Castle Navan's dungeon 7d15) on grey flags (t3s2fl)."},
    {'id': 'theme:catacomb', 'wall': BRICK, 'floor': FLAGS, 'ceiling': ROUGH, 'door': DOOR, 'reveal': BRICK,
     'notes': "The Count's catacombs: older brick (cwb) under rough vaults (cwb1), loculi panels (d2niche) in the walls."},
    {'id': 'theme:count', 'wall': CNB, 'floor': SLABS, 'ceiling': SLABS, 'door': DOOR, 'reveal': CNB,
     'notes': "The Count's own rooms: the same grey stone on dark slabs (7tfb11), dressed with his portraits."},
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


# ------------------------------------------------------------------------------------------------ the crypt (z 0)
FOOT = (-448, 0, 448, 1024)
COFFIN_STAIR = (-192, 1152, 192, 1920)
OSSUARY = (-1920, 0, -640, 1280)
NICHES_R = (-1920, -640, 512, -128)
CHAPEL = (-3264, -640, -2048, 1152)
SEXTON = (-4096, 384, -3456, 1024)
CHAPEL_STAIR = (-2880, -1920, -2496, -768)
# ------------------------------------------------------------------------------------------------ the catacombs (z -640)
CATA_W = (-3072, -4352, -2432, -2048)
GALLERY = (-2304, -2944, -256, -2048)
CATA_E = (-896, -4352, -256, -3072)
FEAST = (-2304, -4352, -1024, -3072)
VAULT_STAIR = (-128, -2688, 1024, -2304)
# ------------------------------------------------------------------------------------------------ the vault (z -1280)
VAULT = (1152, -3456, 3072, -1536)
COUNT_PATH = [[2048, -1408, -1280], [2048, -1152, -1280], [2048, 512, -384], [576, 512, 0]]
RECTS.update({'room:stair_foot': FOOT, 'room:coffin_stair': COFFIN_STAIR, 'room:ossuary': OSSUARY,
              'room:chapel': CHAPEL, 'room:sexton': SEXTON, 'room:chapel_stair': CHAPEL_STAIR,
              'room:cata_w': CATA_W, 'room:gallery': GALLERY, 'room:cata_e': CATA_E, 'room:feast_hall': FEAST,
              'room:vault_stair': VAULT_STAIR, 'room:draco_vault': VAULT})

room('room:stair_foot', 'Coffin stair foot', FOOT, floor=0, ceiling=512, theme='theme:crypt',
     ambient=20,
     notes="The foot of the stair from Draco's coffin on Nightshadow's square, 896 by 1,024: old earth and candle "
           "stubs. The party arrives here from X3 and leaves up the coffin stair (north). The ossuary west, the "
           "niches south, the Count's secret stair (once he is dead) east. No monsters (D-11.3).")
room('room:coffin_stair', 'Coffin stair', COFFIN_STAIR, floor=0,
     slope={'to': 384, 'toward': 'north', 'steps': 12, 'riser': CNB_S, 'tread': FLAGS},
     ceiling=512, ceiling_slope={'to': 896, 'toward': 'north'}, theme='theme:crypt', ambient=22,
     notes="Twelve steps of 32 up north to the underside of Draco's coffin on the square (the way out to X3).")
room('room:ossuary', 'Town ossuary', OSSUARY, floor=0, ceiling=576, theme='theme:crypt',
     walls=[{'wall': 'north', 'surface': BONES}, {'wall': 'south', 'surface': BONES}],
     platforms=[
         block('platform:bone_shelf_w', [-1664, 1200], [384, 160], 160, BONES, top=FLAGS,
               notes="Skulls stacked on a stone shelf against the north wall (F3, 2026-11-21: 160 deep, flush with "
                     "the wall; it stood 32 off it)."),
         block(None, [-896, 1200], [384, 160], 160, BONES, top=FLAGS, notes="More of Nightshadow's dead."),
     ],
     ambient=16,
     notes="Nightshadow's dead, 1,280 square, the bones stacked to the vault along the north and south walls; gnome "
           "vampires sleeping among them (two pairs, D-25). The stair foot east, the chapel's door west.")
NICHE_X = [-1600, -1152, -704, -256, 192]


def niches_outline():
    x0, y0, x1, y1 = NICHES_R
    pts = [[x0, y0]]
    for cx in NICHE_X:
        pts += [[cx - 128, y0], [cx - 128, y0 - 192], [cx + 128, y0 - 192], [cx + 128, y0]]
    pts += [[x1, y0], [x1, y1], [x0, y1]]
    return pts


RECTS['room:niches'] = NICHES_R
rooms.append({
    'id': 'room:niches', 'name': 'Gnome niches', 'outline': niches_outline(), 'floor': 0, 'ceiling': 384,
    'theme': 'theme:crypt',
    'platforms': [block(f'platform:coffin_{i + 1}' if i in (0, 2, 4) else None, [cx, -768], [192, 96], 64, CNB_S,
                        top=PLANK, notes="A gnome-sized coffin in its niche, the lid pushed aside.")
                  for i, cx in enumerate(NICHE_X)],
    'ambient': 14,
    'notes': "A corridor 2,432 long and 512 wide under the square: five niches in its south wall, each with a small "
             "coffin whose lid is ajar ('The coffin is empty.', aaze0029:3). Their owners are up: two and three gnome "
             "vampires (D-25). The stair foot north-east, the chapel west."})
room('room:chapel', 'Night chapel', CHAPEL, floor=0, ceiling=768, theme='theme:crypt',
     ceiling_levels=[{'ceiling': 1088, 'top_scale': 0.35}],
     walls=[{'wall': 'north', 'panels': [
         panel('room:chapel', 'north', 'panel:moon', -2688, 256, 256, 384, S(MOONWIN, 128, 256, fit=True),
               "The moon window painted on the wall over the black altar."),
         panel('room:chapel', 'north', None, -3072, 192, 192, 192, S('d2skulas', 64, 64, fit=True)),
         panel('room:chapel', 'north', None, -2304, 192, 192, 192, S('d2skulas', 64, 64, fit=True)),
     ]}],
     platforms=[block('platform:altar', [-2688, 992], [512, 160], 96, SLABS, top=SLABS,
                      notes="The black altar against the north wall, under the painted moon.")],
     ambient=14,
     notes="The town's burial chapel turned to the moon, 1,216 by 1,792, its roof rising to a point: a black altar "
           "under a moon window painted on the north wall, carved skulls either side. The ossuary's door and the "
           "niches open in the east wall, the sexton's door in the west, the stair down in the south.")
room('room:sexton', "Sexton's room", SEXTON, floor=0, ceiling=384, theme='theme:crypt',
     platforms=[block('platform:bed', [-3584, 896], [192, 224], 48, PLANK, top=S('7tfb11', 128, 128),
                      notes="The sexton's cot in the north-east corner.")],
     ambient=18,
     notes="A dead end, 640 square: the old sexton's cot and his lockbox of burial fees, untouched since he was bitten.")
room('room:chapel_stair', 'Chapel stair', CHAPEL_STAIR, floor=0,
     slope={'to': -640, 'toward': 'south', 'steps': 20, 'riser': CNB_S, 'tread': FLAGS},
     ceiling=448, ceiling_slope={'to': -192, 'toward': 'south'}, theme='theme:crypt', ambient=22,
     notes="Twenty steps of 32 down south from the chapel into the Count's catacombs.")


def loculi(rid, wall, starts, row=0):
    """Loculi panels (d2niche1/2/4) in a catacomb wall at 256-unit steps from the wall's start."""
    out = []
    for i, o in enumerate(starts):
        out.append({'offset': o, 'length': 256, 'bottom': 0, 'height': 256,
                    'surface': S(NICHES[(i + row) % 3], 256, 256, fit=True)})
    return out


room('room:cata_w', 'West catacomb', CATA_W, floor=-640, ceiling=-192, theme='theme:catacomb',
     walls=[{'wall': 'west', 'surface': NICHE_EMPTY, 'panels': loculi('room:cata_w', 'west', [256, 768, 1280, 1792])},
            {'wall': 'east', 'surface': NICHE_EMPTY}],
     ambient=12,
     notes="Loculi three high in both long walls, 640 by 2,304: the chapel stair arrives at its north end; Draco's "
           "gallery opens east, the feast hall's door further south.")
room('room:gallery', "Draco's gallery", GALLERY, floor=-640, ceiling=0, theme='theme:count',
     ceiling_levels=[{'ceiling': 192, 'top_scale': 0.5}],
     walls=[{'wall': 'north', 'panels': [
                panel('room:gallery', 'north', 'panel:portrait_1' if i == 1 else None, x, 256, 96, 384,
                      S(PORTRAIT, 128, 256, fit=True)) for i, x in enumerate([-1920, -1280, -640])]},
            {'wall': 'south', 'panels': [
                panel('room:gallery', 'south', None, x, 256, 96, 384, S(PORTRAIT, 128, 256, fit=True))
                for x in [-1920, -1280]]}],
     ambient=14,
     notes="The set piece on the way down, 2,048 by 896, 640 high under a low hipped roof: the Count's portraits down "
           "both long walls, the same pale face in every frame, centuries apart. The west catacomb west, the east "
           "catacomb south, the vault stair east.")
room('room:cata_e', 'East catacomb', CATA_E, floor=-640, ceiling=-192, theme='theme:catacomb',
     walls=[{'wall': 'east', 'surface': NICHE_EMPTY, 'panels': loculi('room:cata_e', 'east', [0, 512, 1024], row=1)},
            {'wall': 'west', 'surface': NICHE_EMPTY}],
     platforms=[block(None, [-384, -4224], [192, 160], 48, ROUGH, top=ROUGH, notes="A collapsed loculus: rubble.")],
     ambient=12,
     notes="Older loculi, collapsed in places, 640 by 1,280: a draught from the feast hall's door.")
room('room:feast_hall', "The Count's feast hall", FEAST, floor=-640, ceiling=-64, theme='theme:count',
     walls=[{'wall': 'south', 'panels': [panel('room:feast_hall', 'south', None, -1664, 256, 96, 384,
                                               S(PORTRAIT, 128, 256, fit=True))]}],
     platforms=[block('platform:table', [-1600, -4000], [768, 224], 72, PLANK, top=SLABS,
                      notes="A long table laid for guests who never left.")],
     ambient=14,
     notes="1,280 by 1,280: a long table laid for guests who never left, the Count's portrait at its foot; the silver "
           "plate in a chest at the head of the table. Doors west (west catacomb) and east (east catacomb), both "
           "along the north side so the table is off the walking line.")
room('room:vault_stair', 'Vault stair', VAULT_STAIR, floor=-1280,
     slope={'to': -640, 'toward': 'west', 'steps': 20, 'riser': CNB_S, 'tread': SLABS},
     ceiling=-768, ceiling_slope={'to': -128, 'toward': 'west'}, theme='theme:count',
     walls=[{'wall': 'east', 'panels': [panel('room:vault_stair', 'east', 'panel:sign_night', -2496, 256, 384, 96,
                                              S('cnb1s', 128, 256),
                                              "Cut over the iron door: 'Only at night can you put up a fight.'")]}],
     ambient=16,
     notes="Twenty steps of 32 down east from the gallery to the iron door with the Count's symbol (open only by "
           "night, D-25 Q1). No monsters: the party may rest here until 21:00.")
room('room:draco_vault', "Draco's resting vault", VAULT, floor=-1280, ceiling=-512, theme='theme:count',
     ceiling_levels=[{'ceiling': 0, 'top_scale': 0.3}],
     walls=[{'wall': 'south', 'panels': [panel('room:draco_vault', 'south', None, 2048, 256, 128, 384,
                                               S(PORTRAIT, 128, 256, fit=True))]}],
     levels=[{'id': 'level:dais', 'outline': rect(1536, -2432, 2560, -1856), 'floor': -1248,
              'edge': CNB_S, 'surface': SLABS}],
     platforms=[block('platform:sarcophagus', [2048, -2144], [224, 448], 112, CNB_S, top=SLABS,
                      notes="The Count's great sarcophagus on the dais; the rhyme cut into its foot.")],
     beams=[{'path': [[1152, -2432], [3072, -2432]], 'width': 48, 'depth': 48, 'bottom': -560,
             'surface': CNB_S, 'notes': "A rib across the vault."},
            {'path': [[2048, -3456], [2048, -2456]], 'width': 48, 'depth': 48, 'bottom': -560,
             'surface': CNB_S, 'notes': "A rib along the vault (south half)."},
            {'path': [[2048, -2408], [2048, -1536]], 'width': 48, 'depth': 48, 'bottom': -560,
             'surface': CNB_S, 'notes': "A rib along the vault (north half)."}],
     ambient=10,
     notes="The deepest room, 1,920 square at 1,280 under the square, under a hipped ribbed vault rising to 1,280: "
           "the great sarcophagus on a dais (a step of 32), Count Draco and two of his household. His hoard (tier 4) "
           "by the north wall. The iron door west; the Count's stair behind the dais, in the north wall (secret, "
           "opened by his death).")
rooms.append({
    'id': 'room:count_stair', 'name': "The Count's stair", 'path': COUNT_PATH, 'width': 320, 'floor': -1280,
    'ceiling': -896, 'theme': 'theme:crypt', 'ambient': 22,
    'notes': "The Count's own way up: a narrow ramp from behind his dais, 1,280 up to the stair foot (a level start, "
             "1,664 north climbing 896, a turn west climbing the last 384). Shut at both ends by secret slabs that his "
             "death opens: a shortcut both ways once he is dead (D-25, D-33 (1))."})

# Openings: centred on the stretch the two walls share unless `along` says another.
op('open:foot_coffin', 'room:stair_foot', 'room:coffin_stair', width=320, height=320, link='link:coffin_stair')
op('open:foot_ossuary', 'room:stair_foot', 'room:ossuary', width=384, height=352, shape='arch', apex=432,
   link='link:foot_ossuary')
op('open:foot_niches', 'room:stair_foot', 'room:niches', width=384, height=320, link='link:foot_niches')
op('open:ossuary_chapel', 'room:ossuary', 'room:chapel', width=192, height=320, link='link:ossuary_chapel')
op('open:niches_chapel', 'room:niches', 'room:chapel', width=384, height=320, link='link:niches_chapel')
op('open:chapel_sexton', 'room:chapel', 'room:sexton', width=192, height=320, link='link:chapel_sexton')
op('open:chapel_stair', 'room:chapel', 'room:chapel_stair', width=320, height=320, link='link:chapel_cataw')
op('open:stair_cataw', 'room:chapel_stair', 'room:cata_w', width=320, height=320, link='link:chapel_cataw')
op('open:cataw_gallery', 'room:cata_w', 'room:gallery', width=384, height=384, link='link:cataw_gallery')
op('open:gallery_catae', 'room:gallery', 'room:cata_e', width=384, height=384, link='link:gallery_catae')
op('open:cataw_feast', 'room:cata_w', 'room:feast_hall', width=192, height=320, along=0.83,
   link='link:feast_cataw')
op('open:feast_catae', 'room:feast_hall', 'room:cata_e', width=192, height=320, along=0.83,
   link='link:catae_feast')
op('open:gallery_vstair', 'room:gallery', 'room:vault_stair', width=320, height=320, link='link:gallery_vstair')
op('open:vault_door', 'room:vault_stair', 'room:draco_vault', width=256, height=352, link='link:vault_door')
op('open:vault_count', 'room:draco_vault', 'room:count_stair', width=256, height=320, link='link:private_stair')
op('open:count_foot', 'room:count_stair', 'room:stair_foot', width=256, height=320, link='link:private_stair')

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:crypt', 'ambient': 16}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-24 Nightshadow Crypt: the town's crypt at z 0, the Count's catacombs at -640, his vault at "
                      "-1280; x east, y north. Written by output/studio_cal/xd24/tools/gen.py."}

# ================================================================================================ plan.yml
FLOORS = {0: ['room:stair_foot', 'room:coffin_stair', 'room:ossuary', 'room:niches', 'room:chapel', 'room:sexton',
              'room:chapel_stair'],
          -640: ['room:cata_w', 'room:gallery', 'room:cata_e', 'room:feast_hall', 'room:vault_stair'],
          -1280: ['room:draco_vault', 'room:count_stair']}
PLAN_SPACES = [
    ('room:stair_foot', 'Coffin stair foot', 'room', 'S', "The foot of the stair from Draco's coffin on the square; old earth, candle stubs. No monsters (D-11.3).", []),
    ('room:coffin_stair', 'Coffin stair', 'corridor', 'S', "Up to the underside of Draco's coffin: the way out to X3.", []),
    ('room:ossuary', 'Town ossuary', 'room', 'M', "Nightshadow's dead, skulls stacked to the vault; gnome vampires sleeping among the bones.", [(0, 2, 2)]),
    ('room:niches', 'Gnome niches', 'corridor', 'M', "Rows of small coffins in wall niches, lids ajar: 'The coffin is empty.' Their owners are up.", [(0, 1, 2), (0, 1, 3)]),
    ('room:chapel', 'Night chapel', 'room', 'M', "The town's burial chapel turned to the moon: a black altar, a moon window painted on the wall; the stair down.", [(0, 1, 3)]),
    ('room:sexton', "Sexton's room", 'room', 'S', "The old sexton's bed and his lockbox of burial fees, untouched since he was bitten.", []),
    ('room:chapel_stair', 'Chapel stair', 'corridor', 'S', "Down from the chapel to the Count's catacombs.", []),
    ('room:cata_w', 'West catacomb', 'corridor', 'M', "Loculi three high; the chapel stair arrives here.", [(0, 1, 2)]),
    ('room:gallery', "Draco's gallery", 'room', 'M', "Portraits of the Count down the centuries, the same face in every one; the vault stair at its end.", [(1, 1, 1)]),
    ('room:cata_e', 'East catacomb', 'corridor', 'M', "Older loculi, collapsed in places; a draught from the feast hall.", [(0, 1, 2)]),
    ('room:feast_hall', "The Count's feast hall", 'room', 'M', "A long table laid for guests who never left; silver plate in a chest at the head of the table.", [(1, 1, 2)]),
    ('room:vault_stair', 'Vault stair', 'corridor', 'S', "Down from the gallery to an iron door with the Count's symbol, open only by night. Empty: the party may rest here until 21:00.", []),
    ('room:draco_vault', "Draco's resting vault", 'room', 'L', "A ribbed vault, the great sarcophagus on a dais; Count Draco and two of his household. His hoard (tier 4).", [(1, 1, 2)]),
    ('room:count_stair', "The Count's stair", 'corridor', 'S', "A secret ramp behind the dais up to the stair foot, opened by the Count's death.", []),
]
LEVELS = {0: [32, 32], 1: [40, 40]}
NIGHT = {'lua': 'Xeen.isNight()'}


def plan_doc(level):
    spaces = []
    for sid, name, kind, size, purpose, pops in PLAN_SPACES:
        z = next(z for z, ids in FLOORS.items() if sid in ids)
        s = {'id': sid, 'name': name, 'kind': kind, 'size': size, 'floor': z, 'purpose': purpose}
        if pops:
            s['population'] = [{'slot': t + 1, 'groups': g, 'per_marker': [n, n], 'levels': LEVELS[t],
                                'notes': f"{n} {'Gnome Vampire' if t == 0 else 'Vampire'}{'s' if n > 1 else ''} placed."}
                               for t, g, n in pops]
            if sid == 'room:draco_vault':
                s['population'].insert(0, {'slot': 2, 'groups': 1, 'per_marker': [1, 1], 'levels': [45, 45],
                                           'notes': "Count Draco (A2's boss row 11293), placed."})
        else:
            s['empty'] = True
        spaces.append(s)
    links = [
        {'id': 'link:coffin_stair', 'from': 'room:stair_foot', 'to': 'room:coffin_stair', 'kind': 'stairs'},
        {'id': 'link:foot_ossuary', 'from': 'room:stair_foot', 'to': 'room:ossuary', 'kind': 'open'},
        {'id': 'link:foot_niches', 'from': 'room:stair_foot', 'to': 'room:niches', 'kind': 'open'},
        {'id': 'link:ossuary_chapel', 'from': 'room:ossuary', 'to': 'room:chapel', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:niches_chapel', 'from': 'room:niches', 'to': 'room:chapel', 'kind': 'open'},
        {'id': 'link:chapel_sexton', 'from': 'room:chapel', 'to': 'room:sexton', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:chapel_cataw', 'from': 'room:chapel', 'to': 'room:cata_w', 'kind': 'stairs'},
        {'id': 'link:cataw_gallery', 'from': 'room:cata_w', 'to': 'room:gallery', 'kind': 'open'},
        {'id': 'link:gallery_catae', 'from': 'room:gallery', 'to': 'room:cata_e', 'kind': 'open'},
        {'id': 'link:catae_feast', 'from': 'room:cata_e', 'to': 'room:feast_hall', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:feast_cataw', 'from': 'room:feast_hall', 'to': 'room:cata_w', 'kind': 'door', 'motion': 'swing'},
        {'id': 'link:gallery_vstair', 'from': 'room:gallery', 'to': 'room:vault_stair', 'kind': 'stairs'},
        {'id': 'link:vault_door', 'from': 'room:vault_stair', 'to': 'room:draco_vault', 'kind': 'door',
         'motion': 'swing',
         'notes': "The iron door: it opens at any hour (D-89, orchestrator 2026-11-22: the vault follows the outer "
                  "door, no night condition; was D-25 Q1). Once opened (vault_open) it stays open."},
        {'id': 'link:private_stair', 'from': 'room:draco_vault', 'to': 'room:stair_foot', 'kind': 'secret_door',
         'motion': 'sink', 'one_way': True, 'condition': {'qbit': 'draco_done'},
         'notes': "The Count's stair behind the dais, opened by his death (a kill timer, A3's q-c7.draco)."},
    ]
    doc = {
        'format': 0, 'level': level if level != 'L4' else 'L3',
        'pitch': "The crypt under Nightshadow's square, entered down the stair in Count Draco's own coffin. The town's crypt on top (the ossuary, niches of gnome-sized coffins, the burial chapel turned to the moon), the Count's catacombs below with the gallery of his portraits and his feast hall, and his resting vault at the bottom behind an iron door that opens only by night. Back up the Count's own stair once he is dust.",
        'purpose': "Q-C7 The Count of Nightshadow (A3's q-c7.draco sets q-c7.done 112141: Nightshadow liberated; Du Monay's Nosferatu promotion). Party 25-29, monsters 32-40 (Gnome Vampire 32, Vampire 40), Count Draco 45.",
        'mood': "Cold grey stone, candle stubs, bones stacked to the vault; below, brown loculi and the Count's portraits, the same pale face in every frame; at the bottom a ribbed vault and a black sarcophagus.",
        'datum': 'arrival',
        'spaces': spaces, 'links': links,
        'loops': [
            {'id': 'loop:square', 'spaces': ['room:stair_foot', 'room:ossuary', 'room:chapel', 'room:niches'],
             'notes': "Round the town's crypt: ossuary or niches to the chapel."},
            {'id': 'loop:catacombs', 'spaces': ['room:cata_w', 'room:gallery', 'room:cata_e', 'room:feast_hall'],
             'notes': "Round the catacombs through the feast hall."},
            {'id': 'loop:count_stair', 'spaces': ['room:stair_foot', 'room:chapel', 'room:cata_w', 'room:gallery',
                                                  'room:vault_stair', 'room:draco_vault', 'room:count_stair'],
             'closed_until': {'qbit': 'draco_done'},
             'notes': "Down through the crypt, back up the Count's own stair once he is dead."},
        ],
        'entrances': [{'id': 'entrance:x3_coffin', 'space': 'room:stair_foot', 'kind': 'both', 'facing': 's',
                       'neighbour': 'exit:x3_coffin',
                       'how': "From X3's open coffin on Nightshadow's square (thing:coffin_open) to the stair foot; the coffin stair leads back up (the exit preset, D-24)."}],
        'critical_path': ['room:stair_foot', 'room:ossuary', 'room:chapel', 'room:chapel_stair', 'room:cata_w',
                          'room:gallery', 'room:vault_stair', 'room:draco_vault'],
        'goals': [{'id': 'goal:draco', 'space': 'room:draco_vault', 'kind': 'kill', 'story': 'Q-C7',
                   'what': "Count Draco (A2's boss row 11293, level 45): his death runs A3's q-c7.draco.",
                   'gives': {'qbit': 'draco_done'}}],
        'keys': [],
        'points_of_interest': [
            {'id': 'poi:sarcophagus', 'space': 'room:draco_vault', 'kind': 'inscription',
             'behaviour': "The rhyme's second half on the sarcophagus's foot (aaze0029:8)."},
            {'id': 'poi:portraits', 'space': 'room:gallery', 'kind': 'set_piece',
             'behaviour': "The same face in every portrait: the Count before he is met."},
            {'id': 'poi:niches', 'space': 'room:niches', 'kind': 'coffins',
             'behaviour': "'The coffin is empty.' (aaze0029:3)"},
        ],
        'states': [
            {'id': 'state:draco', 'condition': {'qbit': 'draco_done'}, 'opens': ['link:private_stair'],
             'notes': "Count Draco dead: A3's q-c7.draco (q-c7.done 112141, 10,000 experience); the Count's stair opens."},
        ],
        'diagram': {'file': 'diagram.txt'},
        'totals': {'rooms': 14, 'sectors': 14, 'monsters_about': 22, 'chests': 3, 'doors': 7, 'loops': 3,
                   'floor_area_munits2': 19},
        'notes': "Size S (MAPS: at most 15 sectors and 20 M units², 15-30 monsters, 0-3 chests, 3-8 doors). From the MU-6 graph devdocs/xeen/mockups/act3_graphs/xd24.graph.yml and D-25 (mockups/act3_a7_decisions.md): the iron door night-only and open once opened, ossuary 2+2, niches 2+3, the first room and the vault stair empty, the Count's stair one way back up. Rooms 11 of the graph plus the coffin stair, the chapel stair and the Count's stair as their own sectors.",
    }
    if level in ('L3', 'L4'):
        doc['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return doc


DIAGRAM = """XD-24 Nightshadow Crypt (not to scale; north up).

  z 0, the town's crypt                       (X3: Draco's coffin on the square)
                                                    [coffin stair] = exit up
   [sexton]=door=[NIGHT CHAPEL]=door=[ossuary]--arch--[STAIR FOOT]==(secret: the Count's stair, after Draco)
                   | altar, moon    '--open--[gnome niches]--open--'
                   | stair down
  z -640, the catacombs
               [west catacomb]--arch--[DRACO'S GALLERY]--stair down-->
                     |door                  |open
               [feast hall]------door---[east catacomb]
  z -1280                                      --> [vault stair]=IRON DOOR (night)=[DRACO'S VAULT]
                                                                      dais, sarcophagus, hoard
                                                    [the Count's stair] secret, up to the stair foot
"""

# ================================================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:coffin_stair', 'at': [0, 1600], 'facing': 270,
                    'notes': "F45 (2026-11-24): on the coffin stair, facing down into the crypt (south), out of the "
                             "Gnome Vampires' sight and 380 from the exit: where X3's open coffin (thing:coffin_open) "
                             "arrives (X3's `into`: 0, 1600, 224 facing south, 1536)."}
objects['exits'] = [
    {'id': 'exit:coffin', 'room': 'room:coffin_stair', 'wall': 'north', 'size': [256, 352],
     'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x3_coffin',
     'notes': "The top of the coffin stair: up through Draco's open coffin to Nightshadow's square (X3)."}]
objects['doors'] = [
    {'id': 'door:ossuary', 'opening': 'open:ossuary_chapel', 'kind': 'hinged', 'thickness': 16, 'surface': DOOR,
     'notes': "The chapel's door from the ossuary."},
    {'id': 'door:sexton', 'opening': 'open:chapel_sexton', 'kind': 'hinged', 'thickness': 16, 'surface': DOOR,
     'notes': "The sexton's door."},
    {'id': 'door:feast_w', 'opening': 'open:cataw_feast', 'kind': 'hinged', 'thickness': 16, 'surface': DOOR,
     'notes': "The feast hall's west door."},
    {'id': 'door:feast_e', 'opening': 'open:feast_catae', 'kind': 'hinged', 'thickness': 16, 'surface': DOOR,
     'notes': "The feast hall's east door."},
    {'id': 'door:iron', 'opening': 'open:vault_door', 'kind': 'hinged', 'thickness': 24, 'speed': 96,
     'surface': IRON, 'back_surface': IRON,
     'notes': "The iron door with the Count's symbol: opens only by night (D-25 Q1), stays open once opened."},
    {'id': 'door:count_base', 'opening': 'open:vault_count', 'kind': 'slide_down', 'thickness': 32, 'speed': 200,
     'tile': True, 'surface': CNB, 'back_surface': CNB,
     'notes': "A slab of the wall behind the dais (drawn as the wall, no secret flag: the stair is found by his death, not by Perception): sinks when Count Draco dies."},
    {'id': 'door:count_top', 'opening': 'open:count_foot', 'kind': 'slide_down', 'thickness': 32, 'speed': 200,
     'tile': True, 'surface': CNB, 'back_surface': CNB,
     'notes': "A slab of the stair foot's east wall, drawn as the wall: sinks when Count Draco dies."},
]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


FIRE = [255, 190, 120]
CANDLE = [255, 170, 100]
MOON = [170, 185, 230]
COLD = [160, 170, 200]
objects['lights'] = [
    light('light:foot', 'room:stair_foot', [0, 512], 384, 1000, CANDLE),
    light('light:coffin_stair', 'room:coffin_stair', [0, 1536], 600, 700, MOON,
          notes="The night (or day) through Draco's open coffin at the top."),
    light('light:ossuary', 'room:ossuary', [-1280, 640], 420, 1100, FIRE),
    light('light:niches_w', 'room:niches', [-1280, -384], 280, 900, CANDLE),
    light('light:niches_e', 'room:niches', [-128, -384], 280, 900, CANDLE),
    light('light:chapel_moon', 'room:chapel', [-2688, 900], 500, 1200, MOON,
          notes="The painted moon's cold light over the altar."),
    light('light:chapel', 'room:chapel', [-2688, 0], 560, 1300, CANDLE),
    light('light:sexton', 'room:sexton', [-3776, 704], 280, 700, CANDLE),
    light('light:chapel_stair', 'room:chapel_stair', [-2688, -1344], 0, 800, FIRE),
    light('light:cata_w', 'room:cata_w', [-2752, -2816], 320, 1000, COLD),
    light('light:cata_w_s', 'room:cata_w', [-2752, -4000], 320, 900, FIRE),
    light('light:gallery_w', 'room:gallery', [-1792, -2496], 480, 1100, CANDLE),
    light('light:gallery_e', 'room:gallery', [-768, -2496], 480, 1100, CANDLE),
    light('light:cata_e', 'room:cata_e', [-576, -3776], 320, 900, COLD),
    light('light:feast', 'room:feast_hall', [-1600, -3776], 460, 1300, CANDLE),
    light('light:vault_stair', 'room:vault_stair', [448, -2496], 0, 900, [150, 170, 255],
          pulse={'intensity': [0.8, 1], 'frequency': 0.6}, notes="The Count's symbol on the iron door glows faintly."),
    light('light:vault', 'room:draco_vault', [2048, -2496], 640, 1700, [200, 120, 130]),
    light('light:vault_dais', 'room:draco_vault', [2048, -1800], 300, 900, CANDLE),
    light('light:count_stair', 'room:count_stair', [2048, -400], 0, 900, CANDLE),
]
objects['sounds'] = [
    {'id': 'sound:drip_w', 'room': 'room:cata_w', 'at': [-2752, -3584], 'sound': 'drip02', 'radius': 1400,
     'volume': 0.5, 'wait': [3, 9], 'notes': "Water seeping through the catacomb's vault."},
    {'id': 'sound:drip_e', 'room': 'room:cata_e', 'at': [-576, -4096], 'sound': 'drip03', 'radius': 1200,
     'volume': 0.5, 'wait': [4, 11]},
    {'id': 'sound:draught', 'room': 'room:gallery', 'at': [-1280, -2496], 'sound': 'whistling wind', 'radius': 1600,
     'inner_radius': 300, 'volume': 0.35, 'notes': "A draught along the gallery."},
    {'id': 'sound:hum', 'room': 'room:vault_stair', 'at': [768, -2496], 'sound': 'humming', 'radius': 1100,
     'inner_radius': 300, 'volume': 0.4, 'notes': "The Count's symbol hums in the iron door."},
]
objects['chests'] = [
    {'id': 'chest:sexton', 'room': 'room:sexton', 'at': [-4000, 512], 'treasure_level': 3,
     'random_items': 2, 'gold': 600, 'trap_level': 2, 'notes': "The sexton's lockbox of burial fees."},
    {'id': 'chest:feast', 'room': 'room:feast_hall', 'at': [-2192, -4000], 'treasure_level': 3,
     'random_items': 3, 'gold': 900, 'trap_level': 2, 'notes': "The Count's silver plate, at the head of the table."},
    {'id': 'chest:hoard', 'room': 'room:draco_vault', 'at': [2688, -1648], 'treasure_level': 4,
     'random_items': 3, 'gold': 2000, 'trap_level': 3, 'notes': "Draco's hoard (tier 4), by the north wall."},
]

VAMP_A, VAMP_B, DRACO = 11290, 11291, 11293


def mon(id, rm, kind, at, facing, group, **kw):
    d = {'id': id, 'room': rm, 'monster': kind, 'at': at, 'facing': facing, 'hostile': True, 'group': group}
    d.update(kw)
    return d


objects['monsters'] = [
    # the ossuary: two pairs (D-25)
    mon('monster:ossuary_1', 'room:ossuary', VAMP_A, [-1600, 896], 0, 1),
    mon('monster:ossuary_2', 'room:ossuary', VAMP_A, [-1408, 1024], 0, 1),
    mon('monster:ossuary_3', 'room:ossuary', VAMP_A, [-1536, 256], 0, 2),
    mon('monster:ossuary_4', 'room:ossuary', VAMP_A, [-1280, 352], 0, 2),
    # the niches: two and three (D-25)
    mon('monster:niches_1', 'room:niches', VAMP_A, [-1664, -384], 0, 3),
    mon('monster:niches_2', 'room:niches', VAMP_A, [-1472, -448], 0, 3),
    mon('monster:niches_3', 'room:niches', VAMP_A, [-1024, -320], 0, 4),
    mon('monster:niches_4', 'room:niches', VAMP_A, [-896, -480], 0, 4),
    mon('monster:niches_5', 'room:niches', VAMP_A, [-768, -320], 0, 4),
    # the chapel: three
    mon('monster:chapel_1', 'room:chapel', VAMP_A, [-2944, 640], 0, 5),
    mon('monster:chapel_2', 'room:chapel', VAMP_A, [-2688, 768], 0, 5),
    mon('monster:chapel_3', 'room:chapel', VAMP_A, [-2432, 640], 0, 5),
    # the catacombs
    mon('monster:cataw_1', 'room:cata_w', VAMP_A, [-2752, -3264], 90, 6),
    mon('monster:cataw_2', 'room:cata_w', VAMP_A, [-2752, -3520], 90, 6),
    mon('monster:gallery_1', 'room:gallery', VAMP_B, [-1280, -2496], 180, 7,
        notes="One of the Count's household, alone among his portraits."),
    mon('monster:catae_1', 'room:cata_e', VAMP_A, [-576, -3456], 90, 8),
    mon('monster:catae_2', 'room:cata_e', VAMP_A, [-576, -4160], 90, 8),
    mon('monster:feast_1', 'room:feast_hall', VAMP_B, [-1920, -3456], 270, 9),
    mon('monster:feast_2', 'room:feast_hall', VAMP_B, [-1280, -3616], 270, 9),
    # the vault
    mon('monster:vault_1', 'room:draco_vault', VAMP_B, [1664, -2240], 180, 10),
    mon('monster:vault_2', 'room:draco_vault', VAMP_B, [1664, -2752], 180, 10),
    mon('monster:draco', 'room:draco_vault', DRACO, [2048, -2688], 180, 11,
        notes="Count Draco (A2's boss row 11293, level 45, blink on hit); his death runs A3's q-c7.draco."),
]


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


TABLE_TOP = -640 + 72
ALTAR_TOP = 96
objects['decorations'] = [
    torch('deco:foot_torch', 'room:stair_foot', 'west', 0.85),
    deco('deco:foot_candle_2', 'room:stair_foot', 'cndlab0', [352, 96]),
    deco('deco:foot_bones', 'room:stair_foot', 'dec29', [-320, 896]),
    torch('deco:ossuary_torch_e', 'room:ossuary', 'east', 0.85),
    torch('deco:ossuary_torch_w', 'room:ossuary', 'west', 0.15),
    deco('deco:ossuary_skulls_1', 'room:ossuary', 'sklplrev', [-1824, 96]),
    deco('deco:ossuary_skulls_2', 'room:ossuary', 'sklplrev', [-736, 96]),
    deco('deco:ossuary_skull', 'room:ossuary', '7dec20', [-1664, 1226], floor_height=160),
    deco('deco:ossuary_bones', 'room:ossuary', 'dec29', [-1120, 160]),
    deco('deco:niches_bones_1', 'room:niches', 'dec29', [-1152, -768], floor_height=64),
    deco('deco:niches_bones_2', 'room:niches', 'dec29', [192, -768], floor_height=64),
    torch('deco:niches_torch', 'room:niches', 'north', 0.75),
    deco('deco:altar_candle_1', 'room:chapel', 'cndlab0', [-2880, 992], floor_height=ALTAR_TOP),
    deco('deco:altar_candle_2', 'room:chapel', 'cndlab0', [-2496, 992], floor_height=ALTAR_TOP),
    deco('deco:chapel_candles_1', 'room:chapel', 'dec02', [-3136, 1024]),
    deco('deco:chapel_candles_2', 'room:chapel', 'dec02', [-2176, 1024]),
    torch('deco:chapel_torch_s', 'room:chapel', 'south', 0.2),
    torch('deco:sexton_torch', 'room:sexton', 'south', 0.5),
    torch('deco:chapel_stair_torch', 'room:cata_w', 'north', 0.15),
    torch('deco:cataw_torch', 'room:cata_w', 'south', 0.5),
    deco('deco:cataw_bones', 'room:cata_w', 'dec29', [-2960, -2816]),
    torch('deco:gallery_torch_w', 'room:gallery', 'west', 0.2),
    torch('deco:gallery_torch_e', 'room:gallery', 'east', 0.2),
    deco('deco:gallery_candles_1', 'room:gallery', 'dec02', [-1600, -2144]),
    deco('deco:gallery_candles_2', 'room:gallery', 'dec02', [-960, -2144]),
    torch('deco:catae_torch', 'room:cata_e', 'north', 0.2),  # lamp rule: 0.5 stood in the north opening
    deco('deco:catae_bones', 'room:cata_e', 'dec29', [-400, -4200]),
    deco('deco:feast_plates_1', 'room:feast_hall', 'dec39', [-1856, -4000], floor_height=TABLE_TOP),
    deco('deco:feast_plate_1', 'room:feast_hall', 'dec39', [-1600, -4048], floor_height=TABLE_TOP),
    deco('deco:feast_plate_2', 'room:feast_hall', 'dec39', [-1344, -3952], floor_height=TABLE_TOP),
    deco('deco:feast_goblet_1', 'room:feast_hall', '7dec46', [-1728, -3936], floor_height=TABLE_TOP),
    deco('deco:feast_goblet_2', 'room:feast_hall', '7dec48', [-1472, -4064], floor_height=TABLE_TOP),
    deco('deco:feast_candle', 'room:feast_hall', 'cndlab0', [-1600, -3952], floor_height=TABLE_TOP),
    deco('deco:feast_candles_1', 'room:feast_hall', 'dec02', [-2176, -4224]),
    deco('deco:feast_candles_2', 'room:feast_hall', 'dec02', [-1152, -4224]),
    torch('deco:feast_torch', 'room:feast_hall', 'north', 0.5),
    torch('deco:vstair_torch', 'room:vault_stair', 'north', 0.3),
    deco('deco:vault_candles_1', 'room:draco_vault', 'dec02', [1344, -1728]),
    deco('deco:vault_candles_2', 'room:draco_vault', 'dec02', [2880, -3264]),
    deco('deco:vault_candle_1', 'room:draco_vault', 'cndlab0', [1696, -1952], floor_height=-1248),
    deco('deco:vault_candle_2', 'room:draco_vault', 'cndlab0', [2400, -1952], floor_height=-1248),
    deco('deco:vault_goblet', 'room:draco_vault', '7dec46', [2048, -2032], floor_height=-1168),
    torch('deco:vault_torch_e', 'room:draco_vault', 'east', 0.5),
]

# ================================================================================================ wiring
QBITS = {'vault_open': 110940, 'draco_done': 112141}
COFFIN_TEXT = "The coffin is empty."
events = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'not': {'qbit': 'draco_done'}},
     'effects': [{'message': "Draco's coffin was a door: the stair under it ends in the old crypt of Nightshadow. "
                             "Somewhere below, the Count waits in his vault."}],
     'notes': "Say why the party is here (a one-shot timer: a load event's window is not shown; XD-07's method)."},
    {'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:coffin', 'title': "Up to Nightshadow's square",
     'notes': "D-24: the exit preset (the game's own leave window), live to X3 at (17664, -5888, 992) facing south."},
    {'id': 'evt:door_ossuary', 'preset': 'door', 'source': 'door:ossuary', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_sexton', 'preset': 'door', 'source': 'door:sexton', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_feast_w', 'preset': 'door', 'source': 'door:feast_w', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:door_feast_e', 'preset': 'door', 'source': 'door:feast_e', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:iron_door', 'preset': 'script', 'source': 'door:iron', 'title': 'Iron door',
     'opens': ['door:iron'], 'sets': {'qbit': 'vault_open'},
     'effects': [{'text': "The symbol on the iron door flares once and goes dark. The door swings inward."}],
     'notes': "The iron door opens at any hour (D-89, orchestrator 2026-11-22: the vault follows the outer door, no "
              "night condition; was D-25 Q1's Xeen.isNight). Once opened (vault_open, map qbit 110940) it stays open."},
    {'id': 'evt:vault_state', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'vault_open'},
     'opens': ['door:iron'], 'effects': [{'lua': '-- the iron door stays open once opened'}],
     'notes': "Once opened, the iron door stays open (every load)."},
    {'id': 'evt:sign_night', 'preset': 'text', 'source': 'panel:sign_night', 'title': 'Inscription',
     'text': "Cut into the stone over the iron door: Only at night can you put up a fight.", 'window': True,
     'notes': "Original line (aaze0029:6)."},
    {'id': 'evt:draco_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:draco'}},
     'opens': ['door:count_base', 'door:count_top'],
     'effects': [{'lua': 'XeenQuests.hook("q-c7.draco")'},
                 {'message': "Behind the dais a slab of the wall sinks into the floor: a narrow stair climbs into "
                             "the dark, the Count's own way up."}],
     'notes': "goal:draco: the kill timer (XD-05's drum method) calls A3's q-c7.draco (q-c7.done 112141, 10,000 "
              "experience, its text) and opens the Count's stair at both ends (D-25: yes)."},
    {'id': 'evt:count_state', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'draco_done'},
     'opens': ['door:count_base', 'door:count_top'], 'effects': [{'lua': "-- the Count's stair stays open"}],
     'notes': "After Draco's death the Count's stair stays open (every load)."},
    {'id': 'evt:sarcophagus', 'preset': 'text', 'source': 'platform:sarcophagus', 'title': 'Inscription',
     'text': "Words are cut into the foot of the great sarcophagus: Open his coffin and bid him farewell; only then "
             "can you use the magic of the well.", 'window': True,
     'notes': "Original line (aaze0029:8), the rhyme's second half (X3's board has all of it)."},
    {'id': 'evt:altar', 'preset': 'text', 'source': 'platform:altar', 'title': 'Black altar',
     'text': "A black altar under a painted moon. The candles on it burned down long ago, and nobody here needs light."},
    {'id': 'evt:moon', 'preset': 'text', 'source': 'panel:moon', 'title': 'Moon window',
     'text': "A window painted on the stone: a full moon over Nightshadow. The chapel's congregation never wanted a real one."},
    {'id': 'evt:portrait', 'preset': 'text', 'source': 'panel:portrait_1', 'title': 'Portrait',
     'text': "Count Draco, painted in the fashion of one century or another. Every portrait in the gallery has the same pale face."},
    {'id': 'evt:table', 'preset': 'text', 'source': 'platform:table', 'title': 'Feast table',
     'text': "A long table laid for guests who never left. The wine has dried to a black crust in the goblets."},
    {'id': 'evt:bed', 'preset': 'text', 'source': 'platform:bed', 'title': "Sexton's cot",
     'text': "The sexton's cot. The blanket is folded; he went out one night and came back different."},
    {'id': 'evt:count_stair_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:count_stair', 'once': True,
     'text': "A narrow ramp, worn smooth by one pair of feet over many centuries, climbs toward the crypt above.",
     'seconds': 5},
]
for n in (1, 3, 5):
    events.append({'id': f'evt:coffin_{n}', 'preset': 'text', 'source': f'platform:coffin_{n}', 'title': 'Coffin',
                   'text': COFFIN_TEXT, 'notes': "Original line (aaze0029:3)."})
for name, eid in [('chest:sexton', 'evt:chest_sexton'), ('chest:feast', 'evt:chest_feast'),
                  ('chest:hoard', 'evt:chest_hoard')]:
    events.append({'id': eid, 'preset': 'chest', 'source': name, 'title': 'Chest'})
wiring = {'format': 0, 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd24', 'name': 'Nightshadow Crypt', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'XD-24', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': [15, 10], 'climbs': 'n'},
    'map_stats': {'id': 9147, 'encounter_chance': 0, 'treasure_level': 3, 'trap_dice': 3,
                  'perception_difficulty': 3, 'refill_days': 672, 'music': 3, 'environment': 'STONEROOM',
                  'lock_difficulty': 3, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Vampire', 'tier': 0, 'per_marker': [2, 3], 'weight': 75},
                            {'monster': 'Xeen Vampire', 'tier': 1, 'per_marker': [1, 2], 'weight': 25}]},
    'neighbours': [
        {'id': 'exit:x3_coffin', 'to': X3_STEM, 'kind': 'door', 'arrival': X3_ARRIVAL,
         'arrival_hint': "On Nightshadow's square, 512 south of Draco's coffin (thing:coffin_open), facing away from it.",
         'direction': 270,
         'notes': "A5's points (briefs/x3/DOORS.md). X3's open coffin leads in to this map's start (0, 1600, 224) facing "
                  "south (1536)."}],
    'qbits': QBITS,
    'notes': "Xeen design brief, level L4: XD-24 Nightshadow Crypt, under Nightshadow's square on X3, Act III, class S "
             "(MU-6 graph devdocs/xeen/mockups/act3_graphs/xd24.graph.yml, decisions D-25). Q-C7: Count Draco 11293 "
             "(45) placed; his death (a kill timer) calls A3's q-c7.draco (done 112141) and opens his stair up. "
             "Monsters placed (A2's rows): 16 Gnome Vampires 11290 (32), 5 Vampires 11291 (40), Draco; no spawn "
             "points, no rest encounters (the vault stair is the resting place until 21:00). Map card 9147, music 3, "
             "treasure 3 (hoard 4). Map qbit 110940 (vault_open) of the block 110940-110949. The coffin stair leads "
             "out to X3 (A5's arrival).",
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
        p['notes'] = f"Xeen design brief, level {lv}: XD-24 Nightshadow Crypt (see L4/NOTES.md)."
        write(BRIEF / lv, [('plan.yml', plan_doc(lv)), ('project.yml', p), ('diagram.txt', DIAGRAM)])
    p['notes'] = "Xeen design brief, level L3: XD-24 Nightshadow Crypt, the plan and the to-scale shell (rooms.yml)."
    write(BRIEF / 'L3', [('plan.yml', plan_doc('L3')), ('project.yml', p), ('diagram.txt', DIAGRAM),
                         ('rooms.yml', rooms_doc)])
    print('written L1-L3')
    sys.exit(0)

write(BRIEF / 'L4', [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring),
                     ('project.yml', project), ('plan.yml', plan_doc('L4')), ('diagram.txt', DIAGRAM)])
print('written L4')
