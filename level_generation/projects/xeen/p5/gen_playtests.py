#!/usr/bin/env python3
"""P5: writes the L4 playtests (A5 sub-agent `agent:a5-p5`, 2026-11-21), after X9's: the walk (every cloud, the
ring, the causeway, every board and Rest Stop, the note, the observatory, the sealed stair door, the shrine refused),
the refusal alone, the ending played out and skipped, the reload after the ending, the disc, three falls in D-54's
shape (ring, causeway, shrine) and the hostility check. Event numbers from the build's ids.lock.yml and actor numbers
from the built Lua (run after b.sh's build)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

L4 = gen.BRIEF / 'L4'
BUILD = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'build'
LOCK = yaml.safe_load(open(BUILD / 'ids.lock.yml'))
EV = dict(LOCK.get('events', {}))
LANDING = (-4608, 2560)            # X5's entrance:p5_fall as A6 placed it (A3's Xeen.SkyFalls.p5)
LANDING_Z = 1504
CUBE, SCEPTER = 12365, 12366
SLEEPERS = [111760, 111761, 111762, 111763]          # m38.fire, air, earth, water (A3's m42.shrine requires)
CEREMONY_SHOWN = 111841
AWARD = 417
MAP = 'xeen_p5.blv'


def actor_numbers():
    """monster id -> actor index, read from the built evt:figures_load (ActorIndex() written as numbers)."""
    lua = (BUILD / 'xeen_p5.lua').read_text()
    m = re.search(r'-- evt:figures_load\n.*?\n((?:\s+evt\.SetMm9ActorCanReceiveDamage\(\d+, false\)\n)+)', lua)
    if not m:
        return {}
    idx = [int(v) for v in re.findall(r'\((\d+), false\)', m.group(1))]
    return dict(zip(('pharaoh', 'roland', 'kalindra'), idx))


ACTOR = actor_numbers() if go.FIGURES else {}
MON = {'pharaoh': go.PHARAOH, 'roland': go.ROLAND, 'kalindra': go.KALINDRA}


def party(level=61, gold=0):
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


def walk(x, y, z=None, radius=128, timeout=90):
    step = {'x': int(x), 'y': int(y), 'radius': radius, 'timeout_seconds': timeout, 'close_dialogs': True}
    if z is not None:
        step['z'] = int(z)
        step['z_tolerance'] = 200
    return {'walk_to': step}


def walk_h(pt, radius=160):
    z = gen.height_at(pt)
    return walk(pt[0], pt[1], z, radius)


def click_status(event, contains):
    return [{'play_lua': {'source': f"status(); click({EV[event]}); wait(0.5); local s = status() or ''; "
                                    f"if not string.find(s, {lua_str(contains)}, 1, true) then "
                                    f"error('{event}: status was ' .. s) end; close()"}}]


def click_dialog(event, contains):
    return [{'play_lua': {'source': f'click({EV[event]}); wait(0.5)'}},
            {'assert': {'dialog': {'active': True, 'text_contains': contains}}},
            {'play_lua': {'source': f"if not close() then error('{event} showed no window') end"}}]


def lua_str(t):
    return '"' + t.replace('\\', '\\\\').replace('"', '\\"') + '"'


def front_of(pid, d=448):
    p = gen.PLACE[pid]
    phi = math.radians(gen.COMPASS[p['face']])
    return (p['at'][0] + math.cos(phi) * d, p['at'][1] + math.sin(phi) * d)


def link_heads(lid):
    l = next(x for x in D.LINKS if x['id'] == lid)
    a, b, d, (ux, uy) = gen.link_cut(l, 0)
    return [(a[0] - ux * 400, a[1] - uy * 400), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (b[0] + ux * 400, b[1] + uy * 400)]


# the walk's order: each pad, its boards and hut, then the road on
ORDER = [
    ('room:crown', ['poi:board_nwc'], None),
    ('link:road_1', ['poi:board_kings_bounty'], None),
    ('room:rest_east', [], 'poi:rest_1'),
    ('link:road_2', ['poi:board_inherit'], None),
    ('room:ne_turn', ['poi:board_empire'], None),
    ('link:road_3', ['poi:board_spaceward'], None),
    ('room:observatory', [], None),
    ('link:road_4', ['poi:board_planets'], None),
    ('room:nw_turn', ['poi:board_vegas'], None),
    ('link:road_5', [], None),
    ('room:rest_west', [], 'poi:rest_2'),
    ('link:road_6', [], None),
    ('room:sw_turn', ['poi:board_tunnels'], None),
    ('link:road_7', ['poi:board_nuclear'], None),
    ('room:rest_south', [], 'poi:rest_3'),
    ('link:causeway', [], None),
    ('room:shrine', ['poi:board_mm'], None),
]


def main_walk():
    s = start()
    s += [{'assert': {'party_position': {'x': D.ARRIVAL[0], 'y': D.ARRIVAL[1], 'radius': 192, 'z_min': -20,
                                         'z_max': 60}}},
          {'note': "The crown: the stair house's door sealed until FD-03 (no move), the Pharaoh's note."},
          walk_h((gen.STAIR_DOOR[0], gen.STAIR_DOOR[1] + 192))]
    if go.FD03:
        s += [{'note': "FD-03 is installed: the door leads down to its entrance:p5_stair (224, 1904, 3072), facing west; "
                       "then back to P5's arrival"},
              {'play_lua': {'source': f'click({EV["evt:stair_door"]}); wait(1)'}},
              # F16 (A5 s30): the entrance window with A3's trans row 5064; OK goes down
              {'assert': {'dialog': {'active': True, 'text_contains': 'A tower of black stone'}}},
              {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_fd03.blv'}},
              {'assert': {'party_position': {'x': 224, 'y': 1904, 'radius': 200, 'z_min': 2992, 'z_max': 3232}}},
              {'load_map': {'map': MAP, 'pos': f'{gen.STAIR_DOOR[0]}, {gen.STAIR_DOOR[1] + 192}, 0'}},
              {'play_lua': {'source': 'wait(2); close()'}},
              {'assert': {'map': MAP}}]
    else:
        s += click_status('evt:stair_door', 'Not open yet')
        s += [{'assert': {'map': MAP}}]
    s += [walk_h((4096, -4032))]
    s += click_dialog('evt:pharaoh_note', "long road ahead")
    for where, boards, hut in ORDER:
        if where.startswith('room:'):
            if where == 'room:crown':
                pass
            elif where == 'room:shrine':
                s.append(walk_h((0, -1300)))
            else:
                x, y = gen.SPACE[where]['at']
                ax, ay = gen.SPACE[where]['anchor']
                s.append(walk_h((ax, ay)))
        else:
            s += [walk_h(p) for p in link_heads(where)]
        for b in boards:
            s.append(walk_h(front_of(b), 192))
            s += click_status(f'evt:{gen.key(b)}', go.hook_text(go.BOARD_HOOK[b]))
            s += click_status(f'evt:{gen.key(b)}_back', go.hook_text(go.BOARD_HOOK[b]))
        if hut:
            s.append(walk_h(front_of(hut, 640), 192))
            s += click_status(f'evt:{gen.key(hut)}_sign', 'Rest Stop')
            s += click_status(f'evt:{gen.key(hut)}_back', 'Rest Stop')
        if where == 'room:observatory':
            ox, oy = gen.OBS
            s.append(walk_h((ox, oy - gen.OBS_APOTHEM - 256), 160))
            s += click_status('evt:observatory', 'The observatory is closed.')
            s.append({'note': "The observatory's door never opens: the party still stands outside."})
    s += [{'note': "The shrine without the Cube, the Scepter and the sleepers: the Pharaoh's refusal."},
          walk_h((0, -900))]
    s += click_dialog('evt:shrine', 'Dragon Pharaoh, Guardian of Xeen')
    s += [{'assert': {'qbit_clear': [go.M42_DONE]}}, {'assert': {'map': MAP}}]
    return {'id': 'xeen.p5.l4', 'title': 'Clouds of the Ancients (P5 L4): the whole ring walked, every board, Rest '
            'Stop, the note, the observatory, the sealed stair door and the refused shrine', 'world': 'xeen',
            'mode': 'faithful', 'steps': s}


def at_shrine(done=False, ceremony=False):
    s = start()
    if done:
        s.append({'setup_shortcut': {'kind': 'set_qbit', 'id': go.M42_DONE}})
    if ceremony:
        s.append({'setup_shortcut': {'kind': 'set_qbit', 'id': CEREMONY_SHOWN}})
    s += [{'load_map': {'map': MAP, 'pos': f'0, -1200, {go.SHRINE_Z}'}},
          {'play_lua': {'source': 'wait(1.5); close()'}},
          {'assert': {'map': MAP}}]
    return s


def figures_hidden(hidden):
    out = []
    for nm in ('roland', 'kalindra'):
        if nm in ACTOR:
            out.append({'assert': {'actor_visible': {'actor_index': ACTOR[nm], 'monster_id': MON[nm], 'hidden': hidden}}})
    if 'pharaoh' in ACTOR:
        out.append({'assert': {'actor_visible': {'actor_index': ACTOR['pharaoh'], 'monster_id': MON['pharaoh'],
                                                 'hidden': False}}})
    return out


def wedding_shown():
    return figures_hidden(False)


def gift_touch(opens):
    """The gift (merge point 25's hidden chest). Before state:wedding the party walks into the chest's own spot (it is
    Invisible and Untouchable, as A1's mp25 test); after it a click from 160 south, looking north and down, opens it."""
    if not opens:
        return [{'set_pose': {'map': MAP, 'x': go.GIFT[0], 'y': go.GIFT[1] - 200, 'z': go.SHRINE_Z, 'yaw': 1.5708,
                              'pitch': 0.0}},
                {'advance_runtime': {'seconds': 0.3}},
                {'walk_to': {'x': go.GIFT[0], 'y': go.GIFT[1], 'z': go.SHRINE_Z, 'z_tolerance': 200, 'radius': 32,
                             'timeout_seconds': 10, 'close_dialogs': True}}]
    return [{'set_pose': {'map': MAP, 'x': go.GIFT[0], 'y': go.GIFT[1] - 160, 'z': go.SHRINE_Z, 'yaw': 1.5708,
                          'pitch': -0.6}},
            {'advance_runtime': {'seconds': 0.5}},
            {'press_interact': {}},
            {'advance_runtime': {'seconds': 0.5}},
            {'assert': {'chest_view': {'open': True}}},
            {'play_lua': {'source': 'wait(0.3); if held() ~= 0 then stow() end; close(); wait(0.3)'}}]


def refusal():
    s = at_shrine()
    s += [{'note': 'Only the Cube and the Scepter: the sleepers are still asleep, so the Pharaoh refuses.'},
          {'grant_item': {'item_id': CUBE, 'member_index': 0}}, {'grant_item': {'item_id': SCEPTER, 'member_index': 1}}]
    s += click_dialog('evt:shrine', 'Elemental Sleepers must be awakened')
    s += [{'assert': {'qbit_clear': [go.M42_DONE]}},
          {'play_lua': {'source': f"if not has_item({CUBE}) or not has_item({SCEPTER}) then "
                                  "error('the refusal took the items') end"}}]
    s += figures_hidden(True)
    s += [{'note': 'The gift is not there before state:wedding.'}] + gift_touch(False)
    return {'id': 'xeen.p5.l4.refusal', 'title': 'Clouds of the Ancients (P5): the shrine refuses a party without the '
            'four sleepers, and keeps nothing', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


CEREMONY = 'reading the vows'


def ending(skip):
    s = at_shrine()
    s += [{'grant_item': {'item_id': CUBE, 'member_index': 0}}, {'grant_item': {'item_id': SCEPTER, 'member_index': 1}}]
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': b}} for b in SLEEPERS]
    s += figures_hidden(True)
    s += [{'note': 'The gift is not there before state:wedding.'}] + gift_touch(False)
    s += [{'walk_to': {'x': 0, 'y': -900, 'z': go.SHRINE_Z + 8, 'z_tolerance': 200, 'radius': 160,
                       'timeout_seconds': 30, 'close_dialogs': True}},
          {'note': "The shrine with everything: A3's m42.shrine takes the two, sets m42.done, plays `unification`."},
          {'play_lua': {'source': f"click({EV['evt:shrine']})"}},
          {'advance_runtime': {'seconds': 0.5}},
          {'console': {'line': 'cinematic list', 'expect_contains': 'playing unification'}},
          {'assert': {'qbit_set': [go.M42_DONE]}},
          {'play_lua': {'source': f"if has_item({CUBE}) or has_item({SCEPTER}) then error('the items were not taken') end"}},
          {'assert': {'award_acquired': [{'id': AWARD, 'member_index': 0}]}}]
    if skip:
        s += [{'advance_runtime': {'seconds': 2.0}},
              {'note': 'Skipped: its event cues (state:wedding) still run, then the done event (A3\'s 42149).'},
              {'console': {'line': 'cinematic skip'}},
              {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}}]
    else:
        s += [{'advance_runtime': {'seconds': 12.0}},
              {'console': {'line': 'cinematic list', 'expect_contains': 'playing unification'}},
              {'note': 'Before the fade: the couple still hidden.'}] + figures_hidden(True) + \
             [{'advance_runtime': {'seconds': 11.0}},
              {'note': "In the fade (the cue at 22.5 s): state:wedding shown mid-visit."}] + wedding_shown() + \
             [{'advance_runtime': {'seconds': 12.5, 'present_dialogs': True}}]
    s += [{'note': "The done event: A3's m42.ceremony text, once."},
          {'assert': {'dialog': {'active': True, 'text_contains': CEREMONY}}},
          {'assert': {'qbit_set': [CEREMONY_SHOWN]}},
          {'play_lua': {'source': "if not close() then error('the ceremony showed no window') end"}},
          {'advance_runtime': {'seconds': 2.0, 'present_dialogs': True}},
          {'console': {'line': 'cinematic list', 'expect_contains': 'Cinematics: unification'}}]
    s += wedding_shown()
    s += [{'note': 'The gift (treasure 6) against the pavilion\'s back, shown with state:wedding: a click opens it.'},
          {'walk_to': {'x': go.GIFT[0], 'y': go.GIFT[1] - 288, 'z': go.SHRINE_Z, 'z_tolerance': 200, 'radius': 160,
                       'timeout_seconds': 40, 'close_dialogs': True}}] + gift_touch(True)
    s += [{'note': 'The shrine again: m42\'s else_text.'}, walk_h((0, -900))]
    s += click_dialog('evt:shrine', 'somebody has left cake')
    s += [{'note': 'A reload after the ending: the state is shown, no ceremony text again.'},
          {'load_map': {'map': MAP, 'pos': f'0, -1200, {go.SHRINE_Z}'}},
          {'advance_runtime': {'seconds': 1.5, 'present_dialogs': True}},
          {'assert': {'dialog': {'active': False}}}]
    s += wedding_shown()
    name = 'skipped' if skip else 'played'
    return {'id': f'xeen.p5.l4.ending_{name}', 'title': f'Clouds of the Ancients (P5): the ending {name}: m42.done, '
            'the items taken, state:wedding shown mid-visit, the ceremony text once, the gift, a reload',
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


def reload_after():
    s = at_shrine(done=True, ceremony=True)
    s += [{'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}}, {'assert': {'dialog': {'active': False}}}]
    s += wedding_shown()
    s += [walk_h((0, -900))]
    s += click_dialog('evt:shrine', 'somebody has left cake')
    return {'id': 'xeen.p5.l4.reload', 'title': 'Clouds of the Ancients (P5): a visit after m42.done shows the wedding '
            'state (figures, gift) and the quiet shrine', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def disc():
    s = at_shrine(done=True, ceremony=True)
    dx, dy = gen.DISC
    s += [walk_h((dx, dy - 320)),
          {'play_lua': {'source': f"status(); click({EV['evt:disc']}); wait(0.5)"}},
          {'advance_runtime': {'seconds': 1.0}},
          {'play_lua': {'source': "local s = status() or ''; if not string.find(s, 'You step onto the disc', 1, true) "
                                  "then error('the disc said: ' .. s) end"}},
          {'assert': {'map': MAP}},
          {'assert': {'party_position': {'x': D.ARRIVAL[0], 'y': D.ARRIVAL[1], 'radius': 256}}}]
    return {'id': 'xeen.p5.l4.disc', 'title': "Clouds of the Ancients (P5): after the ending the disc moves the party to "
            "entrance:fd03_roof with A3's line", 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# Each member's HP just after the fall (Xeen.SkyFallHeight 850 on the level-61 party: deterministic). None: probe run.
# Before merge point 26 (05:26) the landing never "landed" and the party kept its full 345/154/216/144.
# Since then the fall from 850 above X5's rock takes about a third: 233/105/147/98 (measured 2026-11-21 06:23,
# xrun/run_062348, the same from all three).
FALL_HP = None if os.environ.get('P5_FALL_PROBE') == '1' else [233, 105, 147, 98]


def hp_after_fall(label):
    if FALL_HP is None:
        return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': 1,
                                                                    'health_max': 100000}}} for k in range(4)]
    return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': hp, 'health_max': hp}}}
                                for k, hp in enumerate(FALL_HP)]


def fall(name, title, start_pt, yaw, seconds=2.5):
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}},
         {'play_lua': {'source': 'wait(2); close()'}},
         {'movement_segment': {'input': 'forward', 'seconds': seconds, 'actor_collision': True, 'actor_ai': True,
                               'start': {'map': MAP, 'x': start_pt[0], 'y': start_pt[1], 'z': start_pt[2],
                                         'yaw_degrees': yaw, 'pitch': 0},
                               'expect_stop': {'map': MAP, 'x': start_pt[0], 'y': start_pt[1], 'z': start_pt[2],
                                               'yaw_degrees': yaw, 'pitch': 0},
                               'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}},
         {'advance_runtime': {'seconds': 3.0, 'follow_map_move': True}},
         {'advance_runtime': {'seconds': 0.5}},
         {'assert': {'map': 'xeen_x5.odm'}},
         {'assert': {'party_position': {'x': LANDING[0], 'y': LANDING[1], 'radius': 256}}}]
    s += [{'console': {'line': 'hp show'}}]
    s += hp_after_fall('0.5 s after the landing: everyone alive, the fall\'s damage only (D-6.2)')
    s += [{'advance_runtime': {'seconds': 20.0}}]
    s += hp_after_fall('After 20 s on X5 (D-54): nobody has lost a point more')
    s += [{'assert': {'map': 'xeen_x5.odm'}}]
    return {'id': f'xeen.p5.l4.{name}', 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def hostility():
    s = start() + [{'advance_runtime': {'seconds': 2}},
                   {'assert': {'actor_count': {'hostile': True, 'max': 0}}}]
    if go.FIGURES:
        s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': go.M42_DONE}},
              {'setup_shortcut': {'kind': 'set_qbit', 'id': CEREMONY_SHOWN}},
              {'load_map': {'map': MAP, 'pos': f'0, -1200, {go.SHRINE_Z}'}},
              {'advance_runtime': {'seconds': 12}}]
        for m in (go.PHARAOH, go.ROLAND, go.KALINDRA):
            s += [{'assert': {'actor_count': {'monster_id': m, 'hostile': False, 'min': 1}}},
                  {'assert': {'actor_count': {'monster_id': m, 'hostile': True, 'max': 0}}},
                  {'assert': {'actor_count': {'monster_id': m, 'hurt': True, 'max': 0}}}]
        s += [{'assert': {'actor_count': {'hostile': True, 'max': 0}}}]
    return {'id': 'xeen.p5.l4.hostility', 'title': 'Clouds of the Ancients (P5): nothing hostile; the three figures '
            'peaceful and unhurt', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def write(name, data, header):
    with open(L4 / name, 'w') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


SHRINE_RIM_W = gen.G.ray_exit(gen.POLYS['room:shrine'], (0, 0), (-40000, 0))


if __name__ == '__main__':
    H = '# Written by output/studio_cal/p5/tools/gen_playtests.py; run with --world xeen --map xeen_p5.blv.\n'
    write('playtest.yml', main_walk(), "# Playtest of the Clouds of the Ancients (P5, L4): the walk.\n" + H)
    write('playtest_refusal.yml', refusal(), '# The shrine refuses without the four sleepers.\n' + H)
    write('playtest_ending_played.yml', ending(False), '# The ending played out (D-56 5).\n' + H)
    write('playtest_ending_skipped.yml', ending(True), '# The ending skipped: its event cues still run.\n' + H)
    write('playtest_reload.yml', reload_after(), '# A visit after the ending.\n' + H)
    write('playtest_disc.yml', disc(), '# The disc back to the crown (D-56 7).\n' + H)
    # falls: east off the east road (the ring), west off the causeway, north off the shrine behind the pavilion
    write('playtest_fall_ring.yml', fall('fall_ring', "Clouds of the Ancients (P5): a fall off the ring lands on X5's "
                                         'entrance:p5_fall, nobody dies, nobody hurt after (D-56 10)',
                                         (D.RING + 300, -1200, 50), 0, 1.0), '# A fall off the east road.\n' + H)
    cy = (-2931 + -1557) / 2
    write('playtest_fall_causeway.yml', fall('fall_causeway', "Clouds of the Ancients (P5): a fall off the causeway "
                                             "lands on X5's entrance:p5_fall (D-56 10)",
                                             (-250, int(cy), 490), 180, 1.0), '# A fall off the causeway.\n' + H)
    write('playtest_fall_shrine.yml', fall('fall_shrine', "Clouds of the Ancients (P5): a fall off the shrine's cloud "
                                           "lands on X5's entrance:p5_fall (D-56 10)",
                                           (int(SHRINE_RIM_W[0]) + 150, 0, 520), 180, 1.0), "# A fall off the shrine's west rim.\n" + H)
    write('playtest_hostility.yml', hostility(), '# Hostility: nothing hostile, the figures peaceful.\n' + H)
    print('written playtests', 'actors', ACTOR)
