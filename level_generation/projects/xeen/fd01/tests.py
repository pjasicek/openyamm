#!/usr/bin/env python3
"""Writes FD-01's playtests into devdocs/xeen/briefs/fd01/L4 from the generator's geometry and the L4's ids.lock.yml
(event and door numbers), so a renumbering rewrites them. Run after `gen.py L4` and a build (cycle.sh)."""
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
MAP = 'xeen_fd01.blv'
CUBE, KEY, AMULET = 12365, 12376, 12372


def ev(name):
    return EV['evt:' + name]


def door(name):
    return DOOR[name]


PARTY = {'gold': 0, 'food': 20, 'members': [
    {'name': 'Brokk', 'class': 'Knight', 'level': 58, 'skills': [], 'equipment': {}},
    {'name': 'Hild', 'class': 'Paladin', 'level': 58, 'skills': [], 'equipment': {}},
    {'name': 'Ivar', 'class': 'Archer', 'level': 58, 'skills': [], 'equipment': {}},
    {'name': 'Sefa', 'class': 'Knight', 'level': 58, 'skills': [], 'equipment': {}}]}


def lua(src):
    return {'play_lua': {'source': src}}


def check(cond, msg):
    return lua(f"if not ({cond}) then error({msg!r} .. ' / ' .. status() .. ' / ' .. party()) end")


def walk(x, y, z=0, r=64, t=40, hostiles=2500, close=True):
    d = {'x': x, 'y': y, 'z': z, 'radius': r, 'timeout_seconds': t, 'close_dialogs': close}
    if hostiles:
        d['clear_hostiles'] = hostiles
    return {'walk_to': d}


def pose(x, y, z, yaw):
    return {'set_pose': {'map': MAP, 'x': x, 'y': y, 'z': z, 'yaw_degrees': yaw, 'pitch': 0}}


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


def click_dialog(event, text, wait=0.6):
    return [lua(f"close(); click({event}); wait({wait})"), adv(0.5, dialogs=True), dialog(text)]


def click_status(event, text, wait=0.8):
    return [lua(f"close(); status(); click({event}); wait({wait})"),
            check(f"string.find(status(), {text!r}, 1, true)", f"event {event} did not say {text!r}")]


def wait_door(d, state, n=30):
    return lua(f"for _ = 1, {n} do if door_state({d}) == '{state}' then break end; wait(0.5) end; "
               f"if door_state({d}) ~= '{state}' then error('door {d} is ' .. door_state({d}) .. ', not {state}') end")


def reload_():
    return [lua("for i = 1, 4 do if not close() then break end wait(0.3) end"), {'reload': {}}, adv(3, dialogs=True),
            lua("for i = 1, 4 do if not close() then break end wait(0.3) end")]


def prologue(start='xeen_d6.odm', cube=True, to=None):
    """New game on D6 (or D7); with the Cube; moved into FD-01 as D6's stair (or D7's hatch) does."""
    s = [{'new_game_flow': {'start_map': start, 'party': PARTY}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}}, adv(2), lua("close()")]
    if cube:
        s.append({'grant_item': {'item_id': CUBE}})
    x, y, z, f = to or (0, 0, 0, 1024)
    s += [{'lua_event': {'source': f'evt.MoveToMap({x}, {y}, {z}, {f}, 0, 0, 0, 0, "{MAP}")'}},
          adv(1.5, follow=True), {'assert': {'map': MAP}}, adv(2, dialogs=True)]
    return s


def header(path, comment, tid, title, steps):
    text = ''.join('# ' + line + '\n' for line in comment.strip().split('\n'))
    text += '# Run with --world xeen --map xeen_fd01.blv (output/studio_cal/fd01/four.sh). Written by tools/tests.py.\n'
    body = yaml.dump({'id': tid, 'title': title, 'world': 'xeen', 'mode': 'faithful', 'steps': steps},
                     Dumper=gen.D, sort_keys=False, allow_unicode=True, width=120)
    (L4 / path).write_text(text + body)


# the way from the stair round the C to the Hall of Nine and the lever hall
def to_levers():
    return [
        walk(-1400, -512), lua(f"open_door({ev('door_gallery')}, {door('door:gallery')})"),
        walk(-2300, -512), walk(-3600, -512), walk(-5500, -512), walk(-6600, -512),
        lua(f"open_door({ev('door_guard')}, {door('door:guard')})"),
        walk(-7168, -512), walk(-7168, 2000), walk(-7168, 5000), walk(-7168, 7168), walk(-5000, 7168),
        walk(-2816, 7168), lua(f"open_door({ev('door_north')}, {door('door:north')})"),
        walk(-2816, 6500), walk(-2816, 5000), walk(-2816, 4300), walk(-3456, 3200), walk(-3456, 2496),
        {'clear_hostiles': {'radius': 5000}},
    ]


def pull(side, first=True):
    other = {'west': 'east', 'east': 'west'}
    text = f"Far to the {side}, a wall grinds down into the floor." if first else "The lever won't budge."
    s = click_status(ev('lever_' + side), text)
    if first:
        s += [check(f"qbit({gen.QBITS['slab_' + side]})", f"slab_{side} not set"),
              wait_door(door('door:slab_' + side), 'open')] + thrown(side)
    return s


def thrown(side):
    """D-71 P2: the lever stands thrown down (its one mover, arm and grip, swung to its end)."""
    return [wait_door(door(f'mover:lever_{side}_arm'), 'open')]


def levers_then_east():
    """From the lever hall: back through the Hall of Nine and the sealed passage into the workshop, to the key vault."""
    return [walk(-3456, 3200), walk(-3900, 3840), walk(-4600, 3840), walk(-4608, 2000), walk(-4608, 1100),
            walk(-4608, 400), {'clear_hostiles': {'radius': 4000}}, walk(-3200, 640), walk(-2240, 700),
            walk(-1700, 768), {'clear_hostiles': {'radius': 4000}}]


def main_test():
    s = prologue()
    s += [pos(0, 0, 64, -8, 8, 1024),
          lua("if close() then error('a line on the D6 arrival: ' .. status()) end"),
          # the statue's boast as the party comes near, once
          walk(-560, 0, hostiles=0), pose(-900, -64, 0, 180), adv(1, dialogs=True),
          dialog("Not only is Alamar a wise and just ruler"),
          lua("close()"), check(f"qbit({gen.QBITS['statue_spoken']})", "statue_spoken 117840 not set"),
          walk(-500, 0, hostiles=0), pose(-1000, -200, 0, 180), adv(1, dialogs=True),
          lua("if close() then error('the statue spoke twice') end")]
    # D-71 item 5: after the boast the statue's click answers on the status bar (A3's else_text), no window
    s += click_status(ev('statue'), "The statue says nothing more. Alamar has had his say.")
    s += [adv(0.5, dialogs=True), lua("if close() then error('the statue click opened a window') end")]
    s += to_levers()
    # the levers, west then east; then the lever won't budge
    s += pull('west') + pull('east') + pull('west', False) + pull('east', False)
    s += levers_then_east()
    # the key box once, then "Nothing here."
    s += [walk(-1216, 720)]
    s += click_dialog(ev('keybox'), "The Key to the Dragon Tower.")
    s += [lua("close()"), check(f"has_item({KEY}) and qbit({gen.QBITS['key_box']})", "the key box gave no key")]
    s += [lua("remember('n', (#pack_items() + ((held() ~= nil and held() ~= 0) and 1 or 0)))")]
    s += click_status(ev('keybox'), "Nothing here.")
    s += [check("(#pack_items() + ((held() ~= nil and held() ~= 0) and 1 or 0)) == recall('n')", "the box gave something more")]
    # the warden's chest: the key line once, then the cushion line
    s += [walk(-1216, 1900), lua(f"open_door({ev('door_warden')}, {door('door:warden')})"), walk(-1216, 2400),
          {'clear_hostiles': {'radius': 4000}}, walk(-1700, 2816)]
    s += click_dialog(ev('chest_warden'), "a key of black stone", 0.8)
    s += [lua("for i = 1, 4 do if not close() then break end wait(0.3) end"),
          check(f"qbit({gen.QBITS['m39_darkstone_key']})", "darkstone_key 111780 not set"),
          lua(f"local before = gold(); loot_chest({ev('chest_warden')}); remember('gw', gold() - before)"),
          lua("for i = 1, 4 do if not close() then break end wait(0.3) end")]
    s += click_dialog(ev('chest_warden'), "An empty velvet cushion.", 0.8)
    s += [lua("for i = 1, 4 do if not close() then break end wait(0.3) end"),
          check("recall('gw') > 0", "the warden's chest gave no gold")]
    # the skull door with the Cube; still open after a reload
    s += [walk(-1216, 3250)]
    s += click_dialog(ev('skull_door'), "Access granted.")
    s += [lua("close()"), wait_door(door('door:skull'), 'open'),
          check(f"qbit({gen.QBITS['skull_door_open']})", "skull_door_open 117845 not set")]
    s += reload_() + [check(f"door_state({door('door:skull')}) == 'open'", "the skull door shut after a reload")]
    # the lift down, the vault pair
    s += [walk(-1216, 3700), walk(-1216, 3904, r=48), lua(f"click({ev('lift_head')}); wait(4)"),
          pos(-1216, 3904, 160, -790, -740),
          lua(f"open_door({ev('door_vault')}, {door('door:vault')})"),
          walk(-600, 3904, z=geo.LOW), {'clear_hostiles': {'radius': 4000}}, walk(-260, 3904, z=geo.LOW)]
    # the coffin: the field down, the lid open, 111781, the amulet; a reload; the empty line
    s += click_dialog(ev('coffin'), "The coffin's lid slides back", 0.8)
    s += [lua("for i = 1, 4 do if not close() then break end wait(0.3) end"),
          wait_door(door('mover:field'), 'open'), wait_door(door('mover:lid'), 'open'),
          check(f"qbit({gen.QBITS['m39_done']}) and has_item({AMULET})", "m39.roland's state")]
    s += reload_() + [check(f"door_state({door('mover:field')}) == 'open' and door_state({door('mover:lid')}) == 'open'",
                            "the field or the lid came back after a reload")]
    s += click_dialog(ev('coffin'), "An empty stasis coffin, still faintly cold.")
    s += [lua("close()")]
    # the stasis vault's chest
    s += [walk(96, 4600, z=geo.LOW),
          lua(f"local before = gold(); loot_chest({ev('chest_stasis')}); if gold() <= before then error('the stasis chest gave no gold') end")]
    # back up: the lift, then round to the pyramid nook and the assembly hall
    s += [walk(-600, 3904, z=geo.LOW), walk(-1216, 3904, z=geo.LOW, r=48), lua(f"click({ev('lift_foot')}); wait(4)"),
          pos(-1216, 3904, 160, -10, 30),
          walk(-1216, 3300), walk(-1216, 2400), walk(-1216, 1900), walk(-1700, 768), walk(-2240, 700),
          walk(-3200, 400), walk(-5000, 128), walk(-6000, 128), walk(-6400, 128),
          lua(f"local before = gold(); loot_chest({ev('chest_pyramid')}); if gold() <= before then error('the nook chest gave no gold') end")]
    s += click_dialog(ev('pyramid'), "Its light is out.")
    s += [lua("close()"), walk(-5632, 600), walk(-5632, 2700),
          lua(f"open_door({ev('door_works')}, {door('door:works')})"), walk(-5632, 3500),
          {'clear_hostiles': {'radius': 4000}}, walk(-5400, 4900),
          lua(f"local before = gold(); loot_chest({ev('chest_assembly')}); if gold() <= before then error('the assembly chest gave no gold') end"),
          lua("log('done: ' .. party())")]
    header('playtest.yml', """FD-01 Alamar Depths (L4), the critical path of M39 and Q-F1's key. A level-58 party with the Cube comes down D6's
stair (D6's thing:fd01_stair makes this move once A6 lifts DUNGEON['fd01']): entrance:d6_stair (0, 0, 0) facing 1024,
no line. The statue's boast as the party comes near (m39.statue, 117840), never again from the plate; the click then answers "The statue says nothing more." on the status bar (D-71 item 5). Round the
C to the lever hall: the west lever, then the east (each its status line, 117841/117842, its slab down), then "The
lever won't budge." from both. The sealed passage, the workshop, the east spur, the key vault: the box once (12376,
117844), then "Nothing here.". The warden's chest: the key line (111780), the gold, then the cushion line. The skull
door with the Cube ("Access granted.", 117845; open after a reload). The lift down, the pair, the coffin: the field
down, the lid open, 111781, the amulet 12372; a reload (both stay); the empty line. The four chests (stasis, nook,
assembly; the warden's above). The pyramid's line.""", 'xeen.fd01.l4.walk',
           'Alamar Depths (FD-01 L4): the D6 arrival, the statue, the levers west then east, the key box, the warden, the skull door, Roland and the four chests', s)


def levers_test():
    s = prologue()
    s += [lua("close()"), pose(-3456, 2496, 0, 90), {'clear_hostiles': {'radius': 9000}}]
    s += pull('east') + pull('west')
    s += reload_() + [check(f"door_state({door('door:slab_west')}) == 'open' and door_state({door('door:slab_east')}) == 'open'",
                            "a slab came back after a reload")] + thrown('west') + thrown('east')
    s += pull('east', False) + pull('west', False)
    # the pivot boss is the lever too (hover 'Lever'); the grip is a part of the arm's mover, so its click is the arm's
    for side in ('west', 'east'):
        for part in ('boss',):
            s += click_status(ev(f'lever_{side}_{part}'), "The lever won't budge.")
    s += [check(f"door_state({door('door:slab_west')}) == 'open' and door_state({door('door:slab_east')}) == 'open'",
                "a second pull moved a slab")]
    header('playtest_levers.yml', """FD-01's levers in the other order (D-69 change 10): east, then west, each its status line ("Far to the east, a wall
grinds down into the floor.", "Far to the west, ..."), its qbit (117842, 117841), its slab down and the lever thrown
(D-71 P2: the arm with its grip swung over to hang from the pivot); both slabs down and both levers thrown after a save and a reload; then "The lever won't budge."
from both, and from each lever's pivot boss, and nothing moves.""",
           'xeen.fd01.l4.levers', 'Alamar Depths (FD-01 L4): the levers east then west, a reload, then the lever won\'t budge', s)


def skull_test():
    s = prologue(cube=False)
    s += [lua("close()"), pose(-1216, 3250, 0, 90), {'clear_hostiles': {'radius': 9000}}]
    s += click_dialog(ev('skull_door'), "Access denied! You do not have the proper I.D.")
    s += [lua("close(); wait(2)"),
          check(f"door_state({door('door:skull')}) == 'closed' and not qbit({gen.QBITS['skull_door_open']})",
                "the skull door opened without the Cube")]
    header('playtest_skull.yml', """FD-01's skull door without the Cube: m39.skull_door's fail line "Access denied! You do not have the proper I.D."
(aaze0052:3) and the door stays shut (117845 clear).""",
           'xeen.fd01.l4.skull', 'Alamar Depths (FD-01 L4): the skull door without the Cube', s)


def grate_test():
    g = door('door:grate')
    s = prologue()
    s += [lua("close()"), pose(-3328, -512, 0, 90), {'clear_hostiles': {'radius': 9000}}]
    s += [lua(f"status(); click({ev('grate_bolted')}); wait(0.8)"),
          check("string.find(status(), 'Bolted from the other side.', 1, true)", "no bolted line from the gallery"),
          lua("wait(1)"), check(f"door_state({g}) == 'closed'", "the grate opened from the gallery side")]
    s += [pose(-3328, 400, 0, 270), {'clear_hostiles': {'radius': 9000}}]
    s += click_status(ev('grate_bolt'), "You draw the bolt.")
    s += [wait_door(g, 'open'), check(f"qbit({gen.QBITS['grate_bolt']})", "grate_bolt 117843 not set")]
    s += reload_() + [check(f"door_state({g}) == 'open'", "the grate shut after a reload")]
    s += [pose(-3328, -512, 0, 90), walk(-3328, -200, hostiles=0), walk(-3328, 400, hostiles=0),
          pos(-3328, 400, 96), lua("log('through the grate: ' .. party())")]
    header('playtest_grate.yml', """FD-01's bolted grate (D-69 change 4) from both sides: from the south gallery "Bolted from the other side."
(m39.grate_bolted) and the leaf stays shut; from the workshop "You draw the bolt." (m39.grate_bolt, 117843) and the
leaf rises; still open after a save and a reload; then the party walks through from the gallery side into the workshop.""",
           'xeen.fd01.l4.grate', 'Alamar Depths (FD-01 L4): the bolted grate from both sides', s)


def shaft_test():
    ax, ay = dress.ROOF_AT
    rx, ry, rz, rf = dress.D7
    s = prologue(start='xeen_d7.blv', to=(ax, ay, 0, 0))
    s += [pos(ax, ay, 64, -8, 8, 0),
          check(f"qbit({gen.QBITS['arrived_from_d7']})", "arrived_from_d7 117846 not set"),
          check("string.find(status(), 'You climb down through smoke and rubble', 1, true)", "no shaft arrival line"),
          lua("if close() then error('a window on the shaft arrival') end")]
    # a second arrival: no line
    s += [{'lua_event': {'source': f'evt.MoveToMap({rx}, {ry}, {rz}, {rf}, 0, 0, 0, 0, "xeen_d7.blv")'}},
          adv(2, follow=True), lua("close(); status()"), {'assert': {'map': 'xeen_d7.blv'}},
          {'lua_event': {'source': f'evt.MoveToMap({ax}, {ay}, 0, 0, 0, 0, 0, 0, "{MAP}")'}},
          adv(1.5, follow=True), {'assert': {'map': MAP}}, adv(1.5),
          check("not string.find(status(), 'smoke and rubble', 1, true)", "the arrival line came twice"),
          lua("if close() then error('a window on the second arrival') end")]
    # the ladder: No stays; Yes without roof_unlocked: bolted; with it: up to D7's entrance:fd01_roof
    # D-71 P1: the rails and the rungs ask too
    s += [{'clear_hostiles': {'radius': 9000}}]
    for part in ('ladder_rail_n', 'ladder_rail_s', 'ladder_rung_01', 'ladder_rung_16'):
        s += [lua(f"click({ev(part)}); wait(0.6)"), adv(0.5, dialogs=True), dialog("Bolted from above."),
              lua("close()"), adv(1.5, dialogs=True), {'assert': {'map': MAP}}]
    s += [lua(f"click({ev('ladder')}); wait(0.6)"), adv(0.5, dialogs=True), dialog("Bolted from above."),
          lua("close()"), adv(1.5, follow=True), {'assert': {'map': MAP}},
          {'lua_event': {'source': 'SetQBit(QBit(113521))'}},
          lua(f"click({ev('ladder')}); wait(0.6)"), adv(0.5, dialogs=True),
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'Close'}}, adv(1.5, dialogs=True), lua("close()"), {'assert': {'map': MAP}},
          lua(f"click({ev('ladder_rung_16')}); wait(0.6)"), adv(0.5, dialogs=True),
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'OK'}}, adv(2, follow=True), adv(1, follow=True), lua("close()"),
          {'assert': {'map': 'xeen_d7.blv'}}, pos(rx, ry, 160, facing=rf),
          lua("log('D7 entrance:fd01_roof: ' .. party())")]
    header('playtest_shaft.yml', """FD-01's rubble shaft (D-69 change 5): a party from D7 (D7's hatch makes this move: entrance:d7_roof at the shaft's
foot, facing 0) gets m39.shaft_arrival's status line once (117846) and none on a second arrival. The ladder (foot,
rails, rungs) without roof_unlocked (113521): "Bolted from above." and the party stays; with 113521 set, the standard
entrance window (F16): Close stays, OK moves the party to D7's entrance:fd01_roof (-18688, 8448, 1536) facing 1024.""",
           'xeen.fd01.l4.shaft', 'Alamar Depths (FD-01 L4): the D7 arrival line once, the ladder bolted, Close, then up to D7', s)


def exit_test():
    x, y, z, f = dress.D6
    s = prologue()
    s += [lua("close()"), {'clear_hostiles': {'radius': 9000}}, walk(600, 0, hostiles=0),
          walk(1340, 0, z=geo.STAIR_TOP, r=64, hostiles=0),
          lua(f"click({ev('exit_hatch')}); wait(0.5)"),
          {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
          {'select_topic': {'match_label': 'OK'}}, adv(1.5, follow=True),
          {'assert': {'map': 'xeen_d6.odm'}}, pos(x, y, 160, facing=f),
          lua("log('D6 entrance:fd01_stair: ' .. party())")]
    header('playtest_exit.yml', """FD-01's way out to D6: up the ruin stair to the hatch's underside, the exit preset's window (OK), D6 at
entrance:fd01_stair (-6656, 4608, 2208) facing 1536.""",
           'xeen.fd01.l4.exit', 'Alamar Depths (FD-01 L4): out by the stair to D6', s)


def in_test():
    d6 = yaml.safe_load((gen.R / 'devdocs/xeen/briefs/d6/L4/ids.lock.yml').read_text())
    stair = d6['events']['evt:thing:fd01_stair']
    s = [{'new_game_flow': {'start_map': 'xeen_d6.odm', 'party': PARTY}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}}, adv(2), lua("close()"),
         {'grant_item': {'item_id': CUBE}}, {'lua_event': {'source': 'SetQBit(QBit(111662))'}},
         {'lua_event': {'source': 'evt.MoveToMap(-6656, 4608, 2208, 1536, 0, 0, 0, 0, "xeen_d6.odm")'}},
         adv(2, dialogs=True, follow=True), lua("for i = 1, 3 do if not close() then break end wait(0.5) end"),
         {'assert': {'map': 'xeen_d6.odm'}},
         {'note': f"D6's thing:fd01_stair is D6's event {stair} (devdocs/xeen/briefs/d6/L4/ids.lock.yml); m39.depths_door "
                  "(the Cube), then the stair's entrance window (F16; D6's own walk test does the same), OK, and the move to "
                  "entrance:d6_stair."},
         # The window came with F16's entrance windows (the hatch's `screen:` text 5062); this test still closed it as a
         # stray dialog and stayed on D6 (xeen-fb4-dungeon6, 2026-11-25).
         lua(f"click({stair}); wait(0.5)"), adv(0.3),
         {'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}},
         {'select_topic': {'match_label': 'OK'}},
         adv(1.5, follow=True), adv(1, dialogs=True, follow=True),
         lua("for i = 1, 3 do if not close() then break end wait(0.5) end"),
         {'assert': {'map': MAP}}, pos(0, 0, 64, -8, 8, 1024), lua("log('entrance:d6_stair: ' .. party())")]
    header('playtest_in.yml', """The way in from D6 (live since A6's 08:39 D6 install): with the Cube and m33.done (111662, the ruin shown), D6's
thing:fd01_stair (its event number read from D6's ids.lock.yml when this file was written: rewrite it with
tools/tests.py after a D6 rebuild), m39.depths_door, the stair's entrance window (F16, OK), then FD-01's
entrance:d6_stair (0, 0, 0) facing 1024.""",
           'xeen.fd01.l4.in', 'Alamar Depths (FD-01 L4): in from D6 by the gatehouse stair', s)


def hostility_test():
    s = [{'new_game_flow': {'start_map': MAP, 'party': PARTY}},
         {'setup_shortcut': {'kind': 'immortal', 'value': True}}, adv(2), lua("close()"),
         {'assert': {'actor_count': {'monster_id': 11611, 'hostile': True, 'min': 28, 'max': 28}}},
         {'assert': {'actor_count': {'monster_id': 11612, 'hostile': True, 'min': 6, 'max': 6}}},
         {'assert': {'actor_count': {'monster_id': 11611, 'hostile': False, 'max': 0}}},
         {'assert': {'actor_count': {'monster_id': 11612, 'hostile': False, 'max': 0}}},
         {'note': "Both kinds spawned side by side in the workshop, nearer each other than the party: they must not take each other on."},
         pose(-5800, 400, 0, 0), {'console': {'line': 'arena trace on'}},
         {'spawn_actor': {'monster_id': 11611, 'x': -4300, 'y': 384, 'z': 0}},
         {'spawn_actor': {'monster_id': 11612, 'x': -4000, 'y': 384, 'z': 0}},
         {'spawn_actor': {'monster_id': 11611, 'x': -3700, 'y': 384, 'z': 0}},
         {'spawn_actor': {'monster_id': 11612, 'x': -3400, 'y': 384, 'z': 0}},
         adv(10),
         {'assert': {'ai_trace': {'event': 'target', 'target': 'actor', 'max_count': 0, 'report': True}}},
         {'console': {'line': 'arena trace off'}}]
    header('playtest_hostility.yml', """FD-01's robots (the XD-27 form): Annihilator 11611 (28) and Autobot 11612 (6), one faction, all hostile at load,
none peaceful; both kinds spawned side by side in the workshop do not take each other on.""",
           'xeen.fd01.l4.hostility', 'Alamar Depths (FD-01): the robots hostile, one faction, no infighting', s)


if __name__ == '__main__':
    main_test()
    levers_test()
    skull_test()
    grate_test()
    shaft_test()
    exit_test()
    in_test()
    hostility_test()
