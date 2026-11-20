# Fix plan E: turn-based doors, arena factions, TB monster speed, Arcomage AI, outdoor slopes

Line numbers checked against the working tree on 2026-10-25 (HEAD 2476b1e90 + unstaged edits).
**Preserve the unstaged `int64_t` stat-snapshot edits** in `game/scene/IndoorSceneRuntime.cpp` (~:967-968),
`game/scene/OutdoorSceneRuntime.cpp`, `game/gameplay/InteractiveDecorationRules.{h,cpp}`. Edit around them; never
restore/stash. All fixes are shared code (Standard MMerge and MAW alike).

---

## 1. Indoor doors freeze in turn-based mode (small)

**Cause.** `IndoorRenderer::render` (game/indoor/IndoorRenderer.cpp:3800) calls
`m_pSceneRuntime->advanceSimulation()` only when `!turnBasedCombatRuntime().active()`. Mechanisms are stepped
inside it (game/scene/IndoorSceneRuntime.cpp:685-735). OE steps doors every frame with `pEventTimer->dt()`, which
keeps ticking in TB (OE `Indoor.cpp:1496-1500`, `Time/Timer.cpp:16-28`).

**Outdoor check: not affected.** Outdoor model mechanisms run in `OutdoorWorldRuntime::updateWorld`
(OutdoorWorldRuntime.cpp:7978-), called from `GameApplication.cpp:11414` with no TB gate (only pause/console/inspect).
Event timers in TB are advanced on both sides by `advanceTurnBasedGameMinutes` per completed turn
(IndoorSceneRuntime.cpp:509-520, OutdoorSceneRuntime.cpp:273-), so timers need no change.

**Change.**
- `IndoorSceneRuntime.h:130`: add `bool advanceMechanisms(float deltaMilliseconds);` next to `advanceSimulation`.
- `IndoorSceneRuntime.cpp`: move the block from `if (!hasMovingMechanism(*m_eventRuntimeState))` (:685) to the end
  of `advanceSimulation` (:735) into the new function unchanged. `advanceSimulation` ends with
  `return advanceMechanisms(deltaMilliseconds) || stateChanged;` (keep the `stateChanged` semantics).
  ```cpp
  bool IndoorSceneRuntime::advanceMechanisms(float deltaMilliseconds)
  {
      if (!m_eventRuntimeState || !m_mapDeltaData || deltaMilliseconds <= 0.0f)
      {
          return false;
      }

      if (!hasMovingMechanism(*m_eventRuntimeState))
      {
          m_mechanismAccumulatorMilliseconds = 0.0f;
          return false;
      }
      // ... existing accumulator loop, geometry refresh and clamp, unchanged ...
      return mechanismSteps > 0;
  }
  ```
- `IndoorRenderer.cpp:3800`: drop the TB term from the condition. Pick the call by mode; everything after it
  (geometry upload, rebuild) stays as is:
  ```cpp
  if (allowWorldSimulation && m_pSceneRuntime != nullptr)
  {
      const bool turnBasedActive = gameSession.turnBasedCombatRuntime().active();
      ...
      const bool simulationAdvanced = turnBasedActive
          ? m_pSceneRuntime->advanceMechanisms(deltaMilliseconds)
          : m_pSceneRuntime->advanceSimulation(deltaMilliseconds);
  ```

**Edge cases.**
- Game minutes, timers, MM9 teacher schedule and positioned transitions must stay frozen in TB. They remain in
  `advanceSimulation` only.
- `applyMovingMechanismSupportMovement` (party on a lift) now runs in TB too. That is correct, since the original
  moves the party with the platform.
- Door sound (`updateMechanismAudio`) plays in TB. OE plays it too.
- Out of scope, worth noting: `updatePartyFaceTriggers()` (:663) is also skipped in TB, so pressure plates and
  face-enter events don't fire while the party walks in the movement stage. In OE, `BLV_ProcessPartyActions` runs
  in TB. Check this separately before changing it.
- `ScenarioRuntimeDriver.cpp:559/1102/2777` calls `advanceSimulation` with no TB gate, so scenarios never showed
  this bug. If the runner should mirror the game, gate it the same way.

**Verification.** Extend `tests/IndoorMovingFloorRuntimeTests.cpp`, which already builds an `IndoorSceneRuntime`,
triggers mechanism 19 at :95 and steps `advanceSimulation` at :110. Add the case "indoor mechanisms advance without
the world simulation (turn-based)": trigger the door, call `scene.advanceMechanisms(1000/60)` N times, and CHECK
that the mechanism's distance/state changes, `worldRuntime.gameMinutes()` is unchanged and timers didn't fire.
Manual check: `./tools/run_game.sh --isolated tbdoor --world mm6 --map <dungeon>`, enter TB and click a door.

---

## 2. Arena opponents fight each other (trivial)

**Cause.** `startArenaChallenge` (game/gameplay/ArenaRuntime.cpp:226-246) leaves `actor.group = 0`. The same-group
truce in `GameplayActorService::resolveActorTargetPolicy` (GameplayActorService.cpp:910) needs `group != 0`, so
mixed-faction opponents fall through to `getRelationBetweenMonsters` (:914). Original MM8 at `0x4bc74f`:
`mov dword [esi+0x34c], 1`. MMExt names MM8 MapMonster `0x34c` `Group`
(`reference/MMExtension/Scripts/Structs/01 common structs.lua:1450-1452`). OE also uses `group = 1`
(`Actor.cpp:3236`).

**Group value.** Use a named constant equal to the original, `constexpr uint32_t ArenaOpponentGroup = 1;`, in the
anonymous namespace of ArenaRuntime.cpp.
- **No collisions found.** The Arena maps start empty, and their event scripts (`mm6 zarena.lua`, `mm7 7d05.lua`,
  `mm8 d42.lua`) use no group calls.
- **Special groups elsewhere.** Party summons use `group = ally = 999` (IndoorWorldRuntime.cpp:14252-14253), and
  `hostileToSummon` bypasses the truce (:906-910), so opponents still attack party summons. Groups 38/55 only
  matter for stealing (IndoorWorldRuntime.cpp:12874).
- **relations.yml and shields.** `MonsterRelationAddOns` works on monster ids, and the truce check comes first, so
  there is no interaction. `MonsterShields` has no group logic.

**Change** (ArenaRuntime.cpp, after `actor.hostilityType = 4;` at :236):
```cpp
        // The original puts every opponent in one group, so they never fight each other (MM8 0x4bc74f).
        actor.group = ArenaOpponentGroup;
```
Also update the `re_mm8/ARENA.md` table row for `0x4bc60d`: "hostility 4, group 1, clears loot".

**Edge cases.**
- MAW boss offspring and summoner minions spawn with `request.group = 0` (MawMonsterRules.cpp:1700-1731,
  MawCombatRules.cpp:2285-2301). In the Arena they can still fight opponents of a hostile faction. Optional
  follow-up: when the spawning monster has a non-zero group, copy it to the spawn request.
- Saves with an Arena fight in progress keep `group = 0` until that fight ends. No migration is needed.
- Berserk: like OE, the same-group check wins over Berserk. Not changed.

**Verification.** Extend `tests/ArenaRuntimeTests.cpp`. In the loop at :248-254 add
`CHECK_EQ(actor.group, 1u);`. Then add a case that builds two opponents from factions that are hostile in
`hostile.txt` and calls `GameplayActorService::resolveActorTargetPolicy`: CHECK `canTarget == false`, and still
true against a `controlMode`-summon target. `tests/GameplayActorAiSystemTests.cpp:316-354` shows how to build those
facts. For runtime coverage, run the existing `tests/scenarios/arena/` scenarios.

---

## 3. Turn-based monster movement too short (trivial, plus an optional small change)

**Cause.** The wait slice is right: 64 ticks at 128/s, `InitialWaitTicks` (TurnBasedCombatRuntime.cpp:20,26,
1189-1192). What's missing is the speed boost during the wait stage. MM8 `0x46fcf1-0x46fd34`: pursue/flee
(states 6/7) ×2, then if TB is on (`[0xb21628]`) and the stage is wait (`[0x509bec]==1`) ×`[0x6f3904]`, then the
1000 cap. `[0x6f3904] = recmod1 × 1.6667` (init `0x465e89-0x465e98`, double `0x3ffaaaaaaaaaaaab` at `0x4ea710`,
`recmod1` from the INI, default "1.0"). OE: `debug_turn_based_monster_movespeed_mul = 1.666…` (mm7_data.h:124), used
in Outdoor.cpp:1645 and Indoor.cpp:872.

**Where to apply.** Inside `GameplayActorAiSystem::updateActors` (GameplayActorAiSystem.cpp:4503-4528), so indoor
and outdoor share it and the world runtimes stay unchanged. Both worlds move actors by
`movementIntent.moveSpeed`: Outdoor at OutdoorWorldRuntime.cpp:10508, Indoor at IndoorWorldRuntime.cpp:8789-8790,
where 0 falls back to `effectiveMoveSpeed`. Scale the speed of every move in the result, then cap again:
```cpp
// The original speeds monsters up by 5/3 during the turn-based wait stage, before its 1000 cap (MM8 0x46fd09).
constexpr float TurnBasedWaitMoveSpeedMultiplier = 5.0f / 3.0f;
...
    updateBackgroundActors(facts, result);
    updateActiveActors(facts, result);

    if (facts.turnBased.mode == ActorTurnBasedMode::MoveOnly)
    {
        for (ActorAiUpdate &update : result.actorUpdates)
        {
            if (update.movementIntent.applyMovement && update.movementIntent.moveSpeed > 0.0f)
            {
                update.movementIntent.moveSpeed = std::min(
                    update.movementIntent.moveSpeed * TurnBasedWaitMoveSpeedMultiplier, MaxActorMoveSpeed);
            }
        }
    }

    return result;
```
- **Cap order.** `movementSpeedForMotion` (:91-105) already caps at 1000 after the pursue factor; the second
  `std::min` reproduces the original "multiply, then cap".
- **Zero-speed fallback.** The fallback path (`moveSpeed == 0` falls back to `effectiveMoveSpeed`, Indoor :8790) is
  not scaled. Check whether any MoveOnly path leaves `moveSpeed` at 0 while moving. If one does, either set
  `moveSpeed` there or scale `effectiveMoveSpeed` in the world runtimes instead.
- Background actors are scaled too, as in the original (it applies to every walking actor in the wait stage).

**Pursue factor.** Keep the user's 1.75 (comment at :32, a user choice on 2026-10-22). That gives
160 × 1.75 × 5/3 × 0.5 s ≈ 233 units per wait for a goblin, against 267 in the original and 140 today. If the user
wants exact TB parity, a separate `TurnBasedPursueMoveSpeedMultiplier = 2.0f` for the wait stage is an option. Ask
first, because it reverses a recorded choice.

**Optional (small): fresh movement decision when the wait stage starts.** OE's `ActorAISetMovementDecision`
(TurnEngine.cpp:753-771) re-plans every queued actor at the start of the wait stage. Ours keeps whatever
stand/idle timer the AI chose while held (Hold mode still runs the AI with `movementAllowed = false`,
:4507-4522), so an actor can spend the whole wait standing. My guess is that this is the "small steps"
complaint; it isn't confirmed at runtime. Hook: `GameSession.cpp:1035` calls `setTurnBasedActorMode` every frame,
so detect the change:
```cpp
void OutdoorWorldRuntime::setTurnBasedActorMode(ActorTurnBasedMode mode)   // OutdoorWorldRuntime.cpp:7881
{
    const bool enteringWait =
        mode == ActorTurnBasedMode::MoveOnly && m_turnBasedActorFacts.mode != ActorTurnBasedMode::MoveOnly;
    m_turnBasedActorFacts.mode = mode;

    if (enteringWait)
    {
        for (MapActorState &actor : m_mapActors)
        {
            if (!actor.isDead && actor.aiState == ActorAiState::Standing)
            {
                actor.actionSeconds = 0.0f;
                actor.idleDecisionSeconds = 0.0f;
            }
        }
    }
    ...
}
```
Do the same in `IndoorWorldRuntime::setTurnBasedActorMode` (IndoorWorldRuntime.cpp:10892) on
`m_mapActorAiStates`. Skip actors that are dying, stunned, paralysed or in an attack presentation.
`stopTurnBasedActorMovement` (Outdoor :7921-7975) already zeroes `actionSeconds` at the end of the wait stage, so
only timers set during Hold need clearing.

**Verification.**
- `tests/GameplayActorAiSystemTests.cpp`: copy "uses the pursuit speed multiplier and cap" (:852-884) into
  "turn-based wait stage multiplies movement speed by 5/3 before the cap". Use speed 200 with MoveOnly and CHECK
  `moveSpeed ≈ 200 × 1.75 × 5/3 = 583.3`. Use speed 700 and CHECK it stays at 1000. With Hold, CHECK no movement
  (as at :807-810). Also update "moves but never attacks in turn-based move-only mode" (:789) if it asserts a speed.
- `tests/TurnBasedCombatRuntimeTests.cpp` for the optional re-decision, if it is done through a fake world.
- In game: MM6 New Sorpigal goblins, `./tools/run_game.sh --isolated tbspeed --world mm6 --map oute3.odm`.
  Compare the distance moved per turn before and after using the `turn_based_*` debug traces.

---

## 4. Arcomage AI misjudges Shift, Flood Water, the value 99 and conditional cards (small)

**Cause.** `ArcomageAi::calculateCardPower` (game/arcomage/ArcomageAi.cpp:118-185) scores only `card.primary`
and reads raw deltas.
- Shift (card 33) has all-zero fields. The swap is coded by name in `applyMm8SpecialCard`
  (ArcomageRules.cpp:39-67), so the card scores `5 × min(3, spare)` > 0 and is played whatever the wall heights.
  Flood Water (30) has the same problem.
- The value 99 means "set to the other side's value" (`applyScalarChange`, ArcomageRules.cpp:489-503). Copping the
  Tech (7: primaryPlayerQuarry = 99, condition LesserQuarry) and Parity (47: primaryPlayerMagic = 99,
  secondaryEnemyMagic = 99, condition LesserMagic) score 40 × 99, so they are always played, even when the
  condition picks the empty or harmful branch.
- OE scores 99 as `enemy − player` (Arcomage.cpp:558+).

**Change.**
- `ArcomageRules.h:46`: move `evaluateCondition` to `public:`. It is a pure static, and the AI must use the same
  rule as `playCard` (ArcomageRules.cpp:238).
- `ArcomageAi.cpp`, in `calculateCardPower`:
  ```cpp
  namespace
  {
  // A field of 99 sets the value to the other side's (ArcomageRules::applyScalarChange).
  int scalarChange(int ownValue, int otherValue, int delta)
  {
      return delta == 99 ? std::max(0, otherValue) - ownValue : delta;
  }
  }
  ...
      const ArcomageEffectBundle &bundle = ArcomageRules::evaluateCondition(card.condition, player, enemy)
          ? card.primary
          : card.secondary;

      int towerGain = scalarChange(player.tower, enemy.tower, bundle.playerTower) + bundle.bothTower
          - scalarChange(enemy.tower, player.tower, bundle.enemyTower);
      int wallGain = scalarChange(player.wall, enemy.wall, bundle.playerWall) + bundle.bothWall
          - scalarChange(enemy.wall, player.wall, bundle.enemyWall);
      int dungeonGain = ...;   // same pattern for quarry, magic, dungeon, bricks, gems, recruits

      if (card.name == "Shift")
      {
          wallGain += 2 * (enemy.wall - player.wall);   // own wall +(e−p), enemy wall −(e−p)
      }
      else if (card.name == "Flood Water")
      {
          // The lower wall loses 1 dungeon and 2 tower; equal walls hit both (ArcomageRules.cpp:41-59).
          const int ownHit = player.wall <= enemy.wall ? 1 : 0;
          const int enemyHit = player.wall >= enemy.wall ? 1 : 0;
          towerGain += 2 * (enemyHit - ownHit);
          dungeonGain += enemyHit - ownHit;
      }
  ```
  Keep the existing weights. Put the special cases in a small helper next to `applyMm8SpecialCard`, so the rule
  and its score don't drift apart. Better still, expose one function from ArcomageRules that both use.
- The kill check (:180) should read the selected bundle (it already uses `bundle.enemyTower`). It ignores
  `enemyBuildings` damage, which is optional to improve.
- Mastery 0 (random play, :55-87) is unchanged by design.

**Edge cases.**
- `playCard` evaluates the condition after `consumeCardCost` (ArcomageRules.cpp:237-238). No condition depends on
  bricks, gems or recruits, so evaluating it before paying is the same.
- A negative score lets `bestPlayableScore > 0` fail, so the AI discards the card instead. `canDiscardCard`
  respects the card's `discardable` flag (Shift is discardable).
- `scalarChange` clamps at 0, like `applyScalarChange`.

**Verification.** Extend `tests/ArcomageRegressionTests.cpp`, following "arcomage ai turn can be simulated
headlessly" (:157-183) and "mm8 special cards" (:185-234). Set `harness.state.aiMastery = 1` and `2` and give
player 1 a hand of {Shift, Amethyst} with enough resources:
- AI wall 20 against enemy 5: the AI does not play Shift.
- AI wall 5 against enemy 20: the AI plays Shift.
- Copping the Tech with the AI's quarry higher: not played. With it lower: played.
- Parity both ways.
- Flood Water: played only when the enemy wall is lower.

---

## 5. Optional follow-up: remaining outdoor slope differences (not part of this fix)

Already in HEAD (`ddcf6696d`, after v1.11): `IndoorSlopeRule::Party` and the terrain ClimbBetter pull
(`TerrainSlopeSlideGravityMultiplier = 1.0f`, OutdoorMovementController.cpp:35, :2068). Still different from MM8
(`re_mm8/PARTY_SLOPE_CLIMBING.md`, gap 3 and item 5):
- Extra slide on steep outdoor model faces: `partyOnSteepBModel` (OutdoorMovementController.cpp:1992-1995) and its
  branch at :2072- (4 × gravity downhill, uphill input removed). The original only refuses the upward push
  (`0x4751c4-0x47553d`) and never slides.
- Small-face height: `MaxSmallSlopeHeight = 128` (:24, used at :1453 and :2656) against the original's 32
  (`cmp eax, 0x20` at `0x47520b`). Ours lets party and actors walk up faces 33-127 high that MM8 refuses. Making it
  party-only matches the indoor `IndoorSlopeRule` split.
- Gravity: MM8 strength is 10 (or 2 with the flag), against `GravityPerSecond = 1280` (:37) = OE's 5. Not
  investigated; it would change jump and fall arcs and every gravity-scaled slide.
Verification for any of these: extend `tests/scenarios/mm8_party_slopes.yml` with an outdoor model-face probe.
