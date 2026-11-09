# MM9 rework: Anskram Keep (`anskramkeep.blv`)

The first dungeon pilot of the [MM9 rework](../../../devdocs/mm9_rework/PLAN.md): MM9's Anskram Keep converted from
its DAT world into a native indoor map (BLV: sectors, portals, linear movers, lights, exit volumes). Built into the
isolated review root `output/mm9_rework/assets_dev` ([`../mm9r_common/review_root.py`](../mm9r_common/review_root.py));
`assets_dev` is not written. Built on the shared converter [`../mm9r_common/dungeon/`](../mm9r_common/DUNGEON_PLAYBOOK.md)
since 2026-10-30 (`convert.py` is the map's `Hooks`; the old stand-alone converter is kept in `legacy_converter/` with the
build it made). Status 2026-10-30: geometry, rooms, portals, doors, lights and exits, the population: 241 MM9 props and
7 chests as 3D decorations, the 8 Imp gate fires, the 47 monsters, the chests' loot; MM9's plates, crushers, levers,
airlock gate, cages, Imp gates, the Giant Imp with its shaft and lift, as native events; MM9's swinging doors, levers,
pivot traps with their niches, pits and spike pits, ladders and hatches as rotating movers
([design](../../../devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md)); the 12 perception hints.

## Build and review

```sh
cmake --build build --target mm9_compile_indoor_source -j25                 # the shared indoor compiler
# The props (once, or after a model change): level_generation/props/mm9_anskramkeep_claude/README.md
python3 level_generation/projects/mm9r_common/review_root.py                # link new models and world rows
python3 level_generation/projects/mm9r_anskramkeep/convert.py --plan        # analysis only: work/rooms*.png (10 s)
python3 level_generation/projects/mm9r_anskramkeep/convert.py               # build, compile, install (30 s)
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_anskramkeep   # walkability
python3 level_generation/projects/mm9r_anskramkeep/make_scenarios.py        # scenario_chests/scripted/rotating.yml
for s in doors_exits chests scripted rotating; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_anskramkeep/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_anskramkeep   # the bake
python3 level_generation/projects/mm9r_anskramkeep/make_tour.py v04         # tour of the new map
python3 level_generation/projects/mm9r_anskramkeep/make_tour.py v04 --original   # same views, old map
./tools/run_game.sh --isolated mm9ansk --world mm9 --map anskramkeep.blv \
    --assets "$PWD/output/mm9_rework/assets_dev" --position 0 1300 -491 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 120 --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_anskramkeep/review_tour_v04.yml
./tools/run_game.sh --isolated mm9anskorig --world mm9 --map anskramkeep.odm \
    --assets "$PWD/output/mm9_rework/assets_original" --position 0 102 -491 --yaw-radians 1.5708 --pitch-degrees 0 \
    --warmup 3 --seconds 120 --set video.view_distance=unlimited \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_anskramkeep/review_tour_v04_original.yml
python3 level_generation/projects/mm9r_anskramkeep/review_sheet.py review/v04 review/v04_original
python3 level_generation/projects/mm9r_anskramkeep/review_movers.py tours; bash level_generation/projects/mm9r_anskramkeep/review/movers_run.sh
python3 level_generation/projects/mm9r_anskramkeep/review_movers.py sheet   # review/movers_compare.jpg
python3 level_generation/projects/mm9r_anskramkeep/compare_builds.py <old build dir> level_generation/projects/mm9r_anskramkeep/work
```

**The original tours need `--set video.view_distance=unlimited`.** The old map runs on the outdoor renderer, whose enclosed
maps default to `view_distance_scale: 0.4`: it fades far geometry, which is not MM9. Without the setting the 30 views
measure 46.2, with it 44.4.

The original map forbids saving, which the isolated launcher needs: `convert.py` places a copy of the old
`anskramkeep.scene.yml` with `allow_save_game: true` in `output/mm9_rework/assets_original` (temporary file, then
rename). After a `review_root.py` refresh, rerun `convert.py`: it removes the old map's sidecars from the mirror again
(they are recorded in `owned.txt`, so a refresh should keep them away).

Review: `review/v03_compare.jpg` (30 eye-level views, MM9's bmodel_world map left, the native BLV right): the 18
geometry views of v02 plus the barracks, officers' rooms, store rooms, the gate and its levers, the treasure panel,
the two cages and an Imp gate. The in-game map is the engine's BLV line map (the painted MM9 PCX is no longer listed
in the review root's `worlds/mm9/ui/maps/catalog.yml`).

## Files

- `convert.py`: the map's hooks on the shared converter: the population and the map Lua (decorations, trigger pads,
  perception hints, actors, MM9's scripted objects). Geometry, rooms, movers, lights, loot, tables and install are the
  shared package's.
- `overrides.yml`: the explicit choices a rerun keeps: the `map` settings, what every DAT world model becomes, the
  archway cuts, the exit volume change, the rectangle portals, the ladders.
- `legacy_converter/`: the stand-alone converter this map had until 2026-10-30 and, in `work_snapshot/`, the last build
  it made; `compare_builds.py` compares any build against it.
- `props.json`: every prop, torch and chest placement (written by `../../props/mm9_anskramkeep_claude/scripts/
  placements.py`, checked against the old map's baked BModels), with each torch's BLV light.
- `source/`: the indoor source package (`anskramkeep.glb`, `anskramkeep.geometry.yml`) the compiler reads.
- `work/`: `transform.json`, `rooms.png` / `rooms_large.png` (the room plan with portals), `build_report.json`
  (numbers, every portal and its rooms, the table rows), `doors.json` (every mover with its DAT names, door id, event,
  room and motion), `lights.json`, `content.json` (every decoration, trigger pad, actor, chest and Imp gate with its
  DAT anchor, room and event; the light coverage), `population.json` (the DAT monsters and chests), `models.json`,
  `walkability.json`, `dropped_faces.json`, `mixed_faces.json`, `runtime/` (the compiled BLV, scene, Lua, doors).
- `make_tour.py`, `review_sheet.py`, `review_tour_v0*.yml`, `review/`, `walkability.py`, `make_scenarios.py`,
  `scenario_doors_exits.yml`, `scenario_chests.yml`, `scenario_scripted.yml`, `scenario_rotating.yml`, `review_movers.py`,
  `compare_builds.py`.

## What the conversion does

**Frame.** `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (`work/transform.json`): the frame of the old bmodel_world
map, which fits int16 (x -6 881..6 922, y -696..16 015, z -1 137..573), so its transition coordinates and minimap bounds
stay valid. The main floor is at z -491.

**Geometry.** MM9's `PhysicsBSP` is the keep's lightmapped static world (the `VisBSP` has no lightmaps: it is the
structural visibility hull with the leaves and UserPortals; the old ODM import skipped it too). Each v66 poly stores
its ring twice, the plain ring and the same ring with its T-junction vertices; the shared reader sums the two counts,
so `geometry.poly_ring` keeps the second (watertight) ring. This affects the old transcoders too: their polygons are
the two rings concatenated, which is where the 6 937 "degenerate triangles" of the old import come from. Kept static
models: the carpets and `WorldObject0` (non-solid: untouchable faces), the invisible brushes and ladder blockers
(invisible collision faces). The breakable `Floordoor` slabs are movers (below). Left out: 230 `AITrk` navigation
helpers, `VisBSP`. The 3 `Ladder` volumes become the scene's `ladders`. The 12 `PerceptionBrush`es are the hints (below).

6 890 static source polygons; BSP fragments merged back where the union stays convex (only 122: MM9's fragments are
mostly cut around beams and do not form convex unions); the faces with no air in front of them dropped (between
brushes, facing out, or in the sealed Imp gate alcoves, which no seed reaches). Texel UVs from MM9's surface mapping, textures through the existing 10-character aliases in
`worlds/mm9/textures` (`anskramkeep.material_aliases.yml`). Result: **8 946 native faces** (polygons where integer
coordinates keep them planar, triangles where not), 12 669 vertices.

**Rooms and portals (the method).** A 16-unit voxel grid of the keep's air (6.1 M voxels; flood from every start,
light, trigger, monster and chest; sealed, no leak to the outside) is divided by portal barriers, and its connected
parts are the rooms. Portals:

- 28 of MM9's 33 `UserPortal`s (all at doors: the double doors, round doors and the gates); the 5 diagonal ones,
  `DoubleDoor6`, which has none, and the two cage plugs (`CritterBreakOut0/1`) from their leaves' plane and extent:
  **36 door portals**. Each door portal stands on its leaves' face on the side of its normal's negative side, so the
  leaves lie wholly in one room: the engine collides the party with door faces of the next room only once its
  sphere reaches the portal, and with the portal through the middle of the gates' 82-unit leaves the party walked
  half way into a shut gate from the other side before meeting it.
- **19 archway portals** from the 13 cuts in `overrides.yml`: a voxel slice perpendicular to x or z through a chosen
  point, sealing the opening the point stands in (each opening of a multi-opening cut is its own portal, since each
  joins its own pair of rooms). They split the ring corridors, the open north hall (one 2 000 × 1 800 LT space at
  walking height), the central and south halls.

Every face goes to the room in front of it (the nearest labelled air, ignoring air behind it); a face that sees two
rooms is clipped at the portal plane between them (378 splits) or, for a ceiling or floor brush running over the walls
between rooms, at the plane where the rooms' samples separate (114 splits). 230 faces still see two rooms (most
under a wall standing on them) and go to the room most of them faces. **47 rooms + empty sector 0, 61 portal faces**
(the 55 above and nine rectangles: below), median 164 faces per room, largest 702. Every portal joins two different rooms.

**The barred windows.** The airlock's two windows (`AirlockWindowWest`, `AirlockWindowEast`) are holes in the 48-LT wall
between the vestibule and its side rooms. Their three 4-LT bars stand in the same voxel column, so the 16-LT air pass
saw a solid wall and the rooms got no portal: through the bars the engine drew black. Two `rect_portals` stand in the
windows now. A sweep with 6-LT voxels and axis-aligned sight lines finds no other pair of rooms that sees through
without a portal.

**Perception hints.** The dark red rectangles on the floor at the traps are not carpets: they are MM9's 12
`PerceptionBrush`es, Perception.spr (a red caustic with alpha, 20 frames at 15 fps) on the one visible polygon of a brush
at brush `Alpha` 0.5, shown to a party with Perception 2 or better (`PerceptionValue`; the outdoor import reads it the
same way). They mark the three pivot traps, the three crusher plates, four spots on the west diagonal and two in the
airlock's side rooms. Each is an untouchable face `TRIGGER_perception_<brush>` with cog 300 + k, translucent
(`translucent_faces`, found by texture since `faces.yml` lists only `STATIC_` nodes). The map script hides or shows them
on load and every 3 s (`IsAtLeast(PerceptionSkill, 2)`); the BLV keeps them visible so that the bake lightmaps them. The
frames are 20 rows in the review root's copy of `engine/data_tables/texture_frame_data.txt`.

**Doors (97 MM9 door objects, 2 cage walls and 4 floor slabs → 103 native movers).**

| MM9 | Count | Became |
| --- | --- | --- |
| `RotatingDoor` double doors (`DoubleDoorL/R1–28`) | 56 leaves | 56 rotating movers: MM9's 90° about the hinge at 70°/s, sine, open away from the party, shut themselves after 7 s, reverse off a body; a click (events 101–134) moves both leaves |
| `Door` round doors (`RoundDoorLeft/Right0–3`) | 8 | 8 linear movers, MM9's own sideways slide into the wall (48 LT); a click |
| `Door` gates (`Outerdoor0/1`, `Innerdoor0/1`) | 4 | 4 linear movers, MM9's slide (128 LT), opened by the gate switches and, once both levers are pulled, a click on a leaf (below); the outer leaves are authored apart and MM9's "open" slides them shut, so they are built shut and start open |
| `Door` plates and fittings (6 `ShooterPlate`, 3 `CeilingCrush`, 3 `CeilingCrushPlate`, `PivotTreasurePanel1`, `LeverPanel`, `LeverPanel0`) | 15 | 15 linear movers with MM9's motion, wired (below) |
| `Door` `ExitStairs`, 3 `PivotButton` | 4 | linear movers with MM9's motion; the buttons (in the niches) spring the traps, `ExitStairs` raises the Giant Imp |
| `DestructableBrush` `Floordoor1–4` | 4 | movers that drop 216 LT down the shaft and out of sight under its floor when the Giant Imp comes (MM9 destroys them; `slide`) |
| `RotatingDoor` levers and switches (`SwitchLever0`, `PanelLever`, `Switch0/1`) | 4 | 4 rotating movers, MM9's −80° / ±35° about their horizontal axes at 20–50°/s; toggles |
| `DestructableBrush` cages (`CritterBreakOut0/1`) | 2 | movers that sink by their height into the floor and wall below (`sink`), with doorway portals |
| `RotatingDoor` traps and hatches (`PivotWallTrap1–3`, `TrapExitDoor1–3`) | 6 | 6 rotating movers (below) |

Each mover is named by its DAT object (`MECH_DoubleDoorL15`, `MECH_RoundDoorLeft0`, ...; `work/doors.json` lists door
ids, events, rooms, motion and the `mover` block). The door groups' click events trigger all movers of the group
(`evt.SetDoorState(id, DoorAction.Trigger)`). MM9's doors also open for monsters (`AITriggerable`); these open on the
party's click only (a later step; the rotating movers already stop for and reverse off monsters).

**Traps, pits, ladders.** Each `PivotWallTrap` is a cross of floor and wall turning about its centre on the floor plane:
90° at 100°/s, MM9's 5 s wait (the mover's auto-close), back at 50°/s. `bodies: push` and `carry` tip the party: it rides
the half under it to the walkable limit, slides off and falls into the pit, and the former wall arm closes the floor
above it. Stepping on the corridor's half of the floor springs the trap (a pressure plate on the mover's faces, whose
handler checks the party's side of the axle; MM9's trigger is a box on that half, and a pad would stay in the air when
the floor turned); its `PivotButton` does the same, and the trap is armed again after 8 s. The covers are not solid in the voxel pass, so the pits' air floods from the corridors; six
`rect_portals` (each trap's opening, each hatch's hole, in the floor plane) cut them off as rooms, and the cross and hatch
belong to both rooms (`extra_rooms`). The `south_corridor_east` archway moved from x 1300 to x 1180: it stood in the trap.
Each pit has MM9's `SpikePit` on its floor (the model `mm9_spikepit`) with a pad that strikes for 20 physical (MM9: 20 per
second while touching; a timer strikes once a second while the party stays within 40 units of the pad), the two `LadderBlocker`s, a `Ladder` (`overrides.yml` `ladders`) and
above it a `TrapExitDoor` hatch that opens on a click, swings up at 60°/s and shuts after 5 s. Climbing past the top
places the party on the corridor floor beside the hole. `work/doors.json`, `scene.ladders`.

**The niches.** The cross has four quarters and turning it by 90° swaps them, so the V between floor and wall carries a
body round the axle. That is how MM9 reaches the niche behind each trap's wall, and why the trap closes at half its
opening speed (`ClosingSpeed` 50 against `Speed` 100): a party standing on the turned floor while the trap waits rides
the slow swing back over the axle and lands on the niche's floor. Inside, the `PivotButton` springs the trap (its closing
triggers `PivotWallTrapTrigger`) and the fast opening swing carries the party out to the corridor's side, on the floor,
not into the pit. At trap 1 the niche holds `PivotTreasurePanel1` and TreasureChest1. The way in asks for the trap to be
sprung without falling into it: run across its floor and stop beyond it, then step back on while it stands turned. This
reading comes from the geometry and the speeds (no MM9 script describes it). The native mover rules do all of it;
`scenario_rotating.yml` rides in and out.

**Lights.** MM9's 113 `Light` objects (the 408 `DirLight`s only fed its lightmap bake; the 101 `WallTorch` props carry
no light of their own) as native point lights, radius × 2.56, colour as authored, taken smallest first while no floor
point is under more than 4: **112 lights**; the dropped one is `Light6`, the 3 072-radius fill light of the central
hall. Sector minimum ambient 20 everywhere. Of these, 101 are the wall torches' lights: every `WallTorch` has its own
kept `Light` 41–93 units away (one each). The torch decorations carry no light of their own (their rows have
LightRadius 0), so nothing doubles; `props.json` names each torch's light. The 8 Imp gate fires are decorations that
carry their light (MM9's `Fire` objects are their own lights: LightMaxRadius 80 LT = 205, colour 255/190/130, row
`mm9_gatefire`). With them no floor point is under more than 4 lights (`work/content.json` `light_coverage`).

**Where the lights come from (for the baked lighting).** BLV point lights: `work/lights.json` (name, position, radius,
colour, kept or dropped and why), also in `source/anskramkeep.geometry.yml` `lights`. Decoration lights: the
`mm9_gatefire` row in `assets_dev/worlds/mm9/data_tables/decoration_data.txt` placed at the 8 positions in
`work/content.json` `decorations` (decoration `mm9_gatefire`, anchors `ImpGateFire0-7`); a gate's fire goes out
(`evt.SetSprite(200 + k, false)`) when its gate is cleared. The wall torches are lit by their BLV lights only.

**Exits and tables.** The two `ExitTrigger`s stay MM9 positioned transition volumes from
`worlds/mm9/data_tables/map_transitions.txt` (the indoor runtime supports them). The review root's copy changes only
this map's 4 rows, computed from the assets_dev originals: source and destination files become `anskramkeep.blv`,
arrivals land on the floor (z -491), and `Sturmfordexit` reaches down to the foot of the spiral stair. The
`map_stats.txt` row 9036 names `anskramkeep.blv`. Party starts: `Anskramkeepback` (start 0, south, facing
north into the keep) and `Anskramkeepfront` (north, facing south): MM9's 90 − ry; the old converter's −ry had them a
quarter turn off, as it had the 47 actors. Props keep −ry, which their placements use.

**Population.** `content.py`, from `props.json` and the old scene (`assets_dev/worlds/mm9/maps/anskramkeep.scene.yml`):

- **256 decoration entities** (`DECOR_<DAT name>` markers listed in their room's `source_nodes`; the entity name is the
  DAT name, and the build refuses one that equals a decoration name): 241 props (101 wall torches, 28 medium beds,
  20 crates, 20 dressers, 16 chairs, 17 weapons cabinets, 10 barrels, 5 scrolls, 4 round tables, 4 bone piles, 3
  broken tables, 3 weapon racks, 4 bookcases, 2 beds, 2 armchairs, 2 desks), the 7 chests and the 8 Imp gate
  fires. At most 17 per room. The models are the props project's (`../../props/mm9_anskramkeep_claude/`).
- **7 chests**: decorations whose click (secondary event 41–47) runs `evt.OpenChest(k)`; the loot records are the old
  scene's (treasure type 7, levels 0–2, trap levels 1–3, repopulate) in the same frame, `openedChestIds` in
  `SetMapMetadata`. TreasureChest1 sits in a niche behind `PivotTreasurePanel1`.
- **47 monsters** as placed actors: the old scene's MM9 actor records (monster rows 9078–9112, whose pictures are now
  the `MM9 <Family> A|B|C` families), at their DAT positions on the floor under them, facing as in MM9, sector from
  their room. Scripted ones: the Giant Imp (group 51, hidden, 100 HP, twice the size: DAT Scale 2) and its two guards
  (group 52, hidden, not hostile: `AK_GiantImpGuard.scr` makes them the party's friends), the caged Nagate
  Hatchlings (53) and Airborne Ickies (54). No packs or spawn points were added.

**Scripted objects** (`worlds/mm9/events/maps/anskramkeep.lua`, written by `content.map_script`; MM9's touch triggers are
invisible pressure-plate pads `TRIGGER_<DAT name>` 3 units over the floor, shrunk to stay on one floor in one room and
moved off a doorway they straddle):

| MM9 | Native |
| --- | --- |
| `ShooterPlate5–10` → `Shooter5–8`, `CeilingShooter0/1` (FireBolt, DamageAmt 5/10) | the plate is a pressure plate (events 60–65): it sinks, a fire bolt (`evt.FireMissile("Fire")`) starts a third of the way from the shooter toward the party, the plate rises after 3 s (timers 150–155) |
| `CeilingCrushPlate1–3` → `CeilingCrush1–3` (Speed 300, MoveDist 176, spikes 20/s) | the plate (events 66–68) sinks and the crusher drops; 0.7 s later a party under it takes 20 physical, and the crusher rises after 3 s (timers 156–161) |
| `PivotTreasurePanel1` (PushOpen, Sticky) | a click (event 70) slides it up, showing TreasureChest1 |
| `SwitchLever0`, `PanelLever`, `Switch0/1`, `LeverPanel/LeverPanel0`, `Outerdoor0/1`, `Innerdoor0/1` | the airlock gate: SwitchLever0 (event 71) slides both lever panels aside, PanelLever (72) unlocks the switches, either switch (73/74) shuts the outer gate and opens the inner one, or the reverse (MM9 does one after the other); with both levers pulled a click on a gate leaf (89) does the same, before that it says "The gate is locked." |
| `TriggerNagateBust`, `TriggerIckyBust` → `CritterBreakOut0/1` (`KingKong.scr`) | pads (events 75/76) sink the cage walls; the caged monsters come out |
| `ImpGateSpawner0–7` (`AK_ImpGate.scr` "Imp 5"), `TriggerClosetGate0–3`, `TriggerBarrackGate0–9`, `ImpGateFire0–7` | 14 pads (events 170–183) start their gate; it sends 5 Imps (row 9079) one after another, each when the last is dead (monster-killed hook 95), then its fire goes out |
| `TriggerGiantImp` (all eight gates done), `GiantImp`, `GiantImpGuard0/1`, `Floordoor1–4`, `ExitStairs` | four pads round the shaft (event 90; a pad is a floor, and one over the shaft would hold the party up) once the quest key is given: the slabs fall and the lift `ExitStairs` rises 208 LT at 50 LT/s with the Giant Imp on its lower disc, which closes the shaft level with the hall (the party walks through between its pillars); the Imp and its guards appear |
| `Killed` (`Anskrammainline.scr`), keys | each gate gives its key 510–517 (`AK_ImpGate.scr`), the last one also quest key 39: QBits 90510–90517 and 90039 (`MM9.giveKey`), which NPC997's quest entries read. On load the fires go out by these keys |
| `PivotWallTrap1–3`, `PivotWallTrapTrigger1–3`, `PivotButton1–3`, `TrapExitDoor1–3`, `Spikes14/16/17` | the trap's corridor half (events 77–79) or its button (83–85) springs it, a timer arms it again; the hatch opens on a click (80–82); the spike pads (86–88) strike, then a timer every second while the party stays (`SpikeHits` counts) |
| `Prop3–7` (`BookLetter.scr` "488 Letter" x4, "489 Letter 1") | a click (events 191–195) shows MM9's BOOK AND SCROLL TEXT.csv rows: the Memorandum to all Soldiers (488) and the Letter to Captain (489), with bookopen.wav (2026-11-06; scenario_chests clicks all five) |

Named map variables keep the state (`Gate`, `ImpGate<k>`, ...; saved with the map); the load event (1) puts out the
fires of finished gates and sets the perception hints. `ShotsFired`, `CrushHits` and `ImpsSummoned` count for the scenarios.
`anskramkeep.script_ir.yml` and the bmodel_world sidecars are removed from the mirror.

## Checks

- `scenario_doors_exits.yml` passes: the closed entrance door stops the party, opens on its event, the party walks
  through, and both exits raise their MM9 exit trigger (987 north, 988 south).
- All four scenarios pass on the build of 2026-10-30 on the shared converter. `compare_builds.py`
  `legacy_converter/work_snapshot work`: nothing lost: 241 props + 7 chests + 8 fires + 3 spikes = 259 decorations, 47
  actors, 7 chests with identical loot, every old mover and pad (103 movers with the 4 slabs; `TriggerGiantImp` is now
  its four pads), 112 lights. The port alone, before the fixes, was byte-identical in BLV, doors and faces.
- `scenario_rotating.yml` passes: a shut leaf stops the party; a click swings both leaves open and the party walks
  through; they shut themselves after 7 s; with the party in the doorway the closing leaves reverse and stay open; a step on
  PivotWallTrap1 tips the party into the pit, onto the spike pad, and the trap turns back; on Ladder4 the shut hatch stops
  the climb under it; opened, the party climbs out onto the corridor floor; the hatch shuts itself; the spikes strike
  every second while the party stands there and stop when it leaves; the party rides the turned floor into the niche,
  and the niche's button carries it out to the corridor's side; a save in mid-swing.
- `scenario_chests.yml` passes: the 7 chests open (6 by the interact key from in front of their models; TreasureChest1
  after its panel slides up, by its event, since headless runs pick against the renderer's vertex copy, which follows
  door motion only while frames render).
- `scenario_scripted.yml` passes: a switch and a click on the inner gate are refused until the levers; SwitchLever0
  slides the lever panels; then a real click on the inner gate from the airlock shuts the outer gate and opens the inner
  one, and Switch0 swaps them back and again; from the vestibule the party walks on north, from the south it stops at
  the shut outer gate; ShooterPlate8 sinks, its bolt is accepted and the plate rises again; CeilingCrush1 drops,
  strikes the party on its plate and rises; TriggerNagateBust sinks CritterBreakOut0; TriggerClosetGate1 sends an Imp.
  All eight gates started by walking onto their own pads (gates 0 and 3 in the north hall), five Imps each killed one
  by one, give keys 510-517 and the quest key 39 (2026-11-06); a pad drops the slabs, raises the
  lift and shows the Giant Imp; the party walks across the raised lift at floor height.
  Not confirmed headless: the bolt's hit (no damage registered within 1.5 s; the headless party regenerates quickly).
- Walkability (`dungeon/audit.py`, `work/walkability.json`): 42
  steps and 29 flights, all on MM9's spiral stair (sector 1: risers of 24 LT = 61 native, more than the party's 50)
  and the 8-unit-long lips of the round door frames; 17 mover notes (the trap plates sink 10, the cage plugs sink into
  floor and wall, `ExitStairs` stands in its shaft); 1 unreachable ledge (0.02 M
  units²); 6 actor notes: the caged critters stand tight in their cages, as MM9 places them.
- Compiler unit tests (`openyamm_indoor_source_tests`) pass, including the polygon-fan case.
- Load: 47 actors, 29 of them untextured in the headless run: the Imp and Icky families' descriptors
  (`worlds/mm9/data_tables/monster_descriptors.txt`, `MM9 Imp A-C`, `MM9 Icky A-C`) name MM6 sprites (`m179s`,
  `m159w`...), archived since MM6 went 3D-only. That is creature art for the MM9 creature work, not placement.

## Deviations from MM9 and why

- MM9's doors open for monsters too; here only for the party (the rotating movers stop for monsters; the opening itself
  is a later step).
- The airlock opens both gates at once instead of one after the other.
- The gate's leaves take a click (event 89): with both levers pulled it works the gate like a switch. MM9's leaves take
  none; a player who had pulled both levers stood in the airlock at the shut inner gate, Switch0 behind its slid panel
  outside, and took the gate for broken (save AK_DOOR_NOT_OPEN, 2026-11-06).
- Waveforms: MM9's slow-on hatches ease as sine (the user's choice); a body's push is not swept against walls.
- The trap springs from the whole of the floor's corridor half instead of MM9's trigger box on it (a plate fires where
  the party steps on, and a pad would float when the floor turned). The spikes strike 20 once a second, not 20 per
  second in small steps.
- The `Floordoor` slabs drop down the shaft instead of breaking into debris (their `ExplodeDamage` is not carried over).
  The Giant Imp appears at once, without MM9's sound delay and black smoke. The guards do not fight the Giant Imp (they
  appear friendly to the party).
- The perception hints are checked every 3 s, not per frame.
- The Imp gate fires stand on the hall floor at the gate's mouth: MM9 burns them in the sealed alcove behind each gate
  (floor 112 LT below the hall; not built). Spawned Imps appear in front of the gate.
- The three `SpikePit`s under the crushers are not placed: they move, decorations do not; the crushers' strike is a
  scripted 20 damage instead.
- MM9's touch volumes are pressure pads on the floor (an MM9 trigger fires on any part of the party in its box; a pad
  when the party stands on it). MM9's barrels (`Barrel`: drinkable liquids) and bone piles (searchable, disease) are
  decorations only; the old scene's barrel and bone-pile records are not wired.
- No perception hints or lightmaps; the light is native point lights and ambient (a baked indoor lighting pass will
  read the lights above). The south exit volume reaches down to the floor, since the spiral stair's risers are too
  high to climb.

## Texture density (checked 2026-10-30)

The face UVs are MM9's own mapping, unchanged: `polygon_uvs` evaluates each DAT surface's `(O, P, Q)` in texels and the
compiler stores them as integer texels of the 1× size, so a texture repeats exactly where it repeats in MM9. Measured
per face (planar gradient of the BLV UVs against the GLB's float UVs, all 8 749 faces): the medians match the DAT's
`|P|`, `|Q|` / 2.56 for every texture, e.g. 1 texel per LithTech unit = **0.39 texels per native unit** for the walls,
floor, ceiling and wood (128² tiles every 328 native units), `anskramdoor` 1.333 per LT = 0.52 (each 123 × 246 door
leaf shows exactly half of the double-door picture: the finite art fits once), `street2` 4 per LT on its 64² texture.
The integer rounding is negligible (mean 0.035 texel, 95th percentile 0.18). `convert.py` needs no change.

**The engine used to draw them 4× too dense; fixed.** A surface texture with no cooked file in the active tier falls
back to the 1× bitmap, and that fallback computed its logical size with the *active* tier instead of the file's
(`game/maps/MapAssetLoader.cpp`, the source-image branch after the cooked slots), so with the desktop default
`texture=x4` a 128² MM9 bitmap became 32 logical texels and repeated 4× per MM9 repeat. Since commit `f6bed391c` the
branch takes the tier of the loaded file (`loadedTier` from `loadBitmapPixelsBgra`), like the cooked branch
(`decodeCookedSurfaceTexture`, `assetScaleTierFromResolvedPath`). Confirmed in game on 2026-10-31 on Temple of Honk,
which had no x4 files: the 1× art draws at MM9's density
(`level_generation/textures_x4/audit/mm9_shots/density_honk_spawn.png`). The 1× carrier stage
`output/textures_x4_runs/mm9-anskram-x1carrier` is no longer needed for comparisons. The sprite paths
`IndoorRenderer.cpp` (`billboardTexture.width = ... m_assetScaleTier`) and `OutdoorBillboardRenderer.cpp` still use the
active-tier rule (not checked here).

At MM9's own mapping the density is lower than MM6–MM8's (1 texel per native unit at 1×): 128² textures at
0.39/unit are 2.56× coarser in each direction. The x4 tier (512² masters, same UVs) brings the keep to 1.56 texels
per native unit, between MM6–MM8's 1× and 2×; their x4 density (4/unit) would need about 10× masters. The x4 run is
in [`../../textures_x4/PLAYBOOK.md`](../../textures_x4/PLAYBOOK.md) ("MM9 rework maps"); comparison
`review/x4_compare.jpg` (old import, 4× too dense | native 1× as the user sees it now, 4× too dense | native 1×
at the right scale | native x4).

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

**Installed: lightmap-matched (re-lit 2026-10-31, the user's decision of 2026-10-30: dungeon lighting follows MM9's DAT
lightmaps for brightness and hue; MM9 draws walls as texture x lightmap x1, `devdocs/mm9_rework/MM9_RENDER_LIGHTING_RE.md`).**
`../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_anskramkeep.yml`: 128 samples,
3 bounces, **`direct_scale` 0.46, `bounce_scale` 6, `ambient_scale` 0.58, `max_lighting` 1**, `dirlights: true` (MM9's
408 DirLights as spots), the fill light `Light6` bake-only; sector minimum light 20 and the scene's black fog
unchanged. One 4096 x 1664 page, passes in `output/mm9_rework/bakes/anskramkeep`; the re-light was a `--recompose`
through `../mm9r_common/bake_slot.sh` (no Cycles run). `tools/lighting/stale_bakes.py --assets
output/mm9_rework/assets_dev --check` does not list the map. Bake again after every `convert.py` that changes the BLV.

**Method.** `../mm9r_common/relight_fit.py` composes the saved passes per zone and per room without Blender; `--grid --max
1` fitted (direct, ambient) to the zones' mean, B/R, G/R and the map-wide texel quantiles (MM9 p10/p50/p90 0.19 / 0.41 /
0.67). Zones: `hue_zones.py`, ten k-d boxes (`../mm9r_common/relight_zones.py`). This map was already the closest of
the five (it had been fitted to a capture that is dark here), so the change is small.

Lightmap texel luminance ours / MM9's DAT lightmaps per zone (`../mm9r_common/hue_vs_lightmaps.py`,
`work/relight/hue_before.txt`, `hue_after.txt`):

| Zone | MM9 luma | before | after | ratio before -> after | B/R MM9 / after | G/R MM9 / after |
| --- | --- | --- | --- | --- | --- | --- |
| z01_sw | 0.410 | 0.555 | 0.413 | 1.35 -> **1.01** | 0.71 / 0.73 | 0.93 / 0.90 |
| z02_w_mid | 0.445 | 0.627 | 0.456 | 1.41 -> **1.02** | 0.74 / 0.71 | 0.94 / 0.89 |
| z03_w_north | 0.442 | 0.587 | 0.423 | 1.33 -> **0.96** | 0.75 / 0.72 | 0.94 / 0.90 |
| z04_nw | 0.414 | 0.514 | 0.381 | 1.24 -> **0.92** | 0.72 / 0.75 | 0.94 / 0.91 |
| z05_s_midwest | 0.417 | 0.461 | 0.351 | 1.11 -> **0.84** | 0.73 / 0.77 | 0.94 / 0.92 |
| z06_centre_south | 0.455 | 0.666 | 0.503 | 1.47 -> **1.11** | 0.73 / 0.75 | 0.94 / 0.92 |
| z07_centre_north | 0.427 | 0.589 | 0.424 | 1.38 -> **0.99** | 0.74 / 0.76 | 0.94 / 0.90 |
| z08_ne | 0.415 | 0.540 | 0.395 | 1.30 -> **0.95** | 0.73 / 0.74 | 0.94 / 0.91 |
| z09_se | 0.398 | 0.544 | 0.398 | 1.37 -> **1.00** | 0.72 / 0.74 | 0.93 / 0.90 |
| z10_e_mid | 0.472 | 0.603 | 0.443 | 1.28 -> **0.94** | 0.70 / 0.71 | 0.93 / 0.90 |

Hue matches in every zone (warm yellow, B/R 0.71-0.77 against MM9's 0.70-0.75). Per room (`work/relight/fit_after.txt`)
two small rooms that MM9 lights and our bake does not (sectors 11 and 17, x0.5, at the floor) and sector 36 (x0.67)
stay under; MM9's darkest room (43, texels 0.17) matches.

**Screen brightness** (the 30 v04 views, `work/relight/views.txt`, centre crop luma): capture 46.4 (information only),
unbaked 45.9, old bake 46.9, **lightmap bake 35.1 (x0.76)**. Darkest baked views: the gate switch 17.6, the treasure panel
19.0, the north gates and gate levers 22.0: no room needs a player-light floor (none under luma 12). No real MM9
screenshot of this map exists.

**Props: the old path stays** (sector minimum light 20, `model_lighting: false` in `overrides.yml`). Same bake both ways
(`../mm9r_common/relight_props.py`, `work/relight/model_lighting_props.txt`): relative brightness of the props to their
view, capture 1.07, **old path 1.49**, model lighting (AmbientLight 40, ModelAdd 30) 1.03; in the furniture rooms
(views 15-23) the old path stays at the capture's 1.15-1.67 and model lighting falls to 0.59-1.21. By eye
(`review/lighting_v06_props_compare.jpg`, capture | old | model) model lighting draws the officers' wardrobes and the
barracks beds near black (AmbientLight 40 is low and the torches are far); the old path keeps them as the capture shows
them. The trial rebuilt the map with the block and back: BLV and scene byte-identical at the end; the four scenarios
(chests, doors_exits, rotating, scripted) pass.

Sheets (looked at): `review/lighting_v06_compare.jpg`, `review/lighting_v06_p01-p05.jpg` (capture | unbaked | old bake |
lightmap bake). The pale entrance stone now reads yellow-green as in the capture instead of grey, the halls a little
dimmer.

**Documented alternative: the capture-matched bake** (installed until 2026-10-31): `work/profile_capture_matched.yml`
(direct 1.0, bounce 6, ambient 0.5, max 1): lightmap ratios 1.11-1.47, screen mean 46.9. To switch back: copy it over the
profile and `--recompose` as above.

### History (capture-matched calibration, 2026-10-30)

The BLV is lightmapped from its own lights ([indoor baked lighting](../../../devdocs/INDOOR_BAKED_LIGHTING.md)):
`../mm9r_common/dungeon/lighting.py level_generation/projects/mm9r_anskramkeep` bakes `anskramkeep.lighting` / `.bake.json`
(profile `tools/lighting/baked_indoors/profiles/mm9_anskramkeep.yml`, passes in `output/mm9_rework/bakes/anskramkeep`, about
12 min) and installs them through `review_root.install()`; `--recompose` retunes the scales, `--remove` uninstalls. The
bake belongs to the BLV it was made from: run it again after `convert.py` changes the map.

**Colour (2026-10-30).** The keep's colour is in MM9's `DirLight`s, not in its textures. The x4 masters match their 1×
natives within 2 levels per channel, so they were left alone. MM9's lightmaps average (101, 95, 75), hue 1.12 / 1.05 /
0.83, from its 408 `DirLight`s (241, 235, 154: three fans and an up-light per torch), while the BLV lights are the
torches' orange (231, 157, 90): the bake without them read warm tan. `dirlights: true` in the profile (spots with MM9's
aim) brings the 30 views' hue to 1.19 / 1.01 / 0.81 against MM9's 1.14 / 1.02 / 0.83 (before: 1.22 / 0.97 / 0.81).

**Scale.** Mean of the 30 views (`review_colour.py review/v04_original review/v04 --views`): MM9 **44.4** at unlimited view
distance (46.2 was the faded reading), native **42.1**, view ratio median 0.91, 10-90 % 0.69-1.32. Profile: direct 0.48,
bounce 10.5, ambient 0.66. **Not matched:** the entrance and south hall stay brighter than MM9 (1.3×, and paler on the
door row), the north hall and the store rooms darker (0.68). MM9's lightmaps clip at 255, which is ×1 on the texture
(12-30 % of the entrance's texels sit there, on `anskramedge`/`anskramframe`, mean 112), while the bake reaches ×4 near
overlapping torch fans. The scales above compress that range by moving energy from direct to bounce; a ceiling in the
bake (a profile `max_lighting` in place of the fixed 4 in `compose`) would fix it at the cause and let the dim rooms rise.
That file belongs to the bake and fog work. MM9's map fog (black, 1 to 5000 LT) arrives with that work too.

**2026-10-30, ceiling and fog.** The bake has `max_lighting` now and the scene carries the fog (`Source.fog`, automatic;
[indoor fog](../../../devdocs/INDOOR_FOG.md)). Profile: direct 1.0, bounce 6, ambient 0.5, `max_lighting` 1, by recompose
of the 15:03 passes. Mean of the 30 views with fog drawn: **45.3** (MM9 44.4; fog alone takes about 3 off), mean absolute
error 7.5 (9.7 before); entrance 1.10 (was 1.32), south hall 0.98 (1.30), central hall 0.91 (0.74), north hall 0.81
(0.68). Still off: the store rooms (20, 25: 0.6), the small rooms 26, 27, 29, 30 (1.5-1.6) and the brightest stone,
which is paler than MM9 (red/blue of the top 30 % of the entrance 1.41, MM9 1.63, 1.90 before the ceiling). A ceiling of
1.25 did not fix the hue (1.43) and put the entrance back at 1.28. The reference draws no fog, so a match in brightness
with fog on leaves the lightmaps somewhat brighter than MM9's. Sheet `review/lighting_v05_compare.jpg`.

**2026-10-30: doors and the fill light.** The 708 mover faces
(gates, doors, panels, levers, the exit stair) are lightmapped in their stored pose and their light moves with them
(before, vertex-lit and brighter than the walls); MM9's fill light `Light6` (radius 3 072, over the four-per-point
cap) lights the bake only, which brings the central hall (views 05/06: MM9 55, before 31/34, after 60/63) up to MM9.
The keep has no sky faces or windows. `ambient_scale` 0.85 (was 1.0). Mean brightness of the 30 v03 views (centre
crop, `python3 -m dungeon.sheet --brightness`): MM9 46.2, before 48.0, after 47.3. Sheet
`review/lighting_v03_compare.jpg` (MM9 | before | after).

## Engine and tool change

The glTF route triangulated every polygon (about 17 000 faces for this map). The indoor import setting
`triangulate_ngons` existed but was never read; `triangulate_ngons: false` now keeps a glTF `TRIANGLE_FAN` primitive
as one convex polygon face (`editor/import/ObjModelImport.cpp`, passed by `IndoorSourceGeometryCompiler.cpp`; the
default stays true, so existing sources are unchanged). Test: `tests/IndoorSourceGeometryCompilerTests.cpp`
"indoor source keeps glTF fan polygons whole when n-gons are not triangulated". The compiler's planarity rule (0.01
after integer quantization) still applies, which is why non-axis-aligned polygons are written as triangles.

## What remains

Monsters opening doors (above); the barrels and bone piles as MM9 loot props; the MM9 Imp and Icky family art (creature
work); a native density and pack pass (PLAN.md: later); the perception frames as a world contribution instead of a review
root row (the engine's `texture_frame_data.txt` has no world layer).

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:55:23 (convert.py from the current shared converter, end 14:56:24): 3 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 8965 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_rotating.yml` pass (after the fix below), `scenario_scripted.yml` pass.

**`scenario_rotating.yml` and MM9's monster bodies (fixed 2026-10-31).** Step 36 (TrapExitDoor1, mechanism 101, still
"opening" 2 s after its click) failed after the rebuild. Not the table and not the geometry: with the old table the
new map still failed, with the new BLV and only the scene's old actor radius/height it passed. The walks run without
actor AI but the waits do not: NagateHatchling3 (placed at (0, 2621); MM9 radius 46, the stand-in's 109) now follows
the party from the double doors to the trap corridor (with 109 it stuck at x 1681) and stood at (3101, 1920) with its
body in the hatch's swing (leaf x 3092-3256, y 1720-1884), so the hatch waited for it. That is the engine doing what a
blocked mover should; the scenario relied on the oversized body keeping monsters away. `make_scenarios.py` now slays
the placed monsters that are awake at load (not the Invisible ones: the Giant Imp, the guards) before the mover checks;
they stay dead on the scenario's reload.

## Rebuild 2026-11-06: black doorways, quarter-turned furniture, the cage window

User reports: nine views drawing black, bookcases, desks and dressers standing a quarter turn off, z-fighting under
the Icky cage window once it opens. Three causes, all fixed in the shared converter (`../mm9r_common/dungeon/`):

- **Floors past their portal** (the black views). With `split_minor_rooms: false` the floor of a room ran on through
  19 doorways past its portal, which `door_portals` moves onto the leaves' face (Anskram's doorways: 134 units past
  the plane; one hall floor ran 960 units on past a portal into the next room). The engine finds the party's sector
  by the floor under it, so a party standing there was put in the room behind the portal it was looking through,
  and only that room was drawn (`portals stats`: `portals_traversed=0`). Now `split_minor_rooms: true` (also the shared
  default) and `rooms.doorway_floors`: every floor piece in a doorway's width takes the room of its side of the portal,
  and a part beyond 6 voxels takes the room of the air over it. The floor check (`build_report.json` `floor_check`)
  looked inside the floor's own solid voxel and saw 18 LT²; it now samples a voxel and a half up.
- **Props in MM9's pose.** LithTech draws a prop in its first animation at its first key. The `*NS` ABCs
  (DresserNS, BookCase02NS, Desk01NS, Cabinet0xNS, the pews, Table01NS, WeaponRackNS, Stovens, ...) are their plain
  twins' files whose static animation turns the Scene Root by -90° about the vertical; the GLBs are the bind mesh,
  so placed at -ry they stood with their sides to the wall (and so does the old transcoder's bake, which `props.json`
  was fitted to). `dungeon/prop_pose.py` measures each model's pose against its bind mesh and, where the pose is a
  rigid quarter or half turn and the decoration's GLB is that bind mesh, places the GLB at yaw -ry + turn (-ry - 90
  for the `*NS` furniture) about the ABC origin; props.json yaws of those models are replaced (`content.json`
  `pose_turned`). Other props keep their props.json placement. Here: 20 dressers, 2 bookcases, 1 desk.
- **Sinking plugs go under the floor** (`movers.sink_length`). `CritterBreakOut1`, the Icky cage window set 128 LT up
  in the wall, sank only its height and ended in the wall below it, its faces in that wall's planes.
