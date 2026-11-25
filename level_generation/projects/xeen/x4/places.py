"""X4 Burlock Savannah, L3/L4: the towns' plots, the structures, actors, events and scatter. A5, 2026-11-20.

Used by gen.py. Positions come from gen_l1.py (the approved L1 with D-11.2/5/6) unless written here. Cells [x, y].
Text: short lines; three from the source with their aaze reference (noted beside them).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/tools/xeen')
import villagers as V  # noqa: E402  D-96 (A4, F20): each settlement's street villagers, source/towns/villagers.yml
import kit_pieces as KIT  # noqa: E402  D-95: the sunken entrance (tools/xeen/kit_pieces.py)
import math
import os

import yaml

import gen_l1 as L1
import kit as K
import land as LD

# ---------------------------------------------------------------- the world's rows (A2) and switches
# D-11.2: the hostile knights are A2's renegades, their own family and faction (hostile in the world's relations.yml).
KNIGHT_SLOT = 'Xeen Renegade'        # A2's rows (2026-11-20): Renegade Jouster 11680, Knight 11681, Captain 11682
KNIGHT_ROWS = {'jouster': '11680', 'leader': '11682'}
OGRE_ROWS = {'ogre': '11060', 'brute': '11061'}
BARBARIAN_ROWS = {'barbarian': '11100', 'warrior': '11101', 'chief': '11102'}
KINGS_GUARD = '11143'                 # friendly to the party (its own faction)
PEASANTS_M = ['371', '368', '362']    # MMerge peasants (MM7), as X2's townsfolk
PEASANTS_F = ['377', '350', '354']
X3_LIVE = True                        # D-11.6: the south edge west of x 0 leads to X3 (edge_spans, A1 merge point 9)
X3_ARRIVAL = (-7168, 22016, 1120, 270)  # X3's north arrival (x, y, z, direction in DEGREES)
DOORWAY_LEAVES = True                 # a doorway's `leaves: 2` (merge point 15, oymap 20:03:53; doors.half_wing)
X6_LIVE = True                        # X6 installed (19:40) with A2's row 9104 and the X4-X6 travel rows (edge_spans)
# X7 Mount Firestone (D-40): installed 21:58 with A2's row 9105 and A1's travel rows (A5 tenth session); the east
# edge arrives at X7's entrance:west_road, X7's west edge comes back to X4's entrance:east_road (22016, -1280, 1056)
_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../..'))
X7_LIVE = (os.path.exists(os.path.join(_REPO, 'assets_dev/worlds/xeen/maps/xeen_x7.odm'))
           and 'xeen_x7.odm' in open(os.path.join(_REPO, 'assets_dev/worlds/xeen/data_tables/map_stats.txt'),
                                     encoding='latin-1').read())
X7_ARRIVAL = (-22016, -1024, 1408, 0)     # X7's entrance:west_road, facing east (degrees)
X6_ARRIVAL = (22016, 2048, 1216, 180)  # X6's east arrival, cell (107, 60), facing west (A2's edge_spans row)
XD07_LIVE = True                      # A7's dungeons, installed and leading back here (2026-11-20)
XD25_LIVE = True
XD26_LIVE = True
# each door's inside arrival (x, y, z, direction in DEGREES): the dungeon's start (its scene's StartPoint0)
XD07_ARRIVAL = (0, 384, 0, 90)        # inside Castle Burlock's door in the gatehouse, facing north to the portcullis
XD25_ARRIVAL = (-2208, 1760, 256, 0)  # the top of the cellar stair under Asp's square, facing east down it
# D-95 (the orchestrator 2026-11-22, after the user's culvert on X1): the undercroft stair is set into Asp's square,
# not a mound on it: a ditch a party height deep (floor nodes x 41-42 on row 81, 224 under the square's 1,056) whose
# ramp rises south to row 82; the stair's dark mouth in its north end face, the crown under the square's level, a stone
# cap behind it. The revetments are 448 thick (the house east of it stands at x 43.0) and end at row 81.6 (their tops
# 16 under the cap's, as X1's culvert). XD-25's way out lands at
# (41.5, 82.45) on the square south of the ramp's top (XD-25 unchanged).
XD25_CUT = KIT.SunkenEntrance('xd25_stair', 41, 42, face_y=81, floor_to=81, ramp_to=82, ground=1056, top=1088,
                              depth=224, back_to=80.0, revet_to=81.6, revet_thick=448)
XD26_ARRIVAL = (1344, -1000, 0, 90)   # the eyrie's cave mouth, facing north into the mountain
XD02_ADIT_ARRIVAL = (2720, 5184, 256, 0)
# D-15 (3): A6's own pedestal caps (installed 2026-11-20; XD-02's xnbasred/xnbasblu stood in before)
CAP_RED, CAP_BLUE = 'xnpedred', 'xnpedblu'   # inside XD-02's collapsed west adit, past the fall, facing east (A7)

HOUSE_NAMES = {
    4151: 'The Royal Armoury', 4152: 'Plate and Mail by Royal Appointment', 4153: 'Chapel of the Crown',
    4154: "The King's Lists", 4155: 'Royal Stables of Burlock', 4156: 'The Jousting Pig',
    4158: "Dame Ysolde's House", 4159: 'The Weathervane', 4160: 'Keeper of the Bestiary', 4161: 'Pomfrey House',
    4162: 'The Royal Laundry', 4163: "Wat's Cottage", 4164: 'The Bakehouse', 4165: 'Holt House',
    4166: "Carlawna's Hut", 4167: "Falagar's Hut", 4170: 'The Travel Pit', 4171: 'Roadside Shrine',
    4172: "Sarah Slither's House", 4173: 'Snake Oil', 4174: 'Scale House', 4175: 'Asp Guild of Earth',
    4176: 'Asp Guild of Body', 4178: 'Reed House', 4179: 'Moss Cottage', 4180: 'Brook House',
    4181: 'Slade Residence', 4182: 'Ashworth House', 4183: "The Potter's", 4184: 'Dale Residence',
    4185: "Mother Ophidia's", 4186: 'The Old Mill'}
# each service building's shape and extras (kit.shape kinds; 'chapel' is drawn here)
SHAPES = {
    'building:burlock_temple': ('chapel', {'sign': 'sgtempl'}),
    'building:burlock_tavern': ('gable_porch', {'sign': '7sgtvrn', 'storeys': 2}),
    'building:burlock_weapons': ('forge', {'sign': 'sgweapon'}),
    'building:burlock_armour': ('jetty', {'sign': '7sgarm', 'storeys': 2}),
    'building:burlock_training': ('barn', {'sign': '7sgtrain'}),
    'building:burlock_stables': ('barn', {'sign': '7sgstabl'}),
    'building:asp_travel_pit': ('barn', {'sign': '7sgstabl'}),
    'building:asp_shrine': ('cottage', {'sign': 'sgtempl'}),
    'building:asp_guild_earth': ('tower_house', {'sign': 'sgearth'}),
    'building:asp_guild_body': ('tower_house', {'sign': 'sgbody'}),
    'building:asp_alchemist': ('jetty', {'sign': '7sgalch'}),
    'building:asp_armour': ('cottage', {'sign': '7sgarm'}),
    'building:carlawna_hut': ('round_hut', {}),
    'building:falagar_hut': ('cottage', {}),
}
HOUSE_SHAPES = ['cottage', 'gable_porch', 'L']
_TOWN = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../../../assets_dev/worlds/xeen/source/towns/x4.yml')))
# X4_ASP_OPEN=1: Asp as after q-c5.done (no closed texts), for town_feel's measure of Asp's houses only (never installed)
CLOSED = {} if os.environ.get('X4_ASP_OPEN') else {
    h['id']: h['closed_text'] for h in _TOWN['houses'] if h.get('opens') == 'q-c5.done' and h['id'] != 4177}
# D-150: Nystor's Landing, the boat back to Rivercity (A4's house whose door is the landing's mooring post)
NYSTOR_HOUSE = next((h['id'] for h in _TOWN['houses'] if h.get('door') == 'thing:nystor_post'), None)


def W(x, y):
    return (round((x - 64) * 512), round((64 - y) * 512))


def msg(text):
    return {'lua': 'evt.SimpleMessage("%s")' % text.replace('\\', '\\\\').replace('"', '\\"')}


def status(text):
    """F13 / D-90 2 (A5 s29): a touch's gain (a stat, experience) and its refusal on the status line, held by its length
    (the studio's text rule: max(2, min(6, 2 + len // 15)) seconds), not in a window."""
    return {'lua': 'evt.StatusText("%s", %d)' % (text.replace('\\', '\\\\').replace('"', '\\"'),
                                                 max(2, min(6, 2 + len(text) // 15)))}


def hook(name):
    return {'lua': 'XeenQuests.hook("%s")' % name}


def daily(sid, effects, again):
    """D-70 Q2: a temporary source works once a day for the whole party (Xeen.usedToday / Xeen.markToday, every member
    by evt.ForPlayer(Players.All)); a second use the same day gives `again` and nothing else."""
    key = 'x4_' + sid.split(':', 1)[1]
    return {'condition': {'not': {'lua': 'Xeen.usedToday("%s")' % key}},
            'effects': [{'lua': 'Xeen.markToday("%s") evt.ForPlayer(Players.All)' % key}] + effects,
            'else_effects': again}


WATER = [{'text': 'The water is cool and refreshing.'}]     # aaze0011:17 (D-70)


def into(stem, arrival):
    return {'map': stem, 'at': list(arrival[:3]), 'facing': arrival[3] * 2048 // 360}


def deco(sid, name, at, **kw):
    d = {'id': sid, 'kind': 'decoration', 'decoration': name, 'at': [round(at[0], 3), round(at[1], 3)]}
    d.update(kw)
    return d


def half(at):
    return [round(v * 2) / 2 for v in at]


# ---------------------------------------------------------------- plots
plots_by_space = {}
doors = []            # (plot id, house, door cell, cell 0.9 out, title)
footprints = []


def _chapel(facing, fp):
    W_, H_ = K.plot_extent(facing, fp)
    parts = [{'id': 'nave', 'at': [64, 96], 'size': [W_ - 384, H_ - 192], 'wall_height': 384, 'roof': 'gable',
              'roof_pitch': 50, 'ridge_along': 'ns', 'windows': 'all'},
             {'id': 'bell', 'at': [W_ - 288, 96], 'size': [224, 224], 'wall_height': 768, 'roof': 'hip',
              'roof_pitch': 60, 'windows': 'none', 'textures': {'roof': '7hhr1rf'}}]
    return parts, {'part': 'nave', 'wall': facing}


def add_plot(space, bid, index, house, fp, at, facing, kit, door_to=None):
    at = half(at)
    kind, extra = SHAPES.get(bid, (None, {}))
    if kind is None:
        area = fp[0] * fp[1]
        kind = 'cottage' if area <= 1.0 else HOUSE_SHAPES[(index or 0) % len(HOUSE_SHAPES)]
        if kind == 'L' and min(fp) < 1.5:
            kind = 'gable_porch'
    plot = {'building': bid, 'at': at, 'facing': facing, 'kit': kit}
    turn = 0
    if kind == 'round_hut':
        plot['facing'] = 's'
        turn = K.TURN_OF[facing]
        if turn > 180:
            turn -= 360
        if turn:
            plot['turn'] = turn
    if index:
        plot['index'] = index
    if door_to:
        plot['door_to'] = door_to
    plot['house'] = house
    plot['title'] = HOUSE_NAMES[house]
    if house in CLOSED:
        # A4's x4.yml: the cursed Asp houses open with q-c5.done (qbit 112102); before it, the house's closed text
        plot['condition'] = {'qbit': 'asp_liberated'}
        plot['else_effects'] = [msg(CLOSED[house])]
    if kind == 'chapel':
        parts, door = _chapel(facing, fp)
    else:
        roof = K.THATCH if kit == 'poor' else K.ROOFS.get(kit)
        parts, door = K.shape(kind, plot['facing'], fp, kit, sign=extra.get('sign'), roof_tex=roof)
        if extra.get('storeys', 1) > 1:
            for p in parts:
                if 'bottom' not in p and p.get('shape') != 'round':
                    p['wall_height'] = 512
    plot['parts'] = parts
    plot['door'] = door
    plots_by_space.setdefault(space, []).append(plot)
    pid = bid + ('#%d' % index if index else '')
    footprints.append((pid, K.footprint(at[0], at[1], facing if kind != 'round_hut' else 's', fp, turn)))
    if kind == 'round_hut':
        dc = K.door_cell(at[0], at[1], 's', fp, turn, -0.08)
        out = K.door_cell(at[0], at[1], 's', fp, turn, 0.9)
    else:
        dc = K.door_cell(at[0], at[1], facing, fp, 0, 0.0)
        out = K.door_cell(at[0], at[1], facing, fp, 0, 0.9)
    doors.append((pid, house, dc, out, plot['title']))


for bid, service, house, fp, at, facing, door_to, kit in L1.BURLOCK:
    add_plot('town:burlock', bid, None, house, fp, at, facing, kit, door_to)
for i, (house, fp, at, facing, kit) in enumerate(L1.BURLOCK_HOUSES, 1):
    add_plot('town:burlock', 'building:burlock_houses', i, house, fp, at, facing, kit)
for bid, service, house, fp, at, facing, door_to, kit, note in L1.ASP:
    add_plot('town:asp', bid, None, house, fp, at, facing, kit, door_to)
for i, (house, fp, at, facing, kit) in enumerate(L1.ASP_HOUSES, 1):
    add_plot('town:asp', 'building:asp_houses', i, house, fp, at, facing, kit)
for space, bid, service, house, fp, at, facing, kit in L1.HUTS:
    add_plot(space, bid, None, house, fp, at, facing, kit)


# ---------------------------------------------------------------- structures
# the barbarian camp's dress (bones, a skull pile): gone once the camp is burnt (D-152)
# D-142 (2026-11-25): the whole camp 4 cells east and 2 north of where it stood (its fighters were 2,632-3,776 from
# the X6 edge arrival (20, 60), the floor 4,096); land.py's flat, ground and calm and gen_l1's track moved with it
BARBARIAN_DRESS = [('7dec18', (29.6, 54.6)), ('sklplrev', (25.6, 53.4)), ('7dec20', (30.2, 52.6))]
BARBARIAN_DRESS_IDS = ['thing:barbarian_dress_%d' % (i + 1) for i in range(len(BARBARIAN_DRESS))]


def structures():
    out = []
    S = out.append
    # ======== Castle Burlock on its rise (XD-07's gate) =========================================================
    # plot [56, 43] 12 x 7 cells = 6144 x 3584; the curtain wall's block, four round towers, the keep, the gatehouse
    # whose door (the gate) looks south over the village at y 50 (the ramp's top).
    # The royal kit's MM6 Ironfist set (hcwall, cs...) is not a texture of world xeen's outdoor builds (the studio:
    # "the world xeen has no texture hcwall"; requested of A1/A6). Until it is: MM7 Castle Gryphonheart's chb1
    # fieldstone set (Erathia, 7out03), with the kit's own slate cones, arrow slits and Burlock's arms.
    hc = {'wall': 'chb1', 'window': 'chbw', 'door': 'chb1dl', 'post_left': 'chb1el', 'post_right': 'chb1er',
          'trim': 'chb1s', 'roof': 'xtslate'}
    cs = dict(hc, window='xkarrow')
    towers = []
    for i, (tx, ty) in enumerate([(640, 768), (5504, 768), (640, 3072), (5504, 3072)]):
        towers.append({'id': 'tower_%d' % (i + 1), 'shape': 'round', 'at': [tx, ty], 'radius': 448, 'sides': 10,
                       'wall_height': 1280, 'roof': 'cone', 'roof_pitch': 68, 'windows': 'alternate',
                       'textures': dict(hc, window='xkarrow')})
    gate_effects = ([{'lua': 'XeenQuests.hook("m5.crusaders_gate")'}] if XD07_LIVE else
                    [msg("The gate of Castle Burlock is shut and barred. A guard calls down: \"The King receives no "
                         "one today.\"")])
    castle = {
        'id': 'thing:castle_burlock', 'kind': 'building', 'at': [56, 43], 'size': [12, 7], 'kit': 'castle',
        'floor': LD.CASTLE_H, 'facing': 's', 'title': 'Castle Burlock',
        'parts': [
            {'id': 'curtain', 'at': [640, 768], 'size': [4864, 2304], 'wall_height': 768, 'roof': 'flat',
             'parapet': 96, 'battlements': True, 'windows': 'none', 'textures': dict(cs)},
            {'id': 'keep', 'at': [2176, 1024], 'size': [1792, 1408], 'wall_height': 1536, 'roof': 'hip',
             'roof_pitch': 52, 'windows': 'alternate', 'textures': dict(hc)},
            *towers,
            {'id': 'gate', 'at': [2432, 2816], 'size': [1280, 768], 'wall_height': 1024, 'roof': 'flat',
             'parapet': 96, 'battlements': True, 'windows': 'none', 'door_height': 512,
             'textures': dict(hc),
             'signs': [{'wall': 's', 'bay': 4, 'texture': 'xkburcrst', 'size': [128, 256], 'out': 16,
                        'bottom': 640}]},
        ],
        'door': 'none',
        'notes': "XD-07 Castle Burlock (A7). Royal castle kit: hc cream ashlar, cs grey curtain, xtslate cones, "
                 "Burlock's arms (D-3.1) over the gate. The gate is thing:castle_gate (a plot door is one bay, 128 wide)."}
    S(castle)
    # the castle gate: a 384-wide door in a stone frame set against the gatehouse's south wall, its sill on the rise
    # (1,888) at the castle lane's top (XD-07's own castle door is hclgdr 384 x 384); two leaves, chb1dl and its mirror
# (the user's double-door rule, A1's doors.half_wing)
    gate = {'id': 'thing:castle_gate', 'kind': 'doorway', 'at': [62, 50.06], 'turn': 0, 'width': 384, 'height': 448,
            'depth': 96, 'floor': LD.CASTLE_H, 'textures': {'door': 'chb1dl', 'wall': 'chb1'},
            'title': 'Castle Burlock', 'effects': gate_effects,
            'notes': "XD-07 Castle Burlock's gate (A7): sealed with a line until XD-07 opens its own way out to X4."}
    if DOORWAY_LEAVES:
        gate['leaves'] = 2
    if XD07_LIVE:
        gate['into'] = into('xeen_xd07.blv', XD07_ARRIVAL)
        gate.pop('effects')
    S(gate)
    # the castle lane: a ramp from the village square up the rise's face to the gate (576 over 3.5 cells)
    S({'id': 'thing:castle_ramp', 'kind': 'stairs', 'line': [[62, 53.6], [62, 49.95]], 'width': 640, 'ramp': True,
       'rise': LD.CASTLE_H - LD.VILLAGE_H, 'textures': {'wall': 'chb1', 'top': 'cwb'},
       'title': 'The castle lane', 'notes': "Up to the gate from the village square."})
    # ======== the village wall (grey castle stone), gates south (King's road) and east (stables, falls path)
    # F19 (the user 2026-11-22: "the walls should close off the city, not have a gap"): the wall's ends ran out at
    # (55, 50.6) and (69, 50.6), 970 short of the castle, and the rise's flanks are walkable: both ends now climb the
    # flank to the castle's south corner towers (57.25, 49) and (66.75, 49), the top following the land (level over
    # the village, which is flat) so it stays one piece with no joint (tools/xeen/wall_check.py).
    S({'id': 'thing:village_wall', 'kind': 'wall',
       'line': [[57.25, 49.0], [55, 49.0], [55, 62], [69, 62], [69, 49.0], [66.75, 49.0]],
       'height': 448, 'thickness': 128, 'top': 'follow', 'textures': {'wall': 'chb1'},
       'gates': [{'at': [62.5, 62], 'width': 512, 'height': 384, 'arch': 'round', 'sides': 8},
                 {'at': [69, 57.5], 'width': 448, 'height': 352, 'arch': 'round', 'sides': 8}],
       'title': "Burlock's village wall"})
    # ======== the village square: Well of Might, the mirror, the herald's board
    S({'id': 'thing:well_might', 'kind': 'well', 'at': [63.5, 57.0], 'title': 'Well of Might',
       'frame': {'height': 224, 'roof': 'gable', 'roof_height': 64},
       **daily('thing:well_might', [{'add': {'var': 'MightBonus', 'value': 10}}, {'text': '+10 Might until you rest'}],
               WATER)})
    S({'id': 'thing:burlock_mirror', 'kind': 'portal', 'at': [60.4, 55.6], 'radius': 112, 'sides': 12, 'turn': 90,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror', 'effects': [{'lua': 'Xeen.useMirror(4157, eventId, continueStep)'}],
       'notes': 'A4 4157, The Mirror of Castle Burlock (qbit 119003).'})
    S({'id': 'thing:herald_board', 'kind': 'sign', 'at': [65.3, 54.6], 'height': 224, 'width': 160,
       'title': "Herald's board",
       'effects': [msg("By order of the King: a reward to any who bring the Sixth Mirror to Castle Burlock. "
                       "Crusaders only past the gate.")]})
    for i, (x, y) in enumerate([(61.2, 58.6), (65.0, 58.6)]):
        S(deco('thing:square_flag_%d' % (i + 1), 'fla1__01', (x, y)))
    # ======== the jousting lists: a tilt barrier north-south, stands on the east side, pavilions north
    S({'id': 'thing:tilt_barrier', 'kind': 'fence', 'line': [[69.5, 64.2], [69.5, 71.6]],
       'notes': 'The tilt barrier (it leads the eye north to the castle).'})
    S({'id': 'thing:lists_stand', 'kind': 'building', 'at': [72.5, 64.5], 'size': [1.5, 5], 'turn': 0, 'kit': 'timber',
       'door': 'none', 'title': 'The stands',
       'parts': [{'id': 'stand', 'at': [64, 64], 'size': [640, 2432], 'wall_height': 256, 'posts': 32,
                  'post_every': 512, 'roof': 'lean_to', 'roof_low': 'w', 'windows': 'none'}]})
    for i, (x, y, title) in enumerate([(66.3, 63.8, "The challenger's pavilion"), (71.0, 63.8, "The champion's pavilion")]):
        S({'id': 'thing:pavilion_%d' % (i + 1), 'kind': 'tent', 'at': [x, y], 'size': [640, 640], 'height': 416,
           'title': title, 'open': True})
    S({'id': 'thing:lists_challenge', 'kind': 'sign', 'at': [67.6, 71.6], 'height': 256, 'width': 160,
       'title': "The Master of the Lists' challenge",
       'condition': {'stat': {'name': 'BaseMight', 'at_least': 30}},
       'effects': [{'add': {'var': 'Experience', 'value': 2000}},
                   status('You unhorse the practice knight in three passes. The crowd cheers. (+2,000 experience)')],
       'else_effects': [status('The practice knight unhorses you at the first pass. Come back with a stronger arm '
                            '(Might 30).')],
       'once': True})
    for i, (x, y) in enumerate([(66.2, 66.0), (66.2, 69.0)]):
        S(deco('thing:lists_flag_%d' % (i + 1), 'fla1__01', (x, y)))   # fla2__01 has no 3D model
    # ======== Burlock Cross: King Burlock's statue and the signposts
    S(deco('thing:king_statue', '7dec54', (60.6, 74.6), title="King Burlock's statue",
           effects=[msg('King Burlock, first of the name. North: the castle. West: Asp and the desert. East: '
                        'Rivercity and Firestone.')]))
    arms = {
        'junction:burlock_cross': [('Castle Burlock', 'n'), ('Asp', 'w'), ('Rivercity', 'e'), ('Jousting fields', 's')],
        'junction:east_fork': [('Mount Firestone', 'e'), ('Rivercity', 's'), ('Castle Burlock', 'w')],
        'junction:landing_fork': [("Nystor's landing", 'w'), ('Rivercity', 's'), ('Castle Burlock', 'n')],
        'junction:west_fork': [('Desert', 'w'), ('Gargoyle Eyrie', 'n'), ('Castle Burlock', 'e')],
        'junction:asp_gate': [('Asp', 'w'), ('Castle Burlock', 'e'), ('Lifeforce Lagoon', 's')],
    }
    sign_at = {'junction:burlock_cross': (63.6, 75.2), 'junction:east_fork': (89.0, 75.0),
               'junction:landing_fork': (86.0, 98.0), 'junction:west_fork': (37.0, 61.0),
               'junction:asp_gate': (51.4, 82.6)}
    for i, j in enumerate(L1.SIGNPOSTS, 1):
        s = {'id': 'thing:signpost_%d' % i, 'kind': 'sign', 'at': list(sign_at[j]), 'height': 256,
             'arms': [{'title': t, 'toward': d} for t, d in arms[j]]}
        if j == 'junction:asp_gate':
            s['title'] = 'Signpost'
            s['effects'] = [hook('x4.sign_asp')]
        S(s)
    # ======== the King's Bridge over the river and its cairn (D-11.5)
    # F67 p1 (2026-11-25): on y 76.5, the middle of the road's tile row (a road line on a node line lays its tiles in
    # the row south of it, y 76-77): the deck at y 76 met the road with half its width beside it
    S({'id': 'thing:kings_bridge', 'kind': 'bridge', 'line': [[76.6, 76.5], [84.4, 76.5]], 'width': 640,
       'arches': {'count': 3, 'rise': 192, 'form': 'segment', 'pier_width': 256}, 'kerb': 96,
       'textures': {'deck': 'cwb', 'side': 'cwb1', 'pier': 'cwb1'}, 'title': "The King's Bridge"})
    S(deco('thing:bridge_cairn', 'rock26', (77.2, 77.6)))     # D-20: dressing (no click)
    # ======== the falls and the Olympian Fountain (+2 Might, permanent, once)
    # F67 p3/p4 (2026-11-25): the sheet leans out (`lean`), as the shipped falls and the rim falls do: an upright water
    # face is drawn with a level face's waves and read as a plain dark slab; the top water reaches only over the cut
    # row before the lip (back 768: it lay 1,088 up the tarn, 2 over its water) and the foot water only a half cell
    # out into the pool (768 before, a second slab over the pool's water)
    S({'id': 'thing:falls', 'kind': 'waterfall', 'line': [[80.5, 40.2], [80.5, 42.5]], 'top': LD.TARN_H,
       'foot': LD.RIVER_LVL, 'width': 1024, 'back': 768, 'pool': 256, 'lean': 448, 'spread': 1.3,
       'title': 'The falls'})
    S({'id': 'thing:olympian_fountain', 'kind': 'fountain', 'at': [75.5, 48.0], 'title': 'Olympian Fountain',
       'tiers': [[96, 48]], 'textures': {'wall': 'chb1'},
       'condition': {'not': {'map_var': 'olympian_drunk'}},
       'effects': [{'set': {'var': {'map_var': 'olympian_drunk'}, 'value': 1}},
                   {'add': {'var': 'BaseMight', 'value': 2}}, {'text': '+2 Might (permanent)'}],
       'else_effects': [{'text': 'The water is cold from the range.'}]})
    # ======== Asp: the well, the eight pedestals (D-4, XD-25 1), the rule stone, the undercroft stair, the mirror
    wx, wy = L1.ASP_WELL
    S({'id': 'thing:asp_well', 'kind': 'well', 'at': [wx + 0.5, wy + 0.5], 'title': "Asp's well",
       'frame': {'height': 200}, 'effects': [{'text': 'The water smells faintly of snake.'}]})
    for i, (cx, cy) in enumerate(L1.pedestals(), 1):
        pid = 'thing:pedestal_%d' % i
        S({'id': pid, 'kind': 'platform', 'at': [cx + 0.5, cy + 0.5], 'size': [160, 160], 'height': 112,
           'textures': {'top': 'chb1s', 'wall': 'chb1'}, 'title': 'Pedestal',
           'condition': {'all': [{'not': {'qbit': 'asp_pedestals'}}, {'not': {'map_var': 'ped_%d' % i}}]},
           'effects': [{'set': {'var': {'map_var': 'ped_%d' % i}, 'value': 1}},
                       {'hide': pid + '_blue'}, {'show': pid + '_red'}, hook('q-c5.pedestal_touch')],
           'else_effects': [{'lua': 'if not IsQBitSet(QBit(112101)) then'},
                            {'set': {'var': {'map_var': 'ped_%d' % i}, 'value': 0}},
                            {'show': pid + '_blue'}, {'hide': pid + '_red'},
                            {'lua': 'end'}, hook('q-c5.pedestal_touch')],
           'notes': 'Pedestal %d clockwise from the south-west (D-4): a blue or a red cap shown.' % i})
        for colour, tex, size, high in (('blue', CAP_BLUE, 176, 24), ('red', CAP_RED, 168, 28)):
            S({'id': '%s_%s' % (pid, colour), 'kind': 'platform', 'at': [cx + 0.5, cy + 0.5], 'size': [size, size],
               'height': high, 'raise': 112, 'textures': {'top': tex, 'wall': tex}, 'same_event_as': pid})
    # the rule stone beside the stair's cut (D-95: moved off the cut, 42.1, 81.4 before)
    S({'id': 'thing:rule_stone', 'kind': 'decoration', 'decoration': 'rock65', 'at': [43.2, 83.0],
       'title': 'Rule stone', 'effects': [hook('q-c5.pedestal_rhyme')]})
    # D-95: the stair's mouth in the end face of its sunken cut (was a hatch mound at 41.5, 81.5), the revetments and
    # the cap behind it (XD25_CUT); event, window and arrival as before
    for st in XD25_CUT.structures(
            {'id': 'thing:xd25_stair', 'kind': 'culvert', 'height': 176, 'width': 320, 'outflow': 0,
             'water_level': 0, 'title': 'The undercroft stair', 'hint': 'Cellar stair',
             **({'into': into('xeen_xd25.blv', XD25_ARRIVAL)} if XD25_LIVE else
                {'effects': [msg('A stair goes down under the square into the dark. Hissing comes up it, and rubble '
                                 'blocks the way below the third step.')]}),
             'notes': "XD-25 Asp Undercroft (A7): open from day one (the field of light inside drops with "
                      "q-c5.pedestals)."}):
        S(st)
    S({'id': 'thing:asp_mirror', 'kind': 'portal', 'at': [41.6, 88.5], 'radius': 112, 'sides': 12, 'turn': 0,
       'textures': {'membrane': {'texture': 'xmirror'}},
       'title': 'Magic Mirror', 'effects': [{'lua': 'Xeen.useMirror(4177, eventId, continueStep)'}],
       'notes': "A4 4177, The Mirror of Asp (opens with q-c5.done)."})
    # Sarah Slither's lisp (aaze0054-like source line, MAPS X4) on her door's board; the town sign
    S({'id': 'thing:asp_sign', 'kind': 'sign', 'at': [51.8, 84.6], 'height': 224, 'width': 160, 'title': 'Asp',
       'effects': [msg('Asp. Travellers welcome. (Someone has added: "Ssstay out.")')]})
    # ======== the Autumn Druid's grove (Q-C1, T1-C)
    S({'id': 'thing:druid_ring', 'kind': 'stone_ring', 'at': [26, 70], 'radius': 640, 'count': 6, 'lintel': False,
       'title': "The Autumn Druid's ring"})
    # ======== the barbarian camp to burn (x4.barbarian_camp)
    # D-144 (F69b): a click burns it, the hook's line on the status line; the source's "You have stumbled upon a
    # Barbarian encampment. Burn?" was a free Yes/No whose No changed nothing (no cost, no war or peace)
    # D-152: the tents stay drawn after the burn, so the after-line says what is drawn; the bones and the skull pile
    # go with the camp (and stay gone: evt:barbarian_camp_burnt)
    burn = ('if IsQBitSet(QBit(116060)) then evt.StatusText("Scorched planks. The barbarians will not camp here '
            'again.", 4) return end XeenQuests.hook("x4.barbarian_camp") '
            + ' '.join('HideThing("%s")' % t for t in BARBARIAN_DRESS_IDS))
    for i, (x, y, w, d) in enumerate([(26.4, 51.2, 896, 704), (29.4, 51.0, 768, 640), (26.8, 54.4, 768, 640)]):
        S({'id': 'thing:barbarian_tent_%d' % (i + 1), 'kind': 'tent', 'at': [x, y], 'size': [w, d], 'height': 384,
           'title': 'Barbarian tent', 'open': i != 1, 'lua': burn})
    S(deco('thing:barbarian_fire', 'cmpfyr00', (28.4, 53.4), title='Campfire'))
    S({'id': 'thing:barbarian_chest', 'kind': 'chest', 'at': [28.4, 52.75], 'title': "The chief's chest",
       'chest': {'level': 3, 'random_items': 3}})
    for i, (d, at) in enumerate(BARBARIAN_DRESS):
        S(deco(BARBARIAN_DRESS_IDS[i], d, at))
    # ======== the renegade knights' camp (burn: a line and experience) and the quintain field
    for i, (x, y) in enumerate([(55.0, 102.0), (57.6, 102.2)]):
        S({'id': 'thing:knight_tent_%d' % (i + 1), 'kind': 'tent', 'at': [x, y], 'size': [768, 640], 'height': 416,
           'title': 'Torn pavilion', 'open': True,
           'condition': {'not': {'map_var': 'knights_camp_burnt'}},
           'effects': [{'set': {'var': {'map_var': 'knights_camp_burnt'}, 'value': 1}},
                       {'add': {'var': 'Experience', 'value': 1500}},
                       status("You put the renegades' pavilions to the torch. (+1,500 experience)")],
           'else_effects': [{'text': 'Charred canvas and a broken lance rack.'}]})
    S(deco('thing:knight_fire', 'dec24', (56.4, 103.6), title='Campfire'))
    S({'id': 'thing:knights_chest', 'kind': 'chest', 'at': [55.9, 103.9], 'title': "The renegades' chest",
       'chest': {'level': 3, 'random_items': 2}})
    S(deco('thing:quintain', 'dec13', (60.5, 93.5), title='Quintain',
           **daily('thing:quintain', [{'add': {'var': 'AccuracyBonus', 'value': 5}},
                                      status('You tilt at the quintain and duck the swinging sack. '
                                          '(+5 Accuracy until you rest)')],
                   [status('The quintain creaks round on its post. Enough tilting for one day.')])))
    # ======== the ogres' camp in the red hills (burn) and the dwarves' things
    S({'id': 'thing:ogre_camp', 'kind': 'decoration', 'decoration': 'dec24', 'at': [106.0, 86.0],   # fire01: no model
       'title': "The ogres' fire",
       'condition': {'not': {'map_var': 'ogre_camp_burnt'}},
       'effects': [{'set': {'var': {'map_var': 'ogre_camp_burnt'}, 'value': 1}},
                   {'add': {'var': 'Experience', 'value': 1500}},
                   status("You scatter the ogres' fire into their bedding and the camp burns. (+1,500 experience)")],
       'else_effects': [{'text': 'Ashes and gnawed bones.'}]})
    S({'id': 'thing:ogre_chest', 'kind': 'chest', 'at': [107.3, 84.6],   # out of the ogres' spread (check_spawn_clear)
        'title': "The ogres' loot",
       'chest': {'level': 3, 'random_items': 2}})
    for i, (d, at) in enumerate([('7dec18', (104.8, 86.8)), ('dec19', (107.4, 87.2)), ('7rock08', (104.6, 84.6))]):
        S(deco('thing:ogre_dress_%d' % (i + 1), d, at))
    S({'id': 'thing:dwarf_stone', 'kind': 'sign', 'at': [96.0, 90.0], 'height': 224, 'width': 160,
       'title': 'Boundary stone',
       'effects': [msg('Here begin the hills of the Red Dwarves. Mind the adits.')]})
    S({'id': 'thing:ore_cart', 'kind': 'crate', 'at': [101.2, 97.4], 'title': 'Ore cart',
       'chest': {'level': 2, 'random_items': 2}})
    adit = {'id': 'thing:xd02_adit', 'kind': 'doorway', 'at': [104.0, 95.5], 'turn': 90, 'height': 320, 'floor': 1504,
            'width': 256, 'depth': 448, 'hood': 64,
            'textures': {'door': '7solid01', 'wall': 'cwb1'}, 'title': 'The west adit',
            'condition': {'qbit': 'x4_adit_open'},
            'else_effects': [msg('Rock fills the adit to the roof. Someone inside could drag it clear.')],
            'into': {'map': 'xeen_xd02.blv', 'at': list(XD02_ADIT_ARRIVAL[:3]),
                     'facing': XD02_ADIT_ARRIVAL[3] * 2048 // 360},
            'notes': "XD-02 Red Dwarf Mines' west adit (M3, qbit 110020): open once the winch inside has dragged the "
                     "fall clear."}
    S(adit)
    # torches either side of the adit and the miners' spoil (OUTDOOR_REBUILD_PROCEDURE: dungeon entrances that read)
    for i, at in enumerate([(103.75, 94.85), (103.75, 96.15)]):
        S(deco('thing:adit_torch_%d' % (i + 1), 'dec06', at))
    S(deco('thing:adit_spoil', '7rock08', (103.4, 93.9)))
    # ======== the eyrie (XD-26), its sky-crack ledge, the waystone; the gargoyles' roost
    S({'id': 'thing:xd26_eyrie', 'kind': 'cave_mouth', 'at': [46, 41], 'size': [1024, 1024],
       'mouth': {'width': 512, 'height': 416, 'depth': 128}, 'textures': {'shell': 'cwb1', 'door': '7solid01'},
       'roughness': 0.7, 'seed': 4, 'title': 'The Gargoyle Eyrie', 'hint': 'Gargoyle Eyrie',
       **({'into': into('xeen_xd26.blv', XD26_ARRIVAL)} if XD26_LIVE else
          {'effects': [msg('Wings beat somewhere far up inside the mountain. A slide of fresh scree chokes the way in.')]}),
       'notes': 'XD-26 Gargoyle Eyrie (A7): its mouth leads back here (DOORS.md).'})
    # the skull pile 0.9 west and 0.4 north (2026-11-25, town_fit decorations.slope): at (44.6, 41.4) its rim reached
    # the cave mouth's own land (1,792 at node (45, 42)), which wins over its level pad; it stood 40-57 over its rim
    for i, (d, at) in enumerate([('7dec18', (45.0, 42.2)), ('dec19', (47.2, 42.4)), ('sklplrev', (43.7, 41.0))]):
        S(deco('thing:eyrie_bones_%d' % (i + 1), d, at))
    S({'id': 'thing:sky_crack_ledge', 'kind': 'platform', 'at': [49.5, 35.5], 'size': [768, 512], 'height': 32,
       'textures': {'top': 'cwb', 'wall': 'cwb1'}, 'title': 'A ledge high on Gargoyle Peak',
       'notes': "D-4: XD-26's sky crack lets out here (one way); the whole savannah below."})
    S({'id': 'thing:eyrie_waystone', 'kind': 'sign', 'at': [42.4, 50.6], 'height': 224, 'width': 160,
       'title': 'Waystone',
       'effects': [msg("Down: Carlawna's hut. Up: the Gargoyle Eyrie. Gargoyles take anything that shines.")]})
    S({'id': 'thing:gargoyle_roost', 'kind': 'chest', 'at': [88.0, 37.2], 'title': 'A heap of shiny things',
       'chest': {'level': 3, 'random_items': 3}})
    S(deco('thing:kings_beacon', 'dec60', (64.0, 31.6), title="The King's beacon"))
    S(deco('thing:crest_cairn_w', 'rock26', (40.5, 26.6), title="Climbers' cairn",
           **daily('thing:crest_cairn_w', [{'add': {'var': 'LuckBonus', 'value': 5}},
                                           status('A cairn on the lip of the world. Below it, nothing but stars. You add '
                                               'a stone. (+5 Luck until you rest)')],
                   [status('You have added your stone today.')])))
    S(deco('thing:climber_bones', 'dec19', (22.4, 27.4), title="A climber's bones",
           effects=[msg('A climber\'s bones, picked clean, and a rope frayed through on the rock. Gargoyles.')]))
    S(deco('thing:crest_wind_stone', 'rock68', (75.5, 26.6), title='Wind stone',   # rock67: no model
           **daily('thing:crest_wind_stone', [{'add': {'var': 'SpeedBonus', 'value': 5}},
                                              status('The wind off the rim howls through a hole in the stone. Your feet '
                                                  'feel lighter. (+5 Speed until you rest)')],
                   [status('The wind howls through the stone. Nothing more.')])))
    # ======== the lava fields: the Shrine of Fire (D-11.2: inside the map), the burned caravan, the rim lookout
    S({'id': 'thing:shrine_fire', 'kind': 'building', 'at': [103, 44.5], 'size': [2, 2], 'kit': 'stone',
       'title': 'Shrine of Fire', 'facing': 's',
       'parts': [{'id': 'shrine', 'at': [128, 128], 'size': [768, 768], 'wall_height': 384, 'posts': 64,
                  'roof': 'hip', 'roof_pitch': 40, 'windows': 'none', 'textures': {'roof': 'xtslate'},
                  'title': 'Shrine of Fire',
                  'condition': {'not': {'map_var': 'fire_shrine_used'}},
                  'effects': [{'set': {'var': {'map_var': 'fire_shrine_used'}, 'value': 1}},
                              {'add': {'var': 'FireResistance', 'value': 5}},
                              {'text': '+5 Fire resistance (permanent)'}],
                  'else_effects': [{'text': 'The embers on the altar glow, and nothing more.'}]}],
       'door': 'none'})
    S(deco('thing:shrine_brazier', 'brazir2f', (104.0, 45.5), title='Brazier'))
    S(deco('thing:burned_wagon', 'dec24x', (105.6, 51.6), title='Burned caravan'))
    S({'id': 'thing:burned_strongbox', 'kind': 'chest', 'at': [106.4, 52.4], 'title': 'Charred strongbox',
       'chest': {'level': 3, 'random_items': 2}})
    S({'id': 'thing:rim_lookout', 'kind': 'building', 'at': [103, 30], 'size': [2, 2], 'kit': 'stone',
       'title': 'A broken watch post', 'facing': 's', 'door': 'none',
       'parts': [{'id': 'post', 'shape': 'round', 'at': [512, 512], 'radius': 320, 'sides': 8,
                  'wall_height': 256, 'ruin': {'height': [96, 256], 'gaps': 0.3}, 'textures': {'wall': 'chb1'},
                  'title': 'A broken watch post',
                  'effects': [msg('Scratched on the stone: "The stars are below us. Do not lean over."')]}]})
    # ======== the river: the mill ruin, the sunken barge, Joe's caravan, Nystor's landing
    S({'id': 'thing:mill_ruin', 'kind': 'building', 'at': [84, 60], 'size': [2, 2], 'kit': 'poor', 'door': 'none',
       'title': 'Burnt-out mill', 'facing': 'w',
       'parts': [{'id': 'mill', 'at': [64, 64], 'size': [896, 896], 'wall_height': 256,
                  'ruin': {'height': [96, 256], 'gaps': 0.25}, 'title': 'Burnt-out mill',
                  'effects': [msg("The miller's last ledger, charred at the edges: \"Gargoyles again off the falls. Took the "
                       "lambs and the weathercock.\"")]}]})
    S({'id': 'thing:sunken_barge', 'kind': 'crate', 'at': [78.0, 91.0], 'title': "A barge's cargo box",
       'chest': {'level': 2, 'random_items': 2}})
    S({'id': 'thing:joe_wagon', 'kind': 'tent', 'at': [88.4, 86.6], 'size': [640, 1024], 'height': 352,
       'title': "Joe's wagon", 'open': True})
    for i, (d, at) in enumerate([('bigbarel', (89.2, 87.9)), ('7dec21', (89.5, 87.9)), ('haybale2', (87.6, 85.6))]):
        S(deco('thing:joe_dress_%d' % (i + 1), d, at))
    # D-174 (xeen-fb4-outdoor9): the land end on node line 83 (as installed since D-170): on line 82 the deck's
    # quarter-width edge ran past the lake's corner node (82, 102) at 640 and the end stood 39 over the land beyond
    # (town_fit bridges.step) once common/wild.py stopped taking the jetty's own cut for water
    S({'id': 'thing:nystor_jetty', 'kind': 'bridge', 'line': [[83.0, 101.0], [79.4, 101.0]], 'width': 384,
       'height': LD.BANK + 32, 'kerb': 0, 'textures': {'deck': 'trim11_32'}, 'title': "Nystor's jetty"})
    S({'id': 'thing:nystor_post', 'kind': 'sign', 'at': [82.4, 100.4], 'height': 256, 'width': 128,
       'title': "Captain Nystor's landing",
       'condition': {'qbit': 'nystor_upriver'},
       'else_effects': [msg("A mooring post with Captain Nystor's mark. \"Closed until the ogres stop throwing "
                            "boulders.\"")],
       # D-150: the post is the door of the boat back to Rivercity (A4's x4.yml house 4187, route 434, q-c23.done),
       # closed as the Asp houses are until then; before A4's row lands, its old line
       **({'house': NYSTOR_HOUSE} if NYSTOR_HOUSE else
          {'effects': [msg('Captain Nystor\'s boat calls here on its way upriver. Ask at his dock in Rivercity.')]})})
    S({'id': 'thing:nystor_boathouse', 'kind': 'building', 'at': [83, 98.5], 'size': [2, 1.5], 'kit': 'timber',
       'facing': 'w', 'door': 'none', 'title': "Nystor's boathouse",
       'parts': [{'id': 'house', 'at': [48, 48], 'size': [928, 672], 'wall_height': 320, 'roof': 'gable',
                  'ridge_along': 'ew', 'roof_pitch': 36, 'textures': {'roof': 'hhm1rf'}}]})
    # ======== chests with a reason in the south and west
    S({'id': 'thing:saddlebags', 'kind': 'crate', 'at': [52.0, 91.6], 'title': "A fallen charger's saddlebags",
       'chest': {'level': 2, 'random_items': 2}})
    S({'id': 'thing:champions_barrow', 'kind': 'chest', 'at': [70.0, 86.2], 'title': "The champions' grave goods",
       'chest': {'level': 3, 'random_items': 2},
       'effects': [{'text': 'Here lie the champions of the lists. They fell off last.'}]})
    # D-20: the barrow stone and the graves are dressing; their lines are the chests' (rock65 for rock66: no model)
    S(deco('thing:barrow_stone', 'rock65', (70.0, 85.2)))
    for i, at in enumerate([(26.2, 95.4), (27.4, 95.2), (26.4, 96.8), (27.8, 96.7), (28.6, 95.9)]):
        S(deco('thing:asp_grave_%d' % (i + 1), 'rock65', at))
    S({'id': 'thing:sexton_chest', 'kind': 'chest', 'at': [25.4, 96.2], 'title': "The sexton's chest",
       'chest': {'level': 2, 'random_items': 2},
       'effects': [{'text': 'Beside it, five graves, a shed snakeskin across each.'}]})
    # ======== the obelisk, the wells and the small devices (D-11.5)
    S({'id': 'thing:obelisk', 'kind': 'obelisk', 'at': [48, 66.5], 'height': 768, 'title': 'Obelisk',
       'effects': [{'lua': 'XeenQuests.hook("obelisks.x4")'}]})   # A3's hook: the word, its bit, the autonote (A5)
    for sid, at, title, eff, line in (
            ('thing:herders_well', (40.4, 101.0), "Herders' well", 'EnduranceBonus', '+5 Endurance until you rest'),
            ('thing:wayfarers_well', (96.6, 71.2), "Wayfarers' well", 'SpeedBonus', '+5 Speed until you rest'),
            ('thing:savannah_well', (93.0, 50.0), "Herders' well", 'MightBonus', '+5 Might until you rest')):
        S({'id': sid, 'kind': 'well', 'at': list(at), 'title': title, 'frame': {'height': 200},
           **daily(sid, [{'add': {'var': eff, 'value': 5}}, {'text': line}], WATER)})
    S(deco('thing:standing_stone', 'rock68', (21.0, 83.0), title='Standing stone',
           **daily('thing:standing_stone', [{'add': {'var': 'PersonalityBonus', 'value': 5}},
                                            status('The stone is warm from the sun. You feel bolder. '
                                                '(+5 Personality until you rest)')],
                   [status('No one seems to be listening.')])))
    # D-20: the jouster's grave and the red waymark are dressing (no click)
    S(deco('thing:jousters_grave', 'rock65', (69.0, 106.0)))
    S(deco('thing:red_waymark', 'rock68', (104.0, 76.0)))
    # ======== the edges: X6 west, X7 east (not built), X3 south-west (D-11.6); the south edge's west half
    if not X6_LIVE:
        S({'id': 'thing:west_road_end', 'kind': 'sign', 'at': [19.8, 59.2], 'height': 224, 'width': 160,
           'title': 'Sign', 'effects': [{'text': 'The road west to the Desert of the Sphinx is buried in drifts. Turn back.'}],
           'notes': 'X6 is not built: the west edge has no travel until it is.'})
    if not X7_LIVE:
        S({'id': 'thing:east_road_end', 'kind': 'sign', 'at': [108.2, 65.6], 'height': 224, 'width': 160,
           'title': 'Sign', 'effects': [{'text': 'Lava has crossed the road to Mount Firestone. Turn back.'}],
           'notes': 'X7 is not built: the east edge has no travel until it is.'})
    # D-11.6: the south edge leads to X3 west of x 0 (64 in cells) and to X2 east of it: the world's edge_spans table
    # (A1/A2) and the X3 neighbour's `span` in gen.py; no plate or barrier.
    S({'id': 'thing:x3_road_end', 'kind': 'sign', 'at': [37.4, 105.0], 'height': 224, 'width': 160, 'title': 'Sign',
       'effects': [{'text': 'Lifeforce Lagoon: south. Mind the floods.'}]})
    # ======== dressing: barrels in pairs by walls (DRESSING.md), hay by the stables, flowers
    for i, (p1, p2) in enumerate([((58.8, 51.75), (58.8, 52.05)), ((66.25, 51.9), (66.25, 52.2)),
                                  ((67.55, 54.75), (67.85, 54.75)), ((55.35, 57.4), (55.35, 57.7))]):
        S(deco('thing:village_barrel_%d' % (i + 1), 'bigbarel', p1))
        S(deco('thing:village_barrel_%d_pair' % (i + 1), 'smlbarel', p2))
    # The second bale in the stables' paddock (classic_kit's stables, 2026-11-24: the old shed is an open fenced
    # paddock now; at 68.6, 55.4 the bale stood through its east fence)
    for i, at in enumerate([(68.6, 54.8), (68.05, 55.85)]):
        S(deco('thing:stable_hay_%d' % (i + 1), 'haybale2', at))
    # Burlock's yard trees and flower beds (the scatter cannot place inside the village wall's box)
    for i, at in enumerate([(56.0, 54.1), (65.2, 58.2), (59.5, 61.3), (66.8, 61.6)]):
        S(deco('thing:village_tree_%d' % (i + 1), ['7tree19', '7tree28'][i % 2], at))
    for i, at in enumerate([(58.6, 57.9), (59.0, 58.2), (64.4, 56.3), (64.7, 56.6)]):
        S(deco('thing:village_flowers_%d' % (i + 1), 'flower11', at))
    return out


# ---------------------------------------------------------------- actors
def actors():
    out = []
    A = out.append
    # placed hostiles (L1 ACTORS): the barbarian camp, the ogres' camp, the renegade knights' camp
    # 2026-11-25 (oymap: "an actor stands inside thing:barbarian_tent_3", x 22.18-23.43): the four east of the tent,
    # [24.0, 56.4] spread 1.4 before
    A({'monster': BARBARIAN_ROWS['barbarian'], 'at': [28.7, 54.8], 'count': 4, 'spread': 0.9, 'group': 61,
       'hostile': True})
    A({'monster': BARBARIAN_ROWS['warrior'], 'at': [29.6, 53.2], 'count': 1, 'spread': 0, 'group': 61, 'hostile': True})
    A({'monster': BARBARIAN_ROWS['chief'], 'at': [27.4, 53.0], 'count': 1, 'spread': 0, 'group': 61, 'hostile': True})
    # D-142 (X4 rebuilt under it): XD-02's adit exit (103, 95) keeps 4,096 from the ogres (one stood at 3,993)
    A({'monster': OGRE_ROWS['ogre'], 'at': [106.6, 86.4], 'count': 3, 'spread': 0.9, 'group': 62, 'hostile': True})
    A({'monster': OGRE_ROWS['brute'], 'at': [105.2, 85.4], 'count': 1, 'spread': 0, 'group': 62, 'hostile': True})
    # F63 (check_spawn_clear): south of the pavilions, out of tent 2's walls ([56.4, 102.6] spread 1.2 before)
    A({'monster': KNIGHT_ROWS['jouster'], 'at': [56.2, 103.9], 'count': 3, 'spread': 0.8, 'group': 63,
       'hostile': True})
    A({'monster': KNIGHT_ROWS['leader'], 'at': [57.0, 103.8], 'count': 1, 'spread': 0, 'group': 63, 'hostile': True})
    # Burlock's people: D-96's villagers (gen.py fills these places, villagers.yml); the King's Guard (friendly)
    out.extend(V.slots(10))
    # a pair at the castle lane's foot, a pair beside the south gate, one beside the east gate (never in a gateway)
    for (x, y) in [(61.3, 53.9), (62.7, 53.9), (61.7, 62.9), (63.3, 62.9), (69.9, 56.6)]:
        A({'monster': KINGS_GUARD, 'at': [x, y], 'spread': 0, 'group': 51})
    # Asp's people: D-96's villagers (gen.py fills these places, villagers.yml)
    out.extend(V.slots(3))
    # A4's outdoor NPCs: Adam and Eve by the well, Joe at his wagon, the Autumn Druid in her ring (D-91: lane S's friendly row 11929 Xeen Druidess, Druidess A's body)
    for npc, kind, (x, y) in ((4301, '371', (43.4, 84.2)), (4302, '377', (43.4, 86.8)), (4320, '368', (87.6, 87.8)),
                              (4321, '11929', (26.0, 70.6))):
        A({'monster': kind, 'npc': npc, 'at': [x, y], 'spread': 0, 'group': 53})
    return out


def relations():
    # The world's relations.yml (A2) holds the families' hostility: Burlock knights 11140-11142, ogres, barbarians and
    # gargoyles are the party's foes; the King's Guard 11143 is friendly. No feud between the map's families.
    # D-91 (A5 s30): the Autumn Druid stands on S's row 11929 (friendly in the world): no map relation for row 517
    return []


def events():
    ev = []
    ev.append({'id': 'evt:barbarian_camp_burnt', 'trigger': 'load', 'condition': {'lua': 'IsQBitSet(QBit(116060))'},
               'effects': [{'hide': t} for t in BARBARIAN_DRESS_IDS],
               'notes': 'x4.barbarian_camp (D-144, D-152): the burnt camp keeps its bones and skull pile gone.'})
    # the pedestals' caps on entering the map, from the map's variables (blue or red shown)
    for i in range(1, 9):
        pid = 'thing:pedestal_%d' % i
        ev.append({'id': 'evt:pedestal_%d_load' % i, 'trigger': 'load',
                   'condition': {'map_var': 'ped_%d' % i},
                   'effects': [{'hide': pid + '_blue'}, {'show': pid + '_red'}],
                   'else_effects': [{'show': pid + '_blue'}, {'hide': pid + '_red'}]})
    # solved: the south-west one (1) and every second one round the ring red (D-4)
    cond = [({'map_var': 'ped_%d' % i} if i % 2 else {'not': {'map_var': 'ped_%d' % i}}) for i in range(1, 9)]
    ev.append({'id': 'evt:pedestals_set', 'trigger': 'timer', 'every': 1, 'once': True,
               'condition': {'all': cond + [{'not': {'qbit': 'asp_pedestals'}}]},
               'effects': [hook('q-c5.pedestals'),
                           msg('The pedestals hum together, and somewhere under the square a deep note answers.')],
               'notes': "Q-C5 (A3): the pedestals set; A3's hook q-c5.pedestals sets qbit 112101 and the field of "
                        'light in XD-25 drops.'})
    return ev
