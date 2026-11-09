# Authorized complete redo — active run

User authorized all 56 insufficient MM6 families, generation and offline processing without per-family approval. Stage only; installed packages remain unchanged. See [PROGRESS.md](PROGRESS.md), [WORKFLOW.md](WORKFLOW.md) and [inventory.json](inventory.json).

## Current checkpoints (2026-09-14)

- Archer `mm6_arc1/redo_2x`: VALIDATED, 58 frames, minimum actual sampling 2.304, runtime 2x. Acceptance and artifact hashes frozen. Do not re-export casually: export resets review state. Native blue neckband retained; dark bowstrings repaired. Read review_notes.md for motion review method and interpretive limits.
- Barbarian `mm6_bar1/redo_2x`: VALIDATED, 57 frames, minimum 2.390, runtime 2x. Purple-safe local contour repair preserves leather. All blade axes reviewed, eight corrected; final masks hash-bound to aligned alpha. Separate static-view calibration documented; animated poses use common batch scales. Acceptance frozen.
- Bat `mm6_bat/redo_2x`: VALIDATED, all 78 poses, minimum measured generated detail 2.0934959, runtime 2x. Final native metadata/atlas/variant checks and 36 distinct browser playback bindings pass. Hash-frozen acceptance exists. Read review_notes.md for explicit manual-landmark uncertainty, attack overlap scale evidence and interpretive silhouette limits. Do not re-export or regenerate accepted Bat assets casually.
- Beholder `mm6_bh/redo_2x`: VALIDATED, all 48 poses, minimum generated detail 2.2992701, runtime 2x. 36 native browser playback bindings passed; final all-pose three-palette review and acceptance frozen. Read review_notes.md for shared-pose scale calibration, manual annotation uncertainty, fixed tone, and corrected enhanced iris/flare masks. Clipped bhwlke2 from walk_2_redo_01 was replaced by its complete duplicate in walk_2_redo_02. Do not re-export accepted assets casually.
- Bloodsucker `mm6_bld/redo_2x`: VALIDATED, all 78 native poses, minimum generated detail 2.1951219512, runtime 2x. 36 native browser bindings passed; all native/raw, common-crop motion, unbound poses, 234 palette images and light/dark edge composites reviewed. Acceptance frozen. See review_notes.md for manual landmark uncertainty, retained anatomy-distance flags and interpretive contours. Rear-flight hanging tail corrected in v2; wrong-mouth duplicate in final unused sheet excluded. No gameplay installation.
- Werewolf `mm6_wfigt1/redo_2x`: VALIDATED. Eight insufficient unbound poses redone at minimum 2.5329x; 55 adequate poses retained byte-for-byte, combined 63-pose minimum 2.0287x. All 42 native browser bindings and full combined motion/variant review passed. New heel anchors and retained provenance are documented in review_notes.md; acceptance frozen.
- Air Elemental `mm6_aie1/redo_2x`: VALIDATED, all 24 native poses, minimum generated sampling 2.4909091x, runtime 2x. Fifteen browser bindings passed. Native wind narrowing/fade, all three palettes, edge composites and common-crop sequences reviewed; acceptance frozen. Read review_notes.md for direct native-core calibration (failed SIFT rejected), diffuse-tip uncertainty and smoother ribbon interpretation.
- Demon Queen `mm6_qfi/redo_2x`: VALIDATED, all24 native poses, minimum generated sampling2.2654028x, runtime2x. Twenty selected RGBA sheets,26 retained raw versions. Five browser bindings, all16 overlap panels, all-pose material/edge/native-motion review passed; acceptance frozen. See review_notes.md for corrected attack/collapse poses and boundary repair, fixed tonal policy and manual-anchor limits.
- Other48 redo families remain pending. Redo ledger:8 validated,48 pending. Canonical inventory:12 adequate MM6 families(4 retained +8 validated redo),48 remaining.

## Bat-specific findings

Standing sheet2 first overlap has the wrong front/rear view: discard that duplicate and retain batwaa3 from standing sheet1; second pose batwaa4 is usable. Walk1 sheet2 v2 repaired a clipped wing. Unused0 sheet2 v1 had wrong-facing batsta4 (second cell); v2 correctly shows the back. Its apparent undersizing was traced to a knee mislabeled as a foot: fivefold native review corrected the foot annotation to y237 in the panel. Keep v2 selected. Draft batst colors are stippled even with embedded palette; no SFT palette assignment exists. Follow native silhouette/pose and accepted identity materials, with explicit stored-view order. Do not add unused poses to playback.

Some September14 sheets arrived with genuine alpha despite magenta prompts. THE USER NOW PREFERS TRUE TRANSPARENCY. Never request or accept a painted checkerboard. extract_run.py preserves supplied alpha and uses it for gutters; it must not convert transparent background to opaque black. Skip matte extraction for supplied alpha, but check missing thin details and edge RGB. Retain valid historical magenta sheets and their recorded extraction settings. prepare_run.py now requests true alpha for future families. Exact submitted prompts in attempts are immutable.

Bat native flight clearance must be preserved; do not align feet to a constant floor. Native process.py records overall gain .82 and explicit pose/view wing shadow factors. Adapt its tonal policy to new enhanced wing masks. No per-frame histogram normalization. Scale must be anatomical, measured from delivered pixels, strictly greater than 2 in both axes.

## Resume and ownership

Use the pipeline's current **lean default** for new work: static screening, compact visual sequence/detail/edge/variant
contacts, existing processing tools and one artifact-bound acceptance. Shared-template HTML export uses no API calls
and can run automatically; browser traces are optional. The historical browser evidence below describes already
completed work; it is not a new-work gate.
See [lean acceptance record](WORKFLOW.md#lean-acceptance-record).

prepare_run.py verifies and reuses existing runs instead of overwriting edited prompts. stage_result.py PROJECT JOB RAW copies outputs and hashes exact prompts/references. It now locks the shared ledger and atomically writes it; same-output staging is idempotent. A race between simultaneous staging calls lost two ledger entries although their raw PNGs existed; attack_redo_04 and hit_redo_02 were explicitly recovered from unchanged source outputs. Submit 2–4 ready image calls, then stage their results sequentially. No separate API or background generation worker.

extract_run.py PROJECT -> cleaned cells. register_archer.py and register_barbarian.py are family-specific, not general alignment. Reuse applicable tools; add special processing only for demonstrated unsupported geometry/materials. export_run.py PROJECT -> staged atlases, contacts, numeric checks and a cheap shared-template viewer; it resets review status. --skip-viewer omits the HTML export. Review every sequence contact, mask/variant and edge view plus representative 100% detail. freeze_review.py PROJECT accepts the lean review/decision.json tied to the manifest and inspected contacts, without notes or browser trace. Historical browser-backed decisions remain supported. It never infers artistic approval.

After acceptance, run refresh_progress.py and ../inventory_remaining.py. Historical installed below-2x audit remains separate from reviewed staged replacements. Do not rewrite its canonical paths to staged roots blindly. Do not claim completion from raw generation, manifest existence or sampling alone.

Current raw/checkpoint audit: audit_run.py verifies every selected raw, delivered dimensions, exact submitted prompt and reference hashes, and reports supplied-alpha sheets. Counts change as calls finish; use audit_run.py and progress.json instead of stale prose counts. Final outputs must be copied into the workspace. Active tool calls are session-local and are not a persistent background worker.

## September 14 registration review additions

`prepare_bat_landmarks.py` creates diagnostic coordinate panels; `review/anatomy_points.json` records manually matched anatomical points and hashes. Display fits must never become registration scales. Occluded rear heads use explicit foot anchors. `calibrate_bat_overlaps.py` records matched features between attack split sheets; correspondence panels were visually reviewed and only the uniform scale ratio is used. It resets its review status when rerun. `register_bat.py` applies these measurements, fixed native tonal policy and enhanced wing masks, preserving native canvas and flying clearance. Its remaining diagnostic disagreements are retained in review/registration_concerns.json. `review_bat_sequences.py` renders native and restored motion strips in a common crop. Animated flight/attack/hit/falling sequences and all static drafts have been inspected; noted pose corrections are complete. Bat review and acceptance are frozen. Do not rerun generation, registration or export scripts on the accepted Bat package without a demonstrated new defect.

## Further extraction and mask findings

extract_run.py has explicit opt-in connected-body extraction for interleaved Bloodsucker flight silhouettes. These sheets have no straight empty row cut, even column-first. Exactly one major connected solid body per native pose is required; each delivered foreground pixel is assigned once, tiny adjacent islands go to their nearest body, and raw coordinates stay authoritative. This is not an automatic fallback and is not suitable blindly for fragmented death effects. Review extracted contacts and physical boundary clipping. True-alpha red speckles in the tool preview were alpha 1–2; light/dark composites after the reviewed floor4 cleanup were clean. Never judge low-alpha RGB by the raw tool display alone.

prepare_bat_landmarks.py now honors processing.json selected_frame_jobs for complete overlap-pose replacement. export_run.py updates its cleaned-frame symlink when such a selection changes, preventing stale provenance. Beholder iris masks require the native purple chroma search ROI (palette index range included face pixels), then a nearby enhanced purple component connected through its blue iris rim. Closest blue pixel alone can select the white catchlight; largest blue component can select the forehead. Both were visually caught and corrected before the Beholder freeze.

## Retaining adequate poses in a partial redo

Werewolf required only eight new stored poses; 55 adequate images were retained as independent copies.
register_werewolf.py records original registration and asset hashes in retained_from. export_run.py
verifies those sources and carries forward exact legacy generation provenance without fabricating
new imagegen jobs. Post-export byte equality was checked for all retained cleaned/aligned/mask files.
Do not use writable symlinks for retained images because packing refreshes their RGB padding.
