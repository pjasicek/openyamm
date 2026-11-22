"""XD-17 Shangri-La: the L2-L4 layout (A5, 2026-11-21), the approved L1 (`places.py`, D-50 applied) fitted to what the
studio builds. places.py stays the L1 record; this module takes it and moves what had to move.

What moved, and why (each by 128-768):
- The terraces are parts of the valley floor's TIN (a paved top, a stone bank about 1.5 steep, a ramp of about 0.4 to
  0.5): the west terrace became two (the library at 256, the temple at 384, 192 apart), the pyramid terrace keeps
  (0, 3200, 256) for D-50's entrance:d6_pyramid on its top.
- Buildings moved off the banks and ramps: the library (-4096, -1280), the temple (-5120, 704), Benedict (-2368, -1920),
  An Education (-2112, 1344), Murray's villa (1792, 4160), the Light guild's tower (3200, 2560), Pilar's house
  (4480, 3712, D-50: a small house with a door, clear of the pool's north shore), the tavern 64 shallower.
- The lanes run on the compass axes (the floor's lines are cut on a 64 grid), each 64 clear of every bank and wall.
- The pool shrank to radii (1024, 704) so its rim stays on the flat floor; the stream leaves its south rim.
Map units, x east, y north; the datum is the well.
"""
import copy

import places as P
from places import *  # noqa: F401,F403  (what L2 does not move)

GRID = P.GRID
FLOOR = P.FLOOR
CREST = P.CREST
crest_height = P.crest_height
SUMMIT = P.SUMMIT
dist = P.dist

MOVED = {
    'building:public_library': dict(at=(-4096, -1280), door=(-3584, -1280)),
    'building:earth_temple': dict(at=(-5120, 704), door=(-4544, 704)),
    'building:benedict': dict(at=(-2368, -1920), door=(-1984, -1920)),
    'building:an_education': dict(at=(-2112, 1344), door=(-1600, 1344)),
    'building:murray': dict(at=(1792, 4160), door=(1792, 3712)),
    'building:guild_light': dict(at=(3200, 2560), door=(3200, 2112)),
    'building:pilar': dict(at=(4480, 3712), door=(4480, 3328)),
    'building:tavern_xanadu': dict(size=(1152, 832)),
}

BUILDINGS = []
for _b in copy.deepcopy(P.BUILDINGS):
    m = MOVED.get(_b['id'], {})
    if 'at' in m:
        _b['at'] = m['at']
    if 'size' in m:
        _b['size'] = m['size']
    if 'door' in m:
        d = _b['doors'][0]
        _b['doors'] = [(d[0], d[1], d[2], m['door'], d[4])]
    BUILDINGS.append(_b)
SERVICES = P.SERVICES

# How each building is built (studio masses): wall height, roof rise, textures. 'gable' roofs ride the long axis;
# 'tower' and 'hut' are octagons with tapering roof tiers; 'dome' a low tiered dome on a square house.
STYLE = {
    'building:tavern_xanadu': dict(kind='gable', wall=512, roof=288, walls='7hhr1bs2', roof_tex='7hhr1rf',
                                   door='7hhr1d', sign='7sgtvrn'),
    'building:arm_and_hammer': dict(kind='gable', wall=384, roof=256, walls='chb1', roof_tex='hhm1rf', door='hhm3d',
                                    sign={'door:arm_and_hammer_arms': 'sgweapon',
                                          'door:arm_and_hammer_armour': '7sgarm'}),
    'building:earth_temple': dict(kind='gable', wall=448, roof=160, walls='ch1b1', roof_tex='6grastyl', door='hhm3d',
                                  sign='sgtempl'),
    'building:guild_light': dict(kind='tower', wall=1152, walls='7tws1f', roof_tex='ygtemprf', door='7hhr1d',
                                 sign='sglight'),
    'building:an_education': dict(kind='gable', wall=512, roof=256, walls='hhm2b2', roof_tex='hhm2rf', door='hhm2d'),
    'building:public_library': dict(kind='gable', wall=512, roof=256, walls='7tws1f', roof_tex='xtslate',
                                    door='7hhr1d', colonnade=True),
    'building:maurice': dict(kind='gable', wall=512, roof=320, walls='hhm3b', roof_tex='hhm3rf', door='hhm3d'),
    'building:alexander': dict(kind='gable', wall=512, roof=224, walls='hhm1b1', roof_tex='hhm1rf', door='hhm1d'),
    'building:pilar': dict(kind='dome', wall=512, walls='7hhr1bs2', roof_tex='xtslate', door='7hhr1d'),
    'building:benedict': dict(kind='gable', wall=512, roof=256, walls='hhp1b', roof_tex='hhp2rf', door='hhp1d'),
    'building:elona': dict(kind='gable', wall=512, roof=224, walls='hhm2b1', roof_tex='hhm2rf', door='hhm2d'),
    'building:murray': dict(kind='gable', wall=512, roof=288, walls='7hhr1b', roof_tex='7hhr1rf', door='7hhr1d'),
    'building:sally': dict(kind='hut', wall=512, walls='hhm3b', roof_tex='gtemprf', door='hhm3d'),
    'building:martok': dict(kind='gable', wall=320, roof=224, walls='gstrrf', roof_tex='hhm1rf', door='hhm1d'),
}

# ---------------------------------------------------------------- terraces (TIN: top, bank, ramp)
# top [x0, y0, x1, y1] at `h`; the bank `bank` wide all round (0 at its foot); the ramp on side `side` centred `at`
# along that side, `width` wide and `length` long, from the top's edge down to the floor.
TERRACES = {
    'terrace:library': dict(top=(-4864, -2112, -3264, -512), h=256, bank=192, side='e', at=-1280, width=512,
                            length=640),
    'terrace:temple': dict(top=(-5824, 64, -4288, 1344), h=384, bank=256, side='e', at=704, width=512, length=768),
    'terrace:pyramid': dict(top=(-1280, 3072, 2496, 4672), h=256, bank=192, side='s', at=0, width=640, length=640),
}

# ---------------------------------------------------------------- lanes and the first square (rectangles)
# Each [x0, y0, x1, y1]; the floor between them is cut on a 64 grid. 'square' is paved (gtempflr), lanes gravel.
SQUARE = [(-1792, -4096, -256, -2240)]
LANES = {
    'lane:first_street': [(-1472, -5184, -1088, -4096), (-1408, -2240, -1152, -1664)],
    'lane:court_walk': [(-1408, -1920, 1408, -1664), (-1408, 1664, 1408, 1920), (-1408, -1664, -1152, 1664),
                        (1152, -1664, 1408, 1664)],
    'lane:west': [(-2624, -1408, -1408, -1152)],
    'lane:benedict': [(-1920, -2048, -1408, -1792)],
    'lane:temple': [(-3520, 576, -1408, 832)],
    'lane:an_education': [(-1536, 1216, -1408, 1472)],
    'lane:north_west': [(-1792, 1664, -1408, 1920), (-1792, 1920, -1536, 3584), (-5248, 3328, -1792, 3584)],
    'lane:pyramid': [(-128, 1920, 128, 2368)],
    'lane:pool': [(1408, 1024, 3968, 1280), (3712, 1280, 3968, 3264), (3968, 3072, 4736, 3264)],
    'lane:guild': [(3072, 1280, 3328, 2048)],
    'lane:east': [(1408, -1920, 2688, -1664), (2432, -2720, 2688, -1920)],
    'lane:orchard': [(2688, -2304, 3584, -2048)],
    'lane:martok': [(-3840, -2592, -1856, -2368), (-3840, -2944, -3584, -2592)],
}

# ---------------------------------------------------------------- devices, people, ways
WELL = P.WELL
PYRAMID = {'at': (0, 4032), 'base': 896, 'height': 704, 'floor': 256, 'portal': (0, 3584), 'arrival': (0, 3200)}
POOL = {'at': (5120, 2304), 'radii': (1024, 704), 'level': -40}
STREAM = [(5120, 1600), (5440, 0), (5504, -1792), (5376, -3264)]
STREAM_WIDTH = 160
FALL = P.FALL
# The fall decoration (D-50 Q7): S's `xeen_waterfall`; added by the generator when the world binds that model.
FALL_MODEL = 'xeen_waterfall'
# S's placement (level_generation/decorations/xeen_waterfall_claude/README.md): the model's origin is the cliff-foot
# point under the notch, on the floor (z 0); facing 200 degrees is the pour, along the ray from the notch to the foot.
# The model is fitted to this rock: moving the notch, the foot or the pool means S rebuilds it (fit_xd17.py).
FALL_AT = (6272, 2304)
FALL_FACING = 200
ORCHARD_TREES = [t for t in P.ORCHARD_TREES]
STUMPY = P.STUMPY
LACEY = P.LACEY
LACEY_NPC, STUMPY_NPC = 4719, 4718
LACEY_MONSTER, STUMPY_MONSTER = 11915, 11916
PYRAMID_ARRIVAL = P.PYRAMID_ARRIVAL
# The cave mouth: the foot of a sheer bluff in the south cliff; the throat runs 768 into it.
BLUFF_S = [(-1792, -5248), (-768, -5248)]           # its front on the cliff foot (west, east)
BLUFF_S_SIDES = [(-2176, -6528), (-384, -6528)]     # where its sides bend outward (west, east)
THROAT = (-1472, -6016, -1088, -5280)                # x0, y0, x1, y1 (32 behind the bluff's front: the mouth's depth)
THROAT_CEILING = 448
BLUFF_LINTEL = 704                                   # the south bluff's front: rock over the cave mouth
XD16_ARRIVAL = P.XD16_ARRIVAL
# The back passage: a slot open to the sky behind a sheer bluff in the north-west cliff. It leaves square to the cliff
# foot (the foot runs (9, 11) there, so the passage first runs (-11, 9), north-west, about 900), then bends west to
# the rockfall at x -7,680. Its mouth is centred on the foot at (-5440, 3520), 370 wide.
WEDGE_FRONT = [(-5242, 3762), (-5638, 3278)]         # the wedge's front on the cliff foot (north-east, south-west)
WEDGE_N = [(-5946, 4338), (-7896, 4638)]             # the wedge's north side: bend, then out west (-13, 2)
WEDGE_S = [(-6342, 3854), (-7917, 3809)]             # the wedge's south side, out west (-35, -1)
PASSAGE = [(-5590, 3404), (-5356, 3690), (-6027, 4239), (-7680, 4416), (-7680, 4032), (-6261, 3953)]   # 43 behind the bluff's front
PASSAGE_END_CEILING = 1536
WEDGE_LIP = 640                                      # the gorge's walls at its mouth
X7CLEFT_ARRIVAL = (-7296, 4224)
X7_CLEFT_POINT = P.X7_CLEFT_POINT
CRYSTAL_X = -928                                     # on the bluff's front, east of the mouth, eye height

TOUR = {
    'arrival': dict(at=(-1280, -4736), z=170, yaw=90, pitch=4),
    'signature': dict(at=(-3200, -1600), z=256 + 170, yaw=28, pitch=4),
    'forge_square': dict(at=(-1600, -3900), z=170, yaw=40, pitch=0),
    'pyramid_terrace': dict(at=(-700, 3150), z=256 + 170, yaw=250, pitch=-4),
}


def doors():
    out = []
    for b in BUILDINGS:
        for d in b['doors']:
            out.append(d + (b,))
    return out
