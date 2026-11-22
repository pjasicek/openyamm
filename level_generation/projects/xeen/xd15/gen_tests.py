#!/usr/bin/env python3
"""XD-15 The Sphinx: writes the L4 playtests from the built ids.lock.yml (run after level_generation/projects/xeen/xd15/cycle.sh).

  playtest.yml            the critical path: up the throat, the riddle chamber, GOLUX, the legend throne and its
                          books, down to the King's, Queen's and Thieves' thrones, a save and load
  playtest_drop.yml       D-39 Q5: a wrong name, the drop, the clue walls, the library, the climb back by the dungeon
                          stair, the vault's Might Boosts and the great sarcophagus (Might 40)
  playtest_exit.yml       the way out to X6, its landing measured
  playtest_hostility.yml  golems and mummies hostile, no fights among them
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
from pathlib import Path

import yaml

L4 = Path(_REPO_ROOT + '/devdocs/xeen/briefs/xd15/L4')
ids = yaml.safe_load((L4 / 'ids.lock.yml').read_text())
EV, DR, CH, MV = ids['events'], ids['doors'], ids['containers'], ids['map_vars']


def ev(name):
    return EV[f'evt:{name}']


def dr(name):
    return DR[f'door:{name}']


def ch(name):
    return CH[f'chest:{name}']


PARTY = """  - new_game_flow:
      start_map: xeen_xd15.blv
      party:
        gold: 0
        food: 20
        members:
          - {name: Brokk, class: Knight, level: 31, skills: [], equipment: {}}
          - {name: Hild, class: Cleric, level: 31, skills: [], equipment: {}}
          - {name: Ivar, class: Archer, level: 31, skills: [], equipment: {}}
          - {name: Sefa, class: Sorcerer, level: 31, skills: [], equipment: {}}
  - assert: {map: xeen_xd15.blv}
  - setup_shortcut: {kind: immortal, value: true}"""


def walk(x, y, z=0, r=64, clear=1500, t=40, ztol=None, dlg=False):
    zt = f", z_tolerance: {ztol}" if ztol else ""
    cl = f", clear_hostiles: {clear}" if clear else ""
    end = "close_dialogs: false, expect: dialog" if dlg else "close_dialogs: true"
    return f"  - walk_to: {{x: {x}, y: {y}, z: {z}{zt}, radius: {r}{cl}, timeout_seconds: {t}, {end}}}"


def lua(src):
    return f'  - play_lua: {{source: "{src}"}}'


def expect(evt, text, what):
    return lua(f"click({evt}); wait(0.7); local s = status(); if not string.find(s, '{text}', 1, true) then "
               f"error('{what}: ' .. s) end; close()")


# Lines A3's hooks show on the status line (F13/D-89, 2026-11-22): checked there, not in a window.
STATUS_LINES = ("Sit where you like", "+2 Endurance", "sat here before", "+2 Might", "+2 Personality", "+2 Accuracy")


def dialog(text):
    if text in STATUS_LINES:
        return ("  - play_lua:\n      source: |\n        local s = tostring(status())\n"
                f"        if not string.find(s, [[{text}]], 1, true) then error(\"status line: \" .. s) end")
    return f'  - assert: {{dialog: {{active: true, text_contains: "{text}"}}}}'


# The way up to the head, from the paw hall (0, 1300).
UP = [walk(832, 1000), walk(832, 560, ztol=40), walk(832, -1700, 1280, ztol=48, t=60), walk(832, -2300, 1280),
      "  - clear_hostiles: {radius: 2000}"]

main = f"""# Playtest of the Sphinx (XD-15, L4; lane A7, agent:xeen-a7-xd15; written by output/studio_cal/xd15/tools/gen_tests.py
# from ids.lock.yml): the critical path. A level-31 party (immortal) starts in the breast gate (entrance:x6_paws): the
# arrival line, the way out's window (cancelled), the paw hall and its 'Stairs up.' sign; up the throat stair to the
# head; the west lappet's chest; the riddle chamber: A3's q-c9.riddle on entering, a plaque, the legend door still sealed;
# the sun disc: GOLUX (A3's q-c9.name_right: done 112181, the three throne doors open), stepping on it again ("Still
# me"); the throne of legends (+2 Endurance once, then "sat here before") and its two books (Starburst 421, Divine
# Intervention 487, once); back down to the belly hall: the King's throne behind the crown door, the Queen's behind the
# veil door, the loose panel and the Thieves' throne. Then every window closed and a save and load: the doors stay open.
id: xeen.xd15.l4.walk
title: The Sphinx (XD-15 L4), up the throat to the riddle, GOLUX and the four thrones
world: xeen
mode: faithful
steps:
{PARTY}
  - assert: {{party_position: {{x: 0, y: 256, radius: 64, z_min: -8, z_max: 8}}}}
  - play_lua: {{source: "wait(2); log('arrive: ' .. status()); close()"}}
  - assert: {{state_dump_map_var: {{index: {MV['once.arrive']}, value: 1}}}}
  # The way out asks (playtest_exit.yml leaves by it); here Cancel stays.
  - walk_to: {{x: -128, y: 120, z: 0, radius: 48, timeout_seconds: 20, close_dialogs: true}}
  - play_lua: {{source: "click({ev('exit_w')}); wait(0.5)"}}
  - assert: {{dialog: {{active: true, text_contains: "Do you wish to leave"}}}}
  - play_lua: {{source: "close()"}}
  - assert: {{map: xeen_xd15.blv}}
  # The paw hall and its sign.
{walk(0, 1300)}
  - clear_hostiles: {{radius: 2500}}
{walk(1152, 960, r=48)}
{expect(ev('sign_up'), 'Stairs up.', 'sign')}
  # Up the throat stair (40 steps, 1,280) to the neck landing.
""" + "\n".join(UP) + f"""
  # The west lappet: the priest's chest.
{walk(-64, -2496, 1280)}
  - clear_hostiles: {{radius: 2000}}
{walk(-256, -2752, 1280, r=48)}
  - play_lua: {{source: "local g = gold(); loot_chest({ev('chest_lappet')}); close(); if held() ~= 0 then stow() end; if gold() < g + 900 then error('the lappet chest held no gold') end"}}
  # The riddle chamber: A3's q-c9.riddle as the party comes in.
{walk(-64, -3200, 1280, clear=0)}
{walk(-64, -3650, 1280, clear=0, dlg=True)}
{dialog("What is my name?")}
  - play_lua: {{source: "close()"}}
  - assert: {{state_dump_map_var: {{index: {MV['once.riddle_voice']}, value: 1}}}}
  - clear_hostiles: {{radius: 3000}}
{walk(448, -3600, 1280, r=48, clear=0)}
  - play_lua: {{source: "click({ev('plaque_1')}); wait(0.5)"}}
{dialog("five letters long")}
  - play_lua: {{source: "close()"}}
{walk(-250, -4160, 1280, r=48, clear=0)}
{expect(ev('door_legend'), 'sealed door', 'legend door before the name')}
  - play_lua: {{source: "if door_state({dr('legend')}) ~= 'closed' then error('legend door: ' .. door_state({dr('legend')})) end"}}
  # The sun disc: GOLUX.
{walk(832, -3800, 1280, r=48, clear=0)}
{walk(832, -4160, 1288, r=48, clear=0, ztol=24, dlg=True)}
  - answer_input: {{text: "Golux"}}
  - advance_runtime: {{seconds: 2, present_dialogs: true}}
{dialog("Sit where you like")}
  - play_lua:
      source: |
        close(); wait(5)
        if not qbit(112181) then error('q-c9.done 112181 not set') end
        for _, d in ipairs({{{dr('king')}, {dr('queen')}, {dr('legend')}}}) do
          if door_state(d) ~= 'open' then error('throne door ' .. d .. ': ' .. door_state(d)) end
        end
  # Off the disc and on again: "Still me."
{walk(832, -3700, 1280, r=48, clear=0)}
{walk(832, -4160, 1288, r=48, clear=0, ztol=24, dlg=True)}
{dialog("Still me")}
  - play_lua: {{source: "close()"}}
  # The throne of legends and its books.
{walk(-250, -4160, 1280, r=48, clear=0)}
{walk(-1024, -4200, 1280, r=64, clear=0)}
  - play_lua: {{source: "click({ev('throne_legend')}); wait(0.7)"}}
{dialog("+2 Endurance")}
  - play_lua: {{source: "close(); click({ev('throne_legend')}); wait(0.7)"}}
{dialog("sat here before")}
  - play_lua: {{source: "close()"}}
{walk(-1344, -4250, 1280, r=48, clear=0)}
  - play_lua: {{source: "click({ev('book_heavens')}); wait(0.5); if held() ~= 0 then stow() end; if not has_item(421) then error('no Starburst book') end"}}
{walk(-704, -4250, 1280, r=48, clear=0)}
  - play_lua: {{source: "click({ev('book_sun')}); wait(0.5); if held() ~= 0 then stow() end; if not has_item(487) then error('no Divine Intervention book') end"}}
{expect(ev('book_sun'), 'bare', 'the second book click')}
  # Back down: the riddle chamber, the east lappet, the landing, the throat stair, the east gallery, the belly hall.
{walk(-250, -4160, 1280, clear=0)}
{walk(1728, -3650, 1280)}
{walk(1728, -2496, 1280)}
  - clear_hostiles: {{radius: 2000}}
{walk(832, -2300, 1280)}
{walk(832, -1700, 1280, ztol=48)}
{walk(832, 900, 0, t=60)}
{walk(832, 1100)}
{walk(1792, 1440)}
  - clear_hostiles: {{radius: 2500}}
{walk(1792, 2752)}
{walk(0, 2752)}
  - clear_hostiles: {{radius: 3500}}
  # The King's throne behind the crown door.
{walk(-1100, 4288, r=48)}
  - play_lua: {{source: "if door_state({dr('king')}) ~= 'open' then click({ev('door_king')}); wait(3) end"}}
{walk(-1900, 4288)}
  - play_lua: {{source: "click({ev('throne_king')}); wait(0.7)"}}
{dialog("+2 Might")}
  - play_lua: {{source: "close()"}}
  # The Queen's throne behind the veil door; the loose panel and the Thieves' throne.
{walk(-1100, 4288, clear=0)}
{walk(1100, 4288, r=48, clear=0)}
  - play_lua: {{source: "if door_state({dr('queen')}) ~= 'open' then click({ev('door_queen')}); wait(3) end"}}
{walk(1920, 4300, clear=0)}
  - play_lua: {{source: "click({ev('throne_queen')}); wait(0.7)"}}
{dialog("+2 Personality")}
  - play_lua: {{source: "close()"}}
{walk(2300, 4288, r=48, clear=0)}
  - play_lua: {{source: "click({ev('panel')}); wait(3); if door_state({dr('panel')}) ~= 'open' then error('loose panel: ' .. door_state({dr('panel')})) end"}}
{walk(2880, 4288, r=48, clear=0)}
  - play_lua: {{source: "click({ev('throne_thieves')}); wait(0.7)"}}
{dialog("+2 Accuracy")}
  - play_lua: {{source: "close(); wait(1); close()"}}
  # A save and load: the throne doors and the panel stay open, the name stays given.
  - reload: {{}}
  - play_lua: {{source: "wait(1); close()"}}
  - play_lua:
      source: |
        if not qbit(112181) then error('q-c9.done lost on reload') end
        for _, d in ipairs({{{dr('king')}, {dr('queen')}, {dr('legend')}, {dr('panel')}}}) do
          if door_state(d) ~= 'open' then error('door ' .. d .. ' after the reload: ' .. door_state(d)) end
        end
"""

drop = f"""# Playtest of the Sphinx's wrong name (XD-15, L4; lane A7; written by output/studio_cal/xd15/tools/gen_tests.py from
# ids.lock.yml), D-39 Q5: a level-31 party (immortal) goes up the throat to the riddle chamber and answers the sun disc
# wrongly: A3's q-c9.name_wrong, the disc sinks with the party on it, the party lands hurt in the drop cell (30 each),
# the disc rises again. The drop cell's first clue and its door (opened from inside, stays open); the east hall's two
# clues; the library (the fifth clue, A3's q-c9.hieroglyphs, the two gem finds, the chest); the west hall's clue; up the
# dungeon stair to the haunch vault: its sign and its chest's two Might Boosts (first opening only, map qbit 118010);
# the belly hall, the west gallery: the great sarcophagus refuses Might 15 and opens for Might 12 + a Might Boost (42).
id: xeen.xd15.l4.drop
title: The Sphinx (XD-15 L4), a wrong name, the drop, the clues and the climb back
world: xeen
mode: faithful
steps:
{PARTY}
  - play_lua: {{source: "wait(2); close()"}}
{walk(0, 1300)}
  - clear_hostiles: {{radius: 2500}}
""" + "\n".join(UP) + f"""
{walk(1728, -2496, 1280)}
  - clear_hostiles: {{radius: 2000}}
{walk(1900, -2752, 1280, r=48, clear=0)}
  - play_lua: {{source: "click({ev('offering')}); wait(0.5); if held() ~= 0 then stow() end; if not has_item(2061) then error('no emerald in the offering niche') end"}}
{walk(1728, -3200, 1280, clear=0)}
{walk(1728, -3650, 1280, clear=0, dlg=True)}
  - play_lua: {{source: "close()"}}
  - clear_hostiles: {{radius: 3000}}
  # The wrong name.
{walk(832, -3800, 1280, r=48, clear=0)}
{walk(832, -4160, 1288, r=48, clear=0, ztol=24, dlg=True)}
  - answer_input: {{text: "Sphinx"}}
  # Within a second the party is set on the disc's middle and the disc sinks with it (map var drop leaves 1); the
  # fall comes one timer tick (1 s) after that, so 0.8 s after the sink began the party is on the sunk disc.
  - play_lua: {{source: "for i = 1, 60 do if mapvar({MV['drop']}) ~= 1 then break end; wait(0.05) end; if mapvar({MV['drop']}) == 1 then error('the disc never sank') end"}}
  - advance_runtime: {{seconds: 0.8, follow_map_move: true}}
  - play_lua: {{source: "log('wrong name, on the sinking disc: ' .. status())"}}
  - assert: {{party_position: {{x: 832, y: -4160, radius: 200, z_min: 1080, z_max: 1250}}}}
  # Then the fall to the drop cell's sand heap and A3's words there.
  - advance_runtime: {{seconds: 3, present_dialogs: true, follow_map_move: true}}
{dialog("the floor agrees with it")}
  - play_lua: {{source: "close()"}}
  - advance_runtime: {{seconds: 4}}
  - play_lua: {{source: "log('after the drop: ' .. status()); if qbit(112181) then error('a wrong name set q-c9.done') end"}}
  - assert: {{party_position: {{x: 2688, y: 8640, radius: 160, z_min: -660, z_max: -560}}}}
  - assert: {{state_dump_map_var: {{index: {MV['drop']}, value: 0}}}}
  # The drop cell: the first clue, the door from inside.
{walk(2688, 8900, -640, r=64, clear=0)}
  - play_lua: {{source: "click({ev('clue_1')}); wait(0.5)"}}
{dialog("My first is in giant")}
  - play_lua: {{source: "close()"}}
{walk(2420, 8704, -640, r=48, clear=0)}
  - play_lua: {{source: "click({ev('door_drop')}); wait(3); if door_state({dr('drop')}) ~= 'open' then error('drop cell door: ' .. door_state({dr('drop')})) end"}}
  # The east hall's two clues.
{walk(1900, 8704, -640)}
  - clear_hostiles: {{radius: 3000}}
  - play_lua: {{source: "if door_state({dr('drop')}) ~= 'open' then error('the drop cell door closed again') end"}}
{walk(1088, 8450, -640, r=48)}
  - play_lua: {{source: "click({ev('clue_3')}); wait(0.5)"}}
{dialog("lich")}
  - play_lua: {{source: "close()"}}
{walk(1664, 8960, -640, r=48)}
  - play_lua: {{source: "click({ev('clue_4')}); wait(0.5)"}}
{dialog("Girard")}
  - play_lua: {{source: "close()"}}
  # The library.
{walk(640, 8900, -640)}
{walk(640, 9500, -640)}
  - clear_hostiles: {{radius: 3000}}
{walk(-1100, 10304, -640, r=64)}
  - play_lua: {{source: "click({ev('clue_5')}); wait(0.5)"}}
{dialog("XEEN but not in Queen")}
  - play_lua: {{source: "close()"}}
{walk(-64, 10380, -640, r=64)}
  - play_lua: {{source: "click({ev('hieroglyphs')}); wait(0.5)"}}
{dialog("My first is in giant but not in defiant. My second")}
  - play_lua: {{source: "close()"}}
{walk(-256, 10260, -640, r=48)}
  - play_lua: {{source: "click({ev('lectern')}); wait(0.5); if held() ~= 0 then stow() end; if not has_item(2063) then error('no sunstone on the lectern') end"}}
{walk(830, 9760, -640, r=48)}
  - play_lua: {{source: "click({ev('tablets')}); wait(0.5); if held() ~= 0 then stow() end; if not has_item(2065) then error('no sapphire behind the tablets') end"}}
{walk(960, 10420, -640, r=48)}
  - play_lua: {{source: "local g = gold(); loot_chest({ev('chest_library')}); close(); if held() ~= 0 then stow() end; if gold() < g + 1000 then error('the library chest held no gold') end"}}
  # The west hall's clue, through the library's door.
{walk(-704, 9350, -640, r=48)}
  - play_lua: {{source: "if door_state({dr('library')}) ~= 'open' then open_door({ev('door_library')}, {dr('library')}) end"}}
{walk(-704, 8900, -640)}
  - clear_hostiles: {{radius: 3000}}
{walk(-1600, 8950, -640, r=48)}
  - play_lua: {{source: "click({ev('clue_2')}); wait(0.5)"}}
{dialog("mole")}
  - play_lua: {{source: "close()"}}
  # The climb back: the stair foot, the dungeon stair, the haunch vault.
{walk(-320, 8600, -640)}
{walk(0, 7800, -640)}
  - clear_hostiles: {{radius: 2000}}
{walk(0, 5700, 0, t=60)}
  - clear_hostiles: {{radius: 2500}}
{walk(448, 6000, 0, r=48)}
{expect(ev('sign_down'), 'Stairs down.', 'sign down')}
  # The vault's chest: two Might Boosts on the first opening only.
{walk(0, 5900, 0, r=48)}
  - press_action: {{action: select_member, member_index: 3}}
  - play_lua:
      source: |
        if qbit({118010}) then error('vault_potions set before the chest was opened') end
        loot_chest({ev('chest_vault')})
        remember('vault_status', status())
  - press_action: {{action: select_member, member_index: 2}}
  - play_lua:
      source: |
        if held() ~= 0 then stow() end
        log('vault chest, first opening: ' .. recall('vault_status'))
        if item_count(240) ~= 2 then error('the vault chest gave ' .. item_count(240) .. ' Might Boosts') end
        if not qbit(118010) then error('vault_potions 118010 not set') end
        close(); wait(1)
        loot_chest({ev('chest_vault')}); if held() ~= 0 then stow() end
        if item_count(240) ~= 2 then error('the second opening gave ' .. item_count(240) .. ' Might Boosts') end
        close()
  # Through the haunch door to the belly hall and the west gallery's great sarcophagus.
{walk(0, 5350, 0, r=48)}
  - play_lua: {{source: "if door_state({dr('haunch')}) ~= 'open' then open_door({ev('door_haunch')}, {dr('haunch')}) end"}}
{walk(0, 4700)}
  - clear_hostiles: {{radius: 3500}}
{walk(-1150, 4288, r=48)}
{expect(ev('door_king'), 'crown', 'the crown door before the name')}
{walk(-1000, 2752)}
{walk(-1800, 2752)}
  - clear_hostiles: {{radius: 3000}}
{walk(-1800, 2112, r=48)}
  - press_action: {{action: select_member, member_index: 0}}
  - console: {{line: "lua SetValue(BaseMight, 15)", expect_contains: "Lua ran."}}
  - play_lua: {{source: "click({ev('chest_sarcophagus')}); wait(1)"}}
{dialog("You aren't strong enough to open the sarcophagus.")}
  - play_lua: {{source: "close()"}}
  - press_action: {{action: select_member, member_index: 3}}
  - console: {{line: "lua SetValue(BaseMight, 12)", expect_contains: "Lua ran."}}
  - use_item: {{item_id: 240, member_index: 3}}
  - play_lua: {{source: "log('Sefa after a Might Boost: ' .. party()); local g = gold(); loot_chest({ev('chest_sarcophagus')}); close(); if held() ~= 0 then stow() end; if gold() < g + 1500 then error('the great sarcophagus did not open for Might 42') end"}}
  # The galleries' plain sarcophagi.
{walk(-1800, 1280, r=64)}
{expect(ev('sarc_w1'), 'nothing in the sarcophagus', 'empty sarcophagus')}
  - play_lua: {{source: "close(); wait(1); close()"}}
  - reload: {{}}
  - play_lua: {{source: "wait(1); close(); if door_state({dr('drop')}) ~= 'open' then error('drop door after reload') end; if not qbit(118010) then error('vault_potions lost') end"}}
"""

exit_ = f"""# Playtest of the Sphinx's way out (XD-15, L4; written by output/studio_cal/xd15/tools/gen_tests.py): the breast
# gate's west leaf (the exit preset) out to X6 between the paws (A5's point (9216, 9728, 1408), facing south); the leave
# window's OK pressed; the landing measured with status().
id: xeen.xd15.l4.exit
title: The Sphinx (XD-15 L4), the breast gate out to X6
world: xeen
mode: faithful
steps:
{PARTY}
  - play_lua: {{source: "wait(3); close()"}}
  - walk_to: {{x: -128, y: 120, z: 0, radius: 48, timeout_seconds: 20, close_dialogs: true}}
  - execute_event: {{id: {ev('exit_w')}}}
  - assert: {{dialog: {{active: true, text_contains: "Do you wish to leave"}}}}
  - select_topic: {{match_label: "OK"}}
  - advance_runtime: {{seconds: 1.5, follow_map_move: true}}
  - assert: {{map: xeen_x6.odm}}
  - play_lua: {{source: "log('landing: ' .. status())"}}
  - advance_runtime: {{seconds: 2.0}}
  - play_lua: {{source: "log('landing after 2 s: ' .. status())"}}
  - assert: {{party_position: {{x: 9216, y: 9728, radius: 160, z_min: 1380, z_max: 1440}}}}
"""

host = f"""# Hostility check of the Sphinx (XD-15, L4; written by output/studio_cal/xd15/tools/gen_tests.py): A2's golems (Sand
# Golem 11590, Stone Golem 11581, Iron Golem 11582) and Tomb Mummies (11270) all hostile at load and after a save and
# load; side by side they do not fight each other and go for the party. No window is open before the reload.
id: xeen.xd15.l4.hostility
title: 'the Sphinx (XD-15): golems and mummies hostile, no fights among them'
world: xeen
mode: faithful
steps:
{PARTY}
  - advance_runtime: {{seconds: 2}}
  - play_lua: {{source: "close()"}}
  - assert: {{actor_count: {{monster_id: 11590, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11581, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11582, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11270, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11590, hostile: true, min: 16}}}}
  - assert: {{actor_count: {{monster_id: 11581, hostile: true, min: 18}}}}
  - assert: {{actor_count: {{monster_id: 11582, hostile: true, min: 4}}}}
  - assert: {{actor_count: {{monster_id: 11270, hostile: true, min: 7}}}}
  - reload: {{}}
  - assert: {{actor_count: {{monster_id: 11590, hostile: false, max: 0}}}}
  - assert: {{actor_count: {{monster_id: 11581, hostile: true, min: 18}}}}
  - assert: {{actor_count: {{monster_id: 11270, hostile: true, min: 7}}}}
  - note: 'A Sand Golem, a Stone Golem and a Tomb Mummy side by side in the breast gate, nearer each other than the party:
      they must not take each other on, and they go for the party.'
  - console: {{line: arena trace on}}
  - spawn_actor: {{monster_id: 11590, x: -256, y: 560, z: 16}}
  - spawn_actor: {{monster_id: 11270, x: 256, y: 560, z: 16}}
  - spawn_actor: {{monster_id: 11581, x: 0, y: 620, z: 16}}
  - advance_runtime: {{seconds: 12}}
  - assert: {{ai_trace: {{event: target, target: actor, max_count: 0, report: true}}}}
  - assert: {{ai_trace: {{actor_index: last, event: target, target: party, min_count: 1}}}}
  - assert: {{actor_count: {{monster_id: 11270, hurt: true, max: 0}}}}
"""

for name, text in (('playtest.yml', main), ('playtest_drop.yml', drop), ('playtest_exit.yml', exit_),
                   ('playtest_hostility.yml', host)):
    (L4 / name).write_text(text)
    yaml.safe_load(text)
print('written playtests')
