# MM9 rework: Verhoffin Ruins (`verhoffinruins.blv`)

MM9's Verhoffin Ruins (reached by a stair from the Isle of Ashes; the capstone quest's last stop) converted from its DAT
world into a native indoor map (BLV: sectors, portals, rotating and linear movers, lights, an exit volume) on the shared
dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated
review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop
models ([props project](../../props/mm9_verhoffinruins_claude/README.md)). No x4 textures yet.

Status 2026-10-30 (overnight run): geometry, 30 sectors, 76 movers, 85 lights, the exit, 94 decorations, 6 chests, 30
actors, the pentagram puzzle, the capstone and writ, the water trap, the saw, the paddle, the busts, the perception hints,
baked lighting. The shared converter is unchanged: every map-specific fix is in `convert.py`.

Update 2026-10-31 (floor holes: the shared converter's `dungeon/floors.py`,
[`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md), Thousand Terrors section): two `Cliff 2`
ledges in the crevasse (-410, under the ruin floor's overhang) and one quad of the crevasse's wading water (`Ocean3`,
-451, x 2096-2949, y -5079 to -4810) are restored; each was a hole with nothing below it in the installed BLV. 5 957
faces, 164 dropped. Walkability now: 129 steps, 28 flights, 10 unreachable regions (new: 0.25 M units² of sector 19 at
(-2104, -4344, -328), 123 over the open floor), 3 pits (new: the restored ledge at (-4952, -2152, -410), 82 units under
the overhang, where no body stands), no actor note (the Fright's overhang is gone); actors 11 and 27 now reach the party
start. Rebuilt and rebaked (`bake_slot.sh`); the three scenarios pass.

Update 2026-11-02 (**swimming**, overrides.yml `map: {swim: true}`; devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md,
the shared [`dungeon/water.py`](../mm9r_common/dungeon/water.py)): MM9's four water volumes are the scene's
`water_volumes` and the party swims, dives and drowns in them (section "Water and swimming" below). The crevasse's and
the pit's surfaces are non-solid over their beds, the flooded bed joined the ruin's room (28 rooms, 5 air components),
TreasureChest0 is opened on the bed, the trap room's water is a volume on its slide mover. Not rebaked (the map has no
bake: classic lighting, see "Baked lighting").

Update 2026-11-07 (**trap room floor**): the hall's floor (room 18) ran on under the water-trap room's walls into the
room (23), which shares no portal with the hall, so a party in the trap room south of the room's own floor was put in
the hall's sector and saw the room black (play-test at native (596, -2241)). `edit_polygons` cuts that floor at the
walls standing on it (the shared `dungeon/wall_splits.py`, selected by `TRAP_ROOM_FLOOR_POINT_LT`): `floor_check`
"18->23" 52 966 LT² -> 0, all rooms 74 112 -> 21 146, 6 148 -> 6 195 faces. Rebuilt (convert, layout, lightmap
transfer: coverage 0.994), the four scenarios pass, promoted into `assets_dev` (backup
`output/mm9_rework/promotion_verhoffin_20261107/`).

Update 2026-11-10 (**the busts fall through the ceiling**, play-test: "3 skeletons just appear"): as in MM9
(`KingKong.scr :FallThrough`), the busts wait in the two pockets over the corridor's ceiling slabs `BreakOut0/1`, standing
on them, hidden. BustTrigger0/1's ForceFall destroys the slab (a scene destructible, `motion: break, doorway: true`:
stone debris, MM9's `rockscrumblingloop.wav`); its broken event (226, 227) shows the pocket's group, hostile, and puffs
its dust (`BreakOutDust1/0`), and the monsters fall into the corridor. A slab broken by the party's weapons (CanDamage,
100 HP) drops them the same way (before, it was already breakable but opened onto nothing and released nobody). The
pockets are seeded air (the busts left `seed_exclude`) and are rooms of their own behind a horizontal portal under each
slab (shared `rooms.leaf_rectangle`: a flat leaf gets a horizontal doorway); 6 193 -> 6 282 faces, 29 -> 31 sectors. The
engine drops an idle actor whose floor face is destroyed (`IndoorWorldRuntime::destroyIndoorDestructible`). Rebuilt
(convert, layout, lightmap transfer: coverage 0.9936), the four scenarios pass (scripted: the busts start above the
slab, the slab breaks, they land on the corridor floor), promoted into `assets_dev` (backup
`output/mm9_rework/promotion_verhoffin_busts_20261110/`). The review root does not load MM9 maps at present
(`world.yml` openAirMaps: `isleofashes.blv` is not a BLV there, the root also has the old `isleofashes.odm`): the bake and
the scenarios used `assets_dev` with this map's new files.

## Build and review

```sh
python3 level_generation/projects/mm9r_verhoffinruins/convert.py --plan     # rooms only: work/rooms*.png
python3 level_generation/projects/mm9r_verhoffinruins/convert.py            # build, compile, install
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_verhoffinruins
python3 level_generation/projects/mm9r_verhoffinruins/make_scenarios.py
for s in doors_exits chests scripted swim; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_verhoffinruins/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_verhoffinruins
level_generation/projects/mm9r_verhoffinruins/reach/run_probes.sh
python3 level_generation/projects/mm9r_verhoffinruins/make_tour.py v06 [--original]   # also features_v01, lighting
./tools/run_game.sh --isolated vr --world mm9 --map verhoffinruins.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position -1229 -5967 -327 --yaw-radians 1.5708 --pitch-degrees 0 --warmup 3 --seconds 260 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_verhoffinruins/review_tour_v06.yml
./tools/run_game.sh --isolated vrorig --world mm9 --map verhoffinruins.odm \
    --assets "$PWD/output/mm9_rework/assets_original" ... --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_verhoffinruins/review_tour_v06_original.yml
python3 level_generation/projects/mm9r_verhoffinruins/work/pages.py review/v06_pages review/v06_original \
    review/v06_unbaked review/v06                                                # compare pages, 6 views each
python3 level_generation/projects/mm9r_verhoffinruins/work/brightness.py review/v06_original review/v06_unbaked review/v06
```

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). One storey at floor -128 LT; the
  crevasse's bed -256, its water -177; the electrified pit's floor -288, its water -161; the sky face 512.
- 4 339 source polygons -> **5 957 native faces**, 9 398 vertices; 164 faces with no air in front dropped (3 restored 2026-10-31, above) (the busts'
  sealed pockets over the corridor's ceiling, the undersides of floors, the water volumes).
- **29 rooms** (+ sector 0), 6 sealed air components (the ruin, the crevasse's flooded bed, 4 alcoves behind stained
  glass), no leak. The open ruin round the crevasse is one room (2 400 faces): its walls are broken, MM9 has no
  UserPortals there and no archway cut closes it (MM9 is one open ruin; see Open items).
- **32 portal faces**: 15 MM9 UserPortals, 13 from door leaves (the cells, DD14), 4 glass portals (the stained glass).
  Every portal joins two rooms; floor check 0 LT².
- **75 movers**: 69 `rotate` (MM9's own swing: double doors, the cells' bars and frames, prison doors, the falling door,
  the nozzles, the paddle), 3 `dat` (the two water-room buttons, the paddle's plate), 3 `slide` (the saw's blade and arm,
  the trap room's water); the bolt is a scene destructible (`break`, 2026-11-06; before, a `sink` mover).
- **85 lights** of MM9's 96 (+11 over the four-per-point cap light the bake only) and its 3 `DirLight`s in the bake.
- **94 decorations** (85 props.json placements, 4 spike pits, 5 pentagram flames), **6 chests** (loot from the shared MM9
  item sources), **30 actors** (5 hidden busts), 0 pads (MM9's touch triggers are polled boxes in the Lua).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `InvisibleBrush0-6`, `PaddleMesh`, `BrokenDoor1`, `TransGate*` | static world; invisible collision; the stained glass (`staind_a_glass`, brush Alpha 0.5) translucent, a glass portal into each lit alcove |
| `RotatingDoor` double doors, `CellBars*`+`CellDoor*`, `PrisonDoor*`, `Door5`, `FallingDoor`, `TortureChamberDoor*` | `rotate` movers, one per leaf, MM9 pivot, angle, speed |
| `WaterNozzle0-3`, `Paddle` | `rotate`; the paddle pushes bodies (`bodies: push`) |
| `WaterRoomButton1/2`, `PaddlePlate`, `SawBladeArm1` + `SawBlade1` | `dat` / `slide` (the blade rides the arm, MM9's AttachTo) |
| `DestructableBrush12` | the bolt on PrisonDoor2: scene destructible 648 (50 hp, cog 20648); weapons break it, a click on it or its hint deals the killing blow (event 38648) |
| `WaterTrap` (BlueWater, DrainWater.scr) | its top face as a `slide` mover: lowered under the floor, rises to -30 LT (16 s, MM9's 10 LT/s), untouchable, liquid (see-through 0.37), two-sided; with `swim` also a water volume whose top follows the mover (`mover_door_id` 76) |
| `BlueWater0/1`, `WorldObject0` (one Ocean3 quad over the map) | the volumes' top faces with `Ocean3.spr`: with `swim` non-solid surfaces at -177 LT over the bed and two water volumes; without it a **wading floor** at -176 LT |
| `WaterSurface`, `ElectricWater1`, `ElectricDamager1`, `Spikes5-8` | the pit's water125 surface at -161 LT (with `swim` non-solid and see-through 0.25 over a water volume, else a wading floor), an invisible ledge out (`PIT_STEP`), 5 electric damage a second while in it, the spike pits on the floor under the water |
| `skymarker` | `sky04` stretched (0.2 texel/LT), the bake's sky emitter |
| `Light` (96), `DirLight` (3) | BLV point lights; bake-only lights; profile `dirlights: true` |
| `Prop`, `Torch`, `TreasureChest` | 3D decorations (props project); the beds in MM9's "onside" pose; tipped chairs, tables, a cabinet, a scroll |
| `Fire` `PentaFire1-5` | five coloured flame decorations (cogs 310-314), hidden until the puzzle starts |
| 6 monster classes | 30 placed actors, MM9's bodies (ABC extents x Scale x 2.56: zombie 38/179, skeletons 38/189, banshees 51/154) |
| `StartPoint0`, `ExitTrigger0` | start 0 on the stair's foot (facing 103°); MM9 positioned exit to the Isle of Ashes (VRStartPoint) |
| `PerceptionBrush0/2/3`, `PerceptionLightWaterTrap` | 15 untouchable translucent faces (Perception/Perception2.spr, Alpha 0.5, two-sided), cogs 320-323, shown at Perception 9 |
| `AIRail`, `AITrk`, `AIBarrier*`, `saw blade ai barrier`, `saw damage`, `TriggerTimer1`, `SwingPaddle`, `Marker*`, `SkyBox0`, `TOD_Sky0`, `OutsideDef0`, `AmbientSound` | not built; the Lua does their jobs where they had one |

## Scripted objects (`worlds/mm9/events/maps/verhoffinruins.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Pentagram** `PentagramPuzzle.scr` ("TortureChamberDoor0 TortureChamberDoor1"), `PentaCenter`, `TriggerPentagram1-5`, `TriggerPuzzleOn/Off` | the torture chamber's door is locked; the centre lights the five flames; each point latches once with `doorlatch01.wav`; a wrong one resets (OnFailure); the fifth unlocks both leaves and opens TortureChamberDoor1 only (UnlockDoor's "Trigger NULL, open"). The flames' colours (red, yellow, blue, green, orange) are the order, as letter 485 says |
| **Door shooters** `DoorShooter0/1`, the leaves' OpenTriggers | opening TortureChamberDoor0 turns them on, TortureChamberDoor1 off; on, they fire a FireBolt (20) every 4 s at a party in the chamber |
| **Capstone** `Capstone.scr`, `placeCapstone.scr` (HeadsmanBlock1) | with key 98 and item 396 a click on the block places it: key 99, 154 000 experience, the capstone shows, the writ appears, the item is taken |
| **Writ** `Writ.scr` | a world item (`dungeon/pickups.py`, item 392) shown with key 99 until key 100; its pickup gives 162 000 experience and key 100 |
| **Fake book** `fakebook.scr` | keys 281 and 290, item 242; gone (also on later loads with 281 or 282) |
| **Key** `givetake.scr` "559", **Door5** `DoorLock.scr` "559 1" | the key goes to the packs; with it Door5 opens and the key is taken |
| **Diary scraps** `BookLetter.scr` "484 Letter", "485 Letter" | `evt.SimpleMessage` with MM9's text |
| **Water trap** `DrainWater.scr` (WaterTrap), nozzles' OpenTriggers, `TriggerWaterLock/Unlock`, `WaterRoomButton2`, `Trigger0` | a click on a nozzle floods the room: DD5 shuts, the water rises, the drain button's hint shows to a perceptive party; 10 drowning damage every 2 s after 8 s; the drain button lowers it and frees the door and nozzles. `WaterRoomButton1` is a dummy (Locked, nothing unlocks it) |
| **Saw** `SawBladeTrigger1`, `saw damage trigger 1/2`, `TriggerTimer1` | blade and arm slide across the corridor and back (2 s), 40 to a party in the blade's path, re-armed after 5 s |
| **Paddle** `PaddleTrigger`, `Paddle`/`SwingPaddle`/`PaddlePlate` | the paddle sweeps over its plate toward the pit and back, pushing what stands in its way; re-armed |
| **Busts** `KingKong.scr` "BreakOut0/1" ForceFall on `BustTrigger0/1` | the slab (`BreakOut0/1`, a scene destructible with a horizontal doorway) is destroyed; the pocket's monsters, waiting on it hidden, are shown, hostile, and fall into the corridor; the slab's dust puffs (`BreakOutDust1/0`). Weapons breaking a slab do the same |
| **Bolt** `DestructableBrush12` (Damage/DeathTrigger) | its damage (event 209) hides PerceptionBrush0 (`BoltHintOff`); its death (event 206: weapons, or a click) sets `BoltBroken`, which unlocks PrisonDoor2 |
| **Falling door** `FallingDoor` (OpenTrigger2 locks it) | falls flat once on a click |
| **PerceptionBrushes** | shown at Perception 9 (`evt.CheckSkill`), checked on load and every 3 s; the hint boxes round the bolt and the drain button take their clicks |
| Locked doors MM9 never opens (`DoubleDoorL/R10`, `TortureChamberDoor6/7`) | "The door is locked." |

**Unmatched** (not carried, with reasons): `PerceptionLight0-3` (red point lights at the nozzles; no switchable runtime
lights), the pentagram fires' coloured lights (same), `BreakOutDust0/1` (dust puffs; no particle object), MM9's
`AmbientSound` (26, a later pass), `PropAnim.scr` on the pews
(their ABC has no `onside` animation: MM9 shows them upright too).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_verhoffinruins.yml`: 64 samples,
**direct 0.7, bounce 6, ambient 0.6, sky_scale 0.4** (lightmap-matched), `dirlights: true` (MM9's 3 DirLights),
`max_lighting: 1` (MM9 clips at x1), 11 bake-only lights, the sky face (`sky04`) an emitter coloured (1.0, 0.97, 0.88)
(MM9's lightmaps over the open core are warm, B/R 0.90; the first blue sky made it blue). Sector ambient `map.ambient` 20.
`stale_bakes.py --check` does not list the map.

## Brightness

**Installed: lightmap-matched, validated against a real MM9 screenshot.** The user's screenshot of MM9 itself at the
spawn corridor (`review/mm9_real_spawn.png`; side by side with ours in `review/spawn_real_vs_v09.jpg`), central crop:
**real MM9 luma 62, RGB (68, 63, 45); ours (v09) luma 57, RGB (64, 57, 41)**: the same brightness and the same warm
yellow-green. The "MM9 original" capture (the old import in our outdoor renderer) is 94 there and greyer: it is **not a
valid brightness reference** for this map (it draws the textures nearly unlit; a bake clipped flat at x1, ambient 3.0,
matched it x0.99-1.01 in 50 of 59 views, `review/v06`).

Lightmap texel luminance ours/MM9's DAT lightmaps per zone (`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`):
torture chamber 1.22, south cells 1.06, ruin core 1.67, east halls 1.00, north halls 1.11, west wing 1.22; hue (B/R, G/R)
within 0.03 of MM9 in every zone. Screen means against the capture (59 views, `review/brightness_v09.txt`): capture
74.5, unbaked 62.7, **baked 31.4** (x0.42): the halls and stairs 40-55, the cells 14-20 (MM9's lightmaps make them the
darkest zone; only the spawn corridor is checked against real MM9, the cells are not).

**Documented alternative (capture-matched, `review/v08`):** direct 0.65, ambient 2.1, sky_scale 0.5: mean 62.9 (x0.84 of
the capture), no view under x0.66, but the neutral ambient dilutes the hue (B/R 0.96-0.99) and flattens the zones; at the
spawn it measures luma 89, RGB (97, 88, 72), too bright and too grey against the real MM9 shot. Switch by editing the
profile and `bake_slot.sh python3 .../dungeon/lighting.py level_generation/projects/mm9r_verhoffinruins --recompose`.

Sheets: `review/v09_compare.jpg` (61 views, capture | native baked), `review/lighting_v09_compare.jpg` and
`review/v09_pages_p01-p11.jpg` (capture | unbaked | baked), `review/v08_*` (the capture-matched alternative),
`review/features_v01/` (the pentagram's flames lit by standing on the centre, the sconces' flame cards from the side and
the front, the stained glass, the pit). Views r16_a/b stand on the crevasse's flooded bed under the wading surface
(the tour's room picker) and are left out of the numbers.

## Checks

- Scenarios (all pass on the final build, real clicks for doors, the key, the bolt, the nozzle, the drain button, the
  chests, the book, the block and the writ): `scenario_doors_exits.yml` (the stair raises ExitTrigger0; DoubleDoor1 stops the
  party, opens on a click and is walked through; DoubleDoor10 stays shut; Door5 stays locked, the key is taken, Door5
  opens; PrisonDoor2 stays bolted after 49 damage on the bolt (its hint gone) until the bolt is clicked; 2026-11-06), `scenario_chests.yml` (the 6 chests; TreasureChest0 on the
  crevasse's bed, under the water (with swimming; by its event before); a Fright standing at TreasureChest4 is killed first), `scenario_scripted.yml` (the locked
  torture door; the pentagram's wrong order and right order; the shooters fire; the water trap floods, drowns, drains;
  saw, paddle, pit damage; BustTrigger0; the fake book; the capstone and the writ).
- Walkability (`work/walkability.json`, before the floor fix of 2026-10-31: the update above has the new counts): 132 steps, 28 flights, 29 mover notes, 1 actor note. The steps: the crevasse's
  rim (123: wading water -451 to floor -328, the NW ramp is the way out; MM9 swims), the pit's rim (82, the ledge),
  door sills and frames (41-93), the start's spiral stair (the flights: 41-123 rises over 16-80 widths; the party climbs
  it, `scenario_doors_exits.yml` walks up 215 units into the exit). Its unreachable entries: one with actors (next
  section); the pit (monsters cannot leave: real, a trap); and floors "above the open floor", which the audit measures
  from the crevasse's water, the largest floor (not cut off from the party).
- Faces: `work/mixed_faces.json` lists the edge noise of a voxel-thin wall's samples; the visible holes it caused
  (cell ceilings, a 2x2 cell floor, the east room's north wall) are fixed by convert.py's splits (below).

## Can the monsters reach the party

The audit reports sector 4 (the room behind DD14, Terror0 and Terror4) as cut off from the party start. Probes
(`reach/make_probes.py`, `reach/run_probes.sh`, `report_state` every 2 s) on the final map: with DD14 open and the party
in sight in the corridor (`room4_seen`) Terror0 comes to the doorway and targets the party; with the party out of sight
(`room4_hidden`) it walks out of the room to (2468, -5796) and on along the corridor. **False.** The spawned controls
(`control_corridor`, `control_near`) stay idle: `spawn_actor` gives row 9164 no hostility toward the party, so the placed
actor is the evidence. The other 29 actors are in rooms the audit joins to the start.

## Deviations from MM9 and why

- **Water** (see "Water and swimming"): MM9's volumes, swum in. Kept from the wading build: **the pit's invisible
  ledge** (`PIT_STEP`, -145 LT, 38 over the pit's water): the pit's rim (its wooden border, -128 LT) stands 82 over the
  water and the surface jump reaches 59, so without it the party could not leave the pit (the audit: "rims beyond the
  surface jump: [82]"); MM9's own way out of the pit was not found. The trap room's drowning is the engine's breath
  (15 s, then 1/6 of maximum HP every 2 s), no longer the script's fixed 10 every 2 s after 8 s.
- **Water shader (2026-10-31, [shared helper](../mm9r_common/liquids.py))**: the trap room's rising water (Water115,
  `water115_mm9`) and the electrified pit's surface (water125's first frame, `water125_frame_mm9`) draw with the liquid
  shader, opaque (the trap water was 0.7); the crevasse's Ocean3 was liquid before. All `depth: shallow`; the wading
  floors, the ledge and the drowning script are unchanged. Sheet: `review/liquid/before_after_p1.jpg`.
- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): the trap room's rising water (`WaterTrap`, SurfaceAlpha 0.9 x Water115.spr
  0.42 = 0.37, `lqw115o37`; matched to its DAT volume across its 415-unit rise) is see-through. The pit's water125
  wading floor and the Ocean3 brush (0.9) stay opaque: no floor of their rooms lies under them. Note: `TRAP_OPACITY`
  in convert.py says 0.7, the DAT has 0.9. Sheet `review/liquid/see_through.jpg` (the trap water is under the floor
  until the trap fires, so it shows the pit).
- **Trap water** rises to -30 LT, under the ceiling (MM9's volume rises into it); drowning is a fixed 10 every 2 s.
- **The busts are hidden in their pockets** until their slab breaks (MM9 draws them; the pockets are sealed, so no player
  sees the difference).
- **The bolt also breaks on a click** (a killing blow; MM9: weapon damage only, which works too since 2026-11-06).
- **Doors without a doorway portal**: DD9, PrisonDoor1/4, Cell8 stand in broken walls (both sides are one room); DD10 and
  TortureChamberDoor6 have rock behind them; TortureChamberDoor7 the chamber's own air.
- **Stained glass** draws at MM9's brush Alpha 0.5: the lit alcoves show through it (the old import draws it opaque).
- **Sky**: `sky04` instead of MM9's SeaSky box and night starfield (the capture shows a navy void).
- **Brightness** follows MM9's lightmaps (validated against a real MM9 screenshot), not the old-import capture
  (Brightness; the capture-matched alternative is documented there).
- **AI**: actors stand at their DAT positions (no AIRail patrols).

## Water and swimming

With `map: {swim: true}` (2026-11-02) the shared build writes the scene's `water_volumes` from the DAT
(`dungeon/water.py`) and convert.py sets the trap's top. Volumes (native units; MM9 tint (0, 0.5, 0.7), no fog, no
current; the engine's point test: inside a piece's polygon and bottom <= z < top):

| Volume | Pieces | Top | Bottom | Notes |
| --- | --- | --- | --- | --- |
| `BlueWater0` (the crevasse, east) | 6 | -453.1 | -819.2 | bed -655 (ledges to -489), the east ramp ends on a ledge 82 under the floor |
| `BlueWater1` (the crevasse, west) | 12 | -453.1 | -819.2 | bed -655; TreasureChest0 on it at (-4347, -761, -654); the NW ramp (-3727 to -4383 at y about -1600) climbs from the bed to -348 |
| `ElectricWater1` (the pit) | 1 | -409.6 | -737.3 | pit floor -737 (the spikes); out by the PIT_STEP ledge |
| `WaterTrap` (the trap room) | 2 | -76.8 | -983.0 | `mover_door_id` 76: the top is the BLV's stored (full, closed) pose of the trap face; the door's open (lowered) pose puts it at MM9's -491.5, under the room's floor (-328) |

- **Surfaces**: the crevasse's Ocean3 quads (built at the volume top) and the pit's WaterSurface are non-solid
  (`TRIGGER_nonsolid`, untouchable); the liquid shader draws them from both sides. The pit's water125 is see-through
  (0.25: `lqw125o25`, new in liquids.py's SEE_THROUGH); the crevasse's Ocean3 stays opaque: liquids.py's bed test
  samples each surface quad's centre and corners, and most of MM9's brush rectangles run on over rock under the ruin's
  floor slab (0.9 would hardly differ).
- **Rooms**: the flooded bed is no longer a sealed air component: 6 -> 5 components, 29 -> 28 rooms, 30 -> 29 sectors.
  `water_room_mismatches` 0 (the air just under each surface is the room over it: the party crosses no room without a
  portal), `water_bed_holes` 0 (no open water without a bed inside the volume). Faces without air dropped 164 -> 154:
  the pit's bed and the wood beams' undersides at its waterline are kept now.
- **Floor-hole check: 1** (explained): a 768 LT² sliver of the pit's Cliff ledge at the waterline (-160 LT,
  (-6436, -3991, -410)) under the wooden border's beam, whose underside lies on it: no air over it, correctly dropped.
- **Audit** (`dungeon/audit.py`, water rule: floors in a volume or beside it at most 59 over the top are one swim set;
  the party climbs 50): steps 129 -> 88 (the wading waterline edges are gone), flights 28, unreachable 10 -> 4,
  pits 3 (the crevasse's bed 8.54 M units² and the two -410 ledges in the crevasse, all marked `water`: the party
  swims out by the NW ramp; walking monsters stay on the bed, as in MM9), mover 29, actor 0. Each volume: the party
  gets out. Rims out of the surface jump's reach: the pit's 82 (hence the ledge), the crevasse's 105-246.
- **Scenarios**: `scenario_swim.yml` (make_scenarios.py) needs the engine's swimming (`water` asserts, `fly_up` in
  `movement_segment`): off the rim at (-4347, -560, -328) southward into the water, down to the bed, TreasureChest0
  from (-4355, -871, -654), breath (10 s: 0.25-0.42 left, no tick; 16 s: a tick; 20 s: 3 ticks, health down), Fly Up to
  the surface (feet -586.5: the eye point 1 over -453.1), a save under water loads with full breath, out by the NW
  ramp from the surface over (-3700, -1600) walking west, the trap room flooded for 30 s (breath gone) and drained.
  `scenario_chests.yml` opens TreasureChest0 from its bed pose (no event); `scenario_scripted.yml` drops the script's
  `Drowned` check with swimming. All four pass on the swimming engine (2026-11-02); the measured water states: the
  dive ends on the bed (-655) at 0.83 breath, 10 s under 0.33, a tick at 16 s, 3 at 20 s, the surface pose at -586.5,
  breath full after loading a save made on the bed (the state is worked out on load), the flooded
  trap room 2 ticks after 30 s. Rebuild: `convert.py`, `make_scenarios.py`, then the scenarios (Build and review).
  `scenario_swim_monsters.yml` (hand-written): a Jellyspore (MM9 swimmer, Fly `YS`) spawned in BlueWater1 swims to the
  surface under the party on the rim and stays in its water (centre 1 under the surface); a Bandit spawned over the
  water sinks and walks the bed under the party; a Sea Monster (Fly `S`) spawned in the open east crevasse swims to a
  party at the surface, held 1 under it. (Spawned in the west channel at (-4347, -1100) the Sea Monster's 192 radius
  barely lets it move.)

## Map-local converter changes (`convert.py`, the shared package unchanged)

- `looser_separating_plane` (patched over `rooms.separating_plane` from `edit_polygons`): the original's answer first;
  else a split between one room's samples and the rest's percentiles, purity counted outside a 20 LT band; else a plane
  between room medians parting a 2x2 grid of cells. The cells' walls are a voxel thin and the ceilings and floors run
  over rows of cells: without it three cells shared one ceiling (black ceilings in two of them) and four cells one floor.
- `presplit_assign_faces` (patched over `build.assign_faces`): a polygon whose second room holds 4-15 % of its samples
  is split before the shared pass, which keeps such a polygon whole (the east room's north wall ran on from the NE hall).
- `trap_top` (in `extra_seeds`, wrapping `source.polygons`): the water trap volume as its top face only.

## Open items

- MM9 models for the Zombie, Skeleton Warrior/Master and Banshee families draw stand-ins (another session builds them).
- The open ruin is one 2 400-face room; archway cuts round the crevasse could split it (not needed for correctness).
- Ambient sounds; switchable lights for the perception and pentagram lights; swimming and diving (the crevasse chest).
- A density and pack pass (PLAN.md: later); x4 textures last.

## Not checked

- The water trap's rising surface and the paddle's swing seen in a running game (the scenarios prove the states,
  timing and damage; no desktop capture of the water mid-rise or the paddle pushing a party into the pit).
- The bake's look on the moving water face (stored at its full height; it should carry the room's light).
- Arrival from the Isle of Ashes by walking its ExitTrigger (the transition row's arrival is on the start's floor).
- Perception hints shown at Perception 9 in a desktop capture (the scenario path hides them at Perception 0).
- Monster combat AI beyond the reach probes; the Banshee family as fliers.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:58:49 (convert.py from the current shared converter, end 14:59:38): 0 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV is byte-identical to before (no face of this map met the rule); its baked lighting was removed for the scene file's water change of the same day, not for this rebuild; it has 5957 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
