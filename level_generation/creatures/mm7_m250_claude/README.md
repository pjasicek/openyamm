# MM7 Gog (m250) — 2026-10-20

Batch M, model 8 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 274–276 (Gogling, Gog, Magog; internal AGog A/B/C).
Source: the installed MM8 model mm8_m612.glb
([mm8_m612_claude](../mm8_m612_claude/README.md), reduction [mm8_m612_reduce_claude](../mm8_m612_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same art, same palettes.** The MM7 frames (`m250*`) are the MM8 `m612` render: alpha IoU median
0.981, index-equal 0.98, and the three MM7 tiers use palettes 613 / 614 / 615, the same files as MM8 Gog A/B/C. The
batch file expected "same body, other colours"; the palettes turned out to be identical.

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m250.glb`](export/mm7_m250.glb), 9.9 MB, sha256 `49c98ae86c05b9f960ed9ae43ea33064d00c4feefd1107e0e8bf4fe16244c46c` |
| Source | `assets_source/worlds/mm8/models/mm8_m612.glb` (sha256 `751a7d25dc9a…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | the installed MM8 ones (no change) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m250_claude/review/viewer/) (3 models; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

The Gog ramps (`mm8_m612_claude/scripts/compose_textures.py`) are an affine map from palette A to each
tier's palette over the scale indices, so they depend only on the palette files, which are identical. The installed
`gog_a/b/c` ramps are kept unchanged; only the variants are renamed `m250_a/b/c`. Shots match the native green /
blue / red tiers.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m250_claude check`: 3 × 9 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

Same raster; tier A scale 83.91 (= 85.98 × 0.65 / 0.666), B 85.21, C 167.8 by `scale_reference` (MM7 frame
scales 0.65 / 0.66 / 1.3, MM8 0.666 / 0.8 / 1.0). Model height 143 / 145 / 285 game units against MM7 collision
heights of only 47 / 48 / 95 (MM8: 160). The MM7 table is the odd one out; the MM7 sprite is drawn just as tall, so
the model matches what MM7 shows, and the low collision box is a data quirk to keep in mind.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 0.649994 | 0.659988 | 1.29999 |
| MM7 collision height | 47 | 48 | 95 |
| MM7 model scale | 83.9148 | 85.205 | 167.83 |
| Model height (largest mesh, bind pose) | 142.7 | 144.9 | 285.3 |
| MM8 collision height | 160 | 160 | 160 |

MM8 tier A: frame scale 0.665985, model scale 85.9793. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done): bind the MM8 model, no copy

Recommended and chosen (2026-10-20): the export is the same as (only the variant names differ from) the installed `mm8_m612.glb`, so MM7 binds that file directly
instead of installing a second copy. The game merges every mounted world's `actors.yml` into one manifest and
resolves `worlds/mm8/models/...` from any world, so no `tools/install_model.py` run is needed and no MM8 asset
changes. Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml)
(the MM8 tier-A entry with the MM7 descriptor names, the MM8 model and skin names, and the MM7 scales above).

`export/` keeps the verified MM7 copy as a fallback for a build that ships MM7 without the MM8 world; its install
command would be
`python3 tools/install_model.py level_generation/creatures/mm7_m250_claude/export/mm7_m250.glb --world mm7`
with `model: worlds/mm7/models/...` in the binding.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  (shared batch-M scripts; run from the repository root).
