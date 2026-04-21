# Shared Actor AI Refactor Wiggum Plan

This document is the authoritative executable plan for the shared actor AI
refactor.

It is designed for repeated autonomous execution. Do not execute it linearly
from top to bottom. Use the task queue section as the executable queue and
update the progress section after every meaningful slice.

## Goal

Make actor AI readable and shared between outdoor and indoor without merging
ODM and BLV world types.

The target architecture is:

```cpp
ActorAiFrameFacts facts = world.collectActorAiFrameFacts(deltaSeconds);
ActorAiFrameResult result = actorAiSystem.updateActors(facts);
world.applyActorAiFrameResult(result);
```

World runtimes collect world facts. Shared actor AI performs the actor loop and
gameplay decisions. World runtimes apply the results to ODM or BLV state.

The shared actor AI pass should read like direct actor behavior, not like a
chain of dozens of tiny decision objects.

## Boundary Rule

Shared actor AI owns what actors decide to do.

Active world owns where actors are, what they can see/reach, how movement
collides, and how AI results are applied to ODM/BLV state.

Do not create another callback wall. Use coarse facts and coarse result packets.

## Non-Goals

- Do not copy OpenEnroth code.
- Do not merge outdoor and indoor actor storage types.
- Do not move terrain, sector, floor, portal, or collision resolution into
  shared gameplay.
- Do not create another callback wall.
- Do not add more tiny public `Input` / `Result` structs to
  `GameplayActorService`.
- Do not make indoor full AI work before outdoor has a readable shared path.
- Do not rewrite all actor behavior at once.

## Current Pain

`OutdoorWorldRuntime::updateMapActors` currently contains most of the real actor
AI frame:

- active actor selection;
- death and dying state;
- spell-effect timers;
- stun/paralyze/fear/blind handling;
- animation timing;
- target selection;
- hostility and party detection;
- attack choice;
- attack start and impact;
- non-combat wander/return-home behavior;
- movement intent;
- outdoor movement and collision;
- crowd steering;
- world item, projectile, and fire spike updates.

`GameplayActorService` contains useful shared rules, but the public API is too
fragmented. The code is mechanically testable, but hard to read because the
gameplay story is split across too many small contracts.

## OpenEnroth Direction

Use the local OpenEnroth checkout only as reference. Do not copy code.

Useful direction:

```cpp
if (outdoor)
{
    build outdoor active actor list;
}
else
{
    build indoor active actor list;
}

update background actors;
for each full-ai actor:
    run common actor AI logic;
```

OpenYAMM should follow the ownership idea, not OE's global/static style.

## Target Ownership

### Shared Gameplay Owns

- actor behavior loop;
- background actor ticking;
- active actor ticking;
- death/dying/stun/paralyze/fear/blind decisions;
- spell-effect timer semantics;
- target choice from supplied target facts;
- hostility and detection changes;
- flee/pursue/stand/wander decisions;
- attack ability choice;
- attack start;
- attack impact decision;
- ranged attack and spell attack requests;
- actor-vs-actor and actor-vs-party combat requests;
- audio/FX intent requests;
- high-level crowd/back-off behavior rules.

### Active World Owns

- actor storage;
- actor list construction;
- actor position/floor/sector facts;
- line-of-sight and detection facts;
- nearby actor facts;
- movement collision and floor resolution;
- applying actor state patches to ODM or BLV runtime state;
- spawning world projectile representation;
- applying world-local audio positions;
- decals and world-specific FX placement;
- render-facing actor synchronization.

## Target Readable Loop

The shared actor AI implementation should read structurally like:

```cpp
ActorAiFrameResult GameplayActorAiSystem::updateActors(const ActorAiFrameFacts &facts)
{
    ActorAiFrameResult result;

    updateBackgroundActors(facts, result);

    for (const ActorAiFacts &actor : facts.activeActors)
    {
        ActorAiUpdate update = updateActor(actor, facts);
        result.actorUpdates.push_back(update);
    }

    return result;
}
```

And per-actor update should read as behavior:

```cpp
ActorAiUpdate GameplayActorAiSystem::updateActor(
    const ActorAiFacts &actor,
    const ActorAiFrameFacts &frame)
{
    if (handleDeath(actor))
    {
        return makeDeathUpdate(actor);
    }

    if (handleStatusLock(actor))
    {
        return makeStatusUpdate(actor);
    }

    ActorTargetFacts target = chooseTarget(actor, frame);

    if (finishAttackIfReady(actor, target))
    {
        return makeAttackImpactUpdate(actor, target);
    }

    if (shouldFlee(actor, target))
    {
        return aiFlee(actor, target);
    }

    if (shouldAttack(actor, target))
    {
        return aiAttack(actor, target);
    }

    if (shouldPursue(actor, target))
    {
        return aiPursue(actor, target);
    }

    return aiStandOrWander(actor);
}
```

Exact method names may change. The main rule is that actor AI reads as actor
behavior.

## Target Data Shape

Use fewer, heavier structs.

```cpp
struct ActorAiFrameFacts
{
    float deltaSeconds = 0.0f;
    float fixedStepSeconds = 0.0f;
    ActorPartyFacts party;
    std::vector<ActorAiFacts> backgroundActors;
    std::vector<ActorAiFacts> activeActors;
};
```

```cpp
struct ActorAiFacts
{
    size_t actorIndex = static_cast<size_t>(-1);
    uint32_t actorId = 0;

    ActorIdentityFacts identity;
    ActorStatsFacts stats;
    ActorRuntimeFacts runtime;
    ActorStatusFacts status;
    ActorTargetFacts target;
    ActorMovementFacts movement;
    ActorWorldFacts world;
};
```

```cpp
struct ActorAiUpdate
{
    size_t actorIndex = static_cast<size_t>(-1);

    ActorStatePatch statePatch;
    ActorAnimationPatch animationPatch;
    ActorMovementIntent movementIntent;

    std::optional<ActorAttackRequest> attackRequest;
    std::vector<ActorWorldEvent> worldEvents;
};
```

```cpp
struct ActorAiFrameResult
{
    std::vector<ActorAiUpdate> actorUpdates;
    std::vector<ActorCombatEvent> combatEvents;
    std::vector<ActorProjectileRequest> projectileRequests;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};
```

Do not split these into dozens of one-purpose public structs unless a real
repeated concept emerges.

## Executable Task Queue

### Step 1 - Freeze the micro-struct direction

- [ ] Audit public structs in `GameplayActorService.h`.
- [ ] Mark in this document which current public micro-struct groups are
  candidates for removal or privatization.
- [ ] Do not add new public micro-decision structs for new actor AI work.
- [ ] Build and run ctest if code changed.
- [ ] Update progress.

Acceptance:

- New actor AI work is required to use coarse frame/update structs.
- Existing tiny structs may remain temporarily.

### Step 2 - Split outdoor actor frame into named phases

- [ ] Audit `OutdoorWorldRuntime::updateMapActors`.
- [ ] Extract behavior-preserving named phase helpers such as:
  `updateActorFrameGlobalEffects`, `selectOutdoorActiveActors`,
  `updateOutdoorBackgroundActors`, `updateOutdoorActiveActors`, and
  `applyActorFrameSideEffects`.
- [ ] Keep behavior unchanged.
- [ ] Do not introduce shared AI yet if the frame is still unreadable.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- `updateMapActors` reads as a frame outline.
- Outdoor behavior remains unchanged.

### Step 3 - Add coarse actor AI facts/result types

- [ ] Add `ActorAiFrameFacts`.
- [ ] Add `ActorAiFacts`.
- [ ] Add `ActorAiUpdate`.
- [ ] Add `ActorAiFrameResult`.
- [ ] Keep types free of outdoor/indoor storage details.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- New types represent actor AI domain facts/results.
- No world representation leaks into shared type names.

### Step 4 - Introduce `GameplayActorAiSystem`

- [ ] Add a shared actor AI system class.
- [ ] Add `updateActors(const ActorAiFrameFacts &facts)`.
- [ ] Implement an initial behavior-readable loop.
- [ ] It may call existing `GameplayActorService` rules internally.
- [ ] Do not expose the current micro-decision API through the new system.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Public API is one frame facts struct and one frame result struct.
- The main loop reads as actor behavior.

### Step 5 - Move outdoor decisions behind shared AI loop

- [ ] Add outdoor fact collection for active/background actors.
- [ ] Call `GameplayActorAiSystem::updateActors` from outdoor actor update.
- [ ] Apply result back to outdoor actor state.
- [ ] Keep outdoor terrain/collision/movement integration outdoor-owned.
- [ ] Preserve crowd steering, target choice, attack starts/impacts, status
  locks, death transitions, spell timers, actor-vs-actor behavior, and
  projectile requests.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Shared actor AI decides behavior.
- Outdoor world applies representation-specific state and movement.
- `OutdoorWorldRuntime::updateMapActors` no longer manually sequences every
  tiny actor rule.

### Step 6 - Demote `GameplayActorService`

- [ ] Move obsolete public micro-decision structs into private implementation
  detail where possible.
- [ ] Keep reusable rule helpers small and named by behavior.
- [ ] Remove or privatize public methods no longer used outside shared AI.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Public actor AI surface is not the old list of micro decisions.
- `GameplayActorService` is a helper, not the main AI frame API.

### Step 7 - Add indoor runtime AI state

- [ ] Audit indoor actor runtime state needs.
- [ ] Add persistent indoor AI state comparable to outdoor where missing:
  AI state, animation state, action timer, recovery/cooldown, idle/pursue/attack
  decision counters, movement intent, attack impact state, detected-party state,
  spell-effect overrides.
- [ ] Keep BLV representation separate from outdoor actor storage.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Indoor can represent shared AI result concepts without pretending BLV actors
  are outdoor actors.

### Step 8 - Implement indoor fact collection

- [ ] Build indoor active actor facts using BLV-specific data.
- [ ] Include distance to party, sector membership, same-sector/portal
  activation, previous detection state, LOS, floor/height facts, and reachable
  target facts.
- [ ] Keep indoor detection/LOS world-owned.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Indoor can produce the same `ActorAiFrameFacts` shape as outdoor.

### Step 9 - Apply shared AI to indoor

- [ ] Indoor calls the same `GameplayActorAiSystem::updateActors` path.
- [ ] Indoor applies AI results to indoor actor runtime state.
- [ ] Indoor applies movement through BLV collision/floor/sector logic.
- [ ] Indoor spawns projectiles/audio/FX through indoor world application.
- [ ] Build and run ctest.
- [ ] Update progress.

Acceptance:

- Outdoor and indoor share actor AI decisions.
- Indoor and outdoor keep separate world representation, movement, collision,
  and rendering.

## Naming Guidance

Prefer behavior names over abstract decision names.

Good:

- `aiStand`;
- `aiStandOrBored`;
- `aiFlee`;
- `aiPursue`;
- `aiWander`;
- `aiStartAttack`;
- `aiFinishAttack`;
- `chooseTarget`;
- `selectActiveActors`.

Avoid for the main public API:

- `ResolveCombatFlowDecisionInput`;
- `CombatEngageApplicationResult`;
- `ActorFrameRouteAction`;
- `ActorFrameCommitInput`;
- `PresentationDecision`;
- `CommandResult`.

Small internal helper structs are fine when they genuinely clarify code. The
primary actor AI must read as actor behavior.

## Wiggum Prompt

Use this prompt for autonomous loop execution:

```text
Read these files first:

- AGENTS.md
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md
- docs/actor_ai_shared_refactor_plan.md

Use docs/actor_ai_shared_refactor_plan.md as the executable plan for this run.

Do not execute the plan linearly. Execute the next unfinished task from the
Executable Task Queue.

Work on one coherent slice. Keep actor behavior unchanged unless fixing a clear
bug. Do not merge indoor/outdoor actor storage or movement/collision logic. Do
not introduce callback bags or adapters that hide ownership. Shared actor AI
owns behavior decisions; active world owns facts and application.

Use the local OpenEnroth checkout only as behavioral/structural reference. Do
not copy code from OpenEnroth.

Run:
- cmake --build build --target openyamm -j25
- ctest --test-dir build --output-on-failure

Update the progress section in docs/actor_ai_shared_refactor_plan.md with
concrete evidence, validation, and remaining work.

Stop only after finishing the current slice and leaving the repo buildable, or
if the progress section records: Hard blocker: YES.
```

## Progress

Current status:

- Overall completion: not complete.
- Current focus: Step 1 - freeze the micro-struct direction.
- Last validated at: not yet validated for this refactor.
- Hard blocker: NO

Done definition satisfied: NO

Validation history:

- None for this refactor yet.

Manual smoke status:

- Not run yet.

## Done Definition

This refactor is done only when:

- shared actor AI owns high-level actor behavior decisions;
- outdoor and indoor produce the same coarse actor AI facts shape;
- outdoor and indoor apply the same coarse actor AI result shape;
- movement, collision, LOS, floor/sector/terrain, and representation-specific
  application remain world-owned;
- `GameplayActorService` is no longer the public micro-decision API for the
  actor frame;
- behavior is validated by build/tests and relevant manual smoke notes;
- this progress section says `Done definition satisfied: YES`.
