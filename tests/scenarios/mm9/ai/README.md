# AI arenas

Test arenas for monster AI, from phase 0 of
[the MM9 monster AI plan](../../../../devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md).
An arena is a map with every placed actor removed, only the test's monsters spawned and the party placed. The monsters'
decisions are traced. The same arena file plays in the game window and runs headless as a scenario step.

| Arena | Scenario | What it shows |
| --- | --- | --- |
| `skirmisher.arena.yml` | `skirmisher.yml` | Two MM9 Skeletoids (9183, `skirmisher` modifier) on `thearena.blv`, their footwork on MM9's crawler loop (detection taunt, arrival timing). Monster 1's overrides make it always strafe and evade |
| `ranged.arena.yml` | `ranged.yml` | An MM9 Skull Thrower (9185) throwing at its Range.inc shot check, then closing in (phase 0's orbit/throttle flip is gone) |
| `crawler.arena.yml` | `crawler.yml` | An MM9 Grey Wolf (9114, BaseCrawl.inc): detection, ShouldRunAfter's arrival timing after the party jumps away, strikes from its own reach, no footwork |
| `archer.arena.yml` | `archer.yml` | An MM9 Bandit (9101, Range.inc type 1): a shot at its 1-2.5 s check on the run, strikes in reach (Att% 100), Range.inc's pursuit veto |
| `holder.arena.yml` | `holder.yml` | Range.inc type 2: an Evil Apprentice (9156, never chases, casts at its checks, strikes a party in its reach: in reach MM9 always strikes, native RE section 7.2.3) and a Bandit placed `ranged_type: 2` (strikes a party in reach, follows it out to 3 x its range) |
| `retarget.arena.yml` | `retarget.yml` | NewTargetCheck: a Grey Wolf holding a party ally (`party_ally`) is hit by the party (35 %), later by the ally (51.75 %); it kills the ally and taunts |
| `give_up.arena.yml` | `give_up.yml` | A Grey Wolf and an Evil Apprentice lose a party behind the gate after 8 s (the wolf waits, unable to reach it; the apprentice's `reposition` walks once to a spot that sees where the party vanished, does not see it there and holds); the apprentice, the party out of its range attack range, gives up after 30 s |
| `bird.arena.yml` | `bird.yml` | Phase 3 flier: a Bird (9093, BaseFly.inc) taunts on noticing the party, passes it 45 degrees off the line while it strikes, backs off upward, swoops back in; hit while backing off it rolls the 50/101 switch and backs off again |
| `banshee.arena.yml` | `banshee.yml` | Phase 3 flier with FlyRange: a Fright (9162, Banshee.scr) passes undead (its melee window; a pass is a blow), backs off 0.6 s without a swoop, and shoots at FlyRange's checks (61 in 101) |
| `lobber.arena.yml` | `lobber.yml` | Phase 3 turret: a Lobber (9086, lobber.scr) scans by turning until it sees the party, plays Aware, launches Lobber Pods (9084) up to five alive, then shoots (its lone spell, Poison as Poison Spray, on every shot: `Att%` 0); a pod killed lets it launch another |
| `jellyspore.arena.yml` | `jellyspore.yml` | Phase 3 swimmer on Isle of Ashes: a Jellyspore (9168, BaseSwim.inc) notices the party only once it is in the sea, fights it, runs at once when it steps onto the beach and never notices it on land |
| `patrol.arena.yml` | `patrol.yml` | Phase 4a wander: a Skeletoid (9183) walks a three-marker path with 1-2 s waits; a Grey Wolf (9114) wanders aimlessly on a 400 unit leash (stops at it, next walk heads home). The party steps up at 28 s (detection, an alert to the wolf) and leaves behind the gate at 31 s: 8 s later both lose it, and the path goes on to the marker after the one it was heading for (MM9 quirk) |
| `alarm.arena.yml` | `alarm.yml` | Phase 4a alerts: a Grey Wolf notices the party and alerts (its next alert after the stale g_nRandom, 57 s); a Skeletoid within its 1 229 takes the party from the alert, a second Skeletoid beyond it from the first one's (a cascade); a Bird ignores every alert (BaseFly.inc reads the alerter) |
| `flee.arena.yml` | `flee.yml` | Phase 4a flight (replaces phase 2's): hurt runners run to hiding places out of the party's sight in the pens, opening the pen doors, calling for help every 1.5 s and on arrival, then drop the party; the idle Bandit in the west pen joins on the wolf's help call; one Bandit (a model with a Cower clip) cowers instead (10 in 101); the non-runner fights on and winces |
| `necromancer.arena.yml` | `necromancer.yml` | Phase 4a resurrection: a slain Skeleton Warrior (placed `can_be_resurrected`) asks; an Evil Apprentice answers, casts ResurrectSpell and raises it at the clip's key; the warrior rises (its Resurrect clip) and fights again. A Skeleton Master killed with no resurrecter left raises itself |
| `door.arena.yml` | `door.yml` | Phase 4a doors: a Skeletoid patrolling out of the east pen walks into the pen's shut door (scene `ai_open`), opens both leaves, waits their 1.52 s opening and walks on |
| `civilians.arena.yml` | `civilians.yml` | Phase 4b townsfolk: a Commoner (9015) hit by the party runs to the Town Guard (9107) farther than 500 LT from the party (NPCBase.inc), calling for help on the way and on arrival; the help call about its friend the party turns the guard on the party; the party's second hit on the fleeing Commoner is ignored |
| `civilians_monster.arena.yml` | `civilians_monster.yml` | Phase 4b: a Horde Grunt (9129) set on Bjarni Thorvaldssen (9246) by a timed event (HateNPC.scr's AddEnemy NPC as `evt.SetMonsterRelation`); Bjarni runs to the northern guard (the one by the grunt is within 500 LT of it), whose help call makes that guard fight the grunt |
| `guards.arena.yml` | `guards.yml` | Phase 4b guards and monsters at war (generated `worlds/mm9/relations.yml`): a guard notices a Bandit and fights it, the Bandit the guard; a second guard joins from its fellow's alert, counts the party's hits and turns on the party at the third |
| `factions.arena.yml` | `factions.yml` | Phase 4b factions: a Grey Wolf and a Horde Grunt, friends by MM9's default, until a timed hate event (HateAll as The Arena's bouts write it) sets the wolf on the grunt, which takes its attacker (MM9's IsFriend asks both sides) |
| `dormant.arena.yml` | `dormant.yml` | Phase 4b dormant starts: two coffin mummies (MummyAwaken.scr) notice nothing; a trigger event wakes one, a hit the other (the hit itself lost); a hanging Flying Icky (9088) wakes when it sees the party during a hanging fidget or hears an alert, drops for its Launch clip and fights |
| `spawn.arena.yml` | `spawn.yml` | Phase 4b spawn-ins: a Greater Demon spawned with ScriptParams 1 hides, plays Spawn and Aware, then fights; a Lesser Demon so spawned, killed, spawns a Greater Demon at its corpse (it spawns in); a placed Lesser Demon spawns nothing |
| `dragon_king.arena.yml` | `dragon_king.yml` | Phase 5 boss on Dragon Stadium (`dragonstadium.blv`): the Dragon King (`worlds/mm9/behaviors/dragon_king.lua`) lands and taunts once woken, fire-bolts the party, switches to a Winged Mutant (he hates every AI) which fights him and dies, breathes and buffets with his wings at close range (a push), lets the party go beyond 1 800 LT |
| `njam.arena.yml` | `njam.yml` | Phase 5: Njam1000 hunts the party, a physical hit does nothing, spells bring him under his threshold and he vanishes; NjamChase waits for its Chase trigger; NjamFreeze never fights |
| `ebora.arena.yml` | `ebora.yml` | Phase 5: the Bathhouse's Ebora launches on sight and never fights; her concubines launch, then fight; three dead concubines send her off in a column of fire; the mine's Ebora is freed by a trigger and vanishes |
| `yanmir.arena.yml` | `yanmir.yml` | Phase 5: Yanmir hunts Ice Lobbercicles (his friends) at random, squashes them and wipes his shoe; physical hits do nothing; the party gets his 45 s chase limit |
| `summoner.arena.yml` | `summoner.yml` | Phase 5: a Lich Lab summoner's startup summons Specters at its points and replaces each one that dies, until it dies; an Isle of Ashes summoner's seven spawn triggers bring six Skeletoids (quirk) |
| `spell_conditions.arena.yml` | `spell_conditions.yml` | The `spell_conditions` modifier and MM9's spell choice ([MM9_SPELL_MAPPING.md](../../../../devdocs/mm9_rework/MM9_SPELL_MAPPING.md) sections 6, 6.6 and 6.7): a Lich (9207) casts Fear and leaves Afraid; an Oculus (9230) shoots its BlueLine and casts both its spells at its shot checks, Curse (as Dark Grasp) more often than Paralyze, which leaves Paralyzed on the (invulnerable) party for MM9's 10 game minutes (present 2 s after it lands, gone 26 s later), and strikes in reach; health stays full. Starts with `new_game_flow` so there is a party to strike |
| `move_zero.arena.yml` | `move_zero.yml` | MM9 never reads MONSTERS.txt's Move: a Magreeb (9277) and Forad Darre (9252), both Move 0, close in and strike; a Lobber (9086, no velocity, the one Stationary kind) never pursues; an Evil Apprentice placed on WizardSummoner.scr (Range type 2, as the Wizard's Lab places its six) holds and casts, never chases |
| `placement_script.arena.yml` | `placement_script.yml` | The placement's `ScriptName` wins (PROFILE.md "Placement scripts"): two Ghasts (9174, row script baserange.scr); the one placed as Lich Lab places it (KingKong.scr: caged until its trigger, `profile: {ranged: none}` as the converters write it) checks no shots and never casts, only strikes; the one on its row's script casts Fear at its shot checks |
| `sparks.arena.yml` | `sparks.yml` | A monster's Sparks volley (G3): an Initiate (9123, Expert) fires 5 sparks, a Winged Aberration (9161, Grandmaster) 9 (`fire_actor_projectile`, `assert: projectiles`) |
| `perception_placed_yaw.arena.yml` | `perception_placed_yaw.yml` | Perception on a real map (Ruined Temple, `clear_actors: false`): the Skeleton (actor 0) sees the party 700 units along its placement facing, in plain view. It failed while indoor map actors started at yaw 0 instead of their placement yaw ([MM9_AI_NATIVE_RE.md](../../../../devdocs/mm9_rework/monster_ai/MM9_AI_NATIVE_RE.md) section 5.4, item 1, fixed) |
| `perception_placed_sight.arena.yml` | `perception_placed_sight.yml` | The measurement after that fix (Drangheim Prison, `clear_actors: false`): the Nagate Elder (actor 39, placement yaw about 215 degrees, sight 1 536, hearing 369) notices the party 1 444 units along its facing (0.94 of its sight) on its first AI step |
| `perception_placed_sight_beyond.arena.yml` | `perception_placed_sight_beyond.yml` | Its companion: at 1 628 units (1.06 of its sight), in plain view, the Elder never notices the party itself and takes it only from the Nagate Hatchlings' alert |
| `sight_all_round.arena.yml` | `sight_all_round.yml` | The world's sight (`world.yml` `mm9Sight`, [plan](../../../../devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md) "Awareness of the party"): a Skeletoid with its back to the party 800 away (sight 600 x 1.5) notices it; one facing it 1 000 away does not; a mummy dormant until sighted, its back to the party, keeps MM9's half view and sleeps on |
| (no arena) | `background_townsfolk.yml` | Thjorgard City's tavern: three dwarves facing each other keep their facing while the party is far off (MM8's background StandOrBored turns an actor outside the thinking set to the party; one on MM9's loop no longer) |
| (no arena) | `turn_based_townsfolk.yml` | Thjorgard City's tavern: three dwarves facing each other keep their facing when turn-based mode starts and ends (MM8's turn engine turns every actor to the party; townsfolk on MM9's loop that are not hostile no longer) |
| `provoke.arena.yml` | `provoke.yml` | The world's provoke (`mm9Provoke` range and radius 128): a Skeletoid hit from 4 837 takes no target; one hit from 2 400, beyond its senses, runs at the party and strikes, its friend 100 beside it with it; a third 700 off, beyond the radius, is not provoked; a coffin mummy beside them never wakes |
| `reposition_lost_sight.arena.yml` | `reposition_lost_sight.yml` | The `reposition` modifier (an OpenYAMM addition, [MONSTER_MODIFIERS.md](../../../../devdocs/MONSTER_MODIFIERS.md)): an Evil Sorcerer (9157) posted at (600, -600) loses the party just inside the open east pen (doors 3-4 opened by the arena), where it stops as it vanishes behind the pen's west wall; 2 s later it asks for a spot within its 1 024 leash that sees where it last saw the party (`reposition` note `spot`), runs there, stops as it sees the party (`reposition_arrived` note `sight`) and casts at once |
| `reposition_rush.arena.yml` | `reposition_rush.yml` | The modifier's back-off: the party runs at an Evil Sorcerer and stops outside its reach; inside 640 units it backpedals 384 units (`back_off_rush` note `spot`, its BackpedalRun clip), then casts; it never strikes |
| `reposition_leash.arena.yml` | `reposition_leash.yml` | The modifier's leash: an Evil Sorcerer posted beside the east pen's doorway with a 250 unit leash (override `reposition_leash_radius`) loses the party just inside the pen; the spots that see where it vanished and keep 640 units from there all lie beyond the leash, so every search finds none (`reposition` note `none`), it never moves and gives the party up 8 s after losing it (with the default 1 024 leash it finds one 630 units from its post and sees the party) |
| `reposition_unchanged.arena.yml` | `reposition_unchanged.yml` | A Bandit placed `ranged_type: 2` (a holder by its placement, no modifier) keeps MM9's holder: it stands blind, gives the party up after 8 s (`give_up` note `lost`) and never repositions or backs off when the party later runs at it |
| `idle_fidget.arena.yml` | `idle_fidget.yml` | MM9's idle fidget ([ambient animation](../../../../devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md) §2.1): a Town Guard (9108) and a Commoner (9001) stand idle for 70 s, the party out of sight; each fidgets first 5-12 s after entering idle and again 5-12 s after each fidget ends, never two within 5 s, each time one of its model's clips (`fidget` note `idle`, its `variant` and its clip's `seconds`; the Commoner's `Fidget2` and `Fidget3` in the animation trace) |
| (no arena) | `talk_turn.yml` | Talking to an MM9 townsperson (§2.4) on Sturmford City itself: Bjarni Herjolfssen (actor 1, a passive placement) faces the party as the dialogue opens and turns back north at 180 degrees a second once it closes (45 degrees after a quarter second, home after about one) |
| `marker_stops.arena.yml` | `marker_stops.yml` | A path's marker stops (BaseWander.inc OnWanderAtMarkerNext; §4 item 6 of the ambient animation): a Town Guard (9108) walks a two-marker path; at marker 1 (`path_stops`: facing south, its own 4 s wait, Fidget2 looped) it turns to the marker's facing, waits the marker's time and plays its clip, at marker 0 the placement's 1-1.5 s wait |
| `townsfolk_chat.arena.yml` | `townsfolk_chat.yml` | Townsfolk chatting (§2.3, NPCBase.inc): a Commoner (9015) wandering aimlessly without a leash looks for someone 5-15 s after its wander starts, finds the Commoner (9022) standing in front of it, which accepts (`chat` note `hello`) while it walks over (`approach`); together (`begin`) they face each other and take turns at one Conv clip each, the wanderer first (`converse`, the clip's `variant` and `seconds`; `Talk` in the animation trace), for 10-30 s; it ends the chat (`end`), the other says `goodbye`, both turn away and the wanderer walks on; the one standing never looks itself |
| `set_target.arena.yml` | `set_target.yml` | `evt.SetActorTarget` (arena event `target: [monster, party \| monster]`): a caged Grey Wolf (dormant until a trigger) notices nothing until the 3 s event wakes it and sets it on the party; a Grey Wolf and a Horde Grunt, friends, until the event sets the wolf on the grunt (Dragon.scr's GetMe), which fights back |
| `lua_summon.arena.yml` | `lua_summon.yml` | `evt.SummonMonstersById`'s `mm9` placement (`lua_event`): a summoned Skeletoid walks its two-marker wander path, a summoned Greater Demon with `script_params = "1"` spawns in (hidden, Spawn, Aware), then fights |
| `mm8_summon_patrol_out01.arena.yml` | `mm8_summon_patrol_out01.yml` | MM6-MM8 outdoors: a peaceful Lizardman Peasant summoned with `patrol` walks out to its far waypoint |
| `mm8_melee_out01.arena.yml` | `mm8_melee_out01.yml` | MM6-MM8 regression anchor: an MM8 Regnan Bandit (10) on Dagger Wound (`out01.odm`, the outdoor runtime) pursues and strikes, with no MM9 footwork |
| `mm6_3d_out.arena.yml` | `mm6_3d_out.yml` | MM6-MM8 check of the shared 3D presentation: two MM6 barbarians (478), an archer (475) and a thief (637) on New Sorpigal's green (`oute3.odm`) close in on the party with MM6's AI; their models must not flicker ([MM9_ANIMATION_AUDIT.md](../../../../devdocs/mm9_rework/MM9_ANIMATION_AUDIT.md)) |

MM9 arenas need the MM9 review root `output/mm9_rework/assets_dev`, where MM9's maps are BLVs. `thearena.blv` is an
open, flat octagonal pit with its floor at z = 1 (about x, y within 1 380 and |x| + |y| within 1 900). The map's party
start (0, -3686) is in the entry corridor, behind a gate at about y = -1500 that blocks the monsters' sight, so the
arenas place the party inside at (0, -900) or (0, -1300). Its two pens are small rooms off the pit, x 1 556-1 966 (east)
and -1 966 to -1 556 (west), y within 205, each behind a shut double door (doors 3-4 east, 5-6 west) that MM9 monsters
open (`ai_open`, written by the converter since phase 4a).

The swimmer arena needs Isle of Ashes' root, the one with the sea's water volume. The party drops into the sea at
(-2900, 450), north-east of the spores' bay, and the scenario moves it onto the beach at (-2450, 900):

```sh
./build/game/openyamm --asset-root output/mm9_rework/isleofashes_blv_root --world mm9 \
  --headless-run-scenario tests/scenarios/mm9/ai/jellyspore.yml
./tools/run_game.sh --isolated ai_jellyspore --world mm9 --map isleofashes.blv \
  --assets "$PWD/output/mm9_rework/isleofashes_blv_root" \
  --set debug.ai_arena_path="$PWD/tests/scenarios/mm9/ai/jellyspore.arena.yml" --warmup 3 --seconds 20
```

## Running an arena

In the game window (the arena is applied once gameplay starts; the map must be the arena's):

```sh
./tools/run_game.sh --isolated ai_skirmisher --world mm9 --map thearena.blv \
  --assets "$PWD/output/mm9_rework/assets_dev" \
  --set debug.ai_arena_path="$PWD/tests/scenarios/mm9/ai/skirmisher.arena.yml" \
  --warmup 3 --seconds 30 --visible
```

Add `--set debug.screenshot_path=/abs/shot.png --set debug.screenshot_delay_seconds=8` for a capture. To judge motion,
add `--set debug.screenshot_burst_count=120 --set debug.screenshot_burst_interval_ms=40` for a burst of frames
(`shot_000.png`, `shot_001.png` ...; [Desktop game runs](../../../../tools/RUN_GAME.md)) and `--set
debug.time_scale=0.25` for slow motion. With an arena each frame's line in `game.log` carries the trace clock
(`Screenshot: saved ... (trace t=3.906)`), to match frames with trace lines. `--seconds 0`
keeps the window open to play. The game prints `AI arena: arena '<name>' ... trace log <absolute path>`. The log is
`ai_trace.log` in the run's own folder, next to `game.log`.

Headless (the scenario loads the arena's map itself). Never put `--set` before `--headless-run-scenario`:

```sh
./build/game/openyamm --asset-root output/mm9_rework/assets_dev --world mm9 \
  --headless-run-scenario tests/scenarios/mm9/ai/skirmisher.yml
./build/game/openyamm --headless-run-scenario tests/scenarios/mm9/ai/mm8_melee_out01.yml
./build/game/openyamm --headless-run-scenario tests/scenarios/mm9/ai/mm6_3d_out.yml
```

Headless, an arena poses its monsters' 3D models after every runtime step, as the window poses them every frame: a
model's missile leaves from its release socket (`WorldFxSystem::actorLaunchPoint`), so the arena plays as the window
does (the Dragon King's breath missed the Winged Mutant headless before, from the body's launch point). Scenarios
without an arena still launch from the body.

Debug console (`~`):

| Command | Effect |
| --- | --- |
| `arena load <file>` | Sets the arena up on the current map (which must be the arena's map) |
| `arena reload` | Sets the same arena up again: re-reads the file, hides every actor (the last run's monsters too), respawns, restarts the trace and the log |
| `arena trace on\|off` | Records or stops recording. Without an arena, `on` traces every visible actor of the map |
| `arena anim on\|off` | Traces the monsters' 3D model presentation too (`anim` lines; the arena's `trace_animation`) |
| `arena overlay on\|off` | The decision overlay above each traced actor (on by default) |
| `arena dump [lines]` | The last trace lines (20 by default) in the console |

## Arena file

```yaml
name: mm9_skirmisher           # defaults to the file name
world: mm9                     # for the reader; the run's --world decides
map: thearena.blv              # required: the map the arena plays on
asset_root: output/mm9_rework/assets_dev   # for the reader; the run's asset root decides
clear_actors: true             # hide every placed actor (default true)
party_awareness: world         # world (the world.yml actorAwareness, default) or mm9 (MM9's own perception)
trace: true                    # record decisions (default true)
trace_animation: false         # also trace the monsters' 3D models (anim lines, below); default false
seed: 1                        # spawn seed (positions are exact)
party:
  position: [0, -1600, 1]      # required
  yaw_degrees: 90              # or yaw (radians); pitch_degrees / pitch likewise
  invulnerable: true           # default true: monster blows do no harm (the Immortal cheat's immunity)
  members: 2                   # optional: dismiss members beyond this many
monsters:
  - monster_id: 9183
    position: [300, 400, 1]
    yaw_degrees: 270           # or yaw (radians); default: the world's own
    hostile: true              # default true
    group: 0
    overrides: {strafe_attack_chance: 1, evade_chance: 1}
  - monster_id: 9101
    position: [400, 700, 1]
    mm9_ai: {ranged_type: 2, runaway_chance: 1, hiding_places: [[0, 1800, 1]]}   # an MM9 placement
    hostile: false             # a townsperson or a guard: the party's friend
  - monster_id: 9183
    position: [-96, 1300, 1]
    party_ally: true           # a friendly summon (placed 96 units east of its position)
events:                        # timed, as a map's triggers (trace clock seconds)
  - {at: 4, wake: 0}           # evt.WakeActor on arena monster 0 (a dormant start)
  - {at: 8, relation: [9114, 9129, 2]}   # evt.SetMonsterRelation(from, to, level): MM9's HateAll / AddEnemy
  - {at: 2, trigger: [0, startup]}       # evt.TriggerActor: MM9's Trigger <object>, <message> to its behaviour
  - {at: 0, door: 3}                     # a map door opens, as a click on it
  - {at: 0, door: {id: 4, hold: true}}   # ... and stays open (MM9's CloseWaitTime would shut it 5 s later)
  - {at: 4, party_walk: {to: [1700, 100, 1], seconds: 2}}   # the party walks in a straight line to a point
```

`mm9_ai` is a scene actor's MM9 placement map (`sight`, `hearing`, `runaway_chance`, `ranged_type`, `hiding_places`
..., `devdocs/mm9_rework/monster_ai/PROFILE.md`), given to the spawned monster (indoors and outdoors). An arena's markers are a
placement's: `wander: path` with `path: [[x, y, z], ...]` (and `path_random`, and `path_stops: [{point, face, wait,
clip, loop}]` for its markers' facing in degrees, own wait and clip), `wander: aimless` with `wander_leash`,
`wander_wait: [min, max]` and `wander_time: [min, max]`, `hiding_places: [[x, y, z], ...]`, `can_be_resurrected`, as the
MM9 converters write them from a map's markers and objects; `dormant: {until, pose}` starts it dormant (as a row that
hangs does with any `mm9_ai`), `script_params: "1"` marks MM9's spawns (ScriptParams 1: spawn-ins, death spawns), and
`script` with `profile` gives a placement script's own loop as the converters write it (`profile: {ranged: none}`,
`{passive: true}`, `{archetype: skirmisher, skirmisher: {...}}`; PROFILE.md "Placement scripts").
`party_ally` summons the
monster as a party ally instead (its `hostile`, `group` and `mm9_ai` are not used), so an arena monster can be attacked
by someone besides the party.

An arena does not create a party: every arena scenario starts with `new_game_flow: {start_map: <the arena's map>}`, so
the monsters' blows and spells land (on an invulnerable party unless the arena says otherwise). Without that step there
is no party and nothing lands.

Unknown keys are errors. Removed actors are hidden the way an event's invisible bit hides them (`SetMonsterBit`), so
they leave without loot, experience or death events. Arena monsters are spawned through `spawnMonsters`, the same path
as scripted and console spawns, with no loot. They follow the map's actors in the actor list (on `thearena.blv` arena
monster k is actor 5 + k). The trace prints their actor indices; assertions name them by arena order
(`arena_monster`). What they spawn later (pods, a death spawn) follows them and is traced too (`actor_index`).

`events` run at the trace time `at`, after that AI step, in both the window and headless: `wake` (an arena monster
index) as a map trigger's `evt.WakeActor`, `relation: [from monster id, to monster id, level]` as
`evt.SetMonsterRelation` (one row toward another; 0 friendly, 1-4 hostile), `trigger: [arena monster, message]` as
`evt.TriggerActor` (its behaviour script's `onTrigger`, phase 5). They stand for the map scripts the tests
need: MM9's triggers (`awaken`), HateAll, HateNPC.scr. `door` opens a map door (its mechanism to Open, as a click on it; `{id, hold: true}` opens it again every step and
restarts its auto-close timer, so a converted MM9 door, which shuts `CloseWaitTime` seconds after opening, stays open)
and `party_walk` moves the party from where it stands at `at` to `to` over `seconds`, placed along the line every AI step
(`IGameplayWorldRuntime::teleportParty`: walls do not stop it, the party's velocity reads as a walk), so a test can hide
the party or run it at a monster in the window too.

`overrides` set an arena monster's AI facts each AI step, after its monster modifiers and behaviours. The fields are
`skirmish`, `strafe_attack_chance`, `evade_chance`, `evade_seconds`, `back_off_seconds`, `taunt_chance`,
`taunt_seconds`, `ranged_min_distance`, `ranged_max_distance`, `traverse_radians_per_second`,
`fire_tolerance_radians`, `lead_seconds`, `hold_post`, `post_leash_radius`, `ai_type`
(suicide/wimp/normal/aggressive), `no_flee`, and for a monster with the `reposition` modifier
`reposition_lost_sight_seconds`, `reposition_leash_radius`, `reposition_search_distance`,
`reposition_back_off_trigger_distance` and `reposition_back_off_distance`. A new profile field is one row in `overrideFields()` in
`game/gameplay/ActorAiTrace.cpp`.

## Decision trace

```
[ai] t=3.406 actor=5 monster=9183 "Skeletoid" decision=strafe_attack target=party detail="ability attack1 chance 0.80 roll 0.13"
[ai] t=4.102 actor=6 monster=9183 "Skeletoid" event=motion detail="pursuing"
```

`t` counts AI steps (1/128 s each) from the arena's start. `actor` is the map actor index.

- **Decisions** (`decision=`) come from `GameplayActorAiSystem`, which sets `ActorStateUpdate::decision` (an
  `ActorAiDecision`) where it takes one:
  - idle: `stand`, `fidget`, `wander`, `return_home`;
  - chase and waits: `pursue` (detail: direct, offset_short, offset_wide), `orbit`, `wait_cooldown`, `wait_no_shot`,
    `crowd_hold`;
  - attacks: `attack_melee`, `attack_ranged`, `attack_spell` (detail: the ability);
  - fleeing: `flee` (detail: fear, forced, ai_type) and `blind_wander`;
  - skirmisher footwork: `strafe_attack`, `evade`, `circle`, `back_off`, `taunt` and `throttle` (waits so that its
    attack is ready as it arrives; note `arrival` on an MM9 walker);
  - MM9 fliers and turrets (phase 3): `fly_pass` (note `left` or `right`), `back_off` (note `up`, `up not_ready`, `up
    hit`), `swoop` (note `left` or `right`), `melee_window` (a Banshee's pass, note `undead`), `shot_check` (FlyRange's
    roll, chance 0.60, note `skip`, `clear` or `blocked`; a Lobber's, chance 1 or 0.26), `taunt_detect` (note `always`
    for a flier, `aware` for a turret), `scan` (an idle turret turns, note `left` or `right`), `pod_launch`, and
    `hold` (note `aware` while the Lobber plays its Aware clip, `out_of_range`); a swimmer's `flee_decision` with note
    `land`;
  - MM9 walkers (phase 2): `detect` (it takes the target the world found; chance and roll of the 40 % taunt) or
    `taunt_detect` (it taunts), `retarget` (a hit by another attacker; note `switch`, `keep` or `no_target`, the target
    is the one it holds afterwards), `give_up` (note `chase_time`, `lost`, `dead`, `fled`), `taunt_kill`, `shot_check`
    (Range.inc's roll; note `clear` or `blocked`), `pursuit_veto`, `flee_decision` (note `hurt` or `unreachable`;
    the chance is the placement's runaway chance), `wince` (the native roll at a hit; note `yes` or `no`), `hold` (a
    ranged holder keeps its place) and `unreachable` (it waits, trying again every 1.5 s);
  - the MM9 layers (phase 4a, every MM9 archetype): `wander_wait` (it waits before its next walk; note `path` or
    `aimless`, `seconds`), `wander` (note `aimless`: an aimless walk, `seconds` long), `patrol` (it walks to `marker
    N`), `marker_reached` (`marker N`), `leash` (note `stop`: beyond its leash it stops; `home`: its next walk heads
    back); `send_alert` (it alerts its friends; `seconds` until the next alert, 0: none) and `call_help` (note `run` or
    `hide`); `alert` and `help` received (note `take`, `switch` or `keep` with the chance and roll, `ignored`; a help call
    while it holds a target, or a call naming the target it holds, is not traced); `hide` (note `run` to hiding place `marker N`, `arrived`), `cower` (note
    `start`, `end`) and `flee` (note `hide` or `run`, the flight's movement); `resurrect_ask` (a corpse asks; note
    `asked`: a resurrecter answered, `none`, `self` with the `seconds` until it raises itself), `resurrect_accept` (a
    resurrecter takes the corpse, `actor:N`, and starts `seconds` later), `resurrect` (note `cast`, `gone`), `raised`
    (the corpse rises: note `rise`, `self`, `wait` while an actor stands too close; `attack` when its Resurrect clip
    ends and it takes its old target); `open_door` (`marker` is the door id, `seconds` its opening time);
  - phase 4b: `flee_decision` note `hit` (a townsperson runs from its attacker), `hide` note `guard` (it runs to a town
    guard, the guard's actor index as `marker`; `arrived`), `flee` note `guard`; `turn_hostile` (a guard makes the party
    its enemy: note `hit 1`-`hit 3`, `help`, `alert`), `alert` note `monster` (a guard ignores a monster's alert);
    `wake` (a dormant start wakes: note `woken` by the world, `alert`, `help`, `sighted`), `fidget` note `hang` (a
    hanging fidget); `spawn_in` (note `hidden`, `spawn`, `aware`, `begin`) and `death_spawn` (`marker` the monster id);
  - phase 5 (boss behaviours, `worlds/mm9/behaviors/`): `script` — the loop carrying out a script's directive (note
    `target`: it holds the target the script named, `attack`: it starts the script's attack, `not_ready`: the attack
    was dropped) and, with free text, the script's own decisions (`self:trace`: e.g. `bolt party distance 2097`,
    `switch actor:2 first chance 80 roll 5`, `vanish hp 1100 below 1512`); `give_up` note `script` (the script
    dropped its target); `hold` note `script` (a script-driven turret waits for its script's attack);
  - the `reposition` modifier (an OpenYAMM addition): `reposition` (note `spot` with `at x y z`, the spot it runs to,
    `post` it walks back to its post, `none` it holds; `checks` the sight lines the world tested), `reposition_arrived`
    (note `sight` it saw its target on the way, `spot`, `post`, `leash`, `timeout`; `at` where it stopped) and
    `back_off_rush` (note `spot` with the point it backpedals to, `blocked` the world found no room, `leash` none
    inside its leash).
  - a townsperson's chats (NPCBase.inc, `devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md` section 2.3): `chat`,
    the target the other one, note `look` (its search starts; `seconds` the window), `refused` (the one it found is
    busy), `approach` (it walks to the one who accepted; `seconds` its give-up), `hello` (another asked it), `give_up`,
    `begin` (together; the asker's `seconds` the chat's length), `converse` (a Conv clip: `variant`, `seconds`), `end`
    (its chat time is over), `goodbye` (the other left); `end` and `goodbye` give the wait to its next search.

  `detail` holds the chance and roll where there was one. A strike's line shows the strafe roll that failed.
- **Events** (`event=`) are changes the world sees: `spawn`, `motion` (new motion state), `target` (the world's target
  pick: party, actor:N, none), `damaged` and `healed` (HP), `died`, `revived` (an MM9 corpse raised), `impact` (the
  attack applies: the blow lands, the missile leaves, the spell is cast; detail `<ability> at <seconds into the
  action>`). Target switches are events, because the world picks targets.
- **Animation** (`event=anim`, only with the arena's `trace_animation: true` or the console's `arena anim on`): the
  3D model as `WorldFxSystem::syncActorModels` poses it each frame, written when it changes:
  `detail="main=<clip> [layer=<clip>] rate=<r>[ layer_rate=<r>] speed=<s>[ blend=<b>]"`.
  - `main` is the clip of the whole body, or of the legs under a layer (a backpedal without its clip plays the gait
    forwards, as MM9's). `layer` is the upper-body clip (`upper_body_root`), MM9's `Top` track.
  - `rate` is clip seconds a second over the last 0.1 s (missing on a clip's first line), `layer_rate` the layer's
    (an attack swung over the gait plays at 1 when its blow lands at the clip's key); MM9 plays walk and run at the
    actor's speed over its `WalkVelocity`/`RunVelocity`. `speed` is the body's in units a second.
  - `blend` marks a crossfade this frame starts (its seconds); `blend=0.00` is a cut, the pose jumping.
  - A line is written when the main or layer clip changes, a crossfade starts, or a rate moves by more than a quarter.
  Headless, an arena poses the models after every runtime step (1/30 s); in the window every frame. Without
  `trace_animation` the presentation never calls the trace.

A step may carry three decisions: an MM9 walker's detection, retarget, give-up, wince or shot check
(`ActorStateUpdate::earlierDecision`) is traced first, then one of the shared layers (`layerDecision`: a call sent or
received, a flight's mode, a resurrection), then the step's own. A lasting decision (chase, stand, wait, flee) is
logged once until another decision or target comes between. An attack or footwork decision is logged every time. Later phases add kinds at the end of `ActorAiDecisionKind` and a row in
`DecisionNames` (`ActorAiTrace.cpp`); a `static_assert` there catches a missing name.

The trace lives in `GameApplication` and is bound to the active world runtime
(`IGameplayWorldRuntime::bindActorAiTrace`).
Both world runtimes apply its overrides after building the AI facts and feed it each AI step's facts and result. With
no arena nothing is bound, and the cost is one null check per AI step.

## Overlay

While an arena is active, each traced monster shows its last three decisions above its head, newest at the bottom (in
yellow), each as `#<actor> <t> <decision> <detail>`; a dead one shows `dead` at the bottom. `arena overlay off` hides
it.

## Scenario steps

- `ai_arena: {path, log}` sets the arena up, loading its map when another one or none is loaded. A relative path is
  read next to the scenario first. `log` writes a trace log file; by default there is none.
- `assert: {ai_trace: {actor_index | arena_monster, decision | event, target, detail, min_count, max_count,
  max_in_window, within_seconds, after, before, report}}` counts matching trace lines:
  - `decision` or `event` names the line, and `target` is `party` or `actor:N`;
  - `detail` keeps only lines whose detail contains it (`detail: up hit`, `detail: chance 0.60`);
  - `within_seconds` counts only the last seconds of the trace clock; `after` and `before` are absolute trace times;
  - without `min_count` or `max_count`, at least one line must match;
  - `max_in_window: {count, seconds}`: no span of that many trace seconds holds more than `count` matching lines (for
    flickering: `{event: anim, detail: "blend=", max_in_window: {count: 3, seconds: 0.3}}`);
  - `report: true` prints the matching lines.
- `ai_trace_dump: {actor_index | arena_monster, decisions_only, last}` prints the trace.
