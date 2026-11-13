# What the next code batches take (merged from round five, XD-01's second pass and outdoor round two)

Written by the lead on 2026-11-13 from the agents' final reports. Each item names where it was found; the report is
the "Round five" (dungeons), "Second pass" (XD-01) or "Round two" (outdoor) section of that project's `NOTES.md`,
and repros are under `output/studio_cal/<key>/repro/` (build copies with `--out`). Indoor code batch five
(`output/studio_obj3/list.txt`) finished door leaves (`fold`, `travel`, `split`, `pictures`, `back_pictures`,
`tile`) and was cut off after that; its unfinished items are folded in below. Outdoor code batch four left
`core/OutdoorRim.{h,cpp}` written (900 lines, from measurements in `output/studio_s4e/orig/*.rim*.txt` and
prototypes in `output/studio_s4e/scripts/`) but called by nothing and not in the schema.

## Indoor, in order

1. **Item spawn points** (the Forge 17, Temple of the Moon 7, the Lincoln 20; every map has them): a random item of a
   treasure level, rolled when the map is first entered. `spawns[]` takes monsters only. Read how a shipped BLV's
   spawn records hold them.
2. **Quick ones:** `chests[].random_levels` is read by the build and refused by the indoor schema (Temple, Darkmoor:
   `chest_random_levels_schema`); a negative item id in a chest passes `validate` and fails the build (Temple
   `chest_random_levels`); `add: {var: Awards, value: 103}` builds as award 0, and an award for every member
   (Control Center `award_by_add`); `ids.lock.yml` keeps ids of removed objects (several maps; batch five was
   writing the prune when it stopped); a `lua` text must name a map variable by its number in the lock, which is
   not the declaration order (the Forge tested the wrong variable without a word); a mover's half-unit `at` against
   the east or north wall is refused (Abandoned Temple `mover_half_unit_at_wall`); a liquid texture asks for a
   `size` that `oymap assets` says it has none of (XD-01 `liquid_size`).
3. **Monsters:** the lead's check of the Lincoln's placed droids against the original's scene file: positions,
   kinds (`monster_info_id`) and hit points agree; the original's actor records also hold `monster_id` 5600 or 3000
   where the build writes the kind's number again, and `attributes` 65536 at the start (the agent sets that bit by
   a load event instead): find what both are and write them as the original does. One that carries an item (the Temple's captain and his longbow, Darkmoor's Lich King and his wand:
   `monsters[].carries`); one that starts invisible (the Lincoln's 17 droids, today a load event setting a group
   bit); one-sided doors and a different event for each side of a door (the Hive's doors 4, 5, 10 to 12; the
   Abandoned Temple's 63 and 64).
4. **`solve`, `audit --reach`, `probe`:** `solve` treats a `kills` condition as met (the Hive
   `kills_teleport_solve`: it puts the reactor's carry before the double door); a 32-unit step at a slope's foot
   blocks all three though the game walks it (the Lincoln `step_off_slope`); a sector lower than the party counts
   as never reached; they do not climb ladders; the 179-high mouth (Temple `low_mouth_solve`).
5. **Events the originals have and the words lack:** a decoration as an event's source (the Hive's keg, Darkmoor's
   crystal: `keg_decoration_source`, `decoration_source`); an event on leaving the map (`trigger: leave`: the
   Abandoned Temple's 6 and 10, the Hive's 65012); texture changes on faces and `SetFacetBit` (Darkmoor's cubes and
   forcefield `unseen_barrier`, the Abandoned Temple's door 1 and trap panels); a question whose answer is read
   (Darkmoor's sarcophagi `question`); a chest opened from a second source (Control Center `chest_from_shelf`); a
   message window; a door event that may run again.
6. **Shapes:** stairs open along their side (Darkmoor `stair_open_side`); floor points at the corners of a rock
   island (Temple `pillar_inside_steep`, believed a defect); banks steeper than 2 per run on upright feet (Temple,
   Darkmoor: the originals' are 2 to 3.6); leaning walls (the Lincoln's slope and viewport sides); a sheared tunnel
   and an end cut on a given plane (the Lincoln's lower corridor); a ceiling lower over part of a room (Control
   Center); tunnels: a raking sill and full width on side doorways, a section that changes along the way, fans
   toward junctions, a junction at a bend, more than 24 path points, a platform in a tunnel (the Hive).
7. **From batch five's list, not started:** a `bars` word (XD-01 made bars by hand from mover parts: it reads well);
   texture offsets and a way for `compare` to see them; the insets and banks and what slope the game walks; the
   surfaces left (bank sides, floor-hole rims, flight risers apart from sides); the small ones (the false "wall
   without thickness" warning, still in six maps; an opening flush to its wall's end); `compare` reading a
   one-sided upward sheet as invisible from below (the Abandoned Temple's false floor).

7a. **Spawn points take no group.** The Lincoln's original has its spawn points in group 51 (and others); the
   rebuild writes group 0 for every spawn point. `spawns[].group`. Found by the lead on 2026-11-13 while chasing a
   chance failure of the Lincoln's playtest (a spawned droid wandering into a locker's mouth takes the use key in
   about one run of three; see the comment in its `playtest.yml`).
8. **From XD-02, the Red Dwarf Mines** (`devdocs/xeen/briefs/xd02/L4/NOTES.md`, repros under
   `output/studio_cal/xd02/repro/`): `consume` inside an `any` condition is silently dropped and `once` on a click
   script event is silently ignored (`consume_in_any`); a map's own monster relations (MM7's dwarves are the
   party's friends: `clan_peaceful`, a Lua load event today); hiding a placed monster until an event; once per
   character; camera shake; a turning mover (the turntable); an exit on a moving part (the cart); lights and
   decorations riding a mover; a reveal surface per opening (secret doors in timbered rooms showed a frame); a
   clickable sunken pool (today a platform for its surface); several arrival points; the movers' schema text
   still says a level slide does not carry the party (it does since 2026-11-12, with `carry`); `oymap metrics`
   skips pulsing lights; `plan.yml` cannot say level L4.

9. **From the Temple of the Moon's round six** (its NOTES.md): `panels[].secret` (the rock-face chests do not pulse
   for a perceptive party); a pillar with several surfaces (the islands' carved faces); a chest opened only from a
   wall panel without naming a box (`chests[].panel`, or `box_of` left out when an `open_chest` names the chest);
   an upright corner between two banks (a floor point has one height); a doorway with filled corners (the double
   doors' octagonal frame).

10. **From XD-03, the Deep Mine** (`devdocs/xeen/briefs/xd03/L4/NOTES.md`, repros under
   `output/studio_cal/xd03/repro/`): a platform with `base` on a raised level is measured from the room floor and
   ends up buried in the level without a warning (`platform_on_raised_level`); `solve` ignores `monsters[].carries`
   (`solve_carries`); the sound refusal for MM7 is misleading and refuses the engine's own `lava loop.wav`
   (`sound_mm7`); `oymap assets` hints that mislead (`7dec11` "dirt" draws a tree, `Corpse`/`Corpse07` draw standing
   people); a condition on a monster's health; decorations hidden or swapped by an event; a floor's lava flag set by an
   event; rotating levers; things other than blocks, chests and switches riding a mover; exits on movers; one arrival
   point per project; `plan.yml` levels beyond L3. The scenario runner's `open_door` kills monsters near the door
   (it killed the gong sentry), a light assert on a pulsing light reads `unset`, and map timers do not run in
   screenshot tours (for the user).

11. **From Warlord's Fortress, first rebuild** (`devdocs/map_studio/briefs/mm6_6d16/L4/NOTES.md`, repros under
   `output/studio_cal/mm6_6d16/repro/`): a tunnel mouth into a room whose end wall rises into a whole-ceiling level is
   refused (`tunnel_mouth_gable`); a panel with `bottom`/`height` on a stair's raking wall builds with its bottom
   dropped though the schema says it is refused (`panel_on_stepped_wall`); click spots on tunnel sides, floors and
   roofs; a tunnel's chamfered roof carried into the room at its mouth, and over a side doorway; a random choice of
   teleport; effects that wait on a variable; a band at an absolute height on a raking wall; a random item by level
   and kind; two textures for a wall's two ends and doorway jambs; openings flush with a room's corner; the build
   warns for every light that is dark at the start though the originals' are (attribute 8).

12. **From the Hive's round six** (its NOTES.md "Round six", with the original's face numbers): a surface for a
   doorway's jambs; a recessed, bevelled wall panel; a hexagonal tunnel section; a chest lid laid from the chest's
   corner; texture offsets on movers and folding leaves; a leaf's own top, ends and underside; the reactor's damage
   hook (event 65010) and the kill flow's random carry (65011). Tools: `solve` files a `side` door's event under the
   sector its leaf is in, not its side; `press_interact` cannot expect "no target"; `ingame_compare.py` takes no
   console lines per shot and renumbers every later picture when one side skips a shot; `ids.lock.yml` is written
   into the project by builds with `--out` and by `oymap export <project>`.

13. **After the eighth merge (lead, 2026-11-13):** a chest kind's lid variant (the Forge's chest at (-1631, 6698)
   has the carved `ch3tpbv` top in the middle of its lid where `kind: ch3` lays `ch3topb`; MM6 has `ch2tpbv` too);
   the code agent's own "not fixed" list: MM7/MM8 chest variants (`7gt003` lock plates, "j" top ends), T65 crates,
   niche chests as a kind, more lever shapes (Darkmoor's plate-mounted arm), crossing beams and blocks built whole
   (they overlap in one plane), the coplanar check not knowing faces hidden inside a wall, `oymap things` choosing
   a blocked view of some levers.

14. **From Control Center's round six** (its NOTES.md "Round six", with face numbers): a door leaf's free edge
   takes the from room's reveal with all-zero texture coordinates (one flat colour; the original uses `swr4dk`,
   `swr3`, `swceilf`); one reveal per doorway, from one room only (two-sided frames); door frames that are not
   rectangles (an octagon, a funnel); a grate beside a pressure plate refused (face 1741) and texture regions on a
   level floor or ceiling only through points; a slit above a leaf (a leaf must fill its doorway); a button's top
   surface and its travel (13 in the original); picture offsets on doors and walls; a room's floor as a click source.

15. **From Castle Darkmoor's round six** (its NOTES.md, with face numbers): a leaf's free edge with a surface of its
   own (doors 1, 4, 5: `BemSV32c`, `BemV32c`, `BemVdk`); `set_texture` on one face of a platform (the podium's
   top) and a platform face's texture offset; an indoor sprite-change word (the crystal's `SetSprite(325)` by an
   entity number that moves); two openings in one wall closer than 16; a click on a forcefield face (event 58); floor
   mist. Tools: `oymap things` puts the crystal in sector 0; decoration numbers are not kept in `ids.lock.yml`;
   `ids.lock.yml` keeps a removed second leaf.

16. **From the Abandoned Temple's round six** (its NOTES.md): the party's eye outside the sector of the top it stands
   on (the arrival on the box's top at 2432: black view in every direction; given to code batch nine as its first
   item, as a check for every map); secret faces that are not doors (floor plates, 22 ceiling faces tracing a hidden
   walkway) and `secret` on one face of a leaf; cogs on doors and platforms (door 1's texture change, event 451's
   secret bit); a toggle with a guard condition (the trap panels relight on a second press only while the trap
   runs); stone chests (a carved front leaning back, a rim and lid; tapered, carved on two adjacent sides); a door's
   place in a deep doorway; a wall carving's phase under a niche. Tools: `audit` names a coplanar door by its lock
   number; `compare` counts the false floor seen from below and door faces in the maze passage. The scenario's
   `new_game_flow` party is one character with one pack (the cause of its step-175 failure: the idol needs a free
   2x4 block).

## Outdoor, in order

1. **The rim:** finish `core/OutdoorRim` (read the head of `OutdoorRim.cpp` and the measurements first), wire it into
   the lowering and the schema (`frame.rim` entries with a `form`, `frame.edge`), and judge it honestly in
   `oymap compare` (the party sees only its skyline from inside the playable square). Harmondale's twelve worst
   regions all lie outside the playable square.
2. **Land inside the square:** one-node ridges and ledges (`heights.ridges[]`: Harmondale E4 and three more
   stretches); ground roughness per area (Ravenshore: the original rises 213 per cell, the rebuild 185, everywhere).
3. **Decorations in rows and rings** (`scatter[].line` with `closed`: Ravenshore placed 438 singly instead).
4. **Buildings:** a door on an upper storey (`doors[].storey`); a hip roof with a flat top; one roof over a hall that
   is not convex (the Sanctum); an arcade; a bridge that arches, with kerbs above 256 (Harmondale's footbridge).
5. **Events:** a model import's faces (a `hint`, which faces click, a switch shared between structures: Ravenshore's
   ships and pier); the transition picture of a way into another map (`into.screen`); steps that run before the
   house opens (`lua_before`); calendar timers (`trigger: daily|weekly` with an hour: Harmondale's wells).
6. **The measure:** a model placed by a garbage stored centre (Harmondale's `Wagon_W_5`); a bridge's arch faces read
   as its top; `differences.json` should name the original's decorations without a partner; null decorations and
   empty hint events counted as things to pair.
7. **Text:** the sketch schema says `hip` is not for outline parts while the build accepts it.

8. **From outdoor round four** (both NOTES.md "Round four", repros under `output/studio_cal/<key>/repro/`):
   `oymap things` refuses outdoor maps (`things_outdoor`); a part with `outline` but no `shape: outline` builds as a
   box over the whole plot without a word (`outline_without_shape`); `oymap assets --world mm7` lists MM8 textures
   (`assets_other_world`); scatter placement depends on the entries before it (splitting one entry moves
   decorations all over the map); a height point on a cliff-line vertex moves the neighbouring node; a hole in a
   part (Harmondale's hatch and the chest in its pit); building forms the kits lack: round thatched halls, round huts,
   open pavilion shrines, a slender obelisk, signposts, recessed porch doors, crenellated gates, porches, hips without
   gables, front step slabs, wall signs, a door canopy, an open railing, fountains and wells, a cave mouth's arch
   (Ravenshore's Smuggler's Cove); a lit interior that the original keeps dark (Harmondale's stable).

## Not studio work (for the user)

- The game ignores a placed monster's hit points (XD-01's boss `boss_hp`: the scene holds 40, the game gives 21).
- A placed monster's own name shows on a living monster only with a row in the engine's `place_mon.txt`.
- MM7 has no ambient sound files of the names the studio places (XD-01 `sound_world_audio`).
- Outdoors, a model shown by a `SetFacetBit` event stays unclickable, in the shipped Ravenshore too
  (`output/studio_cal/mm8_out02/repro/wind_hidden/`).
- Headless runs plan monster paths inside the frame (no worker threads): a walk next to a 64-high block took 180 s
  of wall time for 5 s of game time (perf: 99.9 % in `ActorPathRuntime::queuePlan` -> `PathPlanner::plan`, up to
  8000 nodes outdoors). Plan on worker threads in headless runs or bound a plan's time; and line-buffer the scenario
  runner's output (its WALK lines come only at the end when written to a file). Found by outdoor code batch six.
- An item an event gives lands in the party's hand, where the scenario's `item_count` and the game's own HasItem
  test do not count it (a second click on Darkmoor's crystal gave a second crystal). The original Darkmoor drawn by
  OpenYAMM tints the walls round both lever niches red while a lever is pulled; worth a look (found by its round
  six).
- The scenario runner: the `light` assert takes the light's place in the built map's list, not its id; `mapvar()`
  in `play_lua` reads only named variables; a `lua_event` calling `evt.SetMonGroupBit` is not applied;
  `evt.MoveToMap` from a `lua_event` does not move the party (`load_map` does).
