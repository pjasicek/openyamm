# Prep: segments 09-11 (Sven and Frosgard, Krohn, Njam's house and the Tomb of a Thousand Terrors)

Research for `09_frosgard_tamur.yml`, `10_krohn.yml` and `11_tomb.yml` (2026-11-08). Sources: the map scripts and
scenes in `assets_dev/worlds/mm9/` (what the game runs; the review roots differ for these maps, but the game reads
`assets_dev`), the RUDE files in `assets_dev/worlds/mm9/dialogue/rude/`, the MM9 DAT dump
`level_generation/projects/mm9r_1000terrors/work/objects.txt`, and headless probes. Keys: `MM9.hasKey(K)` = qbit
90000+K. Items: engine id 10000 + raw MM9 id. Coordinates are native units.

**Validation.** Segment 09 (Hall → Sven → Thjorgard → Frosgard battle → Tamur → Thorolf) and segment 10 (defeat →
Hall → Krohn) and the city part of 11 (Njam's house → the Tomb's door) **passed headless from the real checkpoint
`08_six_fires.oysav`**. The Tomb was proved leg by leg from `load_map` with `qbit set 90108`. Every leg passed, and
one run walked from the Tomb's start to the lift top in a single scenario. The top level passed from the lift's foot
through Njam's freeze to the epilogue's Writ of Fate. Two complete runs were then stopped in the entry level's central
corridor, at about (8010, −8600, −143), by invulnerable actors standing in the way: risk 3. All probe files are in
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/prep_c/`:
`real.yml` and `real2.yml` (real save), `full.yml` (the whole Tomb), `top.yml` (lift to epilogue), and `p*.yml`.

**Status (later on 2026-11-08).** The segments exist (`09_frosgard_tamur.yml`, `10_krohn.yml`, `11_tomb.yml`) and
pass, also as the chain `run.py 09 10 11`. Fixed since this research:
- Risks 4 and 5 (the stair gates) and the Flying Ickies of risk 3, in `mm9r_1000terrors/convert.py`; Njam is waited
  out in segment 11.
- Risk 7: `play_lua` now has `take_chest()`, and segment 11 takes both keys from their chests.
- Risk 10: `party_defeat` now sets the view up, so the woken party walks.
- Risk 11 (Tamur and Thorolf2 after a load), in `mm9r_frosgardcity/citylua.py`.

Each converter README records its change. Later the same day the Stairs Key requirement was withdrawn (MM9 opens the gate without it), and the water hall's stones became MM9's sinking WeightedLifts: a touch sinks one after 1 s, and it rises 2 s later carrying what is over it, which is MM9's way out of the pool. Segment 61's running jumps follow each landing at once. The pool stair (risk 1) waits for the user's decision.

---

## Traversal risks and suspected bugs (read first)

1. **The water hall needs running jumps (the normal Jump key, not the spell). walk_to cannot do them.** The hall lies
   at x 10977–17331, y −10721–−16620. Its stepping stones are MM9's `WeightedLift0-15` (MM9 sinks each one 160 LT
   under the party; our build keeps them static, README:166/262). They are 491-unit squares at z −128 over water: bed
   −620, surface −251. The gaps between stones are 246 straight and 348 or 409 diagonal.
   - The party's jump: `DefaultJumpVelocity` 480, `PartyGravityPerSecond` 1280 (IndoorPartyRuntime.cpp:24-26).
     Integration is semi-implicit Euler at 1/128 s (v −= g·dt, then z += v·dt; IndoorMovementController.cpp:2336-2347).
     The apex is **88.1** (measured 84.6 at 0.30 s), airtime about 0.75 s. At run speed (760 u/s with
     `always_run=true`) the jump carries about **570**. Walking (`run_walk_modifier`) carries about **285**: that
     lands 30 short of a 246 gap from 66 back, and never clears the diagonals.
   - The Jump spell (v 1000, lift 5, PartySpellSystem.cpp:35-36) peaks at 392. The water surface jump (704,
     IndoorWater.h:102) lifts the feet about 191 from the swimming depth (feet −387), to about −196. That is below
     every stone and rim (−128/−113), so **a party in the pool cannot climb onto any stone**. The pool's only exit is the
     south ramp (x 12370–12708, y −16159→−18186, then east to SecretDoor2 at (13676, −18161)), into the south hall.
   - Southbound is fine without jumping: swim, take the ramp, click SecretDoor2 (validated). **Northbound** from the
     south hall and the sealed room has no route without jumps. My geometric BFS (rise ≤ 50) reaches only the south
     hall, the south-east rooms, the bolt corridor, the sealed room and the pool. Six running hops do it (validated:
     `movement_segment` with `jump: true`, coordinates in L5 below).
   - This is very likely the "only with Jump" spot the user hit: whoever falls in, or does not run, is stuck south.
     **Proposed converter deviation** (as for the Dark Passageway): add a climb-out from the pool bed onto the central
     dais. For example, a flight of 11 treads of 46 (each ≤ 50, the `MaximumRise`) from the bed (−620) up to the dais
     rim (−113) against the dais' west face (x 13691, y −12400…−12150), built inside the water volume. Or let the
     weighted lifts sink as MM9's do (a mover pose at −538 when stood on), which re-creates MM9's intent but not a
     walk. The hops already work, so the deviation is optional; it matters only for walking-speed or non-jumping
     players.
2. **Rotating and sliding doors close on their own, and a click from inside a leaf's swing fails.** MM9's
   `CloseWaitTime` is carried: 5 s for LowerDoor3-18, RotatingDoor0/1, SecretDoor2, EDoor3/4 and FoyerDoorSouth1/2;
   8 s for SBrick0/1; 10 s for StairGate0. A click while the party stands in a leaf's arc leaves the party stuck. This
   happened at SecretDoor2 from (13623, −18020), LowerDoor3/4 from (8162, −8715) and FoyerDoorSouth from
   (690, −17609). Pattern: stop 250–350 before the door on its axis, `click(event)`, `wait(3.2)`, then walk through
   (`plan: false`). EDoor3/4's leaves meet exactly at y −18330, so a walk aimed along that line clicks between the
   leaves ("nothing to click ahead"). Walk along y −18290 and let walk_to's click-ahead open it.
   Monsters can open EDoor first, and a pre-click would then close it.
3. **Invulnerable actors body-block corridors.** Both full Tomb runs stalled in the entry level's central corridor at
   about (8010, −8600, −143), each for its last 25–30 s.
   - Actor 113, the Tomb's Njam (`NjamtheMeddler0`, key 108, `mm9_can_receive_damage: false`), stood 83 away. He
     appears at the Njam triggers for 20–60 s and hunts the party (1000terrors.lua:256-277). His triggers are
     TriggerNjam0 (7306..8689, −9370..−9114, the central corridor), 1/2/3/4/6 (the crypts), 7 (783..2166,
     −8320..−8064, the west wing) and Marker5 (the sealed room's trap).
   - Actor 18, one of the 19 Flying Ickies (actors 0-18, `mm9_can_receive_damage: false`, dormant until
     TriggerFlyingCritters (4511..5893, −16389..−16133), which is right beside the Tomb's start), stood 68 away. Their
     flight paths are not carried (README:149), so awake they idle in the corridors.
   - `clear_hostiles` also "kills" these 19 Ickies on every sweep, so `killed=` counts in the logs run to the
     hundreds. The count is meaningless.
   - A `play_lua: {source: "wait(61)"}` after each Njam trigger box lets him vanish, and is what a player does.
     Probes p22/p23 passed the corridor both with and without the wait; the block is random.
   - **Converter-side fix to propose:** keep the Ickies dormant (no `go` wake while their paths are missing), or make
     them non-blocking.
4. **The Tomb's lock logic is looser than MM9's: two sequence breaks.**
   - `StairGate` (event 115, at (8090, −7020, 230)) opens on a click. No lock is set at load (1000terrors.lua:408,
     664-669), so the Lesser Demon in the sealed room (actor 76, `DEATH[76]`, lua:114) is not needed. MM9's StairGate
     has no `PushOpen`; only LesserDemon0's death opens it. It moves at 3 LT/s and takes 54 s to open.
   - `StairGate0` (event 369, lua:503-506) opens without the Stairs Key. It takes item 600 only if the party carries
     it. MM9's `DoorLock.scr "600; 1"` requires the key.
   - Converter fix: set `LockStairGate` at load and drop its click, and make handler 369 refuse without item 600, as
     handler 367 already does for 599.
5. **StairGate0 auto-closes, and the Lua's open flag goes stale.** It shuts about 10 s after opening (probe p7b). The
   script still keeps `OpenStairGate0 = 1`, so the next `click(369)` only clears the flag (`closeGroup` on a gate that
   is already shut) and a third click opens it. The README contradicts this (README:154 "a click opens and shuts it",
   README:267 "StairGate0 stays open once opened"). The monster poll (lua:628) also stops reopening it. Walk through
   within 10 s of `wait(13.8)`.
6. **walk_to arrives on xy alone, and the planner gives a straight route to a point under the current floor.**
   `std::hypot(goal.x - pose.x, goal.y - pose.y)` is at ScenarioRuntimeDriver.cpp:1549. A target of
   (8310, −8450, −2079), given from the entry level, "arrived" at (8296, −8402, **−143**) with "planned (1 waypoints,
   0 nodes)". Use the spiral's foot (8462, −6322, −2092), which nothing on the entry level overlaps, then an
   `assert: party_position` with `z_min`/`z_max` after every change of level.
7. **Chests cannot be looted by a scenario.** `click(42)` and `click(53)` open the loot screen, and nothing takes the
   items: there is no take-all step, console command or `play_lua` call. The Maze Key (10599, KeyChest3, event 53) is
   required at ToLowerTombGate (lua:493-497). The Stairs Key (10600, TreasureChest5, event 42) is required in MM9 but
   not here (risk 4). The probes use `grant_item` as a stand-in. **A runner addition is needed**, for example
   `play_lua` `take_chest()` or a `chest_take_all` step that drives `takeAllActiveChestItems`
   (GameplayOverlayInputController.cpp:765).
8. **Planner traps.** walk_to's route works over the indoor path map, so some legs need `via` points:
   - Trap-door strip (937..1920, −13870..−11412, z −2570): the planner routes down into the trap-door pit
     (858, −12094, −3246), a closed water pit. Use `via` (2200, −12150) → (1430, −12150) → (1430, −13800) → (1430,
     −14400).
   - Central corridor: from (10649, −12265) the planner stalls at (9355, −12147) near statue 5. Use `via` (9892,
     −12361), (9512, −12880), (9101, −13065), (8218, −12616) before planning on to (8000, −7300).
   - Wind maze: the path map does not join the maze's raised walkways or the ledge ("partial"). The 50-point `via`
     list in L9 comes from a geometric BFS and was walked.
   - Bolt corridor: `SBrick0/1` (event 114, x 10179, y −22585…−23112) close its west end. MM9 opens them by a push;
     here they need `click(114)` both ways, and they auto-close after 8 s.
9. **The win switch needs the party north of y −9421** (1000terrors.lua:517-518), past the double gate Door0/Door1.
   The gate opens only on the end Greater Demon's death (lua:564-569).
10. **After `party_defeat` the woken party cannot walk until a save is reloaded.** After the defeat in Frosgard, a
    `set_pose` beside the Hall's door followed by `walk_to` stayed stuck at (19800, −11703) for 17 s. With
    `save_game` then `load_game` between them it walks (probe `defeat.yml`). Suspected leftover defeat state in the
    runtime. End segment 09 with the defeat and its save, as segment 04 does.
11. **Frosgard City reload hides Tamur.** Every map load runs `show(0, false); show(1, false)` and starts the battle
    only once (key 377) (frosgardcity.lua:321, 329). Never save and reload in the city before Tamur joins (key 106).
    Thorolf2's approach talk (lua:343) did not fire within 8 s from 750 away; click him (`interact_actor 4`).
12. **Hall of the Gods: Philip (actor 4) wanders** and blocked the aisle at (4384, 2951, 686) on the way out. Place the
    party at the door (as segment 08 does) or walk with a retry.
13. **There is no wind in the wind maze.** The DAT has no `Fan` or `Wind` objects. `Trigger19Close/Open` send to
    `Fan15/18/21/23` and `Wind15/…`, which do not exist and have no box (lua:177-178, objects.txt line 1826-1827). The
    guide's "fans push you about" does not apply to our build, and probably not to MM9's shipped map either.
14. Small notes:
    - The quest overlay labels qbit 90470 (Njam's chase) "Pass through Dungeon of Secrets" and 90190 (Tamur joined)
      "Go to Thronheim…". MM9 key ids are reused there, which is harmless for asserts.
    - The chess capture camera (2 s, `chess_capture_<n>`) plays on each attacked square.
    - The Tomb's Njam taunt (`njam_taunt`, Trigger19 at x 1720..1884, y −17285..−15974, z 2253..2580) plays when the
      top route crosses it (key 497). It is not required.

No spot needs a crouch. No spot needs the Jump **spell**: the maze, the ledge and ramps, the lift and the top level
were all walked. Only the water hall (risk 1) needs the normal jump.

---

## Segment 09: Sven, Frosgard, Tamur Leng (validated on `08_six_fires.oysav`)

Start: Hall of the Gods, keys 90102, 90103 and 90189 set, 90104 clear (90085 is set: Thorolf's first "What is it?"
row, which forbids 85, stays hidden).

1. Out of the hall: `walk_to (-7700, 2949, 1) expect: dialog`, then "OK", then `follow_map_move` → `arslegardcity.blv`.
   The exit is ExitTriggerHall at (−7619, 2949, 174); arrival is at (19999, −11703, 493).
2. **Sven Forkbeard**, actor 33, at (15073, −11138, 1). He is shown with key 102 and without 104
   (arslegardcity.lua:114, 163). Use `set_pose (15273, −11138, 1) yaw π`, then `interact_actor 33`, then these lines
   (NPC3.rude:39, 1):
   - `"Sven!  It is good to see you!"` (two spaces; requires 103, gives **104**)
   - `"Gather the army.  We shall make for Frosgard immediately!"`
   - `"Goodbye."`

   The exit hook 50152 gives **486** (lua:105-106). Assert `qbit_set [90104, 90486]`.
3. Leave for Thjorgard by the bridge: ExitTrigger4 at (14418, 3043, −82), half size 410×164×410. Use `set_pose (14418,
   2500, −82) yaw π/2`, then `walk_to (14418, 3100, −82) expect: dialog`, then "OK" → `thjorgard.blv` (arrival
   (−11665, 16700, 1291)). ExitTrigger3, the clouds box at (9953, −5600, −744), is the other way out.
4. To Frosgard: `travel: {map: frosgard.blv, days: 3}`. The Sea's Fang sails from Thjorgard on Wednesdays; overland
   takes 8 days through Thjorgard's ExitTrigger1 at (−11916, −20013, 3461). Then go into the city:
   `set_pose (1783, 3700, 1738) yaw −π/2`, `walk_to (1783, 3250, 1738) expect: dialog`, "OK" → `frosgardcity.blv`,
   arriving at FrosgardCityStart (10486, 7209, −4).
5. **The battle starts on arrival** (map load with 104 and without 377; frosgardcity.lua:262-275, 329). It gives key
   **377** and shows Forad (actor 0, (−819, −1556, 1)) and Tamur (actor 1, (−3768, −1475, 45)). The Horde summons are:
   - rows 9129/9130/9131 at Atlimarker (7700, −901): 2 + 1 + 1
   - BadGuys0 (5243, −4342): 2 + 1
   - BadGuys2 (5734, 4424): 2 + 1
   - BadGuys3 (−1393, −1638): 2 of row 9131, beside Forad and Tamur
   - 4 clan soldiers (row 9107) at (7291, −2048)

   Trigger0 (event 234, a floor face at (4424, −82, 3)) brings a second wave at (5161, 1720) and 3 soldiers
   (lua:276-283). **Nothing has to die**: Tamur's talk has no requirement. Assert `qbit_set [90377]`, then
   `clear_hostiles {radius: 3000}` at Tamur.
6. Forad Darre is optional. His approach talk opens his dialogue within 140 of him (lua:336-338). It reads "There you
   are, Traitor!!!", then "Not without killing us, he hasn't!", then "We could never rule alongside a traitor!", then
   "Goodbye." (NPC2.rude:23, 9, 1). Its close turns him hostile (lua:209-213). His death gives 494 and 18 500
   experience (lua:222-226). His first click gives 480.
7. **Tamur Leng**: `set_pose (−3568, −1475, 45) yaw π`, `interact_actor 1`, then these lines in order
   (NPC309.rude:8, 7, 6, 5, 4, 3, 1):
   - `"We have come to end this, Tamur Leng!"`
   - `"The traitor is finished."`
   - `"You are beaten!  What makes you think you will escape?"`
   - `"Destiny?  What are you talking about?"`
   - `"That cannot be!  We are destined to stop you!"`
   - `"WE have a Writ of Fate!!"` (gives **106**)
   - `"Come with us!"`, which closes the talk itself: **no `cancel_dialog`**

   The exit 50069 gives **190** and 22 500 experience, `addHireling(309)`, removes Tamur and shows Thorolf2
   (lua:196-202). Assert `qbit_set [90106, 90190]`.
8. **Thorolf Ratatoskssen** (Thorolf2, actor 4, at (−1147, −1720, 1)): `set_pose (−1450, −1720, 1) yaw 0`, then
   `interact_actor 4` straight away, then these lines (NPC378.rude:6, 3, 2):
   - `"What is it?"` (requires 106, gives **107**)
   - `"What?  Why?"`
   - `"Very well.  We shall go."`, which closes itself

   Exit 50073: he vanishes. Assert `qbit_set [90107]`.
9. Return to Arslegard the story's way, by dying. Use `setup_shortcut immortal false`, then `party_defeat:
   {knock_out: true, wait_seconds: 5, expect_map: arslegardcity.blv}`, `advance_runtime 2`, and save the checkpoint
   `09_frosgard_tamur`. The defeat must end the segment: risk 10.

## Segment 10: Krohn and Njam's Key (validated)

1. Start: `load_game 09…`, immortal, assert `arslegardcity.blv`, `qbit_set [90107]`, `qbit_clear [90108]`. Keys 98
   and 9515 are set from earlier, so no gate scene plays.
2. Into the Hall: `set_pose (19800, −11703, 493) yaw 0`, `walk_to (20300, −11703, 493) expect: dialog`, "OK" →
   `hallofthegods.blv`.
3. `walk_to (5600, 2949, 851) radius 150`: planned, about 17 s. **Krohn** is actor 0 at (5898, 2949, 851); actor 8,
   another Krohn, is the hidden epilogue copy. Then `interact_actor 0` and these lines (NPC335.rude:9, 8, 7, 3, 6, 5,
   4, 1):
   - `"As you have summoned us, so we have come."` (requires 107)
   - `"We have a Writ of Fate!  It says we're supposed to stop him!"`
   - `"Yes sir!"`
   - `"Njam the Meddler?"`
   - `"What task?"`
   - `"How are we supposed to get him to follow us?"`
   - `"We will do this for you."` (gives **108**)
   - `"Goodbye."`

   The exit 50124 gives **Njam's Key, item 10576**, key **191** and 22 500 experience (hallofthegods.lua:33-40). Assert
   `qbit_set [90108, 90191]` and `has_item(10576)`. Save `10_krohn`.

## Segment 11: Njam's house and the Tomb

### Arslegard (validated on the real save)

1. Out of the hall: place the party near the door (risk 12) with `set_pose (−7000, 2949, 1) yaw π`, then `walk_to
   (−7700, 2949, 1) expect: dialog`, "OK".
2. **Njam's house**: its front door, NjamDoor0/1, is event 231 with faces at (7598, −10085, −308). Item 10576 opens
   it; otherwise the status reads "The door is locked." (arslegardcity.lua:45-49). Use `set_pose (7670, −10450, −491)
   yaw π/2` and `click(231); wait(2)`.
3. The letter on the desk is Prop8, event 338, at (7352, −9681, −399). Use `walk_to (7352, −9780, −491)` and
   `click(338)`: item **10575** "Njam's Struggle" (lua:146-151).
4. The chase is trigger face event 240 at (7326, −9026, −486). Use `walk_to (7326, −9026, −486)`. It gives key
   **470**, 22 500 experience, and Njam (actor 34, 6 600 HP, *damageable*) turns hostile and follows (lua:64-81).
   **Do not `clear_hostiles` in Arslegard after this**: it would kill him, for no gain.
5. The Tomb's door: ExitTrigger1 at (−922, −6501, −297), with the locked double-door faces (event 230) at
   (−932, −6552). Use `set_pose (−500, −6542, −424) yaw π`, `walk_to (−1100, −6542, −424) expect: dialog`, then
   **"OK"** (the dialogue is titled "Thousand Terrors"), then `follow_map_move` → `1000terrors.blv`. The start is
   (5202, −16630, −142). ExitTrigger0, back to Arslegard, is 256 south of the start at (5192, −16886), so do not walk
   south.

### The Tomb (`1000terrors`): the walked route

Every block below passed in the probes. `walk_to` defaults are `clear_hostiles: 1500`, `timeout_seconds` 40–300.

**L1. Start to the west water gate.**
`walk_to (10650, −12265, −128)` (planned), then `click(117); wait(12.5)`. WaterGate0 is a portcullis that rises
307 at 26 u/s; it shuts again after MM9's 15 s. Then `walk_to (11959, −12265, −128) plan: false`.

**L2. The water hall southbound, swimming.** `walk_to via [[12250,−13000,−387],[12250,−16000,−387],[12540,−16100,
−387],[12540,−18000,−374]] → (13300, −18020, −239) plan: false`. This route keeps west of the stones: a straight line
hits the stone at x 12462..12954. The party swims at the surface (feet −387) and lands on the ramp. Then
`clear_hostiles`, `click(122); wait(3)` (SecretDoor2, rotating, opened from 300 away), and `walk_to (14100, −18020,
−128) plan: false`.

**L3. The bolt corridor and the sealed room.**
- `walk_to (13900, −22770, −128)`, then `walk_to (10400, −22770) plan: false`. The plates Trigger5-17 (boxes at x
  11246..13714, y −22029..−23503) sink and the wall shooters fire.
- `click(114); wait(2)` for the secret bricks, then `walk_to (9300, −22770) plan: false`. Entering the box
  TriggerPuzzleDoor0 (9426..9682, −23168..−22400) shows puzzle wall A behind the party at x 9882
  (`ButtonTriggerState` = 1), summons TP2/TP3 Lesser Demons at (8028, −21955/−23593), and with key 108 shows Njam
  at (7700, −22774) (lua:156).
- `walk_to (7300, −22774, −66)`, then four rounds of `clear_hostiles 4000` + `advance 3`. LesserDemon0 is actor 76 at
  (9175, −21135); its death opens StairGate. Assert `mapvar('OpenStairGate') == 1`. Lesser Demons rise again as
  Greater Demons: lua:115-116, 573-578.
- TreasureChest5 is event 42 at (6994, −22774, −31). It holds the **Stairs Key 10600** and item 10593; see risk 7.

**L4. Puzzle wall A** (block k is event 300+k, PuzzleDoor k; k = 4·row + column, row 0 is the top row and column 0
is the north end, y −22626, the left side seen from inside facing east).
- A click pushes the block and its four neighbours (lua:303-317). The pull Pull1, event 360 at (9728, −23010, 164),
  resets the wall.
- From `walk_to (9500, −22770)`: `click(360); wait(1.5)`, then `click(302), click(304), click(311), click(313)`
  (the guide's 3rd of the top row, 1st of the 2nd, 4th of the 3rd and 2nd of the bottom row; the mirror 301, 307,
  308, 314 also works). Exhaustive check: 16 solutions exist and both of these are among them. Assert
  `mapvar('ButtonTriggerState') == 2`; the wall vanishes after 0.8 s.
- `walk_to (10400, −22770) plan: false`, `click(114); wait(2)`, then `walk_to (10600, −22770)`.
- The same solution works for walls B (events 316-331, Pull2 361) and C (events 332-347, Pull3 362) in the south-east
  rooms, which only guard treasure.

**L5. Back north across the water hall (jumps, risk 1).**
`walk_to (14180, −17100, −128)`, then `click(123); wait(12.5)` (WaterGate2 at (14182, −16794)), then `walk_to
(14180, −15700) plan: false`. Then six hops. Each hop is a `walk_to` (plan false, radius 24) to its take-off point,
then a `movement_segment {input: forward, jump: true, seconds: 0.75, start: <take-off>, yaw_degrees: <yaw>,
expect_stop: <landing>, loose_tolerance, tolerance_xy 200, tolerance_z 60}`, then `advance_runtime 1`:

| take-off | yaw° | lands near | stone (x range, y range) |
| --- | --- | --- | --- |
| (14180, −15700) | 89.8 | (14182, −15130) | 13937..14428, −15391..−14899 |
| (13990, −14950) | 118.9 | (13715, −14451) | 13445..13937, −14653..−14162 |
| (13490, −14200) | 135.3 | (13085, −13799) | 12708..13199, −13916..−13425 |
| (13150, −13470) | 84.7 | (13203, −12902) | 12954..13445, −13179..−12687 |
| (13000, −12730) | 118.7 | (12726, −12230) | 12462..12954, −12442..−11950 |
| (12500, −12196) | 180.0 | (11930, −12196) | the west floor, 10977..12216 |

Then `walk_to (11100, −12265) plan: false`, `click(117); wait(12.5)`, and `walk_to (10600, −12265)`.
- **Optional:** HiddenButton1, event 366 at (13891, −12278, −190) on the central dais, opens the TreasureDoors to the
  north room with TreasureChest11/12 (events 44/45).

**L6. The central corridor and the stair gates.**
- `walk_to via [[9892,−12361],[9512,−12880],[9101,−13065],[8218,−12616]] → (8000, −7300, −128)`. Mind risk 3:
  TriggerNjam0 crosses this corridor.
- The sorceress statues fire from TrigSorcStatueOn/On0 (boxes in the side rooms, lua:129-136), harmlessly.
- `play_lua`: `if mapvar('OpenStairGate') ~= 1 then click(115); wait(57) end; click(369); wait(13.8)`. StairGate is
  event 115; StairGate0 is event 369, at (8305, −6973), and stays open about 10 s.
- `walk_to (8462, −6322, −2092)` goes down the 53-step spiral stair. The planner hiccups once at the landing (8237,
  −6641, −1572) and recovers. Assert `party_position z −2150..−2000`.

**L7. The crypts to the chess room.**
- `walk_to (8310, −8450, −2079)` and assert its z. `click(106); wait(3.2)` (LowerDoor3/4, axis x 8310), then
  `walk_to (8310, −9300) plan: false`.
- The skull: TrigSkelHeadOn0 (8187..8443, −8975..−8719) sets SkeletonHead's two shooters going after 1 s (lua:137,
  349-360). Bolts, harmless.
- `walk_to (6850, −11904)`, `click(107); wait(3.2)` (LowerDoor5/6, axis y −11904), `walk_to (6150, −11904) plan:
  false`.
- The trap-door strip `via` points (risk 8). Rotating Lever 17, event 363 at (922, −11904), would drop the trap doors:
  never click it.
- `walk_to (3450, −15345, −2755)`, `click(112); click(113); wait(3.5)` (RotatingDoor0/1 at x 3840), then
  `walk_to via [[4300,−15345]] → (6450, −16350, −2749)`. That is the west platform of the chess room; the room
  itself is a sea-monster pool, BlueWater2.

**L8. The chess board.** The board is at x 6623..8425 and y −14508..−16474 (8 × 8 squares of about 225 × 246). Columns
run 1–8 from west to east and rows 1–8 from north to south. Attacked squares are listed by the Lua's CHESS table
(lua:183, poll 607-627):
```
row 1  . . X . . . X .      P = piece (solid model): pawns at (2,4) and (4,4), bishops at (5,3) and (6,7),
row 2  X . . X X X X .          knights at (3,1) and (6,4)
row 3  X X X X P . . X      X = attacked: 60 damage on stepping in, and a 2 s camera
row 4  . P X P . P . .      the pawn trap: (1,3) and (1,5); stepping in queens the pawn into a Terror
row 5  X . X X . . X X          (row 9164, 1 069 HP) after 2 s (lua:593-602)
row 6  . X . . X . X X
row 7  X . . . . P . .
row 8  . . . . X . X .
```
The guide's diagonal line brushes corners of attacked squares, including the trap square (1,5) beside the entry
square (1,4). The validated route has **1 hit and no queen**: it enters at row 8 and passes beside the bishop at (6,7):

`walk_to via [[6735,−16350],[7411,−16350],[7411,−16105],[7636,−16105],[7755,−15990],[7861,−15860],[7861,−15614],
[8087,−15614],[8087,−15368],[8312,−15368],[8835,−15368,−2755]] → (9700, −15600, −2662) plan: false, radius: 40`
(z −2749 on the board).

The bridge east is at y −15222..−15713, from column 8, row 4. KeyChest3 is event 53 at (9923, −15647, −2580): the
**Maze Key 10599** (risk 7). TreasureChest2 is event 52, beside it. Go back the same way in reverse, then through
`click(112); click(113)` and `walk_to (3300, −15345)`.

**L9. The north-west gate and the wind maze.**
- `walk_to (−706, −3900, −2570)` (planned, through the crypt shallows at −3062, about 24 s).
- ChessNote0 is event 372 at (−707, −3052, −2319); it gives 10598 "Care for a nice game of chess?".
- ToLowerTombGate is event 367 at (−706, −3026, −1864). It opens with item 10599; otherwise the status reads "Locked"
  (lua:493-497). Then `walk_to (−706, −2700, −2324) plan: false`.
- The maze (sector 19) has three tiers:
  - a floor at −2324, ringed by a slatted bridge;
  - a moat around everything, which is water BlueWater3, bed −2826, surface −2458 (the README calls it "the chess
    pool");
  - a ramp up (x −584..−338, y 768..983) to a platform at −2186, and a second ramp (y 1966..2150) to the −2079
    walkways.
- From the walkways, the east strip (x 4577..4823) runs south to (2120..4823, −2949..−246). Then the **ledge** ramp
  climbs west from −2079 to −1341 at (−829..−338, −3318..−2703). The zigzag runs east up to −604 at (2200, −3300),
  then west up to −128 at (0..300, −3500), at ToWindMazeGate.
- Max rise on the BFS route is 31, so **no jump is needed**. The validated via list:

```
[[-706,-1100,-2324],[-578,-972,-2324],[-546,-972,-2324],[-322,-748,-2324],[-322,-684,-2324],[-98,-460,-2324],
 [414,-460,-2324],[894,20,-2324],[1886,20,-2324],[1886,-172,-2324],[2110,-396,-2324],[2366,-396,-2324],
 [2622,-140,-2324],[2622,436,-2324],[2654,468,-2324],[2622,500,-2324],[-66,500,-2324],[-98,468,-2324],
 [-322,468,-2324],[-354,500,-2324],[-354,1364,-2186],[-450,1460,-2186],[-461,1500,-2186],[-461,2364,-2079],
 [-333,2492,-2079],[147,2492,-2079],[179,2460,-2079],[179,2172,-2079],[403,1948,-2079],[1651,1948,-2079],
 [1651,2012,-2079],[1875,2236,-2079],[2131,2236,-2079],[2131,1916,-2079],[2355,1692,-2079],[3347,1692,-2079],
 [3379,1724,-2079],[3379,3356,-2079],[3600,3950,-2079],[4000,4055,-2079],[4600,4100,-2079],[4563,-452,-2079],
 [3539,-1476,-2079],[3340,-1500,-2079],[2124,-2716,-2079],[-148,-2716,-1417],[-372,-2940,-1341],
 [-372,-3068,-1341],[-340,-3100,-1341],[1996,-3100,-641]]  →  (2284, -3388, -604), plan: false, radius: 40
```

Then `walk_to (150, −3500, −128) plan: false`, `click(116); wait(3)` (ToWindMazeGate, (276, −3778)), and `walk_to
(276, −4300) plan: false`.
- The other ladder: Ladder7 runs from (−2253, −2936, −2821) to (−2094), exiting at (−2253, −2629, −2314). It belongs
  to the maze's entry room, and the route does not use it.

**L10. The west wing, the fireball plates and the lift.**
- `walk_to (4823, −12560, −123)` (planned, about 16 s). It passes FireballPlate (Trigger3 box at (41..512,
  −5571..−5243)) and FireballPlate2 (Trigger4 at (3098..3354, −8968..−8712)); both fire, harmlessly.
- `walk_to (4823, −13100, −82) plan: false` puts the party on the lift deck: GearElevator, door 14, deck x
  4598..5048, y −13199..−12749, at −82 down and 2253 up. The deck is 41 above the shaft floor (−123), so there is no
  step problem.
- LowerLever is event 364 at (4823, −13235, 84). Use `click(364); wait(14)`; the lift rises 2335 at 512 u/s
  (lua:478-489). Assert `party_position z 2200..2300`. LowerLever0 (event 365) is at the top, at (4823, −12708, 2429).

**L11. The top level** (the lift has no way north or east; the route goes around).
- `walk_to (4823, −17700, 2253) plan: false`, then `walk_to (4650, −18290)`, then `clear_hostiles 2500`, then
  `walk_to (4000, −18290) plan: false`. EDoor3/4 is event 119; let walk_to's click-ahead open it (risk 2).
- `walk_to (690, −17850)`, `clear_hostiles`, `click(368); wait(3.2)`. FoyerDoorSouth1/2 is event 368 at
  (645, −17556) and needs key 108, otherwise "Locked" (lua:508-511). Then `walk_to (690, −17250) plan: false`.
- `walk_to (4400, −11800, 2304)` (planned). This crosses Trigger19 (`njam_taunt`, 18.8 s, key 497), Trigger1
  (Spawner6), the FoyerShooterPlate box (3267..3922, −13486..−13240), and Trigger18 in the octagon (4588..4751,
  −12534..−10895), which spawns four demons at the statues (lua:88-91, 125-128, 147).
- `walk_to (7500, −11700, 2777)`, up the ramp into the demon hall.

**L12. Demon waves, the end demon and the switch.**
- 12 rounds of `clear_hostiles 3000` + `advance 4`. The counted spawns are Spawner8 (GreaterDemon1, actor 68, dies),
  TP5 (Oculus7, actor 69) and Spawner13 (Oculus9, actor 70). After the third, the **end Greater Demon** appears at
  (8929, −11674, 2777). Its death sets `EndDemonDead` and opens Door0/Door1 (lua:242-252, 564-569). Assert
  `mapvar('EndDemonDead') == 1`.
- `walk_to (8294, −9700, 2777)`, then `walk_to via [[8294,−9300,2806]] → (8800, −9300, 2806) plan: false`.
- WinMan, event 370 at (8928, −9378, 2898): `click(370)` starts the cinematic `njam_freeze_win` (36.7 s; experience,
  then key **109**, then `MoveToMap` to the Hall; lua:516-528, 863-891). Then `advance_runtime {seconds: 45,
  follow_map_move: true}` and assert `qbit_set [90109]` and `map hallofthegods.blv`.
- **The epilogue**: on loading the Hall with 109 and without item 394, the cinematic `gods_epilogue` (105.6 s) plays.
  It gives the **Writ of Fate 10394** (hallofthegods.lua:91-96, 144-155). `advance_runtime 120` with
  `follow_map_move`, then `has_item(10394)`.
- Optional: Krohn's `"We have imprisoned Njam."` (NPC335 335/3) is available afterwards.

---

## The guide (ch3_5.yml) against our build

- "Run over the floor plates … the room at the corridor's west end": it omits the secret bricks (event 114) that close
  the corridor.
- "The Lesser Demon, whose death opens the inner stair gate": true, but a click opens it too (risk 4). The Stairs Key
  is not needed (risk 4).
- "Leave the water hall south by its water gate": that needs the stone hops. Swimming south by the ramp and SecretDoor2
  works without them; north needs them (risk 1).
- The chess "safe line": its diagonals touch attacked corners, including the pawn trap. Use the route above.
- "The wind maze, where fans push you about": there are no fans (risk 13).
- "On the top level, clear the demon hall east of the lift": the lift does not connect to it. Go south through EDoor
  and FoyerDoorSouth (key 108) and north through the octagon, where four statue demons spawn.
- "Thorolf appears beside you": he appears at his own spot (−1147, −1720), not beside the party.

## Original MM9 (rpggamers.com walkthrough)

The source agrees on the chests in the southern room, the block puzzle, the chess room in the south-east, the maze
north, and "follow the ramps up to the zigzag room … go to the very end and pull a lever to go up". It gives a chess
route (F1, G2, G3, G4, G5, H6, G7, G8, E7, D8) in a different square notation. It mentions no fans, no water room and
no jumping. MM9's DAT shows the water-hall stones as sinking `WeightedLift`s (MoveDist 160 LT, MoveDelay 1 s), so MM9
also expected hopping across them.
