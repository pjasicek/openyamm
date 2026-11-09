# MM9 SCR audit, part 3 of 4: NPCs, quests, dialogue hooks, minigames, services

Audit of 2026-11-06 (report only: nothing converted, built or edited). The user's request: go through every MM9 `.scr`,
check that each is handled in some way and name the gaps, in particular where the engine behaviour exists and only
the data plumbing is missing. This part covers the 164 scripts of the scratch inventory's `cat_npc_quest_minigame.json`
and 15 includes of `cat_includes.json` that those scripts use for NPCs, quests and games (listed under
[Includes](#includes)). `healer.inc`, `checkstat.inc`, `thething.inc`, `theit.inc` and `traininghostility.inc` are left
to the other parts: no script of this list includes them.

**Sources.** MM9 scripts `mm9/extracted/SCRIPTS/SCRIPTS/`; RUDE `assets_dev/worlds/mm9/dialogue/rude/` (key columns as
`game/mm9/Mm9RudeDialogue.cpp`: required 7/9/11/13/15, granted 16-20, forbidden 21-25, removed 26-30, 1-based; a
service row applies its tail only for -10/-11); DAT objects `assets_editor_dev/worlds/mm9/maps/<stem>.raw_objects.yml`
(ScriptName, ScriptParams); the installed map Lua `assets_dev/worlds/mm9/events/maps/*.lua` and scenes (promoted on
2026-11-06 12:12, before the final rebuild R2); the converters `level_generation/projects/mm9r_*` (what R2 installs).
Rework event ids: RUDE exit 50000 + DAT index, click 53000 + index, FoundPlayer 56000 + index (`Mm9RudeDialogue.h`).

**Method.** Every `givekey`/`takekey`/`haskey`, item, gold, experience, promotion, `DoRude`, `OnRudeExit`,
`OnFoundPlayer`, `@M` schedule, spawn and removal of the 164 scripts was extracted with its line and handler, and the
objects that run each script were taken from the 44 DATs (all 164 are placed at least once). Every key a script
grants was matched against the rework's grantors: RUDE rows, installed Lua (`giveKey`, `reward`, `gameWon`, loops) and
converter sources (R2). Suspected gaps were confirmed with headless scenarios (below). Status words:
OK (carried; how verified in the row), PARTIAL (the quest effect is carried, something cosmetic or secondary is not),
MISSING_DATA (the engine can do it, the map Lua or data does not), MISSING_ENGINE (needs engine work), NOT_NEEDED
(checked: nothing to carry).

## Summary

| Status | Scripts (164) | Includes (15) |
| --- | --- | --- |
| MISSING_ENGINE | 0 | 0 |
| MISSING_DATA | 21 | 1 |
| PARTIAL | 23 | 2 |
| NOT_NEEDED | 14 | 2 |
| OK | 106 | 10 |

Quest keys granted by these scripts: 168 (literal and the includes' named constants). 149 have a grantor in the
installed rework, 5 arrive with the final rebuild (R2), 5 are granted only behind a dead gate (G2), 6 have no
grantor (2 of them quest-blocking: 194, 277; 466 blocks a side quest), 3 are not needed. Every item these scripts
give, take or test (61 raw ids, the games' tickets and prizes included) is in `MM9.ItemIds`
(`worlds/mm9/events/common/world_common.lua`). No reachable gap needs engine work; the four quest-blocking gaps are
map Lua in the converters.

## Gaps, by priority

Quest-blocking first. Each was confirmed by a headless scenario against `assets_dev` (files in the session
scratchpad `npcq/scen/`; `SDL_AUDIODRIVER=dummy ./build/game/openyamm --asset-root assets_dev --headless-run-scenario`).

| # | Gap | Effect | Fix type | Maps |
| --- | --- | --- | --- | --- |
| G1 (fixed) | Ivsar outside Drangheim Prison: NPC90.scr :OnUse (l.63-93, run by OnFoundPlayer on the two Drangheim-region copies "Drangheim Main"/"Drangheim Well", DAT 24 and 114, visible with key 17) gives key 194 and opens RUDE 90, whose row 7 (requires 194) gives 242. `drangheim.lua` has no Ivsar handler (`mm9r_drangheim_blv/regionlua.py`: "Not here"). Scenario `ivsar.yml`: the talk offers only "Come on, General." and "Sorry to bother you"; 194 stays clear. | 242 never set, so Sturmford's Ivsar stays hidden (`show(27, has(242))`), his exit never gives 196, Bjarni's "We've rescued Ivsar" (21) and the reward 117 (42 000 xp, 3 500 gold) never come, and Bjarni cannot join the coalition (NPC45 row 52: 41 + 21 -> 38). Five of the six jarls' clan checks (United.inc) need 38; key 83 (the war council, main quest) is then reachable only through Bjarni's own click check (82, 34, 51, 63, 74 -> 178) and another jarl's row. | MISSING_DATA: converter `mm9r_drangheim_blv/regionlua.py`: hide the copies without 17 and with 194/242 (:Init l.160-185), on a click (53000 + 24/114, or 56000 FoundPlayer) `MM9.giveKey(194); MM9.openRude(90)` and hide the other copy. | drangheim (effects: sturmfordcity, every jarl's city) |
| G2 (fixed) | Promotion quest starts gated on MM9's per-character keys: NPC161 :ScholarCheck (201, l.57-81), NPC128 :Promocheck (206, l.81-106), NPC129 :Givequest (250-252, l.85-113) give their quest key only while a member holds 425-428 / 437-440 / 441-444. No script or RUDE row sets 401-448 (probably MM9's engine, from the class-check codes 2075-2086 in column 16 of the "We are seeking promotion" rows); the rework kept the gates (`thjorgardcity.lua` l.124, `guberlandcity.lua` l.134, 142; `citylua.py` the same). Scenarios `scholar.yml`, `healer.yml`, `priest.yml`: 201, 206, 250 stay clear. | The Scholar (Magreeb), Healer (Nutty Nurtigan) and Priest (new temple) quests never start; downstream Mage (NPC4 needs 205), Priest (NPC129 row 2 needs 213) and Druid (NPC182 row 5 needs 213) are cut off: the whole magic promotion line in MM9. | MISSING_DATA: converters `mm9r_thjorgardcity/citylua.py`, `mm9r_guberlandcity/citylua.py`: replace the key loops by `MM9.canPromote("Scholar")`, `("Healer")`, `("Priest")` (the decided rule: a promotion shows while a member is eligible; D1's open item). Side note: those RUDE rows also set the raw codes as QBits 92075-92086 (harmless). | thjorgardcity, guberlandcity |
| G3 (fixed) | Frosgard's pledges: pledge.inc :Pledge/:CheckAllNPC/:reward (l.27-31, 41-130), run on the dialogue exit of NPC190/191/193/195/196/197/199 and Pledge.scr (217, 218), gives key 277 and 5 000 xp when at most one of the pledges 269-274 is missing (its loop never decides on 275, and its 7-slot array never reads 276; the journal asks for seven residents). Left out (`mm9r_frosgardcity/README.md` l.175). Scenario `pledge.yml`: with 265 and 269-275, closing Soxolf's (NPC190) talk leaves 277 clear. | The Green Man's "We have completed your tasks" (NPC221 row 11 requires 268, 277, 278) never shows: no key 279, so `frosgard.lua`'s reward (280, 63 000 xp, 5 000 gold, item 213, the Druid promotion) never runs. | MISSING_DATA: `mm9r_frosgardcity/citylua.py`: one shared exit handler for those eight objects (265, not 277: MM9's count of 269-274 with at most one missing, or a plain six of 269-276 -> 277, `balanced_experience(5000, 277)`, quest sound). | frosgardcity (effect: frosgard) |
| G4 (fixed) | Mary's sheep (Yorwick): MarySheep.scr :OnUse makes Ewe0 follow and signals Mary; NPC312 :RuntoMe (l.52) gives 466 when it comes within 512 of her. Not carried: Ewe0 placed (M19) but no follow (`mm9r_yorwick_blv/regionlua.py` l.22-25). | RUDE 312 row 15 "Here's your sheep" (requires 466) never shows: no 467, so the 20 000 xp reward (468) cannot be earned. Side quest. | MISSING_DATA: `regionlua.py`: a click on Ewe0 (53000 + 249) starts a follow by `evt.MoveActorTo` to the party on the poll; within 512 LT of Mary: `MM9.giveKey(466)` and the ewe runs to her. A true follower behaviour would be engine work, not needed here. | yorwick |
| G5 (fixed) | Guberland's stones game and whack-a-honky (StonesGame.scr, Whack-a-Honky.scr) not carried (`mm9r_guberland_blv/regionlua.py` l.21). | Two of the five Gathering games missing; their keys 7110/7113 have no reader and the random prize (362-367, needed six times for NPC133's Capstone of Order) still comes from the bell, the runes and arm wrestling. Not blocking. | MISSING_DATA: reuse Thjorgard's generated game Lua (`mm9r_thjorgard_blv/regionlua.py`) with Guberland's objects (TronMgr 266, Honky0-3 325-328). | guberland |
| G6 | NPC voices on a click: most NPC scripts' :OnUse plays `voices\NPC\NPC_<id>.wav` (Shopkeeper.scr param 0, NPCxxx.scr, Retainer.scr); 192 voices are imported, but only four maps play any (afterworld, bootcamp, wizardslab, isleofashes). | Cosmetic, well over 100 actors. | **fixed 2026-11-06 (night)**: the shared rule dungeon/voices.py + objects.py `voice_lines`: each placed actor whose script's :OnUse plays a voice and whose click (53000 + index) the map's Lua does not take plays it, then opens its RUDE | all cities and regions (reconverted) |
| G7 | Ambient scenes not carried: the Guberland Players' show (Narrator, Abriel, Trislan, Ralof, Wilam, Leffery; voices `cinema/guberlandplay` imported), the Temple of Honk ceremony and accountant round (HonkLeader, HonkFollower, HonkAccountant @M), Ercc's and Tryggva's rants in Sturmford, Ake's four places, the Thjorad miners' work loop, Ta'Sar's guards off duty at night, Thorolf's walk-up (carried 2026-11-07, all six cities), Hatlati's noon stealing walk, Yanmir's children following, the spectators' cheers, the chess pieces' moves. | Cosmetic; no key any quest reads (Ercc's 113 is read only by Ercc). | **partly fixed 2026-11-06 (night)**: the Guberland Players' show (voices at the stage, 14:30 and 16:30, the curtain; actors not placed), the Temple of Honk ceremony (bell, the leader's preaching and pacing; the followers' walk not carried), Ercc's and Tryggva's barks (AMBIENT_SOUNDS.md "Scripted voices and scenes"). The rest open (walks: evt.MoveActorTo per map) | guberlandcity, templeofhonk, sturmfordcity; others open |
| G8 | Waiting for R2 (converter done, installed Lua older): keys 111 (bob_and_doug), 114 (Knut), 5020 (newgame_talk), 492 (Absolution), 494 (Forad's death, 194 000 xp capped), Tamur joining (`MM9.addHireling(309)`), Forad leaving at the council (`removeHireling(2)`), the council, battlefield and dwarves-and-humans cinematics, M23 breakout, AtliGuard placement, Yanmir's children RUDE 433. | None once R2 is installed. | Check after R2: grep the installed Lua for these keys and calls. | frosgardcity, thronheimcity, guberland, afterworld, yorwick, drangheimcity, yanmirsfort |

**Fixed 2026-11-06 evening** (converters; converted into the review roots, not yet promoted; scenarios beside each
project, all PASS in the review roots):

| Item | Fix | Scenario |
| --- | --- | --- |
| G1 Ivsar | `mm9r_drangheim_blv/regionlua.py` `ivsar()`: both copies shown with 17 until 242; click (53024/53114) or FoundPlayer (56024/56114): key 194, the other copy hidden, voice, RUDE 90; exit with 242: 194 taken, both hidden | `scenario_ivsar.yml` (row "What is it, General?" offered, 242 given) |
| G2 Scholar, Healer, Priest | `mm9r_thjorgardcity/citylua.py`, `mm9r_guberlandcity/citylua.py`: the quest key once the promotion row was asked (its code key 2081 / 2083 / 2084) and `MM9.canPromote("Scholar" / "Healer" / "Priest")` | `scenario_promotions.yml` in both (no quest before the row, quest after it) |
| G3 pledges | `mm9r_frosgardcity/citylua.py` `pledge()` on the exits of NPC190/191/193/195/196/197/199 and Pledge.scr 217/218: 265, at most one of 269-274 missing -> 277, `balanced_experience(5000, 277)`, quest sound | `scenario_pledges.yml` (two missing: nothing; one missing: 277) |
| G4 Mary's sheep | `mm9r_yorwick_blv/regionlua.py` `ewe()` + overrides.yml (Ewe0 moved from `monster_classes` to `outdoor.people`, so its click runs 53249): the click starts a half-second `evt.MoveActorTo` follow; within 512 LT of Mary: 466 and the ewe runs to her | `scenario_sheep.yml` (466, then 467 and the 468 reward) |
| G5 Guberland games | `mm9r_guberland_blv/regionlua.py` `stones_game()`, `whack_a_honky()` (Thjorgard's, keys 7110/7113, prize 7116); overrides.yml Switch0 a `rotate` mover (event 104); pieces/geese events and cogs 700-739 | `scenario_games.yml` (7113, 7116, a won stones game 7110) |
| Magreebs' 202 (Lindisfarne) | `mm9r_lindisfarne_blv/regionlua.py` `magreeb_lines()`: a 1 s poll, any of the 16 Magreebs seeing the party (`evt.ActorSeesParty`, its SightDistance) during 201 gives 202 | `scenario_magreeb.yml` |
| Njam's chase (Arslegard) | `mm9r_arslegardcity/citylua.py` `njamChase()` sends `evt.TriggerActor(34, "Chase")` | `scenario_njam.yml` (Njam targets the party) |
| Six Fires (Afterworld) | `mm9r_afterworld_blv/regionlua.py` `populate()` (a new optional hook in `mm9r_common/outdoor_blv.py` populate) places the six fires (mm9_gatefire_x8, cogs 420-425); `sixFires()` on load, after Skraelos' click/exit and Forad's death: Guilt 381, Confession 383, Suffering 491, Retribution 387, Absolution 389, Rebirth 391 (MM9 never lights GuiltFire) | `scenario_fires.yml` |
| Town Portal | `engine/data_tables/town_portal_switch.txt`: new group `TPChedian` (six rows, maps 9001-9014, the scenes' TownPortal start points, QBits 95011-95016; icon boxes from MM9's TOWNPORTAL-COORDS.txt x 0.8). **Open**: the engine picks the group by map id (`GameplayUiRuntime.cpp` `townPortalGroupNameForMap`: MM9 maps fall to Jadame's `townport`), and the art (TOWNPORTALBG.pcx and the six city buttons as `tpchedian` and `tp<city>` icons) is not imported | Town Portal doctests pass; MM8 table load |

Not gaps (checked): the windows of Sturmford's tavern and temple (Sturmgaardinn.scr, Beathag.scr :OnBreak, keys 5000,
5002) only start a pay-for-the-glass penalty and the rework has no breakable windows; Guberland has no boat race
(7111); NPC9.scr's OnRude exits at once; the Old Hag's hair comes from the hairbrush (her :GiveHair hangs on a
commented-out OnDamage); NPC241/Retainer/Thronheim actors' `NPCBase.inc` socialising is shared AI by contract.

## Quest-key coverage

Every key the 164 scripts and their includes grant. MM9 grantor: script:line handler. Rework grantor: RUDE file
or installed map Lua (first few); R2: only in the converter today. GATED: granted, but behind G2's dead condition.

| Key | MM9 grantor | Rework grantor | Status |
| --- | --- | --- | --- |
| 40 | argument:50 War | LUA:thronheimcity, RUDE:NPC400 | OK |
| 77 | honkies:69 Reward | LUA:thronheimcity, RUDE:NPC400 | OK |
| 85 | argument:51 War | LUA:thronheimcity | OK |
| 93 | argument:57 War | LUA:thronheimcity, RUDE:NPC1 | OK |
| 94 | thjorgardgamescommon.inc:147 GiveThjorgardPrize | LUA:thjorgard, RUDE:NPC400 | OK |
| 97 | svenspeech:197 Award | LUA:yorwick, RUDE:NPC400 | OK |
| 102 | npc336:309 OnReborn | LUA:afterworld, RUDE:NPC400 | OK |
| 111 | npc214:31 OnStart | bob_and_doug | R2 |
| 113 | erccspeech:25 OnBlabber | cosmetic (Ercc rant), nothing reads it | MISSING |
| 114 | knutspeech:36 Speak | council.py Knut rant | R2 |
| 116 | ludwigvan:26 OnRude | LUA:sturmfordcity | OK |
| 117 | bjarni:96 Ivsar | LUA:sturmfordcity | OK |
| 122 | npc133:80 Nicolai | LUA:guberland | OK |
| 127 | npc186:69 Mercpromo | LUA:guberland | OK |
| 137 | npc89:56 crusaderpromo | LUA:drangheimcity | OK |
| 146 | npc239:148 honkys | LUA:thronheimcity | OK |
| 147 | npc239:122 loveletter | LUA:thronheimcity | OK |
| 149 | bjarni:189 Anskram | LUA:sturmfordcity | OK |
| 150 | bjarni:128 Loveletter | LUA:sturmfordcity | OK |
| 151 | bjarni:148 loveletter2; bjarni:160 loveletter2 | LUA:sturmfordcity | OK |
| 152 | npc239:173 MountainPass | LUA:thronheimcity | OK |
| 163 | npc3:102 Thjorad | LUA:arslegardcity, LUA:thjorgardcity | OK |
| 164 | npc130:40 Trivia | LUA:guberland | OK |
| 165 | npc127:125 Ivan | LUA:guberlandcity | OK |
| 167 | npc127:93 Bookofrules | LUA:guberlandcity | OK |
| 168 | npc127:157 Dook | LUA:guberlandcity | OK |
| 170 | npc87:150 CronaKiga | LUA:drangheimcity | OK |
| 171 | npc87:117 FortStenig | LUA:drangheimcity | OK |
| 172 | npc180:100 Yanmir | LUA:frosgardcity | OK |
| 175 | npc180:133 Breakice | LUA:frosgardcity | OK |
| 177 | npc3:135 Refinery | LUA:arslegardcity, LUA:thjorgardcity | OK |
| 178 | united.inc:140 CheckAllClansloop; united.inc:98 OnCheck | LUA:arslegardcity, LUA:drangheimcity, LUA:frosgardcity, LUA:guberlandcity, LUA:sturmfordci | OK |
| 179 | united.inc:48 United | LUA:arslegardcity, LUA:drangheimcity, LUA:frosgardcity, LUA:guberlandcity, LUA:sturmfordci | OK |
| 180 | npc239:210 givekey | LUA:thronheimcity | OK |
| 181 | npc239:97 treaty | LUA:thronheimcity | OK |
| 184 | argument:49 War | LUA:thronheimcity | OK |
| 185 | argument:77 OnRude | LUA:thronheimcity | OK |
| 186 | npc244:44 Prize | LUA:thronheim | OK |
| 187 | npc338:54 darkpass | LUA:darkpassageway | OK |
| 188 | npc133:55 Capstone; npc338:44 darkpass | LUA:darkpassageway, LUA:guberland | OK |
| 189 | npc336:130 sixfires | LUA:hallofthegods | OK |
| 190 | npc309:46 StopTamur | LUA:frosgardcity | OK |
| 191 | npc335:49 StopNjam | LUA:hallofthegods | OK |
| 194 | npc90:70 OnUse | drangheim regionlua `ivsar()` (converted, not promoted) | FIXED |
| 196 | npc90:140 FollowPlayer | LUA:sturmfordcity | OK |
| 197 | atlipromo:29 OnLeave | LUA:guberland | OK |
| 198 | npc92:45 Herbs | LUA:drangheim | OK |
| 199 | npc93:48 dolly | LUA:drangheim | OK |
| 200 | npc91:49 Plow | LUA:drangheim | OK |
| 201 | npc161:66 ScholarCheck; npc161:71 ScholarCheck; npc161:76 ScholarCheck; npc161:81 ScholarCheck | thjorgardcity citylua: 2081 + canPromote (converted, not promoted) | FIXED |
| 202 | scholarpromo:28 RunAway | LUA:thjorgard | OK |
| 205 | npc161:127 ToScholar; npc161:140 ToScholar | LUA:thjorgardcity | OK |
| 206 | npc128:100 Promocheck; npc128:106 Promocheck; npc128:88 Promocheck; npc128:94 Promocheck | guberlandcity citylua: 2083 + canPromote (converted, not promoted) | FIXED |
| 207 | npc132:39 GiveHair; npc142:83 OnUse | LUA:guberlandcity | OK |
| 209 | npc142:70 Givekey | LUA:guberlandcity | OK |
| 213 | npc128:121 Nurtigan | LUA:guberlandcity | OK |
| 215 | bjarni:212 OnUse; bjarni:221 OnUse; npc61:144 OnUse; npc61:153 OnUse | LUA:sturmfordcity | OK |
| 217 | arena:293 Onuse; arena:388 FightWin | LUA:thearena | OK |
| 221 | npc61:84 Gladiator | LUA:sturmfordcity | OK |
| 225 | npc95:33 OnDeath | LUA:drangheimcity | OK |
| 227 | npc88:96 promo | LUA:drangheimcity | OK |
| 229 | npc282:111 giveletter | LUA:lindisfarnemonastery | OK |
| 233 | npc416:36 OnDeath | LUA:thjorgardcity | OK |
| 235 | npc3:77 Lifesaver; npc3:82 Lifesaver | LUA:arslegardcity, LUA:thjorgardcity | OK |
| 237 | npc282:97 paladins | LUA:lindisfarnemonastery | OK |
| 241 | npc181:114 OnUse | LUA:frosgardcity | OK |
| 244 | npc417:50 OnTrap | LUA:dungeonofsecrets | OK |
| 245 | npc417:74 OnFinish | LUA:dungeonofsecrets | OK |
| 247 | npc417:33 Secrets | LUA:dungeonofsecrets | OK |
| 249 | npc181:63 Ranger | LUA:frosgardcity | OK |
| 250 | npc129:103 Givequest; npc129:111 Givequest; npc129:87 Givequest; npc129:95 Givequest | guberlandcity citylua: 2084 + canPromote (converted, not promoted) | FIXED |
| 251 | npc129:104 Givequest; npc129:112 Givequest; npc129:88 Givequest; npc129:96 Givequest | as 250 | FIXED |
| 252 | npc129:105 Givequest; npc129:113 Givequest; npc129:89 Givequest; npc129:97 Givequest | as 250 | FIXED |
| 254 | npc283:51 GiveKey | LUA:lindisfarnemonastery | OK |
| 258 | npc188:36 ritual | LUA:frosgardcity | OK |
| 261 | npc129:131 priest | LUA:guberlandcity | OK |
| 268 | npc190:36 Maypole | LUA:frosgardcity | OK |
| 277 | pledge.inc:29 reward | frosgardcity citylua `pledge()` (converted, not promoted) | FIXED |
| 280 | npc221:48 Promo | LUA:frosgard | OK |
| 288 | npc4:63 toMageOne | LUA:thjorgardcity | OK |
| 294 | npc4:83 Reward | LUA:thjorgardcity | OK |
| 300 | npc87:95 Gossip | LUA:drangheimcity | OK |
| 303 | npc184:31 GiveKeg | LUA:frosgardcity | OK |
| 306 | npc141:34 takeKeg | LUA:guberlandcity | OK |
| 308 | npc184:55 Reward | LUA:frosgardcity | OK |
| 310 | npc184:80 BadReward | LUA:frosgardcity | OK |
| 313 | npc55:33 BlackOrb | LUA:wizardslab | OK |
| 315 | npc241:31 BlackOrb | LUA:thronheimcity | OK |
| 317 | npc242:60 GiveBadNews | LUA:thronheimcity | OK |
| 319 | npc246:42 TakeBadNews | LUA:thronheimcity | OK |
| 321 | npc242:32 Reward | LUA:thronheimcity | OK |
| 323 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:thjorgardcity | OK |
| 324 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:sturmfordcity | OK |
| 325 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:drangheimcity | OK |
| 326 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:guberlandcity | OK |
| 327 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:frosgardcity | OK |
| 328 | bankorb/bankorb.inc :OnRude givekey nKey2 | LUA:thronheimcity | OK |
| 330 | bankorb:43 OnUse; npc206:43 OnBank | LUA:drangheimcity, LUA:frosgardcity, LUA:guberlandcity, LUA:sturmfordcity, LUA:thjorgardci | OK |
| 337 | bankorb.inc:90 CheckAll; bankorb:108 CheckAll | LUA:drangheimcity, LUA:frosgardcity, LUA:guberlandcity, LUA:sturmfordcity, LUA:thjorgardci | OK |
| 342 | npc283:32 MissingRelic | LUA:lindisfarnemonastery | OK |
| 344 | honk:22 Onuse | templeofhonk.lua (`taken` = 344 or 345) | OK |
| 345 | honk:34 Onuse | templeofhonk.lua (`taken`) | OK |
| 347 | npc337:36 GoldenHonk | LUA:hallofthegods | OK |
| 354 | npc334:64 OnUse | LUA:arslegardcity | OK |
| 357 | npc334:41 Gungnir | LUA:arslegardcity | OK |
| 362 | npc7:138 Payment; npc7:159 Payment | LUA:thjorgardcity | OK |
| 363 | npc7:142 Payment; npc7:164 Payment | LUA:thjorgardcity | OK |
| 364 | npc7:257 OnMarkMachine | LUA:thjoradmine | OK |
| 368 | forad:73 Forad | LUA:frosgardcity, LUA:isleofashes | OK |
| 370 | npc427:21 OnRude | LUA:drangheimprison | OK |
| 373 | npc142:33 givePotion | LUA:guberlandcity | OK |
| 376 | atlipromo:56 Givekey | LUA:guberland | OK |
| 378 | npc209:40 Book | LUA:frosgardcity | OK |
| 379 | npc336:111 Teleport; npc336:151 DoRude | LUA:afterworld, LUA:hallofthegods | OK |
| 381 | npc336:292 OnDone | LUA:afterworld | OK |
| 383 | npc336:211 OnUse | LUA:afterworld | OK |
| 389 | npc336:263 OnUse | LUA:afterworld | OK |
| 391 | npc336:308 OnReborn | LUA:afterworld | OK |
| 395 | npc5:104 OnUse; npc5:110 OnUse; npc5:98 OnUse | LUA:thjorgardcity | OK |
| 396 | npc5:99 OnUse | LUA:thjorgardcity | OK |
| 397 | npc5:105 OnUse | LUA:thjorgardcity | OK |
| 398 | npc5:111 OnUse | LUA:thjorgardcity | OK |
| 466 | npc312:52 RuntoMe | yorwick regionlua `ewe()` (converted, not promoted) | FIXED |
| 468 | npc312:32 OnRude | LUA:yorwick | OK |
| 471 | spieslikeus:26 OnRude | LUA:sturmfordcity | OK |
| 473 | npc436:72 OnLeave | LUA:bootcamp | OK |
| 476 | npc338:53 darkpass | LUA:darkpassageway, RUDE:NPC338 | OK |
| 480 | forad:28 OnUse | LUA:frosgardcity, LUA:isleofashes | OK |
| 486 | npc3:58 GoGetEm | LUA:arslegardcity, LUA:thjorgardcity | OK |
| 487 | npc133:132 ItemCheck | LUA:guberland | OK |
| 489 | npc87:76 OnRude | LUA:drangheimcity | OK |
| 490 | npc133:32 OnRude | LUA:guberland | OK |
| 491 | sixfires.inc:206 Suffering | LUA:afterworld | OK |
| 492 | sixfires.inc:287 Absolution | afterworld regionlua Absolution | R2 |
| 494 | forad:157 OnDeath | frosgardcity citylua Forad.scr :OnDeath | R2 |
| 495 | randverrun:32 OnRudeExit2 | LUA:sturmfordcity | OK |
| 496 | npc436:22 OnRude | LUA:bootcamp | OK |
| 1009 | arena:228 Init; arena:391 FightWin | LUA:thearena | OK |
| 1018 | arena:363 OnMonsterAWin; arena:376 OnMonsterBWin | LUA:thearena | OK |
| 1020 | arenafight:525 OnDead | LUA:thearena | OK |
| 1034 | svenarena:130 OnUse | LUA:thearena | OK |
| 5000 | sturmgaardinn:49 OnBreak | no breakable tavern window | NOT_NEEDED |
| 5002 | beathag:47 OnBreak | no breakable temple windows | NOT_NEEDED |
| 5005 | npc419:21 OnRude | LUA:drangheimprison | OK |
| 5006 | drangheimhostility.inc:100 TurnHostilityOn; guardhelp:53 OnDamage; guardrude:55 OnDamage; guardtonegate:111 Se | LUA:drangheimprison, RUDE:NPC426 | OK |
| 5008 | sturmguard:29 OnUse | LUA:sturmfordcity | OK |
| 5009 | npc48:141 Init | LUA:sturmfordcity | OK |
| 5010 | npc110:44 OnStart | LUA:drangheimcity | OK |
| 5020 | npc150:34 OnStart | newgame_talk cinematic | R2 |
| 5021 | sixfires.inc:245 Retribution | LUA:afterworld | OK |
| 7000 | honkkey:70 GivePlayerKey | LUA:templeofhonk | OK |
| 7002 | stonesplayer:38 OnRudeEnter | LUA:guberland, LUA:thjorgard | OK |
| 7100 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7101 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7102 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7103 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7104 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7105 | thjorgardgamescommon.inc :Record*Win | LUA:thjorgard | OK |
| 7106 | thjorgardgamescommon.inc:140 GiveThjorgardPrize | LUA:thjorgard | OK |
| 7110 | thjorgardgamescommon.inc :Record*Win | guberland regionlua `stones_game()` (converted, not promoted) | FIXED |
| 7111 | thjorgardgamescommon.inc :Record*Win | Guberland has no boat race in its DAT (RacingBoat.scr is Thjorgard only) | NOT_NEEDED |
| 7112 | thjorgardgamescommon.inc :Record*Win | LUA:guberland | OK |
| 7113 | thjorgardgamescommon.inc :Record*Win | guberland regionlua `whack_a_honky()` (converted, not promoted) | FIXED |
| 7114 | thjorgardgamescommon.inc :Record*Win | LUA:guberland | OK |
| 7115 | thjorgardgamescommon.inc :Record*Win | LUA:guberland | OK |
| 7116 | thjorgardgamescommon.inc:155 GiveGuberlandPrize | LUA:guberland | OK |
| 9511 | npc8:96 OnExit | LUA:thjoradmine | OK |
| 9514 | npc5:76 Refinery | LUA:thjorgardcity | OK |

Keys these scripts test that nothing in the rework grants (besides the above): MM9's per-character keys 401-448
(G2; the rework promotes by class, `MM9.promoteParty`) and 375 (GreatBookKey's 'appear', which nothing in MM9 sends
either). Hire keys 450-462 come from `hirelings.txt` (engine hire service).

## Minigames and services

| Game or service | MM9 scripts | Rework | Status |
| --- | --- | --- | --- |
| The Thing, Thjorgard: tickets, stones, boat race, runes, bell, whack-a-honky, arm wrestling -> Stuffed Dragon + key 94 (Yrsa's errand) | ThjorgardGamesCommon.inc, StonesGame/Player, Whack-a-Honky, ArmWrestle (+ boat, bell, mastermind scripts of other parts) | `thjorgard.lua` l.57-430; `scenario_games.yml` PASS (this audit) | OK |
| The Gathering, Guberland: tickets, bell, runes, arm wrestling, stones, whack-a-honky -> random prize 362-367 | same | bell, runes, arm wrestling, tickets carried; stones and whack-a-honky not | PARTIAL (G5) |
| The Arena: rank fights (Page to Lord), bouts to bet on (50-1 000 gold), Sven's double and Byri | Arena, ArenaFight, SvenArena, NPC245, PickMon.inc | `thearena.lua`; `scenario_sven.yml` PASS (this audit); scenario_bout/fight/lord exist | OK |
| Chess, 1000 Terrors | ChessSquare/Pawn/Knight/Bishop/Camera, ChessBase.inc | attacked squares hurt, capture camera, pawn queening (R2); pieces static | PARTIAL |
| HONK buttons puzzle, Temple of Honk | HonkSecretDoor, HonkKey | `templeofhonk.lua` | OK |
| Banks (Orb of Linking quest) | BankOrb.scr/.inc, NPC206 | five city Lua + Frosgard; bank service -6 | OK |
| Hirelings hidden while hired | Retainer, AkeRetainer, RandverRetainer | `show(..., not has(key))` in eight maps; hire/dismiss -10/-11 in the engine | OK |
| Promotions | NPC4, 61, 88, 89, 128, 129, 161, 181, 186, 221, 282 GivePromo | `MM9.promoteParty` in every handler | OK for the might line; magic line blocked by G2/G3 |
| Drinking, races, betting outside the Arena | Tryggva's 'Ondrink' is a rant animation only; no other betting or drinking script in this list | - | NOT_NEEDED |

## Detail per script

Maps: the DAT maps whose objects run the script (count when more than one). Line numbers are the MM9 script's; the
rework column names the installed Lua (map, approximate lines) or converter.

| Script | Maps | MM9 | Rework | Status |
| --- | --- | --- | --- | --- |
| abriel.scr | guberlandcity | Guberland Players show actor (OnWalk/OnSpeak*, voices cinema/guberlandplay, slap, bow); no keys | the show's voices play at the speakers' places (citylua play_lines, THEPLAY.scr's timeline, 14:30/16:30); actors not placed, walks not carried | PARTIAL |
| ak_giantimpguard.scr | anskramkeep 2 | Anskram Giant Imp guards: no gravity until Appear, Die on damage | anskramkeep.lua Imp gates block: guards appear with the Giant Imp (AK_GiantImp) | OK |
| ake.scr | thronheimcity | Ake socialism blabber; four positions by key 114 | installed: none; R2 rant carries 114; Ake's four-place cycle not carried | PARTIAL |
| akeretainer.scr | sturmfordcity | Ake hidden while hired (454), blabber | sturmfordcity.lua SetSprite 404 | OK |
| arena.scr | thearena | Arena Master: bouts (PickMon), betting 50-1000 gold (keys 1012-1016), fights by rank 1004-1007, wins 1009/1018/1020/217, gold | thearena.lua scheduler; scenario_bout/fight/lord/sven pass (sven run here: PASS) | OK |
| arenafight.scr | thearena | Page/Squire/Knight/Lord fights by party level, OnDead 1020 + reward | thearena.lua fights; scenario_fight.yml | OK |
| argument.scr | thronheimcity | war council: 184, 40, 85, 93, 26500 xp, item 401 taken; RemoveNPC 2; cinema | installed: reward at once; council_argument cinematic + removeHireling(2) at R2 (council.py) | OK |
| armwrestle.scr | guberland, thjorgard | might contest with ticket (ThjorgardGamesCommon) | thjorgard.lua + guberland.lua (53330); scenario_games.yml PASS | OK |
| atlipromo.scr | guberland | late guard relief @m 2:45/3:15 (376), leaves -> 197 | guberland.lua relief poll (RELIEF_RADIUS); AtliGuard placed (M21, R2) | OK |
| bankorb.scr | drangheimcity, guberlandcity, sturmfordcity, thjorgardcity, thronheimcity | Orb of Linking: click with item 252 + 322 -> 330; exit places it (nKey2 323-328), 6 orbs -> 337 + 20000 xp + 15000 gold | all five city Lua (BankOrb blocks); guberlandcity scenario | OK |
| beathag.scr | sturmfordcity | temple window broken -> 5002 (:OnBreak l.47); pay 700 on exit | windows are glass faces (not breakable): the penalty never starts; pay branch carried | NOT_NEEDED |
| bjarni.scr | sturmfordcity | Ivsar (21 -> 117, 42000 xp, 3500 g), love letter (22 -> item 247, 150; 24/25 -> 151), Anskram (41 -> 149), Basilisk skin 215, United.inc | sturmfordcity.lua l.234-245 all carried; but 21 is unreachable (Ivsar chain, gap G1) | PARTIAL |
| chessbishop.scr | 1000terrors 2 | bishop attacks diagonals, slides onto party square | squares hurt (60) while attacker on board; pieces static | PARTIAL |
| chesscamera.scr | 1000terrors | capture camera + letterbox | cinematic chess_capture_<k> (C11, at R2) | OK |
| chessknight.scr | 1000terrors 2 | knight attacks | as bishop | PARTIAL |
| chesspawn.scr | 1000terrors 2 | pawn attacks, PawnToQueen -> Terror | ChessPiece1 queens (M24, R2); ChessPiece0 never moves | PARTIAL |
| chesssquare.scr | 1000terrors 64 | 64 squares ping attackers on touch | 1000terrors.lua CHESS boxes poll | OK |
| darkp_npcdie.scr | darkpassageway | Dark Passageway adventurer struck down (Die, GaveTreasure) | darkpassageway.lua Colloidal Warrior block | OK |
| dookguardbasic.scr | dookscastle 16 | DookHostility.inc guard (friend until DOOK_HOSTILITY removed) | dookscastle.lua guards block (hostility on secret door / hurt guard) | OK |
| dorude.scr | lindisfarne, thronheimcity | generic DoRude NPC_ID on use (Lindisfarne monk 305) | engine opens RUDE on click | OK |
| dp_patrol.scr | drangheimprison 2 | patrol marker walk; its objects have ExecuteScript 0 (nothing starts it) | B7: prison guards stand at posts (MM9 same) | NOT_NEEDED |
| drangheimdoorman.scr | drangheimprison | interrogation-room doorman (OpenRoom/CloseRoom) | drangheimprison.lua interrogation block | OK |
| drangheimguardbasic.scr | drangheimprison 6 | DrangheimHostility.inc guard only | drangheimprison.lua pass/alarm block (keys 5006/5007) | OK |
| drangheiminterrogator.scr | drangheimprison | escorts 3 prisoners, beatings, link-broken stop | drangheimprison.lua interrogation block | OK |
| drangheimsmith.scr | drangheimprison 2 | smith anvil loop, sounds, attached props | drangheimprison.lua smith (hammers while grate shut); DwarvenSmith1 removed as MM9 | OK |
| drangheimwarden.scr | drangheimprison | opens/closes cells for the interrogator | drangheimprison.lua interrogation block | OK |
| dwarvenminer.scr | thjoradmine 6 | Thjorad miners mine/dump loop with props; OnRudeEnter/Exit pause | placed and talk; work loop not carried (cosmetic) | PARTIAL |
| erccspeech.scr | sturmfordcity | Ercc rant on Blabber: key 113 (self-only), anims, voices ercc01/02 | Ercc's rant: Trigger1/2, key 113, ercc01 and ercc02 at him (citylua barks) | OK |
| forad.scr | frosgardcity, isleofashes | Forad: first click 480/800 xp; 368/4000 xp; gone on 29; OnDeath 494 + 194000 xp; DoRude 2 | frosgardcity.lua l.195-205, isleofashes story; death award at R2 | OK |
| greenparty.scr | inventastorca 9 | Invent-a-Storca dead party KillThem -> Die | inventastorca.lua IS_KillingLich block | OK |
| guardhelp.scr | drangheimprison 3 | prison helpers: pass check (5007), alarm 5006 on damage | drangheimprison.lua pass/alarm | OK |
| guardrude.scr | drangheimprison 3 | gate guards: DoRude 425/426, alarm 5006, give Visitor's Pass item 446 (:OnMove l.87-91) | drangheimprison.lua gate guards; scenario_quests.yml | OK |
| guardtonegate.scr | drangheimprison 3 | barracks guards vs Nagate; alarm 5006 (l.93,111) | drangheimprison.lua barracks block | OK |
| hidemodel.scr | frosgardcity, isleofashes, yorwick | prop/actor shown by key (Frosgard 278, Isle 28, Yorwick 102) | frosgardcity, isleofashes, yorwick Lua | OK |
| honk.scr | templeofhonk | Golden Honk item 369; key 344 (on quest 343) or 345; hostility | templeofhonk.lua l.121-132 (`taken` variable) | OK |
| honkaccountant.scr | templeofhonk | @M 7:00/19:00 money round, chest, key-theft watch (KeyWasStolen) | theft-under-eyes hostility done (HonkKey block); round walk not carried | PARTIAL |
| honkfollower.scr | templeofhonk 12 | @M 6:15/18:15 ceremony walk to the pulpit, gong | the leader's ceremony runs (bell, preaching); the followers' walk to the pulpit not carried | PARTIAL |
| honkfollowgoose.scr | templeofhonk 2 | two big geese follow/run | geese left out (no runtime row; README), cosmetic | NOT_NEEDED |
| honkfollowgoose2.scr | templeofhonk 2 | as above, hostile variant | as above | NOT_NEEDED |
| honkies.scr | thronheimcity 3 | missionaries: 145 + persuaded 142-144 leave; third 77 + 8000 xp | thronheimcity.lua l.129-145 | OK |
| honkkey.scr | templeofhonk | accountant key: item 445 + key 7000; theft turns Honks hostile | templeofhonk.lua; scenario_scripted.yml | OK |
| honkleader.scr | templeofhonk | ceremony leader: gong, sermon strings | bell at 6:15/18:15, thunder preaching and pacing (evt.MoveActorTo) until 6:45/18:45 (convert.py ceremony_lines) | OK (followers PARTIAL) |
| honksecretdoor.scr | templeofhonk | H-O-N-K buttons need key 7000 | templeofhonk.lua buttons/secret door | OK |
| is_dyingnpc.scr | inventastorca | dying adventurer killed by the Lich King | inventastorca.lua IS_KillingLich block | OK |
| klusoshidden.scr | klusoshouse 7 | hidden guards wake on object-link broken (RunScript baseMelee) | klusoshouse.lua; scenario_scripted.yml | OK |
| klusospatrol.scr | klusoshouse 4 | patrol traverse, AlertOthers, HuntPlayer | path walkers via mm9_ai (overrides.yml); alert chain by shared AI | PARTIAL |
| klusossleeper.scr | klusoshouse 8 | sleepers wake on link broken | klusoshouse.lua; mm9_ai_placement dormancy trigger | OK |
| knutspeech.scr | thronheimcity | Knut rant on first sight: key 114, 91 s speech | installed: none; council.py ambient rant + giveKey(114) at R2 | OK |
| leffery.scr | guberlandcity | same show (Guberland City Leffery, not the Abbot) | the show's voices play at the speakers' places (citylua play_lines, THEPLAY.scr's timeline, 14:30/16:30); actors not placed, walks not carried | PARTIAL |
| ludwigvan.scr | sturmfordcity | Ludwig: 19 -> 116, item 248 taken | sturmfordcity.lua l.227-231; scenario_scripted | OK |
| monkguardbasic.scr | lindisfarnemonastery 19 | monks pray/work/fidget; DoRude MONK_RUDE on use; MonkHostility | click opens dialogue, hostility done; prayer/work animations not carried (cosmetic) | PARTIAL |
| narrator.scr | guberlandcity | starts the show at @m 14:30 / 16:30: curtain open, narration, cast calls | curtain is a click toggle; poster text kept (handler 330); show not carried | MISSING_DATA |
| npc109.scr | drangheimcity | Alfrigg quarrel lines and fight with Hrolf | installed: key only; dwarves_and_humans cinematic at R2 | OK |
| npc110.scr | drangheimcity | Hrolf: first sight 5010, quarrel, then at marker | drangheimcity.lua l.130-179; cinematic at R2 | OK |
| npc127.scr | guberlandcity | Markel: Book of Rules 61->167 (item 391), Ivan 62->165 (item 400), Dook 66->168, United | guberlandcity.lua l.112-127; scenario_scripted | OK |
| npc128.scr | guberlandcity | Tjolnir: Promocheck gives 206 when a member holds 437-440 (l.81-106); Nurtigan 212 -> 213, 24500 xp, GivePromo Healer | guberlandcity.lua l.134 still gates 206 on keys 437-440, which nothing sets: the Healer quest never starts (scenario FAIL, gap G2) | MISSING_DATA |
| npc129.scr | guberlandcity | Gray Slemnir: Givequest 250/251/252 when a member holds 441-444 (l.85-113); 260 -> 261, items 241/430 taken, GivePromo Priest | guberlandcity.lua l.142 gates on 441-444: the Priest quest never starts (scenario FAIL, G2) | MISSING_DATA |
| npc130.scr | guberland | Ivan the Smart: trivia 60 -> 164, item 400 | guberland.lua l.63-65 | OK |
| npc131.scr | guberlandcity | Nurtigan cured with item 558 (211); leaves the room | guberlandcity.lua l.172-179 (door opens, no walk) | OK |
| npc132.scr | guberland | the hag: DoRude 132 (GiveHair only via commented-out OnDamage) | placed (RUDE 132); the hair comes from the hairbrush prop (guberland.lua l.68-77) | OK |
| npc133.scr | guberland | Thorir: six prizes 362-367 -> 490, Capstone 188 (item 396, 146000 xp), Nicolai 121 -> 122, 487 | guberland.lua l.56-60 | OK |
| npc141.scr | guberlandcity | tavern keg 304 -> 306, item 249 taken | guberlandcity.lua l.149-152 | OK |
| npc142.scr | guberlandcity | apothecary: 207 on click with hair; 240 taken, @m potion 209; 558 + 373, sickroom unlocked | guberlandcity.lua l.155-171 | OK |
| npc150.scr | guberland | Scandlan new-game talk on sight, key 5020 | installed: none; newgame_talk cinematic at R2 (key 5020) | OK |
| npc151.scr | guberland | Broccan talk, walks away (5020) | newgame_talk at R2 | OK |
| npc161.scr | thjorgardcity | Tymon: ScholarCheck 201 when a member holds 425-428 (l.57-81); 203/204 -> 205, GivePromo Scholar | thjorgardcity.lua l.124 gates on 425-428: the Scholar quest (and Mage after it) never starts (scenario FAIL, G2) | MISSING_DATA |
| npc180.scr | frosgardcity | Tryggva: Yanmir 172, Break ice 175, United | frosgardcity.lua l.135-144; scenario_scripted PASS (this audit) | OK |
| npc181.scr | frosgardcity | Ranger 248 -> 249; click with item 184 -> 241 | frosgardcity.lua l.148-159 | OK |
| npc182.scr | frosgardcity | voice only | - | NOT_NEEDED |
| npc183.scr | frosgardcity | item 245 with 295 | frosgardcity.lua l.160-163 | OK |
| npc184.scr | frosgardcity | brewmaster keg 303 (item 249), 308, 310 | frosgardcity.lua l.164-169 | OK |
| npc185.scr | frosgardcity | voice, empty labels | - | NOT_NEEDED |
| npc186.scr | guberland | Atli: Mercenary 126 -> 127, 1000 g, 24000 xp, GivePromo Mercenary | guberland.lua l.113-118 promoteParty | OK |
| npc187.scr | guberland | Atli's daughter: gone with 127 | guberland.lua show(55, ...) | OK |
| npc188.scr | frosgardcity | ritual 257 -> 258, item 430 | frosgardcity.lua l.171-173 | OK |
| npc190.scr | frosgardcity | maypole 267 -> 268 (500 g); pledge.inc check on exit | maypole carried; pledge count missing (G3) | PARTIAL |
| npc191.scr | frosgardcity | pledge.inc check on exit | pledges left out (README): key 277 never set (G3) | MISSING_DATA |
| npc192.scr | frosgardcity | voice only (RUDE pledge row) | - | NOT_NEEDED |
| npc193.scr | frosgardcity | pledge.inc check | G3 | MISSING_DATA |
| npc194.scr | frosgardcity | voice only | - | NOT_NEEDED |
| npc195.scr | frosgardcity | pledge.inc check | G3 | MISSING_DATA |
| npc196.scr | frosgardcity | pledge.inc check | G3 | MISSING_DATA |
| npc197.scr | frosgardcity | pledge.inc check | G3 | MISSING_DATA |
| npc198.scr | frosgardcity | voice only | - | NOT_NEEDED |
| npc199.scr | frosgardcity | pledge.inc check | G3 | MISSING_DATA |
| npc206.scr | frosgardcity | Frosgard banker (BankOrb.inc), hatch DoRude 206 | frosgardcity.lua bank block | OK |
| npc209.scr | frosgardcity | dockmaster: 72 -> item 562, 378 | frosgardcity.lua l.126-130 | OK |
| npc213.scr | frosgardcity | Robert (bob & doug banter) | bob_and_doug ambient cinematic at R2 | OK |
| npc214.scr | frosgardcity | Douglas: first sight key 111 + banter | bob_and_doug at R2 (giveKey 111) | OK |
| npc215.scr | frosgardcity | powder seller: 1022 barrel; @m 22:00-4:00 cannon test | barrel carried; night test not carried (no quest) | PARTIAL |
| npc221.scr | frosgard | Green Man: 279 -> 280, 63000 xp, 5000 g, item 213, Druid promotion | frosgard.lua l.34-38 carried; 279 needs 277 (G3): unreachable | PARTIAL |
| npc239.scr | thronheimcity | Kira: treaty 181 (item 401), love letter 147 (item 247), Honkies 146, Mountain Pass 152, @M 6:00 88->180, Markel dead | thronheimcity.lua l.103-122 | OK |
| npc240.scr | thronheimcity | Thorfinn voice only | - | NOT_NEEDED |
| npc241.scr | thronheimcity | Ealusaid: 314 -> 315, item 250 taken | thronheimcity.lua l.163-166 | OK |
| npc242.scr | thronheimcity | Dagfari: 316 -> 317 item 251; 320 -> 321 | thronheimcity.lua l.168-173 | OK |
| npc244.scr | thronheim | Bikki: 95 -> 186, item 395 taken | thronheim.lua l.44-47 | OK |
| npc245.scr | thearena | Byri the Scarred: OnRude with 231 runs off, vanishes | thearena.lua Byri block | OK |
| npc246.scr | thronheimcity | Erlend: 318 -> 319, item 251 taken | thronheimcity.lua l.168-176 | OK |
| npc282.scr | lindisfarnemonastery | Grehgknak: letter 228 -> 229 item 419; Paladin 236 -> 237 | lindisfarnemonastery.lua l.202-217; scenario_quests | OK |
| npc283.scr | lindisfarnemonastery | Abbot: relic 341 -> 342 (item 368); @M 5:00 253 -> 254 | lindisfarnemonastery.lua l.219-235 | OK |
| npc284.scr | lindisfarnemonastery | Robert Aefgil appears with 254, gone 255 | lindisfarnemonastery.lua l.233-240 | OK |
| npc3.scr | arslegardcity, thjorgardcity | Sven: GoGetEm 486, Lifesaver 235, Thjorad 163 (item 197), Refinery 177, United | thjorgardcity.lua l.131-148, arslegardcity.lua l.84-87 | OK |
| npc309.scr | frosgardcity | Tamur Leng: 106 -> 190, 412000 xp, AddNPC 309 | frosgardcity.lua l.187-193; MM9.addHireling(309) at R2 | OK |
| npc312.scr | yorwick | Mary: :RuntoMe gives 466 when the following ewe reaches her (l.52); 467 -> 468, 2 g, 20000 xp | yorwick.lua l.75-78 pays 468; 466 never set: the ewe does not follow (regionlua header): row 15 unreachable (G4) | MISSING_DATA |
| npc334.scr | arslegardcity | Hanndl: Gungnir 353 + item 189 -> 354; 356 -> 357, 40000 g | arslegardcity.lua l.70-80 | OK |
| npc335.scr | hallofthegods | Krohn: 108 -> 191, item 576, 218000 xp | hallofthegods.lua l.31-40; scenario_quests | OK |
| npc336.scr | afterworld, hallofthegods | Skraelos: teleport 379, six fires 380-392, confessions 501-506 -> 383, swords 563-567 -> 389, reborn 391/102, OnFound DoRude | afterworld.lua l.74-141 (56000 FoundPlayer), hallofthegods.lua l.42-48 | OK |
| npc337.scr | hallofthegods | Fre: Golden Honk 346 -> 347, item 369 taken | hallofthegods.lua l.64-70 | OK |
| npc338.scr | darkpassageway | Wyrde: 476/187, 188 with item 396, flame cage | darkpassageway.lua l.324-330; scenario_doors_exits | OK |
| npc377.scr | hallofthegods | Great Honk DoRude 377 | engine opens RUDE on click | OK |
| npc378.scr | drangheimcity 2, frosgardcity 3, guberlandcity 2, sturmfordcity 2, thjorgardcity 2, thronheimcity 2 | Thorolf messenger: :Init shows Thorolf0/1 with 83 until 84 (Frosgard's third copy comes with 106 through NPC309's Appear), runs to the party (OnFound, RunTo 16) and DoRude 378, vanishes on 84/107 | all six cities: the walk-up (dungeon/lua.py thorolf_approaches), dialogue reopens, vanish; the five other cities showed him on 106 alone too (fixed 2026-11-07: 83 and not 84, as :Init); scenario_thorolf.yml in each (no one on 106 alone or 83+84) | OK |
| npc4.scr | thjorgardcity | Johannes: toMageOne 293 -> items 242/244, 288; Reward 493 -> 294, item 243, Mage promotion | thjorgardcity.lua l.106-116 carried; unreachable while 205 is (G2) | PARTIAL |
| npc414.scr | drangheimcity, guberland | Nicolai present only with 121 (Guberland) | guberland.lua; drangheimcity.lua | OK |
| npc415.scr | dookscastle | Baron Dook DoRude 415 | engine opens RUDE | OK |
| npc416.scr | thjorgardcity | Harris: OnDeath key 233 | thjorgardcity.lua l.187 | OK |
| npc417.scr | dungeonofsecrets | Chadwick trial 243-247 | dungeonofsecrets.lua l.506-612; scenario_trial | OK |
| npc419.scr | drangheimprison | cook: 5004 -> 5005, cell unlocked, else alarm 5006 | drangheimprison.lua l.111-118; scenario_quests | OK |
| npc420.scr | lindisfarnemonastery | organ player: 9506 plays hymn | lindisfarnemonastery.lua l.194-200 | OK |
| npc427.scr | drangheimprison | Antoni: 369 -> 370, 4000 xp, vanish | drangheimprison.lua l.120-128 | OK |
| npc436.scr | bootcamp | Grandpa: items 589/298/302 + 496, 579/580; OnFound DoRude; OnLeave 473 | bootcamp.lua l.144-165 | OK |
| npc48.scr | sturmfordcity | Hatlati: @m 12:00 wanders stealing, arrest 154 -> cell, 5009 | sturmfordcity.lua l.86-93 (arrest/cell); stealing wander not carried | PARTIAL |
| npc49.scr | sturmfordcity | moved with 157 | sturmfordcity.lua | OK |
| npc5.scr | thjorgardcity | Gunnar: ore 359-361 -> 395-398; payment 700/1500/3000; refinery 9513 -> 9514 (398 -> 399) | thjorgardcity.lua l.151-170 | OK |
| npc50.scr | sturmfordcity | Magi: blabber only | nothing to carry | NOT_NEEDED |
| npc55.scr | wizardslab | Robinssen: Black Orb 312 -> 313, 2000 g, item 250 | wizardslab.lua l.373-380 | OK |
| npc61.scr | sturmfordcity | clerk: skin 380/591 -> 215, Gladiator 26 -> 221, Kira's shield 375 | sturmfordcity.lua l.134-149 | OK |
| npc7.scr | thjoradmine, thjorgard, thjorgardcity | Hjarrand: payment 1000/2000 -> 362/363; machine 364; leaves | thjorgardcity.lua l.173-185, thjoradmine.lua l.634 | OK |
| npc8.scr | thjoradmine | Gudrek: with 9510 walks to Marker3, 9511 on exit | thjoradmine.lua l.647-652 | OK |
| npc87.scr | drangheimcity | Sigmund: item 596/489, gossip 300, Fort Stenig 171, Crona Kiga 170 (item 390), United | drangheimcity.lua l.75-87; scenario_scripted | OK |
| npc88.scr | drangheimcity | Atli the Quick: 226 -> 227, Assassin | drangheimcity.lua l.91-99 | OK |
| npc89.scr | drangheimcity | Keith: 136 -> 137, Crusader | drangheimcity.lua l.100-105 | OK |
| npc9.scr | thjoradmine | OnRude exits at once ("removed because it wasn't working"); voice | nothing to carry | NOT_NEEDED |
| npc90.scr | drangheim 2, drangheimprison, sturmfordcity | Ivsar: Drangheim region copies ("Drangheim Main/Well", visible with 17) OnFoundPlayer -> :OnUse givekey 194 + DoRude 90 (l.63-93); RUDE 90 row 7 (req 194) gives 242; Sturmford copy shown with 242, exit gives 196 (l.140) | drangheimprison.lua and sturmfordcity.lua carried; drangheim.lua has no Ivsar handler (regionlua: "Not here"): 194 never set, row 7 never shows (scenario FAIL, G1) | MISSING_DATA |
| npc91.scr | drangheim | Hring: plow 133 -> 200 (item 371) | drangheim.lua l.76-78 | OK |
| npc92.scr | drangheim | Ragnheid: herbs 134 -> 198 (item 372) | drangheim.lua l.79-81 | OK |
| npc93.scr | drangheim | Tyock: dolly 135 -> 199 (item 370) | drangheim.lua l.82-84 | OK |
| npc95.scr | drangheimcity | Guaire: shown with 222 (HP 300, AC 50), death 225 | drangheimcity.lua l.109-113, 177 | OK |
| npc96.scr | drangheimcity | voice, empty Thjorad/Refinery labels | nothing to carry | NOT_NEEDED |
| npcshopkeeper.scr | guberland, sturmford, thronheim | voice on use, wander | the voice on a click where its ScriptParams or script name one (shared voice_lines) | OK |
| propanim.scr | 1000terrors 14, afterworld 30, anskramkeep 28, arslegardcity 6, beethoven 2, drangheim, drangheimcity 2, frosgard, frosgardcity 6, guberland 3, guberlandcity, hallofthegods 7, isleofashes, klusoshouse 7, lindisfarne 4, lindisfarnemonastery 27, ruinedtemple 6, sturmford, sturmfordcity 4, tasaracademy 3, templeofhonk 5, thearena 11, thjoradmine 19, thjorgard 3, thjorgardcity 9, thronheim, thronheimcity 19, verhoffinruins 10, yanmirsfort 7, yorwick 34 | 70 posed props: PlayAnim/Loop by param, Sit; OnUse | static props; council RUDEProps open their dialogue; cosmetic | PARTIAL |
| ralof.scr | guberlandcity | same show (speeches, converse) | the show's voices play at the speakers' places (citylua play_lines, THEPLAY.scr's timeline, 14:30/16:30); actors not placed, walks not carried | PARTIAL |
| randverretainer.scr | thjorgardcity | Randver hidden while hired (453) | thjorgardcity.lua show(54, not has(453)) | OK |
| randverrun.scr | sturmfordcity | Randver: 15 -> 495, 800 xp, runs and vanishes | sturmfordcity.lua l.125-133 | OK |
| retainer.scr | drangheimcity 2, frosgardcity, guberland, guberlandcity 2, lindisfarne, sturmfordcity, thjorgardcity 2, thronheimcity | hireling hidden while hired (key 450-462), voice | all eight maps show(..., not has(key)); hire/dismiss engine (hirelings.txt) | OK |
| scholarpromo.scr | thjorgard | Magreeb runs away on sight, 202 with 201 | thjorgard.lua scholarpromo hook (M4); depends on 201 (G2) | OK |
| shopkeeper.scr | drangheim, drangheimcity 4, frosgardcity 8, guberlandcity 6, lindisfarne 4, sturmfordcity, thjoradmine, thjorgard, thjorgardcity 11, thronheimcity 9, yorwick 2 | OnUse plays the NPC voice (param 0); JohnGoodman position fix | shops are RUDE services; the greeting voice plays on a click (shared voice_lines) | OK |
| spieslikeus.scr | sturmfordcity | Bjarni Herjolfssen: 18 -> 471 | sturmfordcity.lua l.120-122 | OK |
| stonesgame.scr | guberland, thjorgard | stones board game vs bot (Thjorgard 7100, Guberland 7110) | Thjorgard: full (St0-35); Guberland: not carried (regionlua header) - prize still won by the other 3 games | PARTIAL |
| stonesplayer.scr | guberland, thjorgard | bot: OnRudeEnter key 7002 + DoRude 428, OnRudeExit takes 7002 | thjorgard.lua; guberland.lua 53267/50267 | OK |
| sturmgaardinn.scr | sturmfordcity | tavern window broken -> 5000 (:OnBreak l.49); pay 500 | no breakable windows; NPC57 rows gated by 5000 stay hidden (correct) | NOT_NEEDED |
| sturmguard.scr | sturmfordcity | jail guard: 5008 then DoRude 425; jail 5018/5019; Hatlati 154/5009 | sturmfordcity.lua l.150-160 | OK |
| svenarena.scr | thearena 3 | Sven double walks in with key 230, 1034 on use | thearena.lua Sven block; scenario_sven.yml PASS (this audit) | OK |
| svenspeech.scr | yorwick | battlefield speech cinema; Award 95 -> 97, 114000 xp | yorwick.lua reward; battlefield_sven cinematic at R2 | OK |
| tasarguardduty.scr | tasaracademy 4 | @m 20:xx guards go to bed markers, @m 6:xx back on duty (SetPos) | not carried: guards stay at posts all day (cosmetic; no key) | PARTIAL |
| tasarstudent.scr | tasaracademy 6 | sparring students hate the captains | tasaracademy.lua sparring block | OK |
| tasarteacher.scr | tasaracademy | GuardCaptain spawns sparring (OnSpawn Hate) | tasaracademy.lua sparring; scenario_scripted.yml | OK |
| thjorgardspectator.scr | guberland 2, thjorgard 11 | Thing spectators cheer/boo/jump idles | placed, idle only (cosmetic) | PARTIAL |
| thronheimcity_actor.scr | thronheimcity 2 | Ben/Shmoe flee the Desert Terror, Shmoe killed, Ben to guard | M23 breakout (citylua.py, takes effect at R2); installed: shorter version | OK |
| thronheimcity_guard.scr | thronheimcity 2 | guards GetBadAss; OnDeath sends a new guard | M23 kill hook 264, cap 12 (at R2) | OK |
| trislan.scr | guberlandcity | same show (Emperor Trislan: speeches, OnDie/GetUp) | the show's voices play at the speakers' places (citylua play_lines, THEPLAY.scr's timeline, 14:30/16:30); actors not placed, walks not carried | PARTIAL |
| tryggvaspeech.scr | sturmfordcity | Tryggva (Sturmford) drunken lines on Blabber, Tryygva01-04 | one of Tryygva01-04 at his table, once (citylua barks) | OK |
| whack-a-honky.scr | guberland 4, thjorgard 4 | whack the raised geese (Thjorgard 7103, Guberland 7113) | Thjorgard: done (M1, scenario PASS); Guberland: not carried | PARTIAL |
| wilam.scr | guberlandcity | same show | the show's voices play at the speakers' places (citylua play_lines, THEPLAY.scr's timeline, 14:30/16:30); actors not placed, walks not carried | PARTIAL |
| yanmirchild.scr | yanmirsfort 7 | children shout for help, follow with key 7001, escape | yanmirsfort.lua l.265-300 (no follow walk); RUDE 433 fix at R2 | PARTIAL |

## Includes

| Include | MM9 | Rework | Status |
| --- | --- | --- | --- |
| bankorb.inc | Frosgard bank variant of BankOrb | frosgardcity.lua | OK |
| chessbase.inc | attack slide, PawnToQueen, camera | squares/queening/camera carried; pieces static | PARTIAL |
| dookhostility.inc | Dook guards hostility | dookscastle.lua | OK |
| drangheimhostility.inc | pass 5007 / alarm 5006 (TurnHostilityOn gives 5006) | drangheimprison.lua | OK |
| honkhostility.inc | Honks friends until hurt/robbed | templeofhonk.lua; scenario_hostility | OK |
| monkhostility.inc | monks friends until hurt | lindisfarnemonastery.lua | OK |
| nogold.inc | a member's no-gold voice grumble | status text instead | PARTIAL |
| npcbase.inc | socialising, chat, wander, run-away base of Retainer/NPC241/Thronheim actors | by contract (MM9_RUDE_SCR_INTEGRATION "SCR Conversion Boundary"): shared AI | NOT_NEEDED |
| pickmon.inc | arena monster table by level | mm9r_thearena/pickmon.py -> thearena.lua table | OK |
| pledge.inc | :Pledge collects 269-276, :CheckAllNPC (at most one of 269-274 missing) -> :reward key 277 + 5000 xp (l.27-31); run by NPC190/191/193/195/196/197/199, HideModel, ARG_Unhide, ChangeModel, Pledge.scr exits | not carried (frosgardcity README): 277 never set (G3) | MISSING_DATA |
| policeman.inc | guards help each other | shared guard AI / M23 | NOT_NEEDED |
| sixfires.inc | Afterworld fires: Guilt..Rebirth, 491/492/5021, spawns | afterworld regionlua (492 Absolution and spawns at R2) | OK |
| svenshowtake.inc | shows/hides the battlefield and afterworld tableaux | yorwick and afterworld regionlua | OK |
| thjorgardgamescommon.inc | tickets 557 (5 / 40 g), rule book 594, wins 7100-7105 -> 7106 + 94 + item 395 + 10000 xp (with 93); Guberland 7110-7116 + random prize 362-367 | thjorgard.lua l.57-95, guberland.lua l.121-156 | OK |
| united.inc | jarl click: five other clans -> 178; United 83 -> 179 + 26500 xp + 6000 g | every jarl's city Lua, per-jarl key sets | OK |

## Verification run for this audit

Against `assets_dev` with the current `build/game/openyamm` (scenario files in the session scratchpad `npcq/scen/`):

| Scenario | Result |
| --- | --- |
| `ivsar.yml` (drangheim, keys 12 and 17, talk to Ivsar 33) | FAIL as expected: dialogue 90 offers rows 8 and 9 only; 90194 clear (G1) |
| `pledge.yml` (frosgardcity, 265 + 269-275, close NPC190's talk) | FAIL as expected: 90277 clear (G3) |
| `scholar.yml`, `healer.yml`, `priest.yml` (class-check key set, close Tymon's, Tjolnir's, Gray's talk) | FAIL as expected: 90201, 90206, 90250 clear (G2) |
| `mm9r_thjorgard_blv/scenario_games.yml` | PASS (220 steps) |
| `mm9r_thearena/scenario_sven.yml` | PASS |
| `mm9r_frosgardcity/scenario_scripted.yml` | PASS |

