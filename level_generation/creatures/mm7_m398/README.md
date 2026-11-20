# MM7 skeleton warrior — validated offline restoration

All 124 native frame names are restored across palettes 63, 64 and 399 and descriptors 397–399. Open `viewer.html` for native/restored playback, masks and mirrored views. Assets remain staged offline; originals are unchanged and nothing is installed into gameplay.

The 18 accepted built-in imagegen sheets preserve the aged ochre-ivory bones, hollow skull, spiked steel helmet, battered dark steel armor with brass rims, faded blue-violet trousers, rusty red markings, short sword and two lodged arrows with pale fletching. All 19 raw outputs and exact submitted prompts remain recorded. The standing v2 checkpoint corrected a missing lower arrow in the front-right view. Collapse artwork preserves detached sword, helmet and limb components at native positions. Palette variants share this generated base artwork.

Coverage includes 114 referenced frames and ten unused family-owned images ag0–4 and ah0–4, exported without invented playback. Standing uses sa; walk uses eight wa–wh poses; attack/shoot six aa–af; hit six na–nf. Death uses na0, nb0, da0, db0, dc0, dd0; corpse holds xa0; fidget uses fa0, fb0, fc0, fd0, fc0, fb0. Timed frames are 125 ms except fidget: descriptor 397 uses 375 ms for every pose, while 398/399 use 375 ms for fd0 and 125 ms elsewhere. Five stored views, mirrors 5–7 and Image1 reuse for death/corpse/fidget are preserved. Logical size is 256×256 with bottom pivot (128,256), no Center flag. Native descriptor bindings are 397→palette 399/scale 1.199997, 398→palette 63/scale 1.299988, and 399→palette 64/scale 1.399994. Variant descriptor metadata was corrected to derive these bindings directly from native groups.

Processing uses tone 0.80, warm contour protection, core threshold 24, common anatomical scale per batch, alpha cleanup and premultiplied 2× resizing. Enhanced-art R8 cloth masks use blue-violet chroma, connected support and alpha-normalized 0.45-pixel feathering. Fixed native ACT RGB fits use blue-violet entries within indices 174–247. Bones, armor, brass, arrows, sword and rusty markings remain protected. Palette 63 bypasses exactly; all variants preserve alpha.

Two RGBA8 base/R8 mask page pairs measure 2048×3929 and 2048×1498. Shared decoded memory including packing and masks is 55,572,480 bytes (53.00 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and a self-contained viewer.

Review covered all native/restored frames, all 372 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges and final mirrored tan-cloth attack/green-cloth death browser captures. All package checks pass, including native sources, full coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, masks, alpha and base bypass. Edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m398 --tone .80
python3 level_generation/creatures/mm7_m398/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m398
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m398
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m398
python3 level_generation/creatures/mm7_m398/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native art; physical 2× export size does not imply identical per-pose generation resolution.
