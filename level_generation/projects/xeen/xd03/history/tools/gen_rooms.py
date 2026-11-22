# XD-03 Deep Mine, L4: the shell (rooms.yml). A first-shell generator kept in the scratch folder; numbers are design
# numbers (there is no original). Run: python3 gen_rooms.py <L4 folder>. Once the project has hand edits the files
# are the source.
import sys
import yaml

L4 = sys.argv[1]


def S(t, w=None, h=None, **kw):
    d = {'texture': t}
    if w:
        d['size'] = [w, h]
    d.update(kw)
    return d


def octo(cx, cy, a, b):
    """Octagon with half-width a and the chamfer's half-length b, counter-clockwise from east-south."""
    return [[cx + a, cy - b], [cx + a, cy + b], [cx + b, cy + a], [cx - b, cy + a],
            [cx - a, cy + b], [cx - a, cy - b], [cx - b, cy - a], [cx + b, cy - a]]


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# Surfaces
DEEP = S('c2b', 256, 256)
DEEP1 = S('c2b', 256, 256)
CAVEFLOOR = S('cfb1', 128, 128)
CAVESTONES = S('cfb1', 128, 128)
BASALT = S('vlcwl1lg', 256, 256)
COLUMNS = S('vlcwl2', 128, 256)
SLAGROCK = S('vlcwl1', 128, 256)
SOOTBRICK = S('d2wlactr', 128, 256)
BIGBLOCK = S('vlcwl3a', 128, 256)
OLDBLOCK = S('7cdb', 128, 256)
DRESSED = S('ctwl5', 256, 256)
PILASTER = S('ctwl5le', 128, 256, fit=True)
RUNES = S('vlctrm3', 128, 128)
RUNEFRIEZE = S('vlctrm3', 128, 128)
RUNEGLOW = S('7tfb1', 128, 128)
DARKFLAGS = S('vlcflore', 128, 128)
HEATFLAGS = S('vlcflorc', 128, 128)
FLAGSTONE = S('vlcflora', 128, 128)
CRYSTALFLOOR = S('crdrf1', 128, 128)
INLAY = S('ctflor1', 128, 128)
ROCKCEIL = S('d2ceil3', 256, 256)
BEAMCEIL = S('d2ceil1', 256, 256)
GREYROCK = S('vlcgnrc2', 256, 256)
CRYSTAL = S('crstont', 256, 256)
GOLDROCK = S('c1gold', 256, 256)
GOLDDEEP = S('c2b', 256, 256)
EARTHROCK = S('c2b', 256, 256)
DIRT = S('cfb1', 128, 128)
POST = S('bemv16a', 16, 256)
MINEPOST = S('trim11_32', 32, 64)
MINEBEAM = S('trim9_32a', 64, 32)
DRESSED2 = S('ctwl2', 256, 256)
TFB2 = S('tfb2', 128, 128)
BEAM = S('bemh16a', 256, 16)
PLANKS = S('bemvwal', 128, 256)
PLANKFLOOR = S('7trimda', 256, 128)
IRON = S('ch004i', 64, 64)
LAVA = S('orfyrlga', 256, 256)
GLOW = S('orfyrlga', 256, 256)
COPPER = S('ctflor5', 128, 128)
SKULL = S('ctceil3', 128, 128, fit=True)
WEB = S('c2b', 256, 256)
GEODEWALL = S('crstont', 256, 256)
CRACKED = S('crstont', 256, 256)
GEMWALL = S('d3ystlwl', 256, 256, fit=True)
DARKFLAGS2 = S('vlcflore', 128, 128)
DARKIRON = S('vlcgnrc3', 256, 256)

themes = [
    {'id': 'theme:deep_rock', 'wall': DEEP, 'floor': CAVEFLOOR, 'ceiling': DEEP1,
     'notes': "Deep rock: XD-02's Deep Line rock (c2b) and its dark cave floor, at the landing, the Deep Line head, "
              "the sentry cut, the breach and the escape shaft."},
    {'id': 'theme:clan_hold', 'wall': SOOTBRICK, 'bands': [{'height': 128, 'surface': BIGBLOCK}],
     'floor': DARKFLAGS, 'ceiling': BEAMCEIL, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),
     'notes': "The clan's hold: soot-blackened dwarven brick over a footing of big dressed blocks, dark flagstones, "
              "plank ceilings on beams (d2ceil1), carved rune stone in the doorways, the studded skull door."},
    {'id': 'theme:forge', 'wall': BASALT,
     'bands': [{'height': 128, 'surface': BIGBLOCK}, {'height': 448, 'surface': SOOTBRICK}],
     'floor': HEATFLAGS, 'ceiling': ROCKCEIL, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),
     'notes': "The forge floor: big dressed blocks and soot-black brick up to 576, raw grey volcanic rock above it "
              "to the rough roof; flagstones cracked by heat with the glow in their seams."},
    {'id': 'theme:tower', 'wall': SOOTBRICK, 'bands': [{'height': 128, 'surface': BIGBLOCK}],
     'floor': FLAGSTONE, 'ceiling': GREYROCK, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),
     'notes': "The furnace tower on the smelter's old stack: soot brick, worn flagstones, a sooty flue overhead."},
    {'id': 'theme:king_hall', 'wall': DRESSED,
     'bands': [{'height': 96, 'surface': BIGBLOCK}, {'height': 576, 'surface': DRESSED},
               {'height': 704, 'surface': S('vlctrm3', 128, 128)}],
     'ends': {'length': 128, 'surface': PILASTER},
     'floor': DARKFLAGS2, 'ceiling': ROCKCEIL, 'reveal': RUNES, 'door': S('d2lgdor', 256, 256, fit=True),
     'notes': "The Clan King's hall: dressed red-brown blocks over a dark footing, a frieze of carved runes, carved "
              "pilasters in every corner, a floor of red stone inlay, the geode's crystal in the dome."},
    {'id': 'theme:hoard', 'wall': GOLDROCK, 'floor': TFB2, 'ceiling': GOLDDEEP, 'reveal': DEEP,
     'door': S('d2lgdor', 256, 256, fit=True),
     'notes': "The King's hoard: raw rock shot with gold veins, the hall's red inlay floor."},
    {'id': 'theme:geode', 'wall': CRYSTAL, 'floor': CRYSTALFLOOR, 'ceiling': CRACKED, 'reveal': DEEP,
     'notes': "The geode: blue-green crystal walls and crown, a floor of crushed blue crystal."},
    {'id': 'theme:dwarf_vault', 'wall': S('cwb', 128, 256), 'bands': [{'height': 96, 'surface': OLDBLOCK}], 'floor': S('7tfb1', 128, 128), 'ceiling': S('cwb', 128, 256), 'reveal': OLDBLOCK,
     'notes': "Red Dwarf work: the older olive-grey dwarven blocks, dark flagstones, rune stone round the doorway."},
    {'id': 'theme:warren', 'wall': EARTHROCK, 'floor': DIRT, 'ceiling': EARTHROCK,
     'notes': "The mole warren: brown earthy rock bored by the moles, loose earth underfoot."},
]

rooms = []
openings = []


def room(**kw):
    rooms.append(kw)
    return kw


def opening(**kw):
    openings.append(kw)
    return kw


# ---------------------------------------------------------------------------------------------------------- arrival
room(id='room:deep_line', name='Deep Line head', space='room:deep_landing',
     outline=rect(7744, 960, 8320, 1216), floor=384, ceiling=640, theme='theme:deep_rock', ambient=22,
     platforms=[
         {'rise': 4, 'outline': rect(7744, 1032, 8304, 1044), 'surface': IRON, 'top_surface': IRON, 'notes': 'Rail'},
         {'rise': 4, 'outline': rect(7744, 1132, 8304, 1144), 'surface': IRON, 'top_surface': IRON, 'notes': 'Rail'},
     ],
     beams=[{'path': [[7904, 960], [7904, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': MINEBEAM},
            {'path': [[8160, 960], [8160, 1216]], 'width': 32, 'depth': 32, 'bottom': 576, 'surface': MINEBEAM}],
     notes="The foot of XD-02's Deep Line: a short level stretch of rock-cut tunnel with its rails, where the line "
           "comes in from the Red Dwarf Mines; the way back is its east end (the exit), the way on its west mouth, "
           "high in the landing's east wall.")

surface_z = lambda x: 384 - (7296 - x) / 2.0
trestle_posts = []
for x in (7168, 6976, 6784):
    top = int(surface_z(x)) - 40
    for y in (1048, 1128):
        trestle_posts.append({'at': [x, y], 'size': [24, 24], 'rise': top, 'surface': MINEPOST, 'top_surface': MINEPOST,
                              'notes': 'Trestle post'})
rail_beams = []
for y in (1040, 1136):
    rail_beams.append({'path': [[7296, y], [6592, y]], 'width': 12, 'depth': 16, 'bottom': 368,
                       'bottom_end': 16, 'surface': IRON, 'notes': 'Rail of the incline'})
    rail_beams.append({'path': [[7296, y + 8], [6640, y + 8]], 'width': 28, 'depth': 24, 'bottom': 344,
                       'bottom_end': 16, 'surface': MINEBEAM, 'notes': 'Stringer under the rail'})
for x in (7168, 6976, 6784):
    rail_beams.append({'path': [[x, 1024], [x, 1152]], 'width': 24, 'depth': 24,
                       'bottom': int(surface_z(x)) - 64, 'surface': MINEBEAM, 'notes': "Cap of a trestle bent"})

room(id='room:deep_landing', name='Deep landing',
     outline=[[6144, 768], [6272, 640], [7552, 640], [7680, 768], [7680, 1408], [7552, 1536], [6272, 1536],
              [6144, 1408]],
     floor=0, ceiling=640, theme='theme:deep_rock', ambient=22,
     rough={'step': 192, 'depth': 36},
     ceiling_points=[[7680, 768, 896], [7680, 1408, 896], [7552, 640, 832], [7552, 1536, 832],
                     [7104, 1088, 1024], [6464, 1088, 768], [6144, 768, 576], [6144, 1408, 576]],
     levels=[{'id': 'level:head_ledge', 'outline': rect(7296, 832, 7680, 1344), 'floor': 384, 'edge': DEEP,
              'surface': CAVEFLOOR, 'notes': "The ledge at the Deep Line's mouth, where the cart waits."}],
     platforms=trestle_posts + [
         {'rise': 4, 'outline': rect(6240, 1034, 6600, 1046), 'surface': IRON, 'top_surface': IRON,
          'notes': 'Rail on the floor'},
         {'rise': 4, 'outline': rect(6240, 1130, 6600, 1142), 'surface': IRON, 'top_surface': IRON,
          'notes': 'Rail on the floor'},
         {'at': [6224, 1088], 'size': [48, 224], 'rise': 112, 'surface': MINEBEAM, 'end_surface': MINEPOST,
          'top_surface': MINEBEAM, 'notes': 'The buffer stop: a baulk of timber across the rails'},
         {'at': [6192, 1088], 'size': [32, 288], 'rise': 64, 'surface': BIGBLOCK, 'notes': "The buffer's stone"},
     ],
     beams=rail_beams,
     notes="Rock platform at the foot of the Deep Line, 1536 x 896, its roof rising to 1024 where the line comes down "
           "out of the east wall. The Deep Line's last pitch is a timber trestle falling 384 from the mouth ledge to "
           "the floor; the cart (a mover) runs down it and back with the party on it; a buffer stop at the west end.")

room(id='room:sentry_cut', name='Sentry cut',
     path=[[6528, 1600, 0], [6528, 2112, 0], [6272, 2368, 0], [6272, 2752, 0], [5824, 2752, -64],
           [5184, 2752, -128]],
     width=256, floor=0, ceiling=384, theme='theme:deep_rock', ambient=24,
     platforms=[{'at': p, 'size': [24, 24], 'rise': 340, 'surface': MINEPOST, 'top_surface': MINEPOST, 'notes': 'Timber set post'}
                for p in ([6420, 1820], [6636, 1820], [6420, 2060], [6636, 2060])] +
               [{'at': p, 'size': [24, 24], 'rise': 330, 'surface': MINEPOST, 'top_surface': MINEPOST, 'notes': 'Timber set post'}
                for p in ([5600, 2644], [5600, 2860])],
     beams=[{'path': [[6408, y], [6648, y]], 'width': 32, 'depth': 28, 'bottom': 340, 'surface': MINEBEAM,
             'notes': 'Cap of a timber set'} for y in (1820, 2060)] +
           [{'path': [[5600, 2632], [5600, 2872]], 'width': 32, 'depth': 24, 'bottom': 240, 'surface': MINEBEAM,
             'notes': 'Cap of a timber set'}],
     notes="The way in: a rock cut north from the landing, a jog west, the run past the lookout niche, then west and "
           "down 128 to the gallery door in the furnace hall's east wall.")
room(id='room:sentry_lookout', name='Lookout niche', space='room:sentry_cut',
     outline=rect(6464, 2432, 6720, 2688), floor=0, ceiling=320, theme='theme:deep_rock', ambient=20,
     notes="The lookouts' niche off the cut's east side.")

# ---------------------------------------------------------------------------------------------------- furnace hall
A = lambda x: x - 608   # near-bank edge of the slag channel (y = x - 608)
B = lambda x: x - 64    # far-bank edge (y = x - 64)
channel = [[2592, 1984], [4352, 3744], [3808, 3744], [2592, 2528]]
north_span = [[3920, 3312], [4352, 3744], [3808, 3744], [3648, 3584]]
south_bridge = [[2960, 2352], [3096, 2488], [2824, 2760], [2688, 2624]]
smelter = octo(4224, 2048, 224, 96)
gong_x, gong_y = 4912, 3640
gong_slabs = []
for i, (w, b) in enumerate([(96, 64), (160, 96), (192, 128), (192, 160), (160, 192), (96, 224)]):
    gong_slabs.append({'at': [gong_x, gong_y], 'size': [w, 12], 'base': b + 32 + 384, 'rise': 32, 'surface': COPPER,
                       'end_surface': COPPER, 'top_surface': COPPER})
gong_slabs[2]['id'] = 'platform:gong'
gong_slabs[2]['notes'] = "The great gong (clicked): a bronze disc built of six slabs hanging in its frame."

room(id='room:furnace_hall', name='Furnace Hall',
     outline=[[2560, 1536], [4928, 1536], [5120, 1728], [5120, 3776], [2560, 3776]],
     floor=-512, ceiling=320, theme='theme:forge', ambient=22,
     ceiling_points=[[3712, 2624, 704], [3136, 2112, 544], [4352, 3200, 576], [2976, 3264, 576],
                     [4224, 2048, 640], [3520, 3584, 448], [4544, 2400, 512], [3456, 1792, 448]],
     levels=[
         {'id': 'level:slag', 'outline': channel, 'floor': -640, 'edge': SLAGROCK, 'surface': LAVA,
          'notes': "The slag channel: 384 wide and 128 deep, running at 45 degrees from under the north span to the "
                   "west wall; molten slag underfoot (lava in objects.yml floors)."},
         {'id': 'level:gallery', 'outline': rect(4704, 2432, 5120, 3776), 'floor': -128, 'edge': BIGBLOCK,
          'surface': DARKFLAGS,
          'notes': "The gong gallery: a balcony 384 over the hall along its east wall, behind a parapet."},
     ],
     pillars=[{'outline': smelter, 'surface': BIGBLOCK,
               'notes': "The ruined smelter's stack, floor to roof; its chimney goes up into the rock."}],
     platforms=[
         {'id': 'platform:north_span', 'outline': north_span, 'base': 80, 'rise': 48, 'surface': BIGBLOCK,
          'top_surface': FLAGSTONE, 'bottom_surface': BIGBLOCK,
          'notes': "The north span: a broad stone slab over the channel's head, 270 wide at the far bank, 660 at the "
                   "near; no rails."},
         {'id': 'platform:south_bridge', 'outline': south_bridge, 'base': 80, 'rise': 48, 'surface': BIGBLOCK,
          'top_surface': FLAGSTONE, 'bottom_surface': BIGBLOCK,
          'notes': "The south bridge: a narrow slab 192 wide near the channel's foot; no rails."},
         {'outline': octo(4224, 2048, 320, 132), 'rise': 192, 'surface': BIGBLOCK, 'top_surface': BIGBLOCK,
          'notes': "The smelter's furnace: a stone base round the stack."},
         {'id': 'platform:furnace_mouth', 'at': [4224, 2376], 'size': [176, 16], 'base': 16, 'rise': 144,
          'surface': GLOW, 'end_surface': BIGBLOCK,
          'notes': "The smelter's cold furnace mouth on its north face, still glowing."},
         {'at': [4224, 2388], 'size': [240, 24], 'base': 160, 'rise': 24, 'surface': DARKIRON,
          'top_surface': DARKIRON, 'notes': "The mouth's iron lintel"},
         {'at': [gong_x, gong_y], 'size': [320, 96], 'base': 384, 'rise': 32, 'surface': BIGBLOCK, 'top_surface': BIGBLOCK,
          'notes': "The gong's plinth"},
         {'at': [gong_x - 136, gong_y], 'size': [24, 24], 'base': 416, 'rise': 320, 'surface': POST,
          'notes': "Gong frame post"},
         {'at': [gong_x + 136, gong_y], 'size': [24, 24], 'base': 416, 'rise': 320, 'surface': POST,
          'notes': "Gong frame post"},
     ] + gong_slabs,
     flights=[
         {'from': [5008, 1968], 'to': [5008, 2432], 'width': 192, 'steps': 12,
          'sides': {'height': 64, 'thickness': 24, 'surface': BIGBLOCK}, 'riser': BIGBLOCK, 'tread': DARKFLAGS,
          'notes': "The gallery stair: twelve steps of 32 down along the east wall."},
         {'from': [3151, 2791], 'to': [3275, 2667], 'width': 352, 'steps': 4, 'riser': BIGBLOCK, 'tread': FLAGSTONE,
          'notes': "The slag steps: four steps out of the main reach onto the near bank, beside the south bridge."},
         {'from': [2692, 2332], 'to': [2816, 2208], 'width': 224, 'steps': 4, 'riser': SLAGROCK, 'tread': FLAGSTONE,
          'notes': "The drain steps: the way out of the south reach, beside the breach."},
     ],
     parapets=[{'path': [[4900, 2444], [4716, 2444], [4716, 3764]], 'height': 64, 'thickness': 24,
                'surface': BIGBLOCK, 'notes': "The gallery's parapet"},
               {'path': [[3928, 3320], [3656, 3592]], 'height': 16, 'thickness': 16, 'surface': DARKIRON,
                'notes': "The north span's iron edge (a kerb, no rail)"},
               {'path': [[2968, 2360], [2696, 2632]], 'height': 16, 'thickness': 16, 'surface': DARKIRON,
                'notes': "The south bridge's iron edge"},
               {'path': [[3088, 2480], [2816, 2752]], 'height': 16, 'thickness': 16, 'surface': DARKIRON,
                'notes': "The south bridge's iron edge"}],
     beams=[{'path': [[gong_x - 160, gong_y], [gong_x + 160, gong_y]], 'width': 24, 'depth': 24, 'bottom': -128 + 352,
             'surface': BEAM, 'notes': "Gong frame beam"}] +
           [{'path': [[x, 1536], [x, 3776]], 'width': 48, 'depth': 48, 'bottom': 160, 'surface': BEAM,
             'notes': "Soot-black roof timber"} for x in (3008, 3584)],
     notes="One hall round a ruined smelter, 2560 x 2240, cut by the slag channel at 45 degrees (a sunken level): the "
           "near bank south-east, the far bank a triangle north-west. The north span covers the channel's head, the "
           "south bridge crosses near its foot, the slag steps and the drain steps climb out. The gong gallery is a "
           "balcony 384 up along the east wall with its stair at its south end and the gong at its north end. Rough "
           "rock roof 832 to 1216 over the floor.")

room(id='room:back_stair_head', name='Back stair head', space='room:barracks',
     outline=rect(5184, 3040, 5440, 3232), floor=-128, ceiling=192, theme='theme:clan_hold', ambient=18,
     notes="The landing at the head of the back stair, off the gallery.")
room(id='room:back_stair', name='Back stair', space='room:barracks',
     outline=rect(5184, 3296, 5440, 3776), floor=-128, slope={'to': -512, 'toward': 'north', 'steps': 12},
     ceiling=256, ceiling_slope={'to': -128, 'toward': 'north'}, theme='theme:clan_hold', ambient=18, bands=[],
     notes="Twelve steps of 32 down north from the gallery to the barracks' south-east corner.")

room(id='room:barracks', name="Sergeants' barracks", outline=rect(3904, 3840, 5440, 4864), floor=-512, ceiling=-64,
     theme='theme:clan_hold', ambient=24,
     platforms=[
         {'at': [4160, 4736], 'size': [384, 160], 'rise': 40, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Bunk bench'},
         {'at': [5184, 4736], 'size': [384, 160], 'rise': 40, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Bunk bench'},
         {'at': [4128, 3968], 'size': [384, 160], 'rise': 40, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Bunk bench'},
         {'at': [4672, 4352], 'size': [576, 128], 'rise': 72, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Trestle table'},
         {'at': [4672, 4240], 'size': [512, 48], 'rise': 40, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Bench'},
         {'at': [4672, 4464], 'size': [512, 48], 'rise': 40, 'surface': PLANKS, 'top_surface': PLANKFLOOR,
          'notes': 'Bench'},
     ],
     beams=[{'path': [[x, 3840], [x, 4864]], 'width': 32, 'depth': 32, 'bottom': -96, 'surface': BEAM}
            for x in (4288, 4672, 5056)],
     notes="1536 x 1024, 448 high, under a plank ceiling on three beams: bunk benches along the walls, a trestle "
           "table, the lever alcove in the north wall; dark until the alarm.")
room(id='room:lever_alcove', name='Lever alcove', space='room:barracks', outline=rect(4544, 4928, 4800, 5120),
     floor=-512, ceiling=-128, theme='theme:clan_hold', ambient=24,
     notes="A niche behind the bunks: lever A on its back wall.")
room(id='room:armoury', name='Clan armoury',
     outline=[[5504, 4160], [6016, 4160], [6272, 4352], [6080, 4480], [6272, 4608], [6016, 4800], [5504, 4800]],
     floor=-480, ceiling=-96, theme='theme:clan_hold', ambient=20,
     platforms=[
         {'at': [6120, 4288], 'size': [192, 16], 'base': 96, 'rise': 16, 'facing': 37, 'surface': BEAM, 'notes': 'Weapon rack rail'},
         {'at': [6120, 4288], 'size': [192, 16], 'base': 176, 'rise': 16, 'facing': 37, 'surface': BEAM, 'notes': 'Weapon rack rail'},
         {'at': [6197, 4346], 'size': [20, 20], 'rise': 224, 'surface': POST, 'top_surface': POST, 'notes': 'Weapon rack post'},
         {'at': [6043, 4230], 'size': [20, 20], 'rise': 224, 'surface': POST, 'top_surface': POST, 'notes': 'Weapon rack post'},
         {'at': [6120, 4672], 'size': [192, 16], 'base': 96, 'rise': 16, 'facing': -37, 'surface': BEAM, 'notes': 'Weapon rack rail'},
         {'at': [6120, 4672], 'size': [192, 16], 'base': 176, 'rise': 16, 'facing': -37, 'surface': BEAM, 'notes': 'Weapon rack rail'},
         {'at': [6197, 4614], 'size': [20, 20], 'rise': 224, 'surface': POST, 'top_surface': POST, 'notes': 'Weapon rack post'},
         {'at': [6043, 4730], 'size': [20, 20], 'rise': 224, 'surface': POST, 'top_surface': POST, 'notes': 'Weapon rack post'},
     ],
     notes="A narrow room east of the barracks, one step up; its east wall folds into two angled bays where the weapon "
           "racks stand.")

# ---------------------------------------------------------------------------------------------------- the King
room(id='room:kings_antechamber', name='Antechamber', outline=[[2688, 3840], [3712, 3840], [3456, 4608], [2944, 4608]],
     floor=-512, ceiling=192, ceiling_levels=[{'ceiling': 448, 'top_scale': [0, 1]}], theme='theme:clan_hold',
     ambient=22,
     platforms=[
         {'at': [2960, 4560], 'size': [32, 48], 'rise': 480, 'surface': DARKIRON, 'notes': "Bar bracket"},
         {'at': [3440, 4560], 'size': [32, 48], 'rise': 480, 'surface': DARKIRON, 'notes': "Bar bracket"},
     ],
     notes="A wedge 1024 wide at the hall narrowing to 512 at the King's Gate under a pointed vault: the two hacked "
           "statues against its slanting walls, two flambeaux, the gate's two iron bars (movers).")

hall = [[2752, 4672], [3648, 4672], [4544, 5568], [4544, 6464], [1856, 6464], [1856, 5568]]
dome_c = (3200, 5728)
r1 = octo(*dome_c, 560, 232)
r2 = octo(*dome_c, 448, 186)
r3 = octo(*dome_c, 288, 119)
r4 = octo(*dome_c, 112, 46)
room(id='room:king_hall', name="The Clan King's hall", outline=hall, floor=-512, ceiling=448,
     theme='theme:king_hall', ambient=21,
     levels=[
         {'id': 'level:gutter_w', 'outline': rect(1888, 5632, 2080, 6432), 'floor': -544, 'edge': SLAGROCK,
          'surface': GREYROCK, 'notes': "West gutter, 32 deep: dry until the King's wrath."},
         {'id': 'level:gutter_e', 'outline': rect(4320, 5632, 4512, 6432), 'floor': -544, 'edge': SLAGROCK,
          'surface': GREYROCK, 'notes': "East gutter, 32 deep."},
         {'id': 'level:dais', 'outline': rect(2688, 6016, 3712, 6464), 'floor': -320, 'edge': DRESSED2,
          'surface': INLAY, 'notes': "The throne floor at the top of the dais, against the north wall."},
     ],
     platforms=[
         {'id': 'platform:gutter_w', 'outline': rect(1890, 5634, 2078, 6430), 'rise': 4, 'surface': GREYROCK,
          'top_surface': GREYROCK, 'notes': "The west gutter's bed (its surface turns to slag by event)."},
         {'id': 'platform:gutter_e', 'outline': rect(4322, 5634, 4510, 6430), 'rise': 4, 'surface': GREYROCK,
          'top_surface': GREYROCK, 'notes': "The east gutter's bed."},
         {'at': [3200, 6208], 'size': [448, 224], 'base': 192, 'rise': 32, 'surface': BIGBLOCK, 'top_surface': BIGBLOCK,
          'notes': "The throne's plinth"},
         {'id': 'platform:throne', 'at': [3200, 6200], 'size': [112, 64], 'top_size': [208, 112], 'base': 224,
          'rise': 72, 'surface': DARKIRON, 'top_surface': DARKIRON, 'notes': "The anvil throne's seat: an anvil."},
         {'at': [3200, 6304], 'size': [256, 32], 'base': 224, 'rise': 176, 'surface': BIGBLOCK,
          'top_surface': BIGBLOCK, 'notes': "The throne's back."},
         {'at': [3200, 6304], 'size': [224, 40], 'base': 400, 'rise': 192, 'surface': SKULL, 'end_surface': BIGBLOCK,
          'top_surface': BIGBLOCK, 'notes': "The throne's crest: a skull carved in the stone."},
         {'at': [2944, 6200], 'size': [96, 96], 'base': 192, 'rise': 48, 'surface': BIGBLOCK, 'notes': "Forge brazier stand"},
         {'at': [3456, 6200], 'size': [96, 96], 'base': 192, 'rise': 48, 'surface': BIGBLOCK, 'notes': "Forge brazier stand"},
     ],
     pillars=[{'at': p, 'size': [224, 224], 'surface': DRESSED2}
              for p in ([2464, 5408], [3936, 5408], [2464, 6048], [3936, 6048])],
     flights=[{'from': [3200, 5712], 'to': [3200, 6016], 'width': 1024, 'steps': 6, 'riser': BIGBLOCK, 'tread': INLAY,
               'notes': "The stepped dais: six steps of 32 up to the throne floor."}],
     ceiling_levels=[
         {'outline': r1, 'ceiling': 704, 'top_outline': r2, 'edge': CRYSTAL},
         {'outline': r2, 'ceiling': 928, 'top_outline': r3, 'edge': CRYSTAL},
         {'outline': r3, 'ceiling': 1088, 'top_outline': r4, 'edge': CRYSTAL},
         {'outline': r4, 'ceiling': 1152, 'top_scale': 0, 'edge': GEMWALL},
     ],
     notes="The signature room: a six-sided hall 2688 wide and 1792 deep narrowing south to the King's Gate like a "
           "coffin, 960 high, under a dome of geode crystal (four rings rising to 1664 over the floor). Four squat "
           "pillars in a ring round the dome; two slag gutters along the east and west walls; the throne floor "
           "(-320) along the north wall up six steps 1024 wide; the anvil throne on its plinth, the forge braziers "
           "either side, the hoard door behind it.")
room(id='room:king_hoard', name="The King's hoard",
     outline=[[2944, 6528], [3456, 6528], [3584, 6912], [3584, 7296], [2816, 7296], [2816, 6912]],
     floor=-320, ceiling=128, theme='theme:hoard', ambient=18,
     notes="A vault behind the throne, widening from 512 at its door to 768 at the back, 768 deep and 448 high.")
room(id='room:escape_shaft', name='Escape shaft', outline=rect(3648, 6912, 4416, 7424), floor=-320, ceiling=1536,
     theme='theme:deep_rock', ambient=20,
     levels=[{'id': 'level:shaft_head', 'outline': rect(4160, 6912, 4416, 7424), 'floor': 1216, 'edge': DEEP,
              'surface': PLANKFLOOR, 'notes': "The shaft head's landing, 1536 up: the way out to the X1 hills."}],
     notes="A shaft 512 square going straight up 1856: the counterweight cage runs in it; at its top the shaft "
           "head's landing (a level 1536 up) with the exit to the X1 hills.")

# ---------------------------------------------------------------------------------------------------- the tower
tower = [[1472, 2944], [1856, 2944], [2048, 3136], [2048, 3520], [1856, 3712], [1472, 3712], [1280, 3520], [1280, 3136]]
tower_top = [[1592, 3184], [1736, 3184], [1808, 3256], [1808, 3400], [1736, 3472], [1592, 3472], [1520, 3400],
             [1520, 3256]]
room(id='room:furnace_tower', name='Furnace tower', outline=tower, floor=-256, ceiling=256,
     ceiling_levels=[{'ceiling': 512, 'top_outline': tower_top}, {'outline': tower_top, 'ceiling': 896}],
     theme='theme:tower', ambient=20,
     platforms=[{'outline': octo(1664, 3328, 160, 66), 'rise': 24, 'surface': BIGBLOCK, 'top_surface': S('vlcflorc', 128, 128),
                 'notes': "The old crucible's hearth, still cracked with heat"}],
     notes="The smelter's old stack: an octagon 768 across, 512 high, its roof drawing in to the sooty flue.")
room(id='room:tower_stair', name='Tower stair', space='room:furnace_tower', outline=rect(2112, 3200, 2496, 3456),
     floor=-512, slope={'to': -256, 'toward': 'west', 'steps': 8}, ceiling=-128,
     ceiling_slope={'to': 128, 'toward': 'west'}, theme='theme:tower', ambient=16,
     notes="Eight steps of 32 up west from the far bank to the tower door.")

# ---------------------------------------------------------------------------------------------------- the caves
room(id='room:geode_breach', name='Breach', space='room:geode_grotto',
     outline=[[1920, 1472], [2496, 1472], [2496, 1984], [2176, 1984], [1920, 1792]], floor=-512, ceiling=0,
     theme='theme:deep_rock', ambient=20, rough={'step': 160, 'depth': 40},
     notes="The rough hole where the smelter's workers broke into the natural cave.")
room(id='room:geode_descent', name='Geode descent', space='room:geode_grotto', outline=rect(1408, 1536, 1856, 1760),
     floor=-512, slope={'to': -640, 'toward': 'west'}, ceiling=-64, ceiling_slope={'to': -192, 'toward': 'west'},
     theme='theme:deep_rock', ambient=20, notes="A rough ramp falling 128 west into the geode.")
geode = [[1088, 1024], [1344, 1280], [1344, 1920], [1152, 2304], [768, 2496], [384, 2368], [128, 1984], [128, 1472],
         [320, 1152], [448, 1024]]
room(id='room:geode_grotto', name='Geode grotto', outline=geode, floor=-640, ceiling=-128,
     ceiling_points=[[768, 1760, 320], [576, 1408, 192], [1024, 1984, 192], [960, 1344, 128], [448, 2048, 128]],
     theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 48},
          pillars=[
         {'outline': [[832, 1728], [880, 1792], [848, 1872], [768, 1888], [704, 1824], [720, 1744]],
          'surface': CRACKED, 'notes': 'Crystal column'},
         {'outline': [[560, 1360], [608, 1408], [592, 1472], [528, 1488], [480, 1440], [496, 1376]],
          'surface': CRACKED, 'notes': 'Crystal column'},
     ],
     notes="The upper terrace: the hollow of the geode, its crown 960 over the floor, two crystal columns, webs "
           "between the crystals, the bat queens in its crown.")
room(id='room:geode_flight', name='Geode terrace steps', space='room:geode_grotto', outline=rect(512, 768, 896, 960),
     floor=-640, slope={'to': -768, 'toward': 'south', 'steps': 4}, ceiling=128, theme='theme:geode', ambient=22,
     notes="Four steps of 32 down to the lower terrace.")
room(id='room:geode_lower', name='Geode lower terrace', space='room:geode_grotto',
     outline=[[256, 64], [1216, 64], [1344, 448], [1088, 704], [320, 704], [128, 576], [128, 192]],
     floor=-768, ceiling=-256, ceiling_points=[[704, 384, -64], [384, 320, -128], [1024, 320, -128]],
     theme='theme:geode', ambient=24, rough={'step': 160, 'depth': 40},
     notes="The lower terrace; its west wall is the singing crystal wall in front of the Red Dwarf vault.")
vault = [[-512, 0], [-128, 0], [64, 192], [64, 576], [-128, 768], [-512, 768], [-704, 576], [-704, 192]]
room(id='room:red_dwarf_vault', name='Red Dwarf vault', outline=vault, floor=-768, ceiling=-256,
     ceiling_levels=[{'ceiling': -64, 'top_scale': 0.5}], theme='theme:dwarf_vault', ambient=24,
     platforms=[
         {'id': 'platform:rune_ring', 'outline': octo(-320, 384, 192, 80), 'rise': 2, 'surface': RUNEGLOW,
          'top_surface': RUNEGLOW, 'notes': "The ring of runes in the floor (glowing)."},
         {'id': 'platform:lectern', 'at': [-320, 672], 'size': [96, 48], 'top_size': [128, 72], 'rise': 112,
          'surface': OLDBLOCK, 'top_surface': RUNES, 'notes': "The stone lectern with the mine's history (clicked)."},
     ],
     notes="The Red Dwarves' first vault, older than anything else here: an octagon of olive-grey blocks under a low "
           "dome, a ring of runes in the floor, the lectern, the chest.")
room(id='room:warren_mouth', name='Burrow mouth', space='room:mole_warren', outline=rect(3840, 960, 4096, 1472),
     floor=-512, slope={'to': -768, 'toward': 'south'}, ceiling=-128, ceiling_slope={'to': -384, 'toward': 'south'},
     theme='theme:warren', ambient=24, notes="A burrow mouth in the hall's south wall, falling 256 over 512.")
room(id='room:mole_warren', name='Mole warren',
     outline=[[3200, 256], [3584, 0], [4352, 0], [4864, 256], [4992, 640], [4608, 896], [4224, 896], [3712, 896],
              [3328, 768]],
     floor=-768, ceiling=-352,
     floor_points=[[3584, 0, -800], [4864, 256, -784], [3400, 500, -736], [4600, 500, -800]],
     ceiling_points=[[3968, 160, -384], [4352, 704, -384], [3500, 640, -416], [4800, 450, -400], [4096, 448, -320]],
     theme='theme:warren', ambient=26, rough={'step': 128, 'depth': 40},
     pillars=[
         {'outline': [[3712, 352], [3904, 320], [3968, 448], [3872, 576], [3712, 544], [3648, 448]],
          'surface': EARTHROCK, 'notes': 'Rock core'},
         {'outline': [[4352, 352], [4544, 384], [4576, 512], [4448, 576], [4320, 528], [4288, 432]],
          'surface': EARTHROCK, 'notes': 'Rock core'},
     ],
     notes="A knot of burrows round two rock cores, low and uneven; the dead prospector in the east burrow.")

# ---------------------------------------------------------------------------------------------------- openings
opening(id='open:head_ledge', **{'from': 'room:deep_line'}, to='room:deep_landing', width=224, height=256)
opening(id='open:landing_cut', **{'from': 'room:deep_landing'}, to='room:sentry_cut', link='link:landing_sentry_cut',
        width=224, height=320)
opening(id='open:cut_lookout', **{'from': 'room:sentry_cut'}, to='room:sentry_lookout', width=192, height=288)
opening(id='open:sentry_door', **{'from': 'room:sentry_cut'}, to='room:furnace_hall', link='link:sentry_cut_gong',
        width=192, height=288)
opening(id='open:stairhead', **{'from': 'room:furnace_hall'}, to='room:back_stair_head', width=160, height=288)
opening(id='open:stairhead_stair', **{'from': 'room:back_stair_head'}, to='room:back_stair', width=224, height=288)
opening(id='open:back_stair_foot', **{'from': 'room:back_stair'}, to='room:barracks',
        link='link:barracks_gong_back_stair', from_wall='north', to_wall='south', width=224, height=320)
opening(id='open:barracks_doors_e', **{'from': 'room:furnace_hall'}, to='room:barracks', link='link:furnace_barracks',
        from_wall='north', to_wall='south', along=0.58, width=144, height=320)
opening(id='open:barracks_doors_w', **{'from': 'room:furnace_hall'}, to='room:barracks',
        from_wall='north', to_wall='south', along=0.72, width=144, height=320)
opening(id='open:barracks_alcove', **{'from': 'room:barracks'}, to='room:lever_alcove', width=192, height=288)
opening(id='open:armoury_door', **{'from': 'room:barracks'}, to='room:armoury', link='link:barracks_armoury',
        width=128, height=256)
opening(id='open:far_antechamber', **{'from': 'room:furnace_hall'}, to='room:kings_antechamber',
        link='link:furnace_antechamber', width=768, height=448)
opening(id='open:gate_e', **{'from': 'room:kings_antechamber'}, to='room:king_hall', link='link:antechamber_king_hall',
        along=0.2656, width=208, height=384)
opening(id='open:gate_w', **{'from': 'room:kings_antechamber'}, to='room:king_hall', along=0.7344, width=208,
        height=384)
opening(id='open:hall_hoard', **{'from': 'room:king_hall'}, to='room:king_hoard', link='link:king_hall_hoard',
        width=128, height=256)
opening(id='open:hoard_shaft', **{'from': 'room:king_hoard'}, to='room:escape_shaft', link='link:hoard_escape_shaft',
        width=256, height=384)
opening(id='open:tower_stair_foot', **{'from': 'room:furnace_hall'}, to='room:tower_stair',
        link='link:furnace_tower_bridge', width=224, height=320)
opening(id='open:tower_door', **{'from': 'room:tower_stair'}, to='room:furnace_tower', width=224, height=320)
opening(id='open:hall_breach', **{'from': 'room:furnace_hall'}, to='room:geode_breach', link='link:furnace_geode',
        width=256, height=384)
opening(id='open:breach_descent', **{'from': 'room:geode_breach'}, to='room:geode_descent', width=192, height=384)
opening(id='open:descent_geode', **{'from': 'room:geode_descent'}, to='room:geode_grotto', width=192, height=384)
opening(id='open:geode_flight', **{'from': 'room:geode_grotto'}, to='room:geode_flight', width=352, height=448)
opening(id='open:flight_lower', **{'from': 'room:geode_flight'}, to='room:geode_lower', width=352, height=448)
opening(id='open:crystal_wall', **{'from': 'room:geode_lower'}, to='room:red_dwarf_vault', link='link:geode_vault',
        width=192, height=320)
opening(id='open:hall_warren', **{'from': 'room:furnace_hall'}, to='room:warren_mouth',
        link='link:furnace_mole_warren', width=224, height=320)
opening(id='open:warren_mouth', **{'from': 'room:warren_mouth'}, to='room:mole_warren', width=224, height=320)

doc = {'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:deep_rock', 'ambient': 18}, 'rooms': rooms,
       'openings': openings,
       'notes': "L4 of the Deep Mine (XD-03): L3's plan redrawn with the studio's words of 2026-11-13 (one furnace hall "
                "with the slag channel as a sunken level, bridges as hanging slabs, the gong gallery as a balcony, the "
                "King's hall with a crystal dome, gutters, a dais and the anvil throne in it; the Deep Line's last pitch "
                "as a trestle the cart rides down). Whole map units, x east and y north, heights against the arrival "
                "datum (the landing's floor 0). First written by output/studio_cal/xd03/tools/gen_rooms.py; see "
                "NOTES.md."}

with open(L4 + '/rooms.yml', 'w') as f:
    yaml.safe_dump(doc, f, sort_keys=False, width=120, default_flow_style=None)
