# New Sorpigal land terrain — connected v5

[Review screenshots and comparisons](review.html) · [Interactive tile bench](index.html) ·
[Iteration policy](ITERATION_POLICY.md)

This project contains 33 imagegen-derived coverage masks and 36 opaque, 256×256 runtime tiles.
Water, shore tiles and water alpha remain original and are outside this pass.
The final review record is [reports/review_v5.json](reports/review_v5.json).

## Materials and masks

| Family | Masks | White foreground | Black background |
|---|---:|---|---|
| Grass/dirt, `6grdrt*` | 12 | Grass | Dirt |
| Rock/dirt, `voldrt*` | 12 | Volcanic rock | Dirt |
| Roads, `6drsr*` | 9 | Cobbles including grout | Dirt |

The 36 runtime files contain these 33 transitions plus pure grass, dirt and volcano.
Cobbles are a shared material placed through the nine road masks, never a full-tile road replacement.
All masks are authoring coverage, not runtime transparency. The engine uses baked opaque PNGs.

Each native source was independently interpreted by imagegen, keeping its orientation and shape vocabulary.
Raw outputs, exact prompts and source hashes are retained in `raw/`, `prompts/` and `mask_inventory.json`.
The built-in imagegen tool was used; it does not expose a backend model selector.
The inverse dirt coverage is derived as `1 - foreground`; it is not another AI generation.

Current materials: grass v1, cobbles v1, volcano v2, **dirt v6**.
Dirt v6 supersedes the earlier v4 selection following the user's `test_img/1263.png` comparison:
v4 was too orange and its contrast clusters made diagonal repetition conspicuous.
V5 redistributed the clods; v6 darkened and muted the brown and reduced highlight contrast.
The selected masters and their history live in the sibling `mm6_new_sorpigal_master_study/`.

`material_seams/connected_v2/` contains the wrapping derivatives used by this composite iteration.
Grass, cobbles and volcano retain their earlier interiors. The new dirt is a full user-requested redo.
The central448×448 pixels of each current512px source are preserved during the mechanical edge constraint.
These derivatives share symmetric8px sampling strips fading by16px, so both512 and Lanczos256 exports wrap.
Earlier master and composite versions remain available for comparison.

## Composition and continuity

`masks/connected_v4/` is the current set of33 normalized512px masks.
Shared profiles are defined per material topology and axis, with pure-material endpoints and common road openings.
N/S sides read left-to-right; E/W sides read top-to-bottom. There is no implicit reversal or tile rotation.
An8px shared strip approaches the AI silhouette through a further24px signed-distance repair band.
The v2 profile contract stays fixed across subsequent interior/material revisions.

The composer combines the same-phase512px materials in linear-light RGB, then downsamples finished tiles to256px.
The v5 pass adds 33 AI-generated boundary edits, constrained to narrow coverage-distance bands.
Roads gain dark contact rims, grass gains an irregular olive/brown fringe, and rock receives weaker mineral/earth blending.
The accepted material interiors and connected_v4 coverage masks remain unchanged. Shared colour strips keep
the new boundary artwork continuous across tile joins. Prompts, raw edits, rejected attempts and separate
authoring layers are retained in [edge_treatment/](edge_treatment/README.md).
`composites/v5/` retains512px outputs; `runtime_x2/worlds/mm6/terrain_x2/` contains the36 runtime PNGs.

Two extraction defects were repaired: the first road straight exposed dirt in internal grout, and a grass X-corner
repair initially left a rectangular paste boundary. The final grass tile uses the complete repaired AI mask with
fixed shared edges. All other masks are unchanged from the preceding connected version.

## Map corrections

The original map has eight contradictory directed land joins. A separate seven-cell tile-selection patch resolves
them while keeping all other map bytes unchanged, including geometry, heights, actors and water/shore tiles.
See [map_corrections/patch.json](map_corrections/patch.json) for exact coordinates, before/after native IDs and hashes.
`map_corrections/oute3.odm` is the corrected copy; **the production map is untouched**.
A texture-only installation retains these original layout defects.

The source audit preserves207 original join types and280 original2×2 configurations, including the known invalid
ones. The browser labels incompatible source cases. Compare those against corrected map contexts, not against an
invented mask that tries to satisfy contradictory material edges.

## Verification and limits

- `check_masks.py`:33 opaque grayscale512px masks;398 compatible boundary checks across512 and256 coverage.
- `check_composites.py`:211 unique RGB joins covering8,524 placements in the corrected map and six legal layouts.
  Both 512px authoring and 256px runtime joins pass. Boundary pixels must agree within1/255. These numeric checks do not certify the appearance of tile interiors.
- Flat image review: all199 compatible original pair types, all280 original corner cases with source conflicts
  identified, family contact sheets, pure repeats and six larger connected layouts.
- Native engine fixture:537 separated pads, flat heights, no bmodels, actors or decorations. Only valid internal
  pad joins are assessed. The cobble material repeat is a browser swatch, not a native full-tile road.
- Actual game captures include the four requested New Sorpigal poses, corrected-land contexts, top views of the
  six layouts, and near/far views facing all four directions. Filtering and sampled motion evidence are linked
  from the review page and recorded in the final review JSON.

A test initially hit the engine's outdoor position clamp and photographed the wrong pad. Grass layouts were moved
inside the playable boundary; coastal map contexts are viewed from inland. Their earlier captures are superseded.
The fixture keeps the original minimap artwork, which is unrelated to its synthetic terrain arrangement.

Repeated use of one master still repeats fine texture; this pass removes the conspicuous clump bands and mismatched
joins, not all mathematical repetition. Water transitions remain visibly original in coastal screenshots.
Software-display captures are visual evidence, not a GPU performance benchmark. Sampled motion frames do not
certify temporal stability on every renderer/GPU. No new terrain geometry, shaders or dynamic grass were introduced.

## Files and reproduction

`runtime_x2/` is a world-scoped asset overlay, prepared locally and not installed in production assets.
The delivery ZIP contains this overlay and a separate optional corrected-map copy with its patch manifest.
Use terrain quality x2. The map correction is specific to the source hash recorded in `patch.json`.

From the repository root, with Pillow, NumPy and SciPy available:

```sh
python3 level_generation/terrain/mm6_new_sorpigal_transitions/build_audit.py
python3 level_generation/terrain/mm6_new_sorpigal_transitions/prepare_material_seams.py
python3 level_generation/terrain/mm6_new_sorpigal_transitions/compose_tiles.py
python3 level_generation/terrain/mm6_new_sorpigal_transitions/check_masks.py level_generation/terrain/mm6_new_sorpigal_transitions/masks/connected_v4 --output /tmp/terrain-mask-check.json
python3 level_generation/terrain/mm6_new_sorpigal_transitions/edge_treatment/bake_edges.py --version v5 --publish-runtime
python3 level_generation/terrain/mm6_new_sorpigal_transitions/check_composites.py --version v5 --runtime-dir level_generation/terrain/mm6_new_sorpigal_transitions/edge_treatment/runtime/v5 --authoring-dir level_generation/terrain/mm6_new_sorpigal_transitions/composites/v5
```

`prepare_map_corrections.py` recreates the exact map patch; `build_fixture.py` uses the existing OpenYAMM editor
native writer and verifies the terrain round trip. `prepare_trials.py` creates isolated `/tmp` asset stages and
saved camera poses (build its helper first with `python3 level_generation/terrain/mm6_new_sorpigal_transitions/build_pose_helper.py`). `capture_trials.py` drives the existing game capture helper under Xvfb; its logs and pose-console
screenshots accompany the actual game images. Prompts and original AI outputs are retained for deliberate retries;
re-running the mechanical tools does not incur model calls.

See `ITERATION_POLICY.md` for case-based feedback, shared-edge ownership, visual failure criteria and retry limits.

The v5 review compares original artwork, pre-edge v4, and current v5 using the same frozen engine binary and saved poses.
The previous delivery is preserved as `new_sorpigal_land_x2_v4.zip` and `review_v4.html`.
