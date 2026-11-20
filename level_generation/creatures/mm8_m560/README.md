# MM8 Wyvern restoration

Staged restoration of all 135 unique native m560 BMP frames (all 135 referenced; no missing or aliased files), covering standing, flight, attack, reaction, death and corpse poses in all five stored views. The three native actor bindings retain every action, timing, mirror and native Center/bottom-center anchor flag on the logical 256x256 canvas. Nothing is installed into gameplay.

Open `viewer.html` offline for native/restored/mask comparison, playback, frame stepping, all eight runtime views, three palettes and direct stored-pose inspection.

## Deliverables

Six RGBA8 base atlas pages and six matching R8 coverage pages at 2x runtime scale; native green/ochre palette 561, deterministic blue variant 562 and brown/red variant 563. `manifest.json`, `animations.json`, `variants.json`, `sources.json` and `validation.json` record placement, animation, native provenance and review checks. Decoded base-plus-mask packing is 104110080 bytes (83288064 RGBA + 20822016 R8); tight storage is 75428030 bytes, with 28682050 bytes packing overhead.

## Reproduction and retained evidence

`generation.json` records exact selected built-in imagegen prompts, reference order, raw outputs and hashes. Twenty-one base-art batches cover all 135 native poses; palette variants are never generated independently. The original 21 sheets and three localized rear-face repairs remain under `raw/`; rejection records, original identity acceptance and placement corrections remain under `checkpoints/`.

`process.py` extracts fixed native cells from the magenta sheets with local matte unmixing (core tolerance 16/255), then uses premultiplied Lanczos at the common native scale. A single identity luminance multiplier 0.9847410987248223 is frozen across actions. RGB-only contour repair allows measured native magenta/cyan chroma of 9/255 and removes only excess in the four-pixel contour band; alpha is unchanged.

Four generated second rows were too high: attack view 0 +68px, attack view 1 +43px, death view 0 +67px and death view 3 +43px at physical 2x resolution. Each is a common row translation, never independent pose fitting. `calibrate.py` uses one shared similarity transform per action/view batch; all identity and flight views keep exact native cell scale/origin after visual endpoint review rejected mass-driven flight shrink. All registered masters are 576x576 with origin [-32,-32].

`tone.py` restores native alpha-normalized coarse RGB (Gaussian sigma 7px) plus 0.7 of generated fine detail, retaining enhanced alpha/geometry. `materials.py` derives soft coverage from enhanced pixels using eight nearest native palette samples in (R-G, B-G, 0.5*luma709), inverse fourth-power weights and distance floor 2. Native palette deltas drive variants; base 561 bypasses recoloring exactly. Coverage follows enhanced material boundaries, with no spatial native silhouette/mask transfer.

`package.py` retains four-pixel crop padding, three-pixel hidden RGB/coverage bleed and sixteen-pixel aligned gutters without mipmaps. Export checks verify unchanged native source hashes, exact crop reconstruction, atlas extraction, matching mask placement and identical variant alpha. The offline browser checks exercise 405 variant decodes, 135 stored poses, 192 native animation/view tracks and 1248 timing boundaries. Complete registration, native/final and three-palette/mask contacts plus magnified edge patches are retained for visual review.

Run `python3 level_generation/creatures/mm8_m560/rebuild.py` from the repository to reproduce from selected raw outputs and frozen settings. Rebuilding does not grant acceptance: inspect changed contacts, run `browser_checks.py` through the authorized offline wrapper, renew `review/decision.json`, run `finalize.py`, then refresh `inventory_remaining.py`. `review/acceptance.json` seals the reviewed artifact hashes; stale or missing evidence is incomplete.
