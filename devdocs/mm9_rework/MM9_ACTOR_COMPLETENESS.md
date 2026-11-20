# MM9 actor completeness before the final rebuild (2026-11-06)

The user (2026-11-06): "I am worried that we missed more than just this. I dont want any missing npcs or actors."
This audit takes every character-like MM9 DAT object of the 44 rebuilt maps and gives it exactly one status. It also
checks that every RUDE dialogue can be opened in the game, and that MM9's spawners and timed spawns are carried. It
builds on [FINAL_REBUILD_WORK.md](FINAL_REBUILD_WORK.md) M2 and M15-M20 and on
[MM9_ACTOR_PROPERTY_AUDIT.md](MM9_ACTOR_PROPERTY_AUDIT.md) (B3-B13).

**Result.** There are 2 376 character objects. 2 121 are placed actors (25 of them from the next conversion on), 104
are placed props, 39 are scripted, 108 are excluded with a reason and **4 are missing**. The four missing ones need
new work, listed in FINAL_REBUILD_WORK.md M22-M23, **since carried by the converters (2026-11-06, effective at R2): the
audit now counts them as scripted (43 scripted, 0 missing)**. Of the 439 RUDE files, **one real dialogue was unreachable**: the
Yanmir's Fort children's RUDE 433, now fixed in the converter. The other 27 unreachable files are journal tables or
dialogues that MM9 itself never opens.

**Re-run:** `python3 level_generation/projects/mm9r_common/actor_completeness.py` (6 s; `--json FILE` for the full
list). The script holds the reasoned rules for every object that a conversion does not place. After the rebuild the 25
pending actors must show as plain placed actors. Until the five maps concerned are reconverted, the installed Yanmir's
Fort still shows the children's old RUDE 432.

**Blocker for R2, found on the way.** Promotion P1 deleted the old import's `assets_dev/worlds/mm9/maps/<stem>.material_aliases.yml`.
Every converter's `Source()` (`mm9r_common/dungeon/source.py` `Project.aliases`) reads that file, so every map
conversion now stops with FileNotFoundError before any geometry. The same is true of `terrain_textures.py` /
`terrain_blend.py` (regions) and Invent-a-Storca's `verhoffinruins` aliases. The files still exist in the review root
`output/mm9_rework/assets_dev`, in `output/mm9_rework/promotion_backup_20261106/worlds/mm9/maps/` and in
`assets_editor_dev/worlds/mm9/maps/`. Five of the editor copies (bootcamp, lindisfarne, thjoradmine, wizardslab,
yorwick) differ from the backup in their statistics header. Not changed here: the main session decides where these
converter inputs live. This audit read them from the backup.

## Method

- **Objects:** `assets_editor_dev/worlds/mm9/maps/<stem>.raw_objects.yml` for the 44 projects' `map.stem`, plus Great
  Gate. An object counts as a character when it has any of the following:
  - SightDistance or HearingDistance;
  - class RUDEProp, or RUDENPCId, NPCNbr or DoRude;
  - class Spawner, or DefaultSpawn;
  - a prop drawn with a character model (a model of any AI object or RUDEProp, plus njam, fre and the Wyrdes): a
    posed figure.

  There are 2 218 AI objects, 25 RUDEProps, 23 Spawners and 109 posed figures. Every NPCNbr/DoRude object is also an
  AI object. Animals, guards, townsfolk, shopkeepers, retainers, bosses and CacheOnly templates are all AI objects
  here.
- **Placed:** a placed actor has its DAT name as an `anchor` in the project's `work/content.json` (the last
  conversion). A placed prop has its index in `props.json` `source_object`, or its name in `source_name` or in the
  content.json decorations. For objects that neither file holds, the current converter inputs were re-run offline
  (`Content.monster_bases(npc_rows=True)` on the DAT and the floor under each object). The result is "placed at the
  rebuild": Boot Camp's 15 goats and cows (9268/9267/9297), the Temple of Honk's six fish (9227) and two geese
  (9293), Yorwick's ewe (9272), and Guberland's late guard (fixed below).
- **Reasons:** each reason was checked against the object's MM9 script (`mm9/extracted/SCRIPTS/SCRIPTS`) and the
  map's generator (convert.py, citylua.py, regionlua.py, story.lua).
- **RUDE:** the dialogue files are `assets_dev/worlds/mm9/dialogue/rude/NPC<id>.rude`. A dialogue counts as reached
  when one of these opens it:
  - an installed scene's `mm9_rude_id`;
  - `MM9.openRude` or `evt.OpenMm9Rude` in any MM9 Lua;
  - `hirelings.txt`.

  Each DAT host's own id was then compared with its placed actor. The id comes from DoRude with NPCnnn.scr, from
  NPC_nnn.wav or NPCNbr (stored as a float's bits), from RUDENPCId, from DoRude.scr p0, or from the parameter that
  GuardRude, MonkGuardBasic, ThjoradMonk and Honkies pass to DoRude. Services (service_venues.txt) open from their
  keeper's dialogue, so they add no entry point.

## Check 1: counts per map

| Map | Placed actor | of which at the rebuild | Placed prop | Scripted | Excluded | Missing |
|---|---:|---:|---:|---:|---:|---:|
| 1000terrors | 114 |  | 8 | 14 | 65 |  |
| afterworld | 8 |  | 30 |  |  |  |
| anskramkeep | 47 |  |  | 8 |  |  |
| arslegardcity | 36 |  |  |  |  |  |
| bathhouse | 16 |  |  |  |  |  |
| beethoven | 82 |  |  | 2 |  |  |
| bootcamp | 24 | 15 | 9 |  |  | 3 |
| chasmofthedead | 171 |  | 8 | 2 |  |  |
| connectingtunnels | 38 |  |  |  |  |  |
| darkpassageway | 43 |  | 10 |  |  |  |
| dookscastle | 47 |  |  |  |  |  |
| dragonstadium | 1 |  |  | 1 |  |  |
| drangheim | 39 |  |  |  |  |  |
| drangheimcity | 39 |  |  |  |  |  |
| drangheimprison | 80 |  |  |  | 1 |  |
| dungeonofsecrets | 1 |  |  |  |  |  |
| frosgard | 37 |  |  | 1 |  |  |
| frosgardcity | 50 |  | 2 |  |  |  |
| guberland | 64 | 1 |  |  |  |  |
| guberlandcity | 46 |  | 1 |  |  |  |
| hallofthegods | 10 |  | 7 |  | 2 |  |
| inventastorca | 39 |  |  |  |  |  |
| isleofashes | 51 |  |  |  |  |  |
| klusoshouse | 20 |  |  |  |  |  |
| lichlab | 147 |  |  |  |  |  |
| lindisfarne | 63 |  |  |  |  |  |
| lindisfarnemonastery | 27 |  |  |  |  |  |
| mountainpass | 76 |  |  |  |  |  |
| ruinedtemple | 15 |  |  |  |  |  |
| sturmford | 57 |  |  |  |  |  |
| sturmfordcity | 48 |  | 9 |  |  |  |
| tasaracademy | 24 |  |  | 1 |  |  |
| templeofhonk | 24 | 8 |  |  | 2 |  |
| thearena | 5 |  | 11 |  |  |  |
| thjoradmine | 73 |  |  |  |  |  |
| thjorgard | 53 |  |  |  | 1 |  |
| thjorgardcity | 60 |  |  |  |  |  |
| thronheim | 46 |  |  |  |  |  |
| thronheimcity | 43 |  | 7 | 1 | 7 | 1 |
| traininghall | 22 |  |  |  |  |  |
| verhoffinruins | 30 |  |  |  |  |  |
| wizardslab | 58 |  |  | 1 |  |  |
| yanmirsfort | 72 |  |  | 8 |  |  |
| yorwick | 75 | 1 | 2 |  | 29 |  |
| greatgate (not rebuilt) |  |  |  |  | 1 |  |
| **all** | **2 121** | **25** | **104** | **39** | **108** | **4** |

### MISSING (4, new work: FINAL_REBUILD_WORK.md M22, M23; carried since, see there)

| Map | Object | What MM9 does | Needed |
|---|---|---|---|
| bootcamp | EvilGrandSorcererCACHEONLY, OrbusCACHEONLY (Oculus), ReverendMonkCACHEONLY | BC_Manager.scr, sent `fight` / `open` by the museum's Switch0 / Switch1. It spawns an Evil Grand Sorcerer and an Oculus that fight each other as a demonstration (BC_MonsterFight.scr, mist effect, removed 120 s on or when one dies). It also spawns a Reverend Monk who walks to the chests and opens them (BC_MonsterOpen.scr, BC_TreasureChest.scr's lids and fire trap). | Actor-against-actor combat between two spawned non-party monsters, and a scripted walk (FINAL_REBUILD_GAPS section 4). The switches already exist as movers. |
| thronheimcity | GuardSpawn0 (Spawner) | ThronheimCity_Guard.scr :OnDeath. During the Terror's breakout, every dead guard sends a new PoorTownGuard1 from GuardSpawn0 that hunts the Terror (GetBadAss), until the Terror dies. | A kill hook on the breakout guards that summons row 9107 at GuardSpawn0, set against the Terror. The city's README records "the one extra guard comes once" as a choice: confirm with the user, then it is a small citylua.py change. |

### SCRIPTED (39)

| Map | Objects | Carried by |
|---|---|---|
| 1000terrors | Spawner0-13 | the map Lua's SPAWNS / `send(target, "spawn")` (convert.py); EndCount's Greater Demon at the third end-hall spawn |
| anskramkeep | ImpGateSpawner0-7 (Fish, Visible 0) | the imp gates (convert.py, AK_ImpGate.scr: five Imps, key 510 + k) |
| beethoven, frosgard, yanmirsfort | LobberPodA0, LobberPodB0, IceLobbercicle0, IceLobbercicle8 (CacheOnly) | the engine's Lobber pod launch (MM9_MONSTER_AI_PLAN.md); Yanmir's Fort's bugs also respawn through YanmirFort_BugSpawn.scr (convert.py RESPAWNS) |
| chasmofthedead | GhostSpawner (Visible 0), ApparitionCACHE_ONLY | `spawnGhost()`: an Apparition (9139) at the next of Apparition0-12 |
| dragonstadium | WingedMutantCache | `spawnMutants()` (Dragon.scr :SpawnMutants: 45 s, then 90, 180 ... s) |
| tasaracademy | Dagrell0 (CacheOnly) | DestructableProp0's SpawnObject "Dagrell Scale 0.75": the hidden crate Dagrell that Trigger4 shows |
| thronheimcity | GuardSpawn1 | Thronheimcity_BadAss.scr :GetExtraGuard: the hidden ExtraGuard of the breakout |
| wizardslab | GreaterDemonCACHEONLY | WizardMaster.scr's summon: citylua.py summons 9242 |
| yanmirsfort | Spawner0-6 | convert.py SPAWNERS (Trigger6-10, the Yetis' DeathTriggerTarget) |

### EXCLUDED (108)

| Map | Objects | Reason (checked against MM9's scripts) |
|---|---|---|
| 1000terrors | SquareObj0-63 (64, Fish, Visible 0) | ChessSquare.scr's squares: invisible script holders; the map Lua carries them as the boxes the static pieces attack |
| 1000terrors | LeverHand (posed PeasantM1) | WG_hand.scr :Init clears Visible, Solid and Gravity. :OnPlay, in the win cinema, plays an animation, but its `SetFlag Visible` is commented out, so the hand is never seen in MM9. |
| drangheimprison | DwarvenSmith1 | DrangheimSmith.scr :Main with p0 0 (bBearer) calls RemoveObject at once |
| hallofthegods | DragonAzure0, DragonAzure1 | `models\DragonAzure.abc` is in no MM9 archive (MODELS has no such file) and the class has no MONSTERS.txt row: MM9 cannot show them either (convert.py's omitted note corrected) |
| templeofhonk | Skeleton10, Skeleton11 (Honk, Honk2) | CacheOnly 1 (LithTech never spawns the object), and no script of the map spawns Honk or Honk2 (HonkLeader.scr and HonkFollower.scr have no Spawn) |
| thjorgard | ShopkeeperElfFemaleB8 (Hjarrand, RUDE 7) | MM9 parks this copy about 28 000 units outside the region (LT 13632, 71, -8640). No polygon of MM9's DAT lies under it, so it is unreachable in MM9 too. RUDE 7 opens from his placed copies in Thjorgard City and Thjorad Mine. |
| thronheimcity | Kira, Bjarni, Sigmund, Forad, Tryygva, Markel (AI), Sven (posed) | The Argument cinema's cast: ARG_*.scr only animate the cutscene, on its stage under the city, which is not built (convert.py STAGE_TOP_LT). The council itself is the six posed RUDEProps SvenProp ... BjarniProp, all placed. |
| yorwick | Kira, Kira0, Tryygva, guard, Sven, Sven0-16, Sven20-26 (29 posed figures) | The fallen of the battlefield. SvenShowTake.inc :RemoveAll, run by Svenspeech.scr :Init, hides them on every load except during the battlefield cutscene (key 95 without 97). That cutscene is later work; the reward (key 97) comes without it. |
| greatgate | Hanndl (map not rebuilt) | the lose-game cinema (LoseMan.scr, Losecam1-4): the `MM9LoseGame` movie of world.yml `partyDeath` (E6) |

## Check 2: dialogues

439 RUDE files; 411 opened by something in the installed content, 412 after the next Yanmir's Fort conversion.

**Unreachable, fixed:** RUDE 433 "Child". Yanmir's Fort's seven caged children (ChildFar0-3 and ChildNear0-2, NPCNbr
433.0, DoRude 1) had `CHILD_RUDE = 432`, which is the Afterworld Questioner's id. The use handler also never opened a
dialogue. MM9's YanmirChild.scr :OnUse exits FALSE, so the click goes on to its DoRude. Now the children carry 433,
and a click without key 7001 opens their dialogue ("I don't wanna answer any questions"); with the key they still
run for the teleporter (mm9r_yanmirsfort/convert.py).

**Unreachable because MM9 never opens them (24).** No DAT object of any map hosts them, and no script opens them,
neither through DoRude, NPCnnn.scr, NPC_nnn.wav, NPCNbr, RUDENPCId nor a script parameter:

- 94 Lord Kluso: NPC94.scr has no DoRude and no object runs it; Kluso's House's Count Kluso0 has no DoRude.
- 106 Ercc Bloodfist: only ErccSpeechOld.scr opens it, and no object runs that script. Sturmford City's Ercc (RUDEProp1)
  runs ErccSpeech.scr, which has no DoRude.
- 400 "Keys and Locks!!!!!": a developer test; only DeanTest.scr mentions it, and no object runs that script.
- 108, 136, 139, 164, 205, 222-232, 236, 342, 344, 345, 418: named townsfolk with no object in any MM9 map.

They need no host.

**Journal tables, not dialogues (3):** 997 Quest Notes, 998 Auto Notes, 999 Awards. They are read by
generate_mm9_quest_interactions.py and the journal.

**Hosts against placements:** every other placed DAT host shows its own MM9 id, or the map Lua opens it. All 15
hirelings in hirelings.txt also have a placed host in the world.

## Check 3: spawners and timed spawns

| Source | Status |
|---|---|
| `AISPAWN.txt` (ScenarioNbr 0 and 6: Goblin, Orc, Dwarf, Gargoyle, Troll, ...) | **unused by MM9's maps**. Only RESPAWN.scr, CampDirector.scr and Goblin/Zombie/DwarfCamp.scr read it, through `AISpawn<n>` objects, and no map has such an object or runs those scripts. Its classes are not MM9 monster rows. |
| Spawner objects (23) | 1000 Terrors 14 and Yanmir's Fort 7 converted; Thronheim City GuardSpawn1 converted, GuardSpawn0 converted (M23: citylua.py's kill hook) |
| SpawnMgr.scr / SpawnLoc.scr (1000 Terrors, Bathhouse, Lich Lab, Thjorad Mine), SpawnGeneric.scr, SpawnNjam.scr, EndCount.scr (1000 Terrors), SpawnNjamCameo.scr (Dark Passageway), Chasm_GhostSpawner.scr, AK_ImpGate.scr, YanmirFort_BugSpawn.scr, Isle_Summoner.scr (story.lua), Converter.scr (Lich Lab), WizardMaster.scr, BattleMan.scr (Frosgard City), Arena.scr / ArenaFight.scr, Atliwagon.scr (Guberland's bandits), Dragon.scr (mutants) | converted (the maps' Lua) |
| SixFires.inc (Afterworld, NPC336.scr) | **was missing, fixed**: :Retribution's 8 Horde Leaders (9131) and 4 Horde Warriors (9130) at BadGuys0/1 with Forad, and the Zombie, Ghast and five Frights of :Absolution (once) and :Rebirth (at every Skraelos exit with key 390, as MM9's) at BadGuys0/1 and GoodGuys0 (mm9r_afterworld_blv/regionlua.py `SPAWNS`). :Spawn and :GoodGuys (the clan soldiers' battle) have no caller in MM9: dead code. |
| LesserDemon.scr p0 1: a Greater Demon from the body at death | **was missing, fixed for the placed ones**: Bathhouse LesserDemon0 and 1000 Terrors LesserDemon13/14 (their kill hooks; 9242). **Done (M24)**: 1000 Terrors' spawned "LesserDemon ScriptParams 1" (Spawner8/13's DefaultSpawn and SpawnMgr), marked by the spawn's returned actor indices. |
| ChessBase.inc :Spawn "Terror" (1000 Terrors) | **converted (M24)**: ChessPiece1's attack on the last rank queens it into a Terror; the pieces are static otherwise, so ChessPiece0 never gets there (README) |
| BC_Manager.scr (Boot Camp) | converted (M22: regionlua.py `museum_lines`) |
| SpawnObject (DestructableProps) | Ta'Sar's crate Dagrell converted; the 22 TreasureBag drops are loot (C6) |
| SourceMan.scr, NightDwellers.scr, Isle_SpawnMgr.scr, SpawnTest.scr | no object in any map runs them |

## Converter changes (2026-11-06; no map converted)

- `mm9r_yanmirsfort/convert.py`: CHILD_RUDE 432 -> 433 and the children's dialogue on a click without the key.
- `mm9r_guberland_blv/overrides.yml` and `mm9r_common/outdoor_blv.py` `npcs()`. An `outdoor.people` value may now be
  `{name, monster_id}`, which gives a person whose class has no MM9 row the row of its model. Guberland's late guard
  AtliGuard (WealthyTownGuard1, guard.abc, atlipromo.scr) is now placed on the Guard row 9111, friendly, as
  Invent-a-Storca's guards are. `regionlua.py` hides him once relieved (key 197) and on load after that.
- `mm9r_afterworld_blv/regionlua.py`: SixFires.inc's stage spawns (`SPAWNS`, `spawn_lines`).
- `mm9r_bathhouse/convert.py`, `mm9r_1000terrors/convert.py`: LesserDemon.scr p0 1's Greater Demon (`GREATER_ON_DEATH`).
- Notes corrected: Hall of the Gods' DragonAzure omission reason; Yorwick's regionlua (Ewe0 is placed).
- `mm9r_common/actor_completeness.py`: this audit.

All the changed converters import, and the Afterworld spawn lines were generated against the DAT offline. They take
effect at R2.
