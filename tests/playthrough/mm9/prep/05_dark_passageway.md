# Prep: segment 05, Arslegard's gate and the Dark Passageway

Research for `05_dark_passageway.yml` (Chapter III start, guide `tools/mm9_site/story/ch3_5.yml`, first section).
Starts from `checkpoints/04_death_to_arslegard.oysav` and ends on Guberland's dock. Everything below was
checked against the map scripts and scenes, and most legs were run headless with the current binary. The scratch
scenarios are in `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/71103dcf-46f6-4f99-97fd-0c82879b3192/scratchpad/prep_a/`
(`d1`…`d23`, each with its `.log`).

**One hard blocker:** a walking party cannot get from the path into the tube room. The opening is 123 units high, the
party is 160 tall, and the engine has no crouch on land (Risks, R1). Every leg after it was checked from a `set_pose`
past the opening.

Conventions: coordinates are native (x, y, z). Yaw is in radians, with -1.5708 facing -y (south). Keys are qbit
90000+K. MM9 items are engine id 10000+raw. `mapvar(...)` is the map's own var (`darkpassageway.lua`).

## 0. Arslegard: Hanndl's refusal (automatic)

- Nothing to click. On every arrival in Arslegard City, `handlers[1]` (map load) starts the 1 s `poll()` timer. At the
  third poll (about 2-3 s), `fateMan()` runs, and without key 98 it starts the cinematic `gate_fate`
  (`assets_dev/worlds/mm9/events/maps/arslegardcity.lua:122-126,155-169`). The cinematic is 71.15 s long
  (`arslegardcity.cinematics.yml:7-55`). Its steps are at `arslegardcity.lua:259-276`:
  - t=0: key 98
  - t=14: the peephole Door0 opens
  - t=71.15: 18 500 experience and `evt.MoveToMap(-18995, 1393, 1, 1536, …, "darkpassageway.blv")`, which is
    ExitTrigger2's row in `map_transitions.txt:11`
- The party lands on the Dark Passageway's only start point, `StartPoint0` (-18995, 1393, 1), facing 270° (south).
- Checked (`d1_gate`): load 04, then `advance_runtime: {seconds: 85, follow_map_move: true}`. The result is
  `darkpassageway.blv` with 90098 set. Checkpoint 04 is saved before the cinematic starts (`Cinema.gate_fate.started`
  is 0 in it), so the scene replays on load.
- Asserts: `{map: darkpassageway.blv}`, `{qbit_set: [90098]}`. Quest 90240 "Get a Writ of Fate" now shows
  (`quests_overlay.txt:176-178`).

```yaml
  - load_game: {path: output/playthrough/mm9/checkpoints/04_death_to_arslegard.oysav}
  - setup_shortcut: {kind: immortal}
  - assert: {map: arslegardcity.blv, qbit_clear: [90098]}
  - advance_runtime: {seconds: 85, follow_map_move: true}
  - assert: {map: darkpassageway.blv}
  - assert: {qbit_set: [90098]}
```

## 1. Start room: the scroll

- Prop38 is the scroll on the wall at (-18330, 5, 174). Event **216** gives item 483 (**10483 Scrap of Book**) once and
  hides the sprite. It shows no status text (`darkpassageway.lua:292-304`).
- Its text (`readable_items.txt:251`) puts the undead in capitals, in this order: SKELETON, BANSHEE, LICH, ZOMBIE,
  BANSHEE, LICH, ZOMBIE, SKELETON. That is the bridge order.
- `walk_to: {x: -18330, y: 95, z: 1}` arrives in 1.8 s. Then `click(216)`, and `has_item(10483)` is true.

## 2. The bridge lake

### Layout

The start corridor ends at the top of Ladder5 (-19041, -1356). The walk drops straight down about 1 230 onto Bridge0;
no ladder is needed and the party is immortal. A planned `walk_to: {x: -19100, y: -1550, z: -1228}` from the scroll
does this. Add `advance_runtime: {seconds: 3}` afterwards, because `walk_to` "arrives" on XY while the party is still
falling.

The decks are about 245 wide, with rails 120 high on both sides. Deck height is **-1229 when up and -1638 when down**.
The lake surface is at -1536, so a down deck is 100 under water. The pillars reach the lake bed, so a raised section is
a wall: a swimmer cannot pass under it, and nobody can climb onto it from below.

Deck centre lines (from the BLV's plank faces; bridge `k` is door id `k+1`):

| Bridge | Centre line | Statue on it (event) | Statue position | Stand here to click |
| --- | --- | --- | --- | --- |
| 0 (built up) | (-19046, -1313) to (-19046, -2867) | Skeleton, SwitchCreature0 (**201**, A) | (-19159, -1603) | (-19046, -1600) |
| 1 (built down) | (-19046, -2867) to (-18749, -3932) to (-18473, -4915) | Zombie, SwitchCreature1 (**202**, B) | (-18857, -3153) | (-18966, -3153) |
| 2 (built down) | (-18473, -4915) to (-18473, -6472) | Lich, SwitchCreature2 (**203**, C) | (-18583, -5202) | (-18473, -5202) |
| 3 (built down) | (-18473, -6472) to (-18898, -7537) to (-19292, -8520) | Banshee, SwitchCreature3 (**204**, D) | (-18463, -6716) | (-18570, -6716) |
| 4 (built up) | (-19292, -8520) to (-19292, -9779) | none | | |

- Reset statue: SwitchCreature5 (**205**), the ice terror at the top of Ladder5, (-19272, -1279, 139). It sets the
  state back to 14 (`darkpassageway.lua:84-88`). It can be clicked from the start corridor, but not after the puzzle
  is solved.
- The statues give no status text, only sounds. What a player sees is which sections rise and sink.
- **Stand points must be on the deck centre line.** In the first try the party stood on the east rail at
  (-18407, -6629). When Banshee raised bridge 3, it threw the party into the water, where it sank to -1876 and `walk_to`
  could not get it out (`d3_puzzle`).

### Script (`darkpassageway.lua:47-92`)

- The state is 5 bits; bit (4-k) is set while bridge k is down. Before the first click the state is 14
  (`puzzleState()`, `mapvar("Puzzle")` is 0 until `PuzzleSet` is 1).
- Each statue maps the state through its table, and the sections whose bit changed move. A section moves 410 at 460/s,
  under 1 s, and a party standing on it rides it.
- State 0 sets `PuzzleSolved`, plays the quest sound and opens **TeleportDoor0** (door 42: 384 at 64/s, **6 s**).
- Assert: `mapvar("PuzzleSolved") == 1`, `{mechanism: {id: 42, state: open}}` after 7 s.

### The scroll's order: A D C B D C B A (checked: `d5_scroll`, `d20_bridge_scroll`)

The order is Skeleton, Banshee, Lich, Zombie, Banshee, Lich, Zombie, Skeleton.

| Click | Party stands | State after | Then |
| --- | --- | --- | --- |
| A | Bridge0 (up), (-19046, -1600) | 22 | Bridge0 sinks with the party; Bridge1 rises and walls it in |
| D | **swim leg** (below), then Bridge3 down, (-18570, -6716) | 21 | Bridge3 rises with the party |
| C | drop onto Bridge2 (down), (-18473, -5202) | 19 | Bridge2 rises with the party |
| B | walk onto Bridge1 (up), (-18966, -3153) | 31 | every section sinks |
| D | walk to Bridge3, (-18570, -6716) | 29 | Bridge3 rises |
| C | drop to Bridge2, (-18473, -5202) | 25 | Bridge2 rises |
| B | drop to Bridge1, (-18966, -3153) | 17 | Bridge1 rises |
| A | drop to Bridge0, (-19046, -1600) | **0, solved** | all sections up; TeleportDoor0 opens |

The swim leg after A is the step the original walkthrough describes: "swim to the Banshee area, climb onto the bridge
there, and stay on the bridge from then on". Over the east rail of Bridge0, south through the lake east of Bridge1 and
Bridge2, then up onto Bridge3:

```yaml
  - walk_to: {via: [[-19046, -2750, -1638], [-18750, -2750, -1638], [-18200, -3300, -1638], [-18200, -6000, -1638],
              [-18300, -6500, -1638]], x: -18570, y: -6716, z: -1638, plan: false, timeout_seconds: 120}
  - advance_runtime: {seconds: 1}     # it climbs on with walk_to's stuck-jump and may still be in the air
```

That walk takes about 22 s. It gets over the rail and onto the deck only through `walk_to`'s stuck handler (its jump).
That worked twice but is the most fragile part of the bridge.

The other legs, with `plan: false`:

- D to C: `via [[-18473,-6400,-1638]]`, target (-18473, -5202).
- C to B: `via [[-18500,-4850,-1229],[-18749,-3932,-1229]]`, target (-18966, -3153).
- B to D: `via [[-18749,-3932,-1638],[-18500,-4850,-1638],[-18473,-6400,-1638]]`, target (-18570, -6716).
- D to C: as before.
- C to B: `via [[-18500,-4850,-1638],[-18749,-3932,-1638]]`, target (-18966, -3153).
- B to A: `via [[-19046,-2800,-1638]]`, target (-19046, -1600).

### Fallback with no swimming: C D D C B D C B A (checked: `d4_dry`)

A breadth-first search over (state, the section the party stands on) found this 9-click order. It never needs the
water: start on Bridge0, walk down onto Bridge1 and Bridge2 (both down), click Lich, then use the same legs as above.
It is not the scroll's order, though a player watching the sections could find it. Use it if the swim leg proves
flaky.

### Lake crystal to the canyon

After the solve, walk the raised sections south to the LakeTeleporter box, centre (-19292, -9974, -1065). The arrival
is LakeArrival (-19323, -10394, -1309), facing south (`darkpassageway.lua:96,367`).

```yaml
  - walk_to: {via: [[-19046,-2800,-1229],[-18749,-3932,-1229],[-18500,-4850,-1229],[-18473,-6400,-1229],
              [-18898,-7537,-1229],[-19250,-8450,-1229],[-19292,-9500,-1229],[-19292,-9974,-1100]],
              x: -19323, y: -10500, z: -1309, radius: 200, plan: false, timeout_seconds: 90, clear_hostiles: 1500}
```

Assert `mapvar("LastTeleportLakeTeleporter") == 1`.

### Teleporter pattern for `walk_to`

All five crystals are polled boxes (0.25 s polls, the box grown by 37). Walking into one gives `evt.MoveToMap` on the
same map (`darkpassageway.lua:94-102,356-372`). `walk_to` sees "map move … now on", but it keeps steering at its
current goal. If that goal was the box, the party gets stuck on the far side (the first try in `d4`).

The fix: put the last via point **on the line from the arrival through the box centre, just short of the box**, and
make the final target the arrival itself with `radius: 150-200`. The party then crosses the box on the way to the
arrival and is "arrived" as soon as it lands.

## 3. The canyon (the ice statue, the eyes, the doors)

- **Do not use the planner to reach the statue.** Its route climbs the east ledge and then steps off into the
  5 000-deep pit (`d6_canyon`, first try). The pit is a dead end in this build: the carpet cannot be boarded
  (Risks, R2).
- What works (`d6`, `d7`):
  1. Planned `walk_to: {x: -19722, y: -21315, z: -283, clear_hostiles: 1500}`, about 25 s. It goes round the west
     rim to the canyon's south shelf in front of the doors, killing 15 Specters and Apparitions on the way.
  2. Then up the east ramp with `plan: false`. From the BLV height map, the ramp is about 200 wide, x -19200 to -19100.
     It climbs from z 0 at y -21400 to 400, dips to 184, rises to 532 and comes down to the statue ledge at 31:

     ```yaml
       - walk_to: {via: [[-19500,-21450,-121],[-19150,-21350,0],[-19150,-19300,400],[-19150,-18800,184],
                   [-19150,-17900,532],[-19150,-17200,383],[-19150,-16900,225],[-19350,-16880,123]],
                   x: -19598, y: -16860, z: 31, plan: false, timeout_seconds: 120, clear_hostiles: 1500}
     ```

     At x -19300 the floor next to the ramp is the pit or -1311, so keep the ramp's x.
- **Ice statue**, SwitchCreature4 at (-19703, -16829, 164), event **206** (`darkpassageway.lua:104-144`):
  - one use only (`CanyonUsed`)
  - every 1.2 s a pair of banshee eyes wakes (`mapvar("EyesOn")` goes 2, 4, 6, 8)
  - at 8 the doors unlock and open (`CanyonOpen` = 1); CanyonDoor is doors 6-9, 164 at 51/s, **3.2 s**
  - no status text
  - each awake eye fires a 5-damage missile at the party every second while it is within 6 000. One run took 132
    shots, which the immortal party ignores.
- Before the statue, a click on the doors (event **219**) says "The door is locked."
- Back down the ramp (the same via points in reverse; the first step needed a stuck-jump onto the 123 shelf), then
  through the doors to the mountain crystal. MountainTeleporter box centre (-19783, -21995, -164); arrival
  (-18801, -22036, -326), facing east. An invisible wall, WorldObject20 at x about -19500, splits the room south of the
  doors, and the crystal carries the party past it.

  ```yaml
    - walk_to: {via: [... ramp reversed ..., [-19500,-21450,-121], [-20398,-21450,-328], [-20398,-21800,-328],
                [-19783,-21995,-164]], x: -18700, y: -22036, z: -326, radius: 150, plan: false, clear_hostiles: 1500}
  ```

- **Eyes off:** the TriggerBansheeOff0 box (-18611..-18355, -22287..-21724) is just east of the mountain *arrival*
  (`darkpassageway.lua:360`). `walk_to: {x: -18483, y: -22005, z: -328}` then gives `mapvar("EyesOff") == 1`. The guide
  places this spot "beside the next crystal"; in the script it is the arrival side, after the teleport.

## 4. Mountain room and forest

- **MountainForestDoor**, event **104**, at (-16056, -20255): a plain door that opens and closes on a click
  (`darkpassageway.lua:18`). The planned walk got stuck on it and opened it with its "click ahead" after 14 s, so
  click it on purpose instead. Walk to (-16056, -20400), `click(104)`, `wait(2)`.
- **TriggerDoor0** box (-15683..-15119, -17516..-17260): walking in unlocks and opens ForestDoor0 (door 30, auto-close
  2 s). **TriggerAttack0** box (-16169..-14633, -16461..-15437): it shuts and locks ForestDoor0, and 1.5 s later the
  Colloidal Warrior's blow removes the Adventurer and wakes the Warrior (`darkpassageway.lua:161-176,358-359`). A
  planned `walk_to: {x: -15401, y: -15949, z: -327}` crosses both (`d8`).
- Asserts: `ForestUnlocked` = 1, `ForestLocked` = 1, `AdventurerDead` = 1.
- Afterwards, clicks on ForestDoor0 (**220**) and TeleportDoor1 (**218**) say "The door is locked."
- **Colloidal Warrior**, actor **2**, at (-15534, -14377, -327), monster 9235; the **Adventurer** is actor **3** at
  (-15462, -14582). `clear_hostiles: {radius: 3000}` killed the Warrior, and the monster-killed hook set `WarriorDead`
  = 1 (`darkpassageway.lua:185-190`). The scenario kill fires the hook.
- If the Warrior dies before TriggerAttack0, the Adventurer lives (`MM9.receives`, line 170); TeleportDoor1 still
  unlocks.
- **Painting**, event **208**, on the east wall at x -14418, y -15073..-14418. A click swings it up (rotating about
  y) and opens DoubleDoor40 to the hidden room with chests **41, 42, 43** at (-13885, -14746 ± 205). It has no status
  text, and its perception hint (cog 301) goes off (`darkpassageway.lua:192-199`).
  - **Click it from at least 400 west of the wall.** From (-14580, -14789) the swinging painting hit the party
    (`bodies: reverse`) and stayed "opening" (`d10`). `PaintingOpen` is already 1, so a second click does nothing. It
    finishes once the party steps back (`d12`).
  - From (-14950, -14746) it opens, and `walk_to (-13985, -14746)` enters the hidden room (`d11`).
  - The chests are optional.
- **TeleportDoor1**, event **218**, at (-15401, -11315). After the Warrior's death the click opens it (205 at 64/s,
  3.2 s) and sets `TeleportDoor0Locked` (harmless: TeleportDoor0 stays open).
- **ForestTeleporter** box centre (-15401, -10936, -164); arrival (-15401, -9708, 2), facing north:

  ```yaml
    - walk_to: {x: -15401, y: -11450, z: -327, timeout_seconds: 90, clear_hostiles: 1500}
    - play_lua: {source: 'click(218); wait(3.5)'}
    - walk_to: {via: [[-15401, -10936, -164]], x: -15401, y: -9600, z: 2, radius: 200, plan: false}
  ```

## 5. The path, the tube room, the tube and the ocean (the lake of the guide)

- **The path** (Specters) runs from ForestArrival to its south end. A planned walk reaches (-13308, -21565, -696),
  and `walk_to: {x: -13400, y: -21299, z: -696}` stands in front of the opening (`d9`, `d13`).
- **BLOCKER R1, the crouch slot.** The only way from the path to the tube room is a slot at x -13271..-13107,
  y -21422..-21176. Its floor is -696 and its ceiling -573, so it is **123 high** (BLV faces 95-99, 134, 135). The
  party is 160 tall (`IndoorMovementController.h:46`). `walk_to` stays stuck at (-13308, -21299) with every recovery
  (`d13`).
  - MM9 crouched here; the original walkthrough says "Follow the tunnel to a point where you must crouch".
  - The engine has no crouch on land: Fly Down is MM9's crouch only on the water's surface (`IndoorWater.cpp:253`).
  - The project's own scenarios only ever reached the tube room with `set_pose` (`scenario_swim.yml`).
  - **Nothing after this point can be walked to.**
- Past the slot (checked with `set_pose: {x: -13000, y: -21299, z: -900}`, discovery only):
  - The party sinks to the tube room's bed (-1884). The surface is -983, and the bed continues as the tube's floor.
    The male sea monster (actor 40, (-10895, -20316, -1482)) dies to `clear_hostiles`.
  - `walk_to: {via: [[-10600, -21500, -1824]], x: -9585, y: -21565, z: -1884, plan: false, radius: 100,
    clear_hostiles: 2000}` swims along the tube into the shaft.
  - `advance_runtime: {seconds: 6, follow_map_move: true}`: the current carries the party down to the ShaftExit box
    (-9708..-9462, -21709..-21422, z -2683..-2458). It is moved under the ocean hall's sky and falls into the ocean
    (`mapvar("ShaftDrops") == 1`, about (-9585, -21565, -3821); `darkpassageway.lua:371`).
- **Onto the island.** The ocean surface is -3359, and the sand stands 30-60 above it (x -8100..-7200,
  y -21200..-22100). `walk_to` alone stays stuck at the north edge with stuck-jumps (`d14`, `d23`). What works is the
  swim scenario's surface jump at the sand's lowest edge (`d15`):

  ```yaml
    - walk_to: {x: -7858, y: -20989, z: -3491, plan: false, radius: 40, timeout_seconds: 60}
    - movement_segment: {input: forward, seconds: 1.0, jump: true, actor_collision: false, actor_ai: false,
        start: {map: darkpassageway.blv, x: -7858, y: -20989, z: -3491, yaw: 5.1051, pitch: 0},
        expect_stop: {map: darkpassageway.blv, x: -7739, y: -21275, z: -3324, yaw: 5.1051, pitch: 0},
        loose_tolerance: true, tolerance_xy: 450, tolerance_z: 200}
    - assert: {water: {state: dry}}
  ```

  `movement_segment` sets its start pose, a snap of a few units after the `walk_to` with radius 40. This is the only
  key-driven move in the segment.
- **Sea Monster Female**, actor **4**, at (-6164, -21811, -3671): a swimmer that keeps away from a party on land.
  `clear_hostiles: {radius: 4000, min: 1}` from the island killed her. The hook sets `CageBroken` = 1 and drops
  DB_TeleporterCage0 (door 10; assert `{mechanism: {id: 10, state: open}}` after 4 s; `darkpassageway.lua:187-189`).
- **Teleporter0**: box centre (-7537, -21770, -3226) round the crystal Prop0. The arrival is in the pillared room at
  (-7864, -18678, -817), facing north. The arrival lies north while the party lands on the north side, so walk round
  to the south of the box first:

  ```yaml
    - walk_to: {via: [[-7900, -21450, -3300], [-7900, -22000, -3325], [-7537, -22050, -3325]],
                x: -7864, y: -18678, z: -817, radius: 150, plan: false, timeout_seconds: 60}
  ```

  `mapvar("LastTeleportTeleporter0") == 1`.

## 6. The pillared room, Njam and the desert mirrors

- The planned `walk_to: {x: -3152, y: -13102, z: -306, clear_hostiles: 1500}` from the arrival takes 13.5 s and kills
  5 Terrors. On the way, **Trigger1** (-8044..-7685, -14761..-14403) runs **Njam's cameo**: actor 43, friendly, shown
  2 s later and removed 15 s later (`NjamShown` = 1). Ignore him; `clear_hostiles` does not touch him.
- The desert floor is at about -490 to -540. `walk_to` arrives on XY, and the z it reports is the dune height.
- **Gemstone**, event **215**, at (-3272, -13102, -277). Click it standing at (-3152, -13102). Each click counts in
  `Shines`. It shows no status text, only beams (`evt.Beam`).
- **Mirrors**: each click turns one 10° and shows the status **"The mirror turns (N degrees)."**
  (`darkpassageway.lua:250-269`). The accepted angles, in the order the light reaches the mirrors, are 330, 10, 340
  and 50 (`MIRRORS` targets 33, 1, 34, 5, line 208; the guide agrees).

| Mirror | Event | Position | Stand at (checked) | Target status | Clicks from new |
| --- | --- | --- | --- | --- | --- |
| Mirror0 (west of the gem) | **210** | (-6548, -13107) | (-6428, -13105) | "(330 degrees)" | 33 |
| Mirror1 | **211** | (-3113, -11141) | (-3233, -11139) | "(10 degrees)" | 1 |
| Mirror2 | **212** | (-6881, -10486) | (-6761, -10486) | "(340 degrees)" | 34 |
| Mirror3 | **213** | (-3031, -9134) | (-3151, -9134) | "(50 degrees)" | 5 |

The player loop (checked, `d16`) clicks until the status line reads the angle. That copes with a mirror already
turned by an earlier visit:

```lua
for i = 1, 36 do click(210); wait(0.2); if status():find("330 degrees") then break end end
-- 211: "%(10 degrees", 212: "340 degrees", 213: "%(50 degrees"   (escape the parenthesis: 10 and 50 are suffixes)
```

- Then walk back to (-3152, -13102) and `click(215); wait(5)`:
  - `CagesOpen` = 1
  - the six cage doors (13-18) open
  - after 3.2 s the six Terrors (actors 6-11) wake (`darkpassageway.lua:217-231`)
  - **DesertDoor0** (door 11, 307 at 64/s, 4.8 s) opens; assert `{mechanism: {id: 11, state: open}}`
- Before that, a click on DesertDoor0 (**222**) says "The door is locked."
- The cage chests 44-47 are optional.

## 7. The spike room and the desert crystal

- The planned `walk_to: {x: -4915, y: -3800, z: -328, clear_hostiles: 1500}` goes through DesertDoor0 (-5570, -5284)
  and up the trap corridor in 14 s.
- Two doors stand in the spike room's south wall at y -3628: **TrapRoomDoor1** (event 105, x -5570) on the left and
  **TrapRoomDoor2** (event 106, x -4915) on the right. "Be righteous" (the original walkthrough): take the right one.
  `click(106)` opens it.
- The spike flaps cover x -5827..-5335, y -3533..-3041. Stepping on them (the **SpikeTrigger1** box,
  -5857..-5304, -3564..-3011) tips all four into the pit for good (`darkpassageway.lua:357`). Ladder0 at
  (-5580, -3113) climbs out. Keep x above -5260; the right-hand route below leaves `SpikesOpen` at 0.
- **DesertTeleporter**: box centre (-4710, -2826, -205), round the crystal Prop35. Arrival DesertArrival
  (-5243, -1454, -754), facing north. The first straight line from (-4771, -3229) clipped past the box without firing.
  The working via lies on the line from the arrival through the box centre (`d17`):

  ```yaml
    - walk_to: {via: [[-4915, -3400, -328], [-4593, -3128, -328]], x: -5243, y: -1454, z: -754, radius: 150,
                plan: false, timeout_seconds: 60, clear_hostiles: 1500}
  ```

## 8. The exit room: four plates, the riser, the ramp

- The planned `walk_to: {x: -5243, y: 900, z: -1188, clear_hostiles: 1500}` kills 4 Specters. **ExitRoomDoor**
  (event **102**, at (-5243, 655), auto-close 7 s) needs a click: `walk_to`'s click-ahead opened it after 11 s, so
  click it on purpose.
- Plates (`darkpassageway.lua:306-331,362-365`): small polled boxes 164 square (grown by 37), all at floor -1188. Only
  the plate that is "on" reacts; a wrong plate does nothing and resets nothing. `ExitOn2` = 1 from the first load.

| Order | Plate (box) | Marked | Centre | `ExitOn0..3` after (checked) |
| --- | --- | --- | --- | --- |
| 1 | ExitTrigger2, north-east | III | (-4956, 1495) | 1010 |
| 2 | ExitTrigger0, south-west | I | (-5530, 1126) | 1100 |
| 3 | ExitTrigger1, south-east | II | (-4956, 1126) | 1001 |
| 4 | ExitTrigger3, north-west, on the riser | IIII | (-5530, 1495) | riser and ramp start (`RiserUp` = 1) |

```yaml
  - walk_to: {x: -4956, y: 1495, z: -1188, radius: 30, plan: false}
  - advance_runtime: {seconds: 0.5}
  - walk_to: {via: [[-5243, 1300, -1188]], x: -5530, y: 1126, z: -1188, radius: 30, plan: false}
  - advance_runtime: {seconds: 0.5}
  - walk_to: {x: -4956, y: 1126, z: -1188, radius: 30, plan: false}
  - advance_runtime: {seconds: 0.5}
  - walk_to: {via: [[-5243, 1300, -1188]], x: -5530, y: 1495, z: -1188, radius: 30, plan: false}
  - advance_runtime: {seconds: 11}          # riser 584 at 128/s (4.6 s, the party rides it to -599); ramp 532 at 51/s (10.4 s)
  - assert: {mechanism: {id: 23, state: open}}
  - assert: {mechanism: {id: 22, state: open}}
  - walk_to: {x: -5243, y: 1540, z: -584, plan: false, radius: 30}   # across the 123 gap onto the ramp: walked, no jump needed
  - walk_to: {x: -5243, y: 2450, z: -573, plan: false, radius: 30}   # the upper ledge
  - play_lua: {source: 'click(103); wait(2)'}                        # ExitRoomTempleDoor0/1 (auto-close 6 s)
```

- **Timing risk:** the riser has `auto_close_seconds: 15` in the scene (door 23). The ramp needs 10.4 s, so after it is
  out there are only a few seconds before the riser starts down. If the party is still on the riser when it lowers,
  the plates are spent: every `ExitOn` is 0 and `RiserUp` stays 1. Only the **Switch**, event **217** at
  (-5223, 1974, -1050), resets them to the start, with `ExitOn2` = 1.

## 9. The Specters' corridor and the Wyrde of the Unknown

- The planned `walk_to: {x: -550, y: 6513, z: -572, clear_hostiles: 1500}` from the ledge kills 11 Specters and an
  Apparition in 10 s.
- **Wyrde of the Unknown**, actor **0**, at (-348, 6513, -572): immobile, RUDE 338, the dialogue title **"Igrid"**.
  `interact_actor: {actor_index: 0}` runs event 53284, which plays her voice and opens RUDE 338
  (`darkpassageway.lua:420`). The lines (`dialogue/rude/NPC338.rude`) and what was offered (`d19`):
  1. "We've come seeking a Writ of Fate." needs key 97 and not 476 (row 6).
  2. "What is it?" (row 5)
  3. "Why the Isle of Ashes?" (row 4)
  4. "We will do this.  Thank you for your time." has two spaces and grants **476** (row 3). `match_label: "We will do
     this."` works.
  5. "Goodbye." (row 1). Then `press_action: {action: cancel_dialog}`.

  "Uhh, one more thing?" and "How do we get out of here?" exist for a second talk (rows 7, 2).
- Closing the talk runs the exit event **50284** (`darkpassageway.lua:341-351`). Without key 187 it gives keys **476**
  and **187** and 18 500 experience, plays the quest sound and sets `CageOpen` = 1. The flame damage stops at once, and
  the FlameCage (doors 27-29) sinks 328 at 38/s, **8.6 s**.
- With the Capstone (item 10396) it would also give key 188; not on this run.
- Asserts: `{qbit_set: [90098, 90476, 90187]}`, then after 9 s `{mechanism: {id: 27, state: open}}`.
- **The portal** is ExitPoint, box centre (441, 6349, -507), half 128 × 77 × 92. It leads to `guberland.blv`
  StartPoint0 (22003, 4558, -122), facing 180°, with **no prompt** (`map_transitions.txt:23`, AskPlayer 0).
  - The Wyrde stands between the party and the portal: a straight walk stays stuck on her ("nearest actor 0 at 77").
  - Go round her:

  ```yaml
    - walk_to: {via: [[-348, 6200, -573], [150, 6349, -573]], x: 441, y: 6349, z: -507, plan: false,
                timeout_seconds: 60, expect_map: guberland.blv}
    - advance_runtime: {seconds: 1, follow_map_move: true}
    - assert: {map: guberland.blv}
  ```

## End-of-segment asserts and keys

- Map `guberland.blv`; qbits **90098** (Hanndl), **90476** and **90187** (the Wyrde); not 90188 (no Capstone yet);
  `has_item(10483)` (Scrap of Book).
- Quest 90240 closes on 90187, and 90250 "Take the Capstone of Order to the Verhoffin Ruins" opens
  (`quests_overlay.txt:176-181`).
- Experience: 18 500 (Hanndl) + 18 500 (Wyrde).
- Map vars worth logging: `PuzzleSolved`, `CanyonOpen`, `EyesOff`, `WarriorDead`, `CageBroken`, `CagesOpen`,
  `RiserUp`, `CageOpen` and the `LastTeleport<name>` counters.

## Guide (`ch3_5.yml`) against the scripts, and against the original MM9

- Hanndl, the scroll, the statues' north-to-south order (Skeleton, Zombie, Lich, Banshee), the bridge order, the
  mirrors (330/10/340/50 with 33/1/34/5 clicks), the plates (NE, SW, SE, NW = III, I, II, IIII), the switch reset and
  the Wyrde's four lines all match the scripts. The original walkthrough (zimlab "Dark Passageway") gives the same
  statue order and plates 3, 1, 2, 4. It calls the Wyrde "Igrid", and so does our dialogue title.
- **"A spot beside the next crystal turns the eyes off"**: in the script, the box is on the mountain *arrival* side,
  after the teleport (`darkpassageway.lua:360`).
- **"If you fall into the pit, click the magic carpet at its bottom to ride back up"**: does not work in this build
  (R2).
- **"In the forest the door slams and locks behind you."** Yes, but ForestDoor0 also auto-closes 2 s after
  TriggerDoor0 opens it (door 30 `auto_close_seconds: 2`). A slow party could be shut out before TriggerAttack0. The
  `walk_to` crossed in time.
- **The lake leg.** The guide says only "kill the sea monster in the lower pool". The original also requires
  crouching through a low tunnel and swimming down an underwater tunnel. Our build kept the tunnel but not the crouch
  (R1).
- **"One route is enough … the Wyrde only explains"**: true for the keys. NPC338's exit event gives 476 and 187 on the
  first close of *any* talk, even without picking the four lines (`darkpassageway.lua:346-350`). That follows MM9's
  `NPC338.scr`, though the RUDE row grants 476 only on "We will do this.".
- The guide's plate step omits the riser's auto-close (R5).

## Risks / suspected bugs

- **R1, blocker: the path's crouch slot cannot be passed.** It sits at x -13271..-13107, y -21422..-21176, floor -696,
  ceiling -573 (123 high), and is the only link from the path to the tube room. MM9 needs Crouch here; the engine has
  none on land, and the party is 160 tall. Nothing past it (the tube, the ocean cage, the desert, the plates, the
  Wyrde, the exit) can be reached on foot. Options, all the user's call:
  - an engine crouch (Fly Down lowers the body on land, as `IndoorWater.cpp:253` already does on the surface)
  - a converter deviation in `level_generation/projects/mm9r_darkpassageway/convert.py` that raises that slot's
    ceiling, written up in the README's Deviations
  - a `set_pose` exception for this one spot in the playthrough's rules
- **R2 (fixed in the converter 2026-11-09: the carpet rests 30 LT lower, 67 over the floor, and a jump lands on it;
  README Deviations): the magic carpet cannot be boarded from the pit floor.** The pit floor is -6554, and the carpet's plank sits
  at -6431..-6410, 123-144 above it. The party is blocked at its edge (x -19716) whether walking or jumping (`d21`,
  `d22`). Its stuck-click then raises the carpet without the party. Every check so far set the pose onto the carpet
  (`scenario_scripted.yml`). A party that falls into the pit is soft-locked. The carpet geometry comes from
  `convert.py:139-144` (`CARPET_SHIFT_LT`, `CARPET_PLANK_LT`) and `darkpassageway.lua:146-159`. The planner's own
  route to the statue falls into the pit, so the segment **must** use the explicit east-ramp waypoints in section 3.
- **R3 (fixed 2026-11-09: the beams leave along each mirror's DAT facing, 0/180/0/180, so the accepted angles aim at the next mirror; README Deviations): the mirror beams mislead.** `beamFrom()` draws an off-target mirror's beam at `facing - count*10` degrees
  (`darkpassageway.lua:212-216`). At the accepted counts that direction does not point at the next mirror. Mirror0 at
  330 would point north-west, while Mirror1 lies to its north-east, and a beam aimed at Mirror1 would need count 6. So
  aiming by the beam, which the README claims shows where each mirror points, cannot find the solution. The segment
  relies on the status angles and the hint book's 330/10/340/50.
- **R4: the bridge swim leg is fragile.** After the scroll's first click (Skeleton), Bridge0 is a dead end, and the
  party must cross the rail into the lake and climb onto Bridge3. `walk_to` manages it only through its stuck-jump. If
  the party ends up under water away from a deck, `walk_to` (pitch 0, no swim-up) cannot surface it (`d3`). The dry
  order C D D C B D C B A avoids the water entirely. Stand points off the deck centre (on a rail) get the party thrown
  off when a section rises.
- **R5: riser auto-close.** Door 23 (ExitRiser) closes 15 s after it opens, while the ramp takes 10.4 s. Wait 11 s,
  then cross at once. If it is missed, click the Switch (217) and redo the four plates.
- **R6: the painting blocked by the party.** Clicking 208 from within the painting's swing (under about 330 from the
  wall) leaves it "opening" until the party backs off. The handler sets `PaintingOpen` first, so a second click does
  nothing (`darkpassageway.lua:194-199`). Click from x ≤ -14900.
- **R7: teleporters versus `walk_to`.** After a same-map teleport, `walk_to` keeps steering at its old goal and gets
  stuck. Always use the via-before-the-box plus target-the-arrival pattern from section 2. Also, the polls run every
  0.25 s, so a line that only clips a box corner can pass straight through it.
- **R8: getting onto the island needs `movement_segment` with jump** at (-7858, -20989), yaw 5.1051. That is a
  key-driven move, but its start pose snaps the party. `walk_to`'s stuck-jump alone never gets out of the water there.
- **R9: `walk_to` arrival ignores z.** It "arrives" over a drop (the bridge, the island, the pit) while the party is
  still falling. Follow each with `advance_runtime: {seconds: 1-3}`.
- **R10: auto-closing doors.** ForestDoor0 2 s, ExitRoomDoor 7 s, ExitRoomTempleDoor 6 s (scene `mover`
  `auto_close_seconds`). Click each right before walking through it.
- Minor: the monster-killed hook compares `context.monsterId` with actor indices 2 and 4 as well as
  `context.actorIndex` (`darkpassageway.lua:186-187`). The MM9 monster ids here are all 9xxx, so the comparison is
  dead but harmless.
- Not tested: a save and load in the middle of a puzzle; the Specters' corridor without `clear_hostiles`; the
  four-plates order after a reset by the Switch.

## Segment 05 as written

`tests/playthrough/mm9/05_dark_passageway.yml`: 132 steps, using the legs and coordinates above.

- **Bridge:** the scroll's order (A D C B D C B A) with the swim leg. The dry order was not needed.
- **BLOCKER R1:** the only `set_pose` in the dungeon, at (-13000, -21299, -900) past the slot. A `play_lua` log line
  "BLOCKER R1: …" comes right before it.
- **Tube room**, changed from section 5: the party does not reach the bed. Swimming level keeps whatever depth it has.
  So the segment swims to the tube's mouth (-10700, -21500), waits 4 s to sink below the tube's top, then swims on.
  Without the wait it hung at the lip until `walk_to`'s stuck handler let it sink.
- **Ends** on Guberland's dock. Asserts: keys 90098, 90476, 90187 set, 90188 clear, and the Scrap of Book in the pack.
  Saves `checkpoints/05_dark_passageway.oysav`.

Results (2026-11-08): `python3 tests/playthrough/mm9/run.py 05` passed 6 times. Each run took 23-25 s of wall time,
including the 71 s Hanndl cinematic in game time. With the final file, every run has the same 6 `walk_to` "stuck:"
checks, all expected:

- 4 on the swim leg: aim further, then jump, once at Bridge0's rail and once at Bridge3.
- 2 on the way back down the canyon ramp: aim further, then jump onto the 123 shelf.

73 enemies were killed by `clear_hostiles`.
