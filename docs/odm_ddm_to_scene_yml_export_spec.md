# ODM + DDM To `.scene.yml` Export Spec

## Purpose

This document defines the exact first migration step for outdoor maps:

- input: `XX.odm` + `XX.ddm`
- output: `XX.scene.yml`

This is a transitional export step.

It is intentionally conservative:

- `XX.odm` remains on disk unchanged
- `XX.ddm` remains supported as a compatibility input for old maps
- the new `.scene.yml` becomes the authored scene supplement for successor-native outdoor maps

The goal is to move authored outdoor scene state and legacy outdoor semantics out of `DDM` and selected parts of `ODM`,
without replacing the current outdoor geometry container yet.

## Non-Goals

This document does not define:

- indoor `BLV` / `DLV` migration
- replacement of `ODM` geometry
- final long-term pretty scene schema
- editor UX

This is a precise migration/export spec for the first outdoor `.scene.yml` format.

## Required High-Level Model

The engine model after this migration must be:

1. load `XX.odm`
2. load `XX.scene.yml` if present
3. build initial authored runtime state from `ODM` geometry + `.scene.yml`
4. if a save exists, apply save overrides on top
5. if `.scene.yml` is absent, keep current legacy `DDM` fallback behavior

Precedence must be:

- save data
- `.scene.yml`
- legacy `DDM`
- legacy `ODM`

`ODM` is not rewritten by the exporter in this first phase.

Only duplicated authored fields in `ODM` are ignored when the same field is provided by `.scene.yml`.

## Required First Implementation Strategy

The first loader implementation must be conservative.

It must not redesign outdoor runtime state.

It must:

- continue using the current outdoor runtime path after load
- continue using the same effective runtime structs the engine already uses for
  outdoor authored state
- treat `.scene.yml` primarily as a different authored input source, not as a
  reason to invent a new outdoor runtime model in the same change

Concretely, the first implementation should behave like this:

1. load `ODM` into the normal `OutdoorMapData`
2. if `.scene.yml` is present:
   - apply duplicated `ODM` authored overrides from `.scene.yml` onto that
     loaded outdoor map representation
   - populate the same effective outdoor delta/runtime-authored state that
     legacy `DDM` currently provides
3. continue through the existing runtime assembly path

This means the first migrated load should be structurally close to:

- `ODM + scene.yml -> OutdoorMapData + MapDeltaData-like authored state`

not:

- `ODM + scene.yml -> brand new runtime scene architecture`

That larger refactor can happen later.

The goal of the first change is to replace the authored input seam, not to
rewrite outdoor runtime.

## Current Source Inventory

### `ODM` Outdoor Data Currently Loaded

OpenYAMM currently loads outdoor map data into [`game/outdoor/OutdoorMapData.h`](/home/pjasicek/github/OpenYAMM/game/outdoor/OutdoorMapData.h:96).

Important current `ODM` field groups:

- base map identity:
  - `version`
  - `name`
  - `fileName`
  - `description`
- outdoor environment basics:
  - `skyTexture`
  - `groundTilesetName`
  - `masterTile`
  - `tileSetLookupIndices`
- terrain:
  - `heightMap`
  - `tileMap`
  - `attributeMap`
  - `someOtherMap`
  - `normalMap`
  - `normals`
- outdoor mesh/model geometry:
  - `bmodels`
  - per-face `attributes`
  - per-face `cogNumber`
  - per-face `cogTriggeredNumber`
  - per-face `cogTrigger`
  - per-face UVs and texture information
- authored outdoor scene objects:
  - `entities`
  - `spawns`
- derived outdoor spatial lookup fields:
  - `decorationPidList`
  - `decorationMap`
- currently opaque/unclear outdoor fields:
  - `someOtherMap`

### `DDM` Outdoor Data Currently Loaded

OpenYAMM currently loads outdoor companion data into [`game/maps/MapDeltaData.h`](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h:130)
via [`game/maps/MapDeltaData.cpp`](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.cpp:658).

For outdoor maps, the parsed `DDM` currently contains:

- location header:
  - `respawnCount`
  - `lastRespawnDay`
  - `reputation`
  - `alertStatus`
  - `totalFacesCount`
  - `decorationCount`
  - `bmodelCount`
- reveal state:
  - `fullyRevealedCells`
  - `partiallyRevealedCells`
- mutable face/decor state:
  - `faceAttributes`
  - `decorationFlags`
- dynamic scene content:
  - `actors`
  - `spriteObjects`
  - `chests`
- local event variables:
  - `mapVars`
  - `decorVars`
- location time/environment-like data:
  - `lastVisitTime`
  - `skyTextureName`
  - `weatherFlags`
  - `fogWeakDistance`
  - `fogStrongDistance`
  - `reserved`

Outdoor `DDM` does not currently parse doors.

Important clarification from local references:

- `decorationPidList` is the legacy outdoor `IDList`
- `decorationMap` is the legacy outdoor `OMAP`, i.e. per-tile offsets into `IDList`
- `attributeMap` is the legacy outdoor `AMAP`
- `MapDeltaLocationTime.weatherFlags` is a legacy bitfield field, not a final semantic name
- `MapDeltaLocationTime.reserved` is not fully opaque in MM8
  - it matches the remaining `MapExtra` payload:
    - `Bits`
    - `Ceiling`
    - four periodic timers

## Export Scope

The exporter must produce a `.scene.yml` that contains:

- selected authored duplicate data from `ODM`
- authored initial scene state from `DDM`
- no save-specific or purely runtime-only state

This means the first `.scene.yml` is not a pure idealized redesign.
It is a structured outdoor authored-state export.

## Export Rules

## Fields Exported From `ODM`

The exporter must copy these `ODM` values into `.scene.yml`.

These fields are duplicated on purpose so the engine can stop taking them from `ODM` when `.scene.yml` is present.

### 1. Environment

Export from `ODM`:

- `skyTexture`
- `groundTilesetName`
- `masterTile`
- `tileSetLookupIndices`

The resulting `.scene.yml` fields are:

- `environment.sky_texture`
- `environment.ground_tileset_name`
- `environment.master_tile`
- `environment.tile_set_lookup_indices`

### 2. Terrain Attribute Semantics

Export from `ODM`:

- `attributeMap`

This field is the legacy outdoor `AMAP`.

Do not dump the full `128 x 128` byte grid as one huge inline YAML matrix.

Instead, export only non-zero terrain cells as sparse authored overrides:

- one entry per non-zero terrain attribute cell
- addressed by `x` and `y` tile coordinates
- storing the raw legacy byte value as `legacy_attributes`
- additionally expose only the confirmed named semantics:
  - `burn` for bit `0x01`
  - `water` for bit `0x02`

Do not assign names to higher `AMAP` bits in this first version.

The resulting `.scene.yml` field is:

- `terrain.attribute_overrides`

Tile coordinate mapping:

- `x = cellIndex % 128`
- `y = cellIndex / 128`

### 3. Interactive Outdoor BModel Face Metadata

Export from `ODM`:

- `OutdoorBModelFace.attributes`
- `OutdoorBModelFace.cogNumber`
- `OutdoorBModelFace.cogTriggeredNumber`
- `OutdoorBModelFace.cogTrigger`

Export only faces where at least one of these is non-zero.

The resulting `.scene.yml` field is:

- `bmodel_faces.interactive_faces`

Each exported entry must include:

- `bmodel_index`
- `face_index`
- `legacy_attributes`
- `cog_number`
- `cog_triggered_number`
- `cog_trigger`

### 4. Outdoor Entities

Export all `ODM` entities from `OutdoorMapData.entities`.

The resulting `.scene.yml` field is:

- `entities`

Each entity entry must include:

- `entity_index`
- `name`
- `decoration_list_id`
- `ai_attributes`
- `position.x`
- `position.y`
- `position.z`
- `facing`
- `event_id_primary`
- `event_id_secondary`
- `variable_primary`
- `variable_secondary`
- `special_trigger`

### 5. Outdoor Spawns

Export all `ODM` spawns from `OutdoorMapData.spawns`.

The resulting `.scene.yml` field is:

- `spawns`

Each spawn entry must include:

- `spawn_index`
- `position.x`
- `position.y`
- `position.z`
- `radius`
- `type_id`
- `index`
- `attributes`
- `group`

## Fields Exported From `DDM`

### 1. Initial Location State

Export from `DDM` location header:

- `respawnCount`
- `lastRespawnDay`
- `reputation`
- `alertStatus`

Do not export:

- `totalFacesCount`
- `decorationCount`
- `bmodelCount`

Those three are validation/derived-count style fields and do not belong in authored scene YAML.

The resulting `.scene.yml` field is:

- `initial_state.location`

### 2. Initial Face Attribute Overrides

Export from `DDM`:

- `faceAttributes`

This vector is currently flattened in the same order OpenYAMM uses in
[`parseOutdoorTail`](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.cpp:551):

1. iterate `outdoorMapData.bmodels` in order
2. for each bmodel, iterate `bmodel.faces` in order
3. append one face attribute entry per face

The exporter must reconstruct `(bmodel_index, face_index)` from that flat vector.

Export only entries whose value differs from the corresponding `ODM` face `attributes`.

The resulting `.scene.yml` field is:

- `initial_state.face_attribute_overrides`

Each exported entry must include:

- `bmodel_index`
- `face_index`
- `legacy_attributes`

### 3. Initial Decoration Flags

Export from `DDM`:

- `decorationFlags`

Outdoor `decorationFlags` are indexed to `ODM` entities by entity order.

Do not export them as a separate top-level array.

Instead, attach each flag directly onto the matching exported entity entry as:

- `initial_decoration_flag`

This keeps entity-related initial scene state with the entity itself.

### 4. Initial Actors

Export all `DDM` actors.

The resulting `.scene.yml` field is:

- `initial_state.actors`

Each actor entry must include:

- `actor_index`
- `name`
- `npc_id`
- `attributes`
- `hp`
- `hostility_type`
- `monster_info_id`
- `monster_id`
- `radius`
- `height`
- `move_speed`
- `position.x`
- `position.y`
- `position.z`
- `sprite_ids`
- `sector_id`
- `current_action_animation`
- `group`
- `ally`
- `unique_name_index`

### 5. Initial Sprite Objects

Export all `DDM` sprite objects.

The resulting `.scene.yml` field is:

- `initial_state.sprite_objects`

Each sprite object entry must include:

- `sprite_object_index`
- `sprite_id`
- `object_description_id`
- `position.x`
- `position.y`
- `position.z`
- `velocity.x`
- `velocity.y`
- `velocity.z`
- `yaw_angle`
- `sound_id`
- `attributes`
- `sector_id`
- `time_since_created`
- `temporary_lifetime`
- `glow_radius_multiplier`
- `spell_id`
- `spell_level`
- `spell_skill`
- `field54`
- `spell_caster_pid`
- `spell_target_pid`
- `lod_distance`
- `spell_caster_ability`
- `initial_position.x`
- `initial_position.y`
- `initial_position.z`
- `raw_containing_item_hex`

`raw_containing_item_hex` must be an uppercase hexadecimal string without separators.

### 6. Initial Chests

Export all `DDM` chests.

The resulting `.scene.yml` field is:

- `initial_state.chests`

Each chest entry must include:

- `chest_index`
- `chest_type_id`
- `flags`
- `raw_items_hex`
- `inventory_matrix`

`raw_items_hex` must be an uppercase hexadecimal string without separators.

### 7. Initial Event Variables

Export from `DDM`:

- `mapVars`
- `decorVars`

The resulting `.scene.yml` field is:

- `initial_state.variables.map`
- `initial_state.variables.decor`

Keep them as integer arrays.

Do not pack them into opaque blobs in this first version.

### 8. Initial Environment State From `DDM`

Export from `DDM` location time:

- `skyTextureName`
- `weatherFlags`
- `fogWeakDistance`
- `fogStrongDistance`
- `reserved`

Do not export:

- `lastVisitTime`

`lastVisitTime` is save/runtime state, not authored initial scene state.

Interpretation rules:

- `weatherFlags` must be treated as raw legacy `day_bits`
- `reserved` must be decoded in MM8 layout as:
  - bytes `0x00..0x03` -> `bits`
  - bytes `0x04..0x07` -> `ceiling`
  - bytes `0x08..0x17` -> four periodic timers

The four periodic timers must not be exported.

`skyTextureName` must override `ODM.skyTexture` when non-empty.

This means:

- `environment.sky_texture` comes from `DDM.locationTime.skyTextureName` if it is non-empty
- otherwise `environment.sky_texture` comes from `ODM.skyTexture`

`weatherFlags`, decoded MM8 `bits`, `fogWeakDistance`, `fogStrongDistance`, and decoded MM8 `ceiling`
must always be exported into:

- `environment.day_bits_raw`
- `environment.map_extra_bits_raw`
- `environment.flags.foggy`
- `environment.flags.raining`
- `environment.flags.snowing`
- `environment.flags.underwater`
- `environment.flags.no_terrain`
- `environment.flags.always_dark`
- `environment.flags.always_light`
- `environment.flags.always_foggy`
- `environment.flags.red_fog`
- `environment.fog.weak_distance`
- `environment.fog.strong_distance`
- `environment.ceiling`

Bit decoding rules:

- `environment.flags.foggy = (day_bits_raw & 0x1) != 0`
- `environment.flags.raining = (map_extra_bits_raw & 0x1) != 0`
- `environment.flags.snowing = (map_extra_bits_raw & 0x2) != 0`
- `environment.flags.underwater = (map_extra_bits_raw & 0x4) != 0`
- `environment.flags.no_terrain = (map_extra_bits_raw & 0x8) != 0`
- `environment.flags.always_dark = (map_extra_bits_raw & 0x10) != 0`
- `environment.flags.always_light = (map_extra_bits_raw & 0x20) != 0`
- `environment.flags.always_foggy = (map_extra_bits_raw & 0x40) != 0`
- `environment.flags.red_fog = (map_extra_bits_raw & 0x80) != 0`

## Fields Explicitly Omitted In This First Export

The exporter must not place these fields into `.scene.yml` in this first outdoor migration.

They remain in legacy sources for now.

### Omitted From `ODM`

- `heightMap`
- `tileMap`
- `bmodels` geometry
- per-face vertex indices
- per-face UV arrays
- per-face texture fields
- `someOtherMap`
- `normalMap`
- `normals`
- `decorationPidList`
- `decorationMap`
- `version`
- `name`
- `fileName`
- `description`

### Omitted From `DDM`

- `fullyRevealedCells`
- `partiallyRevealedCells`
- `lastVisitTime`
- `totalFacesCount`
- `decorationCount`
- `bmodelCount`
- the four periodic timers encoded inside `LocationTime.reserved`

Why these are omitted:

- `decorationPidList` and `decorationMap` are derived runtime spatial lookup structures
  - MMExtension identifies them as `IDList` and `IDOffsets`
  - they are regenerated from placed map sprites/decorations
- `normalMap` and `normals` are legacy helper/runtime data
- `someOtherMap` is still unresolved and must not be redesignated as authored truth
- reveal state and visit time are runtime/save state
- periodic timers are runtime state, not authored scene state

## `.scene.yml` File Naming

For `Out02.odm` and `Out02.ddm`, the exporter must generate:

- `Out02.scene.yml`

The file must sit next to the map files in the same logical map asset location.

## `.scene.yml` Format

The top-level YAML structure must be exactly:

```yaml
format_version: 1
kind: outdoor_scene
source:
  geometry_file: ""
  legacy_companion_file: ""
environment:
  sky_texture: ""
  ground_tileset_name: ""
  master_tile: 0
  tile_set_lookup_indices: [0, 0, 0, 0]
  day_bits_raw: 0
  map_extra_bits_raw: 0
  flags:
    foggy: false
    raining: false
    snowing: false
    underwater: false
    no_terrain: false
    always_dark: false
    always_light: false
    always_foggy: false
    red_fog: false
  fog:
    weak_distance: 0
    strong_distance: 0
  ceiling: 0
terrain:
  attribute_overrides: []
bmodel_faces:
  interactive_faces: []
entities: []
spawns: []
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  face_attribute_overrides: []
  actors: []
  sprite_objects: []
  chests: []
  variables:
    map: []
    decor: []
```

Top-level field meanings:

- `format_version`
  - fixed value `1`
- `kind`
  - fixed value `outdoor_scene`
- `source`
  - migration/debug metadata only
- `environment`
  - authored outdoor environment state and `ODM` environment duplication
- `terrain`
  - sparse terrain semantic overrides migrated out of `ODM.attributeMap`
- `bmodel_faces`
  - interactive authored face metadata migrated out of `ODM`
- `entities`
  - authored outdoor entities migrated out of `ODM`, including `DDM` decoration flags
- `spawns`
  - authored spawn anchors migrated out of `ODM`
- `initial_state`
  - initial mutable scene state that used to come from `DDM`

## Exact YAML Entry Shapes

### Terrain Attribute Override Entry

```yaml
- x: 0
  y: 0
  legacy_attributes: 0
  burn: false
  water: false
```

### Interactive BModel Face Entry

```yaml
- bmodel_index: 0
  face_index: 0
  legacy_attributes: 0
  cog_number: 0
  cog_triggered_number: 0
  cog_trigger: 0
```

### Entity Entry

```yaml
- entity_index: 0
  name: ""
  decoration_list_id: 0
  ai_attributes: 0
  position:
    x: 0
    y: 0
    z: 0
  facing: 0
  event_id_primary: 0
  event_id_secondary: 0
  variable_primary: 0
  variable_secondary: 0
  special_trigger: 0
  initial_decoration_flag: 0
```

### Spawn Entry

```yaml
- spawn_index: 0
  position:
    x: 0
    y: 0
    z: 0
  radius: 0
  type_id: 0
  index: 0
  attributes: 0
  group: 0
```

### Face Attribute Override Entry

```yaml
- bmodel_index: 0
  face_index: 0
  legacy_attributes: 0
```

### Actor Entry

```yaml
- actor_index: 0
  name: ""
  npc_id: 0
  attributes: 0
  hp: 0
  hostility_type: 0
  monster_info_id: 0
  monster_id: 0
  radius: 0
  height: 0
  move_speed: 0
  position:
    x: 0
    y: 0
    z: 0
  sprite_ids: [0, 0, 0, 0]
  sector_id: 0
  current_action_animation: 0
  group: 0
  ally: 0
  unique_name_index: 0
```

### Sprite Object Entry

```yaml
- sprite_object_index: 0
  sprite_id: 0
  object_description_id: 0
  position:
    x: 0
    y: 0
    z: 0
  velocity:
    x: 0
    y: 0
    z: 0
  yaw_angle: 0
  sound_id: 0
  attributes: 0
  sector_id: 0
  time_since_created: 0
  temporary_lifetime: 0
  glow_radius_multiplier: 0
  spell_id: 0
  spell_level: 0
  spell_skill: 0
  field54: 0
  spell_caster_pid: 0
  spell_target_pid: 0
  lod_distance: 0
  spell_caster_ability: 0
  initial_position:
    x: 0
    y: 0
    z: 0
  raw_containing_item_hex: ""
```

### Chest Entry

```yaml
- chest_index: 0
  chest_type_id: 0
  flags: 0
  raw_items_hex: ""
  inventory_matrix: []
```

## Example `.scene.yml`

This example shows shape and naming only.
It is not intended to mirror a full real map.

```yaml
format_version: 1
kind: outdoor_scene
source:
  geometry_file: "Out02.odm"
  legacy_companion_file: "Out02.ddm"
environment:
  sky_texture: "sky19"
  ground_tileset_name: "grastyl"
  master_tile: 6
  tile_set_lookup_indices: [90, 91, 92, 93]
  day_bits_raw: 1
  map_extra_bits_raw: 0
  flags:
    foggy: true
    raining: false
    snowing: false
    underwater: false
    no_terrain: false
    always_dark: false
    always_light: false
    always_foggy: false
    red_fog: false
  fog:
    weak_distance: 4096
    strong_distance: 8192
  ceiling: 4000
terrain:
  attribute_overrides:
    - x: 41
      y: 52
      legacy_attributes: 2
      burn: false
      water: true
    - x: 42
      y: 52
      legacy_attributes: 2
      burn: false
      water: true
bmodel_faces:
  interactive_faces:
    - bmodel_index: 12
      face_index: 4
      legacy_attributes: 1024
      cog_number: 301
      cog_triggered_number: 0
      cog_trigger: 1
entities:
  - entity_index: 0
    name: "torch01"
    decoration_list_id: 17
    ai_attributes: 0
    position:
      x: 13568
      y: 9472
      z: 256
    facing: 512
    event_id_primary: 405
    event_id_secondary: 0
    variable_primary: 0
    variable_secondary: 0
    special_trigger: 0
    initial_decoration_flag: 0
spawns:
  - spawn_index: 0
    position:
      x: 20480
      y: 12288
      z: 0
    radius: 1024
    type_id: 3
    index: 41
    attributes: 0
    group: 2
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  face_attribute_overrides:
    - bmodel_index: 12
      face_index: 4
      legacy_attributes: 1024
  actors:
    - actor_index: 0
      name: "Peasant"
      npc_id: 0
      attributes: 0
      hp: 20
      hostility_type: 0
      monster_info_id: 5
      monster_id: 5
      radius: 32
      height: 128
      move_speed: 32
      position:
        x: 20100
        y: 11800
        z: 0
      sprite_ids: [100, 101, 102, 103]
      sector_id: -1
      current_action_animation: 0
      group: 0
      ally: 0
      unique_name_index: 0
  sprite_objects:
    - sprite_object_index: 0
      sprite_id: 120
      object_description_id: 45
      position:
        x: 19968
        y: 11776
        z: 0
      velocity:
        x: 0
        y: 0
        z: 0
      yaw_angle: 0
      sound_id: 0
      attributes: 0
      sector_id: -1
      time_since_created: 0
      temporary_lifetime: 0
      glow_radius_multiplier: 0
      spell_id: 0
      spell_level: 0
      spell_skill: 0
      field54: 0
      spell_caster_pid: 0
      spell_target_pid: 0
      lod_distance: 0
      spell_caster_ability: 0
      initial_position:
        x: 19968
        y: 11776
        z: 0
      raw_containing_item_hex: ""
  chests:
    - chest_index: 0
      chest_type_id: 2
      flags: 0
      raw_items_hex: ""
      inventory_matrix: []
  variables:
    map: [0, 0, 0, 0, 0]
    decor: [0, 0, 0, 0, 0]
```

## Exporter Requirements

The builder session implementing this spec must follow these rules exactly.

### Required Behavior

- do not modify `ODM`
- require both `ODM` and `DDM` as exporter inputs
- produce exactly one `XX.scene.yml` output file
- preserve ordering of entities, spawns, actors, sprite objects, and chests
- preserve integer values exactly
- emit uppercase hexadecimal strings for opaque byte payloads
- emit sparse terrain attribute overrides only for non-zero cells
- expose only confirmed named `AMAP` semantics:
  - `burn` for bit `0x01`
  - `water` for bit `0x02`
- decode MM8 `LocationTime.reserved` into:
  - `map_extra_bits_raw`
  - `ceiling`
  - omit periodic timers from YAML
- emit sparse interactive face entries only when at least one exported face field is non-zero
- emit sparse face attribute overrides only when the `DDM` face attribute differs from the `ODM` face attribute

### Validation Rules

The exporter must validate:

- if `DDM.totalFacesCount` is non-zero, it must equal total flattened outdoor face count
- if `DDM.decorationCount` is non-zero, it must equal `ODM.entities.size()`
- if `DDM.bmodelCount` is non-zero, it must equal `ODM.bmodels.size()`
- `DDM.faceAttributes.size() == total flattened outdoor face count`
- `DDM.decorationFlags.size() == ODM.entities.size()`

If any of those checks fail, the exporter must fail loudly instead of producing partial output.

The first three count fields must be treated as advisory rather than authoritative because real MM8 outdoor
`DDM` files in the asset set commonly leave them as zero.

## Loader/Engine Follow-Up Requirements

The builder session that consumes this document must implement the outdoor load seam so that:

- `.scene.yml` is optional
- when `.scene.yml` exists, the engine prefers it over duplicated `DDM` / `ODM` authored fields
- when `.scene.yml` is absent, the current outdoor `DDM` + `ODM` path keeps working

Outdoor fields that must switch to `.scene.yml` ownership when present:

- environment:
  - `skyTexture`
  - `groundTilesetName`
  - `masterTile`
  - `tileSetLookupIndices`
- terrain semantic attributes:
  - sparse overrides from `terrain.attribute_overrides`
- bmodel face interaction metadata:
  - `attributes`
  - `cogNumber`
  - `cogTriggeredNumber`
  - `cogTrigger`
- `entities`
- `spawns`
- `DDM` initial location state
- `DDM` face attribute overrides
- `DDM` decoration flags
- `DDM` actors
- `DDM` sprite objects
- `DDM` chests
- `DDM` local event variables
- `DDM` environment weather/fog fields
- decoded MM8 `LocationTime` environment bits and ceiling

Outdoor fields that remain in `ODM` for now:

- geometry
- UVs
- terrain height/tile grids
- bmodel mesh shape
- texture names
- currently opaque helper arrays
- derived decoration lookup structures:
  - `decorationPidList`
  - `decorationMap`

## Why This First Version Is Intentionally Conservative

This migration is not the final pretty outdoor scene schema.

It is the minimum correct migration seam that:

- removes authored initial scene state from `DDM`
- starts moving authored outdoor semantics out of `ODM`
- keeps legacy outdoor geometry intact
- lets new maps stop depending on `DDM`
- allows later cleanup into richer per-domain YAML files without another binary-coupled redesign

After this step is working, future cleanup can split `Out02.scene.yml` into more specialized files such as:

- `Out02.environment.yml`
- `Out02.materials.yml`
- `Out02.encounters.yml`
- `Out02.interactions.yml`

Do not do that split in this first exporter.
First make `ODM + DDM -> .scene.yml` work exactly as specified above.
