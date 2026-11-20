# New Sorpigal minimap comparison

[Open the interactive comparison](http://127.0.0.1:8899/level_generation/ui/hud_inventory/minimap_study_20260927/).

This is the historical comparison pilot for MM6 `oute3.odm`. Its images and source receipts preserve the alternatives
reviewed before replacement. The **light-noise** treatment was subsequently selected and authorized for all 42
MM6–MM8 outdoor maps. Current batch status, accepted artifacts and deployment receipts belong to the
[canonical minimap workspace](../../../minimaps/README.md). No imagegen was used.

Retained comparison: **light and medium terrain noise** over the gentler capture, with unchanged building artwork and
no coordinate displacement. The viewer defaults to the gentle base versus light noise. Fixed-seed, monochrome
variation at several scales breaks up uniform grass/dirt; open water is excluded using an unlit material-color mask.
See [noise comparison](noise_comparison.png) and [settings/checks](new_sorpigal/noise_trial.json).
The pilot's reproduction scripts verify its historical source hashes. Use the canonical workspace for future
revisions and redeployment after installation.

The first batch request was stopped before rendering or publication while noise was explored. The later instruction,
“yes light noise is the winner here. accept this approach, regen all minimaps and deploy them to icons_x2”,
supersedes that stop. Medium noise and the other alternatives remain comparison candidates.

Follow-up: [historical evidence and measured visual differences](TECHNIQUE_RESEARCH.md).
The [vinevi process reproduction](VINEVI_PROCESS.md) is now rendered and selected by default in the browser:
warm sun/cool fill, separate terrain/buildings, no cast shadows, selective filtering and color grading.

## Findings

| Route | Result in this pilot | Main tradeoff |
| --- | --- | --- |
| Native painting → Real-ESRGAN anime-video x2 | Best neural-upscale trial here; smoother contours, recognizable native terrain and landmarks. | Some source dithering remains. Tiny features soften; local neural changes still need inspection. |
| Native painting → x4plus → Lanczos x2 | Sharper small structures, but conspicuous grid-like water artifacts. | Not recommended for a bulk minimap pass with these settings. |
| Native painting → mild denoise → either model | A little calmer; the anime-video variant avoids the worst grid artifacts. | Fine roof/landmark detail softens further. |
| Orthographic terrain/BModel capture → deterministic styling | Precisely registered to current geometry; all 4,486 model vertex projections match the runtime transform. | Current prototype lacks sprite vegetation and has more visibly tiled coastlines. Lighting and water need further art direction. |
| Vinevi's layered render/filter process | Stronger hill shading, richer color, brighter buildings; separate editable layers. | Numeric settings reconstructed from the written method; repeated water texture and missing vegetation remain. |

For the lowest-cost faithful replacement, begin with **anime-video x2 without pre-denoising** and inspect each
map's structures at full x2 resolution. The standard x4plus model is not automatically the better choice for
these tiny, dithered maps. This conclusion is from this comparison, not a universal model-quality claim.

For maps whose actual terrain/buildings have changed, the **geometry capture** is the more dependable foundation:
it derives positions from the map itself. It can be polished without relocating features. A useful next improvement
would be deterministic overhead tree/rock symbols at the actual decoration coordinates, plus a calmer water
material. Vertical billboard sprites do not provide authentic overhead crowns; they should not simply be tilted
flat and mistaken for a true top-down capture. No vegetation symbols have been added in this pilot.

The previously installed generated restoration remains in the viewer as a comparison. Its town buildings visibly
drift from model outlines. The original map itself is a painted/rendered representation and should also be checked
against geometry; preserving the original does not prove perfect registration to today's map.

## Use the comparison

- Buttons select the new layered process against the original or previous capture, plus the earlier upscale/capture pairs.
  Each dropdown exposes all sixteen images, including both noise trials, the earlier stronger vinevi version,
  lighting-only and no-terrain-fringe comparisons. The default compares the gentler base with light terrain noise.
- **1 / 2 / 3** select the full map, town or northern islands. Drag to pan and use the wheel/slider to zoom both views.
- **L** toggles actual model outlines; **Landmark anchors** adds named model-center controls.
- Hold **Space** to blink the right view back to the original. Both images share the same map coordinates.
- **Open full image** opens the exact 1024×1024 candidate, independent of browser display scaling.

[Full comparison screenshot](review_full.png) · [Town alignment screenshot](review_town_alignment.png)

## Registration and scope

The runtime defaults in `game/ui/GameplayOverlayTypes.h` and `GameplayMinimapTransform.h` use:

```text
u = (world_x + 32768) / 65536
v = (32768 - world_y) / 65536
x2 pixel = (u * 1024, v * 1024)
```

New Sorpigal has no map-presentation override. The camera is north-up and orthographic, centered on world XY=(0,0),
with a 65,536-unit extent. Do not fit the camera to occupied land or add automatic margins. That would misalign
the minimap's party marker and landmarks even if the image looked correct.

The terrain uses the actual 127×127 cells from 128×128 samples, with the runtime's anti-diagonal triangle split.
An unlit/differently shaded view must keep the same camera. The final 512-unit south/east margin beyond the final
terrain sample is water in this pilot; it is not filled by stretching the terrain. BModels retain their full
coordinates and texture UVs. Heights and all geometry positions remain unchanged; smooth normals and the optional
height-derived relief pass only alter shading.

All four neural trials report **zero whole-frame translation** against the native image. This phase-correlation
check is not proof against local neural shape changes. All **4,486 BModel vertex controls** report **0 x2-pixel
camera projection error**. Canvas validation requires every displayed image to be 1024×1024. Browser checks cover
image loading, shared zoom, geometry overlays, method selection and blink comparison.

[comparison.json](new_sorpigal/comparison.json) records hashes and measured checks.
[browser_check.json](browser_check.json) records the isolated-browser check.
[outdoor_scope.json](outdoor_scope.json) indexes **42 currently present MM6–MM8 outdoor maps**: 15 MM6, 13 MM7,
14 MM8; all 42 have accepted minimap entries. Only New Sorpigal has been processed. This list is not a claim that
every retained/unused map icon is active. Indoor vector automaps and MM9 presentation images are separate paths.

## Files and reproduction

- `new_sorpigal/original.png`: lossless RGB decoding of the archived original 512×512 minimap.
- `new_sorpigal/sources.json`: source, installed image and all selected texture hashes.
- `new_sorpigal/esrgan_*_master.png`: cropped x4plus masters; final exports end in `_x2.png`.
- `new_sorpigal/esrgan_anime_raw/`: padded direct-x2 anime-video outputs.
- `new_sorpigal/blender_master.png`, `blender_smooth_master.png`: 2048×2048 captures before final filtering.
- `new_sorpigal/new_sorpigal.blend`: isolated, editable base scene with relative material references.
- `new_sorpigal/materials/`: assembled actual tile textures and restored BModel textures; no generated replacements.
- `new_sorpigal/blender_capture.json`: camera, projection checks and rendering limitations.

Run from the repository root (Python dependencies: Pillow, NumPy, SciPy):

```sh
python3 -B level_generation/ui/hud_inventory/minimap_study_20260927/prepare.py

tools/upscaling/realesrgan-ncnn-vulkan \
  -i level_generation/ui/hud_inventory/minimap_study_20260927/new_sorpigal/esrgan_input \
  -o level_generation/ui/hud_inventory/minimap_study_20260927/new_sorpigal/esrgan_raw \
  -n realesrgan-x4plus -s 4 -m tools/upscaling/models -g 0 -j 1:1:1

tools/upscaling/realesrgan-ncnn-vulkan \
  -i level_generation/ui/hud_inventory/minimap_study_20260927/new_sorpigal/esrgan_input \
  -o level_generation/ui/hud_inventory/minimap_study_20260927/new_sorpigal/esrgan_anime_raw \
  -n realesr-animevideov3 -s 2 -m tools/upscaling/models -g 0 -j 1:1:1
```

The native input receives a 16-pixel reflected border, removed at the corresponding output scale. x4plus runs
at its actual x4 scale before Lanczos reduction to x2. The alternate input blends 40% of a 3×3 median-filtered
version into the native painting. Final inference was verified on an NVIDIA RTX 3060 Ti; the first sandbox run
used llvmpipe, so it was repeated on the GPU. Both showed the x4plus water problem.

In Blender MCP (preserves unrelated scenes), with the checkout's actual absolute path:

```python
exec(compile(open('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory/minimap_study_20260927/render_blender.py').read(),
             'render_blender.py', 'exec'), {'REPO': '/home/pjasicek/github/OpenYAMM'})
```

Then finish derivatives and alignment checks:

```sh
python3 -B level_generation/ui/hud_inventory/minimap_study_20260927/finish.py
```

The styled capture uses a small bilateral color filter, gamma 0.88 and soft relief derived from the real heightfield.
The heightfield is filtered for the shading calculation only; there is no geometry or image-coordinate warp.
The base capture omits actors, decoration billboards, event-driven state, runtime baked lighting and animated water.
No engine build, runtime package rebuild or installation is required to view this trial.
