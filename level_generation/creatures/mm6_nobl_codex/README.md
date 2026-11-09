# MM6 Swordsman — review handoff

Feedback revision v5 is installed: the concept-shaped sword has a broader point and small upper flare,
adding only 24 triangles. The previous character repairs are preserved. Artistic review remains open. This is reviewable placeholder artwork, following
[Claude's humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md); user artistic acceptance is **not recorded**.
Meshy consumed **40 / 100 credits**, with no pending jobs.

[Open the interactive review](http://127.0.0.1:8901/level_generation/creatures/mm6_nobl_codex/review/viewer/?rev=feedback5)
for all three tiers, eight clips, normal/slow playback, frame stepping, native references and frame feedback.

## Selected delivery

| Artifact | Purpose |
| --- | --- |
| [Packed Blender master](export/mm6_nobl.blend) | Editable rig, sword, eight actions and embedded textures |
| [Portable GLB](export/mm6_nobl_lod0.glb) | Complete body and attached sword, standard glTF, all actions |
| [Runtime body](export/mm6_nobl.glb) | Four LODs, corrected shadow meshes, merged head material, native palette variants |
| [Runtime sword](export/mm6_nobl_sword.glb) | Rigid Sword socket attachment, four LODs |
| [Texture maps and palette ramps](textures/) | Separate body/head maps, padded region masks, native tier ramps |
| [Canonical progress](creature_3d_progress.json) | Selected hashes, job receipts, corrections, completion and acceptance status |

The runtime files are installed in `assets_dev/worlds/mm6/models/`, with bindings in that directory's
`actors.yml`. Installed bytes match the audited exports; permissions are 0644.
The MM6 family is native `nobl`: merged monster IDs **586 / 587 / 588**, descriptors
**Nobleman A / B / C**, displayed as **Swordsman / Expert Swordsman / Master Swordsman**.

| Tier | Palette | Cloak / tunic |
| --- | --- | --- |
| Swordsman | 777 | Olive / burgundy |
| Expert | 778 | Blue / blue-violet |
| Master | 779 | Magenta / dark brown |

The tiers share geometry, rig, clips and texture atlases. Two cloth regions change through native palette ramps;
face, collar, leather, silver/gold trim and sword retain their colours. Browser preview models bake those ramps
for Three.js; the installed runtime uses the shared region-mask material contract.

## Geometry, motion and runtime contract

LOD triangle counts including the sword: **9,749 / 4,788 / 1,672 / 502**.
LOD0 comprises 9,493 body triangles and 256 sword triangles; the head has 2,250 faces.
The skeleton has 141 joints, including baked cloth chains and eight retained unused back-tabard joints.
LOD0 has up to four skin influences; reduced runtime LODs support up to eight.

The grey-haired, moustached body preserves the clean chin, standing collar, capelet, belted tunic, silver greaves
and brown gloves. The locally modelled double-edged sword has a silver blade with a flared point and base, curved gold guard, blue
grip and round gold pommel, without a gem. It is held in the right hand and assembled in every complete export.

| Runtime role | Duration | Local library source |
| --- | ---: | --- |
| Standing | 2.000 s | RelaxIdle |
| Walking | 0.800 s | ArmedWalk |
| Running | 0.800 s | ArmedRunForward |
| Attack | 1.200 s | SwordAttackR1, with native ready/wind-up adaptation |
| Hit | 0.500 s | ArmedGetHitF1, recovery to ready |
| Death | 1.833 s | ShieldDeath1, forward kneel/fall with cloth settling |
| Dead | 1.000 s | Held terminal death pose |
| Fidget | 2.000 s | RelaxIdle |

Source motions use the fitted source-frame rig and world-rotation retargeting. Mesh-measured hands,
connectivity-based finger weights, forearm twists and rigid bracers were corrected locally.
Cloak and front-tabard motion is simulated and baked into the actions; cycle endpoints are closed.
No paid animation jobs or new animation-library downloads were needed.

Runtime scale is **109.874099**, calibrated against the upright walking height of 1.713772 m and native
269-pixel standing frame at scale 0.699997, approximately 188.30 game units. All tiers use the same scale.
Stride is 1.2 m, yaw offset is -1.570796327, melee impact is **0.683 s**, upper-body root is B_Spine,
and B_Neck/B_Head supply head look. Master uses Running at its native speed; the lower tiers walk.
The family has no native spell. Cast/ranged aliases resolve to Attack only for runtime role completeness.

## Original production verification (historical)

- Ordinary OpenYAMM build passed. The affected MM6 actor regression suite passed **29/29** after installation
  and binding-test addition; the final texture revision also passed the focused Swordsman regression **1/1**.
- The shared browser check passed all **24 tier/clip combinations**, without console errors or failed loads.
- Actual exported motion was checked at 48 fps for arm/hand contacts across all eight clips: no detected contacts.
  Blade/body and hand/head penetration checks were zero. Source-relative trace reported zero flags.
- Arm edge stretch worst p99 was 1.82×; hand edge maxima were 3.70× right and 1.22× left, below the 4.5× hand gate.
  Some optional elbow-area/ring measurements are unavailable on sparse geometry or rigid-bracer sections;
  direct stretch, contact and visual checks remain the applicable evidence.
- Both body and head UV audits report zero overlapping pixels. Head density is approximately 3.46× body density.
  Returned UVs were transferred through exact face/corner correspondence without replacing the animated body.
- Maximum exported cycle endpoint difference is 1.20 mm (Running); Walking is 0.0013 mm. Floor residual is below
  0.002 mm. Dead is held exactly.
- Export validation checks clips, LODs, normalized supported influences, variants, textures, attachment and the
  sword's zero region-mask samples. The packed master's normal maps use the same verified orientation.
- Native desktop review covered all tiers indoors and outdoors, movement and attacks, with the same camera
  used for original-sprite comparisons. Outdoor shadows were inspected off and at qualities 2 and 3.
  Runs used OpenGL 3.3 on NVIDIA through Wayland.

Persistent numeric reports, renderer logs, browser results and the final regression output are under
[review/validation](review/validation/). Each in-game comparison folder includes the launch record, settings
and game log. Full-suite 29/29 was observed in the task run; the focused final test has a saved stdout receipt.

| Comparison | Model | Original sprites |
| --- | --- | --- |
| Outdoor, oute3.odm | [Three tiers](review/ingame/out_3d/tiers.png), [attack](review/ingame/out_3d/attack.png) | [Three tiers](review/ingame/out_sprites/tiers.png) |
| Indoor, 6d19.blv | [Three tiers](review/ingame/in_3d/tiers.png), [attack](review/ingame/in_3d/attack.png) | [Three tiers](review/ingame/in_sprites/tiers.png) |
| Outdoor shadows | [Quality 2](review/ingame/out_shadow2/tiers.png), [quality 3](review/ingame/out_shadow3/tiers.png) | — |

Additional renders include [lit body](review/lit_body_three_quarter.png),
[right grip](review/lit_hand_Standing0_R_c.png) and [left hand](review/lit_hand_Standing0_L_a.png).

## References, credits and reproduction

Native observations and source selection are in [ANIMATION_STUDY.md](source/ANIMATION_STUDY.md).
The original sprite project is [mm6_nobl](../mm6_nobl/). Five unresized generated HD body references and four
head references, prompts, rejected returns and provenance are retained under `references_hd/` and
`references_head/`. Inferred hidden anatomy is a modelling interpretation, not recovered original geometry.
Original Meshy returns remain under `meshy/`; requests and hashes are retained in the canonical progress record.

| Meshy operation | Credits | Selected result |
| --- | ---: | --- |
| Smart Topology v1 | 0 | Rejected unsupported image-enhancement option; corrected before resubmission |
| Smart Topology v2 | 5 | Body geometry |
| Rig v1 | 5 | Joint/weight reference, corrected locally |
| Body retexture v1 | 10 | Selected body maps and transferred UVs |
| Head retexture v1 | 10 | Superseded because its upload UVs overlapped |
| Head retexture v2 | 10 | Selected maps after corrected, overlap-free unwrap |
| **Total** | **40** | **60 credits unspent** |

For feedback v2, the original v9 checkpoint remains preserved. The historical scripts
`feedback_geometry.py` and `feedback_tabard.py` produce v10. For historical v3, run
`feet_cloak_repair.py` (v10 → v11_geometry), `feet_cloak_finish.py` (→ v11), and
`fall_cloak_clearance.py` (→ v12), then the export sequence below. Authoring time remains 30 fps;
foot correction keys are spaced at quarter frames. Export samples at 120 fps with unchanged durations.

For v4, `scripts/shoulder_buckle_repair.py` takes v12 to v13; `shoulder_buckle_build.py` also exports it.
The selected authoring checkpoint is `work/rig_v14.blend`; it retains part attributes, source UVs and closed
cloth loops. The packed export is the portable editing handoff. Earlier `rig_v*` files and diagnostic scripts
are checkpoints, not alternative accepted models.

To rebuild from the selected authoring checkpoint, first claim the creature with `tools/creature_workspace.py`.
Use its returned token for all project writes. Run, in order: `scripts/compose_nobl.py`;
`scripts/export_runtime.py` through `tools/run_creature_blender.sh`;
`tools/prepare_actor_glb.py` from the portable LOD0 to `export/mm6_nobl_runtime_lod0.glb`;
`scripts/build_lods.py` through the Blender wrapper; `scripts/package_runtime.py`; and
`scripts/export_audit.py`. Ordinary scripts run through `creature_workspace.py run`.
Packaging includes shadow correction, variants, sword separation, head merging and viewer models/manifest.
Copy the two verified runtime exports to the installed paths and rerun the focused binding and browser checks.
Do not rerun the earlier head handoff onto this checkpoint: it predates cloth-loop closure.

## Feedback revision v2 (2026-10-11)

- **Tabard:** pinned waist and continuous shared bending replace the per-frame translation corrections.
  Standing displacement fell from 38.36 mm to 2.69 mm per 30 fps frame; the shipped GLB was checked separately
  at 48 fps (maximum 1.65 mm per sample). Death cloth folds onto the ground and Dead is held exactly.
- **Belt:** the apparent texture bleed was intersecting geometry. The shirt is tucked inside the leather shell
  and follows the same pelvis motion; the leather hue is corrected.
- **Left hand:** shorter palm, shallow knuckle arc, corrected thumb/finger lengths and volume, fitted joints
  and a relaxed curl. All eight clips pass the hand stretch gate (left maximum 1.22×).
- **Historical F04, corrected in v3:** the apparent missing head in corpse close-ups was a viewer culling
  error, not confirmed head/collar geometry penetration. Controlled Blender views established the cause.

[Final belt](review/feedback_20261011/viewer_final/belt.png) ·
[Final hand](review/feedback_20261011/viewer_final/hand.png) ·
[Walking tabard](review/feedback_20261011/viewer_final/walk.png) ·
[Historical corpse view](review/feedback_20261011/viewer_final/dead.png) ·
[Outdoor verification](review/feedback_20261011/out_3d/tiers.png) ·
[Indoor verification](review/feedback_20261011/in_3d/tiers.png).

The final revision passes all 24 viewer combinations and the focused actor regression. Actual exported clips
were checked for contacts and between-frame cloth motion; final runtime hashes are in the progress record.
The 35-frame motion set predates only the final, smaller waist inset; six final browser views and the native
indoor/outdoor captures use the installed revision. No additional Meshy credits were spent (40/100 total).


## Feedback revision v3 (2026-10-11)

- **Feet:** boot heels previously inherited calf motion, and the grounding pass only grounded one lowest point.
  Sole weights are rigid on the feet. Fitted leg contact keeps idle soles flat, with heel strike, toe-off and
  swing clearance during locomotion. Dense corrective sampling prevents dips between animation frames.
- **Upper cloak:** the dark polygons were an overlapping covered layer exposed by inconsistent skin weights.
  Mantle and cloak now share chest/shoulder deformation; collar flex is confined to the upright neck opening.
- **Fall:** a smooth clearance arch prevents the boots protruding through the lower cloak, then settles before Dead.
- **Viewer:** animated head geometry no longer disappears from close corpse cameras because of stale frustum bounds.
  This corrects the earlier F04 diagnosis. The head itself was intact.

The exported boot check covers all eight clips at 240 samples/second. Maximum idle sole tilt is **0.098°**;
boot shape error is below **0.001 mm**. The worst between-frame floor residual is **−0.607 mm**.
The final fall-cloak pass changes only cloak channels in Death/Dead; all previously checked foot, root, body
and other animation channels are identical, verified in [channel invariants](review/feet_cloak_20261011/final_channel_invariants.json).
The exported fall-cloak check at 120 samples/second reports no boot breakthrough with a 4 mm margin.

All 24 tier/clip combinations load without errors; the focused Swordsman regression passes 1/1.
All eight clips pass hand/body, blade/body and hand/head contact checks. Maximum cycle mismatch is **0.177 mm**.
Indoor/outdoor native review covered the three tiers, gait and attack; a final native death run verifies the
last cloth correction. These checks used OpenGL 3.3 on NVIDIA via Wayland. No additional Meshy credits were spent.

[Idle feet](review/feet_cloak_20261011/viewer_final/idle_feet.png) ·
[Side contact](review/feet_cloak_20261011/viewer_final/idle_side.png) ·
[Walking](review/feet_cloak_20261011/viewer_final/walk6.png) ·
[Corpse upper cloak](review/feet_cloak_20261011/viewer_final/corpse_close.png) ·
[Fall clearance](review/feet_cloak_20261011/viewer_final/death24.png) ·
[Native fall](review/feet_cloak_20261011/death_native/fall.png) ·
[Native settling](review/feet_cloak_20261011/death_native/cloth.png).

Receipts and final selected hashes are in [the review directory](review/feet_cloak_20261011/) and the canonical
progress record. The native run's last `corpse.png` shows the engine's subsequent loot bag, not the body pose.

## Feedback revision v4 (2026-10-11)

- **Shoulder:** the covered shirt followed clavicle/twist motion differently from the mantle. Its shoulder weights
  now match the existing cloth deformation, with a smooth transition into the visible sleeve. The cape itself,
  its overlapping layers, all animation keys, boots, hands and tabard are preserved.
- **Buckle:** the metal medallion was already rigidly attached to the belt through the pelvis. Its hip sway is
  intentional. A second buckle painted onto the shirt moved differently; a pale imprint also remained on the belt.
  Corrected UVs reuse clean fabric and leather, and the metal medallion sits 28 mm lower, centered on the broad belt.
  This intentional UV reuse supersedes the original non-overlapping body UV audit for these waist faces.

The actual exported model was sampled at 120 Hz: **18 covered shoulder probes, 1,224 poses across eight clips**.
The old Walking export let the shirt protrude **7.36 mm** at these probes. The repair retains at least **5.25 mm**
of coverage across the clips (Walking: **11.06 mm**). These are targeted shoulder measurements, not a general
cloth collision guarantee. Maximum buckle/belt attachment error is below **0.001 mm**.
[Animation channel comparison](review/shoulder_buckle_20261011/channel_invariants.json) confirms every animation
channel is unchanged; source assertions also preserve all unrelated geometry and skin weights.

All 24 viewer tier/clip combinations pass; hand/body, blade/body and hand/head checks pass across all eight clips.
The focused Swordsman actor regression passes 1/1. Native indoor/outdoor captures verify all tiers, walking and
attack in OpenGL 3.3 on NVIDIA/Wayland. No new Meshy jobs or credits were needed: total remains **40/100**.

[Before](review/shoulder_buckle_20261011/viewer_before/walk6.png) ·
[Corrected walk](review/shoulder_buckle_20261011/viewer_final/walk6.png) ·
[Buckle](review/shoulder_buckle_20261011/viewer_final/belt.png) ·
[Cloak back](review/shoulder_buckle_20261011/viewer_final/back.png) ·
[Outdoor](review/shoulder_buckle_20261011/out_3d/walk.png) ·
[Indoor](review/shoulder_buckle_20261011/in_3d/tiers.png).

Receipts and selected-export measurements are in [the review directory](review/shoulder_buckle_20261011/).
User artistic acceptance remains pending.

## Feedback revision v5 (2026-10-11) — current

The user supplied a concept drawing and requested a modest blade silhouette change within the existing triangle
budget. The blade now has a narrow middle, a small flare directly below the guard, and a broader diamond-shaped
point. Its center ridge, length, fitted grip, guard and pommel remain intact. This selected concept-guided shape
supersedes the earlier plain straight blade; fine engraving was outside the request.

The full sword is **256 triangles**, up from 232 (**+24**). Sword LODs are **256 / 118 / 64 / 42** triangles;
combined character LODs are **9,749 / 4,788 / 1,672 / 502**. The reduced meshes simplify the fine silhouette at distance.
The main body mesh's positions, normals, UVs, indices and skin weights are byte-identical, as are all animation channels.

Sword/body contact checks pass across all eight clips. Final viewer checks pass all 24 tier/clip combinations,
the focused actor regression passes 1/1, and the installed sword was inspected on all tiers during native
outdoor standing/movement/attack captures (NVIDIA, OpenGL 3.3, Wayland). No new Meshy credits were spent.
The 120 Hz floor comparison confirms the existing Death-only sword/ground intersection still peaks at **47.02 mm**;
the reshaped blade does not increase that depth. Changing that existing death/grip animation was outside this shape request.

[Before / after, left / right](review/sword_concept_20261011/sword_comparison.png) ·
[Supplied concept](review/sword_concept_20261011/concept.png) ·
[Exported blade](review/sword_concept_20261011/viewer_final/blade.png) ·
[Attack](review/sword_concept_20261011/viewer_final/attack.png) ·
[Native view](review/sword_concept_20261011/out_3d/attack.png).

The selected authoring revision is **v14**. Run `scripts/sword_concept_build.py` through the owned Blender wrapper
to reproduce v13 → v14, exports, LODs, packaging and focused checks. Final hashes and receipts are in the
canonical progress record and [review directory](review/sword_concept_20261011/). Artistic acceptance is pending.

## Remaining art limits

The left glove anatomy was reshaped in feedback v2. Cloak folds, braid and ornament details are simplified within the 10k triangle
budget. Cloth is baked and does not dynamically collide with scenery or other actors. These are disclosed
limitations for review, not user-accepted deviations. No further paid work is pending.
The existing Death sword/ground intersection is unchanged by the v5 blade-only revision.
Android was not tested, and changes are uncommitted.
