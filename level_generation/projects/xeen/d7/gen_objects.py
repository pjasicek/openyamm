#!/usr/bin/env python3
"""D7: writes L4 objects.yml, wiring.yml and atmosphere.yml (A6 sub-agent, sixteenth session, 2026-11-21), after X9's
and P5's gen_objects.py. Positions from gen.py and d7_design.py (with D-58); A3's hooks by name
(data_tables/quest_hooks.yml); a hook that does not exist yet leaves its thing placed but unwired (listed in the L4
NOTES as blocked; no hook or qbit of A3's is invented).

Switches (each flips by itself when its blocker lands):
- LIVE[...]: a door to a dungeon (DD-15's sky door, DD-17's roof hatch, DD-26's stair) leads there once the BLV is in
  assets_dev and its studio.yml lists the arrival (D4's dungeon_live); else a short sealed line.
- Q-D26's kill qbit (the Megadragon hidden on load once it is dead, D-3) once A3 writes it.
- D1's `entrance:d7_rope` read from xeen_d1.studio.yml, else the coordinates the lead gave.
"""
import math
import os
import random
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402

D = gen.D
G = gen.G
L4 = gen.BRIEF / 'L4'
WORLD = gen.WORLD
MAPS = WORLD / 'maps'

GRIFFIN, SKY_GOLEM, CLOUD_DRAGON, CLOUD_GOLEM, MEGADRAGON, SKY_BANDIT = 11562, 11594, 11650, 11592, 11654, 11116
WYRMFANG, ROOF_KEY = 12530, 12377
FLYERS = (GRIFFIN, CLOUD_DRAGON, MEGADRAGON)
MEGA_GROUP = 60
BANDIT_GROUP = {'north': 70, 'east': 71, 'south': 72, 'west': 73}

HOOKS = yaml.safe_load(open(WORLD / 'data_tables/quest_hooks.yml'))
USED = set()
BLOCKED = []          # (what, owner, why) for the NOTES


def hook(name):
    assert name in HOOKS, f'A3 has no hook {name}'
    USED.add(name)
    return f'XeenQuests.hook("{name}")'


def has_hook(name):
    return name in HOOKS


def lua_str(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


# ------------------------------------------------------------------------------------------------ switches

def dungeon_arrival(stem, arrival):
    """(x, y, z, facing) of `arrival` in an installed dungeon's studio.yml, else None (D4's dungeon_live)."""
    if os.environ.get(f'D7_{stem.upper()}_LIVE') == '0':
        return None
    blv, studio = MAPS / f'xeen_{stem}.blv', MAPS / f'xeen_{stem}.studio.yml'
    if not (blv.exists() and studio.exists()):
        return None
    m = re.search(rf'name: "{arrival}", at: \[(-?\d+), (-?\d+), (-?\d+)\], facing: (\d+)', studio.read_text())
    return tuple(int(v) for v in m.groups()) if m else None


LIVE = {'dd15': dungeon_arrival('dd15', 'entrance:d7_sky'), 'dd17': dungeon_arrival('dd17', 'entrance:d7_roof'),
        'dd26': dungeon_arrival('dd26', 'entrance:d7_stair'), 'fd01': dungeon_arrival('fd01', 'entrance:d7_roof')}
M33_DONE = 111662

D1_ROPE_FALLBACK = (-8192, 14336, 1088, 768)


def d1_rope():
    s = (MAPS / 'xeen_d1.studio.yml').read_text()
    m = re.search(r'name: "entrance:d7_rope", at: \[(-?\d+), (-?\d+), (-?\d+)\], facing: (\d+)', s)
    return (tuple(int(v) for v in m.groups()), True) if m else (D1_ROPE_FALLBACK, False)


D1_ROPE, D1_ROPE_BY_NAME = d1_rope()

# A3's Q-D26 kill qbit (D-3): any q-d26 hook that sets a kill bit; none written yet
QD26_KILL = next((v['sets'][b] for k, v in HOOKS.items() if k.startswith('q-d26') for b in v.get('sets', {})
                  if 'kill' in b or 'dead' in b or 'slain' in b), None)

PT = gen.PT


def at(pid):
    x, y = PT[pid]['at']
    return [int(x), int(y)]


# ------------------------------------------------------------------------------------------------ monsters

SPREAD = {1: [(0, 0)], 2: [(0, -224), (0, 224)], 3: [(0, -320), (0, 0), (0, 320)]}   # along the road (rotated)


def monsters():
    out = []
    rnd = random.Random(7)
    count = {}
    for g, grp in enumerate(D.GROUPS):
        cx, cy = grp['at']
        a = rnd.uniform(0, 2 * math.pi)
        if grp['space'].startswith('link:'):
            # on a road: the group strung along it (walkers on the middle line, flyers over it)
            l = next(x for x in D.LINKS if x['id'] == grp['space'])
            _, _, _, (ux, uy) = gen.link_cut(l, 0)
            a = math.atan2(uy, ux) - math.pi / 2
        step = 512 if grp['actor'] in FLYERS else 320
        for j, (dx, dy) in enumerate(SPREAD[grp['count']]):
            if grp['space'].startswith('link:'):
                dy = dy / 320 * step if grp['count'] == 3 else dy / 224 * step * 0.7
                if grp['actor'] not in FLYERS:
                    dx = 224 if j % 2 else -224     # walkers either side of the paved band, on the cloud
            if grp['actor'] in FLYERS and not grp['space'].startswith('link:'):
                f = 2.5 if grp['actor'] != GRIFFIN else 1.6
                dx, dy = dx * f, dy * f              # the flyers' bodies are wide
            x = cx + dx * math.cos(a) - dy * math.sin(a)
            y = cy + dx * math.sin(a) + dy * math.cos(a)
            k = gen.key(grp['id'])
            count[k] = count.get(k, 0) + 1
            if (grp['actor'] in FLYERS and not grp['space'].startswith('link:')
                    and gen.inside(gen.P[grp['space']], (x, y))):
                for _ in range(8):                    # a flyer over an island keeps clear of the roads' ends
                    if gen.height_at((x, y)) == D.SPACE[grp['space']]['floor']:
                        break
                    x, y = x + (cx - x) * 0.3, y + (cy - y) * 0.3
            e = {'id': f'monster:{k}_{count[k]}', 'room': 'room:air', 'monster': grp['actor'],
                 'at': [int(round(x)), int(round(y))], 'facing': rnd.choice([0, 45, 90, 135, 180, 225, 270, 315]),
                 'hostile': True, 'group': 10 + g}
            if grp['actor'] not in FLYERS:
                e['immobile'] = True
            out.append(e)
    bx, by = D.BOSS['at']
    out.append({'id': 'monster:megadragon', 'room': 'room:air', 'monster': MEGADRAGON, 'at': [bx, by], 'facing': 0,
                'hostile': True, 'leash': 1024, 'group': MEGA_GROUP,
                'notes': ("Q-D26 (D-58 Q8): the Megadragon (125, uncounted) asleep on Castle Alamar's roof hatch, "
                          "leashed 1,024 round it (the plan's leash; dungeon monsters take `leash` since merge point "
                          "26). Hidden on load once A3's kill qbit is set (D-3).")})
    for b in D.BANDITS:
        k = b['space'].split(':')[1].split('_')[0]
        k = {'mud': 'east', 'south': 'south', 'north': 'north', 'west': 'west'}.get(k, k)
        toll = next(p for p in D.POINTS if p['kind'] == 'toll' and p['space'] == b['space'])
        tx, ty = toll['at']
        for i, (bx_, by_) in enumerate(gen.bandit_spots(toll)):
            e = {'id': f'monster:bandit_{k}_{i + 1}', 'room': 'room:air', 'monster': SKY_BANDIT,
                 'at': [int(bx_), int(by_)], 'facing': int(round(gen.toward_deg((bx_, by_), (tx, ty)))) % 360,
                 'hostile': False, 'immobile': True, 'group': BANDIT_GROUP[k]}
            if i == 0:
                e['notes'] = (f"Two Sky Bandits (A2's 11116, 55, peaceful, uncounted) either side of the road at the {k} "
                              "toll (D-58 D-6): hostile only on a refusal (A3's toll hook).")
            out.append(e)
    return out


# ------------------------------------------------------------------------------------------------ decorations

def decorations():
    d = []

    def add(did, deco, xy, **kw):
        e = {'id': f'deco:{did}', 'room': 'room:air', 'decoration': deco, 'at': [int(round(xy[0])), int(round(xy[1]))]}
        e.update(kw)
        d.append(e)

    ox, oy = PT['poi:mirror']['at']
    for k in range(1, 5):
        x, y = at(f'poi:statue_{k}')
        add(f'statue_{k}', '7dec54', (x, y), facing=int(round(gen.toward_deg((x, y), (ox, oy)))) % 360)
    for p in D.POINTS:
        if p['kind'] == 'bottle':
            add(gen.key(p['id']), 'dec05', p['at'])
    rx, ry = D.SPACE['room:roost']['at']
    for k, (dx, dy, deco) in enumerate(((-768, -768, '7dec18'), (896, -384, '7dec20'), (-1024, 256, 'dec19'),
                                        (512, 640, '7dec18'))):
        add(f'roost_bones_{k + 1}', deco, (rx + dx, ry + dy))
    sx, sy = at('poi:chest_stranded_west')
    add('castaway_bones', 'dec19', (sx - 320, sy + 192))
    # Q-D27's three lamps: S's xeen_genielamp where each lies (the angry one on its rock), clicked: A3's Xeen.genieLamp
    for p in D.POINTS:
        if p['kind'] == 'lamp':
            add(gen.key(p['id']), 'xeen_genielamp', p['at'], facing=30)
    # S's sky-barges (one per merchant, the island floor as floor_height) and Lucio's celestial boat (A6 s24)
    # Each hull lies over the void, where the only floor is the safety floor (gen.FLOOR): the deck's z as a height
    # above it, hanging (the build would call it floating); radius 0, no collision, clicked by its model.
    for cargo, b in D.BARGES.items():
        add(f'barge_{cargo}', b['decoration'], b['at'], facing=b['facing'], height=b['floor'] - gen.FLOOR,
            hangs=True, notes=f"S's {b['decoration']} (the {cargo} merchant's), deck level with the island "
            f"({b['floor']}); not boardable: the merchant stands at {list(b['merchant'])} by the gangplank.")
    add('lucio_boat', D.SKYBOAT['decoration'], D.SKYBOAT['at'], facing=D.SKYBOAT['facing'],
        height=D.SKYBOAT['floor'] - gen.FLOOR, hangs=True,
        notes="S's celestial boat moored along the jetty's north-east side, prow out to the void.")
    # S's benches in the Rest Stop huts (P5's xeen_bench), two against each back wall
    for p in gen.RESTS:
        k = gen.key(p['id']).replace('rest_', '')
        for i, (xy, deg, z) in enumerate(gen.hut_benches(p)):     # on the hut's floor, not its roof
            add(f'hut_{k}_bench_{i + 1}', 'xeen_bench', xy, facing=int(round(deg)), floor_height=int(z))
    return d


def chests():
    spec = [('hoard', 'poi:chest_hoard', 'ch3', 1500, [WYRMFANG, ROOF_KEY],
             "The Megadragon's hoard (Q-D26): Wyrmfang (12530) and the Key to Castle Alamar's Roof (12377), A2's rows."),
            ('castaway_west', 'poi:chest_stranded_west', 'ch1', 1000, [],
             "The first castaway's strongbox by his bones ('A2 at 12,14')."),
            ('castaway_south', 'poi:chest_stranded_south', 'ch1', 1000, [],
             "The second castaway's strongbox under his lean-to ('C3 at 7,0')."),
            ('camp', 'poi:chest_camp', 'ch2', 2000, [], "The skywaymen's strongbox: the tolls go somewhere."),
            ('pack', 'poi:chest_launch', 'ch1', 800, [], "A lost traveller's pack by the old launch.")]
    out = []
    for c, pid, kind, gold, items, notes in spec:
        e = {'id': f'chest:{c}', 'room': 'room:air', 'at': at(pid), 'kind': kind, 'facing': 'n',
             'treasure_level': 6, 'random_items': 3 if not items else 1, 'gold': gold, 'notes': notes}
        if items:
            e['items'] = items
        out.append(e)
    return out


SOUND_SPOTS = [(-21845, 11264), (0, 11264), (21845, 11264), (-21845, -11264), (0, -11264), (21845, -11264)]


# AU's session 5 lines (devdocs/xeen/AUDIO.md "The lines to paste", D7): the four corner tips carry their plane's bed
# as a panned point sound (D-58), the Megadragon's sleep on the roost (A3 switches it off on its kill and on every load
# after), cloud dragons calling far off. (id, at, height, sound, radius, inner, volume, extra, notes)
AU_SOUNDS = [
    ('corner_fire', (-30464, 20480), 128, 'xeen_amb_plane_fire', 2500, 600, 0.5, {},
     "The Fire Corner's tip: P1's lava heard through the corner (D-58), panned."),
    ('corner_air', (30464, 20480), 128, 'xeen_amb_plane_air', 2500, 600, 0.5, {}, "The Air Corner's tip: P2's gale."),
    ('corner_earth', (30464, -20480), 128, 'xeen_amb_plane_earth', 2500, 600, 0.9, {},
     "The Earth Corner's tip: P3's grinding."),
    ('corner_water', (-30464, -20480), 128, 'xeen_amb_plane_water', 2500, 600, 0.5, {},
     "The Water Corner's tip: P4's surf."),
    ('megadragon_sleep', (-19456, 9216), 128, 'xeen_megadragon_sleep', 3500, 900, 0.6, {},
     "The Megadragon asleep on the hatch (Q-D26): off on its kill and on every load after (evt:megadragon_death, evt:megadragon_gone: AmbientSound<key> 2)."),
    # over the void between Olympus and the cap: the studio stands it on the safety floor (gen.FLOOR), so its height
    # puts it level with the other two calls (about 1,024 over the roads, z 2,150)
    ('dragon_call_cap', (4608, 4768), 2150 - gen.FLOOR, 'xeen_dragon_call', 9000, 2500, 0.45, {'wait': [25, 60]},
     'Cloud dragons calling far off (over the void: height from the safety floor, z 2,150).'),
    ('dragon_call_cap_b', (13056, -1024), 1024, 'xeen_dragon_call', 9000, 2500, 0.45, {'wait': [25, 60]}, None),
    ('dragon_call_east', (-20736, -4864), 1024, 'xeen_dragon_call', 9000, 2500, 0.45, {'wait': [25, 60]}, None),
]



def sound_key(sid):
    """A placed sound's key (its AmbientSound<key> map variable) from the build's ids.lock.yml; a new sound has none
    until the first build, so build once, then generate again."""
    lock = yaml.safe_load(open(L4 / 'ids.lock.yml'))
    return lock.get('sounds', {}).get(sid)


SLEEP_KEY = sound_key('sound:megadragon_sleep')
assert SLEEP_KEY, 'sound:megadragon_sleep has no key in ids.lock.yml yet: build once, then generate again'


def sounds():
    """The sky-map wind (X8's, X9's, P5's bed `xeen_amb_sky`, D-48 `pan: false`) over each sixth of the sky, then AU's
    D7 list (AU_SOUNDS)."""
    out = [{'id': f'sound:sky_bed_{k + 1}', 'room': 'room:air', 'at': list(p), 'height': 1024, 'sound': 'xeen_amb_sky',
            'radius': 16000, 'inner_radius': 11000, 'volume': 0.35, 'pan': False} for k, p in enumerate(SOUND_SPOTS)]
    for k, p, h, name, radius, inner, volume, extra, notes in AU_SOUNDS:
        e = {'id': f'sound:{k}', 'room': 'room:air', 'at': list(p), 'height': h, 'sound': name, 'radius': radius,
             'inner_radius': inner, 'volume': volume}
        e.update(extra)
        if notes:
            e['notes'] = notes
        out.append(e)
    return out


FACE = {'n': 'n', 's': 's', 'e': 'e', 'w': 'w', 'ne': 45, 'nw': 135, 'se': 315, 'sw': 225}


def arrival_z(a):
    z = gen.height_at(a['at'])
    return z


def objects():
    arr = []
    for a in D.ARRIVALS:
        arr.append({'entrance': a['id'], 'room': 'room:air', 'at': [int(a['at'][0]), int(a['at'][1])],
                    'facing': FACE[a['facing']], 'notes': a['how']})
    start = next(a for a in arr if a['entrance'] == 'entrance:d1_rope')
    o = {
        'format': 1,
        'start': {'room': 'room:air', 'at': list(start['at']), 'facing': start['facing'],
                  'notes': "The top of the Dark Grove rope (entrance:d1_rope, the map's start), facing east down the "
                           "inner road."},
        'arrivals': arr,
        'sounds': sounds(),
        'chests': chests(),
        'monsters': monsters(),
        'decorations': decorations(),
        'notes': ('D7 L4 objects (generated by output/studio_cal/d7/tools/gen_objects.py): 50 monsters placed in 19 '
                  'groups (no spawn markers, encounter 0), the Megadragon (uncounted) and eight peaceful Sky Bandits '
                  '(uncounted); five chests at treasure 6; statues, lamps, bottles, bones, benches; the wind. No '
                  'lights.'),
    }
    return o


# ------------------------------------------------------------------------------------------------ wiring

FALL_LUA = 'local x, y, z = evt.GetPartyPosition()\n{guard}Xeen.skyFallD7()'


def fall_lua(guard):
    lua = FALL_LUA.format(guard='if z > -1000 then return end\n' if guard else '')
    if os.environ.get('D7_FALL_TRACE') == '1':           # a probe build: which of the two runs the fall
        lua = lua.replace('Xeen.skyFallD7()', f'evt.StatusText("fall:{"timer" if guard else "floor"} z=" .. z)\n'
                                              'Xeen.skyFallD7()')
    return lua


def text_ev(eid, source, title, text, notes=None):
    e = {'id': eid, 'preset': 'text', 'source': source, 'title': title, 'text': text, 'window': False}
    if notes:
        e['notes'] = notes
    return e


HATCH_TITLES = {'dd08': "The Northern Tower's hatch", 'dd06': "The Southern Tower's hatch",
                'dd07': "The Eastern Tower's hatch", 'dd14': "Castle Blackfang's trapdoor",
                'dd05': "The Western Tower's hatch", 'dd02': "Ellinger's Tower's hatch",
                'dd03': "Castle Kalindra's hatch"}
BOLTED = 'It is bolted from below.'
SEALED_SKY = "The capstone's door does not move. (Not open yet.)"
SEALED_SEWER = 'The grate is fast in its frame. (Not open yet.)'
ALAMAR_LOCKED = ("Descend to Castle Alamar?  The door is locked.  Scratched on the surface are some words: The "
                 "Megadragon has the key!")
VAULT_SEALED = yaml.safe_load(open(WORLD / 'source/quests/m31.yml'))['hooks']['soul_storage']['fail_text']   # A3
CORNER_ANSWERS = {'fire': ['Fire', 'fire', 'FIRE'], 'air': ['Air', 'air', 'AIR'],
                  'earth': ['Earth', 'earth', 'EARTH'], 'water': ['Water', 'water', 'WATER']}


def yes_q(name, ask='Yes or No?'):
    """A3's hook's own question (quest_hooks.yml `question`), answered Yes."""
    return {'message': HOOKS[name]['question'], 'ask': ask, 'answers': ['Yes', 'Y', 'yes', 'y']}


def quoted(text):
    return gen.board_line(text)


def wiring():
    ev = []
    ev.append({'id': 'evt:fall_check', 'preset': 'script', 'trigger': 'timer', 'every': 1, 'lua': fall_lua(True),
               'notes': ("set:fall: a party under -1,000 has fallen off the roads; A3's Xeen.skyFallD7() picks the map "
                         "below by the party's x, y (six zones, Q10) and sets it down at that map's entrance:d7_fall "
                         "with falling damage.")})
    ev.append({'id': 'evt:fall_floor', 'preset': 'script', 'trigger': 'step', 'source': 'room:air',
               'lua': fall_lua(False), 'notes': 'The safety floor at -6,000: a fall the one-second check missed.'})
    ev.append({'id': 'evt:olympus_arrival', 'preset': 'script', 'trigger': 'step', 'source': 'platform:olympus_jetty',
               'once': True, 'effects': [{'lua': hook('m31.arrival')}],
               'notes': "A3's m31.arrival on the first landing at Lucio's jetty (entrance:olympus_dock)."})
    # the corners (corners.yml, D-58 relays A3): the tip asks; the element's name runs its hook (A3's, which moves the
    # party onto the plane through Xeen.toPlane), any other answer m38.corner_wrong
    for space in gen.CORNERS:
        el = space.split(':')[1].split('_')[0]
        ev.append({'id': f'evt:corner_{el}', 'preset': 'script', 'trigger': 'step', 'source': f'platform:tip_{el}',
                   'question': {'message': 'What do you seek?', 'ask': 'Answer?', 'answers': CORNER_ANSWERS[el],
                                'wrong_effects': [{'lua': hook('m38.corner_wrong')}]},
                   'effects': [{'lua': hook(f'm38.corner_{el}')}],
                   'notes': (f"The {el.capitalize()} Corner's tip (corners.yml): 'What do you seek?'; "
                             f"'{el.capitalize()}' runs A3's m38.corner_{el}, any other answer m38.corner_wrong.")})
    # boards (D-7): the words on hover, and the same as a status line on a click; both faces
    for bid, _, _, words in gen.all_boards():
        for side in ('', '_back'):
            ev.append(text_ev(f'evt:board_{bid}{side}', f'platform:board_{bid}{side}', words, words))
    for p in gen.RESTS:
        k = gen.key(p['id']).replace('rest_', '')
        for part in ('sign', 'sign_back', 'back'):
            ev.append(text_ev(f'evt:hut_{k}_{part}', f'platform:hut_{k}_{part}', 'Rest Stop', 'Rest Stop'))
    # roof hatches: one way up (D-4); the source's line and a refusal until A3's lines exist
    for p in D.POINTS:
        if p['kind'] != 'hatch' or p['id'] == 'poi:hatch_dd17':
            continue
        k = gen.key(p['id']).replace('hatch_', '')
        h = f'd7.hatch_{k}'
        if has_hook(h):
            ev.append({'id': f'evt:hatch_{k}', 'preset': 'script', 'source': f"platform:{gen.key(p['id'])}",
                       'title': HATCH_TITLES[k], 'question': yes_q(h), 'effects': [{'lua': hook(h)}],
                       'notes': f"One way up (D-4): A3's {h} (the source's line, then 'Bolted from below.')."})
        else:
            ev.append(text_ev(f'evt:hatch_{k}', f"platform:{gen.key(p['id'])}", HATCH_TITLES[k],
                              f"{quoted(p['text'])}  {BOLTED}", 'One way up (D-4): the source line and a refusal.'))
    # D-66 (DD-08 item 3): an exit into a BLV asks with the map's own Yes/No buttons (AskChoiceWithAnswerSteps, as
    # DD-15's sky door and DD-08's roof), then moves at once ({direct = true}); typed prompts stay for riddles.
    def move_to(stem, arrival):
        x, y, z, f = arrival
        return f'evt.MoveToMap({x}, {y}, {z}, {f}, 0, 0, 0, 0, "xeen_{stem}.blv", {{direct = true}})'

    def choice(step, question):
        return (f'AskChoiceWithAnswerSteps(eventId, 3, {lua_str(question)}, '
                f'{{{{Answer = "Yes", Step = {step}}}, {{Answer = "No", Step = 2}}}})')

    def choice_lua(yes, before):
        """yes: {step: [lines]} run on Yes (steps 1, 4); before: the lines up to and including the question."""
        out = []
        for step, lines in yes.items():
            out += [f'if continueStep == {step} then'] + ['    ' + l for l in lines] + ['    return', 'end']
        out += ['if continueStep ~= nil then', '    return', 'end'] + before
        return '\n'.join(out)

    # Alamar's hatch (D-5, D-61 Q14): before m33.done into DD-17, after it into FD-01 Alamar Depths; A3's q-d26.hatch
    # (its question "Descend to Castle Alamar?") decides on Yes (the key, the locked line); after m33.done until FD-01
    # exists it runs without the question ("Castle Alamar is gone."). Each way goes live by name when its map is installed.
    # s32 (F16, D-90): no Yes/No before a move into a dungeon: each hook decides (its refusal line), then the standard
    # entrance window (picture 1) with the dungeon's trans.txt row asks (A3's source/entrances.yml: 5050 the roof
    # hatch, 5062 FD-01 after the castle falls, 5047 the Pyramid, 5061 the Olympus Sewer)
    def into(stem, arrival, row):
        x, y, z, f = arrival
        return f'evt.MoveToMap({x}, {y}, {z}, {f}, 0, 0, {row}, 1, "xeen_{stem}.blv")'

    lines = [f'if IsQBitSet(QBit({M33_DONE})) then']
    if LIVE['fd01'] and has_hook('q-d26.hatch'):
        lines += [f'    if not {hook("q-d26.hatch")} then return end', '    ' + into('fd01', LIVE['fd01'], 5062)]
    elif has_hook('q-d26.hatch'):
        lines.append('    ' + hook('q-d26.hatch'))
    else:
        lines.append('    evt.StatusText(' + lua_str(ALAMAR_LOCKED) + ', 6)')
    lines += ['    return', 'end']
    if LIVE['dd17'] and has_hook('q-d26.hatch'):
        # D-89 (A8, s32): DD-17 no longer sets a party without Corak's Soul Box back on the roof: the hatch checks it
        # before the move (m33.roof_arrival's refusal on the status line; the same rule as D6's gate)
        roof_fail = yaml.safe_load(open(WORLD / 'source/quests/m33.yml'))['hooks']['roof_arrival']['fail_text']
        lines += [f'if not {hook("q-d26.hatch")} then return end',
                  'if not XeenQuests.can("m33.roof_arrival") then evt.StatusText(' + lua_str(roof_fail) + ', 6) '
                  'return end', into('dd17', LIVE['dd17'], 5050)]
    else:
        lines.append('evt.StatusText(' + lua_str(ALAMAR_LOCKED) + ', 6)')
    alamar = {'id': 'evt:hatch_dd17', 'preset': 'script', 'source': 'platform:hatch_dd17',
              'title': "Castle Alamar's roof hatch", 'lua': '\n'.join(lines)}
    if not LIVE['dd17']:
        BLOCKED.append(("Alamar's roof hatch into DD-17 before m33.done (D-5, D-61)", 'A8 (DD-17 with entrance:d7_roof)',
                        "the source's locked lines"))
    if not LIVE['fd01']:
        BLOCKED.append(("Alamar's roof hatch into FD-01 after m33.done (D-61)", 'A7/A8 (FD-01 with entrance:d7_roof)',
                        "A3's q-d26.hatch: 'Castle Alamar is gone.'"))
    alamar['notes'] = ("aaze0089:4-5; D-5: opens with the hoard's key (A3's Q-D26: its refusal line); F16: the entrance "
                       "window (row 5050) into DD-17's entrance:d7_roof (FD-01's after m33.done, row 5062).")
    ev.append(alamar)
    # the Pyramid's sky door (D-4): A3's d7.pyramid_door decides (before m30.done its "Access Denied!", as DD-15's
    # side), then the entrance window into DD-15's entrance:d7_sky once DD-15 is installed
    sky = {'id': 'evt:sky_door', 'preset': 'script', 'source': 'platform:sky_door', 'title': 'The Great Pyramid'}
    if LIVE['dd15']:
        sky['lua'] = '\n'.join([f'if not {hook("d7.pyramid_door")} then return end', into('dd15', LIVE['dd15'], 5047)])
    else:
        sky['effects'] = [{'text': SEALED_SKY}]
        BLOCKED.append(("The Pyramid's sky door", 'A8 (DD-15)', 'sealed line'))
    sky['notes'] = ("aazex102:0, A3's d7.pyramid_door; F16: the entrance window (row 5047), DD-15's entrance:d7_sky "
                    "after m30.done.")
    ev.append(sky)
    # the Olympus Sewer's grate (Q-D28): the entrance window (row 5061) into DD-26's entrance:d7_stair
    sewer = {'id': 'evt:sewer_grate', 'preset': 'script', 'source': 'platform:sewer_grate',
             'title': "A marble grate",
             'notes': ("The Olympus Sewer's stair (DD-26, Q-D28): F16, the entrance window (row 5061; A3's "
                       "q-d28.sewer_grate question 'Descend into the sewer?' retired), DD-26's entrance:d7_stair.")}
    if LIVE['dd26']:
        USED.add('q-d28.sewer_grate')
        sewer['lua'] = into('dd26', LIVE['dd26'], 5061)
    else:
        sewer['effects'] = [{'text': SEALED_SEWER}]
        BLOCKED.append(("Olympus Sewer's grate", 'A8 (DD-26)', 'sealed line'))
    ev.append(sewer)
    # the rope (D-23): both ways; down to D1's entrance:d7_rope
    x, y, z, f = D1_ROPE
    rope_lua = f'evt.MoveToMap({x}, {y}, {z}, {f}, 0, 0, 0, 0, "xeen_d1.odm", {{direct = true}})'
    for src in ('platform:rope', 'platform:rope_beam'):
        ev.append({'id': f"evt:{gen.key(src)}", 'preset': 'script', 'source': src, 'title': "Bucket o' Darkness",
                   'question': {'message': 'Descend to the Darkness Below?', 'ask': 'Descend (Yes/No)?',
                                'answers': ['Yes', 'Y', 'yes', 'y'], 'wrong_text': 'You leave the rope be.'},
                   'effects': [{'lua': rope_lua}],
                   'notes': ("The Dark Grove rope (aaze0091:5, :7): down to D1's entrance:d7_rope "
                             + ('(by name)' if D1_ROPE_BY_NAME else f'(not in D1 yet: the lead\'s point {D1_ROPE})')
                             + '.')})
    # Olympus: A4's houses, the mirror, the statues, Soul Storage
    for b in D.BUILDINGS:
        bid, house, service, door, f, fp, zone, note = b
        k = gen.key(bid)
        ev.append({'id': f'evt:{k}', 'preset': 'script', 'source': f'door:{k}', 'title': service,
                   'effects': [{'lua': f'evt.EnterHouse({house})'}], 'notes': f"A4's house {house}, {service}."})
    for src in ('platform:mirror', 'platform:mirror_frame', 'platform:mirror_sill', 'platform:mirror_post_w',
                'platform:mirror_post_e'):
        ev.append({'id': f"evt:{gen.key(src)}", 'preset': 'script', 'source': src, 'title': 'The Mirror of Olympus',
                   'effects': [{'lua': 'Xeen.useMirror(4807, eventId, continueStep)'}],
                   'notes': "A4's house 4807 (qbit 119012): Xeen.useMirror, as Castleview's."})
    for k in range(1, 5):
        ev.append({'id': f'evt:statue_{k}', 'preset': 'script', 'source': f'deco:statue_{k}', 'title': 'Statue',
                   'effects': [{'lua': hook(f'm31.statue_{k}')}], 'notes': f"A3's m31.statue_{k} (a prophecy)."})
    ev.append({'id': 'evt:vault_open', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'm30_done'},
               'effects': [{'hide': 'platform:vault_door'}, {'passable': 'platform:vault_door'}],
               'notes': "Soul Storage's door stands open for the Chosen Ones (m30.done; A3's m31.soul_storage)."})
    ev.append(text_ev('evt:vault_door', 'platform:vault_door', 'Soul Storage', VAULT_SEALED,
                      "Before m30.done the door stays shut: A3's m31.soul_storage fail_text (source/quests/m31.yml)."))
    ev.append({'id': 'evt:vault_shelf', 'preset': 'script', 'source': 'platform:vault_shelf', 'title': 'Shelves',
               'effects': [{'lua': hook('m31.soul_storage')}], 'notes': "A3's m31.soul_storage: the Soul Box."})
    ev.append({'id': 'evt:true_name_plaque', 'preset': 'script', 'source': 'platform:true_name_plaque',
               'title': 'Plaque', 'effects': [{'lua': hook('m31.true_name_plaque')}],
               'notes': "A3's m31.true_name_plaque."})
    # tolls (D-6): A3's Xeen.toll on the toll's line across the road (pay: open until the refill; refuse: this toll's
    # two bandits turn hostile)
    for p in D.POINTS:
        if p['kind'] != 'toll':
            continue
        k = gen.key(p['id']).replace('toll_', '')
        ev.append({'id': f'evt:toll_{k}', 'preset': 'script', 'trigger': 'step', 'source': f'platform:toll_{k}_line',
                   'lua': f'Xeen.toll("{k}", {BANDIT_GROUP[k]}, eventId, continueStep)',
                   'notes': (f"D-6: A3's Xeen.toll (d7.toll_paid, d7.toll_refused) for the {k} toll; its bandits are "
                             f"group {BANDIT_GROUP[k]}.")})
        USED.update(('d7.toll_paid', 'd7.toll_refused'))
        ev.append(text_ev(f'evt:toll_{k}_booth', f'platform:toll_{k}', 'Toll booth', 'A toll booth. Nobody inside.'))
    # the Megadragon (D-3): its death sets A3's q-d26.slain; the load event keeps it gone
    if has_hook('q-d26.slain'):
        ev.append({'id': 'evt:megadragon_death', 'preset': 'script', 'trigger': 'timer', 'every': 2,
                   'condition': {'not': {'qbit': 'qd26_slain'}},
                   'lua': (f'if evt.CheckMonstersKilled(ActorKillCheck.Group, {MEGA_GROUP}, 0, false) then\n'
                           f'    {hook("q-d26.slain")}\n    evt.SetMapVar("AmbientSound{SLEEP_KEY}", 2)\nend'),
                   'notes': ("D-3: the Megadragon's death (its group) runs A3's q-d26.slain (sets slain, 113520) and "
                             "switches sound:megadragon_sleep off (AmbientSound<key> 2).")})
        ev.append({'id': 'evt:megadragon_gone', 'preset': 'script', 'trigger': 'load', 'condition': {'qbit': 'qd26_slain'},
                   'effects': [{'hide_actors': MEGA_GROUP},
                               {'lua': f'evt.SetMapVar("AmbientSound{SLEEP_KEY}", 2)'}],
                   'notes': ('D-3: unique; once slain it stays gone (and its sleep sound off) through refills and a '
                             'reset after a rebuild.')})
    else:
        BLOCKED.append(('The Megadragon hidden once dead (D-3)', 'A3 (q-d26.slain)', 'placed, always shown'))
    # the merchants' riddles, the lamps, the bottles, the scarab sellers (A3's hooks)
    for p in D.POINTS:
        k = gen.key(p['id'])
        if p['kind'] == 'merchant':
            cargo = k.replace('merchant_', '')
            ev.append({'id': f'evt:{k}', 'preset': 'script', 'source': f'deco:barge_{cargo}',
                       'title': 'Merchant of the Elements',
                       'lua': f'Xeen.merchantRiddle("{cargo}", eventId, continueStep)',
                       'notes': f"A3's Xeen.merchantRiddle: d7.merchant_{cargo} or d7.merchant_wrong."})
            USED.update((f'd7.merchant_{cargo}', 'd7.merchant_wrong'))
        if p['kind'] == 'lamp':
            name = k.replace('lamp_', 'd7_')
            assert has_hook(f'q-d27.{name}'), name
            ev.append({'id': f'evt:{k}', 'preset': 'script', 'source': f'deco:{k}', 'title': "A genie's lamp",
                       'lua': f'Xeen.genieLamp("{name}", eventId, continueStep)',
                       'notes': f"Q-D27: A3's Xeen.genieLamp('{name}') (q-d27.{name})."})
            USED.add(f'q-d27.{name}')
        if p['kind'] == 'bottle':
            h = {'poi:bottle_genies': 'd7.bottle_genies', 'poi:bottle_test': 'd7.bottle_test',
                 'poi:bottle_a2': 'd7.bottle_west', 'poi:bottle_c3': 'd7.bottle_south'}[p['id']]
            ev.append({'id': f'evt:{k}', 'preset': 'script', 'source': f'deco:{k}', 'title': 'A bottle',
                       'effects': [{'lua': hook(h)}], 'notes': f"A3's {h}."})
        if p['kind'] == 'scarab':
            who = k.replace('scarab_', '')
            el = {'rahib': 'fire', 'wardoz': 'air', 'clara': 'water', 'dorion': 'earth'}[who]
            for part in ('', '_awning'):
                ev.append({'id': f"evt:stall_{who}{part}", 'preset': 'script', 'source': f"platform:stall_{who}{part}",
                           'title': 'Scarab seller', 'question': yes_q(f'd7.scarab_{el}'),
                           'effects': [{'lua': hook(f'd7.scarab_{el}')}],
                           'notes': f"Q5: A3's d7.scarab_{el} (a permanent +10 resistance for gems, once a member)."})
    for c in ('hoard', 'castaway_west', 'castaway_south', 'camp', 'pack'):
        ev.append({'id': f'evt:chest_{c}', 'preset': 'chest', 'source': f'chest:{c}'})
    return {'format': 0, 'variables': [f'd7_toll_{k}' for k in BANDIT_GROUP], 'events': ev}


def atmosphere():
    a = yaml.safe_load(open(gen.BRIEF / 'L1/atmosphere.yml'))
    a['notes'] = ("Q9: the Skyroads' preset xeen_skyroads (alias xeenroads; Darkside's amber day, below_horizon: sky) "
                  "for every stage; an outdoor view at twice the view distance so the far side of the ring and "
                  "Olympus from the rope read; no weather; X9's daylight warmed.")
    return a


def write(name, data):
    L4.mkdir(parents=True, exist_ok=True)
    with open(L4 / name, 'w') as f:
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def all_polys():
    polys = dict(gen.P)
    polys.update({f'tip:{k}': v for k, v in gen.TIPS.items()})
    return polys


def check():
    """Every placed thing on a cloud or a road; walkers and chests 256 or more inside a cloud's rim."""
    o = objects()
    things = [(m['id'], m['at'], m['monster']) for m in o['monsters']] + \
        [(c['id'], c['at'], 'chest') for c in o['chests']] + [(d['id'], d['at'], 'deco') for d in o['decorations']] + \
        [(a['entrance'], a['at'], 'arrival') for a in o['arrivals']]
    bad = 0
    for tid, p, kind in things:
        z = gen.height_at(p)
        if z is None and not tid.startswith(('deco:barge_', 'deco:lucio_boat')):   # S's hulls lie over the void
            print('NOT ON A CLOUD:', tid, p)
            bad += 1
    return bad


if __name__ == '__main__':
    write('objects.yml', objects())
    write('wiring.yml', wiring())
    write('atmosphere.yml', atmosphere())
    print('monsters', len(objects()['monsters']), 'live', {k: bool(v) for k, v in LIVE.items()}, 'd1 rope', D1_ROPE,
          'by name' if D1_ROPE_BY_NAME else 'fallback', 'hooks', len(USED), 'qd26 kill', QD26_KILL)
    print('off clouds', check())
    for b in BLOCKED:
        print('blocked:', b)
