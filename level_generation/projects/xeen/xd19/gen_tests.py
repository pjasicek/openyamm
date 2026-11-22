#!/usr/bin/env python3
"""XD-19 Castle Xeen: writes the playtests of devdocs/xeen/briefs/xd19/L4 from gen.py's geometry and the built
ids.lock.yml (run after a build: level_generation/projects/xeen/xd19/cycle.sh, then this).

    playtest.yml            the critical path: the arrival, the sealed gate, the four generators (the barrier with
                            three down still stands, then falls), the crown stair, the aviary (Xeen's Pet), the throne
                            doors' plate, Lord Xeen (no damage without the sword), his death, the hoard, the scepter
                            (No, then Yes: the cinematic; the party stays), a save and load
    playtest_pool.yml       the guard foundry: the clock shows one hidden guard, both machines broken show the rest
                            and open the bays (the gem find)
    playtest_hostility.yml  every row hostile at load and after a reload; side by side they do not fight each other
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import importlib.util
import math
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gen', HERE / 'gen.py')
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

L4 = G.BRIEFS / 'L4'
# The installed scene's actors (their indices; gen.py no longer names a build scene).
SCENE = G.ROOT / 'assets_dev/worlds/xeen/maps/xeen_xd19.scene.yml'
_ACTS = yaml.safe_load(SCENE.read_text())['initial_state']['actors']
POOL_IDX = [a['actor_index'] for g in (41, 42, 43, 44) for a in _ACTS if a.get('group') == g]
LORD_IDX = [a['actor_index'] for a in _ACTS if a.get('group') == 60][0]   # Lord Xeen (group 60)
LOCK = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
# Xeen's Guards on the map (placed and the foundry's pool; D-98 raised it from 14).
N_GUARDS = sum(1 for _, _, ms, _ in G.PLACED for m in ms if m[0] == G.GUARD) + len(G.POOL)
EV = LOCK['events']
DOOR = LOCK['doors']
DES = LOCK['destructibles']
Q = G.QBITS
STEM = 'xeen_xd19.blv'
# Lord Xeen's HP from his row (A2's monster_data.txt; 2,200 since A2's ninth session).
LORD_HP = next(int(r.split('\t')[4]) for r in (Path(_REPO_ROOT + '/assets_dev/worlds/xeen/data_tables/'
                                                     'monster_data.txt').read_text().splitlines())
               if r.startswith('11634\t'))


def ev(name):
    return EV[f'evt:{name}']


def door(name):
    return DOOR[f'door:{name}']


def header(tid, title, comment):
    return {'id': tid, 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': [
        {'new_game_flow': {'start_map': STEM, 'party': {'gold': 0, 'food': 20, 'members': [
            {'name': 'Brokk', 'class': 'Knight', 'level': 50, 'skills': [], 'equipment': {}},
            {'name': 'Hild', 'class': 'Cleric', 'level': 50, 'skills': [], 'equipment': {}},
            {'name': 'Ivar', 'class': 'Archer', 'level': 50, 'skills': [], 'equipment': {}},
            {'name': 'Sefa', 'class': 'Sorcerer', 'level': 50, 'skills': [], 'equipment': {}}]}}},
        {'assert': {'map': STEM}},
        {'setup_shortcut': {'kind': 'immortal', 'value': True}}]}, comment


def floor_at(rid):
    return G.ROOMS[rid]['floor']


def inside(oid, rid, depth=220):
    """A point `depth` inside room `rid` from opening `oid`'s middle, at the room's floor (the gallery's top when the
    opening is a stair hall's head)."""
    pt, width, a, b, z = G.OPEN_AT[oid]
    x0, y0, x1, y1 = G.ROOMS[rid]['rect']
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    px, py = pt
    # the opening's wall: the room side nearest the point
    if abs(px - x0) < 200 or abs(px - x1) < 200:
        nx = 1 if abs(px - x0) < abs(px - x1) else -1
        if not (abs(px - x0) < 200 and abs(px - x1) < 200):
            p = (x0 + depth if nx > 0 else x1 - depth, py)
        else:
            p = (cx, py)
    else:
        p = (px, y0 + depth if abs(py - y0) < abs(py - y1) else y1 - depth)
    if abs(py - y0) < 200 or abs(py - y1) < 200:
        if not (abs(px - x0) < 200 or abs(px - x1) < 200):
            p = (px, y0 + depth if abs(py - y0) < abs(py - y1) else y1 - depth)
    zz = floor_at(rid)
    st = G.STAIR.get(rid)
    if st:
        gx0, gy0, gx1, gy1 = st['gallery']
        if gx0 <= p[0] <= gx1 and gy0 <= p[1] <= gy1 and z > zz:
            zz = st['top']
    return int(p[0]), int(p[1]), int(zz)


def W(x, y, z, radius=64, tol=None, timeout=40, clear=1600):
    d = {'x': int(x), 'y': int(y), 'z': int(z), 'radius': radius}
    if tol:
        d['z_tolerance'] = tol
    d.update({'clear_hostiles': clear, 'timeout_seconds': timeout, 'close_dialogs': True})
    return {'walk_to': d}


def thru(oid, a, b):
    """Walk from room a through opening oid into room b."""
    return [W(*inside(oid, a)), W(*inside(oid, b))]


def climb(rid):
    """From the foot of a stair hall's flight to its gallery."""
    st = G.STAIR[rid]
    (fx, fy), (tx, ty) = st['f_from'], st['f_to']
    sgn = 1 if ty > fy else -1
    f = G.ROOMS[rid]['floor']
    return [W(fx, fy - sgn * 160, f, tol=40), W(tx, ty + sgn * 200, st['top'], tol=48, timeout=60)]


def lane(rid, side_x, y_from, y_to):
    """Walk along a stair hall beside its flight (under its gallery) from one end to the other."""
    f = G.ROOMS[rid]['floor']
    return [W(side_x, y_from, f), W(side_x, y_to, f)]


def lua(src):
    return {'play_lua': {'source': src}}


def need_status(text, label):
    return lua(f"wait(1.2); local s = tostring(status()); if not string.find(s, {text!r}, 1, true) then "
               f"error('{label}: ' .. s) end")


def door_open(evt_name, door_name):
    return lua(f"open_door({ev(evt_name)}, {door(door_name)})")


def qbit_is(q, on=True, label=''):
    return lua(f"if {'not ' if on else ''}qbit({q}) then error('{label or q} {'not set' if on else 'set'}') end")


def gen_question(g):
    return [lua(f"click({ev('gen_' + g)}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
            {'advance_runtime': {'seconds': 1.5}}, {'play_lua': {'source': 'close()'}},
            qbit_is(Q['gen_' + g], label=f'gen_{g}'),
            {'console': {'line': f"destructible {DES[f'destructible:gen_{g}']} state", 'expect_contains': 'broken'}}]


def near_core(g, rid):
    cx, cy = G.GENS[g]['core']
    return W(cx, cy + 300 * G.GENS[g]['front'], floor_at(rid), radius=48)


def playtest():
    t, comment = header('xeen.xd19.l4.walk', 'Castle Xeen (XD-19 L4): the generators, the barrier, the crown, Lord '
                        'Xeen and the scepter', None)
    s = t['steps']
    s += [{'assert': {'party_position': {'x': G.START[0], 'y': G.START[1], 'radius': 64, 'z_min': -8, 'z_max': 8}}},
          {'note': "The arrival line (a one-shot timer; the headless runner opens no window from a timer: the step "
                   "asserts that the event ran and the hook set m35.started)."},
          lua("wait(3)"), {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['once.arrive'], 'value': 1}}},
          lua('close()'),
          qbit_is(Q['started'], label='m35.started'),
          {'assert': {'map': STEM}}]
    # F0: the great hall, the west aisle and ward, the west gallery, the cold vault: the Water Generator.
    s += [W(*inside('gate_nave', 'gate')), W(*inside('gate_nave', 'nave')), {'clear_hostiles': {'radius': 2400}}]
    s += thru('arcade0_w2', 'nave', 'aisle_w') + thru('aisle_w_ward_w', 'aisle_w', 'ward_w')
    s += thru('ward_w_gallery_w', 'ward_w', 'gallery_w') + [W(*inside('gallery_w_vault', 'gallery_w'))]
    s += [door_open('door_vault_w', 'vault_w'), W(*inside('gallery_w_vault', 'vault_w')),
          {'clear_hostiles': {'radius': 2400}}, near_core('water', 'vault_w')]
    s += gen_question('water')
    s += [lua(f"click({ev('gen_water')}); wait(0.8); close()")]   # the dead generator's else line
    # Through the stair hall to the gravel vault: the Earth Generator.
    s += [W(*inside('vault_w_stair', 'vault_w')), door_open('door_vault_w_stair', 'vault_w_stair'),
          W(*inside('vault_w_stair', 'stair_hall')), {'clear_hostiles': {'radius': 2400}},
          W(*inside('vault_e_stair', 'stair_hall')), door_open('door_vault_e_stair', 'vault_e_stair'),
          W(*inside('vault_e_stair', 'vault_e')), {'clear_hostiles': {'radius': 2400}}, near_core('earth', 'vault_e')]
    s += gen_question('earth')
    # The east gallery and the south-east tower up to its top: the Air Generator.
    s += [W(*inside('gallery_e_vault', 'vault_e')), door_open('door_vault_e', 'vault_e'),
          W(*inside('gallery_e_vault', 'gallery_e')), {'clear_hostiles': {'radius': 2400}},
          W(*inside('gallery_e_tower0', 'gallery_e')), W(*inside('gallery_e_tower0', 'tower0_e'))]
    x0, y0, x1, y1 = G.ROOMS['tower0_e']['rect']
    s += lane('tower0_e', x1 - 120, y1 - 400, y0 + 200) + climb('tower0_e')
    s += [W(*inside('tower0_e_top', 'tower0_e')), W(*inside('tower0_e_top', 'tower1_e'))]
    x0, y0, x1, y1 = G.ROOMS['tower1_e']['rect']
    s += [W((x0 + x1) // 2, y1 - 200, G.ROOMS['tower1_e']['floor'])] + climb('tower1_e')
    s += [W(*inside('tower1_e_top', 'tower1_e')), W(*inside('tower1_e_top', 'gen_air')),
          {'clear_hostiles': {'radius': 2400}}, near_core('air', 'gen_air')]
    s += gen_question('air')
    # The upper east gallery to the barrier hall: three pylons dark, the field still stands.
    s += [W(*inside('upper_e_gen_air', 'gen_air')), door_open('door_gen_air', 'gen_air'),
          W(*inside('upper_e_gen_air', 'upper_e')), {'clear_hostiles': {'radius': 2400}}]
    s += thru('upper_e_barrier', 'upper_e', 'barrier_e') + thru('arcade2_e2', 'barrier_e', 'barrier')
    s += [{'clear_hostiles': {'radius': 2400}},
          W(0, G.ROOMS['barrier']['rect'][1] + 200, G.ROOMS['barrier']['floor'], radius=48),
          lua(f"wait(2); if door_state({door('field')}) ~= 'closed' then error('field with three generators down: ' "
              f".. door_state({door('field')})) end; if qbit({Q['barrier_down']}) then error('barrier_down early') end"),
          lua(f"click({ev('field')}); wait(0.8)"),
          {'assert': {'dialog': {'active': True, 'text_contains': 'Four pylons feed it'}}}, lua('close()')]
    # The upper west gallery to the south-west tower top: the Fire Generator; the barrier falls.
    s += thru('arcade2_w2', 'barrier', 'barrier_w') + thru('upper_w_barrier', 'barrier_w', 'upper_w')
    s += [{'clear_hostiles': {'radius': 2400}}, W(*inside('upper_w_gen_fire', 'upper_w')),
          door_open('door_gen_fire', 'gen_fire'), W(*inside('upper_w_gen_fire', 'gen_fire')),
          {'clear_hostiles': {'radius': 2400}}, near_core('fire', 'gen_fire')]
    s += gen_question('fire')
    s += [{'advance_runtime': {'seconds': 2}}, lua('close()'),
          qbit_is(Q['barrier_down'], label='barrier_down'),
          lua(f"wait(2); if door_state({door('field')}) ~= 'open' then error('field after four generators: ' .. "
              f"door_state({door('field')})) end")]
    # Back through the barrier hall, up the crown stair.
    s += [W(*inside('upper_w_gen_fire', 'gen_fire')), W(*inside('upper_w_gen_fire', 'upper_w'))]
    s += thru('upper_w_barrier', 'upper_w', 'barrier_w') + thru('arcade2_w2', 'barrier_w', 'barrier')
    s += [W(*inside('field', 'barrier')), W(*inside('field', 'crown_stair'))] + climb('crown_stair')
    s += [W(*inside('crown_top', 'crown_stair')), W(*inside('crown_top', 'crown_landing'))]
    # The aviary: Xeen's Pet.
    s += [W(*inside('arch_s', 'crown_landing')), W(*inside('arch_s', 'aviary_s')),
          {'clear_hostiles': {'radius': 3000}}, {'advance_runtime': {'seconds': 3}}, lua('close()'),
          qbit_is(Q['pet_slain'], label='pet_slain')]
    s += thru('aviary_mid', 'aviary_s', 'aviary_n') + thru('arch_n', 'aviary_n', 'threshold')
    # The throne doors and the plate: the first sight; Lord Xeen held 4 s.
    s += [W(0, G.ROOMS['threshold']['rect'][3] - 160, G.Z[3], radius=48),
          door_open('door_throne', 'throne'),
          W(0, G.ROOMS['throne']['rect'][1] + 96, G.Z[3], radius=40, clear=0),
          lua("wait(1.5); close()"),
          qbit_is(Q['lord_xeen_seen'], label='lord_xeen_seen'),
          {'assert': {'actor_visible': {'actor_index': LORD_IDX, 'dead': False}}},
          lua("wait(5); close()"),
          {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['freed'], 'value': 1}}},
          # No damage without the Slayer Sword (D-47 Q12): blows that would add up (kill: true) leave his HP whole,
          # and the first zeroed hit of the visit gives m35.untouchable's line (map var untouched).
          # (about one swing in twelve lands on him: 96 swings; the map var proves a hit was zeroed)
          {'party_attack': {'actor_index': LORD_IDX, 'member_index': 0, 'count': 48, 'kill': True, 'report': True}},
          {'party_attack': {'actor_index': LORD_IDX, 'member_index': 2, 'count': 48, 'kill': True, 'report': True}},
          {'assert': {'actor_visible': {'actor_index': LORD_IDX, 'dead': False, 'hp': LORD_HP, 'report_state': True}}},
          {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['untouched'], 'value': 1}}},
          # With the Xeen Slayer Sword (12500) in hand, melee blows land and he dies.
          {'grant_item': {'item_id': G.SLAYER_SWORD, 'member_index': 0, 'equip': 'main_hand'}},
          {'party_attack': {'actor_index': LORD_IDX, 'member_index': 0, 'count': 1500, 'kill': True,
                            'report': True}},
          {'advance_runtime': {'seconds': 3}},
          {'assert': {'actor_visible': {'actor_index': LORD_IDX, 'dead': True, 'report_state': True}}},
          {'clear_hostiles': {'radius': 4000}},
          {'advance_runtime': {'seconds': 3}}, lua('close()'),
          qbit_is(Q['lord_xeen_slain'], label='lord_xeen_slain'),
          lua(f"wait(2); if door_state({door('treasury')}) ~= 'open' then error('treasury: ' .. "
              f"door_state({door('treasury')})) end")]
    # The mirror (aaze0078:5), the scepter: No; the hoard, a save and load; the scepter: Yes, the cinematic, out on X9.
    ty = G.THRONE_AT[1]
    s += [W(0, G.ROOMS['apse']['rect'][1] + 120, G.Z[3], radius=64), W(-420, ty - 240, G.Z[3] + 64, radius=48),
          lua(f"click({ev('mirror')}); wait(0.8)"),
          {'assert': {'dialog': {'active': True, 'text_contains': 'force field'}}}, lua('close()'),
          W(0, ty - 240, G.Z[3] + 64, radius=48),
          lua(f"click({ev('throne')}); wait(0.8)"),
          {'assert': {'dialog': {'active': True, 'text_contains': 'Take it?'}}},
          {'answer_input': {'text': 'No'}}, {'advance_runtime': {'seconds': 1}}, lua('close()'),
          qbit_is(Q['done'], on=False, label='done after No'),
          # The hoard, and a save and load, before the scepter (its cinematic ends on X9).
          W(768, G.ROOMS['apse']['rect'][3] - 200, G.Z[3], radius=48),
          W(768, G.ROOMS['treasury']['rect'][1] + 220, G.Z[3], radius=64),
          lua(f"click({ev('chest_hoard')}); wait(0.8); if take_chest() then close() end; close()"),
          {'reload': {}},
          lua(f"if door_state({door('field')}) ~= 'open' then error('field after reload') end; "
              f"if door_state({door('treasury')}) ~= 'open' then error('treasury after reload') end"),
          W(768, G.ROOMS['apse']['rect'][3] - 200, G.Z[3], radius=48),
          W(0, ty - 240, G.Z[3] + 64, radius=48),
          lua(f"click({ev('throne')}); wait(0.8)"),
          {'answer_input': {'text': 'Yes'}}, {'advance_runtime': {'seconds': 18, 'follow_map_move': True}},
          {'advance_runtime': {'seconds': 2, 'follow_map_move': True}},
          qbit_is(Q['done'], label='m35.done'),
          {'assert': {'map': 'xeen_x9.blv'}},
          {'assert': {'party_position': {'x': 0, 'y': 11264, 'radius': 200, 'z_min': 700, 'z_max': 860}}},
          lua("log('after the cinematic: ' .. status()); close()")]
    return t, ("# Playtest of Castle Xeen (XD-19, L4; lane A7, agent:xeen-a7-xd19; written by\n"
               "# output/studio_cal/xd19/tools/gen_tests.py from ids.lock.yml): the critical path. A level-50 party\n"
               "# (immortal) arrives in the gatehall (entrance:x9_gate): m35.arrival; the great hall,\n"
               "# the west ward and gallery, the cold vault's Water Generator ('Destroy?' Yes); the stair hall, the\n"
               "# gravel vault's Earth Generator; the east gallery, up the south-east tower to the Air Generator; the\n"
               "# barrier hall with three generators down (the field stands); the south-west tower top's Fire\n"
               "# Generator: the field falls (barrier_down 118062); up the crown stair, the aviary (Xeen's Pet,\n"
               "# m35.pet), the throne doors' plate (m35.lord_xeen_sight, Lord Xeen freed 4 s later), no damage\n"
               "# without the Slayer Sword (m35.untouchable once), then his death by the sword (m35.lord_xeen; the\n"
               "# treasury opens), the mirror (aaze0078:5), the scepter: No; the hoard, a save and load; the scepter: Yes\n"
               "# (m35.scepter, the cinematic, then out on X9 before the gate: the done event's direct leave).\n")


def playtest_pool():
    t, _ = header('xeen.xd19.l4.pool', "Castle Xeen (XD-19 L4): the guard foundry's hidden pool", None)
    s = t['steps']
    fx0, fy0, fx1, fy1 = G.ROOMS['foundry_w']['rect']
    lx0, ly0, lx1, ly1 = G.ROOMS['grand_landing']['rect']
    pool_ids = sorted(i for i, (pid, rid, grp, at) in enumerate(G.POOL))
    s += [lua('wait(2); close()'),
          {'set_pose': {'map': STEM, 'x': 0, 'y': (ly0 + ly1) // 2, 'z': G.Z[1], 'yaw_degrees': 90, 'pitch': 0}},
          {'advance_runtime': {'seconds': 1}},
          {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['pool_on'], 'value': 1}}},
          {'assert': {'actor_count': {'monster_id': G.GUARD, 'min': N_GUARDS, 'max': N_GUARDS}}},
          {'clear_hostiles': {'radius': 3000}},
          lua('wait(46); close()'),
          {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['pool'], 'value': 1}}},
          {'assert': {'actor_visible': {'actor_index': POOL_IDX[0], 'hidden': False}}},
          {'assert': {'actor_visible': {'actor_index': POOL_IDX[1], 'hidden': True}}},
          {'clear_hostiles': {'radius': 6000}},
          W(*G.MACHINES['w']['at'][:1], G.MACHINES['w']['at'][1] - 520, G.Z[1], radius=64)]
    mx_, my_ = G.MACHINES['w']['at']
    s[-1] = W(mx_ + 400, my_ - 200, G.Z[1], radius=64)
    s += [lua(f"click({ev('machine_w')}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
          {'advance_runtime': {'seconds': 1.5}}, lua('close()'),
          qbit_is(Q['machine_w_down'], label='machine_w_down'),
          lua(f"if door_state({door('bays')}) ~= 'closed' then error('bays open after one machine') end"),
          W(mx_ + 400, 3000, G.Z[1]), W(0, 3000, G.Z[1])]
    ex, ey = G.MACHINES['e']['at']
    s += [W(ex - 400, ey - 200, G.Z[1], radius=64),
          lua(f"click({ev('machine_e')}); wait(0.5)"), {'answer_input': {'text': 'Yes'}},
          {'advance_runtime': {'seconds': 2.5}}, lua('close()'),
          qbit_is(Q['machine_e_down'], label='machine_e_down'),
          qbit_is(Q['bays_open'], label='bays_open'),
          {'assert': {'state_dump_map_var': {'index': LOCK['map_vars']['pool'], 'value': 4}}},
          lua(f"wait(3); if door_state({door('bays')}) ~= 'open' then error('bays: ' .. door_state({door('bays')})) "
              "end"),
          {'assert': {'actor_visible': {'actor_index': POOL_IDX[1], 'hidden': False, 'dead': False}}},
          {'assert': {'actor_visible': {'actor_index': POOL_IDX[2], 'hidden': False, 'dead': False}}},
          {'assert': {'actor_visible': {'actor_index': POOL_IDX[3], 'hidden': False, 'dead': False}}},
          {'clear_hostiles': {'radius': 6000}},
          W(0, 3000, G.Z[1]), W(0, G.ROOMS['foundry']['rect'][3] - 200, G.Z[1], radius=64),
          W(0, G.ROOMS['bays']['rect'][1] + 200, G.Z[1], radius=64),
          W(0, G.ROOMS['bays']['rect'][3] - 240, G.Z[1], radius=48),
          # The tray's three Emeralds (183) arrive in the packs: counted before and after (A3's probe, s21); a
          # second click finds the tray empty and gives nothing.
          lua(f"if held() ~= 0 then stow() end; local before = item_count(183); click({ev('gems')}); wait(0.8); "
              "local s = tostring(status()); if not string.find(s, 'emeralds', 1, true) then error('gems: ' .. s) end; "
              "close(); wait(0.3); if held() ~= 0 then stow() end; local n = item_count(183); "
              "log('emeralds ' .. before .. ' -> ' .. n); if n ~= before + 3 then error('emeralds: ' .. before .. "
              "' -> ' .. n) end; click(" + str(ev('gems')) + "); wait(0.8); s = tostring(status()); "
              "if not string.find(s, 'empty tray', 1, true) then error('second tray click: ' .. s) end; close(); "
              "wait(0.3); if held() ~= 0 then stow() end; if item_count(183) ~= n then error('the tray gave again: ' "
              ".. item_count(183)) end"),
          {'reload': {}},
          lua(f"if door_state({door('bays')}) ~= 'open' then error('bays after reload') end")]
    return t, ("# Playtest of Castle Xeen's guard foundry (XD-19, L4; written by output/studio_cal/xd19/tools/\n"
               "# gen_tests.py): the party is set on the grand landing (the first step into the foundry starts the\n"
               "# pool's clock); 46 s later one of the four hidden guards has been shown (pool 1); the west machine's\n"
               "# 'Destroy?' Yes (the bays stay shut), then the east's: the rest of the pool is shown (pool 4: two\n"
               "# guards left alive after the first two fights), the shutters open (bays_open 118063), the gem tray\n"
               "# gives three Emeralds; after a save and load the bays stay open. The count stays 14 guards (D-47).\n")


def playtest_hostility():
    t, _ = header('xeen.xd19.l4.hostility', "Castle Xeen (XD-19): its rows hostile, no fights among them", None)
    s = t['steps']
    rows = {G.DEMON: 28, G.DEVIL: 14, G.SCREAMER: 4, G.GUARD: 10, G.FIRE_EL: 2, G.AIR_EL: 2, G.WATER_EL: 2,
            G.EARTH_EL: 2, G.GREATER: 2, G.PET: 1, G.LORD: 1}
    s += [{'advance_runtime': {'seconds': 2}}, lua('close()')]
    for r, n in rows.items():
        s.append({'assert': {'actor_count': {'monster_id': r, 'hostile': False, 'max': 0}}})
        s.append({'assert': {'actor_count': {'monster_id': r, 'hostile': True, 'min': n}}})
    s.append({'reload': {}})
    for r, n in rows.items():
        s.append({'assert': {'actor_count': {'monster_id': r, 'hostile': False, 'max': 0}}})
    gx, gy = G.START
    s += [{'note': "A Demon, a Xeen's Guard, a Lesser Air Elemental and a Greater Elemental side by side in the great "
                   "hall, nearer each other than the party: they must not take each other on, and they go for the "
                   "party."},
          {'console': {'line': 'arena trace on'}},
          {'spawn_actor': {'monster_id': G.DEMON, 'x': -200, 'y': -2300, 'z': 16}},
          {'spawn_actor': {'monster_id': G.GUARD, 'x': 200, 'y': -2300, 'z': 16}},
          {'spawn_actor': {'monster_id': G.AIR_EL, 'x': -200, 'y': -2000, 'z': 16}},
          {'spawn_actor': {'monster_id': G.GREATER, 'x': 200, 'y': -2000, 'z': 16}},
          {'advance_runtime': {'seconds': 12}},
          {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}},
          {'assert': {'ai_trace': {'actor_index': 'last', 'event': 'target', 'target': 'party', 'min_count': 1}}}]
    return t, ("# Hostility check of Castle Xeen (XD-19, L4; written by output/studio_cal/xd19/tools/gen_tests.py):\n"
               "# A2's demons (11630-11632), Xeen's Guard (11603; the four hidden at the chutes not counted while\n"
               "# hidden), the elementals (11620, 11624-11626, 11622), Xeen's Pet (11644) and Lord Xeen (11634) all\n"
               "# hostile at load and after a save and load; side by side they do not fight each other and go for the\n"
               "# party. No window is open before the reload.\n")


def playtest_gate():
    t, _ = header('xeen.xd19.l4.gate', "Castle Xeen (XD-19 L4): the gate out to X9", None)
    s = t['steps']
    gx0, gy0, gx1, gy1 = G.ROOMS['gate']['rect']
    s += [lua('wait(2); close()'),
          W(-128, gy0 + 120, 0, radius=48),
          {'execute_event': {'id': ev('gate_r')}},
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'OK'}},
          {'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}},
          {'assert': {'map': 'xeen_x9.blv'}},
          lua("log('landing: ' .. status())"),
          {'assert': {'party_position': {'x': 0, 'y': 11264, 'radius': 160, 'z_min': 700, 'z_max': 860}}}]
    return t, ("# Playtest of Castle Xeen's gate (XD-19, L4; written by output/studio_cal/xd19/tools/gen_tests.py): the\n"
               "# gate's west leaf (the exit preset; into an indoor map, so no leave window) out to X9 at its named\n"
               "# arrival entrance:xd19_gate (0, 11264, 768) facing south, the landing measured. X9's gate back in\n"
               "# (to entrance:x9_gate) is A5's, opened once XD-19 is installed.\n")


def write(name, pair):
    t, comment = pair
    with open(L4 / f'{name}.yml', 'w') as f:
        f.write(comment)
        yaml.dump(t, f, sort_keys=False, width=120, allow_unicode=True)


if __name__ == '__main__':
    write('playtest', playtest())
    write('playtest_pool', playtest_pool())
    write('playtest_hostility', playtest_hostility())
    write('playtest_gate', playtest_gate())
    print('written playtest, playtest_pool, playtest_hostility, playtest_gate')
