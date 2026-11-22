"""DD-02 Ellinger's Tower: writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd02/L*) from one place.

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd02), phase 3, decider D-26.
Plan frame: x east, y north; floors 480 apart (ground 0, the gauntlet 480, the library 960, the tapestry floor 1440,
Ellinger's study 1920). Every room's ceiling stays 64 under the floor of any room above it in plan. The main stair is
a switchback column (lanes L x 768-1056 and R x 1120-1408; flights y 896-2176; landings south y 448-832 and north
y 2240-2624): flight 1 (L, 0-480, north), flight 2 (R, 480-960, south), flight 3 (L, 960-1440, north) and flight 4
(R, 1440-1920, north, reached only from the trapped walk's west end). The back stair is a second switchback at x
3968-4608. The lift shaft (x -1024 to -512, y 1344-1856) is one closed room from 0 to 2400 with openings only at the
ground floor (the entry hall) and at the top (the lift head beside the study).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
OUT = R + '/devdocs/xeen/briefs/dd02'


class Flow(list):
    pass


def flow_rep(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


yaml.add_representer(Flow, flow_rep)


def F(*a):
    return Flow(a)


def S(texture, w, h, scale=None, **kw):
    d = {'texture': texture, 'size': F(w, h)}
    if scale:
        d['scale'] = scale
    d.update(kw)
    return d


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers

MAP_ID = 9151
QBITS = {
    'arrived_once': 117080,          # the map's own (provisional block 117080-117119)
    'question_passed': 111340,       # M17 (A3)
    'password': 111341,
    'm17_done': 111342,
    'm18_started': 111360,
    'm26_stage4': 111522,
}
BIT_SORCERER = 11312
BIT_FIRE = 11313
BIT_ELEC = 11314
ELLINGER_NPC = 4954
ELLINGER_BODY = 11901    # A2's Xeen Ellinger (session 7; faction xeen_character_ellinger, friendly to the party)

FLOOR = [0, 480, 960, 1440, 1920]

# D1's tower door (thing:ellinger_tower, event 102 of the installed xeen_d1.odm): its face at (3285, 9321, 1280), used
# from (3029, 9321, 1152), the door facing west. Leaving DD-02 the party stands at A6's return point for this door
# (the lane lead, 2026-11-20): (2560, 9216, 1152), facing east (0), toward the tower (measured with playtest_exit.yml).
D1_ARRIVAL = [2560, 9216, 1152]
D1_FACING = 0

# ---------------------------------------------------------------------------------------------------------------------
# Textures (D-26 / the graph): MM6 Agar's Laboratory 6d19 (dungeon_families towers): rose and white marble brick
# t1wl0lg, its column walls t1wl9ctl, t1wl4cts, t1wl7ctb, floors t1f1-t1f3, ceiling t1c3, trim t1trima, door t1d3,
# pillar t1spcla; MM7 Castle Harmondale 7d29 tapestries tap1, tap4, tap7.

MARBLE = S('t1wl0lg', 256, 256)
COLWALL = S('t1wl9ctl', 256, 256)
NARROW = S('t1wl4cts', 128, 256)
DARKWALL = S('t1wl7ctb', 256, 256)
TRIM = S('t1trima', 32, 32)
FLOOR1 = S('t1f1', 128, 128)
FLOOR2 = S('t1f2', 128, 128)
FLOOR3 = S('t1f3', 128, 128)
CEIL = S('t1c3', 64, 64, 2)
DOOR = S('t1d3', 128, 256, 1.25)
PILLAR = S('t1spcla', 128, 256)
BOOKS = S('bookcas1', 256, 256)
BOOKS2 = S('bookcas2', 256, 256)
DESK_SIDE = S('deskside', 64, 64)
DESK_TOP = S('desktop', 128, 64)
MIRROR = S('xkmirror', 128, 128)   # A6's silvered glass (D-37 (2)), a seamless tile


def desk_side(rise):
    # Session 7 (texture fit): deskside is a band (wood under a brass edge, 64 high): stretched to the platform's rise
    # so the edge shows once, at the top (a platform side takes `scale`, not `fit`).
    return S('deskside', 64, 64, rise / 64.0) if rise != 64 else DESK_SIDE


def desk_top(w, h, x0, y0):
    # Session 7: the desk-top picture (a lion, a note, an inkwell) laid once over a top cut to its 2:1 shape; the
    # picture starts at the world grid, so the offset brings its corner to the top's (x0, y0: the top's south-west).
    k = w / 128.0
    return S('desktop', 128, 64, k, offset=F(*desk_offset(x0, y0, k)))


def desk_offset(x0, y0, k):
    # Texels (u = x / k, v = -y / k on a top): shift the picture's corner from the world grid to the top's corner.
    return (int(round(-x0 / k % 128)) % 128, int(round(y0 / k % 64)) % 64)


TAP = {'tap1': S('tap1', 128, 256, 1.5), 'tap4': S('tap4', 128, 256, 1.5), 'tap7': S('tap7', 128, 256, 1.5)}
CIRCLE = S('td1', 512, 512, 0.75)

THEMES = [
    {'id': 'theme:tower', 'wall': MARBLE, 'bands': [{'height': 32, 'surface': TRIM}], 'floor': FLOOR1,
     'ceiling': CEIL, 'reveal': NARROW, 'door': DOOR,
     'notes': "Ellinger's tower: MM6 Agar's Laboratory (6d19) rose and white marble brick t1wl0lg over a trim t1trima, "
              "its floor t1f1, the dark marble ceiling t1c3, the door t1d3."},
    {'id': 'theme:stair', 'wall': NARROW, 'floor': FLOOR3, 'ceiling': CEIL, 'reveal': NARROW, 'door': DOOR,
     'notes': "The stairs and the lift shaft: 6d19's narrow column wall t1wl4cts, floor t1f3."},
    # Session 7 (texture fit): t1wl9ctl is one storey's band (columns under a Greek-key frieze, 256): laid once over
    # the trim (32-288), the plain column-wall blocks t1wl4cts above it to the ceiling; never 1.5 times up a wall.
    {'id': 'theme:hall', 'wall': NARROW,
     'bands': [{'height': 32, 'surface': TRIM}, {'height': 288, 'surface': COLWALL}], 'floor': FLOOR2, 'ceiling': CEIL, 'reveal': NARROW, 'door': DOOR,
     'notes': "The great rooms (wards, library, study): 6d19's column wall t1wl9ctl once over the trim, the plain "
              "t1wl4cts above it, its floor t1f2."},
    {'id': 'theme:dark', 'wall': DARKWALL, 'bands': [{'height': 32, 'surface': TRIM}], 'floor': FLOOR3,
     'ceiling': CEIL, 'reveal': NARROW, 'door': DOOR,
     'notes': "The bat floors (roost, loft, trapped walk) and the back stair: 6d19's darker wall t1wl7ctb."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


LANE_L = (768, 1056)
LANE_R = (1120, 1408)
FLIGHT_Y = (896, 2176)
LAND_S = (448, 832)
LAND_N = (2240, 2624)


def flight(i, name, lane, f0, f1, toward, ceiling, notes):
    return {'id': 'room:' + i, 'name': name, 'outline': rect(lane[0], FLIGHT_Y[0], lane[1], FLIGHT_Y[1]),
            'floor': f0, 'slope': {'to': f1, 'toward': toward, 'steps': 15}, 'ceiling': ceiling,
            'theme': 'theme:stair', 'ambient': 16, 'notes': notes}


def landing(i, name, y, floor, notes, x=(768, 1408), theme='theme:stair', ceiling=None):
    return {'id': 'room:' + i, 'name': name, 'outline': rect(x[0], y[0], x[1], y[1]), 'floor': floor,
            'ceiling': ceiling or floor + 416, 'theme': theme, 'ambient': 18, 'notes': notes}


def panel(i, wall, at, surface, length=192, bottom=48, height=384, notes=None):
    d = {'id': 'panel:' + i, 'length': length, 'bottom': bottom, 'height': height, 'surface': surface}
    if at == 'centre':
        d['at'] = 'centre'
    else:
        d['offset'] = at
    if notes:
        d['notes'] = notes
    return d


def plat(i, at, size, rise, surface, top=None, **kw):
    d = {'id': 'platform:' + i, 'at': F(*at), 'size': F(*size), 'rise': rise, 'surface': surface,
         'top_surface': top or surface}
    d.update(kw)
    return d


ROOMS = [
    # ---- ground floor (0)
    {'id': 'room:entry', 'name': 'Entry hall', 'outline': rect(-1408, 0, 512, 1280), 'floor': 0, 'ceiling': 640,
     'theme': 'theme:tower', 'ambient': 22,
     # Session 7 (D-37 (2)): the dead mirror is A6's silvered glass xkmirror, framed in the ceiling's dark marble t1c3
     # (pale glass in rose brick: the hall's bright light washes the pale trim marble into the glass).
     'walls': [{'wall': 'north', 'panels': [
         panel('mirror', 'north', 256, MIRROR, length=192, bottom=96, height=288,
               notes="The dead mirror, silvered glass in a marble frame."),
         panel('mirror_frame_w', 'north', 224, CEIL, length=32, bottom=64, height=352, notes="The mirror's frame."),
         panel('mirror_frame_e', 'north', 448, CEIL, length=32, bottom=64, height=352),
         panel('mirror_frame_s', 'north', 256, CEIL, length=192, bottom=64, height=32),
         panel('mirror_frame_n', 'north', 256, CEIL, length=192, bottom=384, height=32)]}],
     'pillars': [{'at': F(x, 1152), 'size': F(96, 96), 'surface': PILLAR} for x in (-1280, 384)],
     'notes': "Inside the door from Castleview: a marble hall 1,920 by 1,280, the dead mirror on the north wall, the "
              "lift's cage north, the storeroom's door south, the Hall of the Question east."},
    {'id': 'room:question', 'name': 'Hall of the Question', 'outline': rect(640, 128, 1792, 832), 'floor': 0,
     'ceiling': 544, 'theme': 'theme:hall', 'ambient': 22,
     'walls': [{'wall': 'north', 'panels': [panel('mouth', 'north', 816, S('t1spclb', 128, 256), length=128,
                                                  bottom=368, height=128,
                                                  notes="A carved face over the stair door: the door's mouth.")]}],
     'notes': "A square hall before the stair door, which asks its question."},
    {'id': 'room:store', 'name': 'Storeroom', 'outline': rect(-1152, -768, 256, -128), 'floor': 0, 'ceiling': 448,
     'theme': 'theme:tower', 'ambient': 16,
     'notes': "Cabinets and a chest; bats got in through the vent."},
    {'id': 'room:lift_foot', 'name': 'Lift foot (the shaft)', 'outline': rect(-1024, 1344, -512, 1856), 'floor': 0,
     'ceiling': 2400, 'theme': 'theme:stair', 'ambient': 16,
     'notes': "A closed shaft 512 square from the ground floor to above the study: the cage's two stops, no opening "
              "on the floors between (D-9.2, D-26)."},
    flight('stair1f', 'Main stair (ground to gauntlet)', LANE_L, 0, 480, 'north', 896,
           "Fifteen marble steps up north from the question's door to the gauntlet floor."),
    # ---- the gauntlet (480)
    landing('stair1', 'Stair (gauntlet floor)', LAND_N, 480, "The main stair's north landing on the gauntlet floor."),
    {'id': 'room:wards', 'name': 'Hall of Wards', 'outline': rect(1536, 1280, 2816, 2816), 'floor': 480,
     'ceiling': 896, 'theme': 'theme:hall', 'ambient': 20,
     'platforms': [plat('ward_1', (1920, 1792), (384, 384), 2, CIRCLE, notes="A warded circle in the floor."),
                   plat('ward_2', (2432, 2304), (384, 384), 2, CIRCLE, notes="A warded circle in the floor.")],
     'notes': "Ellinger's defences: warded circles in the floor and the constructs that keep spies out."},
    {'id': 'room:roost', 'name': 'Bat roost', 'outline': rect(2944, 1920, 3840, 2816), 'floor': 480, 'ceiling': 896,
     'theme': 'theme:dark', 'ambient': 12,
     'walls': [{'wall': 'east', 'panels': [panel('window', 'east', 'centre', S('t1wl1ctl', 256, 256), length=192,
                                                 bottom=160, height=192, notes="A broken window, boarded with "
                                                                                 "nothing.")]}],
     'notes': "A cold room with a broken window: the bats' way in."},
    {'id': 'room:tapestry1', 'name': 'Tapestry gallery', 'outline': rect(2944, 512, 3840, 1792), 'floor': 480,
     'ceiling': 896, 'theme': 'theme:tower', 'ambient': 18,
     'walls': [{'wall': 'west', 'panels': [panel('tap1_a', 'west', 160, TAP['tap1']),
                                           panel('tap1_b', 'west', 880, TAP['tap4'])]},
               {'wall': 'east', 'panels': [panel('tap1_c', 'east', 384, TAP['tap7'])]}],
     'notes': "Tapestries of boots through the ages; a button behind one opens the back stair."},
    landing('back1', 'Back stair (foot)', LAND_S, 480, "The servants' stair's foot, behind the tapestry gallery.",
            x=(3968, 4256), theme='theme:dark'),
    flight('backf1', 'Back stair (first flight)', (3968, 4256), 480, 960, 'north', 1376,
           "The servants' stair, up north from the gauntlet floor to the library floor."),
    # ---- the library (960)
    flight('stair2f', 'Main stair (gauntlet to library)', LANE_R, 480, 960, 'south', 1376,
           "Fifteen steps up south to the library floor."),
    landing('stair2', 'Stair (library floor)', LAND_S, 960, "The main stair's south landing on the library floor."),
    {'id': 'room:library', 'name': 'The library', 'outline': rect(1536, 128, 2816, 2176), 'floor': 960,
     'ceiling': 1376, 'theme': 'theme:hall', 'ambient': 20,
     'platforms': [
         plat('shelf_w1', (1600, 1152), (64, 448), 288, BOOKS, CEIL, notes="A bookcase along the west wall."),
         plat('shelf_e1', (2752, 384), (64, 384), 288, BOOKS2, CEIL, notes="A bookcase along the east wall."),
         plat('shelf_n', (1856, 2112), (384, 64), 288, BOOKS, CEIL, notes="Bookcases either side of the reading "
                                                                           "room's door."),
         plat('shelf_n2', (2560, 2112), (320, 64), 288, BOOKS2, CEIL),
         plat('stack_1', (2048, 768), (448, 64), 224, BOOKS, CEIL, notes="A free-standing stack."),
         plat('stack_2', (2048, 1536), (448, 64), 224, BOOKS2, CEIL, notes="A free-standing stack."),
         plat('lectern_fire', (1728, 640), (64, 48), 80, desk_side(80),
              S('desktop', 128, 64, offset=F(*desk_offset(1696, 616, 1))),
              notes="The Book of Fire's lectern."),
         plat('lectern_elec', (1728, 1792), (64, 48), 80, desk_side(80),
              S('desktop', 128, 64, offset=F(*desk_offset(1696, 1768, 1))),
              notes="The Book of Electricity's lectern."),
         plat('lectern_sorc', (2560, 1152), (64, 48), 80, desk_side(80),
              S('desktop', 128, 64, offset=F(*desk_offset(2528, 1128, 1))),
              notes="The Book of Sorcerer's Knowledge's lectern."),
     ],
     'notes': "Shelves round a reading floor, free-standing stacks, three lecterns; gargoyle bookends wake."},
    {'id': 'room:reading', 'name': 'Reading room', 'outline': rect(1536, 2304, 2816, 3072), 'floor': 960,
     'ceiling': 1376, 'theme': 'theme:hall', 'ambient': 20,
     'platforms': [plat('reading_table', (2176, 2688), (256, 128), 72, desk_side(72),
                        desk_top(256, 128, 2048, 2624),
                        notes="A long reading table.")],
     'notes': "Armchairs, a long table and a locked reading chest."},
    {'id': 'room:gallery2', 'name': 'Gargoyle gallery', 'outline': rect(2944, 640, 3840, 2624), 'floor': 960,
     'ceiling': 1376, 'theme': 'theme:tower', 'ambient': 18,
     'pillars': [{'at': F(3584, y), 'size': F(96, 96), 'surface': PILLAR} for y in (1024, 1536, 2048)],
     'notes': "A long gallery along the outer wall, columns making bays where the gargoyles stand."},
    landing('back2', 'Back stair', LAND_N, 960, "The servants' stair's landing on the library floor.",
            x=(3968, 4608), theme='theme:dark'),
    flight('backf2', 'Back stair (second flight)', (4320, 4608), 960, 1440, 'south', 1856,
           "The servants' stair, up south from the library floor to the tapestry floor."),
    # ---- the tapestry floor (1440)
    flight('stair3f', 'Main stair (library to tapestry floor)', LANE_L, 960, 1440, 'north', 1856,
           "Fifteen steps up north to the tapestry floor."),
    landing('stair3', 'Stair (tapestry floor)', LAND_N, 1440, "The main stair's head: north landing of the tapestry "
                                                              "floor."),
    {'id': 'room:tapestries', 'name': 'Tapestry maze',
     'outline': [F(1536, 512), F(3840, 512), F(3840, 896), F(2816, 896), F(2816, 3328), F(1536, 3328)],
     'floor': 1440, 'ceiling': 1952, 'theme': 'theme:tower', 'ambient': 16,
     'platforms': [
         plat('hang_1', (1888, 2304), (640, 32), 384, TAP['tap4'], CEIL, notes="A hanging tapestry on a frame."),
         plat('hang_2', (2464, 1792), (640, 32), 384, TAP['tap1'], CEIL, notes="A hanging tapestry on a frame."),
         plat('hang_3', (1888, 1280), (640, 32), 384, TAP['tap7'], CEIL, notes="A hanging tapestry on a frame."),
     ],
     'walls': [{'wall': 0, 'panels': [panel('tap3_a', 0, 1984, TAP['tap1'])]},
               {'wall': 'west', 'panels': [panel('tap3_b', 'west', 1600, TAP['tap4'])]},
               {'wall': 'north', 'panels': [panel('tap3_c', 'north', 'centre', TAP['tap7'])]}],
     'notes': "A hall divided by tapestries hung on frames, and an arm running east along the south wall; behind "
              "three wall tapestries a button: one opens the back stair, two do nothing."},
    {'id': 'room:loft', 'name': 'Beholder loft', 'outline': rect(2944, 1920, 3840, 3072), 'floor': 1440,
     'ceiling': 2112, 'theme': 'theme:dark', 'ambient': 12,
     'beams': [{'path': [F(2944, y), F(3840, y)], 'width': 48, 'bottom': 1888, 'depth': 48, 'surface': DESK_SIDE}
               for y in (2176, 2432, 2688)],
     'notes': "Under the roof timbers: the red-eyed bats roost."},
    {'id': 'room:trap_walk', 'name': 'Trapped walk',
     'outline': [F(1472, 64), F(5152, 64), F(5152, 2560), F(3904, 2560), F(3904, 2240), F(4832, 2240), F(4832, 384),
                 F(1472, 384)],
     'floor': 1440, 'ceiling': 1856, 'theme': 'theme:dark', 'ambient': 12,
     'notes': "The gauntlet's last stretch: a walk 320 wide round the tower's outer wall from the loft to the last "
              "stair, its floor plates firing bolts."},
    landing('back3', 'Back stair (top)', LAND_S, 1440, "The servants' stair's head on the tapestry floor.",
            x=(3968, 4608), theme='theme:dark'),
    {'id': 'room:crates', 'name': 'Crate room', 'outline': rect(2944, 960, 4256, 1792), 'floor': 1440,
     'ceiling': 1856, 'theme': 'theme:dark', 'ambient': 14, 'store': True,
     'notes': "A storeroom of barrels and sacks off the back stair; a chest."},
    landing('stair4', 'Last stair (foot)', (128, 832), 1440, "The trapped walk's west end and the foot of the last "
                                                            "flight.", x=LANE_R, theme='theme:dark'),
    # ---- Ellinger's study (1920)
    flight('stair4f', 'Last stair', LANE_R, 1440, 1920, 'north', 2336,
           "Fifteen steps up north from the trapped walk to the top landing."),
    landing('landing4', 'Top landing', LAND_N, 1920, "The last stair's head; the last door west."),
    {'id': 'room:pass_door', 'name': 'The last door', 'outline': rect(128, 2240, 640, 2624), 'floor': 1920,
     'ceiling': 2336, 'theme': 'theme:hall', 'ambient': 22,
     'walls': [{'wall': 'west', 'panels': [panel('mouth4', 'west', 96, S('t1spclb', 128, 256), length=128,
                                                 bottom=320, height=96,
                                                 notes="A mouth carved over the last door.")]}],
     'notes': "A short passage before the study's door, which asks whom the party seeks."},
    {'id': 'room:study', 'name': "Ellinger's study", 'outline': rect(-1664, 2304, 0, 3712), 'floor': 1920,
     'ceiling': 2624, 'ceiling_points': [F(-832, 3008, 2880)], 'theme': 'theme:hall', 'ambient': 24,
     'platforms': [
         plat('desk', (-704, 3264), (256, 128), 80, desk_side(80), desk_top(256, 128, -832, 3200),
              notes="Ellinger's desk: the Book o' Boots."),
         plat('list', (-1088, 3264), (128, 64), 80, desk_side(80), desk_top(128, 64, -1152, 3232),
              notes="A side table: his list of disk sources."),
         plat('shelf_s', (-1600, 2944), (64, 448), 288, BOOKS, CEIL, notes="Bookshelves along the west wall."),
         plat('charts', (-1344, 2560), (192, 96), 80, desk_side(80), desk_top(192, 96, -1440, 2512),
              notes="A table of star charts."),
         plat('boot_rack', (-64, 3392), (64, 384), 96, desk_side(96), CEIL, notes="A rack of boots."),
     ],
     'notes': "Ellinger among star charts and boots: his desk, a list on a side table, shelves; the lift head south, "
              "the boot closet north."},
    {'id': 'room:lift_top', 'name': 'Lift head', 'outline': rect(-1088, 1920, -448, 2240), 'floor': 1920,
     'ceiling': 2336, 'theme': 'theme:stair', 'ambient': 20,
     'notes': "The lift's upper stop behind the study."},
    {'id': 'room:boots', 'name': 'Boot closet', 'outline': rect(-1664, 3840, -640, 4352), 'floor': 1920,
     'ceiling': 2304, 'theme': 'theme:tower', 'ambient': 18,
     'platforms': [plat('boots_rack', (-1600, 4096), (64, 384), 160, desk_side(160), CEIL,
                        notes="Racks of boots.")],
     'notes': "Racks of boots and the chest with a pair Ellinger outgrew."},
]


def op(i, a, b, link, width, height, **kw):
    d = {'id': 'open:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'link': 'link:' + link, 'width': width,
         'height': height}
    d.update(kw)
    return d


OPENINGS = [
    op('entry_question', 'entry', 'question', 'entry_question', 384, 384, shape='arch', apex=480),
    op('entry_store', 'entry', 'store', 'entry_store', 192, 320),
    op('entry_lift', 'entry', 'lift_foot', 'entry_lift', 224, 288, notes="The cage's gate at the ground floor."),
    op('question_stair', 'question', 'stair1f', 'question_stair', 224, 352, notes="The question's door."),
    op('s1f_s1', 'stair1f', 'stair1', 's1_s2', 'full', 'full', from_wall='north', to_wall='south'),
    op('s1_wards', 'stair1', 'wards', 's1_wards', 320, 352),
    op('wards_roost', 'wards', 'roost', 'wards_roost', 192, 352),
    op('roost_tap1', 'roost', 'tapestry1', 'roost_tap1', 384, 352),
    op('tap1_back1', 'tapestry1', 'back1', 'tap1_back1', 192, 320, notes="The gallery's secret panel."),
    op('back1_bf1', 'back1', 'backf1', 'back1_back2', 'full', 'full', from_wall='north', to_wall='south'),
    op('bf1_back2', 'backf1', 'back2', 'back1_back2', 'full', 'full', from_wall='north', to_wall='south'),
    op('s1_s2f', 'stair1', 'stair2f', 's1_s2', 'full', 'full', from_wall='south', to_wall='north'),
    op('s2f_s2', 'stair2f', 'stair2', 's1_s2', 'full', 'full', from_wall='south', to_wall='north'),
    op('s2_library', 'stair2', 'library', 's2_library', 320, 352),
    op('library_reading', 'library', 'reading', 'library_reading', 192, 352),
    op('library_gallery', 'library', 'gallery2', 'library_gallery', 448, 384, shape='arch', apex=400),
    op('gallery_back2', 'gallery2', 'back2', 'gallery_back2', 256, 352),
    op('back2_bf2', 'back2', 'backf2', 'back2_back3', 'full', 'full', from_wall='south', to_wall='north'),
    op('bf2_back3', 'backf2', 'back3', 'back2_back3', 'full', 'full', from_wall='south', to_wall='north'),
    op('s2_s3f', 'stair2', 'stair3f', 's2_s3', 'full', 'full', from_wall='north', to_wall='south'),
    op('s3f_s3', 'stair3f', 'stair3', 's2_s3', 'full', 'full', from_wall='north', to_wall='south'),
    op('s3_tap', 'stair3', 'tapestries', 's3_tap', 320, 384),
    op('tap_back3', 'tapestries', 'back3', 'tap_back3', 192, 320, notes="The tapestry floor's secret panel."),
    op('tap_loft', 'tapestries', 'loft', 'tap_loft', 192, 352),
    op('back3_crates', 'back3', 'crates', 'back3_crates', 224, 352),
    op('loft_trap', 'loft', 'trap_walk', 'loft_trap', 256, 352),
    op('trap_s4', 'trap_walk', 'stair4', 'trap_s4', 224, 352),
    op('s4_s4f', 'stair4', 'stair4f', 'trap_s4', 'full', 'full', from_wall='north', to_wall='south'),
    op('s4f_l4', 'stair4f', 'landing4', 'trap_s4', 'full', 'full', from_wall='north', to_wall='south'),
    op('l4_pass', 'landing4', 'pass_door', 'l4_door', 256, 352),
    op('pass_study', 'pass_door', 'study', 'pass_study', 224, 320, notes="The last door: 'Who do you seek?'"),
    op('study_boots', 'study', 'boots', 'study_boots', 192, 320),
    op('study_lift', 'study', 'lift_top', 'study_lift', 384, 352),
    op('lift_top', 'lift_foot', 'lift_top', 'lift', 224, 288, notes="The cage's gate at the top."),
]

# ------------------------------------------------------------------------------------------------ D-89 identity
# Lane A8 s29 (2026-11-22), reviews/DESIGN_GATING_AND_IDENTITY.md 2.2 (DD-02: "6d19 rose marble done well, but a
# mansion: a straight corridor for the walk round the outer wall") and 2.3 "Towers are towers": the tapestry floor (3)
# and the study floor (4) stand inside one octagonal outer wall, OCT below (x -1664..5632, y -384..4352, corners cut
# 1280). Every room on that wall shows windows to the sky (flush sky faces framed in t1trima, D1's Darkside sky by
# day): on floor 3 the trapped walk, which now follows the octagon's south, south-east and east sides (two 135-degree
# bends, then the stub into the loft) and the last stair's foot; on floor 4 the study's west and north-west walls and
# the boot closet's north and north-west walls. The study's other walls and the library's south wall are bookcase
# walls (6d19's own bookcas1/2); the bat roost's broken window is open to the sky (a jagged hole).
OCT = [F(-384, -384), F(4352, -384), F(5632, 896), F(5632, 3072), F(4352, 4352), F(-384, 4352), F(-1664, 3072),
       F(-1664, 896)]
SKY = S('t1c3', 64, 64, 2, sky=True)       # the picture is never drawn: the sky shows (atmosphere.yml open_sky)
ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_day'},
              'notes': "The tower's windows (sky faces in the octagonal outer wall of floors 3-4 and the roost's "
                       "broken window) show D1's Darkside sky by day (the preset's own name, never the alias "
                       "xeendark1): the party climbs the tower before M17 is done."}
IDENTITY = {'shape': 'tower', 'family': '6d19',
            'seen': ["rose and white marble halls with columns under a Greek-key frieze, the dead mirror by the door",
                     "the trapped walk bending round the tower's octagonal outer wall, windows to the Darkside sky "
                     "along it",
                     "Ellinger's study inside the same octagon: bookcase walls, windows to the sky, star charts and "
                     "boots"]}


def _edge_len(outline, k):
    a, b = outline[k], outline[(k + 1) % len(outline)]
    return int(round(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5))


def window(wall, offset, length=128, bottom=96, height=224, frame=32, centre_of=None, sky_id=None):
    """A window to the sky in a wall: a flush sky panel framed by four t1trima strips (panels never overlap)."""
    if centre_of is not None:
        offset = (centre_of - length) // 2
    sky = panel(sky_id or 'x', wall, offset, SKY, length=length, bottom=bottom, height=height,
                notes="A window to the sky.")
    if not sky_id:
        sky.pop('id')
    strips = [(offset - frame, frame, bottom - frame, height + 2 * frame), (offset + length, frame, bottom - frame,
                                                                          height + 2 * frame),
              (offset, length, bottom - frame, frame), (offset, length, bottom + height, frame)]
    out = [sky]
    for o, ln, b, h in strips:
        p = panel('x', wall, o, TRIM, length=ln, bottom=b, height=h)
        p.pop('id')
        out.append(p)
    return out


_RM = {r['id'].split(':')[1]: r for r in ROOMS}
# Floor 3: the trapped walk round the octagon's S, SE and E sides (320 wide; the diagonal's inner line x - y = 4288),
# then the stub west into the loft as before. The last stair's foot reaches down to the walk's west end.
_RM['trap_walk']['outline'] = [F(1472, -384), F(4352, -384), F(5632, 896), F(5632, 2560), F(3904, 2560), F(3904, 2240),
                               F(5312, 2240), F(5312, 1024), F(4224, -64), F(1472, -64)]
_RM['trap_walk']['walls'] = [
    {'wall': 0, 'panels': sum([window(0, o) for o in (416, 1248, 2080)], [])},
    {'wall': 1, 'panels': window(1, 0, centre_of=_edge_len(_RM['trap_walk']['outline'], 1))},
    {'wall': 2, 'panels': sum([window(2, o) for o in (384, 1152, 1440)], [])}]   # 1440: the stub's far end
_RM['trap_walk']['notes'] = ("The gauntlet's last stretch: a walk 320 wide round the tower's octagonal outer wall "
                             "(its south, south-east and east sides, windows to the sky) from the loft to the last "
                             "stair, its floor plates firing bolts.")
_RM['stair4']['outline'] = rect(1120, -384, 1408, 832)
_RM['stair4']['walls'] = [{'wall': 'south', 'panels': window('south', 0, centre_of=288)}]
# Floor 4: the study's north-west corner cut by the octagon (windows west and north-west), bookcase walls south and
# east; the boot closet moved inside the octagon's north-west corner (windows north and north-west).
STUDY_BOOKS = S('bookcas1', 256, 256, 1.375)    # two rows of cases up the study's 704
STUDY_BOOKS2 = S('bookcas2', 256, 256, 1.375)
_RM['study']['outline'] = [F(-1664, 2304), F(0, 2304), F(0, 3712), F(-1024, 3712), F(-1664, 3072)]
_RM['study']['platforms'] = [p for p in _RM['study']['platforms'] if p['id'] != 'platform:shelf_s']
_RM['study']['walls'] = [
    # whole bookcase walls, floor to ceiling (a panel of cases beside the plain wall reads as a patch)
    {'wall': 0, 'surface': STUDY_BOOKS2, 'bands': False, 'notes': "A bookcase wall."},
    {'wall': 1, 'surface': STUDY_BOOKS, 'bands': False, 'notes': "A bookcase wall."},
    {'wall': 3, 'panels': window(3, 0, length=192, bottom=320, height=288,
                                 centre_of=_edge_len(_RM['study']['outline'], 3))},
    {'wall': 4, 'panels': window(4, 0, length=192, bottom=320, height=288, centre_of=768)}]
_RM['study']['notes'] = ("Ellinger among star charts and boots inside the tower's octagonal outer wall: bookcase "
                         "walls, windows to the sky west and north-west, his desk, a list on a side table; the lift "
                         "head south, the boot closet north.")
_RM['boots']['outline'] = [F(-896, 3840), F(256, 3840), F(256, 4352), F(-384, 4352)]
_RM['boots']['platforms'] = [plat('boots_rack', (64, 3904), (320, 64), 160, desk_side(160), CEIL,
                                  notes="Racks of boots.")]
_RM['boots']['walls'] = [{'wall': 2, 'panels': window(2, 0, length=128, bottom=96, height=192, centre_of=640)},
                         {'wall': 3, 'panels': window(3, 0, length=128, bottom=96, height=192,
                                                      centre_of=_edge_len(_RM['boots']['outline'], 3))}]
_RM['boots']['notes'] = ("Racks of boots and the chest with a pair Ellinger outgrew, in the octagon's north-west "
                         "corner: windows to the sky.")
# Floor 1: the bat roost's broken window open to the sky: a jagged hole (the sky panel keeps its id for the event).
_RM['roost']['walls'] = [{'wall': 'east', 'panels': [
    panel('window', 'east', 352, SKY, length=192, bottom=160, height=192,
          notes="A broken window open to the sky: the bats' way in."),
    panel('x', 'east', 384, SKY, length=96, bottom=352, height=48),
    panel('x', 'east', 400, SKY, length=128, bottom=112, height=48),
    panel('x', 'east', 304, SKY, length=48, bottom=208, height=112),
    panel('x', 'east', 544, SKY, length=32, bottom=192, height=96)]}]
for _p in _RM['roost']['walls'][0]['panels'][1:]:
    _p.pop('id')
# Floor 2: the library's south wall is a bookcase wall, floor to ceiling.
_RM['library']['walls'] = [{'wall': 'south', 'surface': S('bookcas2', 256, 256, 1.625), 'bands': False,
                            'notes': "A bookcase wall, one case floor to ceiling."}]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (the graph's mix, D-26): Night bats 11311 Vampire Bat 14 (14), 11312 Beholder Bat 20 (10); Gargoyles 11540
# Gargoyle 16 (10), 11541 Gargoyle Lord 22 (6); Magic constructs 11600 Flying Feet 18 (8), 11601 Guardian 24 (2).

VB, BB, GA, GL, FF, GU = 11311, 11312, 11540, 11541, 11600, 11601
POP = [
    ('store', 1, [(VB, -960, -384), (VB, -512, -512), (VB, -96, -384)]),
    ('wards', 2, [(FF, 1856, 1536), (FF, 2496, 1536), (FF, 1856, 2560), (FF, 2496, 2560),
                  (GU, 2176, 2048), (GU, 2560, 2048)]),
    ('roost', 3, [(VB, 3136, 2112), (VB, 3392, 2176), (VB, 3648, 2112), (VB, 3136, 2624), (VB, 3392, 2560),
                  (VB, 3648, 2624)]),
    ('tapestry1', 4, [(FF, 3200, 768), (FF, 3584, 1024), (FF, 3200, 1408), (FF, 3584, 1536)]),
    ('library', 5, [(GA, 1664, 384), (GA, 2688, 896), (GA, 1856, 1856), (GA, 2688, 1792)]),
    ('reading', 6, [(GA, 1728, 2496), (GA, 2624, 2496), (GL, 1728, 2880), (GL, 2496, 2880)]),
    ('gallery2', 7, [(GA, 3712, 832), (GA, 3712, 1280), (GA, 3712, 1792), (GA, 3712, 2304),
                     (GL, 3200, 1024), (GL, 3200, 1536), (GL, 3200, 2048), (GL, 3200, 2432)]),
    ('tapestries', 8, [(VB, 1792, 2816), (VB, 2560, 2560), (VB, 1792, 1984), (VB, 2560, 1088), (VB, 3328, 704)]),
    ('loft', 9, [(BB, 3136, 2112), (BB, 3392, 2112), (BB, 3648, 2112), (BB, 3136, 2624), (BB, 3392, 2560),
                 (BB, 3648, 2624)]),
    # D-89 identity (s29): the walk follows the octagon (its east side x 5312-5632, the diagonal, the south side
    # y -384..-64)
    ('trap_walk', 10, [(BB, 5472, 1536), (BB, 4928, 256), (BB, 4096, -224), (BB, 2560, -224)]),
]
MONSTERS = []
for room, group, entries in POP:
    for n, (row, x, y) in enumerate(entries):
        MONSTERS.append({'id': 'monster:%s_%d' % (room, n + 1), 'room': 'room:' + room, 'monster': row,
                         'at': F(x, y), 'facing': 270, 'group': group})
MONSTERS.append({'id': 'monster:ellinger', 'room': 'room:study', 'monster': ELLINGER_BODY, 'at': F(-704, 3424),
                 'facing': 270, 'group': 20, 'immobile': True,
                 'notes': "Ellinger behind his desk (NPC 4954 talks through the desk: Words needed): A2's row 11901 "
                          "Xeen Ellinger, friendly to the party (relations.yml xeen_character_ellinger)."})
COUNT = {}
for m in MONSTERS[:-1]:
    COUNT[m['monster']] = COUNT.get(m['monster'], 0) + 1
assert COUNT == {VB: 14, BB: 10, GA: 10, GL: 6, FF: 8, GU: 2}, COUNT

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, room, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + room, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('entry_chandelier', 'entry', 'chndlir0', (-320, 640), hangs=True),
    deco('entry_sconce_s', 'entry', 'scon100', (-1024, 0), wall='south'),
    deco('question_sconce_w', 'question', 'scon100', (640, 320), wall='west'),
    deco('question_sconce_e', 'question', 'scon100', (1792, 480), wall='east'),
    deco('store_barrel_1', 'store', 'bigbarel', (-1064, -680)),
    deco('store_barrel_2', 'store', 'bigbarel', (-1064, -568)),
    deco('store_sack_1', 'store', 'bag01', (168, -680)),
    deco('store_sack_2', 'store', 'bag01', (168, -568)),
    deco('wards_sconce_n', 'wards', 'scon100', (2176, 2816), wall='north'),
    deco('wards_sconce_s', 'wards', 'scon100', (2176, 1280), wall='south'),
    deco('tap1_sconce', 'tapestry1', 'scon100', (3392, 512), wall='south'),
    deco('library_chandelier', 'library', 'chndlir0', (2176, 1152), hangs=True),
    deco('library_candle_1', 'library', 'cndlab0', (1728, 640), floor_height=1040),
    deco('library_candle_2', 'library', 'cndlab0', (2560, 1152), floor_height=1040),
    deco('reading_candle', 'reading', 'cndlab0', (2088, 2688), floor_height=1032),
    deco('reading_sconce', 'reading', 'scon100', (1536, 2688), wall='west'),
    # lights audit (merge point 14): out of the library arch (y 1184-1632) onto the west wall south of it
    deco('gallery_sconce_1', 'gallery2', 'scon100', (2944, 896), wall='west'),
    deco('gallery_sconce_2', 'gallery2', 'scon100', (2944, 2240), wall='west'),
    deco('tap_sconce_1', 'tapestries', 'scon100', (2816, 2560), wall=3),
    deco('tap_sconce_2', 'tapestries', 'scon100', (1536, 1792), wall='west'),
    deco('crates_barrel_1', 'crates', 'bigbarel', (3032, 1048)),
    deco('crates_barrel_2', 'crates', 'bigbarel', (3032, 1160)),
    deco('crates_barrel_3', 'crates', 'bigbarel', (3144, 1048)),
    deco('crates_barrel_4', 'crates', 'bigbarel', (3032, 1704)),
    deco('crates_barrel_5', 'crates', 'bigbarel', (3144, 1704)),
    deco('crates_sack_1', 'crates', 'bag01', (3480, 1704)),
    deco('crates_sack_2', 'crates', 'bag01', (3592, 1704)),
    deco('crates_sack_3', 'crates', 'bag01', (3704, 1704)),
    deco('crates_barrel_6', 'crates', '7dec32', (4160, 1704)),
    deco('crates_barrel_7', 'crates', '7dec32', (4160, 1584)),
    deco('study_chandelier', 'study', 'chndlir0', (-832, 3008), hangs=True),
    deco('study_candle', 'study', 'cndlab0', (-616, 3264), floor_height=2000),
    deco('study_sconce', 'study', 'scon100', (0, 2880), wall='east'),
    deco('landing4_sconce', 'landing4', 'scon100', (1088, 2624), wall='north'),
    deco('boots_sconce', 'boots', 'scon100', (256, 4160), wall='east'),   # D-89 identity (s29): the closet moved
]

LIGHTS = [
    {'id': 'light:entry', 'room': 'room:entry', 'at': F(-448, 640), 'height': 480, 'radius': 1600,
     'color': F(255, 220, 180)},
    {'id': 'light:question', 'room': 'room:question', 'at': F(1216, 480), 'height': 400, 'radius': 1100,
     'color': F(255, 210, 170)},
    {'id': 'light:store', 'room': 'room:store', 'at': F(-448, -384), 'height': 300, 'radius': 900,
     'color': F(255, 190, 140)},
    {'id': 'light:shaft', 'room': 'room:lift_foot', 'at': F(-768, 1600), 'height': 300, 'radius': 700,
     'color': F(220, 210, 255)},
    {'id': 'light:shaft_top', 'room': 'room:lift_top', 'at': F(-768, 2080), 'height': 300, 'radius': 800,
     'color': F(220, 210, 255)},
    {'id': 'light:wards', 'room': 'room:wards', 'at': F(2176, 2048), 'height': 320, 'radius': 1500,
     'color': F(190, 200, 255), 'pulse': {'intensity': F(0.75, 1), 'frequency': 0.4}},
    {'id': 'light:roost', 'room': 'room:roost', 'at': F(3392, 2368), 'height': 300, 'radius': 900,
     'color': F(170, 190, 220)},
    {'id': 'light:tapestry1', 'room': 'room:tapestry1', 'at': F(3392, 1152), 'height': 320, 'radius': 1200,
     'color': F(255, 200, 150)},
    {'id': 'light:library', 'room': 'room:library', 'at': F(2176, 1152), 'height': 320, 'radius': 1700,
     'color': F(255, 210, 160)},
    {'id': 'light:reading', 'room': 'room:reading', 'at': F(2176, 2688), 'height': 300, 'radius': 1200,
     'color': F(255, 200, 150)},
    {'id': 'light:gallery', 'room': 'room:gallery2', 'at': F(3392, 1632), 'height': 300, 'radius': 1400,
     'color': F(255, 200, 150)},
    {'id': 'light:tapestries', 'room': 'room:tapestries', 'at': F(2176, 1920), 'height': 400, 'radius': 1600,
     'color': F(255, 200, 150)},
    {'id': 'light:loft', 'room': 'room:loft', 'at': F(3392, 2368), 'height': 400, 'radius': 900,
     'color': F(255, 120, 100), 'notes': "The beholder bats' red eyes."},
    {'id': 'light:trap_s', 'room': 'room:trap_walk', 'at': F(3200, -224), 'height': 300, 'radius': 1200,
     'color': F(255, 160, 110)},
    {'id': 'light:trap_e', 'room': 'room:trap_walk', 'at': F(5472, 1280), 'height': 300, 'radius': 1200,
     'color': F(255, 160, 110)},
    {'id': 'light:crates', 'room': 'room:crates', 'at': F(3584, 1376), 'height': 300, 'radius': 900,
     'color': F(255, 190, 140)},
    {'id': 'light:stairs', 'room': 'room:stair2', 'at': F(1088, 640), 'height': 300, 'radius': 1000,
     'color': F(255, 210, 170)},
    {'id': 'light:stair1', 'room': 'room:stair1', 'at': F(1088, 2432), 'height': 300, 'radius': 1000,
     'color': F(255, 210, 170)},
    {'id': 'light:stair3', 'room': 'room:stair3', 'at': F(1088, 2432), 'height': 300, 'radius': 1000,
     'color': F(255, 210, 170)},
    {'id': 'light:landing4', 'room': 'room:landing4', 'at': F(1088, 2432), 'height': 300, 'radius': 1000,
     'color': F(255, 210, 170)},
    {'id': 'light:back', 'room': 'room:back2', 'at': F(4288, 2432), 'height': 300, 'radius': 1000,
     'color': F(255, 190, 140)},
    {'id': 'light:study', 'room': 'room:study', 'at': F(-832, 3008), 'height': 560, 'radius': 1800,
     'color': F(255, 220, 180)},
    {'id': 'light:boots', 'room': 'room:boots', 'at': F(-160, 4096), 'height': 300, 'radius': 800,
     'color': F(255, 200, 150)},
]

SOUNDS = [
    {'id': 'sound:roost_wind', 'room': 'room:roost', 'at': F(3776, 2368), 'sound': 'whistling wind', 'radius': 1600,
     'inner_radius': 400, 'volume': 0.5, 'notes': "Wind through the broken window."},
    {'id': 'sound:wards_hum', 'room': 'room:wards', 'at': F(2176, 2048), 'sound': 'humming', 'radius': 1600,
     'inner_radius': 500, 'volume': 0.4, 'notes': "The wards humming in the floor."},
    {'id': 'sound:study_cauldron', 'room': 'room:study', 'at': F(-1280, 2432), 'sound': 'bubbling cauldron01',
     'radius': 1200, 'inner_radius': 300, 'volume': 0.35, 'notes': "Something simmering in Ellinger's study."},
    {'id': 'sound:loft_wind', 'room': 'room:loft', 'at': F(3392, 2560), 'sound': 'whistling wind', 'radius': 1400,
     'inner_radius': 400, 'volume': 0.3, 'notes': "Wind under the roof."},
    # Session 7: the tower's bed (AUDIO.md xeen_amb_tower, bright chimes: quiet). One source in the middle of the
    # tower (the library floor) reaches every room on all five floors, so no two beds stack where they overlap.
    {'id': 'sound:tower_bed', 'room': 'room:library', 'at': F(2176, 1600), 'height': 64, 'sound': 'xeen_amb_tower',
     'radius': 5200, 'inner_radius': 2600, 'volume': 0.35, 'pan': False,  # session 23 (A8): D-48, a bed
     'notes': "The wizard's tower humming with chimes, heard on every floor (one source: no stacking)."},
]


def door(i, opening, kind='hinged', **kw):
    d = {'id': 'door:' + i, 'opening': opening, 'kind': kind}
    if kind == 'hinged':
        d.update({'hinge': 'left', 'thickness': 16, 'speed': 80})
    d.update(kw)
    return d


DOORS = [
    door('question', 'open:question_stair', surface=DOOR, back_surface=DOOR, edge_surface=TRIM,
         notes="The stair door that asks its question (m17.question)."),
    door('store', 'open:entry_store', surface=DOOR, back_surface=DOOR, edge_surface=TRIM),
    door('roost', 'open:wards_roost', surface=DOOR, back_surface=DOOR, edge_surface=TRIM),
    door('back1', 'open:tap1_back1', kind='slide_up', secret=True, thickness=16, speed=80, surface=MARBLE,
         back_surface=DARKWALL, tile=True, notes="The gallery's secret panel to the back stair: opened by the button behind a "
                                      "tapestry, or found and clicked."),
    door('reading', 'open:library_reading', surface=DOOR, back_surface=DOOR, edge_surface=TRIM),
    door('back3', 'open:tap_back3', kind='slide_up', secret=True, thickness=16, speed=80, surface=MARBLE,
         back_surface=DARKWALL, tile=True, notes="The tapestry floor's secret panel to the back stair."),
    door('loft', 'open:tap_loft', surface=DOOR, back_surface=DOOR, edge_surface=TRIM),
    door('pass', 'open:pass_study', surface=DOOR, back_surface=DOOR, edge_surface=TRIM,
         notes="The last door: 'Who do you seek?' (m17.password)."),
    door('boots', 'open:study_boots', surface=DOOR, back_surface=DOOR, edge_surface=TRIM),
    door('gate_foot', 'open:entry_lift', kind='slide_up', thickness=16, speed=160, state='open',
         surface=DOOR, notes="The cage's gate at the ground floor: open while the cage is down."),
    door('gate_top', 'open:lift_top', kind='slide_up', thickness=16, speed=48, surface=DOOR,
         notes="The cage's gate at the top: opened slowly with the cage's climb (it is up before the gate is), "
               "closed when it goes down."),
]

LIFTS = [
    {'id': 'lift:cage', 'room': 'room:lift_foot', 'at': F(-768, 1600), 'size': F(448, 448), 'travel': 1920,
     'thickness': 16, 'speed': 480, 'surface': FLOOR3,
     'notes': "The cage: a floor 448 square riding the shaft between the ground floor (down) and the lift head "
              "(up, 1920)."},
]

SWITCHES = [
    {'id': 'switch:call_foot', 'room': 'room:entry', 'kind': 'button', 'at': F(-384, 1280), 'height': 112,
     'notes': "Call button beside the cage's gate in the entry hall."},
    {'id': 'switch:ride_up', 'room': 'room:lift_foot', 'kind': 'button', 'at': F(-1024, 1600), 'floor_height': 0,
     'height': 112, 'notes': "Inside the shaft at the foot: sends the cage up."},
    {'id': 'switch:call_top', 'room': 'room:lift_top', 'kind': 'button', 'at': F(-448, 2048), 'height': 112,
     'notes': "Call button beside the cage's gate at the lift head."},
    {'id': 'switch:ride_down', 'room': 'room:lift_foot', 'kind': 'button', 'at': F(-1024, 1600), 'floor_height': 0,
     'height': 2032, 'notes': "Inside the shaft at the top, in reach of a rider on the raised cage: sends it down."},
    {'id': 'switch:tap1_button', 'room': 'room:tapestry1', 'kind': 'plate', 'wall': 'east', 'along': 0.8,
     'height': 128, 'notes': "Never drawn plainly: the button lies behind the east tapestry (its panel's event)."},
]
SWITCHES = SWITCHES[:4]

# D-89 identity (s29): two plates on the octagon's south side, two on its east side.
TRAP_AT = [(2240, -224), (3584, -224), (5472, 1344), (5472, 2048)]
PLATES = [
    {'id': 'plate:trap_%d' % i, 'room': 'room:trap_walk', 'at': F(x, y), 'size': F(256, 256),
     'surface': S('t1f2', 128, 128), 'notes': "A floor plate that fires a bolt."}
    for i, (x, y) in enumerate(TRAP_AT, 1)
]

CHESTS = [
    {'id': 'chest:store', 'room': 'room:store', 'at': F(-224, -672), 'kind': 'ch1', 'treasure_level': 2, 'random_items': 2, 'gold': 200, 'notes': "The storeroom's chest."},
    {'id': 'chest:reading', 'room': 'room:reading', 'at': F(2720, 2944), 'kind': 'ch1', 'treasure_level': 2, 'random_items': 2, 'gold': 300, 'notes': "The locked reading chest."},
    {'id': 'chest:crates', 'room': 'room:crates', 'at': F(3008, 1440), 'kind': 'ch1', 'facing': 's',  # MP42: back to the wall
     'treasure_level': 2, 'random_items': 2, 'gold': 250, 'notes': "A chest among the crate room's stores."},
    {'id': 'chest:boots', 'room': 'room:boots', 'at': F(-96, 4256), 'kind': 'ch1', 'treasure_level': 3, 'random_items': 3, 'gold': 500,
     'notes': "The tower's best chest (the map's hoard, one level up): a pair of boots Ellinger outgrew, and more."},
]

EXITS = [
    {'id': 'exit:d1', 'room': 'room:entry', 'wall': 'west', 'size': F(192, 320), 'surface': S('7solid01', 128, 256, 1.25),
     'to': 'exit:d1_tower', 'notes': "The tower's front door out to Castleview (D1)."},
]

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:entry', 'at': F(-1216, 640), 'facing': 0,
              'notes': "Just inside the front door, facing in (east); D1's door:dd02 lands the party here."},
    'doors': DOORS,
    'lifts': LIFTS,
    'plates': PLATES,
    'switches': SWITCHES,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-02's contents, written by output/studio_cal/dd02/tools/gen.py: 11 doors (two secret, two lift "
             "gates), the lift, 4 chests, 50 placed monsters and Ellinger, no spawn points.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring

D1_MOVE = 'evt.MoveToMap(%d, %d, %d, %d, 0, 0, 0, 0, "xeen_d1.odm", {direct = true})' % (D1_ARRIVAL[0], D1_ARRIVAL[1], D1_ARRIVAL[2],
                                                                        D1_FACING * 2048 // 360)
QUESTION = ("if continueStep == 1 or continueStep == 2 then\n"
            "    XeenQuests.hook(\"m17.question_right\")\n"
            "    return\n"
            "end\n"
            "if continueStep == 3 then\n"
            "    XeenQuests.hook(\"m17.question_wrong\")\n"
            "    AskChoiceWithAnswerSteps(eventId, 5, \"Begone!\", {{Answer = \"Leave the tower\", Step = 5}})\n"
            "    return\n"
            "end\n"
            "if continueStep == 5 then\n"
            "    " + D1_MOVE + "\n"
            "    return\n"
            "end\n"
            "if continueStep ~= nil then\n"
            "    return\n"
            "end\n"
            "XeenQuests.hook(\"m17.question\")\n"
            "AskChoiceWithAnswerSteps(eventId, 4, \"Answer the question:\", {{Answer = \"Let him take up his "
            "sword\", Step = 1}, {Answer = \"Cut him down\", Step = 2}, {Answer = \"I just don't know\", Step = 3}})")
SORCERER = ("if IsPlayerBitSet(PlayerBit(%d)) then\n"
            "    XeenQuests.hook(\"m17.sorcerer_book_again\")\n"
            "    return\n"
            "end\n"
            "if IsAtLeast(ActualIntellect, 20) then\n"
            "    AddValue(BaseIntellect, 2)\n"
            "    SetPlayerBit(PlayerBit(%d))\n"
            "    XeenQuests.hook(\"m17.sorcerer_book\")\n"
            "    return\n"
            "end\n"
            "local hp = 0\n"
            "for v = 10, 5000, 10 do\n"
            "    if not IsAtLeast(HP, v) then break end\n"
            "    hp = v\n"
            "end\n"
            "evt.DamagePlayer(Players.Current, const.Damage.Physical, math.max(5, hp // 10))\n"
            "XeenQuests.hook(\"m17.sorcerer_book_hurt\")") % (BIT_SORCERER, BIT_SORCERER)
LIFT_OK = {'lua': "XeenQuests.can(\"m17.tower_lift\")"}
LIFT_NO = [{'lua': "XeenQuests.hook(\"m17.tower_lift\")"}]
# Session 7: the chain rattle (AUDIO.md xeen_lift) at the cage's shaft, halfway up its travel, whenever it moves.
LIFT_SOUND = [{'lua': "evt.PlaySoundName(\"xeen_lift\", -768, 1600, 960)"}]


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


def book(i, source, title, bit, var, line, resist):
    return {'id': 'evt:' + i, 'preset': 'script', 'source': source, 'title': title,
            'condition': {'not': {'player_bit': bit}},
            'effects': [{'add': {'var': var, 'value': 5}}, {'player_bit': bit},
                        {'text': "%s. %s" % (title.upper(), line)}],  # F13: a status line, not a window
            'else_effects': [{'text': "You learn nothing more from the book."}],
            'notes': "The library's %s (aaze0054): +5 %s resistance once per character (player bit %d; the source's "
                     "+20 rescaled, the graph)." % (title, resist, bit)}


EVENTS = [
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'not': {'qbit': 'arrived_once'}}, 'once': True,
     'effects': [{'message': "ELLINGER'S TOWER. The Queen's wizard locked himself in with his defences when Alamar "
                             "took the throne. Madame Oorla said the orb must see him first, and that at the top the "
                             "tower asks whom you seek. Somewhere above, bats are stirring."},
                 {'qbit': 'arrived_once'}],
     'notes': "Why the party is here (M17), on the first arrival only (arrived_once 117080)."},
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "Ellinger's Tower.",
     'notes': "Every entry: a status line."},
    {'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:d1', 'title': "Exit Ellinger's Tower",
     'notes': "Out to D1 in front of the tower door (exit:d1_tower): the game's own window (D-24); the source's "
              "'Exit Ellinger's Tower?' (aaze0053:0) is the title."},
    {'id': 'evt:mirror', 'preset': 'text', 'source': 'panel:mirror', 'title': 'Mirror',
     'condition': {'qbit': 'm26_stage4'},
     'text': "The mirror shows Ellinger's study, and a small sign: 'Private. Use the one in the square.'",
     'else_effects': [{'text': "The mirror does not respond."}],
     'notes': "The dead mirror (D-26: flavour, no prompt): 'The mirror does not respond.' (aaze0053:11) before "
              "m26.stage4 (111522), the sign after."},
    {'id': 'evt:question', 'preset': 'door', 'source': 'door:question', 'side': 'room:question', 'title': 'Door',
     'condition': {'qbit': 'question_passed'}, 'else_effects': [{'lua': QUESTION}],
     'notes': "m17.question: the door asks (A3's text, the three answers as buttons); 1 or 2: m17.question_right "
              "(question_passed; evt:question_open opens the door), 3: m17.question_wrong and the party is put out "
              "on D1 in front of the tower door. Once passed, a plain door."},
    {'id': 'evt:question_back', 'preset': 'door', 'source': 'door:question', 'side': 'room:stair1f', 'title': 'Door'},
    {'id': 'evt:question_open', 'preset': 'text', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'qbit': 'question_passed'}, 'opens': ['door:question'], 'text': "The stair door swings open.",
     'notes': "The door opens once the question is answered (question_passed set by m17.question_right)."},
    {'id': 'evt:door_store', 'preset': 'door', 'source': 'door:store', 'title': 'Door'},
    {'id': 'evt:chest_store', 'preset': 'chest', 'source': 'chest:store', 'title': 'Chest'},
    {'id': 'evt:chest_reading', 'preset': 'chest', 'source': 'chest:reading', 'title': 'Chest'},
    {'id': 'evt:chest_crates', 'preset': 'chest', 'source': 'chest:crates', 'title': 'Chest'},
    {'id': 'evt:chest_boots', 'preset': 'chest', 'source': 'chest:boots', 'title': 'Chest'},
    {'id': 'evt:door_roost', 'preset': 'door', 'source': 'door:roost', 'title': 'Door'},
    {'id': 'evt:door_reading', 'preset': 'door', 'source': 'door:reading', 'title': 'Door'},
    {'id': 'evt:door_loft', 'preset': 'door', 'source': 'door:loft', 'title': 'Door'},
    {'id': 'evt:door_boots', 'preset': 'door', 'source': 'door:boots', 'title': 'Door'},
    {'id': 'evt:door_back1', 'preset': 'door', 'source': 'door:back1', 'title': 'Panel'},
    {'id': 'evt:door_back3', 'preset': 'door', 'source': 'door:back3', 'title': 'Panel'},
    {'id': 'evt:pass', 'preset': 'door', 'source': 'door:pass', 'side': 'room:pass_door', 'title': 'Door',
     'question': {'message': "Who do you seek?", 'ask': "Answer?", 'answers': ['Ellinger'],
                  'wrong_effects': [{'lua': "XeenQuests.hook(\"m17.password_wrong\")"}]},
     'effects': [{'lua': "XeenQuests.hook(\"m17.password\")"}],
     'notes': "The last door (aaze0056:0-3): 'Who do you seek?'; Ellinger: m17.password ('You may pass!', the qbit "
              "once) and the door opens; any other answer: m17.password_wrong ('Begone!')."},
    {'id': 'evt:pass_back', 'preset': 'door', 'source': 'door:pass', 'side': 'room:study', 'title': 'Door'},
    # The lift (D-9.2, D-26): two stops, called from either end by m17.tower_lift.
    {'id': 'evt:call_foot', 'preset': 'switch', 'source': 'switch:call_foot', 'title': 'Call the lift',
     'condition': LIFT_OK, 'else_effects': LIFT_NO, 'closes': ['lift:cage', 'door:gate_top'],
     'opens': ['door:gate_foot'], 'text': "The cage rattles down the shaft.", 'effects': LIFT_SOUND},
    {'id': 'evt:ride_up', 'preset': 'switch', 'source': 'switch:ride_up', 'title': 'Lift: up',
     'condition': LIFT_OK, 'else_effects': LIFT_NO, 'opens': ['lift:cage', 'door:gate_top'],
     'closes': ['door:gate_foot'], 'text': "The cage climbs the shaft to Ellinger's study.", 'effects': LIFT_SOUND},
    {'id': 'evt:call_top', 'preset': 'switch', 'source': 'switch:call_top', 'title': 'Call the lift',
     'condition': LIFT_OK, 'else_effects': LIFT_NO, 'opens': ['lift:cage', 'door:gate_top'],
     'closes': ['door:gate_foot'], 'text': "The cage climbs the shaft to you.", 'effects': LIFT_SOUND},
    {'id': 'evt:ride_down', 'preset': 'switch', 'source': 'switch:ride_down', 'title': 'Lift: down',
     'condition': LIFT_OK, 'else_effects': LIFT_NO, 'closes': ['lift:cage', 'door:gate_top'],
     'opens': ['door:gate_foot'], 'text': "The cage sinks to the ground floor.", 'effects': LIFT_SOUND},
    # Tapestries (aaze0054:0-2, aaze0055)
    {'id': 'evt:tap1_button', 'preset': 'switch', 'source': 'panel:tap1_c', 'title': 'Tapestry',
     'opens': ['door:back1'], 'text': "Click",
     'notes': "The button behind the gallery's east tapestry: the back stair's panel slides up."},
    text('tap1_a', 'panel:tap1_a', 'Tapestry', "Nothing happens"),
    text('tap1_b', 'panel:tap1_b', 'Tapestry', "Nothing happens"),
    {'id': 'evt:tap3_button', 'preset': 'switch', 'source': 'panel:tap3_a', 'title': 'Tapestry',
     'opens': ['door:back3'], 'text': "Click",
     'notes': "The button behind the tapestry at the arm's east end: the back stair's panel slides up."},
    text('tap3_b', 'panel:tap3_b', 'Tapestry', "Click. Nothing happens.",
         notes="One of the two buttons that do nothing."),
    text('tap3_c', 'panel:tap3_c', 'Tapestry', "Click. Nothing happens."),
    # Books
    {'id': 'evt:sorcerer_book', 'preset': 'script', 'source': 'platform:lectern_sorc',
     'title': "Book of Sorcerer's Knowledge", 'lua': SORCERER,
     'notes': "D-26: the clicking member's current Intellect 20 or more: +2 Intellect (base) once per character "
              "(player bit 11312) and m17.sorcerer_book; again: m17.sorcerer_book_again; below 20: about a tenth of "
              "that member's present hit points (counted in tens: the scripts read no maximum) and "
              "m17.sorcerer_book_hurt, nothing used up."},
    book('book_fire', 'platform:lectern_fire', 'Book of Fire', BIT_FIRE, 'FireResistance',
         "+5 Fire (permanent).", 'Fire'),
    book('book_elec', 'platform:lectern_elec', 'Book of Electricity', BIT_ELEC, 'AirResistance',
         "+5 Elec. (permanent).", 'Air'),
    # The study
    {'id': 'evt:ellinger', 'preset': 'script', 'source': 'platform:desk', 'title': 'Ellinger',
     'lua': "evt.SpeakNPC(%d)" % ELLINGER_NPC,
     'notes': "Ellinger (NPC 4954; A3's topics: Alamar, m17.done with the orb): the studio cannot give a placed "
              "indoor monster its NPC (Words needed), so his desk speaks for him, as DD-04's throne."},
    {'id': 'evt:book_of_boots', 'preset': 'script', 'source': 'platform:boot_rack', 'title': "Book o' Boots",
     'lua': "XeenQuests.hook(\"m17.book_of_boots\")",
     'notes': "m17.book_of_boots (aaze0056:8-9) on the boot rack by the desk."},
    {'id': 'evt:sources', 'preset': 'script', 'source': 'platform:list', 'title': "Ellinger's list",
     'condition': {'qbit': 'm18_started'}, 'lua': "XeenQuests.hook(\"m18.sources_note\")",
     'else_effects': [{'text': "Columns of figures about energy disks. Ellinger has not finished it."}],
     'notes': "m18.sources_note after M17 (m18.started)."},
    {'id': 'evt:study_cue', 'preset': 'text', 'trigger': 'step', 'source': 'room:study', 'once': True,
     'text': "Ellinger looks up from a desk heaped with star charts and boots.", 'seconds': 4},
    # Flavour
    text('charts', 'platform:charts', 'Star charts',
         "Star charts of the Darkside's sky, the sun's path drawn in red and crossed out twice.", window=False),
    text('reading_table', 'platform:reading_table', 'Reading table', "Nothing here."),
    text('window', 'panel:window', 'Broken window', "Wind, and the roofs of Castleview far below.")
]
# The trapped walk's plates (the gauntlet's bolts): a Fire Bolt from the walk's outer wall at the plate.
_from = {1: (2240, -384), 2: (3584, -384), 3: (5632, 1344), 4: (5632, 2048)}   # D-89 identity (s29)
for i, (x, y) in enumerate(TRAP_AT, 1):
    fx, fy = _from[i]
    EVENTS.append({'id': 'evt:trap_%d' % i, 'preset': 'script', 'trigger': 'step', 'source': 'plate:trap_%d' % i,
                   'effects': [{'cast': {'spell': 2, 'from': F(fx, fy, 1560), 'to': F(x, y, 1500),
                                         'mastery': 'expert', 'level': 8}},
                               {'text': "A bolt of fire leaps from the wall!"}],
                   'notes': "A trap plate of the gauntlet's last stretch."})

WIRING = {'format': 0, 'events': EVENTS,
          'notes': "DD-02's events (gen.py): M17's hooks (the question, the password, the lift, the books, the Book o' "
                   "Boots), M18's list, Ellinger's talk by his desk, the dead mirror, the tapestries, the trap "
                   "plates, the exit to D1, the doors and chests."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd02', 'name': "Ellinger's Tower", 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-02', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(13, 9), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 2, 'trap_dice': 3,
        'perception_difficulty': 3, 'refill_days': 672, 'music': 34, 'environment': 'stoneroom',
        'lock_difficulty': 6,
        'slots': [{'monster': 'Xeen Night Bat', 'tier': 1, 'per_marker': F(2, 3), 'weight': 40},
                  {'monster': 'Xeen Gargoyle', 'tier': 0, 'per_marker': F(2, 3), 'weight': 35},
                  {'monster': 'Xeen Construct', 'tier': 0, 'per_marker': F(1, 2), 'weight': 25}],
    },
    'neighbours': [{
        'id': 'exit:d1_tower', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': F(*D1_ARRIVAL),
        'arrival_hint': "On D1 inside Castleview's walls, in front of Ellinger's Tower's door (thing:ellinger_tower): "
                        "A6's return point, facing east toward the tower.",
        'direction': D1_FACING,
        'notes': "D1 installed (A6). The tower door's face stands at (3285, 9321); the party lands at A6's return "
                 "point 725 west of it, facing east. D1's door into this map (A6's door:dd02) lands at this map's start: (-1216, 640, 0), "
                 "facing east (0)."}],
    'qbits': QBITS,
    'notes': "Xeen design brief, DD-02 Ellinger's Tower (D1; M17-M19, M26), class M, built from the MU-6 graph "
             "(devdocs/xeen/mockups/act3_graphs/dd02.graph.yml) with decider D-26 (mockups/act3_a8_decisions_a.md). "
             "Party 20-22, band 14-24, 50 placed monsters on the world's rows (night bats 11311-11312, gargoyles "
             "11540-11541, constructs 11600-11601; no spawn points, encounter chance 0), treasure 2 (the boot "
             "closet's chest 3), music 34. Quest bits M17's (111340-111342), M18's started (111360), M26's stage4 "
             "(111522) read; the map's arrived_once 117080 (provisional block 117080-117119). Player bits 11312 "
             "(Book of Sorcerer's Knowledge), 11313 (Book of Fire), 11314 (Book of Electricity).",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan (L1 words; L2 adds extents, floors and heights)

TOWER_T = "MM6 Agar's Laboratory (6d19): rose and white marble brick t1wl0lg, column walls, marble floors, t1c3"
DARK_T = "6d19's darker wall t1wl7ctb, floor t1f3"
STAIR_T = "6d19's narrow column wall t1wl4cts, floor t1f3"


def placed(actor, count, level, notes=None):
    d = {'actor': actor, 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


def room_box(i):
    for r in ROOMS:
        if r['id'] == 'room:' + i:
            xs = [p[0] for p in r['outline']]
            ys = [p[1] for p in r['outline']]
            f0 = r['floor']
            f1 = r['slope']['to'] if 'slope' in r else f0
            clear = r['ceiling'] - max(f0, f1) if 'slope' not in r else r['ceiling'] - max(f0, f1)
            return (max(xs) - min(xs), max(ys) - min(ys)), (f0 if f0 == f1 else F(f0, f1)), clear
    raise KeyError(i)


def sp(i, name, kind, size, purpose, theme, pop=None, treasure=None, **kw):
    ext, floor, clear = room_box(i)
    d = {'id': 'room:' + i, 'name': name, 'kind': kind, 'size': size, 'extent': F(*ext), 'floor': floor,
         'clear_height': clear, 'purpose': purpose, 'theme': theme}
    if pop:
        d['population'] = pop
    if treasure:
        d['treasure'] = treasure
    d.update(kw)
    return d


def chest(tier, notes):
    return [{'kind': 'chest', 'count': 1, 'tier': tier, 'items': F(2, 2), 'notes': notes}]


SPACES = [
    sp('entry', 'Entry hall', 'room', 'M', "Arrival and the exit to D1: inside the door from Castleview; the dead "
       "mirror ('The mirror does not respond.'); the lift's cage north.", TOWER_T, safe=True, empty=True),
    sp('question', 'Hall of the Question', 'room', 'M', "The stair door asks: 'Intruders, answer the following "
       "question or be destroyed!' (m17.question): 1 or 2 open it, 3 puts the party out on D1.", TOWER_T, empty=True),
    sp('store', 'Storeroom', 'room', 'S', "Barrels, sacks and a chest; bats.", TOWER_T,
       [placed('Vampire Bat (11311)', 3, 14)], chest(2, "The storeroom's chest.")),
    sp('lift_foot', 'Lift foot', 'corridor', 'S', "The cage at the foot of a closed shaft: before Ellinger has spoken it "
       "does not move (m17.tower_lift); after, it runs to the study and back.", STAIR_T, empty=True),
    sp('stair1f', 'Main stair (ground to gauntlet)', 'corridor', 'S', "Past the question's door.", STAIR_T, empty=True),
    sp('stair1', 'Stair', 'corridor', 'S', "The main stair's landing on the gauntlet floor.", STAIR_T, empty=True),
    sp('wards', 'Hall of Wards', 'room', 'L', "Ellinger's defences: warded circles and the constructs that keep "
       "Alamar's spies out.", TOWER_T, [placed('Flying Feet (11600)', 4, 18), placed('Guardian (11601)', 2, 24)]),
    sp('roost', 'Bat roost', 'room', 'M', "A cold room with a broken window.", DARK_T,
       [placed('Vampire Bat (11311)', 6, 14)]),
    sp('tapestry1', 'Tapestry gallery', 'corridor', 'M', "Tapestries of boots through the ages; a button behind one "
       "opens the back stair ('Click'), the others 'Nothing happens'.", TOWER_T, [placed('Flying Feet (11600)', 4, 18)]),
    sp('back1', 'Back stair (foot)', 'corridor', 'S', "The servants' stair's foot, behind a tapestry.", DARK_T,
       empty=True),
    sp('backf1', 'Back stair (first flight)', 'corridor', 'S', "The servants' stair.", DARK_T, empty=True),
    sp('stair2f', 'Main stair (gauntlet to library)', 'corridor', 'S', "The main stair.", STAIR_T, empty=True),
    sp('stair2', 'Stair', 'corridor', 'S', "The main stair's landing on the library floor.", STAIR_T, empty=True),
    sp('library', 'The library', 'room', 'L', "Shelves and stacks; the Book of Fire and the Book of Electricity (+5 "
       "Fire, +5 Air resistance, once per character), the Book of Sorcerer's Knowledge (D-26); gargoyle bookends "
       "wake.", TOWER_T, [placed('Gargoyle (11540)', 4, 16)]),
    sp('reading', 'Reading room', 'room', 'M', "A long table and a locked reading chest.", TOWER_T,
       [placed('Gargoyle (11540)', 2, 16), placed('Gargoyle Lord (11541)', 2, 22)],
       chest(2, "The reading chest.")),
    sp('gallery2', 'Gargoyle gallery', 'corridor', 'M', "A gallery along the outer wall, statues in every bay.",
       TOWER_T, [placed('Gargoyle (11540)', 4, 16), placed('Gargoyle Lord (11541)', 4, 22)]),
    sp('back2', 'Back stair', 'corridor', 'S', "The servants' stair's landing on the library floor.", DARK_T,
       empty=True),
    sp('backf2', 'Back stair (second flight)', 'corridor', 'S', "The servants' stair.", DARK_T, empty=True),
    sp('stair3f', 'Main stair (library to tapestry floor)', 'corridor', 'S', "The main stair.", STAIR_T, empty=True),
    sp('stair3', 'Stair', 'corridor', 'S', "The main stair's head on the tapestry floor.", STAIR_T, empty=True),
    sp('tapestries', 'Tapestry maze', 'room', 'L', "A hall divided by hanging tapestries; behind three wall "
       "tapestries a button: one opens the back stair, two 'Nothing happens'.", TOWER_T,
       [placed('Vampire Bat (11311)', 5, 14)]),
    sp('loft', 'Beholder loft', 'room', 'M', "Under the roof timbers: the red-eyed bats roost.", DARK_T,
       [placed('Beholder Bat (11312)', 6, 20)]),
    sp('trap_walk', 'Trapped walk', 'corridor', 'M', "A walk round the outer wall whose floor plates fire bolts: the "
       "gauntlet's last stretch, to the last stair.", DARK_T, [placed('Beholder Bat (11312)', 4, 20)]),
    sp('back3', 'Back stair (top)', 'corridor', 'S', "The servants' stair, behind a tapestry.", DARK_T, empty=True),
    sp('crates', 'Crate room', 'room', 'S', "A storeroom (barrels and sacks in clumps) and a chest.", DARK_T,
       treasure=chest(2, "A chest among the stores."), empty=True),
    sp('stair4', 'Last stair (foot)', 'corridor', 'S', "The trapped walk's end.", DARK_T, empty=True),
    sp('stair4f', 'Last stair', 'corridor', 'S', "Up to the top landing.", STAIR_T, empty=True),
    sp('landing4', 'Top landing', 'corridor', 'S', "The last stair's head; one door, with a mouth carved over it.",
       STAIR_T, empty=True),
    sp('pass_door', 'The last door', 'room', 'S', "The door asks: 'Who do you seek?' Ellinger: 'You may pass!' "
       "(m17.password); anything else: 'Begone!' (m17.password_wrong). Oorla gives the name (M15).", TOWER_T,
       empty=True),
    sp('study', "Ellinger's study", 'room', 'L', "Ellinger among star charts and boots (NPC 4954, M17-M19, M26): "
       "he takes the disks here, five at a time. The Book o' Boots (m17.book_of_boots), the list of disk sources "
       "(m18.sources_note).", TOWER_T, empty=True),
    sp('lift_top', 'Lift head', 'corridor', 'S', "The lift's upper stop, behind the study.", STAIR_T, empty=True),
    sp('boots', 'Boot closet', 'room', 'S', "Racks of boots; the tower's best chest.", TOWER_T,
       treasure=chest(3, "A pair Ellinger outgrew, and more (the hoard)."), empty=True),
]
for s in SPACES:
    if s.get('empty') and 'population' in s:
        del s['empty']
FLOOR_OF = {}
for r in ROOMS:
    FLOOR_OF[r['id']] = r['floor']


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


LINKS = [
    link('entry_question', 'entry', 'question', 'open'),
    link('entry_store', 'entry', 'store', 'door', motion='swing'),
    link('entry_lift', 'entry', 'lift_foot', 'door', motion='slide', notes="The cage's gate."),
    link('question_stair', 'question', 'stair1f', 'door', motion='swing', notes="The question's door."),
    link('s1_wards', 'stair1', 'wards', 'open'),
    link('wards_roost', 'wards', 'roost', 'door', motion='swing'),
    link('roost_tap1', 'roost', 'tapestry1', 'open'),
    link('tap1_back1', 'tapestry1', 'back1', 'secret_door', notes="Behind a tapestry: a button opens it."),
    link('s1_s2', 'stair1f', 'stair2', 'stairs', rise=960, notes="Up the main stair: stair1f, stair1, stair2f."),
    link('back1_back2', 'back1', 'back2', 'stairs', rise=480, notes="The back stair's first flight (backf1)."),
    link('s2_library', 'stair2', 'library', 'open'),
    link('library_reading', 'library', 'reading', 'door', motion='swing'),
    link('library_gallery', 'library', 'gallery2', 'open'),
    link('gallery_back2', 'gallery2', 'back2', 'open'),
    link('s2_s3', 'stair2', 'stair3', 'stairs', rise=480, notes="The main stair's third flight (stair3f)."),
    link('back2_back3', 'back2', 'back3', 'stairs', rise=480, notes="The back stair's second flight (backf2)."),
    link('s3_tap', 'stair3', 'tapestries', 'open'),
    link('tap_back3', 'tapestries', 'back3', 'secret_door', notes="Behind a tapestry: a button opens it."),
    link('tap_loft', 'tapestries', 'loft', 'door', motion='swing'),
    link('loft_trap', 'loft', 'trap_walk', 'open'),
    link('back3_crates', 'back3', 'crates', 'open'),
    link('trap_s4', 'trap_walk', 'landing4', 'stairs', rise=480, notes="The last stair (stair4, stair4f)."),
    link('l4_door', 'landing4', 'pass_door', 'open'),
    link('pass_study', 'pass_door', 'study', 'door', motion='swing', notes="'Who do you seek?'"),
    link('study_boots', 'study', 'boots', 'door', motion='swing'),
    link('study_lift', 'study', 'lift_top', 'open'),
    link('lift', 'lift_foot', 'lift_top', 'lift', rise=1920, notes="The cage: after m17.done (Ellinger has spoken), "
                                                                     "both ways, two stops (D-9.2)."),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "Ellinger, the Queen's wizard, locked himself in his tower inside Castleview's walls when Alamar took "
                 "the throne. The door asks a question of conscience; any honest answer passes, and 'I just don't "
                 "know' puts the party back in the street. Above, the gauntlet: a hall of wards with Ellinger's "
                 "constructs, bats, a library whose gargoyle bookends wake, a floor of tapestries hiding buttons and "
                 "back stairs, a loft of beholder bats and a trapped walk round the outer wall. At the top a door asks "
                 "whom you seek. Ellinger explains the Energy Disks; after that a lift runs from his study to the "
                 "ground floor, so the disks come to him without the climb.",
        'purpose': "M17 Ellinger's Tower (D1): the question, the gauntlet, the password, Ellinger; M18's list; the "
                   "study is where Ellinger takes the disks (M19, M26). Party 20-22; band 14-24; 50 monsters; "
                   "treasure 2, the boot closet 3. About 25 minutes.",
        'mood': "A scholar's tower of rose and white marble, lamplit; dusty tapestries, wind at broken windows, bats "
                "under the roof.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'loops': [
            {'id': 'loop:back_stair', 'spaces': ['room:tapestry1', 'room:back1', 'room:back2', 'room:gallery2',
                                                 'room:library', 'room:stair2', 'room:stair1', 'room:wards',
                                                 'room:roost'],
             'notes': "The servants' stair joins floors 1-2 behind the tapestries: a second way up."},
            {'id': 'loop:top', 'spaces': ['room:tapestries', 'room:back3', 'room:crates', 'room:back2',
                                          'room:gallery2', 'room:library', 'room:stair2', 'room:stair3'],
             'notes': "Round the tapestry floor by the back stair."},
            {'id': 'loop:lift', 'spaces': ['room:entry', 'room:lift_foot', 'room:lift_top', 'room:study'],
             'notes': "After M17 the lift closes the climb into a ring (D-9.2)."}],
        'entrances': [{'id': 'entrance:front_door', 'space': 'room:entry', 'kind': 'both',
                       'neighbour': 'exit:d1_tower', 'facing': 'e', 'how': "Just inside the front door, facing in."}],
        'critical_path': ['room:entry', 'room:question', 'room:stair1f', 'room:stair1', 'room:stair2f', 'room:stair2',
                          'room:stair3f', 'room:stair3', 'room:tapestries', 'room:loft', 'room:trap_walk',
                          'room:stair4', 'room:stair4f', 'room:landing4', 'room:pass_door', 'room:study'],
        'return_path': ['room:study', 'room:lift_top', 'room:lift_foot', 'room:entry'],
        'goals': [
            {'id': 'goal:ellinger', 'space': 'room:study', 'kind': 'set',
             'what': "Speak with Ellinger holding the Dragon Pharaoh's orb (m17.done); the lift then runs."}],
        'atmosphere': "Lamplit marble (ambient 18-24), the bat floors dim (12). Music 34. Sounds: wind at the roost's "
                      "broken window and under the roof, the wards humming, something simmering in the study.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': 4, 'doors': 11, 'fixed_actors': 51, 'loops': 3, 'monsters_about': 50,
                   'rooms': len(ROOMS), 'sectors': len(ROOMS), 'spawn_points': 0, 'floor_area_millions': 34},
        'notes': "Class M (MAPS, Dungeons): 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors. The "
                 "graph's 25 review spaces as 32 rooms (each flight of the two switchback stairs a room of its own, "
                 "and the last stair's foot). D-26: the Book per Q1, the mirror flavour only, the crate room a real "
                 "storeroom, the lift shaft closed on floors 1-3.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """ Floor 4 (1920)   [Boot closet $$]
                        |door
                 [ELLINGER'S STUDY: Ellinger, Book o' Boots, list]=door 'Who do you seek?'=[last door]--[top landing]
                        |                                                                       |  last stair
                 [Lift head]                                                                    |
 Floor 3 (1440)    ||   [stair]--[Tapestry maze: 3 buttons]==door==[Beholder loft]              |
                   ||       |          \\## (tapestry)                  |                        |
                   ||       |           [back stair top]--[Crate room $, storeroom]              |
                   ||       |                                    [Trapped walk: plates]---------+
 Floor 2 (960)     ||   [stair]--[The library: 3 books]==door==[Reading room $]
                   ||       |          \\----[Gargoyle gallery]--[back stair]
 Floor 1 (480)     ||   [stair]--[Hall of Wards]==door==[Bat roost]--[Tapestry gallery]##[back stair foot]
                   ||       |
 Floor 0 (0)   [LIFT SHAFT, closed on floors 1-3]
                   |gate
  D1 door --[Entry hall: dead mirror]--[Hall of the Question]==the question's door==[stair]
                   |door
               [Storeroom $]

 $ chest   == door   ## secret panel behind a tapestry   || the closed lift shaft (cage: two stops, after m17.done)
"""


def write(level):
    d = OUT + '/' + level
    os.makedirs(d, exist_ok=True)
    dump(d + '/project.yml', dict(PROJECT, identity=IDENTITY) if level == 'L4' else PROJECT)
    dump(d + '/plan.yml', plan(level))
    open(d + '/diagram.txt', 'w').write(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d + '/rooms.yml', {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:tower', 'ambient': 18},
                                'rooms': ROOMS, 'openings': OPENINGS,
                                'notes': "DD-02 at L3/L4: 32 rooms on five floors in the plan's frame (x east, y "
                                         "north). Written by output/studio_cal/dd02/tools/gen.py."})
    if level == 'L4':
        dump(d + '/atmosphere.yml', ATMOSPHERE)   # D-89 identity (s29): the windows' sky
        dump(d + '/objects.yml', OBJECTS)
        dump(d + '/wiring.yml', WIRING)


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
