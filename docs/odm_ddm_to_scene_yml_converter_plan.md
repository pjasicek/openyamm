# ODM + DDM To `.scene.yml` Converter Implementation Plan

## Purpose

This document defines the implementation plan for the first outdoor converter:

- input: `XX.odm` + `XX.ddm`
- output: `XX.scene.yml`

This plan is derived from:

- [odm_ddm_to_scene_yml_export_spec.md](/home/pjasicek/github/OpenYAMM/docs/odm_ddm_to_scene_yml_export_spec.md)
- [odm_scene_yml_acceptance_test_spec.md](/home/pjasicek/github/OpenYAMM/docs/odm_scene_yml_acceptance_test_spec.md)

It is intended for a later builder Codex session that will implement the actual
converter.

## Scope

The converter in this phase must:

- read one outdoor `ODM`
- read the matching outdoor `DDM`
- export one `.scene.yml`
- preserve every field required by the export spec
- leave the input `ODM` unchanged

The converter in this phase must not:

- rewrite `ODM`
- generate save-state data
- migrate indoor `BLV` / `DLV`
- invent new long-term schema beyond the current export spec

## Recommended Implementation Choice

Implement the converter as a Python tool under `tools/`.

Recommended path:

- `tools/export_outdoor_scene_yml.py`

Reasons:

- the repository already contains small binary-to-YAML exporter scripts in
  `tools/`
- the first migration step is a one-way export, not a runtime loader
- Python is fast enough for this scale of binary parsing
- a fixed-schema writer can emit stable YAML without introducing a new runtime
  dependency for the tool

Do not add a Python YAML dependency just for this tool.

Use:

- `struct`
- `pathlib`
- `argparse`
- `json` for safe quoted scalars in YAML output

Write YAML manually in the same style as existing exporters such as
[export_sprite_frame_table.py](/home/pjasicek/github/OpenYAMM/tools/export_sprite_frame_table.py).

## Source Of Truth

The builder session must treat the export spec as authoritative.

If there is any ambiguity during implementation:

1. follow `odm_ddm_to_scene_yml_export_spec.md`
2. follow current OpenYAMM struct layouts and parsing behavior
3. preserve raw legacy values rather than renaming uncertain semantics

Do not redesign the schema during implementation.

## Required Builder Approach

The later builder session should treat this migration as a format-seam change
first, not as a runtime redesign.

That means:

- the exporter produces `.scene.yml`
- the loader reads `.scene.yml`
- the loader then fills the same effective outdoor authored/runtime structs the
  engine already uses today
- the existing downstream outdoor runtime path stays in place for the first
  implementation

In practice, the intended first target is:

- `ODM + scene.yml` populate the same effective data that `ODM + DDM` currently
  provides

This is the lowest-risk path and is the one the acceptance test is designed to
validate.

## Output Contract

For a pair:

- `Out01.odm`
- `Out01.ddm`

the tool must emit:

- `Out01.scene.yml`

The file must contain only the sections defined by the export spec.

The top-level section order must be stable:

1. `environment`
2. `terrain`
3. `bmodel_faces`
4. `entities`
5. `spawns`
6. `initial_state`

Within each section, field order must also be stable.

This is required for:

- diff readability
- deterministic exports
- acceptance testing

## CLI Shape

The first implementation should support:

```text
tools/export_outdoor_scene_yml.py --odm path/to/Out01.odm --ddm path/to/Out01.ddm --output path/to/Out01.scene.yml
```

Recommended additional modes:

```text
tools/export_outdoor_scene_yml.py --map-base path/to/Out01
tools/export_outdoor_scene_yml.py --input-dir path/to/maps --map Out01
```

Required behavior:

- fail clearly if `ODM` is missing
- fail clearly if `DDM` is missing
- fail clearly if the parsed map is not outdoor
- fail clearly on malformed binary input
- overwrite the output file only after a successful full export

Use atomic write behavior:

- write to `*.tmp`
- rename to final path only on success

## File Layout

The implementation should remain in one Python file unless it becomes clearly
unwieldy.

If splitting is needed, use:

- `tools/export_outdoor_scene_yml.py`
- `tools/openyamm_binary.py`
- `tools/openyamm_scene_yml.py`

The first builder session should prefer a single-file implementation.

## Implementation Phases

### Phase 1. Binary Reader Helpers

Implement low-level helpers:

- `read_u8`
- `read_i8`
- `read_u16`
- `read_i16`
- `read_u32`
- `read_i32`
- `read_fixed_string`
- `read_bytes`
- `expect_size_at_least`

Requirements:

- little-endian only
- bounds checked
- every read failure must raise a descriptive exception
- string decoding must match current exporter style:
  - strip trailing `\0`
  - decode with `latin1`
  - preserve original casing unless the source logic explicitly lowercases

### Phase 2. ODM Parsing

Implement parsing of the outdoor fields needed by the export spec only.

Do not attempt to parse every theoretical `ODM` field if it is not required for
export.

The parser must produce an in-memory dict-like model with these groups:

- `environment`
- `terrain_attribute_overrides`
- `interactive_faces`
- `entities`
- `spawns`

#### ODM Fields Required

From current OpenYAMM outdoor parsing, extract:

- `skyTexture`
- `groundTilesetName`
- `masterTile`
- `tileSetLookupIndices`
- `attributeMap`
- `bmodels[*].faces[*].attributes`
- `bmodels[*].faces[*].cogNumber`
- `bmodels[*].faces[*].cogTriggeredNumber`
- `bmodels[*].faces[*].cogTrigger`
- `entities`
- `spawns`

Do not export:

- `heightMap`
- `tileMap`
- `someOtherMap`
- `normalMap`
- `normals`
- `decorationPidList`
- `decorationMap`
- geometry vertices and UV arrays

#### Terrain Attribute Export

For `attributeMap`:

- iterate `128 * 128` cells
- export only non-zero cells
- compute:
  - `x = index % 128`
  - `y = index // 128`
  - `legacy_attributes = raw_byte`
  - `burn = (raw_byte & 0x01) != 0`
  - `water = (raw_byte & 0x02) != 0`

Do not infer names for any higher bits.

#### Interactive Face Export

For every bmodel face:

- export only if at least one of:
  - `attributes`
  - `cogNumber`
  - `cogTriggeredNumber`
  - `cogTrigger`
  is non-zero

Each entry must include:

- `bmodel_index`
- `face_index`
- `legacy_attributes`
- `cog_number`
- `cog_triggered_number`
- `cog_trigger`

#### Entity Export

Export all entities in original order.

Each entry must contain:

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

#### Spawn Export

Export all spawns in original order.

Each entry must contain:

- `spawn_index`
- `position.x`
- `position.y`
- `position.z`
- `radius`
- `type_id`
- `index`
- `attributes`
- `group`

### Phase 3. DDM Parsing

Implement parsing of the outdoor fields needed by the export spec only.

The parser must produce these groups:

- `location`
- `environment_overrides`
- `face_attribute_overrides`
- `entity_initial_flags`
- `actors`
- `sprite_objects`
- `chests`
- `variables`

#### DDM Fields Required

Extract:

- location header
  - `respawnCount`
  - `lastRespawnDay`
  - `reputation`
  - `alertStatus`
- `faceAttributes`
- `decorationFlags`
- `actors`
- `spriteObjects`
- `chests`
- `mapVars`
- `decorVars`
- location time
  - `skyTextureName`
  - `weatherFlags`
  - `fogWeakDistance`
  - `fogStrongDistance`
  - `reserved`

Do not export:

- `fullyRevealedCells`
- `partiallyRevealedCells`
- `lastVisitTime`
- periodic timers from `MapExtra`
- `totalFacesCount`
- `decorationCount`
- `bmodelCount`

#### MM8 `MapExtra` Decoding

Interpret the `location time` payload as:

- `sky_texture_name`
- `day_bits_raw`
- `fog.weak_distance`
- `fog.strong_distance`
- `map_extra_bits_raw`
- `ceiling`

Decoded booleans to export:

- `foggy`
- `raining`
- `snowing`
- `underwater`
- `no_terrain`
- `always_dark`
- `always_light`
- `always_foggy`
- `red_fog`

Rules:

- `foggy = (day_bits_raw & 0x01) != 0`
- all other named booleans come from `map_extra_bits_raw`

Preserve the raw integers even when decoded booleans are also emitted.

#### Face Attribute Overrides

`DDM.faceAttributes` is a flattened override array.

The exporter must:

1. iterate `ODM` bmodels in order
2. iterate each bmodel face in order
3. map flattened `DDM.faceAttributes` to `(bmodel_index, face_index)`
4. compare each override value against the base `ODM` face `attributes`
5. export only entries where the values differ

Each exported entry must include:

- `bmodel_index`
- `face_index`
- `legacy_attributes`

This rule is important.

Do not export redundant entries that merely restate the base `ODM` value.

#### Initial Decoration Flags

`DDM.decorationFlags` is parallel to `ODM.entities`.

The exporter must:

- require matching counts
- attach each flag to the corresponding exported entity as
  `initial_decoration_flag`

If counts differ:

- fail with a descriptive error

#### Actor Export

Export all initial actors in original order.

Preserve all fields required by the acceptance spec, including:

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
- `position`
- `sprite_ids`
- `sector_id`
- `current_action_animation`
- `group`
- `ally`
- `unique_name_index`

Preserve raw numeric values even for fields whose semantics are only partly
understood.

#### Sprite Object Export

Export all initial sprite objects in original order.

Preserve all fields required by the acceptance spec, including:

- `sprite_id`
- `object_description_id`
- `position`
- `velocity`
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
- `initial_position`
- raw containing item bytes

Represent raw containing item bytes as a lowercase hexadecimal string.

#### Chest Export

Export all initial chests in original order.

Preserve the exact schema required by the export spec.

If the spec and current implementation diverge during the builder session,
update the plan only if the export spec is also updated intentionally.

#### Variable Export

Export:

- `map_vars`
- `decor_vars`

as ordered integer sequences without trimming trailing zeros.

This is important for exact comparison behavior.

### Phase 4. Merge ODM + DDM Into Scene Model

Create one normalized in-memory scene dict with this exact shape:

- `environment`
- `terrain`
- `bmodel_faces`
- `entities`
- `spawns`
- `initial_state`

Rules:

- `environment` starts from `ODM` values
- `DDM` contributes initial environment-time fields
- entities start from `ODM.entities`
- `initial_decoration_flag` is then attached from `DDM.decorationFlags`
- `initial_state` contains only authored initial state, not save-only fields

Do not perform any clever deduplication beyond what the export spec requires.

### Phase 5. Deterministic YAML Writer

Implement a manual YAML emitter.

Requirements:

- stable key order
- stable sequence order
- blank-line discipline consistent across runs
- JSON quoting for strings when needed
- booleans written as `true` / `false`
- no anchors
- no flow-style maps
- flow-style sequences allowed only where the export spec already uses them and
  they remain readable

Recommended helpers:

- `quote_yaml_string`
- `append_key_value`
- `append_position_block`
- `append_sequence_of_maps`
- `append_hex_scalar`

Formatting rules:

- always end file with newline
- use 2-space indentation
- do not emit empty sections unless the spec requires them
- emit empty sequences as `[]` only where needed to preserve explicit structure

### Phase 6. Validation

The tool must validate before writing output.

Required validations:

- if non-zero, `DDM.totalFacesCount` matches flattened `ODM` face count
- if non-zero, `DDM.decorationCount` matches `ODM.entities` count
- if non-zero, `DDM.bmodelCount` matches `ODM.bmodels` count
- `ODM` face count matches flattened `DDM.faceAttributes` length
- `ODM.entities` count matches `DDM.decorationFlags` count
- every sparse `(x, y)` terrain coordinate is within `0..127`
- every exported `(bmodel_index, face_index)` exists in `ODM`
- all parallel vectors required by actor/sprite/chest parsing are consistent

Validation failures must:

- stop the export
- identify the map name or input path
- state the mismatched counts or offending index

### Phase 7. Initial Verification

The builder session implementing the tool must verify it on at least one real
outdoor map by inspecting the produced YAML manually.

Minimum manual verification checklist:

- environment block is populated
- sparse terrain overrides are not exploded into a full matrix
- interactive faces appear only where expected
- entities have `initial_decoration_flag`
- face override list is sparse and non-redundant
- raw containing item bytes are preserved for sprite objects

## Suggested Internal Data Model

The script should use plain Python dictionaries and lists, not custom classes.

Recommended shapes:

```python
scene = {
    "environment": {...},
    "terrain": {
        "attribute_overrides": [...],
    },
    "bmodel_faces": {
        "interactive_faces": [...],
    },
    "entities": [...],
    "spawns": [...],
    "initial_state": {
        "location": {...},
        "face_attribute_overrides": [...],
        "actors": [...],
        "sprite_objects": [...],
        "chests": [...],
        "variables": {...},
    },
}
```

This keeps the first implementation simple and aligned with the fixed export
schema.

## Required Mapping Functions

The implementation should have explicit mapping functions with narrow
responsibility:

- `parse_odm(path) -> dict`
- `parse_ddm(path, odm_model) -> dict`
- `build_scene_model(odm_model, ddm_model) -> dict`
- `write_scene_yaml(scene_model, output_path) -> None`
- `validate_scene_model(scene_model, odm_model, ddm_model) -> None`

Recommended lower-level helpers:

- `collect_terrain_attribute_overrides(attribute_map)`
- `collect_interactive_faces(bmodels)`
- `collect_face_attribute_overrides(odm_bmodels, ddm_face_attributes)`
- `attach_entity_initial_flags(entities, decoration_flags)`
- `decode_map_extra(location_time_reserved)`

## Error Handling

All tool failures must be actionable.

Bad:

- `failed to parse file`

Good:

- `Out01.ddm: expected 317 face attribute overrides, got 316`
- `Out13.odm: entity count 142 does not match decoration flag count 141`
- `Out02.ddm: truncated sprite object record at index 58`

## Acceptance Alignment

The builder session must treat the converter as only half of the migration.

The implementation is not done when the script runs once.

It is done when:

1. the converter emits `.scene.yml`
2. loader support exists for `ODM + .scene.yml`
3. the acceptance comparison from
   [odm_scene_yml_acceptance_test_spec.md](/home/pjasicek/github/OpenYAMM/docs/odm_scene_yml_acceptance_test_spec.md)
   passes on the required maps

The converter implementation should therefore make deterministic output a hard
requirement, because test fixtures and diff review depend on it.

## Builder Session Execution Order

A later builder session should implement in this order:

1. add `tools/export_outdoor_scene_yml.py`
2. implement binary readers
3. implement `ODM` parsing for required exported fields
4. implement `DDM` parsing for required exported fields
5. implement scene-model merge
6. implement deterministic YAML writing
7. export one real map and inspect output
8. add loader support for `.scene.yml`
9. add headless equivalence tests
10. run acceptance suite on required maps

Do not start with loader changes.

The exporter is the cleanest place to lock the schema first.

## Explicit Non-Goals For First Implementation

Do not do any of the following in the first converter implementation:

- rename uncertain `AMAP` bits beyond `burn` and `water`
- export `decorationPidList`
- export `decorationMap`
- export normals
- export `someOtherMap`
- compress or prettify data by inventing custom aliases
- merge indoor and outdoor conversion into one tool

## Done Criteria

The converter implementation is complete when:

- it deterministically exports `.scene.yml` for real outdoor maps
- it matches the export spec exactly
- it preserves all raw fields required by the acceptance spec
- it emits actionable validation errors
- it is ready to be paired with the loader and acceptance tests

Until the acceptance suite passes, the converter is implemented but the
migration is not yet proven complete.
