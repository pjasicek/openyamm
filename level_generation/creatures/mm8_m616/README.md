# MM8 Bone Dragon restoration

Staged restoration of all 135 unique native m616 BMP frames: 115 referenced and 20 additional stored poses, with no missing or aliased files. All native actions, five stored views, eight runtime directions, timing, mirrors, logical 256x256 size and anchor flags are retained. Nothing is installed into gameplay.

Open `viewer.html` offline for native/restored/mask comparison, playback, frame stepping and direct stored-pose inspection. Bone Dragon has one native palette, 616; matching R8 masks have zero recolor coverage and base artwork bypasses recoloring exactly.

## Deliverables

Six RGBA8 base atlas pages and six matching R8 mask pages at 2x runtime scale. Placement, native animation bindings and palette metadata are recorded in `manifest.json`, `animations.json`, `variants.json`, `sources.json` and `validation.json`. Decoded base-plus-mask packing is 111144960 bytes (88915968 RGBA + 22228992 R8); tight storage is 80507470 bytes, with 30637490 bytes packing overhead.

## Reproduction and evidence

Twenty-one base-art batches cover every native pose. All 21 original sheets and two rear-attack repair revisions remain under `raw/`. Exact selected built-in imagegen prompts, reference order and hashes are in `generation.json`; rejected results and identity acceptance remain under `checkpoints/`. Rear-attack revision 3 corrects invented frontal facial sockets while retaining the fading blue breath in the seventh pose.

`process.py` extracts fixed native cells using local magenta matte unmixing with core tolerance 20/255, then premultiplied Lanczos resampling. Identity luminance multiplier 1.0367130986885624 is frozen across actions. RGB-only contour cleanup uses measured per-frame native magenta, cyan and green bounds from `native_frame_edge_limits.json`; this protects blue attack breath while removing demonstrated green fringe on gray bones. Alpha is unchanged by this color repair.

`calibrate.py` uses a shared similarity transform per action/view sheet. Death view 2 needs a common second-row translation [0,+38] physical pixels at 2x; flight view 2 needs [+13,0]. Identity and all five flight views retain exact native-cell scale and origin following visual endpoint review. No independent pose recentering is applied. Registered masters are 576x576 with origin [-32,-32]. Original diagnostics and pre-correction contacts are retained.

`tone.py` restores alpha-normalized native coarse RGB (Gaussian sigma 7px) plus 0.7 generated fine detail. Enhanced alpha and geometry are retained. Native silver-gray bones, lavender shadows, torn charcoal wing membranes and blue attack breath remain authoritative. `materials.py` records the single-palette configuration and produces matching zero-coverage masks without inventing alternate colors.

`package.py` retains four-pixel crop padding, three-pixel hidden RGB/coverage bleed and sixteen-pixel aligned gutters without mipmaps. Checks cover native source hashes, full native file coverage, exact crop reconstruction, atlas extraction, matching mask placement and base bypass. All 135 frames pass native-aware edge-spill checks at cleaned, aligned and atlas stages. Visual evidence includes 21 registration, 21 native/final and 21 palette/mask contacts, magnified edges, tone comparisons and an offline viewer capture. Browser checks pass 135 base-palette decodes, 135 stored poses, 192 native tracks and 1272 timing boundaries.

Run `python3 level_generation/creatures/mm8_m616/rebuild.py` from the repository to reproduce from retained selected raw outputs and frozen settings. Rebuilding does not grant acceptance: inspect changed contacts, run `browser_checks.py` through the authorized offline wrapper, renew `review/decision.json`, run `finalize.py`, then refresh `inventory_remaining.py`. `review/acceptance.json` seals reviewed artifact hashes; stale or missing evidence is incomplete.
