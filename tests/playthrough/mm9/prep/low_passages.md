# Prep: low passages in the MM9 BLV maps (places MM9's party crouched through)

All 44 MM9 BLVs in `assets_dev/worlds/mm9/maps/` were scanned on 2026-11-08 (BLVs as installed that evening; the
Dark Passageway BLV is the 18:43 rebuild). Coordinates are native (x, y, z). "Clearance" is floor to the lowest face
over the party's body, as the movement code sees it (see Method). Scratch work, logs and scenarios:
`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/lowpass/`
(`lowpass.py` the scan, `results3/<map>.json` per map, `sc/*.yml` + `.log` the headless checks).

**Summary.** Only one low passage lies on the main story route: the Dark Passageway's crouch slot, which has been
fixed (its ceiling is now raised; the party walks through). Two more are real and still too low, both in Drangheim
Prison and both optional, with nothing behind them. Every other candidate the scan found is something else: a door,
a destructible, a railing, furniture, a ladder's posts, a cave wall sloping down, or the inside of a walled plinth.

## What blocks the party

- Party movement indoors uses `IndoorBodyDimensions{radius 37, height 160}` (`game/indoor/IndoorMovementController.h:43-47`,
  built by `IndoorPartyRuntime.cpp:125-183` and `IndoorSceneRuntime.cpp:671,794`). The sweep spheres run up to
  `height - radius` = 123 with radius 37, so anything lower than 160 over the party stops it.
  `PartyCollisionHeight = 192` (`IndoorWorldRuntime.cpp:889`) is only the party's size as actors and the AI see it
  (melee reach, line of sight, facts). It does not limit the party's own movement.
- Checked headless (`walk_to`, `plan: false`):
  - Clearances of 154 (`cal154`, Sturmford City beam) and 149 (`cal143`, Drangheim Prison shelf) stop the party.
  - 226 (the raised Dark Passageway slot, `dp_slot_now`) does not.
- There is no crouch on land (`IndoorWater.cpp:253`: Fly Down is the crouch only on a water surface).
- For comparison, MM9's player box is 66 LT standing (about 169 native) and 40 LT crouched (about 102)
  (`devdocs/mm9_rework/MM9_PLAYER_SLOPE_RE.md:74-77`, x 2.56). So 102-159 is crouch-only in MM9, and lower than about
  102 MM9 could not pass either.

## Story-critical

### Dark Passageway (`darkpassageway.blv`), main story, Chapter III, segment 05

| Place | Floor | Ceiling | Clearance | Connects | Status | Verified |
| --- | --- | --- | --- | --- | --- | --- |
| Crouch slot, x -13271..-13107, y -21627..-20972 (BLV faces 95-99, 132-136) | -696 | was -573, now -470 | was 123, now 226 | the path (Specters) to the tube room, then the tube, the ocean hall, the desert and the Wyrde. It is the only way on | **Fixed** (2026-11-08, the user's decision): `convert.py` `CROUCH_SLOT` raises the ceiling (README Deviations, "The crouch slot is walked upright") | headless: before the rebuild, `dp_slot.yml` stuck at (-13308, -21299). After the 18:43 BLV, `dp_slot_now.yml` arrives at (-12988, -21299) in 0.6 s |

The 05 prep doc's BLOCKER R1 and the `set_pose` past the slot in `05_dark_passageway.yml` are now obsolete. The
scan finds no other low spot on this map: two edge cells of 7k units² each, and the party passes beside both.

## Optional (real low passages)

### Drangheim Prison (`drangheimprison.blv`); the map is on the story route (Ivsar), these two spots are not

| Place | Floor | Ceiling | Clearance | Connects | Story | Verified |
| --- | --- | --- | --- | --- | --- | --- |
| Hatchlings' lane, x 1512..1968, y -4368..-3696 (sector 17, between InvisibleBrush1/2; ceiling PRISHCTA0T, sloping down to under 90 at its sides) | -3584 | about -3490 to -3435 | 92-149 (median 114; the README says 102-123) | the lower level (west) and the hatchlings' room (x 1944..2352, y -4488..-3336) | optional. The room holds only the six Nagate Hatchlings, which come out by themselves; no chest, no event. The README already records it: "The party cannot enter the hatchlings' room" | headless: `prison_hatch` (west to east) stuck at (1519, -3955); `prison_hatch_out` (east to west) stuck at (1962, -4000) |
| Barracks lane, x 3528..3960, y 1008..1560 (east of the barracks cots, between InvisibleBrush4/5) | -1905 | about -1813 to -1782 | 90-123 (median 112) | the Nagate barracks (NagateInBrcks0-2, x about 3340-3400) and an empty space at x 3960..4368, y 792..1944. From there the party can drop to the lower level (hatchlings at (4096, 328) and (4260, 655)) | optional, nothing there: no DAT object, chest, actor or event in the space. It looks like the Nagate's own tunnel; the lower level is reached by its ladders anyway | headless: `prison_lane2` stuck at (3527, 1250) |

Both are under MM9's own crouched box in places (90-102), so MM9's crouching party may not have fit the narrow parts
either. If the user wants them walkable, the fix would follow `CROUCH_SLOT`.

## Candidates checked and dismissed

| Map | Place | Seen as | What it is | How checked |
| --- | --- | --- | --- | --- |
| verhoffinruins (story, segment 07) | x -4608..-4400, y -4352..-4272, floor -328 | 111-143 under a bar; the start's upright reach grows from 15 M to 45 M units² past it | PrisonDoor2 (door 61, 246 high) and its bolt `DestructableBrush12` (scene destructible 648, centre (-4506, -4306, -184), 144 above the floor). Once the bolt breaks, the doorway is full height. Segment 07 already breaks the bolt (`click(38648)`) | faces and scene; `verh_s` stuck at the closed door |
| verhoffinruins | the crevasse chest (TreasureChest0, (-4347, -761, -654)), the "chest crevice" the walkthroughs crouch to | none | open to the sky (1 971 clear), under BlueWater1. Reached by swimming, no crouch | faces |
| thjoradmine (story) | x 7560..8016, y -12120..-12024, floor -1493 | 91-155 under boards | `ABMineBoards1`, destructible boards (604). The steam valve's jet breaks them (event 217). After that the passage is full height | `mine_n` stuck before; `mine_valve` (valve, then walk) arrives |
| arslegardcity | x 14880..15528, y 5472..7032, floor -1188 | 123-158 | the inside of the horse statue's walled plinth (Statue3, wall 10554 287 high at x 14991; gold rim beams at -1044). Not a way anywhere | `ars_frame` and `ars_frame_out` both stop at the plinth wall |
| drangheimcity | x 11872..13152, y 3616..5264, floor -778 | 90-160 under hanging cliff faces | open beach; the hanging faces are only near the walls | `dcity_out` walks out freely |
| chasmofthedead | x 1440..1560, y 14040..14376 | 104-158 | a rock overhang at the edge of the ramp | `chasm_up` and `chasm_down` both pass |
| sturmfordcity | x 8304..8400, y 12864..13104, floor 20193 | 154 | a beam (FLOOX94CUW) at the edge of a drop to a small floor at 19753. Used as the 154 calibration | `cal154` stuck |
| sturmfordcity | x 4992..5064, y 4224..5016, floor 20562 | 102-133 | a bench or rail slab over a 300 drop | faces |
| lindisfarnemonastery | x -744..96, y 6168..7584, floor 3236 | 102 | the railing round the gallery (Ladder3) over the room 819 below | ASCII plan, DAT objects |
| thjorgardcity | x 4608..5304, y 11448..13464, floor 451 | 112-136 | beams over the open holes of an upper walkway floor; the rooms below are reached by dropping beside them | ASCII plan |
| traininghall | (0, 0), floor 1085 | 91 | the posts of the four ChainLadders at the room's centre (the ladder climbs to 1638) | scene ladders |
| traininghall | x ±80..640, y 832..1120 | 102 | under the benches or stands (a slab with a floor 21-123 above) | faces |
| drangheimprison | x 120..672, y 0..120, floor -1884 | 133-153 | bunks or shelves (a 10-thick slab) along a wall | `cal143` stuck, a dead end |
| thjoradmine, drangheimprison, chasmofthedead, connectingtunnels, dookscastle, 1000terrors, beethoven, thronheimcity, isleofashes, lindisfarne, lichlab, wizardslab, tasaracademy, inventastorca | about 60 small pockets, 5-150k units² each | 90-159 | cave and tunnel margins where the ceiling slopes down to the floor, alcoves and niches, edges under eaves, furniture. Each sits beside open floor with no second region behind it | cluster shape (one neighbouring region, no chest within 300) and ASCII plans for the larger ones |

No candidate lower than 90 looks like an intended passage. The low clusters found are solids under raised floors,
water beds, or the undersides of slabs.

## Method

`lowpass.py` builds on `level_generation/projects/hesper_stage/check_walkability.py`. It loads each BLV with the
scene's doors counted as open. It rasters the floors on a 16-unit grid for small maps, 24 for larger ones, and 32 or
48 for the outdoor-sized regions, coarsened to stay under a 12 GB limit.

For each floor sample it measures the clearance:

- the lowest down-facing face above it, plus ceiling edges within the party's radius of 37, weighted by the
  sphere-top geometry;
- lintels: wall polygons whose bottom edge hangs above the floor. Walls are tested as polygons, so a doorway notched
  into a merged wall shows its lintel.

Samples are dropped when they lie inside solids (a floor less than 160 above) or within 22 of a wall at body height.

The samples are then classed walkable (160 or more), crouch (90-159) or low (under 90) and joined into regions by
steps of 50 at most. Drops and ladders are added as one-way and two-way links. A crouch or low cluster is reported
when it touches two regions (by step or by drop) that are not joined to each other upright, or when it has a chest
within 300. Clusters in water volumes are skipped, since the party swims there.

Candidates were then identified from their faces' textures, DAT objects (`assets_editor_dev/.../*.raw_objects.yml`),
scene doors and destructibles, and ASCII plans. The converter READMEs and map Lua decided what lies behind each one.
The real ones were confirmed headless: `load_map`, `set_pose` on one side, then `walk_to` with `plan: false` to the
other (`./build/game/openyamm --headless-run-scenario <file> --scenario-no-color`, binary of 18:29). Limits: doors
count as open, so a door or destructible across a gap can look like a lintel; this is why each candidate was checked
by hand. Rotating movers are seen in one pose. Teleports and scripted moves are not links in the region graph.
