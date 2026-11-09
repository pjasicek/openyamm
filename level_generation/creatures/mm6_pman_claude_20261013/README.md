# MM6 male peasant — new production, 2026-10-13

Rebuilt the New Sorpigal male peasant from the native `pman` family using the current shared Claude humanoid
playbook. The user explicitly excluded Attack. This project contains no attack clip, knife or weapon attachment.
The old `../mm6_pman_claude/` project and its old GLB remain available; the three male-peasant bindings now use
`mm6_pman_v2.glb`.

[Open the review viewer](http://127.0.0.1:8912/level_generation/creatures/mm6_pman_claude_20261013/review/viewer/).
It supports all three colours, six animations, normal/slow playback, frame stepping, native references and
frame-linked feedback. It uses the existing repository HTTP server on port 8912.

## Selected delivery

- Editable, packed master: [export/mm6_pman_v2.blend](export/mm6_pman_v2.blend).
- Complete runtime model: [export/mm6_pman_v2.glb](export/mm6_pman_v2.glb).
- Canonical provenance, Meshy receipts, hashes and progress: [creature_3d_progress.json](creature_3d_progress.json).
- New five-view body masters: [references_hd](references_hd/), with prompts/hashes in `generation_runs.json`.
- New four-view head masters: [references_head](references_head/), with prompts/hashes in `generation_runs.json`.

The body has 10,554 triangles, including a 3,211-triangle head. The fitted source-frame B rig has 56 bones,
including fingers and four twist bones. Display LODs contain 10,554 / 5,275 / 1,898 / 632 triangles, with separate
inset shadow LODs. Weights are normalized and stay within the engine's eight-influence limit.
Separate 1K body and head authoring maps become four 2080×1024 runtime atlases and one material draw per tier.
Only the tunic follows native palette ramps 798/799/800; skin, hair, leggings, leather and brass retain their colours.
Roughness and the MR.R specular mask distinguish cloth, skin, leather and the buckle.

| Descriptor ID | Native descriptor | Variant |
| --- | --- | --- |
| 607 | PeasantM1 A | Green, pman_a |
| 608 | PeasantM1 B | Charcoal, pman_b |
| 609 | PeasantM1 C | Red, pman_c |

## Forearm feedback correction — current revision

Selected revision: `pman_v2_forearms_20261013`. Mesh reduction had collapsed the forearms into long triangles,
causing the pinched elbows and faceted edges in the user's side/rear screenshots. Both arms now use their
original pre-reduction topology and skin weights from `work/clearance_v1.blend`, adding only 747 triangles.
The hands retain their source detail; 2,819 matching triangles retain exact texture coordinates. The new
triangles receive surface-reprojected paint with the old stretched skin bands removed. Hidden arm ends fit
beneath the sleeves; exposed forearms preserve their original shape. The hairline correction remains intact.

[Left arm](review/feedback_v2/closeups/arm_left.png), [right arm](review/feedback_v2/closeups/arm_right.png),
[rear](review/feedback_v2/closeups/arms_back.png), [hit](review/feedback_v2/closeups/hit.png).
[Normal playback](review/feedback_v2/playback_1_sheet.png) and
[quarter-speed playback](review/feedback_v2/playback_0.25_sheet.png) cover all six clips, with side and rear views.
All 1,008 animation channels remain byte-identical. UV overlap is zero; export parity remains within 0.026 mm.
The hidden caps remain inside the sleeves in every animation frame, with at least 11.965 mm clearance.
The final containment test uses closed-garment ray crossings; the old closest-face-normal sign was unreliable
at a concave cuff corner. Its final pass is in `review/feedback_v2/cuff_containment.log`.

All 18 viewer tier/clip combinations passed. The installed GLB and export match SHA-256
`bda8d983662e5d5a8326db85d22c69bc942a41a600d422761df1749f5455de82`.
The focused peasant regression passes for all 17 town peasants. Native outdoor and indoor checks also pass
using an isolated copy of the unchanged male bindings: [outdoor](review/feedback_v2/outdoor),
[indoor](review/feedback_v2/indoor). Ordinary AI remains active; indoor corpses partly leave the camera/are
occluded by columns, so death silhouette inspection additionally uses the close-up viewer playback.

The earlier shared-configuration check failed because the then-current loader required attack-role keys
on the separate female-peasant bindings. This repair did not change those bindings or engine code. The failed full-configuration
check and successful isolated check are recorded separately in `checks/forearm_pman_regression.log` and
`checks/forearm_isolated_regression_pass.log`. The subsequent installation check now passes against the normal shared configuration; see
`checks/accepted_install_regression.log`. This installation changed no engine code or female bindings.

Reproduce the current geometry, texture transfer, AO, maps, export, LODs and viewer with
`scripts/forearm_rebuild.py` through the leased Blender wrapper. It starts from the retained pre-feedback
checkpoint and uses `work/forearms_dense.npz`, extracted by `scripts/probe_forearms.py` from the original dense
source. Then install with `tools/install_model.py`. Earlier reproduction routes below are historical and do
not reproduce the selected forearm revision. No paid generation or new animation was needed.
The user accepted this revision and requested installation on 2026-10-13. The accepted export is installed
for PeasantM1 A/B/C (607/608/609); source and runtime hashes match the export.

## Hairline and cuff feedback correction

The previous revision was `pman_v2_feedback1_20261013`. The skin-painted skirt on the hair mesh was trimmed at
its hairline and seated into the scalp; stray hair pigment on the forehead was cleaned. Oversized arm-cap
corners were refitted beneath the cuffs, with extra cuts and a rounded section for the exposed upper forearms.
Stray cuff pigment on the skin was also removed. This corrected the hairline and cuff protrusions, but left the forearm shape defect described above. No additional Meshy jobs were needed.

[Hairline](review/feedback_v1/closeups/head.png), [side](review/feedback_v1/closeups/head_side.png),
[left cuff](review/feedback_v1/closeups/sleeve_L.png), [right cuff](review/feedback_v1/closeups/sleeve_R.png).
[Normal playback](review/feedback_v1/playback_1_sheet.png) and
[slow playback](review/feedback_v1/playback_0.25_sheet.png) cover all six clips. All 1,008 animation channels
are byte-identical to the previous export. Arm caps remain beneath the cuffs through every sampled frame,
with at least 8.3 mm signed clearance. UV, export, LOD and 18-combination viewer checks passed.
The focused peasant regression passed again, followed by native outdoor and indoor checks in
[review/feedback_v1](review/feedback_v1/). Earlier captures below document the initial revision.

Historical reproduction for the first feedback revision used `scripts/feedback_refine.py`;
it repairs geometry, preserves UVs, rebakes local AO, composes maps, exports, checks and refreshes LODs/viewer.
The original texture-ingestion sequence below predates these corrections. This revision was superseded
by the forearm repair after user feedback; use `scripts/forearm_rebuild.py` for the current result.

## Animation sources

| Role | Owned library source | Duration |
| --- | --- | --- |
| Standing | Mixamo Standard Idle | 3.0 s |
| Walking | Mixamo Standard Walk | 1.166667 s |
| Fidget | Mixamo Neck Stretching | 3.2 s |
| Hit | Humanoid set UnarmedGetHitF1 | 0.5 s |
| Death | Humanoid set UnarmedDeath1 | 1.3 s |
| Dead | Held final Death pose | 1/30 s |

The hit retains the library's upper-body recoil with standing legs and blended endpoints. Its original hop was
rejected during playback. Small shoulder clearance corrections fit the motions to this body. No motion was
invented. This slow civilian uses Walking for the runtime flee/run slot. Unused attack/cast bindings point to
Standing without changing monster AI or statistics.

The native standing frame is 253 pixels at scalar 0.699997. Its 177.099-unit height gives model scale 104.502737.
Measured planted-foot travel gives stride 1.864216 metres. Runtime head look uses B_Neck/B_Head, limited to
60 degrees yaw and 35 degrees pitch. The binding snapshot is [checks/installed_pman_binding.yml](checks/installed_pman_binding.yml).

## Checks and corrections

The source motions, joint fit, arm/hand deformation and contacts were reviewed before texturing. UV transfer
matches faces/corners to the retained weighted mesh. One body-return ear triangle is absent only from Meshy's
body result; its complete appearance is supplied by the independent head result. Hair UV overlaps were repaired
and the returned paint reprojected, preserving face-chart orientation. Both final layouts pass raster overlap
checks; hair micro-normals were flattened after its tangent frames changed.

Quaternion continuity and linear sample interpolation fixed the initial export mismatch during Death.
[Export parity](work/export_parity.json) compares 1,110 samples at 120 Hz across all six clips: maximum error
0.026 mm. Loop endpoints match. [Floor checks](work/final_floor_stride.json) include between-key samples;
minimum contact is within 1.2 mm of the floor. Final finger edge stretch is at most 2.68×, and measured hand/arm
penetration is zero in the tested clips. Both hands and the face were also inspected visually.

- [Normal-speed playback samples](review/final_playback_1x_sheet.png) and
  [quarter-speed samples](review/final_playback_quarter_sheet.png), from actual browser playback.
- [Viewer check](checks/viewer_check.json): all 18 tier/clip combinations load, no console errors.
- [Final GLB structure](checks/final_structure.json): textures, LODs, normalized weights and all six clips.
- Native desktop runs: New Sorpigal `oute3.odm` and Agar's Laboratory `6d19.blv`, OpenGL/NVIDIA on Wayland.
  Each includes original-sprite comparison, ordinary walking/flee AI, a hit and death/corpse captures.
  [Outdoor comparison](review/game/outdoor_comparison.png), [indoor comparison](review/game/indoor_comparison.png).
  AI keeps running, so exact poses/timing differ between captures. Run receipts and logs are in `review/game/`.
- Standard `openyamm` build passed. [Peasant regression](checks/pman_regression.log) passed: all 17 existing town
  peasants bind correctly (A=1, B=9, C=7), share variants and preserve simulation data.
- [Broader MM6 actor regression](checks/mm6_regression.log): 54 passed, 3 existing material failures for the mage,
  guard and ooze. The same failures appear in `../mm6_fmp_codex/review/game/mm6_actor_regressions.log`.
  Those assets were unchanged by this task.

## Reproduction and installation

The retained packed master is the authoring checkpoint. Source-generation scripts, exact image prompts and
four downloaded Meshy jobs are retained; total Meshy consumption was 30 credits. No new job is needed to resume.
For texture-return ingestion run `scripts/texture_ingest.py`, then `scripts/compose_textures.py` and
`scripts/finish_export.py`. The latter normalizes animation, exports and audits deformation.
`scripts/finish_runtime.py` prepares PNGs, builds LODs, applies region ramps, merges the head atlas and refreshes
the viewer. Blender scripts use `tools/run_creature_blender.sh`; claim this creature through
`tools/creature_workspace.py` first and pass your own lease token.

Installation used `tools/install_model.py` with this project’s `export/mm6_pman_v2.glb` and `--world mm6`,
run from the repository root. The authoritative source is
`assets_source/worlds/mm6/models/mm6_pman_v2.glb`; runtime is
`assets_dev/worlds/mm6/models/mm6_pman_v2.glb`. The installer found no hidden backface copies to remove, so both
match the delivered GLB hash. Only PeasantM1 A/B/C blocks in `assets_dev/worlds/mm6/models/actors.yml` changed.
The focused regression expectation in `game/outdoor/HeadlessOutdoorDiagnostics.cpp` now requires six library
clips and rejects Attack/Knife. No gameplay implementation changed.

The repaired model is accepted and installed. The focused regression passes with the normal shared
configuration, and the earlier visual checks remain valid for this unchanged model hash.
