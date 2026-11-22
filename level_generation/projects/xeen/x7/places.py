"""X7 Mount Firestone, L3/L4: the structures, actors and events. A5, 2026-11-20, after X6's places.py.

Used by gen.py. Positions come from gen_l1.py (the approved L1 with D-40) unless written here. Cells [x, y].
Textures: the dwarves' watch in the cloudside_town kit's fieldstone (chb1, MM7); the north's black rock in MM6's
volcanic set (Gharik's Forge: vlcwl1lg, vlcwl3a), the Dragon Tower in it (black stone, D-40); the doors chb1dl wings.
Original lines from the source with their aaze reference beside them; A3's hooks (source/npcs/x7.yml, xd17.yml,
quests/q-c14.yml, m37.yml, obelisks.yml) by name.
"""
import glob
import math
import os

import yaml

import kit as K
import land as LD

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')


def live(stem, env):
    """A dungeon is live when its map is installed in the world (or the env override says so)."""
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) or os.environ.get(env) == '1'


DUNGEON = {k: live('xeen_%s.blv' % k, 'X7_%s_LIVE' % k.upper()) for k in ('xd05', 'xd16', 'xd17', 'xd18', 'fd04')}
# The inside points of the dungeon doors: a named arrival of the dungeon's studio.yml (D-37: `entrance:x7_<name>`),
# None until its lane gives it. The names proposed to the lanes (NOTES, requests to A7 and A5's XD-17):
PROPOSED = {'xd05': 'entrance:x7_gate', 'xd16': 'entrance:x7_mouth', 'xd17': 'entrance:x7_cleft',
            'xd18': 'entrance:x7_mouth', 'fd04': 'entrance:x7_gate'}


def has_arrival(key):
    """The installed dungeon's studio.yml names the arrival (or the env override X7_<KEY>_INSIDE=1 says so)."""
    path = os.path.join(WORLD, 'maps', 'xeen_%s.studio.yml' % key)
    name = PROPOSED[key].split(':', 1)[1]
    return (os.path.exists(path) and name in open(path).read()) or os.environ.get('X7_%s_INSIDE' % key.upper()) == '1'


INSIDE = {k: (PROPOSED[k] if has_arrival(k) else None) for k in PROPOSED}

# lane S's lava fall (D-40 change 7): placed once it is bound in the world; no stand-in until then
_DECOS = open(os.path.join(WORLD, 'models/decorations.yml')).read()
LAVAFALL_LIVE = 'name: xeen_lavafall' in _DECOS
# three on the cove's south wall (y 29), 1,536 apart, pouring north (turn 0) into the stars, each turned a little
# toward the signature camera on the cove's west lip [67, 25] (D-35's lesson: their faces toward the camera)
CAMERA = (67.0, 25.0)
LAVAFALLS = [(70.5, 29.0), (73.5, 29.0), (76.5, 29.0)]
FALL_TURN_MAX = 25


def fall_turn(at):
    """Degrees clockwise from pouring north toward the camera (pouring north-west turns anticlockwise: negative)."""
    dx, dy = CAMERA[0] - at[0], at[1] - CAMERA[1]
    ang = math.degrees(math.atan2(dx, dy))        # 0 north, negative west
    return int(round(max(-FALL_TURN_MAX, min(FALL_TURN_MAX, ang))))


# ---------------------------------------------------------------- A3's hooks: the generated table, else the sources
HOOKS = set(yaml.safe_load(open(os.path.join(WORLD, 'data_tables/quest_hooks.yml'))) or {})
for _f in glob.glob(os.path.join(WORLD, 'source/quests/*.yml')) + glob.glob(os.path.join(WORLD, 'source/npcs/*.yml')):
    _d = yaml.safe_load(open(_f)) or {}
    for _k in (_d.get('hooks') or {}):
        HOOKS.add('%s.%s' % (os.path.splitext(os.path.basename(_f))[0], _k))
USED = set()

# Player bits (A3's npcs/x7.yml)
PB = {'well_speed': 11338, 'shrine_fire': 11339}
DAILY_BITS = []   # D-70 Q2: the Shrine of Fire is daily() for the party now (player bit 11339 unused)


def hook_lua(name):
    assert name in HOOKS, 'A3 has no hook %s' % name
    USED.add(name)
    return 'XeenQuests.hook("%s")' % name


def hook(name):
    return {'lua': hook_lua(name)}


def lua_str(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def asked_way(message, ask, way):
    """D-72 item 3: an outdoor entrance that keeps its source question asks it as one Yes/No prompt with buttons whose
    own text is the look followed by the question (no SetMessage before it: D-65 B1). Yes runs the way (the move, or the
    sealed line); No and Escape stay."""
    assert 'condition' not in way and 'else_effects' not in way
    # F16 / D-90 (A5 s29, 2026-11-22): the standard entrance window asks; its line is the trans.txt row of the look
    # and the question (level_generation/projects/xeen/common/entrance.py), so the way moves without a question of its own
    return dict(way)


def asked_first(message, ask, d):
    """D-72 item 3 for a question behind its own condition: the condition and else stay; the effects open with one
    Yes/No prompt with buttons (the look followed by the source question, no SetMessage before it). Yes (step 1) runs
    the effects; No and Escape stay."""
    prompt = message + ' ' + ask
    gate = {'lua': 'if continueStep ~= 1 then if continueStep == nil then AskChoiceWithAnswerSteps(eventId, 3, %s, '
                   '{{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}}) end return end' % lua_str(prompt)}
    return dict(d, effects=[gate] + list(d['effects']))


def reflector(name, message):
    """A Reflector (M37): one Yes/No prompt with buttons, the look of the disc and the source's question joined (D-65 B1:
    a message before a question drops the question's own text; D-66 item 6: yes/no answers are buttons); Yes calls A3's
    hook, No does nothing."""
    ask = message + ' Reflector. Activate?'
    return [{'lua': 'if continueStep == 1 then %s return end' % hook_lua(name)},
            {'lua': 'if continueStep ~= nil then return end'},
            {'lua': 'AskChoiceWithAnswerSteps(eventId, 3, %s, {{Answer = "Yes", Step = 1}, {Answer = "No", Step = 2}})'
                    % lua_str(ask)}]


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lua_str(text)}


def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d


SEALED = 'The way in is sealed. (Not open yet.)'


def dungeon_way(key, hook_name=None, sealed=None):
    """into (+ the hook as condition) when the dungeon is installed and its inside point given; else the hook (if any)
    and a sealed line (D2's, D3's and X6's rule)."""
    if DUNGEON[key] and INSIDE[key]:
        w = {'into': {'map': 'xeen_%s.blv' % key, 'arrival': INSIDE[key]}}
        if hook_name:
            w['condition'] = {'lua': hook_lua(hook_name)}
        return w
    text = sealed or SEALED
    if hook_name:
        return {'effects': [{'lua': 'if %s then evt.SimpleMessage(%s) end' % (hook_lua(hook_name), lua_str(text))}]}
    return {'effects': [msg(text)]}


def once_per_character(key, effects, again):
    return {'condition': {'not': {'player_bit': PB[key]}}, 'effects': effects + [{'player_bit': PB[key]}],
            'else_effects': again}


def daily(sid, effects, again):
    """D-70 Q2: a temporary source works once a day for the whole party (Xeen.usedToday / Xeen.markToday, every member
    by evt.ForPlayer(Players.All)); a second use the same day gives `again` and nothing else."""
    key = 'x7_' + sid.split(':', 1)[1]
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s") evt.ForPlayer(Players.All)' % key}] + effects,
            'else_effects': again}


def once_a_day(var, effects, again):
    """The whole party once a day (a map variable the daily event clears)."""
    return {'condition': {'not': {'map_var': var}},
            'effects': effects + [{'set': {'var': {'map_var': var}, 'value': 1}}], 'else_effects': again}


# ---------------------------------------------------------------- the kits
FIELD = {'wall': 'chb1', 'window': 'chb1', 'door': 'hhm1d', 'post_left': 'chb1el', 'post_right': 'chb1er',
         'roof': 'hhm2rf', 'trim': 'trim2_32', 'gable': 'chb1', 'ridge': 'trim2_32'}
BLACK = {'wall': 'vlcwl3a', 'window': 'vlcwl3a', 'door': 'chb1dl', 'post_left': 'vlcwl3a', 'post_right': 'vlcwl3a',
         'roof': 'vlcwl3a', 'trim': 'vlcwl3a', 'gable': 'vlcwl3a', 'ridge': 'vlcwl3a'}
RED_ROCK = 'cwb1'          # the south's red-brown rock (MM7 cave rock)
BASALT = 'vlcwl1lg'        # the north's black volcanic rock (MM6 Gharik's Forge)

# the places (cells)
GAP_SIGN = (63.2, 65.4)
OBELISK = (64.0, 63.0)
FORK_SIGN = (62.1, 51.3)
SLOPE_SIGN = (67.3, 93.0)
WATCH = [[64.6, 79.6], [70.4, 79.6], [70.4, 85.4], [64.6, 85.4]]
WATCH_GATE = (64.6, 82.5)
PAY_CHEST = (68.6, 85.1)
SABLE_CAVE = (77.0, 90.0)
SABLEWING = (76.35, 90.05)   # D-91 (A5 s29): under his shelter's overhang (was 75.6, 90.1 before the mouth)
SABLE_FIRE, SABLE_POT, SABLE_BONES = (76.15, 89.72), (76.22, 89.6), (76.45, 90.38)   # D-91: under the overhang
OUTPOST = (31.0, 86.0)
OUTPOST_FIRE = (31.0, 86.2)
SHRINE = (52.2, 98.2)
WELL_SPEED = (28.1, 102.1)
SPRING = (94.0, 84.1)
CAIRN = (40.1, 64.9)
BACK_GATE = (88.0, 100.0)
DEN = (83.0, 104.0)
DEN_FIRE, DEN_HIDES = (82.75, 103.35), (83.75, 102.75)   # D-91 (A5 s29): the fire under the overhang, hides beside it
ADIT = (44.0, 70.0)
XD16 = (66.5, 45.0)       # A7: a 384 x 384 mouth in a rock face 1,024 across, 512 deep
CLEFT = (74.0, 48.0)
XD18 = (56.5, 29.0)       # A7: a 768 x 640 mouth, footprint 1,536 x 1,024
TOWER_AT = (27.5, 27.6)   # A7: a round tower about 1,024 across, a 384 x 448 two-leaf door
FD04_DOOR = (29.0, 31.62)
REFLECTOR = (101.2, 26.6)
LAVA_ROCK = (35.0, 44.0)
KNIGHT = (59.4, 36.4)
WALLOW = (41.6, 54.8)
HOARD = (97.0, 46.4)
MINER_CHEST = (44.7, 68.8)
DEN_CHEST = (83.15, 103.3)   # D-91 (A5 s29): under the den's overhang (F6: 84.4, 102.7)
DEN_CHEST_F6 = (84.4, 102.7)   # F6 (2026-11-21): beside the den, not on its mouth's line (was 83.0, 102.6 before the dark door face)
OUTPOST_CHEST = (31.6, 86.9)
# the arrivals the neighbours' doors and edges send here (cells; facing)
CLEFT_ARRIVAL = (71.8, 48.0)     # XD-17's back passage lets out before the cleft, facing west (away from it)
SOUTH_MARKERS = int(os.environ.get('X7_SOUTH_MARKERS', '13'))   # A2 (Act I 1.166 -> 1.148): 8, no placed Orc Guard; F10 (2026-11-21): 13 markers of 1-2 orcs (19.5; 8 x 2.5 = 20 before), spread over five areas


# ---------------------------------------------------------------- structures
def structures():
    out = []
    S = out.append
    gap(S)
    watch(S)
    south(S)
    north(S)
    doors(S)
    finds(S)
    basalt(S)
    if LAVAFALL_LIVE:
        for i, at in enumerate(LAVAFALLS, 1):
            S(deco('thing:lavafall_%d' % i, 'xeen_lavafall', at, turn=fall_turn(at),
                   notes="Lane S's lava fall (D-40 change 7) on the cove's south wall at the lip, pouring north into "
                         "the stars, turned %d toward the signature camera at [67, 25]." % fall_turn(at)))
    return out


BASALT_LIVE = 'name: xeen_basalt1' in _DECOS
# Lane S's basalt boulders (D-40: the Dragon Tower's crag and the north's black rock); world rows 4005-4007, which the
# studio's scatter does not read (only the engine's table), so each stands as a decoration of its own.
BASALT_AREAS = [  # (name, polygon, count, seed)
    ('tower_crag', [[25.0, 25.4], [33.4, 25.4], [33.6, 34.0], [24.6, 34.0]], 22, 41),
    ('dragon_crag', [[52.0, 25.4], [61.0, 25.4], [61.0, 29.2], [52.0, 29.2]], 12, 42),
    ('flats', [[52, 30], [66, 30], [70, 34], [75, 42], [74, 55], [62, 58], [53, 55]], 22, 43),
    ('cone', [[79.5, 25.0], [103.2, 25.0], [103.2, 56], [88, 59], [77, 54], [76, 36], [78.5, 30]], 40, 44),
]


def basalt_ok(x, y):
    if LD.in_void(x, y) or min(LD.RIM_X - x, y - LD.RIM_Y) < 1.0 or K.edge_dist((x, y), LD.COVE) < 1.2:
        return False
    if K.inside((x, y), LD.LAKE) or K.inside((x, y), LD.CRATER) or K.edge_dist((x, y), LD.LAKE) < 0.8:
        return False
    if LD.dist_to_line(x, y, LD.RIVER) < 1.6 or LD.dist_to_line(x, y, LD.ARM) < 1.4:
        return False
    if any(LD.dist_to_line(x, y, ln) < 1.5 for ln, _p, _h, _b in LD.PROFILED):
        return False
    for door in (XD16, (64.5, 45.0), CLEFT, (72.0, 48.0), XD18, (56.5, 31.0), FD04_DOOR, (29.0, 32.6), REFLECTOR, HOARD,
                 KNIGHT, LAVA_ROCK):
        if math.hypot(x - door[0], y - door[1]) < 3.2:
            return False
    if TOWER_AT[0] - 0.3 < x < TOWER_AT[0] + 3.3 and TOWER_AT[1] - 0.3 < y < TOWER_AT[1] + 4.3:
        return False
    return not any(math.hypot(x - f[0], y - f[1]) < 2.5 for f in LAVAFALLS)


def basalt(S):
    if not BASALT_LIVE:
        return
    import random
    for name, poly, count, seed in BASALT_AREAS:
        rnd = random.Random(seed)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        pts = []
        tries = 0
        while len(pts) < count and tries < count * 400:
            tries += 1
            p = (rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys)))
            if not K.inside(p, poly) or not basalt_ok(*p) or any(math.hypot(p[0] - q[0], p[1] - q[1]) < 1.3
                                                                  for q in pts):
                continue
            pts.append(p)
        for i, p in enumerate(pts, 1):
            S(deco('thing:basalt_%s_%d' % (name, i), 'xeen_basalt%d' % rnd.choice((1, 1, 2, 2, 3)), p,
                   turn=rnd.randrange(-180, 180, 15)))


def gap(S):
    """The Firestone Gap: the signpost with D-40's warning, the obelisk on the north lip; the other two signposts."""
    S({'id': 'thing:gap_sign', 'kind': 'sign', 'at': list(GAP_SIGN), 'height': 256, 'title': 'The Firestone Gap',
       'arms': [{'title': 'North: Mount Firestone. Dragons. Turn back.', 'toward': 'n'},
                {'title': 'Vertigo', 'toward': 's'}, {'title': 'Burlock', 'toward': 'w'}],
       'effects': [msg('North: Mount Firestone. Dragons. Turn back.')],
       'notes': "D-40 change 4: the deadly north is announced at the Gap's signpost."})
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': list(OBELISK), 'height': 768, 'title': 'Obelisk',
       'effects': [hook('obelisks.x7')], 'notes': "Cloudside's seventh obelisk (A3's obelisks.x7) on the Gap's north lip, "
                                                 'the whole north below.'})
    # Eleventh session: the two fork signposts read when clicked, as L1 counted them (D-40's 22 POIs: only the third
    # signpost's click was to go, and only past 28)
    S({'id': 'thing:signpost_fork', 'kind': 'sign', 'at': list(FORK_SIGN), 'height': 256, 'title': 'Signpost',
       'arms': [{'title': 'The Dragon Cave', 'toward': 'n'}, {'title': 'The Volcano Cave', 'toward': 'e'},
                {'title': 'The lava lake', 'toward': 'w'}, {'title': 'The Gap', 'toward': 's'}],
       'effects': [msg('North: the Dragon Cave. East: the Volcano Cave. West: the lava lake. South: the Gap, '
                       'and home.')]})
    S({'id': 'thing:signpost_slope', 'kind': 'sign', 'at': list(SLOPE_SIGN), 'height': 256, 'title': 'Signpost',
       'arms': [{'title': "The hermit's cave", 'toward': 'e'}, {'title': 'The Shrine of Fire', 'toward': 'w'},
                {'title': 'The Firestone Gap', 'toward': 'n'}, {'title': 'Vertigo', 'toward': 's'}],
       'effects': [msg("North: the Firestone Gap. South: Vertigo. West: the Shrine of Fire. East: the hermit's "
                       'cave.')]})


def watch(S):
    """The abandoned dwarves' watch (D-40 change 8): a fieldstone stockade, its gate west onto the road, the signal
    tower, the fallen barracks, the pay chest with its note; the pony shed under the range."""
    S({'id': 'thing:watch_wall', 'kind': 'wall', 'line': [list(p) for p in WATCH], 'closed': True, 'height': 256, 'thickness': 128,
       'textures': {'wall': 'chb1', 'top': 'cwb'}, 'title': "The dwarves' watch",
       'gates': [{'at': list(WATCH_GATE), 'width': 448, 'height': 240}],
       'notes': "The stockade's fieldstone wall, its gate open on the road (abandoned)."})
    S({'id': 'thing:watch_tower', 'kind': 'building', 'at': [68.2, 80.0], 'size': [2.0, 2.0], 'kit': 'plaster',
       'door': 'none', 'title': "The watch's signal tower", 'textures': dict(FIELD), 'floor': LD.WATCH_H,
       'parts': [{'id': 't', 'shape': 'round', 'at': [512, 512], 'radius': 352, 'sides': 10, 'wall_height': 1280,
                  'roof': 'cone', 'roof_pitch': 58, 'windows': 'none'}],
       'notes': "The signal tower beside the road, its brazier cold (a landmark seen from the X1 arrival)."})
    S({'id': 'thing:watch_barracks', 'kind': 'building', 'at': [65.0, 83.0], 'size': [2.4, 2.0], 'kit': 'plaster',
       'door': 'none', 'title': "The watch's barracks, roofless", 'textures': dict(FIELD), 'floor': LD.WATCH_H,
       'ruin': {'height': [96, 352], 'gaps': 0.35, 'thickness': 64, 'seed': 7},
       'parts': [{'id': 'r', 'at': [64, 64], 'size': [1100, 896], 'wall_height': 352, 'roof': 'none',
                  'windows': 'none'}]})
    S({'id': 'thing:pay_chest', 'kind': 'chest', 'at': list(PAY_CHEST), 'title': "The watch's pay chest",
       'chest': {'level': 2, 'random_items': 2}, 'effects': [hook('x7.watch_note')],
       'notes': "D-40 changes 1 and 8: level 2; the note by it (A3's x7.watch_note)."})
    for i, (d, at) in enumerate([('bigbarel', (65.3, 80.05)), ('smlbarel', (65.65, 80.05))]):
        S(deco('thing:watch_barrel_%d' % (i + 1), d, at))
    S(deco('thing:watch_brazier', 'dec24x', (67.4, 80.4), title='A cold brazier'))
    S({'id': 'thing:pony_shed', 'kind': 'building', 'at': [75.0, 75.4], 'size': [2.0, 1.4], 'kit': 'plaster',
       'door': 'none', 'title': "The watch's pony shed, its roof fallen in", 'textures': dict(FIELD),
       'ruin': {'height': [64, 256], 'gaps': 0.45, 'thickness': 64, 'seed': 3},
       'parts': [{'id': 's', 'at': [48, 48], 'size': [928, 620], 'wall_height': 256, 'roof': 'none',
                  'windows': 'none'}]})


def south(S):
    """Sablewing's cave, the orc outpost to burn, the Shrine of Fire, the Well of Speed, the hot spring, the cairn,
    the landmarks of the slopes and the range."""
    # Sablewing's cave mouth under the red crag (D-5.2, D-40): his hoard heaped inside as dressing
    S({'id': 'thing:sablewing_cave', 'kind': 'cave_mouth', 'at': list(SABLE_CAVE), 'size': [1024, 1024], 'turn': 90,
       'mouth': {'width': 512, 'height': 416, 'depth': 256}, 'textures': {'shell': RED_ROCK},
       'roughness': 0.6, 'seed': 12, 'title': "Sablewing's cave", 'form': 'shelter',
       'notes': "D-5.2: the hermit's cave under the red crag, off the road from X1; D-91: a lit open shelter, "
                "Sablewing and his hoard under it, no way in."})
    S(deco('thing:sable_fire', '7dec02', SABLE_FIRE, title='A small fire'))
    S(deco('thing:sable_pot', '7dec03', SABLE_POT))
    S(deco('thing:sable_bones', 'dec29', SABLE_BONES))
    # the orc outpost (source E2): hides on poles round a fire; burns once (A3's x7.orc_outpost); its chest one spot
    burnt = ['thing:outpost_hide_1', 'thing:outpost_hide_2', 'thing:outpost_hide_3']
    for i, (at, size, turn) in enumerate([((29.6, 84.9), [512, 640], 20), ((32.6, 85.0), [512, 640], -15),
                                          ((30.2, 87.6), [640, 512], 80)]):
        S({'id': burnt[i], 'kind': 'tent', 'at': list(at), 'size': size, 'height': 352, 'open': True, 'turn': turn,
           'title': 'Orc hides on poles'})
    hide_lua = ' '.join('HideThing("%s")' % b for b in burnt)
    S(deco('thing:outpost_fire', '7dec02', OUTPOST_FIRE, title='The orc outpost',
           **asked_first('Hides stretched on poles round a fire pit, bones and filth everywhere.',
                         'You have found an Orc Outpost. Put it to the torch?',
                         {'condition': {'not': {'qbit': 'outpost_burned'}},
                          'effects': [{'lua': 'if %s then %s end' % (hook_lua('x7.orc_outpost'), hide_lua)}],
                          'else_effects': [hook('x7.orc_outpost')]}),
           notes='Source E2 (xeen/aaze0018:3-4); A3 x7.orc_outpost: once, 500 experience, outpost_burned (116160).'))
    S({'id': 'thing:outpost_chest', 'kind': 'chest', 'at': list(OUTPOST_CHEST), 'title': "The orcs' loot",
       'chest': {'level': 1, 'random_items': 2}, 'notes': 'D-40 changes 1 and 5: level 1; one spot with the outpost.'})
    for i, (d, at) in enumerate([('7dec18', (29.0, 86.6)), ('sklplrev', (33.2, 87.2)), ('dec19', (32.4, 84.0))]):
        S(deco('thing:outpost_bones_%d' % (i + 1), d, at))
    # the Shrine of Fire on its knoll (source E2; D-40 question 2: daily, a temporary Fire resistance)
    S({'id': 'thing:shrine_fire_house', 'kind': 'building', 'at': [51.4, 97.4], 'size': [1.6, 1.6], 'kit': 'plaster',
       'door': 'none', 'title': 'The Shrine of Fire', 'textures': dict(FIELD), 'floor': LD.SHRINE_H,
       'parts': [{'id': 's', 'at': [96, 96], 'size': [627, 627], 'wall_height': 352, 'posts': 32, 'roof': 'hip',
                  'roof_pitch': 38, 'windows': 'none'}]})
    S(deco('thing:shrine_fire', 'dec64', SHRINE, title='Shrine of Fire',
           **daily('thing:shrine_fire', [{'add': {'var': 'FireResistanceBonus', 'value': 10}}, hook('x7.shrine_fire')],
                   [hook('x7.shrine_fire_again')]),
           notes='Source E2 (xeen/aaze0018:5-6); A3 x7.shrine_fire: +10 Fire resistance until you rest, once a day '
                 'for the party (D-70: x7_shrine_fire).'))
    # the Well of Speed (source E2; D-40 question 2: +2 Speed, once per character, the map's permanent device)
    S({'id': 'thing:well_speed', 'kind': 'well', 'at': list(WELL_SPEED), 'title': 'The Well of Speed',
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       **once_per_character('well_speed', [{'add': {'var': 'BaseSpeed', 'value': 2}}, hook('x7.well_speed')],
                            [hook('x7.well_speed_again')]),
       'notes': 'Source E2 (xeen/aaze0018:0); A3 x7.well_speed: +2 Speed (base), once per character (player bit 11338).'})
    # the dwarves' hot spring in the red rock (L1: heals, daily)
    S({'id': 'thing:hot_spring', 'kind': 'fountain', 'at': list(SPRING), 'radius': 320, 'sides': 9, 'pillar': 0,
       'title': 'A hot spring', 'textures': {'wall': RED_ROCK},
       **once_a_day('spring_used', [{'lua': 'evt.ForPlayer(Players.All) AddValue(HP, 150)'},
                                    {'text': 'You soak until the ache leaves your bones. (+150 hit points)'}],
                    [{'text': 'The water is still warm. You have soaked enough today.'}]),
       'notes': "The dwarves' hot spring (L1): +150 hit points to every member, once a day."})
    # the cairn of the unreturned beside the Firestone road (L1: +Luck, daily)
    S(deco('thing:cairn', 'rock26', CAIRN, title='The cairn of the unreturned',
           **daily('thing:cairn', [{'add': {'var': 'LuckBonus', 'value': 10}},
                                   {'text': 'Names scratched on every stone: those who went north. You add a stone. '
                                            'The stones seem to wish you luck. (+10 Luck until you rest)'}],
                   [{'text': 'You have added your stone today.'}])))
    for i, at in enumerate([(39.6, 64.5), (40.7, 65.3)]):
        S(deco('thing:cairn_stone_%d' % (i + 1), '7rock08', at))
    # landmarks (no click): the boundary stone, the slag heaps, the charcoal pits, the fallen cart, the east lookout,
    # the dragon's skull
    S({'id': 'thing:boundary_stone', 'kind': 'sign', 'at': [31.0, 68.4], 'height': 224, 'width': 160,
       'title': 'A dwarf boundary stone, carved with a dragon and a line'})
    for i, (d, at) in enumerate([('7rock09', (51.6, 83.6)), ('rock28', (52.6, 84.4)), ('7rock09', (52.2, 85.2)),
                                 ('rock30', (53.4, 83.8)), ('7rock08', (51.2, 84.8))]):
        S(deco('thing:slag_%d' % (i + 1), d, at, **({'title': "The dwarves' old slag heaps"} if i == 0 else {})))
    for i, at in enumerate([(56.6, 89.6), (57.6, 90.4), (56.9, 90.9)]):
        S(deco('thing:charcoal_pit_%d' % (i + 1), 'dec24x', at, title='A cold charcoal pit'))
    S({'id': 'thing:fallen_cart', 'kind': 'tent', 'at': [42.0, 106.2], 'size': [448, 768], 'height': 256,
       'open': False, 'turn': 70, 'title': 'An overturned ore cart'})
    S({'id': 'thing:east_lookout', 'kind': 'building', 'at': [83.0, 69.0], 'size': [2.0, 2.0], 'kit': 'plaster',
       'door': 'none', 'title': "The dwarves' east lookout", 'textures': dict(FIELD),
       'ruin': {'height': [128, 384], 'gaps': 0.3, 'thickness': 64, 'seed': 9},
       'parts': [{'id': 'h', 'at': [96, 96], 'size': [832, 832], 'wall_height': 384, 'roof': 'none',
                  'windows': 'none'}]})
    # the Red River Basin's far end: a dwarf ore wagon the orcs broke up, its bones and its ore spilt (6,000 rule)
    S({'id': 'thing:broken_wagon', 'kind': 'tent', 'at': [100.4, 92.6], 'size': [512, 896], 'height': 288,
       'open': False, 'turn': -35, 'title': 'A broken ore wagon, its ore spilt red down the slope'})
    for i, (d, at) in enumerate([('rock28', (99.4, 93.6)), ('rock30', (101.2, 91.4)), ('dec19', (99.8, 91.6))]):
        S(deco('thing:wagon_ore_%d' % (i + 1), d, at))
    for i, (d, at) in enumerate([('dec29', (97.6, 73.6)), ('sklplrev', (98.4, 74.2)), ('dec21', (99.0, 73.4)),
                                 ('7dec18', (97.8, 74.8))]):
        S(deco('thing:dragon_skull_%d' % (i + 1), d, at, **({'title': "A dragon's bones, picked clean"} if i == 0
                                                            else {})))


def north(S):
    """The black bridge, the lava rock's island, the Fire Reflector, the idols."""
    S({'id': 'thing:black_bridge', 'kind': 'bridge', 'line': [[61, 41.2], [61, 44.8]], 'width': 448, 'kerb': 64,
       'textures': {'deck': 'voltyl', 'side': BASALT, 'pier': BASALT}, 'title': 'The black bridge',
       'notes': 'A bridge of black cooled flow over the lava river.'})
    # D-90 (A5 s30, merge point 42): the Ever-Hot Lava Rock is a 3D ground item (12314) at LAVA_ROCK (gen.py's sketch
    # `items`); its decoration and click are gone
    for i, (d, at) in enumerate([('7rock09', (33.6, 43.0)), ('rock28', (36.6, 42.4)), ('7rock08', (33.4, 45.6))]):
        S(deco('thing:island_rock_%d' % (i + 1), d, at))
    S({'id': 'thing:fire_reflector', 'kind': 'obelisk', 'at': list(REFLECTOR), 'height': 384, 'sides': 8,
       'title': 'Fire Reflector',
       'effects': reflector('m37.reflector_fire', 'A disc of red crystal on a stone stem, turned toward the heat off '
                            'the mountain.'),
       'notes': "Original line: xeen/aaze0021:0; M37 after M36 (A3's m37.reflector_fire)."})


# Lane S's idols (XD-16, D-40): xeen_idol_demon (list id 4007) and xeen_idol_devil (4008), origin at the plinth's
# bottom centre, turn -90 = facing 90 (west, out of the mouth). Symmetric about the mouth's axis (y 45): the demon
# 358 north (its centre 305 from the opening's edge, >= 250), the devil 486 south (wings +-282 north-south; centre 390
# from the opening's edge, >= 350, its wing tips 204 off the axis, clear of the 384 opening); both 256 before the face.
# The volcano path ends on the axis; the cleft path starts south of the devil (land.CLEFT_PATH, 13th session).
IDOLS = [('thing:idol_demon', 'xeen_idol_demon', (65.5, 44.3), 'A demon idol'),
         ('thing:idol_devil', 'xeen_idol_devil', (65.5, 45.95), 'A devil idol')]
IDOL_SINK = 0     # the mouth's pad is flat (2,240) under both plinths: no sink needed


def idol(sid, name, at, title):
    extra = {'raise': -IDOL_SINK} if IDOL_SINK else {}
    return deco(sid, name, at, turn=-90, title=title, effects=[hook('x7.idols')], **extra,
                notes="Lane S's idol model (D-40) flanking XD-16's mouth, facing west; A3's x7.idols.")


def doors(S):
    """The five ways in, each sealed until its map exists and its lane names the inside arrival (D-37)."""
    # XD-16 the Volcano Cave, facing west at Firestone's foot, the demon and the devil idol flanking it (one spot)
    S({'id': 'thing:xd16_mouth', 'kind': 'cave_mouth', 'at': list(XD16), 'size': [1024, 512], 'turn': 90,
       'mouth': {'width': 384, 'height': 384, 'depth': 192}, 'textures': {'shell': BASALT, 'door': '7solid01'},
       'roughness': 0.6, 'seed': 16, 'title': 'The Volcano Cave', 'hint': 'Volcano Cave', 'floor': LD.MOUTH_H,
       **asked_way('A cave mouth breathing heat between a demon and a devil carved in black rock.',
                   'Enter the Volcano Cave?',
                   dungeon_way('xd16', None, 'Heat pours out of the cave, and the way in is choked with fallen rock. '
                                             '(Not open yet.)')),
       'notes': 'XD-16 Volcano Cave (A7, Q-C26): "Enter the Volcano Cave?" (xeen/aaze0017:1); sealed until XD-16 is '
                'installed and A7 names its inside arrival (proposed entrance:x7_mouth).'})
    for sid, name, at, title in IDOLS:
        S(idol(sid, name, at, title))
    # XD-17 Shangri-La's cleft (D-40 question 3): a rockfall from this side until the party leaves the valley once by
    # its back passage (A3's xd17.cleft_opened sets cleft_open 116140); the door asks A3's xd17.cleft
    S({'id': 'thing:xd17_cleft', 'kind': 'cave_mouth', 'at': list(CLEFT), 'size': [1024, 1024], 'turn': 90,
       'mouth': {'width': 256, 'height': 480, 'depth': 384, 'sides': 2}, 'textures': {'shell': 'vlcwl3a',
                                                                                     'door': '7solid01'},
       'roughness': 0.8, 'seed': 17, 'title': 'A cleft in the black rock', 'floor': LD.CLEFT_H,
       **dungeon_way('xd17', 'xd17.cleft', 'The cleft is clear, but the passage beyond is not there yet. '
                                           '(Not open yet.)'),
       'notes': "XD-17 Shangri-La's back gate (D-40 question 3): A3's xd17.cleft (fail text: the rockfall), then "
                'sealed until XD-17 is installed and names entrance:x7_cleft; the rock shows open or closed by '
                'cleft_open (evt:cleft_state).'})
    for i, at in enumerate([(72.85, 47.8), (72.9, 48.25), (72.7, 48.0)]):
        S(deco('thing:cleft_fall_%d' % (i + 1), ['7rock08', '7rock09', 'rock28'][i], at))
    for i, at in enumerate([(72.3, 47.0), (72.4, 49.1)]):
        S(deco('thing:cleft_spoil_%d' % (i + 1), ['7rock09', '7rock08'][i], at))
    # XD-18 the Dragon Cave in its crag at the rim, facing south
    S({'id': 'thing:xd18_mouth', 'kind': 'cave_mouth', 'at': list(XD18), 'size': [1536, 1024], 'turn': 0,
       'mouth': {'width': 768, 'height': 640, 'depth': 256}, 'textures': {'shell': BASALT, 'door': '7solid01'},
       'roughness': 0.7, 'seed': 18, 'title': 'The Dragon Cave', 'hint': 'Dragon Cave', 'floor': LD.CRAG_FOOT_H,
       **asked_way('Scorched rock, gnawed bones, and a smell of sulphur.',
                   'The Dragon Cave smells pretty bad. Are you sure you wish to enter?',
                   dungeon_way('xd18', None, 'A wall of rock fills the cave a few steps in. Something huge breathes '
                                             'behind it. (Not open yet.)')),
       'notes': 'XD-18 Dragon Cave (A7, phase 6; Q-C25): "The Dragon Cave smells pretty bad. Are you sure you wish to '
                'enter?" (xeen/aaze0017:0); the tax office inside its mouth; sealed until XD-18 exists.'})
    for i, (d, at) in enumerate([('dec29', (54.8, 31.0)), ('7dec20', (57.3, 31.2)), ('dec19', (55.2, 31.9))]):
        S(deco('thing:xd18_bones_%d' % (i + 1), d, at))
    # FD-04 the Dragon Tower on its crag over the lava lake (D-40: black stone, small at its planned distance; A7: a
    # round tower about 1,024 across, its two-leaf door 384 x 448 with the sill on the crag top)
    S({'id': 'thing:dragon_tower', 'kind': 'building', 'at': list(TOWER_AT), 'size': [3.0, 4.0], 'kit': 'plaster',
       'facing': 's', 'door': 'none', 'floor': LD.TOWER_H, 'title': 'The Dragon Tower', 'textures': dict(BLACK),
       'parts': [{'id': 'keep', 'shape': 'round', 'at': [768, 1531], 'radius': 512, 'sides': 12, 'wall_height': 2048,
                  'roof': 'cone', 'roof_pitch': 66, 'windows': 'none'}],
       'notes': "FD-04's shell: a black tower on its crag at the north rim over the lava lake."})
    gate4 = {'id': 'thing:fd04_gate', 'kind': 'doorway', 'at': list(FD04_DOOR), 'facing': 's', 'width': 384,
             'height': 448, 'depth': 96, 'leaves': 2, 'floor': LD.TOWER_H, 'hood': 48,
             'textures': {'door': 'chb1dl', 'wall': 'vlcwl3a'}, 'title': 'The Dragon Tower',
             **dungeon_way('fd04', 'q-f1.tower_door',
                           'The black doors do not move. Far up the tower, something shifts its '
                           'weight. (Not open yet.)'),
             'notes': "FD-04 (A7, phase 6; Q-F1, Q-F2): A3's q-f1.tower_door (the Key to the Dragon Tower, 12376; "
                      'D-57 Q23), then sealed until FD-04 exists. Two leaves (chb1dl, mirrored).'}
    S(gate4)
    # XD-05's back gate in the hillside (opened from inside: x1-tam.back_gate sets 110051)
    gate5 = {'id': 'thing:xd05_gate', 'kind': 'doorway', 'at': list(BACK_GATE), 'facing': 'w', 'width': 384,
             'height': 384, 'depth': 448, 'leaves': 2, 'floor': LD.GATE_H, 'hood': 64,
             'textures': {'door': 'chb1dl', 'wall': RED_ROCK}, 'title': "The Orc Caves' back gate"}
    if DUNGEON['xd05'] and INSIDE['xd05']:
        gate5.update({'condition': {'qbit': 'orc_back_gate'}, 'into': {'map': 'xeen_xd05.blv',
                                                                       'arrival': INSIDE['xd05']},
                      'else_effects': [msg('A heavy door of logs in the hillside, barred from within.')]})
    else:
        gate5.update({'condition': {'qbit': 'orc_back_gate'},
                      'effects': [msg('The bar is off inside, but rubble still chokes the passage behind the logs. '
                                      '(Not open yet.)')],
                      'else_effects': [msg('A heavy door of logs in the hillside, barred from within.')]})
    gate5['notes'] = ("XD-05 Orc Caves' back gate (A7, built): barred until x1-tam.back_gate (110051); then into "
                      "XD-05's entrance:x7_gate (sealed while XD-05 does not name it).")
    S(gate5)
    for i, at in enumerate([(87.7, 99.35), (87.7, 100.65)]):
        S(deco('thing:gate_torch_%d' % (i + 1), 'dec06', at))


def finds(S):
    """The chests (D-40 change 1: levels by who reaches them) and the miner's adit, the orcs' den."""
    S({'id': 'thing:orc_den', 'kind': 'cave_mouth', 'at': list(DEN), 'size': [1024, 1024], 'turn': 180,
       'mouth': {'width': 448, 'height': 352, 'depth': 256}, 'textures': {'shell': RED_ROCK},
       'roughness': 0.6, 'seed': 21, 'title': "The gate pickets' den", 'form': 'shelter',
       'notes': 'D-91: a lit open shelter, the stash and a fire under it, no way in.'})
    S(deco('thing:den_fire', '7dec02', DEN_FIRE, title="The pickets' fire"))
    S(deco('thing:den_hides', '7dec18', DEN_HIDES))
    S({'id': 'thing:den_chest', 'kind': 'chest', 'at': list(DEN_CHEST), 'title': "The orcs' stash",
       'chest': {'level': 1, 'random_items': 2},
       'effects': [{'text': 'Crude furnishings and filthy bedding: orcs have been living under this overhang.'}],
       'notes': "Source F2 (xeen/aaze0022:1, its \"Pillage?\" dropped: the chest opens at once and the source's "
                'look is its status line, A5 s31 for the user: "let me open the chest and loot it"); '
                'D-40 change 1: level 1.'})
    S({'id': 'thing:miner_adit', 'kind': 'cave_mouth', 'at': list(ADIT), 'size': [1024, 1024], 'turn': 180,
       'mouth': {'width': 256, 'height': 320, 'depth': 128, 'sides': 0, 'rim': 96},
       'textures': {'shell': RED_ROCK}, 'roughness': 0.5, 'seed': 22, 'form': 'blocked',
       'effects': [{'text': 'The adit has fallen in.'}],
       'title': "A dwarf miner's old adit, its props fallen", 'notes': 'D-91: blocked at its face (rubble).'})
    S({'id': 'thing:miner_cache', 'kind': 'crate', 'at': list(MINER_CHEST), 'title': "The miner's cache",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'Behind a fallen prop, a box the miner meant to come back for.'}],
       'notes': 'D-40 change 1: level 3 (an Act II party reaches it from X4\'s road).'})
    S({'id': 'thing:knight_remains', 'kind': 'chest', 'at': list(KNIGHT), 'title': "A knight's strongbox",
       'chest': {'level': 5, 'random_items': 3},
       'effects': [{'text': 'A knight who came for the Dragon Cave. His armour has run into the rock.'}],
       'notes': 'D-40 change 1: level 5.'})
    for i, (d, at) in enumerate([('dec19', (58.6, 36.9)), ('7dec20', (60.1, 37.0))]):
        S(deco('thing:knight_bones_%d' % (i + 1), d, at))
    S({'id': 'thing:hydra_wallow', 'kind': 'chest', 'at': list(WALLOW), 'title': "A pilgrim's pack",
       'chest': {'level': 5, 'random_items': 2},
       'effects': [{'text': 'The hydras wallow here in the heat off the lava. Bones, and a pilgrim\'s pack.'}],
       'notes': 'D-40 change 1: level 5.'})
    for i, (d, at) in enumerate([('dec29', (40.8, 54.2)), ('7dec18', (42.6, 54.0)), ('dec21', (41.2, 55.5))]):
        S(deco('thing:wallow_bones_%d' % (i + 1), d, at))
    S({'id': 'thing:dragon_hoard', 'kind': 'chest', 'at': list(HOARD), 'title': "A dragon's hoard",
       'chest': {'level': 6, 'random_items': 4},
       'effects': [{'text': 'Gold among scorched bones. Whatever sleeps on this is not sleeping on it now.'}],
       'notes': 'D-40 change 1: level 6.'})
    for i, (d, at) in enumerate([('dec29', (96.2, 46.0)), ('sklplrev', (97.8, 47.0)), ('7dec18', (96.6, 47.3))]):
        S(deco('thing:hoard_bones_%d' % (i + 1), d, at))


# ---------------------------------------------------------------- actors
def actors():
    out = [
        {'monster': '11593', 'at': [35.0, 44.0], 'count': 6, 'spread': 1.2, 'group': 61, 'hostile': True,
         'notes': "Lava Golems 55 on the Ever-Hot Lava Rock's island (D-40 question 4); movement Short (about 1,024) "
                  'from where they stand, inside the island.'},
        {'monster': '11593', 'at': [35.5, 51.0], 'count': 2, 'spread': 0.6, 'group': 61, 'hostile': True,
         'notes': 'Two more on the causeway.'},
        {'monster': '11030', 'at': [31.0, 85.4], 'count': 2, 'spread': 0.8, 'group': 62, 'hostile': True,
         'notes': "Orcs 5 at the outpost to burn (placed, never refilled); no Orc Guard (A2: Act I 1.148)."},
        {'monster': '11927', 'npc': 4720, 'at': list(SABLEWING), 'spread': 0, 'group': 53,
         'notes': 'Sablewing the Dragon Hermit (A4 4720, D-5.2, D-40): Dragon Master, at his cave mouth; his own row 11927 on the gold dragon (F9).'},
    ]
    return out


def events():
    clear = '\n'.join(['evt.ForPlayer(Players.All)'] + ['ClearPlayerBit(PlayerBit(%d))' % PB[k] for k in DAILY_BITS])
    fall = ['thing:cleft_fall_%d' % i for i in (1, 2, 3)]
    spoil = ['thing:cleft_spoil_%d' % i for i in (1, 2)]
    return [
        {'id': 'evt:daily', 'trigger': 'daily',
         'effects': ([{'lua': clear}] if DAILY_BITS else []) + [{'set': {'var': {'map_var': 'spring_used'}, 'value': 0}}],
         'notes': 'Once a day: the hot spring (an HP restoration; the shrine and the cairn are daily for the party by '
                  'Xeen.usedToday, D-70).'},
        {'id': 'evt:outpost_state', 'trigger': 'load', 'condition': {'qbit': 'outpost_burned'},
         'effects': [{'hide': ['thing:outpost_hide_1', 'thing:outpost_hide_2', 'thing:outpost_hide_3']}],
         'notes': 'x7.orc_outpost: the burnt outpost stays burnt (outpost_burned 116160).'},
        {'id': 'evt:cleft_state', 'trigger': 'load', 'condition': {'qbit': 'cleft_open'},
         'effects': [{'hide': fall}, {'show': spoil}], 'else_effects': [{'show': fall}, {'hide': spoil}],
         'notes': "D-40 question 3: the cleft's two states (xd17.cleft_open 116140): the fallen rock in it, or "
                  'cleared to its sides.'},
    ]
