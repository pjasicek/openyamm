# MM7 packed outline session 07 — accepted restoration

All seven previously partial families are repaired and accepted after static visual review. **All eight assigned families are complete: 1,003/1,003 native bitmaps, 51/51 unused images, 210/210 whole-animation/stored-view or unused-art sheets and all 24 native palettes. No family remains partial; no tool-return job remains blocked.** The previously accepted Thief package remains unchanged.

| Family | Merged descriptor IDs | Native palettes | Frames | Whole sheets | Minimum actual detail | Acceptance |
| --- | --- | --- | ---: | ---: | ---: | --- |
| MM7 Roc A | 391–393 | 553, 554, 555 | 125 | 30 | 2.409× | Accepted |
| MM7 Sea Monster A | 394–396 | 395, 396, 397 | 158 | 27 | 1.489× | Accepted |
| MM7 Skeleton Warrior A | 397–399 | 63, 64, 399 | 124 | 28 | 2.442× | Accepted |
| MM7 Spider A | 400–402 | 66, 67, 68 | 124 | 28 | 2.117× | Accepted |
| MM7 Swordsman A | 403–405 | 70, 74, 409 | 116 | 24 | 2.164× | Accepted |
| MM7 Thief A | 406–408 | 84, 85, 86 | 124 | 23 | 1.656× | Accepted |
| MM7 Titan A | 409–411 | 91, 92, 93 | 116 | 23 | 2.010× | Accepted |
| MM7 Troglodyte A | 412–414 | 95, 96, 97 | 116 | 27 | 2.056× | Accepted |

Each selected sheet contains the complete native sequence for its action and stored view. Timing, mirrors, aliases, descriptor bindings, unused-art exclusion from playback and fractional anchors are preserved exactly. Masters are physically 2×. Sea Monster reaches 1.489× and Thief 1.656× actual detail on their lowest complete sheets, accepted under the authorized whole-cycle priority. Export interpolation is not counted as generated detail. All other families now reach at least 2× actual detail.

## Resolved visual findings

- Roc: compact complete flying cycles, faithful hidden rear head, uniform actual eye/ankle/crown calibration and reviewed whole-pose positions. Wing roots, neck/chest, feather fans, talon joints and tails checked independently. Masks protect gold talons, warm body feathers and beaks across palettes 553/554/555.
- Sea Monster: complete ten-step attack views, final rear hidden-mouth ownership and native long later tail steps. Actual snout, dorsal/caudal joints and hidden jaw-ring calibration; corrected later hit/collapse positions. Belly, teeth and lip colours protected in all palettes.
- Skeleton Warrior: complete raised-sword sheet with enlarged padding, helmet/skull/collapse calibration and body/debris placement. Clothing recolour excludes steel and arrow fletching in every pose.
- Spider: complete eight-leg cycles and unused art, native rear-head occlusion, actual body/leg-chain calibration, textured terminal hooks and protected eyes/warm legs. Palette 68’s purple band is native material, confirmed against original indexed colours; all palette/mask poses reviewed.
- Swordsman: native blue base palette 74, confirmed helmet equipment, independent helmet/shoulder/hip/boot and collapse/corpse placement. Steel, gold fittings and white cloth protected.
- Titan: protected weapons, actual crest/armor/joint scale and later collapse/debris positions. Uniform calibration measures at least 2.010× actual detail; all palettes/masks reviewed.
- Troglodyte: native digit/thumb ownership, thin tail, olive/cyan material coverage and complete hit/walk/attack/death/corpse repairs. Actual spine/sole/crown calibration and whole-pose grounding corrections; hand, scale, drool, tail and alpha poses reviewed.
- Thief: retained its prior complete local acceptance and unchanged package.

Every current pose was inspected in native coordinates using independent anatomical placement features. All native palette/mask poses and original-size 100% material/alpha contacts were inspected before freezing artifact-bound acceptance. Outlines guide geometry only; accepted art retains texture and natural shading. Review was static: **timed playback was not watched**.

## Export and audit

Each family’s `redo_2x/` contains checked 2× masters, aligned material masks, base/mask atlases, all native palette variants and exact placement/animation metadata. `review/acceptance.json` and `review/all_pose_review.json` bind complete local acceptance, resolved findings and measured sampling to current artifact hashes. All local run ledgers mark selected sheets accepted.

**325 submissions produced 317 archived complete-sheet returns and eight historical quota errors. All quota-blocked jobs recovered.** Superseded returns, prompts, references and failures remain preserved. Initial sheets used a common native-coordinate union crop with two native pixels of alpha padding; demonstrated edge faults used six or eight. Every submission attached untouched native colour/alpha, a matching separate outline-only guide and same-family detail art. Every prompt begins with the required MM7 restoration context.

Final audit verifies unchanged hashes for 1,003 source BMPs, 24 native palette files, 19 native frame-group files, 32 older-project metadata files, the merged descriptor table and remaining inventory. All 317 preparations exactly reconstruct their native colour/alpha and outline-only boundaries; every raw, prompt and reference hash verifies. See [final_source_integrity.json](final_source_integrity.json).

Browser rendering passed all 1,536 palette/action/view clips and 3,009 palette-frame images against current manifests. This verifies loading and exported sequences; visual acceptance comes from the separate pose/material/palette review. Chrome closed cleanly. See [shared_browser_validation.json](shared_browser_validation.json).

## Shared reviewer

The unchanged shared reviewer loads the hash-pinned collection and shows eight accepted families in local review state.

```bash
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm7_mm8_packed_outline/session_mm7_07/mm7_m390/review_collection.json \
  --state-dir level_generation/creatures/mm7_mm8_packed_outline/session_mm7_07/mm7_m390/shared_review_state \
  --port 8897
```

Open <http://127.0.0.1:8897/> while the server is running. All writes remain under the assigned session staging directories. Source projects, older accepted packages, shared tools/skills, global ledgers and runtime assets were preserved. No gameplay installation or renderer changes were made.
