# MM9 rework: Dark Passageway (`darkpassageway.blv`)

MM9's Dark Passageway (the way from Arslegard to Guberland; Specters, Terrors, sea monsters, a Colloidal Warrior and the
Wyrde of the Unknown) converted from its DAT world into a native indoor map (BLV: sectors, portals, linear and rotating
movers, ladders, lights, exit volumes) on the shared dungeon converter
([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into the isolated review root
`output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows and the prop models
([props project](../../props/mm9_darkpassageway_claude/README.md)). Status 2026-10-31 (overnight run): geometry, 30
sectors, every mover, every scripted object as native Lua, three ladders, the water swum (Water), 113
decorations, 7 chests, 44 actors, baked lighting matched to MM9's DAT lightmaps plus a floor standing in for MM9's player light. No engine change, no shared converter
change.

The passage is a chain of small worlds under a starred night sky, joined by teleporters (MM9 `Teleporter` objects):
the start room (from Arslegard, StartPoint) with a scroll; the **bridge lake** (five bridge sections over deep water,
raised and lowered by four ice statues standing on them: MM9's bridge puzzle, solved by the order ADCBDCBA; the terror
statue at the top of the ladder resets it) and its locked TeleportDoor0; the **canyon** (a 2 000 LT deep pit under
rock plateaus, the magic carpet at its bottom, the ice skeleton-warrior statue on a ledge whose call wakes the stone
banshees' eyes and opens the canyon doors); the mountain room and the **forest** (TriggerDoor0 lets the party in,
TriggerAttack0 slams the door behind it while the Colloidal Warrior strikes down an adventurer; its death unlocks
TeleportDoor1; the painting hides a room with three chests); a winding path down to the flooded **tube room**, whose
water runs down into the **ocean hall** (an island with a caged teleporter, broken when the female sea monster dies);
the pillared room and the **desert** under the night sky (four mirrors turned in 10 degree steps carry the gemstone's
light round the desert; with all four aimed it releases the six caged Terrors and opens DesertDoor0); the spike-trap
corridor, the exit room (four corner triggers in order raise a riser and run out a ramp), a curved canyon corridor and
the Wyrde of the Unknown's room, where talking to her opens the flame cage round the exit to Guberland.

## Build and review

```sh
python3 level_generation/projects/mm9r_darkpassageway/analyse.py           # DAT survey: work/analysis.json, dat_objects.json
python3 level_generation/projects/mm9r_darkpassageway/convert.py --plan    # rooms only (60 s)
python3 level_generation/projects/mm9r_darkpassageway/convert.py           # build, compile, install (2 min)
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_common/dungeon/lighting.py \
    level_generation/projects/mm9r_darkpassageway                          # bake (64 samples)
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_darkpassageway   # zones
python3 level_generation/projects/mm9r_darkpassageway/make_scenarios.py
bash level_generation/projects/mm9r_darkpassageway/work/run_scenarios.sh   # doors_exits chests scripted
./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_darkpassageway/work/reach_monsters.yml --scenario-no-color
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_darkpassageway
python3 level_generation/projects/mm9r_darkpassageway/make_tour.py v02 [--original]   # 47 eye-level views
bash level_generation/projects/mm9r_darkpassageway/work/run_tours.sh v02 [--set video.lightmaps=false]   # SDL_AUDIODRIVER=dummy
bash level_generation/projects/mm9r_darkpassageway/work/run_tour_original.sh v02     # view_distance=unlimited
python3 level_generation/projects/mm9r_darkpassageway/tools/pages.py review/v02_pages review/v02_original review/v02
```

## Files

- `overrides.yml`: every DAT world model's rule, 18 doorways, 4 archway cuts, `seeds`/`seed_exclude`, the sky and
  water textures, glass, `thin_walls`, `model_lighting`; `convert.py`: the population, the water surfaces, the carpet's
  column and plank, the exit's gate slab, the statue copies, the perception hints, the ladders, the light colours, every
  script (a `dungeon.Hooks` subclass); `analyse.py`, `make_scenarios.py`, `make_tour.py`, `hue_zones.py`, `tools/`
  (`leak.py`, `route.py` the party's route graph, `section.py`/`heights.py` side and height views of the DAT,
  `floors.py`/`fastfloor.py`, `blvfaces.py`, `pages.py`), `scenario_*.yml`, `review_tour_*.yml`, `review/`.
- `props.json`: 109 placements from the props project; `work/`: `build_report.json`, `doors.json`, `lights.json`,
  `content.json`, `walkability.json`, `rooms*.png`, `runtime/`, `reach_monsters.yml`, scenario logs, `run_*.sh`,
  `sky/` (MM9's DARKP sky box), `sec_*.png`/`h_*.png` (DAT sections used to plan the canyon and the ocean).

## Numbers

| | |
| --- | --- |
| Frame | `native = (LT.x, LT.z, LT.y) x 2.56`, no offset (the old map's frame) |
| Geometry | 3 489 source polygons -> 2 867 merged (+ 240 water tiles and the carpet's plank) -> **4 424 native faces**, 7 408 vertices; 187 faces with no air in front dropped (backs of the dunes and rocks against the outside, the invisible walls' outer sides, water tiles half in a wall: below) |
| Air | sealed (`leaked_to_border` 0) once ExitReset (a relay box in the rock), the six Terrors MM9 parks over the roofs at y 64 and the two Specters inside the ramp's slab are out of the seeds; 8 seeded components: the passage's worlds are joined only by teleporters (MM9's design), plus the painting's hidden room |
| Rooms | **29 + sector 0** (27 with swimming since 2026-11-06: the tube room, the tube, the shaft and the ocean hall are one room; Water): the start room and the lake, the lake's far landing, the canyon corridor, the canyon, the mountain corridor and room, the forest, the hidden room, the forest's teleporter, the path, the tube room, the ocean hall, the pillared room and its shaft, the desert, six cages, the trap corridor, the spike room, the desert arrival, the exit room, the curved corridor, the Wyrde's room; faces per sector median 40, largest 1 180 (the desert's dunes) |
| Portals | **22 faces**: 18 doorways from door leaves (VisBSP has no UserPortals here), 4 archway cuts (`canyon_corridor`, `pillar_passage`, `wyrde_room`, `path_tube`); every portal joins two rooms; floor check 0 LT² |
| Movers | **40 mechanisms**: 5 bridges, 4 spike flaps, the painting, the hidden double door, 6 cage doors, the carpet, the teleporter cage, the riser, ramp and switch, the flame cage (its invisible slab and glass parts), 14 plain doors with their invisible parts |
| Lights | 120 `Light` -> **76 BLV lights** (colour x BrightScale x zone gain); 44 over the four-per-point cap bake only; 11 `DirLight`s as bake spots; at most 4 per floor point (`content.json`) |
| Decorations | **117**: 109 from the props project (4 claw torches, 7 crystals, 51 bushes, 25 trees, the rune stone, logs, barrel, scroll, 6 ice statuettes, 4 stone banshees, 7 chests, the spike pit), the 4 bridge statues' second poses and the 4 desert mirrors (`mm9_mirror`, `mirrors.json`) |
| Actors | **44**: Specter 16, Apparition 3, Desert / Reptilian / Amphibious Terror 18, Terror 1, Colloidal Warrior 1, Sea Monster 2 (at MM9's body sizes), the Wyrde, the adventurer, Njam (hidden) |
| Ladders | **3**: Ladder5, Ladder1, Ladder0 |
| Translucent faces | 71 since the liquid shader: the flame cage (60), perception hints (10), the ladder rungs; the 244 water tiles are liquid faces (Water) |
| Exits | `ExitPoint` (object 274) to Guberland StartPoint0, gated by the flame cage; arrival from Arslegard (its ExitTrigger2) on StartPoint (facing south into the start room) |

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `Terrain0/2/3/4/6/7` (the desert's dunes, the ocean's island, rocks) | static world; `VisBSP` holds no UserPortals here: every doorway comes from its door's leaves |
| `skymarker` faces (121) | drawn with the map's own starfield texture (`STARB78A3F`): MM9's DARKP sky box is a dark starred night sky (`work/sky/sheet.png`); no indoor sky, no sky emitter in the bake (MM9's moonlight is its DirLights) |
| `Door` (ExitRoomDoor, TrapRoomDoor1/2, MountainForestDoor, DesertRoomDoor1, ExitRoomTempleDoor0/1, TeleportDoor0/1, CanyonDoorL0/R0, ForestDoor0, DesertDoor0, the cage doors Door1-6, the hidden room's DoubleDoorL40/R40) | `dat` movers (MM9's MoveDir, MoveDist, Speed) with doorway portals from their leaves; the Locked ones run the map's handler (a click says it is locked until their script unlocks them) |
| `Door0` (MoveDist 0, Locked, nothing unlocks it) | static: the lid at the bottom of the pillared room's shaft |
| `FlameCage` (Door, TorchFlame2.spr), `FlameDamage` (PoisonGas) | the cage a mover drawn translucent at 0.6 with an invisible slab ring round ExitPoint riding it (the exit's gate); FlameDamage a polled fire box (10 a second) until the cage opens |
| `ExitRiser`, `ExitRamp` (Door) | movers driven by the exit room's corner triggers |
| `Switch` (RotatingDoor-like, StartOpen) | a rotating lever; a click turns it and sends ExitReset |
| `SpikeDoor1-4` (RotatingDoor, 85 about x) | rotating trap flaps (`bodies: push`, `carry`) opened by SpikeTrigger1; the pit's Ladder0 out |
| `Painting` (RotatingDoor, 90 about y) | a rotating mover; its click opens DoubleDoor40 (MM9's OpenTriggers) |
| `Bridge0-4` (WorldObject, DarkP_RaisingBridge.scr) | linear movers, 160 LT between their markers at 180 LT/s (`slide`) |
| `Mirror0-3` (WorldObject, PassageMirror.scr) | not built as geometry (overrides.yml `skip`): the `mm9_mirror` decoration from their brush (the props project's `mirror_source.py`, `build_mirror.py`), placed from `mirrors.json` with cogs 420-423 and the mirror's click event; the map turns it (evt.AimDecoration) |
| `ElevatorObj` (MagicCarpet.scr) | a linear lift up the canyon's pit (below: Deviations) |
| `DB_TeleporterCage0` (DestructableBrush, 1000 HP) | a mover that drops under the island when the female sea monster dies (her DeathTriggerTarget) |
| `WorldObject0-22`, `InvisibleBrush` WorldObject2-5 (the desert's invisible walls), `WorldObject6-17` (the ocean's) | static (invisible collision where MM9 has it); WorldObject22, the ramp's slab south of the desert arrival, keeps Specter9/10 inside it in MM9 |
| `BlueWater0` (lake, Water115.spr, 0.4), `TubeRoomWater`/`TubeRoomWater0` (DirtyWater, water125.spr, 0.7), `Ocean` (Ocean4.spr, 0.95) | scene `water_volumes` (swum); their tops as non-solid liquid tiles (below: Water) |
| `Ladder5` (rungs WorldObject10), `Ladder1`, `Ladder0` | scene ladders: Bridge0 up to the start corridor; out of the lake onto Bridge0; out of the spike pit |
| `PerceptionBrush0-3` | untouchable translucent faces at 0.5 with a cog, shown at MM9's PerceptionValue; each takes the click of what it marks (MountainForestDoor, the painting, TrapRoomDoor2, ForestDoor0) |
| `Teleporter` (10: five pairs) | polled boxes; the party walking in is moved to the pair's arrival (`evt.MoveToMap` on the same map, facing as the arrival) |
| `Light` (120) | 76 BLV lights (colour x BrightScale); 44 over the four-per-point cap bake only |
| `DirLight` (11: moonlight over the canyon, desert and start room; the cages' spots) | bake spots (`dirlights: true`) |
| `Prop`, `CandleProp`, `TreasureChest`, `PropDamager` | 3D decorations (props project): claw torches, crystals, the rune stone, bushes and trees, the ice statuettes, the stone banshees, chests, the spike pit; the four bridge statues have a second copy at their bridge's other pose |
| `ExitTrigger` ExitPoint (StartOn 0) | MM9 positioned transition volume to Guberland (StartPoint0), gated by the flame cage's slab; its box reaches 40 LT toward the room and 12 LT down to the floor (`EXIT_GROW_LT`: the water barrel Prop36 stands on it) |
| `StartPoint` | `party_start_points` (facing south into the start room); Arslegard's ExitTrigger2 arrives on it |
| monsters | 41 placed actors at MM9's body sizes (ABC extents x Scale x 2.56); the Wyrde (RUDE 338, elf woman row 338, immobile), the adventurer (guard row 404) and Njam the Meddler (row 9261, hidden) |
| `AmbientSound` (115), `CClientFX` fireflies (7), `ObjectLight` (8), `PerceptionLight` (61), `Marker`, `AITrk`, `OutsideDef`, `Snow` (DemoSkyWorldModel), `Shooter`s | not built (sounds, particle fireflies, model-only lights, AI helpers, sky box); the Shooters are the map script's missiles |
| `Door7`, `DoubleDoorL28/R28` (RotatingDoor objects with no world model) | nothing to build |

## Scripted objects (`worlds/mm9/events/maps/darkpassageway.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **The bridge puzzle**: `DarkP_bridgepuzzle.scr` + `DarkP_initMyStuff.inc` on PuzzleManager0, `DarkP_RaisingSwitch.scr` on SwitchCreature0-3 (Hit A-D), `DarkP_RaisingBridge.scr` on Bridge0-4, `DarkP_BridgeReset.scr` on SwitchCreature5 | MM9's state machine as is: a 5-bit state (bit 4 - k: bridge k down) from 14, each statue maps it through its table (aA-aD), the bridges whose bit changed move (sound eshield.wav); state 0 (all up) stops the statues and unlocks and opens TeleportDoor0. The statues ride their bridges (each has a copy at the other pose, shown by cog). The reset statue puts it back to 14. The statues are animated decorations (2026-11-11): at start each holds fidget1's end (the banshee stands at rest: BANSHEE.abc has no awareAir); a click plays fidget1 (the banshee fidgetair1, statue and twin together) with EnchantItem.wav and the puzzle moves only at the clip's end (cog 410-418, timers 430-434; clip lengths read from the anim GLBs) |
| **The teleporters**: Teleporter0 -> Teleporter1, LakeTeleporter -> LakeArrival, MountainTeleporter -> MountainArrival, DesertTeleporter -> DesertArrival, ForestTeleporter -> ForestArrival | polled boxes (any part of the party), `evt.MoveToMap` same map with the arrival's facing (UseRotation) |
| **The canyon**: `DarkP_CanyonSwitch.scr` on SwitchCreature4, Shooters BansheeAEye0-7 (KBYellowLine, 5 damage, 1 s), CanyonDoorL0/R0 (Locked), TriggerBansheeOff0 | a click on the statue (an animated decoration, cog 419) plays Hattack2, Taunt, Rattack1 and Fidget1 in turn, each with EnchantItem.wav; each clip's end wakes a pair of eyes (0/1, 2/3, 6/7, 4/5: MM9's animation chain), each awake eye fires a missile at the party every second; after the last the statue holds Fidget1's end and the canyon doors unlock and open. Its start clip CastSpell is not in SKELETONWARRIOR.abc: it stands at rest. TriggerBansheeOff0 by the mountain teleporter turns the eyes off |
| **The magic carpet**: `MagicCarpet.scr "0"` on ElevatorObj | a click on the carpet lifts it to the statue ledge's height; 8 s at the top, then it sinks back (Deviations) |
| **The forest**: TriggerDoor0, TriggerAttack0, `DarkP_Warrior.scr` (ColloidalWarrior0, DeathTriggerTarget TeleportDoor1 UnLock), `DarkP_NPCDie.scr` (NPCAdventurer0), ForestDoor0, TeleportDoor1 (OpenTrigger: TeleportDoor0 Lock) | TriggerDoor0 unlocks and opens ForestDoor0 (AutoTrigger); TriggerAttack0 shuts and locks it, and 1.5 s later the warrior's blow removes the adventurer and the warrior wakes (dormant until then); its death (monster killed hook) unlocks TeleportDoor1, whose opening locks TeleportDoor0 |
| **The painting**: Painting (RotatingDoor) with OpenTriggers DoubleDoorL40 open, Painting lock, PerceptionBrush1 off | a click (or on its hint) swings the painting, opens the double door, turns the hint off |
| **The mirror puzzle**: `PassageMirror.scr` on Mirror0-3 ("330 Mirror1", "10 Mirror2", "340 Mirror3", "50 Gemstone"), `PassageLaser.scr` (GemLight0, LightBeam0-3), `PassageGemstone.scr "CageTerror 0 5"`, `DP_CageMonster.scr` on CageTerror0-5 (Door1-6), DesertDoor0 | a click turns a mirror 10 degrees clockwise at MM9's 180 degrees a second (counter + 1 mod 36, status text; `evt.AimDecoration` to -10 x MirrorTurns<k>, every click counted, re-applied at load since aims are not saved); a click on the gemstone shines its light: beams (`evt.Beam`, arc beam) from GemLight0 to Mirror0 and on through every mirror on its target; a mirror off target sends the beam its own way and stops it, one turned 70-290 degrees sends none (PassageMirror.scr :GiveFocus); all four on target: the light reaches BeamReceiver1 and the gemstone releases the cages, the cage doors open and the Terrors wake after the doors' open time (3.2 s), DesertDoor0 opens |
| **Njam's cameo**: Trigger1 -> SpawnNjam0 Spawn (`SpawnNjamCameo.scr`, `NjamCameo.scr`) | MM9's timing: 1 s later the GreaterDemon effect and Windup10 at the spawner, 2 s later Njam the Meddler (hidden friendly actor, `mm9_ai` script `njamcameo.scr`) appears with the town portal sound and wanders (BaseWanderForceStartUp; `evt.SetActorImmobile` frees him); 10-20 s later the map sends him "vanish" (`evt.TriggerActor`). His behaviour's cameo mode (`worlds/mm9/behaviors/njam.lua`): passive, and a hit sends him away at once (NjamCameo.scr OnDamage); leaving is the effect and Windup10, then the teleport sound and gone a second later (2026-11-09; before, a hit started a fight with a level-200 monster) |
| **The spike trap**: SpikeTrigger1, SpikeDoor1-4 (OpenTrigger lock), Spikes1 (PropDamager, DamagePerSecond 100, OneTimeDamage) | stepping on the flaps tips all four into the pit (they stay open); the spike damage is the fall (Deviations) |
| **The ocean's cage**: SeaMonsterFemale0 DeathTriggerTarget DB_TeleporterCage0 Destroy | her death drops the cage under the island |
| **The exit room**: ExitTrigger0-3 (one on at a time: 2 -> 0 -> 1 -> 3), ExitRiser (Locked), ExitRamp, Switch -> ExitReset | MM9's on/off chain on polled boxes; the last raises the riser 228 LT and runs out the ramp; the Switch resets all |
| **The Wyrde of the Unknown**: `NPC338.scr` :OnRude (RUDE 338's exit event 50284), FlameCage, ExitPoint (StartOn 0), FlameDamage | as MM9: with key 476 the cage opens; with item 396 and no key 188, key 188 and 146 000 experience; first talk (no key 187): keys 476 and 187, 92 000 experience, quest sound, the cage opens; the cage's slab leaves ExitPoint free |
| **The scroll**: `Givetake.scr "483 false 1"` on Prop38 | a click gives item 483 (Scrap of Book) into the packs and hides the scroll |
| **Unmatched** | the `Shooter` LightBeam0-3 and GemLight0 laser visuals beyond the beams; Njam's animations; ambient sounds; fireflies |

## Water: swimming (2026-11-06)

MM9 swims a large part of this map: the bridge lake (BlueWater0, 512 LT deep), the tube room and its flooded tube down
into the ocean hall (DirtyWater TubeRoomWater0/TubeRoomWater), and the ocean round the caged island (Ocean). Since
2026-11-06 the party swims and dives there (the shared water rule, `dungeon/water.py` `swimming`, on for every map;
devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): the scene's **`water_volumes`** are MM9's four volumes (TubeRoomWater
with MM9's current, 90 LT/s down = 230 u/s; MM9's tints; no fog), and `edit_polygons`' 32 LT surface tiles (`WATER`)
lie at each volume's own top (lake -600, tube room -384, ocean -1312 LT: MM9's) as **non-solid** liquid faces. The air
under them is the room above (rooms 29 -> 27: the tube room, the tube, the shaft and the ocean hall are one room);
the shared gates: `water_room_mismatches` 0, `water_bed_holes` 0. All 242 tiles are see-through now (liquids.py: each
has its bed in its room). Without swimming (`map: {swim: false}`) the tiles are the old wading floors and the dive box
returns.

- **The lake**: the bridges' plank decks stand 118 LT over the water (up, -480 LT) or under it (down, -640): a party in
  the water cannot climb onto a raised bridge or the far landing, so the puzzle still decides the crossing; Ladder1 takes
  a party out of the water onto Bridge0, as in MM9.
- **The tube and the shaft**: the party drops 128 LT from the path into the tube room's water, dives to its east end
  and swims along the tube (PhysicsBSP, -576 to -736 LT) into the shaft (x -3792..-3696, z -8480..-8368 LT), down which
  the current carries it. The shaft's bottom is the ocean hall's sky (Terrain4's down-facing starfield polygon at -977
  LT, which MM9's party passes from behind): non-solid here (`SHAFT_SKY`; still drawn from the hall). **Deviation**:
  the engine holds a body whose eye leaves a volume through its bottom as at a surface (it hangs at TubeRoomWater's
  bottom, -968 LT, over the hall's air), so a box at the shaft's bottom (`ShaftExit`, `SHAFT_EXIT_LT`) moves the party
  80 LT straight down under the sky (`SHAFT_DROP_LT`, map var `ShaftDrops`), from where it falls into the ocean (no
  fall damage into water). Engine item: let a body leave a volume through its bottom. The dive box is gone.
- **The ocean**: MM9's surface (-1312 LT); the island's sand (Terrain3) slopes up from 8 LT over the water, so the party
  swims to it and steps or surface-jumps out.
- **Sea monsters** are swimmers (water.SWIMMER_CLASSES; content.actor floats their box centre at MM9's position):
  SeaMonsterMale0 in the tube room's water (feet -1482), SeaMonsterFemale0 in the ocean (feet -3671); BaseSwim's rule
  sends them away from a party on land; her death still breaks the teleporter cage.
- **Ladder1** rises out of the lake: with swimming its foot reaches 60 LT under the surface, where a party swimming at
  it has its feet (the engine grabs a ladder from 24 under its foot).
- `scenario_swim.yml` (make_scenarios.py, from the built scene): into the lake, under, up to the surface; the tube,
  the shaft and the drop into the ocean; out onto the island (a surface jump at the sand's lowest edge, 21 LT over the
  water); the female stays in the ocean while the party stands on the island. All four scenarios pass (2026-11-06,
  review root; `scenario_doors_exits.yml` climbs Ladder1 from the water).

**Liquid shader (2026-10-31, [shared helper](../mm9r_common/liquids.py)):** the surfaces draw with the engine's liquid
shader (Water115 `lqw115…`, the tube room's water125, the ocean's Ocean4) and leave `translucent_faces`; MM9 opacity =
the surface's alpha x its sprite's mean alpha (the lake 0.17, `lqw115o17`), see-through where a floor of its room lies
under it. Sheets `review/liquid/` (before swimming).

## Deviations from MM9 and why

- **Water**: swum as in MM9; the shaft's open bottom is a move under the hall's sky (Water).
- **The crouch slot is walked upright** (2026-11-08, the user's decision): the only way from the path to the tube room,
  native x -13271..-13107, y -21627..-20972, was 123 high (floor -696, ceiling -573) and MM9's party crouched through
  it. The engine has no crouch on land, and a clearance scan of all 44 MM9 maps found no other low passage on the
  story path (`tests/playthrough/mm9/prep/low_passages.md`), so `CROUCH_SLOT` raises its ceiling to -470 (226 high)
  instead of adding a mechanic: the ten
  ceiling vertices move up and the walls that share them stretch. The MM9 playthrough (`tests/playthrough/mm9/`,
  segment 05) walks through it.
- **The magic carpet**: MM9's carpet rises at 500 LT/s and drifts the way the party faces at 800 LT/s until it reaches y
  0 or sticks, then falls back: the party steers it from the pit's bottom to the statue's ledge. Native linear movers
  carry the party up and down but not sideways, so the carpet sits in the pit's corner under the ledge (moved 476 / 524
  LT from its DAT spot, `CARPET_SHIFT_LT`), rises straight to the ledge's height (12 LT) and an invisible plank
  (`CARPET_PLANK_LT`, 100 x 100 LT at 12 LT) bridges the last 90 LT to the ledge; 8 s at the top, it sinks back. It
  rests 30 LT lower than MM9's (`CARPET_DROP_LT`, its lift 2546 LT instead of 2516; 2026-11-09): its top was 123-144
  over the pit floor, out of the party's jump (about 90), so a party that fell into the pit was stuck. Now it is 67 over
  the floor: walking stops at its edge, a jump lands on it (`scenario_scripted.yml`).
- **The statues ride their bridges** as two decorations each (one per pose), swapped by cog when the bridge moves
  (decorations do not move natively).
- **The mirrors' light** leaves along each mirror's own facing (its DAT Rotation: 0, 180, 0, 180 degrees), turned
  clockwise 10 degrees a click, as PassageLaser.scr's GetFaceDir reads it; the targets 330, 10, 340, 50 then aim it at
  the next mirror and BeamReceiver1 (2026-11-09: it left along the glass normal, 90 degrees off, so a mirror that
  looked right sent the beam astray). The solution: Mirror0 330, Mirror1 10, Mirror2 340, Mirror3 50 (33, 1, 34 and 5
  clicks from 0). The glass does not face the light's way (the brush is in world space): MM9's look.
- **The mirrors' pivot** is the brush's box centre, 1 LT (2.6 units) from MM9's Pos (2026-11-09: before, the mirrors were
  movers that never moved and only the beams showed their angle). The DAT keeps a WorldObject's brush in world space, so
  all four take facing 0 whatever their Rotation (90 or 270).
- **The spike pit** hurts by the fall (173 LT); Spikes1's one-time 100 damage is not added.
- **The banshee eyes** fire the engine's missile (`evt.FireMissile`, 5 damage) at the party once a second while awake,
  standing in for MM9's KBYellowLine Shooters; each shot plays KBYellowLine's launch sound at its eye
  (`MM9.launchSound`, PROJECTILE.txt; 2026-11-09). Its impact sound (KBYellowLineImpact.wav) is not carried.
- **Njam's cameo**: a hit sends him away, as MM9's OnDamage; a click or touch (MM9's Use and TouchNotify) does not: the
  behaviours have no click or touch hook. The first hit's damage lands (no hit can kill him: 6 600 HP; then he is
  invulnerable).
- **ExitPoint's box** reaches 40 LT toward the room and 12 LT down to the floor: the native exit tests the party's centre,
  which the water barrel on the exit (Prop36, non-solid in MM9) keeps outside MM9's box.
- **Light colours**: x BrightScale and zone gains fitted to MM9's lightmaps (Baked lighting).
- **The adventurer and the Wyrde** use the engine's guard (404) and elf-woman (338) bodies: MM9's own models are not
  in the runtime tables; the Wyrde opens MM9's RUDE 338 on a click.

## Can the monsters reach the party

The audit's eight "unreachable" regions are the passage's worlds: MM9 joins them only by teleporters, which monsters do
not use, so every monster outside the start's world "cannot walk to the party start" (false as a cut-off, true as a
description; MM9 is the same). Bodies carry MM9's sizes (Terrors 64 / 256, Specters 55 / 295, the Colloidal Warrior
157 / 358, sea monsters 192-230). Tested in game (`work/reach_monsters.yml`, passes):

- **Control**: DesertTerror2 on the plain floor of the trap corridor sees the party 650 south of it and closes to 356.
- **The pillared room's two 1M regions** (four Terrors MM9 drops from y 64 onto side platforms 82 units over the floor):
  DesertTerror1 comes down off its platform and closes on a party on the room's floor (from 1 000 to 340): **false**.
- **The canyon pit** (10M): Terror0, a flying banshee at the pit's bottom, closes on a party that fell in: **false**; the
  pit is left by the carpet (party) or flying (Terror0).
- The tube room's water and the ocean (SeaMonsterMale0, SeaMonsterFemale0): swimmers bound to their volumes (Water); a
  party in the water is reached there, one on land is not (MM9's BaseSwim).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_darkpassageway.yml`: 64 samples,
3 bounces, **direct 0.9, bounce 1.0, ambient 0.22**, `dirlights: true` (11 DirLights: the moonlight over the canyon, the
desert and the start room, the cages' spots), `max_lighting: 1`; no emitters (MM9's sky here is a dark starred night).
44 bake-only lights (over the four-per-point cap: the lake's and the canyon's big blue fills). One 4096 x 2525 page.
`stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map.

Light colours (`convert.py` `scale_lights`): MM9 colour x BrightScale (Ruined Temple lesson), the bake-only lights the
same, times **zone gains fitted to MM9's DAT lightmaps** (`LIGHT_GAINS`, from a 16-sample draft): the lake x1.0 / 2.0 /
2.1 (MM9's pure blue), the canyon x1.3, the tube room x1.4, the ocean x1.6, the spike corridor x1.7, the curve x1.45, the
Wyrde's room x2.6 / 2.2 / 2.2; the mountain room x0.25, the path's north part x0.45, the exit room x0.65. Bounce 6 (the
first draft) made the desert orange (light off the sand) and every zone 1.5-2x too bright; bounce 1 matches.

**The player light's stand-in.** MM9's lightmaps leave the corridors between the worlds almost unlit (canyon corridor
0.001, the pillared room 0.001, the mountain room 0.012, the path 0.01-0.02): MM9 lights them, and every surface near the
party, with its player light (WorldProperties `PlayerLightOn 1`, a camera light the RE did not resolve,
`MM9_RENDER_LIGHTING_RE.md`). The native map has no player light (the engine lights the party's surroundings only with
the Torch Light spell), so matched exactly those rooms render black (screen luma 2) and the dark-textured lit rooms read
6-9. The stand-in is an ambient floor per room (`convert.py` `ROOM_LEVELS`: sector minimum light levels, which the bake
turns into max(0.18, (31 - level) / 31 x 0.97) x the profile's `ambient_scale` 0.22): level 0, about 0.21, for the unlit
corridors (canyon corridor, lake landing, mountain rooms, the forest's corridors and teleporter, the path, the pillared
room, the desert arrival, the spike room's teleporter alcove); level 8, about 0.16, for the canyon with its pit and the
start room with the lake; level 15, about 0.11, for the tube room, the ocean and the trap corridor; the rest of the map
level 30 (0.04). An archway cut (`path_tube`) gives the path its own room apart from the lit tube room. **Revert**:
`ROOM_LEVELS = []` in `convert.py` and `ambient_scale` 0.2 in the profile (rebuild, rebake): the lightmap-exact bake.

**Brightness and hue.** The lightmaps are matched first (direct, bounce, zone gains: the lit zones within x0.9-1.2 of
MM9's DAT lightmaps on the lightmap-exact bake), then the player light's stand-in adds its floor. Per zone with the floor
(`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`, `work/hue.txt`, `work/hue_summary.txt`), green-channel level
ours / MM9 and hue (B/R MM9 / ours):

| Zone | Level | B/R MM9 / ours |
| --- | --- | --- |
| forest | 1.10 | 1.21 / 1.06 |
| desert | 1.12 | 1.02 / 0.84 |
| curved corridor | 0.91 | 0.98 / 0.95 |
| Wyrde's room | 0.98 | 0.68 / 0.84 (MM9's warm light capped at 255) |
| tube room (level 15) | 1.33 | 1.09 / 1.05 |
| lake (level 8) | 1.44 | pure blue / 3.06 (the floor greys it a little) |
| ocean (level 15) | 1.50 | 1.41 / 1.37 |
| exit room | 1.82 | 1.00 / 0.99 (its box takes in the desert arrival's floor) |
| canyon (level 8) | 2.15 | 1.00 / 0.98 |
| start room (level 8) | 2.56 | 1.90 / 1.15 (MM9 adds its four claw torches' dynamic light here too) |
| unlit corridors (level 0): canyon corridor, pillared room, mountain rooms, path, spike corridor | MM9 0.001-0.05, ours 0.16-0.25 | neutral |

Lightmap-exact numbers (no floor: `ROOM_LEVELS = []`, ambient 0.2; an earlier bake of this night): start 1.19, lake
0.99, canyon 1.04, forest 1.07, tube 1.07, ocean 0.96, desert 1.05, spike 1.08, exit 1.16, curve 0.89, Wyrde 0.96.

No real MM9 screenshot of this map exists (`devdocs/mm9_rework/overnight/real_mm9/`). Screen means
(`work/brightness_v02.txt`, 47 views, centre crop): capture 79.6 (information only: the old import drawn fullbright by
our outdoor renderer), native unbaked 49.8, **native baked 21.5 (x0.27)**; **the darkest baked view is 9.6** (k03, a
dark wall in the desert teleporter's alcove, a level 0 room), the next 11.4-13.1 (the path, the lake's landing, the canyon
corridor, the mountain rooms).

## Open items

- MM9's player light (`PlayerLightOn`): not reproduced as a light; the per-room ambient floor stands in for it (Baked
  lighting). A camera light would light only near the party and leave the far ends dark, as MM9 does.
- Leaving the tube's volume through its bottom (engine; ShaftExit stands in); the
  carpet's steering; Spikes1's damage; MM9's monster models (the Wyrde and the adventurer use engine bodies).
- `AmbientSound` (115), the fireflies (`CClientFX`).
- Done 2026-10-31 by the props project (`../../props/mm9_darkpassageway_claude/README.md`, "Fixes"): the ice
  statuettes are translucent (blended Icebolt), the four claw torches (CandleProp0-3) are the new `mm9_clawtorchlit`
  (row 2453) with blue flames rising from the orb between the talons (`mm9_clawtorch` stays flameless for Dungeon of
  Secrets), and the posed statues lost Blender's bone-display ball. `props.json` regenerated (only the torches'
  decoration changed), `convert.py` rerun (the BLV changed only in those four decoration ids) and the lighting
  re-baked through `bake_slot.sh`.

## Not checked

- Actors drawn with MM9 art; a desktop playthrough with real input: the bridge puzzle by hand, the carpet ride on the
  desktop (scenario: a real click from on it and a walk from its top), the banshee eyes' missiles hitting, fighting
  the sea monsters on the water, the female's death breaking the cage in a real fight (scenario: not killed), the
  Colloidal Warrior's death unlocking TeleportDoor1 (the kill hook is written, not exercised), the swim down the tube on the desktop,
  every teleporter on the desktop (one checked); save/load in the middle of the puzzles; arrival seen from Arslegard and in
  Guberland; Android.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 15:08:46 (convert.py from the current shared converter, end 15:10:23): 2 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 4422 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass (below).
**`scenario_scripted.yml` step 192 (fixed 2026-10-31, scenario).** The scenario always passed; step 192 logged
`ASSERT fail ... expected=opening actual=open` as a tolerated "transient state" warning (already on the build night),
which the rebuild script counted as a failed assert. The expectation was wrong: ForestDoor0 rises 96 LT at 70 LT/s
(1.4 s), so 3 s after TriggerDoor0 it is open. `make_scenarios.py` now checks `opening` 1 s after the trigger and
`open` 2 s later; no warning left. No map change.
