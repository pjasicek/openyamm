# FighterChain handoff — review round 6

## Review round 6

Changed **Running** and the **body/axe steel appearance** only. Runtime body and axe exports need orchestrator replacement. Geometry, UVs, weights, normal/base/mask image pixels, tier cloth ramps, nodes and seven other animation payloads are identical to the accepted round-5 package. The shield GLB is byte-identical. **integration/actors.yml did not change**, SHA-256 `888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b`. [Exact parity and storage proof](review/round6/artifact_parity.json).

No new paid generation: **0 this round; 30/100 credits total**. No game, build, install or commit. This is the requested scoped review delivery with disclosed inherited failures, not a full shared-gate PASS claim.

### Running clip: Standard Run

Source: `anim_library/mixamo/Standard Run.fbx`, SHA-256 `64d7e112a4ce95b2543cccfea18a4a654f00bde8fddd0612b40bb43261fdd6bb`. Existing rest-delta retarget path, source frames 0–22 at 30 fps, **0.733333 s** seamless loop, baked at 120 Hz. Stride binding stays **1.2 m**, corresponding to **1.86 m** at the runtime 1.55× running multiplier (nominal cycle speed 2.536 m/s). Neither Jogging nor RelaxRunForward is used.

The old per-leg pelvis lowering and subsequent per-frame root floor snap caused the height jerk. The new pelvis follows one analytic 12 mm-amplitude sinusoid, two symmetric bobs per cycle, at a constant feasible baseline. Legs solve to that curve. Sole orientation/height is fitted against shipped mesh samples, with no subsequent root snapping. Source torso/arm motion is periodically smoothed, loop endpoint equals start exactly, feet travel linearly backwards in stance (48% per foot) and use a smooth swing/recovery. The axe-carry rotation is distributed over forearm, twist helper and wrist; both props move with their arms and clear the body.

[Front](review/round6/running_front.png), [side](review/round6/running_left.png), [three-quarter](review/round6/running_three_quarter.png), [viewer frames 4](review/round6/viewer/running4.png) / [8](review/round6/viewer/running8.png), [motion fit](review/round6/motion_fit.json), [48 Hz curves](review/round6/vertical_motion.png).

| Bone | Max vertical velocity, before → after, m/s | Max vertical acceleration, before → after, m/s² |
|---|---:|---:|
| B_Pelvis | 3.257 → 0.204 | 135.326 → 3.616 |
| B_Head | 3.280 → 0.253 | 135.491 → 5.152 |

All reused shared torso angular-jitter rows pass. The existing runner has **no positional velocity/acceleration gate**; those measurements are diagnostics, not a newly invented pass gate. [Complete jitter series](review/round6/running_jitter.json). All Running channels close exactly; the other seven clips remain byte-identical.

| Colour LOD | Contact | Peak lowest sole, mm | Worst floor penetration, mm | Max arm / hand stretch |
|---|---:|---:|---:|---:|
| 0 | 88.64% | 11.046 | 1.482 | 3.320 / 1.605 |
| 1 | 82.95% | 11.538 | 1.482 | 1.888 / 1.546 |
| 2 | 82.95% | 11.538 | 1.482 | 1.747 / 1.340 |
| 3 | 100.00% | 5.166 | 1.362 | 2.205 / 1.316 |

All colour LODs pass contact, floor and stretch checks. Arm/wrist angular jitter, elbow plane/flexion, forearm/wrist roll and prop/body clearance pass. LOD0 trunk lean stays within 9.97°. The lowest foot remains within 11.05 mm of the floor. Contact complement at LOD0 is 11.36% of the cycle (the gate defines contact as ≤10 mm, so this is not literal zero-contact flight time).

Shared Running verdict: **FAIL → FAIL**, FAIL rows **90 → 86**, final counts **{'PASS': 886, 'FAIL': 86, 'INFO': 20, 'UNVERIFIED': 3}**. [Final shared report](review/round6/final/gates.md). Remaining failures: accepted finger gaps (axe middle 5.243 mm; shield ring 4.693 mm), shield penetration 7.691 mm, palm axes, generic pelvis minimum 0.9 m versus fitted minimum 0.793 m, distant yaw/sole sampling, shadow LOD1/2 contact (71.59% / 65.91%), and existing LOD ratios. No thresholds were relaxed. Attack and its blade/blow timing are unchanged; the round-6 runner is scoped to Running.

### Mid-grey matte steel

Body and axe steel use the **sRGB midpoint** between archived round-1 and current steel ramps, evaluated at matching source luminance. The same steel ramp applies to all three tiers of each model; existing painted texture detail is retained. Steel ORM red (specular mask) is capped at 32/255 and green (roughness) raised to at least 220/255, blended by the existing steel mask. Metallic factor remains zero. High roughness implements the requested matte/no-shine appearance; lowering roughness would make it glossier.

[Round 1 / current / new front](review/round6/steel_comparison_front.png), [three-quarter](review/round6/steel_comparison_three_quarter.png), [axe close-up](review/round6/axe_steel_comparison.png). These isolate the three palettes on identical accepted geometry and lighting; the shield is unchanged in every column. [Numeric native comparison](review/round6/steel_luminance.json) uses the recorded 2233 native armor pixels and core atlas-mask texels, not viewer lighting or surface-area averages.

| Material | Round 1 mean / P95 sRGB | Current mean / P95 | New mean / P95 |
|---|---:|---:|---:|
| mm6_figc.glb | 0.389 / 0.501 | 0.210 / 0.380 | 0.300 / 0.441 |
| mm6_figc_axe.glb | 0.348 / 0.524 | 0.213 / 0.423 | 0.280 / 0.474 |

Native steel mean / P95: **0.318 / 0.596**. Linear mean and P50/P90/P95 are also recorded. Shield appearance remains accepted and untouched.

### Files and checks

Triangle counts are unchanged:

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 6797 | 3610 | 1725 | 694 |
| Axe | 796 | 432 | 196 | 78 |
| Shield | 1328 | 634 | 303 | 86 |
| Total | 8921 | 4676 | 2224 | 858 |

Body images **4 → 4**, axe images **4 → 4**, one shared set per component across LODs. Geometry/UV density and atlas margins remain unchanged. Body size **11887472 → 11963100 bytes**; axe **2559776 → 2420352 bytes**.

| File | Bytes | SHA-256 |
|---|---:|---|
| export/mm6_figc.glb | 11963100 | `fb84d332b61592eeb1cf453b3c91935e6529b4d8cc1d4f4d02ac55b13d2584c8` |
| export/mm6_figc_axe.glb | 2420352 | `a3939e28cd2afe475c31103daeb3a63ea9c0797527833a76a411ad23eadb2f78` |
| export/mm6_figc_shield.glb | 9829824 | `75c7af5de8ccefc9aa872f32d56f1d87291d5294f5865ac05de417da08af34a6` |
| export/mm6_figc_lod0.glb | 10242412 | `cc26e9628fcc8dd3c1368de9c520af5ed9d84d5b48bd1c5530b2a666ef564cd2` |
| export/mm6_figc_portable.glb | 20384844 | `fe604272cdc878b67f1f5c0e2b2305d460c8f87df7e09adc959a0af108eb671b` |
| export/mm6_figc_authoring.blend | 20884928 | `9bbb9726b5e578d7f756a41bee098b7847daa2c4257210b1509073dc2d98b9e5` |

Changed source/review files: `scripts/*_r6.py`, `textures/round6/body/metal_rough.png`, `textures/round6/axe/metal_rough.png` and their `steel_ramp.json`, `export/artifacts.json`, assembled three-tier viewer GLBs/manifest, editable LOD0 tier-A blend, refreshed full front/side/three-quarter sheets, `review/round6/`, README and progress record. Runtime exports remain authoritative for all LODs and tier ramps.

**check_bindings.py: no BAD line** ([log](review/round6/bindings_check.txt)); **viewer: 24/24 tier/clip switches, no console errors** ([result](review/round6/viewer_check.json)). Running and Attack playback captured at 1× and 0.5×. Native integration/capture remains the orchestrator's job. The final shared gate report is bound to the exported body hash; no changes to game assets were made.

Reproduction under a reclaimed lease: `run_retarget_r6.py` → `run_fit_r6.py` → `run_patch_r6.py` → `materials_r6.py` → `final_checks_r6.py` → `sheets_r6.py`; shared bindings/viewer checks and `record_r6.py`. Blender uses one background process, `--threads 4`. Earlier round builders below are historical and would restore rejected clips. **Never use RelaxRunForward or Jogging.**

Workspace lease released at round-6 handoff; local HTTP viewer server and browser captures closed.

## Earlier handoffs (superseded)

# FighterChain handoff — review round 5

## Review round 5 (running clip)

Replaced Running's rejected RelaxRunForward motion with local **Mixamo Jogging**. All seven other clips, nodes, meshes, weights, textures, tiers and LODs retain their original definitions and binary payload. Axe and shield GLBs are byte-identical to round 4. **integration/actors.yml did not change** (SHA-256 888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b). No game launch, build, installation or commit; zero new credits, **30/100** total.

Running uses the existing rest-delta Mixamo retarget path, source frames 0.5–26.5 at 30 fps, fitted to a **0.8 s** loop. The source supplies torso and arm swing; the shield arm keeps 45% of its swing for plate clearance. Hands retain the accepted closed grip and both attachments follow their hand. Two-bone leg IK fits a **1.86 m** run stride to the unchanged **1.2 m** binding and the runtime's **1.55×** run multiplier (game/fx/WorldFxSystem.cpp). Stance is 47% per foot, with a short low transition; toes align with travel. Root-floor fitting uses the shared runner's mesh evaluator against every shipped colour LOD. Keys are baked at 120 Hz, and every Running channel's final value equals its first value exactly. No new gate implementation was added.

Source SHA-256: `7012cf160057ddd7d06ec68f2fa6090dab3ba60502e2c62b375ee70ed4f01695`. [Motion fit](review/round5/motion_fit.json), [sole fit](review/round5/sole_fit.json), [binary preservation proof](review/round5/artifact_parity.json), [final validation](review/round5/final_validation.json).

[Front](review/round5/running_front.png), [side](review/round5/running_left.png), [three-quarter](review/round5/running_three_quarter.png), [viewer shots/playback](review/round5/viewer/playback_review.json). The three existing full clip sheets have only their Running rows refreshed.

### Checks and remaining limits

Shared runner scoped to **Running**, baseline and final: **FAIL → FAIL**; FAIL rows **126 → 90**. [Final gate report](review/round5/final/gates.md), [accepted baseline](review/round5/baseline/gates.md). The script only filters the shared runner's clip inventory; all measurement and thresholds are its unchanged implementation. Exact loop closure is separately asserted on all exported animation accessors; the shared runner has no dedicated loop endpoint gate.

| LOD | Ground contact | Peak lowest sole, mm | Worst floor penetration, mm | Max arm / hand stretch |
|---|---:|---:|---:|---:|
| 0 | 79.17% | 12.268 | 1.933 | 3.182 / 1.605 |
| 1 | 79.17% | 12.355 | 1.933 | 1.722 / 1.546 |
| 2 | 79.17% | 12.355 | 1.968 | 1.720 / 1.340 |
| 3 | 100.00% | 8.027 | 1.923 | 1.933 / 1.316 |

Ground contact at LOD0–2 is **79.17%, below the shared 80% threshold**; LOD3 is 100%. Floor penetration and arm/hand stretch pass at every colour and shadow LOD.

The accepted baseline's LOD0 contact was 66.15%, floor penetration 7.710 mm. Final LOD0 trunk lean is 11.38°, pelvis minimum 0.750 m. The inherited generic posture threshold requires pelvis ≥0.9 m and still fails on the fitted run. Existing LOD3 sole sampling has no usable left heel/toe separation, and right yaw remains above 10°. Full rig certification is **not** claimed.

Grip remains at the accepted local transforms: LOD0 axe middle-finger gap **5.243 mm**, shield gap **4.693 mm**, shield penetration **7.691 mm**; the shared grip limits still fail. Correcting these would change the otherwise accepted fingers/prop fit. No such changes were made.

check_bindings.py has **no BAD line**. Viewer passes **24 tier/clip switches** and all eight clips advance at 1× and 0.5×. [Bindings](review/round5/bindings_check.txt), [viewer result](review/round5/viewer_check.json). Shared-suite failures and the historical distant LOD visual limit remain explicit; technical completion is false.

### Unchanged triangles and delivery hashes

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body | 6797 | 3610 | 1725 | 694 |
| Axe | 796 | 432 | 196 | 78 |
| Shield | 1328 | 634 | 303 | 86 |
| Total | 8921 | 4676 | 2224 | 858 |

Only the body runtime GLB needs replacement by the orchestrator. Its embedded image count remains **4**; prop image bytes and sizes are unchanged. Review GLBs and the editable blend carry the new Running loop too.

| File | Bytes | SHA-256 |
|---|---:|---|
| export/mm6_figc.glb | 11887472 | 078c1b8baae07a578a4b86be7de51a67ce528124ee555ec47b0f93572d287b71 |
| export/mm6_figc_axe.glb | 2559776 | f239c577cefa62d17ed74233cbabec6530ae35f819c984086904210865b779dc |
| export/mm6_figc_shield.glb | 9829824 | 75c7af5de8ccefc9aa872f32d56f1d87291d5294f5865ac05de417da08af34a6 |
| export/mm6_figc_portable.glb | 20475176 | be2747bc8b85ca3bde5931fbf763474dc434e72c91fe0fb65f34e11af0159676 |
| export/mm6_figc_lod0.glb | 22420044 | be1c421e57773e009c92a86e5da3d4c49bba876fa2a2fc06e49132f507c007b7 |
| export/mm6_figc_authoring.blend | 21528023 | 9ebc5fdd8f82ee3abe88b203c4b9333d54066677e5480d3b84c79eb03f7fbeed |

Reproduction under a reclaimed lease: run_retarget_r5.py → run_refit_r5.py → run_patch_r5.py → run_gates_r5.py → run_finish_r5.py; then shared check_viewer.mjs, viewer_shots.mjs and run_record_r5.py. run_patch_r5.py always starts from review/round5/before, preserving the original payload. The editable blend uses corrected imported bone frames. Previous-round builders below are historical and would restore older Running clips. User rule: **never use RelaxRunForward again**.

Lease released at handoff. Integration and native game review belong to the orchestrator; use tools/install_model.py for accepted model installation, never copy to assets_dev.

## Historical handoffs (superseded)

# FighterChain handoff — review round 4

## Review round 4

Fixed-target axe reduction and texture consolidation are staged. Axe LOD0 is **796 triangles, down 62.49% from 2,122**. The body geometry, all weights/normals, skeleton and eight clips are unchanged; the shield is byte-identical to the installed file. **integration/actors.yml did not change** (SHA-256 888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b). 30/100 credits used overall; zero this round. No game launch, build, assets_dev installation or commit.

| Component | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| Body, unchanged | 6797 | 3610 | 1725 | 694 |
| Axe before | 2122 | 945 | 356 | 118 |
| Axe after | 796 | 432 | 196 | 78 |
| Shield, unchanged | 1328 | 634 | 303 | 86 |
| Combined after | 8921 | 4676 | 2224 | 858 |

The 24-point bit outlines, beard curves, bevels and socket retain the silhouette. The shaft uses eight sides; the fitted grip uses twelve. Wrap turns, rivets and forged wear are baked from the accepted axe into base colour and tangent normals. Removing the raised langets exposed a connection gap; extending the bit necks closes it without changing the fixed counts. The UV gutters were corrected after a pixel audit. These were implementation repairs to one fixed target, not a reduction search or curve.

[Close-up comparison](review/round4/axe_closeup.png), [same in-game scale](review/round4/axe_ingame.png), [eight body views](review/round4/body_eight_views.png), [LOD1 texture comparison](review/round4/body_lod1.png), [lower levels](review/round4/lower_lods.png). Gameplay-scale axe height corresponds to a 700-pixel actor; these are offline renders, not game captures. Fresh clip sheets contain 168 frames. The viewer passes 24 tier/clip switches and all eight clips advance at 1x and 0.5x.

### Texture memory

| File | Embedded images before → after | GLB MB before → after |
|---|---:|---:|
| mm6_figc.glb | 16 → 4 | 18.67 → 11.71 |
| mm6_figc_axe.glb | 4 → 4 | 9.88 → 2.56 |
| mm6_figc_shield.glb | 4 → 4 | 9.83 → 9.83 |

All four body LODs reference ONE 2304×2608 set: base colour, ORM/specular mask, tangent normal and region mask. 458 islands are packed by shape without rotation, scaling or resampling. Existing LOD0 texels are copied at 1:1 density with at least 16 pixels of dilation. Black base-colour pixels fall from 51.26% to 28.08%. Lower LODs use their retained original UV-chart lineage to address this shared atlas; tiny charts absent from LOD0 are explicitly mapped to the nearest surviving surface. Body positions, normals and skin weights remain exactly equal per triangle corner across colour and shadow LODs.

The axe uses ONE shared 1024×1024 four-map set for all LODs. Its measured 16-pixel island dilations do not overlap, and the image border is 16.89 pixels. Average surface texel density is 1252.7 texels/m versus 1221.7 before. Maps are in textures/round4_body/ and textures/round4_axe/. Estimated unmipped RGBA8 image storage: body 146.67 → 96.14 MB; axe 67.11 → 16.78 MB. These are pixel estimates, not a hardware VRAM measurement. [Storage](review/round4/storage.json), [atlas](review/round4/body_atlas.json), [padding](review/round4/axe_padding.json), [density](review/round4/axe_density.json), [invariance proof](review/round4/invariance.json).

### Shared gates and open limits

**Shared runner verdict: FAIL**, on both the accepted and revised exports. The accepted baseline has 1078 FAIL rows; the revision has 1041. Both retain 13 UNVERIFIED rows. The full [current report](review/round4/gates/gates.md) and [accepted baseline](review/round4/accepted_gates/gates.md) include the unchanged body/hand motion findings; thresholds were not relaxed. Cloth containment is unverified, outside this axe/texture-only scope.

All 16 axe strike checks pass (four checks at four LODs): the shared 48-Hz runner selects **0.697917 s** on both exports, versus unchanged impact binding **0.715 s** (17.083 ms error, below 20.833 ms). Edge share is **0.999544** and signed lead **0.833311**. The node Axe and local grip point [0,0,0] remain fixed. Maximum measured axe/body penetration improves from 13.731 to 6.161 mm but remains above the runner's 2-mm limit.

| LOD | Maximum grip gap, mm: before → after | Grip penetration, mm: before → after |
|---|---:|---:|
| 0 | 5.307 → 5.243 | 0.000 → 0.000 |
| 1 | 3.821 → 3.601 | 0.376 → 0.000 |
| 2 | 11.005 → 9.582 | 0.823 → 0.262 |
| 3 | 16.248 → 17.736 | 0.000 → 1.807 |

**Grip does not receive a false PASS.** LOD0's middle-finger gap improves but remains over 3 mm; LOD3's gap grows by 1.488 mm. The body/hands remain untouched as requested. The selector includes the whole narrow haft so coarse triangles spanning the grip are actually measured. The fixed-target pass stops here under the cost controls. The older round-3 distant silhouette failure is historical and was not remeasured as a new curve.

check_bindings.py prints no BAD line and weight-sum error is zero for all three runtime files. [Binding result](review/round4/bindings_check.txt), [viewer check](review/round4/viewer_check.json), [playback](review/round4/viewer/playback_review.json).

### Files and hashes

Install candidates are export/mm6_figc.glb and export/mm6_figc_axe.glb. The shield is listed for verification and remains identical. The portable GLB is the tier-A review; the packed authoring blend reflects the current un-ramped scene. review/round4/axe_authoring.blend contains the editable axe and its LODs. [All changed delivery hashes](review/round4/changed_files.json).

| File | SHA-256 |
|---|---|
| export/mm6_figc.glb | cda51c08823f2f377d560fd0a0ce2ef40d1549d433780451265fc12b71ba8693 |
| export/mm6_figc_axe.glb | f239c577cefa62d17ed74233cbabec6530ae35f819c984086904210865b779dc |
| export/mm6_figc_shield.glb | 75c7af5de8ccefc9aa872f32d56f1d87291d5294f5865ac05de417da08af34a6 |
| export/mm6_figc_portable.glb | 831f43675fd726e55c63ad9aa8863702ebd69d0af45d9e8772005105d2056648 |
| export/mm6_figc_authoring.blend | cdd5de160b0b1759f7996d5169f0cd39c4c00ba164ca135bcafd275c30d26be5 |
| export/mm6_figc_lod0.glb | 127fa9802c6b56487173263519c932ec7741ef47088e3d324ee8d03adddce98e |

Reproduction, under a reclaimed lease: scripts/axe_reduce_r4.py creates the fixed axe/maps; scripts/body_atlas_r4.py and body_source_uv_r4.py/body_uv_r4.py preserve and share the body atlas; scripts/package_r4.py produces runtime and viewer GLBs without round-tripping the body animation; scripts/review_r4.py refreshes the editable snapshot and sheets. Call the shared gate runner with gates.json, then record_round4.py and validate_handoff.py. The earlier round-3 runtime_finish.py/lods.py pipeline is historical and would restore per-LOD textures.

The lease is released at handoff. The orchestrator owns integration, game checks and review of the recorded limits.

## Historical handoffs

The sections below are retained as history; their counts, hashes, completion claims and reproduction commands are superseded by review round 4.

# FighterChain handoff — review round 3

**Re-exported and reviewed; the LOD3 visual gate remains open.** The round-2 appearance was accepted by the user. No clips, tier ramps, grip frames or binding values were redesigned. 30/100 credits used overall; 0 credits used in round 3.

## Triangle reduction

LOD0 is **10,247 triangles, down 33.58%**. The body is 6,797, the axe 2,122 and the shield 1,328 triangles. Geometry was reduced in approximately 10% component steps with weighted protection for the face, hands, joints, silhouettes and contacts. Body/head maps were rebaked with their seam connectivity retained; rigid props received separate UV charts and isolated source baking. Base colour, masks, ORM and tangent normals were transferred. The accepted axe head, socket and wooden shaft remain exact source geometry; the 318 axe-triangle saving comes from the wrap/fittings. More aggressive head reduction produced a visible inner-bevel defect and was rejected even when whole-character SSIM passed.

| LOD | Before | After (body + axe + shield) | Min IoU | Pooled IoU | Min SSIM | Rig gates |
|---|---:|---:|---:|---:|---:|---|
| 0 | 15,427 | 10,247 (6797 + 2122 + 1328) | 0.996202 | 0.997215 | 0.982186 | pass |
| 1 | 7,712 | 5,189 (3610 + 945 + 634) | 0.989312 | 0.991729 | 0.933472 | pass |
| 2 | 2,771 | 2,384 (1725 + 356 + 303) | 0.975665 | 0.979497 | 0.921162 | pass |
| 3 | 903 | 898 (694 + 118 + 86) | 0.942966 | 0.959037 | 0.860437 | pass |


LOD0 uses the user's original strict thresholds (every view IoU >= 0.995 and SSIM >= 0.98), at about 690–700 pixels body height. LOD1–3 use the subsequently revised batch criterion: pooled IoU >= 0.97 at actor heights 550/220/88 pixels. Minimum per-view SSIM is reported for the distant levels without pretending those levels meet 0.98. Metrics use eight azimuths, Standing at frame 0, fixed cameras, the actual tier-A material equation, CPU Cycles and a tight foreground bounding window for SSIM. All three tiers share the same geometry and unchanged ramp values.

The next body trial (9,192 combined triangles with its trial props) failed at 0.994412 IoU / 0.978499 SSIM. The more aggressive prop trial (8,814 combined) failed SSIM at 0.974644. The 9,565-triangle trial passed whole-body metrics but failed the manual prop close-up. This is a measured, conservative stop, not a claim of globally optimal topology. The complete historical trials and selected results are in [review/round3/](review/round3/), especially [reduction_curve.csv](review/round3/reduction_curve.csv), [close_reduction_curve.json](review/round3/close_reduction_curve.json), [reduction_results.json](review/round3/reduction_results.json), [eight-view pairs](review/round3/eight_view_comparison.png) and the three LOD comparison sheets.

**Open fault:** LOD3's pooled IoU is 0.959037, below 0.97. It improves on the installed 903-triangle LOD3's 0.937759 under the same 88-pixel comparison, and its 898 triangles remain below the installed cap. Contour fitting, extra silhouette edges and contact projection improved it but did not meet the target. Technical completion is therefore recorded as false. No failing trial has been labelled a pass.

## Review round 3

The three runtime GLBs below are the integration candidates; the portable GLB is combined tier-A LOD0 for review, and the Blender file is the canonical packed authoring source. [All changed delivery-file hashes](review/round3/changed_files.json), [artifact sizes](export/artifacts.json), [texture hashes/dimensions](review/round3/texture_manifest.json) and lower-LOD authoring files are retained. Re-export the packed source with `scripts/export_baked.py`; `scripts/export_runtime.py` is only for explicitly supplied original-UV trial sources. `scripts/lods.py` and `scripts/runtime_finish.py` package the selected lower meshes, colour regions, head atlases, attachments and viewer.

| File | SHA-256 |
|---|---|
| export/mm6_figc.glb | `e3cf967228357f281bb5dcfd4d0ea37ba03b4500cc4f726468ef476399e80cbf` |
| export/mm6_figc_axe.glb | `e1e16398efb1fa4d44bf0c07eec04b07aef5f8a19d0e59b015dc8cf1cd919400` |
| export/mm6_figc_shield.glb | `75c7af5de8ccefc9aa872f32d56f1d87291d5294f5865ac05de417da08af34a6` |
| export/mm6_figc_portable.glb | `3dd2a9f414b4d7a05fede85a305243fcfec72400456e0838b0711d634fd0c43f` |
| export/mm6_figc_authoring.blend | `f3eb28e3a3f5a9954f1ba0b25506f298f9ac02ccb9e27a59e54d85792f719812` |


**integration/actors.yml did not change.** SHA-256: `888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b`. Descriptors 535–537, tiers figc_a/b/c, scale 126.027899, z offset -1.512415, yaw -1.570796327 and melee impact 0.715 seconds remain unchanged. The 1,392 animation channels in each raw LOD export are byte-identical to the accepted export; all eight clips and the 58-bone skeleton remain. [Animation/binding proof](review/round3/animation_invariance.json).

Existing G4/G5/G6 checks pass on all four colour LODs, all eight clips, 682 samples per LOD at 48 Hz. LOD0 maximum pooled arm p99 is 1.494136, finger stretch 1.604588, head contact 5.310 mm; arm/prop-body contacts are zero and floors stay nonnegative. The blade gate passes at 0.714583 s, speed 23.707 m/s and edge share 0.998678. Motion trace has no flags. Dense grip-envelope clearance changed by at most 0.0568 mm. This is an envelope comparison, not a new per-digit surface-contact certificate. Export parity and UV checks pass.

Bindings/weights are checked by `check_bindings.py` with no BAD line. The viewer check covers 24 tier/clip switches; all eight clips are played at 1x and 0.5x. Fresh front, side and three-quarter sheets contain 168 frames. [Viewer](review/viewer/index.html), [round-3 close-ups](review/round3/details/), [axe comparison](review/round3/axe_comparison.png), [shield comparison](review/round3/shield_comparison.png), [playback record](review/round3/viewer_c/playback_review.json).

Coverage limit: unchanged bone channels preserve the accepted elbow/roll/palm motion, but this round does not claim a new absolute closed-volume sleeve/hem containment certificate for the layered, open garment surfaces. Exploratory nearest-face cloth probes are not acceptance evidence. Colour-mesh rig gates and final weight checks are distinct from a new full shared-suite audit of every shadow mesh.

Body/gear LOD0 maps are 2048 pixels; the head is 1024. The body/head atlas is 3104x2048, followed by 2080x1024, 1056x512 and 544x256. A 1K body colour trial failed SSIM (0.977633). Per-LOD rebakes increase texture storage: the three runtime GLBs total 36.60 MiB versus 26.08 MiB before. [Storage estimates](review/round3/storage.json) report the separate uncompressed pixel cost; triangle savings are not a claim of lower total GPU memory.

No assets_dev installation, game launch, build, regression run or commit was performed. Integration and game checks remain with the orchestrator. The workspace lease is released at handoff.

## Historical handoffs

The following sections record earlier deliveries. Their counts, hashes and completion statements are superseded by the round-3 record above.

# FighterChain / figc — technical handoff

**Review round 2 ready for orchestrator re-integration, 2026-10-12.** Technical production is complete; artistic acceptance is
not recorded. **30/100 Meshy credits consumed, 70 unused.** No commits, runtime installs, shared-file edits,
CMake builds, game launches or game regression runs were made by this production session.

## Files to integrate

| File | Purpose |
|---|---|
| [export/mm6_figc.glb](export/mm6_figc.glb) | Body, 58 bones, eight clips, three tiers, colour/shadow LODs |
| [export/mm6_figc_axe.glb](export/mm6_figc_axe.glb) | Native right-hand axe; attachment node Axe |
| [export/mm6_figc_shield.glb](export/mm6_figc_shield.glb) | Native left-hand shield; attachment node Shield |
| [integration/actors.yml](integration/actors.yml) | Exact FighterChain A/B/C blocks for merged actors.yml |
| [integration/regression.md](integration/regression.md) | Proposed case, map, ids, dimensions and attachment checks |
| [integration/playbook_notes.md](integration/playbook_notes.md) | Production lessons; no shared playbook changes |

Copy only these three runtime GLBs to assets_dev/worlds/mm6/models/. Merge the three entries under the
existing actors list; do not replace the shared file. The source sheathed sword/hilt is body geometry on the
pelvis, so it requires no third runtime attachment. The sprite's held weapon is an axe despite the batch
nickname “swordsman”. The sprite-restoration project ../mm6_figc was used read-only.

Bindings: descriptors **535–537**, skins **figc_a / figc_b / figc_c**, shared scale **126.027899**,
z offset **-1.512415**, yaw offset **-1.570796327**. Melee impact **0.715 s** in the **1.5 s** Attack.
Standing calibration is **247 px x 0.899994 = 222.298518 game units**, from a **1.763883397 m** posed model.
The regression proposal is **mm6_chain_fighter_actor_models_and_equipment**, indoors **6d07.blv**,
summoned ids **535, 536, 537**, standing height **212–233**, tier difference at most **1 unit**.

## Review and editable assets

- [Viewer](review/viewer/index.html): serve the repository root over HTTP and open this path.
  Reuses the established shared viewer; no server is left running by this session.
- Final sheets: [front](review/clips_front.png), [side](review/clips_left.png),
  [three-quarter](review/clips_three_quarter.png), seven frames per clip in all eight roles.
- Final Veteran [standing](review/round2/viewer_c/standing.png), [corpse](review/round2/viewer_c/corpse.png),
  and [all-role playback record at 1x / 0.5x](review/round2/viewer_c/playback_review.json).
- [Portable complete tier-A GLB](export/mm6_figc_portable.glb) and
  [packed authoring Blender file](export/mm6_figc_authoring.blend).
- [Full README](README.md), [progress/paid-job receipts](creature_3d_progress.json),
  [artifact sizes and SHA-256](export/artifacts.json),
  [static handoff validation](review/handoff_validation.json).

Runtime tiers use shared base textures, masks and native-derived palette ramps. Viewer variants bake their
colours for standard glTF. The body/head atlas set is 2080x1024. Combined colour triangles including props:
**15,427 / 7,712 / 2,771 / 903**. LOD0 deliberately exceeds a generic 10k target to retain armour, hands and face.

## Gate numbers

All **eight clips / 682 samples at 48 Hz** passed the measured G4/G5/G6 gates on the exported GLB:

| Check | Worst result | Gate / evidence |
|---|---:|---|
| G4 arm edge stretch p99 | **1.4948x** | Under the approximately 1.5–2x playbook range |
| G5 fingers, both hands | **2.4189x** | Below 4.5x |
| G6 sampled arm/body and actual prop/body contact | **0 mm** | Below 2 mm, every clip |
| Head into pauldrons | **4.9838 mm** | Below 10 mm |
| Source/export group motion | **0 flags** | No group exceeds source + 10 degrees / 48-Hz sample |
| Actual axe edge lead | **0.9987** | Cutting edge leads |
| Target-facing cut | **0.6459 forward**, **23.707 m/s** | Fastest qualifying cut at **0.714583 s** |
| Model-plane clearance | **4.290 mm** | Worst Running sample, before binding z offset |
| Viewer | **24/24 switches** | Zero failures / console errors |

Living clip pelvis minima: Standing **1.053 m**, Walking **0.988**, Running **0.923**, Attack **0.975**,
Hit **0.999**, Fidget **1.027**. Maximum trunk lean respectively **3.33, 5.65, 3.71, 19.23, 14.67, 19.38 degrees**.
Death/Dead intentionally fall to **96.21 / 86.50 degrees**; the props release and land outside the corpse.

Evidence: [exported gates](work/export_full_gates.json), [motion traces](work/export_motion_trace.json),
[blade gate](work/blade_gate.json), [viewer check](review/viewer_check.json),
[UV check](work/uv_checks.json), [scale calibration](work/scale_calibration.json).

## Open faults and limits

No blocking failure remains in the measured rig, blade or viewer gates. Preserve these qualifications:

- **Artistic review of round 2 is pending.** Requested dull-grey steel and equipment changes are implemented.
  No user acceptance or new in-game approval is implied by this handoff.
- Individual arm-edge maximum is **4.628x** in Death; the p99 gate passes. The broad lower torso/leg
  diagnostic peaks at **3.185x** in Running (p99 **2.414x**). Reports retain these values.
- Export/authoring parity is **0.0233 mm** on integer frames, up to **4.169 mm** between frames from
  30-fps export of denser floor keys. Rig/contact gates checked the exported interpolation.
- The contact scan uses nearest-face candidates within 5 cm plus three-ray inside voting for open garment
  surfaces. It checks selected arms, actual props and head; it does not certify every garment self-contact.
- One head-UV boundary/raster texel overlaps at 512-square measurement (**0.000739%**); body overlap is zero,
  with no degenerate UV triangles. No visual UV fault was found in the reviewed export.
- The z offset produces approximately **0.972 game units** of worst Running floor dip. Proposed runtime
  visual tolerance is two units. Additive head-look clearance, stride speed, GPU material response and
  indoor/outdoor behaviour remain untested until integration.

## Orchestrator next steps

1. Install the three runtime GLBs and merge [integration/actors.yml](integration/actors.yml).
2. Implement/run the proposed focused regression and affected MM6 actor suite, using the standard development build.
3. Run serialized indoor 6d07.blv and outdoor oute3.odm comparisons with native sprites: all tiers, locomotion,
   melee impact, hit, fidget, death/corpse, head look and LOD transitions.
4. Present the viewer/captures for artistic review; return corrections to this project.

The production lease is released at handoff. Reclaim mm6:figc before any further edits. Never replay paid
jobs merely to resume: successful topology, rig and retextures and their provenance are already retained.

## Review round 1

**Ready for re-integration. No additional credits used; 30/100 total.** Historical round-1 record: this revision was rejected for slab-like props and light steel.
Review round 2 below supersedes its appearance and hashes. The previous exports and state are
preserved in review/round1/before/. The supplied in-game comparison depicts that previous revision.

Changes:

- **Steel:** identical dull-grey steel ramps across A/B/C body, head and gear, with compressed highlights;
  armour specular-mask strength 0.40 and roughness around 0.64 replace the previous 0.85 / 0.34 response.
- **Axe:** rebuilt curved double bits with actual edge thickness and bevels, a forged socket and ferrules,
  wood grain, helical leather wrap, forged grain/scratches in a dedicated material atlas.
- **Shield:** tall coffin outline, bevelled grey studded rim, grey central face, native tier-coloured side
  panels, raised dark four-point star and oval bronze boss. The 23 low-sided rivet caps total 138 triangles;
  hidden stems and back caps are omitted. Front and back have distinct surface materials.
- Body geometry, rig, hand grips and clip timing remain unchanged. Dropped-prop floor clearance was refreshed.
  All runtime and portable GLBs, packed authoring blend and review assets are re-exported.

| LOD | Body | Axe | Shield | Combined |
|---|---:|---:|---:|---:|
| 0 | 11,511 | 732 | 358 | 12,601 |
| 1 | 5,754 | 270 | 274 | 6,298 |
| 2 | 2,067 | 132 | 64 | 2,263 |
| 3 | 685 | 47 | 14 | 746 |

LOD0 adds **778 triangles / 6.58%** over the installed previous revision, entirely in held equipment.
Gear uses one authored 1024-square atlas set; each self-contained attachment embeds its required maps.

**integration/actors.yml changed:** only the three attack_melee impact values **0.719 -> 0.715 s**.
The actual new blade's 240-Hz measured peak is **0.714583 s** (23.848 m/s, forward 0.6459, edge lead 0.9987).
Scale, z/yaw offsets, clips, sockets/attachments, stride and look settings are identical. Replace the three
installed GLBs and apply those timing values; no shared files were edited here.

Repeated checks: **8 clips, 682 samples at 48 Hz**, G4 arm p99 **1.4948x**, G5 fingers **2.4189x**, sampled
arm/prop penetration **0 mm**, head/pauldron **4.9838 mm**, motion-trace **0 flags**. Per-clip posture passes;
blade gate passes with the new actual mesh. Export parity remains **0.0233 mm** at keyed frames and
**4.169 mm** between keys. Body/head UV measurements are unchanged; all new gear UV triangles have nonzero
area. Three.js viewer **24/24 switches**, no console errors; all eight clips played at 1x and 0.5x.
Front/side/three-quarter sheets have been regenerated and inspected.

Visual evidence: [three tiers](review/round1/tiers.png), [axe](review/round1/details/axe.png),
[shield](review/round1/details/shield.png), [final corpse](review/round1/viewer_c/corpse.png),
[playback](review/round1/viewer_c/playback_review.json), [viewer check](review/round1/viewer_check.json).
Numeric reports remain at the gate links above. [Artifact manifest](export/artifacts.json) and
[static handoff validation](review/handoff_validation.json) describe the current revision.

| Changed export | Bytes | SHA-256 |
|---|---:|---|
| [export/mm6_figc.glb](export/mm6_figc.glb) | 10,457,992 | 52a7298d6d3d42e3eafc9c3b114fe4436793a98da58dd3b1d0ab6e08217c7751 |
| [export/mm6_figc_axe.glb](export/mm6_figc_axe.glb) | 862,424 | d11e91542d019db391f2a3c4abd2c75681b651c2009613435d10ae469ce72c21 |
| [export/mm6_figc_shield.glb](export/mm6_figc_shield.glb) | 2,179,604 | fc648ca4cd18579cbbf86c35e7326c3a68b3019d9d177d906c041834065a53fc |
| [export/mm6_figc_portable.glb](export/mm6_figc_portable.glb) | 14,632,708 | 6701b0c37aa359845e80c8dc9b2a809f20c98549bb75fa443fc53f6af6fbbb2a |
| [export/mm6_figc_authoring.blend](export/mm6_figc_authoring.blend) | 10,579,511 | fa439dc3e86e0a6c99fbe84885e3afecc65217dca7dbe0486c032097df59abce |

No blocking rig/export fault remains. **Artistic acceptance and new in-game validation are pending with the
orchestrator.** The previously documented extreme single-edge stretch and fractional-frame export limits
remain; this equipment/material correction does not conceal or broaden those gates. No game launch, build,
asset installation, shared-file edit or commit occurred in this review session.


## Review round 2

**Technical handoff complete; ready for orchestrator re-integration. Artistic acceptance is pending.**
The installed round-1 exports are preserved under review/round2/before/. This review uses **zero additional
Meshy credits: 30/100 total, 70 remaining**. No assets_dev installation, shared-file edit, build, game launch or commit.

The four standalone HD designs were generated with **Codex built-in image generation**, using native figcsta0/1
frames as the silhouette/palette references. Prompts, source/output hashes and selection are retained in
[references_hd/round2_equipment](references_hd/round2_equipment/provenance.json). The side/front designs are
projected onto carefully modelled surfaces and baked into a shared **2048-square gear atlas**; quarter views
supply the construction reference. No procedural flat-colour fallback or new Meshy model is used.

- **Axe, 2,440 triangles:** tapered double crescent forgings, distinct ground bevels and cutting highlights,
  thick oval socket, four riveted langets, wood shaft, eight raised leather turns and bevelled end cap.
  Forge marks, scratches, oxide and worn wrap edges come from the generated painted design. The grip keeps
  its fitted 11.5 mm radius; triangles go to the silhouette, bevels, socket and wrap.
- **Shield, 1,476 triangles:** native tall coffin outline, curved/domed wood core, raised bevelled iron rim,
  18 visible domed studs, oval boss, painted four-point star and worn tier-coloured insets. The actual crown
  is 47 mm. The back and handle supports are inexpensive; buried stud stems/back caps are omitted.
- **Steel:** body, head and equipment use the same dull-grey treatment across A/B/C. Numeric calibration
  sampled **2,233 native armour pixels**, with explicit helmet/pauldron/bracer/greave rectangles and saturation
  filtering. Native median linear luminance is **0.07227**; final mapped body/head/gear medians are
  **0.03652 / 0.03595 / 0.03515** (encoded sRGB approximately 0.21). Highlights cap at 0.15 linear before
  the slight neutral-grey hue. Armour specular mask is 0.28, roughness 0.72.
  Under the unchanged viewer lighting, the same bracer crop drops from **0.493 to 0.266 median sRGB**,
  against the native bracer sample about 0.247. Reports:
  [native/material calibration](review/round2/steel_luminance.json),
  [same-camera viewer comparison](review/round2/viewer_steel_luminance.json).

Body geometry, fitted hands, 58-bone rig and eight source motions are retained. New prop geometry was floor-fitted
for Death/Dead and re-exported. **integration/actors.yml is byte-for-byte unchanged from round 1**
(SHA-256 `888dbde5b62081df84317a05fb50229099096c8dd46e270f4f1fa1d75930732b`): scale, offsets, attachment
nodes, clips and impact **0.715 s** stay the same. Replace all three runtime GLBs; no binding merge is needed
if the orchestrator installed round 1's 0.715-second markers.

| LOD | Body | Axe | Shield | Combined |
|---|---:|---:|---:|---:|
| 0 | 11,511 | 2,440 | 1,476 | 15,427 |
| 1 | 5,754 | 1,150 | 808 | 7,712 |
| 2 | 2,067 | 431 | 273 | 2,771 |
| 3 | 685 | 131 | 87 | 903 |

LOD0 adds **2,826 triangles** over round 1, entirely in equipment, within the requested 1–3k per prop.
The larger painted gear atlas increases the self-contained runtime files to approximately **27.35 MB combined**.

Repeated gates on the exported mesh: **8 clips / 682 samples at 48 Hz**, G4 arm p99 **1.4948x**, G5 finger
maximum **2.4189x**, sampled arm/prop penetration **0 mm**, head/pauldron maximum **4.9838 mm**, posture checked
for every role, source/export motion **0 flags**. At 240 Hz the actual blade reaches its fastest target-facing
cut at **0.714583 s**, **23.7068 m/s**, forward **0.6459**, cutting-edge lead **0.99868**. Export parity remains
**0.0233 mm** on integer frames and **4.169 mm** between keys. New gear UV triangles all have nonzero area.
The viewer passes **24/24 tier/clip switches** with no console errors; all eight clips were played at 1x and 0.5x.
[Archived round-2 gates and export input hashes](review/round2/gates/input_hashes.json).

Review evidence: [designs beside final props](review/round2/prop_comparison.png),
[axe in viewer](review/round2/details/axe.png), [shield in viewer](review/round2/details/shield.png),
[three tiers](review/round2/tiers.png),
[full playback](review/round2/viewer_c/playback_review.json),
[viewer check](review/round2/viewer_check.json). Front, side and three-quarter clip sheets were regenerated.
The standalone prop front/quarter renders are in review/round2/details/.

| Changed export | Bytes | SHA-256 |
|---|---:|---|
| [export/mm6_figc.glb](export/mm6_figc.glb) | 10,306,876 | ef555c96d179c14dfbdc5f7a260f565ef9cba107386112a180c264744ff12e3e |
| [export/mm6_figc_axe.glb](export/mm6_figc_axe.glb) | 9,632,400 | 1720e579c47bb9416e95b6a4832df62940e78c206f2de72eafb9e2d8b546be36 |
| [export/mm6_figc_shield.glb](export/mm6_figc_shield.glb) | 7,408,860 | 21d484a60363fa2f2c70c60d2976e423777164d9d43c7d7e2177cdfd8cb82ee9 |
| [export/mm6_figc_portable.glb](export/mm6_figc_portable.glb) | 25,372,440 | fec70bbf0a318866eeea27edbbefbc13194e7ec382f4c5a9ef9762784352cafd |
| [export/mm6_figc_authoring.blend](export/mm6_figc_authoring.blend) | 18,201,295 | 576f0b864e1ca32246be92035dbfac23ecb5ac1a172e5517934dbad0e19747a8 |

| New HD design | SHA-256 |
|---|---|
| [references_hd/round2_equipment/axe_side.png](references_hd/round2_equipment/axe_side.png) | 3c98810cb5e3a39a1cccc17553cfef12fe1bd9620da1a9d345ac8859e5d8cc00 |
| [references_hd/round2_equipment/axe_quarter.png](references_hd/round2_equipment/axe_quarter.png) | deb2bb115ab9e0dc076bf80eb1c7dc4f8919e5ad91ac7bae1bc6cfc8c9beb772 |
| [references_hd/round2_equipment/shield_front.png](references_hd/round2_equipment/shield_front.png) | 34e1e97f0bbd3dc10447bbb32b3e18bc035bb1bf7e8665092cbde730a2c30e3b |
| [references_hd/round2_equipment/shield_quarter.png](references_hd/round2_equipment/shield_quarter.png) | 65036ca64af26f9680089cab4d12f666e29499a3ea1fe188b24eca4a774c1230 |

The corresponding `.prompt.txt` files contain the exact prompts. Implementation files are
scripts/repair_equipment_r2.py, gear_textures_r2.py, calibrate_steel.py and render_props_r2.py; export_runtime.py
and viewer_tiers.py now consume the painted gear atlas. [Round-2 changed-file hashes](review/round2/changes.json)
include the texture maps, ramps, prompts and scripts; [artifact manifest](export/artifacts.json) records final counts.

Reproduction from the retained round-1 master: run gear_textures_r2.py, calibrate_steel.py,
repair_equipment_r2.py in guarded Blender, export_runtime.py, prepare_actor_glb.py, lods.py, runtime_finish.py,
gates_exported.py and check_round2.py, then viewer checks and sheet composition. Each Blender invocation must
use the lease wrapper and `--threads 4`. No paid job needs replaying.

No blocking measured rig/export/viewer failure remains. In-game material response, additive head look, stride,
LOD transitions and indoor/outdoor regression remain the orchestrator's checks. The previous extreme single-edge
stretch and fractional-frame export limits remain documented above. No artistic approval is implied.

## Texture size (orchestrator, 2026-10-13)

Oversized embedded maps were scaled down (largest side capped at 2048, Lanczos) with no visible difference at close range;
the previous export is kept as `export/mm6_figc_prelarge_backup.glb`. Geometry, rig, clips and materials are unchanged.
