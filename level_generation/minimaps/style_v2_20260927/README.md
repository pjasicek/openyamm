# MM7/MM8 Blender shoreline and shading calibration

**Superseded, unpublished experiment:** on 2026-09-28 the user switched MM7/MM8 to
[native ESRGAN upscaling](../esrgan_study_20260928/README.md). The final shoreline-mask preparation was not rendered;
the retained images and exports reflect an earlier iteration. Do not treat this gallery as validated final artwork.

[Open the comparison](http://127.0.0.1:8899/level_generation/minimaps/style_v2_20260927/).

Four candidates respond to `test_img/2055.png`–`2058.png`: Evenmorn Island and Ravenshore are the initial calibration
maps; Avlee and Garrote Gorge are the cross-checks. These are review candidates. The accepted MM6 treatment and
the existing runtime minimap files remain at the previously deployed revision.

Use the left-image selector to compare the new render with either the native painting or the deployed capture.
Arrow keys change maps, B changes the left image, Space blinks the right image, and clicking either image zooms
both views at that location. Geometry outlines and exact canvas aspect ratios are retained.

## What changed

- Rounded coastline contours replace exposed tile steps. A directed marching-squares contour trace is smoothed
  along its arc length, then rasterized into a material mask. Narrow rivers are preserved by smoothing their banks
  as contours. A two-x2-pixel water expansion better separates the river from its thick dirt bank. Changes are
  restricted to a bounded coastal band; measured displacement is recorded separately from geometry checks.
  Water identity comes from tile families and the native magenta/cyan shore keys, not the colors of animated water
  textures. This avoids treating MM8's gray water highlights as small holes in the river.
  Native key stippling is converted to coverage before the contour is traced. Both the raw key mask and the
  recovered source coverage are retained; shoreline movement is measured against that recovered coverage.
- Water colors come from distance to the shoreline: cyan-to-deep-blue for MM7, dark bank/lavender shallows/dark
  offshore water for MM8. Texture variation increases offshore; shallow rivers remain calmer. Palette values are
  visual calibration parameters, not recovered original author settings.
- Material colors blend across terrain tiles. The selected light grain is retained. Smoothed height-derived normals
  control relief without moving terrain vertices. MM8 uses softer illumination than MM7.
- Buildings render separately from terrain, using native texture colors, shading-normal relief, a small shader bevel
  and local ambient occlusion. Building mesh positions and camera coordinates are unchanged. Original minimaps can
  have different pictorial silhouettes and object readability; these trials do not establish an exact art match.

The original painted minimap is used only for comparison. Its pixels are not pasted into the candidates.
Blender renders both passes with the new materials and lighting; Python prepares masks, composites the passes,
performs alpha-aware building sharpening and exports the final images. No imagegen is used.

## Retained artifacts

`recipe.json` contains the world-specific settings. Each `maps/<world>/<map>/` includes:

- `land_color.png`, `water_color.png`, `water_mask.png`, original water mask and shading normals.
- `terrain.blend` and `buildings.blend`, each retaining the exact lighting and view-layer selection of its pass.
- Raw terrain/building renders, processed building layer, 2048-square master and exact native-x2 export.
- `layers.ora`, with terrain and buildings separately editable in Krita.
- Source, capture and export hash records. The source geometry comes from the immutable earlier batch workspace.

`validation.json` checks the four exports, fixed mesh positions, native export dimensions, processed building alpha,
input/output hashes and all 42 existing accepted/runtime minimap files. `browser_check.json` exercises all four maps,
both baselines, zoom, blink, geometry outlines and the 1024×1020 MM8 canvases.

Shore-mask displacement is intentionally nonzero. The zero geometry-projection error does not mean the painted
shoreline or building silhouettes match the original exactly. Use the actual-size and zoomed comparisons to judge
those visual differences.

## Reproduce

From the repository root, after changing the recipe:

```sh
python3 -B level_generation/minimaps/style_v2_20260927/prepare.py
/snap/bin/blender --background --factory-startup --python level_generation/minimaps/style_v2_20260927/render.py
python3 -B level_generation/minimaps/style_v2_20260927/finish.py
python3 -B level_generation/minimaps/style_v2_20260927/validate.py
```

Run these steps sequentially. Blender can resume completed maps when their inputs and script hashes match.
The background renderer owns its separate process and preserves the live GUI's scenes. These scripts have no
acceptance or deployment operation. A later selected revision uses the canonical icons ledger replacement workflow.
