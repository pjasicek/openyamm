# MM9 SCR audit, part 2 of 4: monsters, AI, special monsters, bosses, spawners

Date: 2026-11-06. Audit only: no engine, converter, data or map change was made for it. The monster AI, its
converter rules (`tools/mm9_import_discovery/mm9_ai_placement.py`, `generate_mm9_monster_modifiers.py`,
`generate_mm9_monster_tables.py`) and `assets_dev/worlds/mm9/{behaviors.yml,behaviors/*.lua,modifiers.yml}` belong to
the openyamm-19 session; map Lua belongs to the map session (the `mm9r_*` converters). Each gap below names its owner.

Scope: the 48 scripts of `cat_monsters_ai.json` and the AI/monster includes of `cat_includes.json`, plus every spawner
object, every monster death or damage trigger and every boss phase in the 45 shipped DATs. Scripts are cited as
`FILE:line` in `mm9/extracted/SCRIPTS/SCRIPTS/` (the file's own line numbers). The base scripts' state machines are
already documented line by line in [MM9_AI_DATA_AND_SCRIPTS.md](../monster_ai/MM9_AI_DATA_AND_SCRIPTS.md) §3-4 and are
cited from there rather than repeated.

## Method and what was verified

- **Installed data** (`assets_dev/worlds/mm9/maps/*.scene.yml`, written 2026-11-06 12:12): 44 maps, all BLVs; 2 123
  actors, 2 120 with an `mm9_ai` record (the other three are script stand-ins: Dark Passageway's Njam, Ta'Sar's crate
  Dagrell, Thronheim's late guard); 602 with a placement script, 432 `profile` overrides in 38 maps (passive 271,
  ranged 103, archetype 49, skirmisher 43, guard_refuge 14, throttle 2), 147 `dormant`, 94 hostility gates, 9 `summon`,
  13 `boss`, 323 wanderers (144 on paths). No installed scene has `path_stops` or `draw_scale` yet, and the animals'
  wander (M20) and 1000 Terrors' M24 Lua are not in assets_dev: they arrive with the final rebuild (R2), which was
  converting into `output/mm9_rework/assets_dev` during this audit (1000 Terrors, Anskram Keep and Hall of the Gods
  already rewritten at 16:31-16:35).
- **Row profiles** (`modifiers.yml` `mm9_ai`): spot-checked the family hooks of every script below (Banshee
  `melee_window_seconds`, Icky `dormant_until`, Dagrell `throttle: false`, pods `always_evade`, Lobbers `pod_launch`,
  demons `death_spawn`/`spawn_in`, `boss` on 9206/9212, guards, swimmers, fliers, holders and `reposition`).
- **DAT objects**: every placed object of the 48 scripts with its `ScriptParams`, every `Spawner` and its
  `DefaultSpawn`, every `DeathTriggerTarget`/`DamageTriggerTarget` (extracted from
  `assets_editor_dev/worlds/mm9/maps/*.raw_objects.yml`), checked against each map's installed Lua.
- **Headless arenas** (binary copied from `build/game/openyamm` of 16:25, review root `output/mm9_rework/assets_dev`,
  Isle root for `jellyspore`), each log read: `summoner`, `spawn`, `lobber`, `banshee`, `dormant`, `njam`, `ebora`,
  `yanmir`, `dragon_king`, `civilians`, `guards`, `bird`, `placement_script`, `jellyspore`: **14 of 14 "Scenario
  passed"**. The other arenas (crawler, skirmisher, archer, holder, retarget, give_up, patrol, alarm, flee, necromancer,
  door, factions, townsfolk_chat, marker_stops ...) were not rerun; the handoff records them passing on 2026-11-06.
- **Engine reads**: `evt.SummonMonstersById` (`game/events/EventRuntime.cpp:8665-8760`), `evt.TriggerActor` and
  `evt.WakeActor`, the Stationary rule (`game/indoor/IndoorWorldRuntime.cpp:11812-11820`), the swimmer's water facts
  (`IndoorWorldRuntime.cpp:11493-11511`).

## Summary by status

| Status | Scripts (of 48) |
| --- | --- |
| OK | 26: basecrawl, basefly, basemelee, baserange, crawlrange, dagrell, evilsorcerer, flyingicky, flyrange, ghost, guardbase, isle_summoner, lesserdemon, lobber, lobberpod, npcbase, policeman, spawngeneric, spawnloc, spawnnjam, summoner, titan, yanmirbase, yanmirfort_bugspawn, chasm_ghostspawner, greaterdemon (engine path) |
| PARTIAL | 15: banshee, baseswim, cat, dog, cow, goat, pig, rooster, fish, dp_cagemonster, dragon, spawncreature, spawnmgr, spawnnjamcameo, wizardsummoner |
| MISSING_DATA | 1: magreeb (Stationary rows; key 202 hook); plus the data halves of wizardsummoner and of the spawned scripts below |
| MISSING_ENGINE | 0 whole scripts; four small shared features recorded as parts of PARTIAL items (see the gap list) |
| NOT_NEEDED | 6: base (Huber Carryall), princess (RailTest), hen, duck, greenman, monkbase |

Outside the 48 but in scope (spawned through spawn strings, which the inventory marks "unused_unreferenced" because no
object names them): `enddemon.scr` (**gap 1**), `njam1000.scr` (OK, via njam.lua), `njamcameo.scr` (see
spawnnjamcameo), `wizarddemon.scr` (OK, Wizard's Lab Lua), `isle_spawncreature.scr` (OK since 2026-11-06: story.lua runs each Skeletoid to MarkerFrom, teleports it to MarkerTo
and spawns the next at its death),
`spawnface.scr` (dead: SpawnGeneric's `bFace = 1` exits before using it, `SPAWNGENERIC.scr:19`, `:81`).

## Prioritised gap list

### 1. Fights or progress that do not work

1. **1000 Terrors: the end demon's death opens nothing (probable progression block, verify in game).**
   `EndCount.scr` spawns `GreaterDemon ScriptName EndDemon.scr` at the third counted spawn; `ENDDEMON.scr:25-33` opens
   `sDoorA` on its death (`:21-22` declares it twice, Door1 then Door0; `sDoorB` is never set). Door0/Door1 (LT
   x 3184 and 3792, z -3682) are the double gate in front of the win switch (WinMan, LT 3488, -3658) and Njam's place;
   Door0 is `Triggers 0` (no player use). In the rework both doors have no click handler and the only `openGroup("Door0")`
   is the `njam_taunt` cinematic, which closes it again; the summoned end demon (`1000terrors.lua` `spawn()`,
   `evt.SummonMonstersById{monster = 9242}`) has no kill hook, and the win switch refuses a party south of the wall
   ("nothing from beyond the wall", LT z < -3680). Unless another route reaches the alcove, the finale (key 109, the move
   to the Hall of the Gods) cannot be reached. The scripted scenarios use the switch's event directly, so they would not
   notice. **Fix:** map Lua (mm9r_1000terrors/convert.py): keep the end demon's returned index and open Door0 and Door1
   at its death (the M24 marking pattern). Also: EndDemon spawns in (hidden, Spawn clip) and its HP line writes
   Hitpoints = AC x 1.5 (`:95-101`, MM9 bug, documented in MM9_AI_DATA_AND_SCRIPTS.md §4.2).

No other monster fight was found that cannot be won or lost or that blocks a quest. The items below change how fights
play.

### 2. Visible behaviour

2. **Fixed 2026-11-06** (table generator: only all-zero velocities are Stationary; Move 0 with a velocity is Short;
   arena `move_zero`; `monster_data.txt` regenerated). Was: **Rows the importer made `Stationary` never move**
   (MISSING_DATA, table generator; openyamm-19). MM9 never reads
   `Move` (MM9_AI_DATA_AND_SCRIPTS.md §1), but `generate_mm9_monster_tables.py` maps it to MM8's movement type and the
   indoor runtime lets a Stationary row move only when it is a civilian or has a behaviour script
   (`IndoorWorldRuntime.cpp:11812-11820`). Placed and affected: Magreeb 9277 x12 and Armored Magreeb 9278 x4
   (Lindisfarne), MagreebBaby 9244 (Thjorgard), Forad Darre 9252 (Afterworld, the Retribution fight). Njam, Ebora and
   the concubines walk (behaviour exemption); Lobbers are turrets anyway. Fix: write the movement from the velocities
   (all zero: stationary), or exempt every MM9-profiled row.
3. **Fixed 2026-11-06** (`classify`: a script whose own file sets Range type 2 is a ranged holder, so
   WizardSummoner.scr resolves to the row's holder and the converter writes no `profile`; arena `move_zero`). Was:
   **Wizard's Lab apprentices chase instead of holding** (MISSING_DATA, `placement_profile`; openyamm-19). After the
   ritual `WIZARDSUMMONER.scr:107-117` runs RangeInit and sets `g_rangeAttackType = RANGE_TYPE2`, and Range.inc's type 2
   never runs after a target (`RANGE.inc:291-316`, "in TYPE2 mode, we don't want to run after them"). The converter
   resolves the script to `archetype: skirmisher` (Range type 1), overriding the row's correct `ranged_holder` (6
   placements, actors 46-48, 50-52). Fix: a script that assigns RANGE_TYPE2 resolves to the holder (only
   EvilSorcerer.scr, WizardSummoner.scr and the unused SpellCaster.scr do).
4. **Arslegard's Njam never chases** (MISSING_DATA, map Lua; map session). `arslegardcity.lua` `njamChase()` gives key
   470 and the experience and sets group 4 hostile, but never sends `evt.TriggerActor(34, "Chase")`; njam.lua holds a
   `njamchase.scr` Njam passive until that trigger or a hit (`behaviors/njam.lua:107-110`). `evt.TriggerActor` is
   called by no installed map Lua and no converter. Not blocking (the reward is given).
5. **Magreeb.scr's quest hook is missing in Lindisfarne** (MISSING_DATA, map Lua). `MAGREEB.scr:12-39`: any Magreeb
   that first sees the party while it holds key 201 gives key 202 (Scholar promotion). Thjorgard's own Magreebs give it
   (R2 Lua); Lindisfarne's 16 row-script Magreebs do not, so MM9's second route is gone. Fix: a poll with
   `evt.ActorSeesParty` in Lindisfarne's Lua, or a generic "found party gives key" hook.
6. **No way to give an actor the party (or another actor) as its target** (MISSING_ENGINE, small; openyamm-19).
   MM9 does it in `SPAWNCREATURE.scr:23-41` (every SpawnMgr spawn and Anskram's StarterIcky0/1), `DP_CAGEMONSTER.scr:
   47-53` (Dark Passageway's six cage Terrors after `evt.WakeActor`), `WIZARDDEMON.scr:18-22`, the BaseCrawl/BaseFly
   `GetPlayer`/`GetMe` triggers (`BASECRAWL.inc:1234-1251`: Frosgard's Yetis, Thjorgard's jumpers, the Isle's Peter
   through Jumper.inc) and Dragon.scr's `SpawnMutants` (GetMe on the Dragon King). The rework's actors must perceive
   the party first, and Dragon Stadium's Winged Mutants take whoever they meet (the dragon by relation, or the party).
   Only Lua bosses can `setTarget`. Fix: `evt.SetActorTarget(actor, "party" | actorIndex)` or a summon field `target`,
   then the converters' calls.
7. **Lua summons lose their spawn string** (MISSING_ENGINE, small, plus converters). `evt.SummonMonstersById` takes no
   MM9 placement, so a spawn gets MM9's defaults: Spawner `DefaultSpawn` wander paths are dropped (1000 Terrors
   Spawner0/4/5/6/7/12 `WanderPathName EntPath/HallPath/EndPath/DemonPath`; Yanmir's Fort Spawner0-6 `YanM`, `YetiM`,
   `TreasM`, `KidM`, `PatrolM`, `TMark`; Thronheim City GuardSpawn0/1 `GMark` random), and `ScriptParams 1` spawn-ins
   (every Greater Demon the maps summon: 1000 Terrors' death spawns and end demon, Wizard's Lab's WizardDemon) appear
   without hiding and their Spawn clip. Fix: a summon field carrying an `mm9_ai` placement (path, script, params) and
   the converters filling it.
   **1000 Terrors fixed 2026-11-06:** the end demon (EndDemon.scr forces its spawn-in) and LesserDemon.scr p0 1's Greater
   Demons are summoned with `mm9 = {script_params = "1"}` (hidden, Spawn clip, Aware; the GreaterDemon effect stays the
   map's `evt.SpawnWorldEffect`).
8. **Swimmers on maps without water volumes** (PARTIAL, map geometry C8; map session). 1000 Terrors (2 Sea Monsters),
   Bathhouse (7 Jellyspores) and Dark Passageway (2 Sea Monsters, one with a death trigger) have no `water_volumes`, so
   BaseSwim.inc's land rule is off (`mm9WaterKnown`) and they fight as crawlers on the wading floor. Temple of Honk's six
   Fish (9227, arriving at R2) will be swimming civilians on a map without water either (FISH.scr swims and jumps inside
   its liquid container, `FISH.scr:37-100`). Check after R2.
   **Decided from the data (2026-11-06,** `re_mm8/work/mm9_water/dat_water_volumes.txt`, the DATs' placements): MM9 has
   water in all four. 1000 Terrors' Sea Monsters float (Gravity 0) inside BlueWater2 (160 LT deep); Dark Passageway's
   Female inside Ocean, the Male inside TubeRoomWater0: they swim there and, by BaseSwim.inc's ShouldRunAway (the
   *target's* IsInWater), run from a party on land. Bathhouse's BaseSwim Jellyspores (ColWInRoomC0 and the other
   row-script ones) stand on room floors (Gravity 1, MoveToFloor 1) above the wading pools: MM9 shows them on land
   fleeing a dry party and fighting one in a pool; the ImpHenchman.scr spores fight normally. Temple of Honk's six Fish
   float at the surface of BlueWater0 (a 22 LT trough, x -1232..-1120): they swim it, turn and jump (FISH.scr). So the
   fix is each map's `overrides.yml` `map: {swim: true}` (dungeon/water.py writes the DAT volumes) and a reconversion,
   by each map's owner; nothing in the monster rows.
   **Bathhouse fixed 2026-11-06** (the shared water rule, 12 volumes; review root, not promoted): its Jellyspores
   keep standing on the room floors as in MM9; one spawned in pool B's shaft runs from a dry party and stays in the
   water (`mm9r_bathhouse/scenario_swim.yml`).
   **Temple of Honk fixed 2026-11-06** (the shared water rule, on for every map; review root, not promoted): the pool is
   a 15-unit volume the party wades in; the fish are swimmers bound to it (mm9r_templeofhonk `swim_fish`: feet 2 over
   the bed, a 22-unit body so the centre starts under the surface; MM9's centres 10 LT over it would leave them walkers
   that climb the rims).
   **Dark Passageway fixed 2026-11-06** (the shared water rule; review root, not promoted): four volumes, both Sea
   Monsters swimmers at MM9's box centres (the Male in TubeRoomWater0, the Female in Ocean); the Female, hit by a party
   on the island, stays in the ocean (`mm9r_darkpassageway/scenario_swim.yml`).
9. **Dark Passageway's Njam cameo** (PARTIAL, verify). MM9 spawns `NjamtheMeddler ScriptName NjamCameo.scr`
   (`SPAWNNJAMCAMEO.scr:26`, `:61-71`): he wanders 10-20 s and vanishes when hit, used or touched (NjamCameo.scr Main).
   The rework shows the placed actor 43 for 15 s and removes it; it has no `mm9_ai` record, so njam.lua runs it in
   "plain" mode on its row's baserange loop (6 600 HP, two Grandmaster spells). Check that he does not fight a party that
   attacks him; better: vanish on hit as the cameo does.

### 3. Cosmetic

10. Banshee's `Undead` stat during passes (`BANSHEE.scr:19-84`): traced only, its effect undecoded (MM9_AI_NATIVE_RE
    open list); Banshees fly 896 where MM9 has 640.
11. Animals (M20 wander at R2): cat/dog hang-out with townsfolk and the dog chasing cats (`CAT.scr:58-160`,
    `DOG.scr:159-270`), the cat fleeing projectiles (`CAT.scr:264`), pig/hen/rooster pause clips (wander.inc), the
    goat's butt on use (`GOAT.scr:16-30`) and cow tipping on use (`COW.scr:27-80`): map Lua on the 53000 + object click
    (E3) could play the clips.
12. Summoners' show: Summoner.scr's RAttack1, sparklies and blue fire on each new minion (`SUMMONER.scr:88-101`),
    Isle_Summoner's hAttack1 per spawn (`ISLE_SUMMONER.scr:59-64`), Chasm_GhostSpawner's blue fire, SpawnGeneric's and
    SpawnNjam's appear sounds and GreaterDemon FX. The Lich Lab and Isle summoner behaviours never receive
    `startup`/`spawn` (the map Lua does the spawning itself), so summoner.lua only fights there.
13. Critter flights: Lich Lab's 24 LL_FlyingCreature Ickies hang in MM9 until their wing's trigger, then fly their
    marker list (passive in both). Here their placement says `dormant: {trigger, hang}` but the scene sets no actor
    `dormant`, so the AI does not hold them (passive actors still walk a placed path), and the wing triggers only set
    the Hostile bit (`lichlab.lua` handlers 233-238, no `evt.WakeActor`): they likely fly from the start; check in the
    window. 1000 Terrors' 19 critters are held and woken, but their flight paths are not carried (its README).
14. Jumper.inc's leap off the cliff and Isle_SeaMon's marker jumps (impulse moves, no engine support); OnProjectile near
    misses (BaseCrawl retarget, NPCBase flight, a hanging Icky's wake); Lobbers' `FadeOnDeath` (B11); GuardBase idle
    sounds (`GS_Init` unreachable in MM9 too); Ebora's Launch/CastSpell before her escape (the map Lua removes her first;
    R2's cinematics cover it).

## Detail per script

Rows are MM9 `MONSTERS.txt` numbers (runtime ids are 9000 + row). "Placed" counts the installed scenes unless noted.

| Script | What MM9 does | Rows, placements | Rework | Status |
| --- | --- | --- | --- | --- |
| `basecrawl.scr` | Crawler: chase with arrival timing, 70/45 % retarget, 30 s give-up, kill taunt, flee when told, alerts, resurrection (MM9_AI_DATA_AND_SCRIPTS.md §3.1) | 12 rows (Nagates, wolves, mummies, sheep, scholars, Dook militia) | `archetype: crawler`, MM9 loop | OK: arenas crawler, retarget, give_up, patrol (handoff), profiles checked |
| `basemelee.scr` | Skirmisher: crawler + strafe attack, evade, back-off taunt, speed throttle (§3.2) | 35 rows, 106 placed | `skirmisher` archetype + `skirmisher` modifier | OK: skirmisher arena |
| `baserange.scr` | Skirmisher + Range.inc type 1 shots and casts (§3.3) | 64 rows, 853 placed | `ranged: walker` | OK: ranged, archer arenas |
| `crawlrange.scr` | Crawler + Range.inc | 4 rows (Nagate Elder, Basilisks) | crawler + walker ranged | OK (same loop pieces) |
| `titan.scr` | Crawler + Range.inc (`TITAN.scr:9-19`) | 2 rows; 4 Forest Giants (Yanmir's Fort, via YanmirHidden.scr) | crawler + walker ranged | OK |
| `ghost.scr` | BaseMelee + Range on a hovering class (`GHOST.scr:7-18`) | 3 rows (Shadow, Apparition, Specter) | skirmisher, `movement: fly` | OK |
| `dagrell.scr` | BaseMelee without SpeedThrottle (`DAGRELL.scr:16-22`) | rows 148-149 | `throttle: false`; KingKong's two get `throttle: true` | OK |
| `evilsorcerer.scr` | Range type 2 holder, never chases (`EVILSORCERER.scr:11-46`) | rows 156-158, 42 placed | `ranged_holder` + `reposition` (user-approved deviation) | OK: holder, reposition arenas |
| `basefly.scr` | Flier passes, back off up, swoop, never flees (§3.5) | Birds 93-95 | `flier` | OK: bird arena |
| `flyrange.scr` | BaseFly + FlyRange shots (§3.5) | 6 rows; 2 Oculi placed with it (1000 Terrors) | `ranged: flier`; the Oculi's profile archetype flier | OK: banshee arena covers FlyRange |
| `banshee.scr` | FlyRange; `Undead` for up to 5 s per pass, no swoop, short low back-off, hides Cloth (`BANSHEE.scr:19-84`) | rows 162-164; 15 placed (Verhoffin, Dark Passageway) | `melee_window_seconds: 5` (traced) | PARTIAL: arena passes; the stat's effect unknown (gap 10) |
| `flyingicky.scr` | Hangs (Hang, hangfidget 2-10 s) until disturbed, Launch, BaseFly (`FLYINGICKY.scr:18-247`) | rows 87-89 | `dormant_until: disturbed`, `wake_seconds`, fidget | OK: dormant arena |
| `baseswim.scr` | Crawler bound to water: ignores and flees targets on land (`BASESWIM.inc:14-56`) | rows 168-170, 177-178; 39 placed | `swimmer`, `movement: swim`; water facts indoors | PARTIAL: jellyspore arena passes; three maps without water volumes (gap 8) |
| `lobber.scr` | Turret: idle scan turns, Aware, pod launch, RangeAttack, 30 s forget (`LOBBER.scr:39-340`) | rows 86, 106; 16 Beethoven, 14 Ice Lobbers | `turret`, `pod_launch` (pod rows assumed) | OK: lobber arena |
| `lobberpod.scr` | Crawler, always evades 1.8-2.2 s, never shoots, turns on Lobbers that hit it (`LOBBERPOD.scr:18-158`) | rows 84, 85, 105 | `always_evade`, no projectiles | OK (lobber arena launches them) |
| `lesserdemon.scr` | p0 = 1: a Greater Demon at its corpse (`LESSERDEMON.scr:18-53`) | row 241; 16 placed | `death_spawn: 9242` (engine, spawns with p0 1); map Lua for placed/spawned p0 1 (Bathhouse, 1000 Terrors M24, R2) | OK: spawn arena; M24 only in the review root so far |
| `greaterdemon.scr` | p0 = 1: hidden, Spawn clip, Aware, fight (`GREATERDEMON.scr:14-77`) | row 242 | `spawn_in` for engine spawns | OK on the engine path; Lua summons skip it (gap 7) |
| `policeman.scr` | Guard faction, 3 hits, help/alert rules (`POLICEMAN.inc:22-154`) | rows 107-110 | `guard` archetype, `relations.yml` | OK: guards, civilians arenas |
| `guardbase.scr` | Base + idle sounds (`GUARDBASE.scr:8-24`; GS_Init likely unreachable) | rows 111-113, 58 placed | skirmisher | OK (sounds cosmetic) |
| `monkbase.scr` | Hostility parameter through a misspelt variable: own logic never runs (`MONKBASE.scr:12-26`) | rows 123-125; placed monks run MonkGuardBasic.scr | row skirmisher; placements' own profile | NOT_NEEDED (MonkGuardBasic is part 3) |
| `npcbase.scr` | Townsfolk: wander, chats, flee to guards with help calls, RUDE on use (§3.11) | 86 rows; 475 `mm9_civilian` placements | `civilian`, `guard_refuge`, chats (indoor; every map is a BLV) | OK: civilians, civilians_monster, townsfolk_chat, talk_turn; no OnProjectile (gap 14) |
| `magreeb.scr` | BaseCrawl; key 202 on first sight with key 201 (`MAGREEB.scr:12-39`) | rows 244, 276-278; Lindisfarne 16 | crawler (walks since 2026-11-06) | PARTIAL (gap 5: Lindisfarne's key 202) |
| `dragon.scr` | Boss: fly-in on trigger, distance-banded wing/breath/bolt, target switching, hates all AI, mutants every 45 s doubling, reward (§4.1) | row 212; Dragon Stadium | `dragon_king.lua` on the turret loop; Lua wakes him, spawns mutants, gives key 472 and item 577 | PARTIAL: arena passes; mutants without GetMe (gap 6), smoke not drawn |
| `yanmirbase.scr` | Boss: Squish wake, hunts Ice Lobbercicles, door kicks, immune, trap ending (§4.1) | row 206; Yanmir's Fort | `yanmir.lua` + map Lua (wake, trap, doors, rewards) | OK: yanmir arena; earthquake spot and Wipe marker restore not modelled (plan) |
| `cat.scr` | Always wanders; hangs out with NPCs; flees dogs and projectiles (`CAT.scr:58-302`) | rows 294, 299, 300; 8 cats placed | civilian; wander at R2 (M20) | PARTIAL (gap 11) |
| `dog.scr` | Always wanders; hangs out; chases cats (`DOG.scr:111-304`) | row 295; 2 in Sturmford City | civilian; wander at R2 | PARTIAL (gap 11) |
| `cow.scr` | FarmAnimal wander with WanderON; tipping on use (`COW.scr:27-125`) | rows 267, 297; 2 placed (+8 Boot Camp at R2) | civilian | PARTIAL (gap 11) |
| `goat.scr` | FarmAnimal; butts whoever uses it (`GOAT.scr:16-36`) | row 268; 2 (+7 Boot Camp at R2) | civilian | PARTIAL (gap 11) |
| `pig.scr` | wander.inc tick, pause clips | row 271; 2 (Ta'Sar) | aimless approximation at R2 | PARTIAL (gap 11) |
| `rooster.scr` | Old base.inc + wander.inc | row 270; 1 (Drangheim Prison) | aimless approximation at R2 | PARTIAL (gap 11) |
| `hen.scr` | wander.inc | row 269; placed nowhere | — | NOT_NEEDED |
| `duck.scr` | wander.inc | row 293 (Goose); both placed geese run DumbGoose*.scr | — | NOT_NEEDED |
| `fish.scr` | Swims in its liquid, turns, jumps near the surface (`FISH.scr:37-154`) | row 227; Temple of Honk 6 at R2 (the Anskram and 1000 Terrors "Fish" are invisible script holders) | swimming civilian | OK for Temple of Honk (2026-11-06: BlueWater0 a scene water volume, the six fish swimmers bound to it, `scenario_swim.yml`; review root, not promoted); the surface jump has no clip |
| `greenman.scr` | BaseWander, ignores damage (`GREENMAN.scr:10-24`) | row 266; the one Green Man runs NPC221.scr | his placement's script | NOT_NEEDED (part 3) |
| `princess.scr` | Follows a target, hostage rescue triggers (`PRINCESS.scr:308-317`) | row 296 RailTest; placed nowhere | — | NOT_NEEDED |
| `base.scr` | BaseMelee only (`BASE.scr:12-23`) | row 298 Huber Carryall (no model); placed nowhere, not in the runtime table | — | NOT_NEEDED |
| `spawncreature.scr` | BaseMelee; targets the party at once (no SpawnRally exists in any map), tells SpawnMgr on death (`SPAWNCREATURE.scr:23-52`) | SpawnMgr's spawns; Anskram StarterIcky0/1 | skirmisher override (correct) | PARTIAL (gap 6) |
| `spawnmgr.scr` | p0 kills per respawn, p1 per batch, p2 class (`LesserDemon` gets `ScriptParams 1`), cap 10 kills, Off/On/ForceSpawn (`SPAWNMGR.scr:44-160`) | 1000 Terrors, Bathhouse, Lich Lab, Thjorad Mine | map Lua per map (Thjorad and Lich Lab caps at 10; Bathhouse and Thjorad reveal pre-placed hidden actors) | PARTIAL: spawns lack SpawnCreature's party target (gap 6) |
| `spawnloc.scr` | `spawn` = focus + ForceSpawn, `focus`, On/Off (`SPAWNLOC.scr:41-72`) | 17 objects, same maps | map Lua tables | OK |
| `spawngeneric.scr` | After 1+2 s and effects spawns p0; `Terrors` path tells EndCount (`SPAWNGENERIC.scr:41-81`) | 1000 Terrors TP0-5 | `spawn()` + `COUNTS` | OK (effects cosmetic) |
| `spawnnjam.scr` | With key 108: Njam1000 at a marker for 20-60 s, one at a time (`SPAWNNJAM.scr:80-133`) | 1000 Terrors, 8 markers | `njamAppear` moves the placed Njam (njamtaunt.scr, hunts as Njam1000 in njam.lua) | OK: njam arena |
| `spawnnjamcameo.scr` | Spawns NjamCameo.scr Njam for 10-20 s (`SPAWNNJAMCAMEO.scr:61-71`) | Dark Passageway SpawnNjam0 | actor 43 shown 15 s, removed | PARTIAL (gap 9) |
| `yanmirfort_bugspawn.scr` | A dead Ice Lobbercicle returns 600-900 s later, only out of the party's sight (`YANMIRFORT_BUGSPAWN.scr:10-80`) | Yanmir's Fort Respawn0-3 | `BUG_RESPAWN`, `tickRespawns` (party not near) | OK |
| `chasm_ghostspawner.scr` | Each `spawn` brings an Apparition (ghost.scr) at the next of 13 markers, then stops (`CHASM_GHOSTSPAWNER.scr:26-62`) | Chasm of the Dead | `spawnGhost()` | OK (blue fire not drawn) |
| `summoner.scr` | `startup`: a minion at each point; each death another at a random point with RAttack1 and effects; off at its death (`SUMMONER.scr:63-101`) | Lich Lab LichSummoner (Power Lich) | map Lua: 4 Specters, replacements to 10 kills, stop at the summoner's death; profile `ranged: none` (correct: no Range.inc) | OK (show cosmetic, gap 12) |
| `isle_summoner.scr` | Each `spawn`: hAttack1 and a Skeletoid (Isle_SpawnCreature.scr); six spawns (quirk) (`ISLE_SUMMONER.scr:59-64`) | Isle of Ashes LichSummoner (Lich King) | map Lua (`on("LichSummoner","spawn")`, six); Lich King `passive` (no AI loop, as MM9) | OK |
| `wizardsummoner.scr` | Friend of the party; ritual chain; then a type 2 holder against the Greater Demon; dies at once from any non-party hit; hostile if the party hits it (`WIZARDSUMMONER.scr:35-117`) | Wizard's Lab SummoningGuy0-6 (6) | ritual, beams, relations and the demon in map Lua; the row's holder (gap 3 fixed 2026-11-06) | OK |
| `dp_cagemonster.scr` | `go`: unlock and open its door, after the door's open time BaseInit with the party as target (`DP_CAGEMONSTER.scr:35-53`) | Dark Passageway CageTerror0-5 | `dormant: {trigger, caged}`; Lua wakes them after the open time | PARTIAL (gap 6) |

### AI includes

| Include | Rework | Status |
| --- | --- | --- |
| `aicommon.inc` (alerts, resurrection, hate/enrage) | alert tick, help calls, the resurrection chain; HateAll and the like as `evt.SetMonsterRelation` | OK (alarm, necromancer, factions arenas) |
| `basecrawl.inc`, `basemelee.inc`, `baseevade.inc`, `speedthrottle.inc`, `range.inc` | MM9 walker loops, skirmisher footwork, Range type 1/2 | OK; Range type 2 from a script assignment missed once (gap 3) |
| `basefly.inc`, `flyrange.inc` | flier loop and shots | OK |
| `baseswim.inc` | swimmer land rule | PARTIAL (gap 8) |
| `baserun.inc` | flee, cower, hiding places, help calls | OK (flee arena); OnProjectile missing |
| `basewander.inc` | aimless, leash, marker paths; marker stops at R2 | OK; `WanderPathStart` (B12) cosmetic |
| `basedoor.inc` | monster-opened doors (`ai_open`) | OK (door arena) |
| `basetimers.inc`, `aiglobals.inc`, `baseglobals.inc` | infrastructure | NOT_NEEDED |
| `npcbase.inc`, `policeman.inc` | civilian and guard archetypes | OK |
| `farmanimal.inc`, `wander.inc` | animal wander (M20, R2) | PARTIAL (gap 11) |
| `listmaker.inc`, `listtraverse.inc` | marker patrols from the converter's `path` | OK for walkers; passive critter flocks keep still (gap 13) |
| `jumper.inc` | ordinary monsters that see the party (M9) | PARTIAL (gaps 6, 14) |
| `njam1000.inc` | njam.lua hunt mode; :Init CanDamage FALSE as the scene's `mm9_can_receive_damage: false` (1000 Terrors' NjamtheMeddler0, 2026-11-06: no hit hurts him, so the HP-threshold vanish is never reached, as in MM9) | OK |
| `dookhostility.inc`, `drangheimhostility.inc`, `honkhostility.inc`, `monkhostility.inc`, `traininghostility.inc` | placement `hostility`/`faction` (94) and the maps' group bits | OK by data; their placement scripts are part 3 |
| `guardsounds.inc`, `monksounds.inc` | not carried | cosmetic |
| `base.inc`, `newbase.inc`, `baserange.inc`, `wanderair.inc` | only rooster.scr (for wander.inc) and unused scripts (base2, bat, bird, pigeon) | NOT_NEEDED |

Skipped as NPC, level or engine-free includes (parts 1, 3, 4): bankorb, bot*, checkstat, chessbase, cutscene,
cutsceneactor, cutscenebase, damagecalc, damagetype, darkp_initmystuff, firebreather (unused), flags, followpath
(cameras), followplayer (MarySheep, Yanmir's children, NPC48/90: the rework has no followers, `yanmirsfort.lua:267`),
globals, healer, lichlabscenes, lichscenetransitions, listtraversenonai, nogold, pickmon, pigplaylist, pledge,
proplauncher, sixfires, spellnames, svenshowtake, testingstuff, theit (unused), thething, basefile,
thjorgardgamescommon, united, water.

## Spawners and spawn scripts

| Source | Where | Rework | Status |
| --- | --- | --- | --- |
| `Spawner` objects (23) | 1000 Terrors 14, Yanmir's Fort 7, Thronheim City 2 | map Lua `SPAWNS`/`SPAWNERS` on the death triggers; Thronheim's guards M23 | OK; DefaultSpawn paths dropped (gap 7) |
| SpawnMgr / SpawnLoc | 1000 Terrors, Bathhouse, Lich Lab, Thjorad Mine | map Lua | PARTIAL (gap 6) |
| SpawnGeneric, EndCount, EndCountTrigger | 1000 Terrors | map Lua; end demon's door missing | **gap 1** |
| SpawnNjam, SpawnNjamCameo | 1000 Terrors, Dark Passageway | map Lua + njam.lua | OK / gap 9 |
| Chasm_GhostSpawner, Isle_Summoner, Summoner, WizardSummoner/WizardMaster, YanmirFort_BugSpawn | as named | map Lua | OK (gap 3 for the apprentices) |
| AISPAWN.txt, SourceMan, NightDwellers, Isle_SpawnMgr, SpawnTest | no map uses them | — | NOT_NEEDED (MM9_ACTOR_COMPLETENESS.md check 3) |

## Death and damage triggers from monsters

All monster `DeathTriggerTarget`s are carried by kill hooks: 1000 Terrors (16: spawners, TP4/TP5, StairGate), Yanmir's
Fort (Yetis to spawners, bugs to Respawn), Drangheim (bandits to the Hardrock counter, M5), Isle of Ashes (13
dragonflies to KillControl), Afterworld (Forad to RetributionCounter), Dark Passageway (ColloidalWarrior0 unlocks
TeleportDoor1, `darkpassageway.lua:163-178`; SeaMonsterFemale0 breaks DB_TeleporterCage0, `:183`), Wizard's Lab
(EvilGrandSorcerer1 and Oculus0 to the super eye, `wizardslab.lua:63-73`), Thjorgard (Jumper0/1 BuddyDead, B8). Monster
damage triggers: Lich Lab SkeletonMaster1 to SkeletonMaster52 `Resurrect` and Verhoffin's BustWraith0-3 dust (B8). The
one script-level death trigger not carried is ENDDEMON.scr's door (gap 1).

## Boss phases

| Boss | MM9 | Rework | Status |
| --- | --- | --- | --- |
| Dragon King (Dragon Stadium) | trigger fly-in, distance-banded attacks, target switching, mutants with GetMe, reward | `dragon_king.lua`, map Lua trigger, mutants, reward | PARTIAL (GetMe, gap 6) |
| Yanmir (Yanmir's Fort) | dormant until Squish, bug hunting, immune, trap death | `yanmir.lua` + map Lua | OK |
| Njam (1000 Terrors, Arslegard, Dark Passageway) | hunt with HP-threshold vanish; chase on trigger; cameo | `njam.lua` + map Lua | OK / gap 4 / gap 9 |
| Ebora and concubines (Bathhouse, Thjorad Mine) | invulnerable taunting, escape at the third death; FreeAtLast | `ebora.lua`, `concubine.lua`; the maps' Lua does the escapes and rewards directly | OK (Launch/CastSpell skipped, cosmetic) |
| Set-piece bosses (AK_GiantImp, IS_KillingLich, ISLE_SeaMon, ThronheimCity_Badass) | per-map scripts | `boss: true` placements without a behaviour; their maps' Lua carries the set pieces | part 3; Isle_SeaMon's patrol jumps not carried (gap 14) |
| Summoners, WizardMaster's demon | rituals and minions | map Lua | OK / gap 3 |

## Notes for the other parts and the handoff

- The inventory's "unused" list contains six live scripts reached only through spawn strings (njam1000, njamcameo,
  enddemon, wizarddemon, isle_spawncreature; spawnface is truly dead).
- HANDOFF_MONSTER_AI.md is stale on two points: no MM9 map is outdoor any more (all 44 are BLVs with `mm9_ai` on
  every placed actor), and the placement-script overrides are in 38 installed maps (432 placements), not missing in 29.
- `evt.TriggerActor` is used by no map: every trigger the boss behaviours listen for (summoner `startup`, Ebora
  `FreeAtLast`, Njam `Chase`) is either done by the map Lua itself or missing (gap 4).
