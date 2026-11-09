# MM7 dragon — offline restoration

All 107 native frames are restored across palettes 183–185 and descriptors 223–225, including 100 referenced frames and seven unused fa0–fg0 poses. `viewer.html` contains native/restored playback, masks and all eight views. Assets are staged offline; originals are unchanged and gameplay installation is outside this package.

Twenty selected built-in imagegen sheets retain the small horned head, long neck and tail, green scaled body, gold ventral plates, pale claws and enormous pointed mottled wings. Twenty-three raw outputs and exact prompts/reference hashes are retained. One rejected recoil sheet invented an extra head in nf3; its targeted v2 repair restores the single native head. All variants derive from one enhanced base.

Native standing, walk and fidget share sa, wa, wb, wc, wd, we, wf: durations 125, 125, 187.5, 187.5, 125, 125, 62.5 ms. Attack/shoot share sa then aa–af, each 125 ms. Hit uses sa then na–nf, each 125 ms. Death is sa0, na0, nb0, nc0, da0, db0, dc0, xa0, dd0; db0 and xa0 are 187.5 ms, the rest 125 ms. Corpse holds xa0. Unused fa0–fg0 remain available without adding them to playback. Five stored directions, mirrors 5–7 and Image1 death/corpse reuse are preserved. Native logical canvas is 256×256, pivot (128,256), Center flag; scales are 5.0, 5.099991 and 5.25. The viewer supports zooming below 1 to inspect these large native scales.

Processing uses tone 0.80, warm contour protection, core threshold 24, connected pose extraction and common anatomical scale per batch before premultiplied 2× resizing. RGB8 enhanced-art masks isolate green scales (R), wing membranes/dorsal accents (G) and the continuous gold ventral strip (B), protecting neutral horns, claws and teeth. Fixed native ACT fits use indices 1–35 and 216–255 for scales, 36–61 and 104–215 for membranes, and 62–87 for gold. Six authored profile-recoil exclusions prevent large dorsal spines from joining the belly mask. The red membrane transform uses nonnegative least squares: the initial unconstrained fit extrapolated warm tail accents into green, as retained in the before-repair death capture. Corrected red previews cover every frame. Base 183 bypasses exactly; alpha remains unchanged. Mask feathering is alpha-normalized Gaussian sigma 0.45.

Three RGBA8 base/RGB8 mask atlas pairs measure 2048×3913, 2048×4076, 2048×636. Shared decoded memory including masks and packing is 123,648,000 bytes (117.92 MiB); tight content is 105,476,798 bytes. Placement, animation, palette and descriptor metadata accompany aligned masters and tight crops.

Review covers all 107 native/restored frames, all 321 frame/palette combinations, corrected spine masks, every final red frame, ordered native action sequences, enlarged light/dark edges and mirrored blue attack/red Image1 death browser captures. Package checks verify original hashes, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, valid masks, exact base bypass and unchanged variant alpha. Residual edge candidates above 32: zero. Generated detail is a reviewed interpretation of native artwork; all 107 frames now meet measured generated sampling of at least 2.016607 pixels per native pixel. Four overlapping detail sheets replace the six rear recoil and seven unused fidget poses; overlap references are exported once. Prior accepted metadata is retained in checkpoints/before_sampling_repair.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m182 --tone .80
python3 level_generation/creatures/mm7_m182/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m182
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m182
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m182
python3 level_generation/creatures/mm7_m182/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed artifact hashes.
