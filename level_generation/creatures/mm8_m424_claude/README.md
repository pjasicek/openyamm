# MM8 male Dark Elf peasant — Claude 3D workflow

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m424_reduce_claude/`](../mm8_m424_reduce_claude/README.md) (LOD0 11,585 -> 7,873). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m424_reduce_claude/work/mm8_m424_source_pre_reduce.glb`.


The male `m424` family, monster IDs **19 / 20 / 21**, with original palettes **425 / 426 / 427**. The user requested the MM8 Dark Elf peasant; male was the stated default after the optional sex clarification. Female `m428` is separate scope. References are agent-selected; no user artwork acceptance is recorded.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m424_claude/review/viewer/) · [canonical progress](creature_3d_progress.json) · [motion selection](motion_selection.json)

## Installed assets

- Body source: `assets_source/worlds/mm8/models/mm8_m424.glb`.
- Dagger source: `assets_source/worlds/mm8/models/mm8_m424_dagger.glb`.
- Both installed through `tools/install_model.py --world mm8`; it produced the current desktop cooked runtime copies and textures under `assets_dev/worlds/mm8/models/`.
- Bindings: `assets_dev/worlds/mm8/models/actors.yml`, descriptors `Dark Elf Pesant Male A/B/C` (native spelling). Scale **115.22549242** gives the original **196-unit** standing height. All three native frame scales are equal, so each binding uses that measured scale directly.
- Both native attack roles alias Walking. Gameplay damage, hostility, event timing and AI are unchanged. Walking/Running use measured strides **1.422045 / 2.013467 m**.

The selected editable master is [work/m424_textured_master.blend](work/m424_textured_master.blend). Body LODs have **11,585 / 5,791 / 2,084 / 693** triangles; dagger LODs have **102 / 51 / 23 / 23**. Four normalized influences per body vertex, one body draw and one rigid attachment draw. The LOD0 budget is above the approximate 10k civilian example to retain the detailed face, pointed ears and separated five-finger hands; distant LODs reduce that cost.

## Art and animation

Five full-body and four selected head references are preserved in `references_hd/`; `references_hd/generation_runs.json` records prompts and selected/rejected image provenance. Original sprite hashes and palette mapping come from `../mm8_m424/sources.json` and the native DSFT. The existing 2D restoration project was not modified.

| Clip | Duration | Source / finishing |
|---|---:|---|
| Standing | 2.0 s | Humanoid set RelaxIdle; civilian dagger carry |
| Walking | 0.8 s | RelaxWalkForward, fitted arms and grip |
| Running | 0.7333 s | Stored Mixamo Standard Run; source arm swing and calibrated dagger grip |
| Hit | 0.5 s | UnarmedGetHitF1 recoil relative to the civilian stance |
| Death | 1.3 s | UnarmedDeath1, side/back fall |
| Dead | 1.0 s | Last Death pose held |
| Fidget | 2.2 s | Native-inspired toss: release, one full turn, catch |

Source motions were reviewed before modelling. The final skeleton clones the source bone frames; Meshy supplies joint estimates, followed by anatomical wrist/finger fitting, component weights and twist bones. Generated rounded ears and missing ring fingers were repaired before rigging. Sleeve attachment rings were fitted into the torso; the final hand and arm deformation gates are retained under `work/`.

The dagger is our own 102-triangle mesh, fitted to the right-hand grip. Its `Dagger` bone follows the hand except during the ballistic fidget flight. Export samples at 60 Hz to retain the half-frame catch key; body animation durations remain unchanged. The selected source Death retains its sharp initial head recoil, reviewed in normal and slow browser playback.

Body and independent head retextures were transferred by verified face/corner correspondence onto the animated master. No Meshy texture-return geometry replaced the rig. The unused provisional UV layer was removed before export. Body/head use their own 1K maps; runtime packing preserves both at full resolution in a **2080 × 1024** atlas with a gutter. Warm brown skin is graded consistently across head and hands. The shared region mask recolours only green tunic cloth to the original green, blue and burgundy tiers; hair, skin, white trim, sleeves, trousers, boots and dagger stay fixed.

PBR maps include normal, roughness and material-class specular masks. ORM red carries `openyamm_specular_mask`, not AO; a separate AO bake is gently applied to albedo. The plain steel/brass/leather dagger uses a small authored atlas.

Meshy receipts: smart topology **5**, rig **5**, body texture **10**, head texture **10** = **30 credits**. No paid animation requests. Original job IDs, requests, hashes and downloads remain in the progress record.

## Verification and review

- Dense motion gates: `work/all_motion_gate.json`, `work/g4_final.json`. Arm edge p99 below 2×; right-hand worst edge stretch 2.111×; grounded feet within 2 cm. Two sleeve vertices brush torso clothing within 2 mm during Walking; no hand/head/dagger penetration reported by the applicable closed-surface checks.
- [Export parity](work/export_parity.json): 65 sampled poses across all seven clips, including release/catch, maximum surface error **0.016 mm** after GLB re-import.
- [Static package audit](work/static_audit.json): valid indices, finite animation data, normalized four-influence skin, descending LODs, three tiers, unskinned attachment and exact installed-source hashes.
- Viewer: all **21** tier/clip combinations load without console errors. `review/playback/` contains normal-speed and half-speed WebM recordings, time-stamped live browser samples and inspected per-clip review sheets. `review/viewer/` supports frame stepping, exact-frame links and local feedback.
- Development `openyamm` build passed. Focused regressions check all three MM8 tiers, native height, clip durations, dagger bone, LODs and unchanged simulation state; the existing MM6 male-cannibal height regression also passed. Logs: `review/regressions/`.
- Native desktop OpenGL checks use the NVIDIA GPU on Wayland with engine-written PNGs. Same-camera model/sprite comparisons and LOD captures are catalogued in `review/ingame/captures.json`.

Android and Vulkan were not tested. Native screenshots are visual checks, not performance benchmarks. Indoor console summons lack on-demand loading of foreign sprite families; the comparison uses an isolated fixture declaring the three families before load (`scripts/prepare_indoor_fixture.py`, `review/ingame/indoor_fixture.json`). The production map and renderer are unchanged. Same cameras and spawn coordinates are used; poses are not frame-synchronized. The outdoor map reports pre-existing stale decoration lighting bakes; this creature work does not change bake inputs.

## Reproduction

Acquire the creature workspace lease before modifying this project. Run project commands through `tools/creature_workspace.py run` or `tools/run_creature_blender.sh --token <lease>`. From the repository root:

1. `scripts/rebuild_arm.py` rebuilds the corrected motion chain, copies only Running into the retained textured master with preservation assertions, then exports LOD0. The earlier `scripts/recheck_motion.py` is the full initial motion build.
2. `scripts/export_uploads.py`, then the recorded Meshy retexture jobs, then `scripts/transfer_textures.py` establish production UVs and AO. Reuse the completed receipts; do not resubmit.
3. `scripts/compose_textures.py` grades maps and native ramps; `scripts/export_runtime.py` builds the final textured master and LOD0 export.
4. `tools/prepare_actor_glb.py`, `scripts/build_lods.py`, then `scripts/finish_runtime.py` prepare normals, four LODs, shared ramps, dagger attachment and the merged head atlas. `scripts/export_audit.py` and `scripts/static_audit.py` validate the results.
5. Install both final exports with `tools/install_model.py --world mm8`. The existing review tours retain exact positions and input sequences.

## Running-arm correction — 2026-10-16

The fixed dagger-carry solve was forcing the running elbow sideways. Running now retains the source arm swing with a calibrated wrist roll to keep the dagger clear. Mesh, weights, UVs, other clips and leg motion are unchanged. The updated body is installed; the dagger asset is byte-identical.

[Correction evidence](review/arm_20261016/README.md) · [Running at 1×](review/arm_20261016/playback/Running-1.webm) · [Running at ½×](review/arm_20261016/playback/Running-0.5.webm). All clips passed export/playback checks; focused regression and native indoor/outdoor Running checks passed.
