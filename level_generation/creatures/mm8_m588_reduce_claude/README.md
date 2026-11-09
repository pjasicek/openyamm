# MM8 Malevolent Boulder (`m588`, Malevolent Boulder A/B/C) reduction (2026-10-19)

The user picked the boulder for a reduction batch. This project follows [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
and its MM8 batch lessons, on the no-retexture branch: textures, region ramps, clips, sockets and actor bindings are
unchanged. No Meshy credits.

The source is the installed `assets_source/worlds/mm8/models/mm8_m588.glb`, byte-identical to
`../mm8_m588_claude/export/mm8_m588.glb` and copied to `work/mm8_m588_source_pre_reduce.glb` (the rollback source).
It has one `Body` node with 34 bones, one opaque material and three tiers that share palette 588 and differ only in
scale. Every vertex has exactly one joint, and there are colour LODs 5,350 / 2,673 / 1,327 / 648 plus four shadow LODs
with the same geometry.

## Result: buried faces removed, no decimation

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed (colour = shadow) | 5,350 | 2,673 | 1,327 | 648 |
| export (colour = shadow) | **4,928** | 2,600 | 1,325 | 648 |

The boulder is **122 separate rigid stones** (median 44 triangles and about 25 vertices each, 0.15-0.89 m across). It
was already built lean, and only removing faces no camera can see passes the gates.

- **Decimation fails every gate.** Every collapse moves a stone surface by centimetres. The gate limits for a 2.0 m
  model are p99 6 mm and max 30 mm:

  | ladder | triangles | p99 / max mm | IoU | SSIM | |
  |---|---:|---|---|---|---|
  | all stones, teeth kept (`k20`) | 4,546 (85 %) | 21.8 / 31.0 | 0.9935 | 0.965 | fail |
  | | 4,012 (75 %) | 26.2 / 39.9 | 0.991 | 0.945 | fail |
  | | 2,942 (55 %) | 36.9 / 58.5 | 0.980 | 0.904 | fail |
  | only the 18 stones of 56+ faces (`big`) | 5,136 (96 %) | 18.1 / 31.0 | 0.9975 | 0.987 | fail |
  | | 4,814 (90 %) | 26.9 / 48.6 | 0.993 | 0.977 | fail |

  Only the image scores (IoU, SSIM) pass at 85 %. The surface error is real stone-shape change, not an offset: a 99.9 %
  near-identity run gives p99 0.0 mm. The fourteen mouth stones of 12-20 faces (the teeth) were kept exactly in
  every run.
- **Weights:** stones share texture space and overlap, so `uv_weights.py`'s UV lookup and nearest-vertex fallback gave
  vertices a neighbour's bone. That tore stones apart in Death (max 120 mm). `scripts/piece_weights.py` gives every
  output vertex its own stone's single bone, which brought the max down to 31 mm.
- **Buried faces:** `scripts/hidden_faces.py` (welded LOD0) and `scripts/cull_glb.py` (each LOD on its own geometry)
  find triangles inside another stone in every one of 125 sampled frames (every 2nd frame of all seven clips).
  - A triangle counts as buried when 10 points on it, and the same points 5 mm out along its normal, all have a
    generalized winding number above 0.5 for one closed stone.
  - Two cap stones at the back have small holes (30 open edges in all), so stones with open edges never count as
    enclosing. Before that rule, a few faces showing through their holes were removed (up to 11 pixels changed).
  - Posed positions come from per-bone rigid fits (Kabsch) to the source stones in each frame.
  - Removed: LOD0 422, LOD1 73, LOD2 2, LOD3 none. Each shadow LOD takes its colour LOD's cut, since it has
    identical positions and indices.
- **Export:** only those primitives get new index accessors, and the unused buffer data is compacted (9.03 -> 8.92 MB).
  Vertex buffers, normals, UVs, weights, materials, colour variants, region masks, images, nodes and every clip are
  byte-identical to the source.

## Checks

- **Pixels** (`scripts/render_compare.py`): tier-A viewer GLBs, every 3rd frame of every clip, six views (front,
  three-quarter, side, back, top, below), 516 images per model. The largest difference is 2/255 on at most 40
  pixels (rasterisation rounding); 141 images are identical. Summary: `work/pixel_compare.json`.
- **Tiers with the ramps applied** (`viewer_variants.py` bake, `scripts/tier_sheet.py`, `review/tiers/sheet.png`):
  installed vs culled tier A, then culled B and C, at rest and at the Attack gape, from four views. No dark streaks
  or flecks, and the tiers match. No texture fix is needed.
- **Normals:** splits only at UV seams. They are smooth but not the area-weighted default (median 6 deg off). Every
  normal is kept as installed.
- `check_winding.py`: 0 inverted closed parts, in both the source and the export.
- `lod_check.py` (REA_NODE=Body): bounds and lowest points match the source at every LOD, with no stretched faces.
  - Already in the installed model and not touched here: LOD1-3 dip 19 / 27 / 36 mm under the floor in some clip.
  - A LOD rebuild with floor locks could fix that, but rebuilding the angular far LODs fails the same gates.
- Viewer: installed vs culled per tier, opening on Attack.
  `python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m588_reduce_claude check`: 42
  switches, no console errors.

Viewer: http://127.0.0.1:8912/level_generation/creatures/mm8_m588_reduce_claude/review/viewer/

## Animation (unchanged; `../mm8_m604_reduce_claude/scripts/bone_velocity.py`)

Neither clip has a dead start: both move from the first key (backward anticipation).

- **Attack:** the bite snaps in. Peak bone speed goes from 8 deg/s at 0.88 s to 223 deg/s at 0.91 s and 380 deg/s
  at 0.94 s, just before the 1.0 s impact. The largest change from one viewer frame to the next is 215 deg/s, at
  0.875 s.
- **Cast:** a double pulse at the release: 203 deg/s at 0.97 s, down to 49, then 261 deg/s at 1.06 s.

No retime was made.

## Status

Installed 2026-10-19 (user: "boulder - ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_malevolent_boulder ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_malevolent_boulder_actor_models_keep_stone_motion_and_spells` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m588_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `REA_NODE=Body REA_GLB=level_generation/creatures/mm8_m588_reduce_claude/work/mm8_m588_source_pre_reduce.glb blender -b -P scripts/import_source.py`.
2. Dump the source data: `REA_PROTECT=Jaw blender -b -P scripts/dump_mesh.py`, `blender -b -P scripts/face_bones.py`,
   `blender -b -P scripts/dump_weights.py`.
3. `blender -b -P scripts/posed_verts.py`, then `python3 scripts/hidden_faces.py`.
4. `python3 scripts/cull_glb.py work/mm8_m588_source_pre_reduce.glb export/mm8_m588.glb`.
5. Viewer files: `viewer_variants.py work/mm8_m588_source_pre_reduce.glb r100` and
   `viewer_variants.py export/mm8_m588.glb cull`.
6. Checks: `render_compare.py -- src=...,cull=...`, `tier_sheet.py`, `lod_check.py`.
7. Ladders (evidence only): `REA_SMALL=20 small_pieces.py` (`work/keep.npy`), then
   `REA_INFLUENCES=1 REA_WEIGHTS=component REA_KEEP_FACES=work/keep.npy REA_HEIGHT_M=2.0 run_ladder.sh k20 0.85,0.75,0.65,0.55,0.45`,
   and the same with `REA_KEEP_FACES=work/keep_notbig.npy` as `big 0.96,0.95,0.93,0.90`.
