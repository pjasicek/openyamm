# Projectile Service Moderate Refactor Wiggum Plan

This document is the authoritative executable plan for the projectile service
moderate refactor.

It is designed for repeated autonomous execution. Do not execute it linearly
from top to bottom. Use the task queue section as the executable queue and
update the progress section after every meaningful slice.

## Goal

Reduce projectile over-abstraction without merging indoor/outdoor world logic.

Keep the core architecture:

- shared projectile code owns projectile state and gameplay rules;
- active world owns collision/fact collection and world-specific application;
- projectile simulation is entered from the active world update path;
- behavior remains unchanged unless a clear projectile bug is found and fixed
  intentionally.

The target readable frame shape is:

```cpp
ProjectileFrameFacts facts = world.collectProjectileFrameFacts(projectile, deltaSeconds);
ProjectileFrameResult result = projectileService.updateProjectileFrame(projectile, facts);
world.applyProjectileFrameResult(projectile, result);
```

## Boundary Rule

Shared projectile service owns what projectile gameplay should do.

Active world owns what the projectile collided with, how collision is computed,
and how results are applied to ODM/BLV representation.

Do not replace many decision structs with many callbacks. The exchange should
be domain data: facts in, result out.

## Non-Goals

- Do not merge indoor and outdoor runtime/render/collision types.
- Do not rewrite projectile behavior.
- Do not split `GameplayProjectileService` into many files in this refactor.
- Do not move all projectile code into `GameSession`.
- Do not change save format unless unavoidable.
- Do not refactor Fire Spike, Meteor Shower, Starburst, and projectile
  presentation all at once.
- Do not create another adapter layer that only hides the existing complexity.

## Current Pain

`GameplayProjectileService` exposes too many intermediate frame-decision types:

- `ProjectileFrameAdvanceResult`;
- `ProjectileImpactDecision`;
- `ProjectileLifetimeExpiryDecision`;
- `ProjectileBounceDecision`;
- `ProjectileCollisionOutcomeDecision`;
- `ProjectileCollisionPresentationDecision`;
- `ProjectileCollisionResolutionDecision`;
- `ProjectileCollisionFrameDecision`;
- `ProjectileUpdateFrameDecision`;
- multiple command enums.

This is mechanically correct but hard to read. The public API describes the
extraction mechanics more than the projectile domain.

## Target Public Shape

### `ProjectileFrameFacts`

A heavier facts struct built by the active world. It should contain all data
shared projectile logic needs for one projectile frame:

```cpp
struct ProjectileFrameFacts
{
    float deltaSeconds = 0.0f;
    float gravity = 0.0f;
    float bounceFactor = 0.0f;
    float bounceStopVelocity = 0.0f;
    float groundDamping = 0.0f;

    ProjectileMotionSegment motion;

    bool hasCollision = false;
    ProjectileCollisionFacts collision;

    GameplayWorldPoint partyPosition;
    float partyCollisionRadius = 0.0f;
    float partyCollisionHeight = 0.0f;

    std::vector<ProjectileAreaActorFacts> areaActors;
};
```

### `ProjectileFrameResult`

A heavier result struct returned by shared projectile logic. It should contain
readable outcomes, not nested command scripts:

```cpp
struct ProjectileFrameResult
{
    ProjectileMotionSegment motion;
    bool applyMotionEnd = false;
    bool expireProjectile = false;
    bool logCollision = false;
    bool logLifetimeExpiry = false;

    std::optional<ProjectileBounceResult> bounce;
    std::optional<ProjectileDirectPartyImpact> directPartyImpact;
    std::optional<ProjectileDirectActorImpact> directActorImpact;
    std::optional<ProjectileAreaImpact> areaImpact;
    std::optional<ProjectileFxRequest> fxRequest;
    std::optional<ProjectileAudioRequest> audioRequest;
    std::vector<ProjectileSpawnRequest> spawnedProjectiles;
};
```

Exact names may change to fit current code. The important part is one readable
frame facts packet and one readable frame result packet.

### Frame API

Add or converge to:

```cpp
ProjectileFrameResult GameplayProjectileService::updateProjectileFrame(
    ProjectileState &projectile,
    const ProjectileFrameFacts &facts) const;
```

Keep low-level mutators only where they are true world application helpers.

## Executable Task Queue

### Step 1 - Add coarse frame facts/result types

- [ ] Audit current public projectile structs in `GameplayProjectileService.h`.
- [ ] Add `ProjectileFrameFacts` beside existing types.
- [ ] Add `ProjectileFrameResult` beside existing types.
- [ ] Prefer complete domain packets over many tiny public input/result structs.
- [ ] Do not change call sites yet.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Project builds.
- No projectile behavior changes.
- New types do not expose outdoor or indoor representation details.

### Step 2 - Add outdoor projectile frame fact builder

- [ ] Audit `OutdoorWorldRuntime::updateProjectiles`.
- [ ] Add a helper that collects all world facts needed for one projectile
  frame.
- [ ] Reuse existing collision/bounce/area-impact helpers internally.
- [ ] Keep behavior unchanged.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- `updateProjectiles` becomes slightly flatter.
- World-specific collision and terrain/bmodel facts remain outdoor-owned.

### Step 3 - Implement `updateProjectileFrame`

- [ ] Implement the new frame API in `GameplayProjectileService`.
- [ ] Initially delegate to existing internal decision builders if that reduces
  risk.
- [ ] Convert old decision output into `ProjectileFrameResult`.
- [ ] Add local helper names that describe projectile behavior, not extraction
  plumbing.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Old and new paths produce equivalent outcomes.
- No old public structs removed yet.

### Step 4 - Switch outdoor projectile loop to facts/result

- [ ] Change outdoor projectile loop to collect facts, call
  `updateProjectileFrame`, then apply result.
- [ ] Add `OutdoorWorldRuntime::applyProjectileFrameResult`.
- [ ] Keep existing helper methods temporarily where useful.
- [ ] Preserve projectile logging, audio, FX, bounce, area damage, direct damage,
  lifetime expiry, and spawned projectile behavior.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- `OutdoorWorldRuntime::updateProjectiles` reads as the target loop.
- Outdoor no longer switches over shared service command enums for the main
  projectile frame.

### Step 5 - Remove or privatize old frame-decision layer

- [ ] Remove old intermediate decision structs from the public header where no
  longer used by call sites.
- [ ] Keep old helpers private only if they still clarify internal
  implementation.
- [ ] Remove public command enums that are only frame-update plumbing.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Public projectile API is smaller and domain-shaped.
- Old frame-update command-script API is gone from public use.

### Step 6 - Rename misleading presentation terms

- [ ] Rename result/effect types that use "presentation" for audio/log/impact
  orchestration.
- [ ] Reserve "presentation" for actual render-facing state.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Naming distinguishes gameplay result/effects from renderer-facing
  presentation state.

### Step 7 - Re-audit Fire Spike and shower projectiles only after stable frame path

- [ ] Audit Fire Spike, Meteor Shower, Starburst, and special projectile paths.
- [ ] Record whether they fit the new frame shape or need a separate follow-up.
- [ ] Do not refactor them unless the main projectile loop is already stable and
  the change is small.
- [ ] Build and run ctest if code changed.
- [ ] Update progress.

Acceptance:

- Special projectile paths are documented and not accidentally broken.

## Wiggum Prompt

Use this prompt for autonomous loop execution:

```text
Read these files first:

- AGENTS.md
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md
- docs/projectile_service_moderate_refactor_plan.md

Use docs/projectile_service_moderate_refactor_plan.md as the executable plan
for this run.

Do not execute the plan linearly. Execute the next unfinished task from the
Executable Task Queue.

Work on one coherent slice. Keep projectile behavior unchanged unless fixing a
clear bug. Do not merge indoor/outdoor world logic. Do not introduce callback
bags or adapters that hide ownership. Shared projectile service owns projectile
gameplay decisions; active world owns collision facts and world application.

Run:
- cmake --build build --target openyamm -j25
- ctest --test-dir build --output-on-failure

Update the progress section in docs/projectile_service_moderate_refactor_plan.md
with concrete evidence, validation, and remaining work.

Stop only after finishing the current slice and leaving the repo buildable, or
if the progress section records: Hard blocker: YES.
```

## Progress

Current status:

- Overall completion: not complete.
- Current focus: Step 1 - add coarse frame facts/result types.
- Last validated at: not yet validated for this refactor.
- Hard blocker: NO

Done definition satisfied: NO

Validation history:

- None for this refactor yet.

Manual smoke status:

- Not run yet.

## Done Definition

This refactor is done only when:

- the main projectile loop uses `ProjectileFrameFacts` and
  `ProjectileFrameResult`;
- shared projectile service owns projectile gameplay decisions;
- active world owns projectile collision facts and world-specific application;
- public projectile frame API no longer exposes the old micro-decision command
  layer;
- behavior is validated by build/tests and relevant manual smoke notes;
- this progress section says `Done definition satisfied: YES`.
