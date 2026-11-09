# MM7 Water Elemental (m210) — 2026-10-20

Batch M, model 3 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 244–246 (Sprite, Sylph, Water Elemental; internal Elemental Water A/B/C).
Source: the installed MM8 model mm8_m500.glb
([mm8_m500_claude](../mm8_m500_claude/README.md), reduction [mm8_m500_reduce_claude](../mm8_m500_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same render, one tier in other colours.** The MM7 frames (`m210*`) are the MM8 `m500` render: 122 paired
frames, alpha IoU median 0.982, index-equal 0.98. MM7 tiers A and B use palettes 501 and 502, the same files as MM8
A and B. MM7 tier C uses palette 503, which MM8 does not use (its tier C reuses 501).

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m210.glb`](export/mm7_m210.glb), 8.0 MB, sha256 `38b4208a07477d2dc0248f0fa7063a1d122ba7bce393b48036844a1c4aadc582` |
| Source | `assets_source/worlds/mm8/models/mm8_m500.glb` (sha256 `47159fd7bb41…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | [`textures/m210_ramps.json`](textures/m210_ramps.json) from `scripts/tier_ramps.py` |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m210_claude/review/viewer/) (3 models; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

`scripts/tier_ramps.py` uses the m500 method (`mm8_m500_claude/scripts/compose_textures.py`): palette indices of
the standing frames are split by their palette-501 hue into scales / ventral / fins, the region's median native
colour × gain (1.65 / 1.14 / 1.12) is the target, and the ramp scales it linearly with luminance over the region
range. The method is checked first: rebuilt from the MM8 frames it reproduces the installed MM8 A and B ramps
exactly (max difference 0.0). Each region's median luminance `mid`, not stored in the GLB, is recovered from the
MM8 tier-A ramp.

- `m210_a`, `m210_b`: the installed `water_a` / `water_b` ramps unchanged (same palette, same render). A refit from
  the MM7 frames differs by at most 0.036 / 0.044 linear on the scales (the 2 % of pixels that differ move the median).
- `m210_c`: fitted from the MM7 standing frames `m210sa0–4` with palette 503: rust-orange scales (target sRGB
  0.49 / 0.28 / 0.18), off-white ventral, teal fins — the MM7 Water Elemental's colours.
- Mask: the installed m500 atlas mask (scales, ventral, fins); no new channel needed.

The method is a median target per region, not a least-squares fit, so there is no fit error beyond the method
check above.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m210_claude check`: 3 × 9 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

Same frame raster; tier A scale 89.77 (MM7 and MM8 tier A both 1.1). Model height 177 / 201 / 225 game
units against MM7 collision heights 180 / 202 / 224: a close match.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 1.09999 | 1.25 | 1.39999 |
| MM7 collision height | 180 | 202 | 224 |
| MM7 model scale | 89.7661 | 102.008 | 114.248 |
| Model height (largest mesh, bind pose) | 176.7 | 200.8 | 224.9 |
| MM8 collision height | 160 | 160 | 160 |

MM8 tier A: frame scale 1.09999, model scale 89.7661. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m210_claude/export/mm7_m210.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml), the MM8
tier-A entry with the MM7 descriptor names, model path, skins and the scales above (animation, sockets, events and
clips unchanged from MM8).

Recommended (2026-10-20): install this project's own GLB as above, which leaves the installed MM8 model untouched.
Alternative, not chosen: Adding one variant (`m210_c`, palette 503) to `mm8_m500.glb` would let MM7 bind A/B to the existing
`water_a` / `water_b` skins and C to the new one, with no second copy of the 8 MB GLB. That changes an installed MM8
asset, so it is the user's call.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  and `scripts/tier_ramps.py` (shared batch-M scripts; run from the repository root).

## Texture quality pass (2026-10-31)

The MM8 Water Elemental got new UVs and a 4K repaint (see
[its README, "Texture quality pass (2026-10-31)"](../mm8_m500_claude/README.md#texture-quality-pass-2026-10-31---current-installed-textures));
this model follows it. `scripts/tier_ramps.py` now recovers both the median `mid` and the pass's contrast factor `k`
from the MM8 tier A ramp (`colour = target * (1 + k * (lum / mid - 1))`; checked: rebuilds MM8 A/B exactly, and on
the pre-pass GLB reproduces the old ramps) and reads the MM7 frames from
`assets_legacy/sprites_mm7_monsters_20261021/`. `scripts/build_glb.py` then builds `export/mm7_m210.glb` from the
installed MM8 GLB (binary chunk identical), installed with `tools/install_model.py export/mm7_m210.glb --world mm7`.
Winding 0; floor audit Elemental Water A-C ok; `mm6_mm7_mm8_actor_models_build_every_binding` passes. Tier C tone at
the same surface points: scales and fins within 3 levels, ventral 9 darker, spreads matched
(`review/texpass_tone_report.json`). Sheets: `review/texpass/texpass_sheet_{a,b,c}.png`; viewer `review/viewer/`
(before/after per tier). Before state: `work/before_texpass/`. Meshy: 0 credits here.

2026-11-01: rebuilt and reinstalled after the MM8 eye correction (approved eye paint carried over; see the MM8
README, "Eye correction"). Viewer revision `mm7-texpass-20261101-r4-eyes`.
