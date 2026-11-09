# Prep: block A, Sturmford and Drangheim side quests

Research for five side-quest scenarios (2026-11-08): `find_the_saboteur.yml`, `take_love_letter_to_kira_the_cold.yml`,
`retrieve_ludwig_s_manuscript.yml`, `find_out_who_is_spreading_gossip.yml`, `get_nicolai_a_job.yml`. Sources: the map
Lua and scenes in `assets_dev/worlds/mm9/` (what the game runs), the RUDE rows in `assets_dev/worlds/mm9/dialogue/rude/`
(byte-identical to MM9's `mm9/extracted/RUDE/RUDE/` for all ten NPCs involved; no `promotions.yml`/`lost_items.yml`
overlay touches them), MM9's scripts in `mm9/extracted/SCRIPTS/SCRIPTS/`, the quest notes in
`worlds/mm9/data_tables/english/quests_overlay.txt`, `transport_routes.txt`, `map_transitions.txt`, the beethoven
project (`level_generation/projects/mm9r_beethoven/`) and headless discovery runs.

Conventions as in `tests/playthrough/mm9/prep/`: MM9 key K = qbit 90000+K; MM9 item N = engine item 10000+N; an actor's
click event is 53000 + its DAT object index, its dialogue-exit event 50000 + that index; +y is north, yaw 0 faces east.
RUDE columns: node, choice, line, reply, next (999 = the goodbye node, -1 = end), required keys (c7/9/11/13/15),
granted (c16-20), forbidden (c21-25). Experience: `MM9.giveExperience` gives the full amount to every member.

No quest here needs story state: every giver's opening line is offered in a new game. Each scenario starts with
`new_game_flow` at the giver's map (Knight, Cleric, Thief, Sorcerer at level 28, 10 000 gold) and sets no qbits.

## Getting around

| from | how | to |
| --- | --- | --- |
| sturmfordcity | ExitN (11346, 14541): stand (11141, 14300, 19723) yaw pi/2, walk in, "OK" | sturmford (8090, -3312) |
| sturmfordcity | ExitDock (2089, -1352): stand at StartPoint0 (2089, -1065, 19723) yaw -pi/2, walk south, "OK" | sturmford dock (1003, -13101) |
| sturmford | city gate ExitTrigger0: stand (8090, -3312, 252) yaw pi, walk to (7300, -3312, 400) plan false, "OK" | sturmfordcity "Sturmford" (11141, 14519) |
| sturmford | dock gate ExitTrigger1: stand (1014, -12900, 260) yaw pi/2, walk to (1014, -12589, 543), "OK" | sturmfordcity docks (2089, -1065) |
| drangheimcity | ExitTrigger0: stand (10000, -4178, 1010) yaw pi, walk to (9667, -4178, 1311), "OK" | drangheim (11458, -4164) |
| drangheim | city gate: stand (11458, -4164, 757) yaw 0, walk to (12032, -4164, 963), "OK" | drangheimcity (10240, -4178) |
| thronheim | land gate ExitTrigger2: stand (1392, 6100, 1279) yaw pi/2, walk to (1392, 6498, 1279), "OK" | thronheimcity (14377, 164) |
| thronheimcity | dock gate ExitTrigger0: stand (2089, 14600, 3093) yaw pi/2, walk to (2089, 15073, 3093), "OK" | thronheim (5099, 15222) |

Boats (`transport_routes.txt`; `travel` ignores weekdays and fares): Sturmford's Olaf the Thronish (actor 56, Dragon
Passage) goes only to Drangheim (1 day). Drangheim's Svein Hjarrandssen (actor 32, Black Hammer): Guberland 1,
Sturmford 1. Guberland's Olaf Ullson (actor 53, Flying Bird): Drangheim 1, Sturmford 2, Thronheim 5. Thronheim's
Moenach A'Tryht (actor 45, The Raider): Sturmford 4. **Sturmford has no boat to Thronheim** (and no road): Drangheim,
Guberland, then the Flying Bird, 7 days; one `travel` of 7 days in the scenario.

## 1. Find the Saboteur (Sturmford City)

| who | actor | position | stand | RUDE / events |
| --- | --- | --- | --- | --- |
| Bjarni Herjolfssen | 1 | (-932, 515, 19757), the tavern by the docks (south-west) | (-932, 715) yaw -pi/2 | 46; click 53788, exit 50788 (SpiesLikeUs.scr) |
| Randver the Storm | 39 | (4634, 4475, 19744), town hall ground floor (Fridleif is upstairs, z 20565) | (4634, 4275) yaw pi/2 | 51; click 53841, exit 50841 (Randverrun.scr) |

Talks: Herjolfssen "Perhaps we can buy you a drink?" -> "What's your trouble?" (forbidden 13, 18) -> "We'd be happy to
help." -> "You think someone's been deliberately breaking these things?" -> "You can't do anything about it?" -> "We will
try to sniff out the spies for you." (key 13) -> "Goodbye.". Randver "We'd like to ask you a few questions." -> "What do
you know about Anskram Keep?" (needs 13) -> "'Those' Sturmfordians?  What do you mean?" -> "Why do I think that you're
lying to us?" -> "What do you know about sabotage?" (15) -> "What?  What are you talking about?" -> "What?" (his goodbye
node; reply BLANK). The close: key 495, 800 experience, town-portal effect, actor removed (also on every load with 15).
Without 13 Randver offers only "What do you know about Drangheim?" / "Nevermind.  Goodbye." (checked). Herjolfssen:
"We've discovered who the saboteur is." (needs 15, forbidden 18) -> "A man named Randver the Storm." (18) -> "He
disappeared." -> "Good luck." -> "Goodbye."; the close: key 471, 2 000 experience, 500 gold. Note 90580 (13 until 18).
Rewards match MM9's scripts (800; 2 000 and 500).

## 2. Take Love Letter to Kira the Cold (Sturmford City, Thronheim City)

| who | actor | position | stand | RUDE / events |
| --- | --- | --- | --- | --- |
| Jarl Bjarni Thorvaldssen | 56 | (7311, 8192, 19822), the palace throne | (7000, 8192, 19743) yaw 0 | 45; 53808 / 50808 (Bjarni.scr) |
| Kira the Cold | 41 | (-11182, 16865, 3278), her hall, the city's far (north-west) corner | (-11182, 16500, 3278) yaw pi/2 | 239; 53228 / 50228 (NPC239.scr) |

Bjarni: "Is there anything we can do for you?" (forbidden 22 and 40; key 40 is the council's signatures,
thronheimcity.lua:77) -> "What can we do for you?" -> "Of course.  We would be happy to aid you." (22) -> "Goodbye.";
the close gives item 10247 Love Letter and key 150. Kira: "We've been sent by Bjarni Thorvaldssen" (needs 22, gives 23)
-> "He gave us this letter to give to you." -> "He seems quite taken with you." -> "What should we tell him for you?" ->
"Alright.  So we should tell him the truth." (back to her first page) -> "Sorry to bother you"; the close takes the letter,
key 147, 12 000 experience (MM9 12 000). Key 23 comes with her first line, so any close after it pays (as MM9). Bjarni:
"We have come with a response from Kira the Cold." (needs 23, forbidden 24, 25) -> "She, uhh, she..smiled." (25) ->
"Thanks." -> "Sorry to bother you." (or "Well, she said, umm, er, well, she said..no." (24) -> "She called you a great
warrior..." -> "No!  That was exactly..." -> "Oh.  In that case, good luck."); either answer: key 151, 12 500
experience (MM9 15 200, the XP profile), 2 000 gold. Note 90590 (22 until 24/25).

## 3. Retrieve Ludwig's Manuscript (Sturmford City, beethoven.blv)

Ludwig Van, actor 49, (4306, 2401, 19743), faces south; stand (4306, 2201) yaw pi/2; RUDE 47, click 53789, exit 50789
(LudwigVan.scr). "We'd like you ask you a few questions." (sic) -> "You don't look that busy to us." (forbidden 14) ->
"What happened to your manuscript?" -> "Why can't you go down there?" (forbidden 110) -> "Perhaps we could go down
there for you." -> "Perhaps we could go down there for you!" -> "We'll get your manuscript for you." (14) -> "Goodbye.".
Return: "We've found your manuscript." (needs 16, forbidden 19) -> "WE FOUND YOUR MANUSCRIPT!!" (19) -> "You're welcome."
-> "Goodbye."; the close: key 116, 10 500 experience (MM9 12 000, the profile), 2 000 gold, the manuscript taken.
Found first (key 110): "Does it look like this?" under "Why can't you go down there?". Note 90600 (14 until 19).

The grate: BeetHovengrate (event 242, doors 4 and 5) in his cellar over Ladder3 (top exit (5376, 1689, 19753)); stand
there yaw 0, click, wait 2 s (both "open"), walk east to (5600, 1689, 19005) plan false: the party drops and GrateExit
(5509, 1700, 19005) asks "Beet Hoven" OK/Close; arrival Sewergrate (-1720, 2867, 0). Other entrances: ExitS by the
tavern (1075, 52), ExitW (-5555, 12626) and ExitE (15537, 17080).

The sewers, as walked (`retrieve_ludwig_s_manuscript.yml`; storeys: upper channels 0/82, cavern bed -2949 and surface
about -2141, catacombs -1884/-1966, lower tunnel and lower sewers -3113):

1. `walk_to (-1720, -2202, 102)` planned: south along the channel to the Grand Entrance shaft's lip (17 Lobbers and
   others die on the way).
2. Ladder0 (no `grab_at_top`, so `climb down` is refused): `movement_segment forward 0.35 s` from the lip yaw 270 takes
   the ladder ((-1720, -2290, 201)); `movement_segment backward 18 s` from there climbs down (about 190/s), off the foot
   under water, and the party sinks to the bed at about (-1717, -1842, -2949) (water state `bed`). A movement_segment's
   `start` teleports; at a point in the ladder's volume the party is on the ladder again (no input: it holds).
3. Swim: `walk_to (-1510, -2938, -2949)` plan false along the bed (passes under the shaft's south wall, which hangs below
   the surface), `fly_up` 3 s to the surface (state `surface`), `forward + jump` 0.6 s onto the catacombs' sill
   (-1551, -3189, -1966), dry. (From the ladder's foot the walker, facing the rungs, climbs back up: go via the bed.)
4. `walk_to (-5488, -4600, -1884)` planned, click Door21 (event 109, leaves 17/18, close after 3 s), wait 1 s,
   `walk_to (-5488, -5150)` straight into the tall room.
5. `walk_to (-5567, -6538, -3113)` straight south: the floor's trench (the beam's gap, y -5816..-5740, about 1 230 deep)
   drops the party into the tunnel below (MarkerLower5-8, the bottle's path).
6. `walk_to (-8521, -8249, -3111)` planned (west, then south), `pick_up 10248` from there (167 away, through the grate's
   bars): key 16 (with 14; else 110), world item gone for good (`forbidden_qbits` 90016, 90110).
7. Out: the tunnel joins the lower sewers; `walk_to (-14418, -2611, -3112)` planned (24 s), `climb Ladder1` to the
   catacombs (-14418, -2522, -1884); Door15 (event 104, leaves 7/8): stand (-11730, -5044), click, 1.5 s, walk to
   (-11100, -5044); Door10 (event 101, leaves 1/2): stand (-9110, -4470), click, 1.5 s, walk to (-8500, -4470); planned
   to the sill (-1551, -3189, -1966).
8. North off the sill into the water (-1720, -2684): the party sinks (submerged at about -2279); `walk_to (-1720,
   -2420, -2304)` under the wall into the shaft, `fly_up` 2 s, `climb Ladder0` (8.3 s) to the lip.
9. `walk_to (4450, 17572, 82)` planned through the upper channels (30 s), click SewerDoorE (event 114, door 34, closes
   after 5 s), wait 1.5 s, walk to ExitE (4956, 17572, 328): "Sturmford City" OK/Close; arrival SewerE (15360, 16876).

Without the explicit door clicks the walker gets stuck against Door21 and Door15 (its own "click ahead" from against a
leaf: playbook §6). Planner routes from the sill to the manuscript are "partial" (the trench is not on the monsters'
path map); the legs above avoid relying on them.

## 4. Find Out Who Is Spreading Gossip (Drangheim City, Sturmford City)

| who | actor | position | stand | RUDE / events |
| --- | --- | --- | --- | --- |
| Sigmund the Stressed | 20 | (19005, -5530, 1476), town hall upper floor (east side) | (19005, -5390) yaw -pi/2 | 87; 53334 / 50334 (NPC87.scr) |
| Greudach A'Dorad | 23 | (14418, -819, 776), the north edge of the city (city y -10404..-82) | (14418, -1019) yaw pi/2 | 96; 53337 |
| Marsaili A'Lanth | 2 (Sturmford City) | (3850, 4764, 19723), the street west of the town hall, south of the palace | (3650, 4764) yaw 0 | 52 |

Sigmund: "We'd like to ask you a few questions." -> "Do you have any news?" (forbidden 55) -> "What rumors?" -> "That
is a problem." -> "We will do this." (52) -> "Goodbye.". Greudach: 'We'd like to talk to you about your "news".' (needs
52, forbidden 53) -> "We want to know who you have been hearing it from." -> "Not everyone.  The people we spoke to said
you were the source." -> "We promise." (53) -> "Thank you." (ends). Marsaili: "We'd like to talk to you about your
news." (needs 53, forbidden 54) -> "We understand you've been spreading gossip to Drangheim." -> "We've come to ask you
to stop." -> "Perhaps we will inform the Jarl." -> "Not Bjarni.  Sigmund." -> "Alright.  Should have kept your mouth
shut." (54) -> "Goodbye.". Sigmund: "We've found out who's been spreading the gossip." (needs 54, forbidden 55) -> "A
person named Marsaili A'Lanth in Sturmford." (55) -> "Thank you." -> "Thanks for your time." (goes to his goodbye node,
not the end) -> "Goodbye."; the close: key 300, 5 000 experience, 5 000 gold (MM9 the same). "Greudach A'Dorad talked."
(needs 53, forbidden 54) only sends the party on. After 55 Marsaili has no tongue ("You don't seem to be talkative
anymore."). Notes 90630 (52), 90632 (53), 90634 (54).

## 5. Get Nicolai a Job (Drangheim City, Guberland)

| who | actor | position | stand | RUDE / events |
| --- | --- | --- | --- | --- |
| Nicolai Ironfist | 30 (Drangheim City) | (16712, -82, 348), the north edge | (16712, -282) yaw pi/2 | 414; 53344 |
| Thorir Mouth | 41 (guberland) | (11727, 16984, 121), the Gathering | (11977, 16984) yaw pi | 133; 53021 / 50021 (NPC133.scr) |
| Nicolai at the Gathering | 62 (guberland) | (13857, 19278, 121) | | 414; shown on loads with 121 |

Nicolai: "We'd like to ask you a few questions." -> "What do you know about duty?" (forbidden 118) -> "You don't sound
especially fond of your duty." -> "What happened to duty?" -> "Alright.  We'll find you a job." (118) -> "Thanks for your
time." -> "Goodbye.". Thorir: "You're not looking for any help, are you?" (needs 118, forbidden 119) -> "We may have just
the person." (119) -> "We don't have time for games today." -> "Goodbye.". Nicolai: "We've found you a job." (needs 119,
forbidden 120) -> "At the Gathering in Guberland." (120) -> "Thanks for your time." -> "Goodbye.". Thorir: "Did Nicolai
take the job?" (needs 120, forbidden 122, gives 121) -> ... -> "Goodbye."; the close: key 122, 16 500 experience (MM9
20 000, the profile), 5 000 gold. Drangheim City hides actor 30 and Guberland shows actor 62 on their next loads
(NPC414.scr :Init, as MM9: not at once). Notes 90620 (118), 90622 (119), 90624 (120).

## Discrepancies

### Guide errors (`tools/mm9_site/story/side_a.yml`, `side_b.yml`) and proposed text

**Coordinator's correction (2026-11-09):** the compass items below were judged with +y as north, but the guide's
directions follow its map images (`output/mm9_site/data/presentations.json`): Sturmford City and Drangheim City have
`flipU: true, flipV: false`, i.e. +y is south and +x west on the image. Checked point by point, the guide's original
directions are right and were kept (Herjolfssen north-east, town hall north of the palace, Ludwig north of the town
hall, the sewer exits east and south-west, Sigmund west, Greudach and Nicolai south, Marsaili east of the town hall and
north of the palace). Applied from this list: the palace instead of the longhouse, the Thronheim route tip, the Ludwig
sewer route (Beet Hoven's image has +y north, so its directions stand) and way back, the missing gossip and Nicolai
lines, and "from your next visit".

1. find-the-saboteur, step 1: "drinks in the tavern in the north-east corner of the city" -> "drinks in the tavern by the
   docks in the south-west of the city". Map caption: "Herjolfssen is in the tavern by the docks in the south-west;
   Randver is in the town hall south of the Jarl's palace." (town hall y 4475, palace y 8192).
2. take-love-letter, step 1: "In his longhouse in the middle of Sturmford City" -> "On his throne in the Jarl's palace"
   (the guide calls the same building the palace elsewhere). Add a tip: "Sturmford has no boat to Thronheim: take the
   Dragon Passage to Drangheim, the Black Hammer to Guberland and the Flying Bird to Thronheim (7 days); the Raider
   brings you back to Sturmford in 4."
3. retrieve-ludwig-s-manuscript:
   - step 1: "the house north of the town hall" -> "the house south of the town hall" (Ludwig y 2401, town hall y 4475).
   - step 2: "in the south-west corner of the city" -> "in the north-west of the city" (ExitW (-5555, 12626)); "at the
     east edge beyond the temple" -> "in the north-east corner" (ExitE (15537, 17080)).
   - step 3: "go a few steps south to the round shaft and climb down its long ladder to the catacombs below" -> "follow
     the channel south to the round shaft and climb down its long ladder into the flooded cavern; swim under the shaft's
     south wall and climb out onto the sill of the catacombs."
   - step 4: "lies in the narrow tunnel that runs south from the catacombs toward the maze. Click it to take it." -> "lies
     at the dead end of the tunnel under the catacombs, against a grate. Go west through the catacombs to the double door
     on their south side and drop through the gap in the tall room's floor into the tunnel, then follow it west and south.
     Take it."
   - add a step: "The only way back up is through the lower sewers: west to the ladder up to the catacombs, east through
     the catacombs to the cavern, then up the long ladder. The east exit, behind a door at the end of the upper channels,
     brings you out at the city's north-east corner."
   - map caption: "the manuscript is on the lower level, in the tunnel between the catacombs and the maze" -> "...in the
     tunnel under the catacombs' tall room".
4. find-out-who-is-spreading-gossip:
   - step 1: "In his castle in the west of Drangheim City" -> "In the town hall on the east side of Drangheim City, on
     its upper floor".
   - step 2: "Find Greudach A'Dorad in the south of the city" -> "in the north of the city". Caption: "Sigmund's town hall
     is on the east side of the city; Greudach stands at its north edge."
   - step 3: "Marsaili walks the streets east of Sturmford's town hall, north of Bjarni's longhouse" -> "west of
     Sturmford's town hall, south of the Jarl's palace"; the line list lacks "We understand you've been spreading gossip
     to Drangheim." between "We'd like to talk to you about your news" and "We've come to ask you to stop". Caption:
     "Marsaili is by the town hall, south of the palace."
5. get-nicolai-a-job, step 1: "Ask 'What do you know about duty?'" -> "Say 'We'd like to ask you a few questions.', then
   'What do you know about duty?', ...". Step 4: "Nicolai then works at the Gathering" -> "Nicolai works at the
   Gathering from your next visit." Add: "Nicolai stands at the north edge of Drangheim City."

Everything else (lines, keys, rewards, tips about Randver's questions, either answer to Bjarni, Greudach "talked")
matches the scripts.

### Suspected game bugs

None found that a player would hit: every stage's key, item and reward is granted as MM9's scripts do (rewards scaled by
`mm9_quest_xp_profile.yml` where noted). Minor, MM9-faithful or harmless:

- Randver vanishes where he stands (sturmfordcity.lua `handlers[50841]`); MM9 runs him to `RandverHide` first. Cosmetic.
- MM9's NPC87.scr `:OnRude` ends its whole handler on the first reward's `exit` (the gossip reward would skip Fort
  Stenig/Crona Kiga on the same close); drangheimcity.lua `handlers[50334]` pays all due rewards at once. Harmless.

### Runner observations (for the coordinator)

- `walk_to` gets stuck against MM9 double doors (Door21, Door15) when it "clicks ahead" from against a leaf; explicit
  clicks from about 300 in front, then a straight walk, pass (playbook §6, already known).
- `climb: {down: true}` needs `grab_at_top`; beethoven's Ladder0/Ladder1 have none, though a player takes Ladder0 from
  the lip with forward and climbs down with back (README "Ladders"). The scenario does that with two movement_segments.
- `walk_to` while holding a ladder underwater climbs it again (forward faces the rungs).
- The shared scratchpad of the four agents is one folder (another agent's `actors.py` replaced mine); and
  `output/side_quests/mm9/report.md` is rewritten by every agent's `run.py` call.
