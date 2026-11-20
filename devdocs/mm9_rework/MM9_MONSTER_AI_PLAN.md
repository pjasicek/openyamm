# MM9 monster AI: implementation plan

The user approved the approach of [MM9_MONSTER_AI.md](MM9_MONSTER_AI.md) on 2026-11-04 with every recommendation:
native archetypes in the shared AI, data flags for hooks and placement patterns, Lua only for bosses; MM9's quirks
reproduced as MM9 plays them (and recorded); MM9's monster factions (allies unless a script sets hate); MM9 only (no
MM6-MM8 opt-in yet); a sleep tier later. Animation-blending problems the new behaviour exposes are fixed later, not in
this work. The user also asked for **test arenas**: a map with every placed monster removed, only the test's monsters
spawned, playable in the game window and replayable headless, with the monsters' decisions logged and checked.

Research: [monster_ai/](monster_ai/) (MM9 data and scripts, MM9 native RE, OpenYAMM today).

## Rules for every phase

- MM6-MM8 behaviour must not change: an actor without an MM9 profile takes exactly today's code path. Run the
  existing actor/AI unit tests and the MM8 actor scenarios after each phase.
- The AI stays a pure function of facts (seeded rolls, no hidden state); new per-actor state travels in
  `ActorRuntimeFacts` / `ActorStateUpdate` like the skirmish state.
- Data is generated, never hand-edited: `MONSTERS.txt` rows through `tools/mm9_import_discovery/`, placements through
  the MM9 map converters.
- Every behaviour lands with an arena scenario that shows it (headless, asserting on the decision trace) and a unit
  test for its pure logic where one fits.
- Cost: no per-frame Lua; profile branches only where the profile is present.

## Decisions after the plan

- **Turn-based combat stays MM6-MM8's** (user, 2026-11-04), on MM9 maps too. MM9's own turn-based scheduler (decoded
  in [MM9_AI_NATIVE_RE.md](monster_ai/MM9_AI_NATIVE_RE.md) §7.2.1, including its lost second turn after every attack)
  is not reproduced. MM9 monsters take their turns in the shared turn-based mode, ordered by their (correctly
  converted) recovery. Later item: on an MM9 monster's turn, choose its action the MM9 way (Att% blow or spell, ranged
  Type 1/2, fliers never flee) inside the MM6-MM8 turn.
- **Recovery is MM9 game seconds** (§7.2.1): `Recovery` × 33 ms of real time (30 → 0.99 s), counted from the end of
  the attack clip; a blow that hits, a released shot or a cast sets recovery at that moment, and an attack a wince cuts
  before its hit sets none. Spells use their `SPELL.txt` recovery. To be fixed in the importer and the MM9 loop.
- **Animation follow-ups** (user, 2026-11-04; [MM9_ANIMATION_AUDIT.md](MM9_ANIMATION_AUDIT.md) "Follow-ups done"): no
  MM6-MM8/MM9 split where a behaviour is generic, one code path driven by data. Every 3D monster gets the audit's
  presentation rules (attack legs held, stand grace, gait by command, backpedal only on the AI's request), a 0.1 s
  blend into death and a gait smoothed between AI steps; an attack applies at its 3D clip's impact key where no sprite
  contact frame is authored (in any world), and a manifest whose clips are its monsters' native timing (`attack_timing:
  clip`, the MM9 manifest) times the action by the clip. These deliberately change MM6-MM8 presentation; MM6 attack
  timing is unchanged (every MM6 attack has a contact frame).
- **Repositioning casters** (user, 2026-11-05; an OpenYAMM addition, not MM9): the three Evil Sorcerer rows (156-158,
  ranged holders) get an optional, data-driven `reposition` behaviour usable by any monster. A holder that has lost
  sight of its target for about 2 s walks to a nearby spot, within a leash of its post, from which it sees the target,
  then holds and casts again. A holder the target rushes backs off a few steps before casting. Hand-placed Type 2
  holders (`ranged_type: 2` placements) stay as MM9 plays them.
- **Ambient animation** (user, 2026-11-05): items 1-4 of
  [MM9_AMBIENT_ANIMATION.md](monster_ai/MM9_AMBIENT_ANIMATION.md) section 4 (the fidget timer, stand variants, the talk
  turn, the head look); townsfolk chats and marker clips (5-6) after. The talk turn deliberately changes MM6-MM8:
  their indoor NPCs now face the party when it talks to them, as outdoor ones already did. Stand variants were dropped
  after a survey (no MM9 monster or townsperson model has more than one). See "Ambient animation" below.
- **Thinking cap** (user, 2026-11-06): the cap of 48 MM9 actors thinking at once, nearest first ("Perception fixes"),
  is enough; it stays.
- **Townsfolk chats** (user, 2026-11-06): item 5 of the ambient animation, for immersion. See "Townsfolk chats" below.
- **The 2026-11-06 batch** (user: "do all as you recommend"): timed conditions from MM9 spells, with durations running
  on the game clock (also in turn-based mode, where MM9's own clock nearly stops: not reproduced) and MM9's short Curse
  kept; MM9 projectile blasts and homing from `PROJECTILE.txt`; marker facing, wait and clips on paths; a backpedal
  without its clip plays the gait forwards, as MM9's. See "Timed conditions", "Marker stops" and "Backpedal" below.
- **Awareness of the party** (user, 2026-11-07; a deliberate departure from MM9): MM9 loop monsters see the party all
  round and half again as far as their placement says, a party hit from within 4 096 provokes the monster and its awake
  friends within 256, a hit from farther gives it no target, and dormant starts keep MM9's rules. See "Awareness of the
  party" below.
- **Spells:** the first version maps MM9's monster, script and trap spells onto MM6-MM8 spells
  ([MM9_SPELL_MAPPING.md](MM9_SPELL_MAPPING.md), under review).

## Shared contracts

### 1. The MM9 AI profile (data, phase 1)

Per monster row, generated from `MONSTERS.txt` and the default script's include chain, carried into
`ActorTacticsFacts` the way the `skirmisher` modifier is (`MonsterModifiers` → `ActorBehaviorCatalog` →
`ActorBehaviorRuntime::applyTactics`). Fields (names indicative):

| Field | Source |
| --- | --- |
| `archetype`: crawler, skirmisher, ranged_holder, flier, swimmer, turret, civilian, guard | class (`AISwimFly`, `Lobber`, `NPC`) and default script (`basecrawl`, `basemelee`, `EvilSorcerer`, `basefly`, `BaseSwim`, `lobber`, `NPCbase`, `policeman`) |
| `ranged`: none, walker (Range Type 1), flier (FlyRange) | script includes (`Range.inc`, `FlyRange.inc`) |
| `attack_reach` (decide-to-attack distance), `melee_sweep` (hit length) | `AttackReach`, `AttackRange` × scale (the names are swapped in MM9) |
| `alert_radius`, `lunge_velocity`, run/walk/fly speeds | table |
| `strafe_attack_chance`, `evade_chance`, `taunt` | table / script (the existing skirmisher fields) |
| wince: never (`Always Wince? = 1`), else 20-50 % at ≤ 20 % HP | table (MM9's inverted column, recorded as a quirk) |
| `resurrecter` | `Resurrect` |
| family hooks: `throttle: false`, `always_evade`, `pod_launch`, `melee_window`, `spawn_in`, `death_spawn`, `dormant_start` | the per-family scripts (MM9_AI_DATA_AND_SCRIPTS.md §4.1) |

Per placement (scene actor fields written by the MM9 converters from the DAT object and its `ScriptName` /
`ScriptParams`): `sight` (default 1 320), `hearing` (360), `runaway_chance`, `ranged_type` (1 or 2),
`can_be_resurrected`, wander mode, `patrol` markers and leash, `dormant: {until, pose}`, `hostility`
(friendly until provoked / hostile after an event), `summon`. A placement value overrides the row's.

**Implemented (phase 1):** the fields as generated, their sources and units, the archetype rules, counts and the MM9
quirks they reproduce are in [monster_ai/PROFILE.md](monster_ai/PROFILE.md). Row: modifier `mm9_ai` →
`ActorTacticsFacts::mm9Profile`; placement: scene actor `mm9_ai` → `MapDeltaActor::mm9Ai` →
`ActorMovementFacts::mm9Placement`. Distances are ours (MM9 × 2.56).

### 2. The decision trace (harness, phase 0)

The AI reports what it decided: an optional `ActorAiDecision` (an enum plus a small detail: target, ability, chance
rolled) in `ActorStateUpdate`, set only where a decision is taken. The world, when tracing is on, also records state
changes it already sees (motion state, target, skirmish phase, attack ability, damage, death). A trace line:

```
[ai] t=12.300 actor=3 monster=9104 "Skeletoid" decision=strafe_attack target=party detail="chance 0.20"
```

Tracing is off by default and costs nothing then. On: a ring per actor for the GUI overlay plus a log file.

### 3. The arena (harness, phase 0)

An arena file (YAML) says which map and asset root, where the party stands and faces, that every placed actor is
removed, and which monsters to spawn where, with optional profile/placement overrides, plus optional party settings
(invulnerable, members). The same file:

- **plays in the game window:** `./tools/run_game.sh --isolated <name> ... --set debug.ai_arena_path=<file>` (a
  one-shot launch directive like the screenshot keys) sets the arena up once the map loads; the decision overlay draws
  each traced actor's latest decisions above it, and the trace goes to a log; `arena reload` in the debug console
  replays it;
- **runs headless:** a scenario step `ai_arena: {path}` sets it up, `advance_runtime` runs it, and
  `assert: {ai_trace: {actor_index, decision, min_count, max_count, within_seconds}}` checks the decisions.

Arena files and their scenarios live in `tests/scenarios/mm9/ai/`; the arena maps are MM9's own BLVs in the MM9 review
root (`output/mm9_rework/assets_dev`: `thearena.blv` for open fights, Isle of Ashes' root for water, a dungeon for
doors and patrols).

## Phases

| Phase | Work | Done when |
| --- | --- | --- |
| 0. Harness | Decision trace, arena file, GUI launch and overlay, console `arena`, scenario steps `ai_arena` and `assert: ai_trace`; arenas for today's behaviour (an MM8 monster, an MM9 skirmisher) as the baseline. | A skirmisher arena runs in the window with its decisions overlaid, and headless with trace asserts passing. |
| 1. Data | The profile generator and catalogue; per-placement fields from the converters; no behaviour change. | Every MM9 row has a profile; MM6-MM8 tables unchanged; converters re-run on the review root. |
| 2. Walkers | Crawler and skirmisher fidelity (arrival timing, 70/45 % retarget, 30 s give-up, kill taunt), per-actor attack reach and sweep, sight/hearing with the 180° view and doubling after contact, alert radius, wince, walker ranged Type 1, ranged holder Type 2, flee rule (runners, hurt or unreachable). | Arenas: crawler, skirmisher, archer (Type 1), sorcerer (Type 2), retarget, give-up, flee. |
| 3. Fliers, swimmers, turrets | Flier passes, back-off up, swoop, flier ranged; swimmer land rule; turret scan, shots and pod launch. | Arenas: bird, banshee, jellyspore/sea monster, lobber. |
| 4a. Layers | Marker patrols and leash, flee/cower/hide, alerts and help calls, the resurrection chain, doors, on every MM9 archetype of phases 2-3. | Arenas: patrol, alarm, flee (hiding place, cower, help), necromancer raising, door. |
| 4b. Layers | Civilians and guards in shared code on BLVs, MM9 factions and hate triggers, dormant starts and spawn-ins. | Arenas: civilians fleeing to guards, dormant mummies. |
| 5. Bosses | Lua behaviours: Dragon King, then Njam, Ebora, Yanmir, summoners. | Boss arenas. |

Each phase updates this file's status table below.

## Status

| Phase | State | Notes |
| --- | --- | --- |
| 0 | done 2026-11-04 | `ActorAiDecision` in `ActorStateUpdate`, `ActorAiTrace` (trace, overlay ring, per-actor overrides), `game/debug/AiArena`, `debug.ai_arena_path`, console `arena`, scenario `ai_arena` / `assert: ai_trace` / `ai_trace_dump`. Arenas in `tests/scenarios/mm9/ai/` (README): MM9 skirmisher, MM9 skull thrower (shows an orbit/throttle flip each step today), MM8 bandit on `out01.odm`. Target switches are world events (the world picks targets) |
| 1 | done 2026-11-04 | [PROFILE.md](monster_ai/PROFILE.md). 252 rows profiled (skirmisher 99, civilian 97, crawler 26, flier 15, swimmer 5, guard 4, ranged holder 3, turret 3); placements written by `mm9_ai_placement.py` from the shared BLV actor builder and the ODM transcoder; saves keep them (version 147). Reconverted: The Arena, Sturmford City, Isle of Ashes; the other maps get the fields at their next `convert.py`. No behaviour change: MM8 scenarios and the actor/tactics/modifier tests pass. |
| 2 | done 2026-11-04 | Walkers (crawler, skirmisher, ranged holder; every other MM9 archetype and MM6-MM8 keep the native AI). Pure rules in `game/gameplay/Mm9ActorRules` (retarget chance, ShouldRunAfter, shot checks, ShouldRunAway, runner roll, wince, perception, reach and sweep; `tests/Mm9ActorRulesTests.cpp`). The loop in `GameplayActorAiSystem` (`AI_Mm9Prelude`, `AI_Mm9Engage`, `AI_Mm9AttackStep`) on `ActorMm9State` (AI-owned, runtime only) and `ActorMm9WorldFacts` (hits, kills, winces, reachability, set by the world). Both runtimes: per-actor reach and sweep, MM9 perception and the held target, the wince roll, hit and kill bookkeeping, the alert radius for the faction alert; indoors also actor perception and reachability from the path planner. Placement `hiding_places` (generator, parser, save 148). Arenas: crawler, skirmisher, archer, holder, retarget, give_up, flee, ranged (tests/scenarios/mm9/ai/README.md). See "Phase 2" below. |
| 3 | done 2026-11-04 | Fliers (15 rows: BaseFly.inc, FlyRange.inc, Banshee.scr), swimmers (5 rows: BaseSwim.inc's land rule on the crawler loop) and turrets (the Lobbers: lobber.scr; the Dragon King keeps the native AI until phase 5). Pure rules in `Mm9ActorRules` (tests in `tests/Mm9ActorRulesTests.cpp`); the loops in `GameplayActorAiSystem` (`AI_Mm9FlierEngage`, `AI_Mm9TurretEngage`, `AI_Mm9TurretIdle`, the prelude's per-archetype hits and detection) on new `ActorMm9State` fields (runtime only, no save change). The world reads `ActorBehaviorRuntime::mm9LoopProfile` (was `mm9WalkerProfile`) for every loop archetype; indoors it adds the water facts (`ActorMm9WorldFacts::waterKnown`, `inWater`, `targetInWater`; a swimmer in water perceives only what is in water) and both runtimes count and place pods (`ActorSpawnRequest`) and play the Lobber's Aware clip. Arenas: bird, banshee, lobber, jellyspore. See "Phase 3" below. |
| 4a | done 2026-11-04 | The shared layers on every MM9 loop archetype (walkers, fliers, turrets; MM6-MM8 and MM9 civilians/guards keep their paths). Pure rules in `Mm9ActorRules` (wander, NewTargetCheck, alert repeat, help radius, cower, run-away turn and tick, resurrection delays, CanResurrectNow, the door test; `tests/Mm9ActorRulesTests.cpp`). The AI (`GameplayActorAiSystem`): the prelude's calls, flight, resurrecter and alert tick; `AI_Mm9Idle` (BaseWander.inc), `AI_Mm9Flee`, `AI_Mm9Door`, `AI_Mm9LayerHold`, `AI_Mm9Corpse`, on new `ActorMm9State` fields (runtime only, no save change) and `ActorMm9WorldFacts` (hiding places out of sight, calls, resurrection, doors); requests in `ActorAiUpdate::mm9Request`, a third traced slot `ActorStateUpdate::layerDecision`. Indoors the world delivers alerts and help calls, answers a corpse's ask, raises and revives, opens doors, wakes MM9 wanderers near the party and plays the cower, ResurrectSpell and Resurrect clips. Data: profile `cower`, `raise_seconds`, `resurrect_spell_seconds`, `resurrect_key_seconds` from the MM9 models (generator); scene door `ai_open` from the DAT's `AITriggerable` (`mm9r_common/dungeon/build.py`; The Arena reconverted); placements unchanged (paths, leash, waits and hiding places were already written). Arenas: patrol, alarm, flee (replaces phase 2's), necromancer, door. See "Phase 4a" below. |
| 4b | done 2026-11-04 | Townsfolk (`civilian`, NPCBase.inc) and town guards (`guard`, PoliceMan.inc on the walker loop) run MM9 loops indoors; MM9's factions (generated `worlds/mm9/relations.yml`: guards and monsters at war, monsters friends; MM9's IsFriend asks both sides) and hate triggers (evt.SetMonsterRelation); dormant starts (the scene's `dormant`: trigger, disturbed, sighted; poses and the Icky's launch) and spawn-ins / death spawns (ScriptParams 1). Pure rules in `Mm9ActorRules` (tests in `tests/Mm9ActorRulesTests.cpp`); the AI in `GameplayActorAiSystem` (`mm9CivilianHit`, the police rules in `mm9WalkerHit` and `mm9ReceiveCall`, `AI_Mm9Dormant`, `AI_Mm9Launch`, the prelude's spawn-in and wake, `AI_Mm9DeathSpawn`) on new `ActorMm9State` / `ActorMm9WorldFacts` fields (runtime only, no save change). Data: profile `guard_refuge`, `wake_seconds`, `dormant_fidget_seconds`, `spawn_seconds`, `aware_seconds` (generator); scene `mm9_civilian` for townsfolk on stand-in rows and `dormant` for self-waking starts (`Content.actor`); Sturmford City reconverted. Arena `events` (timed wake and relation). Arenas: civilians, civilians_monster, guards, factions, dormant, spawn. See "Phase 4b" below. |
| 5 | done 2026-11-04 | Bosses as Lua behaviours on the MM9 loops (`assets_dev/worlds/mm9/behaviors.yml`, `worlds/mm9/behaviors/*.lua`): the Dragon King (`dragon_king.lua`, now on the turret loop with his script picking targets and attacks), Njam (`njam.lua`), Ebora and her concubines (`ebora.lua`, `concubine.lua`), Yanmir (`yanmir.lua`), the summoners (`summoner.lua`). The hold of a script on its loop: `ActorMm9ScriptFacts` (`ActorBehaviorFacts::mm9Script`: drives attacks, passive, ignores calls, chase limit, turn rate; one-shot target and attack; trace lines), `ActorBehaviorMm9Script` in the behaviour runtime (runtime only, no save change) with the Lua API `setMm9`, `target`, `targets`, `actor`, `setTarget`, `attack`, `attackReady`, `seesParty`, `push`, `trace`, `placement`, `summonPoints` and the handlers `onTargetChanged`, `onAttackDone`, `onHit`, `onTrigger`; `evt.TriggerActor` and the arena event `trigger`; decision `script` in the trace. Data: `relations.yml` gains `mm9_dragon` (Dragon.scr AddEnemy AIBase). Arenas: dragon_king (Dragon Stadium), njam, ebora, yanmir, summoner. Also MM9's recovery (Recovery x 33 ms from the clip's end, spells their own; "Recovery" in Phase 5). See "Phase 5" below. |

## Phase 2: walkers

**What runs.** An actor whose profile archetype is crawler, skirmisher or ranged holder runs MM9's loop in real time
(turn-based combat keeps the native turns). Each AI step: its timers; the wince the world rolled; losing its target
(8 s unseen), giving up (30 s since it set up its target or began an attack) or seeing it die; a hit by anyone but its
target (NewTargetCheck); noticing the nearest perceived target (40 % taunt; sight and hearing doubled once it has
targeted the party); ShouldRunAway; the kill taunt. It fights only the target it holds, and the world offers that one.
The engagement: Range.inc's shot check (1-2.5 s, a holder 0.2-0.4 s; outside its attack range, within its range attack
range, attack ready; 100 % with a clear line, 0 without), the blow in reach (always: "Follow-ups"), the holder's
place, CanReachTarget (stop and retry every 1.5 s), ShouldRunAfter with Range.inc's 5 s pursuit veto, the chase. The
skirmisher footwork (strafe attack, evade, back-off taunt, SpeedThrottle) is unchanged on top; `throttle: false` drops
the throttle and `always_evade` evades after every attack (2 s, no strafe attacks). Fear flees as before; otherwise a
walker flees only by ShouldRunAway, with today's flee movement for 15 s or 2 560 units, then drops its target.

**Att% and RangeAttack (resolved by RE, 2026-11-04).** The character sheet copies `Att%` (column 33, record `+0x128`)
to `+0x200` (`0x10052bff`). Its only reader is the getter `0x10053f40`, called once, from the combat manager's action
choice (`0x100b5690`): with a blow (bit 2) and a spell or ranged attack (bit 4) both available, a d100 (1-100) at most
`Att%` keeps the blow, else the ranged attack (`0x100b577d`-`0x100b579d`). The native RE note called it the spell-use
percentage. ~~So `Att%` is the chance a monster in reach strikes rather than shoots or casts (the Evil Sorcerers cast
point blank).~~ **Corrected by the RE of section 7.2.3 (2026-11-04):** that roll only sets a kind that `Attack` ignores,
so a monster in reach always strikes its blow, whatever `Att%` and its script (EvilSorcerer.scr calls no `RangeAttack`
of its own); only a monster holding a ranged weapon prop (profile `ranged_weapon`; no MM9 monster holds one) shoots or
casts by it in reach. `Att%` is rolled once per action and only matters for shots: the out-of-reach shot check's
`CanRangeAttack` keeps the projectile with it, else the spell (below). See "Follow-ups" at the end.
`RangeAttack` (resolved by RE, 2026-11-04, [native RE section 7.2.2](monster_ai/MM9_AI_NATIVE_RE.md#722-attack-kind-spell-choice-rangeattack-and-concat)):
it casts with a chance of `100 - Att%` when the row has attack 2 (100 % without it; never when both spells are defense
or healing), choosing `Spl1` by `SpellUse%1` when it has both spells and its only spell otherwise; else it fires
`Projectile1`. The generator writes these chances as the table's sequential spell 1 and spell 2 chances, and
`mm9RangedAbility` rolls them (`mm9RangedSpellSlot`), then the projectile, else a spell as its only ranged attack.
(Before, the assumption was spell 1 by `SpellUse%1`, else `Projectile1`: a row with a projectile never reached spell
2, and the Oculus never cursed.)

**Assumptions.**
- `EstimateRangeAttackHit` has four outcomes (target 100 %, nothing 20 %, an object 15 %, an AI or the world 0 %);
  OpenYAMM knows only the line to the target, so a clear line is 100 % and a blocked one 0 %.
- `RangeAttackRange` = min(the engine's ranged reach, placement sight - 5 LT): there is no per-projectile range.
- `CanRangeAttack` = a ranged attack at hand (not blind, no Dark Grasp, a line to the party) and the attack ready.
- The melee sweep lands within the attacker's radius + max(sweep, attack reach) + the target's radius at the blow:
  MM9's lunge key, which carries a short-sweep monster (Skeletoids: sweep 54, reach 102) into reach, is not modelled.
- CanReachTarget is the indoor path planner's last answer (a partial or failed plan: unreachable; a direct way:
  reachable). Outdoors no reachability is reported (MM9 maps are BLVs).
- Outdoors the held target is the party only (an actor target is not forced). ~~Perception is limited to the world's
  engagement range, and runtime spawns keep MM9's placement defaults.~~ Both fixed in "Perception fixes" below.
- A target that flies (ShouldRunAway's unreachable branch) is never assumed: the party counts as walking.

**MM9 quirks reproduced.**
- NewTargetCheck doubles the target's distance before its second test, so every attacker that is not farther gets
  x1.15 (70 % becomes 80.5 %, 45 % becomes 51.75 %).
- The 30 s give-up counts only its own attacks and target set-ups: hits by its own target do not reset it. A monster
  that gives up on a party it still perceives takes it again a second later (MM9 searches once a second).
- ShouldRunAfter and the pursuit veto only keep it from starting a run: a run under way continues (MM9's `Stop` is
  commented out).
- The 0.70 re-chase band lies inside RunTo's 0.95 arrival, so a striking crawler chases only beyond 0.95 of its range.
- `Always Wince? = 1` never winces; others roll 20-50 % only at 20 % health or less (and not while attacking: the
  native hit reaction's rule).
- Only runners (placement `runaway_chance`, rolled once per actor) with a named hiding place flee by morale.

**Left for later phases.** Cowering, hiding and running to the hiding place, AlertTick and help calls and the
resurrection chain (done in phase 4a; the faction alert's radius remains the alert radius when the party hits an MM9
walker); fliers, swimmers, turrets (phase 3); the lunge impulse; a taunt clip for crawlers
(the decision is traced, models without a skirmisher taunt clip only stand); a sleep tier. Animation blending glitches
the new movement exposes (crawlers now move while they strike, a one-step stand after a target switch) are out of scope.

## Phase 3: fliers, swimmers, turrets

**What runs.** Real time only (turn-based combat keeps the native turns), on the same prelude as the walkers (timers,
the native wince roll, 8 s unseen, 30 s without an attack, a dead target) with each archetype's own hit and detection
rules.

- **Fliers** (`archetype: flier`: Dragonflies, Ickies, Birds, Winged Mutants, Banshees). On noticing its target it
  always taunts (`taunt_detect`, note `always`). Out of its attack range it flies straight at its target (OpenYAMM's
  flyer aim: the party's head height). In range with its attack ready it makes a pass (`fly_pass`): the blow (always,
  as the walkers: "Follow-ups") while flying level 45 degrees past its target to a random side, at
  0.8 of its speed (at most 200 LT a second) past a still target, straight at a moving one out of range, on along its
  line once the blow has landed. The pass ends in a back-off (`back_off`, note `up`): 1 s straight away from its
  target and up (the direction (away, 0.6) normalised: 0.86 of its speed outward, 0.51 upward), facing it; then a
  swoop (`swoop`): 1 s level, 30-50 whole degrees off the line to its target, facing its flight; then the chase again.
  In range but not ready it backs off (note `up not_ready`). A hit: no target, it takes the attacker; else it switches
  to whoever hit it 50 times in 101; not switching and unable to attack, it backs off at once (note `up hit`). It
  never flees by morale (no BaseRun layer) and never doubles its sight and hearing. FlyRange (`ranged: flier`): a shot
  check every 0.3-1.3 s (`shot_check`, chance 0.60) while not backing off or swooping, needing its attack ready, a
  ranged attack at hand, its target within its range attack range and a clear line; it shoots on the way unless its
  target is less than 1.1 s of flight away. When a back-off ends it may shoot first (2 s after its last shot), holding
  still, and swoops after the shot. Banshee.scr: a 0.6 s back-off rising 0.2, no swoop, and the stat `Undead` during
  each pass (`melee_window`, note `undead`).
- **Swimmers** (`archetype: swimmer`: Jellyspores, Sea Monsters) run the crawler loop. On a map with water volumes a
  swimmer in water notices only what is in water (the party in any swim state but dry, an actor in a volume); a target
  it holds that is not in water sends it running at once (`flee_decision`, note `land`), without the 30 s hold, for
  today's flight (15 s or beyond 1 000 LT, confined to its water), after which it drops the target (`give_up` `fled`).
- **Turrets** (`archetype: turret` but bosses: the Lobber and the Ice Lobber). With no target it scans (`scan`): every
  5-15 s it turns 20-120 degrees to a side at 180 degrees a second. On noticing a target, or a hit with no target, it
  plays its Aware clip (`taunt_detect`, note `aware`; 1.5 s, the model's `aware` script clip) and makes its attack check
  a second later, then every second: a pod (`pod_launch`) while it can lob, else a shot within its range attack range
  (`shot_check`); it faces its target meanwhile, never switches targets and gives up after 30 s without an attack. The
  pod (the profile's `pod_launch` row) comes at the launch's contact time, placed 128 units beyond the Lobber's radius
  toward its target, facing it, of its hostility and group; the world remembers its launcher.

**MM9 quirks reproduced.**
- `GetRandomInt 0, 100` is inclusive: BaseFly's 50 % switch is 50 in 101, FlyRange shoots 61 times in 101 (skips below
  40), a Lobber without a clear shot shoots 26 times in 101 (skips below 75).
- A flier switches on any hit, its own target's too, and a switch restarts its 30 s clock.
- A flier that waits in its attack range for its attack restarts its 30 s clock at each back-off: it never gives up
  there.
- FlyRange's 2 s minimum between shots applies only to the shot after a back-off (its `CanRangeAttack` routine); the
  timed checks ask only the native `CanRangeAttack`.
- FlyRange's check timer starts only when it notices its target, when a swoop ends and at a shot: a flier that took
  its target from a hit checks no shots until its first swoop ends.
- A swoop cut short (a hit while it can attack, or a hit backing it off) leaves FlyRange's swoop flag set: no shot
  checks until a later swoop ends.
- Fliers and turrets never double their sight and hearing (only BaseCrawl's SetupTarget does).
- lobber.scr never sets `g_lastLobberLaunch`, so its 5-10 s wait never runs: a Lobber launches at every attack check
  its native `CanLob` allows (its attack ready and fewer than five pods alive, `0x1002a160`: the pod list at `+0xbcc`,
  count `+0xbe0`, a pod leaves it when its link breaks). The profile's `pod_cooldown_min/max` are therefore unused.
- BaseSwim's land rule runs before BaseCrawl's 30 s hold and asks only whether the target is in water: a dry swimmer
  (Bathhouse's three spores stand in rooms) runs from any dry target it notices.
- A swimmer in water targets only what is in water (`AISwimFly` CanTarget `0x1001c950`); a target it already holds is
  tracked out of the water (tracking does not ask CanTarget) until the land rule sends it running.

**Assumptions and limits.**
- Speeds: a flier flies at the walkers' pursuit speed (the table speed doubled), not the profile's `fly_speed` (equal
  for Birds and Dragonflies; a Banshee flies 896 where MM9 has 640).
- MM9's aggressive tick (0.2 s) runs every AI step; the RunTo arrival (0.95 of the range) is not modelled for fliers:
  the pass starts as soon as it is in range. The chase aims at the party's head height and may end above the party (a
  flier coming down from a back-off passes it from overhead); MM9 maps set no melee vertical reach, so the blow lands.
- A target that flies would keep the back-off level; the party never flies on MM9's maps and actor targets are not
  checked (always rising).
- Hits during a pass are ignored (MM9 backs off mid-pass and again when the pass ends); a carrying-on hit during a
  back-off does not cut it short (MM9 resumes its aggressive tick while the back-off timer runs on).
- A pass is always a blow (native RE section 7.2.3, "Follow-ups"; before, it followed the old `Att%` reading and
  Banshees and Dragonflies cast in passes). The Banshee's melee window is traced only: what MM9's `Undead` stat changes
  is unknown.
- The detection taunt is traced but held only with a skirmisher taunt time (the flier rows have none).
- Fear still makes a flier flee (OpenYAMM's spell rule); BaseFly registers no fear handler.
- The Lobber's launch plays its ranged attack clip and takes its recovery like an attack (the native launch's call into
  the combat manager, `0x1002a223`, was not decoded); MM9 lobs the pod at its target from the `LaunchPod` key, OpenYAMM
  places it. The pod's launcher is runtime only: after a reload a Lobber may launch five more. A shot without a line
  finds no ranged attack at hand in OpenYAMM, so the 26 % blind shot never fires. Its idle has no fidgets, and it scans
  only while active (MM9 deactivates far actors).
- Water facts exist only indoors on maps with water volumes; outdoors a swimmer is a crawler. The party counts as in
  water in any swim state but dry (wading included).
- The Isle of Ashes Sea Monster's boss placement (`ISLE_SeaMon`, patrol and jumps) runs the swimmer loop until phase 5.

**Left for later.** The Icky's hanging start and the flier's slow wander (phase 4: dormant starts, wander layer); the
alerts a flier sends at the end of a back-off and a Lobber on noticing or being hit (phase 4); the Dragon King (phase
5); the pod's lob arc and a `LaunchPod` clip; the Banshee's undead window effect; flying actor targets. Animation: the
back-off plays the flying gait while the flier faces its target (no backpedal clip), the turret's scan turns without a
turning clip, and the crawler loop's arrival flip between `throttle` and `wait_cooldown` (phase 2) shows in the
Jellyspore's trace.

**Open questions.** ~~Whether a pass's `Attack` really casts by `Att%`~~ (resolved, native RE section 7.2.3: `Attack`
ignores the kind, so a pass is always a blow; see "Follow-ups"), and what the Banshee's `Undead` stat does.


## Phase 4a: the shared layers

**What runs.** Real time only, for every MM9 loop archetype (walkers, swimmers, fliers, turrets; civilians, guards
and the Dragon King wait for 4b and 5). Indoors (MM9's maps are BLVs) the world carries the calls, resurrections and
doors; outdoors only the wander runs.

- **Wander and patrol** (`BaseWander.inc`, `AI_Mm9Idle`). A second after it appears a monster with a placement wander
  (`wander: path | aimless`) waits `wander_wait` (3-8 s by default; below 0.2 s it goes at once, `wander_wait`), then
  walks: a path walks to its next marker in turn (random order: any other, never back to the same; `patrol`, `marker
  N`) at the row's walking speed, along the indoor path planner (MM9's rails), touches it within 1 LT of the edges
  (`marker_reached`) and waits again; an aimless walk turns 15-180 degrees (15-90 after a wall stopped the last one)
  and walks `wander_time` (3-8 s; `wander`), stops beyond its leash (`leash` note `stop`), and the next walk heads
  for where it started (`leash` note `home`). With a target the wander stops; when the target goes it starts again
  with a wait where the monster stands. A placement without a wander stands with the native fidgets. A monster that
  wanders thinks within 10 240 of the party wherever it is (MM9 wakes the actors near the player).
- **Flight** (`BaseRun.inc`, the prelude's `mm9StartFlight`/`mm9FlightStep`, `AI_Mm9Flee`). ShouldRunAway (phase 2)
  now needs a hiding place out of its target's sight (the world tests the line from the target's chest to each named
  place; `hidingPlacesUnseen`). A flight begins with the cower roll for a monster whose MM9 model has a Cower clip (10
  in 101: it cowers in place, `cower` note `start`, the model's `cower` clip, until its target no longer sees it at a
  5 s check, `cower` note `end`); else it runs (the path planner, at its run pace) to the first unseen hiding place
  (`hide` note `run`), calling for help every 1.5 s (`call_help` note `hide`), and on arrival stops, turns round, calls
  for help and drops its target (`hide` note `arrived`, `give_up` note `fled`). Without one (a swimmer's land flight)
  it runs off at an angle, re-aiming every 0.3-0.8 s with a help call (`call_help` note `run`), looking for a hiding
  place every 1.5 s, until 15 s (then a cower if it can), 1 000 LT, or ShouldRunAway says no. A flight never loses its
  target nor gives up by the 30 s clock; hits and calls do not turn it. Fear keeps the native flight.
- **Alerts and help calls** (`AICommon.inc` AlertTick, BaseCrawl/BaseFly OnAlert/OnHelp, `mm9ReceiveCall`). A walker
  or flier that sets up a target alerts at once (`send_alert`) and again every g_nRandom seconds; a Lobber alerts on
  noticing a target and at each hit. The world hands the call to every MM9 loop monster thinking this step within the
  sender's `alert_radius` (help: ten times its half height) that is not its enemy (no line of sight, as MM9). A walker
  runs NewTargetCheck on the target named (`alert`/`help` note `take` with no target, else the 70/45 % roll: `switch`
  or `keep`; `ignored` for a friend, a dead one, or while it flees or resurrects); a help call reaches only a monster
  holding no target. A flier takes a help call's target only without one of its own; a turret an alert's.
- **Resurrection** (`AICommon.inc`, `mm9ResurrecterStep`, `AI_Mm9Corpse`). A monster whose placement says
  `can_be_resurrected` and whose MM9 model has a Resurrect clip (`raise_seconds`), once its death clip ends, asks
  (`resurrect_ask`) the first resurrecter (walking the actor list from its end) within 1 000 LT that is thinking, has a
  ResurrectSpell clip and holds no target or the corpse's death target, and again every 5 s while one answers. The
  resurrecter (`resurrect_accept`, unless busy or fleeing) starts 3-6 s later; attacking or wincing it tries again
  0.1 s later; then it faces the corpse and plays ResurrectSpell (`resurrect` note `cast`); at the clip's
  DoResurrection key the corpse is raised. The corpse rises once no actor (nor the party) stands within twice its
  radius (`raised` note `rise`, or `wait` and 0.5 s later again): full health, its Resurrect clip, then the target it
  died holding (`raised` note `attack`). A resurrecter whose second ask finds no one raises itself 2-10 s later
  (`resurrect_ask` note `self`, `raised` note `self`).
- **Doors** (`BaseDoor.inc`, `AI_Mm9Door`). A monster whose move ran into a shut door with `ai_open` (MM9's
  AITriggerable doors, not Locked), heading within 45 degrees into it, stops, faces it, opens it and the movers of its
  group (both leaves, the shells), and stands for its opening time (move_length / open_speed: 1.52 s for The Arena's
  pens) with its script timers paused (`open_door`, marker = the door id). The indoor path map leaves these doors out
  while they are shut, as MM9's rails run through doors, so routes lead into them; an open one (or opening) stands in
  the map where it swung or slid to, as any door does (2026-11-08: Thjorad Mine's slag extractor hatch, left open
  across the corridor, had Hjarrand's scripted walk push into its leaf for ever).

**MM9 quirks reproduced.**
- AlertTick waits g_nRandom, the last random number the script drew, whatever it was: a 40 % taunt roll of 57 repeats
  the alert after 57 s, a wander wait of 3.14 s every 3.14 s, a turn of -60 degrees or nothing drawn yet (0) never.
  OpenYAMM keeps it from the loop's own draws (the taunt and retarget rolls as integers 0-100, shot-check intervals,
  wander waits, walks and turns in degrees, run ticks and turns, resurrection delays).
- A flier never joins on an alert: BaseFly.inc's OnAlert reads the alerter (p0), a friend, instead of the target.
- After a fight a path walks to the marker after the one it was heading for (BaseWanderStop forgets the marker;
  BaseWanderGetNextMarker takes the next).
- The leash only stops the walk; its timer runs on, and the next walk, heading home, walks its whole time (past the
  start and beyond the leash on the other side).
- The run-away turn's side test is `GetRandomFloat 0, 1 == 1`, which a float never meets: a run always turns the same
  way.
- A hiding run has no time or distance limit; only arrival, its target's death or a cleared target ends it.
- A corpse's first ask finding nobody does nothing (g_bAskedForResurrection is set after it); the second decides.
- A resurrecter's search takes the first match from the end of GetObjects' array, so a nearer one may be passed over.

**Not reproduced.** MM9 removes a corpse (gibbers excepted) when an ask after the first finds no resurrecter
(RemoveObject 5 s after death); MM9 drops a separate treasure bag, OpenYAMM loots the corpse, so it stays (and stops
asking).

**Assumptions and limits.**
- Markers carry no per-marker settings (UseMarkerWaitTime, rotation, animation): the placement's wait. A marker
  CanReachObject refuses (MM9 falls back to aimless) is not tested: the path planner walks toward it.
- BaseWanderObstacle ignores 70 % of walls (90 % of actors) and turns by the wall's normal: OpenYAMM sees a blocked walk
  only after the movement step, ends it, turns round and waits.
- The hiding place is the first unseen of HidingPlace0-2 (MM9's FindHidingPlace order is untraced); the global
  hiding-place list is unused (HidingPlaces is 0 on every placement). Outdoors every named place counts as unseen.
  A run's 100 LT wall ray and BaseRunAwayObstacle's side choice (three bumps in a second: cower) are not modelled.
- Calls reach monsters thinking this step and not dormant; one call per receiver per step (the last); the party is a
  valid target for a receiver hostile to it, an actor by OpenYAMM's relations (MM9's IsFriend and hate triggers: 4b).
  The help radius uses OpenYAMM's collision height.
- A resurrecter without a ResurrectSpell clip (Skeletoid, Bone Thrasher, Skull Thrower: skeleton.abc has none) raises
  no one else (assumed: MM9's PlayAnim of a missing clip never reaches DoResurrection); it still raises itself. A dead
  resurrecter is not asked (MM9's IsObjectActive). A raised monster gets full health (`SetStat Resurrect` assumed),
  keeps its hostility and gives experience again when killed. CanResurrectNow counts the party as an actor.
- All layer state is runtime only (no save change): after a reload a wander restarts with its startup second, a flight
  ends, and only a death seen this session asks to be raised (MM9 saves its scripts).
- Doors: map Lua locks (The Arena's LockArenaDoor variables) are not seen by monsters; MM9's CloseWaitTime is not
  reproduced for linear doors (a BLV door stays open as after the party's click; rotating movers keep their own
  auto-close); IsClosed is shut or closing. The door opening pauses the loop's script timers (shot checks, wander,
  alerts, flight ticks, the resurrection wait), as PauseWait; GetTime clocks (30 s give-up, flight time) run on.
- Outdoors (the legacy ODM imports) there are no calls, resurrections or doors; wander and flight run.

**Seams for 4b.**
- Civilians and guards: `AI_Mm9Idle`, the flight (`mm9StartFlight`, hiding places, cower, help calls) and
  `mm9ReceiveCall` take no archetype-specific state; NPCBase.inc's run to a guard and PoliceMan.inc's OnHelp (the
  culprit's class an enemy) are new branches there; `mm9LoopArchetype` gains them.
- Factions and hate triggers: `IndoorWorldRuntime::mm9ActorsAreEnemies` (calls, IsFriend) and `callTargetValid` are
  the places MM9's default "monsters are friends" and HateAll/HateAllOthers plug in.
- Dormant starts: dormant actors are skipped by calls today; "disturbed" wakes on damage, alerts, help and projectiles
  hook into the prelude's hit and call handling. `Mm9WanderPhase::Startup` is where a spawn-in delays the wander.
  AutoResurrect.scr (risen underground on a trigger) can reuse `reviveMm9Actor` and the raised hold.

**Animation notes (out of scope).** The cower, ResurrectSpell and Resurrect clips play as script clips over the stand;
a hiding run uses the walk gait at run speed; a monster waiting at a door or a leash plays its stand.


## Phase 4b: townsfolk, guards, factions, dormant starts and spawn-ins

**What runs.** Real time, indoors (MM9's maps are BLVs); MM6-MM8 actors never carry an MM9 profile and keep their
path, and the engine's relation table and peasant rules are untouched.

- **Townsfolk** (`archetype: civilian`: NPCBase.inc's 86 townsfolk rows, the named NPCs, the animals; and any actor a
  converter placed on a stand-in engine row with the scene's `mm9_civilian`, which runs `mm9StandInCivilianProfile`:
  the MM9 cities place their people on the old import's peasant rows). They never take a target (the NPC class's
  CanTarget is for chat partners) nor hear calls (NPCBase registers no OnAlert or OnHelp), wander by their placement
  (an `immobile` placement stands, but runs when it flees), and never raise the dead. A hit (OnDamage) makes the
  attacker its target and starts BaseRunAway (`flee_decision` note `hit`): a cower roll if its model has a Cower clip;
  a hiding place of its own out of the attacker's sight; else, with `guard_refuge` (every NPCBase row), a town guard
  (BaseRunFindHidingPlace: the guard-archetype actors within 1 600 LT, the first five in the actor list, that stand
  farther than 500 LT from the attacker; GetRandomInt picks one; `hide` note `guard`, the guard's actor index as the
  marker), run to like a hiding place (calling for help every 1.5 s and on arrival, then the flight ends); else a run
  away at an angle that ends at its first tick when ShouldRunAway says no. The importer's `Stationary` (Move 0, the
  named NPCs) does not stop a townsperson: MM9 never reads Move.
- **Guards** (`archetype: guard`, PoliceMan.inc: the four Town Guard rows) run the walker loop (BaseMelee) with its
  police rules: the party is its friend, so the party's hits only count (`turn_hostile` note `hit 1`, `hit 2`) until
  the third makes the party its enemy (`hit 3`, then NewTargetCheck); an alert a monster sends is ignored (`alert` note
  `monster`); a fellow guard's alert or anyone's help call naming its friend the party makes the party its enemy at
  once (`turn_hostile` note `alert` or `help`, the world's `setMapActorHostilityFromEvent`; saved as the actor's
  hostility). A party hit never turns a townsperson or a guard hostile by the native rule, nor rouses its kind.
- **Factions.** MM9's default (IsFriend `0x10018130`): monsters are friends of each other, enemies of the party; the
  engine table already leaves the MM9 rows (9000+) friendly to each other. The one faction a default script sets is the
  guards' (PoliceMan.inc AddEnemy AIBase, AddFriend Player, NPC, Cat, Animal, GuardBase), written as data:
  `tools/mm9_import_discovery/generate_mm9_monster_modifiers.py` also writes `assets_dev/worlds/mm9/relations.yml`
  (factions `mm9_guards`: rows 107-110, `mm9_monsters`: every row whose native class is an AIBase that is not an NPC,
  Animal, Cat or GuardBase; both ways `long`). MM9's IsFriend asks both sides ("not a friend if it considers me an
  enemy"), so indoors an MM9 monster may target, and calls treat as an enemy, another MM9 monster that counts it as its
  enemy (one-way hate triggers, as The Arena's bouts or HateNPC.scr set them). Hate triggers are map scripts: MM9's
  `HateAll` is sent only by Arena.scr (its bouts: already `evt.SetMonsterRelation` in The Arena's Lua), HateNPC.scr and
  Hate.scr are spawn managers' (map Lua again), and the placement hostility gates (MonkHostility.inc and the like:
  every linked monk turns at once) are each map converter's groups and `SetMonGroupBit` (Lindisfarne's).
- **Dormant starts** (the scene's `dormant`, saved; how it waits and what wakes it from the placement's `dormant` or the
  row's). `AI_Mm9Dormant` holds it in its pose (the world plays the `hang`, `hang_fidget`, `coffin` or `sleep` script
  clip) noticing nothing but what wakes it (`mm9DormantWakes`): a trigger (`evt.WakeActor`) and a hit wake every start
  through the world (`wake` note `woken`); a disturbed one also an alert naming a target that is not its friend
  (FlyingIcky.scr IckyAlert), a help call or a target it notices, a hanging one only while it plays its hanging fidget
  (every 2-10 s; `fidget` note `hang`); a sighted one a target it notices (`wake` note `alert`, `help`, `sighted`: it
  takes that target). Woken from hanging it drops at 100 LT/s while its Launch clip plays (`AI_Mm9Launch`), then flies;
  woken from anything else its base starts (MummyAwaken.scr WakeUp: BaseInit) and it looks for a target at its next
  update (0.1 s). The converters write `dormant` for the starts the AI wakes by itself (`starts_dormant`: a placed
  `disturbed` one, a row that hangs by its own script unless its p0 is 2); trigger starts stay with each map's wiring
  (Chasm of the Dead's mummies already set `dormant` and wake them in Lua). A spawn with an MM9 placement starts
  dormant as its placement or row says.
- **Spawn-ins and death spawns** (GreaterDemon.scr, LesserDemon.scr). MM9 runs them only for monsters spawned with
  ScriptParams 1 ("LesserDemon ScriptParams 1", the 1000 Terrors spawners): a placement record that runs its row's script
  with p0 = 1 (`mm9SpawnedWithParam`; arena `mm9_ai: {script_params: "1"}`). A Greater Demon so spawned is hidden
  1.1 s (`spawn_in` note `hidden`), plays its Spawn clip facing the party (`spawn`), then Aware (`aware`: its Taunt),
  then its base starts (`begin`); hits and calls meanwhile are lost (no handlers yet). A Lesser Demon so spawned, once
  its death clip ends, spawns a Greater Demon at its corpse (`death_spawn`, the monster id as its marker; an
  `ActorSpawnRequest` with `mm9Spawned`, whose spawn gets ScriptParams 1 and so spawns in).

**MM9 quirks reproduced.**
- A townsperson whose target is the party ignores every further hit, a monster's too (NPCBase.inc OnDamage exits when
  `g_hTarget` is the player).
- A townsperson without a guard near and without a hiding place runs half a second and stops: its first BaseRunAwayTick
  asks the native ShouldRunAway, which wants a runner with a named hiding place (no help call goes out: the call comes
  after the check).
- A hanging Icky notices a target only during its hanging fidget (FlyingIcky.scr registers OnFoundTarget only in
  Fidget), but wakes on any alert (IckyAlert reads the target, unlike BaseFly.inc's OnAlert, which reads the alerter).
- The hit that wakes a coffin mummy is lost (its OnDamage handler is WakeUp until BaseInit runs).
- Guards share their enemies: a guard turned by the party alerts its fellows about the party (AlertStart on SetupTarget),
  which makes the party their enemy too (PoliceAlert), unless the turned guard already held another target.
- AddEnemy and AddFriend each take the class off the other list (object.lto `0x1001a610`: AddEnemy calls RemoveFriend
  first; `0x1001a7a0` the reverse), so PoliceMan.inc's third hit (AddEnemy Player over AddFriend Player) does turn the
  guard; its RemoveFriend before AddEnemy in OnHelp is redundant.

**Not reproduced.**
- NPCBase.inc's chats (Converse clips, Hello/GoodBye, every 5-15 s), its daily schedule markers (`current_marker`:
  BaseRunAway runs to it instead; the city DATs carry none), and the timer BaseRunCancel leaves running: 1.5 s after a
  cancelled run MM9 searches for a guard again with no target (GetPos of NULL), which is not modelled.
- OnProjectile (a projectile within 200 LT of a townsperson or a hanging Icky makes it run or wake): OpenYAMM reports no
  near misses; only hits and calls count.
- PoliceMan.inc's OnHelp making a culprit that is a friend class other than the party (a townsperson, an animal) its
  enemy: townsfolk never attack, so only the party is handled.
- The spawn-in's client effect (`GreaterDemon` FX) and MM9's sounds: the spawn-in only hides, then plays its clips.

**Assumptions and limits.**
- GetObjects' five guards are the first five in the actor list; CanReachObject is not asked (the path planner has no
  such test); a guard that moves is followed where it stands each step. The guard search uses 3D centre distances.
- `callFromMonster` counts every sender that is neither a townsperson nor a guard (MM9's IsMonster column: Clan Soldiers
  and other IsMonster 0 fighters would be counted as monsters here).
- The Aware state of a spawn-in plays Taunt (the demons have no Aware clip; assumed).
- The guards' hit count, a dormant start's fidget and launch, and a spawn-in's phase are runtime only: after a reload a
  guard counts from 0, and a living spawned Greater Demon spawns in again.
- ~~Which `ScriptName` wins when a placement and its row name one stays open.~~ Closed (2026-11-04): the placement's,
  as MM9 runs it (see "Follow-ups"). Sturmford's prison guard (`sturmguard.scr`, a dialogue script with no AI) is
  passive on his guard loop.
- Outdoors (the legacy ODM imports) townsfolk and guards run their loops without refuges, police calls or dormant
  wakes; the old ODM reactions (`updateMm9ActorReactions`) still apply there.
- ~~The `Stationary` exemption covers townsfolk only; the Magreebs, Njam, the Wyrdes and other MM9 monster rows the
  importer made stationary still do not move.~~ Fixed in the table generator (2026-11-06): MM9 never reads Move, so
  only a row with no velocity is Stationary (the Lobbers, the Magic Mine); Move 0 rows are Short (the MM8 idle's wander
  class; the MM9 loops wander by the placement). Arena `move_zero`.
- Summon placements (`summon: {class, points}`: Summoner.scr, ISLE_Summoner, WizardSummoner, WizardMaster,
  Chasm_GhostSpawner) are set pieces driven by their spawn managers' triggers (`startup`, `trigger`, `focus`): map Lua
  (the converters) or phase 5, not the AI.

**Data.** Sturmford City reconverted (`mm9_civilian` on 45 of its 48 actors: the townsfolk on stand-in rows and the two
dogs; the townsfolk stay `immobile`: they run when they flee; its doors_exits, shops, chests and scripted scenarios
pass); The Arena and the other maps get `mm9_civilian` and the self-waking `dormant` at their next `convert.py`; Isle
of Ashes' placements do not change.

**Checks.** Unit tests (`tests/Mm9ActorRulesTests.cpp`: the pure rules, a townsperson's flight to a guard, the
guard's third hit and help call, a hanging Icky's wake); arenas `civilians`, `civilians_monster`, `guards`, `factions`,
`dormant`, `spawn` headless (tests/scenarios/mm9/ai/README.md) and once each in the game window with an engine
screenshot (`output/mm9_rework/ai_phase4/<arena>.png`, `dormant_rest.png` and `dormant_awake.png` for the dormant arena, each with its trace `<name>.trace.log`): the window runs show the
monster-driven chains (Bjarni running to the guard, the guard fighting the grunt; the guards and the Bandit; the wolf
set on the grunt; the coffin mummies and their wake; the Greater Demon's Spawn clip). The party's hits (a Commoner
running from the party, a guard's three hits, a hit waking a mummy, killing a Lesser Demon for its death spawn) need
`damage_actor` and show only headless; `civilians.png` shows its idle start.

**Seeded damage (follow-up, 2026-11-04).** The retarget arena failed about 3 runs in 7: the monsters' damage dice came
from a thread generator seeded by `random_device` (`rollAttackDamage`), and the world's seeded hit roll reads the
damage, so the Skeletoid ally's hits and misses, and with them the wolf's switch back and its kill, moved between runs
(the kill at 10.6-22.7 s, or none within the 25 s). An MM9 monster's loop now rolls its damage seeded by its actor id,
attack count and MM9 roll count, so the AI stays a pure function of its facts; MM6-MM8 monsters keep the free
generator. The retarget trace is now identical run to run (12 runs: the kill at 18.9 s).

**Left for phase 5.** The Dragon King (hates every AI), Yanmir, Njam, Ebora and the summoners' rituals as Lua
behaviours; the arena events (`wake`, `relation`) are the triggers their scripts and the map Lua send. Animation notes
(out of scope): a townsperson runs with its walk gait at run speed; the Icky's launch holds the stand pose under its
Launch clip while it drops; a mummy waking from its coffin pose snaps to its stand (MummyAwaken plays no Wakeup clip).


## Phase 5: bosses

**What runs.** Real time, indoors. A boss is a Lua behaviour (devdocs/ACTOR_SCRIPTING_INVESTIGATION.md) on its row's
MM9 loop, attached by monster id in `worlds/mm9/behaviors.yml`; each script reads its placement's MM9 script (the
scene's `mm9_ai` `script`, `self:placement()`) and keeps the plain loop where that script is not its own. Lua decides
when, on its own timers and the loop's events; the loop does the work (perception, held targets, attacks, movement).
No per-frame Lua: the scripts think at 0.1-0.5 s and run their timers at the step.

The script's hold on its loop (`ActorMm9ScriptFacts`, set every AI step by `ActorBehaviorRuntime::applyMm9Script`):
`drives_attacks` (the loop holds and faces its target, at `turn_degrees` a second, and attacks only when told:
`AI_Mm9ScriptedEngage`), `passive` (it takes no target, answers no hit or call, never engages), `ignores_calls`,
`chase_limit` (the give-up clock; 0: none), `immune = "physical"` (CanDamage FALSE: a hit of the physical shield tier
does nothing), and one-shots for the next step: `setTarget` (held from then on and offered by the world whatever
their relation: `ActorMm9State::scriptTarget`; its shots hit that target too) and `attack` (`attack1`, `attack2`,
`spell1`, `spell2`; dropped, traced `script` note `not_ready`, when its attack is not ready). The script sees the last
AI step: its held target with MM9's AIGetDistance (centre to centre less both radii), a line to it and its height,
every actor's place and health (`targets`, `actor`), whether it perceives the party (`seesParty`), its attack ready.
Its events: `onTargetChanged`, `onAttackDone`, `onHit` (with the attacker), `onTrigger` (a map's `evt.TriggerActor`,
an arena's `trigger`). Its decisions reach the trace as `decision=script detail="<text>"` (`self:trace`). Until its
script has started (the step after the first AI step that shows it its loop) an MM9 monster with a behaviour is
passive. A boss with a script that its row made `Stationary` walks at its MM9 velocities (MM9 never reads Move), as
townsfolk do.

- **The Dragon King** (`dragon_king.lua`, Dragon.scr). The turret loop (`mm9LoopArchetype` now takes the turret
  bosses) driven by the script. Hidden at the start (a dormant start; the map's trigger wakes it) it lands (its Land
  clip, 5.8 s) and taunts (2.2 s), passive meanwhile, then holds the party (TauntDone). SetupAttack waits 0.2-0.6 s;
  DoAttack by the edge distance: under 200 LT DoCloseAttack (the commented-out hand attack's roll, then 21 in 101 the
  wing buffet: its AttackMelee clip as a scripted action, no damage, a 512-unit push at the clap 0.533 s, then the
  next attack at once; else the breath), under 230 LT the breath (a target higher than DIMS_Z above his feet gets
  rAttack1, the fire bolt, else rAttack3, his first spell Incinerate), under 1 800 LT the fire bolt (attack 1), beyond
  nothing; without CanAttack or CanRangeAttack (attack ready and a line) again in 0.2 s. After an attack
  MaybeSwitchTarget (not within 3 s of the last switch less the hurry; a found target always after 6 s; else 20 %, 80
  % for a nearer one, +45 % for the last attacker) over FindTarget (half the time the targets within wing distance
  first; the last attacker by its place in the list; else the first in range with a shot that is not the current
  one). OnDamage: the last attacker; a hit by another than his target hurries the switch by 0.5 s (20 in 101).
  TargetTooFar beyond 1 800 LT (checked at 0.1 s), OnLostTarget idles, TargetDead looks for the next at once. He
  hates every AI: the generator writes `mm9_dragon` (row 212) hostile to `mm9_monsters` and `mm9_guards` (and the
  guards to him) in `worlds/mm9/relations.yml`; MM9's IsFriend asks both sides, so the monsters fight him back. No 30
  s give-up, no alerts (Dragon.scr includes no AICommon.inc). The trigger, the mutant spawns and the reward stay the
  map's (`dragonstadium.lua`). He never moves (Dragon.scr has no move command; the map places him `immobile`), and a
  turret is rooted (2026-11-11): his row's Fly Y gave him the shared flyer climb, which lifted an arena King placed
  free 1 800 units toward the Winged Mutant he held and left him there once he held the party (beyond his sight from
  up there, so it was never offered and he lost it). No MM9 turret climbs or sinks toward its target now. A flier
  without a target still holds its height, as BaseFly.inc's ClearTarget only starts its wander.
- **Njam** (`njam.lua`). `njam1000.scr` (SpawnNjam's spawns) and `njamtaunt.scr` (the placement the 1000 Terrors
  converter moves to the spawn markers): he targets the party at once, physical blows do nothing, and once his hit
  points fall below the threshold rolled at start (1 500-4 500) he vanishes (the test runs in ShouldRunAway: every 0.2
  s while he holds a target; the effect, then gone a second later); a spawned one (`njam1000.scr`) vanishes on a
  load. `njamchase.scr`: passive until the Chase trigger or a hit, then the same. `njamfreeze.scr`: passive.
- **Ebora** (`ebora.lua`). `eborabath.scr`: passive, physical blows do nothing, Launch on first sight of the party;
  each concubine's death taunts (traced with MM9's text id), the third (or `DeadPal`) sends her off: Launch, CastSpell
  (her ranged clip: the model has no CastSpell), the column of fire (`mm9:column_of_fire`), gone a second later.
  `eboramines.scr`: passive until `FreeAtLast` or a hit, then Fidget2 3 s, Taunt 5 s, Rattack1 2 s, the column of
  fire, gone 3 s later. **The concubines** (`concubine.lua`): Launch on first sight of the party, then their loop.
- **Yanmir** (`yanmir.lua`, YanmirBase.scr) on his crawler + Range loop: physical blows do nothing, alerts are lost on
  him; 3 s after he holds no target, then every 0.5-2 s, a random Ice Lobbercicle within 500 LT that he sees becomes
  his target (15 s chase limit; 45 s on the party), he gives up on a bug after his fourth attack, and 0.2 s after he
  squashed one he wipes his shoe (Wipe). His dormant start and its Squish wake, the trap, the doors and the reward are
  the map's.
- **The summoners** (`summoner.lua`, on the Power Lich). `summoner.scr`: its `startup` trigger summons its class at
  every point and one more at a random point (OnMinionDied: the focus, RAttack1); each minion that dies brings the next
  at a random point; its death stops it. `isle_summoner.scr`: each `spawn` trigger plays hAttack1 and spawns its class
  at its point. The spawn manager is folded into the script, which counts its own minions.

**MM9 quirks reproduced.**
- Dragon.scr's CheckClearShot rolls its 75 % "ignore" and leaves bClearShot FALSE either way: a target beyond breath
  range without a clear shot is never taken from the loop. In FindTarget a candidate skipped for its shot or range
  stays found, so the last one in the list is taken when none qualifies (unless it is the current target).
- FindTarget's g_nTemp (50, or 20 when not on the last attacker) is computed and never used: the wing-distance search
  is always 50 %.
- DoBreathAttack plays rAttack1, the fire-bolt clip and its bolt, at a target higher than his body's depth (flying
  Winged Mutants get fire bolts at point blank).
- After the wing buffet the next attack comes at once (SetupPostWingAttack's wait is commented out).
- Isle_Summoner.scr tests `nCounter >= 5` before counting: six spawns, not five.
- NjamTaunt.scr's placement doubles as SpawnNjam's Njam in the converted 1000 Terrors, so it hunts as Njam1000.

**Assumptions and limits.**
- `CanDamage FALSE` is a physical immunity (YanmirBase.scr's own comment and the TELP note), so Njam's spells-only
  damage reaches his threshold. The converted maps' Lua also zeroes all damage to Yanmir and Ebora (their damage
  hooks).
- The Dragon King's DIMS_Z is his radius (200 LT); the wing push (512 units) is ours; FindTargets' order is by
  distance (nearest first) and its radius 0 means everyone; his MAX_ATTACK_DIST stays 1 800 LT (his placement's sight
  is not larger). A line is known only to the target he holds: every other candidate counts as a clear shot (the
  behaviour layer traces no lines between actors). OnFoundTarget is the loop's perception (his placement's sight).
- The wing buffet's AttackMelee clip plays as a scripted action (`perform`), not an attack: no recovery.
- Njam1000 and NjamChase keep Range.inc's shots (NjamChase.scr has no Range.inc: not modelled); SpawnNjam's own 20-60
  s vanish is the map's (`1000terrors.lua`).
- Ebora's escape in the Bathhouse: the map's handler removes her at the third death at once (before the behaviour's
  Launch and CastSpell); the behaviour's escape plays where no map Lua does (the arena). Her rollover texts are MM9's
  level strings (not in the review root): the trace names their ids.
- Yanmir: his kill is assumed when the bug he held lies dead; the BaseCrawl kill taunt still runs under the Wipe
  (YanmirBase.scr replaces OnTargetDead); his path resumes at the marker the loop chooses (WipeDone's marker restore is
  not modelled); BaseCrawlGetHim's earthquake spot (YanmirDoEQ), KickDoor's clip, TimeToDie, PlayerRanAway and
  DestroyFloor stay the map's or are not reproduced.
- Summoners: the classes are a short table of MM9 class names (Skeletoid, Shadow, Apparition, Specter) or a row number;
  the spawn manager's own limits are map data the review root does not carry (no cap); the sparklies and blue fire are
  traced (`focus`), not drawn at the point (`self:effect` draws at the actor). The Lich Lab's map Lua keeps its own
  SpawnMgr and sends no `startup`, so the summoner there only fights; WizardSummoner, WizardMaster and
  Chasm_GhostSpawner are not scripted. The Isle summoner is attached only on the Power Lich row.
- Directives are runtime only (scripts set them in onStart and onLoad); the saved script state `s` carries the rest.
- Outdoors (the legacy ODM imports): a script target is not offered against the relation, the stationary exemption
  does not apply; MM9's boss maps are BLVs.

**Not reproduced.** The Dragon King's breathing smoke (DoBreathing every 2.5 s), his hand attack (commented out in
MM9), the sleep-until-damaged mode (unused); the Winged Mutants' GetMe on the Dragon King (Dragon.scr's SpawnMutants
sets them on him; the map Lua summons them plain: they fight him only by IsFriend); NjamFreeze's and NjamTaunt's cut
scenes, skins and camera; EboraBath's turn-based fade; MM9's sounds of the boss scripts.

**Checks.** Unit test (`tests/ActorBehaviorRuntimeTests.cpp`: an MM9 boss script drives its loop); arenas
`dragon_king` (Dragon Stadium), `njam`, `ebora`, `yanmir`, `summoner` headless (tests/scenarios/mm9/ai/README.md) and
once each in the game window with an engine screenshot (`output/mm9_rework/ai_phase5/<arena>.png`, trace
`<arena>.trace.log`). Damage-driven behaviour (Njam's vanish, Ebora's concubines dying, the Dragon King's hit, the
summoner's minion death) needs `damage_actor` and shows only headless.

**Recovery (follow-up, 2026-11-04; MM9_AI_NATIVE_RE.md section 7.2.1, "Decisions after the plan").** MM9 actors
recovered about 3 times too long. Now, for MM9 actors on their loops in real time (MM6-MM8 and turn-based mode keep the
shared rule):
- `generate_mm9_monster_tables.py` converts `Recovery` at 33 ms a unit (30 → 0.99 s, 59 ticks; was 0.1 s, 180).
- `AI_StartAttack` sets the cooldown with `mm9AttackStartCooldown` (`Mm9ActorRules`): the clip + the recovery from the
  attack's start, for blows and shots alike, no 0.9-1.2 factor; a cast: the time to its cast key + its spell's own
  recovery (`SPELL.txt` at the row's mastery x 33 ms: profile `spell1_recovery`, `spell2_recovery`, written by
  `generate_mm9_monster_modifiers.py` for the 32 rows that cast; the monster's Recovery where SPELL.txt gives none).
- The hit arms the recovery (`ActorMm9State::hitRecoveryArmed`, the clip left at that moment): a blow whose target is
  in reach, a released shot, a cast. A wince may now cut an MM9 blow or cast while its clip plays (not a shot: its
  rangeAttack state refuses it; indoors), and leaves `mm9CutAttackCooldown`: the hit's recovery, or none before the hit
  or after a miss. Death is the only other interruption; knock-back and conditions do not cut an attack.
- `mm9ShouldRunAfter` is given RecoveryTimeLeft as the scripts read it, 3.03 x the real time left
  (`mm9ScriptRecoveryTimeLeft`): MM9's late arrival.

Measured (arena traces, blow to blow; before → after): Skeletoid (Recovery 30) 2.9-3.4 s → 1.74 s; Grey Wolf (Recovery
40) 3.9-4.5 s → 2.20 s; Bandit 2.9-3.9 s → 1.99-2.19 s, 2.4-3.5 s across an evade; Dragon King fire bolts 3.7 s →
1.9-2.1 s. Re-tuned arenas: archer (25 s, no-shot window between blows in reach), banshee (40 s: Fear's 2.97 s cast
recovery), give_up (the retaken target taunts), holder (the type-2 Bandit's evade off), ranged (strikes now strafe
attacks), dragon_king (the mutant dies sooner). A latent flier bug the faster recovery exposed is fixed: a Banshee's
shot after a back-off no longer swoops (RangeAttackDone's SwoopIn goes straight to SwoopDone). Gap: the outdoor
runtime's wince does not cut attacks (MM9 maps are BLVs).

**Animation follow-ups (2026-11-04; [MM9_ANIMATION_AUDIT.md](MM9_ANIMATION_AUDIT.md) "Follow-ups done").** P1-P7
and the generalised presentation are done. For the AI: an MM9 blow, shot or cast applies at its clip's key and the
action lasts the clip (`attack_timing: clip`, `resolveActorAttackTiming`; recovery as above, now from the real clip),
a coffin or sleeping start gets up with its Wakeup clip before its base runs (profile `wakeup_seconds`,
`mm9WakeHoldSeconds`), and arenas pose their models headless (missiles leave from the release sockets as in the
window). Every arena starts with a party (`new_game_flow`); `alarm`, `archer`, `bird`, `dormant`, `dragon_king`,
`holder`, `necromancer` and `ranged` were re-tuned; new arena `mm6_3d_out` checks MM6 3D monsters.

**Left overall.** The converters' map Lua should send `evt.TriggerActor` for the summoners' `startup`/`spawn`, Ebora's
`FreeAtLast` and NjamChase's `Chase` (and leave the escape to the behaviour), and spawn the mutants with GetMe; the
remaining set pieces (WizardSummoner's ritual, WizardMaster's demon, Chasm_GhostSpawner, ThronheimCity_Badass,
AK_GiantImp, IS_KillingLich, ISLE_SeaMon's patrol and jumps); the outdoor runtime's script targets; and the animation
notes of earlier phases.

## Follow-ups (2026-11-04)

Approved by the user; one shared rule each, driven by generated data, MM6-MM8 unchanged (their tables are byte-identical).

- **No `Bonus` specials** ([MM9_SPELL_MAPPING.md](MM9_SPELL_MAPPING.md) 6.7). MM9 never reads the column: the table
  generator writes no on-hit special attack for any MM9 row (60 rows had one, at level x level %).
- **The placement's `ScriptName` wins** ([monster_ai/PROFILE.md](monster_ai/PROFILE.md) "Placement scripts"). The
  converters resolve each placement's script with the row generator's code (include chain, the loop it starts, its
  hand-overs) and write the scene `mm9_ai` `profile` where it runs a different loop than its row's default: archetype,
  ranged add-on, family hooks, BaseMelee's footwork, or `passive` for a script with no AI (Sturmguard.scr, shopkeepers,
  set-piece fliers). Saved from version 149 (older saves take it from the map's scene). 435 of 2 115 placements in 40
  maps. The arena roots (The Arena, Sturmford City, Isle of Ashes) and a few more are reconverted; every other map gets
  the overrides at its next conversion by the map generation session (the list is in PROFILE.md "Conversion
  status"). Arena `placement_script`: a Ghast placed with KingKong.scr never
  casts, one on its row's baserange.scr does.
- **Blows in reach, the Lobber family** (native RE section 7.2.3). `mm9BlowOrShot`: a monster in reach strikes, with no
  `Att%` roll and no ranged choice, unless its profile says it holds a ranged weapon prop. `mm9RangedAbility`: the
  projectile needs attack 2's damage (attack 1 alone never shoots). Lobber Pods and the Ice Lobbercicle: no projectiles
  in their table rows, the 1.8-2.2 s evade after every attack from their profile (`evade_min_seconds`,
  `evade_max_seconds`, a seeded roll, `ActorTacticsFacts::evadeSecondsMax`). A Lobber's pod launch arms its recovery as a
  released shot does (a wince after the key keeps it); there is no 5-10 s spacing (phase 3 already launched at every
  check `CanLob` allows). Re-tuned arenas: `holder` (the Evil Apprentice strikes a party in its reach), `ranged`,
  `spell_conditions` (the Oculus strikes in reach, casts at its shot checks), `dragon_king` (the Winged Mutant's passes
  are blows, so it comes into his breath and dies at about 19 s without the scenario's kill).

## Perception fixes (2026-11-04)

Approved by the user after the perception RE ([MM9_AI_NATIVE_RE.md](monster_ai/MM9_AI_NATIVE_RE.md) section 5; what
changed is in its section 5.5). Shared code driven by data, no world check:

- **Placement yaw indoors.** Indoor map actors start facing their placement (`initialYawUnits`), as outdoors. This is
  the one deliberate MM6-MM8 change: their DLVs carry a yaw too, which the scene exporter now keeps; 35 placed MM7/MM8
  actors in 10 dungeons turn to it (before/after captures in `output/mm9_rework/perception_fix/`). MM6 has none.
- **Senses beyond the shared ranges.** An MM9 loop monster considers the party, and is updated, as far as its
  placement's sight or hearing reach (doubled after contact), at most 10 240: outdoors over the world's 4 096
  engagement range and 5 632 update range, indoors over the 5 120 activation and line range. MM9's world manifest is
  unchanged.
- **Indoor activation.** MM9 loop monsters are picked apart from the shared selection (no slot of its nearest 30), the
  nearest 48 thinking: the same budget as before, now by distance.
- **Outdoor spawns** keep their MM9 placement (arena `mm9_ai`, a death spawn's ScriptParams 1); saved from version 150.
- **Sight lines** of MM9 loop monsters run from the eye (profile `eye_below_top`, 2 LT below the top) to the party's
  centre.

Checks: unit tests (`tests/Mm9ActorRulesTests.cpp`: sense range, eye; `tests/Mm9MonsterAiTests.cpp`: the profile
field); arenas `perception_placed_yaw` (passes now), `perception_placed_sight` and `perception_placed_sight_beyond`
(the measurement: a placed monster facing the party sees it at 0.94 of its sight, not at 1.06); every arena in
`tests/scenarios/mm9/ai/`; the MM6-MM8 scenarios.

**Open.**
- The 11 outdoor MM9 maps (Boot Camp, its authored variant, Drangheim, Guberland, Isle of Ashes, Lindisfarne, Mountain
  Pass, Sturmford, Thjorgard, its authored variant, Yorwick) still lack `mm9_ai` (RE section 5.4, item 2): default
  sight and hearing, no wander, hostility or dormancy. They get it at their next conversion by the map generation
  session (the transcoder's `placement_ai`); nothing was reconverted here.
- Beethoven's `scenario_doors_exits` fails at step 10 (door 21 open, expected closed). Cause, from the trace: the Bone
  Thrasher placed 573 units from the scenario's start (actor 48, hearing 922) hears the party at once, chases it, and
  when Door3 has shut behind the party it opens the door's other leaf (door 22, scene `ai_open: [21, 22]`, both leaves
  swing) at 5.6 s, MM9's BaseDoor rule (phase 4a). Not caused by the facing: hearing needs none. That is MM9's
  behaviour, so the scenario's expectation is outdated (it was written before monsters opened doors); the map
  generation session owns the scenario (`make_scenarios.py`), e.g. to clear the actors or check the door without AI.

## Repositioning casters (2026-11-05)

Approved by the user ("Decisions after the plan"); an OpenYAMM addition, not MM9. One shared, data-driven rule: the
monster modifier `reposition` ([MONSTER_MODIFIERS.md](../MONSTER_MODIFIERS.md); parameters, defaults and costs there).
No world check: the generator gives it to rows 156-158 (Evil Apprentice, Evil Sorcerer, Evil Grand Sorcerer) and
nothing else; MM6-MM8 and every monster without it take exactly the old path (their tables are byte-identical).

- **Where it acts.** The MM9 walker loop of a ranged holder (`AI_Mm9Reposition`, called last in `AI_Mm9LayerHold`,
  before the engagement). A placement script that makes the row something else (WizardSummoner.scr's skirmisher
  apprentices) drops it with the archetype; a monster that is a holder by its placement's `ranged_type: 2` (Bandits,
  Oculi, the 1000 Terrors' casters) has no modifier and keeps MM9's holder (arena `reposition_unchanged`). The one
  Evil Grand Sorcerer Wizard's Lab places with `ranged_type: 2` is a holder by its row anyway and repositions (the
  user, 2026-11-05: keep it so).
- **Lost sight.** With its held target unseen (`ActorMm9State::unseenSeconds`, the prelude's clock that drops a target
  after 8 s) for `lost_sight_seconds` (2), it asks the world (`ActorMm9Request::reposition`, an `ActorRepositionQuery`)
  for a spot that sees where it **last saw** the target (`ActorMm9State::lastSeenTarget`, the target point the prelude
  notes at every step it sees the target; user, 2026-11-05): it does not know where the target went, and one it only
  heard and never saw gives it nowhere to look. It names up to `candidates` (8) spots it picked itself
  (`repositionCandidates`: rings at half and all of `search_distance` around it, a seeded bearing, pulled inside
  `leash_radius` of its post, its home position; nearest first). The world answers the next step
  (`ActorMm9WorldFacts::repositionSerial/Found/Spot/SightChecks`) with the first spot that passes the blink's spot
  checks, a straight walk on the path map and a sight line from its MM9 eye there to the last-seen point, at least 640 (`back_off_trigger_distance`) from it; it stops before `max_sight_checks` (12) sight
  lines. Found: it runs there (`reposition` note `spot`, the point and the lines tested) and stops once it sees the
  target, on the spot, past its leash or after twice the walk's time (`reposition_arrived` note `sight`, `spot`,
  `leash`, `timeout`); its shot check is due at once. From then on its own perception decides: on a spot reached
  without the target in sight it searches no more for that place (it holds; seeing the target again notes a new
  place), and MM9's 8 s TargetLostTime drops a target that stays unseen. None: it walks back to its post
  (`reposition` note `post`) or holds there (note `none`), and searches again after `retry_seconds` (2).
- **Rushed.** A target it sees, outside its reach and within `back_off_trigger_distance` (640, edge to edge), closing
  at `back_off_closing_speed` (200) or more, makes it ask for room to back off: `back_off_distance` (384) straight away,
  then 30 and 60 degrees to either side, inside the leash and farther from the target (`repositionBackOffCandidates`;
  the world's spot check and direct walk, no sight line). Found: it backpedals there at half its run, facing the
  target, as the skirmisher's back-off phase (`ActorSkirmishPhase::BackOff`), which the model plays as its backpedal clip
  (`back_off_rush` note `spot`); then its shot check is due at once. No room: `back_off_rush` note `blocked` (no spot
  passed) or `leash` (none inside the leash). The next back-off waits `back_off_cooldown_seconds` (5). A target that
  reaches its reach meanwhile is struck, and dodged, as before.
- **Outdoors** too: `OutdoorWorldRuntime::answerRepositionQuery` with the outdoor blink checks (floor, water, slope,
  faces, decorations, bodies) and the outdoor path map; not exercised by an arena (MM9's maps are BLVs).
- **State and cost.** Runtime only, like the other loop state (`ActorMm9State::reposition*`, `backOffWaitSeconds`; no
  save change). Its rolls use their own counter (`repositionCount`), so MM9's roll sequence (and g_nRandom) is
  unchanged. The world tests spots only when asked: at most once per `retry_seconds` per monster while its target is
  unseen, and once per back-off.
- **Shared code it changed.** `blinkMapActorTo` (both runtimes) is split into `checkMapActorSpot` (the checks, with an
  optional MM9 eye and a sight-line counter) and the move; the presentation's backpedal also reads a monster with
  `reposition` but no `skirmisher`; arenas gained the events `door` and `party_walk` (`IGameplayWorldRuntime::
  teleportParty`) and the overrides `reposition_*`.

Checks: unit tests (`tests/Mm9ActorRulesTests.cpp` `*reposition*`: the candidate rings and leash, back-off spots, the
rush and lost-sight rules, the AI's query, walk, sight stop, post and leash ends, the back-off and its end;
`tests/MonsterModifierTests.cpp`: parsing, defaults, errors, tactics). Arenas (`tests/scenarios/mm9/ai/`, README):
`reposition_lost_sight` (searches 2 s after losing the party in the east pen, walks to a spot that sees where the party
vanished, sees it there and casts at once), `reposition_rush` (backs off 384 from a party running at it, its BackpedalRun clip, then casts),
`reposition_leash` (posted by the pen's doorway with a 250 leash: the spots that see where the party vanished and keep
640 from there all lie beyond it, so every search finds nothing, it never moves and gives up at 8 s; with the default
leash it finds one 630 units out),
`reposition_unchanged` (a Bandit placed `ranged_type: 2` holds blind and gives up at 8 s, no back-off). Window captures
in `output/mm9_rework/reposition/`.

**Open.**
- A target that moved on after it vanished is not followed: the spot sees only where it was last seen.
- A sight query rejects spots within `back_off_trigger_distance` of the target, so a monster never repositions into a
  rush; a target hiding close to it may leave it no spot.
- Arrival is within 8 units of the spot, which the sight test used: a spot on the edge of the view can still be missed
  by a step (the next search, 2 s later, picks again).

## Ambient animation (2026-11-05)

Approved by the user ("Decisions after the plan"). MM9's rules are in
[MM9_AMBIENT_ANIMATION.md](monster_ai/MM9_AMBIENT_ANIMATION.md), which records each fix's outcome in its section 4.
One shared code path each, driven by data; no world check.

- **Fidget timer** (§2.1). `AI_Mm9IdleStand`, the idle of every MM9 loop (a wander's waits, an actor that does not
  wander): entering idle arms the fidget 5-12 s later (`mm9IdleFidgetWaitSeconds`); when it comes the actor plays one
  fidget, picked uniformly (`mm9FidgetVariant`), for its clip's length, then idles again with a fresh wait. Only idle
  runs the timer: a walk, a fight, a talk or any other state arms it anew on the return (`ActorMm9State::idleLastStep`,
  `idleThisStep`). The rolls have their own counter (`idleRollCount`), so MM9's other rolls keep their sequence and the
  existing arenas their outcomes. MM6-MM8 keep their 1.5 s stand / 2 s bored idle.
- **Fidget clips.** The manifest's `fidget_variants: true` (`worlds/mm9/models/actors.yml`): a binding's fidgets are
  its `fidget` clip, then its `fidget<n>` and `search<n>` script clips (`ActorModelManifest::BoundClips`, read with the
  attack clips from the model file's clip lengths, so headless runs time them too). The converted models already name
  MM9's numbered Fidget*/Search* clips so, of the right medium for fliers and swimmers (the dragonfly's `fidget2` is
  FidgetAir2), and 69 of 114 MM9 models have more than one. The AI gets the lengths
  (`ActorRuntimeFacts::fidgetClips`); the runtimes show a variant other than the binding's own as its script clip.
  Without variants (an MM9 row drawn as a sprite) the actor plays its one fidget for the sprite's length.
- **Talk turn** (§2.4). `faceMapActorForTalk` (indoor new, outdoor around the old `faceMapActorTowardPoint`) on every
  dialogue path: the actor faces the party at once and stands; its 3D model eases to it at 540 degrees a second
  (3 pi, the presentation's turn rate, which is MM9's NPC turn), a sprite at once. An MM9 actor keeps its facing
  (`ActorMm9State::beginTalk`) and, once its AI idles again, turns back to it at 180 degrees a second (`AI_Mm9IdleStand`);
  a walk (its path's next marker, an aimless walk) or a target cancels the turn back. MM6-MM8 indoor NPCs now turn to
  the party (they did not turn at all) and never turn back, as outdoors.
- **Head look** (§2.4). The profile's `head_turn` (false for the 51 `HeadTurn` 0 rows; generator) and
  `GameplayRuntimeActorState::looksAtHeldTarget`, `headTurn`, `holdsPartyTarget`/`holdsActorTarget`: an MM9 loop
  actor's look follows only the target its AI holds or the party while it is the dialogue partner (the speaker the
  paused world keeps animating), at any distance, and a `head_turn: false` row's not at all. Each model keeps its
  binding's `max_yaw_degrees` (60, or 50) where MM9 allows 90. MM6-MM8 bindings keep the party-in-range look.
- **Trace.** `fidget` is a discrete decision (every one recorded, with `variant` and `seconds` for the MM9 idle; MM6-MM8
  bored stands and the hanging Icky's fidgets are recorded each time too).

**Limits and deviations.**
- The saved animation state is not restored after a talk: the loop resumes from its own state, which is where MM9's
  restore puts it (a walk walks on). An aimless walk resumes facing its way at once; MM9 turns back at 180 degrees a
  second while it walks.
- Fliers and swimmers use the same timer; MM9's flyIdle and swimIdle timers were not traced separately.
- Whether MM9's fidget timer fires during a long dialogue was not traced; ours cannot (the world is paused, and the
  talk cuts the fidget and re-arms the timer).

Checks: unit tests (`tests/Mm9ActorRulesTests.cpp`: `*MM9 idle*` timing, variants, the sprite fidget and re-arming;
`*turns back to its facing after a talk*`). Scenarios (`tests/scenarios/mm9/ai/`, README): `idle_fidget` (two
townsfolk over 70 s: first fidget 5-12 s in, 5-12 s after each one ends, three clips each with their real lengths) and
`talk_turn` (Sturmford City's Bjarni Herjolfssen faces the party, then turns back north 45 degrees in 0.25 s and home
in about one second). MM8: an indoor NPC (d12 actor 2) faces the party on talk and keeps that facing afterwards.

## Townsfolk chats (2026-11-06)

NPCBase.inc's socializing ([MM9_AMBIENT_ANIMATION.md](monster_ai/MM9_AMBIENT_ANIMATION.md) section 2.3), on the
civilian loop; one shared code path, driven by the placement (no world check).

- **Who.** A townsperson wandering aimlessly without a leash or a path (`mm9Socializes`, BaseWanderStartup) looks for
  someone; any other townsperson on the civilian loop (not `passive`: shopkeepers and script-only placements) may be
  asked, wandering, on a path or standing. Only NPCBase.inc townsfolk chat (the profile's `guard_refuge`, which marks
  NPCBase.inc in the script chain): the animals on the civilian loop (FarmAnimal.inc, wander.inc, cat.scr, dog.scr)
  neither look nor answer (2026-11-06; a cat's and a dog's own hang-out with townsfolk is not reproduced). In the converted review maps 118 of 462 townsfolk look (23 in Sturmford
  City), mostly in the cities.
- **The cycle** (`AI_Mm9Chat`, `ActorMm9State::chatPhase`). The first search is set up when its wander starts
  (Startup): 5-15 s later (`mm9SocializeWaitSeconds`, GetRandomInt, whole seconds) it looks for 5-10 s
  (`mm9ChatSearchSeconds`), once a second asking the world (`ActorMm9Request::chatSearch`). The world
  (`IndoorWorldRuntime::answerMm9ChatSearch`) takes the nearest townsperson that thinks this step and that it sees
  (its placement's sight, in front, a clear line: the NPC class's FindTargets is sight only) and greets it: one with
  no target, no chat and not asked by another this step accepts (`Mm9ChatAnswer::Asked` to it, `Accepted` to the
  asker), a busy one refuses (`Refused`: SetupNextChat). Nobody in sight: it keeps looking; the window over, the next
  search is set up again.
- **Together.** The asker walks to the other at its walking speed (`approach`, giving up after 4-10 s); the other
  stands and waits up to 20 s (`hello`). On arrival (edge to edge within 33 units) they stand together for 10-30 s
  (`mm9ChatLengthSeconds`), facing each other at 180 degrees a second, and take turns: the asker first, one Conv clip
  each, handed over when it ends (`mm9ChatTurnIsMine`, the partner's turns and clip in `ActorMm9WorldFacts`). The clip
  is picked uniformly among the model's (`ActorRuntimeFacts::convClips`: the script clip `conv` alone when the model
  has one, else its `conv<n>`; `ActorModelManifest::BoundClips::convRoles`) and shown as its script clip. Between
  clips the idle fidget timer runs, as MM9's SetIdle arms it. Both look at each other (the head look's held actor).
- **Parting.** When its time is over the asker ends the chat (`end`); the other sees it gone (`goodbye`). Both turn
  about by 180 +- 45 degrees at 180 a second (LeaveChat) and the wanderer walks on at once (BaseWanderGo). An end of
  either side for any reason (a give-up, a target, a flight, a talk with the party: `ActorMm9State::endChat`) ends the
  other's the same way.
- **Trace.** Decision `chat` (discrete) with the notes look, refused, approach, hello, give_up, begin, converse (variant
  and length), end, goodbye; the target is the other one.

**MM9 quirks reproduced.**
- Each new search setup stops a wandering socializer and restarts its wander with a wait (SetupNextChat's Stop and
  EnableWandering), so an aimless walker pauses every 10-25 s while nobody is around.
- One who stands still turns away after a chat too (OnGoodBye's LeaveChat), and keeps that new facing.

**Limits and deviations.**
- The city converters placed every townsperson `immobile`, which keeps an MM9 civilian from walking, so no chat
  happened in a city until Sturmford City's converter let its 24 NPCBase.inc aimless wanderers walk (2026-11-07,
  `wanders()` in `level_generation/projects/mm9r_sturmfordcity/convert.py`). The other cities still pin them.
- Indoors only: the outdoor runtime carries no MM9 requests yet (alerts, help calls and resurrections are indoor only
  too). The MM9 cities are BLVs; the outdoor maps' townsfolk (Guberland, Lindisfarne and others) do not chat.
- MM9's messages (Hello, LetsTalk, ChatBegin, YourTurn, GoodBye) are replaced by the world's answer and each side
  reading the other's chat state every step (one step, 1/128 s, of latency). MM9's RunAway cancels the chat timers
  without a GoodBye, which can leave the other one standing; here the other leaves.
- Arrival is edge to edge within 33 units (MM9's `WalkTo hTarget, 0` arrival radius was not traced).
- A model without Conv clips stands through its turns (MM9's empty conversation list was not traced).

Checks: unit tests (`tests/Mm9ActorRulesTests.cpp`: `*MM9 chat rules*`, `*looks for someone, walks over*`,
`*asked to chat waits*`). Scenario `townsfolk_chat` (`tests/scenarios/mm9/ai/`, README): a wandering Commoner looks
7 s in, finds the one standing in front of it, walks over, and they take turns at Talk, Conv5, Conv1 for 29 s; it
ends the chat, the other says goodbye, both turn away and the wanderer walks on (a second chat at 59 s).

## Wander obstacles and posed people (2026-11-07)

User reports from Sturmford City once its townsfolk walked: wanderers slid along walls for whole walks, and MM9's
posed people (the innkeeper, the tavern drinkers, Ludwig, Bjarni) stood as frozen decorations.

- **Wander obstacles** (BaseWander.inc `BaseWanderObstacle`). Ours turned an aimless walker away only when a wall
  stopped it dead; a glancing contact slid it along the wall for its whole 3-8 s walk. MM9 raises the notice at every
  contact: a wall stops the walk 30 % of the times (another actor 10 %), the walker faces away along the wall's normal,
  waits and its next walk turns only 15-90 degrees. Now the indoor movement step notes the contact
  (`ActorMm9State::wallContact` with the wall's horizontal normal, `actorContact`; kept until the wander reads it,
  since several movement steps run between two AI steps) and `AI_Mm9Idle`'s aimless walk rolls it
  (`Mm9WanderWallStopChance`, `Mm9WanderActorStopChance`), recorded as the wait note `obstacle wall` / `obstacle
  actor`. Sturmford City over 240 s: 246 obstacle stops in 457 walks. Indoors only (the outdoor runtime notes no
  contact). The wait is the wander's own 3-8 s; MM9's is WANDER_LEASH_WAIT, 5 s.
- **Posed people** (`level_generation/projects/mm9r_common/rude_props.py`). MM9's RUDEProps loop one animation for
  ever (PropAnim.scr `LoopAnim`, Sturmgaardinn.scr, TryggvaSpeech.scr, ErccSpeech.scr, LudwigVan.scr, Bjarni.scr,
  AkeRetainer.scr). They are now actors on the HD body of their model and skin (no model of their own), passive,
  immobile, never hurt and `posed` (`MapDeltaActor::posed`, saved from version 164): the indoor world never moves them
  (no initial placement fix, no movement or physics step), so they sit in their seat's collision. The map's load
  handler loops their pose and holds their facing (`evt.PlayActorClip`, `evt.FaceActorTo`: the presentation replaces
  the AI's animation and turns the head look off, so they neither turn nor look at the party in a dialogue). Their
  scripts' use parts (voice line, keys, Ludwig looking up) and exit parts are the actor hooks.
- **Clip sequences.** `evt.PlayActorClip(actor, {"ercc01a", "ercc01b", "ercc01c", "ercc02"}, "hold")`: a list plays
  its clips in order (`GameplayRuntimeActorState::scriptedClipThen`, resolved by the model presentation from the clip
  lengths), the end rule (true: loop, "hold": hold the last frame, else release) applies to the last one.
- **Clips.** `mm9_peasantm2` and `mm9_peasantm2d` carry MM9's PeasantSeated/PeasantWork clips as script clips
  (`sitting`, `sitting2`, `listen`, `conv_seated`, `ercc01a-c`, `ercc02`, `ercc_out`, `ludwig_writing`,
  `ludwig_lookup`, `innkeeper2`); the named heroes use their `sit`. Known defect: in the seated clips the thighs cut
  through the tunic's side panels (the skirt hinges cannot drape a horizontal thigh; cloth work).

- **Names** (user, 2026-11-07). The hover label of an MM9 person showed its body's row (Commoner, Shopkeeper, Monk).
  `resolveMapDeltaActorName` now gives an actor with its own RUDE dialogue (`mm9RudeId`) its own name, the one its
  dialogue shows; dogs, monsters and other actors without a dialogue keep their row's. The converters' shared pass
  (`level_generation/projects/mm9r_common/dungeon/people.py`, every map) names such an actor by NPCNAME.rude where it
  had kept a DAT object name (PoorTownGuard10, ForadDarre, TronPlayer) or its row's name (Lindisfarne's Monks and
  Initiates, the Baron): 36 actors on 9 maps, which take their names at their next conversion (Sturmford City done).

- **Greeting voices** (user, 2026-11-07: "no sound on talking"). MM9's talk sounds are only a placement's
  GreetingSound (the native NPC use plays it) and a voice in its script's :OnUse; the RUDE dialogues carry none, and
  ordinary townsfolk have neither (MM9 is silent there too; 75 NPC voice files are referenced by nothing). The shared
  `dungeon/voices.py` read only the scripts, and skipped a click the map's Lua handles: 65 voices on 16 maps were
  missing (Sturmford's shopkeepers, trainer, banker, clerk...). It now reads GreetingSound first and puts the voice
  in front of a map's own click handler that does not play it. Sturmford City rebuilt; the other maps take it at their
  next conversion.
- **Walk or run** (user, 2026-11-07: children "very slowly", a villager "running very slowly"). The speeds were
  MM9's (adults walk 192 / run 384, children 128 / 320), but the model's clip was picked by speed, so short-strided
  walks lost to the run: wandering women and children jogged their run below its authored rate, the dwarves ran at
  the cap. MM9's actors.yml now says `gait: intent` (walk while the AI walks, run while it hurries, unless that clip
  would crawl or scurry outside its window) and the townsfolk walk strides were remeasured: MM9_ANIMATION_AUDIT.md A8.

## Dragon King against fliers (2026-11-06)

The handoff's open question ("he rarely hits the flying mutant since his bolts launch from his mouth"). Six headless
runs of `dragon_king.arena.yml` with the Winged Mutant starting at different places (scratch arenas, projectile debug
`OPENYAMM_INDOOR_PROJECTILE_DEBUG=1`): 25 bolts and breaths at the mutant, 10 hits. Four runs hit 2 of 2 or 3 and kill
it at 16-19 s; two account for the misses.
- **Blocked line.** A mutant hovering by the stands (192, -1778, 2720) took 7 bolts, all into wall face 1583 or ceiling
  face 1595: the line from his mouth is blocked where his clear-shot fact (the line to the target he holds) says clear.
- **Moving target.** A mutant circling 800-950 units away dodged 7 of 9: the bolt (4 000 units/s) flies at where it
  was at release; MM9 leads no target either (native RE section 7.3).
- **MM9's bolt explodes.** `PROJECTILE.txt` gives DragonFireBolt (and FireBolt) a 25 ft damage radius (12 LT a foot,
  NPCBASE.inc's "100 feet" = 1 200: 300 LT, 768 units) with 20 % at the edge (`Min Radius Pct` 0.2), and DragonBreath2
  30 ft. The generator maps them to the MM6-MM8 `Fire` missile, which hits only what it touches. With MM9's blast most
  near misses and the wall hits by the stands would still burn the mutant. Other MM9 projectiles carry blast radii
  (RedYellowThingy, RingOfFire, ScreamingSkull 10 ft) or homing (`HS *` columns: RedThingy) the generator drops too.
  Fixed 2026-11-06 ([MM9_PROJECTILES_RE.md](MM9_PROJECTILES_RE.md)): MM9's blast hits everyone whose centre lies within
  `damageRadius` (no sight test) with the attack whole; `Min Radius Pct`'s falloff never applies (the RPG attack
  replaces the engine's distance-scaled damage) and the `HS *` homing columns are never read: MM9's projectiles fly
  straight. So the generator writes `missile_blast` (the attack missiles' radii, devdocs/MONSTER_MODIFIERS.md) for the
  rows with one, the launch sets the projectile's `explosionRadius`, and the shared area impact spares the shooter,
  its friends and the actor it struck; no homing. Not reproduced: MM9's burst at the end of a projectile's lifetime
  (ours expires quietly; the Dragon King's bolt flies 19 000 units in its 5 s) and the push-back of blast victims.

## Timed conditions (2026-11-06)

MM9's party conditions come only from monster spells and wear off: `SPELL.txt`'s `Duration (min)` for the cast's
mastery, plain or per point of the cast's e1 or e2 skill (the `MONSTERS.txt` cell is `Spell,Mastery,e1,e2`;
Spell::Duration `0x1008af90` and its siblings: `[+0xdc]` x 60 game seconds). An MM9 game minute is 60 x 33 ms, 1.98 s;
ours is 2 s, so MM9's minutes carry over 1:1.

- **Data.** `spell_conditions` gains `spell1_minutes` and `spell2_minutes` (0: until cured, MM6-MM8's default), written
  by `generate_mm9_monster_modifiers.py` (`spell_durations`, `duration_minutes`) for the 15 rows: Paralyze 5-10 min
  (Oculus 10, Petrified Mummy 10, Dragon King 5), Curse 3-5, Fear 20-100, Dark Grasp 70-100.
- **Engine.** `Character::conditionExpireGameMinutes` (saved from version 157); `Party::applyMemberCondition` with an
  end time (a recast keeps the later end; one without a time, any MM6-MM8 source, lasts until cured);
  `Party::setGameMinutes` clears a condition whose time has passed (every member and MM9 hireling; resting and waiting
  count) and drops the time of one something else cleared. The monster spell hit passes its slot's minutes
  (`MonsterHitCondition::minutes`, `GameplayCombatActorInfo::spell1ConditionMinutes`).
- **Decisions.** The durations run on the game clock in turn-based mode too (MM9's clock moves one game second a round
  there, so Paralyze would last about 600 rounds: not reproduced). MM9's short Curse (3-5 min) is kept on our Cursed.
- **Not changed.** Rest still clears only Unconscious, Drunk, Fear, Asleep and Weak; Protection from Magic, saves and
  immunities as before.

Checks: unit tests (`*spell_conditions minutes*`, `*timed conditions*`, `*timed condition keeps its end time*`, the
modifier parse test), `tools/mm9_import_discovery/test_generate_mm9_monster_modifiers.py`.

## Marker stops (2026-11-06)

BaseWander.inc OnWanderAtMarkerNext ([MM9_AMBIENT_ANIMATION.md](monster_ai/MM9_AMBIENT_ANIMATION.md) section 4 item 6):
at a wander path's marker MM9 stops, takes the marker's own wait (`UseMarkerWaitTime`: `WanderWaitMin/Max`, a 0 read as
0.01) once, turns horizontally to the marker's facing at 360 degrees a second (`UseMarkerRotation`) and plays its
`AnimationName` looped (`LoopAnim`) or once, if the model has it; the next walk replaces it.

- **Converter** (`tools/mm9_import_discovery/mm9_ai_placement.py`, both callers pass every object's properties and
  their own facing function): `mm9_ai.path_stops: [{point, face, wait, clip, loop}]` for a BaseWander path (not the
  patrol scripts' marker lists, whose stops read no marker data). Clip roles: Fidget1 is `fidget` (the binding's own),
  `fidget<n>`, `taunt`, hAttack<n> is `attack<n>`. The maps get them at their next conversion (map session): about 60
  walkers pass a facing or wait marker, 8 a clip marker (Guberland and Thronheim city guards, the Thjorgard
  cutpurses, Hatlati in Sturmford city, Yanmir).
- **Engine.** `Mm9AiPathStop` in the placement record (saved from version 157; older saves walk without stops),
  `ActorMovementFacts::mm9PathStops`; at a marker `AI_Mm9Idle` takes its wait and starts its turn
  (`ActorMm9State::markerTurn`) and clip (`markerStop`, `markerClipSeconds`); a walk, a target, a talk or a chat's
  hello ends them. The runtimes show the clip as a script clip with an end mode (`ScriptedClipEnd`: Hold, as
  behaviours had it, Loop, or Release, which gives the AI's animation back after a clip played once); the role
  `fidget` plays the binding's own fidget. A role the model lacks plays nothing, as MM9's GetAnimNbr -1.
- **Limits.** Hatlati's `fidget5` is missing from `mm9_peasantm2` (nothing plays, as MM9 would without it). The idle
  fidget timer no longer runs under a looped marker clip (MM9's LoopAnim holds its script state 0x11, which never
  fidgets: [ambient animation](monster_ai/MM9_AMBIENT_ANIMATION.md) section 2.1, traced 2026-11-10).

Checks: arena `marker_stops` (a Town Guard: marker 1's 4 s wait, its turn to the south, Fidget2 looped; marker 0
the placement's wait); unit test `*parses its path's marker stops*`, the placement save test;
`tools/mm9_import_discovery/test_mm9_ai_placement.py` (`test_wander_path_stops`, `test_marker_clip_roles`).

## Backpedal (2026-11-06)

[MM9_ACTOR_ANIMATION_BLENDING_RE.md](MM9_ACTOR_ANIMATION_BLENDING_RE.md), the section on strafe and fliers: MM9's
animator fills an empty BackPedal list from Walk and BackPedalRun from Run (`0x1001e266`, `0x1001e2b7`) and never
plays a clip in reverse. `WorldFxSystem::syncActorModels` now does the same: a backpedal plays the model's backpedal
clip for its gait (`backpedal` for the walk, `backpedal_run` for faster gaits) or else the gait forwards; the trace's
` rev` marker is gone. Only the MM9 skirmish footwork asks for a backpedal, so MM6-MM8 models are unaffected; a walker
without backpedal clips now steps forwards while it slides back, as in MM9 (the Oculus beats its wings forwards).

## Animals (2026-11-06)

MM9's animals run the civilian loop, and most wander whatever their placement's `WanderON` says (asked by the map
session; the converter's `placement_ai` decides it from the script the placement runs, its own or its row's):

- **cat.scr, dog.scr** (cat, dog, mouse, evil mouse: rows 294, 295, 299, 300): StartUp calls BaseWanderForceStartUp a
  second in, so they always wander, aimless or on a path, by the placement's own WanderLeash, WanderWaitMin/Max and
  WanderTimeMin/Max (BaseWanderStartup reads a 0 as 0.01 s, as it now does for every wanderer).
- **wander.inc** (pig.scr, hen.scr, rooster.scr: rows 269-271): their own loop, no WanderON check: within
  MAX_DIST_FROM_STARTPOINT of the start (ScriptParams p0, else 350 LT), a 5 s tick re-heads them 15-90 degrees or
  pauses them (about 40 %, an idle or special clip). Written as `wander: aimless`, leash (p0 or 350) x 2.56, waits
  [5, 5] and walks [5, 10] s: an approximation of the tick.
- **FarmAnimal.inc** (cow.scr, goat.scr: rows 267, 268, 297): FarmAnimalInit sets WanderWaitMin/Max to 10 and 20, then
  BaseWander starts only with WanderON; so they stand without it and wait 10-20 s with it.
- Chats are NPCBase.inc's alone (the profile's `guard_refuge`): no animal looks for anyone or answers.

**Open (not reproduced).** A cat's and a dog's hang-out with townsfolk (every 10-20 s it finds an NPC, walks to it,
sits 8-15 s: LoopAnim StandDown and its sit fidgets, follows it beyond 120 LT, then wanders on), a dog chasing cats
(DogChase, the cat's run and give-up), the pig's rest and roll and the hen's peck and sit clips at wander.inc's
pauses, and a tipped cow starting to wander when it stands up (cow.scr's EnableWandering).

Checks: `tools/mm9_import_discovery/test_mm9_ai_placement.py` `test_animal_wanders`; unit test `*MM9 animal on the
civilian loop never looks*`. The maps get it at their next conversion (map session).

## Awareness of the party (2026-11-07)

The user's request: MM9 monsters should notice the party in range whatever way they face, notice it farther, and answer
a ranged hit, with their friends close by, but not one from very far (as MM6-MM8's provoked rule outdoors,
`re_mm8/PARTY_HIT_AGGRO.md`, scaled to MM9). Decided: all-round sight, sight x 1.5, provoke range 4 096, radius 256;
sleeping (dormant) monsters are not woken by any of it.

The engagement range is 3 800 (the user, 2026-11-09; 4 096 before), and so is the provoke range. Before contact the
scaled sight goes no farther than 4 275 (world.yml `mm9Sight max`): the engagement range and 12.5 % more, as MM6-MM8
notice outdoors a little beyond their yellow alert (full-AI range 5 632 against 5 120). MM9's default sight, 1 320 LT
(3 379 units), would reach 5 068 at 1.5, and 59 % of placements saw farther than 4 096 (6 912 for 14 %). Doubled
after contact it reaches 8 550 at most. Scenario:
`tests/scenarios/mm9/party_notice_range.yml`.

The party cannot hit from beyond that range either (the user, 2026-11-09): its shots vanish and its targeted spells are
refused past the world's declared engagement range, 3 800 (`GameplayActorService::partyHitReach`), under any ruleset,
so no hit lands where it would not provoke and the HUD shows green. Worlds that declare no range (MM6-MM8) use the
engine's 5 120, the yellow alert range. Area spells (Souldrinker, Inferno, Mass Fear ...) take no monster beyond it
either; Armageddon strikes the whole map. Monsters shoot and cast at the party from no farther than that same reach
(`ActorAiFrameFacts::partyHitReach`, capping Range.inc's range from the placement's sight), so the party can answer
every shot. Scenario: `tests/scenarios/mm9/party_hit_reach.yml`.

**Before.** MM9's own rule (native RE section 5.1): sight only in the front half-space, hearing all round but short
(922 by default, 369 on most of Isle of Ashes), both doubled after contact. A party hit made the monster take the party
(NewTargetCheck), but the world offered the held party only within its doubled sight, so a shot from farther (3 072 for
a 600 LT placement; arrows indoors fly about 24 000) left it standing until it gave the party up 8 s later (`lost`). Its
MM9 alert reached friends that then needed to perceive the party themselves. The scene's `actor_detection` neighbour
wake sets `hasDetectedParty`, which the MM9 loop never reads (and MM9's outdoor regions turn it off).

**Data.** `world.yml` `actorAwareness` (`Mm9PartyAwareness`, `game/gameplay/Mm9ActorRules.h`; undeclared: MM9's
rules, so MM6-MM8 and any world without the keys are unchanged):

```yaml
actorAwareness:
  partyEngagementRange: 3800
  mm9Sight: {allRound: true, scale: 1.5, max: 4275}  # seen all round; placement sight x 1.5, at most 4275 before contact
  mm9Provoke: {range: 3800, radius: 128}     # a party hit within range provokes; its friends it sees within radius too
```

`radius` is the provoked friends' distance from the hit monster, centre to centre (`Mm9PartyAwareness::provokeRadius`;
undeclared or 0: the monster's own alert radius). A map may set its own: scene `actor_detection: {provoke_radius: N}`
(`IndoorMapData::actorProvokeRadius`), which wins over both.

**Rules** (indoor runtime; only monsters on an MM9 loop, civilians, guards and passive scripts keep MM9's):
- Sight: `mm9PartySenses` scales the placement's sight, `mm9PartyInView` makes the view all round. Both apply to the
  party only (monsters perceiving other actors keep MM9's rule) and not to a dormant start, whose own wake rules
  (sighted, disturbed) see with MM9's senses.
- A party hit within the provoke range (`mm9PartyHitProvokes`, the party's distance to the monster's edge) sets
  `MapActorAiState::mm9Provoked`: the world offers the party it holds as far as the provoke range
  (`mm9HeldPartyRange`) wherever it stands, so it runs at the party until it loses it (8 s without a clear line, as
  MM9's TargetLostTime) or gives up (30 s). It is cleared once the monster holds no target. A provoked monster thinks
  ahead of the nearest 48.
- Its awake friends within the world's provoke radius, 128 (the user, 2026-11-09; 256 before, then for a day its own
  alert radius, MM9's AlertRadius x Scale, 3072 for most rows; not enemies, hostile to the party, a clear line from its
  eye to their centre)
  are provoked too and hear of the party as from an alert (`alert`, `take` in the trace). Dormant starts are skipped:
  they wake only by their own rules (a hit on themselves or their group, a trigger, MM9's alerts for disturbed ones).
- A party hit from beyond the provoke range (`mm9PartyHitTooFar`, `ActorMm9WorldFacts::attackerTooFar`) is no reason to
  take a target: the hit reaction plays, nothing else (it may still see the party within its own senses).
- MM9's row alerts are unchanged: friends within the row's alert radius take the party but keep it only as far as
  their own senses reach.

**Limits.** Indoor only: every MM9 map is a BLV (the outdoor runtime's MM9 loop, used by outdoor arenas, keeps MM9's
rule). The provoked state is not saved (after a load a provoked monster keeps the party only within its senses).

Checks: unit test "MM9 party awareness"; scene parse ("indoor actor detection"); world manifest; arenas `provoke`
(too far, provoked, the friend beside it, the farther friend on the MM9 alert only, a coffin mummy sleeping on) and
`sight_all_round` (behind it and within x 1.5, beyond it, a sighted sleeper with MM9's view).

## Doors a monster opens from either side (2026-11-07)

Found by the map session's walker check after the cities' townsfolk were set walking: Guberland City's bank staff and a
peasant at the Palace opened the same double door every 5 s without getting through. The doors are `open_away`
rotating leaves with `bodies: reverse` and MM9's 5 s `auto_close_seconds`.

- An `open_away` leaf took its side from the party (`IndoorSceneRuntime::chooseMoverOpenAwayDirections`), wherever the
  party was. A monster opening it from the party's far side met the leaf swinging into it, the leaf turned back shut
  on its body, and the monster, seeing a shut door again, opened it again.
- A leaf also keeps its side until it is shut: a monster that reopened a door still swinging shut after a walker from
  the other side reopened it toward itself, with the same result.

Now (`IndoorWorldRuntime::openMm9Door`): a door a monster opens from shut swings away from that monster
(`RuntimeMechanismState::openerSet`, runtime only; the party's clicks are unchanged), and a leaf swinging shut on the
monster's side is left to shut; the monster's next try (after its 1.8 s door wait) opens it away from it. Guberland City
over 150 s: every walker gets through (at most two tries more than before at a door used from both sides) and reaches
its markers. Arenas `door`, `flee`, the four `reposition_*`, `give_up`, `patrol`, `dormant`, `provoke` pass.

The other symptom of that check, walkers that never start or stop half way, is the indoor activation range: no MM9
actor thinks beyond 10 240 units of the party (`ActiveActorUpdateRange`; MM9 also deactivates far actors). Guberland
City's ten walkers placed beyond it stand until the party comes near; a walker whose marker lies beyond it stops at
the range's edge (the Palace peasant at about 10 260).

## Townsfolk facing the party (2026-11-08)

User report: Thjorgard City's tavern dwarves, placed facing each other (MM9's rotations, kept by the converter), all
faced the party after entering the city and stayed so in the save. A yaw trace of Dagfinnr found the cause: an actor
outside the thinking set (beyond the activation range or past the 48 nearest) runs `updateBackgroundActor`, MM8's
background `AI_StandOrBored`, which turns it to the party at every idle decision (about every second), from any
distance. Entering at the city gate turned the whole city toward it; at the tavern the dwarves join the thinking set
on MM9's loop, which never turns an idle actor back, so they kept the gate's bearing. Now an actor on MM9's loop keeps
its facing in the background too (both runtimes, by data: the MM9 loop profile); every MM6-MM8 actor still turns as
before. Scenario `tests/scenarios/mm9/ai/background_townsfolk.yml`.

Turn-based mode had the same effect (`updateTurnBasedPausedActorAnimations`, as MM8's TurnEngine, turns every nearby
actor to the party while it waits): an actor on MM9's loop that is not hostile to the party now keeps its facing there
as well (scenario `turn_based_townsfolk.yml`); hostile MM9 monsters still face the party. Saves made before the fixes
keep the turned facings in their map state (a fresh entry of the map, or one rebuilt since, restores MM9's).

## Per-group enemies and the party's blows (2026-11-08)

User report (Drangheim Prison): after the alarm the gate guards stood for 15 s; Nagate killing guards rang the alarm.
MM9's `AddEnemy` is per object: only the three barracks guards (GuardToNegate.scr) add the Nagate, but the map gave
the relation to every guard row, so the kitchen guards fought the pen's Nagate at load and the alert relay
(`deliverMm9Call`, faithful) carried the unreachable beetles to every guard, which kept switching to them. Now a relation
row may name an actor group on either side (`evt.SetMonsterRelation({group = n}, monster, relation)`,
`GameplayActorService::relationGroupSide`; a group's row wins over its monsters' rows), and the map gives the relation to
the barracks group only. DrangheimHostility.inc turns a guard on only for the player's blow (`IsPlayer`): the damage and
killed hooks' context now carries `byParty` (indoors at each damage source; the killed hook from `killedByParty`, also
outdoors). Tests: "a relation row may name an actor group" (GameplayActorAiSystemTests).

A path marker's clip named by a binding's `clips` role (`attack_melee` from a marker's HAttack1, the smith's anvil) did
not resolve in `WorldFxSystem` (only `script_clips`, `fidget` and raw clip names did), so the actor stood; the roles now
resolve to the binding's own clips.

