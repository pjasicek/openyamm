# lindisfarnemonastery — status

- Phase: DONE (2026-10-31). Engine change built by the orchestrator (00:45); all four scenarios PASS on it.
- Record: `level_generation/projects/mm9r_lindisfarnemonastery/README.md`; props:
  `level_generation/props/mm9_lindisfarnemonastery_claude/README.md`. Playbook row + lessons added.

## Summary
- Faces 13 766, rooms 7 (8 sectors), portal faces 13, movers 40 (10 rotate leaves, 25 organ keys, 5 bell ropes),
  ladders 7, lights 106 BLV + 20 bake-only + 264 DirLights, decorations 125, chests 0 (none in MM9), actors 27.
- Props: 11 models built, 8 reused, rows 2323-2337, fit median 0.52 (bells 25-37 vs the old bake's wrong pose).
- Scenarios: doors_exits PASS (exit, shut door stops, 8 door groups by click, 7 ladders climbed), quests PASS
  (RUDE by clicks: monk, abbot relic, Grehgknak letter + paladins, organist hymn, Robert at 5:00), immobile PASS (18),
  scripted PASS (letters, organ key, rope by real clicks; wrong/right bell order, key 9507, Thjorad monks at their
  prayer markers, Thjorad by a real click: item 197 + key 162; hurting a monk turns the others hostile).
- Audit: 190 steps, 2 flights, 1 unreachable 0.03 M (fountain basin in MM9's solid sound box), 0 actors cut off.
- Brightness (lightmap-matched, no real shot): ours/MM9 DAT lightmaps per zone 0.84-1.31; >10 % off: narthex x1.12,
  east tower x1.29, bell tower x1.31, hillside x1.13, east wing x0.84. Screen means capture 92.0 / unbaked 62.0 /
  baked 51.6. Props/wall 0.96-2.80 (no black props). Stale check: not listed.
- Unmatched: monk work/prayer animations, wandering paths, attached tools, bell swing + re-ring guard, book.scr
  animation, NPC voice lines, AmbientSounds, WeatherMan fog switching.
- Sheets (looked at): review/v03_compare.jpg, review/lighting_v03_compare.jpg, review/v02_compare.jpg.
- Engine change: IndoorWorldRuntime::setMapActorPosition (+ test in tests/IndoorActorFlyingRuntimeTests.cpp).
