#!/usr/bin/env python3
"""X8: writes L4 playtest.yml, playtest_fall.yml, playtest_fall_east.yml and playtest_hostility.yml (A6 sub-agent)."""
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen  # noqa: E402
import gen_objects as go  # noqa: E402

L4 = gen.BRIEF / 'L4'
EV = {}  # event ids by name, read from the lock the build writes
LOCK = yaml.safe_load(open(L4 / 'ids.lock.yml'))
for k, v in LOCK.get('events', {}).items():
    EV[k] = v
CH = LOCK.get('chests', {})


def party(level=18):
    return {'gold': 0, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': level, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': level, 'skills': [], 'equipment': {}}]}


def link(lid):
    for l in gen.LINKS:
        if l[0] == lid:
            return l
    raise KeyError(lid)


def heads(lid, reverse=False):
    """The two bridge heads of a link, 320 inside each island, in walking order, with their floor heights."""
    _, frm, to, kind, width, notes = link(lid)
    ca, cb = gen.ISLANDS[frm][0], gen.ISLANDS[to][0]
    ra = gen.rim_point(gen.OUTLINES[frm], ca, cb)
    rb = gen.rim_point(gen.OUTLINES[to], cb, ca)
    d = math.hypot(rb[0] - ra[0], rb[1] - ra[1])
    ux, uy = (rb[0] - ra[0]) / d, (rb[1] - ra[1]) / d
    a = (int(ra[0] - ux * 320), int(ra[1] - uy * 320), gen.ISLANDS[frm][2])
    m = (int((ra[0] + rb[0]) / 2), int((ra[1] + rb[1]) / 2), int((gen.ISLANDS[frm][2] + gen.ISLANDS[to][2]) / 2))
    b = (int(rb[0] + ux * 320), int(rb[1] + uy * 320), gen.ISLANDS[to][2])
    pts = [a, m, b]
    return pts[::-1] if reverse else pts


def walk(x, y, z=None, radius=96, timeout=60):
    step = {'x': x, 'y': y, 'radius': radius, 'timeout_seconds': timeout, 'clear_hostiles': 2500,
            'close_dialogs': True}
    if z is not None:
        step['z'] = z
        step['z_tolerance'] = 200
    return {'walk_to': step}


def cross(lid, reverse=False):
    out = []
    for x, y, z in heads(lid, reverse):
        out.append(walk(x, y, z))
    return out


def at(iid, dx=0, dy=0):
    (cx, cy), _, floor, _ = gen.ISLANDS[iid]
    return walk(cx + dx, cy + dy, floor)


def click_dialog(event, contains):
    return [{'play_lua': {'source': f'click({EV[event]}); wait(0.5)'}},
            {'assert': {'dialog': {'active': True, 'text_contains': contains}}},
            {'play_lua': {'source': f"if not close() then error('{event} showed no window') end"}}]


def nest(k):
    return [{'play_lua': {'source': f'click({EV[f"evt:nest_{k}"]}); wait(0.5)'}},
            {'answer_input': {'text': 'Yes'}},
            {'advance_runtime': {'seconds': 1}},
            {'play_lua': {'source': f"close(); if not qbit({115020 + k}) then error('nest {k}: its bit is not set') end"}}]


def loot(chest):
    return {'play_lua': {'source': f'loot_chest({EV["evt:chest_" + chest]}); wait(1); if held() ~= 0 then stow() end; close()'}}


def main_walk():
    s = [{'new_game_flow': {'start_map': 'xeen_x8.blv', 'party': party()}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'assert': {'map': 'xeen_x8.blv'}},
         {'assert': {'party_position': {'x': go.WITCH_ARRIVAL[0], 'y': go.WITCH_ARRIVAL[1], 'radius': 160,
                                        'z_min': -16, 'z_max': 40}}},
         {'note': 'The Witch Clouds: the landing, the causeway, the offering terrace.'},
         at('witch_landing', 0, 400)]
    s += cross('witch_causeway')
    s += [at('offering_terrace', 0, 0)]
    # an offering statue refuses a party that is not Crusaders, then gives to Crusaders
    s += click_dialog('evt:offering_1', 'kept for Crusaders')
    s += [{'setup_shortcut': {'kind': 'set_qbit', 'id': 110047}},
          {'play_lua': {'source': f'click({EV["evt:offering_2"]}); wait(0.5); if held() ~= 0 then stow() end; close()'}},
          {'note': 'The spires: two nests to burn.'}]
    s += cross('spires_ramp')
    s += [at('nest_spires', 0, 0)]
    s += nest(1) + nest(2)
    s += cross('eyrie_ramp')
    s += [at('queens_eyrie', 0, -600), {'clear_hostiles': {'radius': 3000}}, at('queens_eyrie', 256, -160),
          loot('hoard')]
    s += cross('explorer_bridge')
    s += [at('explorers_rock', 0, -300)]
    s += click_dialog('evt:explorer', 'Super Explorer')
    s += [{'play_lua': {'source': "if not qbit(115020) then error('the explorer\\'s bit is not set') end"}}]
    s += cross('explorer_bridge', True) + [at('queens_eyrie', 0, -600)]
    s += cross('eyrie_ramp', True) + [at('nest_spires', 0, 0)]
    s += cross('spires_ramp', True) + [at('offering_terrace', 0, 0)]
    s += [{'note': 'The long bridge: the half-way cloud, then the High Magic Clouds.'}]
    s += cross('long_bridge_east') + [at('half_way', 0, 0)] + cross('long_bridge_west')
    s += [at('observatory_isle', 1000, -640)]
    s += [{'note': "The rhymes show only past the Linguist gate (A3's xd07.runes reads qbit 116240)"},
          {'setup_shortcut': {'kind': 'set_qbit', 'id': 116240}}]
    s += click_dialog('evt:rhyme_3', "Illusion holds Magic's key")
    ox, oy = gen.ISLANDS['observatory_isle'][0]
    s += [walk(ox - 512, oy + 1152 - 1000, 256)]
    s += click_dialog('evt:telescope', 'brass telescope')
    s += [loot('star_charts')]
    s += [{'note': 'The long ramp up to the golem heights: a dead end.'}]
    s += cross('heights_ramp') + [at('golem_heights', 0, -800), {'clear_hostiles': {'radius': 4000}},
                                  at('golem_heights', 128, 1000), loot('golem_cache')]
    s += cross('heights_ramp', True) + [at('observatory_isle', 0, 0)]
    s += [{'note': 'Round the High Magic loop: the garden, the stair landing, the lantern cloud.'}]
    s += cross('garden_obs_bridge', True) + [at('rhyme_garden', 0, -500)]
    s += click_dialog('evt:rhyme_2', 'Taxman then must have his bit')
    s += cross('garden_bridge', True) + [at('stair_landing', 0, 0)]
    s += cross('lantern_bridge') + [at('lantern_cloud', 0, 0), at('lantern_cloud', 256, -500), loot('lantern')]
    s += cross('lantern_bridge', True) + [at('stair_landing', 0, 0)]
    s += cross('high_causeway') + [at('observatory_isle', 0, 0)]
    s += cross('windward_bridge') + [at('windward_rock', 0, 0)] + cross('windward_bridge', True)
    s += [{'note': 'Back over the long bridge to the witch\'s perch.'}]
    s += cross('long_bridge_west', True) + [at('half_way', 0, 0)] + cross('long_bridge_east', True)
    s += [at('offering_terrace', 0, 0)] + cross('witch_causeway', True) + [at('witch_landing', 0, 0)]
    s += cross('perch_bridge') + [at('witch_perch', 0, 0)]
    s += nest(3)
    s += click_dialog('evt:rhyme_1', 'credits for King to hold')
    s += [{'play_lua': {'source': "for k = 115020, 115023 do if not qbit(k) then error('bit ' .. k .. ' not set') end end"}},
          {'assert': {'map': 'xeen_x8.blv'}}]
    return {'id': 'xeen.x8.l4', 'title': 'Cloudreach (X8 L4): every island, bridge and causeway walked; nests, '
            'statues, telescope and chests used', 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def fall(name, title, start, yaw, target_map, landing, damage, settle=0):
    s = [{'new_game_flow': {'start_map': 'xeen_x8.blv', 'party': party()}}]
    s += [{'play_lua': {'source': 'wait(3); close()'}},
          {'clear_hostiles': {'radius': 40000}},
          {'movement_segment': {'input': 'forward', 'seconds': 2.5, 'actor_collision': True, 'actor_ai': True,
                                'start': {'map': 'xeen_x8.blv', 'x': start[0], 'y': start[1], 'z': start[2],
                                          'yaw_degrees': yaw, 'pitch': 0},
                                'expect_stop': {'map': 'xeen_x8.blv', 'x': start[0], 'y': start[1], 'z': start[2],
                                                'yaw_degrees': yaw, 'pitch': 0},
                                'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}},
          {'advance_runtime': {'seconds': 4.0, 'follow_map_move': True}},
          {'advance_runtime': {'seconds': 4.0}},
          {'assert': {'map': target_map}},
          {'assert': {'party_position': {'x': landing[0], 'y': landing[1], 'radius': 700}}},
          {'assert': {'party_health': {'full': not damage}}}]
    if damage:
        s += [{'assert': {'member_points': {'member_index': 0, 'health_min': 1}}}]
    if settle:
        # D-54: the lake dragons' leash circles keep their fire off the landing; nobody is hurt while the party waits.
        s += [{'advance_runtime': {'seconds': float(settle)}},
              {'assert': {'party_health': {'full': True}}}]
    return {'id': f'xeen.x8.l4.{name}', 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': s}


def hostility():
    kinds = [go.HARPY, go.HAG, go.QUEEN, go.FEET, go.GUARD, go.GOLEM]
    s = [{'new_game_flow': {'start_map': 'xeen_x8.blv', 'party': party()}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}},
         {'advance_runtime': {'seconds': 2}}]
    for k in kinds:
        s.append({'assert': {'actor_count': {'monster_id': k, 'hostile': False, 'max': 0}}})
    for k in kinds:
        s.append({'assert': {'actor_count': {'monster_id': k, 'hostile': True, 'min': 1}}})
    s.append({'note': 'Kinds of the map side by side on the half-way cloud, nearer each other than the party: they '
                      'must not take each other on.'})
    s.append({'console': {'line': 'arena trace on'}})
    for i, k in enumerate((go.HARPY, go.FEET, go.HAG, go.GUARD)):
        s.append({'spawn_actor': {'monster_id': k, 'x': -300 + 128 * i, 'y': 256, 'z': -64}})
    s += [{'advance_runtime': {'seconds': 12}},
          {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}}]
    for k in (go.HARPY, go.FEET, go.HAG, go.GUARD):
        s.append({'assert': {'actor_count': {'monster_id': k, 'hurt': True, 'max': 0}}})
    return {'id': 'xeen.x8.l4.hostility', 'title': 'Cloudreach (X8): foes hostile to the party, no fights among them',
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


def write(name, data, header):
    with open(L4 / name, 'w') as f:
        f.write(header)
        yaml.safe_dump(data, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    write('playtest.yml', main_walk(),
          '# Playtest of Cloudreach (X8, L4; written by output/studio_cal/x8/tools/gen_playtests.py). From the Witch\n'
          '# Clouds\' stair head over every island, bridge and causeway: nests burnt (A3\'s hooks), the explorer\'s\n'
          '# statue, the rhymes, the telescope, the offering statues, the four chests. Run with --world xeen --map\n'
          '# xeen_x8.blv.\n')
    write('playtest_fall.yml', fall('fall', 'Cloudreach (X8): a fall off the half-way cloud lands in Lake Darzog on X2 '
                                    'without damage (D-6.4)', (0, 256, -64), 90, 'xeen_x2.odm',
                                    (go.X2_LANDING[0], go.X2_LANDING[1], go.X2_LANDING[2]), False, settle=20),
          '# The middle zone\'s fall (D-6.4): off the half-way cloud\'s north edge; caught under -1,000 and set\n'
          '# down at A5\'s point in Lake Darzog (X2), at the surface, no damage; still unhurt 20 s later (D-54).\n')
    lx, ly = gen.ISLANDS['witch_landing'][0]
    write('playtest_fall_east.yml', fall('fall_east', 'Cloudreach (X8): a fall off the Witch Clouds lands on X1 by '
                                         'the Witch Tower and costs hit points (D-6.2, D-6.4)', (lx + 1200, ly, 0), 0,
                                         'xeen_x1.odm', (go.X1_LANDING[0], go.X1_LANDING[1], go.X1_LANDING[2]),
                                         True),
          '# The east zone\'s fall: off the Witch landing\'s east edge, no immortality; A3\'s Xeen.skyFall sets the\n'
          '# party 850 over X1\'s ground by the Witch Tower and the engine\'s fall damage takes about a third of each\n'
          '# member\'s hit points (D-6.2), none dies.\n')
    if go.X3_LIVE:
        sx, sy = gen.ISLANDS['stair_landing'][0]
        write('playtest_fall_west.yml', fall('fall_west', 'Cloudreach (X8): a fall off the Magic stair landing lands '
                                             "in X3's lagoon by the Tower of High Magic (D-6.4)", (sx - 1200, sy, 0),
                                             180, 'xeen_x3.odm', (go.X3_LANDING[0], go.X3_LANDING[1],
                                                                  go.X3_LANDING[2]), False),
              "# The west zone's fall (D-6.4, X3 installed): off the Magic stair landing's west edge; set down in\n"
              "# X3's lagoon east of the Tower of High Magic's islet, at the surface, no damage.\n")
    write('playtest_hostility.yml', hostility(),
          '# Hostility check of Cloudreach (X8): every kind hostile to the party, none fighting another (the\n'
          '# world\'s relations.yml).\n')
    print('written playtests')
