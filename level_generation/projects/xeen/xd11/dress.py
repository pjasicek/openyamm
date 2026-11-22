#!/usr/bin/env python3
"""XD-11 Tower of High Magic, L4: objects.yml, wiring.yml, atmosphere.yml (written by gen.py L4)."""
import geo
from geo import S_

WARM = [220, 180, 130]
CORE = ['core0', 'core1', 'core2', 'core3']


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
def doors():
    d = [
        ('door:foyer_athanor', 'open:foyer_athanor', geo.DOOR_BLUE, "The carved door from the foyer to the athanor."),
        ('door:coils_core0', 'open:coils_core0', geo.DOOR_BLUE, "The door from the coils to the foot of the lift shaft."),
        ('door:still_reagents', 'open:still_reagents', geo.DOOR_SIGIL, "The reagent store's door."),
        ('door:energy_magic', 'open:energy_magic', geo.DOOR_SIGIL, "The door between the energy and magic labs."),
        ('door:library_study', 'open:library_study', geo.DOOR_SIGIL, "The Archmage's study door."),
        ('door:librarian', 'open:quarters_hstair', geo.DOOR_BLUE,
         "The Librarian's door: the stair to the top floor, locked to the Librarian's Key."),
        ('door:frost', 'open:poison_wstair', geo.FROST,
         "The frost-sealed door of the west stair: a leaf furred with frost (Icewind Keep's orair32) until the steam valve thaws it."),
    ]
    out = [{'id': i, 'opening': o, 'kind': 'slide_left', 'surface': dict(s, fit=True), 'notes': n} for i, o, s, n in d]
    for n, o in ((1, 'open:landing1_core1'), (2, 'open:quarters_core2'), (3, 'open:landing3_core3')):
        out.append({'id': f'door:gate{n}', 'opening': o, 'kind': 'slide_left', 'surface': dict(geo.GRILLE, fit=True), 'speed': 160,
                    'notes': f"Lift gate {n}: brass grille, bolted until the lever beside it on the landing side is pulled."})
    return out


def lifts():
    out = []
    for lid, room, at, upper in (('lift:a', 'core0', geo.LIFT_W, 'core1'), ('lift:b', 'core1', geo.LIFT_E, 'core2'),
                                 ('lift:c', 'core2', geo.LIFT_W, 'core3')):
        out.append({'id': lid, 'room': R(room), 'at': at, 'size': geo.LIFT_SIZE, 'travel': 640, 'thickness': 32,
                    'speed': 192, 'state': 'up', 'surface': geo.BEAMS,
                    'notes': f"The brass cage's floor (dark planks) between {room} and {upper}: it starts at the upper stop, flush with {upper}'s floor, and runs only once that floor's gate lever is pulled."})
    return out


def switches():
    out = [
        {'id': 'switch:valve', 'room': R('reagents'), 'kind': 'lever', 'at': [-1600, -1152], 'height': 160,
         'size': [12, 48], 'reach': 40,
         'notes': "The steam valve on the north wall, beside the pipe that runs from the store toward the garden."},
        {'id': 'switch:gate1', 'room': R('landing1'), 'kind': 'lever', 'at': [1024, -1024], 'height': 140,
         'size': [12, 48], 'reach': 40, 'notes': "Gate 1's lever, right of the gate."},
        {'id': 'switch:gate2', 'room': R('quarters'), 'kind': 'lever', 'at': [1024, -128], 'height': 140,
         'size': [12, 48], 'reach': 40, 'notes': "Gate 2's lever, right of the gate."},
        {'id': 'switch:gate3', 'room': R('landing3'), 'kind': 'lever', 'at': [1024, -1024], 'height': 140,
         'size': [12, 48], 'reach': 40, 'notes': "Gate 3's lever, right of the gate."},
    ]
    for lid, lo, hi, x in (('a', 'core0', 'core1', 256), ('b', 'core1', 'core2', 1024), ('c', 'core2', 'core3', 256)):
        out.append({'id': f'switch:lift_{lid}_bottom', 'room': R(lo), 'kind': 'button', 'at': [x, -576], 'height': 112,
                    'notes': f"Calls or sends lift {lid} at its lower stop, beside the cage."})
        out.append({'id': f'switch:lift_{lid}_top', 'room': R(hi), 'kind': 'button', 'at': [x, -768], 'height': 112,
                    'notes': f"Calls or sends lift {lid} at its upper stop, beside the shaft."})
    return out


def chests():
    return [
        {'id': 'chest:reagents_box', 'room': R('reagents'), 'at': [-1920, -1280], 'kind': '7gt002', 'facing': 's',
         'treasure_level': 3, 'random_items': 0,
         'notes': "A Pandorian Box, empty: 'The box is empty.' (aaze0055:5)."},
        {'id': 'chest:obs_box', 'room': R('observatory'), 'at': [-1952, 1088], 'kind': '7gt002', 'treasure_level': 3, 'random_items': 3, 'gold': 450, 'trap_level': 3,
         'notes': "A Pandorian Box (aaze0055:4): trapped."},
        {'id': 'chest:study', 'room': R('study'), 'at': [-1952, -1088], 'kind': '7gt002', 'treasure_level': 3, 'random_items': 2, 'gold': 600, 'items': ['skeleton_key'],
         'notes': "The Archmage's chest: the Skeleton Key lies in it with his treasure, an ordinary chest item (F15, 2026-11-21: quest items are looted, MM6-MM8 style); A3's hook m13.skeleton_key sets the bit on its first opening."},
        {'id': 'chest:quarters', 'room': R('quarters'), 'at': [1952, 128], 'kind': '7gt002', 'treasure_level': 3, 'random_items': 2, 'gold': 300},
        {'id': 'chest:mysteries', 'room': R('library'), 'at': [-704, 1216], 'size': [256, 96, 256],
         'surface': geo.CABS, 'end_surface': dict(geo.DESK, uneven=True), 'top_surface': geo.DESK,
         'treasure_level': 3, 'random_items': 1, 'items': ['prismatic_light'],
         'notes': "The cabinet of Mysteries of Light (aaze0058:2): the Prismatic Light spellbook (engine 483; D-4 item 2)."},
    ]


SPAWNS_A = [('foyer', [-1600, -512]), ('foyer', [-640, 512]), ('athanor', [-1280, 1472]), ('athanor', [1280, 1408]),
            ('coils', [640, 320]), ('landing1', [768, -1600]), ('reagents', [-1728, -1664]),
            ('still', [-512, -1280]), ('poison', [-512, 768])]
SPAWNS_B = [('landing2', [-768, 1728]), ('energy', [-384, 512]), ('magic', [1600, 1024]), ('landing3', [768, -1600]),
            ('library', [-512, -256]), ('roof', [0, -512])]


def spawns():
    out = []
    n = {}
    for tier, lst in (('a', SPAWNS_A), ('b', SPAWNS_B)):
        for room, at in lst:
            n[room] = n.get(room, 0) + 1
            out.append({'id': f'spawn:{room}_{n[room]}', 'room': R(room), 'at': at, 'slot': 1, 'tier': tier,
                        'group': 51})
    return out


SORC = [('magic', [896, 1600]), ('magic', [1792, 1280]), ('quarters', [896, 128]), ('quarters', [1600, 128]),
        ('library', [-384, 832]), ('library', [-768, -1216]), ('study', [-1600, -1088]), ('study', [-1536, -1856]),
        ('observatory', [-1600, -128]), ('observatory', [-1728, 896])]


def monsters():
    out = []
    n = {}
    for room, at in SORC:
        n[room] = n.get(room, 0) + 1
        out.append({'id': f'monster:sorceress_{room}_{n[room]}', 'room': R(room), 'monster': 11180, 'at': at,
                    'facing': 270, 'hostile': True, 'group': 1})
    out.append({'id': 'monster:head_sorceress', 'room': R('magic'), 'monster': 11185, 'at': [1344, 1472],
                'facing': 270, 'hostile': True, 'group': 2, 'carries': 'librarian_key',
                'notes': "The Head Sorceress (A2's row 11185, level 32) beside the Magic Brew's dais: her corpse holds the Librarian's Key."})
    return out


BREWS = [
    # key, room, at, floor_height, colour, bit, resistance selector, school, title
    ('fire', 'athanor', [768, 1600], None, [255, 110, 40], 11246, 'FireResistance', 'Fire', 'Fire Brew'),
    ('electric', 'coils', [128, 320], None, [150, 190, 255], 11247, 'AirResistance', 'Air', 'Electric Brew'),
    ('cold', 'still', [-128, -1920], None, [200, 235, 255], 11248, 'WaterResistance', 'Water', 'Cold Brew'),
    ('poison', 'poison', [-1120, 1248], None, [110, 230, 90], 11249, 'BodyResistance', 'Body', 'Poison Brew'),
    ('energy', 'energy', [-1120, 32], None, [255, 230, 90], 11250, 'EarthResistance', 'Earth', 'Energy Brew'),
    ('magic', 'magic', [1344, 1664], 1312, [190, 110, 255], 11251, 'MindResistance', 'Mind', 'Magic Brew'),
]
BREW_TEXT = {
    'fire': "FIRE BREW. A red brew that smokes in its cauldron by the athanor. It burns going down, and the heat stays in you: +5 Fire resistance (permanent).",
    'electric': "ELECTRIC BREW. The brew crackles blue between the coils and stings your tongue like a storm: +5 Air resistance (permanent).",
    'cold': "COLD BREW. Frost creeps up the ladle. It is like swallowing a winter, and afterwards the cold cannot find you: +5 Water resistance (permanent).",
    'poison': "POISON BREW. Nightshade and hemlock, boiled down until they cure what they once caused. Bitter, and then nothing at all: +5 Body resistance (permanent).",
    'energy': "ENERGY BREW. It glows yellow in the ladle and hums in your bones for a long moment: +5 Earth resistance (permanent).",
    'magic': "MAGIC BREW. Violet, and stranger than it looks: for a moment you hear your own thoughts from outside. Then the mind closes, stronger: +5 Mind resistance (permanent).",
}


def decorations():
    out = []
    for key, room, at, fh, *_ in BREWS:
        d = {'id': f'deco:brew_{key}', 'room': R(room), 'decoration': 'cauld00', 'at': at,
             'notes': f"The {key} brew's cauldron (clicked: evt:brew_{key})."}
        if fh is not None:
            d['floor_height'] = fh
        out.append(d)
    # torches and sconces on the walls
    torch = geo.TORCHES
    n = {}
    for room, wall, along in torch:
        n[room] = n.get(room, 0) + 1
        kind = 'torch02' if geo.R[room][4] in ('theme:ground', 'theme:core') else 'scon100'
        out.append({'id': f'deco:light_{room}_{n[room]}', 'room': R(room), 'decoration': kind, 'wall': wall,
                    'along': along, 'height': 192})
    # set pieces
    for i, at in enumerate(([-1024, 1856], [1024, 1856])):
        out.append({'id': f'deco:brazier_athanor_{i}', 'room': R('athanor'), 'decoration': 'brzier00', 'at': at,
                    'hangs': True, 'height': 396, 'notes': "A brazier by the athanor's stack, hung on its chains from the ceiling."})
    for i, at in enumerate(([-1152, 1152], [192, 1152], [-1152, -0], [192, -0])):
        pass
    for i, at in enumerate(([-1152, 1152], [256, 1152], [256, -16])):
        out.append({'id': f'deco:crystal_energy_{i}', 'room': R('energy'), 'decoration': 'crystl0', 'at': at,
                    'notes': "A glowing crystal of the energy lab, against the wall."})
    out.append({'id': 'deco:orrery', 'room': R('observatory'), 'decoration': 'crystl0', 'at': [-1440, 384],
                'floor_height': 1984, 'notes': "The orrery's crystal sun on its iron plinth."})
    # the poison garden's beds
    flowers = ['6Flower01', '6Flower02', '6Flower07', '6Flower08', '6Flower11']
    k = 0
    for bx, by in ((-768, 0), (-768, 768), (-128, 384), (-128, 1152)):
        for dx in (-96, 96):
            out.append({'id': f'deco:plant_{k}', 'room': R('poison'), 'decoration': flowers[k % len(flowers)],
                        'at': [bx + dx, by], 'floor_height': 688, 'notes': "Nightshade in its bed."})
            k += 1
    # the reagent store: sacks and barrels by the walls (a storeroom)
    for i, (dec, at) in enumerate((('bigbarel', [-1504, -1984]), ('bigbarel', [-1952, -1472]),
                                   ('floursac', [-1760, -1730]), ('floursac', [-1632, -1860]))):
        out.append({'id': f'deco:store_{i}', 'room': R('reagents'), 'decoration': dec, 'at': at,
                    'notes': "Reagents in barrels and sacks along the store's walls."})
    # D-89: the laboratories' benches carry glasses, candles and glowing crystals (MM8's glass dec35, MM7's goblets 7dec46,
    # 7dec48; MM6's candle cndlab0 and small crystals mcryst01; all with 3D models in engine/models)
    glass = ['dec35', '7dec46', 'mcryst01', '7dec48', 'cndlab0', 'dec35']
    k = 0
    for room, benches in geo.BENCHES.items():
        fl = geo.R[room][2]
        for b in benches:
            (x, y), (w, h) = b['at'], b['size']
            long_x = w >= h
            for t in (-0.38, 0.0, 0.38):
                at = [round(x + t * w), y] if long_x else [x, round(y + t * h)]
                out.append({'id': f'deco:glass_{k}', 'room': R(room), 'decoration': glass[k % len(glass)], 'at': at,
                            'floor_height': fl + b['rise'], 'notes': "Glassware on a laboratory bench."})
                k += 1
    for i, (x, y) in enumerate(((-1344, 1888), (1344, 1888))):
        for j, dx in enumerate((-96, 96)):
            out.append({'id': f'deco:crucible_{i}_{j}', 'room': R('athanor'), 'decoration': ('dec35', '7dec48')[(i + j) % 2],
                        'at': [x + dx, y], 'floor_height': 96, 'notes': "Glassware on the bench of crucibles."})
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
        if room in ('roof',):
            continue
        o = geo.outline(room)
        cx = (min(p[0] for p in o) + max(p[0] for p in o)) // 2
        cy = (min(p[1] for p in o) + max(p[1] for p in o)) // 2
        w = max(p[0] for p in o) - min(p[0] for p in o)
        h = max(p[1] for p in o) - min(p[1] for p in o)
        r = int(min(1600, max(800, 0.55 * max(w, h))))
        if room in ('stairway',):
            continue
        col = WARM
        if room in geo.LABS:
            # D-89: each laboratory under its own coloured light (half its brew's colour, half the lamps' warmth)
            col = [(a + b) // 2 for a, b in zip(WARM, geo.LABS[room])]
        add(room, [cx, cy], r, col)
    for key, room, at, fh, col, *_ in BREWS:
        add(room, at, 640, col, height=160, fh=fh,
            pulse={'intensity': [0.35, 0.7], 'radius': [480, 680], 'frequency': 0.4},
            notes=f"The {key} brew's glow.")
    add('athanor', [0, 1632], 1600, [255, 120, 50], height=96, pulse={'intensity': [0.7, 1.0], 'radius': [1300, 1700], 'frequency': 0.33},
        notes="The hearth's coals.")
    for x, y in ((320, 192), (960, 192), (320, 640), (960, 640)):
        add('coils', [x, y], 700, [170, 200, 255], height=480, pulse={'intensity': [0.3, 1.0], 'radius': [400, 800], 'frequency': 1.5},
            notes="A coil's crackling crown.")
    return L


def sounds():
    return [
        {'id': 'sound:athanor', 'room': R('athanor'), 'at': [0, 1632], 'sound': 'lava loop', 'radius': 1800,
         'inner_radius': 600, 'volume': 0.7, 'notes': "The athanor's coals."},
        {'id': 'sound:coils', 'room': R('coils'), 'at': [640, 416], 'height': 400, 'sound': '7sparks', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.8, 'wait': [2, 6], 'notes': "The coils crackling."},
        {'id': 'sound:still', 'room': R('still'), 'at': [-1024, -1856], 'sound': 'drip02', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'wait': [3, 8], 'notes': "Melt dripping from the frosted still."},
        {'id': 'sound:poison', 'room': R('poison'), 'at': [-1120, 1248], 'sound': 'bubbling cauldron01',
         'radius': 1200, 'inner_radius': 300, 'volume': 0.5, 'notes': "The Poison Brew bubbling."},
        {'id': 'sound:energy', 'room': R('energy'), 'at': [-1120, 32], 'sound': 'bubbling cauldron01', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "The Energy Brew bubbling."},
        {'id': 'sound:magic', 'room': R('magic'), 'at': [1344, 1664], 'sound': 'bubbling cauldron01', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "The Magic Brew bubbling."},
        {'id': 'sound:roof', 'room': R('roof'), 'at': [0, 0], 'height': 256, 'sound': 'whistling wind',
         'radius': 3000, 'inner_radius': 1200, 'volume': 0.4, 'notes': "Wind over the roof."},
        {'id': 'sound:stairway', 'room': R('stairway'), 'at': [-512, 1728], 'height': 640, 'sound': 'whistling wind',
         'radius': 1600, 'inner_radius': 500, 'volume': 0.3, 'notes': "Wind down the Stairway to Heaven."},
        # Session 7: AU's tower bed (AUDIO.md, A8: XD-11 xeen_amb_tower, volume 0.3-0.4). One source in the middle of
        # the tower (above the first floor's centre, z 1120, half-way between the ground and the top floor) so no two
        # beds stack: every floor's centre inside the inner radius, the corner rooms fainter, the roof under the wind.
        {'id': 'sound:tower_bed', 'room': R('poison'), 'at': [0, 0], 'height': 480, 'sound': 'xeen_amb_tower',
         'radius': 3300, 'inner_radius': 1000, 'volume': 0.35, 'pan': False,
         'notes': "The tower's bed (AU): chimes and sparkle through the halls of all four floors."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('door'), 'at': [-1408, -1792], 'facing': 'n',
                  'notes': "Just inside the enchanted door, facing into the tower."},
        'doors': doors(), 'lifts': lifts(), 'switches': switches(), 'chests': chests(), 'spawns': spawns(),
        'monsters': monsters(), 'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [{'id': 'exit:enchanted_door', 'room': R('door'), 'at': [-1408, -2048], 'size': [192, 384],
                   'surface': S_('7solid01', 128, 256, scale=1.5), 'to': 'exit:x3_door',
                   'notes': "The enchanted door (Celeste's carved blue door): out to X3's islet (session 3; was a sealed panel)."}],
        'notes': "XD-11's contents, written by output/studio_cal/xd11/tools/dress.py: 10 doors (three brass lift gates), three stacked lifts, four levers (the steam valve and the three gate levers), six call buttons, five chests, 15 spawn points of the Magic constructs (9 Flying Feet, 6 Guardians), 10 placed Sorceresses and the Head Sorceress, the six brews' cauldrons.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("THE TOWER OF HIGH MAGIC. The Enchanted Key from the Cave of Illusion turns, and the door shuts again behind "
           "you with a sound like a held breath. Artemus was plain about it: the Skeleton Key that opens Darzog's "
           "Tower lies with the Archmage who built this place, in his study at the very top. Six laboratories climb "
           "the floors between, and their keepers will not welcome you. The stairs go up the east and west sides in "
           "turn.")


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say why the party is here (M13: the Skeleton Key in the Archmage's study at the top), on the first arrival only (arrived_once; a timer's once is once per visit)."})
    E.append({'id': 'evt:enchanted_door', 'preset': 'exit', 'source': 'exit:enchanted_door',
              'title': 'Leave the Tower of High Magic',
              'notes': "The way out to X3's islet (exit:x3_door). The game's exit window asks to leave the Tower of High Magic (aaze0055:6's sense). A plain exit, so the exit preset and the game's own window (D-24: no 'Leave X?' map question; question + leave only for a real choice, as the cloud stair)."})
    E.append({'id': 'evt:cloud_stair', 'preset': 'script', 'source': 'platform:cloud_top',
              'title': 'Stairway to Heaven',
              'effects': [{'exit': 'exit:x8_clouds'}],
              'notes': "Original title 'Stairway to Heaven' (aaze0058:6). F16 (2026-11-22): the standard entrance window (OK/Close, no Yes/No); OK climbs to X8 (exit:x8_clouds)."})
    for key, room, at, fh, col, bit, var, school, title in BREWS:
        E.append({'id': f'evt:brew_{key}', 'preset': 'script', 'source': f'deco:brew_{key}', 'title': title,
                  'condition': {'not': {'player_bit': bit}},
                  'effects': [{'add': {'var': var, 'value': 5}}, {'player_bit': bit}, {'text': BREW_TEXT[key]}],
                  'else_effects': [{'text': f"You have drunk the {title} already. It does nothing more for you."}],
                  'notes': f"poi:brews: +5 {school} resistance once per character (player bit {bit}; D-4 item 1). Original name '{title}' (aaze0055/0057)."})
    # doors
    for did, title in (('door:foyer_athanor', 'Door'), ('door:coils_core0', 'Door'), ('door:still_reagents', 'Door'),
                       ('door:energy_magic', 'Door'), ('door:library_study', 'Door')):
        e = {'id': 'evt:' + did.split(':')[1], 'preset': 'door', 'source': did, 'title': title}
        E.append(e)
    E.append({'id': 'evt:librarian_door', 'preset': 'door', 'source': 'door:librarian', 'title': "Librarian's door",
              'condition': {'item': 'librarian_key'}, 'action': 'open',
              'locked_text': "The door is locked. Its keyhole is cut in the shape of an open book: the Librarian's "
                             "Key, which the Head Sorceress keeps about her in the magic lab.",
              'notes': "link:quarters_l3: the Librarian's Key from the Head Sorceress's corpse opens it for good."})
    E.append({'id': 'evt:frost_door', 'preset': 'door', 'source': 'door:frost', 'title': 'Frozen door',
              'condition': {'map_var': 'frost_thawed'}, 'action': 'open',
              'else_effects': [{'message': "The door is frozen shut: a sheet of blue ice covers it from lintel to "
                                           "sill, and its hinges are lost in it. A steam pipe runs cold along the wall to its "
                                           "frame, back toward the reagent store."}],
              'notes': "The frost seal (link:poison_l1w): 'frozen shut' until the steam valve; then it opens."})
    E.append({'id': 'evt:valve', 'preset': 'switch', 'source': 'switch:valve', 'title': 'Steam valve',
              'condition': {'not': {'map_var': 'frost_thawed'}}, 'opens': ['door:frost'],
              'sets': {'map_var': 'frost_thawed'},
              'else_effects': [{'text': "The valve is open as far as it goes; steam hisses in the pipes."}],
              'effects': [{'message': "You heave the steam valve round. The pipes knock and hiss along the walls, "
                                      "and from the garden beyond the still comes the crack and drip of thawing ice: "
                                      "the frozen door of the west stair stands open."}],
              'notes': "poi:steam_valve: two states (shut, open); thaws and opens door:frost."})
    for n, room in ((1, 'landing1'), (2, 'quarters'), (3, 'landing3')):
        E.append({'id': f'evt:gate{n}_lever', 'preset': 'switch', 'source': f'switch:gate{n}', 'title': 'Gate lever',
                  'condition': {'not': {'map_var': f'gate{n}_open'}}, 'opens': [f'door:gate{n}'],
                  'sets': {'map_var': f'gate{n}_open'},
                  'else_effects': [{'text': "The lever is down and the gate stands open."}],
                  'text': "The bolt shoots back and the brass gate rises. Beyond it the cage will answer you now.",
                  'notes': f"poi:gate{n}_lever: unbolts lift gate {n}; the lift below this floor runs from now on."})
        E.append({'id': f'evt:gate{n}', 'preset': 'door', 'source': f'door:gate{n}', 'title': 'Lift gate',
                  'condition': {'map_var': f'gate{n}_open'}, 'action': 'open',
                  'locked_text': "The lift gate is bolted. The lever beside it on the wall works the bolt.",
                  'notes': f"Lift gate {n}: bolted until its lever is pulled."})
    for lid, n, lo, hi in (('a', 1, 'ground floor', 'first floor'), ('b', 2, 'first floor', 'second floor'),
                           ('c', 3, 'second floor', 'top floor')):
        cond = {'map_var': f'gate{n}_open'}
        refuse = (f"The brass cage will not move. Its gate on the {hi} is still bolted, and the cage answers only "
                  f"to an open gate.")
        E.append({'id': f'evt:lift_{lid}', 'preset': 'switch', 'source': f'lift:{lid}', 'title': 'Brass cage',
                  'condition': cond, 'toggles': [f'lift:{lid}'], 'text': "The cage creaks on its chains and moves.",
                  'else_effects': [{'text': refuse}]})
        E.append({'id': f'evt:lift_{lid}_bottom', 'preset': 'switch', 'source': f'switch:lift_{lid}_bottom',
                  'title': 'Call the cage', 'condition': cond, 'toggles': [f'lift:{lid}'],
                  'text': "Chains rattle in the shaft and the cage moves.",
                  'else_effects': [{'text': f"The cage hangs at the {hi} above and will not come down while its gate up there is bolted."}]})
        E.append({'id': f'evt:lift_{lid}_top', 'preset': 'switch', 'source': f'switch:lift_{lid}_top',
                  'title': 'Call the cage', 'condition': cond, 'toggles': [f'lift:{lid}'],
                  'text': "Chains rattle in the shaft and the cage moves.", 'else_effects': [{'text': refuse}]})
    # chests
    E.append({'id': 'evt:reagents_box', 'preset': 'chest', 'source': 'chest:reagents_box', 'title': 'Pandorian Box',
              'text': 'The box is empty.', 'notes': "Original lines 'Pandorian Box', 'The box is empty.' (aaze0055:4, 5)."})
    E.append({'id': 'evt:obs_box', 'preset': 'chest', 'source': 'chest:obs_box', 'title': 'Pandorian Box',
              'notes': "Original line 'Pandorian Box' (aaze0055:4): trapped (trap level 3)."})
    # D-89 (INWARD, 2026-11-22): the Enchanted Key (the Cave of Illusion's skull) guards only its beat, the Skeleton
    # Key's chest. The study door stays a plain door: the study, the observatory, the stairway and the roof beyond it
    # (two sorceresses, the roof's spawn, the Stairway to Heaven) are cleared without the key (the user's F17).
    E.append({'id': 'evt:study_chest', 'preset': 'chest', 'source': 'chest:study', 'title': 'Chest',
              'condition': {'lua': 'XeenQuests.hook("m13.study_door")'},
              'effects': [{'lua': 'XeenQuests.hook("m13.skeleton_key")'}],
              'notes': "D-89: A3's m13.study_door first (the Enchanted Key 12306; else its refusal line); then A3's hook m13.skeleton_key (once): sets 111260, 6,000 experience and its status line (aaze0058:7); the Skeleton Key 12100 is the chest's item (F15)."})
    E.append({'id': 'evt:quarters_chest', 'preset': 'chest', 'source': 'chest:quarters', 'title': 'Chest'})
    E.append({'id': 'evt:mysteries', 'preset': 'chest', 'source': 'chest:mysteries', 'title': 'Cabinet',
              'text': "MYSTERIES OF LIGHT, says the brass plate on the cabinet's door.",
              'notes': "'Mysteries of Light' (aaze0058:2) names the shelf; the Prismatic Light spellbook inside (D-4 item 2)."})
    E.append({'id': 'evt:art_of_magic', 'preset': 'text', 'source': 'platform:art_of_magic', 'title': 'The Art of Magic',
              'window': True,
              'text': "THE ART OF MAGIC. 'Every spell is a door, and every door a lock. The novice forces the lock; the "
                      "master learns the shape of the key. Fire wants feeding, water wants a vessel, air will go "
                      "where it likes, earth will not go at all. Learn what each wants, and it will come to your hand "
                      "as a dog comes to its name.' The rest is the Archmage's notes in the margins, in a hand too "
                      "small to read.",
              'notes': "poi:art_of_magic: lore only (D-4 item 2). Original title 'The Art of Magic' (aaze0058:1)."})
    for i in (0, 1):
        E.append({'id': f'evt:bed_{i}', 'preset': 'text', 'source': f'platform:bed_{i}', 'title': 'Bed',
                  'text': 'There is nothing on, in, or under the bed.', 'notes': "poi:beds (original line)."})
    return E


def wiring():
    return {'format': 0, 'variables': ['frost_thawed', 'gate1_open', 'gate2_open', 'gate3_open'],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "XD-11's events, written by output/studio_cal/xd11/tools/dress.py."}


ATMOS = {'format': 0, 'open_sky': {'mode': 'open', 'preset': 'fair', 'view': 'outdoor', 'view_distance_scale': 1},
         'daylight': {'ambient_rgb': [90, 90, 100], 'sun_rgb': [255, 240, 220]},
         'notes': "The roof and the Stairway to Heaven open to the sky (their sky faces); the rest is lit by its own lights."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
    gen.dump(folder / 'atmosphere.yml', ATMOS)
