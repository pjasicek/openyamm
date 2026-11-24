#!/usr/bin/env python3
"""X8: writes L4 objects.yml, wiring.yml and atmosphere.yml (lane A6 sub-agent, 2026-11-20). Positions from gen.py."""
import json
import math
import random
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402

L4 = gen.BRIEF / 'L4'
HARPY, HAG, QUEEN, FEET, GUARD, GOLEM = 11520, 11521, 11522, 11600, 11601, 11592

# The fall (D-6.4): A3's Xeen.skyFall(x, y, groundZ, yaw, map, onWater); yaw in the game's 2048 units.
X1_LANDING = (11264, -7936, 768, 1752)    # 1,100 north-west of XD-04's door on X1, facing the door
X2_LANDING = (-10240, 8448, 576, 256)     # A5's point in Lake Darzog's north-east lobe, facing the near shore
# X3 (A5, installed 2026-11-20): the lagoon east of the Tower of High Magic's islet, about 1,300 from XD-11's door
# (its exit (256, -1674, 992)), on the water (860; no actor within 12,000), facing the islet
X3_LANDING = (1536, -1280, 864, 1120)
X3_LIVE = (gen.ROOT / 'assets_dev/worlds/xeen/maps/xeen_x3.odm').exists()
ZONE_X = 3072                             # |x| under this: the half-way cloud and the inner 2,000 of each span
FALL_LUA = (
    'local x, y, z = evt.GetPartyPosition()\n'
    '{guard}'
    'if x > {zone} then\n'
    '    Xeen.skyFall({x1[0]}, {x1[1]}, {x1[2]}, {x1[3]}, "xeen_x1.odm", false)\n'
    '{west}'
    'else\n'
    '    -- the middle zone (D-6.4)\n'
    '    Xeen.skyFall({x2[0]}, {x2[1]}, {x2[2]}, {x2[3]}, "xeen_x2.odm", true)\n'
    'end')


def fall_lua(guard):
    west = ('elseif x < -{zone} then\n'
            '    Xeen.skyFall({x3[0]}, {x3[1]}, {x3[2]}, {x3[3]}, "xeen_x3.odm", true)\n').format(
                zone=ZONE_X, x3=X3_LANDING) if X3_LIVE else ''
    return FALL_LUA.format(guard='if z > -1000 then return end\n' if guard else '', zone=ZONE_X,
                           x1=X1_LANDING, x2=X2_LANDING, west=west)


def stair_head(iid, x):
    cx, cy = gen.ISLANDS[iid][0]
    rim = gen.rim_point(gen.OUTLINES[iid], (x, cy), (x, cy - 10000))
    return [x, int(rim[1]) + 448]


WITCH_ARRIVAL = stair_head('witch_landing', 11520)
MAGIC_ARRIVAL = stair_head('stair_landing', -10752)


def at(iid, dx, dy):
    (cx, cy) = gen.ISLANDS[iid][0]
    return [cx + dx, cy + dy]


def monsters():
    out = []
    # (island, group, [(monster, dx, dy)...])
    plan = [
        ('witch_landing', 10, [(HARPY, -640, 1184), (HARPY, 0, 1376), (HARPY, 576, 1120), (HAG, 128, 960)]),
        ('offering_terrace', 11, [(HARPY, -1024, -768), (HAG, -768, 896), (HAG, 1280, 640), (HARPY, 1408, -896),
                                  (HAG, 0, -1152)]),
        ('nest_spires', 12, [(HAG, -1152, 256), (HAG, -384, 1408), (HARPY, 384, 1536)]),
        ('nest_spires', 13, [(HAG, 1152, -768), (HAG, 384, -256), (HARPY, 1408, 512), (HAG, -768, -1408)]),
        ('queens_eyrie', 14, [(QUEEN, 0, 384), (HAG, -768, 768), (HAG, 768, 768), (HAG, -640, -384),
                              (HAG, 640, -384), (HAG, 0, 1152)]),
        ('explorers_rock', 15, [(HARPY, -512, -384), (HARPY, 512, -384)]),
        ('witch_perch', 16, [(HARPY, -384, -640), (HAG, 768, 256), (HAG, 0, 512)]),
        ('half_way', 17, [(HARPY, -256, 256), (HARPY, 384, -128)]),
        ('stair_landing', 20, [(FEET, -768, 1216), (FEET, 0, 1344), (FEET, 896, 1088), (FEET, 1408, 512),
                               (GUARD, 384, 896)]),
        ('observatory_isle', 21, [(GUARD, -1152, -384), (GUARD, 768, -896), (GUARD, 1408, 256), (FEET, 896, 1152),
                                  (FEET, -1536, 640)]),
        ('observatory_isle', 22, [(GUARD, -128, -1408), (GUARD, 1664, -1280)]),
        ('golem_heights', 23, [(FEET, -1792, -640), (FEET, -1280, -1152), (FEET, -512, -1472), (FEET, 1536, -896),
                               (FEET, 1792, -256), (FEET, 896, -1408), (GUARD, 256, -256)]),
        ('rhyme_garden', 24, [(FEET, -640, -640), (FEET, 640, 512), (GUARD, -512, 512), (GUARD, 512, -512),
                              (GUARD, 1024, 0)]),
        ('lantern_cloud', 25, [(GUARD, -640, -256), (GUARD, 384, 256), (GUARD, 896, -128), (GUARD, -128, 640),
                               (FEET, 0, -768)]),
    ]
    rnd = random.Random(8)
    names = {HARPY: 'harpy', HAG: 'hag', QUEEN: 'queen', FEET: 'feet', GUARD: 'guardian'}
    count = {}
    for iid, group, members in plan:
        for monster, dx, dy in members:
            key = f'{iid}_{names[monster]}'
            count[key] = count.get(key, 0) + 1
            e = {'id': f'monster:{key}_{count[key]}', 'room': 'room:air', 'monster': monster, 'at': at(iid, dx, dy),
                 'facing': rnd.choice([0, 45, 90, 135, 180, 225, 270, 315]), 'hostile': True, 'group': group}
            if monster == QUEEN:
                e['notes'] = "The Harpy Queen (24) on her great nest, her court of Hags round her."
            out.append(e)
    for k, (dx, dy) in enumerate(((-384, 1024), (768, 192))):
        out.append({'id': f'monster:cloud_golem_{k + 1}', 'room': 'room:air', 'monster': GOLEM,
                    'at': at('golem_heights', dx, dy), 'facing': 270, 'hostile': True, 'group': 30,
                    'immobile': True,
                    'notes': ('A Cloud Golem (50) standing like weather at the back of the heights: the map\'s rare '
                              'danger, a trap far above the band (D-1.2); it keeps its place.')})
    return out


def decorations():
    d = []

    def add(did, deco, iid, dx, dy, **kw):
        e = {'id': f'deco:{did}', 'room': 'room:air', 'decoration': deco, 'at': at(iid, dx, dy)}
        e.update(kw)
        d.append(e)
    add('explorer_statue', '7dec55', 'explorers_rock', 0, 128, facing=270)
    add('rhyme_1', '7dec54', 'witch_perch', -512, 128, facing=0)
    add('rhyme_2', '7dec54', 'rhyme_garden', 0, 0, facing=270)
    add('rhyme_3', '7dec54', 'observatory_isle', 1408, -640, facing=0)
    add('offering_1', 'sta1a', 'offering_terrace', 512, 512, facing=180)
    add('offering_2', 'sta1a', 'offering_terrace', 1024, -256, facing=180)
    # nests: bones and skulls in the straw
    for iid, (dx, dy), tag in (('nest_spires', (-768, 256), 'n1'), ('nest_spires', (896, -192), 'n2'),
                               ('witch_perch', (384, -256), 'n3')):
        add(f'{tag}_bones', '7dec18', iid, dx - 64, dy + 32)
        add(f'{tag}_skull', '7dec20', iid, dx + 96, dy - 64)
    for k, (dx, dy) in enumerate(((-256, 384), (-128, 576), (-320, 64), (128, 64))):
        add(f'eyrie_bones_{k + 1}', '7dec18' if k % 2 == 0 else 'dec19', 'queens_eyrie', dx, dy)
    for k, (dx, dy) in enumerate(((-1024, -640), (1152, -768))):
        add(f'heights_bones_{k + 1}', 'dec19', 'golem_heights', dx, dy)
    # lanterns on their posts
    for k, (dx, dy) in enumerate(((-768, 384), (512, 640), (0, -512), (896, -384))):
        add(f'lantern_{k + 1}', 'dec02', 'lantern_cloud', dx, dy)
    return d


def chests():
    return [
        {'id': 'chest:hoard', 'room': 'room:air', 'at': at('queens_eyrie', 256, 128), 'kind': 'ch2', 'facing': 's',
         'treasure_level': 4, 'random_items': 3, 'gold': 600, 'notes': "The Harpy Queen's hoard, in her nest."},
        {'id': 'chest:star_charts', 'room': 'room:air', 'at': [gen.ISLANDS['observatory_isle'][0][0] - 768,
                                                                gen.ISLANDS['observatory_isle'][0][1] + 1152 - 704],
         'kind': 'ch1', 'facing': 's', 'treasure_level': 3, 'random_items': 2, 'gold': 300,
         'notes': "The sorcerer's chest of star charts and coin, on the observatory's porch."},
        {'id': 'chest:golem_cache', 'room': 'room:air', 'at': at('golem_heights', 128, 1280), 'kind': 'ch3',
         'facing': 's', 'treasure_level': 4, 'random_items': 3, 'gold': 500,
         'notes': "A cache at the Cloud Golems' feet."},
        {'id': 'chest:lantern', 'room': 'room:air', 'at': at('lantern_cloud', 256, -640), 'kind': 'ch1', 'facing': 'n',
         'treasure_level': 3, 'random_items': 2, 'gold': 250, 'notes': 'An old chest among the lanterns.'},
    ]


def objects():
    return {
        'format': 1,
        'start': {'room': 'room:air', 'at': WITCH_ARRIVAL, 'facing': 'n',
                  'notes': ("The head of the Witch Clouds' stair: XD-04's cloud stair arrives here (the map's "
                            'start).')},
        'sounds': [
            {'id': 'sound:wind_east', 'room': 'room:air', 'at': at('witch_landing', 0, 0), 'height': 256,
             'sound': 'whistling wind', 'radius': 9000, 'inner_radius': 3000, 'volume': 0.35},
            {'id': 'sound:wind_middle', 'room': 'room:air', 'at': at('half_way', 0, 0), 'height': 256,
             'sound': 'whistling wind', 'radius': 7000, 'inner_radius': 2500, 'volume': 0.45},
            {'id': 'sound:wind_west', 'room': 'room:air', 'at': at('observatory_isle', 0, 0), 'height': 256,
             'sound': 'whistling wind', 'radius': 9000, 'inner_radius': 3000, 'volume': 0.35},
            {'id': 'sound:wind_high', 'room': 'room:air', 'at': at('queens_eyrie', 0, 0), 'height': 256,
             'sound': 'whistling wind', 'radius': 6000, 'inner_radius': 2000, 'volume': 0.35},
            # AU (2026-11-20, devdocs/xeen/AUDIO.md): the open-air bed over the middle, gusts with a wait beside the
            # shipped wind at both ends
            {'id': 'sound:sky_bed', 'room': 'room:air', 'at': at('half_way', 0, 0), 'height': 256,
             'sound': 'xeen_amb_sky', 'radius': 14000, 'inner_radius': 7000, 'volume': 0.4, 'pan': False},
            {'id': 'sound:gust_east', 'room': 'room:air', 'at': at('witch_landing', 0, 0), 'height': 384,
             'sound': 'xeen_sky_gust', 'radius': 7000, 'inner_radius': 2500, 'volume': 0.5, 'wait': [6, 14]},
            {'id': 'sound:gust_west', 'room': 'room:air', 'at': at('observatory_isle', 0, 0), 'height': 384,
             'sound': 'xeen_sky_gust', 'radius': 7000, 'inner_radius': 2500, 'volume': 0.5, 'wait': [6, 14]},
            {'id': 'sound:bells', 'room': 'room:air', 'at': at('rhyme_garden', 0, 0), 'height': 160,
             'sound': '7chimes', 'radius': 2400, 'inner_radius': 900, 'volume': 0.5, 'loop': False,
             'wait': [4, 12], 'notes': 'The wind bells on their posts.'},
        ],
        'lights': [
            {'id': f'light:lantern_{k + 1}', 'room': 'room:air', 'at': at('lantern_cloud', dx, dy + 24),
             'height': 192, 'radius': 900, 'color': [255, 200, 120],
             'pulse': {'intensity': [0.8, 1], 'frequency': 0.6, 'phase': 0.25 * k}}
            for k, (dx, dy) in enumerate(((-768, 384), (512, 640), (0, -512), (896, -384)))
        ],
        'chests': chests(),
        'monsters': monsters(),
        'decorations': decorations(),
        'notes': ('X8 L4 objects (generated by output/studio_cal/x8/tools/gen_objects.py). 60 monsters placed (no '
                  'spawn markers); four chests; the statues and nests\' props; lanterns and wind.'),
    }


RHYMES = {
    1: ('A message at the base of the statue reads:  Golem, Terror, and Yak it\'s told have credits for King to '
        'hold.', 'xeen/aaze0025:1'),
    2: ('A message at the base of the statue reads:  The Clerics of Yak you must outwit Taxman then must have his '
        'bit.', 'xeen/aaze0025:2'),
    3: ('A message at the base of the statue reads:  Conquer terror and then you\'ll see Illusion holds Magic\'s '
        'key.', 'xeen/aaze0025:4'),
}


def wiring():
    ev = []
    ev.append({'id': 'evt:arrive', 'preset': 'text', 'trigger': 'load', 'once': True,
               'text': 'The cloud holds under your feet like stone. Far below, through the gaps, lies the land.',
               'notes': 'First arrival.'})
    ev.append({'id': 'evt:fall_check', 'preset': 'script', 'trigger': 'timer', 'every': 1,
               'lua': fall_lua(True),
               'notes': ('set:fall (D-6.4): a party under -1,000 has fallen off the clouds; it lands by zone '
                         'through A3\'s Xeen.skyFall (X1 850 over the ground, Lake Darzog at the surface).')})
    ev.append({'id': 'evt:fall_floor', 'preset': 'script', 'trigger': 'step', 'source': 'room:air',
               'lua': fall_lua(False),
               'notes': 'The safety floor at -6,000: a fall the one-second check missed lands the same way.'})
    for k in (1, 2, 3):
        ev.append({
            'id': f'evt:nest_{k}', 'preset': 'script', 'source': f'platform:nest_{k}', 'title': 'Harpy Nest',
            'effects': [{'hide': f'platform:nest_{k}'}, {'passable': f'platform:nest_{k}'},
                        {'lua': f'XeenQuests.hook("x8-sky.nest_{k}")'}],
            'notes': f'poi:harpy_nests: a click burns the nest (F47, the player\'s pins 2026-11-24: no Yes/No '
                     f'for a quest goal; the source asked, xeen/aaze0025:5); A3\'s hook x8-sky.nest_{k} (500 XP).'})
    ev.append({'id': 'evt:explorer', 'preset': 'script', 'source': 'deco:explorer_statue', 'title': 'Statue',
               'effects': [{'lua': 'XeenQuests.hook("x8-sky.explorer_statue")'}],
               'notes': ('poi:explorer_statue: A3\'s hook (Super Explorer, +2 Speed; "I dub all who find me Super '
                         'Explorer", xeen/aaze0025:7; "The statue is silent.", :6).')})
    for k, (text, ref) in RHYMES.items():
        ev.append({'id': f'evt:rhyme_{k}', 'preset': 'script', 'source': f'deco:rhyme_{k}', 'title': 'Statue',
                   'effects': [{'lua': 'if XeenQuests.hook("xd07.runes") then evt.SimpleMessage(%s) end'
                                       % json.dumps(text)}],
                   'notes': f'poi:rhyme_statues: the source\'s rhyme, verbatim ({ref}), shown only when A3\'s '
                            f'xd07.runes returns true (the Linguist gate, 2026-11-21).'})
    for k in (1, 2):
        ev.append({
            'id': f'evt:offering_{k}', 'preset': 'script', 'source': f'deco:offering_{k}', 'title': 'Offering',
            'condition': {'qbit': 110047, 'map_var': {'name': f'offering_{k}', 'equals': 0}},
            'effects': [{'set': {'var': {'map_var': f'offering_{k}'}, 'value': 1}}, {'give_item': {'level': 3}},
                        {'text': 'The statue\'s open hands hold a gift for a Crusader.'}],
            'else_effects': [{'lua': (
                'if IsQBitSet(QBit(110047)) then\n'
                '    evt.StatusText("The statue\'s hands are empty.")\n'
                'else\n'
                '    evt.DamagePlayer(Players.All, const.Damage.Air, 30)\n'
                '    evt.SimpleMessage("A gust of wind strikes you from the statue\'s hands. It is kept for Crusaders.")\n'
                'end')}],
            'notes': ('poi:offering_statues (the source\'s "Offering", xeen/aaze0025:9): a Crusader party (M4 done, '
                      '110047) is given an item of treasure level 3, once each statue; anyone else is struck.')})
    ev.append({'id': 'evt:telescope', 'preset': 'script', 'source': 'platform:telescope', 'title': 'Telescope',
               'effects': [{'message': ('Through the brass telescope the land lies small and clear far below: the '
                                        'lagoon to the west with the Tower of High Magic on its shore, Lake Darzog '
                                        'under the long bridge, and east, past Vertigo, the crooked Witch Tower.')}],
               'notes': 'poi:observatory: the sorcerer\'s telescope (our words).'})
    for c in ('hoard', 'star_charts', 'golem_cache', 'lantern'):
        ev.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}'})
    return {'format': 0, 'variables': ['offering_1', 'offering_2'], 'events': ev}


def atmosphere():
    return {
        'format': 0,
        'open_sky': {'mode': 'open', 'sky_texture': 'xeencloud', 'view': 'outdoor'},
        'daylight': {'ambient_rgb': [110, 112, 125], 'sun_rgb': [255, 248, 232],
                     'night_scale_rgb': [134, 143, 168], 'sun_gain': 3},
        'notes': ('Sky xeencloud (xeen_cloud_sea: below_horizon sky, high sun), an outdoor view; no weather (the '
                  'islands are above the rain); daylight on the open air.'),
    }


def write(name, data):
    with open(L4 / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    write('objects.yml', objects())
    write('wiring.yml', wiring())
    write('atmosphere.yml', atmosphere())
    print('arrivals: witch', WITCH_ARRIVAL, 'high magic', MAGIC_ARRIVAL)
    print('monsters', len(objects()['monsters']))


def inside(poly, p):
    x, y = p
    c = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def check():
    o = objects()
    things = [(m['id'], m['at']) for m in o['monsters']] + [(c['id'], c['at']) for c in o['chests']] + \
        [(d['id'], d['at']) for d in o['decorations']] + [('start', o['start']['at']),
                                                          ('magic_arrival', MAGIC_ARRIVAL)]
    for tid, p in things:
        hits = [k for k, poly in gen.OUTLINES.items() if inside(poly, p)]
        if not hits:
            print('NOT ON AN ISLAND:', tid, p)
            continue
        poly = gen.OUTLINES[hits[0]]
        dmin = min(math.hypot(p[0] - x, p[1] - y) for x, y in poly)
        if dmin < 300:
            print('near a rim:', tid, p, int(dmin))


if __name__ == '__main__':
    check()
