# MM7 Fire Elemental (m202) — 2026-10-20

Batch M, model 2 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 238–240 (Warden of Fire, Guardian of Flame, Fire Elemental; internal Elemental Fire A/B/C).
Source: the installed MM8 model mm8_m496.glb
([mm8_m496_claude](../mm8_m496_claude/README.md), reduction [mm8_m496_reduce_claude](../mm8_m496_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same art, same palette: the MM8 model unchanged.** The MM7 frames (`m202*`) are the MM8 `m496` render:
144 paired frames with alpha IoU 0.97–0.98 (median 0.979) and index-equal 0.94, all tiers on palette 496 as in MM8.
Only the frame scales differ (MM7 1.1 / 1.5 / 2.0, MM8 1.3 / 1.75 / 2.0).

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m202.glb`](export/mm7_m202.glb), 3.2 MB, sha256 `89936467148eb20c1ebdfff4d10b5227e46a78bfd30b18d98440d73c7d82fd3c` |
| Source | `assets_source/worlds/mm8/models/mm8_m496.glb` (sha256 `89936467148e…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | the installed MM8 ones (no change) |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m202_claude/review/viewer/) (1 model; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

No colour work: the MM8 model has no variants (body, flame, ash and burst materials) and the palette is the
same. The export is a byte-for-byte copy of the MM8 file.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m202_claude check`: 1 × 9 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

Tier A scale 80.81 (MM8 95.51 × 1.1 / 1.3); B and C follow by `scale_reference`. Model height 150 / 204 /
272 game units against MM7 collision heights 180 / 250 / 330: it fits.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 1.09999 | 1.5 | 2 |
| MM7 collision height | 180 | 250 | 330 |
| MM7 model scale | 80.8127 | 110.2 | 146.933 |
| Model height (largest mesh, bind pose) | 149.5 | 203.9 | 271.9 |
| MM8 collision height | 160 | 180 | 200 |

MM8 tier A: frame scale 1.29999, model scale 95.5058. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done): bind the MM8 model, no copy

Recommended and chosen (2026-10-20): the export is byte-identical to the installed `mm8_m496.glb`, so MM7 binds that file directly
instead of installing a second copy. The game merges every mounted world's `actors.yml` into one manifest and
resolves `worlds/mm8/models/...` from any world, so no `tools/install_model.py` run is needed and no MM8 asset
changes. Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml)
(the MM8 tier-A entry with the MM7 descriptor names, the MM8 model and skin names, and the MM7 scales above).

`export/` keeps the verified MM7 copy as a fallback for a build that ships MM7 without the MM8 world; its install
command would be
`python3 tools/install_model.py level_generation/creatures/mm7_m202_claude/export/mm7_m202.glb --world mm7`
with `model: worlds/mm7/models/...` in the binding.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  (shared batch-M scripts; run from the repository root).
