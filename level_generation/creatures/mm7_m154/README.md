# MM7 archer — validated offline restoration

All 120 native frame names are restored across palettes 155–157, descriptors 202–204. Open `viewer.html` for native/restored playback, masks and mirrored views. Assets remain staged offline; originals are unchanged and nothing is installed into gameplay.

Twenty-nine selected built-in imagegen sheets retain the tan face, horned black steel helmet with brass trim, chainmail, teal heraldic tabard, white bird emblem, brown leather equipment, quiver, bow and arrows. All thirty-five raw outputs, exact submitted prompts and reference hashes are retained. Palette variants share the generated base artwork.

Sampling repair replaced 48 undersampled walk/profile and attack frames using seventeen compact overlapping sheets. The other 72 frame registrations are exactly unchanged. The clipped raised arrow in a_1_detail_0 is reference only; ac1 exports intact from a_1_detail_1. Visual review corrected a tabard-mask leak onto ac4 boots by excluding the reviewed leather region below aligned y=440. The previous settings and acceptance are retained in checkpoints/before_sampling_repair.

Native actions reference 105 frames; the other 15 (ag/ah in all five stored views and fa0–fe0) are preserved as unused frames without adding playback. Standing and fidget use sa; walk uses wa–wh; attack/shoot use aa–af, with af held for 375 ms and preceding frames 125 ms; hit uses na–ne at 125 ms. Death uses na0, nb0, da0, db0, dc0, dd0 at 125 ms; corpse holds xa0. Five stored views, mirrors 5–7 and Image1 reuse for death/corpse are preserved. Logical size is 256×256, pivot (128,256), Center flag, and descriptor scale 0.799988 for all variants.

Processing uses tone 0.80, warm contour protection, core threshold 24, common anatomical scale per batch, alpha cleanup and premultiplied 2× resizing. Enhanced-art R8 tabard masks use green chroma, connected material support and alpha-normalized 0.45-pixel feathering. Fixed native ACT RGB fits use green entries within indices 151–199. Skin, white emblem, chainmail, steel, brass, horns, leather, bow and arrows remain protected. Palette 155 bypasses exactly; blue 156 and red 157 preserve alpha.

Three RGBA8 base/R8 mask page pairs measure 2048×3701, 2048×3906 and 2048×500. Shared decoded memory including packing and masks is 83,015,680 bytes (79.17 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and a self-contained viewer.

Repair review inspected all 48 replacements, all 144 replacement palette appearances and masks, ordered comparisons, light/dark edges, mirrored red 375 ms attack hold and playing blue profile walk. Prior visual acceptance is reused for the 72 unchanged poses. Review covered all 120 native/restored frames, all 360 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, mirrored red attack at its 375 ms hold and blue Image1 death browser captures. All package checks pass, including native sources, full coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, masks, alpha and base bypass. Edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m154 --tone .80
python3 level_generation/creatures/mm7_m154/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m154
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m154
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m154
python3 level_generation/creatures/mm7_m154/review_variants.py
python3 level_generation/creatures/mm7_m154/review_repair.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native art; all 120 final frames have measured actual generated sampling at least 2.0434899× native resolution before 2× export.
