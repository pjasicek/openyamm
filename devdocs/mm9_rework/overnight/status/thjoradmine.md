# thjoradmine status

- Phase: DONE (2026-10-31 ~01:45). README: level_generation/projects/mm9r_thjoradmine/README.md; props:
  level_generation/props/mm9_thjoradmine_claude/README.md.
- Faces 11 076, rooms 59 (60 sectors), portal faces 62 (59 archway cuts found by work/cuts/auto_cuts.py + 6 by hand,
  3 UserPortals), movers 71 (49 slide, 15 rotate, 7 dat), lights 257 (all BLV, none over 4 per point), decorations 371
  (rows 2338-2358 + 14 reused), chests 15, actors 93 (73 placed + 20 hidden spawns).
- Scenarios: doors_exits PASS, chests PASS, scripted PASS, machinery PASS (final BLV and bake).
- Brightness vs MM9 DAT lightmaps (calib_lightmaps.py, profile direct 1.05 / bounce 4 / ambient 0.5, BLV lights x
  BrightScale/0.75, model_lighting on): entrance 0.93, refinery 0.98, west halls 0.99, north-west 1.20, north tunnels
  1.13, cave-in/cavern 1.13, east mines 1.00, Ebora 1.25, abandoned 1.04; hue within 0.09 B/R. Capture (info only):
  lighting01 capture 27.7 / baked 27.3; v03 27.0 / 25.8. Views off >10 %: a01 0.64, a06 1.36, a08 1.25, a11 0.79, r05,
  r17, r20, r23, r40, r43, r46, r52. Bake current (stale_bakes --check does not list it).
- Reach: flooded cavern "cut off" FALSE (party and monsters climb the tunnel flights, work/reach/); board room REAL
  (72 LT fence MM9 jumps) -> invisible ramps, proven in and out.
- Unmatched scripted objects: Mine.scr (de-activated by TELP 1.3), ThjoradQuake/EarthQuake (no camera shake),
  EboraCam1 (no cutscene camera), miners' and NPCs' walks, mine cart ride (swap), falling torches' fall, steam jet,
  PerceptionLights, SpawnMgr respawn-on-death.
- Orchestrator follow-up (01:55): a07 was a bad pose (eye in the rock just off the flooded cavern), moved to the
  pool's rim, v04 tours + review/v04_compare.jpg; the cavern draws (25.7 vs capture 25.7). Model lighting vs old path
  measured on props (review/model_lighting_compare.jpg, work/model_lighting_props.txt): old path 0.32-1.39 of the
  capture (a black ore bin), model lighting 0.72-1.17; kept model_lighting: true (no capped lights here).
- Sheets: review/v04_compare.jpg (70 views), review/v03_compare.jpg, review/lighting01_compare.jpg (27 views, 3 columns), v01/v02 compares; all
  looked at.
- Not checked: desktop playthrough with real input (cave-in fall, the long climb out, barrel chain look), save/load
  mid-machinery, Thjorgard arrival, Hjarrand/Gudrek quest rows with Thjorgard keys, Android, flames of oil lamps in game.
- Blockers: none. Note for the orchestrator: tables.OLD_SIDECARS lacks `<stem>_authored.scene.yml` and
  `events/maps/<stem>_authored.lua` (Drangheim, Thjorgard, Boot Camp have them too); handled map-locally here.
