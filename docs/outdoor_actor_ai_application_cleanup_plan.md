# Outdoor Actor AI Application Cleanup Plan

## 2026-04-22 Status

Implemented in game code:

- `OutdoorActorAiFrameApplication` has been deleted from `OutdoorWorldRuntime`.
- Outdoor applies `ActorAiFrameResult` directly.
- Movement facts needed by the world are carried on `ActorMovementIntent`.
- The remaining shared actor result shape uses `ActorStateUpdate` / `ActorAnimationUpdate` instead of public
  patch-named result packets.
- `cmake --build build --target openyamm -j25` and `ctest --test-dir build --output-on-failure` passed after the
  cleanup, with CTest reporting no registered tests.

The older design notes below are kept as historical rationale for why the application object was removed.

## Goal

Make the outdoor actor update path readable after the shared actor AI refactor.

The current architecture is broadly correct:

```cpp
ActorAiFrameFacts facts = collectOutdoorActorAiFrameFacts(...);
ActorAiFrameResult result = actorAiSystem.updateActors(facts);
applyOutdoorActorAiFrameResult(result, ...);
updateOutdoorActorsForStep(...);
```

But the current outdoor application layer is too complicated. It uses a large `OutdoorActorAiFrameApplication` object
with many parallel masks and arrays. That object should not become a permanent abstraction. It should be removed and
replaced with direct per-actor application.

The target is not another wrapper layer. The target is simpler code.

## Current Problem

Outdoor now has a clean top-level loop, but the work below it is still heavy:

- `OutdoorActorAiFrameApplication` stores many parallel vectors;
- `applyOutdoorActorAiFrameResult` interprets shared AI phase flags;
- `updateOutdoorActorsForStep` re-interprets those masks and arrays;
- movement data is copied through side arrays before being consumed;
- `ActorAiUpdate` exposes internal phase flags such as `combatFlowHandled`, `combatEngageHandled`,
  `nonCombatHandled`, and `frameCommitHandled`;
- result application is harder to read than the original desired flow.

This means the refactor improved ownership, but did not fully improve readability.

## Desired End State

Outdoor actor update should read as a direct frame:

```cpp
void OutdoorWorldRuntime::updateMapActors(float deltaSeconds, float partyX, float partyY, float partyZ)
{
    updateActorFrameGlobalEffects(deltaSeconds, partyX, partyY, partyZ);

    while (m_actorUpdateAccumulatorSeconds >= ActorUpdateStepSeconds)
    {
        const OutdoorActorFrameContext context = buildOutdoorActorFrameContext(partyX, partyY, partyZ);
        ActorAiFrameFacts facts = collectOutdoorActorAiFrameFacts(context);
        ActorAiFrameResult result = m_actorAiSystem.updateActors(facts);

        applyOutdoorActorAiFrameResult(result, context);
        applyActorFrameSideEffects(ActorUpdateStepSeconds, partyX, partyY, partyZ);

        m_actorUpdateAccumulatorSeconds -= ActorUpdateStepSeconds;
    }
}
```

And result application should be direct:

```cpp
void OutdoorWorldRuntime::applyOutdoorActorAiFrameResult(
    const ActorAiFrameResult &result,
    const OutdoorActorFrameContext &context)
{
    for (const ActorAiUpdate &update : result.actorUpdates)
    {
        applyOutdoorActorAiUpdate(update, context);
    }

    applyOutdoorActorProjectileRequests(result.projectileRequests);
    applyOutdoorActorAudioRequests(result.audioRequests);
    applyOutdoorActorFxRequests(result.fxRequests);
}
```

Per actor:

```cpp
void OutdoorWorldRuntime::applyOutdoorActorAiUpdate(
    const ActorAiUpdate &update,
    const OutdoorActorFrameContext &context)
{
    MapActorState &actor = m_mapActors[update.actorIndex];

    applyOutdoorActorStatePatch(actor, update.statePatch);
    applyOutdoorActorAnimationPatch(actor, update.animationPatch);
    applyOutdoorActorAttackRequest(actor, update.attackRequest);

    if (update.movementIntent.applyMovement)
    {
        resolveOutdoorActorMovement(actor, update, context);
    }

    syncOutdoorActorIntegerPosition(actor);
}
```

This should read as:

1. Apply state patch.
2. Apply animation patch.
3. Apply attack request.
4. Resolve outdoor movement if requested.
5. Apply post-movement shared AI update if movement/crowd state needs it.
6. Sync actor position.

## What To Remove

Delete `OutdoorActorAiFrameApplication`.

Do not replace it with another object that has the same parallel-vector shape.

Remove these concepts from outdoor application:

- `activeUpdatesAppliedActorMask`;
- `combatFlowsAppliedActorMask`;
- `combatEngagesAppliedActorMask`;
- `nonCombatAppliedActorMask`;
- `frameCommitsAppliedActorMask`;
- `frameCommitKeepCurrentAnimationMask`;
- `frameCommitResetAnimationTimeMask`;
- `frameCommitResetCrowdSteeringMask`;
- `frameCommitClearVelocityMask`;
- `frameCommitApplyMovementMask`;
- `combatFlowDesiredMoveX`;
- `combatFlowDesiredMoveY`;
- `combatEngageDesiredMoveX`;
- `combatEngageDesiredMoveY`;
- `nonCombatDesiredMoveX`;
- `nonCombatDesiredMoveY`;
- `combatEngageMeleePursuitActiveMask`;
- `movementEffectiveMoveSpeed`;
- `movementTargetPosition`;
- `movementTargetEdgeDistance`;
- `movementInMeleeRangeMask`.

Those are not domain concepts. They are temporary coordination artifacts.

## What To Replace Them With

`ActorAiUpdate` should carry the data needed to apply one actor update directly.

The update should describe the result in domain terms:

```cpp
struct ActorAiUpdate
{
    size_t actorIndex = static_cast<size_t>(-1);

    ActorAiUpdateKind kind = ActorAiUpdateKind::None;
    ActorStatePatch statePatch;
    ActorAnimationPatch animationPatch;
    ActorMovementIntent movementIntent;

    std::optional<ActorAttackRequest> attackRequest;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};
```

Use a single result kind instead of many phase booleans:

```cpp
enum class ActorAiUpdateKind
{
    None,
    Background,
    Death,
    StatusLock,
    ContinueAttack,
    StartAttack,
    Pursue,
    Flee,
    Wander,
    Stand,
    PostMovement,
};
```

This is not for branching everywhere. It is for debugging, assertions, and occasional world-specific handling.

Outdoor should normally just apply patches and movement intent.

## Movement Intent

`ActorMovementIntent` should contain everything outdoor needs for movement:

```cpp
struct ActorMovementIntent
{
    ActorAiMovementAction action = ActorAiMovementAction::None;

    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float desiredMoveX = 0.0f;
    float desiredMoveY = 0.0f;
    float yawRadians = 0.0f;

    float moveSpeed = 0.0f;
    GameplayWorldPoint targetPosition;
    float targetEdgeDistance = 0.0f;

    bool updateYaw = false;
    bool clearVelocity = false;
    bool applyMovement = false;
    bool meleePursuitActive = false;
    bool inMeleeRange = false;
};
```

This removes the need for side arrays such as `movementEffectiveMoveSpeed`, `movementTargetPosition`, and
`movementInMeleeRangeMask`.

If a field is only needed to resolve world movement, it belongs in `ActorMovementIntent`, not in
`OutdoorActorAiFrameApplication`.

## Frame Commit

Do not keep `frameCommitHandled` as a public result flag.

Frame commit effects should become direct patch fields:

```cpp
struct ActorAnimationPatch
{
    std::optional<ActorAiAnimationState> animationState;
    std::optional<float> animationTimeTicks;
    bool keepCurrentAnimation = false;
    bool resetAnimationTime = false;
};

struct ActorMovementIntent
{
    bool clearVelocity = false;
    bool applyMovement = false;
};

struct ActorAiUpdate
{
    bool resetCrowdSteering = false;
};
```

Outdoor should apply those fields directly. It should not first copy them into `frameCommit...Mask` vectors.

## Missing Stats And Inactive Actors

The current `updateOutdoorActorsForStep` still contains special handling for missing stats and inactive actor
presentation.

Keep these outdoor-owned paths, but make them explicit:

```cpp
for each actor:
    if actor has no monster stats:
        updateOutdoorActorMissingStats(...)
        continue;

    if actor is inactive:
        updateOutdoorInactiveActor(...)
        continue;

    apply shared AI update for actor
```

Do not hide these paths inside the shared AI system. Missing stats and inactive presentation are outdoor runtime
concerns.

## Post-Movement AI

Outdoor movement/collision stays outdoor-owned.

The current `GameplayActorAiSystem::updateActorAfterWorldMovement` can remain, but should be used directly:

```cpp
if (update.movementIntent.applyMovement)
{
    OutdoorActorMovementResult movement = resolveOutdoorActorMovement(actor, update.movementIntent, context);

    ActorAiFacts postMoveFacts = buildOutdoorPostMovementActorFacts(actor, movement, update);
    ActorAiUpdate postMoveUpdate = actorAiSystem.updateActorAfterWorldMovement(postMoveFacts);

    applyOutdoorActorAiUpdate(postMoveUpdate, context);
}
```

The important rule:

Do not send post-movement data through another frame-wide application object.

## Migration Steps

### Step 1 - Introduce `ActorAiUpdateKind`

Add `ActorAiUpdateKind` to `GameplayActorAiTypes.h`.

Set it in `GameplayActorAiSystem` where updates are built:

- death;
- status lock;
- continue attack;
- start attack;
- pursue;
- flee;
- wander;
- stand;
- non-combat;
- post-movement.

Acceptance:

- Build passes.
- No outdoor logic changes yet.

### Step 2 - Move Movement Application Data Into `ActorMovementIntent`

Add the outdoor-needed movement fields to `ActorMovementIntent`:

- `moveSpeed`;
- `targetPosition`;
- `targetEdgeDistance`;
- `meleePursuitActive`;
- `inMeleeRange`.

Populate them in `GameplayActorAiSystem`.

Acceptance:

- Outdoor no longer needs movement side arrays for those values.

### Step 3 - Add Direct Per-Actor Application Helpers

Add helpers in `OutdoorWorldRuntime`:

```cpp
void applyOutdoorActorStatePatch(MapActorState &actor, const ActorStatePatch &patch);
void applyOutdoorActorAnimationPatch(MapActorState &actor, const ActorAnimationPatch &patch);
void applyOutdoorActorMovementIntent(
    size_t actorIndex,
    MapActorState &actor,
    const ActorMovementIntent &intent,
    const OutdoorActorFrameContext &context);
void applyOutdoorActorAiUpdate(
    const ActorAiUpdate &update,
    const OutdoorActorFrameContext &context);
```

Acceptance:

- Existing application logic starts moving into direct patch application helpers.
- No new wrapper object is introduced.

### Step 4 - Replace `applyOutdoorActorAiFrameResult`

Rewrite `applyOutdoorActorAiFrameResult` to loop over updates and call `applyOutdoorActorAiUpdate`.

It should no longer return `OutdoorActorAiFrameApplication`.

Acceptance:

- `applyOutdoorActorAiFrameResult` returns `void`.
- Projectile/audio/FX/attack requests are applied directly.
- Build passes.

### Step 5 - Collapse `updateOutdoorActorsForStep`

Remove the current phase-mask interpretation from `updateOutdoorActorsForStep`.

Either delete the function or reduce it to only outdoor-specific inactive/missing-stats handling.

Target:

```cpp
void OutdoorWorldRuntime::updateOutdoorActorsForStep(...)
{
    updateOutdoorMissingStatsActors(...);
    updateOutdoorInactiveActors(...);
}
```

If direct per-actor application handles movement, this function may disappear entirely.

Acceptance:

- No references to `combatFlowsAppliedActorMask`, `combatEngagesAppliedActorMask`, or similar masks remain.

### Step 6 - Delete `OutdoorActorAiFrameApplication`

Delete the struct from `OutdoorWorldRuntime.h`.

Acceptance:

- `rg "OutdoorActorAiFrameApplication"` returns no matches.
- `rg "combatFlowsAppliedActorMask|frameCommitApplyMovementMask|movementEffectiveMoveSpeed"` returns no matches.

### Step 7 - Remove Public Phase Flags From `ActorAiUpdate`

Once outdoor no longer branches on them, remove:

- `statusLockHandled`;
- `combatFlowHandled`;
- `combatEngageHandled`;
- `nonCombatHandled`;
- `frameCommitHandled`;
- `crowdSteeringHandled` if it can be represented as post-movement update kind plus movement intent.

Acceptance:

- `ActorAiUpdate` reads as a domain update, not as internal refactor state.
- Outdoor applies patches and movement intents directly.

### Step 8 - Format The Touched Code

Run the project formatter if one exists. If not, manually clean indentation in the touched outdoor actor AI helpers.

Acceptance:

- No visually broken indentation in `collectOutdoorActorAiFacts`, `applyOutdoorActorAiFrameResult`, or movement helpers.

## Validation

Build:

```bash
cmake --build build --target openyamm -j25
```

Tests:

```bash
ctest --test-dir build --output-on-failure
```

Smoke tests:

- outdoor actor idle/stand;
- outdoor actor wander;
- outdoor actor pursuit;
- outdoor melee attack;
- outdoor ranged attack/projectile spawn;
- actor-vs-actor combat;
- stun/paralyze/fear/blind behavior;
- actor dying/dead transition;
- crowd steering around other actors;
- projectiles/fire spikes still update after actor frame.

## Non-Negotiable Cleanup Rule

Do not preserve the current mask object under a different name.

Bad:

```cpp
OutdoorActorAiFrameApplication2
OutdoorActorAiAppliedState
OutdoorActorAiApplicationMasks
```

Good:

```cpp
for (const ActorAiUpdate &update : result.actorUpdates)
{
    applyOutdoorActorAiUpdate(update, context);
}
```

The goal is to make the actor update path readable, not to hide the current complexity behind another layer.
