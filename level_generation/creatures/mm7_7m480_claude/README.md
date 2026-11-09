# MM7 Ultra Dragon (7m480) — 2026-10-20

Batch M, model 6 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 460–462 (zUltra Dragon A/B/C, an unused MM7 monster).
Source: the installed MM8 model mm8_m492.glb
([mm8_m492_claude](../mm8_m492_claude/README.md), reduction [mm8_m492_reduce_claude](../mm8_m492_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same art: the MM8 Dragon body and colours.** The MM7 `7m480*` bitmaps have the MM8 Dragon's (`m492`)
silhouettes exactly (alpha IoU 1.0 on every compared frame, best-match p10 1.0) but other palette indices
(index-equal 0.0007): MM7 palette 531 is a reordering of MM8 palette 492. Drawn, the two are the same picture — per
pixel the MM7 colour differs from the MM8 one by 0.7 levels on average (p95 5) on the frames sampled. All three MM7
tiers use the same frames, palette 531 and frame scale 7.0 (MM8 Dragon: 5.0).

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_7m480.glb`](export/mm7_7m480.glb), 31.9 MB, sha256 `ff9dc8574579c13b0a231ce5f7e0c246bd627ca93d3e6c1249e5da4b74f9f909` |
| Source | `assets_source/worlds/mm8/models/mm8_m492.glb` (sha256 `360e5aa6c22c…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | the installed MM8 ones (no change) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_7m480_claude/review/viewer/) (1 model; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

Same colours, so the installed MM8 Dragon ramps are kept unchanged; only the variant is renamed (`m492` →
`7m480`, one variant for all three tiers, as MM8 binds its Dragon). The MM8 Dragon's accepted ramps read warmer and
brighter in the viewer than the dark native sprite (see [tiers_vs_native.png](review/shots/tiers_vs_native.png)); that
is the MM8 production's look, not something this copy changes.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_7m480_claude check`: 1 × 9 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

Tier scale 2106.0 for A, B and C (= 1504.29 × 7.0 / 5.0). The frame groups `7m499*` that the MM7 descriptors
name are missing from the sprite frame tables (the identity check reads the frames from the native project's
manifest), so the engine's `scale_reference` would fail for these descriptors; the binding therefore gives each tier
its explicit scale. The model is about 900 game units tall in its bind pose against an MM7 collision height of 190
(MM8 Dragon: 500): the box is far too small for this dragon, as it is for the MM7 sprite. The monster is unused in
MM7, so nothing in the game places it today.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 7 | 7 | 7 |
| MM7 collision height | 190 | 190 | 190 |
| MM7 model scale | 2106 | 2106 | 2106 |
| Model height (largest mesh, bind pose) | 897.6 | 897.6 | 897.6 |
| MM8 collision height | 500 | 500 | 500 |

MM8 tier A: frame scale 5, model scale 1504.29. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done): bind the MM8 model, no copy

Recommended and chosen (2026-10-20): the export is the same as (only the variant name differs from) the installed `mm8_m492.glb`, so MM7 binds that file directly
instead of installing a second copy. The game merges every mounted world's `actors.yml` into one manifest and
resolves `worlds/mm8/models/...` from any world, so no `tools/install_model.py` run is needed and no MM8 asset
changes. Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml)
(the MM8 tier-A entry with the MM7 descriptor names, the MM8 model and skin names, and the MM7 scales above).

`export/` keeps the verified MM7 copy as a fallback for a build that ships MM7 without the MM8 world; its install
command would be
`python3 tools/install_model.py level_generation/creatures/mm7_7m480_claude/export/mm7_7m480.glb --world mm7`
with `model: worlds/mm7/models/...` in the binding.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  (shared batch-M scripts; run from the repository root).
