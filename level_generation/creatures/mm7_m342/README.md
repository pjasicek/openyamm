# MM7 human female peasant 1 — complete staged restoration

Validated 84/84 native frames across descriptors 349–357: five standing views, 40 walk poses,
30 recoil poses, four fidget poses, four falling poses and one corpse. Every owned native
frame is referenced and retained. Thirteen accepted base sheets come from 21 built-in
imagegen outputs; eight superseded sheets and one failed generation attempt are preserved
alongside exact prompts, reference hashes, raw dimensions and selection records.

The original dark brown flowing hair, gold earrings, dark green laced bodice and gown,
white linen sleeves and underskirt, dark belt and sheathed dagger are preserved. Nine native
palettes (343–351) share one enhanced base. RGB8 masks use R for green cloth, G for hair and
zero B. Fixed native ACT luminance-to-color fits retain enhanced shading; palette 343 bypasses
recoloring exactly. A fixed 0.65 hair gain compensates the enhanced hair's brighter brown.
Authored face boundaries, two hand exclusions and three prone hair zones protect skin and
equipment. All 756 frame/palette combinations were reviewed.

The 256×256 logical canvas, bottom pivot (128,256), native scale 0.899994 and original flags
are preserved at 2 physical pixels per logical pixel. This family does not use Center flags.
Views 0–4 are stored; 5–7 follow native mirrors. Every timing entry is 125 ms. Standing holds
one pose; walk/attack/shoot share eight walk poses; hit uses all six recoil poses. Death
reuses na0 and nb0 followed by da0..dd0, then holds; corpse holds xa0. Fidget uses
fa0, fb0, fc0, fd0, fc0, fb0. Native action-specific Image1 reuse and descriptor bindings remain intact.

One 2048×2731 base atlas and matching RGB8 mask use 39,151,616 decoded bytes (37.34 MiB),
including packing. The standalone viewer.html embeds native and enhanced palette previews.
Nothing is installed into gameplay and no native assets were overwritten.

Review covered every native/restored pose, ordered action sequences, all masks, all 756
variants, native timelines and enlarged light/dark edges. Browser captures verify a mirrored
gray-haired purple-gown walk and the blonde brown-gown falling pose. Demonstrated white/skin
gaps in bodice lacing and incorrect falling boots/head placement were corrected through saved
imagegen revisions. Mask leakage into faces/hands, missed hair and nine oblique front-lock boundaries were corrected locally.
The final edge repair excludes magenta interior samples, including nearly black pixels whose
small tint would otherwise be amplified. It changes RGB only and runs before and after
premultiplied resizing. The final cleaned/atlas audit has zero candidates above 32.
validation.json passes complete coverage, unchanged source hashes, raw bounds, crop/atlas
reconstruction, exact base bypass, unchanged variant alpha, mask weights and native timings/flags.

Reproduce from accepted checkpoints, sequentially from the repository root:

```sh
python3 level_generation/creatures/mm7_m514/process.py --project level_generation/creatures/mm7_m342 --tone .80
python3 level_generation/creatures/mm7_m342/variants.py
python3 level_generation/creatures/mm7_m514/package.py --project level_generation/creatures/mm7_m342
python3 level_generation/creatures/mm7_m342/review_variants.py
python3 level_generation/creatures/mm7_ambient/review_contacts.py --project level_generation/creatures/mm7_m342
python3 level_generation/creatures/mm7_m514/build_viewer.py --project level_generation/creatures/mm7_m342
```

Reuse the accepted package. Rebuilding invalidates acceptance hashes and requires review of
changed outputs. Fine details interpret the original low-resolution artwork.
