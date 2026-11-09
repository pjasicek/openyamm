# MM7 spider — validated offline restoration

All 124 native frame names are restored across palettes 66–68 and descriptors 400–402. Open `viewer.html` for native/restored playback, palette masks and mirrored views. Assets remain staged offline; originals are unchanged and nothing is installed into gameplay.

The 18 accepted built-in imagegen sheets preserve the glossy green abdomen with broad ivory highlights and deep teal underside, small dark head with yellow eyes, eight angular black legs, red serrated distal segments and ivory hooks. Exact submitted prompts, raw outputs, reference hashes and accepted checkpoints are recorded in `generation.json`. Native blue and red/purple abdomen variants are deterministic recolors of this shared artwork.

Coverage includes 114 referenced frames and ten additional family-owned images, ag0–4 and ah0–4. Unused images are exported without invented playback. Standing uses sa, walk eight wa–wh poses, attack/shoot six aa–af, and hit six na–nf. Death uses na0, nb0, da0, db0, dc0, dd0; corpse holds xa0; fidget uses fa0, fb0, fc0, fd0, fc0, fb0. Timed frames remain 125 ms except the native fd0 fidget hold of 375 ms. Five stored views, mirrors 5–7, Image1 reuse for death/corpse/fidget, logical 256×256 size, bottom pivot (128,256), no Center flag and native scale 1.399994 are preserved. Descriptor group aliases 7m403/m404/7m405 remain native.

Processing uses tone 0.80, warm contour protection, core threshold 24, connected extraction for moving view batches, common anatomical scale per sheet, alpha cleanup and premultiplied 2× resizing. Enhanced-art R8 abdomen masks use green/chroma qualification and connected support, with alpha-normalized 0.45-pixel feathering. Review found reflected green leaking onto crossing legs in ae2; stronger seed and weight thresholds corrected that mask defect throughout the family. The diagnostic is preserved under `review/mask_authoring/`. Fixed native ACT RGB fits use indices 93–213. Red legs, ivory hooks and neutral highlights are protected; palette 66 bypasses exactly and variant alpha remains unchanged.

Two RGBA8 base/R8 mask page pairs measure 2048×4074 and 2048×1596. Shared decoded memory including packing and masks is 58,060,800 bytes (55.37 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and the self-contained viewer.

Review covered every native/restored frame, all 372 final frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, mirrored blue attack and red death browser captures. Final checks pass for source hashes, full coverage, unclipped raw cells, crop/atlas reconstruction, timing/flags, masks, alpha and base bypass. Edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m402 --tone .80
python3 level_generation/creatures/mm7_m402/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m402
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m402
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m402
python3 level_generation/creatures/mm7_m402/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native art; physical 2× export size does not imply identical generation resolution per pose.
