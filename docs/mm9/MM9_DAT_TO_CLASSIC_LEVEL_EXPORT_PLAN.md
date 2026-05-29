# MM9 DAT To Classic ODM/BLV Export Plan

Status: new direction. MM9 should be treated as a source asset format for level export, not as a game/runtime
integration target.

## Decision

Do not integrate MM9 as a native gameplay runtime. Keep the useful import work: DAT/DTX parsing, DAT-to-ODM/BLV
transcoding, bitmap extraction, source metadata, raw object diagnostics, event/mechanism sidecars, and map
classification.

The target output is classic OpenYAMM content:

- outdoor wilderness maps as ODM shells;
- cities may stay ODM shells when they work well enough in editor/game;
- dungeons/interiors should normally be BLV shells;
- MM9 DTX textures converted into classic bitmap assets;
- compact sidecars that preserve source provenance, mechanisms, bindings, and optional event hints;
- no imported MM9 monsters/NPCs as active gameplay entities;
- no native `game/mm9` world runtime requirement.

The exported levels should be useful shells: terrain/world geometry, collision, water, source props/models, and fully
working mechanisms. Hand-authored monsters, NPCs, quests, and level Lua can be added later.

## What To Keep

The existing export/discovery toolchain is the foundation:

- `tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py`
  - Parses MM9 DAT v66 world models, surfaces, polygons, planes, points, leaves, user portals, and object records.
  - Emits an ODM shell, `.material_aliases.yml`, `.mm9.yml`, `.model_assets.yml`, `.raw_objects.yml`, `.scene.yml`, and
    bitmap aliases.
  - Preserves source model/poly/surface/texture ids in metadata.
- `tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py`
  - Reuses the DAT geometry parse, emits a source GLB plus `indoor_geometry` metadata, then optionally calls
    `build/tools/mm9_compile_indoor_source` to write a BLV.
  - Supports `one_room`, `spatial_grid`, and `leaf_grid` sector strategies.
  - Uses `VisBSP` leaf data and DAT `UserPortal` records where available.
  - Emits `.geometry.yml`, `.bsp.yml`, `.mm9.yml`, `.material_aliases.yml`, `.raw_objects.yml`, `.scene.yml`, and
    optionally `.blv`.
- `tools/mm9_import_discovery/generate_mm9_events.py`
  - Derives mechanism/event sidecars from raw DAT objects and script evidence.
  - Already extracts mechanism kinds, activation flags, linear/rotating motion properties, timing, sounds, trigger
    outputs, and exact object-name/world-model bindings.
- `tools/mm9_import_discovery/classify_mm9_maps.py`
  - Produces `docs/mm9/MM9_MAP_RUNTIME_CLASSIFICATION.md`.
  - Correctly identifies that many current ODM exports are actually portal/BSP city maps.
- `tools/mm9_import_discovery/generate_mm9_maps_from_manifest.py` and
  `tools/mm9_import_discovery/regenerate_mm9_maps.sh`
  - Existing orchestration for selected or manifest-driven ODM/BLV generation.

Keep `docs/mm9/MM9_DAT_FORMAT_NOTES.md` as the parser contract. The old native DAT runtime goal docs can remain as
historical research, but they should not drive implementation.

## What To Drop

Do not continue the native `game/mm9` DAT world runtime work as the main path:

- no native DAT world renderer in gameplay;
- no native DAT party movement/collision runtime;
- no MM9 actor/NPC/monster runtime integration;
- no MM9 billboard fallback;
- no `.level.yml + DAT` playable runtime target;
- no broad shared-engine LithTech object model.

The runtime should load normal ODM/BLV maps plus normal scene/event data. Any MM9-specific code that remains should be
small import/export glue or a narrow compatibility hook for exported mechanisms.

## Target Map Classification

The manifest should become explicit and pragmatic:

- ODM:
  - broad outdoor wilderness/terrain maps such as `guberland`, `sturmford`, `thronheim`, `lindisfarne`, `thjorgard`,
    `drangheim`, `frosgard`, `mountainpass`, `yorwick`, `isleofashes`, `afterworld`.
  - cities can remain ODM if the exported shell is playable, has acceptable visibility/rendering, and only needs a
    small number of outdoor bmodel mechanisms.
- BLV:
  - dungeons, caves, building interiors, and maps that require sector/portal behavior for collision or navigation.
  - a city only if ODM export produces unacceptable collision, visibility, mechanism, or interaction behavior.

`docs/mm9/MM9_MAP_RUNTIME_CLASSIFICATION.md` is still useful as source-structure evidence, but it should not force
cities into BLV. If a city has dense `UserPortal`/`VisBSP` data but the ODM shell works in-game and the mechanisms are
manageable as outdoor bmodel mechanisms, keep it ODM.

## Output Contract

Each exported map should have:

- `<map>.odm` or `<map>.blv`
  - The playable classic geometry file.
- `<map>.scene.yml`
  - Runtime state shell: environment, no imported actors, no imported sprite objects unless deliberately enabled.
  - For BLV, `initial_state.doors` should be populated when the geometry compiler emits mechanisms.
  - For ODM, any outdoor model mechanisms should be declared or referenced here if not stored in a separate sidecar.
- `<map>.material_aliases.yml`
  - Texture alias table from short classic material names to source DTX paths and DTX metadata.
- `<map>.mm9.yml`
  - Source provenance: DAT path, scale, target format, bmodel/face/source mapping, stats.
- `<map>.geometry.yml`
  - BLV source geometry metadata, including rooms, portals, materials, and mechanisms.
- `<map>.bsp.yml`
  - BLV/DAT BSP diagnostics, especially `VisBSP` leaves and `UserPortal` evidence.
- `<map>.raw_objects.yml`
  - Lossless importer/debug sidecar only. Do not make gameplay depend on it directly.
- `<map>.events.yml` or a smaller `<map>.mechanisms.yml`
  - DAT-derived mechanism/event/binding records.
  - This can be generated from raw DAT objects during export and then consumed by the classic scene/event import path.
- `<map>.bitmaps/` or world texture output
  - DTX-derived BMPs/texture aliases for classic rendering.

For long-term cleanliness, gameplay should consume only the classic map, scene/event data, textures, and a compact
mechanism/event sidecar. The raw object dump should stay an audit artifact.

## Geometry Fidelity

The exporter should preserve source shape, not rebuild a "similar" map.

Required behavior:

- Preserve every DAT world model that contributes visible geometry, collision, water, or mechanism geometry.
- Preserve source polygon provenance for every emitted face:
  - source model index/name;
  - source poly index;
  - source surface index/flags;
  - source texture index/flags;
  - emitted bmodel/face index.
- Keep the verified LithTech axis conversion:
  - MM9/DAT uses `X/Z` horizontal and `Y` vertical.
  - OpenYAMM/classic maps use `X/Y` horizontal and `Z` vertical.
  - Conversion is DAT `(x, y, z)` -> OpenYAMM `(x, z, y)`, with the existing scale `2.56`.
- Keep polygon winding/plane-normal checks. The current ODM exporter already reverses triangles and corrects when the
  transformed source plane disagrees.
- Avoid geometry simplification that changes collision or mechanism face membership.
- For BLV, avoid merging faces that are mechanism targets, trigger surfaces, collision helper faces, or source
  provenance boundaries. If `merge_coplanar_faces` remains enabled, mechanism/collision-sensitive nodes need a no-merge
  flag.

Triangulation is acceptable where ODM/BLV requires it, as long as the source face mapping records fan splits and the
surface area/plane stays identical.

## Collision Policy

Collision is the most important correction to make.

Implemented baseline:

- `transcode_mm9_dat_to_odm.py` now assigns explicit face roles and records them in source metadata.
- `PhysicsBSP` and intentional invisible collision faces are emitted as `Invisible` without `Untouchable`.
- `VisBSP`, AI/pathing helpers, sound-only helpers, and water/helper volumes remain non-collidable where appropriate.

Target policy:

- `PhysicsBSP`:
  - invisible in normal rendering;
  - collision active;
  - not interactable/pickable unless explicitly marked by an event binding;
  - preserved in source metadata.
- `VisBSP`:
  - visibility/sector/portal source evidence;
  - normally not emitted as collision unless the source map lacks separate `PhysicsBSP` and validation proves it is
    needed.
- `AITRK*`, pathing rails, trigger volumes, sound-only surfaces:
  - invisible;
  - no party collision unless an explicit MM9 class/property says otherwise.
- `InvisibleBrush` and intentional invisible walls:
  - invisible;
  - collision active.
- Render-invisible should be independent from collision-disabled.

Implementation should introduce an export-side classification such as:

```yaml
source_collision_role: physics_hull | visibility_hull | trigger_volume | no_collision | visual
render_hidden: true
collision_enabled: true
interaction_enabled: false
```

Then map those roles to classic face attributes carefully. Do not use `Untouchable` as a generic synonym for invisible;
use it only when the classic runtime must not collide or interact with that face.

## Water Policy

Water should be classic non-diveable water:

- Do not import MM9 dive/swim/water-volume semantics.
- Use MM8/default water textures by policy unless a map explicitly needs a source DTX visual.
- Visible water surfaces should render as classic fluid/animated faces where practical.
- Water volumes should not become collision blockers.
- Ocean height should be represented by visible surfaces and classic water behavior only.

The current ODM exporter distinguishes some `Ocean`, `BlueWater`, and water-texture cases. That should be made explicit
and tested instead of relying only on texture-name heuristics.

## Mechanism Requirement

Mechanisms must work. This is the main remaining implementation area.

DAT source evidence:

- Mechanism objects are in DAT `ObjectData`, usually with a `Name` matching a source world model.
- `generate_mm9_events.py` already extracts:
  - classes such as `Door`, `RotatingDoor`, `WeightedLift`, `RotatingBrush`, `InvisibleBrush`, `DestructableBrush`,
    `BlueWater`, `Ladder`, `Shooter`, `ScriptObject`;
  - `MoveDir`, `MoveDist`, `Speed`, `ClosingSpeed`;
  - `RotationPoint`, `RotationAngles`, `OpenAway`;
  - `StartOpen`, `StartOn`, `Locked`, `PushOpen`, `TouchToOpen`, `ReopenOnContact`, `DoubleDoorName`;
  - `MoveDelay`, `OpenWaitTime`;
  - open/close/trigger outputs and sounds;
  - bindings from object names to ODM/BLV bmodels/source model names.

Indoor BLV plan:

- Emit BLV mechanisms through `indoor_geometry` `mechanisms:` entries.
- The existing indoor source compiler already supports mechanism metadata with:
  - `source_nodes`;
  - `trigger_surfaces`;
  - `door.direction`;
  - `door.move_length`;
  - `door.open_speed`;
  - `door.close_speed`;
  - `door.initial_state`.
- Linear doors/lifts should map directly:
  - DAT `MoveDir` -> OpenYAMM direction `(x, z, y)`;
  - DAT `MoveDist * 2.56` -> `move_length`;
  - DAT speeds scaled to OpenYAMM units;
  - affected source node is the bound DAT world model.
- Trigger faces should be mapped from DAT trigger volumes or nearest/use faces into `trigger_surfaces` or classic event
  face ids.
- `StartOpen`, locked state, and initial position should populate scene initial door state.

Indoor BLV gaps:

- Current indoor mechanism metadata is linear. DAT rotating doors/brushes need either:
  - a small extension to indoor compiled mechanisms/runtime to support rotation around a pivot; or
  - a documented approximation for maps where the visual/collision result remains acceptable.
- For fidelity, rotating mechanisms should not be flattened into static geometry.
- The BLV compiler must keep mechanism source nodes separate and not merge their vertices/faces into static room
  geometry in a way that loses affected face/vertex membership.

Outdoor ODM plan:

- Use ODM bmodels for exported DAT world models.
- Register mechanism definitions against bmodel names/indices from the generated mechanism sidecar.
- The current outdoor runtime already has an MM9-oriented model-mechanism path with translation and rotation fields in
  `EventRuntimeState::OutdoorModelMechanismDefinition`.
- That path should be preserved or generalized as imported outdoor bmodel mechanisms, so it is not tied to a native MM9
  game mode.
- Collision and rendering must use the moved bmodel geometry. Mechanism state should not be visual-only.

Outdoor ODM gaps:

- The exporter should write stable mechanism declarations into `.scene.yml` or `.events.yml` so outdoor runtime can
  register them without reading raw MM9 dumps.
- Trigger/use faces need classic event ids or a small sidecar mapping from face/bmodel to mechanism id.
- Moving outdoor bmodel collision needs acceptance tests for door blocking, platform floor support, and rotation.

## Events And Scripts

Events should be classic-style and editable:

- Export interactable face/event bindings where the DAT provides enough information.
- Prefer generating normal map Lua/event files from a compact sidecar, similar to MM6-MM8 generated event scripts.
- Keep source provenance in comments/metadata, but make the generated script editable through the normal pipeline.
- It is acceptable for initial maps to have sparse event behavior; the user can add quests and custom logic later.
- Mechanism events are not optional: the generated scripts or scene state must be able to open/close/toggle mechanisms.

Practical first pass:

- Generate Lua helpers for `open`, `close`, `toggle`, and `locked` messages.
- Convert `ExitTrigger` to map transition stubs with destination map/startpoint metadata preserved, but not necessarily
  fully wired to campaign travel yet.
- Preserve unresolved target names in diagnostics instead of silently dropping them.

## Props And Referenced DAT Objects

Do not import NPCs/monsters as active gameplay actors.

For DAT objects with referenced models:

- Static map objects such as boats, moats, doors, machinery, and large props should become geometry, usually bmodels or
  static model instances depending on collision needs.
- Objects with `Solid` should get collision if they are part of the shell.
- Objects with `RayHit` and no solid collision can become future interaction markers.
- NPCs/monsters should be skipped from runtime actors and preserved only in diagnostics/source metadata.
- Sound-only, script-only, spawn-only, and AI-only objects should not create visible geometry unless they bind to a
  mechanism or shell object.

For highest compatibility, source world models that are already in DAT should become bmodels. ABC/GLB object models can
remain model instances only if they do not need to behave as classic bmodel mechanisms.

## Sidecar Strategy

Keep sidecars compact and purposeful.

Useful runtime/import sidecars:

- `material_aliases.yml`: texture alias source of truth.
- `mm9.yml`: source provenance and emitted face/model mapping.
- `geometry.yml`: BLV compiler input.
- `scene.yml`: normal runtime state shell.
- `events.yml` or `mechanisms.yml`: compact mechanism/event declarations.

Diagnostic-only sidecars:

- `raw_objects.yml`: full DAT object dump.
- `bsp.yml`: parser/portal/leaf diagnostics.
- broad model asset reports.

Avoid requiring gameplay to read `raw_objects.yml`. If a field is needed at runtime, promote it into `scene.yml`,
`events.yml`, `mechanisms.yml`, or the classic map file during export.

## Validation Gates

Add exporter-focused tests and smoke checks:

- DAT parse gate:
  - all 45 local DAT files parse with zero failures;
  - object properties decode;
  - leaf polygon refs validate.
- Geometry gate:
  - emitted face count plus skipped count matches source polygon accounting;
  - no degenerate face emission;
  - source model/poly/surface provenance covers every emitted face;
  - normal/winding checks pass.
- Texture gate:
  - every emitted material alias resolves to a bitmap or explicit fallback;
  - water aliases use the chosen MM8/default water policy.
- Collision gate:
  - `PhysicsBSP`/invisible wall faces are hidden but collidable;
  - `Untouchable` is not accidentally applied to required collision hulls;
  - party movement blocks against exported helper collision in at least one outdoor map and one BLV city/dungeon.
- Mechanism gate:
  - every DAT mechanism is classified as exported, explicitly unsupported, or intentionally skipped;
  - linear doors/lifts work in BLV and ODM;
  - rotating mechanisms work or are listed as blocking gaps;
  - moved mechanism collision matches moved visual geometry;
  - trigger/use opens a real exported mechanism.
- No-MM9-game gate:
  - exported maps load through normal ODM/BLV runtime paths;
  - no native DAT gameplay runtime required;
  - no imported MM9 monsters/NPCs.

## Immediate Work Plan

1. Freeze the new scope.
   - Treat `tools/mm9_import_discovery/*`, parser docs, and generated map sidecars as the assets to carry forward.
   - Stop adding native playable DAT runtime features.

2. Fix map classification/manifest policy.
   - Keep cities as ODM unless a specific map proves it needs BLV.
   - Keep dungeons/interiors as BLV.
   - Use classification as an audit signal, not an automatic format switch.

3. Fix collision attribute export.
   - Add explicit face roles for visual, physics hull, visibility hull, trigger volume, water, AI/pathing, and no
     collision.
   - Make `PhysicsBSP` and invisible walls hidden-but-collidable.
   - Add collision smoke tests before mechanism work.

4. Make BLV mechanisms export.
   - Done for bound linear doors/lifts: `transcode_mm9_dat_to_blv.py` splits those DAT bmodels into `MECH_*` GLB
     nodes and emits `indoor_geometry.mechanisms`.
   - The existing indoor compiler now writes `IndoorSceneDoor` records for that slice.
   - Rotating indoor mechanisms remain preserved in compact scene/event metadata and are still a follow-up gap.

5. Generalize outdoor mechanisms.
   - Generated ODM `.scene.yml` now contains compact mechanism declarations with bmodel bindings, linear deltas, and
     rotation pivots/angles.
   - Outdoor runtime now parses these scene mechanisms and registers them through the generic outdoor bmodel mechanism
     path. This keeps ODM city/outdoor mechanisms independent from the older MM9-specific `.events.yml` registration.

6. Keep events minimal but usable.
   - Generate face-to-event bindings for mechanism use.
   - Generate Lua stubs that call existing classic mechanism APIs.
   - Leave quests/NPC dialogue/monster placement to later hand authoring.

7. Regenerate representative maps and test in editor/game.
   - Current generated acceptance slice lives under `assets_dev/worlds/mm9_openyamm/`.
   - ODM: `thjorgard`.
   - ODM city: `thjorgardcity`.
   - BLV dungeon: `darkpassageway`.
   - Broader batch remains: `guberland`, `sturmford`, `thronheim`, `lindisfarne`, and a smaller city.
   - BLV dungeon: `darkpassageway` or another already proven BLV prototype.

## Practical Commands

Build the indoor compiler:

```bash
cmake --build build --target mm9_compile_indoor_source -j25
```

Regenerate curated maps:

```bash
tools/mm9_import_discovery/regenerate_mm9_maps.sh
```

Regenerate selected maps under the new policy:

```bash
tools/mm9_import_discovery/regenerate_mm9_maps.sh --clear-defaults --outdoor THJORGARD --indoor THJORGARDCITY
```

Run map classification:

```bash
python3 tools/mm9_import_discovery/classify_mm9_maps.py
```

## Open Questions

- Which exact face attributes should represent hidden-but-collidable outdoor ODM helper faces? This must be verified
  against party movement and picking, not guessed from names.
- Should rotating indoor mechanisms get a small native extension, or should the first export pass require manual review
  for those maps?
- Should `events.yml` remain the mechanism sidecar, or should a smaller `mechanisms.yml` be generated from it for
  runtime/import use?
- Which cities actually need BLV, if any? Default to ODM city shells unless collision, visibility, or mechanisms prove
  otherwise.
- Should source props from ABC/GLB become classic bmodels when they need collision, or remain model instances plus
  separate invisible collision hulls?

## Success Definition

This work is successful when MM9 source maps can be regenerated as classic OpenYAMM maps with:

- visually faithful terrain/world geometry;
- working party collision from DAT helper/physics geometry;
- non-diveable classic water;
- no imported MM9 actors/monsters;
- source props preserved where useful;
- working doors/lifts/rotating mechanisms through classic ODM/BLV runtime paths;
- editable classic event/Lua hooks for interactable faces;
- compact source sidecars sufficient for debugging and future regeneration.
