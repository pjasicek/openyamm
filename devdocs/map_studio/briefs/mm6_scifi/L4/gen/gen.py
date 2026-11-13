# Writes the mm6_scifi L4 project files from the measured room table below.
# The tables are the description; this script only spares typing 90 rooms of YAML by hand and computes each
# opening's `along` from the original portal's centre. Run: python3 output/studio_cal/mm6_scifi/gen.py
import json, math, sys, collections, os
sys.path.insert(0, 'output/studio_cal/mm6_scifi')
from secs import d, V, F, S, area, bb
import yaml

L4 = 'devdocs/map_studio/briefs/mm6_scifi/L4'
TS = json.load(open('output/studio_cal/mm6_scifi/texsizes.json'))
SC = yaml.safe_load(open('assets_dev/worlds/mm6/maps/sci-fi.scene.yml'))


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


ROOMS = []
RB = {}


def R(rid, name, sec, outline, floor, ceil, **kw):
    a = sum(outline[i][0] * outline[(i + 1) % len(outline)][1] - outline[(i + 1) % len(outline)][0] * outline[i][1]
            for i in range(len(outline)))
    if a < 0:
        outline = outline[::-1]
    r = dict(id=rid, name=name, sec=sec, outline=outline, floor=floor, ceiling=ceil, **kw)
    ROOMS.append(r)
    RB[rid] = r


OPEN = []


def O(a, b, at, w, h, sill=0, **kw):
    OPEN.append(dict(a=a, b=b, at=at, w=w, h=h, sill=sill, **kw))


def surf(t, **kw):
    s = {'texture': t, 'size': TS[t]}
    s.update(kw)
    return s


# ---------------------------------------------------------------- the two halls
HALL_LOW = [[-1186, -3544], [0, -3544], [0, -3151], [768, -3151], [768, -3544], [1975, -3544], [3556, -1965],
            [3556, -768], [3168, -768], [3168, 0], [3556, 0], [3556, 1197], [1975, 2777], [768, 2777], [768, 2383],
            [0, 2383], [0, 2777], [-1186, 2777], [-2767, 1197], [-2767, 0], [-2371, 0], [-2371, -768],
            [-2767, -768], [-2767, -1965]]
R('hall_lower', 'Reactor hall, lower level', 1, HALL_LOW, 0, 768,
  wall='swll4dk', floor_t='swflorc', ceil_t='swcirc2', nobands=True,
  walls=[{'wall': w_, 'surface': surf('swall5')} for w_ in (1, 2, 3, 7, 8, 9, 13, 14, 15, 19, 20, 21)],
  pillars=[{'outline': [[-384, -768], [0, -768], [0, -1175], [768, -1175], [768, -768], [1163, -768], [1163, 0],
                        [768, 0], [768, 407], [0, 407], [0, 0], [-384, 0]], 'surface': surf('swall5')}],
  notes="Sectors 1 to 4 of the original (the four quadrants of one octagonal hall, 7,113 across, 768 high): its "
        "floor at 0 with the plus-shaped core in the middle as a pillar. The 256-high walkway that runs round "
        "the wall is the twelve walk rooms (a raised part of a floor may not touch the room's walls, so it "
        "cannot be a level or a platform of this room). The walkway is cut by the two stair blocks north and "
        "south and by the two door porches east and west: notches of this outline. Not said: the vaulted soffit "
        "over the walkway (sloping ceiling faces from 256 up to 768) and the four 448-square shafts in the "
        "ceiling up to the upper hall (placeholders in objects.yml).")
WALK = [('w_n', rect(-3162, 0, -2767, 1197), (-2767, 600)),
        ('nw', [[-3162, 1197], [-2767, 1197], [-1186, 2777], [-1186, 3172]], (-1976, 1987)),
        ('n_w', rect(-1186, 2777, 0, 3172), (-593, 2777)),
        ('n_e', rect(768, 2777, 1975, 3172), (1371, 2777)),
        ('ne', [[1975, 2777], [3556, 1197], [3951, 1197], [1975, 3172]], (2765, 1987)),
        ('e_n', rect(3556, 0, 3951, 1197), (3556, 600)),
        ('e_s', rect(3556, -1965, 3951, -768), (3556, -1366)),
        ('se', [[3556, -1965], [3951, -1965], [1975, -3940], [1975, -3544]], (2765, -2755)),
        ('s_e', rect(768, -3940, 1975, -3544), (1371, -3544)),
        ('s_w', rect(-1186, -3940, 0, -3544), (-593, -3544)),
        ('sw', [[-1186, -3940], [-1186, -3544], [-2767, -1965], [-3162, -1965]], (-1976, -2755)),
        ('w_s', rect(-3162, -1965, -2767, -768), (-2767, -1366))]
for i, (k, o, at) in enumerate(WALK):
    R('walk_' + k, 'Lower hall walkway, ' + k.replace('_', ' '), 1, o, 256, 768, wall='swll5dk', floor_t='swrdk2',
      ceil_t='swcirc2', nobands=True)
    O('hall_lower', 'walk_' + k, at, 'full', 'full')
for a_, b_, at in [('w_n', 'nw', (-2964, 1197)), ('nw', 'n_w', (-1186, 2975)), ('n_e', 'ne', (1975, 2975)),
                   ('ne', 'e_n', (3753, 1197)), ('e_s', 'se', (3753, -1965)), ('se', 's_e', (1975, -3742)),
                   ('s_w', 'sw', (-1186, -3742)), ('sw', 'w_s', (-2964, -1965))]:
    O('walk_' + a_, 'walk_' + b_, at, 'full', 'full')

HALL_UP = [[-1152, -3968], [1920, -3968], [3968, -1920], [3968, 1152], [1920, 3200], [-1152, 3200], [-3200, 1152],
           [-3200, -1920]]
PAN = surf('swflora')
panels = []
for o in [[[-384, -768], [-1664, -768], [-1664, -1792], [0, -1792], [0, -1152]],
          [[-3072, -1792], [-2176, -1792], [-2176, -768], [-3072, -768]],
          [[-2688, -2304], [-2176, -2816], [-2176, -2304]],
          [[-1664, -2304], [-1664, -3328], [-1152, -3840], [0, -3840], [0, -2304]],
          [[0, 384], [0, 1024], [-1664, 1024], [-1664, 0], [-384, 0]],
          [[0, 1536], [0, 3072], [-1152, 3072], [-1664, 2560], [-1664, 1536]],
          [[1152, 0], [2432, 0], [2432, 1024], [768, 1024], [768, 384]],
          [[2432, 1536], [2432, 2560], [1920, 3072], [768, 3072], [768, 1536]],
          [[768, -1152], [768, -1792], [2432, -1792], [2432, -768], [1152, -768]],
          [[768, -2304], [768, -3840], [1920, -3840], [2432, -3328], [2432, -2304]],
          [[3840, -768], [2944, -768], [2944, -1792], [3840, -1792]],
          [[3456, -2304], [2944, -2304], [2944, -2816]],
          [[-2688, 1536], [-2176, 1536], [-2176, 2048]],
          [[2944, 2048], [2944, 1536], [3456, 1536]],
          [[-2176, 0], [-2176, 1024], [-3072, 1024], [-3072, 0]],
          [[3840, 1024], [2944, 1024], [2944, 0], [3840, 0]]]:
    a = sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o)))
    if a < 0:
        o = o[::-1]
    panels.append({'outline': o, 'floor': 1120, 'surface': PAN, 'edge': surf('swr2dk')})
panels.sort(key=lambda p: len(p['outline']) == 3)
R('hall_upper', 'Reactor hall, upper level', 5, HALL_UP, 1184, 1940,
  wall='swll5dk', floor_t='swfloor2b', ceil_t='swfloor2b',
  levels=panels,
  ceiling_levels=[{'outline': [[-588, -2755], [1376, -2755], [2765, -1366], [2765, 597], [1376, 1986],
                               [-588, 1986], [-1977, 597], [-1977, -1366]],
                   'ceiling': 2380, 'surface': surf('sky_nit2'), 'edge': surf('swfloor2b')}],
  notes="Sector 5 of the original, standing on top of the lower hall (floor 1184 over the lower ceiling at 768): "
        "an octagon 7,168 across with 16 floor panels sunk 64 (swflora) between walkways 512 wide, and sector 67, "
        "the eight-sided lantern with the night sky, as a raised ceiling. Not said: the ceiling rises as an "
        "eight-sided pyramid from 1696 at the walls to 2183 at the lantern's rim (drawn flat at their mean, 1940, with "
        "the lantern's drum from there), and the four 448-square shafts through the floor down into the lower hall "
        "(sectors 86 to 89; placeholders).")

# ---------------------------------------------------------------- upper level, round the upper hall
R('s7_south_gate', 'South gate passage', 7, rect(197, -4599, 593, -3968), 1184, 1539)
R('s8_south_corridor', 'South corridor (upper)', 8, rect(-2560, -5027, 4768, -4599), 1184, 1539)
R('s10_north_corridor', 'North corridor (upper)', 10,
  [[4768, 4456], [-692, 4456], [-692, 4061], [197, 4061], [197, 3200], [593, 3200], [593, 4061], [4768, 4061]],
  1184, 1539)
R('s10_alcove', 'North corridor alcove', 10, rect(889, 3600, 1382, 4061), 1184, 1440,
  notes="An alcove of the corridor (sector 10). A room of its own because an opening takes the longest pair of "
        "facing walls of its two rooms: as part of the corridor its end wall faced the hall's north wall over a "
        "longer stretch than the gate passage does, and the hall's doorway was built into the alcove.")
O('s10_north_corridor', 's10_alcove', (1135, 4061), 'full', 'full')
R('s11_east_corridor', 'East corridor (upper)', 11,
  [[4768, -5027], [5163, -5027], [5163, 4456], [4768, 4456], [4768, -186], [3968, -186], [3968, -581],
   [4768, -581]], 1184, 1539)
R('s13_se_room', 'South-east room', 13, rect(3168, -4471, 4640, -3552), 1184, 1712)
R('s14_se_gallery', 'South-east viewing room', 14,
  [[4640, -1965], [4148, -1965], [3264, -2849], [3264, -3360], [4640, -3360]], 1184, 1536)
R('s15_east_cell_s', 'East cell (south)', 15, rect(4096, -1760, 4640, -768), 1200, 1520)
R('s16_east_cell_n', 'East cell (north)', 16, rect(4144, 16, 4640, 1008), 1192, 1512)
R('s17_ne_gallery', 'North-east viewing room', 17,
  [[3951, 2283], [4768, 2283], [4768, 2679], [3951, 2679], [3951, 3864], [3654, 3864], [3654, 4061], [3160, 4061],
   [3160, 3864], [2865, 3864], [2865, 2579], [3753, 1691], [3951, 1691]], 1184, 1579)
R('s18_ne_office', 'North-east office', 18,
  [[2172, 3271], [2370, 3074], [2667, 3074], [2667, 3864], [2172, 3864]], 1184, 1579)
R('s19_south_closet', 'South closet', 19, rect(889, -4599, 1382, -4138), 1184, 1440)
R('s20_ne_cell', 'North-east cell', 20, rect(4144, 2880, 4640, 3872), 1184, 1648)
R('s63_east_cell_mid', 'East cell (middle)', 63, rect(4144, 1200, 4640, 2192), 1184, 1512)
R('s64_se_closet', 'South-east closet', 64,
  [[2272, -4480], [2976, -4480], [2976, -3776], [2464, -3776], [2272, -3968]], 1184, 1712)

O('hall_upper', 's7_south_gate', (395, -3968), 'full', 355)
O('s7_south_gate', 's8_south_corridor', (395, -4599), 'full', 355)
O('hall_upper', 's10_north_corridor', (395, 3200), 'full', 355)
O('hall_upper', 's11_east_corridor', (3968, -383), 'full', 355)
O('s10_north_corridor', 's11_east_corridor', (4768, 4258), 'full', 355)
O('s8_south_corridor', 's11_east_corridor', (4768, -4813), 'full', 355)
O('s8_south_corridor', 's19_south_closet', (1135, -4599), 'full', 256)
O('s8_south_corridor', 's13_se_room', (4050, -4599), 395, 355)
O('s11_east_corridor', 's13_se_room', (4768, -3877), 395, 355)
O('s13_se_room', 's14_se_gallery', (4099, -3552), 296, 288)
O('s13_se_room', 's64_se_closet', (3036, -4322), 197, 272)
O('s14_se_gallery', 's15_east_cell_s', (4494, -1890), 198, 240)
O('s11_east_corridor', 's16_east_cell_n', (4717, 357), 198, 224)
O('s11_east_corridor', 's17_ne_gallery', (4768, 2481), 'full', 355)
O('s10_north_corridor', 's17_ne_gallery', (3407, 4061), 'full', 355)
O('s17_ne_gallery', 's18_ne_office', (2789, 3518), 198, 272)
O('s17_ne_gallery', 's63_east_cell_mid', (4024, 1937), 197, 232)
O('s17_ne_gallery', 's20_ne_cell', (4024, 3518), 198, 272)
O('hall_upper', 's17_ne_gallery', (3136, 1984), 904, 197, sill=99,
  notes="A window: the original's sill is 99 above the floors and 229 deep through the hall's wall.")
O('hall_upper', 's14_se_gallery', (3584, -2304), 700, 157, sill=99,
  notes="A window: the original's sill is 99 above the floors.")

# ---------------------------------------------------------------- the ways up: west ramps
R('s22_west_junction', 'West junction', 22, rect(-7508, -3150, -5972, -2766), 393, 648)
R('s21_ramp_up_1', 'South-west ramp, first rise', 21, rect(-5972, -3150, -4446, -2766), 393, 1184,
  slope=dict(to=788, toward='east'),
  notes="The original's ceiling rises with the floor (255 clear); a level ceiling at the top end's height is the "
        "nearest the vocabulary has.")
R('s12_ramp_landing', 'South-west ramp, landing', 12, rect(-4446, -3150, -4050, -2656), 788, 1184)
R('s12_ramp_up_2', 'South-west ramp, second rise', 12, rect(-4446, -2656, -4050, -1110), 788, 1539,
  slope=dict(to=1184, toward='north'))
R('s12_west_gate', 'West gate passage (upper)', 12,
  [[-4446, -1110], [-4050, -1110], [-4050, -581], [-3200, -581], [-3200, -186], [-4050, -186], [-4050, 307],
   [-4446, 307]], 1184, 1539)
R('s46_ramp_down', 'North-west ramp, upper rise', 46, rect(-4446, 307, -4050, 1888), 1184, 1539,
  slope=dict(to=788, toward='north'))
R('s46_ramp_landing', 'North-west ramp, landing', 46, rect(-4446, 1888, -4050, 2382), 788, 1184)
R('s47_ramp_up', 'North-west ramp, lower rise', 47, rect(-5928, 1986, -4446, 2382), 393, 1184,
  slope=dict(to=788, toward='east'))
R('s47_passage', 'North-west passage', 47, rect(-7252, 1986, -5928, 2382), 393, 657)
O('s22_west_junction', 's21_ramp_up_1', (-5972, -2958), 'full', 255)
O('s21_ramp_up_1', 's12_ramp_landing', (-4446, -2958), 'full', 396)
O('s12_ramp_landing', 's12_ramp_up_2', (-4248, -2656), 'full', 396)
O('s12_ramp_up_2', 's12_west_gate', (-4248, -1110), 'full', 355)
O('s12_west_gate', 'hall_upper', (-3200, -383), 'full', 355)
O('s12_west_gate', 's46_ramp_down', (-4248, 307), 'full', 355)
O('s46_ramp_down', 's46_ramp_landing', (-4248, 1888), 'full', 396)
O('s47_ramp_up', 's46_ramp_landing', (-4446, 2184), 'full', 396)
O('s47_passage', 's47_ramp_up', (-5928, 2184), 'full', 264)

# ---------------------------------------------------------------- lower hall's four ways out
R('s9_porch', 'West porch', 9, rect(-3359, -678, -2456, -85), 0, 400, wall='swankdk')
R('s9_ramp', 'West passage ramp', 9, rect(-4150, -678, -3359, -85), 196, 888, slope=dict(to=0, toward='east'),
  wall='swankdk',
  notes="The original's ceiling climbs from 256 at the hall to 888 here, where the lounge above (sector 62) looks "
        "down through a window 128 above its floor. The window is not drawn: it would stand over the passage's "
        "mouth in the same wall, and two openings of one wall may not stand one above the other.")
R('s9_west_passage', 'West passage', 9, rect(-6320, -678, -4150, -85), 196, 463, wall='swankdk')
R('s6_porch', 'East porch', 6, rect(3264, -640, 4000, -128), 0, 256, wall='swall5')
R('s6_ramp', 'East ramp down', 6, rect(4000, -640, 5630, -128), 0, 256, slope=dict(to=-393, toward='east'),
  wall='swall5')
O('hall_lower', 's9_porch', (-2392, -382), 256, 256)
O('s9_porch', 's9_ramp', (-3359, -382), 'full', 'full')
O('s9_ramp', 's9_west_passage', (-4150, -382), 'full', 267)
O('hall_lower', 's6_porch', (3200, -384), 256, 256)
O('s6_porch', 's6_ramp', (4000, -384), 'full', 256)

R('s36_stair_head_w', 'North stair head, west', 36, rect(0, 2876, 197, 3074), 256, 600)
R('s36_stair_head_e', 'North stair head, east', 36, rect(593, 2876, 768, 3074), 256, 600)
R('s36_passage', 'North passage', 36, rect(197, 2876, 593, 4096), 256, 600)
R('s36_ramp', 'North passage ramp', 36, rect(197, 4096, 593, 4753), 256, 649, slope=dict(to=393, toward='north'))
O('walk_n_w', 's36_stair_head_w', (0, 2975), 'full', 344)
O('walk_n_e', 's36_stair_head_e', (768, 2975), 'full', 344)
O('s36_stair_head_w', 's36_passage', (197, 2975), 'full', 'full')
O('s36_stair_head_e', 's36_passage', (593, 2975), 'full', 'full')
O('s36_passage', 's36_ramp', (395, 4096), 'full', 'full')

R('s30_stair_head_w', 'South stair head, west', 30, rect(0, -3842, 208, -3644), 256, 739,
  slope=dict(to=293, toward='east'))
R('s30_stair_head_e', 'South stair head, east', 30, rect(592, -3842, 768, -3644), 256, 739,
  slope=dict(to=293, toward='west'))
R('s30_stair_top', 'South stair, top', 30, rect(208, -3842, 592, -3644), 293, 739)
R('s30_stair', 'South stair', 30, rect(208, -4222, 592, -3842), 293, 648, slope=dict(to=393, toward='south', steps=6))
R('s30_passage', 'South passage', 30, rect(208, -5518, 592, -4222), 393, 648)
O('walk_s_w', 's30_stair_head_w', (0, -3743), 'full', 483)
O('walk_s_e', 's30_stair_head_e', (768, -3743), 'full', 483)
O('s30_stair_head_w', 's30_stair_top', (208, -3743), 'full', 'full')
O('s30_stair_head_e', 's30_stair_top', (592, -3743), 'full', 'full')
O('s30_stair_top', 's30_stair', (400, -3842), 'full', 355)
O('s30_stair', 's30_passage', (400, -4222), 'full', 255)

# ---------------------------------------------------------------- east: the low rooms
R('s49_east_hall', 'East hall', 49, rect(5696, -1856, 8704, 448), -393, -64)
R('s50_east_lobby', 'East lobby', 50, rect(7104, 512, 7360, 2176), -393, -128)
R('s51_east_store', 'East store', 51, rect(5760, 896, 6912, 2176), -393, -64)
R('s52_east_closet', 'East hatch room', 52, rect(5696, -2176, 5953, -1856), -393, -64)
R('s53_ramp_down', 'East ramp to the vault', 53, rect(6016, -2176, 8320, -1920), -417, -128,
  slope=dict(to=-985, toward='east'))
R('s53_vault_lobby', 'Vault lobby', 53,
  [[8384, -2784], [8640, -2784], [8640, -1920], [8320, -1920], [8320, -2176], [8384, -2176]], -985, -725)
R('s54_vault', 'Vault', 54, rect(7552, -3584, 9088, -2816), -985, -656)
O('s6_ramp', 's49_east_hall', (5696, -384), 'full', 265)
O('s49_east_hall', 's50_east_lobby', (7232, 480), 240, 265)
O('s50_east_lobby', 's51_east_store', (7008, 1728), 240, 265)
O('s49_east_hall', 's52_east_closet', (5824, -1856), 'full', 265)
O('s52_east_closet', 's53_ramp_down', (5984, -2048), 240, 255)
O('s53_ramp_down', 's53_vault_lobby', (8320, -2048), 'full', 260)
O('s53_vault_lobby', 's54_vault', (8512, -2800), 240, 260)

# ---------------------------------------------------------------- west: reactor room and around
R('s23_generator', 'Generator room', 23,
  [[-7904, -1965], [-6718, -1965], [-6320, -1550], [-6320, 802], [-6718, 1197], [-7904, 1197], [-8320, 802],
   [-8320, -1550]], 196, 937, wall='swall1',
  beams=[{'path': [[-7252, 1133], [-6700, 1133], [-6384, 818], [-6384, -1566], [-6700, -1901], [-7252, -1901]],
          'width': 128, 'depth': 128, 'bottom': 452, 'surface': surf('swildk')}],
  notes="An eight-sided room 741 high with a balcony 128 wide at 580 along its east side (underside at 452), "
        "which the two upper rooms (sectors 27 and 35) open onto across the cut corners.")
R('s24_ramp', 'Generator room, south ramp', 24, rect(-7508, -2766, -7252, -2063), 393, 648,
  slope=dict(to=221, toward='north'))
R('s25_west_lobby', 'West lobby', 25, rect(-8960, -910, -8320, 192), 196, 610, ceil_t='swll4dk',
  beams=[{'path': [[-8640, -910], [-8640, 192]], 'width': 384, 'depth': 98, 'bottom': 512, 'surface': surf('swankdk')}],
  notes="The ceiling is 610 along the two doorways and 512 over the middle: the lower middle is a beam 384 wide.")
R('s26_west_hall', 'West hall', 26, rect(-9472, -1344, -8960, 320), 196, 708)
R('s27_upper_room_s', 'Balcony room (south)', 27,
  [[-6320, -1550], [-6718, -1965], [-6718, -2190], [-5744, -2190], [-5744, -1550]], 580, 868)
R('s27_east_arm', 'Balcony room (south), east arm', 27, rect(-5744, -2190, -5360, -1934), 580, 847,
  notes="Part of sector 27 (its floor rises 11 along the arm; drawn level). A room of its own because the "
        "opening to the upper corridor would otherwise take the room's longer north-east wall.")
O('s27_upper_room_s', 's27_east_arm', (-5744, -2062), 'full', 'full')
R('s28_upper_corridor', 'Upper corridor', 28,
  [[-4976, -590], [-5232, -590], [-5232, -846], [-5360, -846], [-5360, -2190], [-4976, -2190]], 591, 847)
R('s29_upper_link', 'Upper link', 29, rect(-4976, -1102, -3504, -846), 591, 847)
R('s35_upper_room_n', 'Balcony room (north)', 35,
  [[-6320, 802], [-5730, 802], [-5730, 1010], [-5232, 1010], [-5232, -14], [-4720, -14], [-4720, 242],
   [-4976, 242], [-4976, 1395], [-6718, 1395], [-6718, 1197]], 580, 847)
R('s62_lounge', 'Lounge over the west passage', 62, rect(-5874, -590, -4150, -85), 591, 847)
R('s61_low_passage', 'Low passage', 61, rect(-6320, 434, -4841, 562), 196, 452)
R('s60_low_ramp', 'Low passage ramp', 60, rect(-4841, 434, -3953, 562), 196, 649, slope=dict(to=393, toward='east'))
R('s60_low_top', 'Low passage, behind the plug', 60, rect(-3953, 434, -3696, 562), 393, 649)
R('s44_link_ramp', 'Link ramp', 44, rect(-4720, -14, -4050, 242), 591, 905, slope=dict(to=393, toward='east'))
R('s44_link', 'Link passage', 44, rect(-4050, -14, -3441, 242), 393, 649)
R('s45_ramp', 'Generator room, north ramp', 45, rect(-7508, 1197, -7252, 1986), 196, 657,
  slope=dict(to=393, toward='north'))
R('s45_gate_south', 'North corridor, below the gate', 45, rect(-7508, 1986, -7252, 2382), 393, 657)
R('s45_corridor', 'North-west corridor', 45, rect(-7508, 2579, -7252, 4032), 393, 649)
O('s23_generator', 's9_west_passage', (-6320, -382), 'full', 256)
O('s23_generator', 's24_ramp', (-7380, -2063), 'full', 231)
O('s24_ramp', 's22_west_junction', (-7380, -2766), 'full', 255)
O('s23_generator', 's25_west_lobby', (-8320, -359), 'full', 414)
O('s25_west_lobby', 's26_west_hall', (-8960, -359), 'full', 414)
O('s23_generator', 's27_upper_room_s', (-6519, -1757), 'full', 256)
O('s23_generator', 's35_upper_room_n', (-6519, 1000), 'full', 256)
O('s23_generator', 's61_low_passage', (-6320, 498), 'full', 256)
O('s23_generator', 's45_ramp', (-7380, 1197), 'full', 256)
O('s27_east_arm', 's28_upper_corridor', (-5360, -2062), 'full', 256)
O('s28_upper_corridor', 's62_lounge', (-5104, -590), 'full', 256)
O('s28_upper_corridor', 's29_upper_link', (-4976, -974), 'full', 240)
O('s62_lounge', 's35_upper_room_n', (-5056, -85), 161, 256)
O('s35_upper_room_n', 's44_link_ramp', (-4720, 114), 'full', 256)
O('s44_link_ramp', 's44_link', (-4050, 114), 'full', 256)
O('s61_low_passage', 's60_low_ramp', (-4841, 498), 'full', 256)
O('s60_low_ramp', 's60_low_top', (-3953, 498), 'full', 256)
O('s45_ramp', 's45_gate_south', (-7380, 1986), 'full', 264)
O('s45_gate_south', 's47_passage', (-7252, 2184), 'full', 264)
O('s45_gate_south', 's45_corridor', (-7380, 2480), 'full', 232, id='gate_slab')

# ---------------------------------------------------------------- the 393 level: corridors round the lower hall
R('s38_west_corridor', 'West corridor', 38, rect(-3441, -14, -3185, 4753), 393, 649)
R('s37_north_corridor', 'North corridor', 37, rect(-3441, 4753, 1184, 5009), 393, 649)
R('s39_meeting_hall', 'Meeting hall', 39, rect(-3072, 3392, -1312, 4480), 393, 713)
R('s40_wedge_room', 'Wedge room', 40,
  [[-3040, 1984], [-2912, 1856], [-1920, 2976], [-1920, 3104], [-3040, 3104]], 393, 713)
R('s43_locked_room', 'Room behind the meeting hall', 43, rect(-992, 3424, 96, 4480), 393, 713)
R('s42_nw_corridor', 'North-west corridor (east run)', 42, rect(-7508, 4032, -3441, 4288), 393, 649)
H = "Sector 41 is one H-shaped room; three rooms here, because the door from the corridor would otherwise be " \
    "built into the west wing (an opening takes the first of two equally long pairs of facing walls)."
R('s41_h_room', 'H-shaped room, east wing', 41, rect(-4512, 4480, -4000, 5248), 393, 713, notes=H)
R('s41_h_bar', 'H-shaped room, bar', 41, rect(-4992, 4864, -4512, 4992), 393, 713)
R('s41_h_west', 'H-shaped room, west wing', 41, rect(-5504, 4480, -4992, 5248), 393, 713)
O('s41_h_room', 's41_h_bar', (-4512, 4928), 'full', 'full')
O('s41_h_bar', 's41_h_west', (-4992, 4928), 'full', 'full')
R('s48_panel_room', 'Panel room', 48, rect(-5376, 3072, -4352, 3840), 393, 713)
R('s32_sw_corridor', 'South-west corridor', 32, rect(-3760, -5518, -3504, -1868), 393, 648)
R('s32_ramp', 'South-west corridor ramp', 32, rect(-3760, -1868, -3504, -1102), 393, 847,
  slope=dict(to=591, toward='north'))
R('s31_south_corridor', 'South corridor', 31, rect(-4016, -5774, 1104, -5518), 393, 648)
R('s33_storage_corridor', 'Storage corridor', 33, rect(-7706, -3598, -3760, -3342), 393, 648)
R('s33_ramp', 'Storage corridor ramp', 33, rect(-8496, -3598, -7706, -3342), 393, 648,
  slope=dict(to=196, toward='west'))
R('s34_repair_bay', 'Storage and repair bay', 34, rect(-3200, -5376, 0, -4224), 393, 712)
R('s69_storage_1', 'Storage room 1', 69, rect(-6953, -4816, -6144, -3792), 393, 712)
R('s70_storage_2', 'Storage room 2', 70, rect(-5984, -4816, -5175, -3792), 393, 712)
R('s71_storage_3', 'Storage room 3', 71, rect(-4969, -4816, -4160, -3792), 393, 712)
for i in range(8):
    x0 = -2944 + 384 * i
    R('s%d_bay_stall' % (78 + i), 'Repair bay stall %d' % (i + 1), 78 + i, rect(x0, -4224, x0 + 128, -3968), 393, 648)
    O('s34_repair_bay', 's%d_bay_stall' % (78 + i), (x0 + 64, -4224), 'full', 255)
R('s77_bay_stall_w', 'Repair bay stall (west)', 77, rect(-3328, -4608, -3200, -4480), 393, 648)
O('s34_repair_bay', 's77_bay_stall_w', (-3200, -4544), 'full', 255)
O('s38_west_corridor', 's37_north_corridor', (-3313, 4753), 'full', 256)
O('s38_west_corridor', 's42_nw_corridor', (-3441, 4160), 'full', 256)
O('s38_west_corridor', 's39_meeting_hall', (-3120, 3805), 240, 256)
O('s38_west_corridor', 's40_wedge_room', (-3120, 2704), 240, 256)
O('s38_west_corridor', 's44_link', (-3441, 114), 'full', 256)
O('s60_low_top', 's38_west_corridor', (-3568, 498), 'full', 250, id='plug')
O('s39_meeting_hall', 's43_locked_room', (-1136, 4210), 240, 256)
O('s36_ramp', 's37_north_corridor', (395, 4753), 'full', 256)
O('s42_nw_corridor', 's41_h_room', (-4245, 4384), 240, 256)
O('s42_nw_corridor', 's48_panel_room', (-4750, 3936), 240, 256)
O('s42_nw_corridor', 's45_corridor', (-7380, 4032), 'full', 256)
O('s32_sw_corridor', 's32_ramp', (-3632, -1868), 'full', 255)
O('s32_ramp', 's29_upper_link', (-3632, -1102), 'full', 256)
O('s32_sw_corridor', 's33_storage_corridor', (-3760, -3470), 'full', 255)
O('s32_sw_corridor', 's31_south_corridor', (-3632, -5518), 'full', 255)
O('s32_sw_corridor', 's34_repair_bay', (-3408, -4986), 240, 255)
O('s31_south_corridor', 's30_passage', (400, -5518), 'full', 223)
O('s33_storage_corridor', 's33_ramp', (-7706, -3470), 'full', 255)
O('s33_storage_corridor', 's69_storage_1', (-6549, -3696), 240, 255)
O('s33_storage_corridor', 's70_storage_2', (-5579, -3696), 240, 255)
O('s33_storage_corridor', 's71_storage_3', (-4565, -3696), 240, 255)
O('s22_west_junction', 's33_storage_corridor', (-7358, -3246), 240, 255)

# ---------------------------------------------------------------- far west: the entrance wing and the tube
R('s55_plate_room', 'Pressure plate room', 55,
  [[-9616, -3792], [-9360, -3792], [-9360, -3598], [-8595, -3598], [-8595, -3342], [-8848, -3342], [-8848, -2062],
   [-9616, -2062], [-9616, -2634], [-9376, -2634], [-9376, -2890], [-9616, -2890]], 196, 724)
R('s55_door_ramp', 'Pressure plate room, ramp to the west door', 55, rect(-9616, -2890, -9376, -2634), 196, 724,
  slope=dict(to=288, toward='west'),
  notes="In the original this ramp lies open in the room (one can step onto it from its sides) and is 384 long; a ramp inside a "
        "room is not in the vocabulary, so it is a room of its own with walls along its sides, and 240 long, because an opening takes the longest pair of facing walls and would otherwise choose the ramp's side.")
O('s55_plate_room', 's55_door_ramp', (-9376, -2762), 'full', 'full')
R('s68_plate_store', 'Store behind the plate door', 68, rect(-10543, -3264, -9776, -2240), 288, 608)
R('s56_east_bay', 'Entrance wing, east bay', 56, rect(-8784, 1600, -8016, 3200), 196, 524)
R('s57_c_room', 'Entrance wing, C-shaped store', 57,
  [[-11376, 1009], [-9584, 1009], [-9584, 3313], [-11376, 3313], [-11376, 2545], [-10096, 2545], [-10096, 2033],
   [-11376, 2033]], 196, 516)
R('s58_airlock_hall', 'Airlock hall', 58, rect(-11312, 3377, -9840, 3889), 196, 524)
R('s58_airlock_step', 'Airlock hall, raised end', 58, rect(-11696, 3377, -11312, 3889), 228, 524, floor_t='swfloor5a')
O('s58_airlock_hall', 's58_airlock_step', (-11312, 3633), 'full', 'full')
R('s65_entrance_corridor', 'Entrance corridor', 65, rect(-9408, 320, -9024, 3776), 196, 551)
R('s65_entry', 'Entry', 65, rect(-9536, 3776, -8896, 4288), 196, 452, floor_t='swrdk2', ceil_t='swankdk',
  notes="The head of the entrance corridor, where the party arrives: the original's grated floor and lower "
        "panelled ceiling (the corridor's own ceiling is a shallow vault from 452 to 551, drawn flat at 551).")
O('s65_entrance_corridor', 's65_entry', (-9216, 3776), 'full', 'full')
R('s59_ramp_1', 'Way to the pit, first ramp', 59, rect(-9024, 3264, -8153, 3520), 196, 452,
  slope=dict(to=0, toward='east'))
R('s59_bend', 'Way to the pit, bend', 59,
  [[-8153, 3264], [-7616, 3264], [-7616, 3632], [-7872, 3632], [-7872, 3520], [-8153, 3520]], 0, 452)
R('s59_ramp_2', 'Way to the pit, second ramp', 59, rect(-7872, 3632, -7616, 4441), 0, 452,
  slope=dict(to=-196, toward='north'))
R('s66_pit', 'The pit', 66, rect(-8320, 4544, -5760, 7104), -196, 316,
  levels=[{'outline': [[-7349, 4576], [-5792, 4576], [-5792, 7072], [-7744, 7072], [-7744, 6592], [-7349, 6592]],
           'floor': -452}],
  flights=[{'from': [-6894, 6831], 'to': [-7744, 6831], 'width': 478, 'steps': 16, 'riser': surf('swrdk2')}],
  notes="A hall 2,560 square. Its west third is 256 higher than the rest (-196 over -452) and a stair of two "
        "flights in the north joins the two (nine steps north to a landing, then seven west). The low part is a "
        "sunken level; because a level must keep clear of the room's walls, a ledge 32 wide of the upper floor "
        "runs along the pit's south, east and north walls, which the original does not have. The stair is one "
        "straight flight of 16 steps west along the north wall: the original's first flight and its landing "
        "cannot be built, because a platform inside a sunken level stands at the room's floor, not the level's.")
R('s91_airlock', 'Airlock', 91, rect(-12272, 3377, -11760, 3889), 228, 492, floor_t='swfloor5a')
TUBE = "A tube: the original's cross-section is six-sided (a floor strip 128 wide between two banks that slope up " \
       "74, and the same overhead); drawn as a plain box, since a room's section cannot be chamfered."
R('s91_tube', 'Tube, entry ramp', 91, rect(-13634, 3477, -12272, 3784), 240, 698, slope=dict(to=393, toward='west'),
  floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s91_tube_corner', 'Tube, north-west corner', 91, rect(-14018, 3424, -13634, 3808), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s90_tube', 'Tube, west run', 90, rect(-13988, -4032, -13683, 3424), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s90_tube_corner', 'Tube, south-west corner', 90, rect(-14016, -4416, -13632, -4032), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s76_tube', 'Tube, south run', 76, rect(-13632, -4392, -11072, -4085), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s76_tube_corner', 'Tube, south corner', 76, rect(-11072, -4416, -10688, -4032), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s75_tube', 'Tube, short north run', 75, rect(-11023, -4032, -10716, -2088), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s75_tube_corner', 'Tube, middle corner', 75, rect(-11076, -2088, -10692, -1704), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s74_tube', 'Tube, east run', 74, rect(-10692, -2035, -8644, -1728), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s74_tube_corner', 'Tube, east corner', 74, rect(-8644, -2088, -8260, -1704), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s73_tube', 'Tube, last south run', 73, rect(-8620, -2766, -8313, -2088), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
R('s73_tube_corner', 'Tube, last corner', 73, rect(-8644, -3150, -8260, -2766), 393, 698, floor_t='swrdk', ceil_t='swdoorc', wall='swall4')
R('s72_tube', 'Tube, exit run', 72, rect(-8260, -3097, -7700, -2790), 393, 698, floor_t='swrdk2', ceil_t='swflorb', wall='swll4dk', notes=TUBE)
O('s33_ramp', 's55_plate_room', (-8545, -3470), 'full', 264)
O('s55_door_ramp', 's68_plate_store', (-9712, -2762), 224, 255)
O('s26_west_hall', 's65_entrance_corridor', (-9216, 320), 'full', 355)
O('s65_entrance_corridor', 's56_east_bay', (-8896, 2144), 192, 221)
O('s65_entrance_corridor', 's57_c_room', (-9456, 2865), 256, 221, id='c_room_n')
O('s65_entrance_corridor', 's57_c_room', (-9520, 1425), 192, 256, id='c_room_s')
O('s57_c_room', 's58_airlock_hall', (-10224, 3345), 384, 224, sill=24, id='airlock_hall_e')
O('s57_c_room', 's58_airlock_hall', (-10864, 3345), 384, 224, sill=24, id='airlock_hall_w')
O('s58_airlock_step', 's91_airlock', (-11728, 3624), 256, 264)
O('s65_entrance_corridor', 's59_ramp_1', (-9024, 3392), 'full', 256)
O('s59_ramp_1', 's59_bend', (-8153, 3392), 'full', 'full')
O('s59_bend', 's59_ramp_2', (-7744, 3632), 'full', 'full')
O('s59_ramp_2', 's66_pit', (-7744, 4492), 'full', 512)
O('s91_airlock', 's91_tube', (-12272, 3630), 'full', 228)
O('s91_tube', 's91_tube_corner', (-13634, 3630), 'full', 305)
O('s91_tube_corner', 's90_tube', (-13835, 3424), 'full', 305)
O('s90_tube', 's90_tube_corner', (-13835, -4032), 'full', 305)
O('s90_tube_corner', 's76_tube', (-13632, -4238), 'full', 305)
O('s76_tube', 's76_tube_corner', (-11072, -4238), 'full', 305)
O('s76_tube_corner', 's75_tube', (-10870, -4032), 'full', 305)
O('s75_tube', 's75_tube_corner', (-10870, -2088), 'full', 305)
O('s75_tube_corner', 's74_tube', (-10692, -1881), 'full', 305)
O('s74_tube', 's74_tube_corner', (-8644, -1881), 'full', 305)
O('s74_tube_corner', 's73_tube', (-8466, -2088), 'full', 305)
O('s73_tube', 's73_tube_corner', (-8466, -2766), 'full', 305)
O('s73_tube_corner', 's72_tube', (-8260, -2943), 'full', 305)
O('s22_west_junction', 's72_tube', (-7588, -2958), 256, 255)

if os.path.exists('output/studio_cal/mm6_scifi/gen_extra.py'):
    exec(open('output/studio_cal/mm6_scifi/gen_extra.py').read())

# ================================================================ derive and write
def edges(o):
    return [(o[i], o[(i + 1) % len(o)]) for i in range(len(o))]


def frame(o, i):
    p, q = o[i], o[(i + 1) % len(o)]
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    ax, ay = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    return p, (ax, ay), (ay, -ax), L


def best_pair(A, B):
    best = (0, None)
    for i in range(len(A)):
        po, al, ow, L = frame(A, i)
        for j in range(len(B)):
            qo, bl, bw, M = frame(B, j)
            if al[0] * bl[0] + al[1] * bl[1] > -1 + 1e-9:
                continue
            ox, oy = qo[0] - po[0], qo[1] - po[1]
            gap = ox * ow[0] + oy * ow[1]
            if gap < -1e-6 or gap > 512:
                continue
            ts = ox * al[0] + oy * al[1]
            lo, hi = max(0, ts - M), min(L, ts)
            if hi - lo > best[0] + 1e-6:
                best = (hi - lo, (i, j, lo, hi, gap))
    return best


def poly_area(o):
    return sum(o[i][0] * o[(i + 1) % len(o)][1] - o[(i + 1) % len(o)][0] * o[i][1] for i in range(len(o))) / 2


def dom(si, kind):
    c = collections.Counter()
    for fi in S[si][kind]:
        c[F[fi]['texture'].lower()] += area(F[fi])
    for bad in ('pending',):
        c.pop(bad, None)
    return c.most_common(1)[0][0] if c else None


def Y(v):
    return json.dumps(v)


def inside(o, x, y):
    c = False
    for (p, q) in edges(o):
        if (p[1] > y) != (q[1] > y) and x < (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]) + p[0]:
            c = not c
    return c


def clear(o, x, y, m):
    if not inside(o, x, y):
        return False
    for i in range(len(o)):
        p, al, ow, L = frame(o, i)
        t = (x - p[0]) * al[0] + (y - p[1]) * al[1]
        t = max(0, min(L, t))
        if math.hypot(x - p[0] - al[0] * t, y - p[1] - al[1] * t) < m:
            return False
    return True


def room_at(x, y, z, slack=40):
    best = None
    for r in ROOMS:
        if inside(r['outline'], x, y):
            lo = min(r['floor'], r.get('slope', {}).get('to', r['floor']))
            lo = min([lo] + [l['floor'] for l in r.get('levels', [])])
            hi = max([r['ceiling']] + [c['ceiling'] for c in r.get('ceiling_levels', [])])
            if lo - slack <= z <= hi + slack:
                dist = abs(z - (lo + hi) / 2)
                if best is None or dist < best[0]:
                    best = (dist, r)
    return best[1] if best else None


from bands import bands as sector_bands

DOORISH = ('swdoor', 'swor', 'pending', 'ch5', 'trekscr')


def main_floor(si):
    fl = collections.Counter()
    for fi in S[si]['floor_faces']:
        lo, hi = bb(F[fi])
        fl[lo[2]] += area(F[fi])
    return fl.most_common(1)[0][0]


def edge_texture(r, i):
    """The original's dominant wall texture along one edge of a room."""
    p, al, ow, L = frame(r['outline'], i)
    c = collections.Counter()
    for fi in S[r['sec']]['wall_faces']:
        f = F[fi]
        t = f['texture'].lower()
        if t.startswith(DOORISH):
            continue
        n = f['plane_normal']
        nx, ny = n[0] / 65536, n[1] / 65536
        if nx * ow[0] + ny * ow[1] > -0.9:
            continue
        lo, hi = bb(f)
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
        t_ = (cx - p[0]) * al[0] + (cy - p[1]) * al[1]
        dd = (cx - p[0]) * ow[0] + (cy - p[1]) * ow[1]
        if 0 <= t_ <= L and -40 <= dd <= 140:
            c[t] += area(f)
    if not c:
        return None
    t, a = c.most_common(1)[0]
    if a < 0.3 * L * (r['ceiling'] - r['floor']):
        return None
    return t


from outl import loops_of, simp, parea


def coffer(r):
    """A raised middle of the original's ceiling (a coffer inside a lower rim), measured from its ceiling faces."""
    si = r['sec']
    g = collections.defaultdict(list)
    for fi in S[si]['ceiling_faces']:
        lo, hi = bb(F[fi])
        if lo[2] == hi[2]:
            cx = sum(V[i][0] for i in F[fi]['vertices']) / len(F[fi]['vertices'])
            cy = sum(V[i][1] for i in F[fi]['vertices']) / len(F[fi]['vertices'])
            if inside(r['outline'], cx, cy):
                g[lo[2]].append(fi)
    if len(g) < 2:
        return None
    ar = {z: sum(area(F[i]) for i in fs) for z, fs in g.items()}
    tot = sum(ar.values())
    zhi = max(z for z in g if ar[z] >= 0.15 * tot)
    lows = [z for z in g if z < zhi and ar[z] >= 0.05 * tot]
    if not lows or zhi > r['ceiling'] + 2:
        return None
    zlow = max(lows, key=lambda z: ar[z])
    if zhi - zlow < 16 or zlow - r['floor'] < 200:
        return None
    ls = [simp(l, 12) for l in loops_of(g[zhi])]
    ls = [l for l in ls if parea(l) > 20000]
    if len(ls) != 1 or len(ls[0]) > 12:
        return None
    o = [list(p_) for p_ in ls[0]]
    if not all(clear(r['outline'], x, y, 30) for x, y in o):
        return None
    tx = collections.Counter()
    for fi in g[zhi]:
        tx[F[fi]['texture'].lower()] += area(F[fi])
    rim = collections.Counter()
    for fi in g[zlow]:
        rim[F[fi]['texture'].lower()] += area(F[fi])
    edge = collections.Counter()
    for fi in S[si]['wall_faces']:
        lo, hi = bb(F[fi])
        if lo[2] >= zlow - 1 and hi[2] <= zhi + 1:
            edge[F[fi]['texture'].lower()] += area(F[fi])
    lvl = {'outline': o, 'ceiling': zhi, 'surface': surf(tx.most_common(1)[0][0])}
    if edge and edge.most_common(1)[0][0] in TS:
        lvl['edge'] = surf(edge.most_common(1)[0][0])
    return zlow, rim.most_common(1)[0][0], lvl


def main():
    themes = {}
    out = {'format': 0}
    rooms = []
    for r in ROOMS:
        assert poly_area(r['outline']) > 0, r['id'] + ' is clockwise'
        si = r['sec']
        if 'slope' not in r and 'ceiling_levels' not in r and not r.get('nobands') and not r.get('nocoffer'):
            cf = coffer(r)
            if cf:
                r['ceiling'], rimtex, lvl = cf
                r['ceiling_levels'] = [lvl]
                r.setdefault('ceil_t', rimtex)
        w = r.get('wall') or dom(si, 'wall_faces')
        f = r.get('floor_t') or dom(si, 'floor_faces')
        c = r.get('ceil_t') or dom(si, 'ceiling_faces')
        key = (w, f, c)
        tid = 'theme:%s_%s_%s' % key
        themes[tid] = key
        y = {'id': 'room:' + r['id'], 'name': r['name'], 'outline': r['outline'], 'floor': r['floor']}
        if 'slope' in r:
            y['slope'] = r['slope']
        y['ceiling'] = r['ceiling']
        y['theme'] = tid
        y['ambient'] = S[si]['min_ambient_light_level']
        if 'slope' not in r and not r.get('nobands') and 'bands' not in r and abs(main_floor(si) - r['floor']) < 2:
            b = sector_bands(si, r['floor'], r['ceiling'])
            b = [(t, h) for t, h in b if not t.startswith(DOORISH) and t in TS]
            if len(b) > 1 and 'wall' not in r:
                r['bands'] = [{'height': h, 'surface': surf(t)} for t, h in b[:-1]]
                w = b[-1][0]
        if 'walls' not in r and 'bands' not in r and not r.get('nobands'):
            ws = []
            for i in range(len(r['outline'])):
                t = edge_texture(r, i)
                if t and t != w and t in TS:
                    ws.append({'wall': i, 'surface': surf(t)})
            if ws:
                r['walls'] = ws
        key = (w, f, c)
        tid = 'theme:%s_%s_%s' % key
        themes[tid] = key
        y['theme'] = tid
        for k in ('walls', 'bands', 'pillars', 'platforms', 'levels', 'ceiling_levels', 'flights', 'parapets', 'beams'):
            if k in r:
                y[k] = r[k]
        n = r.get('notes', '')
        y['notes'] = ('Sector %d. ' % si) + n if n else 'Sector %d.' % si
        rooms.append(y)
    tl = []
    for tid, (w, f, c) in sorted(themes.items()):
        tl.append({'id': tid, 'wall': surf(w), 'floor': surf(f), 'ceiling': surf(c)})
    out['themes'] = tl
    out['defaults'] = {'theme': tl[0]['id'], 'ambient': 21}
    out['rooms'] = rooms
    ops = []
    used = set()
    for o in OPEN:
        A, B = RB[o['a']]['outline'], RB[o['b']]['outline']
        L, bp = best_pair(A, B)
        if bp is None:
            print('NO PAIR', o['a'], o['b'])
            continue
        i, j, lo, hi, gap = bp
        po, al, ow, _ = frame(A, i)
        c = (o['at'][0] - po[0]) * al[0] + (o['at'][1] - po[1]) * al[1]
        dperp = (o['at'][0] - po[0]) * ow[0] + (o['at'][1] - po[1]) * ow[1]
        if not (-2 <= dperp <= gap + 2 and lo - 2 <= c <= hi + 2):
            print('WRONG WALL PAIR', o['a'], o['b'], 'at', o['at'], 'edge', A[i], 'gap', gap, 'perp', dperp, 'c', c, lo, hi)
        oid = 'open:' + (o.get('id') or (o['a'].split('_', 1)[0] + '_' + o['b']))
        if o['a'] == 'hall_lower' or o['a'] == 'hall_upper':
            oid = 'open:' + (o.get('id') or ('hall_' + o['b']))
        if oid in used:
            oid += '_2'
        used.add(oid)
        y = {'id': oid, 'from': 'room:' + o['a'], 'to': 'room:' + o['b']}
        w = o['w']
        if w != 'full':
            if w + 32 > L:
                print('narrowed', oid, w, '->', L - 32)
                w = int(L - 32)
            al_ = (c - lo) / (hi - lo) if hi > lo else 0.5
            y['along'] = round(min(1, max(0, al_)), 3)
        y['width'] = w
        y['height'] = o['h']
        if o['sill']:
            y['sill'] = o['sill']
        if o.get('notes'):
            y['notes'] = o['notes']
        o['oid'] = oid
        o['gap'] = gap
        ops.append(y)
    out['openings'] = ops
    out['notes'] = ("The Control Center of MM6 (sci-fi.blv) in the original's own frame. Room ids carry the "
                    "original's sector number (s23_generator is sector 23). Written from measurements of the "
                    "original's sectors; see NOTES.md for what could not be said.")
    yaml.safe_dump(out, open(L4 + '/rooms.yml', 'w'), default_flow_style=None, sort_keys=False, width=100000)
    if 'write_objects' in globals():
        write_objects()
    print(len(rooms), 'rooms', len(ops), 'openings', len(tl), 'themes')


if __name__ == '__main__':
    main()
