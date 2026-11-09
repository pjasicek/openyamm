# MM9 SCR audit, part 4: the unreferenced scripts

Date: 2026-11-06. Scope: the 304 files of `cat_unused_unreferenced.json` (no DAT `ScriptName`, no MONSTERS.txt row, no `#include`).
For each, other ways MM9 could reach it were searched:

- every other DAT property value of the 45 `assets_editor_dev/worlds/mm9/maps/*.raw_objects.yml` (ScriptParams, SpawnObject, trigger
  targets and messages, names; all 45 WORLDS `.dat` files are exported). No `.scr` name occurs outside `ScriptName`; the only
  embedded spawn strings (`SpawnObject` in thronheimcity) name ThronheimCity_Guard.scr.
- the code (comments stripped) of all 804 scripts: `Spawn` strings (`" ScriptName X.scr"`), `RunScript`, `CacheScript`,
  `Trigger h,RunScript X`, `#include X.scr`. Dynamic `RunScript` targets come from `GetStatStr ...,ScriptName` (the MONSTERS.txt
  script) and are already counted. Reachability was taken transitively from the scripts used by maps or MONSTERS.txt.
- `mm9/extracted/DATA/DATA/*` (only MONSTERS.txt names scripts), the 441 RUDE files (no script references; RUDE has no
  RUNSCRIPT column), `autoexec.cfg`/`defaults.cfg`.
- `strings` (ASCII + UTF-16) of cshell.dll, object.lto, lithtech.exe, mm9.exe and the other game DLLs. The only hard-coded
  script paths are `scripts\mmixscripttext.csv` and `SuperChicken.scr` (the Rooster spawn, not in this list). There is no
  `NPC%d.scr` pattern (only `RUDE\NPC%d.rude`), so NPCnnn.scr files load only by `ScriptName`.
- duplicates: line-set similarity (Jaccard of code lines) to every other script, to name the used successor of old copies.

Result: **19 REACHED**, **285 UNUSED**. Reached ones by category: level_environment 3, monsters_ai 11, npc_quest_minigame 4, npc_quest_minigame (shared text table) 1.
Status of the reached ones: MISSING_DATA 1, OK 11, PARTIAL 7.

## Reached scripts with gaps

| Script | Category | Status | Gap |
|---|---|---|---|
| `banditattack.scr` | monsters_ai | OK | fixed 2026-11-06: regionlua.py summons them at SpawnMarker and runs each to Atlimarker0 (`evt.MoveActorTo`, run); the watch's poll stops a runner that sees the party (`evt.ActorSeesParty`, then `evt.SetActorTarget` party: :OnExit) or has arrived; a load sends the rest on (OnPostSaveLoad) |
| `enddemon.scr` | monsters_ai | OK | fixed 2026-11-06: the summon at EndDemonMarker on the third count spawns in (`mm9 = {script_params = "1"}`: hidden, the GreaterDemon effect, Spawn clip, Aware; scratch check hidden at 0.3 s, shown at 2.8 s) and its death opens Door0/Door1 (scenario_finale.yml); the HP lines (x10, then MM9's bug HP = AC x 1.5) not carried |
| `hatenpc.scr` | monsters_ai | OK | fixed 2026-11-06: citylua.py `clansAgainstHorde` also sets the Horde rows hostile to every townsperson row of the map (AddEnemy NPC, one way; Kira the Cold is not in Frosgard City) |
| `isle_spawncreature.scr` | monsters_ai | OK (2026-11-06) | story.lua: the Skeletoid runs to MarkerFrom (evt.MoveActorTo, 20 s at most), teleports to MarkerTo with a column of fire, and its death sends LichSummoner `spawn` (six in all) |
| `mmixscripttext.csv` | npc_quest_minigame (shared text table) | MISSING_DATA | only thjorgard_blv regionlua.py (and the shared DoorLock 17 text) uses it; bathhouse, thjoradmine, 1000terrors, yanmirsfort and guberland say "not in the extracted data" and use own words or nothing for RollOverText 8, 11, 12, 14, 15, 16, 200, 201 |
| `njam1000.scr` | monsters_ai | OK | OK 2026-11-06: njamAppear() shows NjamtheMeddler0 hostile for 20-60 s (njam.lua hunt); Njam1000.inc :Init CanDamage FALSE is the scene's `mm9_can_receive_damage: false` (no hit of any kind hurts him; checked: 100 000 damage, HP 6 600 kept) |
| `njamcameo.scr` | monsters_ai | PARTIAL | darkpassageway README: appears and vanishes; wandering and vanish-on-touch not carried |
| `peasanttransformee.scr` | level_environment | OK | fixed 2026-11-06: with the chamber door down a Commoner (9050) appears at the closet's marker (Converter.scr p3), walks to the chamber's centre 2 s later (`evt.MoveActorTo`), cowers (Cower clip, wizardeyeloop.wav), winces and is turned into the Skeleton where he stands (lichlab convert.py, scenario_scripted.yml) |

The biggest one is `mmixscripttext.csv`: the RollOverText strings several converters believe are missing
(e.g. 8 "Ebora: Free at Last!! ...", 11/12/14 Ebora in the bath, 15/16 Njam's taunt, 200/201 Yanmir's children) are
in `mm9/extracted/SCRIPTS/SCRIPTS/MMIXSCRIPTTEXT.csv` (CRLF, `number,text`). Their own-words subtitles can be replaced.

## Reached scripts

| Script | Category | How MM9 reaches it | Behaviour | Status | Rework evidence |
|---|---|---|---|---|---|
| `ak_impgatespawn.scr` | monsters_ai | spawned by AK_ImpGate.scr (anskramkeep ImpGateSpawner0-7): `sScriptName = " ScriptName AK_ImpGateSpawn.scr"` | spawned Imp: BaseMelee, targets the player at once (AggressiveStart) | OK | anskramkeep convert.py summons hostile Imps per gate (script_imps) |
| `arenacreature.scr` | npc_quest_minigame | spawned by Arena.scr (thearena) `set SCRIPT " ScriptName ArenaCreature.scr"` | bout monsters walk out, hate each other, fight; lock doors | OK | thearena README "Bouts"/"Doors" |
| `arenafightplayer.scr` | npc_quest_minigame | spawned by ArenaFight.scr (thearena) `SCRIPT = " ScriptName ArenaFightPlayer.scr"` | arena fight monsters vs the party, key 1011 on start | OK | thearena convert.py (ArenaFightPlayer :Main/:Startup) |
| `arenamini.scr` | npc_quest_minigame | spawned by Arena.scr :pick (thearena) `set Script " ScriptName ArenaMini.scr"` | betting figurines on the counter; click = bet on A/B | OK | thearena convert.py slip() (Marker3/4) |
| `arenavictory.scr` | npc_quest_minigame | Arena.scr :BeVictorious `Trigger hWinner,RunScript ArenaVictory.scr` | winner taunts and runs off, next pair drawn | OK | thearena boutOver() |
| `banditattack.scr` | monsters_ai | spawned by Atliwagon.scr (guberland) `set SCRIPT " ScriptName BanditAttack.scr"` | bandits run (terrain mode) to Atlimarker0, then BaseMelee on the party | OK (2026-11-06) | fixed 2026-11-06: regionlua.py summons them at SpawnMarker and runs each to Atlimarker0 (`evt.MoveActorTo`, run); the watch's poll stops a runner that sees the party (`evt.ActorSeesParty`, then `evt.SetActorTarget` party: :OnExit) or has arrived; a load sends the rest on (OnPostSaveLoad) |
| `bc_monsterfight.scr` | level_environment | BC_Manager.scr (bootcamp) SPAWN_PARAM_0/1 "... ScriptName BC_MonsterFight.scr", CacheScript | museum demo: Evil Grand Sorcerer vs Oculus fight each other (EvilSorcerer/FlyRange AI) | OK | bootcamp_blv regionlua.py FIGHTERS |
| `bc_monsteropen.scr` | level_environment | BC_Manager.scr (bootcamp) SPAWN_PARAM_2 "ReverendMonk ScriptName BC_MonsterOpen.scr" | museum demo: a Reverend Monk walks to chests 4, 3, 0 and opens them | OK | bootcamp_blv regionlua.py bcOpen() |
| `enddemon.scr` | monsters_ai | spawned by EndCount.scr (1000terrors) `SCRIPT = " ScriptName EndDemon.scr"` | Greater Demon: invisible, spawn FX + Spawn anim, HP x nHPMod, range AI; :OnDeath opens Door0 (sDoorA) | OK (2026-11-06) | fixed 2026-11-06: the summon at EndDemonMarker on the third count spawns in (`mm9 = {script_params = "1"}`: hidden, the GreaterDemon effect, Spawn clip, Aware; scratch check hidden at 0.3 s, shown at 2.8 s) and its death opens Door0/Door1 (scenario_finale.yml); the HP lines (x10, then MM9's bug HP = AC x 1.5) not carried |
| `hate.scr` | monsters_ai | BattleMan.scr :GoodGuys (frosgardcity) `set SCRIPT " ScriptName Hate.scr"` (SixFires.inc :GoodGuys has it too but that label is never called) | clan soldiers: AddFriend NPC/Player, AddEnemy Horde, BaseMelee | OK | frosgardcity citylua.py clansAgainstHorde() relations |
| `hatenpc.scr` | monsters_ai | BattleMan.scr :Spawn (frosgardcity) `set SCRIPT " ScriptName HateNPC.scr"` | the Horde: AddEnemy NPC, ClanSoldier, KiratheCold, BaseMelee | OK (2026-11-06) | fixed 2026-11-06: citylua.py `clansAgainstHorde` also sets the Horde rows hostile to every townsperson row of the map (AddEnemy NPC, one way; Kira the Cold is not in Frosgard City) |
| `isle_spawncreature.scr` | monsters_ai | spawned by Isle_Summoner.scr (isleofashes LichSummoner) `sScriptName = " ScriptName Isle_SpawnCreature.scr"`; also named by the unused Isle_SpawnMgr.scr | Skeletoid: FX, RunTo MarkerFrom, teleport to MarkerTo, then wander + BaseMelee; on death triggers LichSummoner `spawn` (the next one) | PARTIAL | isleofashes.lua spawns a Skeletoid at SpawnLocation per `spawn` message, but no MarkerFrom/MarkerTo teleport and no death -> next spawn chain (only the trigger messages spawn) |
| `mmixscripttext.csv` | npc_quest_minigame (shared text table) | hard-coded in object.lto: `scripts\mmixscripttext.csv` (loaded for the RollOverText command) | 245 numbered RollOverText strings (Ebora, Njam, Yanmir children, games, "You used a key.", ...) | MISSING_DATA | only thjorgard_blv regionlua.py (and the shared DoorLock 17 text) uses it; bathhouse, thjoradmine, 1000terrors, yanmirsfort and guberland say "not in the extracted data" and use own words or nothing for RollOverText 8, 11, 12, 14, 15, 16, 200, 201 |
| `njam1000.scr` | monsters_ai | spawned by SpawnNjam.scr (1000terrors) `SCRIPT = " ScriptName Njam1000.scr"` | Njam appears HOSTILE (AddEnemy Player, BaseMelee + Range, CanDamage FALSE) for 20-60 s, then vanishes | OK (2026-11-06) | OK 2026-11-06: njamAppear() shows NjamtheMeddler0 hostile for 20-60 s (njam.lua hunt); Njam1000.inc :Init CanDamage FALSE is the scene's `mm9_can_receive_damage: false` (no hit of any kind hurts him; checked: 100 000 damage, HP 6 600 kept) |
| `njamcameo.scr` | monsters_ai | spawned by SpawnNjamCameo.scr (darkpassageway) `SCRIPT = " ScriptName NjamCameo.scr"` | Njam cameo: wanders, vanishes when damaged/touched | PARTIAL | darkpassageway README: appears and vanishes; wandering and vanish-on-touch not carried |
| `peasanttransformee.scr` | level_environment | spawned by Converter.scr (lichlab SkeletonTransformer) `SCRIPT_NAME = " ScriptName PeasantTransformee.scr"` | a peasant walks from the closet into the chamber, cowers, is turned into a Skeleton (hostile or party ally) | OK (2026-11-06) | fixed 2026-11-06: with the chamber door down a Commoner (9050) appears at the closet's marker (Converter.scr p3), walks to the chamber's centre 2 s later (`evt.MoveActorTo`), cowers (Cower clip, wizardeyeloop.wav), winces and is turned into the Skeleton where he stands (lichlab convert.py, scenario_scripted.yml) |
| `spawnface.scr` | monsters_ai | spawned by SpawnGeneric.scr (1000terrors TP0-3) `sScript = " ScriptName SpawnFace.scr"` | spawned monster targets the player at once, melee + range | OK | 1000terrors spawn() summons hostile monsters (default AI aggro) |
| `wizarddemon.scr` | monsters_ai | WizardMaster.scr (wizardslab) SPAWN_PARAM "GreaterDemon ScriptName WizardDemon.scr" | summoned Greater Demon: spawn/angry anims, enemy of the party, "finish" -> WizardDemonDeath | OK | wizardslab README: summon, relations, banishing done |
| `wizarddemondeath.scr` | monsters_ai | WizardDemon.scr :PlayDeathAnims `RunScript "WizardDemonDeath.scr"` (reached through wizarddemon.scr) | banished demon: four death animations, lifted and sunk | OK | wizardslab citylua.py banishing (scr_spec.md) |

## All 304

Class REACHED rows carry their category and status; UNUSED rows the evidence. "(0.xx)" is the code similarity to the named
successor. Weak hits (the bare word in RUDE text, object or texture names, engine class/command names such as `Damager`,
`AddNPC`, `Drunk`, `Teleporter`) were inspected and are not references.

| Script | Class | Evidence | Status |
|---|---|---|---|
| `1000t_bigicky.scr` | UNUSED | older copy of LL_FlyingCreature.scr (0.88, lichlab) / 1000T_FlyingCreature_.scr | NOT_NEEDED |
| `abuwater.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `addnpc.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `aggresive1.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `aitest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `ak_guardescape.scr` | UNUSED | Anskram Keep guard escape; no object | NOT_NEEDED |
| `ak_impgatespawn.scr` | REACHED (monsters_ai) | spawned by AK_ImpGate.scr (anskramkeep ImpGateSpawner0-7): `sScriptName = " ScriptName AK_ImpGateSpawn.scr"` | OK |
| `alfriggfight.scr` | UNUSED | cut conversation scenes (Alfrigg/Hrolf; the play); Alfrigg is "<<< REMOVED >>>" in MM_DrangheimCity; no object | NOT_NEEDED |
| `altcinemamgr.scr` | UNUSED | early cut-scene manager; no CinemaMgr object; maps use CutsceneBase.inc and per-map camera scripts | NOT_NEEDED |
| `animtest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `arenacreature.scr` | REACHED (npc_quest_minigame) | spawned by Arena.scr (thearena) `set SCRIPT " ScriptName ArenaCreature.scr"` | OK |
| `arenafightplayer.scr` | REACHED (npc_quest_minigame) | spawned by ArenaFight.scr (thearena) `SCRIPT = " ScriptName ArenaFightPlayer.scr"` | OK |
| `arenamini.scr` | REACHED (npc_quest_minigame) | spawned by Arena.scr :pick (thearena) `set Script " ScriptName ArenaMini.scr"` | OK |
| `arenavictory.scr` | REACHED (npc_quest_minigame) | Arena.scr :BeVictorious `Trigger hWinner,RunScript ArenaVictory.scr` | OK |
| `arg_tryygvascr.scr` | UNUSED | misnamed copy; ARG_Tryygva.scr is used (thronheimcity) | NOT_NEEDED |
| `arguecam2.scr` | UNUSED | copy of ArgueCam1.scr (0.92, thronheimcity) | NOT_NEEDED |
| `arraymaker.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `arrow.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `attack.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `attacktest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `attatchto.scr` | UNUSED | identical code to SpawnFace.scr (1.0); nothing spawns or attaches it by name | NOT_NEEDED |
| `aw_shoot.scr` | UNUSED | Six Fires shooter stub; no object | NOT_NEEDED |
| `banditattack.scr` | REACHED (monsters_ai) | spawned by Atliwagon.scr (guberland) `set SCRIPT " ScriptName BanditAttack.scr"` | OK (2026-11-06) |
| `barrel.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `base2.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `base2.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `basemove.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `baslisk.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `bat.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `bathhouse.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `battlejukebox.scr` | UNUSED | sound jukeboxes with no ScriptObject; DungeonJukebox.scr is the used one | NOT_NEEDED |
| `bc_monsterfight.scr` | REACHED (level_environment) | BC_Manager.scr (bootcamp) SPAWN_PARAM_0/1 "... ScriptName BC_MonsterFight.scr", CacheScript | OK |
| `bc_monsteropen.scr` | REACHED (level_environment) | BC_Manager.scr (bootcamp) SPAWN_PARAM_2 "ReverendMonk ScriptName BC_MonsterOpen.scr" | OK |
| `bell.scr` | UNUSED | bell prototypes; lindisfarnemonastery uses LindisfarneBell.scr | NOT_NEEDED |
| `bird.scr` | UNUSED | old dragon/flyer AI: DragonRed is the old Dragon.scr (0.67, MONSTERS.txt); the three fliers are identical stubs; no table row | NOT_NEEDED |
| `birdbase.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `bladetrap.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `bobanddoug.scr` | UNUSED | Bob and Doug talk; the same voices\cinema\BobandDoug lines are in NPC213.scr (used, frosgardcity) | NOT_NEEDED |
| `bonedragon.scr` | UNUSED | bone dragon experiment (SJR); no object | NOT_NEEDED |
| `bonelimb.scr` | UNUSED | bone dragon experiment (SJR); no object | NOT_NEEDED |
| `botbase.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `botevade.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `bouncyballfollow.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `button.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `c0test.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `cage.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `camera.scr` | UNUSED | only `#include camera.scr` / `runscript camera.scr` in TEST.scr, itself unused; "jeffs fun test" | NOT_NEEDED |
| `camerafollow.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `cameratest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `campdirector.scr` | UNUSED | camp-battle demo (John Machin); no CampDirector object | NOT_NEEDED |
| `cathedralbell.scr` | UNUSED | bell prototypes; lindisfarnemonastery uses LindisfarneBell.scr | NOT_NEEDED |
| `checkstat.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `chessking.scr` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `chesspiece.scr` | UNUSED | old chess AI; the 1000terrors board uses ChessPawn/Knight/Bishop + ChessBase.inc ("ChessPiece 0 5" in ChessSquare ScriptParams is an object-name list) | NOT_NEEDED |
| `chessplayer.scr` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `chessqueen.scr` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `chessrook.scr` | UNUSED | old chess AI; the 1000terrors board uses ChessPawn/Knight/Bishop + ChessBase.inc ("ChessPiece 0 5" in ChessSquare ScriptParams is an object-name list) | NOT_NEEDED |
| `cinemamgr.scr` | UNUSED | early cut-scene manager; no CinemaMgr object; maps use CutsceneBase.inc and per-map camera scripts | NOT_NEEDED |
| `circle.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `clandie.scr` | UNUSED | Hate.scr variant (0.55); no object | NOT_NEEDED |
| `closeshop.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `coffin.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `completeisleofashes.scr` | UNUSED | debug cheat/readout including TestingStuff.inc (win/max/min triggers); no object | NOT_NEEDED |
| `cotd_coffin.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `crusader.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `dagrellold.scr` | UNUSED | old Dagrell.scr (used via MONSTERS.txt) | NOT_NEEDED |
| `damagecalc.scr` | UNUSED | debug cheat/readout including TestingStuff.inc (win/max/min triggers); no object | NOT_NEEDED |
| `damager.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `dc_sleepyguard.scr` | UNUSED | old DooksSleepGaurd.scr (used, dookscastle) | NOT_NEEDED |
| `deadbird.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `deadcritter.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `deantest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `defense.scr` | UNUSED | old quest checkers: sturmford "defense" runs AK_Disable.scr; Anskrammainline.scr is used; sixfires logic lives in NPC336.scr :sixfires | NOT_NEEDED |
| `diesirae.scr` | UNUSED | organ/book songs; no object (lindisfarne uses LindisfarneBellController) | NOT_NEEDED |
| `director1.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `dookbattler.scr` | UNUSED | Dook's castle bridge battle; no object | NOT_NEEDED |
| `dookscastlecamera.scr` | UNUSED | camera scripts with no object (pattern of WizardLabCamera.scr, used) | NOT_NEEDED |
| `dp2boiler.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp2dragondead.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp2flamecontroller.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp2megahydra.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp3dragondead.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp3fireelemental.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp3lavashooter.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp3startup.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dp_checkpass.inc` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_guard0.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_guard1.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_guard2.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_interrogationguard0.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_interrogationguard1.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_interrogationprisoner.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dp_prisoner.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dpguard.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `dragonazure.scr` | UNUSED | hallofthegods DragonAzure objects have no ScriptName; no MONSTERS.txt row uses them | NOT_NEEDED |
| `dragonearth.scr` | UNUSED | hallofthegods DragonAzure objects have no ScriptName; no MONSTERS.txt row uses them | NOT_NEEDED |
| `dragonpharaoh2flame.scr` | UNUSED | cut "Dragon Pharaoh" levels (MonsterPharaoh2); only DP2Steam/DP2WaterDamage were reused (bathhouse, darkpassageway) | NOT_NEEDED |
| `dragonpharaoh2water.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `dragonred.scr` | UNUSED | old dragon/flyer AI: DragonRed is the old Dragon.scr (0.67, MONSTERS.txt); the three fliers are identical stubs; no table row | NOT_NEEDED |
| `dragonredair.scr` | UNUSED | old dragon/flyer AI: DragonRed is the old Dragon.scr (0.67, MONSTERS.txt); the three fliers are identical stubs; no table row | NOT_NEEDED |
| `dragontest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `drunk.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `dwarfcamp.scr` | UNUSED | camp-battle demo (John Machin); no CampDirector object | NOT_NEEDED |
| `dwarvenally.scr` | UNUSED | Thjorad mine prototypes; the mine uses DwarvenMiner.scr / NPC9.scr | NOT_NEEDED |
| `dwarvenminion.scr` | UNUSED | Thjorad mine prototypes; the mine uses DwarvenMiner.scr / NPC9.scr | NOT_NEEDED |
| `e3dungeoncamera0.scr` | UNUSED | E3 demo dungeon camera/director (pendulum, throne, scythe ...); no such map | NOT_NEEDED |
| `e3dungeondirector.scr` | UNUSED | E3 demo dungeon camera/director (pendulum, throne, scythe ...); no such map | NOT_NEEDED |
| `easy.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `eboragossip.scr` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `enddemon.scr` | REACHED (monsters_ai) | spawned by EndCount.scr (1000terrors) `SCRIPT = " ScriptName EndDemon.scr"` | OK (2026-11-06) |
| `erccspeechold.scr` | UNUSED | old ErccSpeech.scr (used, sturmfordcity) | NOT_NEEDED |
| `everstrike.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `evileyeactor.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `example1.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `farmerfemale.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `fill_rate_water.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `fire.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `firebreather.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `followcam.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `followpath.scr` | UNUSED | path helper of the camera tests (CameraTest/C0Test/Camera.scr, all unused) | NOT_NEEDED |
| `foremanminer.scr` | UNUSED | Thjorad mine prototypes; the mine uses DwarvenMiner.scr / NPC9.scr | NOT_NEEDED |
| `foremanminered.scr` | UNUSED | Thjorad mine prototypes; the mine uses DwarvenMiner.scr / NPC9.scr | NOT_NEEDED |
| `fortsteningmainline.scr` | UNUSED | old quest checkers: sturmford "defense" runs AK_Disable.scr; Anskrammainline.scr is used; sixfires logic lives in NPC336.scr :sixfires | NOT_NEEDED |
| `furnaceswitch.scr` | UNUSED | bathhouse mechanism prototypes (Karl Drown); bathhouse uses SteamVentDB/DrainWater/BathFurnace | NOT_NEEDED |
| `fxtest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `gargoyle.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `gasrelease.scr` | UNUSED | bathhouse mechanism prototypes (Karl Drown); bathhouse uses SteamVentDB/DrainWater/BathFurnace | NOT_NEEDED |
| `ghostfade.scr` | UNUSED | mummy/ghost prototypes; chasmofthedead uses MummyAwaken.scr, ghost.scr | NOT_NEEDED |
| `givestat.scr` | UNUSED | utility/prototype scripts with no object (AddNPC/Damager hits are engine command/class names) | NOT_NEEDED |
| `goblincamp.scr` | UNUSED | camp-battle demo (John Machin); no CampDirector object | NOT_NEEDED |
| `goblincin1.scr` | UNUSED | camp-battle demo (John Machin); no CampDirector object | NOT_NEEDED |
| `gopher.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `guard.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `guardactor.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `guardsounds.scr` | UNUSED | copy of GuardBase.scr (0.67, MONSTERS.txt) | NOT_NEEDED |
| `guardwalk.scr` | UNUSED | guard walk prototype; "GuardWalk" in Narrator.scr is a label of its own | NOT_NEEDED |
| `gungnir.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `hardrockcam.scr` | UNUSED | camera for TM_HardRock (used) with no object | NOT_NEEDED |
| `hate.scr` | REACHED (monsters_ai) | BattleMan.scr :GoodGuys (frosgardcity) `set SCRIPT " ScriptName Hate.scr"` (SixFires.inc :GoodGuys has it too but that label is never called) | OK |
| `hatenpc.scr` | REACHED (monsters_ai) | BattleMan.scr :Spawn (frosgardcity) `set SCRIPT " ScriptName HateNPC.scr"` | OK (2026-11-06) |
| `healer.scr` | UNUSED | healer prototypes; lichlab uses ILSHealerRoom.scr (+ healer.inc) | NOT_NEEDED |
| `hiredgoon.scr` | UNUSED | cut Drangheim Prison routines; the prison DAT uses DP_Patrol.scr / DrangheimHostility.inc (dp_checkpass.inc included by nobody) | NOT_NEEDED |
| `honkaccountant.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `honkfirstceremony.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `honkguardbasic.scr` | UNUSED | HONK guard prototypes; templeofhonk/thronheimcity use MonkGuardBasic.scr / Honkies.scr | NOT_NEEDED |
| `honkpamphlet.scr` | UNUSED | HONK guard prototypes; templeofhonk/thronheimcity use MonkGuardBasic.scr / Honkies.scr | NOT_NEEDED |
| `honkroompuzzle.scr` | UNUSED | Temple of Honk secret-room manager; no object | NOT_NEEDED |
| `horserider.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `huckster.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `ilsfan.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsfirebook.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilshealerbook.scr` | UNUSED | healer prototypes; lichlab uses ILSHealerRoom.scr (+ healer.inc) | NOT_NEEDED |
| `ilshurtroom.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsminotaurcage.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsnagash.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsrotateshooter.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsskeletonstart.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsskeletonstop.scr` | UNUSED | cut rooms of the "ILS" dungeon (the shipped lichlab uses only ILSShootingBook/ILSHealerRoom); Nagash and minotaur cage objects absent | NOT_NEEDED |
| `ilsspellroom.scr` | UNUSED | healer prototypes; lichlab uses ILSHealerRoom.scr (+ healer.inc) | NOT_NEEDED |
| `imptrickster.scr` | UNUSED | bathhouse imp prototype; bathhouse uses ImpHenchman.scr | NOT_NEEDED |
| `integris.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `isle_spawncreature.scr` | REACHED (monsters_ai) | spawned by Isle_Summoner.scr (isleofashes LichSummoner) `sScriptName = " ScriptName Isle_SpawnCreature.scr"`; also named by the unused Isle_SpawnMgr.scr | PARTIAL |
| `isle_spawnloc.scr` | UNUSED | Isle copies of SpawnMgr.scr (0.62) / SpawnLoc.scr (0.79); isleofashes uses Isle_Summoner.scr instead | NOT_NEEDED |
| `isle_spawnmgr.scr` | UNUSED | Isle copies of SpawnMgr.scr (0.62) / SpawnLoc.scr (0.79); isleofashes uses Isle_Summoner.scr instead | NOT_NEEDED |
| `ivsarfollow.scr` | UNUSED | copies of Princess.scr (0.92 / 0.41, MONSTERS.txt); no Ivsar object | NOT_NEEDED |
| `ivsarfollownew.scr` | UNUSED | copies of Princess.scr (0.92 / 0.41, MONSTERS.txt); no Ivsar object | NOT_NEEDED |
| `jarb.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `jeff.scr` | UNUSED | working-monk prototypes (jeff.scr is a copy, 0.83); monastery monks run MonkGuardBasic/ThjoradMonk; "Jeff" in isleofashes is an object name | NOT_NEEDED |
| `jeffcameratest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `jefftest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `junk.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `junk2.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `lichactor.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `licheffects.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `lichescort.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `lichlab.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `lichlabcamera.scr` | UNUSED | camera scripts with no object (pattern of WizardLabCamera.scr, used) | NOT_NEEDED |
| `lichsacrifice.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `lichsorcerer.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `lichsorcerernew.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `ll_machinepanel.scr` | UNUSED | Lich lab machine panel; no object | NOT_NEEDED |
| `mercenarypromo.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `mm_arslegaard.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_arslegard.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_arslegardcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_drangheimcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_frosgardcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_guberlandcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_jyrkavik.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_lindisfarne.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_sturmfordcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_thjorgardcity.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_thronheim.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mm_yorwick.scr` | UNUSED | "Mundane Task List" NPC day schedules (Jim Craig); no object, no spawn, no binary string: cut system (Arslegaard/Jyrkavik/Yorwick copies identical) | NOT_NEEDED |
| `mmixscripttext.csv` | REACHED (npc_quest_minigame (shared text table)) | hard-coded in object.lto: `scripts\mmixscripttext.csv` (loaded for the RollOverText command) | MISSING_DATA |
| `moonwater.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `movehotwater.scr` | UNUSED | bathhouse mechanism prototypes (Karl Drown); bathhouse uses SteamVentDB/DrainWater/BathFurnace | NOT_NEEDED |
| `mummylives.scr` | UNUSED | mummy/ghost prototypes; chasmofthedead uses MummyAwaken.scr, ghost.scr | NOT_NEEDED |
| `navtest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `newgame.scr` | UNUSED | Broccan/Scandlan talk; the same voices\cinema\NewGame lines are in NPC150.scr (used, guberland) | NOT_NEEDED |
| `newrange.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `nightdwellers.scr` | UNUSED | night/auto spawners with no object | NOT_NEEDED |
| `njam1000.scr` | REACHED (monsters_ai) | spawned by SpawnNjam.scr (1000terrors) `SCRIPT = " ScriptName Njam1000.scr"` | OK (2026-11-06) |
| `njamcameo.scr` | REACHED (monsters_ai) | spawned by SpawnNjamCameo.scr (darkpassageway) `SCRIPT = " ScriptName NjamCameo.scr"` | PARTIAL |
| `nobleman.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `npc1.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc100.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc11.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc140.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc189.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc243.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc281.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc339.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc382.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc6.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc67.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc94.scr` | UNUSED | NPCnnn.scr not attached: the placed NPCs run other scripts (1 Yrsa: yrsa/ARG_Yrsa; 100/140/243: BankOrb; 6/11: Shopkeeper; 281: retainer) or none (189, 339, 382, 67); 94 is not placed; no automatic NPC%d.scr load in the binaries (only RUDE\NPC%d.rude) | NOT_NEEDED |
| `npc9mod.scr` | UNUSED | modified NPC9.scr; NPC 9 (thjoradmine) runs NPC9.scr | NOT_NEEDED |
| `npccommon.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `oldbase.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `orb.inc` | UNUSED | include file #included by no script (successors: base.inc/newbase.inc/basemelee.inc, range.inc, pledge.inc, Orb.scr) | NOT_NEEDED |
| `peasanttransformee.scr` | REACHED (level_environment) | spawned by Converter.scr (lichlab SkeletonTransformer) `SCRIPT_NAME = " ScriptName PeasantTransformee.scr"` | OK (2026-11-06) |
| `pigcam.scr` | UNUSED | Thjorgard pig races: cut (no pig racer objects) | NOT_NEEDED |
| `pigeon.scr` | UNUSED | old dragon/flyer AI: DragonRed is the old Dragon.scr (0.67, MONSTERS.txt); the three fliers are identical stubs; no table row | NOT_NEEDED |
| `pigracer.scr` | UNUSED | Thjorgard pig races: cut (no pig racer objects) | NOT_NEEDED |
| `pigracerai.scr` | UNUSED | Thjorgard pig races: cut (no pig racer objects) | NOT_NEEDED |
| `plateaujukebox.scr` | UNUSED | sound jukeboxes with no ScriptObject; DungeonJukebox.scr is the used one | NOT_NEEDED |
| `playeractortest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `pooldamage.scr` | UNUSED | copy of SteamVentDB.scr (0.77, bathhouse) | NOT_NEEDED |
| `priest.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `propbonus.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `proptest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `propthrower.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `pyramidshooter.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `removebrush.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `respawn.scr` | UNUSED | night/auto spawners with no object | NOT_NEEDED |
| `rocktest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `rondo.scr` | UNUSED | organ/book songs; no object (lindisfarne uses LindisfarneBellController) | NOT_NEEDED |
| `rotatetest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `rt_cryptbutton.scr` | UNUSED | copy of RT_CaveIn.scr (0.74, ruinedtemple); no object | NOT_NEEDED |
| `ryanbutton.scr` | UNUSED | identical to Book.scr (1.0, used) | NOT_NEEDED |
| `ryanteleporter.scr` | UNUSED | Ryan's deathmatch test (with RyanButton); no object | NOT_NEEDED |
| `scenecamera0.scr` | UNUSED | only named as an object by SceneTest.scr (unused); no DAT object SceneCamera0 | NOT_NEEDED |
| `scenetest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `scriptobjecttest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `shootervolume.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `sixfires.scr` | UNUSED | old quest checkers: sturmford "defense" runs AK_Disable.scr; Anskrammainline.scr is used; sixfires logic lives in NPC336.scr :sixfires | NOT_NEEDED |
| `song.scr` | UNUSED | organ/book songs; no object (lindisfarne uses LindisfarneBellController) | NOT_NEEDED |
| `soundtest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `sourcecreature.scr` | UNUSED | SourceMan.scr spawns SourceCreature.scr, but no object runs SourceMan; superseded by SpawnMgr.scr/SpawnCreature.scr (used) | NOT_NEEDED |
| `sourceman.scr` | UNUSED | SourceMan.scr spawns SourceCreature.scr, but no object runs SourceMan; superseded by SpawnMgr.scr/SpawnCreature.scr (used) | NOT_NEEDED |
| `spawnface.scr` | REACHED (monsters_ai) | spawned by SpawnGeneric.scr (1000terrors TP0-3) `sScript = " ScriptName SpawnFace.scr"` | OK |
| `spawntest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `spellcaster.scr` | UNUSED | copy of BaseRange.scr (0.67, MONSTERS.txt) | NOT_NEEDED |
| `startuptest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `strengthtest.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `suntemplebuttons` | UNUSED | extension-less duplicate of SunTempleButtons.scr (0.96, ruinedtemple) | NOT_NEEDED |
| `suntempleentrance.scr` | UNUSED | Grand Temple of the Sun altar/prison scripts; ruinedtemple DAT uses only SunTempleButtons.scr, rt_* | NOT_NEEDED |
| `suntempleprison.scr` | UNUSED | Grand Temple of the Sun altar/prison scripts; ruinedtemple DAT uses only SunTempleButtons.scr, rt_* | NOT_NEEDED |
| `taladdermove.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `teleporter.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `test.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `tester.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `testingstuff.scr` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `th_bullseye.scr` | UNUSED | Training Hall extras with no object (the hall uses ten other TH_*.scr) | NOT_NEEDED |
| `th_chandelier.scr` | UNUSED | Training Hall extras with no object (the hall uses ten other TH_*.scr) | NOT_NEEDED |
| `thegopher.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `theit.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `theplay.scr` | UNUSED | cut conversation scenes (Alfrigg/Hrolf; the play); Alfrigg is "<<< REMOVED >>>" in MM_DrangheimCity; no object | NOT_NEEDED |
| `thething.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `thethingerizer.scr` | UNUSED | cut Lich Lab transformation cinema (actors, effects, TheThing/TheIt); "TheThing" eye in lichlab has no ScriptName | NOT_NEEDED |
| `thjoradmonkmod.scr` | UNUSED | modified copy of ThjoradMonk.scr (0.69, lindisfarnemonastery) | NOT_NEEDED |
| `tocatta.scr` | UNUSED | organ/book songs; no object (lindisfarne uses LindisfarneBellController) | NOT_NEEDED |
| `tonywater.scr` | UNUSED | only a `:	TonyWater.scr` header label copied into MoonWater/WawaWater (unused); successor water.inc (0.89) | NOT_NEEDED |
| `townsfolkboy.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `townsfolkfemale.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `townsfolkgirl.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `townsfolkmale.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `traps.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `tremors.scr` | UNUSED | generic prop/trap prototypes; maps use engine classes (Teleporter, Door, DestructableBrush, Shooter) or other scripts (NPC88.scr barrels, PropTrigger.scr, ButtonPuzzle.scr, PropLauncher.inc); weak hits are object/texture names only | NOT_NEEDED |
| `triggertest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `trongame.scr` | UNUSED | renamed Stones game: the TronPlayer objects (guberland, thjorgard) run StonesPlayer.scr; StonesGame/StonesPiece used | NOT_NEEDED |
| `tronpiece.scr` | UNUSED | renamed Stones game: the TronPlayer objects (guberland, thjorgard) run StonesPlayer.scr; StonesGame/StonesPiece used | NOT_NEEDED |
| `tronplayer.scr` | UNUSED | renamed Stones game: the TronPlayer objects (guberland, thjorgard) run StonesPlayer.scr; StonesGame/StonesPiece used | NOT_NEEDED |
| `turtle.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `utils.inc` | UNUSED | empty file (0 bytes) | NOT_NEEDED |
| `wander.scr` | UNUSED | early "Default script for wanderers" ambient AI; MONSTERS.txt uses NPCbase/Guardbase/MonkBase/animal scripts; class names in Guard/Nobleman are AlertName checks | NOT_NEEDED |
| `wanderman.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `water.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `watertrap.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `wawawater.scr` | UNUSED | water raise/sink prototypes (Tony Evans/Jeff Leggett); the shipped water uses DrainWater.scr / water.inc; "WaterTrap" in verhoffinruins is a BlueWater running DrainWater.scr; Abu Dectome/Temple of the Moon/Training Arena rooms not in the DATs | NOT_NEEDED |
| `wg_scene7cam3.scr` | UNUSED | copy of WG_Scene7Cam1.scr (0.73); hallofthegods camera WG_Scene7Cam3 has no ScriptName (WinMan's triggers to it do nothing) | NOT_NEEDED |
| `wizarddemon.scr` | REACHED (monsters_ai) | WizardMaster.scr (wizardslab) SPAWN_PARAM "GreaterDemon ScriptName WizardDemon.scr" | OK |
| `wizarddemondeath.scr` | REACHED (monsters_ai) | WizardDemon.scr :PlayDeathAnims `RunScript "WizardDemonDeath.scr"` (reached through wizarddemon.scr) | OK |
| `workingmonk.scr` | UNUSED | working-monk prototypes (jeff.scr is a copy, 0.83); monastery monks run MonkGuardBasic/ThjoradMonk; "Jeff" in isleofashes is an object name | NOT_NEEDED |
| `workingmonkmod.scr` | UNUSED | working-monk prototypes (jeff.scr is a copy, 0.83); monastery monks run MonkGuardBasic/ThjoradMonk; "Jeff" in isleofashes is an object name | NOT_NEEDED |
| `worldtest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `wptest.scr` | UNUSED | developer test/stub (header "test", trace prints or an empty :Main); no DAT object, spawn string, table or binary string | NOT_NEEDED |
| `wyvern.scr` | UNUSED | WyvernAir/WyvernGround RunScript each other, but nothing starts either; no Wyvern in MONSTERS.txt ScriptName | NOT_NEEDED |
| `wyvernair.scr` | UNUSED | WyvernAir/WyvernGround RunScript each other, but nothing starts either; no Wyvern in MONSTERS.txt ScriptName | NOT_NEEDED |
| `wyvernground.scr` | UNUSED | WyvernAir/WyvernGround RunScript each other, but nothing starts either; no Wyvern in MONSTERS.txt ScriptName | NOT_NEEDED |
| `yanmirpatrol.scr` | UNUSED | patrol prototype (DP_Patrol pattern); yanmirsfort objects use Yanmir*.scr | NOT_NEEDED |
| `yobboe.scr` | UNUSED | early quest/promo checkers; the shipped quests run in NPC334.scr :Gungnir, LudwigVan.scr, NPC89/91-93.scr, NPC240/186.scr, npc416.scr, Givetake.scr, HucksterMod.scr and the Thjorgard games; RUDE only mentions the words | NOT_NEEDED |
| `zombiecamp.scr` | UNUSED | camp-battle demo (John Machin); no CampDirector object | NOT_NEEDED |

Note: a few UNUSED scripts belong to quests whose MM9 logic moved elsewhere (sixfires.scr -> NPC336.scr :sixfires,
gungnir.scr -> NPC334.scr :Gungnir, integris.scr -> LudwigVan.scr, huckster.scr -> HucksterMod.scr); those quests are
audited through the used scripts in the other parts. NPC339.scr (Jokull, :Bathhouse) is itself unattached in MM9: the
Arslegard City shopkeeper with RUDE 339 has no ScriptName.
