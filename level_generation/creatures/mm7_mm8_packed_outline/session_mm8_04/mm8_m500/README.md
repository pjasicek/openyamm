# Water Elemental A — accepted local restoration

35 complete packed animation/view sheets, 160 native files, 136 playback files and 24 unused files. Native descriptor IDs [76, 77, 78] and all native ACT palettes are preserved.

Checked physical masters are 2x. Minimum measured generated detail is 1.904348x; 1 reviewed whole-cycle sheet falls below 2x. Every pose, independent placement feature, palette/mask, exported alpha edge and 100% material detail was reviewed. See review/acceptance.json for frozen hashes and run.json for the actual ordered attachment paths, roles, hashes and every attempt.

10 RGBA8/R8 atlas pairs, 167,846,400 bytes uncompressed. Native aliases, timing, mirrors, fractional anchors and unused art remain preserved. No gameplay installation. Static chronological review; no timed playback claim.

## Accepted falling/collapse restoration v4

The clarified built-in imagegen prompt returned the complete five-frame front falling animation successfully. It describes loss of balance, two backward arches, the downward inverted-U fall and the lower final fold, with continuous opaque fish scales and pearly scale plating. Native colour and its matching outline remain the geometry authorities; the selected rear detail sheet supplies scale/fin materials only.

All five native poses, independent head/hand/body-arch/tail/coil features, 100% material detail, both palette variants and authored masks, cleaned/final-atlas alpha edges and exact native bindings/anchors passed review. The 1536x1024 RGBA return has genuine alpha. Whole-cycle calibration is 2.644231x; minimum registered generated detail across the five frames is **2.641975x**. Checked physical exports are 2x. Static chronology was reviewed; no timed playback claim.

[Native/restored falling pose and placement comparison](review/death_0_sheet_placement.png) · [complete returned sheet](raw/death_0_sheet_v4.png) · [prompt v4](prompts/death_0_sheet_v4.txt) · [actual submitted paths, roles, hashes and checks](review/death_0_v4_submission.json) · [100% raw/atlas edge detail](review/death_0_v4_edge_detail.png)

Actual attached input images, in order: [native colour](references/death_0_sheet_native.png), [matching outline-only anatomy](references/death_0_sheet_outline.png), [same-family scale/fin appearance](references/selected_rear_detail_v1.png). The separate outline is actually present in the tool arguments; it supplies geometry only, with material masks authored after generation.

The grid screen flagged small existing coil/wrist extremities crossing the nominal empty-cell boundary. [Actual light/dark alpha inspection](review/death_0_v4_grid_warning.png) and ownership reconstruction confirmed five sprites, no sixth pose or backdrop, and every original foreground pixel assigned once without clipping. No regeneration or alpha threshold removal was used.

All 155 previously accepted frame masters, masks, palette panels and registration transforms remain unchanged; valid artifact-bound reviews were resumed. Water is now complete locally at **160/160 native files, 35/35 whole sheets**, including all 24 unused native files without adding playback steps. The family minimum remains 1.904348x because one previously reviewed whole sheet is below 2x.

## Earlier accepted head/recoil correction v4

The built-in imagegen retry of the complete six-frame rear hit cycle succeeded. All six corrected head turns, head heights, neck/torso bends, unequal hand positions and lifted/lowering tail-fan poses were reviewed against the native sheet. The raw return is 1490x1055 RGBA with true alpha; measured whole-sheet calibration is 3.344907x and minimum registered detail across its six frames is **3.340136x**. Checked 2x physical masters, both native palettes, authored masks and repacked base/mask atlases are exported.

[Native/restored pose and placement comparison](review/hit_4_sheet_placement.png) · [100% raw/atlas alpha-edge detail](review/hit_4_v4_edge_detail.png) · [complete returned sheet](raw/hit_4_sheet_v4.png) · [prompt v4](prompts/hit_4_sheet_v4.txt) · [actual submission paths, roles and hashes](review/hit_4_v4_submission.json)

Actual attached input files, in order: [native colour](references/hit_4_sheet_native.png), [matching outline-only geometry](references/hit_4_sheet_outline.png), [detailed Water appearance](references/selected_rear_detail_v1.png), and [v3 edit target](raw/hit_4_sheet_v3.png). Native and outline geometry overrides the repeated heads in the detail/edit references. V3 remains a rejected return.

All 149 prior accepted physical masters, material masks, palette previews and registrations retain their previous pixels/transforms. Their valid pose/material reviews were resumed by SHA-256; six new poses were directly inspected, and every affected final atlas contact was inspected on light/dark backgrounds. Native aliases, timing, mirrors, fractional anchors and unused art bindings are preserved. Review used static chronology.

This correction added six native files, taking coverage from 149/160 to 155/160 before the accepted falling/collapse restoration completed the family.


## Historical material-specific retry v3

0/2 v3 retried whole sheets accepted. Coverage at that historical checkpoint: 149/160 native files. The accepted v4 hit correction adds six native files; the subsequent v4 falling/collapse correction adds the final five. Native-colour, matching outline-only geometry and same-family detailed appearance files were actually attached, in that order, on every retry. All submitted paths, roles, SHA-256 hashes, prompts, rejection messages and request IDs are in [retry_v3_submissions.json](review/retry_v3_submissions.json).

The following are the exact submission files, relative to this family folder:

| Sheet | Outcome | Prompt | Native colour | Outline-only | Appearance |
| --- | --- | --- | --- | --- | --- |
| hit_4_sheet | rejected in pose review | [prompt v3](prompts/hit_4_sheet_v3.txt) | [native PNG](references/hit_4_sheet_native.png) | [outline PNG](references/hit_4_sheet_outline.png) | [detail PNG](references/selected_rear_detail_v1.png) |
| death_0_sheet | imagegen safety rejection | [prompt v3](prompts/death_0_sheet_v3.txt) | [native PNG](references/death_0_sheet_native.png) | [outline PNG](references/death_0_sheet_outline.png) | [detail PNG](references/selected_collapsed_detail_v1.png) |

Returned sheets:

- [hit_4_sheet v3](raw/hit_4_sheet_v3.png) — rejected in pose review.

Alternative appearance files:

- [selected_collapsed_detail_v1.png](references/selected_collapsed_detail_v1.png)
- [selected_family_detail_v1.png](references/selected_family_detail_v1.png)
- [selected_rear_detail_v1.png](references/selected_rear_detail_v1.png)

The older mm8_m500 project contains sources.json and batches.json, with no generated sprite sheet or composite found. Existing generated same-family references from this session were retained; these do not replace missing native animation steps.



## Preserved historical reuse candidates

Both approximate adjacent-view candidates are now superseded by accepted native-view restorations. They remain preserved under [reuse_candidates.json](reuse_candidates/reuse_candidates.json) with their source pixels, masks, native palette variants, timing/placement provenance and review evidence. There are **zero active fallback slots** and no missing native frames.

| Target cycle | Historical source cycle | Frames | Current native restoration | Preserved approximate candidate |
| --- | --- | --- | --- | --- |
| death_0_sheet | unused_d_1_sheet | 5 | accepted falling/collapse v4 | [PNG](reuse_candidates/death_0_sheet_from_unused_d_1_sheet_base_2x.png) |
| hit_4_sheet | hit_3_sheet | 6 | accepted head/recoil v4 | [PNG](reuse_candidates/hit_4_sheet_from_hit_3_sheet_base_2x.png) |

Neither approximate candidate contributes to the accepted native coverage or playback. All native completion comes from the packed complete-sheet restorations with actually attached matching outlines. Nothing is installed into gameplay.
