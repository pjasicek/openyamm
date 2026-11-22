#!/usr/bin/env python3
"""DD-01 Castleview Sewer, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo
from geo import S_

DIRE, VBAT, GREM, SAB, WERE, ROOKA, VALIO = 11393, 11311, 11020, 11021, 11400, 11403, 11193
NAME = {DIRE: 'dire_rat', VBAT: 'vampire_bat', GREM: 'gremlin', SAB: 'saboteur', WERE: 'wererat', ROOKA: 'rooka',
        VALIO: 'valio'}
VALIO_GROUP = 20
ROOKA_GROUP = 5

Q_ARRIVED, Q_OUTFALL, Q_PURSE = 117000, 117001, 117002
Q_ROOKA, Q_ANGERED = 113101, 113104
BIT_RED, BIT_GREEN = 11310, 11311

LAMP = [215, 180, 120]
DRAIN = [150, 165, 130]
DEEP = [120, 135, 115]
DAY = [190, 200, 215]
NESTC = [175, 140, 105]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
DOORS = [
    # id, opening, kind, surface, notes
    ('cross_west', 'open:cross_west', 'slide_up', geo.DOOR, "A wooden door from the cross into the west drain."),
    ('cross_east', 'open:cross_east', 'slide_up', geo.DOOR, "A wooden door from the cross into the east drain."),
    ('north_cross', 'open:north_cross', 'slide_up', geo.DOOR, "A wooden door from the north drain into the cross."),
    ('sluice_north', 'open:sluice_north', 'slide_up', geo.IRONDOOR, "The sluice house's iron door into the north drain."),
    ('east_market', 'open:east_market', 'slide_up', geo.DOOR, "A wooden door to the market shaft."),
    ('valio_overflow', 'open:valio_overflow', 'slide_up', geo.DOOR, "A wooden door from Valio's niche to the overflow."),
    ('deep_outfall', 'open:deep_outfall', 'slide_up', geo.IRONDOOR, "An iron door from the deep cistern into the outfall tunnel."),
]


def doors():
    return [{'id': f'door:{k}', 'opening': op, 'kind': kind, 'surface': dict(s, fit=True), 'notes': n}
            for k, op, kind, s, n in DOORS]


WATER_OUTLINE = [[1056, -3040], [1504, -3040], [1504, -1952], [1056, -1952]]
WATER_H = 272
GRATE_SIZE = [256, 256]


def movers():
    return [
        {'id': 'mover:water', 'room': R('culvert'), 'outline': WATER_OUTLINE, 'bottom': 0, 'height': WATER_H,
         'travel': [0, 0, -(WATER_H + 18)], 'speed': 58, 'surface': dict(geo.SEWAGE), 'top_surface': dict(geo.SEWAGE),
         'notes': "The culvert's water: one block from its floor to 16 under its roof while the sluice runs; the lever sinks it 290 (its top 18 under the floor) in about 5 s, and raises it again (XD-10's route)."},
        {'id': 'mover:sluice_gate', 'room': R('sluice'), 'at': [-1728, 1664], 'size': [248, 48], 'floor_height': -96,
         'bottom': 160, 'height': 400, 'travel': [0, 0, -160], 'speed': 64, 'surface': dict(geo.IRONDOOR),
         'top_surface': dict(geo.IRONDOOR),
         'notes': "The sluice gate, wedged 160 up by gremlins with the mill's gears; closed it drops onto the channel's floor."},
        {'id': 'mover:grate', 'room': R('east_drain'), 'at': geo.GRATE_AT, 'size': GRATE_SIZE, 'floor_height': 0,
         'bottom': 0, 'height': 8, 'travel': [240, 0, 0], 'speed': 160, 'surface': dict(geo.FLOORGRATE),
         'top_surface': dict(geo.FLOORGRATE),
         'notes': "The cellar's floor grate over the hole in the south walk; the bolt below slides it aside."},
    ]


def switches():
    return [
        {'id': 'switch:sluice_lever', 'room': R('sluice'), 'kind': 'lever', 'at': [-1280, 2048], 'reach': 48,
         'notes': "The sluice lever on the north wall beside the gate."},
        {'id': 'switch:outfall_bar', 'room': R('outfall'), 'kind': 'lever', 'at': [4096, -4608], 'reach': 48,
         'notes': "The outfall grate's bar, on the tunnel's north wall by the grate."},
        {'id': 'switch:grate_bolt', 'room': R('cellar'), 'kind': 'lever', 'at': [4960, 32], 'height': 256,
         'reach': 40, 'notes': "The grate's bolt, high on the cellar's north wall beside the ladder."},
    ]


def ladders():
    return [{'id': 'ladder:cellar', 'room': R('cellar'), 'at': [geo.GRATE_AT[0] - 72, geo.GRATE_AT[1]], 'facing': 'w',
             'height': -geo.MIDDEN, 'exit': [geo.GRATE_AT[0] - 240, geo.GRATE_AT[1]], 'grab_at_top': True,
             'surface': S_('bemv', 32, 256, uneven=True),
             'notes': "An iron ladder from the drowned cellar up through the floor grate to the east drain's south walk."}] + [
        # F14 (A8 26th): iron rungs out of the four sunken pools (64-96 down), so a party that drops in climbs out on foot.
        {'id': f'ladder:{k}', 'room': R(room), 'at': at, 'facing': f, 'height': h, 'exit': ex, 'grab_at_top': True,
         'surface': S_('bemv', 32, 256, uneven=True), 'notes': f"F14: iron rungs up the {what}'s {side} edge."}
        for k, room, at, f, h, ex, what, side in (
            ('cross_sump', 'cross', [0, 152], 'n', 64, [0, 256], 'sump', 'north'),
            ('overflow_pool', 'overflow', [-1152, -1416], 'n', 96, [-1152, -1312], 'overflow pool', 'north'),
            ('deep_pool', 'deep_cistern', [-1152, -4488], 'n', 64, [-1152, -4384], 'deep pool', 'north'),
            ('sluice_channel', 'sluice', [-1608, 1024], 'e', 96, [-1504, 1024], 'sluice channel', 'east'))]


def chests():
    return [
        {'id': 'chest:valio', 'room': R('valio'), 'at': [-2240, -1488], 'treasure_level': 2,
         'random_items': 1, 'gold': 300,
         'notes': "Valio's chest by his bed (the diploma is the hook's text): q-d5.valio_chest on its opening."},
        {'id': 'chest:market', 'room': R('shaft_market'), 'at': [3024, 928], 'facing': 's', 'treasure_level': 2,
         'random_items': 2, 'gold': 150, 'notes': "Things dropped through the market grate over the years."},
        {'id': 'chest:hoard', 'room': R('rat_nest'), 'at': [3840, -1440], 'facing': 'w', 'treasure_level': 3,
         'random_items': 3, 'gold': 800, 'notes': "Rooka's hoard."},
        {'id': 'chest:midden', 'room': R('midden'), 'at': [6272, -1696], 'treasure_level': 2,
         'random_items': 2, 'gold': 200, 'notes': "A sodden pack among the bones."},
        {'id': 'chest:cellar', 'room': R('cellar'), 'at': [4608, -1184], 'treasure_level': 2,
         'random_items': 2, 'gold': 250, 'notes': "The gremlins' box of stolen tools."},
    ]


PLACED = {
    'west_drain': [(DIRE, [-2560, -240]), (DIRE, [-2240, 240]), (DIRE, [-1600, -240]), (DIRE, [-1280, 240])],
    'sluice': [(GREM, [-2432, 896]), (GREM, [-2432, 1664]), (GREM, [-1216, 896]), (GREM, [-1216, 1664]),
               (SAB, [-1408, 1280]), (SAB, [-2176, 1280])],
    'north_drain': [(GREM, [256, 960]), (GREM, [1024, 1344]), (GREM, [1792, 960])],
    'east_drain': [(VBAT, [1536, 240]), (VBAT, [2560, -240]), (VBAT, [3456, 240]), (VBAT, [4224, 240])],
    'overflow': [(DIRE, [-1472, -1344]), (DIRE, [-832, -1344]), (DIRE, [-1472, -1984]), (DIRE, [-832, -1984])],
    'shaft_market': [(DIRE, [3072, 640]), (DIRE, [3328, 640]), (DIRE, [3328, 832])],
    'rat_runs': [(WERE, [896, -3968]), (WERE, [1664, -3712]), (WERE, [1920, -4096]), (DIRE, [512, -3584]),
                 (DIRE, [1280, -3456]), (DIRE, [2176, -3648])],
    'deep_cistern': [(VBAT, [-1920, -4224]), (VBAT, [-384, -4224]), (VBAT, [-1920, -5248]), (VBAT, [-384, -5248])],
    'rat_nest': [(ROOKA, [3328, -2432]), (WERE, [2944, -2112]), (WERE, [3712, -2112]), (WERE, [2944, -2752]),
                 (WERE, [3712, -2752]),
                 # the nest culvert's four (D-26): on the nest side above the culvert's high-water line
                 (DIRE, [2560, -1600]), (DIRE, [2560, -1280]), (DIRE, [2816, -1440]), (DIRE, [2816, -1760])],
    'midden': [(DIRE, [5632, -2560]), (DIRE, [6144, -2560]), (DIRE, [5888, -1920])],
    'cellar': [(GREM, [4864, -768]), (GREM, [5120, -448]), (GREM, [5504, -384]), (SAB, [4928, -1024])],
}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'hostile': True, 'group': 1}
            if row == ROOKA:
                d['id'] = 'monster:rooka'
                d['group'] = ROOKA_GROUP
                d['notes'] = "Rooka the Rat Queen (boss row 11403, 24): q-d5.rooka at her death."
            if room == 'rat_nest' and row == DIRE:
                d['notes'] = "One of the nest culvert's four (D-26): at the nest's mouth, above the culvert's high-water line."
            out.append(d)
    out.append({'id': 'monster:valio', 'room': R('valio'), 'monster': VALIO, 'at': [-2240, -1680], 'facing': 90,
                'hostile': True, 'group': VALIO_GROUP, 'hidden': True,
                'notes': "Valio Magnus (11193, 45), placed hidden: shown, hostile, once valio_angered (113104) is set (q-d5.valio_angry). A trap (D-1.2): not counted."})
    return out


# key: (decoration, room, at, floor height or None, title or None)
DECOS = [
    ('red_liquid', 'dec35', 'shaft_west', [-3456, 160], 128, 'Red Liquid'),
    ('green_liquid', 'dec35', 'shaft_temple', [5632, 160], 128, 'Green Liquid'),
    ('guard_bones', 'dec05', 'shaft_north', [1920, 1984], None, 'Bones'),
    ('shiny_heap', 'trasheap', 'rat_nest', [3904, -2880], None, 'Heap of shiny things'),
    ('rubble_1', '7dec10', 'rat_runs', [384, -3392], None, 'Rubble'),
    ('rubble_2', '7dec01', 'rat_runs', [2304, -4256], None, 'Rubble'),
    ('barrel_1', 'bigbarel', 'cellar', [5792, -288], None, 'Barrel'),
]
PROPS = [
    ('barrel_2', 'bigbarel', 'cellar', [5792, -448]),
    ('nest_straw_1', '7dec11', 'rat_nest', [2496, -2304]),
    ('nest_straw_2', '7dec11', 'rat_nest', [3456, -2880]),
    ('nest_bones', 'dec19', 'rat_nest', [2688, -2880]),
    ('midden_bones_1', '7dec18', 'midden', [5440, -2432]),
    ('midden_bones_2', 'dec19', 'midden', [6336, -2304]),
    ('midden_bones_3', '7dec18', 'midden', [5504, -2752]),
    ('runs_bones', 'dec29', 'rat_runs', [256, -4352]),
]
# lights audit (merge point 14): MM6's brazier hangs on chains, so Felix's hangs from his tunnel's ceiling (384 clear),
# its top 2 into it (146 high)
HUNG = [('felix_brazier', 'brzier00', 'felix', [-2768, -2720], 236)]
TORCHES = [('cross', 'n', 0.25), ('cross', 's', 0.75), ('cross', 'e', 0.25), ('cross', 'w', 0.75),
           ('sluice', 'w', 0.5), ('sluice', 'e', 0.3), ('west_drain', 's', 0.3), ('north_drain', 's', 0.7),
           ('east_drain', 'n', 0.6), ('east_drain', 's', 0.2), ('valio', 'n', 0.8), ('cellar', 'w', 0.5)]


def decorations():
    out = []
    for key, dec, room, at, fh, title in DECOS:
        d = {'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at, 'notes': f"{title} (clicked: evt:{key})."}
        if fh is not None:
            d['floor_height'] = fh
        out.append(d)
    for key, dec, room, at in PROPS:
        out.append({'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at})
    for key, dec, room, at, height in HUNG:
        out.append({'id': f'deco:{key}', 'room': R(room), 'decoration': dec, 'at': at, 'height': height, 'hangs': True,
                    'notes': 'A brazier hung on its chains from the ceiling.'})
    for i, (room, wall, along) in enumerate(TORCHES):
        out.append({'id': f'deco:torch_{i}', 'room': R(room), 'decoration': 'torch02', 'wall': wall, 'along': along,
                    'height': 192})
    return out


def lights():
    L = []

    def add(room, at, radius, color, height=None, pulse=None, notes=None, fh=None):
        d = {'id': f'light:{room}_{sum(1 for x in L if x["room"] == R(room)) + 1}', 'room': R(room), 'at': at,
             'radius': radius, 'color': color}
        if height:
            d['height'] = height
        if fh is not None:
            d['floor_height'] = fh
        if pulse:
            d['pulse'] = pulse
        if notes:
            d['notes'] = notes
        L.append(d)
    for room in geo.R:
        (w, h), c = geo.extent(room)
        if room.startswith('shaft_'):
            add(room, c, 900, DAY, height=1100, notes="Daylight down through the street grate.")
            continue
        col = DEEP if geo.R[room][2] < 0 else DRAIN
        if room in ('rat_nest', 'midden', 'rat_runs'):
            col = NESTC
        r = int(min(2000, max(700, 0.6 * max(w, h))))
        if max(w, h) > 2400:
            ax = 0 if w >= h else 1
            for f in (0.25, 0.75):
                p = list(c)
                lo = c[ax] - (w if ax == 0 else h) / 2
                p[ax] = int(lo + f * (w if ax == 0 else h))
                add(room, p, int(r * 0.7), col)
        else:
            add(room, c, r, col)
    add('felix', [-2880, -2752], 600, LAMP, height=160, notes="Felix's lantern on his bench.",
        pulse={'intensity': [0.8, 1.0], 'radius': [560, 620], 'frequency': 0.5})
    add('valio', [-2240, -1792], 500, LAMP, height=128, notes="A candle stub by Valio's bed.",
        pulse={'intensity': [0.7, 1.0], 'radius': [450, 520], 'frequency': 0.7})
    return L


def sounds():
    return [
        {'id': 'sound:west_drain', 'room': R('west_drain'), 'at': [-1984, 0], 'sound': 'water lapping loop',
         'radius': 1600, 'inner_radius': 500, 'volume': 0.35, 'notes': "The channel's slow water."},
        {'id': 'sound:north_drain', 'room': R('north_drain'), 'at': [896, 1152], 'sound': 'water lapping loop',
         'radius': 1600, 'inner_radius': 500, 'volume': 0.35, 'notes': "The channel's slow water."},
        {'id': 'sound:east_drain', 'room': R('east_drain'), 'at': [2944, 0], 'sound': 'water lapping loop',
         'radius': 1800, 'inner_radius': 600, 'volume': 0.35, 'notes': "The channel's slow water."},
        {'id': 'sound:sluice', 'room': R('sluice'), 'at': [-1728, 1856], 'sound': 'rushing water loop',
         'radius': 1500, 'inner_radius': 400, 'volume': 0.6, 'notes': "The town's water pouring through the jammed sluice."},
        {'id': 'sound:cross', 'room': R('cross'), 'at': [0, 0], 'sound': 'drip02', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'wait': [2, 6], 'notes': "Drips into the cross's sump."},
        {'id': 'sound:overflow', 'room': R('overflow'), 'at': [-1152, -1664], 'sound': 'drip03', 'radius': 1300,
         'inner_radius': 400, 'volume': 0.5, 'wait': [2, 5], 'notes': "The overflow cistern dripping."},
        {'id': 'sound:deep', 'room': R('deep_cistern'), 'at': [-1152, -4832], 'sound': 'drip01', 'radius': 1600,
         'inner_radius': 500, 'volume': 0.5, 'wait': [2, 6], 'notes': "The deep cistern dripping."},
        {'id': 'sound:culvert', 'room': R('culvert'), 'at': [1280, -2496], 'sound': 'water lapping loop',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.5, 'notes': "The culvert's water (heard from the rat runs)."},
        {'id': 'sound:outfall', 'room': R('outfall'), 'at': [4096, -4864], 'sound': 'whistling wind', 'radius': 1400,
         'inner_radius': 300, 'volume': 0.3, 'notes': "The gorge's air through the outfall grate."},
        {'id': 'sound:cellar', 'room': R('cellar'), 'at': [5504, -832], 'sound': 'drip02', 'radius': 1000,
         'inner_radius': 300, 'volume': 0.5, 'wait': [3, 7], 'notes': "The drowned cellar dripping."},
        # AU's sewer bed (xeen_amb_sewer, 62800): three sources ~4,500 apart, inner circles apart (AUDIO.md, session 7).
        {'id': 'sound:bed_west', 'room': R('west_drain'), 'at': [-1280, 0], 'sound': 'xeen_amb_sewer', 'radius': 3200,
         'inner_radius': 1000, 'volume': 0.4, 'pan': False, 'notes': "The sewer's trickles and drips (bed, west)."},
        {'id': 'sound:bed_east', 'room': R('east_drain'), 'at': [3584, 0], 'sound': 'xeen_amb_sewer', 'radius': 3200,
         'inner_radius': 1000, 'volume': 0.4, 'pan': False, 'notes': "The sewer's trickles and drips (bed, east)."},
        {'id': 'sound:bed_south', 'room': R('rat_runs'), 'at': [1280, -3840], 'sound': 'xeen_amb_sewer',
         'radius': 3200, 'inner_radius': 1000, 'volume': 0.4, 'pan': False,
         'notes': "The sewer's trickles and drips (bed, south)."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('shaft_square'), 'at': [0, -1088], 'facing': 'n',
                  'notes': "At the hatch ladder's foot, facing the drain cross (D1's hatch arrives here)."},
        # lights audit (merge point 14): the outfall's named arrival, inside the grate facing up the tunnel, for D1's
        # way in by the gorge (A6: `into: {map: xeen_dd01.blv, arrival: entrance:d1_outfall}`)
        'arrivals': [{'entrance': 'entrance:d1_outfall', 'room': R('outfall'), 'at': [4096, -4864], 'facing': 'w',
                      'notes': "Inside the outfall grate, facing up the tunnel (D1's gorge grate arrives here)."}],
        'doors': doors(), 'movers': movers(), 'switches': switches(), 'ladders': ladders(), 'chests': chests(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [
            {'id': 'exit:hatch', 'room': R('shaft_square'), 'wall': 'south', 'size': [128, 256],
             'surface': dict(geo.LADDER), 'to': 'exit:d1_hatch',
             'notes': "The iron ladder up to the hatch by the square's south-east corner (D1)."},
            {'id': 'exit:outfall', 'room': R('outfall'), 'wall': 'east', 'size': [320, 320],
             'surface': dict(geo.GRATE), 'to': 'exit:d1_outfall',
             'notes': "The outfall's iron grate onto the mill gorge (D1), barred until its bar is lifted."},
        ],
        'notes': "DD-01's contents, written by output/studio_cal/dd01/tools/dress.py: 7 doors, three movers (the culvert's water, the sluice gate, the floor grate), three levers (the sluice, the outfall bar, the grate's bolt), one ladder, five chests, 50 placed monsters (21 Dire Rats, 8 Vampire Bats, 10 Gremlins, 3 Saboteurs, 7 Wererats, Rooka) and Valio's hidden monster.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("THE CASTLEVIEW SEWER. The ladder from the square ends ankle-deep in something you decide is water. Down "
           "here the town's rats keep what they steal, Nadia's onyx necklace among it, in the nest of the Queen Rat "
           "they call Rooka. Four more shafts come down from the streets, their grates bolted from above: this hatch "
           "is the way back up.")
SLUICE_SHUT = ("You throw your weight on the lever. Gears grind, crack and spit out of the sluice: the gremlins' wedge. "
               "The gate drops shut, the channel stills, and somewhere below you water drains away with a long gurgle.")
SLUICE_OPEN = ("You heave the lever back. The sluice gate lifts and the town's water pours through it again; below, the "
               "old culvert floods to its roof.")
FLOODED = "The old culvert is flooded to its roof. Somewhere above, the town's sluice is pouring into it."
BOLTED_ABOVE = "The grate is bolted from above. You hear the town over your head."
BOLTED_BELOW = "The grate is bolted from below."
BOLT_DRAWN = "You draw the rusty bolt. The grate above the ladder scrapes aside onto the drain's walk."
BAR_UP = "You lift the iron bar out of its brackets. The grate swings free on the mill gorge."
BAR_DOWN = "You drop the iron bar back across the grate."
BARRED = "The grate is barred. The iron bar across it lifts out from this side."


def liquid_lua(bit, var, stat):
    return "\n".join([
        f'if IsPlayerBitSet(PlayerBit({bit})) then',
        f'    evt.StatusText("You have had your share of the {stat} liquid.")',
        '    return',
        'end',
        f'AddValue({var}, 2)',
        f'SetPlayerBit(PlayerBit({bit}))',
        f'evt.StatusText("+2 {stat} (permanent).")',
    ])


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say why the party is here (M16: the rats' nest; Q-D5's Rooka), on the first arrival only (arrived_once 117000)."})
    for k, op, kind, s, n in DOORS:
        E.append({'id': f'evt:door_{k}', 'preset': 'door', 'source': f'door:{k}', 'title': 'Door'})
    E.append({'id': 'evt:sluice_lever', 'preset': 'switch', 'source': 'switch:sluice_lever', 'title': 'Sluice lever',
              'toggles': ['mover:water', 'mover:sluice_gate'],
              'effects': [{'lua': 'if IsAtLeast(MapVar(sluice_shut), 1) then SetValue(MapVar(sluice_shut), 0) '
                                  f'evt.SimpleMessage("{SLUICE_OPEN}") else SetValue(MapVar(sluice_shut), 1) '
                                  f'evt.SimpleMessage("{SLUICE_SHUT}") end'}],
              'notes': "poi:sluice (D-26): two states. Shut: the gate drops, the culvert's water sinks (the way to the nest); opened again: the water rises and the culvert floods. The map variable sluice_shut follows the lever (a refill resets both)."})
    E.append({'id': 'evt:culvert_water', 'preset': 'switch', 'source': 'mover:water', 'title': 'Flooded culvert',
              'condition': {'not': {'map_var': 'sluice_shut'}}, 'effects': [{'text': FLOODED}],
              'locked_text': "The culvert lies drained.",
              'notes': "The flooded culvert refuses the party while the sluice runs (Felix's hint names the sluice)."})
    E.append({'id': 'evt:grate_bolt', 'preset': 'switch', 'source': 'switch:grate_bolt', 'title': 'Bolt',
              'condition': {'not': {'map_var': 'grate_open'}}, 'opens': ['mover:grate'], 'sets': {'map_var': 'grate_open'},
              'effects': [{'text': BOLT_DRAWN}], 'locked_text': "The bolt is drawn; the grate lies open above the ladder.",
              'notes': "poi:grate_bolt (D-26): the cellar's way up, a floor grate bolted from below, opened once from the cellar side."})
    E.append({'id': 'evt:grate', 'preset': 'switch', 'source': 'mover:grate', 'title': 'Sewer Drain',
              'condition': {'not': {'map_var': 'grate_open'}}, 'effects': [{'text': BOLTED_BELOW}],
              'locked_text': "The grate lies open over the ladder.",
              'notes': "From above (D-26): 'The grate is bolted from below.'; 'Sewer Drain' is the source's name for a drain grate (dark/aaze0030)."})
    E.append({'id': 'evt:outfall_bar', 'preset': 'switch', 'source': 'switch:outfall_bar', 'title': 'Iron bar',
              'effects': [{'lua': f'if IsQBitSet(QBit({Q_OUTFALL})) then ClearQBit(QBit({Q_OUTFALL})) '
                                  f'evt.StatusText("{BAR_DOWN}") else SetQBit(QBit({Q_OUTFALL})) '
                                  f'evt.StatusText("{BAR_UP}") end'}],
              'notes': "poi:outfall_bar (D-26): a two-state bar; lifted it sets q-d5.outfall_unbarred (117001, provisional), which this map's outfall exit and D1's grate (D1 event 222) read."})
    E.append({'id': 'evt:exit_outfall', 'preset': 'exit', 'source': 'exit:outfall', 'title': 'Outfall grate',
              'condition': {'qbit': 'outfall_unbarred'}, 'locked_text': BARRED,
              'notes': "To D1's mill gorge by the burnt mill, once the bar is lifted (the game's leave window)."})
    E.append({'id': 'evt:exit_hatch', 'preset': 'exit', 'source': 'exit:hatch', 'title': 'Ladder to the square',
              'notes': "'Exit the Sewer?' (dark/aaze0030): the game's own leave window, to D1 by the square's hatch."})
    for pid in ('ladder_west', 'ladder_north', 'ladder_market', 'ladder_temple'):
        E.append({'id': f'evt:{pid}', 'preset': 'text', 'source': f'panel:{pid}', 'title': 'Sewer Drain',
                  'window': False, 'text': BOLTED_ABOVE,
                  'notes': "D-26: the four other shafts end at grates bolted from the street side; 'Sewer Drain' (dark/aaze0030)."})
    E.append({'id': 'evt:red_liquid', 'preset': 'script', 'source': 'deco:red_liquid', 'title': 'Red Liquid',
              'lua': liquid_lua(BIT_RED, 'BaseMight', 'Might'),
              'notes': "Red Liquid (dark/aaze0030: '+5 Might (permanent).', rescaled to +2): once per character (player bit 11310, provisional)."})
    E.append({'id': 'evt:green_liquid', 'preset': 'script', 'source': 'deco:green_liquid', 'title': 'Green Liquid',
              'lua': liquid_lua(BIT_GREEN, 'BaseEndurance', 'Endurance'),
              'notes': "Green Liquid (dark/aaze0030: '+5 Endurance (permanent).', rescaled to +2): once per character (player bit 11311, provisional)."})
    E.append({'id': 'evt:guard_bones', 'preset': 'script', 'source': 'deco:guard_bones', 'title': 'Bones',
              'condition': {'not': {'qbit': 'guard_purse'}}, 'sets': {'qbit': 'guard_purse'},
              'effects': [{'gold': 150},
                          {'text': "A gate guard who fell through the grate long ago. His purse is still on his belt: 150 gold."}],
              'else_effects': [{'text': "Nothing here."}],
              'notes': "A guard's bones (D-26 find); afterwards 'Nothing here.' (dark/aaze0030)."})
    for k in ('rubble_1', 'rubble_2'):
        E.append({'id': f'evt:{k}', 'preset': 'text', 'source': f'deco:{k}', 'title': 'Rubble', 'window': False,
                  'text': "Nothing here.", 'notes': "'Rubble' / 'Nothing here.' (dark/aaze0030)."})
    E.append({'id': 'evt:barrel_1', 'preset': 'text', 'source': 'deco:barrel_1', 'title': 'Barrel', 'window': False,
              'text': "The barrel is empty.", 'notes': "dark/aaze0030."})
    E.append({'id': 'evt:shiny_heap', 'preset': 'script', 'source': 'deco:shiny_heap', 'title': 'Heap of shiny things',
              'lua': 'XeenQuests.hook("m16.necklace")',
              'notes': "goal:necklace: A3's once-hook m16.necklace (the onyx necklace 12332, necklace_found 111321)."})
    E.append({'id': 'evt:rooka_dead', 'preset': 'script', 'trigger': 'timer', 'every': 2,
              'condition': {'kills': {'monster': 'monster:rooka'}}, 'once': True,
              'lua': 'XeenQuests.hook("q-d5.rooka")',
              'notes': "goal:rooka: Rooka's death runs A3's once-hook q-d5.rooka (rooka_slain 113101, 3,000 XP)."})
    E.append({'id': 'evt:bed', 'preset': 'script', 'source': 'platform:bed', 'title': 'Bed',
              'lua': f'if IsQBitSet(QBit({Q_ANGERED})) then evt.StatusText("The bed is empty, its blankets thrown back.") '
                     'else evt.SpeakNPC(4957) end',
              'notes': "Valio the Simple (NPC 4957, source/towns/d1.yml) talks from his bed ('Bed', dark/aaze0030): topic Rats (Q-D5). Words needed: an indoor monster with an npc id."})
    E.append({'id': 'evt:felix', 'preset': 'script', 'source': 'platform:felix_bench', 'title': 'Felix the Tinker',
              'lua': 'evt.SpeakNPC(4958)',
              'notes': "Felix the Tinker (NPC 4958, D-26): a flavour talk at his bench, the sluice hint; sells nothing."})
    E.append({'id': 'evt:chest_valio', 'preset': 'chest', 'source': 'chest:valio', 'title': 'Chest',
              'effects': [{'lua': 'XeenQuests.hook("q-d5.valio_chest")'}],
              'notes': "q-d5.valio_chest (A3): opened before Valio pays, he yells and gets out of bed (valio_angered 113104)."})
    E.append({'id': 'evt:valio_angry', 'preset': 'script', 'trigger': 'timer', 'every': 1,
              'condition': {'qbit': 'valio_angered', 'not': {'map_var': 'valio_shown'}},
              'effects': [{'show_actors': VALIO_GROUP}, {'set': {'var': {'map_var': 'valio_shown'}, 'value': 1}}],
              'notes': "q-d5.valio_angry: once valio_angered is set (on the chest, or on any later entry) the hidden monster Valio (11193) shows, hostile; the map variable keeps a looted corpse hidden, a refill resets both."})
    for c in ('market', 'hoard', 'midden', 'cellar'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    return E


def wiring():
    return {'format': 0, 'variables': ['sluice_shut', 'grate_open', 'valio_shown'],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "DD-01's events, written by output/studio_cal/dd01/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
