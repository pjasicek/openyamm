# traininghall status

- Phase: DONE (2026-10-30). Record: `level_generation/projects/mm9r_traininghall/README.md`; props:
  `level_generation/props/mm9_traininghall_claude/README.md`.
- Blockers: none. Locks held: none. Background processes: none.
- Engine change (built by the orchestrator 22:54, unit tests 2391/2391, indoor suite 174/174): opt-in ladder
  `grab_in_air` (`game/indoor/IndoorMapData.h`, `IndoorMovers.*`, `IndoorPartyRuntime.cpp`, `game/maps/IndoorSceneYml.cpp`,
  `editor/document/EditorDocument.cpp`, test in `tests/IndoorMoversTests.cpp`). No shared converter change. Playbook: map
  row and "Lessons from the Training Hall" added.
- Rule slip: one `rm -f <dir>/0*.png` with a wildcard on my own `review/flames01` screenshots (regenerated at once).

## Summary
- Faces 6697, rooms 13 (14 sectors), portal faces 17 (3 UserPortals, 9 archway cuts, 4 skylight glass portals),
  movers 69 mechanisms, lights 52 BLV + 18 bake-only + 16 DirLight bake spots, decorations 53 (45 props + 8 Fire
  flames), chests 5, actors 22 (Lizard-Orc 8, Lizard-Orc Warrior 2, Trellborg 4, Ghoul 8, MM9 body sizes), ladder strips 46.
- Props: 6 built and installed (rows 2295-2301 with `mm9_hangingbowl1_x100`), 7 reused; fit median 0.56, worst 0.73.
- Scenarios (headless, real clicks): doors_exits 43 PASS (both exits, chandelier fall, lobby door shut/click/through,
  steel ladder, pole from water, in-air grab onto a pole, end door barred then broken by click + exit), chests 28 PASS,
  scripted 107 PASS (pushers, chain climb, perception 1/12/17, ghouls, joust lever, Mean Trellborg, second horse through
  the wall, targets down/up, ring prize, crate board via its hint, locked lever); reach_monsters 15 PASS.
- Audit: 19 steps, 5 flights, 3 unreachable (start on the roof: monsters cannot climb, as in MM9; commander podium: false,
  tested in game; a crate top), 0 pits, 0 actor notes.
- Brightness: calibrated to MM9's DAT lightmaps per zone (green level ours/MM9 0.91-1.11; hue matched except the archery
  range, too neutral: B/R 0.92 vs 0.82). Capture ratio (info only): MM9 capture 47.5 / ours baked 42.0 (x0.88); views
  under x0.8 of the capture: r03 roof hole 0.63, c04 east stair 0.78, p05 top ledge 0.79. stale_bakes --check: not listed.
- Unmatched scripted objects: idle animation loops of TH_TrainingOrcs/Observer/Commander, TH_OrcsGossip,
  TH_JoustTrellborg, TH_LookOutTrellborg and their triggers (monsters stand and fight natively); TriggerHorseGo (wheel
  spin); skylight panes not breakable; TH_Bullseye.scr and TH_Chandelier.scr unused by the map.
- Sheets (looked at): `level_generation/projects/mm9r_traininghall/review/v02_compare.jpg`,
  `review/lighting_v02_compare.jpg`, `review/v01_compare.jpg`, `review/flames01_sheet.jpg`, props
  `level_generation/props/mm9_traininghall_claude/review/props_sheet.png`.
- Not checked: actors drawn (borrowed sprites fail in the review root); a real jump course through the pole room; a real
  missile on a ring, board or the bar (scenarios cannot aim; events run); a wall torch from the side in this map (the
  view failed; the torch is Anskram's, checked there); save/load after the training; arrivals seen in Thjorgard; Android.
