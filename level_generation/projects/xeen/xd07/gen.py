#!/usr/bin/env python3
"""XD-07 Castle Burlock: writes the project files of devdocs/xeen/briefs/xd07/L1..L4 (lane A7, sub-agent xeen-a7-xd07).

    python3 level_generation/projects/xeen/xd07/gen.py            all four levels
    python3 level_generation/projects/xeen/xd07/gen.py L4         one level

Frame: x east, y north, the court floor at 0, the castle door (south wall of the gatehouse) at y 0. One room is one
rectangle (outline) except where a note says otherwise. Ids that the playtests use are read from ids.lock.yml after
each build (the build keeps it).
"""
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
BRIEFS = ROOT / 'devdocs/xeen/briefs/xd07'
# X4 (Burlock Savannah, lane A5): once xeen_x4.odm is installed, the castle door and the old throne's throw lead onto it
# at A5's points (2026-11-20); until then both stay sealed. XD07_X4=1 or 0 overrides the test (scratch builds).
X4_STEM = 'xeen_x4.odm'
X4_IN = os.environ.get('XD07_X4', '1' if (ROOT / 'assets_dev/worlds/xeen/maps' / X4_STEM).exists() else '0') == '1'
X4_GATE_ARRIVAL = (-1024, 6912, 1808)      # on the castle rise in front of the gate (A5's built point, 2026-11-20)
X4_THROW_ARRIVAL = (-4608, 9728, 2504)     # beside the west tower outside the walls, 1,000 over the ground (A5's built point)


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
MAP_STATS_ID = 9123
MUSIC = 29
QBITS = {
    'crusader': 110047,          # m4.done (A3): the party is Crusaders
    'audience': 111100,          # m5.audience (A3): the King's audience
    'dungeon_key': 116080,       # xd07.dungeon_key (A3, npcs/xd07.yml): Artemus gave the dungeon key
    'tiara_done': 112061,        # Q-C3 done (A3): Roxanne lets the party open her chest
    'den_bar_lifted': 110720,    # map: the troll den's bar on the cellar door lifted (the dungeon ring)
    'cage_lever_pulled': 110721,  # map: the warden's lever pulled (the pit portcullis up)
}
PLAYER_BIT_BLACK = 11070        # once per character: the Black Liquid (+2 Might)

# Rooms: id -> (name, rect, floor, ceiling, theme, extra)
ROOMS = {}


def room(rid, name, r, floor, ceiling, theme, **extra):
    ROOMS[rid] = dict(name=name, rect=r, floor=floor, ceiling=ceiling, theme=theme, **extra)


# The court (floor 0)
room('gatehouse', 'Gatehouse', (-640, 0, 640, 1024), 0, 640, 'gate')
room('great_hall', 'Great hall', (-1536, 1280, 1536, 3328), 0, 960, 'hall')
room('throne_room', 'Throne room', (-1280, 3584, 1280, 6144), 0, 1152, 'hall')
room('armour_gallery', 'Gallery of arms', (1536, 3584, 4352, 4352), 0, 640, 'court')
room('library', 'Library', (1792, 2304, 3328, 3328), 0, 640, 'library')
room('well_court', 'Well court', (1792, 1280, 2816, 2048), 0, 768, 'court')
room('east_tower_base', 'East tower foot', (1536, 4864, 2560, 5888), 0, 640, 'royal')
room('east_stair_1', 'East tower stair', (2816, 5120, 3840, 5632), 0, 448, 'royal',
     slope={'to': 640, 'toward': 'east', 'steps': 20}, ceiling_slope={'to': 1088, 'toward': 'east'})
room('east_landing', "Princess's landing", (4096, 4864, 5120, 5888), 640, 1152, 'royal')
room('east_stair_2', 'East tower upper stair', (4352, 6144, 4864, 7168), 640, 1088, 'royal',
     slope={'to': 1280, 'toward': 'north', 'steps': 20}, ceiling_slope={'to': 1728, 'toward': 'north'})
room('royal_bedroom', 'Royal bedroom', (3840, 7424, 5376, 8448), 1280, 1792, 'royal')
room('west_tower_base', 'West tower foot', (-2816, 1792, -1792, 2816), 0, 640, 'tower')
room('west_stair_1', 'West tower stair', (-4096, 2048, -3072, 2560), 0, 448, 'tower',
     slope={'to': 640, 'toward': 'west', 'steps': 20}, ceiling_slope={'to': 1088, 'toward': 'west'})
room('fools_hall', "Fools' hall", (-5632, 1536, -4352, 3072), 640, 1152, 'tower')
room('west_gallery', 'West tower gallery', (-5376, 3328, -4608, 5376), 640, 1088, 'tower')
room('west_stair_2', 'West tower upper stair', (-5248, 5632, -4736, 6656), 640, 1088, 'tower',
     slope={'to': 1280, 'toward': 'north', 'steps': 20}, ceiling_slope={'to': 1728, 'toward': 'north'})
room('gargoyle_loft', 'Gargoyle loft', (-5888, 6912, -4096, 8192), 1280, 2048, 'loft')
room('old_throne', "Old King's throne", (-5632, 8448, -4352, 9728), 1280, 1920, 'loft')
room('kitchens', 'Kitchens', (-2304, -256, -896, 1024), 0, 640, 'service')
room('kitchen_stair', 'Cellar stair', (-1920, -1536, -1408, -512), 0, 448, 'service',
     slope={'to': -640, 'toward': 'south', 'steps': 20}, ceiling_slope={'to': -192, 'toward': 'south'})
# Cellars and dungeon (floor -1, -640) and the pit (-1152)
room('cellar', 'Wine cellar', (-2560, -3072, -768, -1792), -640, -128, 'cellar')
room('cell_block', 'Cell block', (-512, -3328, 1536, -1536), -640, -64, 'dungeon')
room('pit_gallery', 'Pit gallery', (1792, -2816, 3840, -2048), -640, -128, 'dungeon')
room('pit_stair', 'Pit stair', (2864, -3840, 3024, -3072), -640, -352, 'dungeon',
     slope={'to': -1152, 'toward': 'south', 'steps': 16}, ceiling_slope={'to': -864, 'toward': 'south'})
room('dragon_pit', 'Dragon pit', (1792, -6144, 4096, -4096), -1152, -128, 'cave')
room('old_cistern', 'Old cistern', (-512, -5376, 1536, -3584), -640, -64, 'cistern')
room('troll_den', 'Troll den', (-2816, -5376, -768, -3328), -640, -128, 'cave')
room('postern', 'Postern tunnel', (-4096, -4608, -3072, -4096), -640, -256, 'dungeon')

THEMES = [
    dict(id='theme:cave', wall=S('gcav1flr', 256, 256), floor=S('gcav2flr', 128, 128, scale=2),
         ceiling=S('gcav1flr', 256, 256),
         notes="The troll den and the dragon pit: the castle's foundations break into the hill's rock (MM8 Ogre Fortress "
               "d12's rock, as XD-05)."),
    dict(id='theme:cellar', wall=S('cswl128', 128, 256), floor=S('tfb08', 128, 128), ceiling=S('csbr128', 128, 128),
         door=S('t5d1', 128, 256, fit=True),
         notes="The wine cellar: MM6 grey castle ashlar (cswl128), MM7 Titans' Stronghold flags (tfb08), grey blocks overhead."),
    dict(id='theme:cistern', wall=S('cswl128', 128, 256), floor=S('gcav2flr', 128, 128, scale=2),
         ceiling=S('csbr128', 128, 128),
         notes="The old cistern: the castle's grey ashlar round a floor of wet dark rock where the water stood."),
    dict(id='theme:court', wall=S('t3s2b1', 128, 256), floor=S('t3s2fl1', 128, 128), ceiling=S('t3s2c', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The court's rooms: MM7 Titans' Stronghold cream marble (t3s2b1, t3s2fl1, t3s2c; the royal kit's interior "
               "set), Castle Harmondale's arched oak doors."),
    dict(id='theme:dungeon', wall=S('cswl128', 128, 256), floor=S('tfb08', 128, 128), ceiling=S('csbr128', 128, 128),
         door=S('t5d1', 128, 256, fit=True),
         notes="The cell block and the warden's ways: grey ashlar, dark flags, riveted iron doors (t5d1)."),
    dict(id='theme:gate', wall=S('hcwall', 128, 256), floor=S('cstyl', 128, 128), ceiling=S('csbr128', 128, 128),
         door=S('xkportc', 256, 256, fit=True),
         notes="The gatehouse: Castle Ironfist's white ashlar (hcwall) and grey flags (cstyl), the kit's portcullis."),
    dict(id='theme:hall', wall=S('t3s2b1', 128, 256), floor=S('t3s2fl1', 128, 128), ceiling=S('t3s2c', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The great hall and the throne room: the marble set with the carved knotwork dado (t3s2b) as a band."),
    dict(id='theme:library', wall=S('7t1books', 128, 256), floor=S('t3s2fl1', 128, 128), ceiling=S('t3s2c', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The library: shelves of books (7t1books, Castle Harmondale's) on every wall."),
    dict(id='theme:loft', wall=S('hcwall', 128, 256), floor=S('cstyl', 128, 128), ceiling=S('roof', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The top of the west tower: white ashlar under the underside of the old shingle roof (Ironfist's roof)."),
    dict(id='theme:royal', wall=S('t3s2b1', 128, 256), floor=S('t3s2fl1', 128, 128), ceiling=S('7tws1h', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The east tower, the royal family's: the marble walls under Castle Harmondale's warm ceilings."),
    dict(id='theme:service', wall=S('cswl128', 128, 256), floor=S('tfb09', 128, 128), ceiling=S('7tws1h', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The kitchens: grey ashlar and Castle Harmondale's service-room flags (tfb09)."),
    dict(id='theme:tower', wall=S('hcwall', 128, 256), floor=S('cstyl', 128, 128), ceiling=S('7tws1h', 128, 128),
         door=S('chb1dl', 128, 256, fit=True),
         notes="The west tower: the white ashlar of the outside walls inside too (a fortified tower), grey flags."),
]

HALL_BANDS = [FlowDict(height=256, surface=S('t3s2b', 128, 256))]

# Openings: (id, from, to, width, height, extra)
OPENINGS = [
    ('gate_hall', 'gatehouse', 'great_hall', 384, 448, {'link': 'link:gate_hall', 'notes': "The Crusaders' portcullis."}),
    ('gate_kitchens', 'gatehouse', 'kitchens', 288, 320, {'link': 'link:gate_kitchens'}),
    ('hall_throne', 'great_hall', 'throne_room', 384, 512, {'link': 'link:hall_throne'}),
    ('hall_westtower', 'great_hall', 'west_tower_base', 288, 384, {'link': 'link:hall_westtower'}),
    ('hall_well', 'great_hall', 'well_court', 640, 512, {'link': 'link:hall_well'}),
    ('well_library', 'well_court', 'library', 288, 384, {'link': 'link:well_library'}),
    ('library_gallery', 'library', 'armour_gallery', 288, 384, {'link': 'link:library_gallery'}),
    ('throne_gallery', 'throne_room', 'armour_gallery', 512, 512, {'link': 'link:throne_gallery'}),
    ('throne_easttower', 'throne_room', 'east_tower_base', 288, 384, {'link': 'link:throne_easttower'}),
    ('easttower_stair', 'east_tower_base', 'east_stair_1', 384, 384, {}),
    ('eaststair_landing', 'east_stair_1', 'east_landing', 384, 384, {'link': 'link:easttower_parlour'}),
    ('landing_stair', 'east_landing', 'east_stair_2', 384, 384, {}),
    ('eaststair_bedroom', 'east_stair_2', 'royal_bedroom', 288, 384, {'link': 'link:parlour_bedroom'}),
    ('westtower_stair', 'west_tower_base', 'west_stair_1', 384, 384, {}),
    ('weststair_fools', 'west_stair_1', 'fools_hall', 384, 384, {'link': 'link:westtower_fools'}),
    ('fools_gallery', 'fools_hall', 'west_gallery', 512, 384, {'link': 'link:fools_gallery'}),
    ('gallery_stair', 'west_gallery', 'west_stair_2', 384, 384, {}),
    ('weststair_loft', 'west_stair_2', 'gargoyle_loft', 384, 384, {'link': 'link:gallery_loft'}),
    ('loft_throne', 'gargoyle_loft', 'old_throne', 288, 384, {'link': 'link:loft_throne'}),
    ('kitchens_stair', 'kitchens', 'kitchen_stair', 384, 384, {}),
    ('stair_cellar', 'kitchen_stair', 'cellar', 384, 384, {'link': 'link:kitchens_cellar'}),
    ('cellar_cells', 'cellar', 'cell_block', 256, 384, {'link': 'link:cellar_cells'}),
    ('cells_cistern', 'cell_block', 'old_cistern', 512, 448, {'link': 'link:cells_cistern'}),
    ('cistern_den', 'old_cistern', 'troll_den', 512, 448, {'link': 'link:cistern_den'}),
    ('den_cellar', 'troll_den', 'cellar', 256, 384, {'link': 'link:den_cellar'}),
    ('den_postern', 'troll_den', 'postern', 256, 320, {'link': 'link:den_postern'}),
    ('cells_pitgallery', 'cell_block', 'pit_gallery', 256, 384, {'link': 'link:cells_pitgallery'}),
    ('pitgallery_stair', 'pit_gallery', 'pit_stair', 128, 288, {}),
    ('stair_pit', 'pit_stair', 'dragon_pit', 128, 256, {'link': 'link:pitgallery_pit'}),
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
        if r['theme'] == 'hall':
            d['bands'] = Flow(HALL_BANDS)
        walls = WALLS.get(rid)
        if walls:
            d['walls'] = walls
        if rid in PILLARS:
            d['pillars'] = PILLARS[rid]
        if rid in PLATFORMS:
            d['platforms'] = PLATFORMS[rid]
        d['ambient'] = AMBIENT.get(rid, 16)
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
    return {'format': 0, 'themes': THEMES, 'defaults': FlowDict(theme='theme:court', ambient=16), 'rooms': rooms,
            'openings': openings,
            'notes': "XD-07 Castle Burlock at L4: the court floor at 0 (gatehouse, great hall, throne room, gallery of arms, "
                     "library, well court, kitchens), the two towers' floors at 640 and 1280 (west: fools, gallery, "
                     "gargoyle loft, the old throne; east: the princess's landing and the royal bedroom), the cellars and "
                     "the dungeon at -640 and the dragon pit at -1152. No room stands over another. Written by "
                     "output/studio_cal/xd07/tools/gen.py."}


def panel(pid, offset, length, bottom, height, surface, notes=None):
    d = FlowDict(id=pid, offset=offset, length=length, bottom=bottom, height=height, surface=surface)
    if notes:
        d['notes'] = notes
    return d



def _wall_of(rid, other):
    """The wall of room rid that faces room other, and the shared stretch's centre as an offset along that wall."""
    ax0, ay0, ax1, ay1 = ROOMS[rid]['rect']
    bx0, by0, bx1, by1 = ROOMS[other]['rect']
    if bx1 <= ax0:
        wall, lo, hi = 'west', max(ay0, by0), min(ay1, by1)
        return wall, ay1 - (lo + hi) / 2
    if bx0 >= ax1:
        lo, hi = max(ay0, by0), min(ay1, by1)
        return 'east', (lo + hi) / 2 - ay0
    if by1 <= ay0:
        lo, hi = max(ax0, bx0), min(ax1, bx1)
        return 'south', (lo + hi) / 2 - ax0
    lo, hi = max(ax0, bx0), min(ax1, bx1)
    return 'north', ax1 - (lo + hi) / 2


def wall_length(rid, wall):
    x0, y0, x1, y1 = ROOMS[rid]['rect']
    return (x1 - x0) if wall in ('north', 'south') else (y1 - y0)


def busy_spans(rid, wall):
    """Stretches of a wall taken by openings (with 64 of margin each side) and by its own panels."""
    spans = []
    for oid, a, b, w, h, extra in OPENINGS:
        if rid in (a, b):
            other = b if rid == a else a
            wl, c = _wall_of(rid, other)
            if wl == wall:
                spans.append((c - w / 2 - 64, c + w / 2 + 64))
    return spans


def window_panels(rid, wall, texture, every=512, width=128, height=256, bottom=128, prefix='win', extra=()):
    """Panels of one picture (an arrow slit, a window) every `every` along a wall, clear of its openings."""
    length = wall_length(rid, wall)
    spans = busy_spans(rid, wall) + [(a - 32, b + 32) for a, b in extra]
    out = []
    n = 0
    off = every / 2 - width / 2
    while off + width <= length - 64:
        if off >= 64 and all(off + width <= a or off >= b for a, b in spans):
            n += 1
            out.append(panel(f'panel:{prefix}_{rid}_{wall}_{n}', int(off), width, bottom, height,
                             S(texture, 128, 256, fit=True)))
        off += every
    return out

PLAQUE = S('sign128', 256, 128, fit=True)

# Walls are counted counter-clockwise from the outline's first point: south wall runs west->east (offset from x0),
# east wall south->north (offset from y0), north wall east->west (offset from x1), west wall north->south (offset from y1).
WALLS = {
    'gatehouse': [
        {'wall': 'north', 'panels': Flow([
            panel('panel:crest_w', 128, 256, 128, 512, S('xkburcrst', 128, 256, fit=True),
                  "Burlock's arms east of the portcullis (the north wall runs east to west)."),
            panel('panel:crest_e', 896, 256, 128, 512, S('xkburcrst', 128, 256, fit=True),
                  "Burlock's arms west of the portcullis."),
        ])},
        {'wall': 'south', 'panels': Flow([
            panel('panel:castle_door', 448, 384, 0, 384, S('hclgdr', 256, 256, fit=True),
                  "The castle's great door to X4 (Burlock Savannah): sealed until X4 is built (NOTES 'Sealed exits')."),
        ])},
        {'wall': 'east', 'panels': Flow(window_panels('gatehouse', 'east', 'xkarrow', every=384))},
    ],
    'great_hall': [
        {'wall': 'north', 'panels': Flow([
            panel('panel:banner_hall_1', 640, 256, 192, 512, S('xkburban', 128, 256, fit=True)),
            panel('panel:banner_hall_2', 2176, 256, 192, 512, S('xkburban', 128, 256, fit=True)),
            panel('panel:plaque_happy', 1024, 192, 256, 96, PLAQUE, "The plaque 'Don't worry, be happy.' beside the throne room doors."),
        ])},
        {'wall': 'south', 'panels': Flow([
            panel('panel:tap_hall_1', 512, 256, 192, 512, S('tap1', 128, 256, fit=True)),
            panel('panel:tap_hall_2', 2304, 256, 192, 512, S('tap4', 128, 256, fit=True)),
        ])},
    ],
    'throne_room': [
        {'wall': 'north', 'panels': Flow([
            panel('panel:throne_crest', 1088, 384, 256, 768, S('xkburcrst', 128, 256, fit=True),
                  "Burlock's arms, tall, over the throne."),
            panel('panel:banner_throne_e', 448, 256, 256, 640, S('xkburban', 128, 256, fit=True)),
            panel('panel:banner_throne_w', 1856, 256, 256, 640, S('xkburban', 128, 256, fit=True)),
        ])},
        {'wall': 'west', 'panels': Flow([
            panel('panel:tap_throne_1', 512, 256, 192, 512, S('tap7', 128, 256, fit=True)),
            panel('panel:tap_throne_2', 1536, 256, 192, 512, S('tap1', 128, 256, fit=True)),
        ])},
    ],
    'armour_gallery': [
        {'wall': 'north', 'panels': Flow([
            panel('door:advisor', 384, 192, 0, 320, S('chb1dl', 128, 256, fit=True),
                  "The Royal Advisor's study (house 4202, A4's towns/xd07.yml): Artemus."),
            panel('panel:plaque_roland', 1312, 192, 160, 96, PLAQUE, "Under Prince Roland's armour stand."),
            panel('panel:plaque_king', 2016, 192, 160, 96, PLAQUE, "Under King Burlock's armour stand."),
        ])},
        {'wall': 'south', 'panels': Flow([
            panel('door:builder', 2304, 192, 0, 320, S('chb1dr', 128, 256, fit=True),
                  "The Master Builder's office (house 4203): Emerson."),
            panel('panel:banner_gallery', 1920, 256, 128, 448, S('xkburban', 128, 256, fit=True)),
        ])},
        {'wall': 'east', 'panels': Flow(window_panels('armour_gallery', 'east', 'hcwindo', every=768))},
    ],
    'east_landing': [
        {'wall': 'east', 'panels': Flow([
            panel('door:roxanne_parlour', 384, 192, 0, 320, S('chb1dl', 128, 256, fit=True),
                  "The Princess's Parlour (house 4204): Roxanne."),
            panel('panel:plaque_first_day', 640, 192, 160, 96, PLAQUE, "Beside the princess's door."),
        ])},
        {'wall': 'north', 'panels': Flow([panel('panel:tap_landing', 32, 256, 64, 448, S('tap4', 128, 256, fit=True))])},
    ],
    'royal_bedroom': [
        {'wall': 'south', 'panels': Flow([
            panel('panel:plaque_think_thin', 1184, 192, 160, 96, PLAQUE, "Over the dressing table."),
        ])},
        {'wall': 'north', 'panels': Flow([
            panel('panel:tap_bed', 512, 256, 160, 448, S('tap7', 128, 256, fit=True)),
        ])},
        {'wall': 'west', 'panels': Flow(window_panels('royal_bedroom', 'west', 'hcwindo', every=512))},
    ],
    'east_tower_base': [{'wall': 'east', 'panels': Flow([
        panel('panel:tap_easttower', 64, 256, 128, 448, S('tap1', 128, 256, fit=True))])}],
    'west_tower_base': [{'wall': 'south', 'panels': Flow(window_panels('west_tower_base', 'south', 'xkarrow'))}],
    'fools_hall': [
        {'wall': 'south', 'panels': Flow(window_panels('fools_hall', 'south', 'xkarrow'))},
        {'wall': 'west', 'panels': Flow([
            panel('panel:plaque_sharp', 640, 192, 160, 96, PLAQUE, "The fools' plaque."),
        ])},
    ],
    'west_gallery': [
        {'wall': 'west', 'panels': Flow([
            panel('panel:plaque_ruler', 384, 192, 160, 96, PLAQUE),
            panel('panel:plaque_sword', 1024, 192, 160, 96, PLAQUE),
            panel('panel:plaque_nice_day', 1664, 192, 160, 96, PLAQUE),
        ] + window_panels('west_gallery', 'west', 'xkarrow', every=640,
                          extra=[(384, 576), (1024, 1216), (1664, 1856)]))},
        {'wall': 'east', 'panels': Flow(window_panels('west_gallery', 'east', 'xkarrow', every=640))},
    ],
    'gargoyle_loft': [{'wall': 'west', 'panels': Flow(window_panels('gargoyle_loft', 'west', 'xkarrow'))},
                      {'wall': 'east', 'panels': Flow(window_panels('gargoyle_loft', 'east', 'xkarrow'))}],
    'old_throne': [{'wall': 'north', 'panels': Flow(window_panels('old_throne', 'north', 'hcwindo', every=640, bottom=192,
                                                                  extra=[(512, 768)]))},
                   {'wall': 'west', 'panels': Flow(window_panels('old_throne', 'west', 'xkarrow'))}],
    'well_court': [{'wall': 'east', 'panels': Flow(window_panels('well_court', 'east', 'hcwindo', every=384))}],
    'library': [{'wall': 'south', 'surface': S('t3s2b1', 128, 256)}],
    'pit_gallery': [{'wall': 'south', 'panels': Flow([
        panel('panel:warning', 1472, 192, 96, 96, S('warnsign', 256, 128, fit=True),
              "The warden's sign beside the cage lever: 'Do not pull.'"),
    ])}],
}
# The postern: a live exit once X4 is in the world (lane A7 fifth session, made in L4 by hand then; folded into this
# generator in the sixth session), else the sealed panel.
if not X4_IN:
    WALLS['postern'] = [{'wall': 'west', 'panels': Flow([
        panel('panel:postern_door', 128, 256, 0, 320, S('t5d1', 128, 256, fit=True),
              "The sally port to the moat on X4, barred: sealed until X4 is built (NOTES 'Sealed exits')."),
    ])}]

PILLARS = {
    'great_hall': Flow([FlowDict(at=F(x, y), size=F(128, 128), surface=S('t3elr', 128, 256))
                        for x in (-640, 640) for y in (1920, 2688)]),
    'throne_room': Flow([FlowDict(at=F(x, y), size=F(128, 128), surface=S('t3elr', 128, 256))
                         for x in (-768, 768) for y in (4224, 5120)]),
    'old_cistern': Flow([FlowDict(at=F(x, y), size=F(160, 160), surface=S('cswl128', 128, 256))
                         for x, y in ((-192, -4992), (1216, -4992), (1216, -4096))]),
}


def block(at, size, rise, surface, top=None, notes=None, pid=None, base=None):
    d = FlowDict()
    if pid:
        d['id'] = pid
    d['at'] = F(*at)
    d['size'] = F(*size)
    d['rise'] = rise
    d['surface'] = surface
    if top:
        d['top_surface'] = top
    if base is not None:
        d['base'] = base
    if notes:
        d['notes'] = notes
    return d


MARBLE = S('7tws1f', 128, 128)
WOOD = S('7t1beds', 256, 64)
STONE = S('csbr128', 128, 128)
PLATFORMS = {
    'throne_room': Flow([
        block((0, 5824), (1536, 448), 48, MARBLE, MARBLE, "The dais under the arms."),
        block((0, 5952), (192, 160), 112, S('t3elr', 128, 256), S('tfb09r1i', 64, 64), "The throne of Burlock: "
              "its seat (clicked: the audience, house 4201).", pid='platform:throne'),
        block((0, 6080), (224, 64), 352, S('t3elr', 128, 256), MARBLE, "The throne's tall back."),
    ]),
    'well_court': Flow([
        block((2304, 1664), (320, 320), 64, STONE, S('7wtrtyl', 128, 128, liquid='water'), "The well: a stone kerb round dark water "
              "(clicked: 'The water refreshes you.').", pid='platform:well'),
    ]),
    'library': Flow([
        block((1984, 2816), (256, 128), 96, WOOD, WOOD, "Reading desk with the Book of Languages.", pid='platform:book_languages'),
        block((3136, 2816), (256, 128), 96, WOOD, WOOD, "Reading desk with the Book of Astrology.", pid='platform:book_astrology'),
    ]),
    'armour_gallery': Flow([
        block((2944, 4224), (192, 160), 48, MARBLE, MARBLE, "Prince Roland's armour stand: a plinth with its statue."),
        block((2240, 4224), (192, 160), 48, MARBLE, MARBLE, "King Burlock's armour stand."),
    ]),
    'kitchens': Flow([
        block((-2176, 384), (192, 384), 64, STONE, STONE, "The kitchen hearth's stone floor (the fire on it)."),
        block((-1600, 512), (512, 192), 80, WOOD, WOOD, "The kitchen table."),
    ]),
    'royal_bedroom': Flow([
        block((4224, 8192), (384, 384), 64, WOOD, S('tfb09r1i', 64, 64), "The royal bed."),
        block((5120, 7552), (384, 128), 80, S('7t1cab', 128, 256), WOOD, "The princess's dressing table."),
    ]),
    'fools_hall': Flow([
        block((-5248, 1792), (384, 192), 48, WOOD, WOOD, "The fools' straw pallets: a low board."),
    ]),
    'old_throne': Flow([
        block((-4992, 9472), (256, 192), 112, STONE, S('tfb09r1i', 64, 64), "The old King's throne: its seat "
              "(clicked: the throw).", pid='platform:old_throne'),
        block((-4992, 9600), (288, 64), 384, STONE, STONE, "The old throne's back."),
    ]),
    'cell_block': Flow([
        block((x, -1760), (16, 448), 512, S('xwcage', 128, 256), S('cswl128', 128, 256), "Cell bars, broken open.")
        for x in (0, 512, 1024)
    ] + [
        block((256, -1600), (128, 64), 48, WOOD, WOOD, "A cell bench."),
        block((768, -1600), (128, 64), 48, WOOD, WOOD, "A cell bench."),
    ]),
    'old_cistern': Flow([
        block((512, -4480), (512, 512), 24, STONE, S('7wtrtyl', 128, 128, liquid='water'), "The last of the cistern's water in a "
              "stone basin."),
    ]),
    'dragon_pit': Flow([
        block((3456, -5760), (768, 768), 32, S('gcav1flr', 256, 256), S('gcav2flr', 128, 128, scale=2),
              "The dragon's hoard mound, against the pit's south wall (F6, 2026-11-21: it stopped 256 short of it)."),
    ]),
}

AMBIENT = {'gatehouse': 18, 'great_hall': 20, 'throne_room': 22, 'cellar': 12, 'cell_block': 10, 'pit_gallery': 10,
           'pit_stair': 8, 'dragon_pit': 10, 'old_cistern': 10, 'troll_den': 8, 'postern': 8, 'gargoyle_loft': 12,
           'old_throne': 14, 'fools_hall': 12, 'west_gallery': 12}

ROOM_NOTES = {
    'gatehouse': "Inside the castle door: the portcullis in the north wall lifts only for Crusaders (m5.crusaders_gate); "
                 "two King's Guards; the kitchens' door in the west wall. The arrival.",
    'great_hall': "The court: four marble pilasters, Burlock's banners and Harmondale's tapestries, King's Guards; the "
                  "throne room doors north, the well court's arch east, the closed door of the west tower west.",
    'throne_room': "The throne on its dais under the arms, between two rows of pilasters; the gallery of arms opens east, "
                   "the royal family's door to the east tower behind it.",
    'armour_gallery': "The gallery of arms: the two ceremonial armour stands with their plaques, the doors of Artemus "
                      "(north) and Emerson (south), the library's door.",
    'library': "Shelves on every wall, two reading desks (the Book of Languages, the Book of Astrology).",
    'well_court': "A small court round the castle well.",
    'east_tower_base': "The foot of the royal family's tower, behind the throne room.",
    'east_stair_1': "Twenty marble steps up the east tower.",
    'east_landing': "The princess's landing: her parlour's door (house 4204) and her plaque.",
    'east_stair_2': "The stair to the royal bedroom.",
    'royal_bedroom': "The royal bedroom at the top of the east tower: the bed, the dressing table, Roxanne's chest.",
    'west_tower_base': "The foot of the west tower behind its closed door (D-4): the fools' noise above.",
    'west_stair_1': "Twenty worn steps up the west tower.",
    'fools_hall': "The jesters' quarters: pallets, rubbish, the mad fools.",
    'west_gallery': "The west tower's gallery of arrow slits and joke plaques; gargoyles at the slits.",
    'west_stair_2': "The stair to the top of the west tower.",
    'gargoyle_loft': "The roosts under the west tower's roof; the gargoyles' chest of shiny things.",
    'old_throne': "Burlock's grandfather's throne under the tower's roof: sit on it and it throws you out.",
    'kitchens': "The servants' way from the gate: hearth, table, larder sacks, the cellar stair.",
    'kitchen_stair': "Twenty steps down from the kitchens to the wine cellar.",
    'cellar': "The wine cellar, a storeroom (barrels and casks in rows along its walls); the iron dungeon door east, the "
              "troll den's barred door south.",
    'cell_block': "Broken cells along the north wall, the warden's strongbox; the pit gallery's door east, the old "
                  "cistern south.",
    'pit_gallery': "The warden's walk above the dragon pit: the cage lever and his sign; the narrow stair down.",
    'pit_stair': "A narrow, low stair down to the pit's portcullis: 160 wide, too narrow for the dragon.",
    'dragon_pit': "The caged Fire Dragon on its hoard (optional).",
    'old_cistern': "The castle's old cistern, dry but for a basin; the Black Liquid in a bucket.",
    'troll_den': "Where the trolls sleep on rotten straw; their pile of loot; the barred door to the cellar.",
    'postern': ("The sally port, out to the castle rise's west foot on X4 (exit:postern)." if X4_IN
                else "A sally port toward the moat, barred."),
}

# ---------------------------------------------------------------------------------------------------------------------
# objects.yml


WINGS = F(F(S('chb1dl', 128, 256), S('chb1dr', 128, 256)))
# The pairs' doorways are 288 wide (were 256 with one leaf): each leaf stands in the middle of a 256-deep doorway, and a
# leaf 128 wide swung open would end in the room's wall face (z-fighting, the build's coplanar warning); one 144 wide
# lies along the reveal and stands 16 out of it, and the open doorway stays as wide as before (a leaf swung 80 degrees
# instead narrowed it and hid the party from the kitchens in playtest_hostility).
WING_PAIR = {'kind': 'hinged', 'leaves': 2, 'thickness': 16, 'pictures': WINGS}


def objects_yml():
    doors = [
        {'id': 'door:portcullis', 'opening': 'open:gate_hall', 'kind': 'slide_up', 'thickness': 16, 'speed': 80,
         'surface': S('xkportc', 256, 256, scale=1.75), 'tile': True,
         'notes': "The Crusaders' portcullis (the kit's xkportc, a cut-out): it lifts only for Crusaders."},
        # Castle Harmondale's oak doors are double doors: chb1dl and chb1dr are its left and right wings (twins), one on
        # each leaf of a pair (DOORS.md; A1's door check, merge point 15). The 256-wide doorways are hinged pairs.
        {'id': 'door:kitchens', 'opening': 'open:gate_kitchens', **WING_PAIR},
        {'id': 'door:throne_doors', 'opening': 'open:hall_throne', 'kind': 'slide_left', 'leaves': 2, 'thickness': 16,
         'pictures': WINGS, 'notes': "The throne room's double doors: the left and the right wing."},
        {'id': 'door:west_tower', 'opening': 'open:hall_westtower', **WING_PAIR,
         'notes': "The closed door at the foot of the west tower (D-4): the fools and gargoyles behind it."},
        {'id': 'door:library_s', 'opening': 'open:well_library', **WING_PAIR},
        {'id': 'door:library_n', 'opening': 'open:library_gallery', **WING_PAIR},
        {'id': 'door:east_tower', 'opening': 'open:throne_easttower', **WING_PAIR},
        {'id': 'door:bedroom', 'opening': 'open:eaststair_bedroom', **WING_PAIR},
        {'id': 'door:old_throne', 'opening': 'open:loft_throne', **WING_PAIR},
        {'id': 'door:dungeon', 'opening': 'open:cellar_cells', 'kind': 'slide_up', 'thickness': 24,
         'surface': S('t5d1', 128, 256, fit=True), 'notes': "The iron dungeon door (Artemus's key, a qbit)."},
        {'id': 'door:den_bar', 'opening': 'open:den_cellar', 'kind': 'slide_up', 'thickness': 24,
         'surface': S('t5d1', 128, 256, fit=True), 'notes': "Barred on the den side: lifting the bar closes the dungeon ring."},
        {'id': 'door:postern_inner', 'opening': 'open:den_postern', 'kind': 'slide_up', 'thickness': 24,
         'surface': S('t5d1', 128, 256, fit=True)},
        {'id': 'door:cell_door', 'opening': 'open:cells_pitgallery', 'kind': 'slide_up', 'thickness': 24,
         'surface': S('t5d1', 128, 256, fit=True)},
        {'id': 'door:pit_portcullis', 'opening': 'open:stair_pit', 'kind': 'slide_up', 'thickness': 16, 'speed': 48,
         'surface': S('xkportc', 256, 256), 'tile': True,
         'notes': "The cage portcullis at the stair's foot, raised only by the warden's lever (D-4)."},
    ]
    switches = [
        {'id': 'switch:cage_lever', 'room': 'room:pit_gallery', 'kind': 'lever', 'at': F(3168, -2816),
         'off': S('t5d1', 128, 256), 'notes': "The warden's lever, beside his 'Do not pull' sign."},
        {'id': 'switch:den_bar', 'room': 'room:troll_den', 'kind': 'lever', 'at': F(-1408, -3328),
         'off': S('t5d1', 128, 256), 'notes': "The bar's handle on the den side of the cellar door."},
    ]
    chests = [
        {'id': 'chest:loft', 'room': 'room:gargoyle_loft', 'at': F(-5664, 8000), 'kind': 'ch1', 'facing': 'e',
         'treasure_level': 2, 'random_items': 3, 'gold': 300, 'notes': "The gargoyles' chest of shiny things."},
        {'id': 'chest:roxanne', 'room': 'room:royal_bedroom', 'at': F(5152, 8224), 'kind': 'ch1', 'facing': 'w',
         'treasure_level': 3, 'random_items': 4, 'gold': 1000,
         'notes': "Roxanne's chest (q-c3.bedroom_chest): opens once Q-C3 is done; the map's T3 loot."},
        {'id': 'chest:warden', 'room': 'room:cell_block', 'at': F(1344, -3136), 'kind': 'ch1', 'facing': 'n',
         'treasure_level': 2, 'random_items': 2, 'gold': 250, 'notes': "The warden's strongbox."},
        {'id': 'chest:den', 'room': 'room:troll_den', 'at': F(-2592, -5152), 'kind': 'ch1', 'facing': 'e',
         'treasure_level': 2, 'random_items': 3, 'gold': 200, 'notes': "The trolls' pile of loot."},
        {'id': 'chest:hoard', 'room': 'room:dragon_pit', 'at': F(3712, -6096), 'kind': 'ch1', 'facing': 'e',
         'treasure_level': 3, 'random_items': 5, 'gold': 3000, 'floor_height': -1120,
         'notes': "The dragon's hoard (tier 3) on its mound, its back to the south wall and its front north (F6, "
                  "2026-11-21: it stood at (3712, -5856) half over the mound's edge)."},
    ]
    spawns = []

    def sp(name, rid, at, slot, tier, group=51, notes=None):
        d = {'id': f'spawn:{name}', 'room': f'room:{rid}', 'at': F(*at), 'slot': slot, 'tier': tier, 'group': group}
        if notes:
            d['notes'] = notes
        spawns.append(d)

    # Madmen (slot 1): Raving Lunatic 12 (c), Mad Fool 8 (b) (D-4)
    sp('fools_1', 'fools_hall', (-5248, 2432), 1, 'c')
    sp('fools_2', 'fools_hall', (-4736, 2176), 1, 'c')
    sp('fools_3', 'fools_hall', (-4864, 2816), 1, 'b')
    sp('wgallery_1', 'west_gallery', (-4992, 3840), 1, 'c')
    sp('wgallery_2', 'west_gallery', (-4992, 4864), 1, 'b')
    sp('kitchens', 'kitchens', (-1408, 128), 1, 'b', notes="Two fools raiding the larder.")
    sp('cellar_1', 'cellar', (-2048, -2176), 1, 'c')
    sp('cellar_2', 'cellar', (-1152, -2688), 1, 'c')
    # Gargoyles (slot 2): Gargoyle 16 (a), Gargoyle Lord 22 (b)
    sp('wgallery_garg', 'west_gallery', (-4864, 5120), 2, 'a', notes="Gargoyles at the slits.")
    sp('loft_1', 'gargoyle_loft', (-5504, 7296), 2, 'a')
    sp('loft_2', 'gargoyle_loft', (-4480, 7296), 2, 'a')
    sp('loft_3', 'gargoyle_loft', (-4992, 7680), 2, 'b')
    sp('loft_4', 'gargoyle_loft', (-5504, 7936), 2, 'a')
    sp('loft_5', 'gargoyle_loft', (-4480, 7936), 2, 'b')
    sp('throne_1', 'old_throne', (-5248, 8960), 2, 'a')
    sp('throne_2', 'old_throne', (-4736, 8960), 2, 'b')
    # Trolls (slot 3): Troll 18 (a)
    sp('cells_1', 'cell_block', (0, -2432), 3, 'a')
    sp('cells_2', 'cell_block', (1024, -2432), 3, 'a')
    sp('cells_3', 'cell_block', (512, -3008), 3, 'a')
    sp('pitgallery', 'pit_gallery', (2304, -2432), 3, 'a')
    sp('cistern_1', 'old_cistern', (-128, -4480), 3, 'a')
    sp('cistern_2', 'old_cistern', (1152, -4480), 3, 'a')
    sp('cistern_3', 'old_cistern', (512, -5120), 3, 'a')
    sp('den_1', 'troll_den', (-1792, -4352), 3, 'a')
    sp('den_2', 'troll_den', (-2304, -4864), 3, 'a')
    sp('den_3', 'troll_den', (-1280, -4864), 3, 'a')

    monsters = []

    def guard(name, rid, at, facing):
        monsters.append({'id': f'monster:{name}', 'room': f'room:{rid}', 'monster': 11143, 'at': F(*at),
                         'facing': facing, 'group': 30, 'immobile': True,
                         'notes': "King's Guard (11143, level 40): peaceful to the party by the world's relation "
                                  "(xeen_burlock_knights_d, D-4)."})

    guard('guard_gate_w', 'gatehouse', (-384, 832), 0)
    guard('guard_gate_e', 'gatehouse', (384, 832), 180)
    guard('guard_hall_w', 'great_hall', (-1280, 3072), 0)
    guard('guard_hall_e', 'great_hall', (1280, 3072), 180)
    guard('guard_throne_w', 'throne_room', (-448, 5504), 0)
    guard('guard_throne_e', 'throne_room', (448, 5504), 180)
    guard('guard_easttower', 'east_tower_base', (2304, 5632), 270)
    monsters.append({'id': 'monster:fire_dragon', 'room': 'room:dragon_pit', 'monster': 11642, 'at': F(3456, -5120),
                     'facing': 90, 'hostile': True, 'group': 40,
                     'notes': "The caged Fire Dragon (11642, level 75, Dragons C): optional, behind the warden's "
                              "portcullis at the foot of a stair 160 wide (its body 476 across, 487 high)."})

    decos = []

    def deco(name, rid, d, at=None, **kw):
        e = {'id': f'deco:{name}', 'room': f'room:{rid}', 'decoration': d}
        if at:
            e['at'] = F(*at)
        e.update(kw)
        decos.append(e)

    # Torches on the walls (Castle Harmondale's torch01)
    torches = [
        ('gatehouse', 'east'), ('gatehouse', 'west', 0.2),
        ('great_hall', 'east', 0.8), ('great_hall', 'west', 0.8), ('great_hall', 'west', 0.2),
        ('throne_room', 'east', 0.85), ('throne_room', 'west', 0.85), ('throne_room', 'west', 0.15),
        ('armour_gallery', 'north', 0.62), ('library', 'east'), ('well_court', 'north', 0.2),
        ('east_tower_base', 'north'), ('east_landing', 'south'), ('royal_bedroom', 'east'),
        ('west_tower_base', 'north'), ('fools_hall', 'north', 0.15), ('west_gallery', 'west', 0.39),
        ('gargoyle_loft', 'south', 0.25), ('old_throne', 'east'), ('kitchens', 'north'),
        ('cellar', 'west'), ('cell_block', 'west', 0.2), ('cell_block', 'south', 0.25), ('pit_gallery', 'north'),
        ('old_cistern', 'west', 0.15), ('old_cistern', 'east'), ('troll_den', 'east', 0.7),
        ('dragon_pit', 'north', 0.75), ('postern', 'north'),
    ]
    for i, t in enumerate(torches):
        kw = {'wall': t[1]}
        if len(t) > 2:
            kw['along'] = t[2]
        deco(f'torch_{i + 1:02d}', t[0], 'torch01', height=176, **kw)
    # Chandeliers and braziers of the court
    deco('chandelier_hall_w', 'great_hall', 'dec27', (-640, 2304), hangs=True)
    deco('chandelier_hall_e', 'great_hall', 'dec27', (640, 2304), hangs=True)
    deco('chandelier_throne', 'throne_room', 'dec27', (0, 4672), hangs=True)
    deco('brazier_dais_w', 'throne_room', 'flamb00', (-1088, 5888))
    deco('brazier_dais_e', 'throne_room', 'flamb00', (1088, 5888))
    # Statues for the armour stands
    deco('armour_roland', 'armour_gallery', '7dec55', (2944, 4224), floor_height=48)
    deco('armour_king', 'armour_gallery', '7dec54', (2240, 4224), floor_height=48)
    # Library candles
    deco('candle_languages', 'library', 'dec02', (1920, 2816), floor_height=96)
    deco('candle_astrology', 'library', 'dec02', (3200, 2816), floor_height=96)
    # Kitchens: the hearth fire, a fruit bowl, a pair of sacks against the west wall by the hearth
    deco('hearth_fire', 'kitchens', 'ckfyr00', (-2176, 384), floor_height=64)
    deco('fruit_bowl', 'kitchens', '7dec08', (-1600, 512), floor_height=80)
    deco('sack_1', 'kitchens', 'floursac', (-2176, 832))
    deco('sack_2', 'kitchens', 'bag01', (-2048, 896))
    # Wine cellar: a storeroom (rows of barrels and casks along the walls, 12 containers)
    for i, (x, y) in enumerate([(-2432, -2048), (-2432, -2176), (-2432, -2304), (-2432, -2560), (-2432, -2688),
                                (-2432, -2944)]):
        deco(f'cellar_barrel_{i + 1}', 'cellar', '7dec32', (x, y))
    for i, (x, y) in enumerate([(-2176, -2944), (-2048, -2944), (-2304, -1920), (-2176, -1920)]):
        deco(f'cellar_cask_{i + 1}', 'cellar', '7dec21', (x, y))
    for i, (x, y) in enumerate([(-896, -2048), (-896, -1920)]):
        deco(f'cellar_keg_{i + 1}', 'cellar', 'smlbarel', (x, y))
    # Cell block: bones in the cells, the sludge bucket
    deco('cell_bones', 'cell_block', '7dec18', (256, -1792))
    deco('cell_bucket', 'cell_block', 'Bucket', (1408, -1664))
    # Old cistern: the Black Liquid's bucket on the dry floor by the basin
    deco('black_liquid', 'old_cistern', 'Bucket', (512, -4096))
    # Troll den: rubbish and bones (cave rubble, off the walking lines)
    deco('den_trash', 'troll_den', '7dec01', (-2560, -3712))
    deco('den_bones', 'troll_den', 'dec19', (-1024, -5120))
    deco('den_skull', 'troll_den', '7dec20', (-2560, -4608))
    # Dragon pit: bones of the dragon's meals
    deco('pit_bones_1', 'dragon_pit', '7dec18', (2176, -5888))
    deco('pit_bones_2', 'dragon_pit', 'sklplrev', (3904, -4480))
    # Fools' hall and loft
    deco('fools_trash', 'fools_hall', '7dec01', (-5440, 2944))
    deco('fools_goblet', 'fools_hall', '7dec48', (-5248, 1792), floor_height=688)
    deco('loft_bones', 'gargoyle_loft', '7dec18', (-4352, 8000))

    lights = []

    def light(name, rid, at, height, radius, color):
        lights.append({'id': f'light:{name}', 'room': f'room:{rid}', 'at': F(*at), 'height': height, 'radius': radius,
                       'color': F(*color)})

    warm = (255, 200, 140)
    for rid in ROOMS:
        if ROOMS[rid].get('slope'):
            continue
        r = ROOMS[rid]
        h = min(r['ceiling'] - r['floor'] - 64, 640)
        radius = 1400 if rid in ('great_hall', 'throne_room', 'dragon_pit') else 1000
        col = warm if r['floor'] >= 0 else (200, 170, 140)
        if rid == 'dragon_pit':
            col = (255, 120, 60)
        light(rid, rid, (cx(rid), cy(rid)), h, radius, col)

    exits = []
    if X4_IN:
        exits.append({'id': 'exit:castle_door', 'room': 'room:gatehouse', 'wall': 'south', 'size': F(384, 384),
                      'surface': S('7solid01', 256, 256, fit=True), 'to': 'exit:x4_gate',
                      'notes': "The castle's great door, out onto the castle rise on X4 (Burlock Savannah)."})
        exits.append({'id': 'exit:postern', 'room': 'room:postern', 'wall': 'west', 'along': 0.5, 'size': F(256, 320),
                      'surface': S('7solid01', 128, 256, fit=True), 'to': 'exit:x4_moat',
                      'notes': "The sally port, out to the flat ground at the castle rise's west foot on X4 (A5's point; "
                               "X4 has no moat)."})
    relations = []
    return {'format': 0,
            'start': {'room': 'room:gatehouse', 'at': F(0, 384), 'facing': 90,
                      'notes': "Inside the castle door, facing the Crusaders' portcullis."},
            'doors': doors, 'lights': lights, 'switches': switches, 'chests': chests, 'spawns': spawns,
            'monsters': monsters, 'decorations': decos, 'exits': exits, 'relations': relations}


# ---------------------------------------------------------------------------------------------------------------------
# wiring.yml


def hook(name):
    return {'lua': f'XeenQuests.hook("{name}")'}


def wiring_yml():
    ev = []

    def e(**kw):
        ev.append(kw)

    e(id='evt:arrive', preset='script', trigger='timer', every=1, once=True,
      effects=[{'message': "Castle Burlock, seat of King Burlock of Cloudside. Beyond the portcullis lies the court; "
                           "the guards let only Crusaders through."}],
      notes="Say where the party is (a one-shot timer: a load event's window is not shown). A3 has no arrival hook "
            "for XD-07.")
    e(id='evt:portcullis', preset='script', source='door:portcullis', title='Portcullis',
      condition={'qbit': 'crusader'}, opens=['door:portcullis'], effects=[hook('m5.crusaders_gate')],
      else_effects=[hook('m5.crusaders_gate')],
      notes="m5.crusaders_gate: opens for Crusaders (m4.done 110047); otherwise the hook's fail text, the source's "
            "'Only Crusaders are allowed to enter Castle Burlock.' (aaze0014:8).")
    if X4_IN:
        e(id='evt:castle_door', preset='exit', source='exit:castle_door', title='Castle door',
          text="You step out onto the castle rise.",
          notes="Out to X4's castle rise in front of the gate (A5's arrival, facing south).")
    else:
        e(id='evt:castle_door', preset='text', source='panel:castle_door', title='Castle door', window=True,
          text="The great doors are barred from outside. Through the crack a guard calls: 'Nobody leaves till the Captain "
           "says so, Crusaders. The savannah's no place to be today.'",
          notes="Sealed exit to X4 (not built): NOTES 'Sealed exits' says how it becomes the exit.")
    e(id='evt:door_kitchens', preset='door', source='door:kitchens', title='Kitchens')
    e(id='evt:door_throne', preset='door', source='door:throne_doors', title='Throne room')
    e(id='evt:door_west_tower', preset='door', source='door:west_tower', title='West tower')
    e(id='evt:door_library_s', preset='door', source='door:library_s', title='Library')
    e(id='evt:door_library_n', preset='door', source='door:library_n', title='Library')
    e(id='evt:door_east_tower', preset='door', source='door:east_tower', title='East tower')
    e(id='evt:door_bedroom', preset='door', source='door:bedroom', title='Royal bedroom')
    e(id='evt:door_old_throne', preset='door', source='door:old_throne', title='Door')
    e(id='evt:door_cells', preset='door', source='door:cell_door', title='Door')
    e(id='evt:door_postern', preset='door', source='door:postern_inner', title='Postern')
    e(id='evt:throne', preset='script', source='platform:throne', title='King Burlock',
      condition={'qbit': 'crusader'}, effects=[{'lua': 'evt.EnterHouse(4201)'}],
      else_effects=[{'message': "Only Crusaders are allowed to enter Castle Burlock."}],
      notes="The audience: A4's house 4201 Throne Room (the King, Prince Roland), opens on m4.done with its closed "
            "text; the throne is the house's door (A4's door:throne_room).")
    e(id='evt:advisor', preset='script', source='door:advisor', title="Royal Advisor's Study",
      effects=[{'lua': 'evt.EnterHouse(4202)'}], notes="A4's house 4202: Artemus (M6, M7, the dungeon key).")
    e(id='evt:builder', preset='script', source='door:builder', title="Master Builder's Office",
      effects=[{'lua': 'evt.EnterHouse(4203)'}], notes="A4's house 4203: Emerson (M9, M11, M22).")
    e(id='evt:roxanne', preset='script', source='door:roxanne_parlour', title="The Princess's Parlour",
      effects=[{'lua': 'evt.EnterHouse(4204)'}], notes="A4's house 4204: Princess Roxanne (Q-C3, T1-E).")
    for name, src in [('happy', 'plaque_happy'), ('king_armour', 'plaque_king'), ('roland_armour', 'plaque_roland'),
                      ('first_day', 'plaque_first_day'), ('think_thin', 'plaque_think_thin'), ('sharp', 'plaque_sharp'),
                      ('ruler', 'plaque_ruler'), ('sword', 'plaque_sword'), ('nice_day', 'plaque_nice_day')]:
        e(id=f'evt:plaque_{name}', preset='script', source=f'panel:{src}', title='Plaque',
          effects=[hook(f'xd07.plaque_{name}')], notes=f"A3's hook xd07.plaque_{name} (its message window).")
    e(id='evt:well', preset='script', source='platform:well', title='Well',
      effects=[{'add': {'var': 'HP', 'value': 20}}, {'text': "The water refreshes you."}],
      notes="The source's well (aaze0064:29): a drink heals a little, as often as the party likes.")
    e(id='evt:book_languages', preset='script', source='platform:book_languages', title='Book of Languages',
      effects=[hook('xd07.book_languages')],
      notes="A3's hook xd07.book_languages (its window): the first read sets the shared Linguist gate (116240, award "
            "420) that the Cloudside rhyme statues (X8, X9) ask; later reads the plain text.")
    e(id='evt:book_astrology', preset='text', source='platform:book_astrology', title='Book of Astrology', window=True,
      text="The Book of Astrology: charts of the four moons of Xeen. A note in the margin says the moons line up over "
           "the pyramids only once in a long while, and that no one has seen it in years.")
    e(id='evt:dungeon_door', preset='script', source='door:dungeon', title='Dungeon door',
      opens=['door:dungeon'], effects=[hook('xd07.dungeon_door')],
      notes="xd07.dungeon_door: the cellar's iron door opens (D-89, 2026-11-22: the dungeon is unlocked; Artemus's "
            "key 116080 is no longer tested).")
    e(id='evt:den_bar', preset='switch', source='switch:den_bar', title='Bar', condition={'not': {'qbit': 'den_bar_lifted'}},
      opens=['door:den_bar'], sets={'qbit': 'den_bar_lifted'},
      text="You lift the heavy bar out of its brackets: the door to the wine cellar swings free.",
      else_effects=[{'text': "The bar is off; the door to the cellar is open."}],
      notes="state:den_bar: the bar on the den side closes the dungeon ring.")
    e(id='evt:den_door_cellar', preset='door', source='door:den_bar', side='room:cellar', title='Door',
      condition={'qbit': 'den_bar_lifted'}, locked_text="The door won't budge: it is barred on the other side.",
      notes="From the cellar the barred door does not move until the bar is lifted in the den.")
    e(id='evt:den_door_den', preset='door', source='door:den_bar', side='room:troll_den', title='Door',
      condition={'qbit': 'den_bar_lifted'}, locked_text="A heavy bar holds the door shut. Lift it by its handle.")
    e(id='evt:cage_lever', preset='switch', source='switch:cage_lever', title='Lever',
      condition={'not': {'qbit': 'cage_lever_pulled'}}, opens=['door:pit_portcullis'],
      sets={'qbit': 'cage_lever_pulled'},
      effects=[{'shake': {'strength': 0.6, 'seconds': 2}}],
      text="Chains rattle deep below: the portcullis at the foot of the stair grinds up. Something very large stirs.",
      else_effects=[{'text': "The lever is down. Below, the portcullis stands open."}],
      notes="state:cage_lever: the optional fight (D-4).")
    e(id='evt:warning', preset='text', source='panel:warning', title='Sign', window=True,
      text="The sign reads: DO NOT PULL. --The Warden",
      notes="The warden's warning beside the lever (ours, after the graph).")
    e(id='evt:pit_portcullis', preset='door', source='door:pit_portcullis', title='Portcullis', action='open',
      condition={'qbit': 'cage_lever_pulled'},
      locked_text="The portcullis does not move. Its chains run up into the rock toward the gallery above.")
    e(id='evt:dragon_dead', preset='text', trigger='timer', every=2, once=True,
      condition={'kills': {'monster': 'monster:fire_dragon'}},
      text="The Fire Dragon crashes down on its hoard and lies still.")
    e(id='evt:black_liquid', preset='script', source='deco:black_liquid', title='Bucket',
      condition={'not': {'player_bit': PLAYER_BIT_BLACK}},
      effects=[{'player_bit': PLAYER_BIT_BLACK}, {'add': {'var': 'BaseMight', 'value': 2}},
               {'text': "Black Liquid. +2 Might (permanent)."}],
      else_effects=[{'text': "The black liquid does nothing more for you."}],
      notes="The source's Black Liquid (aaze0063:3), rescaled to +2 Might once per character (D-4 values).")
    if X4_IN:
        e(id='evt:old_throne', preset='script', source='platform:old_throne', title='Old throne',
          effects=[{'shake': {'strength': 1, 'seconds': 1}}, hook('xd07.old_throne'), {'leave': 'exit:x4_air'}],
          notes="The throw (D-4): onto X4 about 1,000 above the rise beside the west tower outside the walls; the "
                "game's fall damage hurts the party. A3's hook xd07.old_throne gives the source's line (aaze0065:7).")
    else:
      e(id='evt:old_throne', preset='script', source='platform:old_throne', title='Old throne',
      effects=[{'shake': {'strength': 1, 'seconds': 1}}, {'damage': {'amount': 20, 'kind': 'physical'}},
               {'set': {'var': {'map_var': 'thrown'}, 'value': 1}},
               {'teleport': {'to': F(0, 384, 0), 'direction': 90}}],
      notes="The throw (D-4: onto X4 about 1,000 above the ground beside the west tower). X4 is not built: for now the "
            "party lands inside the castle door with a fall's damage (NOTES 'Sealed exits').")
    if not X4_IN:
      e(id='evt:old_throne_landed', preset='script', trigger='timer', every=1,
      condition={'map_var': {'name': 'thrown', 'equals': 1}},
      effects=[{'set': {'var': {'map_var': 'thrown'}, 'value': 0}}, hook('xd07.old_throne')],
      notes="The throw's message once the party has landed (a window opened before the teleport closes with it): "
            "A3's hook xd07.old_throne, the source's 'You teleported into the air outside the tower!' (aaze0065:7).")
    if X4_IN:
      e(id='evt:postern', preset='exit', source='exit:postern', title='Postern',
        text="You lift the bar and slip out at the foot of the castle rise.",
        notes="Out to X4 at the castle rise's west foot (A5's point, facing west).")
    else:
      e(id='evt:postern', preset='text', source='panel:postern_door', title='Postern', window=True,
        text="You lift the bar and push: the postern opens a hand's breadth onto the moat and stops against a barge "
             "sunk across it. There is no way out here for now.",
        notes="Sealed exit to X4's moat bank (not built).")
    for c in ['loft', 'warden', 'den', 'hoard']:
        e(id=f'evt:chest_{c}', preset='chest', source=f'chest:{c}', title='Chest')
    e(id='evt:chest_roxanne', preset='chest', source='chest:roxanne', title='Chest', condition={'qbit': 'tiara_done'},
      effects=[hook('q-c3.bedroom_chest')], else_effects=[hook('q-c3.bedroom_chest')],
      notes="q-c3.bedroom_chest: Roxanne's chest opens once Q-C3 is done (112061); before, the hook's locked text.")
    ev.sort(key=lambda x: x['id'])
    return {'format': 0, 'variables': ['thrown'], 'events': ev}


# ---------------------------------------------------------------------------------------------------------------------
# project.yml


def project_yml(level):
    p = {
        'format': 0, 'id': 'xeen_xd07', 'name': 'Castle Burlock', 'world': 'xeen', 'kind': 'indoor',
        'profile': 'dungeon', 'map_code': 'XD-07', 'units': FlowDict(plan_grid=512),
        'extent': FlowDict(footprint_cells=F(20, 31), climbs='n'),
        'map_stats': {
            'id': MAP_STATS_ID, 'encounter_chance': 10, 'treasure_level': 2, 'trap_dice': 1,
            'perception_difficulty': 2, 'refill_days': 672, 'music': MUSIC, 'environment': 'castle',
            'lock_difficulty': 2,
            'slots': [
                FlowDict(monster='Xeen Madman', tier=5, per_marker=F(2, 3), weight=40),
                FlowDict(monster='Xeen Gargoyle', tier=1, per_marker=F(1, 2), weight=30),
                FlowDict(monster='Xeen Troll', tier=0, per_marker=F(1, 2), weight=30),
            ],
        },
        'neighbours': [],
        'qbits': dict(sorted(QBITS.items())),
        'notes': "Xeen design brief, level %s: XD-07 Castle Burlock, the royal court on X4 (Act II; MU-6 graph "
                 "devdocs/xeen/mockups/act2_graphs/xd07.graph.yml, decisions D-4). Story M5-M7 (the audience, Artemus), "
                 "Emerson (M9, M11, M22), Roxanne (Q-C3, T1-E). Map card 9123, music 29, treasure 2 (hoard 3); slots "
                 "1 Xeen Madman (Mad Fool 8 b, Raving Lunatic 12 c), 2 Xeen Gargoyle (16 a, Lord 22 b), 3 Xeen Troll "
                 "(Troll 18 a); placed: seven King's Guards 11143 (peaceful by the world's relation) and the caged Fire "
                 "Dragon 11642 (optional). Quest bits: A3's m4.done 110047, m5.audience 111100, xd07.dungeon_key 116080, "
                 "Q-C3 done 112061; the map's own 110720-110759 (two used). The court's people are A4's houses "
                 "4201-4204. Every exit leads to X4 (Burlock Savannah), not built: sealed (NOTES.md)." % level,
    }
    if level == 'L4':
        p['neighbours'] = []
        if X4_IN:
            p['neighbours'] = [
                {'id': 'exit:x4_gate', 'to': X4_STEM, 'kind': 'door', 'arrival': F(*X4_GATE_ARRIVAL),
                 'arrival_hint': "On X4's castle rise in front of Castle Burlock's gate, facing away from it.",
                 'direction': 270,
                 'notes': "A5's points (2026-11-20): the gate on X4 at (-1024, 7168, 1888); the party arrives in front "
                          "of it facing south. X4's gate door leads in to this map's start inside the castle door."},
                {'id': 'exit:x4_air', 'to': X4_STEM, 'kind': 'roof', 'arrival': F(*X4_THROW_ARRIVAL),
                 'arrival_hint': "In the air beside the west tower, outside the walls, about 1,000 above the rise.",
                 'direction': 0, 'one_way': True, 'keep_height': True,
                 'notes': "The old throne's throw (D-4): A5's landing point (briefs/x4/DOORS.md), facing east; the party "
                          "falls about 1,000 (fall damage)."},
                {'id': 'exit:x4_moat', 'to': X4_STEM, 'kind': 'door', 'arrival': F(-5120, 8448, 1312),
                 'arrival_hint': "At the castle rise's west foot on X4, 1,024 west of the rise's face, facing away from the wall.",
                 'direction': 180, 'one_way': True,
                 'notes': "The postern (A5's point, briefs/x4/DOORS.md, 2026-11-20): X4 has no moat; out only (X4 has no "
                          "door into the postern)."},
            ]
    return p


# ---------------------------------------------------------------------------------------------------------------------
# plan.yml


def plan_yml(level):
    sp = []

    def s(rid, kind, size, purpose, population=None, treasure=None, **kw):
        r = ROOMS[rid]
        x0, y0, x1, y1 = r['rect']
        kind = {'hall': 'room', 'stair': 'room', 'cave': 'room'}.get(kind, kind)
        kw.pop('goal', None)
        kw.pop('set_piece', None)
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
        return FlowDict(slot=slot, groups=groups, per_marker=F(2, 3) if slot == 1 else F(1, 2), strength=strength,
                        rank=rank)

    s('gatehouse', 'room', 'M', "Arrival inside the castle door; the Crusaders' portcullis; two King's Guards.",
      shape="White ashlar room, the portcullis in its north wall between Burlock's arms.")
    s('great_hall', 'hall', 'L', "The court: banners, King's Guards, the plaque 'Don't worry, be happy.'",
      shape="Long marble hall with four pilasters and two chandeliers.")
    s('throne_room', 'hall', 'L', "King Burlock on his throne, Prince Roland beside him (house 4201, M5).",
      shape="Tall marble hall, the throne on a dais under the arms.", set_piece=True)
    s('armour_gallery', 'corridor', 'M', "The ceremonial armour and their plaques; Artemus's and Emerson's doors.")
    s('library', 'room', 'M', "The Book of Languages and the Book of Astrology on reading desks.")
    s('well_court', 'room', 'S', "The castle well: 'The water refreshes you.'")
    s('east_tower_base', 'stair', 'S', "The royal family's tower foot behind the throne; a guard.")
    s('east_stair_1', 'stair', 'S', "Up the east tower.")
    s('east_landing', 'room', 'M', "Roxanne's parlour door (house 4204, Q-C3) and her plaque.", goal=True)
    s('east_stair_2', 'stair', 'S', "Up to the royal bedroom.")
    s('royal_bedroom', 'room', 'M', "Roxanne's chest (q-c3.bedroom_chest).", goal=True,
      treasure=[FlowDict(kind='chest', count=1, tier=3, notes="Opens once Q-C3 is done.")])
    s('west_tower_base', 'stair', 'S', "Behind the closed door: the stair up into the abandoned west tower.")
    s('west_stair_1', 'stair', 'S', "Up the west tower.")
    s('fools_hall', 'room', 'M', "The court's fools gone mad.", population=[pop(1, 3, 'c')])
    s('west_gallery', 'corridor', 'M', "Arrow slits and three joke plaques; fools and a gargoyle.",
      population=[pop(1, 2, 'c', 'light'), pop(2, 1, 'a', 'light')])
    s('west_stair_2', 'stair', 'S', "Up to the tower top.")
    s('gargoyle_loft', 'room', 'M', "The roosts; the gargoyles' chest.", population=[pop(2, 5, 'a')],
      treasure=[FlowDict(kind='chest', count=1, tier=2)])
    s('old_throne', 'room', 'M', "The old King's throne: the throw onto X4.", population=[pop(2, 2, 'b', 'light')],
      set_piece=True)
    s('kitchens', 'room', 'M', "The servants' way; two fools in the larder; the cellar stair.",
      population=[pop(1, 1, 'b', 'light')])
    s('kitchen_stair', 'stair', 'S', "Down to the wine cellar.")
    s('cellar', 'room', 'M', "The wine cellar (the map's storeroom); the dungeon door; the den's barred door.",
      population=[pop(1, 2, 'c', 'light')])
    s('cell_block', 'hall', 'L', "Broken cells, the warden's strongbox; trolls.", population=[pop(3, 3, 'a')],
      treasure=[FlowDict(kind='chest', count=1, tier=2)])
    s('pit_gallery', 'corridor', 'M', "The warden's lever and his sign over the pit.", population=[pop(3, 1, 'a', 'light')],
      set_piece=True)
    s('pit_stair', 'stair', 'S', "A narrow low stair to the pit's portcullis.")
    s('dragon_pit', 'cave', 'L', "The caged Fire Dragon on its hoard (optional).",
      population=[FlowDict(actor='Fire Dragon', levels=F(75, 75), placed=True, strength='boss', role='optional')],
      treasure=[FlowDict(kind='chest', count=1, tier=3)])
    s('old_cistern', 'cave', 'M', "The old cistern (D-4: no ice); the Black Liquid (+2 Might once each).",
      population=[pop(3, 3, 'a')])
    s('troll_den', 'cave', 'M', "Where the trolls sleep; their loot; the bar of the cellar door.",
      population=[pop(3, 3, 'a')], treasure=[FlowDict(kind='chest', count=1, tier=2)])
    s('postern', 'corridor', 'S', "The sally port to the moat (sealed until X4 exists).")

    links = []

    def ln(lid, a, b, kind, **kw):
        d = {'id': f'link:{lid}', 'from': f'room:{a}', 'to': f'room:{b}', 'kind': kind}
        d.update(kw)
        links.append(d)

    ln('gate_hall', 'gatehouse', 'great_hall', 'portcullis', condition={'qbit': 'crusader'},
       notes="The portcullis: lifts only for Crusaders (m5.crusaders_gate).")
    ln('gate_kitchens', 'gatehouse', 'kitchens', 'door')
    ln('hall_throne', 'great_hall', 'throne_room', 'double_door')
    ln('hall_westtower', 'great_hall', 'west_tower_base', 'door', notes="Closed (D-4).")
    ln('hall_well', 'great_hall', 'well_court', 'open')
    ln('well_library', 'well_court', 'library', 'door')
    ln('library_gallery', 'library', 'armour_gallery', 'door')
    ln('throne_gallery', 'throne_room', 'armour_gallery', 'open')
    ln('throne_easttower', 'throne_room', 'east_tower_base', 'door')
    ln('easttower_parlour', 'east_tower_base', 'east_landing', 'stairs', rise=640)
    ln('parlour_bedroom', 'east_landing', 'royal_bedroom', 'stairs', rise=640)
    ln('westtower_fools', 'west_tower_base', 'fools_hall', 'stairs', rise=640)
    ln('fools_gallery', 'fools_hall', 'west_gallery', 'open')
    ln('gallery_loft', 'west_gallery', 'gargoyle_loft', 'stairs', rise=640)
    ln('loft_throne', 'gargoyle_loft', 'old_throne', 'door')
    ln('kitchens_cellar', 'kitchens', 'cellar', 'stairs', rise=-640)
    ln('cellar_cells', 'cellar', 'cell_block', 'door', condition={'qbit': 'dungeon_key'},
       notes="The iron dungeon door: Artemus's key (a qbit, xd07.dungeon_door).")
    ln('cells_cistern', 'cell_block', 'old_cistern', 'open')
    ln('cistern_den', 'old_cistern', 'troll_den', 'open')
    ln('den_cellar', 'troll_den', 'cellar', 'door', one_way=True, condition={'qbit': 'den_bar_lifted'},
       notes="Barred on the den side; lifted, both ways.")
    ln('den_postern', 'troll_den', 'postern', 'door')
    ln('cells_pitgallery', 'cell_block', 'pit_gallery', 'door')
    ln('pitgallery_pit', 'pit_gallery', 'dragon_pit', 'stairs', rise=-512, condition={'qbit': 'cage_lever_pulled'},
       notes="A narrow low stair; the portcullis at its foot rises by the warden's lever.")

    plan = {
        'format': 0, 'level': min(level, 'L3'),
        'pitch': "King Burlock's castle on the savannah: a white-stone gatehouse whose portcullis lifts only for "
                 "Crusaders, a marble great hall and throne room where the King hunts his mirror, the gallery of arms "
                 "with Artemus's and Emerson's doors, the library and the well court in a ring round the court. The "
                 "east tower is the royal family's (Roxanne's parlour, the bedroom); the west tower has been given up "
                 "to the court's mad fools and roosting gargoyles, and at its top stands the old King's throne that "
                 "throws whoever sits on it into the air outside. Under the kitchens the wine cellar's iron door opens "
                 "on the dungeon the trolls broke out of, its old cistern, their den, and the warden's pit where a Fire "
                 "Dragon waits behind a portcullis and a sign that says 'Do not pull'.",
        'purpose': "Story M5-M7 (the audience, Artemus, the dungeon key), Emerson for Newcastle (M9, M11, M22), "
                   "Roxanne (Q-C3, T1-E); optional fights in the west tower and the dungeon, an optional dragon. Party "
                   "12-14, monsters 8-22 (the band 10-24; Mad Fools 8 mixed in, D-4).",
        'mood': "A bright, busy court of white stone and cream marble, banners and guards; the abandoned west tower "
                "draughty and noisy; the cellars and dungeon grey, cold and quiet; the pit a hot red cave.",
        'datum': 'arrival',
        'spaces': sp,
        'links': links,
        'loops': [
            {'id': 'loop:court', 'spaces': [f'room:{x}' for x in ('great_hall', 'well_court', 'library',
                                                                   'armour_gallery', 'throne_room')],
             'notes': "Round the court."},
            {'id': 'loop:dungeon', 'spaces': [f'room:{x}' for x in ('cellar', 'cell_block', 'old_cistern', 'troll_den')],
             'notes': "Round the dungeon, closed once the den's bar is lifted."},
        ],
        'entrances': [
            {'id': 'entrance:castle_door', 'space': 'room:gatehouse', 'kind': 'both', 'facing': 'n',
             'how': "Inside the castle door from X4; sealed until X4 exists (NOTES)."},
        ],
        'critical_path': [f'room:{x}' for x in ('gatehouse', 'great_hall', 'throne_room', 'armour_gallery')],
        'goals': [
            {'id': 'goal:audience', 'space': 'room:throne_room', 'kind': 'use',
             'what': "The audience with King Burlock (M5) through the throne (house 4201)."},
            {'id': 'goal:artemus', 'space': 'room:armour_gallery', 'kind': 'use',
             'what': "Artemus (M6, M7; the dungeon key) through his door (house 4202)."},
            {'id': 'goal:roxanne', 'space': 'room:east_landing', 'kind': 'use',
             'what': "Roxanne (Q-C3) through her parlour's door (house 4204); her chest in the bedroom."},
        ],
        'set_pieces': [
            {'id': 'set:portcullis', 'kind': 'scripted', 'spaces': ['room:gatehouse'],
             'rule': "The portcullis lifts for a Crusader party; others hear 'Only Crusaders are allowed to enter "
                     "Castle Burlock.'"},
            {'id': 'set:old_throne', 'kind': 'scripted', 'spaces': ['room:old_throne'],
             'rule': "Sitting on the old throne throws the party into the air outside the west tower (onto X4)."},
            {'id': 'set:dragon_cage', 'kind': 'boss', 'spaces': ['room:pit_gallery', 'room:dragon_pit'],
             'rule': "The warden's lever raises the pit's portcullis at the foot of a stair too narrow for the "
                     "dragon; the fight is optional."},
        ],
        'diagram': FlowDict(file='diagram.txt'),
        'totals': {'rooms': len(ROOMS), 'sectors': len(ROOMS), 'monsters_about': 48, 'chests': 5, 'loops': 2,
                   'doors': 14, 'fixed_actors': 8},
        'notes': "Class M (MAPS: 20-45 sectors, 45-75 monsters). The court floor is peaceful (King's Guards 40 by the "
                 "world's relation); the fights are behind the west tower's closed door and below the dungeon door. "
                 "Every room is a rectangle; stairs are stepped rooms of 32 risers.",
    }
    if level in ('L3', 'L4'):
        plan['sketch'] = FlowDict(file='rooms.yml', grid=512)
    return plan


DIAGRAM = r"""XD-07 Castle Burlock (x east, y north; floors 1280 / 640 / 0 / -640 / -1152)

 1280  [Old King's throne: THROW]          [Royal bedroom: Roxanne's chest T3]
           | door                                   | stair
       [Gargoyle loft: chest T2]           [Princess's landing: Roxanne 4204]
           | stair                                  | stair
  640  [West gallery: plaques]--[Fools' hall]      (east tower)
                                  | stair
    0  [West tower foot]=door=[GREAT HALL]--arch--[Well court]
                                 |   \ PORTCULLIS (Crusaders)  | door
                       [Throne room: KING 4201]  [Library]
                         |        \ open           | door
                 [East tower foot]  [Gallery of arms: Artemus 4202 / Emerson 4203]
            [Kitchens]--door--[GATEHOUSE: arrival, castle door (sealed to X4)]
                 | stair
 -640  [Wine cellar (store)]=IRON DOOR (key 116080)=[Cell block T2]--door--[Pit gallery: LEVER, sign]
          | barred (den side)                         | open                    | narrow low stair
       [Troll den T2]--open--[Old cistern: Black Liquid]                     PORTCULLIS
          | door                                                              |
       [Postern (sealed to X4)]                                    -1152 [Dragon pit: FIRE DRAGON, hoard T3]
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
