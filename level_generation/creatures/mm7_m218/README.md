# MM7 Elf Spearman restoration

All 119 native unique frames are restored and reviewed for descriptors 250/251/252. All are referenced by native playback. Palette 220 supplies the sole generated blue-violet loincloth base; deterministic enhanced-art cloth masks derive native palette 50 green and palette 221 red. Green vines and crown, pale skin, dark hair, brown leather and spear shaft, and silver spear point remain protected. Original assets are unchanged and this package is staged offline only.

## Native coverage and timing

Five stored views retain mirrored directions 5–7. Standing has five images, walking eight poses per view, attack/shoot seven, and hit six. Death plays na0, nb0, da0, db0, dc0, dd0; corpse holds xa0. Fidget plays fa0, fb0, fc0, fd0, fd0, fc0, fb0, fa0: the last two entries hold 500 ms, all others 125 ms. All other action entries are 125 ms. Death, corpse and fidget preserve Image1 reuse across all eight directions. Native logical size 256×256, bottom pivot (128,256), Center and descriptor scale 1 are preserved.

## Artwork and processing

18 selected built-in imagegen sheets, 20 raw outputs retained. Standing v2 removes an invented second spear point; attack a_3 v2 corrects the same issue in its third pose. Exact prompts, references, hashes and accepted checkpoints are retained in generation.json, prompts/submitted and raw. Generated sheet dimensions and registration scales are recorded separately from the 2× export resolution.

Uniform tone 0.80 preserves shadow weight. Magenta extraction, warm contour protection and premultiplied Lanczos resizing retain foliage and weapon edges. Connected pose extraction uses shared anatomical scale per sheet and native baseline anchoring. A reviewed raw-sheet ownership rectangle [360,640,568,775] keeps the complete detached spear with dd0 instead of assigning a tiny tip fragment to xa0; config.json preserves this correction. review/death_extraction_repair.png verifies both repaired poses.

R8 soft masks follow enhanced blue-violet cloth chroma and connected support, with alpha-normalized Gaussian sigma 0.45. Fixed native ACT cloth fits use blue-dominant entries in 189–246, independently of frame shading. The base preset bypasses recoloring exactly. Native masks are not resized onto changed anatomy.

## Validation

Every native/restored frame and all 357 frame/palette combinations were visually reviewed in ordered action contacts. Light/dark edge closeups and the repaired death extraction were inspected. Offline browser captures cover mirrored red attack and green Image1 death. Atlas validation passes source hashes, full frame coverage, unclipped raw cells, exact crop/atlas reconstruction, valid mask weights, unchanged variant alpha, exact base bypass and native timing/flag preservation; zero residual candidates above 32. No unresolved demonstrated visual defect remains.

Decoded padded RGBA8 + R8 payload: 50,227,200 bytes (47.90 MiB); tight payload: 45,832,500 bytes. Page dimensions and placement are authoritative in manifest.json. Final reviewed artifact hashes are in review/acceptance.json.

## Reproduce offline

From the repository root, run these sequentially:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m218 --tone .80
python3 level_generation/creatures/mm7_m218/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m218
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m218
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m218
python3 level_generation/creatures/mm7_m218/review_variants.py
```

Open viewer.html directly for all palettes, masks and native timelines. Rebuilds require renewed visual acceptance.
