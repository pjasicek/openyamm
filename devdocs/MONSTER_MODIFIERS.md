# Monster modifiers

Status (2026-10-23): implemented; `frenzy`, the charge's strike clip and its post leash added 2026-10-26. `skirmisher` added 2026-11-02 (MM9); `spell_conditions` added 2026-11-04 (the MM9
spell mapping, [MM9_SPELL_MAPPING.md](mm9_rework/MM9_SPELL_MAPPING.md)); `reposition` added 2026-11-05 (an OpenYAMM addition for
MM9's ranged holders, [MM9_MONSTER_AI_PLAN.md](mm9_rework/MM9_MONSTER_AI_PLAN.md) "Repositioning casters"); `special_attack_chance`, added the same day for
MM9's `ConcatAttk`, was removed again once the native RE showed MM9 never reads that column. A world
add-on file gives monsters a list of **modifiers** from a fixed engine catalogue: small, parameterised rules over the
shared monster AI and combat (true aim, never staggers, kites party, blink, charge, frenzy, skirmisher, spell
conditions, reposition). It follows the pattern of [shields.yml and relations.yml](ENERGY_SHIELDS_AND_RELATIONS.md): opt-in from data,
keyed by the world's own monster ids, so a monster no world lists (every MM6–MM8 monster) behaves, saves and renders
exactly as before. Hesper's turrets are the first users.

## Data: `worlds/<world>/modifiers.yml` (schema `openyamm.monsterModifiers.v1`)

```yaml
schema: openyamm.monsterModifiers.v1
monsters:
  10065: [never_staggers, {true_aim: {turn_degrees_per_second: 720, max_seconds: 3}}]   # a Ward Turret
  10050-10052: [never_staggers]                                                         # an id range
  10040: [{blink: {on_shield_break: true, cooldown_seconds: 8, max_height_change: 768}}]
```

- Read by `GameDataLoader::loadMonsterTable` beside `relations.yml` and `shields.yml` for every mounted world
  (`MonsterTable::modifiers()`, `findModifiers(id)`). Ids and ranges must lie in the world's `idRanges.monsters`.
- A modifier is a name, or `{name: {parameters}}`; parameters left out take their defaults.
- **Load errors name the file and line** and stop the load: an unknown modifier (the message lists the known ones), an
  unknown parameter (lists the modifier's parameters), a value outside its range or choices, a modifier listed twice for
  a monster, a monster listed twice (by id and by a range), an id outside the world's range, a blink without a trigger,
  `kites_party` with `min_distance >= max_distance`, a charge with `trigger_min_distance >= trigger_max_distance` or
  with both `use_melee: true` and a `damage` (or neither), a frenzy without a trigger.

## Catalogue

`game/tables/MonsterModifiers.{h,cpp}` (`monsterModifierCatalogue()`).

| Modifier | Parameter (default, range) | What it does |
|---|---|---|
| `true_aim` | `turn_degrees_per_second` (180, 1–3600); `max_seconds` (4, 0–60; 0: the whole flight); `then` (`straight` or `expire`) | The monster's projectiles (missiles and spell projectiles) home onto the target they were fired at, the party or an actor: each step they turn toward its current position by at most the turn rate and keep their speed. They still collide with everything on their way (terrain, BModels, decorations, actors, indoor faces), so only cover stops them. After `max_seconds`, or when the target dies or is removed, they fly straight on (`then: expire` ends them instead). |
| `never_staggers` | — | Hits never interrupt it: no hit reaction (the flinch and, outdoors, its knock-back). Stuns and paralysis from spells, skills and the EMP grenade still apply. |
| `indoor_meteor_shower` | — | It casts its Meteor Shower indoors too, each meteor from as high as the room's ceiling allows (`IndoorWorldRuntime::castIndoorMeteorShower`). The original game drops a monster's Meteor Shower indoors; a monster without the modifier never picks it there (`applyIndoorMeteorShowerRule` marks the spell uncastable before the AI), so it fights on with its other attacks. Outdoors every monster casts it as before. A Lua behaviour that casts Meteor Shower indoors needs the modifier too. |
| `kites_party` | `min_distance` (768, 0–20000); `max_distance` (2304, 1–20000) | The tactics ranged band (`ActorTacticsFacts::rangedMinDistance/MaxDistance`): commits to its ranged attack, backs off inside `min_distance`, closes in beyond `max_distance`, circles between shots. A monster whose `behaviors.yml` tactics set `ranged_band` may not also have it (the behaviour catalogue fails to load and names the monster). |
| `charge` | `trigger_min_distance` (384, 0–8192); `trigger_max_distance` (1280, 32–8192); `windup_seconds` (0.6, 0–5); `speed` (1400, 100–8000); `max_distance` (1536, 64–8192); `damage` (0, 0–10000; given without `use_melee`, it replaces the melee attack); `use_melee` (true); `knockback` (256, 0–2048); `cooldown_seconds` (8, 0–600); `stumble_seconds` (1.2, 0–10); `strike_seconds` (0, 0–5); `strike_impact_seconds` (0, 0–5); `effect` (`openyamm:fx/ember_impact`); `windup_sound` (`monster_charge_windup`); `windup_fallback_sound` (`roar 1`); `hit_sound` (`monster_charge_hit`); `hit_fallback_sound` (`swing with blunt weapon01`) | A readable dash onto the party. With the party within the trigger band (edge to edge), in sight, while it fights the party (hostile, aware of it, not party-controlled) and its cooldown ready, it winds up: it holds and faces the party, a flash (`effect`) and `windup_sound`. Then it dashes straight along the line fixed when the wind-up began, at `speed` for up to `max_distance`, following the floor and stopping at walls, ledges, decorations and other actors (the blink's spot checks, step by step). Reaching the party it hits once (its melee attack, or `damage`; the hit always lands, the defence is stepping aside) and throws the party back `knockback` units, with `hit_sound`; a miss (blocked, or the full distance run) ends in a stumble of `stumble_seconds`. With `strike_seconds` a hit is followed by a hold of that long playing the model's `charge_strike` script clip from `strike_impact_seconds` (the clip's blow), so the blow meets the contact. A post (placed `immobile`, tactics with a `post` leash) never charges a party beyond its leash, and its dash stops at the leash like at a wall. The cooldown runs from the end of the charge. |
| `frenzy` | `health_below` (0, 0–0.95; 0: off); `every_seconds` (0, 0–600; 0: never); `on_shield_break` (false); `windup_seconds` (0.8, 0–5); `seconds` (6, 0.5–60); `speed_multiplier` (1.4, 1–3); `attack_rate_multiplier` (1.5, 1–3); `spent_seconds` (0, 0–10); `cooldown_seconds` (20, 0–600); `glow_multiplier` (2, 1–5); `effect` (`openyamm:fx/ember_impact`); `sound` (`monster_frenzy`); `fallback_sound` (`roar 1`) | A haste power-up. Triggers (at least one): its health falls below `health_below` (once), every `every_seconds` roar to roar while it fights (with `health_below`, only while below it), its energy shield breaks. It roars for `windup_seconds` (holds and faces the party, `effect` and `sound` at its body; the model's `frenzy` script clip, else standing); a stun, paralysis or hit reaction in the roar cancels it (the trigger is used). Then for `seconds` it moves `speed_multiplier` faster, its attack recovery runs `attack_rate_multiplier` faster and its model's own emission is `glow_multiplier` brighter; then it holds `spent_seconds` (the `spent` clip, else standing): the punish window. `cooldown_seconds` runs from the end of one frenzy to the next. A frenzy and a charge never overlap. |
| `blink` | `on_hit_chance` (0, 0–1); `on_shield_break` (false); `every_seconds` (0, 0–600; 0: never); `cooldown_seconds` (6, 0–600); `min_distance` (384, 32–8192); `max_distance` (1024, 32–8192); `max_height_change` (256, 0–4096); `effect` (`openyamm:fx/arcane_pulse`); `sound` (`monster_blink`); `fallback_sound` (`30teleport03`) | A short teleport to a free spot it can see, on a damaging hit (by chance), when its energy shield breaks and/or periodically while it fights (a hit taken or a shot fired in the last 5 s), at most once per cooldown. Needs at least one trigger. The effect plays where it leaves and where it arrives, the sound at the arrival; it then faces the threat. |
| `skirmisher` | `strafe_attack_chance` (0.8, 0–1); `evade_chance` (0.4, 0–1); `evade_seconds` (2, 0.2–10); `back_off_seconds` (0.3, 0–3); `taunt_chance` (0.4, 0–1); `taunt_seconds` (0, 0–10; 0: never taunts) | MM9's BaseMelee footwork ([MM9 animation blending RE](mm9_rework/MM9_ACTOR_ANIMATION_BLENDING_RE.md)), real-time only, reading the target's velocity. It starts a chase only when its attack will be ready as it arrives, else waits facing the target. While it strikes it runs after a moving target (until within a quarter of its melee range) or steps after a standing one that leaves reach; its model swings over its gait (the upper-body layer). Its speed then follows MM9's SpeedThrottle: a 1.25x lunge beyond 0.9 of its reach before the blow lands, nearer 0.95x the pace of a target moving away within 45 degrees. Arriving running at a standing target, it may run a strafe attack: 45 degrees off the line to the target, half speed until the blow lands. After a strike it evades by `evade_chance` for `evade_seconds`: it only circles a target moving away (65 degrees off the line to it, re-aimed every 0.1–0.4 s), else backpedals at walking pace for the first half (5–35 degrees off straight back) and then circles; it ends early beyond 1280 units. A strafe attack without an evade backs off `back_off_seconds`. By `taunt_chance` it taunts when it first notices the party and after a back-off: it holds still facing the target for `taunt_seconds` while its model plays its `taunt` script clip. While evading it shoots or casts on the way but does not strike; a shot is also fired on the run at a target more than a second of running away. It faces its target throughout; a model with `backpedal`/`backpedal_run` script clips plays them when it moves backwards. MM9 lists it for every monster whose script builds on BaseMelee.inc, with the taunt length from its model (`tools/mm9_import_discovery/generate_mm9_monster_modifiers.py`). |
| `spell_conditions` | `spell1`, `spell2` (`none`; `afraid`, `asleep`, `cursed`, `weak`, `drunk`, `insane`, `paralyzed`, `poisoned_weak`, `poisoned_medium`, `poisoned_severe`, `diseased_weak`, `diseased_medium`, `diseased_severe`, `stoned`; at least one); `chance` (1, 0–1); `spell1_minutes`, `spell2_minutes` (0, 0–100 000: game minutes until that slot's condition wears off; 0 until cured) | A hit on a party member by its first or second spell (the row's Spell1/Spell2 columns) leaves that slot's condition: per struck member, by `chance`, then the member's save and immunities as against a special attack of that condition (luck plus mind resistance for afraid and paralyzed, personality for cursed, endurance for weak...), Protection from Magic and the ruleset's condition rules. It applies on a hit that does no damage and on an invulnerable party too (health is spared, conditions are not). Area spells leave it on every member they strike. It also makes **Paralyze** and **Fear** castable for that slot: projectiles that deal no damage (`isMonsterConditionSpellName`); a monster without a condition for them never casts them, as before (the MM6–MM8 rows that list Paralyze). A slot a ruleset replaced (MAW's generated spells) leaves none. A slot's minutes make its condition wear off once the game clock passes them (`Character::conditionExpireGameMinutes`, saved since version 157; resting and waiting count); a recast on a member who has it keeps the later end, and one without minutes (an MM6–MM8 source) lasts until cured. Without minutes a struck member keeps it until cured (rest clears Unconscious, Drunk, Fear, Asleep and Weak, not Paralyzed or Cursed). MM9 lists it for every row whose table casts Curse (`cursed`), Dark Grasp (`weak`), Fear (`afraid`) or Paralyze (`paralyzed`): 15 rows, with MM9's durations as the minutes (`SPELL.txt`'s `Duration (min)` for the cast's mastery, per point of its e1 or e2 skill: Paralyze 5-10, Curse 3-5, Fear 20-100, Dark Grasp 70-100) (`generate_mm9_monster_modifiers.py`; the Ghast's and Revenant's `concat` Fear is an ordinary ranged spell). |
| `missile_blast` | `attack1`, `attack2` (0, 0–4096: burst radius in our units; at least one) | Its first or second attack's missile bursts where it strikes (an actor, a wall, the floor): everyone whose body lies within the radius takes the attack (the projectile's area impact, `explosionRadius`), but its shooter, the shooter's friends and the actor the missile struck (hit once). No falloff, no sight test. Spells keep their own radius. MM9 lists it for the rows whose missiles have a `PROJECTILE.txt` `damageRadius` (feet x 12 LT x 2.56; `generate_mm9_monster_modifiers.py`, [MM9_PROJECTILES_RE.md](mm9_rework/MM9_PROJECTILES_RE.md)): the Dragon King's fire bolt (768) and breath (922), the Lizard-Orc Mage and Warrior's fire bolt (768), the Lesser and Greater Demon's and Njam's RedYellowThingy (307), the Trellborgs' RingOfFire (307). |
| `reposition` | `lost_sight_seconds` (2, 0.1–7); `leash_radius` (1024, 64–8192); `search_distance` (640, 64–4096); `candidates` (8, 1–16, whole); `max_sight_checks` (12, 1–32, whole); `retry_seconds` (2, 0.2–30); `back_off_trigger_distance` (640, 0–4096); `back_off_closing_speed` (200, 0–4000); `back_off_distance` (384, 32–2048); `back_off_cooldown_seconds` (5, 0–60) | An OpenYAMM addition for a monster that holds its place to shoot or cast; today it acts on MM9's ranged holder loop (a monster on any other AI keeps it as data only). **Lost sight:** its held target unseen for `lost_sight_seconds`, it asks the world for a spot within `leash_radius` of its post (its home position) that sees where it **last saw** the target (it does not know where the target went; a target only heard gives it nowhere to look): `candidates` spots on rings at half and all of `search_distance` around it (a seeded bearing, pulled inside the leash, nearest first), none within `back_off_trigger_distance` of that place, at most `max_sight_checks` sight lines per search. It runs to the first that passes and stops once it sees the target (its shot check then due at once); on the spot without the target in sight it searches no more for that place and its own perception takes over (MM9 drops the target after 8 s unseen); with no spot it walks back to its post or holds there, and the next search waits `retry_seconds`. **Rushed:** a target it sees, outside its reach, within `back_off_trigger_distance` edge to edge and closing at `back_off_closing_speed` or faster, makes it backpedal `back_off_distance` (straight away, else 30 or 60 degrees aside; inside the leash; room checked by the world) facing the target, as a skirmisher's back-off (its model's backpedal clip), then shoot or cast; the next back-off waits `back_off_cooldown_seconds`. In reach it strikes as before. Real time only. MM9 lists it for the Evil Sorcerer rows 156-158 (`generate_mm9_monster_modifiers.py`). |

Not modifiers, on purpose (the name in `modifiers.yml` is an error that says where the data lives):

- **`energy_immune`** stays in `shields.yml` (`monsters: {<id>: {energy_immune: true}}`): it is a rule of the shield hit
  resolution (`resolveMonsterShieldHit`) and needs the monster's shield profile, so moving it would split one rule over
  two files. The same goes for the shield `link`.
- **`stationary`** is the monster row's `Move` column (`Stationary`) in `monster_data`, which the AI already reads;
  Hesper's generator checks that its `Stationary` rule flag and the column agree.

### Choosing a turn rate

A homing shot turns on a circle of radius `speed / turn rate` (radians). Ener lasers fly 6 000 units a second: at
180 degrees a second the radius is about 1 900, so a shot fired at a party that steps aside or behind cover circles past
it; Hesper's turrets use 720 degrees a second (a radius of about 480). Slow missiles (fire bolts, arrows) home well at
the default.

## Behaviour

| Piece | Where |
|---|---|
| Catalogue, parsing, table | `game/tables/MonsterModifiers.{h,cpp}`; `MonsterTable::modifiers()` |
| Homing state and steering | `GameplayProjectileService::ProjectileHoming`, `attachHoming`, `steerVelocityToward`, `steerHomingProjectile`, `recordHomingEnd` / `recentHomingEnds` |
| A true_aim shot's homing | `trueAimProjectileHoming` (`GameplayActorModifiers.h`); the world runtimes' `attachTrueAim` after an actor's projectile request (`applyOutdoorActorProjectileRequest`, `applyIndoorActorProjectileRequest`), with the target from `ActorProjectileRequest::targetKind/targetActorIndex` |
| Steering each projectile step | `steerOutdoorHomingProjectile` / `steerIndoorHomingProjectile` before the step's collision query, so the predicted and the applied motion agree |
| never_staggers | `beginMapActorHitReaction` (both runtimes) |
| kites_party | `ActorBehaviorCatalog::applyMonsterModifiers` (from `GameApplication::reloadActorBehaviorCatalog`) |
| Blink decisions | `game/gameplay/GameplayActorModifiers.{h,cpp}`: triggers from `applyActorShieldHit` (every HP reduction and shield hit in both runtimes) and the actor's shots, cooldowns, candidate spots (`blinkCandidates`), presentation |
| Blink placement | `OutdoorWorldRuntime::blinkMapActorTo`, `IndoorWorldRuntime::blinkMapActorTo`; `blinkActor` (interface, scenarios) |
| Charge state machine | `GameplayActorModifiers::updateCharges` (wind-up, dash in steps of 24 units, recovery, cooldown), `applyChargeHolds` (the AI hold while charging), `chargeHit`, `chargeKnockbackImpulse`, the presentation |
| Frenzy | `GameplayActorModifiers::updateFrenzies` (triggers, roar, frenzy, spent hold; shield breaks from `observeHit`), `applyFrenzies` (the holds, the move speed and `ActorBehaviorFacts::attackRateMultiplier` before the AI), `moveSpeedMultiplier` (the indoor movement integration's own speed), `emissionMultiplier` → `GameplayRuntimeActorState::emissionMultiplier` → `ModelInstanceSystem::setEmissionMultiplier` (single skinned draws scale their emission; a boosted creature leaves the instanced batch), `scriptedClip` (the `frenzy`, `spent` and `charge_strike` roles into `GameplayRuntimeActorState::scriptedClip`); `frenzyActor` (interface, scenarios, console) |
| Charge in the worlds | `updateActorCharges` per fixed actor step after the AI (both runtimes; frenzies first), `chargeWorld` (sight, one step through `blinkMapActorTo` with `pBlockedByParty`, the events), `handleChargeEvent` (the melee impact through `GameplayCombatController::recordMonsterMeleeImpact`, the party's knock-back: a hop up through `requestSpecialJump` and its horizontal speed as a dash for the whole flight through `requestDash`, so the party lands `knockback` units back; fixed 2026-10-24, when a jump's horizontal speed lasted one frame and moved the party only a few dozen units); `chargeActor`, `chargeCounts` (interface, scenarios, console) |
| Spell conditions | `applyHitConditionModifiers` (`GameplayActorModifiers.h`) onto `GameplayCombatActorInfo::spell1Condition/spell2Condition/spellConditionChance` (both runtimes' combat actor info); `monsterHitCondition` and `rollMonsterHitCondition` in `GameplayCombatController.cpp` choose the condition and roll it (the old `shouldApplyMonsterSpecialAttack`), `applyMonsterSpecialAttack` saves and applies it; castability `monsterConditionSpellCastSupported` (`MonsterSpellSupport.h`) in `buildIndoorMapActorAiState` and `populateOutdoorActorStaticCombatFacts`; the projectile resolvers accept `isMonsterConditionSpellName`; no damage in `resolveProjectilePartyImpactDamage` (`isMonsterConditionSpellId`). Not saved (data only). |
| Skirmisher | `ActorBehaviorCatalog::applyMonsterModifiers` → `ActorTacticsFacts::skirmish`; the footwork in `GameplayActorAiSystem.cpp` (`AI_SkirmishBeforeEngage`, `AI_SkirmishStartAttack`, `AI_SkirmishAttackStep`, `AI_SkirmishAttackDone`, `AI_SkirmishEvade`, `AI_SkirmishTaunt`), its state in `ActorRuntimeFacts::skirmishPhase/skirmishSeconds/skirmishSide` (runtime only, not saved); the target's velocity in `ActorPartyFacts::velocityX/Y` (`ActorPartyVelocityTracker` in both runtimes) and `ActorTargetFacts::currentVelocityX/Y`; the taunt clip in the runtimes' actor presentation (`scriptedClip` `taunt`); a moving attacker's bump or wall stops the step, not the attack (`buildPostMovementBlock`); the backpedal clips in `WorldFxSystem` (`ActorModelBinding::backpedalClip/backpedalRunClip`) |
| Reposition | `ActorBehaviorCatalog::applyMonsterModifiers` → `ActorTacticsFacts::reposition`; the pure rules in `game/gameplay/ActorRepositionRules.h` (candidate spots, back-off spots, the rush, lost sight); the AI in `GameplayActorAiSystem.cpp` (`AI_Mm9Reposition`, from `AI_Mm9LayerHold`), its state in `ActorMm9State::reposition*` and `backOffWaitSeconds` (runtime only, not saved); the query `ActorMm9Request::reposition` (`ActorRepositionQuery`) and the answer `ActorMm9WorldFacts::repositionSerial/Found/Spot/SightChecks`, tested by `IndoorWorldRuntime::answerRepositionQuery` and `OutdoorWorldRuntime::answerRepositionQuery` with `checkMapActorSpot` (the blink's spot checks, also what `blinkMapActorTo` moves by) and the path map's `canReachDirectly`; the backpedal in the runtimes' actor presentation (`state.backpedalling`) |

**True aim.**

- The homing is attached when the shot spawns: every live projectile of that actor spawned during the request (a
  spell's several projectiles included), at its spawn speed. The party target point is the one the AI aims at (feet +
  96); an actor's is its body (feet + 70–75 % of its height).
- Each projectile step first turns the velocity (Rodrigues rotation toward the target, at most turn rate × step), then
  runs the unchanged collision and frame logic. Gravity still applies to missiles without NoGravity; the next step
  restores the speed. Trails and the 3D projectile models follow the position and velocity as before.
- The party's spells, event projectiles and every monster without the modifier never get a homing state, so their
  flight is the same code path with one extra `if`.
- The lead of a turret's tactics (`lead_seconds`) still aims the launch; the homing then steers to the current
  position.
- **Not saved:** a projectile in flight at a save loads without its homing and flies straight on. No save field, no
  `SaveVersion` change (still 95).

**Charge.**

- Phases: ready (the cooldown runs; the trigger is checked each fixed actor step), wind-up, dash, recovery (0.35 s after a
  hit, `stumble_seconds` after a miss), then ready with the cooldown. A charging actor holds through the AI
  (`ActorBehaviorFacts::holdActive`: it neither walks nor attacks; animations: standing in the wind-up, walking in the
  dash, the hit reaction in a stumble). Death, a stun or paralysis ends a charge where it is.
- The dash moves in steps of at most 24 units through the blink's spot check (`blinkMapActorTo` with a height change of
  at most 48 per step): a floor (no water or steep slope for walkers outdoors; walkable, in a sector, with headroom
  indoors), no blocking face or wall, decoration or other actor in its cylinder and a clear line from where it stands.
  The party's cylinder in the way is the contact; anything else ends the dash as a miss. A flyer keeps its height above
  the floor. The actor faces along the dash.
- The hit is one monster melee impact (`recordMonsterMeleeImpact`) with an attack bonus of 1000 (so the armour roll
  passes; the party's own evasion still applies): Attack1's dice, or Attack2's when Attack1 fires a missile and Attack2
  does not (a Lancer's lance thrust), or `damage` (physical). The knock-back is a short hop of the party
  (`requestSpecialJump`: 320 up, the horizontal speed that covers `knockback` under the party's gravity of 1280).
- Presentation: `effect` at its body and `windup_sound` (with `windup_fallback_sound`) at the wind-up, `hit_sound` (with
  `hit_fallback_sound`) at the hit. Drop `monster_charge_windup.wav` and `monster_charge_hit.wav` into a world's or the
  engine's audio to replace the fallbacks.
- Runtime only, like the blink: phases and cooldowns restart on every map load and after a load; no save field.
- The post leash (`ChargeActorFacts::leashRadius`, from `ActorBehaviorRuntime::postLeashRadius`) applies only to actors
  the map placed `immobile` whose tactics hold a post, as the tactics' own leash does.
- The strike clip (`chargeStrikeClip`, through `scriptedClip`) is presentation only: the hit is applied at the contact as
  before, and a behaviour script's own clip wins over it.

**Frenzy.**

- Phases: ready (cooldown, triggers), roar, frenzy, spent, then ready with the cooldown. The roar and the spent hold
  hold the actor through the AI (`ActorBehaviorFacts::holdActive`), as a charge does. A health trigger fires once, when
  the share first falls below `health_below`, and waits (for the cooldown, a charge or a hit reaction to end); a shield
  break waits up to 1 s. The period runs from roar to roar.
- The health and shield triggers need a hostile actor (not party-controlled) that can act; the periodic one also needs
  it to be aware of the party.
- Speed: the AI facts' `effectiveMoveSpeed` (its pursuit and wander intents) and, indoors, the movement integration's
  own speed; the charge's dash keeps its own speed. Attack rate: the attack cooldown ages `attack_rate_multiplier`
  times faster (`ageActorFrameTimers`).
- The glow scales the emission of the creature's own skinned materials; rigid attachments (held blades) draw through
  the static instancing path and keep their emission. Effect and sound: `queueFrenzyPresentation`.
- Runtime only: no save field.

**Blink.**

- Triggers: `on_hit_chance` rolls per damaging hit (a deterministic per-actor sequence); `on_shield_break`; and
  `every_seconds` while the actor fights. A request waits up to 1 s for a cooldown or a stun to end; an actor that is
  dying, stunned, paralysed, invisible or mid-attack does not blink.
- Candidates: 16 random spots on a ring of `min_distance`–`max_distance` around it (seeded per actor and blink), the
  ones sideways or away from the threat (the last attacker, or the target of its last shot) first. Spots that keep the
  threat in sight are tried first, then any free one. A failed blink retries after 0.75 s.
- **Outdoors** a spot needs: inside the map (and its `outdoorBounds`); the highest walkable floor (terrain or a BModel
  top) no more than `max_height_change` above the actor's own floor, and within that range of it; for walkers no water
  and no steep terrain slope; no blocking BModel face (`isOutdoorCylinderBlockedByFace`), decoration, other living actor
  or the party in its cylinder; a clear line of sight from where it stands (`hasClearOutdoorLineOfSight`). A flyer keeps
  its height above the floor.
- **Indoors**: the floor nearest its own height within `max_height_change` (walkable for walkers), headroom for its
  height (`sampleIndoorCeiling`), a sector (`findIndoorSectorForPoint`), no wall within its radius at three heights
  (`findIndoorWallContact`), no decoration, other actor or the party in its cylinder, a clear combat line of sight
  (`hasIndoorCombatLineOfSight`, sector-aware); the move state comes from the movement controller
  (`initializeStateFromEyePosition`), the collider is moved and its path is reset.
- The move keeps the actor's home (posts and leashes are unchanged); outdoors it updates the map delta position.
- Presentation: `effect` at both ends (`EventRuntimeState::worldEffectRequests`), `sound` at the arrival with
  `fallback_sound` while the placeholder has no file (`pendingSounds`). Drop `monster_blink.wav` into a world's or the
  engine's audio to replace the fallback.
- Runtime only: cooldowns restart on every map load and after a load; positions are saved as always.

**Reposition.**

- The AI picks the spots and when to look; the world only tests the spots it is given, the step after it asks, in
  order: a floor within 96 of the actor's own (walkable for walkers; outdoors no water or steep slope), headroom and a
  sector indoors, no wall, face, decoration, other body or the party in its cylinder, a clear line from where it stands
  (one sight line), the path map's straight walk to it, and for a lost-sight search a line from its eye there (MM9's
  `eye_below_top` when it has an MM9 profile) to the point the query names, where the actor last saw its target
  (`ActorRepositionQuery::target`, a second sight line); the world never reads where the target is now. It stops before a spot
  whose sight lines would pass `max_sight_checks`; the trace's `checks` says how many it tested.
- Cost: nothing while it sees its target; a search at most every `retry_seconds` while it does not (at the defaults at
  most 8 spots and 12 sight lines, each spot also two floor samples, a ceiling sample, a sector lookup, three wall
  contacts and an overlap scan of the actors, and one straight-walk test on the path map for a spot that passed);
  a back-off query at most every `back_off_cooldown_seconds` (five spots, one sight line each).
- Trace (`tests/scenarios/mm9/ai/README.md`): `reposition` (note `spot` with the point, `post`, `none`; `checks`),
  `reposition_arrived` (note `sight`, `spot`, `post`, `leash`, `timeout`; where it stopped), `back_off_rush` (note
  `spot` with the point, `blocked`, `leash`).
- A monster that is a ranged holder only by its placement (`ranged_type: 2`) has no modifier and keeps MM9's holder;
  a placement script that makes its row another archetype drops the behaviour (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md
  "Repositioning casters").
- Runtime only: no save field (a reposition under way restarts from its clock after a load).

## Hesper

- The design's `design/kreegan_world/data/make_monster_tables.py` maps rule flags to modifiers (`MODIFIER_RULES`):
  `TrueAim` → `true_aim` (720 degrees a second, 3 s), `NeverStaggers`/`NoStagger` → `never_staggers`, `KitesParty` →
  `kites_party` (1 024–3 072), `Blink` (and a "Blinks…" shield-break reaction) → `blink` (on a shield break, cooldown
  8 s, 512–1 280, height change 768), `Charges` → `charge` (from 384–1 280; per monster in `MODIFIER_OVERRIDES`: the Drudge
  Brute 10001 a quick short rush, the Lancers 10020–10022 a slow, long-telegraphed lance rush, the Glassback Bull 10082
  a heavy gallop from up to 1 536 with a knock-back of 512). It writes `data/monster_modifiers.yml` in the engine format and the "Engine
  modifiers" table of `MONSTERS.md`.
- `level_generation/projects/hesper_stage/stage.py` installs the staged monsters' rows as `worlds/hesper/modifiers.yml`
  (today the Starport Turret 10054 and Landfall's Ward Turret 10065 and Gate Bastion 10066: `true_aim` and
  `never_staggers`).
- Left to Lua behaviours (`devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`) or later engine work: phases (`Phases3`,
  `LinesAt75_50_25`, `LeavesAt50`, `FleesAt30`), summons (`SummonDrudges20s`, `SpawnsHatchlings`, `SpawnsDrudgeWaves`),
  telegraphed attacks (`TelegraphedBeam1.5s`, `TelegraphedSweep2s`, `LockOn3s` with `Strike…`/`Range…`), shields fed or
  refilled by objects (`ShieldFedByEggSacs3`, `ShieldRefilledByColumns3`, `PhaseShieldByConduits4`,
  `RotatingShieldArcs`, `InvulnerableWhileCouplingsLive`), `ArmouredFront`, `Turn40DegPerSecond` (a tactics traverse),
  `DigWindow40s`, `SlagSprayFlanks`, `Mines`, `FireWaves`, `FireTeam`, `Taunts`, `Collared`, `ConsoleLinked`,
  `CourtOfNobles`, `HonourTerms`, `GuardsGridControl` and the relation flags (`relations.yml`).

## Checks

- Unit tests (`tests/MonsterModifierTests.cpp`):
  `--test-case='*monster modifier*,*catalogue lists*,*homing*,*true aim*,*blink*,*kites_party*'`: parsing, defaults,
  ranges, every error with its line; the steering math (turn limit, speed, target straight behind); a projectile
  following a moving target, flying straight after its time, expiring, losing its target; homing given only to the
  firing actor's new projectiles; blink triggers, cooldowns, periodic blinks and the candidate ring; kites_party as a
  ranged band and its conflict.
- Runtime tests (`openyamm_runtime_tests`, `tests/MonsterModifierWorldTests.cpp`) on MM6 maps with a modifier set in a
  copy of the monster table: a homing Fire Bolt in New Sorpigal turns after a party gone behind a building and the
  building stops it (a straight one flies on); outdoor blink spots refused inside a building, behind it, onto another
  monster and outside the map, accepted on open ground; indoor blink spots in the Hive accepted only with a floor, a
  sector, headroom, no wall and a clear line, some refused.
- Spell conditions: unit tests `--test-case='*spell_conditions*,*Paralyze and Fear*'`
  (`tests/MonsterModifierTests.cpp`: parsing, defaults, errors, the combat info, castability and no damage;
  `tests/GameplayRuleRegressionTests.cpp`: each slot's condition on a spell hit, a hit without damage on an invulnerable
  party, a spell hit without the modifier, chance 0). Headless: `tests/scenarios/mm9/ai/spell_conditions.yml` (a
  Lich's Fear leaves Afraid; an Oculus casts both its spells, Curse more often than Paralyze, and its Paralyze leaves
  Paralyzed on the party).
- Charge: unit tests `--test-case='*charge*'` (parsing, defaults and errors; the state machine with a stub world:
  wind-up hold, dash, hit, cooldown, a wall, the longest dash, the band, sight, a stun; the melee or Lancer's thrust
  roll; the knock-back impulse); runtime tests in the MM6 Hive (`openyamm_runtime_tests --test-case='*charge*'`): a
  spawned charger holds through its wind-up, dashes along the floor onto the party and records one melee impact, and a
  charge at a party beyond a wall stops short of the wall and stumbles. Headless (Hesper stage):
  `level_generation/projects/hesper_out1/charge.yml`: a Glassback Bull charges the party on its own and hits it (the
  party hurt); a second bull's charge misses a party that steps aside in the wind-up and ends in a stumble. Captures:
  `level_generation/projects/hesper_out1/review/charge_20261023/` (`tour_charge.yml`, an input tour). Console:
  `actor charge <index|last>`. Scenario: `charge_actor: {actor_index}`, `assert: {charges: {started, hits, misses,
  min_started, min_hits, min_misses}}`. MM6–MM9 monsters have no charge, so their AI, saves and timing are unchanged
  (the hooks return at once without a charging monster). The leash and the strike clip: unit tests `*leash*`,
  `*strike*`.
- Frenzy: unit tests `--test-case='*frenzy*'` (parsing, defaults and errors; the health trigger once, the roar's hold
  and clip, the speed, attack rate and glow, the spent hold; the period below the health share; a stun in the roar; a
  shield break; no overlap with a charge); runtime tests in the MM6 Hive (`openyamm_runtime_tests
  --test-case='*frenzy*'`): a roar that holds and plays its clip, then twice the pursuit speed and the glow, then the
  spent clip; a frenzy that starts by itself below half health. Headless (Hesper stage):
  `level_generation/projects/hesper_out1/frenzy.yml` (a Harrower started by hand; a second one that loses its shield
  and half its health roars on its own). Console: `actor frenzy <index|last>`. Scenario: `frenzy_actor: {actor_index}`,
  `assert: {charges: {frenzies, min_frenzies}}`.
- Headless (Hesper stage): `level_generation/projects/hesper_out1/true_aim.yml`: a Starport Turret west of the crew
  ramp; its shot at the party, which steps behind the ramp, turns after it and ends against the ramp
  (`homing_ends: {hit: world}`), the party unhurt; a fresh turret's shot at the party strafing in the open turns onto it
  and hits it (`homing_ends: {hit: party}`).
- Console: `actor blink <index|last>` blinks an actor with the modifier now; `projectile actor <index|last> attack1
  at_party` fires the actor's shot at the party as its AI would (a true_aim shot homes).
- Captures: `level_generation/projects/hesper_out1/review/true_aim_20261023/` (the turret's laser bending onto a
  strafing party; the MM6 before/after set, within the run-to-run variance of the spawned creatures' motion).
- Scenario steps and checks added for this: `fire_actor_projectile: {actor_index, ability, damage}` (an AI shot at the
  party now), `blink_actor: {actor_index}`, `assert: {projectiles: {source_monster_id, min_count, max_count, homing,
  toward_party_within_degrees, report}}`, `assert: {homing_ends: {source_monster_id, hit, min_count, max_count,
  report}}`, `assert: {party_health: {full}}`.

- Reposition: unit tests `--test-case='*reposition*'` (`tests/Mm9ActorRulesTests.cpp`: candidate rings and the leash,
  back-off spots, the rush and lost-sight rules, the AI's query, walk, sight stop, post and leash ends, back-off and
  its end; `tests/MonsterModifierTests.cpp`: parsing, defaults, errors, tactics). Headless arenas
  `tests/scenarios/mm9/ai/reposition_lost_sight.yml`, `reposition_rush.yml`, `reposition_leash.yml`,
  `reposition_unchanged.yml` (captures in `output/mm9_rework/reposition/`).

## Not done

- A Lua `self:blink()` command and per-placement modifiers (a map's actor list cannot name modifiers yet).
- True aim of the party's own homing weapons (no such item yet), and of traps and events.
- A homing projectile's homing after loading a save (it flies straight).
- The stagger rules proper (a hit over a share of the health staggers, with a cooldown: work item 2); `never_staggers`
  only switches the existing hit reaction off.
