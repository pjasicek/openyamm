# MM7 moon cleric — validated offline restoration

All 109 native frames are restored across palettes 37–39 and descriptors 214–216. Open `viewer.html` for native/restored playback, masks and mirrored views. Assets remain staged offline; originals are unchanged and nothing is installed into gameplay.

Eighteen accepted built-in imagegen sheets preserve the gaunt gray face and hands, black hair, small gold crown, crescent ceremonial collar, turquoise tassels, dark olive hanging fabric panels and green gold-trimmed robe. Twenty raw outputs, exact submitted prompts and reference hashes are retained. Walking w_0 and w_2 v2 removed invented hand sparkles without changing the accepted poses. Palette variants share the generated base artwork.

All 109 frames are referenced. Standing uses sa; walk wa–wh; attack/shoot aa–af; hit na, nb, nc, nd, ne, nd, nc, nb. Death uses na0, nb0, da0, db0, dc0, dd0; corpse holds xa0. Fidget preserves fa0, fb0, fc0, fd0, fc0, fb0, fb0, including the repeated final fb0. Timed frames are 125 ms. Five stored views, mirrors 5–7 and Image1 reuse for death/corpse/fidget are preserved. Logical size is 256×256 with pivot (128,256), Center flag and scale 1 for all descriptors.

Processing uses tone 0.80, warm contour protection, core threshold 24, common anatomical scale per batch, alpha cleanup and premultiplied 2× resizing. Enhanced-art RGB8 masks separate green robe (R) and dark olive panels (G), with B reserved zero. Fixed native ACT RGB fits use robe entries within 165–228 and panel entries within 135–164. Gold ornament, gray skin, black hair and turquoise tassels remain protected. Review demonstrated recoloring of bright gold spell flecks over the robe; explicit enhanced-hue and brightness exclusions corrected this. Palette 37 bypasses exactly; blue 38 and red 39 preserve alpha. Masks use connected material support and alpha-normalized 0.45-pixel feathering.

Two RGBA8 base/RGB8 mask page pairs measure 2048×3819 and 2048×1552. Shared decoded memory including packing and masks is 76,998,656 bytes (73.43 MiB). Placement, animation and variant metadata accompany aligned masters, tight crops and a self-contained viewer.

Review covered all 109 native/restored frames, all 327 frame/palette combinations, native palette references, ordered action sequences, enlarged light/dark edges, mirrored blue casting and red Image1 final-fidget browser captures. Corrected spell flecks remain gold. All package checks pass, including native sources, full coverage, unclipped raw cells, exact crop/atlas reconstruction, timing/flags, masks, alpha and base bypass. Edge audit reports zero residual candidates above 32. No family blockers remain.

Reproduce from the repository root in order:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m170 --tone .80
python3 level_generation/creatures/mm7_m170/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m170
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m170
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m170
python3 level_generation/creatures/mm7_m170/review_variants.py
```

Reproduction requires renewed visual acceptance and refreshed hashes. Generated detail is a reviewed interpretation of native art; physical 2× export size does not imply identical per-pose generation resolution.
