#!/usr/bin/env python3
"""X9: writes L4 objects.yml, wiring.yml and atmosphere.yml (A5 sub-agent, 2026-11-21). Positions from gen.py and
design.py; hooks by name from A3 (data_tables/quest_hooks.yml: m34.*, x9.*)."""
import math
import os
import random
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402
import gen  # noqa: E402
import geom as G  # noqa: E402

L4 = gen.BRIEF / 'L4'
WORLD = gen.ROOT / 'assets_dev/worlds/xeen'
ROC, GRIFFIN, GOLEM, SLICK = 11561, 11562, 11592, 11914
M35_DONE = 111707

# XD-19 (A7) is built but not installed: the gate leads into it once its map is installed and names entrance:x9_gate
# (or X9_XD19_LIVE=1), and is sealed after the m34.gate check until then (X7's places.live()).
XD19_MAP = WORLD / 'maps/xeen_xd19.blv'
XD19_STUDIO = WORLD / 'maps/xeen_xd19.studio.yml'


def xd19_arrival():
    """XD-19's entrance:x9_gate (x, y, z, facing) from its installed studio.yml, else None."""
    if os.environ.get('X9_XD19_LIVE') == '1':
        return (0, -4064, 0, 512)
    if not (XD19_MAP.exists() and XD19_STUDIO.exists()):
        return None
    m = re.search(r'name: "entrance:x9_gate", at: \[(-?\d+), (-?\d+), (-?\d+)\], facing: (\d+)', XD19_STUDIO.read_text())
    return tuple(int(v) for v in m.groups()) if m else None


XD19 = xd19_arrival()

# FD-04 (A7): the way down in the dragon-head rock leads to its entrance:x9_clouds once FD-04 is installed and names it
# (or X9_FD04_LIVE=1); sealed until then (D-57 Q36).
FD04_MAP = WORLD / 'maps/xeen_fd04.blv'
FD04_STUDIO = WORLD / 'maps/xeen_fd04.studio.yml'


def fd04_live():
    if os.environ.get('X9_FD04_LIVE') == '1':
        return True
    return FD04_MAP.exists() and FD04_STUDIO.exists() and 'entrance:x9_clouds' in FD04_STUDIO.read_text()


FD04 = fd04_live()
HOOKS = yaml.safe_load(open(WORLD / 'data_tables/quest_hooks.yml'))
USED = set()


def hook(name):
    assert name in HOOKS, f'A3 has no hook {name}'
    USED.add(name)
    return f'XeenQuests.hook("{name}")'


def has_hook(name):
    return name in HOOKS


# Q-F1 on the Dragon Clouds (D-57 Q36): A3's hooks by these names; an object whose hook is not written yet is placed
# but not clicked (its event is written when the hook appears).
QF1 = {'eye': 'q-f1.eye', 'well': 'q-f1.well',
       **{f'book_{t}': f'q-f1.runes_{t}' for t, _ in gen.QF1_BOOKS},
       **{f'ball_{t}': f'q-f1.ball_{t}' for t, _ in gen.QF1_BALLS},
       **{f'crystal_{k}': f'q-f1.crystal_{k}' for k, _, _ in gen.QF1_CRYSTALS}}
QF1_TITLES = {'eye': 'The Eye of the Dragon', 'well': 'Well of Fantastic Skill',
              **{f'book_{t}': 'Ancient Book of the Dragon' for t, _ in gen.QF1_BOOKS},
              **{f'ball_{t}': f'{t.capitalize()} of the Dragon' for t, _ in gen.QF1_BALLS},
              **{f'crystal_{k}': 'Dragon Power Crystal' for k, _, _ in gen.QF1_CRYSTALS}}
QF1_SOURCES = {'eye': 'deco:dragon_eye', 'well': 'platform:well_water',
               **{f'book_{t}': f'platform:book_{t}' for t, _ in gen.QF1_BOOKS},
               **{f'ball_{t}': f'deco:ball_{t}' for t, _ in gen.QF1_BALLS},
               **{f'crystal_{k}': f'deco:crystal_{k}' for k, _, _ in gen.QF1_CRYSTALS}}


def lua_str(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


# ------------------------------------------------------------------------------------------------ monsters

SPREAD = {2: [(-160, -96), (160, 96)], 3: [(0, 192), (-192, -128), (192, -128)]}


def monsters():
    out = []
    rnd = random.Random(9)
    names = {ROC: 'roc', GRIFFIN: 'griffin', GOLEM: 'golem'}
    count = {}
    for g, grp in enumerate(D.GROUPS):
        cx, cy = G.place_at(grp, gen.POLYS)
        a = rnd.uniform(0, 2 * math.pi)
        for dx, dy in SPREAD[grp['count']]:
            x = cx + dx * math.cos(a) - dy * math.sin(a)
            y = cy + dx * math.sin(a) + dy * math.cos(a)
            k = gen.key(grp['id'])
            count[k] = count.get(k, 0) + 1
            e = {'id': f'monster:{k}_{count[k]}', 'room': 'room:air', 'monster': grp['actor'],
                 'at': [int(round(x)), int(round(y))], 'facing': rnd.choice([0, 45, 90, 135, 180, 225, 270, 315]),
                 'hostile': True, 'group': 10 + g}
            if grp['actor'] == GOLEM:
                e['immobile'] = True
            out.append(e)
    # Slick the Gamemaster behind his prize stand (D-50 Q6; A2's 11914, S's binding): peaceful, placed, uncounted
    sx, sy = G.place_at(next(p for p in D.PLACES if p['id'] == 'landmark:slick'), gen.POLYS)
    out.append({'id': 'monster:slick', 'room': 'room:air', 'monster': SLICK, 'at': [int(sx), int(sy)], 'facing': 0,
                'hostile': False, 'immobile': True, 'group': 40,
                'notes': ('Slick the Gamemaster (11914: peaceful, NoArena, uncounted) behind his prize stand, facing '
                          'the causeway (D-50 Q6). The stand and the booths are the clicks.')})
    return out


# ------------------------------------------------------------------------------------------------ decorations

def decorations():
    d = []

    def add(did, deco, xy, **kw):
        e = {'id': f'deco:{did}', 'room': 'room:air', 'decoration': deco, 'at': [int(round(xy[0])), int(round(xy[1]))]}
        e.update(kw)
        d.append(e)

    facing_to = {'poi:statue_1': 270, 'poi:statue_2': 0, 'poi:statue_3': 270, 'poi:statue_4': 180}
    for k in range(1, 5):
        add(f'statue_{k}', '7dec54', gen.at(f'poi:statue_{k}'), facing=facing_to[f'poi:statue_{k}'])
    for k in range(1, 7):
        add(f'offering_{k}', 'sta1a', gen.at(f'poi:offering_{k}'))
    for tag in ('sw', 'se', 'a1', 'a2', 'a3'):
        x, y = gen.at(f'poi:nest_{tag}')
        add(f'nest_{tag}_bones', '7dec18', (x - 96, y + 64))
        add(f'nest_{tag}_skull', '7dec20', (x + 112, y - 80))
    a = D.SPACES[[s['id'] for s in D.SPACES].index('room:aviary')]['at']
    for k, (dx, dy) in enumerate(((-512, -256), (384, 896), (-1408, 256))):
        add(f'aviary_bones_{k + 1}', 'dec19', (a[0] + dx, a[1] + dy))
    # the Dragon Clouds (D-57 Q36): the Eye on its ledge, the crystal balls on their plinths, the power crystals
    add('dragon_eye', 'crystl0', gen.EYE_AT)
    for tag, xy in gen.QF1_BALLS:
        # MM8's air orb on its plinth (D-59); the orb's model sits 9 into its stand (z_offset -9): NOTES' exception
        add(f'ball_{tag}', 'dec57', xy, floor_height=gen.DRAGON['floor'] + 112, inside=f'platform:ball_{tag}_plinth')
    for k, xy, deco in gen.QF1_CRYSTALS:
        add(f'crystal_{k}', deco, xy)
    # Slick's Sure-Eye Tonic (D-70 Q1, A3's m34.tonic): a cask against the south end of the Accuracy booth's counter
    # (the counter runs north-south at x -3328, y 1024..2048; the shooting line is 448 west, the lane runs west to the
    # bullseye at y 1536, so the cask is off the lane and off the line). No crate model exists: MM7's cask (7dec21).
    add('tonic_crate', '7dec21', TONIC_AT)
    return d


def tonic_at():
    """The cask's point: 64 beyond the counter's south end (the booth stands 384 behind its point, facing west)."""
    x, y = gen.at('poi:accuracy_game')
    return (x + 384, y - 512 - 64)


TONIC_AT = tonic_at()


def chests():
    spec = [('hollow', 'poi:chest_hollow', 'ch2', 'n', 1200, "The hollow under the south-west nest: the rocs' stolen goods."),
            ('cache', 'poi:chest_cache', 'ch1', 'e', 900, "An old traveller's cache on the north-west isle."),
            ('pack', 'poi:chest_pack', 'ch1', 'w', 800, "A lost traveller's pack on the east horn."),
            # F3 (2026-11-21): a chest's `facing` is its long axis, the front 90 degrees anticlockwise: 'w' fronts south
            ('hoard', 'poi:chest_hoard', 'ch3', 'w', 1500, "The rocs' hoard: shiny things carried up from the land.")]
    return [{'id': f'chest:{c}', 'room': 'room:air', 'at': list(gen.at(pid)), 'kind': kind, 'facing': facing,
             'treasure_level': 5, 'random_items': 3, 'gold': gold, 'notes': notes}
            for c, pid, kind, facing, gold, notes in spec]


AU_BEDS = gen.ROOT / 'level_generation/projects/xeen/common/beds/x9.yml'


def sounds():
    """AU's X9 list (session 4, D-48: the beds `pan: false`), in the map's one room."""
    out = []
    for e in yaml.safe_load(open(AU_BEDS))['sounds']:
        e = dict(e)
        e['room'] = 'room:air'
        out.append(e)
    return out


def objects():
    return {
        'format': 1,
        'start': {'room': 'room:air', 'at': list(gen.ARRIVAL), 'facing': 'n',
                  'notes': "The top step of XD-12's cloud stair (entrance:xd12_roof, the map's start)."},
        'arrivals': [
            {'entrance': 'entrance:xd12_roof', 'room': 'room:air', 'at': list(gen.ARRIVAL), 'facing': 'n',
             'notes': "XD-12's cloud stair (A8's exit:clouds_of_xeen): the top step, facing north."},
            {'entrance': 'entrance:xd19_gate', 'room': 'room:air', 'at': list(gen.RETURN), 'facing': 's',
             'notes': "XD-19's way out and the scepter cinematic's leave: before the gate, facing south (1536)."},
            {'entrance': 'entrance:fd04_roof', 'room': 'room:air', 'at': [int(v) for v in gen.FD04_ARRIVAL],
             'facing': 'n', 'notes': ("FD-04's roof stair onto the Dragon Clouds (Q-F1, D-57 Q36): on the cloud about "
                                     "900 south of the snout, facing north toward the dragon-head rock.")},
        ],
        'sounds': sounds(),
        'chests': chests(),
        'monsters': monsters(),
        'decorations': decorations(),
        'notes': ('X9 L4 objects (generated by output/studio_cal/x9/tools/gen_objects.py): 50 monsters placed (no '
                  'spawn markers) and Slick (peaceful, uncounted); four chests; statues, offering statues and the '
                  "nests' bones; the wind. No lights."),
    }


# ------------------------------------------------------------------------------------------------ wiring

FALL_LUA = 'local x, y, z = evt.GetPartyPosition()\n{guard}Xeen.skyFallTo("x9")'


def fall_lua(guard):
    return FALL_LUA.format(guard='if z > -1000 then return end\n' if guard else '')


SEALED = 'The great black doors do not move. (Not open yet.)'
FD04_SEALED = 'The door in the rock does not move. (Not open yet.)'
EYE_MESSAGE = '"Look into the eye of the Dragon and despair"\n"Answer correctly or perish!"'   # dark/aazex128:1
EYE_ASK = '"What is the secret of the Dragon?"'                                               # dark/aazex128:2


def gate_effects():
    """The exit preset's leave (D-50 change 3, D-24) on the two leaf blocks: A3's m34.gate decides (its fail text
    without a doll); with the doll, the studio's `{exit: door:xd19}` (merge point 23: the exit preset's own move, the
    game's leave window, whose meaning is 'Enter Castle Xeen?'). Sealed until XD-19 is installed."""
    if XD19:
        return [{'lua': f'if not {hook("m34.gate")} then return end'}, {'exit': 'door:xd19'}]
    return [{'lua': f'if {hook("m34.gate")} then\n    evt.SimpleMessage({lua_str(SEALED)})\nend'}]


BOOTHS = [('might', 'Might'), ('speed', 'Speed'), ('endurance', 'Endurance'), ('accuracy', 'Accuracy')]
NESTS = ['sw', 'se', 'a1', 'a2', 'a3']
SIGNS = [('danger_sign', 'x9.sign_danger'), ('nine_north', 'x9.sign_nine_north'),
         ('xeendom_sign', 'x9.sign_xeendom'), ('aviary_sign', 'x9.sign_aviary')]


def wiring():
    ev = []
    ev.append({'id': 'evt:arrive', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'once': True,
               'effects': [{'lua': hook('x9.arrival')}],
               'notes': "First arrival: A3's x9.arrival line (a one-second timer, once: a load event's window is not shown)."})
    ev.append({'id': 'evt:fall_check', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'lua': fall_lua(True),
               'notes': ("set:fall: a party under -1,000 has fallen off the clouds; A3's Xeen.skyFallTo('x9') sets it "
                         "down on X2's Darzog island at entrance:x9_fall with falling damage.")})
    ev.append({'id': 'evt:fall_floor', 'preset': 'script', 'trigger': 'step', 'source': 'room:air', 'lua': fall_lua(False),
               'notes': 'The safety floor at -6,000: a fall the one-second check missed lands the same way.'})
    for name, h in SIGNS:
        ev.append({'id': f'evt:{name}', 'preset': 'script', 'source': f'platform:{name}', 'title': 'Sign',
                   'effects': [{'lua': hook(h)}], 'notes': f"A3's {h} (the source's line, xeen/aaze0027)."})
    for k in range(1, 5):
        ev.append({'id': f'evt:statue_{k}', 'preset': 'script', 'source': f'deco:statue_{k}', 'title': 'Statue',
                   'effects': [{'lua': hook(f'm34.statue_{k}')}],
                   'notes': f"A3's m34.statue_{k}: the rhyme for a Linguist, else the runes line."})
    for k in range(1, 7):
        ev.append({'id': f'evt:offering_{k}', 'preset': 'script', 'source': f'deco:offering_{k}', 'title': 'Offering',
                   'effects': [{'lua': hook(f'x9.offering_{k}')}],
                   'notes': f"A3's x9.offering_{k}: an item of treasure level 5 for Crusaders, once; others struck."})
    for tag in NESTS:
        ev.append({
            'id': f'evt:nest_{tag}', 'preset': 'script', 'source': f'platform:nest_{tag}', 'title': 'Roc Nest',
            # D-72 item 3 (A5 s30): the source's question as one Yes/No prompt with buttons; Yes (step 1) burns the
            # nest, No and Escape leave it with a status line
            'effects': [{'lua': 'if continueStep ~= 1 then if continueStep == nil then AskChoiceWithAnswerSteps(eventId, '
                                '3, "Roc Nest.  Destroy?", {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}}) '
                                'else evt.StatusText("You leave the nest as it is.", 4) end return end'},
                        {'hide': f'platform:nest_{tag}'}, {'passable': f'platform:nest_{tag}'},
                        {'lua': hook(f'x9.nest_{tag}')}],
            'notes': (f"The source's question (xeen/aaze0027:0) as Yes/No buttons (D-72); A3's x9.nest_{tag} (2,000 "
                      "experience each, once).")})
        bit = HOOKS[f'x9.nest_{tag}']['sets'][f'nest_{tag}']
        ev.append({'id': f'evt:nest_{tag}_gone', 'preset': 'script', 'trigger': 'load',
                   'condition': {'qbit': f'nest_{tag}'},
                   'effects': [{'hide': f'platform:nest_{tag}'}, {'passable': f'platform:nest_{tag}'}],
                   'notes': f'A burnt nest stays gone (bit {bit}).'})
    for name, title in BOOTHS:
        ev.append({'id': f'evt:booth_{name}', 'preset': 'script', 'source': f'platform:booth_{name}',
                   'title': f'{title} booth', 'effects': [{'lua': hook(f'm34.{name}_game')}],
                   'notes': f"Slick's {title} game: A3's m34.{name}_game."})
    ev.append({'id': 'evt:tonic_crate', 'preset': 'script', 'source': 'deco:tonic_crate', 'title': 'Sure-Eye Tonic',
               'effects': [{'lua': hook('m34.tonic')}],
               'notes': ("Slick's free round (D-70 Q1): A3's m34.tonic gives two Accuracy Boosts (245, power 10) once "
                         'per game, then its else line.')})
    ev.append({'id': 'evt:prize_stand', 'preset': 'script', 'source': 'platform:prize_stand', 'title': 'Prize Stand',
               'effects': [{'lua': hook('m34.prize_stand')}],
               'notes': "Slick's prize stand: A3's m34.prize_stand (four dolls for the Lord Xeen doll)."})
    for side in ('l', 'r'):
        ev.append({'id': f'evt:gate_{side}', 'preset': 'script', 'source': f'platform:gate_leaf_{side}',
                   'title': 'Castle Xeen', 'condition': {'not': {'qbit': 'm35_done'}},
                   'effects': gate_effects(), 'else_effects': [{'lua': hook('x9.castle_gone')}],
                   'notes': ("Castle Xeen's gate (link:gate): A3's m34.gate, then the exit preset's leave into XD-19's "
                             "entrance:x9_gate" + ('' if XD19 else ' (sealed until XD-19 is installed)') + '.')})
    shell = gen.shell_ids()
    gone = []
    for pid in shell:
        gone += [{'hide': pid}, {'passable': pid}]
    ev.append({'id': 'evt:castle_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm35_done'},
               'effects': gone,
               'notes': ("state:castle_gone (D-47 Q14): on m35.done the shell (walls, frieze, lintel, towers, keep, "
                         "leaves) is hidden and passable; its cloud stays; link:gate is sealed.")})
    ev.append({'id': 'evt:castle_spot', 'preset': 'script', 'trigger': 'step', 'source': 'platform:gate_threshold',
               'condition': {'qbit': 'm35_done'}, 'effects': [{'lua': hook('x9.castle_gone')}],
               'notes': "After m35.done the gate's spot reads 'The great Castle Xeen recently stood here.' (aaze0027:44)."})
    for c in ('hollow', 'cache', 'pack', 'hoard'):
        ev.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}'})
    # the Dragon Clouds (D-57 Q36)
    ev.append({'id': 'evt:fd04_door', 'preset': 'script', 'source': 'platform:fd04_door', 'title': 'Dragon Tower',
               'effects': [{'exit': 'door:fd04'}] if FD04 else [{'lua': f'evt.SimpleMessage({lua_str(FD04_SEALED)})'}],
               'notes': ("The way down in the dragon-head rock: the exit preset's leave (its meaning 'Descend into "
                         "Dragon Tower?', dark/aazex128:0) to FD-04's entrance:x9_clouds"
                         + ('' if FD04 else ' (sealed until FD-04 is installed)') + '.')})
    for k, name in QF1.items():
        if not has_hook(name):
            continue
        if k == 'eye':
            # A3's q-f1.eye (D-57 Q36): the map shows the source's two lines and asks; 'Infinity' (any case; 'infinite'
            # too) calls the hook, any other answer q-f1.eye_wrong (event damage, never lethal; ask again). Once done
            # (its bit), a click calls the hook alone (its else line).
            ev.append({'id': 'evt:qf1_eye', 'preset': 'script', 'source': QF1_SOURCES[k], 'title': QF1_TITLES[k],
                       'condition': {'not': {'qbit': 'qf1_eye_done'}},
                       'question': {'message': EYE_MESSAGE, 'ask': EYE_ASK, 'answers': ['Infinity', 'Infinite'],
                                    'wrong_effects': [{'lua': hook('q-f1.eye_wrong')}]},
                       'effects': [{'lua': hook(name)}], 'else_effects': [{'lua': hook(name)}],
                       'notes': ("Q-F1's Eye of the Dragon (dark/aazex128:1-4): A3's q-f1.eye on 'Infinity', "
                                 'q-f1.eye_wrong on any other answer; once done its else line.')})
            continue
        ev.append({'id': f'evt:qf1_{k}', 'preset': 'script', 'source': QF1_SOURCES[k], 'title': QF1_TITLES[k],
                   'effects': [{'lua': hook(name)}], 'notes': f"Q-F1 on the Dragon Clouds: A3's {name} (D-57 Q36, D-59)."})
        if k == 'well':
            for side in ('s', 'n', 'w', 'e'):
                ev.append({'id': f'evt:qf1_well_curb_{side}', 'preset': 'script', 'source': f'platform:well_curb_{side}',
                           'title': QF1_TITLES[k], 'effects': [{'lua': hook(name)}],
                           'notes': f"The well's curb: the same drink, A3's {name} (D-59)."})
    return {'format': 0, 'events': ev}


def atmosphere():
    return {
        'format': 0,
        'open_sky': {'mode': 'open', 'sky_texture': 'xeencloud', 'view': 'outdoor', 'view_distance_scale': 2},
        'daylight': {'ambient_rgb': [110, 112, 125], 'sun_rgb': [255, 248, 232],
                     'night_scale_rgb': [134, 143, 168], 'sun_gain': 3},
        'notes': ('Sky xeencloud (xeen_cloud_sea: below_horizon sky), an outdoor view at twice the player\'s view '
                  'distance so that Castle Xeen reads from the brink 23,000 away (the signature); no weather (above '
                  'the rain); daylight on the open air (X8\'s block).'),
    }


def write(name, data):
    L4.mkdir(parents=True, exist_ok=True)
    with open(L4 / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def check():
    """Every placed thing on a cloud; walkers and chests 300 or more inside its rim."""
    o = objects()
    things = [(m['id'], m['at'], m['monster']) for m in o['monsters']] + \
        [(c['id'], c['at'], 'chest') for c in o['chests']] + [(d['id'], d['at'], 'deco') for d in o['decorations']] + \
        [(a['entrance'], a['at'], 'arrival') for a in o['arrivals']]
    bad = 0
    for tid, p, kind in things:
        hits = [k for k, poly in gen.POLYS.items() if gen.inside(poly, p)]
        if not hits:
            print('NOT ON A CLOUD:', tid, p)
            bad += 1
            continue
        dmin = min(gen.rim_distance(gen.POLYS[h], p) for h in hits)
        if dmin < 300 and kind not in (ROC, GRIFFIN):
            print('near a rim:', tid, p, int(dmin))
    return bad


if __name__ == '__main__':
    write('objects.yml', objects())
    write('wiring.yml', wiring())
    write('atmosphere.yml', atmosphere())
    print('monsters', len(objects()['monsters']), 'xd19', XD19 or 'sealed', 'fd04', 'live' if FD04 else 'sealed',
          'hooks', len(USED), 'q-f1 missing', [n for n in QF1.values() if not has_hook(n)])
    check()
