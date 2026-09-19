# New Sorpigal material study

Texture-inspected content pass for the four viewpoints in `test_img/2006.png` through
`2009.png`. Uses the current face material masks and terrain material LUT. It does
not change diffuse artwork, geometry, lighting bakes, or the user's wetness setting.
The default review is dry; a second capture uses `video.material_wetness=0.45`.

| Surface | Interpretation and treatment |
| --- | --- |
| Tavern porch, `cbrdbrck` | Fired clay brick. Modest worn-face sheen, rough mortar; stronger response when damp. |
| Tavern block walls | Rough masonry; existing restrained stone material retained. |
| `tavldyle`, `tavldyre` | Carved stone figures, not metallic ornaments. Rough scalar material. |
| `tavlgdr` | Timber double door, blue enamel arch, metal masks and handles. Separate smoothness regions. |
| `tavsmdr` | Timber side door inside a carved stone arch; smoother metal ornament. |
| `tavwctr`, `tavwle`, `tavwre` | Stained glass inside masonry. Smooth glass and very faint emissive contribution confined to panes. |
| `tavrf` | Horizontal timber fascia; restrained wood response. |
| `rblbw` | Fieldstone wall. Coarse stone, matte joints, mild damp darkening. |
| `pxstr*` house walls | Matte plaster, moderately smoother timber framing, smooth leaded glass. Window variants have different outlines. |
| `pxstrdr` | Carved wood door, glass transom and metal latch. |
| `armorpor` | Painted wooden sign with metal straps; painted armor emblem does not emit light. |
| `pxshings`, `plruf01`, `pbtrm` | Weathered wood shingles/roof boards and trim. Low dry specular response. |
| `6grastyl` | Matte grass; low wetness response. |
| `6dirttyl` | Rough earth; restrained damp darkening, no puddle-like dry sheen. |
| Road and transition tiles | Retain current neutral material response; see limitation below. |

Definitions live in `assets_dev/engine/rendering/surface_materials.yml`. Matching is
by texture name: other MM6 maps using these textures inherit the treatment. These
are not map-exclusive overrides. Masks live in the MM6 world package.

## Mask authoring

`regions.json` describes inspected regions in x2 texture pixel coordinates. Regions
are applied in order. Luminance/color thresholds further exclude dark lead lines,
mortar or cracks within selected regions. These are approximate semantic masks,
not physically measured material properties. The original texture layout should
remain compatible through normalized UVs; visual review here used x2 textures.

Rebuild with Pillow and NumPy installed:

```sh
python3 level_generation/materials/mm6_new_sorpigal/build_masks.py
```

The 16 generated PNGs contain linear numeric data:

- R: select roughness toward the shader's smooth limit (0.10).
- G: multiply wetness exposure.
- B: select emissive contribution.
- A: 255, unused.

R does not independently change specular intensity or encode metallic properties.
Material scalars therefore remain conservative on mixed plaster/glass textures.
`manifest.json` records source/output hashes and dimensions. Reinspect masks if the
diffuse texture layout changes. Do not apply sRGB conversion to these mask values.

## Review and limits

Review artifacts are in `output/sorpigal-material-study/`: `compare.html` switches
among the four supplied cameras and wipes between before, dry and damp captures.
The three tour YAMLs preserve camera poses. Captures use the ordinary desktop game,
OpenGL 3.3, x2 textures and terrain, with terrain decorations disabled consistently.
NPCs and animation move between runs; compare static surfaces. The renderer log did
not identify the GPU model, and these captures are not performance measurements.

The result is subtle at these mostly shaded views. Glass and metal can have sharper
direct-light highlights, but this pass adds neither environment reflections nor
normal-mapped relief. It is not a complete UE-style visual upgrade.

Follow-up investigation found the practical effect inadequate: compared with materials
disabled, the sampled dry brick porch was 99.98% pixel-identical and the door 99.80%.
An isolated strong-emission diagnostic confirmed table and mask application; the main
limitation is the direct-light-only response and conservative settings, not loading.
See `output/sorpigal-material-study/investigation.md` for measurements and evidence.

Road textures `6drsr*` combine paving and soil in one tile. Existing grass/dirt
decoration masks control vegetation placement, not material shading. Terrain
transition tiles are currently neutralized by the material LUT, and face masks are
not supported by the terrain shader. Selective road sheen therefore needs a terrain
material-mask extension, including correct transition blending, before road masks
would have any effect. This pass does not claim to implement that extension.

Validation: all four dry and damp views captured successfully; surface-material
unit tests passed (15 cases, 176 assertions). Content paths, mask dimensions,
opaque alpha, hashes and unique exact texture ownership were checked separately.
