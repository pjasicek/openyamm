# A player's pins, 2026-11-25 00:54 to 2026-11-26 01:19 (Xeen v3.3/3.4, X2–X7, X9, D1 and seven dungeons)

The same player as [PLAYER_FEEDBACK_20261125.md](PLAYER_FEEDBACK_20261125.md) sent a fourth archive
(`pins_inbox_yamm_3.7z`, 111 pins, of which 65 were the third archive's again and **46 are new**): X2 3, X3 3, X4 1,
X5 1, X6 3, X7 7, X9 10, D1 7, XD-06 1, XD-11 2, XD-12 4, XD-13 1, XD-18 2, XD-19 1.

**Versions.** The third round's fixes (commit 81bd30afa2, 2026-11-25 16:52) went out in 3.4, tagged 2026-11-25 19:55.
Pins up to X5 p14 (19:03) were made on 3.3 or older: X2 p13/p14, XD-06, X3, X7, XD-18 may already be fixed by 3.4
(level pads, D-170 footings, F65 clicks). Pins from 20:29 on (X2 p15, XD-11, XD-12, X9, X6, X4, XD-13, XD-19, D1) may
be on either version; the pin files do not record it. **Every agent first captures each pin's pose on the current
build** and says which pins the current maps already fix.

- Pins are filed in the map projects: `devdocs/xeen/briefs/<map>/L4/review/pins.yml`. New ids: X2 p13–p15, X3 p10–p12,
  X4 p13, X5 p14, X6 p14–p16, X7 p1–p7, X9 p1–p10, D1 p1–p7, XD-06 p1, XD-11 p1–p2, XD-12 p1–p4, XD-13 p2, XD-18
  p1–p2, XD-19 p1. Use `oymap pins list|claim|tour|resolve` (openyamm-studio/README.md, "Pins from the game"), binary
  `openyamm-studio/build-xeen/oymap`.
- Pictures: `output/xeen_fb/p5_20261126/original/<stamp>-<map>.png` (with the pin YAMLs), contact sheets
  `output/xeen_fb/p5_20261126/small/sheet_NN.jpg`, and `<project>/.oymap/pins/pictures/`.
- Housekeeping: X2 p1–p10 and X3 p1–p9 (the 2026-11-23 round) still read `open` in their L4 `pins.yml`. The outdoor
  agent checks each against the current map and resolves the fixed ones with an after picture.

**The rule (the user's, 2026-11-21):** every family is fixed at its source (generator, shared kit, engine, common Lua,
data), then on **every** site of its kind in the Xeen world, with a check that keeps it fixed. The pinned spot is only
the example. See [briefs/FEEDBACK_FIX_RULES.md](../briefs/FEEDBACK_FIX_RULES.md) (its paths to `USER_FEEDBACK_20261121.md`
mean this file for this round).

## The new pins, grouped into families

Poses are `position [x, y, z]`, `yaw` radians, `pitch` degrees, from the pin files. "TB" means the picture shows the
turn-based bar.

| F | Family | Pin(s), map, pose, what the picture shows | Agent |
| --- | --- | --- | --- |
| F70 | **X9's bridges and cloud slabs clip the cloud floor** (F62 on X8 again, on X9) | X9 p2 "bridge clipping through" [-158.5, 7604.8, 672.5] yaw 1.510 pitch -16.8 and p3 "clipping through" [-770.6, 9679.4, 704.0] yaw 0.846 pitch -12.1: a flat stone slab path on the cloud floor, the cloud surface cutting through its edges, before the temple with statues. p4 "maybe clipping" [-12346.9, -16624.9, 512.0] yaw 0.213, p5 [-13978.0, -14716.2, 512.0] yaw 1.681, p6 [-16740.9, -4439.5, 448.0] yaw 5.150, p7 [-16918.3, -966.8, 448.0] yaw 1.544, p8 [-14209.7, 10234.0, 576.0] yaw 5.722, p9 [13495.6, -14511.0, 512.0] yaw 1.357, p10 [15105.5, -3275.5, 512.0] yaw 4.720, all "clipping": a plank bridge rises from an island toward the party, but its last section lies loose on the cloud floor, cut off from the rest by the cloud, which also rises through the deck (p7: a cloud bump through the planks). The side rails stop in the air | dungeon (X9 is a BLV) |
| F71 | **Black or untextured faces on props, roofs and mouths** | X7 p4 "textures missing" [5815.8, -13875.8, 2015.5] yaw 0.275 and p5 "texture missing" [6337.0, -12533.2, 2027.7] yaw 5.041 pitch 26.8: Sablewing's cave mouth, a rock shell with black triangles in its side and a black top face. X3 p10 "texture missing" [-15288.2, -9596.3, 1121.0] yaw 4.674: the Tomb of a Thousand Terrors' doorway is a flat black rectangle (the same spot as X3 p8 of 2026-11-23: still black on 3.3 after F50's cave-mouth shells). X3 p12 "texture missing" [12679.7, 8812.5, 999.8] yaw 1.287 pitch 35.8: The Camp Shrine's roof seen from below (a dark band along the ridge?). X2 p15 "many roofs have missing textures, or i would say there is something missing" [90.8, 13385.8, 1025.0] yaw 5.337 pitch 29.4: Rivercity's half-timbered houses from the street; the gables show only a thin plank edge, no roof thickness or eaves. D1 p3 (with F73) "also the roof has texture problem" [8191.6, 10239.5, 833.0] yaw 4.046: Miller Dunn's mill, a plain white roof. D1 p7 "z-fighting and missing texture" [-7714.1, 4652.8, 1767.4] yaw 3.111 pitch -35.3: Lucio's Jetty, a black void under a deck end between two plank levels. XD-13 p2 "is here something missing?" [-397.7, -1828.6, -640.0] yaw 1.959: a "Speaking grille" with sky behind its bars inside the dungeon | outdoor (kits), dungeon (XD-13) |
| F72 | **Flicker on the ground: fences, water edges, decals, props in the paving** | X3 p11 "z-fighting" [9733.3, 14654.6, 1761.0] yaw 5.458 pitch -42.0: a hexagonal plank enclosure, its floor ring flush with the ground. D1 p1 "z-fighting" [-17370.5, -20085.6, 833.0] yaw 5.203: The Vale Falls, metal hull tiles meeting the water. D1 p6 "z-fighting" [-1645.8, 4062.5, 1161.0] yaw 4.103 pitch -34.4: Castleview square, a dark "#" grid shape on the paving (a grate decal or a shadow). X2 p13 "befor the patch, it did not clip, but now it clipped" [2177.8, 8119.1, 1060.0] yaw 2.831: a barrel and a tub where the paving meets the bark ground by a market stall: a regression of a 3.3 change (pads, kerbs or street paving) | outdoor |
| F73 | **Things on slopes, again: tents, the mill, standing stones, a tree in a rock** | X7 p3 "the tent needs an even ground" [18371.8, -15697.8, 2006.4] yaw 1.423: an A-frame tent off a slope. D1 p2 "tent is in air" [11474.9, 20280.9, 1537.0] yaw 1.517: the party under an A-frame tent whose floor edge hangs over a bank. D1 p3 "the mill is in the air" [8191.6, 10239.5, 833.0] yaw 4.046: Miller Dunn's mill on a stone plinth over a falling bank. X7 p6 "the stones are standing strange" [-22056.7, 18110.3, 1761.0] yaw 6.166: a ring of boulders at night, tilted and sunk at odd heights. X7 p7 "stone and tree are clipping together" [-18859.6, 17066.7, 2593.0] yaw 1.783: a dead tree growing out of a big boulder. X9 p1 "maybe move it more right" [-30.1, 410.5, 416.5] yaw 2.655: a striped pavilion over a cloud island's edge. Check F59's level pads (`common/level_pads.py`) and D-177/D-179 reached X7 and D1 at all | outdoor; dungeon (X9 p1) |
| F74 | **Buildings and props: overlaps, doors, half-built pieces** | X6 p15 "it is clipping" [11429.7, -16200.5, 1505.0] yaw 1.422: a timber porch running into an A-frame tent at The Warzone. X6 p16 "the doors are clipping" [12307.1, -15850.8, 1505.0] yaw 6.267: two arched doors side by side on one facade, frames overlapping. X2 p14 "Make the door bigger. Inside it is bigger." [-1026.0, -17754.6, 1016.8] yaw 4.717: the Temple of Yak's door is a small house door on a huge wall. XD-06 p1 "maybe put a comple fountain there" [1741.4, 4279.0, 0.0] yaw 4.704: a "Statue": a white urn with falling water on a low brick plinth, no basin. D1 p4 "put the letters on, like the other chests with numbers" [451.4, -89.9, 1147.7] yaw 0.682: "A chest with a letter on its lid", a row of plain crates with no letter shown. X7 p2 "make it clickable" [-16827.2, -11706.7, 2017.0] yaw 1.759 (TB): the orc outpost's campfire (F65 again) | outdoor; dungeon (XD-06); decider (X2 p14 door size, XD-06 fountain) |
| F75 | **Big monsters stuck in doors and passages** | XD-18 p1 "dragon gets stuck" [2390.8, -3224.7, 0.0] yaw 0.146 (TB): an Acid Dragon inside a wooden door frame into a narrow passage. XD-18 p2 "they get stuck" [9447.3, 1347.9, -1024.0] yaw 2.929 (TB): a red dragon at a narrow opening. X6 p14 "monst gets stuck" [-14637.2, -13589.1, 1663.5] yaw 3.796 (TB): beside a teal metal wall with lit windows (the machine wall or the hull) in the desert. The rule: a monster's body width against every doorway and passage on its route; the dragons' lairs sized for dragons, or dragons placed where they fit | engine (AI), dungeon (XD-18), outdoor (X6) |
| F76 | **Dungeon roofs and ramps: walls through ramps, stair sides, trees in walls** | XD-11 p1 "here is something wrong" [-1739.8, 1480.2, 1920.0] yaw 0.276 pitch 12.3: a long ramp up to a gallows-like frame; the ramp's side shows saw-tooth steps against the wall. XD-11 p2 "maybe here too" [-378.5, 1861.2, 2496.0] yaw 6.095: an open walk with crenellations and a lower rubble wall, a wall end standing alone. XD-12 p1 "tree clipping through the wall" [-2524.0, 1335.3, 768.0] yaw 4.364 and p2 "tree clipping through" [2688.0, 2996.9, 768.0] yaw 6.066: trees poking through corridor walls. XD-12 p3 "here is something wrong" [2201.6, -1080.2, 2304.0] yaw 0.633: a ramp that runs diagonally into a wall. XD-12 p4 "here is also something strange" [2397.9, 2077.9, 3072.0] yaw 4.102: a roof with crenellations and a separate stone block standing on it | dungeon |
| F77 | **Content: loot, weather, portal, a quest line, goblins** | XD-19 p1 "Fire Elemental have no loot" [91.1, -548.0, 0.0] yaw 1.524 (TB; as X2 p7 "Sprites are giving no loot. Even the bosses." of 2026-11-23). X4 p13 "you cannot port to Winterkill" [-1539.4, 4325.7, 1313.0] yaw 3.224: Town Portal lists Asp, Newcastle, Nightshadow, Rivercity, Vertigo, not Winterkill. X5 p14 "wouldn't it be better to have snow here?" [-15990.2, 18407.4, 1503.5] yaw 0.434: rain falling on the snowfields. D1 p5 "is this a quest bug?" [3119.0, 1981.7, 1153.0] yaw 0.425: Dreyfus, High Priest of Mok, says "You went up their rope? Good. The key to my door is on the top floor, by their altar. Bring it down and let me in." while the player talks to him in the temple (he is already inside his door?). X7 p1 "the map needs more goblin, and more than 2 in a group" [-10774.5, -20797.4, 1899.8] yaw 1.702 | engine/data; decider (elemental loot, X7 density and group size, X5 weather) |

Agents: **dungeon** (F70 X9, F73 X9 p1, F71 XD-13, F74 XD-06, F75 XD-18, F76), **outdoor** (F71 outdoors, F72, F73,
F74 outdoors, F75 X6, the housekeeping above), **engine and data** (F75's AI side, F77, F74 X7 p2's click). **Decider**
first: X2 p14 (the Temple of Yak's door size), XD-06 p1 (a fountain basin), elemental loot (XD-19 p1 and X2 p7), X7's
goblin density and group size, X5's snow instead of rain.

## Results

### Round summary (orchestrator, 2026-11-26 ~12:00)

Of this round's 46 pins, 45 are resolved; X6 p14 waits for the engine. Of the 2026-11-23 X2/X3 pins, all but X2 p3, p5, p8
and X3 p3 are resolved (those four have replies: data owned elsewhere, or the old pose now inside the ground). X4 p13 is
answered (by design, D-188's hint). Decisions D-180 to D-190, and the user's U-16 (the Xeen Slayer Sword is a Club).
Binaries: game and oymap 2026-11-26 10:09:52 (R1–R5 part 1, U-16's view-model set). Rebuilt, installed and baked this
round: X1–X7, X9, X8, D1–D7, XD-02, XD-06, XD-07, XD-11, XD-12, XD-13, XD-14, XD-18, XD-19, XD-21, XD-26, XD-27, FD-02,
FD-04, DD-03, DD-04, DD-05, DD-09, DD-12, DD-13, DD-24, DD-25. End checks: stale bakes 0, `build_world --check` 0,
`town_fit_check` 0 (the `xeen_*` `decorations.through` kept line deleted), `regressions.sh`'s map gates all pass,
including the new `check_beam_ends`, `check_cutout_backing --all`, `check_fountains`, `check_clipping --all` and
`check_monster_fit` (D-185).

Open after the round:
- X6 p14 (A1): worms pursuing from X6's Sphinx cove stop at its east corner (cell 33, 84); repro
  `output/xeen_fb/p5_engine2/r5/x6_cove_worms_pursue.yml`; also let walkers step over a topless fin lower than a step.
- XD-05 (A7): 3 campfires in L4, not installed. Its stage fails `check_drops` (pocket at -2398, 5374, -480), and its
  playtests land on X1 below `z_min` 1300. Both faults are on the installed map too. Then `common/campfires.py --check`
  joins `regressions.sh`.
- FD-04 `check_ledge_shots` 1 error at the machine's lip (already in HEAD; A7).
- `empty_zones --check` fails on X1 and X6 (X1 as on HEAD).
- Pre-existing `textures.feature_repeated` audit errors: X1 6, X2 17, X4 6, X5 3, X6 4.
- For the next decider batch: Darkside's 192-wide tower doors tile MM7 door pictures (a narrow second leaf shows);
  X7's `xd05_gate` picture 416 deep (does D-189's 128 apply to old doors?); D-186's pair is placed N and SE of the egg
  bowl, not in the nest's full south-west quarter; X7's Dragon Tower plinth 215 over its slope (kept).
- `build-xeen/tests/openyamm_unit_tests` does not link while another session's `tests/ImplantTests.cpp` is
  unfinished (engine2 ran the unit tests on a private link: 3223/3223).
- Map Studio changes alter non-Xeen maps at their next build: mm7_7out03 (R1, R3, R4); R3 also mm6_outd3, mm6_oute3,
  mm7_7out02, mm8_out02, mm8_out06 and Hesper's starport_reach, cinder, kreegfall, vharakesh.
- New English text (Q-D6's Dreyfus lines, the Winterkill mirror) needs `tools/l10n.py` extract/update at release.

### F74 X7 p2, F75 AI, F77 (agent xeen-fb5-engine, 2026-11-26; for A1, A2, A3, tools)

Scratch, logs and captures: `output/xeen_fb/p5_engine/` (`f74/`, `f75/`, `f77/`). **No C++ changed, no build**: every
finding was data, a generator or by design; `build-xeen/game/openyamm` (2026-11-25 15:39) ran all checks. Pins: X7 p2,
D1 p5, X5 p14, XD-19 p1 resolved with pictures; X4 p13 replied (by design), left claimed.

**F74 X7 p2 (the orc outpost's fire, "make it clickable", on 3.3): fixed by 3.4, test added.**
- Cause on 3.3: the burn (then a Yes/No) hid only the three hide tents; the fire stayed burning and named, and its click
  repeated only the hook's after-line. The pin's picture shows exactly that (no tents round a lit fire). 3.4 (D-144,
  D-152, X7 rebuilt) burns with one click and hides the fire, hides and bones, showing charred logs and stumps
  ("The burnt outpost"), also after a reload (`evt:outpost_state`).
- Checked on the current build at the pin pose: a Use in turn-based mode burns it (`f74/shots/x7p2_tb_after_use.png`),
  burnt state after `reload map` (`f74/shots/01-x7p2_after_burnt_reload.png`). Note: a left mouse click does nothing in
  the world by default (Attack is F, Use E); only a player who bound the left button to Attack/Use with the smart click
  uses things by clicking.
- New regression `tests/scenarios/xeen/x7_orc_outpost_burn.yml` (turn-based Use at the pin, the burn line, reload, the
  charred logs' after-line): passes.
- Every campfire in Xeen (`f74/fire_survey_outdoor.txt`, scripts `f74/fire_survey*.py`): outdoors 36 fires on 13 maps,
  all with an event (`check_wild.py` `wild.campfire` guards them: 0 errors). Indoors 46 fire decorations on 15 BLVs have
  **no event** (D-104: "dungeon campfires not yet done"); the open campfires among them a player expects to use:
  XD-05 `cookfire`, `den_fire`, `hollows_fire`; XD-27 `chief_fire`, `den_fire`, `quarry_fire`, `yard_fire`,
  `pit_cookfire`, `pit_fire`; XD-21 `boss_fire`; XD-07, XD-14 `hearth_fire`; DD-04 `barracks_fire`; DD-09 `cookfire`;
  DD-13 `fire_e`/`fire_w`; DD-24 `hearth_fire`, `trench_fire_1/2`; DD-25 `hearth_fire`; DD-05 `kitchen_fire`. The rest
  are braziers, forges and XD-04's stoking pots (fixtures, no click wanted). REQUEST to the dungeon lanes below.

**F75, the engine side (big monsters stuck in doors): no engine fault; a check added.**
- The route planner already plans with the body (`game/pathfinding` `PathObject` radius and height; indoor
  `IndoorWorldRuntime` builds it from the actor's collision radius and height, outdoor the same) and with
  `allowPartialPath` routes a body that cannot reach the party to the nearest point it can reach. Probes at XD-18 p1 and
  p2 (`f75/xd18_p*_probe.yml`, logs beside them): the Acid Dragons (radius 238, height 487: a body 476 wide) come to their
  cave's mouth and stop there, creeping a few units a second against it; none enters. XD-18 p1's mouth is BLV portal 1900,
  224 wide x 288 high, between the dragons' cave (room 1) and the party's passage (room 19).
- Every opening of XD-18 is 224-448 wide and 256-320 high: no dragon there fits through any door. This is the lair's
  size, the dungeon agent's fix (lairs sized for dragons, or dragons placed where they fit). MM6-MM9: unchanged.
- New check `tools/xeen/check_body_fit.py` (warnings `body.penned`): a placed monster whose room has no opening as wide as
  its body and as high: 65 on 9 maps (`f75/body_fit.txt`): XD-18 26, FD-04 26, DD-02 4, DD-03 3, XD-19 2, XD-26, XD-12,
  XD-07 (the Fire Dragon's pit, D-32: by design), DD-21 1 each. For the dungeon agent; X6 p14 is outdoor (no portals).

**F77 X4 p13 (Town Portal / mirrors without Winterkill): by design, replied.**
- The list in the picture is Castle Burlock's **mirror** ("Where to?", with Asp, which is a mirror only). Winterkill's
  mirror (X5 event 69, house 4256, qbit 119004, also its Town Portal row) opens only once Q-C6 Ghosts of Winterkill is
  done (`source/towns/x5.yml` `opens: q-c6.done`); before, it answers "A pale face looks back from the mirror. It is
  not yours." and records nothing. On 3.3 the quest's second and third ghost waves stood still (F63, fixed in 3.4), so
  this player likely never finished it. All twelve Town Portal towns have their mirror and row (`town_portal.yml`).
- Test `tests/scenarios/xeen/x5_winterkill_mirror_opens.yml` (shut before Q-C6, sets 119004 after): passes.

**F77 D1 p5 (Dreyfus: "Bring it down and let me in"): a quest-text fault, fixed at the source (for A3).**
- Dreyfus waits in the Temple of Mok; "my door" is his Western Tower's (DD-05) ground door. Q-D6's Quest topic had one
  line for everything between climbing the rope and opening the door, so a party back from the top with the Cult
  Leader dead and the key in its pack still heard "The key ... is on the top floor ... Bring it down".
- `source/quests/q-d6.yml`: three states, key ever found (`found: west_tower_key`), Cult Leader slain, rope climbed;
  each names the tower's ground door. `build_world.py --only gen_quests` (only q-d6's rows and text ids moved);
  `quests.py`, `quest_stub.py` pass. Tests `tests/scenarios/xeen/d1_dreyfus_tower_steps.yml` (new) and the side quest
  `q-d6_heretics_of_mok.yml` pass. Capture `f77/shots/d1p5_c_after_leader_slain.png`.

**F77 X5 p14 (rain on the snowfields): D-184, done (for A2).**
- `tools/xeen/gen_maps.py`: bolster_maps.txt's Rain cell is `-` for `rain: false` (the engine reads "rain unless `-`";
  the generator never wrote it, so every Xeen weather map could rain); the build refuses `snow: true` without
  `rain: false`. `source/map_rows.yml`: X5 `{snow: true, rain: false}`, X6 and D5 `{rain: false}`. New world file
  `assets_dev/worlds/xeen/rendering/weather/weather.yml` (`xeen_x5.odm: {snow: 30}`). `--only gen_maps`: three rows of
  bolster_maps.txt changed, nothing else.
- Test `tests/scenarios/xeen/weather_no_rain_snow_deserts.yml` (13 months of forecasts each on X5, X6, D5: no rain; snow
  on X5 in winter): passes; on the old table it fails at the first month (`f77/weather_old.log`). Capture
  `f77/shots/01-x5p14_after_snow.png`. MM6-MM9: unchanged (Xeen rows and a Xeen world file only).

**F77 XD-19 p1 (elementals leave no loot): D-182, done (for A2).**
- `source/monsters.yml`: robots (11610-11612), elementals (11620-11624) and air elementals (11700-11702) `corpse: none`
  -> `corpse: dying` (their descriptors' dead sprite is now the dying one: a body, then the satchel with the table loot).
  `tools/xeen/gen_monsters.py` refuses `corpse: none` on a row with table loot. `--only gen_monsters`: 11 descriptor
  rows changed, nothing else.
- Tests `tests/scenarios/xeen/elementals_leave_loot.yml` (Standard) and `elementals_leave_loot_maw.yml` (MAW): a Fire
  Elemental and a Patrol on D6 and an Air Elemental on P2 each leave gold; both pass; Standard fails on the old
  descriptors (`f77/loot_old.log`). Capture `f77/shots/xd19p1_c_after_satchel.png` (XD-19 at the pin after the room's
  monsters die: satchels where they stood). X2 p7 is the outdoor agent's.

**Checks at the end:** `build_world.py --check` 0 differ; no map rebuilt, no bake touched. Not run: the full regression
set (no engine change).

### F70, F71 XD-13, F73 X9, F75, F76, D-181 (agent xeen-fb5-dungeon with sub-agents -f75 and -f76, 2026-11-26; for A6, A7, A8, tools)

Scratch `output/xeen_fb/p5_dungeon/` (`tour.sh`, `cyc.sh`, `post.sh`, `runmap.sh`; private game slots `locks/`).
Before captures of every pin on today's build: `before/<map>/` (side by side with the player's picture:
`before/sm/cmp_*.jpg`); after: `after/<map>/`. Every rebuilt map: audit 0 errors, every playtest passing from its
stage, installed, baked where profiled, MAW reserve rerun. End: `stale_bakes --check` 0, `xeen_balance --check` clean,
`build_world --check` 0 differ, `key_npcs --write` (76), `check_actor_heights` clean, `balance.py` exit 0.

**F70, X9 p2–p10 (done; resolved).** The player's X9 was the one before the third round's F62 port (3.3): today's
captures show no cloud through the decks at p2, p3, p5–p10. What today's map still showed, fixed at the generators:
- *A seam on the cloud (p4, "maybe clipping").* The cloud necks' level landings lay 8 over their cloud, their 8-high
  sides and ends a straight line across the cloud. `x9/gen.py`: they lie `NECK_SUNK` 12 under the cloud's top; the neck
  shows from the rim (a 12 step). All 6 necks of X9 (the only cloud-on-cloud links; X8, D7 and the planes have none).
- *Rails ending in the air (p5–p10).* Every rope bridge's two rails stopped at the deck's ends 88 over the cloud.
  `rail_posts()` in `x9/gen.py`, `x8/gen.py`, `d7/gen.py`: a 16 × 16 post on the island at each rail end, its top 16
  over the rail. Sites: X9 8 bridges (32 posts), X8 8 (32), D7 3 (12). Check **`tools/xeen/check_beam_ends.py`** (L4
  beams: an end held by no post, block, beam, wall or floor): open-air maps 76 → 0 errors; dungeons 11 warnings left
  for A7 to look at (XD-01 1, XD-02 4, XD-03 3 trestle caps, XD-26 3 = the torn rail and the hoist beam, meant).
- X9's 4 sky-flagged cloud sides that `check_clipping.py` listed are the unseen way's sky sides (D-50 change 1): kept
  in `check_clipping.yml`.
- Captures `after/x9/01-p1.png` … `10-p10.png`, `after/x8_statue/02-garden_bridge_posts.png`,
  `after/d7/01-stranded_bridge_posts.png`.

**F73, X9 p1 (done; resolved).** The Might and Endurance booths' back walls and awnings hung 120–140 over the carnival
cloud's rim, and three booths stood partly off the plaza (8 over the cloud). `x9/gen.py` `booth_shifts()`: each booth,
its game piece (striker, track, treadmill) and its point move toward the plaza's middle until every piece is 48 inside
the plaza (Might 704, Speed 496, Endurance 800; Accuracy fits). No overlaps between booths or with the tonic crate.

**F71, XD-13 p2 (done; resolved) and the same fault elsewhere.** The speaking grille was a wall panel in `xngrille`, a
cutout made for XD-02's hoist gate: on a solid wall its clear texels showed the void, which on a map with open sky is
drawn as the sky. `xd13/gen.py`: the grille is a thin block 4 off the wall over a black hole panel (`7solid01`),
`evt:grille` on `platform:grille`. Check **`tools/xeen/check_cutout_backing.py`** (every face in a cutout texture,
looked through from the side the party can stand on: error when the void behind it is the sky, warning when it is
black). Sites: XD-13 1 and **DD-12's eight aviary cages** (`xwcage` panels with the Darkside sky behind:
`cutout/dd12_cmp.jpg`) fixed the same way (`dd12/gen.py`, birds' events on `platform:cageN`); 9 → 0 errors. Warnings
left (black behind bars, reads as a dark hole; look at them): DD-06 2 (the pens' bars, a cell door), DD-26 3 (grates),
XD-08 4. Captures `after/xd13/02-p2.png`, `after/dd12/cmp.jpg`.

**D-181, XD-06 p1 (done; resolved).** XD-06's two chapel statues, X8's 2 and X9's 6 offering statues are `7dec55`
(dry statues) instead of `sta1a`, MM6's basin-less fountain; FD-04's real fountain stands in an octagonal basin (kerb
384, water 16 under it, `fd04/gen.py`; installed with the F75 leashes). Check **`tools/xeen/check_fountains.py`**
(a basin-less fountain more than 32 from water): 11 → 0. Captures `after/xd06/01-p1.png`, `after/x9_statue/cmp.jpg`,
`after/x8_statue/01-offering_1.png`, `after/fd04/01-basin.png`.

**F75, XD-18 p1/p2 (sub-agent -f75; done; resolved).** Indoors a monster's radius against the level is capped at 60
(D-32) but its height is not: a dragon (487 high) chasing the party to a 288-high party passage stops about 60 from
it with its body in the frame. Fix as D-154: a leash per big monster in its generator, the largest that keeps it 64
clear of every opening it cannot pass (max 1,536), posts moved where the leash would be too short. XD-18 (41 dragons
and the King; 163 → 0; new `playtest_fit.yml`), FD-04 (26; 68 → 0; the hatchery's second pair at leash 32), FD-02 (6
Dragon Mummies), XD-19 (Xeen's Pet), XD-26 (`open:high_hidden` 224 → 256 high for the gargoyles); all installed and
baked, playtests pass. Check **`tools/xeen/check_monster_fit.py`** (`fit.stuck` error, `fit.squeeze` warning,
`--suggest`). Left: XD-02's Clan Guard vs the 160-high bunk niches (its generator is outside `regen.py`; A7: niches 192
high), XD-09's golems vs the tumbler slots (A8: leash or raise them); XD-01's counter window kept. XD-12's penned
monster in `check_body_fit.py` is Crodo in his cell (by design). Captures `f75/before/`, `f75/after/`.

**F76, XD-11 p1/p2, XD-12 p1–p4 (sub-agent -f76; done; resolved).** Causes: the flights in open-air rooms had no
`riser`, so their risers and sides took the room's wall surface, the sky (XD-11 p1's notches, XD-12 p3's bare slab):
risers in rubble / keep stone (`xd11/geo.py`, `xd12/geo.py` `stair_hall(solid=)`). XD-11 p2: a 448-high doorway in a
wall that was only a parapet: the wall built up to 3,136 round it. XD-12 p1/p2: great trees whose crowns reached up to
1,050 through the keep's wall: small trees with crown clearance (`xd12/dress.py`, `tools/xeen/deco_footprint.py`).
XD-12 p4: the sky stair's two zero-thickness low walls beside the roof: openings, with two 64 × 62 posts over the 16
stubs the studio needs. Check **`tools/xeen/check_clipping.py`** (`sky.solid`, `deco.through`, `piece.free`; kept and
pending in `check_clipping.yml`): XD-11 82 and XD-12 117 → 0; pending with their lanes: XD-17 `tree_4` (A5), DD-09,
XD-27, DD-11C, DD-23, XD-02, XD-03, XD-05 decorations into walls (9). Captures `f76/after/xd11b/`, `f76/after/xd12b/`.

**Not done:** the engine agent's dungeon campfires (about 20 open fires without the D-104 event) and DD-12's/DD-06's
black-backed bars (warnings).

### F71–F75 outdoors, D-180, D-182, D-183, housekeeping (agent xeen-fb5-outdoor with sub-agents a (X2, X3) and b (X6), 2026-11-26 ~07:30–09:20; for A5, A6, A1, A2, tools)

Scratch `output/xeen_fb/p5_outdoor/fb5/` (`tools/run.sh` per map: regen + build until identical, gate, install with
bake, checks, playtests, extras, `level_pads --check`, second regen; `tools/post.sh` the checks after an install the
lane script stopped on another agent's stale dungeon bake; `tour.sh`, `cmp.py`). Before shots of every pin on the
installed maps of 2026-11-25: `before/<map>/`, sheets `view/c<map>_*.jpg`; after shots `after/<map>/`,
`sub_a/after_x2|after_x3|after_xd06/`, `sub_b/after/`. Installed with bakes: X2, X3 (a), X6 (b, run by the parent),
X7, D1. Every playtest and extra scenario passes on each; second regen identical on each; `stale_bakes` 0,
`build_world --check` 0 differ.

**State on 3.4 before work.** Already fixed: X3 p11 (Newcastle's gate tower course, F58/D-170), D1 p6 (the DD-01
hatch now a raised frame), D1 p7 (Lucio's pier from the deck's edge), X7 p3 (the wagon's level pad), X2 p1, p2, p4,
p6, p9, p10 and X3 p1, p2, p4, p5, p6, p7, p9 of the 2026-11-23 round (resolved with after pictures). Not fixed: the
rest below.

**F71, cave shells black (X7 p4/p5).** Cause: the studio's cave-mouth shell (`OutdoorWaysIn.cpp`) chooses each
triangle's facing alone from a guess that leans up; triangles a shake tilted down face into the rock, and the bake
lights them from behind (Sablewing: 7 faces, the black quad and triangle and the dark top band). Check:
`check_faces.py` `faces.flipped` (a shell face wound against its neighbours; cave mouths and hatches only).
Sites: 50 faces on 12 shells (X1 orc_cave_mouth, X2 ogre_lair, X3 tomb, X4 xd26_eyrie, X5 xd10_north/south, X7
sablewing_cave, xd16_mouth, xd17_cleft, xd18_mouth, orc_den, D4 dd23_lair), kept in `check_faces.yml` until REQUEST R1
lands; then each map's rebuild. Pins replied.
**F71, the tomb's black doorway (X3 p10, p8):** `x3/gen.py` door `xvtdoor` (the tower kit's door), resolved. 12 other
built doorways keep a flat black face (DECIDE 1).
**F71, roofs (X2 p15, X3 p12, D1 p3's roof):** the classic kit's `verge` overhang has a barge board but no soffit, so
from below the roof face's own underside shows (shingles; the Camp Shrine's grey planks). Every classic-kit house
(17 sketches use `verge`). REQUEST R2; then D1's mill takes `eaves: 24, verge: 40`. Pins replied.

**F72.** X2 p13: F49 (3.3) moved a keg pair into the quay wall slab's footprint; the studio stands props on the land,
so it stood 73 under the paving: `x2/gen.py PAIR[15]`, new `check_props_support.py support.sunk` (X2 fixed, X4's
brazier at (20480, 9472) left for X4). D1 p1: the hull pieces beside The Vale Falls stood under the falls' spillway
plate: `common/rim.py` cleared a 768 plate while the studio takes the river's width (1,280); `_river_width()` now
reads it as the studio does (X1, D2, D3 hull runs change at their next rebuild), and a hull piece in a river's or
lake's plane stands 24 over it (X7 2, D6 4). X3 p11: already fixed.

**F73, why the level pads missed these, and the rules.** (1) `level_pads.auto` and `decorations.slope` skipped every
`xeen_` model as a set piece, so the world's basalt boulders never sank (X7 p6): rocks by the world table's
description (`basalt`, `boulder`) now sink like rocks, read on the game's terrain triangles (the bilinear land left
them 28–51 over their rim); X7 rebuilt, D5's boulders at its next rebuild. (2) `things.overhang` skipped any sample over
water and looked only under the footprint: the Sardaj tent stood on the land at the gorge's lip (D1 p2): new
`things.edge` (a set piece within 256 of a drop over 160), no water skip under set pieces; the tent moved, the only
site. (3) No rule for a building on a plinth over a bank (D1 p3): new `houses.plinth` (floor over 192 above the lowest
dry land under it): the mill 1.1 cells wide off the lip; X7's Dragon Tower (215) and D6's Alamar NE tower (576) kept in
`town_fit_kept.yml` for a look. (4) The studio's scatter keeps off bmodels, not placed decorations (X7 p7, a dead tree
in a boulder): REQUEST R3, new `decorations.through` (12 sites on X3, X6, X7: kept for every map until R3).
X7 p3: fixed by 3.4's pads.

**F74.** X6 p15 (b): Gorm's coach was laid 1,152 east-west into the pen: `[1152, 640]`, new `town_fit_check.py`
`pieces.overlap` (the only site). X6 p16 (b): the arena gate's two leaves each showed a whole single door:
`common/classic_kit.py` gives listed two-leaf doors the wing picture (arena gate, Castle Basenji), new
`door_check.py` `doors.twin_singles`, `doors.crowded`. D1 p4: the lettered chests' titles name the letter. X2 p14 (a,
D-180): the Temple of Yak has a 384 double door of `xvtdoorw`, still 256 high (REQUEST R4). D-180 checks in
`door_check.py` (b): `doors.small_for_building`, `doors.inside_mismatch`; sites (`sub_b/d180_sites.txt`): X2
yak_temple, darzog_tower; X3 high_magic; X5 darkstone, pagoda; X6 arena_gate (wing pair, height waits on R4);
D1 ellinger_tower, western_tower, kalindra_4; D2 southern_tower; D3 eastern_tower; D4 blackfang_gatehouse; D5
northern_tower; D6 alamar_gatehouse: not done (generators untouched except X2/X6; most need R4 for the height).

**F75 X6 p14 (b):** map side clean (markers 2.4–3.4 cells from the hull, no trap pocket); a pursuing monster steers
into the hull in turn-based mode: REQUEST R5. Replied.

**D-183 (X7 p1):** `source/map_rows.yml` orcs `[3, 4]` (gen_maps: only map_stats' X7 row changed), 8 markers by
`x7/places.py SOUTH_QUOTA` (west 2, red river 2, east range 1, gap 1, hills 1, pony ridge 1); balance Act I 1.15.
`empty_zones.py xeen_x7`: the south-east zone (77, 101) is 717 tiles (358 on HEAD): `SOUTH_MOVES` put the red river's
second marker at (81.5, 106), which D-142 moved back (5,621 from the south start < 5,888): NEXT, (82.5, 107.0).
`empty_zones --check` also lists X1, X6, D5, D6 (X1, D5, D6 fail on HEAD's scenes too). **D-182:** X2 p7 resolved
(F54, `sprites_leave_loot.yml` passes).

**Housekeeping replies (left open, with reason):** X2 p3 (Lindon: F52's line), p5 (pose inside the slope), p8
(F54/F77), X3 p3 (pose inside the rise), X3 p12, X2 p15 (R2), D1 p3 roof (R2), X7 p4/p5 (R1), X7 p7 (R3), X6 p14 (R5).

**REQUESTS to xeen-fb5-engine** (full text `output/xeen_fb/p5_outdoor/fb5/requests.md`): R1 cave shell winding
(`OutdoorWaysIn.cpp`, one winding for the grid, one sign per shell); R2 a soffit under a roof's verge
(`OutdoorBuildings.cpp raiseRoof`, gable block ~7083–7175); R3 scatter keeps off placed decorations
(`OutdoorPlaces.cpp Placer::free`); R4 `door_height` for a door in a wall bay (`OutdoorBuildings.cpp`, `notchDoor`
~4090); R5 outdoor pursuit against model faces (`OutdoorWorldRuntime.cpp applyOutdoorActorMovementIntegration`).

### D-185, D-186, D-188, dungeon campfires (agent xeen-fb5-dungeon2, 2026-11-26; for A7, A8, A4)

Scratch `output/xeen_fb/p5_dungeon2/` (`runmap.sh`, `cyc.sh`, `post.sh` from p5_dungeon with the fit check added to the
stage; `campfire_map.sh`). Every rebuilt map: audit 0 errors, `check_monster_fit` 0 on the stage, every playtest
passing from the stage, installed, baked, MAW reserve rerun. End: `stale_bakes --check` 0, `build_world --check` 0
differ, `xeen_balance --check` clean, `key_npcs --write` (76), `check_actor_heights` clean, `balance.py` exit 0,
`towns.py` 0 errors. No C++ built.

**D-185 (done).** `tools/xeen/check_monster_fit.py`: hidden (staged) actors count (`check_arrivals.hostiles(...,
hidden=True)`); the way round (a low opening is not `fit.stuck` when a doorless opening between the same two sectors,
within leash + radius + 64, passes the body; door leaves from the export's `doors`); the decider's fit rule in the
docstring; `--self-test` (doctest on XD-09's two tumbler slots: uncounted, and counted again with the doorways taken
away; 2 of 2). Counts: 65 -> 8 (XD-09 0; XD-02 3; DD-03 5, as the decider predicted) -> **0 stuck on 69 maps**
(60 squeeze warnings, 3 kept). `tools/xeen/check_body_fit.py` deleted (untracked; no test or script named it).
- XD-02 (L4 is the source): the three bunk niches' openings 160 -> 192 high (the niches' full height).
- DD-03 `gen.py` `LEASH` from `--suggest`: Iron Vithnipravad 256, Argonax 448, Scraps 768. `playtest_dragon.yml` waits
  beyond each of the three openings at stage 3: no dragon within radius + 64 (184) of it.

**D-186 (done, fallback applied).** Captures of the hatchery from both doors and from above at rest
(`fd04/rest/`, crops `fd04/rest_01_crop.jpg`, `rest_04_crop.jpg`) and after a 20 s fight from the nest door (`fd04/fight/`):
the second pair's bodies ran through the first's (a frost dragon's wing through the red's head; a frost head through
a red wing). Group 25 moved to the nest: Fire Dragon (-506, 256), leash 480; Frost Dragon (100, -450), leash 512
(`--suggest`), 687+ from every other dragon, off the egg bowl's bank. The decider's "free south-west quarter" holds
three of the nest's six dragons already. Counts kept. `gen_tests.py` reads actor indices from
`output/studio_cal/fd04/root` (2026-11-21), so its FD-04 scene and BLV were refreshed from the stage first. 9/9
playtests. After: `fd04/after/` (sheet `fd04/after_sheet.jpg`).

**D-188 (done).** House 4256's `closed_text` is the decider's line; `--only gen_towns` (mirrors.yml) and
`--only gen_quests` (the mirror table in xeen_quests.lua), each only that line. `x5_winterkill_mirror_opens.yml`
asserts "Mayor Randon, by the gongs": passes. X4 p13 replied.

**Dungeon campfires, D-104 (10 of 11 maps).**
- Source: `level_generation/projects/xeen/common/campfires.py` adds the outdoor campfire's event (wild.py
  `CAMPFIRE_LUA`, `once: true`) to the listed open fires' L4 wiring; `regen.py` runs it after each listed map's
  generator.
- Sites: 21 fires on 11 maps (the engine agent's list); the other 25 fire decorations are listed as fixtures with
  reasons (braziers, forges, XD-14's study grate, XD-04's stoking pots and vat).
- Installed: XD-07, XD-14, XD-21, XD-27 (6), DD-04, DD-05, DD-09, DD-13 (2), DD-24 (3), DD-25: 18 fires.
- **XD-05 (3 fires) not installed.** Its L4 has the events, but the stage fails two things that predate this change:
  `check_drops` finds a pocket at (-2398, 5374) z -480 (on the installed map too), and `playtest.yml` and
  `playtest_mouth.yml` land on X1 at z 1281 against `z_min` 1300.
- Checks: `campfires.py --check` (`campfire.unlisted`, `campfire.no_event`, `campfire.not_installed`) reports only
  XD-05's `not_installed`. New `tests/scenarios/xeen/dungeon_campfire_once.yml` (DD-09's cookfire gives food once,
  also after a reload): passes.

**Found, not mine:** `check_ledge_shots` 1 error on FD-04 (the machine's lip at z -1888, the Autobots of group 54),
present on HEAD's FD-04.

### R1–R5 (agent xeen-fb5-engine2, 2026-11-26; for A1, A5, A6)

Scratch `output/xeen_fb/p5_engine2/`: `oymap/` (studio build), `game/` (game build, unit tests), `maps/` (every outdoor
Xeen map built from a copy of its L4 with the old and the new oymap, `cmp.py`, `soffits.py`, the checks' outputs),
`r5/` (X6 probes and logs). **Released 10:09:52**: game `build-xeen/game/openyamm` and oymap
`openyamm-studio/build-xeen/oymap` (`output/xeen_fb/p5_engine2/release.sh`). oymap_tests 553/553; unit tests 3223/3223
(a private link without `ImplantTests.cpp`, another session's unfinished file that does not link today; the shared
`build-xeen/tests/openyamm_unit_tests` is missing until it does); `regressions.sh` 54 pass (its runtime-test line failed
only on the private unit binary's folder; `openyamm_runtime_tests` of 2026-11-25 passes those cases); `x1_hull_edge`,
`x4_hull_edge`, `x7_edges` pass. No Xeen map rebuilt or installed.

**R1, cave shells wound one way (F71, X7 p4/p5).** `core/OutdoorWaysIn.cpp`: the shell's triangles keep the grid's own
order on either diagonal and one sign turns the whole shell (the sum of their area normals against the old up-and-out
guess). Doctest "F71: a rough cave mouth's shell is one surface wound one way" (96 builds: buried and free, roughness
0.5 and 1, 12 seeds; no edge run twice the same way). Scratch builds: `check_faces.py faces.flipped` X7 27 → 0, X2 3 → 0.
Other worlds: only `mm7_7out03` has a cave mouth (changes at its next build).

**R2, soffits under verges (F71, X2 p15, X3 p12, D1 p3).** `core/OutdoorBuildings.cpp raiseRoof`: under each slope's
run past a gable end with a verge, a face `barge` under it in `trim`, facing down, from the gable wall's plane to the
verge and from the eaves corner to the apex. Doctest: the verge test (`roofs: flat can be stood on ...`) now counts 4
boards and 4 soffits (2 and 2 with `verge_walls: [e]`). Scratch builds: X2 +178 downward trim faces on 43 models, X6
+2 (Castle Basenji). Other worlds: none (`verge` is Xeen's only). D1's mill can now take `eaves: 24, verge: 40` (A5).

**R3, scatter keeps clear of placed decorations (F73, X7 p7).** `core/OutdoorPlaces.cpp`: the Placer keeps each
scattered decoration (its table radius r) at least (R + r) × 0.6 from every decoration the sketch places, R its model's
drawn reach (`decorationDrawnReach`, `core/OutdoorDecorationCollision.cpp`: the binding's GLB at its height, as
`deco_footprint.py`), else its table radius; pieces reaching over 384 (hull, Sphinx, great crowns) are not discs and are
left out, as `town_fit_check` does. Doctest "F73: scatter keeps clear ...". Scratch builds: `decorations.through` X7 3 →
0; X6's 2 are the check's own (its placed sandfalls reach 1,080, so the check takes them for scattered: REQUEST);
decorations moved: X2 47, X3 98, X7 27. Other worlds: every studio map with placed decorations and scatter
(`mm6_outd3`, `mm6_oute3`, `mm7_7out02`, `mm7_7out03`, `mm8_out02`, `mm8_out06`, Hesper `starport_reach`, `cinder`,
`kreegfall`, `vharakesh`) may move scatter at its next build; none rebuilt.

**R4, `door_height` for a bay door (D-180).** `core/OutdoorBuildings.cpp`: a ground-storey door of a part with
`door_height` in walls at least that high stands that high from its foot, its picture once over it, up into the rows
above through the S8d door holes (a lower door gets a lintel of wall in its row); door frames and recesses take the
same height. Doctest "D-180: a door of the part's door_height ...". Scratch `door_check.py`: X6 arena gate 384 × 256 →
384 × 384 (2 errors → 0), X2 Temple of Yak 384 × 384 (2 → 0; `darzog_tower`'s 116-wide door stays, a generator matter).
Other worlds: `mm7_7out03` sets `door_height` (changes only if a door of it stands in taller walls).

**R5, outdoor pursuit at X6's cove (F75, X6 p14): partly fixed, pin left open.** Repro (`r5/x6_worm_probe3.yml`,
`r5/x6_cove_worms_pursue.yml`): worms north of the Sphinx cove chasing the party south-east of it. Melee pursuers do
plan; the planner took the void's terrain inside the cove for ground and routed them straight across: one stood on
the hull's lip for good, one fell into the void. Fix (`game/outdoor/OutdoorPathfindingBuilder.cpp`): void cells carry
no path floor, and each edge between a void cell and the land is a wall the planner keeps a body's radius from;
`applyOutdoorWaterRestriction` keeps walkers off void cells as off water (a deck over them still carries). Doctest
"outdoor pathfinding builder leaves the void past the world's edge out for every body". **Still stuck:** a worm can
hold at the seam of `hull_092`/`hull_093` (cell 32, 84): `hull_093`'s west end cap rises 16–32 over the land along
y -10166…-9930 with no top behind it, an invisible fin the walker cannot step over (the planner sees the 32 riser as
a step onto `hull_093`'s top strip). REQUEST below; the repro scenario stays in scratch until it passes. MM6–MM9:
unchanged (only Xeen scenes have `terrain.void`; no MM6–MM8 pursuit rerun needed); worms south of the cove still reach
the party (`r5/probe2_new.log`).

**U-16 (optional, done).** `game/render/FirstPersonViewModelKit.cpp`: a two-handed Club takes the two-handed set and
the warhammer template, as a two-handed Mace; doctest "clubs: ...". Every world's Weapon2 clubs (MM6–MM8 have none).

**REQUESTS.** A5/S (X6 hull): the hull pieces' end caps stand over the land where neighbours' tops differ (`hull_093`
1520 vs `hull_092` 1488 at x -16384; the land there 1504–1509): sink the caps to the land or level the run's tops.
A1 (next builder): a walker's step over a tread-less fin lower than its step height (OutdoorMovementController), then
move `r5/x6_cove_worms_pursue.yml` into `tests/scenarios/xeen/`. Tools: `town_fit_check.py check_through` takes
`sketch_at` from the 64–384 pieces only, so a placed decoration reaching further (X6's sandfalls) counts as scattered.

### R1–R4 rebuilds X1–X7, D-189, D-190, X6 hull (agent xeen-fb5-outdoor2, 2026-11-26; for A5, A6, S)

Scratch `output/xeen_fb/p5_outdoor2/` (`tools/run3.sh <key>`: regen + build until two builds match, then
`stage_install2.sh`: gen_walk, the D-170 gate, a hard-link stage of assets_dev with the map installed, the audit (an
error fails only when the installed map lacks it), door/wall/wild/reach/props/D-85/empty-zone checks and every
playtest plus the map's extra scenarios from the stage, then the bake from the stage under bake.lock and the install;
`tour.py`, `tour.sh`, `door_poses.py` for the captures; each map's `run.out`). All seven maps installed with their
bakes on the 10:09:52 oymap; every playtest and extra scenario passed from the stage on each; second regen identical.
No C++ built.

**R1–R4 on X1–X7.** `faces.flipped` 0 on every shell (X1 orc_cave_mouth, X2 ogre_lair, X3 tomb, X4 xd26_eyrie, X5
xd10_north/south, X7 sablewing_cave, xd16/17/18, orc_den); their lines deleted from `tools/xeen/check_faces.yml` (D4's
dd23_lair line is outdoor3's). `decorations.through` 0 on X3, X6, X7. Soffits under every verge. Pins resolved with
after pictures (`after/<map>/`): X7 p4, p5 (shells), p7 (no tree in the boulder), X2 p15 (soffits from the street), X3
p12 (the Camp Shrine's roof from below). X2 p14 replied (the Yak door now 384 × 384).

**D-189 (`door_check.py doors.black_built`, an error; a doorway picture deeper than 128 is a `doors.deep_leaf`
warning in `--list`).** Exceptions by kind (cave mouth, hatch, culvert, a pit or wedge form) and by id word (adit,
culvert, stair, cleft, shaft, hole, pit); a deliberate dark built door goes into `DARK_KEPT` (the sketch schema refuses
a `dark` field). Sites, mine: X1 warehouse door (`xvdoor`, 384 → 128 deep), witch tower door (`xvtdoor`, 384 → 128); X2
den door (`xvsdoor`, 448 → 128); X5 Golem slab (`xvtdoor`, 384 → 128; its frame moved 0.75 cell north to the rocks'
slope foot, since with a picture the land before it stood 210 over its sill and hid the lower door; arrival moved with
it). Darzog's Tower and Darkstone already showed the tower kit's `xvtdoor` (the classic kit replaces a building's own
door role). Kept dark (listed by the check): X1 culvert grate and outfall, mine portal, orc cave, shaft head; X2 ogre
lair; X3 coffin, XD-13 stair; X4 XD-02 adit, XD-25 stair, eyrie; X5 warren, XD-10 mouths; X7 XD-16/17/18; D1 dd10a
adit; D2 dd10b adit, the troll holes; D3 shaft; D4 sewer shaft. Left for outdoor3/A6: D1 outfall, D2 both Graalg
gates (errors in `door_check.py` until rebuilt). One warning: X7 `xd05_gate` (a picture 416 deep, before D-189).

**D-190.** `door_check.py`'s docstring states the 512 (bay + jambs) and the slim-front rule; `building_rules` gives
`doors.small_for_building` for a slim front (under 512) on a type-word building with walls ≥ 640 that leads nowhere:
one leaf 192–384 wide (the front less 128), ≥ 320 high (384 on walls ≥ 896). No site today.

**D-180 sites (mine), all 0 errors.** X2 Temple of Yak 384 × 384 pair (R4); Darzog's Tower 128 × 256 (rule a, XD-12's
128 × 256; it was 116); X3 Tower of High Magic a wing pair 256 × 320 (XD-11 192 × 384; was 132 × 256); X5 Darkstone a
wing pair 256 × 384 (FD-03 224 × 448; was 112 × 256); the Ninja Pagoda 160 × 256 (XD-22 160 × 320); X6 arena gate and
Castle Basenji 384 × 384 pairs (R4). Found on the way: a single leaf wider than its 128 picture is laid tiled (audit
`doors.tiled`), so every widened door is a pair of the kit's wing.

**X7 (D-183).** (82.5, 107.0) was refused by D-142 too (the XD-05 gate's arrival, 3,860 < 5,888) and the marker went
back to (99, 106). A search over every D-142-passing cell (`d142.Rule.why_not`) and the zone measure found [82, 112]:
`SOUTH_MOVES` (82.5, 112.5), the zone's largest piece 103 tiles, `empty_zones --check` passes on X7; `balance.py` Act I
1.15.

**X6 hull (R5's map half).** `common/rim.py hull_sink`: a kerbless piece (`xeen_hullf`) sinks to the lowest land under
its 0.64-cell strip (at most 128), so no end cap stands over the land (`hull_093` 1520 → 1504, `hull_092` 1488 → 1472;
X7's lava-fall faces too). Kerbed pieces never sink: a first version sank them as well and the party stepped over a
sunk kerb (step 128, kerb about 150) into the void (`x4_hull_edge` failed on the stage); X1, X2, X3, X6, X7 were
reinstalled without it. **outdoor3's D1–D5 were installed with that first version** (regenerated 10:31–10:57; note in
`output/xeen_fb/p5_outdoor3/FROM_OUTDOOR2.txt`). At 11:27 D4 and D6 were reinstalled clean, D1–D3 regenerated clean
but still installed from 10:34–10:53, D5's L4 still had 52 sunk kerbed pieces: each needs its rebuild (REQUEST). `x6_cove_worms_pursue.yml`
still fails: the first worm now passes the 092/093 seam and holds at the cove's east corner (cell 33, 84), 3,605 from
the party, not targeting it; it stays in `output/xeen_fb/p5_engine2/r5/`; X6 p14 replied, left open for A1.

**Tools.** `town_fit_check.py check_through`: every decoration the sketch places counts as placed (X6's sandfalls no
longer counted as scattered). `x2/gen_walk.py`, `x5/gen_walk.py` `dark_face` find a doorway's door picture too.
X4: the Shrine of Fire's brazier on its altar (`raise: 128`; `support.sunk` 0). The `xeen_*` `decorations.through`
line of `town_fit_kept.yml` stays until outdoor3's D maps are rebuilt (NEXT).

**Found, not mine:** audit `textures.feature_repeated` windows on X1 (6), X2 (17), X4 (6), X5 (3), X6 (4: the
tavern, stables, houses, coach) present on the installed maps before; `empty_zones --check` fails on X1 (HEAD too).

### R1–R4 rebuilds D1–D6, D-189 Darkside (agent xeen-fb5-outdoor3, 2026-11-26; for A5, A6)

Scratch `output/xeen_fb/p5_outdoor3/` (`tools/run.sh`/`run2.sh` per map: regen + build until two builds are identical;
`tools/stage_check.sh`: the gate, `oymap audit` (no error the installed map lacks), `door_check`, `empty_zones`,
`check_reach`, `check_props_support` and every playtest plus the map's extra scenarios **from a hard-link stage**; then
`a6_install_baked.sh`, the installed checks, `level_pads --check`, a second regen; `tools/kerbs.py` sunk hull pieces;
`tools/tour.py`, `shoot.sh`, `sheet.py` captures). **All six installed with their bakes** on the oymap and game of 10:09:52
and the rim.py of 10:59 (kerbed hull pieces never sink): D6 11:07, D4 11:26, D3 11:28, D1 11:31, D5 11:35, D2 11:37.
Each: every playtest and extra passes from the stage (D1 `d1_ramp`, `d1_dreyfus_tower_steps`, `d1_hull_edge`; D4
`d4_same_map_ferry`, `d4_skerry_water_walk`; D5/D6 `hooks_d5_d6`, D6 `d6_ambrose_flight`), audit no new error,
`door_check` 0, `check_d85`/`common/d85` 0 errors, faces/fit/wild/walls 0, second regen identical, 0 kerbed hull
pieces sunk. (A first round at 10:34–11:07 had the 10:2x rim.py that also sank kerbed pieces; all six were rebuilt.)

**D-189 (Darkside sites).** D1 `dd01_outfall`: MM7's iron grate `c1d1` (seamless, opaque), 96 behind the frame (was
`7solid01`, 512). D2 `dd13_west`/`dd13_east`: a pair of the plank wing `xvdoorw`, each fitted to its 160 × 384 leaf
(`fit`), 128 back. D2 `southern_tower`: a door picture (below). Stay dark: D1 `dd10a_adit`, D2 `dd10b_adit`
(`door_check` lists them as openings into rock). `doors.black_built` 0 on D1–D6.
**D-180/D-190 (all 8 Darkside sites, `door_check` 0 errors).** D1 Ellinger's Tower 192 × 320 (its ground storey radius
416 → 440 so the jambs reach the studio's 16; the string courses at 448 still stand proud); Western Tower 160 × 320;
Kalindra's restored stable gate two 192 × 384 leaves of `chb1dl`. D2 Southern Tower 192 × 384. D3 Eastern Tower 192
× 320. D4 Blackfang's gate 384 × 448 (R4 alone). D5 Northern Tower two leaves, 384 × 448 (its ground storey 576 high,
the vowel sign over the door at 464). D6 Alamar's gate 512 × 448 (DD-17's way out 448 × 448). Two finds on the way:
the classic kit replaced the towers' MM7 tile doors with its single 128 `xvtdoor`, shown 1.5 times on a 192 leaf
(audit `doors.tiled`): `common/classic_kit.yml keep_doors` += `hkm1d`, `hkm3dr`; and a listed door bay with unlisted
rows above took the kit's window up the door's column (audit `feature_repeated`): the rows are listed as wall
(`upper_walls`).
**R2.** D1's mended mill `eaves: 24, verge: 40`; **D1 p3 resolved** (picture `after/d1/01-p3.png`). Soffits seen on
D1, D3, D4 (`after/d1/08-square_up.png`, `after/d4/05-town2.png`). **R1.** D4 `dd23_lair`: 0 flipped faces, lit
evenly (`after/d4/02-lair.png`); its `faces.flipped` line removed from `check_faces.yml`. **R3.** `town_fit_check`
0 errors on D1–D6 (the world's `decorations.through` kept line stays until X1–X7 are done too). **R4.** D2's great tree
door 352 high (`after/d2c/`), D4/D6 gates above.
**Plinths.** D6 Alamar NE tower: right as it is — its walls run down the cliff face to the slope, nothing hangs in the
air (`look/d6_ne_before/`, `after/d6/02-ne_tower_below.png`); kept in `town_fit_kept.yml` with that reason. X7's
Dragon Tower is the X-maps agent's.
**Hull and boulders.** Hull runs at the falls look closed beside the spillways (D1 rim falls, D3 Wrath Falls, D6 two
lavafalls: `after/d1_falls/`, `after/d3_falls/`, `after/d6_falls/`); D5's boulders sit sunk in the sand
(`after/d5/03-boulders.png`).
**`empty_zones.py --check` on D5 and D6: fixed.** Causes: on D5, D-142 (3.3) moved the marker at (68.5, 73) away from
D7's fall, leaving the Great Pyramid's forecourt (the land under the pyramid and D-142's buffers round DD-15's door) one
zone of 534 tiles; on D6, D-164 moved the moat's west-arm lava dwellers north, leaving 828 tiles of the west rim and the
land south of the moat. D5: the sixth sands lizard marker (82, 89) → (74, 81). D6: two field eyes (66, 31) → (29, 65)
and (95, 44) → (45, 71) (6,517 from the pyramid's door, past D-87.3's 5,888). Largest zones now D5 188, D6 290 tiles;
counts and kill XP unchanged. `--check` still lists X1 and X6 (the X-maps agent's).
