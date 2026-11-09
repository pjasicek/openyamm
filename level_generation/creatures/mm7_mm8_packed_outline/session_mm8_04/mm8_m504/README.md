# Earth Elemental A — partial local restoration

152/160 native files restored and locally reviewed, using 34/35 whole animation/view sheets. 8 native files remain unresolved after recorded failed imagegen attempts. Every actual submission includes the matching outline; bootstrap exceptions are recorded.

2x physical masters; minimum measured generated detail 1.826962x. All available poses, independent placement features, palettes/masks, exported alpha edges and 100% delivered material detail reviewed.

Full native aliases, timing, mirrors, fractional anchors and unused art bindings preserved in draft_manifest.json; missing references remain explicit. No gameplay installation. See review/partial_acceptance.json and run.json.

## Explicit MM8 front-walk retry v7

The user-requested wording explicitly describes a **front walking animation of the Earth Elemental from Might and Magic VIII, made entirely of dark-brown rocks**. Built-in imagegen was submitted the complete eight-frame native front walk, its matching separate OUTLINE-ONLY guide and the accepted detailed same-family front-fidget sheet, in that order. The attempt was rejected at output with the nonspecific category “other”; no image was returned. Request ID: 5336be6e-7508-4679-8119-4ecb7f7cf31d.

Exact submitted files: [v7 prompt](prompts/walk_0_sheet_v7.txt), [native colour sheet](references/walk_0_sheet_native.png), [matching outline-only sheet](references/walk_0_sheet_outline.png), [detailed stone appearance](raw/fidget_0_sheet_v3.png). The actual tool arguments, roles, absolute file paths, SHA-256 hashes and full error are recorded in [run.json](run.json) and [partial_acceptance.json](review/partial_acceptance.json).

Accepted art, placement, palettes/masks and exports are unchanged: **152/160 native frames across 34/35 complete sheets**. The eight front-walk frames remain unresolved; no full-family acceptance or gameplay installation.

## Dark-brown stone clarification and complete-cycle retries

Earth now has **152/160 accepted native frames on 34/35 whole animation/view sheets**. Built-in imagegen returned the complete six-step oblique recoil and eight-step oblique walk after prompts described what the original already is: a creature made entirely of dark-brown stones, with angular opaque rock plates, mineral grain, huge rock fists and broad stone feet. Exact native colour and matching OUTLINE-ONLY files were actually attached on every attempt, followed by detailed same-family material art.

| Selected cycle | Accepted return | Minimum actual generated detail | Prompt | Native colour | Outline-only | Actual appearance input |
| --- | --- | --- | --- | --- | --- | --- |
| Oblique recoil, six poses | [hit v4](raw/hit_1_sheet_v4.png) | 2.584x | [prompt](prompts/hit_1_sheet_v4.txt) | [native](references/hit_1_sheet_native.png) | [outline](references/hit_1_sheet_outline.png) | [stone detail](references/selected_family_detail_v1.png) |
| Oblique walk, eight poses | [walk v6](raw/walk_1_sheet_v6.png) | 2.331x | [prompt](prompts/walk_1_sheet_v6.txt) | [padded native](references/walk_1_sheet_native_v5.png) | [padded outline](references/walk_1_sheet_outline_v5.png) | [accepted front-fidget detail](raw/fidget_0_sheet_v3.png) |

The oblique walk v4 return is preserved and rejected because the final lifted foot clips the right sheet edge. Its complete native/outline pair was regenerated with six native pixels of shared padding; v5 was rejected by imagegen and v6 returned with the complete foot. The selected recoil and walking returns have true alpha; remaining outer-border warnings contain only alpha below 32 and no clipped opaque anatomy. Both cycles passed every native pose and independent-placement review, 100% stone-detail review, all three native palettes (ACT504/506/507), authored masks and cleaned/exported alpha edges. The original 138 accepted frames and transforms remain unchanged.

Checked physical exports are 2x. Family minimum generated detail remains **1.826962x** from earlier reviewed complete cycles. Nine RGBA8/R8 atlas pairs use **155,257,600 bytes** uncompressed. Exact native timing, aliases, mirrors, anchors and all 40 unused native images are preserved; unused images are not added to playback. No gameplay installation.

Only the **eight front-walk frames remain unresolved**. All three front-walk attempts in this retry were rejected at output with the nonspecific category “other”, even with alternate detailed same-family references. No returned front-walk sheet or convincing older substitute exists.

Exact remaining submissions:

| Attempt | Prompt | Mandatory native colour | Mandatory outline | Actual detailed appearance |
| --- | --- | --- | --- | --- |
| Front walk v4 — rejected | [prompt](prompts/walk_0_sheet_v4.txt) | [native PNG](references/walk_0_sheet_native.png) | [outline PNG](references/walk_0_sheet_outline.png) | [stone detail](references/selected_family_detail_v1.png) |
| Front walk v5 — rejected | [prompt](prompts/walk_0_sheet_v5.txt) | [native PNG](references/walk_0_sheet_native.png) | [outline PNG](references/walk_0_sheet_outline.png) | [accepted fidget sheet](raw/fidget_0_sheet_v3.png) |
| Front walk v6 — rejected | [prompt](prompts/walk_0_sheet_v6.txt) | [native PNG](references/walk_0_sheet_native.png) | [outline PNG](references/walk_0_sheet_outline.png) | [new oblique walking sheet](raw/walk_1_sheet_v6.png) |

[run.json](run.json) records the actual submitted arguments, attachment roles/absolute paths/SHA-256 hashes, exact prompts, preserved rejected return and all safety errors/request IDs. [partial_acceptance.json](review/partial_acceptance.json) freezes the accepted subset and explicit missing frames. [Walk placement](review/walk_1_sheet_placement.png) and [recoil placement](review/hit_1_sheet_placement.png) compare every new pose to its native counterpart.

Both former approximate reuse candidates are now superseded by these accepted exact native-view whole sheets. Their art, masks and palette files remain preserved, with zero active fallback slots. Front walk still has no convincing older substitute.

## Historical material-specific retry v3

At that checkpoint, 2/5 retried whole sheets were accepted and coverage was 138/160 native files. Native-colour, matching outline-only geometry and same-family detailed appearance files were actually attached, in that order, on every retry. All submitted paths, roles, SHA-256 hashes, prompts, rejection messages and request IDs are in [retry_v3_submissions.json](review/retry_v3_submissions.json).

Newly accepted sheets have measured generated detail of fidget_0_sheet: 2.719x, unused_f_3_sheet: 2.854x. Both export checked 2x physical masters; the unused cycle remains outside native playback.

The following are the exact submission files, relative to this family folder:

| Sheet | Outcome | Prompt | Native colour | Outline-only | Appearance |
| --- | --- | --- | --- | --- | --- |
| walk_0_sheet | imagegen safety rejection | [prompt v3](prompts/walk_0_sheet_v3.txt) | [native PNG](references/walk_0_sheet_native.png) | [outline PNG](references/walk_0_sheet_outline.png) | [detail PNG](references/selected_family_detail_v1.png) |
| walk_1_sheet | imagegen safety rejection | [prompt v3](prompts/walk_1_sheet_v3.txt) | [native PNG](references/walk_1_sheet_native.png) | [outline PNG](references/walk_1_sheet_outline.png) | [detail PNG](references/selected_family_detail_v1.png) |
| hit_1_sheet | imagegen safety rejection | [prompt v3](prompts/hit_1_sheet_v3.txt) | [native PNG](references/hit_1_sheet_native.png) | [outline PNG](references/hit_1_sheet_outline.png) | [detail PNG](references/selected_family_detail_v1.png) |
| fidget_0_sheet | accepted local subset | [prompt v3](prompts/fidget_0_sheet_v3.txt) | [native PNG](references/fidget_0_sheet_native.png) | [outline PNG](references/fidget_0_sheet_outline.png) | [detail PNG](references/selected_family_detail_v1.png) |
| unused_f_3_sheet | accepted local subset | [prompt v3](prompts/unused_f_3_sheet_v3.txt) | [native PNG](references/unused_f_3_sheet_native.png) | [outline PNG](references/unused_f_3_sheet_outline.png) | [detail PNG](references/selected_family_detail_v1.png) |

Returned sheets:

- [fidget_0_sheet v3](raw/fidget_0_sheet_v3.png) — accepted local subset.
- [unused_f_3_sheet v3](raw/unused_f_3_sheet_v3.png) — accepted local subset.

Alternative appearance files:

- [selected_family_detail_v1.png](references/selected_family_detail_v1.png)

The older mm8_m504 project contains sources.json and batches.json, with no generated sprite sheet or composite found. Existing generated same-family references from this session were retained; these do not replace missing native animation steps.

## Historical reuse check of existing generated sheets

The former 14 missing frame slots had staged **approximate** alternatives from 2 complete same-family generated cycles. Every candidate retains a neighbouring stored view, one view step from the target. No candidate is an exact native-pixel duplicate or a newly restored target-view sheet; accepted native coverage at that checkpoint remained 138/160. Both candidates are now superseded and preserved; current accepted coverage is 152/160.

Packed 2x sheets, unchanged authored material masks, every native palette and exact target timing/placement provenance are listed in [reuse_candidates.json](reuse_candidates/reuse_candidates.json). Original accepted frame images, run jobs, bindings and atlases are preserved. These historical candidates are superseded by the newly accepted native-view sheets, remain preserved, and are not installed.

| Missing cycle | Existing source cycle | Frames | Source detail | Packed 2x candidate | Native/source/generated comparison |
| --- | --- | --- | --- | --- | --- |
| hit_1_sheet | hit_0_sheet | 6 | 2.588x | [PNG](reuse_candidates/hit_1_sheet_from_hit_0_sheet_base_2x.png) | [part 1](review/reuse_existing/hit_1_sheet_from_hit_0_sheet_00.png) · [part 2](review/reuse_existing/hit_1_sheet_from_hit_0_sheet_01.png) |
| walk_1_sheet | walk_2_sheet | 8 | 2.510x | [PNG](reuse_candidates/walk_1_sheet_from_walk_2_sheet_base_2x.png) | [part 1](review/reuse_existing/walk_1_sheet_from_walk_2_sheet_00.png) · [part 2](review/reuse_existing/walk_1_sheet_from_walk_2_sheet_01.png) · [part 3](review/reuse_existing/walk_1_sheet_from_walk_2_sheet_02.png) |

Earth front walk (view 0), eight frames: no convincing substitute. Front-facing attack, standing, fidget and hit art cannot preserve its alternating foot lifts and arm swings; the existing walking returns show the side/back. High native silhouette similarity to rear-view walking art does not provide the correct facing.
