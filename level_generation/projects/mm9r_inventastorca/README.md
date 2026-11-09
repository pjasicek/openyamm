# MM9 rework: Inventa Storca (`inventastorca.blv`)

MM9's Inventa Storca (the old library under Thronheim, reached from Thronheim's ExitTrigger5) converted from its DAT
world into a native indoor map (BLV: sectors, portals, rotating and linear movers, a ladder, lights, an exit volume) on
the shared dungeon converter ([`../mm9r_common/DUNGEON_PLAYBOOK.md`](../mm9r_common/DUNGEON_PLAYBOOK.md)). Built into
the isolated review root `output/mm9_rework/assets_dev`; `assets_dev` is written only for the MM9 world's decoration rows
and the prop models ([props project](../../props/mm9_inventastorca_claude/README.md)). No x4 textures yet.

Status 2026-10-30 (overnight run): geometry, 27 rooms, 88 movers, the ladder and its trapdoor, 71 BLV lights, the exit,
108 decorations, 3 chests and 2 treasure bags, 39 actors, the library's scripted objects, the eleven perception hints, the
flooded cavern and the well, and baked lighting. Scenarios pass; review sheets below were looked at.

## Build and review

```sh
python3 level_generation/projects/mm9r_inventastorca/convert.py --plan    # rooms only: work/rooms_<storey>.png
python3 level_generation/projects/mm9r_inventastorca/convert.py           # build, compile, install
python3 level_generation/projects/mm9r_inventastorca/cave_lights.py     # the cave shaft's bake-only lights
level_generation/projects/mm9r_common/bake_slot.sh python3 level_generation/projects/mm9r_inventastorca/bake.py
#   (the shared dungeon/lighting.py plus the cave lights; about 4 minutes; --recompose: seconds)
python3 level_generation/projects/mm9r_inventastorca/make_scenarios.py
for s in doors_exits chests scripted; do ./build/game/openyamm --asset-root "$PWD/output/mm9_rework/assets_dev" \
    --headless-run-scenario level_generation/projects/mm9r_inventastorca/scenario_$s.yml --scenario-no-color; done
python3 level_generation/projects/mm9r_common/dungeon/audit.py level_generation/projects/mm9r_inventastorca
python3 level_generation/projects/mm9r_inventastorca/make_tour.py v07 [--original]   # also v07_unbaked, open01, hints01
SDL_AUDIODRIVER=dummy ./tools/run_game.sh --isolated invsto --world mm9 --map inventastorca.blv --assets "$PWD/output/mm9_rework/assets_dev" \
    --position 369 154 -890 --yaw-radians 3.0796 --pitch-degrees 0 --warmup 3 --seconds 180 \
    --set debug.screenshot_tour_path=$PWD/level_generation/projects/mm9r_inventastorca/review_tour_v07.yml
#   original: --map inventastorca.odm --assets "$PWD/output/mm9_rework/assets_original" --set video.view_distance=unlimited
#   unbaked:  --set video.lightmaps=false
#   open01 / hints01 also take --set debug.menu_input_tour_path=<project>/input_<name>.yml (events / Perception 10)
python3 level_generation/projects/mm9r_inventastorca/tools/brightness.py review/v04_original review/v07_unbaked review/v07
python3 level_generation/projects/mm9r_common/hue_vs_lightmaps.py level_generation/projects/mm9r_inventastorca
```

`tools/`: `cutlab.py` (every cut and door portal against the voxels, leak paths, `--probe x,y,z` labels; cached),
`slice_scan.py` (which slices of a hall are one clean component), `leak_seeds.py`, `column.py` (floors over a point),
`sectors.py` (faces per compiled sector), `brightness.py` (per-view ratios), `diagnose_cut.py`.

## Numbers

- Frame: `native = (LT.x, LT.z, LT.y) * 2.56`, no offset (the old map's frame). Storeys: upper halls -336 (the
  entrance -348), lower library -640 (the ladder hall -576), the cave shaft -640 to +616, the flooded cavern floor -832
  under water at -576.
- 8 390 source polygons -> 8 158 merged -> 7 654 converted polygons -> **9 057 native faces** (14 972 vertices, 27
  triangulated); 996 faces with no air in front dropped (wall backs between brushes, the flooded channel's walls).
- **27 rooms** (+ sector 0), one sealed air component, no leak, faces per sector median 362, largest 706.
- **29 portal faces**: 12 MM9 UserPortals, 6 from door leaves (DoubleDoor6, DoubleDoor14, the breakable walls 0, 2, 3,
  the cage wall 4), 10 archway cuts (overrides.yml `portals`), 1 rectangle (the ladder's hole). Every portal joins two
  rooms (`portals_without_two_rooms` 0).
- **82 movers**: 59 `rotate` (14 double doors, 8 dressers' leaves, 6 falling bookcases and their 7 book switches, 2 secret
  panels), 23 `dat` (16 drawers, 2 desk drawers, the trapdoor, the secret floor panel, 3 switches). The six
  DestructableBrushes are scene destructibles (`break`, 2026-11-06; before: 5 `sink`, 1 `slide` movers).
- **1 ladder** (Ladder5, lower ladder hall to the upper floor through LadderDoor's hole).
- **71 lights** of MM9's 92: 13 over the four-per-point cap are bake-only; 8 left out (Light61-63 in the rock, 66-67 under
  the cavern's floor, 70-72 in the flooded channel under the water surface). No floor point under more than four.
- **108 decorations**, **5 loot containers** (Chest0-2, TreasureBag0/1), **13 pads** + the cavern's water pad,
  **39 actors** (9 of them the dead adventurers).

## What each DAT object became

| MM9 | Native |
| --- | --- |
| `PhysicsBSP`, `WorldObject4` (the ladder's rungs), `InvisibleBrush0-3` | static world, invisible collision; `VisBSP` only for its UserPortals |
| `RotatingDoor` `DoubleDoorL/R1-14` | `rotate` movers, one per leaf, MM9's swing, open-away, auto-close 7 s; doorway portals |
| `RotatingDoor` `DresserDoorL/R1-8`, `Door` `Drawer1-16`, `DeskDrawer`, `DeskDrawer0` | furniture: rotate / dat, a click opens and shuts |
| `Door` `LadderDoor` | the trapdoor over Ladder5's hole (`dat`, 96 LT); the shared classifier skips `Ladder*` models as ladder volumes, `convert.py` keeps this one |
| `RotatingDoor` `FallingBookcase1-6`, `FBR1-5`, the book switches | the bookcase domino: each relay's swing folded into its bookcase (70.5 degrees, MM9's end time), the relays not built, the switches ride their bookcase (Deviations) |
| `RotatingDoor` `SecretPanel`, `SecretPanel0`; `Door` `SecretPanel1`, `SecretSwitch*`, `FalseSwitch4` | the two wall niches with the treasure bags, the floor compartment over Chest1/Chest2, their switches |
| `DestructableBrush0-3` | breakable walls: scene destructibles 422, 421, 420, 423 (MM9 HitPoints 0, 0, 15, 1 -> 1, 1, 15, 1; cogs 20000 + index; `motion: break` keeps the doorway portals, DB1 the archway cut `DB1_opening`); weapons break them, a click (or a click on its red hint) deals the killing blow (events 38420-38423) |
| `DestructableBrush4`, `DestructableBrush5` | the bust-outs' cage wall and ceiling slab: scene destructibles 671 and 670 (no click; weapons break them as in MM9), broken by KingKong.scr's triggers |
| `BlueWater1`, `BlueWater0` | the cavern's surface (LT -576) and the well's (2 LT under the niche floor, so only the well's hole shows it): solid wading faces drawn with MM9's Ocean3.spr (20 frames, review root frame table) and a water liquid entry; `BlueWater2` (the channel under the rock) not built |
| `Ladder5` | scene `ladders` (facing south; the climber steps off over the shaft wall onto the upper floor) |
| `ExitTrigger0` | MM9 positioned transition volume to Thronheim (`InventaStorcaExit`) on the spiral stair by the start |
| `StartPoint0` | start 0, facing into the entrance corridor; Thronheim's ExitTrigger5 arrives there |
| `Prop`, `WallTorch`, `Brazier`, `Barrel`, `BonePile`, `TreasureChest`, `TreasureBag` | 3D decorations (props project); chests and bags open their loot containers |
| 9 monster classes | placed actors; `WealthyTownGuard1/2` (no MM9 monster row) take the Guard (9111) or Bandit (9101) row by model |
| `Trigger` (13) | 12 pressure pads; `Tom Needed A Trigger1` (inside DestructableBrush2) folded into that wall's break |
| `PerceptionBrush0-10` | untouchable translucent faces (Perception.spr, Alpha 0.35, two-sided), cogs 320-330, shown at the brush's PerceptionValue (8; 10 for PerceptionBrush5Level10) until their secret is found; a click on a glow runs the covered object's event (interact picks the glow first) |
| `AIRail`/`AITrk`, `Marker`, `AmbientSound`, `DirLight`, `StaticSunLight`, sky objects, `OutsideDef` | not built (DirLights light the bake) |

- **See-through water (2026-10-31)** ([shared helper](../mm9r_common/liquids.py): MM9 opacity = the surface's alpha x
  its sprite's mean alpha, see-through where a floor of its room lies under it; engine: `liquids.yml` `opacity`,
  devdocs/INDOOR_TRANSLUCENT_FACES.md)): unchanged: the cavern's and the well's surfaces (SurfaceAlpha 0.85 x Ocean3,
  no alpha) are wading faces with no floor of their room under them (`BlueWater2` is not built), so they stay opaque.

## Scripted objects (`worlds/mm9/events/maps/inventastorca.lua`, written by `convert.py`)

| MM9 | Native |
| --- | --- |
| **Orbs of Linking**: `Orb.scr` on Prop0-6 | world items (`dungeon/pickups.py`, item 252), picked up as any ground item; the pickup event plays the quest sound; all hidden once key 337 is held (its Init) |
| **Letters**: `BookLetter.scr` on Prop7, Prop8 (`494/495 Letter`) | MM9's BOOK AND SCROLL TEXT rows 494 (Letter to Thieves) and 495 (On Visitors from Space), bookopen.wav |
| **The dead adventurers**: `GreenParty.scr` on DeadLich0, DeadBandit0-4, DeadGreenPartyGuy0-3 | placed dead (hp 0) at load |
| **The dying adventurer and the Lich King**: `IS_DyingNpc.scr` (GreenPartyDude0), `IS_KillingLich.scr` (LKToKillGreenParty0); SpookTrigger5 and DoubleDoorL9's OpenTrigger send `Kill` | the Lich King is dormant and friendly; the Kill wakes him, makes him and the adventurer's row (9207 vs 9111) enemies and turns him hostile; the adventurer is set to his last hit point (`evt.SetMapActorHp`, also on load after the Kill), so the Lich King's first blow kills him, and then he hunts the party |
| **Spook**: `Spook.scr` (SpookObject), SpookTrigger0-4 | each trigger plays one of its sounds once; a random one every 2-8 minutes |
| **Scurrying basilisks**: `ScurryCreature.scr`, ScurryTrigger0/1 | the three small basilisks of each trigger run to HideMarker0 (`evt.MoveActorTo`, run) and are removed on arrival; a load sends the ones still running again (MM9: at six times their speed) |
| **The ickies in the cave shaft**: `IS_ficky.scr` (BirdIntheSky0), `IS_fickyflock.scr` (BrettBird0-4), BirdTrigg0/1 | the five resting ickies are gone when scattered (MM9: fly up to the FlockM markers and Die); BirdIntheSky0 stays high in the shaft, friendly |
| **Bust-outs**: `KingKong.scr` on BustOutLich0 (`ForceBreak` DestructableBrush4) and BustOutLichKing0 (`ForceFall` DestructableBrush5) | BustOutTrigger0: `evt.DestroyDestructible(671)`, the pair wakes; BustOutTrigger1: `evt.DestroyDestructible(670)` and the Lich King and two skeletons appear under the hole and wake |
| **Bookcases**: FallingBookcaseSwitch -> FBR1..5 -> FallingBookcase1..6 | a click topples one bookcase a second; the switch locks; PerceptionBrush5Level10 off |
| **Secret switches**: SecretSwitch, SecretSwitch0, SecretSwitch1 | each opens its panel once and locks (their OpenTriggers), the hint goes |
| **Breakable walls**: DestructableBrush0-3 (DeathTrigger: the hint off) | weapons or a click break the wall; its destroyed event (180 + k) sets `Broken<k>` and turns its hint off |
| **Furniture**: dressers, drawers, desk drawers, trapdoor | a click opens/shuts; the desk drawers' and trapdoor's hints show again when shut |
| **The flooded cavern** | the party falling from the walkways onto the water is moved to the well's shore (MM9: swims down BlueWater2 and up the well) |

## Baked lighting

> **Baked lighting removed 2026-10-31** (stale after rebuild/scene change); classic lighting until the end-of-integration lighting pass, see `devdocs/mm9_rework/MM9_LIGHTING_DECISION.md`. The removed sidecar pair is in `work/lighting_stale_20261031/`; the section below describes the bake as it was.

`bake.py` runs the shared `../mm9r_common/dungeon/lighting.py` with `tools/lighting/baked_indoors/profiles/mm9_inventastorca.yml`
and adds the cave shaft's lights to its extra lights: one 4096 page, 71 + 13 bake-only lights + MM9's 185 `DirLight`s
(`dirlights: true`) + 6 cave lights, `max_lighting: 1`, about 4 minutes; `direct_scale` 0.46, `ambient_scale` 0.671.
`tools/lighting/stale_bakes.py --assets output/mm9_rework/assets_dev --check` does not list the map.

- **Cave shaft** (`cave_lights.py`, map-local, no converter change): MM9 lights the shaft from DirLights and its
  lightmaps read a lit purple-grey; our bake left it nearly black. Six bake-only point lights stand on the shaft's axis,
  one per 160 LT of height that holds cave polygons, each coloured from MM9's own DAT lightmap of those polygons
  (area mean; blue x1.25, because the bake's warm fill dilutes the purple) at its band's relative strength x 2.05,
  radius 420 LT. Cave lightmap mean: ours (0.519, 0.455, 0.436) against MM9's (0.469, 0.407, 0.393): luminance x1.11,
  B/R 0.84 = MM9's.
- **Sector minimum light 31** (`map.ambient` in overrides.yml; was 20): see "Black tables" below. The bake's own floor is
  unchanged (its scene clamps the sector ambient to 0.18: `ambient_scale` 0.671 x 0.18 = the old 0.35 x 0.345).

## Brightness and hue (calibrated to the DAT lightmaps)

Per the brief's rule since 2026-10-30 22:25, each zone's lightmap mean and hue is matched to MM9's DAT lightmaps
(`hue_zones.py`, `../mm9r_common/hue_vs_lightmaps.py`; `work/lightmap_zones_final.txt`). Lightmap luminance ours/MM9:
west hall 1.26, long hall 1.16, north halls 0.92, green party hall 1.72, reading rooms 0.94, south rooms 0.93, lower
library 0.96, cave shaft 1.11. Hue: every zone "matches" (B/R within 0.03-0.09 of MM9's, ours a little warmer in the
lit halls; G/R 0.04-0.10 higher, a slightly greener cast). The green party hall's torches overshoot (x1.72): the global
scales cannot lower one zone without darkening the reading and south rooms below MM9's.

For information only, against the reference capture (36 views, centre crop, `review/brightness_v07.txt`): capture
66.4, native unbaked 71.7, baked 68.5 (x1.03); the cave views now x1.33/x1.70 of the capture (the capture is not MM9).

Sheets: `review/v07_compare.jpg` (36 views, capture | native baked), `review/lighting_v07_compare.jpg` (12 views,
capture | unbaked | baked), `review/cave06_compare.jpg` (first cave-light pass), `review/open01_sheet.jpg` (the scripted
objects open: domino, niches, broken walls, cage, ceiling hole, trapdoor), `review/hints01_sheet.jpg` (the glow at
Perception 10), `review/flames01_sheet.jpg`, `review/v01_compare.jpg` (first build, unbaked).

## Black tables (traced)

The west hall's five bench tables (`mm9_deco_tablebench2`, Drangheim Prison's model) drew solid black baked and dark
unbaked. The model is fine (normals agree with the winding, material and texture normal; in Drangheim Prison it draws
lit). The cause is the engine's decoration light (`IndoorRenderer::billboardLightingUniform`): a decoration's light is
its sector's ambient plus the grid lights at its centre, **minus the frame ambient** (`IndoorLightingFrame::ambient`,
from the sectors' minimum light level, 0.345 at level 20). In a baked map the sector ambient is the bake's actor ambient,
which is the bounce fill only; the west hall is lit by DirLights (direct light, bake-only), so its actor ambient was
0.26-0.34, at or under the subtracted 0.345, and the tables stand 700+ units from the nearest BLV light (radius 768):
light 0. Fixed in the map: sector minimum light 31 makes the subtracted frame ambient 0, the bake is unchanged (above),
and the table top went from (8, 6, 4) to (31, 28, 21) in `u11` (the rest of the hall's floor reads (60-100)); it is now as
dark as the hall's fill, still darker than its floor. Other maps may share it: any decoration in a baked map far from
BLV lights in a room lit mostly by direct, bake-only light. The engine-side fix (a decoration's baked light should not
subtract the vertex-light frame ambient, or the actor ambient should include the direct share) is not made here.

## Checks

- Scenarios (all pass): `scenario_doors_exits.yml` (the spiral stair raises ExitTrigger0; DoubleDoor1 stops the party,
  opens on a click on its leaf and is walked through; DoubleDoor9's click sends the Lich King's Kill; the shut trapdoor
  stops a climb up Ladder5, clicked open the party climbs out on top; a click breaks DestructableBrush0 (Broken0, its hint off), DestructableBrush2 stands at 14 damage and breaks at 15; 2026-11-06),
  `scenario_chests.yml` (Chest0 by a click; the switches clicked open the niches and the floor compartment; the bags and
  Chest1/2 behind the moved panels by their events: headless picking does not follow door motion), `scenario_scripted.yml`
  (the dead lie dead; hints at Perception 1 and 8; an orb by a click gives item 10252; a letter; the domino; walking onto
  ScurryTrigger0 removes its basilisks; the ickies scatter; both bust-outs; walking onto SpookTrigger5 turns the Lich King,
  who kills the adventurer within 30 s; a spook trigger; the cavern's water).
- Walkability (`work/walkability.json`): steps are the MM9 spiral exit stair (61-92 risers; the party walks it in the
  exit scenario) and the cave shaft's rock ledges (41-125, MM9's own); "pits": the well's puddle and the ceiling slab's
  hidden open pose; 5 "unreachable" regions are desk and table tops (no actors). No region holding actors is cut off from
  the start, so no reach probes were needed; 1 actor note: BrettBird3 (a flier) near the shaft wall.
- Floor check: 1 877 LT² (door sills). Found by looking, not by the check: the cave shaft's -640 floor ran under the wall
  to the lower hall and went to the hall's sector, so the whole cave drew black from inside; `edit_polygons` splits it at
  z -500 (the cave floor is now in the cave's room).
- Flames from the side (`review/flames01_sheet.jpg`): the wall torches' card flames sit on the torch heads from east,
  west and front; the hanging bowl's flame stands in the bowl.
- Dropped faces: wall backs and the flooded channel's walls; no thin partitions found (`thin_walls` on anyway).

## Deviations from MM9 and why

- **Breakable walls also break on a click**: MM9's party smashes DestructableBrush0-3 with weapons only (which work
  too: they are scene destructibles since 2026-11-06).
- **The bookcase domino** turns each bookcase by its relay's angle plus its own (MM9 attaches the bookcase to an invisible
  relay door); the book switches ride along, losing their 3 LT push.
- **Walking scripts**: the basilisks run at their own run speed, not six times it; the ickies vanish instead of
  flying off; the Lich King kills the adventurer by an ordinary blow on his last hit point, not a scripted one; the falling Lich King appears on the floor instead of falling.
- **Water**: no diving or swimming; the cavern and well are wading floors; the three bone piles (TreasureLevel 1) lie at
  the cavern's bottom, unreachable until diving lands.
- **Sounds**: the MM9 anim sounds (lichkingTaunt, gopherwince, dragonflyhattackair1, harpyflap) are not in the audio
  import: Spook plays the other eight; the scurry and scatter use dragonredhop/woodcreak1.
- **AxeTrap**: every DoubleDoor's OpenTrigger toggles `AxeTrap`, which is not in the DAT: unmatched, nothing built.
- **Bodies**: radius and height from the ABC anim-binding extents x the object's Scale x 2.56; the 0.2-scale scurrying
  basilisks draw at their 0.2 (the scene's `draw_scale`). The dying adventurer's 1 HP in the scene is filled up to his
  row's 52 by the load-time bolster; the Kill sets it back to 1 (`evt.SetMapActorHp`).

## Open items

- MM9 3D models for the Guard and Highwayman families draw stand-ins (another session builds them).
- Decorations in baked light under direct-lit rooms stay darker than their floors (Black tables): an engine change.
- The green party hall's lightmap is x1.72 MM9's (its torches).
- A density and pack pass (PLAN.md: later); x4 textures last.

## Rebuild 2026-10-31: invisible ramp bottoms

Rebuilt 2026-10-31 14:59:26 (convert.py from the current shared converter, end 15:00:56): 1 down-facing faces of invisible collision brushes dropped (`work/invisible_bottoms.json`; the flat undersides of MM9's invisible ramp wedges and helper brushes resting at most the party's height over a floor, which stopped the party on stairs as invisible ceilings: `../mm9r_common/DUNGEON_PLAYBOOK.md`, "Package change: invisible brush bottoms"); the BLV now has 9057 faces. The rebuild also carries the converter's other changes of the day (monster collision sizes, water).
Scenarios after the rebuild: `scenario_chests.yml` pass, `scenario_doors_exits.yml` pass, `scenario_scripted.yml` pass.
