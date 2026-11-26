#!/usr/bin/env python3
"""XD-06 Temple of Yak, L4: writes rooms.yml, objects.yml, wiring.yml and project.yml of
devdocs/xeen/briefs/xd06/L4 (and the L3 shell: rooms.yml without objects, devdocs/xeen/briefs/xd06/L3/rooms.yml).
Rerun after every change here; never hand-edit the written files while this generator is in use (NOTES.md says when
it is retired). x east, y north, heights from the porch floor (0); the undercroft at -768."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

R = Path(_REPO_ROOT)
L4 = R / 'devdocs/xeen/briefs/xd06/L4'
L3 = R / 'devdocs/xeen/briefs/xd06/L3'


def S(t, w, h, **kw):
    d = {'texture': t, 'size': [w, h]}
    d.update(kw)
    return d


# ---------------------------------------------------------------- the two families
# Temple: MM7's Temple of Baa (d04): brick t6s1bs, flags t6s1fl, coffered ceiling t6s1c, skull frieze t6s1b,
# green slabs t4s1fl, iron-bound doors t5d1, its push-button stone 7t1butts/7t1butt, bookcase 7t1books1, cabinets 7t1cab.
BRICK = S('t6s1bs', 128, 256)
FRIEZE = S('t6s1b', 128, 256)
FLAGS = S('t6s1fl', 128, 128)
COFFER = S('t6s1c', 128, 128)
SLAB = S('t4s1fl', 128, 128)
DOOR = S('t5d1', 128, 256)
RIVET = S('7gt001a', 64, 64)
BOOKS = S('7t1books', 128, 256)
T2 = S('t2bs', 128, 256)
BUTT = S('7t1butt', 32, 32)
CAB = S('7t1cab', 128, 256)
SHEET = S('t2bedsht', 128, 256)
BEDWOOD = S('7t1beds', 256, 64)
BUTTS = S('7t1butts', 32, 32)
# Undercroft: MM7's Barrow I (mdt03), the Barrow Downs' crypts: sandy rock walls t5bs, grey rock floors t2bs,
# green-black rock roofs t4bs, plastered crypt walls with their frieze hwp1b, cut stone 7t1s2b.
RWALL = S('t5bs', 128, 256)
RFLOOR = S('t2bs', 128, 256)
RROOF = S('t4bs', 128, 256)
PLASTER = S('hwp1b', 128, 256)
CUT = S('7t1s2b', 128, 256)
SLIME = {'texture': '7slimywtr', 'liquid': 'water'}

themes = [
    {'id': 'theme:temple', 'wall': BRICK, 'floor': FLAGS, 'ceiling': COFFER, 'door': DOOR, 'reveal': BRICK,
     'notes': "The temple above: MM7's Temple of Baa (d04) as it lays its set: brick t6s1bs on walls, flagstones t6s1fl underfoot, the coffered ceiling t6s1c, iron-bound doors t5d1."},
    {'id': 'theme:temple_tall', 'wall': BRICK, 'floor': FLAGS, 'ceiling': COFFER, 'door': DOOR, 'reveal': BRICK,
     'bands': [{'height': 640, 'surface': BRICK}, {'height': 896, 'surface': FRIEZE}],
     'notes': "The nave: d04's brick with its skull frieze t6s1b in a band 640 to 896 over the floor (d04 hangs it the same way over its tall halls)."},
    {'id': 'theme:sanctum', 'wall': SLAB, 'floor': FLAGS, 'ceiling': COFFER, 'door': DOOR, 'reveal': BRICK,
     'bands': [{'height': 640, 'surface': SLAB}, {'height': 896, 'surface': FRIEZE}],
     'notes': "The Yak Master's sanctum below: d04's green-black slabs t4s1fl (its lower towers' walls) under the skull frieze."},
    {'id': 'theme:master_stair', 'wall': SLAB, 'floor': FLAGS, 'ceiling': COFFER, 'door': DOOR, 'reveal': BRICK,
     'notes': "The Yak Master's own stair: d04's green-black slabs t4s1fl (its lower towers' walls) under its coffered ceiling, so that the Master's way reads apart from the clerics' brick."},
    {'id': 'theme:crypt', 'wall': RWALL, 'floor': RFLOOR, 'ceiling': RROOF, 'door': DOOR,
     'notes': "The undercroft's caves and crypts: MM7's Barrow I (mdt03) as it lays them: sandy rock t5bs on walls, grey rock t2bs underfoot, green-black rock t4bs overhead."},
    {'id': 'theme:pool', 'wall': RWALL, 'floor': SLIME, 'ceiling': RROOF,
     'notes': "The Yak Pool's basin: Barrow I's rock round MM7's slime water (7slimywtr, drawn by the liquid shader, the fluid bit)."},
    {'id': 'theme:crypt_dressed', 'wall': PLASTER, 'floor': RFLOOR, 'ceiling': RROOF, 'door': DOOR,
     'notes': "Dressed crypts (the ossuary, the lich crypt): Barrow I's plastered wall hwp1b with its moulding, over the barrow's rock floor."},
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


# ================================================================ the temple above (floor 0)
room('room:porch', 'Temple porch', outline=rect(-640, 0, 640, 1152), floor=0, ceiling=1024, theme='theme:temple',
     ambient=16,
     notes="Inside the temple's front door from the fairy woods (X2): a plain brick porch 1,280 by 1,152, the door to the woods in its south wall, the Yak door north.")
room('room:narthex', 'Narthex', outline=rect(-1280, 1216, 1280, 1984), floor=0, ceiling=1024, theme='theme:temple',
     ambient=20,
     notes="A cross hall 2,560 by 768 before the nave; doors west to the clerics' wing and east to the library, the nave through a wide arch north.")
nave_pillars = []
for py in (2688, 3328, 3968, 4608):
    for px in (-640, 640):
        nave_pillars.append({'at': [px, py], 'size': [160, 160], 'surface': BRICK})
room('room:nave', 'Nave of Yak', outline=rect(-1280, 2048, 1280, 5632), floor=0, ceiling=1088, theme='theme:temple_tall',
     ambient=22, pillars=nave_pillars,
     ceiling_levels=[{'outline': rect(-512, 2304, 512, 4864), 'ceiling': 1344}],
     platforms=[
         {'id': 'platform:dais', 'at': [0, 5280], 'size': [1024, 448], 'rise': 32, 'surface': SLAB, 'top_surface': FLAGS,
          'notes': "The idol's dais, one step up, at the nave's north end."},
         {'id': 'platform:idol_plinth', 'at': [0, 5376], 'size': [256, 192], 'base': 32, 'rise': 64, 'surface': SLAB,
          'top_surface': SLAB, 'notes': "The plinth of Yak's idol."},
     ],
     notes="The great hall of the cult, 2,560 by 3,584 and 1,088 high (1,344 under the raised middle), two rows of four brick pillars, Yak's idol on a dais at the north end. The treasury gate stands in the north wall west of the dais; the chapels open off the middle of the side walls.")
room('room:chapel_w', 'West chapel', outline=rect(-2176, 3584, -1344, 4864), floor=0, ceiling=768, theme='theme:temple',
     ambient=22,
     platforms=[{'at': [-1760, 3664], 'size': [512, 128], 'rise': 96, 'surface': SLAB, 'top_surface': SLAB,
                 'notes': "A side altar against the south wall (moved 2026-11-20 from before the refectory doorway: the dressing rule)."}],
     walls=[{'wall': 'north', 'panels': [{'id': 'panel:plaque_w', 'offset': 186, 'length': 128, 'bottom': 58, 'height': 128, 'surface': COFFER,
                                          'notes': "A carved square of the temple's coffer stone behind the lever, so that it shows against the brick."}]}],
     notes="A side chapel off the nave's west wall, 832 by 1,280; the lever for the west bar of the treasury gate on its north wall; a doorway west into the refectory.")
room('room:chapel_e', 'East chapel', outline=rect(1344, 3584, 2176, 4864), floor=0, ceiling=768, theme='theme:temple',
     ambient=22,
     platforms=[{'at': [1760, 3664], 'size': [512, 128], 'rise': 96, 'surface': SLAB, 'top_surface': SLAB,
                 'notes': "A side altar against the south wall (moved 2026-11-20 from before the vestry doorway: the dressing rule)."}],
     notes="The mirror of the west chapel off the nave's east wall; a doorway east into the vestry.")
room('room:passage_w', 'West passage', path=[[-1344, 1600], [-2624, 1600], [-2624, 2368]], width=384, floor=0,
     ceiling=448, theme='theme:temple', ambient=24,
     notes="A narrow passage from the narthex's west door round to the clerics' dormitory.")
room('room:passage_e', 'East passage', path=[[1344, 1600], [2624, 1600], [2624, 2368]], width=384, floor=0,
     ceiling=448, theme='theme:temple', ambient=24,
     notes="The mirror passage from the narthex's east door round to the library.")
# Cots against the side walls, clear of the hidden cell's door (west wall, y 2976-3232) and of the passage's doorway
# (south wall, x -2784 to -2464): two on the west wall south of the door, four on the east wall (moved 2026-11-20).
BED_AT = {'00': [-3648, 2560], '10': [-3648, 2752], '01': [-2432, 2752], '11': [-2432, 3008], '20': [-2432, 3264],
          '21': [-2432, 3520]}
beds = []
for i in range(3):
    for j in range(2):
        beds.append({'id': f'platform:bed_{i}{j}', 'at': BED_AT[f'{i}{j}'], 'size': [256, 128], 'rise': 40, 'surface': BEDWOOD,
                     'top_surface': SHEET, 'notes': "A cleric's cot against the wall."})
room('room:dormitory', 'Dormitory', outline=rect(-3840, 2432, -2240, 3584), floor=0, ceiling=576, theme='theme:temple',
     ambient=24, platforms=beds,
     notes="The clerics' dormitory, 1,600 by 1,152: six cots along the side walls. A secret door in the west wall to a hidden cell.")
room('room:hidden_cell', 'Hidden cell', outline=rect(-4480, 2880, -3904, 3328), floor=0, ceiling=448, theme='theme:temple',
     ambient=26, notes="A cleric's hiding place behind the dormitory's west wall, 576 by 448: a chest.")
room('room:refectory', 'Refectory', outline=rect(-3840, 3648, -2240, 5248), floor=0, ceiling=640, theme='theme:temple',
     ambient=22,
     platforms=[{'at': [-3488, 4448], 'size': [256, 1024], 'rise': 72, 'surface': RIVET, 'top_surface': BEDWOOD,
                 'notes': "The long table, in the west half (off the way from the dormitory door to the stair)."},
                {'at': [-3744, 4448], 'size': [96, 896], 'rise': 40, 'surface': RIVET, 'top_surface': BEDWOOD,
                 'notes': "Bench, west"},
                {'at': [-3232, 4448], 'size': [96, 896], 'rise': 40, 'surface': RIVET, 'top_surface': BEDWOOD,
                 'notes': "Bench, east"},
                {'id': 'platform:crate', 'at': [-2336, 5152], 'size': [128, 128], 'rise': 128, 'surface': RIVET,
                 'top_surface': RIVET, 'notes': "A crate of d04's riveted boards in the north-east corner beside a cask (empty: the source's line)."}],
     notes="The clerics' refectory, 1,600 square: a long table with benches in its west half, casks and a crate in its east corners; the west stair to the undercroft leaves from its north wall.")
room('room:library', 'Library', outline=rect(2240, 2432, 3840, 3584), floor=0, ceiling=640, theme='theme:temple',
     ambient=22,
     platforms=[{'at': [3360, 2592], 'size': [800, 96], 'rise': 256, 'surface': BOOKS, 'end_surface': CAB, 'top_surface': COFFER,
                 'notes': "Bookcases along the south wall east of the passage's doorway."},
                {'at': [2304, 3328], 'size': [96, 384], 'rise': 256, 'surface': BOOKS, 'end_surface': CAB, 'top_surface': COFFER,
                 'notes': "Bookcases along the west wall's north half (the torch above the wall's middle stays clear)."},
                {'at': [3168, 3120], 'size': [96, 384], 'rise': 256, 'surface': BOOKS, 'end_surface': CAB, 'top_surface': COFFER,
                 'notes': "A free-standing bookcase, off the ways from both doorways to the button."}],
     walls=[{'wall': 'east', 'panels': [{'id': 'panel:plaque_e', 'offset': 512, 'length': 128, 'bottom': 58, 'height': 128, 'surface': COFFER,
                                         'notes': "A carved square of coffer stone behind the lever."}]}],
     notes="The cult's library, 1,600 by 1,152: bookcases; the lever for the east bar of the treasury gate on its east wall; a chest of the clerics' scrolls.")
room('room:vestry', 'Vestry', outline=rect(2240, 3648, 3840, 5248), floor=0, ceiling=640, theme='theme:temple', ambient=22,
     platforms=[{'at': [3744, 4448], 'size': [96, 896], 'rise': 256, 'surface': CAB, 'top_surface': COFFER,
                 'notes': "Robe cabinets along the east wall (d04's 7t1cab)."}],
     notes="The priests' vestry, 1,600 square: robe cabinets; the Master's door in its north wall (it opens from the far side, the Master's stair).")
room('room:treasury', 'Treasury', outline=rect(-1152, 5696, -256, 6656), floor=0, ceiling=960, theme='theme:sanctum',
     ambient=24, notes="The cult's treasury behind the barred gate, 896 by 960: the strongbox with the King's Megacredits.")
room('room:stair_w', 'West stair', outline=rect(-3328, 5312, -2752, 6848), floor=0,
     slope={'to': -768, 'toward': 'north', 'steps': 24, 'tread': FLAGS, 'riser': BRICK}, ceiling=448,
     ceiling_slope={'to': -320, 'toward': 'north'}, theme='theme:temple', ambient=26,
     notes="A straight flight of 24 steps of 32 down from the refectory to the crypts (1,536 long).")
room('room:master_stair', "Master's stair", outline=rect(2496, 5312, 3072, 9024), floor=0,
     slope={'to': -768, 'toward': 'north', 'steps': 24, 'tread': FLAGS, 'riser': SLAB}, ceiling=448,
     ceiling_slope={'to': -320, 'toward': 'north'}, theme='theme:master_stair', ambient=22,
     notes="The Yak Master's own stair: 24 long steps up from the lich crypt to the vestry (3,712 long); the door at its top opens from this side only.")

# ================================================================ the undercroft (floor -768)
room('room:crypt', 'Crypt of the clergy', outline=rect(-3840, 6912, -2112, 8448), floor=-768, ceiling=-64,
     theme='theme:crypt', ambient=24,
     pillars=[{'at': [-2976, 7488], 'size': [192, 192], 'surface': CUT}, {'at': [-2976, 7936], 'size': [192, 192], 'surface': CUT}],
     platforms=[{'id': 'platform:tomb_1', 'at': [-3680, 7360], 'size': [128, 256], 'rise': 64, 'surface': CUT, 'top_surface': SLAB,
                 'notes': "A stone tomb."},
                {'id': 'platform:tomb_2', 'at': [-3680, 8000], 'size': [128, 256], 'rise': 64, 'surface': CUT, 'top_surface': SLAB,
                 'notes': "A stone tomb."}],
     notes="A long rock-cut crypt 1,728 by 1,536 under the clerics' wing: two pillars, stone tombs and coffins along the walls; skeletons.")
room('room:ossuary', 'Ossuary', outline=rect(-3712, 8512, -2240, 9856), floor=-768, ceiling=-128, theme='theme:crypt_dressed',
     ambient=24, notes="A plastered bone-house 1,472 by 1,344 heaped with the temple's dead; a passage east to the pool.")
room('room:near_bank', 'Yak Pool, near bank',
     outline=[[-2176, 8704], [-1600, 8640], [-1344, 8832], [-1344, 10432], [-1600, 10624], [-2176, 10560]],
     floor=-768, ceiling=-64, ceiling_points=[[-1760, 9632, 64]], theme='theme:crypt', ambient=20,
     rough={'step': 192, 'depth': 40},
     platforms=[{'id': 'platform:lever_post', 'at': [-1376, 10080], 'size': [64, 288], 'rise': 64, 'surface': CUT,
                 'top_surface': CUT, 'notes': "A low stone kerb at the pool's edge, north of the causeway's landing, with the three bridge levers on its west face: the party pulls them looking over it at the pool."},
                {'id': 'platform:yak_basin', 'at': [-1440, 8992], 'size': [128, 192], 'rise': 56, 'surface': CUT,
                 'top_surface': SLIME, 'notes': "A stone basin at the rim, brimming with the pool's water: 'Yak Pool' (drink)."}],
     notes="A cave 830 wide on the west shore of the Yak Pool; the whole east wall opens onto the pool (160 down). Three levers on a stone post, a basin of the pool's water, bones at the rim.")
spans = [(-1109.5, 341), (-768, 342), (-426.5, 341)]
room('room:yak_pool', 'Yak Pool', outline=rect(-1280, 9024, -256, 10368), floor=-928, ceiling=-64, theme='theme:pool',
     ambient=18,
     flights=[{'from': [-640, 9312], 'to': [-1280, 9312], 'to_height': -768, 'width': 256, 'steps': 5, 'riser': CUT,
               'tread': RFLOOR, 'notes': "Steps out of the pool onto the near bank, in the doorway's south end."}],
     notes="The pool that sickens: a rock basin 1,024 by 1,344, its green water 160 under both banks; a causeway of three stone blocks (lifts) rises out of it when the levers are set right.")
room('room:far_bank', 'Yak Pool, far bank',
     outline=[[-192, 8832], [512, 8704], [1088, 8768], [1408, 9088], [1408, 10368], [1024, 10560], [128, 10560], [-192, 10368]],
     floor=-768, ceiling=0, ceiling_points=[[608, 9632, 192]], theme='theme:crypt', ambient=20,
     rough={'step': 192, 'depth': 48},
     notes="A wide cave 1,600 by 1,850 on the east shore: the sanctum way leaves north, the lich crypt east.")
room('room:lich_crypt', 'Lich crypt', outline=rect(1472, 9088, 3072, 10368), floor=-768, ceiling=-128,
     theme='theme:crypt_dressed', ambient=22,
     platforms=[{'id': 'platform:lich_tomb_1', 'at': [2272, 10208], 'size': [256, 128], 'rise': 64, 'surface': CUT, 'top_surface': SLAB,
                 'notes': "A stone tomb."}],
     notes="The crypt of the dead clergy who would not stay dead, 1,600 by 1,280; the Master's stair climbs from its south wall.")
room('room:sanctum_way', 'Sanctum way', outline=rect(256, 10624, 768, 11200), floor=-768, ceiling=256,
     theme='theme:sanctum', ambient=22, notes="A short dressed passage north to the sanctum's doors.")
sanct_pillars = []
for i in range(8):
    a = math.pi / 8 + i * math.pi / 4
    sanct_pillars.append({'at': [round(512 + 640 * math.cos(a)), round(12480 + 640 * math.sin(a))], 'size': [128, 128],
                          'surface': SLAB})
room('room:sanctum', "The Yak Master's sanctum", outline=octagon(512, 12480, 1216), floor=-768, ceiling=192,
     theme='theme:sanctum', ambient=20, pillars=sanct_pillars,
     platforms=[{'id': 'platform:sanctum_dais', 'at': [512, 13440], 'size': [896, 384], 'rise': 32, 'surface': SLAB,
                 'top_surface': FLAGS, 'notes': "The altar's dais, one step up."},
                {'id': 'platform:altar', 'at': [512, 13392], 'size': [384, 128], 'base': 32, 'rise': 96, 'surface': SLAB,
                 'top_surface': COFFER, 'notes': "The black altar of Yak."}],
     notes="An octagon 2,432 across and 960 high, eight green-black pillars in a ring, the altar on its dais before the reliquary door (north); the Master's cell east.")
room('room:reliquary', 'Reliquary', outline=rect(256, 13760, 768, 14272), floor=-768, ceiling=-320, theme='theme:sanctum',
     ambient=22, notes="A small shrine behind the altar, sealed by the Yak Master's will: the Elixir of Restoration.")
room('room:master_cell', "Master's cell", outline=rect(1792, 12096, 2816, 12864), floor=-768, ceiling=-128,
     theme='theme:sanctum', ambient=22,
     platforms=[{'id': 'platform:master_bed', 'at': [2560, 12480], 'size': [256, 384], 'rise': 48, 'surface': BEDWOOD,
                 'top_surface': SHEET, 'notes': "The Yak Master's bed against the east wall (d04's bed sheets and frames)."},
                {'at': [2240, 12800], 'size': [512, 96], 'rise': 256, 'surface': CAB, 'top_surface': COFFER,
                 'notes': "Robe cabinets along the north wall (d04's bedchamber has its 7t1cab cabinets so)."},
                {'id': 'platform:master_table', 'at': [2176, 12240], 'size': [256, 160], 'rise': 72, 'surface': RIVET,
                 'top_surface': BEDWOOD, 'notes': "A table with a candle by the south wall, off the doorway's axis."}],
     notes="The Yak Master's cell east of the sanctum: his bed and his hoard.")


# ================================================================ openings
op('open:yak_door', 'room:porch', 'room:narthex', link='link:porch_narthex', width=256, height=512, shape=None)
op('open:narthex_nave', 'room:narthex', 'room:nave', link='link:narthex_nave', width=1280, height=640, shape='arch', apex=704)
op('open:narthex_w', 'room:narthex', 'room:passage_w', link='link:narthex_passage_w', width=192, height=384)
op('open:narthex_e', 'room:narthex', 'room:passage_e', link='link:narthex_passage_e', width=192, height=384)
op('open:passage_w_dorm', 'room:passage_w', 'room:dormitory', link='link:passage_w_dormitory', width=320, height=384)
op('open:passage_e_lib', 'room:passage_e', 'room:library', link='link:passage_e_library', width=320, height=384)
op('open:dorm_cell', 'room:dormitory', 'room:hidden_cell', link='link:dormitory_hidden_cell', width=256, height=320)
op('open:dorm_refectory', 'room:dormitory', 'room:refectory', link='link:dormitory_refectory', width=384, height=448)
op('open:refectory_chapel', 'room:refectory', 'room:chapel_w', link='link:refectory_chapel_w', width=320, height=448)
op('open:chapel_w_nave', 'room:chapel_w', 'room:nave', link='link:chapel_w_nave', width=640, height=576, shape='arch', apex=704)
op('open:chapel_e_nave', 'room:chapel_e', 'room:nave', link='link:chapel_e_nave', width=640, height=576, shape='arch', apex=704)
op('open:library_vestry', 'room:library', 'room:vestry', link='link:library_vestry', width=384, height=448)
op('open:vestry_chapel', 'room:vestry', 'room:chapel_e', link='link:vestry_chapel_e', width=320, height=448)
op('open:treasury_gate', 'room:nave', 'room:treasury', link='link:nave_treasury', width=224, height=448)
op('open:refectory_stair', 'room:refectory', 'room:stair_w', link='link:refectory_stair_w', width=448, height=384)
op('open:stair_crypt', 'room:stair_w', 'room:crypt', link='link:stair_w_crypt', width=448, height=384)
op('open:vestry_master', 'room:vestry', 'room:master_stair', link='link:vestry_master_stair', width=320, height=384)
op('open:master_lich', 'room:master_stair', 'room:lich_crypt', link='link:master_stair_lich_crypt', width=384, height=384)
op('open:crypt_ossuary', 'room:crypt', 'room:ossuary', link='link:crypt_ossuary', width=448, height=448)
op('open:ossuary_bank', 'room:ossuary', 'room:near_bank', link='link:ossuary_near_bank', width=448, height=448)
op('open:bank_pool', 'room:near_bank', 'room:yak_pool', link='link:near_bank_pool', width=1024, height=576,
   notes="The near bank's whole middle opens onto the pool, 160 above its water.")
op('open:far_pool', 'room:far_bank', 'room:yak_pool', link='link:far_bank_pool', width=512, height=576,
   notes="The far landing of the causeway, 160 above the water.")
op('open:far_lich', 'room:far_bank', 'room:lich_crypt', link='link:far_bank_lich_crypt', width=384, height=448)
op('open:far_way', 'room:far_bank', 'room:sanctum_way', link='link:far_bank_sanctum_way', width=384, height=448)
op('open:sanctum_doors', 'room:sanctum_way', 'room:sanctum', link='link:sanctum_way_sanctum', width=224, height=448)
op('open:reliquary', 'room:sanctum', 'room:reliquary', link='link:sanctum_reliquary', width=256, height=384)
op('open:master_cell', 'room:sanctum', 'room:master_cell', link='link:sanctum_master_cell', width=192, height=384)
for o in openings:
    if o.get('shape') is None:
        o.pop('shape', None)

rooms_doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:temple', 'ambient': 22}, 'rooms': rooms,
             'openings': openings,
             'notes': "XD-06 Temple of Yak at L4 (x east, y north; the porch floor is 0, the undercroft -768). Two families: MM7's Temple of Baa (d04) for the temple above, the sanctum and the treasury; MM7's Barrow I (mdt03) for the crypts and the pool caves. Written by output/studio_cal/xd06/tools/gen.py."}

# ================================================================ objects
objects = {'format': 0}
objects['start'] = {'room': 'room:porch', 'at': [0, 384], 'facing': 90,
                    'notes': "Inside the temple door from the fairy woods, facing in."}
def _tile_doors(ds):
    for d in ds:
        if d.get('fold'):
            d['tile'] = True
    return ds


objects['doors'] = [
    {'id': 'door:yak_door', 'opening': 'open:yak_door', 'kind': 'slide_up', 'fold': True, 'surface': S('t5d1', 128, 256, scale=2),
     'notes': "The temple's inner door, iron-bound (d04's t5d1), folding up into its lintel."},
    {'id': 'door:narthex_w', 'opening': 'open:narthex_w', 'kind': 'slide_up', 'fold': True, 'surface': S('t5d1', 128, 256, scale=1.5)},
    {'id': 'door:narthex_e', 'opening': 'open:narthex_e', 'kind': 'slide_up', 'fold': True, 'surface': S('t5d1', 128, 256, scale=1.5)},
    {'id': 'door:hidden_cell', 'opening': 'open:dorm_cell', 'kind': 'slide_down', 'secret': True, 'surface': BRICK,
     'notes': "A secret door in the dormitory's west wall: the wall's own brick, flagged secret (it pulses for a perceptive party)."},
    {'id': 'door:treasury_gate', 'opening': 'open:treasury_gate', 'kind': 'slide_up', 'fold': True, 'surface': S('t5d1', 128, 256, scale=1.75),
     'notes': "The treasury gate behind its two iron bars."},
    {'id': 'door:master_door', 'opening': 'open:vestry_master', 'kind': 'slide_up', 'fold': True, 'surface': SLAB,
     'back_surface': SLAB, 'notes': "The Master's door at the top of his stair: a plain slab of the sanctum's stone, no ring on the vestry side."},
    {'id': 'door:sanctum_doors', 'opening': 'open:sanctum_doors', 'kind': 'slide_up', 'fold': True,
     'surface': S('t5d1', 128, 256, scale=1.75), 'notes': "The sanctum's double door."},
    {'id': 'door:reliquary', 'opening': 'open:reliquary', 'kind': 'slide_up', 'fold': True, 'surface': COFFER,
     'notes': "The reliquary's slab behind the altar, carved in the temple's coffer squares so that it reads as a sealed door against the green-black wall; held by the Yak Master's will, it rises when he dies."},
    {'id': 'door:master_cell', 'opening': 'open:master_cell', 'kind': 'slide_up', 'fold': True, 'surface': S('t5d1', 128, 256, scale=1.5)},
]
for _d in objects['doors']:
    if _d['id'] in ('door:yak_door', 'door:narthex_w', 'door:narthex_e', 'door:treasury_gate', 'door:sanctum_doors', 'door:master_cell'):
        _d.pop('fold', None)
        _d.pop('tile', None)
_tile_doors(objects['doors'])
# The two bars of the treasury gate: upright iron-dark posts in front of the gate on the nave side; each sinks into the
# floor when its lever is pulled.
GATE_X = -704
objects['movers'] = [
    {'id': 'mover:bar_w', 'room': 'room:nave', 'at': [GATE_X - 64, 5576], 'size': [48, 48], 'bottom': 0, 'height': 512,
     'travel': [0, 0, -516], 'speed': 160, 'surface': RIVET, 'top_surface': RIVET,
     'notes': "The west bar of the treasury gate: an upright of d04's riveted, iron-banded timber (7gt001a), 48 thick and 512 tall, standing 32 out from the gate's west half; it sinks into the floor when the west chapel's lever is pulled."},
    {'id': 'mover:bar_e', 'room': 'room:nave', 'at': [GATE_X + 64, 5576], 'size': [48, 48], 'bottom': 0, 'height': 512,
     'travel': [0, 0, -516], 'speed': 160, 'surface': RIVET, 'top_surface': RIVET,
     'notes': "The east bar: sinks when the library's lever is pulled."},
]
objects['lifts'] = []
for i, (cx, w) in enumerate(spans, start=1):
    objects['lifts'].append({'id': f'lift:span_{i}', 'room': 'room:yak_pool', 'at': [cx, 9696], 'size': [w, 384],
                             'travel': 160, 'speed': 120, 'surface': CUT,
                             'notes': f"Causeway block {i} of 3 (west to east): it lies in the pool, its top at the water, and rises 160 to the banks' height."})
objects['switches'] = [
    {'id': 'switch:bar_w', 'room': 'room:chapel_w', 'kind': 'button', 'size': [48, 48], 'depth': 24, 'off': S('7t1butt', 32, 32, scale=1.5), 'sides': BUTTS, 'wall': 'north', 'along': 0.3, 'height': 122,
     'notes': "The west chapel's button (MM7's carved 7t1butt push block on 7t1butts sides, as d04's and the Grand Temple of the Moon's): it sinks the treasury gate's west bar."},
    {'id': 'switch:bar_e', 'room': 'room:library', 'kind': 'button', 'size': [48, 48], 'depth': 24, 'off': S('7t1butt', 32, 32, scale=1.5), 'sides': BUTTS, 'wall': 'east', 'along': 0.5, 'height': 122,
     'notes': "The library's button: it sinks the treasury gate's east bar."},
    {'id': 'switch:bridge_1', 'room': 'room:near_bank', 'kind': 'button', 'size': [48, 48], 'depth': 24, 'off': S('7t1butt', 32, 32, scale=1.5), 'sides': BUTTS, 'block': 'platform:lever_post', 'side': 'w',
     'along': 0.25, 'height': 32, 'notes': "Bridge button 1 (south): moves blocks 1 and 2; it stays pressed in while its blocks are moved and comes out again on the next press."},
    {'id': 'switch:bridge_2', 'room': 'room:near_bank', 'kind': 'button', 'size': [48, 48], 'depth': 24, 'off': S('7t1butt', 32, 32, scale=1.5), 'sides': BUTTS, 'block': 'platform:lever_post', 'side': 'w',
     'along': 0.5, 'height': 32, 'notes': "Bridge button 2 (middle): moves blocks 2 and 3."},
    {'id': 'switch:bridge_3', 'room': 'room:near_bank', 'kind': 'button', 'size': [48, 48], 'depth': 24, 'off': S('7t1butt', 32, 32, scale=1.5), 'sides': BUTTS, 'block': 'platform:lever_post', 'side': 'w',
     'along': 0.75, 'height': 32, 'notes': "Bridge button 3 (north): moves block 3."},
]
objects['floors'] = [{'id': 'floor:yak_pool', 'of': 'room:yak_pool', 'kind': 'water',
                      'notes': "The pool's water: MM7's slime water (7slimywtr), the fluid bit; stepping in sickens (wiring)."}]


def light(id, rm, at, h, r, col, **kw):
    d = {'id': id, 'room': rm, 'at': at, 'height': h, 'radius': r, 'color': col}
    d.update(kw)
    return d


RED = [255, 90, 60]
FIRE = [255, 160, 90]
GREEN = [120, 255, 110]
objects['lights'] = [
    light('light:daylight', 'room:porch', [0, 96], 320, 900, [235, 245, 225], notes="The fairy woods' grey light through the open door."),
    light('light:idol', 'room:nave', [0, 5376], 360, 1400, [255, 70, 50], pulse={'intensity': [0.7, 1.0], 'frequency': 0.5},
          notes="A red glow over Yak's idol."),
    light('light:pool', 'room:yak_pool', [-768, 9696], 160, 1300, [150, 215, 110], pulse={'intensity': [0.35, 0.7], 'frequency': 0.35},
          notes="The pool's sick green glow (the tell)."),
    light('light:altar', 'room:sanctum', [512, 13392], 260, 1500, [255, 70, 50], pulse={'intensity': [0.6, 1.0], 'frequency': 0.6}),
    light('light:reliquary', 'room:reliquary', [512, 14016], 200, 600, [180, 220, 255]),
]
# Placed sounds (engine/audio counts since the studio's merge 38; rebase phase 0, 2026-11-20).
objects['sounds'] = [
    {'id': 'sound:pool', 'room': 'room:yak_pool', 'at': [-768, 9696], 'sound': 'bubbling cauldron01', 'radius': 2400,
     'inner_radius': 700, 'volume': 0.7, 'notes': "The Yak Pool bubbling: heard on both banks before it is seen."},
    {'id': 'sound:crypt_drip', 'room': 'room:crypt', 'at': [-2976, 7680], 'sound': 'drip02', 'radius': 1400,
     'volume': 0.6, 'wait': [3, 9], 'notes': "Water dripping in the crypt."},
    {'id': 'sound:ossuary_drip', 'room': 'room:ossuary', 'at': [-2976, 9184], 'sound': 'drip03', 'radius': 1300,
     'volume': 0.5, 'wait': [4, 11], 'notes': "Water dripping in the bone-house."},
    {'id': 'sound:altar_fire', 'room': 'room:sanctum', 'at': [512, 13200], 'sound': 'torch loop', 'radius': 1500,
     'inner_radius': 400, 'volume': 0.5, 'notes': "The torches round the Yak Master's altar."},
]
objects['chests'] = [
    {'id': 'chest:treasury', 'room': 'room:treasury', 'at': [-704, 6464], 'facing': 's', 'kind': '7gt002',
     'items': ['megacredit', 'megacredit', 'megacredit', 'megacredit', 'megacredit'], 'gold': 1500, 'treasure_level': 2,
     'random_items': 2, 'notes': "The cult's strongbox: five King's Megacredits, gold and two rolls of level 2."},
    {'id': 'chest:coffin', 'room': 'room:crypt', 'at': [-3680, 7680], 'facing': 'e', 'size': [128, 224, 72],
     'surface': SLAB, 'end_surface': S('t4s1fl', 128, 128, uneven=True), 'top_surface': SLAB, 'treasure_level': 2, 'random_items': 3,
     'notes': "A heavy stone coffin: a might test to open (the source's 'You are not strong enough to open the coffin.')."},
    {'id': 'chest:library', 'room': 'room:library', 'at': [3600, 3392], 'kind': '7gt002',
     'treasure_level': 2, 'random_items': 2, 'items': [1139, 1141],
     'notes': "The clerics' scroll chest (the source's spell books; here two scrolls of the Earth school and a roll of level 2)."},
    {'id': 'chest:hidden', 'room': 'room:hidden_cell', 'at': [-4192, 3200], 'facing': 's', 'kind': '7gt002',
     'treasure_level': 2, 'random_items': 3, 'notes': "A cleric's private hoard behind the secret door."},
    {'id': 'chest:hoard', 'room': 'room:master_cell', 'at': [1888, 12768], 'facing': 'e', 'size': [128, 64, 256],
     'surface': CAB, 'end_surface': S('7t1cab', 128, 256, uneven=True), 'top_surface': COFFER,
     'treasure_level': 3, 'random_items': 3, 'gold': 2500, 'notes': "The Yak Master's hoard (one step up: level 3)."},
    {'id': 'chest:reliquary', 'room': 'room:reliquary', 'at': [512, 14112], 'facing': 's', 'kind': '7gt002',
     'random_items': 0, 'items': ['elixir'], 'notes': "The reliquary casket: the Elixir of Restoration lies in it, an ordinary chest item (F15, 2026-11-21: quest items are looted, MM6-MM8 style); opening it runs Q-C12's hook, which sets elixir_found."},
]
# Spawn markers (the world's rows, A2; NOTES "Rebase, phase 0"): slot 1 Cultists (Xeen Cultist) a Cleric of Yak 11210
# (14), b Yak Priest 11211 (20), c Yak Elder 11212 (28); slot 2 Skeletons (Xeen Skeleton) b Spirit Bones 11241 (12),
# c Skeleton Lord 11242 (16); slot 3 Rotting dead (Xeen Zombie) c Grave Ghoul 11252 (18).
objects['spawns'] = [
    {'id': 'spawn:nave_s', 'room': 'room:nave', 'at': [0, 2560], 'slot': 1, 'tier': 'b', 'group': 51, 'notes': "Clerics at worship."},
    {'id': 'spawn:nave_m', 'room': 'room:nave', 'at': [-960, 3968], 'slot': 1, 'tier': 'b', 'group': 51},
    {'id': 'spawn:nave_n', 'room': 'room:nave', 'at': [960, 4800], 'slot': 1, 'tier': 'b', 'group': 51},
    {'id': 'spawn:chapel_w', 'room': 'room:chapel_w', 'at': [-1760, 4224], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:chapel_e', 'room': 'room:chapel_e', 'at': [1760, 4224], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:dormitory', 'room': 'room:dormitory', 'at': [-3040, 3008], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:refectory', 'room': 'room:refectory', 'at': [-2688, 4800], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:library', 'room': 'room:library', 'at': [2880, 3328], 'slot': 1, 'tier': 'a', 'group': 51},
    {'id': 'spawn:vestry', 'room': 'room:vestry', 'at': [2880, 4448], 'slot': 1, 'tier': 'b', 'group': 51},
    {'id': 'spawn:crypt_s', 'room': 'room:crypt', 'at': [-2560, 7232], 'slot': 2, 'tier': 'b', 'group': 51, 'notes': "The temple's dead, risen."},
    {'id': 'spawn:crypt_n', 'room': 'room:crypt', 'at': [-3328, 8192], 'slot': 2, 'tier': 'b', 'group': 51},
    {'id': 'spawn:ossuary_w', 'room': 'room:ossuary', 'at': [-3328, 9216], 'slot': 2, 'tier': 'b', 'group': 51},
    {'id': 'spawn:ossuary_e', 'room': 'room:ossuary', 'at': [-2624, 9536], 'slot': 2, 'tier': 'c', 'group': 51},
    {'id': 'spawn:near_bank', 'room': 'room:near_bank', 'at': [-1888, 9984], 'slot': 2, 'tier': 'c', 'group': 51},
    {'id': 'spawn:far_bank_s', 'room': 'room:far_bank', 'at': [640, 9216], 'slot': 2, 'tier': 'c', 'group': 51,
     'notes': "Skeletons waiting across the pool."},
    {'id': 'spawn:far_bank_n', 'room': 'room:far_bank', 'at': [768, 10176], 'slot': 2, 'tier': 'c', 'group': 51},
    # The lich crypt keeps its id; it holds Grave Ghouls (slot 3 Rotting dead, tier c).
    {'id': 'spawn:lich_w', 'room': 'room:lich_crypt', 'at': [1920, 9600], 'slot': 3, 'tier': 'c', 'group': 51},
    {'id': 'spawn:lich_e', 'room': 'room:lich_crypt', 'at': [2688, 9728], 'slot': 3, 'tier': 'c', 'group': 51},
    {'id': 'spawn:sanctum', 'room': 'room:sanctum', 'at': [512, 11776], 'slot': 1, 'tier': 'c', 'group': 51},
]
objects['monsters'] = [
    {'id': 'monster:yak_master', 'room': 'room:sanctum', 'monster': 11213, 'at': [512, 12992], 'facing': 270, 'hostile': True,
     'group': 2, 'carries': 'megacredit',
     'notes': "The Yak Master: the world's boss row 11213 (level 35, boss hit points; the row is named Yak Master, so the scene names nothing). He carries the sixth Megacredit."},
    {'id': 'monster:elder_w', 'room': 'room:sanctum', 'monster': 11212, 'at': [128, 12864], 'facing': 270, 'hostile': True,
     'group': 2, 'notes': "A Yak Elder: the Cultists' tier c row 11212 (level 28; the row is named Yak Elder)."},
    {'id': 'monster:elder_e', 'room': 'room:sanctum', 'monster': 11212, 'at': [896, 12864], 'facing': 270, 'hostile': True,
     'group': 2},
    {'id': 'monster:elder_vestry', 'room': 'room:vestry', 'monster': 11212, 'at': [3200, 4864], 'facing': 270, 'hostile': True,
     'group': 3, 'notes': "An elder robing in the vestry."},
]
# Relations: the world's own (assets_dev/worlds/xeen/relations.yml, A2) make the Cultists (11210-11213), Skeletons
# (11240-11242) and Rotting dead (11250-11252) the party's foes and set no feud among them, so the map has none.


def deco(id, rm, d, at, **kw):
    x = {'id': id, 'room': rm, 'decoration': d, 'at': at}
    x.update(kw)
    return x


decos = []
n = [0]


RED_ROOMS = {'room:nave', 'room:sanctum_way', 'room:sanctum', 'room:reliquary', 'room:master_cell', 'room:master_stair',
             'room:crypt', 'room:ossuary', 'room:lich_crypt'}


def torch(rm, wall, along, h=176):
    n[0] += 1
    decos.append({'id': f'deco:torch_{n[0]}', 'room': rm, 'decoration': 'torch07' if rm in RED_ROOMS else 'torch01',
                  'wall': wall, 'along': along, 'height': h})


for rm, walls in [('room:porch', [('north', 0.2), ('north', 0.8)]),
                  ('room:narthex', [('south', 0.15), ('south', 0.85), ('north', 0.1), ('north', 0.9)]),
                  ('room:nave', [('west', 0.15), ('west', 0.85), ('east', 0.15), ('east', 0.85), ('south', 0.12), ('south', 0.88),
                                 ('north', 0.15), ('north', 0.85)]),
                  ('room:chapel_w', [('south', 0.12), ('west', 0.15), ('north', 0.45)]),
                  ('room:chapel_e', [('south', 0.12), ('east', 0.85)]),
                  ('room:dormitory', [('south', 0.4), ('north', 0.25)]),  # lights audit: south 0.75 was in the doorway
                  ('room:refectory', [('west', 0.25), ('west', 0.75), ('south', 0.25)]),
                  ('room:library', [('north', 0.2), ('north', 0.6), ('west', 0.5), ('east', 0.3)]),
                  ('room:vestry', [('west', 0.25), ('south', 0.2), ('north', 0.8)]),  # lights audit: south 0.5 was in the doorway
                  ('room:treasury', [('east', 0.5), ('west', 0.5)]),
                  ('room:crypt', [('east', 0.25), ('east', 0.75), ('south', 0.25), ('west', 0.2), ('west', 0.8), ('north', 0.75)]),
                  ('room:ossuary', [('west', 0.5), ('north', 0.5)]),
                  ('room:lich_crypt', [('north', 0.3), ('north', 0.7), ('east', 0.5)]),
                  ('room:sanctum_way', [('east', 0.5), ('west', 0.5)]),
                  ('room:master_cell', [('south', 0.25), ('south', 0.75), ('north', 0.25), ('north', 0.75)]),
                  ('room:master_stair', [('west', 0.1), ('east', 0.3), ('west', 0.5), ('east', 0.7), ('west', 0.9)]),
                  ('room:reliquary', [('east', 0.5), ('west', 0.5)])]:
    for w, a in walls:
        if rm == 'room:master_stair':
            # lights audit (merge point 14): the stair falls 768 northward (y 5312 to 9024) and a torch's height is
            # over the room's top floor (0), so the lower torches stood above the sloped ceiling, in the rock: each
            # now hangs 176 over its own step
            y = 9024 - a * 3712 if w == 'west' else 5312 + a * 3712
            torch(rm, w, a, h=176 + round(-768 * (y - 5312) / 3712))
        else:
            torch(rm, w, a)
decos += [
    deco('deco:idol', 'room:nave', '7dec54', [0, 5376], floor_height=96, facing=270,
         notes="Yak's idol on its plinth (MM7's large statue, a stand-in for the yak-headed idol)."),
    deco('deco:dais_skulls_w', 'room:nave', 'sklplrev', [-416, 5376], floor_height=32),
    deco('deco:dais_skulls_e', 'room:nave', 'sklplrev', [416, 5376], floor_height=32),
    deco('deco:dais_candle_w', 'room:nave', 'cndlab0', [-224, 5184], floor_height=32),
    deco('deco:dais_candle_e', 'room:nave', 'cndlab0', [224, 5184], floor_height=32),
    deco('deco:chapel_w_statue', 'room:chapel_w', '7dec55', [-1760, 3692], floor_height=96, facing=90),
    deco('deco:chapel_e_statue', 'room:chapel_e', '7dec55', [1760, 3692], floor_height=96, facing=90),
    deco('deco:cask_1', 'room:refectory', '7dec21', [-2368, 3776]),
    deco('deco:cask_2', 'room:refectory', '7dec21', [-2528, 3776]),
    deco('deco:cask_3', 'room:refectory', '7dec21', [-2528, 5152]),
    deco('deco:treasury_skull', 'room:treasury', '7dec20', [-1024, 6528]),
    deco('deco:crypt_bones_1', 'room:crypt', '7dec18', [-2400, 8256]),
    deco('deco:crypt_bones_2', 'room:crypt', 'dec19', [-3520, 7104]),
    # lights audit (merge point 14): MM6's brazier hangs on chains, so every brazier hangs from the ceiling over its
    # place, its top 2 into it (146 high): height = the ceiling there - the floor - 148
    deco('deco:crypt_brazier_1', 'room:crypt', 'brazir2f', [-2272, 7488], height=556, hangs=True),
    deco('deco:crypt_brazier_2', 'room:crypt', 'brazir2f', [-2272, 7936], height=556, hangs=True),
    deco('deco:ossuary_pile_1', 'room:ossuary', 'sklplrev', [-3520, 8704]),
    deco('deco:ossuary_pile_2', 'room:ossuary', 'sklplrev', [-3520, 9664]),
    deco('deco:ossuary_pile_3', 'room:ossuary', 'sklplrev', [-2432, 8704]),
    deco('deco:ossuary_bones_1', 'room:ossuary', '7dec18', [-3008, 9216]),
    deco('deco:ossuary_bones_2', 'room:ossuary', 'dec19', [-3264, 8832]),
    deco('deco:ossuary_cage', 'room:ossuary', 'Bonecage', [-3456, 9216]),
    deco('deco:rim_bones_1', 'room:near_bank', '7dec18', [-1456, 10336], notes="Bones at the pool's rim (the tell), beyond the kerb's north end (off the pool steps' landing)."),
    deco('deco:rim_bones_2', 'room:near_bank', 'dec19', [-1600, 10450]),
    deco('deco:rim_skull', 'room:near_bank', '7dec20', [-1600, 8896]),
    deco('deco:far_bones', 'room:far_bank', '7dec18', [-64, 10240]),
    deco('deco:far_brazier', 'room:far_bank', 'brazir2f', [1216, 10304], height=648, hangs=True),
    deco('deco:far_brazier_2', 'room:far_bank', 'brazir2f', [1152, 9088], height=644, hangs=True),
    deco('deco:near_brazier', 'room:near_bank', 'brazir2f', [-2000, 8896], height=581, hangs=True),
    deco('deco:lich_pile', 'room:lich_crypt', 'sklplrev', [1664, 10176]),
    deco('deco:lich_brazier', 'room:lich_crypt', 'brazir2f', [2944, 10240], height=492, hangs=True),
    deco('deco:sanctum_brazier_w', 'room:sanctum', 'brazir2f', [160, 13584], floor_height=-736, height=780, hangs=True),
    deco('deco:sanctum_brazier_e', 'room:sanctum', 'brazir2f', [864, 13584], floor_height=-736, height=780, hangs=True),
    deco('deco:sanctum_skulls_w', 'room:sanctum', 'sklplrev', [-384, 12480]),
    deco('deco:sanctum_skulls_e', 'room:sanctum', 'sklplrev', [1344, 11776]),
    deco('deco:altar_candle_w', 'room:sanctum', 'cndlab0', [384, 13392], floor_height=-640),
    deco('deco:altar_candle_e', 'room:sanctum', 'cndlab0', [640, 13392], floor_height=-640),
    deco('deco:reliquary_candle', 'room:reliquary', 'cndlab0', [352, 14112]),
    deco('deco:master_candle', 'room:master_cell', 'cndlab0', [2176, 12240], floor_height=-696),
    deco('deco:master_barrel', 'room:master_cell', '7dec32', [2752, 12784]),
    deco('deco:master_skulls', 'room:master_cell', 'sklplrev', [2688, 12192]),
    deco('deco:stair_skulls', 'room:master_stair', 'sklplrev', [2560, 8896]),
]
objects['decorations'] = decos
objects['exits'] = [
    {'id': 'exit:woods', 'room': 'room:porch', 'wall': 'south', 'size': [224, 448], 'surface': S('7solid01', 128, 256, fit=True),
     'to': 'door:x2_woods', 'notes': "The temple's front door to the fairy woods' dark south end (X2)."},
]
objects['placeholders'] = [
    {'id': 'placeholder:yak_idol', 'room': 'room:nave', 'stands_for': "Yak's idol: a seated yak-headed god in black stone, horns curving up, as tall as the plinth is wide twice over",
     'at': [0, 5376], 'size': [256, 192, 384]},
]

# ================================================================ wiring
var = lambda n: {'map_var': n}
BED = "There is nothing on, in, or under the bed."
events = [
    # Hooks and dressing, D-7 (2026-11-20): the arrival window on the first arrival only (qbit arrived_once 110403)
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'not': {'qbit': 'arrived_once'}},
     'effects': [{'lua': 'XeenQuests.hook("m10.yak_arrival")'}, {'qbit': 'arrived_once'}],
     'notes': "Say why the party is here: A3's hook m10.yak_arrival (its window text; a one-shot timer: a load event's window is not shown), on the first arrival only (arrived_once)."},
    {'id': 'evt:exit_woods', 'preset': 'exit', 'source': 'exit:woods', 'title': 'Leave the Temple of Yak'},
    {'id': 'evt:yak_door', 'preset': 'door', 'source': 'door:yak_door', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:narthex_w', 'preset': 'door', 'source': 'door:narthex_w', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:narthex_e', 'preset': 'door', 'source': 'door:narthex_e', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:hidden_cell', 'preset': 'door', 'source': 'door:hidden_cell', 'title': 'Wall', 'action': 'open',
     'text': "A block of the wall gives under your hand and sinks: a hidden cell!"},
    {'id': 'evt:sanctum_doors', 'preset': 'door', 'source': 'door:sanctum_doors', 'title': 'Door', 'action': 'open'},
    {'id': 'evt:master_cell', 'preset': 'door', 'source': 'door:master_cell', 'title': 'Door', 'action': 'open'},
    # The treasury gate and its two bars.
    {'id': 'evt:bar_w', 'preset': 'switch', 'source': 'switch:bar_w', 'title': 'Button',
     'condition': {'not': var('bar_w')}, 'opens': ['mover:bar_w'], 'sets': var('bar_w'),
     'effects': [{'set_texture': {'of': 'panel:plaque_w', 'to': 't4s1fl'}}],
     'text': "You push the stone button in, and the carving round it darkens. Out in the nave, iron grinds on stone: the west bar before the treasury gate sinks into the floor.",
     'seconds': 7, 'else_effects': [{'text': "The button is pressed in. The treasury gate's west bar is sunk."}]},
    {'id': 'evt:bar_e', 'preset': 'switch', 'source': 'switch:bar_e', 'title': 'Button',
     'condition': {'not': var('bar_e')}, 'opens': ['mover:bar_e'], 'sets': var('bar_e'),
     'effects': [{'set_texture': {'of': 'panel:plaque_e', 'to': 't4s1fl'}}],
     'text': "You push the stone button in, and the carving round it darkens. Out in the nave, iron grinds on stone: the east bar before the treasury gate sinks into the floor.",
     'seconds': 7, 'else_effects': [{'text': "The button is pressed in. The treasury gate's east bar is sunk."}]},
    {'id': 'evt:treasury_gate', 'preset': 'door', 'source': 'door:treasury_gate', 'title': 'Treasury gate', 'action': 'open',
     'condition': {'all': [var('bar_w'), var('bar_e')]},
     'text': "With both bars sunk, the treasury gate lifts.", 'locked_text': "The treasury gate is barred.",
     'else_effects': [{'lua': "local w = IsAtLeast(MapVar(bar_w), 1)\nlocal e = IsAtLeast(MapVar(bar_e), 1)\n"
                              "local s = 'The treasury gate will not move: two iron bars stand before it, each worked by a stone button somewhere in the temple (the clerics keep one in a chapel, one among their books). '\n"
                              "if w then s = s .. 'The west bar is sunk; ' else s = s .. 'The west bar is up; ' end\n"
                              "if e then s = s .. 'the east bar is sunk.' else s = s .. 'the east bar is up.' end\n"
                              "evt.SimpleMessage(s)"}],
     'notes': "set piece:twin_bars. Both levers (west chapel, library) must be pulled; the gate says which bar still stands and where the levers are."},
    {'id': 'evt:gate_seen', 'preset': 'text', 'trigger': 'step', 'source': 'platform:dais', 'once': True,
     'text': "West of the idol stands a barred gate: the clerics' treasury.", 'seconds': 5},
    # The Master's door: one side opens it, the other says why not.
    {'id': 'evt:master_door', 'preset': 'door', 'source': 'door:master_door', 'side': 'room:master_stair', 'title': 'Stone door', 'action': 'open',
     'sets': var('master_door'), 'text': "The slab grinds up: beyond lies the temple's vestry. The way out is short from here.",
     'notes': "From the Master's stair (the door's back, the `to` room's side): it opens."},
    {'id': 'evt:master_door_front', 'preset': 'script', 'source': 'door:master_door', 'side': 'room:vestry', 'title': 'Stone door',
     'condition': {'not': var('master_door')},
     'effects': [{'text': "A plain slab without ring or handle. It is meant to be opened from the other side."}],
     'locked_text': "The slab stands open.",
     'notes': "From the vestry: no way to open it; once opened from the stair it stays open."},
    # The Yak Pool: the bridge levers, the water that sickens, the basin.
    {'id': 'evt:pool_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:near_bank', 'once': True,
     'text': "Green water fills the cave below, bubbling and stinking of rot; bones lie at its rim. Three stone blocks lie in a line under the surface toward the far shore, and three stone buttons are set in a kerb at the edge.",
     'seconds': 8},
    {'id': 'evt:bridge_1', 'preset': 'switch', 'source': 'switch:bridge_1', 'title': 'Button', 'toggles': ['lift:span_1', 'lift:span_2'],
     'text': "The button grinds in or out, and stone moves in the pool.", 'notes': "Moves blocks 1 and 2."},
    {'id': 'evt:bridge_2', 'preset': 'switch', 'source': 'switch:bridge_2', 'title': 'Button', 'toggles': ['lift:span_2', 'lift:span_3'],
     'text': "The button grinds in or out, and stone moves in the pool.", 'notes': "Moves blocks 2 and 3."},
    {'id': 'evt:bridge_3', 'preset': 'switch', 'source': 'switch:bridge_3', 'title': 'Button', 'toggles': ['lift:span_3'],
     'text': "The button grinds in or out, and stone moves in the pool.", 'notes': "Moves block 3."},
    {'id': 'evt:pool_fall', 'preset': 'script', 'trigger': 'step', 'source': 'room:yak_pool',
     'effects': [{'lua': "evt.ForPlayer(Players.All)\nSetValue(DiseasedGreen, 0)"}],
     'text': "The pool makes you ill.",
     'notes': "Anyone who wades into the green water is diseased (the source's 'The pool makes you ill.')."},
    {'id': 'evt:yak_pool', 'preset': 'script', 'source': 'platform:yak_basin', 'title': 'Yak Pool',
     'condition': {'not': {'player_bit': 10400}},
     'effects': [{'player_bit': 10400}, {'add': {'var': 'BaseEndurance', 'value': 2}},
                 {'lua': "SetValue(DiseasedGreen, 0)"},
                 {'text': "You drink from the Yak Pool. Strength runs through your limbs (+2 Endurance, permanent), and then the sickness takes you: the pool makes you ill."}],
     'else_effects': [{'lua': "SetValue(DiseasedGreen, 0)"}, {'text': "The pool makes you ill."}],
     'notes': "The source's Yak Pools: +5 Endurance (permanent) with sickness; here +2 once per character (MM6-8's fountain size), and disease every time."},
    # Chests.
    {'id': 'evt:chest_treasury', 'preset': 'chest', 'source': 'chest:treasury', 'title': 'Chest',
     'effects': [{'lua': 'XeenQuests.hook("m10.yak_treasury")'}],
     'notes': "A3's hook m10.yak_treasury (once): sets treasury_opened, the experience and the text; the chest holds the five Megacredits (the hook's map_gives)."},
    {'id': 'evt:chest_coffin', 'preset': 'chest', 'source': 'chest:coffin', 'title': 'Coffin',
     'condition': {'stat': {'name': 'ActualMight', 'at_least': 25}},
     'else_effects': [{'text': "You are not strong enough to open the coffin."}],
     'notes': "A might test (25, the member's actual Might: a Might potion or spell helps, as the other stat chests; A3 2026-11-22) on the member who tries, as the source's coffins."},
    {'id': 'evt:chest_library', 'preset': 'chest', 'source': 'chest:library', 'title': 'Chest'},
    {'id': 'evt:chest_hidden', 'preset': 'chest', 'source': 'chest:hidden', 'title': 'Chest'},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Cabinet'},
    {'id': 'evt:chest_reliquary', 'preset': 'chest', 'source': 'chest:reliquary', 'title': 'Chest',
     'effects': [{'lua': 'XeenQuests.hook("q-c12.reliquary")'}],
     'notes': "A3's hook q-c12.reliquary (once): sets elixir_found; the Elixir of Restoration is the casket's item (F15)."},
    # Things to click that hold nothing.
    {'id': 'evt:tomb_1', 'preset': 'text', 'source': 'platform:tomb_1', 'title': 'Coffin', 'text': "There is nothing in the coffin."},
    {'id': 'evt:tomb_2', 'preset': 'text', 'source': 'platform:tomb_2', 'title': 'Coffin', 'text': "There is nothing in the coffin."},
    {'id': 'evt:lich_tomb', 'preset': 'text', 'source': 'platform:lich_tomb_1', 'title': 'Coffin', 'text': "There is nothing in the coffin."},
    {'id': 'evt:master_bed', 'preset': 'text', 'source': 'platform:master_bed', 'title': 'Bed', 'text': BED},
    {'id': 'evt:crate', 'preset': 'text', 'source': 'platform:crate', 'title': 'Crate', 'text': "There is nothing in the crate."},
    # The Yak Master.
    {'id': 'evt:sanctum_seen', 'preset': 'text', 'trigger': 'step', 'source': 'room:sanctum', 'once': True,
     'text': "The Yak Master turns from his altar. Behind it a slab seals the reliquary; it will hold while he lives.",
     'seconds': 6},
    {'id': 'evt:master_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'monster': 'monster:yak_master'}},
     'opens': ['door:reliquary'],
     'effects': [{'qbit': 'yak_master_slain'}, {'add': {'var': 'Experience', 'value': 5000}}],
     # m10.yak_master has no call: the map sets its bit; the Master carries the sixth Megacredit (its map_gives).
     'text': "The Yak Master falls, and the slab behind the altar grinds up: the reliquary is open.", 'seconds': 6,
     'notes': "set piece:master: his death opens the reliquary."},
    {'id': 'evt:reliquary', 'preset': 'script', 'source': 'door:reliquary', 'title': 'Reliquary',
     'condition': {'not': {'qbit': 'yak_master_slain'}},
     'effects': [{'text': "The slab will not move while the Yak Master lives."}], 'locked_text': "The reliquary stands open."},
]
for i in range(3):
    for j in range(2):
        events.append({'id': f'evt:bed_{i}{j}', 'preset': 'text', 'source': f'platform:bed_{i}{j}', 'title': 'Bed', 'text': BED})

wiring = {'format': 0, 'variables': ['bar_w', 'bar_e', 'master_door'], 'events': events}

project = {
    'format': 0, 'id': 'xeen_xd06', 'name': 'Temple of Yak', 'world': 'xeen', 'kind': 'indoor', 'profile': 'dungeon',
    'map_code': 'XD-06', 'units': {'plan_grid': 512}, 'extent': {'footprint_cells': [17, 29], 'climbs': 's'},
    'map_stats': {'id': 9139, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 2, 'perception_difficulty': 2,
                  'refill_days': 672, 'music': 28, 'environment': 'stone hall', 'lock_difficulty': 2, 'bolster': 'LowerToEqual',
                  'slots': [{'monster': 'Xeen Cultist', 'tier': 2, 'per_marker': [2, 3], 'weight': 45},
                            {'monster': 'Xeen Skeleton', 'tier': 4, 'per_marker': [2, 3], 'weight': 45},
                            {'monster': 'Xeen Zombie', 'tier': 5, 'per_marker': [1, 2], 'weight': 10}]},
    'neighbours': [
        {'id': 'door:x2_woods', 'to': 'xeen_x2.odm', 'kind': 'door', 'arrival': [-1024, -17840, 1053], 'direction': 90,
         'arrival_hint': "In the fairy woods' dark south end on X2, 400 in front of the Temple of Yak's door (X2 door:xd06, click face at -1024, -18240, 1088, cells [62, 99.63]), facing away from it, north.",
         'notes': "X2 (Rivercity and Lake Darzog): the outside arrival from devdocs/xeen/briefs/x2/DOORS.md (final values from X2's built map, 2026-11-16). X2's door needs the Yak Stone (qbit 110101)."},
    ],
    'qbits': {'elixir_found': 110400, 'yak_master_slain': 110401, 'treasury_opened': 110402, 'arrived_once': 110403},
    'items': {'elixir': 12191, 'megacredit': 12192},
    'notes': "Xeen design brief, level L4: the Temple of Yak built with the studio's words, a playable map (NOTES.md), installed in the Xeen world (assets_dev/worlds/xeen/maps). Story step M10 (King's Megacredits for Newcastle) and Q-C12 (Mirabeth's Elixir of Restoration): devdocs/xeen/QUESTS.md, source/quests/m10.yml and q-c12.yml. Monsters are the world's rows (A2): slot 1 Cultists (Xeen Cultist: Cleric of Yak 11210 at tier a, Yak Priest 11211 at b, Yak Elder 11212 at c), slot 2 Skeletons (Xeen Skeleton: Spirit Bones 11241 at b, Skeleton Lord 11242 at c), slot 3 Rotting dead (Xeen Zombie: Grave Ghoul 11252 at c, in the lich crypt); the three placed Yak Elders are 11212, the Yak Master the boss row 11213. The map_stats row 9139 is the world's (A2's source/map_rows.yml); this card matches it. Items: the Elixir of Restoration 12191, the King's Megacredit 12192. Quest bits 110400-110402 (M10's and Q-C12's names; the map's range 110400-110469). Music: track 28. door:x2_woods leads to X2 at DOORS.md's final arrival (-1024, -17840, 1053, facing north).",
}

if __name__ == '__main__':
    L4.mkdir(parents=True, exist_ok=True)
    for name, doc in [('rooms.yml', rooms_doc), ('objects.yml', objects), ('wiring.yml', wiring), ('project.yml', project)]:
        text = yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120)
        (L4 / name).write_text(text)
    print('written')
