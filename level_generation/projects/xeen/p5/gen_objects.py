#!/usr/bin/env python3
"""P5: writes L4 objects.yml, wiring.yml (with the cinematic `unification`) and atmosphere.yml (A5 sub-agent
`agent:a5-p5`, 2026-11-21), after X9's gen_objects.py. Positions from gen.py and design.py; hooks by name from A3
(data_tables/quest_hooks.yml: m42.*), their hover texts from A3's quest file (source/quests/m42.yml).

Switches (each flips by itself when its blocker lands; see the L4 NOTES "Switches"):
- FD03: the stair house's door leads to FD-03's entrance:p5_stair once xeen_fd03.blv is installed and its studio.yml
  names that entrance (or P5_FD03_LIVE=1); until then it is sealed (a short status line, no move).
- FIGURES: the Pharaoh, Roland and the wedding Kalindra are placed once their monster_data rows and actors.yml
  bindings exist (P5_FIGURES=0 leaves them out).
- gen.DECO: S's Cube, Scepter, stone hands, cake and bench decorations, each once its decoration row exists.
"""
import math
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402
import gen  # noqa: E402

L4 = gen.BRIEF / 'L4'
WORLD = gen.WORLD
PHARAOH, ROLAND, KALINDRA = 11919, 11920, 11921
M42_DONE = 111840
FIGURE_GROUP, COUPLE_GROUP = 50, 51

# ------------------------------------------------------------------------------------------------ switches
FD03_MAP = WORLD / 'maps/xeen_fd03.blv'
FD03_STUDIO = WORLD / 'maps/xeen_fd03.studio.yml'


def fd03_live():
    if os.environ.get('P5_FD03_LIVE') == '1':
        return True
    if not (FD03_MAP.exists() and FD03_STUDIO.exists()):
        return False
    return 'entrance:p5_stair' in FD03_STUDIO.read_text()


FD03 = fd03_live()


def figures_ready():
    if os.environ.get('P5_FIGURES') == '0':
        return False
    rows = (WORLD / 'data_tables/monster_data.txt').read_text()
    binds = (WORLD / 'models/actors.yml').read_text()
    names = {PHARAOH: 'Xeen Dragon Pharaoh', ROLAND: 'Xeen Prince Roland', KALINDRA: 'Xeen Queen Kalindra Wedding'}
    return all(re.search(rf'^{m}\t', rows, re.M) and f'descriptor: {n}\n' in binds for m, n in names.items())


FIGURES = figures_ready()
DECO = gen.DECO

HOOKS = yaml.safe_load(open(WORLD / 'data_tables/quest_hooks.yml'))
M42 = yaml.safe_load(open(WORLD / 'source/quests/m42.yml'))['hooks']
USED = set()


def hook(name):
    assert name in HOOKS, f'A3 has no hook {name}'
    USED.add(name)
    return f'XeenQuests.hook("{name}")'


def hook_text(name):
    """A3's text of a hook (for a hover title that must equal the click's line)."""
    return M42[name.split('.', 1)[1]]['text']


BOARD_HOOK = {
    'poi:board_nwc': 'm42.board_new_world_computing', 'poi:board_kings_bounty': 'm42.board_kings_bounty',
    'poi:board_inherit': 'm42.board_inherit_the_earth', 'poi:board_empire': 'm42.board_empire_deluxe',
    'poi:board_spaceward': 'm42.board_spaceward_ho', 'poi:board_planets': 'm42.board_planets_edge',
    'poi:board_vegas': 'm42.board_vegas_games', 'poi:board_tunnels': 'm42.board_tunnels_and_trolls',
    'poi:board_nuclear': 'm42.board_nuclear_war', 'poi:board_mm': 'm42.board_might_and_magic',
}

PLACE = gen.PLACE
ARRIVAL = D.ARRIVAL
GIFT = (-576, 1352)          # against the pavilion's back wall (y 1464), clear of the couple (y 960) and its mouth
SHRINE_Z = gen.floor_of('room:shrine')


def at(pid):
    x, y = PLACE[pid]['at']
    return [int(x), int(y)]


# ------------------------------------------------------------------------------------------------ objects

def monsters():
    if not FIGURES:
        return []
    return [
        {'id': 'monster:pharaoh', 'room': 'room:air', 'monster': PHARAOH, 'at': at('npc:pharaoh'), 'facing': 270,
         'hostile': False, 'immobile': True, 'group': FIGURE_GROUP,
         'notes': ("The Dragon Pharaoh (11919: peaceful, placed-only, NoArena, uncounted) behind the dais, facing the "
                   "causeway (D-56 3, Q5); unkillable by evt:figures_load. The shrine is the click.")},
        {'id': 'monster:roland', 'room': 'room:air', 'monster': ROLAND, 'at': at('npc:roland'), 'facing': 270,
         'floor_height': SHRINE_Z,   # the pavilion's floor (the default, the highest, is its roof: 1,048)
         'hostile': False, 'immobile': True, 'group': COUPLE_GROUP, 'hidden': True, 'npc': 4405,
         'notes': ("Prince Roland (11920) under the pavilion, hidden until state:wedding (D-56 Q6); NPC 4405, so his "
                   "m42 topic 'The wedding' shows when he is clicked.")},
        {'id': 'monster:kalindra', 'room': 'room:air', 'monster': KALINDRA, 'at': at('npc:kalindra'), 'facing': 270,
         'floor_height': SHRINE_Z,   # the pavilion's floor (the default, the highest, is its roof: 1,048)
         'hostile': False, 'immobile': True, 'group': COUPLE_GROUP, 'hidden': True, 'npc': 5001,
         'notes': ("Queen Kalindra in her wedding look (11921, not 11918) beside him (D-56 3); NPC 5001, so her m42 "
                   "topic 'One world' shows when she is clicked.")},
    ]


def decorations():
    d = []
    # lane S (2026-11-21 06:3x): the hands, cake and bench take yaw_offset -90, so `facing` is the way they look
    # (270 = south, toward the party); the Cube and the Scepter stand at their hand's own x/y on the floor, facing 0
    # (their bindings raise them 394 and 398 onto the palms).
    sx, sy = gen.SHRINE
    hand = {1: [sx - 384, sy + 64], 2: [sx + 384, sy + 64]}
    if 'cube' in DECO:
        d.append({'id': 'deco:cube', 'room': 'room:air', 'decoration': DECO['cube'], 'at': hand[1], 'facing': 0,
                  'hidden': True, 'notes': 'The Cube of Power in the west hand (D-56 4), shown by the cinematic.'})
    if 'scepter' in DECO:
        d.append({'id': 'deco:scepter', 'room': 'room:air', 'decoration': DECO['scepter'], 'at': hand[2], 'facing': 0,
                  'hidden': True, 'notes': "Xeen's Scepter in the east hand (D-56 4), shown by the cinematic."})
    if 'hands' in DECO:
        for k in (1, 2):
            d.append({'id': f'deco:hand_{k}', 'room': 'room:air', 'decoration': DECO['hands'],
                      'at': hand[k], 'facing': 270})
    if 'cake' in DECO:
        # floor_height: the pavilion's floor on the shrine cloud (the default, the highest floor, is the roof's top)
        d.append({'id': 'deco:cake', 'room': 'room:air', 'decoration': DECO['cake'], 'at': at('landmark:cake'),
                  'floor_height': SHRINE_Z, 'hidden': True, 'notes': 'A cake on a table in the pavilion (state:wedding).'})
    if 'bench' in DECO:
        for h in gen.HUTS:
            p = PLACE[h]
            phi = math.radians(gen.COMPASS[p['face']])
            x, y = gen.frame(p['at'], phi, 0, -176)
            d.append({'id': f'deco:{gen.key(h)}_bench', 'room': 'room:air', 'decoration': DECO['bench'],
                      'at': [int(x), int(y)], 'floor_height': gen.floor_of(p['space']),   # not on the hut's roof
                      'facing': gen.COMPASS[p['face']]})
    return d


def chests():
    # merge point 25's hidden chest (`hidden: true`, `show: chest:gift`, kept by map state) replaces the sunk mover
    # on the shrine's cloud (without floor_height the build takes the highest floor there: the pavilion's roof)
    return [{'id': 'chest:gift', 'room': 'room:air', 'at': list(GIFT), 'floor_height': SHRINE_Z, 'kind': 'ch3',
             'hidden': True,
             'treasure_level': 6, 'random_items': 3, 'gold': 2000,
             'notes': "The wedding gift (treasure 6, D-56 Q7), against the pavilion's back, shown with state:wedding."}]


SOUNDS = [
    {'id': 'sound:sky_bed', 'at': [0, 0], 'height': 512, 'sound': 'xeen_amb_sky', 'radius': 16000,
     'inner_radius': 11000, 'volume': 0.4, 'pan': False},
    {'id': 'sound:gust_east', 'at': [4352, -1792], 'height': 512, 'sound': 'xeen_sky_gust', 'radius': 7000,
     'inner_radius': 2500, 'volume': 0.5, 'wait': [6, 14]},
    {'id': 'sound:gust_west', 'at': [-4352, 1792], 'height': 512, 'sound': 'xeen_sky_gust', 'radius': 7000,
     'inner_radius': 2500, 'volume': 0.5, 'wait': [6, 14]},
]


def sounds():
    """AU's sky-map wind (X8's and X9's bed, D-48 `pan: false`) and two gusts; AU's own P5 list replaces this."""
    return [dict(s, room='room:air') for s in SOUNDS]


def objects():
    o = {
        'format': 1,
        'start': {'room': 'room:air', 'at': list(ARRIVAL), 'facing': 'n',
                  'notes': "Out of the stair house's door (entrance:fd03_roof, the map's start), facing north."},
        'arrivals': [
            {'entrance': 'entrance:fd03_roof', 'room': 'room:air', 'at': list(ARRIVAL), 'facing': 'n',
             'notes': "FD-03's roof stair (A7, after M41's seal): out of the stair house, facing north (512)."},
        ],
        'sounds': sounds(),
        'chests': chests(),
        'decorations': decorations(),
        'notes': ('P5 L4 objects (generated by output/studio_cal/p5/tools/gen_objects.py): no monsters but the three '
                  'peaceful figures (FIGURES), the wedding gift on its sunk stand, S\'s decorations once they exist '
                  '(gen.DECO), the wind. No lights.'),
    }
    m = monsters()
    if m:
        o['monsters'] = m
    if not o['decorations']:
        del o['decorations']
    return o


# ------------------------------------------------------------------------------------------------ wiring

FALL_LUA = 'local x, y, z = evt.GetPartyPosition()\n{guard}Xeen.skyFallTo("p5")'


def fall_lua(guard):
    return FALL_LUA.format(guard='if z > -1000 then return end\n' if guard else '')


SEALED = 'The stair house door is shut fast. (Not open yet.)'


def wedding_show():
    """state:wedding shown: the pavilion and the disc drawn and solid, the couple shown, the gift raised, S's
    decorations shown. The roof stays passable: the game stands a placed monster on the highest solid top over it, and
    a solid roof put the couple on it (A5 s17, a visible run); nobody can reach the roof."""
    eff = []
    for pid in gen.pavilion_ids() + ['platform:disc']:
        eff += [{'show': pid}] + ([] if pid == 'platform:pavilion_roof' else [{'solid': pid}])
    if FIGURES:
        eff.append({'show_actors': COUPLE_GROUP})
    for k in ('cube', 'scepter', 'cake'):
        if k in DECO:
            eff.append({'show': f'deco:{k}'})
    eff.append({'show': 'chest:gift'})
    return eff


def wedding_hide():
    eff = []
    for pid in gen.pavilion_ids() + ['platform:disc']:
        eff += [{'hide': pid}, {'passable': pid}]
    return eff


def wiring():
    ev = []
    ev.append({'id': 'evt:fall_check', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'lua': fall_lua(True),
               'notes': ("set:fall: a party under -1,000 has fallen off the clouds; A3's Xeen.skyFallTo('p5') sets it "
                         "down on X5's entrance:p5_fall on Darkstone's rock, with falling damage (D-56 Q3).")})
    ev.append({'id': 'evt:fall_floor', 'preset': 'script', 'trigger': 'step', 'source': 'room:air', 'lua': fall_lua(False),
               'notes': 'The safety floor at -6,000: a fall the one-second check missed lands the same way.'})
    # the way down (D-56 Q10): the exit word through the game's leave window, sealed until FD-03 is installed
    door = {'id': 'evt:stair_door', 'preset': 'script', 'source': 'platform:stair_door', 'title': 'Darkstone Tower',
            'notes': ("The stair house's door: down into FD-03's entrance:p5_stair, meaning 'Descend into Darkstone "
                      "Tower?' (aazex129:14)" + ('.' if FD03 else '; sealed until xeen_fd03.blv is installed.'))}
    if FD03:
        door['effects'] = [{'exit': 'door:fd03'}]
    else:
        door['effects'] = [{'text': SEALED}]
    ev.append(door)
    ev.append({'id': 'evt:pharaoh_note', 'preset': 'script', 'source': 'platform:note_board', 'title': 'A message',
               'effects': [{'lua': hook('m42.pharaoh_note')}], 'notes': "A3's m42.pharaoh_note (aazex129:15)."})
    for pid, h in BOARD_HOOK.items():
        k = gen.key(pid)
        for src in (f'platform:{k}', f'platform:{k}_back'):
            ev.append({'id': f'evt:{k}' + ('_back' if src.endswith('_back') else ''), 'preset': 'script',
                       'source': src, 'title': hook_text(h), 'effects': [{'lua': hook(h)}],
                       'notes': f"A3's {h}: hover and click give the board's name."})
    for h in gen.HUTS:
        k = gen.key(h)
        for part in ('sign', 'sign_back', 'back'):
            ev.append({'id': f'evt:{k}_{part}', 'preset': 'script', 'source': f'platform:{k}_{part}',
                       'title': hook_text('m42.rest_stop'), 'effects': [{'lua': hook('m42.rest_stop')}],
                       'notes': "A3's m42.rest_stop (aazex129:0)."})
    ev.append({'id': 'evt:observatory', 'preset': 'script', 'source': 'platform:observatory_door',
               'title': 'Observatory', 'effects': [{'lua': hook('m42.observatory')}],
               'notes': "A3's m42.observatory: 'The observatory is closed.' (aazex129:11); the door never opens."})
    ev.append({'id': 'evt:shrine', 'preset': 'script', 'source': 'platform:dais', 'title': "The Pharaoh's shrine",
               'effects': [{'lua': hook('m42.shrine')}],
               'notes': ("A3's m42.shrine: true takes the Cube and the Scepter, sets m42.done, gives the award and "
                         "plays `unification` with A3's global done event 42149 (m42.ceremony, the text once); the map "
                         "shows nothing else (D-56 5).")})
    ev.append({'id': 'evt:disc', 'preset': 'script', 'source': 'platform:disc', 'title': 'A cloud-stone disc',
               'condition': {'lua': hook('m42.disc')},
               'effects': [{'teleport': {'to': list(ARRIVAL) + [0], 'direction': 90}}],
               'notes': "D-56 7: A3's m42.disc line, then to entrance:fd03_roof inside the map, facing north."})
    ev.append({'id': 'evt:wedding_hide', 'preset': 'script', 'trigger': 'load', 'condition': {'not': {'qbit': 'm42_done'}},
               'effects': wedding_hide(),
               'notes': 'Before m42.done the pavilion and the disc are not there (hidden and passable).'})
    ev.append({'id': 'evt:wedding_load', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm42_done'},
               'effects': wedding_show(),
               'notes': 'state:wedding on every visit after m42.done (D-56 5): the same as the cinematic\'s cue.'})
    ev.append({'id': 'evt:wedding_show', 'preset': 'script', 'trigger': 'call',
               'effects': wedding_show(),
               'notes': "The cinematic's cue at the fade (a gameplay step: it runs also on a skip)."})
    if 'cube' in DECO or 'scepter' in DECO:
        ev.append({'id': 'evt:hands_filled', 'preset': 'script', 'trigger': 'call',
                   'effects': [{'show': f'deco:{k}'} for k in ('cube', 'scepter') if k in DECO],
                   'notes': "The cinematic's first cue: the Cube and the Scepter in the hands."})
    if FIGURES:
        ev.append({'id': 'evt:figures_load', 'preset': 'script', 'trigger': 'load',
                   'lua': '\n'.join(f'evt.SetMm9ActorCanReceiveDamage(ActorIndex("{m}"), false)'
                                    for m in ('monster:pharaoh', 'monster:roland', 'monster:kalindra')),
                   'notes': 'The three figures are unkillable (D-56 3; as D-51 and D-52).'})
    ev.append({'id': 'evt:chest_gift', 'preset': 'chest', 'source': 'chest:gift',
               'notes': 'The wedding gift: unseen in the cloud until state:wedding raises it.'})
    return {'format': 0, 'variables': [], 'events': ev, 'cinematics': [cinematic()]}


# ------------------------------------------------------------------------------------------------ the cinematic

FADE_COLOUR = [255, 255, 255]   # D-56 6: the fade to white and back (merge point 24's fade `color`); None = black


def fade(at, way, seconds, white=False):
    c = {'at': at, 'fade': way, 'seconds': seconds}
    if white and FADE_COLOUR:
        c['color'] = list(FADE_COLOUR)
    return c


def cinematic():
    """`unification` (D-56 5, the L1 plan's set:unification): about 35 s, skippable; every gameplay step an event cue.
    1 close on the dais (the Cube and the Scepter shown, the Pharaoh's voiced line and A3's subtitle); 2 a rising
    pull-back over the ring; 3 up into the sky and a fade to white, state:wedding shown in the
    fade; 4 fade in on the pavilion, the Pharaoh turning to the couple; 5 the party's view."""
    sx, sy = gen.SHRINE
    z = SHRINE_Z
    px, py = gen.PAV
    shrine = M42['shrine']
    cues = [fade(0, 'in', 1.0)]
    if 'cube' in DECO or 'scepter' in DECO:
        cues.append({'at': 0.5, 'event': 'evt:hands_filled'})
    cues += [{'at': 1.5, 'sound': shrine['cinematic_sound']},
             {'at': 1.5, 'subtitle': shrine['cinematic_subtitles'][0], 'seconds': 5}]
    # AU session 5 (AUDIO.md "The lines to paste"): the four sleepers answer in shot 2 (8-18 s), four far bells, the
    # last the deepest; the wedding fanfare as the pavilion fades in (shot 4 from 24 s)
    cues += [{'at': 9.5 + 2 * i, 'sound': 'xeen_chime_%d' % (i + 1)} for i in range(4)]
    cues += [fade(19.5, 'out', 2.5, True), {'at': 22.5, 'event': 'evt:wedding_show'}, fade(24, 'in', 2, True),
             {'at': 24.5, 'sound': 'xeen_wedding_fanfare'}]
    if FIGURES:
        cues.append({'at': 25, 'monster': 'monster:pharaoh', 'action': 'face', 'look_at': [px, py, z + 120],
                     'seconds': 1.5})
    shots = [
        {'seconds': 8, 'at': [sx, sy - 1500, z + 360], 'look_at': [sx, sy + 200, z + 300], 'fov': 60,
         'easing': 'smooth', 'keys': [{'seconds': 8, 'at': [sx, sy - 1100, z + 300], 'look_at': [sx, sy + 200, z + 320]}]},
        {'seconds': 10, 'at': [sx, sy - 1800, z + 700], 'look_at': [0, 0, z + 200], 'fov': 70, 'easing': 'smooth',
         'keys': [{'seconds': 10, 'at': [600, -6400, 3200], 'look_at': [0, 0, z]}]},
        {'seconds': 6, 'at': [600, -6400, 3200], 'look_at': [0, 0, z], 'fov': 70, 'easing': 'smooth',
         'keys': [{'seconds': 6, 'at': [300, -3000, 5600], 'look_at': [0, 2000, 6000]}]},
        {'seconds': 8, 'at': [px + 700, py - 1500, z + 420], 'look_at': [px, py, z + 200], 'fov': 60, 'easing': 'smooth',
         'keys': [{'seconds': 8, 'at': [px + 300, py - 1200, z + 300], 'look_at': [px, py, z + 180]}]},
        {'seconds': 3, 'party': True},
    ]
    return {'id': 'cinematic:unification', 'skippable': True, 'shots': shots, 'cues': cues,
            'notes': ("D-56 5: the ending, about 35 s, played by A3's m42.shrine (evt.PlayCinematic('unification', "
                      "42149)). The fade into the sky and back on the pavilion is white (FADE_COLOUR); the first "
                      "fade in is from black. AU's chimes (9.5-15.5 s) and "
                      "wedding fanfare (24.5 s).")}


def atmosphere():
    return {
        'format': 0,
        'open_sky': {'mode': 'open', 'sky_texture': 'xeencloud', 'view': 'outdoor', 'view_distance_scale': 1.5},
        'daylight': {'ambient_rgb': [110, 112, 125], 'sun_rgb': [255, 248, 232],
                     'night_scale_rgb': [134, 143, 168], 'sun_gain': 3},
        'notes': ("Sky xeencloud (xeen_cloud_sea: below_horizon sky) as every sky map (D-56 Q9); an outdoor view at "
                  "1.5 times the view distance so the far side of the ring reads; no weather; X9's daylight."),
    }


def write(name, data):
    L4.mkdir(parents=True, exist_ok=True)
    with open(L4 / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def all_polys():
    polys = dict(gen.POLYS)
    for b, poly, _ in gen.LOBES:
        polys[b + '_lobe'] = poly
    return polys


def check():
    """Every placed thing on a cloud, 256 or more inside its rim; every board leg on a cloud."""
    o = objects()
    polys = all_polys()
    things = [(m['id'], m['at']) for m in o.get('monsters', [])] + [(c['id'], c['at']) for c in o['chests']] + \
        [(d['id'], d['at']) for d in o.get('decorations', [])] + [(a['entrance'], a['at']) for a in o['arrivals']] + \
        [(s, gen.PLACE[s]['at']) for s in gen.HUTS] + [('disc', gen.DISC)]
    for pid in gen.BOARD_TEX:
        things += [(f'{pid} leg', leg) for leg in gen.board_legs(pid)]
    for k, (ox, oy) in enumerate(((-744, -488), (744, -488), (744, 488), (-744, 488))):
        things.append((f'pavilion post {k + 1}', (gen.PAV[0] + ox, gen.PAV[1] + oy)))
    bad = 0
    for tid, p in things:
        hits = [k for k, poly in polys.items() if G_inside(poly, p)]
        if not hits:
            print('NOT ON A CLOUD:', tid, p)
            bad += 1
            continue
        dmin = max(gen.rim_distance(polys[h], p) for h in hits)
        if dmin < (64 if ('leg' in tid or 'post' in tid) else 256):
            print('near a rim:', tid, [int(v) for v in p], int(dmin))
    return bad


def G_inside(poly, p):
    return gen.inside(poly, p)


if __name__ == '__main__':
    write('objects.yml', objects())
    write('wiring.yml', wiring())
    write('atmosphere.yml', atmosphere())
    print('figures', FIGURES, 'fd03', FD03, 'deco', sorted(DECO), 'hooks', len(USED))
    check()
