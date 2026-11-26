#!/usr/bin/env python3
"""XD-12 Darzog's Tower: the shell (L3) built on geo.py: every room, the shaft, the four stair halls, the roof, the
outside band, the windows and doorways. L4 (dress.py) adds furniture, objects and wiring on top of this."""
from geo import *  # noqa: F401,F403
import geo

# ----------------------------------------------------------------------------------------------- the Well (shaft)
SHAFT_BANDS = []
for f in range(4):
    SHAFT_BANDS.append({'height': FL[f] + 704, 'surface': CNB})
    SHAFT_BANDS.append({'height': FL[f] + 768, 'surface': CWB})
SHAFT_BANDS.append({'height': ROOF + 128, 'surface': CNB})
room('room:well', 'The Well', octagon_shaft(), 0, SKY, 'theme:shaft', bands=SHAFT_BANDS, ambient=10,
     notes="The tower's core: an octagonal well 1,792 across from the gate floor to the open sky, 4,224 high. Every floor looks into it (arches on the gate floor, railed windows above, the roof's parapet at the top); Darzog's disc rides its north face from the gate floor to his own floor.")

# ----------------------------------------------------------------------------------------------- floor 0: the gate
floor_rooms(0, 'f0', 'theme:gate', {
    'gn': ('room:cloister_n', 'North cloister'), 'ge': ('room:cloister_e', 'East cloister'),
    'gs': ('room:cloister_s', 'South cloister'), 'gw': ('room:cloister_w', 'West cloister'),
    'ne': ('room:guardroom', 'Guardroom'), 'nw': ('room:crypt', 'Crypt of the apprentices'),
    'se': ('room:storeroom', 'Storeroom'), 'sw': ('room:cells', 'Cells'),
    'n': ('room:hall_of_hands', 'Hall of Hands'), 's': ('room:cistern', 'Cistern'),
    'e': ('room:gate_hall', 'Gate hall'),
})
stair_hall('room:west_stair', 'West stair hall', 'w', 0, CE[1], 'theme:gate', 'n', ambient=14,
           notes="Gate floor to the works (0 to 768), two storeys high: one long flight up the west wall to a hanging gallery across the north end and along the east wall.")

# ----------------------------------------------------------------------------------------------- floor 1: the works
floor_rooms(1, 'f1', 'theme:works', {
    'gn': ('room:works_n', 'North walk of the works'), 'ge': ('room:works_e', 'East walk of the works'),
    'gs': ('room:works_s', 'South walk of the works'), 'gw': ('room:works_w', 'West walk of the works'),
    'ne': ('room:smelter', 'Smelter'), 'nw': ('room:scrap_hall', 'Scrap hall'),
    'se': ('room:parts_store', 'Parts store'), 'sw': ('room:quarters', "Apprentices' quarters"),
    'n': ('room:forge', 'Forge of the Hands'), 's': ('room:assembly', 'Assembly hall'),
})
stair_hall('room:east_stair', 'East stair hall', 'e', 1, CE[2], 'theme:works', 's', ambient=14,
           notes="The works to the library (768 to 1536): the flight up the east wall rises south to a gallery across the south end and along the west wall.")

# ----------------------------------------------------------------------------------------------- floor 2: the library
floor_rooms(2, 'f2', 'theme:library', {
    'gn': ('room:library_n', 'North reading walk'), 'ge': ('room:library_e', 'East reading walk'),
    'gs': ('room:library_s', 'South reading walk'), 'gw': ('room:library_w', 'West reading walk'),
    'ne': ('room:study_ne', 'Study of the Voice'), 'nw': ('room:study_nw', 'Study of the Mind'),
    'se': ('room:study_se', 'Study of the Arm'), 'sw': ('room:study_sw', 'Study of the Body'),
    'n': ('room:reading_room', 'Reading room'), 's': ('room:great_library', 'Great library'),
})
stair_hall('room:library_stair', 'Library stair hall', 'w', 2, CE[3], 'theme:library', 's', ambient=16,
           notes="The library to Darzog's floor (1536 to 2304): the flight up the west wall rises south to a gallery across the south end and along the east wall.")

# ----------------------------------------------------------------------------------------------- floor 3: Darzog
floor_rooms(3, 'f3', 'theme:darzog', {
    'gn': ('room:state_n', 'North state gallery'), 'ge': ('room:state_e', 'East state gallery'),
    'gs': ('room:state_s', 'South state gallery'), 'gw': ('room:state_w', 'West state gallery'),
    'nw': ('room:darzog_study', "Darzog's study"), 'se': ('room:clone_vats', 'Clone vats'),
    'sw': ('room:guard_hall', 'Guard hall'),
    'n': ('room:darzog_hall', "Darzog's hall"), 's': ('room:portrait_hall', 'Portrait hall'),
})
room('room:bedchamber', "Darzog's bedchamber", [[B, B], [A, B], [A, 2432], [2432, 2432], [2432, A], [B, A]],
     FL[3], CE[3], 'theme:darzog',
     notes="L-shaped round the secret cell in the tower's north-east corner; the portrait on its north wall is the cell's door.")
room('room:crodo_cell', "Crodo's cell", rect(2560, 2560, A, A), FL[3], CE[3], 'theme:darzog', ambient=20,
     notes="The secret room: a bare cell 512 square behind Darzog's portrait, where Crodo has sat since he vanished.")
# F76 (XD-12 p3, 2026-11-26): `solid` names the flight's risers and the gallery's sides; they took the room's wall,
# here the sky, so the stair read as a bare slab running into the wall (check_clipping.py sky.solid).
stair_hall('room:sky_stair', 'Sky stair', 'e', 3, SKY, 'theme:sky_stair', 'n', ambient=18, solid=CNB,
           bands=[{'height': 896, 'surface': CNB}],
           notes="Darzog's floor to the roof (2304 to 3072), open to the sky: the flight up the east wall rises north to the roof's level.")
geo.ROOMS['room:sky_stair']['walls'] = [{'wall': 'n', 'surface': SKYS}]

# ----------------------------------------------------------------------------------------------- the roof
RB = [{'height': 128, 'surface': CNB}]
AR = 3296   # the roof overhangs the keep's outer wall: its parapets are 32 thick over the lake
RIM = 912   # and its rim round the Well 16 thick over the shaft's flat faces, so the party can look down both
NOTES_ROOF = "The roof reaches over the keep's outer wall to 32 short of the open air, and to 16 short of the Well's four flat faces, so its parapets are thin and the party can look down over them."
room('room:roof_n', 'Roof, north', [[-AR, I], [-528, I], [-528, RIM], [528, RIM], [528, I], [B, I], [B, G], [AR, G],
                                     [AR, AR], [-AR, AR]], ROOF, SKY, 'theme:roof', bands=RB, ambient=24, notes=NOTES_ROOF)
room('room:roof_s', 'Roof, south', [[-AR, -AR], [AR, -AR], [AR, -G], [B, -G], [B, -I], [528, -I], [528, -RIM],
                                     [-528, -RIM], [-528, -I], [-AR, -I]], ROOF, SKY, 'theme:roof', bands=RB, ambient=24,
     notes=NOTES_ROOF)
room('room:roof_w', 'Roof, west', [[-AR, -I], [-I, -I], [-I, -528], [-RIM, -528], [-RIM, 528], [-I, 528], [-I, I],
                                    [-AR, I]], ROOF, SKY, 'theme:roof', bands=RB, ambient=24, notes=NOTES_ROOF)
room('room:roof_e', 'Roof, east', [[I, -I], [B, -I], [B, I], [I, I], [I, 528], [RIM, 528], [RIM, -528], [I, -528]],
     ROOF, SKY, 'theme:roof', bands=RB, ambient=24, notes=NOTES_ROOF)


# ----------------------------------------------------------------------------------------------- outside
def rot(p, k):
    x, y = p
    for _ in range(k):
        x, y = -y, x
    return [x, y]


OUT_BANDS = [{'height': ROOF + 128, 'surface': CNB}]
SHORE = 3840
BANK = 3712
DIRT = S_('7dirt1', 128, 128)
for k, (rid, name) in enumerate([('room:out_n', 'Island and lake, north'), ('room:out_w', 'Island and lake, west'),
                                   ('room:out_s', 'Island and lake, south'), ('room:out_e', 'Island and lake, east')]):
    base = rect(-O, W, W, O)                       # out_n; the others turned a quarter at a time (ccw)
    outline = [rot(p, k) for p in base]
    pts = [[-O, W, -64], [-O, O, -64], [W, O, -64],
           [-BANK, W, 0], [-BANK, BANK, 0], [W, BANK, 0],
           [-SHORE, W, -64], [-SHORE, SHORE, -64], [W, SHORE, -64]]
    fp = [rot(p[:2], k) + [p[2]] for p in pts]
    lines = [[rot(p, k) for p in ([-BANK, W], [-BANK, BANK], [W, BANK])],
             [rot(p, k) for p in ([-SHORE, W], [-SHORE, SHORE], [W, SHORE])]]
    lake_at = rot([0, 6400], k)
    r = room(rid, name, outline, 0, SKY, 'theme:outside', ambient=0, bands=OUT_BANDS,
             floor_points=fp, floor_lines=lines,
             floor_surfaces=[{'at': lake_at, 'surface': WATER}, {'steeper_than': 0.1, 'surface': DIRT}],
             notes="Seen from the windows and the roof, never walked: the island's grass at the keep's foot, a muddy bank, and Lake Darzog beyond under the open sky. A fall from the keep lands here and leaves the map for X2.")
    # the walls toward the lake are sky (edges 2 north and 3 west of out_n, turned with it)
    L2 = (O + W)
    r['walls'] = [{'wall': 2, 'surface': SKYS, 'bands': False}, {'wall': 3, 'surface': SKYS, 'bands': False}]

op('open:out_ne', 'room:out_n', 'room:out_e', 'e', width='full', height='full')
op('open:out_nw', 'room:out_w', 'room:out_n', 'n', width='full', height='full')
op('open:out_sw', 'room:out_s', 'room:out_w', 'w', width='full', height='full')
op('open:out_se', 'room:out_e', 'room:out_s', 's', width='full', height='full')

# ----------------------------------------------------------------------------------------------- openings
GAL = {0: ('cloister', 'room:cloister_'), 1: ('works', 'room:works_'), 2: ('library', 'room:library_'),
       3: ('state', 'room:state_')}
# into the Well: arches on the gate floor, railed windows above, the disc landing on Darzog's floor
for k, side in (('n', 's'), ('e', 'w'), ('s', 'n'), ('w', 'e')):
    op(f'open:arch_{k}', f'room:cloister_{k}', 'room:well', side, width=512, height=384, shape='arch', apex=512)
    op(f'open:works_win_{k}', f'room:works_{k}', 'room:well', side, width=640, height=352, sill=96)
    op(f'open:library_win_{k}', f'room:library_{k}', 'room:well', side, width=512, height=320, sill=96)
    if k == 'n':
        op('open:disc_landing', 'room:state_n', 'room:well', side, width=384, height=320)
    else:
        op(f'open:state_win_{k}', f'room:state_{k}', 'room:well', side, width=640, height=384, sill=96)
PARA = dict(reveal=SKYS, threshold=CNB)
op('open:roof_well_n', 'room:roof_n', 'room:well', 's', width='full', height='full', sill=64, **PARA)
op('open:roof_well_s', 'room:roof_s', 'room:well', 'n', width='full', height='full', sill=64, **PARA)
# the west rim: a parapet either side of a doorway onto the overlook, a railed stone pier out over the Well
# open over its whole face: a parapet of blocks on the roof's side, broken by the way onto the pier
op('open:roof_well_w', 'room:roof_w', 'room:well', 'e', width='full', height='full', **PARA)
geo.ROOMS['room:roof_w'].setdefault('platforms', []).extend([
    {'outline': rect(-944, 128, -914, 526), 'rise': 64, 'surface': CNB, 'top_surface': CNB,
     'notes': "Parapet of the Well's west rim, beside the way onto the overlook."},
    {'outline': rect(-944, -526, -914, -128), 'rise': 64, 'surface': CNB, 'top_surface': CNB,
     'notes': "Parapet of the Well's west rim, beside the way onto the overlook."},
])
KERB = dict(surface=CNB, top_surface=CNB)
geo.ROOMS['room:well'].setdefault('platforms', []).extend([
    {'id': 'platform:well_overlook', 'outline': rect(-896, -128, -448, 128), 'base': ROOF - 32, 'rise': 32,
     'surface': CNB, 'top_surface': TFB03, 'bottom_surface': CNB,
     'notes': "The overlook: a stone pier 448 long out over the Well from the roof's west rim, railed on three sides; from its end the Well drops 3,072 to the rune circle."},
    {'outline': rect(-880, 112, -448, 128), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the overlook.'},
    {'outline': rect(-880, -128, -448, -112), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the overlook.'},
    {'outline': rect(-464, -112, -448, 112), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the overlook.'},
])
op('open:roof_well_e', 'room:roof_e', 'room:well', 'w', width='full', height='full', sill=64, **PARA)

# floor 0
op('open:gate_cloister', 'room:gate_hall', 'room:cloister_e', 'w', centre=0, width=768, height=448, shape='arch',
   apex=576)
op('open:gate_guardroom', 'room:gate_hall', 'room:guardroom', 'n', centre=2496, width=256, height=320)
op('open:gate_store', 'room:gate_hall', 'room:storeroom', 's', centre=2496, width=256, height=320)
op('open:cloister_hands', 'room:cloister_n', 'room:hall_of_hands', 'n', centre=-384, width=512, height=384)
op('open:hands_guardroom', 'room:hall_of_hands', 'room:guardroom', 'e', centre=2496, width=256, height=320)
op('open:hands_crypt', 'room:hall_of_hands', 'room:crypt', 'w', centre=2496, width=256, height=320)
op('open:cloister_cistern', 'room:cloister_s', 'room:cistern', 's', centre=384, width=512, height=384)
op('open:cistern_store', 'room:cistern', 'room:storeroom', 'e', centre=-2496, width=256, height=320)
op('open:cistern_cells', 'room:cistern', 'room:cells', 'w', centre=-2496, width=256, height=320)
op('open:cloister_wstair', 'room:cloister_w', 'room:west_stair', 'w', centre=-768, width=384, height=384)
op('open:wstair_crypt', 'room:west_stair', 'room:crypt', 'n', centre=-2624, width=256, height=320)
op('open:wstair_cells', 'room:west_stair', 'room:cells', 's', centre=-2624, width=256, height=320)
# floor 1: the west stair's gallery at 768
op('open:wstair_works_w', 'room:west_stair', 'room:works_w', 'e', centre=-768, width=384, height=352)
op('open:wstair_scrap', 'room:west_stair', 'room:scrap_hall', 'n', centre=-2624, width=256, height=320)
op('open:wstair_quarters', 'room:west_stair', 'room:quarters', 's', centre=-2112, width=256, height=320)
op('open:works_forge', 'room:works_n', 'room:forge', 'n', centre=-384, width=512, height=384)
op('open:forge_smelter', 'room:forge', 'room:smelter', 'e', centre=2496, width=256, height=320)
op('open:forge_scrap', 'room:forge', 'room:scrap_hall', 'w', centre=2496, width=256, height=320)
op('open:works_assembly', 'room:works_s', 'room:assembly', 's', centre=384, width=512, height=384)
op('open:assembly_parts', 'room:assembly', 'room:parts_store', 'e', centre=-2496, width=256, height=320)
op('open:assembly_quarters', 'room:assembly', 'room:quarters', 'w', centre=-2496, width=256, height=320)
op('open:works_estair', 'room:works_e', 'room:east_stair', 'e', centre=640, width=384, height=384)
# floor 2: the east stair's gallery at 1536
op('open:estair_library_e', 'room:east_stair', 'room:library_e', 'w', centre=640, width=384, height=352)
op('open:estair_study_ne', 'room:east_stair', 'room:study_ne', 'n', centre=2112, width=256, height=320)
op('open:estair_study_se', 'room:east_stair', 'room:study_se', 's', centre=2624, width=256, height=320)
op('open:library_reading', 'room:library_n', 'room:reading_room', 'n', centre=-384, width=512, height=384)
op('open:reading_study_ne', 'room:reading_room', 'room:study_ne', 'e', centre=2496, width=256, height=320)
op('open:reading_study_nw', 'room:reading_room', 'room:study_nw', 'w', centre=2496, width=256, height=320)
op('open:library_great', 'room:library_s', 'room:great_library', 's', centre=384, width=512, height=384)
op('open:great_study_se', 'room:great_library', 'room:study_se', 'e', centre=-2496, width=256, height=320)
op('open:great_study_sw', 'room:great_library', 'room:study_sw', 'w', centre=-2496, width=256, height=320)
op('open:library_lstair', 'room:library_w', 'room:library_stair', 'w', centre=640, width=384, height=384)
# floor 3: the library stair's gallery at 2304
op('open:lstair_state_w', 'room:library_stair', 'room:state_w', 'e', centre=640, width=384, height=352)
op('open:lstair_study', 'room:library_stair', 'room:darzog_study', 'n', centre=-2112, width=256, height=320)
op('open:lstair_guard', 'room:library_stair', 'room:guard_hall', 's', centre=-2624, width=256, height=320)
op('open:state_hall', 'room:state_n', 'room:darzog_hall', 'n', centre=-512, width=512, height=384)
op('open:hall_study', 'room:darzog_hall', 'room:darzog_study', 'w', centre=2496, width=256, height=320)
op('open:hall_bedchamber', 'room:darzog_hall', 'room:bedchamber', 'e', centre=2240, width=256, height=320)
op('open:bedchamber_cell', 'room:bedchamber', 'room:crodo_cell', 'n', centre=2816, width=128, height=256)
op('open:state_portraits', 'room:state_s', 'room:portrait_hall', 's', centre=384, width=512, height=384)
op('open:portraits_vats', 'room:portrait_hall', 'room:clone_vats', 'e', centre=-2496, width=256, height=320)
op('open:portraits_guard', 'room:portrait_hall', 'room:guard_hall', 'w', centre=-2496, width=256, height=320)
op('open:state_skystair', 'room:state_e', 'room:sky_stair', 'e', centre=-512, width=384, height=384)
op('open:vats_skystair', 'room:clone_vats', 'room:sky_stair', 'n', centre=2496, width=256, height=320)
# the roof: one terrace, its parts joined without walls
op('open:roof_nw', 'room:roof_w', 'room:roof_n', 'n', width='full', height='full')
op('open:roof_ne', 'room:roof_e', 'room:roof_n', 'n', width='full', height='full')
op('open:roof_sw', 'room:roof_w', 'room:roof_s', 's', width='full', height='full')
op('open:roof_se', 'room:roof_e', 'room:roof_s', 's', width='full', height='full')
op('open:skystair_roof_n', 'room:sky_stair', 'room:roof_n', 'n', width='full', height='full')
op('open:skystair_roof_s', 'room:sky_stair', 'room:roof_s', 's', width='full', height='full')
# F76 (XD-12 p4, 2026-11-26): the sky stair's west wall north and south of roof_e (768 each, by roof_n and roof_s)
# stood as two low walls of no thickness between the gallery and the roof, both at 3,072: a lone stone block on the
# roof (tools/xeen/check_clipping.py piece.free). Open to roof_n and roof_s too; the studio keeps 16 of wall between
# two openings of one wall, so the opening to roof_e stops 16 short at each end and a square post of keep stone (a
# merlon's height) stands on roof_e's side over each 16 (2 in front of it, as the studio's panels), where the roof's
# three parts and the gallery meet.
op('open:skystair_roof_e', 'room:sky_stair', 'room:roof_e', 'w', centre=0, width=2016, height='full')
op('open:skystair_roof_nw', 'room:sky_stair', 'room:roof_n', 'w', width='full', height='full')
op('open:skystair_roof_sw', 'room:sky_stair', 'room:roof_s', 'w', width='full', height='full')
for _post in (rect(1856, 960, 1918, 1024), rect(1856, -1024, 1918, -960)):
    geo.ROOMS['room:roof_e'].setdefault('platforms', []).append(
        {'outline': _post, 'rise': 160, 'surface': CNB, 'top_surface': CNB,
         'notes': "A post of keep stone where the roof's three parts and the sky stair's gallery meet."})
# battlements: the roof over the lake
op('open:battlement_n', 'room:roof_n', 'room:out_n', 'n', width='full', height='full', sill=64, **PARA)
op('open:battlement_nw', 'room:roof_n', 'room:out_w', 'w', width='full', height='full', sill=64, **PARA)
op('open:battlement_ne', 'room:roof_n', 'room:out_e', 'e', width='full', height='full', sill=64, **PARA)
# the south battlement: a doorway in the middle onto a railed balcony hanging out over the lake
op('open:battlement_s', 'room:roof_s', 'room:out_s', 's', width='full', height='full', **PARA)
geo.ROOMS['room:roof_s'].setdefault('platforms', []).extend([
    {'outline': rect(-3294, -3294, -160, -3262), 'rise': 64, 'surface': CNB, 'top_surface': CNB,
     'notes': 'The south parapet (a block: the battlement is open above the roof here), broken by the way onto the balcony.'},
    {'outline': rect(160, -3294, 3294, -3262), 'rise': 64, 'surface': CNB, 'top_surface': CNB,
     'notes': 'The south parapet, east of the balcony.'},
])
geo.ROOMS['room:out_s'].setdefault('platforms', []).extend([
    {'id': 'platform:lake_balcony', 'outline': rect(-160, -3712, 160, -3328), 'base': ROOF - 32, 'rise': 32,
     'surface': CNB, 'top_surface': TFB03, 'bottom_surface': CNB,
     'notes': "A balcony of stone 320 wide hanging 384 out from the south battlement, railed on three sides: from its rail the island, its trees and Lake Darzog lie 3,000 below."},
    {'outline': rect(-160, -3712, -144, -3328), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the balcony.'},
    {'outline': rect(144, -3712, 160, -3328), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the balcony.'},
    {'outline': rect(-144, -3712, 144, -3696), 'base': ROOF, 'rise': 48, **KERB, 'notes': 'Rail of the balcony.'},
])
op('open:battlement_sw', 'room:roof_s', 'room:out_w', 'w', width='full', height='full', sill=64, **PARA)
op('open:battlement_se', 'room:roof_s', 'room:out_e', 'e', width='full', height='full', sill=64, **PARA)
op('open:battlement_w', 'room:roof_w', 'room:out_w', 'w', centre=0, width=1984, height='full', sill=64, **PARA)
# its two ends (the keep wall's cut, 256 deep) in stone to 288 over the sill, not sky: a party that jumps onto the
# 256-deep sill saw the sky's below-horizon fog at its feet there (check_parapet_gaps.py sky.low; xeen-fb4-dungeon6,
# 2026-11-25). Above the opening the stair's own wall is sky, so its top through the wall is sky too (`lintel`); a
# full-height stone reveal stood up as two bare posts 1,000 into the sky.
op('open:battlement_e', 'room:sky_stair', 'room:out_e', 'e', centre=0, width=3520, height=288, sill=880,
   **dict(PARA, reveal=CNB, lintel=SKYS))

# windows over the lake: slits on the gate floor, windows above, tall windows in the stair halls
WIN = [
    # (room, side toward outside, outside room, centre, width, height, sill)
    ('room:hall_of_hands', 'n', 'room:out_n', -768, 64, 256, 160),
    ('room:hall_of_hands', 'n', 'room:out_n', 768, 64, 256, 160),
    ('room:cistern', 's', 'room:out_s', 0, 64, 256, 160),
    ('room:gate_hall', 'e', 'room:out_e', -1152, 64, 256, 160),
    ('room:gate_hall', 'e', 'room:out_e', 1152, 64, 256, 160),
    ('room:guardroom', 'e', 'room:out_e', 2496, 64, 256, 160),
    ('room:storeroom', 's', 'room:out_s', 2496, 64, 256, 160),
    ('room:cells', 'w', 'room:out_w', -2496, 64, 192, 224),
    ('room:crypt', 'n', 'room:out_n', -2496, 64, 192, 224),
    ('room:west_stair', 'w', 'room:out_w', 512, 256, 512, 384),
    ('room:forge', 'n', 'room:out_n', 0, 256, 256, 160),
    ('room:assembly', 's', 'room:out_s', 0, 256, 256, 160),
    ('room:smelter', 'e', 'room:out_e', 2496, 256, 256, 160),
    ('room:scrap_hall', 'w', 'room:out_w', 2496, 256, 256, 160),
    ('room:parts_store', 'e', 'room:out_e', -2496, 256, 256, 160),
    ('room:quarters', 's', 'room:out_s', -2496, 256, 256, 160),
    ('room:east_stair', 'e', 'room:out_e', -512, 256, 512, 384),
    ('room:reading_room', 'n', 'room:out_n', -896, 256, 320, 160),
    ('room:reading_room', 'n', 'room:out_n', 896, 256, 320, 160),
    ('room:great_library', 's', 'room:out_s', -896, 256, 320, 160),
    ('room:great_library', 's', 'room:out_s', 896, 256, 320, 160),
    ('room:study_ne', 'n', 'room:out_n', 2496, 256, 256, 160),
    ('room:study_nw', 'n', 'room:out_n', -2496, 256, 256, 160),
    ('room:study_se', 's', 'room:out_s', 2496, 256, 256, 160),
    ('room:study_sw', 's', 'room:out_s', -2496, 256, 256, 160),
    ('room:library_stair', 'w', 'room:out_w', -512, 256, 512, 384),
    ('room:darzog_hall', 'n', 'room:out_n', -1152, 256, 320, 160),
    ('room:darzog_hall', 'n', 'room:out_n', 1152, 256, 320, 160),
    ('room:darzog_study', 'w', 'room:out_w', 2496, 256, 256, 160),
    ('room:bedchamber', 'e', 'room:out_e', 2176, 256, 192, 192),
    ('room:portrait_hall', 's', 'room:out_s', 0, 256, 256, 160),
    ('room:clone_vats', 'e', 'room:out_e', -2496, 256, 256, 160),
    ('room:guard_hall', 'w', 'room:out_w', -2496, 256, 256, 160),
]
for i, (rid, side, out, c, w, h, s) in enumerate(WIN):
    op(f'open:window_{i:02d}', rid, out, side, centre=c, width=w, height=h, sill=s)

# trapdoors: holes in the library's floors over the works (a lift in the room below plugs each)
for _tid, _up, _low, _c in TRAPDOORS:
    OPENINGS.append({'id': f'open:{_tid}', 'from': _up, 'to': _low, 'in': 'floor', 'at': list(_c), 'size': [256, 256],
                     'reveal': CFB1})


# merlons: blocks of keep stone 128 long and 32 deep on the roof's side of every battlement, 256 apart (the crenels)
def merlons(rid, axis, fixed, lo, hi, inward, skip=()):
    r = geo.ROOMS[rid]
    p = lo + 128
    while p + 128 <= hi - 64:
        if not any(a - 192 < p + 64 and p + 64 < b + 192 for a, b in skip):
            if axis == 'x':
                y0 = fixed + (2 if inward > 0 else -34)
                out = rect(p, y0, p + 128, y0 + 32)
            else:
                x0 = fixed + (2 if inward > 0 else -34)
                out = rect(x0, p, x0 + 32, p + 128)
            m = {'outline': out, 'rise': 160, 'surface': CNB, 'top_surface': CNB, 'notes': 'A merlon.'}
            if rid == 'room:roof_s' and axis == 'x':
                m.update(base=64, rise=96)
            r.setdefault('platforms', []).append(m)
        p += 384


merlons('room:roof_n', 'x', AR, -AR, AR, -1)
merlons('room:roof_n', 'y', -AR, I, AR - 64, 1)
merlons('room:roof_n', 'y', AR, G, AR - 64, -1)
merlons('room:roof_s', 'x', -AR, -AR, AR, 1, skip=[(-160, 160)])
merlons('room:roof_s', 'y', -AR, -AR + 64, -I, 1)
merlons('room:roof_s', 'y', AR, -AR + 64, -G, -1)
merlons('room:roof_w', 'y', -AR, -I, I, 1)
