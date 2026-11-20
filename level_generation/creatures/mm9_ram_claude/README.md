# MM9 ram (mm9_ram) — 3D model, 2026-10-30

The MM9 ram (`mm9/extracted/MODELS/MODELS/RAM.abc`) for the Ram (MONSTERS.txt row 273: SHEEP2.dtx + RAMHORNBLACK.dtx).
**RAM.abc is SHEEP.abc plus horns:** body, ears and tail have identical vertices and UVs, the skeleton and bind matrices are
identical, and its only clip is a setup pose; it references `sheep.ABC` as a child model and plays that model's clips. So
this project reuses `../mm9_sheep_claude/` (mesh, weights, UVs, textures, role clips) and adds the horns.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_ram.glb` (cooked copy in `assets_dev`), skin `ram_a` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block `mm9_ram_claude`: MM9 273 Ram, scale 100 |
| Descriptor | NPC row in `tools/mm9_import_discovery/mm9_npc_actor_rows.tsv`, fallback visual zdog B (470) |
| Triangles LOD0/1/2/3 | 8,074 / 4,036 / 1,452 / 484 (body 6,370, horns 1,704) |
| Skeleton, clips, events, gait | the sheep's (see `../mm9_sheep_claude/README.md`) |
| Horns | rigid on `Xheadpiv` like MM9's `ramhorn` piece; own material `RamHorn`, 1K maps |
| Meshy credits | **0 / 30** |

## Route

- **Body:** `scripts/ram_export.py` opens the sheep's animated master. Its colours are tier `ram_a`: the sheep's shared
  textures and region mask with ramps fitted to SHEEP2.dtx (`textures/ram_ramps.json`, written by the sheep's
  `compose_sheep.py`): head near black, legs dark brown, wool cream. Eyes, hooves and the mouth are shared untouched.
- **Horns (no Meshy, no HD masters: no Meshy job):** `scripts/horn_geom.py` sweeps a rounded-triangle section along a
  Catmull-Rom centreline through MM9's ring centres, with MM9's radii, the base sunk 3.5 cm into the skull, so the horn
  keeps MM9's path and reads as a smooth curl (36 stations x 12 sides per horn). `scripts/compose_horn.py` builds the texture
  procedurally from the same (arc length, angle) map: a colour ramp sorted from RAMHORNBLACK.dtx's own texels, fine growth
  ridges spaced by the local radius, deeper yearly grooves, fibres, a paler tip; the normal map is the same height.
  Both horns share the layout (mirrored).

## Rebuild

```sh
# after the sheep's rebuild (it writes textures/ram_ramps.json and work/anim_v9.blend)
python3 scripts/compose_horn.py
scripts/rebuild.sh anim_v9.blend r10_ram                 # ram_export.py, runtime, viewer, check
python3 tools/install_model.py export/mm9_ram.glb --world mm9
flock -x ../claude_shared/locks/mm9_actors_yml.lock python3 scripts/bind_actors.py mm9_ram_claude work/actors_block.yml
```

## Symmetry and hooves (user review, 2026-10-30)

Shares the sheep's fix and measurements (`../mm9_sheep_claude/README.md`): the head-to-side look at Standing is MM9's `stand`
clip (head roll up to 8.6 deg, kept), the horns make it more visible; the hooves are straightened in the shared body.
Sheet: `review/symmetry_hooves_viewer.png` (viewer shots).

## Running fold fix (user review, 2026-10-30)

Shared body: see `../mm9_sheep_claude/README.md` for the fix and numbers. Sheet: `review/running_folds_viewer.png`.

## Checks (2026-10-30)

- Viewer `review/viewer/`: `run_creature_review.py check` 1 skin x 8 clips, 0 console errors; `review/playback/` every clip
  at 1x and 0.5x. Sheets from viewer shots: `review/acceptance_viewer_sheet.png`, `review/mm9_vs_ours_viewer.png`,
  `review/tiers_viewer.png`, `review/texture_closeup_viewer.png`.
- `texture_quality.py`: body as the sheep (atlas 60.1 %, spread 1.08, fragments 0 %, stretch 1.10). Horn: atlas 31.4 %, density
  723 (half the body's), spread 1.39, stretch p90 1.86: procedural strips of a tapering tube, not a Meshy paint, so the targets
  are not met there (see below).
- `flat_shading_check.py` 0.00 on body and horns. `detached_parts_audit.py` 3 components (body + 2 horns), 0 detached. Winding 0.
- Orientation, loops, deformation: the sheep's skeleton and clips (`review/orient.json`, `review/gates.json`, same numbers).
- Floor audit ok; regression `mm9_actor_models_build_every_binding` 61 descriptors on 28 models, 0 failed.
- No in-game run (optional in the brief).

## Deviations and open points

- The sheep's clip deviations apply (setup offsets removed).
- Horn texture density and stretch miss the Meshy-paint targets (the inner side of the tight curl compresses).
- Rigid horns sweep into the neck wool at the bottom of Hit and Fidget, as MM9's do; the ears sit inside the curl and can
  touch the horn when they flap, as in MM9.
- RAMHORN.dtx (the brown horn skin) is used by no row and is not built.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_ram_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_ram_reduce_claude/before/`.
