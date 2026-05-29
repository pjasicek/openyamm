# OE Flying Monsters And Turn-Based Implementation Plan

Date: 2026-04-09

Purpose:
- Capture observed behavior from the local OpenEnroth reference.
- Turn that behavior into an implementable OpenYAMM plan.
- Keep OE as behavioral reference only. Do not copy OE code.

Scope:
- Flying monster movement, AI, and collision behavior.
- Full turn-based combat loop:
  - turn stages
  - initiative and recovery
  - player movement points
  - monster action selection
  - attack and projectile sequencing
  - animation timing
  - pending projectile handling
  - turn-based UI states

Non-goals:
- Direct code translation from OE.
- Refactoring OE quirks into a new combat design before parity exists.
- Indoor/outdoor AI redesign beyond OE parity.

## Reference Sources

Primary OE files inspected:
- [reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.cpp)
- [reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.h)
- [reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngineEnums.h](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngineEnums.h)
- [reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/Actor.cpp)
- [reference/OpenEnroth-git/src/Engine/Objects/Character.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/Character.cpp)
- [reference/OpenEnroth-git/src/Engine/Objects/SpriteObject.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Objects/SpriteObject.cpp)
- [reference/OpenEnroth-git/src/Engine/AttackList.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/AttackList.cpp)
- [reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Outdoor.cpp)
- [reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Indoor.cpp)
- [reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/Collisions.cpp)
- [reference/OpenEnroth-git/src/Engine/Graphics/TurnBasedOverlay.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Graphics/TurnBasedOverlay.cpp)
- [reference/OpenEnroth-git/src/Engine/Spells/CastSpellInfo.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Engine/Spells/CastSpellInfo.cpp)
- [reference/OpenEnroth-git/src/Application/Game.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Application/Game.cpp)
- [reference/OpenEnroth-git/src/Io/KeyboardInputHandler.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Io/KeyboardInputHandler.cpp)
- [reference/OpenEnroth-git/src/Io/Mouse.cpp](/home/pjasicek/github/OpenYAMM/reference/OpenEnroth-git/src/Io/Mouse.cpp)

## OE Behavior Summary

### 1. Flying Monsters

OE does not have a separate flying-monster combat brain. Flying monsters use the same target selection and pursue/attack logic as ground monsters, with a few important specializations:

- Their pursue helpers bias target height.
- Their walking movement applies vertical velocity from pitch.
- Their outdoor collision radius changes when flying.
- Some grounded restrictions are skipped when flying.
- Flying is disabled when the monster cannot act.

#### 1.1 Targeting And Direction

Observed in `Actor::GetDirectionInfo` and `Actor::AI_Pursue1/2/3`.

Key rules:
- Direction is computed from actor center at `pos + height * 0.75`.
- When the target is the party and a preferred Z is provided, the target point is `party.pos + preferredZ`.
- Flying monsters set preferred Z only when the party is not flying.
- Preferred Z rules:
  - missile-capable flying monster outdoors: `radius + 512`
  - otherwise: `party.height`

Behavioral result:
- Flying ranged monsters prefer to hover above the party rather than flattening to ground level.
- Flying melee monsters still angle toward the party body height instead of terrain height.

#### 1.2 Pursue Modes

OE uses three shared pursue helpers:
- `AI_Pursue1`: close-in pursue with slight left/right offset
- `AI_Pursue2`: direct pursue with a stop distance
- `AI_Pursue3`: angled pursue with randomized sidestep

Flying-monster-specific behavior inside those helpers:
- Preferred target Z is applied as described above.
- Pitch is taken from the direction info and stored on the actor.
- State becomes `Pursuing`.

Shared rules that still apply to flying monsters:
- If within melee range, they stand or bored instead of continuing pursue.
- Treants bypass this and stand.
- Zero move speed forces stand instead of movement.

#### 1.3 Runtime Movement

Observed in `Outdoor.cpp` and `Indoor.cpp`.

Outdoor movement:
- If the actor animation is walking:
  - base speed = `moveSpeed`
  - slowed doubles recovery and reduces movement speed
  - pursuing or fleeing doubles speed
  - in turn-based `TE_WAIT`, speed is multiplied by `1.666666666666667`
  - speed is capped at `1000`
- Horizontal velocity is derived from yaw.
- If flying, vertical velocity is derived from pitch.
- If not walking, velocity decays by roughly `0.8926` after collision resolution and by another branch-specific decay while idle.

Indoor movement:
- Same overall pattern.
- Flying actors also derive Z velocity from pitch while walking.
- Indoor non-flying actors get explicit gravity.

Important parity note:
- Flying monsters are not just “gravity disabled.”
- Their motion is still integrated through the same actor movement path and same state machine.

#### 1.4 Collision Behavior

Observed in `ProcessActorCollisionsODM` and `ProcessActorCollisionsBLV`.

Outdoor collision:
- Non-flying actor collision radius is hardcoded to `40`.
- Flying actor collision radius uses the actor’s real `radius`.
- Collision still checks:
  - models
  - decorations
  - party
  - sprite objects
  - nearby actors
- Actor-to-actor collisions can cause:
  - stand/bored if in a crowd
  - face-object if both are friendly
  - flee otherwise
- Hitting the party:
  - hostile monsters zero XY velocity
  - party invisibility is broken
- Hitting decorations:
  - velocity is reflected away from the decoration
- Hitting faces:
  - floor snaps Z and cancels downward Z velocity
  - wall collision pushes away along face normal and can rotate yaw

Indoor collision:
- Uses full actor cylinder based on radius and height.
- Performs wall, floor, decoration, actor, party, and sprite collision.
- Non-flying actors are prevented from walking into indoor sky and prevented from stepping off large ledges.
- Those restrictions are skipped when `isFlying`.

Important parity note:
- Outdoor flying collision is not just “same as ground with no gravity.”
- The radius difference alone materially affects crowding and obstacle contact.

#### 1.5 Flying Disable Conditions

Observed in actor movement update.

Flying is effectively disabled for motion/collision if the actor cannot act, including:
- stoned
- paralyzed
- dead/dying/removed/disabled

That means a disabled flying monster does not keep special flying motion.

### 2. Turn-Based Mode

OE turn-based combat is a staged loop with one shared queue of players and nearby monsters.

Stages:
- `TE_NONE`
- `TE_WAIT`
- `TE_ATTACK`
- `TE_MOVEMENT`

High-level loop:
1. Start turn-based mode.
2. Monsters do movement phase in `TE_WAIT`.
3. Monsters resolve attacks and queue timing in `TE_ATTACK`.
4. Party enters `TE_MOVEMENT` and spends movement points.
5. Party attack or cast ends movement and advances back toward monster phase.

This is not a strict “one actor takes a full turn at a time” system. It is a staged hybrid.

## OE Turn Engine Details

### 2.1 Queue Contents

Each queue element tracks:
- packed actor/character id
- initiative
- action length
- AI action type

Observed ordering rules:
- lower initiative acts first
- players win ties over monsters
- lower id wins same-type ties
- non-acting units are pushed out with initiative `1001`

### 2.2 Turn-Based Start

Observed in `TurnEngine::Start`.

Initialization behavior:
- event timer enters turn-based mode
- UI sound plays
- `turn_initiative = 100`
- `turn_stage = TE_WAIT`
- `ai_turn_timer = 64_ticks`
- all acting characters are added
- all nearby active actors are added

Initial initiatives:
- characters with existing recovery:
  - initiative = `timeToRecovery * 0.46875`
- monsters:
  - randomized to `1`, `3`, or `5`
  - then `+16`
- active players with zero recovery:
  - sorted by attack recovery time
  - assigned initiatives `2, 3, 4, ...`

Behavioral result:
- ready players generally act early.
- monsters enter with slight random staggering.

### 2.3 Queue Stepping

Observed in `StepTurnQueue` and `_406457`.

Core mechanics:
- `turn_initiative` starts at `100`.
- Queue stepping decrements all actor initiatives together.
- It stops when:
  - the queue head reaches `0`, or
  - `turn_initiative` reaches `0`

When a player takes an action:
- player recovery becomes new initiative
- minimum recovery is `30_ticks`
- all initiatives are decremented until the next actor reaches front or the turn budget is exhausted

Behavioral result:
- turn-based recovery is not a separate hidden timer.
- it is directly converted into initiative in the queue.

### 2.4 Turn Stages

#### `TE_WAIT`

Monster movement phase.

Observed behavior:
- first frame of wait:
  - `ActorAISetMovementDecision()`
- while timer remains:
  - `ActorAIDoAdditionalMove()`
- when timer expires:
  - `ActorAIStopMovement()`
  - switch toward `TE_ATTACK`

Additional details:
- `ai_turn_timer` begins at `64_ticks`
- monster walking speed is multiplied by `1.666666666666667`
- party cannot spend movement here
- party attacks and casts are blocked here

#### `TE_ATTACK`

Attack and queue resolution phase.

Observed behavior:
- if `turn_initiative == 100`:
  - `StartTurn()`
  - `SetAIRecoveryTimes()`
- otherwise:
  - `_4065B0()`
  - `SetAIRecoveryTimes()`
- once queue resolution for the current cycle is done:
  - `NextTurn()`

Additional details:
- queued monster attack animations continue here
- monster melee damage and projectile creation are triggered when attack animations finish
- player attacks and spell casts are allowed here
- if projectile or spell sprites are pending, the phase is held

#### `TE_MOVEMENT`

Party movement phase.

Observed behavior:
- party gets `uActionPointsLeft = 130`
- each move or strafe input costs `26`
- there are 5 movement chunks
- if AP reaches `0` or player ends movement, engine returns to `TE_WAIT`

During movement:
- monsters can retarget through `ActorAIChooseNewTargets()`
- party attack/cast does not happen as free movement continuation
- pressing pass or certain attack/cast attempts sets the finished flag

### 2.5 Pending Projectile Actions

Observed in `TurnEngine`, `CastSpellInfo.cpp`, and `SpriteObject.cpp`.

OE uses a pending-action stall:
- projectiles and many spell sprites created in turn-based are flagged with `SPRITE_HALT_TURN_BASED`
- each such object increments `pending_actions`
- when the sprite impacts, disappears, or interacts:
  - the flag is cleared
  - `pending_actions` is decremented

`NextTurn()` behavior:
- if `pending_actions > 0`, the engine sets the pending flag and does not advance

Behavioral result:
- turn-based waits for in-flight spells and projectiles to resolve before advancing.

### 2.6 Attack Bucket

Observed in `AttackList.cpp` and `evaluateAoeDamage`.

OE uses a deferred damage bucket:
- `pushMeleeAttack(...)`
- `pushAoeAttack(...)`

This bucket is processed by `evaluateAoeDamage()` later in the frame.

Behavioral result:
- animation completion and projectile impact enqueue damage work.
- actual damage application is centralized later.

This is the “bucket” behavior worth preserving in OpenYAMM.

### 2.7 Monster Attack Animations

Observed in `Actor::AI_MeleeAttack`, `AI_MissileAttack1/2`, `AI_SpellAttack1/2`, and `TurnEngine::AIAttacks`.

Rules:
- Monster must have LOS to attack.
- On attack start:
  - yaw is aligned to target
  - attack state is set
  - current action length is loaded from the corresponding animation
  - velocity is zeroed
  - recovery is set
- In turn-based:
  - monster recovery uses raw monster base recovery
- In realtime:
  - recovery uses scaled realtime conversion

Animation-specific behavior:
- melee uses melee attack animation
- missile and spell attacks use ranged attack animation
- some monster spells use a shortened pre-attack/fidget path instead of a visible attack animation

Attack completion:
- when current action time reaches current action length:
  - melee queues melee damage
  - ranged/spell attacks spawn their projectile or effect
  - actor returns to stand

### 2.8 Player Recovery And Actions

Observed in `Character.cpp`, `CastSpellInfo.cpp`, and `Game.cpp`.

Melee:
- realtime melee sets recovery directly
- turn-based melee calls `ApplyPlayerAction()`

Spell casting:
- spell recovery is written into `pTurnBasedCharacterRecoveryTimes[caster]`
- then the turn engine applies the action

Steal:
- also uses `ApplyPlayerAction()` in turn-based

Minimum player recovery in turn-based:
- `30_ticks`

Important parity note:
- player recovery in turn-based should remain tied to the queue system, not to the realtime recovery decrement path.

### 2.9 Player Input Gating

Observed in `KeyboardInputHandler.cpp`, `Mouse.cpp`, and `Game.cpp`.

Movement input:
- blocked in `TE_WAIT`
- blocked in `TE_ATTACK`
- allowed in `TE_MOVEMENT`
- each move/strafe input costs `26` AP

Attacks:
- blocked in `TE_WAIT`
- blocked in `TE_MOVEMENT`
- allowed in `TE_ATTACK` if no pending actions

Spellbook:
- opening/selecting/casting is blocked in `TE_MOVEMENT`

Pass:
- in `TE_MOVEMENT`, sets finished flag
- outside movement, can act as a recovery-consuming pass

Turn-based toggle off:
- allowed only from `TE_MOVEMENT`
- or if queue head is a player

Mouse stealing:
- in `TE_MOVEMENT`, clicking a steal target also marks movement finished

### 2.10 Timers And Simulation

Observed in `Timer` and engine loop behavior.

Key OE behavior:
- event timer is set to turn-based mode
- while turn-based is on, normal time advancement is effectively paused
- frame dt still exists for UI and animation update paths
- turn-based-specific sequencing still advances using explicit turn engine logic

Behavioral result:
- turn-based is not just “slow realtime.”
- it is a paused world with explicit step logic layered on top.

### 2.11 Turn-Based Overlay

Observed in `TurnBasedOverlay.cpp`.

States:
- initial opening animation
- wait icon
- attack icon
- movement icon

Movement icon behavior:
- icon index is based on `5 - uActionPointsLeft / 26`

Behavioral result:
- the overlay visibly consumes the 5 movement chunks.

## OpenYAMM Implementation Plan

The implementation should be staged. Do not try to land full parity in one patch.

### Phase 1: Core Turn Engine Skeleton

Goal:
- Introduce OE-equivalent staged turn flow without yet matching every attack detail.

Implement:
- `TurnEngineStep` enum:
  - `None`
  - `Wait`
  - `Attack`
  - `Movement`
- queue element struct:
  - actor/character id
  - initiative
  - action length
  - AI action type
- runtime state:
  - `turnStage`
  - `turnInitiative`
  - `actionPointsLeft`
  - `pendingActions`
  - `aiTurnTimer`
  - flags
  - queue

Runtime behavior:
- turn-based start populates queue from:
  - living party members
  - nearby active monsters
- initialize OE-style initiatives
- sort queue OE-style
- implement stage progression:
  - `Wait -> Attack -> Movement -> Wait`

Acceptance:
- can toggle turn-based
- stage changes occur in the right order
- movement AP decrements in 5 chunks

### Phase 2: Player Input Gating

Goal:
- Match OE input restrictions by stage.

Implement:
- movement only in `Movement`
- attacks and steals only in `Attack`
- spellbook interaction blocked in `Movement`
- pass finishes movement in `Movement`
- turn-based cannot be exited except under OE-equivalent rules

Acceptance:
- gameplay inputs behave differently per stage
- no realtime movement leakage while in wait/attack

### Phase 3: Player Recovery Integration

Goal:
- Convert player actions into queue initiative instead of relying on realtime-only recovery.

Implement:
- per-character turn-based recovery staging buffer
- OE-style `applyPlayerAction()`
- OE-style minimum `30_ticks`
- queue stepping after player action

Acceptance:
- melee, spell cast, and pass advance queue correctly
- active character handoff follows queue order

### Phase 4: Monster Turn-Based AI

Goal:
- Recreate OE monster participation in `Wait` and `Attack`.

Implement:
- movement decision pass in `Wait`
- additional movement pass while timer runs
- movement stop at end of `Wait`
- target selection
- AI action selection:
  - melee
  - ranged
  - spell
  - stand
  - flee
  - pursue
- AI recovery setup for initiative-zero actors

Acceptance:
- monsters move during `Wait`
- monsters attack during `Attack`
- movement and attack phases are visually distinct

### Phase 5: Deferred Damage And Pending Projectiles

Goal:
- Match OE sequencing for melee/AOE resolution and projectile stalls.

Implement:
- attack bucket for:
  - melee hits
  - AOE impacts
- per-sprite turn-based halt flag
- `pendingActions` increment on flagged projectile/effect creation
- `pendingActions` decrement on impact/removal/interaction
- `NextTurn` stall while pending actions remain

Acceptance:
- in-flight projectiles hold the turn
- melee and AOE damage are resolved through the bucket, not ad hoc

### Phase 6: Flying Monster Parity

Goal:
- Reproduce OE flying behavior using shared AI plus flying-specific motion/collision rules.

Implement:
- preferred target Z rules in pursue helpers
- pitch-driven vertical motion for flying actors
- disable flying motion when actor cannot act
- outdoor flying collision radius uses actor radius
- indoor flying skips non-flying ledge/sky restrictions
- preserve shared collision reactions:
  - actor
  - party
  - decoration
  - face

Acceptance:
- flying ranged monsters hover above party
- flying melee monsters pursue at party body height
- flying collision differs from ground collision outdoors

### Phase 7: UI And Feedback

Goal:
- Surface OE-equivalent state to the player.

Implement:
- turn-based overlay states:
  - initial
  - wait
  - attack
  - movement
- 5-step movement AP indicator
- optional portrait readiness indicators if desired for parity

Acceptance:
- stage transitions are readable
- movement chunk consumption is visible

### Phase 8: Diagnostics And Regression Coverage

Goal:
- Make the new system debuggable before polishing.

Add diagnostics for:
- turn-based start/stop
- queue ordering
- player recovery application
- pending projectile stall and release
- monster movement phase execution
- flying monster vertical pursue behavior
- indoor and outdoor collision edge cases

Suggested tests:
- single melee monster in outdoor map
- single ranged flying monster in outdoor map
- single flying melee monster in indoor map
- mixed melee/ranged/flying group
- projectile spell cast during turn-based
- bow attack during turn-based
- pass during movement
- steal during turn-based attack phase
- slow effect on monster recovery
- party invisibility broken by collision

## Recommended OpenYAMM State Additions

### Turn Engine State

Add a dedicated runtime object, likely under `game/turn/` or `game/combat/`, with:
- queue vector
- `turnStage`
- `turnInitiative`
- `actionPointsLeft`
- `pendingActions`
- `aiTurnTimer`
- player pending recovery array
- turn flags

Do not scatter this across input/controller/renderer classes.

### Actor Runtime Additions

Ensure actor runtime exposes:
- current action state
- current action time
- current action length
- yaw and pitch
- move speed
- radius and height
- flying capability
- monster recovery

### Sprite Runtime Additions

Add explicit per-sprite turn-based flags:
- halt turn-based until resolved
- source caster id/type if not already present

### Attack Bucket

Add a dedicated damage bucket container rather than direct-impact damage in every path.

Minimum entries:
- source pid
- ability/source type
- world position
- effect radius or reach
- melee vs aoe mode

## Runtime Sequencing To Preserve

OpenYAMM should preserve this order each frame while in turn-based:

1. Process turn engine stage logic.
2. Advance actor action timers needed for the current stage.
3. Advance projectiles/spell sprites.
4. Resolve attack bucket.
5. Allow stage advancement only if pending actions permit it.
6. Render turn-based overlay for current stage.

The key parity rule is:
- queued attacks and in-flight projectiles must not be allowed to race ahead of the stage machine.

## OE Constants Worth Preserving First

Preserve these values initially for parity:
- turn initiative budget: `100`
- AI wait timer start: `64_ticks`
- player movement AP: `130`
- AP per move/strafe: `26`
- minimum turn-based player recovery: `30_ticks`
- monster wait-phase movement multiplier: `1.666666666666667`
- melee range: `307.2f`
- flying ranged preferred Z outdoors: `radius + 512`

These can be moved to config later if needed, but do not parameterize them before parity exists.

## Risks And OE Quirks

### Risks

- Reusing current realtime recovery directly in turn-based will produce wrong queue behavior.
- Letting projectiles resolve outside a pending-action stall will break stage pacing.
- Treating flying as only “no gravity” will miss pursue height and collision differences.
- Skipping the deferred attack bucket will create ordering bugs for melee and AOE.

### OE Quirks To Preserve Initially

- The staged `Wait/Attack/Movement` flow instead of a simpler unit-by-unit turn system.
- Randomized initial monster initiatives.
- Five fixed movement chunks.
- Queue-based action order with player-preferred tie breaks.
- Flying outdoor collision radius difference.

Potential cleanup can be discussed only after parity is working.

## Suggested File Targets In OpenYAMM

Likely new or updated areas:
- `game/combat/TurnEngine.h`
- `game/combat/TurnEngine.cpp`
- `game/combat/AttackBucket.h`
- `game/combat/AttackBucket.cpp`
- `game/outdoor/OutdoorGameView.cpp`
- `game/outdoor/OutdoorMovementDriver.cpp`
- `game/outdoor/OutdoorPartyRuntime.cpp`
- `game/outdoor/OutdoorRenderer.cpp`
- `game/objects/ActorRuntime.*`
- `game/objects/ProjectileRuntime.*`
- `game/ui/GameplayHudRenderer.cpp`
- `game/ui/GameplayPartyOverlayRenderer.cpp`
- `game/outdoor/HeadlessOutdoorDiagnostics.cpp`

Exact file placement can change, but the responsibilities should remain separated:
- turn logic
- actor motion
- projectile stall
- deferred damage
- UI feedback

## Implementation Order Recommendation

1. Land turn engine state and queue with no UI polish.
2. Gate player input by stage.
3. Hook player recovery into the queue.
4. Hook monster movement and monster attack staging.
5. Add pending projectile stall and attack bucket.
6. Add flying-monster height bias and collision differences.
7. Add turn-based overlay and diagnostics.
8. Tune edge cases only after the system is behaviorally complete.

## Deliverable Definition

The feature is ready for parity review when all of the following are true:
- turn-based start/stop works reliably
- stage transitions match OE flow
- player movement uses 5 AP chunks
- player recovery feeds initiative
- monster attack animations gate actual attack resolution
- pending projectiles stall turn advancement
- flying monsters pursue and collide differently from grounded monsters
- basic outdoor and indoor combat scenarios behave consistently
