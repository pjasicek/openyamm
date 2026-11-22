#!/usr/bin/env python3
"""XD-10 Cave of Illusion, L4: objects.yml, wiring.yml (written by gen.py L4)."""
import geo
from geo import S_

FF, G, WG = 11600, 11601, 11591
COLD = [150, 175, 215]
DEEP = [110, 140, 190]
WARM = [220, 170, 120]
HIDDEN_GROUP = 10
GEMS = [177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 177, 178, 179, 180, 181]


def R(r):
    return 'room:' + r


# ------------------------------------------------------------------------------------------------ objects
MIRAGES = [
    # key, opening, approach room, plate at, plate size, notes
    ('safe', 'open:false_cache', 'false_passage', [-1344, 8800], [256, 128],
     "The phantom safe's cave's north wall: a mirage into the cache."),
    ('cache', 'open:cache_n', 'north_mouth', [-480, 9472], [128, 256],
     "The north mouth's west wall: a mirage into the cache."),
    ('maze', 'open:maze_skulls', 'mirror_maze', [704, 6112], [256, 128],
     "The mirror maze's north wall: a mirage into the deep skull alcoves."),
    ('vault', 'open:grotto_vault', 'grotto', [6784, 3936], [256, 128],
     "The grotto's north wall: a mirage into the phantom vault."),
]
GATES = [('drowned', 'open:ledge_drowned', "the drowned gallery"), ('steps', 'open:ledge_steps', "the steps to the reservoir bed"),
         ('wreck', 'open:drowned_wstair', "the stair down to the wreck")]


def doors():
    out = []
    for key, op, room, at, size, notes in MIRAGES:
        out.append({'id': f'door:mirage_{key}', 'opening': op, 'kind': 'slide_down', 'speed': 4000,
                    'surface': dict(geo.MIRAGE_DEEP if geo.R[room][4] == 'theme:deep' else geo.MIRAGE), 'tile': True,
                    'notes': notes + " Rock with the fluid bit (it ripples); a click or walking into it opens it at once."})
    for key, op, what in GATES:
        out.append({'id': f'door:gate_{key}', 'opening': op, 'kind': 'slide_up', 'speed': 128,
                    'surface': dict(geo.BRICK), 'tile': True, **({'leaves': 2} if key == 'wreck' else {}),
                    'notes': f"A stone sluice gate before {what}: shut until the plug is pulled."})
    out.append({'id': 'door:sluice', 'opening': 'open:frost_sluice', 'kind': 'slide_left',
                'surface': dict(geo.SLUICE_DOOR, fit=True), 'notes': "The sluice's door (d33's t09a03c)."})
    return out


def movers():
    return [
        {'id': 'mover:water', 'room': R('reservoir'), 'outline': geo.WATER_OUTLINE, 'bottom': 0,
         'height': geo.WATER_TOP - geo.U2, 'travel': [0, 0, -638], 'speed': 107,
         'surface': dict(geo.WATER), 'top_surface': dict(geo.WATER),
         'notes': "The reservoir's water: one block from the bed to -660 that sinks 638 (its top 2 under the bed, so the hidden monsters on it stand on the bed) in about 6 s when the plug is pulled (D-4 item 2)."},
        {'id': 'mover:plug', 'room': R('sluice'), 'at': [2048, 2944], 'size': [224, 224], 'bottom': 0, 'floor_height': -64,
         'height': 144, 'travel': [0, 0, 448], 'speed': 160, 'surface': dict(geo.PLUG_SIDE), 'top_surface': dict(geo.PLUG_TOP),
         'parts': [{'at': [2048, 2944], 'size': [32, 32], 'height': 424, 'surface': dict(geo.IRON),
                    'notes': "The plug's chain, up into the roof."}],
         'notes': "The great bronze plug in its pool, its iron chain rising into the roof; pulled, it rises out of the pool."},
    ]


def plates():
    return [{'id': f'plate:mirage_{key}', 'room': R(room), 'at': at, 'size': size,
             'notes': "The floor before a mirage: stepping here touches it."} for key, op, room, at, size, _ in MIRAGES]


def chests():
    return [
        {'id': 'chest:cache', 'room': R('mirage_cache'), 'at': [-1280, 9744], 'treasure_level': 3,
         'random_items': 2, 'gold': 400,
         'notes': "The real treasure behind the phantom safe; its first opening gives the fixed Potion of Might (evt:chest_cache, D-22.2)."},
        {'id': 'chest:post', 'room': R('guard_post'), 'at': [-576, 6288], 'treasure_level': 3,
         'random_items': 3, 'gold': 600, 'notes': "The Guardians' chest."},
        {'id': 'chest:gems', 'room': R('echo_cave'), 'at': [-576, 3696], 'treasure_level': 3,
         'random_items': 0, 'items': GEMS,
         'notes': "The echo cave's cache: 15 fixed gems (D-1.6, before the great skull)."},
        {'id': 'chest:wreck', 'room': R('wreck'), 'at': [2048, 1136], 'treasure_level': 3,
         'random_items': 3, 'gold': 500, 'notes': "The sunken boat's strongbox."},
        {'id': 'chest:hoard', 'room': R('phantom_vault'), 'at': [6784, 5008], 'treasure_level': 5,
         'random_items': 4, 'gold': 2000, 'trap_level': 3, 'notes': "The cave's hoard behind the grotto's mirage."},
    ]


PLACED = {
    'north_mouth': [(FF, [-256, 9280]), (FF, [256, 9216])],
    'icicle_hall': [(FF, [0, 7360]), (FF, [384, 7232]), (FF, [0, 8256]), (FF, [320, 8064])],
    'false_passage': [(FF, [-1472, 8064]), (FF, [-1280, 7680])],
    'mirage_hall': [(FF, [0, 5888]), (FF, [640, 6080]), (FF, [-256, 4864]), (G, [768, 5120]), (G, [256, 4736])],
    'frost_cavern': [(FF, [0, 3584]), (FF, [640, 3584]), (G, [256, 2816]), (G, [768, 2944])],
    'south_mouth': [(FF, [-128, 1600]), (FF, [320, 1536])],
    'sluice': [(G, [1664, 3456]), (G, [2432, 3456]), (G, [1664, 2624])],
    'drowned': [(WG, [704, 4672]), (WG, [1408, 3840]), (WG, [416, 3776])],
    'mirror_maze': [(FF, [960, 5120]), (FF, [1472, 5632]), (FF, [768, 5696]), (FF, [1440, 6080]), (G, [1024, 5440])],
    'guard_post': [(G, [-896, 5376]), (G, [-256, 5376]), (G, [-896, 5952]), (G, [-256, 5952])],
    'echo_cave': [(FF, [-768, 4160]), (FF, [-384, 4096])],
    'sump': [(WG, [704, 1664]), (WG, [704, 1088]), (FF, [0, 1856])],
    'wreck': [(FF, [1408, 1856]), (FF, [2432, 1920])],
    'reservoir': [(WG, [4032, 2496]), (WG, [3904, 1152]), (FF, [4032, 1600]), (FF, [4096, 2944]), (FF, [3840, 3392]),
                  (FF, [4160, 2112])],
    'phantom_vault': [(WG, [6784, 4608]), (FF, [6528, 4800]), (FF, [7040, 4800])],
}
NAME = {FF: 'ff', G: 'guardian', WG: 'water_golem'}


def monsters():
    out = []
    for room, lst in PLACED.items():
        n = {}
        for row, at in lst:
            n[row] = n.get(row, 0) + 1
            d = {'id': f'monster:{room}_{NAME[row]}_{n[row]}', 'room': R(room), 'monster': row, 'at': at,
                 'facing': 270, 'hostile': True, 'group': 1}
            if room == 'reservoir':
                d['group'] = HIDDEN_GROUP
                d['hidden'] = True
                d['notes'] = "Under the water until the plug is pulled: shown on the party's first step onto the drained bed."
            out.append(d)
    return out


SKULLS = [
    # key, room, platform, at, floor height, hover
    ('luck', 'skulls_1', [-1728, 3456], 96, 'Skull (Luck)'),
    ('personality', 'skulls_1', [-1728, 2944], 96, 'Skull (Personality)'),
    ('intellect', 'skulls_2', [448, 6976], -544, 'Skull (Intellect)'),
    ('speed', 'skulls_2', [832, 6976], -544, 'Skull (Speed)'),
    ('great', 'grotto', [7200, 3328], -1152, 'Great skull'),
]


def decorations():
    out = []
    for key, room, at, fh, title in SKULLS:
        out.append({'id': f'deco:skull_{key}', 'room': R(room), 'decoration': '7dec20', 'at': at, 'floor_height': fh,
                    'facing': 'e' if room != 'grotto' else 'w',
                    'notes': f"{title}: a talking skull on its rock shelf (clicked: evt:skull_{key})."})
    props = [
        ('skulls_1', 'sklplrev', [-1760, 3200]), ('grotto', 'sklplrev', [7232, 2976]), ('grotto', 'sklplrev', [7232, 3680]),
        ('skulls_2', 'sklplrev', [640, 7040]),
        ('mirage_hall', 'stlmite1', [-832, 4672]),         ('mirage_hall', 'stlmite3', [-832, 6400]), ('icicle_hall', 'stlmite3', [-576, 8576]),
        ('icicle_hall', 'stlmite1', [832, 7104]), ('frost_cavern', 'stlmite3', [-576, 2560]),
        ('frost_cavern', 'stlmite3', [1088, 2560]), ('echo_cave', 'stlmite3', [-960, 4416]),
        ('guard_post', 'stlmite1', [-1120, 4992]), ('sump', 'stlmite3', [-64, 960]),
        ('drowned', '6rock02', [1472, 4640]), ('drowned', '6rock03', [384, 4544]),
        ('wreck', '7dec21', [1312, 1216]), ('wreck', '7dec21', [1440, 1136]), ('sump', '6rock05', [704, 896]),
    ]
    n = {}
    for room, dec, at in props:
        n[room] = n.get(room, 0) + 1
        d = {'id': f'deco:{room}_{n[room]}', 'room': R(room), 'decoration': dec, 'at': at}
        if room == 'reservoir':
            d['floor_height'] = geo.U2
        out.append(d)
    for i, (wall, along) in enumerate((('w', 0.3), ('w', 0.7), ('s', 0.5))):
        out.append({'id': f'deco:sluice_torch_{i}', 'room': R('sluice'), 'decoration': 'torch02', 'wall': wall,
                    'along': along, 'height': 192})
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
        col = WARM if room == 'sluice' else (COLD if geo.R[room][2] == 0 else DEEP)
        r = int(min(2400, max(800, 0.6 * max(w, h))))
        if room == 'reservoir':
            for at in ([4416, 2304], [4416, 5120]):
                add(room, at, 2400, DEEP, height=1200)
            continue
        add(room, c, r, col)
    for key, op, room, at, size, _ in MIRAGES:
        add(room, at, 512, [170, 200, 255], height=160,
            pulse={'intensity': [0.3, 0.7], 'radius': [380, 560], 'frequency': 0.3}, notes="The mirage's shimmer.")
    add('grotto', [7104, 3328], 900, [140, 220, 160], height=256,
        pulse={'intensity': [0.5, 0.9], 'radius': [700, 1000], 'frequency': 0.2}, notes="The great skull's pale glow.")
    return L


def sounds():
    return [
        {'id': 'sound:north_wind', 'room': R('north_mouth'), 'at': [0, 9856], 'height': 256, 'sound': 'whistling wind',
         'radius': 1600, 'inner_radius': 500, 'volume': 0.4, 'notes': "Tundra wind at the north mouth."},
        {'id': 'sound:south_wind', 'room': R('south_mouth'), 'at': [64, 1280], 'height': 256, 'sound': 'whistling wind',
         'radius': 1400, 'inner_radius': 400, 'volume': 0.35, 'notes': "Wind at the south mouth."},
        {'id': 'sound:icicles', 'room': R('icicle_hall'), 'at': [128, 7872], 'sound': 'drip02', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.5, 'wait': [2, 6], 'notes': "Melt dripping from the icicles."},
        {'id': 'sound:mirages', 'room': R('mirage_hall'), 'at': [256, 5504], 'sound': 'drip03', 'radius': 1800,
         'inner_radius': 500, 'volume': 0.4, 'wait': [3, 8], 'notes': "Drips in the warm, wet hall."},
        {'id': 'sound:sluice', 'room': R('sluice'), 'at': [2048, 2944], 'sound': 'water lapping loop', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.5, 'notes': "Water lapping round the plug."},
        {'id': 'sound:reservoir', 'room': R('reservoir'), 'at': [4416, 3712], 'height': 128, 'sound': 'water lapping loop',
         'radius': 3600, 'inner_radius': 1200, 'volume': 0.5, 'notes': "The reservoir's water (heard from the ledge)."},
        {'id': 'sound:sump', 'room': R('sump'), 'at': [288, 1312], 'sound': 'rushing water loop', 'radius': 1600,
         'inner_radius': 400, 'volume': 0.7, 'notes': "The roaring sump."},
        {'id': 'sound:drowned', 'room': R('drowned'), 'at': [960, 4224], 'sound': 'drip01', 'radius': 1400,
         'inner_radius': 400, 'volume': 0.5, 'wait': [2, 5], 'notes': "The drowned gallery dripping."},
        {'id': 'sound:echo', 'room': R('echo_cave'), 'at': [-576, 4160], 'sound': 'drip02', 'radius': 1200,
         'inner_radius': 300, 'volume': 0.6, 'wait': [4, 9], 'notes': "Drips that echo."},
    ]


def objects():
    return {
        'format': 0,
        'start': {'room': R('north_mouth'), 'at': [0, 9664], 'facing': 's',
                  'notes': "Just inside the north mouth, facing into the cave (X5's doors arrive here)."},
        # merge point 14: the south mouth's named arrival, for X5's south door (A6: `arrival: entrance:x5_south`)
        'arrivals': [{'entrance': 'entrance:x5_south', 'room': R('south_mouth'), 'at': [64, 1408], 'facing': 'n',
                      'notes': "Just inside the south mouth, facing into the cave (X5's south door arrives here)."}],
        'doors': doors(), 'movers': movers(), 'chests': chests(), 'monsters': monsters(),
        'decorations': decorations(), 'lights': lights(), 'sounds': sounds(),
        'exits': [
            {'id': 'exit:north', 'room': R('north_mouth'), 'wall': 'north', 'size': [640, 416],
             'surface': S_('7solid01', 128, 128, scale=2), 'to': 'exit:x5_north',
             'notes': "The north mouth's daylight: the snow of the Winterkill Tundra (X5)."},
            {'id': 'exit:south', 'room': R('south_mouth'), 'wall': 'south', 'size': [512, 384],
             'surface': S_('7solid01', 128, 128, scale=2), 'to': 'exit:x5_south',
             'notes': "The south mouth's daylight: out to the Troll Forest side of X5."},
        ],
        'notes': "XD-10's contents, written by output/studio_cal/xd10/tools/dress.py: 8 doors (four mirages, three stone sluice gates, the sluice's door), two movers (the water, the plug), four plates before the mirages, five chests, 50 placed monsters (30 Flying Feet, 12 Guardians, 8 Water Golems; the reservoir's six hidden under the water until the bed is walked), five skulls.",
    }


# ------------------------------------------------------------------------------------------------- wiring
ARRIVAL = ("THE CAVE OF ILLUSION. Warm, wet breath blows out of the ice into your faces. Artemus was plain about it: "
           "somewhere deep in this cave a talking skull sells the key to the Tower of High Magic, and skulls take "
           "gems, not gold. Mind the walls here: not all of them are there.")
MIRAGE_TEXT = "The mirage dissipates with your touch."
SAFE_TEXT = "Your hand passes through the safe as though it were not there."
WEAK_TEXT = "You aren't strong enough to pull the plug. A stronger arm, or a potion of Might, might shift it."
PULLED_TEXT = ("You set your feet and heave on the chain. The bronze plug comes up out of its pool with a sucking roar, "
               "and through the window the black water of the reservoir begins to sink. The water roars away down the "
               "sump; somewhere below, stone gates grind open.")
HANGS_TEXT = "The plug hangs free on its chain. Below the window the reservoir lies empty."
GATE_TEXT = "The stone sluice gate is shut fast. Water presses against it from the other side."
NOTICE_TEXT = ("A board, the words scratched deep: 'THE SKULLS TAKE GEMS, NOT GOLD. THE GREAT ONE AT THE BOTTOM WANTS "
               "TEN FOR HIS KEY - KEEP TEN. THE ECHO CAVE PAST THE GUARDIANS' POST KEEPS SOME. THE PLUG IN THE SLUICE "
               "LETS THE WATER OUT, IF YOU ARE STRONG.'")

SKULL_DEALS = {
    # key: (bit, price, stat selector, rise, offer hook, stat name, the skull's words on a sale)
    'luck': (11236, 3, 'BaseLuck', 2, 'm12.skull_upper', 'Luck'),
    'personality': (11237, 3, 'BasePersonality', 2, 'm12.skull_upper', 'Personality'),
    'intellect': (11238, 5, 'BaseIntellect', 3, 'm12.skull_deep', 'Intellect'),
    'speed': (11239, 5, 'BaseSpeed', 3, 'm12.skull_deep', 'Speed'),
}


def skull_lua(key):
    bit, price, var, rise, hook, stat = SKULL_DEALS[key]
    return "\n".join([
        f'if IsPlayerBitSet(PlayerBit({bit})) then',
        '    XeenQuests.hook("m12.skull_sold")',
        '    return',
        'end',
        'if continueStep == 1 then',
        f'    if Xeen.payGems({price}) then',
        f'        AddValue({var}, {rise})',
        f'        SetPlayerBit(PlayerBit({bit}))',
        f'        evt.SimpleMessage("The skull\'s jaw clacks shut on {price} of your gems. +{rise} {stat} (permanent).")',
        '    else',
        '        XeenQuests.hook("m12.skull_poor")',
        '    end',
        '    return',
        'end',
        'if continueStep ~= nil then',
        '    return',
        'end',
        f'if Xeen.gemCount() < {price} then',
        '    XeenQuests.hook("m12.skull_poor")',
        '    return',
        'end',
        f'XeenQuests.hook("{hook}")',
        f'AskChoiceWithAnswerSteps(eventId, 3, "{price} gems for +{rise} {stat}?", {{{{Answer = "Yes", Step = 1}}, {{Answer = "No", Step = 2}}}})',
    ])


GREAT_LUA = "\n".join([
    'if not IsQBitSet(QBit(111240)) then',
    '    XeenQuests.hook("m12.skull")',
    '    return',
    'end',
    'if IsPlayerBitSet(PlayerBit(11240)) then',
    '    XeenQuests.hook("m12.skull_sold")',
    '    return',
    'end',
    'if continueStep ~= nil and continueStep >= 1 and continueStep <= 3 then',
    '    if Xeen.payGems(10) then',
    '        local stat = "Might"',
    '        if continueStep == 1 then',
    '            AddValue(BaseMight, 5)',
    '        elseif continueStep == 2 then',
    '            AddValue(BaseEndurance, 5)',
    '            stat = "Endurance"',
    '        else',
    '            AddValue(BaseAccuracy, 5)',
    '            stat = "Accuracy"',
    '        end',
    '        SetPlayerBit(PlayerBit(11240))',
    '        evt.SimpleMessage("The great skull takes ten of your gems and grins wider. +5 " .. stat .. " (permanent).")',
    '    else',
    '        XeenQuests.hook("m12.skull_poor")',
    '    end',
    '    return',
    'end',
    'if continueStep ~= nil then',
    '    return',
    'end',
    'if Xeen.gemCount() < 10 then',
    '    XeenQuests.hook("m12.skull_poor")',
    '    return',
    'end',
    'XeenQuests.hook("m12.skull_grotto")',
    'AskChoiceWithAnswerSteps(eventId, 5, "Ten gems for +5 to Might, Endurance or Accuracy?", {{Answer = "Might", Step = 1}, '
    '{Answer = "Endurance", Step = 2}, {Answer = "Accuracy", Step = 3}})',
])

DRAIN_OPENS = ['mover:plug', 'mover:water', 'door:gate_drowned', 'door:gate_steps', 'door:gate_wreck']


def events():
    E = []
    E.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
              'condition': {'not': {'qbit': 'arrived_once'}},
              'effects': [{'message': ARRIVAL}, {'qbit': 'arrived_once'}],
              'notes': "Say why the party is here (M12: the talking skull's key, for gems), on the first arrival only (arrived_once 110641)."})
    for key, op, room, at, size, _ in MIRAGES:
        var = f'mirage_{key}'
        # Merge point 13: the studio's `touch` runs the door's event when the party walks into the mirage (the plates
        # before the walls and their step events are gone).
        E.append({'id': f'evt:mirage_{key}', 'preset': 'door', 'source': f'door:mirage_{key}', 'title': 'Cave wall',
                  'action': 'open', 'touch': True, 'effects': [{'set': {'var': {'map_var': var}, 'value': 1}}],
                  'text': MIRAGE_TEXT,
                  'notes': "A mirage (D-4 item 1): a click or a touch opens it at once. Original line (aaze0042:24)."})
    E.append({'id': 'evt:safe', 'preset': 'text', 'source': 'platform:safe', 'title': 'Safe', 'text': SAFE_TEXT,
              'notes': "poi:safe: the phantom safe (aaze0042:72); not a chest."})
    E.append({'id': 'evt:notice', 'preset': 'text', 'source': 'panel:notice', 'title': 'Notice', 'window': True,
              'text': NOTICE_TEXT, 'notes': "poi:notice: gems before the great skull (D-1.6), plainly."})
    E.append({'id': 'evt:plug', 'preset': 'switch', 'source': 'mover:plug', 'title': 'Bronze plug',
              'condition': {'not': {'qbit': 'plug_pulled'}, 'stat': {'name': 'ActualMight', 'at_least': 30}},
              'opens': DRAIN_OPENS, 'sets': {'qbit': 'plug_pulled'},
              'effects': [{'lua': 'evt.PlaySoundName("xeen_reservoir_drain", 2048, 2944, 0)'}, {'message': PULLED_TEXT}],
              'else_effects': [{'lua': 'if IsQBitSet(QBit(110640)) then evt.StatusText("' + HANGS_TEXT
                                       + '") else evt.StatusText("' + WEAK_TEXT + '", 6) end'}],
              'notes': "poi:plug (D-4 item 3): Might 30 on the pulling member, potions counting (ActualMight); "
                       "'You aren't strong enough to pull the plug.' (aaze0042:23) and A3's hint (a stronger arm or a Might potion, 2026-11-22). Pulled once: plug_pulled, the water sinks, the three gates open."})
    E.append({'id': 'evt:drained_load', 'preset': 'switch', 'trigger': 'load', 'condition': {'qbit': 'plug_pulled'},
              'opens': DRAIN_OPENS,
              'notes': "After a refill the doors and movers start as built: the pulled plug's water stays gone."})
    E.append({'id': 'evt:bed_walked', 'preset': 'script', 'trigger': 'step', 'source': 'room:reservoir',
              'condition': {'qbit': 'plug_pulled', 'not': {'map_var': 'bed_revealed'}},
              'effects': [{'show_actors': HIDDEN_GROUP}, {'set': {'var': {'map_var': 'bed_revealed'}, 'value': 1}}],
              'text': "Shapes stir in the silt of the drained bed.",
              'notes': "D-18 (c): the reservoir's six (placed hidden under the water, group 10, about 1,200 from the steps' and the wreck's ways onto the bed) appear the first time the party steps onto the drained bed, from any side; guarded by the map variable bed_revealed (a refill resets it with the actors)."})
    for key, op, what in GATES:
        E.append({'id': f'evt:gate_{key}', 'preset': 'door', 'source': f'door:gate_{key}', 'title': 'Sluice gate',
                  'condition': {'qbit': 'plug_pulled'}, 'action': 'open', 'locked_text': GATE_TEXT,
                  'notes': f"The stone sluice gate before {what}: the plug opens it."})
    E.append({'id': 'evt:sluice_door', 'preset': 'door', 'source': 'door:sluice', 'title': 'Door'})
    for key in SKULL_DEALS:
        title = next(t for k, _, _, _, t in SKULLS if k == key)
        E.append({'id': f'evt:skull_{key}', 'preset': 'script', 'source': f'deco:skull_{key}', 'title': title,
                  'lua': skull_lua(key),
                  'notes': f"poi:skulls: {title}, once per character (player bit {SKULL_DEALS[key][0]}); A3's hooks for the words."})
    E.append({'id': 'evt:skull_great', 'preset': 'script', 'source': 'deco:skull_great', 'title': 'Great skull',
              'lua': GREAT_LUA,
              'notes': "goal:enchanted_key: A3's hook m12.skull (10 gems: the Enchanted Key, qbit 111240, 1,500 XP); after it one question with three answers (D-18's cheaper option): +5 Might, Endurance or Accuracy for 10 gems, once per character (bit 11240)."})
    E.append({'id': 'evt:chest_cache', 'preset': 'chest', 'source': 'chest:cache', 'title': 'Chest',
              'effects': [{'lua': 'if not IsQBitSet(QBit(110642)) then SetQBit(QBit(110642)) evt.SetHeldItem(240, {bonus = 10}) '
                                  'evt.StatusText("A flask of red draught lies on top.") end'}],
              'notes': "D-22.2: the Potion of Might at a fixed power 10 (+30 Might: any member reaches the plug's 30), given once per game on the cache's first opening (map qbit cache_potion 110642); the chest holds no random Might Boost."})
    for c in ('post', 'gems', 'wreck', 'hoard'):
        E.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}', 'title': 'Chest'})
    E.append({'id': 'evt:exit_north', 'preset': 'exit', 'source': 'exit:north', 'title': 'Leave the Cave of Illusion',
              'notes': "'Leave the Cave of Illusion?' (aaze0042:49): to X5 before the north mouth."})
    E.append({'id': 'evt:exit_south', 'preset': 'exit', 'source': 'exit:south', 'title': 'Leave the Cave of Illusion',
              'notes': "'Leave the Cave of Illusion?' (aaze0042:49): to X5's Troll Forest side."})
    return E


def wiring():
    return {'format': 0, 'variables': [f'mirage_{k}' for k, *_ in MIRAGES] + ['bed_revealed'],
            'events': sorted(events(), key=lambda e: e['id']),
            'notes': "XD-10's events, written by output/studio_cal/xd10/tools/dress.py."}


def write(folder):
    import gen
    gen.dump(folder / 'objects.yml', objects())
    gen.dump(folder / 'wiring.yml', wiring())
