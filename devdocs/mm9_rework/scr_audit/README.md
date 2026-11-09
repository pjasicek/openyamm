# MM9 behaviour gap audit (2026-11-06)

The user asked for every MM9 `.scr` (level, monster, AI, pickup, minigame, environment) and the object wiring between
DAT objects to be checked against the rework, so that no door stays shut, no quest stalls and nothing MM9 does is
silently missing. Inventory: 802 scripts (715 `.scr`, 87 `.inc`) by user (DAT objects, MONSTERS.txt rows, includes),
plus 4,933 trigger/death/damage message links across 45 maps.

| Part | Scope | Result |
| --- | --- | --- |
| [level_environment.md](level_environment.md) | 217 scripts and the object classes/messaging that act without one | 149 OK, 41 partial, 5 data, 2 engine, 16 not needed |
| [monsters_ai.md](monsters_ai.md) | 48 scripts and the AI includes | 26 OK, 15 partial, 1 data, 6 not needed |
| [npc_quest_minigame.md](npc_quest_minigame.md) | 164 scripts, 15 includes, the quest-key table (168 keys) | 116 OK, 25 partial, 22 data, 16 not needed |
| [unreferenced.md](unreferenced.md) | 304 scripts no object names | 285 unused (tests, old copies, cut content), 19 reached by spawns/RunScript |
| [client_fx.md](client_fx.md) | 58 `DoClientFX` calls in 28 live scripts | 57 carried (27 wired 2026-11-06), 1 not carried |

Status words: OK (handled, with evidence), PARTIAL, MISSING_DATA (the engine can do it; the converter does not feed
it), MISSING_ENGINE (a feature is needed), NOT_NEEDED (checked against MM9).

## Implicit engine semantics

What MM9's engine does without any script line saying so, read from `mm9/game/data/object.lto` with Rizin
(2026-11-06; addresses are the DLL's). A hand-ported script must reproduce it; an audit checks it for every port.

Object lifecycle (the message rule is `MM9.receives` in `assets_dev/worlds/mm9/events/common/mm9_common.lua`; every
converter's dispatcher asks it with the receiver's actor index):

| Case | MM9 | Evidence |
| --- | --- | --- |
| Message to a dead or dying AI | Dropped: the actor classes' trigger hook (vtable `+0x224` = `0x10019e90`) passes nothing to the script while IsDead or IsDying (`+0x474`/`+0x475`), except `RESURRECT` while the actor waits for resurrection (WaitForResurrect, `+0xb22`, set by AICommon.inc's OnDeath). The engine commands after it in the router (`0x100bd9f0`: REMOVE, PLAYANIM, TELEPORT, SETSOLID ...) still act on the corpse; DESTROY on a dead actor does nothing (`0x10001fa0`) | Isle_SpawnCreature.scr :OnDeath sends `spawn` to a slain LichSummoner: no Skeletoid comes |
| OnXxx callbacks of a dead AI | Only OnDeath (event 7) and OnDeathDone (8) fire (`0x10018380`); OnFoundPlayer, OnDamage, OnTouchNotify, OnTargetDead and the rest do not | engine: outdoor OnFoundPlayer skips dead actors (indoor already did) |
| Wait timers of a dead AI | Still fire: the script's timer loop (`0x1009e290`) calls the routine for any owner, held only by PauseWait | AICommon.inc :OnDeathDone waits 5 s, then :AskForResurrection (RemoveObject when no one resurrects it); :DoResurrection checks `IsDead g_hMyObject` because its own wait can fire after death. Map Lua timers already run on; the shared actor behaviours (`ActorBehaviorRuntime`) clear an actor's timers at its death, which only AICommon's resurrection clean-up (not in the rework) would need |
| GetObjectHandle on a dead AI | The corpse's handle (FindNamedObjects, `0x100d8d10`); `if( h!=0 )` passes | hence the dropped `spawn` above, not a missing target |
| A destroyed DestructableBrush / DestructableProp | Keeps its script and takes every message (vtable `+0x224` = `0x100bd980`, no state check; vtables `0x101708a0`, `0x10172648`); DESTROY is max-hit-point damage through its Destructible aggregate (`0x100bacf0`) | Thjorad Mine's DB_Barrel6/7: their own DeathTriggerTarget sends HitMe to themselves and BlowUpTheBoards.scr breaks the boards |
| RemoveObject | The object and its script are gone: GetObjectHandle returns 0, Trigger to 0 does nothing (`0x1009ed80`), its waits never fire | `MM9.removeActor` marks the actor removed; `MM9.receives` drops its messages |
| OnUse / RUDE on a dead NPC | `Use` is an AddTrigger message (NPCBASE.inc:808 `AddTrigger Use, OnUse`): dropped like any other; a click on a corpse loots it | the engine's click on a dead actor is the loot |

Other implicit behaviour:
- `Trigger` from a script is queued and delivered at the sender's next update (`0x1009ed80`: SetNextUpdate 0.01 s),
  not inside the calling routine: code after the Trigger runs first.
- Message names compare case-blind (`_stricmp`, `0x100e4bc0`).
- A script's AddTrigger handler wins over the engine command of the same name (the router asks the script first and
  stops when it handled the message); an object without one gets the command: OPEN, CLOSE, TRIGGER, USE, LOCK,
  UNLOCK, TOGGLE, REVERSE, DESTROY, DAMAGE, REMOVE, PLAYANIM/LOOPANIM <anim>, TELEPORT <point>, RUNSCRIPT <scr>,
  SETSOLID, SETNONSOLID. `ON` and `OFF` match as prefixes (2 and 3 letters), so a script-less object takes `OneDown`
  as ON.
- DESTROY on a living AI with no `destroy` handler kills it (`0x10001fa0`: the death flag `+0x560`), it does not
  remove it: the corpse stays and takes no more messages (the Isle's TriggerEffects -> LichSummoner).

## Blocking (doors, exits, quest progress)

| # | Gap | Maps | Fix | State |
| --- | --- | --- | --- | --- |
| 1 | Region exits and arrivals in the old ODM frame (the shared writer ignored overrides.yml `offset`); Arslegard City and Connecting Tunnels offset twice | 12 regions, Afterworld, Arslegard City, Connecting Tunnels and the maps exiting into them | `dungeon/tables.py` `transitions_text` applies the offset; the two city wrappers no longer do | fixed 2026-11-06 ~17:00; all maps reconverted in R3 |
| 2 | The 1000 Terrors end demon's death does not open Door0/Door1 before the win switch (ENDDEMON.scr 25-33) | 1000 Terrors | converter | fixed 2026-11-06 (kill hook opens both; mm9r_1000terrors scenario_finale.yml walks through and wins) |
| 3 | Ivsar (NPC90.scr OnUse, key 194) has no handler: keys 242/196/21, Ivsar's reward (117) and Sturmford's coalition (38) are lost | Drangheim | regionlua | fixed 2026-11-06 evening (converter; review roots, not promoted; npc_quest_minigame.md "Fixed") |
| 4 | Scholar, Healer, Priest quests require MM9's per-character keys 425-444, which nothing sets: the magic promotion line (Mage, Priest, Druid) cannot start | Thjorgard City, Guberland City | citylua: `MM9.canPromote` | fixed 2026-11-06 evening (converter; review roots, not promoted; npc_quest_minigame.md "Fixed") |
| 5 | Pledge counting (pledge.inc, key 277) missing: the Green Man's Druid promotion | Frosgard City (+ Frosgard NPC221) | citylua | fixed 2026-11-06 evening (converter; review roots, not promoted; npc_quest_minigame.md "Fixed") |
| 6 | Thronheim City's Secretdoor0 has no click (loft room, Ladder2, chest sealed); Thjorgard City BembgateL/R and Arslegard CounterDoor likewise | cities | shared rule in `dungeon/movers.py` | fixed 2026-11-06 (movers.free_door: PushOpen, unlocked, no sender; Secretdoor0 by a headless walk and real click, BembgateL/R and CounterDoor by their events) |
| 7 | Mary's sheep (key 466) | Yorwick | regionlua with `evt.MoveActorTo` | fixed 2026-11-06 evening (converter; review roots, not promoted; npc_quest_minigame.md "Fixed") |
| 8 | Lindisfarne's Magreebs do not give key 202 (second Scholar route) | Lindisfarne | regionlua | fixed 2026-11-06 evening (converter; review roots, not promoted; npc_quest_minigame.md "Fixed") |
| 9 | 1000 Terrors' win switch moved to the deleted `hallofthegods.odm` | 1000 Terrors | converter (done) | fixed; scenario_finale.yml arrives in hallofthegods.blv |

## Visible behaviour

Fixed 2026-11-06 (in R3, the final rebuild):
- Engine: a ranged shot or attack spell with no actor under the crosshair takes the standing destructible there
  (Sturmford's chains; the visible outer chain stays undamageable as in MM9); missiles hit destructible props indoors
  and blasts damage every destructible in their radius; `evt.SetActorTarget`; Lua summons keep patrol and `mm9` AI
  settings (INDOOR_DESTRUCTIBLES.md "Aiming", ACTOR_SCRIPTING_INVESTIGATION.md).
- Converters: weapon breakables in 9 dungeons are scene destructibles (`motion: break`); Thjorad Mine's barrels,
  1000 Terrors' skull trap and Njam, Drangheim Prison Celldoor18/lever17, Anskram's letters, Sturmford's portcullis
  lever; MM9 hover texts from MMIXSCRIPTTEXT.csv (`mm9r_common/script_text.py`); Arslegard's Njam chase, Guberland's
  two games, Afterworld's Six Fires.
- Monster data: Magreebs, Forad and 30 other rows no longer Stationary; Wizard's Lab apprentices stand and cast; the
  Isle's Skeletoid chain.
- Town Portal: the TPChedian group (engine selects it for map ids 9001-9099), MM9's portal map and city highlights;
  Dimension Door's Sturmford landing in the BLV frame.

Fixed 2026-11-06 evening (converters; review roots, not promoted):
- Swimming is one shared converter rule (`mm9r_common/dungeon/water.py`, DUNGEON_PLAYBOOK.md "Water volumes and
  swimming"): every MM9 water volume is the scene's water on every map (swum where deep, waded where shallow); the
  maps' liquid surfaces go non-solid where a bed is under them, ShowSurface tops are drawn, swimmers float in their
  volume; `dungeon/swim_check.py` writes a per-map swim scenario. Per-map results in the projects' READMEs and
  FINAL_REBUILD_WORK.md C8.
- Njam (1000 Terrors' NjamtheMeddler0, Njam1000.inc CanDamage FALSE): `mm9_can_receive_damage: false`, no hit hurts
  him; the end demon and LesserDemon.scr p0 1's Greater Demons spawn in (summon `mm9 = {script_params = "1"}`).
- Guberland's bandits run to Atlimarker0 (`evt.MoveActorTo`) until they see the party (`evt.ActorSeesParty`).
- Frosgard City's Horde is hostile to the townsfolk (HateNPC AddEnemy NPC: `evt.SetMonsterRelation`, one way).
- Lich Lab's conscript (PeasantTransformee.scr) walks from the closet into the chamber, cowers and is turned.

Open:
- The scenario runner cannot assert that a TriggerDestroyOnly brush refuses damage (a console line that changes nothing
  fails its step).

Lifecycle rule, 2026-11-06 (night; "Implicit engine semantics" above; converters, review roots, not promoted):
messages to dead or removed AIs are dropped through `MM9.receives` / `MM9.actorAlive` in 28 converters. What changes:
a slain summoner or caged breaker does nothing (Isle LichSummoner, Lich Lab, the KingKong cages of Anskram, Inventa
Storca, Lich Lab, Thjorad Mine, Verhoffin), dead quest NPCs give no key (Arslegard's Njam 470, Afterworld's Skraelos,
Boot Camp's Grandpa 473, Guberland's AtliGuard 197, Yorwick's Mary 466, Thjorgard's Magreeb 202, Dungeon of Secrets'
Chadwick), corpses are no longer moved, shown or removed by scenes (Sturmford's Hatlati and Ivsar, Lindisfarne's monks,
Dook's basilisks, Training Hall's ghouls, the Arena), scripted chains stop at a dead link (Drangheim's quarrel,
Guberland's Players and new-game talk, Thronheim's Terror breakout and council, Wizard's Lab's banishing, Yanmir's
traps, Thjorgard's and Guberland's stones bots). The other way round: Thjorad Mine's barrels break the boards however
they were destroyed, and Dragon Stadium's dead Dragon keeps sending Winged Mutants (Dragon.scr's Wait 22 survives his
death; the corpse stays). Scenarios: `scenario_lifecycle.yml` in mm9r_isleofashes_blv, mm9r_lichlab,
mm9r_chasmofthedead, mm9r_guberland_blv; Arslegard `scenario_njam_dead.yml`, Thronheim `scenario_breakout_dead.yml`.
Thronheim's guard stream goes on after the Terror's death (2026-11-07: as MM9, a dying guard's OnDeath fires and
GuardSpawn0 is no AI, so nothing drops its Default; the guard it sends finds only the corpse). Open (decisions):
1000 Terrors' Njam is one reused actor where MM9 spawns a new one per appearance; WaitForResurrect is not modelled.

Cosmetic, fixed 2026-11-06 (night; converters and engine, review roots, not promoted):
- Engine: `evt.SpinMover` and scene `mover.spin` (continuous RotatingBrush spinners riding their parent mover; save
  version 159), `evt.SetFog` / `evt.ClearFog` (an indoor map's fog from Lua, faded), scenario asserts `light`,
  `scripted_fog` and `mechanism.spinning`. `evt.SetLight` already switched BLV lights, but only on vertex-lit faces (a
  bake keeps them): MM9's switched lights are scene pulsing lights.
- Shared converter: PerceptionLights shown by Perception (Dark Passageway 61, Thjorad Mine 10, Verhoffin 4); the
  WeatherMan's trigger switching (Frosgard's pass fog); wells, cauldrons, cook pots and clovers with their object.lto
  behaviour (RE: [MM9_BONUS_PROPS_RE.md](../MM9_BONUS_PROPS_RE.md)); NPC greeting voices on a click.
- Maps: the Lich Lab's Glow1, the spinners of Training Hall, 1000 Terrors, Dungeon of Secrets, Ruined Temple and
  Verhoffin, Sturmford City's barks (Tryggva, Ercc), the Guberland Players' show (voices only), the Temple of Honk
  ceremony (the leader; not the followers' walk).

The other cosmetic lists (letters, walks and set pieces, animations, skins, the remaining scenes) are in each part's
gap section.
