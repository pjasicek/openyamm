# MM9 playthrough

How it is built, run, debugged and extended (also for other worlds and quests): the
[Playthrough playbook](../PLAYBOOK.md).

A repeatable headless run of MM9's main story, segment by segment, as evidence that it can be played through. Each
segment is an ordinary scenario (`NN_<name>.yml`) that loads the checkpoint the previous segment saved and saves its
own, so a failure can be rerun from just before it.

    cmake --build build --target openyamm -j25
    python3 tests/playthrough/mm9/run.py            # all segments, stopping at the first failure
    python3 tests/playthrough/mm9/run.py 53         # one segment (its starting checkpoint must exist)

Output, all under the git-ignored `output/playthrough/mm9/`: `checkpoints/NN_<name>.oysav`, `logs/NN_<name>.log`
(the full scenario log) and `report.md` (what the party did: games won, dialogue lines picked, where it walked and
where it got stuck, enemies cleared).

Scope: the main story only. Side and promotion quests have their own scenarios (other sessions' work), so a
checkpoint here carries the story's keys, not every side quest's (segment 50 against the user's after-council save
differs only in side quests).

## Rules of the run

- **The party is immortal** (`setup_shortcut: {kind: immortal}`, this run only; settings.ini is not written) and
  enemies near it die (`walk_to`'s `clear_hostiles`, `clear_hostiles`): combat is not what this tests.
- **Outdoors and in cities the party is placed** beside each person, game or exit (`set_pose`, `travel`), as the
  user allowed (2026-11-08). Exits are still entered by walking into them and confirming their prompt.
- **Dungeons are walked** (`walk_to`): a route planned on the monsters' indoor path map, followed with the Forward
  key; when the party stops it aims further along the route, jumps, steps left and right, clicks what is straight
  ahead (a door, a lever, a rock fall) and plans again; it fails, naming the spot, after twelve tries in one place.
  A place a player cannot pass without a spell (the Tomb of a Thousand Terrors' platforms) fails here.
- **Talk is by the line a player reads** (`select_topic: {match_label: ...}`); a missing line fails and lists the
  lines offered.
- **Puzzles and games are played** by `play_lua` scripts that click the props' events and decide from what a player
  sees: status lines, the board, the raised goose (the Thing's six games in segment 01).
- **Party defeat** (`party_defeat: {knock_out: true}`) knocks the party out (the immortal party cannot lose a fight),
  then runs the game's own defeat (the LoseGame movie skipped): MM9 wakes the party in Arslegard City.
- **The party is the new game's own** (four level-1 characters, Ragnar's Might 20 the best), so chances a character's
  stats decide are played as a player would: the strongest member strikes the Gathering's bell, a trapped chest the
  party cannot disarm is clicked again after its trap goes off, and Thjorgard's ticket batches cover the bell.
- **Running jumps** where a player must jump (the Tomb's water hall) are `movement_segment` hops with the Jump key,
  each logged as a `JUMP` line in the report.

## Starting point

`checkpoints/00_after_council.oysav` is the user's save `MM9_5_AFTER_COUNCIL` (saves/save5.oysav, 2026-11-08):
Thronheim City after the war council, Yrsa's errand taken. Copy it there before the first run. A run from a new
game will replace it as the earlier chapters get segments.

Since 2026-11-08 segment 51 loads `50_after_council.oysav` (segment 50's save, the same story state from a new game;
the user's save also has some side quests done: Bjarni's love letter 147/150/151, Knut's speech 114, Magreeb 202).

## Segments

| Segment | Story | Checks |
| --- | --- | --- |
| 01_ravensford | a new game (Chedian: Knight, Cleric, Thief with a bow, Sorcerer): Grandpa's training talks, the museum's scrolls picked up, the store's, north to the boat | Interface I/II, the scrolls, Grandpa's books, keys 474, 475, 496, 473; the Isle of Ashes |
| 03_isle_yrsa | Forad's first talk, Yrsa's hut, the dragonflies walked to, Yrsa's destiny talk | keys 480, 368, 365, 27, 366, 1, 367 |
| 05_leave_the_isle | Forad joins, the Turret Key, the bunker door and chest, the book's cinematic (the islet sinks) | keys 29, 371, 469, 28; Sturmford |
| 07_sturmford_bjarni | into Sturmford City, the Town Portal altar, Bjarni's two tasks | keys 5012, 20, 11, 12 |
| 09_anskram_keep | the sea wall broken, the SE tower's spiral, the high door; the keep walked: eight Imp gates, the pivot trap crossed while sprung, the airlock | keys 510-517, 39 |
| 11_drangheim_sigmund | the road to Drangheim, the altar, Sigmund's two tasks | keys 5013, 43, 44, 46, the Trap Key |
| 13_drangheim_prison | the Visitor's Pass, the gate guards step aside, the top floor's levers, Ivsar freed, the alarm, out; Ivsar outside | keys 5007, 17, 5006, 242 |
| 15_chasm_of_the_dead | the Chasm walked down its ledges to the Crona Kiga (a world item) and back | key 48, the Crona Kiga |
| 17_sturmford_pledge | the road back, the gatehouse's trapdoor, lever and chains (shot), the ladder; Ivsar in the tavern, Bjarni's reports and pledge | keys 47, 196, 41, 21, 38 |
| 19_drangheim_pledge | the road to Drangheim, Sigmund's reports and pledge | keys 49, 50, 51; two clans pledged |
| 20_guberland_markel | the Black Hammer to Guberland, Markel's two tasks | keys 56, 57, 58 |
| 21_ivan_trivia | the Gathering: Ivan the Smart's seven questions | keys 60, 164, the Victory Certificate |
| 22_thjorgard_sven | the Flying Bird to Thjorgard, Sven's two tasks | keys 2, 3, 30 |
| 23_mine_hard_rock | the Thjorad Mine walked: Ketil, the long east tunnel, the hard rock broken (Ebora's cinematic) | keys 9509, 36 |
| 24_mine_cave_in | Gudrek's lead (paced), the crack, the flooded cavern, the climbing tunnel, the cave wall, round to the loop, BarWall1's six spikes, the refinery's spiral, Njal, the slag extractor's hatch; out | keys 35, 5, 9512, the broken part |
| 25_hjarrand_gunnar | Thjorgard City: Hjarrand paid 1 000 gold, Gunnar's spare part | keys 362, 9513, the Slag Extractor |
| 26_mine_slag_extractor | the mine again: Hjarrand at the machine (his mark never comes: ISSUE), the part installed; out | key 37 |
| 27_monastery_thjorad | the Sea's Fang to Lindisfarne; the monastery walked: three ladders (logged CLIMB movement_segments), the ropes 1, 5, 2, 4, 3, down through the ladder holes, Thjorad | keys 9507, 31, Thjorad |
| 28_tasar_book_of_rules | the Ta'Sar Academy walked (hostile guards die): the four textbooks on their tables (ladders up, holes down), the coded scroll, the bookcase, the Book of Rules (a world item) | keys 9501-9504, 9516, 59 |
| 29_sven_joins | the Raider to Thjorgard; Sven hears both reports and joins | keys 32, 33, 34, 163, 177 |
| 30_markel_joins | the Sea's Fang to Guberland; Markel takes the book and the certificate and joins | keys 61, 62, 63, 165, 167; four clans pledged |
| 35_frosgard_ice | on to Frosgard, the road gate; Tryygva's two tasks, Bodvar's powder barrel on the ice, set off from the pier (break_ice), the dock schedule, Tryygva's ice reward | keys 67, 68, 71, 72, 73, 175, 378, 1021, 1022 |
| 36_yanmirs_fort | Yanmir's Sky Fort walked: the north route (his west door wakes him in the doorway), Yanmir's Key, the long curved corridor, the bookcase, the spiral stair, the six supports, the lure from the hall's north side through the trap hall, out by the west gate | keys 69, 7001; TrapFired, YanmirGone |
| 37_tryygva_pledge | Tryygva hears of Yanmir and pledges Frosgard | keys 70, 74, 172; no 178 yet (his check fixed: 34, not 74) |
| 38_kira_honkies | the Racing Fire to Thronheim; Kira's two tasks; Moenach ships the Honkies to Beldonia; the three Honkies talked to the docks | keys 75, 76, 79, 178, 139, 145, 142-144, 77 |
| 39_mountain_pass | the Mountain Pass walked from Thronheim to Thjorgard on geometry-made via points (the path map cannot route it) | key 80 |
| 40_kira_pledge | back to Thronheim; Kira's rewards, her pledge, the war council called | keys 78, 81, 82, 83, 146, 152, 179 |
| 41_thorolf_bjarni | the Raider to Sturmford; Thorolf's news by the gate; Bjarni owns up and wants a treaty | keys 84, 86 |
| 42_sigmund | north on foot to Drangheim; Sigmund wants a treaty | key 87 |
| 43_kira_treaty | to Thronheim; Kira writes the treaty overnight (a day's rest) | keys 88, 180, 89, 181, the Peace Treaty |
| 44_signatures | Sturmford and Drangheim again: both Jarls will sign in Thronheim | keys 90, 91 |
| 50_after_council | to Thronheim; Kira's hall doors: the council cinematic (Forad leaves, the treaty taken); Yrsa's errand | keys 40, 85, 184, 93, 185, 499; 94 clear; the state of 00_after_council (side quests aside) |
| 51_the_thing | Thjorgard: tickets from the Huckster, then the bell, the half-orc, Whack-a-Honky, Stones, Runestones and the boat race | keys 7100-7106 and 94, the Stuffed Dragon in the pack |
| 52_bikki_and_dain | Bikki outside Thronheim's land gate takes the Dragon; through the gate; Dain at Kira's hall | keys 95, 186; the Dragon gone |
| 53_connecting_tunnels | Thronheim's tunnel exit, the Connecting Tunnels on foot, Yorwick's battlefield scene | arrival in Yorwick, key 97 |
| 54_death_to_arslegard | the party is knocked out and wakes in Arslegard City (Chapter III) | the map after the defeat |
| 55_dark_passageway | Hanndl's refusal; the Dark Passageway walked: bridge statues, canyon, forest, the crouch slot (raised by the converter), tube and island, mirrors, plates, the Wyrde, the portal | keys 98, 476, 187; every puzzle's map state |
| 56_guberland_capstone | the Gathering: Thorir's prizes from the bell, the trade | the Capstone of Order, key 188 |
| 57_verhoffin_writ | the Isle of Ashes; the Verhoffin Ruins walked: bolt, pentagram, the block and the Writ; the second defeat | the Writ of Fate; Arslegard |
| 58_six_fires | Hanndl's gate, the Hall of the Gods walked, Skraelos, the Afterworld's six fires | keys 101, 379-391, 189 |
| 59_frosgard_tamur | Sven in Arslegard, Frosgard City's battle, Tamur Leng joins, Thorolf's summons | Tamur in the party |
| 60_krohn | back to Arslegard, the Hall walked, Krohn's task | Njam's Key |
| 61_tomb | Njam's house and chase; the Tomb of a Thousand Terrors walked (six logged running hops in the water hall), both keys from their chests, the switch, the epilogue | key 109 (the game's completion), the Writ of Fate |

## Scenario steps made for it (tests/scenarios/README.md lists every step)

`walk_to`, `clear_hostiles`, `play_lua`, `party_defeat`, `setup_shortcut: {kind: immortal}`, `save_game: {path}`
and `select_topic: {match_label}` without an `action_id`.
