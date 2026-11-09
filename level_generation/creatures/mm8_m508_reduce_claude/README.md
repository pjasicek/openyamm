# MM8 Air Elemental (`mm8_m508`, Lesser / Air / Greater Air Elemental) reduction (2026-10-19)

User: "OK do these ones" (MM8 reduction batch: m420, m416, m500, m508, m480). This follows the default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: UVs are kept, so the baked body map stays
valid. No Meshy credits. Scripts are copied from [mm8_m572_reduce_claude](../mm8_m572_reduce_claude/README.md)
(Phoenix: effect mesh kept with its own LODs, `swap_lod0.py` keeps other nodes' LOD meshes), `glb_close.py` from
[mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md) and `compact_glb.py` from
[mm8_ratman_reduce_claude](../mm8_ratman_reduce_claude/README.md).

Source: the installed `assets_source/worlds/mm8/models/mm8_m508.glb`, identical (sha1) to `mm8_m508_claude/export/`.
It is copied to `work/mm8_m508_source_pre_reduce.glb` (rollback source). Four skinned mesh nodes on one 64-joint rig:

| node | material | LOD0 | LOD1-3 | |
|---|---|---:|---|---|
| Body | `AirElemental_Body` (opaque, unlit, baked colour/AO) | 6,400 | 3,200 / 1,598 / 510 | **reduced** |
| Wind | `AirElemental_Wind` (blended, unlit, UV scroll 0.75/s) | 3,264 | 1,536 / 680 / 232 | unchanged |
| DeathCloud | `AirElemental_Wind` | 720 | 360 / 192 / 168 | unchanged |
| Lightning | `AirElemental_Lightning` (blended, double-sided) | 12 | 12 / 8 / 8 | unchanged |

The wind, dispersal and lightning are procedural effect meshes (`mm8_m508_claude/scripts/build_model.py`: ring strips
with 24 / 16 / 10 / 6 segments per LOD), and their face order is their draw order: shells are ordered
outer-to-inner inside and inner-to-outer outside. A decimation would reorder faces and change the UV repeats that set
each layer's scroll speed, so these meshes keep their accepted LOD chains byte for byte. Images, materials (unlit,
scroll), clips, sockets and the Dead hide are byte-identical as well.

## Ladder (body)

Blender's glTF importer turns each mesh node into an empty named like the node plus a mesh object `Body.001`.
`import_source.py`, `lod_check.py` and `build_lods.py` handle that. After the weld, the body is one closed surface
(7,514 -> 0 open edges, 3,202 vertices, no coincident vertices with other weights, no small pieces). It is split
into about 1,150 UV charts. Limits are scaled to 1.13 m, the body's height (p99 3.39 mm, max 16.95 mm).

| ladder | step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---|---:|---|---|---|---|
| uniform | 70 % | 4,480 | 1.95 / 14.14 | 0.995 | 0.9995 | pass |
| uniform | 55 % | 3,520 | 2.65 / 14.45 | 0.993 | 0.9989 | pass, face blocky |
| uniform | 50 % | 3,200 | 2.90 / 14.45 | 0.993 | 0.9986 | pass, face blocky |
| uniform | 45 % | 2,880 | 3.24 / 14.45 | 0.993 | 0.9982 | pass, face blocky |
| uniform | 40 % | 2,560 | 3.70 / 14.45 | 0.991 | 0.9977 | fail |
| head + neck kept (1,899 faces) | 55 % | 3,520 | 4.32 / 15.38 | 0.990 | 0.9971 | fail |
| head + neck at 80 % | 55 % | 3,520 | 3.42 / 14.45 | 0.993 | 0.9982 | fail |
| face kept (1,021) | 55 % | 3,520 | 3.26 / 14.45 | 0.993 | 0.9982 | pass, chin wedge |
| face at 75 %, chin to neck | 50 % | 3,200 | 3.41 / 14.45 | 0.992 | 0.9980 | fail (p99) |
| **face at 75 %, chin to neck (1,112)** | **55 %** | **3,520** | 2.98 / 14.45 | 0.993 | 0.9986 | **visual pick** |

The body is unlit: its shading, AO and muscle relief are baked into the 1K colour map, so a cut changes the
silhouette, and the baked shading is interpolated across larger triangles. The uniform steps pass every numeric
gate down to 45 %. On the face, though, the baked brow, eye-socket and jaw shading turns into flat facets
(`review/glbclose/` before the pick, `review/close/sheet_uni.png`). Protecting the whole Head group (head and neck,
30 % of the body) pushed the cut onto the torso and failed. The face alone (Head faces in front of the skull's centre,
`scripts/face_faces.py`, decimated on its own at 75 %) keeps the face. Stopping the protected region at the chin
smeared the dark under-chin shading up into a wedge, so the region runs down through the jaw to the front of the neck
(`review/close/sheet_face.png`, `sheet_face2.png`).

The 14.4 mm max is at the fingertips at the cast push (Attack frame 18) and on the bent left forearm (Attack 9, already
14.1 mm at 70 %); hands and fingers match in the close-ups (`sheet_uni.png`, `sheet_uni_b.png`, `review/glbclose/`).
Texture drift at the pick: 4 faces over 40, 2.7 cm². No face stretches over 20x in any clip, in the source or the pick
(`stretch_check.py`).

The source texture has black slivers at the eyelids, ear folds and mouth corners (UV corners on chart gutters). They
are already in the installed model. The uniform cut removed them; the kept face keeps them as in the source.

## Build

`export_cand.py` (`REA_CAND=Cand_55 REA_NODE=Body`, `work/ladder_f75b.blend`) -> `swap_lod0.py ... Body`
(`work/r55_lod0.glb`; other nodes keep their LOD meshes) -> `build_lods.py` in Blender (`tools/build_actor_lods.py`,
ratios 0.5 / 0.25 / 0.145, 4 influences) -> `shadow_chain.py` -> `compact_glb.py`: `export/mm8_m508.glb`, 4.1 MB
(installed 4.4 MB). `shadow_chain.py` restores the production design: the body's shadow uses the colour mesh one LOD
coarser (shadow LOD0-2 = colour LOD1-3), and the merged shadow meshes the LOD builder adds are dropped. No
`KHR_materials_variants` (the tiers differ only by scale), so `carry_variants.py` is not needed.

| | Body LOD0 | LOD1 | LOD2 | LOD3 | all meshes, LOD0 |
|---|---:|---:|---:|---:|---:|
| installed | 6,400 | 3,200 | 1,598 | 510 | 10,396 |
| reduced | 3,520 | 1,760 | 880 | 510 | 7,516 |

`work/lod_check_{src,r55}.json`: every body LOD keeps the source rest bounds (within 6 mm, head top 2.117-2.120 m),
the lowest point per clip is unchanged (0.76 m; the torso floats over the wind), and no face of any LOD stretches
over 20x in any clip. `check_winding.py`: 0 inverted closed parts (source 0). `review/lods/sheet.png`: the reduced
LOD3 keeps the face better than the installed LOD3, at the same 510 triangles. The native-height regression
(`mm8_air_elemental_actor_models_keep_sizes_wind_and_disappearance`, 204 px with 1 / 1.25 / 1.5) measures bounds
that include the unchanged wind.

`review/glbclose/sheet.png` (GLB-direct renders, the files' own normals; installed / reduced, textured and clay):
face front and three-quarter, chest, back, the cast hand with the lightning, whole figure with the wind and the
Death dispersal.

Viewer: `review/viewer/` (revision `reduce-1`: installed vs reduced for each tier, built by `scripts/viewer_tiers.py`
from the m508 project's viewer page and manifest, with a `NativeTierScale` root of 1 / 1.25 / 1.5 as that project
builds them, sha256 and `?v=` rewritten, manifest loaded with `cache: 'no-store'`).
`node level_generation/creatures/claude_shared/check_viewer.mjs http://127.0.0.1:8912/level_generation/creatures/mm8_m508_reduce_claude/review/viewer/`:
54 model/clip switches, no console errors (`review/viewer_shot.png`).

## Status

Installed 2026-10-19 (user: "air elemental ok"); winding 0, the regression passes and the row is in the ledger. Install: run `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py`
on the export, then `python3 tools/install_model.py
level_generation/creatures/mm8_m508_reduce_claude/export/mm8_m508.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_air_elemental_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_air_elemental_actor_models_keep_sizes_wind_and_disappearance`), and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). `actors.yml` needs no change. Rollback: install
`work/mm8_m508_source_pre_reduce.glb` the same way.

Reproduce: `REA_NODE=Body REA_GLB=<rollback source> blender -b -P scripts/import_source.py` ->
`REA_PROTECT=Head blender -b -P scripts/dump_mesh.py` -> `python3 scripts/face_faces.py 0 0` ->
`REA_PROTECT_FACES=work/face_faces.npy REA_PROTECT_RATIO=0.75 scripts/run_ladder.sh f75b 0.55,0.50` ->
`stretch_check.py`, `texture_drift.py r55`, `probe_max.py`, `close_ladder.py`, `close_sheet.py` -> build as above ->
`lod_check.py -- export/mm8_m508.glb r55`, `glb_close.py`, `viewer_tiers.py <rollback source> r100
export/mm8_m508.glb r55`.

## Floor fix — 2026-10-21

`--hover -0.079833 Death Dead`: the lowest living point was 0.08 m above the floor; every living clip is lowered so it meets it, eased out over Death. Only the MM8 export changes; `mm7_m508_claude` is untouched. Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to `export/mm8_m508.glb` (previous export in
`work/floor_fix_base/`) and installed; only animation samplers changed. The editable `.blend` master predates it:
rerun the same operation after any re-export.
