# MM9 Model Asset Structure

This document defines the implemented MM9 LithTech model conversion layout. The goal is to stay close to the original
`MODELS/MODELS` and `SKINS/SKINS` source organization while giving OpenYAMM deterministic GLB, import provenance,
preview, and registry assets.

There are two deliberately separate consumers. The bulk actor/scene conversion below preserves DTX paths as legacy
binding metadata for the not-yet-migrated actor renderer. The shared model/effect runtime uses GLB/glTF plus PNG and
has no ABC or DTX runtime dependency. Do not use the bulk actor metadata to reintroduce DTX loading into that runtime.

## Core Layout

Converted assets live under `assets_dev/worlds/mm9/` and are mirrored to `assets_editor_dev/worlds/mm9/`:

```text
models/
  model_registry.yml
  <root-model>.glb
  <root-model>.model.yml
  props/plantsandtrees/tree04.glb
  props/plantsandtrees/tree04.model.yml
  weapons/dagger.glb
  weapons/dagger.model.yml
  import/

skins/
  <runtime copied DTX files>

skins_preview/
  <decoded PNG previews for tools/GLB preview materials>
```

The pipeline does not generate `models/actors/*/variants/*` or `*.model_set.yml`. Actor variants are metadata
bindings on the source-shaped model sidecar and registry, not separate geometry directories.

## Path Rule

The canonical output path is the lowercase source path below `MODELS/MODELS`, with `.abc` replaced by `.glb` and
`.model.yml`:

```text
MODELS/MODELS/HIGHWAYMAN.abc
  -> models/highwayman.glb
  -> models/highwayman.model.yml

MODELS/MODELS/PROPS/PLANTSANDTREES/TREE04.abc
  -> models/props/plantsandtrees/tree04.glb
  -> models/props/plantsandtrees/tree04.model.yml
```

Root-level ABC files are converted too. If a root actor model was already generated from `ACTOR.txt` or
`MONSTERS.txt`, the collection pass preserves that actor sidecar instead of overwriting its bindings.

## Bulk actor and scene textures

The existing bulk actor/scene pipeline still records DTX as its legacy runtime texture source:

```text
SKINS/SKINS/HIGHWAYMAN1.dtx
  -> skins/highwayman1.dtx
  -> skins_preview/highwayman1.png
```

The GLB points at the PNG preview so general tools can display the model. The `.model.yml` material entry records both
the runtime DTX and the preview PNG:

```yaml
materials:
  - index: 0
    texture: skins_preview/highwayman1.png
    runtime_texture: skins/highwayman1.dtx
    preview_texture: skins_preview/highwayman1.png
    source: mm9/extracted/SKINS/SKINS/HIGHWAYMAN1.dtx
```

This statement applies only to the existing actor/scene pipeline. Its current renderer may consume
`runtime_texture`/DTX metadata where MM9 material behavior matters, while PNG previews are caches.

## Migrated shared model and effect textures

Models used by `engine/models`, rigid props, and `game/fx` use PNG at runtime. DTX is an offline source only. The
effect importer writes exact RGBA PNGs under `assets_dev/engine/effects/mm9/textures/`, retains every decoded source
mip plus source hashes and flags under `assets_dev/engine/effects/mm9/import/textures/`, and records the generated-mip
runtime policy explicitly. Effect-local audio and animation-path GLBs live in the same engine-owned package. Migrated
GLB files either embed PNG or reference package-relative PNG paths.

This is deliberately separate from the world-owned bulk actor/scene conversion described above. The `mm9:` ids retain
provenance, while the promoted effects are base content and can be spawned in MM6, MM7, MM8, MM9, or custom worlds.

The complete subset, coordinate policy, regeneration commands, and known fidelity limits are recorded in
`re_mm8/mm9_vfx/IMPLEMENTATION_CONTRACT.md`.

## Actor Skin Bindings

MM9 actor and monster table rows choose skins for a model. Those choices are represented as `skin_bindings` in the
model sidecar:

```yaml
roles:
  - actor_model
source_model: models/highwayman.abc
source_tables:
  - ACTOR
  - MONSTERS
skin_bindings:
  - id: highwayman_highwayman1_highwaymanss_highwaymandagger
    source_skins:
      - skins/highwayman1.dtx
      - skins/highwaymanss.dtx
      - skins/highwaymandagger.dtx
    actor_rows:
      - table: MONSTERS
        row: 1
        number: "1"
        monster_name: Bandit
        type_picture: Bandit
        base_name: Highwayman
```

Scenes still preserve the original `source_model`, `source_skin`, and `source_class`. Rewriting adds:

- `model_asset` when geometry resolves.
- `model_skin_binding` when the table/skin binding resolves.
- `model_resolution` when binding or geometry resolution is ambiguous or missing.

If geometry resolves but skin choice does not, the scene keeps the `model_asset` and records `skin_ambiguous` rather
than inventing a skin.

## Registry

`models/model_registry.yml` is generated from `*.model.yml` sidecars using schema
`openyamm.mm9.model_registry.v2`. It records:

- source ABC path to source-shaped GLB path.
- runtime DTX skin paths used by the model.
- actor `skin_bindings` and actor table row provenance.
- lookup tables for source model, source model plus skins, and actor table rows.

The editor and scene tools accept this v2 registry directly.

## Regeneration

Use:

```bash
tools/mm9_import_discovery/regenerate_mm9_models.sh
```

The default run cleans and regenerates `models/`, `skins/`, `skins_preview/`, rewrites map scene model references, and
mirrors the same tree to `assets_editor_dev/worlds/mm9/`.

Useful focused reruns:

```bash
tools/mm9_import_discovery/regenerate_mm9_models.sh --no-clean --skip-skins --skip-actors
python3 tools/mm9_import_discovery/test_model_registry_layout.py
```

## Validation Expectations

The current implemented output has:

- `844` source-shaped GLB files and `844` matching `.model.yml` files.
- `895` copied DTX runtime skins and `895` PNG skin previews.
- no generated `models/actors/*`, `variants/*`, or `*.model_set.yml`.
- zero broken generated `model_asset` references.
- remaining unresolved scene model references only where the referenced source ABC is absent from the extracted model
  tree; these stay visible as `model_resolution.status: missing`.
