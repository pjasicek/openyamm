# Gold piles rebuilt from their references

**Complete: all nine piles rebuilt, reviewed at playing distance and installed; zero deferred items.**

Replacement for the nine gold heaps rejected in [the native screenshot](references/rejected_native.png).
The [icon reference sheet](references/icon_sheet.png) defines their layouts. Each pile now consists entirely of
closed, individually modelled coins: short stacks, overlapping loose coins and coins leaning against stacks.
The old smooth dome and random carpet of discs are removed.

The three MM8 designs retain their individual structures: `item204` has a three-coin central stack, `item205` a
five-coin stack with loose coins around it, and `item206` a taller eight-coin stack with several shorter columns.
The MM6/MM7 references share three matching designs, including the large pile's two prominent rear stacks.
Existing item IDs, binding lengths and pickup behavior are preserved.

## Review

[Before/after at playing distance](review/distance_comparison.jpg) shows the corrected rim and engraving read.

[Comparison 1](review/comparison_1.jpg) and [comparison 2](review/comparison_2.jpg) show every icon beside its old
model, neutral clay, textured three-quarter, low, above and underside views.
The [LOD comparison](review/lod_comparison.jpg) shows all four levels at an enlarged review scale.
The [per-icon ledger](LEDGER.md), [handoff](handoff.json), [validation](work/validation.json),
[install receipts](work/install_receipts.json) and [exact desktop cook verification](work/cooked_verification.json)
record the delivered files and checks.

Native outdoor comparisons use the same save and cameras:
[before](review/native_baseline_outdoor/01-all_nine.png),
[after](review/native_final_outdoor/01-all_nine.png),
[closer](review/native_final_outdoor/02-mm8_stacks.png) and
[low](review/native_final_outdoor/03-mm8_low.png), [down the row](review/native_final_outdoor/06-down_row.png), and
[closer view](review/native_final_outdoor/05-mm8_close.png).
Indoor checks use MM6 Agar's Laboratory with the three
[MM6](review/native_indoor_1/gold_piles.png), [MM7](review/native_indoor_2/gold_piles.png) and
[MM8](review/native_indoor_3/gold_piles.png) piles dropped in each isolated run.
Selected settings, logs and binary hashes are indexed in [native run records](work/native_runs.json).
These are visual checks, not performance benchmarks.

## Geometry and materials

The nine base meshes total **40,828 triangles**, ranging from **1,888 to 7,552** per pile, with **8–32 actual coins**.
Every pile has three lower LODs. Coins use 20/12/12/8 sides. All four levels retain a broad raised rim and a recessed face.
They retain every coin, the pile layout and stack height. Every coin has a complete back and positive enclosed
volume; there is no hidden filler mesh. The pivot is at the footprint centre with the lowest contact at zero,
and the longest horizontal dimension is glTF Z.

One material and three shared **512×512** PNG maps cover all nine models: base colour, metallic/roughness and
OpenGL tangent-space normal. Identical coin faces intentionally share UV space. The shared cooked textures total about 0.6 MiB of GPU blocks including mipmaps. The final minting artwork uses broad gold, worn-gold and bronze patina regions that survive mipmapping.
Discrete material colours replace painted lighting gradients; engraved detail also supplies the normal map.
Raised rims and thickness come from geometry. Darker minted side bands separate stacked coins; bright rim finish
and broad recessed engraving keep the coins legible at ordinary playing distance. The earlier flat low LODs
and fine-only texture contrast were rejected in [the distance screenshot](references/rejected_distance_read.png). Colour is sRGB; material and normal maps use linear data.

**Engine-driven material exception:** gold fields use metallic **0.70**, roughness approximately **0.19–0.45**, and saturated amber
unlit gold albedo. The reference palette and material response were calibrated in native lighting. Earlier pale cream/olive versions
were rejected by the user. The fields retain a diffuse share under weak engine environment reflection. Rims use 0.85 metallic and
0.19 roughness; bronze patina regions use 0.10 metallic and up to 0.45 roughness. This separates warm reflective
rims, darker minted side bands and broad engraved recesses. No emission or renderer changes are used. Revisit this approximation if environment lighting
changes. Superseded native captures remain separately labelled in `review/`.

Both face artwork revisions came from the built-in imagegen tool. Its [exact prompt](references/coin_face_prompt.txt),
[original image](references/coin_face_painted.png), [final readable image](references/coin_face_readable.png),
[readability prompt](references/coin_face_readable_prompt.txt) and [receipt](references/generation_receipt.json) are preserved.
The coin geometry is authored in Blender. Meshy spend: **zero credits**.

## Reproduction

From the repository root, run:

```sh
/snap/bin/blender --background --factory-startup --python level_generation/props/gold_piles_refit_20261018/scripts/build_gold.py
python3 level_generation/props/gold_piles_refit_20261018/scripts/validate_gold.py
```

Render `baseline`, `clay`, `replacement`, `lod1`, `lod2` and `lod3` using `scripts/render_gold.py -- <mode>` in separate
background Blender processes, then run `scripts/make_sheets.py` with Python. Inspect the new views and renew their
hashes in `work/visual_review.json` before `scripts/install_gold.py`; it refuses stale or unreviewed exports.
`scripts/verify_installed.py` verifies only these nine installed models. Original models remain in
`references/baseline_models/`, and nine editable scenes remain in `blends/`.

This changes development world-item assets only. Release promotion and Android testing are outside this repair.
