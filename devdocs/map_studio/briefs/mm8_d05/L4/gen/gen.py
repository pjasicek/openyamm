#!/usr/bin/env python3
"""Writes the mm8_d05 (Abandoned Temple) rebuild project from measured data. Run, then oymap fmt."""
import yaml, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
L4 = '/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm8_d05/L4'
rooms = []; openings = []; RB = {}
def T(name, size=(128, 128), **kw):
    d = {'texture': name, 'size': list(size)}; d.update(kw); return d
def R(x0, x1, y0, y1): return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
def room(id, outline, floor, ceiling, theme=None, **kw):
    r = {'id': 'room:' + id, 'outline': outline, 'floor': floor, 'ceiling': ceiling}
    if theme: r['theme'] = 'theme:' + theme
    r.update(kw); rooms.append(r)
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    RB[id] = (min(xs), max(xs), min(ys), max(ys)); return r
def rect(id, x0, x1, y0, y1, floor, ceiling, theme=None, **kw): return room(id, R(x0, x1, y0, y1), floor, ceiling, theme, **kw)
def opn(id, a, b, c=None, width='full', height='full', along=None, **kw):
    """opening between rect-ish rooms a and b; c = centre coordinate along the shared wall"""
    o = {'id': 'open:' + id, 'from': 'room:' + a, 'to': 'room:' + b, 'width': width, 'height': height}
    if along is None and c is not None:
        A = RB[a]; B = RB[b]
        if B[3] <= A[2]: s0, s1 = max(A[0], B[0]), min(A[1], B[1]); along = (c - s0) / (s1 - s0)      # south
        elif B[2] >= A[3]: s0, s1 = max(A[0], B[0]), min(A[1], B[1]); along = (s1 - c) / (s1 - s0)    # north
        elif B[0] >= A[1]: s0, s1 = max(A[2], B[2]), min(A[3], B[3]); along = (c - s0) / (s1 - s0)    # east
        else: s0, s1 = max(A[2], B[2]), min(A[3], B[3]); along = (s1 - c) / (s1 - s0)                # west
    if along is not None and abs(along - 0.5) > 1e-6: o['along'] = round(along, 4)
    o.update(kw); openings.append(o); return o

# ---------------------------------------------------------------- themes
themes = [
 {'id': 'theme:pyramid', 'wall': T('t65c02'), 'floor': T('t65c03'), 'ceiling': T('t65c02'),
  'notes': "The entrance hall under the pyramid (sectors 14, 15, 20): t65c02 blocks on walls and the sloped roof, t65c03 floor."},
 {'id': 'theme:tunnel', 'wall': T('t6502b'), 'floor': T('t6502b'), 'ceiling': T('t6502b'),
  'notes': "Rough rock of the winding tunnel (sectors 2, 3) and the lake cave (18): t6502b everywhere, t6502c patches not drawn."},
 {'id': 'theme:hall', 'wall': T('t65b02'), 'floor': T('t65b03'), 'ceiling': T('t65b04'),
  'notes': "The cut-stone halls, stairs and corridors (sectors 1, 5 to 13, 19): t65b02 walls, t65b03 floor, t65b04 ceiling."},
 {'id': 'theme:false_floor', 'wall': T('t65a02'), 'bands': [{'height': 640, 'surface': T('t65b02')}, {'height': 704, 'surface': T('t65o11a', (128, 64))}], 'floor': T('t65b03'), 'ceiling': T('t65a04'),
  'notes': "Sector 8, the hall of the false floor: t65b02 walls below the walkway's level, a t65o11a course 64 high at the level of the floor, t65a02 above it, t65a04 ceiling."},
 {'id': 'theme:stair', 'wall': T('t65b02'), 'floor': T('t65b14h2', (64, 128)), 'ceiling': T('t65b04'),
  'notes': "The stairs of sectors 6, 9, 10 and 19: treads t65b14h2 (t65b14h in 10 and 19), risers t65b14v."},
 {'id': 'theme:alcove', 'wall': T('t65b04'), 'floor': T('t65b03'), 'ceiling': T('t65b04'), 'notes': "The four button alcoves of sector 1: t65b04 on walls and ceiling."},
 {'id': 'theme:crusher', 'wall': T('t65b02'), 'bands': [{'height': 144, 'surface': T('t65a02')}, {'height': 208, 'surface': T('t65b11a', (128, 64))}], 'floor': T('t65c02'), 'ceiling': T('t65b02m'),
  'notes': "Sector 11, the room of the retracting floor: t65b02 walls, t65b02m ceiling (and floor plates)."},
 {'id': 'theme:maze', 'wall': T('t65a01', (128, 256)), 'floor': T('t65a03'), 'ceiling': T('t65a04c'), 'reveal': T('t65c02'),
  'door': T('t65a05bl', (128, 256)),
  'notes': "The button maze (sectors 22 to 32): t65a01 panelled walls 256 high, t65a03 floor, t65a04c ceiling, t65c02 in the door passages, door leaves t65a05bl (the original's leaf is t65a05bl and t65a05br side by side, one face 256 wide: a door has one surface). The original marks each doorway with one panel 128 wide beside it, t65a06 by a left door and t65a07 by a right one, and sets a t65a12 plate behind each pair of buttons; single panels on a wall cannot be said."},
 {'id': 'theme:sanctum', 'wall': T('t65b02t'), 'bands': [{'height': 256, 'surface': T('t65a01', (128, 256))}], 'floor': T('t65c02'), 'ceiling': T('t65a04b'),
  'notes': "Sectors 16 and 17, the great hall of the four spitting pedestals: t65c02 floor, t65a04b ceiling, t65a01 panels 256 high with a t65b02t course above them."},
]

# ---------------------------------------------------------------- the pyramid hall (sectors 14, 15)
PYR_CEIL = int(os.environ.get('PYR_CEIL', 2432))
room('pyramid', R(-5248, -2624, -3584, 1024),
     944, PYR_CEIL, 'pyramid', name='Pyramid hall',
     levels=[
       {'outline': R(-4176, -3984, -320, -128), 'floor': 1328},
       {'outline': R(-2896, -2704, -320, -128), 'floor': 1616},
       {'outline': R(-3328, -2672, -1664, -1408), 'floor': 1920},
     ],
     flights=[
       {'from': [-4080, -1792], 'to': [-4080, -319], 'width': 192, 'steps': 24, 'sides': 32},
       {'from': [-3985, -224], 'to': [-2895, -224], 'width': 192, 'steps': 18, 'sides': 32},
       {'from': [-2800, -319], 'to': [-2800, -1409], 'width': 192, 'steps': 19, 'sides': 32},
     ],
     notes="Sectors 14 and 15 as one room: a hall 4608 square under a pyramid roof. The original's roof slopes from the floor line (944) at all four walls up to a flat top at 2432; a sloped ceiling cannot be said, so the ceiling is flat at the top's height. In the middle stands the stair tower: three flights round a square (944 to 1328 north, to 1616 east, to 1904 south) to a platform at 1920. The original goes on from that platform by three ramps (to 2048, 2304, 2432) round a smaller square to a second platform at 2432 directly above the first, where the party arrives; a platform above a platform cannot be said in one room, so the tower stops at 1920 and the party arrives there. ")
rect('well', -2624, -1792, -1456, -1232, 944, PYR_CEIL, 'pyramid', name='Stairwell',
     slope={'to': 560, 'toward': 'east', 'steps': 12},
     notes="In the original a hole in the hall's floor (768 by 256): twelve steps down east from 944 to 560 and a landing, open to the hall above on all sides, leading into the tunnel that runs back under the hall's floor. A floor opening onto a room below cannot be said; drawn as a stair room of the hall's height with walls on both long sides, open to the hall at its head.")
rect('pyr_mid', -1792, -640, -1456, -1232, 944, PYR_CEIL, 'pyramid', name='Hall floor over the tunnel',
     notes="The strip of the hall's floor east of the stairwell, which the tunnel passes under: the hall's floor in the original, a room of its own here only because the stairwell is.")
opn('pyr_well', 'pyramid', 'well')
rect('pyr_e_n', -2624, -640, -1216, 1024, 944, PYR_CEIL, 'pyramid', name='Pyramid hall, north-east', notes="Sector 14 north of the stairwell: part of the one hall, open to room:pyramid along its whole west side.")
rect('pyr_e_s', -2624, -640, -3584, -1472, 944, PYR_CEIL, 'pyramid', name='Pyramid hall, south-east', notes="Sector 14 south of the stairwell: part of the one hall.")
opn('pyr_en', 'pyramid', 'pyr_e_n'); opn('pyr_es', 'pyramid', 'pyr_e_s')
opn('pyr_mid_n', 'pyr_mid', 'pyr_e_n'); opn('pyr_mid_s', 'pyr_mid', 'pyr_e_s')
# ---------------------------------------------------------------- tunnel (sectors 2, 3)
# vertical cuts (x, centre y, half height, floor) then the elbow, then horizontal cuts (y, centre x, half width, floor)
TV = [(-1792, -1344, 128, 560), (-1560, -1380, 150, 528), (-1340, -1600, 170, 480), (-1100, -1740, 135, 440), (-832, -1728, 160, 384), (-560, -1690, 140, 345)]
TH = [(-1470, -380, 150, 345), (-1220, -200, 160, 280), (-1060, 0, 165, 225), (-860, 64, 130, 180), (-640, 64, 128, 160)]
def tunnel():
    ids = []
    for i in range(len(TV) - 1):
        (x0, c0, h0, f0), (x1, c1, h1, f1) = TV[i], TV[i + 1]
        id = 'tunnel_%d' % (len(ids) + 1); ids.append(id)
        room(id, [[x0, c0 - h0], [x1, c1 - h1], [x1, c1 + h1], [x0, c0 + h0]], f0, f0 + 256, 'tunnel', name='Tunnel ' + id[-1], slope={'to': f1, 'toward': 1})
    (x, c, h, f) = TV[-1]; (y, cx, hw, _) = TH[0]
    ids.append('tunnel_bend')
    room('tunnel_bend', [[x, c - h], [cx + hw, y], [cx - hw, y], [x, c + h]], f, f + 256, 'tunnel', name='Tunnel bend')
    for i in range(len(TH) - 1):
        (y0, c0, h0, f0), (y1, c1, h1, f1) = TH[i], TH[i + 1]
        id = 'tunnel_%d' % (len(ids)); ids.append(id)
        room(id, [[c0 + h0, y0], [c1 + h1, y1], [c1 - h1, y1], [c0 - h0, y0]], f0, f0 + 256, 'tunnel', name='Tunnel ' + id[7:], slope={'to': f1, 'toward': 1})
    for a, b in zip(ids, ids[1:]): opn(a + '_' + b[7:], a, b)
    rooms[-len(ids)]['notes'] = "Sectors 2 and 3, the rock tunnel from the stairwell (560) under the pyramid hall to the trap hall's south door (160): about 256 wide, falling all the way, winding south-east then north. Drawn as nine straight ramps and a level bend, because a path room cannot slope, a sloped room must be convex and its two ends parallel; the original's walls and ceiling are irregular rock (ceiling 250 to 450 above the floor) and its floor is uneven."
tunnel()
opn('well_tunnel', 'well', 'tunnel_1')


# ---------------------------------------------------------------- sector 1: the hall of the sinking stones
rect('trap_hall', -512, 640, -640, 1408, 0, 480, 'hall', name='Hall of the sinking stones',
     levels=[
       {'outline': R(-128, 256, -640, -384), 'floor': 160, 'surface': T('t65b04'), 'edge': T('t65o02c')},
       {'outline': R(-512, -320, -640, -384), 'floor': 32, 'surface': T('t65b04'), 'edge': T('t65o02c')},
       {'outline': R(448, 640, -640, -384), 'floor': 32, 'surface': T('t65b04'), 'edge': T('t65o02c')},
       {'outline': R(-128, 256, 1280, 1408), 'floor': 160, 'surface': T('t65b04'), 'edge': T('t65o02c')},
     ],
     flights=[
       {'from': [-321, -512], 'to': [-127, -512], 'width': 256, 'steps': 4},
       {'from': [449, -512], 'to': [255, -512], 'width': 256, 'steps': 4},
     ],
     notes="Sector 1. The party comes in from the tunnel onto a dais 160 high against the south wall (ramps down each side to corner blocks 32 high; drawn as four steps each). Six blocks stand 160 high between the dais and a landing 160 high at the north door: stepping stones that sink to 32 when stepped on (lifts here, see objects.yml). On the floor below, four side alcoves open when the floor is first touched; a button in each raises, in order, the four steps of two short stairs beside the north landing. Ceiling 480.")
for nm, x0, x1, y0, y1 in (('alc_sw', -800, -544, -128, 128), ('alc_nw', -800, -544, 768, 1024), ('alc_se', 672, 928, -128, 128), ('alc_ne', 672, 928, 768, 1024)):
    rect(nm, x0, x1, y0, y1, 0, 256, 'alcove', name='Button alcove')
    opn('hall_' + nm, 'trap_hall', nm, height=240)
opn('tunnel_hall', 'tunnel_9', 'trap_hall', height=256)
# ---------------------------------------------------------------- sector 5
rect('corr5', -64, 192, 1408, 2432, 160, 416, 'hall', name='Corridor of the two closets', notes="Sector 5: a corridor north from the trap hall's landing; a closet behind a rising slab on each side, each with a chest on a pedestal; the stair down leaves east at its north end.")
opn('hall_corr5', 'trap_hall', 'corr5', height=256)
rect('clo5_w', -384, -128, 1664, 1920, 160, 416, 'hall', name='West closet', platforms=[{'at': [-304, 1792], 'size': [96, 96], 'rise': 96}])
rect('clo5_e', 256, 512, 1664, 1920, 160, 416, 'hall', name='East closet', platforms=[{'at': [432, 1792], 'size': [96, 96], 'rise': 96}])
opn('corr5_clo_w', 'corr5', 'clo5_w', height=240); opn('corr5_clo_e', 'corr5', 'clo5_e', height=240)
# ---------------------------------------------------------------- sectors 6, 7, 9
rect('stair6', 320, 1344, 2176, 2432, 160, 416, 'stair', name='Long stair down', slope={'to': -352, 'toward': 'east', 'steps': 16, 'riser': T('t65b14v', (128, 32))},
     notes="Sector 6: sixteen steps of 32 down east, 160 to -352, 192 wide between two raking kerbs in a corridor 256 wide. The original's ceiling slopes with the stair (256 above it all the way); a ceiling that follows a stair cannot be said, so the ceiling is level at the head's height.")
opn('corr5_stair6', 'corr5', 'stair6')
rect('room7', 1472, 2112, 2176, 2432, -352, -96, 'hall', name='Door room', notes="Sector 7: at the foot of the stair. East, a double door into the hall of the false floor; north, a block that sinks into the floor (door 6) closes the way back up from under that hall.")
opn('stair6_room7', 'stair6', 'room7')
rect('room7n', 1600, 1856, 2560, 2816, -352, -96, 'hall', name='Head of the return stair')
opn('room7_n', 'room7', 'room7n', height=255)
rect('stair9a', 512, 1472, 2560, 2816, -352, -96, 'stair', name='Return stair, upper flight', slope={'to': -864, 'toward': 'west', 'steps': 16, 'riser': T('t65b14v', (128, 32))},
     notes="Sector 9, the way back up from under the false floor: sixteen steps down west (-352 to -864) beside the long stair, a landing, a turn back east under the long stair, six more steps down to -1056 and a corridor east under sectors 6 and 7 into the lower hall. Ceilings in the original follow the stairs.")
opn('room7n_stair9a', 'room7n', 'stair9a')
rect('land9', 64, 448, 2176, 2816, -864, -608, 'hall', name='Return stair, landing')
opn('stair9a_land9', 'stair9a', 'land9')
rect('stair9b', 448, 832, 2176, 2432, -864, -608, 'stair', name='Return stair, lower flight', slope={'to': -1056, 'toward': 'east', 'steps': 6, 'riser': T('t65b14v', (128, 32))})
opn('land9_stair9b', 'land9', 'stair9b')
rect('corr9', 832, 2240, 2176, 2432, -1056, -800, 'hall', name='Corridor under the stair')
opn('stair9b_corr9', 'stair9b', 'corr9')
# ---------------------------------------------------------------- sector 8
PED = lambda x, y: {'at': [x, y], 'size': [96, 96], 'rise': 96, 'surface': T('t6502b')}
WALK = [[2240, 2176], [2368, 2112], [2496, 1984], [2624, 1728], [2880, 1536], [3264, 1536], [3520, 1792], [3520, 1984], [3328, 2304], [3264, 2624], [3328, 2688], [3456, 2752], [3584, 2624], [3648, 2432], [3712, 2304], [3776, 2112], [3968, 1984], [4096, 2048], [4224, 2176], [4288, 2176], [4288, 2432], [4224, 2432], [4096, 2368], [4032, 2304], [3968, 2368], [3840, 2752], [3648, 3008], [3392, 3072], [3136, 3008], [2976, 2816], [2976, 2496], [3136, 2176], [3200, 1920], [3136, 1856], [3008, 1856], [2816, 2016], [2688, 2304], [2560, 2432], [2368, 2496], [2240, 2432]]
def thin(poly, tol):
    import math
    P = list(poly); ch = True
    while ch:
        ch = False
        for i in range(len(P)):
            a, b, c = P[i - 1], P[i], P[(i + 1) % len(P)]
            l = math.hypot(c[0] - a[0], c[1] - a[1])
            d = abs((c[0] - a[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (c[1] - a[1])) / l
            if d < tol and b[0] not in (2240, 4288): del P[i]; ch = True; break
    return P
WALK = thin(WALK, 60)
INSET = int(os.environ.get('INSET', 48))
SLAB = lambda o: {'outline': [[min(max(x, 2240 + INSET), 4288 - INSET), y] for x, y in o], 'base': 688, 'rise': 16, 'surface': T('t65o11a', (128, 64)), 'top_surface': T('t65b03')}
LV = lambda o: {'outline': o, 'floor': -352, 'edge': T('t65o11a', (128, 64))}
rect('hall8', 2240, 4288, 1344, 3264, -1056, -32, 'false_floor', name='Hall of the false floor',
     levels=[LV(R(2240, 2240 + INSET, 2176, 2432)), LV(R(4288 - INSET, 4288, 2176, 2432)), LV(R(2240, 2496, 1344, 1600)), LV(R(4032, 4288, 1344, 1600)), LV(R(2240, 2496, 3008, 3264)), LV(R(4032, 4288, 3008, 3264))],
     platforms=[PED(2368, 1472), PED(4160, 1472), PED(2368, 3136), PED(4160, 3136),
                SLAB(WALK[:7] + WALK[17:]), SLAB(WALK[6:18])],
     notes="Sector 8: a hall 2048 by 1920 and 1024 high. At the height of the doors (-352) the original has a floor right across it, but only a winding walkway from the west door to the east door (and a square 256 in each corner, each with a chest on a pedestal) is solid: the rest lets the party fall to the true floor 704 below, from where the only way out is the corridor west and the return stair (sector 9); the third fall marks the walkway's faces (event 451). Drawn as the tall room with the walkway as a slab 16 thick hanging at the doors' height (two platforms end to end, because a platform's outline may have 20 corners; the outline thinned from the original's 40 points to %d; its two ends stop 48 short of the doors' walls, because a platform must stand 32 clear of the walls, and a pier 48 deep, a level, carries the floor from each door to the slab; the original has no piers) and the corner squares as levels (solid down to the floor, which the original's are not); the false floor itself, which looks solid and is not, cannot be said and is missing, so the walkway is plain to see." % len(WALK))
opn('room7_hall8', 'room7', 'hall8', height=254)
rect('corr9_jog', 1984, 2240, 2448, 2704, -1056, -800, 'hall', name='Jog (not in the original)',
     notes="Not in the original, where the corridor under the stair (sector 9) runs straight into the hall's west wall at -1056, directly below the door at -352. The build refuses two openings one above the other in one wall (they 'overlap'), so the corridor's last 256 are turned north into this jog and enter the hall 272 further north.")
opn('corr9_jog', 'corr9', 'corr9_jog', height=256)
opn('jog_hall8', 'corr9_jog', 'hall8', height=256)
# ---------------------------------------------------------------- sector 10
room('tri10', [[4288, 2176], [4544, 2432], [4288, 2432]], -352, -96, 'hall', name='Head of the slanting stair')
opn('hall8_tri10', 'hall8', 'tri10', height=256)
room('stair10', [[4288, 2176], [4672, 1792], [4928, 2048], [4544, 2432]], -352, -96, 'stair', name='Slanting stair', slope={'to': -640, 'toward': 1, 'steps': 8, 'riser': T('t65b14v', (128, 32))},
     notes="Sector 10: a stair turned 45 degrees, six steps of 48 in the original (-352 to -640); eight steps of 36 here, because a step may rise 40 at most.")
opn('tri10_stair10', 'tri10', 'stair10')
room('corr11', [[4672, 1792], [5056, 1792], [5936, 2304], [5936, 2560], [5824, 2560], [4928, 2048]], -640, -384, 'hall', name='Slanting corridor')
opn('stair10_corr11', 'stair10', 'corr11')
# ---------------------------------------------------------------- sector 11 (and 21)
rect('crusher', 6016, 7296, 1792, 3072, -656, -128, 'crusher', name='Room of the retracting floor',
     notes="Sectors 11 and 21. In the original the floor is four plates (at -656 and -704) that meet over a funnel (from -736 at the walls down to -1008) round a pit 768 square (sector 21, an unseen floor at -1023 that kills). Using the far door shuts both doors and draws the plates back into the walls at 10 units a second; eight lit panels on the walls (two a wall, 128 by 64, 144 above the plates) must all be put out before the plates are gone; a timer then stops the plates and opens the doors. A floor that draws back cannot be said: the floor is solid at the plates' height, the pit is not built, and the panels are switches that unlock the far door.")
opn('corr11_crusher', 'corr11', 'crusher', height=239)
room('corr12', [[7376, 2304], [7632, 2304], [8128, 2816], [7872, 3072], [7376, 2560]], -640, -384, 'hall', name='Bent corridor, west')
opn('crusher_corr12', 'crusher', 'corr12', height=239)
room('corr13', [[7872, 3072], [8128, 2816], [8896, 2816], [9392, 2304], [9728, 2304], [9728, 2560], [9648, 2560], [9152, 3072]], -640, -384, 'hall', name='Bent corridor, east')
opn('corr12_corr13', 'corr12', 'corr13')
# ---------------------------------------------------------------- sectors 16, 17
TPED = lambda x, y: {'at': [x, y], 'size': [256, 256], 'rise': 160, 'top_size': [128, 128], 'surface': T('t65b04')}
rect('sanctum', 9728, 13824, 1280, 3584, -640, -256, 'sanctum', name='Great hall',
     platforms=[TPED(10368, 1920), TPED(10368, 2944), TPED(13184, 1920), TPED(13184, 2944), {'at': [11776, 2432], 'size': [128, 128], 'rise': 128, 'top_size': [42, 42], 'surface': T('t65b04')}],
     notes="Sectors 16 and 17 as one room: a hall 4096 by 2304, 384 high. Four tapering pedestals (256 square at the foot, 160 high) carry stone heads that spray poison when the floor round them is walked on; a smaller stand in the middle carries the Prophecies of the Sun and throws fire bolts. A hidden niche in the north wall (128 wide, behind a sliding panel that opens when a patch of floor is crossed) holds a chest.")
opn('corr13_sanctum', 'corr13', 'sanctum', height=256)
# ---------------------------------------------------------------- sectors 19, 20
rect('s19a', 13824, 14208, 2176, 2560, -640, -384, 'hall', name='Foot of the back stair')
opn('sanctum_s19a', 'sanctum', 's19a', 2432, width=256, height=256)
rect('stair19a', 13952, 14208, 1152, 2176, -640, 128, 'stair', name='Back stair, first flight', slope={'to': -128, 'toward': 'south', 'steps': 16, 'riser': T('t65b14v', (128, 32))},
     notes="Sector 19: two flights of sixteen steps (192 wide between kerbs), south from -640 to a landing at -128, then back north to 384, the second flight above the great hall's east end. Ceilings in the original follow the flights.")
opn('s19a_stair19a', 's19a', 'stair19a')
rect('land19', 13568, 14208, 768, 1152, -128, 128, 'hall', name='Back stair, landing')
opn('stair19a_land19', 'stair19a', 'land19')
rect('stair19b', 13568, 13824, 1152, 2176, -128, 640, 'stair', name='Back stair, second flight', slope={'to': 384, 'toward': 'north', 'steps': 16, 'riser': T('t65b14v', (128, 32))})
opn('land19_stair19b', 'land19', 'stair19b')
rect('top19', 13568, 13824, 2176, 2304, 384, 640, 'hall', name='Head of the back stair')
opn('stair19b_top19', 'stair19b', 'top19')
room('s20', [[12736, 2048], [13504, 2048], [13504, 2304], [13824, 2304], [13824, 2560], [13504, 2560], [13504, 2816], [12736, 2816], [12736, 2560], [12672, 2560], [12672, 2304], [12736, 2304]],
     384, 896, 'pyramid', name='Back door chamber',
     notes="Sector 20, above the great hall: a chamber 768 square with a recess east (to the stair) and a shallow one west holding the back door out. Its roof in the original is a small pyramid (384 to 896); flat here.")
opn('top19_s20', 'top19', 's20', height=256)
# ---------------------------------------------------------------- the maze (sectors 22 to 32)
HALLS = {'h22': (7360, 9664, 1536, 2048), 'h23a': (6976, 8256, 768, 1280), 'h23b': (6336, 8128, 0, 512), 'h24a': (6144, 7040, -768, -256), 'h24b': (5952, 6848, -1536, -1024),
         'h25': (7232, 8512, -768, -256), 'h26a': (7040, 7936, -1536, -1024), 'h26b': (6848, 7744, -2304, -1792), 'h27a': (8768, 10048, 704, 1216), 'h27b': (8576, 9472, -832, -320),
         'h28a': (9344, 10240, -64, 448), 'h28b': (9536, 10432, -832, -320), 'h29a': (8384, 10048, -1600, -1088), 'h29b': (8192, 9088, -2368, -1856), 'h29c': (9344, 10240, -2368, -1856),
         'h30': (7232, 9664, -3136, -2624), 'h31': (7040, 7936, -3904, -3392), 'h32': (8192, 9088, -3904, -3392)}
MZF, MZC = -640, -384
rect('c22n', 8384, 8640, 2560, 2816, MZF, MZC, 'hall', name='Maze entry, outer')
opn('corr13_c22n', 'corr13', 'c22n', height=256)
rect('c22s', 8384, 8640, 2048, 2496, MZF, MZC, 'hall', name='Maze entry, inner')
opn('c22', 'c22n', 'c22s', height=255)
for k, (x0, x1, y0, y1) in HALLS.items():
    rect(k, x0, x1, y0, y1, MZF, MZC, 'maze', name='Maze hall ' + k[1:])
rooms[-len(HALLS)]['notes'] = "Sectors 22 to 32, the button maze: eighteen halls 512 deep and 256 high, each with two buttons in its south wall and two doorways beside them, a left one and a right one. One button raises the left door and shuts the right, the other the reverse. Some doorways lead on to the next hall (through a wall 256 thick); the others are closets 128 deep where a wrong choice summons a serpent man. Hall 29a has two pairs of buttons and four doorways, hall 30 three pairs and six. The way through ends in the lake cave."
opn('c22s_h22', 'c22s', 'h22', height=256)
rect('c27', 8896, 9152, -320, 640, MZF, -400, 'maze', name='Long passage', notes="The one long doorway of the maze (sector 27): 1024 from hall 27a's left door to hall 27b.")
room('cave_in', [[9280, -4416], [9664, -4416], [9664, -4160], [9536, -4160], [9536, -3200], [9280, -3200]], MZF, -400, 'hall', name='Passage to the cave')
MDOORS = {}   # original door number -> (opening id, from hall, kind)
doors = json.load(open(HERE + '/doors.json'))
def hall_with(side, y, xa, xb):
    for k, (x0, x1, y0, y1) in HALLS.items():
        if (y0 if side == 's' else y1) == y and x0 <= xa and xb <= x1: return k
for D in doors:
    n = D['door_id']
    if not 52 <= n <= 93: continue
    xa, xb = min(D['x_offsets']), max(D['x_offsets']); ya, yb = min(D['y_offsets']), max(D['y_offsets'])
    a = hall_with('s', yb, xa, xb); c = (xa + xb) / 2
    if n == 56: b = 'c27'; opn('d56_b', 'c27', 'h27b', height=240)
    elif n == 89: b = 'cave_in'
    elif yb - ya >= 256: b = hall_with('n', ya, xa, xb)
    else:
        b = 'clo%d' % n
        rect(b, xa, xb, yb - 192, yb - 64, MZF, -400, 'maze', name='Closet of door %d' % n)
    assert a and b, (n, a, b)
    opn('d%d' % n, a, b, c, width=('full' if b.startswith('c') else 256), height=240)
    MDOORS[n] = ('open:d%d' % n, a, b)
# ---------------------------------------------------------------- sector 18: the lake cave
room('cave', [[10752, -5120], [11136, -5120], [11712, -4992], [12096, -4736], [12224, -4416], [12224, -4160], [12096, -3840], [11712, -3584], [11136, -3456], [10752, -3456], [10176, -3584], [9792, -3840], [9664, -4160], [9664, -4416], [9792, -4736], [10176, -4992]],
     -640, -200, 'tunnel', name='Lake cave',
     ceiling_levels=[{'outline': [[10000, -4600], [10500, -4850], [11400, -4850], [11900, -4600], [11900, -3980], [11400, -3730], [10500, -3730], [10000, -3980]], 'ceiling': 160}],
     levels=[
       {'outline': [[10000, -4144], [11936, -4144], [11900, -3900], [11650, -3700], [11100, -3580], [10800, -3580], [10250, -3700], [10000, -3900]], 'floor': -896, 'surface': T('wtrtyl'), 'edge': T('t65b02')},
       {'outline': [[10000, -4432], [10000, -4680], [10250, -4880], [10800, -5010], [11100, -5010], [11650, -4890], [11900, -4680], [11936, -4432]], 'floor': -896, 'surface': T('wtrtyl'), 'edge': T('t65b02')},
       {'outline': R(9936, 11952, -4400, -4176), 'floor': -656, 'surface': T('t65b03')},
     ],
     flights=[
       {'from': [10950, -3836], 'to': [10950, -3579], 'width': 256, 'steps': 8},
       {'from': [10950, -4754], 'to': [10950, -5011], 'width': 256, 'steps': 8},
     ],
     notes="Sector 18: a rock cave about 2560 by 1920 under a dome (the rock roof rises from about 250 above the shore at the walls to 930 above it in the middle; two flat heights here: -200 round the rim, 160 over the middle). A lake fills it, its bed at -896 (256 below the shore, with banks that slope so the party can wade in and out; a sunken level has upright sides, so each half of the lake has one flight of eight steps up to the shore instead), crossed west to east by a paved causeway 256 wide at -704 with a ramp at each end (16 below the shore here, with a kerb of shore 16 wide each side, because levels may not touch) that ends at a stand against the east wall where the Prophecies of the Snake lies. A niche in the north wall behind a rising slab holds another book.")
opn('cave_in_cave', 'cave_in', 'cave', height=240)
rect('cave_n', 10752, 11136, -3424, -3200, -640, -384, 'tunnel', name='Niche behind the slab')
opn('cave_niche', 'cave', 'cave_n', height=240)


# ================================================================ objects and wiring
import re
obj = {'format': 0, 'start': {'room': 'room:pyramid', 'at': [-3008, -1536], 'facing': 'n',
       'notes': "The original arrives on the tower's upper platform at 2464, 544 above this one (see room:pyramid)."}}
D = []; LIFTS = []; SW = []; CH = []; SP = []; LI = []; EX = []; PH = []; EV = []; VARS = []
def pin(pt, poly):
    x, y = pt; ins = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): ins = not ins
    return ins
def room_at(x, y, z):
    best = None
    for r in rooms:
        if not pin((x + 0.01, y + 0.01), r['outline']): continue
        lo = min([r['floor'], r.get('slope', {}).get('to', r['floor'])] + [l['floor'] for l in r.get('levels', [])])
        if lo - 300 <= z <= r['ceiling'] + 8:
            if best is None or r['ceiling'] - lo < best[1]: best = (r, r['ceiling'] - lo)
    return best[0] if best else None
def door(n, opening, kind='slide_up', speed=100, thickness=64, **kw):
    d = {'id': 'door:d%s' % n, 'opening': 'open:' + opening, 'kind': kind, 'state': 'closed', 'speed': speed, 'thickness': thickness}; d.update(kw); D.append(d); return d['id']
def ev(id, preset, source, **kw):
    e = {'id': 'evt:' + id, 'preset': preset, 'source': source}; e.update(kw); EV.append(e); return e
# ---- single doors
for n, o, k, sp, th, note in ((1, 'c22', 'slide_up', 50, 64, "Door 1, the maze's entry: a double door whose leaves change texture when opened (event 11)."),
                              (3, 'corr5_clo_w', 'slide_up', 50, 64, None), (4, 'corr5_clo_e', 'slide_up', 50, 64, None),
                              (5, 'room7_hall8', 'slide_up', 75, 64, None),
                              (6, 'room7_n', 'slide_down', 75, 128, "Door 6: a block 128 thick that fills the doorway from the floor and sinks into it."),
                              (108, 'corr11_crusher', 'slide_up', 75, 64, None), (109, 'crusher_corr12', 'slide_up', 75, 64, None),
                              (114, 'cave_niche', 'slide_up', 75, 32, None)):
    kw = {'notes': note} if note else {}
    kw['surface'] = T({1: 't65a05al', 5: 't65b05l', 108: 't65a05bl', 109: 't65a05bl'}.get(n, 't65b02'), (128, 256) if n in (1, 5, 108, 109) else (128, 128))
    id = door(n, o, k, sp, th, **kw)
    if n != 109: ev('door_%d' % n, 'door', id, title='Door', action='open')
for i, nm in enumerate(('alc_sw', 'alc_nw', 'alc_se', 'alc_ne')):
    id = door('2_' + nm[4:], 'hall_' + nm, 'slide_up', 50, 32, notes="One of the four slabs of door record 2. In the original all four rise together the first time the hall's floor is touched (event 12, bound to the floor's faces); a door opened by walking somewhere cannot be said, so each opens when used.")
    ev('door_2_' + nm[4:], 'door', id, title='Door', action='open')
# ---- the sinking stones and the rising steps (door records 94 to 99, 101 to 107)
for n, at, size, sp in ((94, [64, -128], [384, 128], 30), (95, [160, 192], [288, 144], 40), (96, [-192, 448], [128, 256], 45), (97, [160, 704], [288, 144], 50), (98, [448, 1024], [128, 128], 60), (99, [0, 1024], [256, 128], 70)):
    LIFTS.append({'id': 'lift:stone_%d' % n, 'room': 'room:trap_hall', 'at': at, 'size': size, 'travel': 160, 'speed': sp, 'state': 'up', 'surface': T('t65o02c'),
                  'notes': "Door record %d: a stepping stone, up (160) when the map is entered; it sinks at %d units a second when stepped on (events 506 to 511, bound to its top) and all six rise again when the south dais is stepped on (event 512). The original sinks to 32, not to the floor, and stones 95 and 97 are turned about 27 degrees; a lift has no base height and no facing." % (n, sp)})
    ev('stone_%d' % n, 'switch', 'lift:stone_%d' % n, closes=['lift:stone_%d' % n], notes="Original: runs when the stone is stepped on. Here the stone must be used (clicked).")
STEPV = ['steps_1', 'steps_2', 'steps_3', 'steps_4']; VARS += STEPV
for i, (h, xw, xe) in enumerate(((128, -160, 288), (96, -224, 352), (64, -288, 416), (32, -352, 480))):
    ids = []
    for side, x in (('w', xw), ('e', xe)):
        id = 'lift:step%d_%s' % (i + 1, side); ids.append(id)
        LIFTS.append({'id': id, 'room': 'room:trap_hall', 'at': [x, 1344], 'size': [64, 128], 'travel': h, 'speed': 75, 'state': 'down', 'surface': T('t65o02c')})
    alc = ('alc_nw', 'alc_ne', 'alc_sw', 'alc_se')[i]
    sid = 'switch:step_%d' % (i + 1)
    SW.append({'id': sid, 'room': 'room:' + alc, 'wall': 'west' if alc.endswith('w') else 'east', 'height': 144, 'size': [32, 32], 'off': T('t65a13a', (32, 32)), 'on': 't65a13a',
               'notes': "Door record %d, a button 48 proud of the wall that goes in when pressed; it raises the two steps %d high (door record %d) beside the north landing." % (100 + 2 * i, h, 101 + 2 * i)})
    e = ev('step_%d' % (i + 1), 'switch', sid, title='Button', opens=ids, once=True, sets={'map_var': STEPV[i]})
    if i: e['condition'] = {'map_var': STEPV[i - 1]}; e['locked_text'] = 'The button will not move'
# ---- the maze: doors 52 to 93, buttons 10 to 51 (events 20 to 61)
doortex = {}
for Dr in doors:
    n = Dr['door_id']
    if 52 <= n <= 93:
        o, a, b = MDOORS[n]
        gap = 64 if b.startswith('c') else HALLS[a][2] - HALLS[b][3]     # the wall's thickness: the original's door is a plug as deep as its doorway
        door(n, o[5:], 'slide_up', 100, gap, surface=T('t65a05bl', (128, 256)))
lua_src = open('/home/pjasicek/github/OpenYAMM/assets_dev/worlds/mm8/events/maps/d05.lua').read()
flow = {}
for l in open(HERE + '/flow.txt'):
    l = l.strip().rstrip(',').lstrip('[').rstrip(']')
    if l: e = json.loads(l); flow[e['event']] = e
for Dr in doors:
    n = Dr['door_id']
    if not 10 <= n <= 51: continue
    e = n + 10
    xa, xb = min(Dr['x_offsets']), max(Dr['x_offsets']); y = Dr['y_offsets'][0]
    h = hall_with('s', y - 16, xa, xb); x0, x1, _, _ = HALLS[h]
    sid = 'switch:b%d' % n
    SW.append({'id': sid, 'room': 'room:' + h, 'wall': 'south', 'along': round(((xa + xb) / 2 - x0) / (x1 - x0), 4), 'height': 96, 'size': [32, 32], 'off': T('t65a13a', (32, 32)), 'on': 't65a13a'})
    eff = max(flow[e]['paths'], key=lambda p: len(p['effects']))['effects']
    opens = []; closes = []; summon = None
    for f in eff:
        m = re.match(r'door (\d+) (open|close)', f)
        if m and 52 <= int(m.group(1)) <= 93: (opens if m.group(2) == 'open' else closes).append('door:d' + m.group(1))
        if f.startswith('SummonMonsters'): summon = f
    w = ev('button_%d' % n, 'switch', sid, title='Button')
    if opens: w['opens'] = opens
    if closes: w['closes'] = closes
    if summon:
        m = re.search(r'RegisterEvent\(%d, "Button", function\(\)\s+if not IsAtLeast\(MapVar\((\d+)\), 1\) then\s+(evt\.SummonMonsters\([^)]*\))' % e, lua_src)
        var, call = m.group(1), m.group(2)
        var = int(var) + 40      # the build numbers this project's named variables from 0; the original's 21 to 45 are kept clear of them
        w['lua'] = "if not IsAtLeast(MapVar(%d), 1) then\n    %s\n    SetValue(MapVar(%d), 1)\nend" % (var, call, var)
        w['notes'] = "A wrong button: the first press summons a serpent man in the closet it opens."
SW[-1]['notes'] = "Door records 10 to 51 are the maze's 42 buttons (32 square, 96 above the floor, 16 proud of the south wall of their hall; pressing moves one in and its partner out). Events 20 to 61."
# ---- the retracting-floor room: eight panels, two doors
PANV = ['panel_%d' % i for i in range(1, 9)]; VARS += PANV
for i, (wall, al) in enumerate((('west', (3072 - 2880) / 1280), ('north', (7296 - 6208) / 1280), ('north', (7296 - 7104) / 1280), ('east', (2880 - 1792) / 1280),
                                ('east', (1984 - 1792) / 1280), ('south', (7104 - 6016) / 1280), ('south', (6208 - 6016) / 1280), ('west', (3072 - 1984) / 1280))):
    sid = 'switch:panel_%d' % (i + 1)
    SW.append({'id': sid, 'room': 'room:crusher', 'wall': wall, 'along': round(al, 4), 'height': 176, 'size': [128, 64], 'off': T('t65b11b', (128, 64)), 'on': 't65b11c'})
    ev('panel_%d' % (i + 1), 'switch', sid, title='Button', once=True, sets={'map_var': PANV[i]},
       notes="Events 102 to 109. In the original the panels are dark (t65b11b) until the trap starts, then lit (t65b11c, each with a light); pressing one puts it out, pressing again lights it, and map variable 12 counts the dark ones. Here a panel is dark until pressed and lit after, once.")
ev('door_109', 'door', 'door:d109', title='Leave the Abandoned Temple', action='open', condition={'all': [{'map_var': v} for v in PANV]},
   notes="Events 63, 64 and the timer event 110. In the original using this door (or the near door from inside) starts the trap: both doors shut, the floor draws back, the panels light; when all are dark the timer stops the floor and opens both doors. Here: the door opens once all eight panels have been pressed.")
# ---- chests
def chest(i, room_, at, facing, note=None):
    c = {'id': 'chest:c%d' % i, 'room': 'room:' + room_, 'at': at, 'facing': facing}
    if note: c['notes'] = note
    CH.append(c); ev('chest_%d' % i, 'chest', c['id'], title='Chest')
chest(0, 'clo5_w', [-304, 1792], 'e', "Event 81. Stands on a pedestal 96 high in the original.")
chest(1, 'clo5_e', [432, 1792], 'w', "Event 82.")
chest(2, 'hall8', [2368, 3136], 'e', "Event 83: on the north-west corner pedestal."); chest(3, 'hall8', [4160, 3136], 'w', "Event 84.")
chest(4, 'hall8', [2368, 1472], 'e', "Event 85."); chest(5, 'hall8', [4160, 1472], 'w', "Event 86.")
chest(19, 'sanctum', [10368, 3540], 's', "Event 100: in the original inside a niche 128 wide and 20 deep in the north wall, behind a panel (door record 115) that slides down 127 when a patch of floor at the hall's middle is crossed (event 453). Here it stands in the open against the wall.")
# ---- spawns, lights
scene = json.load(open(HERE + '/scene.json'))
for i, sp in enumerate(scene['spawns']):
    x, y, z = sp['position']['x'], sp['position']['y'], sp['position']['z']
    r = room_at(x, y, z)
    if not r: print('spawn without room', x, y, z); continue
    SP.append({'id': 'spawn:s%02d' % i, 'room': r['id'], 'at': [x, y], 'slot': sp['index'], 'radius': sp['radius']})
orig = json.load(open(HERE + '/orig.json'))['map']
for i, li in enumerate(orig['lights']):
    x, y, z = li['position']
    if li['attributes'] & 8: continue   # the eight panel lights start switched off (event 63 turns them on): a light has no state
    r = room_at(x, y, z)
    if not r: print('light without room', x, y, z); continue
    LI.append({'id': 'light:l%02d' % i, 'room': r['id'], 'at': [x, y], 'height': max(8, z - r['floor']), 'radius': li['radius'], 'color': li['color']})
# ---- exits
EX.append({'id': 'exit:top', 'room': 'room:pyramid', 'wall': 'south', 'along': round((-3008 + 5248) / 2624, 4), 'size': [256, 256], 'surface': T('solid01', (16, 16)), 'to': 'exit:pyramid_top',
           'notes': "Event 501. In the original a black doorway 256 square standing free on the south edge of the tower's top platform (y -1728, z 2464); an exit must be on a room's wall, so it is on the hall's south wall below."})
EX.append({'id': 'exit:back', 'room': 'room:s20', 'wall': 9, 'size': [224, 256], 'surface': T('solid01', (16, 16)), 'to': 'exit:back_door', 'notes': "Event 502: the black doorway in the west recess."})
ev('exit_top', 'exit', 'exit:top', title='Leave the Abandoned Temple'); ev('exit_back', 'exit', 'exit:back', title='Leave the Abandoned Temple')
# ---- placeholders: what the vocabulary has no object for
def ph(id, room_, at, what, size, note):
    PH.append({'id': 'ph:' + id, 'room': 'room:' + room_, 'at': at, 'stands_for': what, 'size': size, 'notes': note})
ph('tower_top', 'pyramid', [-3008, -1536], "The upper turn of the stair tower: three ramps (1920 to 2048 north, to 2304 east, to 2432 south) round a square 640 by 640 to a second platform at 2432 directly above the platform at 1920, with the arrival step (2464) and the exit doorway on its south edge.", [640, 640, 544], "A platform above a platform in one room.")
ph('false_floor', 'hall8', [3264, 2304], "False floor: a floor of t65b03 right across the hall at -352, level with the walkway and not solid (the original's faces are flagged untouchable), with its underside (t65b04) seen from below; events 451 and 452 count the falls and after the third mark the walkway's faces.", [2048, 1920, 16], "No floor that is seen and not solid; no event run by stepping on a floor.")
ph('pit', 'crusher', [6656, 2432], "The funnel and the killing pit under the four floor plates (door records 110 to 113, each drawn 639 into its wall at 10 units a second; event 101 on the funnel and pit floor kills the party).", [768, 768, 500], "No floor that draws back, no hole in a floor, no event on a floor.")
for i, (x, y) in enumerate(((13184, 2944), (13184, 1920), (10368, 1920), (10368, 2944))):
    ph('spitter_%d' % (i + 1), 'sanctum', [x, y], "Trap head on the pedestal: casts four Poison Sprays outward (skill 10, expert) from 96 off the pedestal's centre, 176 above the floor, each time the floor round it is stepped on (event %d)." % (111 + i), [128, 128, 96], "No event run by stepping on a floor, no spell cast from a point.")
ph('fire_stand', 'sanctum', [11776, 2432], "The Prophecies of the Sun (item 626) lying on the middle stand, and the stand's trap: four Fire Bolts from its corners when the floor across the hall's middle is crossed (event 115).", [128, 128, 128], "No item lying in the map, no floor event.")
ph('niche_book', 'cave_n', [10944, -3328], "A second item 626 lying on the niche's floor.", [32, 32, 32], "No item lying in the map.")
ph('snake_book', 'cave', [12192, -4288], "The Prophecies of the Snake (item 186 in the original's object list) on a stand 96 by 160, 144 high, against the east wall at the causeway's end.", [96, 160, 144], "No item lying in the map; the stand would touch the wall, which a platform may not.")
ph('simon', 'pyramid', [-3008, -1536], "Map events run without the player using anything: on entering, Simon Templar (NPC 264) speaks unless quest bit 403 is set (event 1) and the retracting-floor room is reset (event 2); on leaving, quest bit 218 is set if the party carries item 626 (event 6) and quest bit 136 set / 135 cleared if it carries item 652 (event 10).", [64, 64, 192], "wiring.yml has no events run on entering or leaving the map.")

def write():
    y = lambda o: yaml.safe_dump(o, sort_keys=False, width=100000, default_flow_style=None)
    open(L4 + '/rooms.yml', 'w').write(y({'format': 0, 'themes': themes, 'defaults': {'theme': 'theme:hall', 'ambient': 27}, 'rooms': rooms, 'openings': openings}))
    obj.update({'doors': D, 'lifts': LIFTS, 'lights': LI, 'switches': SW, 'chests': CH, 'spawns': SP, 'exits': EX, 'placeholders': PH})
    open(L4 + '/objects.yml', 'w').write(y(obj))
    open(L4 + '/wiring.yml', 'w').write(y({'format': 0, 'variables': VARS, 'events': EV}))
if __name__ == '__main__':
    write()
