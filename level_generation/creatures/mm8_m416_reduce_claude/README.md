# MM8 Pirate Crossbowman (`m416`, Pirate Crossbowman (Female) A/B/C) reduction (2026-10-19)

User: "OK do these ones" (MM8 triangle-reduction batch of openyamm-b4: m420, m416, m500, m508, m480). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no part needed rebuilding, so the installed
textures, the three palette variants (`KHR_materials_variants`, `m416_a/b/c`) and the region ramps stay valid. No Meshy
credits. Scripts copied from the sibling Pirate Warrior reduction ([mm8_m412_reduce_claude](../mm8_m412_reduce_claude/README.md),
scalp cap, region groups, gate diff), with the paths, node name (`PirateCrossbowwoman`) and height (1.845 m) changed.

Source: the installed `assets_source/worlds/mm8/models/mm8_m416.glb`, byte-identical to
`../mm8_m416_claude/export/mm8_m416.glb`, copied to `work/mm8_m416_source_pre_reduce.glb` (rollback source). One
material per tier (`PirateCrossbowwoman_A/B/C`, merged 2080x1024 head/body atlas, head set u > 0.5), 62 bones,
4 influences, 8 clips. The crossbow, bolt, quiver and both string halves (3,582 triangles together) are separate
attachments and unchanged; the body keeps every socket and equipment node.

## Scalp cap (`patch_scalp.py`)

As on the m412 Pirate (user found a hole above the right ear there), the head skin is open on top under the bandanna:
a 48-edge boundary loop, rim 1.64-1.77 m. On the installed model the hair and bandanna cover it at every angle
(`review/temple/src_hide.png`, top rows; with the bandanna removed, the background shows through the open scalp in
the lower rows), but the cut moves both rims, so the opening is capped before the ladder: a 48-face fan around the
rest centroid, wound with the rim, weights averaged from the rim (B_Head), every corner on one hair-brown texel. The
cap faces are kept exactly, and so are the skin and bandanna faces within 1.2 cm of each other (`band_border.py`,
289 faces). With the bandanna removed the reduced head is closed at every LOD (`review/temple/noband_lods.png`,
installed / reduced, LOD0-3, right, front, left); textured temple close-ups per LOD in `review/temple/sheet_lods.png`.
The dark band across the forehead under the bandanna is in the texture (unpatched source too), not the cap.

## Keep sets and regions (`make_groups.py`)

Weld 6,068 -> 424 open edges (376 with the cap); no coincident vertices with other weights.

| label | faces | ratio |
|---|---:|---|
| face skin (head set, `B_Head`, front, above 1.56 m) | 1,104 | 70 % |
| neck, ears and scalp (rest of the head-set skin piece) | 859 | 50 % |
| bandanna | 320 | 60 % |
| hair (two back pieces, 450 + 279) | 729 | kept (ladder c) |
| hands (`B_*_Hand` dominant: back of hand, palm, gauntlet cuff) | 591 | 70 % |
| rest: vest, trousers, boots, sash, arms | 7,277 | remaining budget |

Kept exactly (`work/keep_a.npy`, 3,315 faces): the fingers of both hands (1,924; both hold the crossbow), small pieces
of up to 180 faces (764: eyes, bandanna knot tails, sash tails, buckle), the soles (faces below 6 cm, 320), the scalp
cap and the bandanna/hairline border.

## Ladder (limits for the 1.845 m height: p99 5.54 mm, max 27.7 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source (capped) | | 10,880 | | | | |
| a: hair 60 % | 80 % | 8,704 | 3.66 / 22.5 | 0.995 | 0.997 | pass |
| a | 75 % | 8,160 | 4.44 / 22.5 | 0.991 | 0.996 | pass |
| a | 70 % | 7,614 | 5.49 / 22.5 | 0.988 | 0.994 | pass (at the limit), flecks on the right forearm |
| a | 65 % | 7,072 | 6.87 / 33.1 | 0.984 | 0.991 | fail |
| b: hair 80 % | 75 % | 8,160 | 4.42 / 22.5 | 0.991 | 0.996 | pass; gate Hit head penetration 67 mm |
| **c: hair kept** | **75 %** | **8,160** | 4.55 / 22.5 | 0.991 | 0.995 | **pick** |

The 22.5 mm maximum is the same source point at every step (`Dead` frame 3, a neck vertex under the vest collar;
`probe_max.py`). Texture drift of the pick: no face over 40 (`texture_drift.py r75`), so no lock round. Close-ups of
ladder a (`review/close/sheet_a_head.png`, `sheet_a_body.png`: source / 80 / 75 / 70 / 65, textured, from the welded
blend) show face, temples, hands, sash and boots unchanged down to 75 %.

Why the hair is kept: with hair at 60 % the shared gate's head penetration (B_Head samples, the hair, into the
non-head surface) in Death went from 8.7 to 14.4 mm (limit 10) and in Hit from 54.9 to 61.8 mm (already failing on
the installed model: the hair swings through the shoulders when hit); at 80 % Death passed but Hit got 67 mm; kept,
both match the installed model (8.8 / 54.8 mm).

Shading judged from GLB-direct renders (`glb_close.py`, the file's own normals; plain smooth normals):
`review/glbclose/sheet_tex.png` and `sheet_clay.png` (installed / reduced: head front, three-quarter, side, back,
both temples, chin, both crossbow hands from outside and inside, torso, sash, back, boots, feet, Attack, Death).

## Build

`export_cand.py` (`REA_CAND=Cand_75`, `work/ladder_c.blend`) -> `swap_lod0.py` (`work/c75_lod0.glb`) ->
`build_lods.py` (the creature's ratios 0.5 / 0.25 / 0.125, 4 influences, with the 159 sole vertices protected in every
LOD) -> `carry_variants.py` -> `compact_glb.py` -> `check_winding.py` (0 inverted closed parts):
`export/mm8_m416.glb`, 5.9 MB (installed 6.2 MB). Clips are byte-identical to the installed file.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,832 | 5,413 | 2,705 | 1,350 |
| reduced | 8,160 | 4,080 | 2,039 | 1,016 |

Checks on the export:
- **LODs** (`lod_check.py`, `work/lod_check_{src,c75}.json`): no face stretches over 20x in any frame of any clip at
  any LOD; lowest point -1.2 mm or higher (installed -3.6 mm). Top 1.851 / 1.851 / 1.853 / 1.847 m (installed
  1.850 / 1.850 / 1.848 / 1.851): LOD3 is 4 mm lower at the bandanna top. `review/lods/sheet.png` (installed /
  reduced, LOD0-3: standing three-quarter, Attack, aiming hands). The green flecks on the trousers of LOD1-3 are in the
  installed LODs too.
- **Shared gates** (`claude_shared/gates/run_gates.sh` with `work/gates.json`, the m412 config without the cutlass;
  m416 itself has no gate config): the installed model already FAILs 586 rows (the reduced 572).
  `gate_diff.py work/gates_src/gates.json work/gates_c75/gates.json`: 3 rows that pass on the installed model fail:
  `arm_stretch_p99` arm_L in Attack at LOD1 (colour and shadow; 2.03 against 2.0; the installed LOD0 already fails it
  with 2.08, the reduced LOD0 2.04) and `foot_yaw_deg` L in Walking on the LOD2 shadow mesh (24.6 degrees; the
  installed colour LOD1 and LOD2 fail the same row with 38.9 / 39.5, the reduced colour LODs 24.6). LOD1 head
  penetration is higher than installed (Death 20 -> 32 mm, Hit 39 -> 60 mm; installed LOD1 already fails both): the
  LOD builder cuts the hair there. LOD1 ratios 0.45 and 0.55 gave the same rows.
- **Walking head bob** (peer note from m412): `walk_heights.py` (`work/walk_src.json`, `walk_c75.json`): head and
  pelvis heights per 48 fps frame are identical on both files (the clip is unchanged). The source clip has an uneven
  bob: frame-to-frame pelvis steps +0.3, +12.7, +4.4, +10.3 mm at frames 14-17 and -3.9, +7.4, -2.1, -10.1, -16.2 mm
  at frames 22-26 (amplitude about 6 cm). That is in the installed Walking, not the reduction.

Viewer: `review/viewer/` (installed vs reduced for the three tiers, ramps baked by `viewer_variants.py`, manifest by
`viewer_manifest.py`, sha256 and `?v=` per file),
<http://127.0.0.1:8912/level_generation/creatures/mm8_m416_reduce_claude/review/viewer/>;
`node level_generation/creatures/claude_shared/check_viewer.mjs <url>`: 48 model/clip switches, no console errors.
Equipment is not shown in the viewer.

## Status

Installed 2026-10-19 (user: "crossbowman = ok"); winding 0, the regression below passes and the row is in the ledger.

Install (from the repository root): `python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py
level_generation/creatures/mm8_m416_reduce_claude/export/mm8_m416.glb`, `python3 tools/install_model.py
level_generation/creatures/mm8_m416_reduce_claude/export/mm8_m416.glb --world mm8`, then
`OPENYAMM_REGRESSION_FILTER=mm8_female_crossbow_pirate ./build/game/openyamm --headless-run-regression-suite actors`
(`mm8_female_crossbow_pirate_actor_models_keep_tiers_equipment_and_release`) and add the row to
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). The attachments stay as installed.
Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m416_reduce_claude/work/mm8_m416_source_pre_reduce.glb --world mm8 --name mm8_m416.glb`.

Reproduce: `REA_GLB=<rollback source> REA_NODE=PirateCrossbowwoman import_source.py` -> `dump_mesh.py` ->
`dump_faces.py` -> rename `work/source.blend` to `work/source_unpatched.blend` -> `patch_scalp.py` -> `dump_mesh.py` ->
`make_groups.py` -> `band_border.py work/keep_base.npy work/keep_a.npy` -> `REA_KEEP_FACES=work/keep_a.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.6,4:1.0,5:0.7 run_ladder.sh c 0.75` -> build as above ->
`REA_NODE=PirateCrossbowwoman lod_check.py`, gates and `gate_diff.py`, `glb_close.py`, `temple_views.py`,
`hide_band.py` (`HIDE_GROUPS`, `TARGET`, `ORTHO`), `lod_views.py`, `walk_heights.py`, viewer.

## Walk2 and Jog (2026-10-21)

`export/mm8_m416.glb` now also carries `Walk2` (Mixamo Walking (4), 1.233 s) and `Jog` (Mixamo Jogging, 0.85 s), appended by
[../mm8_pirates_gait_claude](../mm8_pirates_gait_claude/README.md) so every tier walks and chases inside the gait
window (the old Running is a sprint that crawled in game). Existing clips, meshes, LODs and variants are byte-identical;
the pre-gait export is kept as `work/mm8_m416_pre_gait.glb` (rollback: `tools/install_model.py` it with
`--name mm8_m416.glb --world mm8`). Installed 2026-10-21; bindings not changed here. Gate values for every descriptor:
`walking: Walk2`, `run: Jog`, `stride_length: 1.3276`, `run_stride_length: 1.8976`; PASSED (every tier 0.78–1.32). Playback:
[../mm8_m416_gait_claude](../mm8_m416_gait_claude/README.md).

## Gait rollout (2026-10-31)

The installed source `assets_source/worlds/mm8/models/mm8_m416.glb` now also carries `Sprint` (Unarmed-Sprint, 0.65 s, stride 3.9377) for MAW's chase and `Jog2` (Unarmed-Run-Forward, 0.90 s, stride 2.2534) for B/C's Standard chase (a run pace); Wimpy A flees on `Walking`.
Appended by [package h17](../gait_rollout_20261031/h17/README.md) on the installed source (existing clips, meshes, LODs
and variants byte-identical); pre-gait copy and rollback: `../gait_rollout_20261031/h17/work/mm8_m416_pre_gait.glb`.
Bindings are in `../gait_rollout_20261031/h17/bindings.yml` (applied by the rollout coordinator). Rebuild:
`../gait_rollout_20261031/h17/scripts/rebuild.sh m416`. A far-LOD repair, head-bob or reduction rerun that rewrites
this source must re-graft these clips (copy the new source over the pre-gait copy and rebuild, or
`claude_shared/graft_clips.py`).
