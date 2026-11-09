# MM7 female elf peasant — complete staged restoration

Validated 84/84 native frames across descriptors 331–339: five standing views, 40 walk poses,
30 recoil poses, four fidget poses, four falling poses and one corpse. All 79 referenced
frames and five unused nf0..4 poses are retained without adding playback entries.
All 13 base sheets were generated once through built-in imagegen; exact prompts, input hashes,
raw dimensions and selected checkpoints are preserved in generation.json.

The native chestnut hair, brown leather vest, green side-laced trousers, brown boots and
crooked wooden staff are preserved. Nine native palettes (323–331) share one enhanced base.
RGB8 masks use R for cloth, G for hair and zero B. Fixed native ACT luminance-to-color fits
preserve enhanced shading; palette 323 bypasses recoloring exactly. Cloth masks protect the
open side panels and leather lacing. Hair component filtering excludes the staff and vest;
explicit exposed hair islands cover recoil and falling occlusions. Hidden hair is excluded
from the final prone poses. All 756 frame/palette combinations were visually reviewed.

The 256×256 logical canvas, bottom pivot (128,256), native scale 0.799988 and Center flags
are preserved at 2 physical pixels per logical pixel. Views 0–4 are stored; 5–7 mirror native
views. Every timing entry is 125 ms. Standing holds one pose; walk/attack/shoot share the
eight-step walk cycle; hit uses five poses. Death reuses na0 and nb0 followed by da0..dd0,
then holds. Corpse holds xa0. Fidget uses fa0, fb0, fc0, fd0, fc0, fb0.
All action-specific view reuse and descriptor/palette bindings are preserved.

One 2048×3613 base atlas and matching RGB8 mask use 51,795,968 decoded bytes (49.40 MiB),
including packing. The standalone viewer.html embeds native and enhanced palette previews.
Nothing is installed into gameplay and no native assets were overwritten.

Review covered every native/restored pose, ordered animation sequences, all masks, all
756 variants, native timelines and enlarged light/dark alpha edges. Browser captures verify
the mirrored gray-haired black-trouser walk and the blonde cream-trouser falling pose.
The initial masks missed occluded hair and recolored nearby leather/wood; these defects were
corrected and the affected variants rechecked. Final edge review shows no visible magenta
fringe; the cleaned/atlas audit has zero candidates above 32. validation.json passes full
coverage, unchanged source hashes, raw bounds, crop reconstruction, atlas extraction, base
bypass, variant alpha, mask weights and native timings/flags.

Reproduction from saved checkpoints (repository root; run sequentially):

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m322 --tone .80
python3 level_generation/creatures/mm7_m322/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m322
python3 level_generation/creatures/mm7_m322/review_variants.py
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m322
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m322
```

Reuse the accepted package. Regeneration invalidates acceptance hashes and requires review of
changed outputs. Fine details interpret the low-resolution originals; they are not recovered
original high-resolution pixels.
