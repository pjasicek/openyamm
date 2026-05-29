# Indoor Portal Graph Vertical Slices Plan

This is the implementation tracker for the indoor sector/portal rendering refactor.

Comprehensive architecture and acceptance criteria live in:

- `openyamm_sector_portal_collision_rendering_spec.md`

This plan exists so the work can be resumed safely after context refreshes without re-deriving the sequence.

## Current Test Fixtures

Editor-authored room snapshots are available under:

- `tests/indoor_geometry/6d01.yml`
- `tests/indoor_geometry/cd2.yml`

These snapshots are treated as the first ground-truth fixtures for the runtime portal graph. They were produced from
the editor's Room / Portal inspector, so they encode the same source model as the editor's "Connected Rooms" view:

- room id
- connected rooms
- assigned portal faces
- portal face endpoints (`roomNumber`, `roomBehindNumber`)
- direct door/mechanism links from `MapDeltaDoor::faceIds`
- room decoration ids
- room light ids
- room actor ids
- room sprite object ids

## Design Decisions Already Made

- `IndoorSector::portalFaceIds` is the source of truth for sector connectivity.
- Do not derive adjacency from arbitrary `sector.faceIds`.
- Each validated portal face becomes one bidirectional portal link.
- A portal belongs logically to both connected sectors.
- Runtime connected-sector diagnostics should match the editor's connected-room output for validated portals.
- Door blockers are explicit links from portal face to `MapDeltaDoor::doorId`, primarily through `MapDeltaDoor::faceIds`.
- Door/portal bounds overlap is diagnostic only unless explicitly migrated into a validated link.
- Visibility blocker rule is simple:
  - `Closed` blocks traversal.
  - `Open`, `Opening`, and `Closing` allow traversal.
- No generic orphan-sector root-frustum fallback for render visibility.
- Invalid or unknown sector ownership must not silently become sector `0`.

## Slice 1: Fixture Loader and Baseline Tests

Status: completed.

Goal: prove we can consume the editor snapshots in automated tests.

Tasks:

- Add a small parser for `tests/indoor_geometry/*.yml` snapshots.
- Load `6d01.yml` and `cd2.yml` in headless/editor diagnostics.
- Assert snapshot structure is valid:
  - map name present
  - room id present
  - connected rooms present
  - portal entries have face id, room, behind room, connected room
  - object lists parse
- Keep this parser test-only unless the runtime needs it later.

Acceptance:

- Headless/editor test target fails if either fixture is malformed.
- No runtime behavior changes.

## Slice 2: Runtime IndoorPortalGraph Builder

Status: completed for the first runtime graph builder. Not yet wired into rendering.

Goal: build the authoritative runtime graph beside current rendering, without changing rendering yet.

Proposed files:

- `game/indoor/IndoorPortalGraph.h`
- `game/indoor/IndoorPortalGraph.cpp`

Core data:

```cpp
struct IndoorPortalLink
{
    uint16_t faceId;
    uint16_t sectorA;
    uint16_t sectorB;
    std::vector<uint32_t> blockingDoorIds;
};

struct IndoorSectorPortalCache
{
    uint16_t sectorId;
    std::vector<uint16_t> portalLinkIds;
    std::vector<uint16_t> connectedSectorIds;
};

struct IndoorPortalGraph
{
    std::vector<IndoorSectorPortalCache> sectors;
    std::vector<IndoorPortalLink> portals;
    std::vector<IndoorPortalGraphDiagnostic> diagnostics;
};
```

Tasks:

- Validate portal face ids from `IndoorSector::portalFaceIds`.
- Accept only faces marked portal by source/effective attributes.
- Require valid, distinct `roomNumber` and `roomBehindNumber`.
- Reject default/stale sector `0` links unless the face is truly a valid portal to sector `0`.
- Canonicalize each valid portal face into one link.
- Attach the link to both connected sectors.
- Build connected-sector lists from canonical links only.
- Attach direct blockers by matching `MapDeltaDoor::faceIds` against portal face ids.
- Emit diagnostics for rejected portals, one-sided listings, suspicious sector `0` links, and overlap-only doors.

Acceptance:

- Builder runs on loaded indoor maps.
- No rendering changes.
- Diagnostics are available to tests and debug logging.

## Slice 3: Snapshot-vs-Graph Tests

Status: completed for `6d01.yml` and `cd2.yml`.

Goal: prove the runtime graph matches editor-authored ground truth.

Tasks:

- For each snapshot document in `6d01.yml` and `cd2.yml`:
  - load the referenced map
  - build `IndoorPortalGraph`
  - find the snapshot room
  - compare connected rooms
  - compare assigned/canonical portal faces
  - compare portal endpoints
  - compare direct blocking door ids where present
- Add explicit tests for:
  - no arbitrary `sector.faceIds` adjacency
  - no enclosed-room adjacency to sector `0`
  - no duplicate portal links for the same face

Acceptance:

- Fixtures pass against the graph.
- A broken `roomBehindNumber == 0` adjacency fails the tests.

## Slice 4: Replace Neighbor Graph Users

Status: completed.

Goal: remove the current bogus adjacency path before changing portal visibility.

Tasks:

- Replace `buildNeighboringIndoorSectorIds()` usage with the validated graph where needed.
- Remove or restrict helper logic that walks `sector.faceIds` for adjacency.
- Keep movement/collision support-face logic intact unless it truly depends on sector adjacency.
- Update diagnostics to print graph-derived adjacent sectors.

Implementation notes:

- `buildNeighboringIndoorSectorIds()` now delegates to `IndoorPortalGraph`, preserving the existing self+neighbor shape
  for callers while removing arbitrary `sector.faceIds` adjacency.
- `IndoorRenderer` stores a map-load `IndoorPortalGraph` and uses it for visibility diagnostics adjacency.
- Movement support-face caching still uses the helper, so it now receives graph-derived adjacent sectors without a
  separate rendering-specific path.

Acceptance:

- Logs no longer show enclosed sectors adjacent to sector `0` unless the validated graph says so.
- Existing build and current indoor playtest still work.

## Slice 5: Portal Visibility Traversal Uses Graph

Status: completed for sector traversal and explicit door blockers.

Goal: make render-visible sectors come only from validated graph traversal.

Tasks:

- Change indoor portal traversal to iterate graph portal links for the current sector.
- Use `IndoorPortalLink::faceId` for portal polygon/frustum clipping.
- Traverse to the opposite sector from the graph link.
- Apply direct blocking door state:
  - `Closed` blocks
  - `Open`, `Opening`, `Closing` traverse
- Remove broad whole-map door overlap from the production traversal path.
- Remove generic no-portal orphan-sector render visibility fallback.
- Keep diagnostics for rejected portals and orphan/special sectors.

Implementation notes:

- `IndoorPortalVisibilityInput` accepts an optional prebuilt `IndoorPortalGraph`.
- Runtime rendering passes the renderer's map-load graph into visibility traversal.
- Unit tests now assert that missing portal-list entries and unlinked frustum-visible sectors do not silently render.
- `orphanVisibleSectorCount` is retained as a result field for compatibility, but the production fallback is removed.
- Portal traversal now evaluates portal polygon/frustum visibility before applying the closed-door blocker gate, so a
  `blocked_by_closed_door` trace means the portal was otherwise visible through the current view frustum.
- Portal traces include linked blocker door ids, resolved mechanism states, and whether each linked door blocked the
  portal. This keeps `Open`, `Opening`, and `Closing` visible while making false blocker links diagnosable.
- Closed-door blocker candidates are additionally tested against current door geometry before they block traversal. The
  graph link is treated as a candidate list; the blocker only applies when closed door faces actually occlude the
  camera-to-portal segment for the visible portal aperture.
- Unlinked closed door geometry is also allowed to block traversal when a solid door face physically occludes the
  camera-to-portal segment. Portal aperture faces inside door face lists are skipped as blockers so door metadata cannot
  turn another portal into a false wall.
- Recursive traversal treats portal faces as two-sided apertures. Face winding no longer rejects depth-1+ portal
  traversal; portals are only direction-rejected when the aperture centroid is actually behind the camera.
- Accepted portal nodes carry the door ids associated with the crossed portal path. Those crossed doors are ignored by
  descendant portal occlusion checks so an accepted entry-door mechanism cannot re-block deeper rooms from the same
  visibility path.

Remaining follow-up:

- Add targeted headless/playtest coverage for known moving-platform/special-sector maps if a fixture shows a legitimate
  non-portal render island that must remain visible.

Acceptance:

- Enclosed rooms see only themselves.
- Sector `0` pollution does not appear.
- Distant no-portal sectors do not become visible through walls.
- Known open portal paths still render adjacent geometry.

## Slice 6: Visible Sector Instances and Object Submission

Status: completed for render visibility frustums and billboard/light submission gating.

Goal: fix torch/sprite/decor leakage by using clipped sector frustums, not just sector ids.

Tasks:

- Preserve visible sector instances with clipped frustums.
- Build `sector -> visible frustums` each frame.
- Submit decorations, sprite objects, actors, lights, and static billboards only when:
  - render membership sector is visible
  - object bounds intersect at least one clipped frustum for that sector
  - normal hidden/frame/texture checks pass
- Record diagnostics after actual submission, not just sector eligibility.

Implementation notes:

- `IndoorPortalVisibilityResult` now preserves `frustumsBySector`.
- `IndoorRenderer` caches the render visibility frustums next to the sector mask.
- Decoration billboards, runtime actor billboards, static/runtime sprite-object billboards, projectile billboards, FX
  lights, static BLV lights, and decoration lights are rejected when their sphere does not intersect any clipped
  frustum for the owning sector.
- Unit coverage verifies portal-reached sectors retain clipped frustums and reject objects outside the portal window.
- Unit coverage verifies static lights in a visible sector are still culled by the clipped sector frustum.

Remaining follow-up:

- Diagnostics still need to be moved from sector-eligible counts to submitted/rejected counts gathered by the actual
  render loops.

Acceptance:

- No torches/decorations render over black void from portal-reached sectors.
- Diagnostics distinguish loaded, sector-owned, visible, submitted, and rejected.
- Hidden dungeon population does not materially affect indoor frame time.

## Slice 7: Render Membership Cache

Status: partially complete.

Goal: avoid whole-map object scans in hot render paths.

Tasks:

- Build map-load membership:
  - sector id -> static decoration ids
  - sector id -> static sprite/object ids
  - sector id -> static light ids
  - sector id -> mechanism render object ids
- Dynamic actors/items/projectiles update render memberships when moving or changing sector.
- Invalid sector ownership logs a recovery/uncullable reason and does not become sector `0`.

Implementation notes:

- `IndoorRenderer` now builds map-load memberships for static decoration billboards and static sprite-object billboards.
- Static decoration and static sprite-object render paths iterate visible sector memberships instead of scanning the
  whole static billboard list.
- Runtime actor and runtime sprite-object builders now early-reject non-visible sectors before expensive sprite/frame
  resolution in render paths.
- Static light cache already has sector membership; it now additionally applies clipped frustum gating during frame
  light construction.

Remaining follow-up:

- Runtime actors/items/projectiles still need persistent sector membership buckets instead of per-frame linear scans with
  early rejection.
- Mechanism render object membership needs explicit ownership if moving mechanism geometry remains a measurable cost.
- Invalid sector ownership should be counted and logged through the final debug UX, not silently skipped.

Acceptance:

- Rendering loops over visible sector memberships, not all map objects.
- Fixture object lists line up with initial memberships where applicable.

## Slice 8: Sticky Seen-Sector Activation for AI and Collision

Status: completed for runtime actor AI, projectile actor broadphase, and movement collider broadphase.

Goal: hidden indoor population should not consume AI/collision work before the party has actually entered the owning
sector or clearly exposed that sector through an on-screen, unblocked portal.

Behavior:

- `IndoorWorldRuntime` owns a sticky per-sector activation mask.
- On map load, restore, and actor-AI update, the runtime activates:
  - the party foot sector
  - the party eye sector
- Immediately after indoor render, the runtime also activates sectors returned by `visibleIndoorMapRevealSectorIds()`;
  this is intentionally stricter than `render_visible`, uses accepted render portal traces with on-screen, unblocked
  portal faces, and is throttled to 10 Hz.
- Once a sector is activated, it remains activated for the runtime snapshot.
- Actors in unknown/invalid sectors are treated as uncullable rather than remapped to sector `0`.
- Aggressive/default-detected actors do not bypass the activation gate before their owning sector is activated.

Implementation notes:

- `collectIndoorActorAiFrameFacts()` skips actors in inactive sectors before active/background AI fact creation.
- `selectIndoorActiveActors()` rejects inactive-sector actors before distance and line-of-sight checks.
- Active spell-effect override timers are not advanced for inactive-sector actors.
- Projectile actor collision candidates skip inactive-sector actors.
- Party and actor movement collider candidate lists skip inactive-sector actors.
- Radius actor queries skip inactive-sector actors, matching the same broadphase policy.
- Gameplay minimap actor/object markers skip inactive-sector entities.
- The activation mask and visible-portal activation throttle accumulator are included in `IndoorWorldRuntime::Snapshot`.

Remaining follow-up:

- Persist seen-sector activation into saved games if this policy should survive save/load instead of only runtime
  snapshots.
- Add a lightweight debug counter for activated sector count and skipped inactive actors if profiling shows this needs
  in-game confirmation.
- Runtime actors/items/projectiles can still gain true sector buckets later; this slice provides the correctness gate
  before that data-structure optimization.

Acceptance:

- First visit to a dungeon room activates actors there.
- Closed-door/unseen sectors do not run actor AI and do not contribute actor collision candidates.
- Once activated, the sector keeps updating for the rest of the runtime session.

## Slice 9: Cleanup and Debug UX

Status: partially complete.

Goal: make the migration maintainable.

Tasks:

- Remove temporary per-second spam or gate it behind a debug flag.
- Add debug draw for:
  - eye sector
  - foot sector
  - graph connected sectors
  - visible portal paths
  - rejected portal reasons
  - clipped frustums
- Keep editor snapshot export as a fixture authoring tool.
- Update this plan as slices complete.

Acceptance:

- Debug information is useful but not noisy in normal runtime.
- The old fragile sector bitmask shortcuts are gone or isolated as compatibility diagnostics.

Implementation notes:

- `[IndoorVisibility]` and `[IndoorVisibilityPortal]` per-second logs are gated by `settings.ini`:
  `[logging] indoor_visibility=true`.
- Door animation invalidates indoor portal visibility on door state changes and quantized moving-door distance changes.
  This keeps recursive portal frustums current while `Opening`/`Closing` geometry exposes deeper rooms, without
  recomputing traversal for every tiny intermediate distance change. Moving mechanism textured-batch bounds are rebuilt
  once per affected batch, not once per moving face.
- Textured-batch visibility culling remains active while mechanisms move; moving door vertices are patched in place
  instead of rebuilding every adjusted indoor vertex each frame.
- Indoor minimap line generation uses a minimap reveal revision instead of hashing full face/outline state every refresh,
  and it computes visibility only for outline-referenced faces instead of pre-scanning every indoor face.

## Implementation Notes

- Implement slices in order. Do not combine graph construction, traversal replacement, and object-culling changes in one
  patch.
- Prefer unit/doctest coverage for pure graph logic.
- Use headless/editor diagnostics for map-load behavior and snapshot fixture assertions.
- Use OpenEnroth only as a behavioral/structural reference; do not copy code.
