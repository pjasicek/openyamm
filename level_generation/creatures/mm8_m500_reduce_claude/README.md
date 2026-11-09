# MM8 Water Elemental (`m500`, Water Elemental A/B/C) reduction (2026-10-19)

User: "OK do these ones" (MM8 reduction batch: m420, m416, m500, m508, m480). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (UVs kept, so the shared atlas, three
palette materials and region ramps stay valid). No Meshy credits. Scripts copied from
[mm8_wolf_reduce_claude](../mm8_wolf_reduce_claude/README.md) (m492 coincident-vertex separation, exact source
weights), with `reduce_ladder.py`, `uv_weights.py` and `dump_weights.py` from
[mm8_m600_reduce_claude](../mm8_m600_reduce_claude/README.md) (parent-before-transform fix, skin weights through the
UVs) and `floor_contacts.py` from [mm8_m572_reduce_claude](../mm8_m572_reduce_claude/README.md).

Source: installed `assets_source/worlds/mm8/models/mm8_m500.glb`, identical (sha1) to `mm8_m500_claude/export/`;
copied to `work/mm8_m500_source_pre_reduce.glb` (rollback source). A solid scaled fish-serpent: no transparent,
emissive or effect meshes. One mesh node `Body` (head and body texture sets merged into one 2080x1024 atlas), materials
`WaterElemental_A/B/C` as `KHR_materials_variants`, 79 bones, 4 influences, sockets `Socket_Mouth`, `Socket_PalmL`,
`Socket_PalmR`, nine clips.

## Ladder

Weld 13,822 -> 148 open edges (unchanged by every step); no coincident vertices with other weights. Seven small head
pieces of up to 214 faces (eyes, teeth, lip and gill pieces; 728 faces) kept exactly (`REA_SMALL=220
small_pieces.py`). Limits scaled to the 2.0 m standing height (p99 6 mm, max 30 mm; the bound is 3.3 m long with the
tail).

| ladder | step | triangles | p99 / max mm | IoU min | SSIM | drift > 40 | |
|---|---|---:|---|---|---|---|---|
| uniform | 70 % | 7,370 | 2.98 / 37.82 | 0.998 | 0.994 | | fail (max, Dead) |
| uniform | 55 % | 5,790 | 5.53 / 31.18 | 0.993 | 0.991 | | fail (max) |
| uniform | 50 % | 5,264 | 6.38 / 33.72 | 0.991 | 0.989 | | fail |
| uniform | 45 % | 4,738 | 7.54 / 33.95 | 0.986 | 0.986 | | fail |
| fingers at 75 % (v2) | 55 % | 5,790 | 6.84 / 33.72 | 0.989 | 0.987 | | fail (worse) |
| error patches (v4) | 55 % | 5,790 | 4.79 / 15.71 | 0.994 | 0.991 | 7 faces, 68.5 cm2 | pass, pale chin |
| + drift lock, UV weights (v9) | 55 % | 5,790 | 5.07 / 26.36 | 0.994 | 0.991 | 3 faces, 3.8 cm2 | pass, pale chin |
| **+ jaw kept, error patches (v12)** | **55 %** | **5,790** | 5.30 / 15.71 | 0.993 | 0.990 | 7 faces, 35.7 cm2 | **picked** |
| v12 + drift lock (v13) | 55 % | 5,790 | 5.53 / 31.96 | 0.993 | 0.990 | 3 faces, 5.8 cm2 | fail (max) |

The uniform cut fails only on the maximum, at a few points where the tail coil presses against the lower body and in
the corpse's folds (`scripts/probe_max.py`); the 70 % step is worse there than 55 %, so the maximum is local, not
overall loss. `scripts/vertex_error.py` (largest distance of each source vertex to the candidate over every third
frame of every clip) finds those points; the faces within 4 cm of them are kept, plus the few large source faces
around one crease vertex whose blended spine/tail weights moved it 34 mm in Dead. Keeping the finger-weighted faces
as their own 75 % group pushed the cut elsewhere and raised p99, and the hands and webbed fingers of the uniform cut
already match the source in close-ups, so they stay in the shared cut. Skin weights of new vertices come through
the UVs (`REA_WEIGHTS=component`, `uv_weights.py`): the tail coil and body interpenetrate at rest.

GLB close-ups of v9 showed pale faceted triangles on the lower lip (the pale throat colour drifting up across the lip
UV seam), which the per-face drift check did not flag; the faces with a jaw weight over 0.3 (614) are kept exactly
since v10 (`review/glbclose/chin.png`, installed / reduced, clean). A drift-lock round on the final ladder (v13) moved
the maximum error back up to 32 mm, so v12 keeps its 7 drifted faces: four on the right side of the tail fins
(4-10 cm2 each, scale pattern shifted slightly), two at fingertips and one on the brow (1-2 cm2). No face stretches
over 20x its rest area in any frame of any clip (`stretch_check.py`, source and candidate 0).

Shading checked on GLBs imported directly with their own normals (`scripts/glb_close.py`): `review/glbclose/
sheet_tex.png`, `sheet_clay.png` (installed / reduced pairs: head front and side, open mouth, teeth, both hands, cast
pose, dorsal sail, tail fin, caudal fan, belly, back, whole body, corpse). Work-blend close-ups (clay, welded normals):
`review/close/sheet_uni_{a,b}.png`, `sheet_v9_{a,b}.png`. Ladder contact sheet: `review/ladder_sheet.png` (v12).

## Build

`export_cand.py` (`REA_CAND=Cand_55 REA_NODE=Body`, `work/ladder_v12_keep.blend`) -> `swap_lod0.py ... Body`
(`work/r55_lod0.glb`) -> `floor_contacts.py` -> `blender -b -P scripts/build_lods.py` (0.5 / 0.25 / 0.11, 4
influences, protected points: crown, outer hand tips, floor contacts) -> `shrink_shadow_lods.py` (the production
project's: shadow LOD1-3 tucked up to 15 mm inside) -> `carry_variants.py` -> `compact_glb.py`: `export/mm8_m500.glb`,
7.7 MB (installed 8.8 MB). Materials, variants (all 8 colour/shadow meshes), images, the 84 nodes with the three
sockets and the nine clip durations match the installed file.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,530 | 5,263 | 1,893 | 630 |
| reduced | 5,790 | 2,895 | 1,447 | 636 |

The production ratios (0.5 / 0.18 / 0.06) on the smaller LOD0 gave a blocky 346-triangle LOD3 that was also 5 cm lower
(crown), 13 cm narrower (hands) and 25 mm under the floor (installed LOD3: 23 mm under); the picking bounds and the
height regression use the posed model, so the crown, the outer hand tips and the floor contacts are protected points
and LOD3 keeps a budget like the installed one. `work/lod_check_{src,r55}.json`: every LOD keeps the source rest bounds
exactly (1.63 x 3.27 x 1.97 m; LOD3 tail tip within 3 mm), stays 4.3-4.6 mm above the floor in every clip (installed
LOD2 11.5 mm above, LOD3 23 mm below) and has no stretched faces. `review/lods/sheet.png`: installed and reduced LODs,
standing and at the attack release.

Viewer `review/viewer/` (revision `reduce-1`: installed vs reduced for each tier, each tier material's own ramps baked
into the atlas by `scripts/viewer_tiers.py`, LOD0 only; clips and native anchors from the production viewer):
`node level_generation/creatures/claude_shared/check_viewer.mjs
http://127.0.0.1:8912/level_generation/creatures/mm8_m500_reduce_claude/review/viewer/ 120`: 54 model/clip switches,
no console errors. `check_winding.py export/mm8_m500.glb`: 0 inverted closed parts.

## Cast and Attack v2 (user review)

User: "water elemental = some "proper" casting animation with 2 hands, attack can use the same one I guess." The
production Cast only nudged both hands forward at hip height (palm midpoint 0.37 m in front, 1.0 m high at the
release) and Attack flared the arms out to the sides; neither read as a two-handed spell (`review/cast_v2/`, top
rows).

`scripts/cast_v2.py` re-authors the clip on the production rig (`mm8_m500_claude/work/anim_uv_brow.blend`, read
only) with the production posing code (tail curve, trunk chain, two-bone arm IK in the chest frame, floor lift on
Root), sampled at 48 fps. Keyed states, eased with smoothstep:

| s | pose |
|---|---|
| 0 | Standing frame 0 (bones within 0.005 of it) |
| 0.50 | gather: both hands in front of the chest, palms facing each other, fingers curled, trunk leaning back, head up |
| 0.68 | charge: hands a little closer and lower, deeper lean back |
| 0.875 | release: both palms thrust forward together at shoulder height, fingers spread and pointing up, trunk and head lean in, jaw open, tail coil braced |
| 1.0 | hold |
| 1.375 | Standing frame 0 |

The palm orientation is solved per frame (palm normal = the flattest axis of the vertices weighted to the hand and
its digits; the digit bones' own axes are not consistent between digits), the fingers curl and fan about axes built
from it, and the arms keep their bone lengths. `scripts/graft_cast.py` puts the clip into both Cast and Attack of the
export (joints matched by name, rest TRS asserted equal, Blender's one-frame offset removed), then `compact_glb.py`.
Length 1.375 s and impact 0.875 s are unchanged, so `actors.yml` (Attack for melee/ranged, Cast for spells, palm glow,
impact) needs no change. The pre-graft export is `work/mm8_m500_r55_cast_v1.glb`.

Checks: palm sockets at 0.875 s are L (0.094, -0.702, 1.329), R (-0.102, -0.719, 1.326) m (Blender axes, -Y forward),
midpoint (0, -0.71, 1.33): 0.71 m in front at shoulder height, symmetric within 2 cm (the projectile leaves this
midpoint; `mm8_water_elemental_actor_models_keep_tiers_and_palm_cast` compares the projectile origin with it).
Edge stretch over the clip p99 1.44 / max 3.2 (production Cast 1.38 / 3.9, Attack 1.41 / 4.2); floor lift 0.04 m as in
every production clip (`work/cast_v2.json`). `work/lod_check_r55_cast2.json`: no stretched faces at any LOD in any
clip, Cast and Attack lowest point 0.0 mm (not below the floor), other clips, bounds, materials and nodes identical
to the pre-graft file (the other seven clips byte-identical). Winding 0. Filmstrips `review/cast_v2/{Cast,Attack}_
{front,side,close}.png` (previous / new at 48 fps frames 0-66; the release is frame 42). Viewer
`review/viewer_cast/` (revision `reduce-2-cast`; the installed r100 models keep the old clips for comparison):
`check_viewer.mjs`: 54 switches, no console errors.

## Status

Installed 2026-10-19 (user: "water elemental ok", with the v2 Cast/Attack); winding 0, the regression below passes and the
row is in the ledger. Install:
`python3 tools/install_model.py level_generation/creatures/mm8_m500_reduce_claude/export/mm8_m500.glb --world mm8`,
then `OPENYAMM_REGRESSION_FILTER=mm8_water_elemental_actor_models ./build/game/openyamm
--headless-run-regression-suite actors` (`mm8_water_elemental_actor_models_keep_tiers_and_palm_cast`: tier heights
within 3 units, LOD chain, palm sockets, clip durations) and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). `actors.yml` needs no change. Rollback: install
`work/mm8_m500_source_pre_reduce.glb` the same way.

Reproduce: `REA_NODE=Body REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` -> `REA_SMALL=220
small_pieces.py` (`work/keep_small220.npy`) -> `bone_share.py -- jaw Jaw`, `dump_weights.py` -> keep masks
`work/keep_v4.npy` (small pieces + 4 cm around `vertex_error.py` points of the uniform and v3 ladders), `keep_v5.npy`
(+ `REA_LOCK_R=0.05 drift_lock.py`), `keep_v10.npy` (+ jaw), `keep_v11.npy` (+ faces within 8 cm of the Dead crease
vertex), `keep_v12.npy` (+ 4 cm around the v11 `vertex_error.py` points) -> `REA_WEIGHTS=component REA_HEIGHT_M=2.0
REA_KEEP_FACES=work/keep_v12.npy run_ladder.sh v12 0.55` -> `stretch_check.py`, `texture_drift.py r55`,
`close_ladder.py`, `close_sheet.py`, `probe_max.py` -> build as above -> `REA_NODE=Body lod_check.py`,
`lod_views.py`, `glb_close.py`, `viewer_tiers.py <rollback source> r100 export/mm8_m500.glb r55`.
Cast v2: `blender -b -P scripts/cast_v2.py` -> `graft_cast.py work/mm8_m500_r55_cast_v1.glb <tmp>` ->
`compact_glb.py <tmp> export/mm8_m500.glb`.
Textures since 2026-10-31: the installed GLB is this export with new UVs and maps from the texture quality pass
(`../mm8_m500_claude/texpass/export/mm8_m500.glb`, README "Texture quality pass (2026-10-31)"); geometry, LODs and
clips are this project's.
