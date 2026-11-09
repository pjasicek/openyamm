# MM6 Earth Elemental — complete 3D delivery

Rigged, textured and installed on 2026-10-12. Family `ert`, descriptors **526–528**:
Rock Beast / Earth Spirit / Earth Elemental (`ElemEarth A/B/C`). Technical completion is recorded;
user artistic acceptance remains separate. Nothing was committed.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm6_ert_codex/review/viewer/)
includes all three tiers, seven clips, frame stepping, close-up cameras and native sprite references.
It is served by `openyamm-ert-review-8912.service`; LAN host `192.168.1.130`, port `8912`.

## Delivered files

- [Editable master, packed textures](export/mm6_ert.blend).
- [Portable glTF, separate body/head materials](export/mm6_ert_lod0.glb).
- [Runtime glTF, shared palette ramps and LODs](export/mm6_ert.glb), installed byte-identically at
  `assets_dev/worlds/mm6/models/mm6_ert.glb` with three bindings in that directory's `actors.yml`.
- [Exact export measurements](export/export_info.json), [runtime asset audit](work/runtime_asset_audit.json),
  and [canonical progress, input/output hashes and Meshy receipts](creature_3d_progress.json).

**5,998 visible LOD0 triangles**, reduced from 16,590 repaired triangles (63.85% reduction).
Colour and shadow LODs: **5,998 / 2,999 / 1,076 / 415**. One body draw per tier.
22 deform bones plus two hand sockets; normalized skin weights, at most eight influences.
Large rock contours use geometry; fine cracks use base colour and tangent normals.

Separate **1024×1024 body and head** base/normal/ORM sets remain in `textures/` and the editable/portable model.
The runtime packs them without reducing their resolution into **2080×1024** atlases and uses shared textures,
a region mask and native palette ramps for the brown, green and dark grey tiers. Matte roughness is 0.82–1.0,
metallic is zero and the ORM red channel supplies a low specular mask. The normal-map green channel was
corrected from the measured service convention before export. All materials are single-sided.

## Motion and gameplay

| Clip | Seconds | Source / behavior |
|---|---:|---|
| Standing | 2.4 | Small authored torso sway |
| Walking | 1.433333 | Owned Mixamo Mutant Walking, fitted bent arms and measured stride |
| Attack | 1.5 | Authored native left rising fist strike, torso wind-up and recovery |
| Hit | 0.75 | Native backward recoil, both fists raised |
| Fidget | 2.4 | Subtle authored shoulder and body shifts |
| Death | 1.8 | Owned Mutant Dying adapted to a backward fall |
| Dead | 1.0 | Held final supine corpse |

All clips export at 60 Hz. Attack impact/launch is **0.75 s**. The native 40% ranged attack is **Attack 2 / Rock**;
it launches from `Socket_Palm_Left`. The other socket is `Socket_Palm_Right`.
Walking stride is **2.675389974 m**; native height is **197.597036 world units** with scale **82.270811351**.
All three tiers share this height. Run aliases Walking; the unused cast role aliases Attack.
There is no native spell or separate running action to reproduce.

## References and selected production route

The user authorized reuse of completed full-detail MM6 restoration masters from
`../mm6_packed_outline_20261001_batch15/mm6_ert/redo_2x/cleaned/ertst0..4.png`.
[Five selected masters](references_hd/selected_views_review.jpg) retain the native bent-arm standing pose.
The failed fresh reference request is historical, not an unresolved gate.

Meshy geometry v1 with A-pose conversion was rejected for open three-digit hands and generic facial anatomy.
Geometry v2 retained closed fists and the horizontal eye slit. Broken surfaces were capped, joints fitted,
service weights corrected, pilot motions reviewed, and geometry reduced before the final UV handoff.
Body texture v1 and head texture v2 are selected. Head v1 was rejected for mismatched detail and overlapping UVs.
**45 Meshy credits** total; no paid animation clips were needed.

Production checkpoints and scripts are retained in `work/` and `scripts/`. Runtime post-processing uses the
shared prepare/LOD/region-ramp/head-merge tools and `scripts/fix_runtime_material.py`: the latter removes
Blender's portable `KHR_materials_specular` from runtime outputs, whose specular mask is already explicit.
The required back-face tool ran after installation; every material was already single-sided, so it made no split.

## Verification and review

- [Export parity](work/export_parity.json): 684 evaluated samples across seven clips, maximum deviation **0.109 mm**.
  Standing/Fidget loop endpoints coincide; Walking differs by at most **14.47 mm**, about 1.19 runtime world units.
- [UV transfer](work/uv_transfer.json): exact face/corner correspondence, no interior overlap or degenerate faces
  in either selected 1K layout. Dense contacts are in [final_motion_contacts.json](work/final_motion_contacts.json).
- [Viewer check](review/viewer_check.json): all **21 tier/clip combinations** load, no console errors.
  [Normal/quarter-speed running playback](review/final_playback.json) and [loop wrap checks](review/loop_playback.json).
- [Earth family regression](review/game/earth_regression.log): pass, including scales, shared variants, seven clips,
  LOD chain, sockets and an actual rock projectile from the left fist. [Ordinary build](review/game/build.log): pass.
- [MM6 actor suite](review/game/mm6_actor_regressions.log): **44 pass / 3 unrelated material-layout failures** in
  Mage, Guard and Ooze. Their current assets contain 8/6/6 ramp materials while the tests expect merged layouts;
  those assets and assertions were left unchanged.
- Native desktop **OpenGL 3.3, NVIDIA, Wayland** captures: [outdoor comparison](review/game/outdoor_comparison.jpg),
  [indoor comparison](review/game/indoor_comparison.jpg), [outdoor attack sequence](review/game/outdoor_attacks.jpg).
  All four tours completed with 20 captures each; full screenshots, logs and camera/binary records are under
  `review/game/{outdoor,indoor}_{model,sprite}/`. Cameras match; animation phases are not synchronized.

No Android or Vulkan run was made. Runtime checks establish technical delivery, not user approval of the appearance.

## Walking posture correction — user feedback, 2026-10-12

Revision `ert_walk_posture_v2` removes the imported walk's fixed shoulder shrug and upper-spine hunch.
[Idle / before / revised comparison](review/walk_posture_v2/before_after.jpg).
The cyclic body sway remains; feet, timing, mesh, weights, textures and six other clips are unchanged.
The correction also removes the compensating neck/head offset, keeping the face aligned with the revised torso.

All delivered GLBs and the editable/source masters are updated. Reproduction: `scripts/fix_walk_posture.py`,
`scripts/audit_walk_posture.py`, `scripts/apply_walk_posture.py`, `scripts/sync_walk_source.py`; the revision's
`before/` inputs remain immutable. The [byte audit](review/walk_posture_v2/unchanged_data.json) confirms that
only seven Walking rotation tracks changed in the original deliverables.

[Dense deformation checks](review/walk_posture_v2/deformation_audit.json) cover 173 samples, with zero foot change
and upper-body p99 edge stretch reduced from 1.7745 to 1.2822. Export parity, all 21 tier/clip switches,
normal/quarter-speed playback and the focused Earth family regression pass. Native outdoor walking captures
and their run record are in `review/walk_posture_v2/game/`. The full world suite and indoor tour were not
repeated for this animation-only revision. No further Meshy credits were used.

User approved this Walking shoulder/back posture correction on 2026-10-12: “OK this is good.”

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Walk2, Run, Sprint) to
the installed `assets_source/worlds/mm6/models/mm6_ert.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh ert`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_ert_pre_gait.glb`, rerun that rebuild and install its export.
