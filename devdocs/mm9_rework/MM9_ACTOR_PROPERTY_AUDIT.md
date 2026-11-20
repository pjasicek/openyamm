# MM9 placed-actor DAT properties: what the rework carries (2026-11-06)

The user (2026-11-06), on MM9's "can't be damaged" actors: "fix it and check for any similar flags we may lack or if
this is the only one". This audit covers every DAT property that the rework's placed actors carry, for all 44 converted
maps. A placed actor is a row of a project's `work/content.json` `actors`. Its DAT object (matched by its `anchor`) is
in `assets_editor_dev/worlds/mm9/maps/<stem>.raw_objects.yml`. In total that is 2 097 actors. 26 of them have no DAT
object: Bathhouse's four spores, Ta'Sar's crate Dagrell, Thjorad Mine's 20 spawned Troglodytes and Thronheim City's
ExtraGuard. Pack growth copies (`_grow<k>`) are not counted.

The converter is `level_generation/projects/mm9r_common/dungeon/content.py` `Content.actor()`, which every dungeon,
city and region calls (outdoor_blv.py too). Its `mm9_ai` map comes from
`tools/mm9_import_discovery/mm9_ai_placement.py` `placement_ai()`, and each map's own `convert.py` / `citylua.py` /
`regionlua.py` adds its scripted wiring. The sources for what each property does in MM9 are the scripts in
`mm9/extracted/SCRIPTS/SCRIPTS` and the research notes in `monster_ai/MM9_AI_DATA_AND_SCRIPTS.md` (section 1),
`monster_ai/MM9_AI_NATIVE_RE.md` (sections 11-13), `MM9_MONSTER_JUMP_RE.md` and `OUTDOOR_BLV_ALL.md` ("Flying AI
findings").

## 1. CanDamage (fixed: FINAL_REBUILD_WORK.md B3)

**Data.** `CanDamage 0` is set on 412 actors in 25 maps:

- the townsfolk, shopkeepers, retainers and bank orbs of every city and region;
- the gods of the Hall of the Gods and the six Afterworld heroes;
- Baron Dook;
- Bathhouse's Ebora and her fat Colloidal bathmate BigColWinPool2;
- Yanmir;
- the 19 flying critters of 1000 Terrors;
- Isle of Ashes' Yrsa, Forad and SeaMonsterMale;
- Beethoven's eight PetrifiedMummy Rotters;
- Invent-a-Storca's six Scurry Basilisks.

The other 1 684 actors have `CanDamage 1`.

**MM9.** A hit on such an actor does nothing. TELP 1.3's note in YanmirBase.scr calls it "immune to physical damage".
This is MM9's own reading, and two scripts rely on spells still hurting:

- Njam (Njam1000.inc) vanishes once his hit points drop below a threshold while CanDamage is FALSE.
- YanmirBase.scr pays a "non-trap kill".

**Engine.** The engine's scene flag `mm9_can_receive_damage: false` blocks every hit. The hit lands and returns true,
but it does no damage, causes no hostility and no hit reaction, and no stun, debuff or melee side effect takes hold.
This covers melee, missiles, spells, area damage, reflected damage, monster blows and traps.

- Outdoors this was already enforced (OutdoorWorldRuntime `usesMm9ActorRules && !canReceiveDamage`).
- Indoors the flag was parsed and saved but never checked: every rework map is a BLV, so it had no effect. It is now
  enforced in IndoorWorldRuntime:
  - `applyActorShieldHit` (every damage path);
  - `applyPartyAttackMeleeDamage` (party melee and missiles);
  - the damage branch of `applyPartySpellToActor`;
  - `applyActorMeleeAttackToMapActor`;
  - `applyReflectedDamageToActor`;
  - `applyNonPartyAreaDamageToActor`;
  - `stunActor`, `debuffActor` and `applyPartyAttackMeleeEffects`.

Blocking everything is stricter than MM9. **The user's decision (2026-11-06): keep the strict flag** (it blocks all
damage, not only physical). It is the safe choice for townsfolk and gods (no fireballing a quest giver).
For Yanmir and Ebora it matches the rework, whose damage hooks already zero every hit. Njam is never given the flag
(his placements are `CanDamage 1`): his behaviour (`worlds/mm9/behaviors/njam.lua`, `immune = "physical"`) keeps
MM9's physical-only immunity, so spells still reach his vanish threshold.

**Runtime switch.** `evt.SetMm9ActorCanReceiveDamage(actorIndex, on)` (ISceneEventContext, indoors and outdoors) is
wrapped as `MM9.setCanDamage(index, on)` in `worlds/mm9/events/common/mm9_common.lua`. Indoors it writes the
`MapDeltaActor` and outdoors the `MapActorState` (and its placement record). Both are saved with the map already.
Tests (openyamm_runtime_tests `*CanDamage*`): `tests/IndoorActorFactionRuntimeTests.cpp` (indoors, through Lua)
and `tests/MonsterModifierWorldTests.cpp`
(outdoors).

**Converter.** `Content.actor()` writes `mm9_can_receive_damage: false` for every placement with `CanDamage 0`; the
others omit the field (the engine default is true). Pack growth already leaves such members out (`density.py`
`scripted_reason`: "scripted damage"). The ODM transcoder wrote the flag the same way.

**The scripts that switch it at run time (`SetPropNumber CanDamage`).**

| Script | Where | MM9 | The rework | Change |
|---|---|---|---|---|
| COFFINMUMMY.scr | Beethoven, PetrifiedMummy0-7 (Rotters, DAT CanDamage 0, Visible 0) | Invulnerable and not solid in the coffin; `:OnPostDestroy` (the kick that breaks the coffin) sets CanDamage TRUE. | Hidden (group 80 + k) until `mummy(k)` breaks the coffin, then shown and hostile. | `mummy(k)` now also calls `MM9.setCanDamage(MUMMIES[k], true)` (mm9r_beethoven/convert.py; `MUMMIES` from `actors()`). They can be killed once awake. |
| EBORABATH.scr | Bathhouse, Ebora (DAT CanDamage 0) | CanDamage FALSE at start and after loads; she never becomes damageable and leaves in a column of fire after three concubines die. | Damage hook zeroes her damage; removed when she escapes. | None: the DAT flag now also covers her. Not a kill target. |
| YANMIRBASE.scr | Yanmir's Fort, Yanmir0 (DAT CanDamage 0) | `:Reset` CanDamage FALSE on start and every load (TELP); dies by the trap (or spells in MM9). | Damage hook zeroes all damage; the trap moves him into the shaft and `MM9.removeActor` takes him away, paying the key and experience. | None: the flag covers him. He is "killed" by the trap, which does not need damage. |
| NJAM1000.inc | 1000 Terrors (NjamTaunt placement as SpawnNjam's Njam), Arslegard (NjamChase) | `:Init` CanDamage FALSE, vanishes below a random 1 500-4 500 HP (spells still hurt). | njam.lua behaviour: physical immunity, vanish at the threshold; the 1000 Terrors Lua shows him for 20-60 s. | None (deliberately): the full flag would leave the threshold unreachable. |
| ARENAMINI.scr | The Arena: 0.3-scale figurines spawned by Arena.scr `:Init` | Invulnerable bet tokens on the counter; removed when the bout starts. | No actors: betting slips at Marker3/4 (events 110/111). | None. |
| DESTRUCTON.scr | Destructible brushes, not actors: Frosgard City (35 ice blocks), the Sturmford region's Drawbridgechain, Thjorad Mine's CaveIn | `DamageOn` trigger sets CanDamage TRUE; the next hit destroys it. | Scene destructibles (`damage_enabled` from CanDamage); Frosgard City's ice stages in citylua.py, Sturmford's chain by `evt.DestroyDestructible` when both drawbridge chains break, the cave-in as a Lua door. | None. |
| IMPTRICKSTER.scr | Nowhere: no DAT object or script runs it (cut Bathhouse imp) | `Disappear`/`Reappear` toggle Solid, Visible and CanDamage. | Not converted. | None. |
| DP2MEGAHYDRA.scr | Nowhere (cut content, MM9_AI_DATA_AND_SCRIPTS.md 4.2) | `DamageOn` sets CanDamage 1. | Not converted. | None. |

**No boss is left unkillable.** The hostile actors that now have the flag are:

| Actor | Map | How it ends in the rework |
|---|---|---|
| Yanmir | Yanmir's Fort | The trap |
| BigColWinPool2 | Bathhouse | Boiled by the furnace (`KillFatc`, `MM9.removeActor`); Fatc.scr never sets CanDamage TRUE |
| The flying critters | 1000 Terrors | Removed at the end of their path |
| SeaMonsterMale, Yrsa, Forad | Isle of Ashes | Never fought in MM9 (Forad turns hostile only on a cut OnRude branch, key 104, and stays immune) |
| The coffin mummies | Beethoven | Turned damageable when they kick free (above) |

Every map Lua reference to a flagged actor is a show, hide, position or trigger call, not a kill check.

## 2. The other properties

Counts are placed actors and maps. "Carried" means the converter writes the property today.

| Property | Values (actors, maps) | MM9 | Rework | Gap and recommendation |
|---|---|---|---|---|
| `SightDistance`, `HearingDistance` | 27-34 values; sight 600 / 1320 / 1800 …, hearing 360 / 144 / 1200 … | Vision and hearing ranges; both double at the first target. | Carried: `mm9_ai.sight`, `hearing` (x 2.56). | None. |
| `RunawayChance` | 0.25 on 1 726; 0.05 on 256; 0 on 32; 1.0 on 2 … | Input to ShouldRunAway. | Carried: `mm9_ai.runaway_chance`. | None. |
| `RangeAttackType` | 2 on 33 (9 maps) | 2: hold position and shoot. | Carried: `mm9_ai.ranged_type`. | None. |
| `CanBeResurrected` | 1 on 891 (26 maps) | May be raised by a resurrecter. | Carried: `mm9_ai.can_be_resurrected`. | None. |
| `HidingPlace0-2`, `HidingPlaces` | names on 183; HidingPlaces 0 everywhere | Flee targets. | Carried: `mm9_ai.hiding_places`. | None. |
| `WanderON`, `WanderPathName`, `WanderPathRandom`, `WanderLeash`, `WanderWaitMin/Max`, `WanderTimeMin/Max` | WanderON 1 on 256 (20 maps); 96 with a path | BaseWander.inc: marker patrol or aimless wander. | Carried: `mm9_ai.wander`, `path`, `path_random`, `path_stops`, `wander_leash`, `wander_wait`, `wander_time`. | None. |
| `WanderPathStart` | non-zero on 35, of which 5 have a path (Ta'Sar's 3 guards, Thjorgard's JohnGoodmanWalk, a Lich Lab walker) | The first marker it walks to; then BaseWander continues at 1, 2 … (nCurrentMarker is not seeded). | Not carried: the path starts at marker 0. | Later, cosmetic (B12). |
| `ScriptName`, `ScriptParams` | 215 scripts | The placement's AI script. | Carried: `mm9_ai.script`, `script_params`, `profile`, dormant, hostility, summons, paths; boss behaviours by row. | None. |
| `Scale` | not 1.0 on 175 (22 values) | Model and body size. | Carried: `draw_scale` (bodies.draw_scale) and the body (placed_body). | None. |
| `DoRude`, `NPCNbr`, `GreetingSound`, `NPCProps` | 451 NPC objects; NPCProps 0 everywhere | RUDE dialogue, NPC row, voice line. | Carried: `mm9_rude_id`; GreetingSound in the city converters. | None. |
| `DeathTriggerTarget/Message` | 56 actors (11 maps) | Sends a trigger on death (spawners, doors, counters, quests). | Carried by each map's Lua (1000 Terrors and Yanmir's Fort dispatchers, Afterworld's RetributionCounter, Drangheim's YobboeMan, Isle of Ashes' KillControl, Dark Passageway, Wizard's Lab) and, since B8, the Thjorgard region's `Jumper0/1 -> Jumper2/3 BuddyDead` (regionlua.py: a kill hook shows the partner at once). | Done (B8). |
| `DamageTriggerTarget/Message` | 5 actors (2 maps) | Sends a trigger when hurt. | Carried since B8 with damage hooks: Lich Lab `SkeletonMaster1 -> SkeletonMaster52 Resurrect` (the buried one appears, hostile; convert.py `DAMAGE_TRIGGERS`), Verhoffin Ruins `BustWraith0-3 -> BreakOutDust0 On` (a smoke puff at the Fire, once per bust; `DUST_ON_HIT`). | Done (B8). |
| `Visible` | 0 on 26 (8 maps) | Not drawn until a script shows it; some scripts show it at start (CoffinMummy.scr `OnPostStartWorld` SetFlag VISIBLE). | Hidden where the map converter wires it (Beethoven's mummies, the Forest Giants, Yrsa in Thronheim City, Dark Passageway's Njam marker). Placed visible: the six Afterworld heroes and ForadDarre0, Guberland's NPC414 and Retainer commoners, Isle of Ashes' LichKing (Isle_Summoner; also Solid 0, Rayhit 0) and Thjorgard's ambush Bandit and Burgler (Thorgard_actor). | Done (B5): `Content.actor()` now places every DAT `Visible 0` actor hidden. Each has a show at MM9's moment: the Afterworld Lua's `showHeroes` (SixFires.inc :Confession) and Forad's show (:Retribution); Guberland's load shows Nicolai with key 121 (NPC414.scr :Init) and Alvar while not hired (Retainer.scr :Init, key 458). The Isle's Lich summoner stays unseen as in MM9 (story.lua spawns its Skeletoids). Thjorgard's jumpers (all four: Thorgard_actor.scr :SetupJumper hides Jumper0/1 too) appear after JumperTrigger, Jumper0 at once, Jumper1 1-2.5 s, Jumper2 10-25 s, Jumper3 30-45 s later (regionlua.py `jumperTick`). |
| `Solid` | 0 on 56 (8 maps): the critter flocks (1000 Terrors 19, Lich Lab 24), the Forest Giants, Thjorgard's actors, Guberland's two commoners, a Yorwick shopkeeper | The party and monsters pass through. | Not carried: the engine has no non-solid actor; all collide. | B6 later (engine: a scene `solid: false`). The flocks are the visible case. |
| `Rayhit` | 0 on 6: Isle of Ashes' and Lich Lab's Lich Kings and Power Liches, Dark Passageway's marker | Rays (aim and hit tests) pass through. | Not carried. | With B5 (the same set-piece actors). |
| `Gravity`, `MoveToFloor` | 0 on 412 / 407: flyers (Ickies, Eyes, Orbus, Dragonflies, Specters …), swimmers, the coffin Rotters, Thjorgard's 11 spectators, the cliff jumpers | No gravity; not snapped to the floor at load. | Flyers and swimmers by their row; walkers stand on the floor under them (Beethoven's AirBorneIckies keep their height). | None. |
| `TerrainMode` | 1 on 304 (11 maps) | Widens the vertical "can I reach it" rule (no lower limit, 10.5 half-heights up). | Not carried. | Not needed: `CanReachAll 1` on every placed actor bypasses that rule (MM9_MONSTER_JUMP_RE.md). |
| `CanReachAll` | 1 on all 2 096 | Bypasses the reach rule. | The rework has no reach rule. | Not needed. |
| `CheckForCliffs` | 0 on all | Cliff probe (and the actor reads `CheckForCliff`, so it is off for every monster anyway). | None. | Not needed. |
| `CheckForAIBarrier` | 1 on 413 (15 maps); 0 on 1 683, every flyer among them | Only these respect AIBarrier volumes. | The barriers are monster-only walls for every walker (dungeon/build.py `actor_barriers`). | B10 later: an actor-level "ignores barriers" flag only if a map shows a walker held back that MM9 let through. |
| `UsesRails`, `FlyerUsesRails`, `RailDist`, `MaxRailPath`, `RailCheckInterval`, `RailStuff` | UsesRails 0 on 78; FlyerUsesRails 1 on 9 (Verhoffin's Frights and Terrors) | AIRail graph navigation. | The engine's own pathfinding. | Not needed. |
| `AutoDeactivate` | 0 on 109 (Honk followers, Kluso's patrol, the wizards' ritual, Njam, the gods …) | Updated even when no client is near. | The engine's own actor activation. | B9: check those set pieces keep moving with the party far away (Temple of Honk procession, Kluso's House patrol, Wizard's Lab ritual). |
| `ShouldRepopulate` | 0 on 42 (13 maps): retainers, bank orbs, quest NPCs, Kluso's House's Count, Wizard's Lab's hostile Evil Grand Sorcerer | Stays as left (dead, gone) when the map repopulates. | Not carried: a map refill (map_stats refill days 150-600) brings every scene actor back. | Done (B4): the converter writes scene `respawns_on_refill: false`; at a refill (timed or forced) the engine gives such an actor back its saved record when the saved map has the same placement at its index (same name and monster), indoors (`keepActorsThroughRefill`, MapDeltaData) and outdoors (its saved MapActorState). Default true: MM6-MM8 maps are unchanged. The flag is scene data, read at each refill; the kept actor's state is saved as before. |
| `ShouldMiniSave` | 0 on 29 | Not kept in MM9's level-change mini save. | The engine saves the map whole. | Not needed. |
| `ExecuteScript` | 0 on 12: Drangheim Prison's PatrolGuard1 (DP_Patrol) and Guard6, Yanmir's seven caged children, Dark Passageway's dying adventurer, Invent-a-Storca's dying guard, a Guberland City peasant | The placement script is not started at load. In object.lto the AI ReadProp (0x1000cf1f-0x1000d003) reads `CacheOnly` and then `ExecuteScript` (default 1) into a local, and calls the object's run-script method (vtable +0x74) on `ScriptName` only when `ExecuteScript` is set (and the object field +0x18 is clear, presumably "not restored from a save"). Another script may start it later: Guberland City's peasant2 (Abriel, Leffery, Ralof, Trislan, Wilam), the Dark Passageway adventurer (DarkP_Warrior.scr) and the Invent-a-Storca guard (IS_KillingLich.scr). Nothing starts Drangheim Prison's PatrolGuard1 and Guard6 or Yanmir's children. | Done (B7): `Content.actor()` drops from its `mm9_ai` what only a running script gives (wander, its path and stops, waits and leash) when `ExecuteScript 0`, so the two prison guards stand at their posts. The hostility gate, perception and the map converters' own wiring stay. |
| `FadeOnDeath` | 1 on 16 (Beethoven's Lobbers) | The corpse fades out. | Corpses stay. | B11, cosmetic. |
| `BuryOnDeath` | 0 on 42 (the Dragon King, the Lich Kings and Power Liches, the wizards, the critters, GreenParty's corpses) | The corpse stays instead of sinking. | Corpses stay. | Not needed. |
| `TouchNotify` | 1 on Yanmir | Touch events to his script. | His behaviour hunts by distance. | Not needed. |
| `NeedsTick` | 1 on 221 | Engine update each frame. | Not applicable. | Not needed. |
| `GiveTreasure` | 1 on all 1 796 that have it | Drops its treasure. | Death loot by row. | Not needed. |
| `SpawnObject`, `SpawnObjectVel` | empty on all | Spawns an object on death. | None. | Not needed. |
| `Options`, `SurfaceType`, `Transparent`, `Chromakey`, `TintColor`, `TriggerDestroyOnly`, `CacheOnly` | one value each (CacheOnly 1 objects are left out already) | | | Not needed. |
| `Shadow` | 0 on 982 | No blob shadow. | The renderer's own creature shadows. | Not needed (cosmetic). |
| `Filename` | 98 models | The model. | Bound by row (approved 3D models). | None. |

No placed actor has a hostility property of its own. Hostility comes from the row and the placement script
(`mm9_ai.hostility`, `faction`; the Hostility.inc gates), which the converter carries.

## 3. Summary

- Carried now: CanDamage (B3), ShouldRepopulate (B4), Visible (B5), ExecuteScript (B7), every death and damage
  trigger (B8), everything the `mm9_ai` map holds (sight, hearing, runaway, ranged type, resurrection, hiding places,
  wander and paths, script), Scale and the RUDE and NPC fields.
- Open, in FINAL_REBUILD_WORK.md: B6 Solid (and Rayhit), B9 AutoDeactivate set pieces, B10 per-actor AIBarrier,
  B11 FadeOnDeath, B12 WanderPathStart.
- Not needed: TerrainMode, CanReachAll, CheckForCliffs, the rail settings, ShouldMiniSave, BuryOnDeath, TouchNotify,
  NeedsTick, GiveTreasure, SpawnObject and the uniform visual flags.
