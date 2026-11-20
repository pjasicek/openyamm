# New Sorpigal terrain master study

The current darker dirt and completed land transitions are in the [transition review](../mm6_new_sorpigal_transitions/review.html).
The [earlier master study](index.html) preserves previous comparisons at the four requested camera poses. Water remains outside scope.

## Selected masters

| Material | Selected file | Status and use |
|---|---|---|
| Grass | `generated/v1/grass_512.png` | Accepted. Base material. |
| Dirt | `generated/v6/dirt_512.png` | Accepted current darker redo. |
| Cobbles | `generated/v1/cobbles_512.png` | Accepted as a masked overlay material over dirt. |
| Volcanic rock | `generated/v2/volcano_512.png` | Retained provisionally; user notes the original was lighter. |

[Material decisions](material_decisions.json) records the selected versions, paths, hashes and composition roles.
The user superseded the earlier dirt v4 selection after `test_img/1263.png`: restore the darker original brown feeling
and remove conspicuous repeat patterns. V5 redistributes the clods; v6 darkens and mutes the palette. V4 remains archived.

The cobble master is a full square of **material**, not a complete road tile. For each native road shape, compose:

`road tile = dirt master × (1 − road mask) + cobble master × road mask`

White in the road mask exposes cobbles; black retains underlying dirt. Preserve the native path width, turns,
junctions, ends and orientation through their respective masks. The nine full-paving replacements in earlier game
captures were only diagnostic material swatches. They must not become the final road layout or final mixed tiles.
Road mask extraction and composition remain the next phase; no masks were generated in this selection update.

The material sheet, cards and current x2 game screenshots use selected dirt v4. See the saved prompts and provenance
for generation history. Earlier x4 captures remain available under their version directories.

## Runtime exports: x2

[runtime_x2/](runtime_x2/README.md) contains four **256×256 RGB PNG** material exports and three native base overrides
under `overrides/worlds/mm6/terrain_x2/`. Grass v1, dirt v4, cobbles v1 and volcano v2 were reduced from the unchanged
512px masters using Lanczos. The export manifest records source and output hashes.

Author masks and mixed tiles at 512px, then reduce each completed composite to 256px for runtime. The cobbles export
is a separate material reference; its native road overrides require the later mask pass. This is a partial base
export, not a completed transition pack. Runtime captures use an isolated asset tree, leaving development assets intact.

```sh
python3 level_generation/terrain/mm6_new_sorpigal_master_study/prepare_trial.py
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm6_new_sorpigal_master_study/capture_study.py runtime_x2
python3 level_generation/terrain/mm6_new_sorpigal_master_study/build_review.py
```

`prepare_trial.py` defaults to `runtime_x2` and regenerates the export. To export without preparing a game trial,
run `export_runtime.py` in the same directory.

## What the screenshots contain

- Original: native terrain at x1. Current trial: 256×256 terrain at x2; all other asset categories remain x1.
- The three standalone masters replace `6grastyl`, `6dirttyl`, and `6voltyl`.
- MM6 has no standalone cobble master. Current x2 captures keep all nine original road textures. Historical x4
  trials used full paving as a diagnostic material swatch. No land/road masks have been extracted in this pass.
- All mixed grass/dirt, rock/dirt and shoreline tiles retain original artwork, nearest enlarged. This makes the
  unfinished borders obvious. Do not assess those borders as completed transitions.
- Water frames retain the original x1 appearance at the trial resolution; no water generation was performed.
- Grass and dirt poses supplied by the user are identical and face grass. The road view and town overview supply dirt
  context. The dirt right beside the road can still belong to an original mixed tile.
- Images are actual 1600×1200 game captures, with HUD, 8× anisotropic terrain filtering and the same executable.
  Actors and animated scenery can advance between captures. These are visual comparisons, not GPU benchmarks.

The supplied headings in degrees were converted to radians without using the more coarsely rounded radian values.
Exact positions, headings and pitches were checked with the in-game `loc` console command; see
[original pose verification](references/pose_verification.png) and each trial's linked console screenshot.
Native save fixtures keep flight active so elevated poses cannot fall to ground level. The rejected early ground-level
capture is isolated in `review/rejected_ground_level_capture/` and is not used in comparisons.

## Generation and files

Built-in `image_gen` was used: four separate material calls, one targeted rock revision, and three dirt revision calls
(pattern distribution, palette correction, then a return to v1 for border repair). No CLI/API fallback.
Prompts are saved in [prompts/](prompts/), and source output paths in [generated/provenance.json](generated/provenance.json).
Native tile artwork was the material reference; actual game screenshots supplied style and scale context.
Raw outputs are preserved, with 512×512 Lanczos reductions for authoring and 256×256 runtime exports. No colour correction, procedural
repainting, or automatic material-mask extraction was applied after generation.

- `generated/v1/`: four raw first-pass outputs and their 512px textures.
- `generated/v2/`: rock revision and intermediate dirt pattern revision, with 512px textures.
- `generated/v3/`: the dirt candidate with its colour corrected by image generation.
- `generated/v4/`: selected dirt master, based on the preferred chunky v1 dirt.
- `review/original/`, `review/v1/`, `review/v2/`, `review/v3/`: game captures and metadata.
- `runtime_x2/`: selected 256px exports, native base override layout and manifest.
- `review/runtime_x2/`: game captures using the selected masters at the approved runtime resolution.
- `review/dirt_v1_repeat_3x3.png`: preserved dirt repeat before revision; compare with `review/dirt_repeat_3x3.png`.
- `review/*_repeat_3x3.png`: unmodified material repeated nine times for seam/pattern inspection.
- `review/material_checks.json`: dimensions, hashes, colour averages and edge discontinuity diagnostics. Cobbles'
  native average includes dirt borders and is not a like-for-like paving colour measurement.
- `poses.json`, `references/poses/*.oysav`: camera definitions and native save fixtures.
- `prepare_pose_save.cpp`: small tool using OpenYAMM's own save serializer to create/round-trip the flying fixtures.

## Reproduce the material trials

To reproduce the historical diagnostic screenshots, from the repository root with the existing game build:
The explicit `--road-swatches` option recreates their full-tile paving. Without that option, original road tiles are
retained until proper cobble-over-dirt mask composites exist.

```sh
python3 level_generation/terrain/mm6_new_sorpigal_master_study/prepare_trial.py --variant v1 --road-swatches
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm6_new_sorpigal_master_study/capture_study.py v1
python3 level_generation/terrain/mm6_new_sorpigal_master_study/prepare_trial.py --variant v2 --road-swatches
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm6_new_sorpigal_master_study/capture_study.py v2 --only volcano
python3 level_generation/terrain/mm6_new_sorpigal_master_study/prepare_trial.py --variant v3 --road-swatches
xvfb-run -a -s '-screen 0 1600x1200x24' python3 level_generation/terrain/mm6_new_sorpigal_master_study/capture_study.py v3 --only overview cobbles
python3 level_generation/terrain/mm6_new_sorpigal_master_study/build_review.py
```

Captured trials live under `/tmp/openyamm-sorpigal-terrain-master-study/{v1,v2,v3,runtime_x2}`. The x2 trial uses
selected dirt v4. Their terrain overrides are independent copies;
the rest of the content is mirrored using copied metadata and links to whole mounted art folders. Original
`assets_dev` files, maps, renderer code and the user's root settings are not modified by this study.
For baseline recapture, place `references/settings_original.ini` at the `original/settings.ini` stage path and run
`capture_study.py original` under the same virtual display. Capture fixtures are tied to the current save format.

Use the selected masters for the next mask/compositing phase. Reconstruct related mixed tiles from shared materials
and reviewed masks, with cobbles masked over dirt. Keep shoreline alpha/water work separate until that pass.
