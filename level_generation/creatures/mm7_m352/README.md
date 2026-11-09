# MM7 human male peasant 1 — validated offline restoration

All 83 native unique frames are restored and validated across all nine native palettes (353–361), covering descriptors 358–366. Open `viewer.html` for native/restored playback, all stored and mirrored views, palette selection and masks. Assets are staged only; originals are unchanged and nothing is installed into gameplay.

The 13 accepted built-in imagegen sheets preserve the original dark-haired, bearded man, forest-green tunic, brass cuff studs, brown belt, gray-beige trousers and brown shoes. Exact prompts, native references, raw results, hashes and accepted checkpoints are retained in `generation.json`. One n_4 request failed with HTTP 400 and its identical retry succeeded; all accepted artwork is v1. No palette variant was separately generated.

Native coverage is 5 standing, 40 walking, 30 hit, 4 fidget, 3 falling and 1 corpse frames; all 83 are referenced. The native standing action has one pose, walk/attack/shoot reuse the same eight-pose walk, hit has six poses, death uses na0, nb0, da0, db0, dc0, and fidget plays fa0, fb0, fc0, fd0, fc0, fb0, fa0. Each timed native pose lasts 125 ms; the corpse holds. Stored views 0–4 and mirrors 5–7 are preserved. Image1 death, corpse and fidget reuse their native front frames for all views. Logical canvas 256×256, bottom pivot (128,256), scale 0.799988 and native flags are retained.

Processing uses the shared direct restoration scripts, tone 0.80, warm contour protection, core threshold 24, connected pose extraction and common per-sheet anatomical calibration. Alpha cleanup and premultiplied resizing produce the 2× aligned frames. RGB8 masks independently address tunic (R), hair (G) and beard (B), with soft enhanced-art boundaries. Fixed ACT fits recolor cloth; native tonal ramps recover the alternative hair and beard colors from the nearly black base. Base palette 353 bypasses exactly. Skin, eyes, belt, studs, trousers and shoes are protected. `head_bounds.json`, `beard_zones.json` and `head_boundary_corrections.json` preserve authored boundaries, including tilted heads and hair beside the neck. Mask weights are normalized and variant alpha is unchanged.

Runtime export comprises RGBA8 base and matching RGB8 mask pages at 2048×3773 and 2048×340, placement/animation/variant metadata and the self-contained offline viewer. Decoded shared atlas memory including packing is 58,963,968 bytes (56.23 MiB); the nine variants share those pages.

Review covered all 83 native/restored frames, all 747 frame/palette combinations, ordered action sequences, hair/beard boundary corrections, enlarged light/dark edges and browser captures of a mirrored white-haired walk and blue-tunic rear-oblique recoil. Earlier mask authoring diagnostics remain under `review/mask_authoring/`. Final contacts are `review/all_variants_*.png` and `review/comparison_*.png`. Package checks passed source hash preservation, complete coverage, unclipped raw cells, exact crop and atlas reconstruction, native timing/flags, exact base bypass, unchanged variant alpha and valid mask weights. Edge audits report zero residual candidates above 32.

To reproduce offline processing, run from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m352 --tone .80
python3 level_generation/creatures/mm7_m352/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m352
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m352
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m352
python3 level_generation/creatures/mm7_m352/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed acceptance hashes. There are no outstanding family blockers.
