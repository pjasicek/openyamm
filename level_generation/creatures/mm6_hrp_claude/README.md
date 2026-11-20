# MM6 Harpy — Claude creature pipeline

Three native tiers are installed: **556 Harpy**, **557 Harpy Hag**, **558 Harpy Witch**
(`BHarpy A/B/C`, skins `hrp_a/b/c`). The optimized model and upward talon attack are user-accepted (v4).

[Open the review viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_hrp_claude/review/viewer/).
It includes all three tiers, nine clips, native pose references, slow playback and frame feedback.

## Talon attack correction (v2)

Fixed the user-reported knee collapse at frames 34–46 by carrying each knee guide with its leg direction.
The kick no longer reverses its bend plane. [Frame-by-frame review and checks](review/talon_fix/README.md)
cover front/right views, slow playback, quarter-frame continuity and runtime export parity.
A fresh outdoor game capture and the focused Harpy regression pass; earlier indoor comparisons are v1 evidence.
The correction uses zero additional Meshy credits and preserves all three texture sets and attack timing.

## Protected triangle reduction (v3)

Selected the last passing 10% reduction step: **13,534 runtime triangles**, 19.1% fewer than v2.
The next step visibly flattened the chest and made shoulders/thighs angular, so it was rejected.
[Procedure, step counts and comparison evidence](review/reduction/README.md). The existing viewer includes
all three runtime tiers, the accepted original, and the three trials. Textures and animation samples are unchanged.

## Accepted upward attack (v4)

The user accepted the [x2-reference attack preview](review/attack_lean/README.md): higher talons with
forward-facing soles, backward body lean and a slight bank toward her left. It is now installed for all three
tiers and in the main viewer. The other eight clips, all LOD geometry, textures and 13,534-triangle LOD0
remain unchanged. [Promotion receipt](review/checks/accepted_attack.json) verifies every exported animation
sample against the accepted preview; the main tier-A viewer GLB is byte-identical to that preview.
Export reimport passed. The focused Harpy runtime check is blocked while loading the shared model list by
unrelated `mm6_fmp.glb` texture references to UV1 (the loader requires UV0). Harpy materials are byte-identical
to the prior passing asset. Earlier native captures precede this Attack change;
no new native visual capture was needed for the byte-verified promotion.

## Delivery

- Runtime: `assets_dev/worlds/mm6/models/mm6_hrp.glb`, bound in that folder's `actors.yml`.
- Editable master: [export/mm6_hrp.blend](export/mm6_hrp.blend), with native A colours and all required maps packed.
- Portable animated master: [export/mm6_hrp_lod0.glb](export/mm6_hrp_lod0.glb), with the un-ramped base colours.
- Final runtime copy: [export/mm6_hrp.glb](export/mm6_hrp.glb).
- Clip timings and native anchors: [export/clips.json](export/clips.json).
- Effect/socket manifest: [export/effects.json](export/effects.json).
- Installed hash, dimensions, LOD counts and animation integrity: [delivery receipt](review/checks/delivery.json).

The runtime has **13,534 / 6,762 / 2,493 / 883 colour triangles** across four LODs, plus four shadow LODs.
The editable mesh has 13,351 triangles; the backface pass adds 183 required reverse faces at LOD0.
There are 59 bones and three colour primitives per LOD. LOD0 uses at most four bone influences;
decimation blends up to six at coarse LODs, within the existing engine's eight-influence support.

**Body, head and wings retain three independent PBR sets**, as explicitly requested. Each has separate
1024² base colour, normal and specular/roughness/metal maps. Two further 1024² masks select the native
chest and inner-wing feather regions. The head never changes between tiers. No head-material merge is run.
Original Meshy 2048² maps remain in their job folders. The packed MR red channel is the engine's specular mask;
AO is applied gently to base colour and specular, not stored as glTF occlusion in that channel.

## Sources and construction

[ANIMATION_STUDY.md](ANIMATION_STUDY.md) records the native flight, talon attack, hit, death and palette study.
The existing accepted 2D project `../mm6_hrp` remains unchanged. Native palettes 751/752/753 drive the
green/red/blue chest and inner-wing coverts; brown flight feathers, skin, hair and talons are shared.

Five generated full-body HD references and five detailed head references are retained with prompts and output
hashes in `references_hd/` and `references_head/`. Fine anatomy and feather detail are reconstructions from
the native sprites. The custom six-limb rig keeps the ordinary hands independent of the two back wings.
Geometry repairs separated Meshy's fused right wing/arm, restored missing ring fingers and repaired tiny wing holes.
Wing span was fitted to the native flight silhouette before final export.

Meshy cost: **55 credits** against the recorded 100-credit ceiling. All six jobs completed and are downloaded.
The ledger in `creature_3d_progress.json` retains task IDs, requests, credits and input/output hashes.

| Job | Credits | Disposition |
| --- | ---: | --- |
| Smart topology | 5 | Selected geometry, locally repaired |
| Whole-body texture v1 | 10 | Superseded by the requested separate sets |
| Head texture v1 | 10 | Superseded after extending the UV domain over the entire hair fan |
| Torso texture v1 | 10 | Selected body set |
| Wing texture v1 | 10 | Selected wing set |
| Head texture v2 | 10 | Selected head set |

UV transfer was matched by triangle geometry, with maximum corner error below 0.000002 m. Measured normal-map
conventions were corrected to glTF. Material-class masks keep skin/feathers matte and eyes/talons appropriately
glossy. The neck colour is matched across the two atlas boundaries without merging them. Hair is excluded from
the skin grade; isolated green projection spill on outer brown feathers was removed while preserving detail.

## Motion and runtime mapping

All clips are baked at 32 fps: Standing/Walking 1.125 s, Running 0.875 s, Attack 1.75 s, Cast 1.625 s,
Hit 1.125 s, Fidget 2.25 s, Death 1.875 s, Dead 1 s. Flight uses a phased wing chain with torso/tail motion.
Attack chambers both legs, extends the talons and recovers; the arms counterbalance. The Witch's distinct Cast
raises the hands for its native Mass Curse. Death settles onto the side with folded wings, then holds the same corpse.

Scale is 100 world units per metre, shared by all tiers using `scale_reference: BHarpy A`. It was checked against
native `.699997` SFT scaling and model/sprite captures from the same indoor/outdoor cameras.
Attack impact is 1.109375 s (maximum talon forward speed), within half a source tick of the native 1.125 s event.
Cast release is also 1.109375 s. `Socket_Palm_Right` supplies the cast focus and launch position. Eye, gaze and
both palm sockets are exported. `upper_body_root: Root` preserves the whole-body talon/wing choreography.

## Verification

- Ordinary `openyamm` build passed. Focused Harpy actor binding test passed again on the installed final file.
- The MM6 actor suite reported **42 passes / 3 failures**. Failures concern existing Mage/Guard material-count
  expectations and the Ooze glossy-material expectation; their assets and checks were not changed for this task.
- Final delivery validator checks three separate sets at every colour LOD, normalized skinning, variants,
  embedded image sizes, sockets, exact durations, installed byte identity and unchanged animation streams.
- [Quarter-frame mesh/animation audit](review/checks/final_mesh_animation.json): 1,641 samples, finite poses,
  exact looping/end holds and exact Death→Dead transition. Worst interpolated floor penetration is under 0.1 mm.
  The audit records local edge stretch honestly; knees/hips compress during the talon chamber.
- [Runtime GLB reimport](review/export_parity.json) compares all clips and five sockets against the editable master.
- Viewer checks cover all 27 tier/clip combinations; normal and quarter-speed playback captures are retained.
- [Native comparison evidence](review/ingame/receipt.json) contains all three tiers in `oute3.odm` and `6d19.blv`,
  sprite/model comparisons, flight/combat and death captures. Desktop backend: OpenGL 3.3, NVIDIA, Wayland.

No Vulkan/Android build or hardware performance profiling was done. The neck uses a softer shared skin tone at the atlas boundary; fine artistic matching remains subject to user review.

## Resume / rebuild

Use `tools/creature_workspace.py` and claim the creature before writing. `work/textured_master.blend` is the current
geometry/UV/rig authority. Do not rerun the old two-set uploads or `transfer_three_sets.py` alone: the later
`fix_head_domain.py` intentionally expanded the head domain through the complete hair fan.

For motion edits: `animate_harpy.py`, then `sync_actions.py`. For texture edits: `compose_harpy.py`.
Then run `export_harpy.py`, `tools/prepare_actor_glb.py`, `build_lods.py`, `finish_runtime.py`,
`backface_runtime.py` (Blender), `viewer_tiers.py`, `update_viewer_manifest.py`, install the GLB and run
`validate_delivery.py`. Finally run `pack_editable.py`, `final_audit.py`, and `export_parity.py` in Blender.
Blender scripts use the approved `tools/run_creature_blender.sh --token TOKEN <script>` wrapper.
