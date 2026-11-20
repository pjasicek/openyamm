# Reproducing vinevi's minimap process

[Open New Sorpigal comparison](http://127.0.0.1:8899/level_generation/ui/hud_inventory/minimap_study_20260927/).
The default pair is **original → gentler version**. The next button compares the previous stronger vinevi version against it.
Dropdowns also offer the new lighting-only render and a graded version without terrain edge breakup.

The gentler revision raises the sun from 15° to 20°, reduces its strength from 9 to 6.6 and increases fill from .28
to .40. Contrast drops from 1.12 to 1.06. Terrain normals retain 15% of their native triangle definition, Cycles
denoising is disabled, and Random Pick uses a smaller radius and lighter blend. Geometry remains unchanged.
The previous renders, layered image and recipe are retained in `new_sorpigal/vinevi_v1/`; its Blender scene is
`new_sorpigal/new_sorpigal_vinevi_v1.blend` beside the shared texture directory.

[Previous shading versus gentler revision](review_vinevi_full.png) · [Original versus new town, with geometry outlines](review_vinevi_town_alignment.png)

This implements the published method from vinevi's
[Making minimaps for Might and Magic](https://www.moddb.com/mods/minimaps-for-might-magic/tutorials/making-minimaps-for-might-and-magic)
(2020). **These numeric settings are our reconstruction, not the author's recovered presets.** The article supplies
the operations but no numerical lighting/filter values. The linked public Krita project download returned HTTP 403
on 2026-09-27. No claim is made about the original New World Computing production process.

## Reproduced operations

- Cycles, orthographic overhead camera, warm sun with cool world fill; cast shadows disabled.
- Separate terrain and building renders, with terrain holdout preventing buried geometry from showing through.
- Terrain-only Random Pick approximation: deterministic neighboring-pixel sampling with a fixed seed.
- Independent building levels, then contrast, saturation and sharpening on both layers.
- Composition at 2048×2048, followed by one Lanczos reduction to 1024×1024.

The filtering is implemented independently in Python using NumPy, Pillow and SciPy; it is not Krita's exact filter
implementation. The [Krita documentation](https://docs.krita.org/en/reference_manual/filters/other.html) describes
Random Pick as a pixel fringe effect. Here, neighbor sampling is bounded to **one x2 output pixel**, restricted to
terrain (the gentler revision reduces this to **half an x2 pixel**). Buildings never pass through it.
The no-pick version removes that operation entirely.

## Recorded settings

The authoritative editable settings are in [vinevi_recipe.json](vinevi_recipe.json).

| Stage | Settings |
| --- | --- |
| Camera | North up, XY center (0,0), extent 65,536 world units, orthographic scale 512 at 1:128 units |
| Sun | Northwest (315° clockwise from north), elevation 20°, strength 6.6, linear RGB (1, .84, .62) |
| World fill | Strength .40, linear RGB (.35, .5, 1) |
| Shading | 85% smooth / 15% face normals; unchanged terrain heights; no cast shadows or diffuse bounce lighting |
| Cycles | 64 samples, no denoising, seed 60927, Standard view, None look, exposure 0, gamma 1 |
| Terrain Random Pick approximation | Radius 1 master pixel; 25% selection probability; 30% blend; seed 20260927 |
| Building levels | Input black 0, white .85, midtone gamma 1.16; output 0–1 |
| Final contrast | 1.06 about encoded-RGB pivot .30 |
| Final saturation | 1.13 about Rec.709-weighted encoded-RGB gray |
| Sharpening | Gaussian unsharp radius 1.2 master pixels, amount .30, channel threshold 2/255 |

Our import scale differs from the tutorial's .003 because the verified capture already uses 1/128. Camera extent
uses the same scale, so projection is unchanged. The right/bottom world margin is included explicitly rather than
adjusting alignment by eye. Current restored textures are used, which can differ from the tutorial's source textures.
The RGB PNG output does not need the indexed palette/BMP conversion required by the original game.

## Results and limits

This version gives stronger relief and less washed-out color than the previous generic capture. On the fixed
original-image grass mask, median encoded-RGB luma is **73.9**, versus **73.7** in the original and **107.5** in the
previous generic styled capture. Median HSV saturation is **64.3%**, versus **67.3%** and **45.6%**, respectively. These are
descriptive measurements, not proof of visual equivalence: the new shaded hills have a different tonal distribution.
The grass 10th-to-90th percentile luma range narrows from about 53–101 in the first vinevi version to 60–93 here.

The water still reveals its repeated source texture, and sprite vegetation remains absent. This is a useful
lighting/postprocessing reproduction, not a complete reconstruction of the original painted artwork. Only New
Sorpigal is processed. Runtime images and this minimap's acceptance records remain unchanged.

Validation in [vinevi_comparison.json](new_sorpigal/vinevi_comparison.json):

- All 85 BModels, 4,486 model vertices and 16,384 terrain vertices retain their coordinates.
- Model camera projection error: **0 x2 pixels**; processed building alpha equals rendered alpha exactly.
- Terrain neighbor sampling is explicitly bounded; its color fringe can move locally by up to half an output pixel.
- Export dimensions, runtime source hashes and this target's ledger/index acceptance are checked.
- [Browser checks](browser_check.json) exercise image loading, comparison buttons, zoom, outlines and blink.

## Editable artifacts and rerun

- [Blender scene](new_sorpigal/new_sorpigal_vinevi.blend): independent scene with Terrain and Objects view layers.
- [Krita-compatible OpenRaster](new_sorpigal/new_sorpigal_vinevi.ora): two processed layers at 2048×2048; open in Krita.
  These are raster layers, not live Krita filter masks. Raw layer PNGs and the recipe remain available for reprocessing.
- Raw renders: `new_sorpigal/vinevi_terrain_master.png`, `vinevi_objects_master.png`.
- Processed layers: `vinevi_terrain_processed_master.png`, `vinevi_objects_processed_master.png`.
- Full candidate: [vinevi_x2.png](new_sorpigal/vinevi_x2.png), with retained 2048×2048 `vinevi_master.png`.

After editing lighting settings, run in Blender (substitute the checkout path if needed):

```python
exec(compile(open('/home/pjasicek/github/OpenYAMM/level_generation/ui/hud_inventory/minimap_study_20260927/render_vinevi.py').read(),
             'render_vinevi.py', 'exec'), {'REPO': '/home/pjasicek/github/OpenYAMM'})
```

Then, from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/minimap_study_20260927/finish_vinevi.py
```

Only the second command is needed after postprocessing changes. It regenerates the candidate/layers and updates
the comparison manifest. `finish.py` also preserves the new comparison variants when refreshing the older study.
Neither command installs artwork or modifies ledger decisions.
