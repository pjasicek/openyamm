#!/usr/bin/env python3
"""XD-16 Volcano Cave: writes the L4 playtests from the built ids.lock.yml (run after level_generation/projects/xeen/xd16/cycle.sh).

  playtest.yml            the critical path: the devil skull, the rock still shut (its fail line), the demon skull
                          (q-c26.done) and the rock open in the same visit, the four lever stones and their slabs
                          (one-way), the gate run, the heart, the cool passage's line and the sealed end, a reload
  playtest_traps.yml      D-47 Q2: one trap chest (Fire damage once, then empty) and the real chest
  playtest_lava.yml       D-47 Q5: into each lava basin (the lake, both reaches of the river, the heart), burned, and
                          out again by its bank
  playtest_exit.yml       the way out to X7, its landing measured
  playtest_way.yml        the cool passage's end to XD-17's entrance:xd16_way and XD-17's way back
  playtest_hostility.yml  demons, devils and screamers hostile, no fights among them
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/xd16/L4')
ids = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
EV, DR, CH = ids['events'], ids['doors'], ids['containers']


def ev(name):
    return EV[f'evt:{name}']


def dr(name):
    return DR[f'door:{name}']


def ch(name):
    return CH[f'chest:{name}']


def party(immortal=True):
    s = """  - new_game_flow:
      start_map: xeen_xd16.blv
      party:
        gold: 0
        food: 20
        members:
          - {name: Brokk, class: Knight, level: 48, skills: [], equipment: {}}
          - {name: Hild, class: Cleric, level: 48, skills: [], equipment: {}}
          - {name: Ivar, class: Archer, level: 48, skills: [], equipment: {}}
          - {name: Sefa, class: Sorcerer, level: 48, skills: [], equipment: {}}
  - assert: {map: xeen_xd16.blv}"""
    if immortal:
        s += "\n  - setup_shortcut: {kind: immortal, value: true}"
    return s


def walk(x, y, z=0, r=64, clear=1500, t=40, ztol=None, dlg=False):
    zt = f", z_tolerance: {ztol}" if ztol else ""
    cl = f", clear_hostiles: {clear}" if clear else ""
    end = "close_dialogs: false, expect: dialog" if dlg else "close_dialogs: true"
    return f"  - walk_to: {{x: {x}, y: {y}, z: {z}{zt}, radius: {r}{cl}, timeout_seconds: {t}, {end}}}"


def lua(src):
    return f'  - play_lua: {{source: "{src}"}}'


def status_has(evt, text, what):
    return lua(f"click({evt}); wait(0.7); local s = status(); if not string.find(s, '{text}', 1, true) then "
               f"error('{what}: ' .. s) end; close()")


def status(text):
    return ("  - play_lua:\n      source: |\n        local s = tostring(status())\n"
            f"        if not string.find(s, [[{text}]], 1, true) then error(\"status line: \" .. s) end")


def dialog(text):
    return f'  - assert: {{dialog: {{active: true, text_contains: "{text}"}}}}'


def at(x, y, zmin, zmax, r=96):
    return f"  - assert: {{party_position: {{x: {x}, y: {y}, radius: {r}, z_min: {zmin}, z_max: {zmax}}}}}"


def tp(x, y, z):
    return f"  - console: {{line: tp {x} {y} {z}}}"


def health_all(h):
    return "\n".join(f"  - setup_shortcut: {{kind: set_member_points, member_index: {i}, health: {h}}}"
                     for i in range(4))


def health_assert(lo=None, hi=None):
    out = []
    for i in range(4):
        kw = []
        if lo is not None:
            kw.append(f"health_min: {lo}")
        if hi is not None:
            kw.append(f"health_max: {hi}")
        out.append(f"  - assert: {{member_points: {{member_index: {i}, {', '.join(kw)}}}}}")
    return "\n".join(out)


WAY = dr('way')
SLABS = [dr(f'slab_{n}') for n in range(1, 5)]

# --------------------------------------------------------------------------------------------------------------------
main = f"""# Playtest of the Volcano Cave (XD-16, L4; lane A7, agent:xeen-a7-xd16; written by
# output/studio_cal/xd16/tools/gen_tests.py from ids.lock.yml): the critical path (D-47's XD-16 playtests). A level-48
# party (immortal) starts in the mouth (entrance:x7_mouth): the arrival line, the way out's window (cancelled); the ash
# gallery and the fire lake; over the causeway to the island: the devil skull's question, Yes (A3's
# q-c26.devil_skull); the rock at the bottom still shut (q-c26.done unset, door closed, its click gives q-c26.way's
# fail line); round the north shore and up the fissure, the shrine's iron door, the demon skull: Yes (q-c26.done) and
# within two seconds the way's rock open (same visit); a second click on a broken altar gives the splinters line; the
# cinder run to the stair head, down the rough steps; the four lever stones (each slab down, a second click "The lever
# is down."); the gate run, the deep stair, the glass caves, the heart's west ledge, the last cave; through the rock,
# the cool passage's line (q-c26.way) up to its end (playtest_way.yml goes through). Then every window closed
# and a save and load: the rock and the four slabs stay open.
id: xeen.xd16.l4.walk
title: Volcano Cave (XD-16 L4), both skulls, the gate stones and the way
world: xeen
mode: faithful
steps:
{party()}
{at(256, 0, -8, 8)}
  - play_lua: {{source: "wait(2); local s = tostring(status()); log('arrive: ' .. s); if not string.find(s, 'Heat on your face', 1, true) then error('arrival line: ' .. s) end; close()"}}
  # The way out asks (playtest_exit.yml leaves by it); here Cancel stays.
{walk(128, 0, r=48, clear=0)}
  - play_lua: {{source: "click({ev('exit_x7')}); wait(0.5)"}}
{dialog("Do you wish to leave")}
  - play_lua: {{source: "close()"}}
  - assert: {{map: xeen_xd16.blv}}
  # The ash gallery, the fire lake, over the causeway to the devil skull.
{walk(1920, 0)}
{walk(3328, 0)}
  - clear_hostiles: {{radius: 3500}}
{walk(4200, 0, r=48)}
{walk(4480, 0, r=48)}
  - clear_hostiles: {{radius: 2000}}
  - play_lua: {{source: "click({ev('devil_skull')}); wait(0.5)"}}
{dialog("skull of a devil stares at you")}
  - answer_input: {{text: "yes"}}
  - advance_runtime: {{seconds: 1, present_dialogs: true}}
{status("cracks in two")}
  - play_lua:
      source: |
        close(); wait(1)
        if not qbit(112521) then error('devil_skull 112521 not set') end
        if qbit(112522) then error('q-c26.done set after one skull') end
        if door_state({WAY}) ~= 'closed' then error('the rock moved after one skull: ' .. door_state({WAY})) end
  # The rock, clicked after one skull: the fail line of q-c26.way.
  - play_lua: {{source: "click({ev('door_way')}); wait(0.7)"}}
{dialog("Bare rock, hot to the touch")}
  - play_lua: {{source: "close(); wait(1); if door_state({WAY}) ~= 'closed' then error('the rock opened before done') end"}}
  # The broken altar again: the splinters line.
  - play_lua: {{source: "click({ev('devil_skull')}); wait(0.7)"}}
{status("Splinters of black bone")}
  - play_lua: {{source: "close()"}}
  # Back over the causeway, the north shore, the fissure, the shrine's iron door.
{walk(3328, 0, r=64)}
{walk(3328, 1340)}
{walk(5568, 1340)}
{walk(5568, 2500)}
  - clear_hostiles: {{radius: 2500}}
{walk(5568, 3200, r=48)}
  - play_lua: {{source: "open_door({ev('door_shrine')}, {dr('shrine')})"}}
{walk(5568, 3800)}
  - clear_hostiles: {{radius: 2500}}
{walk(5696, 4160, r=48)}
  - play_lua: {{source: "click({ev('demon_skull')}); wait(0.5)"}}
{dialog("skull of a demon grins wickedly")}
  - answer_input: {{text: "yes"}}
  - advance_runtime: {{seconds: 1, present_dialogs: true}}
{status("rock grinds on rock")}
  - play_lua:
      source: |
        close(); wait(6)
        if not qbit(112520) then error('demon_skull 112520 not set') end
        if not qbit(112522) then error('q-c26.done 112522 not set by the second skull') end
        if not qbit(118054) then error('rock_drawn 118054 not set in the same visit') end
        if door_state({WAY}) ~= 'open' then error('the rock is not open in the same visit: ' .. door_state({WAY})) end
  # The cinder run back to the stair head; down the rough steps.
{walk(6464, 3150, r=64)}
{walk(6464, 900, t=60)}
{walk(6464, -1984, t=60)}
{walk(5760, -1984)}
{walk(5760, -2700, ztol=40)}
{walk(5760, -4900, -640, ztol=24, t=60)}
  - clear_hostiles: {{radius: 2500}}
  # The lever hall: the four lever stones round the pillar.
{walk(4900, -5120, -640)}
  - clear_hostiles: {{radius: 2500}}
"""
LEVER_STAND = [(4416, -4880), (4680, -5120), (4416, -5360), (4150, -5120)]
for n in range(1, 5):
    x, y = LEVER_STAND[n - 1]
    if n == 2:
        main += walk(4680, -4880, -640, r=48) + "\n"
    if n == 3:
        main += walk(4680, -5360, -640, r=48) + "\n"
    if n == 4:
        main += walk(4150, -5360, -640, r=48) + "\n"
    main += walk(x, y, -640, r=40) + "\n"
    main += f"""  - play_lua: {{source: "click({ev(f'lever_{n}')}); wait(0.7)"}}
{dialog("lever stone drops into its socket")}
  - play_lua:
      source: |
        close(); wait(5)
        if not qbit({118049 + n}) then error('slab_{n} {118049 + n} not set') end
        if door_state({SLABS[n - 1]}) ~= 'open' then error('slab {n} not down: ' .. door_state({SLABS[n - 1]})) end
  - play_lua: {{source: "click({ev(f'lever_{n}')}); wait(0.7)"}}
{dialog("The lever is down.")}
  - play_lua: {{source: "close()"}}
"""
main += f"""  # Down the gate run past the four lowered slabs, the deep stair, the landing.
{walk(4150, -4880, -640, r=48)}
{walk(4416, -6000, -640, r=64)}
{walk(4416, -6650, -640)}
{walk(4416, -7300, -640)}
{walk(4416, -7940, -640)}
{walk(4416, -8580, -640)}
{walk(4416, -9216, -640)}
  - clear_hostiles: {{radius: 2000}}
{walk(4416, -9700, -640, ztol=40)}
{walk(4416, -11900, -1280, ztol=24, t=60)}
{walk(4416, -12032, -1280)}
  - clear_hostiles: {{radius: 3000}}
  # The glass caves, the heart's west ledge, the last cave.
{walk(3700, -12096, -1280)}
{walk(2880, -12300, -1280)}
{walk(2880, -14144, -1280, t=60)}
  - clear_hostiles: {{radius: 3000}}
{walk(3744, -14144, -1280)}
  - clear_hostiles: {{radius: 3500}}
{walk(3744, -15350, -1280)}
{walk(4864, -15350, -1280)}
{walk(4864, -16300, -1280)}
{walk(4864, -16650, -1280, r=48)}
  # Through the rock: the cool passage's line (q-c26.way); its end leads straight into XD-17 (an indoor map: no
  # leave window), which playtest_way.yml walks; here the party stops short of it.
{walk(4864, -17150, -1280, r=64, clear=0, dlg=True)}
{dialog("Beyond the last cave, cool air")}
  - play_lua: {{source: "close()"}}
{walk(4864, -18250, -1280, r=48, clear=0)}
  - assert: {{map: xeen_xd16.blv}}
  # A save and load with every window closed: the rock and the slabs stay open.
  - play_lua: {{source: "close(); wait(1); close()"}}
  - reload: {{}}
  - play_lua:
      source: |
        wait(2); close()
        if door_state({WAY}) ~= 'open' then error('the rock after reload: ' .. door_state({WAY})) end
        for _, d in ipairs({{{', '.join(str(s) for s in SLABS)}}}) do
          if door_state(d) ~= 'open' then error('slab ' .. d .. ' after reload: ' .. door_state(d)) end
        end
"""

# --------------------------------------------------------------------------------------------------------------------
TRAP_X = 1760          # trap_1, the westmost chest
REAL_X = 1760 + 2 * 168
traps = f"""# Playtest of the Volcano Cave's vault of chests (XD-16, L4; written by output/studio_cal/xd16/tools/gen_tests.py):
# D-47 Q2. A level-48 party (not immortal: the damage is measured) walks to the vault; every member set to 100 HP (under every
# member's maximum); the westmost trap chest bursts ("The chest explodes!", Fire 50 on each member: each then 40-60),
# a second click "The chest is empty." with no more damage; the real chest (third from the west) opens on its loot.
id: xeen.xd16.l4.traps
title: Volcano Cave (XD-16 L4), a trap chest and the real chest
world: xeen
mode: faithful
steps:
{party(immortal=False)}
  - play_lua: {{source: "wait(2); close()"}}
{walk(1920, 0)}
{walk(2176, 0)}
{walk(2176, -900)}
  - clear_hostiles: {{radius: 2500}}
{walk(2176, -1300, r=48)}
  - play_lua: {{source: "open_door({ev('door_vault')}, {dr('vault')})"}}
{walk(2176, -1900)}
{walk(TRAP_X, -2150, r=40)}
  - clear_hostiles: {{radius: 4000}}
{health_all(100)}
  - play_lua: {{source: "click({ev('chest_trap_1')}); wait(0.7); local s = status(); if not string.find(s, 'The chest explodes!', 1, true) then error('trap: ' .. s) end; close(); if not qbit(118055) then error('trap_1 118055 not set') end"}}
{health_assert(40, 60)}
{health_all(100)}
{status_has(ev('chest_trap_1'), 'The chest is empty.', 'the burst chest again')}
{health_assert(100, 100)}
{walk(REAL_X, -2150, r=40)}
  - play_lua: {{source: "local g = gold(); loot_chest({ev('chest_vault_real')}); close(); if held() ~= 0 then stow() end; if gold() < g + 4000 then error('the real chest held no gold') end"}}
"""

# --------------------------------------------------------------------------------------------------------------------
# Each basin: (name, the shore point, a point in the lava, the way out (a bank), floor)
BASINS = [
    ('the lake (north reach)', (4864, 1400, 0), (4864, 760, -128), (4864, 1400, 0), 0),
    ('the lake (west reach, below the causeway)', (3250, 600, 0), (3900, 400, -128), (3250, 600, 0), 0),
    ('the river (north reach)', (2000, -4800, -640), (2496, -4800, -768), (2900, -4800, -640), -640),
    ('the river (south reach)', (2900, -5650, -640), (2496, -5650, -768), (2000, -5650, -640), -640),
    ('the heart', (3744, -14144, -1280), (4500, -14144, -1408), (4864, -12900, -1280), -1280),
]
lava = f"""# Playtest of the Volcano Cave's lava (XD-16, L4; written by output/studio_cal/xd16/tools/gen_tests.py): D-47 Q5. A
# level-48 party (not immortal: the burn is measured) is set on the shore of each lava basin (console tp), walks into the
# lava (it burns: every member set to 100 is under 100 a second later) and walks out by the basin's bank (the floor again, no more
# burning): the lake's north reach, the lake under the causeway, both reaches of the river, the heart.
id: xeen.xd16.l4.lava
title: Volcano Cave (XD-16 L4), into every lava basin and out again
world: xeen
mode: faithful
steps:
{party(immortal=False)}
  - play_lua: {{source: "wait(2); close()"}}
"""
for name, shore, inside, out, fz in BASINS:
    lava += f"""  - note: "{name}"
{tp(shore[0], shore[1], shore[2] + 8)}
  - clear_hostiles: {{radius: 6000}}
{walk(shore[0], shore[1], shore[2], r=64, clear=6000)}
{health_all(100)}
{walk(inside[0], inside[1], inside[2], r=64, clear=6000, ztol=24)}
  - play_lua: {{source: "wait(1)"}}
{at(inside[0], inside[1], inside[2] - 8, inside[2] + 8, r=160)}
{health_assert(1, 99)}
{walk(out[0], out[1], out[2], r=64, clear=6000, ztol=24)}
{at(out[0], out[1], fz - 8, fz + 8, r=120)}
{health_all(100)}
  - play_lua: {{source: "wait(3)"}}
{health_assert(100, 100)}
"""

# --------------------------------------------------------------------------------------------------------------------
exitt = f"""# Playtest of the Volcano Cave's way out (XD-16, L4; written by output/studio_cal/xd16/tools/gen_tests.py): the
# mouth (the exit preset) out to X7 at its named arrival entrance:xd16_mouth (512, 9728, 2240) facing west; the leave
# window's OK pressed; the landing measured with status().
id: xeen.xd16.l4.exit
title: Volcano Cave (XD-16 L4), the mouth out to X7
world: xeen
mode: faithful
steps:
{party()}
  - play_lua: {{source: "wait(3); close()"}}
{walk(128, 0, r=48, clear=0)}
  - execute_event: {{id: {ev('exit_x7')}}}
{dialog("Do you wish to leave")}
  - select_topic: {{match_label: "OK"}}
  - advance_runtime: {{seconds: 1.5, follow_map_move: true}}
  - assert: {{map: xeen_x7.odm}}
  - play_lua: {{source: "log('landing: ' .. status())"}}
  - advance_runtime: {{seconds: 2.0}}
  - play_lua: {{source: "log('landing after 2 s: ' .. status())"}}
  - assert: {{party_position: {{x: 512, y: 9728, radius: 160, z_min: 2200, z_max: 2300}}}}
"""

# --------------------------------------------------------------------------------------------------------------------
host = f"""# Hostility check of the Volcano Cave (XD-16, L4; written by output/studio_cal/xd16/tools/gen_tests.py): A2's demons
# (Demon 11630, Devil 11631, Screamer 11632) all hostile at load and after a save and load; side by side they do not
# fight each other and go for the party. No window is open before the reload.
id: xeen.xd16.l4.hostility
title: 'the Volcano Cave (XD-16): demons, devils and screamers hostile, no fights among them'
world: xeen
mode: faithful
steps:
{party()}
  - advance_runtime: {{seconds: 2}}
  - play_lua: {{source: "close()"}}
  - assert: {{actor_count: {{monster_id: 11630, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11631, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11632, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11630, hostile: true, min: 20}}}}
  - assert: {{actor_count: {{monster_id: 11631, hostile: true, min: 14}}}}
  - assert: {{actor_count: {{monster_id: 11632, hostile: true, min: 6}}}}
  - reload: {{}}
  - assert: {{actor_count: {{monster_id: 11630, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11631, hostile: true, min: 14}}}}
  - assert: {{actor_count: {{monster_id: 11632, hostile: true, min: 6}}}}
  - note: 'A Demon, a Devil and a Screamer side by side in the ash gallery, nearer each other than the party: they must
      not take each other on, and they go for the party.'
  - console: {{line: arena trace on}}
  - spawn_actor: {{monster_id: 11630, x: 1200, y: -160, z: 16}}
  - spawn_actor: {{monster_id: 11632, x: 1200, y: 160, z: 16}}
  - spawn_actor: {{monster_id: 11631, x: 1350, y: 0, z: 16}}
  - advance_runtime: {{seconds: 12}}
  - assert: {{ai_trace: {{event: target, target: actor, max_count: 0, report: true}}}}
  - assert: {{ai_trace: {{actor_index: last, event: target, target: party, min_count: 1}}}}
"""

way = f"""# Playtest of the cool passage's end (XD-16, L4; written by output/studio_cal/xd16/tools/gen_tests.py): with
# q-c26.done (112522), the passage's end (the exit preset; into an indoor map, so no leave window) to XD-17 at its
# named arrival entrance:xd16_way (-1280, -4736, 4) facing north; then XD-17's way back (its event 20,
# A5) to this map's entrance:xd17_way (4864, -18176, -1280).
id: xeen.xd16.l4.way
title: Volcano Cave (XD-16 L4), the cool passage to XD-17 and back
world: xeen
mode: faithful
steps:
{party()}
  - setup_shortcut: {{kind: set_qbit, id: 112522, value: true}}
  - play_lua: {{source: "wait(2); close()"}}
{tp(4864, -18176, -1280)}
  - advance_runtime: {{seconds: 1.0}}
  - play_lua: {{source: "close(); wait(0.3); close()"}}
{walk(4864, -18250, -1280, r=48, clear=0, dlg=True)}
  - play_lua: {{source: "close(); wait(0.3); close()"}}
{walk(4864, -18250, -1280, r=48, clear=0)}
  - execute_event: {{id: {ev('way_end')}}}
  - assert: {{dialog: {{active: true, action_label_present: "OK"}}}}
  - select_topic: {{match_label: "OK"}}
  - advance_runtime: {{seconds: 1.5, follow_map_move: true}}
  - assert: {{map: xeen_xd17.blv}}
  - play_lua: {{source: "log('landing: ' .. status())"}}
  - assert: {{party_position: {{x: -1280, y: -4736, radius: 160, z_min: -40, z_max: 60}}}}
  - advance_runtime: {{seconds: 1.0, present_dialogs: true}}
  - play_lua: {{source: "close(); wait(0.3); close()"}}
  - execute_event: {{id: 20}}
  # XD-17's way back is a BLV-to-BLV move with the leave window (picture 1, A5's rebuild on oymap MP40+): answer it.
  - assert: {{dialog: {{active: true, action_label_present: "OK"}}}}
  - select_topic: {{match_label: "OK"}}
  - advance_runtime: {{seconds: 1.5, follow_map_move: true}}
  - assert: {{map: xeen_xd16.blv}}
  - assert: {{party_position: {{x: 4864, y: -18176, radius: 160, z_min: -1320, z_max: -1240}}}}
  # The arrival line (daylight behind) speaks only in the mouth, not to a party back from XD-17.
  - play_lua: {{source: "wait(2.5); local s = tostring(status()); log('back: ' .. s); if string.find(s, 'Heat on your face', 1, true) then error('the mouth line in the cool passage') end"}}
"""

for name, text in (('playtest.yml', main), ('playtest_way.yml', way), ('playtest_traps.yml', traps), ('playtest_lava.yml', lava),
                   ('playtest_exit.yml', exitt), ('playtest_hostility.yml', host)):
    (L4 / name).write_text(text)
    yaml.safe_load(text)
print('written', 'playtest.yml playtest_way.yml playtest_traps.yml playtest_lava.yml playtest_exit.yml playtest_hostility.yml')
