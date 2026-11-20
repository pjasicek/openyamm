# MM6 Earth Elemental — validated

All 59 native unique images are restored: 58 referenced images and the unused `ertfib0` pose, retained without inventing an animation binding. Descriptor IDs 526–528; palettes 725 brown, 726 dark green and 727 dark grey. Everything remains staged, with originals and gameplay unchanged.

Open [review.html](review.html) directly for native/restored animation and palette comparisons. See [review_notes.md](review_notes.md), [manifest.json](manifest.json), [validation.json](validation.json) and [acceptance.json](acceptance.json).

The final missing right-profile walking sheet succeeded on the first request of the user-authorized five-attempt budget, on 2026-09-13. Exact successful wording and references are retained in `prompts/retry_3_2026_09_13/` and `generation.json`. Earlier failure records are historical, not active blockers.

Reproduce from retained accepted raw sheets:

```sh
python3 level_generation/creatures/mm6_ert/process.py
python3 level_generation/creatures/mm6_ert/package.py
python3 level_generation/creatures/mm6_peasants/build_viewer.py ert
```

Use the family package wrapper: it declares the nonlinear native palette LUTs and their memory cost. Reprocessing/repacking resets visual acceptance and requires review before updating acceptance hashes. The fixed 0.75 RGB grade preserves the muted brown material. An R8 stone mask and two usage-weighted native luminance LUTs preserve the variants' dark shadows. `*_before_palette_fix.*` files retain the rejected linear-fit checkpoint for comparison. No additional image generation is needed.

Runtime integration is separate: the staged LUT contract needs a compatible loader/shader or deterministic variant baking before installation.
