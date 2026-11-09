Angel A / mm7_m150: PARTIAL CANDIDATE, NOT ACCEPTED.

Descriptors 199, 200, 201; native palettes 151, 152, 153. 23/23 whole-animation/view jobs have a return; 22 are currently selected as candidates. 124/124 native bitmaps have provisional 2× physical masters. No native timing, mirrors, aliases, groups or unused-art playback bindings were changed.

Builtin imagegen returned HTTP 429 usage_limit_reached. Its reported reset is 2 October 2026 at about 14:24 Prague / 12:24 UTC. Exact successful attempts and untouched raw returns are in redo_2x/run.json; actual API failures have individual review/*_imagegen_failure.json records. Jobs not submitted after exhaustion are explicitly distinguished in review/generation_blocked.json.

Read session_status.json and redo_2x/review/decision.json before using any artwork. Nominal sheet sampling is provisional until independent actual-art anatomy/placement measurements pass. Physical enlargement never counts as additional generated detail. All available pose/palette/mask overviews and representative 100% detail/alpha samples were inspected; final per-pose detail, independent placement and material ownership acceptance remain incomplete.

- One complete attack/view-1 return is rejected: m150af1 has a clipped outer feather tip (six boundary pixels above alpha 64, maximum alpha 129). A full-cycle replacement with six native pixels of padding is prepared; its imagegen call hit the usage limit.
- Pose-dependent body/wing placement shifts remain in nominal sheet registration. Equipment exposure in rear-oblique poses needs closer comparison. No limb or pose warping was applied.
- All 124 unique candidate poses, 372 palette appearances and 124 masks were inspected in overviews. Representative delivered pixels and dark/light edge closeups were inspected; per-pose 100% detail and independent landmark acceptance are still pending.

Resume the exact prepared prompts and three reference paths listed in redo_2x/run.json with built-in imagegen. Every prompt already starts with the required MM7 restoration context. Each job includes the complete native cycle at its stored view, untouched colour/alpha, a separate outline-only alpha-boundary guide and old same-family detail for appearance only. Submit the whole cycle and require one full returned sheet. Do not split or retry just because nominal sampling is below 2×. Raw successes are staged with the existing stage_result.py tool, preserving attempt prompt/reference hashes. Preserve the current shared native-coordinate crop and reviewed alpha separation policies when extracting/registering.

The active attack_1_sheet job has six-pixel-padding replacement references and NO selected raw. Its older clipped v1 remains in diagnostic candidate atlases only. review/diagnostic_run_snapshot.json records that v1 preparation, so its registration is not confused with the pending v2 crop/grid. Never select the rejected v1 to claim completion. After a valid v2 arrives, re-extract the whole sheet, refresh registration, atlas/palette/reviewer artifacts and replace the diagnostic quality flags.

The shared reviewer metadata is redo_2x/shared_reviewer.json, with manifest.json as the authoritative staged MM7 atlas contract. It converts the existing MM7 descriptor/direction/variant metadata for the shared serve.py; PNG artwork and exact sequences are retained. It does not register an accepted family or change global queues. From the repository root, check/serve this candidate explicitly:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --package level_generation/creatures/mm7_mm8_packed_outline/session_mm7_01/mm7_m150/redo_2x/shared_reviewer.json \
  --state-dir level_generation/creatures/mm7_mm8_packed_outline/session_mm7_01/mm7_m150/review_state --check
```

Remove --check and choose a free --port to open the existing reviewer. It reports complete manifest coverage, which is separate from acceptance; the candidate labels and decision records remain NOT ACCEPTED. The generated viewer.html also shows native timed playback, all mirrors, palette presets and masks.

Before freezing: finish missing/replacement sheets, independent all-pose joints/body/placement checks, every pose at 100% material detail, actual alpha contours on light/dark, all palettes and mask ownership, then re-export with shared tools and bind complete local acceptance to final hashes. Keep older accepted packages, shared tools/skills, global ledgers and runtime assets unchanged. Nothing here is installed into gameplay.
