# Editor Preview Materials

The editor viewport now has built-in preview materials for outdoor terrain and bmodel faces.

## Clay Preview

- Built-in name: `Builtin/TerrainClay`
- Used for terrain sculpting by default.
- Also used when the viewport preview mode is switched to `Clay`.
- Terrain clay is texture-free and lit from per-triangle normals so sculpted slopes, ridges, and valleys stay readable.

Clay tuning lives in:
- [EditorOutdoorViewport.h](/home/pjasicek/github/OpenYAMM/editor/viewport/EditorOutdoorViewport.h)
  - `ClayPreviewSettings`
- [fs_editor_preview_material.sc](/home/pjasicek/github/OpenYAMM/game/shaders/fs_editor_preview_material.sc)

Main clay controls:
- `baseColor`
- `slopeAccentStrength`
- `shadowStrength`
- `lightWrap`

## Grid Preview

- Built-in name: `Builtin/ObjectGrid`
- Used for bmodel faces that have no assigned texture/material reference.
- Also used when the viewport preview mode is switched to `Grid`.

The grid is procedural in the shader and uses CPU-generated planar object-local coordinates per face, so it stays attached to the mesh instead of coming from a bitmap asset.

Grid tuning lives in:
- [EditorOutdoorViewport.h](/home/pjasicek/github/OpenYAMM/editor/viewport/EditorOutdoorViewport.h)
  - `GridPreviewSettings`
- [fs_editor_preview_material.sc](/home/pjasicek/github/OpenYAMM/game/shaders/fs_editor_preview_material.sc)

Main grid controls:
- `baseColorA`
- `baseColorB`
- `minorLineColor`
- `majorLineColor`
- `cellSize`
- `majorInterval`
- `lineThickness`
- `majorLineThickness`

## Missing Assets

- Built-in name: `Builtin/ErrorMissingAsset`
- Separate from normal preview fallback.
- Used when a face references a texture/material name but the asset cannot be resolved or loaded.
- Terrain tiles with broken bitmap references also render through this path.

This currently uses a loud procedural magenta/black-style grid variant so missing assets stay visually distinct from normal untextured preview.

## Fallback Rules

- Terrain while sculpting:
  - always `Builtin/TerrainClay`
- Terrain outside sculpt mode:
  - `Textured` preview mode: textured terrain if the tile atlas is valid, otherwise clay
  - `Clay` preview mode: clay
  - `Grid` preview mode: clay
- Terrain tile with broken/missing assigned bitmap:
  - `Builtin/ErrorMissingAsset`
- Bmodel face with valid assigned texture:
  - textured in `Textured` mode
  - clay/grid in forced preview modes
- Bmodel face with no assigned texture name:
  - `Builtin/ObjectGrid`
- Bmodel face with missing/broken assigned texture:
  - `Builtin/ErrorMissingAsset`

## Switching Modes

Viewport preview modes are exposed in:
- the top `View` toolbar
- the viewport overlay

Modes:
- `Textured`
- `Clay`
- `Grid`

There is also a `Selected Only` toggle:
- when enabled, `Clay` or `Grid` preview applies only to the selected bmodel
- terrain sculpt preview still forces clay regardless

Editor state for the mode is persisted in:
- `.openyamm-editor.ini`
