# thearena (overnight agent)

- Phase: DONE (2026-10-31)
- Faces 1 421 (1 222 native polygons), rooms 4 (+ sector 0), portal faces 4, movers 6 (2 rotate, 4 dat), lights 16
  (none capped), decorations 22, chests 0, actors 5 (NPCs: Arena Master RUDE 430, Byri 245, Sven's double 428, 2 clan
  soldiers), pads 0 (PlayerInTheHouse a polled box).
- Scenarios (all pass, real clicks): doors_exits, fight (Page), lord (key 214 -> 217), bout (bet), sven (keys 230/231).
- Arena: MM9's own arena logic (Arena.scr, ArenaFight.scr, ArenaCreature/Victory/Mini, PICKMON.inc) as map Lua; the
  shared ArenaRuntime (MM6-8 rules) not used, README "Why not ArenaRuntime".
- Brightness: lightmap ratios ours/MM9 hall x0.85, floor x1.16, pens x1.04/1.07, south stand x1.11, east stand x0.77,
  box x0.86 (off > 10 %: floor, east stand, box, hall); hue neutral as MM9. Screen means: capture 89.6, unbaked 101.1,
  baked 74.7 (capture information only). Pens luma 18.6 (MM9's dark, above the 10-12 floor).
- Unmatched scripted objects: PropAnim.scr (11 spectators, no models); WinCheer/LooseBoo relays replaced by a cheer sound.
- Sheets: level_generation/projects/mm9r_thearena/review/v04_compare.jpg, lighting_v04_compare.jpg, lighting_v04_detail.jpg
- Shared converter change: build.py glass-portal ring size (Lich Lab plan identical before/after); playbook lessons added.
- Not checked: fights beyond probes (Knight/Lord multi-opponent AI), sounds, counter-jumping, save mid-bout, models, x4.
