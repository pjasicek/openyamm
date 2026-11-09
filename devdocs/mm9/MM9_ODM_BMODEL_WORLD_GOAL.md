# MM9 ODM BModel World Goal

Long-term goal: consume MM9 maps as ODM-backed BModel worlds, including enclosed dungeons, while retaining the existing
`OutdoorRenderer`, `OutdoorWorldRuntime`, movement, interaction, event, and gameplay systems. Add explicitly opted-in
support for polygon-heavy BModel worlds without changing behavior or performance for existing classic ODM maps.

Current milestone: make only `bootcamp.odm` (Ravensford/Bootcamp) a desktop BModel-world foundation with correct
visible and collision geometry, usable cooked navigation/pathfinding, and working mechanisms. Bootcamp is small, but
contains representative static geometry, rotating and sliding doors, paired doors, switches, and source-script
linkages. NPCs, chests, quests, and other gameplay content may be hand-authored incrementally, but are not acceptance
requirements for this milestone. Do not author or validate another MM9 map until this foundation establishes the
workflow. Generic BModel-world runtime code may remain map-independent, but Bootcamp is the only active content target
and acceptance gate.

The intended tradeoff is simpler conversion and authoring at the cost of less efficient visibility than a reconstructed
BLV portal/sector graph. Do not reconstruct MM9 indoor portals unless a later map-specific requirement proves that an
ODM BModel world cannot represent the required behavior.

## Non-Negotiable Compatibility Boundary

- Existing MM6/MM7/MM8/MMerge ODM maps must retain their current renderer and runtime paths by default.
- Existing scenes that do not declare a new profile must parse and behave exactly as classic ODM scenes do now.
- Do not select MM9 behavior based on world id, `no_terrain`, missing terrain, BModel count, or other inference.
- `no_terrain` is not a sufficient discriminator. Existing non-MM9 maps such as `elema.odm` and `Breach.odm` already
  use it.
- Do not add per-face or per-actor checks for the new profile to classic hot loops. Select the resource/runtime path
  once at map load or once per render pass.
- Do not allocate MM9 chunk or cooked navigation resources for classic maps. Mechanism resources exist only for maps
  whose scene declares a `mechanisms` section (see [Mechanisms on classic ODM scenes](#mechanisms-on-classic-odm-scenes)).
- Keep final collision, picking, actor movement, projectiles, decals, lighting, and gameplay systems shared.
- Keep MM9 BModel-world content and packaging desktop-only for now. Do not add MM9 assets or startup configuration to
  Android builds until Android support is explicitly requested later.

## Representation Decision

Keep the existing outdoor scene and runtime ownership, but separate geometry representation from gameplay environment.

Add explicit optional scene fields equivalent to:

```yaml
scene_profile: "bmodel_world"
environment:
  location_type: "enclosed"
```

Supported values:

- `scene_profile: classic_odm`
  - Default when omitted.
  - Uses the current BModel resource construction, rendering, collision, and pathfinding paths unchanged.
  - May declare typed BModel `mechanisms` (doors, lifts, switches); destructibles and trigger volumes still require
    `bmodel_world`.
- `scene_profile: bmodel_world`
  - Explicitly enables MM9-style spatial render chunks, typed dynamic BModel mechanisms, and cooked navigation.
- `environment.location_type: exterior`
  - Default when omitted.
  - Uses current sky, weather, daylight, outdoor travel, and outdoor gameplay rules.
- `environment.location_type: enclosed`
  - Uses dungeon lighting/environment rules while still using ODM/BModel world representation.

Do not couple `bmodel_world` to `enclosed`: MM9 exterior and enclosed maps should use the same geometry profile while
choosing different environment semantics.

## Implementation Status

Implemented:

- The MM9 package contains 45 generated ODM maps, and every MM9 map-stat row names the corresponding ODM file.
- Every generated scene explicitly selects `bmodel_world` and either `exterior` or `enclosed`; omitted fields still
  resolve to `classic_odm` and `exterior` for existing content.
- Generated Lua and authored map-event overlays are loaded from `events/maps/`. Generated chunks no longer terminate
  before an appended authored script can execute.
- Generated collections and `<map>_authored.scene.yml` content have separate ownership. The editor saves only authored
  tails for BModel-world maps, and regeneration leaves authored scene and Lua files untouched.
- Typed linear and pivot-rotation mechanisms are loaded from scene data. Rendering, collision, picking, floor support,
  party carrying, and navigation blockers consume the same runtime transform.
- All 45 maps have cooked navigation sidecars with 64-bit source identity. The cooker merges safe coplanar surfaces,
  preserves AI barriers, excludes inappropriate source faces, and separates dynamic mechanism facets.
- All 45 maps have cooked render sidecars. Static faces are grouped into cell/material GPU buffers, moving mechanisms
  remain dynamic, chunks are culled conservatively, and static CPU vertex staging is released after upload.
- MM9's explicit transparent-surface flag is preserved in cooked render records. Transparent faces are separated from
  opaque material batches and submitted in a late alpha-blended pass without depth writes; DTX/BMP alpha alone does
  not change an opaque face's render mode. Bootcamp's `Clouds1` window panes exercise this path.
- Enclosed maps suppress weather and the outdoor sky, use dungeon-like atmosphere and clipping, expose indoor gameplay
  semantics, and use a cached vector minimap derived from cooked navigation barriers.
- Rest is an explicit runtime restriction for both indoor and outdoor scene formats.
- Thjorad Mine and Thjorgard were used as early infrastructure prototypes. Their existing authored data may remain, but
  they are no longer active vertical-slice targets or release gates. New MM9 content work is limited to Bootcamp.
- A desktop headless `.oysav` round-trip gate opens an authored chest, mutates an actor, fully opens a real linear or
  rotating BModel mechanism, reloads the destination map assets, and verifies the actor, chest, mechanism state, and
  transformed geometry. Restore deliberately rebuilds mechanism definitions from current map data so stale or older
  save definitions cannot discard authored pivot/rotation data.
- Unsupported source mechanisms are now an explicit audit-only boundary: 297 script-linked `InvisibleBrush` collision
  volumes and 15 continuous revolution-time `RotatingBrush` objects. The package checker rejects any new unclassified
  unsupported class. Audit-only objects remain static instead of being placed in dynamic render/navigation resources.
- The 45 source-script IR files are also explicitly non-executable audit data (569 parsed scripts, 28,110 source
  commands, and 7,718 currently unclassified commands). Playable behavior comes from generated supported mechanism
  handlers plus authored overlays; the IR is never treated as silently implemented gameplay.
- The existing broad package and prototype gates remain useful infrastructure diagnostics, but the active content gate
  is now `tools/mm9_import_discovery/run_mm9_bootcamp_gate.sh`.
- Bootcamp has 27 executable endpoint mechanisms: its supported doors, source-declared paired doors, two generated
  rotary `Switch` controls, two generated linear `Button` controls, and two authored encounter/chest switches. The
  literal switch/button BModels use their source pivots or movement vectors and remain in the dynamic render,
  collision, and navigation resources.
- Typed mechanisms now keep their runtime mechanism id and face interaction event id as separate values. Bootcamp's
  generated scene records both explicitly (for example, Door0 uses mechanism `900565` and event `30565`), while older
  scenes can derive the interaction event from the bound face. E/Space picking therefore dispatches the map event
  instead of narrowing a large mechanism id to `65535`. Focused unit coverage verifies the distinct id spaces, and the
  Bootcamp gate verifies that event `30565` drives Door0 and that its closed/open collision passage behaves correctly.
- MM9 `RotatingDoor.OpenAway` is preserved in the generated mechanism schema. When an opening begins, the runtime
  chooses the positive or negative authored rotation once from the party's side of the closed leaf, so both halves of
  a double door swing away from the opener instead of one swinging toward them. The direction is part of persistent
  mechanism state, feeds the shared render/collision/picking/navigation transform, and adds no per-frame geometry
  classification. The Bootcamp gate verifies opposite directions for the real `MonsterDoor1`/`MonsterDoor2` pair and
  verifies an open rotating door's geometry through a save/load round trip.
- Bootcamp is explicitly `bmodel_world` plus `environment.location_type: exterior`, matching both the source classifier
  and its `PLAINS` map-stat entry. Its BModel-only geometry representation does not turn the training island into an
  enclosed dungeon.
- Bootcamp keeps source-textured `PhysicsBSP` faces visible and collidable because they contain structural surfaces not
  duplicated by the ordinary visual world models, including training-area geometry. `VisBSP` remains a skipped hidden
  visibility helper; treating it as the visual replacement dropped the raised platform/stairs and was reverted. The
  restored platform, both stair runs, railings, pedestals, and surrounding room geometry were manually confirmed in a
  desktop Bootcamp screenshot.
- The source `timer lever 03a` linkage to `axe trap 03` remains an explicit unresolved warning because that target is
  absent from the shipped Bootcamp world. The lever itself still moves; no replacement trap is invented.
- The Bootcamp authored layer contains two initially hidden encounter actors, a map-local NPC, five interactive chests,
  one exit transition, and an enabled save policy. The focused gate verifies each interaction and both linear and
  rotating save/geometry round trips.
- The focused gate activates the encounter before simulating actor AI and verifies hostile walking and movement on the
  cooked navigation surface.

Remaining before the current Bootcamp milestone can be considered complete:

- Manually verify walking on the restored platform/stairs, closed/open door passage, actor pursuit, and the important
  button/switch linkages in a desktop Bootcamp playthrough. Focused automated gates establish the exact cases to test;
  broad NPC/chest/quest validation is outside this milestone.
- Implement continuous `RotatingBrush` motion or script-linked `InvisibleBrush` state only if Bootcamp demonstrates a
  concrete need. Audit-only source objects must otherwise remain static and non-executable.

## Target Runtime Shape

Retain the current renderer and runtime classes. Select one resource layout for each loaded map:

```text
OutdoorRenderer / OutdoorWorldRuntime
|
+-- classic_odm
|   +-- current resource construction
|   +-- current BModel draw grouping
|   +-- current collision and path construction
|
+-- bmodel_world
    +-- spatially chunked static render resources
    +-- separate dynamic mechanism resources
    +-- static collision index plus dynamic mechanism collision
    +-- cooked navigation surface plus dynamic blockers
```

This is not a separate MM9 renderer. Shared rendering features, shaders, texture animation, water, lighting, fog,
sprites, actors, particles, decals, and interaction should continue to be implemented once.

## Static Rendering For BModel Worlds

Cook spatial render data during import/build rather than repeatedly reorganizing the complete scene at runtime.

- Divide static geometry into conservative spatial cells, initially around 2,048-4,096 world units.
- Batch visible faces by spatial cell and resolved material/animation family.
- Record an AABB for every cooked render chunk.
- Exclude invisible PhysicsBSP faces from render buffers.
- Exclude movable mechanisms from static chunks.
- Frustum-cull chunks before submission.
- Apply a configurable conservative view-distance limit for enclosed maps.
- Initially rely on the depth buffer for wall occlusion instead of recreating portals.
- Keep enough face provenance to apply event-driven visibility, texture, and attribute changes without rebuilding the
  entire map.
- Release CPU render staging data after GPU upload when it is not also required for collision, picking, or authored
  event state.

The current classic BModel draw-group construction must remain available and unchanged for `classic_odm`.

If profiling later proves that frustum, distance, batching, and depth rejection are insufficient, investigate coarse
occlusion queries or optional authored visibility zones. Do not begin with a portal reconstruction project.

## Collision And Floor Support

- Continue using `OutdoorGeometryUtils` and `OutdoorMovementController` as the authoritative shared ODM collision path.
- Retain BModel floor support for `no_terrain` worlds.
- Build the static face spatial index once from non-moving geometry.
- Store mechanisms in a small dynamic collision layer.
- Update only a moving mechanism's transformed faces and occupied cells while it animates.
- Do not rebuild the complete static face grid at 30 Hz.
- Ensure moving floors can carry the party and actors.
- Ensure closed doors block party movement, actors, projectiles, picking, and line of sight.
- Ensure sufficiently open doors stop blocking those systems.

## Typed BModel Mechanisms

Promote generated mechanism definitions into the outdoor scene schema and runtime state. A mechanism should identify:

- stable mechanism id;
- one BModel or an explicitly ordered BModel group;
- source/debug name;
- closed and open transforms;
- optional pivot;
- linear or rotational motion;
- movement duration/speed;
- initial state;
- open, close, toggle, and stop semantics;
- push, touch, locked, and disabled behavior where needed;
- whether a moving platform carries the party;
- interaction event id and hint;
- start, busy, stop, open, and close sounds.

Use a shared transform representation for rendering, collision, picking, floor support, and projectiles. Do not
implement separate visual-only and collision-only mechanism transforms.

Implementation order:

1. Load typed linear mechanisms directly from scene data.
2. Make existing generated linear doors and lifts executable without MM9-specific runtime callbacks.
3. Add rotation around an authored pivot.
4. Add grouped mechanisms only for source objects that demonstrably require multiple BModels.
5. Track unsupported source mechanism classes explicitly and resolve them map-by-map or class-by-class.

Lua should activate and condition mechanisms; it should not own their geometry or duplicate their motion definitions.

### Mechanisms On Classic ODM Scenes

Since 2026-10-29 a `classic_odm` scene (no `scene_profile`, as in the MM9 rework maps built as native ODMs) may carry
the same top-level `mechanisms` sequence as a BModel world. The schema is identical; for example a hinged hut door:

```yaml
mechanisms:
  - mechanism_id: 900042        # runtime id, used by evt.SetOutdoorModelMechanismState(900042, 0|1|2)
    event_id: 30042             # map event of the door's clickable faces (their cog_triggered_number)
    source_object_index: 42
    source_class: "RotatingDoor"
    source_name: "HutDoor"
    kind: "rotating_door"       # linear_door, weighted_lift, rotating_door, ...
    binding:
      target_kind: "odm_bmodel"
      bmodel_index: 12
      bmodel_name: "HutDoor"
    motion:
      rotation:                 # or linear: {delta_openyamm: {x, y, z}}
        pivot_openyamm: {x: 1008, y: -64, z: 0}
        rotation_angles_openyamm_deg: {x: 0, y: 0, z: 90}
      move_time_ms: 1800
    activation:
      start_open: false
      open_away: true           # swing away from the opener; the chosen direction is saved
    sounds:
      open_start: "Door/door01open.wav"
      close_stop: "Door/door01close.wav"
```

The door's faces stay in the ODM at their closed position and are listed in `bmodel_faces.interactive_faces` with the
clickable attribute and `cog_triggered_number: 30042`; the map Lua registers event 30042 and calls
`evt.SetOutdoorModelMechanismState(900042, 2)` (0 open, 1 close, 2 toggle). Mechanisms live in the base scene: the
`_authored.scene.yml` overlay does not read a `mechanisms` section.

Runtime behaviour on a classic map:

- The mechanism definitions are built at load exactly as for BModel worlds. A map without the section builds none,
  and every per-frame mechanism path returns on the empty mechanism map, so MM6-MM8 maps are unchanged.
- The classic renderer leaves mechanism BModels out of its static draw groups and draws them per frame with the shared
  runtime transform; collision, picking, LOS, floor support and party carrying use the same transform.
- Actor pathing uses the classic grid path map, which is built from the transformed collision faces. It is rebuilt
  once when a mechanism settles at an endpoint (not while it moves), and the actors' planned routes are dropped then,
  as indoors. The same rule now applies to BModel worlds.
- Saves keep the mechanism state and the open-away direction; restoring a save (or revisiting the map) re-places every
  mechanism's collision at its restored state, for both profiles.
- Limits: the outdoor lighting bake treats a door as static at its closed position (baked shadows and lightmaps do
  not follow it), and water reflections show the static BModels only.

## Navigation For BModel Worlds

Do not feed every rendered and collision face directly into `PathMap` for MM9 maps. Generate a separate cooked
navigation surface.

The cooker should:

- select walkable floor and slope faces;
- use PhysicsBSP as collision evidence without duplicating coincident visible floors;
- exclude decorative baked props, ceilings, foliage, water helpers, secret helpers, and other non-navigation geometry;
- weld or merge safe coplanar adjacent triangles;
- retain blocking walls and useful AI barriers;
- use stable, unrestricted source identity rather than a 4,096-face packed range;
- retain enough height separation for bridges, balconies, lifts, and stacked dungeon floors;
- emit diagnostics for disconnected components, unsupported slopes, duplicate floors, and isolated spawn positions.

Doors should be dynamic navigation blockers. Do not rebuild the complete navigation surface during door animation.
Elevators and moving platforms may expose dynamic floor support and explicit off-mesh links if ordinary adjacency cannot
represent them safely.

Actor pathfinding remains shared. Add MM9-specific behavior only through cooked data and the explicit scene profile.

## Enclosed Environment Semantics

ODM storage must not force outdoor gameplay behavior. For `location_type: enclosed`, define and test:

- no weather or precipitation;
- no outdoor sky unless explicitly requested;
- dungeon daylight and ambient-light rules;
- map-specific fog and view distance;
- fly, Town Portal, Lloyd's Beacon, and rest permissions;
- indoor-style ambient sound and music where appropriate;
- minimap behavior;
- encounter respawn behavior;
- map transitions and exit triggers.

Prefer explicit scene/runtime restrictions over hardcoded MM9 map names.

## Generated And Authored Content Ownership

Treat transcoded geometry and source-audit sidecars as generated inputs. Keep user-authored gameplay data separate.

Generated ownership:

- ODM geometry;
- texture/material aliases;
- source metadata and raw-object audit data;
- initial mechanism extraction;
- cooked static render chunks;
- cooked navigation surface;
- generated event/mechanism baseline.

Authored ownership:

- actors and encounter generators;
- NPCs and dialogue assignments;
- chests, pickups, and decorations;
- event assignments and quest logic;
- mechanism corrections/overrides;
- map transitions;
- environment and gameplay restrictions.

For Bootcamp specifically:

- `bootcamp.odm` is generated geometry and must not be edited to place gameplay content.
- `bootcamp.scene.yml` owns generated BModel bindings, extracted transforms, interactive facets, cooked-resource
  references, and the baseline mechanism list.
- `bootcamp_authored.scene.yml` owns hand-placed NPCs/actors, encounter generators, chests, items/decorations,
  transitions, start/exit data that is not source-derived, and the eventual save policy.
- Generated Bootcamp Lua owns source-evidenced paired-door activation and the baseline handlers for source controls.
  `bootcamp_authored.lua` owns the `Switch0`/`Switch1` encounter and chest actions, NPC dialogue, quest state, and
  Bootcamp-specific corrections to generated event behavior. It is appended after generated Lua and should use
  `ReplaceMapEvent` when intentionally replacing a generated handler.
- A wrong transform or binding shared by a source mechanism class is fixed in the transcoder and regenerated. A truly
  Bootcamp-specific semantic correction belongs in the authored overlay. Generated files are never patched by hand.

Implement an explicit overlay or detached authored map package so rerunning the MM9 transcoder cannot erase editor
work. Do not merge generated and authored ownership implicitly during save.

The implemented scene ownership boundary uses `<map>_authored.scene.yml`, discovered by the normal ordered outdoor
scene-overlay loader. Its `authored_content` map contains only editor-owned collection tails:

```yaml
format_version: 1
kind: outdoor_scene_overlay
source:
  geometry_file: "bootcamp.odm"
authored_content:
  entities: []
  spawns: []
  actors: []
  sprite_objects: []
  chests: []
```

The base loader records generated collection counts before applying overlays. The editor displays the combined state
but saves only entries after those base counts for `bmodel_world` maps, leaving the generated scene and ODM untouched.
Classic ODM save behavior remains unchanged. Generated map regeneration does not create, rewrite, or remove the
`_authored.scene.yml` file.

Generated map Lua must live under `events/maps/`. Generated Lua remains generated and must not be edited directly;
custom behavior belongs in a normal map overlay/fixup file or another explicitly authored script.
Use `<map>_authored.lua` (or the existing `<map>.fixup.lua` convention) under `events/maps/` for authored behavior.
The runtime appends those files after the generated `<map>.lua`, and MM9 regeneration only rewrites the exact generated
Lua and script-IR filenames.

## Data Integration

- Make every MM9 `map_stats.txt` filename agree with the generated ODM filename.
- Synchronize the required MM9 map rows into editor support data.
- Keep map names and world ownership canonical and namespaced.
- Decide whether the first playable pass uses existing merged MM6-MM8 monster definitions or imported MM9 monsters.
- Do not leave encounter names that silently fail to resolve.
- Add explicit world/map travel connections and start points.
- Enable saving only after authored scene state and transitions are stable.

## Implementation Phases

### Phase 1: Compatibility Boundary And Data Consistency

1. Add the optional scene and environment profiles with classic defaults.
2. Add parser, writer, overlay, editor, and round-trip coverage.
3. Mark MM9 generated scenes explicitly as `bmodel_world` and exterior/enclosed.
4. Correct MM9 ODM filenames in map stats and editor data.
5. Move/fix generated map scripts under `events/maps/`.
6. Add diagnostics proving representative MM9 event handlers resolve.

### Phase 2: Authored Content Boundary

1. Define the generated-versus-authored overlay/package format.
2. Make actor, spawn, entity, chest, restriction, and event edits survive MM9 regeneration.
3. Make the editor display and save the authoritative authored layer.
4. Add a regeneration round-trip test with representative authored content.

### Phase 3: Mechanism Baseline

1. Add typed outdoor BModel mechanisms to the scene schema.
2. Load and execute linear doors and lifts directly.
3. Validate render, collision, floor support, party carrying, picking, and event activation.
4. Add rotating pivot transforms.
5. Add focused support for the remaining common MM9 mechanism classes.

### Phase 4: Cooked Navigation

1. Define the navigation sidecar and importer output.
2. Remove the 4,096-face source identity limitation for this path.
3. Deduplicate and simplify MM9 navigation geometry.
4. Preserve useful AI barrier information.
5. Add dynamic door blockers and moving-platform handling.
6. Add representative pursuit tests across roads, stairs, bridges, doors, and stacked floors.

### Phase 5: Chunked Rendering

1. Define cooked static render chunks and provenance metadata.
2. Build per-cell/material GPU buffers for `bmodel_world` only.
3. Keep mechanisms in separate dynamic buffers.
4. Add frustum and distance culling.
5. Release unnecessary CPU staging copies.
6. Profile Bootcamp on desktop; retain the older Thjorgard measurements only as historical infrastructure baselines.

### Phase 6: Bootcamp Playable Slice

1. Verify all supported generated Bootcamp mechanisms and their render/collision transforms.
2. Author source-evidenced paired-door and switch linkages without editing generated Lua.
3. Hand-author representative actors/NPCs, an encounter, chests, items, and one transition in Bootcamp sidecars.
4. Enable and verify Bootcamp save/restore only after those authored objects are stable.
5. Use the focused Bootcamp gate and manual playthrough to drive any remaining runtime/editor work.
6. Defer every other MM9 map as a content target until the Bootcamp workflow is accepted.

## Classic Regression Gates

Before modifying the renderer, capture representative baselines for:

- a terrain-heavy MM7 or MM8 outdoor map;
- Dagger Wound;
- an outdoor map with many BModels;
- a map using animated water;
- `elema.odm`, which already uses `no_terrain`;
- `Breach.odm`, which already uses `no_terrain`.

Automated coverage should verify:

- scenes without the new fields resolve to `classic_odm` and `exterior`;
- classic maps do not construct cooked MM9 chunks or navigation resources;
- classic BModel, face, terrain, and actor counts do not change;
- deterministic classic draw-group and submitted-vertex counters do not change;
- representative floor, collision, picking, LOS, projectile, and pathfinding queries do not change;
- existing outdoor regression suites remain green;
- generated/authored MM9 round trips are stable;
- mechanism open/closed transforms affect rendering and collision identically.

Manual/release validation should compare:

- load time;
- steady-state frame time;
- render submission count;
- GPU-visible triangle count where available;
- resident and peak memory;
- first actor path-request hitch;
- mechanism animation frame time;
- Android validation is deferred while MM9 BModel-world support remains desktop-only.

No classic-map performance regression should be accepted merely because the visual result is unchanged. If a shared
refactor measurably slows classic maps, keep the classic implementation and isolate the BModel-world resource path.

### Desktop Reference Capture (2026-08-20)

One sequential desktop headless full-load sample from the same build produced the following reference values. These are
load/peak-memory diagnostics, not steady-state renderer benchmarks:

| Profile | Map | Elapsed | Peak RSS |
| --- | --- | ---: | ---: |
| `classic_odm` | Dagger Wound (`out01.odm`) | 4.19 s | 790,080 KiB |
| `classic_odm`, existing `no_terrain` | Plane of Air (`elema.odm`) | 3.21 s | 587,088 KiB |
| `classic_odm`, existing `no_terrain` | The Breach (`Breach.odm`) | 2.04 s | 175,260 KiB |
| `bmodel_world`, enclosed | Thjorad Mine | 2.22 s | 310,516 KiB |
| `bmodel_world`, exterior | Thjorgard City | 1.91 s | 212,780 KiB |
| `bmodel_world`, exterior | Bootcamp | 2.33 s | 333,908 KiB |

A 1,600x900 Xvfb/OpenGL 3.3 renderer smoke run from the same build, with VSync disabled and the first loading second
excluded, kept Dagger Wound at 230-251 FPS, Thjorad Mine at 232-246 FPS, and Thjorgard City at 232-251 FPS. This is a
repeatable software/virtual desktop comparison rather than a substitute for a native-GPU release benchmark; it shows
no obvious frame-time penalty specific to the opted-in BModel-world path in this environment.

Bootcamp's corresponding 1,600x900 Xvfb/OpenGL 3.3 smoke run, after correcting it to exterior semantics, stayed at
226-236 FPS after the first second. This remains a virtual-desktop smoke result; a native-GPU manual pass is still the
release-facing performance check.

## Bootcamp Acceptance Criteria

The Bootcamp MM9 ODM slice is complete when:

- it loads through a correct MM9 map-stat row;
- party start and exit transitions work;
- saving/restoring preserves authored state when allowed;
- static render chunks cull correctly without visible holes;
- collision, floor support, stairs, bridges, and stacked floors work;
- all 27 currently supported endpoint mechanisms resolve, and representative linear and rotating mechanisms render and
  collide correctly;
- the `Door0`/`Door1` and `Door2`/`Door3` pairs operate as door groups rather than unrelated leaves;
- `Switch0` and `Switch1` drive explicit authored encounter/open behavior and return to their resting position;
- `SwitchLever0`, `Portcullislever`, `timer lever 03a`, and `Button1` are clickable and animate using their source
  transforms; the absent `axe trap 03` target remains documented rather than fabricated;
- a closed door blocks actors and the party, and the same door permits passage when open;
- hostile actors can pursue the party through representative corridors and doors;
- placed actors, NPCs, chests, and events survive regeneration;
- generated and authored event handlers resolve from `events/maps/`;
- no classic ODM regression is observed in automated or manual baselines;
- desktop performance and memory are acceptable for Bootcamp.

The original MM9 `BC_Manager` script is behavioral evidence, not automatically executable content. It indicates that
`Switch0` starts a two-creature demonstration fight and `Switch1` spawns a friendly opener that visits three treasure
chests. The authored OpenYAMM slice may reproduce that behavior or define a smaller equivalent demonstration, but the
choice and concrete actor/chest content must be explicit rather than silently inferred by the importer.

## Explicit Non-Goals

- Reconstructing MM9 BLV portals, BSP room ownership, or sector graphs.
- Reimplementing the LithTech runtime.
- Copying OpenEnroth, mm_mapview2, or LithTech source code.
- Translating every original MM9 script before a playable vertical slice exists.
- Enabling the new path for classic maps through automatic detection.
- Adding broad compatibility fallbacks that hide stale map-stat, event-path, monster-table, or generated-content data.
- Maintaining two duplicated gameplay or renderer implementations.
