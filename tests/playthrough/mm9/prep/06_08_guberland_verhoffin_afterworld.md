# Prep: segments 06-08 (Guberland's Capstone, the Verhoffin Ruins, the Six Fires)

> **Directions (corrected 2026-11-09):** compass words in this note were taken from raw coordinates as if +y were
> north. On MM9's outdoor maps (regions and cities, `flip_u` in `worlds/mm9/ui/maps/catalog.yml`) the map a player
> sees has +y at the bottom and +x at the left, so those directions are turned 180 degrees; the guide's directions,
> which follow the maps and agree with the original walkthroughs, are right. Indoor maps are not affected.

Research for `06_guberland_capstone.yml`, `07_verhoffin_writ.yml` and `08_six_fires.yml`. Every step below was run
headless (current `build/game/openyamm`, 2026-11-08 18:09) from `checkpoints/04_death_to_arslegard.oysav` with the
missing keys set by console; the scratch scenarios are in
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/prep_b/`
(`a_guberland.yml`, `b_rng.yml`, `c_verh.yml`, `d_door*.yml`, `f_pit.yml`, `e_after.yml`, `g_after.yml`,
`h_after.yml`, `i_hall.yml`, logs beside them). Two engine problems block a clean run of 08 (see "Risks / suspected
bugs" 1); everything else passed.

Conventions: MM9 key K = qbit 90000+K (keys >= 9000 are 9xxxx too: 5021 -> 95021, 7110 -> 97110, 9515 -> 99515); MM9
item N = engine 10000+N. +y is north, yaw 0 faces east (+x), 1.5708 north. Map scripts are
`assets_dev/worlds/mm9/events/maps/<stem>.lua`. An actor's click event is 53000 + its DAT object index
(`mm9_source_object_index` in the scene), its dialogue-exit event 50000 + that index.

---

## Segment 06: Guberland's Gathering, the Capstone of Order (`guberland.blv`)

Start: segment 05 ends by stepping into the Wyrde's portal. `darkpassageway` ExitPoint (441, 6349, -507) moves
straight (AskPlayer 0) to Guberland **StartPoint0, the dock: (22003, 4558, -122), facing 180 (west)**
(`map_transitions.txt` row `darkpassageway/274`). The boats arrive at the same point.

Preconditions to assert: key 98 (Hanndl's refusal; Thorir's prize row requires it), and note **gold is 0**: the
defeat in segment 04 took all of it (91 296 in checkpoint 03, 0 in 04). The ticket master cannot sell
(`guberland.lua:247`, "You don't have enough gold."; the line never reaches `status()` because it is printed by the
dialogue-exit hook). The party still carries **24 Game Tickets (10557) left over from Thjorgard** (counted: 24 bell
games, then `has_item(10557)` false), and those are what it plays with.

The Gathering is south of the dock on the player's map (the guide is right; +y is south here): the fair spans x 9 000-16 000,
y 14 000-21 000, z 121. Outdoors the party may be placed.

### People (scene `assets_dev/worlds/mm9/maps/guberland.scene.yml`)

| actor | name | position | click / exit event | RUDE |
| --- | --- | --- | --- | --- |
| 41 | Thorir Mouth | (11727, 16984, 121) | 53021 / 50021 | 133 |
| 60 | Huckster (the ticket master) | (14072, 18868, 121) | - / 50324 | 429 |
| 61 | Mata Abyomi (arm wrestling) | (15823, 18786, 121) | 53330 | 148 |
| 57 | Peasant (the stones player, the bot) | (11850, 19442, 121) | 53267 / 50267 | 428 |
| 53 | Olaf Ullson (The Flying Bird, to the Isle of Ashes on Tuesdays, 3 days) | (17953, 4409, -122) | 53078 | 144 |

### The six prizes

`gameWon` (`guberland.lua:230-234`): every win gives the game's key, key 7116 and **one random prize**
`MM9.random(362, 367)`, status **"You win! Here is your prize."** (a loss: "You lose."). Detect a prize by item:

| item | prize |
| --- | --- |
| 10362 | Wooden Sword |
| 10363 | Wooden Shield |
| 10364 | Fur Cap |
| 10365 | Cloth Gloves |
| 10366 | Fuzzy Slippers |
| 10367 | Quilted Armor |

The checkpoint party **already holds 10362, 10365, 10366 and 10367** (earlier loot; `has_item` counts packs and
equipped items, as `MM9.hasItem` does, `mm9_common.lua:102-105`): only the Shield and the Fur Cap are missing. The
random generator is deterministic for a given save: from checkpoint 04 the bell's 5th win gave the Shield and the 8th
the Cap, identically in two runs (`b_rng.yml`). From the real 05 checkpoint the order will differ but stay repeatable.
Loop until all six `has_item(10362..10367)` are true, and fail if `has_item(10557)` goes false first.

Win keys (set on the first win of each game, never cleared, so use them only as "won at least once"): stones 7110
(97110), runes 7112 (97112), Whack-a-Honky 7113 (97113), bell 7114 (97114), arm wrestling 7115 (97115), any win 7116
(97116).

### Games (each start takes one ticket: `ticket()`, `guberland.lua:221-229`, status "A game ticket is used.")

- **Ding the Bell** (`guberland.lua:276-297`): `click(102)` (Strikeplate1, at the foot of the bell tower, Bell prop
  (15935, 20097, 900)). Win if `random(40,60) + Might > random(60,80)`; the result shows about 1 s later, the plate
  works again 3 s after that, so `click(102); wait(4.5)`. Measured: 28 of 28 wins with this party. The cheapest
  source of prizes; use it.
- **Arm wrestling** (`guberland.lua:262-268`): `click(53330)` (Mata). Win if `Might + random(9,50) >= random(1,40)`.
  2 of 2 wins. The click also opens Mata's RUDE 148; `click(53330)` twice in a row in one `play_lua` worked, follow
  the `play_lua` with `press_action: {action: cancel_dialog}`. **`interact_actor: {actor_index: 61}` did nothing**
  (no ticket used, no status): use `click(53330)`.
- **Whack-a-Honky** (`guberland.lua:496-561`): `click(104)` (Switch0 lever, geese Honky0-3 at (13904-14150, 20804,
  120)), countdown "Five..." to "One...", then 10 s of geese; eight hits win. The Thjorgard loop works with the
  goose events **736-739**: `click(735 + mapvar("HonkUp"))` while `mapvar("HonkState") == 2`. Won 1 of 1 (34 clicks).
- **Runes** (Mastermind, `guberland.lua:306-389`): colour buttons `click(332..336)` (red, blue, yellow, orange, green;
  status "The red rune." ...), rune stones `click(337..340)` (slots 1-4; the first stone painted in a round takes the
  ticket), lever `click(103)`, `wait(1.2)`. Status after the lever: "No rune is right. 3 chances left." /
  "Right: rune 2, 4. 2 chances left." / "You win! Here is your prize." / "... You lose." after the 4th try. Parse
  `s:match("Right: rune ([%d, ]+)")` (the Thjorgard script parsed "Flames burn by stone"). With 5 colours and 4 tries
  a round wins only ~40 % (measured 2 of 6): skip it unless the tickets run out of better uses.
- **Stones** (`guberland.lua:400-487`): squares `click(700..735)` (square i = 700 + i, row-major from the north-west,
  Piece0 at (11952, 19544), 41 apart). Same rules and map vars (`St0`-`St35`, 1 the party, 2 the bot) as Thjorgard, so
  01's greedy player works unchanged with `click(700 + best)`. Status "White wins!!! | You win! Here is your prize." /
  "Black wins!!!", invalid "Stone must be placed adjacent to another of your stones.". 3 of 3 wins.
- The board, the runes and the geese reset on every map load (`guberland.lua:581-601`).

### Thorir and the trade

1. `set_pose: {map: guberland.blv, x: 11977, y: 16984, z: 121, yaw: 3.1416}`; `interact_actor: {actor_index: 41}`
   (runs 53021); `select_topic: "Do you give out any prizes?"` (key 2087, his offer); the only line then is
   "Well if we ever need a Capstone of Order, we'll be by." -> "Goodbye." (optional; nothing requires this talk:
   the trade row only needs keys 487 and 98).
2. Win prizes until all six are in the packs (play_lua, bell first).
3. `interact_actor: {actor_index: 41}` again: the click checks the six prizes and gives **key 487**
   (`guberland.lua:49-56`); `select_topic: "We've got your set of prizes."` (row requires 487 and 98, gives 488;
   `NPC133.rude:12`); then `press_action: cancel_dialog` (or "Goodbye."). The exit hook (`guberland.lua:59-63`) takes
   one of each prize (key 490) and gives **the Capstone of Order 10396**, key 188 and 18 500 experience.
4. Assert: `qbit_set: [90487, 90488, 90490, 90188]`, `has_item(10396)`.

Verified in `a_guberland.yml` (prizes completed by console there; the games separately).

---

## Segment 07: Isle of Ashes, Verhoffin Ruins (walked), the Writ, the second death

### To the Isle of Ashes

The Flying Bird (Olaf Ullson, actor 53, RUDE 144: "Yes please." is the service row) sails on Tuesdays, 3 days, base
price 20 x 2 (`transport_routes.txt` `144/tuesday`), and **the party has no gold**. Use the outdoors rule:
`travel: {map: isleofashes.blv, days: 3}`.

The Verhoffin stair: ExitTrigger0 (1290, 4198, 1138), half extents 164 (`map_transitions.txt` `isleofashes/485`).
Worked: `set_pose: {map: isleofashes.blv, x: 1260, y: 4636, z: 860, yaw: -1.5708}`,
`walk_to: {x: 1290, y: 4198, z: 1000, timeout_seconds: 30, expect: dialog}` (the prompt opens at (1287, 4391, 952)),
`select_topic: {match_label: "OK"}` (title "Verhoffin Ruins"; the label is **"OK"**, not "Enter"),
`advance_runtime: {seconds: 1.0, follow_map_move: true}`. Arrival: StartPoint0 (-1230, -5969, -327), facing 103.

### Verhoffin Ruins (`verhoffinruins.blv`, walked, `clear_hostiles: 1500` on every walk)

All of this passed in `c_verh.yml`:

1. **To the bolted door**: `walk_to: {x: -4430, y: -4420, z: -328, timeout_seconds: 400, clear_hostiles: 1500}`
   (15 s). On the way the walker stops at PrisonDoor3 (about (-1669, -5321)) and opens it by its own click-ahead
   (event 125, `verhoffinruins.lua:60`), and passes BustTrigger0/1 (x -3575..-2006, y -5684..-5129), which drop the
   pocket monsters (killed). The planner always takes this southern corridor to the pentagram.
2. **The bolt** (PrisonDoor2, `verhoffinruins.lua:82-94`, 390): in one `play_lua`: `click(205)` -> "The door is
   bolted shut."; `click(38648)` (the bolt, a scene destructible: a click is the killing blow; a player hits it with
   weapons) -> `mapvar("BoltBroken") == 1`; `click(205)` opens the door; `wait(2.5)`. Without this the walker's own
   click-ahead breaks the bolt but gives up (twelve tries) before the door has swung.
3. **The pentagram** (`verhoffinruins.lua:169-196`, boxes `:33`, polled 4 times a second `:333-367`): each box fires
   once on entry; the party's feet must be inside an 90 x 90 box, so walk with `radius: 20`:

   | step | box | centre to walk to | latches |
   | --- | --- | --- | --- |
   | centre | PentaCenter | (-4382, -3727, -327) | `PuzzleStarted` 1, five flames (sprites 310-314) |
   | 1 red, SE | TriggerPentagram1 | (-4137, -3891, -327) | `PuzzleProgress` 1 |
   | 2 yellow, N | TriggerPentagram2 | (-4423, -3481, -327) | 2 |
   | 3 blue, S | TriggerPentagram3 | (-4423, -3973, -327) | 3 |
   | 4 green, NE | TriggerPentagram4 | (-4137, -3563, -327) | 4 |
   | 5 orange, W | TriggerPentagram5 | (-4628, -3727, -327) | 5, `PuzzleSolved` 1 |

   Each `walk_to` took 0.4-0.6 s, `PuzzleFailures` stayed 0 (the straight lines between them cross no other point).
   The order comes from the Scrap of Diary letter 485 (`click(225)` shows it, `verhoffinruins.lua:167`; a player who
   reads it knows the colour order; the flames' colours give the points). A wrong point resets (`PuzzleFailures`).
   The fifth opens **only TortureChamberDoor1 (mechanism 65), the south leaf**.
4. **Into the torture chamber through the south leaf**:
   `walk_to: {via: [[-4640, -3830, -328], [-5000, -3830, -328]], x: -6984, y: -3628, z: -204, radius: 60,
   timeout_seconds: 300, clear_hostiles: 1500}`. Through y -3830 it passes with no click (`d_door-3830.yml`). Walked
   without `via`, the route runs at y -3625 into the shut north leaf; the walker then clicks the door (event 204),
   which swings both leaves (north open, south shut) and **turns the fire-bolt shooters on** (`ShootersOn` 1, 20
   fire damage every 4 s to a party in the chamber, `verhoffinruins.lua:198-206, 315-329`). Never click 204.
   On the way west: PaddleTrigger (x -5971..-5661, y -4005..-3450) swings the paddle across its plate toward the pit
   (ran once, did not push the party); the route then skirts the electrified pit along its north edge (y about -3466;
   pit box x -6472..-5980, y -3973..-3482) and climbs to the block's dais, arriving at (-6971, -3590, -191).
5. **The headsman's block** (`verhoffinruins.lua:141-150`): `click(223)` with key 98 and item 10396: key 99,
   18 500 experience, the capstone shows (sprite 303), the writ appears (302), the Capstone is taken. No status line.
6. **The Writ** (`verhoffinruins.lua:151-158`): `click(222)` (the table behind the block, about (-7429, -3648, -204)):
   **item 10392 Writ of Fate**, key 100, 18 500 experience. Assert `qbit_set: [90099, 90100]`, `has_item(10392)`.
   Optional: the black chest (BlackBox, event 46) in the south-west corner.

### The second death: the electrified pit

`spawn_actor` + `party_defeat` (segment 04's way) **failed here**: six Spectre Dagrells beside the block never killed
the party in 300 s (every hit "God evades damage"). The pit works and is what the guide suggests:

```yaml
  - walk_to: {x: -6226, y: -3728, z: -410, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - advance_runtime: {seconds: 3}
  - setup_shortcut: {kind: immortal, value: false}
  - party_defeat: {wait_seconds: 400, expect_map: arslegardcity.blv}
```

The party drops into the pit (feet -737, on the bed, eye under water: water state `bed`), takes 5 electric damage a
second (`verhoffinruins.lua:364`) and drowns ("You are drowning!"); it woke in Arslegard City well inside 400 s. The
Writ stays in the packs (checked on waking). Save the checkpoint right after the defeat (before the gate scene's
3-second poll), or after it: both work.

---

## Segment 08: Hanndl, the Hall of the Gods, the Six Fires

### Arslegard City: Hanndl opens the gate

The party wakes at world.yml `partyDeath` (14400, 2525, -491). About 3 s after the arrival the map's poll
(`arslegardcity.lua:155-170`) starts **gate_writ** (`:130-133, 293-322`, about 28 s): key **9515**, 22 500
experience, Hanndl (actor 35) removed, the Great Gate (RotatingDoor0/1) opened; a click on the gate (233) opens it from
then on. `advance_runtime: {seconds: 40}` then `assert: {qbit_set: [99515]}` (passed).

City: the party may be placed. **The Hall of the Gods entrance**: ExitTriggerHall (20234, -11703, 678), half extents
(10, 82, 164). Worked: `set_pose: {map: arslegardcity.blv, x: 19800, y: -11703, z: 493, yaw: 0}`,
`walk_to: {x: 20300, y: -11703, z: 493, timeout_seconds: 20, expect: dialog}` (opens at (20207, -11703, 515), title
"Hall of the Gods"), `select_topic: "OK"`, `advance_runtime: {seconds: 1.0, follow_map_move: true}`. Arrival
StartPoint0 (-7281, 2952, 1) facing east.

### The Hall of the Gods (`hallofthegods.blv`, walked)

`walk_to: {x: 4715, y: 1802, z: 677, radius: 150, timeout_seconds: 300}`: 17.5 s, no clicks, up the stair into the
throne hall. Skraelos: **actor 1** (4915, 1802, 677), click 53125 / exit 50125, RUDE 336. Krohn actor 0 (5898, 2949,
851), Fre actor 2. The exit back to Arslegard: ExitTriggerHall (-7619, 2949, 174), half (48, 82, 174), west of the
start (the next segment's way out).

`interact_actor: {actor_index: 1}`, then in order (`NPC336.rude`):

1. "We need your help." (requires key 100, forbids 101)
2. "We've come to ask for the return of our warriors."
3. "Our Writ of Fate says it is our destiny to stop Tamur Leng!"
4. "We will do whatever is required."
5. "What are the Six Fires of Penance?"
6. "Yes." (key 101) -> "Goodbye."

Closing runs 50125 (`hallofthegods.lua:46-62`): key 379 and `toAfterworld()`, `evt.MoveToMap(1731, -2225, 1168, 512,
0, 0, 0, 1, "afterworld.blv")` (`:26-29`). **In the current build the party stays in the hall** (keys 101 and 379
set, map var `ToAfterworld` 1, no prompt, no move; see Risks 1). Until that is fixed the only way on is
`travel: {map: afterworld.blv, days: 0}`, which lands on the same arrival (StartPoint0 (1731, -2225, 1168)).

### The Afterworld (`afterworld.blv`, a region: the party may be placed)

Actors (scene): Forad Darre 0 (6483, 2363, 1108, hidden until Retribution), **Skraelos 1** (1854, -2070, 1168; click
53094, exit 50094, RUDE 336), Tryygva 2 (3066, -5506), Kira 3 (-6834, -6942), Markel 4 (10736, -1671), Sven 5
(-2432, 3978), Bjarni 6 (4201, 8046), Sigmund 7 (11625, 2628) (z about 1051). The Jarls are hidden until Guilt is
answered. Skraelos' greeting on arrival (event 56094, OnFoundPlayer) did not open within 3 s headless: start each talk
with `interact_actor: {actor_index: 1}` from the arrival point (`set_pose: {x: 1731, y: -2225, z: 1168, yaw: 0.9}`).
The six fires (sprites 420-425) light with keys 381, 383, 491, 387, 389, 391 (`afterworld.lua:33-40`).

1. **Guilt**: Skraelos: "What do we do now?" (requires 379, gives 380) -> "Our Guilt?!" (closes). The exit
   (`afterworld.lua:114-117`) plays the cinematic `afterworld_guilt` (13.4 s): `advance_runtime: {seconds: 16}`,
   assert 90381. Its last step reopens his dialogue (`:215-217`) but that **did not open** headless: talk again with
   `interact_actor: {actor_index: 1}`. Then "How were we to know that Forad Darre was a traitor?" (requires 381) ->
   "Yes." (key 382; "No, it was not our fault." gives 392 and throws the party back to the hall) -> "We will do this."
   (closes). The exit shows the six Jarls (`:118`). Assert 90382.
2. **Confession** (each: pose beside him, `interact_actor`, the line, `press_action: cancel_dialog`); all passed:

   | Jarl | actor | pose used | line (exact `NPC*.rude` text) | key |
   | --- | --- | --- | --- | --- |
   | Bjarni | 6 | (4201, 7800, 1051) yaw 1.5708 | "Bjarni, forgive us.  We are the ones who killed you." | 502 |
   | Sven | 5 | (-2432, 3728, 1051) yaw 1.5708 | "Sven.  It is our fault you are dead." | 501 |
   | Sigmund | 7 | (11375, 2628, 1173) yaw 0 | "We are sorry, Sigmund.  Our ignorance killed you." | 503 |
   | Markel | 4 | (10486, -1671, 1051) yaw 0 | "Markel?  Why are you here?  You weren't killed in the battle!" then "Yes, that is true.  Their suffering is our responsibility." | 504 |
   | Tryygva | 2 | (3066, -5256, 1051) yaw -1.5708 | "We failed you Tryygva, and we are sorry." | 505 |
   | Kira | 3 | (-6584, -6942, 1055) yaw 3.1416 | "Kira, you are dead, and we are responsible for it." | 506 |

   The RUDE lines carry **two spaces after full stops**: match on a fragment ("Bjarni, forgive us.", "Why are you
   here?", "Yes, that is true."). Then `interact_actor` Skraelos: the click gives **key 383** (22 500 experience,
   `afterworld.lua:85-88`); "We have confessed our guilt." (key 384) -> "Yes, but how...?" (closes).
3. **Suffering**: that exit (`afterworld.lua:119-133`) poisons and diseases the party and should open the Questioner
   (RUDE 432). **It does not open** (Risks 1; map var `Questioned` is 1). Workaround that worked: `play_lua:
   click(50094); wait(0.5); click(50094); wait(0.5)` (the first click clears `Questioned`, the second opens RUDE 432 with
   no dialogue closing over it). The seven answers (`NPC432.rude`), in order:
   "You, my lord." / "To serve you, my lord." / "We encouraged others to trust our misjudgement." / "We owe those we
   betrayed." / "We must pay the price of our failure." / "The ultimate price, my lord." (the RUDE text is "... my
   lord.  Our lives.", two spaces) / "Yes, my lord." (key 385) -> "Thank you.". Note the decoy "You, my lord"
   (no full stop) belongs to a later question, so match the first one exactly. Then `interact_actor` Skraelos and
   `press_action: cancel_dialog`: the exit gives **key 491** (22 500 experience, conditions cured).
4. **Retribution**: Skraelos: "We have known suffering." (key 386) -> "We will do this.". The exit makes Forad visible
   and summons ghost warriors (`afterworld.lua:134-141`; key 5021 = qbit 95021). `set_pose: {x: 6233, y: 2363, z:
   1108, yaw: 0}`, `clear_hostiles: {radius: 3000}`: Forad's death gives **key 387** (`:176-178`). Then Skraelos:
   "We have slain the soldiers." (388) -> "We will do this.": the exit gives key 492, shows the swords and summons
   more undead (`:142-152`).
5. **Absolution**: the swords (Givetake, `afterworld.lua:57-81`; events 330-334, positions from
   `level_generation/projects/mm9r_afterworld_blv/props.json`): Sven's 330 (3369, 5474, 1070) -> 10563; Bjarni's 331
   (4188, 5474, 1014) -> 10564; Sigmund's 332 (4188, 4819, 1050) -> 10565; Tryygva's 333 (3533, 6129, 1050) -> 10566;
   Kira's 334 (4188, 5802, 1015) -> 10567. Worked: `set_pose: {x: 3800, y: 5300, z: 1060, yaw: 1.5708}`,
   `clear_hostiles: {radius: 4000}`, `play_lua: for e = 330, 334 do click(e); wait(0.2) end` (no status line; check
   the five items). Then `interact_actor` Skraelos: the click takes the swords, **key 389** (`:89-96`); "We have
   collected the swords." (390) -> "We will do this.": the exit opens ExitTrigger1 (`Mm9ExitDisabled105` 0).
6. **Rebirth**: ExitTrigger1, the blazing fire north-west of Skraelos, (-2941, 5160, 1554), half 128. Worked:
   `set_pose: {x: -2941, y: 4700, z: 1700, yaw: 1.5708}` (lands at z 1441), `advance_runtime: 2`,
   `walk_to: {x: -2941, y: 5160, z: 1554, timeout_seconds: 40, expect: dialog}` (title "Hall of the Gods"),
   `select_topic: "OK"`, `advance_runtime: {seconds: 1.0, follow_map_move: true}`. The leave hook (`afterworld.lua:
   165-173`, nearer ExitTrigger1 than ExitTrigger0) gives **keys 391 and 102**, 22 500 experience. Assert
   `map: hallofthegods.blv`, `qbit_set: [90391, 90102]`.

### Back in the hall

Walk to Skraelos again (same `walk_to`, 17 s), `interact_actor: {actor_index: 1}`, "We have lit the Six Fires of
Penance." (requires 102, gives 103) -> "Thank you." -> "Farewell.". The exit gives **key 189** (22 500 experience,
`hallofthegods.lua:52-56`). Assert `qbit_set: [90103, 90189]` (passed in `i_hall.yml`).

---

## Risks / suspected bugs

1. **A dialogue or travel prompt opened by a RUDE exit hook is lost** (blocks segment 08 as written).
   `executeMm9RudeExitCallback` runs the 50xxx hook when the talk closes (`game/gameplay/GameplayDialogController.cpp:
   2790-2794`, and `:4864` for cancel); the hook's `evt.OpenMm9Rude` (`game/events/EventRuntime.cpp:7207-7210`) or a
   `evt.MoveToMap` with an image id (`:7343-7352`) only queues `pendingDialogueContext`, and the close that follows
   clears it (`game/gameplay/GameplayDialogUiFlow.cpp:117`). Seen headless: Skraelos never sends the party from the
   hall to the Afterworld (`hallofthegods.lua:28`, the travel question the hall README says a desktop run showed), and
   the Questioner never appears (`afterworld.lua:130`). Both files have uncommitted edits in the working tree, so this
   may be new; the same path is shared with the desktop game, so check it there. The afterworld_guilt cinematic's
   closing greeting (`afterworld.lua:216`) and Skraelos' arrival greeting (56094) also did not open headless (talk to
   him instead; harmless).
2. **No gold after a defeat** (checkpoint 03: 91 296, checkpoint 04: 0; since 2026-11-11 the defeat keeps the gold,
   as MM9's does). Guberland's tickets and the Flying Bird could not be paid; the run depends on the 24 Thjorgard tickets (keep segment 01's purchase at five batches) and on `travel`.
   With only sure-win games, two missing prizes fail to arrive in 24 wins with about 2.5 % chance per random sequence;
   the sequence is fixed per checkpoint, so a failure would be repeatable, not flaky.
3. **`interact_actor` on Mata Abyomi (61) runs no game** while it works on Thorir and the Huckster: use `click(53330)`.
4. **Thorir's prize check counts equipped items** (`HasItemAnywhere`) and the trade removes with `RemoveItem`
   (`guberland.lua:52, 60`; `mm9_common.lua:102-123`): the checkpoint party already owned four prizes, possibly worn.
   Not checked whether the trade removes worn gear or none. MM9's original probably counted carried items only.
5. **Torture chamber door**: only the south leaf opens (`verhoffinruins.lua:192-195`); the path planner ignores which
   leaf is open, and the walker's click-ahead on the north leaf toggles both and arms the shooters (`:198-206`). Walk
   through y -3830.
6. **Bolted door**: the walker's own click-ahead breaks the bolt (38648) but its twelve tries run out before PrisonDoor2
   (205) has swung (`c_verh.yml`, first run). Click explicitly.
7. **Pit and crevasse**: the route to the block skirts the pit's north edge (y about -3466) after the paddle; a
   stray step falls in (5 electric damage a second plus drowning; out by the PIT_STEP ledge). Walking east toward the
   valve room fell into the crevasse water at (-517, -3432, -587) and stuck there ("no route"). Do not go to the valve
   room (nozzles 210-213 flood it, DD5 shuts, button 214 drains).
8. **`spawn_actor` deaths do not work in the Verhoffin Ruins** (300 s, "God evades damage"): die in the pit.
9. **The guide (`tools/mm9_site/story/ch3_5.yml`) against the scripts**: the Questioner's answer has two spaces
   ("my lord.  Our lives."); after a wrong answer one talk to Skraelos questions again (the Questioner's own exit
   resets `Questioned`); Guilt, Confession, Absolution and the hall rows end with "We will do this." / "Yes, but how...?" / "Thank you." / "Farewell." closing
   lines the guide leaves out. No online MM9 walkthrough was consulted.
10. **Status lines from dialogue-exit hooks** (ticket purchase, the trade) never reach `status()`: assert on keys and
    items instead.

---

## Segments as written (2026-11-08, binary of 18:29)

`06_guberland_capstone.yml`, `07_verhoffin_writ.yml`, `08_six_fires.yml`, chained from
`checkpoints/05_dark_passageway.oysav`; each passed three times (`run.py 06`, `07`, `08` twice, then `run.py 06 07 08`),
5, 17 and 10 s, with identical logs (06 always needs five bell strikes from the 05 checkpoint).

- **06**: gold 0 at the dock (logged by `gold get`); the tickets left from Thjorgard are enough, so nothing is bought
  and no gold is added. Thorir's offer, then the bell (`click(102)`) until all six prizes are held (the party already
  had four: five strikes win the Shield and the Fur Cap), then the trade (closed with his "Goodbye." row: the exit
  hook only gives items, so that row is fine). The other four games are not played (the bell is a sure win and the
  tickets are limited).
- **07**: `travel` to the Isle of Ashes with a logged NOTE (no gold for the fare; travel as the other boat trips); the
  stair's prompt "OK"; the ruins walked as in the prep; the second death is the pit plus `party_defeat: {knock_out:
  true}` (the party is a debug "God", as in 04).
- **08**: the real paths, with three logged ISSUE lines:
  1. Skraelos' **"Goodbye." row loses the question to go to the Afterworld**; closing the talk with Escape
     (`press_action: cancel_dialog`) shows it ("The Afterworld": OK / Close). The binary's fix covers the close
     request (`GameplayDialogController::handleDialogueCloseRequest`), not a RUDE row whose next is -1 (the Close
     selection, `GameplayDialogController.cpp:2790-2794`).
  2. The same for the **Questioner**: the "Yes, but how...?" row after "We have confessed our guilt." loses him
     (checked: scratch `08_rowclose.yml`), Escape brings him. Closing the Questioner's own "Thank you." runs Skraelos'
     exit hook, which lights the fire of Suffering at once (key 491); no second talk is needed.
  3. **After the vision of Guilt Skraelos does not speak again** (the cinematic's `greeting` step,
     `afterworld.lua:215-217`); the party clicks him. His arrival greeting (56094) never opens either; the party clicks
     him there too (no ISSUE line for that one: a player would click him anyway).
