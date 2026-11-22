#!/usr/bin/env python3
"""XD-08 Tomb of a Thousand Terrors: writes the project files of devdocs/xeen/briefs/xd08/L1..L4 (lane A7, sub-agent
xeen-a7-xd08). Route copied from level_generation/projects/xeen/xd07/gen.py.

    python3 level_generation/projects/xeen/xd08/gen.py            all four levels
    python3 level_generation/projects/xeen/xd08/gen.py L4         one level

Frame: x east, y north. The tomb (floor 0) south, the tomb door in the south wall of the entry at y 0; the crypts (-640)
north of it; the deep (-1280) further north. No room stands over another. One room is one rectangle. Ids the playtests
use are read from ids.lock.yml after each build (the build keeps it).
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/xd08'


class Flow(list):
    pass


class FlowDict(dict):
    pass


def _flow_list(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


def _flow_dict(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data, flow_style=True)


yaml.add_representer(Flow, _flow_list)
yaml.add_representer(FlowDict, _flow_dict)


def F(*v):
    return Flow(v)


def S(texture, w, h, **kw):
    d = FlowDict(texture=texture, size=Flow([w, h]))
    d.update(kw)
    return d


def rect(x0, y0, x1, y1):
    return Flow([Flow([x0, y0]), Flow([x1, y0]), Flow([x1, y1]), Flow([x0, y1])])


# ---------------------------------------------------------------------------------------------------------------------
# Numbers
MAP_STATS_ID = 9124
MUSIC = 20
QBITS = {
    'manacles_pulled': 110760,   # map: the manacles pulled in the chain room (the portcullis before the coffin vault up)
    'pay_potions': 110761,       # map: the pay chest's two Might Boosts given (D-22.2, once per game)
}
ITEMS = {'megacredit': 12192, 'might_boost': 240}
# Tomb juices (aaze0080:2-8, D-4: +2 permanent, once per character per colour): colour, stat, player bit, light colour
JUICES = [
    ('red', 'Might', 11270, (255, 40, 30)),
    ('blue', 'Personality', 11271, (40, 80, 255)),
    ('orange', 'Intellect', 11272, (255, 130, 20)),
    ('green', 'Endurance', 11273, (40, 220, 60)),
    ('yellow', 'Accuracy', 11274, (255, 230, 40)),
    ('purple', 'Speed', 11275, (170, 40, 230)),
    ('white', 'Luck', 11276, (255, 255, 255)),
]

ROOMS = {}


def room(rid, name, r, floor, ceiling, theme, **extra):
    ROOMS[rid] = dict(name=name, rect=r, floor=floor, ceiling=ceiling, theme=theme, **extra)


# The tomb (floor 0)
room('door', 'Tomb door', (-384, 0, 384, 768), 0, 512, 'tomb')
room('welcome', 'Hall of Welcome', (-768, 1024, 768, 2304), 0, 768, 'tomb_tall')
room('gallery', 'Gallery of Terrors', (1024, 1280, 4352, 2304), 0, 640, 'tomb_tall')
room('west_mourning', 'West mourning hall', (-1536, 2560, 256, 3840), 0, 640, 'tomb')
room('stocks', 'Stocks yard', (-3072, 2560, -1792, 3840), 0, 576, 'torture')
room('chain_room', 'Chain room', (512, 2560, 1536, 3328), 0, 576, 'torture')
room('maiden_niche', 'Iron maiden', (2560, 2560, 3328, 3328), 0, 576, 'torture')
room('east_mourning', 'East mourning hall', (4608, 1024, 5888, 2560), 0, 640, 'tomb')
room('cage_room', 'Hanging cage', (4352, 2816, 5376, 3584), 0, 640, 'torture')
room('shaft', 'Cage shaft', (4416, 3648, 4928, 4160), -640, 640, 'torture')
# The crypts (floor -1, -640)
room('maiden_stair', "Maiden's stair", (2688, 3584, 3200, 4608), 0, 448, 'crypt',
     slope={'to': -640, 'toward': 'north', 'steps': 20}, ceiling_slope={'to': -192, 'toward': 'north'})
room('cage_pit', 'Cage pit', (3584, 4224, 5120, 5504), -640, -128, 'crypt')
room('crypt_ring_e', 'East crypt ring', (2560, 4864, 3328, 7168), -640, -192, 'crypt')
room('crypt_ring_w', 'West crypt ring', (0, 4864, 768, 7168), -640, -192, 'crypt')
room('portcullis', 'Portcullis way', (1024, 6656, 2304, 7168), -640, -192, 'crypt')
room('ossuary', 'Ossuary', (1024, 4864, 2304, 6144), -640, -128, 'ossuary')
room('coffin_vault', 'Coffin vault', (1024, 7424, 3328, 9216), -640, -64, 'crypt_dressed')
room('barracks', "Tomb guards' barracks", (-1536, 6144, -256, 7168), -640, -128, 'crypt')
room('embalming', 'Embalming room', (-1536, 4864, -256, 5888), -640, -128, 'crypt_dressed')
room('deep_stair', 'Deep stair', (128, 7424, 640, 8448), -640, -192, 'deep',
     slope={'to': -1280, 'toward': 'north', 'steps': 20}, ceiling_slope={'to': -832, 'toward': 'north'})
# The deep (floor -2, -1280)
room('deep_crypt', 'Deep crypt', (-1024, 8704, 768, 9984), -1280, -768, 'deep')
room('bone_pit', 'Bone pit', (-1024, 10240, 768, 11520), -1280, -704, 'deep')
room('terror_hall', 'Hall of a Thousand Terrors', (-1536, 11776, 1280, 13824), -1280, -384, 'tomb_tall')

BAA_WALL = S('t6s1bs', 128, 256)
BAA_FLOOR = S('t6s1fl', 128, 128)
BAA_CEIL = S('t6s1c', 128, 128)
FRIEZE = S('t6s1b', 128, 256)
SLAB = S('t4s1fl', 128, 128)
IRON = S('xwiron', 128, 128)
DOOR_IRON = S('t5d1', 128, 256, fit=True)
ROCK_WALL = S('gcav1flr', 256, 256)
ROCK_FLOOR = S('gcav2flr', 128, 128, scale=2)
TIMBER = S('7gt001a', 64, 64)

THEMES = [
    dict(id='theme:tomb', wall=BAA_WALL, floor=BAA_FLOOR, ceiling=BAA_CEIL, reveal=BAA_WALL, door=DOOR_IRON,
         notes="The tomb proper: MM7's Temple of Baa (d04) as it lays its set: brick t6s1bs, flagstones t6s1fl, the "
               "coffered ceiling t6s1c, iron-bound doors t5d1."),
    dict(id='theme:tomb_tall', wall=BAA_WALL, floor=BAA_FLOOR, ceiling=BAA_CEIL, reveal=BAA_WALL, door=DOOR_IRON,
         notes="The tomb's tall halls: the Baa set with its skull frieze t6s1b as a band under the ceiling (the room's "
               "own bands)."),
    dict(id='theme:torture', wall=SLAB, floor=BAA_FLOOR, ceiling=BAA_CEIL, reveal=BAA_WALL, door=DOOR_IRON,
         notes="The torture rooms (stocks, chains, maiden, cage): d04's green-black slabs t4s1fl on the walls, the "
               "tomb's flags, iron (A6's xwiron, xwcage, the kit's xkportc)."),
    dict(id='theme:crypt', wall=S('t5bs', 128, 256), floor=S('t2bs', 128, 256), ceiling=S('t4bs', 128, 256),
         door=DOOR_IRON,
         notes="The crypts: MM7's Barrow I (mdt03) as it lays them: sandy rock t5bs on walls, grey rock t2bs underfoot, "
               "green-black rock t4bs overhead."),
    dict(id='theme:crypt_dressed', wall=S('hwp1b', 128, 256), floor=S('t2bs', 128, 256), ceiling=S('t4bs', 128, 256),
         door=DOOR_IRON,
         notes="The dressed crypts (coffin vault, embalming room): Barrow I's plastered wall hwp1b with its moulding."),
    dict(id='theme:ossuary', wall=S('hwp1b', 128, 256), floor=S('t2bs', 128, 256), ceiling=S('t4bs', 128, 256),
         door=DOOR_IRON,
         notes="The ossuary: the dressed crypt wall under two bands of skulls (the tomb's skull frieze t6s1b)."),
    dict(id='theme:deep', wall=ROCK_WALL, floor=ROCK_FLOOR, ceiling=ROCK_WALL, door=DOOR_IRON,
         notes="The deep: raw rock (MM8 Ogre Fortress d12's gcav1flr, gcav2flr, as XD-05 and XD-07's caves)."),
]


def frieze(height):
    """The skull frieze, 256 high, under the ceiling of a room `height` high."""
    return Flow([FlowDict(height=height - 256, surface=BAA_WALL), FlowDict(height=height, surface=FRIEZE)])


BANDS = {
    'welcome': frieze(768),
    'gallery': frieze(640),
    'terror_hall': Flow([FlowDict(height=512, surface=SLAB), FlowDict(height=768, surface=FRIEZE)]),
    'ossuary': Flow([FlowDict(height=64, surface=S('hwp1b', 128, 256)), FlowDict(height=320, surface=FRIEZE),
                     FlowDict(height=512, surface=FRIEZE)]),
}

# Openings: (id, from, to, width, height, extra)
OPENINGS = [
    ('door_welcome', 'door', 'welcome', 384, 384, {'link': 'link:door_welcome'}),
    ('welcome_gallery', 'welcome', 'gallery', 384, 448, {'link': 'link:welcome_gallery'}),
    ('welcome_westm', 'welcome', 'west_mourning', 256, 320, {'link': 'link:welcome_westm'}),
    ('westm_stocks', 'west_mourning', 'stocks', 384, 384, {'link': 'link:westm_stocks'}),
    ('westm_chain', 'west_mourning', 'chain_room', 256, 320, {'link': 'link:westm_chain'}),
    ('gallery_chain', 'gallery', 'chain_room', 384, 384, {'link': 'link:gallery_chain'}),
    ('gallery_maiden', 'gallery', 'maiden_niche', 384, 384, {'link': 'link:gallery_maiden'}),
    ('gallery_eastm', 'gallery', 'east_mourning', 256, 320, {'link': 'link:gallery_eastm'}),
    ('eastm_cage', 'east_mourning', 'cage_room', 384, 384, {'link': 'link:eastm_cage'}),
    ('cage_shaft', 'cage_room', 'shaft', 320, 288, {'link': 'link:cage_lift',
                                                     'notes': "The cage's upper gate: 640 over the shaft's floor."}),
    ('shaft_pit', 'shaft', 'cage_pit', 320, 288, {'link': 'link:cage_lift', 'notes': "The cage's lower gate."}),
    ('maiden_secret', 'maiden_niche', 'maiden_stair', 256, 320, {'link': 'link:maiden_stair',
                                                                  'notes': "Behind the iron maiden."}),
    ('mstair_ringe', 'maiden_stair', 'crypt_ring_e', 384, 384, {'link': 'link:mstair_ringe'}),
    ('pit_ringe', 'cage_pit', 'crypt_ring_e', 384, 384, {'link': 'link:pit_ringe'}),
    ('ringe_portcullis', 'crypt_ring_e', 'portcullis', 384, 384, {'link': 'link:ringe_portcullis'}),
    ('ringe_ossuary', 'crypt_ring_e', 'ossuary', 384, 384, {'link': 'link:ringe_ossuary'}),
    ('ossuary_ringw', 'ossuary', 'crypt_ring_w', 384, 384, {'link': 'link:ossuary_ringw'}),
    ('ringw_portcullis', 'crypt_ring_w', 'portcullis', 384, 384, {'link': 'link:ringw_portcullis'}),
    ('portcullis_vault', 'portcullis', 'coffin_vault', 384, 384, {'link': 'link:portcullis_vault'}),
    ('ringw_barracks', 'crypt_ring_w', 'barracks', 256, 320, {'link': 'link:ringw_barracks'}),
    ('ringw_embalming', 'crypt_ring_w', 'embalming', 256, 320, {'link': 'link:ringw_embalming'}),
    ('ringw_deep', 'crypt_ring_w', 'deep_stair', 384, 384, {'link': 'link:ringw_deep'}),
    ('deep_crypt', 'deep_stair', 'deep_crypt', 384, 384, {'link': 'link:deep_crypt'}),
    ('crypt_bonepit', 'deep_crypt', 'bone_pit', 512, 448, {'link': 'link:crypt_bonepit'}),
    ('bonepit_terror', 'bone_pit', 'terror_hall', 448, 448, {'link': 'link:bonepit_terror'}),
]


def cx(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (x0 + x1) // 2


def cy(rid):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (y0 + y1) // 2


# ---------------------------------------------------------------------------------------------------------------------
# rooms.yml


def rooms_yml():
    rooms = []
    for rid, r in ROOMS.items():
        d = {'id': f'room:{rid}', 'name': r['name'], 'outline': rect(*r['rect']), 'floor': r['floor']}
        if 'slope' in r:
            d['slope'] = FlowDict(r['slope'])
        d['ceiling'] = r['ceiling']
        if 'ceiling_slope' in r:
            d['ceiling_slope'] = FlowDict(r['ceiling_slope'])
        d['theme'] = f"theme:{r['theme']}"
        if rid in BANDS:
            d['bands'] = BANDS[rid]
        if rid in STORE:
            d['store'] = True
        walls = WALLS.get(rid)
        if walls:
            d['walls'] = walls
        if rid in PILLARS:
            d['pillars'] = PILLARS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        if rid in LEVELS:
            d['levels'] = LEVELS[rid]
        if rid in FLIGHTS:
            d['flights'] = FLIGHTS[rid]
        d['ambient'] = AMBIENT.get(rid, 14)
        d['notes'] = ROOM_NOTES[rid]
        rooms.append(d)
    openings = []
    for oid, a, b, w, h, extra in OPENINGS:
        d = {'id': f'open:{oid}', 'from': f'room:{a}', 'to': f'room:{b}'}
        if 'link' in extra:
            d['link'] = extra['link']
        d['width'] = w
        d['height'] = h
        if 'notes' in extra:
            d['notes'] = extra['notes']
        openings.append(d)
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:tomb', ambient=14), 'rooms': rooms,
            'openings': openings,
            'notes': "XD-08 Tomb of a Thousand Terrors at L4: the tomb at 0 (entry, Hall of Welcome, Gallery of Terrors, "
                     "the two mourning halls, the torture rooms: stocks, chains, iron maiden, hanging cage), the crypts "
                     "at -640 (a ring round the ossuary, the portcullis way and the coffin vault, barracks, embalming "
                     "room, cage pit) and the deep at -1280 (deep crypt, bone pit, Hall of a Thousand Terrors). The cage "
                     "shaft joins 0 and -640. No room stands over another. Written by output/studio_cal/xd08/tools/gen.py."}


def panel(pid, offset, length, bottom, height, surface, notes=None):
    d = FlowDict(id=pid, offset=offset, length=length, bottom=bottom, height=height, surface=surface)
    if notes:
        d['notes'] = notes
    return d


PLAQUE = S('sign128', 256, 128, fit=True)

# Walls are counted counter-clockwise from the outline's first point: south wall runs west->east (offset from x0),
# east wall south->north (offset from y0), north wall east->west (offset from x1), west wall north->south (offset from y1).
WALLS = {
    'gallery': [{'wall': 'north', 'panels': Flow([
        panel('panel:plaque_manacles', 2624, 192, 160, 96, PLAQUE, "'Manacles', east of the chain room's arch."),
        panel('panel:plaque_maiden', 960, 192, 160, 96, PLAQUE, "'Iron Maiden', east of the maiden's niche."),
    ])}],
    'cage_room': [{'wall': 'north', 'panels': Flow([
        panel('panel:plaque_cage', 288, 192, 160, 96, PLAQUE, "'Cage', east of the cage's gate."),
    ])}],
    'stocks': [{'wall': 'north', 'panels': Flow([
        panel('panel:plaque_stocks', 544, 192, 160, 96, PLAQUE, "'Stocks'."),
    ])}],
}

PILLARS = {
    'chain_room': Flow([FlowDict(at=F(x, 3200), size=F(8, 8), surface=IRON) for x in (704, 864, 1184, 1344)]),
    'terror_hall': Flow([FlowDict(at=F(x, y), size=F(128, 128), surface=BAA_WALL)
                         for x in (-832, 576) for y in (12544, 13184)]),
}


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None, end=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d['at'] = F(*at)
    d['size'] = F(*size)
    d['rise'] = rise
    d['surface'] = surface
    if end:
        d['end_surface'] = end
    if top:
        d['top_surface'] = top
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


# D-22.3: A1's world shader liquids (engine/liquids/liquids.yml, worlds: [xeen]), one per basin
JUICE_TEX = {'red': 'xjuicered', 'blue': 'xjuiceblu', 'orange': 'xjuiceorg', 'green': 'xjuicegrn',
             'yellow': 'xjuiceyel', 'purple': 'xjuicepur', 'white': 'xjuicewht'}
BASIN = S('t4s1fl', 128, 128)
JUICE_AT = [(-1376, 5728), (-1120, 5728), (-864, 5728), (-608, 5728), (-1376, 5024), (-1120, 5024), (-864, 5024)]

PLATFORMS = {
    'welcome': Flow([
        block((-512, 1664), (256, 256), 48, SLAB, BAA_FLOOR, "The statue's plinth (clicked: its plaque, "
              "m10.tomb_welcome).", pid='platform:statue'),
    ]),
    'gallery': Flow([
        block((x, 1408), (256, 192), 48, SLAB, BAA_FLOOR, f"A device on its plinth: {what}.")
        for x, what in ((1536, 'a bone cage'), (2304, 'an empty cage'), (3072, 'a gibbet cage'), (3840, 'a noose'))
    ]),
    'west_mourning': Flow([
        block((x, 3648), (128, 256), 80, SLAB, SLAB, "A stone coffin." if pid is None else "A stone coffin (clicked: "
              "'The coffin is empty.').", pid=pid)
        for x, pid in ((-1280, 'platform:coffin_w1'), (-896, None), (-512, 'platform:coffin_w2'), (-128, None))
    ]),
    'stocks': Flow([
        block((-2560, y), (320, 48), 112, TIMBER, TIMBER, "A pair of stocks (a timber board at neck height).")
        for y in (2816, 3200, 3584)
    ]),
    'east_mourning': Flow([
        block((5504, y), (320, 128), 64, SLAB, BAA_FLOOR, "A bier.") for y in (1280, 1664, 2048)
    ]),
    'maiden_niche': Flow([
        block((2752, 3296), (64, 64), 448, IRON, IRON, "The iron maiden's case, west of its door."),
        block((3136, 3296), (64, 64), 448, IRON, IRON, "The iron maiden's case, east of its door."),
    ]),
    'barracks': Flow([
        block((-1480, 6656), (48, 512), 192, TIMBER, TIMBER, "A rack of rusted halberds along the west wall."),
    ]),
    'embalming': Flow([
        block(at, (192, 192), 64, BASIN, S(JUICE_TEX[c], 128, 128, liquid='water'), f"The {c} tomb juice's basin (clicked: +2 {stat} once per "
              "character).", pid=f'platform:juice_{c}')
        for at, (c, stat, bit, col) in zip(JUICE_AT, JUICES)
    ] + [block((-896, 5376), (384, 160), 80, SLAB, SLAB, "The embalming slab.")]),
    'coffin_vault': Flow([
        block((x, y), (128, 288), 96, SLAB, SLAB, "A heavy coffin.")
        for x in (1408, 1920, 2432, 2944) for y in (7936, 8512)
    ]),
    'deep_crypt': Flow([
        block((x, y), (128, 256), 24, S('t2bs', 128, 256), S('t2bs', 128, 256), "An old grave.")
        for x, y in ((-768, 9216), (-512, 9216), (-768, 9664), (512, 9600))
    ]),
    'terror_hall': Flow([
        block((-128, 13632), (1024, 320), 48, SLAB, BAA_FLOOR, "The dais of the throne."),
        block((-128, 13696), (256, 160), 128, FRIEZE, BAA_FLOOR, "The throne of skulls: its seat."),
        block((-128, 13776), (288, 64), 448, FRIEZE, SLAB, "The throne's tall back (skulls)."),
    ]),
}

LEVELS = {
    'bone_pit': Flow([
        FlowDict(id='level:pit_w', outline=rect(-896, 10368, -416, 11392), floor=-1472,
                 notes="The west half of the bone pit, 192 down."),
        FlowDict(id='level:pit_e', outline=rect(160, 10368, 640, 11392), floor=-1472,
                 notes="The east half of the bone pit, 192 down."),
    ]),
}

FLIGHTS = {
    'bone_pit': Flow([
        FlowDict(**{'from': F(-592, 10880), 'to': F(-416, 10880), 'width': 160, 'steps': 6,
                    'riser': ROCK_WALL, 'tread': ROCK_FLOOR, 'notes': "Steps out of the west pit onto the ledge."}),
        FlowDict(**{'from': F(336, 10880), 'to': F(160, 10880), 'width': 160, 'steps': 6,
                    'riser': ROCK_WALL, 'tread': ROCK_FLOOR, 'notes': "Steps out of the east pit onto the ledge."}),
    ]),
}

STORE = set()

AMBIENT = {'door': 16, 'welcome': 16, 'gallery': 14, 'shaft': 8, 'cage_pit': 10, 'deep_stair': 8, 'deep_crypt': 8,
           'bone_pit': 8, 'terror_hall': 12, 'maiden_stair': 8}

ROOM_NOTES = {
    'door': "Inside the tomb door (out to X3): the arrival.",
    'welcome': "The statue on its plinth and its plaque ('Insanity is our fame, undead is our game.', m10.tomb_welcome); "
               "the gallery's arch east, the west mourning hall's door north.",
    'gallery': "A long hall of devices on plinths along its south wall (a bone cage, an empty cage, a gibbet, a noose); "
               "the chain room's and the maiden's arches north with their plaques; the east mourning hall's door east.",
    'west_mourning': "Four stone coffins along the north wall ('The coffin is empty.'), ghouls, a chest; the stocks yard "
                     "west, the chain room's door east.",
    'stocks': "Three pairs of stocks with skeletons still in them; a chest under the last; the 'Stocks' plaque.",
    'chain_room': "Manacles on long chains running into the floor; pull them and the portcullis below rises.",
    'maiden_niche': "The iron maiden in the north wall between its iron case: it opens on a stair (a secret door).",
    'east_mourning': "Three biers with their dead; tomb guards; the hanging cage's arch north.",
    'cage_room': "The cage's gate in the north wall over the dark shaft; its call button and plaque.",
    'shaft': "The shaft the hanging cage rides, 512 square: its gate to the cage room at 0, to the cage pit at -640.",
    'maiden_stair': "Twenty steps down behind the iron maiden to the east crypt ring.",
    'cage_pit': "Where the cage lands; ghouls waiting for it; the call button by the lower gate.",
    'crypt_ring_e': "The crypt ring's east side: from the maiden's stair and the cage pit to the portcullis way and the "
                    "ossuary.",
    'crypt_ring_w': "The ring's west side: the barracks' and the embalming room's doors, the deep stair north.",
    'portcullis': "The way before the coffin vault, closed by a portcullis that the manacles above raise.",
    'ossuary': "Skull walls; skull piles in the corners; bones that rise.",
    'coffin_vault': "Rows of heavy coffins; the great coffin at the north wall holds the King's Megacredits (Might 30).",
    'barracks': "The tomb guards' racks of rusted halberds, their stores and their pay chest (two Might Boosts).",
    'embalming': "Seven basins of tomb juice round the embalming slab: red, blue, orange, green, yellow, purple, white.",
    'deep_stair': "Twenty steps down into the deep; cold air.",
    'deep_crypt': "Raw rock and old graves; grave ghouls.",
    'bone_pit': "A pit of bones in two halves, crossed on a rock ledge; steps out of each half.",
    'terror_hall': "The tomb's heart: the throne of skulls on its dais, braziers, four pillars, tomb guards, the hoard.",
}

# ---------------------------------------------------------------------------------------------------------------------
# objects.yml


def objects_yml():
    doors = [
        {'id': 'door:westm', 'opening': 'open:welcome_westm', 'kind': 'slide_up', 'thickness': 24, 'surface': DOOR_IRON},
        {'id': 'door:chain', 'opening': 'open:westm_chain', 'kind': 'slide_up', 'thickness': 24, 'surface': DOOR_IRON},
        {'id': 'door:eastm', 'opening': 'open:gallery_eastm', 'kind': 'slide_up', 'thickness': 24, 'surface': DOOR_IRON},
        {'id': 'door:barracks', 'opening': 'open:ringw_barracks', 'kind': 'slide_up', 'thickness': 24,
         'surface': DOOR_IRON},
        {'id': 'door:embalming', 'opening': 'open:ringw_embalming', 'kind': 'slide_up', 'thickness': 24,
         'surface': DOOR_IRON},
        {'id': 'door:terror', 'opening': 'open:bonepit_terror', 'kind': 'slide_left', 'leaves': 2, 'thickness': 24,
         'surface': S('t5d1', 128, 256, scale=1.75), 'tile': True, 'notes': "The great doors of the Hall of a Thousand Terrors."},
        {'id': 'door:portcullis', 'opening': 'open:portcullis_vault', 'kind': 'slide_up', 'thickness': 16, 'speed': 48,
         'surface': S('xkportc', 256, 256, scale=1.5), 'tile': True,
         'notes': "The portcullis before the coffin vault (the kit's xkportc), raised by the manacles above."},
        {'id': 'door:maiden', 'opening': 'open:maiden_secret', 'kind': 'slide_up', 'fold': True, 'secret': True,
         'thickness': 24, 'surface': S('xwiron', 128, 128), 'tile': True,
         'notes': "The iron maiden: its front is the leaf of a secret door that rises on a click."},
        {'id': 'door:gate_top', 'opening': 'open:cage_shaft', 'kind': 'slide_up', 'thickness': 8, 'state': 'open',
         'surface': S('xwcage', 128, 256), 'tile': True,
         'notes': "The cage's upper gate: shut whenever the cage is down (a 640 drop otherwise)."},
        {'id': 'door:gate_bottom', 'opening': 'open:shaft_pit', 'kind': 'slide_up', 'thickness': 8,
         'surface': S('xwcage', 128, 256), 'tile': True,
         'notes': "The cage's lower gate: shut whenever the cage is up, so nobody stands under it."},
    ]
    # The hanging cage: XD-04's hoist method (mover:hoist) with its bars (cage_1). The shaft is 512 square; the cage
    # 504 square, standing at the top (state end) when the map is first entered. Parts are given at the travel's start
    # (down): the floor's top at -638.
    cx0, cy0 = 4672, 3904
    top = -638
    bars = S('xwcage', 128, 256)
    rail = S('xwiron', 128, 128)
    parts = [
        FlowDict(at=F(cx0 - 244, cy0), size=F(8, 488), bottom=top, height=320, surface=bars, top_surface=rail,
                 notes="Bars, west side"),
        FlowDict(at=F(cx0 + 244, cy0), size=F(8, 488), bottom=top, height=320, surface=bars, top_surface=rail,
                 notes="Bars, east side"),
    ]
    for dx in (-244, 244):
        for dy in (-244, 244):
            parts.append(FlowDict(at=F(cx0 + dx, cy0 + dy), size=F(16, 16), bottom=top, height=336, surface=rail,
                                  notes="Corner post"))
    parts += [
        FlowDict(at=F(cx0, cy0 - 244), size=F(472, 16), bottom=top + 320, height=16, surface=rail, notes="Top rail"),
        FlowDict(at=F(cx0, cy0 + 244), size=F(472, 16), bottom=top + 320, height=16, surface=rail, notes="Top rail"),
        FlowDict(at=F(cx0 - 244, cy0), size=F(16, 456), bottom=top + 320, height=16, surface=rail, notes="Top rail"),
        FlowDict(at=F(cx0 + 244, cy0), size=F(16, 456), bottom=top + 320, height=16, surface=rail, notes="Top rail"),
        FlowDict(at=F(cx0, cy0), size=F(472, 8), bottom=top + 336, height=16, surface=rail, notes="Hanger bar"),
        FlowDict(at=F(cx0, cy0), size=F(8, 8), bottom=top + 352, height=920, surface=rail,
                 notes="The chain, up to the shaft's roof"),
    ]
    movers = [{'id': 'mover:cage', 'room': 'room:shaft', 'at': F(cx0, cy0), 'size': F(504, 504), 'bottom': top - 16,
               'height': 16, 'travel': F(0, 0, 640), 'speed': 160, 'state': 'end', 'surface': rail,
               'top_surface': rail, 'parts': Flow(parts),
               'notes': "The hanging cage (D-4.4): an iron floor that fills the shaft, bars on its two closed sides, "
                        "corner posts, a frame and its chain, all riding as one; at the top when the map is first "
                        "entered. Click it to ride; call it with the button beside either gate."}]
    switches = [
        {'id': 'switch:manacles', 'room': 'room:chain_room', 'kind': 'lever', 'at': F(1024, 3328),
         'off': S('t5d1', 128, 256), 'notes': "The manacles' chain on the north wall: pull it."},
        {'id': 'switch:call_top', 'room': 'room:cage_room', 'kind': 'button', 'at': F(5216, 3584),
         'notes': "Call button beside the cage's upper gate."},
        {'id': 'switch:call_bottom', 'room': 'room:cage_pit', 'kind': 'button', 'at': F(4960, 4224),
         'notes': "Call button beside the cage's lower gate."},
    ]
    chests = [
        {'id': 'chest:stocks', 'room': 'room:stocks', 'at': F(-2880, 3600), 'kind': 'ch1', 'facing': 'e',
         'treasure_level': 2, 'random_items': 2, 'gold': 200, 'notes': "Under the last of the stocks."},
        {'id': 'chest:west_mourning', 'room': 'room:west_mourning', 'at': F(-1440, 2700), 'kind': 'ch1', 'treasure_level': 2, 'random_items': 2, 'gold': 250, 'notes': "A mourner's offering box."},
        {'id': 'chest:barracks', 'room': 'room:barracks', 'at': F(-1392, 7056), 'kind': 'ch1', 'treasure_level': 2, 'random_items': 2, 'gold': 300,
         'notes': "The guards' pay chest: pay; its first opening hands over two Might Boosts of power 10 (+30 Might) "
                  "for the great coffin (D-22.2: evt:chest_barracks, map qbit pay_potions)."},
        {'id': 'chest:great_coffin', 'room': 'room:coffin_vault', 'at': F(2176, 9040), 'size': F(384, 192, 112),
         'surface': SLAB, 'top_surface': S('t6s1c', 128, 128), 'treasure_level': 2, 'random_items': 2, 'gold': 500,
         'items': Flow(['megacredit'] * 5),
         'notes': "The great coffin: five King's Megacredits (m10.tomb_vault's map_gives) and the vault's offerings. "
                  "Opens only for a member of Might 30 (D-4.5)."},
        {'id': 'chest:hoard', 'room': 'room:terror_hall', 'at': F(704, 13632), 'kind': 'ch1', 'facing': 'w',
         'treasure_level': 3, 'random_items': 4, 'gold': 2500, 'notes': "The hoard of the Hall (tier 3)."},
    ]
    spawns = []

    def sp(name, rid, at, slot, tier, group=51, notes=None):
        d = {'id': f'spawn:{name}', 'room': f'room:{rid}', 'at': F(*at), 'slot': slot, 'tier': tier, 'group': group}
        if notes:
            d['notes'] = notes
        spawns.append(d)

    # Slot 1 Xeen Zombie (Rotting dead C: Grave Ghoul 18)
    for name, rid, at in [('gallery_ghouls', 'gallery', (3456, 1920)), ('cage_room', 'cage_room', (4864, 3200)),
                          ('stocks', 'stocks', (-2112, 3200)), ('westm_1', 'west_mourning', (-896, 3072)),
                          ('westm_2', 'west_mourning', (-128, 3264)), ('ring_e', 'crypt_ring_e', (2944, 6272)),
                          ('cage_pit', 'cage_pit', (4352, 4992)), ('ring_w', 'crypt_ring_w', (384, 6144)),
                          ('ossuary_ghouls', 'ossuary', (1664, 5888)), ('deep_1', 'deep_crypt', (-384, 9344)),
                          ('deep_2', 'deep_crypt', (128, 9728))]:
        sp(name, rid, at, 1, 'c')
    # Slot 2 Xeen Spirit (Polter-Fool 18 a, Tomb Guard 26 b)
    for name, rid, at in [('welcome', 'welcome', (256, 1664)), ('gallery_spirits', 'gallery', (2048, 1856)),
                          ('embalming', 'embalming', (-896, 5248))]:
        sp(name, rid, at, 2, 'a')
    for name, rid, at in [('eastm_1', 'east_mourning', (5120, 1408)), ('eastm_2', 'east_mourning', (5120, 2176)),
                          ('barracks_1', 'barracks', (-896, 6528)), ('barracks_2', 'barracks', (-896, 6912)),
                          ('vault_1', 'coffin_vault', (1664, 8256)), ('vault_2', 'coffin_vault', (2688, 8832)),
                          ('terror_1', 'terror_hall', (-128, 12416)), ('terror_2', 'terror_hall', (-768, 13248)),
                          ('terror_3', 'terror_hall', (512, 13248))]:
        sp(name, rid, at, 2, 'b')
    # Slot 3 Xeen Skeleton (Skeleton Lord 16): the bones that rise
    sp('ossuary_bones', 'ossuary', (1664, 5120), 3, 'c', notes="The ossuary's bone piles that rise.")
    sp('bone_pit', 'bone_pit', (-128, 11264), 3, 'c', notes="Skeleton Lords up from the pit, on the ledge.")

    monsters = []

    decos = []

    def deco(name, rid, d, at=None, **kw):
        e = {'id': f'deco:{name}', 'room': f'room:{rid}', 'decoration': d}
        if at:
            e['at'] = F(*at)
        e.update(kw)
        decos.append(e)

    # Skull torches on the walls (torskul0), plain torches in the crypts (torch01)
    torches = [
        ('door', 'east'), ('door', 'west'), ('welcome', 'west', 0.2), ('welcome', 'east', 0.2),
        ('gallery', 'south', 0.12), ('gallery', 'south', 0.5), ('gallery', 'south', 0.88), ('west_mourning', 'south', 0.4),
        ('west_mourning', 'north', 0.95), ('stocks', 'south'), ('chain_room', 'east', 0.6), ('maiden_niche', 'east'),
        ('maiden_niche', 'west'), ('east_mourning', 'east'), ('east_mourning', 'south'), ('cage_room', 'east'),
        ('terror_hall', 'east', 0.3), ('terror_hall', 'west', 0.3), ('terror_hall', 'east', 0.7),
        ('terror_hall', 'west', 0.7),
    ]
    for i, t in enumerate(torches):
        kw = {'wall': t[1]}
        if len(t) > 2:
            kw['along'] = t[2]
        deco(f'skulltorch_{i + 1:02d}', t[0], 'torskul0', height=192, **kw)
    torches2 = [
        ('cage_pit', 'east'), ('crypt_ring_e', 'east', 0.6), ('crypt_ring_w', 'west', 0.85), ('portcullis', 'north', 0.2),
        ('ossuary', 'north'), ('ossuary', 'south'), ('coffin_vault', 'east'), ('coffin_vault', 'west'),
        ('barracks', 'north', 0.3), ('embalming', 'west'), ('deep_crypt', 'east'), ('bone_pit', 'east', 0.7),
    ]
    for i, t in enumerate(torches2):
        kw = {'wall': t[1]}
        if len(t) > 2:
            kw['along'] = t[2]
        deco(f'torch_{i + 1:02d}', t[0], 'torch01', height=176, **kw)
    # The welcome statue and the gallery's devices on their plinths
    deco('statue', 'welcome', '7dec55', (-512, 1664), floor_height=48)
    deco('device_bonecage', 'gallery', 'Bonecage', (1536, 1408), floor_height=48)
    deco('device_cage', 'gallery', '7dec05', (2304, 1408), floor_height=48)
    deco('device_gibbet', 'gallery', '7dec06', (3072, 1408), floor_height=48)
    deco('device_noose', 'gallery', '7dec07', (3840, 1408), floor_height=48)
    deco('chain_skeleton_1', 'chain_room', 'dec05', (784, 3232))
    deco('chain_skeleton_2', 'chain_room', 'dec05', (1264, 3232))
    deco('candelabra_welcome', 'welcome', 'cndlab0', (-640, 2112))
    # Stocks: a skeleton in each pair
    for i, y in enumerate((2848, 3232, 3616)):
        deco(f'stocks_skeleton_{i + 1}', 'stocks', 'dec05', (-2560, y + 16))
    # West mourning: urns between the coffins
    deco('candle_w1', 'west_mourning', 'cndlab0', (-1088, 3712))
    deco('candle_w2', 'west_mourning', 'cndlab0', (-320, 3712))
    # East mourning: the dead on the biers
    for i, y in enumerate((1280, 1664, 2048)):
        deco(f'bier_corpse_{i + 1}', 'east_mourning', f'Corpse0{i + 1}', (5504, y), floor_height=64)
    # Cage room: a hanging cage over the floor by the east wall
    deco('cage_room_cage', 'cage_room', '7dec07', (5184, 3072))
    # Barracks: containers in pairs along the walls
    deco('barrel_1', 'barracks', 'bigbarel', (-896, 7040))
    deco('barrel_2', 'barracks', 'bigbarel', (-704, 7040))
    deco('sack_1', 'barracks', 'bag01', (-1120, 6272))
    deco('sack_2', 'barracks', 'floursac', (-928, 6272))
    # Ossuary: skull piles in the corners, bones
    for i, at in enumerate([(1184, 5024), (2144, 5024), (1184, 5984), (2144, 5984)]):
        deco(f'ossuary_pile_{i + 1}', 'ossuary', 'sklplrev', at)
    deco('ossuary_skull_1', 'ossuary', '7dec20', (1344, 5984))
    deco('ossuary_skull_2', 'ossuary', '7dec20', (1984, 5984))
    # Embalming: an urn and a skull
    # The crypt ring: bones in its niches
    deco('ring_e_bones', 'crypt_ring_e', 'dec19', (3200, 6784))
    deco('ring_e_skull', 'crypt_ring_e', '7dec20', (3200, 7072))
    deco('ring_w_bones', 'crypt_ring_w', '7dec18', (640, 4960))
    # Coffin vault: candelabra of skulls either side of the great coffin
    deco('vault_candelabra_w', 'coffin_vault', 'cndlab0', (1792, 9088))
    deco('vault_candelabra_e', 'coffin_vault', 'cndlab0', (2560, 9088))
    # Deep crypt and bone pit: bones and skulls
    deco('deep_bones_1', 'deep_crypt', 'dec29', (-512, 9472))
    deco('deep_bones_2', 'deep_crypt', 'dec29', (512, 9216))
    for i, at in enumerate([(-768, 10560), (-576, 11136), (384, 10624), (512, 11200)]):
        deco(f'pit_pile_{i + 1}', 'bone_pit', 'sklplrev', at)
    for i, at in enumerate([(-704, 10816), (448, 10880)]):
        deco(f'pit_bones_{i + 1}', 'bone_pit', '7dec18', at)
    # Terror hall: the throne's skull piles, skulls on spears, braziers
    deco('throne_pile_w', 'terror_hall', 'sklplrev', (-512, 13632))
    deco('throne_pile_e', 'terror_hall', 'sklplrev', (256, 13632))
    deco('throne_skull_w', 'terror_hall', '7dec20', (-1344, 13632))
    deco('throne_skull_e', 'terror_hall', '7dec20', (1088, 13632))
    deco('brazier_w', 'terror_hall', 'flamb00', (-832, 12864))
    deco('brazier_e', 'terror_hall', 'flamb00', (576, 12864))

    lights = []

    def light(name, rid, at, height, radius, color):
        lights.append({'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
                       'color': F(*color)})

    for rid in ROOMS:
        r = ROOMS[rid]
        if r.get('slope') or rid == 'shaft':
            continue
        h = min(r['ceiling'] - r['floor'] - 64, 640)
        radius = 1400 if rid in ('gallery', 'terror_hall', 'coffin_vault') else 1000
        if r['floor'] >= 0:
            col = (255, 190, 130)
        elif r['floor'] >= -640:
            col = (200, 170, 140)
        else:
            col = (150, 170, 210)
        if rid == 'terror_hall':
            col = (255, 150, 110)
        light(rid, rid, (cx(rid), cy(rid)), h, radius, col)
    for (at, (c, stat, bit, col)) in zip(JUICE_AT, JUICES):
        # D-22.3: the liquids carry the colours now; each basin keeps a faint glow of its own (was 288 at full colour)
        light(f'juice_{c}', 'embalming', at, 112, 160, tuple(v * 2 // 5 for v in col))

    sounds = [
        {'id': 'sound:ring_drip', 'room': 'room:crypt_ring_e', 'at': F(2944, 6016), 'sound': 'drip02', 'radius': 1400,
         'volume': 0.6, 'wait': F(3, 9), 'notes': "Water dripping in the crypts."},
        {'id': 'sound:ossuary_drip', 'room': 'room:ossuary', 'at': F(1664, 5504), 'sound': 'drip03', 'radius': 1300,
         'volume': 0.5, 'wait': F(4, 11)},
        {'id': 'sound:deep_drip', 'room': 'room:deep_crypt', 'at': F(-128, 9344), 'sound': 'drip02', 'radius': 1500,
         'volume': 0.6, 'wait': F(3, 8)},
        {'id': 'sound:juices', 'room': 'room:embalming', 'at': F(-896, 5376), 'sound': 'bubbling cauldron01',
         'radius': 1300, 'inner_radius': 400, 'volume': 0.5, 'notes': "The seven basins bubbling."},
        {'id': 'sound:braziers', 'room': 'room:terror_hall', 'at': F(-128, 12864), 'sound': 'torch loop',
         'radius': 1800, 'inner_radius': 500, 'volume': 0.5},
    ]

    return {'format': 0,
            'start': {'room': 'room:door', 'at': F(0, 384), 'facing': 90,
                      'notes': "Inside the tomb door, facing the Hall of Welcome."},
            'doors': doors, 'movers': movers, 'sounds': sounds, 'lights': lights, 'switches': switches,
            'chests': chests, 'spawns': spawns, 'monsters': monsters, 'decorations': decos,
            'exits': [{'id': 'exit:x3', 'room': 'room:door', 'wall': 'south', 'size': F(224, 448),
                       'surface': S('7solid01', 128, 256, fit=True), 'to': 'door:x3',
                       'notes': "The tomb door: out to X3 (Lifeforce Lagoon), in front of its barrow door."}],
            'relations': []}


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='script', trigger='timer', every=1, once=True,
      effects=[{'message': "The tomb door grinds shut behind you. The air is cold and smells of old graves; from "
                           "somewhere deep below comes a sound like laughter."}],
      notes="Say where the party is (a one-shot timer: a load event's window is not shown). A3 has no arrival hook "
            "for XD-08.")
    e(id='evt:exit_x3', preset='exit', source='exit:x3', title='Leave the Tomb of a Thousand Terrors',
      notes="Out to X3 (installed): the original 'Leave the Tomb of a Thousand Terrors?' (aaze0080:24) as the hint; the "
            "game's window asks 'Do you wish to leave ...?'.")
    e(id='evt:welcome', preset='script', source='platform:statue', title='Statue', effects=[hook('m10.tomb_welcome')],
      notes="A3's hook m10.tomb_welcome: the plaque's words (aaze0080:0).")
    for d, title in [('westm', 'Door'), ('chain', 'Door'), ('eastm', 'Door'), ('barracks', 'Barracks'),
                     ('embalming', 'Door'), ('terror', 'Great doors')]:
        e(id=f'evt:door_{d}', preset='door', source=f'door:{d}', title=title)
    for c in ('w1', 'w2'):
        e(id=f'evt:coffin_{c}', preset='text', source=f'platform:coffin_{c}', title='Coffin', window=True,
          text="The coffin is empty.", notes="aaze0080:1.")
    for name, text in [('manacles', 'Manacles'), ('maiden', 'Iron Maiden'), ('cage', 'Cage'), ('stocks', 'Stocks')]:
        e(id=f'evt:plaque_{name}', preset='text', source=f'panel:plaque_{name}', title='Plaque', window=True,
          text=f"The plaque reads: {text}.", notes="The source's plaques (aaze0080:11-13, 25).")
    e(id='evt:manacles', preset='switch', source='switch:manacles', title='Manacles',
      condition={'not': {'qbit': 'manacles_pulled'}}, opens=['door:portcullis'], sets={'qbit': 'manacles_pulled'},
      effects=[{'shake': {'strength': 0.4, 'seconds': 2}}],
      text="You haul on the manacles and their chains run down into the floor. Far below, iron grinds upward.",
      else_effects=[{'text': "The manacles hang slack. Below, the portcullis stands open."}],
      notes="state:manacles: the portcullis before the coffin vault (D-4).")
    e(id='evt:portcullis', preset='door', source='door:portcullis', title='Portcullis', action='open',
      condition={'qbit': 'manacles_pulled'},
      locked_text="The portcullis does not move. Its chains run up through the roof toward the tomb above.")
    e(id='evt:maiden', preset='door', source='door:maiden', title='Iron Maiden', action='open',
      text="The iron maiden swings open. Its back is no back at all: behind the spikes a stair goes down into the dark.",
      notes="link:maiden_stair: the secret door (D-4).")
    e(id='evt:cage', preset='switch', source='mover:cage', title='Hanging cage',
      toggles=['mover:cage', 'door:gate_top', 'door:gate_bottom'],
      text="You pull the chain. The winch overhead groans and the cage moves.",
      notes="link:cage_lift: ride the cage (D-4.4).")
    e(id='evt:call_top', preset='switch', source='switch:call_top', title='Call the cage',
      opens=['mover:cage', 'door:gate_top'], closes=['door:gate_bottom'], text="The chain rattles: the cage comes up.")
    e(id='evt:gate_top', preset='switch', source='door:gate_top', title='Cage gate',
      opens=['mover:cage', 'door:gate_top'], closes=['door:gate_bottom'], text="The chain rattles: the cage comes up.",
      notes="The upper gate calls the cage like the button beside it (XD-04's hoist gate).")
    e(id='evt:call_bottom', preset='switch', source='switch:call_bottom', title='Call the cage',
      closes=['mover:cage', 'door:gate_top'], opens=['door:gate_bottom'], text="The chain rattles: the cage comes down.")
    e(id='evt:gate_bottom', preset='switch', source='door:gate_bottom', title='Cage gate',
      closes=['mover:cage', 'door:gate_top'], opens=['door:gate_bottom'], text="The chain rattles: the cage comes down.")
    for c in ('stocks', 'west_mourning', 'hoard'):
        e(id=f'evt:chest_{c}', preset='chest', source=f'chest:{c}', title='Chest')
    pay = QBITS['pay_potions']
    e(id='evt:chest_barracks', preset='chest', source='chest:barracks', title='Chest',
      effects=[{'lua': f'if not IsQBitSet(QBit({pay})) then SetQBit(QBit({pay})) '
                       'evt.SetHeldItem(240, {bonus = 10}) evt.SetHeldItem(240, {bonus = 10}) '
                       'evt.StatusText("Two flasks of red draught lie on top of the pay.") end'}],
      notes=f"D-22.2: two Might Boosts of a fixed power 10 (+30 Might: any member reaches the great coffin's 30), once "
            f"per game on the pay chest's first opening (map qbit pay_potions {pay}); the chest holds no random Might "
            "Boost.")
    e(id='evt:great_coffin', preset='chest', source='chest:great_coffin', title='Coffin',
      condition={'stat': {'name': 'ActualMight', 'at_least': 30}}, effects=[hook('m10.tomb_vault')],
      else_effects=[{'message': "You are not strong enough to open the coffin."}],
      notes="D-4.5: the clicking member needs Might 30 (ActualMight: potions and spells count); A3's hook "
            "m10.tomb_vault (once): bit 111201, 2,500 xp and its words; the coffin holds the five Megacredits.")
    for c, stat, bit, col in JUICES:
        e(id=f'evt:juice_{c}', preset='script', source=f'platform:juice_{c}', title=f'{c.capitalize()} Tomb Juice',
          condition={'not': {'player_bit': bit}},
          effects=[{'player_bit': bit}, {'add': {'var': f'Base{stat}', 'value': 2}},
                   {'text': f"{c.capitalize()} Tomb Juice. +2 {stat} (permanent)."}],
          else_effects=[{'text': "The liquid is powerless."}],
          notes=f"aaze0080:{2 + [j[0] for j in JUICES].index(c)} and :9; D-4.2: +2 {stat} once per character "
                f"(player bit {bit}).")
    ev.sort(key=lambda x: x['id'])
    return {'format': 0, 'events': ev}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    p = {
        'format': 0, 'id': 'xeen_xd08', 'name': 'Tomb of a Thousand Terrors', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-08', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(18, 28), climbs='n'),
        'map_stats': {
            'id': MAP_STATS_ID, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 1,
            'perception_difficulty': 2, 'refill_days': 672, 'music': MUSIC, 'environment': 'stone',
            'lock_difficulty': 2,
            'slots': [
                FlowDict(monster='Xeen Zombie', tier=5, per_marker=F(2, 3), weight=50),
                FlowDict(monster='Xeen Spirit', tier=2, per_marker=F(1, 2), weight=40),
                FlowDict(monster='Xeen Skeleton', tier=5, per_marker=F(2, 3), weight=10),
            ],
        },
        'neighbours': [{
            'id': 'door:x3', 'to': 'xeen_x3.odm', 'kind': 'door', 'arrival': F(-15360, -9830, 1146),
            'arrival_hint': "On X3 (Lifeforce Lagoon) in front of the tomb's barrow door (X3 thing:tomb, its face at "
                            "about y -10240), facing away from it, north.",
            'direction': 90,
            'notes': "X3 installed (A5, devdocs/xeen/briefs/x3/DOORS.md): arrival -15360, -9830, 1146 facing north. X3's "
                     "door (m10.tomb_door, the Stone of a Thousand Terrors 12304) brings the party to this map's start "
                     "inside the tomb door (0, 384, 0, facing north)."}],
        'qbits': dict(sorted(QBITS.items())),
        'items': dict(ITEMS),
        'notes': "Xeen design brief, level %s: XD-08 Tomb of a Thousand Terrors, on X3 (Lifeforce Lagoon), Act II, "
                 "class M (MU-6 graph devdocs/xeen/mockups/act2_graphs/xd08.graph.yml, decisions D-4 XD-08). Story M10: "
                 "five King's Megacredits 12192 in the great coffin (m10.tomb_vault), behind a Might check of 30; the "
                 "barracks chest's first opening gives two Might Boosts (240) of power 10 (D-22.2). Map card 9124, music 20, treasure 2 (hoard 3); slots 1 "
                 "Xeen Zombie (Grave Ghoul 18 c), 2 Xeen Spirit (Polter-Fool 18 a, Tomb Guard 26 b; Tomb Terror 40 "
                 "left out, D-4.1), 3 Xeen Skeleton (Skeleton Lord 16 c). Quest bits: A3's tomb_credits 111201 (set "
                 "by the hook); the map's own 110760-110799 (two used). Player bits 11270-11276 (the seven tomb "
                 "juices). The tomb door leads out to X3 (door:x3)." % level,
    }
    return p


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml


def plan_yml(level):
    sp = []

    def s(rid, kind, size, purpose, population=None, treasure=None, **kw):
        r = ROOMS[rid]
        x0, y0, x1, y1 = r['rect']
        kind = {'hall': 'room', 'stair': 'room', 'cave': 'room'}.get(kind, kind)
        d = {'id': f'room:{rid}', 'name': r['name'], 'kind': kind, 'size': size, 'extent': F(x1 - x0, y1 - y0)}
        fl = r['floor'] if 'slope' not in r else F(min(r['floor'], r['slope']['to']), max(r['floor'], r['slope']['to']))
        d['floor'] = fl
        d['clear_height'] = (r['ceiling'] - r['floor']) if 'slope' not in r else 448
        d['purpose'] = purpose
        if population:
            d['population'] = population
        else:
            d['empty'] = True
        if treasure:
            d['treasure'] = treasure
        d.update(kw)
        sp.append(d)

    def pop(slot, groups, rank, strength='pack'):
        return FlowDict(slot=slot, groups=groups, per_marker=F(1, 2) if slot == 2 else F(2, 3), strength=strength,
                        rank=rank)

    chest2 = [FlowDict(kind='chest', count=1, tier=2)]
    s('door', 'room', 'S', "Inside the tomb door (the Stone of a Thousand Terrors opened it on X3): the arrival.")
    s('welcome', 'hall', 'M', "The statue and its plaque: 'Insanity is our fame, undead is our game.'",
      population=[pop(2, 1, 'a', 'light')])
    s('gallery', 'hall', 'L', "A long hall of devices on plinths; the plaques of the manacles and the iron maiden.",
      population=[pop(2, 1, 'a', 'light'), pop(1, 1, 'c', 'light')])
    s('west_mourning', 'hall', 'M', "Coffins ('The coffin is empty.'); ghouls; a chest.", population=[pop(1, 2, 'c')],
      treasure=chest2)
    s('stocks', 'room', 'M', "Rows of stocks with skeletons still in them; a chest under the last.",
      population=[pop(1, 1, 'c', 'light')], treasure=chest2)
    s('chain_room', 'room', 'S', "Manacles on long chains: pull them and the portcullis below rises.")
    s('maiden_niche', 'room', 'S', "The iron maiden: open it, and a stair goes down behind its spikes.")
    s('east_mourning', 'hall', 'M', "Biers and tomb guards.", population=[pop(2, 2, 'b')])
    s('cage_room', 'room', 'S', "The hanging cage over its shaft: ride it down to the crypts.",
      population=[pop(1, 1, 'c', 'light')])
    s('shaft', 'stair', 'S', "The cage's shaft, from 0 down to the cage pit at -640.")
    s('maiden_stair', 'stair', 'S', "The stair from behind the iron maiden.")
    s('cage_pit', 'room', 'S', "Where the cage lands; ghouls waiting for it.", population=[pop(1, 1, 'c')])
    s('crypt_ring_e', 'corridor', 'M', "The crypt ring's east side.", population=[pop(1, 1, 'c', 'light')])
    s('crypt_ring_w', 'corridor', 'M', "The ring's west side; the deep stair.", population=[pop(1, 1, 'c', 'light')])
    s('portcullis', 'corridor', 'S', "The portcullis before the coffin vault, raised by the chains above.")
    s('ossuary', 'room', 'M', "Skull walls; bone piles that rise.", population=[pop(3, 1, 'c'), pop(1, 1, 'c')])
    s('coffin_vault', 'room', 'L', "Heavy coffins; in the largest, the King's Megacredits ('You are not strong enough "
      "to open the coffin.').", population=[pop(2, 2, 'b', 'heavy')],
      treasure=[FlowDict(kind='chest', count=1, tier=2, notes="The great coffin: five Megacredits (Might 30).")])
    s('barracks', 'room', 'M', "Racks of rusted halberds; the guards' pay chest (two Might Boosts).",
      population=[pop(2, 2, 'b')], treasure=chest2)
    s('embalming', 'room', 'M', "Seven basins of tomb juice: one drink each per character.",
      population=[pop(2, 1, 'a', 'light')], set_piece=True)
    s('deep_stair', 'stair', 'S', "Down to the deep; cold air.")
    s('deep_crypt', 'cave', 'M', "Raw rock and old graves; grave ghouls.", population=[pop(1, 2, 'c')])
    s('bone_pit', 'cave', 'M', "A pit of bones crossed on a ledge.", population=[pop(3, 1, 'c')])
    s('terror_hall', 'hall', 'L', "The tomb's heart: a throne of skulls, tomb guards, the hoard (tier 3).",
      population=[pop(2, 3, 'b', 'heavy')], treasure=[FlowDict(kind='chest', count=1, tier=3)])
    for d in sp:
        d.pop('set_piece', None)

    links = []

    def ln(lid, a, b, kind, **kw):
        d = {'id': f'link:{lid}', 'from': f'room:{a}', 'to': f'room:{b}', 'kind': kind}
        d.update(kw)
        links.append(d)

    ln('door_welcome', 'door', 'welcome', 'open')
    ln('welcome_gallery', 'welcome', 'gallery', 'open')
    ln('welcome_westm', 'welcome', 'west_mourning', 'door')
    ln('westm_stocks', 'west_mourning', 'stocks', 'open')
    ln('westm_chain', 'west_mourning', 'chain_room', 'door')
    ln('gallery_chain', 'gallery', 'chain_room', 'open')
    ln('gallery_maiden', 'gallery', 'maiden_niche', 'open')
    ln('gallery_eastm', 'gallery', 'east_mourning', 'door')
    ln('eastm_cage', 'east_mourning', 'cage_room', 'open')
    ln('cage_lift', 'cage_room', 'cage_pit', 'lift', rise=-640, notes="The hanging cage in its shaft (room:shaft).")
    ln('maiden_stair', 'maiden_niche', 'maiden_stair', 'secret_door', notes="Open the iron maiden.")
    ln('mstair_ringe', 'maiden_stair', 'crypt_ring_e', 'stairs', rise=-640)
    ln('pit_ringe', 'cage_pit', 'crypt_ring_e', 'open')
    ln('ringe_portcullis', 'crypt_ring_e', 'portcullis', 'open')
    ln('ringe_ossuary', 'crypt_ring_e', 'ossuary', 'open')
    ln('ossuary_ringw', 'ossuary', 'crypt_ring_w', 'open')
    ln('ringw_barracks', 'crypt_ring_w', 'barracks', 'door')
    ln('ringw_portcullis', 'crypt_ring_w', 'portcullis', 'open')
    ln('portcullis_vault', 'portcullis', 'coffin_vault', 'portcullis', condition={'qbit': 'manacles_pulled'},
       notes="Raised by the manacles in the chain room above.")
    ln('ringw_embalming', 'crypt_ring_w', 'embalming', 'door')
    ln('ringw_deep', 'crypt_ring_w', 'deep_stair', 'open')
    ln('deep_crypt', 'deep_stair', 'deep_crypt', 'stairs', rise=-640)
    ln('crypt_bonepit', 'deep_crypt', 'bone_pit', 'open')
    ln('bonepit_terror', 'bone_pit', 'terror_hall', 'door')

    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "A tomb that its builders meant as a joke on the living: a Hall of Welcome whose statue boasts "
                 "'Insanity is our fame, undead is our game', a gallery of torture devices that work - manacles whose "
                 "chains raise a portcullis far below, an iron maiden that opens on a hidden stair, a hanging cage that "
                 "rides its chain down to the crypts - mourning halls of coffins and biers, a ring of crypts round an "
                 "ossuary, an embalming room of seven coloured juices, and a coffin vault whose great coffin only the "
                 "strong can open. Below, raw rock, a bone pit and the Hall of a Thousand Terrors with its throne of "
                 "skulls.",
        'purpose': "Story M10 (five King's Megacredits in the great coffin, Might 30); the seven tomb juices "
                   "(+2 each, once per character); an optional deep with the hoard. Party 15-17, monsters 15-30 "
                   "(Grave Ghouls, Polter-Fools, Tomb Guards, Skeleton Lords; no Tomb Terror, D-4.1).",
        'mood': "Dark brick and skull friezes lit by skull torches; iron and green-black slabs in the torture rooms; "
                "grey barrow rock in the crypts; cold raw rock in the deep and a red glow in the Hall.",
        'datum': 'arrival',
        'spaces': sp,
        'links': links,
        'loops': [
            {'id': 'loop:upper', 'spaces': [f'room:{x}' for x in ('welcome', 'gallery', 'chain_room', 'west_mourning')],
             'notes': "Round the chain room."},
            {'id': 'loop:cage_maiden', 'spaces': [f'room:{x}' for x in ('gallery', 'east_mourning', 'cage_room',
                                                                        'cage_pit', 'crypt_ring_e', 'maiden_stair',
                                                                        'maiden_niche')],
             'notes': "Down in the cage, up behind the maiden."},
            {'id': 'loop:crypts', 'spaces': [f'room:{x}' for x in ('crypt_ring_e', 'ossuary', 'crypt_ring_w',
                                                                   'portcullis')],
             'notes': "Round the crypts."},
        ],
        'entrances': [
            {'id': 'entrance:tomb_door', 'space': 'room:door', 'kind': 'both', 'facing': 'n',
             'how': "Inside the tomb door from X3 (opened with the Stone of a Thousand Terrors, m10.tomb_door); the "
                    "tomb door leads back out to X3."},
        ],
        'critical_path': [f'room:{x}' for x in ('door', 'welcome', 'gallery', 'chain_room', 'gallery', 'east_mourning',
                                                'cage_room', 'cage_pit', 'crypt_ring_e', 'portcullis', 'coffin_vault')],
        'goals': [
            {'id': 'goal:megacredits', 'space': 'room:coffin_vault', 'kind': 'take',
             'what': "Five King's Megacredits in the great coffin (m10.tomb_vault), for a member of Might 30."},
        ],
        'set_pieces': [
            {'id': 'set:manacles', 'kind': 'scripted', 'spaces': ['room:chain_room', 'room:portcullis'],
             'rule': "Pulling the manacles raises the portcullis before the coffin vault: 'Far below, iron grinds "
                     "upward.'"},
            {'id': 'set:maiden', 'kind': 'scripted', 'spaces': ['room:maiden_niche', 'room:maiden_stair'],
             'rule': "The iron maiden opens on a stair down to the crypts (a secret door)."},
            {'id': 'set:cage', 'kind': 'scripted', 'spaces': ['room:cage_room', 'room:shaft', 'room:cage_pit'],
             'rule': "The hanging cage rides its chain down to the cage pit and back; call buttons at both gates."},
            {'id': 'set:juices', 'kind': 'scripted', 'spaces': ['room:embalming'],
             'rule': "Seven basins: +2 to one stat each, once per character; then 'The liquid is powerless.'"},
            {'id': 'set:coffin', 'kind': 'scripted', 'spaces': ['room:coffin_vault', 'room:barracks'],
             'rule': "The great coffin opens for Might 30 ('You are not strong enough to open the coffin.'); two Might "
                     "Boosts in the barracks chest."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 50, 'chests': 5, 'loops': 3,
                   'doors': 10, 'fixed_actors': 0},
        'notes': "Class M (MAPS: 20-45 sectors, 45-75 monsters). 22 rooms of the graph plus the cage shaft. Every room "
                 "is a rectangle; stairs are stepped rooms of 20 risers of 32.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


DIAGRAM = r"""XD-08 Tomb of a Thousand Terrors (x east, y north; floors 0 / -640 / -1280)

 -1280                [Hall of a Thousand Terrors: throne of skulls, Tomb Guards, hoard T3]
                          | great doors
                      [Bone pit: Skeleton Lords on the ledge]
                          | open
                      [Deep crypt: graves, Grave Ghouls]
                          | stair (20 x 32)
  -640  [Barracks T2: 2 Might Boosts]=door=[W ring]--[PORTCULLIS way]--[E ring]--[Cage pit]
        [Embalming: 7 juices]=door=        |  \       | PORTCULLIS     |   |       | lower gate
                                           |  [COFFIN VAULT: great coffin, 5 Megacredits, Might 30]
                                           +--[Ossuary: bones that rise]--+   |      [SHAFT: hanging cage]
                                                              maiden stair |      | upper gate
     0  [Stocks T2]--[W mourning T2]=door=[Chain room: MANACLES]  [Iron maiden: SECRET]  [Cage room]
                          || door          | open                 | open                 | open
                     [Hall of Welcome: statue]--[GALLERY OF TERRORS: devices]=door=[E mourning: biers]
                          | open
                     [Tomb door: arrival; out to X3]
"""


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def write(level):
    d = BRIEFS / level
    d.mkdir(parents=True, exist_ok=True)
    dump(d / 'project.yml', project_yml(level))
    dump(d / 'plan.yml', plan_yml(level))
    (d / 'diagram.txt').write_text(DIAGRAM)
    if level in ('L3', 'L4'):
        dump(d / 'rooms.yml', rooms_yml())
    if level == 'L4':
        dump(d / 'objects.yml', objects_yml())
        dump(d / 'wiring.yml', wiring_yml())


if __name__ == '__main__':
    for lv in (sys.argv[1:] or ['L1', 'L2', 'L3', 'L4']):
        write(lv)
