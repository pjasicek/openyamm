Bat A / mm7_m158: PARTIAL CANDIDATE, NOT ACCEPTED.

Descriptors 205, 206, 207; native palettes 159, 160, 161. 17/17 whole-animation/view jobs have a return; 17 are currently selected as candidates. 116/116 native bitmaps have provisional 2× physical masters. No native timing, mirrors, aliases, groups or unused-art playback bindings were changed.

Builtin imagegen returned HTTP 429 usage_limit_reached. Its reported reset is 2 October 2026 at about 14:24 Prague / 12:24 UTC. Exact successful attempts and untouched raw returns are in redo_2x/run.json; actual API failures have individual review/*_imagegen_failure.json records. Jobs not submitted after exhaustion are explicitly distinguished in review/generation_blocked.json.

Read session_status.json and redo_2x/review/decision.json before using any artwork. Nominal sheet sampling is provisional until independent actual-art anatomy/placement measurements pass. Physical enlargement never counts as additional generated detail. All available pose/palette/mask overviews and representative 100% detail/alpha samples were inspected; final per-pose detail, independent placement and material ownership acceptance remain incomplete.

- All 17 whole-animation/view sheets have returned and 116/116 native frames are exported, but the family is NOT accepted.
- Folded and spread wing poses have different body/head placement and proportions. Actual-art mouth and far-ear measurements on wa0/wc0 show different residual translations and changed anatomical spans; see review/independent_placement.json and placement_standing_0_00.png. No per-pose resizing or warping was applied.
- All 116 candidate poses, 348 palette appearances and 116 masks were inspected in overviews; representative delivered detail and dark/light contours were inspected. Rear membrane/underbelly material ownership needs further checking. Per-pose 100% acceptance and corrected independent placement remain pending.

Resume the exact prepared prompts and three reference paths listed in redo_2x/run.json with built-in imagegen. Every prompt already starts with the required MM7 restoration context. Each job includes the complete native cycle at its stored view, untouched colour/alpha, a separate outline-only alpha-boundary guide and old same-family detail for appearance only. Submit the whole cycle and require one full returned sheet. Do not split or retry just because nominal sampling is below 2×. Raw successes are staged with the existing stage_result.py tool, preserving attempt prompt/reference hashes. Preserve the current shared native-coordinate crop and reviewed alpha separation policies when extracting/registering.

The shared reviewer metadata is redo_2x/shared_reviewer.json, with manifest.json as the authoritative staged MM7 atlas contract. It converts the existing MM7 descriptor/direction/variant metadata for the shared serve.py; PNG artwork and exact sequences are retained. It does not register an accepted family or change global queues. From the repository root, check/serve this candidate explicitly:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --package level_generation/creatures/mm7_mm8_packed_outline/session_mm7_01/mm7_m158/redo_2x/shared_reviewer.json \
  --state-dir level_generation/creatures/mm7_mm8_packed_outline/session_mm7_01/mm7_m158/review_state --check
```

Remove --check and choose a free --port to open the existing reviewer. It reports complete manifest coverage, which is separate from acceptance; the candidate labels and decision records remain NOT ACCEPTED. The generated viewer.html also shows native timed playback, all mirrors, palette presets and masks.

Before freezing: finish missing/replacement sheets, independent all-pose joints/body/placement checks, every pose at 100% material detail, actual alpha contours on light/dark, all palettes and mask ownership, then re-export with shared tools and bind complete local acceptance to final hashes. Keep older accepted packages, shared tools/skills, global ledgers and runtime assets unchanged. Nothing here is installed into gameplay.
