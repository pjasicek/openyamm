"""DD-03 Castle Kalindra (staged): writes the Map Studio briefs L1 to L4 (devdocs/xeen/briefs/dd03/L*) from one place.

gen.py [L1 L2 L3 L4]   (default: all four). Lane A8 (agent:xeen-a8-dd03), phase 3, decider D-26.
Plan frame: x east, y north. Floors: the dungeon -640 (Scraps' kennel -1152), the ground floor 0, the second floor 640,
the third floor 1280. Every room's ceiling stays at least 64 under the floor of any room above it in plan. The party
comes in from D1 through the gate in the west, facing east.

Stages (A3's Xeen.Stages.kalindra): the map is built with every stage gate shut. Load events on the stage qbits open
the gates (door leaves in the shimmer texture xkshimmer that block monsters too) and show the stage's monsters, which
are placed hidden in their own groups (D-18's pattern): stage 1 m19.stage1 111381 (the gate's portcullis; its
monsters are not hidden, since D1's gate refuses the party before stage 1), stage 2 m19.stage2 111382 (the Cloud
Stairs, the second floor), stage 3 m26.stage3 111521 (the dungeon stair), stage 4 m26.stage4 111522 (the upper stair,
the stable yard's phase wall). A stair's leaf is at its foot (its head for the dungeon), and a step plate before it
carries the source's mist line while the stage is not set.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os
import sys
import yaml

R = _REPO_ROOT
OUT = R + '/devdocs/xeen/briefs/dd03'


class Flow(list):
    pass


class FlowDict(dict):
    pass


yaml.add_representer(Flow, lambda d, v: d.represent_sequence('tag:yaml.org,2002:seq', v, flow_style=True))
yaml.add_representer(FlowDict, lambda d, v: d.represent_mapping('tag:yaml.org,2002:map', v, flow_style=True))


def F(*a):
    return Flow(a)


def S(texture, w, h, **kw):
    d = FlowDict(texture=texture, size=F(w, h))
    d.update(kw)
    return d


def dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=120)


# ---------------------------------------------------------------------------------------------------------------------
# Numbers

MAP_ID = 9152
MUSIC = 29
QBITS = {
    'arrived_once': 117320,        # the map's own (provisional block 117320-117359)
    'stage1': 111381,              # m19.stage1 (A3): 5 disks
    'stage2': 111382,              # m19.stage2: 10 disks
    'stage3': 111521,              # m26.stage3: 15 disks
    'stage4': 111522,              # m26.stage4: 20 disks
    'm19_safes': 111383,           # m19.safes_opened (A3's hook sets it)
    'm24_safes': 111483,           # m24.safes_opened
    'm27_crown': 111541,           # m27.crown
}
BIT_QUEENS_BREW = 11304            # player bit, provisional: the Queen's Brew (+2 Personality)
BIT_KNIGHTS_BREW = 11305           # player bit, provisional: the Knight's Brew (+2 Might)
ENERGY_DISK = 12334
CARL_NPC = 5014
CARL_BODY = 364                    # the engine's peaceful Peasant (as Ellinger's body in DD-02, D1's townsfolk)
MIST = "Your foot passes through the stairs as though they were mist. This level is out of phase and inaccessible."

# D1: A6's return point for DD-03's gate (event 123, entrance:dd03_gate): (-9728, -3072, 1664) facing west (game 1024,
# studio 180). The coaches land at kalindra_gate (-9216, -3072, 1664) facing west.
D1_ARRIVAL = [-9728, -3072, 1664]
D1_FACING = 180
START = (-1600, 0)

# ---------------------------------------------------------------------------------------------------------------------
# Textures: the royal kit restored (MM7 Titans' Stronghold 7d09 cream marble t3s2b1 with the knotwork dado t3s2b,
# floors t3s2fl1 and tfb09, ceiling t3s2c, trim 7tws1fa, door t5d1, pillar t3elr, tapestries tap1/tap4/tap7) with
# Kalindra's crest xkkalcrst, banner xkkalban, portcullis xkportc and arrow slit xkarrow; the wings still out of phase
# and the dungeon in MM7 Castle Gryphonheart 7d33 (chb1, dchb1, 7tfb1, tfb2, 7tfb11, 7trimd, the arched oak door pair
# chb1dl/chb1dr); the gate and the yard in Castle Ironfist's white ashlar hcwall/hcwindo over grey flags cstyl; the
# phase walls in A6's xkshimmer (shared with D1's ghost castle, D-26).

MARBLE = S('t3s2b1', 128, 256)
DADO = S('t3s2b', 128, 256)
MFLOOR = S('t3s2fl1', 128, 128)
FLAGS = S('tfb09', 128, 128)
MCEIL = S('t3s2c', 128, 128)
TRIM = S('7tws1fa', 128, 32)
IRON_DOOR = S('t5d1', 128, 256, fit=True)
PILLAR = S('t3elr', 128, 256)
COBBLE = S('chb1', 128, 256)
DCOBBLE = S('dchb1', 128, 256)
CFLOOR = S('7tfb1', 128, 128)
CCEIL = S('tfb2', 128, 128)
DFLOOR = S('7tfb11', 128, 128)
PLANK = S('7trimd', 128, 256)
OAK_L = S('chb1dl', 128, 256, fit=True)
OAK_R = S('chb1dr', 128, 256, fit=True)
ASHLAR = S('hcwall', 128, 256)
WINDOW = S('hcwindo', 128, 256, fit=True)
YFLOOR = S('cstyl', 128, 128)
SHIMMER = S('xkshimmer', 128, 128)
PORTC = S('xkportc', 256, 256, fit=True)
CREST = S('xkkalcrst', 128, 256, fit=True)
BANNER = S('xkkalban', 128, 256, fit=True)
ARROW = S('xkarrow', 128, 256, fit=True)
GATE = S('hclgdr', 256, 256, fit=True)
SIGN = S('sign128', 256, 128, fit=True)
MIRROR = S('xmirror', 128, 128)  # A6's silvered glass, a seamless tile (D-37 (2))
DESK_SIDE = S('deskside', 64, 64)
# A writing desk's top (inkwell, a paper), meant once: only the ledger desk, 256 x 128 at two units a texel (a
# platform's top takes no `fit`; horizontal pictures start at the world grid: the desk's x edge is on it, its y
# edge half a picture off, hence the offset).
DESK_TOP = S('desktop', 128, 64, scale=2, offset=F(0, 32))
BOARD_TOP = S('7trimd', 128, 256)  # plank tops of the tables, the bench and the racks (seamless)
BEDS = S('7t1beds', 256, 64)
TAP = {n: S(n, 128, 256, fit=True) for n in ('tap1', 'tap4', 'tap7')}

THEMES = [
    {'id': 'theme:hall', 'wall': MARBLE, 'bands': [{'height': 256, 'surface': DADO}], 'floor': MFLOOR,
     'ceiling': MCEIL, 'reveal': PILLAR, 'door': OAK_L,
     'notes': "The restored royal halls: MM7 Titans' Stronghold cream marble t3s2b1 over the knotwork dado t3s2b, "
              "marble floor t3s2fl1, ceiling t3s2c (the royal kit's interior)."},
    {'id': 'theme:royal', 'wall': MARBLE, 'floor': FLAGS, 'ceiling': MCEIL, 'reveal': PILLAR, 'door': OAK_L,
     'notes': "The royal rooms and stairs: the cream marble over Castle Harmondale's flags tfb09."},
    {'id': 'theme:wing', 'wall': COBBLE, 'bands': [{'height': 32, 'surface': TRIM}], 'floor': CFLOOR,
     'ceiling': CCEIL, 'reveal': PLANK, 'door': OAK_L,
     'notes': "The wings still out of phase: MM7 Castle Gryphonheart 7d33 brown cobble chb1, flags 7tfb1, "
              "dark ceiling tfb2, the arched oak doors chb1dl/chb1dr."},
    {'id': 'theme:dungeon', 'wall': DCOBBLE, 'floor': DFLOOR, 'ceiling': CCEIL, 'reveal': DCOBBLE, 'door': IRON_DOOR,
     'notes': "The dungeon: 7d33's dark cobble dchb1, dark flags 7tfb11, riveted iron doors t5d1."},
    {'id': 'theme:gate', 'wall': ASHLAR, 'floor': YFLOOR, 'ceiling': CCEIL, 'reveal': PILLAR, 'door': PORTC,
     'notes': "The gate passage and the bell tower: Castle Ironfist's white ashlar hcwall over grey flags cstyl, the "
              "kit's portcullis xkportc."},
    {'id': 'theme:yard', 'wall': ASHLAR, 'floor': YFLOOR, 'ceiling': S('t3s2c', 128, 128, sky=True), 'reveal': PILLAR,
     'door': OAK_L, 'notes': "The stable yard: the white ashlar round grey flags, open to the sky (sky faces)."},
]

# ---------------------------------------------------------------------------------------------------------------------
# Rooms


def rect(x0, y0, x1, y1):
    return [F(x0, y0), F(x1, y0), F(x1, y1), F(x0, y1)]


RECT = {}


def wall_offset(rid, wall, centre, length):
    """Offset of a panel of `length` centred at `centre` (x on north/south walls, y on east/west) along a rectangular
    room's wall, measured from the wall's start corner (counter-clockwise)."""
    x0, y0, x1, y1 = RECT[rid]
    if wall == 'south':
        return centre - length // 2 - x0
    if wall == 'north':
        return x1 - (centre + length // 2)
    if wall == 'east':
        return centre - length // 2 - y0
    if wall == 'west':
        return y1 - (centre + length // 2)
    raise ValueError(wall)


def panel(rid, i, wall, centre, length, bottom, height, surface, notes=None):
    d = {'id': i, 'offset': wall_offset(rid, wall, centre, length), 'length': length, 'bottom': bottom,
         'height': height, 'surface': surface}
    if notes:
        d['notes'] = notes
    return d


LEFT_IS_LOWER = {'north': True, 'south': False, 'east': False, 'west': True}


def house_door(rid, i, wall, centre, notes):
    """An oak house door as one whole picture: the left wing chb1dl and the right wing chb1dr (as seen from the room)
    on two panels side by side; the left one carries A4's door id, the right one `<id>_r`."""
    lo, hi = (centre - 64, centre + 64)
    left, right = (lo, hi) if LEFT_IS_LOWER[wall] else (hi, lo)
    return [panel(rid, i, wall, left, 128, 0, 256, OAK_L, notes),
            panel(rid, 'panel:' + i.split(':')[1] + '_r', wall, right, 128, 0, 256, OAK_R)]


def framed(rid, i, wall, centre, bottom, surface, notes, length=128, height=256, frame=PLANK, width=16):
    """A panel (a mirror 128 by 256, a sign) in a frame (default oak 7trimd, 16 wide), so it never meets the wall's
    stone bare (the signs' brown board on the cream marble: texture fit's feature_border)."""
    return [panel(rid, i, wall, centre, length, bottom, height, surface, notes),
            panel(rid, i + '_ft', wall, centre, length + 2 * width, bottom + height, width, frame),
            panel(rid, i + '_fb', wall, centre, length + 2 * width, bottom - width, width, frame),
            panel(rid, i + '_fl', wall, centre - (length + width) // 2, width, bottom, height, frame),
            panel(rid, i + '_fr', wall, centre + (length + width) // 2, width, bottom, height, frame)]


def mirror(rid, i, wall, centre, bottom, notes):
    """A mirror: the pale silvered glass xkmirror in a frame of the castle's dark pillar marble t3elr, 32 wide. An oak
    frame baked as pale as the glass, and the glass (lit past white) read as a white sheet (DD-02's finding too)."""
    return framed(rid, i, wall, centre, bottom, MIRROR, notes, frame=PILLAR, width=32)


def marble_sign(rid, i, wall, centre, length, bottom, height, notes):
    """A sign on the royal marble: the board in its oak frame."""
    return framed(rid, i, wall, centre, bottom, SIGN, notes, length, height)


def plat(i, at, size, rise, surface, top=None, **kw):
    d = {'id': 'platform:' + i, 'at': F(*at), 'size': F(*size), 'rise': rise, 'surface': surface,
         'top_surface': top or surface}
    d.update(kw)
    return d


ROOMS = []


def room(rid, name, r, floor, ceiling, theme, ambient, notes, **kw):
    d = {'id': 'room:' + rid, 'name': name}
    if isinstance(r, tuple):
        RECT[rid] = r
        d['outline'] = rect(*r)
    else:
        d['outline'] = [F(*p) for p in r]
    d.update({'floor': floor, 'ceiling': ceiling, 'theme': 'theme:' + theme, 'ambient': ambient})
    d.update(kw)
    d['notes'] = notes
    ROOMS.append(d)
    return d


def walls(rid, spec):
    """spec: {wall: [panel(...), ...]}"""
    return [{'wall': w, 'panels': ps} for w, ps in spec.items()]


def flight(rid, name, r, f0, f1, toward, c0, c1, theme, notes):
    return room(rid, name, r, f0, c0, theme, 16, notes, slope={'to': f1, 'toward': toward, 'steps': 20},
                ceiling_slope={'to': c1, 'toward': toward})


# ---- ground floor (0), stage 1 -------------------------------------------------------------------------------------
room('gate', 'Gate passage', (-2048, -384, -1024, 384), 0, 512, 'gate', 18,
     "Inside Kalindra's gate: the arrival from D1 and the way out, under the portcullis and the Queen's crest.")
RW = {}
RW['gate'] = walls('gate', {
    'north': [panel('gate', 'panel:crest_gate', 'north', -1536, 128, 128, 256, CREST,
                    "Kalindra's crest, her silver crescent and rose on purple, on the ashlar it was painted for.")],
    'south': [panel('gate', 'panel:slit_gate', 'south', -1536, 128, 96, 288, ARROW, "An arrow slit.")]})
room('entrance', 'Entrance hall', (-896, -896, 1024, 896), 0, 768, 'hall', 22,
     "White marble and purple banners: doors to the throne room (east), the north wing, and the shimmering wall of "
     "the stable yard (south).")
RW['entrance'] = walls('entrance', {
    'west': [panel('entrance', 'panel:banner_e1', 'west', -640, 192, 192, 384, BANNER),
             panel('entrance', 'panel:banner_e2', 'west', 640, 192, 192, 384, BANNER)],
    'east': marble_sign('entrance', 'panel:sign_throne', 'east', 448, 192, 256, 96, "Sign: Throne Room."),
    'north': marble_sign('entrance', 'panel:sign_north', 'north', 448, 192, 256, 96, "Sign: North Wing.")})
room('north_wing', 'North Wing', (-896, 1024, 1536, 1408), 0, 512, 'wing', 14,
     "A long cobbled corridor still half out of phase: the Cloud Stairs at its west end, the banquet hall's doors.")
RW['north_wing'] = walls('north_wing', {
    'north': [panel('north_wing', 'panel:sign_banquet', 'north', 160, 192, 288, 96, SIGN, "Sign: Banquet Hall."),
              panel('north_wing', 'panel:shimmer_nw', 'north', 1280, 256, 32, 448, SHIMMER,
                    "A stretch of wall still out of phase.")],
    'south': [panel('north_wing', 'panel:sign_stairs', 'south', -512, 192, 288, 96, SIGN, "Sign: Cloud Stairs.")]})
room('cloud_foot', 'Cloud Stairs', (-2048, 1024, -1024, 1664), 0, 576, 'royal', 20,
     "The foot of a white stair up through painted clouds; until stage 2 the stair itself is mist.")
flight('cloud_flight', 'Cloud Stairs (flight)', (-1792, 1792, -1280, 2816), 0, 640, 'north', 448, 1088, 'royal',
       "Twenty white steps up north to the second floor.")
room('banquet', 'Banquet Hall', (0, 1536, 1536, 2688), 0, 576, 'wing', 14,
     "A table laid for a feast nobody ate.",
     platforms=[plat('banquet_table', (768, 2176), (896, 160), 80, DESK_SIDE, BOARD_TOP,
                     notes="The long banquet table, laid for a hundred years.")])
room('kitchen', 'Kitchen', (1664, 1024, 2944, 2304), 0, 512, 'wing', 18,
     "Barrels, a larder of sun-dried lizard innards, Carl the Mason at his bench; the servants' passage south.",
     platforms=[plat('kitchen_table', (2304, 1856), (448, 160), 80, DESK_SIDE, BOARD_TOP, notes="The kitchen table."),
                plat('carl_bench', (2816, 1600), (128, 256), 48, DESK_SIDE, BOARD_TOP,
                     notes="Carl the Mason's bench by the east wall.")])
RW['kitchen'] = walls('kitchen', {
    'south': [panel('kitchen', 'panel:sign_kitchen', 'south', 1920, 192, 256, 96, SIGN, "Sign: Kitchen.")]})
room('throne', 'Throne Room', (1152, -896, 2944, 896), 0, 768, 'hall', 22,
     "The empty throne on its dais, dust like snow; two safes behind tapestries; the coat closet east.",
     platforms=[plat('dais', (2752, 0), (320, 640), 32, MFLOOR, MFLOOR, notes="The throne's dais."),
                plat('kalindra_throne', (2816, 0), (160, 192), 144, PILLAR, FLAGS,
                     notes="The Empty Throne: house 4501's door (A4's thing:kalindra_throne)."),
                plat('throne_back', (2912, 0), (64, 224), 416, PILLAR, MCEIL, notes="The throne's tall back.")],
     pillars=[{'at': F(x, y), 'size': F(128, 128), 'surface': PILLAR} for x in (1664, 2304) for y in (-640, 640)])
RW['throne'] = walls('throne', {
    'north': [panel('throne', 'panel:tap_safe_w', 'north', 1536, 128, 128, 320, TAP['tap1'],
                    "A tapestry: a safe behind it."),
              panel('throne', 'panel:tap_safe_e', 'north', 1920, 128, 128, 320, TAP['tap4'],
                    "A tapestry: a safe behind it.")],
    'east': [panel('throne', 'panel:crest_throne', 'east', -384, 192, 192, 384, BANNER),
             panel('throne', 'panel:banner_throne', 'east', 384, 192, 192, 384, BANNER)],
    'south': marble_sign('throne', 'panel:sign_south', 'south', 2560, 192, 288, 96, "Sign: South Wing."),
    'west': [panel('throne', 'panel:tap_throne', 'west', -512, 128, 128, 320, TAP['tap7'])]})
room('south_wing', 'South Wing', (1152, -1408, 4992, -1024), 0, 512, 'wing', 14,
     "A cobbled corridor still half out of phase: the armory's door, the dungeon stair at its east end.")
RW['south_wing'] = walls('south_wing', {
    'north': [panel('south_wing', 'panel:sign_armory', 'north', 4096, 192, 256, 96, SIGN, "Sign: Armory."),
              panel('south_wing', 'panel:shimmer_sw', 'north', 3328, 256, 32, 448, SHIMMER,
                    "A stretch of wall still out of phase.")],
    'south': [panel('south_wing', 'panel:shimmer_sw2', 'south', 1792, 256, 32, 448, SHIMMER)]})
room('closet', 'Coat Closet', (3072, 384, 3584, 896), 0, 448, 'wing', 14,
     "A dead end of coat hooks. Its back wall is an illusion (Carl the Mason: 'just keep walking').")
RW['closet'] = walls('closet', {
    'north': [panel('closet', 'panel:hooks', 'north', 3328, 256, 160, 128, PLANK, "Coat hooks on a plank.")]})
room('armory', 'Armory', (3712, -896, 4992, 896), 0, 512, 'wing', 16,
     "Racks of the guard's arms; a tougher safe (10-11-12, Guido's tip).",
     platforms=[plat('rack_n', (4352, 832), (768, 64), 224, PLANK, BOARD_TOP, notes="A weapon rack."),
                plat('rack_e', (4928, -192), (64, 640), 224, PLANK, BOARD_TOP, notes="A weapon rack.")])
room('dstair_head', 'Dungeon stair', (5120, -1408, 5632, -1024), 0, 448, 'dungeon', 14,
     "The head of the dungeon stair: until stage 3 it ends in shimmering nothing.")
flight('dstair', 'Dungeon stair (flight)', (5184, -2560, 5568, -1536), 0, -640, 'south', 448, -192, 'dungeon',
       "Twenty steps down south to the guardroom.")
room('yard', 'Stable yard', (-1664, -3200, 1024, -1024), 0, 1024, 'yard', 26,
     "An open yard inside the castle walls (sky): Kalindra Stables (4510) and the Mirror of Castle Kalindra (4512), "
     "behind the stage-4 phase wall.")
RW['yard'] = walls('yard', {
    'west': house_door('yard', 'door:stables', 'west', -2304, "Kalindra Stables' door (house 4510, stage 4).")
    + [panel('yard', 'panel:yard_win_w', 'west', -1536, 128, 192, 256, WINDOW)],
    'south': [panel('yard', 'panel:yard_win_s1', 'south', -896, 128, 192, 256, WINDOW),
              panel('yard', 'panel:yard_win_s2', 'south', 640, 128, 192, 256, WINDOW),
              panel('yard', 'panel:crest_yard', 'south', -128, 128, 352, 256, CREST,
                    "Kalindra's crest over the mirror, as wide as the glass (a wider crest is cut by the frame's "
                    "columns).")]
    + mirror('yard', 'panel:kalindra_mirror', 'south', -128, 48,
             "The Mirror of Castle Kalindra (house 4512, A4's thing:kalindra_mirror)."),
    'east': [panel('yard', 'panel:yard_win_e', 'east', -2304, 128, 192, 256, WINDOW)]})
ROOMS[-1]['platforms'] = [plat('trough', (-1536, -1664), (64, 384), 64, PLANK, PLANK, notes="A horse trough.")]

# ---- second floor (640), stage 2 -----------------------------------------------------------------------------------
room('l2_landing', 'Second-floor landing', (-2048, 2944, -1024, 3456), 640, 1088, 'royal', 18,
     "The Cloud Stairs' head.")
room('upper_foot', 'Upper stair', (-896, 2944, 256, 3456), 640, 1088, 'royal', 18,
     "The foot of the upper stair: until stage 4 the stair is mist.")
flight('upper_flight', 'Upper stair (flight)', (-640, 3584, -128, 4608), 640, 1280, 'north', 1088, 1728, 'royal',
       "Twenty marble steps up north to the third floor.")
room('residences', "Captain's corridor", (384, 2944, 2944, 3328), 640, 1088, 'royal', 18,
     "Three house doors: Captain's Quarters (4502), Megan's Room (4503), the Observatory (4504).")
RW['residences'] = walls('residences', {
    'north': house_door('residences', 'door:captain_quarters', 'north', 896, "Captain's Quarters (house 4502, Dimitri).")
    + house_door('residences', 'door:megan_room', 'north', 1664, "Megan's Room (house 4503).")
    + house_door('residences', 'door:observatory', 'north', 2432, "The Observatory (house 4504, the telescope).")})
room('sleeping', 'Sleeping Chambers', (384, 1664, 1920, 2816), 640, 1088, 'royal', 16,
     "The household's dormitory, beds made up for a century.",
     platforms=[plat('bed_%d' % i, (x, y), (160, 256), 64, BEDS, BEDS, notes="A bed.")
                for i, (x, y) in enumerate([(512, 1856), (896, 1856), (1280, 1856), (512, 2560), (1664, 1856)], 1)])
RW['sleeping'] = walls('sleeping', {
    'north': marble_sign('sleeping', 'panel:sign_sleeping', 'north', 896, 192, 352, 96, "Sign: Sleeping Chambers.")})
room('phase_gallery', 'Phase gallery', (2048, 1408, 2560, 2816), 640, 1088, 'wing', 14,
     "A gallery whose outer wall still shimmers; the spirits pass through it.")
RW['phase_gallery'] = walls('phase_gallery', {
    'west': [panel('phase_gallery', 'panel:shimmer_pg1', 'west', 1728, 384, 32, 416, SHIMMER)],
    'east': [panel('phase_gallery', 'panel:shimmer_pg2', 'east', 2496, 384, 32, 416, SHIMMER)]})
room('vaults', 'Vaults', (2688, 1408, 3712, 2304), 640, 1088, 'royal', 20,
     "The disk safes (m24.disk_safes, 64-52-31, after Dimitri).")
RW['vaults'] = walls('vaults', {
    'east': [panel('vaults', 'panel:disk_safe', 'east', 1856, 128, 64, 256, IRON_DOOR,
                   "The disk safes: an iron door with six dials.")],
    'west': marble_sign('vaults', 'panel:sign_vaults', 'west', 2176, 128, 352, 64, "Sign: Vaults.")})

# ---- third floor (1280), stage 4 -----------------------------------------------------------------------------------
room('l3_landing', 'Third-floor landing', (-896, 4736, 256, 5248), 1280, 1728, 'royal', 18,
     "The upper stair's head.")
room('bell_tower', 'Bell tower', (-2048, 4352, -1024, 5376), 1280, 2304, 'gate', 14,
     "Ropes and a cracked bell high above; the vampires' roost.",
     beams=[{'path': [F(-2048, y), F(-1024, y)], 'width': 48, 'bottom': 2112, 'depth': 48, 'surface': PLANK}
            for y in (4672, 5056)])
RW['bell_tower'] = walls('bell_tower', {
    'west': [panel('bell_tower', 'panel:slit_bell', 'west', 4864, 128, 192, 288, ARROW, "An arrow slit.")]})
room('attic', 'Shimmering attic',
     [(-1920, 3072), (256, 3072), (256, 3456), (-1536, 3456), (-1536, 4224), (-1920, 4224)], 1280, 1664, 'wing', 12,
     "Rafters still half out of phase: the last spirits; the roof walk from the bell tower to the Queen's court.",
     beams=[{'path': [F(x, 3072), F(x, 3456)], 'width': 48, 'bottom': 1568, 'depth': 48, 'surface': PLANK}
            for x in (-1280, -640, 0)])
room('court3', "The Queen's court", (384, 3072, 2432, 4480), 1280, 1856, 'hall', 22,
     "Five house doors (stage 4): Chapel of the Queen 4506, Royal Treasury 4507, the Queen's Proving Hall 4508, the "
     "Queen's Forge 4509, the Queen's Guard 4511.",
     pillars=[{'at': F(x, y), 'size': F(128, 128), 'surface': PILLAR} for x in (1024, 1792) for y in (3584, 4096)])
RW['court3'] = walls('court3', {
    'south': house_door('court3', 'door:chapel', 'south', 896, "Chapel of the Queen (house 4506).")
    + [panel('court3', 'door:treasury', 'south', 1920, 160, 0, 320, IRON_DOOR, "The Royal Treasury (4507).")],
    'east': house_door('court3', 'door:training', 'east', 3456, "The Queen's Proving Hall (4508).")
    + house_door('court3', 'door:forge', 'east', 4096, "The Queen's Forge (4509)."),
    'west': house_door('court3', 'door:guard_barracks', 'west', 4096, "The Queen's Guard (4511).")
    + [panel('court3', 'panel:banner_c', 'west', 3584, 192, 128, 384, BANNER)]})
room('queens_gallery', "The Queen's gallery", (384, 4608, 2432, 5632), 1280, 1856, 'hall', 20,
     "Portraits of the Queen under her banners; Blackfang's servants waiting for her to come home.")
RW['queens_gallery'] = walls('queens_gallery', {
    'north': [panel('queens_gallery', 'panel:tap_g%d' % i, 'north', x, 128, 160, 320, TAP[t])
              for i, (x, t) in enumerate([(768, 'tap1'), (1408, 'tap7'), (2048, 'tap4')], 1)]
    + [panel('queens_gallery', 'panel:banner_g%d' % i, 'north', x, 192, 128, 384, BANNER)
       for i, x in enumerate([1088, 1728], 1)]})
room('bedchamber', 'Royal Bed Chamber', (2560, 4608, 3584, 5632), 1280, 1792, 'royal', 22,
     "The Queen's room: the wall safe behind her mirror, the Queen's Brew and the Knight's Brew, the button "
     "'Activate Mirror Portals?'.",
     platforms=[plat('royal_bed', (3264, 5312), (384, 448), 80, BEDS, BEDS, notes="The Queen's bed.")])
RW['bedchamber'] = walls('bedchamber', {
    'north': mirror('bedchamber', 'panel:queens_mirror', 'north', 2880, 128,
                    "The Queen's mirror; the wall safe behind it (m27.crown_safe)."),
    'west': marble_sign('bedchamber', 'panel:sign_bed', 'west', 5408, 128, 352, 64, "Sign: Royal Bed Chamber."),
    'east': [panel('bedchamber', 'panel:banner_bc', 'east', 4864, 192, 128, 384, BANNER)]})

# ---- the dungeon (-640), stage 3 -----------------------------------------------------------------------------------
room('guardroom', 'Guardroom', (4736, -3840, 5888, -2688), -640, -128, 'dungeon', 14,
     "The stair's foot; the prisoner ledger on the desk (t2-a.cells); the old well's low mouth south.",
     platforms=[plat('ledger_desk', (5760, -3328), (256, 128), 80, DESK_SIDE, DESK_TOP,
                     notes="The guard's desk: the prisoner ledger.")])
room('cells', 'The cell block', (2432, -3840, 4608, -2688), -640, -128, 'dungeon', 12,
     "Five cells along the north wall, five liches (T2-A).",
     platforms=[plat('cellwall_%d' % i, (x, -2944), (64, 512), 512, DCOBBLE, CCEIL, notes="A cell's side wall.")
                for i, x in enumerate([2848, 3264, 3680, 4096], 1)])
room('maxsec', 'Maximum Security', (1152, -4352, 2304, -2944), -640, -128, 'dungeon', 14,
     "Guido's Cell (4505, stage 3); the kennel's portcullis and its lever under three notes.")
RW['maxsec'] = walls('maxsec', {
    'north': [panel('maxsec', 'door:guido_cell', 'north', 1600, 160, 0, 320, IRON_DOOR, "Guido's Cell (house 4505).")],
    'east': [panel('maxsec', 'panel:sign_maxsec', 'east', -3648, 128, 352, 64, SIGN, "Sign: Maximum Security.")],
    'south': [panel('maxsec', 'panel:note_beware', 'south', 1312, 128, 224, 64, SIGN, "A note: Beware of Scraps!"),
              panel('maxsec', 'panel:note_feed', 'south', 1856, 128, 224, 64, SIGN, "A note: Don't feed Scraps."),
              panel('maxsec', 'panel:note_out', 'south', 2112, 128, 224, 64, SIGN, "A note: Don't let Scraps out!")]})
flight('kennel_stair', 'Kennel stair', (1440, -5632, 1760, -4480), -640, -1152, 'south', -352, -864, 'dungeon',
       "A narrow, low stair down to Scraps' kennel: 320 wide and 288 high, lower than his body (D-32).")
ROOMS[-1]['slope']['steps'] = 16
room('kennel', "Scraps' kennel", (768, -7296, 2944, -5760), -1152, -128, 'dungeon', 10,
     "An undead dragon on the bones of its dinners; the castle's hoard.")
room('vault_d', 'Dungeon vault', (2432, -4992, 3712, -3968), -640, -192, 'dungeon', 14,
     "Confiscated goods; a tougher safe (10-11-12); a secret door to Maximum Security.")
room('well', 'Old well', (3840, -5376, 5120, -3968), -640, 384, 'dungeon', 10,
     "The castle well's dry bottom, a shaft of old stone overhead: two Bone Dragons, Iron Vithnipravad and Argonax.")

# ---------------------------------------------------------------------------------------------------------------------
# Openings


def op(i, a, b, link, width, height, **kw):
    d = {'id': 'open:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'link': 'link:' + link, 'width': width,
         'height': height}
    d.update(kw)
    return d


OPENINGS = [
    op('gate_entrance', 'gate', 'entrance', 'gate_entrance', 320, 384, notes="The portcullis (stage 1)."),
    op('entrance_throne', 'entrance', 'throne', 'entrance_throne', 384, 448, notes="The throne room's double doors."),
    op('entrance_north', 'entrance', 'north_wing', 'entrance_north', 384, 384, shape='arch', apex=448),
    op('north_cloud', 'north_wing', 'cloud_foot', 'north_cloud', 320, 384),
    op('cloud_gate', 'cloud_foot', 'cloud_flight', 'cloud', 384, 384, from_wall='north', to_wall='south',
       notes="The Cloud Stairs' phase leaf (stage 2)."),
    op('cloud_top', 'cloud_flight', 'l2_landing', 'cloud', 'full', 384, from_wall='north', to_wall='south',
       reveal=MARBLE, threshold=FLAGS, notes="The flight's head: its marble walls run on (no dark pillar in the plane)."),
    op('north_banquet', 'north_wing', 'banquet', 'north_banquet', 384, 384, notes="The banquet hall's double doors."),
    op('banquet_kitchen', 'banquet', 'kitchen', 'banquet_kitchen', 320, 384, shape='arch', apex=448),
    op('kitchen_throne', 'kitchen', 'throne', 'kitchen_throne', 192, 320, notes="The servants' passage."),
    op('throne_south', 'throne', 'south_wing', 'throne_south', 384, 384, shape='arch', apex=448),
    op('throne_closet', 'throne', 'closet', 'throne_closet', 256, 256),
    op('closet_armory', 'closet', 'armory', 'closet_armory', 192, 320, reveal=COBBLE, notes="The illusory wall."),
    op('armory_south', 'armory', 'south_wing', 'armory_south', 256, 256),
    op('entrance_yard', 'entrance', 'yard', 'entrance_yard', 384, 384, notes="The yard's phase wall (stage 4)."),
    op('south_dhead', 'south_wing', 'dstair_head', 'south_dhead', 320, 384),
    op('dstair_gate', 'dstair_head', 'dstair', 'dstair', 320, 384, from_wall='south', to_wall='north',
       notes="The dungeon stair's phase leaf (stage 3)."),
    op('dstair_guard', 'dstair', 'guardroom', 'dstair', 320, 384, from_wall='south', to_wall='north'),
    op('l2_upper', 'l2_landing', 'upper_foot', 'l2_upper', 320, 384),
    op('upper_gate', 'upper_foot', 'upper_flight', 'upper', 384, 384, from_wall='north', to_wall='south',
       notes="The upper stair's phase leaf (stage 4)."),
    op('upper_top', 'upper_flight', 'l3_landing', 'upper', 'full', 384, from_wall='north', to_wall='south',
       reveal=MARBLE, threshold=FLAGS, notes="The flight's head: its marble walls run on (no dark pillar in the plane)."),
    op('upper_res', 'upper_foot', 'residences', 'upper_res', 320, 384),
    op('res_sleeping', 'residences', 'sleeping', 'res_sleeping', 256, 256),
    op('sleeping_phase', 'sleeping', 'phase_gallery', 'sleeping_phase', 384, 384, shape='arch', apex=416),
    op('phase_vaults', 'phase_gallery', 'vaults', 'phase_vaults', 384, 384, notes="The vault's double doors."),
    op('l3_gallery', 'l3_landing', 'queens_gallery', 'l3_gallery', 384, 384, shape='arch', apex=416),
    op('l3_bell', 'l3_landing', 'bell_tower', 'l3_bell', 320, 384),
    op('gallery_bed', 'queens_gallery', 'bedchamber', 'gallery_bed', 384, 448, notes="The bedchamber's doors."),
    op('gallery_court', 'queens_gallery', 'court3', 'gallery_court', 512, 448, shape='arch', apex=512),
    op('bell_attic', 'bell_tower', 'attic', 'bell_attic', 320, 320),
    op('attic_court', 'attic', 'court3', 'attic_court', 256, 320),
    op('guard_cells', 'guardroom', 'cells', 'guard_cells', 256, 352),
    op('cells_maxsec', 'cells', 'maxsec', 'cells_maxsec', 320, 384, shape='arch', apex=448),
    op('maxsec_kennel', 'maxsec', 'kennel_stair', 'kennel', 256, 288, from_wall='south', to_wall='north',
       notes="The kennel's portcullis: 288 high (D-32)."),
    op('kennel_mouth', 'kennel_stair', 'kennel', 'kennel', 256, 256, from_wall='south', to_wall='north'),
    op('guard_well', 'guardroom', 'well', 'guard_well', 320, 256, notes="The old well's low mouth (D-32)."),
    op('vault_well', 'vault_d', 'well', 'vault_well', 256, 256, notes="Low (D-32)."),
    op('maxsec_vault', 'maxsec', 'vault_d', 'maxsec_vault', 192, 288, reveal=DCOBBLE, notes="The vault's secret door."),
]

for r in ROOMS:
    k = r['id'].split(':')[1]
    if k in RW:
        r['walls'] = RW[k]

# ---------------------------------------------------------------------------------------------------------------------
# Monsters (D-26): stage 1 visible; stages 2-4 placed hidden in their groups and shown by the stage's load event.

TG, GR, TT, LICH, BD, VAMP, GV, SCRAPS = 11261, 11263, 11262, 11280, 11670, 11291, 11290, 11673
STAGE_GROUPS = {2: [21, 22], 3: [31, 32, 33, 34, 35], 4: [41, 42, 43]}
POP = [
    # (room, group, stage, [(row, x, y, name)])
    ('north_wing', 1, 1, [(TG, -384, 1216), (TG, 256, 1216), (TG, 768, 1216), (TG, 1280, 1216)]),
    ('banquet', 2, 1, [(TG, 256, 1792), (TG, 1280, 1792), (TG, 256, 2496), (TG, 1280, 2496)]),
    ('south_wing', 3, 1, [(GR, 1664, -1216), (GR, 2560, -1216), (GR, 3456, -1216), (GR, 4352, -1216)]),
    ('sleeping', 21, 2, [(GR, 704, 2240), (GR, 1088, 2240), (GR, 1472, 2240), (GR, 1088, 2560),
                         (TT, 896, 2560), (TT, 1600, 2560)]),
    ('phase_gallery', 22, 2, [(TG, 2304, 1664), (TG, 2304, 2048), (TG, 2304, 2432), (TG, 2304, 2688),
                              (TT, 2176, 1856), (TT, 2432, 2240)]),
    ('cells', 31, 3, [(LICH, 2640, -2880, 'Vexor the Black'), (LICH, 3056, -2880, 'Clemon the Dead'),
                      (LICH, 3472, -2880, 'Saxar the Permanent'), (LICH, 3888, -2880, 'Morgrath the Grey'),
                      (LICH, 4352, -2880, 'Ulvane the Unrepentant')]),
    ('maxsec', 32, 3, [(TT, 1408, -3328), (TT, 2048, -3328), (TT, 1408, -3968), (TT, 2048, -3968)]),
    ('guardroom', 33, 3, [(TT, 5056, -3072), (TT, 5248, -3584)]),
    ('well', 34, 3, [(BD, 4224, -4864, 'Iron Vithnipravad'), (BD, 4800, -4608, 'Argonax')]),
    ('kennel', 35, 3, [(SCRAPS, 1856, -6720)]),
    ('queens_gallery', 41, 4, [(VAMP, 768, 5248), (VAMP, 1408, 5248), (VAMP, 2048, 5248), (VAMP, 1408, 4864),
                               (TT, 896, 4864), (TT, 1920, 4864)]),
    ('bell_tower', 42, 4, [(VAMP, -1792, 4608), (VAMP, -1280, 4608), (VAMP, -1792, 5120), (VAMP, -1280, 5120),
                           (GV, -1536, 4608), (GV, -1536, 5120), (GV, -1792, 4864), (GV, -1280, 4864)]),
    ('attic', 43, 4, [(TT, -1728, 3968), (TT, -1024, 3264), (TT, -128, 3264)]),
]
STAGE_OF_GROUP = {}
MONSTERS = []
for rm, group, stage, entries in POP:
    STAGE_OF_GROUP[group] = stage
    for n, e in enumerate(entries):
        row, x, y = e[0], e[1], e[2]
        d = {'id': 'monster:%s_%d' % (rm, n + 1), 'room': 'room:' + rm, 'monster': row, 'at': F(x, y),
             'facing': 270, 'group': group}
        if stage > 1:
            d['hidden'] = True
        if len(e) > 3:
            d['name'] = e[3]
        if row == SCRAPS:
            d['id'] = 'monster:scraps'
            d['notes'] = "Scraps (Drothnavod the Weighty), optional: behind the kennel portcullis, at the foot of a " \
                         "stair 288 high (D-32)."
        MONSTERS.append(d)
MONSTERS.append({'id': 'monster:carl', 'room': 'room:kitchen', 'monster': CARL_BODY, 'at': F(2688, 1408),
                 'facing': 180, 'group': 50, 'hostile': False, 'immobile': True,
                 'notes': "Carl the Mason (NPC 5014) at his bench: he talks through the bench (Words needed). The body "
                          "is the engine's peaceful Peasant 364, as DD-02's Ellinger."})
COUNT = {}
for m in MONSTERS:
    if m['monster'] not in (CARL_BODY, SCRAPS):
        COUNT[m['monster']] = COUNT.get(m['monster'], 0) + 1
assert COUNT == {TG: 12, GR: 8, TT: 15, LICH: 5, BD: 2, VAMP: 8, GV: 4}, COUNT
assert sum(COUNT.values()) == 54

# ---------------------------------------------------------------------------------------------------------------------
# Objects


def deco(i, rm, name, at, **kw):
    d = {'id': 'deco:' + i, 'room': 'room:' + rm, 'decoration': name, 'at': F(*at)}
    d.update(kw)
    return d


DECORATIONS = [
    deco('gate_torch_n', 'gate', 'torch02', (-1280, 384), wall='north'),
    deco('gate_torch_s', 'gate', 'torch02', (-1280, -384), wall='south'),
    deco('entrance_chandelier', 'entrance', 'chndlir0', (64, 0), hangs=True),
    deco('entrance_sconce_n', 'entrance', 'scon100', (-512, 896), wall='north'),
    deco('entrance_sconce_s', 'entrance', 'scon100', (640, -896), wall='south'),
    deco('nw_sconce', 'north_wing', 'scon100', (512, 1024), wall='south'),
    deco('cloud_sconce', 'cloud_foot', 'scon100', (-2048, 1344), wall='west'),
    deco('banquet_chandelier', 'banquet', 'chndlir0', (768, 2176), hangs=True),
    deco('banquet_candle_1', 'banquet', 'cndlab0', (512, 2176), floor_height=80),
    deco('banquet_candle_2', 'banquet', 'cndlab0', (1024, 2176), floor_height=80),
    deco('kitchen_barrel_1', 'kitchen', 'bigbarel', (2744, 2216)),
    deco('kitchen_barrel_2', 'kitchen', 'bigbarel', (2856, 2216)),
    deco('kitchen_sack_1', 'kitchen', 'bag01', (2232, 2216)),
    deco('kitchen_sack_2', 'kitchen', 'bag01', (2344, 2216)),
    deco('kitchen_sconce', 'kitchen', 'scon100', (1664, 1600), wall='west'),
    deco('throne_chandelier', 'throne', 'chndlir0', (1984, 0), hangs=True),
    deco('throne_sconce_n', 'throne', 'scon100', (2560, 896), wall='north'),
    deco('throne_sconce_s', 'throne', 'scon100', (2560, -896), wall='south'),
    deco('sw_sconce', 'south_wing', 'scon100', (2560, -1024), wall='north'),
    deco('armory_sconce', 'armory', 'scon100', (3712, -448), wall='west'),
    deco('dhead_torch', 'dstair_head', 'torch02', (5632, -1216), wall='east'),
    deco('l2_sconce', 'l2_landing', 'scon100', (-1536, 3456), wall='north'),
    deco('upper_sconce', 'upper_foot', 'scon100', (-320, 2944), wall='south'),
    deco('res_sconce_1', 'residences', 'scon100', (1280, 2944), wall='south'),
    deco('res_sconce_2', 'residences', 'scon100', (2048, 2944), wall='south'),
    deco('sleeping_sconce', 'sleeping', 'scon100', (384, 2240), wall='west'),
    deco('vaults_sconce', 'vaults', 'scon100', (3200, 2304), wall='north'),
    deco('l3_sconce', 'l3_landing', 'scon100', (-320, 5248), wall='north'),
    deco('court_chandelier', 'court3', 'chndlir0', (1408, 3776), hangs=True),
    deco('gallery_chandelier', 'queens_gallery', 'chndlir0', (1408, 5120), hangs=True),
    deco('bed_candle', 'bedchamber', 'cndlab0', (2752, 5504)),
    deco('queens_brew', 'bedchamber', 'bigbarel', (3496, 4808)),
    deco('knights_brew', 'bedchamber', 'bigbarel', (3496, 4920)),
    deco('bell_torch', 'bell_tower', 'torch02', (-1024, 4608), wall='east'),
    deco('guard_torch', 'guardroom', 'torch02', (5888, -3072), wall='east'),
    deco('cells_torch_1', 'cells', 'torch02', (3072, -3840), wall='south'),
    deco('cells_torch_2', 'cells', 'torch02', (4096, -3840), wall='south'),
    deco('maxsec_torch', 'maxsec', 'torch02', (1152, -3648), wall='west'),
    deco('kennel_bones_1', 'kennel', '7dec18', (1088, -6976)),
    deco('kennel_bones_2', 'kennel', '7dec18', (2560, -7040)),
    deco('kennel_bones_3', 'kennel', '7dec18', (1216, -6080)),
    deco('well_bones_1', 'well', '7dec18', (4032, -5184)),
    deco('well_bones_2', 'well', '7dec18', (4928, -5120)),
    deco('vault_torch', 'vault_d', 'torch02', (2432, -4736), wall='west'),
]

LIGHTS = []


def light(i, rm, at, height, radius, color, **kw):
    d = {'id': 'light:' + i, 'room': 'room:' + rm, 'at': F(*at), 'height': height, 'radius': radius,
         'color': F(*color)}
    d.update(kw)
    LIGHTS.append(d)


WARM = (255, 215, 170)
TORCH = (255, 180, 120)
GHOST = (200, 190, 255)
light('gate', 'gate', (-1536, 0), 320, 1100, TORCH)
light('entrance', 'entrance', (64, 0), 448, 1800, WARM)
light('nw_w', 'north_wing', (-256, 1216), 320, 1100, GHOST)
light('nw_e', 'north_wing', (1024, 1216), 320, 1100, GHOST)
light('cloud', 'cloud_foot', (-1536, 1344), 384, 1100, (235, 235, 255))
light('banquet', 'banquet', (768, 2176), 400, 1400, GHOST)
light('kitchen', 'kitchen', (2304, 1664), 320, 1200, TORCH)
light('throne', 'throne', (1984, 0), 480, 1900, WARM)
light('sw_w', 'south_wing', (1792, -1216), 320, 1200, GHOST)
light('sw_e', 'south_wing', (3968, -1216), 320, 1200, GHOST)
light('closet', 'closet', (3328, 640), 288, 600, TORCH)
light('armory', 'armory', (4352, -192), 320, 1300, TORCH)
light('dhead', 'dstair_head', (5376, -1216), 288, 700, TORCH)
light('yard', 'yard', (-320, -2112), 640, 2600, (255, 235, 210))
light('l2', 'l2_landing', (-1536, 3200), 960, 900, WARM)
light('upper', 'upper_foot', (-320, 3200), 960, 900, WARM)
light('res', 'residences', (1664, 3136), 960, 1300, WARM)
light('sleeping', 'sleeping', (1152, 2240), 960, 1300, GHOST)
light('phase', 'phase_gallery', (2304, 2112), 960, 1100, GHOST, pulse={'intensity': F(0.75, 1), 'frequency': 0.3})
light('vaults', 'vaults', (3200, 1856), 960, 1000, WARM)
light('l3', 'l3_landing', (-320, 4992), 1600, 900, WARM)
light('bell', 'bell_tower', (-1536, 4864), 1700, 1300, (190, 170, 220))
light('attic', 'attic', (-512, 3264), 1536, 1100, GHOST)
light('court', 'court3', (1408, 3776), 1700, 1800, WARM)
light('gallery', 'queens_gallery', (1408, 5120), 1700, 1700, (230, 190, 210))
light('bed', 'bedchamber', (3072, 5120), 1600, 1200, WARM)
light('guard', 'guardroom', (5312, -3264), -320, 1100, TORCH)
light('cells', 'cells', (3520, -3264), -320, 1500, (180, 200, 255))
light('maxsec', 'maxsec', (1728, -3648), -320, 1200, TORCH)
light('kennel', 'kennel', (1856, -6528), -512, 1600, (170, 200, 150))
light('vault_d', 'vault_d', (3072, -4480), -352, 900, TORCH)
light('well', 'well', (4480, -4672), -256, 1200, (170, 190, 210))
for l in LIGHTS:   # heights above the room's floor
    rm = next(r for r in ROOMS if r['id'] == l['room'])
    l['height'] = l['height'] - rm['floor'] if l['height'] > 600 or l['height'] < 0 else l['height']

# The phase walls warble (xeen_phase_loop, AUDIO.md 62518): one quiet loop by each stage leaf, switched off by the
# stage's load event once its leaf is gone (map variable AmbientSound<number>, numbers from ids.lock.yml), and one in
# each wing whose shimmering patches stay.
PHASE_LOOP = 'xeen_phase_loop'
SOUNDS = [
    {'id': 'sound:shimmer_entrance', 'room': 'room:entrance', 'at': F(64, -768), 'sound': PHASE_LOOP, 'radius': 1300,
     'inner_radius': 300, 'volume': 0.35, 'notes': "The yard's phase wall (stage 4: off)."},
    {'id': 'sound:shimmer_pg', 'room': 'room:phase_gallery', 'at': F(2304, 2112), 'sound': PHASE_LOOP,
     'radius': 1100, 'inner_radius': 300, 'volume': 0.35, 'notes': "The gallery's shimmering walls (they stay)."},
    {'id': 'sound:phase_cloud', 'room': 'room:cloud_foot', 'at': F(-1536, 1600), 'sound': PHASE_LOOP, 'radius': 900,
     'inner_radius': 250, 'volume': 0.35, 'notes': "The Cloud Stairs' phase leaf (stage 2: off)."},
    {'id': 'sound:phase_dstair', 'room': 'room:dstair_head', 'at': F(5376, -1344), 'sound': PHASE_LOOP,
     'radius': 800, 'inner_radius': 200, 'volume': 0.35, 'notes': "The dungeon stair's phase leaf (stage 3: off)."},
    {'id': 'sound:phase_upper', 'room': 'room:upper_foot', 'at': F(-320, 3392), 'sound': PHASE_LOOP, 'radius': 1000,
     'inner_radius': 250, 'volume': 0.35, 'notes': "The upper stair's phase leaf (stage 4: off)."},
    {'id': 'sound:phase_nw', 'room': 'room:north_wing', 'at': F(1280, 1344), 'sound': PHASE_LOOP, 'radius': 900,
     'inner_radius': 200, 'volume': 0.3, 'notes': "The North Wing's shimmering patch (it stays)."},
    {'id': 'sound:phase_sw', 'room': 'room:south_wing', 'at': F(2560, -1216), 'sound': PHASE_LOOP, 'radius': 1100,
     'inner_radius': 250, 'volume': 0.3, 'notes': "The South Wing's shimmering patches (they stay)."},
    {'id': 'sound:kitchen', 'room': 'room:kitchen', 'at': F(1792, 1152), 'sound': 'bubbling cauldron01',
     'radius': 1000, 'inner_radius': 200, 'volume': 0.3, 'notes': "A pot on the kitchen fire."},
    {'id': 'sound:bell_wind', 'room': 'room:bell_tower', 'at': F(-1536, 4864), 'sound': 'whistling wind',
     'radius': 1600, 'inner_radius': 400, 'volume': 0.45, 'notes': "Wind round the bell."},
    {'id': 'sound:yard_wind', 'room': 'room:yard', 'at': F(-320, -2112), 'sound': 'whistling wind', 'radius': 2000,
     'inner_radius': 600, 'volume': 0.3, 'notes': "The open yard."},
    {'id': 'sound:well_wind', 'room': 'room:well', 'at': F(4480, -4672), 'sound': 'whistling wind', 'radius': 1400,
     'inner_radius': 300, 'volume': 0.3, 'notes': "Air down the old well's shaft."},
]




def sound_number(i):
    """A placed sound's number (ids.lock.yml `sounds`, written by the build); the switch is AmbientSound<number>."""
    with open(OUT + '/L4/ids.lock.yml') as f:
        return yaml.safe_load(f)['sounds'][i]


def sounds_off(*ids):
    return {'lua': '; '.join("evt.SetMapVar('AmbientSound%d', 2)" % sound_number(i) for i in ids)}


def door(i, opening, kind='slide_up', **kw):
    d = {'id': 'door:' + i, 'opening': 'open:' + opening, 'kind': kind, 'thickness': 16, 'speed': 120}
    d.update(kw)
    return d


def pic(sfc):
    return S(sfc['texture'], *sfc['size'])


def double(i, opening, **kw):
    return door(i, opening, kind='slide_left', leaves=2, pictures=[[pic(OAK_L), pic(OAK_R)]],
                back_pictures=[[pic(OAK_L), pic(OAK_R)]],
                edge_surface=PLANK, **kw)


DOORS = [
    door('portcullis', 'gate_entrance', surface=PORTC, back_surface=PORTC, speed=160,
         notes="The gate's portcullis: up from stage 1 (the load event)."),
    double('throne', 'entrance_throne', notes="The throne room's double doors."),
    double('banquet', 'north_banquet', notes="The banquet hall's double doors."),
    double('closet', 'throne_closet'),
    door('illusion', 'closet_armory', surface=COBBLE, back_surface=COBBLE, tile=True,
         notes="The coat closet's back wall: an illusion the party walks through (made passable at load)."),
    double('armory', 'armory_south'),
    door('cloud', 'cloud_gate', surface=SHIMMER, back_surface=SHIMMER, tile=True, speed=160,
         notes="The Cloud Stairs' phase leaf: open from stage 2."),
    door('yard', 'entrance_yard', surface=SHIMMER, back_surface=SHIMMER, tile=True, speed=160,
         notes="The stable yard's phase wall: open from stage 4."),
    door('dstair', 'dstair_gate', surface=SHIMMER, back_surface=SHIMMER, tile=True, speed=160,
         notes="The dungeon stair's phase leaf: open from stage 3."),
    door('upper', 'upper_gate', surface=SHIMMER, back_surface=SHIMMER, tile=True, speed=160,
         notes="The upper stair's phase leaf: open from stage 4."),
    double('sleeping', 'res_sleeping'),
    door('vaults', 'phase_vaults', kind='slide_left', leaves=2, pictures=[[pic(IRON_DOOR), pic(IRON_DOOR)]],
         back_pictures=[[pic(IRON_DOOR), pic(IRON_DOOR)]], edge_surface=PLANK, notes="The vault's iron double doors."),
    double('bedchamber', 'gallery_bed', notes="The Royal Bed Chamber's double doors."),
    door('cells', 'guard_cells', surface=IRON_DOOR, back_surface=IRON_DOOR),
    door('kennel', 'maxsec_kennel', surface=PORTC, back_surface=PORTC, speed=64,
         notes="The kennel's portcullis, worked by the lever under 'Don't let Scraps out!'."),
    door('vault_secret', 'maxsec_vault', secret=True, surface=DCOBBLE, back_surface=DCOBBLE, tile=True,
         notes="A secret door from Maximum Security into the dungeon vault."),
]

SWITCHES = [
    {'id': 'switch:kennel_lever', 'room': 'room:maxsec', 'kind': 'lever', 'at': F(2112, -4352), 'height': 128,
     'notes': "The kennel portcullis' lever, under 'Don't let Scraps out!'."},
    {'id': 'switch:mirror_switch', 'room': 'room:bedchamber', 'kind': 'button', 'at': F(3584, 5376), 'height': 128,
     'notes': "The button 'Activate Mirror Portals?' (m26.mirror_switch)."},
]

PLATES = [
    {'id': 'plate:mist_cloud', 'room': 'room:cloud_foot', 'at': F(-1536, 1536), 'size': F(384, 192),
     'surface': FLAGS, 'notes': "Before the Cloud Stairs' leaf: the mist line until stage 2."},
    {'id': 'plate:mist_upper', 'room': 'room:upper_foot', 'at': F(-384, 3328), 'size': F(384, 192),
     'surface': FLAGS, 'notes': "Before the upper stair's leaf: the mist line until stage 4."},
    {'id': 'plate:mist_dstair', 'room': 'room:dstair_head', 'at': F(5376, -1280), 'size': F(384, 192),
     'surface': DFLOOR, 'notes': "Before the dungeon stair's leaf: the mist line until stage 3."},
]

CHESTS = [
    {'id': 'chest:safe_w', 'room': 'room:throne', 'at': F(1536, 832), 'kind': 'ch4', 'treasure_level': 4, 'random_items': 2, 'gold': 600, 'trap_level': 4,
     'notes': "A thievery safe behind its tapestry (m19.safes: the first opened gives the two disks)."},
    {'id': 'chest:safe_e', 'room': 'room:throne', 'at': F(1920, 832), 'kind': 'ch4', 'treasure_level': 4, 'random_items': 2, 'gold': 600, 'trap_level': 4,
     'notes': "The second thievery safe (m19.safes)."},
    {'id': 'chest:armory_safe', 'room': 'room:armory', 'at': F(3808, -768), 'kind': 'ch4', 'treasure_level': 4, 'random_items': 3, 'gold': 1200, 'trap_level': 0,
     'notes': "A tougher safe: three dials, 10-11-12 (Guido's tip)."},
    {'id': 'chest:vault_safe', 'room': 'room:vault_d', 'at': F(3008, -4928), 'kind': 'ch4', 'treasure_level': 4, 'random_items': 3, 'gold': 1200, 'trap_level': 0,
     'notes': "The dungeon vault's tougher safe: 10-11-12."},
    {'id': 'chest:hoard', 'room': 'room:kennel', 'at': F(2752, -7168), 'kind': 'ch4', 'facing': 'n',
     'treasure_level': 5, 'random_items': 4, 'gold': 3000, 'trap_level': 5,
     'notes': "The castle's hoard (5), on Scraps' bones."},
]

EXITS = [
    {'id': 'exit:d1_gate', 'room': 'room:gate', 'wall': 'west', 'size': F(384, 384), 'surface': S('7solid01', 256, 256, fit=True),
     'to': 'exit:d1_gate', 'notes': "Kalindra's gate out to D1's forecourt."},
]

OBJECTS = {
    'format': 0,
    'start': {'room': 'room:gate', 'at': F(*START), 'facing': 0,
              'notes': "Inside the gate, facing in (east); D1's gate (entrance:dd03_gate, event 123) lands here."},
    'doors': DOORS,
    'plates': PLATES,
    'switches': SWITCHES,
    'sounds': SOUNDS,
    'lights': LIGHTS,
    'chests': CHESTS,
    'monsters': MONSTERS,
    'decorations': DECORATIONS,
    'exits': EXITS,
    'notes': "DD-03's contents, written by output/studio_cal/dd03/tools/gen.py: 16 doors (four phase leaves, the "
             "portcullis, four double doors, the illusory wall, a secret door, the kennel portcullis), 5 chests, 54 "
             "placed monsters and Scraps (stage 1 shown, stages 2-4 hidden in their groups), Carl the Mason.",
}

# ---------------------------------------------------------------------------------------------------------------------
# Wiring


def can(h):
    return {'lua': "XeenQuests.can(\"%s\")" % h}


def hook(h):
    return {'lua': "XeenQuests.hook(\"%s\")" % h}


def give_disks(h, n):
    return {'lua': "if XeenQuests.hook(\"%s\") then\n%send" % (
        h, ''.join("    AddValue(InventoryItem(%d), %d)\n" % (ENERGY_DISK, ENERGY_DISK) for _ in range(n)))}


def text(i, source, title, line, **kw):
    d = {'id': 'evt:' + i, 'preset': 'text', 'source': source, 'title': title, 'text': line}
    d.update(kw)
    return d


def status_line(t):
    """F13: a touch effect's text is a status line, evt.StatusText(text[, seconds]), never a window."""
    if len(t) > 30:
        return "evt.StatusText(\"%s\", %d)" % (t, max(2, min(6, 2 + len(t) // 15)))
    return "evt.StatusText(\"%s\")" % t


def brew(i, title, bit, var, line):
    return {'id': 'evt:' + i, 'preset': 'script', 'source': 'deco:' + i, 'title': title,
            'lua': ("evt.ForPlayer(Players.Current)\n"
                    "if IsPlayerBitSet(PlayerBit(%d)) then\n"
                    "    %s\n"
                    "    return\n"
                    "end\n"
                    "AddValue(%s, 2)\n"
                    "SetPlayerBit(PlayerBit(%d))\n"
                    "%s") % (bit, status_line("%s. You have had your fill." % title), var, bit,
                             status_line("%s. %s" % (title, line))),
            'notes': "%s (dark/aaze0043:5-8): +2 once per character (player bit %d; the source's +10 rescaled)."
                     % (title, bit)}


HOUSES = [
    # (source, house, title, stage qbit, closed text)
    ('platform:kalindra_throne', 4501, 'The Empty Throne', 'stage1',
     "Your hand passes through the throne. The castle is not quite here."),
    ('door:captain_quarters', 4502, "Captain's Quarters", 'stage2',
     "A shimmering wall seals the second floor. Something behind it sighs."),
    ('door:megan_room', 4503, "Megan's Room", 'stage2',
     "A shimmering wall seals the second floor. Something behind it sighs."),
    ('door:observatory', 4504, 'The Observatory', 'stage2',
     "A shimmering wall seals the second floor. Something behind it sighs."),
    ('door:guido_cell', 4505, "Guido's Cell", 'stage3', "The dungeon stair ends in shimmering nothing."),
    ('door:chapel', 4506, 'Chapel of the Queen', 'stage4', "The third floor shimmers, half here. Not yet."),
    ('door:treasury', 4507, 'The Royal Treasury', 'stage4', "The third floor shimmers, half here. Not yet."),
    ('door:training', 4508, "The Queen's Proving Hall", 'stage4', "The third floor shimmers, half here. Not yet."),
    ('door:forge', 4509, "The Queen's Forge", 'stage4', "The third floor shimmers, half here. Not yet."),
    ('door:stables', 4510, 'Kalindra Stables', 'stage4', "Ghostly horses stamp in ghostly stalls. Not yet."),
    ('door:guard_barracks', 4511, "The Queen's Guard", 'stage4', "The third floor shimmers, half here. Not yet."),
]

TOUGH_WRONG = "A tougher safe than the others. Three dials."

EVENTS = [
    # ---- arrival and the stages
    {'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
     'condition': {'all': [{'qbit': 'stage1'}, {'not': {'qbit': 'arrived_once'}}]},
     'effects': [hook('m19.first_entry'), {'qbit': 'arrived_once'}],
     'notes': "M19's first arrival in the restored castle (A3's m19.first_entry), once (arrived_once 117320)."},
    {'id': 'evt:enter', 'preset': 'text', 'trigger': 'load', 'text': "Castle Kalindra.",
     'notes': "Every entry: a status line."},
    {'id': 'evt:stage1', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'stage1'},
     'opens': ['door:portcullis'], 'effects': [{'passable': 'door:illusion'}],
     'notes': "Stage 1 (m19.stage1 111381): the gate's portcullis up; the coat closet's illusory wall passable."},
    {'id': 'evt:stage2', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'stage2'},
     'opens': ['door:cloud'],
     'effects': [{'show_actors': g} for g in STAGE_GROUPS[2]] + [sounds_off('sound:phase_cloud')],
     'notes': "Stage 2 (m19.stage2 111382): the Cloud Stairs take a foot; the second floor's spirits shown."},
    {'id': 'evt:stage3', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'stage3'},
     'opens': ['door:dstair'],
     'effects': [{'show_actors': g} for g in STAGE_GROUPS[3]] + [sounds_off('sound:phase_dstair')],
     'notes': "Stage 3 (m26.stage3 111521): the dungeon stair; the liches, the Tomb Terrors, the well's dragons and "
              "Scraps shown."},
    {'id': 'evt:stage4', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'stage4'},
     'opens': ['door:upper', 'door:yard'],
     'effects': [{'show_actors': g} for g in STAGE_GROUPS[4]]
     + [sounds_off('sound:shimmer_entrance', 'sound:phase_upper')],
     'notes': "Stage 4 (m26.stage4 111522): the upper stair and the stable yard; Blackfang's vampires shown."},
] + [
    # The castle shifts (xeen_phase_shift, AUDIO.md 62517): once per stage, a second after the first entry that finds
    # it (the highest stage set only, so a party that skipped a stage hears one shimmer, not two).
    {'id': 'evt:phase_shift%d' % n, 'preset': 'script', 'trigger': 'timer', 'every': 1,
     'condition': {'all': [{'qbit': 'stage%d' % n}] + ([{'not': {'qbit': 'stage%d' % (n + 1)}}] if n < 4 else [])
                   + [{'not': {'map_var': 'phase_seen%d' % n}}]},
     'effects': [{'lua': 'evt.PlaySoundName("xeen_phase_shift")'},
                 {'set': {'var': {'map_var': 'phase_seen%d' % n}, 'value': 1}}],
     'notes': "The castle comes further into phase (stage %d): the glassy shimmer at the party, once." % n}
    for n in (1, 2, 3, 4)
] + [
    {'id': 'evt:mist_cloud', 'preset': 'text', 'trigger': 'step', 'source': 'plate:mist_cloud',
     'condition': {'not': {'qbit': 'stage2'}}, 'text': MIST, 'seconds': 4,
     'notes': "Original line (dark/aaze0041:10) before stage 2."},
    {'id': 'evt:mist_upper', 'preset': 'text', 'trigger': 'step', 'source': 'plate:mist_upper',
     'condition': {'not': {'qbit': 'stage4'}}, 'text': MIST, 'seconds': 4,
     'notes': "Original line (dark/aaze0041:10) before stage 4."},
    {'id': 'evt:mist_dstair', 'preset': 'text', 'trigger': 'step', 'source': 'plate:mist_dstair',
     'condition': {'not': {'qbit': 'stage3'}}, 'text': MIST, 'seconds': 4,
     'notes': "Original line (dark/aaze0041:10) before stage 3."},
    {'id': 'evt:leaf_cloud', 'preset': 'door', 'source': 'door:cloud', 'title': 'Cloud Stairs', 'action': 'open',
     'condition': {'qbit': 'stage2'}, 'locked_text': MIST},
    {'id': 'evt:leaf_upper', 'preset': 'door', 'source': 'door:upper', 'title': 'Upper stair', 'action': 'open',
     'condition': {'qbit': 'stage4'}, 'locked_text': MIST},
    {'id': 'evt:leaf_dstair', 'preset': 'door', 'source': 'door:dstair', 'title': 'Dungeon stair', 'action': 'open',
     'condition': {'qbit': 'stage3'}, 'locked_text': "The dungeon stair ends in shimmering nothing."},
    {'id': 'evt:leaf_yard', 'preset': 'door', 'source': 'door:yard', 'title': 'Shimmering wall', 'action': 'open',
     'condition': {'qbit': 'stage4'},
     'locked_text': "The wall shimmers like heat over a road. Beyond it horses stamp, and you cannot reach them."},
    # ---- the exit
    {'id': 'evt:exit', 'preset': 'exit', 'source': 'exit:d1_gate', 'title': 'Exit Castle Kalindra',
     'notes': "Out to D1 at A6's return point before the gate (exit:d1_gate): the game's own window (D-24); the "
              "source's 'Exit Castle Kalindra?' (dark/aaze0041:0) is the title."},
    # ---- doors
    {'id': 'evt:door_throne', 'preset': 'door', 'source': 'door:throne', 'title': 'Throne Room'},
    {'id': 'evt:door_banquet', 'preset': 'door', 'source': 'door:banquet', 'title': 'Banquet Hall'},
    {'id': 'evt:door_closet', 'preset': 'door', 'source': 'door:closet', 'title': 'Coat Closet'},
    {'id': 'evt:door_armory', 'preset': 'door', 'source': 'door:armory', 'title': 'Armory'},
    {'id': 'evt:door_sleeping', 'preset': 'door', 'source': 'door:sleeping', 'title': 'Sleeping Chambers'},
    {'id': 'evt:door_vaults', 'preset': 'door', 'source': 'door:vaults', 'title': 'Vaults'},
    {'id': 'evt:door_bedchamber', 'preset': 'door', 'source': 'door:bedchamber', 'title': 'Royal Bed Chamber'},
    {'id': 'evt:door_cells', 'preset': 'door', 'source': 'door:cells', 'title': 'Door'},
    {'id': 'evt:door_vault_secret', 'preset': 'door', 'source': 'door:vault_secret', 'title': 'Wall'},
    {'id': 'evt:portcullis', 'preset': 'door', 'source': 'door:portcullis', 'title': 'Portcullis', 'action': 'open',
     'condition': {'qbit': 'stage1'}, 'locked_text': "The portcullis will not move. Beyond it the castle shimmers."},
    # ---- the throne room's safes (m19.safes): the first opened runs the hook and gives the two disks; then chests
    {'id': 'evt:safe_w', 'preset': 'chest', 'source': 'chest:safe_w', 'title': 'Chest',
     'condition': {'qbit': 'm19_safes'}, 'else_effects': [give_disks('m19.safes', 2)],
     'notes': "m19.safes (stage 1, D-26: a trapped chest any party opens): the first use runs the hook (its text, "
              "safes_opened 111383) and the map gives the two Energy Disks (map_gives); from the next use it opens."},
    {'id': 'evt:safe_e', 'preset': 'chest', 'source': 'chest:safe_e', 'title': 'Chest',
     'condition': {'qbit': 'm19_safes'}, 'else_effects': [give_disks('m19.safes', 2)],
     'notes': "The other safe: the same hook (whichever is opened first)."},
    # ---- the tougher safes (Guido's 10-11-12)
    {'id': 'evt:armory_safe', 'preset': 'chest', 'source': 'chest:armory_safe', 'title': 'Chest',
     'question': {'message': "A safe with three dials.", 'ask': "Combination?",
                  'answers': ['10-11-12', '101112'],
                  'wrong_effects': [{'text': TOUGH_WRONG}]},
     'condition': {'not': {'map_var': 'armory_safe'}},
     'effects': [{'set': {'var': {'map_var': 'armory_safe'}, 'value': 1}}],
     'else_effects': [{'open_chest': 'chest:armory_safe'}],
     'notes': "The armory's tougher safe (D-26): 10-11-12 opens it (Guido's tip, aaze0044:47); a wrong answer: "
              "'A tougher safe than the others. Three dials.'"},
    {'id': 'evt:vault_safe', 'preset': 'chest', 'source': 'chest:vault_safe', 'title': 'Chest',
     'question': {'message': "A safe with three dials.", 'ask': "Combination?",
                  'answers': ['10-11-12', '101112'],
                  'wrong_effects': [{'text': TOUGH_WRONG}]},
     'condition': {'not': {'map_var': 'vault_safe'}},
     'effects': [{'set': {'var': {'map_var': 'vault_safe'}, 'value': 1}}],
     'else_effects': [{'open_chest': 'chest:vault_safe'}],
     'notes': "The dungeon vault's tougher safe: 10-11-12."},
    {'id': 'evt:chest_hoard', 'preset': 'chest', 'source': 'chest:hoard', 'title': 'Chest'},
    # ---- the disk safes (m24) and the crown safe (m27)
    {'id': 'evt:disk_safe', 'preset': 'script', 'source': 'panel:disk_safe', 'title': 'Safe',
     'condition': {'all': [{'not': {'qbit': 'm24_safes'}}, can('m24.disk_safes')]},
     'question': {'message': "A combination safe. Six dials.", 'ask': "Combination?",
                  'answers': ['64-52-31', '645231'],
                  'wrong_effects': [{'text': "The dials click round and the safe stays shut."}]},
     'effects': [give_disks('m24.disk_safes', 4)], 'else_effects': [hook('m24.disk_safes')],
     'notes': "m24.disk_safes (stage 2): after Dimitri (m24.done) the six dials ask; 64-52-31 runs the hook and the map "
              "gives four Energy Disks; before m24.done the hook's fail text, after it the else text."},
    {'id': 'evt:crown_safe', 'preset': 'script', 'source': 'panel:queens_mirror', 'title': "The Queen's mirror",
     'condition': {'all': [{'not': {'qbit': 'm27_crown'}}, can('m27.crown_safe')]},
     'question': {'message': "Behind the Queen's mirror, a wall safe with six dials.", 'ask': "Combination?",
                  'answers': ['3-31-62', '33162'],
                  'wrong_effects': [{'text': "The dials click round and the safe stays shut."}]},
     'effects': [hook('m27.crown_safe')], 'else_effects': [hook('m27.crown_safe')],
     'notes': "m27.crown_safe (stage 4, queen_found): 3-31-62 runs the hook (the crown); else its fail or else text."},
    {'id': 'evt:mirror_switch', 'preset': 'script', 'source': 'switch:mirror_switch', 'title': 'Button',
     'question': {'message': "Activate Mirror Portals?", 'ask': "Yes or no?", 'answers': ['Yes', 'Y']},
     'effects': [hook('m26.mirror_switch')],
     'notes': "m26.mirror_switch (dark/aaze0043:16, stage 4): wakes the Darkside mirrors."},
    brew('queens_brew', "Queen's Brew", BIT_QUEENS_BREW, 'BasePersonality', "+2 Personality (permanent)."),
    brew('knights_brew', "Knight's Brew", BIT_KNIGHTS_BREW, 'BaseMight', "+2 Might (permanent)."),
    # ---- the dungeon
    {'id': 'evt:ledger', 'preset': 'script', 'source': 'platform:ledger_desk', 'title': 'Prisoner ledger',
     'lua': "XeenQuests.hook(\"t2-a.cells\")",
     'notes': "t2-a.cells: the prisoner list (dark/aaze0044:8, A3's text with the two added liches)."},
    {'id': 'evt:liches_slain', 'preset': 'script', 'trigger': 'timer', 'every': 2, 'once': True,
     'condition': {'kills': {'group': 31}}, 'lua': "XeenQuests.hook(\"t2-a.liches\")",
     'notes': "t2-a.liches: the cell block's five liches (group 31) dead sets liches_slain 114521."},
    {'id': 'evt:kennel_lever', 'preset': 'switch', 'source': 'switch:kennel_lever', 'title': 'Lever',
     'toggles': ['door:kennel'], 'text': "Chains rattle: the kennel's portcullis moves.",
     'notes': "The kennel's portcullis (D-26): the lever under 'Don't let Scraps out!'."},
    text('kennel_gate', 'door:kennel', 'Portcullis', "A heavy portcullis. A lever beside it, under a note."),
    text('note_beware', 'panel:note_beware', 'A note', "A note reads: Beware of Scraps!"),
    text('note_feed', 'panel:note_feed', 'A note', "A note reads: Don't feed Scraps."),
    text('note_out', 'panel:note_out', 'A note', "A note reads: Don't let Scraps out!"),
    # ---- the talking: Carl the Mason, the mirror, the houses
    {'id': 'evt:carl', 'preset': 'script', 'source': 'platform:carl_bench', 'title': 'Carl the Mason',
     'lua': "evt.SpeakNPC(%d)" % CARL_NPC,
     'notes': "Carl the Mason (NPC 5014, D-26: 'just keep walking', aaze0041:34-35): the studio cannot give a placed "
              "indoor monster its NPC, so his bench speaks for him (DD-01's and DD-02's way)."},
    {'id': 'evt:mirror', 'preset': 'script', 'source': 'panel:kalindra_mirror',
     'title': 'The Mirror of Castle Kalindra', 'lua': "Xeen.useMirror(4512, eventId, continueStep)",
     'notes': "A4's mirror 4512 (opens on m26.stage4; its closed text before)."},
    # ---- flavour
    text('hooks', 'panel:hooks', 'Coat hooks', "Coat hooks. A cloak that went out of fashion a century ago."),
    text('banquet_table', 'platform:banquet_table', 'Banquet table', "A table laid for a feast nobody ate. The bread "
         "has turned to stone.", window=False),
    text('kitchen_table', 'platform:kitchen_table', 'Kitchen table', "Strings of sun-dried lizard innards hang over "
         "the table. They have kept.", window=False),
    text('trough', 'platform:trough', 'Trough', "Clean water. The horses came back with the castle.", window=False),
]
for src, house, title, stage, closed in HOUSES:
    key = src.split(':')[1]
    if src.startswith('door:') and key not in ('treasury', 'guido_cell'):
        EVENTS.append({'id': 'evt:house_%s_r' % key, 'preset': 'script', 'source': 'panel:%s_r' % key,
                       'title': title, 'condition': {'qbit': stage},
                       'effects': [{'lua': 'evt.EnterHouse(%d)' % house}], 'else_effects': [{'message': closed}],
                       'notes': "The right wing of house %d's door." % house})
    EVENTS.append({'id': 'evt:house_%s' % key, 'preset': 'script', 'source': src, 'title': title,
                   'condition': {'qbit': stage}, 'effects': [{'lua': 'evt.EnterHouse(%d)' % house}],
                   'else_effects': [{'message': closed}],
                   'notes': "A4's house %d (%s), open from %s; A4's closed text before." % (house, title, stage)})
SIGNS = [('throne', 'Throne Room'), ('north', 'North Wing'), ('banquet', 'Banquet Hall'),
         ('stairs', 'Cloud Stairs'), ('kitchen', 'Kitchen'), ('south', 'South Wing'), ('armory', 'Armory'),
         ('sleeping', 'Sleeping Chambers'), ('vaults', 'Vaults'), ('bed', 'Royal Bed Chamber'),
         ('maxsec', 'Maximum Security')]
for key, name in SIGNS:
    EVENTS.append(text('sign_' + key, 'panel:sign_' + key, name, name, window=False))
EVENTS.append(text('crest_gate', 'panel:crest_gate', "Kalindra's crest",
                   "A silver crescent and a white rose on purple: Queen Kalindra's arms.", window=False))

WIRING = {'format': 0, 'variables': ['armory_safe', 'vault_safe'] + ['phase_seen%d' % n for n in (1, 2, 3, 4)],
          'events': EVENTS,
          'notes': "DD-03's events (gen.py): the four stages (load events), the mist lines, the safes (m19.safes, "
                   "m24.disk_safes, m27.crown_safe, the tougher safes), the mirror switch, the brews, the prisoner "
                   "ledger and the liches (T2-A), Scraps' lever, Carl the Mason, the houses 4501-4512, the exit."}

ATMOSPHERE = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'xeen_darkside_fading'},
              'notes': "The stable yard is open to Darkside's sky (its ceiling's sky faces; D-22.6's route as "
                       "XD-13): the fading preset of M17-M27, since the yard opens at stage 4 (M26)."}

# ---------------------------------------------------------------------------------------------------------------------
# Project

PROJECT = {
    'format': 0, 'id': 'xeen_dd03', 'name': 'Castle Kalindra', 'world': 'xeen', 'kind': 'indoor',
    'profile': 'dungeon', 'map_code': 'DD-03', 'units': {'plan_grid': 512},
    'extent': {'footprint_cells': F(16, 25), 'climbs': 'n'},
    'map_stats': {
        'id': MAP_ID, 'bolster': 'LowerToEqual', 'encounter_chance': 0, 'treasure_level': 4, 'trap_dice': 3,
        'perception_difficulty': 3, 'refill_days': 672, 'music': MUSIC, 'environment': 'stoneroom',
        'lock_difficulty': 6,
        'slots': [{'monster': 'Xeen Spirit', 'tier': 1, 'per_marker': F(2, 3), 'weight': 40},
                  {'monster': 'Xeen Lich', 'tier': 0, 'per_marker': F(1, 2), 'weight': 25},
                  {'monster': 'Xeen Vampire', 'tier': 1, 'per_marker': F(2, 3), 'weight': 35}],
    },
    'neighbours': [{
        'id': 'exit:d1_gate', 'to': 'xeen_d1.odm', 'kind': 'door', 'arrival': F(*D1_ARRIVAL),
        'arrival_hint': "On D1's forecourt before Castle Kalindra's gate (entrance:dd03_gate): A6's return point, "
                        "facing west, away from the gate.",
        'direction': D1_FACING,
        'notes': "D1 installed (A6). D1's gate (event 123) lands at this map's start: (-1600, 0, 0) facing east (0)."}],
    'qbits': QBITS,
    'notes': "Xeen design brief, DD-03 Castle Kalindra (staged; D1; M19, M24, M26, M27, T2-A), class M, from the MU-6 "
             "graph (devdocs/xeen/mockups/act3_graphs/dd03.graph.yml) with decider D-26 "
             "(mockups/act3_a8_decisions_a.md). Party 30-40, levels 26-45, Scraps 70 optional; 54 placed monsters "
             "on the world's rows (spirits 11261-11263, Lich 11280, Bone Dragon 11670, vampires 11290-11291; Scraps "
             "11673), no spawn points, encounter chance 0; treasure 4 (the kennel's hoard 5); music 29. Stages by "
             "A3's qbits 111381, 111382, 111521, 111522; the map's arrived_once 117320 (provisional block "
             "117320-117359). Player bits 11304 (Queen's Brew), 11305 (Knight's Brew), provisional (11320-11321 are D3's).",
}

# ---------------------------------------------------------------------------------------------------------------------
# Plan (L1 words; L2 adds extents, floors and heights)

HALL_T = "Royal kit restored: MM7 7d09 cream marble t3s2b1 over the knotwork dado t3s2b, floor t3s2fl1, ceiling t3s2c"
ROYAL_T = "The cream marble t3s2b1 over Castle Harmondale's flags tfb09"
WING_T = "MM7 Castle Gryphonheart 7d33: brown cobble chb1, flags 7tfb1, dark ceiling tfb2 (still out of phase)"
DUNG_T = "7d33's dark cobble dchb1, dark flags 7tfb11"
GATE_T = "Castle Ironfist's white ashlar hcwall, grey flags cstyl"
THEME_T = {'theme:hall': HALL_T, 'theme:royal': ROYAL_T, 'theme:wing': WING_T, 'theme:dungeon': DUNG_T,
           'theme:gate': GATE_T, 'theme:yard': GATE_T + ", open to the sky"}
NAMES = {TG: 'Tomb Guard (11261)', GR: 'Ghost Rider (11263)', TT: 'Tomb Terror (11262)', LICH: 'Lich (11280)',
         BD: 'Bone Dragon (11670)', VAMP: 'Vampire (11291)', GV: 'Gnome Vampire (11290)', SCRAPS: 'Scraps (11673)'}
LEVEL = {TG: 26, GR: 27, TT: 40, LICH: 35, BD: 45, VAMP: 40, GV: 32, SCRAPS: 70}

PURPOSE = {
    'gate': "Arrival and the exit to D1 (the game's window, 'Exit Castle Kalindra?'); the portcullis up from stage 1; "
            "m19.first_entry once.",
    'entrance': "Doors to the throne room, the north wing and the stable yard's phase wall (stage 4).",
    'north_wing': "Signed 'North Wing'; spirits in the half-phased wing.",
    'cloud_foot': "The Cloud Stairs: 'Your foot passes through the stairs as though they were mist.' until stage 2.",
    'cloud_flight': "Up to the second floor (stage 2).",
    'banquet': "A table laid for a feast nobody ate; spirits.",
    'kitchen': "Barrels, a larder; Carl the Mason (5014): 'just keep walking'; the servants' passage to the throne.",
    'throne': "The Empty Throne (house 4501's door: Gem, Errol); two trapped safes behind tapestries (m19.safes: two "
              "Energy Disks).",
    'south_wing': "Signed 'South Wing'; Ghost Riders.",
    'closet': "A dead end: its back wall is an illusion (Carl's 'just keep walking').",
    'armory': "Racks; a tougher safe (10-11-12, Guido's tip).",
    'dstair_head': "Down: 'The dungeon stair ends in shimmering nothing.' until stage 3.",
    'dstair': "Down to the guardroom (stage 3).",
    'yard': "Open sky behind the stage-4 phase wall: Kalindra Stables 4510, the Mirror of Castle Kalindra 4512.",
    'l2_landing': "The Cloud Stairs' head.",
    'upper_foot': "Up to the third floor: the mist line until stage 4.",
    'upper_flight': "Up to the third floor (stage 4).",
    'residences': "Captain's Quarters 4502 (Dimitri, M24, T2-A), Megan's Room 4503, the Observatory 4504.",
    'sleeping': "The household's dormitory; spirits.",
    'phase_gallery': "Its outer wall still shimmers; spirits.",
    'vaults': "The disk safes (m24.disk_safes, 64-52-31, after Dimitri; 4 Energy Disks).",
    'l3_landing': "The upper stair's head.",
    'bell_tower': "Ropes and a cracked bell; the vampires' roost.",
    'attic': "Rafters still half out of phase; the last spirits; the roof walk to the Queen's court.",
    'court3': "Five house doors (stage 4): 4506, 4507, 4508, 4509, 4511.",
    'queens_gallery': "Portraits of the Queen; Blackfang's servants waiting for her.",
    'bedchamber': "The crown safe behind the mirror (m27.crown_safe, 3-31-62); the Queen's Brew and the Knight's Brew "
                  "(+2 Personality, +2 Might); 'Activate Mirror Portals?' (m26.mirror_switch).",
    'guardroom': "The stair's foot; the prisoner ledger (t2-a.cells).",
    'cells': "Five cells, five liches (T2-A: t2-a.liches when the group is dead).",
    'maxsec': "Guido's Cell 4505; the kennel's portcullis and its lever; the three notes on Scraps.",
    'kennel_stair': "A stair 288 high and 320 wide, lower than Scraps (D-32).",
    'kennel': "Scraps (70, optional) on the bones of his dinners; the castle's hoard (5).",
    'vault_d': "Confiscated goods; a tougher safe (10-11-12); a secret door to Maximum Security.",
    'well': "Two named Bone Dragons; its openings 256 high (D-32).",
}
STAGE_OF_ROOM = {}
for k in ('l2_landing', 'upper_foot', 'residences', 'sleeping', 'phase_gallery', 'vaults', 'cloud_flight'):
    STAGE_OF_ROOM[k] = 2
for k in ('guardroom', 'cells', 'maxsec', 'kennel_stair', 'kennel', 'vault_d', 'well', 'dstair'):
    STAGE_OF_ROOM[k] = 3
for k in ('l3_landing', 'bell_tower', 'attic', 'court3', 'queens_gallery', 'bedchamber', 'upper_flight', 'yard'):
    STAGE_OF_ROOM[k] = 4


def room_box(r):
    xs = [p[0] for p in r['outline']]
    ys = [p[1] for p in r['outline']]
    f0 = r['floor']
    f1 = r['slope']['to'] if 'slope' in r else f0
    c = r['ceiling']
    return (max(xs) - min(xs), max(ys) - min(ys)), (f0 if f0 == f1 else F(f0, f1)), c - max(f0, f1) if 'slope' not \
        in r else c - f0


def placed(row, count, level, notes=None):
    d = {'actor': NAMES[row], 'groups': 1, 'per_marker': F(count, count), 'levels': F(level, level), 'placed': True}
    if notes:
        d['notes'] = notes
    return d


SPACES = []
for r in ROOMS:
    k = r['id'].split(':')[1]
    ext, floor, clear = room_box(r)
    kind = 'corridor' if k in ('north_wing', 'south_wing', 'residences', 'phase_gallery', 'attic', 'cloud_flight',
                               'upper_flight', 'dstair', 'kennel_stair') else 'room'
    size = 'L' if ext[0] * ext[1] > 2_000_000 else ('M' if ext[0] * ext[1] > 600_000 else 'S')
    d = {'id': r['id'], 'name': r['name'], 'kind': kind, 'size': size, 'extent': F(*ext), 'floor': floor,
         'clear_height': clear, 'purpose': PURPOSE[k] + (" (stage %d)" % STAGE_OF_ROOM[k] if k in STAGE_OF_ROOM
                                                          else ""), 'theme': THEME_T[r['theme']]}
    pops = {}
    for m in MONSTERS:
        if m['room'] == r['id'] and m['monster'] != CARL_BODY:
            pops[m['monster']] = pops.get(m['monster'], 0) + 1
    if pops:
        d['population'] = [placed(row, n, LEVEL[row]) for row, n in pops.items()]
    else:
        d['empty'] = True
    tre = [c for c in CHESTS if c['room'] == r['id']]
    if tre:
        d['treasure'] = [{'kind': 'chest', 'count': len(tre), 'tier': tre[0]['treasure_level'],
                          'items': F(2, 3), 'notes': tre[0]['notes']}]
    if k == 'gate':
        d['safe'] = True
    SPACES.append(d)


def link(i, a, b, kind, **kw):
    d = {'id': 'link:' + i, 'from': 'room:' + a, 'to': 'room:' + b, 'kind': kind}
    d.update(kw)
    return d


LINKS = [
    link('gate_entrance', 'gate', 'entrance', 'door', motion='slide', notes="The portcullis: up from stage 1."),
    link('entrance_throne', 'entrance', 'throne', 'door', motion='slide', notes="Double doors."),
    link('entrance_north', 'entrance', 'north_wing', 'open'),
    link('north_cloud', 'north_wing', 'cloud_foot', 'open'),
    link('cloud', 'cloud_foot', 'l2_landing', 'stairs', rise=640,
         notes="The Cloud Stairs (cloud_flight): the phase leaf at the foot opens at stage 2."),
    link('north_banquet', 'north_wing', 'banquet', 'door', motion='slide', notes="Double doors."),
    link('banquet_kitchen', 'banquet', 'kitchen', 'open'),
    link('kitchen_throne', 'kitchen', 'throne', 'open', notes="The servants' passage."),
    link('throne_south', 'throne', 'south_wing', 'open'),
    link('throne_closet', 'throne', 'closet', 'door', motion='slide'),
    link('closet_armory', 'closet', 'armory', 'secret_door', notes="The illusory wall: walk through it."),
    link('armory_south', 'armory', 'south_wing', 'door', motion='slide'),
    link('entrance_yard', 'entrance', 'yard', 'door', motion='slide', notes="The phase wall: open at stage 4."),
    link('south_dhead', 'south_wing', 'dstair_head', 'open'),
    link('dstair', 'guardroom', 'dstair_head', 'stairs', rise=640,
         notes="The dungeon stair (dstair): the phase leaf at its head opens at stage 3."),
    link('l2_upper', 'l2_landing', 'upper_foot', 'open'),
    link('upper', 'upper_foot', 'l3_landing', 'stairs', rise=640,
         notes="The upper stair (upper_flight): the phase leaf at its foot opens at stage 4."),
    link('upper_res', 'upper_foot', 'residences', 'open'),
    link('res_sleeping', 'residences', 'sleeping', 'door', motion='slide'),
    link('sleeping_phase', 'sleeping', 'phase_gallery', 'open'),
    link('phase_vaults', 'phase_gallery', 'vaults', 'door', motion='slide', notes="Iron double doors."),
    link('l3_gallery', 'l3_landing', 'queens_gallery', 'open'),
    link('l3_bell', 'l3_landing', 'bell_tower', 'open'),
    link('gallery_bed', 'queens_gallery', 'bedchamber', 'door', motion='slide', notes="Double doors."),
    link('gallery_court', 'queens_gallery', 'court3', 'open'),
    link('bell_attic', 'bell_tower', 'attic', 'open', notes="The roof walk."),
    link('attic_court', 'attic', 'court3', 'open'),
    link('guard_cells', 'guardroom', 'cells', 'door', motion='slide'),
    link('cells_maxsec', 'cells', 'maxsec', 'open'),
    link('kennel', 'maxsec', 'kennel', 'door', motion='slide',
         notes="The kennel's portcullis (lever) and the low stair (kennel_stair), 288 high (D-32)."),
    link('guard_well', 'guardroom', 'well', 'open', notes="256 high (D-32)."),
    link('vault_well', 'vault_d', 'well', 'open', notes="256 high (D-32)."),
    link('maxsec_vault', 'maxsec', 'vault_d', 'secret_door'),
]


def plan(level):
    d = {
        'format': 0, 'level': 'L3' if level == 'L4' else level,
        'pitch': "Queen Kalindra's white castle, pulled out of phase by Alamar, comes back into the world a floor at a "
                 "time as the party brings Ellinger Energy Disks. At first only the ground floor is solid: an empty "
                 "throne under dust like snow, wings where spirits still pass through the walls, a closet whose back "
                 "wall is not there. Then the Cloud Stairs take a foot and the second floor's people come back; then "
                 "the dungeon stair, with caged liches, two dragons in the old well and a dragon called Scraps in "
                 "his kennel; last the Queen's floor, where Count Blackfang's vampires wait for her, and the open "
                 "stable yard with the castle's mirror.",
        'purpose': "Story M19 (stage 1-2: the throne room's safes), M24 (Dimitri, the disk safes 64-52-31), M26 (stage "
                   "3-4, the mirror switch), M27 (the crown safe 3-31-62), T2-A (the liches); A4's castle services by "
                   "stage (houses 4501-4512). Party 30-40; 54 monsters at 26-45 (24 in Act III, 30 in Act IV), "
                   "Scraps 70 optional; treasure 4, the kennel's hoard 5.",
        'mood': "Cream marble and purple banners, lamplit; cobbled wings where the walls shimmer violet and spirits "
                "drift; a dark dungeon of cells; wind in the bell tower and the open yard.",
        'datum': 'arrival',
        'spaces': [dict(s) for s in SPACES],
        'links': LINKS,
        'states': [
            {'id': 'state:stage1', 'condition': {'qbit': 'stage1'}, 'opens': ['link:gate_entrance'],
             'notes': "m19.stage1 (5 disks): the gate and the ground floor solid (D1's gate refuses before it)."},
            {'id': 'state:stage2', 'condition': {'qbit': 'stage2'}, 'opens': ['link:cloud'],
             'notes': "m19.stage2 (10 disks): the Cloud Stairs, the second floor and its spirits."},
            {'id': 'state:stage3', 'condition': {'qbit': 'stage3'}, 'opens': ['link:dstair'],
             'notes': "m26.stage3 (15 disks): the dungeon stair; Guido; the liches, dragons and Scraps."},
            {'id': 'state:stage4', 'condition': {'qbit': 'stage4'}, 'opens': ['link:upper', 'link:entrance_yard'],
             'notes': "m26.stage4 (20 disks): the upper stair and the stable yard; the services; the mirror."},
        ],
        'loops': [
            {'id': 'loop:ground', 'spaces': ['room:entrance', 'room:north_wing', 'room:banquet', 'room:kitchen',
                                             'room:throne'],
             'notes': "Round the banquet hall by the servants' passage."},
            {'id': 'loop:south', 'spaces': ['room:throne', 'room:closet', 'room:armory', 'room:south_wing'],
             'notes': "Through the coat closet's illusory wall."},
            {'id': 'loop:top', 'spaces': ['room:l3_landing', 'room:queens_gallery', 'room:court3', 'room:attic',
                                          'room:bell_tower'], 'notes': "By the roof walk."},
            {'id': 'loop:dungeon', 'spaces': ['room:guardroom', 'room:cells', 'room:maxsec', 'room:vault_d',
                                              'room:well'], 'notes': "Through the vault's secret door."}],
        'entrances': [{'id': 'entrance:gate', 'space': 'room:gate', 'kind': 'both', 'neighbour': 'exit:d1_gate',
                       'facing': 'e', 'how': "Inside Kalindra's gate, facing in."}],
        'critical_path': ['room:gate', 'room:entrance', 'room:throne', 'room:entrance', 'room:north_wing',
                          'room:cloud_foot', 'room:cloud_flight', 'room:l2_landing', 'room:upper_foot',
                          'room:residences', 'room:sleeping', 'room:phase_gallery', 'room:vaults'],
        'return_path': ['room:vaults', 'room:phase_gallery', 'room:sleeping', 'room:residences', 'room:upper_foot',
                        'room:l2_landing', 'room:cloud_flight', 'room:cloud_foot', 'room:north_wing',
                        'room:entrance', 'room:gate'],
        'goals': [
            {'id': 'goal:safes', 'space': 'room:throne', 'kind': 'take', 'what': "The two Energy Disks in the throne "
             "room's safes (m19.safes)."},
            {'id': 'goal:disk_safes', 'space': 'room:vaults', 'kind': 'take', 'what': "Four Energy Disks at 64-52-31 "
             "(m24.disk_safes)."},
            {'id': 'goal:liches', 'space': 'room:cells', 'kind': 'kill', 'what': "The five liches (t2-a.liches)."},
            {'id': 'goal:mirror', 'space': 'room:bedchamber', 'kind': 'use', 'what': "Activate Mirror Portals "
             "(m26.mirror_switch); the crown at 3-31-62 (m27.crown_safe)."}],
        'atmosphere': "Lamplit marble (ambient 18-22), the half-phased wings dim and violet (14), the dungeon dark "
                      "(10-14), the stable yard open to Darkside's sky. Music 29. Sounds: the phase walls humming, a "
                      "pot in the kitchen, wind in the bell tower, the yard and the old well.",
        'diagram': {'file': 'diagram.txt'},
        'totals': {'chests': len(CHESTS), 'doors': len(DOORS), 'fixed_actors': len(MONSTERS), 'loops': 4,
                   'monsters_about': 55, 'rooms': len(ROOMS), 'sectors': len(ROOMS), 'spawn_points': 0,
                   'floor_area_millions': 50},
        'notes': "Class M (MAPS, Dungeons): 20-45 sectors, 30-90 M units², 45-75 monsters, 3-7 chests, 6-16 doors. The "
                 "graph's 33 spaces as 34 rooms (each flight a room of its own, the kennel's low stair). D-26: each "
                 "stage's monsters hidden until its qbit, every stage gate a leaf in xkshimmer, the liches named, two "
                 "named Bone Dragons in the old well, Carl the Mason in the kitchen, the stable yard open to the sky.",
    }
    if level == 'L1':
        for s in d['spaces']:
            s.pop('extent', None)
            s.pop('clear_height', None)
        d.pop('totals')
    elif level in ('L3', 'L4'):
        d['sketch'] = {'file': 'rooms.yml', 'grid': 512}
    return d


DIAGRAM = """ Floor 3 (1280, stage 4)
   [Bell tower: vampires]--[landing]--[THE QUEEN'S GALLERY: vampires]==dd==[ROYAL BED CHAMBER: crown safe, brews,
        |  roof walk           |              |                                   'Activate Mirror Portals?']
   [Shimmering attic]----------+------[THE QUEEN'S COURT: houses 4506-4509, 4511]
                               |  upper stair (mist until stage 4)
 Floor 2 (640, stage 2)        |
   [landing]--[upper stair foot]--[Captain's corridor: houses 4502-4504]
        |                                  |door
        |  Cloud Stairs        [Sleeping Chambers]--[Phase gallery]==dd==[VAULTS: disk safes 64-52-31]
 Floor 0 (0, stage 1)
   [Cloud Stairs foot (mist until stage 2)]--[North Wing]==dd==[Banquet Hall]--[Kitchen: Carl]
                                                 |                                 | servants' passage
  D1 gate--[Gate passage]=portcullis=[ENTRANCE HALL]==dd==[THRONE ROOM: throne 4501, 2 safes]--door--[Coat Closet]
                                                 |                  |                                  : illusion
                                         phase wall (stage 4)  [South Wing]--door--------------------[Armory: safe]
                                       [STABLE YARD (sky): stables 4510, mirror 4512]  |
                                                                        [dungeon stair (mist until stage 3)]
 Floor -1 (-640, stage 3)                                                               |
   [Maximum Security: Guido 4505, lever]--[The cell block: 5 liches]==door==[Guardroom: ledger]
        |portcullis   ## secret                                               | low mouth
   [kennel stair, 288 high]  [Dungeon vault: safe]--low--[Old well: 2 Bone Dragons]
        |
   [SCRAPS' KENNEL (-1152): Scraps, the hoard]

 == door   dd double doors   ## secret door   : illusory wall
"""


def write(level):
    d = OUT + '/' + level
    os.makedirs(d, exist_ok=True)
    dump(d + '/project.yml', PROJECT)
    dump(d + '/plan.yml', plan(level))
    open(d + '/diagram.txt', 'w').write(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d + '/rooms.yml', {'format': 0, 'themes': THEMES, 'defaults': {'theme': 'theme:hall', 'ambient': 18},
                                'rooms': ROOMS, 'openings': OPENINGS,
                                'notes': "DD-03 at L3/L4: 34 rooms on four floors in the plan's frame (x east, y "
                                         "north). Written by output/studio_cal/dd03/tools/gen.py."})
    if level == 'L4':
        dump(d + '/objects.yml', OBJECTS)
        dump(d + '/wiring.yml', WIRING)
        dump(d + '/atmosphere.yml', ATMOSPHERE)


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
