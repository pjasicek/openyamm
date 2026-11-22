"""XD-17 Shangri-La: the places of the L1 plan, one source for the brief, the drawings and the concepts (A5, 2026-11-20).

Map units, x east, y north, z up; the datum (0, 0, 0) is the well in the middle of the court. The valley lies in the
same compass as X7 (its cleft faces west on X7, so the back passage leaves the valley westward; Mount Firestone's
summit stands east-north-east, over the valley's north-east rim).

The source (xeen maze0049, aaze0049): a green court of 5 x 9 tiles in a ring of houses, the well in the court's middle
(7, 8), the way in at the south (7, 0, "Leave Shangri-La?"), the pyramid at the court's north end (7, 14).
"""
import math

GRID = 512

# ---------------------------------------------------------------- the valley
# The valley floor's edge, the foot of the black cliffs (clockwise from the west).
FLOOR = [(-6400, 512), (-6016, 2816), (-4864, 4224), (-2560, 4864), (0, 5120), (2304, 4992), (4608, 4480),
         (6016, 3328), (6528, 1280), (6400, -1280), (5888, -3328), (4352, -4608), (1792, -5120), (-1024, -5248),
         (-3584, -4864), (-5376, -3584), (-6272, -1536)]
# The cliff crest: the floor's edge pushed out by CREST_OUT, at the crest height of each side (by bearing from 0, 0).
CREST_OUT = 1792
CREST = [(0, 2560), (45, 3200), (70, 3328), (100, 2944), (150, 2816), (200, 2560), (250, 2304), (290, 2432),
         (330, 2560), (360, 2560)]   # (bearing in degrees from east, counter-clockwise; height)
# Mount Firestone's summit, a backdrop over the north-east rim (question 3): apex, base radius, apex height.
SUMMIT = {'at': (8448, 7168), 'radius': 4096, 'height': 5632, 'crater': 640}


def crest_height(x, y):
    a = math.degrees(math.atan2(y, x)) % 360
    for (a0, h0), (a1, h1) in zip(CREST, CREST[1:]):
        if a0 <= a <= a1:
            t = (a - a0) / (a1 - a0)
            return h0 + t * (h1 - h0)
    return CREST[0][1]


# ---------------------------------------------------------------- spaces (zones of the valley floor)
# id: (name, centre, extent [w, d], floor, purpose)
ZONES = {
    'zone:court': ('The court', (0, 0), (2560, 3584), 0,
                   "The source's green court: a lawn ringed by a flagstone walk, the +1 level well in its middle, "
                   "Lacey grazing by it; every lane of the valley starts at its corners."),
    'zone:first_street': ('The first square', (-1088, -3584), (3200, 2304), [-64, 0],
                          "From the cave mouth up to the court: a paved square with Tavern Xanadu on its west side "
                          "and Arm and Hammer's long forge on its east, both doors on the square; the first houses a "
                          "visitor passes."),
    'zone:west_terrace': ('The west terrace', (-3968, -256), (2560, 4096), [256, 384],
                          "Two low terraces under the west cliff: the Public Library's colonnade (256) and the Earth "
                          "Temple, half sunk into the cliff foot (384); the signature camera on the library steps."),
    'zone:north_terrace': ('The pyramid terrace', (0, 4032), (4608, 1536), 256,
                           "A stone terrace against the north cliff, steps up from the court's north end: the "
                           "travel pyramid in its middle, Murray's villa on its east end."),
    'zone:east_shore': ('The pool and the falls', (4480, 2048), (3584, 3328), [-32, 0],
                        "A cold pool at the east cliff's foot, fed by a white fall from a notch 1,700 up the cliff; "
                        "a stream leaves it south along the cliff foot. Princess Pilar's pavilion on the north shore, "
                        "the Light guild's white tower west of it."),
    'zone:orchard': ('The orchard', (4352, -2304), (2560, 2560), [0, 64],
                     'Fruit trees in uneven rows between the east lane and the stream; Stumpy stands in the middle; '
                     "Elona's house at its west edge."),
    'zone:north_west': ('The north-west lane', (-3584, 2816), (4096, 1792), [0, 128],
                        "Maurice's house by the court, then the lane along the cliff foot to the back passage."),
}
VALLEY = ('room:valley', 'The valley', (0, 0), (12928, 10368))

# ---------------------------------------------------------------- buildings and doors (A4's towns/xd17.yml)
# id: dict(name, house, door (A4's id), studio (the indoor door id, see request to A4), at, size [x, y], floor, faces,
#          height, kind, look). `doors` lists (A4 id, house, studio id, point) for a building with more than one door.
BUILDINGS = [
    dict(id='building:tavern_xanadu', name='Tavern Xanadu', service='tavern', at=(-2432, -3072), size=(1152, 896),
         floor=0, height=640, look='two storeys, timber and white plaster, a broad porch on the street, the sign of '
         'a domed palace', doors=[('door:tavern_xanadu', 4353, 'door:tavern_xanadu', (-1856, -3072), 'e')]),
    dict(id='building:arm_and_hammer', name='Arm and Hammer', service='weapon and armour shop', at=(320, -3072),
         size=(896, 1536), floor=0, height=512, look='a long stone forge, a chimney between two doors on the '
         'street, one sign of a raised arm, one of a hammer', doors=[
             ('door:arm_and_hammer_arms', 4351, 'door:arm_and_hammer_arms', (-128, -3456), 'w'),
             ('door:arm_and_hammer_armour', 4365, 'door:arm_and_hammer_armour', (-128, -2688), 'w')]),
    dict(id='building:earth_temple', name='Earth Temple', service='temple', at=(-5440, 768), size=(1152, 1152),
         floor=384, height=768, look='squat dark stone, a turfed roof, half sunk into the west cliff foot',
         doors=[('door:earth_temple', 4352, 'door:earth_temple', (-4864, 768), 'e')]),
    dict(id='building:guild_light', name="Shangri-La Wizard's Guild", service='Light guild', at=(2560, 2816),
         size=(896, 896), floor=0, height=1536, look='a round white tower with a gilded dome, the valley\'s '
         'tallest roof', doors=[('door:guild_light', 4354, 'door:guild_light', (2560, 2368), 's')]),
    dict(id='building:an_education', name='An Education', service='residence (Jack Alltrades, Learning GM)',
         at=(-2112, 1216), size=(1024, 768), floor=0, height=576, look='a schoolhouse with a bell cote',
         doors=[('door:an_education', 4355, 'door:an_education', (-1600, 1216), 'e')]),
    dict(id='building:public_library', name='Public Library', service='residence (three Grandmasters)',
         at=(-3776, -1280), size=(1024, 1408), floor=256, height=704, look='a pale stone hall, a colonnade and '
         'broad steps facing the court', doors=[('door:public_library', 4356, 'door:public_library', (-3264, -1280),
                                                 'e')]),
    dict(id='building:maurice', name="Maurice's House", service='residence (hint: the sword)', at=(-2240, 2304),
         size=(768, 704), floor=0, height=512, look='a narrow house with a tall gable',
         doors=[('door:maurice', 4357, 'door:maurice', (-1856, 2304), 'e')]),
    dict(id='building:alexander', name="Alexander's House", service='residence (Body Building GM; hint: the Sphinx)',
         at=(1952, 1664), size=(768, 640), floor=0, height=512, look='a stout house with a yard of weights',
         doors=[('door:alexander', 4358, 'door:alexander', (1568, 1664), 'w')]),
    dict(id='building:pilar', name="Princess Pilar's Pavilion", service='residence (Dodging GM; hint: the key)',
         at=(4480, 3456), size=(768, 768), floor=0, height=576, look='a small garden house on the pool, white walls, '
         'a low dome and a door (D-50: a house, not an open gazebo)', doors=[('door:pilar', 4359, 'door:pilar', (4480, 3072), 's')]),
    dict(id='building:benedict', name="Benedict's House", service='residence (Unarmed GM; the crystal joke)',
         at=(-2368, -1792), size=(768, 640), floor=0, height=512, look='a crooked little house, a weathervane '
         'that points the wrong way', doors=[('door:benedict', 4360, 'door:benedict', (-1984, -1792), 'e')]),
    dict(id='building:elona', name="Elona's House", service='residence (Bow GM; hint: the password)',
         at=(2560, -3104), size=(768, 640), floor=0, height=512, look='a house hung with maps and a weathered '
         'pack', doors=[('door:elona', 4361, 'door:elona', (2560, -2784), 'n')]),
    dict(id='building:murray', name="Murray's Villa", service='residence (Staff GM)', at=(1792, 4288),
         size=(1280, 896), floor=256, height=640, look='the valley\'s biggest house, a portico and urns',
         doors=[('door:murray', 4362, 'door:murray', (1792, 3840), 's')]),
    dict(id='building:sally', name="Psychic Sally's", service='residence (the seer; hint: the mirror)',
         at=(1952, -1280), size=(640, 640), floor=0, height=576, look='a round hut, a starry painted roof',
         doors=[('door:sally', 4363, 'door:sally', (1632, -1280), 'w')]),
    dict(id='building:martok', name="Martok's Lodge", service='residence (Dark Elf GM)', at=(-3712, -3328),
         size=(768, 640), floor=0, height=448, look='a log lodge, a bench by the door',
         doors=[('door:martok', 4364, 'door:martok', (-3712, -3008), 'n')]),
]
SERVICES = {'building:tavern_xanadu', 'building:arm_and_hammer', 'building:earth_temple', 'building:guild_light'}

# ---------------------------------------------------------------- devices, people, ways
WELL = (0, 0)
PYRAMID = {'at': (0, 4032), 'base': 896, 'height': 704, 'floor': 256, 'portal': (0, 3584), 'arrival': (0, 3200)}
POOL = {'at': (5120, 2304), 'radii': (1152, 768), 'level': -32}
FALL = {'lip': (6400, 2432), 'z': 1728, 'facing': 'w'}          # the white fall on the east cliff, pouring west
STREAM = [(5120, 1536), (5504, 0), (5568, -1792), (5376, -3456)]   # to a sinkhole at the south-east cliff foot
ORCHARD_TREES = [(x, y) for x in (3584, 4096, 4608, 5120) for y in (-3328, -2816, -2304, -1792, -1280)
                 if (x, y) not in ((4608, -2304), (5120, -3328))]
STUMPY = (4608, -2304)              # monster 11916 Xeen Stumpy (MM7 treant), move stand, peaceful, NPC 4718 (D-50)
LACEY = (448, -384)                 # monster 11915 Xeen Lacey (MM8 unicorn), wanders, peaceful, NPC 4719 (D-50)
PYRAMID_ARRIVAL = (0, 3200, 256)    # entrance:d6_pyramid facing south (1536): Xeen.PyramidArrivals.shangrila
# The cave mouth: the cool passage's end (XD-16) in the south cliff; its throat runs 768 into the rock.
MOUTH = (-1280, -5248)
XD16_ARRIVAL = (-1280, -4736)       # entrance:xd16_way, facing north into the valley (the map's start)
MOUTH_EXIT = (-1280, -5888)         # the throat's back: the exit preset (D-24) -> XD-16 entrance:xd17_way
# The back passage: a slot of rock open to the sky from the north-west cliff, 2,048 west to the inside of X7's cleft.
PASSAGE = [(-5632, 3328), (-6656, 3584), (-7680, 3712)]
PASSAGE_WIDTH = 384
X7CLEFT_ARRIVAL = (-7296, 3648)     # entrance:x7_cleft, facing east toward the valley
PASSAGE_EXIT = (-7680, 3712)        # the rockfall: exit preset; first xd17.cleft_opened, then X7 entrance:xd17_cleft
X7_CLEFT_POINT = (4096, 8192, 2496)  # X7's entrance:xd17_cleft (installed xeen_x7.studio.yml), facing west (1024)
CRYSTAL = (-832, -5216)             # question 5 (a): in the cliff face east of the cave mouth, at eye height
# The lanes (polylines), each a walking line that must stay clear of props.
LANES = {
    'lane:first_street': [(-1280, -4736), (-1280, -2304), (-1024, -1792)],
    'lane:court_walk': [(-1280, -1792), (1280, -1792), (1280, 1792), (-1280, 1792), (-1280, -1792)],
    'lane:west': [(-1280, 0), (-2816, -256), (-3264, -1280)],
    'lane:temple_steps': [(-2816, -256), (-3584, 768), (-4864, 768)],
    'lane:north_west': [(-1280, 1792), (-1600, 2048), (-1600, 2944), (-3584, 2944), (-5632, 3328)],
    'lane:maurice': [(-1600, 2304), (-1856, 2304)],
    'lane:pyramid_steps': [(0, 1792), (0, 3200), (0, 3584)],
    'lane:north_east': [(1280, 1792), (1792, 2176), (2560, 2176), (2560, 2368)],
    'lane:murray': [(1792, 2176), (1792, 3840)],
    'lane:pool': [(1280, 1024), (2560, 1280), (3712, 1792), (3712, 3008), (4480, 3008)],
    'lane:alexander': [(1280, 1664), (1568, 1664)],
    'lane:east': [(1280, -1792), (2560, -2240), (2560, -2784)],
    'lane:orchard': [(2560, -2240), (3584, -2240)],
    'lane:sally': [(1280, -1280), (1632, -1280)],
    'lane:benedict': [(-1280, -2048), (-1984, -1792)],
    'lane:martok': [(-1280, -2368), (-3712, -2368), (-3712, -3008)],
    'lane:first_square': [(-1856, -3072), (-1280, -3072), (-1280, -3456), (-128, -3456), (-128, -2688), (-1280, -2688)],
}

# ---------------------------------------------------------------- cameras (MU-4)
EYE = 170
CAMERAS = {
    'arrival': {'at': (-1280, -4736), 'z': -64 + EYE, 'yaw': 78, 'pitch': 4, 'fov': 80,
                'what': "Out of the cool passage's cave mouth, facing north: the first street between the tavern "
                        "and the forge, the court and the well, the pyramid on its terrace against the north cliff, "
                        "the white fall on the east cliff, Firestone's summit over the north-east rim."},
    'signature': {'at': (-3008, -1408), 'z': 384 + EYE, 'yaw': 28, 'pitch': 3, 'fov': 80,
                  'what': "From the library steps across the valley to the east-north-east: the court with the well "
                          "and Lacey, the houses, Pilar's pavilion on the pool, the white fall, the guild's gilded "
                          "dome, the ring of black cliffs and, over them, Firestone's black summit."},
}


def doors():
    """Every door: (A4 id, house id, studio id, point, facing, building)."""
    out = []
    for b in BUILDINGS:
        for d in b['doors']:
            out.append(d + (b,))
    return out


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])
