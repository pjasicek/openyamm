#!/usr/bin/env python3
"""X9: writes the L4 playtests (A5 sub-agent, 2026-11-21), modelled on X8's: playtest.yml (every cloud, bridge, the
unseen way, the booths, statues, nests, offerings, chests and the gate), three falls (the stair clouds, a chain cloud,
Xeendom) and the hostility check. Event numbers from the build's ids.lock.yml (run after b.sh's build)."""
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import design as D  # noqa: E402
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

L4 = gen.BRIEF / 'L4'
LOCK = yaml.safe_load(open(L4 / 'ids.lock.yml'))
EV = dict(LOCK.get('events', {}))
LANDING = D.FALL_LANDING_X2['at']
LINK = {l['id']: l for l in D.LINKS}
LINGUIST = 116240
CRUSADERS = 110047
LORD_XEEN_DOLL = 12371
XD19_GATE_R = 36   # XD-19's evt:gate_r (A7's ids.lock.yml): its right leaf, the way out to X9


def party(level=46, gold=0):
    return {'gold': gold, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': level, 'skills': [], 'equipment': {}}]}


def walk(x, y, z=None, radius=128, timeout=90):
    step = {'x': int(x), 'y': int(y), 'radius': radius, 'timeout_seconds': timeout, 'clear_hostiles': 2500,
            'close_dialogs': True}
    if z is not None:
        step['z'] = int(z)
        step['z_tolerance'] = 200
    return {'walk_to': step}


def heads(lid, reverse=False):
    """A link's two ends 400 inside each cloud and its middle, in walking order, with floor heights."""
    l = LINK[lid]
    p, q = gen.link_ends(l)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    za, zb = gen.floor_of(l['a']), gen.floor_of(l['b'])
    pts = [(p[0] - ux * 400, p[1] - uy * 400, za), ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, (za + zb) / 2),
           (q[0] + ux * 400, q[1] + uy * 400, zb)]
    return pts[::-1] if reverse else pts


def cross(lid, reverse=False):
    return [walk(x, y, z) for x, y, z in heads(lid, reverse)]


def at(sid, dx=0, dy=0):
    x, y = gen.SPACE[sid]['at']
    return walk(x + dx, y + dy, gen.floor_of(sid))


def near(pid, dx=0, dy=-320):
    x, y = gen.at(pid)
    return walk(x + dx, y + dy, gen.space_floor(pid), radius=160)


def click_dialog(event, contains):
    # F13 / D-90 (A5 s29): a touch's line is a status line (A3's hooks), a note or a choice's answer a window
    return [{'play_lua': {'source': f'status(); click({EV[event]}); wait(0.5)'}},
            {'play_lua': {'source': f"local s = status(); local w = close(); if not w and not string.find(s, {contains!r}, "
                                    f"1, true) then error('{event} showed neither a window nor its line: ' .. s) end"}}]


def nest(tag):
    bit = go.HOOKS[f'x9.nest_{tag}']['sets'][f'nest_{tag}']
    return [near(f'poi:nest_{tag}', 0, -520),
            {'play_lua': {'source': f'click({EV[f"evt:nest_{tag}"]}); wait(0.5)'}},
            # D-72 (A5 s30): Yes/No buttons
            {'assert': {'dialog': {'active': True, 'action_label_present': 'Yes'}}},
            {'select_topic': {'match_label': 'Yes'}},
            {'advance_runtime': {'seconds': 1}},
            {'play_lua': {'source': f"close(); if not qbit({bit}) then error('nest {tag}: its bit is not set') end"}}]


def loot(chest):
    return [near(f'poi:chest_{chest}', 0, -288),
            {'play_lua': {'source': f'loot_chest({EV["evt:chest_" + chest]}); wait(1); if held() ~= 0 then stow() end; '
                                    'close()'}}]


def gift(k):
    return [near(f'poi:offering_{k}'),
            {'play_lua': {'source': f'click({EV[f"evt:offering_{k}"]}); wait(0.5); if held() ~= 0 then stow() end'}},
            {'assert': {'dialog': {'active': True, 'text_contains': 'gift for a Crusader'}}},
            {'play_lua': {'source': 'close()'}}]


def main_walk():
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': party(gold=20000)}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'assert': {'map': 'xeen_x9.blv'}},
         {'assert': {'party_position': {'x': gen.ARRIVAL[0], 'y': gen.ARRIVAL[1], 'radius': 160, 'z_min': 290,
                                        'z_max': 360}}},
         {'note': "The stair clouds: the 'Danger' sign, the west statues, the south-west nest."},
         at('room:stair_head', 0, 0), near('poi:danger_sign')]
    s += click_dialog('evt:danger_sign', 'Danger! Go back!')
    s += cross('link:west_neck') + [at('room:west_wing'), near('poi:statue_1', 0, -360)]
    s += click_dialog('evt:statue_1', 'strange runes')
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': LINGUIST}}, near('poi:statue_2', 0, 360)]
    s += click_dialog('evt:statue_2', 'faithful vassal')
    s += cross('link:sw_neck') + [at('room:sw_nest')] + nest('sw') + loot('hollow')
    s += [{'note': 'The west chain: four lone clouds and their offering statues, the cache.'}]
    s += cross('link:west_bridge_1') + [at('room:west_pillar', 0, -400), near('poi:offering_1')]
    s += click_dialog('evt:offering_1', 'kept for Crusaders')
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': CRUSADERS}}]
    s += gift(1)
    s += cross('link:west_bridge_2') + gift(2)
    s += cross('link:west_bridge_3') + gift(3)
    s += cross('link:west_bridge_4') + [at('room:nw_isle')] + gift(4) + loot('cache')
    s += [{'note': "The back lot and Slick's carnival: the four booths."}]
    s += cross('link:back_lot_bridge') + [at('room:back_lot', 512, -512), {'clear_hostiles': {'radius': 4000}}]
    s += cross('link:back_lot_neck') + [at('room:carnival')]
    for name, title in go.BOOTHS:
        s += [near(f'poi:{name}_game', 0, 0)]
        s += click_dialog(f'evt:booth_{name}', 'Slick:')
    # Slick's Sure-Eye Tonic beside the Accuracy booth (D-70 Q1): two bottles once, then the else line
    tx, ty = go.TONIC_AT
    s += [walk(tx - 192, ty, gen.space_floor('poi:accuracy_game'), radius=160)]
    s += [{'play_lua': {'source': f'click({EV["evt:tonic_crate"]}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Sure-Eye Tonic, two bottles'}}},
          {'play_lua': {'source': 'close(); for _ = 1, 3 do if held() ~= 0 then stow() end end'}}]
    s += click_dialog('evt:tonic_crate', 'The free round was the first one.')
    s += [{'note': "The Xeen road to the gate: the prize stand, the gate refused without a doll, sealed with one."}]
    s += cross('link:xeen_road') + [at('room:gate_court', 0, 0)]
    sx, sy = gen.at('poi:prize_stand')
    s += [walk(sx + 320, sy, gen.floor_of('room:gate_court'))]
    s += click_dialog('evt:prize_stand', "Get lost and don't come back")
    s += [walk(gen.RETURN[0], gen.RETURN[1] + 192, gen.BASE)]
    s += click_dialog('evt:gate_l', 'without a cupie doll')
    s += [{'grant_item': {'item_id': LORD_XEEN_DOLL, 'member_index': 0}}]
    if go.XD19:
        # the doll shown, the right leaf leads into XD-19 (A7's entrance:x9_gate, facing north); XD-19's right leaf
        # (its event 36, the studio's leave, direct) brings the party back to entrance:xd19_gate before the gate
        x, y, z, f = go.XD19
        # F16 (A5 s30): the gate shows the MM6-MM8 entrance window with A3's trans row 5019; OK enters
        s += [{'play_lua': {'source': f'click({EV["evt:gate_r"]}); wait(1)'}},
              {'assert': {'dialog': {'active': True, 'text_contains': 'Castle Xeen, sitting on its cloud'}}},
              {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_xd19.blv'}},
              {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
              {'play_lua': {'source': 'close(); wait(0.3)'}},
              {'assert': {'party_position': {'x': x, 'y': y, 'radius': 256}}},
              {'execute_event': {'id': XD19_GATE_R}},
              # XD-19's way out (A7, F16) shows the game's leave window
              {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
              {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_x9.blv'}},
              {'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}},
              {'play_lua': {'source': 'close(); wait(0.3)'}},
              {'assert': {'party_position': {'x': gen.RETURN[0], 'y': gen.RETURN[1], 'radius': 256}}}]
    else:
        s += click_dialog('evt:gate_r', 'Not open yet')
    s += [{'note': "Round the castle's apron, up the aviary stair: the sign, three nests, the hoard."}]
    x0, y0, x1, y1 = gen.SHELL
    s += [walk(0, y0 - 512, gen.BASE), walk(x1 + 512, y0 - 512, gen.BASE), walk(x1 + 512, gen.CY - 2048, gen.BASE)]
    s += [{'clear_hostiles': {'radius': 4000}}]
    s += cross('link:aviary_stair') + [near('poi:aviary_sign', 0, -320)]
    s += click_dialog('evt:aviary_sign', "Xeen's Aviary")
    s += [{'clear_hostiles': {'radius': 5000}}]
    s += nest('a1') + nest('a2') + nest('a3') + loot('hoard')
    s += [{'note': 'Down the east chain: the east horn, the offering ledge, the lone pillar, the south-east nest.'}]
    s += cross('link:east_bridge_4', True) + [at('room:east_horn')] + gift(6) + loot('pack')
    s += cross('link:east_bridge_3', True) + gift(5)
    s += cross('link:east_bridge_2', True) + [at('room:east_pillar')]
    s += cross('link:east_bridge_1', True) + [at('room:se_nest')] + nest('se')
    s += cross('link:se_neck', True) + [at('room:east_wing'), near('poi:statue_3', 0, -360)]
    s += click_dialog('evt:statue_3', 'island tower')
    s += [near('poi:statue_4', 0, 360)]
    s += click_dialog('evt:statue_4', "Xeen's life can take")
    s += [{'note': "The brink and the unseen way: 'Xeen--9N.', nine cells north over the gap to Xeendom."}]
    s += cross('link:east_neck', True) + cross('link:brink_neck') + [near('poi:nine_north', 448, -320)]
    s += click_dialog('evt:nine_north', 'Xeen--9N.')
    s += cross('link:unseen_way') + [near('poi:xeendom_sign', 448, 320)]
    s += click_dialog('evt:xeendom_sign', 'Now entering Xeendom')
    s += cross('link:landing_road') + [at('room:carnival')]
    bits = [go.HOOKS[f'x9.nest_{t}']['sets'][f'nest_{t}'] for t in go.NESTS]
    s += [{'play_lua': {'source': 'for _, k in ipairs({' + ', '.join(map(str, bits)) + '}) do if not qbit(k) then '
                                  "error('nest bit ' .. k .. ' not set') end end"}},
          {'assert': {'map': 'xeen_x9.blv'}}]
    return {'id': 'xeen.x9.l4', 'title': 'Clouds of Xeen (X9 L4): every cloud, bridge and the unseen way walked; signs, '
            'statues, nests, offerings, booths, the prize stand, the gate and the chests used', 'world': 'xeen',
            'mode': 'faithful', 'steps': s}


def fall(name, title, start, yaw, seconds=2.5):
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': party()}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'clear_hostiles': {'radius': 40000}},
         {'movement_segment': {'input': 'forward', 'seconds': seconds, 'actor_collision': True, 'actor_ai': True,
                               'start': {'map': 'xeen_x9.blv', 'x': start[0], 'y': start[1], 'z': start[2],
                                         'yaw_degrees': yaw, 'pitch': 0},
                               'expect_stop': {'map': 'xeen_x9.blv', 'x': start[0], 'y': start[1], 'z': start[2],
                                               'yaw_degrees': yaw, 'pitch': 0},
                               'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}},
         # the fall ends on X2 within about 3 s (L4 NOTES, "Falls")
         {'advance_runtime': {'seconds': 3.0, 'follow_map_move': True}},
         {'advance_runtime': {'seconds': 0.5}},
         {'assert': {'map': 'xeen_x2.odm'}},
         {'assert': {'party_position': {'x': LANDING[0], 'y': LANDING[1], 'radius': 256}}}]
    s += hp_after_fall('Just after the fall: everyone alive, the fall\'s damage only')
    # D-54: X2's lake dragons are leashed at least 5,888 from the landing and the tower door; 20 s on X2, then the walk
    # to Darzog's door, and nobody has lost a point more
    s += [{'advance_runtime': {'seconds': 20.0}}]
    s += hp_after_fall('After 20 s on X2 (D-54)')
    s += [{'walk_to': {'x': TOWER_DOOR[0], 'y': TOWER_DOOR[1], 'z': LANDING_Z, 'z_tolerance': 600, 'radius': 160,
                       'timeout_seconds': 60}},
          {'assert': {'map': 'xeen_x2.odm'}}]
    s += hp_after_fall("At Darzog's tower door (D-54)")
    return {'id': f'xeen.x9.l4.{name}', 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': s}


# Each member's HP just after the fall. Until merge point 26 (05:26) the landing on X2 never "landed" (no sound, no
# damage) and the party kept its full 270/124/171/114; since then the fall from 850 above X2's ground takes about a
# third: 181/85/115/78 (the orchestrator's figures from A1's run, checked by the 2026-11-21 sixth-hour runs). A change
# of the classes' HP or the fall height changes these.
FALL_HP = [181, 85, 115, 78]
TOWER_DOOR = (-15731, 3014)     # before Darzog's door, as X2's walk stands there
LANDING_Z = 768


def hp_after_fall(label):
    return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': hp, 'health_max': hp}}}
                                for k, hp in enumerate(FALL_HP)]


def castle_gone():
    """state:castle_gone: with m35.done set, the map reloaded at the gate: the gate's spot speaks A3's line and the
    party walks through where the shell stood (hidden and passable)."""
    gx, gy = gen.GATE
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': party()}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'setup_shortcut': {'kind': 'set_qbit', 'id': go.M35_DONE}},
         {'load_map': {'map': 'xeen_x9.blv', 'pos': f'{gen.RETURN[0]}, {gen.RETURN[1] - 256}, {gen.BASE}'}},
         {'play_lua': {'source': 'wait(2); close()'}},
         {'clear_hostiles': {'radius': 40000}},
         {'assert': {'map': 'xeen_x9.blv'}},
         {'note': "The gate's spot: A3's x9.castle_gone (aaze0027:44)."},
         {'walk_to': {'x': gx, 'y': int(gy - 160), 'z': gen.BASE, 'z_tolerance': 200, 'radius': 96,
                      'timeout_seconds': 30, 'close_dialogs': False, 'expect': 'dialog'}},
         {'advance_runtime': {'seconds': 0.5}},
         {'assert': {'dialog': {'active': True, 'text_contains': 'recently stood here'}}},
         {'play_lua': {'source': "if not close() then error('the castle-gone line showed no window') end"}},
         {'note': 'Through where the walls, the keep and a tower stood: the shell is gone.'}]
    x0, y0, x1, y1 = gen.SHELL
    for x, y in ((0, gen.CY), (x1 - 768, y1 - 768), (0, y1 - 256)):
        s.append({'walk_to': {'x': int(x), 'y': int(y), 'z': gen.BASE, 'z_tolerance': 200, 'radius': 160,
                              'timeout_seconds': 60, 'close_dialogs': True}})
    s.append({'assert': {'map': 'xeen_x9.blv'}})
    return {'id': 'xeen.x9.l4.castle_gone', 'title': 'Clouds of Xeen (X9): after m35.done the castle is gone, its '
            "spot speaks, its cloud stays", 'world': 'xeen', 'mode': 'faithful', 'steps': s}


QF1_PARTY = {'gold': 0, 'food': 20, 'members': [
    {'name': 'Brokk', 'class': 'Knight', 'level': 62, 'might': 30, 'intellect': 20, 'skills': [], 'equipment': {}},
    {'name': 'Hild', 'class': 'Cleric', 'level': 62, 'intellect': 25, 'skills': [], 'equipment': {}},
    {'name': 'Ivar', 'class': 'Archer', 'level': 62, 'intellect': 25, 'skills': [], 'equipment': {}},
    {'name': 'Sefa', 'class': 'Sorcerer', 'level': 62, 'intellect': 45, 'skills': [], 'equipment': {}}]}
ELDER_STAFF = 12505
QF1_FULL_HP = [380, 168, 237, 158]   # each member's maximum with the well's +20 Endurance (the run's `hp show`)


def heal():
    """Every member back to full without `hp full` (which restores the party and drops the well's +20)."""
    return [{'setup_shortcut': {'kind': 'set_member_points', 'member_index': k, 'health': hp}}
            for k, hp in enumerate(QF1_FULL_HP)]


def select(k):
    return {'press_action': {'action': 'select_member', 'member_index': k}}


def says(event, contains):
    """A click (by the selected member) whose window says `contains`, then closed."""
    # F13 / D-90 (A5 s29): a touch's line is a status line (A3's hooks), a note or a choice's answer a window
    return [{'play_lua': {'source': f'status(); click({EV[event]}); wait(0.5)'}},
            {'play_lua': {'source': f"local s = status(); local w = close(); if not w and not string.find(s, {contains!r}, "
                                    f"1, true) then error('{event} showed neither a window nor its line: ' .. s) end"}}]


def alive():
    return [{'assert': {'condition': {'name': 'dead', 'present': False, 'member_index': k}}} for k in range(4)] + \
           [{'assert': {'condition': {'name': 'unconscious', 'present': False, 'member_index': k}}} for k in range(4)]


def dragon_clouds():
    """The Dragon Clouds (D-57 Q36, D-59), not immortal: from FD-04's arrival round the court. The way down (sealed until
    FD-04 is installed: its line, the party stays). The well: +20 (Brokk's might 30 -> 50), a second drink that day
    nothing. The balls: Brokk (intellect 20 + 20) fails, Weak, alive; Sefa (45 + 20 = 65) hears each phrase. The
    crystals: Hild paid 3k/4k/5k with the surge, her second touch "nothing more" and no pay, Ivar still paid. The
    books: the runes line, then each syllable for a Linguist. The Eye: a wrong answer ("Die fools!", everyone alive),
    then INFINITY: the Elder Staff and the bit; a later click its else line. No monster; nobody dies; after a rest the
    well's +20 is gone."""
    fl = gen.DRAGON['floor']
    ax, ay = gen.FD04_ARRIVAL
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': QF1_PARTY}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'load_map': {'map': 'xeen_x9.blv', 'pos': f'{ax}, {ay}, {fl}'}},
         {'play_lua': {'source': 'wait(2); close()'}},
         {'assert': {'map': 'xeen_x9.blv'}},
         {'note': 'No monster on the Dragon Clouds (D-57 Q37): none within 3,000 of the arrival (the cloud is 4,096 x 3,584).'},
         {'assert': {'actor_count': {'near': [ax, ay, 3000], 'max': 0}}},
         {'console': {'line': 'hp full'}},
         {'console': {'line': 'hp show'}},
         {'console': {'line': 'player sheet', 'expect_contains': 'Brokk (Knight) level 62, might 30'}}]
    if not all(go.has_hook(n) for n in go.QF1.values()):
        raise SystemExit('Q-F1 hooks missing: ' + str([n for n in go.QF1.values() if not go.has_hook(n)]))
    wx, wy = gen.QF1_WELL
    s += [{'note': "The Well of Fantastic Skill (D-59 2): +20 to every statistic until rest, once a day."},
          walk(wx, wy - 400, fl, timeout=60), select(0)]
    s += says('evt:qf1_well', 'until you rest')
    s += [{'console': {'line': 'player sheet', 'expect_contains': 'Brokk (Knight) level 62, might 50'}}]
    s += says('evt:qf1_well_curb_s', 'cool and refreshing')
    s += [{'console': {'line': 'player sheet', 'expect_contains': 'Brokk (Knight) level 62, might 50'}}]
    dx, dy = gen.FD04_DOOR
    s += [walk(dx, dy - 200, fl + 16, radius=96, timeout=60)]
    if go.FD04:
        s += [{'play_lua': {'source': f'click({EV["evt:fd04_door"]}); wait(1)'}},
              # F16 (A5 s30): the entrance window with A3's trans row 5065; OK goes down
              {'assert': {'dialog': {'active': True, 'text_contains': 'The Dragon Tower'}}},
              {'select_topic': {'match_label': 'OK'}},
              {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
              {'assert': {'map': 'xeen_fd04.blv'}},
              {'note': "FD-04's entrance:x9_clouds (-1312, 608, 4224), facing south"},
              {'assert': {'party_position': {'x': -1312, 'y': 608, 'radius': 200, 'z_min': 4144, 'z_max': 4384}}},
              {'load_map': {'map': 'xeen_x9.blv', 'pos': f'{dx}, {dy - 200}, {fl}'}},
              {'play_lua': {'source': 'wait(2); close()'}}]
    else:
        s += [{'note': 'The way down is sealed until FD-04 is installed: its line, and the party stays.'}]
        s += says('evt:fd04_door', 'does not move')
        s += [{'assert': {'map': 'xeen_x9.blv'}}]
    ex, ey = gen.EYE_AT
    s += [{'note': "The Eye (D-57 Q36): a wrong answer is A3's q-f1.eye_wrong (\"Die fools!\", never lethal); then "
                   'INFINITY pays the Elder Staff.'},
          walk(ex, ey - 300, fl, timeout=60),
          {'play_lua': {'source': f'click({EV["evt:qf1_eye"]}); wait(0.5)'}},
          {'answer_input': {'text': 'Dragons'}},
          {'advance_runtime': {'seconds': 1}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Die fools'}}},
          {'play_lua': {'source': "close(); close()"}}] + alive() + [
          {'play_lua': {'source': f'click({EV["evt:qf1_eye"]}); wait(0.5)'}},
          {'answer_input': {'text': 'infinity'}},
          {'advance_runtime': {'seconds': 1}},
          # F13 / D-90 (A5 s30): the Eye's answer is a window or a status line (the staff into the packs)
          {'play_lua': {'source': "local s = status(); local w = close(); if not w and not string.find(s, "
                                  "'Very good, mortals', 1, true) then error('the Eye: neither a window nor its line: ' "
                                  ".. s) end"}},
          {'play_lua': {'source': f"close(); if held() ~= 0 then stow() end; close(); "
                                  f"if not has_item({ELDER_STAFF}) then error('no Elder Staff') end; "
                                  f"if not qbit({go.HOOKS['q-f1.eye']['sets']['done']}) then error('the Eye bit') end"}}]
    s += says('evt:qf1_eye', 'nothing more to say')
    s += heal()
    balls = dict(gen.QF1_BALLS)
    phrase = {'mind': 'knowledge is limitless', 'past': 'history is endless', 'future': 'possibilities are unlimited'}
    s += [{'note': "The crystal balls (D-59 1): intellect 60 or more (buffs count) hears the phrase; less: 70 Mind "
                   'damage and Weak, alive.'}]
    for k, tag in enumerate(('mind', 'past', 'future')):
        x, y = balls[tag]
        s += [walk(x + 300, y, fl, timeout=60), select(0),
              {'play_lua': {'source': f'click({EV["evt:qf1_ball_" + tag]}); wait(0.5); close(); wait(2)'}},
              {'assert': {'condition': {'name': 'weak', 'present': True, 'member_index': 0}}}] + alive()
        s += [select(3)] + says(f'evt:qf1_ball_{tag}', phrase[tag])
    s += heal()
    books = dict(gen.QF1_BOOKS)
    s += [{'note': 'The four Ancient Books: the runes line, then each syllable for a Linguist (A3: bit 116240).'},
          walk(books['in'][0], books['in'][1] - 250, fl, timeout=60)]
    s += says('evt:qf1_book_in', 'unable to understand')
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': LINGUIST}}]
    s += says('evt:qf1_book_in', 'inscription: IN')
    crys = {k: xy for k, xy, _ in gen.QF1_CRYSTALS}
    pay = {1: 3000, 2: 4000, 3: 5000}
    stand = {'fi': (0, -250), 'ni': (0, -250), 'ty': (0, -250)}
    order = [('book', 'fi'), ('crystal', 1), ('book', 'ni'), ('crystal', 2), ('crystal', 3), ('book', 'ty')]
    s += [{'console': {'line': 'hp show'}}]   # (not `hp full`: it restores the party and drops the well's +20)
    for kind, key in order:
        if kind == 'book':
            x, y = books[key]
            s += [walk(x + stand[key][0], y + stand[key][1], fl, timeout=60)]
            s += says(f'evt:qf1_book_{key}', f'inscription: {key.upper()}')
            continue
        x, y = crys[key]
        off = {1: (0, -250), 2: (0, -220), 3: (150, 250)}[key]
        ev_ = EV[f'evt:qf1_crystal_{key}']
        s += [{'note': f'Dragon Power Crystal {key} (D-59 3): {pay[key]:,} once per character, a 70 Energy surge.'},
              walk(x + off[0], y + off[1], fl, timeout=60)] + heal() + [select(1),
              {'play_lua': {'source': f"local e = experience(1); click({ev_}); wait(0.5); close(); wait(2); "
                                      f"if experience(1) ~= e + {pay[key]} then error('crystal {key}: not paid') end"}},
              {'assert': {'member_points': {'member_index': 1, 'health_max': QF1_FULL_HP[1] - 1}}},
              select(1),
              {'play_lua': {'source': f"local e = experience(1); status(); click({ev_}); wait(0.5); "
                                      f"if experience(1) ~= e then error('crystal {key}: paid twice') end"}},
              # F13 (A5 s30): the else line is a status line or a window
              {'play_lua': {'source': "local s = status(); local w = close(); if not w and not string.find(s, "
                                      f"'nothing more for you', 1, true) then error('crystal {key}: no else line: ' .. s) "
                                      "end"}},
              {'play_lua': {'source': 'close(); wait(2)'}},
              select(2),
              {'play_lua': {'source': f"local e = experience(2); click({ev_}); wait(0.5); close(); "
                                      f"if experience(2) ~= e + {pay[key]} then error('crystal {key}: Ivar not paid') end"}}]
        s += alive()
    s += [{'note': "After a rest the well's +20 is gone (D-59 2)."},
          walk(ax, ay, fl, timeout=60),
          {'console': {'line': 'rest heal 480'}},
          {'advance_runtime': {'seconds': 2}},
          {'play_lua': {'source': 'close(); close()'}},
          {'console': {'line': 'hp show'}},
          {'console': {'line': 'player sheet', 'expect_contains': 'Brokk (Knight) level 62, might 30'}},
          {'assert': {'map': 'xeen_x9.blv'}}] + alive()
    return {'id': 'xeen.x9.l4.dragon_clouds', 'title': "Clouds of Xeen (X9): the Dragon Clouds from FD-04's arrival: "
            'the way down, the Eye, the books, balls, well and crystals; no monsters, nobody dies (D-57, D-59)',
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


GEMS = [177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 988, 989, 990, 991, 992, 993, 994, 995, 996, 997, 998,
        2056, 2057, 2058, 2059, 2060, 2061, 2062, 2063, 2064, 2065]
ACCURACY_BOOST = 245
ACCURACY_DOLL = 12370


def set_accuracy(member, value):
    """The member's Accuracy as the sheet shows it (ActualAccuracy) set to `value` through its base statistic."""
    return {'console': {'line': (f'lua evt.ForPlayer({member}) local v = 0 while v < 255 and IsAtLeast(ActualAccuracy, '
                                 f'v + 1) do v = v + 1 end if v > {value} then SubtractValue(BaseAccuracy, v - {value}) '
                                 f'elseif v < {value} then AddValue(BaseAccuracy, {value} - v) end '
                                 'evt.ForPlayer(Players.Current)'), 'expect_contains': 'Lua ran.'}}


def read_accuracy(member, want):
    return [{'console': {'line': (f"lua evt.ForPlayer({member}) local v = 0 while v < 255 and IsAtLeast(ActualAccuracy, "
                                  "v + 1) do v = v + 1 end evt.ForPlayer(Players.Current) evt.StatusText('acc ' .. v)"),
                         'expect_contains': 'Lua ran.'}},
            {'play_lua': {'source': (f"local v = tonumber(string.match(status(), 'acc (%d+)')); log('member {member} "
                                     f"Accuracy ' .. v); if v ~= {want} then error('Accuracy ' .. v .. ', wanted "
                                     f"{want}') end")}}]


def tonic():
    """D-70 Q1: Slick's Sure-Eye Tonic. Member 0 at bare creation Accuracy (30) loses the Accuracy game; the crate's
    first click gives two Accuracy Boosts (245), a second only its else line; one boost drunk (+30, 60) wins the doll;
    one bottle is left."""
    x, y = gen.at('poi:accuracy_game')
    fl = gen.space_floor('poi:accuracy_game')
    tx, ty = go.TONIC_AT
    gems = 'local function gems() local n = 0; for _, id in ipairs({' + ', '.join(map(str, GEMS)) + \
           '}) do n = n + item_count(id) end; return n end; '
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': party()}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'load_map': {'map': 'xeen_x9.blv', 'pos': f'{x}, {y}, {fl}'}},
         {'play_lua': {'source': "wait(2); close(); log('cleared ' .. clear_hostiles(8000))"}},
         {'assert': {'map': 'xeen_x9.blv'}},
         select(0), set_accuracy(0, 30)]
    s += read_accuracy(0, 30)
    s += [{'lua_event': {'source': 'evt.ForPlayer(1) for _ = 1, 20 do AddValue(InventoryItem(183), 183) end '
                                   'evt.ForPlayer(Players.Current)'}},
          {'play_lua': {'source': 'for _ = 1, 25 do wait(0.1); if held() ~= 0 then stow() end end; ' + gems +
                                  "log('gems ' .. gems()); if gems() < 20 then error('only ' .. gems() .. ' gems') end"}},
          {'note': 'At 30 the Accuracy game is lost (10 gems).'},
          {'play_lua': {'source': f'click({EV["evt:booth_accuracy"]}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Oh! Too bad.'}}},
          {'play_lua': {'source': "close(); if qbit(111684) then error('won at 30') end"}},
          {'note': "The tonic crate: two Accuracy Boosts on the first click, then Slick's else line only."},
          walk(tx - 192, ty, fl, radius=160),
          {'play_lua': {'source': f"if item_count({ACCURACY_BOOST}) ~= 0 then error('a boost before the crate') end; "
                                  f'click({EV["evt:tonic_crate"]}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'Sure-Eye Tonic, two bottles'}}},
          {'play_lua': {'source': (f"close(); for _ = 1, 5 do wait(0.1); if held() ~= 0 then stow() end end; "
                                   f"local n = item_count({ACCURACY_BOOST}); log('Accuracy Boosts ' .. n); "
                                   "if n ~= 2 then error('the crate gave ' .. n .. ' Accuracy Boosts, wanted 2') end")}},
          {'play_lua': {'source': f'click({EV["evt:tonic_crate"]}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'The free round was the first one.'}}},
          {'play_lua': {'source': (f"close(); for _ = 1, 3 do wait(0.1); if held() ~= 0 then stow() end end; "
                                   f"local n = item_count({ACCURACY_BOOST}); if n ~= 2 then error('the second click "
                                   "left ' .. n .. ' Accuracy Boosts') end")}},
          {'note': 'Member 0 drinks one boost at the shooting line: 60, and wins the doll.'},
          walk(x, y, fl, radius=160),
          {'use_item': {'item_id': ACCURACY_BOOST, 'member_index': 0}}]
    s += read_accuracy(0, 60)
    s += [select(0),
          {'play_lua': {'source': f'click({EV["evt:booth_accuracy"]}); wait(0.5)'}},
          {'assert': {'dialog': {'active': True, 'text_contains': 'You win a prize.'}}},
          {'play_lua': {'source': (f"close(); for _ = 1, 3 do wait(0.1); if held() ~= 0 then stow() end end; "
                                   f"if not qbit(111684) then error('the Accuracy game is not won') end; "
                                   f"if not has_item({ACCURACY_DOLL}) then error('no Accuracy doll') end; "
                                   f"if item_count({ACCURACY_BOOST}) ~= 1 then error('not one bottle left') end")}}]
    return {'id': 'xeen.x9.l4.tonic', 'title': "Clouds of Xeen (X9): Slick's Sure-Eye Tonic (D-70 Q1): two Accuracy "
            'Boosts once, the else line after; one drunk, a member at 30 Accuracy wins the Accuracy game',
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


def hostility():
    kinds = [go.ROC, go.GRIFFIN, go.GOLEM]
    s = [{'new_game_flow': {'start_map': 'xeen_x9.blv', 'party': party()}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'advance_runtime': {'seconds': 2}}]
    for k in kinds:
        s.append({'assert': {'actor_count': {'monster_id': k, 'hostile': False, 'max': 0}}})
        s.append({'assert': {'actor_count': {'monster_id': k, 'hostile': True, 'min': 1}}})
    s += [{'assert': {'actor_count': {'monster_id': go.SLICK, 'hostile': False, 'min': 1}}},
          {'assert': {'actor_count': {'monster_id': go.SLICK, 'hostile': True, 'max': 0}}}]
    s.append({'note': "The map's kinds side by side by the prize stand (Slick among them), nearer each other than the "
                      'party: they must not take each other on.'})
    s.append({'console': {'line': 'arena trace on'}})
    sx, sy = gen.at('poi:prize_stand')
    for i, k in enumerate((go.ROC, go.GRIFFIN, go.GOLEM, go.ROC)):
        s.append({'spawn_actor': {'monster_id': k, 'x': sx + 384 + 160 * i, 'y': sy + 384, 'z': 704}})
    s += [{'advance_runtime': {'seconds': 12}},
          {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}}]
    for k in kinds + [go.SLICK]:
        s.append({'assert': {'actor_count': {'monster_id': k, 'hurt': True, 'max': 0}}})
    return {'id': 'xeen.x9.l4.hostility', 'title': 'Clouds of Xeen (X9): foes hostile to the party, none fighting '
            'another, Slick peaceful', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def write(name, data, header):
    with open(L4 / name, 'w') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    write('playtest.yml', main_walk(),
          "# Playtest of the Clouds of Xeen (X9, L4; written by output/studio_cal/x9/tools/gen_playtests.py). From\n"
          "# XD-12's stair head over every cloud, bridge and the unseen way: signs, statues (A3's Linguist gate),\n"
          "# nests, offerings, Slick's booths and prize stand, the gate (m34.gate), the four chests.\n"
          "# Run with --world xeen --map xeen_x9.blv.\n")
    bx, by = gen.SPACE['room:brink']['at']
    write('playtest_fall_south.yml', fall('fall_south', "Clouds of Xeen (X9): a fall off the brink lands on X2's "
                                          'entrance:x9_fall, nobody dies, nobody hurt after (D-6.4, D-50, D-54)', (bx + 1300, by + 560, 448), 90, 1.0),
          "# A fall off the stair clouds: north off the brink, east of the unseen way; caught under -1,000 and set down\n"
          "# on X2's Darzog island by the tower door (entrance:x9_fall), with falling damage, nobody dead.\n")
    px, py = gen.SPACE['room:east_pillar']['at']
    write('playtest_fall_chain.yml', fall('fall_chain', "Clouds of Xeen (X9): a fall off the lone pillar (the east "
                                          "chain) lands on X2's entrance:x9_fall, nobody dies, nobody hurt after (D-54)", (px + 700, py, 384), 0),
          "# A fall off a chain cloud: east off the lone pillar; set down on X2 at entrance:x9_fall, nobody dead.\n")
    lx, ly = gen.SPACE['room:landing']['at']
    write('playtest_fall_xeendom.yml', fall('fall_xeendom', "Clouds of Xeen (X9): a fall off Xeendom's landing lands on "
                                            "X2's entrance:x9_fall, nobody dies, nobody hurt after (D-54)", (lx + 1100, ly, 256), 0),
          "# A fall off Xeendom: east off the landing; set down on X2 at entrance:x9_fall, nobody dead.\n")
    write('playtest_castle_gone.yml', castle_gone(),
          "# The castle-gone stage (state:castle_gone, D-47 Q14): m35.done set, the map reloaded at the gate; the gate's\n"
          "# spot gives A3's x9.castle_gone line and the party walks where the shell stood.\n")
    write('playtest_dragon_clouds.yml', dragon_clouds(),
          "# The Dragon Clouds (Q-F1, D-57 Q36, D-59): from FD-04's arrival round the court; the way down (sealed until\n"
          "# FD-04 is installed), the well, the Eye, the balls, the books and the crystals with A3's hooks; no monsters\n"
          "# (Q37); the party is not immortal and nobody dies.\n")
    write('playtest_tonic.yml', tonic(),
          "# Slick's Sure-Eye Tonic (D-70 Q1, A3's m34.tonic) by the Accuracy booth: a member at 30 Accuracy loses; the\n"
          "# crate gives two Accuracy Boosts (245) once, then the else line; one drunk (60), the game is won.\n")
    write('playtest_hostility.yml', hostility(),
          "# Hostility check of the Clouds of Xeen (X9): every kind hostile to the party, none fighting another, Slick\n"
          "# peaceful (the world's relations.yml).\n")
    print('written playtests')
