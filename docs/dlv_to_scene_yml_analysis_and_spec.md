# DLV To `.scene.yml` Analysis And Proposed Indoor Schema

## Purpose

This document prepares the indoor `DLV -> .scene.yml` migration work before
implementation.

Goals:

- inventory what OpenYAMM currently reads from `DLV`
- identify which `DLV` fields are shared with outdoor `DDM`
- identify which fields are indoor-only
- distinguish confirmed MM8 semantics from still-raw legacy payload
- propose an indoor `.scene.yml` format that stays aligned with the outdoor
  `.scene.yml` direction without forcing fake indoor/outdoor symmetry

This is an analysis/spec document, not an implementation.

## Short Recommendation

Use the same `.scene.yml` family and the same broad top-level conventions as
outdoor:

- `format_version`
- `kind`
- `source`
- `environment`
- `initial_state`

Keep the truly indoor-only state inside indoor-specific `initial_state`
sections:

- `visible_outlines`
- indoor flat `face_attribute_overrides`
- `doors`

Do not force the outdoor geometry-oriented sections directly onto indoor.
Outdoor has terrain and bmodels; indoor has sectors, faces, portals, outlines,
and doors.

## Current OpenYAMM `DLV` Inventory

OpenYAMM currently parses indoor delta data through
[MapDeltaData.h](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.h) and
[MapDeltaData.cpp](/home/pjasicek/github/OpenYAMM/game/maps/MapDeltaData.cpp).

The current indoor path is:

- `MapDeltaDataLoader::loadIndoorFromBytes`
- `readLocationHeader`
- `parseIndoorTail`

### Fields Currently Read For Indoor

From the location header:

- `respawnCount`
- `lastRespawnDay`
- `reputation`
- `alertStatus`
- `totalFacesCount`
- `decorationCount`
- `bmodelCount`

From the indoor tail:

- `visibleOutlines`
- `faceAttributes`
- `decorationFlags`
- `actors`
- `spriteObjects`
- `chests`
- `doors`
- `doorsData`
- `eventVariables.mapVars`
- `eventVariables.decorVars`
- `locationTime`

## `DLV` vs `DDM`: Shared And Indoor-Only Parts

The key structural fact is that OpenYAMM already uses one shared abstraction
for both companion formats:

- `MapDeltaData`

That means indoor and outdoor companion formats are already largely the same
logical family.

### Shared Between `DDM` And `DLV`

These field groups exist in both outdoor `DDM` and indoor `DLV`:

- location header:
  - `respawnCount`
  - `lastRespawnDay`
  - `reputation`
  - `alertStatus`
  - validation counts
- mutable face state:
  - `faceAttributes`
- mutable decoration state:
  - `decorationFlags`
- dynamic actors:
  - `actors`
- dynamic sprite objects:
  - `spriteObjects`
- chests:
  - `chests`
- persistent local variables:
  - `mapVars`
  - `decorVars`
- location time / map-extra payload:
  - `lastVisitTime`
  - `skyTextureName`
  - `weatherFlags`
  - `fogWeakDistance`
  - `fogStrongDistance`
  - trailing `reserved` / MM8 `MapExtra` bytes

### Outdoor-Only In The Current Companion Layer

- `fullyRevealedCells`
- `partiallyRevealedCells`

### Indoor-Only In The Current Companion Layer

- `visibleOutlines`
- `doors`
- `doorsData`

## Confidence / Coverage Assessment

This is the important part for not missing fields.

### 1. Location Header

Status:

- parsing coverage is complete for the fields OpenYAMM currently models
- semantics are reasonably clear

Notes:

- `totalFacesCount`
- `decorationCount`
- `bmodelCount`

should remain validation fields, not authored scene truth.

### 2. Visible Outlines

Status:

- structurally accounted for
- semantics are sufficiently clear to preserve

Evidence:

- OpenYAMM reads `875` bytes for indoor visible outlines
- OpenEnroth snapshot data also stores `visibleOutlines` as `875` bytes
- OE preserves visible outlines even across certain timed indoor respawns

Conclusion:

- this belongs in indoor `initial_state`
- but it should be exported in a preservation-friendly form, not renamed into
  speculative high-level semantics

### 3. Face Attributes

Status:

- structurally accounted for in both indoor and outdoor
- mapping differs:
  - outdoor maps them onto `(bmodel_index, face_index)`
  - indoor maps them onto flat `face_index`

Conclusion:

- indoor `.scene.yml` should use flat `face_index`
- outdoor shape should not be forced here

### 4. Decoration Flags

Status:

- structurally accounted for in both indoor and outdoor
- indexed against map decorations/entities

Conclusion:

- should stay attached to authored scene objects when practical
- indoor exporter may need either:
  - direct `entity.initial_decoration_flag` attachment if `BLV` entity export is
    part of the same step
  - or a separate indexed `initial_decoration_flags` section if the first step
    is truly `DLV`-only

### 5. Actors

Status:

- current OpenYAMM coverage is partial
- this is the biggest completeness risk

Important evidence:

- OpenYAMM parses actor records as `0x3cc`
- MMExtension confirms MM8 `MapMonster` size is `0x3CC`
- OpenEnroth MM7 actor snapshot is only `0x344`

This means:

- OE actor layouts are useful reference, but they are not enough to prove full
  MM8 actor coverage
- OpenYAMM currently decodes only a subset of the MM8 actor surface into
  `MapDeltaActor`

Fields currently exposed by OpenYAMM:

- `name`
- `npcId`
- `attributes`
- `hp`
- `hostilityType`
- `monsterInfoId`
- `monsterId`
- `radius`
- `height`
- `moveSpeed`
- `position`
- `spriteIds` as 4 values
- `sectorId`
- `currentActionAnimation`
- `group`
- `ally`
- `uniqueNameIndex`

Fields present in MM8 `MapMonster` that are not currently represented in
`MapDeltaActor` and should be considered for migration coverage:

- full `monsterInfo` payload beyond current subset
- velocity
- yaw / direction
- pitch / look angle
- `currentActionLength`
- start / initial position
- guard position
- tether / guard radius
- `AIState`
- carried item
- `currentActionStep`
- full animation frame table surface
- sound ids
- spell buffs
- actor inventory items
- schedules
- summoner
- last attacker
- reserved MM8 tail bytes

Conclusion:

- a strict “do not miss fields” migration should not rely only on current
  `MapDeltaActor`
- recommended policy:
  - either expand the indoor/outdoor scene actor schema to cover the full MM8
    actor record surface
  - or preserve the unmodeled remainder as raw legacy bytes

Recommendation:

- for first migration correctness, include a raw preservation field for actor
  records if full semantic decode is not implemented yet

Suggested field:

- `raw_record_hex`

or

- `raw_tail_hex`

if the front portion is decoded semantically and only the undecoded MM8 tail is
preserved raw.

This recommendation applies to both `DLV` and `DDM`, because actor records are
shared between them.

### 6. Sprite Objects

Status:

- much better covered than actors

OpenYAMM currently preserves or exposes:

- ids
- position
- velocity
- yaw
- sound id
- attributes
- sector id
- age / lifetime
- glow multiplier
- containing item raw bytes
- spell ids / level / skill
- `field54`
- caster / target pid
- lod-distance-like byte
- caster ability
- initial position

Evidence:

- OpenEnroth `SpriteObject_MM7` matches the current `0x70` record size
- MMExtension `MapObject` aligns with the same surface

Remaining caution:

- `field54` still has unresolved meaning
- containing item is preserved raw, which is good for migration fidelity

Conclusion:

- sprite objects are close to migration-ready
- keep unresolved fields explicit and raw where needed

### 7. Chests

Status:

- effectively accounted for

Current OpenYAMM preserves:

- `chestTypeId`
- `flags`
- raw item payload
- inventory matrix

That is enough for a faithful first migration.

### 8. Doors

Status:

- structurally well accounted for
- indoor-only
- clearly belongs in indoor `.scene.yml`

Current OpenYAMM preserves:

- identity/state:
  - `attributes`
  - `doorId`
  - `timeSinceTriggered`
  - `state`
- motion:
  - `direction`
  - `moveLength`
  - `openSpeed`
  - `closeSpeed`
- topology counts:
  - `numVertices`
  - `numFaces`
  - `numSectors`
  - `numOffsets`
- referenced geometry/index arrays:
  - `vertexIds`
  - `faceIds`
  - `sectorIds`
  - `deltaUs`
  - `deltaVs`
  - `xOffsets`
  - `yOffsets`
  - `zOffsets`

Evidence:

- OpenEnroth `BLVDoor_MM7` is also `0x50`
- door index-vector reconstruction from `doorsData` is already implemented in
  OpenYAMM

Conclusion:

- the indoor door payload is suitable for direct structured YAML export
- no opaque blob is needed here

### 9. Persistent Variables

Status:

- fully accounted for

Current sizes:

- `mapVars`: `75`
- `decorVars`: `125`

These are shared with outdoor and should stay shared in schema shape too.

### 10. Location Time / Map Extra

Status:

- binary surface is accounted for
- MM8-specific semantics are confirmed enough for partial decode

Important MM8 confirmation from MMExtension:

- the final `24` bytes are not generic unused padding in MM8
- they contain:
  - `Bits`
  - `Ceiling`
  - `LastWeeklyTimer`
  - `LastMonthlyTimer`
  - `LastYearlyTimer`
  - `LastDailyTimer`

This matches the outdoor `.scene.yml` direction already adopted in the repo:

- decode `Bits`
- decode `Ceiling`
- do not treat the timer values as authored scene truth

Conclusion:

- indoor should use the same `environment` decoding approach as outdoor
- timers should not become authored `.scene.yml` state

## Confirmed MM8-Specific Points

These are important because OE is mostly MM7-oriented.

### Confirmed With MM8 Local References

- MM8 `MapMonster` size is `0x3CC`
- MM8 `MapExtra` layout extends the MM7 `LocationTime` payload with:
  - `Bits`
  - `Ceiling`
  - four timer values
- MM8 `MapObject` / sprite-object size remains `0x70`

### Practical Consequence

OE is still useful for:

- shared structure understanding
- indoor door layout
- visible outline storage
- broad location-time layout

But OE is not sufficient proof of complete MM8 actor semantics.

## Proposed Indoor `.scene.yml` Direction

## Design Rules

### Rule 1. Share The Common Envelope With Outdoor

Use the same top-level model family:

- `format_version`
- `kind`
- `source`
- `environment`
- `initial_state`

### Rule 2. Share The Common State Shapes Where The Legacy Data Is Shared

Use the same shapes for:

- `initial_state.location`
- `initial_state.variables.map`
- `initial_state.variables.decor`
- `environment.sky_texture`
- `environment.day_bits_raw`
- `environment.map_extra_bits_raw`
- `environment.flags.*`
- `environment.fog.*`
- `environment.ceiling`
- `initial_state.actors`
- `initial_state.sprite_objects`
- `initial_state.chests`

### Rule 3. Keep Indoor-Only Dynamic State Indoor-Specific

Add indoor-specific sections for:

- `initial_state.visible_outlines`
- `initial_state.face_attribute_overrides`
- `initial_state.doors`

### Rule 4. Do Not Pretend Indoor Faces Are Outdoor BModel Faces

Outdoor uses:

- `bmodel_index`
- `face_index`

Indoor should use:

- flat `face_index`

because indoor faces belong to the indoor face array, not to outdoor bmodels.

### Rule 5. Preserve Raw Legacy Data Where Semantic Coverage Is Still Incomplete

For first migration fidelity:

- preserve unresolved payload instead of silently dropping it

This is especially important for:

- actors
- any unresolved object/record tails

## Recommended Schema

This is the recommended long-term indoor scene envelope, even if a first
converter only fills part of it.

```yaml
format_version: 1
kind: indoor_scene
source:
  geometry_file: ""
  legacy_companion_file: ""
environment:
  sky_texture: ""
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
entities: []
spawns: []
initial_state:
  location:
    respawn_count: 0
    last_respawn_day: 0
    reputation: 0
    alert_status: 0
  visible_outlines:
    bitset_hex: ""
  face_attribute_overrides: []
  decoration_flags: []
  actors: []
  sprite_objects: []
  chests: []
  doors: []
  variables:
    map: []
    decor: []
```

## Notes On The Proposed Shape

### `entities` / `spawns`

These are present to keep the indoor schema family aligned with outdoor.

However:

- a pure `DLV -> .scene.yml` converter cannot populate them by itself
- they belong to later `BLV + DLV -> .scene.yml` indoor migration work

So for the first `DLV`-only migration step they may legitimately remain empty or
be omitted if loader rules allow omission.

### `initial_state.decoration_flags`

For indoor, the cleanest final shape depends on whether the same migration pass
also exports BLV entities.

If the converter only has `DLV`:

- keep them as a separate indexed array or indexed entries

If the converter also exports indoor entities from `BLV`:

- attach them directly to the matching entity entries, like outdoor does

Recommended first conservative indoor shape:

```yaml
decoration_flags:
  - entity_index: 0
    flag: 0
```

Later, when BLV entity export is added, this can be folded onto `entities`.

### `visible_outlines`

Recommended first preservation shape:

```yaml
visible_outlines:
  bitset_hex: "..."
```

Reason:

- preserves exact legacy state
- avoids pretending the bit layout is more semantically resolved than it is
- stays deterministic

Possible future editor-friendly derived view:

- `visible_outline_indices`

but the hex-preservation field should remain the authoritative imported state
unless we are fully confident about the bit encoding everywhere.

## Recommended Entry Shapes

### Indoor Face Attribute Override

```yaml
- face_index: 0
  legacy_attributes: 0
```

### Indoor Decoration Flag Entry

```yaml
- entity_index: 0
  flag: 0
```

### Indoor Door Entry

```yaml
- door_index: 0
  legacy_attributes: 0
  door_id: 0
  time_since_triggered_ms: 0
  direction:
    x: 0
    y: 0
    z: 0
  move_length: 0
  open_speed: 0
  close_speed: 0
  state: 0
  vertex_ids: []
  face_ids: []
  sector_ids: []
  delta_us: []
  delta_vs: []
  x_offsets: []
  y_offsets: []
  z_offsets: []
```

### Indoor Actor Entry

For a conservative first implementation, use the current shared actor shape plus
raw preservation:

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
  raw_record_hex: ""
```

Recommended improvement after that:

- expand actor schema to the full MM8 `MapMonster` surface
- then either remove `raw_record_hex` or keep it only for exact roundtrip
  assurance during transition

### Sprite Object Entry

The existing outdoor-style sprite-object shape is already close enough for
indoor too, with the same unresolved-field policy:

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

## What The First `DLV -> .scene.yml` Step Should Export

If the first converter really takes only `DLV` plus map identity, the minimum
sound export scope is:

- `format_version`
- `kind`
- `source.legacy_companion_file`
- `environment`
- `initial_state.location`
- `initial_state.visible_outlines`
- `initial_state.face_attribute_overrides`
- `initial_state.decoration_flags`
- `initial_state.actors`
- `initial_state.sprite_objects`
- `initial_state.chests`
- `initial_state.doors`
- `initial_state.variables`

This avoids blocking on BLV duplication while still giving a real indoor scene
supplement.

## What Later `BLV + DLV -> .scene.yml` Should Add

After the initial migration:

- `source.geometry_file`
- indoor entities exported from `BLV`
- indoor spawns exported from `BLV`
- any indoor face-interaction metadata duplicated out of `BLV`
- possible later indoor structure sidecars if the project splits geometry and
  scene state more finely

## Recommended Implementation Order

1. keep the indoor schema envelope aligned with outdoor
2. implement a `DLV` field inventory test/assertion pass
3. export the fields already fully understood:
   - location
   - visible outlines
   - face attributes
   - decoration flags
   - sprite objects
   - chests
   - doors
   - variables
   - environment/map-extra decode
4. treat actor migration as a special completeness task
5. only after that, layer in `BLV`-duplicated authoring data

## Practical Bottom Line

The indoor companion format is close enough to outdoor that one shared
`.scene.yml` family is the correct choice.

The main places where indoor genuinely differs are:

- visible outlines
- flat indoor faces instead of outdoor bmodel faces
- doors / mechanisms

The main place where the current OpenYAMM abstraction is not yet strong enough
for a “we did not miss anything” migration is:

- MM8 actor record completeness

So the correct next step is not to invent a second indoor schema.
It is to:

- keep one shared scene-yaml family
- add the indoor-only sections cleanly
- make actor preservation explicit until full MM8 actor decode is finished
