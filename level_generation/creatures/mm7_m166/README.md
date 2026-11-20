# MM7 beholder — validated offline restoration

All 124 native frames are restored across palettes 167–169 and descriptors 211–213. Open `viewer.html` for native/restored playback, masks, palette selection and mirrored views. Assets are staged only; originals remain unchanged and nothing is installed into gameplay.

The 27 accepted built-in imagegen sheets retain the brown ridged head, green eyes, gray tentacles with colored tips, ivory teeth and gold mouth strands. All 35 raw outputs, exact prompts and selected versions are preserved in `generation.json`. Four targeted revisions removed invented sparks, corrected native eye illumination timing and restored back-facing eye-stalk surfaces. Eight additional sheets replace 26 undersampled front/rear flight and hit poses; 98 reviewed poses are reused. The minimum measured generated detail is 2.002301 pixels per native pixel. No palette appearance was separately generated.

Coverage includes 90 referenced frames and 34 additional family-owned native frames: af–ai in all five views, fa–fd front, and ne–nf in all five views. Those unused images are exported without inventing playback bindings. Standing, walking and fidget share eight native flight poses; attack/shoot use five poses; hit uses four. Death plays wa0, wb0, da0, db0, dc0, dd0; corpse holds xa0. Palettes 167 and 168 use 187.5 ms per timed pose; palette 169 uses 125 ms. Five stored views and mirrors 5–7, Image1 death/corpse reuse, Center flags, logical 256×256 canvas, bottom pivot (128,256) and scales 1.5/1.549988/1.599991 are preserved.

Processing uses tone 0.80, warm contour protection, core threshold 24, connected pose extraction, common anatomical scale per sheet, alpha cleanup and premultiplied 2× resizing. Detached native eye components remain part of their death frames. Enhanced-art R8 masks recolor only green tentacle tips through fixed ACT RGB fits. Brown head, eyes, gray shafts, teeth and strands are protected. Profile geometry plus `tip_corrections.json` and `tip_exclusions.json` retain the reviewed local boundaries. The final classifier excludes small iris rims; three detached-eye exclusions and eight small-tip inclusions correct demonstrated spill and missed recoloring. Palette 167 bypasses exactly; all variants preserve alpha.

Three RGBA8 base/R8 mask page pairs measure 2048×4044, 2048×3887 and 2048×2568. Decoded shared memory including masks and packing is 107,509,760 bytes (102.53 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and the self-contained viewer.

Review covered every native/restored frame, all 372 frame/palette combinations, ordered native action sequences, corrected tip/eye boundaries and enlarged light/dark edges. Browser captures verify mirrored blue-tip flight and red-tip death with the detached eye. All package checks pass: source preservation, coverage, unclipped raw cells, exact crop/atlas reconstruction, native timing/flags, valid masks, unchanged alpha and exact base bypass. The final edge audit reports zero residual candidates above 32. Mask authoring diagnostics are retained under `review/mask_authoring/`. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m166 --tone .80
python3 level_generation/creatures/mm7_m166/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m166
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m166
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m166
python3 level_generation/creatures/mm7_m166/review_variants.py
python3 level_generation/creatures/mm7_m166/review_masks.py
```

Reproduction requires renewed visual acceptance and refreshed acceptance hashes. Generated detail is a reviewed interpretation of native art; actual per-pose generated resolution is independently checked against the required 2× minimum.
