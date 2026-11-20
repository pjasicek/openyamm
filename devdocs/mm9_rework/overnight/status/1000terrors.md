# 1000terrors (Thousand Terrors) overnight status

- Phase: DONE (04:55). README: level_generation/projects/mm9r_1000terrors/README.md; props project
  level_generation/props/mm9_1000terrors_claude/.
- Faces 17 769, rooms 19 (+sector 0), portal faces 20, movers 121 (38 rotate, 83 dat), BLV lights 379 (+154 bake-only,
  81 DirLights), decorations 402 (117 translucent candle orbs as mm9_waterorb), chests 14, actors 114.
- Outline budget: estimate 6 299 (outlines.py, exact on Lindisfarne/Chasm); 1 867 small up-facing faces compiled
  invisible and redrawn at load.
- Scenarios: doors_exits PASS, chests PASS, scripted PASS (final build 10).
- Brightness: lightmap zones ours/MM9 x1.05-1.41 (ambient floor = player-light stand-in; 0.7 would give x0.74-1.13);
  screen: capture 19.5, baked 21.0; darkest baked view luma 10.7; 19 of 37 views >10 % off the capture (not a reference).
  model_lighting on (light_scale 1.2): the old path drew the skull head black.
- Shared converter change: tables.transitions_text starts from the current row (row 444 1000terrors <-> hallofthegods
  kept both halves; checked after the last install: 1000terrors.blv -> hallofthegods.blv). Lich Lab --plan identical.
- Unmatched: shooter marker flights, chess piece moves/queening, weighted lifts, gears, skull-head turn, flying-critter
  paths, cutscenes/cameras, EarthQuake, Lightning objects, AmbientSound, orb damage, genie smoke.
- Sheets: review/v02_compare.jpg, review/lighting01_compare.jpg, review/ml_new_compare.jpg, review/v01_compare.jpg.
- Not checked: lift ride with the party, combat, south-halls reach, desktop level change, save/load, sounds, Android;
  Pull2 / HiddenButton1 / Lever17 only by event in scenarios.
