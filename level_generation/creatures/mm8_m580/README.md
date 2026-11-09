# MM8 Dragon Turtle — staged restoration

Open `viewer.html` locally to compare the native actor with the restored atlases. All 135 native filenames are covered by 120 unique generated poses and 15 exact aliases. The 26 accepted sheets preserve five stored directions, eight logical views, native mirror flags, 256×256 logical canvases and bottom-center anchoring. All source files are referenced by native actor animations.

The three native actors are 136/137/138, with palettes 581/582/583 and frame scales 4/4.5/5. Standing and walking have eight 125 ms steps; attack and attack2 six; hit six; fidget four; death uses na0, nb0, nc0, da0, db0 and then the separate xa0 corpse. Exact native bindings, durations, reuse, flags and per-step glow are in `manifest.json` and `animations.json`. No missing directions or timing were invented.

Built-in imagegen produced the accepted base artwork. Exact prompts are in `prompts/`, unmodified outputs in `raw/`, and selected versions and rejected attempts in `checkpoints/`. Generated sheet dimensions and pose detail are recorded in `generation.json` and `registration.json`; 2× export size is independent of generated detail. Accepted identity v3 is the shared action-generation reference.

`process.py` preserves common native grid placement, extracts alpha, removes matte spill, applies the frozen identity tone and resizes with premultiplied Lanczos. `lighting.py` applies the documented coarse native illumination correction to demonstrated lifted shadows and warm veins without changing geometry or alpha. Uncorrected aligned masters remain available alongside accepted `final_2x/` masters.

`materials.py` authors three soft masks directly from enhanced-art pixels. Native palette tables determine black-preserving RGB transforms for green shell, desaturated green skin and neutral gray details. Neutral changes are bounded to ±4 RGB8 levels. Ochre patches, cream highlights and facial detail remain protected. Palette 581 is an exact bypass. The other variants require no generation.

Five matching RGBA8 base / RGB8 mask atlas pairs use 16-pixel gutters and three pixels of hidden edge RGB/material bleed, with mipmaps disabled. Decoded runtime memory: base 64,821,248 bytes, masks 48,615,936 bytes, total 113,437,184 bytes (108.18 MiB), including 31,371,732 bytes of packing overhead. `runtime_aligned_2x/`, `runtime_masks_2x/`, trimmed images and deterministic previews are preserved. Offline-only `viewer_rgb/` companions prevent browser alpha-rounding errors before recoloring; they are not runtime requirements.

Validation covers all source and palette hashes, exact atlas reconstruction, base bypass, mask sums, unchanged variant alpha, 135 stored poses, 192 tracks and 1,056 timing boundaries. Browser reconstruction matches all 405 baked variants exactly across 39,032,313 pixels. Visual evidence includes every pose's palette/mask contact and worst-edge light/dark contact, native transitions and three actor captures. `review/acceptance.json` seals the accepted files by hash.

Resume by reusing the validated manifest and its accepted hashes. If correcting a demonstrated defect, preserve a new version of the raw sheet, run only affected extraction, then lighting, materials, package, viewer_rgb, browser_checks and review_evidence in dependency order. Reinspect affected visual evidence before refreshing the review and finalization. The approved Downloads wrapper can run each staging script. Do not rerun identity checkpoint selection on accepted work.

Fine texture interprets the low-resolution sources. All content remains under creature staging; originals are preserved and nothing has been installed into gameplay.
