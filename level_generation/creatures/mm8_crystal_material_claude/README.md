# MM8 crystal material: Crystal Dragon (m548) and Crystal Walker (m596) (2026-10-19)

User, after the Crystal Dragon reduction: "compare with original how it looked like there ... if we should do
something with it material wise", then "adapt the crystal dragon (and crystal walker also, its really similar imo)
according to what you think would be best". No Meshy credits; geometry, rig, animation and LODs unchanged.

## Problem

In game both read as matte pastel pink plastic next to their native sprites:
- **Outdoors:** the native sprites are mauve, with white glint facets and a few lavender ones.
- **Indoors:** the native sprites are mid mauve, while the Walker went dark maroon.

Measured on the native sprites (palettes 548 and 596) against the textures:

| | median RGB | luminance 5 / 50 / 95 / 99 % | HSV saturation |
|---|---|---|---|
| native m548 sprites | 160, 105, 129 | 0.37 / 0.47 / 0.68 / 0.96 | 0.33 |
| native m596 sprites | 165, 109, 137 | 0.39 / 0.49 / 0.76 / 0.99 | 0.33 |
| m548 texture before | 187, 109, 137 | 0.40 / 0.50 / 0.59 / 0.62 | 0.42 |
| m596 texture before | 155, 90, 123 | 0.26 / 0.42 / 0.67 / 0.69 | 0.42 |
| m548 texture after | 162, 108, 133 | 0.36 / 0.48 / 0.82 / 0.90 | |
| m596 texture after | 153, 104, 136 | 0.36 / 0.46 / 0.83 / 0.90 | |

The sprites have 2-4 % near-white glint pixels and about 1 % lavender or blue-violet. Both textures lacked the bright
tail, were too saturated and too pink in hue (338 against 330 deg). The Walker's swatch atlas also had a dark maroon
end.

## What the engine uses

`GltfModelLoader.cpp` and `fs_model.sc` read these material inputs:
- `roughnessFactor` times the metallic-roughness green channel, and `metallicFactor` times its blue channel;
- extras `openyamm_specular` (sun, point-light and sky reflection scale), multiplied per texel by the
  metallic-roughness red channel when `openyamm_specular_mask` is set;
- extras `openyamm_edge_darkening`, a rim darkening by mesh normal;
- the emissive factor, which is one constant colour that also feeds the bloom pass, so it is not used here.

Glossy surfaces trade diffuse for a sky reflection (Fresnel), so lower roughness gives each flat facet its own sky
tone and sun glint.

## Changes, first build (`scripts/crystal_material.py <in> <out> <m548|m596> <gloss|full>`); the dragon is superseded by review 2 below

| | m548 before | m548 after | m596 before | m596 after |
|---|---|---|---|---|
| roughness | 0.392 (ORM green) | per facet 0.10-0.20, glints 0.08 (ORM green) | 0.32 (factor) | 0.15 (factor) |
| specular | 0.45 x mask 0.863 | 0.8 x per-facet mask 0.75-1.0 (glints 1.0) | 0.6 | 0.8 |
| edge darkening | 0.35 | 0.25 | 0.25 | 0.2 |
| metallic | 0 | 0 | 0 | 0 |

Base colour, with the same image size, UVs and painted detail (each texel is recoloured relative to its own value):
1. Saturation is scaled to 0.34.
2. Hue shifts -7 deg toward mauve.
3. HSV value is remapped from 0.35-0.95 to 0.46-0.72, to the sprites' median and dark end.
4. Per-facet tones, deterministic (seed 548 or 596):
   - 5 % near-white glint;
   - 3 % lavender or blue-violet;
   - 20 % brighter;
   - 15 % deeper rose, floor at value 0.50;
   - the rest a small brightness and hue jitter.

Facets by creature:
- **m548:** its UVs are unique per triangle. LOD0 triangles are grouped into flat facets (position-welded
  neighbours within 12 deg; 3,547 facets), and each facet's UV area is rasterised into a facet map. The map is dilated
  into the gutters, so the LOD1-3 triangles, which reuse the atlas, pick up the tone under them. The amber eyes
  (hue 20-60 deg, saturation over 0.45) are kept as painted.
- **m596:** it is 64 swatches of 256 px, each used by 19 faces (rigid closed sections with overlapping UVs), so each
  swatch gets one tone: 35 jitter, 13 bright, 8 deep, 4 glint, 4 violet.

The images and material values are swapped; every other buffer view is copied byte for byte. All three tiers of each
creature still share one palette, as in the native data.

A first pass (`review/ingame/full/`) left the value range at 0.56-0.95. In game it looked washed-out, paler than the
sprites, so the value range was lowered to the native statistics (`full2`, installed).

## Dragon review 2: white patches removed (2026-10-19)

User, on a viewer close-up of the head and neck: "what is this white stuff?" The patches were the painted
near-white glint facets (and some lavender ones) of the `full2` build. They were wrong in three ways:
- they did not follow the geometric facets: one label per texel, so on triangles about 10 texels wide the tone
  boundaries were pixel staircases cutting across triangles;
- the 12 deg grouping merged smooth runs into large bands, as on the neck;
- the many small head triangles formed stripes;
- painted white reads as paint, not a glint.

The installed dragon is now the `subtle` variant (`crystal_material.py ... m548 subtle`):
- **No painted glints.** Glints come only from the specular: roughness a uniform 0.15, specular mask 1.0 x
  `openyamm_specular` 0.8.
- **Same native-matched colour transform** as before: saturation 0.34, hue -7 deg, value 0.46-0.72.
- **Subtle per-facet tones**, on strictly flat facets (coplanar neighbours within 3 deg; 5,442 facets):
  - 15 % brighter (+6-10 % value);
  - 15 % deeper (-6-10 %);
  - 1.5 % faint lavender (hue 25 % toward violet);
  - the rest +-3 %.
- **Exact triangle edges:** the tone field is rasterised at 4x supersampling with full coverage, area-averaged
  (anti-aliased edges that follow the triangles), and the gutters are filled from the nearest covered texel.
- **Quiet head:** no variation within 3 cm of the eyes (215 amber triangles) or the mouth socket, fading in to 6 cm.
  1,744 triangles are damped; the amber eyes stay as painted.

Verification:
- Textured close-ups of the head (side, three-quarter, front), crown, neck (side, front), fore and hind legs and
  body: `review/close/sheet_dragon_closeups.jpg` (rows: installed before / review 1 with white facets / fixed). The
  fixed row shows no staircase, no bands and a uniform head (`scripts/close_views.py`).
- In game: `review/ingame/compare_dragon_subtle.jpg` (native sprites; outdoor, close outdoor and indoor). The sun
  now makes the bright facets, as specular highlights.

The viewer's "final" row is this build.

**Crystal Walker, checked, not changed** (superseded 2026-10-19: rebuilt in [`../mm8_m596_v2_claude/`](../mm8_m596_v2_claude/README.md), which has its own crystal material; the Walker part of this project applies only to the old rigid model): its tones are per swatch, and
every face lies inside one swatch, so the tone edges follow the faces and there is no staircase. But 4 of its 64
swatches (about 76 LOD0 faces) are painted near-white "glints" and 4 are violet, so it has the same painted-white
problem at face level. It is still installed as `full2`, with the rollback in `work/`.

## Evidence

In-game, OpenGL desktop, isolated runs on the same cameras and spawn points as the m548 codex and m596 comparison
captures. The fixture is a hard-linked copy of `assets_dev` with both families preloaded in oute3 and 6d19
(`scripts/ingame_prepare.py <label>`, `scripts/ingame_run.sh <label>`, `scripts/compose_ingame.py <label>`).
The fixtures were deleted after capture.
- `review/ingame/compare_dragon_full2.jpg`, `compare_walker_full2.jpg`: native sprites / installed before / new,
  outdoors and indoors.
- `review/ingame/close_before_after.jpg`: closer outdoor view, before and after.

Viewers (installed / gloss only / gloss + facet colours, every clip):
- Dragon: http://127.0.0.1:8912/level_generation/creatures/mm8_crystal_material_claude/review/viewer/ (check: 24
  switches, no console errors).
- Walker, split into its own directory because its clips differ and the review tool serves one project directory:
  http://127.0.0.1:8912/level_generation/creatures/mm8_crystal_material_walker_claude/review/viewer/ (check: 27
  switches, no console errors).

The browser viewer shows roughness and colour but not the engine's specular scale, mask or edge darkening; judge
gloss in game.

## Status

Installed 2026-10-19 (the user delegated the choice) with `tools/install_model.py export/mm8_m548.glb --world mm8`
and `export/mm8_m596.glb`. `check_winding.py`: 0 inverted closed parts on both.

Regressions pass with `OPENYAMM_REGRESSION_FILTER=... ./build/game/openyamm --world mm8
--headless-run-regression-suite actors`:
- `mm8_crystal_dragon_actor_models_keep_native_sizes_and_roles` (`review/regression_m548.log`);
- `mm8_crystal_walker_actor_models_keep_rigid_parts_and_native_tiers` (`review/regression_m596.log`).

Rollback (the installed sources before this change):

```sh
python3 tools/install_model.py level_generation/creatures/mm8_crystal_material_claude/work/mm8_m548_pre_material.glb --world mm8 --name mm8_m548.glb
python3 tools/install_model.py level_generation/creatures/mm8_crystal_material_claude/work/mm8_m596_pre_material.glb --world mm8 --name mm8_m596.glb
```

Reproduce: dragon `crystal_material.py work/mm8_m548_pre_material.glb export/mm8_m548.glb m548 subtle`; walker `... m596 full`; `... gloss` gives the
gloss-only variant. `work/` keeps both variants.

## User acceptance

Crystal Dragon: accepted 2026-10-19 (user: "crystal dragon ok") after the subtle-tone fix; installed as above.
