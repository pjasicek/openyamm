# MM8 Wyvern (`m560`, Wyvern A/B/C) reduction (2026-10-18)

User: "do cyclops, necro, nightmare, phoenix and wyvern then present me with a viewers for all". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant (UVs kept, so the shared textures, three
palette variants and region ramps stay valid). No Meshy credits. Scripts copied from
[mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md) (coincident-vertex separation, exact source weights).

Source: installed `assets_source/worlds/mm8/models/mm8_m560.glb` (m560_v2, identical to `mm8_m560_claude/export/`),
copied to `work/mm8_m560_source_pre_reduce.glb` (rollback source). One material `Wyvern_A` (B/C are variants),
mesh node `Wyvern`, 4 influences, double-sided material (one membrane sheet per wing; the weld kept all 14,652
triangles, so no reversed copies to restore).

## Ladder

Weld 11,692 -> 201 open edges (unchanged by every step); 14 coincident vertices with other weights, but no split
lip seam: no face stretches over 20x its rest area in any frame of any clip, in the source or any candidate
(`scripts/stretch_check.py`). Limits scaled to the 0.99 m bound (p99 2.97 mm, max 14.85 mm).

| ladder | step | triangles | p99 / max mm | IoU min (view) | SSIM | |
|---|---|---:|---|---|---|---|
| uniform | 70 % | 10,256 | 0.81 / 7.65 | 0.994 | 0.999 | pass |
| uniform | 55 % | 8,058 | 1.19 / 10.22 | 0.982 | 0.999 | auto-pick |
| uniform | 45 % | 6,592 | 1.50 / 10.22 | 0.973 | 0.999 | fail |
| head kept | 55 % | 8,058 | 1.45 / 10.22 | 0.975 | 0.999 | fail |
| **head 80 %** | **55 %** | **8,056** | 1.29 / 10.22 | 0.979 (front) | 0.999 | **picked** |
| head 80 % | 50 % | 7,324 | 1.51 / 10.22 | 0.973 | 0.999 | fail |

The uniform 55 % shrank and dropped the upper teeth and smoothed the brow (`review/close/sheet_teeth.png`). Head
and jaw (2,724 faces, Head/Jaw weights) decimated on their own at 80 % (`REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8`)
keep the upper tooth row close to the source (`review/close/sheet_teeth_h80.png`: source / uniform 55 / head-80
55 / head-80 50). Its IoU misses 0.98 only in the front view (0.979; others 0.991-0.996): one-pixel flips along the
edge-on wing membranes (`review/iou_r55_head80.png`), as with the dragon. Feet and claws, dorsal and tail spines,
belly, wing membranes from both sides and the corpse match (`review/close/sheet_h80_body.png`).
Texture drift: 44 faces over 40, 5.7 cm2 in total; no lock.

## Build

`export_cand.py` (Cand_55 of `work/ladder.blend`, the head-80 ladder) -> `swap_lod0.py` -> `build_lods.py` (the
creature's own LOD settings: `build_actor_lods` default ratios 0.5 / 0.18 / 0.06, 4 influences) ->
`carry_variants.py`: `export/mm8_m560.glb`, 6.73 MB (installed 7.96 MB), 5 clips, 3 variants on all 8
colour/shadow meshes.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,652 | 7,325 | 2,620 | 812 |
| reduced | 8,056 | 4,026 | 1,390 | 415 |

`work/lod_check_{src,r55}.json`: every LOD keeps the source bounds (1.0 x 1.0 x 0.43; LOD3 tail tip 4 mm shorter),
stays above the floor in every frame (lowest 0.5 mm, LOD3 Dead) and has no stretched faces. `review/lods/sheet.png`
compares all LODs in flight and at the attack impact; the wing membranes stay whole down to LOD3.

Viewer `review/viewer/` (installed vs reduced for each tier, ramps baked for the browser by `viewer_tiers.py` from
the m560 project's textures): `tools/run_creature_review.py ... check`, 30 clip switches, no console errors.

## Status

`export/mm8_m560.glb` is now the round-2 build below (rebuilt teeth and dorsal spikes, Meshy retexture); the accepted
55 % reduction it started from is kept as `work/v1/mm8_m560_r55.glb`. Not installed; awaiting user review. Install:
`python3 tools/install_model.py level_generation/creatures/mm8_m560_reduce_claude/export/mm8_m560.glb --world mm8`,
then `OPENYAMM_REGRESSION_FILTER=mm8_wyvern_actor_models ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_wyvern_actor_models_keep_native_tiers_and_motion`) and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m560_source_pre_reduce.glb`.
Winding check (`check_winding.py`): 0 inverted closed parts.

Reproduce round 1: `import_source.py` (REA_NODE=Wyvern, REA_GLB=the rollback source) -> `dump_mesh.py`
(REA_PROTECT=Head,Jaw) -> `REA_PROTECT_HEAD=1 REA_PROTECT_RATIO=0.8 run_ladder.sh head80 0.55,0.50` ->
`stretch_check.py`, `close_ladder.py`, `close_sheet.py`, `texture_drift.py` -> build as above ->
`REA_NODE=Wyvern lod_check.py`, `lod_views.py`, `viewer_tiers.py`. Round 2: see its section.

## Retexture check (2026-10-18)

Superseded by round 2 below: the user asked for new teeth and spikes and then a retexture. This check covers the
round-1 reduction with the installed textures.

Verdict: **no retexture needed** (body set, the only set). No credits.

- Texture set: one material per tier (Wyvern_A/B/C) sharing a 2048² base colour, 1K normal/ORM/region mask and two
  tier ramps; no separate head set. The reduction keeps the UVs: all four images are byte-identical in the reduced
  export.
- Texel density (`scripts/retex_stats.py`, `review/retexture/stats.json`): head 3,590 texels/m, neck/body/wing/leg/tail
  1,520-1,610 (the planned 2.5x head islands). Near-black texels at most 0.1 % per region; no Meshy gaps seen.
- Drift at the picked step, by region (faces over 40 / cm²): head 4 / 0.03, neck 24 / 2.5, body 5 / 1.0, wing 2 / 0.1,
  leg 2 / 0.2, tail 7 / 1.8; worst spots render the same as the source.
- Head vs body colour (linear luminance p10/50/90, hide ramp): head 0.022 / 0.074 / 0.180, neck 0.033 / 0.118 /
  0.300, body 0.043 / 0.152 / 0.376. The darker head matches the native sprites (grey-green head, light green body),
  so no unify step.
- Normals: the installed GLB shades smooth; clay renders of the source GLB and the reduced export (direct imports,
  no weld) match at head, mouth, flanks, belly, wings and feet. No normal transfer needed.
- Sheets: `review/retexture/sheet_head.png`, `sheet_body.png` (clay + tiers A/B/C, source vs reduced),
  `sheet_glb_normals.png`. A small flat dark rectangle under the tail is in the source geometry too (not texture).

## Round 2: teeth and dorsal spikes rebuilt, Meshy retexture (2026-10-18)

User on the reduced wyvern: "re-do his teeth, also these ones seem ultra sloppy - [neck spikes arrowed] - then once
good retexture". The Meshy teeth (30 small pieces, painted green) and the dorsal spikes (39 pieces, crystal shards
toward the head, a flat broken piece on the tail) were separate pieces, so they were replaced rather than repaired
(`scripts/build_parts.py`, on Cand_55 of the accepted head-80 ladder; `parts_probe.py` lists the pieces):

- **Teeth:** 30 six-sided cones on even rows (upper 7 + 7 rigid on Head, lower 8 + 8 rigid on Jaw, the lower rows
  offset half a gap so they interlock). Gum line fitted through the original tooth bases and snapped to the skin,
  roots sunk 35 % into the gum, perpendicular to the snout with a slight outward tilt; front fang 6.8 mm, then
  5.8 mm, tapering to 3.4 mm at the back.
- **Dorsal spikes:** 39 closed six-sided tubes that leave the skin along its normal and curve back toward the tail,
  root sunk along the normal. Lengths are the original row smoothed along the spine; the head/neck spikes are graded
  up to the body spikes (at least 75 % of the row's upper quartile, the first behind the head 85 % of the second);
  the tail row keeps its taper; the flat tail piece takes its neighbours' size. Each spike takes the skin weights at
  its root, so it moves rigidly with that skin point.
- **Gate** (`parts_gate.py`, ray-parity inside test over every frame of every clip; the nearest-face sign test
  misfired on the bent tail): the original pieces never enter the body (`work/parts_gate_baseline.json`); the first
  rebuild had two teeth grazing the jaw in Death (0.6 / 0.9 mm), shortened per tooth by `clearance.py`
  (`work/part_scale.json`). Final: spikes 0, teeth worst 0.06 mm in one Death frame (`work/parts_gate.json`).
- 9,071 triangles (1,907 old teeth/spike faces out, 2,922 in: spikes 2,262, teeth 660).

**Retexture** (10 credits, `creature_3d_progress.json`; the user authorised Meshy for this): fresh UVs with the
creature's own settings (`uv_upload.py`: smart project 1.15 rad, margin 0.004, head and jaw islands 2.5x; head
3,488 / rest 1,609 texels/m, coverage 0.27; installed 3,590 / 1,520-1,610, 0.25; `review/uv_layout.png`), then
`requests/retexture_r1.json` (meshy-7, original UVs, PBR, 2K, the creature's four HD masters copied to
`references_hd/`, hashes identical). Return parity: max corner error 1.2e-7. `scripts/compose.py` follows the
creature's own compose (AO grade, red iris, membrane/body region mask, native palette ramps 561/562/563, 1K normal
and ORM, material classes) and paints the rebuilt teeth and spikes ivory, darker at the root, brighter at the tip.
`scripts/texture_chain.sh`: compose -> skinned geometry -> `swap_rt.py` into the creature's own LOD0 export (clips
byte-identical to the installed model) -> `prepare_actor_glb.py` -> `build_actor_lods.py` (creature's ratios,
4 influences) -> `region_variants.py` -> `material_classes_to_orm.py` -> `export/mm8_m560.glb` (6.73 MB, 3 tier
materials with region extras, variants on all 8 meshes, 5 clips).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 14,652 | 7,325 | 2,620 | 812 |
| reduced (round 1) | 8,056 | 4,026 | 1,390 | 415 |
| round 2 | 9,071 | 4,535 | 1,601 | 473 |

`work/lod_check_rt1.json`: every LOD keeps the source bounds, stays above the floor in every frame (lowest 0.3 mm)
and has no stretched faces. The `reduce_ladder.py` parent-transform fix (from the Nightmare/Naga runs) was applied;
re-running the head-80 ladder gave identical metrics and an identical decimation, so the wyvern was unaffected.

Evidence (straight GLB imports, `scripts/glb_close.py` / `glb_sheet.py`): `review/rebuild/sheet_head.png` (open
mouth, teeth and head per tier, installed vs new), `sheet_eyes.png` (eyes and gape), `sheet_spikes.png` (neck, back
and tail spikes per tier), `sheet_body.png` (wings from above and below, feet, whole), `sheet_clay.png`,
`sheet_lods.png`; geometry iterations `review/glbclose/sheet_reb1_*.png`, `sheet_reb2.png`. Viewer
`review/viewer/` (installed / reduced / new for each tier): 45 clip switches, no console errors.

Reproduce: `parts_probe.py` -> `build_parts.py` -> `parts_gate.py` (+ `clearance.py`, rebuild) -> `uv_upload.py`,
`uv_layout.py` -> AO bake (`claude_shared/bake_creature_ao.py` on `work/uv_master.blend`, Rebuilt, 0.012, 2048) ->
Meshy job `retexture_r1` (reuse the stored return) -> `texture_chain.sh` -> `lod_check.py`, `lod_views.py`,
`viewer_tiers.py export/mm8_m560.glb rt1 textures`.

## Installed (2026-10-18)

User: "OK wyvern is good". `check_winding.py`: 0 inverted closed parts. Installed the round-2 export (rebuilt teeth
and spikes, Meshy retexture) with `tools/install_model.py export/mm8_m560.glb --world mm8`; runtime copy 2.4 MB.
`OPENYAMM_REGRESSION_FILTER=mm8_wyvern_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_wyvern_actor_models_keep_native_tiers_and_motion` passes. Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m560_source_pre_reduce.glb`.
