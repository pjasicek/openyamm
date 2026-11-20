# MM9 hireling rail: native captures (2026-11-06)

Engine-native screenshots of the rail of [revision 2](../README.md#revision-2-current-2026-11-06), as built in
phase 6 of `devdocs/mm9/MM9_HIRELINGS_PLAN.md`. Five-member party (`obsidian_curved_portraits_20260929/native/fixtures/
five.oysav`) in Sturmford City of the MM9 review root; hirelings added with the debug console's `hireling` command.

| Image | Content |
| --- | --- |
| `16x9_1.png`, `4x3_1.png` | Hrolf Spearmaster: buffed (medallion), 82 % HP, recovering (ring) |
| `16x9_2.png`, `4x3_2.png` | plus Arienh A'Klindor: 28 % HP (red), recovering |
| `16x9_3.png`, `4x3_3.png` | plus Forad Darre (the story slot): 55 % HP (amber) |
| `active.png` | a click on Arienh's face made her the acting combatant: the party's selection rim and diamond move to her; Forad is Unconscious (greyed, eyes-closed frame, unlit diamond) |
| `inspect.png` | held RMB on Hrolf: the members' popup with level, HP, AC 24 (row 21 + the fixture's party Stoneskin 3), condition, attacks, resistances 6 (the fixture's party school buffs 3 + Protection from Magic 3; row 0) and his Bless |
| `dialogue.png` | a second click on the active Arienh opens her RUDE dialogue (the debug `hireling add` sets her hire key, so Dismiss shows) |

The combat-log and followers buttons are hidden (MM9 world: `npcFollowers: false`, `combatLog: false`). The
interaction tour uses `--set controls.control_scheme=classic` (modern controls free the cursor only while RMB is held).

Compared with the study: the geometry is the study's (gameplay.yml `Mm9HirelingRail`, checked by
`tests/Mm9HirelingHudTests.cpp`). The HP arc follows the engine's arc convention, the one the party's arcs use: its
lower end stops at the aggro diamond, where the study's browser drawing ran on under the face. A recovering hireling
shows the members' unlit diamond with its recovery ring, as a recovering member does (the study drew a lit diamond).
The faces are the installed x2 `9npcNN` families, not the MM9 originals of the study.

Reproduce (tours in `tours/`, change `output_dir`):

```sh
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated hire --assets output/mm9_rework/assets_dev --world mm9 \
  --map sturmfordcity.blv --save level_generation/ui/obsidian_curved_portraits_20260929/native/fixtures/five.oysav \
  --warmup 0 --seconds 45 --set video.window_mode=windowed --set video.resolution=1920x1080 \
  --set debug.menu_input_tour_path=/absolute/path/to/tours/rail_3_16x9.yml
```
