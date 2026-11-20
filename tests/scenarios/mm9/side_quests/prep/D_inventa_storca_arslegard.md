# Prep: block D, the Inventa Storca and Arslegard (Orbs of Linking, Gungnir, the Bathhouse)

Researched 2026-11-08 against the installed `assets_dev` (map Lua, scenes, RUDE rows), MM9's scripts
(`mm9/extracted/SCRIPTS/SCRIPTS/`) and DAT objects (`level_generation/projects/mm9r_*/work/`), with discovery scenarios
on `build/game/openyamm` (23:20 build). Coordinates are native (x, y, z); MM9 keys are qbits 90000 + key. Room maps:
`level_generation/projects/mm9r_inventastorca/work/rooms_upper.png`, `rooms_lower.png` and
`mm9r_bathhouse/work/rooms_upper.png` (LT units: native = LT x 2.56, no offset for these two maps).
Compass words follow the guide's map images (`output/mm9_site/data/presentations.json`): the Inventa Storca, the
Bathhouse and Arslegard City are unflipped (+x east, +y north); Thronheim is flipped both ways (+x west, +y south).

Scenarios: `get_the_orbs_of_linking.yml`, `find_gungnir.yml`, `clean_out_the_bathhouse.yml`. Each starts with
`new_game_flow` (Knight, Cleric, Thief, Sorcerer, level 28; the Thief has Disarm Traps 8 Master and Perception 8 Master).

## Shared: the Inventa Storca (`inventastorca.blv`, `events/maps/inventastorca.lua`)

**Getting there**: Thronheim region (`thronheim.blv`), ExitTrigger5 at (-22416, -6538, 2724), half extents
(655, 61, 164), "Inventa Storca" OK/Close prompt. Its arrival from the dungeon is (-22426, -6036, 2573): `set_pose`
(-22416, -6100, 2573) yaw -pi/2, walk to (-22416, -6538) `expect: dialog`, "OK". Arrives at StartPoint0
(369, -82, -890), the entrance hall in the north-east. The exit back (ExitTrigger0, (451, -676, -732)) is on the
entrance's spiral stair, 600 from the arrival. On the Thronheim map (catalog `flip_u`) native -x is east: the door is
on the map's east edge, north of the city, as the guide says.

**Double doors** (rotate movers, about 7 s auto-close; a click on a closing leaf does not reopen it: wait until shut,
then click; `walk_to` sometimes says "nothing to click ahead" at them):

| Door | leaf ids | event | position | joins |
| --- | --- | --- | --- | --- |
| DoubleDoor13 | 11, 12 | 105 | (-1659, 246, -891) | entrance hall / small hall west of it |
| DoubleDoor14 | 13, 14 | 106 | (-2478, 471, -891) | that hall / pillared hall (room 22) |
| DoubleDoor10 | 5, 6 | 102 | (-4608, 0, -860) | pillared hall / reading room (21) |
| DoubleDoor9 | 29, 30 | 120 | (-6533, 328, -860) | reading room / long north hall (26); its click also wakes the Lich King who kills the dying adventurer (IS_KillingLich.scr) |
| DoubleDoor12 | 9, 10 | 104 | (-4342, -1392, -860) | pillared hall / walkway over the flooded cavern (not used) |
| DoubleDoor11 | 7, 8 | 103 | (-6636, -3523, -860) | corridor (13) / map room (10) |
| DoubleDoor6 | 23, 24 | 111 | (-5325, -6799, -860) | south corridor (3) / south room (1) |
| DoubleDoor5 | 21, 22 | 110 | (-3257, -7209, -860) | south room / small south-east room (2, the trapdoor) |
| DoubleDoor4 | 19, 20 | 109 | (-1843, -5960, -1475) | lower: ladder room (4) / red stair room (8) |
| DoubleDoor3 | 17, 18 | 108 | (-614, -3952, -1638) | lower hall (14) / book room (9) |
| DoubleDoor2 | 15, 16 | 107 | (20, -3318, -1638) | lower hall / east room (12) |
| DoubleDoor1 | 3, 4 | 101 | (-614, -2642, -1638) | lower hall / north room (18) |

**Cracked walls** (scene destructibles; weapons break them, a click deals the killing blow, Perception 8 shows them):
DestructableBrush2 (event 38420, hp 15) at (-5222, -3512, -707) between the map room and the spiral stair room;
DestructableBrush1 (38421) at (-440, -1312, -1485) between the lower north room and the cave under the entrance;
DestructableBrush0 and 3 elsewhere (not on the routes).

**Trapdoor and ladder**: LadderDoor (door 76, event 156, a click opens/shuts it; PerceptionBrush9) in room 2,
box (-2007..-1679, -7004..-6676, -886); Ladder5 bottom (-1843, -6978, -1472), top (-1843, -6978, -888), facing 270,
top_exit (-1843, -7142, -860). The ladder has no `grab_at_top`, so it cannot be climbed down: the party walks onto the
open hatch (-1843, -6900) and drops ~600 to the ladder room (`walk_to` with `z_tolerance`). Up: `climb: {ladder:
Ladder5}`; the trapdoor stays open (a click from below opens it otherwise; a shut hatch stops the climb).

**Bust-out**: BustOutTrigger1 (event 191) is a 51 x 205 pad at (-3974, -7209, -762), on/under the south room's orb
table (convert notes: "under DeskDrawer0's desk"): a party brushing it gets the ceiling slab broken and a **Lich**
(actor 21, monster 9207; MM9 class Lich with the LichKing model) and two Skeletons (19, 20) dropped at (-4178, -7086).
Standing at (-3932, -7150) trips it in most runs but not all (one run of four did not): the scenarios only log it.

**World items**: seven Orbs of Linking (item 10252, `forbidden_qbits: [90337]`, pickup events 210-216 play quest.wav):

| Prop | position | where | stand at |
| --- | --- | --- | --- |
| Prop0 | (-4301, 1106, -870) | upper, north end of the pillared hall (22) | (-4301, 950) |
| Prop1 | (-11633, -5652, -860) | upper, the far west hall (not taken) | |
| Prop2 | (-4178, -4383, -860) | upper, beside the spiral stair (17), behind DestructableBrush2 from the map room | (-4250, -4250) |
| Prop3 | (-3932, -7291, -765) | upper, the south room's table (1) | (-3932, -7150) |
| Prop4 | (-205, -5734, -1638) | lower, south end of the book room (9) | (-205, -5600) |
| Prop5 | (799, -3686, -1536) | lower, the east room (12) | (799, -3550) |
| Prop6 | (-41, -1106, -1638) | lower, the cave under the entrance (20), behind DestructableBrush1 | (-150, -1150) |

**Chests**: Chest1 (container 1, event 42, BlackChest, `trap_level` 25, `random: false`, fixed item 10189 Gungnir) at
(-576, -4188, -1687) and Chest2 (container 2, event 43, level 4) at (-737, -4188, -1687), in the floor compartment
under SecretPanel1 (door 79) at the book room's north end, just south of DoubleDoor3. SecretSwitch1 (event 171, door
82) is a book on the south face of FallingBookcase4 at (-725, -4852, -1470): stand in the aisle between the third and
fourth bookcases from the south at (-725, -4956), reached from the free east side of the room (x -200). Its handler
opens SecretPanel1 once. Do not click FallingBookcaseSwitch (event 170, on the first bookcase): the domino topples all
six (SecretSwitch1 rides FallingBookcase4). The engine's trap check uses the map's difficulty (map_stats Lock 7, so
Disarm Traps >= 14 disarms), not the chest's 25 (`ChestRuntime.cpp:968-970`). Take All, then `close()` (the open chest
blocks world input).

**Routes that work** (both scenarios): entrance -> DD13 -> DD14 -> (Prop0) -> DD10 -> DD9 -> via (-6700, 328),
(-8500, 300) south down the long west hall -> either (-8500, -600) -> DD11 -> crack 38420 -> via (-4950, -3480) to
Prop2, or (-8500, -6800) -> DD6 -> (-3932, -7150) -> DD5 -> (-1843, -6500) trapdoor. Lower: DD4 -> via (-1950, -5000,
-1500), (-1950, -4150, -1638), (-1500, -3800) -> (-614, -3800) -> DD3 -> via (-614, -4060), (-200, -4300). The planner
alone fails on closed doors (it plans through them, then the leaves are shut when it returns) and on the map room's
east wall (the crack), so every leg is short and door-to-door.

## Get the Orbs of Linking (`get_the_orbs_of_linking.yml`, about 21 s; reload 51 s)

- **Giver**: Brynhildr the Money-wise, Thronheim City bank, actor 4 at (16384, 3809, 3114), yaw 1024 (facing -x);
  stand at (16234, 3809) yaw 0. RUDE 243; the start node is 243. Lines: "What can we help you with?" (forbid 322) ->
  "So what's the problem?" -> "Sounds easy.  Where are these Orbs of Linking?" -> "We will find these orbs for you."
  (key **322**). No prerequisite key.
- Out of the city: TownExit ExitTrigger1 (14950, 82, 3415): `set_pose` (14500, 82, 3093) yaw 0, walk east, "OK".
  Back in by the land gate: `set_pose` thronheim (1392, 6100, 1279), walk to (1392, 6498), "OK" (as playthrough 52).
- **Install** (BankOrb.scr / BankOrb.inc, each city's map Lua): a click with an orb (`HasItemAnywhere`) and 322 gives
  key **330** (unless that bank's second key is set); the row (req 330, forbid the bank key) gives the bank key; the
  talk's exit takes 330, the orb, sets the bank's second key, and with 331-336 all set gives **337**, 12 500 experience
  (MM9 GiveExp 20 000, capped by `mm9_quest_xp_profile.yml`) and 15 000 gold.

| Bank | map Lua | banker (actor, position, stand at) | row | keys |
| --- | --- | --- | --- | --- |
| Thronheim | thronheimcity.lua:204-217 | Brynhildr (4, (16384, 3809, 3114); (16234, 3809) yaw 0) | "We'd like to install an Orb of Linking." | 331, 328 |
| Thjorgard | thjorgardcity.lua:90-105 | Ragnar Gjalpssen (3, (-5079, 11878, 206); (-5079, 11728) yaw pi/2) | "We're here to install an Orb of Linking into your bank." | 335, 323 |
| Sturmford | sturmfordcity.lua:94-109 | Herdis the Stout (28, (9462, 7864, 19846); (9462, 8014) yaw -pi/2) | "We've come to install an Orb of Linking." | 336, 324 |
| Drangheim | drangheimcity.lua:58-73 | Hlif Ingimundssen (15, (21443, -2570, 370); (21293, -2570) yaw 0) | "We'd like to install an Orb of Linking." | 334, 325 |
| Guberland | guberlandcity.lua:95-110 | Ottar Gizurssen (12, (1720, -4424, 1); (1570, -4424) yaw 0) | "We have an Orb of Linking we'd like to install." | 332, 326 |
| Frosgard | frosgardcity.lua:47-75 | Fiachna A'Lanth (7, (2703, 5504, 4); (2703, 5354) yaw pi/2), behind the counter hatch: `click(231)` opens it and his talk | "We have an Orb of Linking." | 333, 327 |

  Town entries (from the playthrough): Thjorgard (-9300, 4392) -> (-8790, 4392); Sturmford (8090, -3312) ->
  (7300, -3312); Drangheim (11458, -4164) -> (12032, -4164); Guberland (6131, -9700) -> (6131, -9194); Frosgard
  (1783, 3700) -> (1783, 3250). `travel` between region maps, 2-8 days.
- **Asserts**: 322; per bank its two keys and 330 clear, one orb fewer; at the sixth 337 and gold 15 000 (from 0).
  Journal: NPC997 rows exist for the quest (not asserted).

## Find Gungnir (`find_gungnir.yml`, about 15 s; reload 34 s)

- **Giver**: Hanndl, actor 9 at (14090, 2674, -491) by the wake point (the peephole's Hanndl is actor 35); stand at
  (14240, 2674) yaw pi. RUDE 334, click 53113, exit 50113 (`arslegardcity.lua:77-89`, NPC334.scr). Lines: "You don't
  seem to like us very much." (forbid 353, 356) -> "That's unfortunate.  You must have really upset Krohn." -> "What's
  Gungnir?" (loops) -> "Maybe we could help?" (forbid 355) -> "We could find it for you." (key **353**).
- Optional: Fre (RUDE 337, Hall of the Gods) "What happened to Hanndl's spear?" (req 353, forbid 354/355). Not played.
- **Prerequisite keys set**: 98 (else gate_fate moves the party to the Dark Passageway 3 s after arrival), 100 and
  9515 (the Writ shown, the gate open; else gate_writ plays). See the discrepancy on Arslegard's access below.
- **Leaving Arslegard**: ExitTrigger4 to Thjorgard (14418, 3043, -82), half (410, 164, 410), lies just north of the
  wake point (14400, 2525) and south of the Great Gate (RotatingDoor0/1 at y 3452-3493): walking north from the wake
  point opens its prompt at y 2855. Then `travel` thronheim 2 days and the Inventa route above.
- The chest: SecretSwitch1, Chest1 (event 42), Take All, `close()`: Gungnir **10189** in the packs.
- **Back**: Arslegard is reached only by dying (world.yml `partyDeath`); `party_defeat: {knock_out: true}` wakes the
  party at (14400, 2525); Gungnir stays in the packs.
- **Hand-in**: the click with 353 and Gungnir gives **354**; "We found your spear." (req 354) gives **356**; the exit
  (356 without 357) takes Gungnir, gives **357**, 40 000 gold, 5 000 experience. Asserts: 354, 356, 357, gold 40 000,
  Gungnir gone.
- Note: GUNGNIR.scr (a Gungnir prop that gives the item and key 354, or 355 without the errand) is not placed in MM9's
  Inventa Storca DAT either; the spear is Chest1's Item1 (189). So Hanndl's "Does your spear look like this?" (req 355)
  is unreachable in MM9 and here; nothing is lost (opening the chest before the errand still works: take the errand,
  click again).

## Clean out the bathhouse (`clean_out_the_bathhouse.yml`, about 10 s; reload 26 s)

- **Giver**: Jokull the Ugly, actor 0 at (16179, -1504, -491) in the Stumbling Hero (Arslegard); stand at (16000, -1504)
  yaw 0. RUDE 339, click 53104 (voice + openRude only). Lines: "Can we ask you some questions?" -> "Do you have any
  news?" (forbid 348, 350) -> "What sort of problem?" -> "Why doesn't he help you?" (forbid 350) -> "Sounds like
  you're in a heap of trouble alright." -> "Why not?  We'd be happy to!" (key **348**).
- **Bathhouse door**: Arslegard ExitTrigger0 (5161, -13423, -158) at the top of the steps: `set_pose` (5161, -12700,
  -491) yaw -pi/2, walk south, "OK". Arrival StartPoint0 (-983, -901, -281); exit back ExitTrigger0 (-1311, -881).
- **Route**: planner to (4240, -2700, -243), north of Door1 (door 2, event 102, sliding, at (4050..4429, -2837));
  through it to (6400, -3191); Door5 (door 6, event 106, at x 6570, y -3420..-2962) east; via (6800, -3191),
  (6800, -4000) into the east room and west through its archway to (6250, -4050) in Ebora's tub room. Sliding doors shut
  by themselves; a click on a closing one does not reopen it (wait until shut). Back: (6800, -4000) -> (6800, -3191),
  Door5, (4240, -3000), Door1, then the planner to the exit.
- **Ebora** (actor 7, (5980, -4588, -368), damage hook refuses) and three Concubines (8, 9, 10, hostile): `walk_to`'s
  `clear_hostiles` kills the Concubines as the party enters; the kill hook (event 98) counts them; the third starts
  `ebora_escape` (about 4 s): map var EboraGone 1, key **349** and 18 500 experience (MM9 80 000 capped) with 348, else
  key 350.
- **Hand-in**: "We cleaned out your bathhouse." (req 349, forbid 351) gives **351**. NPC339.scr's exit then gives 80 000
  experience, 5 000 gold and key 352: **missing here** (bug below), logged as ISSUE by the scenario, which accepts
  either state (it logs the reward once 352 appears; add `gold: 5000` to its assert then).
- Alternative path: clean it before the errand: key 350, and Jokull's "That old place?  We already cleaned it out."
  (req 350) gives 351 too (not played).

## Discrepancies

### Guide errors (proposed corrections for `tools/mm9_site/story/side_*.yml`)

1. **find-gungnir step 1** (side_b.yml:319) misses Hanndl's second line: the first line leads to "That's
   unfortunate.  You must have really upset Krohn." before "What's Gungnir?". Proposed: "Talk to Hanndl by Arslegard's
   gate: 'You don't seem to like us very much', 'That's unfortunate. You must have really upset Krohn', 'What's
   Gungnir?', 'Maybe we could help?' and 'We could find it for you'."
2. **find-gungnir step 3** (side_b.yml:321): "the trapdoor ... in the floor in the south and climb down the ladder".
   The Orbs entry says the small room in the south-east; that is right (room 2, east of the south room). And the ladder
   cannot be climbed down here (see the bug below): the party drops through the hatch. Proposed: "The spear is on the
   lower level: open the trapdoor (the Ladder Door, Perception shows it) in the small room in the south-east of the
   upper floor and drop down the shaft; Ladder5 takes you back up." Also add how to get there and back: "Leave
   Arslegard by the Thjorgard exit just north of where the dead wake; the only way back to Arslegard is to die."
3. **find-gungnir step 4**: say where the book is: "Secret Switch 1 is a book on the south face of the fourth
   bookcase from the south (stand in the aisle between the third and fourth)."
4. **find-gungnir step 5**: "(trap 25: disarm it first)": the engine checks the map's trap difficulty (7), not the
   chest's 25; Disarm Traps 14 or better disarms it. Proposed: "Gungnir is in the black chest (trapped: a Thief with
   Disarm Traps 14 or better disarms it)."
5. **find-gungnir tip 2 vs get-the-orbs step 2**: one says "a Lich and two Skeletons", the other "a Lich King and two
   skeletons". The game's actor is a Lich (monster 9207; MM9: class Lich with the Lich King's model). Proposed for
   both: "a Lich and two Skeletons drop through the ceiling" and, for the orbs, "when you reach the orb's table".
6. **get-the-orbs step 2**: the spiral stair's orb is behind a cracked wall when coming from the map room (west), or
   reached by the walkway south of the pillared hall (DoubleDoor12, not walked). Proposed addition: "(from the map room
   to its west, break the cracked wall)".
7. **get-the-orbs step 3**: "under the entrance in the north-east" is in a cave behind a cracked wall at the north end
   of the lower north room; and "A trapdoor ... hides a ladder down" -> "drop down; the ladder takes you back up".
   Proposed: "...and one in the cave under the entrance, behind a cracked wall at the north end of the north room
   (break it)."
8. **clean-out-the-bathhouse step 1** (side_b.yml:297): Jokull's first page has no "Do you have any news?": it is under
   "Can we ask you some questions?". Proposed: "...ask Jokull the Ugly 'Can we ask you some questions?', 'Do you have
   any news?', ...".
9. **clean-out-the-bathhouse reward** (side_b.yml:306): once the bug below is fixed: "18,500 experience when Ebora
   flees; from Jokull 5,000 gold and the balanced share of MM9's 80,000 experience." Also the way in: "Ebora's tub room
   is entered from the east room (through Door5 at the east end of the corridor north of it)."
10. **requires** (both Arslegard quests: "Access to Arslegard City (the Writ of Fate)"): faithful to MM9, where a party
    that dies before the Writ is turned away (LoseMan.scr). In this build any death after Hanndl's first refusal wakes
    the party in Arslegard with the whole city open (below), so the quests can be done earlier. Keep the guide text if
    the build is meant to follow MM9.

### Suspected game bugs

1. **Jokull's reward is missing** (high). MM9's NPC339.scr `:OnRude` -> `:Bathhouse`: with 351 and without 352, GiveExp
   80 000, GiveGold 5 000, quest.wav, GiveKey 352. `assets_dev/worlds/mm9/events/maps/arslegardcity.lua` has only the
   voice click for him (line 182, `handlers[53104]`) and no exit handler 50104; `level_generation/projects/
   mm9r_arslegardcity/citylua.py` writes no NPC339 block, and `mm9r_common/quest_xp_audit.json` lists no key 352 (only
   Ebora's 349). Repro: `python3 tests/scenarios/mm9/side_quests/run.py clean_out_the_bathhouse` logs "ISSUE Jokull's
   reward ...". Proposed fix (citylua.py, after the Hanndl block, plus the registration; then regenerate per AGENTS.md):

   ```python
   "-- NPC339.scr (Jokull the Ugly, RUDE 339, the Stumbling Hero): the exit after the bathhouse is cleaned (351",
   "-- without 352) pays 80 000 experience and 5 000 gold (352).",
   f"handlers[{rude_exit_event(o['ShopkeeperHuman2MaleA0'])}] = function()",
   "    if not has(352) and has(351) then",
   f"        MM9.giveKey(352); {experience_lua(80000, 352)}",
   "        MM9.giveGold(5000); quest()",
   "    end",
   "end",
   ```
   (`experience_lua` ends with a line comment, so the gold goes on the next line) and in `script.add(...)`:
   `(rude_exit_event(o["ShopkeeperHuman2MaleA0"]), "Jokull the Ugly", None)`. The quest XP profile may want an entry
   for key 352 (`tools/mm9_import_discovery/mm9_quest_xp_profile.yml`, like 349's).
2. **Ladder5 cannot be climbed down** (low). `inventastorca.scene.yml` `ladders[0]` has no `grab_at_top`, so a party at
   the open trapdoor cannot take the ladder (MM9's ladders can be descended) and drops ~600 to the ladder room (fall
   damage for a real party). The shared writer `level_generation/projects/mm9r_common/dungeon/rotation.py:113-134`
   (`ladder_records`) does not pass `grab_at_top` through; proposed: after building each record,
   `if rule.get("grab_at_top"): records[-1]["grab_at_top"] = True`, and in `mm9r_inventastorca/overrides.yml:134` add
   `grab_at_top: true` to Ladder5 (as Drangheim City's TowerLadder1 does in its own convert.py). Logged as ISSUE in both
   Inventa scenarios.
3. **Arslegard's Great Gate gates nothing** (question for the user). The wake point (StartPoint0, world.yml
   `partyDeath` (14400, 2525)) is south of the Great Gate (RotatingDoor0/1, y 3452-3493), on the city side, and so are
   ExitTrigger4 (to Thjorgard, y 2879-3207), the tavern, the Bathhouse door and the Hall of the Gods' entrance: a
   discovery walk from the wake point reached the Hall's gate (19800, -11703) with only key 98 set, and walking north
   from the wake point leaves for Thjorgard with the gate shut. MM9's offsets keep the same relative layout, so this may
   be MM9's own map; but MM9 kept a pre-Writ dead party out with LoseMan.scr (turned away), which the README says is
   not carried ("no death-to-Arslegard flow"). Effect: after the first visit any death puts the party in Arslegard with
   Skraelos' Hall, the Bathhouse and Hanndl's quest open before the Writ. Decision for the user: carry LoseMan (a death
   before the Writ is the old game over / turned away), or accept the open city.
4. Cosmetic: frosgardcity.lua:47 names the banker "Cormac A'Ghrie", the scene and guide "Fiachna A'Lanth";
   drangheimcity.lua:58 says "Ingimar's bank" for Hlif Ingimundssen. Comments only.
5. Observation, not changed: the engine's chest trap uses the map's Lock difficulty, not MM9's per-chest TrapLevel
   (`LootContainerRuntime.cpp:113` only flags the chest trapped; `ChestRuntime.cpp:968-970`).

## Runs (2026-11-08)

| Scenario | `--repeat 2` | `--reload` |
| --- | --- | --- |
| get_the_orbs_of_linking | PASS 18 s, 23 s | PASS 53 s |
| find_gungnir | PASS 12 s, 15 s | PASS 28 s |
| clean_out_the_bathhouse | PASS 8 s, 8 s | PASS 18 s |

Workarounds logged in the runs: `ISSUE` Ladder5 not descendable (both Inventa scenarios), `ISSUE` Jokull's reward
(the bathhouse). No BLOCKER.
