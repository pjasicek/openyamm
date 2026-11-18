# Turn-based combat audit

Started 2026-11-06 from player reports on the 1.21 release. This is the reference for turn-based (TB) fairness work:
how the original turn engine works, what OpenYAMM matches, and each defect that gave the party an advantage or a
disadvantage. Every reproducible defect has a headless scenario under `tests/scenarios/turn_based/` that asserts the
original's behaviour; it failed before its fix and now guards it from `tests/scenarios/release/scenarios.txt`. TB-1 to
TB-8 and TB-10 were fixed on 2026-11-06, TB-11 on 2026-11-16, TB-17 on 2026-11-17; TB-9 turned out not to be a defect. A new finding gets a scenario that fails
first.

```bash
./build/game/openyamm --headless-run-scenario tests/scenarios/turn_based/<name>.yml
```

Sources: `reference/OpenEnroth-git/src/Engine/TurnEngine/TurnEngine.cpp` (MM7, named functions) and the original
`re_mm8/mm8_orig/MM8-Rel.exe` read with Rizin (addresses below belong to that executable,
see [RIZIN_GUIDE](../re_mm8/RIZIN_GUIDE.md)). OpenYAMM's engine is `game/gameplay/TurnBasedCombatRuntime.cpp`.

## Player reports

| Report | Explained by |
| --- | --- |
| "I hit an action and it performs it on the next character as well" | TB-1 |
| "I can attack 3 times in a row before the enemy can react" | design (below), plus TB-1, TB-3, TB-4 |
| "turn base wasn't queued correctly, party turn > enemy turn > party turn" | mostly design (below) |
| "my mana didn't regenerate" | TB-2 |
| "problems casting spells" | TB-1 (swallowed and repeated Quick Cast presses) |
| "did you change the casting animation" of Drain Life | yes: every projectile and impact is new art (Lifedrain, spell 111, `engine/effects/projectiles.yml`); damage and healing follow MM8 ([LIFEDRAIN](../re_mm8/LIFEDRAIN.md)); no TB defect found |
| "I increased the turn speed, but I am always hitting" (2026-11-15, a bow against a Goblin King across a field) | design (below: a melee monster out of reach stands on its turn, and the Goblin King casts Fire Bolt on 30 % of them), plus TB-11 at high speeds |
| "you changed the speed of the game" | not found. Candidates: F2 toggles a 2x mode and is not on the key binding pages (`KeyboardBindings.cpp:76`, `GameApplication::updateDoubleSpeedInput`); the new TB speed settings (default 1x); 1.21's new run clips. Monsters chasing at twice their speed is original. |

## How the original turn engine works

- **Stages.** Wait (monsters move for 64 ticks), Attack (the queue runs), Movement (the party walks on 130 points,
  one per tick held), then Wait again. Ticks are 128 per second.
- **Queue.** Every combatant has an initiative; lowest acts first, a member before a monster on a tie, then lower id.
  An Attack stage lasts 100 initiative (`turn_initiative`): the queue steps down until someone reaches 0 or the 100
  run out, and leftover initiative carries into the next turn.
- **Costs.** A member's action sets its initiative to the action's recovery in original ticks (attack recovery,
  minimum 30; a spell's recovery; a potion 100). A monster's action costs its monster-table recovery, doubled while
  slowed.
- **Turn end.** When the queue is exhausted, the turn runs 213 ticks of timed effects
  (`NextTurn` -> `_494035_timed_effects`): the clock, buffs, conditions, **HP/SP regeneration** and recovery.
- **Start** (`Start`, MM8 `0x406412`-`0x40667b`). Recovering members queue at remaining recovery x 0.46875. Ready
  members get 2, 3, ... **sorted by attack recovery** (`0x4065d7` calls `0x48f237(false)`). Each nearby monster rolls
  `rand() % 99`: under 33 gives 1, under 66 gives 3, else 5. MM8 adds **no** +16 (OpenEnroth's MM7 code does), so a
  monster that rolls 1 acts before the party. The start skips actor id 10 (`0x406451 cmp esi, 0xa`); OpenYAMM does not
  (TB-5).
- **Arrivals** (`StartTurn`, MM8 `0x406ad7`). At each Attack stage, members able to act again join at 100 and new
  nearby monsters at 1. There is no actor-10 skip here.
- **Who may act.** `SortTurnQueue` gives every queued member recovery for its initiative, so only the front member is
  "active". Potions, scrolls and casts check that recovery (`Character::useItem`: "Player is not active").
- **Time.** The game clock is turn-based while TB is on (OE `pEventTimer->isTurnBased()`): frames run no timed
  effects, so buffs, regeneration and monster spell effects advance only by each turn's 213 ticks. MAW's timers follow
  `Game.Time` (`zzMaw-Timers.lua`), so they also advance per turn.

Within one 100-tick turn a member with recovery of 50 or less acts twice and one with 33 or less three times. A party
of four with ~90-tick swords each act before a 100+-recovery monster acts again. That is the original design, and it
is what most of the "3 attacks" and "party turn, enemy turn" reports describe.

## Verified as matching

- The turn's 100 initiative, the movement budget, the 64-tick wait and the 213 ticks of game time per turn.
- Player recovery mapping: realtime seconds / 2.1333 x 128 recovers the original ticks
  (`recoverySecondsToTicks`); the 30-tick minimum; spell recovery via `storeMemberTurnRecovery`.
- Monster recovery from the table, doubled while slowed (`turnBasedActorRecoveryTicks`).
- Start: 0.46875 scale, no +16, ready members 2, 3, ...; end: leftover initiative becomes realtime recovery.
- The per-turn clock **does** run the party's timed states: `GameplayController::advanceTurnBasedGameMinutes`
  calls `Party::advanceTimedStates`, so buffs, Meditation and conditions tick per turn (control in
  `item_regeneration.yml`). An earlier note that buffs never expire in TB was wrong.
- Stealing in TB costs the stealing recovery it costs in real time (TB-9).
- A real-time hit reaction resolves during the party's stage (`updateTurnBasedPausedActorAnimations`), so being hit
  does not cost a monster its turn.

## Findings

| ID | Severity | Status | Effect | Scenario |
| --- | --- | --- | --- | --- |
| TB-1 | high | fixed | a held Attack or Quick Cast acted for the next member too | `single_press_one_member.yml` |
| TB-2 | high | fixed | item and MAW HP/SP regeneration stopped in TB | `item_regeneration.yml` |
| TB-3 | high | fixed | drinking a potion cost no turn, repeatable | `potion_spends_turn.yml` |
| TB-4 | high | fixed | a member whose turn it was not read a scroll for free | `scroll_off_turn.yml` |
| TB-5 | medium | fixed | the map's actor 10 never acted in TB | `actor_ten_joins.yml` |
| TB-6 | medium | fixed | monster stun/paralyse/slow ran on actor AI time, not per turn | `monster_effects_per_turn.yml` |
| TB-7 | low | fixed | entry order was party order, not fastest first | `start_order_by_recovery.yml` |
| TB-8 | low | fixed | a monster's entry initiative was a fixed hash of its index, not random | none (random) |
| TB-9 | low | not a defect | stealing was thought to cost only the 30-tick minimum | none |
| TB-10 | low | fixed | walking in TB ran buffs and regeneration on frame time | covered by `item_regeneration.yml` |
| TB-11 | medium | fixed | at a high game speed monsters walked less each turn | `fast_speed_monsters_walk.yml` |
| TB-12 | high | fixed | Immolation burned every 10 s of wall-clock time, also on the party's turn | `immolation_per_turn.yml` |
| TB-13 | high | fixed | water, lava and burning floors never hurt a party standing in TB, and hurt by walking time | `drowning_per_turn.yml` |
| TB-14 | medium | fixed | indoors, floor triggers (pressure plates) and MM9 exits did not fire during TB | none (code path) |
| TB-15 | medium | fixed | outdoors, walking or falling in TB advanced the clock, timers and the monsters' shields | none (code path) |
| TB-16 | medium | fixed | MAW's timers (poison, monster regeneration and auras, solo talents) ran on actor AI time | `maw_poison_per_turn.yml` |
| TB-17 | medium | fixed | travelling to another map ended turn-based mode (user decision 2026-11-17: it carries over) | `kept_across_map_change.yml` |

### TB-1: one press acts for two members

- **Cause.** Attack and Quick Cast fire while their key is *held* and repeat every 0.14 s
  (`GameplayActionController.h:162` `HeldActionRepeatDebounceSeconds`; `updateAttackAction` `repeatReady` at
  `GameplayActionController.cpp:1164`, `updateQuickCastAction` at `:1107`; held state from
  `GameplayInteractionController.cpp:1519`). A melee swing leaves nothing pending, so `applyPlayerAction` selects the
  next member in the same frame (`TurnBasedCombatRuntime.cpp` `applyPlayerAction` -> `advanceAttackQueue`). An
  ordinary 0.2 s tap swings for two members. In real time recovery hides this; in TB nothing does.
- **Also.** A Quick Cast press while no member may act (a missile still flying, a monster's action) is swallowed
  (`GameplayInputController.cpp:996-1000`), and if the key is still down when the queue returns it fires after the
  repeat delay. Casting feels unreliable.
- **Original.** Acts on key-down messages; Windows repeats a held key after about 0.5 s.
- **Scenario.** One-frame press: member 1 is next (passes). 0.2 s press: member 2 (member 3 before the fix).
- **Fix.** In TB, Attack and Quick Cast act on the press only (`AttackActionConfig::turnBased`,
  `QuickCastActionConfig::turnBased`): no held repeat and no firing when a member becomes ready while the key is
  down. A press while nobody may act does nothing, as in the original.
- **Follow-up (2026-11-13, Discord).** Acting on the press only took away holding the key to attack continuously,
  which the original allows through key repeat. A held key now repeats in TB after the 0.5 s first-repeat pause,
  then every 0.14 s; Fast attack repeat does not shorten the pause there, so a tap still acts for one member.
  `single_press_one_member.yml` checks that a 0.6 s hold swings for two members.

### TB-2: item regeneration stops

- **Cause.** Per-second regeneration (`Party::updateRecovery`: `healthRegenPerSecond`, `spellRegenPerSecond` from
  of Regeneration, of Mana, Plenty, The Troll, The Unicorn, The Eclipse, ...) runs on the world frame time
  (`OutdoorPartyRuntime.cpp:50`, `IndoorPartyRuntime.cpp:360`). In TB that time is
  `movementDeltaSecondsForFrame` (`GameSession.cpp:1051`): zero except while the party walks. The per-turn clock
  advance calls `advanceTimedStates` only. Ruleset regeneration (`rules().skills.updateRegeneration`,
  `GameSession.cpp:1120`, MAW) runs only while actor AI runs, i.e. during the monsters' stages.
- **Original.** `NextTurn` -> `_494035_timed_effects(213)` -> `RegeneratePartyHealthMana` once per turn.
- **Scenario.** Real time: an of Mana ring gives 5 SP in 5 s (passes). Bless loses 600 game seconds over 12 turns
  (passes). SP over 12 turns: at least 10 (a turn is 50 game seconds, worth ~1.7 SP; 0 before the fix).
- **Fix.** `Party::updateRegeneration` (split out of `updateRecovery`: HP/SP per second and personal shields) runs in
  `GameplayController::advanceTurnBasedGameMinutes` for the turn's 1.664 real-second equivalents, followed by the
  ruleset's `updateRegeneration`. `GameSession` no longer runs the ruleset's regeneration on actor AI frames in TB.

### TB-3: potions cost no turn

- **Cause.** `InventoryItemUseRuntime.cpp:1314` only sets real-time recovery on the payer; the turn engine is not
  told. `selectFrontCharacter` and `applyPlayerAction` clear the front member's real-time recovery
  (`TurnBasedCombatRuntime.cpp:745`, `:1041`) every update, so the drinker keeps the turn and may drink again. The
  1.21 notes ("potions cost the active member 100 recovery ticks") hold in real time only. The paused basebar potion
  popup makes this easy.
- **Original.** OpenEnroth `Character::useItem`: in TB, 100 ticks into `pTurnBasedCharacterRecoveryTimes` and
  `ApplyPlayerAction`.
- **Scenario.** The front member drinks Cure Wounds (health 10 -> 40): member 1 next (member 0 before the fix).
- **Fix.** In TB the queue's ready member pays the drink (`InventoryItemUseContext::turnBasedReadyMember`; none while
  monsters act, and the drink is refused). `GameplayItemService` spends that member's turn with the drink's recovery
  (100 ticks in Standard).
- **Follow-up (2026-11-14, Discord OY-204).** Players still drank two potions and attacked in one round under MAW.
  MAW charges its 60 ticks only near monsters that have seen the party (the yellow alert, `zzAlchemy.lua`), and
  the turn queue takes every hostile monster within reach whether it has seen the party or not, so the drink was free
  and the member kept the turn. In TB a drink now always spends the ready member's turn (60 ticks under MAW, so two
  drinks fit one 100-initiative turn; MAW's own value). Every way of drinking (inventory, portrait, basebar potion
  list, quick potion keys, solo action bar) goes through `GameplayItemService::tryUseHeldItemOnPartyMember`.
  `maw_potion_spends_turn.yml` drinks from the inventory and with the quick potion key.

### TB-4: a scroll read off turn is free

- **Cause.** `GameplayScreenRuntime::tryCastSpellRequest` (`:3379`) only checks that some member may act; a scroll's
  caster is the member it is used on (`GameplayItemService.cpp:654`). After the cast, `applyPlayerAction` refuses a
  member who is not the front one (`turn_based_player_action_wrong_front`) and no turn is spent. In TB every member's
  real-time recovery is zero, so nothing else stops it. Any action path that resolves a member other than the front
  member has the same hole (for example `executePartyAttack` switching to the next ready member).
- **Original.** The reader must have no recovery; in TB only the front member qualifies ("Player is not active").
- **Scenario.** Member 2 reads Haste while member 0 is to act: refused (cast before the fix).
- **Fix.** `TurnBasedCombatRuntime::readyMemberIndex` names the member whose turn it is. `tryCastSpellRequest`
  refuses any other caster ("That character is not active"), and `beginPlayerActionOrFinishMovement` makes the ready
  member the active one, so an attack or a steal is always that member's whoever the player selected.

### TB-5: actor 10 never acts

- **Cause.** `actorCanJoinTurnQueue` skips index 10 (`TurnBasedCombatRuntime.cpp:65`), and both the start
  (`:850`) and the per-turn arrival scan (`addArrivedCombatants`, `:918`) use it. A monster with map index 10 is never
  queued, never granted an action and held still by the TB actor modes.
- **Original.** MM8 skips id 10 only at the start; the arrival scan adds it at the next turn with initiative 1.
- **Scenario.** Dagger Wound's Lizardman Peasants 10 and 11 made hostile beside the party; actor 10 is queued from the
  start and after two turns, like the control actor 11 (never before the fix).
- **Fix.** No skip anywhere. MM8's start-only skip looks like an indexing slip and would only delay one monster by a
  turn, so OpenYAMM does not copy it.

### TB-6: monster status timers per turn

- **Cause.** Monster stun, paralyse, slow and the other spell effects counted down on actor AI time
  (`GameplayActorService::updateSpellEffectTimers` from the actor AI step), which in TB runs only in the Wait stage
  (64 ticks, 0.5 s) and while monsters resolve actions, so a debuff lasted a varying number of turns.
- **Original.** Actor buffs expire on game time (`IsBuffExpiredToTime(pParty->GetPlayingTime())`), which advances
  213 ticks (1.664 real-second equivalents) per turn.
- **Fix.** In TB the actor AI step leaves the timers alone (`ActorTurnBasedMode` other than `RealTime`), and
  `IGameplayWorldRuntime::advanceTurnBasedWorldTime` runs every actor's effects down by the turn's time from
  `advanceTurnBasedGameMinutes` (outdoor and indoor).
- **Scenario.** A paralysis of 1800 s is untouched by the wait and the monsters' actions and is 1783.36 s after ten
  turns (`assert: {turn_based: {actor_effect: paralyze, ...}}`).

### TB-7: entry order ignores attack recovery

- **Cause.** `rebuildInitialQueue` sorts ready members by `recoverySecondsRemaining` (`TurnBasedCombatRuntime.cpp:823`),
  zero for all of them, so party order decides.
- **Original.** Sorted by attack recovery (above).
- **Fix.** `GameplayScreenRuntime::toggleTurnBasedMode` passes each combatant's melee attack recovery to `begin`; ready
  members enter fastest first, party order breaking ties.
- **Scenario.** Two-Handed Axe (100) as member 0, Crude Dagger (60) as member 1: member 1 acts first.

### TB-8, TB-9 and TB-10

- TB-8 (fixed): the entry roll was `(actorIndex * 1103515245 + 12345) >> 16 % 3`: the same monster always got the
  same slot and re-entering TB never re-rolled. It is now `rand() % 99` as in MM8 (1, 3 or 5), from a generator
  `GameSession` seeds at random (`TurnBasedCombatRuntime::seedRandom`; unit tests keep the fixed default seed).
- TB-9 (not a defect): `applyStealingAttemptResult` sets the thief's stealing recovery before the turn engine reads
  it, so a steal costs the same in TB as in real time. The earlier note misread the order.
- TB-10 (fixed): while the party walked in TB, `OutdoorPartyRuntime`/`IndoorPartyRuntime` ran recovery, regeneration
  and `advanceTimedStates` on the walking time, so a walk wore buffs down and regenerated on top of the turn's time.
  Turn-based walking now runs neither; the turn's game time does.

### TB-11: monsters walk less at a high game speed

- **Cause.** Fast mode (F2: the fast mode speed setting, 1.5x to 4x) and the turn-based speed settings (1x to 4x)
  multiply each frame's time (`GameApplication::gameplaySpeed`). The turn engine counts the whole multiplied time
  against the monsters' 64-tick
  wait stage, but the world let actors catch up at most 0.1 s per frame (`MaxAccumulatedActorUpdateSeconds`) and
  missiles four 1/60 s steps. Once the multiplied frame passed 0.1 s (above 6x at 60 frames a second, above 3x at
  30), the wait ended before the monsters had walked its 64 ticks. At 16x and 30 frames a second a monster walked
  18 % of its distance per turn, so a ranged party got many more free shots at a melee monster closing in.
- **Original.** Monsters walk 64 ticks per wait stage whatever the speed (MM8Patch's TurnBasedSpeed only shortens
  the real time it takes).
- **Fix.** `IGameplayWorldRuntime::setGameSpeed` (from `GameSession::setGameSpeed` every frame) multiplies the
  world's catch-up limits (actor AI, missiles, indoor world items) by the game speed, so they stay 0.1 s of real time
  and the actors get the whole time the turn engine counts.
- **Scenario.** Lizardman Peasant 11 walks about 355 units a turn at normal speed; over four turns at 16x it walks at
  least 950 (190 before the fix). `turn_based_turns` takes `game_speed` for this.
- **Not changed.** The party's own walking in real-time fast mode keeps its 0.05 s and 0.1 s per-frame limits, so F2
  4x walks at about 3x at 60 frames a second; that does not touch turn-based fairness (the party's turn-based walk is
  never sped up).

### TB-12: Immolation burns on wall-clock time

- **Report.** Discord, 2026-11-17 (translated from Chinese, where the zh-cn name of Immolation, 怒火焚身, was read
  back as "Incinerate"): in TB parties hold doorways with it and keep melee monsters from reaching them; some call it
  the only way to win on the hardest difficulty.
- **Cause.** Both world runtimes ran `updateImmolation` from `updateWorld` on each frame's time, also in TB, burning
  every monster within 307 every five game minutes (10 s). In TB that time passes while a member chooses an action, so
  a party that waited on its turn burned the monsters in reach without spending a turn, and the turn-based speed
  settings made it faster.
- **Original.** The aura burns from the timed effects (OE `Engine.cpp` Immolation block, every five game minutes),
  which TB runs only at a turn's end with 213 ticks (0.832 game minutes), so it burns once every six or seven turns.
- **Fix.** In TB `updateWorld` skips the aura and `advanceTurnBasedWorldTime` advances it by the completed turn's
  time (outdoor and indoor).
- **Scenario.** A paralysed Mercenary Captain 200 units from the party with Immolation (Fire 10) stays unhurt while
  the party idles 30 s on its turn (three burns before the fix), and is burned once over eight turns.
- **Not changed.** A burn still reads in the status line as the caster shooting the monster
  (`recordPartyProjectileActorImpact`).

### Wall clock against the turn's time (TB-13 to TB-16)

After TB-12 the user asked for every other place where frame time stood in for the turn's game time. The rule is
the original's: in TB the game clock (`pEventTimer->time()`) stands still, `_494035_timed_effects` runs once per
completed turn with 213 ticks, and only physics, doors and animation use frame time.

- **TB-13: water, lava and burning floors.** The original's timed effects drown (a tenth of each member's maximum HP)
  or burn the party at most once per call, so once per turn. OpenYAMM ran its one-second damage timers in the
  party's movement update: a turn-based physics step (`turnBasedPhysicsStep`) skipped them and reset the timer, so a
  party standing in deep water or lava in TB was never hurt, and a turn-based walk (`turnBasedMovementStep`) hurt it
  by the walking time. MM9's held breath (indoor water volumes) likewise ran only while walking. Now neither walking
  nor falling in TB advances them, and `advanceTurnBasedWorldTime` gives one water or burning tick per turn
  (`OutdoorPartyRuntime` / `IndoorPartyRuntime::advanceTurnBasedHazards`) and runs the breath down by the turn's
  time. Scenario: in the sea off Dagger Wound, 30 s on the party's turn cost nothing and three turns cost three
  ticks (before the fix the turns healed Ariel to full).
- **TB-14: indoor floor triggers.** To freeze the clock in TB, `IndoorRenderer` ran only `advanceMechanisms`, which
  also skipped `updatePartyFaceTriggers` and MM9's positioned exits (the original runs floor events on every step,
  also in TB). The stepped faces waited until TB ended. `IndoorSceneRuntime::advanceSimulation(ms, false)` now runs
  everything but the clock, its timers and the teacher schedules. The scenario driver called `advanceSimulation` in TB
  and so advanced the indoor clock where the game did not; it now does as the renderer (`advanceIndoorScene`).
- **TB-15: outdoor clock while walking.** `OutdoorSceneRuntime::advanceFrame` passed the turn-based walk's and fall's
  time to `updateTimers` (the clock, timed events, the sky) and queued it as actor AI time, which the next wait stage
  spent as one step: the monsters' energy shields regenerated and modifier cooldowns ran for the whole walk. A
  turn-based step now passes no time to either.
- **TB-16: ruleset timers.** `GameSession` ran `updateAuras`, `updateCombat`, `classes.update` and `updateMonsters`
  on actor AI time, so MAW's poison, monster regeneration and auras and solo talent cooldowns advanced about 0.5 s
  per turn plus the monsters' actions. MAW's timers follow `Game.Time`; in TB they now get no frame time and run once
  per turn from `GameplayController::advanceTurnBasedGameMinutes`.
- **Checked and matching.** Recovery, buffs, conditions and regeneration (TB-2, TB-10); monster spell effects (TB-6);
  Immolation (TB-12); the indoor clock; Armageddon and missiles, which use frame time in the original too.
- **Not changed.** OpenYAMM's own energy shields, monster modifiers and actor behaviours run on actor AI time, which in
  TB passes in the wait stage and the monsters' actions; the shields' design says so (they pause while the party
  acts). Fly and Water Walk drain no mana in OpenYAMM in real time either (the original drains the caster's SP while
  flying); that is not a turn-based question.

### TB-17: a map change ends turn-based mode

Every map load first unbinds the old world (`GameApplication::shutdownRenderer`, `GameSession::bindActiveWorldRuntime`
with no world), and that ended TB, so the party arrived on the next map in real time. By the user's decision
(2026-11-17) TB carries over: `TurnBasedCombatRuntime::leaveMap` keeps the mode, its stage and the members' places
in the queue, and drops the old map's monsters and the actions in flight there; the new map's monsters join as
arrivals at the next attack stage. A new game and a loaded save still reset TB, and a party defeat ends it
(`applyPartyDefeatConsequences`), since the woken party is not in a fight.

## Scenario support

The runner gained, for this audit (documented in `tests/scenarios/README.md`):

- `turn_based_turns: {count, max_seconds, game_speed}` plays turns through the input path, pressing Pass whenever the
  party may; `game_speed` multiplies each frame's time as fast mode and the turn-based speed settings do.
- `assert: {turn_based: {active, stage, front_member, actor_index, actor_queued, actor_effect, effect_min, effect_max,
  report}}`.
- `assert: {member_points: {member_index, spell_points_min/max, health_min/max}}`.
- `assert: {buff: {..., remaining_min, remaining_max}}` in game seconds.
- `setup_shortcut: {kind: set_member_points, member_index, health, spell_points}`.
- The scenario driver now applies the per-turn game time after each gameplay update, as `GameApplication` does.
