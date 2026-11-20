# MM6 Jackalman — review round 4 (staff reduction)

The user accepted the entire body. Only the staff was reduced: **2018 → 866 triangles**, with LODs
**472 / 214 / 86**. Body export, animations, skin, sockets and actor bindings are byte-identical.
[Close-ups](review/round4/staff_closeup.png) · [in-game-size comparison](review/round4/staff_ingame.png) ·
[round-4 handoff](HANDOFF.md#review-round-4-staff-reduction). All 6,602 shared gates and 24 viewer switches pass.
40/100 credits spent; round 4 costs zero. The orchestrator installs only the new staff.

## Current deliverables

- [Body](export/mm6_jak1.glb), [staff](export/mm6_jak1_staff.glb), [packed editable master](source/mm6_jak1.blend).
- [Exact actor entries](integration/actors.yml), [proposed native checks](integration/regression.md).
- [Viewer](review/viewer/index.html), [correction closeups](review/round2/corrections.jpg),
  [front](review/clips_front.jpg), [side](review/clips_left.jpg), [three-quarter](review/clips_three_quarter.jpg).
- [Animation provenance](ANIMATION_STUDY.md), [gates](review/round4/shared_gates/gates.md),
  [reduction curve](review/round2/reduction/curve.png), [round-2 receipt](review/round2/validation.json).

Body LODs: **7480 / 4113 / 1816 / 595**. Staff: **866 / 472 / 214 / 86**.
Eight clips and three native cloth tiers share geometry and textures. The 58-bone source-frame rig includes four
arm twist helpers, Staff and StaffTip. All LODs share rebaked texture maps; the staff is not recoloured per tier.

## Unattended decisions

Round 4 uses one fixed staff target, retaining the hook and baking wraps onto a ten-sided shaft.
Fixed-count grip fitting preserves both accepted hands. Shared 1K maps have 16px dilated gutters.
The separate editable source is `source/mm6_jak1_staff.blend`; the accepted body master is unchanged.
No animation, body LOD or palette corrections were authorized or made. See round-4 HANDOFF for metrics.


Hands were corrected in the rest frame, then solved anatomically; free palm faces the thigh, staff palm faces the body.
Standing/Fidget use actual sole IK, without lowering the body to hide ankle tilt. Library Attack/Cast/Death replace
procedural action motion. The free-arm Walking elbow path is periodic; tests include the loop seam.
The falling staff is a secondary rigid-prop simulation, while the character fall is the library clip.

Round 3 supersedes the earlier bright-skin choice. The shared skin ramp targets 30% of the round-1-to-round-2
mean and p95 luminance increase, measured on the same valid source-UV skin texels. Gold and cloth ramps are untouched.
The user requested a texture-only revision, so the packed master and intensity-carrier base images stay unchanged;
`textures/jak1_ramps_runtime.json` controls the final runtime colour. The viewer bakes this palette for preview.
The open wrap uses an actual-panel signed crossing gate instead of a capped garment volume. See HANDOFF for the
palm-cone, rest-toe-out and approximate walking-yaw calibrations and the rejected volume audit.
The historical round-2 LOD3 full-detail IoU limitation remains documented in HANDOFF. No LOD changes were made
after the user accepted the mesh and explicitly restricted round 3 to skin colour.

## Reproduction and review

Serve the repository root with `python3 -m http.server 8916 --bind 127.0.0.1`, then open
`http://127.0.0.1:8916/level_generation/creatures/mm6_jak1_codex/review/viewer/`.
The server used during production has been closed. Viewer anchors map native phases approximately; they are not
claims of frame-exact reproduction.

Reclaim a lease with `tools/creature_workspace.py` before writes. Use `tools/run_creature_blender.sh --token TOKEN`
for project Blender scripts; it enforces the single background process and four-thread budget.
Canonical checkpoints are `work/runtime_master.blend` (final LOD0 rig), the selected blend in
`review/round2/reduction/selection.json`, and the three fitted blends in `lod_selection.json` in that directory.
`source/mm6_jak1.blend` is the packed artist-facing LOD0 file; its preview shader is not a direct runtime export preset.

Round-2 reconstruction path (historical): `scripts/final_gates.py`, `scripts/rebuild_final_package.py`, `scripts/loop_audit.py`,
then `scripts/render_round2_review.py`, `scripts/make_sheets.py clips`, shared `check_viewer.mjs`, and
`scripts/capture_viewer.mjs`. `export_reduced.py` exports the selected LOD0 with supported runtime materials and
OpenGL normals; do not run the old Meshy normal-channel conversion on these rebakes.
Exploration/one-time fitting scripts are retained as provenance and must not be run as a blanket rebuild sequence.

The orchestrator owns installation, engine regression and native indoor/outdoor captures. `../mm6_jak1/`,
other creature projects, shared tools, playbooks and `assets_dev` are read-only to this session.

Round-3 reproduction: `scripts/round3_skin.py` applies the calibrated palette only to the frozen accepted export
(the script rejects changed binary/metadata); `scripts/viewer_tiers.py` rebuilds tier previews. The current ramp
JSON files are authoritative for packaging. Do not rerun the historical texture composer without reapplying this
skin decision. `round3_gates.py` and `round3_review.py` rerun gates and sheets through the guarded Blender wrapper.

For the round-4 staff, start from `source/mm6_jak1_staff.blend`. Run `round4_rebake_final.py` through the
Blender wrapper, then `round4_refresh.py`, and `round4_final_blender.py` through the wrapper. This exports the
current fitted staff and rebuilds previews while asserting the body and bindings remain byte-identical.
`round4_comparisons.py`, `round4_texture_audit.py`, viewer checks and `round4_record.py` refresh the receipts.
The initial fixed-target construction scripts are historical provenance; do not run them over the fitted source
when only re-exporting.

## Installed (2026-10-15)

`assets_source` still held round 2 (before the round-3 skin tone and the round-4 staff); after the model cook switch
the game ran it. `tools/install_model.py export/mm6_jak1.glb` and `export/mm6_jak1_staff.glb --world mm6` (user:
"replace all with the newest"). Previous sources: `work/pre_install_20261015/`.

## Floor fix — 2026-10-21

`--ground-loop Walking`. Before, in world units at tier A: walking lifts every foot by +2.6.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_jak1.glb`), written to `export/mm6_jak1_floor.glb` and installed as `mm6_jak1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout — 2026-10-31

The [gait rollout package h02](../gait_rollout_20261031/h02/README.md) appended Walk2 (0.82 s, stride 1.7152), Run (0.74 s, 3.2027) and Sprint (0.62 s, 4.366) to the installed
`assets_source/worlds/mm6/models/mm6_jak1.glb` (existing clips, meshes, skins and materials byte-identical; installed
with `tools/install_model.py`). Bindings for Jackalman A/B/C, applied by the rollout coordinator from
`../gait_rollout_20261031/h02/bindings.yml`: walking: Walk2, run: Run, sprint: Sprint (the walk-as-run binding chased at x2.4-3.1 and MAW at x4.5-4.9; tier C wandered at x1.55). Run arms are the Walking's, bent and swung more; the staff stays above the floor. Every tier passes `gait_gate.py` under Standard and MAW.
Rebuild: `../gait_rollout_20261031/h02/scripts/rebuild.sh jak1` (from the pre-gait source kept in
`../gait_rollout_20261031/h02/work/`). Any later re-export of this model, including a far-LOD repair rerun
(`../lod_repair_claude/`) or a floor fix, starts from a source without these clips unless it starts from the installed
one: re-graft them (rerun the rebuild on the new source) and keep the bindings.
