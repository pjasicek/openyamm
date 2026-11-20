# MM7 angel — validated offline restoration

All 124 native frames are restored across palettes 151–153 and descriptors 199–201. Open `viewer.html` for native/restored playback, masks and mirrored views. All assets remain staged offline; originals are unchanged and nothing is installed into gameplay.

Thirty accepted built-in imagegen sheets preserve the stern tan face, crested brass helmet, dark steel breastplate, brass greaves and bracers, green skirt, brown leather tabs, bronze shield, wavy sword and white-lavender wings with deep blue undersides. Thirty-seven raw outputs, exact submitted prompts and input hashes are retained. Recoil n_0 v2 corrected two wing tips that had become extra silver blade shapes, preserving the actual sword and the rest of the sheet. Palette variants share the accepted generated base.

All 124 frames are referenced by native actions. Standing uses sa; walk uses eight wa–wh poses; attack/shoot eight aa–ah; hit six na–nf. Death uses wa0, wb0, da0, db0, dc0, dd0; corpse holds xa0; fidget uses fa0, fb0, fc0, fd0. Timed frames are 125 ms. Five stored views, mirrors 5–7 and Image1 reuse for death/corpse/fidget are preserved. Logical size is 256×256 with pivot (128,256), native Center flag and scale 1.399994 for all three descriptors. Palette bindings are derived directly from native groups.

Processing uses tone 0.80, warm contour protection, core threshold 24, common anatomical scale per batch, alpha cleanup and premultiplied 2× resizing. Enhanced-art R8 skirt masks use green chroma, connected material support and alpha-normalized 0.45-pixel feathering. Fixed native ACT RGB fits use green entries within indices 187–253. Wings, skin, armor, brass, leather tabs, shield and sword remain protected. Palette 151 bypasses exactly; all variants preserve alpha.

Three RGBA8 base/R8 mask page pairs measure 2048×3911, 2048×3992, 2048×942. Shared decoded memory including packing and masks is 90,572,800 bytes (86.38 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and a self-contained viewer.

Review covered every native/restored frame, all 372 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, corrected blue recoil and mirrored purple flight browser captures. All package checks pass, including native sources, full coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, masks, alpha and base bypass. Edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m150 --tone .80
python3 level_generation/creatures/mm7_m150/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m150
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m150
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m150
python3 level_generation/creatures/mm7_m150/review_variants.py
```

Resolution repair replaced 48 frames from six undersized sheets with eighteen compact four-pose sheets; 76 accepted frames are reused. All 124 selected frames measure at least 2.008033 generated pixels per native pixel before 2× runtime export. Overlap selection preserves the tiny foreshortened sword in af3 from a_3_detail_2. The clipped ad1 overlap in a_1_detail_1 is reference-only; exported ad1 comes intact from detail_0. All 48 replacements, 144 palette appearances, enhanced skirt masks, ordered motion, light/dark edges and final mirrored blue attack and playing purple flight browser captures were reviewed.

Reproduction requires renewed visual acceptance and refreshed hashes. Generated microdetail remains a reviewed interpretation of native art.
