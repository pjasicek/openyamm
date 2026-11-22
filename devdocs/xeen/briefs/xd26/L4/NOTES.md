# XD-26 Gargoyle Eyrie, L4: notes

Built 2026-11-20 by `agent:xeen-a7-xd26` (lane A7, phase 2) with Map Studio, `world: xeen` from L1, from the MU-6 graph
(`devdocs/xeen/mockups/act2_graphs/xd26.graph.yml`) and D-4's decisions (`mockups/act2_dungeon_decisions.md`, XD-26).
Key `xd26`, `xeen_xd26.blv`, map_stats 9149, music 31, class S, on X4's Gargoyle Range; party 15-17, monsters 16-28,
treasure 2 (the roost's hoard 3), map qbits 110880-110919 (used: `hoist_winched` 110880).

**State: done in the scratch root, not in assets_dev.** Installed only in `output/studio_cal/xd26/root` (hard-link copy
of assets_dev with real `worlds/xeen/maps`, `events/maps`, and real copies of `data_tables/map_stats.txt` and
`bolster_maps.txt` carrying a hand-written row 9149 for testing, copied from XD-25's 9148 with slot `Xeen Gargoyle`,
music 31, CAVE: A2 writes the real row; the copies were refreshed from assets_dev on 2026-11-20 after D-17, the test row
added again). The lane lead installs into assets_dev.

Scratch: `output/studio_cal/xd26/` — `tools/gen.py` writes every project file (**edit gen.py, never the YAML**;
`gen.py --levels` writes L1-L3); `v.sh` regenerate + validate; `cycle.sh` regenerate, fmt, validate, build, install
into the scratch root, audit `--reach --solve`; `four.sh` the playtests (one game at a time;
`TESTS="playtest playtest_hostility playtest_flyers" N=4`); `shots.sh` + `shots.yml` the tour; `tools/sheet.py`
texture contact sheets (`tex/cand*.jpg`).

## D-17 (decided 2026-11-20, DECISIONS.md)

1. **Shaft floor to the first ledge: the graph's ladder** (`ladder:ledge_low`, in `room:shaft_floor` against the west
   wall under the first ledge's lip, at (4, 448), `exit` (-192, 448) on the ledge). The cut stair is gone. Every ladder
   has `grab_at_top: true`. The audit and `oymap solve` climb ladders: nothing above is unreached.
2. **The winch drives the fence's hoist** (`lift:hoist`, XD-11's two-state lift): a plank deck (`gkp1ceil`, 256 square,
   32 thick) on two ropes under a hoist beam, between `room:hoist_foot` (1024, a low cave under the high ledge's east end
   off the east nests) and `room:high_ledge` (1536) through a notch (`open:hoist_notch`, a floor opening). It starts
   `state: up`, flush with the high ledge. The winch (`switch:winch` in the fence's cache, `evt:winch`) lowers it the
   first time and sets `hoist_winched` (110880); after that the deck (`evt:hoist`) or a call rope at either stop
   (`switch:hoist_bottom`, `switch:hoist_top`) toggles it. Before the winch: "The platform hangs on its ropes at the
   ledge above. Its winch must be in the cave beside you." The plan's link is `link:hoist_high`, kind `lift`, "hoist:
   winch". The ledge_e → high_ledge ladder, `door:winch_ladder` and the ladder cleft are gone (the cleft became the
   hoist's foot: still 13 rooms). The pre-D-17 generator is kept as `output/studio_cal/xd26/tools/gen_before_d17.py`
   (`tools/patch_d17.py` made the change).

## What was built

13 rooms = 13 sectors (S ≤ 15), floor 15.2 M units² (walkable 13.5; S ≤ 20), 3 doors (S 3-8; the hoist besides),
3 chests, 3 ladders, a hoist, 2 loops, 10 spawn markers + 2 placed monsters (about 27).

- **Cave mouth** (floor 0, the map's start at (1344, -1000, 0) facing north): the arrival from X4's door:xd26; the
  daylight exit in its south wall (`exit:mouth`) leads out to X4's Gargoyle Range.
- **Shaft floor** (2,048 square, 2,560 high): every ledge opens on it through its whole side (`width: full, height:
  full` openings: lips with bare rock under them). The **rope bridge** is a plank deck (`platform:bridge`, top 1024,
  320 wide) across it from the west ledge to the east nests, rope rails on poles 64 over the deck; the south rail is
  torn away between x 896 and 1152 (the fall: loop:fall). A pole ladder up the west wall to the first ledge.
- **First ledge** (512) with the pole ladder up to the **west ledge** (1024); the **low nests** (512, straw, two nests)
  and the **rock ramp** (a climbing path room, 512 → 1024) are the loop's other way up.
- **West ledge** (1024): where the bridge starts; the high ledge's gap overhead (the 512 drop).
- **East nests** (1024): nests of sticks and bones; the fence's door in its east wall, the hoist's foot off its north
  wall.
- **The fence's cache** (1024): MM7's dry brown rock and a plank floor; crates and sacks tagged for buyers in Asp, an
  Obsidian Gargoyle guard, the strongbox (T2, trapped), the winch lever, a lantern.
- **Hoist foot** (1024): a low cave under the high ledge's east end; the hoist comes down here, its call rope on the
  west wall, a lantern.
- **High ledge** (1536): a shelf 384 wide and 4,096 long along the shaft's north side: the lip over the shaft, the gap
  over the west ledge, the hoist's notch at its east end under a hoist beam with a lantern and a call rope, the roost ladder on its north wall, the hanging moss (secret
  door) at its west end to the **hidden ledge** (the dead climber's pack, chest T2).
- **Matriarch's roost** (2048): the great nest (`platform:great_nest`, click: A3's hook), the matriarch (a placed
  Obsidian Gargoyle), two more nests, the hoard (chest T3, trapped). The **sky crack** opens east: the daylight exit in
  its east wall (`exit:sky_crack`) is one way out to a ledge high on the peak; clouds (`xwsky`) for a roof.

Critical path: mouth → shaft floor → ladder → first ledge → ladder (or nests and ramp) → west ledge → bridge → east
nests → fence's cache (winch) → hoist foot → hoist → high ledge → roost ladder → roost. Back: the sky crack (one way out to X4's
peak ledge), or down by the drop and the fall to the mouth.

## Monsters and treasure

One slot `Xeen Gargoyle` (A2's gargoyles, block 11540), `per_marker [2, 3]`, every marker fixing its tier:
5 tier-a markers (Gargoyle 16: shaft floor ×2, first ledge, low nests, west ledge), 3 tier-b (Gargoyle Lord 22: the
bridge, the east nests, the high ledge), 2 tier-c (Obsidian Gargoyle 28: the roost); placed: two Obsidian Gargoyles
11542 (the fence's guard, the matriarch). Mean 12.5 + 7.5 + 5 + 2 = **27**; kill XP 12.5 × 416 + 7.5 × 704 + 7 × 1,064
= 17,928, **4.48k per member** against MAPS §0's 4.1k (1.09). Levels 16-28. Treasure level 2; the hoard at 3.
No marker in a nook or a shelf opening (D-4).

**Flyers across the shaft (D-4):** `playtest_flyers.yml` kills the map's gargoyles, then spawns one Gargoyle on each
other ledge and asserts it comes within 480 of the party (they stop about 390 off to strike), deep in its ledge: party
in the east nests (from the west ledge and the first ledge), in the west ledge (from the east nests and the high
ledge), at the high ledge's lip (from the east nests, the west ledge and the first ledge's lip). 4 of 4. Found on the
way: (a) the first bridge (192 wide, rails 160 apart) trapped them between its rails (radius 103): the bridge is now 320
wide; (b) a gargoyle deep in a ledge does not notice a party above or below the lip (line of sight), nor one more than
about 3,000 away: as it should; the test's spawns stand where they see the party.

## Textures (21 distinct; S cap 30; 0 new)

- the eyrie: **MM7's dragon cave (7d36)**: `cwb1` rock on walls and roofs, `cfb1` rock floor; MM6 `straw` on the nest
  caves' floors, the world's `xobones` on the big nests;
- the fence's cache: MM7 `ch1b1` dry brown rock, MM8 `gkp1ceil` planks underfoot, `gkp103a` plank doors;
- timber: `t66abc10a` (XD-05's poles: rails, posts, ladders, nest rims), MM7 `7t1beds` planks on the bridge's deck;
- `xodaylt` (XD-05's daylight) on the two exits, `xwsky` (the world's clouds) over the sky crack; chests the
  world's plain chest.

## Original lines

XD-26 has no source map (the source's scarab lies outdoors); D-4 accepted Carlawna's and stock lines:
- "I know not why they took it, only that gargoyles are hired to steal things for people." (aaze0010:9) — on the
  fence's tag (`panel:tagged_crates`, crates on the cache's south wall, `evt:tags`): a scrap of her complaint to the
  Burlock watch tied to a crate, "Deliver to Asp. Quickly." scrawled under it (D-4);
- "Oh, thank you so much for recovering my Scarab." (aaze0010:11) — Carlawna's hand-in on X4 (A3's q-c10.yml);
- "The chest is empty." (aaze0081:8, stock) — the great nest's second click (A3's hook `else_text`).

The fence's tags are D-4's: on entering the cache, "Deliver to Asp: one silver mirror." / "Deliver to Asp: two
candlesticks." (the hook's own text carries "Deliver to Asp: one scarab." at the nest, so the map does not repeat it).

## Checks

- `validate` no issues (L1-L4); `fmt --check` clean; build: 1 warning (open:ramp_ledgew finds two wall pairs and takes
  the right one, the ramp's east end); `audit --reach --solve` (`output/studio_cal/xd26/audit.txt`): no error, no
  warning, 0 coplanar pairs, no dressing finding (two infos: the ladders' `uneven` poles and the daylight panels are
  "squashed" on purpose). `oymap solve`: wave 0 the mouth, shaft, both low ledges, nests, ramp, west ledge, east nests,
  hoist foot (and the fence's cache behind its door); wave 1, opened by the fence's door and the winch (the hoist down):
  the high ledge, the roost, the sky crack and the hidden ledge's doorway; wave 2 the moss (the hidden ledge); never
  reached 0. The high ledge, hidden ledge, roost and sky crack come only after the winch (D-17).
- Playtests from the scratch root with `--world xeen` (`four.sh`, logs `output/studio_cal/xd26/run/`, summary
  `output/studio_cal/xd26/four.out`): **4 of 4 each**: `playtest.yml` (118 steps before the exits opened: the shaft ladder
  up, down from its top and up again, the west-ledge ladder up and down, the nests and the ramp, the bridge, the hoist's
  call rope refusing, the fence, its tag line, its strongbox, the winch (the hoist comes down, hoist_winched), the deck
  up, down and up again, the top call rope sending the hoist down and back, the moss and the climber's pack, the roost ladder, the scarab once then "The chest is
  empty.", the hoard, the roost ladder down, the 512 drop, the fall off the bridge, back to the mouth),
  `playtest_hostility.yml` (20 steps), `playtest_flyers.yml` (25 steps), and since the exits opened
  `playtest_exit.yml` (21 steps: out by the mouth, `execute_event` 8, OK, on X4 at (-9216, 11376) with z 2,300-2,360,
  still there 2 s later; then `set_pose` back to the sky crack, `execute_event` 12, OK, on X4 at (-7424, 14592) with
  z 3,585-3,610, still there 2 s later). The walk (now 108 steps) no longer clicks the exits.
  **Latest run (after the exits opened, `four.out`): every step of all four playtests passes 4 of 4, and every run then
  crashes on exit (139)**: the `build-xeen` binary of 15:52 segfaults at the end of every headless scenario (XD-25's too);
  the lane lead counts a run whose every step passes as passed.
  (Before the exits: the 4 × 3 runs on the binary from before 15:52 exited cleanly.) Run `four.sh` again on a fixed
  binary for clean exits.
- Pictures: `output/studio_cal/xd26/shots/` (20; sheets `shots_0.jpg`, `shots_1.jpg`), `shots2/` (after fixes,
  `shots2_check.jpg`), `shots3/` (the tagged crates, the sky crack; `shots3_sheet.jpg`), `shots4/` (D-17: the shaft ladder, the hoist up and
  lowered, `shots4_sheet.jpg`); the hoist area was dark, so a lantern hangs at its foot and from its beam. Pictures with the lanterns are still to take (`shots5.yml`): `run_game.sh` refuses to start on the crashing binary. Looked at; fixed: a corpse meant for the shaft floor drawn on the bridge (decorations under the
  bridge now name `floor_height: 0`), the dark rock ramp (a light), the climber's corpse over his pack (moved).

## Dressing

Audit: no finding. Containers: two sacks on the cache's east wall and a keg on its north wall, clear of the door (the tagged crates are a wall panel); skull
piles, bones and stalagmites are rubble by walls. Dressing exceptions: none.

## Exits to X4 (opened 2026-11-20, X4 installed as `xeen_x4.odm`, row 9102)

Both ways out lead to X4 (project neighbours, `exit` presets; the built Lua has two `MoveToMap`s, both to
`xeen_x4.odm`). The pre-opening generator is `output/studio_cal/xd26/tools/gen_before_unseal.py`.

- **The cave mouth** (`exit:mouth`, the mouth's south wall, x 1152..1536, floor 0) → `exit:x4_range`: X4 at
  **(-9216, 11376, 2340) facing south (270)**, 400 south of X4's `door:xd26` face at (-9216, 11776).
- **The sky crack** (`exit:sky_crack`, the crack's east wall, floor 2048), one way → `exit:x4_peak`: X4 at
  **(-7424, 14592, 3600) facing south (270)**, on A5's ledge platform. No fall: it stands on the platform.
- **Measured heights** (2026-11-20, `four.sh`'s root with X4's files copied from assets_dev; the party dropped from
  6,000 at each point and read back): in front of the mouth the ground is **2,330** at (-9216, 11376), 2,357 at
  y 11550, 2,362 at y 11700 (just before the face), falling steeply south to about 1,830 at y 11100 and 1,796 at
  y 10800 (the mouth stands on a shelf 500 over the slope below; A5's DOORS.md estimate was ~1,880). The sky crack's
  ledge platform is level at **3,593** (from x -7650 to -7200 at y 14592; 3,634 at y 14800 behind it, 3,490 and 3,334
  down the path at y 14300 and 14000); A5's estimate was ~3,330. Arrivals stand 10 and 7 over these.
- **X4's `door:xd26`** (still sealed on X4, A5's) should arrive inside at **(1344, -1000, 0) facing north (90°;
  512 in the game's units)**, the map's start (`objects.start`). `playtest_exit.yml` checks the way out only.

## Words needed / workarounds

- No shipped hanging-moss texture: the secret door to the hidden ledge is drawn as the ledge's own rock (Open issues 2).

## Open issues

1. **Carlawna's theft line on a tag** reads as a scrap of her complaint to the Burlock watch (her topic in A3's
   q-c10.yml says the same words when the quest starts, so a player meets them twice, once from her, once on the tag;
   D-4 wanted it so).
2. **The hanging moss** is not drawn (no shipped texture; one new cut-out moss leaf would be within the cap: ≤ 4 new).
3. **The shaft is a plain box of `cwb1`** (rock walls straight, a flat roof 2,560 up): it reads as a tall cave but could
   gain uneven rock (`floor_points`/`ceiling_points`, outcrops) in a later pass.
4. A2's map_stats row 9149 is needed in assets_dev (the scratch root has a hand copy); then `tools/xeen/balance.py`.
5. Lighting bake: the lane lead's.

## Installed (2026-11-20, lane lead A7)

Built from this L4 (`output/studio_cal/xd26/a7_lead_build/`, identical to the scratch install, X4 exits open) and
installed into `assets_dev`; baked (profile `tools/lighting/baked_indoors/profiles/xeen_xd26.yml`, `bake_map.sh xd26
output/studio_cal/xd26/root --sources assets_source`, then `install_bake.py xd26`). The map does not load from
`assets_dev` until A2 writes map_stats/bolster row 9149; the playtests from `assets_dev` follow then.

**A5's built X4 points (2026-11-20, later):** the exits now use A5's built arrivals (they supersede the provisional
DOORS.md ones above): XD-07 gate (-1024, 6912, 1808) south, throw (-4608, 9728, 2504) east; XD-25 (-11520, -9448, 1056)
south; XD-02 adit (20080, -16128, 1504) west; XD-26 mouth (-9216, 11208, 1824) south, sky crack (-7424, 14592, 3600)
south. Measured landing Z: 1802, 1505 (ground), 1057, 1505, 1821.5, 3593. Exit playtests 4 of 4 with clean exits in
`output/studio_cal/a7/root_x4` (`output/studio_cal/a7/x4_built_four.out`); installed, re-baked.

## From assets_dev (2026-11-20, lane lead A7, fourth session)

With A2's row 9149: `playtest.yml` (108 steps), `playtest_hostility.yml` (20), `playtest_flyers.yml` (25) **4 of 4
each, clean exits** (`output/studio_cal/a7/s4_xd26_four.out`). `playtest_exit.yml` fails before leaving: X4's cooked
lighting no longer matches X4's geometry (A5 reinstalled X4 at 16:29, its bake is from 16:05; "outdoor lighting data was
cooked for different geometry", the map does not load). After A5's re-bake (16:44): `playtest_exit.yml` (21 steps)
**4 of 4, clean exits** (`output/studio_cal/a7/s4_xd26_exit.out`). Textures 21/30, 0 new.

**2026-11-20, fifth session (lane A7):** A5 confirmed the mouth exit at (-9216, 11208, 1824) (the earlier
(-9216, 11376, 2340) lay inside the mouth's rock); the exit already used it since the fourth session, only the
project's `arrival_hint` still quoted the old ground and is corrected. Rebuilt, installed (no stale bake);
`playtest_exit` 4 of 4 from `assets_dev` against A5's 16:55 X4 (landings 1,821.5 and 3,593).

## Sixth session (2026-11-20, lane A7)

- **Lamp rule (A1's lights audit, merge point 14):** the lights' heights were absolute; `light()` now takes the room's floor off (11 lights were inside the rock). Clean under the audit.

## Merge point 15 doors, AU's winch (2026-11-20, lane A7, seventh session)

- **Fence door** (`doors.tiled`: gkp103a, one wing of a pair, laid 1.5 times across the 192-wide folding leaf; a folding
  leaf lays its picture one texel to the unit whatever its size): now a hinged single leaf with MM6's single plank
  door `d2smldor`, fitted once on both faces (gen.py `PLANKDOOR`; the themes' door picture too).
- **AU's `xeen_winch`** (devdocs/xeen/AUDIO.md): `evt.PlaySoundName("xeen_winch")` on the winch and on each hoist move
  (the deck and both call ropes).
- Audit no error or warning; build warnings 1 (the ramp's wall choice, unchanged). Installed, re-baked; from
  `assets_dev`: `playtest` (108), `playtest_flyers` (25), `playtest_hostility` (20), `playtest_exit` (21) 4 of 4 each
  (`output/studio_cal/a7/s7_mp15_chain.out`).

## Twentieth session (2026-11-21, lane A7 lead)

- `exit:x4_range` names X4's `entrance:xd26_eyrie` (-9216, 10752, 1792) facing south (gen.py; the raw point (-9216, 11208, 1824) is gone, and the hint's old "ground 2,330" with it). Measured landing (-9216, 10752, 1793) facing 1536 (`playtest_exit.yml` asserts both). `exit:x4_peak` still lands on its raw point (-7424, 14592, 3600); X4 lists `entrance:xd26_sky_crack` (-7680, 14848, 3648), not switched (asked of A5).
- Built into `output/studio_cal/a7/s20/xd26/` with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the Lua differs by the way out only. Lua and studio file installed 06:51:18. Audit from `assets_dev` 0 errors, 0 warnings (`output/studio_cal/a7/s20/audit/xd26.txt`). **16/16 from `assets_dev`** (playtest 108, exit 21, flyers 25, hostility 20; `output/studio_cal/a7/s20/four_xd26.out`).

## chest.front (2026-11-22, lane A7 twenty-seventh session)

The build's `chest.front` warning (merge point 41: an indoor chest's `facing` is its long axis, its front 90 degrees
anticlockwise of it): the chest(s) it named turned 180 degrees in place, back to the wall, front to the room.
Installed with the bake; build warnings and audit as before.
`playtest.yml` fails 4 of 4 at step 14 (merge point 41's game): "could not take hold of ladder 'ledge_low' from
(-144, 448, 512)" when climbing down from the first ledge; it passed 4 of 4 on merge point 40 at 00:32 with the same
ladder (the chest change is across the map). Reported to A1.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.16 / 118 / 0 -> 0.33 / 208 / 0.34; family 7d21 (White
  Cliff Cave, the same cwb1/cfb1 rock; was `xd26`, no shipped map).
- s29: the ledges' floor grids finer (low nests, first and west ledge, step 192: the east ledge stays level for the
  playtest's stand); the landing on the west ledge after the drop asserts 976-1100 (its floor rises and falls).
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/xd26/shots/`  (01-1_arrival.png, 02-2_shaft.png, 03-3_roost.png); all eight maps on
  one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named from the mouth and the roost (gargoyles on
  straw under the crack); the shaft from its floor is plain: nests on every ledge (D-89) are still open.
