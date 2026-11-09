# MM7 flowers: static 3D decorations (2026-10-15/16)

Batch `flowers/` of the MM7 3D decorations project (`../BRIEF.md`, `../README.md`). It covers flower01–13 and flower16,
all outdoors, with 803 placements in total. They are built on the MM6 flower method
(`../../mm6_new_sorpigal_3d/flowers/`): a painted card atlas, then a Blender clump with three LODs, then link, cut and
validate, then review sheets.

## Status

All 14 models are installed and were reinstalled after the quality pass (2026-10-16) with `tools/install_model.py <work/<id>/mm7_deco_<id>.glb> --engine --name
mm7_deco_<id>.glb`. Their sources are in `assets_source/engine/models/` and the cooked runtime copies in
`assets_dev/engine/models/`. Bindings are not added: `decorations.yml` belongs to the orchestrator.

## Build

```bash
./build.sh flower01 [--install] [--grade]   # atlas -> clump -> link/cut/validate -> renders -> sheet
./work/build_all.sh [--grade]               # every species; atlas owners first (flower12, flower16), then 11, 13
```

- `--grade` first renders the model and multiplies the atlas grading gains in `work/<atlas>/grade.json`, then
  rebuilds.
  - The gains are the damped ratios of sprite to render mean colour for flower and foliage pixels
    (`common.flower_mask`).
  - Flowers get a brightness-only gain, capped to 0.75–1.25 in total.
- Shared atlases:
  - flower11 uses flower12's atlas (the same art).
  - flower13 uses flower16's atlas.
  - Only the atlas owner grades.

## Construction (scripts)

- `common.py`: sprite sizes in world units (the x2 frame's opaque art, halved), the atlas layout and the grading
  masks.
- `paint.py` and `make_atlas.py`: each species gets its own 1024² atlas (RGBA plus a normal map from painted
  height), painted with numpy from shared painters. There are no external images. The layout:
  - two grass-blade strips;
  - two large card regions (tufts, leaf masses, moss, fern sprays, foxglove bells);
  - eight head slots;
  - two thin strips (stems, wrapped bloom sides).
- `build_plant.py` (Blender, headless) builds these parts:
  - curved blade strips (4/2 segments);
  - flower heads as cupped cones mapped from above;
  - double blooms (rose, cabbage rose, peony): lathed balls with a wrapped petal band and a rosette cap;
  - water lilies: two stacked star cones;
  - irises: three standards and three falls;
  - foxglove spikes: rows of bell cards round a thin core at LOD0 and crossed silhouette cards at LOD1/LOD2, tinted
    white, coral, pink or lilac through COLOR_0;
  - lily pads: rimmed discs (`profile: rim`) mapped from above;
  - leaves folded along the midrib, shell cards for mounds, and crossed tuft cards for the far levels.

  LOD0 is fitted to the sprite. `fit_spread()` first moves the part anchors horizontally until the width-to-height
  ratio matches the sprite's. Then a uniform scale fits the art height, with a residual horizontal correction of at
  most ±3 %. The coarser levels never exceed LOD0's height. The material and extras are as on the MM6
  flowers: MASK 0.5, double-sided, `openyamm_wind` 0.02, `openyamm_specular` 0.1, `openyamm_translucency` 0.3.
- `post_process.py`:
  - links the LODs (`tools/link_static_model_lods.py`) and cuts the cards (`tools/cut_foliage_cards.py`);
  - validates against the budgets of 1500 / 700 / 300 triangles, with COLOR_0 present and the base on the ground;
  - with `--install`, installs the model.
- `render_review.py`, `sheet.py` and `before_after.py` (`build.sh` switches the review renders to CPU Cycles when less than 1.5 GB of GPU
  memory is free; grading is skipped on those):
  - Eevee renders: front, three-quarter and top for LOD0, and front for each LOD.
  - The sheet shows the sprite next to LOD0 at the same metres per pixel, with the LODs in the second row.

## Sources and licences

All textures are painted procedurally by `scripts/paint.py`. This is original work for this project, with no
external assets.

## Models

These are the values after the 2026-10-16 quality pass. Source GLB sizes include the 1024² base colour and normal
atlases (PNG).

| Sprite | Placements | Model | LOD triangles | Source size | What it is |
|---|---|---|---|---|---|
| flower01 | 180 | `mm7_deco_flower01.glb` | 1294 / 327 / 77 | 1.19 MB | magenta cosmos over arching grass |
| flower05 | 128 | `mm7_deco_flower05.glb` | 832 / 596 / 290 | 1.31 MB | white peonies cupped in olive leaves, needle sprays |
| flower16 | 125 | `mm7_deco_flower16.glb` | 795 / 269 / 146 | 0.93 MB | white water lilies on rimmed, slit, mottled pads |
| flower03 | 83 | `mm7_deco_flower03.glb` | 1356 / 476 / 171 | 1.37 MB | three red roses with leaves in striped grass |
| flower04 | 63 | `mm7_deco_flower04.glb` | 1432 / 684 / 275 | 1.45 MB | cream cabbage roses edged pink, broad leaves, grass |
| flower02 | 53 | `mm7_deco_flower02.glb` | 1294 / 327 / 77 | 1.20 MB | yellow buttercups over grass |
| flower06 | 51 | `mm7_deco_flower06.glb` | 762 / 262 / 110 | 1.23 MB | yellow rudbeckia on a leaf mound between grass tufts |
| flower08 | 39 | `mm7_deco_flower08.glb` | 914 / 348 / 150 | 0.90 MB | magenta irises on stalks over sword leaves |
| flower11 | 39 | `mm7_deco_flower11.glb` | 798 / 386 / 188 | 1.37 MB | pink primula mound with a grass ring (flower12 atlas) |
| flower10 | 16 | `mm7_deco_flower10.glb` | 618 / 312 / 170 | 1.69 MB | white daisy mound over moss |
| flower13 | 14 | `mm7_deco_flower13.glb` | 1411 / 421 / 164 | 1.07 MB | water lilies on pads, grass in the middle (flower16 atlas) |
| flower09 | 10 | `mm7_deco_flower09.glb` | 1060 / 279 / 83 | 0.96 MB | white star flowers (brown edges) over grass |
| flower07 | 1 | `mm7_deco_flower07.glb` | 892 / 232 / 54 | 0.99 MB | foxglove spikes of bell cards: white, coral, pink, lilac |
| flower12 | 1 | `mm7_deco_flower12.glb` | 510 / 290 / 158 | 1.30 MB | pink primula mound |

- Review sheets are `review/<id>_sheet.png`. Before/after sheets for the models the quality pass changed are in
  `review/compare_20261016/`: the morning's top row over the current sheet. The older sheets are kept in
  `review/before_20261016/`.
- The bindings in `assets_dev/engine/models/decorations.yml` are unchanged and still valid: height = `art_height`,
  `height_jitter` 0.15, `lod_pixels` [500, 220, 100]. The quality pass changed no heights.

## Quality pass (2026-10-16)

- **Water lily pads** (flower16, flower13):
  - Each pad is now a nearly flat disc with its outer quarter turned up into a rim (`profile: rim`, 8 segments, two
    rings).
  - The painted pad has a dark-edged slit, mottling, branching veins, a glossy rim and rust-tinged edge patches.
  - The pads are graded again to the sprite's foliage mean: render 59/105/53 against the sprite's 67/113/59.
- **Foxglove** (flower07):
  - LOD0 spikes are rows of single bell cards (5, 4 and 3 per row, 9 rows) round a thin core, with crossed bud
    cards at the tip. Each bell is painted with a flared mouth and a spotted throat.
  - The tints are more saturated.
  - LOD1 and LOD2 keep the crossed silhouette cards, now painted with the same bells.
- **flower05:** the blooms are a tight cluster on short stems, cupped in leaves. The width now comes from the olive
  leaves round the base.
- **Domes** (flower10, 11, 12): the mound is a superquadric (n = 2.6), with a flatter top and steeper sides than the
  old ellipsoid. flower10 has 46 daisies instead of 34.
- **Width fit:**
  - The fit no longer squeezes geometry. `fit_spread()` moves each part's anchor horizontally (sizes unchanged)
    until LOD0 has the sprite's width-to-height ratio.
  - Only a residual horizontal correction of at most ±3 % is applied as scaling.
  - flower05's bloom cluster and flower09's heads keep their positions; the grass and leaves move instead.
- **LOD2:** raised only where the far level lost coverage: flower06 98 → 110 (coverage 0.78 → 1.06), flower09
  71 → 83 (0.80 → 1.11), flower08 132 → 150 (0.73 → 0.87). flower01, 02 and 07 keep their LOD2 (77, 77, 54
  triangles; coverage 0.94–1.21).
- `check_winding.py` reports 0 inverted parts for all 14. The material is double-sided, as on all foliage.
- No Codex or Meshy jobs were used.

## Compromises

- **Shape.**
  - Clumps are round in plan, while the sprites are seen from one side, so heads that face sideways read edge-on from
    some angles.
  - The heads are flat painted cones, not sculpted petals.
  - flower13's central grass covers more of the lilies than the sprite's grass behind them does.
  - The foxglove bells are paler and spikier than the sprite's dense, saturated spikes.
  - flower06's grass tufts arch less than the sprite's.
- **Grading.** Flower gains are brightness only and capped, so yellow and pink petals do not wash out. Those heads
  stay a little darker than the sprites' highlights.
- **LOD2.** It stays below 100 triangles on flower01, 02, 07 and 09 (54–83), where its coverage already matches
  LOD0.
- **CPU renders.** Review renders fall back to CPU Cycles when other sessions hold the GPU. Those renders are darker
  and are never used for grading. The quality-pass sheets are all Eevee.
- **Painting.** Everything is procedural. Leaf and petal detail is simpler than the sprites' pre-rendered shading.
