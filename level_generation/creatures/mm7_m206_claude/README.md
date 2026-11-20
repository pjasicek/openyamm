# MM7 Light Elemental (m206) — 2026-10-20

Batch M, model 4 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 241–243 (Lesser Light Elemental, Light Elemental, Greater Light Elemental; internal Elemental Light A/B/C).
Source: the installed MM8 model mm8_m528.glb (Will o' Wisp)
([mm8_m528_claude](../mm8_m528_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same art, same palette: the MM8 Will o' Wisp model unchanged.** The MM7 frames (`m206*`, single-view
`Image1` frames, lit, glow radius 256) are the MM8 `m528` render: best-match alpha IoU median 0.969 (p10 0.936),
index-equal 0.86, palette 528 for every tier in both games. The lower minimum (0.37, death frame `m206dm0`) is in the
scattered spark particles of the death burst, not the core; [review/identity_sheet.png](review/identity_sheet.png)
shows MM7 above MM8. Frame scales: MM7 1.5 / 1.8 / 2.1, MM8 1.0 / 1.3 / 1.7.

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m206.glb`](export/mm7_m206.glb), 1.5 MB, sha256 `88c30cec70f8a094ad9f7ff7cdbcb60df901bda0a4311ccd9c13537a9ed2a4e6` |
| Source | `assets_source/worlds/mm8/models/mm8_m528.glb` (sha256 `88c30cec70f8…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | the installed MM8 ones (no change) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m206_claude/review/viewer/) (1 model; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

No colour work: the MM8 model has no variants (smoke and light materials) and the palette is the same. The
export is a byte-for-byte copy of the MM8 file.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m206_claude check`: 1 × 6 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

Tier A scale 150 (MM8 100 × 1.5 / 1.0) and the MM8 rule for the sprite's bottom canvas anchor, `z_offset`
= 64 × frame scale: 96 / 115.2 / 134.4. The core model is 23–32 game units, inside MM7 collision heights 95 / 138 /
154. The binding keeps the MM8 `ambient_effect: mm8:fx/wisp_stars`; it resolves in every world, because
`engine/effects/library.yml` includes `worlds/mm8/effects/wisp.yml`.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 1.5 | 1.79999 | 2.09999 |
| MM7 collision height | 95 | 138 | 154 |
| MM7 model scale | 150 | 179.999 | 209.999 |
| Model height (largest mesh, bind pose) | 22.8 | 27.4 | 31.9 |
| MM8 collision height | 160 | 160 | 160 |

MM8 tier A: frame scale 1, model scale 100. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done): bind the MM8 model, no copy

Recommended and chosen (2026-10-20): the export is byte-identical to the installed `mm8_m528.glb`, so MM7 binds that file directly
instead of installing a second copy. The game merges every mounted world's `actors.yml` into one manifest and
resolves `worlds/mm8/models/...` from any world, so no `tools/install_model.py` run is needed and no MM8 asset
changes. Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml)
(the MM8 tier-A entry with the MM7 descriptor names, the MM8 model and skin names, and the MM7 scales above).

`export/` keeps the verified MM7 copy as a fallback for a build that ships MM7 without the MM8 world; its install
command would be
`python3 tools/install_model.py level_generation/creatures/mm7_m206_claude/export/mm7_m206.glb --world mm7`
with `model: worlds/mm7/models/...` in the binding.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  (shared batch-M scripts; run from the repository root).
