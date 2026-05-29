# MM9 DAT Physics Query Independent Goal

Status: implemented on 2026-05-27 for the collision/query foundation work that can be done before the playable DAT
world view is complete.

## Objective

Implement the source-preserving MM9 DAT physics/query foundation under `game/mm9/*`, with focused unit tests, so future
`DatWorldView`, `Mm9DatLevelRuntime`, movement, projectiles, AI line-of-sight, and editor diagnostics can consume the
same channel-aware collision facts without reparsing or reclassifying DAT geometry.

This goal intentionally does not implement full party movement, live DAT world loading, spatial acceleration tuned for
real maps, actors, projectiles, trigger dispatch, or moving platform carry behavior.

## Read First

- [MM9_DAT_FORMAT_NOTES.md](MM9_DAT_FORMAT_NOTES.md): byte-level DAT parser authority.
- [MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md](MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md): DAT/DTX runtime
  preservation rules and LithTech semantic references.
- [MM9_DAT_PHYSICS_COLLISION_CONTRACT.md](MM9_DAT_PHYSICS_COLLISION_CONTRACT.md): target physics, collision, movement,
  contact, and runtime integration contract.
- [MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md](MM9_SCRIPT_LUA_RUNTIME_COMMAND_INVENTORY.md): movement command and
  callback requirements that future DAT physics must satisfy.

Local LithTech references to consult for semantics only:

- `mm9/lithtech/sdk/inc/iltserver.h`: `IntersectSegment`, `CastRay`, `MoveObject`, `GetStandingOn`, and
  `GetLastCollision`.
- `mm9/lithtech/sdk/inc/ltbasedefs.h`: `CollisionInfo`, `IntersectInfo`, object flags, stair-step, no-sliding,
  point-collide, and player-cylinder flags.
- `mm9/lithtech/runtime/shared/src/collision.cpp`: player collision, stair-step, blocker, and standing semantics.
- `mm9/lithtech/runtime/shared/src/moveobject.cpp`: object movement, standing-object carry, and collision callbacks.
- `mm9/lithtech/runtime/world/src/fullintersectline.cpp`: intersection result and surface/user flag reporting.

Do not copy LithTech source code into OpenYAMM. Use it only to understand behavior and data shape.

## Current Baseline

Already present:

- `Mm9DatWorld` parses source world models, surfaces, polygons, planes, leaves, nodes, user portals, and PBlock summary.
- `Mm9DatRenderTriangle` preserves source model, polygon, surface, texture ids, source model/texture names, DAT surface
  flags, and DTX texture flags.
- `buildMm9DatRenderMesh` triangulates DAT polygons while keeping source ids.
- `pickMm9DatRenderMesh` performs source-id-preserving ray picking, but it is render-mesh oriented and not
  channel-aware.
- `classifyMm9DatRenderMeshFilters` classifies triangles as visual, invisible, sky, water, helper, physics, visibility,
  trigger, terrain, and movable using model roles plus DAT surface flags.
- Existing tests cover source id preservation, pick source ids, DAT surface flag constants, and real helper geometry
  classification.

This goal should build on those APIs rather than replacing them.

## Scope

Implement now:

- A pure `game/mm9` DAT physics/query layer over `Mm9DatRenderMesh` plus `Mm9DatRenderFilterResult`.
- Channel-aware raycast and segment queries.
- Source-preserving hit/contact result structs.
- Query channel masks for visible art, physics, visibility, trigger/volume, water, sky, movable, and debug helper
  geometry.
- Separation of DAT surface flags and DTX texture/user flags in all query results.
- Triangle normal and plane-distance reporting for ray hits.
- Deterministic tie-breaking when multiple triangles hit at the same distance.
- A small diagnostic/stat struct reporting channel counts and missing authoritative physics geometry.
- A pure movement math helper for plane projection/sliding only if it can be kept independent from runtime state.
- Unit tests using synthetic meshes first, with one or more real DAT-backed tests where existing test helpers already
  make that cheap.

Defer:

- Final `DatWorldView` class ownership.
- Full `IGameplayWorldRuntime` integration.
- Full party movement and gravity.
- Stair-step resolver integration with real map geometry.
- Actor/object/projectile runtime movement.
- Trigger, water, ladder, and touch callback dispatch.
- Dynamic world-model transform proxies beyond isolated math/prototype tests.
- Optimized spatial acceleration. A linear scan is acceptable for the first query layer if the API leaves room for an
  index later.
- Any fallback that makes generated ODM/BLV compatibility geometry authoritative for MM9.

## Architecture

Keep this work MM9-specific for now.

The API should be small and direct:

- `Mm9DatWorld` remains the lossless parsed source.
- `Mm9DatRenderMesh` remains the existing source-preserving triangle projection.
- `Mm9DatRenderFilterResult` remains the existing role/channel classification input.
- The new query layer should not depend on editor, renderer, scenario, or MM6-MM8 world code.
- Runtime-facing result structs should preserve enough facts to later produce equivalents of LithTech `CollisionInfo`,
  LithTech `IntersectInfo`, `GameplayWorldHit`, projectile hit facts, and editor/debug inspection facts.

Prefer a construction shape like:

```cpp
Mm9DatPhysicsQueryView queryView = buildMm9DatPhysicsQueryView(mesh, filters);
std::optional<Mm9DatPhysicsRayHit> hit = raycastMm9DatPhysicsQueryView(queryView, ray, options);
```

Exact naming can change to match local style, but the layer should be plain data plus functions unless a class is
clearly more maintainable.

## Proposed Files

Expected new files:

- `game/mm9/Mm9DatPhysicsQuery.h`
- `game/mm9/Mm9DatPhysicsQuery.cpp`
- `tests/Mm9DatPhysicsQueryTests.cpp`

Use a different name only if the repository gains a clearer MM9 collision naming convention before implementation.

## Query Data Requirements

Define query channel flags covering:

- visible geometry;
- physics geometry;
- visibility geometry;
- trigger/volume geometry;
- water geometry;
- sky geometry;
- movable geometry;
- helper/debug geometry.

Define a source reference struct containing:

- query triangle index;
- render mesh triangle index;
- source model index;
- source model name;
- source polygon index;
- source surface index;
- source texture index;
- source texture path/name;
- DAT surface flags;
- DTX texture/user flags;
- render/query channel flags.

Define ray/segment hit structs containing:

- `hit` or optional presence;
- hit point;
- hit normal;
- plane distance;
- distance along query;
- barycentric coordinates if useful for diagnostics;
- source reference;
- channel flags.

Keep DAT surface flags and DTX texture flags separate. Do not collapse them into one "surface flags" field.

## Raycast And Segment Requirements

- Normalize query direction internally.
- Reject zero-length directions.
- Support finite segments by max distance.
- Support rays by infinite or explicit max distance.
- Support optional backface inclusion.
- Filter triangles by channel mask before intersection.
- Return the nearest accepted hit.
- Preserve source ids exactly from the underlying `Mm9DatRenderTriangle`.
- Report normals consistently with the emitted triangle winding.
- Report plane distance using the same coordinate space as the hit point and normal.
- Do not infer collision from UVs or texture names.
- Do not silently fall back from missing physics channels to visible geometry unless the caller explicitly asks for a
  visible/debug channel.

## Diagnostics Requirements

Expose a small stats/diagnostic result:

- total triangles;
- per-channel triangle counts;
- unclassified triangle count;
- whether any physics channel triangles exist;
- whether any visibility channel triangles exist;
- source model count when available;
- warnings for a physics query view with no physics geometry.

Diagnostics should be available to tests/editor/debugging but quiet by default.

## Optional Pure Movement Kernel

Only implement this in the same goal if the query layer lands cleanly first.

Allowed now:

- plane projection helper for sliding velocity along a hit normal;
- deterministic earliest-contact selection from a list of abstract contacts;
- small source-preserving support/standing result structs;
- unit tests against synthetic contacts and planes.

Do not implement full party movement in this goal. Real movement needs live DAT world state, dynamic object flags,
gravity/flying inputs, actor/object colliders, and future `DatWorldView` ownership.

## Tests

Unit tests should not require the full DAT runtime.

Synthetic query tests:

- Query view preserves one triangle's source model/poly/surface/texture ids.
- Physics-channel raycast ignores visible-only triangles.
- Visible-channel raycast ignores physics-only triangles when requested.
- Combined-channel raycast returns the nearest accepted hit.
- Backface-disabled raycast rejects a backface hit.
- Segment query respects max distance.
- Hit result reports DAT surface flags and DTX texture flags separately.
- Hit result reports a finite normal, point, plane distance, and distance.
- Zero direction returns no hit.
- Missing physics channel produces explicit diagnostics but no automatic visible fallback.
- Deterministic tie-breaking chooses the lower render triangle index for equal-distance hits.

Real DAT-backed tests where practical:

- `thjorgard` or another existing fixture builds a query view with nonzero physics and visibility channel counts.
- A ray against a selected `PhysicsBSP` triangle returns that triangle's source ids through the physics channel.
- A ray against a selected visible triangle can be limited to the visible channel and does not require physics fallback.

Optional pure movement tests:

- Projecting velocity along a vertical wall removes only the velocity into the wall.
- Projecting against a floor does not corrupt horizontal movement.
- Earliest-contact selection keeps source ids from the earliest contact.
- `SURF_NOTASTEP` is visible on the selected support/contact result for future stair-step logic.

## Build And Verification

Use focused unit coverage first:

```bash
cmake --build build --target openyamm_unit_tests/fast -j25
./build/tests/openyamm_unit_tests --test-case="MM9 DAT physics query*" --success=false
```

If CMake metadata changes or the focused test target does not include the new files, run the normal project build when
the worktree is not broken by unrelated sessions:

```bash
cmake --build build --target openyamm -j25
```

Other Codex sessions may be changing the tree. If broad builds fail due to unrelated files, do not fix those changes.
Report the unrelated blocker and keep the focused test results.

## Acceptance Criteria

- [x] New query APIs compile under `game/mm9`.
- [x] The query layer has no editor, renderer, scenario, MM6-MM8 indoor, or MM6-MM8 outdoor dependency.
- [x] Raycast and segment queries are channel-aware.
- [x] Hit results preserve DAT source ids, DAT surface flags, and DTX texture flags.
- [x] Physics queries never silently fall back to visible geometry.
- [x] Tests cover synthetic channel filtering, source preservation, normal/plane reporting, and max-distance behavior.
- [x] At least one real DAT-backed test verifies physics/visibility helper geometry can feed the query layer.
- [x] Existing `Mm9DatWorld` parser/render mesh behavior remains source-preserving.
- [x] No generated Lua, generated YAML, raw DAT source, or `mm9/source/*` file is hand-edited.

Implementation evidence:

- `game/mm9/Mm9DatPhysicsQuery.h`
- `game/mm9/Mm9DatPhysicsQuery.cpp`
- `tests/Mm9DatPhysicsQueryTests.cpp`
- `cmake --build build --target openyamm_unit_tests/fast -j25`
- `./build/tests/openyamm_unit_tests --test-case="MM9 DAT physics query*" --success=false`
- `cmake --build build --target openyamm -j25`

## Follow-Up Goals

After this query layer exists:

- Add `DatWorldView` ownership/caching for static query views.
- Add a spatial index without changing query result semantics.
- Add transformed dynamic proxies for movable world models and mechanisms.
- Implement static `PhysicsBSP` party-cylinder sweep, sliding, standing surface query, and `SURF_NOTASTEP` stair-step
  behavior.
- Route MM9 projectile impacts, AI line-of-sight, object movement callbacks, and editor collision overlays through the
  same query services.
