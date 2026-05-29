# Outdoor `.scene.yml` Acceptance Test Spec

## Purpose

This document defines the acceptance criteria for declaring the first outdoor
`.scene.yml` migration correct.

It is intended for a later builder Codex session that will implement:

- outdoor `.scene.yml` loading
- outdoor `ODM + DDM -> .scene.yml` export
- headless equivalence tests

The key rule is:

The new path must prove that loading:

- `ODM + DDM`

produces the same effective authored runtime state as loading:

- `ODM + .scene.yml`

for all fields intentionally covered by the migration.

## Test Harness Target

Implementation should use the existing headless diagnostics infrastructure in:

- [HeadlessOutdoorDiagnostics.cpp](/home/pjasicek/github/OpenYAMM/game/outdoor/HeadlessOutdoorDiagnostics.cpp)

The acceptance suite should be added there rather than inventing a separate
test runner.

## Required Load Modes

The acceptance suite must support two outdoor load modes for the same map:

1. legacy mode
   - load `ODM`
   - load `DDM`
   - do not load `.scene.yml`

2. migrated mode
   - load `ODM`
   - load `.scene.yml`
   - do not load `DDM`

Optional third mode:

3. mixed precedence mode
   - load `ODM`
   - load `DDM`
   - load `.scene.yml`
   - verify `.scene.yml` wins for duplicated authored fields

The core acceptance comparison is between:

- legacy mode
- migrated mode

## Maps To Cover

The test suite must run on multiple real outdoor maps, not just one.

Minimum required outdoor maps:

- `Out01.odm`
- `Out02.odm`
- `Out05.odm`
- `Out13.odm`

Why:

- `Out01.odm`
  - baseline terrain and bmodel coverage
- `Out02.odm`
  - town/outdoor interaction density
- `Out05.odm`
  - different terrain/content mix
- `Out13.odm`
  - later-game outdoor map with different content profile

If any of these maps lack a valid legacy `DDM` companion or expose a known
content gap unrelated to migration, the suite may skip that map only with an
explicit reason in the failure output.

## Comparison Model

The test must compare normalized authored runtime state, not raw pointers,
caches, or GPU resources.

The implementation should build a normalized outdoor scene snapshot for both
load modes and compare those snapshots field by field.

The normalized snapshot should include only fields that are intended to be
equivalent after migration.

## Required Loader Strategy Assumption

The acceptance suite assumes the first migrated loader is conservative.

It should not require a new runtime scene architecture in order to pass.

The expected first implementation is:

- legacy mode:
  - `ODM + DDM` fill the current outdoor authored/runtime structs
- migrated mode:
  - `ODM + scene.yml` fill the same effective outdoor authored/runtime structs

After that point, both modes should proceed through the same downstream runtime
assembly and simulation path.

This is important because the migration target is authored-state equivalence,
not simultaneous runtime-architecture replacement.

## Fields That Must Match Exactly

### Environment

These must match exactly after normalization:

- sky texture
- ground tileset name
- master tile
- tile set lookup indices
- fog weak distance
- fog strong distance
- MM8 environment bits
- decoded MM8 flags:
  - foggy
  - raining
  - snowing
  - underwater
  - no terrain
  - always dark
  - always light
  - always foggy
  - red fog
- ceiling

### Terrain Semantic Overrides

For outdoor terrain attributes:

- all non-zero terrain attribute cells must match
- raw `legacy_attributes` values must match exactly
- named `burn` and `water` semantics must match exactly

This comparison must be done as sparse normalized entries:

- `(x, y, legacy_attributes, burn, water)`

### Interactive BModel Face Metadata

For each exported interactive outdoor bmodel face, these must match exactly:

- `bmodel_index`
- `face_index`
- `legacy_attributes`
- `cog_number`
- `cog_triggered_number`
- `cog_trigger`

This comparison must be sparse:

- only faces with relevant non-zero authored metadata are compared

### Outdoor Entities

For every outdoor entity:

- entity count must match
- entity order must match
- every exported field must match exactly:
  - `name`
  - `decoration_list_id`
  - `ai_attributes`
  - position
  - `facing`
  - `event_id_primary`
  - `event_id_secondary`
  - `variable_primary`
  - `variable_secondary`
  - `special_trigger`
  - `initial_decoration_flag`

### Outdoor Spawns

For every outdoor spawn:

- spawn count must match
- spawn order must match
- every exported field must match exactly:
  - position
  - `radius`
  - `type_id`
  - `index`
  - `attributes`
  - `group`

### Initial Location State

These must match exactly:

- `respawn_count`
- `last_respawn_day`
- `reputation`
- `alert_status`

### Initial Face Attribute Overrides

The normalized sparse override list must match exactly:

- `bmodel_index`
- `face_index`
- `legacy_attributes`

Only entries that actually differ from base `ODM` face attributes should be in
the normalized comparison.

### Initial Actors

For every actor:

- actor count must match
- actor order must match
- every exported field must match exactly:
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
  - position
  - `sprite_ids`
  - `sector_id`
  - `current_action_animation`
  - `group`
  - `ally`
  - `unique_name_index`

### Initial Sprite Objects

For every sprite object:

- sprite object count must match
- sprite object order must match
- every exported field must match exactly:
  - `sprite_id`
  - `object_description_id`
  - position
  - velocity
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
  - initial position
  - raw containing item bytes

### Initial Chests

For every chest:

- chest count must match
- chest order must match
- every exported field must match exactly:
  - `chest_type_id`
  - `flags`
  - raw item bytes
  - inventory matrix

### Initial Event Variables

These must match exactly:

- `mapVars`
- `decorVars`

## Fields That Must Match By Behavior

These should be checked with direct behavioral probes in addition to
snapshot-equality comparison.

### Water Semantics

For at least one known water tile per tested map:

- legacy mode and migrated mode must both report water
- outdoor movement/water support logic must behave identically

### Burning Semantics

If a tested map contains burning terrain:

- legacy mode and migrated mode must both report burning
- party/environment damage path must behave identically

If no required real map contains burning terrain, build one synthetic modified
headless scenario in memory from an existing outdoor map and compare:

- one chosen terrain cell with `legacy_attributes = 0x01`

### Face Interaction Semantics

For at least one interactive outdoor face with non-zero authored metadata:

- legacy mode and migrated mode must expose the same face interaction metadata
- click-trigger or step-trigger behavior must match if the map uses it

### Entity Decoration Flags

For maps with non-zero outdoor `decorationFlags`:

- legacy mode and migrated mode must produce the same per-entity initial flag
  values

## Fields Explicitly Excluded From Equality

These are not acceptance blockers for this migration:

- render caches
- collision caches
- GPU resources
- terrain normals regenerated at runtime
- `normalMap`
- `normals`
- `someOtherMap`
- `decorationPidList`
- `decorationMap`
- reveal state:
  - `fullyRevealedCells`
  - `partiallyRevealedCells`
- `lastVisitTime`
- MM8 periodic timer values embedded in `LocationTime.reserved`

These are either:

- derived runtime structures
- unresolved legacy helpers
- intentionally omitted runtime/save state

## Required Validation Failures

The headless acceptance suite must fail loudly if any of these differ between
legacy and migrated mode:

- counts differ
- ordering differs
- any scalar field differs
- any raw byte payload differs
- any decoded environment bit differs
- any sparse terrain semantic entry differs
- any sparse interactive face entry differs
- any sparse face attribute override differs

Failure output must identify:

- map file name
- comparison section
- entity/actor/chest/object index when applicable
- expected value
- actual value

## Precedence Test

The suite must include one precedence-specific test.

Scenario:

1. load `ODM + DDM`
2. also load a `.scene.yml` for the same map
3. inject or choose one field where `.scene.yml` intentionally differs from the
   legacy source
4. verify the runtime uses the `.scene.yml` value

Minimum required precedence checks:

- environment sky texture
- one terrain semantic override entry
- one entity field

This proves the intended ownership rule:

- save
- `.scene.yml`
- `DDM`
- `ODM`

## Round-Trip Acceptance

If an exporter exists, the suite must include:

1. export `ODM + DDM -> .scene.yml`
2. load `ODM + DDM`
3. load `ODM + exported .scene.yml`
4. compare normalized snapshots

This is the main acceptance gate for migration correctness.

## Optional Stronger Acceptance

These are recommended but not required for the first milestone:

- compare event-runtime initial state built from both modes
- compare actor-preview billboard materialization counts
- compare sprite-object runtime materialization counts
- compare chest runtime opening behavior on a known map/scripted case

## Final Pass Condition

The migration may be considered accepted for outdoor first-phase use only if:

1. all required maps pass legacy-vs-migrated equivalence
2. precedence tests pass
3. round-trip export/load tests pass
4. no excluded field is accidentally being used as the authored authority for
   migrated mode

## Implementation Guidance

The simplest correct implementation is:

1. build a normalized `OutdoorSceneSnapshot`
2. build it once from legacy load
3. build it once from migrated load
4. compare snapshots
5. add a few direct behavior probes for water/burn/interaction semantics

Do not rely only on visual or renderer-oriented checks.
This migration is about authored scene equivalence, not screenshots.
