"""X6 Desert of the Sphinx, L3/L4: the hamlet's plots, the structures, actors and events. A5, 2026-11-20, after D3's
places.py.

Used by gen.py. Positions come from gen_l1.py (the approved L1 with D-31) unless written here. Cells [x, y].
Textures: Sphinx Wells in the cloudside_town kit's plain grade (hhm2 ochre plaster, hhp poor rubble, chb1 fieldstone
for the coach yard); Castle Basenji in the towers kit (hwm2 grey rubble under black timber, D-31); the two sphinxes in
MM6's pyramid stone (egy*); A6's xs* signs. Original lines from the source with their aaze reference beside them.
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


_MAP_STATS = open(os.path.join(WORLD, 'data_tables/map_stats.txt')).read()


def live(stem, env):
    """A dungeon is live when its map is installed in the world and has its map_stats row (A2), so the game can
    load it (tenth session: XD-14/XD-15 were installed before their rows); or the env override says so."""
    if os.environ.get(env) in ('0', '1'):
        return os.environ.get(env) == '1'
    return os.path.exists(os.path.join(WORLD, 'maps', stem)) and ('\t%s\t' % stem) in _MAP_STATS


DUNGEON = {k: live('xeen_%s.blv' % k, 'X6_%s_LIVE' % k.upper()) for k in ('xd14', 'xd15', 'xd20', 'fd02')}
# the inside points of the dungeon doors: a named arrival of the dungeon's studio.yml (A7, D-37), or (x, y, z,
# direction in DEGREES); None until given. A7 (tenth session): XD-14 entrance:x6_gate, its way out lands at
# (-13312, 15104, 2593); XD-15 entrance:x6_paws, out at (9216, 9728, 1409); XD-20 entrance:x6_yard when built, back
# to (12128, -15872, 1504) facing west. FD-02 (D-57): entrance:x6_door; its way out comes back to X6's
# entrance:fd02_door (-12288, -10240), 256 before the breast's leaves (whole cells only), facing east.
INSIDE = {'xd14': 'entrance:x6_gate', 'xd15': 'entrance:x6_paws', 'xd20': 'entrance:x6_yard', 'fd02': 'entrance:x6_door'}

# lane S's sand-fall decoration (D-31): placed only once it is bound in the world; no stand-in until then
_DECOS = open(os.path.join(WORLD, 'models/decorations.yml')).read()
SANDFALL_LIVE = 'xeen_sandfall' in _DECOS or os.environ.get('X6_SANDFALL_LIVE') == '1'
# D-35: facing 0 pours north; since merge point 15 a decoration's `turn` is written as its facing, so the falls stand
# on the cove's north wall turned 180, pouring south (SANDFALLS_SOUTH), in sight of the crest at [38, 96].
# SANDFALLS is the old south-wall row (pouring north), kept for reference.
SANDFALLS = [(25.3, 92.0), (28.5, 92.0), (31.7, 92.0)]
# lane S's sphinx models (xeen_sphinx_north row 4010, xeen_sphinx_south row 4011; the contract
# level_generation/decorations/xeen_sphinx_claude/integration/sphinx_collision.yml): when both are bound, the masses go;
# a minimal carrier block keeps each door (its front 8 inside the door plane, the rest inside the model's breast), the
# models stand at S's origins turned to their facings (`turn` is clockwise: facing = -turn). D-141 (F61): the models
# are solid by their own LOD2 proxies (worlds/xeen/models/decorations.yml `collision_model`), no barrier rings.
SPHINX_MODELS_LIVE = (('xeen_sphinx_north' in _DECOS and 'xeen_sphinx_south' in _DECOS)
                      if os.environ.get('X6_SPHINX_MODELS') not in ('0', '1')
                      else os.environ.get('X6_SPHINX_MODELS') == '1')
SPHINX_CONTRACT = os.path.join(ROOT, 'level_generation/decorations/xeen_sphinx_claude/integration/sphinx_collision.yml')
SANDFALLS_SOUTH = [(25.3, 84.0), (28.5, 84.0), (31.7, 84.0)]

# ---------------------------------------------------------------- the world's rows
HOOKS = yaml.safe_load(open(os.path.join(WORLD, 'data_tables/quest_hooks.yml')))
USED = set()
MISSING = set()

# Player bits for the once-per-character devices (proposed by A5 for A3 to register in npcs/x6.yml, as A7's XD-07
# and XD-08 bits were): the daily ones are cleared for every member by evt:daily_bits.
PB = {'oasis_fountain': 11330, 'shrine_energy': 11331, 'well_accuracy': 11332, 'waters_power': 11333,
      'sun_stones': 11334, 'caravan_cairn': 11335}
DAILY_BITS = ['waters_power']   # D-70 Q2: the Well of Accuracy, the sun stones and the cairn are daily() now


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


def reflector(name):
    """A Reflector (M37), D-144 (F69b): a click calls A3's hook, whose line goes on the status line (`status: true`:
    before M36 its fail text, then once its experience, after that its else text). The source's "Reflector. Activate?"
    was a free Yes/No whose No changed nothing."""
    return [hook(name)]


def msg(text):
    return {'lua': 'evt.SimpleMessage(%s)' % lua_str(text)}


def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d


def sign(sid, at, title, text, height=224, width=160, **kw):
    d = {'id': sid, 'kind': 'sign', 'at': [round(at[0], 3), round(at[1], 3)], 'height': height, 'width': width,
         'title': title, 'effects': [msg(text)]}
    d.update(kw)
    return d


SEALED = 'The way in is sealed. (Not open yet.)'


def sound(name):
    """AU's sound (devdocs/xeen/AUDIO.md), played where the party stands."""
    return 'evt.PlaySoundName(%s)' % lua_str(name)


def dungeon_way(key, hook_name=None, sealed=None, stir=None):
    """into (+ the hook as condition) when the dungeon is installed and its inside point given; else the hook (if any)
    and a sealed line (D2's and D3's rule)."""
    if DUNGEON[key] and INSIDE[key]:
        a = INSIDE[key]
        if isinstance(a, str):   # a named arrival of the dungeon's studio.yml (`entrance:<id>`), preferred
            w = {'into': {'map': 'xeen_%s.blv' % key, 'arrival': a}}
        else:
            w = {'into': {'map': 'xeen_%s.blv' % key, 'at': list(a[:3]), 'facing': a[3] * 2048 // 360}}
        if hook_name:
            # A hook with `once` answers false (its "stands open" line) after the first time: the door then opens on
            # the bit the hook set, without a second run of the hook (eleventh session, XD-15's q-c9.door).
            h = HOOKS[hook_name]
            if h.get('once'):
                assert len(h['sets']) == 1, hook_name
                w['condition'] = {'any': [{'qbit': list(h['sets'].values())[0]}, {'lua': hook_lua(hook_name)}]}
            else:
                w['condition'] = {'lua': hook_lua(hook_name)}
        if stir:
            w['effects'] = [{'lua': sound(stir)}]
        return w
    text = sealed or SEALED
    if hook_name:
        play = (sound(stir) + ' ') if stir else ''
        return {'effects': [{'lua': 'if %s then %sevt.SimpleMessage(%s) end' % (hook_lua(hook_name), play,
                                                                             lua_str(text))}]}
    return {'effects': [msg(text)]}


def daily(sid, effects, again):
    """D-70 Q2: a temporary source works once a day for the whole party (Xeen.usedToday / Xeen.markToday, every member
    by evt.ForPlayer(Players.All)); a second use the same day gives `again` and nothing else."""
    key = 'x6_' + sid.split(':', 1)[1]
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s") evt.ForPlayer(Players.All)' % key}] + effects,
            'else_effects': again}


def once_per_character(key, effects, again):
    """The device works once for each member (or once a day: DAILY_BITS), else `again`."""
    return {'condition': {'not': {'player_bit': PB[key]}}, 'effects': effects + [{'player_bit': PB[key]}],
            'else_effects': again}


PEASANTS_M = ['371', '368', '362']    # MMerge peasants (MM7), as X4's and D3's townsfolk
PEASANTS_F = ['377', '350', '354']
ARIE, SAUL, SUMMER_DRUID = 4608, 4602, 4601

_TOWN = yaml.safe_load(open(os.path.join(WORLD, 'source/towns/x6.yml')))
HOUSE = {h['id']: h for h in _TOWN['houses']}
GORM_LINE = next(n for n in _TOWN['npcs'] if n['id'] == 4605)['gate_line']

# ---------------------------------------------------------------- the kits' grades (plot `textures`)
# Sphinx Wells in the sandcaster kit (D3's Sandcaster: MM8 t07 sandstone in grades, flat roofs behind parapets); the
# doors MM6's single hc door (the t07 doors are halves of double doors)
OCHRE = {'wall': 't07a01', 'window': 't07a02c', 'door': 'hcsmdr', 'post_left': 't07a10a', 'post_right': 't07a10a',
         'roof': 't07a05', 'trim': 't07a11a', 'gable': 't07a01', 'ridge': 't07b01'}
# Texture fit (merge point 16, D-41): the t07b panels carry a footing band, meant once at a wall's foot: the rows above
# the lowest are plain t07a01 (the same adobe, seamless both ways), as are the parapets and gables
POOR = {'wall': 't07b01', 'window': 't07b04a', 'door': 'hcsmdr', 'post_left': 't07b07', 'post_right': 't07b06',
        'roof': 't07b02', 'trim': 't07a11a', 'gable': 't07a01', 'ridge': 't07a11a', 'parapet': 't07a01'}
RICH = {'wall': 't07a01b', 'window': 't07c04c', 'door': 'hcsmdr', 'post_left': 't07c07', 'post_right': 't07c07',
        'roof': 'desrf2a', 'trim': 't07a11b', 'gable': 't07a01', 'ridge': 't07a11b', 'parapet': 't07a01'}
def plain_bays(length, tex='t07a01'):
    """A plain row of `tex` for a wall this long, in as many bays as the studio asks (96-192 wide, 128 drawn)."""
    lo, hi = -(-int(length) // 192), int(length) // 96
    return [tex] * max(lo, min(hi, round(length / 128)))


def plain_upper(parts, tex):
    """The footing panels' plain rows above the lowest (D-41: an edge panel never stacks): each box part over 256
    high gets `upper_walls` of plain t07a01 on its four walls."""
    if tex.get('wall') != 't07b01':
        return parts
    for part in parts:
        if 'size' in part and part.get('wall_height', 256) > 256 and 'posts' not in part:
            du, dv = part['size']
            part['upper_walls'] = {'s': plain_bays(du), 'n': plain_bays(du), 'e': plain_bays(dv),
                                   'w': plain_bays(dv)}
    return parts
FIELD = {'wall': 'chb1', 'window': 'chbw', 'door': 'hhm1d', 'post_left': 'chb1el', 'post_right': 'chb1er',
         'roof': 'hhm2rf', 'trim': 'trim2_32', 'gable': 'chb1', 'ridge': 'trim2_32'}
BASENJI = {'wall': 'hwm2wall', 'window': 'hwm2bw', 'door': 'hwm2d', 'post_left': 'hwm2el', 'post_right': 'hwm2er',
           'roof': 'hwm2rf', 'trim': 'hwm2bs1', 'gable': 'hwm2b', 'ridge': 'trim11_32'}
SPHINX = {'wall': 'egybiga', 'window': 'egybiga', 'door': 'egydrsmc', 'post_left': 'egywla', 'post_right': 'egywla',
          'roof': 'egywalh', 'trim': 'egywlb', 'gable': 'egybiga', 'ridge': 'egywlb'}
SPHINX_HEAD = dict(SPHINX, wall='egywalh', window='egywalh', gable='egywalh', roof='egywalhb')

WELL_AT = (61.0, 60.85)            # Old Ibb's well, in the street between the tavern and the stables
# on the pond's east shore, beside the oasis track; 0.9 east of the water's edge since 2026-11-24 (at 45.7 its basin
# hung 86 over the bank's slope to the pond, whose nodes keep the water's level: town_fit_check things.overhang)
OASIS_FOUNTAIN = (46.6, 61.2)
NSPHINX = (82.0, 39.0)
SPHINX_DOOR = (82.0, 43.98)        # XD-15 (A7): in the breast's face between the paws, facing south
HOARD = (82.62, 44.7)              # the mound by the east paw, clear of the door's line, within 400 of it
SSPHINX_X0 = 34.0                  # the Southern Sphinx's plot (x 34-40, moved a cell east for the cove)
BASENJI_GATE = (38.0, 33.7)        # XD-14 (A7): in the gatehouse on the terrace at about 2,600, facing south
ARENA_GATE = (88.69, 95.0)          # XD-20 (A7): the portal's door in the cliff, facing west into the yard
YARD_GATE = (83.0, 96.0)           # the yard's desert gate in its west wall (D-8.1)
YARD_ARRIVAL = (86.4, 96.4)
WELLS_ARRIVAL = (63.0, 61.3)


def house_parts(kind, facing, fp, sign_tex=None):
    F, D = fp[0] * 512, fp[1] * 512
    door = {'part': 'body', 'wall': facing}
    signs = {}
    if sign_tex:
        signs = {'signs': [{'wall': facing, 'bay': 0, 'texture': sign_tex, 'hang': True, 'size': [128, 64],
                            'out': 48, 'bottom': 176}]}
    if kind == 'flat':
        b = K.box('body', facing, fp, 48, 64, F - 96, D - 112, roof='flat', parapet=64, wall_height=384)
        b.update(signs)
        return [b], door
    if kind == 'tavern':
        # a flat-roofed tavern with a shade awning on posts along its front (L1: flat roofs with awnings)
        b = K.box('body', facing, fp, 48, 176, F - 96, D - 224, roof='flat', parapet=64, wall_height=448,
                  porches=[{'wall': facing, 'depth': 144, 'posts': 24, 'height': 288, 'floor': 16}])
        b.update(signs)
        w = K.box('wing', facing, fp, int(F * 0.5), int(D * 0.55), int(F * 0.5) - 128, int(D * 0.45) - 16,
                  roof='flat', parapet=48, wall_height=320, windows='none')
        return [b, w], door
    if kind == 'barn':
        # the caravans' long shed: flat roof behind a parapet, an open lean-to stall on posts along its back
        b = K.box('body', facing, fp, 48, 64, F - 96, int(D * 0.62), roof='flat', parapet=64, wall_height=448)
        b.update(signs)
        sh = K.box('shed', facing, fp, 96, int(D * 0.62) + 16, F - 192, int(D * 0.38) - 80, roof='lean_to',
                   wall_height=320, posts=24, windows='none')
        return [b, sh], door
    if kind == 'coach':
        b = K.box('body', facing, fp, 48, 64, F - 96, D - 112, roof='flat', parapet=64, wall_height=448)
        b.update(signs)
        return [b], door
    raise ValueError(kind)


# ---------------------------------------------------------------- plots
plots_by_space = {}
doors = []            # (plot id, house, door cell, cell 0.9 out, title)
footprints = []


def add_plot(space, bid, index, house, fp, at, facing, kind, tex, sign_tex=None, door_to=None):
    plot = {'building': bid}
    if index:
        plot['index'] = index
    plot.update({'at': list(at), 'facing': facing, 'kit': 'plaster', 'textures': dict(tex)})
    if door_to:
        plot['door_to'] = door_to
    parts, door = house_parts(kind, facing, fp, sign_tex)
    plot['parts'] = plain_upper(parts, tex)
    plot['door'] = door
    plot['house'] = house
    plot['title'] = HOUSE[house]['name']
    plots_by_space.setdefault(space, []).append(plot)
    pid = bid + ('#%d' % index if index else '')
    footprints.append((pid, K.footprint(at[0], at[1], facing, fp, 0)))
    dc = K.door_cell(at[0], at[1], facing, fp, 0, 0.0)
    out = K.door_cell(at[0], at[1], facing, fp, 0, 0.9)
    doors.append((pid, house, dc, out, plot['title']))


KINDS = {'building:x6_tavern': ('tavern', RICH, 'xstavern'), 'building:x6_stables': ('barn', POOR, 'xscaravan')}
# L3: the hamlet drawn closer than L1's sketch (town_feel: buildings 1,288 apart against the shipped 162-744)
HAMLET_AT = {'building:x6_tavern': [58, 58], 'building:x6_stables': [61.5, 58], 1: [58.5, 62.5], 2: [61.5, 62.5]}
for bid, service, house, fp, at, facing, door_to, kit in L1.HAMLET:
    kind, tex, sg = KINDS[bid]
    add_plot('town:sphinx_wells', bid, None, house, fp, HAMLET_AT[bid], facing, kind, tex, sg, door_to)
for i, (house, fp, at, facing, kit) in enumerate(L1.HAMLET_HOUSES, 1):
    add_plot('town:sphinx_wells', 'building:x6_houses', i, house, fp, HAMLET_AT[i], facing, 'flat',
             POOR if i == 2 else OCHRE)
_bid, _service, _house, _fp, _at, _facing, _door_to, _kit = L1.COACH
add_plot('zone:coach_yard', _bid, None, _house, _fp, _at, _facing, 'coach', FIELD, 'xscaravan', _door_to)


def check_plots():
    bad = []
    for i, (a, p) in enumerate(footprints):
        for (b, q) in footprints[i + 1:]:
            if any(K.inside(v, q) for v in p) or any(K.inside(v, p) for v in q):
                bad.append('plots overlap: %s and %s' % (a, b))
    if bad:
        raise SystemExit('\n'.join(bad))


check_plots()


# ---------------------------------------------------------------- structures
def structures():
    out = []
    S = out.append
    hamlet(S)
    coach_yard(S)
    northern_sphinx(S)
    southern_sphinx(S)
    basenji(S)
    camps(S)
    devices(S)
    finds(S)
    # signposts at the forks (arms only: not POIs, D-20)
    for i, (at, arms) in enumerate([
            ((54.9, 60.5), [('Burlock and Asp', 'e'), ('Winterkill', 's'), ('Castle Basenji', 'n'),
                            ('The oasis', 'w')]),
            ((80.9, 60.2), [('The Sphinx', 'n'), ('Sphinx Wells', 'w'), ('Burlock', 'e')]),
            ((51.0, 83.1), [('The Warzone', 'e'), ('Winterkill', 's'), ('Sphinx Wells', 'n'),
                            ('The Southern Sphinx', 'w')])], 1):
        S({'id': 'thing:signpost_%d' % i, 'kind': 'sign', 'at': list(at), 'height': 256,
           'arms': [{'title': t, 'toward': d} for t, d in arms]})
    # lane S's sand-falls on the west lip (D-31): only once the decoration is bound (no stand-in)
    if SANDFALL_LIVE:
        for i, at in enumerate(SANDFALLS_SOUTH, 1):
            S(deco('thing:sandfall_%d' % i, 'xeen_sandfall', at, turn=180,
                   notes="Lane S's sand-fall (D-31, D-35): on the cove's north wall at the lip's height, turned 180 "
                         '(A1, merge point 15) to pour south into the cove, its face toward the crest at [38, 96].'))
    return out


def hamlet(S):
    """Sphinx Wells (A4's x6.yml): Old Ibb's well, the camel pen, awnings, barrels by the walls, hay."""
    S({'id': 'thing:wells_well', 'kind': 'well', 'at': list(WELL_AT), 'title': "Old Ibb's well",
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       'effects': [{'text': 'The water is cool and refreshing.'}],
       'notes': 'Original line: xeen/aaze0001:4. "The well is deeper than the Sphinx is tall" (Old Ibb, A4).'})
    # the camel pen behind the stables (north), its gate on the east side
    S(K.fence('thing:camel_pen', [[64.4, 57.75], [64.4, 55.4], [61.6, 55.4], [61.6, 57.75]]))
    S({'id': 'thing:pen_trough', 'kind': 'platform', 'at': [63.0, 56.0], 'size': [640, 160], 'height': 96,
       'textures': {'top': 'wtrtyl', 'wall': 'chb1'}, 'title': 'Water trough'})
    for i, (d, at) in enumerate([('haybale2', (62.0, 57.2)), ('haybale2', (62.35, 57.25)),
                                 ('bigbarel', (58.2, 57.75)), ('smlbarel', (58.5, 57.75)),
                                 ('bigbarel', (59.0, 63.8)), ('smlbarel', (59.3, 63.8)),
                                 ('7dec21', (64.25, 59.75)), ('7dec21', (64.25, 59.45))]):
        S(deco('thing:wells_prop_%d' % (i + 1), d, at))
    # a stall of dates and water skins under an awning by the road (not a service: dressing)
    S(K.stall('thing:date_stall', [55.6, 62.4], 0, kit='timber', roof_tex='hhm2rf'))


def coach_yard(S):
    """D-8.1: a pocket in the Barbaric cliffs (rock shoulders north and south, the cliff at its back: land.py), Gorm's
    coach house and the arena gate only; a short wall between the west shoulders holds the desert gate, barred from
    inside until a party opens it from the desert side (A3's x6.warzone_gate, x6.warzone_gate_open)."""
    # F19 (the user 2026-11-22: a town's walls close it): the short wall stood free on the yard floor and the
    # shoulders north-west and south are walkable slopes, so a party walked round the barred gate. The wall now runs
    # from the north rim's cliff (row 91-92) down the yard's west side and along its south side into the cliff at its
    # back (x 87-90, row 98), its top following the land (tools/xeen/wall_check.py).
    S({'id': 'thing:yard_wall', 'kind': 'wall', 'line': [[83, 91.9], [83, 98.3], [87.3, 98.3]], 'height': 448,
       'thickness': 160, 'top': 'follow',
       'textures': {'wall': 'chb1', 'top': 'cwb'}, 'title': 'The coach yard wall',
       'gates': [{'at': list(YARD_GATE), 'width': 512, 'height': 416}],
       'notes': 'A fieldstone wall from the north rim to the cliff at the back; its gate opens on the coach track.'})
    half = 0.5
    gate_text = 'The yard gate swings open.'
    hide_all = [{'hide': 'thing:yard_gate_%s_%s' % (sd, w)} for sd in ('outer', 'inner') for w in ('n', 's')]
    for side, off in (('outer', -0.3), ('inner', 0.3)):
        x = round(YARD_GATE[0] + off, 3)
        for wing, (a_, b_) in (('n', (YARD_GATE[1] - half, YARD_GATE[1])), ('s', (YARD_GATE[1], YARD_GATE[1] + half))):
            leaf = {'id': 'thing:yard_gate_%s_%s' % (side, wing), 'kind': 'wall', 'height': 384, 'thickness': 32,
                    'line': [[x, a_], [x, b_]], 'textures': {'wall': 'hhm1b1', 'top': 'hhm1b1'},
                    'title': 'The yard gate', 'effects': hide_all + [{'lua': sound('xeen_yard_gate')},
                                                                     {'text': gate_text}]}
            if side == 'outer':
                leaf['effects'] = hide_all + [{'lua': sound('xeen_yard_gate')}, {'lua': hook_lua('x6.warzone_gate')}]
                leaf['notes'] = "D-8.1: the desert side lifts the bar (A3's x6.warzone_gate, once); two plank wings."
            else:
                leaf['condition'] = {'lua': hook_lua('x6.warzone_gate_open')}
                leaf['notes'] = ("D-8.1: barred from the yard side until x6.warzone_gate; before it, Gorm's gate_line "
                                 "(A3's fail text: %s)" % GORM_LINE)
            S(leaf)
    # the arena gate (XD-20): a carved stone portal sunk into the cliff at the yard's back, facing the yard's middle
    arena = {'part': 'portal', 'wall': 'w', 'bay': 2, 'leaves': 2, 'arch': 'round', 'title': 'The Warzone',
             **asked_way('An iron-bound gate cut into the cliff. Beyond it a crowd roars, and something roars '
                         'back.', 'Enter the War Zone?',
                         dungeon_way('xd20', None, 'The gate does not give. A voice behind it: "Not today. The pit is '
                                                   'being raked." (Not open yet.)')),
             'notes': 'XD-20 The Warzone (A7, D-8.1): "Enter the War Zone?" (xeen/aaze0006:4); sealed until XD-20 is '
                      'installed and A7 gives the inside point. Two leaves 192 x 256 (chb1dl; the 448 height of A7 waits on A1).'}
    S({'id': 'thing:arena_gate', 'kind': 'building', 'at': [88.5, 94.0], 'size': [0.5, 2.0],
       'kit': 'plaster', 'facing': 'w', 'door': 'none', 'doors': [arena], 'floor': LD.YARD_H, 'title': 'The Warzone',
       'textures': dict(FIELD, door='chb1dl'),
       # D-180: 384 x 384 (XD-20's way out is 192 x 384); the studio draws a bay door under walls taller than its
       # door_height 256 high until A1's request (fb5 sub_b REQUESTS) lands
       'parts': [{'id': 'portal', 'at': [96, 0], 'size': [672, 1024], 'wall_height': 640, 'roof': 'flat',
                  'windows': 'none', 'door_height': 384,
                  'walls': {'w': ['wall', 'wall', ['door', 384], 'wall', 'wall']}}],
       'notes': 'The arena gate (XD-20) in a stone portal sunk into the Barbaric cliff (its top under the rock), '
                'facing the yard (A7).'})
    for i, at in enumerate([(88.45, 93.85), (88.45, 96.15)]):
        S(deco('thing:arena_torch_%d' % (i + 1), 'dec06', at))
    # D-174 (xeen-fb4-outdoor9): the coach and the barrels stand on the yard's level floor (rows 92-96, YARD_H): at
    # y 93.0 the coach's north end and at 91.9 the barrels stood on the rise to the cliff (row 91), which only an auto
    # pad cutting that rise by 672 levelled
    # F74 (X6 p15, 2026-11-26): a tent's `size` is [length, width], unturned its length north-south and its width
    # east-west, so [640, 1152] lay 1,152 east-west and ran 170 into the coach house's pen (x 86.41); [1152, 640]
    # stands north-south as D-174 meant (y 92.475-94.725), 0.26 cells clear of the pen (town_fit_check.py
    # pieces.overlap)
    S({'id': 'thing:warzone_coach_wagon', 'kind': 'tent', 'at': [87.3, 93.6], 'size': [1152, 640], 'height': 384,
       'open': False, 'title': "Gorm's coach",
       'notes': 'The Warzone coach (A4 4305): a closed coach standing by the cliff (dressing, no click).'})
    for i, (d, at) in enumerate([('haybale2', (83.5, 97.6)), ('haybale2', (83.85, 97.65)),
                                 ('bigbarel', (86.8, 92.1)), ('smlbarel', (87.15, 92.1))]):   # clear of the coach
        # F66 (X6 p3, 2026-11-25): at y 92.2 the barrels (drawn 47 and 36 wide in radius) showed through the coach
        # wagon's plank wall (y 92.375); now a third of a cell further north (D-174: 92.1, the coach's wall 92.475)
        S(deco('thing:yard_prop_%d' % (i + 1), d, at))
    S({'id': 'thing:yard_trough', 'kind': 'platform', 'at': [85.6, 97.6], 'size': [640, 160], 'height': 96,
       'textures': {'top': 'wtrtyl', 'wall': 'chb1'}, 'title': 'Water trough'})


def northern_sphinx(S):
    """XD-15 (A7's numbers): a recumbent lion with a human head facing south at (82, 39). A long low body under a
    rounded back (about half the head's height), domed haunches behind, two long low forelegs reaching to y 45 with
    768 clear between, the chest rising to a nemes headdress wider than the face, its lappets falling to the
    shoulders, a flat-topped head about 2,400 over the ground; the door (384 x 512, two leaves) in the breast at y 44."""
    x0, y0 = 80.25, 30.0
    u = lambda x: round((x - x0) * 512)   # noqa: E731
    v = lambda y: round((y - y0) * 512)   # noqa: E731
    nemes = dict(SPHINX_HEAD, wall='egycol64', window='egycol64', gable='egycol64', roof='egywalh')
    parts = [
        {'id': 'haunch', 'shape': 'round', 'at': [u(82.0), v(33.4)], 'radius': 860, 'sides': 12, 'wall_height': 352,
         'roof': 'dome', 'windows': 'none'},
        {'id': 'body', 'at': [u(80.6), v(33.2)], 'size': [u(83.4) - u(80.6), v(40.8) - v(33.2)], 'wall_height': 448,
         'roof': 'vault', 'ridge_along': 'ns', 'windows': 'none'},
        {'id': 'foreleg_w', 'at': [0, v(38.8)], 'size': [512, v(45.0) - v(38.8)], 'wall_height': 192,
         'roof': 'vault', 'ridge_along': 'ns', 'windows': 'none'},
        {'id': 'foreleg_e', 'at': [u(82.75), v(38.8)], 'size': [512, v(45.0) - v(38.8)], 'wall_height': 192,
         'roof': 'vault', 'ridge_along': 'ns', 'windows': 'none'},
        {'id': 'chest', 'at': [32, v(39.2)], 'size': [1728, v(42.2) - v(39.2)],
         'wall_height': 1024, 'batter': 288, 'roof': 'flat', 'windows': 'none'},
        {'id': 'breast', 'at': [u(81.25), v(41.6)], 'size': [768, v(44.0) - v(41.6)], 'wall_height': 640, 'walls': {'s': ['wall', ['door', 384], 'wall']}, 'roof': 'vault', 'ridge_along': 'ns',
         'windows': 'none'},
        {'id': 'nemes', 'at': [u(80.65), v(39.9)], 'size': [u(83.35) - u(80.65), v(42.1) - v(39.9)],
         'bottom': 1216, 'wall_height': 1184, 'taper': 0.62, 'roof': 'flat', 'windows': 'none', 'textures': nemes},
        {'id': 'face', 'at': [u(81.38), v(41.8)], 'size': [u(82.62) - u(81.38), v(42.7) - v(41.8)], 'bottom': 1536,
         'wall_height': 768, 'roof': 'flat', 'windows': 'none', 'textures': dict(SPHINX_HEAD)},
        {'id': 'lappet_w', 'at': [u(80.95), v(41.9)], 'size': [u(81.38) - u(80.95), v(42.45) - v(41.9)],
         'bottom': 896, 'wall_height': 832, 'roof': 'flat', 'windows': 'none', 'textures': nemes},
        {'id': 'lappet_e', 'at': [u(82.62), v(41.9)], 'size': [u(83.05) - u(82.62), v(42.45) - v(41.9)],
         'bottom': 896, 'wall_height': 832, 'roof': 'flat', 'windows': 'none', 'textures': nemes},
        {'id': 'brow', 'at': [u(81.3), v(41.85)], 'size': [u(82.7) - u(81.3), v(42.6) - v(41.85)], 'bottom': 2240,
         'wall_height': 112, 'roof': 'flat', 'windows': 'none', 'textures': nemes},
        {'id': 'tail', 'at': [u(83.35), v(33.6)], 'size': [160, v(38.6) - v(33.6)], 'wall_height': 96,
         'roof': 'vault', 'ridge_along': 'ns', 'windows': 'none'},
    ]
    if SPHINX_MODELS_LIVE:
        # D-141 (F61 p9: the carrier stood through the model's sides): the opening (384 x 512, S's contract) plus 16 a
        # side and on top, its ends hidden in the model's jambs; front 8 behind the door plane, inside the reveal (S:
        # -16..52); 200 deep
        parts = [{'id': 'breast', 'at': [u(82.0) - 208, v(44.0) - 8 - 200], 'size': [416, 200], 'wall_height': 528,
                  'walls': {'s': [['wall', 16], ['door', 384], ['wall', 16]]}, 'roof': 'flat', 'windows': 'none'}]
    way = dungeon_way('xd15', 'q-c9.door', 'The amulet glows, and the stone doors grind a finger\'s width and '
                                           'stop. Something inside is not ready. (Not open yet.)',
                      stir='xeen_sphinx_stir')
    if 'into' in way:
        # s25 (A3's Q-C9 answer 6): the opening click stays on X6, so q-c9.door's status line ("The amulet grows
        # warm...") shows in full with the stir; a move in the same click left it to the load and XD-15's arrival line
        # replaced it. Once 112180 is set, a click goes straight in (the hook's else line is never reached).
        h = HOOKS['q-c9.door']
        way = {'into': way['into'], 'condition': {'qbit': list(h['sets'].values())[0]},
               'else_effects': [{'lua': 'if %s then %s end' % (hook_lua('q-c9.door'), sound('xeen_sphinx_stir'))}]}
    door = {'part': 'breast', 'wall': 's', 'bay': 1, 'leaves': 2, 'title': "The Sphinx's door", **way,
            'notes': "XD-15 The Sphinx (A7; Q-C9): A3's q-c9.door wants the Jewelled Amulet (12317); once it has opened "
                     "(112180) the door leads to XD-15's entrance:x6_paws; the opening click stays (its line, xeen_sphinx_stir). Two leaves 192 x 256 "
                     '(egydrlgl; the 512 height of A7 waits on the paired-leaf word of A1).'}
    S({'id': 'thing:northern_sphinx', 'kind': 'building', 'at': [x0, y0], 'size': [3.5, 15.0], 'kit': 'plaster',
       'facing': 's', 'door': 'none', 'doors': [door], 'floor': LD.FORE_H, 'title': 'The Sphinx',
       'textures': dict(SPHINX, door='egydrlgl'), 'parts': parts,
       'notes': "XD-15's shell (D-31: at (82, 39) facing south, in sight of the X4 road), A7's numbers."
                + (" The body is lane S's xeen_sphinx_north; this is the door's carrier." if SPHINX_MODELS_LIVE else '')})
    if SPHINX_MODELS_LIVE:
        sphinx_model(S, 'north', 'thing:northern_sphinx_model', 'The Sphinx')
    S(deco('thing:cloud_hoard', '7dec11', HOARD, title='A mound of sand', effects=[hook('obelisks.cloud_hoard')],
           notes="A3's obelisks.cloud_hoard: with the seven Cloudside words an iron box, else sand."))


def southern_sphinx(S):
    """FD-02 (A7, phase 6): a second sphinx facing east, buried to its shoulders at the cove's edge: the nemes and the
    face out of the sand, a hump of back and haunch behind; the door (320 x 448, two leaves) in the breast."""
    x0, y0 = SSPHINX_X0, 82.0
    u = lambda x: round((x - x0) * 512)   # noqa: E731
    v = lambda y: round((y - y0) * 512)   # noqa: E731
    nemes = dict(SPHINX_HEAD, wall='egycol64', window='egycol64', gable='egycol64', roof='egywalh')
    parts = [
        {'id': 'back', 'at': [u(x0 + 0.4), v(83.2)], 'size': [u(x0 + 3.6) - u(x0 + 0.4), v(84.8) - v(83.2)],
         'wall_height': 96, 'roof': 'vault', 'ridge_along': 'ew', 'windows': 'none'},
        {'id': 'haunch', 'shape': 'round', 'at': [u(x0 + 0.9), v(84.0)], 'radius': 480, 'sides': 10,
         'wall_height': 64, 'roof': 'dome', 'windows': 'none'},
        {'id': 'shoulders', 'at': [u(x0 + 3.2), v(82.8)], 'size': [u(x0 + 5.0) - u(x0 + 3.2), v(85.2) - v(82.8)],
         'wall_height': 288, 'roof': 'vault', 'ridge_along': 'ns', 'windows': 'none'},
        {'id': 'breast', 'at': [u(x0 + 4.6), v(83.4)], 'size': [u(x0 + 5.5) - u(x0 + 4.6), v(84.6) - v(83.4)],
         'wall_height': 448, 'walls': {'e': ['wall', ['door', 320], 'wall']}, 'roof': 'vault',
         'ridge_along': 'ew', 'windows': 'none'},
        {'id': 'nemes', 'at': [u(x0 + 3.9), v(83.0)], 'size': [u(x0 + 5.0) - u(x0 + 3.9), v(85.0) - v(83.0)],
         'bottom': 288, 'wall_height': 1056, 'taper': 0.66, 'roof': 'flat', 'windows': 'none', 'textures': nemes},
        {'id': 'face', 'at': [u(x0 + 4.85), v(83.55)], 'size': [u(x0 + 5.25) - u(x0 + 4.85), 460], 'bottom': 640,
         'wall_height': 576, 'roof': 'flat', 'windows': 'none', 'textures': dict(SPHINX_HEAD)},
    ]
    if SPHINX_MODELS_LIVE:
        # D-141 (F61 p13: the door stood proud of the body): the opening (320 x 448, S's contract) plus 16 a side and
        # on top; front 8 behind the door plane on x 39.5, inside the reveal (S: -16..44); 200 deep
        parts = [{'id': 'breast', 'at': [u(39.5) - 8 - 200, v(84.0) - 176], 'size': [200, 352], 'wall_height': 464,
                  'walls': {'e': [['wall', 16], ['door', 320], ['wall', 16]]}, 'roof': 'flat', 'windows': 'none'}]
    door = {'part': 'breast', 'wall': 'e', 'bay': 1, 'leaves': 2, 'title': 'The Southern Sphinx',
            **dungeon_way('fd02', 'm40.sphinx_door', "The jaw opens on a stair full of sand. It will take more than "
                                                     "an amulet to dig it out. (Not open yet.)"),
            'notes': "FD-02 (A7, phase 6; M40): A3's m40.sphinx_door (Roland's amulet), then "
                     + ("into FD-02 at entrance:x6_door" if DUNGEON['fd02'] else 'sealed until FD-02 exists')
                     + '. Two leaves 160 x 256 (egydrlgl; 448 high waits on A1).'}
    S({'id': 'thing:southern_sphinx', 'kind': 'building', 'at': [x0, y0], 'size': [6.0, 4.0], 'kit': 'plaster',
       'facing': 'e', 'door': 'none', 'doors': [door], 'floor': LD.SPHINX2_H, 'title': 'The Southern Sphinx',
       'textures': dict(SPHINX, door='egydrlgl'), 'parts': parts,
       'notes': "FD-02's shell: buried to its shoulders at the cove's edge, facing the morning (east)."
                + (" The body is lane S's xeen_sphinx_south; this is the door's carrier." if SPHINX_MODELS_LIVE else '')})
    if SPHINX_MODELS_LIVE:
        sphinx_model(S, 'south', 'thing:southern_sphinx_model', 'The Southern Sphinx')


def sphinx_model(S, key, sid, title):
    """Lane S's sphinx decoration at its contract origin, turned to its facing. D-141 (F61): solid by its binding's
    `collision: model` (the LOD2 proxy); the closed barrier rings on S's body and head outlines are gone."""
    c = yaml.safe_load(open(SPHINX_CONTRACT))[key]
    turn = (-c['facing']) % 360
    turn = turn - 360 if turn > 180 else turn
    S(deco(sid, c['decoration'], c['origin_cells'], turn=turn, title=title,
           notes="Lane S's %s (row %d): origin the door threshold's middle, facing %d (turn %d)."
                 % (c['decoration'], c['row'], c['facing'], turn)))


def basenji(S):
    """XD-14 Castle Basenji on its north-rim crag (D-31: grey rubble and black timber, the towers kit; never moved
    nearer): a hall and a keep with four round towers; the gate on the terrace at about 2,600 (A7)."""
    x0, y0 = 35.0, 27.4
    parts = [
        {'id': 'hall', 'at': [192, 1600], 'size': [2688, 1408], 'wall_height': 896, 'roof': 'flat',
         'battlements': True, 'windows': 'none'},
        # D-180 (2026-11-26): a castle's gate is a double door 384 x 384 (door_check doors.small_for_building; XD-14's
        # way out is 192 x 352): taller than the 352 walls, the studio cuts it into the gable
        {'id': 'gatehouse', 'at': [1152, 2880], 'size': [768, 352], 'wall_height': 352, 'roof': 'gable',
         'ridge_along': 'ns', 'roof_pitch': 52, 'windows': 'none', 'door_height': 384,
         'walls': {'s': ['wall', ['door', 384], 'wall']}},
        {'id': 'keep', 'at': [704, 320], 'size': [1664, 1408], 'wall_height': 1664, 'roof': 'flat',
         'battlements': True, 'windows': 'none'},
        {'id': 'tower_sw', 'shape': 'round', 'at': [256, 2880], 'radius': 352, 'sides': 10, 'wall_height': 1280,
         'roof': 'cone', 'roof_pitch': 60, 'windows': 'none'},
        {'id': 'tower_se', 'shape': 'round', 'at': [2816, 2880], 'radius': 352, 'sides': 10, 'wall_height': 1280,
         'roof': 'cone', 'roof_pitch': 60, 'windows': 'none'},
        {'id': 'tower_nw', 'shape': 'round', 'at': [512, 448], 'radius': 320, 'sides': 10, 'wall_height': 2048,
         'roof': 'cone', 'roof_pitch': 64, 'windows': 'alternate'},
        {'id': 'tower_ne', 'shape': 'round', 'at': [2560, 448], 'radius': 384, 'sides': 10, 'wall_height': 1792,
         'roof': 'cone', 'roof_pitch': 62, 'windows': 'alternate'},
    ]
    gate = {'part': 'gatehouse', 'wall': 's', 'bay': 1, 'leaves': 2, 'arch': 'pointed',
            'title': 'Castle Basenji',
            **asked_way('Black oak doors under a pointed arch. Somewhere inside, a dog howls, then a man.',
                        'Castle Basenji. Enter?',
                        dungeon_way('xd14', None, 'The doors are barred from within. (Not open yet.)')),
            'notes': 'XD-14 Castle Basenji (A7; Q-C8): "Castle Basenji.  Enter?" (xeen/aaze0001:19), then XD-14\'s '
                     'entrance:x6_gate. Two leaves (chb1dl, mirrored).'}
    S({'id': 'thing:castle_basenji', 'kind': 'building', 'at': [x0, y0], 'size': [6.0, 6.0], 'kit': 'plaster',
       'facing': 's', 'door': 'none', 'doors': [gate], 'floor': LD.TERRACE_H, 'title': 'Castle Basenji',
       'textures': dict(BASENJI, door='chb1dl'), 'parts': parts,
       'notes': "XD-14's shell on the crag (38, 31); D-31's grey rubble and black timber."})
    for i, at in enumerate([(37.3, 33.55), (38.7, 33.55)]):
        S(deco('thing:basenji_torch_%d' % (i + 1), 'dec06', at))
    S(deco('thing:basenji_skulls', 'sklplrev', (35.0, 34.6)))


def camps(S):
    """Arie's camp below the cliff, Saul's hermitage, the Summer Druid's grove, the prospector's camp."""
    # Arie the Apprentice (4608, Q-C8) at the foot of the cliff path
    S({'id': 'thing:arie_tent', 'kind': 'tent', 'at': [44.0, 44.0], 'size': [768, 640], 'height': 384,
       'awning': 256, 'title': "Arie's tent", 'notes': "Arie's camp (Q-C8): her master's books under the awning."})
    S(deco('thing:arie_fire', '7dec02', (45.9, 46.4), title='Campfire'))
    S(deco('thing:arie_pot', '7dec03', (46.4, 45.9)))
    # Saul's hermitage: a stone hut with an awning, the urn (x6.saul_urn)
    S({'id': 'thing:saul_hut', 'kind': 'building', 'at': [28.5, 68.8], 'size': [2.0, 1.5], 'kit': 'plaster',
       'facing': 'e', 'door': 'none', 'title': "Saul's hermitage", 'textures': dict(OCHRE, roof='hhm2rf'),
       'parts': plain_upper([{'id': 'hut', 'at': [64, 64], 'size': [768, 640], 'wall_height': 288, 'roof': 'flat',
                              'parapet': 48, 'windows': 'alternate',
                              'porches': [{'wall': 'e', 'depth': 192, 'posts': 24, 'height': 224, 'floor': 16}]}],
                            OCHRE)})
    S(deco('thing:saul_urn', 'dec26', (30.35, 71.2), title="Saul's urn", effects=[hook('x6.saul_urn')]))
    # the Summer Druid's grove: palms and a spring round a stone basin
    S({'id': 'thing:druid_spring', 'kind': 'fountain', 'at': [70.6, 89.3], 'radius': 192, 'sides': 10,
       'pillar': 0, 'title': "The Summer Druid's spring", 'textures': {'wall': 'chb1'},
       'notes': 'The one green place in the south (dressing: the spring is not a device, its title a hover).'})
    # the prospector's camp in the Barbaric notch
    px, py = LD.PROSPECTOR
    S({'id': 'thing:prospector_tent', 'kind': 'tent', 'at': [px - 0.6, py - 0.9], 'size': [512, 512], 'height': 320,
       'open': True, 'title': "A prospector's tent"})
    S(deco('thing:prospector_fire', 'dec24x', (px + 0.6, py - 0.2), title='A cold fire'))


def devices(S):
    """The obelisk, the fountains and wells, the shrine, the sun stones, the cairn, the Reflector."""
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [75.0, 51.0], 'height': 768, 'title': 'Obelisk',
       'effects': [hook('obelisks.x6')], 'notes': "Cloudside's sixth obelisk (A3's obelisks.x6) on its red knoll."})
    S({'id': 'thing:oasis_fountain', 'kind': 'fountain', 'at': list(OASIS_FOUNTAIN), 'radius': 224, 'sides': 10,
       'title': 'The oasis fountain', 'textures': {'wall': 'chb1'}, 'tiers': [[64, 48]],
       **once_per_character('oasis_fountain',
                            [{'add': {'var': 'BaseEndurance', 'value': 2}},
                             {'text': 'Clear water from deep under the sand. You feel it in your bones. '
                                      '(+2 Endurance, permanent)'}],
                            [{'text': 'Clear, cold water. It has given you all it will.'}]),
       'notes': 'MAPS X6: +2 Endurance, permanent, once per character (player bit 11330, A3 to register).'})
    S({'id': 'thing:well_accuracy', 'kind': 'well', 'at': [52.0, 92.0], 'title': 'The Well of Accuracy',
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       **daily('thing:well_accuracy',
               [{'add': {'var': 'AccuracyBonus', 'value': 10}},
                {'text': 'The water is so still you can see the bottom. Your eye sharpens. '
                         '(+10 Accuracy until you rest)'}],
               [{'text': 'The water is cool and refreshing.'}])})
    S({'id': 'thing:waters_power', 'kind': 'fountain', 'at': [30.6, 34.4], 'radius': 256, 'sides': 8,
       'title': 'The Waters of Great Power', 'textures': {'wall': 'hwm2wall'}, 'tiers': [[64, 48]],
       **once_per_character('waters_power',
                            [{'add': {'var': 'HP', 'value': 200}},
                             {'text': 'The water is cool and refreshing. (+200 hit points)'}],
                            [{'text': 'The water is cool and refreshing.'}]),
       'notes': 'Original line: xeen/aaze0001:4; once per character a day (player bit 11333).'})
    # the Shrine of Energy by the west rim: an open shrine round a pedestal ("Shrine of Energy.  Pray?")
    S({'id': 'thing:shrine_energy_house', 'kind': 'building', 'at': [27.2, 53.2], 'size': [1.6, 1.6],
       'kit': 'plaster', 'door': 'none', 'title': 'The Shrine of Energy', 'textures': dict(FIELD),
       'parts': [{'id': 's', 'at': [96, 96], 'size': [627, 627], 'wall_height': 352, 'posts': 32, 'roof': 'hip',
                  'roof_pitch': 38, 'windows': 'none'}]})
    # D-144 (F69b, X6 p5): a click, its line on the status line; the source's "Shrine of Energy. Pray?" was a free
    # Yes/No whose No changed nothing
    S(deco('thing:shrine_energy', 'dec64', (28.0, 54.0), title='Shrine of Energy',
           **once_per_character('shrine_energy',
                                [{'add': {'var': 'AirResistance', 'value': 5}},
                                 {'text': 'Lightning runs over your skin and is gone. (+5 Air resistance, '
                                          'permanent)'}],
                                [{'text': 'The sparks crackle, but leave you alone.'}]),
           notes='Original line: xeen/aaze0001:0; +5 Air resistance (D-4), once per character (player bit 11331).'))
    # the sun stones: a ring of red standing stones the Summer Druid keeps (A3's x6.sun_stones, once a day)
    S({'id': 'thing:sun_stones', 'kind': 'stone_ring', 'at': [69.0, 103.0], 'radius': 640, 'count': 7,
       'lintel': False, 'stone': [128, 96, 384], 'altar': [320, 256, 96], 'seed': 6,
       'textures': {'wall': 'chb1'}, 'title': 'The sun stones',
       **daily('thing:sun_stones', [{'add': {'var': 'FireResistanceBonus', 'value': 10}}, hook('x6.sun_stones')],
               [hook('x6.sun_stones_again')])})
    # the caravan cairn by the desert road (A3's x6.caravan_cairn, once a day)
    S(deco('thing:caravan_cairn', 'rock26', (96.0, 57.4), title='Caravan cairn',
           **daily('thing:caravan_cairn', [{'add': {'var': 'LuckBonus', 'value': 10}}, hook('x6.caravan_cairn')],
                   [hook('x6.caravan_cairn_again')])))
    for i, at in enumerate([(95.5, 57.0), (96.6, 57.9)]):
        S(deco('thing:cairn_stone_%d' % (i + 1), '7rock08', at))
    # the Air Reflector on the rock spit where the rims meet (A3's m37.reflector_air)
    S({'id': 'thing:air_reflector', 'kind': 'obelisk', 'at': [26.4, 26.4], 'height': 384, 'sides': 8,
       'title': 'Air Reflector',
       'effects': reflector('m37.reflector_air'),
       'notes': 'Original line: xeen/aaze0001:17 ("Reflector. Activate?"); M37 after M36 (A3).'})


def finds(S):
    """The seven chests, each with a reason (L1), and their dressing."""
    # a wagon the dunes swallowed, a worm's hole beside it
    S({'id': 'thing:swallowed_wagon', 'kind': 'tent', 'at': [93.0, 31.4], 'size': [512, 960], 'height': 288,
       'open': False, 'turn': 20, 'title': 'A half-buried wagon'})
    # xeen-fb4-outdoor3 (2026-11-25): the strongbox beside the wagon on its 1,920 pad; at (94.3, 32.7) its own pad
    # (1,792) cut into the wagon's footprint, which hung 42 over it (town_fit things.overhang)
    S({'id': 'thing:wagon_strongbox', 'kind': 'crate', 'at': [95.0, 30.6], 'title': "The wagon's strongbox",
       'chest': {'level': 3, 'random_items': 3},
       'effects': [{'text': 'Half a wagon sticks out of the dune. Beside it, a hole wide as a door, still settling.'}]})
    # the werewolves' den under the castle's east wall
    S({'id': 'thing:werewolf_den', 'kind': 'cave_mouth', 'at': [52, 30], 'size': [1024, 1024],
       'mouth': {'width': 448, 'height': 352, 'depth': 128}, 'roughness': 0.7, 'form': 'blocked',
       'effects': [{'text': "Fallen earth and stones fill the den's mouth. The pack sleeps out in the open now."}],
       'seed': 9, 'free': True, 'title': "The werewolves' den: gnawed bones and the stink of wet fur",
       'notes': 'D-91: a barrow on level land with no way in, blocked at its face (rubble); the pack stays outside.'})
    S({'id': 'thing:den_chest', 'kind': 'chest', 'at': [53.6, 31.4], 'title': "What the pack's victims carried",
       'chest': {'level': 3, 'random_items': 2}})
    for i, (d, at) in enumerate([('7dec18', (51.3, 31.6)), ('dec19', (53.4, 31.9)), ('7dec20', (51.7, 32.5))]):
        S(deco('thing:den_bones_%d' % (i + 1), d, at))
    # a ruined watchtower of the old Gargoyle Range road on the foothills (a landmark: no click; the 6,000 rule)
    S({'id': 'thing:gargoyle_watch', 'kind': 'building', 'at': [104, 38], 'size': [2, 2], 'kit': 'plaster',
       'door': 'none', 'title': 'A fallen watchtower', 'textures': dict(FIELD),
       'parts': [{'id': 't', 'shape': 'round', 'at': [512, 512], 'radius': 384, 'sides': 10, 'wall_height': 896,
                  'ruin': {'height': [192, 896], 'gaps': 0.35, 'seed': 5}, 'roof': 'none', 'windows': 'alternate'}]})
    S(deco('thing:watch_bones', '7dec18', (103.6, 40.4)))
    # the ruined caravanserai and its keeper's strongbox
    S({'id': 'thing:caravanserai', 'kind': 'building', 'at': [76.4, 74.4], 'size': [3.6, 3.6], 'kit': 'plaster',
       'door': 'none', 'title': 'The ruined caravanserai', 'textures': dict(FIELD),
       'ruin': {'height': [96, 416], 'gaps': 0.4, 'thickness': 64, 'seed': 11},
       'parts': [{'id': 'r', 'at': [96, 96], 'size': [1650, 1650], 'wall_height': 416, 'roof': 'none',
                  'windows': 'alternate'}]})
    S({'id': 'thing:serai_strongbox', 'kind': 'chest', 'at': [78.2, 76.2], 'title': "The old keeper's strongbox",
       'chest': {'level': 3, 'random_items': 3}})
    S(deco('thing:serai_well', 'dec24x', (77.4, 77.4)))
    # the bone fields: a dead caravan among the giant bones
    S({'id': 'thing:bone_chest', 'kind': 'chest', 'at': [62.4, 81.4], 'title': "A dead caravan's pay chest",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'The bones of something enormous, and among them the bones of the caravan it ate.'}]})
    for i, (d, at) in enumerate([('dec29', (61.4, 80.6)), ('dec21', (63.6, 80.2)), ('7dec18', (60.8, 82.4)),
                                 ('sklplrev', (64.0, 82.8)), ('dec19', (62.2, 83.6)), ('7dec20', (59.6, 80.8)),
                                 ('dec29', (65.4, 79.6)), ('7dec18', (63.0, 78.8))]):
        S(deco('thing:bones_%d' % (i + 1), d, at))
    # an explorer's pack at the rim's lip, a rope going over
    S({'id': 'thing:rim_pack', 'kind': 'chest', 'at': [25.9, 100.4], 'title': "An explorer's pack",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'A note pinned to the pack: "Gone to see where the sand goes."'}]})
    S(deco('thing:rim_stake', 'dec13', (25.2, 101.1)))
    # a great bird's nest on the big mesa's top, reached by the crack
    S({'id': 'thing:mesa_nest', 'kind': 'chest', 'at': [66.0, 34.6], 'title': "A great bird's nest",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'Sticks the size of spears, and among them, glittering things.'}]})
    S(deco('thing:nest_bones', 'dec29', (65.3, 34.1)))
    # the prospector's strongbox in his camp
    px, py = LD.PROSPECTOR
    S({'id': 'thing:prospector_box', 'kind': 'chest', 'at': [px + 0.2, py + 0.5], 'title': "The prospector's box",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'The fire is long cold. His pick is still in the rock.'}]})


# ---------------------------------------------------------------- actors
def actors():
    out = []
    A = out.append
    for m, at, c, s, g, n in L1.ACTORS:
        A({'monster': m, 'at': list(at), 'count': c, 'spread': s, 'group': 60 + g, 'hostile': True, 'notes': n})
    # Sphinx Wells' caravaners: D-96's villagers (gen.py fills these places, villagers.yml)
    out.extend(V.slots(4))
    A({'monster': '354', 'npc': ARIE, 'at': [45.4, 45.0], 'spread': 0, 'group': 53,
       'notes': 'Arie the Apprentice (A4 4608, Q-C8) at her camp below Castle Basenji.'})
    A({'monster': '368', 'npc': SAUL, 'at': [31.1, 70.6], 'spread': 0, 'group': 53,
       'notes': 'Saul the Hermit (A4 4602): Meditation Master.'})
    A({'monster': '11929', 'npc': SUMMER_DRUID, 'at': [69.6, 90.2], 'spread': 0, 'group': 53,
       'notes': "The Summer Druid (A4 4601, Q-C1) in her grove; D-91: lane S's row 11929 Xeen Druidess (Druidess A's body)."})
    return out


def events():
    clear = '\n'.join(['evt.ForPlayer(Players.All)'] + ['ClearPlayerBit(PlayerBit(%d))' % PB[k] for k in DAILY_BITS])
    return [
        {'id': 'evt:daily_bits', 'trigger': 'daily', 'effects': [{'lua': clear}],
         'notes': 'Once per character a day: the Waters of Great Power (as MM7 7out02 clears its well bit; the '
                  'temporary sources are daily for the party, D-70).'},
        {'id': 'evt:yard_gate_state', 'trigger': 'load', 'condition': {'qbit': 'warzone_gate'},
         'effects': [{'hide': 'thing:yard_gate_%s_%s' % (sd, w)} for sd in ('outer', 'inner') for w in ('n', 's')],
         'notes': 'D-8.1: once opened from the desert side the yard gate stays open (x6.warzone_gate, 116100).'},
    ]
