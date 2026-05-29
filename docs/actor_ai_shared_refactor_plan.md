# Shared Actor AI Command-Shape Refactor Wiggum Plan

This document is the authoritative executable plan for the shared actor AI
refactor and follow-up command-shape cleanup.

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

Current follow-up goal:

- keep the completed shared `ActorAiFrameFacts -> ActorAiFrameResult` boundary;
- reshape the internals of `GameplayActorAiSystem.cpp` to read like
  `UpdateActorAI + AI_* command helpers`;
- remove private phase leakage from `ActorAiUpdate`;
- keep indoor/outdoor as fact providers and result applicators only.

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

OpenYAMM should also follow OE's readable command naming for state-changing
actor behaviors:

- `AI_Stand`;
- `AI_StandOrBored`;
- `AI_Bored`;
- `AI_RandomMove`;
- `AI_Flee`;
- `AI_Pursue1`;
- `AI_Pursue2`;
- `AI_Pursue3`;
- `AI_MeleeAttack`;
- `AI_MissileAttack1`;
- `AI_MissileAttack2`;
- `AI_SpellAttack1`;
- `AI_SpellAttack2`;
- `AI_CrowdSteer`;
- `AI_CrowdStand`;
- `AI_CrowdRetreat`;
- `AI_CrowdSidestep`;
- `AI_HandleMovementBlock`;
- `AI_DeathOrStatus`;
- `AI_ContinueCurrentAction`.

These names are intentionally not lower camel case because they mirror the
domain vocabulary used by the original actor AI. They are local shared-AI
commands, not public engine API.

`AI_Crowd*` is OpenYAMM-specific rather than OE parity, but it should still be
command-shaped because it mutates actor state and movement outcomes.

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
ActorAiUpdate GameplayActorAiSystem::updateActor(const ActorAiFacts &actor, const ActorAiFrameFacts &frame)
{
    ActorAiCommandContext ai(actor, frame);

    if (AI_DeathOrStatus(ai))
    {
        return ai.finish();
    }

    if (AI_ContinueCurrentAction(ai))
    {
        return ai.finish();
    }

    if (AI_CrowdSteer(ai))
    {
        return ai.finish();
    }

    if (AI_Flee(ai))
    {
        return ai.finish();
    }

    if (AI_AttackOrPursue(ai))
    {
        return ai.finish();
    }

    AI_StandOrBored(ai);
    return ai.finish();
}
```

Exact helper decomposition may change, but state-changing behavior helpers
should use the `AI_*` command names. Small predicates may remain ordinary
behavior-named helpers, but the main actor state transitions should not be
hidden behind `resolve*Input` / `resolve*Result` plumbing.

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

    ActorAiMotionState motionState = ActorAiMotionState::Standing;
    GameplayActorAnimationState animationState = GameplayActorAnimationState::Idle;

    float actionSeconds = 0.0f;
    float recoverySeconds = 0.0f;
    float animationTimeTicks = 0.0f;

    float yawRadians = 0.0f;
    float pitchRadians = 0.0f;

    float moveDirectionX = 0.0f;
    float moveDirectionY = 0.0f;
    float desiredMoveX = 0.0f;
    float desiredMoveY = 0.0f;

    bool applyMotionState = false;
    bool applyAnimationState = false;
    bool applyYaw = false;
    bool clearVelocity = false;
    bool applyMovement = false;
    bool resetAnimationTime = false;
    bool keepCurrentAnimation = false;

    std::optional<ActorAttackRequest> attackRequest;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};
```

```cpp
struct ActorAiFrameResult
{
    std::vector<ActorAiUpdate> actorUpdates;
    std::vector<ActorProjectileRequest> projectileRequests;
    std::vector<ActorAudioRequest> audioRequests;
    std::vector<ActorFxRequest> fxRequests;
};
```

Do not split these into dozens of one-purpose public structs unless a real
repeated concept emerges.

The exact final fields may differ, but they must express semantic outcomes.
They must not expose internal AI phase flags such as:

- `combatFlowHandled`;
- `combatEngageHandled`;
- `nonCombatHandled`;
- `frameCommitHandled`.

If the world needs to know whether movement should be integrated, use
`applyMovement`. If it needs to know whether velocity should be cleared, use
`clearVelocity`. Do not encode which private shared-AI phase produced that
decision.

## Current Follow-Up Pain

The coarse extraction is complete, but readability is still weak:

- `GameplayActorAiSystem.cpp` is large and still contains many state-resolver
  helpers.
- `ActorAiUpdate` still exposes internal phase flags.
- Outdoor application still carries masks named after AI phases.
- The main actor flow is shared, but not yet easy to audit like OE's
  `UpdateActorAI` plus `AI_*` helpers.

This follow-up loop exists to fix that without moving ownership back into
outdoor/indoor code.

## Step 1 Micro-Struct Freeze Audit

`GameplayActorService.h` currently exposes useful shared actor rules, but many
public contracts describe outdoor frame mechanics rather than actor behavior.
New actor AI work must not add more public micro-decision structs to that API.
The replacement direction is `ActorAiFrameFacts`, `ActorAiFacts`,
`ActorAiUpdate`, and `ActorAiFrameResult`.

Candidates for later removal or privatization once `GameplayActorAiSystem`
owns the frame:

- Frame plumbing:
  `ActiveActorUpdateCandidate`, `ActiveActorUpdateSelectionInput`,
  `ActiveActorUpdateSelectionResult`, `ActorFrameRouteInput`,
  `ActorFrameRouteResult`, `ActorFrameTimerInput`, `ActorFrameTimerResult`,
  `ActorAnimationTickInput`, `ActorAnimationTickResult`,
  `ActorMovementBlockInput`, `ActorMovementBlockResult`,
  `ActorFrameCommitInput`, `ActorFrameCommitResult`, `ActorAttackFrameInput`,
  `ActorAttackFrameResult`, `ActorMoveSpeedInput`, `ActorMoveSpeedResult`,
  `ActorStatusFrameInput`, `ActorStatusFrameResult`, `ActorDeathFrameInput`,
  and `ActorDeathFrameResult`.
- Combat sequencing micro-decisions:
  `CombatEngagementInput`, `CombatEngagementResult`,
  `CombatAbilityDecisionInput`, `CombatAbilityDecisionResult`,
  `CombatEngageDecisionInput`, `CombatEngageDecisionResult`,
  `CombatEngageApplicationInput`, `CombatEngageApplicationResult`,
  `CombatFlowDecisionInput`, `CombatFlowDecisionResult`,
  `CombatFlowApplicationInput`, `CombatFlowApplicationResult`,
  `ActorPartyProximityInput`, `ActorPartyProximityResult`,
  `RangedAbilityCommitInput`, `AttackStartInput`, `AttackStartResult`,
  `AttackImpactInput`, and `AttackImpactResult`.
- Target and relation selection plumbing:
  `CombatTargetCandidate`, `CombatTargetInput`, `CombatTargetResult`, and
  `FriendlyTargetEngagementResult`.
- Movement, crowd, idle, and inactive behavior helpers:
  `PursueActionInput`, `PursueActionResult`, `CrowdSteeringState`,
  `CrowdSteeringResult`, `CrowdSteeringEligibilityInput`,
  `IdleBehaviorResult`, `InactiveFidgetResult`,
  `InactiveActorBehaviorInput`, `InactiveActorBehaviorResult`,
  `NonCombatBehaviorInput`, and `NonCombatBehaviorResult`.

Rules that may remain public temporarily because they are reused outside the
actor frame or are not the main AI frame API:

- direct/shared spell impact and spell-effect helper results;
- combat availability and hit-reaction predicates;
- initial timing and small attack-choice helpers used during actor spawn or
  local combat application;
- runtime state structs in `GameplayRuntimeInterfaces.h`, unless later coarse
  AI facts make a narrower public shape possible.

## Executable Task Queue

### Step 10 - Reopen actor AI for command-shape cleanup

- [ ] Treat Steps 1-9 as completed baseline.
- [ ] Audit current `GameplayActorAiSystem.cpp` state-resolver helpers.
- [ ] Map each state-changing resolver to an intended `AI_*` command name.
- [ ] Include OpenYAMM-specific crowd behavior in the command map:
  `AI_CrowdSteer`, `AI_CrowdStand`, `AI_CrowdRetreat`, and
  `AI_CrowdSidestep`.
- [ ] Include death/status/current-action/movement-block state transitions in
  the command map or explicitly classify them as pure helpers.
- [ ] Record any helper that should remain a predicate or math helper instead
  of becoming an `AI_*` command.
- [ ] Do not change behavior in this step unless the change is documentation
  only.
- [ ] Update progress.

Acceptance:

- The first implementation slice has a concrete rename/restructure map.
- The map distinguishes state-changing `AI_*` commands from pure helper
  predicates/math.

A10 audit map, recorded 2026-04-22:

- Death/status/current action:
  `aiHoldDeathState` maps to `AI_DeathOrStatus`; `aiResolveStatusState`
  maps into the status branch of `AI_DeathOrStatus`; `aiContinueAttack`,
  `applyAttackImpactPatch`, and current attack flow in `updateActor` map to
  `AI_ContinueCurrentAction`.
- Movement block:
  `buildPostMovementBlockPatch` plus `updateActorAfterWorldMovementInternal`
  state application maps to `AI_HandleMovementBlock`.
- Stand/bored/random movement:
  `idleStandBehavior`, `applyIdleBehaviorPatch`, `resolveActorNonCombatBehavior`,
  `applyNonCombatBehavior`, `aiStandOrWander`, `aiNonCombat`, and
  `aiNonCombatWithStatusContinuation` map to `AI_Stand`, `AI_Bored`,
  `AI_StandOrBored`, and `AI_RandomMove`. The random-choice math inside
  `resolveIdleBehavior` should remain a pure helper used by `AI_RandomMove`.
- Flee/pursue:
  `resolveSharedCombatFlowApplication` and `applyCombatFlowApplication`
  currently contain blind-wander, flee, and friendly-near-party state changes.
  The flee branch maps to `AI_Flee`; pursuit setup in `applyEngageTargetBehavior`
  plus `resolvePursueAction` maps to `AI_Pursue1`, `AI_Pursue2`, and
  `AI_Pursue3` by direct, short-offset, and wide-offset pursuit modes.
- Attack:
  `applyEngageTargetBehavior` maps attack starts to `AI_MeleeAttack`,
  `AI_MissileAttack1`, `AI_MissileAttack2`, `AI_SpellAttack1`, and
  `AI_SpellAttack2` according to chosen ability and ranged/spell constraints.
  `startAttack` and `finishAttackImpact` should remain pure patch builders
  until the command context exists.
- Crowd:
  `applyPostMovementCrowdSteering` maps to `AI_CrowdSteer`;
  `applyCrowdStandPatch` maps to `AI_CrowdStand`; `applyCrowdMovePatch` maps
  to `AI_CrowdRetreat` when called with `retreat = true` and
  `AI_CrowdSidestep` otherwise. `resolveCrowdSteering`, `buildCrowdSteeringState`,
  `shouldApplyCrowdSteering`, and `applyCrowdSteeringStatePatch` should remain
  pure or low-level state-copy helpers during Step 15.
- Pure helpers to keep non-`AI_*` for now:
  angle/length math, deterministic decision-seed helpers, attack ability
  predicates, target-state builders, engagement predicate construction,
  timer aging helpers, animation tick aging, attack damage/profile builders,
  target selection, and enum-to-state mapping helpers.

### Step 11 - Introduce actor AI command context

- [x] Add a private `ActorAiCommandContext` or equivalent local helper in
  `GameplayActorAiSystem.cpp`.
- [x] The context owns one mutable `ActorAiUpdate`.
- [x] It exposes small operations for setting motion, animation, timers, yaw,
  movement, attack/audio/FX requests, and crowd intent.
- [x] Keep the context file-local/private.
- [x] Do not expose the context through public headers.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- New `AI_*` commands can write semantic actor outcomes without returning tiny
  resolver structs.
- Public actor AI API remains `ActorAiFrameFacts -> ActorAiFrameResult`.

### Step 12 - Rename and reshape death/status/current-action commands

- [x] Convert death and dying state-changing helpers to `AI_DeathOrStatus` or
  narrower `AI_*` commands if clearer.
- [x] Convert stun/paralyze/status-lock state-changing helpers to command-shaped
  helpers.
- [x] Convert current attack continuation / completed attack handling to
  `AI_ContinueCurrentAction`.
- [x] Convert post-movement block fallout to `AI_HandleMovementBlock`.
- [x] Preserve death, stun, paralyze, current attack, and movement-block
  behavior.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Death/status/current-action/movement-block behavior no longer relies on
  state-changing resolver-shaped helpers.
- No new public micro-decision structs are introduced.

### Step 13 - Rename and reshape stand/bored/random movement commands

- [x] Convert stand/bored/non-combat state-changing helpers to `AI_Stand`,
  `AI_Bored`, `AI_StandOrBored`, and `AI_RandomMove` where applicable.
- [x] Keep pure helpers as predicates/math with behavior names.
- [x] Allow limited duplication if it improves readability.
- [x] Preserve outdoor and indoor behavior.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Non-combat actor behavior reads as explicit `AI_*` commands.
- No new public micro-decision structs are introduced.

### Step 14 - Rename and reshape flee/pursue/attack commands

- [x] Convert flee/pursue state-changing helpers to `AI_Flee`, `AI_Pursue1`,
  `AI_Pursue2`, and `AI_Pursue3` where applicable.
- [x] Convert attack state-changing helpers to `AI_MeleeAttack`,
  `AI_MissileAttack1`, `AI_MissileAttack2`, `AI_SpellAttack1`, and
  `AI_SpellAttack2` where applicable.
- [x] Keep target selection, LOS facts, movement collision, and world
  application world-owned.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Combat behavior reads as explicit `AI_*` commands.
- Attack requests and projectile requests remain shared result outputs.
- Outdoor/indoor do not regain behavior decision ownership.

### Step 15 - Rename and reshape crowd commands

- [x] Convert post-movement crowd steering to `AI_CrowdSteer`.
- [x] Split state-changing crowd outcomes into `AI_CrowdStand`,
  `AI_CrowdRetreat`, and `AI_CrowdSidestep` where it improves readability.
- [x] Keep crowd probe/no-progress math as pure helpers if that is clearer.
- [x] Preserve current OpenYAMM crowd behavior, including brief sidestep/retreat,
  stand/bored fallback, side lock, and no-progress counters.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Crowd behavior reads as explicit OpenYAMM `AI_Crowd*` commands.
- Crowd movement/collision facts remain world-owned.

### Step 16 - Remove phase flags from `ActorAiUpdate`

- [x] Remove `combatFlowHandled`, `combatEngageHandled`, `nonCombatHandled`,
  and `frameCommitHandled` from `ActorAiUpdate`.
- [x] Replace outdoor/indoor application checks with semantic outcome checks:
  state present, movement present, attack request present, audio/FX present,
  or apply-movement flag.
- [x] Rename any remaining outdoor masks that are phase-named to semantic
  application data or remove them if no longer needed.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- World application no longer depends on private AI phase markers.
- The result shape describes what happened, not which internal branch handled
  it.

### Step 17 - Main active actor flow readability pass

- [x] Rewrite the private active actor update outline so it reads as behavior:
  death/status, current action continuation, target selection, crowd steer if
  applicable, fear/flee, attack/pursue, non-combat stand/random move.
- [x] Keep comments sparse and only where control flow is non-obvious.
- [x] Remove obsolete `resolve*` state-resolver names that were replaced by
  `AI_*` commands.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- A reviewer can follow one actor update without tracking a chain of tiny
  resolver result packets.
- `rg` shows no main-frame state-changing helper still named as a
  `resolve*Decision` / `resolve*Application` pair.

### Step 18 - Smoke and profiler guard

- [x] Run the documented build and ctest.
- [x] Run available indoor/dialogue headless smoke if feasible.
- [x] Re-check `gprof.txt` if the user provides a new profile.
- [x] Record manual smoke requests for outdoor hostile pursuit, melee/ranged
  attack, actor-vs-actor, crowd steering, death, and indoor actor movement if
  interactive testing is needed.
- [x] Update progress and root acceptance.

Acceptance:

- Behavior remains equivalent.
- No obvious performance regression is introduced.
- Done definition is updated only after evidence is recorded.

### Step 1 - Freeze the micro-struct direction

- [x] Audit public structs in `GameplayActorService.h`.
- [x] Mark in this document which current public micro-struct groups are
  candidates for removal or privatization.
- [x] Do not add new public micro-decision structs for new actor AI work.
- [x] Build and run ctest if code changed.
- [x] Update progress.

Acceptance:

- New actor AI work is required to use coarse frame/update structs.
- Existing tiny structs may remain temporarily.

### Step 2 - Split outdoor actor frame into named phases

- [x] Audit `OutdoorWorldRuntime::updateMapActors`.
- [x] Extract behavior-preserving named phase helpers such as:
  `updateActorFrameGlobalEffects`, `selectOutdoorActiveActors`,
  `updateOutdoorActorsForStep`, and `applyActorFrameSideEffects`.
- [x] Keep behavior unchanged.
- [x] Do not introduce shared AI yet if the frame is still unreadable.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- `updateMapActors` reads as a frame outline.
- Outdoor behavior remains unchanged.

### Step 3 - Add coarse actor AI facts/result types

- [x] Add `ActorAiFrameFacts`.
- [x] Add `ActorAiFacts`.
- [x] Add `ActorAiUpdate`.
- [x] Add `ActorAiFrameResult`.
- [x] Keep types free of outdoor/indoor storage details.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- New types represent actor AI domain facts/results.
- No world representation leaks into shared type names.

### Step 4 - Introduce `GameplayActorAiSystem`

- [x] Add a shared actor AI system class.
- [x] Add `updateActors(const ActorAiFrameFacts &facts)`.
- [x] Implement an initial behavior-readable loop.
- [x] It may call existing `GameplayActorService` rules internally.
- [x] Do not expose the current micro-decision API through the new system.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Public API is one frame facts struct and one frame result struct.
- The main loop reads as actor behavior.

### Step 5 - Move outdoor decisions behind shared AI loop

- [x] Add outdoor fact collection for active/background actors.
- [x] Call `GameplayActorAiSystem::updateActors` from outdoor actor update.
- [x] Apply result back to outdoor actor state.
- [x] Keep outdoor terrain/collision/movement integration outdoor-owned.
- [x] Preserve crowd steering, target choice, attack starts/impacts, status
  locks, death transitions, spell timers, actor-vs-actor behavior, and
  projectile requests.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Shared actor AI decides behavior.
- Outdoor world applies representation-specific state and movement.
- `OutdoorWorldRuntime::updateMapActors` no longer manually sequences every
  tiny actor rule.

### Step 6 - Demote `GameplayActorService`

- [x] Move obsolete public micro-decision structs into private implementation
  detail where possible.
- [x] Keep reusable rule helpers small and named by behavior.
- [x] Remove or privatize public methods no longer used outside shared AI.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Public actor AI surface is not the old list of micro decisions.
- `GameplayActorService` is a helper, not the main AI frame API.

### Step 7 - Add indoor runtime AI state

- [x] Audit indoor actor runtime state needs.
- [x] Add persistent indoor AI state comparable to outdoor where missing:
  AI state, animation state, action timer, recovery/cooldown, idle/pursue/attack
  decision counters, movement intent, attack impact state, detected-party state,
  spell-effect overrides.
- [x] Keep BLV representation separate from outdoor actor storage.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Indoor can represent shared AI result concepts without pretending BLV actors
  are outdoor actors.

### Step 8 - Implement indoor fact collection

- [x] Build indoor active actor facts using BLV-specific data.
- [x] Include distance to party, sector membership, same-sector/portal
  activation, previous detection state, LOS, floor/height facts, and reachable
  target facts.
- [x] Keep indoor detection/LOS world-owned.
- [x] Build and run ctest.
- [x] Update progress.

Acceptance:

- Indoor can produce the same `ActorAiFrameFacts` shape as outdoor.

### Step 9 - Apply shared AI to indoor

- [x] Indoor calls the same `GameplayActorAiSystem::updateActors` path.
- [x] Indoor applies AI results to indoor actor runtime state.
- [x] Indoor applies movement through BLV collision/floor/sector logic.
- [x] Indoor spawns projectiles/audio/FX through indoor world application.
- [x] Build and run ctest.
- [x] Update progress.

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

- Overall completion: command-shape cleanup reopened after the coarse shared actor AI extraction completed.
- Current focus: actor AI command-shape cleanup closure.
- Last validated at: 2026-04-22, actor AI A18 smoke/profiler guard.
- Hard blocker: NO

Done definition satisfied: YES

Validation history:

- 2026-04-22: Completed Step 18 / A18. `cmake --build build --target openyamm -j25` completed successfully, and
  `ctest --test-dir build --output-on-failure` completed successfully with no registered tests in the current build
  tree.
- 2026-04-22: A18 headless validation passed: `timeout 300s build/game/openyamm --headless-run-regression-suite
  indoor` completed with `passed=21 failed=0`, and `timeout 300s build/game/openyamm --headless-run-regression-suite
  dialogue` completed with `passed=242 failed=0`.
- 2026-04-22: A18 actor smoke coverage in the dialogue suite included friendly idle/wander, hostile pursuit, melee
  attack entry, mixed ranged choice/release/projectile hit, actor-vs-actor hostile damage, attack
  persistence/recovery, actor death, corpse loot, and death audio. No separate interactive play session was run.
- 2026-04-22: A18 static command-shape audit found all expected private `AI_*` helpers in
  `GameplayActorAiSystem.cpp`, and found no remaining internal phase flags or obsolete
  `resolve*Decision` / `resolve*Application` / `CombatEngage*` state-resolver names in the actor AI/runtime paths.
  The documented pure `resolveCrowdSteering` crowd probe/no-progress helper remains, while state-changing crowd
  outcomes route through `AI_CrowdSteer`, `AI_CrowdStand`, `AI_CrowdRetreat`, and `AI_CrowdSidestep`.
- 2026-04-22: A18 profiler guard checked the local profile files. No new profile was provided during this slice.
  The latest `gprof.txt` is stale relative to current helper names, but its flat profile still places actor AI work
  below render/texture/bgfx and world-fact hot spots; `gprof_combat.txt` shows `OutdoorWorldRuntime::updateMapActors`
  at 1.25% self time. No obvious actor AI command-shape performance regression is indicated by the available profiles.
- 2026-04-22: Completed Step 17 / A17. `GameplayActorAiSystem.cpp` now routes the private active actor update through
  a behavior-ordered outline: death/status first, target selection, `AI_ActiveCurrentAction` for in-progress attacks,
  then `AI_ActiveBehavior` for combat-flow fear/flee/blind/friendly-near-party, attack/pursue, and non-combat
  stand/bored/random movement fallback. Post-world-movement crowd steering remains in the world-movement follow-up
  path where collision/contact facts exist.
- 2026-04-22: Removed the obsolete private combat-engage state resolver/application pair. Attack ability selection is
  now `chooseCombatAbility`, engage selection is `chooseCombatEngagePlan`, and static `rg` shows no
  `resolve*Decision`, `resolve*Application`, `CombatEngageDecision*`, or `CombatEngageApplication*` names remaining
  in `GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A17.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A17; no tests were found in
  the current build tree.
- 2026-04-22: Focused headless dialogue smoke passed after A17:
  `friendly_actor_can_idle_wander`, `party_attack_on_actor_3_causes_wimp_flee`,
  `hostile_melee_actor_uses_side_pursuit_when_far`,
  `hostile_melee_actor_uses_direct_pursuit_when_close`, `hostile_actor_enters_attack_state`,
  `mixed_actor_53_ranged_release_spawns_arrow_projectile`, and
  `pirate_and_lizardman_hostile_actors_damage_each_other`.
- 2026-04-22: `timeout 300s build/game/openyamm --headless-run-regression-suite indoor` completed successfully after
  A17 with `passed=21 failed=0`.
- 2026-04-22: Completed Step 16 / A16. `ActorAiUpdate` no longer exposes `combatFlowHandled`,
  `combatEngageHandled`, `nonCombatHandled`, or `frameCommitHandled`; static `rg` over `game/` shows no remaining
  references to those internal phase flags.
- 2026-04-22: Outdoor result application now consumes semantic outcome data: `behaviorAppliedActorMask`, desired
  movement, melee pursuit state, animation keep/reset, crowd reset, velocity clear, and apply-movement masks. The old
  combat-flow, combat-engage, non-combat, and frame-commit outdoor masks were removed or renamed. Indoor movement
  application now keys directly off `ActorMovementIntent::applyMovement`.
- 2026-04-22: Movement integration and collision remain world-owned. Shared AI only emits state, animation, movement,
  attack, audio, and FX outcomes; outdoor and indoor still apply those outcomes to their own actor representations.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A16.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A16; no tests were found in
  the current build tree.
- 2026-04-22: Focused headless dialogue smoke passed after A16:
  `hostile_melee_actor_uses_side_pursuit_when_far`,
  `hostile_melee_actor_far_pursuit_accumulates_motion`,
  `hostile_melee_actor_uses_direct_pursuit_when_close`, `hostile_actor_enters_attack_state`,
  `mixed_actor_53_ranged_release_spawns_arrow_projectile`, `friendly_actor_can_idle_wander`, and
  `party_attack_on_actor_3_causes_wimp_flee`.
- 2026-04-22: `timeout 300s build/game/openyamm --headless-run-regression-suite indoor` completed successfully after
  A16 with `passed=21 failed=0`.
- 2026-04-22: Completed Step 15 / A15. Post-world-movement crowd steering now routes through private
  `AI_CrowdSteer`; state-changing crowd outcomes now apply through `AI_CrowdStand`, `AI_CrowdRetreat`, and
  `AI_CrowdSidestep` using `ActorAiCommandContext`.
- 2026-04-22: Crowd probe/no-progress decision math remains in pure helpers, while shared AI still owns brief
  sidestep/retreat, stand/bored fallback, side lock, no-progress counters, and pursuit-decision count updates. Outdoor
  remains the movement/collision fact provider and result applicator.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A15.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A15; no tests were found in
  the current build tree.
- 2026-04-22: Focused headless dialogue smoke passed after A15:
  `hostile_melee_actor_uses_side_pursuit_when_far`, `hostile_melee_actor_far_pursuit_accumulates_motion`, and
  `hostile_melee_actor_uses_direct_pursuit_when_close`.
- 2026-04-22: Completed Step 14 / A14. Combat-flow flee behavior now routes through private `AI_Flee`, and pursuit
  starts now route through private `AI_Pursue1`, `AI_Pursue2`, and `AI_Pursue3` by direct, short-offset, and
  wide-offset pursuit mode.
- 2026-04-22: Attack starts now route through private `AI_MeleeAttack`, `AI_MissileAttack1`,
  `AI_MissileAttack2`, `AI_SpellAttack1`, and `AI_SpellAttack2` wrappers using `ActorAiCommandContext`. Target
  selection, LOS facts, movement collision, projectile request output, and world application ownership were unchanged.
- 2026-04-22: Removed the private state-changing `resolveSharedCombatFlowApplication` /
  `applyCombatFlowApplication` and `applyEngageTargetBehavior` plumbing. The remaining combat ability, engagement,
  pursue-action, and attack timing helpers stay pure decision/math builders.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A14.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A14; no tests were found in
  the current build tree.
- 2026-04-22: Focused headless dialogue smoke passed after A14:
  `party_attack_on_actor_3_causes_wimp_flee`, `hostile_melee_actor_uses_side_pursuit_when_far`,
  `hostile_melee_actor_uses_direct_pursuit_when_close`, `hostile_actor_enters_attack_state`,
  `mixed_actor_53_pursues_and_can_choose_ranged_attack`, and
  `mixed_actor_53_ranged_release_spawns_arrow_projectile`.
- 2026-04-22: Completed Step 13 / A13. Non-combat stand, bored, idle random-wander, continue-wander, and return-home
  state changes now flow through private `AI_Stand`, `AI_Bored`, `AI_StandOrBored`, and `AI_RandomMove` commands using
  `ActorAiCommandContext`.
- 2026-04-22: Removed the private `ActorNonCombatAction` / `ActorNonCombatPatch` resolver packet and the
  `resolveActorNonCombatBehavior` / `applyIdleBehaviorPatch` / `applyNonCombatBehavior` plumbing. The deterministic
  idle-choice helpers remain pure, and no public actor AI API shape changed.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A13.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A13; no tests were found in
  the current build tree.
- 2026-04-22: Focused headless dialogue smoke passed after A13:
  `friendly_actor_can_idle_wander` and `friendly_actor_3_cycles_idle_and_walk`.
- 2026-04-22: Completed Step 12 / A12. Death and dying state mutations now flow through private
  `AI_DeathOrStatus` / `AI_ApplyDeathState` commands using `ActorAiCommandContext`; stun, paralyze, recovered stun,
  and status-timer continuation now flow through `AI_ApplyStatusState` while preserving the existing continuation
  path for expired status timers.
- 2026-04-22: Current attack continuation now starts from private `AI_ContinueCurrentAction`, and post-world-movement
  blocked movement fallout now flows through `AI_HandleMovementBlock`. The remaining frame commit and combat/noncombat
  phase flags are intentionally left for A16/A17.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A12.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A12; no tests were found in
  the current build tree.
- 2026-04-22: Completed Step 11 / A11. `GameplayActorAiSystem.cpp` now has a file-local
  `ActorAiCommandContext` that owns one mutable `ActorAiUpdate`; `makeActorUpdate` uses it as the construction point
  while public actor AI headers remain unchanged.
- 2026-04-22: The private context exposes semantic operations for motion, animation, timers, yaw, movement intent,
  velocity clearing, crowd intent, attack/projectile attack requests, audio requests, and FX requests. It also
  supports optional frame access for active-frame commands, preparing the A12-A15 `AI_*` conversions without adding
  new public micro-decision structs.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A11.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A11; no tests were found in
  the current build tree.
- 2026-04-22: Completed Step 10 / A10 as an audit-only command-shape slice. The current
  `GameplayActorAiSystem.cpp` state-changing helpers are now mapped above to the intended private `AI_*` commands:
  death/status/current-action/movement-block, stand/bored/random move, flee/pursue/attack, and OpenYAMM-specific
  crowd behavior.
- 2026-04-22: A10 classified pure helpers that should stay non-`AI_*` for now, including math, deterministic decision
  seeds, predicates, target and engagement fact builders, timer/animation aging, attack damage builders, target
  selection, and enum-to-state conversion helpers.
- 2026-04-22: No runtime behavior code changed in A10; the slice updated `TASK_QUEUE.md`, `PROGRESS.md`, and this
  progress section with the concrete map for the later command-context and helper-conversion steps.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after A10.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after A10; no tests were found in
  the current build tree.
- 2026-04-22: Reopened the actor AI refactor loop for command-shape cleanup. The target is to keep the completed
  shared `ActorAiFrameFacts -> ActorAiFrameResult` world boundary while reshaping `GameplayActorAiSystem.cpp` so
  state-changing behavior helpers use OE-shaped `AI_*` command names. This is documentation/planning only; no code
  behavior was changed in this slice.
- 2026-04-22: Expanded the command-shape cleanup plan to include OpenYAMM-specific crowd behavior and other
  state-changing families that were missing from the first pass. The executable queue now includes
  `AI_CrowdSteer`, `AI_CrowdStand`, `AI_CrowdRetreat`, `AI_CrowdSidestep`, `AI_HandleMovementBlock`,
  `AI_DeathOrStatus`, and `AI_ContinueCurrentAction` alongside the OE-shaped stand/flee/pursue/attack commands.
  This was documentation/planning only; no runtime code changed.

- 2026-04-22: Acceptance follow-up fixed legacy outdoor companion lookup outside actor AI ownership.
  `MapAssetLoader` now resolves staged legacy DDM companions from `_legacy/map_delta` after checking `Data/games`,
  allowing `outdoor_scene_yml_matches_legacy_ddm_authored_state` to compare scene-YML state against legacy state for
  Out01, Out02, Out05, and Out13.
- 2026-04-22: Acceptance follow-up changed the focused `app_background_music_follows_selected_map` diagnostic outside
  actor AI ownership to initialize runtime-only after renderer shutdown; that case checks selected-map music track
  state and does not need render-facing outdoor view assets.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the legacy companion/music
  diagnostic follow-up slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the legacy companion/music
  diagnostic follow-up slice; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions passed after the follow-up slice:
  `outdoor_scene_yml_matches_legacy_ddm_authored_state` and `app_background_music_follows_selected_map`. Actor AI
  manual smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue root acceptance remains open: a
  broad run before the music diagnostic adjustment passed the relevant actor smoke and scene-YML parity cases, then
  exited 139 in the following headless audio/view initialization area.
- 2026-04-22: Acceptance follow-up stabilized the focused treasure-spawn diagnostic outside actor AI ownership. The
  synthetic case now uses high ordinary treasure-map conditions and a small batch of added treasure spawns so it no
  longer depends on a rare-only/no-materialized-item outcome.
- 2026-04-22: Acceptance follow-up fixed the focused speech-audio headless crash outside actor AI ownership. The
  speech-audio diagnostics now initialize runtime-only after renderer shutdown instead of allocating HUD/view textures
  through bgfx in a headless no-renderer path.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the diagnostic stabilization
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the diagnostic stabilization
  slice; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions passed after the diagnostic stabilization slice:
  `treasure_spawn_points_materialize_world_items_on_first_outdoor_load`,
  `spellbook_speech_audio_resolves_for_success_failure_and_store_closed`,
  `damage_speech_audio_resolves_for_all_default_seed_members`, and
  `damage_speech_audio_resolves_for_roster_seeded_party_members`. Actor AI manual smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue rerun passed the previously
  residual actor/projectile smoke and speech-audio cases, but root acceptance remains open because
  `outdoor_scene_yml_matches_legacy_ddm_authored_state` fails and the process exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up fixed the focused CanShowTopic killed-context diagnostic. The change is outside
  actor AI ownership: the synthetic CanShowTopic script now checks actor-id kill policy for actor 8, matching the
  diagnostic setup that kills actor 8.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the CanShowTopic diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the CanShowTopic diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regression
  `OPENYAMM_REGRESSION_FILTER=event_can_show_topic_actor_killed_uses_scene_context timeout 120s
  build/game/openyamm --headless-run-regression-suite dialogue` passed with `passed=1 failed=0`. Actor AI manual
  smoke remains pending.
- 2026-04-22: Indoor headless suite passed with `passed=21 failed=0`. Full dialogue rerun still passed relevant actor
  smoke cases, but root acceptance remains open because treasure-spawn materialization still fails and the process
  exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up fixed the focused spell-backend coverage diagnostic. The change is outside actor AI
  ownership: Fire Aura and Vampiric Weapon coverage now supplies an equipped common weapon item target, Recharge Item
  requests inventory-item selection, and utility-target spells without an action report `NeedUtilityUi` instead of
  falling through to a generic failure.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the spell-backend diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the spell-backend diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regression
  `OPENYAMM_REGRESSION_FILTER=party_spell_backend_supports_all_defined_non_utility_spells timeout 120s
  build/game/openyamm --headless-run-regression-suite dialogue` passed with `passed=1 failed=0`. Actor AI manual smoke
  remains pending; root acceptance remains open for full-suite dialogue/audio follow-up and manual smoke.
- 2026-04-22: Acceptance follow-up fixed the focused outdoor party water-boundary diagnostic. The change is outside
  actor AI ownership: the synthetic diagnostic now computes water/land tile centers through `outdoorGridCornerWorldX/Y`,
  and party movement allows already-airborne water crossing while keeping grounded no-water-walk blocking intact.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the water-boundary diagnostic
  fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the water-boundary diagnostic
  fix; no tests were found in the current build tree.
- 2026-04-22: Focused dialogue regressions for
  `party_airborne_movement_allows_water_entry_without_water_walk` and
  `party_ground_movement_blocks_water_entry_without_water_walk` both passed with `passed=1 failed=0`. Actor AI manual
  smoke remains pending; root acceptance remains open for unrelated residual dialogue diagnostics and full-suite audio
  decode exit 139.
- 2026-04-22: Acceptance follow-up fixed the residual outdoor corpse-loot diagnostic by making
  `OutdoorWorldRuntime::openMapActorCorpseView` reject invisible actors. After the last corpse item is taken,
  `takeActiveCorpseItem` clears the cached corpse view and marks the actor invisible; reopening now correctly fails
  instead of rebuilding loot from monster stats.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the corpse-loot fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the corpse-loot fix; no tests
  were found in the current build tree.
- 2026-04-22: Focused dialogue regression
  `OPENYAMM_REGRESSION_FILTER=world_actor_death_generates_corpse_loot timeout 120s build/game/openyamm
  --headless-run-regression-suite dialogue` passed with `passed=1 failed=0`.
- 2026-04-22: Full dialogue headless rerun now passes `world_actor_death_generates_corpse_loot` plus relevant actor
  smoke cases including friendly idle/wander, hostile pursuit, melee attack entry, ranged release/party hit,
  actor-vs-actor hostility, attack persistence, post-attack recovery, and actor death audio. Root acceptance remains
  open because treasure spawn materialization, airborne water entry, Fire Aura backend coverage, and CanShowTopic
  killed-context diagnostics still fail, then the process exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up static audit reran `rg` checks. Outdoor and indoor still collect
  `ActorAiFrameFacts`, call `GameplayActorAiSystem::updateActors`, and apply `ActorAiFrameResult`.
- 2026-04-22: Acceptance follow-up static audit found no remaining references to the audited old public actor-frame
  micro-decision names in `GameplayActorService.h`, `game/outdoor`, or `game/indoor`, including `ActorFrameRoute`,
  `ActorFrameTimer`, `ActorAnimationTick`, `ActorMovementBlock`, `ActorFrameCommit`, `ActorStatusFrame`, old
  attack-start/impact packets, old combat-flow packets, old non-combat packets, and old combat target/engagement
  packets.
- 2026-04-22: Acceptance follow-up reran `cmake --build build --target openyamm -j25`; the build completed
  successfully.
- 2026-04-22: Acceptance follow-up reran `ctest --test-dir build --output-on-failure`; CTest completed successfully
  and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke coverage passed
  again, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence when the party moves away,
  post-attack recovery, and actor death audio.
- 2026-04-22: Root acceptance remains open. The dialogue suite still reports residual failures for airborne water
  entry, Fire Aura backend coverage, actor-killed topic context, and corpse loot reopening, then exits 139 after audio
  decode errors.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up documentation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke coverage passed in
  the log, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence when the party moves away,
  post-attack recovery, and actor death audio.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures for
  airborne water entry, Fire Aura backend coverage, actor-killed topic context, and corpse loot reopening, then exits
  139.
- 2026-04-22: Static `rg` audit reconfirmed that outdoor and indoor collect `ActorAiFrameFacts`, call
  `GameplayActorAiSystem::updateActors`, and apply `ActorAiFrameResult`; audited old public actor-frame
  micro-decision names remain absent from `GameplayActorService.h`, `game/outdoor`, and `game/indoor`.
- 2026-04-22: Current acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Current acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Current acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Current acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke coverage passed in
  the log, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence when the party moves away,
  post-attack recovery, and actor death audio.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures for
  airborne water entry, Fire Aura backend coverage, actor-killed topic context, and corpse loot reopening, then exits
  139 after repeated audio decode errors.
- 2026-04-22: Current static `rg` audit reconfirmed that outdoor and indoor collect `ActorAiFrameFacts`, call
  `GameplayActorAiSystem::updateActors`, and apply `ActorAiFrameResult`.
- 2026-04-22: Current static `rg` audit found no remaining references to the audited old public actor-frame
  micro-decision names in `GameplayActorService.h`, `game/outdoor`, or `game/indoor`, including `ActorFrameRoute`,
  `ActorFrameTimer`, `ActorAnimationTick`, `ActorMovementBlock`, `ActorFrameCommit`, `ActorStatusFrame`, old
  attack-start/impact packets, old combat-flow packets, old non-combat packets, and old combat target/engagement
  packets.
- 2026-04-22: Acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke cases still passed
  in the log, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence, post-attack recovery, and actor death
  audio.
- 2026-04-22: Root acceptance remains open. The dialogue suite now reports residual failures for airborne water entry,
  Fire Aura backend coverage, actor-killed topic context, and corpse loot reopening, then exits 139 after repeated
  audio decode errors. The earlier treasure-spawn case passed in this run.
- 2026-04-22: Acceptance follow-up reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke coverage passed
  again in the log, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence, and actor death audio.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it still reports residual failures for
  treasure spawn materialization, airborne water entry, Fire Aura backend coverage, actor-killed topic context, and
  corpse loot reopening, then exits 139 after audio decode errors.
- 2026-04-22: Acceptance follow-up validation slice reran
  `cmake --build build --target openyamm -j25`; the build completed successfully.
- 2026-04-22: Acceptance follow-up validation slice reran
  `ctest --test-dir build --output-on-failure`; CTest completed successfully and still reports no registered tests.
- 2026-04-22: Acceptance follow-up validation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite indoor`; the indoor suite completed successfully
  with `passed=21 failed=0`.
- 2026-04-22: Acceptance follow-up validation slice reran
  `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue`. Relevant actor smoke coverage passed
  again, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack choice/release/party
  hit, actor-vs-actor hostile damage, attack persistence when the party moves away, post-attack recovery, and actor
  death audio.
- 2026-04-22: The dialogue suite remains non-clean acceptance evidence because it reports residual failures for
  treasure spawn materialization, airborne water entry, Fire Aura backend coverage, actor-killed topic context, and
  corpse loot reopening, then exits 139 after repeated audio decode errors.
- 2026-04-22: Fixed an acceptance-follow-up regression where shared outdoor attack-start updates were applied to
  `MapActorState`, then overwritten back to standing by the later outdoor actor body. Attack-start updates now also
  populate the combat-engage application mask, so the outdoor-owned movement/body pass preserves the shared-applied
  attacking state and animation.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the attack-start
  preservation fix.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the attack-start preservation
  fix; no tests were found in the current build tree.
- 2026-04-22: `build/game/openyamm --headless-run-regression-suite indoor` completed successfully during acceptance
  follow-up and reported `passed=21 failed=0`.
- 2026-04-22: Re-ran `timeout 300s build/game/openyamm --headless-run-regression-suite dialogue` after the fix.
  The actor-refactor cases for hostile attack start, mixed ranged attack choice/release/party hit, actor-vs-actor
  hostile damage, attack persistence, and post-attack recovery now pass.
- 2026-04-22: The dialogue suite still is not full acceptance evidence. It reported residual failures outside this
  attack-start preservation fix for treasure spawn materialization, airborne water entry, Fire Aura backend coverage,
  actor-killed topic context, and corpse loot reopening, then exited with code 139 after repeated audio decode errors.
- 2026-04-22: Final actor AI acceptance audit confirmed with static `rg` that outdoor and indoor collect
  `ActorAiFrameFacts`, call `GameplayActorAiSystem::updateActors`, and apply `ActorAiFrameResult`.
- 2026-04-22: Static `rg` audit found no remaining references to the audited old public actor-frame
  micro-decision names in `GameplayActorService.h`, `game/outdoor`, or `game/indoor`, including
  `ActorFrameRoute`, `ActorFrameTimer`, `ActorAnimationTick`, `ActorMovementBlock`, `ActorFrameCommit`,
  `ActorStatusFrame`, old attack-start/impact packets, old combat-flow packets, old non-combat packets, and old
  combat target/engagement packets.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully during the final actor AI
  acceptance audit slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully during the final actor AI
  acceptance audit slice; no tests were found in the current build tree.
- 2026-04-22: Attempted extra headless validation with
  `build/game/openyamm --headless-run-regression-suite dialogue`. The run passed many relevant actor cases before it
  could be treated as acceptance evidence, including friendly idle/wander, hostile pursuit, ranged projectile release,
  actor-vs-actor hostility, and actor death/audio cases.
- 2026-04-22: The extra dialogue regression suite did not complete cleanly: it reported
  `party_airborne_movement_allows_water_entry_without_water_walk` as failed, then stopped producing output after the
  later outdoor geometry case and was interrupted. This is recorded as pending follow-up and not counted as passing
  acceptance evidence.
- 2026-04-22: Continued Step 9 by adding indoor BLV face/world projectile collision to
  `IndoorWorldRuntime::updateIndoorProjectiles`. Indoor now builds mechanism-adjusted face geometry, tests the
  projectile motion segment against non-portal touchable BLV faces, and feeds the nearest face hit to shared
  projectile service as `ProjectileFrameCollisionKind::World`.
- 2026-04-22: Indoor projectile collision ordering now lets BLV face hits, party hits, and actor hits compete by
  segment progress before `GameplayProjectileService::updateProjectileFrame` resolves impact behavior. Indoor still
  owns BLV geometry, mechanism-adjusted vertices, actor/party damage application, audio queueing, and impact FX.
- 2026-04-22: Static audit shows the new indoor projectile face collision helpers and world-fact wiring:
  `findProjectileIndoorFaceHit`, `indoorSegmentMayTouchFaceBounds`,
  `buildIndoorMechanismAdjustedVertices`, and `ProjectileFrameCollisionKind::World` in
  `game/indoor/IndoorWorldRuntime.cpp`.
- 2026-04-22: Line-length audit with `awk` found no lines over 120 characters in
  `game/indoor/IndoorWorldRuntime.cpp` after the Step 9 indoor BLV face/world projectile collision slice.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor BLV
  face/world projectile collision slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor BLV
  face/world projectile collision slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor BLV face/world projectile collision slice; validation was
  limited to build, ctest, static audit, and line-length audit.
- 2026-04-22: Continued Step 9 by exposing indoor projectile presentation packets through
  `IndoorWorldRuntime::collectProjectilePresentationState` and rendering active projectile/impact billboards from
  `IndoorDebugRenderer::renderSpriteObjectBillboards`. Indoor projectile drawing now uses the same shared
  `GameplayProjectilePresentationState` / `GameplayProjectileImpactPresentationState` packets as outdoor while the
  indoor renderer remains responsible for sprite-frame texture lookup, depth sorting, and billboard submission.
- 2026-04-22: Step 9 remains incomplete because indoor BLV face/world projectile collision is still pending; this
  slice covers render-facing projectile billboards without moving BLV geometry or collision facts into shared
  gameplay.
- 2026-04-22: Static audit shows the new indoor projectile presentation path:
  `collectProjectilePresentationState`, `GameplayProjectilePresentationState`,
  `GameplayProjectileImpactPresentationState`, and `appendProjectileDrawItem` in `game/indoor`.
- 2026-04-22: Line-length audit with `awk` found no new over-120 lines in
  `game/indoor/IndoorWorldRuntime.cpp`, `game/indoor/IndoorWorldRuntime.h`,
  `game/indoor/IndoorDebugRenderer.cpp`, or `game/indoor/IndoorDebugRenderer.h` after the Step 9 indoor projectile
  billboard rendering slice. The audit still reports pre-existing over-120 lines in
  `game/indoor/IndoorDebugRenderer.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor projectile
  billboard rendering slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor projectile
  billboard rendering slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor projectile billboard rendering slice; validation was limited
  to build, ctest, static audit, and line-length audit because indoor BLV face/world projectile collision remains
  pending.
- 2026-04-22: Continued Step 9 by routing shared indoor actor projectile requests into
  `GameplayProjectileService::ProjectileState` instead of applying damage immediately. Indoor now resolves monster
  projectile definitions from the monster projectile/object/spell tables, spawns shared projectile state with indoor
  sprite-frame data, and advances actor projectiles from `IndoorWorldRuntime::updateIndoorProjectiles`.
- 2026-04-22: Indoor actor projectiles now use `ProjectileFrameFacts` / `ProjectileFrameResult` for runtime travel,
  actor/party collision facts, direct actor/party impact, splash damage, projectile audio requests, impact FX points,
  bounce/motion/expiry application, and spawned projectile requests. Indoor still owns damage application to
  `MapDeltaActor`, party damage, `EventRuntimeState::pendingSounds`, and debug-renderer impact FX.
- 2026-04-22: Step 9 remains incomplete because indoor BLV face/world projectile collision and render-facing
  projectile billboards are still pending; this slice covers actor projectile runtime representation and actor/party
  collision without moving BLV geometry facts into shared gameplay.
- 2026-04-22: Static audit shows the new indoor projectile runtime entry points and shared frame API use:
  `applyIndoorActorProjectileRequest`, `updateIndoorProjectiles`, `ProjectileFrameFacts`, `ProjectileFrameResult`,
  `m_pGameplayProjectileService`, and `IndoorResolvedProjectileDefinition` in `game/indoor/IndoorWorldRuntime.cpp`.
- 2026-04-22: Line-length audit with `awk` found no lines over 120 characters in
  `game/indoor/IndoorWorldRuntime.cpp`, `game/indoor/IndoorWorldRuntime.h`,
  `game/scene/IndoorSceneRuntime.cpp`, or `game/scene/IndoorSceneRuntime.h` after the Step 9 indoor actor projectile
  runtime representation slice. The audit still reports two pre-existing over-120 lines in
  `game/app/GameApplication.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor actor
  projectile runtime representation slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor actor
  projectile runtime representation slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor actor projectile runtime representation slice; validation
  was limited to build, ctest, static audit, and line-length audit because indoor BLV face/world projectile collision
  and render-facing projectile billboards remain pending.
- 2026-04-22: Continued Step 9 by adding indoor-owned actor-target projectile application for shared
  `ActorProjectileRequest` results. `IndoorWorldRuntime::applyIndoorActorProjectileRequest` now handles party-target
  projectile damage as before and resolves actor-target projectile lines against BLV actors while ignoring the source
  actor, then applies damage to the hit actor and triggers the existing indoor projectile impact visual path.
- 2026-04-22: Step 9 remains incomplete because full indoor projectile representation is still pending; this slice
  applies shared projectile requests directly through indoor world state rather than adding projectile travel/collision
  simulation for indoor actors.
- 2026-04-22: Line-length audit with `awk` found no lines over 120 characters in
  `game/indoor/IndoorWorldRuntime.cpp` or `game/indoor/IndoorWorldRuntime.h` after the Step 9 actor-target projectile
  application slice.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor
  actor-target projectile application slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor
  actor-target projectile application slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor actor-target projectile application slice; validation was
  limited to build, ctest, static audit, and line-length audit because full indoor projectile representation remains
  pending.
- 2026-04-22: Continued Step 9 by applying shared indoor AI movement intent through
  `IndoorWorldRuntime::applyIndoorActorMovementIntegration`. Indoor now feeds movement updates into
  `IndoorMovementController`, which keeps BLV floor, ceiling, wall, mechanism, and sector resolution world-owned, then
  syncs resolved precise position, velocity, and sector id back to `MapActorAiState` and `MapDeltaActor`.
- 2026-04-22: Indoor blocked-movement fallout now calls
  `GameplayActorAiSystem::updateActorAfterWorldMovement` after BLV movement resolution. Shared AI still owns
  stand/velocity-clearing fallout decisions, while indoor supplies the movement-block fact and applies the resulting
  state/animation/movement patches. Indoor crowd steering remains disabled until indoor contact facts are collected.
- 2026-04-22: Step 9 remains incomplete because full indoor projectile representation and actor-target projectile
  application are still pending. Previous indoor-owned audio and hit/spell/death FX request application paths remain
  active.
- 2026-04-22: Line-length audit with `awk` found no lines over 120 characters in
  `game/indoor/IndoorWorldRuntime.cpp` or `game/indoor/IndoorWorldRuntime.h` after the Step 9 indoor BLV movement
  application slice.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor BLV
  movement application slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor BLV
  movement application slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor BLV movement application slice; validation was limited to
  build, ctest, static audit, and line-length audit because full indoor projectile representation remains pending.
- 2026-04-22: Continued Step 9 by routing `IndoorWorldRuntime::updateActorAi` through
  `GameplayActorAiSystem::updateActors`. Indoor now collects the same coarse `ActorAiFrameFacts` shape, receives an
  `ActorAiFrameResult`, and applies it through `IndoorWorldRuntime::applyIndoorActorAiFrameResult`.
- 2026-04-22: Indoor result application now patches indoor-owned `MapActorAiState` and BLV `MapDeltaActor` state for
  motion, animation, timers, queued attack ability, attack-impact latch, hostility/detection, spell effects, death,
  and movement intent. Indoor also applies party melee/projectile damage, actor-vs-actor melee damage, monster audio
  requests through `EventRuntimeState::pendingSounds`, and hit/spell/death FX intent through indoor-owned runtime and
  renderer hooks.
- 2026-04-22: Step 9 remains incomplete because BLV movement integration through indoor collision/floor/sector logic
  and full indoor projectile representation/actor-target projectile application are still pending. The old
  spell-effect timer fallback remains only for actors whose effect state was not patched by shared AI in the frame.
- 2026-04-22: Static audit shows the new indoor shared-AI application path and request consumers:
  `GameplayActorAiSystem`, `applyIndoorActorAiFrameResult`, `ActorProjectileRequest`, `ActorAudioRequest`,
  `ActorFxRequest`, and `spellEffectsAppliedMask` in `game/indoor/IndoorWorldRuntime.cpp`.
- 2026-04-22: Line-length audit with `awk` found no lines over 120 characters in
  `game/indoor/IndoorWorldRuntime.cpp` or `game/indoor/IndoorWorldRuntime.h` after the Step 9 application slice.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 9 indoor shared-AI
  state/result application slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 9 indoor shared-AI
  state/result application slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 9 indoor shared-AI state/result application slice; validation was
  limited to build, ctest, static audit, and line-length audit because BLV movement and full indoor projectile
  representation remain pending.
- 2026-04-22: Completed Step 8 by adding indoor `ActorAiFrameFacts` collection in
  `IndoorWorldRuntime::collectIndoorActorAiFrameFacts`. Indoor now selects active BLV actors, builds active and
  background `ActorAiFacts`, and keeps `MapDeltaActor` storage separate from shared AI facts.
- 2026-04-22: Indoor actor facts now include party distance, active flags, current/previous detection and hostility
  state from `MapActorAiState`, BLV sector id, same-sector and portal-reachable path facts, floor samples from
  `sampleIndoorFloor`, target height, current target facts, reachable actor target candidates, and indoor-owned
  line-of-sight approximation from sector/portal reachability.
- 2026-04-22: `IndoorWorldRuntime` now receives `IndoorMapData` from `IndoorSceneRuntime` and headless indoor
  diagnostic setup so fact collection can use BLV sectors, portal faces, mechanism-adjusted vertices, and floor
  sampling without exposing those representation details to shared actor AI types.
- 2026-04-22: Static `rg` audit shows the new indoor fact collection entry points and ownership fields:
  `collectIndoorActorAiFrameFacts`, `collectIndoorActorAiFacts`, `selectIndoorActiveActors`, `m_pIndoorMapData`,
  `sameSectorAsParty`, and `portalPathToParty` in `game/indoor`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 8 indoor fact
  collection slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 8 indoor fact
  collection slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 8 indoor fact collection slice; validation was limited to build,
  ctest, and static audit because the slice collects facts and does not yet apply shared AI results, movement,
  projectiles, audio, or FX to indoor actors.
- 2026-04-22: Completed Step 7 by adding `IndoorWorldRuntime::MapActorAiState` as indoor-owned persistent actor AI
  state. It now carries actor id/name, motion state, animation state, recovery/cooldown/action timers, idle/pursue/
  attack decision counters, movement intent fields, attack impact latch, queued attack ability, detection/hostility,
  and spell-effect overrides without reusing outdoor `MapActorState` or changing BLV `MapDeltaActor` storage.
- 2026-04-22: Replaced the old indoor `m_mapActorSpellEffectStates` runtime vector with `m_mapActorAiStates` and
  `syncMapActorAiStates`. Indoor actor runtime/inspect/attack/spell paths now read and update spell effects through
  the indoor AI state; newly summoned indoor actors receive initialized AI state from BLV map actor data and monster
  stats.
- 2026-04-22: Indoor save version 24 now serializes `IndoorWorldRuntime::MapActorAiState`; version 23 saves still
  read the legacy `mapActorSpellEffectStates` field and migrate those spell-effect overrides into the new per-actor AI
  state during snapshot restore.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed successfully after the Step 7 indoor runtime AI
  state slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed successfully after the Step 7 indoor runtime AI
  state slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 7 indoor runtime AI state slice; validation was limited to build,
  ctest, and serializer compatibility review because this slice adds persistent indoor AI state but does not yet route
  indoor actors through shared AI behavior or BLV movement.
- 2026-04-22: Completed Step 6 by removing the public
  `CombatTargetKind`, `CombatTargetResult`, `CombatEngagementInput`,
  `CombatEngagementResult`, and
  `GameplayActorService::resolveCombatEngagement` micro-decision API.
- 2026-04-22: Shared AI now resolves actor target/engagement state through
  private `ActorTargetState` / `ActorEngagementState` helpers in
  `GameplayActorAiSystem.cpp`. Outdoor target fact shaping and debug inspection
  now use file-local `OutdoorTargetFacts` / `OutdoorEngagementState` helpers,
  while outdoor still owns LOS checks, target candidate collection, and target
  policy fact shaping.
- 2026-04-22: Static `rg` audit confirms no remaining old public combat
  target/engagement API names: `GameplayActorService::CombatTarget*`,
  `GameplayActorService::CombatEngagement*`, `CombatTargetKind`,
  `CombatTargetResult`, `CombatEngagementInput`, `CombatEngagementResult`, or
  `resolveCombatEngagement` in game, engine, editor, or tools code.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 combat target/engagement public micro-decision
  demotion completion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 combat target/engagement public micro-decision
  demotion completion slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 6 combat target/engagement
  public micro-decision demotion completion slice; validation was limited to
  build, ctest, and static `rg` audit because this preserved the same target
  sensing, friendly-hostility promotion, alert, flee, melee-range, and
  friendly-near-party engagement rules behind private or file-local helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `CombatTargetCandidate`, `CombatTargetInput`, and
  `GameplayActorService::resolveCombatTarget` target-selection micro-decision
  API.
- 2026-04-22: Outdoor target fact shaping now uses file-local
  `OutdoorCombatTargetCandidate` and `resolveOutdoorCombatTarget` helpers with
  outdoor-owned LOS facts plus the existing shared target-policy helpers.
  `GameplayActorService` no longer exposes the selected-target input packet or
  resolver.
- 2026-04-22: Static `rg` audit confirms no remaining exact
  `CombatTargetCandidate`, `CombatTargetInput`, or
  `GameplayActorService::resolveCombatTarget` references in game, engine,
  editor, or tools C++ code. Remaining public `CombatTargetResult` /
  `CombatEngagement*` names are the next target/engagement demotion surface.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 combat target public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 combat target public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 6 combat target public
  micro-decision demotion slice; validation was limited to build, ctest, and
  static `rg` audit because this kept the same target priority/range/LOS
  behavior in outdoor fact shaping while removing only the obsolete public
  service packet and resolver.
- 2026-04-22: Continued Step 6 by removing the public
  `IdleBehaviorAction`, `IdleBehaviorResult`,
  `GameplayActorService::idleStandBehavior`, and
  `GameplayActorService::resolveIdleBehavior` micro-decision API.
- 2026-04-22: Active stand/wander idle behavior now stays private to
  `GameplayActorAiSystem.cpp`; outdoor inactive presentation remains
  outdoor-owned and is not routed through the removed public service packets.
- 2026-04-22: Static `rg` audit confirms no remaining
  `GameplayActorService::Idle*`, `idleStandBehavior`, or
  `resolveIdleBehavior` references in public service, outdoor, indoor, engine,
  editor, or tools code. Remaining `IdleBehavior*` names are file-local private
  helpers in `GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 idle behavior public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 idle behavior public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 6 idle behavior public
  micro-decision demotion slice; validation was limited to build, ctest, and
  static `rg` audit because this kept the same deterministic active idle
  stand/wander math inside shared AI and removed only the obsolete public
  service packets.
- 2026-04-22: Continued Step 6 by removing the public
  `InactiveFidgetResult`, `InactiveActorBehaviorInput`,
  `InactiveActorBehaviorResult`,
  `GameplayActorService::resolveInactiveFidget`, and
  `GameplayActorService::resolveInactiveActorBehavior` micro-decision API.
- 2026-04-22: Outdoor inactive actor presentation now applies the same
  deterministic fidget countdown and 5 percent bored-idle decision locally.
  Active stand/wander behavior remains owned by `GameplayActorAiSystem`, and
  outdoor still owns inactive presentation application to `MapActorState`.
- 2026-04-22: Static `rg` audit confirms `InactiveFidgetResult`,
  `InactiveActorBehaviorInput`, `InactiveActorBehaviorResult`,
  `resolveInactiveFidget`, `resolveInactiveActorBehavior`, and
  `InactiveActorBehavior` no longer appear in game, engine, editor, or tools
  C++ code. The now-unused outdoor `applyIdleBehavior` helper was also removed.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 inactive actor presentation public
  micro-decision demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 inactive actor presentation public
  micro-decision demotion slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 6 inactive actor presentation
  public micro-decision demotion slice; validation was limited to build, ctest,
  and static `rg` audit because this preserved the same inactive actor fidget
  timing/seed behavior behind outdoor-local presentation code.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorInitialTimingInput` / `ActorInitialTimingResult`,
  `ActorCombatAvailabilityInput`, and `ActorHitReactionInput` micro-structs
  plus the old `GameplayActorService::resolveActorInitialTiming` method.
- 2026-04-22: Outdoor actor initialization now calls
  `GameplayActorService::initialAttackCooldownSeconds` and
  `initialIdleDecisionSeconds` directly. Outdoor combat availability and hit
  reaction checks now call behavior-named predicate helpers without exposing
  public input/result packets.
- 2026-04-22: Static `rg` audit confirms `ActorInitialTiming`,
  `resolveActorInitialTiming`, `ActorCombatAvailability`, `ActorHitReaction`,
  and `buildActorCombatAvailabilityInput` no longer appear in game, engine,
  editor, or tools C++ code.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 initial timing and combat predicate public
  micro-decision demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 initial timing and combat predicate public
  micro-decision demotion slice; no tests were found in the current build tree.
- 2026-04-22: Manual smoke not run for the Step 6 initial timing and combat
  predicate public micro-decision demotion slice; validation was limited to
  build, ctest, and static `rg` audit because this preserved the same actor
  startup timing formulas and combat availability / hit-reaction predicates
  behind smaller public helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `ActiveActorUpdateCandidate`, `ActiveActorUpdateSelectionInput`,
  `ActiveActorUpdateSelectionResult`, and
  `GameplayActorService::selectActiveActorUpdates` micro-decision API.
- 2026-04-22: Active actor list construction is now outdoor-owned in
  `OutdoorWorldRuntime::selectOutdoorActiveActors` through the file-local
  `selectOutdoorActiveActorMask` helper; the selection behavior remains the
  same distance-filtered, stable-sorted nearest actor mask capped by
  `MaxActiveActorUpdates`.
- 2026-04-22: Static `rg` audit confirms the removed active actor selection
  public API names no longer appear in game, engine, editor, or tools code;
  only outdoor-owned `ActiveActorUpdateRange` / `MaxActiveActorUpdates`
  constants retain that wording.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 active actor selection public micro-decision
  demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 active actor selection public micro-decision
  demotion slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 active actor selection public micro-decision
  demotion slice; validation was limited to build, ctest, and static `rg`
  audit because this moved the same distance-sorted outdoor active-list
  selection rule from a public service helper into outdoor-owned file-local
  code.
- 2026-04-22: Continued Step 6 by removing the public
  `CrowdSteeringAction`, `CrowdSteeringState`, `CrowdSteeringResult`, and
  `CrowdSteeringEligibilityInput` micro-decision API plus the old
  `GameplayActorService::resolveCrowdSteering` and
  `GameplayActorService::shouldApplyCrowdSteering` methods.
- 2026-04-22: `GameplayActorAiSystem.cpp` now owns post-movement crowd
  steering through file-local helpers while outdoor still owns contacted-actor
  fact collection, movement/collision integration, and `MapActorState`
  application.
- 2026-04-22: Static `rg` audit confirms no remaining public-service crowd
  steering API references in game, engine, editor, or tools code; remaining
  `CrowdSteering` names are file-local shared-AI helpers or outdoor state/reset
  field names.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 crowd-steering public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 crowd-steering public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 crowd-steering public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  the same post-movement crowd steering rule moved from public service helpers
  into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `FriendlyTargetEngagementResult` and
  `GameplayActorService::resolveFriendlyTargetEngagement` micro-decision API.
  The friendly-target hostility promotion rule now lives as a file-local helper
  used only by `GameplayActorService::resolveCombatEngagement`.
- 2026-04-22: Static `rg` audit confirms
  `FriendlyTargetEngagementResult` and
  `GameplayActorService::resolveFriendlyTargetEngagement` no longer appear in
  game, engine, editor, or tools code; the remaining
  `resolveFriendlyTargetEngagement` symbol is private to
  `GameplayActorService.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 friendly-target public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 friendly-target public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 friendly-target public micro-decision
  demotion slice; validation was limited to build, ctest, and static `rg` audit
  because the same friendly-target promotion rule is still called only from
  `resolveCombatEngagement`.
- 2026-04-21: Completed Step 1 by auditing public structs in
  `GameplayActorService.h` and recording the current public micro-struct groups
  that should be removed or privatized once `GameplayActorAiSystem` owns the
  actor frame.
- 2026-04-21: Actor AI direction is now frozen around coarse
  `ActorAiFrameFacts`, `ActorAiFacts`, `ActorAiUpdate`, and
  `ActorAiFrameResult` packets. New public micro-decision structs should not be
  added to `GameplayActorService` for actor AI frame work.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after Step 1.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after Step 1; no tests were found in the current build tree.
- 2026-04-21: Completed Step 2 by extracting `OutdoorWorldRuntime::updateMapActors`
  into named frame phases: `updateActorFrameGlobalEffects`,
  `selectOutdoorActiveActors`, `updateOutdoorActorsForStep`, and
  `applyActorFrameSideEffects`.
- 2026-04-21: The active actor selection and world side-effect ticks are now
  explicit phases. The existing outdoor actor behavior, movement, collision,
  combat, projectile, and crowd-steering body remains in outdoor runtime and no
  shared AI system or new actor micro-decision structs were introduced.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after Step 2.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after Step 2; no tests were found in the current build tree.
- 2026-04-21: Completed Step 3 by adding `game/gameplay/GameplayActorAiTypes.h`
  with coarse shared actor AI packets: `ActorAiFrameFacts`, `ActorAiFacts`,
  `ActorAiUpdate`, and `ActorAiFrameResult`.
- 2026-04-21: The new packets include domain sub-facts for party, identity,
  stats, runtime, status, targets, movement, and world facts, plus coarse
  state patch, animation patch, movement intent, attack request, combat event,
  projectile request, audio request, and FX request result shapes. They are
  included from `GameplayActorService.h` but do not add new micro-decision
  structs to `GameplayActorService`.
- 2026-04-21: The new shared actor AI types use shared gameplay concepts only
  and avoid outdoor/indoor storage, renderer, terrain, collision, and callback
  details.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after Step 3.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after Step 3; no tests were found in the current build tree.
- 2026-04-21: Completed Step 4 by adding `game/gameplay/GameplayActorAiSystem.h`
  and `game/gameplay/GameplayActorAiSystem.cpp`, then registering
  `GameplayActorAiSystem.cpp` in `game/CMakeLists.txt`.
- 2026-04-21: The public shared actor AI system API is
  `GameplayActorAiSystem::updateActors(const ActorAiFrameFacts &facts) const`.
  The first implementation separates background and active actor loops and uses
  behavior-named internal helpers for death/dying holds, status locks, attack
  continuation, flee, pursue, and stand/wander updates.
- 2026-04-21: The new system returns coarse `ActorAiFrameResult` /
  `ActorAiUpdate` packets and does not expose the existing
  `GameplayActorService` micro-decision API. It is not wired into outdoor or
  indoor runtime actor frames yet; fact collection and result application remain
  the Step 5 work.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after Step 4.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after Step 4; no tests were found in the current build tree.
- 2026-04-21: Started Step 5 by adding outdoor coarse actor AI fact collection
  in `OutdoorWorldRuntime::collectOutdoorActorAiFrameFacts` and
  `collectOutdoorActorAiFacts`. The facts split actors into active/background
  packets and include party facts, identity, stats, runtime state, spell
  effects, target candidates, current target, movement facts, and outdoor-owned
  LOS facts without exposing `MapActorState`.
- 2026-04-21: `OutdoorWorldRuntime::updateMapActors` now calls
  `GameplayActorAiSystem::updateActors` once per fixed actor update step using
  the collected facts. The returned `ActorAiFrameResult` is intentionally not
  applied yet; the existing `updateOutdoorActorsForStep` path still applies
  outdoor actor behavior so this slice does not change runtime behavior.
- 2026-04-21: Step 5 remaining work is result application and then transfer of
  outdoor decisions behind `GameplayActorAiSystem` while preserving outdoor
  ownership of terrain, collision, movement integration, projectile spawn
  application, audio, and FX.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor fact/update preview slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor fact/update preview slice; no tests were
  found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring the outdoor terminal
  dead/dying actor path to shared `ActorAiFrameResult` application.
  `GameplayActorAiSystem` now resolves the dead, mark-dead, and advance-dying
  outcomes through the existing actor death rule and returns coarse state
  patches plus a blood-splat world event.
- 2026-04-21: Added `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult`.
  Outdoor applies the terminal result to `MapActorState`, keeps blood splat,
  corpse state, movement clearing, and rounded representation coordinates
  outdoor-owned, returns a handled mask, and skips those actors in the legacy
  outdoor actor body.
- 2026-04-21: Step 5 remains open. Status locks, spell timers, target choice,
  attack starts/impacts, actor-vs-actor behavior, movement integration, crowd
  steering, projectile requests, audio, and FX are still handled by the legacy
  outdoor actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 terminal dead/dying actor result application
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 terminal dead/dying actor result application
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active stun/paralyze status-lock
  decisions to shared `ActorAiFrameResult` application. `GameplayActorAiSystem`
  now resolves hold-stun, recover-from-stun, hold-paralyze, and force-stun
  outcomes through the existing actor status and animation tick rules, and
  marks only completed status-lock updates as handled by the shared path.
- 2026-04-21: Outdoor fact collection now includes default hostility so shared
  spell-effect timer expiry can preserve the existing control-expiry hostility
  behavior. Outdoor applies active status-lock results to `MapActorState`,
  including spell-effect timers, motion/animation state, animation ticks, action
  seconds, attack-impact clearing for paralyze, and movement clearing. Inactive
  status actors and status locks that expire before producing a lock result
  still fall through to the legacy outdoor body.
- 2026-04-21: Step 5 remains open. Non-lock spell timers, target choice, attack
  starts/impacts, actor-vs-actor behavior, movement integration, crowd steering,
  projectile requests, audio, and FX are still handled by the legacy outdoor
  actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active status-lock result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active status-lock result application slice; no
  tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active non-lock spell-effect
  timer aging to shared `ActorAiFrameResult` application.
  `GameplayActorAiSystem` now emits active actor spell-effect timer patches for
  non-terminal actors that continue into attack, flee, pursue, stand, or wander
  decisions, and for status-lock actors whose lock expires before producing a
  handled lock result.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now returns
  separate masks for fully handled actors and actors whose spell effects were
  already applied. The outdoor actor body skips only the old timer update for
  those spell-effect-applied actors, while preserving legacy target choice,
  attacks, movement integration, crowd steering, projectiles, audio, and FX.
- 2026-04-21: Step 5 remains open. Target choice, attack starts/impacts,
  actor-vs-actor behavior, movement integration, crowd steering, projectile
  requests, audio, and FX are still handled by the legacy outdoor actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active non-lock spell-effect timer result
  application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active non-lock spell-effect timer result
  application slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active actor frame timer aging to
  shared `ActorAiFrameResult` application. `ActorRuntimeFacts` now carries idle
  decision, attack cooldown, action, and crowd timer inputs, and
  `GameplayActorAiSystem` advances them through the existing actor frame timer
  rule.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  active frame timer patches and records a separate frame-timers-applied mask.
  The outdoor actor body skips only the old frame timer update for those actors,
  while target choice, attack starts/impacts, actor-vs-actor behavior, movement
  integration, crowd steering decisions, projectile requests, audio, and FX
  remain on the legacy outdoor path.
- 2026-04-21: Step 5 remains open. Target choice, attack starts/impacts,
  actor-vs-actor behavior, movement integration, crowd steering decisions,
  projectile requests, audio, and FX are still handled by the legacy outdoor
  actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active frame timer result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active frame timer result application slice; no
  tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active animation tick aging to
  shared `ActorAiFrameResult` application. `GameplayActorAiSystem` now advances
  active actor animation ticks through the existing actor animation tick rule
  for non-terminal actors that continue into attack, flee, pursue, stand, or
  wander decisions.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  active animation-time patches and records a separate
  animation-ticks-applied mask. The outdoor actor body skips only the old
  animation tick increment for those actors, while target choice, attack
  starts/impacts, actor-vs-actor behavior, movement integration, crowd steering
  decisions, projectile requests, audio, and FX remain on the legacy outdoor
  path.
- 2026-04-21: Step 5 remains open. Target choice, attack starts/impacts,
  actor-vs-actor behavior, movement integration, crowd steering decisions,
  projectile requests, audio, and FX are still handled by the legacy outdoor
  actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active animation tick result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active animation tick result application slice;
  no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active combat engagement state
  to shared `ActorAiFrameResult` application. `ActorAiFrameFacts` now carries
  current target relation and current hostile-to-party state, and
  `GameplayActorAiSystem` resolves party detection, actor-target hostility
  promotion, and party alert requests through the existing combat engagement
  rule.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  active engagement patches for `hasDetectedParty` and `hostilityType`, and
  applies shared alert audio requests with outdoor-owned monster sound lookup
  before the legacy actor body runs. The legacy body still owns target choice,
  attack starts/impacts, movement integration, crowd steering, projectile
  requests, non-alert audio, and FX.
- 2026-04-21: Step 5 remains open. Target choice, attack starts/impacts,
  actor-vs-actor attack application, movement integration, crowd steering
  decisions, projectile requests, non-alert audio, and FX are still handled by
  the legacy outdoor actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active combat engagement result application
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active combat engagement result application
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active attack-impact completion
  to shared `ActorAiFrameResult` application. `ActorAiFrameFacts` now carries
  attack damage profile facts, and `GameplayActorAiSystem` resolves completed
  attack frames plus impact kind/damage through the existing attack-frame and
  attack-impact rules.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  shared attack-impact requests for party melee combat-controller records,
  actor-vs-actor damage, ranged/spell projectile release, and the
  `attackImpactTriggered` latch. The legacy outdoor body skips the old
  attack-impact block for those actors, while target choice, attack starts,
  movement integration, crowd steering decisions, non-alert audio, and FX remain
  on the legacy path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active attack-impact result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active attack-impact result application slice;
  no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active attack-start decisions to
  shared `ActorAiFrameResult` application. Outdoor fact collection now supplies
  melee and ranged attack animation duration facts, and `GameplayActorAiSystem`
  resolves attack ability choice, engage-start eligibility, attack
  cooldown/action timing, queued attack ability, facing, animation reset, and
  attack audio through the existing actor rules.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  shared attack-start patches for state, attack animation, queued attack
  ability, attack decision count, cooldown/action timers,
  `attackImpactTriggered`, facing, move-direction clearing, and attack audio
  before the legacy body runs. The legacy body sees those actors as
  in-progress attacks, so the old attack-start block does not run again.
- 2026-04-21: Step 5 remains open. Target choice, movement integration, crowd
  steering decisions, projectile request shaping beyond direct actor attack
  release, non-alert/non-attack audio, and FX are still handled by the legacy
  outdoor actor loop.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active attack-start result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active attack-start result application slice;
  no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active combat-flow outcomes for
  continue-attack, blind-wander, flee, and friendly-near-party to shared
  `ActorAiFrameResult` application. `GameplayActorAiSystem` now resolves those
  outcomes through the existing combat-flow decision/application rules and
  marks them as shared-applied flow updates.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  shared combat-flow state, animation, action/idle timers, move direction,
  desired movement, yaw, and clear-velocity requests before the legacy actor
  body. The legacy body skips re-running old flow application for those actors
  and still owns movement integration, terrain/collision response, and crowd
  steering.
- 2026-04-21: Step 5 remains open. Engage-target pursuit/target choice,
  non-combat movement decisions, movement integration, crowd steering decisions,
  projectile request shaping beyond direct actor attack release,
  non-alert/non-attack audio, and FX are still handled by the legacy outdoor
  path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active combat-flow result application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active combat-flow result application slice; no
  tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active engage-target pursuit
  decisions to shared `ActorAiFrameResult` application. Outdoor fact collection
  now supplies effective actor move speed, and `GameplayActorAiSystem` resolves
  attack ability choice, engage application, pursue direction/action timing,
  attack-decision count, pursue-decision count, and crowd-preservation intent
  through existing actor rules.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  shared engage-target pursuit patches for state, animation, yaw, move
  direction, desired movement, `attackImpactTriggered`, pursue/attack decision
  counts, and melee/crowd steering flags before the legacy actor body. The
  legacy body reuses those values and still owns frame commit, water/terrain
  restrictions, movement integration, collision response, and crowd steering.
- 2026-04-21: Step 5 remains open. Non-combat movement decisions, movement
  integration, crowd steering result transfer, projectile request shaping beyond
  direct actor attack release, non-alert/non-attack audio, and FX are still
  handled by the legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active engage-target pursuit result application
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active engage-target pursuit result application
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active non-combat stand, idle,
  wander, and return-home decisions to shared `ActorAiFrameResult`
  application. `ActorMovementFacts` now carries idle-wander availability, and
  `GameplayActorAiSystem` resolves the existing non-combat behavior rule into
  coarse state, animation, yaw, move-direction, desired-movement, timer, and
  idle decision-count patches.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now applies
  shared non-combat patches before the legacy actor body. The legacy body
  reuses those values and still owns frame commit, water/terrain restrictions,
  movement integration, collision response, movement-block handling, and crowd
  steering.
- 2026-04-21: Step 5 remains open. Movement integration extraction, crowd
  steering result transfer, projectile request shaping beyond direct actor
  attack release, non-alert/non-attack audio, and FX are still handled by the
  legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active non-combat movement decision result
  application slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active non-combat movement decision result
  application slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active shared-applied
  frame-commit decisions to shared `ActorAiFrameResult` application.
  `GameplayActorAiSystem` now resolves keep-current-animation,
  reset-animation-time, reset-crowd-steering, clear-velocity, and
  apply-movement flags for shared-applied combat-flow, engage-target pursuit,
  and non-combat decisions through the existing actor frame-commit rule.
- 2026-04-21: `OutdoorWorldRuntime::applyOutdoorActorAiFrameResult` now records
  shared frame-commit flags and the legacy outdoor movement body consumes those
  flags instead of re-running the old frame-commit rule for those actors.
  Outdoor still owns water/terrain restrictions, movement integration,
  collision response, movement-block handling, and crowd steering.
- 2026-04-21: Step 5 remains open. Movement integration extraction,
  movement-block fallout, crowd steering result transfer, projectile request
  shaping beyond direct actor attack release, non-alert/non-attack audio, and
  FX are still handled by the legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active shared frame-commit result application
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active shared frame-commit result application
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active post-movement block
  fallout to shared AI. `GameplayActorAiSystem::updateActorAfterWorldMovement`
  now consumes the outdoor-owned blocked/not-blocked movement fact through the
  existing coarse `ActorAiFacts` packet and returns an `ActorAiUpdate` for
  velocity clearing, move-direction reset, short action timer, and stand-state
  fallout.
- 2026-04-21: Outdoor still owns water/terrain restrictions, movement
  integration, collision response, and precise actor position sync. The outdoor
  actor body now applies movement first, then asks shared AI for the
  movement-block fallout patch instead of calling the old actor-service
  micro-decision directly.
- 2026-04-21: Step 5 remains open. Movement integration extraction, crowd
  steering result transfer, projectile request shaping beyond direct actor
  attack release, non-alert/non-attack audio, and FX are still handled by the
  legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active post-movement block fallout shared-AI
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active post-movement block fallout shared-AI
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by transferring active post-collision crowd
  steering to shared AI. `ActorAiFacts` now carries coarse crowd steering state
  plus outdoor-owned contact facts, and
  `GameplayActorAiSystem::updateActorAfterWorldMovement` resolves crowd
  eligibility, stand/retreat/sidestep choice, crowd timers/state,
  pursue-decision count, yaw, and movement intent.
- 2026-04-21: Outdoor still owns water/terrain restrictions, movement
  integration, collision response, precise actor position sync, contacted-actor
  counting, and `MapActorState` application. The outdoor actor body now applies
  the shared post-movement crowd-steering patch instead of calling the old
  actor-service crowd steering micro-decisions directly.
- 2026-04-21: Step 5 remains open. Movement integration extraction, projectile
  request shaping beyond direct actor attack release, non-alert/non-attack
  audio, and FX are still handled by the legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active post-collision crowd steering shared-AI
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active post-collision crowd steering shared-AI
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by moving active ranged/spell attack projectile
  release shaping into `ActorAiFrameResult::projectileRequests`.
  `GameplayActorAiSystem` now emits coarse `ActorProjectileRequest` entries for
  ranged and spell attack impacts, while outdoor application records monster
  ranged release and keeps projectile/spell spawning, runtime table lookup, and
  world-specific application in `OutdoorWorldRuntime`.
- 2026-04-21: Step 5 remains open. Movement integration extraction,
  non-alert/non-attack audio, and FX are still handled by the legacy outdoor
  path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active projectile request shaping shared-AI
  slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active projectile request shaping shared-AI
  slice; no tests were found in the current build tree.
- 2026-04-21: Continued Step 5 by extracting active outdoor actor movement
  integration into `OutdoorWorldRuntime::applyOutdoorActorMovementIntegration`
  and post-movement shared-AI result application into
  `OutdoorWorldRuntime::applyOutdoorActorPostMovementAiUpdate`.
- 2026-04-21: Outdoor still owns water restrictions, slope response,
  movement-controller collision, fallback ODM movement, precise actor position
  sync, and contacted-actor fact collection. Shared AI still receives only
  coarse post-movement blocked/contact facts and resolves block/crowd fallout
  through `GameplayActorAiSystem::updateActorAfterWorldMovement`.
- 2026-04-21: Step 5 remains open. Non-alert/non-attack audio and FX are still
  handled by the legacy outdoor path.
- 2026-04-21: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor movement integration extraction slice.
- 2026-04-21: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor movement integration extraction slice;
  no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 by moving active actor-vs-actor melee hit/death
  audio intent into `ActorAiFrameResult::audioRequests`. Outdoor now collects
  current target HP and audio position as coarse target facts, suppresses
  legacy damage-audio emission for shared actor melee damage application, and
  resolves monster `winceSoundId` / `deathSoundId` plus world-local playback
  when applying the shared result.
- 2026-04-22: Terminal dead/dying blood-splat intent now uses
  `ActorAiFrameResult::fxRequests` with `ActorAiFxRequestKind::Death`. The old
  public `ActorWorldEvent` frame path was removed, while outdoor still owns
  blood-splat placement, terrain sampling, geometry baking, and map-state
  mutation.
- 2026-04-22: Step 5 remains open for final audit/cleanup of outdoor shared
  result application before Step 6. Outdoor terrain, collision, movement
  integration, projectile spawning, sound-ID lookup, audio playback, and FX
  placement remain world-owned.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 actor-vs-actor audio and death FX result
  request slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 actor-vs-actor audio and death FX result
  request slice; no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the stale outdoor
  `OutdoorActorAiFrameApplication::attackStartsAppliedActorMask`. Attack-start
  result application now relies directly on the shared-applied
  state/animation/movement patches, and static `rg` audit shows no remaining
  references to `attackStartsAppliedActorMask`, `ActorWorldEvent`, or
  `worldEvents` in `game/outdoor` or `game/gameplay`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 shared-result application cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 shared-result application cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the unused
  `ActorCombatEvent` struct and `ActorAiFrameResult::combatEvents` vector.
  Shared AI no longer emits a duplicate combat-event result stream; outdoor
  applies combat through `ActorAiUpdate::attackRequest`,
  `ActorProjectileRequest`, `ActorAudioRequest`, and `ActorFxRequest`.
- 2026-04-22: Static audit with `rg` confirmed no remaining
  `ActorCombatEvent` or `combatEvents` code references in `game`, `engine`,
  `editor`, or `tools`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 combat-event result cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 combat-event result cleanup slice; no tests
  were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by making
  `OutdoorWorldRuntime::updateOutdoorActorsForStep` consume shared-applied
  combat-flow, engage-target pursuit, and non-combat masks before calling the
  old combat-flow and non-combat actor-service rules. The fallback service
  calls remain only for actors without shared-applied behavior results, while
  outdoor movement integration, terrain checks, collision, and result
  application remain outdoor-owned.
- 2026-04-22: Static audit with `rg` shows the fallback calls to
  `resolveCombatFlowDecision`, `resolveCombatFlowApplication`, and
  `resolveNonCombatBehavior` now sit behind the shared-applied mask checks in
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 shared behavior-mask preference slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 shared behavior-mask preference slice; no tests
  were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by making shared-applied active
  status-lock updates skip the legacy outdoor actor body directly from
  `ActorAiUpdate::statusLockHandled`. This preserves the old
  recover-from-stun behavior where the actor returns to standing and stops
  processing the rest of the actor frame, while outdoor still owns state
  application.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 status-lock legacy-skip cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 status-lock legacy-skip cleanup slice; no tests
  were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the legacy outdoor
  attack-impact fallback from `OutdoorWorldRuntime::updateOutdoorActorsForStep`.
  Active attack-impact application now stays on the shared-result request paths:
  `ActorAiUpdate::attackRequest`, frame-level `ActorProjectileRequest`, and
  frame-level `ActorAudioRequest`.
- 2026-04-22: Removed the now-unused
  `OutdoorActorAiFrameApplication::attackImpactsAppliedActorMask`. Static `rg`
  audit found no remaining outdoor references to `resolveAttackImpact`,
  `AttackImpactInput`, `AttackImpactResult`, `AttackImpactAction`, or
  `attackImpactsAppliedActorMask`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor attack-impact fallback cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor attack-impact fallback cleanup slice;
  no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the legacy active
  dying/status-lock fallback blocks from
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`. Active dying, stun
  recovery, paralyze hold, and force-stun frames now rely on shared
  `ActorAiFrameResult` application plus the shared handled/status-lock skip
  path. Inactive actors still route through inactive presentation, and
  missing-stats actors still use the existing frame route fallback.
- 2026-04-22: Static `rg` audit confirms no remaining
  `ActorStatusFrameInput`, `ActorStatusFrameResult`,
  `ActorStatusFrameAction`, or `resolveActorStatusFrame` references in
  `game/outdoor/OutdoorWorldRuntime.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor status/death fallback cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor status/death fallback cleanup slice;
  no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by restricting the remaining outdoor
  `resolveActorDeathFrame` fallback to actors whose monster stats are missing
  and therefore cannot enter `ActorAiFrameFacts`. Valid actor death/dying
  decisions now stay on `GameplayActorAiSystem::aiHoldDeathState`, then outdoor
  skips them through the shared handled mask after `ActorAiFrameResult`
  application.
- 2026-04-22: Removed the now-unreachable
  `ActorFrameRouteAction::MissingStats` branch from the valid-stats route in
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`. Static `rg` audit confirms
  outdoor `ActorDeathFrameInput` / `resolveActorDeathFrame` references remain
  only in the `pStats == nullptr` fallback; the shared death-frame decision
  remains in `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 missing-stats death fallback cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 missing-stats death fallback cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by adding
  `OutdoorActorAiFrameApplication::combatEngagementsAppliedActorMask`. Active
  combat engagement side effects for `hostilityType`, alert audio, and
  `hasDetectedParty` now remain on the shared `ActorAiFrameResult` application
  path; the old outdoor application in `updateOutdoorActorsForStep` is
  fallback-only for actors without a shared-applied engagement result.
- 2026-04-22: Static `rg` audit confirms the remaining outdoor
  `actor.hostilityType = engagement.hostilityType`,
  `engagement.shouldPlayPartyAlert`, and
  `actor.hasDetectedParty = engagement.hasDetectedParty` side-effect code sits
  behind `combatEngagementsAppliedActorMask`; outdoor still recomputes
  engagement facts needed for movement fallback without re-applying those
  shared-owned side effects.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 combat engagement fallback cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 combat engagement fallback cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the valid-stats outdoor
  `GameplayActorService::resolveActorFrameRoute` call from
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`. Missing-stats actors keep
  their explicit fallback because they cannot be represented in shared AI
  facts, while normal active/inactive routing now uses the world-owned
  `activeActorMask` directly.
- 2026-04-22: Static `rg` audit confirms `ActorFrameRoute` and
  `resolveActorFrameRoute` are no longer referenced by
  `game/outdoor/OutdoorWorldRuntime.cpp` or
  `game/gameplay/GameplayActorAiSystem.cpp`; the remaining references are
  confined to `GameplayActorService` for the later Step 6 demotion pass.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 actor frame route fallback cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 actor frame route fallback cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 by moving active attack-completion behavior
  continuation into `GameplayActorAiSystem`. Completed attack updates now can
  carry their impact request plus the next shared engage-target or non-combat
  behavior result in the same `ActorAiUpdate`, which gives outdoor result
  application a shared-applied behavior mask instead of relying on the legacy
  combat-flow/non-combat fallback for that frame.
- 2026-04-22: Visible targets that resolve to "do not engage" now fall through
  to shared non-combat behavior instead of the transitional unhandled pursue
  update. Static `rg` audit of `GameplayActorAiSystem.cpp` shows the unused
  `aiPursue` helper was removed, and the shared continuation paths are
  `applyEngageTargetBehavior`, `aiNonCombat`, and
  `applyNonCombatBehaviorFrame`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 shared attack-completion behavior continuation
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 shared attack-completion behavior continuation
  slice; no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the transitional outdoor
  combat-flow/non-combat fallback block from
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`. Valid active actors now
  consume shared-applied `combatFlowHandled`, `combatEngageHandled`, or
  `nonCombatHandled` behavior masks from `ActorAiFrameResult`; outdoor still
  owns frame commit consumption, water/terrain restrictions, movement
  integration, collision, and post-movement shared-AI fallout.
- 2026-04-22: Static `rg` audit confirms `resolveCombatFlowDecision`,
  `resolveCombatFlowApplication`, and `resolveNonCombatBehavior` are no longer
  referenced by `game/outdoor/OutdoorWorldRuntime.cpp`; those decision calls
  remain inside `game/gameplay/GameplayActorAiSystem.cpp` as the shared
  behavior owner.
- 2026-04-22: Status-lock expiry continuation now stays inside
  `GameplayActorAiSystem`. If a stun/paralyze lock ages into a non-lock
  spell-effect patch, the shared AI carries the aged spell-effect facts into
  the same-frame combat-flow, engage-target, or non-combat behavior update
  instead of depending on an outdoor fallback behavior block.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor combat-flow/non-combat fallback removal
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor combat-flow/non-combat fallback removal
  slice; no tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the legacy outdoor active
  animation tick, spell-effect timer, and frame-timer fallback blocks from
  `OutdoorWorldRuntime::updateOutdoorActorsForStep`. Valid active actors now
  rely on `ActorAiFrameResult` application for animation-time, spell-effect,
  idle/action/cooldown, and crowd-timer aging; outdoor still owns active
  selection, target/LOS fact collection, terrain/collision movement
  integration, and result application to `MapActorState`.
- 2026-04-22: Static `rg` audit confirms no remaining
  `advanceActorAnimationTick`, `updateSpellEffectTimers`, or
  `advanceActorFrameTimers` calls in `game/outdoor/OutdoorWorldRuntime.cpp`;
  those actor-frame timing decisions now remain in
  `game/gameplay/GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor active timer fallback removal slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor active timer fallback removal slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing the legacy outdoor active
  frame-commit fallback from `OutdoorWorldRuntime::updateOutdoorActorsForStep`.
  Valid active actors now consume frame-commit flags emitted by
  `GameplayActorAiSystem`; outdoor no longer recomputes
  `resolveActorFrameCommit` or `resolveActorAttackFrame` in the main actor
  update loop, and the stale `combatEngagePreserveCrowdSteeringMask`
  application field was removed.
- 2026-04-22: Static `rg` audit confirms no remaining
  `resolveActorFrameCommit`, `ActorFrameCommitInput`,
  `ActorFrameCommitResult`, or `combatEngagePreserveCrowdSteeringMask`
  references in `game/outdoor/OutdoorWorldRuntime.cpp` or
  `game/outdoor/OutdoorWorldRuntime.h`. `ActorAttackFrameInput` remains in
  outdoor debug info collection only; main attack-frame decisions remain in
  `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 outdoor frame-commit fallback removal slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 outdoor frame-commit fallback removal slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by carrying active movement integration
  inputs from the shared actor AI fact/result path instead of recomputing them
  in `OutdoorWorldRuntime::updateOutdoorActorsForStep`. `ActorAiFrameFacts` now
  supplies effective move speed, target position, target edge distance, and
  melee-range facts to `OutdoorActorAiFrameApplication`; the active valid-actor
  body no longer reruns local combat target, party proximity, or combat
  engagement fallback logic before outdoor-owned terrain/collision movement
  integration.
- 2026-04-22: Static `rg` audit confirms the remaining outdoor
  `resolveOutdoorCombatTarget`, `resolveActorPartyProximity`,
  `resolveCombatEngagement`, and `ActorMoveSpeedInput` references are in actor
  fact collection or debug inspection, not in the active valid-actor movement
  body.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 active movement fact reuse cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 active movement fact reuse cleanup slice; no
  tests were found in the current build tree.
- 2026-04-22: Continued Step 5 cleanup by removing stale
  `OutdoorActorAiFrameApplication` masks for spell-effect timer, animation
  tick, and frame timer fallback suppression. The active actor movement body now
  uses `OutdoorActorAiFrameApplication::activeUpdatesAppliedActorMask` as the
  shared active-result gate instead of the misleading
  `combatEngagementsAppliedActorMask` name.
- 2026-04-22: Static `rg` audit confirms no remaining
  `spellEffectsAppliedActorMask`, `animationTicksAppliedActorMask`,
  `frameTimersAppliedActorMask`, or `combatEngagementsAppliedActorMask`
  references in `game/outdoor/OutdoorWorldRuntime.cpp` or
  `game/outdoor/OutdoorWorldRuntime.h`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 stale shared-result mask cleanup slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 stale shared-result mask cleanup slice; no tests
  were found in the current build tree.
- 2026-04-22: Completed Step 5 final audit. `OutdoorWorldRuntime::updateMapActors`
  now collects `ActorAiFrameFacts`, calls `GameplayActorAiSystem::updateActors`,
  applies `ActorAiFrameResult`, and then runs only outdoor-owned movement/collision
  application and side effects for the active frame.
- 2026-04-22: Static `rg` audit confirms the old valid-active outdoor frame
  fallback decisions are absent from `OutdoorWorldRuntime.cpp`: no remaining
  `resolveActorStatusFrame`, `advanceActorAnimationTick`, `advanceActorFrameTimers`,
  `resolveAttackImpact`, `resolveCombatFlowDecision`, `resolveCombatFlowApplication`,
  `resolveNonCombatBehavior`, `resolveActorFrameCommit`, or `resolveActorFrameRoute`
  calls remain in the outdoor runtime.
- 2026-04-22: The remaining `GameplayActorService` calls in outdoor are outside
  the valid active behavior body: active actor selection, inactive presentation,
  outdoor fact shaping for target/proximity/move-speed facts, the malformed
  missing-stats death fallback, direct spell handling, projectile helpers, and
  debug inspection. Outdoor terrain, water restrictions, slope response, movement
  controller collision, fallback ODM movement, precise position sync, projectile
  spawning, audio playback, and FX placement remain world-owned.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 5 final outdoor shared-AI result audit.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 5 final outdoor shared-AI result audit; no tests
  were found in the current build tree.

Manual smoke status:

- 2026-04-22: Not run interactively for the corpse-loot fix. Focused headless dialogue coverage confirms looted
  outdoor corpses no longer reopen; broader dialogue smoke still passes the relevant actor AI cases but remains
  non-clean because unrelated residual diagnostics and audio decode errors remain.
- 2026-04-22: Not run interactively for the actor attack-start preservation fix. Headless dialogue coverage now
  confirms hostile melee attack entry, mixed ranged attack choice/release/party hit, actor-vs-actor hostile damage,
  attack persistence when the party moves away, and post-attack recovery behavior; residual non-clean dialogue-suite
  failures remain recorded in validation history.
- 2026-04-22: Not run for final actor AI acceptance. Outdoor idle/wander, pursuit, melee/ranged attack,
  actor-vs-actor hostility, fear/blind/stun/paralyze/death transitions, crowd steering, and indoor shared AI behavior
  remain pending for interactive/manual acceptance.
- 2026-04-21: Not run for Step 1; this slice only audited and documented the
  public actor-service API direction and did not change runtime behavior.
- 2026-04-21: Not run for Step 2; validation was limited to build and ctest
  because this slice only extracted named outdoor actor frame phase helpers and
  kept actor behavior logic unchanged.
- 2026-04-21: Not run for Step 3; validation was limited to build and ctest
  because this slice only added shared actor AI data packets and did not change
  runtime behavior or call sites.
- 2026-04-21: Not run for Step 4; validation was limited to build and ctest
  because this slice added the shared AI system class but did not connect it to
  outdoor or indoor runtime actor updates.
- 2026-04-21: Not run for Step 5 fact/update preview; validation was limited to
  build and ctest because the shared AI result is collected but not applied yet,
  leaving existing outdoor actor behavior as the runtime path.
- 2026-04-21: Not run for Step 5 terminal dead/dying actor result application;
  validation was limited to build and ctest. Outdoor death/dying, blood splat,
  corpse transition, and dead actor persistence manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active status-lock result application;
  validation was limited to build and ctest. Outdoor stun/paralyze hold, stun
  recovery, force-stun, and spell-effect timer expiry manual smoke remain
  pending.
- 2026-04-21: Not run for Step 5 active non-lock spell-effect timer result
  application; validation was limited to build and ctest. Outdoor slow, fear,
  blind, control/charm expiry, shrink expiry, and dark-grasp expiry manual smoke
  remain pending.
- 2026-04-21: Not run for Step 5 active frame timer result application;
  validation was limited to build and ctest. Outdoor attack cooldown, action
  timer, idle decision timer, and crowd timer manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active animation tick result application;
  validation was limited to build and ctest. Outdoor walk/attack/idle animation
  tick progression and slow-effect animation pacing manual smoke remain
  pending.
- 2026-04-21: Not run for Step 5 active combat engagement result application;
  validation was limited to build and ctest. Outdoor party detection, alert
  audio, actor-vs-actor hostility promotion, and friendly-near-party behavior
  manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active attack-impact result application;
  validation was limited to build and ctest. Outdoor party melee impact,
  actor-vs-actor melee damage, ranged projectile release, spell projectile
  release, and duplicate-impact prevention manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active attack-start result application;
  validation was limited to build and ctest. Outdoor melee/ranged attack start
  timing, selected attack ability, attack animation reset, facing, cooldown,
  and attack audio manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active combat-flow result application;
  validation was limited to build and ctest. Outdoor continue-attack,
  blind-wander, fear/flee, friendly-near-party stop behavior, and movement
  integration after shared-applied flow remain pending manual smoke.
- 2026-04-21: Not run for Step 5 active engage-target pursuit result
  application; validation was limited to build and ctest. Outdoor target pursuit
  start/continue, ranged pursuit, melee pursuit, cooldown standing, and crowd
  steering after shared-applied pursuit remain pending manual smoke.
- 2026-04-21: Not run for Step 5 active non-combat movement decision result
  application; validation was limited to build and ctest. Outdoor idle stand,
  bored idle, wander start/continue, return-home, water/terrain movement
  integration, and collision response after shared-applied non-combat decisions
  remain pending manual smoke.
- 2026-04-21: Not run for Step 5 active shared frame-commit result application;
  validation was limited to build and ctest. Outdoor animation commit, velocity
  clearing, movement enable/disable, crowd reset/preservation, water/terrain
  movement integration, and collision response after shared-applied decisions
  remain pending manual smoke.
- 2026-04-21: Not run for Step 5 active post-movement block fallout shared-AI
  slice; validation was limited to build and ctest. Outdoor blocked pursuit,
  blocked wandering/return-home, velocity clearing, short action timer, and
  stand-state fallout manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active post-collision crowd steering shared-AI
  slice; validation was limited to build and ctest. Outdoor crowd side-step,
  retreat, stand/bored pause, contacted-actor counting, and pursuit recovery
  manual smoke remain pending.
- 2026-04-21: Not run for Step 5 active projectile request shaping shared-AI
  slice; validation was limited to build and ctest. Outdoor ranged attack
  projectile release, spell projectile release, monster ranged-release combat
  record, and duplicate projectile prevention manual smoke remain pending.
- 2026-04-21: Not run for Step 5 outdoor movement integration extraction
  slice; validation was limited to build and ctest. Outdoor water restriction,
  steep-slope response, actor movement-controller collision, fallback ODM
  movement, post-movement block fallout, and crowd steering recovery manual
  smoke remain pending.
- 2026-04-22: Not run for Step 5 actor-vs-actor audio and death FX result
  request slice; validation was limited to build and ctest. Outdoor
  actor-vs-actor melee hit/death audio, duplicate audio prevention, and
  terminal blood-splat placement manual smoke remain pending.
- 2026-04-22: Not run for Step 5 shared-result application cleanup slice;
  validation was limited to build, ctest, and static `rg` audit because this
  slice removed an unused application mask without changing runtime behavior.
- 2026-04-22: Not run for Step 5 combat-event result cleanup slice; validation
  was limited to build, ctest, and static `rg` audit because this slice removed
  an unused duplicate result channel without changing runtime behavior.
- 2026-04-22: Not run for Step 5 shared behavior-mask preference slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor
  continue-attack, blind-wander, flee, friendly-near-party stop, pursuit,
  non-combat wander/return-home, and movement integration manual smoke remain
  pending.
- 2026-04-22: Not run for Step 5 status-lock legacy-skip cleanup slice;
  validation was limited to build and ctest. Outdoor stun hold,
  recover-from-stun, paralyze hold, force-stun, and duplicate legacy status
  processing manual smoke remain pending.
- 2026-04-22: Not run for Step 5 outdoor attack-impact fallback cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor melee
  impact, actor-vs-actor melee damage/audio, ranged projectile release, spell
  projectile release, and duplicate-impact prevention manual smoke remain
  pending.
- 2026-04-22: Not run for Step 5 outdoor status/death fallback cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor
  dying/dead transitions, stun recovery, paralyze hold, force-stun, and
  duplicate legacy status processing manual smoke remain pending.
- 2026-04-22: Not run for Step 5 missing-stats death fallback cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor
  dying/dead transition manual smoke remains pending for normal shared-result
  actors and for malformed/missing-stats actor data.
- 2026-04-22: Not run for Step 5 combat engagement fallback cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor party
  detection, alert audio, actor-vs-actor hostility promotion, and duplicate
  legacy engagement side-effect prevention manual smoke remain pending.
- 2026-04-22: Not run for Step 5 actor frame route fallback cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor
  active/background actor routing and inactive presentation manual smoke remain
  pending.
- 2026-04-22: Not run for Step 5 shared attack-completion behavior
  continuation slice; validation was limited to build, ctest, and static `rg`
  audit. Outdoor completed melee/ranged attack continuation, immediate
  re-engage, non-combat fallback after unengaged visible targets, and
  duplicate-impact prevention manual smoke remain pending.
- 2026-04-22: Not run for Step 5 outdoor combat-flow/non-combat fallback
  removal slice; validation was limited to build, ctest, and static `rg` audit.
  Outdoor continue-attack, blind-wander, fear/flee, friendly-near-party stop,
  pursuit, non-combat wander/return-home, frame commit, and movement
  integration manual smoke remain pending.
- 2026-04-22: Not run for Step 5 outdoor active timer fallback removal slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor
  animation tick progression, spell-effect expiry, attack cooldown, action
  timer, idle timer, and crowd timer manual smoke remain pending.
- 2026-04-22: Not run for Step 5 outdoor frame-commit fallback removal slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor frame
  commit, movement enable/disable, animation reset/keep-current behavior, and
  movement integration after shared-applied decisions remain pending manual
  smoke.
- 2026-04-22: Not run for Step 5 active movement fact reuse cleanup slice;
  validation was limited to build, ctest, and static `rg` audit. Outdoor target
  pursuit, melee-range crowd behavior, movement speed effects, and
  terrain/collision movement integration after shared-applied decisions remain
  pending manual smoke.
- 2026-04-22: Not run for Step 5 stale shared-result mask cleanup slice;
  validation was limited to build, ctest, and static `rg` audit because this
  slice only removed obsolete application masks and clarified the active
  shared-result gate name.
- 2026-04-22: Not run for Step 5 final outdoor shared-AI result audit; validation
  was limited to build, ctest, and static `rg` audit. Outdoor idle/wander,
  pursuit, melee/ranged attack, actor-vs-actor hostility, fear/blind/stun/paralyze,
  death, projectile request, and crowd steering manual smoke remain pending before
  the full actor AI done definition can be satisfied.
- 2026-04-22: Started Step 6 by removing the public `ActorFrameTimerInput` /
  `ActorFrameTimerResult` and `ActorAnimationTickInput` /
  `ActorAnimationTickResult` micro-structs plus their `GameplayActorService`
  methods. `GameplayActorAiSystem.cpp` now owns active frame timer aging and
  animation tick aging through private behavior-named helpers, while
  `GameplayActorService` no longer exposes those frame-aging contracts.
- 2026-04-22: Static `rg` audit confirms `advanceActorFrameTimers`,
  `advanceActorAnimationTick`, `ActorFrameTimerInput`, `ActorFrameTimerResult`,
  `ActorAnimationTickInput`, and `ActorAnimationTickResult` no longer appear in
  `game/gameplay`, `game/outdoor`, or `game/indoor`. Remaining Step 6 work
  includes demoting other public actor-frame micro decisions still used only by
  `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 frame-aging public micro-struct demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 frame-aging public micro-struct demotion slice;
  no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 frame-aging public micro-struct demotion slice;
  validation was limited to build, ctest, and static `rg` audit because the same
  timer math moved from public service helpers into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the obsolete public
  `ActorFrameRouteAction`, `ActorFrameRouteInput`, `ActorFrameRouteResult`, and
  `GameplayActorService::resolveActorFrameRoute` API. Active versus inactive
  actor routing is now owned by the outdoor active mask and missing-stats
  fallback path, so the old public frame-route micro-decision had no remaining
  callers.
- 2026-04-22: Static `rg` audit confirms no remaining `ActorFrameRoute` or
  `resolveActorFrameRoute` references in `game/gameplay`, `game/outdoor`, or
  `game/indoor`. Remaining Step 6 work includes demoting other public actor-frame
  micro decisions still used only by `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 frame-route public micro-decision removal slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 frame-route public micro-decision removal slice;
  no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 frame-route public micro-decision removal slice;
  validation was limited to build, ctest, and static `rg` audit because this
  slice removed an unused public actor-frame route helper.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorMovementBlockInput` / `ActorMovementBlockResult` and
  `ActorFrameCommitInput` / `ActorFrameCommitResult` micro-decision structs plus
  their `GameplayActorService` methods. `GameplayActorAiSystem.cpp` now owns
  active frame commit flags and post-movement blocked fallout through private
  behavior helpers that operate on coarse `ActorAiFacts` / `ActorAiUpdate` data.
- 2026-04-22: Static `rg` audit confirms `ActorMovementBlock`,
  `resolveActorMovementBlock`, `ActorFrameCommit`, and `resolveActorFrameCommit`
  references are confined to private helper names in `GameplayActorAiSystem.cpp`,
  with no public service, outdoor, or indoor references remaining. Remaining
  Step 6 work includes demoting other public actor-frame micro decisions still
  used only by `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 frame-commit and movement-block public
  micro-decision demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 frame-commit and movement-block public
  micro-decision demotion slice; no tests were found in the current build tree.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorStatusFrameAction`, `ActorStatusFrameInput`, `ActorStatusFrameResult`,
  and `GameplayActorService::resolveActorStatusFrame` micro-decision API.
  `GameplayActorAiSystem.cpp` now resolves active stun hold, stun recovery,
  paralyze hold, and force-stun outcomes through private shared-AI status
  helpers while still using `GameplayActorService::updateSpellEffectTimers` for
  shared spell-effect timer semantics.
- 2026-04-22: Static `rg` audit confirms `ActorStatusFrame` and
  `resolveActorStatusFrame` references are confined to private helper names in
  `GameplayActorAiSystem.cpp`, with no public service, outdoor, or indoor
  references remaining. Remaining Step 6 work includes demoting other public
  actor-frame micro decisions still used only by `GameplayActorAiSystem`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 status-frame public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 status-frame public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 frame-commit and movement-block public
  micro-decision demotion slice; validation was limited to build, ctest, and
  static `rg` audit because the same frame-commit and blocked-movement fallout
  math moved from public service helpers into private shared-AI helpers.
- 2026-04-22: Not run for Step 6 status-frame public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  the same stun/paralyze status-lock decision moved from a public service helper
  into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorAttackFrameInput` / `ActorAttackFrameResult` micro-structs and
  `GameplayActorService::resolveActorAttackFrame` method.
  `GameplayActorAiSystem.cpp` now resolves attack in-progress/completed state
  through the private `buildActorAttackFrameState` helper, and outdoor debug
  inspection computes the same booleans locally instead of depending on the
  public actor service micro-decision API.
- 2026-04-22: Static `rg` audit confirms `ActorAttackFrameInput`,
  `ActorAttackFrameResult`, `GameplayActorService::ActorAttackFrame`, and
  `GameplayActorService::resolveActorAttackFrame` no longer appear in
  `game/gameplay`, `game/outdoor`, or `game/indoor`. The only remaining
  `ActorAttackFrame` name is the private `ActorAttackFrameState` helper in
  `GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 attack-frame public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 attack-frame public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 attack-frame public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  the same attack completion predicate moved from a public service helper into
  a private shared-AI helper plus equivalent outdoor debug-only booleans.
- 2026-04-22: Continued Step 6 by removing the public
  `AttackStartInput` / `AttackStartResult`, `AttackDamageProfile`,
  `AttackImpactAction`, `AttackImpactInput` / `AttackImpactResult`, and
  `GameplayActorService::resolveAttackStart` /
  `GameplayActorService::resolveAttackImpact` micro-decision API.
  `GameplayActorAiSystem.cpp` now owns attack start timing, attack cooldown
  jitter, attack damage fallback, shrink/dark-grasp damage modifiers, and
  ranged/melee impact classification through private shared-AI helpers.
- 2026-04-22: Static `rg` audit confirms no remaining
  `GameplayActorService::Attack*` attack-start/impact public references,
  `resolveAttackStart`, `resolveAttackImpact`, `AttackStartInput`,
  `AttackStartResult`, `AttackImpactInput`, or `AttackImpactResult` in
  `game/gameplay`, `game/outdoor`, or `game/indoor`. The remaining
  `AttackImpactAction` name is private to `GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 attack-start/impact public micro-decision
  demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 attack-start/impact public micro-decision
  demotion slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 attack-start/impact public micro-decision
  demotion slice; validation was limited to build, ctest, and static `rg` audit
  because this moved the same attack timing and impact classification math from
  public service helpers into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorDeathFrameAction`, `ActorDeathFrameInput`, `ActorDeathFrameResult`, and
  `GameplayActorService::resolveActorDeathFrame` micro-decision API.
  `GameplayActorAiSystem.cpp` now resolves dead, mark-dead, and dying
  advancement through a private shared-AI helper, while the outdoor malformed
  missing-stats fallback uses a local fallback rule instead of keeping the
  service method public.
- 2026-04-22: Static `rg` audit confirms `ActorDeathFrame` and
  `resolveActorDeathFrame` references are confined to private helper names in
  `GameplayActorAiSystem.cpp` plus the outdoor-local
  `MissingStatsActorDeathFrame` fallback. No public service, outdoor
  service-call, or indoor references remain.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 death-frame public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 death-frame public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 death-frame public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  this moved the same death/dying frame rule from a public service helper into
  private shared-AI and outdoor malformed-actor fallback helpers.
- 2026-04-22: Continued Step 6 by removing the public `CombatFlowAction`,
  `CombatFlowDecisionInput` / `CombatFlowDecisionResult`,
  `CombatFlowApplicationInput` / `CombatFlowApplicationResult`, and
  `GameplayActorService::resolveCombatFlowDecision` /
  `GameplayActorService::resolveCombatFlowApplication` micro-decision API.
  `GameplayActorAiSystem.cpp` now resolves continue-attack, blind-wander,
  flee, friendly-near-party, and engage/non-combat routing through private
  shared-AI helpers that emit the same coarse state, animation, movement, yaw,
  velocity, action-timer, and idle-timer patches.
- 2026-04-22: Static `rg` audit confirms `GameplayActorService::CombatFlow`,
  `resolveCombatFlow`, `CombatFlowDecision`, and `CombatFlowApplication` no
  longer appear in public service, outdoor, or indoor code. Remaining
  `CombatFlow` names are private helpers in `GameplayActorAiSystem.cpp`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 combat-flow public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 combat-flow public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 combat-flow public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  this moved the same combat-flow decision/application logic from public service
  helpers into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `NonCombatBehaviorAction`, `NonCombatBehaviorInput`,
  `NonCombatBehaviorResult`, and
  `GameplayActorService::resolveNonCombatBehavior` micro-decision API.
  `GameplayActorAiSystem.cpp` now resolves stand, idle, wander, return-home, and
  continue-move behavior through private shared-AI helpers while keeping the
  reusable idle behavior helper public for outdoor inactive presentation.
- 2026-04-22: Static `rg` audit confirms `NonCombatBehaviorInput`,
  `NonCombatBehaviorResult`, `NonCombatBehaviorAction`, and
  `resolveNonCombatBehavior` no longer appear in `game/gameplay`,
  `game/outdoor`, or `game/indoor`.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 non-combat public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 non-combat public micro-decision demotion slice;
  no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 non-combat public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  the same non-combat stand/wander/return-home rule moved from a public service
  helper into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `RangedAbilityCommitInput`, `CombatAbilityDecisionInput` /
  `CombatAbilityDecisionResult`, `CombatEngageDecisionInput` /
  `CombatEngageDecisionResult`, `CombatEngageApplicationInput` /
  `CombatEngageApplicationResult`, `PursueActionInput` / `PursueActionResult`,
  `GameplayActorService::chooseAttackAbility`,
  `GameplayActorService::resolveAttackAbilityConstraints`,
  `GameplayActorService::shouldCommitToRangedAbility`,
  `GameplayActorService::resolveCombatAbilityDecision`,
  `GameplayActorService::resolveCombatEngageDecision`,
  `GameplayActorService::resolveCombatEngageApplication`, and
  `GameplayActorService::resolvePursueAction` micro-decision API.
  `GameplayActorAiSystem.cpp` now owns attack-ability choice, ranged commit,
  engage start/continue/stand selection, and pursue-action shaping through
  private shared-AI helpers.
- 2026-04-22: Static `rg` audit confirms the removed combat-engage public
  service API names no longer appear in `GameplayActorService.h`,
  `GameplayActorService.cpp`, `game/outdoor`, `game/indoor`, `engine`,
  `editor`, or `tools`. `CombatEngagementInput` / `CombatEngagementResult`
  intentionally remain public because outdoor still uses them for fact shaping
  and debug inspection outside the valid active behavior body.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 combat-engage public micro-decision demotion
  slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 combat-engage public micro-decision demotion
  slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 combat-engage public micro-decision demotion
  slice; validation was limited to build, ctest, and static `rg` audit because
  the same attack choice, ranged commit, engage routing, and pursue-action rules
  moved from public service helpers into private shared-AI helpers.
- 2026-04-22: Continued Step 6 by removing the public
  `ActorMoveSpeedInput` / `ActorMoveSpeedResult` and
  `ActorPartyProximityInput` / `ActorPartyProximityResult` micro-structs plus
  `GameplayActorService::resolveActorMoveSpeed` and
  `GameplayActorService::resolveActorPartyProximity`. `GameplayActorAiSystem`
  and outdoor fact/debug shaping now use direct behavior helpers:
  `GameplayActorService::effectiveActorMoveSpeed` and
  `GameplayActorService::partyIsVeryNearActor`.
- 2026-04-22: Static `rg` audit confirms `ActorMoveSpeedInput`,
  `ActorMoveSpeedResult`, `resolveActorMoveSpeed`, `ActorPartyProximityInput`,
  `ActorPartyProximityResult`, and `resolveActorPartyProximity` no longer
  appear in game, engine, editor, or tools C++ code.
- 2026-04-22: `cmake --build build --target openyamm -j25` completed
  successfully after the Step 6 move-speed/proximity public micro-decision
  demotion slice.
- 2026-04-22: `ctest --test-dir build --output-on-failure` completed
  successfully after the Step 6 move-speed/proximity public micro-decision
  demotion slice; no tests were found in the current build tree.
- 2026-04-22: Not run for Step 6 move-speed/proximity public micro-decision
  demotion slice; validation was limited to build, ctest, and static `rg` audit
  because the same move-speed and party-proximity formulas are still called from
  the same fact collection and debug-inspection sites through smaller public
  helpers.
- 2026-04-22: Root acceptance closure reran static actor AI audits, `cmake --build build --target openyamm -j25`,
  `ctest --test-dir build --output-on-failure`, `timeout 300s build/game/openyamm
  --headless-run-regression-suite indoor`, and `timeout 300s build/game/openyamm
  --headless-run-regression-suite dialogue`. Build and CTest passed, CTest still has no registered tests, indoor
  passed with `passed=21 failed=0`, and dialogue completed cleanly with `passed=242 failed=0`. Relevant headless
  actor smoke cases passed, including friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, party arrow and spell projectile actor hits, fireball splash, actor-vs-actor hostile
  damage, visible spell impact, attack persistence, post-attack recovery, corpse loot, and actor death audio. No
  separate interactive actor play session was run.
- 2026-04-22: Acceptance follow-up fixed a headless bgfx resource crash outside
  actor AI ownership. `cmake --build build --target openyamm -j25`, `ctest
  --test-dir build --output-on-failure`, and the indoor headless suite passed;
  full dialogue now completes instead of exiting 139 and reports `passed=236
  failed=6`. Relevant actor smoke still passes in the dialogue log, including
  friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence,
  post-attack recovery, and actor death audio. Interactive actor manual smoke is
  still not run.
- 2026-04-22: Acceptance follow-up fixed the six residual dialogue diagnostics
  outside actor AI ownership. `cmake --build build --target openyamm -j25`
  passed; `ctest --test-dir build --output-on-failure` passed with no
  registered tests; `timeout 300s build/game/openyamm
  --headless-run-regression-suite indoor` passed with `passed=21 failed=0`; and
  full dialogue now completes cleanly with `passed=242 failed=0`. Relevant
  non-interactive actor smoke still passed in the dialogue log, including
  friendly idle/wander, hostile pursuit, melee attack entry, mixed ranged attack
  choice/release/party hit, actor-vs-actor hostile damage, attack persistence,
  post-attack recovery, and actor death audio. Interactive actor manual smoke is
  still not run.
- 2026-04-22: A19 removed the remaining top-level control leakage from
  `ActorAiUpdate`: `statusLockHandled`, `crowdSteeringHandled`,
  `preserveCrowdSteering`, and top-level `resetCrowdSteering` no longer exist in
  game code. Movement application facts now live on `ActorMovementIntent`,
  including move speed, target position, target edge distance, melee pursuit,
  melee range, crowd reset, and post-move crowd-probe update.
- 2026-04-22: A19 deleted `OutdoorActorAiFrameApplication` from game code.
  Outdoor applies `ActorAiFrameResult` directly and keeps only world-owned
  movement integration, collision, inactive presentation, missing-stats fallback,
  projectile/audio/FX application, and post-movement crowd fact collection.
- 2026-04-22: A19 renamed the shared state/animation result shape away from
  patch terminology (`ActorStateUpdate`, `ActorAnimationUpdate`,
  `ActorAiUpdate::state`, `ActorAiUpdate::animation`). Private shared-AI helper
  result names were also moved from `*Patch` to `*Outcome` / `*Update`, so the
  outdoor-facing result seam is no longer a patch/mask application layer.
- 2026-04-22: Validation after A19: `cmake --build build --target openyamm
  -j25` passed; `ctest --test-dir build --output-on-failure` passed with no
  registered tests.
- 2026-04-22: A20 split outdoor `ActorAiFrameResult` application into semantic
  helpers for state, animation, movement intent, attack request, and terminal
  actor fallout. The old `updateOutdoorActorsForStep` name was replaced with
  `updateOutdoorInactiveAndInvalidActors` because that pass now handles only
  missing-stats fallout and inactive actor presentation.
- 2026-04-22: A20 follow-up split frame-level projectile/audio/FX request
  application into `applyOutdoorActorRequests` and narrower request helpers, so
  `applyOutdoorActorAiFrameResult` now owns only per-actor update dispatch plus
  the request handoff.
- 2026-04-22: Validation after A20: `cmake --build build --target openyamm
  -j25` passed; `ctest --test-dir build --output-on-failure` passed with no
  registered tests.

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
