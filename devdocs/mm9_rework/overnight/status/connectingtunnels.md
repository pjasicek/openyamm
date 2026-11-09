# connectingtunnels status

- Phase: DONE (2026-10-31 ~03:15). README: level_generation/projects/mm9r_connectingtunnels/README.md
- Faces 4 254, rooms 31 (32 sectors), portal faces 32 (automatic tunnel cuts, work/cuts/tunnel_cuts.py), movers 4
  (coffin lids x2 rotate, rock fall x2 slide), BLV lights 76 (+7 capped fills bake-only, +8 LIGHTDEFS ice lights),
  decorations 119 (props project level_generation/props/mm9_connectingtunnels_claude, rows 2417-2434), chests 2,
  actors 38 (MM9 bodies; 12 draw untextured: missing MM9 art).
- Frame offset [17000, 0, 0] (DAT wider than int16); convert.py shifts transition rows (offset_transitions).
- Scenarios: doors_exits PASS (3 exits, rock fall by real click), chests PASS, scripted PASS (coffin lids by real
  click; grave chest locked until open, opened by its event: headless picking does not follow the lids).
- Audit: 0 unreachable, 0 pits; 3 actor notes false (in-game chase probes = control); flights walked (probes).
- Brightness: DAT lightmap zones ours/MM9 0.84-1.38 (tunnels 0.98-1.14; centre/NE high from the player-light stand-in);
  hue matched in tunnels via new opt-in bake key ambient_colour (MM9 AmbientLight 15/25/35); blue halls half as blue
  as MM9. Screen: capture 19.4 / baked 16.9, min baked view 13.0; 30 of 39 views >10 % off the capture (information
  only; list in README). Player-light stand-in: 13 rooms at sector level 14/17 (revert: ROOM_LEVELS = []).
- model_lighting: kept (compared both paths: old path draws crates/skeleton black).
- Unmatched scripted objects: none (no .scr in the DAT); AIRail/AmbientSound not built.
- Sheets: review/lighting_v02.jpg, review/v02_compare.jpg, review/v01_compare.jpg, review/model_lighting_compare.jpg.
- Not checked: desktop playthrough with real input, save/load, arrivals from Thronheim/Yorwick, candle flames in game.
- Shared changes: tools/lighting/bake_indoor.py `ambient_colour` (opt-in, default white); playbook lessons + table row;
  devdocs/INDOOR_BAKED_LIGHTING.md key documented.
