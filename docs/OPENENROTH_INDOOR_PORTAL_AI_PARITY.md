# OpenEnroth Indoor Portal Visibility And AI Activation Parity

This note summarizes how the local OpenEnroth reference handles indoor portal rendering, moving doors, actor draw
visibility, and actor AI activation, then turns that into an OpenYAMM action plan.

OpenEnroth is used here only as a behavioral and structural reference. Do not copy implementation code.

## Executive Summary

OpenEnroth does not solve indoor portal visibility by asking whether a door is "open" or "closed". Its render traversal
is portal/frustum based. Doors are regular moving geometry: door vertices are moved every update, door face planes are
recomputed, and the rendered door surface occludes what is behind it through normal depth testing.

OpenEnroth also does not use the render-visible sector list as the source of truth for full actor AI activation. The BSP
visible sector list is used to decide which actor sprites can be submitted for drawing. Full AI activation is built
separately from actor distance, previous detection flags, same-sector membership, and a portal-line detection function.

The OpenYAMM parity direction should therefore be:

1. Split render portal traversal from gameplay perception.
2. Make render visibility door-state agnostic, OE-style.
3. Stop using render-visible sectors as the authoritative activation source for AI.
4. Keep AI activation as an actor-to-party detection query, not a camera-frustum sector query.
5. If OpenYAMM needs stricter "closed doors block AI perception" than OE, implement it as a real current-geometry line
   of sight/blocker query, not as portal traversal state heuristics.

## OpenEnroth Render Portal Flow

Reference files:

- `reference/OpenEnroth-git/src/Engine/Graphics/BspRenderer.h:28-48`
- `reference/OpenEnroth-git/src/Engine/Graphics/BspRenderer.cpp:14-191`
- `reference/OpenEnroth-git/src/Engine/Graphics/BspRenderer.cpp:207-238`
- `reference/OpenEnroth-git/src/Engine/Graphics/BspRenderer.cpp:241-285`
- `reference/OpenEnroth-git/src/Engine/Graphics/PortalFunctions.cpp:344-411`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:139-164`
- `reference/OpenEnroth-git/src/Engine/Graphics/Renderer/OpenGLRenderer.cpp:2975-3077`

OpenEnroth's indoor draw setup calls `pBspRenderer->Render()` from `PrepareDrawLists_BLV()`. The BSP renderer owns:

- `nodes`: sector views, each with the portal face that produced it and a frustum.
- `faces`: concrete non-portal faces to draw.
- `pVisibleSectorIDs_toDrawDecorsActorsEtcFrom`: sectors accepted by traversal for draw-list purposes.

The root node is the party eye sector, with the camera frustum. `AddNode()` walks that sector's non-BSP faces and BSP
faces. `AddFace()` handles both normal faces and portals:

- For normal faces:
  - Clip face vertices to the current node frustum.
  - Reject empty/invisible/untextured/back-facing faces.
  - Append the face to the draw list.
- For portal faces:
  - Reject the entry portal to avoid immediate recursion back through the same face.
  - Reject some backward-facing portal traversal except at the root node.
  - Clip/build a portal shape and derive a child frustum from the portal aperture.
  - Step to the other sector through `sectorId` / `backSectorId`.
  - Reject ancestor-sector loops.
  - Add the sector to the visible-sector list if it is a new sector.
  - Recurse into the child node.

Important portal edge handling in OE:

- It keeps duplicate nodes for a sector seen through different portals, while the visible-sector list is unique. This
  matters for places where the same sector can be viewed through different apertures.
- It has explicit loop guards: skip the entry portal, skip likely backward traversal, and reject ancestor-sector loops.
- If the camera is close to a root portal, or the portal normal is vertical in Z, OE resets the child node frustum to
  the full camera frustum. This avoids over-clipping near or horizontal portals.
- Portal traversal is based on current face geometry and frustum clipping. There is no "closed door blocks this portal"
  decision in the BSP traversal.

## OpenEnroth Moving Door Handling

Reference files:

- `reference/OpenEnroth-git/src/Engine/Graphics/FaceEnums.h:60-66`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.h:36-57`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:633-717`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:719-767`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:769-817`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:1496-1500`

OE door state names are endpoint names, not semantic "open means passable" names. The enum comment says most closed
doors are in `DOOR_OPEN = 0`, and most open doors are in `DOOR_CLOSED = 2`. The reliable interpretation is:

- State 0: initial mesh position.
- State 2: alternative mesh position at `direction * moveLength`.
- States 1 and 3: moving between endpoints.

Door initialization and update convert the current door state/time into a displacement distance.
`BLV_UpdateDoorGeometry` then:

- Moves all door vertex IDs to their current positions.
- Recomputes planes and z calculations for all door face IDs.
- Updates door-moved texture offsets.

The key implication is that OE does not need the portal walker to understand door semantics. The door mesh is in the
world. If it visually blocks what is behind it, depth testing blocks it. If it has moved out of the way, the view is no
longer occluded by that mesh.

## OpenEnroth Actor And Sprite Drawing

Reference files:

- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:139-164`
- `reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp:690-790`
- `reference/OpenEnroth-git/src/Engine/Graphics/Renderer/BaseRenderer.cpp:64-105`
- `reference/OpenEnroth-git/src/Engine/Graphics/Renderer/OpenGLRenderer.cpp:3163-3193`

OE uses `pVisibleSectorIDs_toDrawDecorsActorsEtcFrom` for draw submission:

- Decorations are gathered only from BSP visible sectors.
- Indoor actors are considered for billboards only if their sector is in the BSP visible-sector list.
- Sprite objects perform the same sector-list test indoors.
- Lights are also filtered against visible sectors and portal frustums.

This means the BSP visible-sector list is a render draw-list broad phase. It is not a guarantee that every pixel in that
sector is visible. A closed door can allow the sector to be in the list while the door surface still hides the sector's
pixels.

## OpenEnroth Indoor AI Activation

Reference files:

- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:2457-2487`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:2489-2551`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:2553-2815`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:3847-3895`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:3898-3985`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:3988-4134`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.h:86-101`

OE's `Actor::UpdateActorAI()` first builds the active AI list. Indoors this calls `MakeActorAIList_BLV()`.

The indoor activation behavior is:

- Clear each actor's full-AI flag.
- Ignore actors that cannot act.
- Compute 3D distance from party minus actor radius.
- Keep actors within 10240 map units as candidates.
- Set hostile/yellow/red alert flags from distance and relation.
- Sort candidates by distance.
- For each candidate, pick it if:
  - it already has `ACTOR_NEARBY`, or
  - `Detect_Between_Objects(actor, party)` succeeds.
- Cap this first detection pass at 30 picked actors.
- Add any actor in the party's current sector.
- Add actors that are already active or nearby and still can act.
- Apply the configured full-AI actor limit and set `ACTOR_FULL_AI_STATE`.

Actors not in full AI still receive background AI maintenance. Full-AI actors run the heavier targeting and action
logic.

OE's `Detect_Between_Objects()`:

- Computes source/target positions and sectors.
- Rejects if distance is above 5120.
- Returns true immediately if source and target sectors match.
- Indoors, traces a straight segment through portal faces.
- At each step, finds the first portal in the current sector whose plane is crossed by the segment and whose
  intersection point lies inside the portal polygon.
- Advances to the sector behind that portal.
- Succeeds if the target sector is reached.
- Stops after 30 portal steps.

Important limitation: this detection function is portal-topology based. It does not appear to test moving door occluder
geometry. This is consistent with OE's render philosophy, but it means OE parity is not the same as "closed solid doors
always block actor perception".

## OE Line Of Sight Is A Separate Tool

Reference files:

- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:1241-1286`
- `reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp:1288-1344`
- `reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp:2060-2125`

OE has a separate `Check_LineOfSight()` path. Indoors it tests three nearby rays: center, offset left, offset right. The
indoor ray test checks non-portal, non-ethereal faces in the source and target sectors.

This is not the same as `MakeActorAIList_BLV()` activation. The activation pass uses `Detect_Between_Objects()`. Target
selection for party targets also becomes mostly distance/relation once the actor is already active.

For OpenYAMM, that distinction matters:

- Portal detection controls "can wake up / stay in full AI".
- Combat/projectile/spell LOS should use current geometry collision/LOS.
- Render visibility should not be reused as either one.

## Pre-Implementation OpenYAMM Flow

This section describes the OpenYAMM flow before the parity implementation that removed render-time door blockers and
decoupled indoor actor AI activation from render-visible sectors.

Reference files:

- `game/indoor/IndoorPortalGraph.h:35-56`
- `game/indoor/IndoorPortalGraph.cpp:100-126`
- `game/indoor/IndoorPortalVisibility.h:55-91`
- `game/indoor/IndoorPortalVisibility.cpp:717-839`
- `game/indoor/IndoorPortalVisibility.cpp:1121-1465`
- `game/indoor/IndoorRenderer.cpp:2092-2226`
- `game/indoor/IndoorRenderer.cpp:2234-2279`
- `game/indoor/IndoorRenderer.cpp:2638-2698`
- `game/indoor/IndoorRenderer.cpp:5722-5830`
- `game/indoor/IndoorRenderer.cpp:6046-6130`
- `game/indoor/IndoorRenderer.cpp:6531-6635`
- `game/indoor/IndoorWorldRuntime.cpp:3903-3941`
- `game/indoor/IndoorWorldRuntime.cpp:3977-4084`
- `game/indoor/IndoorWorldRuntime.cpp:2689-2786`

Current OpenYAMM behavior is a hybrid:

- `IndoorPortalGraph` builds portal links and attaches direct door blockers from `MapDeltaDoor::faceIds`.
- `IndoorPortalVisibility` does OE-like portal recursion, but also asks `collectPortalBlockerDoorTraces()` whether doors
  should reject portal traversal.
- Door rejection currently mixes direct door membership, runtime mechanism state, non-portal door geometry, base door
  geometry, bounds checks, ray sampling, and several special cases.
- `IndoorRenderer::buildVisibleSectorMask()` caches the resulting sector mask and uses it for render draw submission,
  picking, billboards, sprites, and diagnostics.
- `IndoorWorldRuntime::refreshActivatedIndoorSectors()` can activate sectors from
  `IndoorRenderer::visibleIndoorPortalSectorIds()`.
- `IndoorWorldRuntime::selectIndoorActiveActors()` then skips actors whose sector has not been activated, and only after
  that performs distance and `indoorDetectBetweenObjects()` checks.

This is why the current system is sensitive to Hive, Naga vault, Abandoned Temple, and Goblinwatch door variants. Door
state and door-face metadata are being used to decide portal traversal, and that sector result is later used for actor
activation.

## Parity Target

The parity target should explicitly define four separate outputs:

1. `render_visible_sectors`
   - Purpose: draw-list broad phase for geometry, decorations, actors, sprites, lights.
   - Source: OE-style camera portal/frustum traversal.
   - Door rule: no semantic door blocker test.
   - Occlusion: current rendered geometry and depth.

2. `render_visible_nodes/frustums`
   - Purpose: portal-clipped billboard and light tests.
   - Source: same traversal as `render_visible_sectors`.
   - Door rule: no semantic door blocker test.

3. `actor_detection(actor, party)`
   - Purpose: decide whether actor can become/keep full AI.
   - Source: actor-to-party portal-line detection, not camera visibility.
   - OE parity: 5120 detection distance, 30 portal-step limit, same-sector succeeds.
   - Optional stricter OpenYAMM behavior: after portal-line success, run current-geometry LOS to block solid moved
     doors.

4. `actor_active_mask`
   - Purpose: full AI update selection.
   - Source: all can-act actors, distance sorting, previous detection, same sector, detection query, active limit.
   - Door/render rule: never depend on camera render-visible sectors.

## Action Plan

### 1. Make Render Portal Traversal Door-State Agnostic

Change `buildIndoorPortalVisibility()` or add a new render-specific path so the render mask never rejects portals
because of `blocked_by_closed_door`.

Practical options:

- Preferred: remove mechanism blocker checks from the render path entirely, and keep `ignoreMechanismBlockers=true` only
  for interaction/picking if a separate interaction rule is still needed.
- Transitional: make `IndoorRenderer::buildRenderVisibleSectorMask()` call `buildVisibleSectorMask(camera, true)` and
  rename the flag away from "interaction" semantics.

Expected result:

- Hive sector 76 can include sectors beyond the door in render-visible if portal geometry says so.
- The closed door mesh still visually hides them.
- Naga vault moving doors stop producing black portals because traversal no longer waits for a door state endpoint.
- Goblinwatch grouped doors stop depending on which door owns a shared portal face.

Required tests:

- Render traversal accepts portals independent of `MapDeltaDoor::state`.
- Render traversal accepts while a mechanism is moving.
- Door geometry still renders and depth-occludes behind-door geometry in a headless/pixel test.
- Existing portal-frustum loop tests still pass.

### 2. Keep Door Geometry Current And Authoritative For Visual Occlusion

OE parity depends on door vertices and face planes being updated before render traversal/draw submission.

OpenYAMM should verify:

- Runtime moved vertices are available to rendered textured batches.
- Door non-portal faces are submitted when their sector is render-visible.
- Door faces write depth before or with the same opaque pass as behind geometry.
- Moving door face bounds and planes update every tick without stale cached geometry.

Required tests:

- Naga vault sliding door: while moving, the portal sector is render-visible, but pixels behind the solid door area
  remain occluded by the door surface.
- Hive entry door: initial visible-sector list may include beyond-door sectors in render mode, but the first room still
  appears visually isolated.
- Goblinwatch chest door: after opening the selected chest door, room 13 can be rendered through portal 1941; adjacent
  grouped door metadata cannot black it out.

### 3. Stop Activating AI From Render-Visible Sectors

Do not use `IndoorRenderer::visibleIndoorPortalSectorIds()` as the source of actor sector activation.

Current risk:

- If render traversal is OE-style, sectors behind closed doors may become render-visible. Feeding that into
  `m_activatedIndoorSectorMask` wakes actors for the wrong reason.
- If render traversal keeps door blockers, actors may fail to activate in cases where OE would still consider them by
  distance/detection.

OpenYAMM changes:

- Remove render-visible sector activation from `refreshActivatedIndoorSectors()` for AI purposes.
- Keep party sector/eye sector activation only if sector activation is needed for lightweight simulation or map reveal.
- In `selectIndoorActiveActors()`, remove the hard skip on `!indoorActorSectorActivated(...)`, or replace it with a
  non-render source such as "actor was visited/spawned/loaded and is within coarse distance".

Required tests:

- Actor behind a closed door is not selected just because the camera render traversal includes its sector.
- Actor in an unopened but nearby sector is still evaluated by detection if within the actor candidate range.
- Same-sector actors are selected even if render cache is empty/stale.
- AI activation result is unchanged by camera yaw/pitch.

### 4. Align Actor Activation With OE First

OpenYAMM already has a similar detection shape in `indoorDetectBetweenObjects()`: range check, same-sector success,
portal-plane segment walk, 30-step limit.

Parity changes to consider:

- Match OE's detection distance: 5120 for the portal detection query.
- Match OE's candidate distance: 10240 for indoor active candidates.
- Match OE's same-sector force-add behavior.
- Preserve stable sorting by distance.
- Decide whether the full-AI cap should be OE/config parity or OpenYAMM's current `MaxActiveActorUpdates = 48`.

Required tests:

- Candidate at 10239 is considered; candidate at 10240+ is not.
- Detection ray through a chain of portal faces succeeds before 30 steps and fails after the step limit.
- Detection succeeds immediately in the same sector.
- Previous detection/active state keeps an actor eligible, independent of current camera-visible sectors.

### 5. Decide Whether To Exceed OE With Real Door-Blocking Perception

OE parity does not prove closed doors block activation. `Detect_Between_Objects()` follows portal faces and does not
appear to test moving door occluder geometry.

If OpenYAMM wants stricter gameplay behavior, implement it explicitly:

- First do OE-style portal-line detection to determine topological visibility.
- Then run a current-geometry LOS query from actor eye/attack point to party eye/target point.
- The LOS query should test current non-portal, non-ethereal faces along relevant sectors, including moved door faces.
- Do not use door state names or `door.faceIds` portal membership as blocker authority.

Required tests:

- Closed current-geometry door blocks actor detection.
- Moving door blocks or permits detection according to actual geometry intersection, not state number.
- Fully moved-open door does not block detection if the current mesh no longer intersects the ray.
- State 0 and state 2 variants both work because the actual vertices decide.

### 6. Keep Interaction/Picking Separate

Picking often wants a different rule than rendering or AI. It may need to ignore a closed door for debugging, or respect
doors for normal gameplay interaction.

Action:

- Do not reuse `render_visible_sectors` blindly for interaction.
- Keep a named interaction visibility policy if needed:
  - `Render`: OE-style, no semantic door blockers.
  - `GameplayPick`: current-geometry ray hit, nearest hit wins.
  - `DebugPick`: optionally ignores doors/occluders.
  - `ActorDetection`: OE portal-line plus optional geometry LOS.

## Migration Checklist

- [x] Rename current "visible sectors" APIs so render masks cannot be mistaken for gameplay visibility.
- [x] Add a render-specific portal traversal mode that cannot return `blocked_by_closed_door`.
- [x] Remove direct render dependence on `IndoorPortalLink::blockingDoorIds`.
- [x] Keep `IndoorPortalGraph` for topology diagnostics, but stop treating door membership as render authority.
- [x] Decouple `refreshActivatedIndoorSectors()` from renderer visible sectors for AI.
- [x] Make `selectIndoorActiveActors()` scan candidate actors by distance without render-sector gating.
- [x] Keep `indoorDetectBetweenObjects()` as the OE-parity portal detection query.
- [ ] Add optional current-geometry LOS after portal detection if stricter closed-door perception is desired.
- [ ] Add diagnostics that print render-visible and AI-detectable separately.
- [ ] Add headless/pixel tests for door occlusion rather than only sector-mask tests.

## Regression Map Set

Use these as the minimum parity set before removing the current blocker heuristics:

- MM6 Hive start sector 76:
  - Render traversal may include beyond-door sectors.
  - Actual first room should still render visually isolated while the door mesh is closed.
  - AI must not wake solely from render-visible sectors.
- MM8 Naga vault portal 318:
  - Portal sector should render while the sliding door is moving.
  - Door geometry should occlude until it has moved away.
- MM6 Abandoned Temple 6d02 sector 47 -> 49:
  - Adjacent state-zero door 2 must not block unrelated portal 3392.
- MM6 Goblinwatch 6d01 room 7 -> 13 portal 1941:
  - Opening chest door 9 should reveal room 13.
  - Adjacent grouped door 8 must not be treated as the authoritative portal blocker.

## Non-Goals

- Do not infer semantic open/closed from state 0 or state 2.
- Do not add per-map door-state compatibility tables.
- Do not trust `door.faceIds` membership as proof that a door blocks a portal.
- Do not use camera render-visible sectors as actor AI perception.
- Do not make actor activation depend on camera yaw, camera pitch, or render cache freshness.

## Bottom Line

OpenEnroth avoids our current portal-door edge cases by not making render portal traversal door-aware. Door geometry
moves, renders, and occludes through depth. Actor AI activation is a separate distance/detection system, not a camera
visibility system.

OpenYAMM should match that separation first. If stricter closed-door AI perception is required, add it as a current
geometry LOS layer after OE-style actor detection, not as another portal-blocker heuristic.
