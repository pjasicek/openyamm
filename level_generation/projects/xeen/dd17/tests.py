#!/usr/bin/env python3
"""Writes DD-17's playtests into devdocs/xeen/briefs/dd17/L4 from the generator's geometry and the L4's ids.lock.yml
(event, door and actor numbers), so a renumbering or a re-scale rewrites them. Run after `gen.py L4` and a build."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dress  # noqa: E402
import gen  # noqa: E402
import geo  # noqa: E402

L4 = gen.BR / 'L4'
LOCK = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
EV, DOOR = LOCK['events'], LOCK['doors']
sc = gen.sc


def ev(name):
    return EV['evt:' + name]


def door(name):
    return DOOR[name]


def actor_index(mid):
    objs = yaml.safe_load((L4 / 'objects.yml').read_text())
    ids = sorted(m['id'] for m in objs['monsters'])
    return ids.index(mid)


SOUL_BOX, CUBE = 12364, 12365
ARR = [sc(dress.ARRIVAL_AT[0]), sc(dress.ARRIVAL_AT[1])]
ROOF = [sc(dress.ROOF_AT[0]), sc(dress.ROOF_AT[1])]
PARTY = {'gold': 0, 'food': 20, 'members': [
    {'name': 'Brokk', 'class': 'Knight', 'level': 53, 'skills': [], 'equipment': {}},
    {'name': 'Hild', 'class': 'Cleric', 'level': 53, 'skills': [], 'equipment': {}},
    {'name': 'Ivar', 'class': 'Archer', 'level': 53, 'skills': [], 'equipment': {}},
    {'name': 'Sefa', 'class': 'Sorcerer', 'level': 53, 'skills': [], 'equipment': {}}]}


def lua(src):
    return {'play_lua': {'source': src}}


def check(cond, msg):
    return lua(f"if not ({cond}) then error({msg!r} .. ' / ' .. status() .. ' / doors ' .. door_state(1) .. ' ' .. door_state({DOOR['door:field_fire']}) .. ' / ' .. party()) end")


def walk(x, y, z, r=64, t=40, close=True):
    return {'walk_to': {'x': x, 'y': y, 'z': z, 'radius': r, 'timeout_seconds': t, 'clear_hostiles': 3000,
                        'close_dialogs': close}}


def pose(x, y, z, yaw):
    return {'set_pose': {'map': 'xeen_dd17.blv', 'x': x, 'y': y, 'z': z, 'yaw_degrees': yaw, 'pitch': 0}}


def step_onto(x0, y0, z, yaw, x1, y1, secs=0.45):
    """A short key press from (x0, y0) onto a plate near (x1, y1): walk_to stops when a window opens."""
    return {'movement_segment': {'input': 'forward', 'seconds': secs, 'loose_tolerance': True, 'tolerance_xy': 6000,
                                 'tolerance_z': 40, 'start': {'map': 'xeen_dd17.blv', 'x': x0, 'y': y0, 'z': z,
                                                              'yaw_degrees': yaw},
                                 'expect_stop': {'map': 'xeen_dd17.blv', 'x': x1, 'y': y1, 'z': z}}}


def adv(s, dialogs=False, follow=False):
    d = {'seconds': s}
    if dialogs:
        d['present_dialogs'] = True
    if follow:
        d['follow_map_move'] = True
    return {'advance_runtime': d}


def pos(x, y, r=96, zmin=None, zmax=None, facing=None):
    p = {'x': x, 'y': y, 'radius': r}
    if zmin is not None:
        p['z_min'], p['z_max'] = zmin, zmax
    if facing is not None:
        p['facing'], p['facing_within'] = facing, 64
    return {'assert': {'party_position': p}}


def dialog(text):
    return {'assert': {'dialog': {'active': True, 'text_contains': text}}}


def prologue(box=True):
    """New game on D6; with the Soul Box, moved into DD-17 at entrance:d6_gate (as D6's door does)."""
    s = [{'new_game_flow': {'start_map': 'xeen_d6.odm', 'party': PARTY}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}}, adv(2), lua("close()")]
    if box:
        s.append({'grant_item': {'item_id': SOUL_BOX}})
    s += [{'lua_event': {'source': f'evt.MoveToMap({ARR[0]}, {ARR[1]}, 0, 512, 0, 0, 0, 0, "xeen_dd17.blv")'}},
          adv(3, dialogs=True, follow=True)]
    return s


def answer(event, text, wait=0.6, asks=None):
    s = [lua(f"click({event}); wait({wait})")]
    if asks:
        s.append(dialog(asks))
    return s + [{'answer_input': {'text': text}}, adv(0.8, dialogs=True)]


def turn_dial(el, times):
    s = []
    for _ in range(times):
        s += [lua(f"close(); click({ev('dial_' + el)}); wait(0.5)"), {'answer_input': {'text': 'Yes'}}, adv(0.4)]
    return s


def head_room_centre(el):
    (w, h), c = geo.extent(dress.HEAD_ROOMS[el])
    return [sc(c[0]), sc(c[1])]


def dial_point(el):
    room = geo.DIAL_ROOM[el]
    (w, h), c = geo.extent(room)
    x, y = geo.DIAL_AT[el]
    # stand between the plinth and the field
    return [sc((c[0] + x) / 2 + (256 if el in ('fire', 'water') else -256)), sc(y)]


def main():
    s = prologue()
    s += [dialog("The Soul Box hums"), lua("close()"), {'assert': {'map': 'xeen_dd17.blv'}},
          pos(ARR[0], ARR[1], 64, -8, 8, 512),
          check("qbit(111660) and qbit(117600)", "m33.arrival did not set inside / arrived_once")]
    # The gate before nine, the lift before the gate.
    ix = sc(896)
    s += [pose(ix, 0, geo.RIM, 0), {'clear_hostiles': {'radius': 4000}},
          lua(f"click({ev('gate')}); wait(0.8)"), dialog("The time is not right"), lua("close()"),
          check(f"door_state({door('door:gate')}) == 'closed'", "the gate opened before nine")]
    lx = sc(geo.LIFT_AT[0])
    s += [pose(lx, 0, geo.L2, 0),
          lua(f"status(); click({ev('lift_low')}); wait(1)"),
          check(f"string.find(status(), 'Access to the upper floor is denied!', 1, true) and door_state({door('lift:core')}) == 'closed'",
                "the lift ran before the gate")]
    # The fire belt: the mouth plate's ride keeps the facing given (north, 512), the back plate carries forward again.
    bx = sc(-1920)
    land = sc(dress.BELTS['fire'][5])
    mouth, back = sc(dress.BELTS['fire'][3]), sc(dress.BELTS['fire'][4])

    def seg(y0, yaw):
        return {'movement_segment': {'input': 'forward', 'seconds': 0.35, 'loose_tolerance': True, 'tolerance_xy': 6000,
                                     'tolerance_z': 40,
                                     'start': {'map': 'xeen_dd17.blv', 'x': bx, 'y': y0, 'z': 0, 'yaw_degrees': yaw},
                                     'expect_stop': {'map': 'xeen_dd17.blv', 'x': bx, 'y': land, 'z': 0}}}
    s += [{'clear_hostiles': {'radius': 4000}}, lua("status()"),
          {'note': "Short recorded walks onto the plates: each ride lands at the belt's end facing north (512), the "
                   "facing it gives (A1's merge point 28); the held key is playtest_belt.yml."},
          seg(mouth - 96 - 100, 90), adv(0.3),
          check("string.find(status(), 'The floor lurches and carries you along.', 1, true)", "no belt line"),
          pos(bx, land, 400, -8, 8, 512), lua("log('fire belt ride: ' .. party())"),
          seg(back + 96 + 100, 270), adv(0.3), pos(bx, land, 400, -8, 8, 512), lua("log('fire belt back ride')")]
    # The maintenance door before the Head is visited: bolted.
    s += [pose(sc(-2624), sc(1408), 0, 90),
          lua(f"status(); click({ev('maint_fire')}); wait(1)"),
          check(f"string.find(status(), 'bolted on the other side', 1, true) and door_state({door('door:maint_fire')}) == 'closed'",
                "the maintenance door opened from the return side first")]
    # The four Heads (the fire one walked into from its belt's end), each shut down.
    for el in ('fire', 'water', 'air', 'earth'):
        hx, hy = head_room_centre(el)
        if el == 'fire':
            s += [walk(hx, hy, 0, 96)]
        else:
            s += [pose(hx, hy, 0, 90)]
        s += [{'clear_hostiles': {'radius': 4000}}, lua("status()")]
        if el == 'fire':
            # D-66: one Yes/No prompt with the Head's line; No leaves the field up.
            s += [lua(f"click({ev('head_' + el)}); wait(0.6)"), dialog(dress.HEAD_ASK[el]),
                  {'answer_input': {'text': 'No'}}, adv(1, dialogs=True), lua("close()"), adv(1),
                  check(f"not qbit({dress.QB[el]}) and door_state({door('door:field_' + el)}) == 'closed'",
                        "No shut the fire Head down")]
        s += [lua(f"click({ev('head_' + el)}); wait(0.6)"), dialog(dress.HEAD_ASK[el]),
              {'answer_input': {'text': 'Yes'}}, adv(1, dialogs=True), dialog("Somewhere above, a field dies."),
              lua("close()"), adv(3),
              check(f"qbit({dress.QB[el]}) and door_state({door('door:field_' + el)}) == 'open'",
                    f"the {el} Head did not drop its field"),
              lua(f"click({ev('maint_' + el)}); wait(2)"),
              check(f"door_state({door('door:maint_' + el)}) == 'open'", f"the {el} maintenance door did not open")]
    # The four sundials to nine (fire 3, air 6, earth 12, water 7); each slab rises at nine.
    turns = {'fire': 6, 'air': 3, 'earth': 9, 'water': 2}
    for el in ('fire', 'air', 'earth', 'water'):
        x, y = dial_point(el)
        s += [pose(x, y, geo.L2, 0), {'clear_hostiles': {'radius': 4000}}, lua("status()")]
        s += turn_dial(el, turns[el])
        s += [check("string.find(status(), 'The dial clicks home at nine.', 1, true)", f"no line at nine ({el})"),
              adv(4),
              check(f"door_state({door('lift:slab_' + el)}) == 'open'", f"the {el} slab did not rise")]
    s += [check("qbit(111663)", "m33.sundial_nine not set with four at nine")]
    # The bridges: from the lip across the four slabs to the island.
    s += [pose(sc(-1088), 0, geo.RIM, 0), {'clear_hostiles': {'radius': 4000}},
          walk(sc(-512), 0, geo.RIM, 48), walk(sc(0), 0, geo.RIM, 48), walk(sc(448), 0, geo.RIM, 48),
          walk(ix, 0, geo.RIM, 64), pos(ix, 0, 96, geo.RIM - 16, geo.RIM + 16),
          lua("log('on the island: ' .. party())")]
    # The gate: a wrong name, then Sheltem.
    s += answer(ev('gate'), 'Alamar', asks=dress.GATE_ASK) + [dialog("Wrong!"), lua("close()"),
                                         check(f"door_state({door('door:gate')}) == 'closed' and not qbit(111661)",
                                               "a wrong name opened the gate")]
    s += answer(ev('gate'), 'Sheltem', asks=dress.GATE_ASK) + [dialog("Access approved!"), lua("close()"), adv(3),
                                          check(f"qbit(111661) and door_state({door('door:gate')}) == 'open'",
                                                "Sheltem did not open the gate")]
    # The lift up to the deck.
    s += [walk(sc(1440), 0, geo.L2, 64), walk(lx, 0, geo.L2, 48),
          lua(f"click({ev('lift_low')}); wait(4)"), adv(2),
          check(f"door_state({door('lift:core')}) == 'open'", "the lift did not rise"),
          pos(lx, 0, 160, geo.L3 - 16, geo.L3 + 16)]
    # A trapdoor: the first plate inside the lift head drops the party 1,280 to the chasm floor; the way back.
    tx, ty = sc(geo.TRAPS[0][1][0]), sc(geo.TRAPS[0][1][1])
    s += [walk(sc(1088), 0, geo.L3, 64), walk(tx, ty, geo.L3, 48, 20), adv(4),
          pos(tx, ty, 200, -16, 64),
          check(f"door_state({door('lift:trap_t1')}) == 'closed'", "the trapdoor did not fall"),
          lua("log('after the fall: ' .. party())"),
          walk(sc(512), sc(-500), 0, 64), walk(sc(448), sc(-830), 0, 48), walk(sc(448), sc(-1080), 0, 48),
          walk(sc(448), sc(-1300), 0, 48), walk(sc(448), sc(-1500), 0, 48), walk(sc(448), sc(-1720), 0, 64),
          walk(sc(-640), sc(-1720), 0, 64), walk(sc(-640), sc(-2240), 0, 64),
          lua(f"status(); click({ev('door_sump')}); wait(1)"),
          check(f"door_state({door('door:sump')}) == 'closed'", "the sump door opened without its lever"),
          lua(f"click({ev('sump_lever')}); wait(3)"),
          check(f"door_state({door('door:sump')}) == 'open'", "the sump lever did not open the door"),
          lua(f"click({ev('sump_bones')}); wait(0.5)"),
          walk(sc(-64), sc(-2240), 0, 64), walk(sc(32), sc(-2208), 0, 64),
          walk(sc(1000), sc(-2208), geo.L2, 64), walk(sc(960), sc(-2560), geo.L2, 64),
          walk(sc(960), sc(-2944), geo.L2, 96), pos(sc(960), sc(-2944), 128, geo.L2 - 16, geo.L2 + 16),
          lua("log('back on the south walk: ' .. party())")]
    # The robot bay's vault release, the strongroom; the juice; "Come to ME!".
    s += [pose(sc(864), sc(2240), geo.L3, 0), {'clear_hostiles': {'radius': 5000}},
          lua(f"click({ev('vault_release')}); wait(0.6)"), dialog("Vault release. Pull?"),
          {'answer_input': {'text': 'Yes'}}, adv(4),
          check(f"qbit(117605) and door_state({door('door:vault')}) == 'open'", "the vault release did not open the strongroom"),
          lua(f"click({ev('juice')}); wait(0.5)"), check("string.find(status(), '+2 Might', 1, true)", "no juice line"),
          lua(f"click({ev('juice')}); wait(0.5)"), check("string.find(status(), 'You have had yours', 1, true)", "no second juice line"),
          pose(sc(-1088), 0, geo.L3, 180), {'clear_hostiles': {'radius': 5000}},
          step_onto(sc(-1536) + 200, 0, geo.L3, 180, sc(-1536), 0), adv(1, dialogs=True), dialog("Come to ME!"),
          lua("close()"),
          check("qbit(117606)", "Come to ME not set")]
    # Command Central: Sheltem and Corak hidden; the dais plate's No, then Yes: the cinematic, the leave to D6.
    sh, co = actor_index('monster:sheltem'), actor_index('monster:corak')
    px, py = sc(-2272), sc(-3072)
    s += [{'assert': {'actor_visible': {'actor_index': sh, 'monster_id': dress.SHELTEM, 'hidden': True}}},
          {'assert': {'actor_visible': {'actor_index': co, 'monster_id': dress.CORAK, 'hidden': True}}},
          {'clear_hostiles': {'radius': 5000}},
          step_onto(px + 200, py, geo.L3, 180, px, py), adv(0.8, dialogs=True),
          dialog("Before the throne. Open the Soul Box?"), {'answer_input': {'text': 'No'}}, adv(1, dialogs=True), lua("close()"),
          check("not qbit(111662)", "No ran the confrontation"),
          step_onto(px + 200, py, geo.L3, 180, px, py), adv(0.8, dialogs=True),
          dialog("Before the throne. Open the Soul Box?"), {'answer_input': {'text': 'Yes'}},
          adv(4, dialogs=True),
          {'assert': {'actor_visible': {'actor_index': sh, 'monster_id': dress.SHELTEM, 'hidden': False}}},
          {'assert': {'actor_visible': {'actor_index': co, 'monster_id': dress.CORAK, 'hidden': False}}},
          lua("log('cinematic: Sheltem and Corak shown')"),
          adv(18, follow=True), adv(3, follow=True), lua("close()"),
          {'assert': {'map': 'xeen_d6.odm'}},
          pos(dress.D6[0], dress.D6[1], 200, None, None, dress.D6[3]),
          check(f"qbit(111662) and has_item({CUBE}) and not has_item({SOUL_BOX})", "m33.sheltem's state"),
          lua("log('D6 after the cinematic: ' .. party())")]
    return s


def dials():
    """Dial reset and sync: water to nine (its slab up), a save and a load (still up), one more turn (it drops)."""
    s = prologue() + [lua("close()")]
    for el in ('water',):
        hx, hy = head_room_centre(el)
        s += [pose(hx, hy, 0, 90), {'clear_hostiles': {'radius': 4000}},
              lua(f"click({ev('head_' + el)}); wait(0.6)"), {'answer_input': {'text': 'Yes'}}, adv(3, dialogs=True),
              lua("close()")]
    x, y = dial_point('water')
    slab = door('lift:slab_water')
    s += [pose(x, y, geo.L2, 0), {'clear_hostiles': {'radius': 4000}}, lua("status()")]
    s += turn_dial('water', 2)
    s += [check("string.find(status(), 'The dial clicks home at nine.', 1, true)", "no line at nine"), adv(4),
          check(f"door_state({slab}) == 'open'", "the water slab did not rise"),
          lua("close()"), {'reload': {}}, adv(3, dialogs=True),
          lua("if close() then error('the castle greets again after a load: ' .. status()) end"),
          check(f"door_state({slab}) == 'open'", "the water slab dropped after a reload"),
          check("not qbit(111663)", "sundial_nine set with one dial at nine")]
    s += turn_dial('water', 1)
    s += [check("string.find(status(), 'Somewhere below, stone drops away.', 1, true)", "no line leaving nine"), adv(4),
          check(f"door_state({slab}) == 'closed'", "the water slab did not drop"),
          lua("close()"), {'reload': {}}, adv(3, dialogs=True),
          lua("if close() then error('the castle greets again after a load: ' .. status()) end"),
          check(f"door_state({slab}) == 'closed'", "the water slab rose after a reload")]
    return s


def hatch():
    """The roof hatch: bolted before roof_unlocked, then up to D7's entrance:dd17_roof; and back in from D7."""
    s = prologue() + [lua("close()")]
    s += [pose(ROOF[0], ROOF[1], geo.L3, 0), lua(f"click({ev('hatch')}); wait(0.8)"), dialog("Bolted from above."),
          lua("close()"), {'assert': {'map': 'xeen_dd17.blv'}},
          {'lua_event': {'source': 'SetQBit(QBit(113521))'}},
          lua(f"click({ev('hatch')}); wait(0.8)"),
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'Close'}}, adv(1, dialogs=True), lua("close()"),
          {'assert': {'map': 'xeen_dd17.blv'}},
          lua(f"click({ev('hatch')}); wait(0.8)"),
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'OK'}}, adv(2, follow=True), adv(1, follow=True), lua("close()"),
          {'assert': {'map': 'xeen_d7.blv'}}, pos(dress.D7[0], dress.D7[1], 160, None, None, dress.D7[3]),
          lua("log('D7 roof: ' .. party())"),
          {'lua_event': {'source': f'evt.MoveToMap({ROOF[0]}, {ROOF[1]}, {geo.L3}, 0, 0, 0, 0, 0, "xeen_dd17.blv")'}},
          adv(3, dialogs=True, follow=True), dialog("The Soul Box hums"), lua("close()"),
          {'assert': {'map': 'xeen_dd17.blv'}}, pos(ROOF[0], ROOF[1], 64, geo.L3 - 8, geo.L3 + 8, 0),
          lua("log('entrance:d7_roof: ' .. party())")]
    return s


def refused():
    """Without the Soul Box (D-89, 2026-11-22: no refusal moves the party; the box is checked at D6's gate and D7's
    hatch): an arrival at the gate and one by the roof show no line and leave the party inside."""
    s = prologue(box=False)
    s[-1] = adv(3, follow=True)
    s.insert(-1, lua("status()"))
    s += [adv(2, dialogs=True), lua("if close() then error('a window on a refused arrival') end"),
          check("not string.find(status(), 'nothing I need to fear', 1, true)", "the refusal line inside"),
          {'assert': {'map': 'xeen_dd17.blv'}},
          check("not qbit(111664) and not qbit(111660)", "refused_once or inside set without the box"),
          lua("log('no box at the gate: ' .. party())"),
          {'lua_event': {'source': f'evt.MoveToMap({ROOF[0]}, {ROOF[1]}, {geo.L3}, 0, 0, 0, 0, 0, "xeen_dd17.blv")'}},
          adv(3, dialogs=True, follow=True), adv(1, follow=True),
          lua("if close() then error('a window on a refused roof arrival') end"),
          {'assert': {'map': 'xeen_dd17.blv'}}, pos(ROOF[0], ROOF[1], 96, geo.L3 - 8, geo.L3 + 8),
          lua("log('no box by the roof: ' .. party())")]
    return s


def belt():
    """D-66 item 7: the fire belt crossed with the forward key held, as everyone walks (A1's merge point 28,
    tests/scenarios/xeen/dd17_belt_forward_held.yml): held 1.2 s from 912 short of the mouth plate, the ride comes at
    about 1.05 s and lands at the belt's far end facing north (512); the held key walks on a little after it. Then a
    tap onto the plate: the party lands there facing 512 and a second later is still there."""
    bx, land, mouth = sc(-1920), sc(dress.BELTS['fire'][5]), sc(dress.BELTS['fire'][3])
    s = prologue() + [lua("close()"), {'clear_hostiles': {'radius': 4000}}, lua("status()"),
                      pose(bx, mouth - 912, 0, 90), adv(0.2),
                      {'press_action': {'action': 'forward', 'seconds': 1.2}},
                      check("string.find(status(), 'The floor lurches and carries you along.', 1, true)", "no belt line"),
                      lua("log('held-key belt ride: ' .. party())"),
                      {'assert': {'party_position': {'x': bx, 'y': land, 'radius': 260, 'facing': 512,
                                                     'facing_within': 8}}},
                      pose(bx, mouth - 128, 0, 90), adv(0.2),
                      {'press_action': {'action': 'forward', 'seconds': 0.15}},
                      pos(bx, land, 96, -8, 8, 512), adv(1), pos(bx, land, 96, -8, 8, 512),
                      lua("log('tapped belt ride: ' .. party())")]
    return s


def exit_():
    s = prologue() + [lua("close()"),
                      walk(0, sc(-3780), 0, 64), lua(f"click({ev('exit_gate')}); wait(0.5)"),
                      {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
                      {'select_topic': {'match_label': 'OK'}}, adv(1.5, follow=True),
                      {'assert': {'map': 'xeen_d6.odm'}},
                      pos(dress.D6[0], dress.D6[1], 160, None, None, dress.D6[3]),
                      lua("log('D6 by the gate: ' .. party())")]
    return s


def hostility():
    s = prologue() + [lua("close()")]
    counts = {11610: 30, 11611: 20, 11612: 6, 11620: 2, 11624: 2, 11625: 2, 11626: 2, 11572: 6}
    for mid, n in counts.items():
        s += [{'assert': {'actor_count': {'monster_id': mid, 'hostile': True, 'min': n, 'max': n}}},
              {'assert': {'actor_count': {'monster_id': mid, 'hostile': False, 'max': 0}}}]
    sh, co = actor_index('monster:sheltem'), actor_index('monster:corak')
    s += [{'assert': {'actor_visible': {'actor_index': sh, 'monster_id': dress.SHELTEM, 'hidden': True}}},
          {'assert': {'actor_visible': {'actor_index': co, 'monster_id': dress.CORAK, 'hidden': True}}},
          {'assert': {'actor_count': {'monster_id': dress.SHELTEM, 'hostile': True, 'max': 0}}},
          {'assert': {'actor_count': {'monster_id': dress.CORAK, 'hostile': True, 'max': 0}}},
          {'note': 'No infighting: robots, elementals and gazers left alone for 20 s, the party out of reach.'},
          pose(ARR[0], ARR[1], 0, 90), adv(20)]
    for mid, n in counts.items():
        s += [{'assert': {'actor_count': {'monster_id': mid, 'hostile': True, 'min': n, 'max': n}}}]
    return s


HEADERS = {
    'playtest': ("Playtest of Castle Alamar (DD-17, L4): from D6 with the Soul Box (m33.arrival); the gate before the "
                 "dials and the lift before the gate refuse; the fire belt's ride and back ride keep the facing given "
                 "(north); the maintenance door bolted until the Head; the four Heads shut down (each field drops, "
                 "each maintenance door opens); the four sundials to nine (the line at nine, each slab rises); across "
                 "the four bridges to the island; the gate: a wrong name, then Sheltem; the lift up; a trapdoor drops "
                 "the party 1,280 and it walks out by the sump's lever and the stair; the vault release, the juice, "
                 "'Come to ME!'; the dais plate's No and Yes, the cinematic shows Sheltem and Corak, the leave to "
                 "D6's entrance:dd17_gate. Numbers from ids.lock.yml (output/studio_cal/dd17/tools/tests.py)."),
    'playtest_dials': ("Dial reset and sync (D-61): the water Head off, the water dial to nine (its slab rises), a save "
                       "and a load (still up), one more turn (the line, the slab drops), a save and a load (still down). "
                       "No load greets the party again (the arrival line once per real entry, A3's segment 77)."),
    'playtest_hatch': ("The roof hatch (Q-D26, D-61 Q14, D7 installed): 'Bolted from above.' before roof_unlocked; with "
                       "113521 set the climb lands on D7 at entrance:dd17_roof facing 1024; back in at entrance:d7_roof."),
    'playtest_refused': ("Without the Soul Box (D-89: the box is checked before the move, at D6's gate and D7's hatch): "
                         "an arrival at the gate or by the roof shows nothing and moves nobody."),
    'playtest_belt': ("D-66 item 7: the fire belt crossed with the forward key held rides to its far end facing north "
                      "(512); a tap onto the plate lands there facing 512 and stays (A1's merge point 28, game "
                      "06:49:47)."),
    'playtest_exit': "The way out: the gate's exit preset (OK) to D6's entrance:dd17_gate, facing south (1536).",
    'playtest_hostility': ("Hostility: 30 Patrols, 20 Annihilators, 6 Autobots, the eight Head elementals and 6 Gamma "
                           "Gazers hostile at load, none peaceful; Sheltem and Corak hidden and never hostile; after "
                           "20 s nobody has fallen to infighting."),
}


def write():
    for name, fn in (('playtest', main), ('playtest_dials', dials), ('playtest_hatch', hatch),
                     ('playtest_refused', refused), ('playtest_exit', exit_), ('playtest_hostility', hostility),
                     ('playtest_belt', belt)):
        doc = {'id': f'xeen.dd17.l4.{name}', 'title': f'Castle Alamar (DD-17 L4): {name}', 'world': 'xeen',
               'mode': 'faithful', 'steps': fn()}
        text = yaml.dump(doc, Dumper=gen.D, sort_keys=False, allow_unicode=True, width=120)
        head = '\n'.join('# ' + line for line in _wrap(HEADERS[name])) + \
            "\n# Run with --world xeen --map xeen_dd17.blv (output/studio_cal/dd17/four.sh). Written by tools/tests.py.\n"
        (L4 / f'{name}.yml').write_text(head + text)


def _wrap(t, w=116):
    out, line = [], ''
    for word in t.split():
        if len(line) + len(word) + 1 > w:
            out.append(line)
            line = word
        else:
            line = (line + ' ' + word).strip()
    out.append(line)
    return out


if __name__ == '__main__':
    write()
