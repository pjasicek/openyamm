# MM6 PeasantF2 — rigged 3D delivery

Installed on 2026-10-12 for **PeasantF2 A/B/C**, family `fmp`, monster IDs **598–600**.
The existing Wimp AI and gameplay data are unchanged. The user explicitly omitted attack and weapon work:
there is no Attack clip, rolling pin, weapon attachment, grip, finger articulation or hand socket.

[Interactive review](http://192.168.1.130:8912/level_generation/creatures/mm6_fmp_codex/review/viewer/)
has all three colours, seven clips, frame controls, slow playback, close cameras and native reference sheets.
[Selected colours and head close-ups](review/selected_variants.jpg).

## Deliverables

- [Editable Blender master with packed maps](export/mm6_fmp.blend).
- [Portable GLB with separate body/head materials](export/mm6_fmp_lod0.glb).
- [Installed runtime GLB](export/mm6_fmp.glb), byte-identical to
  `assets_dev/worlds/mm6/models/mm6_fmp.glb`; bindings are in that folder's `actors.yml`.
- [Measurements](export/export_info.json), [runtime audit](work/runtime_asset_audit.json),
  [canonical state, receipts and delivery hashes](creature_3d_progress.json).

LOD triangles: **9,902 / 4,948 / 1,779 / 592**. The original generated mesh had 15,433 triangles.
The fitted rig has 90 bones: 22 body bones, four arm twist bones and 64 skirt bones.
Hands retain their ordinary relaxed shape. Skin weights are normalized with at most eight influences.
All materials are opaque and single-sided; each runtime colour tier uses one body draw.

Body and head each retain **1024×1024 base colour, normal and metal/roughness maps**.
The runtime packs them into 2080×1024 atlases with a 32-pixel gutter, preserving their resolution.
Shared region ramps change only the apron, waist tie and cap: pale lavender, blue and ochre.
The brown dress, tan blouse, skin, hair and shoes are protected. Fabric is matte, metallic is zero,
and the ORM red channel supplies the low specular mask. Normal green channels were corrected from their
measured service convention. The neck overlap uses matching body colour to soften the separate-set seam.

## Motion and binding

| Clip | Seconds | Basis |
|---|---:|---|
| Standing | 2.0 | Owned Relax idle with more breathing, head and arm movement |
| Walking | 0.8 | Owned Relax walk with a shorter stride under the dress |
| Run | 0.8 | Owned Relax run, with fitted legs and skirt motion |
| Hit | 0.75 | Owned UnarmedGetHitF2 recoil, fitted to the relaxed stance |
| Fidget | 0.75 | Larger head turn and shoulder/arm movement |
| Death | 2.0 | Owned kneeling forward fall, adapted to the long dress |
| Dead | 1.0 | Held final prone corpse |

Animations export at 60 Hz. Standing, Walking, Run and Fidget loop; Dead is motionless.
Native standing height is **249 alpha pixels × 0.699997 = 174.299253 world units**.
The shared binding scale is **105.656395359**, and measured walking stride is **0.804319130 m**.
The runtime's required but unused melee/ranged/cast roles alias Standing. Run has its own clip;
ordinary gameplay still chooses locomotion from actor movement. No combat timing or AI rule was changed.

## Production and corrections

Selected HD A-pose masters are retained in `references_hd/`, with matching close head references in
`references_head/`. Geometry used Meshy smart topology and the service's joint estimate; the retained
mesh received a fitted source-frame rig and local geometric weights. Owned clips came from
`anim_library/humanoid_set/Relax.glb`; no animation purchase was necessary.

Source checkpoints and production scripts remain in `work/` and `scripts/`. The selected geometry is
`work/textured_uv.blend`; `export/mm6_fmp.blend` is the final editable material/animation master.
Historical work files and clay sheets are not the selected delivery.

Corrections included sleeve-root holes, shoulder weights, separate head/body reduction budgets, skirt chains,
covered upper-leg removal, shoe ground contacts and stable skirt/leg interpolation during the fall.
The texture service discarded two coincident opposite-facing finger triangles; exact correspondence checks
identified and removed only that zero-volume fold. Every other returned face/corner matched the retained rig.

Body texture v1 and head texture v2 are selected. Head v1 was rejected for visible UV paint artifacts.
Final variants preserve the cloth's original contrast rather than redistributing its fine grain across the
native sprite's full shadow range. Export retains one UV layer, as required by the runtime.
Total Meshy cost: **40 credits**. No further generation is pending.

To rebuild the selected revision, start from `work/textured_uv.blend`, run `export_model.py`, the shared
`tools/prepare_actor_glb.py`, `build_lods.py`, `assemble_runtime.py` and `install_runtime.py`.
Use the workspace lease wrapper. The old `model_backface_split.py` pass has been retired; packaging owns geometry
cooking through `tools/cook_model_geometry.py`. This authored source already uses single-sided opaque materials.

## Feedback revision v3 — 2026-10-12

The face retains its separate **1K texture set**. The marked blouse opening and inner-eye slivers were geometry/UV
faults: six local repair triangles, a small nose smoothing pass and painted-skin UV samples remove them.
All 9,896 existing triangle windings are preserved; only the reviewed openings received new faces.

Death now uses a consistent drape and grounded boot poses fitted through the open hem, with the cut cuffs covered.
The source kneel and upper-body fall remain. The library `UnarmedGetHitF2` replaces the weak authored Hit;
Standing has stronger breathing/sway and Fidget adds a clearer head, shoulder and arm gesture. Clip lengths,
walking/running, ordinary hands and the no-attack decision remain unchanged. No additional Meshy credits were spent.

[Revision record and limitations](review/feedback_v3/delivery.json),
[geometry/winding check](review/feedback_v3/repair_validation.json),
[normal/slow playback](review/feedback_v3/playback.json),
[loop checks](review/feedback_v3/loops.json),
[targeted poses](review/feedback_v3/targeted_poses.json),
[native checks](review/feedback_v3/native_checks.json),
[face close-up](review/feedback_v3/closeups/fmp-final-fmp_a-head.png) and
[corpse boots](review/feedback_v3/closeups/fmp-v3-boots.png).
The prior selected files are preserved under `review/feedback_v3/before/`.

## Verification

- [UV checks](work/uv_transfer.json): unique face/corner matches, no interior overlap and no degenerate faces
  in either selected layout. Density is recorded by bone region.
- [Export parity](work/export_parity.json): **979 samples**, including half-frames, across all seven clips;
  maximum vertex deviation **0.140 mm**. Run loop endpoint difference is 7.19 mm; other loops are below 0.05 mm.
- [Final deformation checks](work/final_deformation_gate.json): finite geometry, rigid hands and positive
  floor clearance across all sampled clips. Contact and interpolation corrections are preserved separately.
- [Viewer check](review/viewer_check.json): all **21 tier/clip combinations** load, no console errors.
  [Final normal/quarter-speed playback](review/final_playback.json) and
  [four live loop wraps](review/loop_playback.json) pass. Captures are retained in `review/playback/`.
- [Ordinary desktop build](review/game/build.log) and
  [PeasantF2 binding regression](review/game/peasant_regression.log) pass.
- [MM6 actor suite](review/game/mm6_actor_regressions.log): **47 pass / 4 unrelated failures**:
  Mage, Guard and Ooze material-layout expectations, and missing male Cannibal model binding.
  These families were not changed by this delivery.
- Native **OpenGL 3.3, NVIDIA, Wayland** checks: [outdoors](review/game/outdoor_comparison.jpg) and
  [indoors](review/game/indoor_comparison.jpg), each compared with original sprites at the same camera.
  All four runs completed with 16 engine-native screenshots each. Full captures, logs, binary hashes and
  camera records remain under `review/game/{outdoor,indoor}_{model,sprite}/`.

Android and Vulkan were not run. The v3 verification above supersedes the historical review files.
Technical delivery is complete. The user accepted **fmp_v3** on 2026-10-12 ("OK accepted"). Nothing was committed.
