# MM7 Air Elemental (m508) — 2026-10-20

Batch M, model 1 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 232–234 (Tempest, Cyclone, Air Elemental; internal Elemental Air A/B/C).
Source: the installed MM8 model mm8_m508.glb
([mm8_m508_claude](../mm8_m508_claude/README.md), reduction [mm8_m508_reduce_claude](../mm8_m508_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same art, same palette: the MM8 model unchanged.** The MM7 Air Elemental draws the MM8 bitmaps
themselves: all 117 paired frames are byte-identical files (alpha IoU 1.0, index-equal 1.0) and every tier uses
palette 508, as MM8 does. MM7's descriptor TintColor (B `0x0000ffff`, C `0x00ff5a5a`) is not used by the renderer
(`MonsterTable` reads it, nothing draws with it), so the three MM7 tiers differ only in frame scale (1.0 / 1.3 /
1.5; MM8 1.0 / 1.25 / 1.5).

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m508.glb`](export/mm7_m508.glb), 4.1 MB, sha256 `70a9d2239434e59f2a087e7f312ebd2a9d655088f177086e027e8e3cc243e919` |
| Source | `assets_source/worlds/mm8/models/mm8_m508.glb` (sha256 `70a9d2239434…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | the installed MM8 ones (no change) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m508_claude/review/viewer/) (1 model; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

No colour work: the MM8 model has no variants or region ramps (white wind, body and lightning materials), and
the MM7 tiers share its palette. The export is a byte-for-byte copy of the MM8 file (same sha256).

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m508_claude check`: 1 × 9 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

MM7 collision heights are 85 for all tiers (MM8: 160 / 190 / 190), while the body mesh alone is 113 / 147 /
170 game units tall at the MM7 scales, with the wind funnel below it. The model therefore rises well above the MM7
collision box, as the MM7 sprite does (same bitmap height × the same frame scale); a low ceiling can cut the head.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 1 | 1.29999 | 1.5 |
| MM7 collision height | 85 | 85 | 85 |
| MM7 model scale | 100 | 129.999 | 150 |
| Model height (largest mesh, bind pose) | 113.4 | 147.4 | 170 |
| MM8 collision height | 160 | 190 | 190 |

MM8 tier A: frame scale 1, model scale 100. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done): bind the MM8 model, no copy

Recommended and chosen (2026-10-20): the export is byte-identical to the installed `mm8_m508.glb`, so MM7 binds that file directly
instead of installing a second copy. The game merges every mounted world's `actors.yml` into one manifest and
resolves `worlds/mm8/models/...` from any world, so no `tools/install_model.py` run is needed and no MM8 asset
changes. Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml)
(the MM8 tier-A entry with the MM7 descriptor names, the MM8 model and skin names, and the MM7 scales above).

`export/` keeps the verified MM7 copy as a fallback for a build that ships MM7 without the MM8 world; its install
command would be
`python3 tools/install_model.py level_generation/creatures/mm7_m508_claude/export/mm7_m508.glb --world mm7`
with `model: worlds/mm7/models/...` in the binding.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  (shared batch-M scripts; run from the repository root).
