# dookscastle — overnight status

- Phase: DONE (2026-10-30 ~23:00). Record: `level_generation/projects/mm9r_dookscastle/README.md`; props:
  `level_generation/props/mm9_dookscastle_claude/README.md`. Playbook: table row + "Lessons from Dook's Castle".
- Blockers: none. No engine change, no shared converter change; no lock held, no background process.

## Summary
- Faces 4588, rooms 11 (12 sectors), portal faces 12, movers 16 (14 rotating door leaves, the secret sliding door,
  the button's invisible box), lights 156 BLV + 18 bake-only + 7 DirLights in the bake, decorations 96, chests 7
  (6 placed + TreasureChest6 on the lake bed by a dive pad), actors 47 (17 Half Orc Captains, 4 Half Orc Soldiers,
  Baron Dook with RUDE 415, 11 Trellborgs, 6 winged mutants, 6 basilisks, 2 King Basilisks).
- Props: 9 models built and installed (rows 2278-2294 incl. 8 scale variants), 20 reused; fit median 0.49.
- Lake: solid wading surface (Ocean4 frames, water shader colour 70/120/170, display emitter), 33 faces cut to the
  cavern; Ladder0 from the surface to the bridges; 3 invisible ramps over the rim's 40-48 LT rock steps.
- Scenarios: doors_exits PASS (gate exit, shut door stops/opens/walk through/auto-close, 7 doors by real clicks,
  ladder climb), chests PASS (6 by interact, dive pad), scripted PASS (friendly guards, 2 letters + Baron's RUDE
  dialogue by clicks, sleepers woken, both scurry boxes, shield -> secret door -> hostility, guard closes in),
  alarm PASS (damaging a guard -> all hostile).
- Audit: 0 unreachable, 0 pits (after ramps), steps/flights explained, 9 actor notes (4 false "ceiling" notes).
  Reach probes work/reach/: bridge->north landing, landing upper step, west planks->tunnel all climb.
- Brightness (calibrated to DAT lightmaps): castle zones ours/MM9 0.92-1.06, tunnels 1.62, north caves 1.29, lake
  zone 10 (MM9's lake zone is its unlit bed); capture ratio (info) 28.0 / 31.3 = 0.89, no view under 0.6x; views off
  >10 %: 24 listed in the README (castle rooms 0.68-0.88, the dark cave/lake views a few grey levels either way).
- Bake current (stale_bakes --check does not list dookscastle).
- Unmatched scripted objects: militia wander (BaseWander), sargent's walk to each sleeper and the sleepers' cower/
  fidget anims, basilisks' run to HideMarkers (vanish in place), BlockRude (nothing to block); NPC415 OnRude empty.
- Sheets (looked at): review/v03_compare.jpg, review/lighting01_compare.jpg, review/flames01/flames_sheet.jpg,
  review/v01_compare.jpg, props review/props_sheet.png.
- Not checked: actors are not drawn in the review root (borrowed sprite atlases "requires cooked schema 2"; only the
  winged mutants have MM9 3D models); desktop playthrough with real input (fight, bridges, ladder), save/load after the
  secret door, the arrival in Guberland, the Baron's quest rows with Markel's keys, Android.
