# MM9 Import Toolchain

This document describes the local MM9 import/discovery tools used to convert extracted Might and Magic IX assets into
OpenYAMM world content. The tools live under `tools/mm9_import_discovery/`.

MM9 uses LithTech assets, not MM6-MM8 map formats. The import pipeline converts those source assets into OpenYAMM-native
development assets under `assets_dev/worlds/mm9/`, then mirrors usable outputs into `assets_editor_dev/worlds/mm9/`.

For LithTech lighting, shadows, compiled render data, and legacy `.ed` editor source findings, see
`docs/mm9/MM9_LITHTECH_LIGHTING_AND_ED_RESEARCH.md`.

## Inputs

Expected extracted source root:

```text
mm9/extracted/
  DATA/DATA/
  MODELS/MODELS/
  SKINS/SKINS/
  SOUNDS/SOUNDS/
  TEXTURES/TEXTURES/
  WORLDS/WORLDS/
```

Use `extract_rez.py` to produce this tree from the original MM9 `.REZ` archives.

`WORLDS/WORLDS/` may also contain legacy `.ed` editor source files for a subset of maps. These files should be
preserved as source artifacts when present, but DAT remains the runtime authority because the local extracted `.ed`
corpus is incomplete.

The importer uses a coordinate scale of `2.56` by default. That converts MM9/LithTech world and model units into the
OpenYAMM scale used by MM6-MM8 content. The shared constant is in `tools/mm9_import_discovery/mm9_units.py`.
MM9/LithTech data is Y-up; OpenYAMM map content is Z-up. Map exporters convert world coordinates as
`(x, y, z) -> (x, z, y)` before applying the scale. ABC model exporters preserve model-local axes and only scale local
distances; scene placement/rendering applies the same Y-up to Z-up transform when instancing models.

## Wrapper Scripts

Run wrappers from the repository root.

```bash
tools/mm9_import_discovery/regenerate_mm9_static_assets.sh
tools/mm9_import_discovery/regenerate_mm9_maps.sh
tools/mm9_import_discovery/regenerate_mm9_models.sh
tools/mm9_import_discovery/regenerate_mm9_all.sh
```

### Static Assets

```bash
tools/mm9_import_discovery/regenerate_mm9_static_assets.sh
```

Copies original-format assets that OpenYAMM can keep directly:

- `SOUNDS/SOUNDS` -> `sounds`
- `DATA/DATA/PCVOICES` -> `voices/pcvoices`
- `TEXTURES/TEXTURES` -> `textures`
- `SKINS/SKINS` -> `skins`

Useful options:

```bash
tools/mm9_import_discovery/regenerate_mm9_static_assets.sh --dry-run
tools/mm9_import_discovery/regenerate_mm9_static_assets.sh --extracted-root /path/to/extracted
```

### Maps

```bash
tools/mm9_import_discovery/regenerate_mm9_maps.sh
```

Default curated map set:

- `GUBERLAND.dat` -> `guberland.odm`
- `DARKPASSAGEWAY.dat` -> `darkpassageway.blv`

The wrapper also writes sidecars such as `.scene.yml`, `.mm9.yml`, `.material_aliases.yml`, `.raw_objects.yml`,
`.events.yml`, generated `events/<name>.lua`, and for outdoor imports `.model_assets.yml` plus map-local
`<name>.bitmaps/*.bmp` material aliases. MM9 event sidecars are generated only by the MM9 import pipeline and do not
change MM6-MM8 event loading.

Useful options:

```bash
tools/mm9_import_discovery/regenerate_mm9_maps.sh --all-odm
tools/mm9_import_discovery/regenerate_mm9_maps.sh --all-blv
tools/mm9_import_discovery/regenerate_mm9_maps.sh --clear-defaults --outdoor GUBERLANDCITY
tools/mm9_import_discovery/regenerate_mm9_maps.sh --clear-defaults --indoor DARKPASSAGEWAY
tools/mm9_import_discovery/regenerate_mm9_maps.sh --no-events
```

Indoor BLV generation needs the C++ compiler helper:

```bash
cmake --build build --target mm9_compile_indoor_source -j25
```

Pass `--no-compile` to stop after writing the indoor source GLB and metadata.

Generate or validate MM9 event sidecars directly:

```bash
python3 tools/mm9_import_discovery/generate_mm9_events.py
python3 tools/mm9_import_discovery/generate_mm9_events.py --validate-only
python3 tools/mm9_import_discovery/generate_mm9_events.py --only-map guberland
```

### Models

```bash
tools/mm9_import_discovery/regenerate_mm9_models.sh
```

This wrapper:

1. Copies shared `SKINS/*.dtx` files as runtime skin assets and writes PNG previews under `skins_preview/`.
2. Converts actor ABC models referenced by `ACTOR.txt` and `MONSTERS.txt`.
3. Converts non-actor model collections while preserving the original `MODELS/MODELS` subtree shape.
4. Generates `models/model_registry.yml`.
5. Rewrites map `model_asset` references through the registry.
6. Mirrors generated models/skins/skin previews/maps into `assets_editor_dev/worlds/mm9/`.

Generated model paths are source-shaped. For example,
`MODELS/MODELS/HIGHWAYMAN.abc` becomes `assets_dev/worlds/mm9/models/highwayman.glb` plus
`highwayman.model.yml`, and `MODELS/MODELS/PROPS/PLANTSANDTREES/TREE04.abc` becomes
`assets_dev/worlds/mm9/models/props/plantsandtrees/tree04.glb` plus `tree04.model.yml`. Actor/monster table skin
choices are recorded as `skin_bindings` in the model sidecar and registry; the pipeline does not create
`models/actors/*/variants/*` paths.

Generate MM9 actor billboard visual definitions and frame assets from the converted actor GLBs:

```bash
python3 tools/mm9_generate_actor_billboards.py --map guberland --write-yaml --placeholder-png \
  --report assets_dev/worlds/mm9/rendering/scripted_billboards/guberland_generation_report.yml
python3 tools/mm9_generate_actor_billboards.py --map guberland --dry-run --fail-on-unresolved
python3 tools/mm9_generate_actor_billboards.py --verify-output
```

The tool emits world-scoped `mm9_*` visual YAML files under
`assets_dev/worlds/mm9/rendering/scripted_billboards/`. The current placeholder PNG mode creates deterministic
nonblank frames for runtime integration. The same tool owns the Blender-backed render path for replacing those
placeholders with captured GLB animation frames.

Useful options:

```bash
tools/mm9_import_discovery/regenerate_mm9_models.sh --skip-skins
tools/mm9_import_discovery/regenerate_mm9_models.sh --skip-actors --skip-collections
tools/mm9_import_discovery/regenerate_mm9_models.sh --scale 2.56
```

### Everything

```bash
tools/mm9_import_discovery/regenerate_mm9_all.sh
```

This runs static assets, maps, then models. It defaults to the curated map set.

Useful options:

```bash
tools/mm9_import_discovery/regenerate_mm9_all.sh --map-mode curated
tools/mm9_import_discovery/regenerate_mm9_all.sh --map-mode all-odm
tools/mm9_import_discovery/regenerate_mm9_all.sh --map-mode all-blv
tools/mm9_import_discovery/regenerate_mm9_all.sh --no-editor-copy
```

## Individual Tools

### `extract_rez.py`

Extracts LithTech REZ v1 archives.

```bash
python3 tools/mm9_import_discovery/extract_rez.py mm9/game/WORLDS.REZ mm9/extracted/WORLDS
python3 tools/mm9_import_discovery/extract_rez.py --list mm9/game/WORLDS.REZ
```

### `sync_static_assets.py`

Copies static source-format MM9 assets into one or more world roots. Wrapped by
`regenerate_mm9_static_assets.sh`.

### `transcode_mm9_dat_to_odm.py`

Converts an MM9 DAT world into an OpenYAMM outdoor ODM shell and scene sidecars. It also extracts placed model
instances from DAT object properties.

Primary outputs:

- `<name>.odm`
- `<name>.scene.yml`
- `<name>.mm9.yml`
- `<name>.material_aliases.yml`
- `<name>.model_assets.yml`
- `<name>.raw_objects.yml`
- `<name>.bitmaps/*.bmp` material aliases

### `transcode_mm9_dat_to_blv.py`

Converts an MM9 DAT world into an indoor BLV prototype. It can emit one-room, spatial-grid, or leaf-grid sectors.

Primary outputs:

- `<name>.source.glb`
- `<name>.geometry.yml`
- `<name>.blv` when `--compile-tool` is supplied
- `<name>.scene.yml`
- `<name>.mm9.yml`
- `<name>.bsp.yml`
- `<name>.material_aliases.yml`
- `<name>.raw_objects.yml`

### `convert_abc_model.py`

Converts one LithTech ABC model to GLB plus `.model.yml` sidecars. The converter preserves LithTech ABC model-local
axes and applies the default `2.56` coordinate scale to mesh positions, bind translations, animation translations,
sockets, animation binding extents/origins, radius, and LOD distances. It preserves normals, rotations, UVs, face
winding, and source object instance scale values.

### `convert_skin_library.py`

Copies the shared MM9 `SKINS/SKINS/*.dtx` library to `assets_dev/worlds/mm9/skins` and writes decoded PNG previews to
`assets_dev/worlds/mm9/skins_preview`.

### `batch_convert_actor_models.py`

Builds actor model sidecars from `DATA/DATA/ACTOR.txt` and `DATA/DATA/MONSTERS.txt`, resolves skin bindings, calls
`convert_abc_model.py`, and stores the bindings in each `.model.yml`.

### `batch_convert_model_collection.py`

Converts non-actor ABC collections such as props, projectiles, pickups, spell models, weapons, and gibs. It can use
scene `source_skin` observations as defaults for models whose skins are otherwise ambiguous.

### `generate_model_registry.py`

Builds `assets_dev/worlds/mm9/models/model_registry.yml` from generated source-shaped `.model.yml` sidecars.

### `rewrite_scene_model_assets.py`

Rewrites `model_instances[].model_asset` in MM9 scene files through `model_registry.yml`. It also rebuilds
`.model_assets.yml` summaries from rewritten scenes when a matching scene exists.

### `test_dat_bsp_parser.py`

Focused Python tests for MM9 DAT BSP parsing/layout helpers and ABC coordinate scaling.

### `test_model_registry_layout.py`

Focused Python tests for source-shaped model registry resolution, actor skin binding preservation, and billboard
registry compatibility.

## Recommended Regeneration Flow

For the current curated import:

```bash
cmake --build build --target mm9_compile_indoor_source -j25
tools/mm9_import_discovery/regenerate_mm9_all.sh
python3 tools/mm9_import_discovery/test_dat_bsp_parser.py
python3 tools/mm9_import_discovery/test_model_registry_layout.py
```

For a full exploratory outdoor shell import of every DAT:

```bash
tools/mm9_import_discovery/regenerate_mm9_all.sh --map-mode all-odm
```

For a full exploratory indoor BLV prototype import of every DAT:

```bash
cmake --build build --target mm9_compile_indoor_source -j25
tools/mm9_import_discovery/regenerate_mm9_all.sh --map-mode all-blv
```

Do not treat full `all-odm` or `all-blv` output as a final world classification. MM9 DATs need explicit classification
and gameplay interpretation over time.
