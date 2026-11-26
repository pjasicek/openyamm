"""D3 Sandcaster and the Aging Forest, L3/L4: the towns' plots, the structures, actors and events. A5, 2026-11-20
(seventh session), after X4's places.py.

Used by gen.py. Positions come from gen_l1.py (the approved L1 with D-28) unless written here. Cells [x, y].
Textures: the sandcaster kit (level_generation/xeen_art/kits/sandcaster.yml): MM8 t07 sandstone in three grades, MM6
hc pink ashlar for the guilds and the wizard quarter, t30 for the walls and gates, MM6 tents for the stalls, A6's xs*
signs. Three original lines from the source with their aaze reference (noted beside them).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
import math
import os

import yaml

import gen_l1 as L1
import kit as K
import land as LD

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
WORLD = os.path.join(ROOT, 'assets_dev/worlds/xeen')


def live(stem, env):
    """A neighbour or a dungeon is live when its map is installed in the world (or the env override says so)."""
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) or os.environ.get(env) == '1'


D4_LIVE = live('xeen_d4.odm', 'D3_D4_LIVE')            # not built: the north edge sealed by a sign (phase 4)
DUNGEON = {k: live('xeen_%s.blv' % k, 'D3_%s_LIVE' % k.upper()) for k in ('dd18', 'dd19', 'dd07')}
# the inside points of the dungeon doors (x, y, z, direction in DEGREES), from their lanes: None until given
# (or a named arrival of the dungeon's studio.yml, `arrival: entrance:<id>`, preferred)
INSIDE = {'dd18': 'entrance:d3_shaft', 'dd19': 'entrance:d3_guild_gate', 'dd07': 'entrance:d3_door'}   # DD-18: A8's shaft ladder foot
# (0, 128, 0) south; DD-07: A7's (-2496, 0, 0) facing east, its way out to (15360, 9216, 1888) facing west

# ---------------------------------------------------------------- the world's rows
HOOKS = yaml.safe_load(open(os.path.join(WORLD, 'data_tables/quest_hooks.yml')))
USED = set()
MISSING = set()


def hook_lua(name):
    assert name in HOOKS, 'A3 has no hook %s' % name
    USED.add(name)
    return 'XeenQuests.hook("%s")' % name


def hook(name):
    return {'lua': hook_lua(name)}


def player_bit(name):
    """A once-per-character bit from A3's registry (`player_bits`, map D3: the quest files and the map's own file in
    source/npcs, QUESTS_FORMAT section 5); None (and a request) if missing."""
    files = [os.path.join(WORLD, d, f) for d in ('source/quests', 'source/npcs')
             for f in sorted(os.listdir(os.path.join(WORLD, d))) if f.endswith('.yml')]
    for path in files:
        q = yaml.safe_load(open(path)) or {}
        for k, v in (q.get('player_bits') or {}).items():
            if k == name and isinstance(v, dict) and v.get('map') == 'D3':
                return v['id']
    MISSING.add('player bit %s (map D3)' % name)
    return None


PEASANTS_M = ['371', '368', '362']    # MMerge peasants (MM7), as X4's townsfolk
PEASANTS_F = ['377', '350', '354']
HORNET, SWARM = '11350', '11351'      # A2's Hell Hornet 35, Hornet Swarm 42 (placed, the Aging Forest only)
CORNELIUS = 5247                      # A4: the outdoor Perception teacher, no house

_TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/d3.yml')))
HOUSE = {h['id']: h for h in _TOWN['houses']}
SEALED = 'The way in is sealed. (Not open yet.)'


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lua_str(text)}


def lua_str(text):
    return '"%s"' % text.replace('\\', '\\\\').replace('"', '\\"')


def daily(sid, effects, again):
    """D-70 Q2: a temporary source works once a day for the whole party (Xeen.usedToday / Xeen.markToday, every member
    by evt.ForPlayer(Players.All)); a second use the same day gives `again` and nothing else."""
    key = 'd3_' + sid.split(':', 1)[1]
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s") evt.ForPlayer(Players.All)' % key}] + effects,
            'else_effects': again}


WATER = [{'text': 'The water is cool and refreshing.'}]     # aaze0011:17 (D-70)
NOBODY = [{'text': 'No one seems to be listening.'}]       # aaze0011:21 (D-70)


def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d


def sign(sid, at, title, text, height=224, width=160, **kw):
    d = {'id': sid, 'kind': 'sign', 'at': [round(at[0], 3), round(at[1], 3)], 'height': height, 'width': width,
         'title': title, 'effects': [msg(text)]}
    d.update(kw)
    return d


def dungeon_way(key, hook_name=None, sealed=None):
    """into (+ the hook as condition) when the dungeon is installed and its inside point given; else the hook (if
    any) and a sealed line (D2's rule)."""
    if DUNGEON[key] and INSIDE[key]:
        a = INSIDE[key]
        if isinstance(a, str):
            w = {'into': {'map': 'xeen_%s.blv' % key, 'arrival': a}}
        else:
            w = {'into': {'map': 'xeen_%s.blv' % key, 'at': list(a[:3]), 'facing': a[3] * 2048 // 360}}
        if hook_name:
            w['condition'] = {'lua': hook_lua(hook_name)}
        return w
    text = sealed or SEALED
    if hook_name:
        return {'effects': [{'lua': 'if %s then evt.SimpleMessage(%s) end' % (hook_lua(hook_name), lua_str(text))}]}
    return {'effects': [msg(text)]}



def asked_dungeon_way(key, hook_name, ask, sealed):
    """D-72 (D4 74's shape): a door whose hook's own line ends on the question. The hook first, then Yes/No buttons
    (the hook's line is the prompt's text; `ask` shows only if the hook wrote none); Yes moves, No and Escape stay.
    Sealed with the hook and a line while the dungeon is not installed."""
    w = dungeon_way(key)
    if 'into' not in w:
        return dungeon_way(key, hook_name, sealed)
    # F16 / D-90 (A5 s29, 2026-11-22): the standard entrance window asks, its line the trans.txt row of the hook's
    # line (level_generation/projects/xeen/common/entrance.py); no Yes/No of the map's own, no hook window before it
    return dict(w)

# ---------------------------------------------------------------- the sandcaster kit's grades (plot `textures`)
T07A = {'wall': 't07a01', 'window': 't07a02c', 'door': 't07a03a', 'post_left': 't07a10a', 'post_right': 't07a10a',
        'roof': 't07a05', 'trim': 't07a11a', 'gable': 't07a01', 'ridge': 't07a11b'}
# Texture fit (merge point 16, D-41; tenth session, as X6): the t07b panels carry a footing band meant once at a
# wall's foot, and t07a01b / t07c04c / t07c07 a corbel course at their top that does not meet itself up the wall: the
# rows above the lowest are plain t07a01 (the same adobe, seamless both ways; `plain_upper`), as are the parapets and
# gables; the lowest row's corbel course then reads as a string course between storeys
T07B = {'wall': 't07b01', 'window': 't07b04a', 'door': 't07a03a',   # F2: t07b03c is one wing; t07a03a a single door
         'post_left': 't07b07', 'post_right': 't07b06',
        'roof': 't07b02', 'trim': 't07a11a', 'gable': 't07a01', 'ridge': 't07a11a', 'parapet': 't07a01'}
T07C = {'wall': 't07a01b', 'window': 't07c04c', 'door': 't07c03b', 'post_left': 't07c07', 'post_right': 't07c07',
        'roof': 'desrf2a', 'trim': 't07a11b', 'gable': 't07a01', 'ridge': 't07a11b', 'parapet': 't07a01'}
# hcwindo (one window per storey) laid once per bay of the lowest row, stretched to the bay; the rows above plain hcwall
HC = {'wall': 'hcwall', 'window': {'texture': 'hcwindo', 'fit': True, 'size': [128, 256]}, 'door': 'hcsmdr',
      'post_left': 'hcw1le', 'post_right': 'hcw1re', 'roof': 'desrf2a', 'trim': 't07a11b', 'gable': 'hcwall',
      'ridge': 't07a11b'}


def plain_bays(length, tex='t07a01'):
    """A plain row of `tex` for a wall this long, in as many bays as the studio asks (96-192 wide, 128 drawn)."""
    lo, hi = -(-int(length) // 192), int(length) // 96
    return [tex] * max(lo, min(hi, round(length / 128)))


def plain_upper(parts, tex):
    """The rows above the lowest of a T07B or T07C part in plain t07a01 (D-41: an edge panel never stacks; the
    corbel course once): each box part over 256 high gets `upper_walls` of plain t07a01 on its four walls."""
    if tex.get('wall') not in ('t07b01', 't07a01b'):
        return parts
    for part in parts:
        if 'size' in part and part.get('wall_height', 256) > 256 and 'posts' not in part:
            du, dv = part['size']
            rows = upper_rows if part.get('wall_height', 256) >= 512 else plain_bays
            part['upper_walls'] = {'s': rows(du), 'n': rows(du), 'e': rows(dv), 'w': rows(dv)}
    return parts


def upper_rows(length):
    """An upper storey of a house two storeys high or more: plain t07a01 with the ochre grade's window t07a02c (the
    same adobe round it, seamless both ways) in every other bay, walls at the ends."""
    bays = plain_bays(length)
    return [('t07a02c' if k % 2 and k < len(bays) - 1 else b) for k, b in enumerate(bays)]
T30 = {'wall': 't30c01', 'window': 't30a04a', 'door': 't07c03b', 'post_left': 't30a06', 'post_right': 't30a07',
       'roof': 't07b02', 'trim': 't07a11a', 'gable': 't30c01', 'ridge': 't07a11a'}


def tent(k):
    c = {1: 'tentwal1', 2: 'tentwal2', 3: 'tentwal3', 7: 'tentwal7a'}[k]
    return {'wall': c, 'window': c, 'door': {1: 'tentdor1', 2: 'tentdor1', 3: 'tentdor3', 7: 'tentdor7a'}[k],   # F2: tentdor7 is 256 wide
            'post_left': c, 'post_right': c, 'roof': {1: 'tentrf1', 2: 'tentrf2', 3: 'tentrf3', 7: 'tentrf2'}[k],
            'trim': c, 'gable': c, 'ridge': c}


GRADE = {'poor': T07B, 'plaster': T07A, 'rich': T07C, 'stone': HC, 'castle': HC}

# service buildings: (shape, textures, sign)
SERVICE = {
    # D-92 (A4, 2026-11-22): every service hangs its kind's sign, a guild its school's (never sgspell)
    'building:sc_lucio_jetty': ('sky_stair', T07A, 'sgdock'),
    'building:sc_guild_mind': ('guild', HC, 'sgmind'),
    'building:sc_guild_spirit': ('guild', HC, 'sgspirit'),
    'building:sc_guild_light': ('guild', HC, 'sglight'),
    'building:sc_magic': ('hip', T07C, 'xsmagic'),
    'building:sc_alchemist': ('flat2', T07A, 'xspotions'),
    'building:sc_temple': ('temple', T07C, 'xstemple'),
    'building:sc_training': ('court', T07A, 'xstraining'),
    'building:sc_tavern': ('court', T07C, 'xstavern'),
    'building:sc_weapons': ('flat2', T07C, 'xsweapons'),
    'building:sc_armour': ('flat2', T07A, 'xsarmour'),
    'building:sc_stables': ('barn', T07B, 'xscaravan'),
    'building:wq_guild_dark': ('guild', HC, 'sgdark'),
    'building:wq_magic': ('guild', HC, 'xsmagic'),
    'building:celia_derek_cottage': ('flat', T07B, None),
    'building:thaddeus_hut': ('flat', T07B, None),
}
STALL_SIGNS = {1: 'xsstfood', 2: 'xsstrobes', 3: 'xsstneck', 4: 'xsstbelts', 5: 'xsstboots', 6: 'xscaleb'}
STALL_TENTS = {1: 2, 2: 7, 3: 3, 4: 1, 5: 2, 6: 3}

# the wizard quarter (D-28: a raised walled terrace, towers at most a storey over the guild row), its doors on half
# cells round an open court; the stair comes up its south face between houses 4637 and 4638
QUARTER = [
    ('building:wq_guild_dark', None, 4613, [2, 2], [40.5, 20.5], 'e'),
    ('building:wq_magic', None, 4614, [2, 1.5], [44.5, 20.5], 's'),
    ('building:wq_houses', 1, 4615, [1.5, 1.5], [40.5, 25], 'e'),
    ('building:wq_houses', 2, 4616, [1.5, 1.5], [43, 25], 'n'),
    ('building:wq_houses', 3, 4617, [1.5, 1.5], [45, 23.5], 'w'),
]
QUARTER_STAIR = [[42.5, 29.4], [42.5, 27.05]]
# the Sky Stair's tiers (u0 from each side, v0 from the front, bottom, wall height; map units on its 2 x 2 plot at
# [27.5, 20.5] facing south): 1,536 in all, the top tier 544 x 256 against the north side
SKY_PLOT = (27.5, 20.5)
SKY_TIERS = [(48, 48, 0, 448), (112, 288, 448, 384), (176, 528, 832, 384), (240, 720, 1216, 320)]
SKY_TOP = 1536
GATE_W, GATE_H = 256, 256     # the gates' openings: two 128 x 256 wings (t30a03b1/b2) fill one exactly
CITY_WALL_H = 288     # eighth session: lowered from 512 so the terrace's roofs, the guilds and the quarter show
DD19_GATE = (43.5, 20.15)
# D-42: the guild precinct north of the quarter's wall (x 40-47), and DD-19's return point on D3 (A8: (-10496, 22150,
# 1728) facing south = cell (43.5, 20.74) on the quarter terrace, kept clear: no prop, no spawn marker)
PRECINCT_AT, PRECINCT_SIZE, PRECINCT_H = (40.55, 15.3), (6.0, 3.7), 1424
DD19_RETURN = (43.5, 20.74)
# the south alley's three houses moved half a cell south for the stair (D-28's quarter)
MOVED = {4637: ([40, 28.5], [1.5, 1]), 4638: ([43.5, 28.5], [1, 1]), 4639: ([45.5, 28.5], [1, 1])}
CELIA = L1.HUTS[0]
GATES = {'south': ((36.5, 39), (1, 0), (0, 1)), 'east': ((47, 31.5), (0, 1), (1, 0))}   # mid, along, out of town
CORNER_TOWERS = [(27, 20), (39.5, 20), (47, 27.5)]   # F19: over the joints of the four walls
SQUARE = [[33, 27], [40, 27], [40, 33], [33, 33]]
MIRROR = (33.6, 31.6)
OMID_WELL = (38.4, 31.2)
YARD_ARRIVAL = (39.5, 43.0)
DD18_SHAFT = (30, 32)
EAST_TOWER = (97, 46)
OAK = (53, 65)


# the hung signs at their pictures' size (texture fit: sgspell is 64 x 64, the stall boards 128 x 32)
SIGN_SIZE = {'sgspell': [64, 64], 'xscaleb': [128, 32], 'xscaravan': [128, 64]}
SIGN_SIZE.update({k: [64, 64] for k in ('sgmind', 'sgspirit', 'sglight', 'sgdark', 'sgdock')})
SIGN_SIZE.update({k: [128, 32] for k in ('xsstfood', 'xsstrobes', 'xsstneck', 'xsstbelts', 'xsstboots')})


def house_parts(kind, facing, fp, sign_tex=None):
    F, D = fp[0] * 512, fp[1] * 512
    door = {'part': 'body', 'wall': facing}
    signs = {}
    if sign_tex:
        signs = {'signs': [{'wall': facing, 'bay': 0, 'texture': sign_tex, 'hang': True,
                            'size': SIGN_SIZE.get(sign_tex, [128, 64]),
                            'out': 48, 'bottom': 160}]}
    if kind in ('flat', 'flat2'):
        b = K.box('body', facing, fp, 48, 64, F - 96, D - 112, roof='flat', parapet=64,
                  wall_height=384 if kind == 'flat' else 576)
        b.update(signs)
        return [b], door
    if kind == 'court':
        a = K.box('body', facing, fp, 48, 48, F - 96, int(D * 0.55), roof='flat', parapet=64, wall_height=448)
        a.update(signs)
        w = K.box('wing', facing, fp, int(F * 0.5), int(D * 0.55) - 32, int(F * 0.5) - 80, int(D * 0.45) - 16,
                  roof='flat', parapet=64, wall_height=320)
        return [a, w], door
    if kind == 'hip':
        b = K.box('body', facing, fp, 64, 64, F - 128, D - 128, roof='hip', roof_pitch=26, wall_height=448)
        b.update(signs)
        return [b], door
    if kind == 'guild':
        b = K.box('body', facing, fp, 48, 112, F - 96, D - 160, roof='gable', ridge_along=K.ALONG[facing],
                  roof_pitch=36, wall_height=512,
                  porches=[{'wall': facing, 'depth': 112, 'posts': 32, 'height': 256, 'floor': 16}])
        b.update(signs)
        return [b], door
    if kind == 'temple':
        b = K.box('body', facing, fp, 64, 64, F - 128, D - 128, roof='flat', parapet=96, wall_height=512)
        b.update(signs)
        c = K.centre(facing, fp, F / 2, D / 2)
        dome = {'id': 'dome', 'shape': 'round', 'at': [round(c[0]), round(c[1])], 'radius': int(min(F, D) * 0.3),
                'sides': 12, 'bottom': 512, 'wall_height': 160, 'roof': 'cone', 'roof_pitch': 38, 'windows': 'none',
                'textures': {'roof': 'desrf3a'}}
        return [b, dome], door
    if kind == 'barn':
        parts, door = K.shape('barn', facing, fp, 'poor', sign=sign_tex, roof_tex='t07b02')
        for part in parts:
            for sg in part.get('signs', []):
                sg['size'] = SIGN_SIZE.get(sg['texture'], sg['size'])
        return parts, door
    if kind == 'stall':
        b = K.box('body', facing, fp, 80, 80, F - 160, D - 160, roof='hip', roof_pitch=24, wall_height=288,
                  windows='none')
        b.update(signs)
        return [b], door
    if kind == 'sky_stair':
        # the Sky Stair (D-28; eighth session, the lane review: it read as a plain six-storey block): a stepped
        # stair-tower in the city's sandstone, four tiers each set back from the square (south) with a parapet round
        # its terrace, the top tier against the north side; Lucio's timber jetty lies on the top (structures)
        parts = []
        for k, (u0, v0, bottom, wh) in enumerate(SKY_TIERS):
            # each tier's back 16 in from the one below (one plane would z-fight)
            p = K.box('body' if k == 0 else 'tier%d' % (k + 1), facing, fp, u0, v0, F - 2 * u0, D - 48 - v0 - 16 * k,
                      roof='flat', wall_height=wh, windows='alternate' if k < 3 else 'none')
            if k:
                p['bottom'] = bottom
            if k < len(SKY_TIERS) - 1:
                p['parapet'] = 64
            if k == 0:
                p.update(signs)     # D-92: Lucio's anchor board on the lowest tier, by the door
            parts.append(p)
        return parts, door
    if kind == 'tower':
        # the wizard quarter's towers: round, a cone a storey over the guild row's ridges (D-28)
        r = int(min(F, D) * 0.4)
        t = {'id': 'body', 'shape': 'round', 'at': [F // 2, D // 2], 'radius': r, 'sides': 10, 'wall_height': 512,
             'roof': 'cone', 'roof_pitch': 48, 'windows': 'alternate'}
        return [t], {'part': 'body'}
    raise ValueError(kind)


# ---------------------------------------------------------------- plots
plots_by_space = {}
doors = []            # (plot id, house, door cell, cell 0.9 out, title)
footprints = []


def closed_gate(house):
    h = HOUSE[house]
    if h.get('opens') == 'q-d14.done':
        return {'condition': {'qbit': 'quarter_open'}, 'else_effects': [msg(h['closed_text'])]}
    if h.get('opens') == 'm30.done':
        return {'condition': {'qbit': 'lucio_open'}, 'else_effects': [msg(h['closed_text'])]}
    return {}


def add_plot(space, bid, index, house, fp, at, facing, kind, tex, sign_tex=None, door_to=None):
    plot = {'building': bid}
    if index:
        plot['index'] = index
    plot.update({'at': list(at), 'facing': facing, 'kit': 'plaster', 'textures': dict(tex)})
    turn = 0
    if kind == 'tower':
        plot['facing'] = 's'
        turn = K.TURN_OF[facing]
        if turn > 180:
            turn -= 360
        if turn:
            plot['turn'] = turn
    if door_to:
        plot['door_to'] = door_to
    parts, door = house_parts(kind, facing, fp, sign_tex)
    plot['parts'] = plain_upper(parts, tex)
    plot['door'] = door
    plot['house'] = house
    plot['title'] = HOUSE[house]['name']
    plot.update(closed_gate(house))
    if house == 4647:
        # A3's q-c22.cottage: the hook refuses until q-c22 is done, then moves Celia and Derek in (q-c22.moved);
        # it is `once` with no else line, so every later knock enters on the bit it set (s25, A3's Q-C22 answer)
        plot['condition'] = {'any': [{'qbit': 112443}, {'lua': hook_lua('q-c22.cottage')}]}
    plots_by_space.setdefault(space, []).append(plot)
    pid = bid + ('#%d' % index if index else '')
    footprints.append((pid, K.footprint(at[0], at[1], facing if kind != 'tower' else 's', fp, turn)))
    if kind == 'tower':
        dc = K.door_cell(at[0], at[1], 's', fp, turn, -0.08)
        out = K.door_cell(at[0], at[1], 's', fp, turn, 0.9)
    else:
        dc = K.door_cell(at[0], at[1], facing, fp, 0, 0.0)
        out = K.door_cell(at[0], at[1], facing, fp, 0, 0.9)
    doors.append((pid, house, dc, out, plot['title']))


HOUSE_KINDS = ['flat', 'court', 'flat2', 'flat', 'hip']
for bid, service, house, fp, at, facing, door_to, kit in L1.SANDCASTER:
    kind, tex, sg = SERVICE[bid]
    space = 'zone:caravan_yard' if bid == 'building:sc_stables' else 'town:sandcaster'
    add_plot(space, bid, None, house, fp, at, facing, kind, tex, sg, door_to)
for i, (house, fp, at, facing, kit) in enumerate(L1.SC_HOUSES, 1):
    if house in MOVED:
        at, fp = MOVED[house]
    kind = 'flat' if fp[0] * fp[1] <= 1.0 else HOUSE_KINDS[i % len(HOUSE_KINDS)]
    if kind == 'court' and min(fp) < 1.5:
        kind = 'flat2'
    add_plot('town:sandcaster', 'building:sc_houses', i, house, fp, at, facing, kind, GRADE[kit])
for bid, idx, house, fp, at, facing in QUARTER:
    if idx:
        add_plot('zone:wizard_quarter', bid, idx, house, fp, at, facing, 'tower', HC)
    else:
        kind, tex, sg = SERVICE[bid]
        add_plot('zone:wizard_quarter', bid, None, house, fp, at, facing, kind, tex, sg)
for idx, house, angle, facing, fp in L1.CROSS_STALLS:
    add_plot('town:crossroads', 'building:xr_stall', idx, house, fp, L1.stall_at(angle, fp), facing, 'stall',
             tent(STALL_TENTS[idx]), STALL_SIGNS[idx])
for space, bid, service, house, fp, at, facing, kit in L1.HUTS:
    kind, tex, sg = SERVICE[bid]
    add_plot(space, bid, None, house, fp, at, facing, kind, tex, sg)


def check_plots():
    bad = []
    for i, (a, p) in enumerate(footprints):
        for (b, q) in footprints[i + 1:]:
            if any(K.inside(v, q) for v in p) or any(K.inside(v, p) for v in q):
                bad.append('plots overlap: %s and %s' % (a, b))
    for line in [ln for _, ln, w, _ in L1.ROADS if w == 'road']:
        for pid, poly in footprints:
            if pid.startswith('building:xr_stall'):
                continue          # the stalls stand between the six roads at the ring's edge (checked by eye)
            if K.line_hits_poly(line, poly, 0.45):
                bad.append('road against %s' % pid)
    if bad:
        raise SystemExit('\n'.join(bad))


check_plots()


# ---------------------------------------------------------------- structures
def structures():
    out = []
    S = out.append
    # ======== Sandcaster's wall on its terrace's edge, two gates with the pass (Q-D8) =============================
    wall_tex = {'wall': 't30c01', 'top': 't30a05c'}
    # the ring is open at the south gate (its towers and leaves close it), so its ends never overlap (A5: a ring
    # closed on itself made a coplanar pair at the joint); the east gate is an arch in the wall
    # eighth session: the ring in four walls, each level at CITY_WALL_H over the highest ground under it (one wall's
    # top is level: as one ring it stood at the quarter's and the dunes' height, 600 over the terrace in the south)
    # F19 (the user 2026-11-22, wall pieces meet flush): the four walls' tops differ (each level over its own
    # ground), so each joint stands inside a corner tower (CORNER_TOWERS), and the south gate's walls end inside its
    # towers (they stopped at the towers' edge: a 32 slit beside each tower)
    sides = [('west', [[35.9, 39], [27, 39], [27, 20]], None),
             ('north', [[27, 20], [39.5, 20]], None),
             ('quarter', [[39.5, 20], [47, 20], [47, 27.5]], None),
             ('east', [[47, 27.5], [47, 39], [37.1, 39]], {'at': list(GATES['east'][0]), 'width': GATE_W,
                                                       'height': GATE_H, 'arch': 'round', 'sides': 8})]
    for side, line, gate in sides:
        # the quarter's side 32 higher: its walk would lie in the plane of the guild gate's frame top
        w = {'id': 'thing:city_wall_%s' % side, 'kind': 'wall', 'line': line,
             'height': CITY_WALL_H + (32 if side == 'quarter' else 0),
             'thickness': 192, 'battlements': True, 'textures': dict(wall_tex), 'title': "Sandcaster's walls"}
        if gate:
            w['gates'] = [gate]
        S(w)
    for k, (cx, cy) in enumerate(CORNER_TOWERS):
        S({'id': 'thing:corner_tower_%d' % (k + 1), 'kind': 'building', 'at': [round(cx - 0.4, 3), round(cy - 0.4, 3)],
           'size': [0.8, 0.8], 'kit': 'plaster', 'door': 'none', 'title': "Sandcaster's walls",
           'textures': dict(T30),
           'parts': [{'id': 'tower', 'at': [32, 32], 'size': [345, 345], 'wall_height': 512, 'roof': 'flat',
                      'battlements': True, 'windows': 'none'}],
           'notes': 'F19: a corner tower over the joint of two walls of different height.'})
    for g, (mid, al, nrm) in GATES.items():
        # two square gate towers either side of each gate
        for k, s in enumerate((-1, 1)):
            cx, cy = mid[0] + al[0] * s * 0.95, mid[1] + al[1] * s * 0.95
            S({'id': 'thing:gate_tower_%s_%d' % (g, k + 1), 'kind': 'building', 'at': [round(cx - 0.45, 3),
                                                                                     round(cy - 0.45, 3)],
               'size': [0.9, 0.9], 'kit': 'plaster', 'door': 'none', 'title': "Sandcaster's %s gate" % g,
               'textures': dict(T30),
               'parts': [{'id': 'tower', 'at': [32, 32], 'size': [396, 396], 'wall_height': 768, 'roof': 'flat',
                          'battlements': True, 'windows': 'alternate'}]})
        # eighth session (the double-door rule, lanes/README): each gate is a 256-wide round-arched opening closed by
        # two leaves side by side, MM8's paired gate wings (t30a03b1 the left, t30a03b2 the right, 128 x 256: one
        # picture each, untiled), outside and inside; a click hides all four. Outside, A3's q-d8.sandcaster_gate
        # (the pass); inside, open. The south gate's opening is a gatehouse wall between its towers.
        if g == 'south':
            S({'id': 'thing:south_gatehouse', 'kind': 'wall', 'line': [[35.9, 39], [37.1, 39]], 'height': 448,
               'thickness': 192, 'battlements': True, 'textures': dict(wall_tex), 'title': "Sandcaster's south gate",
               'gates': [{'at': list(mid), 'width': GATE_W, 'height': GATE_H, 'arch': 'round', 'sides': 8}]})
        leaves = ['thing:%s_gate_%s_%s' % (g, side, half) for side in ('outer', 'inner') for half in ('l', 'r')]
        # both pairs stand inside the arch on the terrace's edge, so each leaf is exactly 256 over level ground
        for side, off in (('outer', 0.1), ('inner', -0.1)):
            c = (mid[0] + nrm[0] * off, mid[1] + nrm[1] * off)
            # seen from outside the outer pair's left is along -al; from inside the inner pair's left is along +al
            for half, sgn in (('l', -1), ('r', 1)):
                a = sgn if side == 'outer' else -sgn
                p0 = (c[0] + al[0] * min(a, 0) * 0.25, c[1] + al[1] * min(a, 0) * 0.25)
                p1 = (p0[0] + al[0] * 0.25, p0[1] + al[1] * 0.25)
                tex = 't30a03b1' if half == 'l' else 't30a03b2'
                leaf = {'id': 'thing:%s_gate_%s_%s' % (g, side, half), 'kind': 'wall', 'height': GATE_H,
                        'thickness': 32, 'line': [[round(p0[0], 4), round(p0[1], 4)], [round(p1[0], 4), round(p1[1], 4)]],
                        'textures': {'wall': tex, 'top': '7trimda'}, 'title': "Sandcaster's %s gate" % g,
                        'effects': [{'hide': lid} for lid in leaves] + [{'text': 'The gate swings open.'}]}
                if side == 'outer':
                    leaf['condition'] = {'lua': hook_lua('q-d8.sandcaster_gate')}
                S(leaf)
    # ======== the square: paving, the mirror, Omid's deep well, the original lines (aaze0031) ==================
    # platforms.through (2026-11-24): the quarter terrace's foot rose 54 through the paving's north-east corner (x
    # 39.5-39.75, y 27.25-27.6); the paving starts half a cell further south, where the land is level
    S({'id': 'thing:sc_square', 'kind': 'platform', 'at': [36.5, 30.25], 'size': [3328, 2560], 'height': 16,
       'textures': {'top': 't30a05c', 'wall': 't30a05a'}, 'title': "Sandcaster's square"})
    S({'id': 'thing:sc_mirror', 'kind': 'portal', 'at': list(MIRROR), 'radius': 112, 'sides': 12, 'turn': 90,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror', 'effects': [{'lua': 'Xeen.useMirror(4612, eventId, continueStep)'}],
       'notes': "A4 4612, The Mirror of Sandcaster (qbit 119009): the Town Portal anchor's square."})
    S({'id': 'thing:omid_well', 'kind': 'well', 'at': list(OMID_WELL), 'title': "Omid's deep well",
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       **daily('thing:omid_well', [{'add': {'var': 'IntellectBonus', 'value': 5}},
                                   {'text': 'Something at the bottom hums. You feel clever, for a while. '
                                            '(+5 Intellect until you rest)'}], WATER)})
    # the Vulture Repellant board by the alchemist's door and the scrawl under it (dark/aaze0031:19 and :25)
    S(sign('thing:repellant_board', (39.35, 27.35), 'Vulture Repellant',
           'Special today! Vulture Repellant, only 25,000 gold!   (Scratched underneath: Vulture Repellant '
           "doesn't work.)", notes='Original lines: dark/aaze0031:19 and dark/aaze0031:25.'))
    # the wizards' warning at the foot of the quarter stair (dark/aaze0031:29)
    S(sign('thing:quarter_notice', (43.3, 29.1), 'Notice',
           'The wizards in this town are sensitive to insults. Watch what you say!',
           notes='Original line: dark/aaze0031:29.'))
    # ======== the wizard quarter (D-28): retaining wall with a parapet, the stair, the guild gate (DD-19) =====
    q_tex = {'wall': 'hcwall', 'top': 't30a05c'}
    # F19: both ends run into the city wall's body (they stopped 8 short of it: a slit)
    for k, line in enumerate([[[39.88, 20.1], [39.88, 27.12], [42.05, 27.12]], [[42.95, 27.12], [46.9, 27.12]]]):
        S({'id': 'thing:quarter_wall_%d' % (k + 1), 'kind': 'wall', 'line': line,
           'height': LD.QUARTER_H - LD.TOWN_H + 128, 'thickness': 128, 'textures': dict(q_tex),
           'title': 'The wizard quarter'})
    S({'id': 'thing:quarter_stair', 'kind': 'stairs', 'line': QUARTER_STAIR, 'width': 384,
       'rise': LD.QUARTER_H - LD.TOWN_H, 'textures': {'wall': 'hcwall', 'top': 't30a05c'},
       'title': 'The quarter stair'})
    # hclgdr is one picture of a double door made for a 256 x 256 opening (eighth session, the double-door rule)
    gate = {'id': 'thing:dd19_gate', 'kind': 'doorway', 'at': list(DD19_GATE), 'turn': 0, 'width': 256,
            'height': 256, 'depth': 96, 'floor': LD.QUARTER_H, 'textures': {'door': 'hclgdr', 'wall': 'hcwall'},
            'title': 'The guild gate', 'hint': 'Wizard Quarter',
            **asked_dungeon_way('dd19', 'q-d14.quarter_gate', 'Enter?',
                                "The guild gate is barred from the far side. Voices behind it argue about whose turn "
                                "it is to open it. (Not open yet.)"),
            'notes': "DD-19 Wizard Quarter (A8): A3's q-d14.quarter_gate (its line ends on 'Enter?'), then Yes/No "
                     "buttons (D-72); Yes enters at DD-19's entrance:d3_guild_gate (0, 384, 0) facing north."}
    S(gate)
    # ======== the guild precinct north of the wall (D-42): what DD-19 is, seen from the town ====================
    # a walled court behind the guild gate with two gabled halls in the quarter's pink hc ashlar and a covered bridge
    # between them over the court's middle wall; no door and nothing that enters (the way in is the guild gate).
    # North of the wall the dunes fall to about 1,260-1,480 (land.py): the plot levels its ground at PRECINCT_H; the
    # court walls stand on it, with short pieces up the slope to the city wall's foot so the court is closed
    hall = {'roof': 'gable', 'ridge_along': 'ns', 'roof_pitch': 40, 'wall_height': 640, 'windows': 'alternate'}
    S({'id': 'thing:guild_precinct', 'kind': 'building', 'at': list(PRECINCT_AT), 'size': list(PRECINCT_SIZE),
       'kit': 'plaster', 'door': 'none', 'floor': PRECINCT_H, 'title': "The guild's precinct",
       'textures': dict(HC),
       'parts': [dict(hall, id='hall_w', at=[96, 160], size=[1152, 1728]),
                 dict(hall, id='hall_e', at=[1824, 160], size=[1152, 1728]),
                 {'id': 'bridge', 'at': [1232, 704], 'size': [608, 384], 'bottom': 384, 'wall_height': 256,
                  'roof': 'gable', 'ridge_along': 'ew', 'roof_pitch': 34, 'windows': 'none'}],
       'notes': "D-42: DD-19's precinct (an open-sky court and the guild halls) seen over the quarter's north wall; "
                'no entry from outside.'})
    pw = {'wall': 'hcwall', 'top': 't30a05c'}
    x0, x1, xm = 40.45, 46.65, 43.55
    y0, ys, yw = 15.2, 19.0, 19.85          # north side; where the level court ends; into the city wall's body
    # F19: each wall one piece from the court's north side to the city wall's body, its top following the land (the
    # short pieces up the slope stood higher than the court walls they met: a step at each joint)
    for k, line in enumerate([[[x0, yw], [x0, y0], [x1, y0], [x1, yw]], [[xm, y0], [xm, yw]]]):
        S({'id': 'thing:precinct_wall_%d' % (k + 1), 'kind': 'wall', 'line': line, 'height': 288,
           'thickness': 96, 'top': 'follow', 'textures': dict(pw), 'title': "The guild's precinct"})
    # ======== the Sky Stair: Lucio's timber jetty with mooring posts on its top (D-28; D-5.3: departs only) ====
    # eighth session: the deck lies on the top tier (no posts down to the land: they read as a crane's legs) and
    # reaches out north over the city wall into thin air; six mooring posts and a kerb make it read as a jetty
    u0 = SKY_TIERS[-1][0]
    v_front = SKY_TIERS[-1][1]
    x0, x1 = SKY_PLOT[0] + u0 / 512.0 - 0.1, SKY_PLOT[0] + 2 - u0 / 512.0 + 0.1
    y_south = SKY_PLOT[1] + 2 - v_front / 512.0
    top = LD.TOWN_H + SKY_TOP + 48
    S({'id': 'thing:jetty_deck', 'kind': 'deck', 'outline': [[round(x0, 3), 19.1], [round(x1, 3), 19.1],
                                                             [round(x1, 3), round(y_south, 3)],
                                                             [round(x0, 3), round(y_south, 3)]],
       'level': top, 'thickness': 48, 'kerb': 48, 'posts': 0, 'textures': {'deck': '7trimda'},
       'title': "Lucio's Jetty",
       'notes': "D-28: a timber deck on the Sky Stair's top, reaching out north over the city wall into thin air."})
    for k, (x, y) in enumerate([(x0 + 0.08, 19.25), (x1 - 0.2, 19.25), (x0 + 0.08, 19.85), (x1 - 0.2, 19.85),
                                (x0 + 0.08, 20.45), (x1 - 0.2, 20.45)]):
        S({'id': 'thing:jetty_post_%d' % (k + 1), 'kind': 'deck', 'title': 'Mooring post',
           'outline': [[round(x, 3), round(y, 3)], [round(x + 0.11, 3), round(y, 3)],
                       [round(x + 0.11, 3), round(y + 0.11, 3)], [round(x, 3), round(y + 0.11, 3)]],
           'level': top + 224, 'thickness': 224, 'kerb': 0, 'posts': 0, 'textures': {'deck': '7trimda'}})
    # ======== DD-18's street shaft against Barticus' Gym (D-27): sealed until A8's inside point ===============
    S({'id': 'thing:dd18_shaft', 'kind': 'hatch', 'form': 'pit', 'at': list(DD18_SHAFT), 'size': [512, 512],
       'height': 48, 'textures': {'shell': 't30a05a', 'door': '7solid01'}, 'title': 'An iron lid',
       'hint': 'Sandcaster Sewer',
       **dungeon_way('dd18', None, 'The iron lid is bolted from below. Something down there smells of liniment. '
                                   '(Not open yet.)'),
       'notes': "DD-18 Sandcaster Sewer (D-27): the street shaft under Barticus' sign, down to DD-18's "
                'entrance:d3_shaft (A8: the ladder foot (0, 128, 0) facing south); sealed with its line while DD-18 '
                'is not installed.'})
    # ======== the caravan yard (D-28): a fenced pocket outside the south gate, in sight of it ====================
    S(K.fence('thing:yard_fence', [[38.1, 42.2], [38.1, 44.1], [43.4, 44.1], [43.4, 40.15], [43.0, 40.15]]))
    S({'id': 'thing:yard_trough', 'kind': 'platform', 'at': [42.4, 43.5], 'size': [640, 192], 'height': 96,
       'textures': {'top': 'wtrtyl', 'wall': 't30a05a'}, 'title': 'Water trough'})
    for i, (d, at) in enumerate([('haybale2', (42.8, 41.0)), ('haybale2', (42.8, 41.35)),
                                 ('bigbarel', (40.75, 42.75)), ('smlbarel', (41.05, 42.75))]):
        S(deco('thing:yard_prop_%d' % (i + 1), d, at))
    # ======== the Crossroads: the trough well in the ring, the ring's paving =====================================
    S({'id': 'thing:market_well', 'kind': 'well', 'at': list(L1.CROSS), 'title': "The Crossroads' well",
       'frame': {'height': 200}, 'effects': [{'text': 'Refreshing!'}]})
    # ======== signposts at the forks (arms only: not POIs, D-20)
    arms = {
        'junction:gate_fork': [('Sandcaster', 'n'), ('Sprite Forest', 'w'), ('The Crossroads', 'e')],
        'junction:crossroads': [('Sandcaster', 'n'), ('Sprite Forest', 'w'), ('Wrath Bridge', 'e'),
                                ('Venom Pond', 's')],
        'junction:east_fork': [('Lakeside', 'n'), ('The Eastern Tower', 'e'), ('The Crossroads', 'w')],
        'junction:venom_fork': [('Venom Pond', 's'), ('The river', 'e'), ('The Crossroads', 'n')],
        'junction:forest_fork': [('The Howling Woods', 'w'), ('The rim', 's'), ('The Crossroads', 'n')],
    }
    sign_at = {'junction:gate_fork': (37.4, 44.9), 'junction:crossroads': (58.0, 41.6),
               'junction:east_fork': (82.9, 46.1), 'junction:venom_fork': (76.0, 66.4),
               'junction:forest_fork': (41.0, 79.0)}
    for i, j in enumerate(L1.SIGNPOSTS, 1):
        S({'id': 'thing:signpost_%d' % i, 'kind': 'sign', 'at': list(sign_at[j]), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms[j]]})
    if not D4_LIVE:
        S(sign('thing:north_road_end', (88.9, 21.0), 'Sign',
               'Lakeside: north, over the pass. A rockfall has closed the road beyond the saddle. Turn back.',
               notes='D4 is not built (phase 4): the north edge has no travel until it is.'))
    # ======== the obelisk on its dune knoll ======================================================================
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [50.5, 27.5], 'height': 768, 'title': 'Obelisk',
       'effects': [hook('obelisks.d3')]})
    # ======== Vespar's ruin by the caravan road (Q-D8: the emerald handle) ======================================
    S({'id': 'thing:vespar_ruin', 'kind': 'building', 'at': [44.6, 46.8], 'size': [2, 1.5], 'kit': 'plaster',
       'door': 'none', 'title': 'A roadside ruin', 'textures': dict(T07A),
       'ruin': {'height': [128, 448], 'gaps': 0.35, 'thickness': 48, 'seed': 7},
       # tenth session: the plain ochre grade (a ruin's broken walls lay their panels to the full height, so the
       # t07b footing band stood 1.5 times up them)
       'parts': [{'id': 'r', 'at': [64, 64], 'size': [896, 640], 'wall_height': 448, 'roof': 'none',
                  'windows': 'alternate'}]})
    S(deco('thing:vespar_rubble', 'rock65', (45.6, 48.6), title='Rubble', effects=[hook('q-d8.handle')]))
    # ======== the Wrath Spring at the gorge head, the gorge's cave fall ========================================
    S({'id': 'thing:spring_fall', 'kind': 'waterfall', 'line': [[80.25, 20.75], [81.6, 20.75]], 'top': 1440,
       'foot': LD.RIVER_LVL, 'width': 640, 'back': 512, 'pool': 384, 'spread': 1.2, 'rocks': False,
       'title': 'The Wrath Spring',
       'notes': 'The river bursts from a cave in the gorge head.'})
    S({'id': 'thing:wrath_spring', 'kind': 'well', 'at': [84.2, 22.4], 'title': 'The Wrath Spring',
       'frame': {'height': 160},
       **daily('thing:wrath_spring', [{'add': {'var': 'MightBonus', 'value': 5}},
                                      {'text': 'The water is angry. So, briefly, are you. (+5 Might until you rest)'}],
               WATER),
       'notes': "A spring basin on the gorge's lip, fed by the spray (the spring path's end)."})
    S(deco('thing:spring_sound', 'Snd_Brook', (81.0, 21.4)))
    gorge_rock(S)
    crest_rock(S)
    # ======== Wrath Bridge, the falls over the rim, the Rim Watch ==============================================
    # D-170 (2026-11-25): the west end stands 24 over a pad that runs 1.5 cells on up the bank (`pad_beyond`,
    # common/wild.py): the road graded through the end lifted an end-cell pad back up and the end's edge lay on it
    S({'id': 'thing:wrath_bridge', 'kind': 'bridge', 'line': [[73.6, 46], [77.75, 46]], 'width': 640,
       'raise': 24, 'pad_beyond': 1.5,
       'arches': {'count': 2, 'rise': 160, 'form': 'segment', 'pier_width': 256}, 'kerb': 96,
       'textures': {'deck': 't30a05c', 'side': 't30c01', 'pier': 't30c01'}, 'title': 'Wrath Bridge'})
    # U-12/D-112 (agent xeen-rimmap-c, 2026-11-23): the line on the river's mouth, pouring straight east over the rim
    # (the river ends at (104, 64); written along the edge for the old sea, the rim kit put its lip at y 62.9)
    S({'id': 'thing:wrath_falls', 'kind': 'waterfall', 'line': [[103.2, 64.0], [104.6, 64.0]], 'top': LD.RIVER_LVL,
       'foot': 96, 'width': 1024, 'spread': 1.3, 'title': 'The Wrath Falls',
       'notes': 'The River of Wrath drops off the east rim into the stars (the signature view).'})
    S(deco('thing:falls_sound', 'Snd_Brook', (102.4, 63.6)))
    S({'id': 'thing:rim_watch', 'kind': 'building', 'at': [100.2, 56.2], 'size': [1.6, 1.6], 'kit': 'plaster',
       'door': 'none', 'title': 'The Rim Watch', 'textures': dict(T30),
       'parts': [{'id': 'post', 'shape': 'round', 'at': [410, 410], 'radius': 320, 'sides': 8, 'wall_height': 448,
                  'ruin': {'height': [128, 448], 'gaps': 0.3, 'seed': 3}, 'roof': 'none', 'title': 'The Rim Watch',
                  'effects': [msg("Scratched in the stone: \"Watched the glow for nine years. It never moved. "
                                  "Neither did the sergeant.\"")]}]})
    S({'id': 'thing:rim_locker', 'kind': 'chest', 'at': [100.6, 58.2], 'title': "The watchman's locker",
       'chest': {'level': 3, 'random_items': 2}})
    # ======== the Eastern Tower (DD-07) on its knoll at its planned place (D-28) ===============================
    tx, ty = EAST_TOWER
    # tenth session (texture fit, D-41): hkm3b is a one-storey panel (a skull frieze over a bone footing) and stacked
    # 3.5 times up each tier; the shafts are now the dark seamless stone gtrlwal1 (as X5's Darkstone Tower) with the
    # skull frieze once, a storey under each tier's top, and the yellow-glass hkm3elw windows only in the top band
    stone = {'wall': 'gtrlwal1', 'window': 'gtrlwal1', 'post_left': 'gtrlwal1', 'post_right': 'gtrlwal1',
             'trim': 'gtrlwal1', 'roof': 'gtrlwal1'}
    band = {'wall': 'hkm3b', 'window': 'hkm3b', 'post_left': 'hkm3b', 'post_right': 'hkm3b', 'trim': 'gtrlwal1',
            'roof': 'gtrlwal1'}
    tower = {'id': 'thing:eastern_tower', 'kind': 'building', 'at': [tx - 1.5, ty - 1.5], 'size': [3, 3],
             'kit': 'plaster', 'facing': 'w', 'floor': LD.KNOLL_H, 'title': 'The Great Eastern Tower',
             'textures': {'wall': 'gtrlwal1', 'window': 'hkm3elw', 'door': 'xvtdoor', 'roof': 'xtslate',
                          'trim': 'gtrlwal1'},
             # D-180 rule a (2026-11-26): the door at least as wide as DD-07's way back out (192 x 320) and within 64
             # of its height: a 192 bay 320 high in the west side (was the default 157 x 256); the door the tower kit's
             # xvtdoor laid once over the leaf (classic_kit.py, D-196)
             'parts': [{'id': 'base', 'shape': 'round', 'at': [768, 768], 'radius': 608, 'sides': 12,
                        'wall_height': 640, 'roof': 'none', 'windows': 'none', 'textures': dict(stone),
                        'door_height': 320,
                        'walls': {'9': [['wall', round((2 * 608 * math.sin(math.pi / 12) - 192) / 2, 3)], ['door', 192],
                                        ['wall', round((2 * 608 * math.sin(math.pi / 12) - 192) / 2, 3)]]},
                        'upper_walls': {'9': [['wall', round((2 * 608 * math.sin(math.pi / 12) - 192) / 2, 3)],
                                              ['wall', 192],
                                              ['wall', round((2 * 608 * math.sin(math.pi / 12) - 192) / 2, 3)]]}},
                       {'id': 'base_band', 'shape': 'round', 'at': [768, 768], 'radius': 608, 'sides': 12,
                        'bottom': 640, 'wall_height': 256, 'roof': 'none', 'windows': 'none', 'textures': dict(band)},
                       {'id': 'mid', 'shape': 'round', 'at': [768, 768], 'radius': 512, 'sides': 12, 'bottom': 896,
                        'wall_height': 640, 'roof': 'none', 'windows': 'none', 'textures': dict(stone)},
                       {'id': 'mid_band', 'shape': 'round', 'at': [768, 768], 'radius': 512, 'sides': 12,
                        'bottom': 1536, 'wall_height': 256, 'roof': 'none', 'windows': 'none', 'textures': dict(band)},
                       {'id': 'top', 'shape': 'round', 'at': [768, 768], 'radius': 448, 'sides': 12, 'bottom': 1792,
                        'wall_height': 256, 'roof': 'none', 'windows': 'none', 'textures': dict(stone)},
                       {'id': 'top_band', 'shape': 'round', 'at': [768, 768], 'radius': 448, 'sides': 12,
                        'bottom': 2048, 'wall_height': 256, 'roof': 'cone', 'roof_pitch': 68, 'windows': 'alternate',
                        'textures': {'wall': 'hkm3b', 'post_left': 'hkm3b', 'post_right': 'hkm3b'}}],
             'door': {'part': 'base', 'wall': '9'},
             **dungeon_way('dd07', 'q-d18.tower_door',
                           'The key turns, and something heavy inside the door does not. (Not open yet.)'),
             'notes': "DD-07 (A7, Act IV): A3's q-d18.tower_door (Q-D19's key), then DD-07's entrance:d3_door."}
    S(tower)
    S({'id': 'thing:tower_cart', 'kind': 'crate', 'at': [92.4, 42.6], 'title': "The tower mages' supply cart",
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:tower_cart_wreck', 'dec24x', (91.8, 42.3)))
    # ======== the river meadows: the pear hut (D-28), the wayside shrine =========================================
    fruit_huts(S)
    S({'id': 'thing:wayside_shrine', 'kind': 'building', 'at': [68.6, 57.6], 'size': [1, 1], 'kit': 'plaster',
       'title': 'Wayside shrine of the desert sun', 'door': 'none', 'textures': dict(T07C),
       'parts': [{'id': 's', 'at': [96, 96], 'size': [320, 320], 'wall_height': 288, 'posts': 32, 'roof': 'hip',
                  'roof_pitch': 40, 'windows': 'none', 'title': 'Wayside shrine of the desert sun',
                  **daily('thing:wayside_shrine', [{'add': {'var': 'FireResistanceBonus', 'value': 10}},
                                                   {'text': 'A faded sun painted on the stone, still warm. (+10 Fire '
                                                            'resistance until you rest)'}], NOBODY)}]})
    # ======== Venom Pond: Thaddeus's Fountain of Youth (Q-D18), the drowned skiff ==============================
    S({'id': 'thing:fountain_youth', 'kind': 'fountain', 'at': [79.4, 76.6], 'title': 'The Fountain of Youth',
       'tiers': [[96, 48]], 'textures': {'wall': 't07a01b'},
       'condition': {'qbit': 'fountain_restored'},
       'effects': [hook('q-d18.fountain')],
       'else_effects': [hook('q-d18.fountain'), {'set': {'var': 'PoisonedGreen', 'value': 1}}],
       'notes': "A3's q-d18.fountain: venom before q-d18.done (the map's poison), youth after (Xeen.renewAges)."})
    S({'id': 'thing:drowned_skiff', 'kind': 'chest', 'at': [70.2, 88.9], 'title': "A drowned skiff's locker",
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:skiff_hull', 'dec24x', (69.6, 88.6)))
    S({'id': 'thing:fountain_protection', 'kind': 'fountain', 'at': [95, 95], 'title': 'Fountain of Great Protection',
       'tiers': [[96, 48]], 'textures': {'wall': 't30c01'},
       **daily('thing:fountain_protection', [{'add': {'var': 'ArmorClassBonus', 'value': 10}},
                                             {'text': 'The water tastes of iron and old oaths. (+10 Armor class until '
                                                      'you rest)'}], WATER)})
    # ======== the Aging Forest: the great oak (D-28: off the road by its lane), Cornelius, the fig hut ========
    S(deco('thing:great_oak', '7tree08', OAK, title='The great oak',
           **daily('thing:great_oak', [{'add': {'var': 'PersonalityBonus', 'value': 5}},
                                       {'text': 'You rest a hand on the old bark. You feel older and wiser. Mostly '
                                                'older. (+5 Personality until you rest)'}],
                   [{'text': 'The old bark is warm under your hand, and nothing more.'}])))
    S({'id': 'thing:aged_skeleton', 'kind': 'chest', 'at': [52.4, 88.3], 'title': "A young man's satchel",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'A skeleton in a young man\'s clothes, under the falling leaves. A note: "Just a nap."'}]})
    S(deco('thing:aged_bones', '7dec18', (51.8, 88.0)))
    S(deco('thing:edge_cairn', 'rock26', (46.2, 101.2), title="Pilgrims' cairn",
           **daily('thing:edge_cairn', [{'add': {'var': 'LuckBonus', 'value': 5}},
                                        {'text': 'A cairn on the lip of the world. You add a stone. (+5 Luck until you '
                                                 'rest)'}],
                   [{'text': 'You have added your stone today.'}])))
    # ======== the Howling Woods: the howling stone, the mantis mound, the smugglers' rope =======================
    S(deco('thing:howling_stone', 'rock68', (24.2, 80.2), title='The howling stone',
           effects=[msg('The wind sings through a hole in the stone. It is only the wind. The wolves left years ago. '
                        'Probably.')]))
    S(deco('thing:howl_sound', 'Snd_Howl', (24.6, 80.6)))
    S({'id': 'thing:mantis_mound', 'kind': 'chest', 'at': [25.4, 66.4], 'title': "An explorer's pack",
       'chest': {'level': 3, 'random_items': 2}})
    for i, at in enumerate([(24.6, 65.6), (26.0, 65.9), (25.0, 67.2)]):
        S(deco('thing:mound_%d' % (i + 1), '7rock08', at))
    S({'id': 'thing:smugglers_bundle', 'kind': 'chest', 'at': [30.2, 101.4], 'title': "A smuggler's bundle",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'A rope tied to a stake runs over the rim into nothing. Someone meant to come back.'}]})
    S(deco('thing:smugglers_stake', 'dec13', (30.9, 102.6)))
    # ======== the desert edge: the caravan well, the swallowed caravan; the crest: the courier ===============
    S({'id': 'thing:caravan_well', 'kind': 'well', 'at': [63.5, 28.5], 'title': 'The caravan well',
       'frame': {'height': 200},
       **daily('thing:caravan_well', [{'add': {'var': 'EnduranceBonus', 'value': 5}},
                                      {'text': 'Deep, cold water that tastes of stone. (+5 Endurance until you rest)'}],
               WATER)})
    S({'id': 'thing:caravan_wreck', 'kind': 'crate', 'at': [57.6, 25.9], 'title': "A swallowed caravan's strongbox",
       'chest': {'level': 3, 'random_items': 3},
       'effects': [{'text': 'Half a wagon sticks out of the sand. A worm hole beside it, wide as a door.'}]})
    S(deco('thing:caravan_wagon', 'dec24x', (57.0, 25.3)))
    S({'id': 'thing:courier_satchel', 'kind': 'chest', 'at': [98.6, 21.2], 'title': "A courier's satchel",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': "A courier from Lakeside took the high path round Wrathtop and never came down."}]})
    S(deco('thing:courier_bones', '7dec18', (98.1, 21.5)))
    # ======== dressing in the towns: barrels in pairs against walls, palms in yards (DRESSING.md) =============
    # F40 (2026-11-24): the first pair stood inside Saffron House (sc_houses#10, x 32.09-32.88, y 33.59-34.91, as
    # built); now against its south wall, outside
    for i, (p1, p2) in enumerate([((32.3, 35.03), (32.62, 35.03)), ((39.75, 33.6), (39.75, 33.9)),
                                  ((45.6, 34.85), (45.9, 34.85)), ((27.85, 25.3), (28.15, 25.3)),
                                  ((63.85, 46.6), (63.85, 46.9))]):
        S(deco('thing:barrel_%d' % (i + 1), 'bigbarel', p1))
        S(deco('thing:barrel_%d_pair' % (i + 1), 'smlbarel', p2))
    for i, at in enumerate([(32.2, 36.4), (44.0, 30.9), (28.6, 34.9), (46.0, 36.6), (34.6, 38.3), (43.6, 26.0)]):
        S(deco('thing:sc_palm_%d' % (i + 1), ['tree02', 'tree05', 'tree07'][i % 3], at))
    for i, at in enumerate([(56.4, 40.0), (63.8, 40.2), (56.0, 48.2), (64.4, 44.8)]):
        S(deco('thing:xr_palm_%d' % (i + 1), ['tree03', 'tree06'][i % 2], at))
    return out


# ---------------------------------------------------------------- rock (ninth pass, the lane review of sheet4)
ROCK = {'wall': 'cwb1', 'top': 'cwb1'}     # the world's rock (MM7's cwb1, the studio's rock for waterfalls in mm7 tiles)
# the gorge's rock faces, from the built land (`oymap export` of build_w, ninth pass): each a block of rock 384 thick in
# the cell between a rim node and the floor's outermost node (the cut's one-node wall), 0.75 of a cell out from the rim,
# its face sheer on the river from the floor up, its top (a wall's top is level at its highest ground plus its height)
# about 96 under the rim, so the turf's lip shows over the rock: (key, line, height), each height read from the build
# (its highest ground: the export's top less the height given).
GORGE_FACES = [('w1', [[78.75, 21.0], [78.75, 24.5]], 456), ('w2', [[77.75, 24.5], [77.75, 30.5]], 204),
               ('w3', [[76.75, 30.5], [76.75, 36.5]], 284), ('e1', [[82.25, 21.0], [82.25, 27.5]], 156),
               ('e2', [[81.25, 27.5], [81.25, 33.5]], 140), ('e3', [[80.25, 33.5], [80.25, 37.5]], 360),
               ('head_w', [[78.5, 20.75], [80.35, 20.75]], 220), ('head_e', [[81.65, 20.75], [83.5, 20.75]], 32)]
# P2 F26 (town_fit_check, agent xeen-rimmap-c, 2026-11-23): the faces' feet stood 45-88 over the gorge floor before
# them (`walls.hollow`: e1 and the head's two slabs) and the east rim's turf rose 56-58 over e1-e3's tops
# (`walls.buried`, over the check's 48). The feet go 128 deeper (`raise`, the same top), and e1-e3's tops 24 higher:
# the turf's lip still shows over the rock, about 32 over it. key: (raise, extra height)
GORGE_FIT = {'e1': (-128, 152), 'e2': (0, 24), 'e3': (0, 24), 'head_w': (-128, 128), 'head_e': (-128, 128)}


def gorge_rock(S):
    """The gorge's walls in rock, and the head: the spring's fall in the head's gap (its own slabs off), so it comes
    out of the rock face."""
    for key, line, height in GORGE_FACES:
        lift, more = GORGE_FIT.get(key, (0, 0))
        S({'id': 'thing:gorge_face_%s' % key, 'kind': 'wall', 'line': line, 'thickness': 384, 'height': height + more,
           **({'raise': lift} if lift else {}),
           'textures': dict(ROCK), 'title': 'The Wrath Spring' if key.startswith('head') else 'The gorge'})


# the ground each crag stands on (an obelisk's foot, read from the build, ninth pass): a crag tops out at Wrathtop's
# 3,392 at most (D-28); one with less than 320 of rock over its foot is left out
GROUND = {'crag_1': 2848, 'crag_2': 3120, 'crag_3': 2784, 'crag_4': 2912, 'crag_5': 2528, 'crag_6': 2640,
          'crag_7': 2976, 'crag_8': 2760, 'crag_9': 2848, 'crag_10': 2816, 'crag_11': 2608, 'crag_12': 2752,
          'crag_13': 2336, 'crag_14': 2832}


# the crest's crags: rock pinnacles on the knobs' flanks and in the notches, each topping out at about D-28's crest
# heights (3,100-3,400): (cell, width, turn)
CRAGS = [((91.5, 28.5), 576, 20), ((93.0, 25.5), 512, -15), ((94.5, 23.0), 448, 35), ((97.5, 25.5), 640, 10),
         ((99.0, 23.0), 448, -30), ((100.5, 27.5), 576, 25), ((101.0, 31.5), 512, -10), ((99.5, 34.5), 640, 40),
         ((97.0, 36.5), 512, -25), ((95.0, 32.0), 576, 15), ((93.0, 34.5), 448, -35), ((97.0, 30.5), 512, 5),
         ((92.0, 31.5), 448, 30), ((100.0, 37.5), 448, -20)]


# F59 (2026-11-25, town_fit_check things.overhang): a crag on the crest's flank stood on the land at its middle and
# hung 29-233 over the slope falling away under the rest of its foot (the build of 2026-11-24): each such crag sinks
# its foot below the lowest land under it (the fall, a 32 step and 32 more) and grows by as much, the same top
SINK = {'crag_3': 160, 'crag_4': 192, 'crag_5': 192, 'crag_8': 96, 'crag_10': 64, 'crag_11': 128, 'crag_13': 288}


def crest_rock(S):
    """The Wrath crest's rock: pinnacles (obelisks in the world's rock: a broad tapering shaft, a low tip) along the
    ridge and in its notches."""
    for k, ((x, y), w, turn) in enumerate(CRAGS, 1):
        h = int(min(1024, 3392 - 64 - GROUND['crag_%d' % k]) // 32 * 32)     # the build sets a shaft 64 lower
        if h < 320:
            continue
        w = min(w, h)                          # an obelisk is at least as high as wide
        sink = SINK.get('crag_%d' % k, 0)
        S({'id': 'thing:crag_%d' % k, 'kind': 'obelisk', 'at': [x, y], 'height': h + sink, 'width': w, 'taper': 0.45,
           'tip': int(w * 0.35), 'turn': turn, 'textures': dict(ROCK), 'title': 'The Wrath crest',
           **({'raise': -sink} if sink else {})})


def fruit_huts(S):
    """D-28 (4): the two forbidden-fruit huts, each its own look and line, +2 and a condition once per character
    (player bits; A2's boons, A3's registry). A bit not registered yet: the hut gives its line only (blocked)."""
    huts = [
        ('pear', (87.2, 64.6), 'The pear hut', 'BaseMight', 'Weak',
         'A basket of pears on the sill of a whitewashed hut. "The pear of plenty." You feel stronger, and then very '
         'tired.', '+2 Might (permanent), and Weak',
         {'kind': 'building', 'size': [1.4, 1.4], 'textures': {'wall': 'hhp1b', 'roof': 'hhp2rf'},
          'parts': [{'id': 'hut', 'shape': 'round', 'at': [358, 358], 'radius': 288, 'sides': 10, 'wall_height': 256,
                     'roof': 'cone', 'roof_pitch': 40, 'windows': 'none'}]},
         [('7tree19', (89.0, 64.2)), ('7dec41', (88.4, 65.9))]),
        ('fig', (60.0, 72.0), 'The fig hut', 'BaseIntellect', 'Insane',
         'Figs in a bowl by the door of a mossy log hut. "The fig of foresight." You see everything. Everything sees '
         'you.', '+2 Intellect (permanent), and Insane',
         {'kind': 'building', 'size': [1.6, 1.2], 'textures': {'wall': 'xdbark', 'roof': 'hhp2rf'},
          'parts': [{'id': 'hut', 'at': [64, 64], 'size': [672, 480], 'wall_height': 256, 'roof': 'gable',
                     'roof_pitch': 34, 'ridge_along': 'ew', 'windows': 'none'}]},
         [('tree61a', (61.9, 71.6)), ('dec05', (60.8, 73.1))]),
    ]
    for key, at, title, stat, cond, text, boon, shape, dress in huts:
        bit = player_bit('fruit_%s' % key)
        b = {'id': 'thing:%s_hut' % key, 'at': [at[0] - shape['size'][0] / 2, at[1] - shape['size'][1] / 2],
             'kit': 'poor', 'door': 'none', 'title': title}
        b.update(shape)
        S(b)
        click = {'id': 'thing:%s_basket' % key, 'kind': 'decoration', 'decoration': dress[1][0],
                 'at': [round(dress[1][1][0], 3), round(dress[1][1][1], 3)], 'title': title}
        if bit is not None:
            click['condition'] = {'not': {'player_bit': bit}}
            click['effects'] = [{'add': {'var': stat, 'value': 2}}, {'set': {'var': cond, 'value': 1}},
                                {'player_bit': bit}, {'text': '%s (%s)' % (text, boon)}]
            click['else_effects'] = [{'text': 'You have had your share. The rest look far less tempting now.'}]
        else:
            click['effects'] = [{'text': text.split('"')[0] + '(The basket is covered. Not yet.)'}]
            click['notes'] = 'Blocked: the player bit fruit_%s (A3/A2) is not registered yet.' % key
        S(click)
        S(deco('thing:%s_tree' % key, dress[0][0], dress[0][1]))


# ---------------------------------------------------------------- actors
def actors():
    out = []
    A = out.append
    for m, at, c, s, g, n in L1.ACTORS:
        A({'monster': m, 'at': list(at), 'count': c, 'spread': s, 'group': 60 + g, 'hostile': True, 'notes': n})
    # Sandcaster's people and the Crossroads' shoppers: D-96's villagers (gen.py fills these places, villagers.yml)
    out.extend(V.slots(14))
    # Cornelius the Leprechaun in his glade (A4's NPC 5247, the outdoor Perception teacher)
    A({'monster': '362', 'npc': CORNELIUS, 'at': [40.2, 72.2], 'spread': 0, 'group': 53,
       'notes': 'Cornelius the Leprechaun (teachers_plan cornelius).'})
    return out


def events():
    return [
        {'id': 'evt:sky', 'trigger': 'load', 'effects': [{'lua': 'Xeen.applyDarksideSky()'}],
         'notes': "Darkside's sky by the sun's stage (A3's helper)."},
    ]
