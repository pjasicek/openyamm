# MM9 DAT World Native Runtime Implementation Goal

Status: implementation goal for the first native MM9 DAT world runtime slice in `game/mm9/*`.

## Objective

Implement enough native MM9 DAT runtime support to enter `thjorgard` and `thjorgardcity` through debug/dev entry
points and get these behaviors working without relying on generated ODM/BLV world geometry or bulky generated
sidecars as runtime truth:

- DAT world geometry renders from the source DAT.
- Party movement and party collision work against DAT physics/helper geometry.
- Doors/mechanisms can be triggered, opened, closed, and interacted with.
- Placed MM9 objects, NPCs, and props use authored placement plus LithTech-style one-shot floor placement where enabled.
- MM9 object/NPC presentation is model/native asset oriented. Do not add or keep MM9 billboard visual paths under
  `game/mm9/*`.
- Runtime ownership stays MM9-scoped and does not bloat MM6-MM8 world systems.

The implementation should consume the editor-proven `game/mm9` data products where possible. Do not copy editor viewport
code into the runtime, and do not make the shared engine look like LithTech.

## Primary References

- `docs/mm9/MM9_DAT_FORMAT_NOTES.md`
- `docs/mm9/MM9_DAT_WORLD_RUNTIME_LITHTECH_FINDINGS.md`
- `docs/mm9/MM9_OBJECT_RUNTIME_PRE_DATWORLD_GOAL.md`
- `docs/mm9/MM9_LIGHT_LAYER_PRE_DATWORLD_GOAL.md`
- `game/mm9/Mm9DatWorld.*`
- `game/mm9/Mm9DatPhysicsQuery.*`
- `game/mm9/Mm9ObjectLayer.*`
- `game/mm9/Mm9LightLayer.*`
- `game/mm9/Mm9SkyLayer.*`
- `game/mm9/Mm9ScriptedObjectRuntime.*`
- `editor/document/EditorDocument.cpp`
- `editor/viewport/EditorOutdoorViewport.cpp`
- `assets_dev/worlds/mm9/maps/thjorgard.level.yml`
- `assets_dev/worlds/mm9/maps/thjorgardcity.level.yml`

## Proven Inputs

These pieces already exist and should be used:

- `.level.yml` files for Thjorgard and Thjorgard City declare `runtime.world_backend: dat_world`, source DAT paths,
  selected runtime policies, script paths, and asset/package routing. Any sidecar paths that remain in the manifests are
  editor/import diagnostics and are not native game-runtime inputs.
- `Mm9DatWorld` parses local MM9 DAT v66 world data and builds `Mm9DatRenderMesh`.
- `classifyMm9DatRenderMeshFilters` separates visual, helper, physics, visibility, rail, trigger, sky, terrain, movable,
  water-volume, and visible-water triangles.
- `Mm9DatPhysicsQuery` builds query views and already raycasts/segmentcasts real DAT physics and visible channels.
- The editor uses the same parser/filter/material path to render DAT geometry with DTX textures and source-model
  grouping.
- The editor preview path proves mechanism transform math for source-model batches using event mechanism data.
- `Mm9ObjectLayer`, `Mm9LightLayer`, `Mm9SoundLayer`, `Mm9SpawnLayer`, and `Mm9SkyLayer` project raw DAT objects into
  runtime-friendly source layers.
- `Mm9ScriptedObjectRuntime` already projects `MoveToFloor`, wander, scripted path, speed, and rough flying/rooted
  state from raw/scripted objects.
- Legacy MM9 scripted-billboard visual files have been removed from `game/mm9/*`; placed MM9 object presentation should
  resolve toward DAT source models, model assets, animated actor visuals, and later native static-model drawing.

## Runtime Input Policy

The target game-runtime input is one small `.level.yml` manifest plus the source DAT/native packaged assets. The
manifest may select the backend and name the source DAT, scripts, and asset roots, but the game runtime should not load
large generated YAML sidecars as authoritative world state.

The DAT already contains the core world data needed by the native runtime:

- static/world model geometry, world model names, surfaces, materials, BSP/leaf references, portals, and helper models;
- source object records at `object_data_pos`, including class names and properties such as placement, model/skin,
  `MoveToFloor`, triggers, lights, sounds, spawns, and mechanism/script properties;
- enough source ids to derive stable runtime handles for world models, polygons, surfaces, objects, and bindings.

Sidecar policy for the game runtime:

- `.level.yml`: allowed and expected as the small dev/content manifest.
- `.raw_objects.yml`: do not load in the game runtime. It is an importer/editor/losslessness dump of DAT `ObjectData`,
  not an inventory file and not a runtime format.
- `.dat_world.yml`: editor/import diagnostics only once C++ derives roles from `Mm9DatWorld` names/surfaces/flags.
- `.events.yml`: editor/import diagnostics only once C++ parses DAT object/script properties into native mechanism,
  trigger, and script binding records.
- `.scene.yml`: editor/import diagnostics only once C++ parses DAT object placement/model presentation directly into the
  runtime object registry.
- material/model/compatibility sidecars: importer/editor/cache data. The final runtime should resolve textures and model
  assets through packaged asset manifests or native caches, not map-local source YAML scans.

Editor/import tools may continue using compact bridge sidecars where they help validate parser coverage. Game loading in
`game/mm9/*` is `.level.yml` plus DAT/native packaged assets only; missing runtime fields should be exposed by the C++
DAT parser instead of promoted from sidecars. No per-frame path may parse YAML or do source-name string scans.

Current runtime status:

- `Mm9DatWorld` exposes DAT `ObjectData` records directly.
- `Mm9DatLevelRuntimeLoader` derives model render roles, runtime object records, event object records, mechanism motion,
  activation flags, trigger outputs, sounds, and exact object-name/world-model bindings from DAT data.
- `.dat_world.yml`, `.raw_objects.yml`, `.events.yml`, and `.scene.yml` are not read by the native game runtime loader.
- `Mm9DatMechanismRuntime` can command active DAT-derived mechanisms open, close, or toggle, advances progress by
  authored speed/distance, keeps current bounds in sync with the shared preview transform, and updates only queued
  moving mechanisms rather than scanning every mechanism every tick.
- DAT mechanism activation flags such as `PushOpen`, `TouchToOpen`, and `ReopenOnContact` are preserved on runtime
  mechanism instances. Party movement contact with an eligible mechanism issues an indexed open command and runs the
  same bounded render/collision/bounds sync path used by explicit Use interaction.
- DAT mechanism timing fields such as `MoveDelay`, `OpenWaitTime`, and `LockOnClose` are now preserved and applied by
  the queued mechanism updater. Delayed doors stay in the moving queue without advancing progress until the delay is
  consumed; opened doors with an authored wait remain queued and then start closing; `LockOnClose` locks once the close
  completes.
- `Mm9DatMechanismBoundsIndex` indexes active mechanism bounds into horizontal spatial cells. Movement and interaction
  rays query mechanism candidates from this index, and mechanism animation updates refresh only changed mechanism cell
  membership.
- `Mm9DatMechanismCollisionCache` stores source triangle indices and transformed collision triangles per active
  mechanism. Movement collision reuses these cached transformed triangles instead of rebuilding a source-model mesh from
  the full DAT render mesh on every party step. The cache also stores a mechanism-handle to batch index so movement
  candidates from the bounds grid resolve transformed collision batches without scanning all active mechanism batches.
- `Mm9DatCollisionWorld` now has spatial-cell-backed floor support and segment cast queries, and
  `moveMm9DatParty` performs the first DAT-native party step with wall blocking, slide projection, floor snap, and
  source/candidate diagnostics. Static movement also has a bounded step-up attempt that runs only after a wall block:
  one raised segment cast plus one floor-support query, so low collision lips can be crossed without adding per-frame
  scans.
- `moveMm9DatPartyInWorldRuntime` extends party movement to collide with active mechanism source-model triangles after
  applying the same mechanism transform path used by render/preview code. It also queries transformed mechanism
  triangles as possible floor support, so platforms/elevators can carry floor snap results with mechanism handle,
  object id, source model, and source object diagnostics instead of falling back only to static DAT floors.
- `Mm9DatPartyRuntime` remembers the mechanism handle/progress for the floor currently supporting the party. After a
  mechanism update, party movement applies the same linear/rotating mechanism transform delta to that supported point
  with one handle-indexed lookup, then re-runs floor support. This gives moving platforms/elevators carry behavior
  without scanning all mechanisms or rebuilding collision geometry.
- Mechanism point transforms and inverse point transforms now live beside the existing DAT mechanism preview triangle
  transform helper. Rendered triangles, transformed collision geometry, and party moving-floor carry therefore share
  the same LithTech-to-OpenYAMM axis conversion and linear/rotation transform logic.
- Active mechanism source models are split out of immutable static render/collision batches into
  `Mm9DatMechanismRenderWorld` dynamic batches, so moving geometry has one transform authority and is not duplicated in
  static partitions.
- `Mm9DatPreparedRenderWorld` converts static render partitions and dynamic mechanism batches into contiguous
  vertex/index sections once at load time. Dynamic mechanism sections update their vertex ranges only when mechanism
  transforms change, giving the bgfx submitter grouped geometry without walking raw DAT triangles every frame.
- `Mm9DatRenderSubmissionPlan` turns prepared sections into renderer-facing draw commands with visible-section,
  draw-call, submitted-triangle, opacity-pass, dynamic/static, and texture-miss stats. The plan can also cull sections
  by bounds distance without touching raw DAT triangles.
- Runtime render diagnostics now separate visible water triangles from water-volume/helper triangles. Visible water
  remains in normal render partitions, while water volumes are skipped from normal rendering and counted as preserved
  query/debug data.
- `Mm9DatWorldRenderUploadPlan` splits prepared render sections into immutable static vertex/index data and dynamic
  mechanism vertex/index data. `Mm9DatWorldGeometryResources` and `Mm9DatWorldTextureResources` provide the first
  bgfx-facing upload/destroy helpers for DAT world geometry and DTX texture handles.
- `Mm9DatWorldRenderSubmitPlan` maps runtime draw commands to uploaded static/dynamic sections and loaded texture
  handles by stable material id. Missing upload sections or missing texture resources are accounted once while building
  the submit plan, and the live bgfx submit helper only binds section ranges and texture handles.
- `Mm9DatWorldRuntime` now builds `Mm9LightLayer`, static render-light records, `Mm9SkyLayer`, active sky definition,
  and sky camera-map data directly from parsed DAT `ObjectData` plus world info/model roles. Runtime light/sky ownership
  no longer needs `.raw_objects.yml` as a bridge.
- `Mm9DatRuntimeMaterialTable` deduplicates prepared render-section material keys into stable numeric runtime material
  ids, classifies missing/source/resolved materials, and marks texture-cache eligibility without consulting material
  sidecars.
- `Mm9DatRuntimeTextureCatalog` indexes native `source/textures` DTX files once at load time and
  `Mm9DatRuntimeTextureBindings` resolves texture-cache-eligible material ids to physical source DTX paths without
  per-frame source-name scans.
- `pickMm9DatWorldRuntime` provides the first shared DAT query path for interaction rays across static world
  collision, pickable runtime objects, and mechanism bounds, returning stable object/mechanism handles and source
  triangle/model ids where available.
- `useMm9DatWorldRuntime` routes interaction rays to mechanism commands, and `updateMm9DatWorldRuntime` advances
  mechanism motion while synchronizing dynamic mechanism render batch transforms and prepared dynamic vertex ranges.
- Thjorgard and Thjorgard City now have smoke coverage that picks a real DAT-derived active mechanism through native
  mechanism bounds and activates it through `useMm9DatWorldRuntime`, proving the acceptance maps are not relying only on
  synthetic mechanism fixtures for use-ray interaction.
- Thjorgard and Thjorgard City also have smoke coverage that initializes the native party state from the DAT-authored
  debug-entry start pose and runs a native movement tick that stays grounded on real DAT floor support. This proves the
  acceptance maps exercise the same spatial-cell floor query path the playable debug entry will use.
- `useMm9DatWorldPickedHitRuntime` can apply a mechanism/object command to an already-picked DAT hit, so gameplay
  activation does not have to re-run the ray query. Command application reuses the same bounded sync path for mechanism
  bounds cells, transformed collision batches, dynamic render batches, prepared dynamic vertices, and render-submission
  stats.
- MM9 DAT use results now carry a native activation record for the selected object and linked mechanism. This preserves
  object id/handle, source object index/class/name/model, script name/params, mechanism id/kind/source model, trigger
  outputs, and authored mechanism sound names from DAT-derived event data so the later Lua bridge can dispatch without
  re-parsing sidecars or re-picking the world.
- DAT trigger outputs are also converted into a native dispatch envelope during activation. The runtime resolves target
  names through load-time object id/source-name indexes, records ambiguity and candidate counts, and emits target
  handles/message names for the script bridge without scanning all objects during a use action.
- `Mm9DatSceneRuntime` can now receive the session-owned `Mm9ScriptRuntimeState`; successful native DAT activations
  append resolved trigger dispatches into that state. This keeps MM9 trigger evidence in the existing save/runtime state
  path while still avoiding per-use script package loads.
- When the native DAT scene has a loaded MM9 dialogue package, trigger dispatches are routed through `Mm9ScriptRuntime`
  from the activating object context. This records the dispatch in the same state path and can run registered target
  trigger callbacks without loading the package per interaction.
- Package-backed native DAT activation also runs the activating object's `OnUse` label from that object's MM9 script
  context before applying DAT trigger-output dispatches. This aligns object/mechanism activation with the existing MM9
  generated-script path while keeping package ownership cached at scene/application level.
- `loadMm9DatRuntimeForDevEntry` resolves `.level.yml` by MM9 map id, loads the native DAT runtime, selects DAT-authored
  `StartPoint` objects such as `FTThjorgardStart`/`StartPoint0`, and floor-snaps the initial dev pose through native
  DAT collision.
- `Mm9DatPartyRuntime` owns the first MM9 DAT party pose controller. It initializes from a DAT dev start pose, converts
  input axes through party yaw into native DAT displacement, advances mechanism/runtime updates, moves through native
  DAT collision, applies MM9-scoped falling velocity/gravity, keeps ground state, and builds party-facing use rays for
  mechanism/object/world interaction.
- Native DAT `requestPartyJump` now feeds the MM9 party vertical velocity instead of being a no-op, and landing through
  DAT floor support clears downward velocity.
- `Mm9DatPartyRuntime` also owns native teleport placement. Debug/runtime teleports can snap the requested DAT position
  to the same runtime-aware floor-support query domain used by party movement, including transformed mechanism floors.
  Teleport results preserve static/mechanism floor candidate/test counts, support metadata, and the current mechanism
  support handle when landing on an active moving floor.
- `Mm9DatSceneRuntime` and `Mm9DatWorldGameplayRuntime` provide the first shared-gameplay bridge for native DAT maps.
  The bridge presents MM9 DAT movement, use rays, teleport, game time, and HUD-safe runtime state through
  `IGameplayWorldRuntime`, while unrelated actor/combat/chest/minimap systems remain explicit stubs instead of pulling
  MM6-MM8 indoor/outdoor runtime ownership into `game/mm9`.
- `Mm9DatWorldGameplayRuntime` now builds shared `GameplayWorldPickRequest` rays from the native DAT party pose and maps
  native DAT world/object/mechanism pick hits into shared `GameplayWorldHit` values. Mechanism hits are exposed as
  `EventTarget/Mechanism`, object hits as `EventTarget/Object`, and MM9 source metadata preserves object id, source
  object index, source class/name, and the `mm9_dat` source marker for Lua/context-action routing.
- Shared gameplay hover/context-action routing can now inspect DAT mechanisms and mechanism-routed objects. Native DAT
  activation applies commands from the selected stable handle/object id instead of blindly firing a fresh party-facing
  use ray, while world/ground hits remain non-activatable.
- `Mm9DatObjectRegistry` now keeps typed load-time membership views for renderable, collidable, ray-hit, trigger,
  interactable, actor, prop, pickup, light, mechanism-linked, and ticking objects. These views are MM9-scoped and let
  future object rendering, AI, trigger, script, and query paths avoid repeated all-object scans or shared-engine
  category assumptions.
- `Mm9DatObjectPresentationWorld` now converts the renderable object view into a load-time presentation plan with stable
  object handles, source object ids, object/model/visual asset keys, position, bounds, object kind, and collidable,
  interactable, and ticking flags. This gives model/native object rendering a compact input without reclassifying or
  scanning all DAT objects every frame.
- MM9 billboard presentation has been retired from `game/mm9/*`. Existing shared outdoor billboard rendering remains
  for MM6-MM8 compatibility, but MM9 DAT runtime work must not depend on `scripted_billboards` assets or resurrect an
  MM9 billboard fallback in `game/mm9`.
- Solid collidable DAT objects are indexed into horizontal cells at load time. Native party movement queries that index
  when sweeping through the world, so props/actors with runtime collision radii can block movement without scanning all
  objects every step.
- Runtime stats expose collidable-object cell counts, cell refs, and max refs. Thjorgard/Thjorgard City smoke tests
  assert the movement collision index is populated from real DAT objects.
- The object registry also keeps object-id/object-handle indexes and an object-index to actor-index table, while
  source-name lookup is handled by a load-time name index. `Mm9DatMechanismRuntime` keeps object-id and mechanism-handle
  indexes. Actor picks, object-to-mechanism activation, trigger-target resolution, and activation metadata capture can
  therefore route through stable indexes instead of scanning all objects or mechanisms by string/handle during
  interaction.
- Native DAT actor queries expose the actor membership view through the shared gameplay runtime. The first bridge
  returns stable actor counts, position/radius/height/visibility state, inspect display names, and radius queries using
  the actor view rather than scanning every MM9 object.
- Actor radius queries now use a load-time actor cell index in the MM9 object registry. Shared gameplay AI/combat
  callers collect nearby actor object candidates from spatial cells, then map object index to actor index through the
  registry table, so the path scales with local actors instead of all actors in the map.
- Actor line-of-sight filtering now uses the shared DAT world pick path with static world plus active transformed
  mechanism collision. Nearby actor queries therefore do not see through moving door/platform geometry while movement
  and interaction are using the same mechanism collision cache.
- Native DAT object picks that hit actor-classified objects now map to shared `GameplayWorldHitKind::Actor`; mechanism
  linked objects continue to map to event targets and route to the indexed mechanism command path.
- The native DAT gameplay bridge resolves mechanism handles, object handles, and actor object handles through the
  runtime's load-time handle indexes instead of assuming handles are contiguous `index + 1` values. This keeps
  script-visible handles stable if later save/load or imported object allocation changes handle numbering.
- The debug console now has a native MM9 DAT entry command, `mm9.dat.goto <map-id|map-stem>`, which selects only map
  metadata from `MapStats`, constructs `Mm9DatSceneRuntime`, and lets the native loader read `.level.yml` plus source
  DAT instead of loading generated compatibility scene/event/object sidecars as the world runtime source.
- Runtime `tp <x> <y> <z>` and debug-start overrides can route through the active `IGameplayWorldRuntime`, so native DAT
  party teleport and movement are reachable without an ODM/BLV party runtime. Native DAT teleport now uses DAT floor
  support snapping through the MM9 party runtime before storing the final party pose.
- Native DAT party input now receives the shared control-scheme context. Modern controls use left/right movement actions
  for strafing while relative mouse movement drives yaw/pitch; classic controls keep left/right as keyboard turn input.
  This feeds the native DAT forward/strafe/vertical movement axes before applying DAT collision movement, so
  debug-entered maps are navigable from the shared gameplay loop.
- `Mm9DatWorldGameplayRuntime::renderWorld` now owns the first live bgfx DAT world submission path. It creates static
  geometry buffers once, keeps moving mechanism geometry in dynamic buffers, loads DTX texture handles from the native
  runtime texture bindings, converts DAT `X/Z` horizontal plus `Y` vertical coordinates to OpenYAMM render coordinates,
  scales DAT pixel UVs by decoded texture dimensions, and submits section draw commands without walking raw DAT
  triangles per frame.
- Dynamic mechanism render upload refreshes only prepared dynamic mechanism vertices before updating the dynamic bgfx
  vertex buffer. The live scene runtime keeps a cached bgfx submit plan and dirty flag, so dynamic vertex uploads and
  submit-plan rebuilds happen only after mechanism commands or mechanism animation updates change prepared dynamic
  geometry. Static DAT geometry is not rebuilt when mechanisms move.
- `Mm9DatWorldGameplayRuntime` also owns the first native placed-object model submission path. It builds render
  instances once from `Mm9DatObjectPresentationWorld`, resolves source models through `models/model_registry.yml`, loads
  model assets and sidecars into a per-scene cache, converts MM9 DAT runtime positions from `X/Y-up/Z` into the renderer
  coordinate frame, caches DTX texture handles through the native runtime texture catalog, advances animation clips from
  the world update tick, and submits the cached draw items after world/mechanism geometry.
- `Mm9DatObjectModelRenderPlan` is the headless-verifiable bridge between DAT object presentation and live model
  drawing. Thjorgard and Thjorgard City smoke coverage now proves every planned render instance maps back to a parsed
  DAT scripted object, uses the same runtime-to-renderer axis conversion as the live scene, and resolves through the
  native MM9 model registry before bgfx rendering is involved.
- The same smoke coverage now loads every unique planned model asset and sidecar, initializes native model visuals, and
  verifies valid world bounds plus render-prep draw items before bgfx rendering. Static models with valid draw prep are
  kept renderable even when they do not select an animation clip.
- The model registry now carries explicit source model/skin aliases for known source-data holes such as Thjorgard's
  `Barrel02` reference, and the resolver accepts object-authored `Skin` overrides for static models instead of rejecting
  otherwise valid source-model matches. Sound-only DAT objects are kept out of model presentation.
- Native script IR, final asset package lookup, and richer binding heuristics still need follow-up work. Generated
  sidecars remain useful editor/import validation artifacts, but are not game-runtime dependencies.
- Full static-prop coverage is still follow-up: the first placed-object draw path reuses the existing MM9 animated model
  renderer, so source models that need a dedicated static GLB path can be resolved later without adding billboards or
  map-local sidecar dependencies.

## Non-Goals For This Slice

- Exact LithTech leaf-PVS or portal traversal.
- Final MM9 lightmap/lightgroup rendering.
- Exact skybox and weather presentation.
- Exact ocean physics/height semantics beyond rendering visible water and preserving water volumes for later queries.
- Full NPC AI parity.
- Billboard-based MM9 object/NPC presentation.
- Full save/load format finalization.
- Replacing shared MM6-MM8 indoor/outdoor runtimes.
- Removing generated ODM/BLV compatibility outputs from the toolchain.

## Architecture Target

Add MM9-specific runtime components under `game/mm9/*`:

- `Mm9DatWorldRuntime`: loaded map instance and coordinator for source DAT/native packaged assets, render, collision,
  mechanisms, objects, lights, and query services.
- `Mm9DatRenderWorld`: bgfx-facing render partitions, texture handles, material sections, bounds, and render stats.
- `Mm9DatCollisionWorld`: static DAT collision/query acceleration for physics/helper geometry plus transformed
  mechanism queries.
- `Mm9DatMechanismRuntime`: source-world-model mechanism instances, progress/state, transforms, bounds, trigger/use
  routing, and collision/render integration.
- `Mm9DatObjectRegistry`: stable handles, flags, typed views, and broadphase membership for actors, props, pickups,
  interactables, triggers, lights, and mechanisms.
- `Mm9DatObjectPresentationWorld`: load-time model/native presentation instances derived from the registry's renderable
  object view.
- `Mm9DatMovementController`: party movement and floor/support resolution using DAT collision queries.
- `Mm9DatWorldQueries`: common ray, floor, sweep, overlap, picking, LOS, and material/surface query API.

Names can change if the codebase suggests better ones, but the ownership split should stay.

## Milestone 1: Loader And Runtime Shell

Goal: load a native MM9 DAT level into a runtime object without switching through ODM world geometry.

Tasks:

- Resolve `.level.yml` by map id for at least `thjorgard` and `thjorgardcity`.
- Load source DAT through `Mm9DatWorld` and derive runtime geometry, model roles, object records, events/mechanisms,
  sounds, spawns, lights, and sky data from DAT/native packaged assets.
- Do not load generated sidecar YAMLs in the game runtime; expose needed DAT fields through native C++ parsing.
- Build stable source ids for world models, polygons, surfaces, objects, mechanisms, materials, and event bindings.
- Expose a debug/dev entry point to jump to a native DAT map.
- Bind native DAT dev-entry state to a gameplay-world runtime bridge so shared gameplay input can move the DAT party
  without going through ODM/BLV movement.
- Keep the derived ODM path available as fallback/reference, but do not use it for native runtime world geometry.

Acceptance:

- A native DAT dev-entry loader exists for `thjorgard` and `thjorgardcity`, resolves map id to `.level.yml`, loads DAT
  runtime state, and derives a floor-snapped start pose from DAT `StartPoint` records.
- A native DAT runtime object can be constructed for Thjorgard and Thjorgard City.
- Native DAT scene/runtime bridge exposes party pose, teleport, movement, use rays, and mechanism updates through the
  shared gameplay-world interface.
- `mm9.dat.goto` can enter the native DAT runtime path from the debug console without loading generated map sidecars as
  runtime world data.
- Diagnostics report source counts, DAT/native input usage, missing materials/assets, mechanism counts, object counts,
  and parser warnings.
- No per-frame work starts from YAML string lookups or source-name scans.
- Thjorgard and Thjorgard City runtime smoke tests prove DAT-derived light layers and sky model ownership are present
  without loading generated object sidecars.

## Milestone 2: Static World Rendering

Goal: render native DAT geometry through runtime-owned bgfx buffers.

Tasks:

- Build render partitions from `Mm9DatRenderMesh` and filter results.
- Group by source model, resolved material/DTX texture, opacity/blend state, and spatial chunk.
- Prepare render-ready vertex/index sections from grouped partitions at load time; dynamic mechanisms keep separate
  sections that can be updated in place.
- Decode/cache DTX textures once per source path.
- Split opaque and translucent/additive sections.
- Render visible water as visual geometry and preserve water-volume/helper geometry for debug/query layers.
- Provide placeholder sky behavior using `Mm9SkyLayer` data without blocking the first renderer on final skybox work.
- Add render stats for partitions, visible partitions, draw calls, submitted triangles, texture misses, and helper
  triangles skipped.

Acceptance:

- Thjorgard and Thjorgard City show source DAT terrain/world geometry, models, visible water/ocean, and material
  textures where resolved.
- Runtime stats expose visible-water triangle counts and water-volume/helper skip counts so the water render/query split
  is verifiable without relying on editor sidecars.
- Helper `PhysicsBSP`, `VisBSP`, rails, trigger volumes, and water volumes are hidden in normal rendering.
- Draw submission is grouped; there is no draw-per-polygon path.
- Static geometry does not rebuild per frame, and mechanism animation updates only prepared dynamic mechanism vertex
  ranges after the shared mechanism transform state changes.
- Placeholder sky metadata is available from DAT-derived sky objects/model roles even before final skybox rendering is
  wired to bgfx.
- Renderer-facing draw commands are section-based, expose draw-call/submitted-triangle/texture-miss stats, and can be
  culled by section bounds without a draw-per-polygon path.
- Prepared sections and draw commands carry stable runtime material ids, so future texture cache binding can use numeric
  ids instead of repeated material-key string lookups.
- Runtime texture lookup is backed by a load-time DTX catalog and material-id bindings from native source assets, not by
  map-local material sidecars.
- Upload planning keeps static world geometry in immutable buffers and dynamic mechanisms in updateable buffers.
- bgfx submission consumes the upload plan and runtime draw-command plan by section id/material id. It must not walk
  raw DAT triangles, rebuild section buffers, or resolve texture names during frame submission.
- First live bgfx submission is wired in `Mm9DatWorldGameplayRuntime::renderWorld`: static buffers/textures are created
  once, dynamic mechanism vertices refresh separately, and draw calls come from a cached
  `Mm9DatWorldRenderSubmitPlan`. The cached plan is rebuilt only when mechanism runtime state dirties dynamic geometry.

## Milestone 3: Object And Actor Placement

Goal: create a runtime object registry that preserves MM9 placement and supports later scripting/AI.

Tasks:

- Register raw/source objects with stable runtime handles.
- Bind DAT object placement/model presentation to scripted objects, using scene compatibility only as a temporary
  editor/import bridge.
- Split views for renderable, collidable, ray-hit, trigger, interactable, actor, prop, pickup, light, and mechanism
  membership.
- Build a load-time object presentation plan from the renderable registry view. It should expose stable object handles,
  source object ids, model/source asset keys, presentation kind, position/bounds, and render stats without keeping an
  MM9 billboard fallback.
- Implement one-shot startup floor placement using parsed `MoveToFloor` and class policy.
- Preserve authored positions when `MoveToFloor` is disabled or the class is a helper/mechanism/sky/water/trigger.
- Use a downward DAT collision support query for floor placement and record placement diagnostics.
- Place NPCs/objects above floor only when authored or explicitly unsupported; do not globally clamp all objects.

Acceptance:

- Objects and NPCs are registered from DAT object data, not from hand-authored map exceptions or `.raw_objects.yml`.
- Renderable objects are exposed through a model/native presentation plan rather than MM9 billboard metadata.
- `MoveToFloor=true` objects snap once to DAT support geometry with a small height bias.
- `MoveToFloor=false` objects keep authored placement.
- Diagnostics expose snapped, unsnapped, unsupported, and policy-skipped objects.
- Runtime object category views are built once at load time and expose counts/indices for render, collision,
  interaction, trigger, actor, prop, pickup, light, mechanism-linked, and ticking ownership.
- Solid/collidable objects are indexed into movement-query cells and can block native DAT party movement through the
  same MM9-scoped runtime path.
- Actor lookup from a picked object handle is O(1) through the registry object-to-actor table.
- Object presentation stats match the renderable registry view and expose actor/prop/mechanism/model-asset/source-model
  counts for Thjorgard and Thjorgard City smoke coverage.
- The live DAT scene runtime consumes that presentation world for placed model rendering, not a per-frame object scan.
  Renderable model assets are resolved once through the MM9 model registry and cached per scene.
- Real-map coverage for Thjorgard and Thjorgard City proves the model render plan has no missing scripted-object
  backrefs and no unresolved model registry entries for planned draw instances.
- Real-map coverage also proves planned model draw instances load model assets/sidecars and produce render-prep draw
  items, so static models are not silently dropped just because they do not have an active animation clip.

## Milestone 4: Static Collision And Party Movement

Goal: move the party through the DAT world using native collision data.

Tasks:

- Build `Mm9DatCollisionWorld` from `Mm9DatPhysicsQueryView`.
- Add spatial acceleration for triangle queries, starting with a simple grid or BVH.
- Implement downward floor/support queries, wall raycasts, actor hull sweeps, slide response, and step handling.
- Preserve source model/poly/surface/material ids in collision results.
- Integrate party position, velocity, gravity, floor support, and input movement with DAT collision queries.
- Add debug start/teleport placement using level start/spawn objects when available.

Acceptance:

- First native movement helper exists for floor snap plus wall block/slide, with source hit ids and candidate/tested
  triangle counts from spatial-cell collision queries.
- Party movement works in Thjorgard and Thjorgard City without falling through the world.
- Walls and floors collide with the rendered layout closely enough for normal navigation.
- Native DAT party movement applies falling gravity while airborne, resets downward velocity after floor support, and
  uses the same DAT movement/floor query after jump requests.
- Static DAT party movement can step over low blocking collision when a raised trace clears and floor support is found
  within the configured step height.
- Collision query cost scales with spatial candidates, not all DAT triangles.
- Debug output can show current floor support, hit normal, source model/poly, and collision channel.
- Runtime/debug teleport snaps to DAT floor support when available and keeps the final party pose in the native DAT
  collision coordinate domain.
- Runtime/debug teleport uses the same static-plus-mechanism floor support path as party movement, so debug placement
  can land on an active moving platform and seed later moving-floor carry.
- Thjorgard/Thjorgard City smoke coverage initializes party state from DAT `StartPoint` objects and verifies a native
  movement tick remains grounded through real DAT floor-support candidates.

## Milestone 5: Mechanism Runtime

Goal: make doors/platforms/mechanisms render, collide, and route interaction through native DAT runtime state.

Tasks:

- Build mechanism instances from MM9 events and binding targets.
- Resolve source world-model targets and classify active/previewable versus inert mechanisms.
- Implement linear and rotating mechanism transforms using the same coordinate conversion as the editor preview path.
- Draw moving source-model batches with instance transforms instead of rebuilding render buffers.
- Query moving mechanism collision by transforming queries into local space or by using a cached transformed collision
  representation only when needed.
- Update broadphase bounds when mechanism transforms change.
- Add trigger/use/open/close/toggle handling and route callbacks through the MM9 event/script runtime.
- Track standing-on/carrying behavior enough that party movement does not desync from moving floors.

Acceptance:

- Native command/update state exists for open/close/toggle, progress, current bounds, lock/inert handling, and moving
  mechanism update queues.
- Mechanism update honors authored move delays, open wait time, and lock-on-close without scanning inactive
  mechanisms.
- Mechanism instances preserve DAT-derived trigger outputs and authored sound names for activation/script routing.
- Runtime-aware party movement can collide with transformed mechanism triangles and report mechanism
  handle/object/source ids for the blocking hit.
- Runtime-aware party movement can snap floor support to transformed mechanism triangles and report mechanism
  handle/object/source ids for the support hit.
- Runtime-aware party movement can carry the party on a moving mechanism floor by remembering only the support
  mechanism handle/progress and applying the shared mechanism transform delta after the mechanism update.
- Runtime-aware party movement can open DAT mechanisms marked as push/touch/reopen-on-contact when contact collision
  occurs, without scanning all mechanisms or re-picking the interaction ray.
- Mechanism carry, mechanism render batches, and transformed collision batches share the same point/triangle transform
  implementation instead of duplicating axis conversion or rotation order in the movement controller.
- Active mechanism source models are excluded from static render/collision partitions and exposed as dynamic render
  batches that track mechanism motion/current bounds.
- Known Thjorgard/Thjorgard City mechanism targets can be activated from debug/use interaction.
- Thjorgard/Thjorgard City activation is covered through native DAT use rays against real active mechanism bounds.
- Rendered mechanism transform and collision transform match.
- Inert or unresolved mechanisms remain visible in diagnostics and are not silently dropped.
- Mechanism update cost scales with moved mechanisms, not all world models.
- Mechanism movement and interaction queries use bounds-index candidates instead of scanning every active mechanism.
- Mechanism collision queries use cached transformed source-model triangles that refresh only for mechanisms whose
  transforms changed, and candidate collision-batch lookup is indexed by mechanism handle.
- Moving-floor carry is O(1) for the currently supported mechanism and does not scan all active mechanisms.

## Milestone 6: Interaction And Query Routing

Goal: make runtime interaction use stable handles and one authoritative DAT query service.

Tasks:

- Implement picking/raycast from camera or interaction ray into DAT world and object registry.
- Return source object handle, mechanism id, source model/poly, material/surface, normal, and hit position.
- Route object use, touch, trigger, and mechanism commands through the MM9 object/script dispatch model.
- Wire common script queries such as clear-shot, target checks, object lookups, and trigger callbacks to
  `Mm9DatWorldQueries`.
- Keep direct object fields and routed subclass behavior aligned with `MM9_SCRIPT_OBJECT_HANDLE_DIRECT_VS_ROUTED.md`.

Acceptance:

- First native query helper exists for world/object/mechanism picking, object-id mechanism command routing, stable
  handles, source model/poly/surface ids for world hits, and object broadphase candidate diagnostics.
- Runtime use/update helpers can pick a mechanism from an interaction ray, issue an open/close/toggle command, advance
  mechanism state, and synchronize dynamic mechanism render batch transforms.
- The native scene runtime maps DAT picks into shared gameplay hits, exposes mechanism/object MM9 metadata to context
  action and Lua-facing routing, and activates the already-selected stable handle/object id without a second pick.
- Runtime use results expose picked object/script metadata and linked mechanism trigger/sound metadata from native DAT
  parser output, giving the future script bridge a sidecar-free dispatch envelope.
- Trigger outputs selected by the applied open/close/use phase are resolved to target handles through the MM9 object
  registry and recorded with unresolved/ambiguous diagnostics when a DAT target name cannot be mapped uniquely yet.
- Native DAT scene activation records resolved trigger dispatches into `Mm9ScriptRuntimeState`, preserving map id,
  source object index, script source, target handle, and message for later script runtime consumption/save persistence.
- Package-backed native DAT scene activation dispatches those triggers through `Mm9ScriptRuntime` from the source object
  context when the package is available, so registered target callbacks can execute through the shared MM9 script path.
- The activating object's own `OnUse` script can run through `Mm9ScriptRuntime::runLabelForObject`, preserving owner
  context and session script state instead of treating mechanism motion as the only activation side effect.
- Interact/use can hit static world-linked mechanisms and placed objects.
- Actor-classified object picks are exposed as shared actor hits, while mechanism-linked object picks remain routed
  event targets.
- Script-visible object handles remain stable and route to the right runtime owner.
- Gameplay and interaction raycasts agree on collision domain unless a debug/render-only query was explicitly requested.

## Milestone 7: Diagnostics, Tests, And Performance Gates

Goal: make regressions obvious before the runtime is expanded to all MM9 maps.

Tasks:

- Add focused tests for runtime load, render partition build, collision floor query, movement sweep, object
  `MoveToFloor`, mechanism transform, and mechanism source-target resolution.
- Add Thjorgard/Thjorgard City smoke tests for native DAT world construction and source id consistency.
- Add diagnostics for render partitions, draw calls, triangles submitted, collision queries, broadphase candidates,
  active/inert mechanisms, floor-placement results, and texture cache misses.
- Add debug overlays or textual dumps for collision triangles, render bounds, object broadphase, mechanism axes/AABBs,
  ray hits, support floor, and helper geometry subsets.

Acceptance:

- `cmake --build build --target openyamm -j25` succeeds after implementation.
- Focused tests cover the new pure logic and headless runtime build paths.
- Runtime stats prove there are no all-triangle/all-object hot scans in normal movement, rendering, interaction, or
  mechanism updates. Mechanism bounds-index and collision-cache stats expose indexed mechanism counts, cell counts, cell
  refs, collision batches, indexed collision batches, and transformed collision triangles. Render submission stats
  expose visible sections, draw calls, submitted triangles, texture misses, runtime material counts, missing material
  counts, and texture-cache-eligible material counts. Object stats expose collidable-object cell counts and refs for
  movement collision plus actor cell counts and refs for nearby actor queries.
- Interaction hot paths resolve objects, target names, and mechanisms through load-time id/name/handle indexes before
  capturing activation metadata, producing trigger dispatches, or issuing commands; they do not scan the full
  object/mechanism arrays on each use.

## Performance Guardrails

- No per-frame all-polygon scans.
- No per-frame all-object string lookup.
- No MM9 billboard presentation path or scripted-billboard asset lookup under `game/mm9/*`.
- No per-frame object presentation classification; placed-object render input comes from the load-time presentation
  world.
- No per-frame placed-model asset, sidecar, or DTX reload; model assets and texture handles are cached by the native DAT
  scene runtime.
- No per-frame all-object scan for movement collision against solid DAT objects; object movement collision uses the
  load-time collidable object cell index.
- No per-interaction all-object/all-mechanism scans for object-id or mechanism-handle routing.
- No gameplay bridge assumption that object or mechanism handles are equal to vector index plus one; use runtime
  handle indexes for stable handle routing.
- No per-interaction all-object scans for DAT trigger target-name resolution.
- No all-actor scan for shared nearby-actor queries; use the MM9 object registry actor cell index and object-to-actor
  table.
- Actor line-of-sight queries include active mechanism collision through the shared DAT pick/query path instead of
  checking only static world triangles.
- No draw-per-polygon static rendering.
- No full static buffer rebuild for moving mechanisms.
- No per-frame dynamic mechanism buffer upload when no mechanism transform changed.
- No per-frame render submit-plan rebuild when the DAT runtime render sections are unchanged.
- No per-frame raw DAT triangle walk for already-prepared static render geometry.
- No per-frame all-mechanism scan for party carry; support carry uses the remembered mechanism handle and progress.
- Runtime rendering works from prepared section draw commands, not raw DAT polygon iteration.
- Runtime material lookup works from stable material ids prepared at load time, not sidecar scans or per-frame material
  string lookup.
- No duplicate transform authority between rendering and collision.
- No silent dropping of visible objects, collision candidates, or mechanism targets.
- No global floor clamp over all MM9 objects.
- DTX textures and material assignments are cached by resolved source path/material id.
- DTX path resolution happens once through a runtime texture catalog; draw submission should use material ids and cached
  bindings instead of filesystem scans.
- Static world geometry uses immutable buffers after load.
- Moving mechanisms update transforms, inverse transforms, bounds, and broadphase membership.
- Collision, movement, picking, scripts, and AI use one DAT query service.

## First Playable Slice Done Criteria

- Debug/dev map entry can load native DAT `thjorgard` and `thjorgardcity`.
- Source DAT world geometry renders with resolved textures where available.
- Visible ocean/water renders as visual geometry; water volumes remain query/debug data.
- Placeholder sky behavior is present and does not break geometry rendering.
- Party movement and collision work against DAT physics/helper geometry.
- Objects/NPCs are registered and placed from MM9 data with LithTech-style `MoveToFloor` policy.
- Renderable objects/NPCs have a load-time model/native presentation plan and first native model draw submission path.
- Doors/mechanisms can be triggered/opened/closed/interacted with and have matching render/collision transforms.
- Runtime data lives primarily under `game/mm9/*` with only narrow shared-engine hooks.
- Generated ODM compatibility remains available for comparison but is no longer the active geometry source for this
  native runtime path.
