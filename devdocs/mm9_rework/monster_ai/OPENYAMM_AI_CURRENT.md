# OpenYAMM monster AI today, and how MM9 monsters map onto it

Research date 2026-11-04, against the working tree (uncommitted changes included). Purpose: the starting point for
MM9-faithful monster AI as a native base plus optional cheap Lua extensions. No code was changed. Line numbers are
approximate anchors in a busy tree; search for the named function if they have drifted.

Related: [Actor scripting](../../ACTOR_SCRIPTING_INVESTIGATION.md), [Monster modifiers](../../MONSTER_MODIFIERS.md),
[Energy shields and relations](../../ENERGY_SHIELDS_AND_RELATIONS.md),
[MM9 animation blending and combat AI RE](../MM9_ACTOR_ANIMATION_BLENDING_RE.md),
[MM9 monster collision RE](../MM9_MONSTER_COLLISION_RE.md), [MM9 monster jump RE](../MM9_MONSTER_JUMP_RE.md),
[MM9 water design](../MM9_WATER_SWIMMING_DESIGN.md), [MM8 creature movement](../../../re_mm8/CREATURE_MOVEMENT.md).

## Summary

- **One shared, stateless AI function.** `GameplayActorAiSystem::updateActors(ActorAiFrameFacts) -> ActorAiFrameResult`
  runs at a fixed **128 Hz** in both world runtimes. The world builds a fact record for every live actor, the AI returns
  state, animation and movement intents plus attack, projectile, audio and effect requests, and the world applies them.
  It reproduces MM8's model: four AI types, Attack1/Attack2/Spell1/Spell2 chosen by table percentages, MM8's Pursue1-3
  and the ranged orbit, with OpenYAMM additions (crowd steering, path planning in the world, tactics).
- **Extension points already exist** at three cost levels: per-monster data (`modifiers.yml` → `ActorTacticsFacts`),
  declarative `tactics` in `behaviors.yml`, and event-driven Lua behaviours (`onThink` every 0.5 s by default).
- **MM9 today = MM8 AI + MM9 numbers + one MM9 behaviour.** The table generator maps MONSTERS.txt stats, speeds,
  recovery, attacks and spells into MM8-style rows. The only MM9 combat behaviour reproduced is BaseMelee's footwork
  (the `skirmisher` modifier, 2026-11-02). Sensing is one world-wide radius (4096). Melee reach, lunge, wince, target
  preference, ranged script types, flyer swoops, resurrection and the civilian/guard rules on BLV maps are dropped.
- **Least-churn plug-in point for an MM9 AI profile:** the `skirmisher` route. Generated `modifiers.yml` entries →
  `ActorBehaviorCatalog::applyMonsterModifiers` → `ActorTacticsFacts` → guarded `AI_*` helpers. A few concerns sit
  outside the AI function (sensing radius, melee reach, wince, civilian rules) and need world-side hooks. The profile
  costs well under a microsecond per active actor per step. Line of sight, path planning, collision and building the
  facts dominate.

## 1. The current AI model

### Data flow and tick

| Step (each 1/128 s) | Where |
| --- | --- |
| Fixed step constant | `IndoorWorldRuntime.cpp:111`, `OutdoorWorldRuntime.cpp:724` (`ActorUpdateStepSeconds = 1/128`); AI's own `ActorAiTicksPerSecond = 128` at `GameplayActorAiSystem.cpp:16` |
| Outdoor loop | `OutdoorWorldRuntime::updateMapActors` (`:12432`): MM9 civilian reactions → yell-flee → `m_actorBehaviors.step` → `selectOutdoorActiveActors` → `collectOutdoorActorAiFrameFacts` → `applyAiFacts` → `applyChargeHolds`/`applyFrenzies` → `updateActors` → `observeAiResult` → `applyOutdoorActorAiFrameResult` → charges, stagger tick, inactive actors, side effects |
| Indoor loop | `IndoorWorldRuntime.cpp:10889-11000`: the same order (`collectIndoorActorAiFrameFacts` at `:5482`) |
| Per-actor facts | `collectOutdoorActorAiFacts` (`OutdoorWorldRuntime.cpp:9990`), `collectIndoorActorAiFacts` (`IndoorWorldRuntime.cpp:10134`) |
| Post-move AI pass | `GameplayActorAiSystem::updateActorAfterWorldMovement` (`GameplayActorAiSystem.cpp:5208`): crowd steering and blocked-move reactions (`AI_CrowdSteer`, `AI_HandleMovementBlock` `:2100`) |

Facts in (`GameplayActorAiTypes.h`): `ActorAiFacts` (`:461`) = identity, stats (AI type, HP, speed, `canFly`, spells and
chances, attack dice, ranged constraints), runtime timers (action, cooldown, idle, crowd, skirmish phase), status
(spell effects, hostility, forced flee, `climbAboveTarget`), target (current target, edge distance, line of sight,
candidates), movement (position, home, wander radius, speed, posts, leash, dormant, patrol), world (sector, active),
behaviour directives (scripted hold, attack-rate multiplier) and tactics. Updates out: `ActorAiUpdate` (`:596`) of
optional state fields, animation, an `ActorMovementIntent` (`:518`) and at most one `ActorAttackRequest`, plus audio and
effect requests. Projectile requests are collected per frame (`appendActorUpdate`, `GameplayActorAiSystem.cpp:5096`).

**Active and background actors.** Every live actor gets facts each step. Up to **48** are "active" (full AI, target
scan, line of sight); the rest are "background" (`updateBackgroundActor`, `:5017`: they age timers, idle and face the
party, with no target search and no combat).

| | Indoor | Outdoor |
| --- | --- | --- |
| Active limit | 48 (`IndoorWorldRuntime.cpp:867`) | 48 (`OutdoorWorldRuntime.cpp:510`) |
| Range | 10 240 (`:824`) | 5 632 (`:509`), plus "provoked" actors up to the long range |
| Priority | Party's sector first, then MM8's Active/Nearby bits by distance (`:5260-5470`) | Nearest (`selectOutdoorActiveActors`, `:9841`) |

An MM9 outdoor map built as a BLV is one open-air sector, so on the BLV route "same sector as the party" selects
every actor and the 48 cap decides. There is no other level-of-detail tier or sleep: background actors still get a full
fact record every step.

### Motion states and the decision tree

States (`ActorAiMotionState`, `GameplayActorAiTypes.h:25`): Standing, Wandering, Pursuing, Fleeing, Stunned, Attacking,
Dying, Dead. Skirmish sub-phases (`ActorSkirmishPhase`, `:40`): StrafeAttack, BackOff, Evade, Circle, Taunt.

`updateActor` (`GameplayActorAiSystem.cpp:5057`), each step for an active actor:

1. Death or status lock (stun or paralysis) → `AI_DeathOrStatus` (`:4531`).
2. Pick a target (`chooseTarget`, `:2656`): keep the current target if it is still sensed, else the first available
   candidate with line of sight. The world already picked the nearest valid target: the party if sensed, else the
   nearest hostile actor (`resolveOutdoorTargetFacts`, `OutdoorWorldRuntime.cpp:4083`; indoor `:10351-10490`).
3. Attacking → `AI_ActiveCurrentAction` (`:4890`): age the action, apply the impact at the contact frame, then the
   skirmish step or stand.
4. A scripted hold (Lua `perform`, charge, frenzy, dormant, shield stagger) → `AI_ScriptedHold` (`:4984`).
5. Otherwise `AI_ActiveBehavior` (`:4955`): continue a flee → `AI_CombatFlow` (`:2579`: blind wander, flee, engage or
   friendly stand, `chooseCombatFlowAction` `:2185`) → `AI_AttackOrPursue` (`:4282`) → `AI_StandOrBored` (`:4760`:
   stand, fidget, wander inside the home radius, patrol or post).

### AI types (flee rule)

`GameplayActorAiType` (`GameplayRuntimeInterfaces.h:273`); flee test `GameplayActorService::shouldFleeForAiType`
(`GameplayActorService.cpp:742`), applied in `resolveActorEngagement` (`GameplayActorAiSystem.cpp:1393`) only while the
target is within 10 240.

| Type | Flees |
| --- | --- |
| Suicide | never |
| Wimp | always while engaged |
| Normal | below 20 % HP |
| Aggressive | below 10 % HP |

Fear forces a flee; blindness forces a random wander. Lua `setNoFlee` and `setAiType` override per actor. Flee runs
at 2× speed (`FleeMoveSpeedMultiplier`, `:36`), straight away from the target.

### Attack choice

`AI_AttackOrPursue` → `chooseCombatAbility` (`:1204`) → `chooseCombatEngagePlan` (`:2344`).

1. **Ability roll** (`chooseAttackAbility`, `:1070`), deterministic per actor (seeded by actor id and a decision
   counter): Spell1 by `spell1UseChance` if castable (`monsterSpellIsOkToCast`, `:847`: no re-buffing, heal only when
   hurt, and so on), else Spell2 by its chance, else Attack2 by `attack2Chance`, else Attack1.
2. **Range fix-up.** Out of melee range with a melee ability, it switches to a ranged ability if it has one.
3. **Ranged commit** (`shouldCommitToRangedAbility`, `:1137`). Beyond `MaximumRangedAttackDistance` (5 120, `:30`;
   further if the party shot it from further away) it never shoots. Inside 1.15 × melee range it never shoots.
   In between it shoots by a distance band roll: 15 / 30 / 50 / 72 / 84 / 68 % for gaps past melee of < 256 / 640 /
   1280 / 2560 / 4096 / more, +10 for spells. A failed roll falls back to melee and closes in. Blindness, Dark Grasp
   or no line of sight block ranged. A tactics `ranged_band` or `kites_party` bypasses the roll.
4. **Engage plan.** Ranged and ready → attack. Ranged, not ready → orbit (MM8 Pursue1: a small step round the target's
   circle, one side per actor). Melee in range and ready → attack. In range, not ready → stand. Out of range →
   pursue: Direct (MM8 Pursue1) under 1 024, else OffsetWide (±45°, MM8 Pursue3) (`resolvePursueAction`, `:2419`).
5. **Melee range** is a global constant: `ActorMeleeRange = 307.2` edge distance (`:28`), halved against actors
   (`meleeRangeForCombatTarget`, `:1065`), plus the world's vertical reach (`world.yml actorCombat`).
6. **Timing** (`startAttack`, `:534`). The action lasts the attack animation (at least 0.1 s). The cooldown is the
   table recovery (ranged: recovery + action) × a random 0.9-1.2, and at least action + 0.25 s for melee. The hit lands
   at the authored contact frame or at the end of the action (`sprite_attack_timing.yml` / `actors.yml` events).
   `telegraphed_attack` and the Lua speed multiplier alter it.

### Movement modes

| Mode | Behaviour | Where |
| --- | --- | --- |
| Ground | AI gives a heading and speed. The world integrates with collision, floors and gravity, and uses the path planner (worker threads) for pursuit. Pursue and flee are 2× table speed, capped at 1 000 (`movementSpeedForMotion`, `GameplayActorAiSystem.cpp:128`) | Indoor movement controller and planner (`IndoorWorldRuntime.cpp:9125-9160`), outdoor `applyOutdoorActorMovementIntegration` |
| Fly (`canFly`) | Same heading logic plus `desiredMoveZ` toward the target's height (+ `climbAboveTarget`) in `applyActiveMovementCommit` (`:2555-2571`). A pure vertical gap is closed in `AI_Pursue` (`:3327`). Outdoors a ranged flyer targets party Z + radius + 512 (`OutdoorWorldRuntime.cpp:10231`). Indoors the path plans the feet at the aim height under the ceiling (`flyingFootZUnderCeiling`, `IndoorWorldRuntime.cpp:4777`, `:9141`). Flyers ignore AI barriers | as listed |
| Swim (MM9) | Monster table Fly cell `S`/`YS` → `MonsterStatsEntry::swims`. On a map with scene water volumes, a swimmer that starts in a volume becomes a flyer bound to that volume: a step whose centre leaves it is refused, and it keeps its placed height. Walkers in water: half speed, they sink to the bed | `IndoorWorldRuntime.cpp:19990-20020` (binding), `:3429` (placement), `:9509-9570` (walkers); indoor only |
| Drops | Map flag `actorDropsFollow` raises the walker drop limit (MM9 follows the party down any drop) | `IndoorWorldRuntime.cpp:4720`, `:9134` |

The MM8 baseline these reproduce (state steering, pursue/flee 2×, cap 1 000, no path search in the original) is
documented in `re_mm8/CREATURE_MOVEMENT.md`. OpenYAMM keeps its own planner on purpose
(`re_mm8/CREATURE_MOVEMENT_COMPARISON.md`).

### Per-monster parameters the AI reads

From `monster_data.txt` (`MonsterTable::MonsterStatsEntry`): AI type, Fly (`Y`/`N`/`S`/`YS`), Move (Stationary, Short,
Med, Long or Free, which gives the wander radius), speed, recovery, attack preferences (Pref, used by the party-member
choice: `Party::chooseMonsterAttackTarget`, `Party.cpp:3430`), Attack1/Attack2 type, dice and missile, Att%, Spell1/2
and their use %, and the special (Bonus) on-hit condition. From `monster_descriptors.txt`: height, radius, ToHitRadius.
From sprite or `actors.yml` timing: attack, impact and sound times. World-wide: `world.yml actorAwareness.partyEngagementRange`
(sensing radius, `GameApplication.cpp:8461`) and `actorCombat.meleeVerticalReach`. Per placement (scene): immobile,
leash, dormant, patrol points, keeps_height, ally/group/hostility.

### Extension points

| Layer | What it can do | Cost | Where |
| --- | --- | --- | --- |
| **Monster modifiers** (`worlds/<w>/modifiers.yml`) | Fixed catalogue: `true_aim`, `never_staggers`, `stagger` (damage-window threshold, cooldown), `telegraphed_attack`, `kites_party`, `charge`, `frenzy`, `blink`, `sounds`, `indoor_meteor_shower`, `skirmisher` | Data. `skirmisher` and `kites_party` become tactics; the others are native state machines in `GameplayActorModifiers` | `game/tables/MonsterModifiers.{h,cpp}`, `GameplayActorModifiers.{h,cpp}`, `ActorBehaviorCatalog::applyMonsterModifiers` (`ActorBehaviorCatalog.cpp:416`) |
| **Tactics** (`behaviors.yml tactics`) | Traverse rate and fire cone, lead, turret scan, ranged band, post and leash, shield-break reaction, skirmish | One hash lookup and a 108-byte copy per actor per step (`applyTactics`, `ActorBehaviorRuntime.cpp:1445`) once any monster has tactics. MM9 does, through `skirmisher` | `ActorTacticsFacts` (`GameplayActorAiTypes.h:383`), `AI_TacticEngage`, `AI_HoldPost`, `AI_TacticIdleAim` |
| **Lua behaviours** | Handlers: `onStart`, `onLoad`, `onThink` (`think_interval`, default 0.5 s, min 0.05), `onDamaged`, `onHealthBelow`, `onTimer`, `onWardBlocked`/`Expired`, `onPerformDone`, `onDeath`. Commands: perform (hold + clip), wards, timers, `castNext`/`setSpell`, `setAiType`, `setNoFlee`, summon, blink, shields, leave, `setSpeed`, `setInvulnerable`, `setArmoredFront`, `setLeash`, `setRangedBand`, `moveTo`, `runEvent`, `qbit` | Lua runs only on events and thinks. Saved state is serialised after every handler call (`ActorBehaviorRuntime.cpp:2131`). With no instances and no monster defaults, `step` returns at once (`:1063`) | `assets_dev/engine/behaviors/behavior.lua` (API header), `ActorBehaviorRuntime.{h,cpp}`, `ActorBehaviorCatalog.{h,cpp}`; attach per monster (`worlds/<w>/behaviors.yml monsters:`) or per actor (`evt.SetActorBehavior`) |
| **Placement fields** | Immobile, leash, dormant, patrol | Data | `MapDeltaActor` (`game/maps/MapDeltaData.h:45`), applied in `ActorBehaviorRuntime::applyAiFacts` (`:1294`) |

Lua never drives movement or targeting ("Lua decides when; native code does the per-frame work"). No world in
`assets_dev` attaches a Lua behaviour today; `engine/behaviors/behaviors.yml` declares only `bosses/necro_mage`. MM9 has
`modifiers.yml` only.

### Cost profile

- **The decision function is cheap.** It is branching over one fact record. The world-side work is expensive: line of
  sight, target scans, path planning and collision.
- **Fact records are large and rebuilt every step.** `sizeof(ActorAiFacts)` = 960 bytes and `sizeof(ActorAiUpdate)`
  = 536 (measured with the project's flags). Strings: display and spell names (usually short enough for SSO). For every
  live actor, background ones included, each step:
  - outdoors the record is copied into the frame (`push_back(*actorFacts)`, `OutdoorWorldRuntime.cpp:9978/9982`);
    indoors it is moved;
  - `updateActor` copies it again (`GameplayActorAiSystem.cpp:5059`);
  - an active actor also gets a candidate vector reserved to the map's actor count (`IndoorWorldRuntime.cpp:10385`).
    Outdoors that vector holds every available actor within 10 240 (`buildCombatTargetCandidates`,
    `OutdoorWorldRuntime.cpp:4030`), O(active × N) per step.
- **Line of sight.** Outdoors it is cached per pair for 0.125-0.23 s (`cachedActorLineOfSight`, `:9901`). Indoors
  `hasIndoorCombatLineOfSight` runs per active actor per step, now grid-accelerated (BLV_GEOMETRY_COSTS.md E1/E2).
  Indoors, actor-vs-actor sight inside the same sector is assumed true (`:10447`), so on a one-sector MM9 outdoor
  BLV every actor sees every other.
- **Measured.**
  - Classic MM6-MM8 BLVs: 0.9-2.3 ms CPU per active monster per game second, about 7-18 µs per step.
  - MM9 rooms of 4 800 faces: 23-25 ms per monster per game second before the 2026-10-31/11-02 engine fixes.
  - Sturmford as a BLV, 200 monsters (48 active): monster update 157 µs (it was 340 ms before the face grid), frame
    CPU p50 0.46 ms, against MM8 Ravenshore's 0.73 ms (`../BLV_GEOMETRY_COSTS.md`).
- **Behaviour layer.** Tactics: one `unordered_map` lookup per actor per step. Lua: about 2 calls per second per
  scripted actor plus events, each followed by a state serialisation.

## 2. MM9 MONSTERS.txt columns: honoured, approximated or dropped

Sources: `tools/mm9_import_discovery/generate_mm9_monster_tables.py` (writes `assets_dev/worlds/mm9/data_tables/
monster_data.txt` and `monster_descriptors.txt`, ids 9000 + row), `generate_mm9_monster_modifiers.py` (writes
`assets_dev/worlds/mm9/modifiers.yml`). 134 rows are IsMonster 1. Distinct values below are over those rows. Unit scale
LT × 2.56.

| Column (index) | MM9 values | Status | How and where |
| --- | --- | --- | --- |
| Fly (14) | 0/1 | **Honoured** | `fly_cell` (`gen…tables.py:344`): `Y`/`N`. Banshees (162-164) forced to fly (`SCRIPT_FLYING_SOURCES`, `:25`). AISwimFly rows → `S`/`YS` (`SWIMMER_SOURCES`, `:29`) |
| Walk/Run/FlyVelocity (16-18) | 50-350 | **Approximated** | `movement_speed` (`:351`): table speed = max(velocities) × 2.56 / 2, capped at 1 000. The pursuit doubling then gives MM9's run (or fly) speed. Walk = half the run (MM9 walks at about a third) |
| Move (15) | 0-8 | **Not read by MM9** | `MOVEMENT_TYPES` → MM8 wander classes (Short, Med, Long, Free) for the MM8 idle only (allies, charmed actors); Move 0 with a velocity → Short (2026-11-06: it was Stationary, which held the Magreebs, Forad Darre and the other Move 0 rows still). Only all-zero velocities → Stationary (Lobbers, Magic Mine) |
| Recovery (22) | 10-80 | **Mis-scaled** | `recovery_ticks` (`:367`): 0.1 × value seconds → ticks ÷ the 2.133 OE factor. The AI adds a 0.9-1.2 jitter (`startAttack`). **Wrong by 3×:** MM9 counts game seconds of 33 ms (30 → 0.99 s) from the end of the attack clip, with no jitter ([native RE §7.2.1](MM9_AI_NATIVE_RE.md#721-recovery-its-length-its-clock-and-when-it-starts)). The evade does not touch recovery: `DoEvade` lasts a fixed 2 s (`BaseMelee.inc:172-173`) |
| Type/Damage/Projectile 1-3 (27-39, 66-72) | | **Honoured, with substitutions** | Attack3 replaces Attack2 when present (`build_data_row`, `:479`). Projectiles → engine tokens (`PROJECTILE_TOKENS`). `Elem` → an element from the projectile. Horde rows forced to melee (`MELEE_ONLY_SOURCES`, `:31`) |
| Att% (33) | | **Honoured** | `attack2Chance` |
| SpellUse%1/2, Spl,Mas,Skil (40-43) | | **Approximated** | MM9 spell ids → nearest engine spells (`SPELL_NAMES`, `:97`: Curse/Paralyze → Dark Grasp, Fear → Mind Blast, Souldrinker/Death's Touch → Dragon Breath…). Spell2 with chance 0 gets 100 − spell1 |
| `concat` spells, ConcatAttk (62) | 10-25 on 10 rows | **Approximated / dropped** | A `concat` spell becomes the melee special condition (`condition_for_concat_spell`, `:424`; `special_attack`, `:438`). The ConcatAttk percentage is not read; the engine's own special-attack chance applies |
| Bonus (24) | conditions | **Approximated** | `SPECIAL_ATTACKS`: Steal → item break, Stun → Paralyze x1 |
| ScriptName (52) | 22 scripts | **Partly used** | (a) AI type heuristic `ai_type` (`:327`): basemelee, dagrell, dragon, greater/lesser demon, titan and yanmir → Suicidal; guardbase/monkbase → Normal; the rest Aggressive; farm animals Wimp. MM9's own `ShouldRunAway` is not RE'd. (b) `skirmisher` for every script that includes `BaseMelee.inc` (101 rows incl. NPCs). (c) Banshee flight. **Dropped:** range.inc Type 1/2, BaseCrawl, BaseFly/FlyRange swoops, BaseSwim, Lobber, Magreeb, Dragon, Ghost, Banshee behaviour and every boss script |
| Strafe Attack Pct (60) | 0-100 | **Honoured** (BaseMelee rows) | `modifiers.yml skirmisher.strafe_attack_chance` → `ActorTacticsFacts::strafeAttackChance` |
| Evade Chance (59) | 40 everywhere | **Honoured** (BaseMelee rows) | `skirmisher.evade_chance` (default 0.4). Evade 2 s; ends beyond 1 280 (MM9's 500 LT) |
| Taunt (model clip, not a column) | | **Honoured** | `taunt_seconds` from the model's Taunt clip when the `actors.yml` binding has a `taunt` script clip. 40 % chance. Not after a kill (MM9's KilledTargetTaunt) and not for actor targets |
| LungeVelocity (19) | 50-250 | **Dropped** | The skirmisher lunge is a fixed 1.25× run in the wind-up beyond 0.9 of reach (SpeedThrottle's blending-model rule, `SkirmishLungeSpeedShare`, `GameplayActorAiSystem.cpp:77`). The plain-model impulse (LungeVelocity × 2 toward the target at the `lunge` key) does not exist, and the converter drops the `lunge` keyframe |
| AttackRange (21) / AttackReach (20) | 60 (most), 40-250 / 36 (most), 0-150 | **Dropped** | Melee range is the MM8 constant 307.2 edge distance for every monster (`ActorMeleeRange`, `:28`; `meleeRangeForCombatTarget`, `:1065`). MM9's 60 LT = 154 and 36 LT = 92, so MM9 monsters start swings about twice as far out as MM9 did. The skirmisher's 0.25/0.5/0.75/0.9 range shares scale that constant. Ranged reach is the global 5 120 |
| AlertRadius (25) | 1200 (125 rows), 1600 (9) | **Approximated world-wide** | `worlds/mm9/world.yml actorAwareness.partyEngagementRange: 4096` (1600 LT) for every MM9 actor; 1200 LT would be 3 072. No per-monster radius. Infighting and flee checks still use the 10 240 long range |
| Target Pref (23) | `0` 74; CP, S, X, E, H, XE, G, AR, DR, P, `2` | **Dropped** | The generator writes Pref `0` (`:506`), though the engine supports class, sex and race preferences (`MonsterTable.h:17-33`). MM9's letters need a class mapping (MM9 has no Knight/Paladin set) |
| Always Wince? (44), WinceThreshold (45), WinceTrackTime (46) | 0/1; 40 or 0; 0.5 s | **Dropped** | Every damaging hit starts the hit reaction (`beginMapActorHitReaction`, `IndoorWorldRuntime.cpp:15959`, and outdoor) unless `never_staggers`. The `stagger` modifier (threshold % over a window, cooldown; `MonsterModifiers.h:126`, `GameplayActorModifiers::allowsStagger`) matches this shape but is not generated for MM9 |
| HeadTurn (56) | 1 on 84 rows | **Approximated, not from the column** | 179 `actors.yml` bindings carry hand-authored `look` blocks (neck/head track the target) |
| Resurrect (73), ResurrectFX (77) | 1 on 15 rows | **Dropped** | Written only to `monster_conversion_audit.tsv`. No native ability, and Lua has no corpse query or raise command |
| Hostility Group (63) | 1, 2, 4, 6, 7 | **Dropped** | Hst `4` (or `0` for farm animals) (`:505`). Monster-vs-monster relations come from the base matrix by id. 9 000+ rows fall outside it, so as I read `MonsterTable::getRelationBetweenMonsters` (`MonsterTable.cpp:1580`) they read as friendly unless a placement's `ally` maps them. MM9 has no `relations.yml` |
| SPD (11) | 9-45 | **Dropped** | Not read |
| Scale (58) | | **Body only** | Collision body overrides (`MM9_MONSTER_COLLISION_RE.md`); no per-actor draw scale |
| Special (57), Accuracy (26, empty) | | Dropped | — |
| FootSound/FootRadius/Voice Radius/Transparent/FX* | | Not AI | presentation |

MM9 world rules outside MONSTERS.txt:

| MM9 rule | Status | Where |
| --- | --- | --- |
| Civilians flee 15 s from a hostile party and call guards within 4 096 every 0.5 s | **Outdoor ODM only** | `OutdoorWorldRuntime::updateMm9ActorReactions` (`:12086`), constants `:515-519`, flags `mm9_civilian`/`mm9_guard` written only by `transcode_mm9_dat_to_odm.py`. The BLV converters write none (0 in the review root's `sturmfordcity`/`thronheimcity` scenes), and `IndoorWorldRuntime` has no equivalent |
| OnFoundPlayer RUDE events | **Indoor and outdoor** (2026-11-06) | `updateMm9FoundPlayerEvents` in both runtimes: once a second (`Mm9TargetSearchSeconds`), fired when `mm9Perceives` (placement sight in front, hearing all round, a clear line from 0.75 × height to the party at z + 96); once per visit, the map Lua's `FoundPlayerDisabled` keeps a once-only greeting from repeating. Scenario `mm9/found_player_bootcamp.yml` |
| AIBarrier (monster-only walls) | **Honoured** | scene `actor_barriers`, also walls of the monsters' path map; flyers ignore them (`devdocs/INDOOR_OPEN_SKY.md`) |
| Follow down drops | **Honoured per map** | `actorDropsFollow` |
| AI rails | **Not used** | Our planner instead (`../SPIRAL_STAIR_PATHING.md`) |

## 3. Known MM9 AI gaps already recorded

| Gap | Source |
| --- | --- |
| Lunge is a fixed wind-up window, not the `lunge` keyframe; no KilledTargetTaunt; no taunt for actor targets; upper-body mask is `upper_body_root`, not MM9's `Top` set | `MM9_ACTOR_ANIMATION_BLENDING_RE.md` "Not reproduced" |
| range.inc Type 1 (shot every 1-2.5 s with an EstimateRangeAttackHit chance 100/20/15/0 %, fire on the run, `ShouldRunAfter`) and Type 2 (Evil Sorcerer: never chases, stops before each shot) are described but not implemented; the native distance roll decides instead | same doc, "Ranged" |
| Skirmish state is runtime only, not saved | `MONSTER_MODIFIERS.md`, blending RE |
| Flyers lack BaseFly's climb-away (up 0.6 for 1 s) and angled swoop back in; "optional later work" | `../OUTDOOR_BLV_ALL.md` "Flying AI findings" |
| Melee starts at a 307 edge gap; shrunk MM9 bodies must come closer; Dragon King, Sea Monsters and Colloidals hit and are hit from 70-212 further | `MM9_MONSTER_COLLISION_RE.md` "Combat" |
| No per-actor draw scale (DAT Scale bodies drawn at row size) | same, "Open" |
| Big monsters do not path down spiral stairs (MM9 uses rails) | `overnight/dungeons_ledger.md`, `SPIRAL_STAIR_PATHING.md` |
| Patrols not imported: KlusosPatrol, Yanmir's patrol (chases on sight), militia wandering, monk wander paths | dungeons ledger (Kluso's House, Yanmir's Fort, Dook's Castle, Lindisfarne) |
| GuardTrigger alarm relay unmatched (native AI chases on sight) | dungeons ledger (Kluso's House) |
| "A hostile guard with engagement type 0 never attacks; a hostile monster stops about 400 units short of a party in view with its targeting flag off" (engine notes, not changed) | dungeons ledger (Dook's Castle) |
| Basilisks running off, cower and fidget anims, monk work anims | dungeons ledger |
| Dragon King grounded boss script; monsters opening doors | `../STATUS.md` queue, `../ROADMAP.md` |
| Swimmers indoor only; outdoor ODM swimming not planned (outdoor maps become BLVs) | `MM9_WATER_SWIMMING_DESIGN.md` |
| Scripted cliff jumpers (Frosgard Yetis, Thjorgard bandits) are map scripts, not AI | `MM9_MONSTER_JUMP_RE.md` |
| Policy: do not compile generic MM9 AI from `BASEMELEE.inc`/`NPCBASE.inc`; map it onto shared profiles | `../../mm9/MM9_SCRIPTED_ACTOR_IMPORT_GOAL.md` "SCR Compilation Boundary" |
| Lua `onDamaged` cannot intercept damage; monster damage rolls use an unsaved `random_device` | `ACTOR_SCRIPTING_INVESTIGATION.md` "Limitations" |

Found in this review, not recorded elsewhere:

- MM9 civilian/guard reactions and OnFoundPlayer exist only in the outdoor runtime, while every MM9 map is moving to
  BLV. The BLV converters do not emit the flags. (Since resolved: both run indoors; OnFoundPlayer uses MM9's
  perception since 2026-11-06.)
- AlertRadius, Target Pref, WinceThreshold, AttackRange/Reach, LungeVelocity, Resurrect and Hostility Group are not
  imported (table above).
- The AI type mapping is a script-name heuristic. MM9's native `ShouldRunAway` (`BASE.inc:379`, `BASERUN.inc`) has not
  been reverse engineered.

## 4. Where an MM9 "AI profile" layer plugs in

### Recommended shape: native profile data on the skirmisher route

The `skirmisher` route is the proven path:

- **Generator:** `generate_mm9_monster_modifiers.py` already reads MONSTERS.txt and resolves each script's includes.
- **Catalogue:** `MonsterModifiers.{h,cpp}` parses the entry and checks its ranges.
- **Tactics:** `ActorBehaviorCatalog::applyMonsterModifiers` copies it into `ActorTacticsFacts`.
- **Per step:** `ActorBehaviorRuntime::applyTactics` copies the tactics into each actor's facts.
- **AI:** helpers gated by one boolean (`skirmishActive`, `GameplayActorAiSystem.cpp:3361`).

An MM9 profile is a superset of that: one `mm9_ai` modifier, or a few sibling modifiers, generated per row. MM6-MM8
monsters never see it.

| Profile field (from MM9) | Plug-in point | Churn |
| --- | --- | --- |
| Script family: melee (BaseMelee), crawl (BaseCrawl: no strafe or evade), range type 1 or 2, fly (BaseFly), swim | `ActorTacticsFacts` enum, branches beside the skirmish helpers in `AI_AttackOrPursue` / `AI_ActiveCurrentAction` | AI only |
| Strafe %, evade %, taunt | already `skirmisher` | none |
| Ranged type 1/2 timers and shot chance | new tactics fields plus per-actor timers in `ActorRuntimeFacts` / world actor state (like `skirmishSeconds`) | AI + both runtimes' state carry |
| Fly back-off and swoop | new skirmish-like phases. `status.climbAboveTarget` already steers a flyer's height | AI + state carry |
| AttackRange / AttackReach | per-actor melee range in place of the `ActorMeleeRange` constant: `meleeRangeForCombatTarget` and the world's `inMeleeRange` (`resolveOutdoorEngagementState`, indoor engagement) | AI + both runtimes |
| AlertRadius | per-actor sensing radius where `partyEngagementRange` is read (`resolveOutdoorTargetFacts`, `IndoorWorldRuntime.cpp:10351`) | both runtimes |
| LungeVelocity | skirmish lunge share or a one-off impulse | AI |
| Wince threshold / track time / always | generate the existing `stagger` modifier (threshold %, window, cooldown) | generator only |
| Target Pref | write the Pref column (letter map) | generator only |
| Flee rule | keep the AI type until `ShouldRunAway` is RE'd | none |
| Civilians and guards on BLVs | move `updateMm9ActorReactions` / found-player into shared code, or add an indoor twin; emit `mm9_civilian`/`mm9_guard` from the BLV converters | both runtimes + converter |
| Resurrect | native ability (a corpse query and raise) or a Lua command plus corpse query | new engine work |
| Boss scripts (Dragon, Njam, EndDemon, Dagrell leaps) | Lua behaviours (`perform`, timers, summon, blink, leave) | data + small API additions |

Two lower-churn refinements:

- Resolve the tactics pointer once per actor at spawn or load, instead of a hash lookup per step.
- Keep new per-actor phase state in the same `ActorRuntimeFacts` / `ActorStateUpdate` optional pattern the skirmish
  uses. Saving it is a save-version bump; the skirmish chose runtime-only.

### Cost per actor per tick

| Piece | Estimate |
| --- | --- |
| Profile branches in the AI (a few compares, one integer-hash roll per decision) | well under 0.1 µs per active actor per step; background actors skip combat entirely |
| Profile data in facts | already paid. `ActorTacticsFacts` is 108 bytes of the 960-byte record and is copied each step for monsters with tactics. A few more floats are noise |
| Per-actor sensing and melee radius | replaces constants; zero extra work |
| Ranged type 1 shot check (MM9's EstimateRangeAttackHit) | one extra line-of-sight query per shot check (every 1-2.5 s), not per step; reuse the outdoor pair cache |
| Lua extension (bosses, rare events) | event-driven; `onThink` at 0.5 s is about 2 calls per second per scripted actor plus a state serialisation each |
| For comparison | about 7-18 µs per active MM8 monster per step today (line of sight, targets, planner, collision); 157 µs for all 200 actors on Sturmford-as-BLV |

So an MM9 profile is not a performance risk. The levers that matter stay world-side:

- outdoor candidate vectors of size N per active actor;
- the double copy of 960-byte facts per step;
- indoor line of sight per step;
- path planning.

Separately, the one-sector BLV assumes actor-vs-actor sight inside a sector is always clear, which matters once MM9
monsters fight each other.
