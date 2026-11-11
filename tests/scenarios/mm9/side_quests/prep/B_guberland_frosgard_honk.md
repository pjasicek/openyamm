# Prep: block B (Guberland, Frosgard, Thronheim, the Temple of Honk)

Research for four side-quest scenarios (2026-11-08):

| Scenario | Quest (guide id) | Giver | Story state set |
| --- | --- | --- | --- |
| `convince_the_dook_to_leave_guberland.yml` | convince-the-dook-to-leave-guberland | Markel the Great, Guberland City | none |
| `sell_brewmaster_smith_s_new_concoction_to_guberland.yml` | sell-brewmaster-smith-s-new-concoction-to-guberland | Brewmaster Smith, Frosgard City | keys 72, 73 (Frosgard's docks freed: every Frosgard boat needs 73) |
| `take_the_news_to_the_temple_of_ratatosk.yml` | take-the-news-to-the-temple-of-ratatosk | Dagfari the Peevish, Thronheim City | none |
| `steal_the_golden_honk.yml` | steal-the-golden-honk | Fre, Hall of the Gods | keys 98 (Hanndl's refusal), 9515 (the Great Gate opened) |

Sources: map Lua `assets_dev/worlds/mm9/events/maps/{guberlandcity,guberland,dookscastle,frosgardcity,thronheimcity,
hallofthegods,arslegardcity,templeofhonk}.lua`; scenes `assets_dev/worlds/mm9/maps/*.scene.yml`; RUDE
`assets_dev/worlds/mm9/dialogue/rude/NPC{127,415,184,141,242,246,337}.rude` (0-based columns: 3 prompt, 4 answer,
5 next node, required keys 6/8/10/12/14, given 15-19, forbidden 20-24, taken 25-29); journal
`assets_dev/worlds/mm9/data_tables/english/quests_overlay.txt`; `map_transitions.txt`, `transport_routes.txt`;
MM9's `mm9/extracted/SCRIPTS/SCRIPTS/NPC{127,415,141,184,242,246,337}.scr`, `HONK.scr`, `HONKHOSTILITY.inc`,
`HONKKEY.scr`, `HONKACCOUNTANT.inc`; converter notes `level_generation/projects/mm9r_{dookscastle,templeofhonk}/README.md`
and their `work/rooms_*.png` (LT units: native = LT x 2.56) and `work/doors.json`. `tools/mm9_site/story/online_notes.md`
only mentions the Dook ("talk to Dook at his castle, mention the sword"), which agrees.

Keys: MM9 key K = qbit 90000 + K (9515 -> 99515). Items: engine id 10000 + MM9 id. All four start with the same
level-28 Knight/Cleric/Thief/Sorcerer party, 10 000 gold, `immortal`, experience set to 0 (so
`runtime_event_variable: {id: 13, member_index: 0}` reads the quest experience; `MM9.giveExperience` gives the full
amount to every member). Every claim below passed headless (binary of 2026-11-08 23:19/23:32) in the scenarios or in
probes kept in the shared scratchpad's `blockB/` folder.

## 1. Convince the Dook to leave Guberland

**Markel the Great** (guberlandcity actor 13, (-2978, -9175, 23), RUDE 127; click 53815, close 50815,
`guberlandcity.lua:116, 124`). Pose `(-2722, -9175, 23) yaw pi`. Lines: "Is there anything we can do for you?"
(127.3: forbids 64 and 40, so no story key is needed and the errand closes at the war council) -> "What would you have
us do?" -> "We shall get rid of him for you." (key 64) -> "Goodbye.". Journal 90610 (64, not 65).

**To the castle.** City gate ExitTrigger0 (-655, -41, 307): pose `(-655, -600, -9) yaw pi/2`, walk north, "OK" ->
guberland.blv at (6151, -10359). Dook's Castle: guberland ExitTrigger0 (-13341, 17189, 328), half (246, 82, 246):
pose `(-13341, 16700, 121) yaw pi/2`, walk north, "OK" -> dookscastle StartPoint0 (0, 1393, 1). Back: the castle's
ExitTrigger0 (0, 1147, 205) just south of the arrival; the region's DooksCastleExit (-13341, 16820, 121); Guberland
City's gate ExitTriggerGuberland (6131, -9194, 1651): pose `(6131, -9700, 1651) yaw pi/2` (segment 20's).

**The castle walked** (dungeon). Gate hall (two flights; planned) -> central corridor (native x -269..217, y
3533..9344) -> crossing (y 6661..7153) -> west along it to x -2560 -> north through the throne room's double door
(door05, event 105, movers 10/11, at y ~8046, x -2742..-2388) -> the Dook at the apse. Via points used:
`[-10, 4000] [-160, 4250] [-160, 5520] [0, 5640] [0, 6750] [-2470, 6750] [-2470, 8400] [-2250, 8800] [-2250, 9700]`
to `(-2400, 9950, 513)` radius 120, one `walk_to` (planned legs, straight where clear). The walk clicks door05 itself.

**The guards** (17 Half Orc Captains in groups 1/3, `dookscastle.lua:38-60`): friendly until a guard is hurt or killed
(hooks 96/97: alarm bell, map var `Hostile` = 1, groups 1 and 3 hostile, sleepers woken) or the shield (event 70)
opens the secret door. `clear_hostiles` only kills actors hostile to the party, so it never touches them; the
scenario keeps it off inside the castle anyway and checks `mapvar("Hostile") == 0`. Positions at the start: 2 (0,
4588), 1 (-41, 5366), sergeant 42 (-573, 5243), sleepers 43-46 at x +-205, y 5693-6533 (SleepTrigger at the corridor's
south end wakes them one every 3 s), 12 (-82, 7045), 3 (-41, 8397), 10 (-2662, 7741), 13 (-2621, 8724), 0 (-2540,
9462), 8 (-3154, 9052). **They wander** (`mm9_ai.wander: aimless`), so the routes thread between them.

**The Dook** (actor 16, (-2540, 10281, 513), RUDE 415, immobile): "We've been sent by Markel the Great." (needs 64) ->
"He wants you to leave." -> "Well there's always the sword." -> "Yes." -> "Then leave." (key 65) -> "Make it quick."
-> "Goodbye.". The other branch, "There's no way you'd leave?" -> "We'll pass that on to Markel." gives 138, and
Markel then has "The Dook says he won't leave." -> "Yes, sir!" (no progress). Journal 90612 (65, not 66).

**The return**: walk to `(-2620, 8260)` via `[-2250, 9700] [-2250, 8800] [-2620, 8600]` (facing the door), wait 10 s,
`press_interact` (door05), 1.5 s, then one walk to `(0, 1100, 0)` `expect: dialog` via `[-2600, 7400] [-2560, 6750]
[40, 6750] [40, 5500] [100, 4200]`.

**Markel's reward**: "The Dook is finished." (needs 65) -> "We.." (key 66) -> "Thanks." -> "Thanks for your time." ->
"Goodbye."; the close (50815) gives key 168, 12 500 experience (MM9 GiveExp 40 000 on the rework's profile) and
3 000 gold. Asserted: 90066, 90168, gold 13 000, experience 12 500.

## 2. Sell Brewmaster Smith's new concoction to Guberland

**Brewmaster Smith** (frosgardcity actor 14, (655, -3441, 45), RUDE 184; close 50560, `frosgardcity.lua:159`). Pose
`(400, -3441, 45) yaw 0`. "Is there anything we can do for you?" (forbids 302) -> "What do you want us to do?" -> "We
will be happy to do that for you." (key 302) -> "Goodbye."; the close gives key 303 and the **Keg of Strange Brew**
(10249, on the cursor). Journal 90640 (302, not 308/309/310).

**Travel.** Frosgard's dock is the Racing Fire (Jozka Atlia, actor 8): Guberland on Thursdays, 6 days; Guberland's
dock (Olaf Ullson, guberland actor 53) has the Flying Bird to Frosgard on Fridays, 6 days. Every route into or out of
Frosgard requires raw key 73 (`transport_routes.txt`); without it the party walks to Thronheim (5 days). The scenarios
use `travel` (as the playthrough does); the keg stays on the cursor through the moves.

**Aklai Dorka** (guberlandcity actor 33, (-1782, -4301, 1), RUDE 141; close 50836, `guberlandcity.lua:157`). Pose
`(-1782, -4050, 1) yaw -pi/2`. "We have some beer we'd like to sell." (needs 302, forbids 304) -> "It's a special brew
from Frosgard." -> "Er,..Yes." -> "Sounds good." (key 304) -> "Goodbye."; the close gives key 306, takes the keg, 500
gold, 5 000 experience. ("That's not enough." ends without a sale and can be retried; "Uh, no.  It was made by his
apprentices." -> "You're sure?" gives 305, and her line then becomes "You're not going to fool me".)

**Back to the Brewmaster**: "We sold the beer." (needs 304) -> "500 gold." (key 307) -> "Goodbye."; the close gives
key 308 and 12 500 experience (MM9 20 000), no gold. The failed path: "We couldn't sell the beer." -> "Sorry" (309):
key 310, 2 000 experience, 200 gold, the keg taken (as MM9's BadReward). Asserted totals: gold 10 500, experience
17 500.

## 3. Take the news to the Temple of Ratatosk

**Dagfari the Peevish** (thronheimcity actor 5, (11141, 2458, 3124), RUDE 242; close 50060, `thronheimcity.lua:228`).
Pose `(10900, 2458, 3124) yaw 0`. "What can we help you with?" (forbids 316) -> "What sort of favor?" -> "So what's the
problem?" -> "Sounds easy." -> "We can handle it.  Give us the message." (key 316; back to his first page) -> "Sorry
to bother you."; the close gives key 317 and the **Scroll of Bad News** (10251, on the cursor). Journal 90660.

**Erlend the Nay-sayer** (actor 15, (-8274, 11510, 3268), RUDE 246; close 50098, `thronheimcity.lua:232`). Pose
`(-8024, 11510, 3268) yaw pi`. "We've come to deliver this message." (needs 316, forbids 318) -> "We don't care if you
want it.  You will take it." (key 318) -> "Goodbye."; the close gives key 319 and takes the scroll (from the cursor).

**Dagfari's reward**: "We delivered the message." (needs 318, gives 320) -> "Goodbye."; the close: key 321, 5 000
experience, 5 000 gold (as MM9). Dagfari's warning that the temple may turn hostile has no mechanic in MM9's scripts
or ours. No Thorolf approach talk fires in a new game (he is hidden without key 83).

## 4. Steal the Golden Honk

**Getting to Fre.** Arslegard City on arrival (`arslegardcity.lua:116-170`): without key 98 the gate_fate cinematic
drops the party at the Dark Passageway; with 100 and without 9515 the gate_writ cinematic plays. The Great Gate
(event 233, `arslegardcity.lua:49`) is locked without 9515. So the scenario sets 98 and 9515 (the state after Hanndl
read the Writ) and starts the new game in the Hall of the Gods (StartPoint0 (-7281, 2952, 1)).

**Fre** (hallofthegods actor 2, (4588, 3523, 677), RUDE 337; click 53126, close 50126, `hallofthegods.lua:66`). Walk to
`(4350, 3400, 677)` radius 150 (planned, 15 s). "Can we ask you some questions?" (forbids 343) -> "We would be glad to
do your task." (key 343) -> "We've heard of them." -> "What does it look like?" -> "Thank you for this opportunity." ->
"Goodbye.". Journal 90690 (343, not 347).

**To the temple.** Out by the hall's west door (walk to `(-7700, 2949, 1)`, "OK") -> Arslegard City; pose by the
bridge `(14418, 2500, -82) yaw pi/2`, walk to `(14418, 3100)`, "OK" -> thjorgard.blv; `travel` to guberland.blv (the
Sea's Fang, Thursdays, 4 days). Temple door: guberland ExitTrigger3 (-19567, -18323, 328), half (164, 82, 164); pose
`(-19567, -18800, 165) yaw pi/2`, walk north, "OK" -> templeofhonk StartPoint0 (-3011, 7670, -521) in the pool hall.

**The temple walked.** One planned `walk_to (5420, 3230, 452)` radius 80, z_tolerance 200 (64 s): up to the gallery,
DoubleDoor13 (event 130, `templeofhonk.lua:50`; movers 9/10 at (-3133..-3011, 5324), z 41; "The door is locked."
without key 343), the west corridors, DoubleDoor9 (112, movers 25/26), the amphitheatre, DoubleDoor5 (109, 19/20),
the south halls, DoubleDoor4 (108, 17/18, beyond a ledge that is only dropped down, not climbed: the way back must be
planned), into the great sanctuary. The walk clicks each shut door itself. The Honks (group 1, 18 actors, friendly
until provoked, `templeofhonk.lua:37`) stay friendly (`mapvar("HonksHostile") == 0`).

**The Golden Honk**: a world item (item 10369, (5691, 3400, 573) on the altar behind the Elder Honk (actor 3,
(5458, 3400, 452)); `pick_up` from (5396, 3159, 410) at 378). Its pickup event 76 (`templeofhonk.lua:120`) gives key
344 on the quest (345 without it) and turns the Honks hostile; it lands in the packs.

**The way out**, leg by leg (doors close by themselves after 7 s, double doors toggle per leaf): to `(3600, 2080)`
via `(4654, 3186)`; per door: `clear_hostiles 1500`, wait until both leaves are `closed`, `click(event)`, wait until
both are `open`; then `(3603, 1591)` -> `(1847, 1990)` via `(3718, 576) (2504, 33) (2080, 1364)` -> door 109 ->
`(1847, 2250)` -> `(-505, 4386)` via `(1830, 2843) (600, 3282)` -> door 112 -> `(-569, 4676)` **plan: false** ->
`(-3011, 5200)` via `(-1714, 4808)` -> door 130 -> `(-3011, 5450)` -> exit `(-3011, 8000, -521)` via `(-2899, 5455)
(-2383, 6517, -397)`, `expect: dialog` (the exit box spans y 7885..8049; a target at 7900 stopped short of it).
About 20 hostile Honks die on the way (`clear_hostiles` in each walk).

**Back to Fre.** No road, boat or altar leads into Arslegard (no transition to `arslegardcity` except from the
Hall, the Bathhouse and the Tomb; no Town Portal altar there). The scenario lets the party be defeated in Guberland
(`party_defeat knock_out`, immortality off for it): it wakes in Arslegard City with the Golden Honk and its gold
(MM9's defeat takes none; until 2026-11-11 ours took it all). Placed by the hall `(19800, -11703, 493) yaw 0`, walks into ExitTriggerHall (20234, -11703), "OK",
walks up to Fre. "We have retrieved the Golden Honk." (needs 344, gives 346) -> "Who is behind Tamur Leng?" -> "Will
we succeed in stopping Tamur Leng?" -> "What does the future hold for Chedian?" -> "What sword?  What two Jarls?" ->
"Thanks for your time."; the close: 10 000 gold, 22 500 experience (MM9 80 000), the quest sound, the Golden Honk
taken, key 347 (as MM9's NPC337.scr). Experience is reset before the hand-in (the Honks' kills give experience).

## Discrepancies

### Guide (tools/mm9_site/story/side_*.yml)

1. **steal-the-golden-honk (side_b.yml:164)**: the steps never say how to get back to Fre; a player leaving
   Arslegard by the bridge cannot return by road or boat. Proposed step between the Golden Honk and Fre:
   "No road or boat leads back to Arslegard. Return by your Lloyd's Beacon, or let the party be defeated: it wakes at
   Arslegard's Great Gate with the Golden Honk but without its gold. Walk through the city to the Hall of the Gods."
2. **steal-the-golden-honk, the accountant's key**: "Take it when the accountant isn't beside it" cannot happen, in
   MM9 either (coordinator, from MM9's scripts): applied text "He stands beside it and sees you take it: the whole
   temple turns hostile (unless he is dead)."
3. **sell-brewmaster-smith-s-new-concoction-to-guberland (side_c.yml:237)**: accurate; optional addition to step 2:
   "Back to Frosgard: the Flying Bird from Guberland's dock on Fridays." The keg (step 1) and the scroll in Dagfari's
   quest come when the talk ends, not on the line; harmless as written.
4. **convince-the-dook-to-leave-guberland** and **take-the-news-to-the-temple-of-ratatosk**: accurate (lines, keys,
   rewards; compass directions follow the guide's map images, which flip regions: north = -y, east = -x outdoors).

### Suspected game bugs (data vs MM9)

1. **The Honk accountant never leaves his desk** (not a bug that matters; coordinator's reading of MM9's scripts).
   MM9's `HONKACCOUNTANT.inc` sends him on a trip at 7:00 and 19:00 (PathMarker0-13: the CollectionChest, the
   puzzle on the lower level, and back), but `HONKACCOUNTANT.scr` `:OnTraverseDone` takes the key off the desk at the
   trip's start (`TakeKey`, `HONKKEY.scr` `getkey` removes it) and puts it back on return (`ReplaceKey`). At the desk
   he stands 58 LT from the key, inside `HONKKEY.scr`'s 200 LT. So in MM9 too the key can be taken only under his
   eyes (or after he dies); our `templeofhonk.lua:56-68` gives the same outcome. The trip itself (cosmetic, and the
   key's absence during it) is not carried.
2. **Stale converter note**: `level_generation/projects/mm9r_dookscastle/README.md:89` says the militia "stand"; they
   now wander (`mm9_ai.wander: aimless` in the scene), which matters for anyone routing the castle.

### Runner gaps and harness notes

1. **walk_to cannot get round a friendly actor that keeps against the party** (Dook's Castle). A wandering guard
   that walks into the party stays there for 17 s and more (MM9's wander turns only 15-90 degrees after an obstacle,
   `GameplayActorAiSystem.cpp` `AI_Mm9Idle`), and the walker's side steps return straight into him; once the party
   stood between a guard and a door leaf it could not move at all. The return walk only passes with a tuned 10 s wait
   before the throne room's door (6 s fails, normal and reload). Proposed fix in `ScenarioRuntimeDriver.cpp` stuck
   handling (~line 2010): when the nearest actor is within ~120 and not hostile, step away from it (perpendicular to
   the route, on the side away from the actor) for longer, or insert a temporary detour waypoint ~150 to that side,
   before trying further.
2. **The walker's own click on a double door from contact** sometimes leaves the party wedged against the swinging
   leaf (Dook's throne room door, Temple of Honk DoubleDoor5): the scenarios click doors explicitly after both leaves
   are shut (playbook §6).
3. **A "partial" detour right after a door opens**: in the temple, a planned 1-waypoint leg through DoubleDoor9 came
   back as a 590-waypoint "partial" route round the whole temple once (leaves mid-swing in the path map?); that leg is
   `plan: false`.
4. **play_lua cannot see actors** (`evt` is nil there), so "wait until the doorway is clear" cannot be written; a
   player sees the guard.
5. **Assert labels for MM9 keys**: `qbit_set[90343]` printed the journal row 90343's text ("Study a Magreeb...").
   MM9's overlay rows are numbered 90000 + note entry and use explicit required/forbidden columns
   (`JournalQuestTable::isVisible`), so the journal is right; only the scenario log's label is misleading.
