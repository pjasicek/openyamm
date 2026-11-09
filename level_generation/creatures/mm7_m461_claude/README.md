# MM7 Troll (m461) — 2026-10-20

Batch M, model 5 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 448–450 (Swamp Troll, River Troll, Mountain Troll; internal ATroll A/B/C).
Source: the installed MM8 model mm8_m480.glb (Troll Peasant) + mm8_m480_club.glb
([mm8_m480_claude](../mm8_m480_claude/README.md), reduction [mm8_m480_reduce_claude](../mm8_m480_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same render at a smaller raster, other colours.** The MM7 Troll bitmaps are the MM8 Troll Peasant
render (`m480`, same pose, same red bone club, same body) rasterised 1/1.515 as large and drawn with a larger frame
scale (2.5 instead of 1.1). Direct alpha IoU is low (0.28) only because of that size; with both silhouettes cropped
and scaled to the same height the best-match IoU is 0.956 (p10 0.917), at a consistent factor of 1.515. The other
MM8 troll, `m476` (vest, other club), scores 0.57 and is not the source. See
[review/identity_sheet.png](review/identity_sheet.png) (MM7, MM8 m480, MM8 m476). The MM7 palettes (499 / 505 / 509)
are not the MM8 ones (481 / 482 / 483) and order their indices differently.

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m461.glb`](export/mm7_m461.glb), 5.0 MB, sha256 `414b4b946c27a214df8747777b5693bcc34d5a7ec7535d6b6c7eb2d585918470` |
| Export | [`export/mm7_m461_club.glb`](export/mm7_m461_club.glb), 0.9 MB, sha256 `e9ba307adff4b12fbe72faa51c867d3f9ddf9c41bb9b7563f5278fe6ec6b9bfa` |
| Source | `assets_source/worlds/mm8/models/mm8_m480.glb` (sha256 `8405e7fdeb13…`), `assets_source/worlds/mm8/models/mm8_m480_club.glb` (sha256 `3e57d987a59a…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | [`textures/m461_ramps.json`](textures/m461_ramps.json) from `scripts/tier_ramps.py` |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m461_claude/review/viewer/) (3 models; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

`scripts/tier_ramps.py` uses the m480 method (`mm8_m480_claude/scripts/compose_textures.py`): native indices of
each region are sampled in a box on the standing frames (belly skin, loin wrap, crest, mottled back), sorted by
tier-A luminance, the 15–95 % slice kept, and each tier's ramp is a luminance-neutral tone `stop × mean(tier colour)
/ lum(mean(tier-A colour)) × (1, 1, .7, .85)` over the full range 0..1. Rebuilt from the MM8 frames it reproduces
the installed MM8 ramps exactly (max difference 0.0 on all 12 ramps).

For MM7 the boxes are mapped onto the smaller raster by the frames' bounding boxes, and the index ranges come from the
MM7 palettes: skin 40–126 (identical in all three MM7 palettes), loin wrap 165–198, crest 133–157, and the hair on
the back shares the crest indices 133–157 (the MM8 back used its own range 211–239). Tier A of MM7 (499) is the
luminance reference. Result at the mid stop (sRGB): skin olive-yellow in every tier (MM7 does not recolour the skin);
wrap grey-green / indigo / maroon; crest green / blue-grey / red-brown; back hair the crest's hue — as the MM7 sprites
(Swamp, River, Mountain Troll) and the native project's description. Mask: the installed m480 atlas mask, no new
channel. The method is a mean tone per region, so there is no least-squares fit error beyond the method check.

The club attachment `export/mm7_m461_club.glb` is the MM8 club with its variants renamed to `m461_a/b/c`
(the engine gives an attachment the carrier's skin name); its material and images are unchanged. The viewer shows the
body only (it has no attachment support); the club's geometry and grip are the MM8 project's.

## Checks

- `check_winding.py`: 0 inverted closed parts in each GLB (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m461_claude check`: 3 × 8 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

MM7 sprite height = 1/1.515 of the MM8 bitmap × 2.5 against 1.1 for MM8, so the MM7 troll is 1.50× the MM8
Troll Peasant: tier A scale 192.77 (= 128.49 × 2.5 / 1.1 / 1.515), the same for B and C (all three MM7 tiers use frame
scale 2.5). The model is about 328 game units tall against the MM7 collision height of 256 (MM8 Troll Peasant: 160
units of collision for a 219-unit model), so the head and crest rise about 70 units above the box — the same
proportion as the sprite, and a reason to watch low indoor ceilings.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 2.5 | 2.5 | 2.5 |
| MM7 collision height | 256 | 256 | 256 |
| MM7 model scale | 192.767 | 192.767 | 192.767 |
| Model height (largest mesh, bind pose) | 328.1 | 328.1 | 328.1 |
| MM8 collision height | 160 | 160 | 160 |

MM8 tier A: frame scale 1.09999, model scale 128.489. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.5149.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m461_claude/export/mm7_m461.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m461_claude/export/mm7_m461_club.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml), the MM8
tier-A entry with the MM7 descriptor names, model path, skins and the scales above (animation, sockets, events and
clips unchanged from MM8).

Recommended (2026-10-20): install this project's own GLB as above, which leaves the installed MM8 model untouched.
Alternative, not chosen: Three new variants (`m461_a/b/c`) in `mm8_m480.glb` and the club would avoid a second 5 MB copy;
that changes an installed MM8 asset, so it is the user's call.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  and `scripts/tier_ramps.py` (shared batch-M scripts; run from the repository root).

## Texture quality pass (2026-10-31)

The installed `mm7_m461.glb` shares the MM8 Troll Peasant's geometry and images, so it takes the same new UVs and
maps from [mm8_m480_texpass_claude](../mm8_m480_texpass_claude/README.md) (`scripts/merge_install.sh` builds both).
Its MM7 ramps, variant names and head-bob clips stay as installed. Not installed yet: it waits for gait package h10.

## Gait rollout (2026-10-31)

Package [h10](../gait_rollout_20261031/h10/README.md) appended `Walk2` (the MM8 Troll Peasant's h20 job, 1.15 s, stride 1.1977) and `Run` (0.76 s, stride 2.5072, LoinFront thigh rule) to the installed `assets_source/worlds/mm7/models/mm7_m461.glb`
(existing clips, meshes, skins and materials byte-identical; pre-gait copy `../gait_rollout_20261031/h10/work/mm7_m461_pre_gait.glb`)
and installed it; the bindings (`walking: Walk2`; A/B `sprint: Run` with `Walking` as their run, C `run: Run` and `sprint: Run`) are applied by the rollout coordinator from `h10/bindings.yml`. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h10/scripts/rebuild.sh m461`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
