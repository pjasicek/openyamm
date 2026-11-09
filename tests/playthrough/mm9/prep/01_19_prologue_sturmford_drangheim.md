# Prep: segments 01-19 (a new game, the Prologue, Sturmford and Drangheim)

> **Directions (corrected 2026-11-09):** compass words in this note were taken from raw coordinates as if +y were
> north. On MM9's outdoor maps (regions and cities, `flip_u` in `worlds/mm9/ui/maps/catalog.yml`) the map a player
> sees has +y at the bottom and +x at the left, so those directions are turned 180 degrees; the guide's directions,
> which follow the maps and agree with the original walkthroughs, are right. Indoor maps are not affected.

Research for `01_ravensford.yml` to `19_*.yml` (2026-11-08). Sources: the map scripts and scenes in
`assets_dev/worlds/mm9/` (what the game runs), the RUDE files in `assets_dev/worlds/mm9/dialogue/rude/`, the
converters' `work/content.json` and `work/doors.json`, and headless probes in
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/early1/`.

Conventions: MM9 key K = qbit 90000+K (keys >= 5000 as in the other sheets: 5012 -> 95012). An MM9 item N is engine
item 10000+N **unless `worlds/mm9/data_tables/item_aliases.txt` maps it to an engine item** (`engine_mapping` rows:
the spell scrolls, e.g. 511 Lightning Bolt -> 317). An actor's click event is 53000 + its DAT object index, its
dialogue-exit event 50000 + that index. +y is north, yaw 0 faces east.

RUDE rows (CSV): c2 node, c3 choice, c4 the line a player reads, c6 next node (999 end, -1 goodbye, -10 hire), c7,
c9, c11, c13, c15 required keys, c16-c20 granted, c21-c25 forbidden, c26-c30 removed.

---

## How a new MM9 game starts (segment 01)

- Chedian is continent 5 (`engine/data_tables/character_selection.yml`, `continent_settings.txt` row 5): every
  base class but the Necromancer, every race but the undead. The start is **bootcamp.blv (Ravensford) at
  (323, -8494, 1291), direction 1530**, its own StartPoint0. `world.yml`'s `start: guberland.blv` is not what a new
  game uses (`GameApplication::startNewSessionFromCharacterCreation` resolves the continent's death map 1). So a new
  game does reach the Prologue as MM9 does: Ravensford, the boat, the Isle of Ashes.
- Since the R11 promotion (2026-11-08) Ravensford's scrolls are world items (scene `world_items`), no longer click
  events: the party walks below each and takes it with `pick_up` (the shelf's pairs nearer one first; from
  (x, -8190, 1291)). The Shopkeepers scroll from (-1562, -3130, 1303), not closer (the counter's edge traps the party).
- There are no MM9-specific classes: Chedian offers the merged classes (Archer, Cleric, Druid, Knight, Monk,
  Paladin, Ranger, Thief, Sorcerer ...). The party: Ragnar (Knight, human, portrait 77 = MM9 PC01), Hrothgar
  (Cleric, dwarf, 89 = PC13), Grisha (Thief, half-orc, 86 = PC10; Bow as her chosen skill, a bow: the party's only ranged weapon, needed for
  Anskram's drawbridge chains), Aelwen (Sorcerer, elf, 82 = PC06), level 1,
  each class's free skills plus two, 200 gold and 5 food.
- `new_game_flow` differs from the menu's new game (harness, not the game): it loads the map's StartPoint0 (the
  same point here), it does not hand out the starter items (`grantCreatedCharacterStarterItems`: potion bottle,
  reagent, weapons, rings, spellbooks), and it needs an explicit `equipment` map per member. The party is equipped
  with its class weapons instead.

## Ravensford (bootcamp.blv, segment 01)

| what | where | event / note |
| --- | --- | --- |
| Grandpa (Old Man), actor 20, RUDE 436 | (323, -8822, 1291) | greets the party on sight (56207, once); click 53207, exit 50207 |
| scrolls Spells, Skills, Classes, Notes | (268-376, -7975..-8057, z 1381) | world items 10581-10584 |
| spell scrolls | (-476..-343, -8000) and (1009..1111, -8000) | world items, engine 317, 311, 379, 306, 334, 314 |
| Shopkeepers scroll | store counter (-1562, -2929, 1418) | world item 10585 |
| Movement I/II, Combat | training course (4149-4439, -6180..-6997); Combat up ladders 3-5 at (5688, -3502, 2381) | world items 10586-10588, not taken (below) |
| museum door (MuseumDoor2) | (523, -7788) | 105, rotating |
| store doors | east wall x ~ -1000, y -3370..-3675 | 109, rotating, close by themselves |
| dock exit ExitTrigger0 | (9129, 10634, 1289) | no prompt, six days, to isleofashes StartPoint0 (-11816, 1004, 456) |

Talk 1: "We'd like to start our training." -> "Where do we start?" -> "What do we do when we're finished?" ->
"Why?" (key 474) -> "Goodbye, Grandpa."; the exit gives Interface I and II (10579, 10580). Talk 2: "We're ready to
leave." (needs 474) -> "Why?" (475) -> "Goodbye, Grandpa."; the exit gives Strategy Tips (10589), Disarm Trap Skill
(10298) and Identify Item Skill (10302), key 496. Leaving by the boat: key 473 (NPC436.scr Leave). Reading the
scrolls is not checked (the guide is right).

Walking: rotating doors must be clicked from outside their swing, then waited for (2.5-3 s); the walker's own
"click ahead" toggles a door the party stands against and can close it again. The training course is fenced at
x 3982 (the walker found nothing to click; its doors 107/108/112 were not researched) and the Combat scroll needs
ladders, which `walk_to` cannot climb: those three optional scrolls are skipped. The Lobber Pods between the
village and the dock are killed on the way.

## The Isle of Ashes (segments 03 and 05)

The guide's compass follows the player's map, which is turned 180 degrees against raw coordinates (its "north-west" hut is at our coordinates' south-east). The arrival is
a separate west island.

| who / what | where | events |
| --- | --- | --- |
| Forad Darre, actor 13, RUDE 2 | (2171, -7506, 147); stand at (2171, -7300, 147) | 53061 / 50061 |
| Yrsa the Troll, actor 12, RUDE 1 | in her hut (2866, -16475, 411) | 53046 / 50046 |
| hut door (RotatingDoor8) | west wall, x 2314, y -16568..-16404; stand at (1950, -16486, 420) | 30769; closes itself after 5 s |
| dragonflies, actors 0-11 | x -2600..-6400, y -16000..-19300, flying over the meadow (floor ~790) | 8 deaths: key 27 |
| bunker doors (BunkerDoor1/2) | y 4690, x -1126..-840; slope south at (-983, 3950, 180) | 30498 (takes the Turret Key) |
| bunker chest (TreasureChest2) | (-721, 4844, 21) | 43 |
| book / lectern | (-947, 5416, 125) | 30495 / 30496: cinematic book_sinking (17 s) |

Keys: 480 first person met (800 xp), 365 Yrsa met (800), 477, 368 Forad's talk ends (4000), 7 the dragonfly task,
27 eight dragonflies (200), 366 (2000), 1 destiny accepted (Unite the Clans), 367 (2000), 29 Forad hired, 371,
469 Turret Key given (item 10568), 28 the cinematic (5200, the islet sinks).

Talks: Forad 1: "Our boat crashed on its way to Mendossus." -> "No.  Who is that?" -> "Goodbye.". Yrsa 1: "Who are
you?" -> "Goodbye". Yrsa 2 (key 27): "Who are you?" -> "Very well." -> "Destiny?  What destiny?" -> "What does
Tamur Leng have to do with us?" -> "Thronheim?  Kira the Cold's soldiers will certainly stop them!" -> "You spoke
of a destiny.  Is this our fate?" -> "For the sake of all the Chedian, we will take this quest." -> "Goodbye";
"How do we get off this island?" is optional. Forad 2: "Our boat crashed ..." -> "Yes.  Yrsa sent us to find you"
-> "She has charged us with a quest, and we need your help." -> "It is our destiny to unite the six clans against
Tamur Leng." -> "What is that?" -> "Fair enough.  We'll take care of them then." -> "Welcome Aboard." (hire: the
talk closes, Forad leaves the map). Yrsa 3: "How do we through that door?" (sic) -> "Goodbye".

Placing the party on the slope south of the bunker skips nothing needed: Trigger2's three Bone Thrashers rise
there and die. **set_pose z must be the floor's**: at (-960, 3300) the ground is 841 and a pose at z 300 dropped the
party under the island into the sea (it then "drowned" at z -985).

Minor faults (not story): the well south of the hut (3004, -17428) and Forad's cookpot have no event; Bone Thrasher
0 and the Lich King are placed about 1600 under the ground (the Lich is an invisible spawner); Yrsa hands out
another Turret Key on any later talk once the door has used the first.

## Sturmford City and Bjarni (segment 07)

The boat from the isle lands at sturmford StartPoint0 (7511, -17581, 247). The city's dock gate is ExitTrigger1
(1014, -12589, 543; stand at (1014, -12900, 260)), its prompt "OK", arriving at SturmfordDocks. The city's way back
to the region is ExitN (11346, 14541) in the north-east (stand at (11141, 14300, 19723)); the guide's "south gate"
is wrong.

| who / what | where | events |
| --- | --- | --- |
| Bjarni Thorvaldssen, actor 56, RUDE 45 | throne (7311, 8192, 19822); stand at (7000, 8192, 19743) yaw 0 | 53808 / 50808 |
| Town Portal altar | palace entrance hall (4833, 9083); stand at (4844, 8800, 19723) | 337: key 5012 |
| Ivsar (tavern), actor 27, RUDE 90 | (-655, 655, 19757), the tavern by the docks in the south-west (the guide says north-east) | 53829 / 50829; shown with key 242 |

Bjarni: "We know you are of great importance, and would like your help." -> "We need your help to defeat Tamur
Leng." -> "He is the leader of the Hordes that will soon overrun us." -> "They come from Beldonia.  We must unite the
clans against them." (key 20) -> "What is the first thing you need?" -> "How will we do that?" -> "How do we get
in?" -> "We will do this for you." (11) -> "What is the second thing you need?" -> "You want us to break into a
prison?" -> "We will do this for you." (12) -> "Thanks for your time.". Reports: "Anskram Keep is clear." (needs 39,
gives 41; exit: key 149, 10 500 xp, 3 000 gold); "We've rescued Ivsar." (needs 196, gives 21) -> "He is here." ->
"Thank you." (exit: key 117, 16 500 xp, 3 500 gold); the pledge "We've done as you've asked.  Will you join the
coalition?" (needs 41 and 21, gives 38) -> "We have much work to do, yet.". "We've already done that." (Anskram)
needs key 148, which nothing grants (faithful dead row). Lines that play clans off each other end the talk.

## Sturmford region: Anskram Keep from outside (segments 09 and the defences)

The keep is north-east of the arrival, not south-west. The weak wall is destructible 199 (100 HP), the sea-side
(east) wall of the SE tower at (20011, 14905, 1270); stand at (20090, 14905, 1188) yaw pi and attack (30 attacks of
the level-1 party at 1.5 s broke it). The tower's spiral stair is two counter-clockwise turns from its south-west
corner: (19250, 14720, 1178) east along y 14650, north up the east side, west along y 15250 to the landing (1628),
again to 2120. The walk_to planner finds no route up it (it routes outside); the step list in segment 09 is walked
with `plan: false`. From the top: north on the east wall walk (x 19600, z 2120), west over the bridge (z 2202,
y 16700) to the keep's terrace (18300, 16677, 2120) and the high door Anskramkeepback (17992, 16677), prompt "OK",
arriving at the keep's south end (0, 41, -491). The keep's ground door 987 (0, 15973) leads out to the gate passage
(15135, 16677, 1152).

Six Basilisks (two inside the courtyard), not five.

## Anskram Keep (segment 09)

Floor z -491 on the whole route. Doors are double or round doors that shut by themselves (7 s); each is clicked from
about 300 in front, then the party waits 2 s and walks through; the walker's own "click ahead" toggles a door the
party stands against and often closes it again. Doors on the route: 107 (0, 491), 111 (2130, 6390), 113 (-2130,
6390), 102 (4424, ~7050, east corridor), 127 / 123 (4751, 6717 / 6062), 119 (4096, 9011), 132 (2785, 9011), 117 / 115
(-4752, 5407 / 4096), 110 (-4096, 9011), 129 (-2786, 9011), 131 / 130 (+-2130, 11650).

A gate starts when the party crosses one of its pads (170-183) and sends five Imps one at a time; when all five are
dead the fire goes out and key 510+k is set; all eight: key 39 (the journal says return to Bjarni). Order walked:
4 (r29, pad 171), 5 (r21, pad 172), 1 (pad 181 in the east corridor, closet r37 through 119 and 132), 7 (pad 176,
r23), 6 (pad 175, r10), 2 (pad 179, closet r36 through 110 and 129), then the airlock (lever 71 from (550, 9009),
lever 72 from (-550, 9014), a click on the gate 89 from (0, 10300)), 0 (pad 178, closet r41) and 3 (pad 180, closet
r40). Out round the shaft at x -1300 (its slabs drop once key 39 is held; crossing the TriggerGiantImp pads raises
the giant Imp, killed on the way).

PivotWallTrap3 (event 79, the west corridor y 8054-8422 before gate 2's pad) springs when the party steps on the
corridor's half of its floor, which is the whole corridor width (x < -4250; the corridor is x -4582..-4224). A party
that walks on falls into its spike pit, whose ladder (walk_to cannot climb) leads back south. A player passes it as
the converter README describes: one step onto the trap's edge springs it, the party steps back, the wall arm turns
over and lies as floor for 5 s, and the party crosses (both ways). Not a bug, but worth a sign for players.

Pad 175 (gate 6, a 102 square in the doorway recess) did not fire for a party that walked onto its centre
diagonally from (-4427, 4362) and stopped there (two runs); walking straight west across it from the corridor
(-4424, 4096) fires it. Pressure plates fire on a change of the party's support face
(`IndoorSceneRuntime::updatePartyFaceTriggers`); the MM9 converter's plates lie 3 above the floor and
`IndoorMovementController.cpp:2589-2650` deliberately does not stand the party on trigger faces, so whether a small
plate becomes the support face depends on the approach. Repro: `scratchpad/early1/k_pad.yml` (first version).

## The roads between Sturmford and Drangheim (segments 11, 17, 19)

Sturmford's ExitTrigger3 (-3215, 22165; stand at (-3215, 20900, 760) yaw pi/2) leads by road (two days) to
Drangheim's FTDrangheim (-15739, -21244, 2682); back, Drangheim's ExitTrigger1 (-14661, -21275) lies east of that
arrival point: walk east from (-15739, -21244, 2682). (From the east side, (-14000, -21275), the party is stuck: a
dead end.) Drangheim City's gate: stand at (11458, -4164, 757), walk east to (12032, -4164, 963); the city's way
out is its ExitTrigger0 (9667, -4178; stand at (10000, -4178, 1010) yaw pi). The boats (Sturmford actor 56 Olaf the
Thronish, Drangheim actor 32 Svein Hjarrandssen, one day) were not used.

## Drangheim City and Sigmund (segments 11 and 19)

Sigmund the Stressed is actor 20 (19005, -5530, 1476), RUDE 87, click 53334 / exit 50334, on the town hall's upper
floor, which opens onto the hill district (doors 104/105), not "behind the clerk" (guide error); the town hall is on
the city's east side (guide: west). Stand at (19005, -5390, 1476) yaw -pi/2. The Town Portal altar is event 330
(18964, -5939): key 5013. Tasks: "We have come seeking your aid." -> "The Beldonian Hordes are marching to
Chedian." (43) -> "Join us!  We are trying to unite the Clans against them." -> "What do you need done?" -> "We will
do this for you." (44) -> "What else do you need done?" -> "We will do this for you." (46) -> "Thanks for your
time."; the Trap Key (item 596) comes when the talk closes. Reports: "We've disabled Anskram Keep's defenses." (needs
47, gives 49) -> "Thank you."; "We've got the Crona Kiga." (needs 48, gives 50) -> "Certainly." -> "Thank you.";
"Now that we've done both tasks for you, will you join us?" -> "Yes." (51) -> "We have much to do, yet.  We'll let
you know.". The exit pays 49 (key 171) and 50 (key 170, the Kiga taken).

Faithful dead end (MM9's own data): "We've already done that." for the defences needs key 372, which a party can
only get without key 44, but the trapdoors need the Trap Key that comes with 44. Taking the Kiga before accepting
the task gives key 169, after which MM9's "We've already retrieved that." gives 46, never 50 (MM9 soft-locked
Drangheim there); the converter's Deviation now gives 50 when that talk closes (bug 10).

## Drangheim Prison (segment 13)

Front door: Drangheim's ExitTrigger8 (stand at (-8359, -16250, 1989) yaw -pi/2, walk to (-8359, -16583)). The clerk
(Guard2, actor 54, RUDE 426) stands behind a U-shaped counter (x -2400..-1950, y -6800..-6400, open to the south);
the party walks between the gate guards into the U and talks across it: "We want to get into the prison.",
"Alright.", "No.", "No.", "Uhhh, no." (key 5007), "Goodbye."; the pass (item 446) on closing.

**The gate guards (actors 52 and 53, immobile, friendly) stand in the only gap past the counter.** Since MM9's
friendly people are solid (`friendlyActorsBlockParty`, 2026-11-07), the party cannot get by until each is told
"We want to get in." -> "Alright.  Anything else?" -> "Goodbye." (their exits 51033/51034 move them aside). The
research sheet called that talk optional; it is now required (not a bug: it is the intended use of the row).

Route up (all doors clicked about 300 in front): EntryDoor 123 (-2171, -6021), DDoor7 116 (-942, -4014), the hall,
the stairs to the main storey (-2535, -1639, -1905) and the middle cells (-3655, -407, -1577), the stair tower to
(-4903, 776, -410), ElevatorDoor 122 (x -4157), the top floor's landing (-3285, 550, -82). The guard station's door
103 (pivot (-3338, 445)) serves both the landing and the cell corridor; it shuts 5 s after opening and the guards
open it too, so the party waits 6 s for it to be shut before clicking (a click on an open door shuts it). Levers on
the station's console: 205 opens Ivsar's cell (the last on the south side), 203 Antoni's. The cell corridor is
walked at y 20 (a top-floor guard stands at (-1434, 164)). Ivsar (actor 41, RUDE 90): "We've come to take you back to
Sturmford." -> "We've been sent by Bjarni Thorvaldssen to rescue you." (17) -> "Let's go." -> "Goodbye."; the alarm
(5006) turns the guards hostile. Way out: the same doors in reverse; at the entry door the walker opens it when the
fleeing guards have left it shut. Outside, Ivsar (actor 33) speaks up on sight: "What is it, General?" (242) ->
"We're supposed to take you to see Bjarni." -> "Very well.". In Sturmford's tavern: "Come on, General." (196).

The cook (Aymril Banito), Antoni and the well route were not taken (optional).

## The Chasm of the Dead (segment 15)

Entrance: Drangheim's ExitTrigger7 (stand at (2500, -21450, 2540) yaw 0.355). The walk_to planner handles the
tombs, the spike corridor (its wave cannot be avoided: the plate spans the corridor) and the stair to Door14 (105)
when each leg has a `z_tolerance` (without one an "arrival" on the wrong level counts). **The planner's own route
into the canyon jumps off its ledges** (a fall of 3700 to the deep floor): the walkable descent is given as waypoints
(the canyon to (4904, 5240, -492), the ledge path (2100, -800, -1520) .. (1000, 1300, -2010) .. (600, 4000, -1884),
north to (1800, 13688, -3170), the ramp east along y 14420 to (4620, 14420, -3932), the deep floor). Doors 126, 124
and 125 are 245 wide (x 2458..2703), narrower than the corridor: pass at x 2590. The pivot floor (event 239) is
passed on its east strip x 2742; the ceiling crusher plate at x >= 2720. The Crona Kiga is a world item at
(2580, -18473, -5340) since the R11 promotion: `pick_up` from (2584, -18200) (key 48, 10000 xp); 14 mummies wake.
Doors 107 and 109 on the way back are opened by the walker when it finds them shut.

## Anskram Keep's defences (segment 17)

Hatch1 (event 101, Trap Key) on the gatehouse's roof deck: stand at (15718, 16100, 2120), click, wait 2.5 s, walk
north onto it: the party drops into the chamber (floor 1628). Lever 103 at (15511, 16676): portcullis. The chains are
destructibles 315 (y 17199) and 316 (y 16113) — the research had them swapped — thin slabs x 14868..16200, z
2038..2048, running through the chamber under its ceiling. **A blade does not reach them** (tried from the chamber
floor, the deck and the bridges); a bow does, but only from beyond blow reach (407): within it the attacking member
strikes instead. Shots: from (15700, 16620, 1628) yaw -pi/2 pitch 28 deg (316) and (15700, 16700) yaw pi/2 (315),
with the Thief selected (`press_action: select_member` first: `press_action: attack` ignores `member_index`). From the
gate passage only 315 can be hit (yaw 1.824 pitch 0.937). Both broken and the lever pulled: key 47 and 10000 xp
(`sturmford.lua:66-80`). The chamber's only way out is Ladder0 (walk_to cannot climb): `movement_segment` forward
with `fly_up` for 2.0 s from (15718, 15820, 1628) facing south ends at its top exit (15831, 15750, 2120).

Since the hit-box fix (bug 8) a blow from the chamber floor breaks each chain: from (15700, 16350, 1628) yaw -pi/2
pitch 52 deg (316) and (15700, 17000) yaw pi/2 pitch 55 deg (315). Before it, only shooting worked. The scrolls from Ravensford did not help: `use_item` of the Lightning Bolt scroll consumed it and cast
nothing at the crosshair (a targeted scroll waits for a target; `cast_spell` needs an actor). The party's Thief
therefore takes Bow at creation.

## Bugs, harness gaps and risks found (2026-11-08)

1. **Harness, --reload and cinematics.** `ScenarioRuntimeDriver::saveBlockedReason` (ScenarioRuntimeDriver.cpp:1462-
   1496) blocks a reload while a cinematic plays, but not while `EventRuntimeState::pendingCinematic` waits for the
   next frame. run.py --reload's save between the book's click (segment 05) and the next step dropped the queued
   cinematic (no key 28, the party stayed on the isle). The game itself starts the cinematic on the next frame, so a
   player cannot save there. Segment 05 waits 1 s in the click's own step (logged ISSUE).
2. **Harness, follow_map_move.** `advanceRuntime` (ScenarioRuntimeDriver.cpp:3839-3845, the check at 3876) `continue`s past the
   `followMapMove` check on every frame whose world input is blocked; a map move already pending when the step
   starts (a cinematic's exit cue that fired in an earlier `play_lua` wait) was never carried out in a 5 s
   advance. Worked round by letting the cinematic play inside the `advance_runtime` step itself.
3. **Engine, save/load of a rotating mover mid-swing.** Saving while PivotWallTrap3 (anskramkeep door 83, sine
   easing) turns under the party and loading straight back puts the party 49 east and 133 lower (it falls into the
   pit), with no time advanced. Repro: `scratchpad/early1/n_trapreload.yml` (from a keep save: step onto the trap's
   south edge at (-4424, 8090), `reload`, print the pose: (-4424, 8088, -493) -> (-4375, 8091, -626)). Segment 09's
   step on and off the trap is one walk so --reload does not save mid-swing (logged ISSUE).
4. **Engine, small trigger plates.** Pad 175 (102 square, 3 above the floor) did not fire for a party that walked
   onto it diagonally and stopped (see "Anskram Keep"); crossing it straight fires it. Plate events fire on support
   face changes (`IndoorSceneRuntime::updatePartyFaceTriggers`, IndoorSceneRuntime.cpp:1295) and trigger faces are
   never stood on by the overlapping-floor rule (IndoorMovementController.cpp:2589-2650).
   It bit again with --reload at gate 0's pad (178): a party that ended a walk standing on the plate without firing
   it, saved and loaded there, never fired it (after a load the first floor face is only recorded), so the gate
   never started and key 39 was out of reach. Segment 09 now crosses the closet pads straight from the north
   ((+-2100, 12230) to (+-2100, 11880)). A player who loads a save made on an unfired plate has to step off it.
5. **Harness, walk_to planner and drops.** In the Chasm the planner's routes jump off ledges (a 3700 fall, lethal for
   a real party); arrival ignores z without `z_tolerance`. The descent is given as waypoints.
6. **Harness, ladders.** `walk_to` cannot climb ladders: Ravensford's Combat scroll and the gatehouse chamber's exit
   need a `movement_segment` with `fly_up` (logged CLIMB in segment 17).
7. **Harness or design, spell scrolls.** `use_item` of a targeted spell scroll (Lightning Bolt) consumes it and
   casts nothing (no projectile, no way to give the waiting spell its crosshair target); `cast_spell` needs an actor,
   so a scroll cannot be aimed at a destructible from a scenario.
8. **Fixed (converter), chains in melee.** The chains' invisible hit boxes were MM9's RayHit slivers, 21 x 10 across:
   a blow from the chamber floor hit them only within about 1.5 degrees of aim (measured: a Cleric broke one at 38
   degrees from (15700, 16424), nothing at 37); the pick and the 407 blow reach were never the problem. The user
   decided (2026-11-08) that blows must break them: `mm9r_sturmford_blv/convert.py` grows both boxes to 96 x 96
   across (only those 8 faces change in the BLV; the scene's door vertex ids shift by the 8 new vertices),
   installed into the review root and assets_dev; `tests/scenarios/mm9/destructibles/anskram_chain_melee.yml` (a
   Knight's blow breaks each) and `sturmford_chain_crosshair.yml` (the bow) pass. Segment 17 now has the Knight
   strike them. Sturmford's layout identity changed: older saves reset Sturmford's map state on entry (the breach,
   chests), and its bake is flagged stale by `stale_bakes.py` (only invisible faces moved).
9. **Converter (minor, not story):** Isle of Ashes: the well south of Yrsa's hut and Forad's cookpot have no event;
   Bone Thrasher 0 and the Lich King sit about 1600 under the ground (`mm9r_isleofashes_blv/convert.py` floor lookup).
10. **Faithful dead ends (MM9's data):** Bjarni's "We've already done that." needs key 148, nothing grants it;
    Sigmund's "We've already done that." needs 372 (unreachable with the Trap Key). **Fixed (converter):** taking
    the Crona Kiga before Sigmund's task (key 169) left no way to key 50, so Drangheim could never pledge; Sigmund's
    exit (`mm9r_drangheimcity/citylua.py`, Deviation) now gives 50 to a party that said "We've already retrieved
    that." (46), holds 169 and carries the Kiga. `tests/scenarios/mm9/crona_kiga_before_task.yml` passes (keys 46,
    50, 170, then 51).
11. **Cosmetic:** the console's qbit descriptions do not match MM9 keys (90001 shows "Complete your training", 90510
    "Find the Green Man"): they seem to come from journal entries numbered like the keys.
12. **Guide errors** (prologue_ch1a.yml): the Isle's compass is turned 180 degrees and the arrival is a separate west
    island; Forad's hire talk lacks "What is that?"; the key line is "How do we through that door?"; Sturmford's way
    to the region is its north-east gate, the keep lies north-east of the dock, its weak wall faces east; six
    Basilisks; the tavern is in the south-west; Sigmund's town hall is on the east side and his floor opens onto the
    hill district; the Ravensford scrolls and the Crona Kiga are now picked up, not clicked; the chains can only be
    shot.

13. **Harness quirk:** `press_action: {action: select_member}` fails for the member already selected (segment 17 picks
    the Knight by selecting the Thief first).

Two converter fixes in this range (bugs 8 and 10, the user's decisions); every key the Prologue and the two clans need is granted.
