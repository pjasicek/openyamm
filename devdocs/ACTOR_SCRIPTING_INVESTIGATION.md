# Actor Scripting Investigation

Status (2026-10-10): investigated and implemented as a first version. Per-monster or per-actor Lua **behaviour
scripts** run on top of the shared monster AI. The boss mage (monster 307) is the demonstration.

## Question

MM6–MM8 monsters share one fixed AI: table stats plus a few AI types (Suicide, Wimp, Normal, Aggressive). The goal
was a way to script special monsters, bosses and encounters without forking that AI. A script should be able to drive
phases, animations, sounds, effects and special spells. One example: at 60% health a boss raises a shield that deflects
projectiles, so the party has to step inside it.

## Findings

### MM9 (LithTech, "JSL" scripts)

- Behaviour lives in 715 `.scr` scripts plus 87 `.inc` includes (`mm9/extracted/SCRIPTS/SCRIPTS/`). The language
  manual is `mm9/mm9_tools/script.txt`.
- **Attachment:** `MONSTERS.txt` gives each monster type a default script (`basemelee.scr`, `baserange.scr`,
  `NPCbase.scr`), and each placed object in a world DAT can override it with `ScriptName`/`ScriptParams`.
  `RunScript` swaps a live actor's script.
- **Events:** scripts register callbacks such as `OnDamage`, `OnDeath`, `OnFoundPlayer`, `OnTargetDead`,
  `OnPostSaveLoad` and `OnRudeExit`. Timers use `Wait slot, seconds, routine`. Objects message each other by name
  (`Trigger` and `AddTrigger`). `Exit 0` means "also run the engine default".
- **Inheritance:** overrides work by redefining a label, and `gosub X, 1` calls the parent version.
- **Bosses are scripts:**
  - `DRAGON.scr` is 1181 lines: sleep and wake, four attacks, timed mutant spawns, frame-keyed sounds.
  - `NJAM1000.scr` teleports away at a random health threshold.
  - `ENDDEMON.scr` opens doors on death.
- **The weakness:** all combat AI is untyped script includes, with no planner. It is fragile and slow, and bugs
  shipped (for example, `ENDDEMON.scr` writes armour class into hit points).

### OpenMW

- **Native AI with Lua on top:** the AI stays in C++ (`AiSequence` with `AiPackage`s). Lua scripts attach by object
  type, record or reference through `.omwscripts`, or dynamically when flagged `CUSTOM`. Local scripts get engine
  handlers (`onUpdate`, `onActive`, `onSave`/`onLoad`) and events.
- **Overriding behaviour:** behaviour is extended through overridable **interfaces** and handler chains where
  returning `false` cancels the default. The Morrowind rules (armour, hits, magic) live in Lua override scripts
  (`files/data-mw/`), separate from the engine.
- **Taking over:** `self:enableAI(false)` plus `self.controls` lets Lua drive an actor. The takeover is partial:
  combat engagement still runs, and the animation controller still fights scripted animations.
- **Saving:** script state is saved only as the plain table returned by `onSave`. Timers are saved by callback name,
  never as closures.
- **Pain point:** Lua runs on a worker thread and its world changes are queued, which causes a one-frame delay.
  That delay broke mwscript interaction and needed synchronous exceptions for animation. OpenYAMM runs Lua on the
  game thread, so this does not apply.

### Other engines

These come from general knowledge, not from code in this repository.

- **WoW server emulators (TrinityCore and others)** script bosses in C++/Lua on top of a generic creature AI. Fights
  are built from phases, an event scheduler and hooks such as damage taken and health below a percentage. Simple
  creatures use SmartAI: data rows of event → action → target.
- **Unreal (Behavior Trees, StateTree) and utility AI** are tools for authoring general AI. OpenYAMM already has a
  general AI that matches the original game, so they add little now.

### OpenYAMM before this work

- **Shared AI:** `GameplayActorAiSystem::updateActors(facts) -> updates` is stateless, and indoor and outdoor both
  use it.
- **Lua:** Lua ran only map events. The flat `evt.*` API had no actor queries, animation control or AI control.
- **Gaps:**
  - Animations were a fixed set of 8 states, and nothing could deflect a projectile.
  - The outdoor runtime never fires the `MonsterDamage` hook.
  - Monster damage rolls use an unsaved `random_device`.

## Decision

Native AI stays the base, and an **optional per-actor behaviour script** layers on top. This combines MM9's
attachment model, OpenMW's "return nothing to keep the default" overrides and TrinityCore's phase-based boss scripts.

- **Lua decides *when*; native code does the per-frame work.** A script switches on a ward; the projectile collision
  code enforces it. Scripts never run per projectile or per frame.
- **Event-driven:** handlers run on start, load, damage, health thresholds, timers, ward blocks, the end of a
  scripted action and death. An optional `onThink` runs at a low rate (default 0.5 s).
- **Facts in, commands out:**
  - The behaviour runtime reads actor facts and changes the AI's *input facts*: hold for a scripted action, spell
    override, AI type, no-flee.
  - It emits sounds, effects, status text and summons as requests.
  - The AI stays a pure function. Multiplayer can run the scripts on the authority and send only the results.
- **Saved state is data:** scripts keep state in `s` (booleans, numbers, strings, tables). It is serialised after
  every handler call and saved with the map. Timers are saved by name. A seeded per-actor random-number source
  (`self:random`) replaces `math.random`.
- **No general AI in Lua.** Movement, targeting, pathing and attack timing stay native.

## Implementation

| Piece | Where |
| --- | --- |
| Catalogue (YAML + script sources) | `game/gameplay/ActorBehaviorCatalog.{h,cpp}` |
| Runtime, Lua sandbox, `self` API, serialisation | `game/gameplay/ActorBehaviorRuntime.{h,cpp}` |
| AI hold directive (`ActorBehaviorFacts`, `AI_ScriptedHold`) | `game/gameplay/GameplayActorAiTypes.h`, `GameplayActorAiSystem.cpp` |
| Projectile wards (`ProjectileWardFacts`, `findProjectileWardBlock`) | `game/gameplay/GameplayProjectileService.{h,cpp}` |
| World hooks (step, AI facts, presentation, wards, snapshots) | `OutdoorWorldRuntime.cpp`, `IndoorWorldRuntime.cpp` |
| Save format (versions 86 and 87: behaviours, ward visuals) | `game/maps/SaveGame.cpp` |
| Scripted clip roles on 3D models (`script_clips`) | `game/fx/WorldFxSystem.{h,cpp}`, `actors.yml` |
| `evt.SetActorBehavior(actorIndex, id)` | `game/events/EventRuntime.cpp`, `ISceneEventContext` |
| Console: `actor behavior [<index> <id>]`, `actor damage <index\|last> <n>` | `game/app/GameApplication.cpp` |
| Library, API reference, boss script | `assets_dev/engine/behaviors/behavior.lua`, `bosses/necro_mage.lua` |
| Catalogues | `assets_dev/engine/behaviors/behaviors.yml`, `assets_dev/worlds/mm6/behaviors.yml` |
| Shield dome (fresnel shell renderer and shaders) | `game/render/ShieldDomeRenderer.{h,cpp}`, `game/shaders/vs/fs_shield_dome.sc` |
| Dome presentation (grow, fade, hit ripples) | `WorldFxSystem::syncShieldDomes` in `game/fx/WorldFxSystem.cpp` |
| Ward sparks effect | `openyamm:fx/shadow_ward` in `assets_dev/engine/effects/authored/library.yml` |
| Declarative tactics (turret traverse, ranged band, posts; see Tactics) | `ActorBehaviorCatalog`, `ActorBehaviorRuntime::applyTactics`, `GameplayActorAiSystem.cpp` |
| Tests | `tests/ActorBehaviorRuntimeTests.cpp`, `tests/GameplayActorAiSystemTests.cpp` (tactics) |
| MM9 bosses on the MM9 loops (`self:setMm9`, `target`, `targets`, `setTarget`, `attack`, `onTargetChanged`, `onAttackDone`, `onHit`, `onTrigger`; `evt.TriggerActor`) | `ActorBehaviorMm9Script` in `ActorBehaviorRuntime`, `ActorMm9ScriptFacts`; scripts in `assets_dev/worlds/mm9/behaviors/` (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md "Phase 5") |
| `evt.SetActorTarget(actorIndex, "party" \| targetActorIndex)` (map scripts) | `ISceneEventContext::setMapActorTarget` in both world runtimes; `EventRuntimeState::scriptedActorTargets`, `applyScriptedActorTargets` in `game/gameplay/ScriptedActorMoves.cpp` |
| `evt.SetActorImmobile(actorIndex, immobile)` (map scripts) | `ISceneEventContext::setMapActorImmobile` in both world runtimes (the placement's `immobile`, saved with the map) |
| `evt.SummonMonstersById{..., patrol, mm9}` (a summon's patrol and MM9 placement) | `game/events/EventRuntime.cpp` (`luaValueToYaml` + `parseMm9AiPlacementNode`), `GameplayMonsterSpawnRequest::patrolPoints` |

### Each actor step (1/128 s, indoor and outdoor)

1. `m_actorBehaviors.step(world, dt)` collects facts for scripted actors and newly appended ones through
   `IGameplayWorldRuntime::actorRuntimeState`. It attaches monster defaults, runs handlers and applies requests:
   sounds, effects and status text go to `EventRuntimeState`, summons to `summonHostileMonsterById`.
2. The world collects the AI facts. `applyAiFacts` then sets the hold directive and the spell, AI type and flee
   overrides on scripted actors.
3. `GameplayActorAiSystem::updateActors` runs unchanged except for one branch. An actor holding for a scripted action
   (and not mid-attack, stunned or dying) stands, faces its target and shows the fallback animation.
4. `observeAiResult` clears a one-shot `castNext` once the AI releases that spell.
5. Projectile frames receive `pWards`. A projectile crossing into a ward sphere from outside, before any other
   collision, is stopped at the ward surface with its impact effect. The block is reported to `onWardBlocked`.
   Projectiles that start inside pass, including the owner's own and the party's once it is inside.

### Attaching a behaviour

- **Monster default:** `worlds/<id>/behaviors.yml` maps `monsters: {307: bosses/necro_mage}`. Behaviours are declared
  in `engine/behaviors/behaviors.yml`, and worlds may add their own. The catalogue is re-read on every map load, so
  edited scripts take effect on the next map load.
- **A specific placed actor:** a map script calls `evt.SetActorBehavior(actorIndex, "bosses/necro_mage")`. It is
  idempotent, so on-load events can call it on every load.
- **Debug:** `actor behavior <index> <id>`. `actor behavior` lists the scripted actors.

### Tactics (declarative, no script)

Status (2026-10-22): implemented for Hesper's Landfall defenders; no MM6–MM9 data uses it.

A world's `behaviors.yml` may give monsters **tactics**: small, scriptless adjustments of the native AI, applied by
`ActorBehaviorRuntime::applyAiFacts` to every actor of that monster (`ActorTacticsFacts`). Without a `tactics` entry the
AI facts are untouched, so the native AI runs exactly as before; a catalogue without tactics costs one boolean test per
AI step.

```yaml
schema: openyamm.actorBehaviors.v1
tactics:
  10065: {traverse_degrees_per_second: 120, fire_within_degrees: 5, post: {}, lead_seconds: 0.25,   # a wall turret
          scan: {half_width_degrees: 55, degrees_per_second: 16, pause_seconds: [0.8, 2.6], pitch_degrees: 5,
                 hold_seconds: 3.5}}
  10067: {ranged_band: [768, 2304], post: {leash: 1536}}                         # a rifle guard
```

- **`traverse_degrees_per_second`** (with `fire_within_degrees`, default 6): the actor turns toward its target at this
  rate instead of snapping to it, keeps tracking it between attacks and through the wind-up, and starts an attack only
  once it is within the tolerance. It also keeps turning toward a target it cannot shoot (no line of sight). The turn
  eases out over its last traverse x 0.1 s, so it settles on a target instead of stopping dead. Such a monster gets no
  instant reaction turns from the world runtimes (toward an attacker on a hit or a stun, toward the party when turned
  hostile: `ActorBehaviorRuntime::turnsAtTraverseRate`); its AI turns it there at the traverse rate.
- **`lead_seconds`** (needs a traverse rate, 0–2): aims ahead of a moving target by its velocity times this: the facing,
  the published aim (the barrel) and the shot's target point (`ActorTacticsFacts::aimLead`). The velocity is
  estimated from the target's positions over about 0.3 s (`ActorBehaviorRuntime`), reset on a target change.
- **`scan`** (needs a traverse rate): a stationary turret's idle behaviour (`game/gameplay/ActorTurretScan.h`). With no
  target it sweeps its facing around its placement facing (`half_width_degrees` either side): every move eases in and
  out (smoothstep, peak `degrees_per_second`), ends at a random heading, alternates sides or now and then stops
  part-way, then pauses (`pause_seconds: [min, max]`, default 0.8–2.4); some moves also change the barrel's pitch
  within `pitch_degrees` (presentation). Each turret draws its own sequence (seeded by its actor id) and starts after its
  own delay, so neighbours never move in step. Having lost its target it holds the last aim (facing and barrel) for
  `hold_seconds` (default 3), then sets off after a 0.4 s beat from wherever it points, back into the sweep (beyond it,
  at up to half its traverse rate). A target it senses but does not fight yet (a friendly turret's drone beyond its
  hostility promotion range) is tracked at the traverse rate. The state is presentation-grade and not saved: after a
  load the scan restarts from the saved facing. The AI side is `AI_TacticIdleAim` (posts, Stationary actors, the
  friendly-near-party stand and background actors); without `scan` the post stands as before.
- **`ranged_band: [min, max]`** (edge distances): a chosen ranged attack always commits, instead of the native distance
  roll that walks ranged monsters in to melee; melee (attack 2 on its chance) only happens against an adjacent target.
  Between shots the actor backs off inside `min` (walking, still facing the target), closes in beyond `max` and circles
  the target in between (the native ranged orbit).
- **`shield_break: {react: fall_back, max_seconds}`** (default 8 s): while a hostile actor's energy shield is down
  after a break (`ActorStatusFacts::shieldDownSinceBreakSeconds`, filled by both world runtimes from
  `GameplayActorShields`), for at most `max_seconds`, it takes the native flee from its target
  (`forceFleeFromParty`): it backs off and comes back once the shield is up. Friendly actors (the Landfall guards) and
  actors without a target hold. See `devdocs/ENERGY_SHIELDS_AND_RELATIONS.md`; Hesper's Troopers and Ashrunner Gunners
  have it (`hesper_out1/shield_followups.yml`).
- A world's `modifiers.yml` monster modifier `kites_party: {min_distance, max_distance}` is the same ranged band, merged
  into the tactics when the catalogue loads (`ActorBehaviorCatalog::applyMonsterModifiers`); a monster may not have
  both. The other modifiers (true aim, never staggers, blink) are in [MONSTER_MODIFIERS.md](MONSTER_MODIFIERS.md).
- **`post: {leash}`**: applies only to actors the map places `immobile` (the same monster placed free keeps the native
  wander). The post may leave its spot to fight (unless the monster is Stationary) but never moves further than `leash`
  from home (0: unlimited); with no target it walks back, turns to its placement facing (at the traverse rate when it
  has one) and stands there with the native fidgets, never wandering, also as a background actor.

The facts it reads are filled by both world runtimes: `ActorMovementFacts::placedImmobile`, `hasHomeYaw` and
`homeYawRadians` from the map placement (spawned actors have none). Outdoors a moving actor turns to its movement; a
back-off sets `ActorMovementIntent::keepYawWhileMoving` so it keeps facing its target.

Presentation: an actor with tactics publishes the target it engages as `GameplayRuntimeActorState::aimTarget`
(presentation only, never saved). An `actors.yml` look block opts in with `target: combat`: the look nodes follow that
target at any distance and rest without one, `min_pitch_degrees` limits how far they turn down (default
`-max_pitch_degrees`), and `hold_clip: <clip>` holds that clip's first frame instead of the standing clip while the
actor tracks a target, and also while its tactics `scan` sweeps it (`GameplayRuntimeActorState::aimScanning`: the whole
actor turns, the look only eases the nodes' pitch to the scan's pitch over about 0.6 s), so the model's own idle clip
(the turrets' looping ±25° Standing scan) only plays for a monster without a tactics scan. Landfall's turrets pitch
`B_Barrel` −35…+30° (Ward) and −35…+35° (Bastion).

Code: `ActorTacticsFacts`, `ActorShieldBreakReaction` (`GameplayActorAiTypes.h`), `AI_TacticEngage`, `AI_HoldPost`,
`AI_TacticIdleAim`, `tacticFacingYaw` (`GameplayActorAiSystem.cpp`), the `tactics` parser (`ActorBehaviorCatalog.cpp`),
`applyTactics` and `updateTacticTurret` (`ActorBehaviorRuntime.cpp`), the scan (`ActorTurretScan.h`), `updateActorLook`
(`WorldFxSystem.cpp`). Tests: `--test-case='*tactic*,*turret*,*shield_break*'`. Headless check on Hesper:
`level_generation/projects/hesper_out1/landfall_defenders.yml`, with the scenario steps `damage_actor: {actor_index,
amount}` and the `actor_visible` checks `near`, `far`, `faces` and `has_aim_target`.

Captures of the turret behaviour: `level_generation/creatures/hes_turrets_claude/review/scan/`.

Not covered: patrol routes; a turret's choice of target is the native one (the nearest it senses each step, the party
without line of sight included), with no hysteresis between two targets at similar distances.

### Shield dome

A ward with a `visual` (on by default) draws a PoE-style force-field bubble, built the common way for shield
shaders: a generated sphere drawn additively, depth-tested without depth writes and with no culling, so the far wall
shows through. `fs_shield_dome` provides:

- a fresnel rim whose sharpness is set by `rim`;
- drifting procedural energy noise (`noise`);
- a glowing line where the shell meets the ground, with nothing drawn below it;
- a dimmer far wall;
- up to four hit ripples: a flash plus an expanding ring from each blocked projectile's impact point.

The ripples come from `ActorBehaviorRuntime::wardDisplays()`, which lists the active wards and their recent blocks.
Hit points are presentation-only and never saved. `WorldFxSystem` grows a dome in over 0.35 s with a brief flare,
then swells and fades it over 0.45 s when the ward lapses or its owner dies.

The ground glow is an analytic stand-in for the usual depth-buffer intersection glow. Scene depth is not sampleable
on the default or Android render paths, so this works everywhere.

Energy shields over creatures (a shell following the skinned model, not a dome) and per-world monster relations are
separate: [ENERGY_SHIELDS_AND_RELATIONS.md](ENERGY_SHIELDS_AND_RELATIONS.md). Their shader shares the dome's noise
(`game/shaders/shield_common.sh`).

The renderer has no gameplay coupling: it takes a list of `ShieldDomeDraw` (centre, radius, ground height, colour,
strength, rim, noise, hits). Other shells can reuse it, such as a party Shield or Protection from Magic visual, or
MM9's spell armour.

### Script API

The full handler and command list is at the top of `assets_dev/engine/behaviors/behavior.lua`. A script returns
`Behavior.define{...}`, which rejects misspelt handler names. Handlers receive `(self, s, ...)`.

- **Handlers:**
  - `onStart`, `onLoad`, `onThink` (`think_interval`), `onDamaged(amount)`
  - `onHealthBelow = {[0.6] = fn}`: each fires once, highest first
  - `onTimer` (a table keyed by timer name, or a function), `onWardBlocked`, `onWardExpired`, `onPerformDone`,
    `onDeath`
- **Queries:** `hp`, `maxHp`, `hpFraction`, `position`, `distanceToParty`, `isHostile`, `monsterId`, `age`,
  `random`.
- **Commands:**
  - `say`, `playSound`, `effect(id, scale, heightFraction, forward)` (forward: along the actor's facing, a dragon's
    snout), `effectAt(id, x, y, z, scale)` at a world point (a summoner's spawn location)
  - `perform{clip, seconds, fallback, sound, effect}`: holds the native AI and plays the clip role on 3D models, or
    the fallback state on sprites
  - `addWard{id, radius, seconds, effect, visual = {color = {r, g, b}, intensity, rim, noise} | false}`,
    `removeWard`/`hasWard`
  - `startTimer`/`stopTimer`/`hasTimer`
  - `castNext{spell, skill, mastery}`, `setSpell{..., chance}`/`clearSpell`: monster projectile spells, by name or
    id
  - `setAiType`, `setNoFlee`, `summon(monsterId, count, radius)` around the actor, `summonAt(monsterId, x, y, z,
    count, spread)` around a point (indoors and outdoors)

### Map script orders (2026-11-06)

Two `evt.*` calls of map scripts (not behaviour scripts) for MM9's spawn and cage scripts (devdocs/mm9_rework/
scr_audit/monsters_ai.md gaps 6 and 7):

- **`evt.SetActorTarget(actorIndex, "party" | targetActorIndex)`**: the living map actor goes for the party or the
  other living actor at once (MM9's `GetPlayer`/`GetMe`: SpawnCreature.scr's spawns, DP_CageMonster.scr's cage Terrors
  after their door opens, Dragon.scr's Winged Mutants on the Dragon King). It wakes a dormant start; a party target
  makes it hostile to the party; an MM9 monster's loop then holds the target from its next AI step as a behaviour
  script's `self:setTarget` does (whatever their relation; the order is runtime only, taken within a step of an
  active actor). A monster without the MM9 loop (MM6-MM8 AI) takes only the party: hostile and aware of it; an actor
  target returns false for it. Outdoors an MM9 loop's held actor target is offered by relation only (MM9 maps are
  BLVs). Returns whether the actor took the order. Arena event: `target: [arena monster, party | arena monster]`
  (`tests/scenarios/mm9/ai/set_target.yml`).
- **`evt.SetActorImmobile(actorIndex, immobile)`** (2026-11-08): the actor's `immobile` placement, saved with the
  map. The MM9 converters place still an actor MM9 gives no wander (its script decides when it moves), and `immobile`
  also stops all AI movement, pursuit included; MM9's BaseInit or AddEnemy then lets it fight as a monster, so the
  map's Lua lifts it at that moment: Thronheim City's Desert Terror and Guard1 at the breakout, Arslegard's and the
  Thousand Terrors' Njam, Frosgard City's Forad Darre, Drangheim Prison's gate guards at the alarm, Lindisfarne's
  monks once hostile. A row that never moves (Stationary, MM8's Immobile kind) stays still. Returns whether there is
  such an actor.
- **`evt.SetActorRoutine(actorIndex[, name])`** (2026-11-10): the MM9 routine (scene `mm9_ai.routines`) the actor
  runs while it holds no target, from its first step; no name: none (it wanders by its placement). Without a call it
  runs its `default`. Runtime only (`EventRuntimeState::actorRoutines`): a map script sets it again on load (a
  ceremony from the hour). **`evt.AttachActorItem(actorIndex, model, node)`**, **`evt.DetachActorItem(actorIndex[,
  node])`**: MM9's AttachProp and DetachProp on the actor's held items (scene `held_items`, saved with the map). See
  [MM9 ambient animation](mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md) section 4, items 9 and 10.
- **Orders run wherever the actor is** (2026-11-08): an indoor actor with a pending `evt.MoveActorTo` walk or
  `evt.SetActorTarget` is picked for the full AI step (first, before the actors nearest the party), so it carries the
  order out though it neither sees the party nor shares its sector. Before, such an actor kept the order pending and
  stood still: the caged Desert Terror never walked to its wall, and the guards sent for it never left their post
  (`IndoorWorldRuntime::selectIndoorActiveActors`).
- **A walk's route ends near its point; a stuck walk gives up** (2026-11-11). A walker arrives once its centre is within
  its radius + 32 of the point (`ScriptedActorMoveArrivalDistance`), so indoors its route may end anywhere that close
  less a waypoint's reach (`ActorMovementFacts::scriptedMoveArrivalDistance` -> `ActorMovementIntent::
  targetArrivalDistance` -> `PathPlanRequest::goalDistance`). Before, the planner had to reach the point itself:
  Thjorad Mine's MMarker2 lies 21 from the corridor's end wall, inside Hjarrand's 42, so with the slag extractor's hatch
  open across the corridor the only route found was an 87-waypoint detour south and up the west ramp, dropping onto the
  point from a ledge (the open leaf leaves the hall north of it free: the 17-waypoint route goes round its end). A route
  held near a waypoint whose successor is out of reach is dropped after 2 s (`ActorPathRuntime`,
  `WaypointBlockedSeconds`) and planned again from where the actor stands; before, it was kept for ever. A walker that
  walks for 10 s without getting 32 from one spot (`ScriptedActorMoveGiveUpSeconds`; not while it attacks, is held by
  a status, a script hold or turn-based play) gives up: its move ends without its arrival event, `evt.IsActorMoving`
  turns false and the log says where it stopped. Test: `tests/scenarios/mm9/hjarrand_walks_past_open_hatch.yml`.
- **`evt.SummonMonstersById{..., patrol = {{x, y, z}, ...}, mm9 = {...}}`**: every summoned monster gets a scene
  actor's `patrol` (it walks the waypoints in turn while nothing is in reach; outdoors saved from save version 160)
  and `mm9_ai` placement, read by the scene's own parser (`parseMm9AiPlacementNode`, so its keys and errors are the
  scene's: an unknown key is a Lua error): a Spawner's `DefaultSpawn` wander path (`wander = "path", path = {...}`),
  a placement script and ScriptParams (`script_params = "1"`: a Greater Demon's spawn-in, hidden, Spawn and Aware
  clips), sight, hearing, dormant start and the rest (`tests/scenarios/mm9/ai/lua_summon.yml`,
  `mm8_summon_patrol_out01.yml`). `effect = "mm9:fireblue"` (with `effectScale`) plays that world effect where each
  summoned monster stands as it appears: MM9's `DoClientFX` on a spawned creature (an Imp gate's blue fire, a Greater
  Demon's spawn-in; devdocs/mm9_rework/scr_audit/client_fx.md).

Scenarios run a map script's code with `lua_event: {source}` (tests/scenarios/README.md).

### Sandbox and errors

- Available libraries: base, table, string, math and coroutine. `load`, `loadfile`, `dofile`, `require`,
  `math.random` and `math.randomseed` are removed.
- Each behaviour module gets its own globals table that falls back to the shared one.
- A Lua error, or a value in `s` that cannot be serialised, stops that one script, logs the error and clears its
  directives. The actor keeps its native AI. A script that is missing or fails to load on restore is stopped the same
  way, so saved wards cannot linger.

### The boss mage (monster 307)

- **Phase 1:** never flees.
- **Phase 2, at 60% health:**
  - Plays the `cast_ward` clip (mapped to `Cast` in `actors.yml`) and raises a violet 400-unit shadow ward for 20 s.
  - The ward shows as a shield dome with `openyamm:fx/shadow_ward` sparks, and the spell switches to Shrapmetal.
  - It taunts when missiles break on the ward, and the ward returns 10 s after lapsing.
- **Phase 3, at 30% health:** summons two Ghost A and casts a grandmaster Toxic Cloud next.

Try it on an MM6 outdoor map:

```
actor spawn 307 1
actor damage last 60          # phase 2: ward up
actor spawn 202 3 friendly    # friendly archers: their arrows break on the ward
actor behavior                # list scripted actors, their health, wards and timers
```

Verified on 2026-10-10:
- In New Sorpigal (`oute3.odm`): the phase-2 message, the Cast clip, the ward pulse, and the friendly archers' arrows
  blocked with the taunt.
- In Agar's Laboratory (`6d19.blv`): attach and death detection.
- Unit tests: `./build/tests/openyamm_unit_tests --test-case='*ehavior*,*ward*,*scripted action*'`.

## Scheduled scenes and greetings (MM9, 2026-11-06)

Map Lua over the existing calls, no new actor API: the Temple of Honk's leader paces between his platform markers
with `evt.MoveActorTo` during the ceremony (6:15-6:45 and 18:15-18:45, HonkLeader.scr; the followers' walk to the
pulpit is not carried); a placed MM9 NPC with a greeting voice gets its click event (53000 + DAT index) from the
shared converter, which plays the voice and opens its RUDE dialogue (`evt.OpenMm9Rude` keeps the clicked actor
through the hook context). The Guberland Players are not placed: their show is the voices only
([Ambient sounds](AMBIENT_SOUNDS.md) "Scripted voices and scenes").

## Limitations and next steps

- **Dome depth intersection:** the dome's ground glow assumes a flat floor at the actor's feet. On slopes the cut
  is flat, and walls the shell passes through get no glow. A true intersection glow needs a scene depth copy.
- **Wards stop projectiles only:** direct, area and melee damage still apply. Line-of-sight spells would need their
  own check.
- **Health is observed, not intercepted:** `onDamaged` cannot change or cancel damage. That needs a shared damage
  hook. The outdoor runtime still never fires the map `MonsterDamage` hook, which is a separate existing gap.
- **Spell overrides:** limited to monster projectile spells. Presentation keeps the native spell's cast colour.
- **Map files:** there is no per-placement field in map scene files yet. Use `evt.SetActorBehavior` in the map's
  on-load script.
- **Determinism:** script randomness is seeded and saved, but monster damage rolls still use `random_device`. That has
  to move to saved state before multiplayer or replays.
- **Cutscenes:** camera and letterbox sequences are not covered. A boss can trigger existing movies through map
  events.
- **MM9:** bosses such as `DRAGON.scr` could be ported by hand onto this layer, matching the "behaviour profiles on top
  of shared AI" direction in `MM9_SCRIPTED_ACTOR_IMPORT_GOAL.md`.
- **Simple tweaks:** if many small monster tweaks accumulate, a declarative event → action table (like SmartAI) could
  compile onto the same runtime.
