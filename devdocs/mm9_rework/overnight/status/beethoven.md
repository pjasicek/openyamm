# beethoven — overnight status (re-light against MM9's DAT lightmaps)

- Phase: DONE (2026-10-30, re-light). Record: `level_generation/projects/mm9r_beethoven/README.md` ("Baked lighting").
- Blockers: none. No engine change, no shared converter change.

## What changed
- Profile `tools/lighting/baked_indoors/profiles/mm9_beethoven.yml`: direct 0.7, bounce 6, ambient 0.88, max_lighting 1,
  dirlights true (was direct 1.5, ambient 2.4, no ceiling). Full rebake through `bake_slot.sh` with the new map-local
  `bake.py` (MM9's 21 DirLights as spots instead of point lights; Light54 now in).
- Sector minimum light 20 -> 31 (`overrides.yml` map.ambient; Inventa Storca's fix for decorations drawn black in dark
  bakes). convert.py rerun: the BLV differs only in the 39 sectors' light byte; doors_exits, chests, scripted PASS.
- Old profile kept: `level_generation/projects/mm9r_beethoven/work/profile_capture_matched.yml`, its sidecar in
  `output/mm9_rework/bakes/beethoven_capture_matched/`.
- stale_bakes `--check` does not list beethoven.

## Brightness (lightmap luminance ours / MM9 DAT, per zone; before -> after)
sewers 4.79 -> 1.06, sewers west arm 5.41 -> 1.17, south arrival -> 1.24, catacombs 4.35 -> 0.97, baths 4.29 -> 0.92,
lower sewers 3.93 -> 0.82, lower storey east -> 0.92, south corridors -> 1.04, maze hall 4.42 -> 1.02, flooded cavern
-> 1.09. Hue matches in catacombs, maze, corridors, cavern; baths a little less blue (B/R 1.46 vs 1.78); lower sewers
too neutral (G/R 1.16 vs 1.43) and x0.82.
Screen (23 lighting views, centre-crop luma): capture 94.4, unbaked 30.4, old bake 79.0, new 21.5. South arrival 27 vs
the real MM9 YouTube frame 6.8 (location of that frame uncertain, its blacks crushed).

## Sheets (looked at)
`level_generation/projects/mm9r_beethoven/review/lighting_v05_compare.jpg`, `review/lighting_v05_p01-p04.jpg`
(MM9 capture | unbaked | old bake | lightmap bake). Decorations not darker than their walls; baths' water drawn
brighter than its room (liquid shader, not the lightmap).

## Not checked
- Where exactly the real MM9 frame was taken (none of the four starts clearly matches its "earthen slope").
- Desktop play with Torch Light in the new dark; actors' look (58 draw untextured anyway); the 78-view v04 review was not
  retaken with the new bake; walkability audit not rerun (geometry unchanged); Android.
- A map-local boost of the lower sewers' green lights (left at x0.82, too neutral).
