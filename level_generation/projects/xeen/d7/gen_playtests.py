#!/usr/bin/env python3
"""D7: writes the L4 playtests (A6 sub-agent, sixteenth session, 2026-11-21), after X9's and P5's: the walk (the
rope's head, the ring all round through the four corners, the inner road, Olympus' three gates, the square, the dock),
hostility (the groups hostile, the bandits peaceful), the six falls in D-54's shape, a corner's question, the
Megadragon at its post. Event numbers from the build's ids.lock.yml (run after the build).

    python3 level_generation/projects/xeen/d7/gen_playtests.py [--probe]   # --probe: check each walk leg with oymap probe
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import re
import os
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import gen_objects as go  # noqa: E402
import gen_plan as gp  # noqa: E402

D = gen.D
L4 = gen.BRIEF / 'L4'
X = pathlib.Path(_REPO_ROOT, 'output/studio_cal/d7')
BUILD = X / 'build'
LOCK = yaml.safe_load(open(BUILD / 'ids.lock.yml'))
EV = dict(LOCK.get('events', {}))
MAP = 'xeen_d7.blv'
LEVEL = 55


def party(level=LEVEL, gold=0):
    return {'gold': gold, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': level, 'skills': [], 'equipment': {}}]}


def start(immortal=True):
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}}]
    if immortal:
        s.append({'setup_shortcut': {'kind': 'immortal', 'value': True}})
    return s + [{'play_lua': {'source': 'wait(2); close()'}}, {'assert': {'map': MAP}}]


def walk(pt, radius=192, timeout=120, close=True):
    z = gen.height_at(pt)
    step = {'x': int(pt[0]), 'y': int(pt[1]), 'radius': radius, 'timeout_seconds': timeout, 'close_dialogs': close}
    if z is not None:
        step['z'] = int(z)
        step['z_tolerance'] = 240
    return {'walk_to': step}


def lua_str(t):
    return '"' + t.replace('\\', '\\\\').replace('"', '\\"') + '"'


def link(lid):
    return next(x for x in D.LINKS if x['id'] == lid)


def link_points(lid, rev=False):
    """The link's heads 400 inside each island and its middle (on the paved band)."""
    a, b, d, (ux, uy) = gen.link_cut(link(lid), 0)
    pts = [(a[0] - ux * 400, a[1] - uy * 400), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (b[0] + ux * 400, b[1] + uy * 400)]
    return pts[::-1] if rev else pts


def centre(sid):
    return D.SPACE[sid]['at']


# ------------------------------------------------------------------------------------------------ the walk

RING = [('link:w3', False), ('link:w4', False), ('link:w5', False), ('link:n1', False), ('link:n2', False),
        ('link:n3', False), ('link:n4', False), ('link:n5', False), ('link:e1', False), ('link:e2', False),
        ('link:e3', False), ('link:s1', False), ('link:s2', False), ('link:s3', False), ('link:s4', False),
        ('link:s5', False), ('link:w1', False), ('link:w2', False)]

# Olympus' lanes (the houses stand in the way of a straight line): from each gate to the square and on
GATE = {name.split()[0].replace('-', '_'): g for name, g, _ in D.OLYMPUS_GATES}
SQUARE = (-4608, 6400)                           # entrance:olympus_square (south of the mirror)
OLYMPUS_IN_SW = [GATE['south_west'], (-7936, 5888), (-6272, 5888), (-5120, 5888), SQUARE]
OLYMPUS_TO_N = [SQUARE, (-3328, 6400), (-3328, 9216), (-3072, 10048), GATE['north']]
OLYMPUS_N_TO_E = [GATE['north'], (-3072, 10048), (-3328, 9216), (-3328, 7488), (-2048, 7488), (-768, 7488),
                  GATE['east']]
OLYMPUS_E_TO_DOCK = [GATE['east'], (-768, 7488), (-2048, 7488), (-3328, 7488), (-3328, 5888), (-3328, 4096),
                     (-2048, 3968), (-1280, 3616), (-640, 3200)]


def corner_ok(pt):
    """A walk point never on a corner's tip (stepping there asks the question)."""
    return all(math.hypot(pt[0] - c['at'][0], pt[1] - c['at'][1]) > gen.TIP_DISC + 512 for c in gen.CORNERS.values())


def walk_points():
    rope = next(a for a in D.ARRIVALS if a['id'] == 'entrance:d1_rope')['at']
    pts = [rope, (rope[0], rope[1] + 768), centre('room:rope_head')]
    for lid, rev in RING:
        pts += link_points(lid, rev)
        l = link(lid)
        pts.append(centre(l['b']))
    # the inner road: the launch road, the Broken Launch, the causeway, Olympus, the east causeway
    pts += link_points('link:launch_road') + [centre('room:broken_launch')] + link_points('link:olympus_west')[:2]
    pts += OLYMPUS_IN_SW + OLYMPUS_TO_N[1:] + OLYMPUS_N_TO_E[1:]
    pts += [link_points('link:olympus_east')[1], GATE['east']] + OLYMPUS_E_TO_DOCK[1:]
    assert all(corner_ok(p) for p in pts)
    return [(int(round(x)), int(round(y))) for x, y in pts]


def main_walk():
    s = start()
    s += [{'note': "The rope's head (entrance:d1_rope): the map's start. The walk checks the ways, not the fights: "
                   "the hostile groups are cleared first (playtest_hostility counts them)."},
          {'play_lua': {'source': "log('cleared ' .. clear_hostiles(80000))"}}]
    for p in walk_points():
        s.append(walk(p))
    s += [{'note': "Lucio's jetty: entrance:olympus_dock; m31.arrival ran on stepping onto it (its started bit)."},
          {'assert': {'qbit_set': [111620]}},
          {'assert': {'map': MAP}}]
    return {'id': 'xeen.d7.l4', 'title': "The Skyroads (D7 L4): from the rope's head round the whole ring through the "
            "four corners, the inner road, into Olympus by its south-west gate, the square, out of the north and east "
            "gates, Lucio's jetty", 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# ------------------------------------------------------------------------------------------------ hostility

COUNTS = {}
for g in D.GROUPS:
    COUNTS[g['actor']] = COUNTS.get(g['actor'], 0) + g['count']


def hostility():
    s = start() + [{'advance_runtime': {'seconds': 2}}]
    for mid, n in COUNTS.items():
        s += [{'assert': {'actor_count': {'monster_id': mid, 'hostile': True, 'min': n, 'max': n}}}]
    s += [{'assert': {'actor_count': {'monster_id': go.MEGADRAGON, 'hostile': True, 'min': 1, 'max': 1}}},
          {'assert': {'actor_count': {'monster_id': go.SKY_BANDIT, 'hostile': False, 'min': 8, 'max': 8}}},
          {'assert': {'actor_count': {'monster_id': go.SKY_BANDIT, 'hostile': True, 'max': 0}}},
          {'note': 'Nobody fights anybody else: after 20 s nothing is hurt (the party far off at the rope).'},
          {'advance_runtime': {'seconds': 20}},
          {'assert': {'actor_count': {'hurt': True, 'max': 0}}}]
    return {'id': 'xeen.d7.l4.hostility', 'title': 'The Skyroads (D7): the 50 placed and the Megadragon hostile, the '
            'eight Sky Bandits peaceful, nobody hurt', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# ------------------------------------------------------------------------------------------------ falls (D-54)

# Each member's HP just after a fall (Xeen.SkyFallHeight 850 on the level-55 party: deterministic). None: probe run.
FALL_HP = [214, 97, 136, 90]    # measured 2026-11-21 (xrun/run_042105, run_042336): a fall of 850 (D-6.2)
FULL_HP = [315, 142, 198, 132]  # the level-55 party unhurt
# Per zone, each member's HP just after the landing, re-measured on merge point 26 (A1's landing fix: a fall ending
# within 1 unit of the floor now lands; output/studio_cal/a6/s17/d7falls_052727): every zone takes the fall of 850;
# a landing 1 unit lower takes one point more, so each zone accepts both (ab12 gave either on two runs). The D-54 check (nothing lost in the 20 s
# after) holds in every zone.
FALL_HP_1 = [213, 96, 135, 89]
ZONE_HP = {'d7_ab12': FALL_HP, 'd7_cd12': FALL_HP_1, 'd7_ef12': FALL_HP, 'd7_ab34': FALL_HP_1, 'd7_cd34': FALL_HP_1,
           'd7_ef34': FALL_HP_1}


# (key, island, rim direction): the party starts 192 inside that island's rim and walks off it
FALL_STARTS = [('d7_ab12', 'room:griffin_watch', 90), ('d7_cd12', 'room:north_crossing', 90),
               ('d7_ef12', 'room:east_rest', 90), ('d7_ab34', 'room:skywaymen_camp', 270),
               ('d7_cd34', 'room:steam_post', 270), ('d7_ef34', 'room:south_rest', 270)]


def fall_start(sid, deg):
    c = centre(sid)
    far = (c[0] + 40000 * math.cos(math.radians(deg)), c[1] + 40000 * math.sin(math.radians(deg)))
    rim = gen.G.ray_exit(gen.P[sid], c, far)
    L = math.hypot(rim[0] - c[0], rim[1] - c[1])
    return (int(rim[0] - (rim[0] - c[0]) / L * 192), int(rim[1] - (rim[1] - c[1]) / L * 192), D.SPACE[sid]['floor'])


def hp_after_fall(label, key=None):
    hp = ZONE_HP[key]
    if os.environ.get('D7_FALL_PROBE') == '1':
        hp = None
    if hp is None:
        return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': 1,
                                                                    'health_max': 100000}}} for k in range(4)]
    lo = [min(a, b) for a, b in zip(FALL_HP_1, FALL_HP)] if hp in (FALL_HP, FALL_HP_1) else hp
    hi = [max(a, b) for a, b in zip(FALL_HP_1, FALL_HP)] if hp in (FALL_HP, FALL_HP_1) else hp
    return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': lo[k],
                                                              'health_max': hi[k]}}} for k in range(4)]


def fall(key, sid, deg):
    x, y, z, yaw, m = gp.FALLS[key]
    st = fall_start(sid, deg)
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}},
         {'play_lua': {'source': 'wait(2); close()'}},
         {'movement_segment': {'input': 'forward', 'seconds': 1.5, 'actor_collision': True, 'actor_ai': True,
                               'start': {'map': MAP, 'x': st[0], 'y': st[1], 'z': st[2], 'yaw_degrees': deg,
                                         'pitch': 0},
                               'expect_stop': {'map': MAP, 'x': st[0], 'y': st[1], 'z': st[2], 'yaw_degrees': deg,
                                               'pitch': 0},
                               'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}},
         {'advance_runtime': {'seconds': 3.0, 'follow_map_move': True}},
         {'advance_runtime': {'seconds': 0.5}},
         {'assert': {'map': m}},
         {'assert': {'party_position': {'x': x, 'y': y, 'radius': 256}}}]
    s += hp_after_fall("0.5 s after the landing: everyone alive, the fall's damage only (D-6.2)", key)
    if os.environ.get('D7_FALL_PROBE') == '1':
        s += [{'advance_runtime': {'seconds': 3.0}}] + hp_after_fall('probe: 3 s after', key)
        s += [{'play_lua': {'source': "log('STATUS ' .. (status() or ''))"}}]
    s += [{'advance_runtime': {'seconds': 20.0}}]
    s += hp_after_fall(f'After 20 s on {m} (D-54): nobody has lost a point more', key)
    s += [{'assert': {'map': m}}]
    return {'id': f'xeen.d7.l4.fall_{key[3:]}', 'title': (f"The Skyroads (D7): a fall off {D.SPACE[sid]['name']} "
            f"(zone {key[3:].upper()}) lands on {m}'s entrance:d7_fall; a healthy level-{LEVEL} party lives and loses "
            "nothing more in 20 s (D-54, Q10)"), 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# ------------------------------------------------------------------------------------------------ a corner

WRONG = go.HOOKS['m38.corner_wrong']


def corner():
    sp = 'room:fire_corner'
    tip = gen.CORNERS[sp]['at']
    a, _ = gen.tip_spit(sp)
    YAW = int(math.degrees(math.atan2(tip[1] - a[1], tip[0] - a[0])))
    L = math.hypot(tip[0] - a[0], tip[1] - a[1])
    ST = (int(tip[0] - (tip[0] - a[0]) / L * 640), int(tip[1] - (tip[1] - a[1]) / L * 640))
    s = start()
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': 111600}},
          {'load_map': {'map': MAP, 'pos': f'{int(a[0])}, {int(a[1])}, {gen.floor_of(sp) + 8}'}},
          {'play_lua': {'source': 'wait(1.5); close()'}},
          {'note': "The Fire Corner's tip: stepping on it, the sky asks 'What do you seek?'"},
          {'movement_segment': {'input': 'forward', 'seconds': 0.8, 'actor_collision': True, 'actor_ai': True,
                                'start': {'map': MAP, 'x': ST[0], 'y': ST[1], 'z': gen.floor_of(sp) + 8,
                                          'yaw_degrees': YAW, 'pitch': 0},
                                'expect_stop': {'map': MAP, 'x': ST[0], 'y': ST[1], 'z': gen.floor_of(sp) + 8,
                                                'yaw_degrees': YAW, 'pitch': 0},
                                'loose_tolerance': True, 'tolerance_xy': 2000, 'tolerance_z': 400}},
          {'advance_runtime': {'seconds': 0.5}},
          {'play_lua': {'source': "log('CORNER ' .. (status() or ''))"}},
          {'answer_input': {'text': 'Gold'}},
          {'advance_runtime': {'seconds': 1.0}},
          {'note': "A wrong answer runs A3's m38.corner_wrong: its line, and the party stays on D7."},
          {'assert': {'dialog': {'active': True, 'text_contains': 'The sky says nothing'}}},
          {'play_lua': {'source': "close()"}},
          {'assert': {'map': MAP}}]
    return {'id': 'xeen.d7.l4.corner', 'title': "The Skyroads (D7): the Fire Corner's tip asks 'What do you seek?'; "
            "a wrong answer runs m38.corner_wrong and the party stays", 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# ------------------------------------------------------------------------------------------------ the Megadragon

def megadragon():
    hx, hy = D.BOSS['at']
    l = link('link:dragon_road')
    a, b, d, (ux, uy) = gen.link_cut(l, 0)
    near = (int(b[0] - ux * 600), int(b[1] - uy * 600))       # on the dragon road, 600 before the roost's rim
    s = start()
    s += [{'assert': {'actor_count': {'monster_id': go.MEGADRAGON, 'near': [hx, hy, 256], 'min': 1, 'max': 1}}},
          {'note': 'The party on its road in sight of the roost (immortal), 30 s: it stays at its post (D-54).'},
          {'set_pose': {'map': MAP, 'x': near[0], 'y': near[1], 'z': gen.height_at(near) + 8,
                        'yaw_degrees': int(math.degrees(math.atan2(hy - near[1], hx - near[0]))), 'pitch': 0}},
          {'advance_runtime': {'seconds': 10.0}},
          {'assert': {'actor_count': {'monster_id': go.MEGADRAGON, 'near': [hx, hy, D.BOSS['leash'] + 256],
                                      'min': 1, 'max': 1}}},
          {'advance_runtime': {'seconds': 20.0}},
          {'assert': {'actor_count': {'monster_id': go.MEGADRAGON, 'near': [hx, hy, D.BOSS['leash'] + 256],
                                      'min': 1, 'max': 1}}},
          {'note': 'Its hoard: Wyrmfang and the roof key.'},
          {'set_pose': {'map': MAP, 'x': D.POINTS[[p['id'] for p in D.POINTS].index('poi:chest_hoard')]['at'][0],
                        'y': D.POINTS[[p['id'] for p in D.POINTS].index('poi:chest_hoard')]['at'][1] - 256,
                        'z': D.SPACE['room:roost']['floor'] + 8, 'yaw_degrees': 90, 'pitch': 0}},
          {'play_lua': {'source': (f"loot_chest({EV['evt:chest_hoard']}); wait(1); while held() ~= 0 do stow() end; "
                                   f"close(); if not has_item({go.WYRMFANG}) then error('no Wyrmfang') end; "
                                   f"if not has_item({go.ROOF_KEY}) then error('no roof key') end")}}]
    return {'id': 'xeen.d7.l4.megadragon', 'title': "The Skyroads (D7): the Megadragon holds its post on Alamar's "
            "hatch with the party in sight (D-54); its hoard holds Wyrmfang and the roof key", 'world': 'xeen',
            'mode': 'faithful', 'steps': s}


def doors():
    """Session 18 (A6): Alamar's hatch into DD-17 before m33.done (the roof key; without the Soul Box DD-17's
    m33.roof_arrival sets the party back on the roof at entrance:dd17_roof), the Pyramid's sky door into DD-15 after
    m30.done, a genie's lamp (S's xeen_genielamp) asking its wish."""
    def arrival(name):
        a = next(a for a in D.ARRIVALS if a['id'] == name)
        return int(a['at'][0]), int(a['at'][1])

    def pose(xy, yaw=0):
        return {'set_pose': {'map': MAP, 'x': xy[0], 'y': xy[1], 'z': int(gen.height_at(xy) or 0) + 8,
                             'yaw_degrees': yaw, 'pitch': 0}}

    hatch, sky = EV['evt:hatch_dd17'], EV['evt:sky_door']
    roof = arrival('entrance:dd17_roof')
    s = start()
    s += [{'note': "Alamar's hatch without the roof key: 'Descend to Castle Alamar?' Yes, A3's locked line"},
          pose(roof), {'advance_runtime': {'seconds': 0.5}},
          {'play_lua': {'source': f'click({hatch}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Megadragon has the key'}}},
          {'play_lua': {'source': 'close()'}}, {'assert': {'map': MAP}},
          {'note': "s32: with the key (12377) but without Corak's Soul Box: m33.roof_arrival's refusal on the status "
                   "line, no move (D-89: the hatch checks it, DD-17 no longer throws the party out)"},
          {'grant_item': {'item_id': go.ROOF_KEY}},
          {'play_lua': {'source': f'click({hatch}); wait(0.5)'}},
          {'play_lua': {'source': "local s = status(); if not string.find(s, 'nothing I need to fear', 1, true) then "
                                  "error('no refusal: ' .. s) end"}},
          {'assert': {'map': MAP}},
          {'note': "With the Soul Box (12364): the entrance window (row 5050), OK, DD-17 at entrance:d7_roof"},
          {'grant_item': {'item_id': 12364, 'member_index': 0}},
          {'play_lua': {'source': f'click({hatch}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
          {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
          {'assert': {'map': 'xeen_dd17.blv'}},
          {'play_lua': {'source': 'discard(12364)'}},
          {'load_map': {'map': MAP}},
          {'note': "The Pyramid's sky door before m30.done: A3's d7.pyramid_door 'Access Denied!', no move"},
          pose(arrival('entrance:dd15_sky')), {'advance_runtime': {'seconds': 0.5}},
          {'play_lua': {'source': f'click({sky}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Access Denied!'}}},
          {'play_lua': {'source': 'close()'}},
          {'assert': {'map': MAP}},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 111600, 'value': True}},
          {'note': "After m30.done: 'Enter the Pyramid?' Yes into DD-15 at entrance:d7_sky"},
          {'play_lua': {'source': f'click({sky}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
          {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
          {'assert': {'map': 'xeen_dd15.blv'}}]
    grate = EV['evt:sewer_grate']
    s += [{'note': "The Olympus Sewer's grate (session 19): 'Descend into the sewer?' No stays; Yes into DD-26 at "
                   "entrance:d7_stair (0, 0, 0) facing 512"},
          {'load_map': {'map': MAP}},
          pose(arrival('entrance:dd26_stair')), {'advance_runtime': {'seconds': 0.5}},
          {'play_lua': {'source': f'click({grate}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Even their sewer is marble', 'action_label_present': 'Close'}}},
          {'select_topic': {'match_label': 'Close'}}, {'advance_runtime': {'seconds': 0.5}}, {'assert': {'map': MAP}},
          {'play_lua': {'source': f'click({grate}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
          {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
          {'assert': {'map': 'xeen_dd26.blv'}},
          {'assert': {'party_position': {'x': 0, 'y': 0, 'radius': 64, 'facing': 512, 'facing_within': 64}}}]
    lamp = next(p for p in D.POINTS if p['id'] == 'poi:lamp_kind')
    s += [{'note': "A genie's lamp (S's xeen_genielamp): the kind genie asks for a wish"},
          {'load_map': {'map': MAP}},
          pose((int(lamp['at'][0]), int(lamp['at'][1]) - 200), 90), {'advance_runtime': {'seconds': 0.5}},
          {'play_lua': {'source': f"click({EV['evt:lamp_kind']}); wait(0.5)"}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Thank you for releasing me'}}},
          {'play_lua': {'source': 'close()'}}]
    if go.LIVE['fd01']:
        # session 23 (D-69 change 6): after m33.done the hatch asks its own Yes/No and moves into FD-01's
        # entrance:d7_roof; FD-01's ladder (its own Yes/No, A3's q-d26.depths_hatch) back to D7's entrance:fd01_roof
        fx, fy, fz, ff = go.LIVE['fd01']
        back = arrival('entrance:fd01_roof')
        fd01_lua = gen.ROOT / 'assets_dev/worlds/xeen/events/maps/xeen_fd01.lua'
        m = re.search(r'RegisterEvent\((\d+), "[^"]*", function\(continueStep\)\n(?:(?!RegisterEvent).)*?'
                      r'evt\.MoveToMap\([^)]*"xeen_d7\.blv"', fd01_lua.read_text(), re.S)
        s += [{'note': "After m33.done (111662): 'Descend to Castle Alamar?' No stays; Yes (the key) into FD-01 "
                       "Alamar Depths at entrance:d7_roof (D-61 Q14, D-69 change 6)"},
              {'load_map': {'map': MAP}},
              {'setup_shortcut': {'kind': 'set_qbit', 'id': 111662, 'value': True}},
              {'grant_item': {'item_id': go.ROOF_KEY}},
              pose(roof), {'advance_runtime': {'seconds': 0.5}},
              {'play_lua': {'source': f'click({hatch}); wait(0.5)'}},
              {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}}, {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_fd01.blv'}},
              {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
              {'play_lua': {'source': "log('FD01 ' .. (status() or '')); "
                                      "for i = 1, 3 do if not close() then break end wait(0.5) end"}},
              {'assert': {'party_position': {'x': fx, 'y': fy, 'radius': 64, 'facing': ff, 'facing_within': 64}}}]
        if m:
            s += [{'note': f"FD-01's ladder (event {m.group(1)}): 'Climb up through the hatch?' Yes (roof_unlocked) "
                           "back to D7's entrance:fd01_roof"},
                  {'play_lua': {'source': f'click({m.group(1)}); wait(0.5)'}},
                  {'assert': {'dialog': {'active': True, 'text_contains': 'Climb up through the hatch?'}}},
                  {'answer_input': {'text': 'Yes'}},
                  {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
                  {'assert': {'map': MAP}},
                  {'assert': {'party_position': {'x': back[0], 'y': back[1], 'radius': 256}}}]
    return {'id': 'xeen.d7.l4.doors', 'title': "The Skyroads (D7): Alamar's hatch into DD-17 (refused without the "
            "Soul Box), the Pyramid's sky door into DD-15 after m30.done, the sewer grate into DD-26, a genie's lamp", 'world': 'xeen',
            'mode': 'faithful', 'steps': s}


def write(name, data, header):
    with open(L4 / name, 'w') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


def probe():
    """oymap probe each walk leg on the map installed in the scratch root."""
    root = X / 'root/assets_dev'
    pts = walk_points()
    bad = 0
    for p, q in zip(pts, pts[1:]):
        zp, zq = gen.height_at(p), gen.height_at(q)
        r = subprocess.run([str(gen.ROOT / 'openyamm-studio/build-xeen/oymap'), 'probe', MAP, '--world', 'xeen',
                            '--assets', str(root), '--from', f'{p[0]},{p[1]},{int(zp or 0) + 8}',
                            '--to', f'{q[0]},{q[1]},{int(zq or 0) + 8}'], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        ok = any(l.startswith('straight walk: possible') for l in out)
        if not ok:
            bad += 1
            print('LEG', p, '->', q, ' | '.join(l.strip() for l in out[3:6])[:300])
    print('legs', len(pts) - 1, 'bad', bad)


if __name__ == '__main__':
    if '--probe' in sys.argv:
        probe()
        sys.exit(0)
    H = '# Written by output/studio_cal/d7/tools/gen_playtests.py; run with --world xeen --map xeen_d7.blv.\n'
    write('playtest.yml', main_walk(), '# Playtest of the Skyroads (D7, L4): the walk.\n' + H)
    write('playtest_hostility.yml', hostility(), '# Hostility.\n' + H)
    write('playtest_corner.yml', corner(), "# A corner's question.\n" + H)
    write('playtest_megadragon.yml', megadragon(), '# The Megadragon at its post; its hoard.\n' + H)
    write('playtest_doors.yml', doors(), "# Alamar's hatch, the Pyramid's sky door, a lamp.\n" + H)
    for key, sid, deg in FALL_STARTS:
        write(f'playtest_fall_{key[3:]}.yml', fall(key, sid, deg), f'# A fall in zone {key[3:]} (D-54).\n' + H)
    print('written playtests; walk points', len(walk_points()))
