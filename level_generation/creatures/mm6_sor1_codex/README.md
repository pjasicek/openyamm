# MM6 Sorcerer (sor1) — Codex batch

**Review round 4 texture fix complete. Look and motion accepted by the user.**
[HANDOFF.md](HANDOFF.md) has the current files, hashes, counts and verification.
Only **export/mm6_sor1.glb** and **export/mm6_sor1_staff.glb** are installable.
[Viewer](review/viewer/index.html), [eight-view comparison](review/round4/eight_view_comparison.jpg),
[mip checks](review/round4/mip_comparison.png), [all clips](review/final_clips/front_sheet.jpg).

Body triangles **7753/4085/1852/907**, staff **1674/720/340/148**; all geometry, weights, clips and actor YAML
are unchanged from accepted round 3. Body/head: four shared 2080×1024 maps across every LOD and tier.
Staff: three shared 1024×1024 maps across every LOD. Embedded images **44→7**, total GLB bytes
**19,324,952→10,011,768**. No per-LOD map sets remain.

## Review round 4 decisions

- Use accepted original paint, preserving palette ramps and appearance; no paid generation.
- Put the main robe seam at the back and other seams on piece boundaries/side planes. Pack 180 charts with
  18-pixel margins, then dilate all four maps, including the mask, through unused atlas space.
- Restrict sampling of the old atlas to each source chart's interior. This removes tiny inherited edge flecks
  as well as the long streaks caused by the round-three scattered UV layout.
- Transfer every lower-LOD triangle into one LOD0 chart to avoid interpolating across unrelated atlas islands.
  The staff already has a consistent atlas layout across its geometric LODs, so reuse its accepted LOD0 maps.
- Preserve exact triangle geometry, skin payload and animation sampler bytes by replacing only UV/material
  payloads in the round-three GLBs. Keep the accepted dark collar facets and other geometry unchanged.
- Run the shared runner's static/material checks only, as requested. Carry prior rig evidence through exact
  preservation. Keep accepted far-LOD ratio as the static cap; do not reduce or revise accepted art this round.
- Verify native texel-scale and explicit fourfold-downsampled maps, eight views, all tiers and the shared viewer.
  Six local raster overlaps between adjacent source triangles are documented; unrelated chart bounds never overlap.

## Reproduction and records

Reclaim the lease and guard mutations with `tools/creature_workspace.py`. Blender must use
`tools/run_creature_blender.sh`, one background process, four threads. Historical round-three exporter steps would
restore the old textures; do not run them over this revision.

Current editable files: **work/production_master.blend**, **work/round4_lod0..3.blend**.
Round-three unchanged geometric masters remain `work/round3_lod0..3.blend`.
Round-three endpoints and old records are archived in **review/round4/baseline/**.
Round-two source master/paint are retained under `review/round3/baseline/` and `textures/sor1_*_1k.png`.

Material pipeline: `uv_inspect_r4.py` → `unwrap_r4.py` → `atlas_r4.py` (retained UV cut list) →
`bake_atlas_r4.py` → `transfer_lod_uv_r4.py` → `apply_materials_r4.py` → `export_materials_r4.py`.
The exporter reads frozen round-three baselines, patches UV/materials and asserts geometry/animation preservation.
`material_review_r4.py` checks shared maps, margins and density and assembles the visual comparisons.
`static_gates_r4.py` is a thin entry into the shared runner; `run_browser_r4.py` owns/closes its temporary server
and runs the shared viewer check plus current stills. `render_motions.py` / `sheets.py` refresh clip sheets.

[Material checks](review/round4/material_checks.json), [shared gates](review/round4/shared_gates/gates.md),
[preservation](review/round4/preservation.json), [runtime audit](work/runtime_audit.json),
[bindings](work/round4_bindings_check.txt), [viewer](review/viewer_check.json).
[Round-three README](review/round4/baseline/README.md) retains animation provenance and historical reproduction.

## Budget and boundaries

Smart Topology 5 + rig 5 + body texture 10 + superseded head v1 10 + repaired head v2 10 = **40/100 credits**.
Review rounds 1–4 spent **0** each. No active paid job. No commit, installation, game launch, build or shared edit.
The sprite-restore project `../mm6_sor1/` remains read-only and its recorded source hashes still match.
Native integration/material checks and captures remain with the orchestrator; `integration/actors.yml` is unchanged.


## Gait rollout — 2026-10-31

Package [h03](../gait_rollout_20261031/h03/README.md) appended `Jog` to the installed `mm6_sor1.glb` for the chase
(Sorcerer A-C: Standard and MAW chase at a run pace, Froude above 0.65, which played `Walking` at x2.12-2.54): humanoid set Unarmed-Run-Forward legs, arms and staff from `Walking`, the 16 robe chains re-simulated (numpy port of `scripts/robe_sim.py`);
0.66 s, bound stride 2.6955 (4.09 u/s); phase-aligned to `Walking`, planted feet at 5 deg toe-out. Bound as `run` (the coordinator applies
`h03/bindings.yml`); `Walking` stays the wander clip. Every existing clip, mesh, skin and material is byte-identical.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h03/scripts/rebuild.sh sor1` (from the pre-gait copy
`h03/work/mm6_sor1_pre_gait.glb`). A far-LOD repair, floor-fix or any re-export of this model must re-graft `Jog`
(copy the new source over the pre-gait copy and rerun the rebuild, or graft it with `claude_shared/graft_clips.py`).

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog recomposed with a low knee and short quick steps, and the Walking robe re-simulated over the installed body: cloth
bad 37.5 -> 14.0 % and 21.9 -> 11.1 %; `run_stride_length` 2.0. Details: [mm6_sor1_animfix_claude](../mm6_sor1_animfix_claude/README.md).
