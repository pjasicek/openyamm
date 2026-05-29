# MM9 DAT Physics And Collision Contract

This document defines the target behavior and implementation contract for MM9 DAT world physics, collision, movement,
ray queries, and contact reporting in OpenYAMM.

The goal is LithTech-compatible behavior implemented in OpenYAMM-owned code. The local `mm9/lithtech/` tree is the
primary semantic reference for MM9 world physics, but code must not be copied from it.

## Authority And References

Use these references in this order:

1. Local extracted MM9 DAT files and generated sidecars under `mm9/extracted/` and `assets_dev/worlds/mm9/maps/`.
2. Locally verified DAT parser facts in `docs/mm9/MM9_DAT_FORMAT_NOTES.md`.
3. The runtime integration contract in `docs/mm9/MM9_DAT_DTX_RUNTIME_INTEGRATION_CONTRACT.md`.
4. Local LithTech semantic references under `mm9/lithtech/`.
5. `mm9/ltjs` and other public readers only as cross-checks.

Important local LithTech files:

- `mm9/lithtech/runtime/world/src/de_world.h`
  - `WIF_MOVEABLE`, `WIF_MAINWORLD`, `WIF_PHYSICSBSP`, `WIF_VISBSP`.
  - `SURF_SOLID`, `SURF_PHYSICSBLOCKER`, `SURF_VISBLOCKER`, `SURF_NOTASTEP`, `SURF_INVISIBLE`, `SURF_PORTAL`.
- `mm9/lithtech/tools/PreProcessor/Packer_PC/PCWorldPacker.cpp`
  - DAT version history. Version 66 adds visibility and physics BSPs.
- `mm9/lithtech/tools/PreProcessor/Processing.cpp`
  - Creates the named `PhysicsBSP` model with `WIF_PHYSICSBSP | WIF_MAINWORLD`.
- `mm9/lithtech/runtime/shared/src/moveobject.cpp`
  - Main movement dispatch, standing-on tracking, object movement, carried objects, touch notification flow.
- `mm9/lithtech/runtime/shared/src/moveplayer.cpp`
  - Player cylinder movement, sliding, stair step, standing surface selection, touch pass.
- `mm9/lithtech/runtime/shared/src/collision.cpp`
  - BSP collision, box/cylinder handling, step-up behavior, blockers, `SURF_NOTASTEP`.
- `mm9/lithtech/runtime/world/src/fullintersectline.cpp`
  - Ray/segment intersection and `HPOLY`/surface flag reporting.
- `mm9/lithtech/runtime/world/src/intersectsweptsphere.cpp`
  - Swept sphere against solid world models, useful for query/projectile semantics.
- `mm9/lithtech/runtime/world/src/de_mainworld.cpp`
  - Transforming movable world model BSP data for runtime collision/rendering.

## Design Target

MM9 DAT maps should not use MM6-MM8 ODM or BLV movement semantics as their long-term runtime truth. The DAT runtime
should use a LithTech-shaped world contract:

- DAT world models are authoritative.
- `PhysicsBSP` is the primary static collision source when present.
- `VisBSP`, leaves, and user portals remain available for visibility, portal, and sector-like behavior.
- Visible DAT geometry participates in collision only when required by source flags or when no more specific physics
  source exists.
- Movable world models use transformed collision proxies derived from original DAT BSP data.
- DAT surface flags and DTX texture/user flags are separate source fields and must not be collapsed.
- Runtime contacts carry source model/poly/surface ids so gameplay, debugging, and editor inspection can resolve back to
  original DAT data.

## Runtime Ownership

The target runtime layering is:

```text
Mm9DatWorld
  Parsed, lossless DAT source structures.

DatWorldView
  Read-only or controlled-query view over DAT world geometry, helper BSPs, source metadata, spatial indices, and dynamic
  world-model transforms.

Mm9DatLevelRuntime / DatLevelRuntime
  Implements IGameplayWorldRuntime. Owns party/actor/projectile movement, interaction, events, save state, and calls
  DatWorldView for world-format-specific physics and query services.

Mm9DatLevelView / DatLevelView
  Presentation/render/input wrapper equivalent in role to IndoorGameView and OutdoorGameView. It should not be the
  primary gameplay abstraction.
```

Shared gameplay should talk to `IGameplayWorldRuntime`. `DatWorldView` is the implementation service used by the MM9
runtime, not a new global gameplay dependency.

## DatWorldView Service Contract

`DatWorldView` or its equivalent should provide these services before the MM9 runtime relies on it:

- Access to source world models by role:
  - visible geometry;
  - `PhysicsBSP`;
  - `VisBSP`;
  - sky;
  - water;
  - trigger/volume helpers;
  - movable world models.
- Static spatial acceleration for DAT world geometry.
- Dynamic spatial proxies for movable world models and mechanisms.
- Raycast/segment query against selectable channels.
- Player/party cylinder sweep against DAT physics geometry.
- Actor/object box or cylinder sweep as needed by gameplay.
- Swept sphere query for projectiles or spell effects when appropriate.
- Standing surface query for party and actors.
- Line-of-sight query for combat, AI, projectiles, and spell targeting.
- Trigger/volume overlap query for touch/use dispatch.
- Contact material lookup from DTX texture/user flags.
- Source id lookup for every contact:
  - source model index and name;
  - source poly index;
  - source surface index;
  - source texture index and texture path;
  - DAT surface flags;
  - DTX texture/user flags.

## Coordinate And Source Data Rules

- Keep original DAT/LithTech coordinates in source structures.
- Convert to OpenYAMM coordinates at explicit query/render/runtime boundaries.
- Do not discard DAT source ids after conversion.
- Do not use generated ODM/BLV face ids as MM9 truth. They are compatibility bindings only.
- Do not infer collision from UVs. UV vectors are render/material data.
- Do not infer collision from texture names alone. Texture names may help classify helper content, but DAT flags and
  world-model roles are the primary source.

## Geometry Channel Rules

Collision source priority:

1. `PhysicsBSP` world model, when present.
2. `SURF_PHYSICSBLOCKER` blocker data or equivalent extracted blocker polygons.
3. Movable world model collision proxies.
4. Visible world surfaces with `SURF_SOLID` or other confirmed collision participation.
5. Fallback visible geometry only for temporary diagnostics or maps with missing authoritative physics data.

Visibility/query source priority:

1. `VisBSP`, leaves, and user portals for portal/visibility behavior.
2. Coarser spatial culling may be used before full portal visibility is implemented.
3. `VisBSP` must not be rendered as ordinary visible art.

Interaction source priority:

1. DAT object bindings and generated `events.yml`/script runtime object registry.
2. Picked source model/poly/surface ids.
3. Trigger and volume objects.
4. Compatibility face/bmodel ids only as a transition layer.

## Surface And Material Flags

DAT surface flags control world behavior:

- `SURF_SOLID`: solid surface candidate.
- `SURF_PHYSICSBLOCKER`: hard movement blocker source.
- `SURF_VISBLOCKER`: visibility blocker.
- `SURF_NOTASTEP`: cannot be stepped onto by stair-step logic.
- `SURF_INVISIBLE`: not ordinary visible art; may still be physical/helper geometry.
- `SURF_PORTAL`: portal/open-close semantic hint.

DTX texture/user flags are material/contact metadata:

- Report them in raycast/contact results.
- Preserve them for footsteps, projectiles, damage/material effects, and scripts.
- Do not use them as a replacement for DAT surface flags.

## Party Movement Semantics

The MM9 party movement resolver should be LithTech-compatible:

- Treat the party as a vertical, Y-axis-aligned cylinder for player-style DAT collision.
- Sweep from start to intended destination rather than testing only the final position.
- Find the earliest blocking contact, move to the valid contact boundary, then slide along the blocking plane.
- Apply iterative collision resolution with a bounded iteration count.
- Preserve wall sliding unless a no-sliding state is explicitly active.
- Use stair-step behavior when enabled:
  - first try low movement;
  - if blocked, try a step-up movement;
  - move forward at the raised height;
  - move down to the landing surface;
  - prefer the step-up result only when it advances farther along the intended movement.
- Respect `SURF_NOTASTEP`; such surfaces should block step-up and fall back to full-height collision.
- Track the current standing object/surface:
  - world model object;
  - source BSP node/poly or equivalent source contact;
  - plane/normal;
  - whether the party is grounded.
- Moving platforms and lifts should carry standing objects unless explicitly disabled by runtime state.

Initial constants should follow LithTech behavior where practical:

- Default stair height should come from the body dimensions when no explicit map/runtime value is set.
- Steep slope thresholds should be configurable in one place and initialized from the LithTech-style values found in
  `moveplayer.cpp`.
- Safety margins/epsilons should be centralized and documented, not scattered through query code.

## Actor And Object Movement

Actors and objects should use MM9/DAT geometry services instead of MM6-MM8 terrain or BLV-specific shortcuts.

Actor movement should support:

- cylinder or box collision based on runtime actor/object type;
- gravity and airborne state;
- standing-on tracking;
- sliding against world planes;
- blocker handling;
- interaction with solid actors and solid scripted objects;
- optional path/AI line-of-sight against DAT geometry.

Generic objects should support:

- AABB/box collision where LithTech would use box physics.
- Cylinder collision for player-like or actor-like movers.
- Point collision only for objects that explicitly request point-style movement.
- Trigger/container overlap without forcing solid collision.

## Raycasts, Picking, And Line Of Sight

Raycast and segment query results should contain:

```text
hit: bool
point
plane normal and distance
distance along query
hit kind
source object/runtime object id, if any
source model index and name
source poly index
source surface index
source texture index and source texture path
DAT surface flags
DTX texture/user flags
```

Line-of-sight should use the same collision channels as projectile/world obstruction unless a gameplay feature has a
documented reason to use a different channel.

Picking should allow channel selection:

- visible art;
- physics;
- triggers/volumes;
- actors;
- items;
- scripted objects;
- debug helper geometry.

## Contact Reporting

Movement contacts should map naturally to the current OpenYAMM gameplay structs while preserving LithTech-like facts:

- contact plane;
- hit object/runtime object;
- source poly handle/source ids;
- stop velocity or velocity correction;
- force/impact magnitude when needed for touch notifications;
- material flags;
- support/standing surface.

The MM9 runtime may expose an OpenYAMM-native contact struct, but it must be rich enough to generate equivalents of:

- LithTech `CollisionInfo`;
- LithTech `IntersectInfo`;
- `GameplayWorldHit`;
- projectile impact facts;
- actor AI obstruction facts;
- editor/debug inspection facts.

## Moving World Models And Mechanisms

Movable DAT world models must not be reduced to static mesh-only geometry.

Runtime support should include:

- original rest BSP/source geometry;
- current transform;
- transformed collision proxy;
- transformed render proxy;
- dynamic bounds;
- dirty update flag;
- standing-on carry behavior;
- source object binding for script messages.

Door, rotating door, lift, and platform mechanisms should update both render and collision proxies from the same runtime
state. Do not render a moved object while collision remains at rest, and do not update collision without matching visual
state.

## Trigger, Volume, Water, Ladder, And Helper Brushes

Trigger and volume geometry should be treated as runtime volumes, not ordinary visible art.

Required volume behaviors:

- touch/enter/leave detection;
- use/activate dispatch where supported;
- source object binding;
- optional solid state changes from scripts;
- water/underwater state;
- ladder or forced movement volumes if confirmed by source objects/scripts.

Invisible helper geometry may still be physical, visible-blocking, or trigger-like. Classification must preserve source
flags and object bindings so behavior can be corrected without reparsing DAT.

## Integration With IGameplayWorldRuntime

The MM9 level runtime should implement `IGameplayWorldRuntime` directly or through a thin MM9-specific runtime class.

`IGameplayWorldRuntime` methods should delegate to DAT services where world geometry is needed:

- `updateWorldMovement` uses party movement sweep/collision.
- `updateActorAi` uses DAT line-of-sight, floor/support, and actor movement.
- projectile and spell methods use DAT ray/sweep/contact queries.
- world picking methods use DAT raycast and source binding.
- minimap methods use DAT geometry/portal data, not ODM/BLV assumptions.

Do not add MM9-specific branches throughout shared gameplay when a world-runtime virtual method can provide the needed
behavior.

## Implementation Phases

### Phase 1 - Read-Only Query Foundation

- Build role-filtered DAT geometry views.
- Add source-id-preserving triangle/poly access.
- Add channel-aware raycast against DAT render and physics geometry.
- Add contact result structs with DAT surface flags and DTX texture/user flags.
- Add focused tests for role classification and source id preservation.

### Phase 2 - Static Party Collision

- Implement static `PhysicsBSP` cylinder sweep.
- Add sliding and earliest-contact resolution.
- Add standing-surface query.
- Add `SURF_NOTASTEP` stair-step behavior.
- Add headless tests on representative maps such as Thronheim, Lich Lab, and one small indoor-like DAT map.

### Phase 3 - Actors, Objects, And Projectiles

- Add actor/object sweeps.
- Add actor line-of-sight over DAT physics geometry.
- Route projectile impacts through DAT ray/sweep queries.
- Preserve material/source contact facts for gameplay effects.

### Phase 4 - Movable World Models

- Add dynamic transform proxies.
- Update collision and render from the same mechanism state.
- Support standing-on carry behavior for lifts/platforms.
- Add tests for doors/lifts blocking and becoming passable.

### Phase 5 - Volumes And Mechanism Integration

- Add trigger/water/ladder/helper volume channels.
- Bind touch/use dispatch to MM9 object registry and generated scripts.
- Add save/load state for movable and trigger volume state.

## Tests And Diagnostics

Prefer pure/query tests where possible:

- DAT role classification identifies `PhysicsBSP` and `VisBSP`.
- Raycasts preserve source model/poly/surface ids.
- Physics raycasts report DAT surface flags and DTX texture/user flags separately.
- Cylinder sweep hits the earliest blocking plane.
- Sliding moves along a wall instead of stopping dead.
- `SURF_NOTASTEP` blocks stair-step.
- Standing-on detects the correct source support surface.
- Movable world model transform changes collision results.

Add headless gameplay tests when the behavior requires runtime state:

- party walks across a DAT floor without falling through;
- party is blocked by `PhysicsBSP` walls;
- party slides along a wall;
- party steps onto allowed low geometry;
- party cannot step onto `SURF_NOTASTEP`;
- actor/projectile line-of-sight is blocked by DAT physics geometry;
- moving lift/door updates collision.

Diagnostics should be available but quiet by default:

- selected collision channel overlay;
- picked source model/poly/surface ids;
- contact plane/normal display;
- standing-on source display;
- movement trace for last party collision frame;
- role counts for visible/physics/visibility/helper geometry.

## Non-Goals

- Do not copy LithTech or LTJS source code into OpenYAMM.
- Do not make generated ODM/BLV compatibility geometry the authoritative MM9 collision source.
- Do not infer collision from texture UVs.
- Do not collapse DAT surface flags and DTX user flags.
- Do not add broad fallback behavior that hides missing `PhysicsBSP`, stale source ids, or broken DAT parsing.
- Do not change MM6-MM8 indoor/outdoor movement semantics while adding MM9 DAT physics.

