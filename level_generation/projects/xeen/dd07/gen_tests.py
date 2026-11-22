#!/usr/bin/env python3
"""DD-07 Eastern Tower: writes the L4 playtests from the built ids.lock.yml (run after level_generation/projects/xeen/dd07/cycle.sh).

  playtest.yml            the critical path: up the stair to L3, the door of light and its two pylons, the vault's
                          jewel and the disk alcoves, up to the study (the letter, the two books, the chest), the
                          laboratory (the fountains, the vat), down on the floating disc, a save and load; then a
                          floating mage across the well engages the party at the third landing's window
  playtest_exit.yml       the way out to D3, its landing measured
  playtest_hostility.yml  the floating mages and the eyes hostile, no fights among them
  playtest_roof.yml       the roof stair (D-58): up to the trapdoor; shut before m30.done, then up to D7
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/dd07/L4')
ids = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
EV, DR, CH, MV, DS = ids['events'], ids['doors'], ids['containers'], ids['map_vars'], ids['destructibles']


def ev(name):
    return EV[f'evt:{name}']


def dr(name):
    return DR[f'door:{name}'] if f'door:{name}' in DR else DR[name]


def ch(name):
    return CH[f'chest:{name}']


PARTY = """  - new_game_flow:
      start_map: xeen_dd07.blv
      party:
        gold: 0
        food: 20
        members:
          - {name: Brokk, class: Knight, level: 36, skills: [], equipment: {}}
          - {name: Hild, class: Cleric, level: 36, skills: [], equipment: {}}
          - {name: Ivar, class: Archer, level: 36, skills: [], equipment: {}}
          - {name: Sefa, class: Sorcerer, level: 36, skills: [], equipment: {}}
  - assert: {map: xeen_dd07.blv}
  - setup_shortcut: {kind: immortal, value: true}"""


def walk(x, y, z=0, r=64, clear=1500, t=40, ztol=None, dlg=False):
    zt = f", z_tolerance: {ztol}" if ztol else ""
    cl = f", clear_hostiles: {clear}" if clear else ""
    end = "close_dialogs: false, expect: dialog" if dlg else "close_dialogs: true"
    return f"  - walk_to: {{x: {x}, y: {y}, z: {z}{zt}, radius: {r}{cl}, timeout_seconds: {t}, {end}}}"


def lua(src):
    return f'  - play_lua: {{source: "{src}"}}'


def says(evt, text, what, wait=0.8):
    """Click an event; its words show in a window or on the status line: either must hold `text`."""
    return lua(f"click({evt}); wait({wait}); local s = tostring(status()); if not string.find(s, '{text}', 1, true) "
               f"then error('{what}: ' .. s) end; close()")


def says_dialog(evt, text):
    return [lua(f"click({evt}); wait(0.8)"), f'  - assert: {{dialog: {{active: true, text_contains: "{text}"}}}}',
            lua("close()")]


def says_status(evt, text):
    """Click an event whose words go to the status line (F13): the status line must hold `text`."""
    return [lua(f"click({evt}); wait(0.8)"),
            "  - play_lua:\n      source: |\n        local s = tostring(status())\n"
            f"        if not string.find(s, [[{text}]], 1, true) then error(\"status line: \" .. s) end",
            lua("close()")]


def door(evt, d):
    return lua(f"open_door({evt}, {d})")


def playtest():
    s = [
        "# Playtest of the Eastern Tower (DD-07, L4; lane A7, agent:xeen-a7-dd07; written by",
        "# output/studio_cal/dd07/tools/gen_tests.py from ids.lock.yml): the critical path. A level-36 party (immortal)",
        "# starts in the door hall (entrance:d3_door): the arrival line, the way out's window (cancelled); up the first",
        "# and second stair halls to the third landing; the door of light (shut, its words), the conjury's and the",
        "# scrying room's ward pylons broken by a click each (the door fades); the vault's jewel (q-d18.jewel) and the",
        "# disk alcoves (q-d18.l3_disks); up the third stair to the top landing; the study: Ellinger's letter",
        "# (q-d18.letter), the Book of Fantastic Knowledge (+2 Intellect, then 'already fantastic'), the Book of Great",
        "# Power's final refusal, the chest; the laboratory: the Fountain of Minimal Abilities (then 'cool and",
        "# refreshing'), the Fountain of Life, the vat; out to the gallery under the cone and onto the floating disc, its",
        "# lever: the party rides it down the well to the foot; the foot's lever calls it back up; every window closed",
        "# and a save and load (the door of light stays gone). Then D-39's check: at the third landing's window a",
        "# Floating Adept spawned across the well, in the third gallery's east arm, takes the party on.",
        "id: xeen.dd07.l4.walk",
        "title: Eastern Tower (DD-07 L4), the stair, the pylons, the vault, the study, the disc down the well",
        "world: xeen",
        "mode: faithful",
        "steps:",
        PARTY,
        "  - assert: {party_position: {x: -2496, y: 0, radius: 64, z_min: -8, z_max: 8}}",
        lua("wait(2); log('arrive: ' .. tostring(status())); close()"),
        f"  - assert: {{state_dump_map_var: {{index: {MV['once.arrive']}, value: 1}}}}",
        "  # The way out asks (playtest_exit.yml leaves by it); here Cancel stays.",
        walk(-2660, 0, r=48, clear=0, t=20),
        lua(f"click({ev('exit')}); wait(0.5)"),
        '  - assert: {dialog: {active: true, text_contains: "Do you wish to leave"}}',
        lua("close()"),
        "  - assert: {map: xeen_dd07.blv}",
        "  # The first stair hall: its foot beside the door, twenty steps east to the second landing.",
        walk(-2624, -120, r=48, clear=0, t=20),
        walk(-2624, -520, r=48, clear=0, t=20),
        walk(-2690, -768, r=48, clear=0, t=20),
        walk(-1640, -768, 640, r=64, ztol=48, t=40),
        walk(-1472, -520, 640, r=64, t=20),
        walk(-1472, 0, 640, r=64, t=20),
        "  # The second stair hall: its foot at the east end, twenty steps west to the third landing.",
        walk(-1472, 480, 640, r=48, t=20),
        walk(-1300, 560, 640, r=48, t=20),
        walk(-1300, 704, 640, r=48, t=20),
        walk(-2360, 704, 1280, r=64, ztol=48, t=40),
        walk(-2496, 480, 1280, r=64, t=20),
        walk(-2496, 0, 1280, r=64, t=20),
        "  # Into the third gallery and round to the door of light: shut, its words explain both beams.",
        walk(-736, 0, 1280, r=64, t=30),
        walk(-736, 560, 1280, r=64, t=30),
        "  - clear_hostiles: {radius: 2500}",
        walk(700, 700, 1280, r=64, t=30),
        walk(800, 0, 1280, r=48, t=30),
        "  - clear_hostiles: {radius: 2500}",
        says(ev('ward'), 'Two beams feed it', 'the door of light before the pylons'),
        lua(f"if door_state({dr('ward')}) ~= 'closed' then error('ward: ' .. door_state({dr('ward')})) end"),
        "  # The conjury: the west pylon.",
        walk(700, 700, 1280, r=64, t=30),
        walk(-384, 820, 1280, r=48, t=30),
        door(ev('door_conjury'), dr('conjury')),
        walk(-384, 1220, 1280, r=64, t=30),
        "  - clear_hostiles: {radius: 2500}",
        f"  - console: {{line: destructible {DS['destructible:pylon_w']} state, expect_contains: standing}}",
        walk(-576, 1440, 1280, r=48, t=30),
        lua(f"click({ev('pylon_w')}); wait(2.5); local s = tostring(status()); if not string.find(s, 'west pylon "
            f"shatters', 1, true) then error('west pylon: ' .. s) end"),
        f"  - console: {{line: destructible {DS['destructible:pylon_w']} state, expect_contains: broken}}",
        f"  - assert: {{state_dump_map_var: {{index: {MV['pylons']}, value: 1}}}}",
        lua(f"if door_state({dr('ward')}) ~= 'closed' then error('ward after one pylon: ' .. door_state({dr('ward')})) "
            "end"),
        "  # Through the passage in the wall to the scrying room: the east pylon; the door of light fades.",
        walk(0, 1600, 1280, r=48, t=30),
        walk(500, 1600, 1280, r=48, t=30),
        "  - clear_hostiles: {radius: 2500}",
        walk(1472, 1440, 1280, r=48, t=30),
        lua(f"click({ev('pylon_e')}); wait(2.5); local s = tostring(status()); if not string.find(s, 'east pylon "
            f"shatters', 1, true) then error('east pylon: ' .. s) end"),
        f"  - assert: {{state_dump_map_var: {{index: {MV['pylons']}, value: 2}}}}",
        lua(f"wait(4); if door_state({dr('ward')}) ~= 'open' then error('ward after both pylons: ' .. "
            f"door_state({dr('ward')})) end"),
        lua(f"click({ev('ball_3')}); wait(0.5); close()"),
        "  # Back to the gallery and through the faded door: the jewel, the disks.",
        walk(640, 1220, 1280, r=48, t=30),
        door(ev('door_scrying'), dr('scrying')),
        walk(640, 800, 1280, r=48, t=30),
        walk(800, 0, 1280, r=48, t=30),
        walk(1250, 0, 1280, r=48, t=30),
        "  - clear_hostiles: {radius: 2500}",
        walk(1520, 0, 1280, r=48, t=30),
        "  # The Jewel of Ages lies on its stand as a ground item (D-90): picked up.",
        lua("if ground_items(12527) ~= 1 then error('the Jewel of Ages is not on its stand') end"),
        "  - pick_up: {item_id: 12527}",
        lua("if held() ~= 0 then stow() end; if not has_item(12527) then error('no Jewel of Ages') end"),
        walk(2250, 0, 1280, r=48, t=30),
        *says_status(ev('disks'), 'Two Energy Disks'),
        lua("if not qbit(113362) then error('tower_disks 113362') end; "
            "if held() ~= 0 then stow() end; if item_count(12334) < 2 then error('disks: ' .. item_count(12334)) end"),
        *says_status(ev('disks'), 'Loose wires'),
        "  # Back to the third landing and up the third stair to the top landing.",
        walk(1250, 0, 1280, r=48, t=30),
        walk(736, -620, 1280, r=64, t=30),
        walk(-736, -620, 1280, r=64, t=30),
        walk(-736, 0, 1280, r=64, t=30),
        walk(-2624, 0, 1280, r=64, t=40),
        walk(-2624, -520, 1280, r=48, t=20),
        walk(-2690, -768, 1280, r=48, t=20),
        walk(-1640, -768, 1920, r=64, ztol=48, t=40),
        walk(-1472, -520, 1920, r=64, t=20),
        walk(-1472, 0, 1920, r=64, t=20),
        "  # The study: the letter, the two books, the chest.",
        walk(-1920, 140, 1920, r=48, t=30),
        door(ev('door_study_landing'), dr('study_landing')),
        walk(-1920, 600, 1920, r=64, t=30),
        "  - clear_hostiles: {radius: 3000}",
        walk(-1920, 1180, 1920, r=48, t=30),
        lua(f"loot_chest({ev('letter')}); wait(0.5); local s = tostring(status()); "
            "if not string.find(s, 'sealed with Ellinger', 1, true) then error('letter: ' .. s) end; close()"),
        lua("if not qbit(113363) then error('letter_found 113363') end; "
            "if held() ~= 0 then stow() end; if not has_item(12361) then error('no letter') end"),
        walk(-2420, 1344, 1920, r=48, t=30),
        *says_status(ev('book_fantastic'), '+2 Intellect'),
        *says_status(ev('book_fantastic'), 'already fantastic'),
        walk(-2420, 896, 1920, r=48, t=30),
        *says_dialog(ev('book_power'), 'answers to no one living'),
        walk(-2560, 640, 1920, r=48, t=30),
        lua(f"local g = gold(); loot_chest({ev('chest_study')}); close(); if held() ~= 0 then stow() end; "
            "if gold() < g + 2400 then error('the study chest held no gold') end"),
        "  # The laboratory: the fountains, the vat.",
        walk(-1250, 1344, 1920, r=48, t=30),
        door(ev('door_study'), dr('study')),
        walk(-760, 1344, 1920, r=48, t=30),
        "  - clear_hostiles: {radius: 3000}",
        walk(-576, 1340, 1920, r=48, t=30),
        *says_status(ev('fountain_min'), 'statistics have increased'),
        *says_status(ev('fountain_min'), 'cool and refreshing'),
        walk(576, 1340, 1920, r=48, t=30),
        says(ev('fountain_life'), 'closes your wounds', 'the Fountain of Life'),
        walk(0, 1700, 1920, r=48, t=30),
        says(ev('vat'), 'Bubbling Vat', 'the vat'),
        "  # Out to the gallery under the cone and onto the floating disc; its lever sends it down the well.",
        walk(0, 1220, 1920, r=48, t=30),
        door(ev('door_lab'), dr('lab')),
        walk(0, 780, 1920, r=48, t=30),
        walk(700, 700, 1920, r=64, t=30),
        "  - clear_hostiles: {radius: 3000}",
        walk(700, 0, 1920, r=48, t=30),
        walk(270, 0, 1920, r=40, clear=0, t=30),
        "  - assert: {party_position: {x: 256, y: 0, radius: 120, z_min: 1900, z_max: 1940}}",
        lua(f"if door_state({dr('lift:disc')}) ~= 'open' then error('disc at load: ' .. door_state({dr('lift:disc')})) "
            "end"),
        lua(f"click({ev('disc_top')}); wait(12); log('after the ride: ' .. tostring(status()))"),
        "  - assert: {party_position: {x: 256, y: 0, radius: 160, z_min: -8, z_max: 40}}",
        f"  - assert: {{state_dump_map_var: {{index: {MV['disc_sent']}, value: 1}}}}",
        "  # At the foot: step off, the call lever brings the disc back up.",
        walk(-200, 0, 0, r=48, t=30),
        "  - clear_hostiles: {radius: 3000}",
        walk(380, 260, 0, r=48, clear=0, t=20),
        lua(f"click({ev('disc_foot')}); wait(10); if door_state({dr('lift:disc')}) ~= 'open' then "
            f"error('disc after the call: ' .. door_state({dr('lift:disc')})) end"),
        "  # Back to the door hall; every window closed, then a save and load: the door of light stays gone.",
        walk(-1200, 0, 0, r=64, t=40),
        lua("close()"),
        "  - reload: {}",
        lua(f"wait(1); if door_state({dr('ward')}) ~= 'open' then error('ward after the reload: ' .. "
            f"door_state({dr('ward')})) end; if held() ~= 0 then stow() end; if not has_item(12527) then error('the Jewel of Ages was lost') end"),
        "  # D-39: a floating mage across the well takes on the party at the third landing's window.",
        "  - console: {line: arena trace on}",
        "  - console: {line: actor kill 200000}",
        "  - set_pose: {map: xeen_dd07.blv, x: -640, y: 0, z: 1280, yaw_degrees: 0, pitch: 0}",
        "  - advance_runtime: {seconds: 1}",
        "  - spawn_actor: {monster_id: 11203, x: 736, y: 0, z: 1280}",
        "  - advance_runtime: {seconds: 20}",
        "  - assert: {ai_trace: {actor_index: last, event: target, target: party, min_count: 1}}",
        "  - assert: {ai_trace: {actor_index: last, decision: attack_ranged, target: party, min_count: 1, report: true}}",
        "  - assert: {combat_log: {taken_min: 1}}",
    ]
    return '\n'.join(s) + '\n'


def playtest_exit():
    s = [
        "# Playtest of the Eastern Tower's way out (DD-07, L4; written by output/studio_cal/dd07/tools/gen_tests.py):",
        "# the west door (the exit preset) out to D3 by its named arrival entrance:dd07_door (A5's (15360, 9216, 1888),",
        "# facing west); the leave window's OK pressed; the landing measured with status().",
        "id: xeen.dd07.l4.exit",
        "title: Eastern Tower (DD-07 L4), the west door out to D3",
        "world: xeen",
        "mode: faithful",
        "steps:",
        PARTY,
        lua("wait(3); close()"),
        walk(-2660, 0, r=48, clear=0, t=20),
        f"  - execute_event: {{id: {ev('exit')}}}",
        '  - assert: {dialog: {active: true, text_contains: "Do you wish to leave"}}',
        '  - select_topic: {match_label: "OK"}',
        "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
        "  - assert: {map: xeen_d3.odm}",
        lua("log('landing: ' .. status())"),
        "  - advance_runtime: {seconds: 2.0}",
        lua("log('landing after 2 s: ' .. status())"),
        "  - assert: {party_position: {x: 15360, y: 9216, radius: 160, z_min: 1860, z_max: 1920}}",
    ]
    return '\n'.join(s) + '\n'


def playtest_hostility():
    s = [
        "# Hostility check of the Eastern Tower (DD-07, L4; written by output/studio_cal/dd07/tools/gen_tests.py):",
        "# A2's floating mages (Floating Adept 11203, Floating Magus 11204, Mystic Mage 11200) and Floating Eyes",
        "# (11570) all hostile at load and after a save and load; side by side they do not fight each other and go for",
        "# the party. No window is open before the reload.",
        "id: xeen.dd07.l4.hostility",
        "title: 'the Eastern Tower (DD-07): floating mages and eyes hostile, no fights among them'",
        "world: xeen",
        "mode: faithful",
        "steps:",
        PARTY,
        "  - advance_runtime: {seconds: 2}",
        lua("close()"),
    ]
    counts = {11203: 15, 11204: 9, 11200: 4, 11570: 2}
    for m in counts:
        s.append(f"  - assert: {{actor_count: {{monster_id: {m}, hostile: false, max: 0}}}}")
    for m, n in counts.items():
        s.append(f"  - assert: {{actor_count: {{monster_id: {m}, hostile: true, min: {n}}}}}")
    s.append("  - reload: {}")
    for m in counts:
        s.append(f"  - assert: {{actor_count: {{monster_id: {m}, hostile: false, max: 0}}}}")
    s.append(f"  - assert: {{actor_count: {{monster_id: 11203, hostile: true, min: 15}}}}")
    s += [
        "  - note: 'A Floating Adept, a Floating Magus and a Floating Eye side by side in the door hall, nearer each other",
        "      than the party: they must not take each other on, and they go for the party.'",
        "  - console: {line: arena trace on}",
        "  - spawn_actor: {monster_id: 11203, x: -1600, y: -120, z: 16}",
        "  - spawn_actor: {monster_id: 11570, x: -1600, y: 120, z: 16}",
        "  - spawn_actor: {monster_id: 11204, x: -1500, y: 0, z: 16}",
        "  - advance_runtime: {seconds: 12}",
        "  - assert: {ai_trace: {event: target, target: actor, max_count: 0, report: true}}",
        "  - assert: {ai_trace: {actor_index: last, event: target, target: party, min_count: 1}}",
        "  - assert: {actor_count: {monster_id: 11570, hurt: true, max: 0}}",
    ]
    return '\n'.join(s) + '\n'


def playtest_roof():
    e = ev('roof_trapdoor')
    s = [
        "# Playtest of the Eastern Tower's roof stair (DD-07, L4; lane A7, seventeenth session, 2026-11-21, decider",
        "# D-58; written by output/studio_cal/dd07/tools/gen_tests.py from ids.lock.yml): the party is put in the top",
        "# gallery's south arm (1920), walks south into the roof stair, up its flight to the head (2,432) and under the",
        f"# roof trapdoor (event {e}, evt:roof_trapdoor, on platform:roof_hatch). Without m30.done (111600) A3's",
        "# d7.roof_dd07 answers 'The trapdoor is shut fast.' and the party stays; with it set the hook passes and the",
        "# game's entrance window asks (F16; was D-66's Yes/No): OK goes up to",
        "# D7's entrance:dd07_roof (27136, -6144, 1024) facing 1024, measured there.",
        "id: xeen.dd07.l4.roof",
        "title: Eastern Tower (DD-07 L4), the roof stair and its trapdoor (shut before M30, up to D7 after it)",
        "world: xeen",
        "mode: faithful",
        "steps:",
        PARTY,
        lua("wait(2); close()"),
        "  - set_pose: {map: xeen_dd07.blv, x: 0, y: -736, z: 1920, yaw_degrees: 270, pitch: 0}",
        "  - advance_runtime: {seconds: 1}",
        "  - assert: {party_position: {x: 0, y: -736, radius: 64, z_min: 1912, z_max: 1928}}",
        "  - clear_hostiles: {radius: 4000}",
        "  # Through the gallery's south wall into the roof stair, to the flight's foot, up it to the head, under the hatch.",
        walk(0, -1200, 1920, r=48, clear=0, t=20),
        walk(256, -1280, 1920, r=48, clear=0, t=20),
        walk(1150, -1280, 2432, r=48, clear=0, t=30),
        walk(1312, -1280, 2432, r=48, clear=0, t=20),
        "  - assert: {party_position: {x: 1312, y: -1280, radius: 80, z_min: 2424, z_max: 2440}}",
        lua(f"if qbit(111600) then error('m30.done (111600) is set at the start') end; click({e}); wait(0.5)"),
        '  - assert: {dialog: {active: true, text_contains: "The trapdoor is shut fast."}}',
        lua("close(); wait(0.7); local s = tostring(status()); if string.find(s, 'Not open yet', 1, true) then "
            "error('the sealed line showed before m30.done: ' .. s) end"),
        "  - assert: {dialog: {active: false}}",
        "  - assert: {map: xeen_dd07.blv}",
        "  # With m30.done the hook passes and the game's entrance window asks (F16, 2026-11-22: was D-66's Yes/No);",
        "  # OK goes up to D7's entrance:dd07_roof.",
        "  - setup_shortcut: {kind: set_qbit, id: 111600, value: true}",
        lua(f"click({e}); wait(0.5)"),
        "  - advance_runtime: {seconds: 0.5, present_dialogs: true}",
        '  - assert: {dialog: {active: true, action_label_present: "OK"}}',
        '  - select_topic: {match_label: "OK"}',
        "  - advance_runtime: {seconds: 1.5, follow_map_move: true}",
        "  - assert: {map: xeen_d7.blv}",
        "  - assert: {dialog: {active: false}}",
        lua("log('landing: ' .. status())"),
        "  - clear_hostiles: {radius: 6000}",
        "  - advance_runtime: {seconds: 4.0}",
        lua("log('landing after 4 s: ' .. status())"),
        "  - assert: {party_position: {x: 27136, y: -6144, radius: 160, z_min: 950, z_max: 1100}}",
    ]
    return '\n'.join(s) + '\n'


(L4 / 'playtest.yml').write_text(playtest())
(L4 / 'playtest_exit.yml').write_text(playtest_exit())
(L4 / 'playtest_hostility.yml').write_text(playtest_hostility())
(L4 / 'playtest_roof.yml').write_text(playtest_roof())
print('written playtest.yml, playtest_exit.yml, playtest_hostility.yml, playtest_roof.yml')
