> Resolved 2026-09-13: the goblin correction is applied and all MM6 families are installed. See [current installation](../INSTALLATION.md). The measurements below describe the pre-correction review.

# MM6 ground-origin review — 2026-09-13

The staged sheets show **no broad ground-origin shift**, but the previously accepted goblin front artwork has a small real upward displacement that should be corrected before a full installation. This review changed no restored assets, manifests, originals or gameplay files.

## Coverage and result

Measured actual atlas-extracted alpha against original indexed BMP transparency for all **3,481 frame names across 60 families**. Of 3,479 nonempty frames, **3,446 match the original lowest visible point within 0.5 native logical pixel** at alpha >=128. Two native empty Cactus endpoints remain empty. All 1,946 distinct frame names used by standing/walk bindings were included; death, hits, attacks, fidgets and unused native poses were also measured. Native variants share the same geometry/alpha.

Every declared vertical pivot and native-canvas offset matches its recorded anchor convention. Comparison uses `pivotY - (cropY + visibleBottom)/tier` against the original image's visible bottom relative to its native pivot. This accounts for crop padding, negative origins, variable source canvases and the 2x tier. It does not mistake the packed rectangle's edge for the ground.

All ten family contacts were visually inspected: two selected poses per family at the same actor origin and scale, plus the eight enlarged foot comparisons. Staff-bearing Cleric, Jackalman, PeasantM2, PeasantM3 and Sorcerer samples were inspected so that a low staff tip would not hide floating feet. Their feet align closely. Floating originals retain their existing clearance. These contacts are a representative visual review alongside an exhaustive pixel-bound scan, not a claim that every animated pose was watched in-game.

## Small goblin discrepancy

31 goblin frame names exceed 0.5 native pixel of upward displacement. These are the reused accepted front checkpoint, rather than the newly generated side/rear views. Standing `gobsta0` is 1.5 pixels high; walking `gobwaa0` is 2 pixels high; worst attack/fidget/hit frames reach 2.5 pixels. The enlarged contact confirms a small gap below the claws. At 2x these correspond to 3–5 texture pixels, before applying the native frame scale.

This is small, not a large flying-monster displacement, but a deterministic placement correction is justified before installation. Reuse the accepted artwork, move the demonstrated front-frame registration down to the native planted-foot level, preserve the raised foot and native gait, then rebuild matching masks/crops/atlas/viewer and update acceptance. Do not force every frame's feet onto zero: originals have real raised-foot poses and native clearance. Exact affected names are in [findings.json](findings.json). No correction has been applied during this review.

Two other frames exceed 0.5 pixel at the 128 threshold: one Air Elemental endpoint and one Ghost pose. Their soft contours make threshold-dependent bounds vary; the floating family comparisons show no grounded-leg regression. At the stricter 224 threshold, sparse wisps/claws can disappear earlier, so that number is a sensitivity check rather than a ground-contact verdict.

## Runtime contract

For bottom-anchored actors, current `game/render/SpriteAtlasCache.cpp` computes crop offsets using the logical canvas height and physical tier; `spriteBillboardCenter` applies them and mirrors horizontal placement. This agrees with the audit for ordinary legged actors. Installation must preserve this path and native frame/actor scale. Renaming tight crops or padded aligned masters as replacement PNGs without consuming their logical offsets is not equivalent.

Cactus is separately declared center-anchored in the staged manifest. The current cache computes vertical offset from canvas bottom and does not consume `logical_pivot.y`; actor and decoration paths also differ in handling native Center flags. Its installation needs explicit agreement on that convention. This is a special integration issue, not evidence that ordinary humanoid sheets are floating. No renderer code was changed or runtime compatibility promised here. Some staged palette LUT models also require integration separately from this placement review.

## Evidence and repeat

- [Numeric audit](audit.json), including all frames, threshold sensitivity and manifest hashes.
- [Focused foot comparisons](feet_closeups.png): native left, atlas right; cyan line is actor origin.
- Family contacts: [1](families_01.png), [2](families_02.png), [3](families_03.png), [4](families_04.png), [5](families_05.png), [6](families_06.png), [7](families_07.png), [8](families_08.png), [9](families_09.png), [10](families_10.png).

```sh
python3 level_generation/creatures/mm6_remaining/ground_anchor_audit.py
```

Positive lift means higher than the original, in native logical pixels before frame/actor scale. The cyan line is the actor origin, not a demand that flying creatures or center-anchored Cactus touch it. Re-running regenerates the numeric audit and family contacts; reviewed findings must be reconsidered if source assets change.
