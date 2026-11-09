# MM7/MM8 native minimap ESRGAN study

[Open the comparison](http://127.0.0.1:8899/level_generation/minimaps/esrgan_study_20260928/).

**User-selected: `realesr-animevideov3`, native 2× inference, full strength.**
The user approved this exact variant for all 27 MM7/MM8 maps on 2026-09-28. The assistant's earlier 75% blend
recommendation remains a comparison trial; the selected artwork uses no blend. The 15 approved MM6 maps
retain their Blender light-noise treatment. Acceptance and deployment receipts are
[accepted.json](accepted.json) and [installed.json](installed.json).

The user selected an ESRGAN route on 2026-09-28. This supersedes the unfinished
[Blender calibration](../style_v2_20260927/README.md) as the active MM7/MM8 direction.

## What was compared

Eight native maps cover the reported failures and additional materials: Evenmorn, Avlee, Ravenshore, Garrote
Gorge, Harmondale, Bracada Desert, Ironsand Desert and Plane of Water. Each has seven neural settings plus
nearest and Lanczos baselines. The other 19 maps have the shortlisted model, both blends and both baselines.

| Model / setting | Observed result |
| --- | --- |
| Anime-video v3, direct 2× | Strongest model for this task. Cleans roads, roofs and shores while retaining most MM7 water texture. Removes too much of some MM8 source grain at full strength. |
| Anime-video v3, 4× reduced to 2× | Very similar; no compelling improvement at the delivered resolution. |
| General x4plus, 4× reduced to 2× | Over-interprets tiny structures and terrain. Broad smooth patches replace original water texture on Evenmorn and Avlee. |
| Anime x4plus, 4× reduced to 2× | Stronger flattening, hard outlines and simplified terrain. Poor fit for retaining the original painted style. |
| Anime-video 2× with TTA | Softer small buildings and texture; no useful improvement for this set. |
| Anime-video 2×, 50% blend | Very conservative, but retains more visible source pixelation. Available for comparison. |
| Anime-video 2×, 75% blend | Earlier assistant recommendation; retains some original grain. User selected the full-strength direct 2× version instead. |

The 75% setting is an explicit **output blend**, not a model denoise-strength parameter. The installed NCNN
program has no denoise-strength option. No input blur, median filtering, sharpening, colour grading or added
noise is used. Detail is enhanced from the original painting; there is no new geometry capture or imagegen.

The official [model list](https://github.com/xinntao/Real-ESRGAN/blob/master/docs/model_zoo.md) distinguishes
general, illustration and video models. The installed program's options match the
[NCNN usage documentation](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan#-usages).
The quality recommendation above comes from these local trials, not the model names or an objective quality score.

## Exact recipe and identity checks

1. Losslessly decode each archived original BMP to RGB. Never feed a previous generated minimap to the model.
2. Add a 16-native-pixel reflected border on every edge.
3. Run `realesr-animevideov3 -s 2 -t 0 -g 0 -j 1:1:1`; omit `-x` (TTA).
4. Remove exactly 32 output pixels on each edge. This leaves the original complete map extent at exactly 2×.
5. Save the full-strength result as an opaque lossless PNG. Do not blend, recrop, recenter or stretch.

Inference ran on the NVIDIA GeForce RTX 3060 Ti (device 0), using the existing NCNN executable. Model and binary
hashes are recorded in [approved_recipe.json](approved_recipe.json) and [exports.json](exports.json).
The direct-2× neural master is genuinely 2×; it is not enlarged again and described as a higher-resolution master.

Seven MM8 maps remain **1024×1020**, reflecting their native 512×510 canvases. The other 20 candidates are
1024×1024. All 27 have minimum smoothed-pixel error at zero translation. Phase correlation also reports zero
on 26 maps; Mount Nighon's phase-only peak is one pixel vertically. Its full-frame, town and coast pixel-error
checks favour zero shift, so no corrective warp was applied. These checks do not guarantee identical local contours.
Some fine dithering is intentionally retained. This is a modest faithful enhancement, not newly painted detail.

[validation.json](validation.json) verifies source hashes, candidate hashes/canvases, and unchanged installed maps.
[browser_check.json](browser_check.json) records browser image/control checks.

## Workspace and reproduction

- `maps/<world>/<map>/original.png`: immutable-native RGB reference.
- `maps/<world>/<map>/video2_master.png`: cropped direct-2× neural master.
- `maps/<world>/<map>/video2.png`: user-selected full-strength delivered image.
- `recommended/<world>/<map>.png`: copies of the user-selected full-strength images.
- `accepted/worlds/<world>/icons_x2/`: immutable accepted artifacts used by the global icon ledger.
- `raw/`: padded inference outputs; `input/` and `remaining_input/`: reflected source inputs.
- `contacts/`: model contact sheets and full-resolution detail comparisons.
- `scope.json`: all 27 source records; `runtime_before.json`: hashes of all 42 installed minimaps.

From the repository root, using Python with Pillow, NumPy and SciPy:

```sh
python3 -B level_generation/minimaps/esrgan_study_20260928/study.py prepare
# Run the five literal model commands saved in commands.txt to reproduce the eight-map comparison.
bash level_generation/minimaps/esrgan_study_20260928/commands.txt
python3 -B level_generation/minimaps/esrgan_study_20260928/study.py expand
tools/upscaling/realesrgan-ncnn-vulkan \
  -i level_generation/minimaps/esrgan_study_20260928/remaining_input \
  -o level_generation/minimaps/esrgan_study_20260928/raw/video2 \
  -n realesr-animevideov3 -s 2 -m tools/upscaling/models -g 0 -j 1:1:1 -t 0
python3 -B level_generation/minimaps/esrgan_study_20260928/study.py finish
python3 -B level_generation/minimaps/esrgan_study_20260928/study.py blend
python3 -B level_generation/minimaps/esrgan_study_20260928/study.py select
```

The study scripts refuse to regenerate a published revision; create a new dated workspace for future edits.
Publication uses `publish.py --apply` and the standard `deploy_icons.py --install` command. For redeployment,
run only `python3 -B level_generation/ui/hud_inventory/deploy_icons.py --install`; it reads the current accepted
index and cannot replay an obsolete revision. Use `--check` to verify installed hashes.

Publication also records an [input reconciliation](input_reconciliation/receipt.json) for nine independently
updated menu/font inputs. Their existing runtime bytes and all earlier reconciliation snapshots are preserved.
This updates the ledger's input history without changing icon contracts, menu files, fonts or equipment offsets.
