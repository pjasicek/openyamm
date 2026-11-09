# klusoshouse — overnight status

- Phase: DONE (2026-10-30). Record: `level_generation/projects/mm9r_klusoshouse/README.md`; props:
  `level_generation/props/mm9_klusoshouse_claude/README.md`.
- Blockers: none. No engine change, no shared converter change (an opt-in try was reverted; Lich Lab `--plan`
  byte-identical before/after, converter lock released).

## Summary
- Faces 1716, rooms 10 (11 sectors), portal faces 13, movers 26 (13 rotating double doors), lights 36 BLV + 5
  bake-only, decorations 112, chests 1, actors 20 (19 Guard Captains, Count Kluso).
- Props: 21 models built and installed (rows 2239-2262 with 3 scale variants), 19 reused; fit median 0.54.
- Scenarios: doors_exits PASS (13 door groups by real clicks, shut door stops and opens, both exits), chests PASS,
  scripted PASS (letter by click; Blackheart by click: item 10029 + QBit 90223, hidden guards appear, a sleeper that
  ignored the party now targets it).
- Audit: 0 unreachable; 3 step edges = side of the upper stair flight over the lower; 8 actor notes (DAT placements).
- Lighting (second follow-up, 2026-10-30 night): **matched to the user's 4 real MM9 screenshots** (direct 0.75,
  ambient 1.188, max_lighting 1.4, sector minimum light 31). Real vs ours (central-crop luma): 1 corridor/guard (room 4,
  NE) 64.7 / 65.7 x1.02; 2 doorway (room 4, S) 47.6 / 48.0 x1.01; 3 dark room (master bedroom, SE) 37.0 / 35.4 x0.96;
  4 Count's room (great hall, SE) 92.4 / 82.2 x0.89 (MM9's crop holds the gold-clad Count; ours draws no actors).
  b/r real 0.55/0.64/0.67/0.50, ours 0.54/0.59/0.64/0.54. Lightmap luma ours/MM9 1.19-1.37 (warmer than the DAT
  lightmaps). Props vs walls: shot 3 MM9 cabinet/wall x1.11, ours x1.70 (our walls darker, cabinet x0.92 of MM9); the
  central room's chairs/wall x0.37 -> x0.49 with the sector-minimum-light 31 workaround. Reused cabinet04ns turned 90°
  (real shots show its front). Alternatives documented: lightmap-matched (0.35/0.72), capture-matched
  (`work/profile_capture_matched.yml`). Lighting views mean 49.2 (capture 93.4).
- Bake current (stale_bakes --check does not list klusoshouse).
- Unmatched scripted objects: KlusosPatrol.scr patrol paths (no native patrol; guards stand), its AlertOthers /
  GuardTrigger "charge" relay (native AI pursues on sight; aware2.wav not in our audio); PropAnim.scr "ns" idle loop on
  static furniture (nothing to carry).
- Sheets (looked at): `level_generation/projects/mm9r_klusoshouse/review/real_vs_real09.jpg` (real | ours),
  `review/lighting10_compare.jpg` (capture | lightmap-matched | installed), `review/v04_compare.jpg` (capture-matched bake),
  `review/lighting08_compare.jpg` (capture | unbaked | capture-matched | lightmap-matched), `review/lighting07_compare.jpg`, flames from the side `review/flames01/`.
- Scenarios rerun on the final build (map rebuilt for ambient 31 and the cabinet turn): all three PASS.
- Not checked: actors are not drawn in the review root (borrowed MM6 sprite atlases fail: "requires cooked schema 2";
  no MM9 3D models yet); desktop playthrough with real input; save/load after the theft; arrivals in Drangheim City;
  Android.
