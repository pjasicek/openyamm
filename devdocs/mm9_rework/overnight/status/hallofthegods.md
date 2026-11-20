# hallofthegods status

- Phase: DONE (2026-10-31 ~04:30).
- Decision: fits the dungeon route (an open temple of real geometry inside MM9's 6-face skymarker box, over the
  Arslegaard sky box); only the end-game cinema (cameras) is beyond the engine and is carried as its outcome.
- Faces 2 164 compiled (1 905 native polygons), rooms 1 (+ sector 0), portal faces 0, movers 0, lights 34 BLV
  (+12 bake-only, 31 DirLights in the bake), decorations 41 (props project mm9_hallofthegods_claude, rows 2441-2451),
  chests 0, actors 10 (4 gods shown: Krohn 335, Skraelos 336, Fre 337, Great Honk 377; the cinema's 6 hidden), monsters 0.
- Scenarios: doors_exits PASS, scripted PASS, quests PASS, immobile PASS (final build). Compiler tests 21/21.
- Brightness (ours / MM9 DAT lightmaps): porch x0.80, west hall x1.00, stair x1.01, throne hall x1.23, dais x1.07;
  off by > 10 %: porch, throne hall (one room, one sector ambient). Hue neutral as MM9. Screen: capture 85.9, baked 76.2.
  Not stale (stale_bakes --check). model_lighting tried and rejected (statues darker than MM9).
- Unmatched: the cinema's cameras, letterbox, 13 voice lines, DoHighScore (engine win screen is MM8's); WinMan Part1
  routines; NPC336 six-fires scenes (Afterworld's); voices; ambient sound; dragons (MM9 ships no models).
- Sheets: level_generation/projects/mm9r_hallofthegods/review/v02_compare.jpg, lighting01_compare.jpg,
  model_lighting_compare.jpg.
- Shared row 1000terrors/444 verified (source 1000terrors.blv, destination hallofthegods.blv).
- Not checked: cinema on the desktop, arrivals by walking the neighbours' exits, Arslegard exit on the desktop,
  save/load, Android, statue LOD/collision.
