# Prep: block C, the dragon chain and the Wizard's Lab

Research for four side-quest scenarios (2026-11-08): `survive_the_training_hall.yml`, `retrieve_the_missing_relic.yml`,
`slay_the_dragon.yml` (the three stages of Snorri's chain, each played once; a later scenario sets the earlier stage's
last key) and `get_black_orb_of_knowledge.yml`. Sources: the map Lua and scenes in `assets_dev/worlds/mm9/` (what the
game runs), RUDE rows in `assets_dev/worlds/mm9/dialogue/rude/` (NPC6, 55, 241, 283 byte-identical to MM9's
`mm9/extracted/RUDE/RUDE/`; greetings from `TOPBLURB.rude`), MM9's scripts (`NPC6.scr`, `NPC55.scr`, `NPC241.scr`,
`NPC283.scr`, `RELIC.scr`, `TRAININGENTER.scr`, `TRAININGHALLEXIT.scr`, `DRAGON.scr`), the journal rows in `NPC997.rude`,
`data_tables/map_transitions.txt`, `transport_routes.txt`, `ui/maps/catalog.yml`, the converter projects
(`mm9r_wizardslab/work/doors.json`), the UHS hints for MM9, and headless discovery runs.

Conventions: MM9 key K = qbit 90000+K; MM9 item N = engine item 10000+N; experience from `MM9.giveExperience` goes in
full to every member and follows `tools/mm9_import_discovery/mm9_quest_xp_profile.yml`.

**Compass.** Directions here follow the in-game map images, as the guide does (`ui/maps/catalog.yml`, also
`output/mm9_site/data/presentations.json`): the region maps (Thjorgard, Lindisfarne, Thronheim, Yorwick, Sturmford)
have `flip_u: true, flip_v: false`, so on their images **-y is up (north) and -x is right (east)**; cities and dungeons
mostly have `flip_v: true` (+y up), though some city images carry their own compass rose (Thronheim City's points N to
the left). Plotting the exits on `lindisfarne.pcx`, `thjorgard.pcx`, `yorwick.pcx` and `thronheimcity.pcx` puts the
monastery in Lindisfarne's north-east, the Dragon's Lair in its north-west, the Training Hall in Thjorgard's north
(left of the Mountain Pass exit in x, i.e. east of it), the Wizard's Lab on Yorwick's south shore and Ealusaid near
Thronheim City's land gate: the guide's directions for these quests are right. (The main playthrough's
`27_monastery_thjorad.yml` header and `prep/20_34_thjorgard_guberland.md` say "the monastery lies at the island's far
south, not north as the guide has it": that used +y = north and is wrong by the map image.)

No quest here needs story state beyond its own chain: Snorri, Ealusaid, the Connecting Tunnels, Yorwick, the lab and
the lair test no key. Party in every scenario: Knight, Cleric, Thief, Sorcerer at level 30.

## Getting around

| from | how | to |
| --- | --- | --- |
| thjorgardcity | Thjorgarddocks (655, -819): stand (655, -400, -19) yaw -pi/2, walk south, "OK" | thjorgard (-9336, 4386) |
| thjorgard | city gate ExitTrigger2 (-8790, 4392): stand (-9300, 4392, 1951) yaw 0, walk east, "OK" | thjorgardcity (655, 164) |
| thjorgard | Training Hall hole ExitTrigger3 (-5526, -18479, 4219), front door ExitTrigger6 (-5153, -16291): both off until key 301 (map vars `Mm9ExitDisabled486`/`114`) | traininghall (0, 287, 1639) chandelier / (0, -3359) |
| lindisfarne | monastery ExitTrigger0 (-11749, -21240): stand (-11250, -21240, 2734) yaw pi, walk west, "OK" | monastery (-327, -935) |
| lindisfarnemonastery | ExitTrigger0 (-328, -1393): walk south from (-328, -1000) | lindisfarne (-10909, -21059) |
| lindisfarne | Dragon's Lair ExitTrigger2 (14947, -16356): stand (14947, -15950, 205) yaw -pi/2, walk south, "OK" | dragonstadium (1802, -5734) facing +y |
| dragonstadium | ExitTrigger0 (2345, -6636): walk back down the tunnel | lindisfarne (15326, -15875) |
| thronheimcity | land gate ExitTrigger1 (14950, 82): stand (14500, 82, 3093) yaw 0, "OK" | thronheim (1412, 5883) |
| thronheim | land gate ExitTrigger2 (1392, 6498): stand (1392, 6100, 1279) yaw pi/2, "OK" | thronheimcity (14377, 164) |
| thronheim | tunnel ExitTrigger6 (16168, -17075): stand (16168, -16700, 2090) yaw -pi/2, "OK" (1 day) | connectingtunnels (17324, -3523) |
| connectingtunnels | walk_to (-17737, -7782, 1501), `clear_hostiles: 1500`, about 81 s; back: walk_to (17243, -3850, 1884), about 124 s | yorwick (-23768, -13565) / thronheim (16168, -16706) |
| yorwick | tunnel ExitTrigger7 (-23768, -13893): stand (-23768, -13565, 1052) yaw -pi/2, "OK" (1 day) | connectingtunnels (-17164, -7782) |
| yorwick | Wizard's Lab ExitTrigger6 (-6575, 17744): stand (-6200, 17744, 1051) yaw pi, "OK" | wizardslab (3154, 7165) facing -x |
| wizardslab | ExitTrigger0 (3727, 7168): walk_to (3850, 7168) from the hall (a target at the box's centre arrives short of it) | yorwick (-6125, 17744) |

Yorwick is reached only through the Connecting Tunnels (no boat, no road); both tunnel walks together take about 30 s
of wall time. Boats Lindisfarne <-> Thronheim: 3 days (`travel`).

## 1. Survive the Training Hall (Thjorgard City, Thjorgard)

| who / what | id | position | notes |
| --- | --- | --- | --- |
| Snorri the Fist | actor 23, RUDE 6 | (-1270, 164, 1), the tavern bar | stand (-1100, 164, 1) yaw pi; click 54068 |
| cracked wall | DestructableBrush7, destructible 479, 15 hp | (-5470, -18444, 4260) | destroyed event 370 |

Snorri (greeting "Greetings, stranger. Buy an old man a drink?"): "Of course." (row 6.1, forbidden 8) -> "Weave your
tale, old man." -> "Who us?  Of course!" -> "What is this task?" -> "Where is it?" (keys 8, 483) -> "If it is there, we
will find it." -> "Goodbye.". After key 301: "Of course." (6.2, needs 301, forbidden 484: "I can see by your faces
that you succeeded...") -> "We're ready for the challenge." (key 484: "Go see Abbot Leffery Caid in Lindisfarne") ->
"Goodbye.". Snorri's .scr has no reward.

The wall: two sword blows break it (checked). Handler 370 (thjorgard.lua:537): exits 486 and 114 on, the Perception
hint off, then once: key 301, `AddValue(BaseMight, 5)`, `AddValue(BaseIntellect, 5)` for the current member (in the
run it was member 2, the one whose blow broke it), 18 500 experience (MM9 20 000), quest.wav. MM9's
`TRAININGENTER.scr` :OnBreak (TELP 1.3) is the same; the hall's own bar on its end door (traininghall.lua:188) gives
the same once. Walking east from the walkway into the hole asks "Training Hall" (source 486); the scenario closes it.

Where the wall is: the hall stands in Thjorgard's north (west of the Mountain Pass exit in x, which is east on the map:
the guide's "east of the Mountain Pass exit" is right). Its central block (roof z 4474-4580, x about -5600..-4600,
y -19000..-17800) is ringed by a walkway at z 4065 (yard 3656); on the -x side (map east) a parapet (top 4147, x
-5843..-5790) closes the walkway, and the cracked wall is the central block's face at x -5470 at the north (-y) end.
The scenario places the party on the walkway at (-5650, -18444, 4065) facing +x (outdoors placement).

**Verified 2026-11-09 (coordinator): yes, on foot, no jumps.** The second ramp is on the hall's +x side (MM9's
west): a tilted brick slab in PhysicsBSP (about 32°, foot (-4211, -18705) z 3676, top (-4518, -19319) z 4106) leaning
on the +x wall, through a gap in the +x parapet (y -19360..-18725). The first rubble on the -x side carries an invisible
ramp (InvisibleBrush3, about 38°) to the plinth's top (z 3656) at y -18640; from there round the +y front and down the
+x corridor (x -4497..-4350). The scenario walks this route. Earlier notes, kept for the record:
**Was: can a player climb up?** UHS (hint 566): "Go around to the east side of the building and climb up some
rubble there. Then go around to where another piece of rubble forms a ramp up. On the top level, move around the
central structure until you find a wall with cracks in it." A height probe (100-unit grid) found rubble rising on the
-x side at x -6800..-6500 from z 3470 (y -18400) to 4450 (y -19600) and on to the hills, and a slope from (-6000,
-19800, 4410) down to the parapet's north corner (-5800, -19450, 4147). Straight `walk_to`s did not get up: from the
yard to the parapet (491 up), from (-5700, -17000) north (a 476 step at y -17650), and up the rubble (stuck at
(-6696, -18976, 3823)). A route with jumps may exist; a hand check is worth doing (`./tools/run_game.sh --isolated th
--world mm9 --map thjorgard.blv --position -6650 -18500 3700`). If the walkway cannot be reached on foot, the quest is
blocked for players (only the front door, which needs key 301, remains).

## 2. Retrieve the Missing Relic (Lindisfarne Monastery, Wizard's Lab)

| who / what | id | position | notes |
| --- | --- | --- | --- |
| Abbot Leffery Caid | actor 0, RUDE 283 | (-425, 11366, 103), main altar (north end) | click 53408, exit 50408 |
| the Saint's Relic | world item 0 (`wizardslab:barrel`, item 10368) | (-860, 12657, 90) | pickup event 334; forbidden qbit 90340 |

Monastery walk (as segment 27): walk_to (-330, 1000) plan false; click 101 (nave doors 1, 2); via (-100, 1700) to
(-100, 5600); click 102 (doors 3, 4); via (-100, 6300) to (-330, 6900); walk_to (-425, 11000) planned. Back the same
way, clicking a door group when `door_state` is not open. Bred Gagii (actor 7, mobile) wanders about (-348, 4035)
and after a reload stood on the aisle's east line (x -112): the nave is walked via (-100, 3000), (-250, 3800),
(-250, 4700) between him and the pews (east pews from x about 180; immobile monks 13 and 14 at (-348, 2401) and
(-497, 4326)).

Leffery (greeting "You aren't from around here are you? Would you be willing to do a task for me?"): "We're here to
summon the dragon." (283.1, needs 484, forbidden 338) -> "Whatever it takes to summon the dragon." -> "So what's the
problem?" -> "Where do you think the relic is?" (3.2) -> "Who is he?" -> "We will retrieve the real relic for you.
Where is this lab?" (key 338) -> "Goodbye.". With the relic: "We've found your relic." (283.5, needs 340, keys 341,
485) -> "Thank you." (back to his first page) -> "Not right now." ends it; the close (handler 50408, NPC283.scr
:MissingRelic): with 341 and not 342, item 368 taken, 3 000 gold, 12 500 experience (MM9 80 000), key 342. Relic taken
before the quest (key 339): "We found a bone fragment in the Wizard's Lab." on page 3 (needs 339) gives 341 and 485 too.

The relic (RELIC.scr): with 338 and no 340, key 340; without 338 and no 339, key 339. Here a world item lying where
MM9's barrel object was (a pick_up, not a click on a barrel); handler 334 sets the key.

**Wizard's Lab teleporters** (wizardslab.lua:177-290). Six stations (walk-in boxes, polled four times a second, one
trip per crystal click; the destination resets after the trip):

| station | box (x, y) | arrival (facing) | crystals here (event: destination) |
| --- | --- | --- | --- |
| 1 Blue | -16488..-16158, 8314..8644, z 236 | (-16323, 8274, 204) (-y) | 230 yellow, 231 white, 232 red, 233 purple, 234 green; white0 at (-16097, 8724) |
| 5 White (entrance hall) | -206..124, 7003..7333, z 31 | (164, 7168, 2) (+x) | 250 yellow, 251 red, 252 purple, 253 green, 254 blue; on its west side ((-287, 7393), (-379, 7045)) |
| 6 Yellow | 327..657, 10464..10794, z 31 | (492, 10834, 2) (+y) | 255 white (717, 10383), 256 red, 257 purple, 258 green, 259 blue |

The white pad can only be entered from the east (+x): a rail closes its south side (the party stops at y 6879) and
the crystals its west. Closets: Teleporter1 (5114..5331, 11811..11926) behind Closet1Door (event 101, doors 15/16,
closed) in the easternmost bedroom's south wall -> (-1710, 13230), facing kept; Teleporter2 (-1809..-1612,
13357..13472) behind Closet2Door (event 102, open) in the relic room -> (5222, 12083).

The four bedrooms off the yellow corridor (y about 11370), doors at y 11571-11653: DoubleDoor11 (event 103, x -3433),
DoubleDoor10 (event 200, x -812, the relic room: locked, nothing unlocks it), DoubleDoor9 (109, x 1810), DoubleDoor8
(108, x 4431, the easternmost). Route played: walk_to (300, 7168) from the entrance (18 Eyes etc. die on the way),
click 250, Forward onto the pad -> yellow arrival; walk_to (4431, 11450), click 108 if shut, walk_to (5222, 12060),
click 101, Forward into the closet -> relic room; walk_to (-860, 12550), pick_up 10368; walk_to (-1710, 13200),
Forward into its closet -> east bedroom; walk_to (4431, 11800), click 108 if shut, walk_to (492, 10950), click 255,
walk_to via (492, 10950) to (164, 7168) radius 150 (enters the yellow pad from its north on the line to the hall's
arrival); walk_to (3850, 7168) to the exit.

walk_to cannot use a same-map teleporter whose arrival does not lie beyond the box on the line of approach: after
the teleport it steers on at the via it had not reached, and fails stuck. The white pad (to yellow) and both closets
are like that, so those steps are `movement_segment`s (Forward 0.8 s from where the party stands), logged as
`TELEPORT`. Runner gap: see the report (proposed: end the walk when a same-map move lands within `radius` of the
final point).

## 3. Slay the Dragon (Dragon's Lair)

| who / what | id | position | notes |
| --- | --- | --- | --- |
| Dragon King | actor 0, group 1, monster 9212, hidden | (1864, 737, -163) | killed hook 95 |
| DragonTrigger | box (1055..2591, -4813..-4557, -125..366), polled 4/s | the entry tunnel | handler 60 |

Walking up the tunnel (walk_to (1802, -4400)) wakes him (map var `DragonAwake`); Winged Mutants (monster 9160) appear
at two markers after 45 s, then 90, 180 ... more (also after his death, as MM9's Wait 22 does). He dies to
`clear_hostiles` on the way to (1864, -500); handler 95: key 472, item 577 (Super Guber Award, 10577). Journal
(NPC997): 482 -> "Speak to Snorri"; 483 -> "Complete his task"; 484 -> "meet Abbot Leffery"; 485 -> "Leffery Caid has
the relic... meet the dragon in his cave"; 472 ends it. Nothing tests 485: the dragon wakes without the relic (as in
MM9: DragonTrigger is a plain trigger, Dragon.scr checks no key; the guide's tip says so).

## 4. Get Black Orb of Knowledge (Thronheim City, Wizard's Lab)

| who | id | position | notes |
| --- | --- | --- | --- |
| Ealusaid A'Norta a'thrakan | actor 0, RUDE 241 | (6308, -164, 3114) | stand (6308, -20, 3114) yaw -pi/2; click 53054, exit 50054 |
| Robinssen | actor 57, group 29, RUDE 55 | (-16323, 5038, -165), the star hall | click 53044, exit 50044; 15+ hostiles round him |

Ealusaid ("Hello. Did you need some healing?"): "Yes." (241.1, forbidden 313) -> "Why not?" (forbidden 311) ->
"What's stopping you?" -> "What can we do to help?" -> "Where can we find one?" -> "We will find it for you." (key
311; the talk ends). Robinssen ("Who are you? How did you get in here?"): "We've heard you are the Mad Wizard
Robinssen." (55.1, needs 311, forbidden 312) -> "We were wondering if you could help us." -> "We're sure you're not
mad." -> "We've heard you have a Black Orb of Knowledge." -> "Do you have one?  If you do, we'd like to buy it from
you." -> "Name your price." -> "That's pretty steep." -> "Well, alright.  2000 gold it is." (key 312) -> "Goodbye.";
the close: 2 000 gold taken, key 313, item 250 (without the gold: 312 taken, "You don't have enough gold."). Ealusaid:
"We've got the Black Orb." (241.2, needs 313, forbidden 314) -> "Not only did he have it, he invented it." (314) ->
"Goodbye."; the close: key 315, 18 500 experience (MM9 50 000), 10 000 gold, item 250 taken.

Lab route: walk_to (300, 7168), click 254 (blue), walk_to via (300, 7168) to (-16323, 8274) radius 150 (the line west
crosses the white pad); walk_to (-16323, 5300) with `clear_hostiles: 2500` (15 die), `clear_hostiles: 3000` (4 more);
talk. Back: walk_to (-16323, 8230), click 231 (white), Forward onto the blue pad (logged TELEPORT) -> (164, 7168);
walk_to (3850, 7168) to the exit.

## Discrepancies

Guide (`tools/mm9_site/story/side_*.yml`):

1. side_c survive-the-training-hall, maps caption "the cracked wall is on its north side", and step "Climb the tumble
   of rocks beside the hall": the wall is the central block's east face (map east) at the north end, seen from the
   walkway that rings the upper level. Proposed: "Climb the rubble on the hall's east side to the walkway round its
   upper level; the cracked wall is the central block's face at the walkway's north end." and caption "The Training
   Hall in the north; the cracked wall faces the upper walkway's east side at its north end." (if the climb works).
2. side_b and side_c disagree on the relic route only in detail; both are right in this build. side_b's is exact (the
   easternmost of the four bedrooms; open its closet, step in; the relic room is second from the west, its door locked
   for good). side_c's "step into its small teleporter" should say "open the closet in its south wall and step in";
   "Click the barrel there for the Saint's Relic" should be "pick up the Saint's Relic lying by the barrel" (a world
   item here). Proposed side_c step: "Inside, click the yellow crystal on the west side of the white teleporter and
   step onto it from the east. Walk east along the yellow corridor to the last bedroom, open the closet in its south
   wall and step in: you arrive in the relic room, whose own door is locked for good. Pick up the Saint's Relic by the
   barrel and leave through that room's closet."
3. get-black-orb: "At the white teleporter in the entrance hall, click the blue crystal" is right; worth adding that
   the pad is entered from its east side (its south side is railed off).
4. All quoted dialogue lines, rewards (18 500 + 5/5; 3 000 + 12 500; 18 500 + 10 000; the Super Guber Award) and map
   directions (hall in the north east of the Mountain Pass exit; monastery north-east; lair north-west) match the game.

Game (suspected bugs):

1. **Snorri lets the party skip the Training Hall** (user 2026-11-09: kept MM9-faithful for now, to revisit; README "Kept as MM9 had it") (original MM9 data, `NPC6.rude` row 6 choice 3): "Of course." with
   483 and without 301 replies "Come back and buy me another drink when you've learned that for yourselves." but goes
   to node 15, whose "We're ready for the challenge." has no condition and grants 484 (Leffery's dragon talk). Fix
   (MM9-faithful or not is the user's call): that row's next 15 -> 999, as a dialogue override in the RUDE overlay (the
   mechanism `promotions.yml` uses; it has added rows and waived keys but no row override yet), not an edit of the
   imported RUDE. Confirmed headless: a new game with keys 8 and 483 set, Snorri's "Of course." offers only "We're
   ready for the challenge.", which sets 484 without 301.
2. **The Training Hall's walkway may be unreachable on foot** (unverified, section 1). If so it is a converter problem
   in `mm9r_thjorgard_blv` (the rubble's collision) and blocks the quest for players.
3. `dragonstadium.lua:118` (handler 95) gives key 472 and the award whoever kills the dragon; MM9's `DRAGON.scr`
   :OnDeath checks `IsPlayer`. A dragon killed by a party summon or by the Winged Mutants... still rewards here. Minor.
4. Ealusaid's "We've got the Black Orb." needs only key 313; a party that sold the orb still gets the reward (the take
   fails quietly). Same in MM9 (`NPC241.scr`); not a bug in the port.
5. Console cosmetics: `qbit dump` describes 90008 as "Find a way off the island" and 90338/90340 as other quests' notes
   (the known mismatch of MM9 keys and the engine's quest descriptions, prep/01_19 item 11).
