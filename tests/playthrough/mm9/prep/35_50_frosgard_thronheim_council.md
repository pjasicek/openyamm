# Prep: segments 35-50 (Frosgard, Thronheim, the war council, peace between Sturmford and Drangheim)

Research for `35_*.yml` .. `50_after_council.yml` (2026-11-08). Chapter I's last two clans (Tryygva of Frosgard: Yanmir
and the ice; Kira of Thronheim: the Honkies and the Mountain Pass), the war council's call, and Chapter II's peace up to
just after the council when Yrsa has given her errand. Segment 50 must save
`output/playthrough/mm9/checkpoints/50_after_council.oysav`, equivalent to `00_after_council.oysav`, from which
`51_the_thing.yml` continues (Thronheim City, keys 93 and 185 set, 94 clear).

Sources: the map scripts (`assets_dev/worlds/mm9/events/maps/{frosgardcity,frosgard,yanmirsfort,thronheimcity,
thronheim,mountainpass,sturmfordcity,drangheimcity}.lua`), scenes (`assets_dev/worlds/mm9/maps/*.scene.yml`; the
review roots differ for yanmirsfort, frosgardcity and thronheimcity, but the game reads `assets_dev`), RUDE files
(`assets_dev/worlds/mm9/dialogue/rude/NPC*.rude`; columns: node, prompt, next node, required keys c7/9/11/13/15, given
c16-20, forbidden c21-25, taken c26-30), `mm9/extracted/SCRIPTS/SCRIPTS/UNITED.inc`, `map_transitions.txt`,
`transport_routes.txt`, converter work files (`level_generation/projects/mm9r_*/work/doors.json`, `content.json`) and
the geometry GLBs (`level_generation/projects/mm9r_{yanmirsfort,mountainpass_blv}/source/*.glb`) for routes.
Keys: `MM9.hasKey(K)` = qbit 90000+K. Items: engine id 10000 + raw MM9 id. Coordinates are native units; yaw 0 = +x,
pi/2 = +y.

**Validation.** Every part below passed headless (binary of 2026-11-08 21:23) in scratch probes, from `load_map` or
`00_after_council.oysav` with keys set by `set_qbit` / `qbit set|clear`. Probe files:
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/early3/`
(logs in `runs/`):

| Probe | What passed |
| --- | --- |
| `d_frosgard.yml` | Tryygva's two tasks, Bodvar's delivery, the barrel and the ice (key 72), Tryygva's ice reward (73, 175) |
| `d_gates.yml` | travel to Frosgard, the road gate into Frosgard City, the city's exit back to the region |
| `d_fortfull.yml` | **Yanmir's Sky Fort walked end to end**: TPS1 in, north route (no Squish at the entrance), secret wall, spiral stair, six supports, back up, east route to the feast hall, the lure, the trap (key 69), back out by TPS1 |
| `d_pass6.yml` | **the Mountain Pass walked end to end** from Thronheim to Thjorgard (keys 80; Trigger1 then Trigger0) |
| `d_thron.yml` | Kira's tasks, the dock gate, Moenach (139, 145), the three Honkies (142-144, 77), Kira's two rewards, her pledge and the council call (78, 81, 82, 83, 146, 152, 179) |
| `d_thron2.yml` | Thorolf in Thronheim City (84), Kira's treaty (88, 06:00 -> 180, 89, item 10401), the council door, the cinematic, Yrsa's dialogue (93, 185, 499; 94 clear; the treaty taken) |
| `d_peace.yml` | Sturmford: the city gate, Thorolf (84), Bjarni's war and treaty talks (86, 90); on foot to Drangheim; Sigmund's (87, 91); out of Drangheim City |

**Status (later on 2026-11-08).** Segments 35-44 and 50 exist and pass twice (`run.py 35 .. 50`) and once with
`--reload`, from `30_markel_joins.oysav`; 51-54 run on from `50_after_council.oysav`. Changes from this sheet: Tryygva's
clan check fixed in the converter (risk 7; `tests/scenarios/mm9/tryygva_united_keys.yml`); Yanmir's Key is a world item
(`pick_up`, 36); the lure ends the hall loop on its north side (the first version, from (492, -5000), let Yanmir step
onto the floor with the party still on it in the `--reload` run: the party fell to Frosgard City).

---

## Target state (00_after_council.oysav)

Keys set (qbit - 90000), read with a `play_lua` loop over `qbit(i)`: 1, 2, 3, 5, 7, 11-23, 25, 27-41, 43, 44, 46-52, 56-91,
93, 113, 114, 116, 117, 139, 142-147, 149-152, 163-165, 167, 168, 170-172, 175, 177-181, 184, 185, 196, 202, 242,
250-252, 311, 360, 362, 364-371, 378, 469, 471, 473, 474, 477, 480, 489, 495, 499, 510-517, 1021, 1022, 1030, 2008,
2009, 2046, 2081, 2083, 2084, 5004-5007, 5011-5013, 5020, 7001, 7114, 7116, 8500, 9507, 9508, 9511-9514.
Clear: 94, 95, 173, 174, 176, 186 (and 108). Notes:
- **My part's keys** that must be set in 50: 67-91 (both Jarls' tasks and pledges 74 and 82, 83 call, 84 message, 85
  council, 86-91 peace), 139 + 145 (Beldonia, the user's choice), 142-144 + 146 (Honkies), 152 (pass reward), 172 +
  175 (Tryygva's rewards), 178/179 (clans united), 180/181 (treaty), 184 (council), 40, 93, 185, 499, 1021/1022
  (Bodvar), 378 (Frosgard dock schedule, optional: talk to the Frosgard dockmaster once the docks are free), 7001
  (Yanmir's key, optional: the user had it; see the fort's optional block).
- Forad Darre has left the party (the council's `forad` step, `MM9.removeHireling(2)`; key 29 stays).
- The Peace Treaty (10401) is gone. Kira (actor 41) is hidden on every later load (`show(41, not has(40) or has(108))`).
- Loading 00 prints "map thronheimcity.blv changed since the save; its state was reset": its map state is not part of
  the equivalence.
- Keys 250-252 (Capstone) are set in the user's save: earlier than the story needs them; not mine.

## Traversal risks and suspected bugs (read first)

1. **The Mountain Pass cannot be walked with walk_to's planner.** On this open-air BLV region the indoor path map plans
   "partial" routes that hit the 400 000 node limit, put waypoints at z -328 (under the terrain) and climb the
   mountainsides (the party stalls at (-5571, -13803, 1983), (-336, -11394, 1334)). The scene blocks steep slopes
   (`party_movement: steep_slopes: block`, normal z < 0.707). Straight lines between points along the valley stall on
   decorations and walls ((-7157, 6234)). **Fix used:** `plan: false` via points from a floor/wall BFS of the GLB
   (walkable normal >= 0.707, walls and decorations inflated by the party radius, rise <= 45 per 64-unit cell, a
   penalty near walls so the route keeps to the valley's middle); validated in `d_pass6.yml` (below). Tool:
   `scratchpad/early3/tools/walk2.py` (`route_c`, `simplify`), then a Douglas-Peucker pass at 90 units. Worth a look
   by whoever owns walk_to: the path map for MM9 open-air regions.
2. **Yanmir body-blocks the entrance door.** SquishTrigger0 (-4215..-3895, -2874..-2042) is the west door of his hall
   (DPortal22, -3973). Walked in from the west gate he wakes, walks at the party and stands in the doorway: walk_to
   stalls at (-4021, -2906) for good (`d_fort.yml`). He cannot be killed (`clear_hostiles` reports "killed 1" every
   sweep; his HP stays 850, the damage hook zeroes it). **Fix used:** the north route (DPortal18 -> NW room -> stairs
   -> upper corridor), which wakes him at SquishTrigger1 (DPortal12, upper level) far from him, so he never reaches the
   party; the party comes back to his hall by the east corridor later to lure him.
3. **Yanmir does wander** (scene `mm9_ai.wander: path`, 31 points through the trap hall): seen at (609, -9603) and
   (497, -10880) in the trap hall, (-1113, -196), (-265, -4117) in the feast hall. The converter README's "Yanmir does
   not walk his path" (Deviations) is stale. He did **not** walk into the armed trap on his own in 6 minutes
   (`d_fort7.yml`): a lure is needed. Risk: if he stands in the trap box (x 123..891, y -9513..-6697) when the sixth
   support breaks, the trap fires at once; with the party in the basement (inside EndOfWorld, x -82..1065,
   y -10854..-6554, z -9175..-768) the party is then sent to Frosgard City (`FellToCity`, keys still given).
   Mitigation: break the supports far end first and the two at y -10039 last, then leave by the spiral at once.
4. **Doors.** walk_to's click-ahead opens the fort's double doors, but only after 6-7 s of stuck handling each: the
   route clicks each door's event from 300 in front (`click(ev); wait(2.0)`), then walks through. The open secret wall's
   leaf (pivot (2580, -14459), swings -90 deg) blocks the passage's north half: walk along y -14700 (stuck at
   (2652, -14481) otherwise). Ice Lobbercicles and spawned Yetis stand on the spiral stair: the climb back up needs
   `clear_hostiles` (stalled with actors 74/80/82 at 4-114 units without it).
5. **Exit volumes are thin.** TPS1 (Frosgard -> fort, half 92 x 20) and the fort's TPS1 (half 20 x 92): a walk_to with
   the default radius 64 "arrives" before the volume. Aim 100+ beyond it with `radius: 10, plan: false`.
6. **Thorolf does not come to the party in Thronheim City.** From the land gate (14377, 164) Thorolf1 (actor 9, at
   (13025, 1147)) is 1 650 away, beyond his 1 536 sight; 15 s of `present_dialogs` showed nothing. Place the party
   300 from him and `interact_actor` (as segment 59 does in Frosgard). In Sturmford City Thorolf0 (actor 44) stands at
   (9994, 14090), next to the land-gate arrival; the same pattern works.
7. **Suspected bug: Tryygva's clan check.** `frosgardcity.lua:132` (from `mm9r_frosgardcity/citylua.py:58-59`,
   "Thjorgard City's NPC3 reading": Sven's list) gives key 178 for keys 82, 38, 51, 63, **74**. MM9's
   `UNITED.inc :TryygvaInit` reads 82, 38, 51, 63, **34** (Tryygva's own pledge 74 is never part of his list; Sven's
   34 is). Effect: Tryygva offers "The Clans have united..." without Sven's pledge. Harmless in this run (all clans are
   done before the call) but wrong.
8. Kira's 06:00 clock (`thronheimcity.lua:119-125`) needs the map loaded across a 06:00 (or a return later): resting
   in the city (`advance_game_time: {hours: 24}` stands in) works (`d_thron2.yml`).
9. Boats: Frosgard's routes need key 73 (Tryygva told of the ice) (`transport_routes.txt`: The Raider (Moenach, 257)
   Sunday 3 days, The Racing Fire (Frosgard dockmaster, 209) Tuesday 3 days). The first trip to Frosgard is on foot
   (Thronheim ExitTrigger3 -> Frosgard, 5 days). Segments use `travel` with the days.

## Guide errors (tools/mm9_site/story/ch1c_ch2.yml)

- Tryygva's first talk: "We need your help." leads to "But without your help, the Chedian will perish!" and "Perhaps we
  could help?" (key 67) before "Tell us about the frost giant." The guide's "About those things you need done..."
  appears only on later talks (it has four dots in RUDE: "About those things you need done....").
- Tryygva's pledge after the ice: "The ice has been cleared from the docks." -> "The boats should be coming very soon."
  (73) leads straight to node 16, whose line is "Now that we have done as you asked, will you join us?" (the guide's
  "We have done as you asked.  Will you help us now?" is the root-menu variant).
- Kira's first lines are longer than the guide's: "There is an army marching towards Thronheim as we speak.", "We've
  been to see Yrsa the Troll on the Isle of Ashes.", "Yrsa sent us to unite the Six Clans against them.", "Name your
  task.  We shall prove our worth." (match_label falls back to "contains", but use the full lines).
- Kira's council line has no full stop: "The clans are united.  It is time for the war council" (node 16).
- Yanmir: the guide's "Let Yanmir see you in the feast hall, then run south through the hallway" is right; "he wakes
  as soon as you walk in" holds only for the west door (risk 2).
- Bjarni's talk has two lines the guide skips: "Kira has told us you have gone to war with Drangheim!!" and "You must
  stop this war immediately!" before "They didn't do that, we did!".
- Yrsa's first line is "Yrsa?  What do you want?" (the guide starts at "What? We're a little busy right now.").

---

## Segment plan

All `walk_to` steps below take `clear_hostiles: 1500` unless they say otherwise. Every dialogue ends on its last line
(often "Goodbye.") or `press_action: {action: cancel_dialog}`; exit handlers run on either.

### 35_frosgard_ice: Tryygva's tasks and the ice (Frosgard City)

Start: assert pledges of the other clans as the previous agent leaves them (at least 38, 51, 34, 63 for the council
call later); `qbit_clear: [90067, 90071, 90072]`.
1. `travel: {map: frosgard.blv, days: 5}` (on foot from Thronheim; the harbour is frozen).
2. Road gate (frosgard ExitTrigger2 (1783, 3320, 1738), half 1311 x 128): `set_pose (1783, 3700, 1738) yaw -pi/2`,
   `walk_to (1783, 3250, 1738) expect: dialog`, "OK", `advance_runtime {1, follow_map_move}` -> frosgardcity
   (FrosgardCityStart (10486, 7209, -4)).
3. Tryygva Ravenlocks, actor 5, (-3768, -1638, 45), seated in the City Hall (`show(5, has(108) or not (has(104) or
   has(40)))`). `set_pose (-3568, -1638, 45) yaw pi`, `interact_actor 5` (handler 53075: the clan check, RUDE 180):
   "We need your help." -> "But without your help, the Chedian will perish!" -> "Perhaps we could help?" (67) ->
   "Tell us about the frost giant." -> "What can we do to help?" -> "We will do this for you." (68) ->
   "Tell us about the frozen sea." -> "What can we do?" -> "We will do this for you." (71) -> "Thanks for your time.".
   Assert 90067, 90068, 90071.
4. Bodvar Elvissen, actor 25, (15811, -1966, 4): `set_pose (15611, -1966, 4) yaw 0`, `interact_actor 25` (RUDE 215):
   "What do you do all the way out here?" (1021; stays on the root) -> "Say, you wouldn't mind making a delivery would
   you?" (1022; needs 71 and 1021) -> "On the ice just outside the dock." -> "Thanks for the tip." -> "Goodbye.". The
   exit (50571) shows the barrel (cog 404). Assert 91021, 91022.
5. The barrel (DestructableProp0, event 232) on the ice at (4260, -11796, -289), over the cannon. The pier:
   `set_pose (4260, -10486, -81) yaw -pi/2`, `walk_to (4260, -11000, -81) plan: false radius 60` (800 from the
   barrel; its burst is 512 and 100 fire). `play_lua: click(232); wait(18)`: status "The powder barrel explodes!", the
   cannon fires 8 bolts, cinematic `break_ice` (16.3 s), the floes sink; `iceReward`: key 72, 8 000 experience. Assert
   90072. (A player shoots it; a click is the converter's stand-in.)
6. Optional (00 has 378): the dockmaster Jozka Atlia, actor 8, (4751, -10650, -81): `interact_actor 8`, cancel: the
   exit gives the Boat Schedule (item 562) and key 378 once 72 is set.
7. Back to Tryygva (step 3's pose): "The ice has been cleared from the docks." -> "The boats should be coming very
   soon." (73) -> "Thank you." -> "Thanks for your time.". Exit 50075: 175, 12 500 experience, 3 000 gold. Assert
   90073, 90175. Save `35_frosgard_ice`.

### 36_yanmirs_fort: Yanmir's Sky Fort, walked (validated as `d_fortfull.yml`)

Start: assert 90068 set, 90069 and 90173 clear.
1. City exit (frosgardcity ExitTrigger0 (11983, 8146, 428), half 1311 x 128): `set_pose (11983, 7700, 0) yaw pi/2`,
   `walk_to (11983, 8400, 0) z_tolerance 700 radius 10 plan: false expect: dialog`, "OK", follow -> frosgard
   (FrosgardCityExit (2733, 4536, 1261)). Validated in `d_gates.yml`.
2. The teleporter to the fort (frosgard TPS1 (-21900, -7483, 2780), half 92 x 20 x 143), on the shore below the fort
   (outdoors: placed): `set_pose (-21900, -7156, 2611) yaw -pi/2` (the fort's return arrival, YanmirsMainExit),
   `walk_to (-21900, -7600, 2700) z_tolerance 400 radius 10 plan: false expect: dialog`, "OK", follow ->
   yanmirsfort StartPoint0 (-8197, -2458, 1), the west gate.
3. The walk (doors: event = DPortal handler; each is clicked from in front):

```yaml
  - walk_to: {via: [[-5079, -2458, 0]], x: -5079, y: -400, z: 0, radius: 60, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(111); wait(2.0)'}          # DPortal18, north of the entrance corridor
  - walk_to: {x: -5079, y: 500, z: 0, plan: false, radius: 80, timeout_seconds: 60, clear_hostiles: 1500}
  - walk_to: {x: -5300, y: 1065, z: 0, radius: 60, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(103); wait(2.0)'}          # DPortal10, west into the stair room
  - walk_to: {x: -6200, y: 1065, z: 0, plan: false, radius: 80, timeout_seconds: 60, clear_hostiles: 1500}
  - walk_to: {via: [[-7400, 1100, 0], [-7400, 2000, 512], [-7400, 2700, 655], [-4000, 3500, 655]], x: -1700, y: 3441, z: 655, radius: 60, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(105); wait(2.0)'}          # DPortal12 (SquishTrigger1 here wakes Yanmir, far below)
  - walk_to: {via: [[-1000, 3441, 655], [500, 3500, 655]], x: 2000, y: 3441, z: 655, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(104); wait(2.0)'}          # DPortal11
  - walk_to: {x: 3850, y: 3441, z: 328, plan: false, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(107); wait(2.0)'}          # DPortal14, into the key room
  - walk_to: {via: [[4600, 3441, 328]], x: 5950, y: 5079, z: 328, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(108); wait(2.0)'}          # DPortal15, east wing
  - walk_to: {via: [[6700, 5079, 328], [7700, 4300, 328], [7700, 1500, 0]], x: 7864, y: -1500, z: 0, radius: 60, timeout_seconds: 90, clear_hostiles: 1500}
  - play_lua: {source: 'click(109); wait(2.0)'}          # DPortal16, into the east corridor (y -2458)
  - walk_to: {via: [[7864, -2458, 0]], x: 8900, y: -2458, z: 0, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(117); wait(2.0)'}          # DPortal24, onto the long curved corridor
  - walk_to: {via: [[9700, -2458, 0], [10200, -4000, 0], [8900, -7000, 0], [8000, -9500, 0]], x: 7537, y: -10750, z: 0, radius: 60, timeout_seconds: 200, clear_hostiles: 1500}
  - play_lua: {source: 'click(127); wait(2.0)'}          # Portal4
  - walk_to: {via: [[7537, -11500, 0], [5900, -13400, 0]], x: 5200, y: -13763, z: 0, radius: 100, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(125); wait(2.0)'}          # Portal12, into the wedge room (thralls)
  - walk_to: {via: [[4400, -13763, 0]], x: 2900, y: -14582, z: -41, radius: 60, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(210); wait(2)'}            # the bookcase: Secretdoor opens for good (SecretOpen 1)
  # west along the passage's south half (the leaf), then down the spiral stair (counter-clockwise, -328 -> -983)
  - walk_to: {via: [[2900, -14700, -41], [2300, -14700, -96], [1500, -14650, -188], [700, -14650, -292], [420, -14560, -328], [292, -14523, -350], [189, -14571, -420], [123, -14665, -490], [113, -14778, -560], [161, -14881, -630], [255, -14947, -700], [368, -14957, -770], [471, -14909, -850], [537, -14815, -930], [549, -14721, -983], [500, -14450, -983]], x: 500, y: -13300, z: -983, plan: false, radius: 50, z_tolerance: 400, timeout_seconds: 60}
  - walk_to: {x: 492, y: -11700, z: -962, radius: 100, timeout_seconds: 120, clear_hostiles: 1500}
  # the six supports under the trap hall, far end first (events 38759+k: the support's click, a killing blow)
  - walk_to: {x: 205, y: -7738, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38763); wait(0.5)'}        # DestructableBrush4
  - walk_to: {x: 778, y: -7738, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38764); wait(0.5)'}        # 5
  - walk_to: {x: 205, y: -9048, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38761); wait(0.5)'}        # 2
  - walk_to: {x: 778, y: -9048, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38762); wait(0.5)'}        # 3
  - walk_to: {x: 778, y: -10039, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38760); wait(0.5)'}        # 1
  - walk_to: {x: 205, y: -10039, z: -962, timeout_seconds: 60, radius: 60}
  - play_lua: {source: 'click(38759); wait(0.5)'}        # 0: TrapArmed 1
  - assert: {state_dump_named_map_var: {name: TrapArmed, value: 1}}
  # back up the spiral to the wedge room at once (clear_hostiles: monsters stand on the stair)
  - walk_to: {via: [[492, -11700, -962], [500, -13300, -983], [500, -14450, -983], [549, -14721, -983], [537, -14815, -930], [471, -14909, -850], [368, -14957, -770], [255, -14947, -700], [161, -14881, -630], [113, -14778, -560], [123, -14665, -490], [189, -14571, -420], [292, -14523, -350], [420, -14560, -328], [700, -14650, -292], [1500, -14650, -188], [2300, -14700, -96]], x: 2900, y: -14700, z: -41, plan: false, radius: 50, z_tolerance: 400, timeout_seconds: 120, clear_hostiles: 1500}
  # back east and round to the feast hall's east door
  - walk_to: {via: [[4400, -13763, 0]], x: 5200, y: -13763, z: 0, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(125); wait(2.0)'}
  - walk_to: {via: [[6200, -13600, 0], [6900, -12800, 0]], x: 7537, y: -11500, z: 0, radius: 120, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(127); wait(2.0)'}
  - walk_to: {via: [[7537, -10750, 0], [8000, -9500, 0], [8900, -7000, 0], [10200, -4000, 0]], x: 9700, y: -2458, z: 0, radius: 60, timeout_seconds: 200, clear_hostiles: 1500}
  - play_lua: {source: 'click(117); wait(2.0)'}
  - walk_to: {x: 5300, y: -2458, z: 0, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(116); wait(2.0)'}          # DPortal23, into the feast hall
  # the lure: a loop through the hall until Yanmir targets the party, then south through the trap hall without stopping
  - walk_to: {via: [[2500, -2500, 0], [1500, -800, 0], [-1500, -800, 0], [-3000, -2500, 0], [-1500, -4500, 0]], x: 492, y: -5000, z: 0, radius: 150, timeout_seconds: 120, clear_hostiles: 1500}
  - advance_runtime: {seconds: 4}
  - walk_to: {x: 492, y: -5300, z: 0, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(112); wait(2.0)'}          # DPortal19, the trap hall's north door
  - walk_to: {x: 492, y: -10900, z: 0, plan: false, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(113); wait(2.0)'}          # DPortal20, its south door
  - walk_to: {x: 492, y: -11900, z: 0, plan: false, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua:
      max_seconds: 200
      source: |
        for i = 1, 40 do wait(3); if mapvar("YanmirGone") == 1 then break end end
        if mapvar("TrapFired") ~= 1 then error("Yanmir never fell") end
  - assert: {qbit_set: [90069], qbit_clear: [90173]}
  # out by the west gate (never over the fallen trap floor: it sends the party to Frosgard City)
  - walk_to: {via: [[2000, -11700, 0], [4000, -11100, 0], [6000, -10200, 0], [8000, -9500, 0], [8900, -7000, 0], [10200, -4000, 0]], x: 9700, y: -2458, z: 0, radius: 100, timeout_seconds: 300, clear_hostiles: 1500}
  - play_lua: {source: 'click(117); wait(2.0)'}
  - walk_to: {x: 5300, y: -2458, z: 0, radius: 60, timeout_seconds: 60, clear_hostiles: 1500}
  - play_lua: {source: 'click(116); wait(2.0)'}
  - walk_to: {via: [[4500, -2458, 0], [0, -2458, 0]], x: -3600, y: -2458, z: 0, radius: 60, timeout_seconds: 120, clear_hostiles: 1500}
  - play_lua: {source: 'click(115); wait(2.0)'}          # DPortal22
  - walk_to: {x: -7500, y: -2458, z: 0, timeout_seconds: 120, clear_hostiles: 1500}
  - walk_to: {x: -8900, y: -2458, z: 0, radius: 10, plan: false, timeout_seconds: 30, expect: dialog}   # TPS1
  - select_topic: {match_label: "OK"}
  - advance_runtime: {seconds: 1.0, follow_map_move: true}
  - assert: {map: frosgard.blv}
```

   Observed in the validated run: Yanmir targeted the party during the hall loop (at (-1477, -4296), then
   (-282, -4989)), followed through DPortal19 and fell while the party stood at (492, -10900): the party was on a
   watch rail (WATCH boxes, `yanmirsfort.lua:139`), so the "no camera" path ran (`Cinema.yanmir_death.started` 0,
   TrapFired, YanmirGone, key 69, 8 000 experience). The yanmir_death cinematic plays only with the party off the
   rails (beyond y -11428), which needs the party out of the south door before he reaches the box; not required.
   Optional, as the user's save has key 7001: Yanmir's Key (event 212 at (5322, 2321, 605) in the key room, item 10570,
   key 7001), then the seven cages (events 220-226, `RotatingDoor61-67`) and a click on each child (events
   53618-53624, actors 64-70) sends it away. The Sage's Diary (chest in the far west room) is lore only.
   Save `36_yanmirs_fort`.

### 37_tryygva_pledge: Tryygva's reward and pledge

1. Into the city (35 step 2), Tryygva (35 step 3's pose), `interact_actor 5`: "Yanmir the Frost Giant is dead." (needs
   69) -> "Perhaps they were not strong enough." (70) -> "Now that we have done as you asked, will you join us?" (needs
   70 and 73; gives 74) -> node 17: "We shall be having a war council soon." (forbid 178) -> "We have more to do, but
   when that is done, we shall." -> "Goodbye.". Exit: 172 (18 500 experience, 10 000 gold).
   If 178 is already set (risk 7: his check misses Sven), node 17 offers "The Clans are united.  It is time for the
   war council." instead; do not take it here (the call goes to Kira in 40).
   Assert 90070, 90074, 90172. Save `37_tryygva_pledge`.

### 38_kira_honkies: Kira's tasks, Moenach, the Honkies

1. `travel: {map: thronheim.blv, days: 3}` (The Racing Fire, Tuesday, now that 73 is set; or 5 on foot).
2. Land gate (thronheim ExitTrigger2 (1392, 6498)): `set_pose (1392, 6100, 1279) yaw pi/2`, `walk_to (1392, 6498,
   1279) expect: dialog`, "OK", follow -> thronheimcity Startpoint0 (14377, 164, 3093) (as segment 52).
3. Kira the Cold, actor 41, (-11182, 16865, 3278), in her hall behind KiraDoor1/2 (event 232, y 15493): place the party
   inside, `set_pose (-11182, 16500, 3278) yaw pi/2`, `interact_actor 41` (53228: key 178 if 34, 38, 51, 63, 74;
   RUDE 239): "There is an army marching towards Thronheim as we speak." -> "They are too strong for you." -> "We've
   been to see Yrsa the Troll on the Isle of Ashes." -> "Yrsa sent us to unite the Six Clans against them." -> "We
   will." -> "Name your task.  We shall prove our worth." (75) -> "What is the first task?" -> "How?" -> "We will do
   this for you." (76) -> "What is the second task?" -> "We will find the Mountain Pass for you." (79) -> "Thanks for
   your time.". Assert 90075, 90076, 90079 (and 90178 when the four other clans and Tryygva have pledged).
4. Dock gate (thronheimcity ExitTrigger0 (2089, 15073, 3415), half 492 x 164): `set_pose (2089, 14600, 3093) yaw
   pi/2`, `walk_to (2089, 15073, 3093) expect: dialog`, "OK", follow -> thronheim TownDockExit (5099, 15222, 1270).
5. Moenach A'Tryht, actor 45 in thronheim, (7638, 14976, 1281), on the pier: `set_pose (7438, 14976, 1281) yaw 0`,
   `interact_actor 45` (RUDE 257): "We'd like to ask you a favor." (needs 76) -> "We need to send some people away." ->
   "Perhaps." -> "We'd like to send them to Beldonia." (139, 145; the user's choice, in 00) -> "Thanks." ->
   "Goodbye.". Assert 90139, 90145.
6. Back in by the dock gate (thronheim ExitTrigger1 (4484, 15222), half 164 x 573): `set_pose (4900, 15222, 1281) yaw
   pi`, `walk_to (4484, 15222, 1281) expect: dialog`, "OK", follow -> thronheimcity Startpoint1 (2048, 14664, 3093).
7. The Honkies (group 5, near the land gate; each leaves on its dialogue's exit, handlers 50056/50058/50057):
   - Muiredach A'Lanth, actor 1, (13435, 6390): `set_pose (13235, 6390, 3093) yaw 0`, RUDE 271: "We'd like you to tell
     us about the Great Honk." -> "Great! Why don't you meet us at the docks?" -> "Some friends of ours also want to
     hear." (142) -> "Goodbye.".
   - Comgghan A'Feslo, actor 3, (9830, 6717): `set_pose (9630, 6717, 3093) yaw 0`, RUDE 272: "We want to know more
     about the Honkies." -> "Our friends also would like to hear." -> "They work on the docks." (143) -> "Thank you."
     -> "Goodbye.".
   - Yoltzin Tor, actor 2, (13107, 6717): `set_pose (12907, 6717, 3093) yaw 0`, RUDE 279: "We need your help." -> "We
     have friends at the docks who would like to hear about you." (144) -> "Thank you." -> "Goodbye.". The third
     gives key 77 and 8 000 experience.
   Assert 90142-90144, 90077. Save `38_kira_honkies`.

### 39_mountain_pass: the Mountain Pass, walked (validated as `d_pass6.yml`)

1. Land gate out (thronheimcity ExitTrigger1 (14950, 82), half 164 x 410): `set_pose (14500, 82, 3093) yaw 0`,
   `walk_to (14950, 82, 3093) expect: dialog`, "OK", follow -> thronheim TownExit (1412, 5883, 1279).
2. The pass's exit on the east side of Thronheim (thronheim ExitTrigger0 (-17306, 14679, 2916), half 983 x 164;
   3 days): `set_pose (-17306, 14100, 2600) yaw pi/2`, `walk_to (-17306, 14679, 2600) z_tolerance 600 expect: dialog`,
   "OK" (title "Mountain Pass"), follow -> mountainpass ThronheimStart (-19145, 20120, 1).
3. The walk (risk 1). Trigger1 (-11900..-11245, 12368..14334) then Trigger0 (15461..17427, -5163..-4508); the second
   pays key 80 (with 79) and 12 500 experience (`mountainpass.lua:21-40`). Every leg `plan: false, radius: 120,
   z_tolerance: 300, clear_hostiles: 1500` (it killed 14, 42 and 18 in the validated run; legs took 19, 96 and 33 s):

```yaml
  - walk_to: {via: [[-19360, 19744, 0], [-19488, 18848, 0], [-19744, 18464, 0], [-19744, 16224, 0], [-19552, 16032, 0], [-19232, 15840, 0], [-18336, 15840, 0], [-17696, 16672, 0], [-16736, 16928, 0], [-16288, 17376, 0], [-14752, 17376, 0], [-14624, 16928, 0], [-14240, 16544, 0], [-14240, 16160, 0], [-13408, 15200, 0], [-13408, 14816, 0], [-13024, 14304, 0], [-12064, 13408, 0]], x: -11552, y: 13344, z: 0, plan: false, radius: 120, z_tolerance: 300, timeout_seconds: 300, clear_hostiles: 1500}
  - advance_runtime: {seconds: 1}
  - assert: {state_dump_named_map_var: {name: PassSteps, value: 1}}
  - walk_to: {via: [[-6368, 13344, 0], [-6240, 13216, 0], [-5408, 13216, 0], [-5216, 13024, 0], [-5216, 11488, 0], [-6368, 10336, 0], [-6368, 9696, 0], [-6752, 9312, 0], [-6816, 8736, 0], [-7136, 8416, 0], [-7136, 6944, 0], [-7456, 6304, 0], [-7712, 5280, 0], [-7904, 4832, 0], [-8352, 4384, 0], [-8352, 4128, 0], [-8736, 3744, 0], [-8736, 3296, 0], [-9184, 2848, 0], [-9184, 2080, 0], [-9568, 1696, 0], [-9568, -3104, 17], [-9952, -3488, 60], [-9952, -4320, 126], [-10336, -4704, 133], [-10336, -5088, 161], [-11232, -5984, 161], [-11808, -6816, 176], [-11936, -7200, 189], [-11936, -8672, 152], [-12384, -9120, 152], [-12384, -10336, 231], [-12768, -10720, 231], [-12768, -11488, 400], [-13152, -11872, 433], [-13152, -14496, 640], [-11104, -16544, 916], [-8224, -16544, 1394], [-6624, -15072, 1604], [-5536, -15072, 1874], [-5088, -14624, 1874], [2976, -14624, 1081], [3296, -14944, 1077], [3936, -14944, 990], [4192, -14816, 973], [6688, -14816, 843], [7072, -14432, 792], [7392, -14432, 677], [7840, -13984, 469], [8160, -13920, 441], [8608, -13472, 421], [10080, -13472, 417], [11744, -11808, 372], [12256, -11680, 258], [13728, -10336, 84], [14816, -9248, 0], [15136, -8672, 0], [15776, -8032, 0], [15968, -7200, 0], [15968, -5728, 12], [16352, -5344, 0]], x: 16416, y: -4832, z: 0, plan: false, radius: 120, z_tolerance: 300, timeout_seconds: 900, clear_hostiles: 1500}
  - advance_runtime: {seconds: 1}
  - assert: {qbit_set: [90080], qbit_clear: [90176]}
  - walk_to: {via: [[16416, -1696, 0], [16032, -1312, 0], [16032, 288, 0], [15648, 672, 0], [15648, 2720, 0], [15264, 3104, 0], [15264, 5088, 0], [14816, 5536, 0], [14816, 9248, 0], [17696, 12128, 0], [18080, 12128, 0], [18528, 12576, 0], [18912, 12576, 0], [19296, 12960, 0], [20448, 12960, 0], [20768, 12640, 0], [21216, 12640, 0], [21408, 12448, 0], [22176, 12448, 0], [22368, 12256, 0]], x: 23840, y: 12192, z: 0, plan: false, radius: 120, z_tolerance: 300, timeout_seconds: 600, clear_hostiles: 1500}
  - walk_to: {x: 24000, y: 13269, z: 0, z_tolerance: 900, plan: false, timeout_seconds: 60, clear_hostiles: 1500, expect: dialog}
  - select_topic: {match_label: "OK"}
  - advance_runtime: {seconds: 1.0, follow_map_move: true}
  - assert: {map: thjorgard.blv}
```

   (`PassSteps` is a map variable; if `state_dump_named_map_var` does not see it, use
   `play_lua: {source: 'if mapvar("PassSteps") ~= 1 then error("Trigger1 not crossed") end'}`.) Exit ExitTrigger1
   (24309, 13269), 3 days, to thjorgard MountainPassExit (1910, -13848, 3356). Walking back to Thronheim instead is
   the whole pass again. Save `39_mountain_pass`.

### 40_kira_pledge: Kira's rewards, her pledge, the council called

1. `travel: {map: thronheim.blv, days: 3}` (the pass back is 3 days; the boats run too), land gate as 38 step 2.
2. Kira (38 step 3's pose), `interact_actor 41`: "The Honkies have left." (78) -> "Thank you." -> "We have found the
   Mountain Pass." (81) -> "We have done as you asked.  Now will you join us?" (needs 78 and 81; 82) -> "The clans are
   united.  It is time for the war council" (needs 82 and 178; 83) -> "Tell them to meet here in two weeks." ->
   "Goodbye.". Exit 50228: 146 (12 500, 7 000 gold), 152 (12 500, 12 000), 179 (12 500, 6 000).
   Key 178 must be set before this talk: it comes from the click (53228) when 34, 38, 51, 63 and 74 are all set.
   Without it, node 16 offers only "We will be having a war council soon." and the call goes to whichever Jarl the
   last pledge was. Assert 90078, 90081, 90082, 90083, 90146, 90152, 90179. Save `40_kira_pledge`.

### 41_thorolf_bjarni: Thorolf's news and Bjarni (Sturmford)

1. Thronheim City's own Thorolf comes only on the next load (risk 6); the run goes to Sturmford, where he waits too.
   `travel: {map: sturmford.blv, days: 4}` (The Raider, Thursday) -> sturmford StartPoint0 (7511, -17581).
2. City gate (sturmford ExitTrigger0 (7608, -3312, 543), half 128 x 410): `set_pose (8090, -3312, 252) yaw pi`,
   `walk_to (7300, -3312, 400) z_tolerance 500 radius 10 plan: false expect: dialog`, "OK", follow -> sturmfordcity
   "Sturmford" (11141, 14519, 19723).
3. Thorolf Ratatoskssen, actor 44, (9994, 14090, 19723) (shown with 83 and not 84): `set_pose (10294, 14090, 19723)
   yaw pi`, `interact_actor 44` (RUDE 378): "What is it?" (needs 83, forbids 85; gives 84) -> "What?!  Why?" -> "We
   must stop this!  Tell Kira we'll find a way to stop the war!" -> "Goodbye." (he leaves by town portal). Assert 90084.
4. Bjarni Thorvaldssen, actor 56, (7311, 8192, 19822), on his throne facing west: `set_pose (7011, 8192, 19723) yaw 0`,
   `interact_actor 56` (53808, RUDE 45): "What is the meaning of this?!" (needs 84) -> "Kira has told us you have gone
   to war with Drangheim!!" -> "You must stop this war immediately!" -> "They didn't do that, we did!" -> "Sigmund
   wouldn't join the coalition unless we did." -> "It wasn't their fault.  The blame lies with us." -> "What would
   convince you to withdraw your army?" -> "We will get you that treaty!" (86) -> "Goodbye.". Assert 90086.
   Save `41_thorolf_bjarni`.

### 42_sigmund: on foot to Drangheim, Sigmund

1. North gate out (sturmfordcity ExitN (11346, 14541, 19907), half 128): `set_pose (11141, 14541, 19723) yaw 0`,
   `walk_to (11600, 14541, 19900) z_tolerance 500 radius 10 plan: false expect: dialog`, "OK", follow -> sturmford.
2. The road north to Drangheim (sturmford ExitTrigger3 (-3215, 22165, 1311), half 983 x 737, 2 days):
   `set_pose (-3397, 20609, 712) yaw pi/2`, `walk_to (-3300, 21800, 900) z_tolerance 700 radius 10 plan: false expect:
   dialog`, "OK", follow -> drangheim FTDrangheim (-15739, -21244, 2682).
3. City gate (drangheim ExitTrigger0 (12032, -4164, 1147), half 164 x 328): `set_pose (11458, -4164, 758) yaw 0`,
   `walk_to (12200, -4164, 900) z_tolerance 700 radius 10 plan: false expect: dialog`, "OK", follow -> drangheimcity
   StartPoint0 (10240, -4178, 1002). (Thorolf's copies here, actors 21/22, are gone with 84.)
4. Sigmund the Stressed, actor 20, (19005, -5530, 1476): `set_pose (19005, -5730, 1476) yaw pi/2`, `interact_actor 20`
   (53334, RUDE 87): "Why have you gone to war with Sturmford?!" (needs 84) -> "Sturmford didn't do it.  We did." ->
   "Bjarni said he needed his general.  We gave it to him." -> "What if we got him to sign a treaty?" -> "We will get
   you a treaty." (87) -> "Goodbye.". Assert 90087.
5. Out (drangheimcity ExitTrigger0 (9667, -4178, 1311), half 164 x 328): `set_pose (10240, -4178, 1002) yaw pi`,
   `walk_to (9400, -4178, 1200) z_tolerance 600 radius 10 plan: false expect: dialog`, "OK", follow -> drangheim.
   Save `42_sigmund`.

### 43_kira_treaty: Kira writes the treaty

1. `travel: {map: thronheim.blv, days: 3}`, land gate as 38 step 2. (A Thorolf copy may still show in Thronheim City
   only with 83 and not 84: not with 84.)
2. Kira, `interact_actor 41`: "We need your help." (needs 86 and 87, forbids 88) -> "We need someone to write a peace
   treaty." -> "Thank you." (88) -> "We will see you tomorrow.". Assert 90088.
3. Rest in town past 06:00: `advance_game_time: {hours: 24}`, `advance_runtime: {seconds: 3}`; the poll gives 180
   (risk 8). Assert 90180.
4. Kira: "We've returned for the treaty." (needs 180; 89) -> "Thank you.  We will be back very soon." -> "Goodbye.".
   Exit: 181, 12 000 experience, the Peace Treaty (item 10401). Assert 90089, 90181, `has_item(10401)`.
   Save `43_kira_treaty`.

### 44_signatures: Bjarni and Sigmund agree to sign in Thronheim

1. Sturmford as 41 steps 1-2 (`travel: {map: sturmford.blv, days: 4}`). Bjarni (41 step 4's pose): "We have a peace
   treaty written by Kira herself." (needs 89, forbids 90) -> "You and Sigmund will sign it together in Thronheim."
   (90) -> "We shall see you there." -> "Goodbye.".
2. Drangheim as 42 steps 1-3. Sigmund: "We have a peace treaty written by Kira the Cold." (needs 89, forbids 91) ->
   "You and Bjarni will both sign it in Thronheim." (91) -> "We shall see you there." -> "Goodbye.".
   Assert 90090, 90091 (the council set now sits in Kira's hall: actors 44-49, the treaty and book sprites).
   Save `44_signatures`. (Either Jarl first; both orders work.)

### 50_after_council: the war council and Yrsa's errand (save = the target)

1. `travel: {map: thronheim.blv, days: 3}`, land gate as 38 step 2.
2. Kira's hall door: `set_pose (-11264, 15200, 3278) yaw pi/2` (south of KiraDoor1/2, y 15493),
   `play_lua: {source: 'click(232); wait(1)'}`: the doors open and, with 90 and 91 and not 40, the cinematic
   `council_argument` (167.1 s, 27 shots) starts. Its steps: `stage` 0.95 s, `forad` 6.5 s (Forad leaves the party),
   `war` 21.2 s (keys 184, 40, 85, 93, 12 500 experience, the treaty taken), `end` 166.1 s (Markel's dead prop, Kira
   back, Yrsa's timer 36040).
3. `advance_runtime: {seconds: 170}`; assert 90040, 90184, 90085, 90093. Then `advance_runtime: {seconds: 12,
   present_dialogs: true}`: Yrsa (actor 42, RUDE 1, `openRude(1, 42)` 10 s after `end`) opens her dialogue herself.
   `assert: {dialog: {active: true}}`.
4. "Yrsa?  What do you want?" (needs 40, forbids 499) -> "What?  We're a little busy right now." -> "Alright, what do
   you need done?" -> "What?  You're interrupting us so we can go win some prize?!" -> "Alright.  We will get this
   prize for you." (499, 93) -> "Goodbye" (no full stop). Exit 50230: 185, the quest sound, she vanishes.
5. Asserts: `{qbit_set: [90093, 90185, 90499, 90040, 90184], qbit_clear: [90094]}`, the treaty (10401) gone, map
   `thronheimcity.blv`; then `console: {line: "qbit dump active"}` and
   `save_game: {name: "50 After the council", path: output/playthrough/mm9/checkpoints/50_after_council.oysav}`.
   For `51_the_thing.yml` to start from it, run.py's chain (or 51's `load_game`) has to name 50 instead of 00.

## Actors, events and exits (quick reference)

| Map | What | Index / event | Position |
| --- | --- | --- | --- |
| frosgardcity | Tryygva Ravenlocks (RUDE 180) | actor 5, click 53075, exit 50075 | (-3768, -1638, 45) |
| frosgardcity | Bodvar Elvissen (RUDE 215) | actor 25, exit 50571 | (15811, -1966, 4) |
| frosgardcity | powder barrel (cog 404) | event 232 | (4260, -11796, -289) |
| frosgardcity | dockmaster Jozka Atlia (RUDE 209) | actor 8, exit 50554 | (4751, -10650, -81) |
| frosgardcity | exit to Frosgard | ExitTrigger0 | (11983, 8146, 428), half 1311 x 128 |
| frosgard | to the city / to the fort | ExitTrigger2 / TPS1 | (1783, 3320, 1738) / (-21900, -7483, 2780) |
| yanmirsfort | Yanmir (850 HP, undamageable, dormant) | actor 71 | (-3277, -2294, 1) |
| yanmirsfort | secret bookcase / Yanmir's Key | events 210 / 212 | (2580..2703, -14746..-14418) / (5322, 2321, 605) |
| yanmirsfort | supports 0-5 | 38759-38764 (break) -> 200-205 | basement z -962, x 205 / 778, y -10039 / -9048 / -7738 |
| yanmirsfort | trap box (Yanmir) / west gate exit | TriggerYanmirTrap / TPS1 | x 123..891, y -9513..-6697 / (-8742, -2458, 182) |
| thronheimcity | Kira the Cold (RUDE 239) | actor 41, click 53228, exit 50228 | (-11182, 16865, 3278) |
| thronheimcity | Kira's hall doors (the council) | event 232 | x -11387..-11151, y 15493 |
| thronheimcity | Muiredach / Yoltzin / Comgghan | actors 1 / 2 / 3 | (13435, 6390) / (13107, 6717) / (9830, 6717) |
| thronheimcity | Thorolf (two copies) | actors 8 / 9 | 8 moved to (-7183, 12902) with 83; 9 at (13025, 1147) |
| thronheimcity | Yrsa the Troll (RUDE 1) | actor 42, exit 50230 | (-11039, 16845, 3278) |
| thronheimcity | land gate / dock gate | ExitTrigger1 / ExitTrigger0 | (14950, 82) / (2089, 15073) |
| thronheim | Moenach A'Tryht (RUDE 257) | actor 45 | (7638, 14976, 1281) |
| thronheim | Bikki (segment 52) | actor 44 | (-725, 5097, 1279) |
| thronheim | to the pass / city gate / dock gate | ExitTrigger0 / 2 / 1 | (-17306, 14679) / (1392, 6498) / (4484, 15222) |
| mountainpass | Trigger1 / Trigger0 / exit to Thjorgard | poll 600 | (-11900..-11245, 12368..14334) / (15461..17427, -5163..-4508) / (24309, 13269) |
| sturmfordcity | Bjarni Thorvaldssen (RUDE 45) / Thorolf | actors 56 / 44 | (7311, 8192, 19822) / (9994, 14090) |
| drangheimcity | Sigmund the Stressed (RUDE 87) | actor 20 | (19005, -5530, 1476) |

## Keys of this part

67 Tryygva asked; 68 Yanmir task; 69 Yanmir dead (on the task; 173 without); 70 Yanmir reported; 71 ice task;
72 ice broken; 73 ice reported; 74 Tryygva's pledge; 75 Kira asked; 76 Honkies task; 77 Honkies gone; 78 reported;
79 pass task; 80 pass found (176 without the task); 81 reported; 82 Kira's pledge; 83 war council called; 84 Thorolf's
message; 85 the council held; 86 Bjarni wants a treaty; 87 Sigmund wants one; 88 Kira writes; 180 its 06:00; 89 the
treaty given; 90/91 the Jarls agree to sign; 40, 184 the council; 93 Yrsa's errand, 185 her exit, 499 her talk;
139/145 Moenach's plan (Beldonia); 142-144 each Honky; 146, 152, 172, 175, 179, 181 the reward-once keys;
178 five clans united (34 Sven, 38 Bjarni, 51 Sigmund, 63 Markel, 74 Tryygva, 82 Kira: each Jarl checks the other
five); 1021/1022 Bodvar; 378 Frosgard dock schedule; 7001 Yanmir's key.
