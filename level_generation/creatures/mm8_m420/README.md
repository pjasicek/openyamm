# MM8 Pirate Mage Male — staged restoration

Validated coverage: all 162 native files, 160 unique enhanced poses and two native pixel aliases (`nf4 → nd4`, `ng4 → ne4`). The 22 unreferenced stored files remain available without invented animation timing. All five stored views and native mirror mappings, logical 256×256 geometry, anchoring, actor/frame scales and durations are preserved for all six descriptor bindings (16–18 and 187–189).

Open `viewer.html` offline to compare native poses, restored atlases, palette coverage and all six native palettes: 421 base green/brown hair, 422 blue/gray, 423 red/blond, 649 burgundy/blue hair, 650 purple/orange hair and 651 green/blond. Green coat and hair recolor through enhanced-art R8 coverage and deterministic palette interpolation. Reviewed sash/wood exclusions protect unchanged warm details. The base preset is an exact bypass and every variant preserves alpha.

The built-in imagegen tool generated 26 selected compact identity/action/view sheets. Prompts, native references, all 29 raw attempts, rejected versions and accepted registration/identity checkpoints remain here. Death views 0, 3 and 4 use corrected v2 sheets; other selected sheets use v1. Returned sheet dimensions are recorded per batch in `generation.json`; the 2× export tier is separate from generated detail.

Processing uses local matte unmixing, premultiplied filtering, frozen batch registration and documented shared row corrections. The identity luminance multiplier is 0.9285719939479518; native coarse tone plus 0.7 enhanced fine detail at sigma 7 preserves original tonal weight. Casting-pose highlights remain native. A final local RGB-only edge correction removes demonstrated pink staff rims using nearby interior colors, with all 160 registered alpha hashes unchanged. See `checkpoints/local_edge_repair.json` and retained before/after edge evidence.

All 26 registration, final-frame and six-palette/mask contacts were reviewed, including the corrected material exclusions. Rebuilt edge contacts and mirrored playback were reviewed after the local edge fix. Browser checks pass 972 variant decodes, 162 stored poses, 384 native animation tracks and 2008 timing boundaries. Source hashes, full coverage, crop reconstruction, matching base/mask placement, variant alpha/base bypass and all-frame edge audits pass.

Delivery: six RGBA8 atlas pages plus six matching R8 mask pages, aligned masters, deterministic palette previews, `manifest.json`, `animations.json`, `variants.json`, `validation.json`, and the offline viewer. Decoded allocation is 84,191,232 bytes base plus 21,047,808 bytes masks = 105,239,040 bytes including packing; tight base/mask content is 76,353,270 bytes and packing overhead 28,885,770 bytes. Shared palettes do not multiply resident base geometry.

Restored surface detail is an interpretation of native low-resolution artwork. This package is staged only; originals are unchanged and gameplay installation is separate.

To revise: reuse the retained raw sheets, run `python3 level_generation/creatures/mm8_m420/rebuild.py`, review changed contacts, run the authorized offline browser checks, renew `review/decision.json` evidence hashes only after acceptance, run `finalize.py`, then refresh `inventory_remaining.py`. Artifact hashes in `review/acceptance.json` make changes invalidate completion until revalidated.
