# MM7 Wyvern (m434) — 2026-10-20

Batch M, model 9 ([BATCH_M.md](../mm7_batches/BATCH_M.md)). MM7 descriptors 424–426 (Wyvern, Horned Wyvern, Ancient Wyvern; internal AWyvern A/B/C).
Source: the installed MM8 model mm8_m560.glb
([mm8_m560_claude](../mm8_m560_claude/README.md), reduction [mm8_m560_reduce_claude](../mm8_m560_reduce_claude/README.md)).
Not installed (batch rule): everything stays in this project. Meshy: 0 credits.

## Decision

**Same render, other colours.** The MM7 frames (`m434*`) are the MM8 `m560` render: alpha IoU median
0.98, index-equal 0.976, with MM7 palettes 114 / 115 / 116 instead of MM8 561 / 562 / 563.

Numbers: `scripts/identity_check.py` → [review/identity_check.json](review/identity_check.json). It pairs the MM7 and
MM8 frame sequences per descriptor role and view (alpha IoU with bottom-centre alignment, index-equal fraction), finds
each MM7 frame's best match among all MM8 bitmaps of the family (also with both silhouettes normalised to the same
height, which finds a re-rasterised render), and compares the tier palettes by file hash.

## Delivery

| Item | Value |
|---|---|
| Export | [`export/mm7_m434.glb`](export/mm7_m434.glb), 6.7 MB, sha256 `837cd3f637c2609d2ca1014e5bcd08721a77eded461a0c14e5547326cd01ee69` |
| Source | `assets_source/worlds/mm8/models/mm8_m560.glb` (sha256 `3f032e278259…`) |
| Contents | the MM8 geometry, skin, LODs, shadow LODs, clips and images, byte-identical (binary chunk asserted equal by `scripts/build_glb.py`) |
| Changed | glTF JSON only: variant names, material names and region ramps where listed below |
| Ramps | [`textures/m434_ramps.json`](textures/m434_ramps.json) from `scripts/tier_ramps.py` |
| Viewer | [review/viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m434_claude/review/viewer/) (3 models; ramps baked per tier for three.js) |
| Meshy | 0 credits |

## Colours

`scripts/tier_ramps.py` uses the m560 method (`mm8_m560_reduce_claude/scripts/compose.py`): standing and
walking pixels are split into membrane / body by their palette-561 hue, ranked by tier-A luminance, and each stop takes
the median native colour (× 1.15) at the rank where the region's texel luminance reaches that stop. Region membership
is a property of the palette index (the MM7 frames carry the MM8 indices), so MM7 pixels are classified with palette
561 too, while colours and rank come from the MM7 palettes (tier A 114).

Method check, rebuilt from the MM8 frames against the installed MM8 ramps: body exact; membrane mean 1.2 / 0.5 / 1.5
8-bit sRGB levels (max 0.11 linear on one stop), because the texel quantiles come from the stored 1K mask upsampled to
the 2K raster where m560 used its 2K weights. The installed ranges are kept exactly. MM7 result: Wyvern brown
membrane on an olive body, Horned Wyvern dark blue membrane on a rust-orange body, Ancient Wyvern olive-yellow
membrane on a blue body, as the native frames. Mask: the installed m560 mask, no new channel.

## Checks

- `check_winding.py`: 0 inverted closed parts (geometry unchanged from the installed MM8 model).
- `python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m434_claude check`: 3 × 5 clips
  load, no console errors ([review/viewer_check.json](review/viewer_check.json)).
- Shots in [review/shots/](review/shots/); [tiers_vs_native.png](review/shots/tiers_vs_native.png) puts each tier's
  viewer shot above the MM7 standing frame drawn with that tier's palette.
- Clip gates (floor, loop, corpse, deformation, hands) are the MM8 projects'; nothing here changes geometry, skin or
  clips. The viewer is the Roc viewer with camera framing from the posed body; three.js shows neither the engine's
  UV scrolling nor its additive effects, so the elementals look flatter there than in game.
- No in-game check (optional in the batch rules).

## Size

MM7 frame scale 1.0 for every tier, MM8 1.5: MM7 wyverns are two thirds of the MM8 size. Tier scale 284
(= 426 × 1.0 / 1.5) for A, B and C. The bind-pose body is 122 game units tall against MM7 collision height 144; in the
Fly clip the wings rise above the body, so as with the other flyers the wing tips can leave the box under low
ceilings.

| | A | B | C |
|---|---|---|---|
| MM7 frame scale | 1 | 1 | 1 |
| MM7 collision height | 144 | 144 | 144 |
| MM7 model scale | 284 | 284 | 284 |
| Model height (largest mesh, bind pose) | 121.9 | 121.9 | 121.9 |
| MM8 collision height | 160 | 160 | 160 |

MM8 tier A: frame scale 1.5, model scale 426. MM7 raster factor (MM8
bitmap height / MM7 bitmap height for the same frame): 1.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m434_claude/export/mm7_m434.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`: [review/actors_binding.yml](review/actors_binding.yml), the MM8
tier-A entry with the MM7 descriptor names, model path, skins and the scales above (animation, sockets, events and
clips unchanged from MM8).

Recommended (2026-10-20): install this project's own GLB as above, which leaves the installed MM8 model untouched.
Alternative, not chosen: Three new variants (`m434_a/b/c`) in `mm8_m560.glb` would avoid a second 6.7 MB copy; that changes
an installed MM8 asset, so it is the user's call.

## Scripts

- `scripts/project.json`: descriptor ids, MM8 candidates, build, viewer and sheet settings.
- `scripts/identity_check.py`, `scripts/build_glb.py`, `scripts/viewer.py`, `scripts/tier_sheet.py`
  and `scripts/tier_ramps.py` (shared batch-M scripts; run from the repository root).
